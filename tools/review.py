"""Review page: out/review/gate-<n>.json -> a local HTML page a human can look at and listen to.

usage: python3 tools/review.py <project> [gate]
  <project>  the project directory, or its name under $OVH_PROJECTS / projects/ (the date prefix may be left out)
  [gate]     1 | 2 | 3 | E0-E5 | 2b ... (gate-2 and gate-2.json work too; 1 to 24 letters, digits, - or _);
             default: this round, i.e. out/review/.current, else the last page in review order (name a new page)

The file name sets the gate: gate-2b.json is page 2 of gate ②, whatever its "gate" field says (a mismatch is a
warning). Writes out/review/gate-<n>.html, and the same page as out/review/index.html (always the latest page), notes
<n> in out/review/.current (the review desk's "this round"), then
prints the chat message: the decisions, the reply that takes every recommendation, the least-sure shots, and the path
of gate-<n>.html, which a later page does not overwrite. playbook/01-pipeline.md ("审阅页") explains the page and
every field:

  summary, decisions[{id, question, options[{id, label, pro, con} | "id"], recommend, why, cost, reply, columns}],
  assets[{path, caption, for, t0, t1, poster}], least_sure[{id, note} | "note"], animatic,
  segments[{id, title, t0, t1, note, shots[{id, t0, t1, frame, see, vo, note}]}], appendix[{title, text, path}]
  optional: version (1, as bin/vh gate --init writes it; not read), gate, title, lang (zh | en; default: the BRIEF's "Review
  language" line, else zh), decided[], delegated[], not_reviewed, include (a JSON file, or a list of them, whose keys fill in
  what this file does not set: bin/vh storyboard writes out/check/storyboard/review.json for gate ②). The review desk (bin/vh
  desk, tools/desk/README.md) reads the same file and a few more optional keys (listen, music, film); this page ignores them.
  With JavaScript the page also shows its stop's module read only, above the gate view, as the console draws it (立意 and
  大纲 for gate ①, 分镜 for ②, 声音 for E2 and E3; tools/desk/static/modules.js): the project's data for it goes into the
  page, with the console's renderers. Without JavaScript, or when the project cannot be read, the page is the gate view.
  A text that still holds a {填：…} or {fill in: …} from bin/vh gate --init, here or in a file it includes, is not ready: nothing
  is written (exit 2), and the file is no page yet for bin/vh status, the desk or this round.

Paths are relative to the project and linked relatively, so the page opens straight from disk (images, GIF, mp4 and
audio play in the browser); http(s) URLs pass through, other schemes are refused. Every text is HTML-escaped; appendix
text may hold simple pipe tables (| a | b | / |---|---| / | 1 | 2 |).

Exit: 0 written (warnings, e.g. more than 3 decisions, go to stderr) · 1 written, but the page breaks a rule
(a decision without a question, recommendation or reply, an option without an id, a missing file, a refused URL,
an unknown `for`, a duplicate id); no chat message then, and out/review/.gate-<n>.refused.json keeps what is wrong, so that
bin/vh status does not take the page for one the person has, until a run of it goes through · 2 nothing written (no project, no JSON, bad JSON, a field
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

GATES = {"1": ("关卡 ① 立意和大纲", "Gate ① concept and outline"), "2": ("关卡 ② 分镜", "Gate ② storyboard"),
         "3": ("关卡 ③ 初版", "Gate ③ first draft"), "E0": ("检查点 E0 样帧", "Checkpoint E0 style frames"),
         "E1": ("检查点 E1 脚本", "Checkpoint E1 script"), "E2": ("检查点 E2 声音", "Checkpoint E2 sound"),
         "E3": ("检查点 E3 锁时", "Checkpoint E3 timing lock"), "E4": ("检查点 E4 样板章", "Checkpoint E4 sample chapter"),
         "E5": ("检查点 E5 锁画面", "Checkpoint E5 picture lock")}

T = {
    "zh": dict(html_lang="zh-CN", settled_done="定了", settled_skipped="没单独停", settled_delivered="已交付", settled_note="这一页已经定了，现在只是记录。要改，跟做这支片子的 AI 说。", asked_then="当时问的：", for_dec="关于第 {n} 件", for_dec_s="第 {n} 件", n_decide="等你定 {n} 件", look="这一页只给你看", wait="等你看",
               nothing="这一页没有等你定的事。看完回“通过”，或写要改的。",
               rec="推荐", why_rec="为什么推荐：{w}", reply="回", take_all="照推荐回复", yours="你的回复", copy="复制", copied="已复制",
               rest="没写意见的就算通过；要改哪一镜，写“{shot} 改：……”。", rest_plain="没写意见的就算通过，只写要改的。",
               unanswered="不选就按推荐；", submit="发出去", live_note="不选就按推荐；没写意见就算通过。",
               changed="改了：{x}", least="AI 没把握的", listen="请你听这几处", decided="已经定了", delegated="AI 替你定了",
               not_reviewed="<b>AI 没看、没听的</b> {x}", material="材料", appendix="附录", board="分镜", film="成片", pictures="画面",
               pro="好处", con="代价", titles="标题", cover="封面", seg="{i} / {n}", shots="{n} 镜", avg="平均一镜 {s} 秒", unsure="没把握", n_unsure="{n} 镜没把握",
               plan="打算改", pass_all="没写意见的镜头就算通过；要改的，写“{shot} 改：……”。", no_frame="没有关键帧",
               gone="找不到这个文件（挪走或改了名）", gone_n="这一页发出以后，有 {n} 个文件找不到了（挪走或改了名）",
               others="其他审阅页", src="审阅页", warn="这一页有 {n} 处没按规矩写，修好以前不会发给人：",
               spend="已花 {spent} / 预算 {budget}", no_budget="没有预算", unlimited="不限", over="超了：{cur}",
               theme="主题", themes=("暗场", "棱镜", "舰桥"), play="播放 / 暂停（空格）", mute="静音", full="全屏", keys="空格播放 · ← → 跳镜头 · 1 2 3 选选项",
               page="页面", chat_head="{title} · 等你定 {n} 件", chat_none="{title} · 没有等你定的事，看一眼，回“通过”或写要改的。",
               chat_item="{i}. {q} 回 {reply}\n   推荐 {r}{why}", chat_all="照推荐就回：{all}。不选的就按推荐，没写意见的就算通过。",
               chat_least="我最没把握的{red}：", chat_red="（镜头在页面里标红）",
               why="：{w}", sep="；", colon="：", quoted="「{x}」"),
    "en": dict(html_lang="en", settled_done="Decided", settled_skipped="Not shown on its own", settled_delivered="Delivered", settled_note="This page is settled; it is a record now. To change something, tell the AI making the film.", asked_then="Asked then: ", for_dec="for decision {n}", for_dec_s="#{n}", n_decide="{n} to decide", look="Just for a look", wait="waiting for you",
               nothing="Nothing to decide on this page. Take a look, then reply “ok” or say what to change.",
               rec="recommended", why_rec="Why: {w}", reply="Reply", take_all="Take every recommendation", yours="Your reply",
               copy="Copy", copied="Copied",
               rest="No note means it passes; to change a shot, write “{shot} change: …”.",
               rest_plain="No note means it passes; write only what to change.",
               unanswered="If you don't pick, the recommended one goes. ", submit="Send",
               live_note="If you don't pick, the recommended one goes; no note means it passes.",
               changed="changed: {x}", least="Where the AI is unsure", listen="Please listen to these", decided="Already decided",
               delegated="Decided for you", not_reviewed="<b>What the AI didn't see or hear</b> {x}", material="Material", appendix="Appendix",
               board="Storyboard", film="The film", pictures="Pictures", pro="Pro", con="Cost", titles="Titles", cover="Cover", seg="{i} / {n}", shots="{n} shots",
               avg="{s} s a shot", unsure="unsure", n_unsure="{n} unsure", plan="will change",
               pass_all="A shot with no note passes; to change one, write “{shot} change: …”.", no_frame="no key frame",
               gone="File not found (moved or renamed)", gone_n="Files that can't be found since this page went out (moved or renamed): {n}",
               others="Other review pages", src="Review page",
               warn="Places where this page breaks the rules: {n}. It goes to nobody until they are fixed:",
               spend="Spent {spent} of {budget}", no_budget="no budget", unlimited="no cap", over="over: {cur}",
               theme="Theme", themes=("Darkfield", "Prism", "Bridge"), play="Play / pause (space)", mute="Mute", full="Full screen",
               keys="Space plays · ← → jump shots · 1 2 3 pick an option",
               page="Page", chat_head="{title} · {n} to decide",
               chat_none="{title} · nothing to decide; take a look and reply “ok” or say what to change.",
               chat_item="{i}. {q} Reply {reply}\n   Recommended: {r}{why}",
               chat_all="To take every recommendation, reply: {all}. If you don't pick, the recommended one goes; no note means it passes.",
               chat_least="Least sure about{red}:", chat_red=" (shots are red on the page)",
               why=" — {w}", sep="; ", colon=": ", quoted=" “{x}”"),
}

# The word budget (playbook/01-pipeline.md, 审阅页): the first line is read before anything else, so it stays short; the rest
# of what the agent wants to say goes into the decisions, the folds and the appendix. A warning, never a refusal.
BUDGET = {"summary": (40, 100), "question": (30, 80), "label": (20, 50), "note": (40, 100)}

STATIC = Path(__file__).resolve().parent / "desk" / "static"   # ui.css and ui.js: one stylesheet and one script for the static
# page (inlined) and the console (served), so the gate view looks and behaves the same in both

TIME_ID = re.compile(r"^\s*(?:(\d+):)?(\d+(?:\.\d+)?)\s*(?:[–—-]\s*(?:(\d+):)?(\d+(?:\.\d+)?))?\s*s?\s*$")   # "12.4 s", "0–5 s", "1:05–1:12"


def budget_len(s):
    """The length a word budget counts: a CJK character is 1, any other visible character ½ (so "48 s" is 1.5);
    text without CJK counts its characters. → (length, has CJK)."""
    s = re.sub(r"\s+", " ", re.sub(r"[`*]", "", txt(s))).strip()
    cjk = len(re.findall(r"[　-鿿豈-﫿＀-￯]", s))
    if not cjk:
        return len(s), False
    return cjk + 0.5 * len(re.sub(r"[\s　-鿿豈-﫿＀-￯]", "", s)), True


def over_budget(s, key):
    """(length, limit) when the text is over its word budget, else None."""
    n, zh = budget_len(s)
    lim = BUDGET[key][0 if zh else 1]
    return (n, lim) if n > lim else None


def shot_label(sid):
    """A shot as the page writes it: S4, never S04 or S004 (the console writes it the same way). Its anchor, its
    data and the reply keep the id as given."""
    return re.sub(r"^([A-Za-z]+)0+(?=\d)", r"\1", sid or "")


def time_of(label):
    """'12.4 s', '0–5 s', '1:05–1:12' → (t0, t1 or None); anything else → None. A least-sure item names a time this way."""
    m = TIME_ID.match(txt(label))
    if not m or not (m.group(2)):
        return None
    t0 = float(m.group(2)) + 60 * int(m.group(1) or 0)
    t1 = float(m.group(4)) + 60 * int(m.group(3) or 0) if m.group(4) else None
    return t0, (t1 if t1 is not None and t1 > t0 else None)


COST_ZH = {"低": "不贵", "中": "要花些工夫", "高": "很贵", "很高": "非常贵"}
COST_EN = {"low": "cheap", "medium": "some work", "high": "costly", "very high": "very costly"}
STAGE_ZH = {"锁画面": "定稿", "分镜": "分镜定了", "成片": "出了成片", "初版": "初版定了"}


def cost_words(s, lang="zh"):
    """What a change costs, as a sentence: "现在改：中 · 锁画面后改：高" → "现在改要花些工夫，定稿以后再改就很贵". The levels
    gate --init writes (低 中 高, low medium high); any other wording stays as the agent wrote it. The words' own language
    decides (a page in English over a gate written in Chinese keeps the Chinese, said as a sentence)."""
    s = str(s or "")
    if lang == "zh" or re.search(r"[\u3400-\u9fff]", s):
        s = re.sub(r"现在改：(很高|低|中|高)", lambda m: "现在改" + COST_ZH[m.group(1)], s)
        s = re.sub(r"(\S+?)后改：(很高|低|中|高)", lambda m: f"{STAGE_ZH.get(m.group(1), m.group(1))}以后再改就{COST_ZH[m.group(2)]}", s)
        return s.replace(" · ", "，")
    s = re.sub(r"\bnow: (very high|low|medium|high)", lambda m: f"{COST_EN[m.group(1)].capitalize()} to change now", s)
    s = re.sub(r"\bafter (?:the )?(.+?): (very high|low|medium|high)", lambda m: f"{COST_EN[m.group(2)]} after the {m.group(1)}", s)
    return s.replace(" · ", "; ")


def clock(x):
    """seconds → 0:12.4 (tabular figures do the rest)."""
    if x is None:
        return ""
    m, s = divmod(max(0.0, float(x)), 60)
    return f"{int(m)}:{s:04.1f}"


def static_file(name):
    try:
        return (STATIC / name).read_text(encoding="utf-8")
    except OSError:
        return ""


# the console's modules a static page shows above its gate view, read only, by the gate's base (tools/desk/static/modules.js);
# a stop the cut module stands for (③, E4, E5) has none: the gate view's player and its ruler are its static version
STATION_MODULES = {"1": ("idea", "outline"), "E0": ("idea",), "E1": ("outline",), "2": ("board",), "E2": ("sound",), "E3": ("sound",)}


def module_payload(project, gate, out_dir, marks, lang):
    """What a static page's module reads, as JSON for a <script type="application/json">: the console's reading of the project
    (tools/desk/server.py, project_data) cut to what the stop's modules use, the page's marks, and the way from the page's
    folder to the project's files. None for a stop with no module, or a project that cannot be read."""
    mods = STATION_MODULES.get((re.match(r"E\d|\d", gate or "") or [""])[0])
    if not mods:
        return None
    here = str(STATIC.parent)   # tools/desk
    if here not in sys.path:
        sys.path.insert(0, here)
    import server   # noqa: E402  (imported here: it imports this file)
    d = server.project_data(project, parts=("studio", "mods") if "sound" in mods else ())
    st = d.get("status") or {}
    data = {k: d.get(k) for k in ("project", "concept", "spec", "outline", "facts", "ideas", "shots", "ledger", "agent_decided", "music", "lang")}
    data["rounds"] = [{"id": r["id"], "data": r["data"]} for r in d.get("rounds") or []]
    data["current"] = gate   # the page's own round: its decisions are the ones the module picks
    data["history"] = [{k: h.get(k) for k in ("title", "date", "quotes", "notes")} for h in d.get("history") or []]
    data["status"] = {"stations": st.get("stations") or [], "assets": {"budget": ((st.get("assets") or {}).get("budget") or {})}}
    data["docs"] = [x for x in d.get("docs") or [] if x.get("file") == "STORYBOARD.md"] if "board" in mods else []
    cur = d.get("current")
    if cur and cur != gate and d.get("round_open"):   # a page made after its stop: the open round's unsure places count in its outline as in the console
        try:
            more = [m for m in page_for(project, cur, lang=lang).marks() if m["kind"] == "least" and m["t"] is not None]
        except (ValueError, OSError, AttributeError, KeyError, TypeError):
            more = []
        marks = list(marks) + [m for m in more if m["target"] not in {x["target"] for x in marks}]
    data["marks"] = marks
    if "sound" in mods:
        tl = (d.get("studio") or {}).get("timeline") or {}
        data["studio"] = {"timeline": {"narration": tl.get("narration") or [], "duration": tl.get("duration")}, "peaks": (d.get("studio") or {}).get("peaks"),
                          "film": (d.get("studio") or {}).get("film")}
        data["mods"] = {k: (d.get("mods") or {}).get(k) for k in ("loudness", "silences", "checks", "pace", "voice", "audition", "lifts", "errors")}
    rel = os.path.relpath(project, out_dir).replace(os.sep, "/")
    body = json.dumps({"modules": list(mods), "lang": lang, "rel": "" if rel == "." else rel + "/", "data": data}, ensure_ascii=False, separators=(",", ":"))
    # nothing in it can close the script element or read as markup, and no address reads as one to load
    return body.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("/", "\\/")


HEAD_JS = """(function(){var r=document.documentElement,k=['darkfield','prism','bridge'],t=null;try{t=new URLSearchParams(location.search).get('theme')}catch(e){}
if(k.indexOf(t)<0){try{t=localStorage.getItem('ovh-theme')}catch(e){}}
if(k.indexOf(t)>=0)r.setAttribute('data-theme',t)})();"""

ICON = {"play": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l12-7.5z"/></svg>',
        "big": '<svg viewBox="0 0 54 54" aria-hidden="true"><path d="M20 15v24l19-12z"/><path d="M2 12V2h10M42 2h10v10M52 42v10H42M12 52H2V42"/></svg>',
        "mute": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9.5h4l5-4v13l-5-4H4z"/><path d="M16.5 9a4 4 0 0 1 0 6M19 6.5a7.5 7.5 0 0 1 0 11"/></svg>',
        "full": '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6"/></svg>'}


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
    """1 → 关卡 ① 立意和大纲, E1 → 检查点 E1 脚本, 2b → 关卡 ② 分镜（第 2 页）; anything else → 审阅页 <g>."""
    base, suffix = (g[:-1], g[-1]) if len(g) > 1 and g[-1].isalpha() and g[:-1] in GATES else (g, "")
    name = GATES.get(base, (f"审阅页 {g}", f"Review page {g}"))[0 if lang == "zh" else 1]
    if suffix:
        n = ord(suffix.lower()) - ord("a") + 1
        name += f"（第 {n} 页）" if lang == "zh" else f" (page {n})"
    return name


def stop_settled(project, gate):
    """How the stop a page is for stands now, by bin/vh status: "delivered" (the film went out), "done", "skipped", or None
    (still open, or the project does not read). A static page made after that is said as a record, nothing to pick."""
    try:
        import status as S   # noqa: E402  (imported here: it imports this file)
        st = S.collect(Path(project), light=True)
    except (Exception, SystemExit):
        return None
    base = (re.match(r"E\d|\d", gate or "") or [""])[0]
    s = next((x for x in st["stations"] if x["id"] == base), None)
    if s is None or s["state"] not in ("done", "skipped"):
        return None
    dl = next((x for x in st["stations"] if x["id"] == "deliver"), None)
    return "delivered" if dl and dl["state"] == "done" else s["state"]


# a checkpoint's name for a person, where the records' name (GATES) is a film-maker's shorthand: 锁时 → 定声音 (core.js's stn)
PERSON_NAMES = {"E0": ("画风样张", "style frames"), "E1": ("文案", "script"), "E2": ("配乐安排", "sound plan"), "E3": ("定声音", "final sound"),
                "E4": ("第一章样片", "first chapter"), "E5": ("定画面", "picture lock")}


def gate_name(g, lang):
    """A stop by its name, for a person to read (the page's header, the links between pages, the message the agent pastes
    in the chat): 关卡 ③ 初版 → 初版, 检查点 E3 锁时 → 定声音, 2b → 分镜（第 2 页）. gate_title's code (①, E1) stays in the
    terminal and the records."""
    title = gate_title(g, lang)
    base = g[:-1] if len(g) > 1 and g[-1].isalpha() and g[:-1] in GATES else g
    if base in PERSON_NAMES:
        title = re.sub(r"^((?:检查点|Checkpoint)\s*E\d\s*)\S+(?:\s+\S+)?(?=（|\s\(|$)", lambda m: m.group(1) + PERSON_NAMES[base][0 if lang == "zh" else 1], title)
    n = re.sub(r"^(?:关卡|检查点|Gate|Checkpoint)\s*(?:[①②③④⑤]|E\d)\s*", "", title) or title
    return n[:1].upper() + n[1:]


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
    """One gate page. link: how a project path becomes an href (None: relative from out/review/, the static page that opens
    from disk; the console passes its /f/ address); live: the console's gate view (a submit button instead of a reply to
    copy). The markup is otherwise the same."""

    def __init__(self, project: Path, src: Path, data: dict, gate: str, link=None, live=False):
        self.project, self.src, self.d, self.gate = project, src, data, gate
        self.link, self.live, self._extra, self._normal = link, live, None, False
        self.past = False   # the console showing a page that is no longer this round: what no longer matches is said quietly
        self.settled = None   # the static page of a stop settled since (stop_settled): a record, nothing to pick
        self.out = project / "out" / "review"
        lang = data.get("lang")
        # the same rule as the review desk: this page's lang, else the BRIEF's Review language, else zh
        self.lang = lang if isinstance(lang, str) and lang in T else (review_lang(project) or "zh")
        self.t = T[self.lang]
        self.errors, self.warnings = [], []
        self.shot_ids = set()
        self.flagged = {}      # shot id → least-sure note
        self.bad_paths = set() # each missing or refused path is reported once, however many places use it
        if lang is not None and self.lang != lang:
            self.warn(f"lang {lang!r} is not zh or en; using {self.lang}")

    def err(self, msg):
        if msg not in self.errors:   # a missing animatic used by six segments is reported once
            self.errors.append(msg)

    def warn(self, msg):
        if msg not in self.warnings:
            self.warnings.append(msg)

    def title(self):
        return self.d["title"] or gate_title(self.gate, self.lang)

    def name(self):   # the page's title as a person reads it: the stop by its name, no code
        return self.d["title"] or gate_name(self.gate, self.lang)

    # ---- the shape of the JSON: normalize every field, or raise TypeError / ValueError (exit 2) ----------
    def normalize(self):
        if self._normal:   # body() and render() both ask; once is enough
            return
        self._normal = True
        d = self.d
        jg = scalar(d.get("gate"), "gate").strip()
        if jg and jg != self.gate:
            self.warn(f'"gate": {jg!r} in the JSON, but the file name says {self.gate!r}; the file name wins')
        for k in ("title", "summary", "not_reviewed", "animatic"):
            d[k] = scalar(d.get(k), k).strip()
        if not d["summary"]:
            self.err("`summary` is missing: one line saying what this page asks and how long it takes")
        elif over_budget(d["summary"], "summary"):
            n, lim = over_budget(d["summary"], "summary")
            self.warn(f"`summary` is {n:g} long, over its budget of {lim} (a CJK character counts 1, other text ½): it is the first thing "
                      "read, so say only what this page asks and how long it takes; the rest belongs in the decisions, folds and appendix "
                      "(playbook/01-pipeline.md, 审阅页)")
        for k in ("decided", "delegated"):
            d[k] = [scalar(v, f"{k}[{i}]") for i, v in enumerate(as_list(d.get(k), k))]
        if d.get("decisions") is None:
            self.err("`decisions` is missing: use [] when there is nothing to decide")
        decs = [dict(as_dict(x, f"decisions[{i}]")) for i, x in enumerate(as_list(d.get("decisions"), "decisions"))]
        d["decisions"] = decs
        if len(decs) > MAX_DECISIONS:
            self.warn(f"{len(decs)} decisions on one page: the default is at most {MAX_DECISIONS} (upstream first, the rest "
                      "on the next page); keep them together only if the human asked to see more at once")
        ids, long_q = [], []
        for i, dec in enumerate(decs, 1):
            opts = []
            for j, o in enumerate(as_list(dec.get("options"), f"decisions[{i - 1}].options"), 1):
                o = dict(o) if isinstance(o, dict) else {"id": scalar(o, f"decisions[{i - 1}].options[{j - 1}]")}
                for k in ("id", "label", "pro", "con", "frame", "cover"):   # frame: the card's picture (a concept card's frame); cover: its cover layout
                    o[k] = scalar(o.get(k), f"decisions[{i - 1}].options[{j - 1}].{k}").strip()
                o["titles"] = [t for t in (scalar(x, f"decisions[{i - 1}].options[{j - 1}].titles[{n}]").strip()   # a card's draft titles (playbook/10 §1)
                                           for n, x in enumerate(as_list(o.get("titles"), f"decisions[{i - 1}].options[{j - 1}].titles"))) if t]
                if not o["id"]:
                    self.err(f"decision {i}: option {j} has no `id`")
                opts.append(o)
            dec["options"] = opts
            for k in ("id", "question", "recommend", "why", "cost", "reply"):
                dec[k] = scalar(dec.get(k), f"decisions[{i - 1}].{k}").strip()
            cols = as_list(dec.get("columns"), f"decisions[{i - 1}].columns")   # the pro and con columns' titles
            if cols and len(cols) != 2:
                self.warn(f"decision {i} ({dec['id'] or '?'}): `columns` takes two titles, the pro column's and the con column's; "
                          f"it has {len(cols)}" + (", the first two are used" if len(cols) > 2 else ", the other column keeps its default"))
            dec["columns"] = [scalar(c, f"decisions[{i - 1}].columns[{k}]").strip() for k, c in enumerate(cols[:2])]
            if not dec["question"]:
                self.err(f"decision {i}: no `question`")
            elif over_budget(dec["question"], "question"):
                long_q.append(str(i))
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
        if long_q:
            self.warn(f"the question of decision {', '.join(long_q)} is longer than one line ({BUDGET['question'][0]} CJK characters, "
                      f"{BUDGET['question'][1]} letters): ask it in this film's words, put the reasons in `why`")
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
            t0, t1 = seconds(x.get("t"), f"least_sure[{i}].t"), seconds(x.get("t1"), f"least_sure[{i}].t1")   # optional: where in the film
            least.append({"id": scalar(x.get("id"), f"least_sure[{i}].id").strip(),
                          "note": scalar(x.get("note"), f"least_sure[{i}].note").strip(), "t": t0, "t1": t1 if t1 and t0 is not None and t1 > t0 else None})
        d["least_sure"] = least
        listen = []   # the review desk's "please listen to these" (tools/desk/README.md): [{t, note}]; a malformed one is left out
        for i, x in enumerate(d.get("listen") if isinstance(d.get("listen"), list) else []):
            try:
                t = seconds(x.get("t"), f"listen[{i}].t") if isinstance(x, dict) else None
            except (TypeError, ValueError):
                t = None
            if t is None or t < 0:
                self.warn(f"listen[{i}]: needs t (seconds) and note; left out")
                continue
            listen.append({"t": t, "note": scalar(x.get("note"), f"listen[{i}].note").strip()})
        d["listen"] = listen
        d["film"] = d.get("film") if isinstance(d.get("film"), str) else ""
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
                if self.shot_ids and it["id"] not in self.shot_ids and not time_of(it["id"]):
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
        """The href of a project file (the static page: relative from out/review/, so it opens from disk; the console:
        its /f/ address), or an http(s) URL escaped. Any other scheme (javascript:, data:, file: …) is refused: returns
        None and records an error."""
        p = txt(p).strip()
        if re.match(r"(?i)https?://", p):
            return html.escape(p, quote=True)
        if re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", p) and not re.match(r"[A-Za-z]:[\\/]", p):
            if p not in self.bad_paths:
                self.bad_paths.add(p)
                self.err(f"{what}: {p!r} is neither a project path nor an http(s) URL; refused")
            return None
        f = Path(p) if os.path.isabs(p) else self.project / p
        if not os.path.exists(f):   # said once as an error; no link to it (a page asks for nothing that is not there)
            if p not in self.bad_paths:
                self.bad_paths.add(p)
                self.err(f"{what}: {p} does not exist")
            return None
        if self.link:
            return html.escape(self.link(os.path.relpath(f, self.project).replace(os.sep, "/")), quote=True)
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
                       lambda m: f'<a href="#shot-{m.group(1)}" data-shot-link="{m.group(1)}">{shot_label(m.group(1))}</a>' if m.group(1) in self.shot_ids else shot_label(m.group(1)), e)
            out.append(e.replace("\n", "<br>"))
        return "".join(out)

    @staticmethod
    def kind(path):
        p = txt(path).strip()
        base = re.split(r"[?#]", p)[0] if re.match(r"(?i)https?://", p) else p   # a local "a#1.png" keeps its name
        ext = os.path.splitext(base)[1].lower()
        return ("image" if ext in IMG else "video" if ext in VID else "audio" if ext in AUD else "file"), base

    def alt(self, caption, base):
        return html.escape(re.sub(r"[`*]", "", txt(caption)) or os.path.basename(base))

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

    def all_shots(self):
        return [sh for s in self.d["segments"] for sh in s["shots"]]

    def project_extra(self):
        """The outline and shot table the review desk reads from the project (tools/desk/reader.py), for a ruler when the
        page itself has no segments; {} when they cannot be read. Read once."""
        if self._extra is None:
            self._extra = {}
            try:
                sys.path.insert(0, str(ROOT / "tools" / "desk"))
                import reader
                r = reader.read_project(self.project)
                self._extra = {"outline": r.get("outline") or [], "shots": (r.get("shots") or {}).get("items") or []}
            except Exception:   # the ruler is a help, never a reason for the page to fail
                pass
        return self._extra

    # ---- what goes on the ruler ------------------------------------------------------------------------------
    def marks(self):
        """The places to look at or listen to, with their times when known: [{kind, t, t1, id, note, target}].
        A least-sure item's time: its own t, a time in its id ("12.4 s", "0–5 s"), or its shot's start."""
        starts = {sh["id"]: (sh["t0"], sh["t1"]) for sh in self.all_shots()}
        out = []
        for i, it in enumerate(self.d["least_sure"]):
            t = it.get("t")
            t1 = it.get("t1")
            if t is None:
                tt = time_of(it["id"])
                if tt:
                    t, t1 = tt
                elif it["id"] in starts:
                    t, t1 = starts[it["id"]]
            out.append({"kind": "least", "t": t, "t1": t1, "id": it["id"], "note": it["note"], "target": f"least:{it['id'] or i}"})
        for i, it in enumerate(self.d["listen"]):
            out.append({"kind": "listen", "t": it["t"], "t1": None, "id": "", "note": it["note"], "target": f"atime:{it['t']:g}" if it["t"] is not None else f"least:listen{i}"})
        return out

    def ruler_parts(self):
        """(segments [(t0, t1, title)], shots [(t0, id, label, frame href)]) for the ruler: the page's own segments and
        shots, else the project's outline and shot table (no shots.json: the outline's parts; no outline either: only the
        seconds and the marks)."""
        segs = [(s["t0"], s["t1"], s["title"]) for s in self.d["segments"] if s["t0"] is not None and s["t1"] is not None]
        shots = []
        for sh in self.all_shots():
            if sh["t0"] is not None:
                fr = self.url(sh["frame"], f"shot {sh['id']} frame") if sh["frame"] else None
                shots.append((sh["t0"], sh["id"], sh["see"], fr))
        if not segs and not shots:
            x = self.project_extra()
            segs = [(o["t0"], o["t1"], o.get("title") or "") for o in x.get("outline", []) if o.get("t0") is not None and o.get("t1") is not None]
            for sh in x.get("shots", []):
                if sh.get("start") is not None:
                    fr = sh.get("frame") or ""
                    href = None
                    if fr and not re.match(r"(?i)https?://", fr) and (self.project / fr).is_file():
                        href = self.url(fr, f"shot {sh.get('id')} frame")
                    shots.append((float(sh["start"]), txt(sh.get("id")), txt(sh.get("label")), href))
        return segs, shots

    # ---- components: one markup for the static page and the console -----------------------------------------
    def player(self, a, film=True):
        """A video on its mat, a bar under it and the ruler as its progress bar. Without JavaScript the browser's own
        controls stay (ui.js takes them away when it takes over)."""
        t = self.t
        u = self.url(a["path"], "film" if film else "video")
        if u is None:
            return ""
        poster = self.url(a["poster"], "poster") if a.get("poster") else None
        if not poster:
            first = next((sh["frame"] for sh in self.all_shots() if sh["frame"]), "")
            poster = self.url(first, "poster") if first else None
        frag = "" if poster else "#t=0.001"   # Safari paints nothing before play under preload="metadata" without it
        segs, shots = self.ruler_parts()
        marks = [m for m in self.marks() if m["t"] is not None]
        ends = [x[1] for x in segs] + [x[0] for x in shots] + [m["t1"] or m["t"] for m in marks]
        dur = max(ends) if ends else 0
        parts = ['<span class="r-base"></span><span class="r-done"></span>']
        for t0, t1, title in segs:
            parts.append(f'<span class="r-seg" data-t="{t0:g}" data-t1="{t1:g}" title="{esc(title)}">{esc(title)}</span>')
        for t0, sid, label, fr in shots:
            parts.append(f'<span class="r-shot" data-t="{t0:g}" data-id="{esc(sid)}" data-label="{esc(label)}"'
                         + (f' data-frame="{fr}"' if fr else "") + "></span>")
        for m in marks:
            kind = "listen" if m["kind"] == "listen" else "least"
            parts.append(f'<button type="button" tabindex="-1" class="r-mark {kind}" data-t="{m["t"]:g}" data-target="{esc(m["target"])}" '
                         f'title="{esc(clock(m["t"]))} {esc(m["id"])} {esc(re.sub(r"[`*]", "", m["note"]))}" aria-label="{esc(clock(m["t"]))}"></button>')
        parts.append('<span class="r-head"></span><span class="r-tip" aria-hidden="true"></span>')
        span = ""
        if a.get("t1") is not None:
            span = f' data-t0="{(a.get("t0") or 0):g}" data-t1="{a["t1"]:g}"'
        elif a.get("t0") is not None:
            span = f' data-t0="{a["t0"]:g}"'
        cap = f'<p class="cap">{self.text(a["caption"])}</p>' if a.get("caption") else ""
        return (f'<div class="player"{span} data-dur="{dur:g}"><div class="well">'
                f'<video src="{u}{frag}" controls preload="metadata" playsinline'
                + (f' poster="{poster}"' if poster else "") + f'></video><span class="big">{ICON["big"]}</span></div>'
                f'<div class="p-bar"><button type="button" class="p-btn p-play" title="{esc(t["play"])}" aria-label="{esc(t["play"])}">{ICON["play"]}</button>'
                f'<span class="p-time">0:00.0</span><div class="ruler" role="slider" tabindex="0" aria-label="{esc(t["keys"])}" aria-valuemin="0" aria-valuemax="{dur:g}" aria-valuenow="0">{"".join(parts)}</div>'
                f'<button type="button" class="p-btn p-mute" title="{esc(t["mute"])}" aria-label="{esc(t["mute"])}">{ICON["mute"]}</button>'
                f'<button type="button" class="p-btn p-full" title="{esc(t["full"])}" aria-label="{esc(t["full"])}">{ICON["full"]}</button></div>{cap}</div>')

    def gone(self, path):
        """A local file the page names that is not there (any more): True. An http(s) URL or a refused scheme: False."""
        p = txt(path).strip()
        if not p or re.match(r"(?i)https?://", p) or (re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", p) and not re.match(r"[A-Za-z]:[\\/]", p)):
            return False
        return not os.path.exists(Path(p) if os.path.isabs(p) else self.project / p)

    def figure(self, a, what="asset", thumb=False):
        """One asset: a picture on its mat, a sound to play, or a link; a file that is not there says so in its place."""
        kind, base = self.kind(a["path"])
        if self.gone(a["path"]):
            self.url(a["path"], what)   # said as an error
            cap = f'<figcaption class="cap">{self.text(a["caption"])}</figcaption>' if a.get("caption") else ""
            return f'<figure><div class="well blank" title="{esc(a["path"])}"><span>{esc(self.t["gone"])}</span></div>{cap}</figure>'
        if kind == "video":
            return self.player(a, film=False)
        u = self.url(a["path"], what)
        if u is None:
            return ""
        cap = f'<figcaption class="cap">{self.text(a["caption"])}</figcaption>' if a.get("caption") else ""
        if kind == "image":
            return (f'<figure><a class="well" href="{u}" target="_blank" rel="noopener">'
                    f'<img src="{u}" alt="{self.alt(a.get("caption"), base)}" loading="lazy"></a>{cap}</figure>')
        if kind == "audio":
            return f'<figure class="audio-row">{cap}<audio controls preload="metadata" src="{u}"></audio></figure>'
        name = html.escape(os.path.basename(base))
        return f'<p class="cap"><a href="{u}" target="_blank" rel="noopener">{name}</a>{" · " + self.text(a["caption"]) if a.get("caption") else ""}</p>'

    def gallery(self, imgs):
        """Pictures as a light table: the first one large, the others in a strip that swaps it."""
        if not imgs:
            return ""
        dec_n = {x["id"]: i for i, x in enumerate(self.d["decisions"], 1)}
        items = []
        for a in imgs:
            u = self.url(a["path"], f"decision {a['for']}" if a["for"] else "asset")
            if u:
                items.append((a, u))
        if not items:
            return ""
        items.sort(key=lambda x: "sheet" in Path(x[0]["path"]).name.lower())   # the film's own picture first, a contact sheet after it
        a0, u0 = items[0]
        if len({a["for"] for a, _ in items if a["for"]}) < 2:   # all about one decision (or none): saying so on each says nothing
            dec_n = {}

        def tag(a):
            return f'<span class="for">{self.t["for_dec"].format(n=dec_n[a["for"]])}</span>' if a["for"] in dec_n else ""   # which decision the picture is for, in words
        main = (f'<a class="well gal-main" href="{u0}" target="_blank" rel="noopener"><img src="{u0}" alt="{self.alt(a0["caption"], a0["path"])}"></a>'
                f'<p class="cap gal-cap">{self.text(a0["caption"])}{tag(a0)}</p>')
        if len(items) == 1:
            return f'<div class="gallery">{main}</div>'
        strip = "".join(f'<button type="button" data-src="{u}" aria-current="{"true" if i == 0 else "false"}" '
                        f'title="{self.alt(a["caption"], a["path"])}"><img src="{u}" alt="" loading="lazy">'
                        + (f'<span class="tag">{self.t["for_dec_s"].format(n=dec_n[a["for"]])}</span>' if a["for"] in dec_n else "")
                        + f'<span class="gal-cap-src" hidden>{self.text(a["caption"])}{tag(a)}</span></button>'   # the caption it swaps in, as markup
                        for i, (a, u) in enumerate(items))
        return f'<div class="gallery">{main}<div class="gal-strip">{strip}</div></div>'

    def thumbs(self, imgs):
        return f'<div class="thumbs">{"".join(self.figure(a) for a in imgs)}</div>' if imgs else ""

    def decision(self, i, dec, wide=False):
        t = self.t
        cols = dec["columns"] + ["", ""]
        pro_k, con_k = esc(cols[0]) or t["pro"], esc(cols[1]) or t["con"]
        opts = []
        for o in dec["options"]:
            pick = o["id"] == dec["recommend"]
            pic = ""
            if o["frame"]:
                u = self.url(o["frame"], f"option {o['id']} frame")
                if u:
                    pic = f'<span class="pic"><img src="{u}" alt="{esc(o["id"])} {self.alt(o["label"], o["frame"])}" loading="lazy"></span>'
            pc = ""
            oid = re.sub(r"[^A-Za-z0-9_-]", "_", f'o-{dec["id"]}-{o["id"]}')   # an id that aria-describedby can name
            titles = " / ".join(o.get("titles") or [])
            if o["pro"] or o["con"] or titles or o.get("cover"):
                pc = (f'<span class="pc" id="{oid}">' + (f'<span><span class="k">{pro_k}</span>{self.text(o["pro"])}</span>' if o["pro"] else "")
                      + (f'<span><span class="k">{con_k}</span>{self.text(o["con"])}</span>' if o["con"] else "")
                      + (f'<span><span class="k">{t["titles"]}</span>{self.text(titles)}</span>' if titles else "")
                      + (f'<span><span class="k">{t["cover"]}</span>{self.text(o["cover"])}</span>' if o.get("cover") else "") + "</span>")
            full = re.sub(r"[`*]", "", " · ".join(x for x in (o["label"], o["pro"], o["con"], titles, o.get("cover", "")) if x))
            name = re.sub(r"[`*]", "", f'{o["id"]} {o["label"]}'.strip()) + (f' · {t["rec"]}' if pick else "")
            opts.append(f'<label class="g-opt" title="{esc(full)}"><input type="radio" name="dec-{esc(dec["id"])}" value="{esc(o["id"])}"'
                        f'{" checked" if pick and not self.settled else ""}{" disabled" if self.settled else ""} data-rec="{"1" if pick else ""}" aria-label="{esc(name)}"'
                        + (f' aria-describedby="{oid}"' if pc else "") + f'>{pic}'
                        f'<span class="row"><span class="dot" aria-hidden="true"></span><span class="id">{esc(o["id"])}</span><span class="lab">{self.text(o["label"]) or esc(o["id"])}</span>'
                        + (f'<span class="rec">{t["rec"]}</span>' if pick else "") + f"</span>{pc}</label>")
        why = ""
        if dec["why"]:
            why = f'<p class="g-why">{t["why_rec"].format(w=self.text(dec["why"]))}</p>'
        elif not dec["options"]:
            why = f'<p class="g-why">{t["reply"]} <code>{esc(dec["reply"])}</code></p>'
        cost = f'<span class="g-cost">{self.text(cost_words(dec["cost"], self.lang))}</span>' if dec["cost"] else ""
        body = f'<div class="g-opts{" wide" if wide else ""}" role="radiogroup" aria-label="{esc(re.sub(r"[`*]", "", dec["question"]))}">{"".join(opts)}</div>' if opts else ""
        return (f'<div class="g-dec{" wide" if wide else ""}{"" if opts else " free"}" id="d-{esc(dec["id"])}" data-dec="{esc(dec["id"])}" '
                f'data-n="{i}" data-rec="{esc(dec["recommend"])}" tabindex="-1">'
                f'<p class="g-q"><span class="g-n">{i}</span><span>{self.text(dec["question"])}</span></p>{cost}{body}{why}</div>')

    def act(self):
        t, decs = self.t, self.d["decisions"]
        if self.live:
            return (f'<div class="g-act" data-live><button type="button" class="btn btn-primary g-submit">{t["submit"]}</button>'
                    f'<p class="note">{t["live_note"]}</p></div>')
        shot = self.example_shot()
        rest = t["rest"].format(shot=esc(shot)) if shot else t["rest_plain"]
        if self.settled:
            return f'<div class="g-act"><p class="note">{t["settled_note"]}</p></div>'
        if not decs:
            return f'<div class="g-act"><p class="note">{t["nothing"]}</p></div>'
        allr = esc(self.take_all())
        return (f'<div class="g-act"><div class="g-reply"><span class="g-reply-k" data-yours="{esc(t["yours"])}">{t["take_all"]}</span>'
                f'<code class="g-reply-v">{allr}</code><button type="button" class="btn g-copy" data-done="{t["copied"]}">{t["copy"]}</button></div>'
                f'<p class="note">{t["unanswered"]}{rest}</p></div>')

    def marks_list(self, items, has_player):
        out = []
        for m in items:
            when = clock(m["t"]) + (f'–{clock(m["t1"])}' if m["t1"] else "") if m["t"] is not None else ""
            if when and has_player:
                at = f'<button type="button" class="at" data-seek="{m["t"]:g}">{when}</button>'
            else:
                at = f'<span class="at static">{when}</span>'
            sid = m["id"]
            shown_id = "" if (sid and time_of(sid)) else (f'<a class="id" href="#shot-{esc(sid)}">{esc(shot_label(sid))}</a>' if sid in self.shot_ids else (f'<span class="id">{esc(shot_label(sid))}</span>' if sid else ""))
            out.append(f'<li class="{m["kind"]}" data-target="{esc(m["target"])}"' + (f' data-t="{m["t"]:g}"' if m["t"] is not None else "")
                       + f'>{at}<span>{shown_id}{self.text(m["note"])}</span></li>')
        untimed = "" if any(m["t"] is not None for m in items) else " untimed"   # no times at all: no empty time column
        return f'<ul class="g-marks{untimed}">{"".join(out)}</ul>' if out else ""

    def board(self):
        t, segs = self.t, self.d["segments"]
        if not segs:
            return ""
        colon = t["colon"]
        out = []
        for i, s in enumerate(segs, 1):
            shots = s["shots"]
            durs = [sh["t1"] - sh["t0"] for sh in shots if sh["t0"] is not None and sh["t1"] is not None]
            meta = [f'{clock(s["t0"])}–{clock(s["t1"])}' if s["t0"] is not None and s["t1"] is not None else "",
                    t["shots"].format(n=len(shots)) if shots else "",
                    t["avg"].format(s=f"{sum(durs) / len(durs):.1f}") if durs else ""]
            first = next((sh["frame"] for sh in shots if sh["frame"]), "")
            ratio = (image_ratio(self.project / first) if first and not re.match(r"(?i)https?://", first) else None) or 16 / 9
            width = 220 if ratio >= 1.2 else (160 if ratio >= 0.8 else 130)
            cards = []
            for sh in shots:
                sid, flag = sh["id"], sh["id"] in self.flagged
                dur = f'{sh["t1"] - sh["t0"]:.1f} s' if sh["t0"] is not None and sh["t1"] is not None else ""
                img = f'<span class="empty">{t["no_frame"]}</span>'
                if sh["frame"]:
                    u = self.url(sh["frame"], f"shot {sid} frame")
                    if u:
                        img = f'<img src="{u}" alt="{esc(sid)}" loading="lazy">'
                why = f'{colon}{self.text(self.flagged[sid])}' if flag and self.flagged[sid] else ""
                lines = (f'<span class="see">{self.text(sh["see"])}</span>' if sh["see"] else "") \
                    + (f'<span class="vo">{self.text(sh["vo"])}</span>' if sh["vo"] else "") \
                    + (f'<span class="u">? {t["unsure"]}{why}</span>' if flag else "") \
                    + (f'<span class="p">→ {t["plan"]}{colon}{self.text(sh["note"])}</span>' if sh["note"] else "")
                seek = f' data-t="{sh["t0"]:g}"' + (f' data-t1="{sh["t1"]:g}"' if sh["t1"] is not None else "") if sh["t0"] is not None else ""
                cards.append(f'<figure class="g-shot{" flag" if flag else ""}" id="shot-{esc(sid)}" data-target="shot:{esc(sid)}" data-shot="{esc(sid)}"{seek}>'
                             f'<div class="well">{img}<span class="sid">{esc(shot_label(sid))}</span>' + (f'<span class="dur">{dur}</span>' if dur else "")
                             + f'</div><figcaption>{lines}</figcaption></figure>')
            extra = "".join(self.figure(a, f"segment {s['id']}") for a in self.assets_for(s["id"]))
            note = f'<p class="g-seg-note">{self.text(s["note"])}</p>' if s["note"] else ""
            nflag = sum(1 for sh in shots if sh["id"] in self.flagged)
            badge = f'<span class="flag">{t["n_unsure"].format(n=nflag)}</span>' if nflag else ""
            out.append(f'<section class="g-seg" id="seg-{esc(s["id"])}"><div class="g-seg-h"><span class="meta">{t["seg"].format(i=i, n=len(segs))}</span>'
                       f'<h3>{self.text(s["title"])}</h3><span class="meta">{" · ".join(m for m in meta if m)}</span>{badge}</div>{note}'
                       f'<div class="g-shots" style="--ar:{ratio:.4f};--shot-w:{width}px">{"".join(cards)}</div>{extra}</section>')
        hint = self.example_shot()
        return (f'<section class="g-board"><h2 class="g-h">{t["board"]}<span class="n">{len(self.all_shots())}</span></h2>'
                f'<p class="cap">{t["pass_all"].format(shot=esc(hint)) if hint else t["rest_plain"]}</p>{"".join(out)}</section>')

    def blocks(self, s):
        """Text with simple pipe tables: a run of lines starting with | whose second line is |---| becomes a table."""
        out, para, lines, i = [], [], txt(s).split("\n"), 0
        cells = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]   # noqa: E731
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

    def fold(self, key, title, n, body):
        return f'<details class="fold" data-fold="{key}"><summary>{title}<span class="n">{n}</span></summary><div class="body">{body}</div></details>'

    def more(self, files):
        t, d, out = self.t, self.d, []
        for key in ("decided", "delegated"):
            if d[key]:
                items = "".join(f'<li data-target="{"deleg:" + str(i) if key == "delegated" else ""}">{self.text(v)}</li>' for i, v in enumerate(d[key]))
                out.append(self.fold(key, t[key], len(d[key]), f'<ul class="items">{items}</ul>'))
        if files:
            out.append(self.fold("material", t["material"], len(files), "".join(self.figure(a) for a in files)))
        for a in d["appendix"]:
            body = self.blocks(a["text"]) if a["text"] else ""
            if a["path"]:
                body += self.figure({"path": a["path"], "caption": ""}, "appendix")
            out.append(self.fold("appendix", f'{t["appendix"]} · {self.text(a["title"])}', "", body))
        return f'<section class="g-more">{"".join(out)}</section>' if out else ""

    def others(self):
        if self.live:
            return ""
        pages = sorted(p for p in self.out.glob("gate-*.html") if p.name != f"gate-{self.gate}.html")
        if not pages:
            return ""
        links = " · ".join(f'<a href="{quote(p.name)}">{esc(gate_name(p.stem[5:], self.lang))}</a>' for p in pages)
        return f'<span>{self.t["others"]}{self.t["colon"]}{links}</span>'

    def spend(self):
        """Spent against the budget (tools/assets/budget.py), when there is a budget or a spend; never fails the page."""
        try:
            sys.path.insert(0, str(ROOT / "tools" / "assets"))
            import budget
            b = budget.summary(self.project)
        except Exception:
            return ""
        if not b["limit"] and not b["spent"] and not b["held"] and not b["unlimited"]:
            return ""
        t, sep = self.t, "，" if self.lang == "zh" else ", "
        curs = list(dict.fromkeys(list(b["limit"]) + list(b["spent"]) + list(b["held"])))
        spent = sep.join(budget.money(b["spent"].get(c, 0.0) + b["held"].get(c, 0.0), c) for c in curs) or budget.money(0, "USD")
        have = t["unlimited"] if b["unlimited"] else sep.join(budget.money(v, c) for c, v in b["limit"].items()) or t["no_budget"]
        over = f' · {t["over"].format(cur=", ".join(b["over"]))}' if b["over"] else ""
        return f'<span class="spend{" over" if b["over"] else ""}">{esc(t["spend"].format(spent=spent, budget=have))}{esc(over)}</span>'

    def head(self):
        t, d = self.t, self.d
        n = len(d["decisions"])
        s = d["summary"]
        first, rest = s, ""
        if over_budget(s, "summary"):   # a long first line: its first sentence stands as the heading, the rest under it
            m = re.match(r"(.+?[。！？!?]|.+?[.;；:：](?=\s|$)|.+?：)(\s*\S.*)$", s, re.S)
            if m and len(m.group(1)) < len(s):
                first, rest = m.group(1).strip(), m.group(2).strip()
        now = (f'<span>{t["settled_" + self.settled]}</span>' if self.settled
               else f'<span class="g-wait">{t["n_decide"].format(n=n)}</span>' if n else f'<span>{t["look"]}</span>')
        eyebrow = f'<span class="g-gate">{esc(self.name())}</span>' + now + self.spend()
        lead = f'<p class="g-lead" data-long>{self.text(rest)}</p>' if rest else ""
        long = " long" if over_budget(first, "summary") else ""   # still long: a smaller heading, so the picture stays in view
        warn = ""
        if self.errors and self.past:
            warn = (f'<details class="g-gone"><summary>{esc(t["gone_n"].format(n=len(self.errors)))}</summary>'
                    f'<ul>{"".join(f"<li>{esc(e)}</li>" for e in self.errors)}</ul></details>')
        elif self.errors:
            warn = f'<div class="g-warn">{esc(t["warn"].format(n=len(self.errors)))}<ul>{"".join(f"<li>{esc(e)}</li>" for e in self.errors)}</ul></div>'
        if self.settled:   # a record: what the page asked then, small; the stop's module says what was decided
            return f'<header class="g-head"><div class="g-eyebrow">{eyebrow}</div><p class="g-then">{t["asked_then"]}{self.text(s)}</p>{warn}</header>'
        return f'<header class="g-head"><div class="g-eyebrow">{eyebrow}</div><h1 class="g-summary{long}">{self.text(first)}</h1>{lead}{warn}</header>'

    # ---- the gate view ----------------------------------------------------------------------------------------
    def body(self):
        """The gate view: the picture first (the film with its ruler, the concept cards, the storyboard), the decisions beside it
        as cards to pick, the marks to click, and the rest folded away. The same markup for the static page and the console."""
        self.normalize()
        t, d = self.t, self.d
        assets = d["assets"]
        film = None
        want = txt(d.get("film")).strip()
        if want:
            film = next((a for a in assets if a["path"] == want), None) or {"path": want, "caption": "", "for": "", "poster": "", "t0": None, "t1": None}
        if not film:
            film = next((a for a in assets if self.kind(a["path"])[0] == "video"), None)
        if not film and d["animatic"]:
            film = {"path": d["animatic"], "caption": "", "for": "", "poster": "", "t0": None, "t1": None}
        seg_ids = {s["id"] for s in d["segments"]}
        rest = [a for a in assets if a is not film and a["for"] not in seg_ids]
        imgs = [a for a in rest if self.kind(a["path"])[0] == "image"]
        imgs.sort(key=lambda a: 0 if a["for"] else 1)   # the pictures a decision points at first
        sounds = [a for a in rest if self.kind(a["path"])[0] == "audio"]
        videos = [a for a in rest if self.kind(a["path"])[0] == "video"]
        files = [a for a in rest if self.kind(a["path"])[0] == "file"]
        wide = [i for i, x in enumerate(d["decisions"]) if any(o["frame"] for o in x["options"])]
        main = []
        if film and not re.match(r"(?i)https?://", film["path"]) and not (self.project / film["path"]).is_file():
            self.url(film["path"], "film")   # said as an error; the picture says the file is gone
            main.append(f'<section class="g-stage"><div class="well blank" title="{esc(film["path"])}"><span>{esc(t["gone"])}</span></div></section>')
            film = None
        elif film:
            main.append(f'<section class="g-stage">{self.player(film)}</section>')
        elif imgs and not wide:
            main.append(f'<section class="g-stage">{self.gallery(imgs)}</section>')
            imgs = []
        for i in wide:
            main.append(self.decision(i + 1, d["decisions"][i], wide=True))
        if sounds:
            main.append(f'<section>{"".join(self.figure(a) for a in sounds)}</section>')
        marks = self.marks()
        least = [m for m in marks if m["kind"] == "least"]
        listen = [m for m in marks if m["kind"] == "listen"]
        if least:
            main.append(f'<section><h2 class="g-h">{t["least"]}<span class="n">{len(least)}</span></h2>{self.marks_list(least, bool(film))}</section>')
        if listen:
            main.append(f'<section><h2 class="g-h">{t["listen"]}<span class="n">{len(listen)}</span></h2>{self.marks_list(listen, bool(film))}</section>')
        for a in videos:
            main.append(f'<section>{self.player(a, film=False)}</section>')
        if imgs:
            main.append(f'<section><h2 class="g-h">{t["pictures"]}<span class="n">{len(imgs)}</span></h2>{self.thumbs(imgs)}</section>')
        board = self.board()   # the storyboard is the picture when there is no film to play: first, beside the decisions
        if board:
            main = main + [board] if film else [board] + main
        side_decs = "".join(self.decision(i + 1, x) for i, x in enumerate(d["decisions"]) if i not in wide)
        side = f'<div class="g-decs">{side_decs}</div>{self.act()}' if side_decs else self.act()
        if main:
            grid = f'<div class="g-body has-side"><div class="g-main">{"".join(main)}</div><aside class="g-side">{side}</aside></div>'
        else:
            grid = f'<div class="g-body"><div class="g-main">{side}</div></div>'
        foot = []
        if d["not_reviewed"]:
            foot.append(f'<span class="notseen">{t["not_reviewed"].format(x=self.text(d["not_reviewed"]))}</span>')
        foot.append(self.others())
        src = os.path.relpath(self.src, self.project).replace(os.sep, "/")
        foot.append(f'<span title="{esc(src)}">{t["src"]}</span>')   # where it was made: for whoever keeps the files, not in the text
        attrs = (f'data-gate="{esc(self.gate)}" data-lang="{self.lang}" data-takeall="{esc(self.take_all())}"'
                 + (" data-live" if self.live else " data-static") + (f' data-settled="{self.settled}"' if self.settled else ""))
        more = self.more(files)   # before the head: every missing file is in its warning
        return (f'<article class="gate" {attrs}>{self.head()}{grid}{more}'
                f'<footer class="g-foot">{"".join(x for x in foot if x)}</footer></article>')

    def render(self):
        """The static page: the gate view with ui.css and ui.js inlined, so it opens from disk with no server; with its stop's
        module above it (module_payload) when the stop has one and the project reads."""
        self.settled = stop_settled(self.project, self.gate)   # a page of a stop settled since: a record
        body = self.body()   # normalizes first: the title may come from the gate's name
        t, title, film = self.t, self.name(), brief_title(self.project) or self.project.name
        try:
            data = module_payload(self.project, self.gate, self.out, self.marks(), self.lang)
        except Exception as e:   # an old project, a file that does not read: the page is the gate view alone
            data = None
            self.warn(f"the stop's module above the page left out ({type(e).__name__}: {e})")
        mod_css = f'<style>{static_file("modules.css")}</style>' if data else ""
        mod_js = (f'<script type="application/json" id="ovh-data">{data}</script>'
                  + "".join(f"<script>{static_file(n)}</script>" for n in ("core.js", "modules.js", "static.js"))) if data else ""
        return (f'<!doctype html><html lang="{t["html_lang"]}"><head><meta charset="utf-8">'
                f'<meta name="viewport" content="width=device-width, initial-scale=1">'
                f'<title>{esc(title)} · {esc(film)}</title>'
                f'<style>{static_file("ui.css")}</style>{mod_css}<script>{HEAD_JS}</script></head><body>'
                f'<header class="top"><div class="wrap"><span class="mark">OVH</span><nav class="crumbs">'
                f'<span class="cr"><b>{esc(film)}</b></span><span class="cr hide-s"><span class="sep">/</span><span>{esc(title)}</span></span></nav>'
                f'<div class="top-tools"><details class="tmenu"><summary class="btn btn-quiet">{t["theme"]}</summary><div class="themes" role="group" aria-label="{t["theme"]}">'
                + "".join(f'<button type="button" data-theme-set="{k}" aria-pressed="false">{n}</button>' for k, n in zip(("darkfield", "prism", "bridge"), t["themes"]))
                + '</div></details></div></div></header>'
                f'<main class="wrap">{body}</main>'
                f'<script>{static_file("ui.js")}</script>{mod_js}</body></html>\n')

    def chat(self, page_path):
        """The whole chat message: plain text, no markup."""
        t, decs = self.t, self.d["decisions"]
        title = self.d["title"] or gate_name(self.gate, self.lang)   # the person reads it: the stop's name, no code (①, E1)
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


GATE_ID = re.compile(r"[A-Za-z0-9_-]{1,24}")   # a page name: gate-<id>.json (the review desk uses the same rule)
GATE_ORDER = {"1": 1, "E0": 2, "E1": 3, "2": 4, "E2": 5, "E3": 6, "E4": 7, "3": 8, "E5": 9}


FILL = re.compile(r"\{(?:填：|fill in:)")   # the placeholder bin/vh gate --init writes; a stylesheet cannot write either


def placeholders(x, at=""):
    """Where a gate JSON still holds bin/vh gate --init's placeholders: its paths (summary, decisions[0].question)."""
    if isinstance(x, dict):
        return [w for k, v in x.items() for w in placeholders(v, f"{at}.{k}" if at else str(k))]
    if isinstance(x, list):
        return [w for i, v in enumerate(x) for w in placeholders(v, f"{at}[{i}]")]
    return [at] if isinstance(x, str) and FILL.search(x) else []


def _unfilled(page):
    """A gate JSON that bin/vh gate --init wrote and nobody has filled in, read as JSON (json.dump writes \\uXXXX), with the files
    it includes: not a page yet. One that is not JSON goes by its text."""
    try:
        raw = page.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return False
    try:
        data = json.loads(raw)
    except ValueError:
        return bool(FILL.search(raw))
    try:
        return bool(placeholders(data) or (isinstance(data, dict) and placeholders(merge_includes(page.parents[2], data))))
    except ValueError:   # an include that cannot be read: publish says so
        return False


def _refused_file(project, gate):
    return Path(project) / "out" / "review" / f".gate-{gate}.refused.json"


def refusal(project, gate):
    """What is wrong with a page publish wrote but would not send (exit 1), until a run of it goes through: [message], else
    None. The person got nothing from that run, whatever gate-<n>.html now says."""
    try:
        j = json.loads(_refused_file(project, gate).read_text(encoding="utf-8"))
    except OSError:
        return None
    except ValueError:
        return []
    return [str(x) for x in j["errors"]] if isinstance(j, dict) and isinstance(j.get("errors"), list) else []


def _pages_on_disk(project):
    """out/review/gate-<id>.json files with a valid id whose real path stays inside the project (a symlink that
    leads out of it is skipped)."""
    rdir = Path(project) / "out" / "review"
    root = os.path.realpath(str(project))
    return [p for p in (rdir.glob("gate-*.json") if rdir.is_dir() else [])
            if GATE_ID.fullmatch(p.stem[5:]) and os.path.commonpath([os.path.realpath(str(p)), root]) == root]


def _on_disk(pages, rid):
    """The page whose id is rid, spelled as on disk: an exact match, else the one that matches ignoring case (APFS
    finds gate-1d.json for 1D, and the file's own name is what counts)."""
    exact = [p for p in pages if p.stem[5:] == rid]
    loose = [p for p in pages if p.stem[5:].lower() == rid.lower()]
    return exact[0] if exact else loose[0] if len(loose) == 1 else None


def current_page(project):
    """The id of the page bin/vh review made last (out/review/.current), as spelled on disk, if that page still
    exists; else None."""
    try:
        rid = (Path(project) / "out" / "review" / ".current").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return None
    p = _on_disk(_pages_on_disk(project), rid) if GATE_ID.fullmatch(rid) else None
    return p.stem[5:] if p else None


def gate_pages(project):
    """out/review/gate-*.json in order; the last is this round. This round is the page bin/vh review made last
    (out/review/.current), whatever its name: a concept page 1b after gate 2, a page E3b after gate 3, "final".
    Without it (or when it names a page that is gone), the review order decides: the stop (1, E0, E1, 2, E2, E3, E4,
    3, E5), then the page within it (1, 1b, 1c …, any case); other names come first, ordered by modification time.
    Copying or touching a file never changes which page is current. A skeleton not filled in yet is no page."""
    def key(p):
        m = re.fullmatch(r"(E\d|\d)([A-Za-z]*)", p.stem[5:])
        return (GATE_ORDER.get(m.group(1), 0), len(m.group(2)), m.group(2).lower(), 0, p.name) if m else (0, 0, "", p.stat().st_mtime, p.name)
    pages = sorted((p for p in _pages_on_disk(project) if not _unfilled(p)), key=key)
    cur = current_page(project)
    return [p for p in pages if p.stem[5:] != cur] + [p for p in pages if p.stem[5:] == cur]


def review_lang(project):
    """The project's review language, from the BRIEF's Spec line "- Review language: zh | en" (bin/vh new --lang writes
    it; the agent sets it from the language of the user's first request). None when the line is missing or unclear."""
    try:
        s = (Path(project) / "BRIEF.md").read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return None
    m = re.search(r"^- Review language:[ \t]*([^\s<]+)", s, re.M)
    v = m.group(1).lower() if m else ""
    return "en" if v.startswith("en") else "zh" if v.startswith("zh") or v.startswith("中") else None


def brief_title(project):
    """The film's title from the BRIEF's first line (# BRIEF：片名), or None."""
    try:
        head = (Path(project) / "BRIEF.md").read_text(encoding="utf-8-sig", errors="replace")[:4000]
    except OSError:
        return None
    m = re.search(r"^#\s+BRIEF\s*[：:—–·|-]+\s*(.+?)\s*$", head, re.M)   # "# BRIEF：片名", or an older "# BRIEF — 片名"
    return m.group(1).strip() if m and "{" not in m.group(1) else None


def find_project(arg):
    """The same lookup as bin/vh new, storyboard and style apply: a folder, or a name under $OVH_PROJECTS or
    <harness>/projects, the date prefix optional. None (with the reason on stderr) when nothing, or more than one, matches."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from vhdraw import project_dir   # no pillow needed for this
    try:
        return project_dir(arg)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return None


def merge_includes(project, data):
    """`"include": "out/check/storyboard/review.json"` (or a list): the included JSON fills in the keys this gate JSON does
    not set; the gate JSON always wins. bin/vh storyboard writes that file with the segments, shots, least-sure shots,
    pages and animatic of gate ②."""
    inc = data.pop("include", None)
    if inc is None:
        return data
    for i, p in enumerate([inc] if isinstance(inc, str) else inc if isinstance(inc, list) else [None]):
        if not isinstance(p, str) or not p.strip():
            raise ValueError(f"include[{i}]: a path relative to the project, e.g. out/check/storyboard/review.json")
        f = Path(p) if os.path.isabs(p) else project / p
        try:
            extra = json.loads(f.read_text(encoding="utf-8-sig"))
        except OSError as e:
            raise ValueError(f"include {p}: {e.strerror or e} (bin/vh storyboard writes out/check/storyboard/review.json)")
        except ValueError as e:
            raise ValueError(f"include {p}: not valid JSON ({e})")
        if not isinstance(extra, dict):
            raise ValueError(f"include {p}: expected a JSON object")
        for k, v in extra.items():
            if k not in data and k != "include":
                data[k] = v
    return data


def page_for(project, gate, link=None, live=False, lang=None):
    """A Page for out/review/gate-<gate>.json with its includes, ready to render (body()), for a client that shows it:
    the console's gate view; lang (zh | en) sets the words around the page's own text, as the console's language switch
    does. Raises ValueError (no such page, not JSON, placeholders left, a field of the wrong shape)."""
    project = Path(project)
    src = _on_disk(_pages_on_disk(project), gate) if GATE_ID.fullmatch(gate or "") else None
    if src is None:
        raise ValueError(f"no out/review/gate-{gate}.json")
    try:
        data = json.loads(src.read_text(encoding="utf-8-sig"))
    except OSError as e:
        raise ValueError(f"can't read {src.name}: {e.strerror or e}")
    if not isinstance(data, dict):
        raise ValueError(f"{src.name}: expected a JSON object")
    data = merge_includes(project, data)
    if placeholders(data):
        raise ValueError(f"{src.name}: placeholders still to fill in")
    page = Page(project, src, data, src.stem[5:], link=link, live=live)
    if lang in T:
        page.lang, page.t = lang, T[lang]
    try:
        page.normalize()
    except (AttributeError, KeyError, TypeError) as e:
        raise ValueError(f"{src.name}: a field has the wrong shape ({type(e).__name__}: {e})")
    return page


def stage_for(project, film, link):
    """The project page's picture when no gate waits (the console): the film with the ruler of the project's outline and
    shots, in the gate view's player markup."""
    page = Page(Path(project), Path(project) / "BRIEF.md", {"summary": "·", "decisions": []}, "stage", link=link, live=True)
    page.normalize()
    return page.player({"path": film, "caption": "", "poster": "", "t0": None, "t1": None, "for": ""})


def main():
    ap = argparse.ArgumentParser(description="Build the decision-first review page from out/review/gate-<n>.json")
    ap.add_argument("project", help="project directory, or its folder name under projects/")
    ap.add_argument("gate", nargs="?", help="1 | 2 | 3 | E0–E5 | 2b … (gate-2, gate-2.json too); default: this round "
                                            "(out/review/.current, else the last page in review order)")
    a = ap.parse_args()
    project = find_project(a.project)
    if not project:   # find_project said why
        return 2
    rc, page, page_path = publish(project, a.gate, a.project)
    if rc:
        return rc
    print(page.chat(page_path))
    import activity   # tools/activity.py: this run's line in the project's log, when bin/vh ran us
    activity.note(f"{gate_title(page.gate, 'en')}: {len(page.d['decisions'])} decision(s), {len(page.d['segments'])} segment(s)", [page_path])
    return 0


def no_pack(project, where, gate, shown):
    """What to do about a stop with no gate JSON. A quick project has no gates, unless the person asked for a stop."""
    from gatecheck import effort_of   # (tools/ is on the path: this file's folder, or bin/vh gate's)
    init = f"bin/vh gate {shown or project} {gate or '<n>'} --init"
    if effort_of(project)[0] == "quick":
        return (f"no review pack at {where}. A quick project has no gates, so there is nothing to send unless the person asked for a "
                f"stop (the director mode, CLAUDE.md); for one, {init} writes a skeleton")
    return (f"no review pack at {where}: {init} writes a skeleton to fill in; "
            'the fields: bin/vh know --show "playbook/01-pipeline.md#审阅页"')


def publish(project, gate_arg=None, shown=None):
    """Build out/review/gate-<n>.html (and index.html) from gate-<n>.json and, when it breaks no rule (it can be sent),
    make it this round (.current); what is wrong goes to stderr. → (exit status as main's, the Page, the page's path);
    no Page when nothing was written. bin/vh review prints the page's chat message after it, bin/vh gate
    (tools/gate.py) does the rest of a stop."""
    rdir = project / "out" / "review"
    pages = _pages_on_disk(project)
    g = None
    if gate_arg:
        g = re.sub(r"\.json$", "", re.sub(r"^gate-", "", gate_arg.strip()))
        if not GATE_ID.fullmatch(g):
            print(f"not a gate name: {gate_arg!r} (1 to 24 letters, digits, - or _: 1, 2, 3, E0–E5, 2b …)", file=sys.stderr)
            return 2, None, None
        src = _on_disk(pages, g)   # spelled as on disk: on APFS "1D" finds gate-1d.json, and the page is 1d
        where = rdir / f"gate-{g}.json"
    else:
        ordered = gate_pages(project)
        src = ordered[-1] if ordered else next((p for p in pages if _unfilled(p)), None)   # only a skeleton: said below
        where = rdir / "gate-<n>.json"
        newer = [p for p in pages if src and p.stat().st_mtime > src.stat().st_mtime]
        if newer:
            print(f"! rendering this round, {src.stem[5:]}; {', '.join(sorted(p.name for p in newer))} is newer: to render "
                  f"a new page, name it (bin/vh review {shown or project} <n>)", file=sys.stderr)
    if src is None or not src.is_file():
        print(no_pack(project, where, g, shown), file=sys.stderr)
        return 2, None, None
    gate = src.stem[5:]
    try:
        data = json.loads(src.read_text(encoding="utf-8-sig"))   # a BOM from a Windows editor is fine
        if not isinstance(data, dict):
            raise ValueError("expected a JSON object")
        left = placeholders(data)
        if not left:
            data = merge_includes(project, data)
            left = placeholders(data)
        if left:   # before anything else: a page that is not filled in never reaches the person
            print(f"{src}: {len(left)} placeholder(s) still to fill in ({', '.join(left[:6])}{' …' if len(left) > 6 else ''}): "
                  "replace each one, or delete what this page does not need. Nothing was written, nothing goes to the person", file=sys.stderr)
            return 2, None, None
    except OSError as e:
        print(f"can't read {src}: {e.strerror or e}", file=sys.stderr)
        return 2, None, None
    except ValueError as e:
        print(f"{src}: {e}", file=sys.stderr)
        return 2, None, None
    page = Page(project, src, data, gate)
    try:
        doc = page.render()
    except (AttributeError, KeyError, TypeError, ValueError) as e:   # a field of the wrong shape, e.g. a string for a list
        print(f"{src}: a field has the wrong shape ({type(e).__name__}: {e}); compare with playbook/01-pipeline.md, 审阅页",
              file=sys.stderr)
        return 2, None, None
    page_path = rdir / f"gate-{gate}.html"
    try:
        for p in (page_path, rdir / "index.html"):
            p.write_text(doc, encoding="utf-8")
    except OSError as e:
        print(f"can't write {rdir}: {e.strerror or e}", file=sys.stderr)
        return 2, None, None
    for w in page.warnings:
        print(f"! {w}", file=sys.stderr)
    for e in page.errors:
        print(f"✗ {e}", file=sys.stderr)
    segs = data["segments"]
    what = (f"{page.title()} · {len(data['decisions'])} decision(s) · {len(segs)} segment(s) · "
            f"{sum(len(s['shots']) for s in segs)} shot(s)")
    if page.errors:   # not sent, so not this round either: the desk and its watcher stay on the page that is out
        print(f"✗ {page_path} written with {len(page.errors)} problem(s) above ({what}); fix them before sending, "
              "so no chat message this time", file=sys.stderr)
        try:   # and bin/vh status: the person got nothing from this run
            _refused_file(project, gate).write_text(json.dumps({"version": 1, "errors": page.errors}, ensure_ascii=False) + "\n", encoding="utf-8")
        except OSError as e:
            print(f"can't write {_refused_file(project, gate)}: {e.strerror or e}", file=sys.stderr)
        return 1, page, page_path
    try:   # the page just made is "this round" for the review desk and its watcher, whatever its name or the order of
        # the stops (a concept page 1b after gate 2, a voice page E3b after gate 3, a page called "final")
        (rdir / ".current").write_text(gate + "\n", encoding="utf-8")
        _refused_file(project, gate).unlink(missing_ok=True)
    except OSError as e:
        print(f"can't write {rdir / '.current'}: {e.strerror or e}", file=sys.stderr)
        return 2, None, None
    print(f"✓ {page_path}, also index.html  ({what})", file=sys.stderr)
    return 0, page, page_path


if __name__ == "__main__":
    sys.exit(main())
