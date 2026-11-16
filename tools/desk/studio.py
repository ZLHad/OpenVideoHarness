"""bin/vh studio: show Studio, the console (bin/vh desk), in a window of its own: from a terminal, from an agent ("打开
Studio"), or from the launcher icon this also installs. One window a console: not open yet, it opens; open, it comes
to the front, never a second; a film outside Studio's folders joins Studio's space and opens in that same window.

  bin/vh studio [<project>] [--print-address] [--json]
      Studio running: its window comes to the front (or is made, when it was closed), on that film when one is named; no
      second console, no second window, no conversation in its agent column interrupted. Not running: it starts in the
      background first (it stops by itself 12 h after its last page closes). The window is a Chromium-family browser
      named outright (Chrome, Chromium, Edge or Brave) with Studio's own profile and no address bar (tools/desk/window.py);
      it counts as open only when its page connects back, and otherwise this tries once more, then a tab of the default
      browser, and says what happened. A film outside Studio's folders joins Studio's space (the last fifty such films
      are kept beside the console's own file) and opens in the same window, not in a desk of its own.
      The same when an agent runs it: the person asked for the window. Nothing secret is printed.
      --print-address: for a browser on another machine (no screen here): show nothing; write an address that opens one
      page, once, within ten minutes, to your terminal and nowhere else (not stdout, not --json, not a log). Refused with
      no terminal (an agent's shell has none), and while Studio runs: it comes with a fresh start, and this never closes a
      window that is open (bin/vh desk link --print-address starts it again, on purpose).
  bin/vh studio --install-icon [--dir DIR]    the launcher icon: on macOS "OVH Studio.app" in ~/Applications, on Linux a
      desktop entry in ~/.local/share/applications ($XDG_DATA_HOME). With DIR, all of it goes there and nothing outside it
      is touched (not the system's list of apps either: a test copy, or a folder you add yourself). It runs bin/vh studio in this
      clone, so a git pull needs no reinstall; a clone that moved says which command to run again. Made here, with what
      every macOS has (osacompile, codesign) and stdlib Python (the picture: tools/desk/icon.py)
  bin/vh studio --remove-icon [--dir DIR]     take it away again (only one this wrote); OVH Studio quits first when it
      runs; a default removal also takes Electron's download and the app's own profile when they are its own, and says
      what it left
  bin/vh studio --icon-status [--dir DIR] [--json]   installed or not, and whether it runs this clone (bin/vh doctor says it too)
  bin/vh studio --icon open | alive | quit [--force]   what the icon runs: open (above; the console it starts is the
      icon's own), alive (exit 0 while a Studio runs, 1 when none), quit (stop the console the icon started, and with it
      its window; exit 3 while an agent in its column is mid-turn, unless --force)

Exit: 0 done · 1 the window did not open, nothing came up, the icon could not be made, or --print-address refused (no
terminal, Studio running) · 2 usage · 3 quit refused (an agent mid-turn).
"""
import argparse, hashlib, json, os, plistlib, re, shlex, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import jsonerr   # noqa: E402

APP = "OVH Studio"                       # the name in the Dock and Finder: short, and no other app's
BUNDLE_ID = "io.github.zlhad.ovh-studio"
DESKTOP = "ovh-studio.desktop"
LAUNCHER = 2                             # the launcher's own version: what the app, the applet or the script does around bin/vh studio
SHELL = HERE / "shell"                   # Studio's own window (Electron): its source, run from the clone; its lockfile pins Electron
MARK = "ovh-studio.json"                 # in the app's Resources (Linux: beside its script): which clone, which launcher, which picture


def _say(msg):
    print(msg, file=sys.stderr, flush=True)


# ---------- opening it ----------

def _console():
    import server
    return server.running_info(None, [])


def _place(url, project):
    """Where the page opens: the film's place (/p/<key>) in Studio's space, joining it first when it is outside Studio's
    folders (server.join: Studio's one window, not a desk of its own); Studio's home without a film. → (place, joined)."""
    import launch, server
    if not project:
        return "", False
    at = launch.place(url, project)
    if at:
        return at, False
    joined = server.join(project)
    return (launch.place(url, project) or "") if joined else "", joined


def open_studio(project=None, print_address=False, owner=None):
    """→ (record, exit code). The record: url (an address that opens nothing by itself), opened, how (front, open, app,
    window, tab), started, pid, joined (a film outside Studio's folders, now in its space). print_address: a fresh start
    only, its address with a one-time code written to the terminal (printed: "terminal"), never into the record."""
    import launch, server
    info = server.running_info(None, [])
    rec = {"version": 1, "tool": "bin/vh studio", "where": "studio", "project": str(project) if project else None}
    if print_address:
        if not server.has_terminal():
            return dict(rec, error=server.NO_TERMINAL, refused=True), 1
        if info:
            return dict(rec, refused=True, error="Studio is running already, and an address for another computer comes only with a fresh "
                        "start; this never closes a window that is open. To start it again on purpose (its window closes): bin/vh desk link "
                        "--print-address"), 1
        url, why = launch.start(None, [], False, None, launch.IDLE, True, owner)
        if not url:
            return dict(rec, error=why), 1
        info = server.running_info(None, []) or {}
        at, joined = _place(url.partition("?")[0], project)
        printed = server.to_terminal(server.address_words(url + (f"#{at}" if at else "")))
        return dict(rec, url=url.partition("?")[0] + (f"#{at}" if at else ""), opened=False, started=True, pid=info.get("pid"), joined=joined,
                    printed="terminal" if printed else None), 0 if printed else 1
    started = False
    if not info:
        url, why = launch.start(None, [], False, None, launch.IDLE, False, owner)
        if not url:
            return dict(rec, error=why), 1
        info, started = server.running_info(None, []) or {"url": url}, why != "running"   # another start made it meanwhile
    url = info["url"]
    at, joined = _place(url, project)
    shown = launch.show(url, at)
    rec.update(url=url + (f"#{at}" if at else ""), opened=bool(shown.get("opened")), how=shown.get("how"), why=shown.get("why"), started=started,
               pid=info.get("pid"), owner=info.get("owner"), joined=joined)
    return rec, 0 if rec["opened"] else 1


def icon_quit(force=False):
    """Stop the console the icon started. → (record, exit code): 0 stopped or none of the icon's runs, 3 an agent mid-turn."""
    import launch
    info = _console()
    if not info or info.get("owner") != "icon":
        return {"version": 1, "stopped": False, "why": "no Studio of the icon's runs (one started elsewhere is left as it is)"}, 0
    if not force and launch.busy(info):
        return {"version": 1, "stopped": False, "busy": True,
                "why": "Studio 里的 agent 正在做事，退出会让它停下。 / An agent in Studio is in the middle of a turn: quitting stops it."}, 3
    return {"version": 1, "stopped": launch.stop(info), "pid": info.get("pid")}, 0


# ---------- the icon ----------

def _icon_hash():
    return hashlib.sha256((HERE / "icon.py").read_bytes()).hexdigest()[:12]


def _mark():
    return {"version": 1, "repo": str(ROOT), "launcher": LAUNCHER, "icon": _icon_hash()}


def _env_line():
    """The PATH and locale bin/vh runs with from the icon: this shell's PATH (an app started by the Dock gets the bare
    system one, without Homebrew's python3, node or ffmpeg)."""
    return f"export PATH={shlex.quote(os.environ.get('PATH') or '/usr/bin:/bin')} LANG={shlex.quote(os.environ.get('LANG') or 'en_US.UTF-8')};"


def _platform(forced=None):
    p = forced or ("macos" if sys.platform == "darwin" else "linux" if sys.platform.startswith("linux") else None)
    return p


def _data_home():
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def where(platform, dir_=None):
    """Where the icon goes (or is): the .app, or the desktop entry, and on Linux the folder of its script and picture.
    With --dir, all of it is inside that folder (Linux: <dir>/ovh-studio beside the entry): nothing else is touched."""
    if platform == "macos":
        return Path(dir_).expanduser() / f"{APP}.app" if dir_ else Path.home() / "Applications" / f"{APP}.app", None
    if dir_:
        return Path(dir_).expanduser() / DESKTOP, Path(dir_).expanduser() / "ovh-studio"
    return _data_home() / "applications" / DESKTOP, _data_home() / "ovh-studio"


def _ours(platform, path, data=None):
    """The mark the icon carries, when this command wrote it (else None)."""
    try:
        if platform == "macos":
            return json.loads((path / "Contents" / "Resources" / MARK).read_text())
        text = path.read_text(encoding="utf-8")
        m = re.search(r"^X-OVH-Repo=(.*)$", text, re.M)
        if not m:
            return None
        mark = {"repo": m.group(1)}
        mp = (data or _data_home() / "ovh-studio") / MARK
        if mp.is_file():
            mark.update({k: v for k, v in json.loads(mp.read_text()).items() if k != "repo"})
        return mark
    except (OSError, ValueError):
        return None


def _as_string(s):
    """A Python str as the inside of an AppleScript string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _desktop_arg(s):
    """A path as one argument of a desktop entry's Exec, by the spec: quoted, with " ` $ and \\ escaped inside the quotes,
    then every backslash doubled (the value is a desktop-entry string too) and % written %% (a field code otherwise)."""
    inner = re.sub(r'(["`$\\\\])', r"\\\1", s)
    return ('"' + inner + '"').replace("\\", "\\\\").replace("%", "%%")


def build_app(dest, register=True):
    """OVH Studio.app at dest: a stay-open AppleScript applet (it answers a second click and the Dock's Quit), its icon,
    its name, the clone it runs. Ad-hoc signed, as osacompile signs it; made on this machine, so no quarantine and no
    Gatekeeper check. → None, or why it could not be made."""
    import icon
    for tool in ("osacompile", "codesign"):
        if not shutil.which(tool):
            return f"{tool} is not on this Mac (it comes with macOS: /usr/bin/{tool})"
    src = (HERE / "launcher" / "studio.applescript").read_text(encoding="utf-8")
    src = src.replace("@@REPO@@", _as_string(str(ROOT))).replace("@@ENV@@", _as_string(_env_line()))
    with tempfile.TemporaryDirectory(prefix="ovh-studio-") as t:
        script = Path(t) / "studio.applescript"
        script.write_text(src, encoding="utf-8")
        app = Path(t) / f"{APP}.app"
        r = subprocess.run(["osacompile", "-s", "-o", str(app), str(script)], capture_output=True, text=True, timeout=120)
        if r.returncode or not app.is_dir():
            return f"osacompile: {(r.stderr or r.stdout).strip()[-300:]}"
        res = app / "Contents" / "Resources"
        (res / "applet.icns").write_bytes(icon.icns())
        for extra in ("Assets.car",):   # an asset catalog's icon would win over applet.icns
            (res / extra).unlink(missing_ok=True)
        plist_p = app / "Contents" / "Info.plist"
        with open(plist_p, "rb") as f:
            pl = plistlib.load(f)
        pl.pop("CFBundleIconName", None)
        # the applet template asks for every privacy permission there is; this one needs none of them
        for k in [k for k in pl if re.fullmatch(r"NS\w+UsageDescription", k)]:
            del pl[k]
        pl.update({"CFBundleName": APP, "CFBundleDisplayName": APP, "CFBundleIdentifier": BUNDLE_ID, "CFBundleIconFile": "applet",
                   "CFBundleShortVersionString": str(LAUNCHER), "CFBundleVersion": str(LAUNCHER), "LSApplicationCategoryType": "public.app-category.video",
                   "NSHumanReadableCopyright": "OpenVideoHarness: shows Studio's window"})
        with open(plist_p, "wb") as f:
            plistlib.dump(pl, f)
        (res / MARK).write_text(json.dumps(_mark()))
        r = subprocess.run(["codesign", "--force", "--sign", "-", str(app)], capture_output=True, text=True, timeout=120)
        if r.returncode:
            return f"codesign: {(r.stderr or r.stdout).strip()[-300:]}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(app), str(dest))
    os.utime(dest)   # Finder and the Dock read the icon again
    if register:   # not for --dir: the system's list of apps is outside that folder
        _lsregister("-f", dest)
    return None


LSREGISTER = "/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister"


def _lsregister(flag, app):
    if os.access(LSREGISTER, os.X_OK):
        subprocess.run([LSREGISTER, flag, str(app)], capture_output=True, timeout=60)


def build_desktop(entry, data, register=True):
    """The desktop entry, its script and its picture (256 px). → None, or why not."""
    import icon
    data.mkdir(parents=True, exist_ok=True)
    launch_sh = data / "studio-launch.sh"
    sh = (HERE / "launcher" / "studio-launch.sh").read_text(encoding="utf-8")
    launch_sh.write_text(sh.replace("@@REPO@@", shlex.quote(str(ROOT))).replace("@@ENV@@", _env_line().rstrip(";")), encoding="utf-8")
    launch_sh.chmod(0o755)
    pic = data / "ovh-studio.png"
    pic.write_bytes(icon.png(256, 256, icon.render(256)))
    (data / MARK).write_text(json.dumps(_mark()))
    d = (HERE / "launcher" / DESKTOP).read_text(encoding="utf-8")
    d = d.replace("@@EXEC@@", _desktop_arg(str(launch_sh))).replace("@@ICON@@", str(pic)).replace("@@REPO@@", str(ROOT))
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text(d, encoding="utf-8")
    entry.chmod(0o755)
    upd = shutil.which("update-desktop-database")
    if upd and register:
        subprocess.run([upd, str(entry.parent)], capture_output=True, timeout=60)
    return None


def shell_version():
    return json.loads((SHELL / "package.json").read_text())["dependencies"]["electron"]


def _shell_cache(dir_=None):
    """Where Electron's download is kept: $OVH_STUDIO_SHELL_CACHE, else ~/.cache/ovh/studio-shell; with --dir, inside that
    folder (a --dir install touches nothing outside it; set $OVH_STUDIO_SHELL_CACHE to share one download)."""
    if os.environ.get("OVH_STUDIO_SHELL_CACHE"):
        return Path(os.environ["OVH_STUDIO_SHELL_CACHE"])
    if dir_:
        return Path(dir_).expanduser() / "ovh-studio" / "cache"
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "ovh" / "studio-shell"


CACHE_MARK = "ovh-studio-cache.json"   # in the download cache: what removal takes away is ours


def _app_profile():
    """The app's own profile (Electron's userData for "OVH Studio"): its window size and theme, the page's storage."""
    if os.environ.get("OVH_STUDIO_SHELL_PROFILE"):
        return Path(os.environ["OVH_STUDIO_SHELL_PROFILE"])
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / APP


def _quit_app(dir_=None):
    """The app this install made, if it runs: told to quit (a line it takes, as the console's are), and if it is still
    there after five seconds, its own process (window.shell_pid) ends. So removing it leaves no window on a dead page."""
    import window as WIN
    try:
        exe = json.loads(_record_path(dir_).read_text()).get("exe")
    except (OSError, ValueError):
        return
    if not exe or not WIN.shell_pid(exe):
        return
    WIN.shell_send(exe, {"quit": True})
    for _ in range(50):
        if not WIN.shell_pid(exe):
            return
        time.sleep(0.1)
    pid = WIN.shell_pid(exe)
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass


def _record_path(dir_=None):
    """How the console finds the app (window.shell_record): the default install's only. A --dir install keeps its record
    in that folder, so the console never picks up a test's or a copy's app."""
    return (Path(dir_).expanduser() if dir_ else _data_home()) / "ovh-studio" / "shell.json"


def fetch_electron(out=sys.stderr, dir_=None):
    """The pinned Electron, unpacked → (its dist folder, None) or (None, why). npm ci from the committed lockfile (every
    package with its integrity hash, no install scripts), then Electron's own download step, which checks the archive
    against the checksums in that package; the archive stays in the cache, so making the app again works offline.
    $OVH_STUDIO_ELECTRON_DIST: a dist folder to use instead; $OVH_STUDIO_NO_DOWNLOAD: never download (the checks)."""
    given = os.environ.get("OVH_STUDIO_ELECTRON_DIST")
    if given:
        return (Path(given), None) if Path(given).is_dir() else (None, f"{given} is no folder")
    npm, node = shutil.which("npm"), shutil.which("node")
    if not (npm and node):
        return None, "no npm here (it comes with Node.js)"
    if os.environ.get("OVH_STUDIO_NO_DOWNLOAD"):   # tools/ci.sh: no check downloads Electron
        return None, "no download here (OVH_STUDIO_NO_DOWNLOAD)"
    ver = shell_version()
    cache = _shell_cache(dir_)
    work = cache / ver
    work.mkdir(parents=True, exist_ok=True)
    (cache / CACHE_MARK).write_text(json.dumps({"what": "Electron for OVH Studio (bin/vh studio --install-icon)"}) + "\n")
    for f in ("package.json", "package-lock.json"):
        shutil.copyfile(SHELL / f, work / f)
    dist = work / "node_modules" / "electron" / "dist"
    if not (dist / "version").is_file() or (dist / "version").read_text().strip().lstrip("v") != ver:
        print(f"studio: getting Electron {ver} (about 130 MB the first time; kept in {_shown(cache)}) …", file=out, flush=True)
        env = dict(os.environ, npm_config_update_notifier="false", electron_config_cache=str(cache / "downloads"))
        r = subprocess.run([npm, "ci", "--ignore-scripts", "--no-audit", "--no-fund", "--loglevel=error", "--cache", str(cache / "npm")], cwd=str(work), env=env,
                           capture_output=True, text=True, timeout=900)
        if r.returncode:
            return None, f"npm ci did not finish: {_reason(r)}"
        r = subprocess.run([node, str(work / "node_modules" / "electron" / "install.js")], cwd=str(work), env=env,
                           capture_output=True, text=True, timeout=1800)
        if r.returncode or not (dist / "version").is_file():
            return None, f"Electron's download did not finish: {_reason(r)}"
    return dist, None


def _reason(r):
    """The line of a failed command's output that says what went wrong (an error's own line, not its stack), short."""
    lines = [ln.strip() for ln in (r.stderr or r.stdout or "").splitlines() if ln.strip()]
    hit = next((ln for ln in lines if ("Error" in ln or "ERR" in ln) and not ln.startswith("at ")), None) or (lines[-1] if lines else "")
    net = re.search(r"fetch failed|ECONN|ENOTFOUND|ETIMEDOUT|EAI_AGAIN|network", hit, re.I)
    return ((hit[:160] + ("…" if len(hit) > 160 else "")) + (" (no network?)" if net else "")) or "no network?"


def _tidy(dist):
    """After the app is made, only Electron's download stays in the cache (about 130 MB): enough to make it again offline."""
    if os.environ.get("OVH_STUDIO_ELECTRON_DIST"):
        return
    nm = dist.parent.parent   # <cache>/<version>/node_modules
    if nm.name == "node_modules" and nm.is_dir():
        shutil.rmtree(nm, ignore_errors=True)


def _shown(p):
    h = str(Path.home())
    return "~" + str(p)[len(h):] if str(p).startswith(h + os.sep) else str(p)


def _boot(repo):
    """The app's own code (Resources/app/boot.js, from tools/desk/launcher/shell-boot.js): it runs the shell from the
    clone, with the PATH the installer saw."""
    env = {"PATH": os.environ.get("PATH") or "/usr/bin:/bin", "LANG": os.environ.get("LANG") or "en_US.UTF-8"}
    src = (HERE / "launcher" / "shell-boot.js").read_text(encoding="utf-8")
    return src.replace('"@@REPO@@"', json.dumps(str(repo))).replace("{} /*@@ENV@@*/", json.dumps(env))


def _app_files(res):
    """Resources/app (macOS) or resources/app (Linux): the boot and its package.json."""
    app = res / "app"
    app.mkdir(parents=True, exist_ok=True)
    (app / "package.json").write_text(json.dumps({"name": "ovh-studio", "productName": APP, "version": "1.0.0", "main": "boot.js", "private": True}) + "\n")
    (app / "boot.js").write_text(_boot(ROOT), encoding="utf-8")
    (res / "default_app.asar").unlink(missing_ok=True)


def _boot_ours(p):
    try:
        return "bin/vh studio --install-icon wrote this" in p.read_text(encoding="utf-8")[:400]
    except OSError:
        return False


def _write_record(exe, app, dir_=None):
    rp = _record_path(dir_)
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps({"exe": str(exe), "app": str(app), "electron": shell_version(), "repo": str(ROOT)}) + "\n")


def build_shell_app(dest, out=sys.stderr, dir_=None):
    """OVH Studio.app at dest, Studio's own window: Electron with its own name, bundle id and icon, its code the boot that
    runs the shell from this clone; signed ad hoc (made here, no quarantine: Gatekeeper does not stop it). → None, or why."""
    import icon
    dist, why = fetch_electron(out, dir_)
    if not dist:
        return why
    src = dist / "Electron.app"
    if not (src / "Contents" / "Info.plist").is_file():
        return f"no Electron.app in {dist}"
    with tempfile.TemporaryDirectory(prefix="ovh-studio-") as t:
        app = Path(t) / f"{APP}.app"
        r = subprocess.run(["ditto", str(src), str(app)], capture_output=True, text=True, timeout=600)
        if r.returncode:
            return f"ditto: {r.stderr.strip()[-200:]}"
        res = app / "Contents" / "Resources"
        (res / "ovh-studio.icns").write_bytes(icon.icns())
        _app_files(res)
        plist_p = app / "Contents" / "Info.plist"
        with open(plist_p, "rb") as f:
            pl = plistlib.load(f)
        pl.pop("ElectronAsarIntegrity", None)
        pl.update({"CFBundleName": APP, "CFBundleDisplayName": APP, "CFBundleIdentifier": BUNDLE_ID, "CFBundleIconFile": "ovh-studio.icns",
                   "CFBundleShortVersionString": str(LAUNCHER), "CFBundleVersion": str(LAUNCHER), "LSApplicationCategoryType": "public.app-category.video",
                   "NSHumanReadableCopyright": "OpenVideoHarness: Studio's own window", "LSMultipleInstancesProhibited": True})
        with open(plist_p, "wb") as f:
            plistlib.dump(pl, f)
        (res / MARK).write_text(json.dumps(dict(_mark(), kind="shell", electron=shell_version())))
        r = subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], capture_output=True, text=True, timeout=600)
        if r.returncode:
            return f"codesign: {(r.stderr or r.stdout).strip()[-300:]}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.move(str(app), str(dest))
    os.utime(dest)
    if not dir_:   # not for --dir: the system's list of apps is outside that folder
        _lsregister("-f", dest)
    _write_record(dest / "Contents" / "MacOS" / "Electron", dest, dir_)
    _tidy(dist)
    return None


def build_shell_linux(entry, data, out=sys.stderr, dir_=None):
    """Studio's own window on Linux: Electron copied to <data>/shell with the boot, a desktop entry that runs it. → None, or why."""
    import icon
    dist, why = fetch_electron(out, dir_)
    if not dist:
        return why
    if not (dist / "electron").is_file():
        return f"no electron program in {dist}"
    target = data / "shell"
    if target.exists():
        if not _boot_ours(target / "resources" / "app" / "boot.js"):
            return f"{target} is there and is not one bin/vh studio made: left as it is"
        shutil.rmtree(target)
    shutil.copytree(dist, target, symlinks=True)
    _app_files(target / "resources")
    pic = data / "ovh-studio.png"
    pic.write_bytes(icon.png(256, 256, icon.render(256)))
    (data / MARK).write_text(json.dumps(dict(_mark(), kind="shell", electron=shell_version())))
    d = (HERE / "launcher" / DESKTOP).read_text(encoding="utf-8")
    d = d.replace("@@EXEC@@", _desktop_arg(str(target / "electron"))).replace("@@ICON@@", str(pic)).replace("@@REPO@@", str(ROOT))
    d = d.replace("Terminal=false", "Terminal=false\nStartupWMClass=OVH Studio")
    entry.parent.mkdir(parents=True, exist_ok=True)
    entry.write_text(d, encoding="utf-8")
    entry.chmod(0o755)
    _write_record(target / "electron", target, dir_)
    _tidy(dist)
    return None


def install(platform, dir_=None, use_shell=True, out=sys.stderr):
    """→ (path, kind, note) or (None, None, why). kind: shell (Studio's own window) or launcher (the applet or the script,
    which open a browser's window). use_shell False, or no way to get Electron here: the launcher, and the note says why."""
    path, data = where(platform, dir_)
    if path.exists() and _ours(platform, path, data) is None:
        return None, None, f"{path} is there and is not one bin/vh studio wrote: left as it is (--dir puts the icon somewhere else)"
    note = None
    if use_shell:
        why = build_shell_app(path, out, dir_) if platform == "macos" else build_shell_linux(path, data, out, dir_)
        if not why:
            return path, "shell", None
        note = f"Studio's own window was not made ({why}): this launcher opens it in a browser's window instead"
    _record_path(dir_).unlink(missing_ok=True)
    why = build_app(path, register=not dir_) if platform == "macos" else build_desktop(path, data, register=not dir_)
    return (None, None, why) if why else (path, "launcher", note)


def remove(platform, dir_=None, left=None):
    """Take the icon away (only one this wrote): the app quits first when it runs. A default removal also takes Electron's
    download and the app's own profile, when they are ours; what stays is named in left."""
    path, data = where(platform, dir_)
    if not path.exists():
        return None, None
    if _ours(platform, path, data) is None:
        return None, f"{path} is not one bin/vh studio wrote: left as it is"
    _quit_app(dir_)
    if platform == "macos":
        if not dir_:
            _lsregister("-u", path)
        shutil.rmtree(path)
    else:
        path.unlink()
        if data and data.is_dir():
            shutil.rmtree(data)
    _record_path(dir_).unlink(missing_ok=True)
    left = left if left is not None else []
    cache = Path(dir_).expanduser() / "ovh-studio" / "cache" if dir_ else _shell_cache()   # never a cache another install shares
    if cache.is_dir():   # Electron's download (and npm's cache beside it): only a folder this made
        if (cache / CACHE_MARK).is_file():
            shutil.rmtree(cache, ignore_errors=True)
        else:
            left.append(f"Electron's download in {_shown(cache)} (not one this made)")
    if dir_ and platform == "macos":   # the folder that held the app's record beside it
        try:
            (Path(dir_).expanduser() / "ovh-studio").rmdir()
        except OSError:
            pass
    if not dir_:   # the app's own profile (a --dir copy shares the installed one's: left alone)
        prof = _app_profile()
        if (prof / "ovh-studio.json").is_file():
            shutil.rmtree(prof, ignore_errors=True)
        elif prof.is_dir():
            left.append(f"the app's profile in {_shown(prof)} (it holds nothing of Studio's own)")
    return path, None


def status(platform=None, dir_=None):
    """{state, path, note} for bin/vh doctor and --icon-status: ok (runs this clone, current), outdated (another
    launcher or picture: install again), elsewhere (runs another clone, or one that moved), not installed."""
    platform = _platform(platform)
    if platform is None:
        return {"state": "unsupported", "note": "the launcher icon is for macOS and Linux"}
    places = [where(platform, dir_)] if dir_ else [where(platform)] + ([(Path("/Applications") / f"{APP}.app", None)] if platform == "macos" else [])
    for p, data in places:
        if not p.exists():
            continue
        mark = _ours(platform, p, data)
        if mark is None:
            continue
        repo = mark.get("repo") or ""
        if os.path.realpath(repo) != os.path.realpath(str(ROOT)):
            there = Path(repo, "bin", "vh").is_file()
            return {"state": "elsewhere", "path": str(p), "repo": repo,
                    "note": ("runs another clone" if there else "runs a clone that is no longer there")
                    + ": bin/vh studio --install-icon here makes it run this one"}
        kind = "Studio's own window (Electron " + mark["electron"] + ")" if mark.get("kind") == "shell" else "a launcher that opens a browser's window"
        if mark.get("launcher", LAUNCHER) != LAUNCHER or mark.get("icon", _icon_hash()) != _icon_hash() \
                or (mark.get("kind") == "shell" and mark.get("electron") != shell_version()):
            return {"state": "outdated", "path": str(p), "kind": mark.get("kind") or "launcher",
                    "note": f"{kind}, made by an earlier bin/vh studio: --install-icon makes it again"}
        return {"state": "ok", "path": str(p), "kind": mark.get("kind") or "launcher", "note": f"{kind}; runs this clone (a git pull needs no reinstall)"}
    return {"state": "missing", "note": "not installed (optional): bin/vh studio --install-icon puts OVH Studio, Studio's own window, in "
            + ("~/Applications" if platform == "macos" else "your applications menu")}


# ---------- the command ----------

def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh studio", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("project", nargs="?", help="a project folder, or its name under projects/: open on that film")
    ap.add_argument("--print-address", action="store_true", help="show nothing; write an address that opens one page, once, within ten minutes, "
                                                                 "to your terminal alone (for a browser on another machine; whoever opens it first "
                                                                 "can work in Studio). Refused with no terminal, and while Studio runs")
    ap.add_argument("--force", action="store_true", help="with --icon quit: also while an agent in the column is mid-turn")
    ap.add_argument("--json", action="store_true", help="the record on stdout")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--install-icon", action="store_true", help="put OVH Studio in your applications: Studio's own window (Electron, about 130 MB "
                                                               "downloaded once, 260 MB on disk), or with --no-shell a small launcher that opens a browser's window")
    g.add_argument("--remove-icon", action="store_true", help="take the launcher icon away (a running OVH Studio quits first)")
    g.add_argument("--icon-status", action="store_true", help="is the launcher icon installed, and does it run this clone")
    g.add_argument("--icon", choices=["open", "alive", "quit"], help="what the launcher icon runs")
    ap.add_argument("--no-shell", action="store_true", help="with --install-icon: the small launcher, not Studio's own window (no download)")
    ap.add_argument("--dir", help="with --install-icon, --remove-icon, --icon-status: this folder instead of your applications folder")
    ap.add_argument("--as", dest="as_", choices=["macos", "linux"], help=argparse.SUPPRESS)   # the other platform's icon (a check, on one machine)
    a = ap.parse_args(argv)
    if a.json:
        jsonerr.force()
    if a.no_shell and not a.install_icon:
        return jsonerr.fail("usage", "studio: --no-shell goes with --install-icon")
    if a.dir and not (a.install_icon or a.remove_icon or a.icon_status):
        return jsonerr.fail("usage", "studio: --dir goes with --install-icon, --remove-icon or --icon-status")
    if (a.install_icon or a.remove_icon or a.icon_status or a.icon) and (a.project or a.print_address):
        return jsonerr.fail("usage", "studio: the icon's options take no project and no --print-address")

    if a.install_icon or a.remove_icon or a.icon_status:
        platform = _platform(a.as_)
        if platform is None:
            return jsonerr.fail("refused", "studio: the launcher icon is for macOS and Linux (bin/vh studio opens Studio anywhere)")
        if a.icon_status:
            st = status(platform, a.dir)
            print(json.dumps(dict(st, version=1)) if a.json else f"icon: {st['state']}" + (f" · {st['path']}" if st.get("path") else "") + f" · {st['note']}")
            return 0
        if a.install_icon:
            path, kind, why = install(platform, a.dir, not a.no_shell)
            if not path:
                return jsonerr.fail("failed", f"studio: the icon was not made: {why}", rc=1)
            if a.json:
                print(json.dumps({"version": 1, "installed": str(path), "kind": kind, "note": why}))
            else:
                what = ("Studio's own window: click it in Finder or Launchpad, or keep it in the Dock. Clicked again, the same window comes "
                        "to the front; quitting it stops the Studio it started." if kind == "shell" else
                        "a launcher: click it and Studio opens in a browser's window; clicked again, that window comes to the front.")
                print(f"✓ {APP}: {path}\n  {what} It runs this clone: a git pull needs no reinstall." + (f"\n  ({why})" if why else ""))
            return 0
        left = []
        path, why = remove(platform, a.dir, left)
        if why:
            return jsonerr.fail("refused", f"studio: {why}", rc=1)
        print(json.dumps({"version": 1, "removed": str(path) if path else None, "left": left}) if a.json else
              (f"✓ removed {path}" + "".join(f"\n  left: {x}" for x in left) if path else "studio: no icon to remove there"))
        return 0

    if a.icon == "alive":
        return 0 if _console() else 1
    if a.icon == "quit":
        rec, rc = icon_quit(a.force)
        if a.json:
            print(json.dumps(rec, ensure_ascii=False))
        elif rc == 3:
            _say(rec["why"])
        return rc

    project = None
    if a.project:
        from vhdraw import project_dir
        try:
            project = Path(project_dir(a.project)).resolve()
        except SystemExit as e:
            return jsonerr.fail("no_project", f"studio: {e}")
    rec, rc = open_studio(project, a.print_address, "icon" if a.icon == "open" else None)
    if a.json:
        print(json.dumps(rec, ensure_ascii=False))
        return rc
    if rec.get("refused"):
        _say(f"studio: {rec['error']}")
        return rc
    if rec.get("url") is None:
        _say(f"Studio did not start: {rec.get('error')}")
        return rc
    import server
    if a.print_address:
        print("Studio started in the background: the address for another computer is in your terminal." if rec.get("printed")
              else "Studio started in the background, but its address could not be written to your terminal", flush=True)
    elif rec.get("opened"):
        print(server.said(rec) + (f" ({project.name} is outside Studio's folders: it joined Studio's space)" if rec.get("joined") else "")
              + ("\n  It started in the background; it stops by itself 12 h after its window closes." if rec.get("started") else ""), flush=True)
    else:
        _say(server.said(rec, icon=a.icon == "open"))
    return rc


if __name__ == "__main__":
    import activity   # tools/activity.py: bin/vh exec's into this, so this process writes the run's end
    sys.exit(activity.exiting(lambda: jsonerr.guard(lambda: main(sys.argv[1:]))))
