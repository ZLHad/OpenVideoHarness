"""Is gate ① on record? A standard or studio film is not rendered whole, nor checked, before the person has decided its
concept (CLAUDE.md, 关卡; playbook/01-pipeline.md). A guard rail for the agent, not a lock: a part of a film renders
without it (bin/vh render --range), and so does any page that is not the project's own film page.

usage: python3 tools/gatecheck.py <project | a file or folder inside it> [--for render|check] [--json f]
       (bin/vh render runs it with --for render before a whole film, bin/vh check before the rest of its checks;
       --json f: the result in a file, {state, message, effort, missing, waived}, for bin/vh check's record)

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


def concept_decided(dec):
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
                if st is None or st >= len(c) or "~~" in c[0] or not re.search(r"concept|立意", c[0], re.I):
                    continue
                status = PLACEHOLDER.sub("", re.sub(r"~~.*?~~", "", c[st])).strip()
                status = re.sub(r"^(?:[（(][^）)]*[）)]\s*)+", "", status.replace("**", "").strip("`* "))   # a leading note, "（作废）已定：B"
                if YES.match(status) and not NOT_YET.match(status):
                    return True
        for line, code in lines:   # agent 定的事: - 2026-10-06 concept · …, not struck, not pending
            m = re.match(r"^\s*-\s+(\d{4}-\d{2}-\d{2})\s+(?:concept|立意)\b[^·\n]*·(.*)$", line, re.I)
            if m and not code and not PENDING_LINE.search(m.group(2).split(" — ")[0]):
                return True
    return False


def project_of(p):
    p = p.resolve()
    for d in [p] + list(p.parents):
        if d.is_dir() and (d / "BRIEF.md").is_file():
            return d
    return None


def main():
    args, it, mode, jpath = [], iter(sys.argv[1:]), "check", None
    for a in it:
        if a == "--for": mode = next(it, "check")
        elif a.startswith("--for="): mode = a.split("=", 1)[1]
        elif a == "--json": jpath = next(it, None)   # the result as JSON in a file, for bin/vh check's record
        else: args.append(a)
    if len(args) != 1:
        print("usage: python3 tools/gatecheck.py <project | a file inside it> [--for render|check] [--json f]", file=sys.stderr); sys.exit(2)

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
        done(0, "on record", f"gate record: {effort} ({src}), gate ① decided in the person's words (REVIEW.md) and the concept on record (DECISIONS.md)", effort=effort)
    done(1, "missing", "\n".join([f"gate record: a {effort} project ({src}) with no record of gate ① — the person decides the concept before the film is made whole:"]
                                  + [f"    {m}" for m in missing]
                                  + ['    or, if the user said in chat to skip the reviews, their words: "- 用户授权跳过（YYYY-MM-DD）。原话：“…”" (templates/REVIEW.md)']),
         effort=effort, missing=missing)


if __name__ == "__main__":
    main()
