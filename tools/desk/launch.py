"""Starting a desk in the background with a launch key of its own, and starting one again with a new key: what bin/vh gate
does at a stop, and what bin/vh desk link does when a link was used up or lost.

  start(project, roots, only, port)   a desk in its own session (it outlives the caller), its key on stdin → (url?k=…, None)
                                      or (None, why)
  relink(project, roots, force)       stop the desk serving this project (or the console of these roots), start it again
                                      alike on the same port when it is free → (url?k=…, None) or (None, why)

The key goes to the desk on stdin and into the caller's output, never into a file in the project (an agent working there
can read those): the page that comes with it is the one that gets the desk's token.
"""
import os, secrets, signal, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
import server     # noqa: E402
import agentlock  # noqa: E402

IDLE = 43200   # s: a background desk stops by itself after 12 h without a request


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


def start(project=None, roots=(), only=False, port=None, idle=IDLE):
    """A desk for this project (or the console over these roots) started through bin/vh in its own session, so its run is
    in the activity log and it outlives this command. → (its address with ?k=<key>, None), or (None, why)."""
    key = secrets.token_urlsafe(18)
    cmd = [os.environ.get("OVH_BASH") or "bash", str(ROOT / "bin" / "vh"), "desk"] + ([str(project)] if project else [])
    for r in roots:
        cmd += ["--root", str(r)]
    cmd += (["--only"] if only and project else []) + ["--idle", str(idle), "--key-stdin"] + (["--port", str(port)] if port is not None else [])
    log = _log(project, roots)
    out = open(log, "ab") if log else subprocess.DEVNULL
    try:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=out, start_new_session=True)
    finally:
        if log:
            out.close()
    try:
        p.stdin.write((key + "\n").encode())
        p.stdin.close()
    except OSError:
        pass
    for _ in range(200):
        url = server.running(project, roots)
        if url:
            return f"{url}?k={key}", None
        if p.poll() is not None:
            break
        time.sleep(0.1)
    where = f" ({os.path.relpath(log, project) if project else log} says why)" if log else ""
    return None, f"the desk did not come up{where}"


def turn_running(project, info):
    """Is a conversation in this desk's agent column in the middle of a turn on this project (it holds the project's lock)?"""
    if not project:
        return False
    cur = agentlock.read(project)
    return bool(cur) and cur.get("pid") == info.get("pid")


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


def relink(project=None, roots=(), force=False, port=None):
    """The way out when a link is used up, lost or was opened by someone else: the running desk stops (its conversations
    are read back from their logs) and starts again alike, on the same port when it is free, with a new key; every token
    of the old one is void. A turn in the agent column stops it only with force. → (url?k=…, None), or (None, why)."""
    project = Path(project).resolve() if project else None
    roots = [os.path.realpath(str(r)) for r in roots]
    info = server.running_info(project, roots)
    only = bool(project) and (info.get("only", True) if info else True)
    if info:
        if turn_running(project, info) and not force:
            return None, ("an agent in the console's column is in the middle of a turn on this project: let it finish or stop it "
                          "there, then run this again (--force stops it now)")
        roots = info.get("roots") or roots
        port = info.get("port") if port is None else port
        if not stop(info):
            return None, f"the desk (pid {info.get('pid')}) could not be stopped"
    url, why = start(project, roots, only, port)
    if url is None and port is not None and info:   # its old port taken in the meantime: any free one
        url, why = start(project, roots, only, None)
    return url, why
