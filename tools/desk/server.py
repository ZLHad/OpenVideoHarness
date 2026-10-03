"""Review desk, server: one project, on 127.0.0.1 only, stdlib only.

  GET  /                 the desk (static/index.html, with this run's token)
  GET  /static/<file>    desk.js, desk.css
  GET  /api/data         the project, read fresh from its files (reader.read_project)
  GET  /api/status       is an agent waiting for feedback (bin/vh desk wait)?
  POST /api/feedback     a submission: checked, saved to out/review/feedback/, copied into REVIEW.md
  GET  /p/<path>         a file inside the project (HTTP Range, so video and audio can seek); nothing outside it,
                         no hidden files

Only requests whose Host is this server's own address are answered (no DNS rebinding); a POST also needs the token
printed into the page, a JSON body and, when the browser sends one, a same-origin Origin. So another web page open
in the same browser can neither read the project nor submit feedback in the reviewer's name.
"""
import datetime, http.server, json, mimetypes, os, re, secrets, signal, socket, socketserver, sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import feedback as F   # noqa: E402
import reader          # noqa: E402

STATIC = {"desk.js": "text/javascript; charset=utf-8", "desk.css": "text/css; charset=utf-8"}
DEFAULT_PORTS = range(8780, 8800)
CSP = ("default-src 'self'; img-src 'self' data: https:; media-src 'self' https:; style-src 'self' 'unsafe-inline'; "
       "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
# every project file is served sandboxed without allow-same-origin: an HTML or SVG in the project (a HyperFrames
# index.html, node_modules, a downloaded reference) opened from the desk runs in an opaque origin, so it can neither
# read the page's token nor post feedback in the reviewer's name
P_CSP = "sandbox allow-scripts allow-popups"
mimetypes.add_type("text/markdown", ".md")
mimetypes.add_type("audio/wav", ".wav")


class Desk(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, project):
        super().__init__(("127.0.0.1", port), Handler)
        self.project = Path(project).resolve()
        self.token = secrets.token_urlsafe(24)
        self.port = self.server_address[1]
        self.hosts = {f"{h}:{self.port}" for h in ("127.0.0.1", "localhost")}

    def server_bind(self):
        # HTTPServer.server_bind asks socket.getfqdn("127.0.0.1"), a reverse DNS lookup that can stall for many seconds
        # (it did on GitHub's macOS runners, before the server printed its address); the desk only answers on 127.0.0.1
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = "127.0.0.1", self.server_address[1]

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/"


class Handler(http.server.BaseHTTPRequestHandler):
    server_version = "vh-desk"
    sys_version = ""
    timeout = 30   # a socket that stops sending (a body shorter than its Content-Length) frees its thread

    def log_message(self, fmt, *a):   # quiet: an agent's background log stays readable
        pass

    # ---------- responses ----------
    def _head(self, code, ctype, length, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def _send(self, code, body, ctype, extra=None):
        self._head(code, ctype, len(body), extra)
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, code, msg):
        self._json({"error": msg}, code)

    def _host_ok(self):
        if self.headers.get("Host", "") in self.server.hosts:
            return True
        self._error(403, "this desk only answers on its own address")
        return False

    # ---------- GET ----------
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._host_ok():
            return
        path = urlsplit(self.path).path
        if path in ("/", "/index.html"):
            page = (HERE / "static" / "index.html").read_text(encoding="utf-8").replace("{{TOKEN}}", self.server.token)
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8", {"Content-Security-Policy": CSP})
        if path.startswith("/static/") and path[8:] in STATIC:
            return self._send(200, (HERE / "static" / path[8:]).read_bytes(), STATIC[path[8:]])
        if path == "/api/data":
            try:
                data = reader.read_project(self.server.project)
            except Exception as e:   # a reader bug must not take the desk down; the page says what happened
                return self._error(500, f"could not read the project: {type(e).__name__}: {e}")
            return self._json(data)
        if path == "/api/status":
            return self._json(dict(F.listening(self.server.project), project=self.server.project.name))
        if path.startswith("/p/"):
            return self._file(path[3:])
        self._error(404, "not found")

    def _resolve(self, rel):
        """A file inside the project, or None: no '..', no hidden parts (.env, .git, .listening), no *.env, checked
        on the name asked for and on the file it resolves to (a symlink to .env is refused too), ignoring case."""
        rel = unquote(rel)
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        hidden = lambda ps: any(p == ".." or p.startswith(".") or p.lower().endswith(".env") for p in ps)   # noqa: E731
        if not parts or "\x00" in rel or hidden(parts):
            return None
        root = os.path.realpath(str(self.server.project))
        f = os.path.realpath(os.path.join(root, *parts))
        if os.path.commonpath([f, root]) != root or not os.path.isfile(f) or hidden(os.path.relpath(f, root).split(os.sep)):
            return None
        return f

    def _file(self, rel):
        f = self._resolve(rel)
        if not f:
            return self._error(404, "no such file in this project")
        size = os.path.getsize(f)
        ctype = mimetypes.guess_type(f)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype == "application/json":
            ctype += "; charset=utf-8"
        rng = self.headers.get("Range", "")
        m = re.fullmatch(r"bytes=(\d*)-(\d*)", rng.strip())
        sandbox = {"Content-Security-Policy": P_CSP}
        if rng and m and (m.group(1) or m.group(2)):
            if m.group(1):
                start, end = int(m.group(1)), int(m.group(2)) if m.group(2) else size - 1
            else:   # bytes=-500: the last 500
                start, end = max(0, size - int(m.group(2))), size - 1
            end = min(end, size - 1)
            if start > end or start >= size:
                return self._send(416, b"", "text/plain", dict(sandbox, **{"Content-Range": f"bytes */{size}"}))
            self._head(206, ctype, end - start + 1, dict(sandbox, **{"Content-Range": f"bytes {start}-{end}/{size}", "Accept-Ranges": "bytes"}))
        else:
            start, end = 0, size - 1
            self._head(200, ctype, size, dict(sandbox, **{"Accept-Ranges": "bytes"}))
        if self.command == "HEAD":
            return
        try:
            with open(f, "rb") as fh:
                fh.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = fh.read(min(1 << 16, left))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except OSError:   # the player seeked away, or stopped reading until the socket timed out
            self.close_connection = True

    # ---------- POST ----------
    def do_POST(self):
        if not self._host_ok():
            return
        if urlsplit(self.path).path != "/api/feedback":
            return self._error(404, "not found")
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc not in self.server.hosts:
            return self._error(403, "cross-origin request refused")
        given = self.headers.get("X-Desk-Token", "").encode("utf-8", "replace")   # bytes: a non-ASCII str would raise
        if not secrets.compare_digest(given, self.server.token.encode("ascii")):
            return self._error(403, "missing or wrong desk token: reload the page")
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._error(415, "send JSON")
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > F.MAX_BODY:
            return self._error(413 if n > 0 else 400, f"empty, or larger than {F.MAX_BODY // 1024} KiB")
        try:
            body = self.rfile.read(n)
        except OSError:   # timed out waiting for the rest of the body
            self.close_connection = True
            return self._error(408, "the request body did not arrive")
        if len(body) < n:
            self.close_connection = True
            return self._error(400, f"the body is {len(body)} bytes, not the {n} its Content-Length says")
        try:
            fb = F.validate(self.server.project, json.loads(body.decode("utf-8")))
        except (ValueError, TypeError, AttributeError, RecursionError) as e:   # UnicodeDecodeError is a ValueError
            return self._error(400, str(e) or type(e).__name__)
        path = F.save(self.server.project, fb)
        sys.stderr.write(f"desk: feedback saved → {path} (also in REVIEW.md)\n")
        sys.stderr.flush()
        self._json(dict(F.listening(self.server.project), saved=os.path.relpath(path, self.server.project)))


# ---------- start, once per project ----------

def running(project):
    """The URL of a desk already serving this project (out/review/.desk.json names this very folder, its process is
    alive and its port answers), else None. A copied project carries the original's file; the path tells them apart."""
    info_p = Path(project) / "out" / "review" / ".desk.json"
    try:
        info = json.loads(info_p.read_text())
        if info.get("project") != os.path.realpath(str(project)):
            return None
        os.kill(int(info["pid"]), 0)
        with socket.create_connection(("127.0.0.1", int(info["port"])), timeout=1):
            pass
    except PermissionError:
        return info.get("url")
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return info.get("url")


def serve(project, port=None):
    """Serve until stopped. port None: the first free of 8780–8799; 0: any free port. → exit code."""
    project = Path(project).resolve()
    url = running(project)
    if url:
        print(f"desk: already serving {project.name} at {url} (stop that process to start another)", flush=True)
        return 0
    srv, last = None, None
    for p in ([port] if port is not None else DEFAULT_PORTS):
        try:
            srv = Desk(p, project)
            break
        except OSError as e:
            last = e
    if srv is None:
        print(f"desk: no free port ({last}); pick one with --port N", file=sys.stderr)
        return 2
    info_p = project / "out" / "review" / ".desk.json"
    info_p.parent.mkdir(parents=True, exist_ok=True)
    info_p.write_text(json.dumps({"pid": os.getpid(), "port": srv.port, "url": srv.url, "project": os.path.realpath(str(project)),
                                  "started": datetime.datetime.now().isoformat(timespec="seconds")}))

    def stop(signum, _frame):
        raise SystemExit(0)
    for s in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, stop)
    print(f"desk: {srv.url}  ·  {project.name}  (Ctrl-C stops it)", flush=True)
    try:
        srv.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        try:
            if json.loads(info_p.read_text()).get("pid") == os.getpid():
                info_p.unlink()
        except (OSError, ValueError):
            pass
    return 0


if __name__ == "__main__":
    sys.exit(serve(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None))
