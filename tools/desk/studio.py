"""bin/vh studio: show Studio, the console (bin/vh desk), in a window of its own: from a terminal, from an agent ("打开
Studio"), or from the launcher icon this also installs. One window a console: not open yet, it opens; open, it comes
to the front, never a second. (A film outside Studio's folders has a desk of its own, and so a window of its own.)

  bin/vh studio [<project>] [--print-address] [--json]
      Studio running: its window comes to the front (or is made, when it was closed), on that film when one is named; no
      second console, no second window, no conversation in its agent column interrupted. Not running: it starts in the
      background first (it stops by itself 12 h after its last page closes). The window is a Chromium-family browser
      named outright (Chrome, Chromium, Edge or Brave) with Studio's own profile and no address bar (tools/desk/window.py);
      it counts as open only when its page connects back, and otherwise this tries once more, then a tab of the default
      browser, and says what happened. A film outside Studio's folders opens in its own desk (bin/vh desk <project>).
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
  bin/vh studio --remove-icon [--dir DIR]     take it away again (only one this wrote)
  bin/vh studio --icon-status [--dir DIR] [--json]   installed or not, and whether it runs this clone (bin/vh doctor says it too)
  bin/vh studio --icon open | alive | quit [--force]   what the icon runs: open (above; the console it starts is the
      icon's own), alive (exit 0 while a Studio runs, 1 when none), quit (stop the console the icon started, and with it
      its window; exit 3 while an agent in its column is mid-turn, unless --force)

Exit: 0 done · 1 the window did not open, nothing came up, the icon could not be made, or --print-address refused (no
terminal, Studio running) · 2 usage · 3 quit refused (an agent mid-turn).
"""
import argparse, hashlib, json, os, plistlib, re, shlex, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import jsonerr   # noqa: E402

APP = "OVH Studio"                       # the name in the Dock and Finder: short, and no other app's
BUNDLE_ID = "io.github.zlhad.ovh-studio"
DESKTOP = "ovh-studio.desktop"
LAUNCHER = 1                             # the launcher's own version: what the applet or the script does around bin/vh studio
MARK = "ovh-studio.json"                 # in the app's Resources (Linux: beside its script): which clone, which launcher, which picture


def _say(msg):
    print(msg, file=sys.stderr, flush=True)


# ---------- opening it ----------

def _console():
    import server
    return server.running_info(None, [])


def _in_console_roots(project):
    import projects as PJ
    real = os.path.realpath(str(project))
    try:
        return any(os.path.realpath(r["path"]) == real for r in PJ.listing([])["projects"])
    except (Exception, SystemExit):
        return False


def _place(url, project, own):
    """Where the page opens: the project's place (/p/<key>) in its own desk, or in Studio's listing; Studio's home."""
    import launch, server
    from urllib.parse import quote
    if not project:
        return ""
    if own:
        return "/p/" + quote(server.keyify(project.name, project), safe="")
    return launch.place(url, project) or ""


def open_studio(project=None, print_address=False, owner=None):
    """→ (record, exit code). The record: url (an address that opens nothing by itself), opened, how (front, open,
    window, tab), started, pid, where (studio | desk). print_address: a fresh start only, its address with a one-time code
    written to the terminal (printed: "terminal"), never into the record."""
    import launch, server
    console = _console()
    own = project is not None and not (launch.place(console["url"], project) if console else _in_console_roots(project))
    target = project if own else None   # a film outside Studio's folders: its own desk (every other film a click away there too)
    info = server.running_info(target, [])
    rec = {"version": 1, "tool": "bin/vh studio", "where": "desk" if own else "studio", "project": str(project) if project else None}
    if print_address:
        if not server.has_terminal():
            return dict(rec, error=server.NO_TERMINAL, refused=True), 1
        if info:
            return dict(rec, refused=True, error="Studio is running already, and an address for another computer comes only with a fresh "
                        "start; this never closes a window that is open. To start it again on purpose (its window closes): bin/vh desk link "
                        + (f"{project} " if own else "") + "--print-address"), 1
        url, why = launch.start(target, [], False, None, launch.IDLE, True, owner)
        if not url:
            return dict(rec, error=why), 1
        info = server.running_info(target, []) or {}
        at = _place(url, project, own)
        printed = server.to_terminal(server.address_words(url + (f"#{at}" if at else "")))
        return dict(rec, url=url.partition("?")[0] + (f"#{at}" if at else ""), opened=False, started=True, pid=info.get("pid"),
                    printed="terminal" if printed else None), 0 if printed else 1
    started = False
    if not info:
        url, why = launch.start(target, [], False, None, launch.IDLE, False, owner)
        if not url:
            return dict(rec, error=why), 1
        info, started = server.running_info(target, []) or {"url": url}, True
    url = info["url"]
    at = _place(url, project, own)
    shown = launch.show(url, at)
    rec.update(url=url + (f"#{at}" if at else ""), opened=bool(shown.get("opened")), how=shown.get("how"), why=shown.get("why"), started=started,
               pid=info.get("pid"), owner=info.get("owner"))
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


def install(platform, dir_=None):
    path, data = where(platform, dir_)
    if path.exists() and _ours(platform, path, data) is None:
        return None, f"{path} is there and is not one bin/vh studio wrote: left as it is (--dir puts the icon somewhere else)"
    why = build_app(path, register=not dir_) if platform == "macos" else build_desktop(path, data, register=not dir_)
    return (None, why) if why else (path, None)


def remove(platform, dir_=None):
    path, data = where(platform, dir_)
    if not path.exists():
        return None, None
    if _ours(platform, path, data) is None:
        return None, f"{path} is not one bin/vh studio wrote: left as it is"
    if platform == "macos":
        if not dir_:
            _lsregister("-u", path)
        shutil.rmtree(path)
    else:
        path.unlink()
        if data and data.is_dir():
            shutil.rmtree(data)
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
        if mark.get("launcher", LAUNCHER) != LAUNCHER or mark.get("icon", _icon_hash()) != _icon_hash():
            return {"state": "outdated", "path": str(p), "note": "made by an earlier bin/vh studio: --install-icon makes it again"}
        return {"state": "ok", "path": str(p), "note": "runs this clone (a git pull needs no reinstall)"}
    return {"state": "missing", "note": "not installed (optional): bin/vh studio --install-icon puts a launcher in "
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
    g.add_argument("--install-icon", action="store_true", help="put the launcher icon in your applications")
    g.add_argument("--remove-icon", action="store_true", help="take the launcher icon away")
    g.add_argument("--icon-status", action="store_true", help="is the launcher icon installed, and does it run this clone")
    g.add_argument("--icon", choices=["open", "alive", "quit"], help="what the launcher icon runs")
    ap.add_argument("--dir", help="with --install-icon, --remove-icon, --icon-status: this folder instead of your applications folder")
    ap.add_argument("--as", dest="as_", choices=["macos", "linux"], help=argparse.SUPPRESS)   # the other platform's icon (a check, on one machine)
    a = ap.parse_args(argv)
    if a.json:
        jsonerr.force()
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
            path, why = install(platform, a.dir)
            if not path:
                return jsonerr.fail("failed", f"studio: the icon was not made: {why}", rc=1)
            if a.json:
                print(json.dumps({"version": 1, "installed": str(path)}))
            else:
                print(f"✓ {APP}: {path}\n  " + ("click it in Finder or Launchpad, or drag it to the Dock. Clicked again, it brings Studio back; quitting it "
                                               "stops the Studio it started. It runs bin/vh studio in this clone: a git pull needs no reinstall."
                                               if platform == "macos" else ("it is in your applications menu. " if not a.dir else "") + "It runs bin/vh studio in this clone: a git pull needs no reinstall."))
            return 0
        path, why = remove(platform, a.dir)
        if why:
            return jsonerr.fail("refused", f"studio: {why}", rc=1)
        print(json.dumps({"version": 1, "removed": str(path) if path else None}) if a.json else
              (f"✓ removed {path}" if path else "studio: no icon to remove there"))
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
        print(server.said(rec) + ("" if rec["where"] == "studio" else f" (on {project.name}, in its own desk: it is outside Studio's folders)")
              + ("\n  It started in the background; it stops by itself 12 h after its window closes." if rec.get("started") else ""), flush=True)
    else:
        _say(server.said(rec, icon=a.icon == "open"))
    return rc


if __name__ == "__main__":
    import activity   # tools/activity.py: bin/vh exec's into this, so this process writes the run's end
    sys.exit(activity.exiting(lambda: jsonerr.guard(lambda: main(sys.argv[1:]))))
