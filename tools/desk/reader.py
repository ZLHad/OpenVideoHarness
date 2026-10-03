"""Review desk, core: read one project folder into the desk's data (one JSON object).

The project's markdown and JSON stay the only source of truth: this module reads them and writes nothing. What it
reads is the contract in tools/desk/README.md (BRIEF Spec / Content / Outline, SCRIPT's caption or narration table,
NOTES 素材清单, DECISIONS, REVIEW, shots.json, out/review/gate-*.json, the score's beat map, out/review/feedback/).
What it cannot parse is not lost: every project doc also comes back as safe HTML (render_md), and the desk shows that
wherever a structured view would be empty, with a warning that says what was not found.

Paths in the output are relative to the project; the desk serves them under /p/.
"""
import html, json, os, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import review as R   # noqa: E402  (tools/review.py: merge_includes, review_lang, the gate names)

DOCS = ["BRIEF.md", "STORYBOARD.md", "SCRIPT.md", "STYLE.md", "NOTES.md", "DECISIONS.md", "REVIEW.md",
        "LESSONS.md", "PACKAGING.md", "CHARACTER.md"]
MAX_DOC = 1_000_000          # bytes; a bigger doc is listed but not read
MAX_FEEDBACK = 200           # newest feedback files read
MAX_TICKS = 1500             # music hits drawn on the sound bar
STAGE_OF_GATE = {"1": 1, "E0": 2, "E1": 3, "2": 3, "E2": 4, "E3": 4, "E4": 6, "3": 8, "E5": 8}
REFERENCE_SECTIONS = re.compile(r"^(授权跳过怎么记|给人看的提示|How to record a waived gate|Notes for the reviewer)")


# ---------- markdown: comments, sections, tables, bullets ----------

def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def _fence(line, fence):
    """(fence still open, this line is inside or opens/closes a fence)"""
    s = line.strip()
    if fence:
        if s and set(s) == {fence[0]} and len(s) >= len(fence):
            return None, True
        return fence, True
    m = re.match(r"(`{3,}|~{3,})", s)
    return (m.group(1), True) if m else (None, False)


def sections(text, level=2):
    """[(title, body)] of the level-2 ('## ') sections, fences respected; text before the first one has title ''."""
    out, title, buf, fence, mark = [], "", [], None, "#" * level + " "
    for line in text.split("\n"):
        fence, inside = _fence(line, fence)
        if not inside and line.startswith(mark):
            out.append((title, "\n".join(buf)))
            title, buf = line[len(mark):].strip(), []
        else:
            buf.append(line)
    out.append((title, "\n".join(buf)))
    return out


def section(text, *patterns):
    """The body of the first '## ' section whose title matches one of the regexes (case-insensitive), else ''."""
    for title, body in sections(text)[1:]:
        if any(re.search(p, title, re.I) for p in patterns):
            return body
    return ""


SEP = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def cells(line):
    s = line.strip()
    s = s[1:] if s.startswith("|") else s
    s = s[:-1] if s.endswith("|") and not s.endswith("\\|") else s
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


class Table:
    def __init__(self, head, rows):
        self.head, self.rows = head, rows

    def col(self, *keys):
        """Index of the first header that starts with one of the keys (case-insensitive), else None."""
        for k in keys:
            for i, h in enumerate(self.head):
                if h.lower().startswith(k.lower()):
                    return i
        return None

    def has(self, *keys):
        return self.col(*keys) is not None

    def get(self, row, *keys):
        i = self.col(*keys)
        return row[i] if i is not None and i < len(row) else ""


def tables(text):
    """Every pipe table in text, fences respected."""
    lines, out, i, fence = text.split("\n"), [], 0, None
    while i < len(lines):
        fence, inside = _fence(lines[i], fence)
        if not inside and lines[i].strip().startswith("|") and i + 1 < len(lines) and SEP.match(lines[i + 1]):
            head, rows, j = cells(lines[i]), [], i + 2
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(cells(lines[j]))
                j += 1
            out.append(Table(head, rows))
            i = j
            continue
        i += 1
    return out


def first_table(text, *keys):
    """The first table with a column for one of the keys."""
    return next((t for t in tables(text) if t.has(*keys)), None)


def bullets(text):
    """Top-level '- Key: value' bullets, each with the indented '- …' bullets under it: [(key, value, [sub])]."""
    out = []
    for line in text.split("\n"):
        m = re.match(r"^- ([^:：\n]+?)[:：][ \t]*(.*)$", line)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip(), []))
            continue
        m = re.match(r"^\s{2,}[-*] (.+)$", line)
        if m and out:
            out[-1][2].append(m.group(1).strip())
    return out


def plain(s):
    """A cell or bullet as plain text: no **, no backticks, no surrounding space."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", (s or "")).replace("`", "").strip()


def struck(s):
    """(text, struck through?, the note after it): '~~a~~（关卡 ① 后作废）' → ('a', True, '（关卡 ① 后作废）')."""
    m = re.match(r"^\s*~~(.+?)~~\s*(.*)$", s or "", re.S)
    return (m.group(1).strip(), True, m.group(2).strip()) if m else ((s or "").strip(), False, "")


# ---------- times ----------

_N = r"(\d+(?::\d+(?:\.\d+)?)?(?:\.\d+)?)"


def _secs(x):
    if ":" in x:
        m, s = x.split(":", 1)
        return int(m) * 60 + float(s)
    return float(x)


def span(s):
    """'0–10 s', '1:30–1:52', '12.5 s' → (t0, t1); no time → (None, None); one time → (t, None)."""
    s = (s or "").replace("—", "–")
    m = re.search(_N + r"\s*(?:s|秒)?\s*(?:[–~～至到-]|to)\s*" + _N, s)
    if m:
        return _secs(m.group(1)), _secs(m.group(2))
    m = re.search(_N, s)
    return (_secs(m.group(1)), None) if m else (None, None)


def bar_clock(beats):
    """bar k (1-based) → its start in seconds, from a beat map's downbeats (the last bar's length carries on past
    them); a map with only a bpm counts 4/4 bars. None without a beat map."""
    db = [float(x) for x in beats.get("downbeats") or [] if isinstance(x, (int, float))]
    bpm = beats.get("bpm")
    bar_s = db[-1] - db[-2] if len(db) >= 2 else (240.0 / float(bpm) if isinstance(bpm, (int, float)) and bpm > 0 else None)
    if not bar_s:
        return None

    def start(k):
        if db and k <= len(db):
            return db[k - 1]
        return (db[-1] + (k - len(db)) * bar_s) if db else (k - 1) * bar_s
    return start


def bar_span(cell, start):
    """'4–7' (bars) → (start of bar 4, end of bar 7) with a bar clock, else (None, None)."""
    n = [int(x) for x in re.findall(r"\d+", cell or "")]
    if not n or not start:
        return None, None
    return round(start(n[0]), 3), round(start(n[-1] + 1), 3)


# ---------- safe markdown → HTML (for docs the structured views can't show) ----------

LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")


def _link(m):
    text, url = m.group(1), html.unescape(m.group(2))
    if url.startswith("#"):
        return text
    if re.match(r"^https?://", url):
        return f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener noreferrer">{text}</a>'
    if not re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I) and not url.startswith("/") and ".." not in url.split("/"):
        return f'<a href="/p/{html.escape(url, quote=True)}" target="_blank" rel="noopener">{text}</a>'
    return text


MAX_INLINE = 5000   # characters: a longer line is shown escaped, without inline markup, so no pattern can run long


def inline(s):
    """One line of markdown → HTML. Everything is escaped; code spans stay literal. The patterns stop at the next
    delimiter (no '.+?' across the line), so each runs in linear time."""
    if len(s) > MAX_INLINE:
        return html.escape(s, quote=False)
    out = []
    for i, part in enumerate(re.split(r"(`[^`]+`)", s)):
        if i % 2:
            out.append("<code>" + html.escape(part[1:-1]) + "</code>")
            continue
        p = html.escape(part, quote=False)
        p = re.sub(r"\[([^\[\]]+)\]\(([^()\s]+)\)", _link, p)
        p = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", p)
        p = re.sub(r"~~([^~]+)~~", r"<del>\1</del>", p)
        p = re.sub(r"(?<![*\w])\*([^\s*](?:[^*]*[^\s*])?)\*(?![*\w])", r"<em>\1</em>", p)
        out.append(p)
    return "".join(out)


def _list_html(items):
    out, stack = [], []
    for ind, ordered, text in items:
        tag = "ol" if ordered else "ul"
        while stack and ind < stack[-1][0]:
            out.append(f"</li></{stack.pop()[1]}>")
        if stack and ind == stack[-1][0]:
            out.append("</li>")
        else:
            out.append(f"<{tag}>")
            stack.append((ind, tag))
        m = re.match(r"^\[( |x|X)\]\s+(.*)$", text, re.S)
        body = (("☑ " if m.group(1).lower() == "x" else "☐ ") + inline(m.group(2))) if m else inline(text)
        out.append("<li>" + body.replace("\n", "<br>"))
    while stack:
        out.append(f"</li></{stack.pop()[1]}>")
    return "".join(out)


def _starts_block(lines, i):
    s = lines[i].strip()
    return (not s or s.startswith(("#", ">", "```", "~~~")) or LIST.match(lines[i]) is not None
            or (s.startswith("|") and i + 1 < len(lines) and SEP.match(lines[i + 1]) is not None))


MAX_QUOTE_DEPTH = 8


def render_md(text, depth=0):
    """Markdown → HTML for display. Everything is escaped first; only a small subset becomes markup: headings,
    paragraphs, lists (nested by indent, task boxes), pipe tables, fenced code, blockquotes, rules, **bold**, *italic*,
    `code`, ~~strike~~, and links to http(s) or to a project file (/p/…). HTML comments are dropped."""
    lines, out, i = strip_comments(text).split("\n"), [], 0
    while i < len(lines):
        line, s = lines[i], lines[i].strip()
        if not s:
            i += 1
            continue
        m = re.match(r"(`{3,}|~{3,})", s)
        if m:
            fence, buf, i = m.group(1), [], i + 1
            while i < len(lines) and not (lines[i].strip() and set(lines[i].strip()) == {fence[0]} and len(lines[i].strip()) >= len(fence)):
                buf.append(lines[i])
                i += 1
            out.append("<pre><code>" + html.escape("\n".join(buf)) + "</code></pre>")
            i += 1
            continue
        m = re.match(r"(#{1,6})\s+(.*)$", s)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2).rstrip('#').strip())}</h{n}>")
            i += 1
            continue
        if re.fullmatch(r"(-\s*){3,}|(\*\s*){3,}|(_\s*){3,}", s):
            out.append("<hr>")
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and SEP.match(lines[i + 1]):
            head, j = cells(lines[i]), i + 2
            rows = []
            while j < len(lines) and lines[j].strip().startswith("|"):
                rows.append(cells(lines[j]))
                j += 1
            th = "".join(f"<th>{inline(h)}</th>" for h in head)
            tr = "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
            out.append(f'<div class="tw"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>')
            i = j
            continue
        if s.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = render_md("\n".join(buf), depth + 1) if depth < MAX_QUOTE_DEPTH else \
                "<p>" + "<br>".join(inline(b) for b in buf) + "</p>"   # deeper quotes stay flat: no runaway recursion
            out.append("<blockquote>" + inner + "</blockquote>")
            continue
        if LIST.match(line):
            items = []
            while i < len(lines):
                m = LIST.match(lines[i])
                if m:
                    items.append((len(m.group(1).expandtabs(4)), m.group(2)[0].isdigit(), m.group(3)))
                elif lines[i].strip() and lines[i][:1] in " \t" and items:
                    items[-1] = (items[-1][0], items[-1][1], items[-1][2] + "\n" + lines[i].strip())
                elif not lines[i].strip() and i + 1 < len(lines) and (LIST.match(lines[i + 1]) or lines[i + 1][:1] in " \t" and lines[i + 1].strip()):
                    pass
                else:
                    break
                i += 1
            out.append(_list_html(items))
            continue
        buf = [s]
        i += 1
        while i < len(lines) and not _starts_block(lines, i):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + "<br>".join(inline(b) for b in buf) + "</p>")
    return "".join(out)


# ---------- the project ----------

def _read(p, warnings):
    try:
        if p.stat().st_size > MAX_DOC:
            warnings.append(f"{p.name}: larger than {MAX_DOC // 1000} kB, not read")
            return ""
        return p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _json(p, warnings):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as e:
        warnings.append(f"{p.name}: not readable JSON ({e})")
        return None


def _rel(project, p):
    return Path(os.path.relpath(p, project)).as_posix()


def _inside(project, rel):
    """project / rel when that is a file inside the project (no absolute paths, no way out), else None."""
    if not isinstance(rel, str) or not rel or os.path.isabs(rel):
        return None
    p = (project / rel).resolve()
    return p if p.is_file() and os.path.commonpath([str(p), str(project)]) == str(project) else None


def _match_segment(cell, outline, t0):
    """The outline id a caption or shot belongs to: by its segment cell (id, title, or a title inside it), else by time."""
    c = plain(cell)
    if c:
        for o in outline:
            if c in (o["id"], o["title"]):
                return o["id"]
        for o in outline:
            if o["title"] and o["title"] in c:
                return o["id"]
    if t0 is not None:
        for o in outline:
            if o["t0"] is not None and o["t1"] is not None and o["t0"] - 1e-6 <= t0 < o["t1"] - 1e-6:
                return o["id"]
    return ""


def _concept(brief):
    fields, specifics = [], []
    for k, v, sub in bullets(section(brief, r"^Content", r"^内容")):
        fields.append({"k": k, "v": plain(v)})
        if k.lower().startswith("specifics") or k.startswith("素材"):
            specifics = [plain(x) for x in sub]
    get = lambda *ks: next((f["v"] for f in fields for k in ks if f["k"].lower().startswith(k.lower())), "")   # noqa: E731
    return {"fields": fields, "specifics": specifics, "line": get("Concept", "立意"), "spine": get("Spine", "故事线"),
            "motif": get("Recurring motif", "母题"), "end": get("What the viewer", "看完")}


def _outline(brief, clock, warnings):
    body = section(brief, r"^Outline", r"^大纲")
    t = first_table(body, "段落", "segment", "段")
    if not t:
        if body.strip():
            warnings.append("BRIEF.md: the Outline section has no table with a 段落 / Segment column; shown as text")
        return []
    out = []
    for i, r in enumerate(t.rows):
        title, tag = plain(t.get(r, "段落", "segment", "段")), plain(t.get(r, "标签", "tag"))
        m = re.match(r"^\d*\s*(起|承|转|合|收)\s*[·:：]\s*(.+)$", title)   # an old 'title': "承 · 发出去"
        if m:
            tag, title = tag or m.group(1), m.group(2).strip()
        t0, t1 = span(t.get(r, "时间", "time"))
        if t0 is None:
            t0, t1 = bar_span(t.get(r, "小节", "bars"), clock)
        out.append({"id": plain(t.get(r, "#", "id")) or str(i + 1), "title": title, "tag": tag,
                    "stage": plain(t.get(r, "环节", "阶段", "stage")), "bars": plain(t.get(r, "小节", "bars")),
                    "t0": t0, "t1": t1, "know": plain(t.get(r, "观众", "viewer", "takeaway", "what the viewer")),
                    "visual": plain(t.get(r, "关键画面", "画面", "key visual", "visual"))})
    return out


def _script(script, outline, clock, warnings):
    t = first_table(script, "字幕", "caption", "on-screen", "旁白", "narration", "vo")
    if not t:
        if script.strip():
            warnings.append("SCRIPT.md: no table with a 字幕 / Caption or 旁白 / Narration column; shown as text")
        return {"kind": "", "rows": []}
    kind = "caption" if t.has("字幕", "caption", "on-screen") else "narration"
    rows = []
    for i, r in enumerate(t.rows):
        text = t.get(r, "字幕", "caption", "on-screen") if kind == "caption" else t.get(r, "旁白", "narration", "vo")
        t0, t1 = span(t.get(r, "时间", "time"))
        if t0 is None:
            t0, t1 = bar_span(t.get(r, "小节", "bars"), clock)
        rows.append({"id": plain(t.get(r, "#", "id")) or str(i + 1), "part": plain(t.get(r, "段", "segment")),
                     "seg": _match_segment(t.get(r, "段", "segment"), outline, t0), "term": plain(t.get(r, "术语", "term")),
                     "bars": plain(t.get(r, "小节", "bars")), "t0": t0, "t1": t1, "text": plain(text),
                     "visual": plain(t.get(r, "画面", "visual")), "facts": re.findall(r"#\d+", t.get(r, "素材", "facts", "source"))})
    return {"kind": kind, "rows": rows}


def _facts(notes, warnings):
    body = section(notes, r"^素材清单", r"^Material", r"^Specifics")
    t = first_table(body, "素材", "item", "material")
    facts = []
    if t:
        for r in t.rows:
            claim, gone, _ = struck(t.get(r, "素材", "item", "material"))
            m = re.match(r"^[（(][^）)]*(不用|dropped|unused)[^）)]*[）)]\s*(.*)$", claim, re.I)   # "（关卡 ① 后不用）…"
            if m:
                claim, gone = m.group(2), True
            fid = plain(t.get(r, "#", "id")).lstrip("#")
            facts.append({"id": "#" + fid if fid else "", "claim": plain(claim), "dropped": gone,
                          "kind": plain(t.get(r, "类别", "kind")), "onscreen": plain(t.get(r, "上屏", "on screen", "on-screen")),
                          "source": plain(t.get(r, "出处", "source"))})
    elif notes.strip():
        warnings.append("NOTES.md: no 素材清单 / Material table; shown as text")
    todo_body = section(notes, r"^待核实", r"^To verify", r"^Unverified")
    todo = [{"done": d.lower() == "x", "text": plain(x)} for d, x in re.findall(r"^- \[( |x|X)\] (.+)$", todo_body, re.M)]
    return facts, todo


def _decisions(dec):
    ledger = []
    t = first_table(dec, "决定", "decision")
    if t:
        for r in t.rows:
            ledger.append({"what": plain(t.get(r, "决定", "decision")), "who": plain(t.get(r, "谁拍板", "who", "owner")),
                           "status": plain(t.get(r, "状态", "status")), "where": plain(t.get(r, "在哪看", "where"))})
    agent, group, fence = [], "", None
    body = section(dec, r"^agent 定的事", r"^Decided by the agent", r"^Agent decisions")
    for line in body.split("\n"):
        fence, inside = _fence(line, fence)
        if inside:
            continue
        if line.startswith("### "):
            group = line[4:].strip()
            continue
        if not line.startswith("- "):
            continue
        text, gone, note = struck(line[2:])
        parts = [p.strip() for p in re.split(r"\s+—\s+", text)]
        m = re.match(r"(\{?\d{4}-\d{2}-\d{2}\}?)\s+(.+?)\s+·\s+(.+)$", parts[0])
        pick = lambda *ks: next((re.sub(r"^[^:：]+[:：]\s*", "", p) for p in parts[1:] for k in ks if p.lower().startswith(k)), "")   # noqa: E731
        agent.append({"date": m.group(1) if m else "", "topic": m.group(2) if m else "", "what": plain(m.group(3) if m else parts[0]),
                      "why": plain(pick("理由", "why")), "undo": plain(pick("翻案", "undo")), "superseded": gone,
                      "note": plain(note), "group": group})
    return ledger, agent


def _history(review_md):
    out, paused = [], False
    for title, body in sections(review_md)[1:]:
        if REFERENCE_SECTIONS.match(title):
            continue
        if re.match(r"^(暂停|Paused)", title, re.I) and not re.search(r"恢复|resumed", title, re.I):
            paused = True
        quotes, notes, fence, desk = [], [], None, bool(re.match(r"^(审阅台反馈|Review desk feedback)", title))
        for line in body.split("\n"):
            fence, inside = _fence(line, fence)
            if inside:
                continue
            m = re.match(r"^- (?:原话|Verbatim)\s*(?:[（(]([^）)]*)[）)])?\s*[：:]\s*[\"“「](.+)[\"”」]\s*$", line)
            if m:
                quotes.append({"label": m.group(1) or "", "text": m.group(2)})
                continue
            m = re.match(r"^- (定了|改了|Decided|Changed)\s*[：:][ \t]*(.*)$", line)
            if m:   # "- 定了：A　改了：B" (the template's one-line form) is two notes
                parts = re.split(r"[ \t　]*(改了|Changed)\s*[：:]", m.group(2))
                for k, v in [(m.group(1), parts[0])] + list(zip(parts[1::2], parts[2::2])):
                    if v.strip(" \t　"):
                        notes.append({"k": k, "v": plain(v.strip(" \t　"))})
        if quotes or notes or desk:
            out.append({"title": title, "quotes": quotes, "notes": notes, "desk": desk, "html": render_md(body)})
    return out, paused


GATE_ORDER = {"1": 1, "E0": 2, "E1": 3, "2": 4, "E2": 5, "E3": 6, "E4": 7, "3": 8, "E5": 9}


def gate_pages(project):
    """out/review/gate-*.json in review order; the last is this round. Order: the stop (1, E0, E1, 2, E2, E3, E4, 3,
    E5), then the page within it (1, 1b, 1c …). Modification time only breaks ties between page names outside that
    pattern (they come first), so copying or touching a file never makes an earlier page current again."""
    rdir = Path(project) / "out" / "review"

    def key(p):
        m = re.fullmatch(r"(E\d|\d)([a-z]*)", p.stem[5:])
        return (GATE_ORDER.get(m.group(1), 0), len(m.group(2)), m.group(2), 0, p.name) if m else (0, 0, "", p.stat().st_mtime, p.name)
    pages = [p for p in rdir.glob("gate-*.json") if re.fullmatch(r"[A-Za-z0-9_-]{1,24}", p.stem[5:])] if rdir.is_dir() else []
    return sorted(pages, key=key)


def _rounds(project, warnings):
    out = []
    for g in gate_pages(project):
        rid = g.stem[5:]
        d = _json(g, warnings)
        if not isinstance(d, dict):
            if d is not None:
                warnings.append(f"out/review/{g.name}: expected a JSON object")
            continue
        try:
            d = R.merge_includes(project, d)
        except ValueError as e:
            warnings.append(f"out/review/{g.name}: {e}")
        out.append({"id": rid, "gate": (re.match(r"^(E\d|\d)", rid) or [None, rid])[1], "data": _normalize_round(d),
                    "page": _rel(project, g.with_suffix(".html")) if g.with_suffix(".html").exists() else ""})
    return out


def _normalize_round(d):
    """The shapes tools/review.py accepts, made uniform: options and least_sure as objects, lists as lists."""
    d = dict(d)
    decs = []
    for x in d.get("decisions") or []:
        if not isinstance(x, dict):
            continue
        x = dict(x)
        x["options"] = [o if isinstance(o, dict) else {"id": str(o)} for o in x.get("options") or []]
        decs.append(x)
    d["decisions"] = decs
    d["least_sure"] = [x if isinstance(x, dict) else {"id": "", "note": str(x)} for x in d.get("least_sure") or []]
    for k in ("decided", "delegated", "assets", "appendix", "listen"):
        d[k] = d[k] if isinstance(d.get(k), list) else []
    d["appendix"] = [dict(a, html=render_md(a["text"])) if isinstance(a, dict) and isinstance(a.get("text"), str) else a
                     for a in d["appendix"]]
    d["listen"] = [{"t": float(x["t"]), "note": str(x.get("note", ""))} for x in d["listen"]
                   if isinstance(x, dict) and isinstance(x.get("t"), (int, float))]
    return d


def _shots(project, outline, rounds, warnings):
    sj = _json(project / "shots.json", warnings)
    if sj is None:
        return {}
    items = sj.get("shots") if isinstance(sj, dict) else sj
    if not isinstance(items, list):
        warnings.append("shots.json: expected a list of shots, or {\"shots\": [...]}")
        return {}
    shots = []
    for s in items:
        if not isinstance(s, dict) or "id" not in s:
            continue
        s = dict(s)
        for k in ("start", "end"):
            s[k] = float(s[k]) if isinstance(s.get(k), (int, float)) else None
        reads = s.get("reads")
        s["reads"] = [reads] if isinstance(reads, str) else [str(r) for r in reads] if isinstance(reads, list) else []
        frame = s.get("frame") or f"out/check/storyboard/frames/{s['id']}.png"   # bin/vh storyboard writes these
        s["frame"] = frame if _inside(project, frame) else ""
        s["seg"] = _match_segment(str(s.get("segment", "")), outline, s["start"])
        shots.append(s)
    meta = sj if isinstance(sj, dict) else {}
    video = meta.get("video") or next((r["data"].get("animatic") for r in reversed(rounds) if r["data"].get("animatic")), "") \
        or next((c for c in ("out/animatic.mp4", "out/draft.mp4") if (project / c).is_file()), "")
    return {"video": video if isinstance(video, str) else "", "note": str(meta.get("note", "")), "items": shots}


def _music(project, rounds, warnings):
    g = next((r["data"]["music"] for r in reversed(rounds) if isinstance(r["data"].get("music"), dict)), {})
    bp = _inside(project, g.get("beats"))
    if bp is None:
        cands = sorted((project / "audio").glob("*.beats.json"), key=lambda p: (p.stat().st_mtime, p.name)) if (project / "audio").is_dir() else []
        bp = cands[-1] if cands else None
    beats = (_json(bp, warnings) if bp else None) or {}
    if not isinstance(beats, dict):
        beats = {}
    stem = bp.name[: -len(".beats.json")] if bp and bp.name.endswith(".beats.json") else ""
    audio = g.get("audio") if isinstance(g.get("audio"), str) else next(
        (f"audio/{n}" for n in (f"{stem}_mix.wav", f"{stem}.wav") if stem and (project / "audio" / n).is_file()), "")
    roll = g.get("roll") if isinstance(g.get("roll"), str) else (
        f"audio/{stem}.roll/overview.png" if stem and (project / "audio" / f"{stem}.roll" / "overview.png").is_file() else "")
    labels = g.get("labels") if isinstance(g.get("labels"), dict) else {}
    if not beats and not audio:
        return {}, None
    hits = [{"t": h["t"], "part": str(h.get("what", "")).split(":")[0]} for h in beats.get("hits") or []
            if isinstance(h, dict) and isinstance(h.get("t"), (int, float))]
    if not hits:
        hits = [{"t": n["t"], "part": str(n.get("part", ""))} for n in beats.get("notes") or []
                if isinstance(n, dict) and isinstance(n.get("t"), (int, float))]
    secs = [{"name": str(s.get("name", "")), "label": str(labels.get(s.get("name"), "")), "start": s["start"], "end": s["end"]}
            for s in beats.get("sections") or [] if isinstance(s, dict) and isinstance(s.get("start"), (int, float))
            and isinstance(s.get("end"), (int, float))]
    music = {"bpm": beats.get("bpm"), "duration": beats.get("duration"), "sections": secs, "hits": hits[:MAX_TICKS],
             "audio": audio or "", "roll": roll or "", "beats": _rel(project, bp) if bp else ""}
    return music, beats


def _feedback(project, warnings):
    fdir = project / "out" / "review" / "feedback"
    files = sorted(fdir.glob("*.json"), key=lambda p: (p.stat().st_mtime, p.name))[-MAX_FEEDBACK:] if fdir.is_dir() else []
    out = []
    for f in files:
        j = _json(f, warnings)
        if isinstance(j, dict):
            out.append({"file": _rel(project, f), "round": str(j.get("round", "")), "submitted_at": str(j.get("submitted_at", "")),
                        "decisions": j.get("decisions") if isinstance(j.get("decisions"), dict) else {},
                        "items": [i for i in j.get("items") or [] if isinstance(i, dict)], "general": str(j.get("general", ""))})
    return out


def _docs(project, warnings):
    out = []
    for name in DOCS:
        p = project / name
        if not p.is_file():
            continue
        parts = sections(strip_comments(_read(p, warnings)))
        out.append({"file": name, "intro": render_md(parts[0][1]),
                    "sections": [{"title": t, "html": render_md(b)} for t, b in parts[1:]]})
    return out


def read_project(project):
    """The whole desk data for a project folder (see tools/desk/README.md for every key)."""
    project = Path(project).resolve()
    warnings = []
    brief, script, notes = (_read(project / n, warnings) for n in ("BRIEF.md", "SCRIPT.md", "NOTES.md"))
    dec, review_md = _read(project / "DECISIONS.md", warnings), _read(project / "REVIEW.md", warnings)
    brief, script, notes, dec, review_md = (strip_comments(x) for x in (brief, script, notes, dec, review_md))
    rounds = _rounds(project, warnings)
    music, beats = _music(project, rounds, warnings)
    clock = bar_clock(beats or {})
    spec = [{"k": k, "v": plain(v)} for k, v, _ in bullets(section(brief, r"^Spec", r"^规格"))]
    outline = _outline(brief, clock, warnings)
    captions = _script(script, outline, clock, warnings)
    facts, todo = _facts(notes, warnings)
    ledger, agent = _decisions(dec)
    history, paused = _history(review_md)
    title = (re.search(r"^#\s+BRIEF\s*[：:]\s*(.+)$", brief, re.M) or [None, ""])[1].strip() or project.name
    effort = next((re.split(r"\s", s["v"])[0] for s in spec if s["k"].lower() == "effort"), "")
    cur = rounds[-1] if rounds else None
    # one rule with bin/vh review: this round's gate JSON lang, else the BRIEF's Review language, else zh
    page_lang = cur["data"].get("lang") if cur else None
    lang = page_lang if isinstance(page_lang, str) and page_lang in ("zh", "en") else (R.review_lang(project) or "zh")
    stage = STAGE_OF_GATE.get(cur["gate"], 1) if cur else 0
    return {"version": 1, "lang": lang,
            "project": {"slug": project.name, "title": title, "effort": effort, "paused": paused},
            "stage": stage, "spec": spec, "concept": _concept(brief), "outline": outline, "captions": captions,
            "facts": facts, "fact_todo": todo, "ledger": ledger, "agent_decided": agent, "history": history,
            "rounds": rounds, "feedback": _feedback(project, warnings),
            "shots": _shots(project, outline, rounds, warnings), "music": music,
            "docs": _docs(project, warnings), "warnings": warnings}


if __name__ == "__main__":
    print(json.dumps(read_project(sys.argv[1]), ensure_ascii=False, indent=1))
