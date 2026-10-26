"""How much an agent reads before it starts a film, by effort level and video type, following CLAUDE.md's routing.

usage (from the repo root): python3 tools/readpath.py [--json]

Counts characters (Python's len of the text), not tokens. It estimates what the routing asks an agent to read, not what
an agent actually opened. Every level counts the same base: CLAUDE.md, §4 of playbook/03 (the text-size floor, kept at
every level), templates/TASTE_CHECKLIST.md (hard rule 4) and the engine docs (below). On top of it:
  quick     playbook/quick.md and what its steps name: the type doc's 工作流, 禁止 and Prompt 增量块 sections,
            playbook/12 §3 and §7, and playbook/02's 手机测试 section
  standard  the whole type doc, playbook/01, 02 and 12 (CLAUDE.md steps 1, 2 and 4)
  +sound    standard + playbook/04-audio.md (narration or music)
  max       +sound + playbook/09, 10 and 11 (long or story-driven films, publishing, a themed score). A ceiling of the
            playbook reads, not of everything: playbook/08, recipes/ and styles/ are read on demand and not counted
engine    the engine docs counted at every level: the section of engines/README.md for the engine bin/vh new sets up,
          plus the guide the routing names in full (ANIMATION_GUIDE.md for 04 and 07, engines/editing.md for 09).
          04 and 06 show one engine though their type docs allow two (04: HyperFrames for type-led videos; 06: Manim
          and HyperFrames mixed). A film that spans two types reads both type docs.
tools/ci.sh prints this table as a baseline. It never fails on the numbers; it fails when a file or a section it
counts is missing, so the table cannot quietly shrink.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = {"01": "Manim", "02": "HyperFrames", "03": "HyperFrames", "04": "ClaudeAnimationBase", "05": "HyperFrames",
          "06": "Manim", "07": "ClaudeAnimationBase", "08": "HyperFrames", "09": "HyperFrames"}   # what bin/vh new sets up
GUIDE = {"04": "engines/ClaudeAnimationBase/ANIMATION_GUIDE.md", "07": "engines/ClaudeAnimationBase/ANIMATION_GUIDE.md",
         "09": "engines/editing.md"}

def text(rel):
    p = ROOT / rel
    if not p.is_file(): sys.exit(f"readpath: {rel} is missing")
    return p.read_text(encoding="utf-8")

def sections(rel, *prefixes):
    """The level-2 sections of a markdown file whose heading starts with each prefix, each up to the next ## heading.
    Every prefix must match: a renamed heading stops the script instead of dropping out of the count."""
    found, out, keep = set(), [], False
    for line in text(rel).splitlines(keepends=True):
        if line.startswith("## "):
            hit = [p for p in prefixes if line[3:].startswith(p)]
            keep = bool(hit); found.update(hit)
        if keep: out.append(line)
    missing = [p for p in prefixes if p not in found]
    if missing: sys.exit(f"readpath: {rel} has no '## ' section starting with {', '.join(missing)}")
    return "".join(out)

def outline(rel, levels=(2, 3)):
    """The sections of a markdown file by its headings at these levels: [(level, heading, line, text)], each up to the
    next heading at any of them (a ## section's text stops where its first ### starts), its heading line included;
    the lines before the first one (title and lead) as level 1 under the # title. A heading inside a ``` fence is not
    one. bin/vh know (tools/know.py) indexes these."""
    out, fence, cur = [], False, None
    for n, line in enumerate(text(rel).splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"(#{1,6}) +(.+?)\s*#*\s*$", line)
        lv = len(m.group(1)) if m else 0
        if m and (lv in levels or (lv == 1 and cur is None)):
            cur = [lv, m.group(2).strip(), n, []]
            out.append(cur)
        elif cur is None:
            cur = [1, "", n, []]
            out.append(cur)
        cur[3].append(line)
    return [(lv, h, n, "\n".join(body)) for lv, h, n, body in out]

def table():
    base = len(text("CLAUDE.md")) + len(sections("playbook/03-motion-design.md", "4.")) + len(text("templates/TASTE_CHECKLIST.md"))
    docs = sorted((ROOT / "video-types").glob("[0-9][0-9]-*.md"))
    if not docs: sys.exit("readpath: no type docs in video-types/")
    rows = []
    for doc in docs:
        rel = f"video-types/{doc.name}"; n = doc.name[:2]
        if n not in ENGINE: sys.exit(f"readpath: {rel}: no engine for type {n}; add it to ENGINE (and GUIDE if it has a guide)")
        engine = len(sections("engines/README.md", ENGINE[n])) + (len(text(GUIDE[n])) if n in GUIDE else 0)
        quick = base + engine + sum(len(x) for x in (
            text("playbook/quick.md"), sections(rel, "工作流", "禁止", "Prompt 增量块"),
            sections("playbook/12-ideation.md", "3.", "7."), sections("playbook/02-verification.md", "手机测试")))
        standard = base + engine + len(text(rel)) + sum(len(text(f"playbook/{f}")) for f in
                                                         ("01-pipeline.md", "02-verification.md", "12-ideation.md"))
        sound = standard + len(text("playbook/04-audio.md"))
        top = sound + sum(len(text(f"playbook/{f}")) for f in ("09-narrative.md", "10-hooks-and-packaging.md", "11-composition.md"))
        rows.append({"type": doc.stem, "quick": quick, "standard": standard, "sound": sound, "max": top, "engine": engine})
    return rows

def main():
    rows = table()
    if "--json" in sys.argv[1:]:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    w = max(len(r["type"]) for r in rows)
    print("read path · characters an agent reads before it starts (CLAUDE.md's routing; tools/readpath.py)")
    print(f"{'type':<{w}}  {'quick':>8}  {'standard':>9}  {'+sound':>8}  {'max':>8}    {'(engine)':>8}")
    for r in rows:
        print(f"{r['type']:<{w}}  {r['quick']:>8,}  {r['standard']:>9,}  {r['sound']:>8,}  {r['max']:>8,}    {r['engine']:>8,}")

if __name__ == "__main__":
    main()
