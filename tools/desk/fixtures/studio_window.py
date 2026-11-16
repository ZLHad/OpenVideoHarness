"""A stand-in for Studio's window in the checks ($OVH_STUDIO_BROWSER=<this file>; tools/ci.sh sets it for the whole run,
so a run never opens a real window). Called as window.py calls a Chromium browser (--user-data-dir=<profile> --app=<url>),
it does what the desk needs of one: one process a profile (a second call while one runs is a second window: noted, and it
exits, as Chrome forwards it), the page fetched, its one-time code traded for the token (POST /api/claim), and the
presence stream held open until the desk ends it or this is stopped (then, like a window left open on a dead page, it
waits). Each event is one JSON line in <profile>/stand-in.log.

  FAKE_WINDOW=dead        start, but never fetch the page (a window whose page does not connect; a tab still does)
  --tab <url>             a tab of the default browser instead ($BROWSER="python3 <this file> --tab %s"): the same,
                          its log in $FAKE_TAB_DIR, and it returns at once (webbrowser waits for the command)
"""
import json, os, re, signal, sys, time, urllib.parse, urllib.request
from pathlib import Path


def main(argv):
    tab = "--tab" in argv
    url = next((a[len("--app="):] for a in argv if a.startswith("--app=")), None) or (argv[argv.index("--tab") + 1] if tab else None)
    prof = Path(next((a[len("--user-data-dir="):] for a in argv if a.startswith("--user-data-dir=")), "") or os.environ.get("FAKE_TAB_DIR", "."))
    prof.mkdir(parents=True, exist_ok=True)
    log = prof / "stand-in.log"

    def note(**e):
        with open(log, "a") as f:
            f.write(json.dumps(dict(e, t=round(time.time(), 2), pid=os.getpid())) + "\n")

    if tab:
        if os.fork():   # webbrowser waits for the command: the tab lives on in a child
            return 0
        os.setsid()
    pidf = prof / "stand-in.pid"
    if not tab and pidf.exists():
        try:
            old = int(pidf.read_text())
            os.kill(old, 0)
            note(event="second", url=re.sub(r"c=[^&#]*", "c=…", url or ""))   # Chrome would open a second window in that process
            return 0
        except (OSError, ValueError):
            pass
    if not tab:
        pidf.write_text(str(os.getpid()))

    def bye(*_):
        note(event="closed")
        if not tab:
            try:
                pidf.unlink()
            except OSError:
                pass
        os._exit(0)
    signal.signal(signal.SIGTERM, bye)
    signal.signal(signal.SIGINT, bye)
    note(event="tab" if tab else "launch", url=re.sub(r"c=[^&#]*", "c=…", url or ""))
    def wait():   # a window stays open on a page that is gone; a check's folder gone (its run ended), it goes too
        while prof.exists():
            time.sleep(1)
        os._exit(0)
    if os.environ.get("FAKE_WINDOW") == "dead" and not tab:
        wait()
    u = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(u.query)
    base = f"{u.scheme}://{u.netloc}"
    try:
        page = urllib.request.urlopen(url, timeout=10).read().decode()
        note(event="page", token_in_page=bool(re.search(r'name="desk-token" content="[^"]+"', page)))
        req = urllib.request.Request(base + "/api/claim", data=json.dumps({"c": (q.get("c") or [""])[0]}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        token = json.loads(urllib.request.urlopen(req, timeout=10).read()).get("token") or ""
        note(event="claimed", ok=bool(token))
        if token:   # kept in its profile, as a browser keeps it in its storage: a check reads it there, as a person's page holds it
            (prof / "stand-in.token").write_text(token)
        w = (q.get("w") or [""])[0]
        stream = urllib.request.urlopen(f"{base}/api/presence?token={urllib.parse.quote(token)}&w={w}", timeout=60)
        note(event="present")
        for raw in stream:
            line = raw.decode().strip()
            if line.startswith("data: ") and line != "data: {}":
                note(event="told", data=json.loads(line[6:]))
        note(event="lost")
    except Exception as e:
        note(event="failed", why=f"{type(e).__name__}: {e}"[:200])
    wait()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
