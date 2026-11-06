"""Are the captions older than the timeline they were timed from? (stdlib only)

bin/vh captions records the timeline it read and its sha256 in audio/captions.args.json; captions.json keeps its shape, since
pages read it. bin/vh check and bin/vh artifacts list compare that hash with the file now, as bin/vh mux does for a mix
(tools/audio/mixstate.py) and bin/vh cues for its cues.

usage (bin/vh check runs it): python3 tools/audio/capstate.py <project> [--json f]
prints a line when the captions are out of date, nothing otherwise; --json f: {"state", "why", "timeline"}, for its record.
state(project) → ("fresh" | "stale" | "not_checked", why), or None when the project has no captions. Exit: 0 · 2 usage.
"""
import hashlib, json, os, sys
from pathlib import Path

ARGS = Path("audio") / "captions.args.json"
CAPTIONS = Path("audio") / "captions.json"


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def record(project, timeline):
    """What audio/captions.args.json keeps of the timeline: its path from the project and its sha256."""
    return {"timeline": Path(os.path.relpath(timeline, project)).as_posix(), "timeline_sha256": digest(timeline)}


def state(project):
    """The captions against the timeline on record: ("fresh" | "stale" | "not_checked", why), or None with no captions."""
    project = Path(project)
    if not (project / CAPTIONS).is_file():
        return None
    try:
        made = json.loads((project / ARGS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        made = None
    tl = made.get("timeline") if isinstance(made, dict) else None
    sha = made.get("timeline_sha256") if isinstance(made, dict) else None
    if not isinstance(tl, str) or not isinstance(sha, str):
        return "not_checked", "made before bin/vh captions recorded its timeline: nothing says which take they are from"
    f = project / tl
    if not f.is_file():
        return "stale", f"{tl}, the timeline they were timed from, is gone: bin/vh captions makes them from the timeline there is now"
    try:
        now = digest(f)
    except OSError as e:   # there, and not readable
        return "not_checked", f"{tl} cannot be read ({e.strerror or type(e).__name__}): nothing says whether the captions are from it"
    if now != sha:
        return "stale", f"{tl} changed since the captions were made from it: bin/vh captions makes them again"
    return "fresh", f"made from {tl} as it is"


def main(argv):
    args = list(argv)
    out = None
    if "--json" in args:
        i = args.index("--json")
        if i + 1 >= len(args):
            print("capstate: --json needs a file", file=sys.stderr)
            return 2
        out = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or not Path(args[0]).is_dir():
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    got = state(args[0])
    if got and out:
        made = {}
        try:
            made = json.loads((Path(args[0]) / ARGS).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
        Path(out).write_text(json.dumps({"state": got[0], "why": got[1], "timeline": made.get("timeline") if isinstance(made, dict) else None}, ensure_ascii=False), encoding="utf-8")
    if got and got[0] == "stale":
        print(f"captions: {got[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
