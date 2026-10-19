"""bin/vh activity: what the bin/vh commands did in a project, one JSON line per event in <project>/.ovh/activity.jsonl.

usage: bin/vh activity <project> [--json] [--follow] [--limit N]
  (no flag)  the last N runs (default 20), oldest first, one line each: when it started, the command, how it ended (✓, or ✗
             and the exit status; … while it runs), how long it took, its summary and what it wrote
  --json     {"version": 1, "project", "log", "runs": [...], "events": [...]}: the last N runs (default 100) and the events
             outside a run (tools/desk/README.md, 给客户端的数据, has every field)
  --follow   the events as they are appended, until Ctrl-C; with --json each line as JSON (bad fields dropped)
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

The lines (each has "v": 1, "event", and "t": seconds since the epoch; "run" ties it to one command):
  start     a command began: run, cmd, args (as typed, but never a secret: the value of an option or name=value whose
            name says key, token, secret, pass, auth, cred, cookie, header or bearer, of an upper-case NAME=value and
            of a one-letter option, a URL's user:password@, query values and fragment, a Bearer token, and whatever
            looks like a key are written as "…"; at most 24 of them), cwd, pid, parent (the run of the bin/vh that
            started this one)
  progress  a long command's progress: run, done, total, unit (render: frames)
  note      what a command made, written by the tool itself: run, summary (one line), outputs (paths, relative to the
            project when inside it)
  end       a command ended: run, exit (its exit status: 130 after a Ctrl-C, after which bin/vh ends by SIGINT itself;
            128 + n when a tool that handles signal n stopped on it: desk, desk wait, gate --wait; a command killed by
            TERM or HUP ends at once and has no end line), duration (seconds; whole seconds under a bash without
            EPOCHREALTIME, such as macOS's 3.2)
  feedback  the review desk saved a submission (not part of a run): round, file, items by status
Who writes them: bin/vh writes a run's start before the command and its end from its EXIT trap, and hands the run to what
it starts through the environment (OVH_ACTIVITY_LOG, _RUN, _PID, _T0, _CMD). A tool adds note and progress lines; a tool
that bin/vh exec'd into (it has the run's pid: render, patch, frames and the other page tools, desk, gate) writes the end
itself, since no shell is left to do it. Every bin/vh command that works on a project is logged, except the read-only
views (status, activity, desk data, doctor). Never written: environment variables, keys, file contents.
Safety: a line is one write(2) with O_APPEND, so the lines of commands running at once never interleave: under 1 KiB from
bin/vh (bash's printf writes a longer line in 1024-byte pieces), under 4 KiB from Python and Node; a line that cannot be
written is dropped without a word: a command never fails, and never waits, because of its log. Every line is UTF-8: a
byte that is no part of a UTF-8 character (in an argument, a folder's or a file's name) is written as the text \\xNN, and
the reader shows a raw one in a line an older bin/vh wrote the same way.
A run without an end line is running while its process lives (and started within 7 days), else gone (it was killed, or
the machine restarted). The reader reads the last 4 MB of the log.
"""
import json, os, sys, time
from pathlib import Path

MAX_LINE = 3800              # bytes: one line, one write, well under 4 KiB
TAIL = 4 << 20               # the reader reads this much of the end of the log
RUNNING_FOR = 7 * 86400      # a run with no end line counts as running at most this long after its start
_ended = False


def log_path(project):
    return Path(project) / ".ovh" / "activity.jsonl"


def _ctx():
    """(log, run, cmd) of the run bin/vh handed to this process, or None."""
    log, run = os.environ.get("OVH_ACTIVITY_LOG"), os.environ.get("OVH_ACTIVITY_RUN")
    return (log, run, os.environ.get("OVH_ACTIVITY_CMD") or "") if log and run else None


def _rel(log, p):
    """A path as the log writes it: relative to the project when inside it, else absolute."""
    try:
        proj = os.path.realpath(os.path.dirname(os.path.dirname(log)))
        a = os.path.realpath(os.path.abspath(str(p)))
        return os.path.relpath(a, proj) if os.path.commonpath([a, proj]) == proj else a
    except (ValueError, OSError, TypeError):
        return str(p)


def _text(x):
    """A value as the log holds it: in a str, a byte that was no part of a UTF-8 character (os.fsdecode and sys.argv keep it as
    a surrogate, U+DC80–DCFF) is the text \\xNN, as bin/vh writes it, and any other lone surrogate is U+FFFD, so a line is
    always UTF-8 and prints anywhere; a list or a dict value by value"""
    if isinstance(x, str):
        if not any("\ud800" <= c <= "\udfff" for c in x):
            return x
        return "".join(f"\\x{ord(c) - 0xdc00:02x}" if "\udc80" <= c <= "\udcff" else "�" if "\ud800" <= c <= "\udfff" else c for c in x)
    if isinstance(x, list):
        return [_text(v) for v in x]
    if isinstance(x, dict):
        return {_text(k): _text(v) for k, v in x.items()}
    return x


def _write(log, rec):
    """Append one record as one line; never raises. A summary or an output list too long for one line is cut."""
    try:
        rec = _text(dict({"v": 1}, **rec))
        data = (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        if len(data) > MAX_LINE:
            for k in ("outputs", "args"):
                if isinstance(rec.get(k), list):
                    rec[k] = rec[k][:5] + (["…"] if len(rec[k]) > 5 else [])
            if isinstance(rec.get("summary"), str):
                rec["summary"] = rec["summary"][:300]
            data = (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            if len(data) > MAX_LINE:
                return
        d = os.path.dirname(log)
        if d and not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)
        fd = os.open(log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
    except Exception:   # a full disk, a read-only project, a bad value: the command goes on without its line
        pass


def _summary(s):
    return " ".join(str(s).split())[:300] if s else None


def note(summary=None, outputs=None, **extra):
    """What this command made (one line, the files it wrote), into the run bin/vh handed over; nothing without one."""
    c = _ctx()
    if not c:
        return
    rec = {"event": "note", "run": c[1], "t": round(time.time(), 3), "cmd": c[2]}
    if summary:
        rec["summary"] = _summary(summary)
    if outputs:
        rec["outputs"] = [_rel(c[0], p) for p in outputs if p][:20]
    rec.update({k: v for k, v in extra.items() if v is not None})
    _write(c[0], rec)


def progress(done, total=None, unit=None):
    c = _ctx()
    if c:
        _write(c[0], {"event": "progress", "run": c[1], "t": round(time.time(), 3), "cmd": c[2], "done": done,
                      **({"total": total} if total is not None else {}), **({"unit": unit} if unit else {})})


def end(code, summary=None):
    """The run's end line, when this process is the run's own (bin/vh exec'd into it): once."""
    global _ended
    c = _ctx()
    if not c or _ended or os.environ.get("OVH_ACTIVITY_PID") != str(os.getpid()):
        return
    _ended = True
    now = time.time()
    try:
        dur = round(max(0.0, now - float(os.environ.get("OVH_ACTIVITY_T0") or now)), 3)
    except ValueError:
        dur = None
    rec = {"event": "end", "run": c[1], "t": round(now, 3), "cmd": c[2], "exit": code, "duration": dur}
    if summary:
        rec["summary"] = _summary(summary)
    _write(c[0], rec)


def exiting(fn):
    """Run fn() (a main returning an exit status), write the run's end with how it ended, and return the status."""
    try:
        code = fn()
    except SystemExit as e:
        end(e.code if isinstance(e.code, int) else 0 if e.code is None else 1)
        raise
    except KeyboardInterrupt:
        end(130)
        raise
    except BaseException:
        end(1)
        raise
    code = code if isinstance(code, int) else 0 if code is None else 1
    end(code)
    return code


def event(project, kind, **fields):
    """A line outside any run (the desk saved a submission), written into the project's own log whoever started us."""
    c = _ctx()
    log = str(log_path(project))
    rec = {"event": kind, "t": round(time.time(), 3)}
    if c and os.path.realpath(c[0]) == os.path.realpath(log):
        rec["run"] = c[1]
    rec.update({k: v for k, v in fields.items() if v is not None})
    _write(log, rec)


# ---------- reading ----------

_STR = ("run", "cmd", "cwd", "summary", "unit", "parent", "file", "round")
_INT = ("pid", "exit", "decisions")
_NUM = ("duration", "done", "total")


def _number(x, whole=False):
    return isinstance(x, int if whole else (int, float)) and not isinstance(x, bool)


def record(r):
    """A raw line's object → the record the reader trusts, or None: a v 1 object with an event and a time, each known
    field of the wrong type dropped (args and outputs keep their strings only). A bad line (a tool's bug, a hand edit)
    must not stop bin/vh activity, bin/vh status or a client."""
    if not (isinstance(r, dict) and _number(r.get("v"), True) and r["v"] == 1 and isinstance(r.get("event"), str) and _number(r.get("t"))):
        return None
    r = _text(r)   # a line written before every writer escaped its bytes: they come in as surrogates, out as \xNN
    out = dict(r)
    for k, v in r.items():
        if k in ("args", "outputs"):
            if isinstance(v, list):
                out[k] = [x for x in v if isinstance(x, str)]
            else:
                del out[k]
        elif (k in _STR and not isinstance(v, str)) or (k in _INT and not _number(v, True)) or (k in _NUM and not _number(v)) \
                or (k == "items" and not isinstance(v, dict)):
            del out[k]
    return out


def read(project, tail=TAIL):
    """The log's records, oldest first (the last `tail` bytes of it); unreadable lines are skipped, bad fields dropped."""
    p = log_path(project)
    try:
        with open(p, "rb") as f:
            size = os.fstat(f.fileno()).st_size
            if size > tail:
                f.seek(size - tail)
                f.readline()   # the rest of a line cut by the seek
            data = f.read()
    except OSError:
        return []
    out = []
    for raw in data.split(b"\n"):
        if not raw.strip():
            continue
        try:
            r = record(json.loads(raw.decode("utf-8", "surrogateescape")))   # an old line's raw byte: \xNN (_text)
        except ValueError:
            continue
        if r:
            out.append(r)
    return out


def _alive(pid):
    try:
        os.kill(int(pid), 0)
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError, OverflowError):
        return False
    return True


def runs(records, now=None):
    """(runs, events): the records grouped by run, in the order they began (the log's own order), and the records
    outside any run. A run: {run, cmd, args, cwd, pid, parent, start, end, exit, duration, state, summary, outputs,
    progress}; state is running, ok (exit 0), failed (another exit status) or gone (no end line, and its process is gone)."""
    now = time.time() if now is None else now
    by, events = {}, []   # a dict keeps the order runs first appear in
    for r in records:
        rid, ev = r.get("run"), r["event"]
        if ev not in ("start", "end", "note", "progress") or not isinstance(rid, str):
            events.append(r)
            continue
        run = by.get(rid)
        if run is None:
            run = by[rid] = {"run": rid, "cmd": r.get("cmd") or "", "args": [], "cwd": None, "pid": None, "parent": None,
                             "start": None, "end": None, "exit": None, "duration": None, "state": None, "summary": None,
                             "outputs": [], "progress": None}
        if ev == "start":
            run.update(cmd=r.get("cmd") or run["cmd"], args=r.get("args") if isinstance(r.get("args"), list) else [],
                       cwd=r.get("cwd"), pid=r.get("pid"), parent=r.get("parent"), start=r["t"])
        elif ev == "end":
            run.update(end=r["t"], exit=r.get("exit"), duration=r.get("duration"))
            if r.get("summary"):
                run["summary"] = r["summary"]
        elif ev == "note":
            if r.get("summary"):
                run["summary"] = r["summary"]
            run["outputs"] += [o for o in r.get("outputs") or [] if isinstance(o, str) and o not in run["outputs"]]
        else:
            run["progress"] = {k: r.get(k) for k in ("done", "total", "unit", "t") if r.get(k) is not None}
    out = list(by.values())
    for run in out:
        if run["end"] is not None:
            run["state"] = "ok" if run["exit"] == 0 else "failed"
        elif run["pid"] and _alive(run["pid"]) and (run["start"] or 0) > now - RUNNING_FOR:
            run["state"] = "running"
        else:
            run["state"] = "gone"
    return out, events


# ---------- the command ----------

def _when(t, day=True):
    return time.strftime("%m-%d %H:%M:%S" if day else "%H:%M:%S", time.localtime(t))


def _dur(s):
    if s is None:
        return ""
    return f"{s:.1f} s" if s < 60 else f"{int(s // 60)} min {int(s % 60):02d} s" if s < 3600 else f"{s / 3600:.1f} h"


def _shown(a, cwd, project):
    """An argument as the human listing shows it: a path inside the project relative to it, the rest as typed."""
    a = str(a)
    if project is None or not a or a.startswith("-") or a == "…":
        return a
    k, eq, v = a.partition("=") if "=" in a and not a.startswith("/") else ("", "", a)
    p = v if os.path.isabs(v) else os.path.join(cwd or "", v) if cwd else None
    if not p:
        return a
    p, root = os.path.realpath(p), os.path.realpath(str(project))   # (macOS: /var is /private/var)
    if p == root:
        return k + eq + "."
    if p.startswith(root + os.sep):
        return k + eq + os.path.relpath(p, root)
    return a


def _cmdline(run, project=None):
    a = " ".join(_shown(x, run.get("cwd"), project) for x in (run.get("args") or [])[:6])
    return f"{run['cmd']} {a}".strip()


def show_run(run, now, project=None):
    st = run["state"]
    mark = {"ok": "✓", "failed": f"✗ exit {run['exit']}", "running": "…", "gone": "? gone"}[st]
    how = _dur(run["duration"]) if st in ("ok", "failed") else _dur(now - run["start"]) if st == "running" and run["start"] else ""
    pr = run.get("progress") or {}
    if st == "running" and pr.get("done") is not None:
        how += f" · {pr['done']}" + (f" / {pr['total']}" if pr.get("total") is not None else "") + (f" {pr['unit']}" if pr.get("unit") else "")
    tail = run["summary"] or ""
    outs = [o for o in run["outputs"] if o not in tail]
    if outs:
        tail += (" → " if tail else "→ ") + ", ".join(outs[:3]) + (" …" if len(outs) > 3 else "")
    t = run["start"] or run["end"] or 0
    return f"{_when(t)}  {_cmdline(run, project)[:60]:<28} {mark} {how}".rstrip() + (f"  {tail}" if tail else "")


def show_event(r):
    if r["event"] == "feedback":
        n = r.get("items") or {}
        counts = ", ".join(f"{v} {k}" for k, v in n.items()) if isinstance(n, dict) and n else "no item marked"
        return f"{_when(r['t'])}  feedback (round {r.get('round', '?')}) · {counts} → {r.get('file', '')}"
    return f"{_when(r['t'])}  {r['event']}"


def show_line(r):
    """One raw record, for --follow."""
    ev, cmd = r["event"], r.get("cmd") or ""
    if ev == "start":
        return f"{_when(r['t'], False)}  {cmd:<9} started  {' '.join(str(x) for x in (r.get('args') or [])[:6])}".rstrip()
    if ev == "end":
        mark = "✓" if r.get("exit") == 0 else f"✗ exit {r.get('exit')}"
        return f"{_when(r['t'], False)}  {cmd:<9} {mark} · {_dur(r.get('duration'))}" + (f"  {r['summary']}" if r.get("summary") else "")
    if ev == "progress":
        return f"{_when(r['t'], False)}  {cmd:<9} {r.get('done')}" + (f" / {r['total']}" if r.get("total") is not None else "") + (f" {r['unit']}" if r.get("unit") else "")
    if ev == "note":
        outs = ", ".join(r.get("outputs") or [])
        return f"{_when(r['t'], False)}  {cmd:<9} {r.get('summary') or ''}" + (f" → {outs}" if outs else "")
    return show_event(r)


def follow(project, as_json, limit, poll=0.5):
    p = log_path(project)
    for r in read(project)[-limit:]:
        print(json.dumps(r, ensure_ascii=False) if as_json else show_line(r), flush=True)
    pos = p.stat().st_size if p.exists() else 0
    buf = b""
    try:
        while True:
            time.sleep(poll)
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size < pos:   # the log was replaced: start again from its top
                pos, buf = 0, b""
            if size == pos:
                continue
            with open(p, "rb") as f:
                f.seek(pos)
                buf += f.read(size - pos)
            pos = size
            *lines, buf = buf.split(b"\n")
            for raw in lines:
                try:
                    r = record(json.loads(raw.decode("utf-8", "surrogateescape")))   # an old line's raw byte: \xNN (_text)
                except ValueError:
                    continue
                if r:
                    print(json.dumps(r, ensure_ascii=False) if as_json else show_line(r), flush=True)
    except KeyboardInterrupt:
        return 130


def main(argv):
    import argparse
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    ap = argparse.ArgumentParser(prog="bin/vh activity", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project folder (or a file inside it), or its name under projects/")
    ap.add_argument("--json", action="store_true", help="the runs and events as JSON (with --follow: each line)")
    ap.add_argument("--follow", action="store_true", help="print events as they are appended, until Ctrl-C")
    ap.add_argument("--limit", type=int, help="this many runs (default 20; 100 with --json)")
    a = ap.parse_args(argv)
    from gatecheck import project_of   # a file or folder inside a project → the project
    p = Path(a.project).expanduser()
    project = project_of(p) if p.exists() else None
    if project is None:
        from vhdraw import project_dir
        try:
            project = project_dir(a.project)
        except SystemExit as e:
            print(f"activity: {e}", file=sys.stderr)
            return 2
        if not (project / "BRIEF.md").is_file():
            print(f"activity: {project} is not a project (no BRIEF.md)", file=sys.stderr)
            return 2
    limit = a.limit if a.limit and a.limit > 0 else (100 if a.json else 20)
    if a.follow:
        return follow(project, a.json, limit)
    now = time.time()
    recs = read(project)
    rs, events = runs(recs, now)
    rs = rs[-limit:]
    if a.json:
        print(json.dumps({"version": 1, "project": str(project), "log": str(log_path(project)), "runs": rs,
                          "events": events[-limit:]}, ensure_ascii=False, indent=1))
        return 0
    if not rs and not events:
        print(f"activity: nothing recorded yet in {project.name} ({log_path(project).relative_to(project)})")
        return 0
    first = {}   # where each run and event first appears in the log: the listing keeps the log's order
    for i, r in enumerate(recs):
        first.setdefault(r.get("run") if r["event"] in ("start", "end", "note", "progress") else id(r), i)
    lines = [(first.get(r["run"], 0), show_run(r, now, project)) for r in rs] + [(first.get(id(e), 0), show_event(e)) for e in events]
    for _, line in sorted(lines, key=lambda x: x[0])[-limit:]:
        print(line)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:   # bin/vh activity … | head
        sys.exit(0)
