"""bin/vh cancel: stop what runs in a project, the way each tool stops best, and say so in its log. Stdlib only.

usage: bin/vh cancel <project> [run] [--timeout S] [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).
[run] is a run's id as bin/vh activity --json has it, or the first or last part of one that fits only it. Without it: every
run that is running, but the ones that only wait for a person (a desk, gate --wait: those by name).

Only what the log started: a run with no end line whose process is still that command. The pid in its start line must be
alive and not a zombie, must have started when the log says it did (within a minute before, 3 s after: a reused pid started
later than that), and its command line must be bin/vh or one of tools/, with the command's name in it. Anything else is not
touched: its state says so (not_that_process), and a note in the log has the run read as gone from then on.

How it stops one:
  a tool bin/vh exec'd into (render, patch, the page tools, desk, gate: the pid is the tool): SIGINT, to it alone: it closes its
  own browsers and encoders and writes the end line itself; SIGTERM after --timeout seconds (15), 5 s more.
  a tool bin/vh waits on (the pid is bash; tts, deliver, proxy, thumbs, mix …): SIGINT to the process and everything under it,
  as Ctrl-C reaches a foreground command, and bin/vh writes the end line; SIGTERM to them after 3 s (a command started with
  & from a script has SIGINT ignored, and macOS's ps cannot say so), 5 s more (bash then goes at once, with no end line).
What has no end line once its process is gone gets one from here. A mark in .ovh/cancel/<run>, there only while this runs, tells
bin/vh and the tools that wrote the end line that it is a cancel: "cancelled": true, exit 130 or 143, not gone.
What a tool kept for a resume, it says in a note ("kept": render's chunks, tts's lines); no such note: nothing is kept.

--json: {"version": 1, "tool", "project", "runs": [{"run", "cmd", "pid", "state", "signal", "exit", "seconds", "kept", "why"}],
"skipped": [{"run", "cmd", "why"}], "cancelled": n}. state: cancelled · finished (it ended on its own first) · not_running (a
run named that is over) · not_that_process · still_running (it outlived both signals).
Exit: 0, also with nothing running · 1 a run outlived both signals, or a run named is not that process · 2 usage, no project, no such run.
"""
import argparse, json, os, re, signal, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import activity, jsonerr   # noqa: E402,E401

LISTENING = ("desk", "gate")   # someone waiting, not work being done (bin/vh status)
OURS = re.compile(r"(^|[\s/])bin/vh(\s|$)|/tools/[\w./-]+\.(py|mjs)(\s|$)")
BASH_VH = re.compile(r"^\S*\bbash\s.*\bbin/vh(\s|$)|^\S*/bin/vh(\s|$)|^bin/vh(\s|$)")
EARLY, LATE = 60, 3    # seconds a process may have started before and after its run's time
GRACE = 0.4            # seconds its end line may come after its process has gone
AFTER_TERM = 5
INT_UNDER_BASH = 3


def ps(*args):
    """ps's lines, or None when ps cannot be run."""
    try:
        r = subprocess.run(["ps", *args], capture_output=True, text=True, env=dict(os.environ, LC_ALL="C"), timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.splitlines() if r.returncode == 0 else []


def process(pid):
    """(stat, start time, command line) of a live process; None when there is none or it is a zombie."""
    rows = ps("-ww", "-o", "stat=", "-o", "lstart=", "-o", "command=", "-p", str(pid))
    if not rows:
        return None
    m = re.match(r"\s*(\S+)\s+(\w{3}\s+\w{3}\s+\d+\s+[\d:]+\s+\d{4})\s+(.*)$", rows[0])
    if not m or m.group(1).startswith("Z"):
        return None
    try:
        return m.group(1), time.mktime(time.strptime(re.sub(r"\s+", " ", m.group(2)), "%a %b %d %H:%M:%S %Y")), m.group(3)
    except (ValueError, OverflowError):
        return None


def confirmed(run):
    """(is the run's pid still that command?, the process's (stat, start, command) or None, why not)."""
    p = process(run["pid"]) if run.get("pid") else None
    if p is None:
        return False, None, f"pid {run.get('pid')} is gone"
    _, start, cmdline = p
    if not OURS.search(cmdline):
        return False, p, f"pid {run['pid']} is another program now"
    if run.get("cmd") and run["cmd"] not in cmdline:
        return False, p, f"pid {run['pid']} is another bin/vh command now"
    if run.get("start") is None or not run["start"] - EARLY <= start <= run["start"] + LATE:
        return False, p, f"pid {run['pid']} started at another time than this run: a reused pid"
    return True, p, None


def tree(pid):
    """Everything under a process, children first: (pid, start time)."""
    rows = ps("-A", "-o", "pid=", "-o", "ppid=") or []
    kids = {}
    for row in rows:
        a = row.split()
        if len(a) == 2 and a[0].isdigit() and a[1].isdigit():
            kids.setdefault(int(a[1]), []).append(int(a[0]))
    out, todo = [], list(kids.get(pid, []))
    while todo:
        k = todo.pop()
        out.append(k)
        todo += kids.get(k, [])
    return out


def send(pid, sig):
    try:
        os.kill(pid, sig)
        return True
    except OSError:
        return False


def end_of(project, run_id):
    """The run's end line, from the last of the log."""
    for r in reversed(activity.read(project, tail=1 << 18)):
        if r.get("run") == run_id and r["event"] == "end":
            return r
    return None


class Mark:
    """.ovh/cancel/<run>, while this stops it: what bin/vh and the tools read when they write the end line."""

    def __init__(self, project, run_id):
        self.dir = activity.log_path(project).parent / "cancel"
        self.file = self.dir / run_id

    def set(self, code):
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            self.file.write_text(f"{code}\n", encoding="utf-8")
        except OSError:   # what cannot be marked gets its end line from here
            pass

    def done(self):
        try:
            self.file.unlink()
            self.dir.rmdir()
        except OSError:
            pass


def stop(project, run, timeout):
    """Stop one confirmed run. → its row."""
    rid, pid = run["run"], run["pid"]
    row = {"run": rid, "cmd": run.get("cmd"), "pid": pid, "state": None, "signal": None, "exit": None, "seconds": None, "kept": None, "why": None}
    t0 = time.time()
    ok, p, why = confirmed(run)
    if not ok:
        row.update(state="not_that_process", why=why)
        return row
    under_bash = bool(BASH_VH.search(p[2]))
    first_wait = min(timeout, INT_UNDER_BASH) if under_bash else timeout
    seen = set()

    def signal_all(sig):
        ok, here, _ = confirmed(run)
        if not ok:
            return
        kids = tree(pid) if under_bash else []
        seen.update(kids)
        for k in kids:
            send(k, sig)
        send(pid, sig)
    mark = Mark(project, rid)
    code = 130
    mark.set(code)
    try:
        signal_all(signal.SIGINT)
        row["signal"] = "SIGINT"
        gone = wait_gone(run, first_wait)
        if not gone:
            code = 143
            mark.set(code)
            signal_all(signal.SIGTERM)
            row["signal"] = "SIGTERM"
            gone = wait_gone(run, AFTER_TERM)
        if not gone:
            row.update(state="still_running", seconds=round(time.time() - t0, 2),
                       why=f"pid {pid} outlived SIGINT and SIGTERM; nothing stronger was sent: bin/vh activity shows it running, and kill -9 {pid} is yours to send")
            return row
        for k in seen:   # what was under it and has not gone with it (a child of a bash that went at once)
            q = process(k)
            if q and OURS.search(q[2]):
                send(k, signal.SIGTERM)
        deadline = time.time() + GRACE
        end = end_of(project, rid)
        while end is None and time.time() < deadline:
            time.sleep(0.05)
            end = end_of(project, rid)
        if end is None:   # no line of its own (bash at a TERM, a tool that was killed): written here
            now = time.time()
            end = {"event": "end", "run": rid, "t": round(now, 3), "cmd": run.get("cmd") or "", "exit": code, "duration": round(max(0.0, now - (run.get("start") or now)), 3), "cancelled": True}
            activity._write(str(activity.log_path(project)), end)
    finally:
        mark.done()
    row.update(state="cancelled" if end.get("cancelled") else "finished", exit=end.get("exit"), seconds=round(time.time() - t0, 2))
    now = next((r for r in activity.runs(activity.read(project, tail=1 << 18))[0] if r["run"] == rid), None)
    row["kept"] = (now or {}).get("kept")
    return row


def wait_gone(run, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        ok, _, _ = confirmed(run)
        if not ok:
            return True
        time.sleep(0.1)
    return not confirmed(run)[0]


def show(rec, out):
    if not rec["runs"] and not rec["skipped"]:
        print(f"cancel: nothing is running in {Path(rec['project']).name}", file=out)
    for r in rec["runs"]:
        head = f"cancel: {r['cmd']} ({r['run']})"
        if r["state"] == "cancelled":
            print(f"{head}: stopped by {r['signal']}, exit {r['exit']}, in {r['seconds']} s", file=out)
            print(f"  kept for a resume: {r['kept']}" if r["kept"] else "  nothing is kept for a resume", file=out)
        elif r["state"] == "finished":
            print(f"{head}: it ended on its own, exit {r['exit']}", file=out)
        else:
            print(f"{head}: {r['state'].replace('_', ' ')}" + (f": {r['why']}" if r["why"] else ""), file=out)
    for r in rec["skipped"]:
        print(f"cancel: left running: {r['cmd']} ({r['run']}): {r['why']}", file=out)


def find_project(word):
    import gatecheck as G, review as R
    p = Path(word).expanduser()
    project = G.project_of(p) if p.exists() else None
    if project is None:
        project = R.find_project(word)
        if project is None:
            jsonerr.mark("no_project")
            return None
        if not (project / "BRIEF.md").is_file():
            jsonerr.fail("no_project", f"cancel: {project} is not a project (no BRIEF.md)")
            return None
    return project


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh cancel", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("project", help="project folder (or a file inside it), or its name under projects/")
    ap.add_argument("run", nargs="?", help="this run only: its id, or the first or last part of one (bin/vh activity --json)")
    ap.add_argument("--timeout", type=float, default=15, help="seconds a tool has after SIGINT before SIGTERM (default 15; under bash at most 3)")
    ap.add_argument("--json", action="store_true", help="the record, as JSON (version 1)")
    a = ap.parse_intermixed_args(argv)   # (the run after an option: Python before 3.12 takes it only so)
    project = find_project(a.project)
    if project is None:
        return 2
    all_runs = [r for r in activity.runs(activity.read(project))[0] if r["run"] != os.environ.get("OVH_ACTIVITY_RUN")]   # not this command's own
    rows, skipped = [], []
    if a.run:
        hit = [r for r in all_runs if r["run"] == a.run] or [r for r in all_runs if r["run"].startswith(a.run) or r["run"].endswith(a.run)]
        if not hit:
            return jsonerr.fail("not_found", f"cancel: no run {a.run} in {project.name}", "bin/vh activity <project> --json lists the runs")
        if len(hit) > 1:
            return jsonerr.fail("usage", f"cancel: {a.run} fits {len(hit)} runs: {', '.join(r['run'] for r in hit[:5])}")
        run = hit[0]
        if run["state"] != "running":
            rows.append({"run": run["run"], "cmd": run["cmd"], "pid": run["pid"], "state": "not_running", "signal": None, "exit": run["exit"], "seconds": None, "kept": run.get("kept"), "why": f"it is {run['state']}"})
        targets = [run] if run["state"] == "running" else []
        targets += [r for r in all_runs if r["state"] == "running" and r.get("parent") == run["run"]]   # what it started through bin/vh
    else:
        targets = []
        for r in all_runs:
            if r["state"] != "running" or r["cmd"] == "cancel":   # (another cancel at work)
                continue
            if r["cmd"] in LISTENING:
                skipped.append({"run": r["run"], "cmd": r["cmd"], "why": "it waits for a person: name its run to stop it"})
            else:
                targets.append(r)
    for r in targets:
        one = stop(project, r, a.timeout)
        if one["state"] == "not_that_process":
            activity._write(str(activity.log_path(project)), {"event": "note", "run": r["run"], "t": round(time.time(), 3), "cmd": r["cmd"], "gone": True, "summary": f"its process is gone: {one['why']} (bin/vh cancel)"})
        rows.append(one)
    rec = {"version": 1, "tool": "bin/vh cancel", "project": str(project), "runs": rows, "skipped": skipped, "cancelled": sum(1 for r in rows if r["state"] == "cancelled")}
    if a.json:
        print(json.dumps(rec, ensure_ascii=False, indent=1))
    show(rec, sys.stderr if a.json else sys.stdout)
    activity.note(f"{rec['cancelled']} run(s) cancelled" if rec["cancelled"] else "nothing to cancel", [])
    stuck = [r for r in rows if r["state"] == "still_running" or (r["state"] == "not_that_process" and a.run)]
    if stuck:
        jsonerr.report("failed", f"cancel: {stuck[0]['run']}: {stuck[0]['why']}")   # (with --json: the record is out already)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:
        sys.exit(0)
