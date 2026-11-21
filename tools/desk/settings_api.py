"""Studio's settings page, the server's half: GET /api/settings and POST /api/settings (server.py hands both here).

What a person can change from the page is kept in this machine's settings file and nowhere else, written through
tools/settings.py (never the file itself): Studio's language and look, the agent a new chat starts with, the download
mirrors. The model and effort a new chat starts with stay where the agent column keeps them (picks.json, agents.py), and
only a value the agent offered is ever set. LOCAL.md's lines that people and agents both read (effort, the way a stop is
looked at, budget, asset licences, sound library, who decides) are shown, never written: the page says to ask the agent.

Both routes need this run's token. GET answers {version: 1, file, studio, mirror, agents, local, about}; POST takes
{name, value} (studio_lang, studio_theme, agent_default, mirror, model:<kind>, effort:<kind>) and answers the same as GET.
"""
import os, re, secrets, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent.parent
sys.path.insert(0, str(HERE.parent))
import settings as S   # noqa: E402  (tools/settings.py: this machine's settings file, its one reader and writer)
import agents as A     # noqa: E402

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
    """{file, exists, lines: {id: value or None}}: a line still the template's {…}, empty or missing is None."""
    p = local_md()
    try:
        text = re.sub(r"<!--.*?-->", "", p.read_text(encoding="utf-8", errors="replace"), flags=re.S)
    except OSError:
        return {"file": str(p), "exists": False, "lines": {k: None for k, _ in LOCAL_LINES}}
    out = {}
    for k, labels in LOCAL_LINES:
        m = re.search(rf"^[ \t]*[-*]?[ \t]*(?:\*\*)?(?:{labels})(?:\*\*)?[ \t]*[:：][ \t]*(.*?)[ \t]*$", text, re.I | re.M)
        v = m.group(1).strip().strip("*`").strip() if m else ""
        out[k] = None if not v or v.startswith("{") else v[:200]
    return {"file": str(p), "exists": True, "lines": out}


def version():
    try:
        m = re.search(r'^version:\s*"?([^"\n]+)"?', (WORKSPACE / "CITATION.cff").read_text(encoding="utf-8"), re.M)
        return m.group(1).strip() if m else None
    except OSError:
        return None


def state(mgr):
    d = S.load()
    st = S.studio(d)
    kinds = A.catalog()
    return {"version": 1, "file": str(S.path()), "studio": st,
            "mirror": {"mode": S.mirror(d), "why": d.get("mirror_why"), "at": d.get("mirror_at")},
            "agents": {"default": st["agent_default"],
                       "kinds": [{"kind": a["kind"], "label": a["label"], "installed": a["installed"], "size": a["size"],
                                  "choices": mgr.choices(a["kind"]) if mgr else None} for a in kinds]},
            "local": local_lines(),
            "about": {"version": version(), "workspace": str(WORKSPACE)}}


def token_ok(handler):
    given = handler.headers.get("X-Desk-Token", "").encode("utf-8", "replace")
    return secrets.compare_digest(given, handler.server.token.encode("ascii"))


def get(handler):
    if not token_ok(handler):
        return handler._error(403, "missing or wrong desk token: reload the page")
    return handler._json(state(handler.server.agents))


def post(handler):
    raw = handler._body(4096)
    if raw is None:
        return
    name, value = raw.get("name"), raw.get("value")
    if not isinstance(name, str) or not (value is None or isinstance(value, str)):
        return handler._error(400, "send {name, value}: value a string, or null for Studio's default")
    try:
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
        else:
            raise ValueError(f"{name}: not a setting Studio changes")
    except ValueError as e:
        return handler._error(400, str(e))
    except OSError as e:
        return handler._error(500, f"could not keep it ({type(e).__name__})")
    return handler._json(state(handler.server.agents))
