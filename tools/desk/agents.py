"""The console's agents: a session manager inside bin/vh desk that talks to the agents installed on this machine (Claude
Code, Codex, DeepSeek Harness) through their ACP adapters (acp.py), one long-running adapter process per kind of agent,
started the first time someone talks to it.

A conversation is a Session: one project folder (the agent's working folder), one kind of agent. Everything that happens in
it is an event, appended to <project>/.ovh/agents/<id>.jsonl and pushed to the open pages (server.py, SSE): what the person
typed, every update the agent sends (its text as it comes, its thoughts, each tool call and its changes, its plan, the
context it uses and what it costs), each request to approve something and how it was answered, each turn's start and end.
A page that opens later, or again, reads the events it missed; a request nobody answered yet is there again.

What the person may do, and only the page's own buttons do it (server.py checks the token, the origin and the folder):
  say      the text typed in the box, sent as the person's words (nothing from a project file or the agent's output is ever
           sent in their name: the server takes the text from the request body and nothing else)
  answer   one of the options the agent offered for a request still waiting; no page connected: the request waits, and
           after APPROVAL_TIMEOUT seconds without one it is answered as rejected, never allowed
  stop     every waiting request answered cancelled first, then the turn cancelled
  mode, config   the session's mode, model or reasoning effort, among those the agent offered

Defaults are the person's own, as in their terminal: the agent starts with their settings (mode, allow rules, skills,
model); the page shows them and can change them per session. With personal settings off (Claude Code only), the session
starts from the project's settings alone.

Installed adapters live outside the repo, in $OVH_AGENTS_DIR or $XDG_CACHE_HOME/ovh/agents (~/.cache/ovh/agents), one
folder a kind, each package pinned (ADAPTERS): bin/vh desk agents install <kind>.
"""
import json, os, re, shutil, subprocess, sys, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import acp         # noqa: E402
import agentlock   # noqa: E402

PROTOCOL = 1
APPROVAL_TIMEOUT = float(os.environ.get("OVH_AGENT_APPROVAL_TIMEOUT") or 600)   # s without a page before a request is rejected
TURN_TIMEOUT = 6 * 3600.0
MAX_TEXT = 4000      # characters: what a page sees of a tool's output, a command's text …
MAX_DIFF = 40000     # characters of a diff's old or new text
MAX_PROMPT = 20000   # characters the person may send at once
ID_RE = re.compile(r"^[a-f0-9]{32}$")

# the adapters: the npm package that speaks ACP for each agent, pinned. size: on disk after install (macOS arm64, 2026-11-16)
ADAPTERS = {
    "claude": {"label": "Claude Code", "package": "@agentclientprotocol/claude-agent-acp", "version": "0.107.0",
               "bin": "claude-agent-acp", "args": [], "login": "`claude` works in your terminal", "size": "≈ 0.4 GB",
               "settings_toggle": True},
    "codex": {"label": "Codex", "package": "@agentclientprotocol/codex-acp", "version": "2.6.0",
              "bin": "codex-acp", "args": [], "login": "`codex` works in your terminal", "size": "≈ 0.4 GB"},
    "dsh": {"label": "DeepSeek Harness", "package": "@deepseek-ai/dsh", "version": "0.2.2-rc.3",
            "bin": "dsh", "args": ["--profile", "acp"], "login": "DeepSeek Harness (its desktop app) is signed in", "size": "≈ 1.4 GB"},
}
ORDER = ("claude", "codex", "dsh")


def home():
    """Where the adapters are installed: $OVH_AGENTS_DIR, else $XDG_CACHE_HOME/ovh/agents (~/.cache/ovh/agents)."""
    d = os.environ.get("OVH_AGENTS_DIR")   # absolute: the adapter starts in it, so a relative path would not find itself
    if d:
        return Path(d).expanduser().absolute()
    return (Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "ovh" / "agents").absolute()


def installed(kind):
    """{"path", "version"} of the adapter installed for this kind, or None."""
    a = ADAPTERS[kind]
    base = home() / kind
    exe = base / "node_modules" / ".bin" / a["bin"]
    if not os.access(exe, os.X_OK):
        return None
    try:
        v = json.loads((base / "node_modules" / a["package"] / "package.json").read_text(encoding="utf-8")).get("version")
    except (OSError, ValueError):
        v = None
    return {"path": str(exe), "version": v}


def catalog():
    """Each kind of agent: {kind, label, installed, version, pinned, size, install}: what the column's picker lists."""
    out = []
    for k in ORDER:
        a, got = ADAPTERS[k], installed(k)
        out.append({"kind": k, "label": a["label"], "installed": bool(got), "version": (got or {}).get("version"),
                    "pinned": a["version"], "outdated": bool(got and got.get("version") and got["version"] != a["version"]),
                    "size": a["size"], "install": f"bin/vh desk agents install {k}", "settings_toggle": bool(a.get("settings_toggle"))})
    return out


# ---------- the person's own defaults (read only) ----------

def dsh_user_defaults():
    """DeepSeek Harness desktop's default provider, model and reasoning effort ({} when there is none): the block
    'id: agent-default-model' of ~/.dsh/profiles/desktop/cordis.patch.yml, read for those three values and nothing else."""
    p = Path.home() / ".dsh" / "profiles" / "desktop" / "cordis.patch.yml"
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return {}
    out, inside = {}, False
    for line in text.splitlines():
        if re.match(r"^- ", line):
            inside = bool(re.match(r"^-\s+id:\s*agent-default-model\s*$", line))
            continue
        if inside:
            m = re.match(r"^\s+(provider|model|reasoningEffort):\s*['\"]?([\w.\-]+)['\"]?\s*$", line)
            if m:
                out[m.group(1)] = m.group(2)
    return out


def dsh_profile(base):
    """Write the profile the console starts DeepSeek Harness with: under its own DSH_HOME (base/home), never the person's
    ~/.dsh; their credentials file is named in place (read, not copied), telemetry is off, the default model is theirs."""
    prof = base / "home" / "profiles" / "acp"
    prof.mkdir(parents=True, exist_ok=True)
    d = dsh_user_defaults()
    provider, model = d.get("provider") or "deepseek-official", d.get("model") or "deepseek-v4-flash"
    cred = Path.home() / ".dsh" / ".credentials.yaml"
    (prof / "package.json").write_text(json.dumps({"name": "dsh-profile-acp", "private": True, "dependencies": {},
                                                   "dsh": {"profile": {"bundles": ["@deepseek-ai/dsh-base"]}}}) + "\n")
    (prof / "cordis.yml").write_text("# the profile's root: an empty list; the patches compose it (bin/vh desk agents install dsh)\n[]\n")
    (prof / "cordis.patch.yml").write_text(
        "# Written by bin/vh desk agents install dsh. The console's own profile: the person's DeepSeek Harness credentials\n"
        "# are read where they are (not copied); this folder is not their ~/.dsh.\n"
        f"- id: credentials\n  config:\n    path: {json.dumps(str(cred))}\n"
        "- id: hmr\n  disabled: true\n"
        f"- insert:\n    - id: acp\n      name: '@deepseek-ai/dsh-acp'\n      config:\n        provider: {provider}\n        model: {model}\n")
    return prof


def install(kind, out=sys.stdout):
    """npm install the pinned adapter into home()/<kind> (outside the repo). → exit code."""
    a = ADAPTERS[kind]
    npm = shutil.which("npm")
    if not npm:
        print("desk agents: npm not found (it comes with node: brew install node)", file=sys.stderr)
        return 2
    base = home() / kind
    base.mkdir(parents=True, exist_ok=True)
    (base / "package.json").write_text(json.dumps({"name": f"ovh-agent-{kind}", "private": True,
                                                   "dependencies": {a["package"]: a["version"]}}, indent=1) + "\n")
    print(f"desk agents: installing {a['package']}@{a['version']} into {base} ({a['size']}) …", file=out, flush=True)
    r = subprocess.run([npm, "install", "--no-audit", "--no-fund", "--loglevel=error", "--save-exact"], cwd=str(base),
                       env=dict(os.environ, npm_config_update_notifier="false"))
    if r.returncode != 0:
        print(f"desk agents: npm install failed (exit {r.returncode})", file=sys.stderr)
        return 1
    if kind == "dsh":
        dsh_profile(base)
    got = installed(kind)
    if not got:
        print(f"desk agents: installed, but {a['bin']} is not in {base}/node_modules/.bin", file=sys.stderr)
        return 1
    print(f"desk agents: {a['label']} ready ({got['version']}). It uses your own login: if {a['login']}, it works in the console.", file=out)
    return 0


def command(kind):
    """(argv, extra env) that start this kind's adapter, or None when it is not installed."""
    a, got = ADAPTERS[kind], installed(kind)
    if not got:
        return None
    extra = {}
    if kind == "dsh":
        base = home() / kind
        if not (base / "home" / "profiles" / "acp" / "cordis.patch.yml").exists():
            dsh_profile(base)
        extra = {"DSH_HOME": str(base / "home"), "DSH_TELEMETRY_DISABLED": "1"}
    return [got["path"]] + list(a["args"]), extra


# ---------- what a page sees ----------

def _clip(s, n):
    return s if len(s) <= n else s[:n] + f"\n…（还有 {len(s) - n} 字）"


def clean(obj, root, n=MAX_TEXT, depth=0):
    """An update as the log keeps it: the project's own folder written as a relative path, the home folder as ~, long
    strings clipped (a diff's texts less so), the bulky echoes dropped (Claude's toolResponse repeats the file)."""
    if depth > 12:
        return None
    if isinstance(obj, str):
        if root:
            obj = obj.replace(root + "/", "").replace(root, ".")
        h = str(Path.home())
        if h and len(h) > 1:
            obj = obj.replace(h + "/", "~/")
        return _clip(obj, n)
    if isinstance(obj, list):
        return [clean(x, root, n, depth + 1) for x in obj[:200]]
    if isinstance(obj, dict):
        out = {}
        for k, v in list(obj.items())[:80]:
            if k in ("toolResponse", "sessionId"):
                continue
            out[k] = clean(v, root, MAX_DIFF if k in ("oldText", "newText") else n, depth + 1)
        return out
    return obj


def option_kind(opts, option_id):
    for o in opts:
        if isinstance(o, dict) and o.get("optionId") == option_id:
            return o.get("kind")
    return None


class Unavailable(Exception):
    """An agent cannot be used: not installed, would not start, refused the session. code is for the page's words."""
    def __init__(self, code, message=""):
        super().__init__(message or code)
        self.code = code


class Busy(Exception):
    def __init__(self, who):
        super().__init__("busy")
        self.who = who


# ---------- one conversation ----------

class Session:
    def __init__(self, mgr, kind, project, key, sid=None, header=None, events=None):
        self.mgr, self.kind, self.project, self.key = mgr, kind, Path(project), key
        self.id = sid or uuid.uuid4().hex
        self.root = os.path.realpath(str(project))
        self.log = self.project / ".ovh" / "agents" / f"{self.id}.jsonl"
        self.cond = threading.Condition()
        self.events = events or []
        self.seq = self.events[-1]["seq"] if self.events else 0
        self.header = header or {}
        self.acp_id = self.header.get("acp_id")
        self.personal = self.header.get("personal", True)
        self.live = False          # attached to a session in the running adapter
        self.running = False       # a turn in flight
        self.stopping = False
        self.replaying = False     # a session/load is replaying history we already have
        self.pending = {}          # our request id → {"agent": its JSON-RPC id, "options": [...], "detached": t | None}
        self.config = {}           # modes, configOptions, models: what the agent said last
        self.subscribers = 0
        self._n = 0
        self._attach_lock = threading.RLock()   # attach → set_config (DSH defaults) → attach
        self._say_lock = threading.Lock()
        for e in self.events:      # the state an old log ends in: what the page shows before it talks again
            if e.get("type") == "state":
                self.config.update({k: v for k, v in e.items() if k in ("modes", "configOptions", "models")})

    # ---------- the log ----------
    def emit(self, type_, **fields):
        with self.cond:
            self.seq += 1
            ev = {"seq": self.seq, "t": round(time.time(), 3), "type": type_, **fields}
            self.events.append(ev)
            try:
                self.log.parent.mkdir(parents=True, exist_ok=True)
                with open(self.log, "a", encoding="utf-8") as f:
                    f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            except OSError:
                pass   # a project that cannot be written still talks; the page has the events while the desk runs
            self.cond.notify_all()
        return ev

    def after(self, seq):
        with self.cond:
            return [e for e in self.events if e["seq"] > seq]

    def summary(self):
        title = next((e["u"].get("title") for e in reversed(self.events) if e.get("type") == "update"
                      and isinstance(e.get("u"), dict) and e["u"].get("sessionUpdate") == "session_info_update" and e["u"].get("title")), None)
        first = next((e.get("text") for e in self.events if e.get("type") == "user"), None)
        last = self.events[-1]["t"] if self.events else self.header.get("created")
        return {"id": self.id, "kind": self.kind, "label": ADAPTERS[self.kind]["label"], "title": title, "first": (first or "")[:80],
                "created": self.header.get("created"), "last": last, "live": self.live, "running": self.running,
                "pending": len(self.pending), "personal": self.personal, "turns": sum(1 for e in self.events if e.get("type") == "user")}

    # ---------- attaching to the adapter ----------
    def attach(self):
        """A session in the running adapter for this conversation: the one it had (load or resume, as the agent can),
        else a new one. Raises Unavailable."""
        with self._attach_lock:
            if self.live and self.mgr.peers.get(self.kind) is not None:
                return
            peer, caps = self.mgr.peer(self.kind)
            params = {"cwd": self.root, "mcpServers": []}
            meta = self._meta()
            res, how = None, "new"
            if self.acp_id:
                sc = caps.get("sessionCapabilities") or {}
                try:
                    if caps.get("loadSession"):
                        self.replaying = True
                        res, how = peer.call("session/load", dict(params, sessionId=self.acp_id, **({"_meta": meta} if meta else {})), 120), "load"
                    elif "resume" in sc:
                        res, how = peer.call("session/resume", dict(params, sessionId=self.acp_id), 120), "resume"
                except acp.AcpError:
                    res = None
                finally:
                    self.replaying = False
                if res is None and how in ("load", "resume"):
                    how = "fresh"
            if res is None:
                try:
                    res = peer.call("session/new", dict(params, **({"_meta": meta} if meta else {})), 180)
                except acp.AcpError as e:
                    raise Unavailable("session_refused", str(e))
                if not isinstance(res, dict) or not res.get("sessionId"):
                    raise Unavailable("session_refused", "no sessionId")
                if self.acp_id:
                    self.emit("notice", code="fresh")   # the agent will not remember what was said before
                self.acp_id = res["sessionId"]
                self._header()
            self.mgr.by_acp[(self.kind, self.acp_id)] = self
            self.live = True
            self._state(res if isinstance(res, dict) else {})
            if self.mgr.auth.get(self.kind) == "unauthenticated":
                self.emit("notice", code="signed_out")
            if how == "new" and self.kind == "dsh":
                self._dsh_defaults()

    def _meta(self):
        """What session/new carries besides the folder: with personal settings off, Claude Code reads only the project's
        settings (its user settings, skills, allow rules and CLAUDE.md stay out)."""
        if self.kind == "claude" and not self.personal:
            return {"claudeCode": {"options": {"settingSources": ["project", "local"]}}}
        return None

    def _header(self):
        self.header.update(kind=self.kind, acp_id=self.acp_id, personal=self.personal, created=self.header.get("created") or time.time())
        try:
            self.log.parent.mkdir(parents=True, exist_ok=True)
            (self.log.parent / f"{self.id}.json").write_text(json.dumps(dict(self.header, id=self.id), ensure_ascii=False))
        except OSError:
            pass

    def _state(self, res):
        st = {k: res[k] for k in ("modes", "configOptions", "models") if isinstance(res.get(k), (dict, list))}
        if st:
            self.config.update(st)
            self.emit("state", **clean(st, self.root))

    def _dsh_defaults(self):
        """DeepSeek Harness desktop's reasoning effort, as the person set it there (the model is in the profile already)."""
        want = dsh_user_defaults().get("reasoningEffort")
        for o in self.config.get("configOptions") or []:
            if isinstance(o, dict) and o.get("id") == "reasoning_effort" and want and o.get("currentValue") != want \
                    and any(isinstance(x, dict) and x.get("value") == want for x in o.get("options") or []):
                try:
                    self.set_config("reasoning_effort", want, by="defaults")
                except Unavailable:
                    pass

    # ---------- from the agent ----------
    def on_update(self, u):
        if self.replaying or not isinstance(u, dict):
            return
        kind = u.get("sessionUpdate")
        if kind == "available_commands_update":   # the person's skills, by name: counted, not kept
            u = {"sessionUpdate": kind, "count": len(u.get("availableCommands") or [])}
        elif kind == "current_mode_update" and isinstance(self.config.get("modes"), dict):
            self.config["modes"] = dict(self.config["modes"], currentModeId=u.get("currentModeId"))
        elif kind == "config_option_update" and isinstance(u.get("configOptions"), list):
            self.config["configOptions"] = u["configOptions"]
        self.emit("update", u=clean(u, self.root))

    def on_permission(self, agent_rid, params):
        """The agent asks before it does something: a card on the page, the agent waiting until the person answers."""
        self._n += 1
        rid = f"r{self._n}-{uuid.uuid4().hex[:8]}"
        opts = [o for o in (params.get("options") or []) if isinstance(o, dict) and isinstance(o.get("optionId"), str)]
        with self.cond:
            self.pending[rid] = {"agent": agent_rid, "options": opts, "detached": None if self.subscribers else time.time()}
        self.emit("permission", rid=rid, tool=clean(params.get("toolCall") or {}, self.root),
                  options=[{"optionId": o["optionId"], "name": str(o.get("name") or "")[:120], "kind": o.get("kind")} for o in opts])

    def _answer(self, rid, outcome, by):
        with self.cond:
            p = self.pending.pop(rid, None)
        if p is None:
            return False
        peer = self.mgr.peers.get(self.kind)
        try:
            if peer is not None:
                peer.reply(p["agent"], {"outcome": outcome})
        except acp.AcpError:
            pass
        oid = outcome.get("optionId")
        self.emit("answered", rid=rid, option=oid, kind=option_kind(p["options"], oid) if oid else "cancelled", by=by)
        return True

    def answer(self, rid, option_id):
        """The person picked one of the options offered for a request that still waits. → True; ValueError otherwise."""
        with self.cond:
            p = self.pending.get(rid)
        if p is None:
            raise ValueError("this request was answered already, or is gone")
        if not any(o["optionId"] == option_id for o in p["options"]):
            raise ValueError("not one of the options the agent offered")
        return self._answer(rid, {"outcome": "selected", "optionId": option_id}, "person")

    def reject_waiting(self, by):
        """Each waiting request answered: rejected where the agent offered a rejection, else cancelled (timeout, the agent
        or the desk going away); never allowed."""
        for rid in list(self.pending):
            p = self.pending.get(rid)
            if not p:
                continue
            rej = next((o["optionId"] for o in p["options"] if o.get("kind") == "reject_once"), None)
            self._answer(rid, {"outcome": "selected", "optionId": rej} if rej and by == "timeout" else {"outcome": "cancelled"}, by)

    # ---------- from the person ----------
    def say(self, text, scope=None, despite_waiting=False):
        """A turn with the person's words. Raises Busy (a turn runs, or someone else works on the project: an agent waiting
        for this round's review is let through when the person said so, despite_waiting), Unavailable."""
        with self._say_lock:
            if self.running:
                raise Busy([{"why": "turn", "label": ADAPTERS[self.kind]["label"]}])
            who = agentlock.occupants(self.project, self.mgr.adapter_pids(), self.id)
            if who and not (despite_waiting and all(w["why"] == "waiting" for w in who)):
                raise Busy(who)
            self.attach()
            got = agentlock.acquire(self.project, {"kind": self.kind, "label": ADAPTERS[self.kind]["label"], "session": self.id,
                                                   "desk": self.mgr.url})
            if got is not True:
                raise Busy([dict(got, why="console")])
            self.running, self.stopping = True, False
        self.emit("user", text=text, **({"scope": scope} if scope else {}))
        self.emit("turn", state="start")
        prompt = [{"type": "text", "text": text}]
        if scope:   # what the person had selected in the console: named by the page's own words, not the project's
            prompt.append({"type": "text", "text": scope_note(scope)})
        threading.Thread(target=self._turn, args=(prompt,), name=f"turn-{self.id[:6]}", daemon=True).start()

    def _turn(self, prompt):
        res, err = None, None
        try:
            peer = self.mgr.peers.get(self.kind)
            if peer is None:
                raise acp.AcpError("the agent stopped", code="gone")
            res = peer.call("session/prompt", {"sessionId": self.acp_id, "prompt": prompt}, TURN_TIMEOUT)
        except acp.AcpError as e:
            err = str(e)[:300]
        finally:
            self.reject_waiting("turn_end")
            agentlock.release(self.project, self.id)
            self.running, self.stopping = False, False
        res = res if isinstance(res, dict) else {}
        self.emit("turn", state="end", stop=res.get("stopReason") or ("error" if err else None), usage=clean(res.get("usage") or {}, self.root),
                  **({"error": err} if err else {}))

    def stop(self):
        """Stop the turn: every waiting request answered cancelled first (the protocol's order), then the cancel."""
        self.reject_waiting("stop")
        if not self.running:
            return False
        self.stopping = True
        self.emit("notice", code="stopping")
        peer = self.mgr.peers.get(self.kind)
        if peer is not None and self.acp_id:
            try:
                peer.notify("session/cancel", {"sessionId": self.acp_id})
            except acp.AcpError:
                pass
        return True

    def set_mode(self, mode_id):
        modes = self.config.get("modes") or {}
        ids = [m.get("id") for m in modes.get("availableModes") or [] if isinstance(m, dict)]
        if mode_id not in ids:
            raise ValueError("not one of the modes the agent offered")
        self.attach()
        try:
            self.mgr.peers[self.kind].call("session/set_mode", {"sessionId": self.acp_id, "modeId": mode_id}, 30)
        except (acp.AcpError, KeyError) as e:
            raise Unavailable("refused", str(e))
        self.config["modes"] = dict(modes, currentModeId=mode_id)
        self.emit("state", modes=clean(self.config["modes"], self.root), by="person")

    def set_config(self, config_id, value, by="person"):
        opts = self.config.get("configOptions") or []
        o = next((x for x in opts if isinstance(x, dict) and x.get("id") == config_id), None)
        if o is None:
            raise ValueError("not a setting the agent offered")
        flat = []
        for x in o.get("options") or []:
            flat += x.get("options") if isinstance(x, dict) and isinstance(x.get("options"), list) else [x]
        if o.get("type") == "select" and value not in [x.get("value") for x in flat if isinstance(x, dict)]:
            raise ValueError("not one of the values the agent offered")
        self.attach()
        try:
            res = self.mgr.peers[self.kind].call("session/set_config_option", {"sessionId": self.acp_id, "configId": config_id, "value": value}, 30)
        except (acp.AcpError, KeyError) as e:
            raise Unavailable("refused", str(e))
        if isinstance(res, dict) and isinstance(res.get("configOptions"), list):
            self.config["configOptions"] = res["configOptions"]
        else:
            o["currentValue"] = value
        self.emit("state", configOptions=clean(self.config["configOptions"], self.root), by=by)

    def gone(self, code):
        """The adapter stopped: what waited is cancelled, the turn ends, the next word starts it again."""
        self.live = False
        self.reject_waiting("agent_gone")   # the turn in flight ends by itself: its call hears the adapter is gone
        self.emit("notice", code="agent_gone", exit=code)


def scope_note(scope):
    """The console's note of what the person had selected, built from its kind and id alone (never a label taken from a
    project file): "(In the console the person had selected: shot S4, 0:12–0:18.)"."""
    kind = str(scope.get("kind") or "")[:20]
    ident = re.sub(r"[^\w.:~+-]", "", str(scope.get("id") or ""))[:60]

    def t(x):
        return f"{int(x // 60)}:{x % 60:04.1f}" if isinstance(x, (int, float)) and x == x and 0 <= x < 1e6 else None
    parts = [f"{kind} {ident}".strip()] if kind or ident else []
    a, b = t(scope.get("t")), t(scope.get("t1"))
    if a:
        parts.append(f"{a}–{b}" if b else a)
    mod = re.sub(r"[^\w-]", "", str(scope.get("module") or ""))[:20]
    if mod:
        parts.append(f"module {mod}")
    return "(In the console the person had selected: " + ", ".join(parts) + ".)" if parts else ""


# ---------- the manager: one per desk ----------

class Manager:
    def __init__(self, url=""):
        self.url = url
        self.peers = {}        # kind → acp.Peer
        self.caps = {}         # kind → initialize's agentCapabilities (and agentInfo)
        self.auth = {}         # kind → "authenticated" | "unauthenticated", as the adapter said last (auth/status_update)
        self.sessions = {}     # our id → Session
        self.by_acp = {}       # (kind, acp session id) → Session
        self._lock = threading.RLock()
        self._starting = {k: threading.Lock() for k in ADAPTERS}
        self.closed = False
        threading.Thread(target=self._watch, name="agents-watch", daemon=True).start()

    def adapter_pids(self):
        return [p.proc.pid for p in self.peers.values() if p is not None]

    def peer(self, kind):
        """The running adapter for this kind (started and initialized the first time) and its capabilities."""
        if self.closed:
            raise Unavailable("closing")
        with self._starting[kind]:
            p = self.peers.get(kind)
            if p is not None and p.alive():
                return p, self.caps.get(kind) or {}
            cmd = command(kind)
            if cmd is None:
                raise Unavailable("not_installed")
            argv, extra = cmd
            try:
                p = acp.Peer(argv, env=acp.clean_env(extra), cwd=str(home()), name=kind,
                             on_note=lambda m, prm, k=kind: self._note(k, m, prm),
                             on_request=lambda rid, m, prm, k=kind: self._request(k, rid, m, prm),
                             on_exit=lambda code, k=kind: self._exit(k, code))
            except OSError as e:
                raise Unavailable("no_start", str(e))
            try:
                res = p.call("initialize", {"protocolVersion": PROTOCOL,
                                            "clientCapabilities": {"fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False},
                                            "clientInfo": {"name": "ovh-desk", "title": "OpenVideoHarness console", "version": "1"}}, 90)
            except acp.AcpError as e:
                tail = " / ".join(list(p.stderr)[-3:])
                p.close(0.2, 1.0)
                raise Unavailable("no_start", (str(e) + (" — " + tail if tail else ""))[:500])
            caps = dict((res or {}).get("agentCapabilities") or {}, agentInfo=(res or {}).get("agentInfo") or {})
            self.peers[kind], self.caps[kind] = p, caps
            return p, caps

    def _note(self, kind, method, params):
        if method == "auth/status_update":   # signed in or not: the state only (the account's name and email are not kept)
            state = params.get("state") if isinstance(params.get("state"), str) else None
            if state and state != self.auth.get(kind):
                self.auth[kind] = state
                if state == "unauthenticated":
                    for s in list(self.sessions.values()):
                        if s.kind == kind and s.live:
                            s.emit("notice", code="signed_out")
            return
        if method != "session/update":
            return   # the adapters' own extensions: not part of the conversation
        s = self.by_acp.get((kind, params.get("sessionId")))
        if s is not None:
            s.on_update(params.get("update"))

    def _request(self, kind, rid, method, params):
        p = self.peers.get(kind)
        s = self.by_acp.get((kind, params.get("sessionId")))
        if method == "session/request_permission" and s is not None:
            s.on_permission(rid, params)
            return
        if p is not None:   # the files and terminals are the agent's own business: the console offers none
            p.fail(rid, -32601, f"the console does not handle {method}")
        if s is not None and method not in ("session/request_permission",):
            s.emit("notice", code="unsupported", method=str(method)[:60])

    def _exit(self, kind, code):
        self.peers.pop(kind, None)
        for s in list(self.sessions.values()):
            if s.kind == kind and s.live:
                s.gone(code)

    # ---------- sessions ----------
    def open(self, project, key, kind, personal=True):
        if kind not in ADAPTERS:
            raise ValueError("unknown agent")
        s = Session(self, kind, project, key, header={"created": time.time(), "personal": bool(personal)})
        s._header()
        with self._lock:
            self.sessions[s.id] = s
        return s

    def get(self, sid, project=None, key=None):
        """A session by id: live in this desk, or read back from its project's log (project given)."""
        if not isinstance(sid, str) or not ID_RE.match(sid):
            return None
        with self._lock:
            s = self.sessions.get(sid)
            if s is not None:
                return s if project is None or os.path.realpath(str(project)) == s.root else None
            if project is None:
                return None
            d = Path(project) / ".ovh" / "agents"
            try:
                header = json.loads((d / f"{sid}.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return None
            if header.get("kind") not in ADAPTERS:
                return None
            events = []
            try:
                for line in (d / f"{sid}.jsonl").read_text(encoding="utf-8").splitlines():
                    try:
                        e = json.loads(line)
                    except ValueError:
                        continue
                    if isinstance(e, dict) and isinstance(e.get("seq"), int):
                        events.append(e)
            except OSError:
                pass
            # a request that waited when the desk stopped was answered by nobody: its agent is gone with it
            open_ = {e.get("rid") for e in events if e.get("type") == "permission"} - {e.get("rid") for e in events if e.get("type") == "answered"}
            s = Session(self, header["kind"], project, key, sid=sid, header=header, events=events)
            for rid in open_:
                s.emit("answered", rid=rid, option=None, kind="cancelled", by="desk_restart")
            if events and any(e.get("type") == "turn" for e in events):
                last = [e for e in events if e.get("type") == "turn"][-1]
                if last.get("state") == "start":
                    s.emit("turn", state="end", stop="error", error="desk_restart")
            self.sessions[sid] = s
            return s

    def listing(self, project):
        """The project's conversations, newest first: the live ones and those in its .ovh/agents/."""
        out, seen = [], set()
        d = Path(project) / ".ovh" / "agents"
        for h in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True) if d.is_dir() else []:
            sid = h.stem
            if not ID_RE.match(sid):
                continue
            s = self.get(sid, project)
            if s is not None:
                out.append(s.summary())
                seen.add(sid)
        root = os.path.realpath(str(project))
        for s in list(self.sessions.values()):
            if s.id not in seen and s.root == root:
                out.append(s.summary())
        out.sort(key=lambda x: x.get("last") or 0, reverse=True)
        return out[:30]

    def _watch(self):
        """A request with no page to answer it: after APPROVAL_TIMEOUT seconds without one, it is rejected."""
        while not self.closed:
            time.sleep(1.0)
            now = time.time()
            for s in list(self.sessions.values()):
                for rid, p in list(s.pending.items()):
                    if s.subscribers:
                        p["detached"] = None
                    elif p.get("detached") is None:
                        p["detached"] = now
                    elif now - p["detached"] >= APPROVAL_TIMEOUT:
                        s.reject_waiting("timeout")
                        break

    def shutdown(self):
        """The desk is stopping: waiting requests cancelled, turns cancelled, every adapter stopped (TERM to its group
        when it does not end on its own)."""
        self.closed = True
        for s in list(self.sessions.values()):
            try:
                s.reject_waiting("desk_stop")
                if s.running and s.acp_id and self.peers.get(s.kind):
                    self.peers[s.kind].notify("session/cancel", {"sessionId": s.acp_id})
                agentlock.release(s.project, s.id)
            except Exception:
                pass
            with s.cond:
                s.cond.notify_all()
        threads = [threading.Thread(target=p.close, daemon=True) for p in list(self.peers.values()) if p is not None]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)
        self.peers.clear()
