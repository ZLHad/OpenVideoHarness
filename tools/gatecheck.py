"""Is gate ① on record? A standard or studio film is not rendered whole, nor checked, before the person has decided its
concept (CLAUDE.md, 关卡; playbook/01-pipeline.md).

usage: python3 tools/gatecheck.py <project | a file or folder inside it> [--for render|check]
       (bin/vh render runs it before a whole film, bin/vh check before the rest of its checks)

The project is the nearest folder, from the one given upwards, that holds BRIEF.md. Its effort is the BRIEF's
"- Effort:" line, else an "Effort:" (or 默认档位：) line in the harness's LOCAL.md, else standard. A quick project, and one
without REVIEW.md (made before the templates had one), is not checked. A standard or studio project is on record when
  - REVIEW.md, in a "## 关卡 ①" section ("## Gate 1"; not "关卡 ① 之前"), has a decision: a "定了：…" line
    ("Decided: …", "**定了**：", "决定：") that says something (the template's {…} and an empty "定了：　改了：" do not),
    or one left empty with a list right under it, or a ticked box of the older template ("- [x] 通过"); and
  - DECISIONS.md has a concept 立意 row whose status is neither empty, the template's {…}, nor 待定 (pending), or a
    dated "- YYYY-MM-DD concept · …" (立意 · …) line that is not struck through;
or when REVIEW.md records the user's own words waiving the gates: "用户授权跳过（YYYY-MM-DD）。原话："…"" ("Waived by the
user (YYYY-MM-DD). Verbatim: "…"") with the words in it, anywhere but in a 关卡 ② or ③ section (a waiver there is
for that gate only).
Exit: 0 on record, or not checked (the line printed says which) · 1 a record is missing: each missing line is named,
with what to write · 2 not inside a project.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\{[^}]*\}")
GATE1 = re.compile(r"^(关卡|Gate)\s*(①|1)(?![\d①-⑳])", re.I)
LATER = re.compile(r"^(关卡|Gate)\s*([②③]|[23])(?!\d)", re.I)
DECIDED = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?(?:定了|决定|Decided)(?:\*\*)?\s*(?:[（(][^）)]*[）)])?\s*(?:\*\*)?\s*[：:]\s*(?:\*\*)?(.*)$", re.I)
WAIVER = re.compile(r"(?:用户授权跳过|Waived by the user)\s*[（(]\s*(\d{4}-\d{2}-\d{2})\s*[）)][^\n]*?(?:原话|Verbatim)\s*[：:]\s*[\"“「『](.+?)[\"”」』]", re.I)
PENDING = re.compile(r"^(待定|未定|pending|tbd|undecided|to be decided)", re.I)


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def sections(text):
    """[(title, [lines])] of the '## ' sections, fenced code left out."""
    out, title, buf, fence = [], "", [], None
    for line in text.split("\n"):
        s = line.strip()
        m = re.match(r"(`{3,}|~{3,})", s)
        if fence:
            if s.startswith(fence): fence = None
            continue
        if m:
            fence = m.group(1); continue
        if line.startswith("## "):
            out.append((title, buf)); title, buf = line[3:].strip(), []
        else:
            buf.append(line)
    out.append((title, buf))
    return out


def says(s):
    """Something besides placeholders, field labels, spaces and punctuation."""
    s = PLACEHOLDER.sub("", s)
    s = re.sub(r"(改了|Changed)\s*[：:]", "", s, flags=re.I)
    s = re.sub(r"[\s　*`…。，、；：:;,.\-—]+", "", s)
    return bool(s) and not PENDING.match(s)


def effort_of(project):
    for f, pat in ((project / "BRIEF.md", r"^\s*[-*]\s*Effort\s*[:：]\s*\**\s*(quick|standard|studio)\b"),
                   (ROOT / "LOCAL.md", r"^\s*[-*]?\s*(?:default\s+)?(?:effort|默认档位|档位)\s*[:：]\s*\**\s*(quick|standard|studio)\b")):
        try:
            m = re.search(pat, strip_comments(f.read_text(encoding="utf-8")), re.I | re.M)
        except OSError:
            continue
        if m:
            return m.group(1).lower(), ("BRIEF" if f.name == "BRIEF.md" else "LOCAL.md")
    return "standard", "the default"


def gate1_decided(review):
    for title, lines in sections(review)[1:]:
        if not GATE1.match(title) or re.search(r"之前|before", title, re.I):
            continue
        for i, line in enumerate(lines):
            if re.match(r"^\s*[-*]\s+\[[xX]\]", line) or re.search(r"[-*]\s+\[[xX]\]\s*(通过|按意见修改|推翻重来)", line):
                return True   # the older template's boxes: - [x] 通过　- [ ] 按意见修改　- [ ] 推翻重来
            m = DECIDED.match(line)
            if not m:
                continue
            if says(m.group(1)):
                return True
            for nxt in lines[i + 1:]:   # "定了：" with the decisions listed under it
                if not nxt.strip():
                    continue
                lm = re.match(r"^\s*(?:[-*]|\d+[.)])\s+(.*)$", nxt)
                if not lm:
                    break
                if says(lm.group(1)):
                    return True
    return False


def waiver(review):
    for title, lines in sections(review)[1:]:
        if LATER.match(title) or re.match(r"^(授权跳过怎么记|How to record a waived gate)", title):
            continue
        for m in WAIVER.finditer("\n".join(lines)):
            if says(m.group(2)):
                return m.group(1)
    return None


def concept_decided(dec):
    text = strip_comments(dec)
    for line in text.split("\n"):   # the ledger: | concept 立意 | who | status | where |
        c = [x.strip() for x in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(c) >= 3 and re.search(r"concept|立意", c[0], re.I) and not re.match(r"^:?-+:?$", c[0]):
            if says(c[2]):
                return True
    for title, lines in sections(text)[1:]:   # agent 定的事: - 2026-10-06 concept · …
        for line in lines:
            if re.match(r"^\s*-\s+\d{4}-\d{2}-\d{2}\s+(concept|立意)\b[^·]*·", line, re.I):
                return True
    return False


def project_of(p):
    p = p.resolve()
    for d in [p] + list(p.parents):
        if d.is_dir() and (d / "BRIEF.md").is_file():
            return d
    return None


def main():
    args, it = [], iter(sys.argv[1:])
    for a in it:
        if a == "--for": next(it, None)
        elif not a.startswith("--for="): args.append(a)
    if len(args) != 1:
        print("usage: python3 tools/gatecheck.py <project | a file inside it> [--for render|check]", file=sys.stderr); sys.exit(2)
    proj = project_of(Path(args[0]))
    if not proj:
        print(f"gate record: {args[0]} is not inside a project (no BRIEF.md above it): not checked"); sys.exit(2)
    effort, src = effort_of(proj)
    review_f, dec_f = proj / "REVIEW.md", proj / "DECISIONS.md"
    if effort == "quick":
        print(f"gate record: Effort quick ({src}): no gates to record"); sys.exit(0)
    if not review_f.is_file():
        print("gate record: no REVIEW.md (a project from before the templates had one): not checked"); sys.exit(0)
    review = strip_comments(review_f.read_text(encoding="utf-8", errors="replace"))
    w = waiver(review)
    if w:
        print(f"gate record: {effort} ({src}), the gates waived in the user's own words ({w}, REVIEW.md)"); sys.exit(0)
    missing = []
    if not gate1_decided(review):
        missing.append('REVIEW.md: under "## 关卡 ① 立意和大纲", the decision: "- 定了：…" (which concept card, and what else was settled), '
                       'after "- 原话：" with the person\'s words')
    dec = dec_f.read_text(encoding="utf-8", errors="replace") if dec_f.is_file() else ""
    if not dec_f.is_file():
        missing.append("DECISIONS.md is missing: copy templates/DECISIONS.md and fill in its concept 立意 row")
    elif not concept_decided(dec):
        missing.append('DECISIONS.md: the concept 立意 row\'s status, "已定（关卡 ①）：<the concept>" (it is still 待定 or the template\'s {…})')
    if not missing:
        print(f"gate record: {effort} ({src}), gate ① decided (REVIEW.md) and the concept on record (DECISIONS.md)"); sys.exit(0)
    print(f"gate record: a {effort} project ({src}) with no record of gate ① — the person decides the concept before the film is made whole:")
    for m in missing:
        print(f"    {m}")
    print('    or, if the user said in chat to skip the reviews, their words: "- 用户授权跳过（YYYY-MM-DD）。原话：“…”" (templates/REVIEW.md)')
    sys.exit(1)


if __name__ == "__main__":
    main()
