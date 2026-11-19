"""The console's agents: a session manager inside bin/vh desk that talks to the agents installed on this machine (Claude
Code, Codex, DeepSeek Harness) through their ACP adapters (acp.py), one long-running adapter process per kind of agent,
started the first time someone talks to it.

A conversation is a Session: one project folder (the agent's working folder), one kind of agent. One begun on Studio's space
has no film yet: its record is the space's, the agent works in the workspace (the clone, where CLAUDE.md is), and when
bin/vh new in it makes a film (new_films: a folder that was not there when it began) it becomes that film's conversation
(Manager.adopt). Everything that happens in
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
plugins); the page shows them and can change them per session. Model and reasoning effort are Studio's: a new
conversation starts with what the person last picked in Studio for this kind of agent (picks.json beside the adapters),
else Studio's default (Claude Code: Opus 5.5 at xhigh), else the agent's own; only a value the agent offers is ever set.
With personal settings off (Claude Code only), the session starts from the project's settings alone.

Installed adapters live outside the repo, in $OVH_AGENTS_DIR or $XDG_CACHE_HOME/ovh/agents (~/.cache/ovh/agents), one
folder a kind, each package pinned (ADAPTERS): bin/vh desk agents install <kind>.
"""
import json, os, re, shlex, shutil, subprocess, sys, threading, time, uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent.parent
sys.path.insert(0, str(HERE))
import acp         # noqa: E402
import agentlock   # noqa: E402

PROTOCOL = 1
APPROVAL_TIMEOUT = float(os.environ.get("OVH_AGENT_APPROVAL_TIMEOUT") or 600)   # s without a page before a request is rejected
TURN_TIMEOUT = 6 * 3600.0
INSTALL_LIMIT = float(os.environ.get("OVH_AGENT_INSTALL_LIMIT") or 1800)   # s an install from the column may take before it is stopped
STOP_GRACE = float(os.environ.get("OVH_AGENT_STOP_GRACE") or 8)   # s after a cancel before the desk ends the turn itself
MAX_TEXT = 4000      # characters: what a page sees of a tool's output, a command's text …
MAX_DIFF = 40000     # characters of a diff's old or new text
MAX_PROMPT = 20000   # characters the person may send at once
MAX_ASK = 200000     # characters of any one string in a request to approve: kept whole up to this; a longer one cannot be allowed
CHUNK_GAP = 0.12     # s: the agent's text pieces within this are written as one event (a turn can send tens of thousands)
SCOPE_KINDS = ("dec", "least", "deleg", "concept", "seg", "cap", "shot", "fact", "time", "atime", "led", "doc", "asset", "range",
               "chapter", "card")   # core.js's TARGET_RE: the kinds of thing the console can have selected
ID_RE = re.compile(r"^[a-f0-9]{32}$")
# The Claude adapter tells a client that asks for it (its "async tasks" extension) when Claude Code starts a turn of its own:
# a background command it ran (bin/vh gate --wait, desk wait) ended after its turn, and it carries on. That turn arrives as a
# task of type "turn" (async_task_spawned … async_task_state_update with a terminal state); the console makes it a turn of
# the conversation: running, the film's lock, the stop button. Without the extension its words would come with no turn.
ASYNC_TASKS = {"_meta": {"jetbrains": {"air": {"version": 1, "capabilities": ["asyncTasks"]}}}}
TASK_ENDS = ("completed", "failed", "stopped")

# the adapters: the npm package that speaks ACP for each agent, pinned. size: on disk after install (macOS arm64, 2026-11-16)
ADAPTERS = {
    "claude": {"label": "Claude Code", "package": "@agentclientprotocol/claude-agent-acp", "version": "0.107.0",
               "bin": "claude-agent-acp", "args": [], "install_scripts": [], "login": "`claude` works in your terminal", "size": "≈ 0.4 GB",
               "settings_toggle": True},
    "codex": {"label": "Codex", "package": "@agentclientprotocol/codex-acp", "version": "2.6.0",
              "bin": "codex-acp", "args": [], "install_scripts": [], "login": "`codex` works in your terminal", "size": "≈ 0.4 GB"},
    "dsh": {"label": "DeepSeek Harness", "package": "@deepseek-ai/dsh", "version": "0.2.2-rc.3",
            "bin": "dsh", "args": ["--profile", "acp"],
            # its native modules build or fetch at install: the only packages of the three trees that run a script
            "install_scripts": ["@deepseek-ai/dsh-subprocess-local", "@google/genai", "koffi", "node-pty", "protobufjs"], "login": "DeepSeek Harness (its desktop app) is signed in", "size": "≈ 1.4 GB"},
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


# ---------- model and effort: Studio's default and the person's pick ----------

# what a new conversation starts with when the person has picked nothing in Studio and the agent offers it (an option whose
# name or value is one of these, spaces and case aside); a kind not here starts with the agent's own
DEFAULTS = {"claude": {"model": ("Opus 5.5", "claude-opus-5-5"), "effort": ("xhigh",)}}
ROLES = (("model", "model"), ("effort", "thought_level"))   # Studio's word, the ACP config option's category


def offered(o):
    """A select option's values, its groups flattened: [{value, name}]."""
    out = []
    for x in (o.get("options") or []) if isinstance(o, dict) else []:
        for y in x.get("options") if isinstance(x, dict) and isinstance(x.get("options"), list) else [x]:
            if isinstance(y, dict) and isinstance(y.get("value"), str):
                out.append({"value": y["value"], "name": y.get("name") if isinstance(y.get("name"), str) else y["value"]})
    return out


def option_of(config, role):
    cat = dict(ROLES)[role]
    return next((o for o in (config or {}).get("configOptions") or [] if isinstance(o, dict) and o.get("category") == cat
                 and o.get("type") == "select"), None)


def default_for(kind, role, opts):
    """Studio's default among the values the agent offers, or None."""
    norm = lambda x: re.sub(r"\s+", "", str(x)).lower()   # noqa: E731
    want = {norm(w) for w in (DEFAULTS.get(kind) or {}).get(role) or ()}
    return next((x["value"] for x in opts if norm(x["value"]) in want or norm(x["name"]) in want), None)


def picks_path():
    return home() / "picks.json"


def picks():
    """What the person picked in Studio, this machine, a kind of agent: {kind: {model, effort}} (values the agent offered)."""
    try:
        d = json.loads(picks_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return {k: {r: v for r, v in x.items() if r in ("model", "effort") and isinstance(v, str)} for k, x in d.items()
            if k in ADAPTERS and isinstance(x, dict)} if isinstance(d, dict) else {}


def remember(kind, role, value):
    """The person picked this model or effort: the next new conversation with this kind starts with it."""
    import fcntl
    p = picks_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p.with_name("picks.json.lock"), "a") as lock:   # two consoles, two picks: neither loses the other's
            fcntl.flock(lock, fcntl.LOCK_EX)
            d = picks()
            d.setdefault(kind, {})[role] = value
            tmp = p.with_name(f"picks.{os.getpid()}.{threading.get_ident()}.tmp")
            tmp.write_text(json.dumps(d, indent=1) + "\n", encoding="utf-8")
            os.replace(tmp, p)
    except OSError:
        pass


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


def _stop_group(p):
    """TERM to a process's own group (an install: bash, bin/vh, npm and what npm runs), then, after a grace, KILL to the
    whole group: what is under it may ignore TERM and outlive its leader (and hold its output open)."""
    if p is None:
        return
    try:
        os.killpg(p.pid, 15)
    except OSError:
        return
    try:
        p.wait(5)
    except subprocess.TimeoutExpired:
        pass
    time.sleep(0.2)
    try:
        os.killpg(p.pid, 9)
    except OSError:
        pass


def install(kind, out=sys.stdout):
    """npm install the pinned adapter into home()/<kind> (outside the repo), one install at a time into that folder (a
    second, from another console or a terminal, is refused while the first runs). → exit code."""
    a = ADAPTERS[kind]
    npm = shutil.which("npm")
    if not npm:
        print("desk agents: npm not found (it comes with node: brew install node)", file=sys.stderr)
        return 2
    base = home() / kind
    base.mkdir(parents=True, exist_ok=True)
    import fcntl
    lock = open(base / ".install.lock", "a")   # held until this process ends
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        print(f"desk agents: another install of {a['label']} is running into {base}: wait for it to finish", file=sys.stderr)
        return 3
    locks = HERE / "agent-locks" / kind   # the whole tree pinned, each package with its integrity hash: npm ci installs exactly it
    pinned = json.loads((locks / "package-lock.json").read_text(encoding="utf-8"))["packages"][""].get("dependencies") or {}
    if pinned != {a["package"]: a["version"]}:
        print(f"desk agents: {locks}/package-lock.json pins {pinned}, not {a['package']}@{a['version']}", file=sys.stderr)
        return 2
    for f in ("package.json", "package-lock.json"):
        shutil.copyfile(locks / f, base / f)
    print(f"desk agents: installing {a['package']}@{a['version']} into {base} ({a['size']}) …", file=out, flush=True)
    r = subprocess.run([npm, "ci", "--no-audit", "--no-fund", "--loglevel=error"] + ([] if a["install_scripts"] else ["--ignore-scripts"]), cwd=str(base),
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


def clean(obj, root, n=MAX_TEXT, depth=0, cut=None, also=None):
    """An update as the log keeps it: the project's own folder written as a relative path, the home folder as ~, long
    strings clipped (a diff's texts less so), the bulky echoes dropped (Claude's toolResponse repeats the file). With cut
    (a list): what is asked for approval, kept verbatim (root None: no path rewritten, since "cd /tmp && rm -rf <project>/x"
    is not "rm -rf x"), and each thing clipped or dropped noted in cut."""
    if depth > 12:
        if cut is not None:
            cut.append(depth)
        return None
    if isinstance(obj, str):
        for p, name in (also or {}).items() if cut is None else ():   # a folder written by its name (inside root, or not)
            obj = obj.replace(p + "/", name + "/").replace(p, name)
        if root and cut is None:
            obj = obj.replace(root + "/", "").replace(root, ".")
        h = str(Path.home())
        if h and len(h) > 1 and cut is None:
            obj = obj.replace(h + "/", "~/")
        if cut is not None and len(obj) > n:
            cut.append(len(obj))
        return _clip(obj, n)
    if isinstance(obj, list):
        if cut is not None and len(obj) > 200:
            cut.append(len(obj))
        return [clean(x, root, n, depth + 1, cut, also) for x in obj[:200]]
    if isinstance(obj, dict):
        out = {}
        if cut is not None and len(obj) > 80:
            cut.append(len(obj))
        for k, v in list(obj.items())[:80]:
            if k in ("toolResponse", "sessionId"):
                continue
            out[k] = clean(v, root, max(n, MAX_DIFF) if k in ("oldText", "newText") else n, depth + 1, cut, also)
        return out
    return obj


def private_options(opts):
    """Claude's "agent" setting lists the person's own subagents by name (their plugins): the log keeps the one in use and how
    many there are, not the names."""
    out = []
    for o in opts if isinstance(opts, list) else []:
        if isinstance(o, dict) and o.get("id") == "agent" and isinstance(o.get("options"), list):
            cur = [x for x in o["options"] if isinstance(x, dict) and x.get("value") == o.get("currentValue")]
            o = dict(o, options=cur, count=len(o["options"]))
        out.append(o)
    return out


def folder(d):
    """<project>/.ovh/agents/, made with a .gitignore of *: a project in a git repository of its own never commits a
    conversation (file contents, command output, what it cost) by a git add -A."""
    d.mkdir(parents=True, exist_ok=True)
    g = d / ".gitignore"
    if not g.exists():
        try:
            g.write_text("# the console's conversations with agents (bin/vh desk): never committed\n*\n")
        except OSError:
            pass


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
        self.seq = max((e["seq"] for e in self.events), default=0)   # the largest: a log with a line out of order loses nothing new
        self._buf = None           # the agent's text not written yet: {"u", "text"}; written when CHUNK_GAP passes or anything else comes
        self.header = header or {}
        self.cwd = self.header.get("cwd") or self.root   # the agent's working folder: the film's, or the workspace's for one begun on the space
        self.slugs = set(self.header.get("slugs") or [])   # the bin/vh new it ran (begun on the space)
        self.refused = set()       # films it made whose lock someone else held (said once)
        self.note_again = False    # it had to start afresh: Studio's line goes with the next words again
        self.acp_id = self.header.get("acp_id")
        self.personal = self.header.get("personal", True)
        self.live = False          # attached to a session in the running adapter
        self.running = False       # a turn in flight
        self.stopping = False
        self.replaying = False     # a session/load is replaying history we already have
        self.pending = {}          # our request id → {"agent": its JSON-RPC id, "options": [...], "detached": t | None}
        self.config = {}           # modes, configOptions, models: what the agent said last
        self.asked = None          # {model, effort} the person chose when starting it (a new conversation only)
        self.subscribers = 0
        self._n = 0
        self._attach_lock = threading.RLock()   # attach → set_config (DSH defaults) → attach
        self._say_lock = threading.Lock()
        self._spot_lock = threading.Lock()
        self.own = None            # the adapter's task id of the turn the agent started by itself, while it runs
        self.turn = 0              # this conversation's turns, numbered: a turn ended here is not ended again by its late answer
        self._ended = 0
        for e in self.events:      # the state an old log ends in: what the page shows before it talks again
            if e.get("type") == "state":
                self.config.update({k: v for k, v in e.items() if k in ("modes", "configOptions", "models")})

    @property
    def unplaced(self):
        """Begun on Studio's space and no film made yet: its record is the space's, no project lock is taken."""
        return bool(self.header.get("space")) and not self.header.get("placed")

    def _c(self, obj, n=MAX_TEXT):
        """An update as the log keeps it (clean): paths relative to where the agent works; for one begun on the space, that
        is the workspace before and after its film is made, and the film's own folder is written by its name (never ".")."""
        named = {self.root: self.project.name} if self.header.get("placed") and self.cwd != self.root else None
        return clean(obj, self.cwd, n, also=named)

    # ---------- the log ----------
    def emit(self, type_, **fields):
        with self.cond:
            self._flush()
            self._emit(type_, **fields)

    def _flush(self):
        """Write the agent's text gathered so far as one event."""
        b, self._buf = self._buf, None
        if b:
            self._emit("update", u=self._c(dict(b["u"], content={"type": "text", "text": b["text"]}), MAX_ASK))   # its words whole

    def chunk(self, u):
        """A piece of the agent's text: gathered with the pieces that follow within CHUNK_GAP, of the same message."""
        text = (u.get("content") or {}).get("text") if isinstance(u.get("content"), dict) else None
        if not isinstance(text, str):
            return self.emit("update", u=self._c(u))
        with self.cond:
            b = self._buf
            if b and (b["u"].get("sessionUpdate"), b["u"].get("messageId")) == (u.get("sessionUpdate"), u.get("messageId")) and len(b["text"]) < 8000:
                b["text"] += text
                return
            self._flush()
            self._buf = {"u": u, "text": text}

        def later(mine=self._buf):
            time.sleep(CHUNK_GAP)
            with self.cond:
                if self._buf is mine:
                    self._flush()
        threading.Thread(target=later, daemon=True).start()

    def _emit(self, type_, **fields):
        with self.cond:
            self.seq += 1
            ev = {"seq": self.seq, "t": round(time.time(), 3), "type": type_, **fields}
            self.events.append(ev)
            try:
                folder(self.log.parent)
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
                "space": bool(self.header.get("space")), "placed": self.header.get("placed"),
                "created": self.header.get("created"), "last": last, "live": self.live, "running": self.running,
                "pending": len(self.pending), "personal": self.personal, "turns": sum(1 for e in self.events if e.get("type") == "user")}

    # ---------- attaching to the adapter ----------
    def attach(self):
        """A session in the running adapter for this conversation: the one it had (load or resume, as the agent can),
        else a new one. Raises Unavailable."""
        with self._attach_lock:
            peer, caps = self.mgr.peer(self.kind)
            if self.live:
                return
            params = {"cwd": self.cwd, "mcpServers": []}
            meta = self._meta()
            res = None
            sc = caps.get("sessionCapabilities") or {}
            if self.acp_id:
                try:
                    if caps.get("loadSession"):
                        self.replaying = True
                        res = peer.call("session/load", dict(params, sessionId=self.acp_id, **({"_meta": meta} if meta else {})), 120)
                    elif "resume" in sc:
                        res = peer.call("session/resume", dict(params, sessionId=self.acp_id), 120)
                except acp.AcpError:
                    res = None
                finally:
                    self.replaying = False
            new = res is None
            if new:
                if self.kind == "codex" and not self.unplaced and "systemPrompt" in sc:
                    # A film outside this checkout may never load the harness's AGENTS.md by cwd discovery.
                    guide = shlex.quote(str(WORKSPACE / "AGENTS.md"))
                    command = shlex.join([str(WORKSPACE / "bin" / "vh"), "status", str(self.project)])
                    note = (f"OpenVideoHarness Studio opened a conversation for an existing film. Follow {guide} and run `{command}` "
                            "to find the next step. Use the existing review record and honor pending review stops when continuing production.")
                    params["systemPrompt"] = {"mode": "append", "content": [{"type": "text", "text": note}]}
                try:
                    res = peer.call("session/new", dict(params, **({"_meta": meta} if meta else {})), 180)
                except acp.AcpError as e:
                    if self.kind == "codex" and e.code == -32000:  # ACP auth_required
                        self.mgr.auth[self.kind] = "unauthenticated"
                        raise Unavailable("signed_out", str(e)) from e
                    raise Unavailable("session_refused", str(e))
                if not isinstance(res, dict) or not res.get("sessionId"):
                    raise Unavailable("session_refused", "no sessionId")
                if self.acp_id:
                    self.emit("notice", code="fresh")   # the agent will not remember what was said before
                    self.note_again = self.unplaced     # send the space's direction again to a replacement session
                self.acp_id = res["sessionId"]
                self._header()
            self.mgr.by_acp[(self.kind, self.acp_id)] = self
            self.live = True
            self._state(res if isinstance(res, dict) else {})
            if self.mgr.auth.get(self.kind) == "unauthenticated":
                self.emit("notice", code="signed_out")
            if new:
                self._defaults()

    def _meta(self):
        """What session/new carries besides the folder: with personal settings off, Claude Code reads only the project's
        settings (its user settings, skills, allow rules and CLAUDE.md stay out)."""
        if self.kind == "claude" and not self.personal:
            return {"claudeCode": {"options": {"settingSources": ["project", "local"]}}}
        return None

    def _header(self):
        self.header.update(kind=self.kind, acp_id=self.acp_id, personal=self.personal, created=self.header.get("created") or time.time(), cwd=self.cwd)
        try:
            folder(self.log.parent)
            (self.log.parent / f"{self.id}.json").write_text(json.dumps(dict(self.header, id=self.id), ensure_ascii=False))
        except OSError:
            pass

    def _state(self, res):
        st = {k: res[k] for k in ("modes", "configOptions", "models") if isinstance(res.get(k), (dict, list))}
        if st:
            self.config.update(st)
            seen = {r: offered(option_of(self.config, r)) for r, _c in ROLES if option_of(self.config, r)}
            if seen:
                self.mgr.seen[self.kind] = seen   # what this kind offers, for the next new conversation's pickers
            shown = dict(st, **({"configOptions": private_options(st["configOptions"])} if "configOptions" in st else {}))
            self.emit("state", **self._c(shown))

    def _defaults(self):
        """A new conversation's model, then effort: what the person chose for it when starting it (self.asked, then
        remembered), else what they last picked in Studio for this kind, else Studio's default (DEFAULTS), else, for
        DeepSeek Harness, its desktop's effort; else the agent's own is left. Only a value the agent offers is set."""
        asked, mine = self.asked or {}, picks().get(self.kind) or {}
        for role, _cat in ROLES:
            o = option_of(self.config, role)   # (read again: a new model may bring other efforts)
            if o is None:
                continue
            opts = offered(o)
            vals = [x["value"] for x in opts]
            want = next((v for v in (asked.get(role), mine.get(role)) if v in vals), None) or default_for(self.kind, role, opts)
            if want is None and self.kind == "dsh" and role == "effort":
                want = dsh_user_defaults().get("reasoningEffort")
                want = want if want in vals else None
            if want is None:
                continue
            if want != o.get("currentValue"):
                try:
                    self.set_config(o.get("id"), want, by="defaults")
                except (Unavailable, ValueError):
                    continue
            if asked.get(role) == want:   # taken by the agent: the person's choice for the next one too
                remember(self.kind, role, want)
        self.asked = None

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
            u = dict(u, configOptions=private_options(u["configOptions"]))
        if kind in ("agent_message_chunk", "agent_thought_chunk"):
            return self.chunk(u)
        if kind == "async_task_spawned" and u.get("taskType") == "turn" and isinstance(u.get("asyncTaskId"), str):
            self._own_start(u["asyncTaskId"][:200])
        self.emit("update", u=self._c(u))
        if kind == "async_task_state_update" and u.get("state") in TASK_ENDS and self.own is not None and u.get("asyncTaskId") == self.own:
            self._end(self.turn, stop="cancelled" if u.get("state") == "stopped" else "error" if u.get("state") == "failed" else "end_turn", own=True)
        if kind in ("tool_call", "tool_call_update") and self.unplaced:
            got = ran_new(u) - self.slugs
            if got:   # it runs bin/vh new: kept with the conversation, so a restart still knows
                self.slugs |= got
                self.header["slugs"] = sorted(self.slugs)[-20:]
                self._header()
            if self.slugs and kind == "tool_call_update":   # (another thread: it reads folders, and this one carries every agent's messages)
                threading.Thread(target=self.mgr.spot, args=(self,), name=f"place-{self.id[:6]}", daemon=True).start()

    def on_permission(self, agent_rid, params):
        """The agent asks before it does something: a card on the page, the agent waiting until the person answers."""
        self._n += 1
        rid = f"r{self._n}-{uuid.uuid4().hex[:8]}"
        opts = [o for o in (params.get("options") or []) if isinstance(o, dict) and isinstance(o.get("optionId"), str)]
        cut = []   # what it asks is kept whole, up to MAX_ASK a string: what the person approves is what the agent asked
        tool = clean(params.get("toolCall") or {}, self.root, MAX_ASK, cut=cut)
        with self.cond:
            self.pending[rid] = {"agent": agent_rid, "options": opts, "detached": None if self.subscribers else time.time(), "clipped": bool(cut)}
        self.emit("permission", rid=rid, tool=tool, **({"clipped": True} if cut else {}),
                  options=[{"optionId": o["optionId"], "name": str(o.get("name") or "")[:300], "kind": o.get("kind")} for o in opts])

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
        if p.get("clipped") and str(option_kind(p["options"], option_id) or "").startswith("allow"):
            raise ValueError("this request is too long to show whole, so it can only be refused")
        return self._answer(rid, {"outcome": "selected", "optionId": option_id}, "page")   # what the server knows: the page's token and not an agent's process

    def reject_waiting(self, by):
        """Each waiting request answered: rejected where the agent offered a rejection (a timeout), else cancelled (a stop,
        the agent or the desk going away); never allowed."""
        for rid in list(self.pending):
            p = self.pending.get(rid)
            if not p:
                continue
            rej = next((o["optionId"] for o in p["options"] if o.get("kind") == "reject_once"), None)
            self._answer(rid, {"outcome": "selected", "optionId": rej} if rej and by == "timeout" else {"outcome": "cancelled"}, by)

    # ---------- from the person ----------
    def say(self, text, scope=None, despite=False):
        """A turn with the person's words. Raises Busy (a turn runs, or someone else works on the project; an agent waiting
        for this round's review, or one open in the folder, is let through when the person said so: despite), Unavailable."""
        with self._say_lock:
            if self.running:
                raise Busy([{"why": "turn", "label": ADAPTERS[self.kind]["label"]}])
            space = self.unplaced   # no film yet: nothing to lock (two new films at once are two folders)
            who = [] if space else agentlock.occupants(self.project, self.mgr.adapter_pids(), self.id)
            if who and not (despite and all(w["why"] in ("waiting", "process") for w in who)):
                raise Busy(who)
            self.attach()
            self.turn += 1
            got = True if space else agentlock.acquire(self.project, {"kind": self.kind, "label": ADAPTERS[self.kind]["label"], "session": self.id,
                                                                      "turn": self.turn})   # no address: nothing an agent reads there reaches the desk
            if got is not True:
                self.turn -= 1
                raise Busy([dict(got, why="console")])
            self.running, self.stopping = True, False
            first = self.unplaced and (self.note_again or not any(e.get("type") == "user" for e in self.events))
            self.note_again = False
        self.emit("user", text=text, **({"scope": scope} if scope else {}))
        self.emit("turn", state="start")
        prompt = [{"type": "text", "text": text}]
        if scope:   # what the person had selected in the console: named by the page's own words, not the project's
            prompt.append({"type": "text", "text": scope_note(scope)})
        if first and self.mgr.space_note:   # a film begun on the space: Studio's own line, once (never words from the page or a file)
            prompt.append({"type": "text", "text": self.mgr.space_note})
        threading.Thread(target=self._turn, args=(prompt, self.turn), name=f"turn-{self.id[:6]}", daemon=True).start()

    def _own_start(self, task):
        """The agent began a turn by itself (the adapter's task of type "turn"): a turn of this conversation, as one the
        person began is, with the film's lock when it can have it (it works either way: the page says who holds the film)."""
        with self._say_lock:
            if self.running:
                return
            self.turn += 1
            got = True if self.unplaced else agentlock.acquire(self.project, {"kind": self.kind, "label": ADAPTERS[self.kind]["label"], "session": self.id,
                                                                            "turn": self.turn})
            self.running, self.stopping, self.own = True, False, task
        self.emit("turn", state="start", own=True, **({} if got is True else {"locked": False}))

    def _end(self, n, **fields):
        """End turn n, once: what waits is cancelled, the lock goes, the page hears it. False when it had ended already."""
        with self._say_lock:
            if self._ended >= n:
                return False
            self._ended = n
            self.reject_waiting("turn_end")
            agentlock.release(self.project, self.id, n)
            self.running, self.stopping, self.own = False, False, None
        self.emit("turn", state="end", **fields)
        return True

    def _turn(self, prompt, n):
        res, err = None, None
        try:
            peer = self.mgr.peers.get(self.kind)
            if peer is None:
                raise acp.AcpError("the agent stopped", code="gone")
            res = peer.call("session/prompt", {"sessionId": self.acp_id, "prompt": prompt}, TURN_TIMEOUT)
        except acp.AcpError as e:
            if self.kind == "codex" and e.code == -32000:
                self.mgr.auth[self.kind] = "unauthenticated"
            err = str(e)[:300]
        res = res if isinstance(res, dict) else {}
        self._end(n, stop=res.get("stopReason") or ("error" if err else None), usage=self._c(res.get("usage") or {}),
                  **({"error": err} if err else {}))

    def stop(self):
        """Stop the turn: every waiting request answered cancelled first (the protocol's order), then the cancel."""
        self.reject_waiting("stop")
        if not self.running:
            return False
        self.stopping = True
        self.emit("notice", code="stopping")
        peer = self.mgr.peers.get(self.kind)
        own = self.own
        if peer is not None and self.acp_id and own:   # its own turn: no prompt of ours to cancel; the adapter stops the task

            def ask():
                try:
                    peer.call("_session/async_task/stop", {"sessionId": self.acp_id, "asyncTaskId": own}, 30)
                except acp.AcpError:
                    try:
                        peer.notify("session/cancel", {"sessionId": self.acp_id})
                    except acp.AcpError:
                        pass
            threading.Thread(target=ask, name=f"stop-own-{self.id[:6]}", daemon=True).start()
        elif peer is not None and self.acp_id:
            try:
                peer.notify("session/cancel", {"sessionId": self.acp_id})
            except acp.AcpError:
                pass
        n = self.turn

        def unheard():   # the adapter did not end the turn after the cancel: end it here, and start that agent afresh
            time.sleep(STOP_GRACE)
            if self._ended >= n or self.turn != n:
                return
            if self._end(n, stop="cancelled", error="agent_stuck"):
                self.emit("notice", code="restarted")
                self.mgr.restart(self.kind)
        threading.Thread(target=unheard, name=f"stop-{self.id[:6]}", daemon=True).start()
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
        self.emit("state", modes=self._c(self.config["modes"]), by="page")

    def set_config(self, config_id, value, by="page"):
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
        role = next((r for r, c in ROLES if o.get("category") == c), None)
        if by == "page" and role:   # the person's pick: the next new conversation with this kind starts with it
            remember(self.kind, role, value)
        self.mgr.seen[self.kind] = {r: offered(option_of(self.config, r)) for r, _c in ROLES if option_of(self.config, r)}
        self.emit("state", configOptions=self._c(self.config["configOptions"]), by=by)

    def gone(self, code):
        """The adapter stopped: what waited is cancelled, the turn ends, the next word starts it again."""
        self.live = False
        self.reject_waiting("agent_gone")   # the turn in flight ends by itself: its call hears the adapter is gone
        self.emit("notice", code="agent_gone", exit=code)
        if self.own is not None:   # a turn it began by itself has no call to hear it: it ends here
            self._end(self.turn, stop="error", error="agent_gone", own=True)


def scope_note(scope):
    """The console's note of what the person had selected, built from its kind and id alone (never a label taken from a
    project file): "(In the console the person had selected: shot S4, 0:12–0:18.)"."""
    kind = str(scope.get("kind") or "")
    kind = kind if kind in SCOPE_KINDS else ""   # a kind the console knows, never a word from a file
    ident = str(scope.get("id") or "")
    ident = ident if re.fullmatch(r"[A-Za-z0-9._:~+-]{1,40}", ident) else ""   # an id of the console's own shape (S4, 2, 12.5-18)

    def t(x):
        return f"{int(x // 60)}:{x % 60:04.1f}" if isinstance(x, (int, float)) and x == x and 0 <= x < 1e6 else None
    parts = [f"{kind} {ident}".strip()] if kind or ident else []
    a, b = t(scope.get("t")), t(scope.get("t1"))
    if a:
        parts.append(f"{a}–{b}" if b else a)
    mod = str(scope.get("module") or "")
    mod = mod if mod in ("idea", "outline", "board", "sound", "cut", "ship", "assets", "ledger") else ""
    if mod:
        parts.append(f"module {mod}")
    return "(In the console the person had selected: " + ", ".join(parts) + ".)" if parts else ""


# ---------- a film begun on the space: which one this conversation made ----------

VH_NEW_RE = re.compile(r"(?:^|[^\w-])vh['\"]?\s+new\s+['\"]?[\w.-]+['\"]?\s+['\"]?([A-Za-z0-9][\w.-]{0,80})")   # bin/vh new <type> <slug>


def _texts(o, depth=0):
    if isinstance(o, str):
        yield o[:20000]
    elif isinstance(o, (list, tuple)) and depth < 6:
        for x in o[:50]:
            yield from _texts(x, depth + 1)
    elif isinstance(o, dict) and depth < 6:
        for v in list(o.values())[:50]:
            yield from _texts(v, depth + 1)


def ran_new(u):
    """The slugs of the bin/vh new this tool call runs (its command, as each agent sends it: rawInput's command, a list of
    words, or the title)."""
    return {m.group(1) for t in _texts([u.get("rawInput"), u.get("title")]) for m in VH_NEW_RE.finditer(t)}


def folders(places):
    """The real folders directly in these places (a link is not one): what a snapshot keeps."""
    out = set()
    for pl in places:
        try:
            with os.scandir(pl) as it:
                for e in it:
                    if not e.is_symlink() and e.is_dir(follow_symlinks=False):
                        out.add(os.path.realpath(e.path))
        except OSError:
            continue
    return out


def new_films(places, before, slugs):
    """The films a conversation made: a folder in one of the places (no link, nothing reached through one) that was not
    there when it began (before), named <date>-<slug> for a bin/vh new it ran, with a BRIEF.md. An edit, a chmod or a
    copy cannot make an old folder new, and a folder another conversation made carries that one's slug."""
    names = [re.compile(r"\d{4}-\d{2}-\d{2}-" + re.escape(x) + "$") for x in slugs]
    out = []
    for r in sorted(folders(places) - set(before)):
        inside = any(r.startswith(os.path.realpath(pl) + os.sep) for pl in places)
        if inside and any(n.fullmatch(os.path.basename(r)) for n in names) and os.path.isfile(os.path.join(r, "BRIEF.md")):
            out.append(r)
    return out


# ---------- the manager: one per desk ----------

class Manager:
    def __init__(self, url=""):
        self.url = url
        self.peers = {}        # kind → acp.Peer
        self.caps = {}         # kind → initialize's agentCapabilities (and agentInfo)
        self.auth = {}         # kind → "authenticated" | "unauthenticated", as the adapter said last
        self.sessions = {}     # our id → Session
        self.by_acp = {}       # (kind, acp session id) → Session
        self._lock = threading.RLock()
        self._starting = {k: threading.Lock() for k in ADAPTERS}
        self.closed = False
        self._closing = []     # adapters being stopped (a restart): shutdown waits for them
        self.installs = {}     # kind → the install the person started from the column: {state, since, took, said}
        self.seen = {}         # kind → {model, effort: [{value, name}]}: what its last session offered (this run)
        self.place = None      # the desk's: a film's folder → its key in the console (joining it when it is outside the roots), or None
        self.places = None     # the desk's: the folders a film begun on the space may be made in (its roots, the workspace's projects/)
        self.present = None    # the desk's: is a page of Studio open (a request of a film begun on the space waits while one is)
        self.space_note = ""   # the desk's: Studio's line after the first words of a film begun on the space
        threading.Thread(target=self._watch, name="agents-watch", daemon=True).start()

    def install(self, kind, cancel=False):
        """The person's click on "set it up" in the column: bin/vh desk agents install <kind> in the background, one at a
        time a kind (a click while it runs is the same install; cancel stops it). It stops by itself after INSTALL_LIMIT
        seconds, and with the console. → its state, as the column polls it."""
        with self._lock:
            j = self.installs.get(kind)
            alive = bool(j and j.get("proc") is not None and j["proc"].poll() is None)
            if cancel:
                if j and j["state"] == "running":
                    j["cancel"] = True   # (stopped outside the lock: its grace takes seconds)
                    threading.Thread(target=_stop_group, args=(j.get("proc"),), name=f"stop-install-{kind}", daemon=True).start()
                return self.install_state(kind)
            if self.closed or alive or j and j["state"] == "running":
                return self.install_state(kind)
            j = self.installs[kind] = {"state": "running", "since": time.time(), "took": None, "said": "", "proc": None, "limit": INSTALL_LIMIT}
        threading.Thread(target=self._install, args=(kind, j), name=f"install-{kind}", daemon=True).start()
        return self.install_state(kind)

    def _install(self, kind, j):
        out, code, why = "", -1, None
        try:
            p = subprocess.Popen([os.environ.get("OVH_BASH") or "bash", str(HERE.parent.parent / "bin" / "vh"), "desk", "agents", "install", kind],
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace",
                                 start_new_session=True)   # its own group: npm under it stops with it
            j["proc"] = p
            try:
                out = p.communicate(timeout=INSTALL_LIMIT)[0]
            except subprocess.TimeoutExpired:   # too long: the whole group stops, and the handle is kept until it has
                _stop_group(p)
                why = "timeout"
                try:
                    out = p.communicate(timeout=10)[0] or ""
                except subprocess.TimeoutExpired:
                    out = ""
            code = p.returncode
        except OSError:
            why = "failed"
        lines = [x.strip() for x in (out or "").splitlines() if x.strip()]
        if why is None:
            why = "cancelled" if j.get("cancel") else "no_npm" if "npm not found" in out else "busy" if "another install" in out else "failed"
        home_ = str(Path.home())
        with self._lock:   # (what it printed is kept for whoever looks into it, the home folder as ~; the page says a sentence)
            j.update(state="done" if code == 0 and installed(kind) else why, took=round(time.time() - j["since"]),
                     said="\n".join(lines[-3:])[-600:].replace(home_, "~"), proc=None)

    def choices(self, kind):
        """What a new conversation with this kind starts with, for the column: {model, effort: {value, name, from} or None,
        offered: {model, effort: [{value, name}]} or None}. from: picked (the person, in Studio), default (Studio's), dsh
        (DeepSeek Harness desktop's effort), agent (its own: nothing set). Without a session this run, offered is None and
        a default is named as DEFAULTS has it."""
        seen, mine, out = self.seen.get(kind), picks().get(kind) or {}, {}
        for role, _c in ROLES:
            opts = (seen or {}).get(role)
            names = {x["value"]: x["name"] for x in opts or []}
            if mine.get(role) and (opts is None or mine[role] in names):
                out[role] = {"value": mine[role], "name": names.get(mine[role], mine[role]), "from": "picked"}
            elif opts is not None and default_for(kind, role, opts):
                v = default_for(kind, role, opts)
                out[role] = {"value": v, "name": names[v], "from": "default"}
            elif opts is None and (DEFAULTS.get(kind) or {}).get(role):
                out[role] = {"value": None, "name": DEFAULTS[kind][role][0], "from": "default"}
            elif kind == "dsh" and role == "effort" and dsh_user_defaults().get("reasoningEffort"):
                out[role] = {"value": dsh_user_defaults()["reasoningEffort"], "name": dsh_user_defaults()["reasoningEffort"], "from": "dsh"}
            else:
                out[role] = {"value": None, "name": None, "from": "agent"}
        out["offered"] = seen
        return out

    def install_state(self, kind):
        j = self.installs.get(kind)
        return {k: v for k, v in j.items() if k not in ("proc", "cancel")} if j else None

    def adapter_pids(self):
        return [p.proc.pid for p in self.peers.values() if p is not None]

    def peer(self, kind):
        """The running adapter for this kind (started and initialized the first time) and its capabilities."""
        if self.closed:
            raise Unavailable("closing")
        with self._starting[kind]:
            p = self.peers.get(kind)
            if p is not None:
                # Codex only reads an external login at process startup. Retry an idle, signed-out adapter afresh.
                refresh = (kind == "codex" and self.auth.get(kind) == "unauthenticated"
                           and not any(s.kind == kind and s.running for s in list(self.sessions.values())))
                if p.alive() and not refresh:
                    return p, self.caps.get(kind) or {}
                self.restart(kind, wait=True)
            cmd = command(kind)
            if cmd is None:
                raise Unavailable("not_installed")
            argv, extra = cmd
            try:
                p = acp.Peer(argv, env=acp.clean_env(extra), cwd=str(home()), name=kind,
                             on_note=lambda m, prm, k=kind: self._note(k, m, prm),
                             on_request=lambda rid, m, prm, k=kind: self._request(k, rid, m, prm),
                             on_exit=lambda code, k=kind: self._exit(k, p, code))
            except OSError as e:
                raise Unavailable("no_start", str(e))
            try:
                res = p.call("initialize", {"protocolVersion": PROTOCOL,
                                            "clientCapabilities": dict({"fs": {"readTextFile": False, "writeTextFile": False}, "terminal": False},
                                                                       **(ASYNC_TASKS if kind == "claude" else {})),
                                            "clientInfo": {"name": "ovh-desk", "title": "OpenVideoHarness console", "version": "1"}}, 90)
            except acp.AcpError as e:
                tail = " / ".join(list(p.stderr)[-3:])
                p.close(0.2, 1.0)
                raise Unavailable("no_start", (str(e) + (" — " + tail if tail else ""))[:500])
            caps = dict((res or {}).get("agentCapabilities") or {}, agentInfo=(res or {}).get("agentInfo") or {})
            self.peers[kind], self.caps[kind] = p, caps
            return p, caps

    def _note(self, kind, method, params):
        if method in ("auth/status_update", "_auth/status_update"):
            # codex-acp 2.6 reports an authStatus object. Keep only the normalized state.
            state = params.get("state")
            if method == "_auth/status_update":
                status = params.get("authStatus")
                identity = status.get("kind") if isinstance(status, dict) else None
                if identity not in ("none", "account", "api_key", "gateway", "external"):
                    return
                state = "unauthenticated" if identity == "none" else "authenticated"
            if state in ("authenticated", "unauthenticated") and state != self.auth.get(kind):
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

    def restart(self, kind, wait=False):
        """Stop this kind's adapter (TERM to its group) so that the next word starts it afresh; its conversations read on."""
        p = self.peers.pop(kind, None)
        self.auth.pop(kind, None)
        for s in list(self.sessions.values()):
            if s.kind == kind:
                s.live = False
                s.reject_waiting("agent_gone")
        if p is not None:
            if wait:
                p.close(0.2, 1.0)
                return
            t = threading.Thread(target=p.close, args=(0.5, 3.0), daemon=True)
            t.start()
            self._closing.append(t)   # the desk's shutdown waits for it too

    def _exit(self, kind, peer, code):
        if self.peers.get(kind) is not peer:
            return
        self.peers.pop(kind, None)
        for s in list(self.sessions.values()):
            if s.kind == kind and s.live:
                s.gone(code)

    # ---------- sessions ----------
    def open(self, project, key, kind, personal=True, asked=None, cwd=None):
        """A new conversation in a film's folder; with cwd, one begun on the space: its record in project (the space's
        folder), the agent working in cwd (the workspace, where CLAUDE.md is) until the film it makes takes it (adopt)."""
        if kind not in ADAPTERS:
            raise ValueError("unknown agent")
        header = {"created": time.time(), "personal": bool(personal)}
        if cwd:   # where a film may be made, and what is there now: a folder there later that was not is one it made
            places = [os.path.realpath(p) for p in (self.places() if self.places else [])]
            header.update(space=True, cwd=os.path.realpath(str(cwd)), places=places, before=sorted(folders(places)))
        s = Session(self, kind, project, key, header=header)
        s.asked = {r: v for r, v in (asked or {}).items() if r in ("model", "effort") and isinstance(v, str) and v} or None
        s._header()
        with self._lock:
            self.sessions[s.id] = s
        return s

    def get(self, sid, project=None, key=None, space=False):
        """A session by id: live in this desk, or read back from its project's log (project given). space: asked at the
        space's address, which also reaches one begun there that has since made its film (a page still on the space can
        stop it)."""
        if not isinstance(sid, str) or not ID_RE.match(sid):
            return None
        with self._lock:
            s = self.sessions.get(sid)
            if s is not None:
                return s if project is None or os.path.realpath(str(project)) == s.root or space and s.header.get("space") else None
            if project is None:
                return None
            d = Path(project) / ".ovh" / "agents"
            try:
                header = json.loads((d / f"{sid}.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return None
            if header.get("kind") not in ADAPTERS:
                return None
            if header.get("space") and (self.went(sid, project) if not header.get("placed") else not (d / f"{sid}.jsonl").exists()):
                return None   # a move a crash cut short: the conversation is whole in the one place that has its log
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

    def spot(self, s):
        """After a tool call of a conversation begun on the space that ran bin/vh new: the film it made, when there is
        exactly one (new_films), becomes its film."""
        with s._spot_lock:
            if not s.unplaced or not s.slugs:
                return False
            taken = {x.root for x in list(self.sessions.values()) if x is not s and not x.unplaced}
            made = [r for r in new_films(s.header.get("places") or [], s.header.get("before") or [], s.slugs) if r not in taken]
            return self.adopt(s, Path(made[0])) if len(made) == 1 else False

    def strays(self, film, space):
        """The conversations begun on the space that ran bin/vh new, have no film, and Studio found none for (the folder was
        renamed, or made some other way), that could have made this one (it was not there when each began, and it is in one
        of its places): what a film's empty column offers to bring in."""
        real = os.path.realpath(str(film))
        out = []
        for x in self.listing(space) if space else []:
            s = self.get(x["id"], space)
            if s is not None and s.unplaced and s.slugs and real not in set(s.header.get("before") or []) \
                    and any(real.startswith(p + os.sep) for p in s.header.get("places") or []) \
                    and not new_films(s.header.get("places") or [], s.header.get("before") or [], s.slugs):
                out.append(x)
        return out

    def adopt(self, s, film):
        """The film a conversation begun on the space made: it becomes that film's conversation. A turn in flight takes
        the film's lock first (held by someone else: nothing moves, and the column says so); the record moves in an order
        a crash cannot split (a note at the space of where it goes, its head at the film, its log, then the head at the
        space goes; one place shows it at every step); the page hears where it is now (the window goes there). The agent
        is not touched: same session, same working folder."""
        film = Path(os.path.realpath(str(film)))
        key = self.place(film) if self.place else None
        if key is None:
            return False
        with s._say_lock:   # (a turn ending meanwhile: it lets go of the lock it took here, or of none)
            if not s.unplaced:
                return False
            if s.running:
                got = agentlock.acquire(film, {"kind": s.kind, "label": ADAPTERS[s.kind]["label"], "session": s.id, "turn": s.turn})
                if got is not True:
                    if str(film) not in s.refused:
                        s.refused.add(str(film))
                        s.emit("notice", code="place_busy", name=film.name, who=str((got or {}).get("label") or "")[:60])
                    return False
            with s.cond:
                s._flush()
                old, new = s.log.parent, film / ".ovh" / "agents"
                done = []
                try:
                    (old / f"{s.id}.placed").write_text(str(film))
                    done.append(old / f"{s.id}.placed")
                    folder(new)
                    (new / f"{s.id}.json").write_text(json.dumps(dict(s.header, id=s.id, placed=film.name), ensure_ascii=False))
                    done.append(new / f"{s.id}.json")
                    if (old / f"{s.id}.jsonl").exists():
                        shutil.move(str(old / f"{s.id}.jsonl"), str(new / f"{s.id}.jsonl"))
                except OSError:
                    for f in done:   # a film that cannot be written: the conversation stays whole on the space
                        try:
                            f.unlink()
                        except OSError:
                            pass
                    if s.running:
                        agentlock.release(film, s.id, s.turn)
                    return False
                try:
                    (old / f"{s.id}.json").unlink()
                except OSError:
                    pass
                s.project, s.root, s.key = film, str(film), key
                s.log = new / f"{s.id}.jsonl"
                s.header["placed"] = film.name
        s.emit("notice", code="placed", key=key, name=film.name)
        return True

    def went(self, sid, space):
        """Where a conversation begun on the space went: (its film's folder) when it made one, else None."""
        s = self.sessions.get(sid) if isinstance(sid, str) and ID_RE.match(sid) else None
        if s is not None and s.header.get("space") and not s.unplaced:
            return s.root
        try:
            film = (Path(space) / ".ovh" / "agents" / f"{sid}.placed").read_text().strip() if space and ID_RE.match(str(sid)) else ""
        except OSError:
            return None
        return film if film and (Path(film) / ".ovh" / "agents" / f"{sid}.jsonl").exists() else None

    def _watch(self):
        """A request with no page to answer it: after APPROVAL_TIMEOUT seconds without one, it is rejected."""
        while not self.closed:
            time.sleep(1.0)
            now = time.time()
            for s in list(self.sessions.values()):
                for rid, p in list(s.pending.items()):
                    if s.subscribers or s.unplaced and self.present and self.present():   # (the space lists one that waits, while Studio is open)
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
        for j in list(self.installs.values()):   # an install the person started here stops with the console (npm ci begins afresh next time)
            _stop_group(j.get("proc"))
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
        for t in threads + self._closing:
            t.join(timeout=10)
        self.peers.clear()
