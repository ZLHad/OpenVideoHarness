"""The API keys of the outside services (tools/modules.json's needs.keys), looked up one way by every command: the
environment first, as before, then the key the person saved in Studio's settings page, kept in this computer's own
password store (macOS: the Keychain; Linux: the Secret Service through secret-tool, when there is one). Stdlib only.

A key never goes into a file, a log, a URL, an event or the page, and never onto a command line (where the process list
shows it): it is written to the store through standard input. Only names in KEY_NAMES are read or written here.

usage: python3 tools/keys.py has <NAME>       exit 0 when a command would find that key (environment or store), else 1
       python3 tools/keys.py where            each name: env, studio or -, and what kind of store this computer has
       (there is no command that prints a key)

Tests: OVH_KEYCHAIN=<file> names a keychain of their own on every call (macOS), OVH_KEYSTORE_SERVICE a service name of
their own, OVH_SECRET_TOOL a stand-in for secret-tool (Linux); OVH_KEYSTORE=none turns the store off.
"""
import json, os, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALUE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:+/=-]{7,511}")   # what a provider's API key looks like: no space, no quote, no newline
_CACHE = {}


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
                                   timeout=5, stdin=subprocess.DEVNULL)
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


def _run(argv, stdin=None):
    try:
        return subprocess.run(argv, input=stdin, capture_output=True, text=True, timeout=10,
                              stdin=None if stdin is not None else subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None


def stored(name):
    """The key saved in Studio for this name, or None (no store, nothing saved, the store did not answer)."""
    _known(name)
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
        raise ValueError(f"{name}: that is not an API key (8 to 512 letters, digits and . _ : + / = -, starting with a letter or digit)")
    kind = store_kind()
    if kind == "keychain":   # security's own prompt reads the line on stdin: the key never is an argument of a process
        r = _run(["security", "-i"], stdin=f'add-generic-password -U -s "{service()}" -a {name} -l "{service()} {name}" -w {value} {" ".join(chr(34) + k + chr(34) for k in _keychain())}\n')
    elif kind == "secret-service":
        r = _run([_secret_tool(), "store", f"--label={service()} {name}", "service", service(), "key", name], stdin=value)
    else:
        raise OSError("this computer has no password store: the key can only come from the environment")
    if r is None or r.returncode != 0 or stored(name) != value:
        raise OSError(f"{name} was not saved ({kind} did not take it)")


def clear(name):
    """Take the key saved for this name out of the store (nothing saved: nothing to do)."""
    _known(name)
    kind = store_kind()
    if kind == "keychain":
        _run(["security", "delete-generic-password", "-s", service(), "-a", name, *_keychain()])
    elif kind == "secret-service":
        _run([_secret_tool(), "clear", "service", service(), "key", name])
    if stored(name):
        raise OSError(f"{name} is still saved ({kind} did not take it out)")


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
