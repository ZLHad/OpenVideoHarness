"""bin/vh settings: this machine's own settings, the ones that are not secret, for every clone on it and for Studio. Stdlib only.

usage: bin/vh settings [--json]                         what they are now, and where they are kept
       bin/vh settings mirror cn|off|auto [--why TEXT]   the download mirrors (tools/mirrors.txt):
             cn    later downloads come from the mainland-China mirrors (bin/vh exports their variables for everything
                   it runs, the agents Studio starts included)
             off   never: the official sources, and the installer does not try the mirrors either
             auto  the official sources; the installer tries the official npm registry, Hugging Face and Google's storage
                   (Chrome) and switches to cn when one does not answer twice and its mirror does (the default: no
                   "mirror" key)
       bin/vh settings mirror --get                      cn, off or auto, alone on a line
       bin/vh settings chrome [project]                  with the mirrors on, HyperFrames' Chrome from the mirror now when it
                                                         is not here (HyperFrames has no setting for where it downloads it;
                                                         bin/vh new, render, hf, frames and settings mirror cn do this by
                                                         themselves); project: that project's HyperFrames, else styles/_swatch's
       python3 tools/settings.py env [--mode cn]         the lines bin/vh and the installer run (export NAME=value, unset NAME):
                                                         with cn, the mirror variables; otherwise none, and the ones bin/vh
                                                         exported before (inherited: OVH_MIRROR=cn) taken out again

Kept in $XDG_CONFIG_HOME/ovh/settings.json (~/.config/ovh/settings.json; an XDG_CONFIG_HOME that is not an absolute path
is ignored, as the XDG spec says): one file per machine, outside every clone, so a git pull, a second clone or Studio's
settings panel see the same values. Never a key or a token: those stay in the environment (LOCAL.md names them, never their
values). Shape, "version": 1 (keys only added, never renamed; a key this file does not know is kept as it is when another
is written):
  {"version": 1,
   "mirror": "cn" | "off",          absent: auto
   "mirror_why": "…",               who set it and why, in a sentence (the installer's probe says what did not answer, and how)
   "mirror_at": "YYYY-MM-DD"}
In-process (Studio): update(patch: dict) -> dict and set_mirror(mode, why=None) -> dict; load() reads, path() says where;
env_changes(environ) -> {NAME: value, or None to take it out}: what a long-lived process (Studio's server) applies to its own
environment after a change, so the agents it starts next follow it (bin/vh itself works it out again on every run).
Every write goes through update(patch): under a lock (settings.json.lock), it reads the file as it is now, sets the keys
it was given (None takes one out), keeps all the others, and writes the whole file to a temporary file moved into place,
so two writers at once (Studio and a terminal) both land and a reader never sees half a file. A file that is not a JSON
object (cut short, edited by hand) is kept beside it as settings.json.bad, said, and a fresh one written; a file of a newer
"version" is never written over (Newer). A folder it cannot write to raises OSError; the commands say so in one line.
A variable the person set stays theirs: one set in the environment (an empty one counts as not set), and npm's registry
set in an .npmrc (the person's, the project's, the global one) or uv's default index or Python mirror set in a uv.toml or
pyproject.toml, when it names a source other than the official one and the mirror: bin/vh then does not export that
one, and bin/vh settings says so.
"""
import contextlib, datetime, fcntl, json, os, re, shlex, shutil, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODES = ("cn", "off", "auto")
VERSION = 1


class Newer(Exception):
    """The file was written by a newer OpenVideoHarness ("version" above VERSION): not written over."""


def path():
    x = os.environ.get("XDG_CONFIG_HOME") or ""
    return Path(x if os.path.isabs(x) else Path.home() / ".config") / "ovh" / "settings.json"


def _read():
    """→ (the settings as kept, or None when there is no file, or "bad" when it is not a JSON object, with why)."""
    p = path()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, None
    except (OSError, ValueError) as e:
        return "bad", str(e)
    return (d, None) if isinstance(d, dict) else ("bad", f"a JSON {type(d).__name__}, not an object")


def load():
    """The settings as kept, or {"version": 1} (none yet, or a file that is not a JSON object: said on stderr)."""
    d, why = _read()
    if d == "bad":
        print(f"bin/vh settings: {path()} is not readable ({why}); taken as empty", file=sys.stderr)
    return d if isinstance(d, dict) else {"version": VERSION}


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
            f.write(json.dumps(dict(d, version=VERSION), ensure_ascii=False, indent=2) + "\n")
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def update(patch):
    """The one way to write: under the lock, read the file as it is now, set each key of patch (None takes a key out), keep
    every other key (another writer's, or one this code does not know), and write the whole file to a temp file moved into
    place. → the settings as written. A file that is not a JSON object is kept as settings.json.bad first (said on stderr);
    one of a newer version raises Newer and stays as it is. Studio's settings panel and bin/vh settings both go through it."""
    with locked():
        d, why = _read()
        if d == "bad":
            bad = path().with_name("settings.json.bad")
            shutil.copyfile(path(), bad)
            print(f"bin/vh settings: {path()} was not readable ({why}); kept as {bad.name} beside it, and a new one written",
                  file=sys.stderr)
            d = {}
        d = d or {}
        if isinstance(d.get("version"), int) and d["version"] > VERSION:
            raise Newer(f"{path()} was written by a newer OpenVideoHarness (version {d['version']}): it is left as it is; "
                        "update this clone (git pull) to change it")
        for k, v in patch.items():
            if k == "version":
                continue
            if v is None:
                d.pop(k, None)
            else:
                d[k] = v
        _write(d)
    return dict(d, version=VERSION)


def set_mirror(mode, why=None):
    """The mirror setting, as bin/vh settings mirror <mode> [--why TEXT] writes it, through update(), saying nothing (Studio's
    settings panel calls it in-process, then applies env_changes() to its own environment; main() calls it and does the
    saying). mode: cn, off or auto (auto takes the keys out). → the settings as written. It does not fetch HyperFrames'
    Chrome from the mirror: bin/vh settings mirror cn and bin/vh new do that (bin/vh settings chrome alone)."""
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


def _same(a, b):
    return a.rstrip("/").lower() == b.rstrip("/").lower()


def _upward(cwd, names):
    """The files of these names in cwd and every folder above it, nearest first."""
    d, out = Path(cwd).resolve(), []
    while True:
        out += [d / n for n in names if (d / n).is_file()]
        if d.parent == d:
            return out
        d = d.parent


def _ini(p, key):   # the value of key=… in an .npmrc (the last one counts, as npm reads it)
    v = None
    try:
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"\s*" + re.escape(key) + r"\s*=\s*(\S+)", line)
            if m:
                v = m.group(1).strip("'\"")
    except OSError:
        pass
    return v


def _toml_url(p, keys):   # a uv setting in a uv.toml or pyproject.toml ([tool.uv]): index-url, default-index, a default [[index]]
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    if p.name == "pyproject.toml" and "[tool.uv" not in text:
        return None
    for k in keys:
        m = re.search(r'(?m)^\s*' + re.escape(k) + r'\s*=\s*["\']([^"\']+)["\']', text)
        if m:
            return m.group(1)
    if "default-index" in keys:
        for block in re.split(r"(?m)^\s*\[\[(?:tool\.uv\.)?index\]\]\s*$", text)[1:]:
            block = re.split(r"(?m)^\s*\[", block)[0]
            if re.search(r"(?m)^\s*default\s*=\s*true", block):
                m = re.search(r'(?m)^\s*url\s*=\s*["\']([^"\']+)["\']', block)
                if m:
                    return m.group(1)
    return None


def own_config(row, environ=os.environ, cwd=None):
    """Where the person's own tool configuration names a source of its own for this kind of download (not the official
    one, not the mirror): → "a sentence: the value, from which file", or None."""
    cwd = cwd or os.getcwd(); home = Path(environ.get("HOME") or Path.home())
    def other(v):
        return v and not _same(v, row["official"]) and not _same(v, row["mirror"])
    if row["kind"] in ("npm", "electron"):
        key = "registry" if row["kind"] == "npm" else "electron_mirror"
        node = shutil.which("node", path=environ.get("PATH"))
        files = _upward(cwd, [".npmrc"]) + [Path(environ.get("NPM_CONFIG_USERCONFIG") or home / ".npmrc")]
        files += [Path(environ["NPM_CONFIG_GLOBALCONFIG"])] if environ.get("NPM_CONFIG_GLOBALCONFIG") else \
                 ([Path(node).resolve().parent.parent / "etc" / "npmrc"] if node else [])
        for f in files:
            v = _ini(f, key) if f.is_file() else None
            if v is not None:   # the nearest one npm reads wins
                return f"{v} (npm's {key}, from {f})" if other(v) else None
    if row["kind"] in ("pypi", "python"):
        keys = ("index-url", "default-index") if row["kind"] == "pypi" else ("python-install-mirror",)
        xdg = environ.get("XDG_CONFIG_HOME") or ""
        user = Path(xdg if os.path.isabs(xdg) else home / ".config") / "uv" / "uv.toml"
        for f in _upward(cwd, ["uv.toml", "pyproject.toml"]) + [user, Path("/etc/uv/uv.toml")]:
            v = _toml_url(f, keys) if f.is_file() else None
            if v:
                return f"{v} (uv's {keys[0]}, from {f})" if other(v) else None
        if row["kind"] == "pypi" and environ.get("UV_INDEX_URL"):   # uv's older name for the same setting
            return f"{environ['UV_INDEX_URL']} (UV_INDEX_URL)"
    return None


def env_changes(environ=os.environ, mode=None, cwd=None):
    """What bin/vh (and the installer, and Studio's server) does to its environment for the mirror setting: {NAME: value to
    export, or None to take out}. With cn: each mirror variable not set by the person (unset or empty, or already the
    mirror's value) and not named by their own npm or uv configuration, and OVH_MIRROR=cn. Otherwise, only when the
    environment came from a bin/vh run under cn (OVH_MIRROR=cn inherited): OVH_MIRROR, and each mirror variable that
    still holds exactly the mirror's value, taken out; nothing else is touched."""
    mode = mode or mirror()
    out = {}
    if mode == "cn":
        for r in mirrors():
            v = r["variable"]
            if v and (not environ.get(v) or environ.get(v) == r["mirror"]) and not own_config(r, environ, cwd):
                if environ.get(v) != r["mirror"]:
                    out[v] = r["mirror"]
        if environ.get("OVH_MIRROR") != "cn":
            out["OVH_MIRROR"] = "cn"
        return out
    if environ.get("OVH_MIRROR"):
        out["OVH_MIRROR"] = None
        for r in mirrors():
            if r["variable"] and environ.get(r["variable"]) == r["mirror"]:
                out[r["variable"]] = None
    return out


def env_lines(environ=os.environ, mode=None):
    """env_changes() as shell lines: export NAME=value, unset NAME."""
    return [f"export {k}={shlex.quote(v)}" if v is not None else f"unset {k}" for k, v in env_changes(environ, mode).items()]


def kept_own(environ=os.environ):
    """With cn, the mirror variables bin/vh leaves alone because the person set them: [(kind, why)]."""
    out = []
    for r in mirrors():
        if not r["variable"]:
            continue
        mine = environ.get(r["variable"])
        if mine and mine != r["mirror"]:
            out.append((r["kind"], f"{mine} ({r['variable']}, set in the environment)"))
        else:
            o = own_config(r, environ)
            if o:
                out.append((r["kind"], o))
    return out


def in_effect(environ=os.environ):
    """The mirror variables as this process has them (bin/vh works them out before it runs a tool): {name: value or None}."""
    return {r["variable"]: environ.get(r["variable"]) for r in mirrors() if r["variable"]}


def operators():
    """The mirrors' operators by name, each once: "npmmirror.com, TUNA and hf-mirror.com"."""
    names = list(dict.fromkeys(r["who"].split(",")[0] for r in mirrors()))
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]


def show(d, as_json=False):
    m = mirror(d)
    own = kept_own() if m == "cn" else []
    if as_json:
        print(json.dumps({"version": 1, "tool": "bin/vh settings", "file": str(path()), "settings": d, "mirror": m,
                          "mirrors": mirrors(), "environment": in_effect(), "kept_own": [{"kind": k, "why": w} for k, w in own]},
                         ensure_ascii=False, indent=1))
        return
    print(f"this machine's settings: {path()}" + ("" if path().exists() else " (not written yet: the defaults)"))
    said = {"cn": "the mainland-China mirrors, for the downloads tools/mirrors.txt lists",
            "off": "the official sources; the installer does not try the mirrors",
            "auto": "the official sources; the installer switches to the mirrors when an official source does not answer and its mirror does"}[m]
    print(f"  mirror  {m}: {said}" + (f" · {d['mirror_why']}" if d.get("mirror_why") else "")
          + (f" ({d['mirror_at']})" if d.get("mirror_at") else ""))
    for k, w in own:
        print(f"          {k}: your own source stays, {w}")
    print("  bin/vh settings mirror cn|off|auto changes it")


def main(argv):
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__.strip()); return 0
    if argv[:1] == ["env"]:
        mode = argv[2] if argv[1:2] == ["--mode"] and len(argv) == 3 and argv[2] in MODES else None
        if len(argv) > 1 and mode is None:
            print("usage: python3 tools/settings.py env [--mode cn|off|auto]", file=sys.stderr); return 2
        print("\n".join(env_lines(mode=mode))); return 0
    if not argv or argv == ["--json"]:
        show(load(), bool(argv)); return 0
    if argv[0] == "mirror":
        if argv[1:] == ["--get"]:
            print(mirror()); return 0
        if len(argv) < 2 or argv[1] not in MODES or (len(argv) > 2 and (argv[2] != "--why" or len(argv) != 4)):
            print("usage: bin/vh settings mirror cn|off|auto [--why TEXT]   (or --get)", file=sys.stderr); return 2
        try:
            set_mirror(argv[1], argv[3] if len(argv) == 4 else None)
        except Newer as e:
            print(f"✗ {e}", file=sys.stderr); return 1
        except OSError as e:
            print(f"✗ the choice could not be kept in {path()} ({e.strerror or e}): nothing changed", file=sys.stderr); return 1
        if argv[1] == "cn":
            print(f"✓ downloads now come from the mainland-China mirrors ({operators()}; tools/mirrors.txt), kept in {path()};"
                  " bin/vh settings mirror off turns that off")
            for k, w in kept_own():
                print(f"  {k}: your own source stays, {w}")
        else:
            print(f"✓ downloads come from the official sources{'' if argv[1] == 'auto' else ', and the installer does not try the mirrors'} (kept in {path()})")
        return 0
    print(f"bin/vh settings: unknown {' '.join(argv)} (bin/vh settings -h)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
