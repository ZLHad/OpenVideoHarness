"""A client of the Agent Client Protocol over stdio, Python stdlib only: the console's side of a conversation with a
local agent (Claude Code, Codex, DeepSeek Harness through their ACP adapters).

An adapter runs as a child process in a clean environment (no API key, none of the host session's ANTHROPIC_BASE_URL or
CLAUDE_CODE_* variables) and its own process group, so stopping it stops whatever it started; acp_guard.py leads that
group and stops it if the desk dies without stopping it. The two sides speak JSON-RPC
2.0, one JSON object a line. This module knows the wire, not the conversation: agents.py does that.

  Peer(argv, env, on_note, on_request)  start an adapter; on_note(method, params) gets each notification, on_request(id,
                                        method, params) each request the agent sends (answer it later with reply/fail)
  peer.call(method, params, timeout)    a request; its result, or AcpError
  peer.notify(method, params)           a notification
  peer.close()                          stdin closed, then TERM to its group after a grace, then KILL to what is left of it
"""
import json, os, signal, subprocess, sys, threading, time
from collections import deque
from pathlib import Path

GUARD = Path(__file__).resolve().parent / "acp_guard.py"

# what the adapters need from the environment, and nothing else: the user's own login (in their home folder) does the rest
KEEP_ENV = ("HOME", "USER", "LOGNAME", "SHELL", "LANG", "TMPDIR", "PATH",
            # a proxy or a company's certificates the person's login goes through
            "HTTPS_PROXY", "HTTP_PROXY", "ALL_PROXY", "NO_PROXY", "https_proxy", "http_proxy", "all_proxy", "no_proxy",
            "NODE_EXTRA_CA_CERTS", "SSL_CERT_FILE", "SSL_CERT_DIR", "REQUESTS_CA_BUNDLE",
            # not a secret: "no password store" (tools/keys.py), so a console under tools/ci.sh starts agents that find no saved key
            "OVH_KEYSTORE")
# a key in the environment would bill the person's API account instead of using their subscription, and the host's
# session variables (a Claude Code running the desk) would point the agent at the host's own endpoint and state
DROP_PREFIX = ("ANTHROPIC_", "CLAUDE", "OPENAI_", "CODEX_", "DEEPSEEK_", "GEMINI_", "GOOGLE_API", "AWS_", "AZURE_")
MAX_LINE = 32 << 20   # one message: a session/load replays a long conversation as many lines, never one of this size


class AcpError(Exception):
    def __init__(self, message, code=None, data=None):
        super().__init__(message)
        self.code, self.data = code, data


def _alive(group):
    """Is any process of this process group left?"""
    try:
        os.killpg(group, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:   # someone's, not ours: nothing to wait for
        return False


def clean_env(extra=None):
    """The adapter's environment: the basics a login shell has, LC_* for the locale, TERM=dumb, and extra (DSH_HOME …).
    No variable that names a provider's key or the host agent's session survives, extra's included."""
    env = {k: os.environ[k] for k in KEEP_ENV if os.environ.get(k)}
    env.update({k: v for k, v in os.environ.items() if k.startswith("LC_")})
    env["TERM"] = "dumb"
    env.setdefault("LANG", "en_US.UTF-8")
    env.update(extra or {})
    for k in ("CLAUDE_CONFIG_DIR", "CODEX_HOME"):   # where the person's own settings live, when they moved them
        if os.environ.get(k) and k not in env:
            env[k] = os.environ[k]
    for k in list(env):
        if k in ("CLAUDE_CONFIG_DIR", "CODEX_HOME"):
            continue
        if k.upper().startswith(DROP_PREFIX) or "API_KEY" in k.upper() or k.upper().endswith(("_TOKEN", "_SECRET")):
            del env[k]
    return env


class Peer:
    def __init__(self, argv, env=None, cwd=None, on_note=None, on_request=None, on_exit=None, name="agent"):
        self.name = name
        self.on_note, self.on_request, self.on_exit = on_note, on_request, on_exit
        self._lock = threading.Lock()
        self._wlock = threading.Lock()
        self._next = 1
        self._pending = {}   # id → [event, message]
        self.stderr = deque(maxlen=60)   # its last lines, for "why did it stop"
        self.closing = False
        self.started = time.time()
        # under acp_guard.py, the leader of a group of its own: close() reaches all it started, and should the desk die
        # without a close (kill -9), the guard sees it and stops the group (DeepSeek Harness ignores the end of its input)
        guarded = [sys.executable, str(GUARD), str(os.getpid()), "--"] + list(argv)
        self.proc = subprocess.Popen(guarded, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     cwd=cwd, env=env if env is not None else clean_env(), bufsize=0,
                                     start_new_session=True)
        threading.Thread(target=self._read, name=f"acp-{name}-out", daemon=True).start()
        threading.Thread(target=self._read_err, name=f"acp-{name}-err", daemon=True).start()

    # ---------- the wire ----------
    def alive(self):
        return self.proc.poll() is None

    def _send(self, msg):
        data = (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        with self._wlock:
            try:
                self.proc.stdin.write(data)
                self.proc.stdin.flush()
            except (OSError, ValueError) as e:
                raise AcpError(f"{self.name} is not running ({type(e).__name__})") from None

    def call(self, method, params, timeout=120.0):
        """Send a request and wait for its answer: the result, or AcpError (its error, a timeout, the agent gone)."""
        with self._lock:
            rid = self._next
            self._next += 1
            slot = self._pending[rid] = [threading.Event(), None]
        try:
            self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
            if not slot[0].wait(timeout):
                raise AcpError(f"{method}: no answer in {timeout:g} s", code="timeout")
        finally:
            with self._lock:
                self._pending.pop(rid, None)
        msg = slot[1]
        if msg is None:
            raise AcpError(f"{self.name} stopped before it answered {method}", code="gone")
        if "error" in msg:
            err = msg["error"] if isinstance(msg["error"], dict) else {"message": str(msg["error"])}
            raise AcpError(str(err.get("message") or "error")[:400], code=err.get("code"), data=err.get("data"))
        return msg.get("result")

    def notify(self, method, params):
        self._send({"jsonrpc": "2.0", "method": method, "params": params})

    def reply(self, rid, result):
        self._send({"jsonrpc": "2.0", "id": rid, "result": result})

    def fail(self, rid, code, message):
        self._send({"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}})

    def _read(self):
        buf = b""
        out = self.proc.stdout
        while True:
            try:
                chunk = out.read1(1 << 16) if hasattr(out, "read1") else os.read(out.fileno(), 1 << 16)
            except (OSError, ValueError):
                chunk = b""
            if not chunk:
                break
            buf += chunk
            if len(buf) > MAX_LINE and b"\n" not in buf:   # a runaway line: drop it rather than hold it all
                buf = b""
                continue
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                self._dispatch(line)
        self._gone()

    def _dispatch(self, line):
        line = line.strip()
        if not line:
            return
        try:
            msg = json.loads(line.decode("utf-8", "replace"))
        except ValueError:
            self.stderr.append("(not JSON on stdout) " + line[:200].decode("utf-8", "replace"))
            return
        if not isinstance(msg, dict):
            return
        if "id" in msg and "method" not in msg:   # an answer to one of ours
            with self._lock:
                slot = self._pending.get(msg["id"])
            if slot:
                slot[1] = msg
                slot[0].set()
            return
        method, params = msg.get("method"), msg.get("params") if isinstance(msg.get("params"), dict) else {}
        if not isinstance(method, str):
            return
        try:
            if "id" in msg:
                if self.on_request:
                    self.on_request(msg["id"], method, params)
                else:
                    self.fail(msg["id"], -32601, f"the console does not handle {method}")
            elif self.on_note:
                self.on_note(method, params)
        except Exception as e:   # one bad message never stops the reader
            print(f"desk: agent {self.name}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)

    def _read_err(self):
        for raw in iter(self.proc.stderr.readline, b""):
            self.stderr.append(raw.decode("utf-8", "replace").rstrip()[:400])

    def _gone(self):
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        with self._lock:
            slots = list(self._pending.values())
        for s in slots:   # every call still waiting hears that it is gone
            s[0].set()
        if self.on_exit and not self.closing:
            try:
                self.on_exit(self.proc.returncode)
            except Exception as e:
                print(f"desk: agent {self.name}: {type(e).__name__}: {e}", file=sys.stderr, flush=True)

    def close(self, grace=1.5, term=4.0):
        """Stop it for good: stdin closed (an adapter that ends on EOF ends), TERM to its group after grace seconds (DSH
        does not end on EOF), then KILL to whatever is left of the group once it is empty or term seconds pass, whether the
        adapter ended by itself or not (a child of it may ignore TERM). Safe to call twice."""
        self.closing = True
        try:
            self.proc.stdin.close()
        except (OSError, ValueError):
            pass
        try:
            self.proc.wait(timeout=grace)
        except subprocess.TimeoutExpired:
            pass
        group = self.proc.pid   # the group: the adapter and what it started (Claude Code, the Codex app server)
        try:
            os.killpg(group, signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass
        end = time.time() + term
        while time.time() < end:   # until the whole group is gone: an adapter that ended on EOF may leave a child behind
            if self.proc.poll() is not None and not _alive(group):
                break
            time.sleep(0.1)
        try:   # whatever is left of the group, the adapter gone or not: a child that ignores TERM goes too
            os.killpg(group, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            self.proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            pass
        return self.proc.poll()
