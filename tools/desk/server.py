"""Review desk and console, server: on 127.0.0.1 only, stdlib only.

Started for a project (bin/vh desk <project>, or bin/vh gate on the desk channel) the page opens on that project; started
without one (bin/vh desk) it opens on the console's home, every project bin/vh projects finds. Either way the page reaches
every project under the roots (bin/vh projects': $OVH_PROJECTS, <repo>/projects, each --root), and the project it was
started for wherever that is. The project files and bin/vh are the truth: every answer is read fresh from them, and the page
keeps nothing of its own but the reviewer's draft (in the browser) until it is submitted.

  GET  /                          the page (static/index.html, with this run's token and the project it opens on)
  GET  /static/<file>             ui.css and ui.js (the gate view's: the static review page inlines the same two files),
                                  studio.css and studio.js (the console's shell and modules)
  GET  /api/projects              every project: bin/vh projects' rows, each with its key, a picture, and what it waits for
  GET  /api/p/<key>/data          one project, read fresh: reader.read_project, plus bin/vh status (status), its key and
                                  what the cut module lays out (studio: the resolved timeline, thumbnails, peaks, findings)
  GET  /api/p/<key>/gate/<id>     a gate page as the gate view's markup (tools/review.py: the static page's markup)
  GET  /api/p/<key>/stage         the project's film, or newest draft, as the same player markup, with its ruler
  GET  /api/p/<key>/status        is an agent waiting for this project's feedback (bin/vh desk wait)?
  POST /api/p/<key>/feedback      a submission: checked, saved to out/review/feedback/, copied into REVIEW.md
  GET  /f/<key>/<path>            a file inside that project (HTTP Range, so video and audio can seek); nothing outside
                                  it, no hidden files
  The desk's first addresses stay, for the project it was started for: /api/data (reader.read_project alone, as bin/vh desk
  data prints it), /api/status, /api/feedback, /p/<path>.

Only requests whose Host is this server's own address are answered (no DNS rebinding); a POST also needs the token
printed into the page, a JSON body and, when the browser sends one, a same-origin Origin. So another web page open
in the same browser can neither read a project nor submit feedback in the reviewer's name.
"""
import datetime, hashlib, http.server, json, mimetypes, os, re, secrets, signal, socket, socketserver, sys, tempfile, threading, time
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import feedback as F   # noqa: E402
import reader          # noqa: E402
import review          # noqa: E402  (tools/review.py: the gate view, the same markup as the static page)

STATIC = {"ui.css": "text/css; charset=utf-8", "ui.js": "text/javascript; charset=utf-8",
          "studio.css": "text/css; charset=utf-8", "studio.js": "text/javascript; charset=utf-8"}
DEFAULT_PORTS = range(8780, 8800)
LISTING_TTL = 4.0   # seconds a project listing is reused: the home page asks every few seconds, a walk of the roots is not free
FRESH_GAP = 10.0    # seconds between two walks of the roots that unknown keys ask for
CSP = ("default-src 'self'; img-src 'self' data: https:; media-src 'self' https:; style-src 'self' 'unsafe-inline'; "
       "script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
# every project file is served sandboxed without allow-same-origin: an HTML or SVG in the project (a HyperFrames
# index.html, node_modules, a downloaded reference) opened from the desk runs in an opaque origin, so it can neither
# read the page's token nor post feedback in the reviewer's name
P_CSP = "sandbox allow-scripts allow-popups"
IMG = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif")
VID = (".mp4", ".webm", ".mov", ".m4v")
mimetypes.add_type("text/markdown", ".md")
mimetypes.add_type("audio/wav", ".wav")
mimetypes.add_type("image/svg+xml", ".svg")


def pid_of(path):
    """A project folder's identity in the console: the SHA-1 of its real path. A submission carries it, and one whose
    address names another folder by then is refused, never written there."""
    return hashlib.sha1(os.path.realpath(str(path)).encode("utf-8", "surrogateescape")).hexdigest()


def keyify(name, path):
    """A project's key in the console's addresses: its name as bin/vh projects gives it (a / of a project in a subfolder as
    ~), then ~ and six hex digits of its folder's identity. The same folder always has the same key, whatever else appears
    under the roots or goes, and two folders of the same name never share one (Desk.listing lengthens the digits in the
    one-in-millions case of two that agree on six)."""
    base = re.sub(r"[/\\]+", "~", str(name)).strip("~") or "project"
    return f"{base}~{pid_of(path)[:6]}"


def link(key):
    """How a project path becomes an href in the console: /f/<key>/<path>."""
    return lambda rel: f"/f/{quote(key, safe='')}/" + quote(rel, safe="/")


def _inside(project, rel):
    """rel when it names a file inside the project (no '..', no hidden part), else None."""
    if not isinstance(rel, str) or not rel.strip() or re.match(r"(?i)[a-z][a-z0-9+.-]*:", rel):
        return None
    rel = rel.strip()
    parts = [p for p in rel.replace("\\", "/").split("/") if p not in ("", ".")]
    if not parts or any(p == ".." or p.startswith(".") for p in parts):
        return None
    root = os.path.realpath(str(project))
    f = os.path.realpath(os.path.join(root, *parts))
    return "/".join(parts) if os.path.commonpath([f, root]) == root and os.path.isfile(f) else None


def _newest(project, patterns):
    """The newest file matching any of the glob patterns, as a project path; None."""
    best = None
    for pat in patterns:
        for p in Path(project).glob(pat):
            try:
                m = p.stat().st_mtime
            except OSError:
                continue
            if p.is_file() and not p.name.startswith(".") and (best is None or m > best[0]):
                best = (m, p)
    return best[1].relative_to(project).as_posix() if best else None


def gate_now(project):
    """(this round's id, its gate JSON with includes) or (None, None)."""
    pages = review.gate_pages(project)
    if not pages:
        return None, None
    p = pages[-1]
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
        d = review.merge_includes(Path(project), d) if isinstance(d, dict) else {}
    except (OSError, ValueError):
        d = {}
    return p.stem[5:], d


def picture_of(project, row, gate):
    """The picture a project's card shows: what the person is asked to look at when the film waits for them (the round's
    first card frame, else its film, else its first picture, else a shot's key frame), else a cover, else the film itself (the card shows its middle frame), else a storyboard
    key frame, else the newest picture under out/review/ or out/check/. → {"path", "kind": image | video, "from"} or None."""
    project = Path(project)
    if row.get("state") == "waiting_person" and gate:
        for dec in gate.get("decisions") or []:
            for o in (dec.get("options") or []) if isinstance(dec, dict) else []:
                p = _inside(project, o.get("frame")) if isinstance(o, dict) else None
                if p:
                    return {"path": p, "kind": "image", "from": "gate"}
        assets = [a for a in gate.get("assets") or [] if isinstance(a, dict)]
        film = gate.get("film") if isinstance(gate.get("film"), str) else None
        for p in [film] + [a.get("path") for a in assets if str(a.get("path", "")).lower().endswith(VID)]:   # the film it asks about
            p = _inside(project, p)
            if p and p.lower().endswith(VID):
                return {"path": p, "kind": "video", "from": "gate"}
        for a in assets:
            p = _inside(project, a.get("path"))
            if p and p.lower().endswith(IMG):
                return {"path": p, "kind": "image", "from": "gate"}
        for s in gate.get("segments") or []:
            for sh in (s.get("shots") or []) if isinstance(s, dict) else []:
                p = _inside(project, sh.get("frame")) if isinstance(sh, dict) else None
                if p:
                    return {"path": p, "kind": "image", "from": "gate"}
    cover = _newest(project, [f"{d}/*{e}" for d in ("out/covers", "out/final/covers") for e in IMG]
                    + [f"{d}/cover*{e}" for d in ("out/final", "out/review", "out") for e in IMG])
    if cover:
        return {"path": cover, "kind": "image", "from": "cover"}
    film = (row.get("film") or {}).get("path") if isinstance(row.get("film"), dict) else None
    film = film if film and film.lower().endswith(VID) and _inside(project, film) else None
    if film:   # a still of the film before the film itself: bin/vh thumbs' picture of its middle shot
        still = _thumb_of(project, film)
        if still:
            return {"path": still, "kind": "image", "from": "thumbs"}
        return {"path": film, "kind": "video", "from": "film"}
    sheet = _newest(project, [f"out/check/*sheet*{e}" for e in IMG] + [f"out/check/*/*sheet*{e}" for e in IMG])
    if sheet:
        return {"path": sheet, "kind": "image", "from": "sheet"}
    for _, g in _gate_pictures(project):   # the pictures the stops showed, the newest page first
        return {"path": g, "kind": "image", "from": "gate"}
    frames = sorted(Path(project).glob("out/check/storyboard/frames/*.png"))
    if frames:
        return {"path": frames[len(frames) // 2].relative_to(project).as_posix(), "kind": "image", "from": "storyboard"}
    pic = _newest(project, [f"out/review/*{e}" for e in IMG] + [f"out/check/*{e}" for e in IMG] + [f"out/frames/*{e}" for e in IMG])
    if pic:
        return {"path": pic, "kind": "image", "from": "latest"}
    return None


def _thumb_of(project, film):
    """bin/vh thumbs' picture of the film's middle shot, when it made one for this film and it is there; else None."""
    rec = _load(Path(project) / "out" / "proxy" / (Path(film).stem + ".thumbs") / "thumbs.json")
    shots = [s for s in (rec or {}).get("shots") or [] if isinstance(s, dict) and _inside(project, s.get("file"))] if isinstance(rec, dict) else []
    return shots[len(shots) // 2]["file"] if shots else None


def _gate_pictures(project):
    """(gate id, picture) for every picture a gate page names that is there: its cards' frames, its pictures, its shots'
    key frames; the newest page first."""
    for page in reversed(review.gate_pages(project)):
        d = _load(page)
        if not isinstance(d, dict):
            continue
        cand = [o.get("frame") for dec in d.get("decisions") or [] if isinstance(dec, dict) for o in dec.get("options") or [] if isinstance(o, dict)]
        cand += [a.get("path") for a in d.get("assets") or [] if isinstance(a, dict)]
        cand += [sh.get("frame") for sg in d.get("segments") or [] if isinstance(sg, dict) for sh in sg.get("shots") or [] if isinstance(sh, dict)]
        for c in cand:
            p = _inside(project, c)
            if p and p.lower().endswith(IMG):
                yield page.stem[5:], p


def film_title(project, title):
    """The film's name: BRIEF's (bin/vh status's title), else the newest gate page's title up to its stop's name
    ("片名 · 关卡 ③ 初版" → "片名"), else the folder's name."""
    name = Path(project).name
    if title and title != name:
        return title
    for page in reversed(review.gate_pages(project)):
        d = _load(page)
        t = d.get("title") if isinstance(d, dict) else None
        if isinstance(t, str) and t.strip():
            head = re.split(r"\s+[·|｜—-]\s+(?=关卡|检查点|Gate|Checkpoint|E\d)", t.strip(), maxsplit=1)[0].strip()
            if head and head != t.strip():
                return head
    return title or name


def ask_of(row, gid, gate):
    """What a waiting project asks, in a line: the round's first question, else its summary. None when it waits for no one."""
    if row.get("state") != "waiting_person" or not gate:
        return None
    decs = [d for d in gate.get("decisions") or [] if isinstance(d, dict)]
    q = next((d.get("question") for d in decs if isinstance(d.get("question"), str) and d.get("question").strip()), None)
    s = gate.get("summary") if isinstance(gate.get("summary"), str) else ""
    return {"gate": gid, "title": review.gate_title(gid, "zh"), "title_en": review.gate_title(gid, "en"),
            "question": (q or s or "").strip()[:160], "decisions": len(decs)}


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def studio_extras(project, data):
    """What the cut module lays out, from what bin/vh has already made (nothing is run here): the resolved timeline (bin/vh
    timeline --resolved: shots, chapters, narration, captions, beats), the film's thumbnails and waveform peaks when bin/vh
    thumbs and peaks have made them, and the findings of its latest bin/vh check, each with its time. A part that is not there
    is None, and the page names the command that makes it."""
    st = data.get("status") or {}
    media = st.get("media") or {}
    out = {"timeline": None, "thumbs": None, "peaks": None, "findings": [], "check": None, "film": None, "film_missing": None, "sheet": None}
    # the film: this round's when its stop is the cut's (gate ③, E4, E5), else the one bin/vh status names, else its proxy
    want = []
    rounds = data.get("rounds") or []
    if rounds and re.match(r"(3|E4|E5)", str(rounds[-1].get("id", ""))):
        g = rounds[-1].get("data") or {}
        if isinstance(g.get("film"), str):
            want.append(g["film"])
        want += [a.get("path") for a in g.get("assets") or [] if isinstance(a, dict) and str(a.get("path", "")).lower().endswith(VID)]
    want += [media.get("film"), media.get("proxy")]
    want = [w for w in want if isinstance(w, str) and w.strip() and not re.match(r"(?i)https?://", w)]
    out["film"] = next((w for w in want if _inside(project, w)), None)
    if not out["film"] and want:
        out["film_missing"] = want[0]
    out["sheet"] = _newest(project, [f"out/check/*sheet*{e}" for e in IMG] + [f"out/check/*/*sheet*{e}" for e in IMG])   # a picture when there is no film
    try:
        import resolved
        out["timeline"] = resolved.document(Path(project), data.get("lang"))
        for sh in out["timeline"].get("shots") or []:   # a key frame that is not there is no key frame (and no 404)
            if isinstance(sh, dict) and sh.get("frame") and not re.match(r"(?i)https?://", str(sh["frame"])) and not _inside(project, sh["frame"]):
                sh["frame"] = None
    except (Exception, SystemExit) as e:   # one part's trouble is said, the rest is shown
        data["warnings"].append(f"bin/vh timeline --resolved: {type(e).__name__}: {e}")
    if media.get("thumbs"):
        t = _load(Path(project) / media["thumbs"])
        if isinstance(t, dict) and all(_inside(project, sh.get("file")) for sh in t.get("sheets") or [] if isinstance(sh, dict)):
            out["thumbs"] = {k: t.get(k) for k in ("duration", "tile", "shot", "sheets", "tiles")}
            out["thumbs"]["shots"] = [x for x in t.get("shots") or [] if isinstance(x, dict) and _inside(project, x.get("file"))]
    if media.get("peaks"):
        pk = _load(Path(project) / media["peaks"])
        if isinstance(pk, dict) and isinstance(pk.get("peaks"), list):
            out["peaks"] = {"duration": pk.get("duration"), "peaks": pk["peaks"]}
    chk = st.get("check")
    if isinstance(chk, dict) and chk.get("record"):
        rec = _load(Path(project) / chk["record"])
        if isinstance(rec, dict):
            out["check"] = {k: chk.get(k) for k in ("verdict", "video", "at", "stale", "counts")}
            out["findings"] = [{k: f.get(k) for k in ("kind", "severity", "message", "t", "t1")} for f in rec.get("findings") or []
                               if isinstance(f, dict) and f.get("severity") in ("fail", "warn")][:200]
    return out


class Desk(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port, project=None, roots=(), only=False):
        super().__init__(("127.0.0.1", port), Handler)
        self.project = Path(project).resolve() if project else None   # the project this desk was started for; None: the console
        self.own_key = keyify(self.project.name, self.project) if self.project else None
        self.only = bool(only and self.project)   # bin/vh gate's desk: this project and nothing else under the roots
        self._fresh_at = 0.0   # the last walk an unknown key asked for
        self.roots = [str(r) for r in roots]
        self.token = secrets.token_urlsafe(24)
        self.port = self.server_address[1]
        self.hosts = {f"{h}:{self.port}" for h in ("127.0.0.1", "localhost")}
        self.last = time.time()   # the last request: --idle stops a server nobody has asked anything for that long
        self._lock = threading.Lock()
        self._listing = (0.0, None)
        self._keys = {self.own_key: self.project} if self.project else {}

    def server_bind(self):
        # HTTPServer.server_bind asks socket.getfqdn("127.0.0.1"), a reverse DNS lookup that can stall for many seconds
        # (it did on GitHub's macOS runners, before the server printed its address); the desk only answers on 127.0.0.1
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = "127.0.0.1", self.server_address[1]

    @property
    def url(self):
        return f"http://127.0.0.1:{self.port}/"

    def listing(self, fresh=False):
        """bin/vh projects' record over this desk's roots (the project it was started for always in it), each row with its
        key; reused for LISTING_TTL seconds."""
        import projects as PJ
        import status as S
        with self._lock:
            when, rec = self._listing
            if rec is not None and not fresh and time.time() - when < LISTING_TTL:
                return rec
            if self.only:
                rec = {"version": 1, "roots": [], "count": 1, "projects": [PJ.row(self.project, self.project.name, S, False)]}
            else:
                rec = PJ.listing(self.roots)
                if self.project and not any(os.path.realpath(r["path"]) == os.path.realpath(str(self.project)) for r in rec["projects"]):
                    rec["projects"].append(PJ.row(self.project, self.project.name, S, False))
                    rec["count"] = len(rec["projects"])
            keys = {self.own_key: self.project} if self.project else {}
            for r in rec["projects"]:
                p = Path(r["path"])
                if self.project and os.path.realpath(str(p)) == os.path.realpath(str(self.project)):
                    r["key"] = self.own_key
                    continue
                k = keyify(r["name"], p)
                if k in keys and os.path.realpath(str(keys[k])) != os.path.realpath(str(p)):   # six digits shared: twelve
                    k = f"{k}{pid_of(p)[6:12]}"
                keys[k] = p
                r["key"] = k
            self._keys, self._listing = keys, (time.time(), rec)
            return rec

    def project_of(self, key):
        """The folder a key names, or None. A key not seen yet walks the roots once more, at most once in FRESH_GAP seconds
        (a tab still asking for a project that is gone, or any /f/<nonsense>/, does not walk them on every request)."""
        if key in self._keys:
            return self._keys[key]
        if self.only or time.time() - self._fresh_at < FRESH_GAP:
            return None
        self._fresh_at = time.time()
        self.listing(fresh=True)
        return self._keys.get(key)


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
            self.server.last = time.time()   # an open desk page asks every few seconds: it keeps the server up
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
        srv = self.server
        if path in ("/", "/index.html"):
            page = (HERE / "static" / "index.html").read_text(encoding="utf-8").replace("{{TOKEN}}", srv.token) \
                .replace("{{HOME}}", srv.own_key or "")
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8", {"Content-Security-Policy": CSP})
        if path.startswith("/static/") and path[8:] in STATIC:
            return self._send(200, (HERE / "static" / path[8:]).read_bytes(), STATIC[path[8:]])
        if path == "/api/projects":
            return self._projects()
        m = re.fullmatch(r"/api/p/([^/]+)/(data|stage|status|gate/([A-Za-z0-9_-]{1,24}))", path)
        if m:
            key = unquote(m.group(1))
            project = srv.project_of(key)
            if project is None:
                return self._error(404, f"no project {key!r} under this desk's roots")
            what = m.group(2)
            if what == "data":
                return self._data(project, key)
            if what == "status":   # with this round's page: the console notices a new page the agent sent
                pages = review.gate_pages(project)
                return self._json(dict(F.listening(project), project=project.name, key=key, round=pages[-1].stem[5:] if pages else None))
            if what == "stage":
                return self._stage(project, key)
            lang = (parse_qs(urlsplit(self.path).query).get("lang") or [None])[0]
            return self._gate(project, key, m.group(3), lang if lang in ("zh", "en") else None)
        if path.startswith("/f/"):
            key, _, rel = path[3:].partition("/")
            project = srv.project_of(unquote(key))
            if project is None:
                return self._error(404, "no such project")
            return self._file(project, rel)
        # the desk's first addresses: the project it was started for
        if srv.project and path == "/api/data":
            try:
                data = reader.read_project(srv.project)
            except Exception as e:   # a reader bug must not take the desk down; the page says what happened
                return self._error(500, f"could not read the project: {type(e).__name__}: {e}")
            return self._json(data)
        if srv.project and path == "/api/status":
            return self._json(dict(F.listening(srv.project), project=srv.project.name))
        if srv.project and path.startswith("/p/"):
            return self._file(srv.project, path[3:])
        self._error(404, "not found")

    def _projects(self):
        try:
            rec = self.server.listing()
        except Exception as e:
            return self._error(500, f"could not list the projects: {type(e).__name__}: {e}")
        rows = []
        for r in rec["projects"]:
            r = dict(r)
            try:
                gid, gate = gate_now(r["path"]) if not r.get("error") else (None, None)
                r["picture"] = picture_of(r["path"], r, gate) if not r.get("error") else None
                r["ask"] = ask_of(r, gid, gate)
            except Exception as e:   # one project's trouble stays in its card
                r["picture"], r["ask"] = None, None
                r["error"] = r.get("error") or f"{type(e).__name__}: {e}"
            if r["picture"]:
                r["picture"]["href"] = link(r["key"])(r["picture"]["path"])
            if not r.get("error"):
                r["title"] = film_title(r["path"], r.get("title"))
            rows.append(r)
        rank = lambda r: (0 if r.get("state") == "waiting_person" else 2 if r.get("state") == "delivered" else 1,   # noqa: E731
                          -float((r.get("last_activity") or {}).get("t") or 0), r.get("name") or "")
        rows.sort(key=rank)
        self._json({"version": 1, "home": self.server.own_key, "roots": rec["roots"], "count": len(rows),
                    "waiting": sum(1 for r in rows if r.get("state") == "waiting_person"), "projects": rows})

    def _data(self, project, key):
        try:
            data = reader.read_project(project)
        except Exception as e:
            return self._error(500, f"could not read the project: {type(e).__name__}: {e}")
        try:
            import status as S
            data["status"] = S.collect(project)
        except (Exception, SystemExit) as e:   # the page shows the rest without it
            data["status"] = None
            data["warnings"].append(f"bin/vh status: {type(e).__name__}: {e}")
        data["key"], data["home"], data["pid"] = key, key == self.server.own_key, pid_of(project)
        data["only"] = self.server.only
        data["current"] = data["rounds"][-1]["id"] if data["rounds"] else None
        data["project"]["title"] = film_title(project, data["project"].get("title"))
        # this round is open until its stop is settled (passed or skipped): its decisions go with a submission, as before
        cur = next((x for x in (data.get("status") or {}).get("stations") or [] if data["current"] in (x.get("pages") or [])), None)
        data["round_open"] = bool(data["current"]) and not (cur and cur.get("state") in ("done", "skipped"))
        data["studio"] = studio_extras(project, data)
        return self._json(data)

    def _gate(self, project, key, gid, lang=None):
        try:
            page = review.page_for(project, gid, link=link(key), live=True, lang=lang)
            pages = review.gate_pages(project)
            page.past = not pages or pages[-1].stem[5:] != page.gate
            body = page.body()
        except (ValueError, OSError) as e:
            return self._error(404, str(e))
        except (AttributeError, KeyError, TypeError) as e:
            return self._error(500, f"gate-{gid}.json: {type(e).__name__}: {e}")
        cur = pages[-1].stem[5:] if pages else None
        cards = "".join(page.decision(i + 1, d) for i, d in enumerate(page.d["decisions"]))   # the right column's 要你定, compact
        self._json({"version": 1, "gate": page.gate, "current": page.gate == cur, "this_round": cur, "title": page.title(),
                    "lang": page.lang, "takeall": page.take_all(), "html": body, "errors": page.errors, "warnings": page.warnings,
                    "summary": page.d["summary"], "cards": cards, "marks": page.marks(), "not_reviewed": page.d["not_reviewed"],
                    "decisions": [{"id": d["id"], "question": d["question"], "recommend": d["recommend"],
                                   "options": [o["id"] for o in d["options"]]} for d in page.d["decisions"]]})

    def _stage(self, project, key):
        """The project's picture when no gate waits: its film (bin/vh status's), else the newest draft or animatic, as the
        gate view's player with the ruler of the project's outline and shots; else the newest picture."""
        film = None
        try:
            import status as S
            film = S.collect(project, light=True)["media"]["film"]
        except (Exception, SystemExit):
            pass
        film = film or _newest(project, [f"out/{n}{e}" for n in ("draft*", "final*", "animatic*") for e in VID])
        if film and _inside(project, film):
            try:
                html = review.stage_for(project, film, link(key))
            except (ValueError, OSError, AttributeError, KeyError, TypeError) as e:
                return self._error(500, f"the film's player: {type(e).__name__}: {e}")
            return self._json({"version": 1, "kind": "video", "path": film, "html": html})
        pic = _newest(project, [f"out/check/*{e}" for e in IMG] + [f"out/review/*{e}" for e in IMG] + [f"out/frames/*{e}" for e in IMG])
        if pic:
            return self._json({"version": 1, "kind": "image", "path": pic, "href": link(key)(pic)})
        return self._json({"version": 1, "kind": None})

    def _resolve(self, project, rel):
        """A file inside the project, or None: no '..', no hidden parts (.env, .git, .listening), no *.env, checked
        on the name asked for and on the file it resolves to (a symlink to .env is refused too), ignoring case."""
        rel = unquote(rel)
        parts = [p for p in rel.split("/") if p not in ("", ".")]
        hidden = lambda ps: any(p == ".." or p.startswith(".") or p.lower().endswith(".env") for p in ps)   # noqa: E731
        if not parts or "\x00" in rel or hidden(parts):
            return None
        root = os.path.realpath(str(project))
        f = os.path.realpath(os.path.join(root, *parts))
        if os.path.commonpath([f, root]) != root or not os.path.isfile(f) or hidden(os.path.relpath(f, root).split(os.sep)):
            return None
        return f

    def _file(self, project, rel):
        f = self._resolve(project, rel)
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
        path = urlsplit(self.path).path
        m = re.fullmatch(r"/api/p/([^/]+)/feedback", path)
        if m:
            project = self.server.project_of(unquote(m.group(1)))
            if project is None:
                return self._error(404, "no such project")
        elif path == "/api/feedback" and self.server.project:
            project = self.server.project
        else:
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
            raw = json.loads(body.decode("utf-8"))
            if m:   # the console's address: the page says which folder it was opened on, and it has to be this one
                if not isinstance(raw, dict) or raw.pop("pid", None) != pid_of(project):
                    return self._error(409, "this address names another project now than the page was opened on: reload it")
            fb = F.validate(project, raw)
        except (ValueError, TypeError, AttributeError, RecursionError) as e:   # UnicodeDecodeError is a ValueError
            return self._error(400, str(e) or type(e).__name__)
        saved = F.save(project, fb)
        sys.stderr.write(f"desk: feedback saved → {saved} (also in REVIEW.md)\n")
        sys.stderr.flush()
        self._json(dict(F.listening(project), saved=os.path.relpath(saved, project)))


# ---------- start: once per project, or one console ----------

def _info_path(project, roots=()):
    """Where a running desk says so: out/review/.desk.json in its project; a console's in the temp folder, one per user and
    set of roots (a console over other folders is another console)."""
    if project:
        return Path(project) / "out" / "review" / ".desk.json"
    d = _own_dir()
    if d is None:
        return None
    which = hashlib.sha1("\n".join(sorted(os.path.realpath(r) for r in roots)).encode("utf-8")).hexdigest()[:10]
    return d / f"console-{which}.json"


def _own_dir():
    """This user's folder for consoles in the temp folder (on a Linux /tmp shared with other users too): made 0700, and
    used only while it is a folder, not a link, owned by this user and closed to others; None otherwise."""
    uid = os.getuid() if hasattr(os, "getuid") else None
    d = Path(tempfile.gettempdir()) / f"ovh-desk-{uid if uid is not None else os.environ.get('USERNAME', 'user')}"
    try:
        d.mkdir(mode=0o700, exist_ok=True)
        st = os.lstat(d)
    except OSError:
        return None
    import stat as _st
    if not _st.S_ISDIR(st.st_mode) or (uid is not None and st.st_uid != uid) or st.st_mode & 0o077:
        return None
    return d


def running(project=None, roots=None):
    """The URL of a desk already serving this project (out/review/.desk.json names this very folder, its process is
    alive and its port answers), else None. A copied project carries the original's file; the path tells them apart.
    project None: a console already running with the same roots."""
    info_p = _info_path(project, roots or ())
    if info_p is None:
        return None
    try:
        if hasattr(os, "getuid") and os.lstat(info_p).st_uid != os.getuid():   # someone else's file says nothing about ours
            return None
        info = json.loads(info_p.read_text())
        if project is not None and info.get("project") != os.path.realpath(str(project)):
            return None
        if project is None and sorted(info.get("roots") or []) != sorted(os.path.realpath(r) for r in roots or []):
            return None
        os.kill(int(info["pid"]), 0)
        with socket.create_connection(("127.0.0.1", int(info["port"])), timeout=1):
            pass
    except (OSError, ValueError, KeyError, TypeError):   # PermissionError too: a process this user cannot signal is not its desk
        return None
    return info.get("url")


def serve(project=None, port=None, idle=None, roots=(), only=False):
    """Serve until stopped, or (idle: seconds) until nobody has asked anything for that long. project None: the console.
    port None: the first free of 8780–8799; 0: any free port. only: this project and nothing else under the roots (the desk
    bin/vh gate starts). → exit code."""
    project = Path(project).resolve() if project else None
    url = running(project, roots)
    if url:
        what = project.name if project else "the console"
        print(f"desk: already serving {what} at {url} (stop that process to start another)", flush=True)
        return 0
    srv, last = None, None
    for p in ([port] if port is not None else DEFAULT_PORTS):
        try:
            srv = Desk(p, project, roots, only)
            break
        except OSError as e:
            last = e
    if srv is None:
        print(f"desk: no free port ({last}); pick one with --port N", file=sys.stderr)
        return 2
    info_p = _info_path(project, roots)
    info = {"pid": os.getpid(), "port": srv.port, "url": srv.url, "started": datetime.datetime.now().isoformat(timespec="seconds")}
    if project:
        info["project"] = os.path.realpath(str(project))
    else:
        info["roots"] = [os.path.realpath(r) for r in roots]
    try:   # without it this desk still serves; a second start just cannot find it
        if info_p is None:
            raise OSError("no folder of this user's own in the temp folder")
        info_p.parent.mkdir(parents=True, exist_ok=True)
        info_p.write_text(json.dumps(info))
    except OSError as e:
        print(f"desk: {e}: a second start will not find this one", file=sys.stderr)
        info_p = None

    def stop(signum, _frame):   # the info file goes (finally, below); the exit status says what stopped it: 128 + the signal
        raise SystemExit(128 + signum)
    for s in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, stop)
    if idle:   # bin/vh gate starts the desk detached: it goes by itself once nobody uses it

        def watch():
            while True:
                time.sleep(max(0.2, min(60.0, idle / 10)))
                if time.time() - srv.last > idle:
                    print(f"desk: no request for {idle:g} s, stopped", flush=True)
                    srv.shutdown()
                    return
        threading.Thread(target=watch, daemon=True).start()
    what = (f"{project.name}" + (" only" if only else "")) if project else "console (every project)"
    print(f"desk: {srv.url}  ·  {what}  (Ctrl-C stops it" + (f"; it stops by itself after {idle:g} s without a request)" if idle else ")"), flush=True)
    code = 0
    try:
        srv.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        code = 130
    finally:
        srv.server_close()
        try:
            if info_p is not None and json.loads(info_p.read_text()).get("pid") == os.getpid():
                info_p.unlink()
        except (OSError, ValueError):
            pass
    return code


if __name__ == "__main__":
    sys.exit(serve(sys.argv[1] if len(sys.argv) > 1 else None, int(sys.argv[2]) if len(sys.argv) > 2 else None))
