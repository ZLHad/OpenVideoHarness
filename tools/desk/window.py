"""Studio's window: the one place that knows how a window is made, raised and closed. A desktop shell (Electron, later)
replaces this file and nothing else: the desk gives it an address with a one-time code and asks it to show, raise or close.

  browser()                 the visible Chromium-family program to make the window with: $OVH_STUDIO_BROWSER (a path, or
                            "none"), else Google Chrome, Chromium, Microsoft Edge or Brave where they install, else
                            $CHROME_PATH; never a headless one (chrome-headless-shell, --headless): a window nobody sees
  profile(name)             Studio's own browser profile for one desk (~/.cache/ovh/studio-window/<name>, $XDG_CACHE_HOME;
                            $OVH_STUDIO_PROFILES instead in the checks):
                            no extensions, no other tabs, no session of the person's to fetch the address again; the page's
                            access lives in its storage only
  main_pid(profile)         the browser process that holds that profile (its window or windows), or None
  launch(prog, profile, url)   a window of its own (--app: no address bar, no tabs), started apart from the caller
  raise_(profile)           bring that window to the front → True when asked of the system (macOS: NSRunningApplication
                            by pid, through osascript's JavaScript, which needs no permission; Linux: wmctrl or xdotool when
                            there; $OVH_STUDIO_ACTIVATE <pid> stands in for it in tests)
  close(profile)            end that browser process (its window goes) → True when none is left
  tab(url)                  the fallback: a tab of the default browser ($BROWSER alone when it is set)

Why a program named outright and a profile of its own (2026-11-16): an address handed to "the default browser" went to a
headless Chrome another tool had left running, and nobody saw a window. The desk then waits for the page to connect back,
and only that counts as open (server.Desk.show).
"""
import os, shutil, signal, subprocess, sys, time
from pathlib import Path

MAC_APPS = ("Google Chrome", "Chromium", "Microsoft Edge", "Brave Browser")
LINUX_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "microsoft-edge-stable",
               "brave-browser")
CLASS = "OVHStudio"   # the window's class on Linux (--class): what wmctrl and xdotool find it by


def _visible(path):
    p = str(path).lower()
    return "headless" not in p and os.access(str(path), os.X_OK) and os.path.isfile(str(path))


def browser():
    """The program, or None (no Chromium-family browser here: the desk falls back to a tab)."""
    given = os.environ.get("OVH_STUDIO_BROWSER")
    if given is not None:
        return None if given.strip().lower() in ("", "none") else given
    cands = []
    if sys.platform == "darwin":
        for base in ("/Applications", str(Path.home() / "Applications")):
            cands += [f"{base}/{a}.app/Contents/MacOS/{a}" for a in MAC_APPS]
    else:
        cands += [shutil.which(n) or "" for n in LINUX_NAMES]
    if os.environ.get("CHROME_PATH"):
        cands.append(os.environ["CHROME_PATH"])
    return next((c for c in cands if c and _visible(c)), None)


def profile(name):
    """$OVH_STUDIO_PROFILES/<name> when set (the checks: never the person's own window), else the cache folder's."""
    base = Path(os.environ["OVH_STUDIO_PROFILES"]) if os.environ.get("OVH_STUDIO_PROFILES") else \
        Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "ovh" / "studio-window"
    p = base / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def _argv(prog):
    """A stand-in for tests may be a script: run it with this Python."""
    return [sys.executable, prog] if prog.endswith(".py") else [prog]


def main_pid(prof):
    """The process whose command line holds --user-data-dir=<profile> and is no helper (--type=)."""
    flag = f"--user-data-dir={prof}"
    try:
        out = subprocess.run(["ps", "-ax", "-o", "pid=,command="], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    for line in out.splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if (flag + " ") in (cmd + " ") and "--type=" not in cmd and pid.isdigit() and int(pid) != os.getpid():
            return int(pid)
    return None


def launch(prog, prof, url, size=(1440, 900)):
    """Start the browser with a window of its own at url. The caller does not wait for it; whether it shows is known
    when its page connects back."""
    args = _argv(prog) + [f"--user-data-dir={prof}", f"--app={url}", "--no-first-run", "--no-default-browser-check",
                          f"--window-size={size[0]},{size[1]}", f"--class={CLASS}", "--disable-features=Translate"]
    try:
        subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return True
    except OSError:
        return False


RAISE_JS = ("ObjC.import('AppKit'); function run(a) { const x = $.NSRunningApplication.runningApplicationWithProcessIdentifier(parseInt(a[0]));"
            " return (x && !x.isNil()) ? String(x.activateWithOptions($.NSApplicationActivateAllWindows | $.NSApplicationActivateIgnoringOtherApps)) : 'none'; }")


def raise_(prof):
    pid = main_pid(prof)
    if not pid:
        return False
    stand_in = os.environ.get("OVH_STUDIO_ACTIVATE")
    try:
        if stand_in:
            return subprocess.run([stand_in, str(pid)], capture_output=True, timeout=15).returncode == 0
        if sys.platform == "darwin":
            r = subprocess.run(["osascript", "-l", "JavaScript", "-e", RAISE_JS, str(pid)], capture_output=True, text=True, timeout=15)
            return r.stdout.strip() == "true"
        for cmd in (["wmctrl", "-x", "-a", CLASS], ["xdotool", "search", "--class", CLASS, "windowactivate"]):
            if shutil.which(cmd[0]) and subprocess.run(cmd, capture_output=True, timeout=15).returncode == 0:
                return True
    except (OSError, subprocess.SubprocessError):
        pass
    return False


def close(prof, wait=8.0):
    pid = main_pid(prof)
    if not pid:
        return True
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except PermissionError:
        return False
    end = time.time() + wait
    while time.time() < end:
        if main_pid(prof) is None:
            return True
        time.sleep(0.2)
    try:
        os.kill(pid, signal.SIGKILL)
    except OSError:
        pass
    time.sleep(0.5)
    return main_pid(prof) is None


def tab(url):
    """A tab of the default browser. With $BROWSER set, that command alone (as webbrowser reads it: %s for the address,
    else after it), and never the system's browser after it when it fails: a check's stand-in must not fall through to the
    person's real browser."""
    given = os.environ.get("BROWSER")
    if given:
        import shlex
        for cmd in given.split(os.pathsep):
            try:
                args = shlex.split(cmd)
                args = [a.replace("%s", url) for a in args] if any("%s" in a for a in args) else args + [url]
                if args and subprocess.run(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30).returncode == 0:
                    return True
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
        return False
    try:
        import webbrowser
        return bool(webbrowser.open(url, new=2))
    except Exception:
        return False
