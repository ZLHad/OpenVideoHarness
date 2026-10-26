"""Downloads for the commands that bring material in, and the network convention they all keep (CONTRIBUTING.md, 联网的命令).
Stdlib only.

download(url, dest, sha256=None, rate=None, opener=None, timeout=60, retries=3, headers=None, max_bytes=None) → {"path",
"url", "sha256", "bytes", "resumed", "status", "content_type"}:
  - the bytes go to <dest>.part first, and <dest>.part becomes <dest> (os.replace) only when they are all there: dest is
    never half written. A .part already there is resumed with Range: bytes=<its size>-: a 206 appends to it, a 200 (a
    server that ignores ranges) starts it over, a 416 whose Content-Range total is the .part's size means it was complete
  - rate: at most this many bytes a second, on average over the download ("2M", "500K", or a number)
  - the sha256 is taken as the bytes arrive (a resumed .part is read once first). Given one, a mismatch deletes the .part
    and raises: the next try starts clean
  - a dropped connection, a timeout or a short body is tried again from where it stopped, `retries` times (1, 2, 4 s apart)
  - max_bytes: a file the server says is larger is refused before a byte of it is written (FetchError, its size said)
get_json(url, opener=None, headers=None, timeout=60) → the JSON of a GET (an API's search results).
serve(url, opener=None, rate=None) → a context: (a local http://127.0.0.1 address for that one file, stats) for a program
that reads it with HTTP ranges itself (ffmpeg -ss … -i <it> reads only the parts it needs: the index, then the seconds
asked for). Each request's Range goes to the file through the opener, so a recording answers it as well; stats["bytes"]
is what was read from the file, stats["size"] its whole size once a response said it. Only on 127.0.0.1, only that file.

The opener: Live (urllib, with a User-Agent naming the project; keys belong in headers, never in a URL), Replay(dir) (the
responses recorded in dir/responses.json, matched by URL; a Range is honoured by slicing the recorded body, so a resume
is tested offline too; a recorded "ranges": false answers 200 to a Range, as a server that ignores them), or Record(dir)
(live, each response saved into dir). opener_from(offline): Replay(offline) when a folder is given (the command's
--offline), else Record(OVH_RECORD) when that variable names one, else Live. A recording keeps no request headers (a key
travels in them) and no cookies, refuses a URL that carries a credential in its query or a user:password, and cuts a
body over 256 kB to its first 256 kB with its length noted: a fixture stays small and holds no one's whole file. Every
message names a URL as redact() writes it (no user:password, no query values), and so do the records bin/vh assets
writes.
"""
import contextlib, hashlib, http.client, http.server, json, os, re, threading, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

UA = "OpenVideoHarness (+https://github.com/ZLHad/OpenVideoHarness)"
CUT = 256 * 1024
CHUNK = 64 * 1024


class FetchError(Exception):
    """A download or a request that did not succeed (said why; its URL as redact() writes it)."""


SECRET = re.compile(r"key|token|sig|auth|credential|pass(?:word|wd)?|secret|session|x-amz-|x-goog-", re.I)


def redact(url):
    """A URL as it may be written down or printed: no user:password@, each query value and the fragment as … (the keys
    kept), as the activity log writes one. A signed download link (?token=…, X-Amz-Signature=…) keeps no secret."""
    try:
        p = urllib.parse.urlsplit(url)
        host = p.hostname or ""
        port = p.port
    except ValueError:
        return "…"
    if ":" in host:
        host = f"[{host}]"
    q = "&".join(f"{k}=…" for k, _ in urllib.parse.parse_qsl(p.query, keep_blank_values=True)) or ("…" if p.query else "")
    return urllib.parse.urlunsplit((p.scheme, host + (f":{port}" if port else ""), p.path, q, "…" if p.fragment else ""))


def size_of(n):
    """A byte count as a person reads it: 3.2 GB, 41.5 MB, 230 kB."""
    return f"{n / 1e9:,.1f} GB" if n >= 1e9 else f"{n / 1e6:,.1f} MB" if n >= 1e6 else f"{n / 1e3:,.0f} kB"


def rate_of(s):
    """Bytes a second from "2M", "500K", "1.5m", 4096 or None (no limit)."""
    if s in (None, "", 0, "0"):
        return None
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([kKmMgG]?)[bB]?(?:/s)?\s*", str(s))
    if not m:
        raise ValueError(f"not a rate: {s!r} (2M, 500K, or bytes a second)")
    return float(m.group(1)) * {"": 1, "k": 1e3, "m": 1e6, "g": 1e9}[m.group(2).lower()]


class Response:
    def __init__(self, status, headers, read, close=lambda: None):
        self.status, self.headers, self.read, self.close = status, {k.lower(): v for k, v in headers.items()}, read, close


class Live:
    def open(self, url, headers=None, timeout=60):
        req = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
        try:
            r = urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.HTTPError as e:
            if e.code == 416:
                return Response(416, dict(e.headers or {}), lambda n=-1: b"", e.close)
            raise FetchError(f"{redact(url)}: HTTP {e.code} {e.reason}")
        except (urllib.error.URLError, OSError) as e:
            raise ConnectionError(f"{redact(url)}: {getattr(e, 'reason', e)}")
        return Response(r.status, dict(r.headers), r.read, r.close)


class Replay:
    """The responses recorded in a folder (dir/responses.json: [{"url", "status", "headers", "body", "ranges"?}])."""
    def __init__(self, folder):
        self.dir = Path(folder)
        try:
            self.recs = json.loads((self.dir / "responses.json").read_text(encoding="utf-8"))["responses"]
        except (OSError, ValueError, KeyError, TypeError) as e:
            raise FetchError(f"{self.dir}: no recorded responses ({e})")
        self.seen = []

    def open(self, url, headers=None, timeout=60):
        self.seen.append(url)
        rec = next((r for r in self.recs if r.get("url") == url), None)
        if rec is None:
            raise FetchError(f"{redact(url)}: no recorded response in {self.dir} (record one: OVH_RECORD=<folder> and the same command online)")
        if rec.get("status", 200) >= 400:
            raise FetchError(f"{redact(url)}: HTTP {rec['status']} (recorded)")
        try:
            body = (self.dir / rec["body"]).read_bytes() if rec.get("body") else b""
        except OSError as e:
            raise FetchError(f"{redact(url)}: its recorded body {rec['body']} cannot be read ({e.strerror or e})")
        h = dict(rec.get("headers") or {})
        status = rec.get("status", 200)
        m = re.match(r"bytes=(\d+)-$", (headers or {}).get("Range", ""))
        if m and rec.get("ranges", True):
            a = int(m.group(1))
            if a >= len(body):
                return Response(416, {"Content-Range": f"bytes */{len(body)}"}, lambda n=-1: b"")
            body, status = body[a:], 206
            h["Content-Range"] = f"bytes {a}-{a + len(body) - 1}/{a + len(body)}"
        h["Content-Length"] = str(len(body))
        pos = [0]
        def read(n=-1):
            part = body[pos[0]:] if n is None or n < 0 else body[pos[0]:pos[0] + n]
            pos[0] += len(part)
            return part
        return Response(status, h, read)


class Record(Live):
    """Live, and each response saved into a folder for Replay."""
    def __init__(self, folder):
        self.dir = Path(folder)
        self.dir.mkdir(parents=True, exist_ok=True)

    def open(self, url, headers=None, timeout=60):
        keys = [k for k, _ in urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query, keep_blank_values=True) if SECRET.search(k)]
        if keys or urllib.parse.urlsplit(url).password is not None:
            raise FetchError(f"{redact(url)}: not recorded: the URL carries a credential ({', '.join(keys) or 'user:password'}); "
                             "a key belongs in a header, and a signed link in no fixture")
        r = super().open(url, headers, timeout)
        body = r.read()
        r.close()
        f = self.dir / "responses.json"
        try:
            recs = json.loads(f.read_text(encoding="utf-8"))["responses"]
        except (OSError, ValueError, KeyError):
            recs = []
        name = "body-" + hashlib.sha256(url.encode()).hexdigest()[:12]
        (self.dir / name).write_bytes(body[:CUT])
        keep = {k: v for k, v in r.headers.items() if k in ("content-type", "content-length", "content-range", "etag", "last-modified")}
        rec = {"url": url, "status": r.status, "headers": keep, "body": name, "bytes": len(body)}
        if len(body) > CUT:
            rec["cut"] = True
        recs = [x for x in recs if x.get("url") != url] + [rec]
        f.write_text(json.dumps({"v": 1, "responses": recs}, indent=1) + "\n", encoding="utf-8")
        pos = [0]
        def read(n=-1):
            part = body[pos[0]:] if n is None or n < 0 else body[pos[0]:pos[0] + n]
            pos[0] += len(part)
            return part
        return Response(r.status, r.headers, read)


def opener_from(offline=None):
    if offline:
        return Replay(offline)
    if os.environ.get("OVH_RECORD"):
        return Record(os.environ["OVH_RECORD"])
    return Live()


def get_json(url, opener=None, headers=None, timeout=60):
    r = (opener or Live()).open(url, headers, timeout)
    try:
        data = r.read(16 << 20)
    finally:
        r.close()
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise FetchError(f"{redact(url)}: not JSON ({e})")


def _hasher(part):
    """A sha256 of the .part's bytes so far, and how many."""
    h, n = hashlib.sha256(), 0
    if part.exists():
        with open(part, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
                n += len(b)
    return h, n


def download(url, dest, sha256=None, rate=None, opener=None, timeout=60, retries=3, headers=None, max_bytes=None):
    opener = opener or Live()
    dest = Path(dest)
    part = dest.with_name(dest.name + ".part")
    dest.parent.mkdir(parents=True, exist_ok=True)
    rate = rate if isinstance(rate, (int, float)) else rate_of(rate)
    resumed, status, ctype, t0, got = False, None, None, time.monotonic(), 0
    h, hashed = _hasher(part)
    for attempt in range(retries + 1):
        have = part.stat().st_size if part.exists() else 0
        if hashed != have:   # the .part changed under the hash (started over, cut): hash it again
            h, hashed = _hasher(part)
        hd = dict(headers or {})
        if have:
            hd["Range"] = f"bytes={have}-"
        try:
            r = opener.open(url, hd, timeout)
        except ConnectionError as e:
            if attempt == retries:
                raise FetchError(f"{e} (after {retries + 1} tries; the part so far is kept in {part.name})")
            time.sleep(2 ** attempt)
            continue
        status, ctype, total = r.status, r.headers.get("content-type"), None
        try:
            if r.status == 416:
                m = re.match(r"bytes \*/(\d+)", r.headers.get("content-range", ""))
                if m and int(m.group(1)) == have:
                    break   # the .part was the whole file already
                part.unlink(missing_ok=True)   # a .part longer than the file, or a 416 for another reason: start over
                continue
            if r.status == 206 and have:
                m = re.match(r"bytes (\d+)-\d+/(\d+|\*)", r.headers.get("content-range", ""))
                if not m or int(m.group(1)) != have:
                    part.unlink(missing_ok=True)   # not the range asked for: start over
                    continue
                resumed, mode, total = True, "ab", int(m.group(2)) if m.group(2) != "*" else None
            elif r.status == 200:   # the whole file (a server that ignores ranges sends it all again)
                mode, total = "wb", int(r.headers["content-length"]) if r.headers.get("content-length", "").isdigit() else None
                h, hashed = hashlib.sha256(), 0
            else:
                raise FetchError(f"{redact(url)}: HTTP {r.status}")
            if max_bytes and total and total > max_bytes:
                part.unlink(missing_ok=True)
                raise FetchError(f"{redact(url)}: {size_of(total)}, over the {size_of(max_bytes)} cap: nothing downloaded")
            with open(part, mode) as f:
                while True:
                    b = r.read(CHUNK)
                    if not b:
                        break
                    f.write(b)
                    h.update(b)
                    hashed += len(b)
                    got += len(b)
                    if rate:   # ahead of the average the rate allows: wait until it is caught up
                        ahead = got / rate - (time.monotonic() - t0)
                        if ahead > 0:
                            time.sleep(ahead)
        except (ConnectionError, TimeoutError, http.client.HTTPException, OSError) as e:
            if isinstance(e, (FileNotFoundError, PermissionError)) or attempt == retries:
                raise FetchError(f"{redact(url)}: {e} (the part so far is kept in {part.name})")
            time.sleep(2 ** attempt)
            continue
        finally:
            r.close()
        if total is not None and hashed < total:
            if attempt == retries:
                raise FetchError(f"{redact(url)}: {hashed} of {total} bytes after {retries + 1} tries (the part is kept in {part.name})")
            continue
        break
    if not part.exists():
        raise FetchError(f"{redact(url)}: nothing was downloaded")
    if hashed != part.stat().st_size:
        h, hashed = _hasher(part)
    digest = h.hexdigest()
    if sha256 and digest != sha256.lower():
        part.unlink(missing_ok=True)
        raise FetchError(f"{redact(url)}: sha256 {digest[:12]}… is not the {sha256[:12]}… expected; the download is deleted")
    os.replace(part, dest)
    return {"path": str(dest), "url": redact(url), "sha256": digest, "bytes": dest.stat().st_size, "resumed": resumed, "status": status,
            "content_type": ctype}


@contextlib.contextmanager
def serve(url, opener=None, rate=None, timeout=60):
    """(local_url, stats) while the block runs: see the module's note. A request the opener cannot answer gets a 502 (the
    reading program then fails and says so); the reason is kept in stats["errors"]."""
    opener = opener or Live()
    rate = rate if isinstance(rate, (int, float)) else rate_of(rate)
    stats = {"bytes": 0, "size": None, "requests": 0, "errors": []}
    lock, t0 = threading.Lock(), time.monotonic()
    suffix = re.sub(r"[^A-Za-z0-9.]", "", Path(urllib.parse.urlsplit(url).path).suffix)[:8]
    path = "/file" + suffix

    class Handler(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def do_GET(self):
            if self.path != path:
                self.send_error(404)
                return
            rng = self.headers.get("Range")
            with lock:
                stats["requests"] += 1
            try:
                r = opener.open(url, {"Range": rng} if rng else None, timeout)
            except (FetchError, ConnectionError) as e:
                with lock:
                    stats["errors"].append(str(e))
                self.send_error(502, str(e)[:200])
                return
            try:
                h = r.headers
                m = re.match(r"bytes (?:\d+-\d+|\*)/(\d+)", h.get("content-range", ""))
                with lock:
                    if m:
                        stats["size"] = int(m.group(1))
                    elif r.status == 200 and h.get("content-length", "").isdigit():
                        stats["size"] = int(h["content-length"])
                self.send_response(r.status)
                for k in ("content-type", "content-length", "content-range", "last-modified", "etag"):
                    if h.get(k):
                        self.send_header(k.title(), h[k])
                self.send_header("Accept-Ranges", "bytes" if r.status == 206 or h.get("accept-ranges") == "bytes" else "none")
                self.end_headers()
                while True:
                    b = r.read(CHUNK)
                    if not b:
                        break
                    self.wfile.write(b)
                    with lock:
                        stats["bytes"] += len(b)
                        got = stats["bytes"]
                    if rate:
                        ahead = got / rate - (time.monotonic() - t0)
                        if ahead > 0:
                            time.sleep(ahead)
            except (BrokenPipeError, ConnectionResetError):
                pass   # the reader seeks elsewhere and drops this one: what it read is counted, the rest never fetched
            except (ConnectionError, TimeoutError, http.client.HTTPException, OSError) as e:
                with lock:
                    stats["errors"].append(f"{redact(url)}: {e}")
            finally:
                r.close()

    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    srv.daemon_threads = True
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    try:
        yield f"http://127.0.0.1:{srv.server_address[1]}{path}", stats
    finally:
        srv.shutdown()
        srv.server_close()
