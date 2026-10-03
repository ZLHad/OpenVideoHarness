"""bin/vh desk: the review desk, a local page where the reviewer ticks, comments and submits each stop.

  bin/vh desk <project> [--port N]              serve the desk (127.0.0.1; default: the first free port of 8780–8799;
                                                --port 0: any free port). Already serving this project: print its URL.
  bin/vh desk wait <project> [--timeout s]      block until the reviewer submits, print the feedback, exit 0 (3 on
                                                timeout; default 7100 s). An agent runs it in the background after each
                                                stop: its exit is the wake-up call. A submission for the current page that
                                                came in before it was armed, and was never handed over, is printed at once.
  bin/vh desk feedback <project> [--round r] [--json]   print the latest submission (exit 1 when there is none); it then
                                                counts as handed over (out/review/feedback/.consumed)
  bin/vh desk data <project>                    print the data the desk shows, as JSON (what reader.py makes of the files)

The desk reads the same out/review/gate-<n>.json as bin/vh review, plus the project's markdown (the contract is in
tools/desk/README.md). A submission goes to out/review/feedback/<round>-<time>.json and .md, and its text into
REVIEW.md as a dated section. <project> is a folder, or a name under $OVH_PROJECTS / projects/ (date prefix optional).
"""
import argparse, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))


def find(arg):
    from vhdraw import project_dir   # the lookup bin/vh new, storyboard and review use (no pillow needed)
    try:
        return project_dir(arg)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return None


def main(argv):
    sub = argv[0] if argv and argv[0] in ("wait", "feedback", "data") else "serve"
    rest = argv[1:] if sub != "serve" else argv
    ap = argparse.ArgumentParser(prog="bin/vh desk" + ("" if sub == "serve" else " " + sub),
                                 description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project folder, or its name under projects/")
    if sub == "serve":
        ap.add_argument("--port", type=int, help="port on 127.0.0.1 (default: the first free of 8780–8799; 0: any free)")
    elif sub == "wait":
        ap.add_argument("--timeout", type=float, default=7100, help="seconds to wait (default 7100, under Claude Code's 2 h)")
    elif sub == "feedback":
        ap.add_argument("--round", help="only this gate page (1, 2b, E3 …)")
        ap.add_argument("--json", action="store_true", help="print the JSON record instead of the text")
    a = ap.parse_args(rest)
    project = find(a.project)
    if not project:
        return 2
    if sub == "serve":
        import server
        return server.serve(project, a.port)
    import feedback as F
    if sub == "wait":
        return F.wait(project, a.timeout)
    if sub == "feedback":
        path, rec = F.latest(project, a.round)
        if not path:
            print(f"no feedback{' for round ' + a.round if a.round else ''} in {project}/out/review/feedback/", file=sys.stderr)
            return 1
        if a.json:
            print(json.dumps(rec, ensure_ascii=False, indent=1))
        else:
            F.show(path, rec)
        F.mark_consumed(project, [path])   # handed over: a later bin/vh desk wait doesn't print it again
        return 0
    import reader
    print(json.dumps(reader.read_project(project), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
