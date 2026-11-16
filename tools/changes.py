"""The change notes: one file a change in changes/, gathered into CHANGELOG.md when a version is released (stdlib only).

usage: python3 tools/changes.py show [--titles]     what changed since the last release, newest first: the notes in
                                                    changes/, then the entries still under CHANGELOG.md's ## Unreleased
       python3 tools/changes.py show vX.Y.Z         that release's section of CHANGELOG.md (for gh release --notes-file)
       python3 tools/changes.py check               each note's name and shape (tools/ci.sh runs it)
       python3 tools/changes.py release vX.Y.Z [--date YYYY-MM-DD] [--dry-run]
                                                    CHANGELOG.md gets "## vX.Y.Z — <date>" with every note and every
                                                    Unreleased entry; the notes are deleted; CITATION.cff takes the
                                                    version and the date

A note is changes/<name>.md, <name> in lower-case letters, digits and hyphens. It holds one entry, written as a
CHANGELOG entry is: the first line the bold title (**…**), then its lines (- Why: …). changes/README.md tells someone
browsing the folder what it is for, and is not a note. Two PRs that each add a note never touch the same file, so they
land one after the other without a conflict; tools/land.py takes a PR's squash message from the note it adds.
CHANGELOG.md's ## Unreleased is the older way, kept while PRs written before changes/ land: show and release take its
entries too, after the notes (they are older).
A note's age is the commit that added it (on main: the PR's squash); a note not committed yet is the newest.
Exit: 0 done · 1 a note is malformed; release found nothing to release, or the version is there already; show found
no such release · 2 usage.
"""
import argparse, datetime, os, re, signal, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "changes"
LOG = ROOT / "CHANGELOG.md"
CITATION = ROOT / "CITATION.cff"
NAME = re.compile(r"^[a-z0-9][a-z0-9-]*\.md$")
TITLE = re.compile(r"^\*\*(.+?)\*\*\s*$")
RELEASE = re.compile(r"^## (v\d+\.\d+\.\d+)\b.*$", re.M)
POINTER = ("What changed since the last release is in `changes/`, one file a change; "
           "`python3 tools/changes.py show` prints it.")


def note_files():
    return sorted(p for p in NOTES.glob("*.md") if p.name != "README.md") if NOTES.is_dir() else []


def added_at():
    """{path under the repo: how far down git log the commit that last added it is (0 the newest)}; {} without git. The
    log's order, not the commits' times: two squashes in the same second still come child first."""
    p = subprocess.run(["git", "-C", str(ROOT), "log", "--diff-filter=A", "--no-renames", "--format=%x00",
                        "--name-only", "--", "changes/"], capture_output=True, text=True)
    out, n = {}, -1
    for line in p.stdout.splitlines() if p.returncode == 0 else []:
        if line.startswith("\0"):
            n += 1
        elif line.strip() and n >= 0:
            out.setdefault(line.strip(), n)   # newest first: the first add seen is the latest
    return out


def ordered(files):
    """Newest first: a note not committed yet, then by the commit that added it; the name breaks a tie."""
    at = added_at()
    rel = lambda p: p.relative_to(ROOT).as_posix()   # noqa: E731
    return sorted(files, key=lambda p: (at.get(rel(p), -1), p.name))


def parse(text):
    """(title, body) of one entry, body without the blank lines around it; problems in a list."""
    lines = text.strip("\n").splitlines()
    problems = []
    if not lines or not TITLE.match(lines[0]):
        problems.append("its first line is not a bold title (**…**)")
    if len(lines) < 2 or not "".join(lines[1:]).strip():
        problems.append("it has a title and nothing under it (say what changed and why, as a CHANGELOG entry does)")
    if any(TITLE.match(x) for x in lines[1:]):
        problems.append("it holds two entries (a second bold line at the start of a line): one note a change")
    if any(x.startswith("#") for x in lines):
        problems.append("it has a heading (#): release writes the heading")
    title = TITLE.match(lines[0]).group(1) if lines and TITLE.match(lines[0]) else ""
    return title, "\n".join(lines[1:]).strip("\n"), problems


def unreleased():
    """CHANGELOG.md's ## Unreleased entries, in the file's order, each its text from the title line on."""
    text = LOG.read_text(encoding="utf-8") if LOG.is_file() else ""
    m = re.search(r"^## Unreleased[ \t]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return []
    entries, cur = [], None
    for line in m.group(1).splitlines():
        if TITLE.match(line):
            cur = [line]
            entries.append(cur)
        elif cur is not None:
            cur.append(line)
    return ["\n".join(e).strip("\n") for e in entries]


def pending():
    """[(where, text)], newest first: the notes, then the Unreleased entries."""
    out = [(p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8").strip("\n")) for p in ordered(note_files())]
    return out + [("CHANGELOG.md", e) for e in unreleased()]


def cmd_show(version, titles):
    if version:
        text = LOG.read_text(encoding="utf-8")
        m = re.search(rf"^## {re.escape(version)}\b[^\n]*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
        if not m:
            print(f"changes: no ## {version} in CHANGELOG.md", file=sys.stderr)
            return 1
        print(m.group(1).strip("\n"))
        return 0
    items = pending()
    if not items:
        last = RELEASE.search(LOG.read_text(encoding="utf-8")) if LOG.is_file() else None
        print("nothing has changed since the last release" + (f" ({last.group(1)})" if last else ""))
        return 0
    if titles:
        for where, text in items:
            first = text.splitlines()[0]
            print(f"- {TITLE.match(first).group(1) if TITLE.match(first) else first}  ({where})")
    else:
        print("\n\n".join(text for _, text in items))
    return 0


def cmd_check():
    problems = []
    for p in sorted(NOTES.iterdir()) if NOTES.is_dir() else []:
        if p.name == "README.md":
            continue
        if p.is_dir() or not NAME.match(p.name):
            problems.append(f"changes/{p.name}: a note is changes/<name>.md, the name in lower-case letters, digits and hyphens")
            continue
        problems += [f"changes/{p.name}: {x}" for x in parse(p.read_text(encoding="utf-8"))[2]]
    if LOG.is_file() and len(re.findall(r"^## Unreleased[ \t]*$", LOG.read_text(encoding="utf-8"), re.M)) > 1:
        problems.append("CHANGELOG.md: more than one ## Unreleased")
    if problems:
        print("\n".join(problems))
        return 1
    n, u = len(note_files()), len(unreleased())
    print(f"{n} note(s) in changes/, each one entry with a title and its lines" + (f"; {u} entry(ies) under CHANGELOG.md's ## Unreleased" if u else ""))
    return 0


def cmd_release(version, date, dry):
    if not re.match(r"^v\d+\.\d+\.\d+$", version):
        print(f"changes: {version} is not a version (vX.Y.Z)", file=sys.stderr)
        return 2
    try:
        datetime.date.fromisoformat(date)
    except ValueError:
        print(f"changes: --date {date} is not a day (YYYY-MM-DD)", file=sys.stderr)
        return 2
    text = LOG.read_text(encoding="utf-8")
    if re.search(rf"^## {re.escape(version)}\b", text, re.M):
        print(f"changes: CHANGELOG.md has ## {version} already", file=sys.stderr)
        return 1
    files = ordered(note_files())
    bad = [f"{p.relative_to(ROOT).as_posix()}: {x}" for p in files for x in parse(p.read_text(encoding="utf-8"))[2]]
    if bad:
        print("changes: not released, a note is malformed:\n  " + "\n  ".join(bad), file=sys.stderr)
        return 1
    notes, old = [p.read_text(encoding="utf-8").strip("\n") for p in files], unreleased()
    if not notes and not old:
        print("changes: nothing to release: no note in changes/ and nothing under ## Unreleased", file=sys.stderr)
        return 1
    section = f"## {version} — {date}\n\n" + "\n\n".join(notes + old) + "\n"
    body = re.sub(r"^## Unreleased[ \t]*\n.*?(?=^## |\Z)", "", text, count=1, flags=re.M | re.S)
    first = re.search(r"^## ", body, re.M)
    head, rest = (body[:first.start()], body[first.start():]) if first else (body, "")
    head = head.rstrip("\n")
    if POINTER not in head:
        head += "\n\n" + POINTER
    new = head + "\n\n" + section + ("\n" + rest if rest else "")
    cff = CITATION.read_text(encoding="utf-8") if CITATION.is_file() else None
    if cff is not None:
        cff = re.sub(r'(?m)^version: .*$', f'version: "{version[1:]}"', cff, count=1)
        cff = re.sub(r'(?m)^date-released: .*$', f'date-released: "{date}"', cff, count=1)
    say = (f"CHANGELOG.md: ## {version} — {date}, {len(notes) + len(old)} entries ({len(notes)} note(s) from changes/, "
           f"{len(old)} from ## Unreleased)" + ("; CITATION.cff: its version and date-released" if cff is not None else ""))
    if dry:
        print("dry run, nothing written: " + say + (f"; would delete {len(files)} note(s)" if files else "") + "\n")
        print(section, end="")
        return 0
    LOG.write_text(new, encoding="utf-8")
    if cff is not None:
        CITATION.write_text(cff, encoding="utf-8")
    for p in files:
        os.remove(p)
    print(say + (f"; deleted {len(files)} note(s)" if files else ""))
    print("next: commit these in the release PR (CONTRIBUTING.md, 版本 tag 和 Release)")
    return 0


def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)   # show | head: stop quietly
    ap = argparse.ArgumentParser(prog="tools/changes.py", description="The change notes in changes/ and CHANGELOG.md.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("show", help="what changed since the last release, or one release's section")
    s.add_argument("version", nargs="?")
    s.add_argument("--titles", action="store_true", help="only each entry's title and where it is")
    sub.add_parser("check", help="each note's name and shape")
    r = sub.add_parser("release", help="gather the notes into CHANGELOG.md under a new version")
    r.add_argument("version")
    r.add_argument("--date", default=datetime.date.today().isoformat())
    r.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.cmd == "show":
        sys.exit(cmd_show(a.version, a.titles))
    if a.cmd == "check":
        sys.exit(cmd_check())
    sys.exit(cmd_release(a.version, a.date, a.dry_run))


if __name__ == "__main__":
    main()
