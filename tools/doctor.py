"""bin/vh doctor: what this machine can use, from the table of outside modules (tools/modules.json). Stdlib only.

usage: bin/vh doctor [--json] [--first] [--fill-local] [--probe [--only a,b] [--offline DIR]]
  (bin/vh passes what its own finders found: --chrome, --hf-chrome, --hf-pin, --webgl)
  --json        the same as JSON (below), the lines a person reads not printed
  --first       only the few lines a first film needs (the installer ends with them): ready or not, what is missing
                for a first silent film and how to get it, how a voice comes here. Exit 1 when it is not ready, 3 when
                nothing is missing but something could not be checked (the render browser's libraries on Linux)
  --fill-local  also write LOCAL.md's machine lines (硬件, 已装工具, 已装引擎) from this check, where they still hold
                the template's {…}; with no LOCAL.md, LOCAL.example.md is copied first. A line a person wrote stays;
                the other lines' {…} are their defaults (the installer runs this)
  --probe       also call each service that has a key set, once, at an endpoint that costs nothing (Gemini's model
                list, MiniMax's system voices, ElevenLabs' user, Model Studio's model list): is the key taken, is the
                interface there; and each public one that takes no key (scout's: fxtwitter, Bilibili's view, the hot
                lists): does it still answer the way the adapter reads it. Without it doctor never touches the network
  --only a,b    probe only these modules (by name); the others are reported without a probe
  --offline DIR the probes answered from DIR/responses.json instead, recorded the way tools/assets/fetch.py records
                ({"v": 1, "responses": [{"url", "status", "headers", "body": <file in DIR>}]}): the tests use it
  python3 tools/doctor.py --check   the table against its rules (tools/ci.sh)

Per module: the program on PATH (or found by bin/vh), its version against the table's (min: this or newer; pin: this
one; max_age_days: a dated version no older than that), the parts it needs (libx264 in ffmpeg, a skill file), the
packages in uv's cache, a model in Hugging Face's, and for a service whether one of its keys is set: only whether,
never the value. A module whose needed modules (needs.programs) are not usable here is not ok either ("needs node
(outdated)"); one not made for this platform says what to use instead (elsewhere). A probe's key travels in a header
that no redirect carries on (a 30x is not followed), over https only (a base address set in the environment may be
http for this machine alone), and no answer's text is passed on: a failure is its HTTP status and the provider's error
code, with any run of six or more of the key's characters taken out. A key is never printed, recorded or written.
The machine and repo lines end with three about the host: skills, the stubs bin/vh install-skill
wrote against the stub it would write now (a stub reads skills/ in the clone, so only the stub itself can fall behind;
a whole copy stays as it was when the repo moves on); studio-icon, the launcher bin/vh studio --install-icon makes
(installed or not, which clone it runs, made by an earlier launcher or picture); caches, whether the folders a first run downloads into (uv's,
npm's, Hugging Face's, HyperFrames', bin/vh's own) can be written, tried with a file made and removed.
Exit 0: it is a report (2 on a usage error or an unreadable table; with --first, 1 when a first film still lacks something, 3
when nothing is missing but something could not be checked).

--json, "version": 1 (these fields stay; new ones may be added): {"version", "tool", "platform", "modules": [{"name",
"kind", "status" ("planned" when nothing calls it yet, else "used"), "required", "state", "found", "version", "keys":
{VAR: true|false}, "key_source": {VAR: "env" | "studio" | null} (saved in Studio's settings: tools/keys.py), "note",
"install", "probe": {"state", "note"} | null}], "checks": [{"name", "state", "note"}],
"first_run": [what the first runs still download], "counts": {state: n}}. state: ok · missing · outdated (under the
minimum, not the pin, or older than max_age_days) · incomplete (found, a part it needs is not) · no_key · unsupported
(not on this platform) · per_project · unchecked. A probe: ok · failed · skipped.
"""
import contextlib, datetime, glob, http.client, json, os, platform, re, shutil, subprocess, sys, tempfile, time
import urllib.error, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import keys   # noqa: E402  (tools/keys.py: a key from the environment, else saved in Studio's settings)
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TABLE = ROOT / "tools" / "modules.json"
COMMANDS = ROOT / "tools" / "commands.json"
UA = "OpenVideoHarness (+https://github.com/ZLHad/OpenVideoHarness)"   # tools/assets/fetch.py's
LOCAL = ("localhost", "127.0.0.1", "::1")   # the hosts a key may reach over plain http (a local stand-in, the tests)
KINDS = ("program", "npm", "python", "model", "service", "agent")
STATES = ("ok", "missing", "outdated", "incomplete", "no_key", "unsupported", "per_project", "unchecked")
OK, NO, WA = "\033[32m✓\033[0m", "\033[31m✗\033[0m", "\033[33m!\033[0m"


def run(argv, timeout=20):
    """(exit status, stdout + stderr) of a command; (None, why) when it cannot run."""
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, errors="replace")
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)


def vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or ""))


def home(p):
    return Path(os.path.expanduser(p))


def shown(p):
    """A path as doctor prints it: in the harness relative, under home with ~."""
    p = str(p)
    if p.startswith(str(ROOT) + os.sep):
        return p[len(str(ROOT)) + 1:]
    h = str(Path.home())
    return "~" + p[len(h):] if p == h or p.startswith(h + os.sep) else p


def bytes_of(p):
    """A folder's size on disk in bytes, links followed (a Hugging Face snapshot is all links)."""
    n = 0
    for d, _, fs in os.walk(p, followlinks=True):
        for f in fs:
            try:
                n += os.stat(os.path.join(d, f)).st_blocks * 512
            except OSError:
                pass
    return n


def mb_text(n):
    mb = n / 1e6
    return f"{mb / 1000:.1f} GB" if mb >= 1000 else f"{mb:.0f} MB"


def size_of(p):
    """A folder's size on disk, links followed: "202 MB", "2.0 GB"."""
    return mb_text(bytes_of(p))


def install_says():
    """What install.sh tells someone the reference repos come to ("250 MB"), or None: the figure doctor gives when none
    is fetched, so it is written in one place."""
    try:
        m = re.search(r"reference repos \(about (\d+(?:\.\d+)? [MG]B)", (ROOT / "install.sh").read_text(encoding="utf-8"))
    except OSError:
        return None
    return m.group(1) if m else None


def references_note(have, want, fetched, said):
    """doctor's line for references/repos when not all are fetched, which is the default (they come on first use): the
    whole set's size worked out from the ones that are (fetched: their bytes), else what install.sh says (said), else none."""
    size = f"about {mb_text(fetched * want / have)}, at the size of the {have} here" if have and fetched else f"about {said}" if said else None
    return (f"{have}/{want} repos fetched; an agent fetches the one a doc points to when it first needs it (bash references/fetch.sh <dir>,"
            f" which says its size first); all {want} now: bash references/fetch.sh{' (' + size + ')' if size else ''}")


OWN_CHROME = ("darwin-arm64", "darwin-x86_64", "linux-x86_64")   # where HyperFrames downloads its own chrome-headless-shell
BROWSER_LIBS = {"libnss3.so": "libnss3", "libnspr4.so": "libnspr4"}   # what a fresh Ubuntu with ffmpeg still lacked for it (engines/README.md)


def zh_locale(env=os.environ):
    """The person's language is Chinese: the first of LC_ALL, LC_MESSAGES, LANG that is set starts with zh."""
    v = next((env[k] for k in ("LC_ALL", "LC_MESSAGES", "LANG") if env.get(k)), "")
    return v.lower().startswith("zh")


def browser_libs(plat, path=None, run=subprocess.run):
    """Linux: the system libraries the render browser needs that are missing → (missing .so names, checked). With a browser
    found, what ldd says is "not found" in it; with none yet on a platform where the first render downloads one, whether the
    linker knows libnss3 and libnspr4 (ldconfig -p). Not Linux: nothing to check ([], True). No ldd or ldconfig: ([], False)."""
    if not plat.startswith("linux"):
        return [], True
    try:
        if path and os.path.isfile(path):
            out = run(["ldd", path], capture_output=True, text=True, timeout=20).stdout
            return sorted({ln.split()[0] for ln in out.splitlines() if "not found" in ln}), True
        ldc = shutil.which("ldconfig") or ("/sbin/ldconfig" if os.path.exists("/sbin/ldconfig") else None)
        if not ldc:
            return [], False
        out = run([ldc, "-p"], capture_output=True, text=True, timeout=20).stdout
        return [so for so in BROWSER_LIBS if so not in out], True
    except (OSError, subprocess.SubprocessError):
        return [], False


def first_film(mods, checks, plat, found_by=None, env=os.environ, libs=None):
    """--first, the few lines install.sh ends with: is this machine ready for a first (silent) film, what it lacks for one,
    and how a voice comes. → (lines, "ready" | "not" | "unchecked"). Ready only with nothing missing a first film needs:
    Node, FFmpeg, Python 3, uv, a browser to render with (or a platform where the first render downloads its own) and the
    system libraries it needs (Linux), an agent, and in a Chinese locale a Chinese font. "unchecked": nothing missing, but
    the browser's libraries could not be checked. libs: browser_libs's answer, given by the tests."""
    sys.path.insert(0, str(ROOT / "tools" / "audio"))
    import firstuse
    m, c = {x["name"]: x for x in mods}, {x["name"]: x for x in checks}
    lack, unsure = [], []
    for name, what in (("node", "Node 22 or newer"), ("ffmpeg", "FFmpeg"), ("python3", "Python 3"),
                       ("uv", "uv (it runs the Python tools: contact sheets, sound checks, the voice)")):
        r = m.get(name)
        if r and r["state"] != "ok":
            lack.append(f"{what} → {r.get('install') or 'install it'}")
    own = plat in OWN_CHROME
    if (c.get("browser") or {}).get("state") != "ok" and not own:
        lack.append(f"a browser to render with → {(m.get('chrome') or {}).get('install') or 'set CHROME_PATH'}")
    elif plat.startswith("linux"):
        found_by = found_by or {}
        missing, checked = libs if libs is not None else browser_libs(plat, found_by.get("hf-chrome") or found_by.get("chrome"))
        missing = sorted(missing)
        if missing:
            pkgs = [BROWSER_LIBS[so] for so in missing if so in BROWSER_LIBS]
            lack.append(f"the render browser's system libraries ({', '.join(missing)}) → "
                        + (f"sudo apt install {' '.join(pkgs)}" if len(pkgs) == len(missing) else "install the packages that give them"))
        elif not checked:
            unsure.append("the render browser's system libraries: no ldd or ldconfig here to ask; the first render names any it misses"
                          " (engines/README.md, Linux：渲染前要先备好的三样)")
    agents = [w for n, w in (("claude-code", "Claude Code"), ("codex", "Codex")) if (m.get(n) or {}).get("state") == "ok"]
    old = [(w, m[n]) for n, w in (("claude-code", "Claude Code"), ("codex", "Codex")) if (m.get(n) or {}).get("state") == "outdated"]
    if not agents:
        lack += ([f"{w} is out of date ({r.get('version') or r.get('note') or 'too old'}) → update it" for w, r in old] if old else
                 ["Claude Code or Codex → claude.com/claude-code, or npm install -g @openai/codex"])
    font = (c.get("fonts") or {}).get("state") == "missing"
    if font and zh_locale(env):
        lack.append("a Chinese font (Chinese text would draw as boxes) → sudo apt install fonts-noto-cjk")
    if lack:
        lines = ["✗ Not ready for a first film yet. It still needs:"] + [f"  {x}" for x in lack]
    elif unsure:
        lines = [f"? Nearly ready for a first film: Node, FFmpeg, Python 3, uv and {' and '.join(agents)} are here; not checked:"] + [f"  {x}" for x in unsure]
    else:
        lines = [f"✓ Ready for a first film: Node, FFmpeg, Python 3, uv, a browser to render with, {' and '.join(agents)}"]
    if not lack and (m.get("chrome-headless-shell") or {}).get("state") != "ok" and own:
        lines.append("  The first render downloads its own Chrome once (about 0.2 GB).")
    if font and not zh_locale(env):
        lines.append("! Chinese text: no Chinese font here, so it would draw as boxes → sudo apt install fonts-noto-cjk")
    if ((c.get("mirror") or {}).get("note") or "").startswith("cn:"):
        lines.append("  Downloads come from the mainland-China mirrors (bin/vh settings mirror off turns that off).")
    if plat == "darwin-arm64":
        if (m.get("qwen3-tts") or {}).get("state") == "ok" and (m.get("mlx-audio") or {}).get("state") == "ok":
            lines.append("✓ Voice: the local voice is downloaded.")
        else:
            lines.append(f"- Voice: the first bin/vh tts downloads the local voice once (about {firstuse.gb(firstuse.total(['qwen']))};"
                         " it says so first and shows the progress). --provider edge needs only a small package (free, online).")
    else:
        lines.append("- Voice: bin/vh tts --provider edge (free, online; only a small package), or a cloud voice with a key;"
                     " the local voice needs Apple Silicon.")
    return lines, "not" if lack else "unchecked" if unsure else "ready"


def this_platform():
    m = platform.machine().lower()
    return f"{sys.platform}-{'arm64' if m in ('arm64', 'aarch64') else m}"


def platform_ok(want):
    return not want or this_platform() == want or this_platform().startswith(want + "-")


def uv_has(pkgs):
    """Whether uv can run these packages from its cache, offline (what bin/vh's uv run would use)."""
    if not shutil.which("uv"):
        return None
    argv = ["uv", "run", "-q", "--no-project", "--offline"] + [x for p in pkgs for x in ("--with", p)] + ["python", "-c", ""]
    rc, _ = run(argv, timeout=120)
    return rc == 0


def hf_snapshot(model):
    """The Hugging Face snapshot folder of a model with weights in it, or None."""
    hub = os.environ.get("HF_HUB_CACHE") or os.path.join(os.environ.get("HF_HOME") or os.path.join(os.environ.get("XDG_CACHE_HOME") or str(home("~/.cache")), "huggingface"), "hub")
    for snap in sorted(glob.glob(os.path.join(hub, "models--" + model.replace("/", "--"), "snapshots", "*", ""))):
        if glob.glob(os.path.join(snap, "*.safetensors")):
            return snap
    return None


def check_module(m, found_by, today):
    """One module on this machine: {state, found, version, keys, note}."""
    ck, ver, needs = m.get("check") or {}, m.get("version") or {}, m.get("needs") or {}
    r = {"state": "ok", "found": None, "version": None, "keys": {}, "key_source": {}, "note": ""}
    notes = []
    if not platform_ok(needs.get("platform")):
        r.update(state="unsupported", note=f"for {needs['platform']} only; this is {this_platform()}" + (f": {m['elsewhere']}" if m.get("elsewhere") else ""))
        return r
    for k in needs.get("keys", []):
        r["keys"][k] = bool(keys.get(k))
        r["key_source"][k] = keys.source(k)   # env or studio (saved in Studio's settings), or None
    if ck.get("per_project"):
        r.update(state="per_project", note=f"each project has its own: {ck['per_project']}")
        return r
    if ck.get("program"):
        # as the tool that runs it looks: its environment variable, PATH, then the places it installs to (check's env, paths)
        at = os.environ.get(ck["env"]) if ck.get("env") else None
        path = at or shutil.which(ck["program"])
        if not path:
            at = path = next((p for p in map(os.path.expanduser, ck.get("paths", [])) if os.access(p, os.X_OK)), None)
        if not path:
            r.update(state="missing", note=f"{ck['program']} not found")
            return r
        r["found"] = path
        if ck.get("version"):
            _, out = run([path] + ck["version"][1:] if at else ck["version"])
            mm = re.search(ck.get("pattern", r"(\d+(?:\.\d+)+)"), out or "")
            r["version"] = mm.group(1) if mm else None
        for other in ck.get("also", []):
            if not shutil.which(other) and not (at and os.path.exists(os.path.join(os.path.dirname(path), other))):
                r["state"] = "incomplete"; notes.append(f"no {other} beside it")
        for f in ck.get("features", []):
            _, out = run(f["argv"])
            if f["contains"] not in (out or ""):
                r["state"] = "incomplete"; notes.append(f["missing"])
    elif ck.get("finder"):
        p = found_by.get(ck["finder"]) or ""
        if not p:
            r.update(state="missing", note="not found")
            return r
        r["found"] = p
        if ck["finder"] == "hf-chrome":
            mm = re.search(r"-(\d+(?:\.\d+)+)$", p.rstrip("/"))
            r["version"] = mm.group(1) if mm else None
            pin = found_by.get("hf-pin")
            if pin and r["version"] and r["version"] != pin:
                r["state"] = "outdated"; notes.append(f"not {pin}, the version the HyperFrames installed here pins")
            elif pin and r["version"] == pin:
                notes.append("the version HyperFrames pins")
            if os.path.isdir(p):
                notes += [size_of(p), shown(os.path.dirname(p.rstrip("/")))]
    elif ck.get("desk_agent"):   # an agent's ACP adapter for the console, installed outside the repo (tools/desk/agents.py)
        sys.path.insert(0, str(ROOT / "tools" / "desk"))
        import agents as A
        got = A.installed(ck["desk_agent"])
        if not got:
            r.update(state="missing", note=f"not installed (bin/vh desk agents install {ck['desk_agent']}; the console's column says so too)")
            return r
        r["found"], r["version"] = got["path"], got["version"]
    elif ck.get("studio_shell"):   # Studio's own window, made by bin/vh studio --install-icon outside the repo (tools/desk/studio.py)
        sys.path.insert(0, str(ROOT / "tools" / "desk"))
        import window as W
        rec = W.shell_record()
        prog, why = W.shell()
        if not rec or not prog:
            r.update(state="missing", note=why or "not installed (optional): bin/vh studio --install-icon makes Studio's own window; without it Studio opens in a browser's window")
            return r
        r["found"], r["version"] = shown(rec.get("app") or prog), rec.get("electron")
    elif ck.get("npm"):
        pj = ROOT / ck["npm"]["in"] / "node_modules" / ck["npm"]["package"] / "package.json"
        try:
            r["version"] = json.loads(pj.read_text(encoding="utf-8")).get("version")
            r["found"] = str(pj.parent)
        except (OSError, ValueError):
            r.update(state="missing", note=f"not installed in {ck['npm']['in']}")
            return r
    if ck.get("hf_model"):
        model = os.environ.get(ck["hf_model"].get("env", ""), "") or ck["hf_model"]["default"]
        snap = hf_snapshot(model)
        if snap:
            r["found"] = r["found"] or snap
            notes.append(f"{model} · {size_of(snap)}")
        else:
            r["state"] = "missing"; notes.append(f"{model} not downloaded yet")
    if ck.get("uv"):
        has = uv_has(ck["uv"])
        if has is None:
            r["state"] = "missing"; notes.append("needs uv")
        elif has:
            notes.append(f"{', '.join(ck['uv'])} in the uv cache")
        else:
            r["state"] = "missing"; notes.append(f"{', '.join(ck['uv'])} not in the uv cache yet")
    for f in ck.get("files", []):
        if not home(f).exists():
            r["state"] = "incomplete" if r["state"] == "ok" else r["state"]; notes.append(f"no {f}")
    # the version against the table's
    v = r["version"]
    if v and ver.get("min") and vtuple(v) < vtuple(ver["min"]):
        r["state"] = "outdated"; notes.append(f"{ver['min']} or newer needed")
    if v and ver.get("pin") and (ck.get("npm") or ck.get("program") or ck.get("desk_agent") or ck.get("studio_shell")) and v != ver["pin"].split()[0]:
        r["state"] = "outdated"; notes.append(f"not {ver['pin'].split()[0]}, the pinned version")
    if v and ver.get("max_age_days"):
        mm = re.fullmatch(r"(\d{4})\.(\d{1,2})\.(\d{1,2})(?:\.\d+)?", v)
        if mm:
            age = (today - datetime.date(*map(int, mm.groups()))).days
            if age > ver["max_age_days"]:
                r["state"] = "outdated"; notes.append(f"{age} days old (over {ver['max_age_days']})")
    if needs.get("keys") and not any(r["keys"].values()) and r["state"] == "ok":
        r["state"] = "no_key"; notes.append("no " + " or ".join(needs["keys"]))
    if r["state"] == "ok" and not (ck or needs.get("keys")):
        r["state"] = "unchecked"
    r["note"] = " · ".join(notes)
    return r


class _Stay(urllib.request.HTTPRedirectHandler):
    """Follows no redirect: the 30x is the answer, so a key sent to one host never goes on to another."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def scrub(text, key):
    """The text with every run of 6 or more of the key's characters taken out: a server may echo a key whole, or a
    masked one with a few characters at each end."""
    s = str(text)
    if not key:
        return s
    if len(key) < 6:
        return s.replace(key, "…")
    for n in range(len(key), 5, -1):
        for i in range(len(key) - n + 1):
            if key[i:i + n] in s:
                s = s.replace(key[i:i + n], "…")
    return s


def error_code(js):
    """A provider's error code from its answer (error.status, error.code, detail.code …), never its message: a message
    can echo the key."""
    for k in ("error", "detail"):
        e = js.get(k) if isinstance(js, dict) else None
        if isinstance(e, dict):
            for f in ("status", "code", "type"):
                v = e.get(f)
                if isinstance(v, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{1,40}", v):
                    return v
    return None


def apply_needs(modules, results):
    """A module whose needed modules (needs.programs) are not usable here is not ok either: "needs node (outdated)" at the
    end of its note, until nothing changes (a need can be a need's)."""
    by = {m["name"]: r for m, r in zip(modules, results)}
    usable = lambda r: r["state"] in ("ok", "per_project", "unchecked")
    changed = True
    while changed:
        changed = False
        for m, r in zip(modules, results):
            if r["state"] == "unsupported":
                continue
            for n in (m.get("needs") or {}).get("programs", []):
                dep = by.get(n)
                if dep is None or usable(dep) or f"needs {n} (" in r["note"]:
                    continue
                r["note"] = " · ".join(x for x in (r["note"], f"needs {n} ({dep['state'].replace('_', ' ')})") if x)
                if r["state"] == "ok":
                    r["state"], changed = "incomplete", True
    return results


def probe(m, offline, recs):
    """Call a service once at its free endpoint, with the first of its keys that is set (a public one that takes no key:
    without one). {state, note}. The key goes in a header that no redirect carries on, only over https (or to this
    machine), and no answer's text is passed on."""
    p = m.get("probe")
    if not p:
        return None
    keyless = not (m.get("needs") or {}).get("keys") and not p.get("auth")
    var = None if keyless else next((k for k in (m.get("needs") or {}).get("keys", []) if keys.get(k)), None)
    if not var and not keyless:
        return {"state": "skipped", "note": "no key set"}
    key, url = (keys.get(var) if var else ""), p["url"]
    if p.get("base_env") and os.environ.get(p["base_env"]):
        b = urllib.parse.urlsplit(os.environ[p["base_env"]])
        if not b.hostname or not (b.scheme == "https" or (b.scheme == "http" and b.hostname in LOCAL)):
            return {"state": "failed", "note": f"{p['base_env']} is not an https address (only this machine may be http): not called, the key would leave in the clear"}
        u = urllib.parse.urlsplit(url)
        url = urllib.parse.urlunsplit((b.scheme, b.netloc.rpartition("@")[2], u.path, u.query, ""))
    host = urllib.parse.urlsplit(url).netloc
    body = json.dumps(p["body"]).encode() if "body" in p else None
    try:
        if offline:
            rec = next((x for x in recs if x.get("url") == url), None)
            if rec is None:
                return {"state": "failed", "note": f"no recorded response for {url} in {offline}"}
            status, hdrs = rec.get("status", 200), {str(k).lower(): v for k, v in (rec.get("headers") or {}).items()}
            data = (Path(offline) / rec["body"]).read_bytes() if rec.get("body") else b""
        else:
            req = urllib.request.Request(url, data=body, method=p.get("method", "GET"), headers={"User-Agent": UA})
            if body is not None:
                req.add_header("Content-Type", "application/json")
            if var:
                req.add_unredirected_header(p["auth"]["header"], p["auth"].get("prefix", "") + key)
            try:
                with urllib.request.build_opener(_Stay).open(req, timeout=20) as resp:
                    status, hdrs, data = resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read(4 << 20)
            except urllib.error.HTTPError as e:
                status, hdrs, data = e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, e.read(64 << 10)
    except (OSError, ValueError, http.client.HTTPException) as e:
        return {"state": "failed", "note": scrub(f"{host}: {getattr(e, 'reason', e)}", key)}
    if 300 <= status < 400:
        to = urllib.parse.urlsplit(urllib.parse.urljoin(url, hdrs.get("location", ""))).netloc or "nowhere it says"
        return {"state": "failed", "note": scrub(f"HTTP {status}: {host} sends it on to {to}, not followed (the key went nowhere else)", key)}
    try:
        js = json.loads(data.decode("utf-8")) if data else {}
    except (UnicodeDecodeError, ValueError):
        js = None
    if status >= 400:
        code = error_code(js)
        return {"state": "failed", "note": scrub(f"HTTP {status}" + (f" with {var}" if var else "") + (f" ({code})" if code else ""), key)}
    exp, said = p.get("expect") or {}, [f"{var} taken" if var else f"answers (HTTP {status}, no key)"]
    if exp.get("text"):   # an answer that is not JSON (an RSS feed): the text it must hold
        if exp["text"] not in data.decode("utf-8", errors="replace"):
            return {"state": "failed", "note": f"HTTP {status}, but not the answer the adapter reads (no {exp['text']!r} in it)"}
        return {"state": "ok", "note": ", ".join(said)}
    if not isinstance(js, dict):
        return {"state": "failed", "note": f"HTTP {status}, but not the JSON it answers with"}
    if exp.get("path"):
        v = js
        for part in exp["path"].split("."):
            v = v.get(part) if isinstance(v, dict) else None
        if v in (None, "", [], {}):
            return {"state": "failed", "note": f"HTTP {status}, but no {exp['path']} in the answer (the adapter reads it)"}
    if exp.get("status_code"):
        code = js
        for part in exp["status_code"].split("."):
            code = code.get(part) if isinstance(code, dict) else None
        if code != 0:
            hint = (exp.get("hints") or {}).get(str(code))
            return {"state": "failed", "note": scrub(f"{var or host} refused: status_code {code}" + (f" ({hint})" if hint else ""), key)}
    if exp.get("list"):
        items = js.get(exp["list"])
        if not isinstance(items, list):
            return {"state": "failed", "note": f"HTTP {status}, but no {exp['list']} list in the answer"}
        said.append(f"{len(items)} {exp['list']}")
        if exp.get("names"):
            have = {str(x.get("name", "")).split("/")[-1] for x in items if isinstance(x, dict)}
            gone = [n for n in exp["names"] if n not in have]
            if gone:
                return {"state": "failed", "note": (f"{var} taken" if var else f"{host} answers") + f", but the models bin/vh uses are not listed: {', '.join(gone)}"}
            said.append(f"the {len(exp['names'])} models bin/vh uses among them")
    return {"state": "ok", "note": ", ".join(said)}


def snap_stub(path):
    """Ubuntu's chromium-browser with no chromium snap behind it: a script that only says to install the snap, which cannot run
    where there is no snapd (Docker, many servers). HyperFrames installs it on Linux arm64 (engines/README.md, Linux)."""
    try:
        with open(path, "rb") as f:
            head = f.read(4096)
    except OSError:
        return False
    return head.startswith(b"#!") and b"snap" in head and not os.path.exists("/snap/bin/chromium")


SKILL_HOMES = (("~/.claude/skills", "claude"), ("~/.agents/skills", "codex"))   # where bin/vh install-skill writes, and its word for each
HARNESS_LINE = "Harness path (set by install.sh):"   # the one line install-skill rewrites: the clone a copy points at


def skill_stub(text, name, harness):
    """What bin/vh install-skill writes for a skill: its frontmatter, then tools/skill_stub.md with the name and this clone
    put in, line ends as LF whatever the checkout has (a CRLF one too). bin/vh renders the same with tr, awk and bash; the
    two are held together by tools/ci.sh."""
    lines = text.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)
    front = []
    if lines and lines[0].rstrip("\n") == "---":
        for line in lines:
            front.append(line)
            if len(front) > 1 and line.rstrip("\n") == "---":
                break
    stub = (ROOT / "tools" / "skill_stub.md").read_text(encoding="utf-8").replace("\r", "").rstrip("\n")
    return "".join(front) + stub.replace("@NAME@", name).replace("@HARNESS@", harness) + "\n"


def is_clone(at):
    """Whether a Harness path line names a folder with a clone in it (bin/vh there)."""
    try:
        return bool(at) and (home(at) / "bin" / "vh").is_file()
    except OSError:
        return False


def skills_check():
    """The skills bin/vh install-skill wrote. They are stubs that send the agent to skills/<name>/SKILL.md in the clone, so a
    git pull updates what a host reads; only the stub itself can fall behind: its frontmatter (a host triggers on the
    description) or tools/skill_stub.md. A copy of the whole file, as install-skill wrote before 2026-11-15 or another
    installer writes, stays as it was while skills/ moves on (seen 2026-11: a copy six weeks old still said "8 video
    types" and "three review gates"). Outdated: one of this clone's that is not the stub as it would be written now, a
    skill the folder has not got yet, one whose Harness path names a folder with no clone in it (moved or removed:
    install-skill from here points it at this clone), and one this clone wrote for a skill skills/ no longer has (renamed
    or removed: it still triggers on its old description; install-skill removes those). A copy that points at another
    clone that is there is that clone's, and is left alone."""
    repo = {q.parent.name: q.read_text(encoding="utf-8") for q in sorted((ROOT / "skills").glob("*/SKILL.md"))}
    body = lambda text: [line for line in text.splitlines() if not line.startswith(HARNESS_LINE)]
    same, old, others = 0, {}, []
    for folder, target in SKILL_HOMES:
        ours, absent = False, []
        try:
            there = sorted(q.parent.name for q in home(folder).glob("*/SKILL.md"))
        except OSError:
            there = []
        for name in sorted(set(repo) | set(there)):
            f = home(folder) / name / "SKILL.md"
            try:
                got = f.read_text(encoding="utf-8")
            except (OSError, ValueError):
                if name in repo:
                    absent.append(name)
                continue
            at = next((line[len(HARNESS_LINE):].strip() for line in got.splitlines() if line.startswith(HARNESS_LINE)), "")
            try:
                here = bool(at) and home(at).resolve() == ROOT
            except OSError:
                here = False
            if name not in repo:   # a skill of its own, or one this clone used to have
                if here:
                    old.setdefault(target, []).append(f"{shown(f)} is this clone's, for a skill skills/ no longer has (renamed or removed;"
                                                      " it still triggers on its old description)")
                continue
            if not here and at and not is_clone(at):
                ours = True
                old.setdefault(target, []).append(f"{shown(f)} points at {at}, where there is no clone now (moved or removed?)")
                continue
            if not here:
                others.append(at or "no clone")
                continue
            ours = True
            if body(got) == body(skill_stub(repo[name], name, str(ROOT))):
                same += 1
            elif body(got) == body(repo[name]):   # a whole copy, current today; it falls behind at the next pull
                old.setdefault(target, []).append(f"{shown(f)} is a whole copy of skills/{name}/SKILL.md (it stays as it is when skills/ changes)")
            else:
                old.setdefault(target, []).append(f"{shown(f)} is not the stub install-skill writes now")
        if ours and absent:   # a skill added since this folder was installed
            old.setdefault(target, []).append(f"{folder} has no {', '.join(absent)}")
    left = (f"; left alone: {len(others)} cop{'y' if len(others) == 1 else 'ies'} pointing at {', '.join(sorted(set(others)))}") if others else ""
    if old:
        how = "bin/vh install-skill" + (f" {next(iter(old))}" if len(old) == 1 else "")
        return {"name": "skills", "state": "outdated", "note": "; ".join(x for v in old.values() for x in v)
                + f" → {how} (it writes stubs that read skills/ in this clone, so a git pull keeps them current, and removes"
                  f" the ones it wrote for skills this clone no longer has; an agent reads its skill when a session starts){left}"}
    if same:
        return {"name": "skills", "state": "ok", "note": f"{same} installed stub{'' if same == 1 else 's'} reading skills/ in this clone (a git pull updates them){left}"}
    return {"name": "skills", "state": "unchecked", "note": "none installed for this clone (optional): bin/vh install-skill lets an agent in any folder find this harness" + left}


def can_write(folder):
    """Whether a file can be made in folder, or, while it is not there yet, in the nearest folder above it that is (where it
    would be made). Tried with a file made and removed, which is what a download does; the permission bits are not asked."""
    q = Path(folder)
    while not q.is_dir():
        if q.parent == q:
            return False
        q = q.parent
    try:
        fd, name = tempfile.mkstemp(prefix=".vh-doctor-", dir=str(q))
    except OSError:
        return False
    os.close(fd)
    with contextlib.suppress(OSError):
        os.unlink(name)
    return True


def cache_homes(has_chrome=False):
    """The folders outside the project that a first run writes into: [(whose, folder, what writes there, what moves it)].
    has_chrome: the chrome-headless-shell HyperFrames renders with is already there, so only its fonts are still to come."""
    env = os.environ.get
    uv = env("UV_CACHE_DIR")
    if not uv and shutil.which("uv"):
        rc, said = run(["uv", "cache", "dir"])
        uv = said.strip().splitlines()[-1] if rc == 0 and said.strip() else ""
        uv = uv if os.path.isabs(uv) else ""   # a uv that answers something else (a stand-in, an old one): its default below
    xdg = env("XDG_CACHE_HOME") or str(home("~/.cache"))
    return [
        ("uv", uv or str(home("~/.cache/uv")), "the Python packages of beats, music, qa, tts and the other uv tools", "UV_CACHE_DIR=<folder>"),
        ("npm", env("npm_config_cache") or env("NPM_CONFIG_CACHE") or str(home("~/.npm")), "bin/vh new's npm install and every npx hyperframes", "NPM_CONFIG_CACHE=<folder>"),
        ("Hugging Face", env("HF_HOME") or str(home("~/.cache/huggingface")), "the local voice's model, 1.8 GB", "HF_HOME=<folder>"),
        ("HyperFrames", env("HYPERFRAMES_FONT_CACHE_DIR") or str(home("~/.cache/hyperframes/fonts")), "the fonts a film asks for; its Chrome is already there",
         "HYPERFRAMES_FONT_CACHE_DIR=<folder>") if has_chrome else
        ("HyperFrames", str(home("~/.cache/hyperframes")), "its Chrome on a first snapshot or render, about 200 MB, and its fonts",
         "no setting moves it: let the sandbox write it, or fetch the Chrome once outside the sandbox (" + ("bin/vh settings chrome" if os.environ.get("OVH_MIRROR") == "cn" else "npx hyperframes browser ensure") + ") "
         "and give the fonts HYPERFRAMES_FONT_CACHE_DIR=<folder>"),
        ("bin/vh", os.path.join(xdg, "ovh"), "the font index of fonts and textcheck, HyperFrames' registry list", "XDG_CACHE_HOME=<folder>"),
    ]


def caches_check(has_chrome=False):
    """Whether those folders can be written. In a host that lets an agent write only its workspace (a sandbox), a warm cache
    passes every other line of this report, and the first render on a new machine then fails on a download it cannot store."""
    shut = [(who, folder, what, how) for who, folder, what, how in cache_homes(has_chrome) if not can_write(folder)]
    if not shut:
        return {"name": "caches", "state": "ok", "note": "uv, npm, Hugging Face, HyperFrames and bin/vh can write theirs (the folders outside a project that a first run downloads into)"}
    return {"name": "caches", "state": "incomplete", "note": "cannot be written here (a sandbox that keeps writes to the workspace?): "
            + "; ".join(f"{who}: {shown(folder)} ({what}) → {how}" for who, folder, what, how in shut)
            + ". Point <folder> inside what this session may write, in the same command or the host's environment; what is already in a cache is still read"}


def repo_checks(webgl, found_by):
    """A browser for the page tools, WebGL, the reference repos, LOCAL.md, AGENTS.md, the installed skills and the caches:
    [{name, state, note}]."""
    out = []
    if found_by.get("chrome") and not found_by.get("hf-chrome") and snap_stub(found_by["chrome"]):
        out.append({"name": "browser", "state": "missing", "note": f"{found_by['chrome']} is Ubuntu's stub for the Chromium snap, which does not run "
                    "without snapd: apt purge chromium-browser, then a chrome-headless-shell (engines/README.md, Linux：渲染前要先备好的三样)"})
    elif found_by.get("hf-chrome") or found_by.get("chrome"):
        out.append({"name": "browser", "state": "ok", "note": "the page tools draw with " + ("chrome-headless-shell" if found_by.get("hf-chrome") else "Chrome")})
    else:
        out.append({"name": "browser", "state": "missing", "note": "neither Chrome nor chrome-headless-shell: frames, render, textcheck and the other page tools need one (set CHROME_PATH, or see chrome above)"})
    if sys.platform.startswith("linux"):   # macOS has PingFang; a bare Linux has no Chinese font, and Chinese text then draws as boxes
        try:
            fams = [f for f in subprocess.run(["fc-list", ":lang=zh", "family"], capture_output=True, text=True, timeout=20).stdout.splitlines() if f.strip()]
            out.append({"name": "fonts", "state": "ok", "note": f"Chinese: {len(fams)} font famil{'y' if len(fams) == 1 else 'ies'}, such as {fams[0].split(',')[0]}"} if fams else
                       {"name": "fonts", "state": "missing", "note": "no Chinese font: Chinese text in a film draws as boxes → sudo apt install fonts-noto-cjk (bin/vh fonts check <project> says it per character)"})
        except (OSError, subprocess.SubprocessError):
            out.append({"name": "fonts", "state": "unchecked", "note": "no fc-list (fontconfig) to ask: bin/vh fonts check <project> says whether each character has a font"})
    kind, _, renderer = (webgl or "skipped|").partition("|")
    if kind in ("GPU", "software"):
        out.append({"name": "webgl", "state": "ok", "note": f"{kind}: {renderer}"})
    elif kind == "soft-gl":
        out.append({"name": "webgl", "state": "incomplete", "note": f"no WebGL with the GPU flags, only with --soft-gl ({renderer}): render with node render.mjs --soft-gl"})
    elif kind == "none":
        out.append({"name": "webgl", "state": "missing", "note": "no WebGL with the GPU flags nor with --soft-gl: WebGL scenes will not render on this machine"})
    else:
        out.append({"name": "webgl", "state": "unchecked", "note": "the probe needs Chrome and the ClaudeAnimationBase deps (bin/vh setup)"})
    try:
        want = len(re.findall(r"^(?:full|sparse|textonly)\s", (ROOT / "references" / "fetch.sh").read_text(encoding="utf-8"), re.M))
    except OSError:
        want = 0
    have = sum(1 for d in glob.glob(str(ROOT / "references" / "repos" / "*" / "")) if os.path.isdir(os.path.join(d, ".git")))
    if have >= want:
        out.append({"name": "references", "state": "ok", "note": f"{have}/{want} repos fetched, {size_of(ROOT / 'references' / 'repos')}"})
    else:
        out.append({"name": "references", "state": "ok", "note": references_note(have, want, bytes_of(ROOT / "references" / "repos") if have else 0, install_says())})
    try:   # the download mirrors this machine's settings say (tools/settings.py, tools/mirrors.txt)
        import settings as S
        d = S.load(); m = S.mirror(d); why = f" ({d['mirror_why']})" if d.get("mirror_why") else ""
        out.append({"name": "mirror", "state": "ok", "note": {
            "cn": f"cn: downloads come from the mainland-China mirrors ({S.operators()}; tools/mirrors.txt){why} → bin/vh settings mirror off turns that off",
            "off": f"off: the official sources, and install.sh does not try the mirrors{why} → bin/vh settings mirror auto or cn changes it",
            "auto": "auto: the official sources (install.sh tries the mainland-China mirrors when the official npm registry does not answer) → bin/vh settings mirror cn uses them now"}[m]})
    except (OSError, ValueError, ImportError) as e:
        out.append({"name": "mirror", "state": "unchecked", "note": f"tools/mirrors.txt or this machine's settings not readable: {e}"})
    local = ROOT / "LOCAL.md"
    if not local.exists():
        out.append({"name": "local_md", "state": "missing", "note": "no LOCAL.md → bin/vh doctor --fill-local (copies LOCAL.example.md, writes this machine's lines)"})
    else:
        lines = local.read_text(encoding="utf-8").splitlines()
        left = {m.group(2) for m in map(TEMPLATE_LINE.match, lines) if m}
        todo = [k for k in MACHINE if k in left]
        rest = sum(1 for line in lines if re.search(r"\{[^}]*\}", line)) - len(todo)
        out.append({"name": "local_md", "state": "incomplete" if todo else "ok",
                    "note": (f"{', '.join(todo)} still the template → bin/vh doctor --fill-local writes them" if todo else "this machine's lines filled in")
                    + (f"; {rest} other line(s) still {{…}}, which leaves them at their defaults" if rest > 0 else "")})
    try:
        same = (ROOT / "AGENTS.md").read_text(encoding="utf-8").split("\n", 3)[3].rstrip("\n") == (ROOT / "CLAUDE.md").read_text(encoding="utf-8").rstrip("\n")
    except (OSError, IndexError):
        same = False
    out.append({"name": "agents_md", "state": "ok" if same else "incomplete", "note": "in sync with CLAUDE.md" if same else "out of sync with CLAUDE.md → bin/vh sync-agents"})
    out.append(skills_check())
    out.append(studio_icon_check())
    out.append(caches_check(bool(found_by.get("hf-chrome"))))
    return out


def studio_icon_check():
    """The launcher icon bin/vh studio --install-icon makes (an OVH Studio.app, a desktop entry on Linux): installed or not
    (optional), and whether it runs this clone. It runs bin/vh studio in its clone, so a git pull changes what it does; it
    falls behind only when its launcher or picture changed (made again by --install-icon), or its clone moved."""
    try:
        sys.path.insert(0, str(ROOT / "tools" / "desk"))
        import studio
        st = studio.status()
    except Exception as e:
        return {"name": "studio-icon", "state": "unchecked", "note": f"could not look ({type(e).__name__}: {e})"}
    state = {"ok": "ok", "outdated": "outdated", "elsewhere": "outdated", "unsupported": "unsupported"}.get(st["state"], "unchecked")
    where = f"{shown(st['path'])}: " if st.get("path") else ""
    return {"name": "studio-icon", "state": state, "note": where + st["note"]}


MACHINE = ("硬件", "已装工具", "已装引擎")   # LOCAL.md's lines doctor can write; a {…} left on any other line is its default
TEMPLATE_LINE = re.compile(r"^(- (%s)：)\s*(\{.*?)(\r?\n)?$" % "|".join(MACHINE))   # a machine line whose value is still the template's {…}


def hardware():
    """This machine's chip, GPU and memory, as far as the system says."""
    chip = mem = gpu = ""
    if sys.platform == "darwin":   # an Apple chip names its GPU too
        rc, out = run(["sysctl", "-n", "machdep.cpu.brand_string"])
        chip = out.strip() if rc == 0 else ""
        rc, out = run(["sysctl", "-n", "hw.memsize"])
        mem = out.strip() if rc == 0 else ""
    else:
        try:
            mm = re.search(r"^(?:model name|Hardware|Model)\s*:\s*(.+)$", Path("/proc/cpuinfo").read_text(errors="replace"), re.M)
            chip = mm.group(1).strip() if mm else ""
            mm = re.search(r"^MemTotal:\s*(\d+)\s*kB", Path("/proc/meminfo").read_text(errors="replace"), re.M)
            mem = str(int(mm.group(1)) * 1024) if mm else ""
        except OSError:
            pass
        if shutil.which("nvidia-smi"):
            rc, out = run(["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"])
            gpu = " + ".join(x.strip() for x in out.splitlines() if x.strip()) if rc == 0 else ""
    return " · ".join([chip or platform.machine()] + ([f"GPU {gpu}"] if gpu else []) + ([f"{round(int(mem) / 2 ** 30)} GB 内存"] if mem.isdigit() else []))


def machine_lines(mods):
    """LOCAL.md's machine lines from this check: {label: text}."""
    by = {m["name"]: m for m in mods}

    def found(n):   # found on this machine, whatever its version
        m = by.get(n) or {}
        return m if m.get("state") in ("ok", "outdated", "incomplete") else None

    tools = [f"{label} {m['version'] or shown(m['found'] or '')}".strip() for n, label in (
        ("node", "Node"), ("ffmpeg", "ffmpeg"), ("python3", "Python"), ("uv", "uv"), ("git", "git"), ("chrome", "Chrome"),
        ("latex", "LaTeX"), ("blender", "Blender")) for m in [found(n)] if m]
    hf = found("hyperframes")
    engines = ["ClaudeAnimationBase" + (" ✓" if found("puppeteer-core") else "（依赖没装：bin/vh setup）"),
               "HyperFrames" + (f" {hf['version']}（styles/_swatch；每个项目各装一份）" if hf and hf.get("version") else "（每个项目各装一份，bin/vh new 时装）")]
    engines += [f"{label} {m['version'] or '✓'}" for n, label in (("blender", "Blender"), ("manimgx", "ManimGX")) for m in [found(n)] if m]
    return {"硬件": hardware(), "已装工具": " · ".join(tools), "已装引擎": " · ".join(engines)}


def fill_local(mods):
    """LOCAL.md's machine lines (MACHINE) from this check, where they still hold the template's {…}; LOCAL.example.md is
    copied first when there is no LOCAL.md. Any other line, and a machine line a person wrote, stays as it is.
    → the line to print."""
    local, example = ROOT / "LOCAL.md", ROOT / "LOCAL.example.md"
    new = not local.exists()
    try:   # newline="": a file's own line endings (CRLF) stay as they are
        with open(example if new else local, encoding="utf-8", newline="") as fh:
            text = fh.read()
    except OSError as e:
        return f"LOCAL.md: not written ({e})"
    facts, done, kept, out = machine_lines(mods), [], [], []
    stamp = f"（bin/vh doctor --fill-local，{datetime.date.today().isoformat()}）"
    for line in text.splitlines(keepends=True):
        mm, label = TEMPLATE_LINE.match(line), re.match(r"^- (%s)：" % "|".join(MACHINE), line)
        if mm and facts.get(mm.group(2)):
            line = mm.group(1) + facts[mm.group(2)] + stamp + (mm.group(4) or "")
            done.append(mm.group(2))
        elif label:   # a person's own words, braces and all ("M3 Max {16 core}")
            kept.append(label.group(1))
        out.append(line)
    if new or done:
        dest = local.resolve() if local.is_symlink() else local   # a linked LOCAL.md: write the file it points to
        tmp = dest.with_name(f".{dest.name}.{os.getpid()}")
        try:
            with open(tmp, "w", encoding="utf-8", newline="") as fh:
                fh.write("".join(out))
            os.replace(tmp, dest)
        except OSError as e:
            with contextlib.suppress(OSError):
                tmp.unlink()
            return f"LOCAL.md: not written ({e})"
    said = ("LOCAL.md made from LOCAL.example.md" if new else "LOCAL.md") + ": "
    said += f"wrote {', '.join(done)} from this check" if done else "nothing to write"
    if kept:
        said += f"; {', '.join(kept)} already filled in, left as is"
    return said + "; 渲染速度 is yours to write after a first render, and the lines still {…} are the defaults"


def problems(t, commands=None):
    """What breaks the table's rules, a line each."""
    bad, names = [], []
    if t.get("version") != 1:
        bad.append('"version" is not 1')
    known = None
    table_names = {m.get("name") for m in t.get("modules") or []}
    if commands is not None:
        known = {c.get("name") for c in commands.get("commands", [])}
    for m in t.get("modules") or []:
        n = m.get("name")
        at = f"module {n!r}"
        if not isinstance(n, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", n):
            bad.append(f"{at}: the name is not lower-case letters, digits and -"); continue
        names.append(n)
        extra = set(m) - {"name", "kind", "status", "purpose", "version", "license", "needs", "adapter", "commands", "required", "check",
                          "probe", "first_run", "install", "elsewhere", "cost", "key_url"}
        if extra:
            bad.append(f"{at}: fields doctor does not know: {sorted(extra)}")
        if m.get("kind") not in KINDS:
            bad.append(f"{at}: kind {m.get('kind')!r} is not one of {', '.join(KINDS)}")
        if m.get("status") not in (None, "planned"):
            bad.append(f"{at}: status is only ever \"planned\"")
        for k in ("purpose", "license"):
            if not isinstance(m.get(k), str) or not m[k].strip():
                bad.append(f"{at}: no {k}")
        if not isinstance(m.get("required"), bool):
            bad.append(f"{at}: required is not true or false")
        ver = m.get("version")
        if not isinstance(ver, dict) or set(ver) - {"pin", "min", "range", "tested", "models", "max_age_days"}:
            bad.append(f"{at}: version is not an object of pin, min, range, tested, models, max_age_days")
        if "cost" in m and m["cost"] not in ("free", "free_tier", "paid"):
            bad.append(f"{at}: cost is not free, free_tier or paid")
        if "key_url" in m and not (isinstance(m["key_url"], str) and m["key_url"].startswith("https://") and (m.get("needs") or {}).get("keys")):
            bad.append(f"{at}: key_url is not an https address, or the module needs no key")
        needs = m.get("needs")
        if not isinstance(needs, dict) or set(needs) - {"keys", "programs", "account", "platform"}:
            bad.append(f"{at}: needs is not an object of keys, programs, account, platform")
        else:
            for k in needs.get("keys", []):
                if not re.fullmatch(r"[A-Z][A-Z0-9_]*", k):
                    bad.append(f"{at}: {k!r} is not the name of an environment variable")
            for n in needs.get("programs", []):
                if n not in table_names or n == m.get("name"):
                    bad.append(f"{at}: needs.programs names {n!r}, which is not another module of this table")
            if m.get("elsewhere") and not needs.get("platform"):
                bad.append(f"{at}: elsewhere is what to use where needs.platform does not hold, and it has none")
        adapter = m.get("adapter")
        if not isinstance(adapter, list) or (not adapter and m.get("status") != "planned"):
            bad.append(f"{at}: no adapter (where the repo talks to it)")
        for a in adapter or []:
            path = a.split(" (")[0].split(" ")[0]
            if not glob.glob(str(ROOT / path)):
                bad.append(f"{at}: adapter {path!r} is not in the repo")
        cmds = m.get("commands")
        if not isinstance(cmds, list):
            bad.append(f"{at}: commands is not a list")
        elif known is not None and set(cmds) - known:
            bad.append(f"{at}: commands bin/vh does not have: {sorted(set(cmds) - known)}")
        if m.get("status") == "planned" and cmds:
            bad.append(f"{at}: planned, yet commands use it")
        ck = m.get("check")
        if not isinstance(ck, dict) or set(ck) - {"program", "env", "paths", "version", "pattern", "also", "features", "finder", "npm", "uv", "hf_model", "files", "per_project", "desk_agent", "studio_shell"}:
            bad.append(f"{at}: check has a key doctor does not know")
        elif ck.get("desk_agent") is not None and ck["desk_agent"] not in ("claude", "codex", "dsh"):
            bad.append(f"{at}: desk_agent {ck['desk_agent']!r} is not one of the console's agents (claude, codex, dsh)")
        elif ck.get("finder") not in (None, "chrome", "hf-chrome"):
            bad.append(f"{at}: finder {ck['finder']!r} is not one bin/vh passes (chrome, hf-chrome)")
        p = m.get("probe")
        if p is not None:
            if m.get("kind") != "service":
                bad.append(f"{at}: a probe is for a service")
            elif bool((needs or {}).get("keys")) != bool(p.get("auth")):
                bad.append(f"{at}: a probe sends a key (auth) exactly when the service needs one (needs.keys)")
            if not str(p.get("url", "")).startswith("https://") or re.search(r"[?&][^=]*(key|token|secret)", p.get("url", ""), re.I):
                bad.append(f"{at}: a probe's url is https and carries no key")
            if p.get("method", "GET") not in ("GET", "POST") or ("auth" in p and (not isinstance(p["auth"], dict) or not p["auth"].get("header"))):
                bad.append(f"{at}: a probe needs GET or POST, and its auth an auth.header (the key goes in a header)")
            if set(p.get("expect") or {}) - {"list", "names", "status_code", "hints", "path", "text"}:
                bad.append(f"{at}: a probe's expect has a key doctor does not know")
    if len(set(names)) != len(names):
        bad.append(f"names repeat: {sorted(n for n in set(names) if names.count(n) > 1)}")
    return bad


def print_module(m, r):
    """A module's line (and its probe's): ✓ usable, ✗ a required one that is not, ! an optional one that is not, - n/a."""
    bad = r["state"] in ("missing", "outdated", "incomplete")
    mark = OK if r["state"] == "ok" else NO if bad and m["required"] else WA if bad else "-"
    ck = m.get("check") or {}
    where = shown(r["found"]) if r["found"] and not r["version"] and (ck.get("program") or ck.get("finder") == "chrome") else ""
    src = r.get("key_source") or {}
    have = [f"{k} set {'in Studio' if src.get(k) == 'studio' else 'in the environment'}" for k, on in r["keys"].items() if on]
    detail = " · ".join(x for x in (", ".join(have), r["version"], where, r["note"]) if x)
    if r["state"] == "no_key" and m["commands"]:
        detail += f" (for bin/vh {', '.join(m['commands'])})"
    hint = f" → {r['install']}" if bad and r["install"] else ""
    print(f"{mark} {m['name']}  {detail}{hint}")
    if r["probe"] and r["probe"]["state"] != "skipped":   # skipped: no key, said on the line above
        print(f"   {OK if r['probe']['state'] == 'ok' else NO} live: {r['probe']['note']}")


def main(argv):
    a = {"json": False, "probe": False, "fill-local": False, "first": False, "offline": None, "only": None, "chrome": "", "hf-chrome": "", "hf-pin": "", "webgl": ""}
    i = 0
    while i < len(argv):
        x = argv[i]
        if x in ("-h", "--help"):
            print(__doc__.strip()); return 0
        if x == "--check":
            t = json.loads(TABLE.read_text(encoding="utf-8"))
            bad = problems(t, json.loads(COMMANDS.read_text(encoding="utf-8")) if COMMANDS.exists() else None)
            for b in bad:
                print(f"tools/modules.json: {b}", file=sys.stderr)
            if not bad:
                print(f"tools/modules.json: {len(t['modules'])} modules")
            return 1 if bad else 0
        k, eq, v = x[2:].partition("=")
        if x in ("--json", "--probe", "--fill-local", "--first"):
            a[x[2:]] = True
        elif k in ("offline", "only", "chrome", "hf-chrome", "hf-pin", "webgl") and x.startswith("--"):
            if not eq:
                if i + 1 >= len(argv):
                    print(f"bin/vh doctor: --{k} needs a value", file=sys.stderr); return 2
                i += 1; v = argv[i]
            a[k] = v
        else:
            print(f"bin/vh doctor: unknown option {x} (usage: bin/vh doctor [--json] [--first] [--fill-local] [--probe [--only a,b] [--offline DIR]], or bin/vh doctor <project>)", file=sys.stderr)
            return 2
        i += 1
    if (a["offline"] or a["only"] is not None) and not a["probe"]:
        print(f"bin/vh doctor: --{'offline answers' if a['offline'] else 'only picks'} the probes: give --probe too", file=sys.stderr); return 2
    try:
        t = json.loads(TABLE.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"bin/vh doctor: cannot read {shown(TABLE)}: {e}", file=sys.stderr); return 2
    only = None if a["only"] is None else {n.strip() for n in a["only"].split(",") if n.strip()}
    if only is not None and (not only or only - {m.get("name") for m in t["modules"]}):
        print(f"bin/vh doctor: --only names no module of the table: {', '.join(sorted(only - {m.get('name') for m in t['modules']})) or '(none given)'}", file=sys.stderr)
        return 2
    recs = []
    if a["offline"]:
        try:
            recs = json.loads((Path(a["offline"]) / "responses.json").read_text(encoding="utf-8"))["responses"]
        except (OSError, ValueError, KeyError, TypeError) as e:
            print(f"bin/vh doctor: no recorded responses in {a['offline']} ({e})", file=sys.stderr); return 2
    today = datetime.date.today()
    found_by = {"chrome": a["chrome"], "hf-chrome": a["hf-chrome"], "hf-pin": a["hf-pin"]}
    mods = apply_needs(t["modules"], [check_module(m, found_by, today) for m in t["modules"]])
    for i, (m, r) in enumerate(zip(t["modules"], mods)):
        pr = probe(m, a["offline"], recs) if a["probe"] and (only is None or m["name"] in only) else None
        mods[i] = {"name": m["name"], "kind": m["kind"], "status": m.get("status", "used"), "required": m["required"], **r,
                   "install": (m.get("install") or {}).get("macos" if sys.platform == "darwin" else "linux"), "probe": pr}
    if a["fill-local"]:   # before the checks, so the LOCAL.md line says what is there now (--first: written, not said)
        said = fill_local(mods)
        if not a["first"]:
            print(said, file=sys.stderr if a["json"] else sys.stdout)
    checks = repo_checks(a["webgl"], found_by)
    if a["first"] and not a["json"]:
        lines, state = first_film(mods, checks, this_platform(), found_by)
        print("\n".join(lines))
        return {"ready": 0, "not": 1, "unchecked": 3}[state]
    first = [m.get("first_run") for m, r in zip(t["modules"], mods) if m.get("first_run") and r["state"] == "missing"]
    counts = {}
    for x in mods + checks:
        counts[x["state"]] = counts.get(x["state"], 0) + 1
    if a["json"]:
        print(json.dumps({"version": 1, "tool": "bin/vh doctor", "t": round(time.time(), 3), "platform": this_platform(),
                          "modules": mods, "checks": checks, "first_run": first, "counts": counts}, ensure_ascii=False, indent=1))
        return 0
    sections = [("programs", lambda m: m["kind"] == "program"), ("packages and models", lambda m: m["kind"] in ("npm", "python", "model")),
                ("services (whether a key is set, never its value)", lambda m: m["kind"] == "service"), ("agents", lambda m: m["kind"] == "agent")]
    used = [(m, r) for m, r in zip(t["modules"], mods) if r["status"] != "planned"]
    for title, has in sections:
        print(title)
        for m, r in used:
            if has(m):
                print_module(m, r)
    print("machine and repo")
    for c in checks:
        mark = OK if c["state"] == "ok" else "-" if c["state"] == "unchecked" else NO if c["name"] == "browser" else WA
        print(f"{mark} {c['name'].replace('_', '.').replace('local.md', 'LOCAL.md').replace('agents.md', 'AGENTS.md')}  {c['note']}")
    planned = [(m, r) for m, r in zip(t["modules"], mods) if r["status"] == "planned"]
    if planned:
        print("planned (nothing in bin/vh calls these yet)")
        for m, r in planned:
            print_module(m, r)
    print("- every bin/vh new short|promo|data|meme installs its own pinned HyperFrames into the project (about 140 MB of node_modules)")
    if first:
        mirrored = os.environ.get("OVH_MIRROR") == "cn"
        print(f"   still to come on first use: {', '.join(first)} (wiki: Getting Started; "
              + ("from the mainland-China mirrors, as this machine's settings say: bin/vh settings)" if mirrored else
                 "mirrors behind a slow or blocked network: bin/vh settings mirror cn, wiki China-Network / 国内网络)"))
    if not a["probe"]:
        print("   bin/vh doctor --probe: also call each service with a key once, at an endpoint that costs nothing")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import jsonerr
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except KeyboardInterrupt:
        sys.exit(130)
