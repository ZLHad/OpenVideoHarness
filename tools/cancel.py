"""bin/vh cancel: stop what runs in a project, the way each tool stops best, and say so in its log. Stdlib only.

usage: bin/vh cancel <project> [run] [--timeout S] [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).
[run] is a run's id as bin/vh activity --json has it, or the first or last part of one that fits only it. Without it: every
run that is running, but the ones that only wait for a person (a desk, gate --wait: those by name).

Only what the log started: a run with no end line whose process is still that command, in this project. A log is a file anyone can
copy or write, so nothing in it is taken on its word:
  a pid that is gone, or that started at another time than the log says (within a minute before, 3 s after: a reused pid started later
    than that): not_that_process, and a note in the log has the run read as gone from then on;
  a pid of that time whose command line is not bin/vh's with the command's name, or the tool bin/vh exec's into for it (lyria.py under
    music; ./vh is bin/vh), or whose start line does not say its project (an older bin/vh wrote it), or a run id
    that is not bin/vh's kind ([A-Za-z0-9_-]): not_confirmed. Nothing is sent and no line written: it may well be running; a person looks;
  a start line of another folder (this one is a copy, made while it ran, or it has moved): not_that_process. Nothing is sent and no line
    written: it is someone else's run;
  ps that cannot say, at the first look or later (it failed, it was not let): nothing is sent and no line written, it keeps waiting, and it
    ends as still_running.

How it stops one:
  a tool bin/vh exec'd into (render, patch, the page tools, desk, gate: the pid is the tool): SIGINT, to it alone: it closes its
  own browsers and encoders and writes the end line itself; SIGTERM after --timeout seconds (15), 5 s more.
  a tool bin/vh waits on (the pid is bash; tts, deliver, proxy, thumbs, mix …): SIGINT to the process and everything under it,
  as Ctrl-C reaches a foreground command, and bin/vh writes the end line; SIGTERM to them after 3 s (a command started with
  & from a script has SIGINT ignored, and macOS's ps cannot say so), 5 s more (bash then goes at once, with no end line).
What has no end line once its process is gone gets one from here. A mark in .ovh/cancel/<run> tells bin/vh and the tools that write the
end line that it is a cancel: "cancelled": true, exit 130 or 143, not gone. It goes when this has stopped the run, and stays with one
that is still_running: a tool in a step that takes no signal (ffmpeg under spawnSync) stops when the step ends, and its end line then
says cancelled. The next bin/vh cancel takes away a mark whose run is over.
What a tool kept for a resume, it says in a note ("kept": render's chunks, tts's lines); no such note: nothing is kept.

--json: {"version": 1, "tool", "project", "runs": [{"run", "cmd", "pid", "state", "signal", "exit", "seconds", "kept", "why"}],
"skipped": [{"run", "cmd", "why"}], "cancelled": n}. state: cancelled · finished (it ended on its own first) · not_running (a
run named that is over) · not_that_process · not_confirmed · still_running (it outlived both signals, or ps could not say). signal: the last
one sent, null when none was.
Exit: 0, also with nothing running · 1 a run outlived both signals or could not be confirmed, or a run named is not that process · 2 usage, no project, no such run.
"""
import argparse, json, os, re, signal, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import activity, jsonerr   # noqa: E402,E401

LISTENING = ("desk", "gate")   # someone waiting, not work being done (bin/vh status)
RUN_ID = re.compile(r"[A-Za-z0-9_-]+\Z")   # a run's id names a file in .ovh/cancel: bin/vh writes <seconds>-<pid>
OURS = re.compile(r"(^|[\s/])vh(\s|$)|/tools/[\w./-]+\.(py|mjs)(\s|$)")
SHELL = re.compile(r"^\S*\bbash\s|^(\S*/)?vh(\s|$)")   # the pid is a shell: what stops it is what is under it
EXEC = {"music": r"/tools/audio/lyria\.py"}   # bin/vh's exec into a tool not named after its command
EARLY, LATE = 60, 3    # seconds a process may have started before and after its run's time
GRACE = 0.4            # seconds its end line may come after its process has gone
AFTER_TERM = 5
INT_UNDER_BASH = 3
NOT_KNOWN = object()   # ps could not say
THIS, GONE, ELSEWHERE, UNSURE, NO_PS = "this", "gone", "elsewhere", "unsure", "no ps"


def ps(*args):
    """ps's lines, or None when ps cannot be run."""
    try:
        r = subprocess.run(["ps", *args], capture_output=True, text=True, env=dict(os.environ, LC_ALL="C"), timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.splitlines() if r.returncode == 0 else []


def process(pid):
    """(stat, start time, command line) of a live process; None when there is none or it is a zombie; NOT_KNOWN when ps could not say. ps that says
    nothing is no proof: kill(pid, 0) is the kernel's word that there is no such process (a pid of 0 or less is a group to kill(2): none is ours)."""
    if not isinstance(pid, int) or pid <= 0:
        return None
    rows = ps("-ww", "-o", "stat=", "-o", "lstart=", "-o", "command=", "-p", str(pid))
    if rows:
        m = re.match(r"\s*(\S+)\s+(\w{3}\s+\w{3}\s+\d+\s+[\d:]+\s+\d{4})\s+(.*)$", rows[0])
        if not m:
            return NOT_KNOWN
        if m.group(1).startswith("Z"):
            return None
        try:
            return m.group(1), time.mktime(time.strptime(re.sub(r"\s+", " ", m.group(2)), "%a %b %d %H:%M:%S %Y")), m.group(3)
        except (ValueError, OverflowError):
            return NOT_KNOWN
    try:
        os.kill(pid, 0)
    except PermissionError:
        return NOT_KNOWN
    except (OSError, OverflowError):
        return None
    return NOT_KNOWN


def is_ours(cmd, cmdline):
    """Is this command line bin/vh <cmd>, or the tool bin/vh exec'd into for it?"""
    if not cmd:
        return False
    tool = EXEC.get(cmd) or rf"/tools/(?:[\w.-]+/)*{re.escape(cmd)}\.(?:py|mjs)"
    return bool(re.search(rf"(?:^|[\s/])vh\s+{re.escape(cmd)}(?:\s|$)|{tool}(?:\s|$)", cmdline))


def of_this(said, project):
    """Is a start line's project this folder? By its real path; else the file system's word, for a path that is the same folder in another
    form (a case-insensitive disk, another Unicode form)."""
    real = os.path.realpath(project)
    if said == activity._text(real):
        return True
    try:
        return os.path.samefile(said, real)
    except (OSError, ValueError):
        return False


def confirmed(run, project):
    """(what the run's pid is: THIS, GONE, ELSEWHERE, UNSURE or NO_PS; the process's (stat, start, command) or None; why not)."""
    pid = run.get("pid")
    p = process(pid) if pid else None
    if p is NOT_KNOWN:
        return NO_PS, None, f"ps could not say what pid {pid} is: nothing was sent, and nothing written"
    if p is None:
        return GONE, None, f"pid {pid} is gone"
    if run.get("start") is None or not run["start"] - EARLY <= p[1] <= run["start"] + LATE:
        return GONE, p, f"pid {pid} started at another time than this run: a reused pid"
    if not is_ours(run.get("cmd"), p[2]):
        return UNSURE, p, f"pid {pid} started when this run did, but its command line is not bin/vh {run.get('cmd')}'s: nothing was sent ({activity.scrub(p[2][:80])})"
    said = run.get("project")
    if said is None:
        return UNSURE, p, f"its start line does not say which project it is of (an older bin/vh wrote it), so pid {pid} cannot be said to be this project's: nothing was sent"
    if not of_this(said, project):
        return ELSEWHERE, p, f"its start line is of {said}: this folder is a copy of it, or it has moved: nothing was sent"
    return THIS, p, None


def tree(pid):
    """Every pid under a process; None when ps cannot say."""
    rows = ps("-A", "-o", "pid=", "-o", "ppid=")
    if not rows:
        return None
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
    """.ovh/cancel/<run>, while this stops it: what bin/vh and the tools read when they write the end line. A run's id comes from a log, and a
    project may be someone's: it names a file only as bin/vh writes one, and neither the folder nor the file is followed if it is a link."""

    def __init__(self, project, run_id):
        if not RUN_ID.fullmatch(run_id):
            raise ValueError(f"not a run's id: {run_id!r}")
        self.dir = activity.log_path(project).parent / "cancel"
        self.file = self.dir / run_id

    def set(self, code):
        try:
            if self.dir.is_symlink():
                return
            self.dir.mkdir(parents=True, exist_ok=True)
            fd = os.open(self.file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644)
            try:
                os.write(fd, f"{code}\n".encode())
            finally:
                os.close(fd)
        except OSError:   # what cannot be marked gets its end line from here
            pass

    def done(self):
        try:
            if not self.dir.is_symlink():
                self.file.unlink()
                self.dir.rmdir()
        except OSError:
            pass


def sweep(project, runs):
    """The marks kept for a run that was still_running at an earlier cancel, once it is over."""
    d = activity.log_path(project).parent / "cancel"
    running = {r["run"] for r in runs if r["state"] == "running"}
    try:
        names = [] if d.is_symlink() else os.listdir(d)
    except OSError:
        names = []
    for n in names:
        if RUN_ID.fullmatch(n) and n not in running:
            Mark(project, n).done()


def has_gone(pid, start):
    """Is the process this signalled over: no such pid, or another process with it? ps that cannot say: not yet."""
    q = process(pid)
    return q is None or (isinstance(q, tuple) and q[1] != start)


def wait_gone(pid, start, seconds):
    deadline = time.time() + seconds
    while time.time() < deadline:
        if has_gone(pid, start):
            return True
        time.sleep(0.1)
    return has_gone(pid, start)


def stop(project, run, timeout):
    """Stop one run, if it is confirmed. → its row."""
    rid, pid = run["run"], run["pid"]
    row = {"run": rid, "cmd": run.get("cmd"), "pid": pid, "state": None, "signal": None, "exit": None, "seconds": None, "kept": None, "why": None}
    t0 = time.time()
    if not RUN_ID.fullmatch(rid):
        row.update(state="not_confirmed", why="its id is not one bin/vh writes, so nothing here takes its word: nothing was sent")
        return row
    is_it, p, why = confirmed(run, project)
    if is_it is not THIS:
        end = end_of(project, rid)   # it ended on its own, between the listing and this
        if end:
            row.update(state="cancelled" if end.get("cancelled") else "finished", exit=end.get("exit"))
        elif is_it is NO_PS:
            row.update(state="still_running", why=why)
        elif is_it is UNSURE:
            row.update(state="not_confirmed", why=why)
        else:
            row.update(state="not_that_process", why=why)
            if is_it is GONE:   # only a pid that is gone, or another time's: what may still be running does not read as gone
                activity._write(str(activity.log_path(project)), {"event": "note", "run": rid, "t": round(time.time(), 3), "cmd": run.get("cmd") or "", "gone": True, "summary": f"its process is gone: {why} (bin/vh cancel)"})
        return row
    under_bash = bool(SHELL.search(p[2]))
    first_wait = min(timeout, INT_UNDER_BASH) if under_bash else timeout
    seen = set()

    def signal_all(sig):
        """Send it, while the pid is still that process and what is under it can be read. → was it sent?"""
        q = process(pid)
        if not isinstance(q, tuple) or q[1] != p[1]:
            return False
        kids = tree(pid) if under_bash else []
        if kids is None:
            return False
        seen.update(kids)
        for k in kids:
            send(k, sig)
        send(pid, sig)
        row["signal"] = signal.Signals(sig).name
        return True
    mark = Mark(project, rid)
    code = 130
    mark.set(code)
    keep_mark = False
    try:
        signal_all(signal.SIGINT)
        gone = wait_gone(pid, p[1], first_wait)
        if not gone:
            code = 143
            mark.set(code)
            signal_all(signal.SIGTERM)
            gone = wait_gone(pid, p[1], AFTER_TERM)
        if not gone:
            keep_mark = True
            row.update(state="still_running", seconds=round(time.time() - t0, 2),
                       why=f"pid {pid} has not stopped" + (f" (the last signal sent: {row['signal']})" if row["signal"] else "") + ". A tool in a step that takes no signal stops when the step ends, and its end line "
                       f"then says cancelled; ps may not have been able to say. Nothing stronger was sent: bin/vh activity shows it running, and kill -9 {pid} is yours to send")
            return row
        for k in seen:   # what was under it and has not gone with it (a child of a bash that went at once)
            q = process(k)
            if isinstance(q, tuple) and OURS.search(q[2]):
                send(k, signal.SIGTERM)
        deadline = time.time() + GRACE
        end = end_of(project, rid)
        while end is None and time.time() < deadline:
            time.sleep(0.05)
            end = end_of(project, rid)
        if end is None and not row["signal"]:   # it went before anything was sent, and said nothing: no cancel of this one
            activity._write(str(activity.log_path(project)), {"event": "note", "run": rid, "t": round(time.time(), 3), "cmd": run.get("cmd") or "", "gone": True, "summary": f"its process is gone: pid {pid} (bin/vh cancel)"})
            row.update(state="not_that_process", why=f"pid {pid} is gone")
            return row
        if end is None:   # no line of its own (bash at a TERM, a tool that was killed): written here
            now = time.time()
            end = {"event": "end", "run": rid, "t": round(now, 3), "cmd": run.get("cmd") or "", "exit": code, "duration": round(max(0.0, now - (run.get("start") or now)), 3), "cancelled": True}
            activity._write(str(activity.log_path(project)), end)
    finally:
        if not keep_mark:
            mark.done()
    row.update(state="cancelled" if end.get("cancelled") else "finished", exit=end.get("exit"), seconds=round(time.time() - t0, 2))
    now = next((r for r in activity.runs(activity.read(project, tail=1 << 18))[0] if r["run"] == rid), None)
    row["kept"] = (now or {}).get("kept")
    return row


def said(x):
    """A word from a log, for a terminal: no control characters."""
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "?", str(x))


def show(rec, out):
    if not rec["runs"] and not rec["skipped"]:
        print(f"cancel: nothing is running in {Path(rec['project']).name}", file=out)
    for r in rec["runs"]:
        head = f"cancel: {said(r['cmd'])} ({said(r['run'])})"
        if r["state"] == "cancelled":
            print(f"{head}: stopped by {r['signal']}, exit {r['exit']}, in {r['seconds']} s", file=out)
            print(f"  kept for a resume: {said(r['kept'])}" if r["kept"] else "  nothing is kept for a resume", file=out)
        elif r["state"] == "finished":
            print(f"{head}: it ended on its own, exit {r['exit']}", file=out)
        else:
            print(f"{head}: {r['state'].replace('_', ' ')}" + (f": {said(r['why'])}" if r["why"] else ""), file=out)
    for r in rec["skipped"]:
        print(f"cancel: left running: {said(r['cmd'])} ({said(r['run'])}): {r['why']}", file=out)


def main(argv):
    sys.stdout.reconfigure(errors="backslashreplace")   # (a folder's name that is not UTF-8 prints)
    ap = argparse.ArgumentParser(prog="bin/vh cancel", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("project", help="project folder (or a file inside it), or its name under projects/")
    ap.add_argument("run", nargs="?", help="this run only: its id, or the first or last part of one (bin/vh activity --json)")
    ap.add_argument("--timeout", type=float, default=15, help="seconds a tool has after SIGINT before SIGTERM (default 15; under bash at most 3)")
    ap.add_argument("--json", action="store_true", help="the record, as JSON (version 1)")
    a = ap.parse_intermixed_args(argv)   # (the run after an option: Python before 3.12 takes it only so)
    project = jsonerr.project_arg(a.project, "cancel")
    if project is None:
        return 2
    if not ps("-o", "pid=", "-p", str(os.getpid())):   # no ps, or one that may not look: a pid cannot be confirmed, nor said to be gone
        return jsonerr.fail("missing_tool", "cancel: ps cannot be run here, so no process can be confirmed: nothing was stopped", rc=1)
    recs = activity.read(project)
    all_runs = [r for r in activity.runs(recs)[0] if r["run"] != os.environ.get("OVH_ACTIVITY_RUN")]   # not this command's own
    of = {r["run"]: r.get("project") for r in recs if r["event"] == "start" and isinstance(r.get("run"), str)}
    for r in all_runs:
        r["project"] = of.get(r["run"])
    sweep(project, all_runs)
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
        rows.append(stop(project, r, a.timeout))
    rec = {"version": 1, "tool": "bin/vh cancel", "project": str(project), "runs": rows, "skipped": skipped, "cancelled": sum(1 for r in rows if r["state"] == "cancelled")}
    if a.json:
        print(json.dumps(rec, ensure_ascii=False, indent=1))
    show(rec, sys.stderr if a.json else sys.stdout)
    activity.note(f"{rec['cancelled']} run(s) cancelled" if rec["cancelled"] else "nothing to cancel", [])
    stuck = [r for r in rows if r["state"] in ("still_running", "not_confirmed") or (r["state"] == "not_that_process" and a.run)]
    if stuck:
        jsonerr.report("failed", f"cancel: {stuck[0]['run']}: {stuck[0]['why']}")   # (with --json: the record is out already)
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:
        sys.exit(0)
