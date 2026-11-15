"""The style showcase on the homepage: docs/site/styles/, one overview and one page per style (stdlib; ffmpeg for stills).

usage: python3 tools/style_site.py [build] [--stills]   write the pages from styles/ (bin/vh style site)
       python3 tools/style_site.py check                the pages against styles/ (tools/ci.sh)

build reads styles/showcase.json (the groups, by what the picture looks like, and each style's words in English and
Chinese), each styles/<slug>/tokens.json (palette, fonts) and STYLE.md's title (the Chinese name), and writes:
  - docs/site/styles/index.html: the overview, every style in its group, with search;
  - docs/site/styles/<slug>/index.html: the style's sample, four stills, what it is and what it suits, a sentence to
    give an agent, its palette and fonts, a link to its STYLE.md, three related styles;
  - docs/site/styles/media/<slug>/1-4.jpg: four stills from its sample (at STILL_T), made with ffmpeg when the sample
    changed (media/manifest.json records each sample's sha256), or every time with --stills;
  - docs/site/img/styles/<slug>.jpg, the homepage's thumbnail, when it is missing;
  - the homepage's STYLES list (docs/site/index.html), in the groups' order.
The page's look and motion are docs/site/styles/showcase.css and showcase.js, written by hand. A new style gets its page
on the next build; until showcase.json has its group and words, it sits in a last group with the first paragraph of its
STYLE.md, and check says so.

check builds every page in memory and compares: a page that differs, is missing, or has no style left behind; a style
with no group or words; a still or thumbnail missing, or made from another sample; the homepage's STYLES list out of
order; a link, image or sample a page names that is not in the repo; anything loaded from another site; a page with
more English texts than Chinese or the other way round. Exit status: 0 all good, 1 a problem (each said), 2 usage.
"""
import hashlib, html, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLES = ROOT / "styles"
SITE = ROOT / "docs" / "site"
OUT = SITE / "styles"
MEDIA = OUT / "media"
DATA = STYLES / "showcase.json"
HOME = SITE / "index.html"
REPO = "https://github.com/ZLHad/OpenVideoHarness"
STILL_T = (0.6, 1.6, 3.2, 4.6)   # the four stills: the opening move, building up, everything in place, the end card
CARD = 3                         # the still that stands for the style in cards and the strip (t = 3.2 s)
STILL_W, STILL_H = 640, 360
LOOP = 5.0                       # every sample is 5 s
ROLES = [("display", "Titles", "标题"), ("body", "Text", "正文"), ("zh", "Chinese", "中文"), ("ui", "Interface", "界面"),
         ("mono", "Monospace", "等宽")]


def esc(s):
    return html.escape(str(s), quote=True)


def bi(en, zh, tag="span", cls=""):
    """The same text in both languages, side by side; CSS shows the one that matches <html data-lang>."""
    c = f' class="{cls}"' if cls else ""
    return f'<{tag} lang="en"{c}>{en}</{tag}><{tag} lang="zh"{c}>{zh}</{tag}>'


def hexes(palette):
    """The palette as up to 8 colours: background, text, accent, then the rest in the order tokens.json gives them."""
    first = [palette.get("bg"), palette.get("fg") or palette.get("ink"), palette.get("accent")]
    rest = list(palette.get("extra") or []) + [v for k, v in palette.items() if k not in ("bg", "fg", "ink", "accent", "extra")]
    out = []
    for c in first + rest:
        if isinstance(c, str) and re.fullmatch(r"#[0-9A-Fa-f]{6}", c) and c.upper() not in out:
            out.append(c.upper())
    return out[:8]


def families(fonts):
    out = []
    for key, en, zh in ROLES:
        v = (fonts or {}).get(key)
        fam = v.get("family") if isinstance(v, dict) else v
        if isinstance(fam, str):
            fam = [fam]
        if fam:
            out.append((en, zh, [str(f) for f in fam][:3]))
    return out


def rgb(c):
    return tuple(int(c[i:i + 2], 16) / 255 for i in (1, 3, 5))


def lum(c):
    r, g, b = rgb(c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def distance(a, b):
    """How far apart two styles look, by their background, text and accent colours."""
    d = 0.0
    for w, x, y in zip((2.0, 1.0, 1.0), a["palette"][:3], b["palette"][:3]):
        d += w * sum((p - q) ** 2 for p, q in zip(rgb(x), rgb(y)))
    return d


def first_paragraph(md):
    for block in md.split("\n\n")[1:]:
        b = block.strip()
        if b and not b.startswith(("#", "|", "-", ">", "`", "样片")):
            return re.sub(r"\s+", " ", b)
    return ""


def split_ask(text):
    """'Tell [a fable] in 40 s' → ('Tell ', 'a fable', ' in 40 s'); no blank → (text, '', '')."""
    m = re.search(r"\[([^\]]+)\]|〔([^〕]+)〕", text)
    if not m:
        return text, "", ""
    return text[:m.start()], m.group(1) or m.group(2), text[m.end():]


def load():
    """Every style, in the groups' order, with what its pages say; and the groups. Problems go to the third value."""
    data = json.loads(DATA.read_text(encoding="utf-8"))
    words, groups, bad = data.get("styles", {}), [], []
    folders = sorted(p.parent.name for p in STYLES.glob("*/STYLE.md") if not p.parent.name.startswith("_"))
    seen = {}
    for g in data["groups"]:
        groups.append({"id": g["id"], "name": g["name"], "line": g["line"], "slugs": []})
        for slug in g["styles"]:
            if slug not in folders:
                bad.append(f"styles/showcase.json: group {g['id']} lists {slug}, which is no style in styles/")
            elif slug in seen:
                bad.append(f"styles/showcase.json: {slug} is in both {seen[slug]} and {g['id']}")
            else:
                seen[slug] = g["id"]
                groups[-1]["slugs"].append(slug)
    left = [s for s in folders if s not in seen]
    if left:
        bad += [f"styles/showcase.json: {s} is in no group (add it to the group its picture looks like, with its words)" for s in left]
        groups.append({"id": "new", "name": {"en": "Just added", "zh": "新加的"},
                       "line": {"en": "Styles that are not in a group yet.", "zh": "还没分组的风格。"}, "slugs": left})
    for slug in words:
        if slug not in folders:
            bad.append(f"styles/showcase.json: words for {slug}, which is no style in styles/")
    styles, n = [], 0
    for gi, g in enumerate(groups):
        for slug in g["slugs"]:
            d = STYLES / slug
            tokens = json.loads((d / "tokens.json").read_text(encoding="utf-8"))
            md = (d / "STYLE.md").read_text(encoding="utf-8")
            zh = re.sub(r"^#\s*", "", md.splitlines()[0]).split(" · ")[0].strip()
            en = (tokens.get("name") or {}).get("en") or slug
            w = words.get(slug, {})
            for key in ("what", "for", "ask"):
                for lang in ("en", "zh"):
                    if not (w.get(key) or {}).get(lang):
                        bad.append(f"styles/showcase.json: {slug} has no {key}.{lang}")
            fallback = first_paragraph(md)
            text = {key: {lang: (w.get(key) or {}).get(lang) or "" for lang in ("en", "zh")} for key in ("what", "for", "ask")}
            text["what"]["zh"] = text["what"]["zh"] or fallback
            text["what"]["en"] = text["what"]["en"] or fallback
            text["ask"]["en"] = text["ask"]["en"] or f"Make a 30-second film about [your topic] in the {en} style (styles/{slug})."
            text["ask"]["zh"] = text["ask"]["zh"] or f"用{zh}风格（styles/{slug}）做一支 30 秒的短片，讲〔你的题目〕。"
            pal = hexes(tokens.get("palette") or {})
            if len(pal) < 3:
                bad.append(f"styles/{slug}/tokens.json: fewer than three colours in its palette")
                pal = (pal + ["#111111", "#EEEEEE", "#888888"])[:3]
            n += 1
            styles.append({"slug": slug, "en": en, "zh": zh, "n": n, "group": gi, "palette": pal,
                           "fonts": families(tokens.get("fonts")), "text": text, "near": w.get("near")})
    by = {s["slug"]: s for s in styles}
    for s in styles:   # three related styles: the two closest in its group, then the closest outside it
        if s["near"]:
            s["near"] = [x for x in s["near"] if x in by][:3]
            continue
        same = sorted((o for o in styles if o["group"] == s["group"] and o is not s), key=lambda o: (distance(s, o), o["n"]))
        other = sorted((o for o in styles if o["group"] != s["group"]), key=lambda o: (distance(s, o), o["n"]))
        pick = same[:2] + other[:1]
        pick += [o for o in other[1:] if o not in pick][:3 - len(pick)]
        s["near"] = [o["slug"] for o in pick[:3]]
    return styles, groups, bad


# ---------------------------------------------------------------- pages

# Runs before the first paint: the language (?lang=, the saved choice, the browser's), the motion classes, and the cut from
# the page before. A cut is a cross-document View Transition: "morph" (a card grows into this page's player, named "hero"),
# "wipe-next" / "wipe-prev" (a playhead sweeps the next style in), or, arriving any other way at the overview, the card of
# the style just left takes the player's place. showcase.js marks the cut when a link is clicked.
HEAD_JS = """(function(){var d=document.documentElement,l=null;try{var q=new URLSearchParams(location.search).get('lang');
if(q==='zh'||q==='en')l=q;else l=localStorage.getItem('ovh-lang');}catch(e){}
if(l!=='zh'&&l!=='en')l=/^zh\\b/i.test(navigator.language||'')?'zh':'en';d.setAttribute('data-lang',l);
d.lang=l==='zh'?'zh-CN':'en';document.title=d.getAttribute('data-title-'+l)||document.title;d.classList.add('js');
if(!matchMedia('(prefers-reduced-motion: reduce)').matches)d.classList.add('motion','enter');
function take(k){try{var v=sessionStorage.getItem(k);sessionStorage.removeItem(k);return v}catch(e){return null}}
addEventListener('pagereveal',function(e){var cut=take('ovh-cut'),from=take('ovh-from'),vt=e.viewTransition;if(!vt)return;
d.classList.remove('enter');var h=document.querySelector('.screen');
if(cut==='wipe-next'||cut==='wipe-prev'){try{vt.types.add(cut)}catch(x){}d.classList.add('wiping');if(h)h.style.viewTransitionName='none';
vt.finished.finally(function(){d.classList.remove('wiping');if(h)h.style.viewTransitionName=''});return}
if(cut==='morph'||h||!from)return;var c=document.querySelector('.card[data-slug="'+from+'"] .pic');if(!c)return;
var r=c.getBoundingClientRect();if(r.bottom<0||r.top>innerHeight)return;c.style.viewTransitionName='hero';
vt.finished.finally(function(){c.style.viewTransitionName=''})});
addEventListener('pageswap',function(){var b=document.body;if(b&&b.dataset.slug)try{sessionStorage.setItem('ovh-from',b.dataset.slug)}catch(x){}});
})();"""

GH_ICON = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path fill="currentColor" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 '
           '5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52'
           '-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82'
           '-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1'
           '.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46'
           '.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>')


def head(title_en, title_zh, desc, up, extra=""):
    """<head> and the top bar's first half. up: the way from the page to docs/site/styles/ ('' or '../')."""
    return f"""<!doctype html>
<html lang="en" data-title-en="{esc(title_en)}" data-title-zh="{esc(title_zh)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title_en)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="#04050A">
<!-- Written by tools/style_site.py (bin/vh style site) from styles/: edit styles/showcase.json or the generator, not this file. -->
<script>\n{HEAD_JS}\n</script>
<link rel="stylesheet" href="{up}showcase.css">
{extra}<script src="{up}showcase.js" defer></script>
</head>
"""


def topbar(up, middle):
    home = up + "../"
    return f"""<header class="top">
  <a class="brand" href="{home}">OpenVideo<span>Harness</span></a>
  <a class="crumb" href="{up or './'}">{bi("Styles", "风格库")}</a>
  {middle}
  <button class="langbtn" id="langbtn" type="button" aria-label="中文 / English"><span data-v="en">EN</span><span data-v="zh">中</span></button>
  <a class="gh" href="{REPO}" target="_blank" rel="noopener">{GH_ICON}<span class="t">GitHub</span></a>
</header>
"""


def gloss(s):
    """The name in the other language, under the main one."""
    return f'<span class="gl-en" lang="zh">{esc(s["zh"])}</span><span class="gl-zh" lang="en">{esc(s["en"])}</span>'


def name(s):
    return bi(esc(s["en"]), esc(s["zh"]))


def chips(s, n=6):
    return "".join(f'<i style="--c:{c}"></i>' for c in s["palette"][:n])


def card(s, up, groups, extra_cls=""):
    """A style's card: its picture (which plays from the shared clock on hover), names, what it suits, its colours."""
    g = groups[s["group"]]
    q = " ".join([s["slug"], s["en"], s["zh"], g["name"]["en"], g["name"]["zh"]] +
                 [s["text"][k][l] for k in ("what", "for") for l in ("en", "zh")]).lower()
    return f"""<a class="card{extra_cls}" href="{up}{s['slug']}/" data-slug="{s['slug']}" data-q="{esc(q)}" style="--a1:{s['palette'][0]};--a2:{s['palette'][2]}">
  <span class="pic"><img src="{up}media/{s['slug']}/{CARD}.jpg" width="{STILL_W}" height="{STILL_H}" loading="lazy" decoding="async" alt=""><i class="tick"></i></span>
  <span class="cap"><b>{name(s)}</b><small>{gloss(s)}</small></span>
  <span class="for">{bi(esc(s['text']['for']['en']), esc(s['text']['for']['zh']))}</span>
  <span class="chips" aria-hidden="true">{chips(s)}</span>
</a>"""


def overview(styles, groups):
    total = len(styles)
    up = ""
    data = [{"s": s["slug"], "en": s["en"], "zh": s["zh"], "g": s["group"], "p": s["palette"][:3]} for s in styles]
    gdata = [{"en": g["name"]["en"], "zh": g["name"]["zh"]} for g in groups]
    blob = json.dumps({"loop": LOOP, "styles": data, "groups": gdata}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    rack = "".join(
        f'<a class="sl" href="{s["slug"]}/" tabindex="-1" data-i="{i}"><img src="../img/styles/{s["slug"]}.jpg" width="384" height="216" alt="" decoding="async"></a>'
        for i, s in enumerate(styles))
    first = styles[0]
    nav = "".join(f'<a href="#{g["id"]}" data-g="{g["id"]}">{bi(esc(g["name"]["en"]), esc(g["name"]["zh"]))}<small>{len(g["slugs"])}</small></a>'
                  for g in groups)
    sections = []
    for gi, g in enumerate(groups):
        cards = "\n".join(card(s, up, groups) for s in styles if s["group"] == gi)
        sections.append(f"""<section class="group" id="{g['id']}" data-g="{g['id']}">
  <header class="ghead" data-r><span class="gnum">{gi + 1:02d}</span><h2>{bi(esc(g['name']['en']), esc(g['name']['zh']))}</h2><p>{bi(esc(g['line']['en']), esc(g['line']['zh']))}</p><span class="gcount"><span class="gc">{len(g['slugs'])}</span></span></header>
  <div class="cards">
{cards}
  </div>
</section>""")
    search = (f'<label class="search"><svg viewBox="0 0 20 20" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.5"/><path d="M13 13l4.5 4.5"/></svg>'
              f'<input id="q" type="search" autocomplete="off" spellcheck="false" data-ph-en="Search by name or use: ink, data, launch…" '
              f'data-ph-zh="搜名字或用途：水墨、数据、发布片…" aria-label="Search styles"><kbd>/</kbd></label>')
    return (head(f"Styles · OpenVideoHarness", "风格库 · OpenVideoHarness",
                 f"{total} video styles, each a real 5-second render of the same content. {total} 种视频风格，每种都是同一段内容的 5 秒实渲样片。", up)
            + f"""<body class="overview">
<div class="amb" aria-hidden="true"></div>
{topbar(up, '')}
<main>
<section class="intro">
  <p class="eyebrow" data-r><b></b>{bi('Style library', '风格库')}<span class="sep"></span><span lang="en"><span data-n="styles">{total}</span> styles</span><span lang="zh"><span data-n="styles">{total}</span> 种风格</span></p>
  <div class="intro-head">
    <h1 class="rise">{bi(f'One sentence. <em>{total} ways to draw it.</em>', f'同一句话，<em>{total} 种画法。</em>')}</h1>
    <p class="lede rise">{bi(f'All {total} samples play the same five seconds, on one clock. Move across the strip and it is like changing channels: the story keeps going, only the look changes.',
                            f'{total} 段样片演的是同一段 5 秒，走的是同一个时钟。在下面这一排上横着移动，就像换台：故事接着往下走，换的只是画法。')}</p>
  </div>
  <div class="rack" id="rack" tabindex="0" role="group" data-aria-en="All {total} styles. Left and right arrows to change, Enter to open" data-aria-zh="全部 {total} 种风格。左右键切换，回车打开" aria-label="All {total} styles">
    <div class="frame" aria-hidden="true"><img src="media/{first['slug']}/{CARD}.jpg" width="{STILL_W}" height="{STILL_H}" alt=""><video muted playsinline loop preload="none"></video></div>
    <div class="slices">{rack}</div>
    <i class="ph" aria-hidden="true"></i>
  </div>
  <div class="now" aria-live="polite">
    <span class="idx"><b id="nIdx">01</b> / {total}</span>
    <a class="nm" id="nName" href="{first['slug']}/"><b>{name(first)}</b><small>{gloss(first)}</small><span class="go" aria-hidden="true">→</span></a>
    <span class="grp" id="nGroup">{bi(esc(groups[first['group']]['name']['en']), esc(groups[first['group']]['name']['zh']))}</span>
    <span class="clock" aria-hidden="true"><span class="tc" id="tc">t = 0.00 s</span><span class="ruler"><i id="tph"></i></span></span>
  </div>
</section>
<nav class="gnav" id="gnav" aria-label="Groups">{search}<span class="gl">{nav}</span><span class="found" id="found" aria-live="polite"></span></nav>
{chr(10).join(sections)}
<p class="empty" id="empty" hidden>{bi('No style matches. Try a use, like “history” or “launch”.', '没有找到。换个用途试试，比如“历史”“发布”。')}</p>
<footer class="foot">
  <p>{bi(f'Every sample is a real render made with this repo’s own tools: one script, {total} sets of style rules. Each style is a reference, not a template: borrow one, mix several, or ignore them all.',
          f'每段样片都是用本仓库的工具真渲的：同一份脚本，换 {total} 套风格规则。风格是参考，不是模板：借一种、混几种，或者都不用。')}</p>
  <p class="links"><a href="../">{bi('← The homepage', '← 回到主页')}</a><a href="{REPO}/blob/main/styles/README.md" target="_blank" rel="noopener">{bi('How the styles are written ↗', '风格库的说明 ↗')}</a></p>
</footer>
</main>
<script type="application/json" id="styles-data">{blob}</script>
</body>
</html>
""")


def page(s, styles, groups):
    up = "../"
    root = "../../../../"
    g = groups[s["group"]]
    total = len(styles)
    by = {o["slug"]: o for o in styles}
    prev = styles[(s["n"] - 2) % total]
    nxt = styles[s["n"] % total]
    t = s["text"]
    stills = "".join(
        f'<button class="still" type="button" data-t="{tt}"><img src="{up}media/{s["slug"]}/{i}.jpg" width="{STILL_W}" height="{STILL_H}" loading="lazy" decoding="async" alt="">'
        f'<span>t = {tt:.1f} s</span></button>' for i, tt in enumerate(STILL_T, 1))
    marks = "".join(f'<i style="left:{tt / LOOP * 100:.0f}%"></i>' for tt in STILL_T)
    asks = []
    for lang in ("en", "zh"):
        a, blank, b = split_ask(t["ask"][lang])
        o, c = ("[", "]") if lang == "en" else ("〔", "〕")
        inner = esc(a) + (f'<input class="blank" type="text" placeholder="{esc(blank)}" data-o="{o}" data-c="{c}" size="{max(4, len(blank))}" aria-label="{esc(blank)}">' if blank else "") + esc(b)
        asks.append(f'<p class="sentence" lang="{lang}">{inner}</p>')
    pal_labels = [("Background", "底色"), ("Text", "文字"), ("Accent", "强调")]
    pal = "".join(
        f'<button class="sw" type="button" data-hex="{c}" style="--c:{c}"><i></i><code>{c}</code>'
        + (f'<small>{bi(*pal_labels[i])}</small>' if i < 3 else "<small></small>") + "</button>"
        for i, c in enumerate(s["palette"]))
    fonts = "".join(f'<div><dt>{bi(en, zh)}</dt><dd>{" → ".join(esc(f) for f in fam)}</dd></div>' for en, zh, fam in s["fonts"])
    near = "\n".join(card(by[x], up, groups) for x in s["near"])
    hero_poster = f"{root}styles/{s['slug']}/media/poster.jpg"
    return (head(f"{s['en']} · Styles · OpenVideoHarness", f"{s['zh']} · 风格库 · OpenVideoHarness",
                 f"{s['en']} / {s['zh']}: {t['what']['en']}", up)
            + f"""<body class="style" data-slug="{s['slug']}" style="--a1:{s['palette'][0]};--a2:{s['palette'][2]}">
<div class="amb" aria-hidden="true"></div>
<i class="wipeline" aria-hidden="true"></i>
{topbar(up, f'<nav class="pn" aria-label="Styles"><a rel="prev" href="../{prev["slug"]}/" data-aria-en="Previous: {esc(prev["en"])}" data-aria-zh="上一个：{esc(prev["zh"])}" aria-label="Previous: {esc(prev["en"])}">←</a><span><b>{s["n"]:02d}</b> / {total}</span><a rel="next" href="../{nxt["slug"]}/" data-aria-en="Next: {esc(nxt["en"])}" data-aria-zh="下一个：{esc(nxt["zh"])}" aria-label="Next: {esc(nxt["en"])}">→</a></nav>')}
<main>
<section class="hero">
  <div class="hero-text">
    <p class="eyebrow rise"><b></b><a href="../#{g['id']}">{s['group'] + 1:02d} {bi(esc(g['name']['en']), esc(g['name']['zh']))}</a></p>
    <h1 class="rise">{name(s)}</h1>
    <p class="gloss rise">{gloss(s)}</p>
    <p class="what rise">{bi(esc(t['what']['en']), esc(t['what']['zh']))}</p>
    <p class="for rise"><span class="k">{bi('Good for', '适合')}</span>{bi(esc(t['for']['en']), esc(t['for']['zh']))}</p>
    <p class="rise"><a class="btn" href="#ask">{bi('A sentence to give your agent', '交给 agent 的一句话')}<span class="arrow" aria-hidden="true">↓</span></a></p>
  </div>
  <figure class="player">
    <div class="screen" id="screen">
      <video id="v" muted playsinline loop preload="none" poster="{hero_poster}" src="{root}styles/{s['slug']}/media/swatch.mp4"></video>
      <button class="big" id="big" type="button" data-aria-en="Play" data-aria-zh="播放" aria-label="Play"><span></span></button>
    </div>
    <figcaption class="ctl">
      <button class="pp" id="pp" type="button" data-aria-en="Play or pause" data-aria-zh="播放或暂停" aria-label="Play or pause"><i></i></button>
      <span class="ruler" id="ruler" role="slider" tabindex="0" aria-valuemin="0" aria-valuemax="5" aria-valuenow="0" data-aria-en="Time in the sample" data-aria-zh="样片里的时间" aria-label="Time in the sample">{marks}<b id="rph"></b></span>
      <span class="tc" id="tc">t = 0.00 s</span>
      <button class="snd" id="snd" type="button" aria-pressed="false">{bi('Sound', '声音')}</button>
    </figcaption>
  </figure>
</section>
<section class="block moments" data-r>
  <h2 class="sh"><span>01</span>{bi('Four moments', '四个瞬间')}<i></i><small>{bi('click one to jump there', '点一下跳到那一刻')}</small></h2>
  <div class="stills">{stills}</div>
</section>
<section class="block ask" id="ask" data-r>
  <h2 class="sh"><span>02</span>{bi('Ask for it', '交给 agent')}<i></i></h2>
  <div class="say">{''.join(asks)}</div>
  <p class="row"><button class="btn" id="copy" type="button" data-en="Copy the sentence" data-zh="复制这句话">{bi('Copy the sentence', '复制这句话')}</button>
    <span class="fine">{bi('Fill in the blank, or leave it for the agent to ask. With OpenVideoHarness installed, say it in Claude Code or Codex.', '空格可以填，也可以留给 agent 来问。装好 OpenVideoHarness 后，在 Claude Code 或 Codex 里说这句话。')} <a href="../../#start">{bi('How to install', '怎么安装')}</a></span></p>
</section>
<section class="block spec" data-r>
  <h2 class="sh"><span>03</span>{bi('Colours and type', '色板和字体')}<i></i><small>{bi('click a colour to copy it', '点颜色复制色值')}</small></h2>
  <div class="pal">{pal}</div>
  <dl class="fonts">{fonts}</dl>
  <p class="docs"><a href="{REPO}/blob/main/styles/{s['slug']}/STYLE.md" target="_blank" rel="noopener">{bi('Read its STYLE.md ↗', '读它的 STYLE.md ↗')}</a><span class="fine">{bi('the full grammar: colour, type, motion, transitions, sound, and what to avoid', '完整的写法：色板、字体、运动、转场、声音，还有不该怎么用')}</span></p>
</section>
<section class="block near" data-r>
  <h2 class="sh"><span>04</span>{bi('Close to this one', '相近的风格')}<i></i></h2>
  <div class="cards">
{near}
  </div>
</section>
<footer class="foot">
  <p class="links"><a href="../">{bi(f'← All {total} styles', f'← 全部 {total} 种风格')}</a><a href="../../">{bi('The homepage', '主页')}</a></p>
</footer>
</main>
<script type="application/json" id="style-data">{json.dumps({"loop": LOOP, "stills": STILL_T, "slug": s["slug"]}, separators=(",", ":"))}</script>
</body>
</html>
""")


# ---------------------------------------------------------------- media

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest():
    p = MEDIA / "manifest.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def make_media(styles, force=False):
    man, made = manifest(), []
    ff = shutil.which("ffmpeg")
    for s in styles:
        slug = s["slug"]
        swatch = STYLES / slug / "media" / "swatch.mp4"
        thumb = SITE / "img" / "styles" / f"{slug}.jpg"
        if not thumb.exists() and ff and (STYLES / slug / "media" / "poster.jpg").exists():
            subprocess.run([ff, "-v", "error", "-y", "-i", str(STYLES / slug / "media" / "poster.jpg"), "-vf",
                            "scale=384:216:flags=lanczos", "-q:v", "4", str(thumb)], check=True)
            made.append(str(thumb.relative_to(ROOT)))
        if not swatch.exists():
            continue
        digest = sha(swatch)
        want = {"sample": digest, "t": list(STILL_T), "size": [STILL_W, STILL_H]}
        d = MEDIA / slug
        if not force and man.get(slug) == want and all((d / f"{i}.jpg").exists() for i in range(1, len(STILL_T) + 1)):
            continue
        if not ff:
            print(f"! no ffmpeg: the stills of {slug} were not made", file=sys.stderr)
            continue
        d.mkdir(parents=True, exist_ok=True)
        for i, t in enumerate(STILL_T, 1):
            subprocess.run([ff, "-v", "error", "-y", "-ss", f"{t}", "-i", str(swatch), "-frames:v", "1", "-vf",
                            f"scale={STILL_W}:{STILL_H}:flags=lanczos", "-q:v", "4", str(d / f"{i}.jpg")], check=True)
        man[slug] = want
        made.append(f"docs/site/styles/media/{slug}/")
    MEDIA.mkdir(parents=True, exist_ok=True)
    (MEDIA / "manifest.json").write_text(json.dumps({k: man[k] for k in sorted(man)}, indent=1) + "\n", encoding="utf-8")
    return made


# ---------------------------------------------------------------- the homepage's list

def styles_block(styles, groups):
    lines = []
    for gi, g in enumerate(groups):
        row = ", ".join("['{}', '{}', '{}']".format(s["slug"], s["en"].replace("'", "\\'"), s["zh"]) for s in styles if s["group"] == gi)
        lines.append(f"  {row},   // {g['name']['en']}")
    return ("const STYLES = [   // written by tools/style_site.py from styles/showcase.json: the groups of the style library, in order\n"
            + "\n".join(lines) + "\n];")


STYLES_RE = re.compile(r"const STYLES = \[.*?\n\];", re.S)


def home_with(styles, groups):
    text = HOME.read_text(encoding="utf-8")
    return STYLES_RE.sub(lambda m: styles_block(styles, groups), text, count=1)


# ---------------------------------------------------------------- build and check

def pages(styles, groups):
    out = {OUT / "index.html": overview(styles, groups)}
    for s in styles:
        out[OUT / s["slug"] / "index.html"] = page(s, styles, groups)
    return out


def build(force_stills=False):
    styles, groups, bad = load()
    made = make_media(styles, force_stills)
    want = pages(styles, groups)
    for p, text in want.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_text(encoding="utf-8") != text:
            p.write_text(text, encoding="utf-8")
            made.append(str(p.relative_to(ROOT)))
    for d in OUT.iterdir():   # a style that is gone takes its page and stills with it
        if d.is_dir() and d.name != "media" and (d / "index.html") not in want:
            shutil.rmtree(d)
            made.append(f"removed {d.relative_to(ROOT)}/")
    for d in MEDIA.iterdir():
        if d.is_dir() and d.name not in {s["slug"] for s in styles}:
            shutil.rmtree(d)
            made.append(f"removed {d.relative_to(ROOT)}/")
    home = home_with(styles, groups)
    if home != HOME.read_text(encoding="utf-8"):
        HOME.write_text(home, encoding="utf-8")
        made.append(str(HOME.relative_to(ROOT)) + " (its STYLES list)")
    print(f"{len(styles)} styles in {len(groups)} groups: docs/site/styles/ "
          + ("— wrote " + ", ".join(made[:6]) + (f" and {len(made) - 6} more" if len(made) > 6 else "") if made else "— up to date"))
    for b in bad:
        print("! " + b)
    return 0


LOADS = re.compile(r"<(?:script|img|iframe|embed|object|video|audio|source)\b[^>]*\b(?:src|data|poster)=\"(https?:[^\"]+)\"|"
                   r"<link\b[^>]*\bhref=\"(https?:[^\"]+)\"[^>]*>", re.I)


def page_problems(path, text):
    bad, rel = [], path.relative_to(ROOT)
    for m in re.finditer(r"\b(?:href|src|poster)=\"([^\"]+)\"", text):
        t = m.group(1)
        if t.startswith(("http:", "https:", "mailto:", "data:")) or t.startswith("#"):
            if t.startswith("#") and len(t) > 1 and f'id="{t[1:]}"' not in text:
                bad.append(f"{rel}: links {t}, which is no id on the page")
            continue
        dest = (path.parent / t.partition("#")[0].partition("?")[0]).resolve()
        if not dest.is_relative_to(ROOT) or not dest.exists():
            bad.append(f"{rel}: names {t}, which is not in the repo")
    for m in LOADS.finditer(text):
        link = m.group(0)
        if m.group(2) and not re.search(r"\brel=\"[^\"]*(?:stylesheet|preload|icon|prefetch|preconnect|modulepreload)", link):
            continue
        bad.append(f"{rel}: loads {m.group(1) or m.group(2)} from another site")
    body = text[text.find("<body"):]
    en, zh = (len(re.findall(rf"<\w+\b[^>]*\blang=\"{l}\"", body)) for l in ("en", "zh"))   # a gloss is a pair too
    if en != zh:
        bad.append(f"{rel}: {en} texts in English and {zh} in Chinese: write each in both")
    return bad


def check():
    styles, groups, bad = load()
    want = pages(styles, groups)
    for p, text in want.items():
        rel = p.relative_to(ROOT)
        if not p.exists():
            bad.append(f"{rel}: missing (bin/vh style site writes it)")
        elif p.read_text(encoding="utf-8") != text:
            bad.append(f"{rel}: not what styles/ makes now (bin/vh style site writes it again)")
        bad += page_problems(p, text)
    if OUT.exists():
        for d in OUT.iterdir():
            if d.is_dir() and d.name != "media" and (d / "index.html") not in want:
                bad.append(f"{d.relative_to(ROOT)}/: a page for no style in styles/ (bin/vh style site removes it)")
    man = manifest()
    for s in styles:
        slug = s["slug"]
        swatch = STYLES / slug / "media" / "swatch.mp4"
        if not swatch.exists():
            bad.append(f"styles/{slug}: no media/swatch.mp4, so its page has no sample")
            continue
        missing = [f"{i}.jpg" for i in range(1, len(STILL_T) + 1) if not (MEDIA / slug / f"{i}.jpg").exists()]
        if missing:
            bad.append(f"docs/site/styles/media/{slug}/: no {', '.join(missing)} (bin/vh style site makes them)")
        elif (man.get(slug) or {}).get("sample") != sha(swatch) or man[slug].get("t") != list(STILL_T):
            bad.append(f"docs/site/styles/media/{slug}/: the stills come from another sample (bin/vh style site --stills)")
        if not (SITE / "img" / "styles" / f"{slug}.jpg").exists():
            bad.append(f"docs/site/img/styles/{slug}.jpg: missing (bin/vh style site makes it)")
    if HOME.read_text(encoding="utf-8") != home_with(styles, groups):
        bad.append("docs/site/index.html: its STYLES list is not the style library's groups in order (bin/vh style site writes it)")
    for f in ("showcase.css", "showcase.js"):
        if not (OUT / f).exists():
            bad.append(f"docs/site/styles/{f}: missing")
        else:
            txt = (OUT / f).read_text(encoding="utf-8")
            for u in re.findall(r"(?:url\(\s*[\"']?|@import\s+[\"']?|import\s*\(?\s*[\"'])(https?:[^\"')\s]+)", txt):
                bad.append(f"docs/site/styles/{f}: loads {u} from another site")
    return styles, groups, bad


def main(argv):
    if argv in ([], ["build"]) or argv in (["--stills"], ["build", "--stills"]):
        return build(force_stills="--stills" in argv)
    if argv == ["check"]:
        styles, groups, bad = check()
        if bad:
            print("\n".join(bad))
            return 1
        print(f"the style showcase (docs/site/styles/): {len(styles)} style pages and the overview, as styles/ makes them; "
              f"{len(groups)} groups with every style once; their stills from the current samples; their links in the repo; "
              f"nothing from another site; both languages; the homepage's STYLES in the same order")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
