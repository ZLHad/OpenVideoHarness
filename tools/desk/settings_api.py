"""Studio's settings page, the server's half: GET /api/settings and POST /api/settings (server.py hands both here).

What a person can change from the page is kept in this machine's settings file and nowhere else, written through
tools/settings.py (never the file itself): Studio's language and look, the agent a new chat starts with, the download
mirrors. The model and effort a new chat starts with stay where the agent column keeps them (picks.json, agents.py), and
only a value the agent offered is ever set. LOCAL.md's lines that people and agents both read (effort, the way a stop is
looked at, budget, asset licences, sound library, who decides) are shown, never written: the page says to ask the agent.

Both routes need this run's token. GET answers {version: 1, file, studio, mirror, agents, roots, local, about}; POST takes
{name, value} (studio_lang, studio_theme, agent_default, mirror, model:<kind>, effort:<kind>) and answers the same as GET,
or {name: "reveal", value: <one of roots' paths>}: that folder opens in the system's file browser ($OVH_REVEAL, a command,
stands in for it; twenty a minute).

The services (tools/modules.json's services with needs.keys): GET's services lists each with its keys, where a command
finds each (env, studio or none) and whether one is saved in Studio, never a key itself; store says what keeps them
(keychain, secret-service or none: tools/keys.py). POST {name: "key:<NAME>", value: <the key> or null} saves or takes out
the key saved in Studio; {name: "test:<module>"} asks the service once at its free address (bin/vh doctor --probe --only
<module>; $OVH_PROBE_OFFLINE: answered from that folder's recordings), ten a minute, → {ok, probe: {state, note}}.
"""
import os, re, secrets, subprocess, sys, threading, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
import settings as S   # noqa: E402  (tools/settings.py: this machine's settings file, its one reader and writer)
import agents as A     # noqa: E402
import projects as PJ  # noqa: E402  (where this console looks for films)
import keys as K       # noqa: E402  (tools/keys.py: the services' keys, the environment's or saved in this computer's store)
import json            # noqa: E402

# LOCAL.md's lines shown on the page: id → the labels a line may start with (as the tools that read them accept)
LOCAL_LINES = (
    ("effort", r"默认努力程度|努力程度|默认档位|档位|default\s+effort|effort"),
    ("review", r"审阅方式|review(?:\s+(?:channel|surface|mode))?"),
    ("director", r"默认导演模式|导演模式|director"),
    ("subagent", r"子代理模型|subagent\s+model"),
    ("budget", r"默认预算|default\s+budget|budget"),
    ("assets", r"素材许可|许可策略|assets(?:\s+policy)?"),
    ("sound", r"声音库|sound\s+library"),
)


def local_md():
    """The harness's LOCAL.md, or the file OVH_LOCAL_MD names (as tools/gatecheck.py reads it)."""
    return Path(os.environ.get("OVH_LOCAL_MD") or WORKSPACE / "LOCAL.md")


def local_lines():
    """{file, exists, lines: {id: value or None}}: the list item ("- label：value") that names it, its bracketed hint
    left out; a line still the template's {…}, empty or missing is None."""
    p = local_md()
    try:
        text = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8", errors="replace"), flags=re.S)
    except OSError:
        return {"file": str(p), "exists": False, "lines": {k: None for k, _ in LOCAL_LINES}}
    out = {}
    for k, labels in LOCAL_LINES:
        m = re.search(rf"^[-*][ \t]+(?:\*\*)?(?:{labels})(?:\*\*)?[ \t]*[:：][ \t]*(.*?)[ \t]*$", text, re.I | re.M)
        v = m.group(1).strip() if m else ""
        while re.search(r"[（(][^（）()]*[）)]$", v):   # the template's hint after a value: "standard（不填就是 standard；…）"
            v = re.sub(r"\s*[（(][^（）()]*[）)]$", "", v)
        v = v.strip().strip("*`").strip()
        out[k] = None if not v or v.startswith("{") else v[:200]
    return {"file": str(p), "exists": True, "lines": out}


RELEASES = "https://github.com/ZLHad/OpenVideoHarness/releases"


def version():
    """{version, url}: the release this clone is at (its tag), else its commit; the release's page, else all releases."""
    def git(*a):
        try:
            r = subprocess.run(["git", "-C", str(WORKSPACE), *a], capture_output=True, text=True, timeout=5, stdin=subprocess.DEVNULL)
            return r.stdout.strip() if r.returncode == 0 else ""
        except (OSError, subprocess.SubprocessError):
            return ""
    tag = git("describe", "--tags", "--abbrev=0", "--match", "v[0-9]*")
    exact = tag and git("describe", "--tags", "--exact-match", "--match", "v[0-9]*") == tag
    head = git("rev-parse", "--short", "HEAD")
    v = tag if exact else f"{tag} + {head}" if tag and head else head or None
    return {"version": v, "url": f"{RELEASES}/tag/{tag}" if tag else RELEASES}


def shown(p):
    """A folder as a person reads it: ~ for the home folder."""
    home = os.path.realpath(str(Path.home()))
    return "~" + p[len(home):] if p == home or p.startswith(home + os.sep) else p


def roots(given):
    """The folders this console finds films in, those that exist: {path, shown}."""
    out = []
    for r in PJ.roots_of(given):
        if r.get("exists"):
            p = os.path.realpath(os.path.expanduser(r["path"]))
            out.append({"path": p, "shown": shown(p)})
    return out


def services():
    """[{module, keys: [{name, source, saved}], cost, key_url, probe}]: the services a key opens, as tools/modules.json has them."""
    try:
        t = json.loads((WORKSPACE / "tools" / "modules.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for m in t.get("modules") or []:
        names = (m.get("needs") or {}).get("keys") or []
        if m.get("kind") != "service" or not names:
            continue
        ks = []
        for n in names:
            saved = bool(K.stored(n))
            ks.append({"name": n, "source": "env" if os.environ.get(n) else "studio" if saved else None, "saved": saved})
        out.append({"module": m["name"], "keys": ks, "cost": m.get("cost"), "key_url": m.get("key_url"), "probe": bool(m.get("probe"))})
    return out


def state(mgr, given=()):
    d = S.load()
    st = S.studio(d)
    kinds = A.catalog()
    return {"version": 1, "file": str(S.path()), "studio": st,
            "mirror": {"mode": S.mirror(d), "why": d.get("mirror_why"), "at": d.get("mirror_at")},
            "agents": {"default": st["agent_default"],
                       "kinds": [{"kind": a["kind"], "label": a["label"], "installed": a["installed"], "size": a["size"],
                                  "choices": mgr.choices(a["kind"]) if mgr else None} for a in kinds]},
            "roots": roots(given), "local": local_lines(), "services": services(), "store": K.store_kind(),
            "about": dict(version(), workspace=shown(os.path.realpath(WORKSPACE)))}


def token_ok(handler):
    given = handler.headers.get("X-Desk-Token", "").encode("utf-8", "replace")
    return secrets.compare_digest(given, handler.server.token.encode("ascii"))


def get(handler):
    if not token_ok(handler):
        return handler._error(403, "missing or wrong desk token: reload the page")
    return handler._json(state(handler.server.agents, handler.server.roots))


REVEALED, REVEAL_LOCK, TESTED = [], threading.Lock(), []


def test(module):
    """Ask one service once at its free address (bin/vh doctor's probe) → {state, note}: never a key in what comes back."""
    if module not in {s["module"] for s in services()}:
        raise ValueError(f"test: {module!r} is not a service with a key")
    with REVEAL_LOCK:
        now = time.time()
        TESTED[:] = [x for x in TESTED if now - x < 60]
        if len(TESTED) >= 10:
            raise PermissionError("asked too often: try again in a minute")
        TESTED.append(now)
    argv = [os.environ.get("OVH_BASH") or "bash", str(WORKSPACE / "bin" / "vh"), "doctor", "--json", "--probe", "--only", module]
    if os.environ.get("OVH_PROBE_OFFLINE"):
        argv += ["--offline", os.environ["OVH_PROBE_OFFLINE"]]
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=60, stdin=subprocess.DEVNULL)
        m = next(x for x in json.loads(r.stdout)["modules"] if x["name"] == module)
        return m.get("probe") or {"state": "skipped", "note": "not asked"}
    except (OSError, ValueError, StopIteration, KeyError, subprocess.SubprocessError) as e:
        return {"state": "failed", "note": f"could not ask ({type(e).__name__})"}


def reveal(path):
    """Open one folder in the system's file browser (Finder, the desktop's own), as the person asked on the page."""
    with REVEAL_LOCK:
        now = time.time()
        REVEALED[:] = [x for x in REVEALED if now - x < 60]
        if len(REVEALED) >= 20:
            raise PermissionError("asked too often: try again in a minute")
        REVEALED.append(now)
    cmd = os.environ.get("OVH_REVEAL") or ("open" if sys.platform == "darwin" else "xdg-open")
    subprocess.Popen([cmd, path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def post(handler):
    raw = handler._body(4096)
    if raw is None:
        return
    name, value = raw.get("name"), raw.get("value")
    if not isinstance(name, str) or not (value is None or isinstance(value, str)):
        return handler._error(400, "send {name, value}: value a string, or null for Studio's default")
    try:
        if name == "reveal":   # only one of this console's own film folders, never a path the page makes up
            if value not in {r["path"] for r in roots(handler.server.roots)}:
                raise ValueError("reveal: not one of the folders Studio finds films in")
            reveal(value)
            return handler._json({"ok": True})
        if name.startswith("key:"):   # a key: saved in (or taken out of) this computer's store; never said back
            n = name[4:]
            if n not in K.KEY_NAMES:
                raise ValueError(f"{n}: not the name of a key a service needs")
            if value is None:
                K.clear(n)
            else:
                K.save(n, value)
            return handler._json(state(handler.server.agents, handler.server.roots))
        if name.startswith("test:"):
            return handler._json({"ok": True, "probe": test(name[5:])})
        if name == "agent_default" and value is not None and not (value in A.ADAPTERS and A.installed(value)):
            raise ValueError(f"agent_default: {value!r} is not set up in Studio")
        if name in S.STUDIO:
            S.set_studio(name, value)
        elif name == "mirror":
            if value not in S.MODES:
                raise ValueError(f"mirror: one of {', '.join(S.MODES)}")
            S.set_mirror(value, "set in Studio's settings")
        elif re.fullmatch(r"(model|effort):(\w+)", name):
            role, kind = name.split(":")
            offered = ((handler.server.agents.choices(kind) if kind in A.ADAPTERS else {}).get("offered") or {}).get(role) or []
            if value not in {x["value"] for x in offered}:   # only what this kind of agent offered in a chat this run
                raise ValueError(f"{name}: not a value this agent offered")
            A.remember(kind, role, value)
            if (A.picks().get(kind) or {}).get(role) != value:   # (remember says nothing when it cannot write)
                raise OSError(f"{A.picks_path()} was not written")
        else:
            raise ValueError(f"{name}: not a setting Studio changes")
    except PermissionError as e:
        return handler._error(429, str(e))
    except ValueError as e:
        return handler._error(400, str(e))
    except OSError as e:
        return handler._error(500, f"could not keep it: {e}")   # (tools/keys.py's messages name the key's variable, never the key)
    return handler._json(state(handler.server.agents, handler.server.roots))
