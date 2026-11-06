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
            started this one), project (the real path of the folder the run is of, so a copy of the folder and its log
            is not taken for it; left out when over 480 bytes)
  progress  a long command's progress: run, done, total, unit (render, patch and proxy: frames; tts: lines; thumbs: pictures; deliver:
            percent, of its pass of passes). At most one line every several seconds, and the first and last (Progress below)
  note      what a command made, written by the tool itself: run, summary (one line), outputs (paths, relative to the
            project when inside it); or why it failed, with "level": "error", code and summary the message (tools/jsonerr.py);
            kept: what a tool that was stopped keeps for a resume; gone: true, from bin/vh cancel, when the pid in a run's start
            line is gone or of another time now: the run reads as gone
  end       a command ended: run, exit (its exit status: 130 after a Ctrl-C, after which bin/vh ends by SIGINT itself;
            128 + n when a tool that handles signal n stopped on it: desk, desk wait, gate --wait; a command killed by
            TERM or HUP ends at once and has no end line), duration (seconds; whole seconds under a bash without
            EPOCHREALTIME, such as macOS's 3.2), cancelled: true when bin/vh cancel stopped it (exit 130 or 143; tools/cancel.py)
  feedback  the review desk saved a submission (not part of a run): round, file, items by status
Who writes them: bin/vh writes a run's start before the command and its end from its EXIT trap, and hands the run to what
it starts through the environment (OVH_ACTIVITY_LOG, _RUN, _PID, _T0, _CMD). A tool adds note and progress lines; a tool
that bin/vh exec'd into (it has the run's pid: render, patch, frames and the other page tools, desk, gate) writes the end
itself, since no shell is left to do it. Every bin/vh command that works on a project is logged, except the read-only
views (status, activity, artifacts, projects, desk data, doctor, timeline --resolved, history list and diff). Never written:
environment variables, keys, file contents: what a start line hides of an argument, scrub() hides of a summary, an error's
message above all, which may repeat what was typed (word by word by the same rules; bin/vh's act_scrub is the same in bash).
Safety: a line is one write(2) with O_APPEND, so the lines of commands running at once never interleave: under 1 KiB from
bin/vh (bash's printf writes a longer line in 1024-byte pieces), under 4 KiB from Python and Node; a line that cannot be
written is dropped without a word: a command never fails, and never waits, because of its log. Every line is UTF-8: a
byte that is no part of a UTF-8 character (in an argument, a folder's or a file's name) is written as the text \\xNN, and
the reader shows a raw one in a line an older bin/vh wrote the same way.
A run without an end line is running while its process lives (and started within 7 days), else gone (it was killed, or
the machine restarted). bin/vh cancel stops a running one and sees that its end line says so. The reader reads the last 4 MB of the log.
"""
import json, os, re, subprocess, sys, threading, time
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


_SECRET = re.compile(r"key|token|secret|pass|auth|cred|cookie|header|bearer", re.I)
_KEY_STARTS = r"sk-|sk_|AIza|AQ\.|ghp_|gho_|ghu_|ghs_|github_pat_|glpat-|xox[abposr]-|eyJ|hf_|AKIA|ya29\."
_KEY_START = re.compile(_KEY_STARTS)
_KEY_INSIDE = re.compile(r"(^|[^A-Za-z0-9])((?:" + _KEY_STARTS + r")[A-Za-z0-9_.+/=-]{8,})")
_WORD = re.compile(r"""(["'(\[{<]*)(.*?)(["')\]}>,;:.!?]*)""", re.S)


def keyish(v):
    """Does a word look like a key? bin/vh's act_keyish: a vendor's prefix; 32 or more letters, digits and _; or key characters (also
    . + = -) with a digit among them: 32 or more, 16 or more in both cases, or 20 or more hex digits. Not a file name, a word, a slug, a date."""
    if len(v) < 12:
        return False
    if _KEY_START.match(v):
        return True
    if re.search(r"[^A-Za-z0-9_.+=-]", v):
        return False
    if not re.search(r"[^A-Za-z0-9_]", v) and len(v) >= 32:
        return True
    if not re.search(r"[0-9]", v) or re.search(r"\.[a-z][a-z0-9]{0,3}$", v):
        return False
    if len(v) >= 32 or (re.search(r"[A-Z]", v) and re.search(r"[a-z]", v) and len(v) >= 16):
        return True
    return not re.search(r"[^0-9a-fA-F-]", v) and len(v) >= 20


def _value(v, pname):
    """bin/vh's act_value: a value as a log line shows it."""
    w, frag = v, ""
    if "://" in w:   # user:password@host, and the fragment
        pre, post = w.split("://", 1)
        au = re.split(r"[/?#]", post, maxsplit=1)[0]
        if "@" in au:
            post = "…@" + au.rsplit("@", 1)[1] + post[len(au):]
        if "#" in post:
            post, frag = post.split("#", 1)[0], "#…"
        w = pre + "://" + post
    if "?" in w and ("://" in w or "=" in w.split("?", 1)[1]):   # every query value
        head, q = w.split("?", 1)
        w = head + "?" + "&".join(k.split("=", 1)[0] + "=…" if "=" in k else "…" if keyish(k) else k for k in q.split("&") if k)
    w += frag
    m = re.search(r"bearer ", w, re.I)
    if m:
        w = w[:m.start()] + "Bearer …"
    m = re.match(r"([A-Za-z][A-Za-z0-9_-]*): ", w)
    if m and _SECRET.search(m.group(1)):
        w = m.group(1) + ": …"
    if w == v and not os.path.exists(w):
        if re.search(r"\s", w):   # free text (a --note)
            return scrub(w)
        if pname == w or pname.endswith("-" + w):
            return w
        return "…" if keyish(w) else _KEY_INSIDE.sub(lambda x: x.group(1) + "…", w)
    return w


def _as_logged(a, pname):
    """bin/vh's act_shown: (an argument as a log line shows it, is the next one its value)."""
    n = ""
    if re.match(r"--[^=].*=", a, re.S):
        n = a.split("=", 1)[0]
    elif re.match(r"[A-Za-z_][^=]*=", a, re.S):
        n = a.split("=", 1)[0]
        if re.search(r"[^A-Za-z0-9_.-]", n):
            n = ""
    if n:
        if _SECRET.search(n) or not re.search(r"[^A-Z0-9_]", n):   # a secret's name, or NAME=value: a variable's
            return n + "=…", False
        return n + "=" + _value(a.split("=", 1)[1], pname), False
    if a.startswith("--") and len(a) > 2:
        return a, bool(_SECRET.search(a[2:]))
    if a == "-h":
        return a, False
    if re.fullmatch(r"-[A-Za-z]", a):
        return a, True
    if re.match(r"-[A-Za-z].", a, re.S):
        return a[:2] + "…", False
    return _value(a, pname), False


def scrub(text):
    """Free text as a log line may hold it: word by word, as a start line shows an argument (bin/vh's act_scrub), each word's quotes
    and punctuation aside. A word that names a secret hides the next (--key x, Authorization: x, Bearer x)."""
    log = os.environ.get("OVH_ACTIVITY_LOG") or ""
    pname = os.path.basename(os.path.dirname(os.path.dirname(log)))
    out, hide = [], False
    for i, w in enumerate(re.split(r"([ \t\r\n]+)", str(text))):
        if i % 2 or not w:   # the white space as it was: a message's lines stay lines
            out.append(w)
            continue
        pre, core, post = _WORD.fullmatch(w).groups()
        if hide and not core.startswith("-"):
            hide = core.lower() == "bearer"   # Authorization: Bearer x
            out.append(pre + (core if os.path.exists(core) else "…") + post)
        elif core.lower() == "bearer" or (post.startswith(":") and re.fullmatch(r"[A-Za-z0-9_-]+", core) and _SECRET.search(core)):
            out.append(w)
            hide = True
        else:
            a, hide = _as_logged(core, pname)
            out.append(pre + a + post)
    return "".join(out)


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
    return " ".join(scrub(s).split())[:300] if s else None


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


def progress(done, total=None, unit=None, **extra):
    c = _ctx()
    if c:
        _write(c[0], {"event": "progress", "run": c[1], "t": round(time.time(), 3), "cmd": c[2], "done": done,
                      **({"total": total} if total is not None else {}), **({"unit": unit} if unit else {}), **extra})


class Progress:
    """A long command's progress lines at a low rate: tick(done) writes a line when done has changed and `every` seconds have gone
    by since the last, always the first and the one that reaches total. The log is read back from its tail: a line is small, and
    few. clock: for a test."""

    def __init__(self, total=None, unit=None, every=5.0, clock=time.monotonic, **extra):
        self.total, self.unit, self.every, self.clock, self.extra = total, unit, every, clock, extra
        self.at, self.last = None, None

    def __call__(self, done, **extra):
        now = self.clock()
        final = self.total is not None and done >= self.total
        if done == self.last or (self.at is not None and now - self.at < self.every and not final):
            return False
        self.at, self.last = now, done
        progress(done, self.total, self.unit, **{**self.extra, **extra})
        return True


def follow_ffmpeg(cmd, tick, keep_stderr=True):
    """Run ffmpeg (cmd[0]) with its -progress on a pipe: tick(frame, seconds written) at each of its reports. → (exit status, what it
    wrote on stderr; keep_stderr False: it goes where ours goes). Stopped by an exception (a Ctrl-C), ffmpeg goes too."""
    p = subprocess.Popen([*cmd[:1], "-progress", "pipe:1", *cmd[1:]], stdout=subprocess.PIPE, stderr=subprocess.PIPE if keep_stderr else None, stdin=subprocess.DEVNULL, text=True, errors="replace")
    err, th = [], None
    if keep_stderr:
        th = threading.Thread(target=lambda: err.append(p.stderr.read()), daemon=True)
        th.start()
    frame, seconds = None, None
    try:
        for line in p.stdout:
            k, _, v = line.strip().partition("=")
            if k == "frame" and v.isdigit():
                frame = int(v)
            elif k in ("out_time_us", "out_time_ms") and v.lstrip("-").isdigit():   # both are microseconds, as ffmpeg writes them
                seconds = max(0.0, int(v) / 1e6)
            elif k == "progress":
                tick(frame, seconds)
        p.wait()
    except BaseException:
        p.kill()
        p.wait()
        raise
    if th:
        th.join(5)
    return p.returncode, "".join(err)


def cancelling(log, run, code):
    """(the exit status for the end line, is it a cancel): bin/vh cancel's mark for this run, there while it stops it (tools/cancel.py).
    A run that ended well ended on its own; any other exit under the mark is the cancel's."""
    try:
        with open(os.path.join(os.path.dirname(log), "cancel", run), encoding="utf-8") as f:
            said = f.read().strip()
    except (OSError, ValueError):
        return code, False
    if code == 0:
        return code, False
    return (code if code in (130, 143) else 143 if said == "143" else 130), True


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
    code, cancelled = cancelling(c[0], c[1], code)
    rec = {"event": "end", "run": c[1], "t": round(now, 3), "cmd": c[2], "exit": code, "duration": dur}
    if cancelled:
        rec["cancelled"] = True
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

_STR = ("run", "cmd", "cwd", "summary", "unit", "parent", "file", "round", "level", "code", "kept", "project")
_INT = ("pid", "exit", "decisions")
_NUM = ("duration", "done", "total", "pass", "passes")


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
        if int(pid) <= 0:   # (to kill(2), a process group)
            return False
        os.kill(int(pid), 0)
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError, OverflowError):
        return False
    return True


def runs(records, now=None):
    """(runs, events): the records grouped by run, in the order they began (the log's own order), and the records
    outside any run. A run: {run, cmd, args, cwd, pid, parent, start, end, exit, duration, state, summary, outputs,
    progress, error, cancelled, kept}; state is running, ok (exit 0), failed (another exit status) or gone (no end line, and its
    process is gone, or bin/vh cancel found its pid is another process now); error is why it failed, when the tool could say:
    {code, message} (a note with level error), else null; cancelled: bin/vh cancel stopped it; kept: what it kept for a resume."""
    now = time.time() if now is None else now
    by, events, gone = {}, [], set()   # a dict keeps the order runs first appear in
    for r in records:
        rid, ev = r.get("run"), r["event"]
        if ev not in ("start", "end", "note", "progress") or not isinstance(rid, str):
            events.append(r)
            continue
        run = by.get(rid)
        if run is None:
            run = by[rid] = {"run": rid, "cmd": r.get("cmd") or "", "args": [], "cwd": None, "pid": None, "parent": None,
                             "start": None, "end": None, "exit": None, "duration": None, "state": None, "summary": None,
                             "outputs": [], "progress": None, "error": None, "cancelled": False, "kept": None}
        if ev == "start":
            run.update(cmd=r.get("cmd") or run["cmd"], args=r.get("args") if isinstance(r.get("args"), list) else [],
                       cwd=r.get("cwd"), pid=r.get("pid"), parent=r.get("parent"), start=r["t"])
        elif ev == "end":
            run.update(end=r["t"], exit=r.get("exit"), duration=r.get("duration"), cancelled=r.get("cancelled") is True)
            if r.get("summary"):
                run["summary"] = r["summary"]
        elif ev == "note" and r.get("level") == "error":
            run["error"] = {"code": r.get("code") or "failed", "message": r.get("summary") or ""}
        elif ev == "note":
            if r.get("summary"):
                run["summary"] = r["summary"]
            run["outputs"] += [o for o in r.get("outputs") or [] if isinstance(o, str) and o not in run["outputs"]]
            if r.get("kept"):
                run["kept"] = r["kept"]
            if r.get("gone") is True:
                gone.add(rid)
        else:
            run["progress"] = {k: r.get(k) for k in ("done", "total", "unit", "t", "pass", "passes") if r.get(k) is not None}
    out = list(by.values())
    for run in out:
        if run["end"] is not None:
            run["state"] = "ok" if run["exit"] == 0 else "failed"
        elif run["pid"] and run["run"] not in gone and _alive(run["pid"]) and (run["start"] or 0) > now - RUNNING_FOR:
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
    mark = {"ok": "✓", "failed": "✗ cancelled" if run.get("cancelled") else f"✗ exit {run['exit']}", "running": "…", "gone": "? gone"}[st]
    how = _dur(run["duration"]) if st in ("ok", "failed") else _dur(now - run["start"]) if st == "running" and run["start"] else ""
    pr = run.get("progress") or {}
    if st == "running" and pr.get("done") is not None:
        how += f" · {pr['done']}" + (f" / {pr['total']}" if pr.get("total") is not None else "") + (f" {pr['unit']}" if pr.get("unit") else "") + (f", pass {pr['pass']} of {pr['passes']}" if pr.get("passes") else "")
    tail = run["summary"] or ""
    if run.get("error"):
        tail += (" · " if tail else "") + run["error"]["message"]
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
        mark = "✓" if r.get("exit") == 0 else "✗ cancelled" if r.get("cancelled") else f"✗ exit {r.get('exit')}"
        return f"{_when(r['t'], False)}  {cmd:<9} {mark} · {_dur(r.get('duration'))}" + (f"  {r['summary']}" if r.get("summary") else "")
    if ev == "progress":
        return f"{_when(r['t'], False)}  {cmd:<9} {r.get('done')}" + (f" / {r['total']}" if r.get("total") is not None else "") + (f" {r['unit']}" if r.get("unit") else "")
    if ev == "note" and r.get("level") == "error":
        return f"{_when(r['t'], False)}  {cmd:<9} ✗ {r.get('summary') or ''}"
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
    import jsonerr
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
            return jsonerr.fail("no_project", f"activity: {e}")
        if not (project / "BRIEF.md").is_file():
            return jsonerr.fail("no_project", f"activity: {project} is not a project (no BRIEF.md)")
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
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import jsonerr
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:   # bin/vh activity … | head
        sys.exit(0)
