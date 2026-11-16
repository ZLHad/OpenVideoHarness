"""Who is working on a project: the lock the console's agent takes before a turn, and what else it looks for first.

A turn of an agent in the console holds <project>/.ovh/agent.lock while it runs: a JSON line {pid, desk, kind, label,
session, since}, made with O_EXCL, so two console agents (two pages, two desks, Claude and Codex side by side) never work
on one project at once. A lock whose process is gone is stale and goes. Before taking it the console also looks for work
it did not start:

  - a bin/vh command running in the project (its activity log, tools/activity.py), unless the console's own agent
    started it (a process under the adapter);
  - an agent waiting for this project's review (bin/vh desk wait, out/review/feedback/.listening): the agent in the
    terminal that will carry on once the person submits;
  - an agent program (claude, codex, dsh, opencode, gemini …) whose working folder is in the project (lsof, where it is
    there).

It is advisory, like every lock bin/vh takes: it keeps the console from starting a second agent on a project, it does not
stop a terminal agent that never looks. It shares no file with the other locks (bin/vh mix's *.mix.lock, the asset
ledger's .ledger.lock, the review's .consumed.lock), so it can neither wait for them nor be waited for.
"""
import json, os, re, shutil, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
AGENT_PROGRAMS = re.compile(r"(?i)(^|/)(claude|codex|dsh|opencode|gemini|aider|cursor-agent|goose|amp|qwen)([-.\w]*)$")


def path(project):
    return Path(project) / ".ovh" / "agent.lock"


def _alive(pid):
    try:
        os.kill(int(pid), 0)
        return True
    except PermissionError:
        return True
    except (OSError, ValueError, TypeError):
        return False


def read(project):
    """The lock's record while its process lives, else None (a stale one is left for acquire to clear)."""
    try:
        rec = json.loads(path(project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return rec if isinstance(rec, dict) and _alive(rec.get("pid")) else None


def acquire(project, holder):
    """Take the lock for holder ({kind, label, session, desk}); True, or the record of whoever holds it."""
    p = path(project)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        return {"label": "?", "why": "no_folder"}
    rec = dict(holder, pid=os.getpid(), since=time.time())
    for _ in range(3):
        try:
            fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            cur = read(project)
            if cur is not None:
                if cur.get("pid") == os.getpid() and cur.get("session") == holder.get("session"):
                    return True   # this very session already holds it
                return cur
            try:   # stale: its process is gone
                p.unlink()
            except OSError:
                pass
            continue
        except OSError:
            return {"label": "?", "why": "unwritable"}
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False))
        return True
    return read(project) or {"label": "?", "why": "race"}


def release(project, session, turn=None):
    """Let go of the lock this session holds (another holder's lock is left alone; with turn, only that turn's)."""
    cur = None
    try:
        cur = json.loads(path(project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if isinstance(cur, dict) and cur.get("pid") == os.getpid() and cur.get("session") == session and (turn is None or cur.get("turn") in (None, turn)):
        try:
            path(project).unlink()
        except OSError:
            pass


def _tree():
    """{pid: parent pid} of every process this user can see (ps), or {} where there is no ps."""
    if not shutil.which("ps"):
        return {}
    try:
        out = subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    tree = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            tree[int(parts[0])] = int(parts[1])
    return tree


def _under(pid, roots, tree):
    """Is pid one of roots or a descendant of one?"""
    seen = 0
    while pid and seen < 64:
        if pid in roots:
            return True
        pid = tree.get(pid)
        seen += 1
    return False


def peer_pid(port):
    """The pid of the process whose end of a TCP connection on 127.0.0.1 is this port (lsof; ss on Linux), or None."""
    try:
        if shutil.which("lsof"):
            out = subprocess.run(["lsof", "-nP", f"-iTCP@127.0.0.1:{int(port)}", "-sTCP:ESTABLISHED", "-Fpn"], capture_output=True,
                                 text=True, timeout=5).stdout
            pid = None
            for line in out.splitlines():
                if line.startswith("p") and line[1:].isdigit():
                    pid = int(line[1:])
                elif line.startswith("n") and line[1:].startswith(f"127.0.0.1:{int(port)}->"):
                    return pid
        elif shutil.which("ss"):
            out = subprocess.run(["ss", "-tnpH", "state", "established", f"( sport = :{int(port)} )"], capture_output=True,
                                 text=True, timeout=5).stdout
            m = re.search(r"pid=(\d+)", out)
            return int(m.group(1)) if m else None
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return None


def from_agents(port, ours):
    """Does the connection from this local port come from one of the console's own agents (a process under an adapter)?
    The second line of defence behind the token: a process an agent starts in a session of its own escapes it."""
    roots = {int(p) for p in ours if p}
    if not roots:
        return False
    pid = peer_pid(port)
    return bool(pid) and _under(pid, roots, _tree())


def _agents_in(project, ours, tree):
    """[(pid, program)] of agent programs whose working folder is inside the project, not ours (lsof; [] without it)."""
    if not shutil.which("lsof"):
        return []
    root = os.path.realpath(str(project))
    try:
        out = subprocess.run(["lsof", "-a", "-d", "cwd", "-u", str(os.getuid()), "-Fpcn"], capture_output=True, text=True,
                             timeout=6).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    inside, pid, cmd = [], None, ""
    for line in out.splitlines():
        if line.startswith("p"):
            pid, cmd = int(line[1:]) if line[1:].isdigit() else None, ""
        elif line.startswith("c"):
            cmd = line[1:]
        elif line.startswith("n") and pid:
            n = os.path.realpath(line[1:])
            if (n == root or n.startswith(root + os.sep)) and not _under(pid, ours, tree):
                inside.append((pid, cmd))
    found = []
    args = {}
    if any(not AGENT_PROGRAMS.search(c) for _, c in inside):   # node and python CLIs: their name is in the command line
        try:
            ps = subprocess.run(["ps", "-o", "pid=,args=", "-p", ",".join(str(p) for p, _ in inside)], capture_output=True, text=True, timeout=5).stdout
            args = {int(l.split(None, 1)[0]): l.split(None, 1)[1] for l in ps.splitlines() if len(l.split(None, 1)) == 2 and l.split()[0].isdigit()}
        except (OSError, subprocess.SubprocessError):
            args = {}
    for pid, cmd in inside:
        if AGENT_PROGRAMS.search(cmd):
            found.append((pid, cmd))
            continue
        words = args.get(pid, "").split()[:2]   # node /…/dsh, python3 /…/aider
        hit = next((w for w in words[1:] if AGENT_PROGRAMS.search(w)), None) if words and re.search(r"(?i)(^|/)(node|bun|deno|python3?)$", words[0]) else None
        if hit:
            found.append((pid, os.path.basename(hit)))
    return found


def occupants(project, ours=(), session=None):
    """Who else is working on the project: [{why, label, pid?, cmd?}]. ours: the pids of the console's own agents (what
    they start is theirs). session: the console session asking (its own lock is not another's)."""
    out = []
    cur = read(project)
    if cur and not (cur.get("pid") == os.getpid() and cur.get("session") == session):
        out.append({"why": "console", "label": cur.get("label") or cur.get("kind") or "?", "pid": cur.get("pid"),
                    "session": cur.get("session"), "here": cur.get("pid") == os.getpid()})
    tree = _tree()
    roots = {int(p) for p in ours if p}
    try:
        import activity
        runs, _ = activity.runs(activity.read(project))
    except Exception:   # an unreadable log says nothing about who is working
        runs = []
    try:
        import feedback as F
        waiting = bool(F.listening(project).get("listening"))
    except Exception:
        waiting = False
    for r in runs:   # the desk itself is no work; bin/vh gate --wait is the agent waiting for this round (below)
        if r.get("state") == "running" and r.get("pid") and not _under(int(r["pid"]), roots, tree) and r.get("cmd") != "desk" \
                and not (waiting and r.get("cmd") == "gate"):
            out.append({"why": "command", "label": f"bin/vh {r.get('cmd')}", "pid": r.get("pid")})
    if waiting:
        out.append({"why": "waiting", "label": "bin/vh desk wait"})
    for pid, cmd in _agents_in(project, roots | {os.getpid()}, tree):
        out.append({"why": "process", "label": cmd, "pid": pid})
    return out
