"""Review page: out/review/gate-<n>.json -> a local HTML page a human can look at and listen to.

usage: python3 tools/review.py <project> [gate]
  <project>  the project directory (or a folder name under projects/)
  [gate]     1 | 2 | 3 | E0-E5 | 2b ... (gate-2 and gate-2.json work too); default: the newest out/review/gate-*.json

The file name sets the gate: gate-2b.json is page 2 of gate ②, whatever its "gate" field says (a mismatch is a
warning). Writes out/review/gate-<n>.html, and the same page as out/review/index.html (always the latest page), then
prints the chat message: the decisions, the reply that takes every recommendation, the least-sure shots, and the path
of gate-<n>.html, which a later page does not overwrite. playbook/01-pipeline.md ("审阅页") explains the page and
every field:

  summary, decisions[{id, question, options[{id, label, pro, con} | "id"], recommend, why, cost, reply}],
  assets[{path, caption, for, t0, t1, poster}], least_sure[{id, note} | "note"], animatic,
  segments[{id, title, t0, t1, note, shots[{id, t0, t1, frame, see, vo, note}]}], appendix[{title, text, path}]
  optional: gate, title, lang (zh | en), decided[], delegated[], not_reviewed

Paths are relative to the project and linked relatively, so the page opens straight from disk (images, GIF, mp4 and
audio play in the browser); http(s) URLs pass through, other schemes are refused. Every text is HTML-escaped; appendix
text may hold simple pipe tables (| a | b | / |---|---| / | 1 | 2 |).

Exit: 0 written (warnings, e.g. more than 3 decisions, go to stderr) · 1 written, but the page breaks a rule
(a decision without a question, recommendation or reply, an option without an id, a missing file, a refused URL,
an unknown `for`, a duplicate id); no chat message then · 2 nothing written (no project, no JSON, bad JSON, a field
of the wrong shape, or a file that can't be read or written).
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
         "E1": ("检查点 E1 脚本", "Checkpoint E1 script"), "E2": ("检查点 E2 声音", "Checkpoint E2 sound"),
         "E3": ("检查点 E3 锁时", "Checkpoint E3 timing lock"), "E4": ("检查点 E4 样板章", "Checkpoint E4 sample chapter"),
         "E5": ("检查点 E5 锁画面", "Checkpoint E5 picture lock")}

T = {
    "zh": dict(html_lang="zh-CN", decide="要你定的 {n} 件事", look="这一页只给你过目",
               nothing="这一页没有要你定的事：看一眼，回“通过”，或写要改的。",
               rec="推荐", reply="回", take_all="照推荐回复", copy="复制", copied="已复制",
               rest="其余默认通过；要改哪一镜，写“{shot} 改：……”。", rest_plain="其余默认通过，只写要改的。",
               least="我最没把握的", decided="已经定了", delegated="我替你定了", not_reviewed="这页不审",
               decision="决定 {i}", options="选项", pro="好处", con="代价", other="其他材料",
               seg="分镜 {i}/{n}", shots="{n} 镜", avg="平均 {s} s/镜", unsure="没把握", n_unsure="{n} 镜没把握",
               shot="镜头", dur="时长", vo="旁白", see="看到什么", status="状态", ok="通过", plan="默认改",
               pass_all="默认全部通过，只写要改的，例如“{shot} 改：……”。", clip="这一段动起来的样子（{a}–{b} s，播到段尾自动停）",
               appendix="附录：不影响拍板的细节", others="其他审阅页", src="由 bin/vh review 从 {src} 生成",
               theme="切换深色 / 浅色", nav_decide="决定", nav_other="材料", nav_appendix="附录",
               page="页面", chat_head="{title} · 要你定 {n} 件事", chat_none="{title} · 没有要你定的事，看一眼，回“通过”或写要改的。",
               chat_item="{i}. {q} 回 {reply}\n   推荐 {r}{why}", chat_all="照推荐就回：{all}。其余默认通过。",
               chat_least="我最没把握的{red}：", chat_red="（镜头在页面里标红）",
               why="：{w}", sep="；", colon="：", quoted="「{x}」"),
    "en": dict(html_lang="en", decide="{n} thing(s) for you to decide", look="Just for a look",
               nothing="Nothing to decide on this page: take a look, then reply “ok” or say what to change.",
               rec="Recommended", reply="Reply", take_all="Take every recommendation", copy="Copy", copied="Copied",
               rest="Everything else passes by default; to change a shot, write “{shot} change: …”.",
               rest_plain="Everything else passes by default; only write what to change.",
               least="Least sure about", decided="Already decided", delegated="Decided for you", not_reviewed="Not reviewed here",
               decision="Decision {i}", options="Options", pro="Pro", con="Cost", other="Other material",
               seg="Storyboard {i}/{n}", shots="{n} shots", avg="{s} s per shot", unsure="unsure", n_unsure="{n} unsure",
               shot="Shot", dur="Length", vo="Narration", see="On screen", status="Status", ok="ok", plan="will change",
               pass_all="Every shot passes by default; only write what to change, e.g. “{shot} change: …”.",
               clip="This segment in motion ({a}–{b} s; stops at the segment end)",
               appendix="Appendix: details that don't change the decisions", others="Other review pages",
               src="Built by bin/vh review from {src}", theme="Toggle dark / light",
               nav_decide="Decisions", nav_other="Material", nav_appendix="Appendix",
               page="Page", chat_head="{title} · {n} thing(s) for you to decide",
               chat_none="{title} · nothing to decide; take a look and reply “ok” or say what to change.",
               chat_item="{i}. {q} Reply {reply}\n   Recommended: {r}{why}",
               chat_all="To take every recommendation, reply: {all}. Everything else passes by default.",
               chat_least="Least sure about{red}:", chat_red=" (shots are red on the page)",
               why=" — {w}", sep="; ", colon=": ", quoted=" “{x}”"),
}

CSS = """
:root{color-scheme:light;--bg:#f6f4ef;--card:#fff;--ink:#1d1f23;--muted:#6b6760;--line:#e3dfd5;--soft:#efebe2;
--acc:#2456c9;--acc-soft:#e7edfb;--flag:#c93a27;--flag-soft:#fbe8e3;--ok:#2e7d4f;--plan:#8a5a00;--code:#f0ece3}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){color-scheme:dark;--bg:#131518;--card:#1b1e22;--ink:#e9e7e2;
--muted:#9c978e;--line:#2d3137;--soft:#23272c;--acc:#86a8ff;--acc-soft:#1e2a44;--flag:#ff735e;--flag-soft:#3a211d;--ok:#5cc98a;
--plan:#e0b34f;--code:#262a30}}
:root[data-theme=dark]{color-scheme:dark;--bg:#131518;--card:#1b1e22;--ink:#e9e7e2;--muted:#9c978e;--line:#2d3137;--soft:#23272c;
--acc:#86a8ff;--acc-soft:#1e2a44;--flag:#ff735e;--flag-soft:#3a211d;--ok:#5cc98a;--plan:#e0b34f;--code:#262a30}
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
nav .nf{color:var(--flag);font-size:12.5px;margin-left:5px}
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
.mini{margin:3px 0 2px;padding-left:20px;columns:2;column-gap:32px;font-size:14px}.mini li{break-inside:avoid;margin:1px 0}
.chip{display:inline-block;border:1px solid var(--line);background:var(--card);border-radius:999px;padding:1px 10px;margin:2px 6px 2px 0;font-size:13.5px}
.chip.flag{border-color:var(--flag);color:var(--flag);background:var(--flag-soft)}
figure{margin:14px 0 18px}
figure img,figure video{display:block;max-width:100%;max-height:78vh;border-radius:10px;border:1px solid var(--line);background:var(--soft)}
figure video{width:min(100%,760px)}.segbody figure video{width:100%}
figcaption{color:var(--muted);font-size:14px;margin-top:6px}
figure.audio{display:inline-block;margin:8px 22px 10px 0;vertical-align:top}
figure.audio figcaption{margin:0 0 4px}
table{border-collapse:collapse;width:100%;font-size:14.5px;margin:8px 0 6px}
th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:13px}
tr.pick td{background:var(--acc-soft)}
.tag{font-size:12px;border-radius:5px;padding:0 6px;margin-left:6px;background:var(--acc);color:#fff;vertical-align:1px;white-space:nowrap}
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
.shotcard .p{color:var(--plan);font-size:13.5px;margin-top:3px}
.segbody{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:22px;align-items:start;margin-top:10px}
.segbody figure{margin-top:6px}
table.shotlist td:nth-child(-n+2),table.shotlist th{white-space:nowrap}table.shotlist td:nth-child(3){width:46%}
td.st.ok{color:var(--ok)}td.st.flag{color:var(--flag)}td.st .p{color:var(--plan)}
.small{font-size:13.5px;color:var(--muted)}
details{border:1px solid var(--line);border-radius:10px;background:var(--card);padding:10px 16px;margin:10px 0}
summary{cursor:pointer;font-weight:600}
.text{white-space:pre-wrap;margin-top:8px;font-size:14.5px}
footer{color:var(--muted);font-size:13px;padding:26px 0 40px;border-top:1px solid var(--line);margin-top:30px}
@media (max-width:900px){.shots{grid-template-columns:repeat(calc(var(--cols,3) - 1),minmax(0,1fr))}.segbody{grid-template-columns:1fr}
.drow{grid-template-columns:34px 1fr}.cost{grid-column:2;justify-self:start;white-space:normal}}
@media (max-width:560px){.mini{columns:1}.wrap{padding:0 16px}.shots{grid-template-columns:1fr}.drow{grid-template-columns:30px 1fr}h1{font-size:21px}}
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
try{navigator.clipboard.writeText(s).then(done,old)}catch(e){old()}});
document.querySelectorAll('video[data-t1]').forEach(function(v){var a=+v.getAttribute('data-t0')||0,e=+v.getAttribute('data-t1');
v.addEventListener('play',function(){if(v.currentTime<a-0.05||v.currentTime>=e-0.05)v.currentTime=a});
v.addEventListener('timeupdate',function(){if(v.currentTime>=e){v.pause();v.currentTime=e}})});})();"""


def txt(x):
    """None → "", anything else → str: a null field never renders as "None"."""
    return "" if x is None else str(x)


def esc(x):
    return html.escape(txt(x))


def scalar(x, what):
    """A text or number field. None → ""; a list or object where text belongs is the wrong shape (exit 2)."""
    if x is None:
        return ""
    if isinstance(x, bool) or not isinstance(x, (str, int, float)):
        raise TypeError(f"`{what}` must be text, got {type(x).__name__}")
    return str(x)


def as_list(x, what):
    """None → []; a string where a list belongs is the wrong shape (it would be split into characters)."""
    if x is None:
        return []
    if not isinstance(x, list):
        raise TypeError(f"`{what}` must be a list, got {type(x).__name__}")
    return x


def as_dict(x, what):
    if not isinstance(x, dict):
        raise TypeError(f"`{what}` must be an object, got {type(x).__name__}")
    return x


def seconds(x, what):
    """A time in seconds, or None when absent. A string of digits is accepted; anything else is the wrong shape."""
    if x is None or x == "":
        return None
    if isinstance(x, bool):
        raise TypeError(f"`{what}` must be a number")
    return float(x)   # ValueError on "zero" → exit 2


def gate_title(g, lang):
    """1 → 关卡 ① 大纲, E1 → 检查点 E1 脚本, 2b → 关卡 ② 分镜（第 2 页）; anything else → 审阅页 <g>."""
    base, suffix = (g[:-1], g[-1]) if len(g) > 1 and g[-1].isalpha() and g[:-1] in GATES else (g, "")
    name = GATES.get(base, (f"审阅页 {g}", f"Review page {g}"))[0 if lang == "zh" else 1]
    if suffix:
        n = ord(suffix.lower()) - ord("a") + 1
        name += f"（第 {n} 页）" if lang == "zh" else f" (page {n})"
    return name


def image_ratio(path):
    """width / height from the file's own header (PNG, GIF, JPEG, WebP, AVIF, SVG); None when unknown."""
    try:
        with open(path, "rb") as f:
            b = f.read(65536)
    except OSError:
        return None
    w = h = 0
    if b[:8] == b"\x89PNG\r\n\x1a\n" and len(b) >= 24:
        w, h = int.from_bytes(b[16:20], "big"), int.from_bytes(b[20:24], "big")
    elif b[:6] in (b"GIF87a", b"GIF89a"):
        w, h = int.from_bytes(b[6:8], "little"), int.from_bytes(b[8:10], "little")
    elif b[:2] == b"\xff\xd8":
        i = 2
        while i + 9 < len(b):
            if b[i] != 0xFF:
                i += 1
                continue
            m, n = b[i + 1], int.from_bytes(b[i + 2:i + 4], "big")
            if m in (0xC0, 0xC1, 0xC2):
                h, w = int.from_bytes(b[i + 5:i + 7], "big"), int.from_bytes(b[i + 7:i + 9], "big")
                break
            i += 2 + n
    elif b[:4] == b"RIFF" and b[8:12] == b"WEBP" and len(b) >= 30:
        chunk = b[12:16]
        if chunk == b"VP8X":
            w, h = 1 + int.from_bytes(b[24:27], "little"), 1 + int.from_bytes(b[27:30], "little")
        elif chunk == b"VP8L":
            v = int.from_bytes(b[21:25], "little")
            w, h = (v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1
        elif chunk == b"VP8 " and b[23:26] == b"\x9d\x01\x2a":
            w, h = int.from_bytes(b[26:28], "little") & 0x3FFF, int.from_bytes(b[28:30], "little") & 0x3FFF
    elif b[4:8] == b"ftyp" and b"ispe" in b:   # AVIF/HEIF: the ispe box holds the image size
        i = b.index(b"ispe")
        w, h = int.from_bytes(b[i + 8:i + 12], "big"), int.from_bytes(b[i + 12:i + 16], "big")
    elif b"<svg" in b[:4096]:
        tag = re.search(rb"<svg\b[^>]*>", b[:4096], re.S)
        a = tag.group(0) if tag else b""
        vb = re.search(rb'viewBox\s*=\s*["\']\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', a)
        wh = [re.search(rb'\b%s\s*=\s*["\']\s*([\d.]+)(?:px)?\s*["\']' % k, a) for k in (b"width", b"height")]
        try:
            if vb:
                w, h = float(vb.group(1)), float(vb.group(2))
            elif all(wh):
                w, h = float(wh[0].group(1)), float(wh[1].group(1))
        except ValueError:
            return None
    return w / h if w and h else None


class Page:
    def __init__(self, project: Path, src: Path, data: dict, gate: str):
        self.project, self.src, self.d, self.gate = project, src, data, gate
        self.out = project / "out" / "review"
        lang = data.get("lang")
        self.lang = lang if isinstance(lang, str) and lang in T else "zh"
        self.t = T[self.lang]
        self.errors, self.warnings = [], []
        self.shot_ids = set()
        self.flagged = {}      # shot id → least-sure note
        self.bad_paths = set() # each missing or refused path is reported once, however many places use it
        if lang is not None and self.lang != lang:
            self.warn(f"lang {lang!r} is not zh or en; using zh")

    def err(self, msg):
        if msg not in self.errors:   # a missing animatic used by six segments is reported once
            self.errors.append(msg)

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def title(self):
        return self.d["title"] or gate_title(self.gate, self.lang)

    # ---- the shape of the JSON: normalize every field, or raise TypeError / ValueError (exit 2) ----------
    def normalize(self):
        d = self.d
        jg = scalar(d.get("gate"), "gate").strip()
        if jg and jg != self.gate:
            self.warn(f'"gate": {jg!r} in the JSON, but the file name says {self.gate!r}; the file name wins')
        for k in ("title", "summary", "not_reviewed", "animatic"):
            d[k] = scalar(d.get(k), k).strip()
        if not d["summary"]:
            self.err("`summary` is missing: one line saying what this page asks and how long it takes")
        for k in ("decided", "delegated"):
            d[k] = [scalar(v, f"{k}[{i}]") for i, v in enumerate(as_list(d.get(k), k))]
        if d.get("decisions") is None:
            self.err("`decisions` is missing: use [] when there is nothing to decide")
        decs = [dict(as_dict(x, f"decisions[{i}]")) for i, x in enumerate(as_list(d.get("decisions"), "decisions"))]
        d["decisions"] = decs
        if len(decs) > MAX_DECISIONS:
            self.warn(f"{len(decs)} decisions on one page: the default is at most {MAX_DECISIONS} (upstream first, the rest "
                      "on the next page); keep them together only if the human asked to see more at once")
        ids = []
        for i, dec in enumerate(decs, 1):
            opts = []
            for j, o in enumerate(as_list(dec.get("options"), f"decisions[{i - 1}].options"), 1):
                o = dict(o) if isinstance(o, dict) else {"id": scalar(o, f"decisions[{i - 1}].options[{j - 1}]")}
                for k in ("id", "label", "pro", "con"):
                    o[k] = scalar(o.get(k), f"decisions[{i - 1}].options[{j - 1}].{k}").strip()
                if not o["id"]:
                    self.err(f"decision {i}: option {j} has no `id`")
                opts.append(o)
            dec["options"] = opts
            for k in ("id", "question", "recommend", "why", "cost", "reply"):
                dec[k] = scalar(dec.get(k), f"decisions[{i - 1}].{k}").strip()
            if not dec["question"]:
                self.err(f"decision {i}: no `question`")
            if not dec["recommend"]:
                self.err(f"decision {i} ({dec['id'] or '?'}): no `recommend`; every decision carries the agent's pick")
            if not dec["reply"]:
                if [o for o in opts if o["id"]]:
                    dec["reply"] = " / ".join(o["id"] for o in opts if o["id"])
                else:
                    self.err(f"decision {i} ({dec['id'] or '?'}): no `reply` and no `options` to build one from")
            if opts and dec["recommend"] and dec["recommend"] not in {o["id"] for o in opts}:
                self.warn(f"decision {i}: recommend {dec['recommend']!r} is not one of the option ids")
            bare = [o["id"] for o in opts if re.fullmatch(r"\d+", o["id"])]
            if bare:
                self.warn(f"decision {i}: option ids {bare} are bare numbers and read like decision numbers in the "
                          "combined reply (use T1, A, H2 …)")
            dec["id"] = dec["id"] or f"d{i}"
            ids.append(dec["id"])
        seen = {}
        for i, dec in enumerate(decs, 1):
            for oid in {o["id"] for o in dec["options"] if o["id"]}:
                seen.setdefault(oid, []).append(i)
        rep = {k: v for k, v in seen.items() if len(v) > 1}
        if rep:
            self.warn(f"option ids {sorted(rep)} appear in more than one decision; the take-all reply keeps them apart by "
                      "number, but a freeform reply like 'A' is ambiguous: give each decision its own ids (A/B, H1/H2, T1/T2 …)")
        least = []
        for i, x in enumerate(as_list(d.get("least_sure"), "least_sure")):
            x = dict(x) if isinstance(x, dict) else {"note": scalar(x, f"least_sure[{i}]")}
            least.append({"id": scalar(x.get("id"), f"least_sure[{i}].id").strip(),
                          "note": scalar(x.get("note"), f"least_sure[{i}].note").strip()})
        d["least_sure"] = least
        segs = [dict(as_dict(x, f"segments[{i}]")) for i, x in enumerate(as_list(d.get("segments"), "segments"))]
        d["segments"] = segs
        for i, s in enumerate(segs, 1):
            s["id"] = scalar(s.get("id"), f"segments[{i - 1}].id").strip() or str(i)
            ids.append(s["id"])
            for k in ("title", "note"):
                s[k] = scalar(s.get(k), f"segments[{i - 1}].{k}").strip()
            s["t0"], s["t1"] = self.span(s, f"segment {s['id']}")
            shots = [dict(as_dict(x, f"segments[{i - 1}].shots[{j}]"))
                     for j, x in enumerate(as_list(s.get("shots"), f"segments[{i - 1}].shots"))]
            s["shots"] = shots
            if len(shots) > MAX_SHOTS:
                self.warn(f"segment {s['id']}: {len(shots)} shots (a page reads best with 3–{MAX_SHOTS}); split it")
            for j, sh in enumerate(shots):
                for k in ("id", "frame", "see", "vo", "note"):
                    sh[k] = scalar(sh.get(k), f"segments[{i - 1}].shots[{j}].{k}").strip()
                if not sh["id"]:
                    self.err(f"segment {s['id']}: shot {j + 1} has no `id`")
                elif sh["id"] in self.shot_ids:
                    self.err(f"shot {sh['id']} appears twice")
                self.shot_ids.add(sh["id"])
                sh["t0"], sh["t1"] = self.span(sh, f"shot {sh['id']}")
        for it in least:
            if it["id"]:
                if self.shot_ids and it["id"] not in self.shot_ids:
                    self.warn(f"least_sure {it['id']!r} matches no shot; it is listed as text")
                self.flagged.setdefault(it["id"], it["note"])
        dup = sorted({x for x in ids if ids.count(x) > 1})
        if dup:
            self.err(f"duplicate decision / segment ids: {dup} (assets point at them with `for`)")
        assets = []
        for i, a in enumerate(as_list(d.get("assets"), "assets")):
            a = dict(as_dict(a, f"assets[{i}]"))
            for k in ("path", "caption", "for", "poster"):
                a[k] = scalar(a.get(k), f"assets[{i}].{k}").strip()
            a["t0"], a["t1"] = self.span(a, f"asset {a['path']}")
            if not a["path"]:
                self.err(f"assets[{i}] has no `path`")
            elif a["for"] and a["for"] not in ids:
                self.err(f"asset {a['path']}: `for` {a['for']!r} names no decision or segment")
            assets.append(a)
        d["assets"] = assets
        app = []
        for i, a in enumerate(as_list(d.get("appendix"), "appendix")):
            a = dict(as_dict(a, f"appendix[{i}]"))
            app.append({k: scalar(a.get(k), f"appendix[{i}].{k}").strip() for k in ("title", "text", "path")})
        d["appendix"] = app

    def span(self, x, what):
        t0, t1 = seconds(x.get("t0"), f"{what} t0"), seconds(x.get("t1"), f"{what} t1")
        if (t0 is not None and t0 < 0) or (t1 is not None and t1 < 0):
            self.warn(f"{what}: negative time ({t0}, {t1})")
        if t0 is not None and t1 is not None and t1 <= t0:
            self.warn(f"{what}: ends at {t1:g} s, not after it starts ({t0:g} s)")
        return t0, t1

    # ---- helpers -------------------------------------------------------------------------------------------
    def url(self, p, what):
        """A relative, percent-encoded URL from out/review/ to a project file; http(s) passes through escaped.
        Any other scheme (javascript:, data:, file: …) is refused: returns None and records an error."""
        p = txt(p).strip()
        if re.match(r"(?i)https?://", p):
            return html.escape(p, quote=True)
        if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", p) and not re.match(r"[A-Za-z]:[\\/]", p):
            if p not in self.bad_paths:
                self.bad_paths.add(p)
                self.err(f"{what}: {p!r} is neither a project path nor an http(s) URL; refused")
            return None
        f = Path(p) if os.path.isabs(p) else self.project / p
        if not os.path.exists(f) and p not in self.bad_paths:
            self.bad_paths.add(p)
            self.err(f"{what}: {p} does not exist")
        rel = os.path.relpath(f, self.out).replace(os.sep, "/")
        return quote(rel, safe="/-_.~()")   # spaces, quotes, <, >, # and ? are percent-encoded

    def text(self, s):
        """Escape, then `code`, **bold**, shot ids (S04) as links, newlines as <br>."""
        out = []
        for i, part in enumerate(re.split(r"`([^`]*)`", txt(s))):
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
        if u is None:
            return ""
        p = txt(path).strip()
        base = re.split(r"[?#]", p)[0] if re.match(r"(?i)https?://", p) else p   # a local "a#1.png" keeps its name
        ext = os.path.splitext(base)[1].lower()
        cap = f"<figcaption>{self.text(caption)}</figcaption>" if caption else ""
        if ext in IMG:
            alt = html.escape(re.sub(r"[`*]", "", txt(caption)) or os.path.basename(base))
            return f'<figure><a href="{u}" target="_blank"><img src="{u}" alt="{alt}" loading="lazy"></a>{cap}</figure>'
        if ext in VID:
            frag = data = ""
            if t1 is not None:
                a = t0 or 0.0
                frag, data = f"#t={a:g},{t1:g}", f' data-t0="{a:g}" data-t1="{t1:g}"'
            elif t0 is not None:
                frag = f"#t={t0:g}"
            elif not poster:
                frag = "#t=0.001"   # Safari paints nothing before play under preload="metadata" without it
            pu = self.url(poster, what) if poster else None
            pa = f' poster="{pu}"' if pu else ""
            return f'<figure><video controls preload="metadata" playsinline src="{u}{frag}"{data}{pa}></video>{cap}</figure>'
        if ext in AUD:
            return f'<figure class="audio">{cap}<audio controls preload="metadata" src="{u}"></audio></figure>'
        name = html.escape(os.path.basename(base))
        return f'<p><a href="{u}" target="_blank">{name}</a>{" · " + self.text(caption) if caption else ""}</p>'

    def assets_for(self, key):
        return [a for a in self.d["assets"] if a["for"] == key]

    def loose_assets(self):
        ids = {x["id"] for x in self.d["decisions"]} | {s["id"] for s in self.d["segments"]}
        return [a for a in self.d["assets"] if a["for"] not in ids]

    def example_shot(self, shots=None):
        """The shot id a reply hint uses: from the given shots (a segment), else the first least-sure shot, else the
        first shot; None when the page has no shots."""
        if shots:
            return next((sh["id"] for sh in shots if sh["id"] in self.flagged), shots[0]["id"]) or None
        for it in self.d["least_sure"]:
            if it["id"] in self.shot_ids:
                return it["id"]
        return next((sh["id"] for s in self.d["segments"] for sh in s["shots"] if sh["id"]), None)

    def rec_label(self, dec):
        """The recommended option's label, shown next to its id."""
        return next((o["label"] for o in dec["options"] if o["id"] == dec["recommend"] and o["label"]), "")

    def take_all(self):
        return " · ".join(f"{i} {dec['recommend']}" for i, dec in enumerate(self.d["decisions"], 1))

    # ---- sections ------------------------------------------------------------------------------------------
    def decisions_block(self):
        t, decs, rows = self.t, self.d["decisions"], []
        for i, dec in enumerate(decs, 1):
            label = f" {self.text(self.rec_label(dec))}" if self.rec_label(dec) else ""
            why = f' <span class="why">— {self.text(dec["why"])}</span>' if dec["why"] else ""
            cost = f'<div class="cost">{self.text(dec["cost"])}</div>' if dec["cost"] else "<div></div>"
            rows.append(f'<div class="drow"><a class="num" href="#d-{esc(dec["id"])}">{i}</a><div>'
                        f'<div class="q">{self.text(dec["question"])}</div>'
                        f'<div class="rec">{t["rec"]} <b>{esc(dec["recommend"])}</b>{label}{why}</div>'
                        f'<div class="rep">{t["reply"]} <code>{esc(dec["reply"])}</code></div></div>{cost}</div>')
        shot = self.example_shot()
        rest = t["rest"].format(shot=esc(shot)) if shot else t["rest_plain"]
        if decs:
            allr = self.take_all()
            foot = (f'<div class="takeall"><span>{t["take_all"]}</span><code>{esc(allr)}</code>'
                    f'<button id="copy" data-text="{esc(allr)}" data-done="{t["copied"]}">{t["copy"]}</button>'
                    f'<span class="rest">{rest}</span></div>')
        else:
            foot = f'<div class="rest">{t["nothing"]}</div>'
        head = t["decide"].format(n=len(decs)) if decs else t["look"]
        return f'<div class="card decide" id="decide"><h2>{head}</h2>{"".join(rows)}{foot}</div>'

    def lines_block(self):
        t, d, out = self.t, self.d, []
        if d["least_sure"]:
            chips = []
            for it in d["least_sure"]:
                sid = it["id"]
                label = (f'<a href="#shot-{esc(sid)}">{esc(sid)}</a> ' if sid in self.shot_ids else (esc(sid) + " " if sid else ""))
                chips.append(f'<span class="chip flag">{label}{self.text(it["note"])}</span>')
            out.append(f'<div><span class="k">{t["least"]}</span>{"".join(chips)}</div>')
        for key in ("decided", "delegated"):
            if len(d[key]) > 2:      # a long list reads as a wall on one line
                items = "".join(f"<li>{self.text(v)}</li>" for v in d[key])
                out.append(f'<div><span class="k">{t[key]}</span><ul class="mini">{items}</ul></div>')
            elif d[key]:
                out.append(f'<div><span class="k">{t[key]}</span>{t["sep"].join(self.text(v) for v in d[key])}</div>')
        if d["not_reviewed"]:
            out.append(f'<div><span class="k">{t["not_reviewed"]}</span>{self.text(d["not_reviewed"])}</div>')
        return f'<div class="lines">{"".join(out)}</div>' if out else ""

    def decision_sections(self):
        t, out = self.t, []
        for i, dec in enumerate(self.d["decisions"], 1):
            figs = "".join(self.media(a["path"], a["caption"], f"decision {dec['id']}", a["t0"], a["t1"], a["poster"] or None)
                           for a in self.assets_for(dec["id"]))
            opts, table = dec["options"], ""
            if opts:
                has_pc = any(o["pro"] or o["con"] for o in opts)
                head = f'<tr><th>{t["options"]}</th>' + (f'<th>{t["pro"]}</th><th>{t["con"]}</th>' if has_pc else "") + "</tr>"
                body = []
                for o in opts:
                    pick = o["id"] == dec["recommend"]
                    tag = f'<span class="tag">{t["rec"]}</span>' if pick else ""
                    label = f" {self.text(o['label'])}" if o["label"] else ""
                    cells = f'<td><b>{esc(o["id"])}</b>{label}{tag}</td>'
                    if has_pc:
                        cells += f'<td>{self.text(o["pro"])}</td><td>{self.text(o["con"])}</td>'
                    body.append(f'<tr class="{"pick" if pick else ""}">{cells}</tr>')
                table = f'<table>{head}{"".join(body)}</table>'
            label = f" {self.text(self.rec_label(dec))}" if self.rec_label(dec) else ""
            cost = f' · {self.text(dec["cost"])}' if dec["cost"] else ""
            meta = (f'<div class="meta">{t["rec"]} <b>{esc(dec["recommend"])}</b>{label} · {t["reply"]} '
                    f'<code>{esc(dec["reply"])}</code>{cost}</div>')
            out.append(f'<section id="d-{esc(dec["id"])}"><h2>{t["decision"].format(i=i)} · {self.text(dec["question"])}</h2>'
                       f'{meta}{figs}{table}</section>')
        return "".join(out)

    def other_section(self):
        rest = self.loose_assets()
        if not rest:
            return ""
        figs = "".join(self.media(a["path"], a["caption"], "asset", a["t0"], a["t1"], a["poster"] or None) for a in rest)
        return f'<section id="other"><h2>{self.t["other"]}</h2>{figs}</section>'

    def segment_sections(self):
        t, segs, colon = self.t, self.d["segments"], self.t["colon"]
        out = []
        for i, s in enumerate(segs, 1):
            shots = s["shots"]
            durs = [sh["t1"] - sh["t0"] for sh in shots if sh["t0"] is not None and sh["t1"] is not None]
            meta = [f'{s["t0"]:.1f}–{s["t1"]:.1f} s' if s["t0"] is not None and s["t1"] is not None else "",
                    t["shots"].format(n=len(shots)) if shots else "",
                    t["avg"].format(s=f"{sum(durs) / len(durs):.1f}") if durs else ""]
            first = next((sh["frame"] for sh in shots if sh["frame"]), "")
            ratio = (image_ratio(self.project / first) if first and not re.match(r"(?i)https?://", first) else None) or 16 / 9
            cols = 3 if ratio >= 1.2 else (4 if ratio >= 0.8 else 5)
            has_vo = any(sh["vo"] for sh in shots)
            cards, rows = [], []
            for sh in shots:
                sid, flag = sh["id"], sh["id"] in self.flagged
                dur = f'{sh["t1"] - sh["t0"]:.1f} s' if sh["t0"] is not None and sh["t1"] is not None else ""
                tr = f'{sh["t0"]:.1f}–{sh["t1"]:.1f} s · {dur}' if dur else ""
                img = ""
                if sh["frame"]:
                    u = self.url(sh["frame"], f"shot {sid} frame")
                    if u:
                        img = f'<a href="{u}" target="_blank"><img src="{u}" alt="{esc(sid)}" loading="lazy"></a>'
                why = f'{colon}{self.text(self.flagged[sid])}' if flag and self.flagged[sid] else ""
                unsure = f'<div class="u">? {t["unsure"]}{why}</div>' if flag else ""
                plan = f'<div class="p">→ {t["plan"]}{colon}{self.text(sh["note"])}</div>' if sh["note"] else ""
                cards.append(f'<div class="shotcard{" flag" if flag else ""}" id="shot-{esc(sid)}">{img}'
                             f'<div class="cap"><span class="id">{esc(sid)}</span><span class="t">{tr}</span>'
                             f'<div>{self.text(sh["see"])}</div>{unsure}{plan}</div></div>')
                planline = f'<div class="p">→ {t["plan"]}{colon}{self.text(sh["note"])}</div>' if sh["note"] else ""
                if flag:
                    st = f'<td class="st flag">? {self.text(self.flagged[sid]) or t["unsure"]}{planline}</td>'
                elif sh["note"]:
                    st = f'<td class="st">{planline}</td>'
                else:
                    st = f'<td class="st ok">✓ {t["ok"]}</td>'
                said = self.text(sh["vo"]) if has_vo else self.text(sh["see"])
                rows.append(f'<tr><td><a href="#shot-{esc(sid)}">{esc(sid)}</a></td><td>{dur}</td><td>{said}</td>{st}</tr>')
            table = ""
            if rows:
                third = t["vo"] if has_vo else t["see"]
                hint = self.example_shot(shots)
                table = (f'<div><table class="shotlist"><tr><th>{t["shot"]}</th><th>{t["dur"]}</th><th>{third}</th>'
                         f'<th>{t["status"]}</th></tr>{"".join(rows)}</table>'
                         f'<div class="small">{t["pass_all"].format(shot=esc(hint)) if hint else t["rest_plain"]}</div></div>')
            clip = ""
            if self.d["animatic"] and s["t0"] is not None and s["t1"] is not None:
                cap = t["clip"].format(a=f'{s["t0"]:.1f}', b=f'{s["t1"]:.1f}')
                clip = self.media(self.d["animatic"], cap, "animatic", s["t0"], s["t1"], first or None)
            body = f'<div class="segbody"><div>{clip}</div>{table}</div>' if (clip or table) else ""
            extra = "".join(self.media(a["path"], a["caption"], f"segment {s['id']}", a["t0"], a["t1"], a["poster"] or None)
                            for a in self.assets_for(s["id"]))
            note = f'<div class="segnote">{self.text(s["note"])}</div>' if s["note"] else ""
            nflag = sum(1 for sh in shots if sh["id"] in self.flagged)
            badge = f'<span class="chip flag">{t["n_unsure"].format(n=nflag)}</span>' if nflag else ""
            out.append(f'<section class="segment" id="seg-{esc(s["id"])}"><div class="seghead">'
                       f'<h2>{t["seg"].format(i=i, n=len(segs))} · {self.text(s["title"])}</h2>'
                       f'<span class="meta">{" · ".join(m for m in meta if m)}</span>{badge}</div>{note}'
                       f'<div class="shots" style="--cols:{cols};--ar:{ratio:.4f}">{"".join(cards)}</div>{body}{extra}</section>')
        return "".join(out)

    def blocks(self, s):
        """Text with simple pipe tables: a run of lines starting with | whose second line is |---| becomes a table."""
        out, para, lines, i = [], [], txt(s).split("\n"), 0
        cells = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
        while i < len(lines):
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"):
                j += 1
            if j - i >= 2 and re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?", lines[i + 1].strip()):
                if para:
                    out.append(f'<div class="text">{self.text(chr(10).join(para))}</div>')
                    para = []
                head = "".join(f"<th>{self.text(c)}</th>" for c in cells(lines[i]))
                body = "".join("<tr>" + "".join(f"<td>{self.text(c)}</td>" for c in cells(l)) + "</tr>" for l in lines[i + 2:j])
                out.append(f"<table><tr>{head}</tr>{body}</table>")
                i = j
            else:
                para.append(lines[i])
                i += 1
        if para:
            out.append(f'<div class="text">{self.text(chr(10).join(para))}</div>')
        return "".join(out)

    def appendix_section(self):
        items = []
        for a in self.d["appendix"]:
            body = self.blocks(a["text"]) if a["text"] else ""
            if a["path"]:
                body += self.media(a["path"], "", "appendix")
            items.append(f'<details><summary>{self.text(a["title"])}</summary>{body}</details>')
        return f'<section id="appendix"><h2>{self.t["appendix"]}</h2>{"".join(items)}</section>' if items else ""

    def nav(self):
        t = self.t
        links = [f'<a href="#decide">{t["nav_decide"]}</a>']
        if self.loose_assets():
            links.append(f'<a href="#other">{t["nav_other"]}</a>')
        for i, s in enumerate(self.d["segments"], 1):
            n = sum(1 for sh in s["shots"] if sh["id"] in self.flagged)
            flag = f'<span class="nf">{t["n_unsure"].format(n=n)}</span>' if n else ""
            links.append(f'<a href="#seg-{esc(s["id"])}">{i} {esc(s["title"])}</a>{flag}')
        if self.d["appendix"]:
            links.append(f'<a href="#appendix">{t["nav_appendix"]}</a>')
        return f'<nav>{"".join(f"<span>{x}</span>" for x in links)}</nav>'

    def others(self):
        pages = sorted(p for p in self.out.glob("gate-*.html") if p.name != f"gate-{self.gate}.html")
        if not pages:
            return ""
        links = " · ".join(f'<a href="{quote(p.name)}">{esc(gate_title(p.stem[5:], self.lang))}</a>' for p in pages)
        return f'{self.t["others"]}{self.t["colon"]}{links}<br>'

    def render(self):
        self.normalize()
        t, title = self.t, self.title()
        body = (self.decisions_block() + self.lines_block() + self.decision_sections() + self.other_section()
                + self.segment_sections() + self.appendix_section())
        src = os.path.relpath(self.src, self.project).replace(os.sep, "/")
        return (f'<!doctype html><html lang="{t["html_lang"]}"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width, initial-scale=1">'
                f'<title>{esc(title)} · {esc(self.project.name)}</title>'
                f'<style>{CSS}</style><script>{HEAD_JS}</script></head><body><div class="wrap">'
                f'<header><div class="eyebrow"><span>{esc(self.project.name)} · {esc(title)}</span>'
                f'<button id="theme" title="{t["theme"]}" aria-label="{t["theme"]}">◐</button></div>'
                f'<h1>{self.text(self.d["summary"])}</h1>{self.nav()}</header>'
                f'{body}<footer>{self.others()}{t["src"].format(src=esc(src))}</footer></div>'
                f'<script>{BODY_JS}</script></body></html>\n')

    def chat(self, page_path):
        """The whole chat message: plain text, no markup."""
        t, decs, title = self.t, self.d["decisions"], self.title()
        plain = lambda s: re.sub(r"\*\*(.+?)\*\*", r"\1", txt(s)).replace("`", "")
        lines = [t["chat_head"].format(title=title, n=len(decs)) if decs else t["chat_none"].format(title=title)]
        for i, dec in enumerate(decs, 1):
            r = dec["recommend"] + (t["quoted"].format(x=self.rec_label(dec)) if self.rec_label(dec) else "")
            why = t["why"].format(w=plain(dec["why"])) if dec["why"] else ""
            lines.append(t["chat_item"].format(i=i, q=plain(dec["question"]), r=plain(r), why=why, reply=plain(dec["reply"])))
        if decs:
            lines.append(t["chat_all"].format(all=self.take_all()))
        if self.d["least_sure"]:
            red = t["chat_red"] if any(it["id"] in self.shot_ids for it in self.d["least_sure"]) else ""
            lines.append(t["chat_least"].format(red=red))
            for it in self.d["least_sure"]:
                both = t["colon"].join(x for x in (it["id"], plain(it["note"])) if x)
                lines.append(f"   {both}")
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
    ap.add_argument("gate", nargs="?", help="1 | 2 | 3 | E0–E5 | 2b … (gate-2, gate-2.json too); default: the newest gate-*.json")
    a = ap.parse_args()
    project = find_project(a.project)
    if not project:
        print(f"no such project: {a.project}", file=sys.stderr)
        return 2
    rdir = project / "out" / "review"
    if a.gate:
        g = re.sub(r"\.json$", "", re.sub(r"^gate-", "", a.gate.strip()))
        if not re.fullmatch(r"[A-Za-z0-9_-]+", g):
            print(f"not a gate name: {a.gate!r} (1, 2, 3, E0–E5, 2b …)", file=sys.stderr)
            return 2
        found = [rdir / f"gate-{g}.json"]
    else:
        found = sorted(rdir.glob("gate-*.json"), key=lambda p: p.stat().st_mtime)
    if not found or not os.path.exists(found[-1]):
        where = found[-1] if found else rdir / "gate-<n>.json"
        print(f"no review pack at {where}: write one first (playbook/01-pipeline.md, 审阅页)", file=sys.stderr)
        return 2
    src = found[-1]
    gate = src.stem[5:]
    try:
        data = json.loads(src.read_text(encoding="utf-8-sig"))   # a BOM from a Windows editor is fine
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")
    except OSError as e:
        print(f"can't read {src}: {e.strerror or e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"{src}: {e}", file=sys.stderr)
        return 2
    page = Page(project, src, data, gate)
    try:
        doc = page.render()
    except (AttributeError, KeyError, TypeError, ValueError) as e:   # a field of the wrong shape, e.g. a string for a list
        print(f"{src}: a field has the wrong shape ({type(e).__name__}: {e}); compare with playbook/01-pipeline.md, 审阅页",
              file=sys.stderr)
        return 2
    page_path = rdir / f"gate-{gate}.html"
    try:
        for p in (page_path, rdir / "index.html"):
            p.write_text(doc, encoding="utf-8")
    except OSError as e:
        print(f"can't write {rdir}: {e.strerror or e}", file=sys.stderr)
        return 2
    for w in page.warnings:
        print(f"! {w}", file=sys.stderr)
    for e in page.errors:
        print(f"✗ {e}", file=sys.stderr)
    segs = data["segments"]
    what = (f"{page.title()} · {len(data['decisions'])} decision(s) · {len(segs)} segment(s) · "
            f"{sum(len(s['shots']) for s in segs)} shot(s)")
    if page.errors:
        print(f"✗ {page_path} written with {len(page.errors)} problem(s) above ({what}); fix them before sending, "
              "so no chat message this time", file=sys.stderr)
        return 1
    print(f"✓ {page_path}, also index.html  ({what})", file=sys.stderr)
    print(page.chat(page_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
