"""Is gate ① on record? A standard or studio film is not rendered whole, nor checked, before the person has decided its
concept (CLAUDE.md, 关卡; playbook/01-pipeline.md). A guard rail for the agent, not a lock: a part of a film renders
without it (bin/vh render --range), and so does any page that is not the project's own film page.

usage: python3 tools/gatecheck.py <project | a file or folder inside it> [--for render|check] [--film v] [--spec f] [--json f]
       (bin/vh render runs it with --for render before a whole film, bin/vh check before the rest of its checks;
       --film v: the film bin/vh check is checking, --spec f: tools/speccheck.py's record of it, for its length;
       --json f: the result in a file, {state, message, effort, missing, waived, stops}, for bin/vh check's record)

The project is the nearest folder, from the one given upwards, that holds BRIEF.md. With --for render, only the
project's own page is checked: the project folder itself, or a page directly in it (film.html, index.html); a page in a
folder under it (a concept sketch in out/review/, a look-dev variant) is not. The effort is the BRIEF's "- Effort:"
line, else a 默认努力程度 / Effort line in the harness's LOCAL.md, else standard. A quick project, and one without
REVIEW.md (made before the templates had one), is not checked. A standard or studio project is on record when
  - REVIEW.md has, in a gate ① section ("## 关卡 ① …", "## Gate 1 …", the desk's "## 审阅台反馈 · 关卡 1 · …"; not
    "## 关卡 ① 之前…"), the person's words (a "原话：" / "Verbatim:" line with them, the desk's quoted block under it, or
    quoted words in the section) and a decision: a "定了：…" / "决定：" / "Decided: …" line (bold, numbered or nested too)
    that says something settled (not the template's {…}, an empty "定了：　改了：", "待…", "等…", "未…" or "?"), or one
    left empty with a list right under it, or the older template's ticked "- [x] 通过 / 按意见修改 / 推翻重来"; and
  - DECISIONS.md has, outside code blocks and not struck through, a concept 立意 row whose 状态 / status column says it is
    decided (已定, 定了, 选定, 改了, 通过, decided, chosen, settled, approved) and does not start with 待, 等, 未 or pending,
    or a dated "- YYYY-MM-DD concept · …" (立意 · …) line that is not struck through and not pending (待, 等, 未定, 推荐…);
or when REVIEW.md records the user's own words waiving the gates: "用户授权跳过（YYYY-MM-DD）。原话："…"" ("Waived by the
user (YYYY-MM-DD). Verbatim: "…"") with the words in it, outside code blocks, the reference sections and the 关卡 ② or ③
sections, and without a "范围：" / "Scope:" line right under it that names only gate ② or ③.
Where a film stops is its own (CLAUDE.md, 停在哪): plan_of() reads it for bin/vh status, gate, artifacts and this check.
  - A BRIEF with no "- Stops:" line (a project from before the templates had one): gates ① ② ③, and only gate ① is checked.
  - With the line: gates ① and ③ always; gate ② when the step after the storyboard is expensive for this film (longer than
    90 s by the BRIEF's Output line or by the film checked; a long explainer, type 10; an Engine line that names Blender,
    Three.js or 3D; a Budget line with money in it, or spend on record), when the line names it ("1, 2, 3"), or when the
    Director line keeps the storyboard or the rhythm for the person. A line that leaves gate ② out of an expensive film does
    not take it out: only the user's own words do (the waiver above, under 关卡 ②, or with a 范围 / Scope line that names it).
    Then, --for check on the final film (out/final*, out/final/, media/, Manim at 1080p or more; not a draft, a part or an
    animatic), gate ② needs a decision on record too ("定了：…" in a gate ② section) or that waiver. bin/vh gate asks the
    same before it sends gate ③'s page (tools/gate.py).
Exit: 0 on record, or not checked (the line printed says which) · 1 a record is missing: each missing line is named,
with what to write · 2 not inside a project.
"""
import json, os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\{[^}]*\}")
GATE1 = re.compile(r"(?:^|·\s*)(?:关卡|Gate)\s*(?:①|1)(?![\d])", re.I)
BEFORE = re.compile(r"(?:关卡|Gate)\s*(?:①|1)\s*(?:之前|以前|前[：:\s])|^before\b|before gate", re.I)
LATER = re.compile(r"(?:^|·\s*)(?:关卡|Gate)\s*(?:[②③]|[23])(?![\d])", re.I)
REFERENCE = re.compile(r"^(授权跳过怎么记|给人看的提示|How to record a waived gate|Notes for the reviewer)", re.I)
LIST = r"(?:[-*]|\d+[.)])"
DECIDED = re.compile(rf"^\s*(?:{LIST}\s+)?(?:\*\*)?(?:定了|决定|Decided)(?:\*\*)?\s*(?:[（(][^）)]*[）)])?\s*(?:\*\*)?\s*[：:]\s*(?:\*\*)?(.*)$", re.I)
BOXES = re.compile(r"^\s*[-*]\s+\[[xX]\]\s*(通过|按意见修改|推翻重来|approved|changes requested|start over)", re.I)
SAID = re.compile(rf"^\s*(?:{LIST}\s+)?(?:\*\*)?(?:原话|Verbatim)[^：:\n]*[：:]\s*(.*)$", re.I)
QUOTE = re.compile(r"[\"“「『]([^\"”」』]{2,})[\"”」』]")
WAIVER = re.compile(r"(?:用户授权跳过|Waived by the user)\s*[（(]\s*(\d{4}-\d{2}-\d{2})\s*[）)][^\n]*?(?:原话|Verbatim)\s*[：:]\s*[\"“「『](.+?)[\"”」』]", re.I)
SCOPE = re.compile(r"^\s*(?:[-*]\s+)?(?:范围|Scope)\s*[：:](.*)$", re.I)
NOT_YET = re.compile(r"^\s*(待|等|未|pending|tbd|undecided|not\b|to be decided|[?？])", re.I)
YES = re.compile(r"^\s*(?:(?:own|review|delegate|agent)\S*\s*[：:，,]?\s*)?(?:已定|定了|选定|改了|通过|decided|chosen|settled|approved)", re.I)
PENDING_LINE = re.compile(r"待定|待确认|待人|等人|等用户|未定|未拍板|(?<![按照纳])推荐|propos|pending|tbd|not decided|[?？]\s*$", re.I)
LABEL = re.compile(rf"^\s*(?:{LIST}\s+)?(?:\*\*)?(?:页面|Page|我的理解|理解|agent|下一步|Next|改了|Changed)", re.I)   # lines that are not the person's words


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def read(f):
    return f.read_text(encoding="utf-8", errors="replace")


def sections(text):
    """[(title, [(line, inside a code block)])] of the '## ' sections."""
    out, title, buf, fence = [], "", [], None
    for line in text.split("\n"):
        s = line.strip()
        m = re.match(r"(`{3,}|~{3,})", s)
        if fence:
            if s.startswith(fence) and not s[len(fence):].strip():
                fence = None
            buf.append((line, True)); continue
        if m:
            fence = m.group(1); buf.append((line, True)); continue
        if line.startswith("## "):
            out.append((title, buf)); title, buf = line[3:].strip(), []
        else:
            buf.append((line, False))
    out.append((title, buf))
    return out


def says(s):
    """Something settled: besides placeholders, field labels, spaces and punctuation, and not 待… / 等… / 未… / ?."""
    s = PLACEHOLDER.sub("", s)
    s = re.sub(r"(改了|Changed)\s*[：:]", "", s, flags=re.I)
    if NOT_YET.match(s.strip(" \t　*`")):
        return False
    return bool(re.sub(r"[\s　*`…。，、；：:;,.\-—?？!！]+", "", s))


def local_md():
    """The harness's LOCAL.md (this machine's defaults), or the file OVH_LOCAL_MD names (tests use one of their own)."""
    return Path(os.environ.get("OVH_LOCAL_MD") or ROOT / "LOCAL.md")


def effort_of(project):
    for f, pat in ((project / "BRIEF.md", r"^\s*[-*]\s*(?:\*\*)?Effort(?:\*\*)?\s*[:：]\s*\**\s*(quick|standard|studio)\b"),
                   (local_md(), r"^\s*[-*]?\s*(?:\*\*)?(?:default\s+effort|effort|默认努力程度|努力程度|默认档位|档位)(?:\*\*)?\s*[:：]\s*\**\s*(quick|standard|studio)\b")):
        try:
            m = re.search(pat, strip_comments(read(f)), re.I | re.M)
        except OSError:
            continue
        if m:
            return m.group(1).lower(), ("BRIEF" if f.name == "BRIEF.md" else "LOCAL.md")
    return "standard", "the default"


def record(lines):
    """(decided, the person's words there) in one REVIEW.md section's [(line, inside a code block)]."""
    decided = said = False
    for i, (line, code) in enumerate(lines):
        if code:
            continue
        m = SAID.match(line)
        if m:
            if says(m.group(1).strip("\"“”「」『』")):
                said = True
            else:   # the words under it: a code block (the desk writes one) or a > quote
                for nxt, ncode in lines[i + 1:]:
                    if not nxt.strip() or re.match(r"^\s*(`{3,}|~{3,})", nxt):
                        continue
                    if ncode or nxt.lstrip().startswith(">"):
                        said = said or says(nxt.lstrip(" >"))
                    break
        elif not DECIDED.match(line) and not LABEL.match(line) and any(says(q) for q in QUOTE.findall(line)):
            said = True   # the person's words quoted in the section ("- 10-08（看完第一版）：“…”"), not in a decision line
        if BOXES.match(line):
            decided = True; continue
        m = DECIDED.match(line)
        if not m:
            continue
        if says(m.group(1)):
            decided = True; continue
        if PLACEHOLDER.search(m.group(1)):
            continue   # the template's "定了：{…}" left as it is: nothing listed under it counts either
        for nxt, ncode in lines[i + 1:]:   # "定了：" with the decisions listed under it
            if not nxt.strip():
                continue
            lm = re.match(rf"^\s*{LIST}\s+(.*)$", nxt)
            if ncode or not lm or LABEL.match(nxt) or SAID.match(nxt) or DECIDED.match(nxt):
                break   # another field of the record ("- 改了：…", "- 原话：…"), not a decision under 定了
            if says(lm.group(1)):
                decided = True
                break
    return decided, said


def gate1(review):
    """(decided, the person's words there) over REVIEW.md's gate ① sections."""
    decided = said = False
    for title, lines in sections(review)[1:]:
        if not GATE1.search(title) or BEFORE.search(title):
            continue
        d, s = record(lines)
        decided, said = decided or d, said or s
    return decided, said


# ---- every stop and every page, for bin/vh status (tools/status.py); gate ① above is the same rule ----
CIRCLED = dict(zip("123456789", "①②③④⑤⑥⑦⑧⑨"))


def stop_of(page_id):
    """The stop a review page belongs to, from its name: 1, 2, 3, E0–E5 (2b → 2, e3 → E3); None for another name."""
    m = re.fullmatch(r"(E\d|\d)([A-Za-z]*)", page_id or "", re.I)
    return m.group(1).upper() if m else None


def stop_titles(stop):
    """(the title of a stop's REVIEW.md sections, the title of one that only comes before the stop), as regexes."""
    if stop == "1":
        return GATE1, BEFORE
    if stop.isdigit():
        c = CIRCLED.get(stop, stop)
        return (re.compile(rf"(?:^|·\s*)(?:关卡|Gate)\s*(?:{c}|{stop})(?![\d])", re.I),
                re.compile(rf"(?:关卡|Gate)\s*(?:{c}|{stop})\s*(?:之前|以前|前[：:\s])|before gate\s*{stop}", re.I))
    return re.compile(rf"(?:^|·\s*)(?:(?:关卡|Gate|检查点|Checkpoint)\s*)?{stop}(?![\d])", re.I), re.compile(r"(?!)")


def stop_sections(review, stop):
    """REVIEW.md's sections about a stop: [(title, lines)]."""
    it, before = stop_titles(stop)
    return [(t, ls) for t, ls in sections(review)[1:] if it.search(t) and not before.search(t) and not REFERENCE.match(t)]


def page_sections(review, page_id):
    """REVIEW.md's sections about one review page: the desk's (its title names the page) and those whose lines name
    out/review/gate-<id>.html or .json."""
    t_re = re.compile(rf"(?:^|·\s*)(?:关卡|Gate)\s*{re.escape(page_id)}\s*(?:·|$)", re.I)
    f_re = re.compile(rf"gate-{re.escape(page_id)}\.(?:html|json)\b", re.I)
    return [(t, ls) for t, ls in sections(review)[1:] if not REFERENCE.match(t)
            and (t_re.search(t) or any(f_re.search(x) for x, c in ls if not c))]


def waived_stop(review, stop):
    """The date of the user's own words waiving this stop, else None. Gate ①: waiver() above. Another stop: a waiver in its
    own section, one whose 范围 / Scope line names it or all of them, or one with no scope outside every stop's section."""
    if stop == "1":
        return waiver(review)
    it, _ = stop_titles(stop)
    c = CIRCLED.get(stop, stop)
    named = re.compile(rf"{c}|(?:关卡|gate|检查点|checkpoint)\s*{stop}(?![\d])", re.I) if stop.isdigit() else re.compile(rf"{stop}(?![\d])", re.I)
    any_stop = re.compile(r"(?:^|·\s*)(?:关卡|Gate|检查点|Checkpoint)\s*(?:[①②③]|\d|E\d)", re.I)
    for title, lines in sections(review)[1:]:
        if REFERENCE.match(title):
            continue
        own = bool(it.search(title))
        plain = [line for line, code in lines if not code]
        for i, line in enumerate(plain):
            m = WAIVER.search(line)
            if not m or not says(m.group(2)):
                continue
            scope = next((SCOPE.match(x).group(1) for x in plain[i + 1:i + 5] if SCOPE.match(x)), "")
            if scope and (named.search(scope) or re.search(r"全部|所有|\ball\b", scope, re.I)):
                return m.group(1)
            if not scope and (own or not any_stop.search(title)):
                return m.group(1)
    return None


def waiver(review):
    for title, lines in sections(review)[1:]:
        if LATER.search(title) or REFERENCE.match(title):
            continue
        plain = [line for line, code in lines if not code]
        for i, line in enumerate(plain):
            m = WAIVER.search(line)
            if not m or not says(m.group(2)):
                continue
            scope = next((SCOPE.match(x).group(1) for x in plain[i + 1:i + 5] if SCOPE.match(x)), "")
            if scope and re.search(r"[②③]|关卡\s*[23]|gate\s*[23]", scope, re.I) and not re.search(r"①|关卡\s*1|gate\s*1|全部|所有|\ball\b", scope, re.I):
                continue   # a waiver of the later gates only
            return m.group(1)
    return None


def row_decided(dec, word):
    """Does DECISIONS.md's table have a row for this decision (its first cell matches the regex word) whose 状态 / status
    column says it is decided?"""
    text = strip_comments(dec)
    cells = lambda x: [c.strip() for c in x.strip().strip("|").split("|")]   # noqa: E731
    for _title, lines in sections(text):
        k = 0
        while k < len(lines):   # tables: a header, a separator, rows; the status column found by its header
            line, code = lines[k]
            if code or not line.strip().startswith("|") or k + 1 >= len(lines) or not re.match(r"^\s*\|?\s*:?-{2,}", lines[k + 1][0]):
                k += 1; continue
            head = cells(line)
            st = next((j for j, h in enumerate(head) if re.match(r"(状态|status)", h, re.I)), None)
            k += 2
            while k < len(lines) and lines[k][0].strip().startswith("|") and not lines[k][1]:
                c = cells(lines[k][0])
                k += 1
                if st is None or st >= len(c) or "~~" in c[0] or not re.search(word, c[0], re.I):
                    continue
                status = PLACEHOLDER.sub("", re.sub(r"~~.*?~~", "", c[st])).strip()
                status = re.sub(r"^(?:[（(][^）)]*[）)]\s*)+", "", status.replace("**", "").strip("`* "))   # a leading note, "（作废）已定：B"
                if YES.match(status) and not NOT_YET.match(status):
                    return True
    return False


def concept_decided(dec):
    if row_decided(dec, r"concept|立意"):
        return True
    for _title, lines in sections(strip_comments(dec)):
        for line, code in lines:   # agent 定的事: - 2026-10-06 concept · …, not struck, not pending
            m = re.match(r"^\s*-\s+(\d{4}-\d{2}-\d{2})\s+(?:concept|立意)\b[^·\n]*·(.*)$", line, re.I)
            if m and not code and not PENDING_LINE.search(m.group(2).split(" — ")[0]):
                return True
    return False


# ---- where a film stops (CLAUDE.md, 停在哪; playbook/01-pipeline.md, 人工关卡): its plan, for status, gate, artifacts and main() ----
SHORT = 90   # seconds: up to this long, with nothing expensive after the storyboard, the storyboard is shown on the draft's page
# what a Director line can keep for the person (x=own), and the stop where playbook/01's 导演模式 table first has each
OWN_STOP = {"concept": "1", "spec": "1", "outline": "1", "style": "1", "hook": "1", "character": "E0", "theme": "E0", "voice": "E1", "script": "E1",
            "storyboard": "2", "rhythm": "2", "packaging": "3"}
HEAVY_3D = re.compile(r"blender|three\.?js|\bthree\b|\b3d\b|webgl|path[- ]?trac", re.I)
MANIM_FINAL = re.compile(r"(1080|1440|1920|2160|3840)p")   # media/videos/<scene>/1080p30: the folder is named by the height, so 1920p30 is a vertical 1080p
FAILED_FILM = re.compile(r"\.failed(-\d+)?$", re.I)        # a film bin/vh patch kept because a check failed (tools/proxy.py's is_failed)
WHY = {"long": ("片子长（约 {n} 秒）", "it is long (about {n} s)"), "type10": ("是长讲解", "it is a long explainer"), "3d": ("3D 渲染重", "its 3D render is heavy"),
       "budget": ("有付费调用", "it has paid calls"), "spent": ("有付费调用", "it has paid calls")}


def brief_line(project, key):
    """A Spec line of the BRIEF ("- Stops: 1, 3") without its comment; None when the BRIEF has no such line."""
    try:
        text = strip_comments(read(Path(project) / "BRIEF.md"))
    except OSError:
        return None
    m = re.search(rf"(?m)^[ \t]*[-*][ \t]*(?:\*\*)?{key}(?:\*\*)?[ \t]*[:：][ \t]*(.*)$", text)
    return m.group(1).strip().strip("*`").strip() if m else None


def director_stops(director_line):
    """The checkpoints a Director line asks for: stop=E3, stop=E1,E3, and every stop= on the line (stop=E1, stop=E3)."""
    return {s.upper() for grp in re.findall(r"\bstop\s*=\s*(E[0-9](?![0-9])(?:\s*[,，]?\s*E[0-9](?![0-9]))*)", director_line or "", re.I)
            for s in re.findall(r"E[0-9]", grp, re.I)}


def director_own(director_line):
    """What a Director line keeps for the person, {thing: its stop} (None for a word playbook/01 does not name): voice=own, and
    rest=own for everything the line does not name."""
    said = {k.lower(): v.lower() for k, v in re.findall(r"(\w+)\s*=\s*(\w+)", director_line or "")}
    own = [k for k, v in said.items() if v == "own" and k != "rest"]
    if said.get("rest") == "own":
        own += [k for k in OWN_STOP if k not in said]
    return {k: OWN_STOP.get(k) for k in own}


def named_stops(line):
    """The stops a Stops line names: {"1", "2", "3", "E3"} ("1, 3", "①③", "1, E3, 3"; "all", "每步都看": the three gates); None
    for default, an empty line, the template's {…} or words that name no stop."""
    v = PLACEHOLDER.sub("", line or "").strip()
    if not v or re.match(r"(default|默认)", v, re.I):
        return None
    if re.search(r"\ball\b|every|每步|每一步|全部", v, re.I):
        return {"1", "2", "3"} | {m.upper() for m in re.findall(r"E\d", v, re.I)}
    out = {m.upper() for m in re.findall(r"E\d", v, re.I)}
    rest = re.sub(r"E\d", " ", v, flags=re.I)
    out |= {str("①②③".index(c) + 1) for c in rest if c in "①②③"} | set(re.findall(r"(?<!\d)[123](?!\d)", rest))
    return out or None


def film_seconds(output_line):
    """The length an Output line gives, in seconds: "exactly 45s", "{60–90}s" (its longer end), "12 min"; None when it gives none yet."""
    o = (output_line or "").replace("{", " ").replace("}", " ")
    found = [float(n) for n in re.findall(r"(\d+(?:\.\d+)?)\s*(?:s\b|秒)", o, re.I)]
    found += [float(n) * 60 for n in re.findall(r"(\d+(?:\.\d+)?)\s*(?:min\b|分钟)", o, re.I)]
    return max(found) if found else None


def costly(project, seconds=None):
    """Why the step after the storyboard is expensive for this film, as its files say it: [{"code", "say"}], [] for a short film
    with nothing paid. seconds: the length of the film being checked, when that is known (the BRIEF may not say one yet)."""
    project, why = Path(project), []
    secs = max(film_seconds(brief_line(project, "Output")) or 0, seconds or 0)
    if secs > SHORT:
        why.append({"code": "long", "say": f"{secs:g} s long (over {SHORT} s)", "n": round(secs)})
    try:
        if re.search(r"video-types/10-|<!-- from 10-", read(project / "BRIEF.md")):
            why.append({"code": "type10", "say": "a long explainer (type 10)"})
    except OSError:
        pass
    engine = PLACEHOLDER.sub("", brief_line(project, "Engine") or "")
    if HEAVY_3D.search(engine):
        why.append({"code": "3d", "say": f"a 3D render (Engine: {engine[:40]})"})
    try:   # money: the film's own Budget line, or spend on record (tools/assets/budget.py); what cannot be read is no reason
        sys.path.insert(0, str(ROOT / "tools" / "assets"))
        import budget
        b = budget.parse(brief_line(project, "Budget"))
        if b and (b["unlimited"] or any(v > 0 for v in b["amounts"].values())):
            why.append({"code": "budget", "say": "paid calls are budgeted (the BRIEF's Budget line)"})
        elif any(v > 0 for v in budget.spent(project).values()):
            why.append({"code": "spent", "say": "paid calls on record (assets/spend.jsonl)"})
    except Exception:
        pass
    return why


def plan_of(project, seconds=None):
    """Where this film stops for the person: {"gates": the gates in order, "checkpoints": the E-stops asked for, "line": the
    BRIEF's Stops line (None: the BRIEF has none, a project from before it did), "named": what the line names (None: default),
    "costly": costly(), "kept": the gates the line leaves out and the film keeps, "quick"}. A quick film has no gates."""
    project = Path(project)
    line, director = brief_line(project, "Stops"), brief_line(project, "Director")
    named = named_stops(line)
    own = {v for v in director_own(director).values() if v}   # (what it keeps at a checkpoint is bin/vh status's to follow: settled or not)
    points = sorted(director_stops(director) | {s for s in (named or ()) if s.startswith("E")})
    out = {"gates": [], "checkpoints": points, "line": line, "named": sorted(named) if named else None, "costly": [], "kept": [],
           "quick": effort_of(project)[0] == "quick"}
    if out["quick"]:
        return out
    if line is None:
        out["gates"] = ["1", "2", "3"]
        return out
    out["costly"] = costly(project, seconds)
    gates = {"1", "3"}
    if out["costly"] or "2" in own or (named and "2" in named):
        gates.add("2")
    if named:
        out["kept"] = sorted(g for g in gates if g not in named and (g != "2" or out["costly"]))
    out["gates"] = sorted(gates)
    return out


def plan_note(plan):
    """One line about a plan, for bin/vh status and the tools' messages."""
    if plan["quick"]:
        return "Effort quick: no gates" + (f"; {', '.join(plan['checkpoints'])} asked for" if plan["checkpoints"] else "")
    marks = " ".join(CIRCLED[g] for g in plan["gates"]) + "".join(f" {c}" for c in plan["checkpoints"])
    if plan["line"] is None:
        return f"{marks} (the BRIEF has no Stops line: the three gates)"
    why = "; ".join(c["say"] for c in plan["costly"])
    if "2" in plan["gates"]:
        tail = why or ("the Stops line names it" if plan["named"] and "2" in plan["named"] else "the Director line keeps the storyboard for the person")
        if "2" in plan["kept"]:
            tail += "; the Stops line leaves gate ② out, and only the user's own words take a stop away (REVIEW.md)"
        return f"{marks} (gate ②: {tail})"
    return f"{marks} (a short film with nothing expensive after the storyboard: the storyboard is shown on gate ③'s page)"


def plan_words(plan, lang, title=lambda g: g):
    """What the person is told at the first stop: where this film stops, and that one sentence adds or takes away a stop.
    title: a checkpoint's name in the page's language (tools/review.py's gate_title)."""
    zh = lang != "en"
    why = list(dict.fromkeys(WHY[c["code"]][0 if zh else 1].format(n=c.get("n", "")) for c in plan["costly"] if c["code"] in WHY))
    extra = [title(c) for c in plan["checkpoints"]]
    if "2" in plan["gates"]:
        s = ("这支片子我打算停三次：这一次（立意）、分镜、初版" + (f"；分镜单独停，因为{'、'.join(why)}" if why else "") + "。") if zh else \
            ("I plan to stop three times on this film: now (the concept), at the storyboard, and at the first draft"
             + (f"; the storyboard is a stop of its own because {' and '.join(why)}" if why else "") + ".")
    else:
        s = "这支片子我打算停两次：这一次（立意）和初版；分镜随初版那一页给你，不单独停。" if zh else \
            "I plan to stop twice on this film: now (the concept) and at the first draft; the storyboard comes on the draft's page, not as a stop of its own."
    if extra:
        s += (f"另外在{'、'.join(extra)}也停。" if zh else f" Also at {', '.join(extra)}.")
    return s + ("想多看一步或少看一步，回我一句就行。" if zh else " Tell me in a sentence if you want to see more, or less.")


def stop_on_record(review, stop):
    """Is a stop behind the film: a decision for it on record ("定了：…" in one of its sections; gate ①: in a gate ① section), or
    the user's own words waiving it. → "decided", "waived" or None."""
    if waived_stop(review, stop):
        return "waived"
    decided = gate1(review)[0] if stop == "1" else any(record(ls)[0] for _, ls in stop_sections(review, stop))
    return "decided" if decided else None


def not_on_record(project, before):
    """The gates of this film's plan between gate ① and a stop ("3": gate ②) that are not behind it yet: [gate]. [] for a quick
    film, a BRIEF with no Stops line and a project with no REVIEW.md. Gate ① is main()'s to ask, of the whole render and the check."""
    project = Path(project)
    plan = plan_of(project)
    if plan["quick"] or plan["line"] is None or not (project / "REVIEW.md").is_file():
        return []
    review = strip_comments(read(project / "REVIEW.md"))
    return [g for g in plan["gates"] if "1" < g < before and not stop_on_record(review, g)]


def is_final(path):
    """A film (its path from the project) that counts as the delivery: out/final*, out/final/…, a file directly in media/, or
    Manim's render at 1080p or more; not its drafts (480p15, 720p30), and not a film a failed patch left."""
    parts = Path(path).parts
    if not parts or FAILED_FILM.search(Path(parts[-1]).stem):
        return False
    if parts[:2] == ("media", "videos"):   # Manim's tree: the folder says the quality, whatever the scene is called
        return len(parts) > 1 and bool(MANIM_FINAL.match(parts[-2]))
    return parts[-1].lower().startswith("final") or "final" in parts[:-1] or (len(parts) > 1 and parts[-2] == "media")


def project_of(p):
    p = p.resolve()
    for d in [p] + list(p.parents):
        if d.is_dir() and (d / "BRIEF.md").is_file():
            return d
    return None


def main():
    args, it, mode, jpath, film, spec = [], iter(sys.argv[1:]), "check", None, None, None
    for a in it:
        if a == "--for": mode = next(it, "check")
        elif a.startswith("--for="): mode = a.split("=", 1)[1]
        elif a == "--json": jpath = next(it, None)   # the result as JSON in a file, for bin/vh check's record
        elif a == "--film": film = next(it, None)    # the film bin/vh check is checking
        elif a == "--spec": spec = next(it, None)    # tools/speccheck.py's record of it: its measured length
        else: args.append(a)
    if len(args) != 1:
        print("usage: python3 tools/gatecheck.py <project | a file inside it> [--for render|check] [--film v] [--spec f] [--json f]", file=sys.stderr); sys.exit(2)

    def done(code, state, line, **extra):
        if jpath:
            try:
                Path(jpath).write_text(json.dumps(dict(state=state, message=line.split("\n")[0], **extra), ensure_ascii=False), encoding="utf-8")
            except OSError as e:
                print(f"gatecheck: could not write {jpath} ({e.strerror or e})", file=sys.stderr)
        print(line)
        sys.exit(code)
    given = Path(args[0])
    proj = project_of(given)
    if not proj:
        done(2, "not checked", f"gate record: {args[0]} is not inside a project (no BRIEF.md above it): not checked")
    if mode == "render":   # only the project's own film page: a sketch or a look-dev page in a folder under it renders freely
        where = given.resolve() if given.is_dir() else given.resolve().parent
        if where != proj:
            done(0, "not checked", f"gate record: {args[0]} is not the project's own page (a sketch or look-dev page): not checked")
    effort, src = effort_of(proj)
    review_f, dec_f = proj / "REVIEW.md", proj / "DECISIONS.md"
    if effort == "quick":
        done(0, "no gates", f"gate record: Effort quick ({src}): no gates to record", effort=effort)
    if not review_f.is_file():
        done(0, "not checked", "gate record: no REVIEW.md (a project from before the templates had one): not checked", effort=effort)
    review = strip_comments(read(review_f))
    w = waiver(review)
    if w:
        done(0, "waived", f"gate record: {effort} ({src}), the gates waived in the user's own words ({w}, REVIEW.md)", effort=effort, waived=w)
    missing = []
    decided, said = gate1(review)
    if not said:
        missing.append('REVIEW.md: under "## 关卡 ① 立意和大纲", the person\'s words: "- 原话：“…”" (verbatim, as they wrote them)')
    if not decided:
        missing.append('REVIEW.md: under "## 关卡 ① 立意和大纲", the decision: "- 定了：…" (which concept card, and what else was settled)')
    if not dec_f.is_file():
        missing.append("DECISIONS.md is missing: copy templates/DECISIONS.md and fill in its concept 立意 row")
    elif not concept_decided(read(dec_f)):
        missing.append('DECISIONS.md: the concept 立意 row\'s status, "已定（关卡 ①）：<the concept>" (it is still 待定, the template\'s {…}, or struck through)')
    if not missing:
        # gate ②, for a film whose plan has it (a BRIEF with a Stops line): asked of the final film, not of a draft, a part or an animatic
        seconds = None
        try:
            seconds = float(json.loads(Path(spec).read_text(encoding="utf-8"))["measured"]["duration"]) if spec else None
        except (OSError, ValueError, KeyError, TypeError):
            pass
        plan = plan_of(proj, seconds)
        stops = {"gates": plan["gates"], "checkpoints": plan["checkpoints"]}
        final = False
        if film:
            try:
                final = is_final(Path(os.path.relpath(Path(film).resolve(), proj)))
            except ValueError:
                pass
        if mode == "check" and final and plan["line"] is not None and "2" in plan["gates"] and not stop_on_record(review, "2"):
            why = "; ".join(c["say"] for c in plan["costly"]) or "the BRIEF's Stops or Director line asks for it"
            miss = ['REVIEW.md: under "## 关卡 ② 分镜", the decision: "- 定了：…", once the person has seen the storyboard (bin/vh gate <project> 2)']
            done(1, "missing", "\n".join([f"gate record: a {effort} project ({src}) with no record of gate ② — this film's storyboard is the person's to see before the film is made ({why}):"]
                                          + [f"    {m}" for m in miss]
                                          + ['    or, if the user said in chat to skip it, their words there: "- 用户授权跳过（YYYY-MM-DD）。原话：“…”" (templates/REVIEW.md)']),
                 effort=effort, missing=miss, stops=stops)
        done(0, "on record", f"gate record: {effort} ({src}), gate ① decided in the person's words (REVIEW.md) and the concept on record (DECISIONS.md)", effort=effort, stops=stops)
    done(1, "missing", "\n".join([f"gate record: a {effort} project ({src}) with no record of gate ① — the person decides the concept before the film is made whole:"]
                                  + [f"    {m}" for m in missing]
                                  + ['    or, if the user said in chat to skip the reviews, their words: "- 用户授权跳过（YYYY-MM-DD）。原话：“…”" (templates/REVIEW.md)']),
         effort=effort, missing=missing)


if __name__ == "__main__":
    main()
