"""A decoy "running Studio" for tools/ci.sh. It leaves the record a running Studio leaves in the place every bin/vh looks
for one (server._info_path: console-<id>.json in ovh-desk-<uid> in the temp folder), pointing at this process, which
answers nothing and notes every connection it gets. tools/ci.sh puts it where a check without a temp folder of its own
would find a Studio (the run's own temp folder, never the person's) and, after the groups, wants the record byte for byte
as it was, nothing new beside it and no connection noted: no check saw, joined or asked a Studio it did not start.

  python3 tools/desk/fixtures/decoy_studio.py <log>            stands until TERM; <log>.ready once the record is written
  python3 tools/desk/fixtures/decoy_studio.py --check <log>    exit 0 when untouched, else 1 and what changed
"""
import hashlib, json, os, signal, socket, sys, threading, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import server  # noqa: E402  (the same rule every bin/vh finds a Studio by)


def place():
    return server._info_path(None, [])


def listing(d):
    return sorted(os.listdir(d)) if d and os.path.isdir(d) else []


def stand(log):
    info_p = place()
    if info_p is None:
        sys.exit("decoy: no folder of this user's own in the temp folder")
    if info_p.exists():
        sys.exit(f"decoy: {info_p} is there already: a Studio this run did not start")
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    s.listen(16)
    port = s.getsockname()[1]
    rec = {"pid": os.getpid(), "port": port, "url": f"http://127.0.0.1:{port}/", "started": "2026-01-01T00:00:00", "roots": [],
           "only": False, "idle": None, "owner": "decoy"}
    body = json.dumps(rec).encode()
    info_p.write_bytes(body)
    lock = threading.Lock()
    Path(log).write_text("")

    def note(conn):
        conn.settimeout(2)
        try:
            first = conn.recv(200)
        except OSError:
            first = b""
        conn.close()
        with lock, open(log, "a") as f:
            f.write(json.dumps({"t": round(time.time(), 1), "asked": first.split(b"\r\n")[0].decode("latin-1")}) + "\n")

    Path(log + ".ready").write_text(json.dumps({"record": str(info_p), "sha256": hashlib.sha256(body).hexdigest(),
                                                "beside": listing(info_p.parent)}))
    signal.signal(signal.SIGTERM, lambda *_: os._exit(0))
    while True:
        conn, _ = s.accept()
        threading.Thread(target=note, args=(conn,), daemon=True).start()


def check(log):
    try:
        ready = json.loads(Path(log + ".ready").read_text())
    except (OSError, ValueError):
        print("the decoy never stood (no record written)")
        return 1
    bad = []
    rec = Path(ready["record"])
    try:
        if hashlib.sha256(rec.read_bytes()).hexdigest() != ready["sha256"]:
            bad.append(f"its record changed: {rec.read_text()[:200]}")
    except OSError:
        bad.append("its record is gone")
    new = sorted(set(listing(rec.parent)) - set(ready["beside"]))
    if new:
        bad.append(f"new beside it: {', '.join(new)}" + (f" ({rec.with_name(rec.stem + '.films').read_text()[:300]})"
                                                        if rec.with_name(rec.stem + ".films").exists() else ""))
    asked = Path(log).read_text().splitlines() if Path(log).exists() else []
    if asked:
        bad.append(f"{len(asked)} connection(s) to it: " + "; ".join(json.loads(x)["asked"] or "(a look, nothing asked)" for x in asked[:5]))
    if bad:
        print("; ".join(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["--check"] and len(sys.argv) == 3:
        sys.exit(check(sys.argv[2]))
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    stand(sys.argv[1])
