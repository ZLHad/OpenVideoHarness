"""How much an agent reads before it starts a film, by effort level and video type, following CLAUDE.md's routing.

usage (from the repo root): python3 tools/readpath.py [--json]

Counts characters (Python's len of the text), not tokens. It estimates what the routing asks an agent to read, not what
an agent actually opened:
  quick     CLAUDE.md, playbook/quick.md, the type doc's 工作流 and 禁止 sections, and the section of engines/README.md
            for the type's engine (quick.md, step 1)
  standard  CLAUDE.md, the whole type doc, playbook/01, 02, 03 (§4 holds the text-size floor every level keeps) and 12,
            and templates/TASTE_CHECKLIST.md (CLAUDE.md steps 1, 2 and 4, hard rule 4)
  +sound    standard + playbook/04-audio.md (narration or music)
  studio    +sound + playbook/09, 10 and 11: what CLAUDE.md adds for long or story-driven films, publishing and a
            themed score; the most a film reads before it starts
A film that spans two types reads both type docs. tools/ci.sh prints this table as a baseline; it does not fail.
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = {"01": "Manim", "02": "HyperFrames", "03": "HyperFrames", "04": "ClaudeAnimationBase", "05": "HyperFrames",
          "06": "Manim", "07": "ClaudeAnimationBase", "08": "HyperFrames", "09": "HyperFrames"}   # what bin/vh new sets up
STANDARD = ["CLAUDE.md", "playbook/01-pipeline.md", "playbook/02-verification.md", "playbook/03-motion-design.md",
            "playbook/12-ideation.md", "templates/TASTE_CHECKLIST.md"]
SOUND = ["playbook/04-audio.md"]
STUDIO = ["playbook/09-narrative.md", "playbook/10-hooks-and-packaging.md", "playbook/11-composition.md"]

def text(rel): return (ROOT / rel).read_text(encoding="utf-8")

def sections(rel, *prefixes):
    """The level-2 sections of a markdown file whose heading starts with one of the prefixes, each up to the next ## heading."""
    out, keep = [], False
    for line in text(rel).splitlines(keepends=True):
        if line.startswith("## "):
            keep = any(line[3:].startswith(p) for p in prefixes)
        if keep: out.append(line)
    if not out: sys.exit(f"readpath: {rel} has no section starting with {' or '.join(prefixes)}")
    return "".join(out)

def table():
    rows = []
    for doc in sorted((ROOT / "video-types").glob("0*.md")):
        rel = f"video-types/{doc.name}"; n = doc.name[:2]
        quick = sum(len(x) for x in (text("CLAUDE.md"), text("playbook/quick.md"), sections(rel, "工作流", "禁止"),
                                     sections("engines/README.md", ENGINE[n])))
        standard = sum(len(text(f)) for f in STANDARD) + len(text(rel))
        sound = standard + sum(len(text(f)) for f in SOUND)
        studio = sound + sum(len(text(f)) for f in STUDIO)
        rows.append({"type": doc.stem, "quick": quick, "standard": standard, "sound": sound, "studio": studio})
    return rows

def main():
    rows = table()
    if "--json" in sys.argv[1:]:
        print(json.dumps(rows, ensure_ascii=False, indent=1)); return
    w = max(len(r["type"]) for r in rows)
    print("read path · characters an agent reads before it starts (CLAUDE.md's routing; tools/readpath.py)")
    print(f"{'type':<{w}}  {'quick':>8}  {'standard':>9}  {'+sound':>8}  {'studio':>8}")
    for r in rows:
        print(f"{r['type']:<{w}}  {r['quick']:>8,}  {r['standard']:>9,}  {r['sound']:>8,}  {r['studio']:>8,}")

if __name__ == "__main__":
    main()
