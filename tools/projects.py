"""bin/vh projects: every project on this machine and where each stands, from the files they already have. Stdlib only;
no browser, no ffprobe. Nothing is written, unless --assign asks.

usage: bin/vh projects [--root DIR …] [--assign] [--json]

Where it looks: $OVH_PROJECTS, <repo>/projects and each --root (the first two only when they are there; a --root that is
not a folder is a usage error). A project is a folder holding BRIEF.md, at most DEPTH folders below its root; out/,
node_modules, a project's assets/ and audio/, hidden folders and the like are not gone into. The same folder found twice
(a link, two roots) is one row.
  --assign  give each project without an id one: .ovh/project.json (tools/identity.py). bin/vh new writes it for a new
            project; an older one has none (id null) until this. Moving a folder keeps its id.
  --json    {"version": 1, "tool", "roots": [{"path", "from", "exists"}], "count", "truncated" (more than MAX_DIRS folders
            looked at: a --root too wide), "seconds", "assigned": [path], "projects": [row]}.
A row: id (null until assigned), name (the folder's, with what lies between it and its root: old/docs), title, path, type,
effort, state (below), station ({id, name} of the stop it is at, or null), waiting_on, next_step (both as bin/vh status
--json has them), running (the commands running now), last_activity ({t, at, cmd, run, state, exit}, or null), film
({path, size, mtime, version, check, stale} of the current film, or null), same_id_as (other paths with this id: a folder
copied whole), error (null, or why this project could not be read: its other fields are then null, and the list goes on),
assign_error (with --assign, when its id could not be written). The newest activity first.
state: paused · delivered · waiting_person · waiting_agent · in_progress · no_record (no REVIEW.md: made before the
templates had one) · not_started; the first of them, in this order, that its stops show (tools/desk/README.md).
It takes status's own read of each project (tools/status.py's collect), without the asset ledger, the cast and the
research, which a list does not show: a few milliseconds a project.
Exit: 0, also when a project cannot be read (its row says why) · 2 usage.
"""
import argparse, json, os, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import identity   # noqa: E402

DEPTH = 4         # folders below a root
MAX_DIRS = 20000  # folders looked at, per run: a --root too wide says so and stops there
NOT_IN = {"out", "node_modules", "renders", "media", "assets", "audio", "frames", "dist", "build", "target", "__pycache__", "venv", "site-packages"}
STATE_ORDER = ("waiting_person", "waiting_agent", "in_progress")
MARK = {"paused": "‖", "delivered": "✓", "waiting_person": "●", "waiting_agent": "◆", "in_progress": "…", "no_record": "○", "not_started": "·", "error": "✗"}


def roots_of(given):
    """[{path, from, exists}], each folder once, in the order they are looked at; a --root that is not a folder: ValueError."""
    out, seen = [], set()

    def add(p, src):
        p = Path(p).expanduser()
        real = os.path.realpath(p)
        if real not in seen:
            seen.add(real)
            out.append({"path": str(p), "from": src, "exists": p.is_dir()})
    if os.environ.get("OVH_PROJECTS"):
        add(os.environ["OVH_PROJECTS"], "OVH_PROJECTS")
    add(ROOT / "projects", "repo")
    for r in given:
        if not Path(r).expanduser().is_dir():
            raise ValueError(f"--root {r}: no such folder")
        add(r, "--root")
    return out


def find(roots):
    """([(project folder, the name it goes by)], whether the walk stopped at MAX_DIRS). Each folder once, links followed only one
    step (a link to a project counts; nothing is walked through a link)."""
    found, seen, looked = [], set(), 0

    def take(d, base):
        real = os.path.realpath(d)
        if real in seen:
            return
        seen.add(real)
        rel = Path(d).relative_to(base).as_posix()
        found.append((Path(d), Path(d).name if rel == "." else rel))
    for r in roots:
        if not r["exists"]:
            continue
        base = r["path"]
        for d, dirs, files in os.walk(base):
            looked += 1
            if looked > MAX_DIRS:
                return found, True
            if "BRIEF.md" in files:
                take(d, base)
            depth = 0 if d == base else len(Path(d).relative_to(base).parts)
            keep = []
            for x in sorted(dirs):
                q = os.path.join(d, x)
                if x.startswith(".") or x in NOT_IN or depth >= DEPTH:
                    continue
                if os.path.islink(q):
                    if os.path.isfile(os.path.join(q, "BRIEF.md")):
                        take(q, base)
                else:
                    keep.append(x)
            dirs[:] = keep
    return found, False


def overall(st):
    """A project's state in one word, from its stops (bin/vh status), and the stop it is at."""
    stops = st["stations"]
    at = next((s for s in stops if s["state"] == "in_progress"), None)
    for word in STATE_ORDER:
        at = next((s for s in stops if s["state"] == word), None)
        if at:
            break
    if st["paused"]:
        return "paused", at
    if at:
        return at["state"], at
    if stops and stops[-1]["state"] == "done":
        return "delivered", stops[-1]
    if any(s["state"] == "no_record" for s in stops):
        return "no_record", None
    return "not_started", None


def last_activity(st):
    """The latest of the runs bin/vh status lists (its running, listening and recent), by when it ended or else began."""
    a = st.get("activity") or {}
    runs = [r for k in ("running", "listening", "recent") for r in a.get(k) or []]
    if not runs:
        return None
    r = max(runs, key=lambda x: x.get("end") or x.get("start") or 0)
    t = r.get("end") or r.get("start")
    return {"t": t, "at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t)) if t else None, "cmd": r.get("cmd"), "run": r.get("run"),
            "state": r.get("state"), "exit": r.get("exit")}


def film_of(project, st, P):
    """The current film (tools/proxy.py's current_film) and what status has of it."""
    film = P.current_film(project)
    if film is None:
        return None
    rel = P.rel(project, film)
    seen = next((r for r in st.get("renders") or [] if r["path"] == rel), None)
    if seen:
        c = seen.get("check") or {}
        return {"path": rel, "size": seen["size"], "mtime": seen["mtime"], "version": seen.get("version"), "check": c.get("verdict"), "stale": c.get("stale")}
    s = film.stat()
    return {"path": rel, "size": s.st_size, "mtime": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(s.st_mtime)), "version": None, "check": None, "stale": None}


def row(project, name, S, P, assign):
    """One project's row. Whatever goes wrong reading it stays in this row (error)."""
    r = {"id": identity.id_of(project), "name": name, "title": None, "path": str(project), "type": None, "effort": None, "state": None, "station": None, "waiting_on": None,
         "next_step": None, "running": [], "last_activity": None, "film": None, "same_id_as": [], "error": None}
    if assign and r["id"] is None:
        try:
            r["id"], r["assigned"] = identity.ensure(project)[0]["id"], True
        except OSError as e:
            r["assign_error"] = f"{identity.path(project)}: {e.strerror or e}"
    try:
        st = S.collect(project, light=True)
        state, at = overall(st)
        r.update(title=st["project"]["title"], type=st["project"]["type"], effort=st["project"]["effort"], state=state,
                 station={"id": at["id"], "name": at["name"]} if at else None, waiting_on=st["waiting_on"], next_step=st["next_step"],
                 running=[x["cmd"] for x in st["activity"]["running"]], last_activity=last_activity(st), film=film_of(project, st, P))
    except (Exception, SystemExit) as e:   # one project's trouble is one row
        r["error"] = f"{type(e).__name__}: {e}"
    return r


def listing(given=(), assign=False):
    """The record --json prints."""
    t0 = time.time()
    import proxy as P, status as S
    roots = roots_of(given)
    found, truncated = find(roots)
    rows = [row(p, name, S, P, assign) for p, name in found]
    by_id = {}
    for r in rows:
        if r["id"]:
            by_id.setdefault(r["id"], []).append(r)
    for same in by_id.values():
        for r in same:
            r["same_id_as"] = [x["path"] for x in same if x is not r]
    rows.sort(key=lambda r: (-((r["last_activity"] or {}).get("t") or 0), r["name"]))
    return {"version": 1, "tool": "bin/vh projects", "roots": roots, "count": len(rows), "truncated": truncated, "seconds": round(time.time() - t0, 3),
            "assigned": [r["path"] for r in rows if r.get("assigned")], "projects": rows}


def show(rec):
    print(f"{rec['count']} project{'s' * (rec['count'] != 1)} · " + " · ".join(r["path"] + ("" if r["exists"] else " (not there)") for r in rec["roots"]) + f" · {rec['seconds']:.2f} s")
    if rec["truncated"]:
        print(f"! stopped after {MAX_DIRS} folders: a --root that wide takes a narrower one")
    w = max((len(r["name"]) for r in rec["projects"]), default=0)
    for r in rec["projects"]:
        if r["error"]:
            print(f"{MARK['error']} {r['name']:<{w}}  could not be read: {r['error']}")
            continue
        do = (r["next_step"] or {}).get("do") or ""
        run = f"{', '.join(r['running'])} running · " if r["running"] else ""
        print(f"{MARK[r['state']]} {r['name']:<{w}}  {r['type'] or '?'} · {r['effort']} · {r['state']}" + (f" ({r['station']['name']})" if r["station"] else "") + f" · {run}{do[:90]}" + ("…" if len(do) > 90 else ""))
        for k in ("assign_error",):
            if r.get(k):
                print(f"    ! {r[k]}")
        if r["same_id_as"]:
            print(f"    ! the same id as {', '.join(r['same_id_as'])}: a folder copied whole (tools/identity.py)")
    if rec["assigned"]:
        print(f"assigned an id to {len(rec['assigned'])}")


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh projects", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("--root", action="append", default=[], metavar="DIR", help="another folder to look in (repeat it for more)")
    ap.add_argument("--assign", action="store_true", help="give each project without an id one (.ovh/project.json)")
    ap.add_argument("--json", action="store_true", help="the record, as JSON (version 1)")
    a = ap.parse_args(argv)
    try:
        rec = listing(a.root, a.assign)
    except ValueError as e:
        print(f"projects: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(rec, ensure_ascii=False, indent=1))
    else:
        show(rec)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
