"""bin/vh settings: this machine's own settings, the ones that are not secret, for every clone on it and for Studio. Stdlib only.

usage: bin/vh settings [--json]                         what they are now, and where they are kept
       bin/vh settings mirror cn|off|auto [--why TEXT]   the download mirrors (tools/mirrors.txt):
             cn    every later download comes from the mainland-China mirrors (bin/vh exports their variables)
             off   never: the official sources, and install.sh does not try the mirrors either
             auto  the official sources; install.sh tries the official npm registry once and switches to cn when it
                   does not answer and the mirror does (the default: no "mirror" key)
       bin/vh settings mirror --get                      cn, off or auto, alone on a line
       bin/vh settings chrome                            with the mirrors on, HyperFrames' Chrome from the mirror now when it
                                                         is not here (HyperFrames has no setting for where it downloads it;
                                                         bin/vh new and settings mirror cn do this by themselves)
       python3 tools/settings.py env                     the lines bin/vh and install.sh run to use the mirrors
                                                         (export NAME=value; none when the mirror is not cn, or for a
                                                         variable already set)

Kept in $XDG_CONFIG_HOME/ovh/settings.json (~/.config/ovh/settings.json): one file per machine, outside every clone, so a
git pull, a second clone or Studio's settings panel see the same values. Never a key or a token: those stay in the
environment (LOCAL.md names them, never their values). Shape, "version": 1 (keys only added, never renamed; a key
this file does not know is kept as it is when another is written):
  {"version": 1,
   "mirror": "cn" | "off",          absent: auto
   "mirror_why": "…",               who set it and why, in a sentence (install.sh's probe says what did not answer)
   "mirror_at": "YYYY-MM-DD"}
In-process (Studio): update(patch: dict) -> dict and set_mirror(mode, why=None) -> dict; load() reads, path() says where.
Every write goes through update(patch): under a lock (settings.json.lock), it reads the file as it is now, sets the keys
it was given (None takes one out), keeps all the others, and writes the whole file to a temporary file moved into place,
so two writers at once (Studio and a terminal) both land and a reader never sees half a file.
"""
import contextlib, datetime, fcntl, json, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODES = ("cn", "off", "auto")


def path():
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "ovh" / "settings.json"


def load():
    """The settings as kept, or {"version": 1} (none yet, or a file that is not a JSON object: said on stderr)."""
    p = path()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"version": 1}
    except (OSError, ValueError) as e:
        print(f"bin/vh settings: {p} is not readable JSON ({e}); taken as empty", file=sys.stderr)
        return {"version": 1}
    return d if isinstance(d, dict) else {"version": 1}


@contextlib.contextmanager
def locked():
    """The settings file's lock (settings.json.lock beside it, never removed: another process may hold the old one): held
    by every write, so Studio and a terminal writing at once both land."""
    p = path(); p.parent.mkdir(parents=True, exist_ok=True)
    with open(str(p) + ".lock", "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def _write(d):
    p = path()
    fd, tmp = tempfile.mkstemp(prefix=".settings.", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(dict(d, version=1), ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def update(patch):
    """The one way to write: under the lock, read the file as it is now, set each key of patch (None takes a key out), keep
    every other key (another writer's, or one this code does not know), and write the whole file to a temp file moved into
    place. → the settings as written. Studio's settings panel and bin/vh settings both go through it."""
    with locked():
        d = load()
        for k, v in patch.items():
            if k == "version":
                continue
            if v is None:
                d.pop(k, None)
            else:
                d[k] = v
        _write(d)
    return d


def set_mirror(mode, why=None):
    """The mirror setting, as bin/vh settings mirror <mode> [--why TEXT] writes it, through update(), saying nothing (Studio's
    settings panel calls it in-process; main() calls it and does the saying). mode: cn, off or auto (auto takes the keys
    out). → the settings as written. It does not fetch HyperFrames' Chrome from the mirror: bin/vh settings mirror cn and
    bin/vh new do that (bin/vh settings chrome alone)."""
    if mode not in MODES:
        raise ValueError(f"mirror: {mode!r} is not one of {', '.join(MODES)}")
    on = mode != "auto"
    return update({"mirror": mode if on else None, "mirror_at": datetime.date.today().isoformat() if on else None,
                   "mirror_why": why if on and why else None})


def save(d):
    """Write these keys (as update: under the lock, onto what is there now, nothing else taken out)."""
    return update(d)


def mirror(d=None):
    m = (d if d is not None else load()).get("mirror")
    return m if m in ("cn", "off") else "auto"


def mirrors():
    """tools/mirrors.txt → [{kind, variable, official, mirror, who}]."""
    rows = []
    for line in (ROOT / "tools" / "mirrors.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        kind, var, official, mir, who = line.split(None, 4)
        rows.append({"kind": kind, "variable": None if var == "-" else var, "official": official, "mirror": mir, "who": who})
    return rows


def env_lines(environ=os.environ):
    """export lines for the mirror variables, when the mirror is cn; a variable already set (by the person) is left."""
    if mirror() != "cn":
        return []
    out = [f"export {r['variable']}={r['mirror']}" for r in mirrors() if r["variable"] and not environ.get(r["variable"])]
    return out + ["export OVH_MIRROR=cn"]


def in_effect(environ=os.environ):
    """The mirror variables as this process has them (bin/vh exports them before it runs a tool): {name: value or None}."""
    return {r["variable"]: environ.get(r["variable"]) for r in mirrors() if r["variable"]}


def operators():
    """The mirrors' operators by name, each once: "npmmirror.com, TUNA and hf-mirror.com"."""
    names = list(dict.fromkeys(r["who"].split(",")[0] for r in mirrors()))
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]


def show(d, as_json=False):
    m = mirror(d)
    if as_json:
        print(json.dumps({"version": 1, "tool": "bin/vh settings", "file": str(path()), "settings": d, "mirror": m,
                          "mirrors": mirrors(), "environment": in_effect()}, ensure_ascii=False, indent=1))
        return
    print(f"this machine's settings: {path()}" + ("" if path().exists() else " (not written yet: the defaults)"))
    said = {"cn": "the mainland-China mirrors, for every download (tools/mirrors.txt)",
            "off": "the official sources; install.sh does not try the mirrors",
            "auto": "the official sources; install.sh switches to the mirrors when the official npm registry does not answer"}[m]
    print(f"  mirror  {m}: {said}" + (f" · {d['mirror_why']}" if d.get("mirror_why") else "")
          + (f" ({d['mirror_at']})" if d.get("mirror_at") else ""))
    print("  bin/vh settings mirror cn|off|auto changes it")


def main(argv):
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__.strip()); return 0
    if argv == ["env"]:
        print("\n".join(env_lines())); return 0
    if not argv or argv == ["--json"]:
        show(load(), bool(argv)); return 0
    if argv[0] == "mirror":
        if argv[1:] == ["--get"]:
            print(mirror()); return 0
        if len(argv) < 2 or argv[1] not in MODES or (len(argv) > 2 and (argv[2] != "--why" or len(argv) != 4)):
            print("usage: bin/vh settings mirror cn|off|auto [--why TEXT]   (or --get)", file=sys.stderr); return 2
        set_mirror(argv[1], argv[3] if len(argv) == 4 else None)
        if argv[1] == "cn":
            print(f"✓ downloads now come from the mainland-China mirrors ({operators()}; tools/mirrors.txt), kept in {path()};"
                  " bin/vh settings mirror off turns that off")
        else:
            print(f"✓ downloads come from the official sources{'' if argv[1] == 'auto' else ', and install.sh does not try the mirrors'} (kept in {path()})")
        return 0
    print(f"bin/vh settings: unknown {' '.join(argv)} (bin/vh settings -h)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
