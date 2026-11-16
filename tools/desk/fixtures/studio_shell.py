"""A stand-in for Studio's own app (tools/desk/shell) in the checks ($OVH_STUDIO_SHELL=<this file>, with
$OVH_STUDIO_SHELL_PROFILE: its folder). Called as window.shell_send calls the app (--ovh-from-console, one line of JSON on
stdin), it does what the console needs of it: one process a profile (a second start hands its line to the running one,
through <profile>/forward.jsonl, and exits 0, as Electron's single-instance lock does), one window a role: {url, role, w,
fresh} raises that role's window, or loads the url (a new window, or the same one again when fresh or on another
console), whose page trades its code and holds the presence stream; {close: role} closes it, and with none left it ends.
Each event is one JSON line in <profile>/shell.log, with the program's own command line in the first.

  FAKE_SHELL=broken       exit 1 at once (an app that cannot start)
"""
import json, os, re, signal, sys, threading, time, urllib.parse, urllib.request
from pathlib import Path


def main(argv):
    if os.environ.get("FAKE_SHELL") == "broken":
        return 1
    prof = Path(os.environ.get("OVH_STUDIO_SHELL_PROFILE") or ".")
    prof.mkdir(parents=True, exist_ok=True)
    log, pidf, fwd = prof / "shell.log", prof / "shell.pid", prof / "forward.jsonl"
    lock = threading.Lock()

    def note(**e):
        with lock, open(log, "a") as f:
            f.write(json.dumps(dict(e, t=round(time.time(), 2), pid=os.getpid())) + "\n")

    line = sys.stdin.readline() if "--ovh-from-console" in argv else ""
    try:
        msg = json.loads(line) if line.strip() else None
    except ValueError:
        msg = None
    if pidf.exists():
        try:
            os.kill(int(pidf.read_text()), 0)
            with open(fwd, "a") as f:   # the running one takes it
                f.write(json.dumps(msg) + "\n")
            return 0
        except (OSError, ValueError):
            pass
    pidf.write_text(str(os.getpid()))
    note(event="start", argv=" ".join(argv), code_in_argv=bool(re.search(r"[?&]c=", " ".join(argv))))
    windows = {}   # role → {"origin", "stop": Event}

    def bye(*_):
        note(event="quit")
        try:
            pidf.unlink()
        except OSError:
            pass
        os._exit(0)
    signal.signal(signal.SIGTERM, bye)
    signal.signal(signal.SIGINT, bye)

    def page(role, url, stop):
        u = urllib.parse.urlsplit(url)
        q = urllib.parse.parse_qs(u.query)
        base = f"{u.scheme}://{u.netloc}"
        try:
            urllib.request.urlopen(url, timeout=10).read()
            req = urllib.request.Request(base + "/api/claim", data=json.dumps({"c": (q.get("c") or [""])[0]}).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
            token = json.loads(urllib.request.urlopen(req, timeout=10).read()).get("token") or ""
            note(event="claimed", role=role, ok=bool(token))
            if token:
                (prof / f"token-{role}").write_text(token)
            s = urllib.request.urlopen(f"{base}/api/presence?token={urllib.parse.quote(token)}&w={(q.get('w') or [''])[0]}", timeout=60)
            note(event="present", role=role)
            for raw in s:
                if stop.is_set():
                    break
                ln = raw.decode().strip()
                if ln.startswith("data: ") and ln != "data: {}":
                    note(event="told", role=role, data=json.loads(ln[6:]))
            note(event="lost", role=role)
        except Exception as e:
            note(event="failed", role=role, why=f"{type(e).__name__}: {e}"[:200])

    def handle(m):
        if not isinstance(m, dict):
            return
        if isinstance(m.get("close"), str):
            w = windows.pop(m["close"], None)
            if w:
                w["stop"].set()
                note(event="closed", role=m["close"])
            if not windows:
                bye()
            return
        url, role = m.get("url"), m.get("role") or "console"
        if not isinstance(url, str) or not re.match(r"^http://127\.0\.0\.1:\d+/", url):
            return
        origin = re.match(r"^http://127\.0\.0\.1:\d+", url).group(0)
        w = windows.get(role)
        if w and w["origin"] == origin and not m.get("fresh"):
            note(event="raised", role=role)
            return
        if w:
            w["stop"].set()
        stop = threading.Event()
        windows[role] = {"origin": origin, "stop": stop}
        note(event="window", role=role, reload=bool(w))
        threading.Thread(target=page, args=(role, url, stop), daemon=True).start()

    handle(msg)
    seen = 0
    while prof.exists():   # a check's folder gone (its run ended): this goes too
        if fwd.exists():
            lines = fwd.read_text().splitlines()
            for ln in lines[seen:]:
                try:
                    handle(json.loads(ln))
                except ValueError:
                    pass
            seen = len(lines)
        time.sleep(0.1)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
