"""The API keys of the outside services (tools/modules.json's needs.keys), looked up one way by every command: the
environment first, as before, then the key the person saved in Studio's settings page, kept in this computer's own
password store (macOS: the Keychain; Linux: the Secret Service through secret-tool, when there is one). Stdlib only.

A key never goes into a file, a log, a URL, an event or the page, and never onto a command line (where the process list
shows it): it is written to the store through standard input. Only names in KEY_NAMES are read or written here.

A command that stops because a key is missing says one sentence, the same everywhere (missing()): which service and key,
where to set it (Studio's Settings → Services, or the environment), where to get one, and what works with none; stopping()
also puts it on the run's record with the code no_key (tools/jsonerr.py), which bin/vh status and Studio say while the
film waits on that key (tools/standing.py).

usage: python3 tools/keys.py has <NAME>       exit 0 when a command would find that key (environment or store), else 1
       python3 tools/keys.py where            each name: env, studio or -, and what kind of store this computer has
       (there is no command that prints a key)

"The environment first" is per name: MINIMAX_API_KEY set in the environment and MINIMAX_TOKEN_PLAN_KEY saved in Studio
are both found, and tts.py's MiniMax takes the Token Plan key first, wherever each came from.

A process asks the store once per name (what it found, nothing, or no answer within LOOKUP_S seconds, is remembered
until save or clear changes that name, or forget()): a store that is slow or locked costs a command a few seconds once,
never on every request of a long run.

Who can read a saved key: the item is made by /usr/bin/security with the Keychain's default access, so any program run
as this user (an agent in Studio's column included) reads it without a prompt, as it could read the person's shell
files. The Secret Service is the same once the person's login has unlocked it.

Tests: OVH_KEYCHAIN=<file> names a keychain of their own on every call (macOS), OVH_KEYSTORE_SERVICE a service name of
their own, OVH_SECRET_TOOL a stand-in for secret-tool (Linux); OVH_KEYSTORE=none turns the store off. tools/ci.sh sets
OVH_KEYSTORE=none for all its checks and passes it on where a check builds an environment of its own (acp.clean_env
keeps it too); a check that never set it still runs with a scratch HOME, whose search list has no keychain of the person's.
"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALUE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+/=-]{7,2047}")   # what a provider's API key looks like (JWT-style ones run past 600): no space, quote or newline
LOOKUP_S, WRITE_S = 3, 10   # seconds a store may take to answer a lookup, and a save or a clear
_CACHE, _FOUND = {}, {}   # the store's kind; name → the saved key or None, as this process last asked the store


def key_names():
    """Every key a service in tools/modules.json needs, in the table's order."""
    try:
        t = json.loads((ROOT / "tools" / "modules.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for m in t.get("modules") or []:
        for k in ((m.get("needs") or {}).get("keys") or []):
            if k not in out:
                out.append(k)
    return out


KEY_NAMES = key_names()


def service():
    return os.environ.get("OVH_KEYSTORE_SERVICE") or "OpenVideoHarness"


class NotAKey(ValueError):
    """A value that does not look like an API key (Studio's page says so in the person's language)."""


class NotKept(OSError):
    """The store did not take a save or a clear, or there is no store."""


def _known(name):
    if name not in KEY_NAMES:
        raise ValueError(f"{name}: not the name of a key a service needs (tools/modules.json)")


def store_kind():
    """keychain, secret-service or none: where a key saved in Studio is kept on this computer."""
    if "kind" in _CACHE:
        return _CACHE["kind"]
    kind = "none"
    if os.environ.get("OVH_KEYSTORE") != "none":
        if sys.platform == "darwin" and shutil.which("security"):
            kind = "keychain"
        elif sys.platform.startswith("linux") and _secret_tool():
            try:   # a lookup of nothing: exit 1 when the Secret Service answers, an error message when there is none to answer
                r = subprocess.run([_secret_tool(), "lookup", "service", service(), "key", "-"], capture_output=True, text=True,
                                   timeout=LOOKUP_S, stdin=subprocess.DEVNULL)
                kind = "secret-service" if r.returncode in (0, 1) and not r.stderr.strip() else "none"
            except (OSError, subprocess.SubprocessError):
                kind = "none"
    _CACHE["kind"] = kind
    return kind


def _secret_tool():
    return os.environ.get("OVH_SECRET_TOOL") or shutil.which("secret-tool")


def _keychain():
    k = os.environ.get("OVH_KEYCHAIN")
    return [k] if k else []


def _run(argv, stdin=None, timeout=LOOKUP_S):
    try:
        return subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=timeout,
                              stdin=None if stdin is not None else subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None


def stored(name):
    """The key saved in Studio for this name, or None (no store, nothing saved, the store did not answer): asked once
    per process, then remembered."""
    _known(name)
    if name not in _FOUND:
        _FOUND[name] = _lookup(name)
    return _FOUND[name]


def forget(name=None):
    """Ask the store again next time (one name, or all): for a long-running process when something else changed it."""
    if name is None:
        _FOUND.clear()
    else:
        _FOUND.pop(name, None)


def _lookup(name):
    kind = store_kind()
    if kind == "keychain":
        r = _run(["security", "find-generic-password", "-s", service(), "-a", name, "-w", *_keychain()])
    elif kind == "secret-service":
        r = _run([_secret_tool(), "lookup", "service", service(), "key", name])
    else:
        return None
    v = r.stdout.strip() if r is not None and r.returncode == 0 else ""
    return v or None


def get(name):
    """What a command uses for this key: the environment's when it is set (it wins), else the one saved in Studio, else None."""
    _known(name)
    return os.environ.get(name) or stored(name)


def source(name):
    """env, studio or None: where a command would find this key (the value is not handed back)."""
    _known(name)
    return "env" if os.environ.get(name) else "studio" if stored(name) else None


def save(name, value):
    """Save (or replace) the key for this name in this computer's store. ValueError: an unknown name, a value that is not
    a key; OSError: no store, or it did not take it."""
    _known(name)
    if not isinstance(value, str) or not VALUE.fullmatch(value):
        raise NotAKey(f"{name}: that is not an API key (8 to 2048 letters, digits and . _ : + / = -, starting with a letter or digit)")
    kind = store_kind()
    if kind == "keychain":   # security's own prompt reads the line on stdin: the key never is an argument of a process
        r = _run(["security", "-i"], timeout=WRITE_S, stdin=f'add-generic-password -U -s "{service()}" -a {name} -l "{service()} {name}" -w {value} {" ".join(chr(34) + k + chr(34) for k in _keychain())}\n')
    elif kind == "secret-service":
        r = _run([_secret_tool(), "store", f"--label={service()} {name}", "service", service(), "key", name], stdin=value, timeout=WRITE_S)
    else:
        raise NotKept("this computer has no password store: the key can only come from the environment")
    _FOUND[name] = _lookup(name)   # what the store holds now, asked afresh
    if r is None or r.returncode != 0 or _FOUND[name] != value:
        raise NotKept(f"{name} was not saved ({kind} did not take it)")


def clear(name):
    """Take the key saved for this name out of the store (nothing saved: nothing to do)."""
    _known(name)
    kind = store_kind()
    if kind == "keychain":
        _run(["security", "delete-generic-password", "-s", service(), "-a", name, *_keychain()], timeout=WRITE_S)
    elif kind == "secret-service":
        _run([_secret_tool(), "clear", "service", service(), "key", name], timeout=WRITE_S)
    _FOUND[name] = _lookup(name)
    if _FOUND[name]:
        raise NotKept(f"{name} is still saved ({kind} did not take it out)")


SERVICE = {"gemini": "Gemini", "minimax": "MiniMax", "elevenlabs": "ElevenLabs", "dashscope": "Alibaba Cloud Model Studio"}   # as Studio's page names them


def module_of(name):
    """tools/modules.json's service whose keys include this name, or None."""
    try:
        t = json.loads((ROOT / "tools" / "modules.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return next((m for m in t.get("modules") or [] if name in ((m.get("needs") or {}).get("keys") or [])), None)


def missing(names, instead=None):
    """The sentence for a command that stops because none of these keys (one service's) is set."""
    names = [names] if isinstance(names, str) else list(names)
    m = module_of(names[0]) or {}
    said = " or ".join(names)
    s = f"no {SERVICE.get(m.get('name'), m.get('name') or 'service')} API Key ({said}): paste one into Studio's Settings → Services"
    if m.get("key_url"):
        s += f" (get one at {m['key_url']})"
    s += f", or set {said} in the environment"
    return s + (f"; {instead}" if instead else "")


def stopping(names, instead=None):
    """missing(), put on the run's record with the code no_key (once a run; nothing outside a logged run): → the sentence,
    for the caller to print and stop with."""
    msg = missing(names, instead)
    try:
        import jsonerr
        jsonerr.report("no_key", msg, "Studio's Settings → Services takes the key")
    except Exception:   # the sentence is said all the same
        pass
    return msg


def wanted(names):
    """The key names a no_key message names that are still not set: [] once any of them is (the film waits no more)."""
    names = [n for n in names if n in KEY_NAMES]
    return [] if any(get(n) for n in names) else names


def main(argv):
    if argv[:1] in (["-h"], ["--help"]) or not argv:
        print(__doc__.strip()); return 0 if argv else 2
    if argv[0] == "has" and len(argv) == 2 and argv[1] in KEY_NAMES:
        return 0 if get(argv[1]) else 1
    if argv == ["where"]:
        print(f"store: {store_kind()}")
        for k in KEY_NAMES:
            print(f"  {k}  {source(k) or '-'}")
        return 0
    print("usage: python3 tools/keys.py has <NAME> | where", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
