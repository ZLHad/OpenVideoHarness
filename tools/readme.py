"""The READMEs, their overview diagrams, the installer and the homepage against the repo: the counts they state, the
files they link, the two languages side by side (stdlib only).

usage: python3 tools/readme.py          the counts, from the repo: what to write when one of these pages says one
       python3 tools/readme.py check    the pages in PAGES against the repo (tools/ci.sh)

check reads README.md, README.zh-CN.md, docs/assets/overview.en.svg / overview.zh.svg, install.sh and the homepage
(docs/site/index.html):
  - counts: every phrase like "32 styles" / "32 种风格" (COUNT_PHRASES) states the repo's number, and each page states
    the counts PAGES lists for it, so a reworded sentence cannot leave its number unchecked; install.sh's HyperFrames
    version is the pin in tools/modules.json;
  - links: every relative link and image in the READMEs is a file or folder in the repo, and a #anchor on a markdown
    page is one of that page's headings (GitHub's anchors);
  - the two READMEs: as many sections (##) each, and the same relative links and images once the language is taken out
    of their names (README.zh-CN.md is README.md, docs/research/en/x is docs/research/x, overview.zh.svg is overview.svg);
  - the homepage: each <… data-n="name">N</…> is the count, and its phrases are read as above; its relative links,
    images and #anchors are there; its STYLES are the repo's styles, each with its thumbnail (img/styles/<slug>.jpg) and
    sample, its Chinese name the one in STYLE.md's title; as many lang="en" texts as lang="zh"; nothing from another
    site loads with the page (a stylesheet, script, font, image or frame; a film's <source> waits for play).
Links to the web are not fetched (CI runs offline). Exit status: 0 all good, 1 a problem (each said), 2 usage.
"""
import ast, json, os, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

EN_WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
ZH_DIGITS = {c: i for i, c in enumerate("零一二三四五六七八九")} | {"两": 2, "十": 10}


def number(word):
    """'32', 'five' or '五' → 32, 5, 5; None when it is not a number this checker reads."""
    w = word.strip().lower()
    if w.isdigit():
        return int(w)
    if w in EN_WORDS:
        return EN_WORDS[w]
    if w and all(c in ZH_DIGITS for c in w):   # 五, 十, 十四, 三十七
        if w == "十":
            return 10
        if "十" in w:
            tens, _, ones = w.partition("十")
            return (ZH_DIGITS[tens] if tens else 1) * 10 + (ZH_DIGITS[ones] if ones else 0)
        return ZH_DIGITS[w] if len(w) == 1 else None
    return None


# ── the counts, from the repo ──────────────────────────────────────────────────────────────────────────────────────

def _section_lines(path, start, stop):
    """The lines of a markdown file from the heading `start` up to the next heading of its level (`stop` a prefix)."""
    out, on = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(start):
            on = True
            continue
        if on and line.startswith(stop):
            break
        if on:
            out.append(line)
    return out


def counts():
    import recipes   # tools/recipes.py: the library's own loader (recipe, sequence and grammar cards by their kind)
    kinds = {}
    for _, fm in recipes.load_library().values():
        k = fm.get("kind", "recipe")
        kinds[k] = kinds.get(k, 0) + 1
    sfx_lib = None
    for node in ast.walk(ast.parse((ROOT / "tools/audio/sfx.py").read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "LIB" for t in node.targets) and isinstance(node.value, ast.Dict):
            sfx_lib = len(node.value.keys)
    checklist = _section_lines(ROOT / "templates/TASTE_CHECKLIST.md", "## 检查项", "## ")
    scoring = _section_lines(ROOT / "templates/TASTE_CHECKLIST.md", "## 打分层", "## ")
    table = []
    for line in scoring:   # the eight dimensions: the rows of the table whose header starts with | 维度 |
        if line.strip().startswith("| 维度 |"):
            table = ["in"]
        elif table and line.strip().startswith("|") and not line.strip().startswith("|---"):
            table.append(line)
        elif table and table[0] == "in" and len(table) > 1 and not line.strip().startswith("|"):
            break
    fetch = (ROOT / "references/fetch.sh").read_text(encoding="utf-8")
    engine_rows = _section_lines(ROOT / "README.md", "### Engines", "##")
    return {
        "commands": len(json.loads((ROOT / "tools/commands.json").read_text(encoding="utf-8"))["commands"]),
        "styles": sum(1 for p in (ROOT / "styles").glob("*/STYLE.md") if not p.parent.name.startswith("_")),
        "recipes": kinds.get("recipe", 0),
        "sequences": kinds.get("sequence", 0),
        "grammar": kinds.get("grammar", 0),
        "components": sum(1 for p in (ROOT / "components").glob("*/slots.json")),
        "showcase": sum(1 for p in (ROOT / "showcase").glob("*/README.md")),
        "types": sum(1 for p in (ROOT / "video-types").glob("[0-9][0-9]-*.md")),
        "cases": sum(1 for p in (ROOT / "cases").glob("*.md") if p.name != "README.md"),
        "playbook": sum(1 for p in (ROOT / "playbook").glob("[0-9][0-9]-*.md")),
        "templates": sum(1 for p in (ROOT / "templates").glob("*.md")),
        "refs": len(re.findall(r"^(?:full|sparse|textonly)\s+\S+/\S+\s+\S+", fetch, re.M)),
        "modules": len(json.loads((ROOT / "tools/modules.json").read_text(encoding="utf-8"))["modules"]),
        "sfx": sfx_lib or 0,
        "checklist": sum(1 for line in checklist if re.match(r"\d+\. ", line)),
        "scores": len(table) - 1 if table else 0,
        "engines": sum(1 for line in engine_rows if line.startswith("| ") and not line.startswith(("| Engine ", "|---"))),
    }


WHAT = {   # what each count is, for the listing
    "commands": "bin/vh commands (tools/commands.json)",
    "styles": "style presets (styles/<slug>/STYLE.md)",
    "recipes": "shot recipes (recipes/<family>/, kind recipe)",
    "sequences": "whole-film skeletons (recipes/sequences/, kind sequence)",
    "grammar": "shot-grammar cards (recipes/shot/, kind grammar)",
    "components": "motion components (components/<name>/slots.json)",
    "showcase": "showcase films (showcase/<film>/README.md)",
    "types": "video types (video-types/NN-*.md)",
    "cases": "case studies (cases/*.md but README.md)",
    "playbook": "playbook docs (playbook/NN-*.md)",
    "templates": "project templates (templates/*.md)",
    "refs": "read-only reference repos (references/fetch.sh)",
    "modules": "outside modules (tools/modules.json)",
    "sfx": "built-in synthesized sound effects (tools/audio/sfx.py LIB)",
    "checklist": "taste checklist items (templates/TASTE_CHECKLIST.md 检查项)",
    "scores": "scoring dimensions (templates/TASTE_CHECKLIST.md 打分层)",
    "engines": "engines (the rows of README.md's engine table)",
}

# ── where the pages state them ─────────────────────────────────────────────────────────────────────────────────────
# Each phrase captures a number (digits, or an English or Chinese number word); every match must be the count. Keep a
# phrase narrow enough that it cannot catch another number (第 09 类 is a type's number, not the count of types).
N = r"(\d+|[a-z]+|[零一二两三四五六七八九十]+)"
COUNT_PHRASES = {   # "Run these two commands" is not a count of bin/vh's: commands and components need their word
    "commands": [rf"\ball {N} commands\b", rf"\b{N} `?bin/vh`? commands\b", rf"bin/vh: {N} commands\b",
                 rf"全部 {N} 条命令", rf"{N} 条 ?`?bin/vh`? ?命令", rf"bin/vh：{N} 条命令"],
    "styles": [rf"\b{N} styles\b", rf"\b{N}-style\b", rf"{N} 种风格"],
    "recipes": [rf"\b{N} shot recipes\b", rf"{N} 张镜头配方"],
    "sequences": [rf"\b{N} whole-film skeletons\b", rf"{N} 条全片骨架"],
    "grammar": [rf"\b{N} shot-grammar cards\b", rf"{N} 张镜头语法卡"],
    "components": [rf"\b{N} motion components\b", rf"{N} 个动效组件"],
    "showcase": [rf"\b{N} showcase films\b", rf"{N} 支样片"],
    "types": [rf"\b{N} video types\b", rf"(?<!第 ){N} 类视频"],
    "cases": [rf"\b{N} case studies\b", rf"\b{N} cases\b", rf"{N} 个案例"],
    "playbook": [rf"\b{N} playbook docs\b", rf"{N} 篇 playbook"],
    "templates": [rf"\b{N} project templates\b", rf"{N} 个项目模板"],
    "refs": [rf"\b{N} (?:read-only )?reference repos\b", rf"{N} 个(?:只读的?)?参考仓库"],
    "modules": [rf"\b{N} outside (?:programs|modules)\b", rf"{N} 个外接模块"],
    "sfx": [rf"\b{N} sound effects\b", rf"{N} 个(?:用代码合成的|代码合成的)?音效"],
    "checklist": [rf"\b{N}-point checklist\b", rf"{N} 条的?清单"],
    "scores": [rf"\bon {N} points\b", rf"按 {N} 项打分"],
    "engines": [rf"\b{N} engines\b", rf"{N} 个引擎"],
}

PAGES = {   # page: the counts it must state somewhere (each is also checked wherever else it appears)
    "README.md": ["commands", "styles", "recipes", "sequences", "grammar", "components", "showcase", "types", "cases",
                  "refs", "modules", "sfx", "checklist", "scores"],
    "README.zh-CN.md": ["commands", "styles", "recipes", "sequences", "grammar", "components", "showcase", "types", "cases",
                        "refs", "modules", "sfx", "checklist", "scores"],
    "docs/assets/overview.en.svg": ["types", "playbook", "styles", "recipes", "components", "cases", "refs", "commands"],
    "docs/assets/overview.zh.svg": ["types", "playbook", "styles", "recipes", "components", "cases", "refs", "commands"],
    "install.sh": [],   # counts the reference repos as it runs; a number written into it is checked all the same
    "docs/site/index.html": ["types", "styles", "commands", "engines", "recipes", "sequences", "grammar", "components",
                             "showcase", "cases", "playbook", "templates", "refs", "modules", "sfx", "checklist", "scores"],
}
SITE = "docs/site/index.html"
READMES = ("README.md", "README.zh-CN.md")


def blank(m):
    """A match replaced by its newlines alone, so the lines after it keep their numbers."""
    return "\n" * m.group(0).count("\n")


def visible_text(path, text):
    """The text a reader sees: a markdown page without its fenced code and HTML comments (line numbers kept); an SVG's
    <text> runs, one a line."""
    if path.suffix == ".svg":
        return "\n".join(re.sub(r"<[^>]+>", "", t) for t in re.findall(r"<text\b[^>]*>(.*?)</text>", text, re.S)).replace("&amp;", "&")
    if path.suffix == ".html":   # its words: no script, style or comments; a block's end is a space, inline tags nothing
        text = re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", blank, text, flags=re.S | re.I)
        text = re.sub(r"</?(?:p|div|li|ul|ol|h[1-6]|section|header|footer|nav|figure|figcaption|summary|details|button|td|th|tr|br|dt|dd|article)\b[^>]*>", " ", text, flags=re.I)
        return re.sub(r"<[^>]+>", "", text).replace("&amp;", "&").replace("&nbsp;", " ")
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    return re.sub(r"^```.*?^```", blank, text, flags=re.S | re.M)


def count_problems(have):
    bad = []
    for page, required in PAGES.items():
        p = ROOT / page
        if not p.is_file():
            bad.append(f"{page}: not there")
            continue
        raw = p.read_text(encoding="utf-8")
        text = visible_text(p, raw)
        tagged = set(re.findall(r"\bdata-n=\"(\w+)\"", re.sub(r"<!--.*?-->", "", raw, flags=re.S))) if p.suffix == ".html" else set()
        for key, phrases in COUNT_PHRASES.items():
            seen = [have[key]] if key in tagged else []   # a data-n element states it (site_problems checks its value)
            for pat in phrases:
                for m in re.finditer(pat, text, re.I):
                    n = number(m.group(1))
                    if n is None:
                        continue
                    seen.append(n)
                    if n != have[key]:
                        where = "a <text>" if p.suffix == ".svg" else f"line {text.count(chr(10), 0, m.start()) + 1}"
                        bad.append(f"{page} ({where}): \"{m.group(0)}\", but the repo has {have[key]} {WHAT[key]}")
            if key in required and not seen:
                bad.append(f"{page}: states no count of {WHAT[key]} (a phrase in tools/readme.py COUNT_PHRASES: "
                           f"{' or '.join(phrases)}); say it, or take it out of PAGES")
    return bad


def pin_problems():
    """install.sh names the HyperFrames version it installs: the one tools/modules.json pins."""
    mods = json.loads((ROOT / "tools/modules.json").read_text(encoding="utf-8"))["modules"]
    pin = next(m for m in mods if m["name"] == "hyperframes")["version"]["pin"]
    text = (ROOT / "install.sh").read_text(encoding="utf-8")
    return [f"install.sh: HyperFrames {v}, but tools/modules.json pins {pin}"
            for v in re.findall(r"HyperFrames (\d+\.\d+\.\d+)", text) if v != pin]


# ── links ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def strip_inline(s):
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)        # links and images: their text
    s = re.sub(r"<[^>]+>", "", s)                            # inline HTML
    return s.replace("`", "").replace("*", "")


def anchors(path):
    """GitHub's anchors for a markdown page's headings: lowercase, punctuation and symbols but - and _ dropped, spaces
    to -, a repeat numbered -1, -2 …"""
    out, seen, fence = set(), {}, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else re.match(r"#{1,6}\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        s = "".join(c for c in strip_inline(m.group(1)).strip().lower()
                    if c in "-_ " or not unicodedata.category(c)[0] in "PS").replace(" ", "-")
        k = seen.get(s, 0)
        seen[s] = k + 1
        out.add(s if k == 0 else f"{s}-{k}")
    return out


def links(text):
    """The link and image targets of a markdown page (markdown and HTML), outside fenced code."""
    text = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    found = re.findall(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", text)
    found += re.findall(r"\b(?:href|src)=\"([^\"]+)\"", text)
    return found


def local(target):
    return not re.match(r"[a-z][a-z0-9+.-]*:", target, re.I)   # http:, https:, mailto:, data: … are not files here


def link_problems(page):
    bad = []
    p = ROOT / page
    for t in links(p.read_text(encoding="utf-8")):
        if not local(t):
            continue
        path, _, frag = t.partition("#")
        dest = Path(os.path.normpath(p.parent / path)) if path else p   # lexical: a link may not climb out of the repo
        if not dest.is_relative_to(ROOT) or not dest.exists():
            bad.append(f"{page}: links {t}, which is not in the repo")
            continue
        if frag and dest.is_file() and dest.suffix == ".md" and frag not in anchors(dest):
            bad.append(f"{page}: links {t}, but {dest.relative_to(ROOT)} has no heading with that anchor")
    return bad


def same_file(target):
    """A relative target with its language taken out, for comparing the two READMEs."""
    t = target.partition("#")[0]
    t = re.sub(r"(^|/)README(?:\.zh-CN)?\.md$", r"\1", t)
    t = t.replace("docs/research/en/", "docs/research/")
    t = re.sub(r"\.(?:en|zh)\.(svg|png|jpg)$", r".\1", t)
    return t.rstrip("/") or "."


def pair_problems():
    a, b = ((ROOT / r).read_text(encoding="utf-8") for r in READMES)
    bad = []
    h2 = [len(re.findall(r"^## ", re.sub(r"^```.*?^```", "", x, flags=re.S | re.M), re.M)) for x in (a, b)]
    if h2[0] != h2[1]:
        bad.append(f"{READMES[0]} has {h2[0]} sections (##), {READMES[1]} {h2[1]}: write each in both")
    la = {same_file(t) for t in links(a) if local(t)}
    lb = {same_file(t) for t in links(b) if local(t)}
    for name, only in ((READMES[0], la - lb), (READMES[1], lb - la)):
        if only:
            bad.append(f"only {name} links {', '.join(sorted(only))}")
    return bad


LOADS_WITH_PAGE = ("stylesheet", "preload", "modulepreload", "preconnect", "dns-prefetch", "prefetch", "icon")


def site_problems(have):
    """The homepage: its data-n counts, links and anchors, style wall, languages, and nothing from elsewhere at load."""
    page = ROOT / SITE
    html = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), page.read_text(encoding="utf-8"), flags=re.S)
    base, bad = page.parent, []
    fetched = {line.split()[0] for line in (ROOT / "tools/media.txt").read_text(encoding="utf-8").splitlines()
               if line.strip() and not line.startswith("#")}   # films tools/fetch_media.sh puts back (git leaves them out)
    for m in re.finditer(r"<(\w+)\b[^>]*\bdata-n=\"(\w*)\"[^>]*>(.*?)</\1>", html, re.S):
        key, text = m.group(2), re.sub(r"<[^>]+>", "", m.group(3)).strip()
        line = html.count("\n", 0, m.start()) + 1
        if key not in have:
            bad.append(f"{SITE} (line {line}): data-n=\"{key}\" is no count tools/readme.py knows ({', '.join(have)})")
        elif number(text) != have[key]:
            bad.append(f"{SITE} (line {line}): data-n=\"{key}\" says {text!r}, but the repo has {have[key]} {WHAT[key]}")
    ids = set(re.findall(r"\bid=\"([^\"]+)\"", html))
    for m in re.finditer(r"\b(?:href|src|data-src|poster)=\"([^\"]+)\"", html):
        t = m.group(1)
        if t.startswith("#"):
            if t != "#" and t[1:] not in ids:
                bad.append(f"{SITE}: links {t}, which is no id on the page")
            continue
        if not local(t):
            continue
        dest = Path(os.path.normpath(base / t.partition("#")[0].partition("?")[0]))
        if not dest.is_relative_to(ROOT) or not (dest.exists() or str(dest.relative_to(ROOT)) in fetched):
            bad.append(f"{SITE}: links {t}, which is not in the repo (nor in tools/media.txt)")
    block = re.search(r"const STYLES = \[(.*?)\];", html, re.S)
    listed = re.findall(r"\['([a-z0-9-]+)', '([^']*)', '([^']*)'\]", block.group(1)) if block else []
    repo = {p.parent.name: p for p in (ROOT / "styles").glob("*/STYLE.md") if not p.parent.name.startswith("_")}
    names = {slug for slug, _, _ in listed}
    if not listed:
        bad.append(f"{SITE}: no STYLES list of [slug, English, Chinese] found")
    for slug in sorted(set(repo) - names):
        bad.append(f"{SITE}: STYLES leaves out the style {slug} (add it, with img/styles/{slug}.jpg: see docs/site/README.md)")
    for slug, _, zh in listed:
        if slug not in repo:
            bad.append(f"{SITE}: STYLES lists {slug}, which is no style in styles/")
            continue
        title = repo[slug].read_text(encoding="utf-8").splitlines()[0]
        want = re.sub(r"^#\s*", "", title).split(" · ")[0].strip()
        if zh != want:
            bad.append(f"{SITE}: STYLES names {slug} {zh!r}, but its STYLE.md calls it {want!r}")
        for f in (base / "img" / "styles" / f"{slug}.jpg", ROOT / "styles" / slug / "media" / "swatch.mp4"):
            if not f.is_file():
                bad.append(f"{SITE}: the style {slug} has no {f.relative_to(ROOT)}")
    body = html[html.find("<body"):]
    en, zh = len(re.findall(r"\blang=\"en\"", body)), len(re.findall(r"\blang=\"zh\"", body))
    if en != zh:
        bad.append(f"{SITE}: {en} texts in English and {zh} in Chinese: write each in both")
    outside = [f"<{m.group(1)}> {m.group(3)}" for m in re.finditer(r"<(script|img|iframe|embed|object)\b[^>]*\b(src|data)=\"(https?:[^\"]+)\"", html, re.I)]
    for m in re.finditer(r"<link\b([^>]*)>", html, re.I):
        rel = re.search(r"\brel=\"([^\"]+)\"", m.group(1))
        href = re.search(r"\bhref=\"(https?:[^\"]+)\"", m.group(1))
        if href and rel and set(rel.group(1).lower().split()) & set(LOADS_WITH_PAGE):
            outside.append(f"<link rel={rel.group(1)}> {href.group(1)}")
    for css in re.findall(r"<style\b[^>]*>(.*?)</style>", html, re.S | re.I):
        outside += [f"CSS {u}" for u in re.findall(r"(?:url\(\s*[\"']?|@import\s+[\"']?)(https?:[^\"')\s]+)", css)]
    bad += [f"{SITE}: loads {o} with the page (keep it in the repo, or load it on a click)" for o in outside]
    return bad


def check():
    have = counts()
    bad = [f"tools/readme.py: the repo has no {WHAT[k]}" for k, v in have.items() if not v]
    bad += count_problems(have) + pin_problems() + site_problems(have)
    for page in READMES:
        bad += link_problems(page)
    bad += pair_problems()
    return bad


def main(argv):
    if argv in ([], ["counts"]):
        for k, v in counts().items():
            print(f"{v:5}  {WHAT[k]}")
        return 0
    if argv == ["check"]:
        bad = check()
        if bad:
            print("\n".join(bad))
            return 1
        have = counts()
        print(f"the READMEs, the overview diagrams, install.sh and the homepage: {len(have)} counts as the repo has them "
              f"({have['commands']} commands, {have['styles']} styles, {have['recipes']} recipes …) and the HyperFrames pin; "
              f"their links in the repo; the READMEs side by side; the homepage's styles, both languages, no outside loads")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
