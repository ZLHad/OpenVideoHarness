"""bin/vh desk: the console and review desk, a local page where the person looks at every film, and at a stop picks,
comments and submits.

  bin/vh desk [--root DIR …] [--port N] [--idle s]   the console: every project bin/vh projects finds ($OVH_PROJECTS,
                                                <repo>/projects, each --root), a card a film, waiting ones first; a project's
                                                page (its stops, its film with the ruler, what to decide, its checks and
                                                documents); a stop's gate view, where the options are cards to pick and
                                                one button submits. Already running with these roots: print its URL
  bin/vh desk <project> [--root DIR …] [--port N] [--idle s] [--only]   the same page, opened on that project, every
                                                other film a click away in the space. Default port: the first free of
                                                8780–8799 (--port 0: any free port). Already serving this project: print
                                                its URL. --idle s: stop after s seconds without a request. --only: this
                                                project and nothing else under the roots (bin/vh gate starts the desk of a
                                                stop so, with --idle 43200: 12 h)
  bin/vh desk wait <project> [--timeout s]      block until the reviewer submits, print the feedback, exit 0 (3 on
                                                timeout; default 7100 s). An agent runs it in the background after each
                                                stop: its exit is the wake-up call. A submission for the current page that
                                                came in before it was armed, and was never handed over, is printed at once.
  bin/vh desk feedback <project> [--round r] [--json]   print the latest submission (exit 1 when there is none); it then
                                                counts as handed over (out/review/feedback/.consumed)
  bin/vh desk data <project>                    print the data the desk shows, as JSON (what reader.py makes of the files)
  bin/vh desk link [<project>] [--root DIR …] [--force]   a new link: the desk serving this project (or the console of
                                                these roots) stops and starts again in the background, alike, on the same
                                                port, and this prints its address with a new one-time key; every token of
                                                the old link is void. For a link used up, lost, or opened by someone else
                                                (the page says so). An agent mid-turn in its column: refused (--force stops it)
  bin/vh desk agents [--json]                   the agents the console's column can talk to (Claude Code, Codex, DeepSeek
                                                Harness): installed or not, the pinned adapter version, where they live
  bin/vh desk agents install <claude|codex|dsh>   install that agent's ACP adapter, pinned, outside the repo
                                                ($OVH_AGENTS_DIR, else $XDG_CACHE_HOME/ovh/agents); it uses your own login

The desk reads the same out/review/gate-<n>.json as bin/vh review, and shows a stop with the same markup (tools/review.py,
tools/desk/static/ui.css and ui.js), plus the project's markdown and bin/vh status (the contract is in tools/desk/README.md). A submission goes to out/review/feedback/<round>-<time>.json and .md, and its text into
REVIEW.md as a dated section. <project> is a folder, or a name under $OVH_PROJECTS / projects/ (date prefix optional).
"""
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import jsonerr   # noqa: E402


def find(arg):
    from vhdraw import project_dir   # the lookup bin/vh new, storyboard and review use (no pillow needed)
    try:
        return project_dir(arg)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return None


def main(argv):
    if argv and argv[0] == "agents":
        return agents_cmd(argv[1:])
    if argv and argv[0] == "link":
        return link_cmd(argv[1:])
    sub = argv[0] if argv and argv[0] in ("wait", "feedback", "data") else "serve"
    rest = argv[1:] if sub != "serve" else argv
    ap = argparse.ArgumentParser(prog="bin/vh desk" + ("" if sub == "serve" else " " + sub),
                                 description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?" if sub == "serve" else None, help="project folder, or its name under projects/"
                    + ("; left out: the console, every project" if sub == "serve" else ""))
    if sub == "serve":
        ap.add_argument("--root", action="append", default=[], metavar="DIR",
                        help="another folder to find projects in, as bin/vh projects --root (repeat it for more)")
        ap.add_argument("--port", type=int, help="port on 127.0.0.1 (default: the first free of 8780–8799; 0: any free)")
        ap.add_argument("--idle", type=float, help="stop after this many seconds without a request (an open desk page asks every "
                                                   "few seconds); default: never. bin/vh gate starts it with 43200 (12 h)")
        ap.add_argument("--key-stdin", action="store_true", help="read the launch key from the first line of stdin (bin/vh gate "
                                                                 "prints it in its message; the address the desk prints then has none)")
        ap.add_argument("--only", action="store_true", help="serve this project and nothing else under the roots (bin/vh gate's "
                                                            "desk); without it the space has every film")
    elif sub == "wait":
        ap.add_argument("--timeout", type=float, default=7100, help="seconds to wait (default 7100, under Claude Code's 2 h)")
    elif sub == "feedback":
        ap.add_argument("--round", help="only this gate page (1, 2b, E3 …)")
        ap.add_argument("--json", action="store_true", help="print the JSON record instead of the text")
    else:
        jsonerr.force()   # bin/vh desk data speaks JSON: a failure too
        ap.add_argument("--json", action="store_true", help="it always is (a client may say so)")
    a = ap.parse_args(rest)
    if sub == "serve":
        for r in a.root:   # bin/vh projects' rule: a --root is a folder that is there
            if not r.strip() or not Path(r).expanduser().is_dir():
                print(f"desk: --root {r!r}: no such folder", file=sys.stderr)
                return 2
        project = find(a.project) if a.project else None
        if a.project and not project:
            jsonerr.mark("no_project")
            return 2
        if a.only and not project:
            print("desk: --only needs a project (it serves that project and nothing else)", file=sys.stderr)
            return 2
        import server
        key = sys.stdin.readline().strip() if a.key_stdin else None
        if a.key_stdin and not re.fullmatch(r"[A-Za-z0-9_-]{16,64}", key or ""):
            print("desk: --key-stdin: no key on stdin", file=sys.stderr)
            return 2
        return server.serve(project, a.port, a.idle if a.idle and a.idle > 0 else None, [str(Path(r).expanduser()) for r in a.root], a.only, key)
    project = find(a.project)
    if not project:
        jsonerr.mark("no_project")
        return 2
    import feedback as F
    if sub == "wait":
        return F.wait(project, a.timeout)
    if sub == "feedback":
        path, rec = F.latest(project, a.round)
        if not path:
            return jsonerr.fail("not_found", f"no feedback{' for round ' + a.round if a.round else ''} in {project}/out/review/feedback/", rc=1)
        if a.json:
            print(json.dumps(rec, ensure_ascii=False, indent=1))
        else:
            F.show(path, rec)
        F.mark_consumed(project, [path])   # handed over: a later bin/vh desk wait doesn't print it again
        return 0
    import reader
    print(json.dumps(reader.read_project(project), ensure_ascii=False, indent=1))
    return 0


def link_cmd(argv):
    """bin/vh desk link [<project>] [--root DIR …] [--force] [--json]"""
    ap = argparse.ArgumentParser(prog="bin/vh desk link", description="a new link for the desk serving this project (or the console): it starts again with a new one-time key")
    ap.add_argument("project", nargs="?", help="project folder, or its name under projects/; left out: the console")
    ap.add_argument("--root", action="append", default=[], metavar="DIR", help="the console's folders, as it was started with")
    ap.add_argument("--force", action="store_true", help="also when an agent in its column is mid-turn (that turn stops)")
    ap.add_argument("--json", action="store_true", help="{url} on stdout")
    a = ap.parse_args(argv)
    for r in a.root:
        if not Path(r).expanduser().is_dir():
            print(f"desk link: --root {r!r}: no such folder", file=sys.stderr)
            return 2
    project = find(a.project) if a.project else None
    if a.project and not project:
        jsonerr.mark("no_project")
        return 2
    import launch, server
    url, why = launch.relink(project, [str(Path(r).expanduser()) for r in a.root], a.force)
    if not url:
        print(f"desk link: {why}", file=sys.stderr)
        return 1
    base, _, q = url.partition("?")
    from urllib.parse import quote
    full = f"{base}?{q}" + (f"#/p/{quote(server.keyify(project.name, project), safe='')}" if project else "")
    if a.json:
        print(json.dumps({"version": 1, "url": full}))
    else:
        print(f"desk: {full}\n  open it in the browser you review in: the link works once, and the one before it is void", flush=True)
    return 0


def agents_cmd(argv):
    """bin/vh desk agents [--json] · bin/vh desk agents install <kind>"""
    import agents as A
    ap = argparse.ArgumentParser(prog="bin/vh desk agents", description="the agents the console's column can talk to, and installing one")
    ap.add_argument("what", nargs="?", choices=["list", "install"], default="list")
    ap.add_argument("kind", nargs="?", choices=list(A.ADAPTERS))
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.what == "install":
        if not a.kind:
            print("usage: bin/vh desk agents install <claude|codex|dsh>", file=sys.stderr)
            return 2
        return A.install(a.kind)
    rows = A.catalog()
    if a.json:
        print(json.dumps({"version": 1, "home": str(A.home()), "agents": rows}, ensure_ascii=False, indent=1))
        return 0
    print(f"agents for the console (in {A.home()}):")
    for r in rows:
        state = (f"installed {r['version']}" + (f" (pinned {r['pinned']}: reinstall)" if r["outdated"] else "")) if r["installed"] else f"not installed ({r['size']}): {r['install']}"
        print(f"  {r['label']:<18} {state}")
    return 0


if __name__ == "__main__":
    import activity   # tools/activity.py: bin/vh exec's into this, so this process writes the run's end
    sys.exit(activity.exiting(lambda: jsonerr.guard(lambda: main(sys.argv[1:]))))
