"""Review page: out/review/gate-<n>.json -> a local HTML page a human can look at and listen to.

usage: python3 tools/review.py <project> [gate]
  <project>  the project directory (or a folder name under projects/)
  [gate]     1 | 2 | 3 | E0-E5 | 2b ...  reads out/review/gate-<gate>.json; default: the newest gate-*.json

Writes out/review/gate-<gate>.html, and the same page as out/review/index.html (always the latest page), then prints
the chat message: the decisions, the reply that takes every recommendation, and the path of gate-<gate>.html, which
a later page does not overwrite. Nothing else goes into the chat.
Paths in the JSON are relative to the project; the page links them relatively, so it opens straight from disk
(images, GIF, mp4 and audio play in the browser). templates/REVIEW.md explains the page and every field:

  gate, summary, decisions[{id, question, options[{id, label, pro, con} | "id"], recommend, why, cost, reply}],
  assets[{path, caption, for, t0, t1}], least_sure[{id, note}], animatic,
  segments[{id, title, t0, t1, note, shots[{id, t0, t1, frame, see, vo, note}]}], appendix[{title, text, path}]
  optional: title, lang (zh | en), decided[], delegated[], not_reviewed

The page, top to bottom: the decisions (at most 3, each with a recommendation and a reply), the pictures and options
for each decision, other material, one page per storyboard segment (keyframes, the segment's stretch of the animatic,
least-sure shots flagged, a per-shot table that passes by default), then a folded appendix. Light and dark themes
follow the system; the button or ?theme=dark|light overrides.

Exit: 0 written · 1 written, but the page breaks a rule (more than 3 decisions, a decision without a recommendation
or a reply, a missing file, an unknown `for`, a duplicate id) · 2 nothing written (no project, no JSON, bad JSON, or a
field of the wrong shape).
"""
import argparse, html, json, os, re, sys
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
IMG = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}
VID = {".mp4", ".webm", ".mov", ".m4v"}
AUD = {".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac", ".opus"}
MAX_DECISIONS, MAX_SHOTS = 3, 6

GATES = {"1": ("关卡 ① 大纲", "Gate ① outline"), "2": ("关卡 ② 分镜", "Gate ② storyboard"),
         "3": ("关卡 ③ 初版", "Gate ③ first draft"), "E0": ("检查点 E0 样帧", "Checkpoint E0 style frames"),
         "E1": ("检查点 E1 脚本", "Checkpoint E1 script"), "E2": ("检查点 E2 锁时", "Checkpoint E2 timing lock"),
         "E3": ("检查点 E3 样板章", "Checkpoint E3 sample chapter"), "E4": ("检查点 E4 声音", "Checkpoint E4 sound"),
         "E5": ("检查点 E5 锁画面", "Checkpoint E5 picture lock")}

T = {
    "zh": dict(html_lang="zh-CN", decide="要你定的 {n} 件事", nothing="这一页没有要你定的事：看一眼，回“通过”，或写要改的。",
               look="这一页只给你过目", rec="推荐", reply="回", take_all="照推荐回复", copy="复制", copied="已复制",
               rest="其余默认通过；要改哪一镜，写“{shot} 改：……”。", rest_plain="其余默认通过，只写要改的。",
               least="我最没把握的", decided="已经定了", delegated="我替你定了", not_reviewed="这页不审",
               decision="决定 {i}", options="选项", pro="好处", con="代价", other="其他材料",
               seg="分镜 {i}/{n}", shots="{n} 镜", avg="平均 {s} s/镜", unsure="没把握",
               shot="镜头", dur="时长", vo="旁白", see="看到什么", status="状态", ok="通过",
               pass_all="默认全部通过，只写要改的：“{shot} 改：……”。", clip="这一段动起来的样子",
               appendix="附录：不影响拍板的细节", others="其他审阅页", src="由 bin/vh review 从 {src} 生成",
               theme="切换深色 / 浅色", nav_decide="决定", nav_other="材料", nav_appendix="附录",
               page="页面", chat_head="{title} · 要你定 {n} 件事", chat_none="{title} · 没有要你定的事，看一眼，回“通过”或写要改的。",
               chat_item="{i}. {q} 回 {reply}\n   推荐 {r}{why}", chat_all="照推荐就回：{all}。其余默认通过。",
               why="：{w}", sep="；", colon="："),
    "en": dict(html_lang="en", decide="{n} thing(s) for you to decide", nothing="Nothing to decide on this page: take a look, then reply “ok” or say what to change.",
               look="Just for a look", rec="Recommended", reply="Reply", take_all="Take every recommendation", copy="Copy", copied="Copied",
               rest="Everything else passes by default; to change a shot, write “{shot} change: …”.", rest_plain="Everything else passes by default; only write what to change.",
               least="Least sure about", decided="Already decided", delegated="Decided for you", not_reviewed="Not reviewed here",
               decision="Decision {i}", options="Options", pro="Pro", con="Cost", other="Other material",
               seg="Storyboard {i}/{n}", shots="{n} shots", avg="{s} s per shot", unsure="unsure",
               shot="Shot", dur="Length", vo="Narration", see="On screen", status="Status", ok="ok",
               pass_all="Every shot passes by default; only write what to change: “{shot} change: …”.", clip="This segment in motion",
               appendix="Appendix: details that don't change the decisions", others="Other review pages", src="Built by bin/vh review from {src}",
               theme="Toggle dark / light", nav_decide="Decisions", nav_other="Material", nav_appendix="Appendix",
               page="Page", chat_head="{title} · {n} thing(s) for you to decide", chat_none="{title} · nothing to decide; take a look and reply “ok” or say what to change.",
               chat_item="{i}. {q} Reply {reply}\n   Recommended: {r}{why}", chat_all="To take every recommendation, reply: {all}. Everything else passes by default.",
               why=" — {w}", sep="; ", colon=": "),
}

CSS = """
:root{color-scheme:light;--bg:#f6f4ef;--card:#fff;--ink:#1d1f23;--muted:#6b6760;--line:#e3dfd5;--soft:#efebe2;
--acc:#2456c9;--acc-soft:#e7edfb;--flag:#c93a27;--flag-soft:#fbe8e3;--ok:#2e7d4f;--code:#f0ece3}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--bg:#131518;--card:#1b1e22;--ink:#e9e7e2;
--muted:#9c978e;--line:#2d3137;--soft:#23272c;--acc:#86a8ff;--acc-soft:#1e2a44;--flag:#ff735e;--flag-soft:#3a211d;--ok:#5cc98a;--code:#262a30}}
:root[data-theme=dark]{color-scheme:dark;--bg:#131518;--card:#1b1e22;--ink:#e9e7e2;--muted:#9c978e;--line:#2d3137;--soft:#23272c;
--acc:#86a8ff;--acc-soft:#1e2a44;--flag:#ff735e;--flag-soft:#3a211d;--ok:#5cc98a;--code:#262a30}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB",
"Noto Sans CJK SC","Microsoft YaHei","Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
.wrap{max-width:1160px;margin:0 auto;padding:0 28px}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
code{font:0.9em ui-monospace,"SF Mono",Menlo,monospace;background:var(--code);padding:1px 6px;border-radius:5px}
header{padding:22px 0 6px}
.eyebrow{display:flex;justify-content:space-between;align-items:center;gap:12px;color:var(--muted);font-size:13.5px}
#theme{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;width:34px;height:34px;cursor:pointer;font-size:15px}
h1{font-size:25px;line-height:1.35;margin:6px 0 10px;font-weight:650;letter-spacing:.01em}
nav{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:14px;color:var(--muted);padding-bottom:14px;border-bottom:1px solid var(--line)}
nav .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--flag);margin-left:4px;vertical-align:2px}
h2{font-size:20px;margin:0 0 4px;font-weight:650}
.meta{color:var(--muted);font-size:14px}
section{padding:26px 0 8px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px}
.decide{margin-top:18px;padding:18px 22px 16px}
.decide h2{font-size:17px;color:var(--muted);font-weight:600;margin-bottom:6px}
.drow{display:grid;grid-template-columns:34px 1fr auto;gap:4px 14px;padding:12px 0;border-top:1px solid var(--line)}
.drow:first-of-type{border-top:0}
.num{width:28px;height:28px;border-radius:50%;background:var(--acc);color:#fff;display:grid;place-items:center;font-weight:700;font-size:15px;text-decoration:none!important}
:root[data-theme=dark] .num{color:#0f1115}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .num{color:#0f1115}}
.q{font-size:18px;font-weight:650;line-height:1.4}
.rec{margin-top:3px}.rec b{color:var(--acc)}
.why{color:var(--muted)}
.rep{margin-top:4px;font-size:14.5px;color:var(--muted)}
.cost{align-self:start;font-size:12.5px;color:var(--muted);background:var(--soft);border-radius:999px;padding:3px 10px;white-space:nowrap}
.takeall{display:flex;flex-wrap:wrap;align-items:center;gap:8px 12px;margin-top:6px;padding-top:12px;border-top:1px dashed var(--line)}
.takeall code{font-size:15px;padding:4px 10px;background:var(--acc-soft);color:var(--ink)}
#copy{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:8px;padding:3px 12px;cursor:pointer;font-size:13.5px}
.rest{color:var(--muted);font-size:14px;width:100%}
.lines{margin:14px 2px 0;font-size:14.5px;display:grid;gap:5px}
.lines .k{color:var(--muted);margin-right:8px}
.chip{display:inline-block;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:1px 10px;margin:2px 6px 2px 0;font-size:13.5px}
.chip.flag{border-color:var(--flag);color:var(--flag);background:var(--flag-soft)}
figure{margin:14px 0 18px}
figure img,figure video{display:block;max-width:100%;max-height:78vh;border-radius:10px;border:1px solid var(--line);background:var(--soft)}figure video{width:min(100%,760px)}.segbody figure video{width:100%}
figcaption{color:var(--muted);font-size:14px;margin-top:6px}
figure.audio{display:inline-block;margin:8px 22px 10px 0;vertical-align:top}
figure.audio figcaption{margin:0 0 4px}
table{border-collapse:collapse;width:100%;font-size:14.5px;margin:8px 0 6px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:13px}
tr.pick td{background:var(--acc-soft)}
.tag{font-size:12px;border-radius:5px;padding:0 6px;margin-left:6px;background:var(--acc);color:#fff;vertical-align:1px}
:root[data-theme=dark] .tag{color:#0f1115}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]) .tag{color:#0f1115}}
.segment{border-top:2px solid var(--line);margin-top:18px}
.seghead{display:flex;flex-wrap:wrap;align-items:baseline;gap:4px 14px}
.segnote{margin:6px 0 2px}
.shots{display:grid;grid-template-columns:repeat(var(--cols,3),minmax(0,1fr));gap:16px;margin:14px 0 6px}
.shotcard{background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.shotcard.flag{border:2px solid var(--flag)}
.shotcard img{display:block;width:100%;aspect-ratio:var(--ar,1.7778);object-fit:contain;background:var(--soft)}
.shotcard .cap{padding:8px 12px 10px;font-size:14px}
.shotcard .id{font-weight:700;margin-right:8px}
.shotcard .t{color:var(--muted);font-size:13px}
.shotcard .u{color:var(--flag);font-size:13.5px;margin-top:3px}
.segbody{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:22px;align-items:start;margin-top:10px}
.segbody figure{margin-top:6px}
table.shotlist td:nth-child(-n+2),table.shotlist th{white-space:nowrap}table.shotlist td:nth-child(3){width:46%}td.st.ok{color:var(--ok)}td.st.flag{color:var(--flag)}
.small{font-size:13.5px;color:var(--muted)}
details{border:1px solid var(--line);border-radius:10px;background:var(--card);padding:10px 16px;margin:10px 0}
summary{cursor:pointer;font-weight:600}
.text{white-space:pre-wrap;margin-top:8px;font-size:14.5px}
footer{color:var(--muted);font-size:13px;padding:26px 0 40px;border-top:1px solid var(--line);margin-top:30px}
@media (max-width:900px){.shots{grid-template-columns:repeat(calc(var(--cols,3) - 1),minmax(0,1fr))}.segbody{grid-template-columns:1fr}.drow{grid-template-columns:34px 1fr}.cost{grid-column:2;justify-self:start;white-space:normal}}
@media (max-width:560px){.wrap{padding:0 16px}.shots{grid-template-columns:1fr}.drow{grid-template-columns:30px 1fr}h1{font-size:21px}}
"""

HEAD_JS = """(function(){var r=document.documentElement,t=null;try{t=new URLSearchParams(location.search).get('theme')}catch(e){}
if(t!=='dark'&&t!=='light'){try{t=localStorage.getItem('ovh-review-theme')}catch(e){}}
if(t==='dark'||t==='light')r.setAttribute('data-theme',t)})();"""

BODY_JS = """(function(){var r=document.documentElement,b=document.getElementById('theme'),c=document.getElementById('copy');
if(b)b.addEventListener('click',function(){var cur=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
var n=cur==='dark'?'light':'dark';r.setAttribute('data-theme',n);try{localStorage.setItem('ovh-review-theme',n)}catch(e){}});
if(c)c.addEventListener('click',function(){var s=c.getAttribute('data-text'),l=c.textContent;
function done(){c.textContent=c.getAttribute('data-done');setTimeout(function(){c.textContent=l},1400)}
function old(){var a=document.createElement('textarea');a.value=s;document.body.appendChild(a);a.select();try{document.execCommand('copy');done()}catch(e){}a.remove()}
try{navigator.clipboard.writeText(s).then(done,old)}catch(e){old()}});})();"""


def gate_title(g, lang):
    """1 → 关卡 ① 大纲, E1 → 检查点 E1 脚本, 2b → 关卡 ② 分镜（第 2 页）; anything else → 审阅页 <g>."""
    base, suffix = (g[:-1], g[-1]) if len(g) > 1 and g[-1].isalpha() and g[:-1] in GATES else (g, "")
    name = GATES.get(base, (f"审阅页 {g}", f"Review page {g}"))[0 if lang == "zh" else 1]
    if suffix:
        n = ord(suffix.lower()) - ord("a") + 1
        name += f"（第 {n} 页）" if lang == "zh" else f" (page {n})"
    return name


def image_ratio(path):
    """width / height from a PNG, GIF or JPEG header; None when unknown."""
    try:
        with open(path, "rb") as f:
            b = f.read(65536)
    except OSError:
        return None
    if b[:8] == b"\x89PNG\r\n\x1a\n" and len(b) >= 24:
        w, h = int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    elif b[:6] in (b"GIF87a", b"GIF89a"):
        w, h = int.from_bytes(b[6:8], "little"), int.from_bytes(b[8:10], "little")
    elif b[:2] == b"\xff\xd8":
        i, w, h = 2, 0, 0
        while i + 9 < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m, n = b[i + 1], int.from_bytes(b[i + 2:i + 4], "big")
            if m in (0xC0, 0xC1, 0xC2):
                h, w = int.from_bytes(b[i + 5:i + 7], "big"), int.from_bytes(b[i + 7:i + 9], "big")
                break
            i += 2 + n
    else:
        return None
    return w / h if w and h else None


class Page:
    def __init__(self, project: Path, src: Path, data: dict):
        self.project, self.src, self.d = project, src, data
        self.out = project / "out" / "review"
        self.lang = data.get("lang") if data.get("lang") in T else "zh"
        self.t = T[self.lang]
        self.errors, self.warnings = [], []
        self.shot_ids = set()
        self.gate = str(data.get("gate", "")).strip()

    # ---- helpers -------------------------------------------------------------------------------------------
    def err(self, msg):
        self.errors.append(msg)

    def title(self):
        return str(self.d["title"]) if self.d.get("title") else gate_title(self.gate, self.lang)

    def url(self, p, what):
        """Relative URL from out/review/ to a project path; http(s) passes through. Missing files are errors."""
        p = str(p).strip()
        if re.match(r"^[a-z]+://", p):
            return p
        f = (self.project / p) if not os.path.isabs(p) else Path(p)
        if not f.exists():
            self.err(f"{what}: {p} does not exist")
        rel = os.path.relpath(f, self.out).replace(os.sep, "/")
        return quote(rel, safe="/-_.~()")

    def text(self, s):
        """Escape, then `code`, **bold**, shot ids (S04) as links, newlines as <br>."""
        out = []
        for i, part in enumerate(re.split(r"`([^`]*)`", str(s))):
            if i % 2:
                out.append(f"<code>{html.escape(part)}</code>")
                continue
            e = html.escape(part)
            e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e)
            e = re.sub(r"(?<![A-Za-z0-9])(S\d{1,3}[a-z]?)(?![0-9])",
                       lambda m: f'<a href="#shot-{m.group(1)}">{m.group(1)}</a>' if m.group(1) in self.shot_ids else m.group(1), e)
            out.append(e.replace("\n", "<br>"))
        return "".join(out)

    def media(self, path, caption="", what="asset", t0=None, t1=None, poster=None):
        u = self.url(path, what)
        ext = os.path.splitext(str(path).split("#")[0].split("?")[0])[1].lower()
        cap = f"<figcaption>{self.text(caption)}</figcaption>" if caption else ""
        if ext in IMG:
            alt = html.escape(re.sub(r"[`*]", "", str(caption)) or os.path.basename(str(path)))
            return f'<figure><a href="{u}" target="_blank"><img src="{u}" alt="{alt}" loading="lazy"></a>{cap}</figure>'
        if ext in VID:
            frag = f"#t={float(t0 or 0):g},{float(t1):g}" if t1 is not None else (f"#t={float(t0):g}" if t0 is not None else "")
            pa = f' poster="{self.url(poster, what)}"' if poster else ""
            return f'<figure><video controls preload="metadata" playsinline src="{u}{frag}"{pa}></video>{cap}</figure>'
        if ext in AUD:
            return f'<figure class="audio">{cap}<audio controls preload="metadata" src="{u}"></audio></figure>'
        name = html.escape(os.path.basename(str(path)))
        return f'<p><a href="{u}" target="_blank">{name}</a>{" · " + self.text(caption) if caption else ""}</p>'

    # ---- checks --------------------------------------------------------------------------------------------
    def check(self):
        d = self.d
        if not self.gate:
            self.err("`gate` is missing")
        if not str(d.get("summary", "")).strip():
            self.err("`summary` is missing: one line saying what this page asks and how long it takes")
        decs = d.get("decisions")
        if not isinstance(decs, list):
            self.err("`decisions` must be a list (an empty list means nothing to decide)")
            d["decisions"] = decs = []
        if len(decs) > MAX_DECISIONS:
            self.err(f"{len(decs)} decisions on one page (at most {MAX_DECISIONS}): send the upstream ones now and the rest "
                     "on the next page, or give them a recommendation that passes by default")
        ids = []
        for i, dec in enumerate(decs, 1):
            opts = [o if isinstance(o, dict) else {"id": str(o)} for o in dec.get("options") or []]
            dec["options"] = opts
            if not dec.get("question"):
                self.err(f"decision {i}: no `question`")
            if not str(dec.get("recommend", "")).strip():
                self.err(f"decision {i} ({dec.get('id', '?')}): no `recommend`; every decision carries the agent's pick")
            if not dec.get("reply"):
                if opts:
                    dec["reply"] = " / ".join(str(o.get("id")) for o in opts)
                else:
                    self.err(f"decision {i} ({dec.get('id', '?')}): no `reply` and no `options` to build one from")
            if opts and dec.get("recommend") and str(dec["recommend"]) not in {str(o.get("id")) for o in opts}:
                self.warnings.append(f"decision {i}: recommend {dec['recommend']!r} is not one of the option ids")
            ids.append(str(dec.get("id") or f"d{i}"))
            dec["id"] = ids[-1]
        d["least_sure"] = [x if isinstance(x, dict) else {"note": str(x)} for x in d.get("least_sure") or []]
        segs = d.get("segments") or []
        for i, s in enumerate(segs, 1):
            s["id"] = str(s.get("id") or i)
            ids.append(s["id"])
            shots = s.get("shots") or []
            if len(shots) > MAX_SHOTS:
                self.warnings.append(f"segment {s['id']}: {len(shots)} shots (a page reads best with 3–{MAX_SHOTS}); split it")
            for sh in shots:
                sh["id"] = str(sh.get("id", ""))
                if sh["id"] in self.shot_ids:
                    self.err(f"shot {sh['id']} appears twice")
                self.shot_ids.add(sh["id"])
        dup = {x for x in ids if ids.count(x) > 1}
        if dup:
            self.err(f"duplicate decision / segment ids: {sorted(dup)} (assets point at them with `for`)")
        for a in d.get("assets") or []:
            if a.get("for") and str(a["for"]) not in ids:
                self.err(f"asset {a.get('path')}: `for` {a['for']!r} names no decision or segment")

    # ---- sections ------------------------------------------------------------------------------------------
    def assets_for(self, key):
        return [a for a in self.d.get("assets") or [] if str(a.get("for", "")) == key]

    def example_shot(self):
        """The shot id the reply hint uses: the first least-sure shot, else the first shot."""
        for it in self.d["least_sure"]:
            if str(it.get("id", "")) in self.shot_ids:
                return str(it["id"])
        for seg in self.d.get("segments") or []:
            for sh in seg.get("shots") or []:
                return str(sh.get("id"))
        return "S01"

    def decisions_block(self):
        t, decs = self.t, self.d["decisions"]
        rows = []
        for i, dec in enumerate(decs, 1):
            why = f' <span class="why">— {self.text(dec["why"])}</span>' if dec.get("why") else ""
            cost = f'<div class="cost">{self.text(dec["cost"])}</div>' if dec.get("cost") else "<div></div>"
            rows.append(f'<div class="drow"><a class="num" href="#d-{html.escape(dec["id"])}">{i}</a><div>'
                        f'<div class="q">{self.text(dec.get("question", ""))}</div>'
                        f'<div class="rec">{t["rec"]} <b>{self.text(dec.get("recommend", ""))}</b>{why}</div>'
                        f'<div class="rep">{t["reply"]} <code>{html.escape(str(dec.get("reply", "")))}</code></div>'
                        f'</div>{cost}</div>')
        rest = t["rest"].format(shot=self.example_shot()) if self.shot_ids else t["rest_plain"]
        if decs:
            allr = self.take_all()
            foot = (f'<div class="takeall"><span>{t["take_all"]}</span><code>{html.escape(allr)}</code>'
                    f'<button id="copy" data-text="{html.escape(allr)}" data-done="{t["copied"]}">{t["copy"]}</button>'
                    f'<span class="rest">{rest}</span></div>')
        else:
            foot = f'<div class="rest">{t["nothing"]}</div>'
        head = t["decide"].format(n=len(decs)) if decs else t["look"]
        return f'<div class="card decide" id="decide"><h2>{head}</h2>{"".join(rows)}{foot}</div>'

    def take_all(self):
        return " · ".join(f"{i} {dec.get('recommend', '')}" for i, dec in enumerate(self.d["decisions"], 1))

    def lines_block(self):
        t, d, out = self.t, self.d, []
        if d["least_sure"]:
            chips = []
            for it in d["least_sure"]:
                sid, note = str(it.get("id", "")), self.text(it.get("note", ""))
                label = (f'<a href="#shot-{html.escape(sid)}">{html.escape(sid)}</a> ' if sid in self.shot_ids
                         else (html.escape(sid) + " " if sid else ""))
                chips.append(f'<span class="chip flag">{label}{note}</span>')
            out.append(f'<div><span class="k">{t["least"]}</span>{"".join(chips)}</div>')
        for key in ("decided", "delegated"):
            vals = d.get(key) or []
            if vals:
                out.append(f'<div><span class="k">{t[key]}</span>{t["sep"].join(self.text(v) for v in vals)}</div>')
        if d.get("not_reviewed"):
            out.append(f'<div><span class="k">{t["not_reviewed"]}</span>{self.text(d["not_reviewed"])}</div>')
        return f'<div class="lines">{"".join(out)}</div>' if out else ""

    def decision_sections(self):
        t, out = self.t, []
        for i, dec in enumerate(self.d["decisions"], 1):
            figs = "".join(self.media(a["path"], a.get("caption", ""), f"decision {dec['id']}", a.get("t0"), a.get("t1"))
                           for a in self.assets_for(dec["id"]))
            opts, table = dec["options"], ""
            if opts:
                has_pc = any(o.get("pro") or o.get("con") for o in opts)
                head = f'<tr><th>{t["options"]}</th>' + (f'<th>{t["pro"]}</th><th>{t["con"]}</th>' if has_pc else "") + "</tr>"
                body = []
                for o in opts:
                    pick = str(o.get("id")) == str(dec.get("recommend"))
                    tag = f'<span class="tag">{t["rec"]}</span>' if pick else ""
                    label = f' {self.text(o["label"])}' if o.get("label") else ""
                    cells = f'<td><b>{html.escape(str(o.get("id")))}</b>{label}{tag}</td>'
                    if has_pc:
                        cells += f'<td>{self.text(o.get("pro", ""))}</td><td>{self.text(o.get("con", ""))}</td>'
                    body.append(f'<tr class="{"pick" if pick else ""}">{cells}</tr>')
                table = f'<table>{head}{"".join(body)}</table>'
            cost = f' · {self.text(dec["cost"])}' if dec.get("cost") else ""
            meta = (f'<div class="meta">{t["rec"]} <b>{self.text(dec.get("recommend", ""))}</b> · {t["reply"]} '
                    f'<code>{html.escape(str(dec.get("reply", "")))}</code>{cost}</div>')
            out.append(f'<section id="d-{html.escape(dec["id"])}"><h2>{t["decision"].format(i=i)} · {self.text(dec.get("question", ""))}</h2>'
                       f'{meta}{figs}{table}</section>')
        return "".join(out)

    def loose_assets(self):
        ids = {str(x.get("id")) for x in self.d["decisions"]} | {str(s.get("id")) for s in self.d.get("segments") or []}
        return [a for a in self.d.get("assets") or [] if str(a.get("for", "")) not in ids]

    def other_section(self):
        rest = self.loose_assets()
        if not rest:
            return ""
        figs = "".join(self.media(a["path"], a.get("caption", ""), "asset", a.get("t0"), a.get("t1")) for a in rest)
        return f'<section id="other"><h2>{self.t["other"]}</h2>{figs}</section>'

    def segment_sections(self):
        t, segs = self.t, self.d.get("segments") or []
        colon = "：" if self.lang == "zh" else ": "
        flagged = {str(it.get("id")): it.get("note", "") for it in self.d["least_sure"]}
        out = []
        for i, s in enumerate(segs, 1):
            shots = s.get("shots") or []
            timed = [x for x in shots if x.get("t0") is not None and x.get("t1") is not None]
            durs = [float(x["t1"]) - float(x["t0"]) for x in timed]
            meta = [f'{float(s["t0"]):.1f}–{float(s["t1"]):.1f} s' if s.get("t0") is not None and s.get("t1") is not None else "",
                    t["shots"].format(n=len(shots)) if shots else "",
                    t["avg"].format(s=f"{sum(durs) / len(durs):.1f}") if durs else ""]
            first = next((sh.get("frame") for sh in shots if sh.get("frame")), None)
            ratio = image_ratio(self.project / first) if first else None
            ratio = ratio or 16 / 9
            cols = 3 if ratio >= 1.2 else (4 if ratio >= 0.8 else 5)
            has_vo = any(sh.get("vo") for sh in shots)
            cards, rows = [], []
            for sh in shots:
                sid = str(sh.get("id", ""))
                note = flagged.get(sid)
                dur = f'{float(sh["t1"]) - float(sh["t0"]):.1f} s' if sh in timed else ""
                tr = f'{float(sh["t0"]):.1f}–{float(sh["t1"]):.1f} s · {dur}' if dur else ""
                img = ""
                if sh.get("frame"):
                    u = self.url(sh["frame"], f"shot {sid} frame")
                    img = f'<a href="{u}" target="_blank"><img src="{u}" alt="{html.escape(sid)}" loading="lazy"></a>'
                unsure = f'<div class="u">? {t["unsure"]}{colon}{self.text(note)}</div>' if note is not None else ""
                cards.append(f'<div class="shotcard{" flag" if note is not None else ""}" id="shot-{html.escape(sid)}">{img}'
                             f'<div class="cap"><span class="id">{html.escape(sid)}</span><span class="t">{tr}</span>'
                             f'<div>{self.text(sh.get("see", ""))}</div>{unsure}</div></div>')
                if note is not None:
                    st = f'<td class="st flag">? {self.text(note)}</td>'
                else:
                    extra = colon + self.text(sh["note"]) if sh.get("note") else ""
                    st = f'<td class="st ok">✓ {t["ok"]}{extra}</td>'
                said = self.text(sh.get("vo", "")) if has_vo else self.text(sh.get("see", ""))
                rows.append(f'<tr><td><a href="#shot-{html.escape(sid)}">{html.escape(sid)}</a></td><td>{dur}</td>'
                            f'<td>{said}</td>{st}</tr>')
            table = ""
            if rows:
                third = t["vo"] if has_vo else t["see"]
                table = (f'<div><table class="shotlist"><tr><th>{t["shot"]}</th><th>{t["dur"]}</th><th>{third}</th><th>{t["status"]}</th></tr>'
                         f'{"".join(rows)}</table><div class="small">{t["pass_all"].format(shot=self.example_shot())}</div></div>')
            clip = ""
            if self.d.get("animatic") and s.get("t0") is not None and s.get("t1") is not None:
                clip = self.media(self.d["animatic"], t["clip"], "animatic", s["t0"], s["t1"], first)
            body = f'<div class="segbody"><div>{clip}</div>{table}</div>' if (clip or table) else ""
            extra = "".join(self.media(a["path"], a.get("caption", ""), f"segment {s['id']}", a.get("t0"), a.get("t1"))
                            for a in self.assets_for(s["id"]))
            note = f'<div class="segnote">{self.text(s["note"])}</div>' if s.get("note") else ""
            nflag = sum(1 for sh in shots if str(sh.get("id")) in flagged)
            badge = f'<span class="chip flag">? × {nflag}</span>' if nflag else ""
            out.append(f'<section class="segment" id="seg-{html.escape(s["id"])}"><div class="seghead">'
                       f'<h2>{t["seg"].format(i=i, n=len(segs))} · {self.text(s.get("title", ""))}</h2>'
                       f'<span class="meta">{" · ".join(m for m in meta if m)}</span>{badge}</div>{note}'
                       f'<div class="shots" style="--cols:{cols};--ar:{ratio:.4f}">{"".join(cards)}</div>{body}{extra}</section>')
        return "".join(out)

    def appendix_section(self):
        items = []
        for a in self.d.get("appendix") or []:
            body = f'<div class="text">{self.text(a["text"])}</div>' if a.get("text") else ""
            if a.get("path"):
                body += self.media(a["path"], "", "appendix")
            items.append(f'<details><summary>{self.text(a.get("title", ""))}</summary>{body}</details>')
        if not items:
            return ""
        return f'<section id="appendix"><h2>{self.t["appendix"]}</h2>{"".join(items)}</section>'

    def nav(self):
        t = self.t
        links = [f'<a href="#decide">{t["nav_decide"]}</a>']
        flagged = {str(it.get("id")) for it in self.d["least_sure"]}
        if self.loose_assets():
            links.append(f'<a href="#other">{t["nav_other"]}</a>')
        for i, s in enumerate(self.d.get("segments") or [], 1):
            dot = '<span class="dot"></span>' if any(str(sh.get("id")) in flagged for sh in s.get("shots") or []) else ""
            links.append(f'<a href="#seg-{html.escape(s["id"])}">{i} {html.escape(str(s.get("title", "")))}</a>{dot}')
        if self.d.get("appendix"):
            links.append(f'<a href="#appendix">{t["nav_appendix"]}</a>')
        return f'<nav>{"".join(f"<span>{x}</span>" for x in links)}</nav>'

    def others(self):
        pages = sorted(p for p in self.out.glob("gate-*.html") if p.name != f"gate-{self.gate}.html")
        if not pages:
            return ""
        links = " · ".join(f'<a href="{quote(p.name)}">{html.escape(gate_title(p.stem[5:], self.lang))}</a>' for p in pages)
        return f'{self.t["others"]}{"：" if self.lang == "zh" else ": "}{links}<br>'

    def render(self):
        self.check()
        t, title = self.t, self.title()
        body = (self.decisions_block() + self.lines_block() + self.decision_sections() + self.other_section()
                + self.segment_sections() + self.appendix_section())
        src = os.path.relpath(self.src, self.project).replace(os.sep, "/")
        return (f'<!doctype html><html lang="{t["html_lang"]}"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width, initial-scale=1">'
                f'<title>{html.escape(title)} · {html.escape(self.project.name)}</title>'
                f'<style>{CSS}</style><script>{HEAD_JS}</script></head><body><div class="wrap">'
                f'<header><div class="eyebrow"><span>{html.escape(self.project.name)} · {html.escape(title)}</span>'
                f'<button id="theme" title="{t["theme"]}" aria-label="{t["theme"]}">◐</button></div>'
                f'<h1>{self.text(self.d.get("summary", ""))}</h1>{self.nav()}</header>'
                f'{body}<footer>{self.others()}{t["src"].format(src=html.escape(src))}</footer></div>'
                f'<script>{BODY_JS}</script></body></html>\n')

    def chat(self, page_path):
        t, decs, title = self.t, self.d["decisions"], self.title()
        plain = lambda s: re.sub(r"\*\*(.+?)\*\*", r"\1", str(s)).replace("`", "")
        if not decs:
            return f'{t["chat_none"].format(title=title)}\n{t["page"]}{t["colon"]}{page_path}'
        lines = [t["chat_head"].format(title=title, n=len(decs))]
        for i, dec in enumerate(decs, 1):
            why = t["why"].format(w=plain(dec["why"])) if dec.get("why") else ""
            lines.append(t["chat_item"].format(i=i, q=plain(dec.get("question", "")), r=plain(dec.get("recommend", "")),
                                               why=why, reply=plain(dec.get("reply", ""))))
        lines.append(t["chat_all"].format(all=self.take_all()))
        lines.append(f'{t["page"]}{t["colon"]}{page_path}')
        return "\n".join(lines)


def find_project(arg):
    p = Path(arg).expanduser()
    if p.is_dir():
        return p.resolve()
    q = ROOT / "projects" / arg
    return q.resolve() if q.is_dir() else None


def main():
    ap = argparse.ArgumentParser(description="Build the decision-first review page from out/review/gate-<n>.json")
    ap.add_argument("project", help="project directory, or its folder name under projects/")
    ap.add_argument("gate", nargs="?", help="1 | 2 | 3 | E0–E5 | 2b …; default: the newest out/review/gate-*.json")
    a = ap.parse_args()
    project = find_project(a.project)
    if not project:
        print(f"no such project: {a.project}", file=sys.stderr)
        return 2
    rdir = project / "out" / "review"
    found = [rdir / f"gate-{a.gate}.json"] if a.gate else sorted(rdir.glob("gate-*.json"), key=lambda p: p.stat().st_mtime)
    if not found or not found[-1].is_file():
        where = found[-1] if found else rdir / "gate-<n>.json"
        print(f"no review pack at {where}: write one first (templates/REVIEW.md, section 审阅包 JSON)", file=sys.stderr)
        return 2
    src = found[-1]
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")
    except ValueError as e:
        print(f"{src}: {e}", file=sys.stderr)
        return 2
    page = Page(project, src, data)
    try:
        doc = page.render()
    except (AttributeError, KeyError, TypeError, ValueError) as e:   # a field of the wrong type, e.g. a decision that is a string
        print(f"{src}: a field has the wrong shape ({type(e).__name__}: {e}); compare with templates/REVIEW.md", file=sys.stderr)
        return 2
    gate = src.stem[5:] if src.stem.startswith("gate-") else src.stem
    for name in (f"gate-{gate}.html", "index.html"):
        (rdir / name).write_text(doc, encoding="utf-8")
    page_path = rdir / f"gate-{gate}.html"
    for w in page.warnings:
        print(f"! {w}", file=sys.stderr)
    for e in page.errors:
        print(f"✗ {e}", file=sys.stderr)
    segs = data.get("segments") or []
    print(f"✓ {page_path}, also index.html  ({page.title()} · {len(data['decisions'])} decision(s) · {len(segs)} segment(s) · "
          f"{sum(len(s.get('shots') or []) for s in segs)} shot(s))", file=sys.stderr)
    print(page.chat(page_path))
    return 1 if page.errors else 0


if __name__ == "__main__":
    sys.exit(main())
