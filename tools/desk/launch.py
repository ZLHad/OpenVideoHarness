"""Starting a desk in the background, showing its window, stopping one, and starting one again: what bin/vh studio,
bin/vh gate and bin/vh desk link do.

  start(project, roots, only, port, idle, print_address)   a desk in its own session (it outlives the caller) →
                                      (its address, None), (its address, "running") when another start got there first
                                      (one lock beside the info file: several starts at once give one desk), or (None,
                                      why). The address opens a page that only looks, unless print_address: then a
                                      one-time code is chosen here, handed to the desk on stdin, and in the address (ten
                                      minutes, one page); a desk another start made has no code of ours: (None, why)
  show(url, at)                       the running desk shows Studio's window at that place of the page (POST /api/open)
                                      → {opened, how, why}
  place(url, project)                 that project's place in the desk's page (/p/<key>), from its own listing, or None
  busy(info, project, roots)          is an agent in that desk's column in the middle of a turn?
  stop(info)                          stop that desk (TERM, then KILL)
  relink(project, roots, force, port, print_address)   stop the desk serving this project (or the console of these
                                      roots) and start it again alike, on the same port when it is free: every page of the
                                      old one can only look → (address, None) or (None, why)

Nothing these print or write holds the desk's token or a code. With print_address the address they return carries one,
and the caller writes it to the terminal alone (server.to_terminal), never to stdout, --json or a log.
"""
import fcntl, json, os, secrets, signal, subprocess, sys, time
from pathlib import Path
from urllib.parse import quote, urlsplit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import server     # noqa: E402
import agentlock  # noqa: E402

IDLE = 43200   # s: a background desk stops by itself after 12 h without a request (an open page asks every few seconds)


def _log(project, roots):
    if project:
        p = Path(project) / "out" / "review" / ".desk.log"
    else:
        info = server._info_path(None, roots)
        if info is None:
            return None
        p = info.with_suffix(".log")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _start_lock(project, roots):
    """The lock that makes "is one running? else start one" a single step: beside the desk's info file."""
    info = server._info_path(project, roots)
    if info is None:
        return None
    try:
        info.parent.mkdir(parents=True, exist_ok=True)
        f = open(info.with_name(info.name + ".lock"), "a")
        fcntl.flock(f, fcntl.LOCK_EX)
        return f
    except OSError:
        return None


def start(project=None, roots=(), only=False, port=None, idle=IDLE, print_address=False, owner=None):
    """A desk for this project (or the console over these roots) started through bin/vh in its own session, so its run is
    in the activity log and it outlives this command. → (its address, None); (its address, "running") when another start
    made it while this one waited for the lock; or (None, why). The address opens a page with access only with
    print_address (a one-time code this chose, handed to the desk on stdin)."""
    lock = _start_lock(project, roots)
    try:
        url = server.running(project, roots)
        if url:   # another start got there first
            return (None, "Studio started meanwhile, without this address: run this again once it has stopped") if print_address else (url, "running")
        return _start(project, roots, only, port, idle, print_address, owner)
    finally:
        if lock:
            lock.close()


def _start(project, roots, only, port, idle, print_address, owner):
    key = secrets.token_urlsafe(18) if print_address else None
    cmd = [os.environ.get("OVH_BASH") or "bash", str(ROOT / "bin" / "vh"), "desk"] + ([str(project)] if project else [])
    for r in roots:
        cmd += ["--root", str(r)]
    cmd += (["--only"] if only and project else []) + ["--idle", str(idle), "--no-open"] + (["--code-stdin"] if key else []) \
        + (["--port", str(port)] if port is not None else []) + (["--owner", owner] if owner else [])
    log = _log(project, roots)
    out = open(log, "ab") if log else subprocess.DEVNULL
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE if key else subprocess.DEVNULL, stdout=out, stderr=out, start_new_session=True)
    finally:
        if log:
            out.close()
    if key:
        try:
            p.stdin.write((key + "\n").encode())
            p.stdin.close()
        except OSError:
            pass
    for _ in range(300):
        url = server.running(project, roots)
        if url:
            return (f"{url}?c={key}" if key else url), None
        if p.poll() is not None:
            break
        time.sleep(0.1)
    where = f" ({os.path.relpath(log, project) if project else log} says why)" if log else ""
    return None, f"the desk did not come up{where}"


def show(url, at=""):
    """The desk at url shows Studio's window at that place of the page. → {opened, how, why}."""
    return server.ask_open(url, at)


def place(url, project):
    """The project's place in the page of the desk at url (/p/<key>), from that desk's own listing (the key it gives the
    folder); None when it does not list that folder."""
    import http.client
    u = urlsplit(url)
    try:
        c = http.client.HTTPConnection("127.0.0.1", u.port, timeout=30)
        c.request("GET", "/api/projects", headers={"Host": f"127.0.0.1:{u.port}"})
        r = c.getresponse()
        rows = json.loads(r.read()).get("projects") or []
        c.close()
    except (OSError, ValueError, AttributeError):
        return None
    real = os.path.realpath(str(project))
    for row in rows:
        if os.path.realpath(row.get("path") or "") == real and row.get("key"):
            return "/p/" + quote(row["key"], safe="")
    return None


def turn_running(project, info):
    """Is a conversation in this desk's agent column in the middle of a turn on this project (it holds the project's lock)?"""
    if not project:
        return False
    cur = agentlock.read(project)
    return bool(cur) and cur.get("pid") == info.get("pid")


def busy(info, project=None, roots=()):
    """Is an agent in this desk's column in the middle of a turn: on its project, or (a console) on any project under its
    roots?"""
    if project:
        return turn_running(project, info)
    try:
        import projects as PJ
        rows = PJ.listing(list(info.get("roots") or roots))["projects"]
    except (Exception, SystemExit):
        return False
    return any(turn_running(Path(r["path"]), info) for r in rows)


def stop(info, wait=15.0):
    """Stop the desk this info names (TERM; KILL when it is still there after wait seconds). True when it is gone."""
    pid = int(info.get("pid") or 0)
    if not pid:
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    end = time.time() + wait
    while time.time() < end:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        except PermissionError:
            return False
        time.sleep(0.1)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    time.sleep(0.3)
    return True


def relink(project=None, roots=(), force=False, port=None, print_address=False):
    """The running desk stops (its conversations are read back from their logs) and starts again alike, on the same port
    when it is free; every page of the old run can only look (its button brings the new window). A turn in the agent
    column stops it only with force. → (address, None), or (None, why)."""
    project = Path(project).resolve() if project else None
    roots = [os.path.realpath(str(r)) for r in roots]
    info = server.running_info(project, roots)
    only = bool(project) and (info.get("only", True) if info else True)
    if info:
        if busy(info, project, roots) and not force:
            return None, ("an agent in the console's column is in the middle of a turn: let it finish or stop it there, then run "
                          "this again (--force stops it now)")
        roots = info.get("roots") or roots
        port = info.get("port") if port is None else port
        if not stop(info):
            return None, f"the desk (pid {info.get('pid')}) could not be stopped"
    owner = info.get("owner") if info else None
    url, why = start(project, roots, only, port, IDLE, print_address, owner)
    if url is None and port is not None and info:   # its old port taken in the meantime: any free one
        url, why = start(project, roots, only, None, IDLE, print_address, owner)
    return url, why
