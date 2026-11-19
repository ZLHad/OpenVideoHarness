"""Review desk and console, server: on 127.0.0.1 only, stdlib only.

Started for a project (bin/vh desk <project>, or bin/vh gate on the desk channel) the page opens on that project; started
without one (bin/vh desk) it opens on the console's home, every project bin/vh projects finds. Either way the page reaches
every project under the roots (bin/vh projects': $OVH_PROJECTS, <repo>/projects, each --root), and the project it was
started for wherever that is. The project files and bin/vh are the truth: every answer is read fresh from them, and the page
keeps nothing of its own but the reviewer's draft (in the browser) until it is submitted.

  GET  /[?c=<code>&w=<window>]    the page (static/index.html, and the project it opens on). A GET changes nothing and
                                  gives nothing: the page's own script trades the code for the token (POST /api/claim)
  POST /api/claim                 {c}: a one-time code the desk made for the window it opened (or printed for
                                  --print-address) → {token}, once; the code is gone after, and it lived seconds
  GET  /api/presence?token=&w=    Server-Sent Events while a page with the token is open: the desk knows its window is
                                  there (and when it closed), and sends it where to go ({go: "/p/<key>…"})
  POST /api/open                  {at, renew}: show Studio's window (raise it, or make the one window, or a tab of the
                                  default browser when there is no Chromium-family browser) at that place → {opened, how,
                                  why}; no token needed, nothing secret back; twenty a minute. renew: the window whose
                                  page could not trade its code (Desk.renew): a new token, and a fresh window, twice a run
  GET  /api/hello                 does the page hold this run's token? 403 {reopen} when not
  GET  /static/<file>             ui.css and ui.js (the gate view's: the static review page inlines the same two files),
                                  studio.css and studio.js (the console's shell and the cut), modules.css and modules.js
                                  (the other modules), core.js (the words and helpers a static page shares)
  GET  /api/projects              every project: bin/vh projects' rows, each with its key, a picture, and what it waits for
  GET  /api/p/<key>/data          one project, read fresh: reader.read_project, plus bin/vh status (status), its key and
                                  what the cut module lays out (studio: the resolved timeline, thumbnails, peaks, findings),
                                  and what the other modules read besides (mods: loudness, voices, lifts, covers, the asset
                                  ledger, references and their transcripts)
  GET  /api/p/<key>/gate/<id>     a gate page as the gate view's markup (tools/review.py: the static page's markup)
  GET  /api/p/<key>/stage         the project's film, or newest draft, as the same player markup, with its ruler
  GET  /api/p/<key>/status        is an agent waiting for this project's feedback (bin/vh desk wait)?
  POST /api/p/<key>/feedback      a submission: checked, saved to out/review/feedback/, copied into REVIEW.md
  GET  /f/<key>/<path>            a file inside that project (HTTP Range, so video and audio can seek); nothing outside
                                  it, no hidden files
  GET  /v/<key>/<path>            that file on a page of its own with a slim bar (its name): text and markdown as text, a
                                  picture, a player, a page in a frame, else a sentence; Studio's app opens new-page links here
  GET  /api/p/<key>/agents        the column's agents (installed or how to install), the project's conversations, its lock
  GET  /api/p/<key>/agent/<id>/events?token=   one conversation's events, as Server-Sent Events (agents.py)
  POST /api/p/<key>/agent/new · install · <id>/say · answer · stop · mode · config   the person's actions in the agent column:
                                  the typed text, an answer among the agent's own options, stop (waiting requests cancelled
                                  first), a setting among those the agent offered
  GET  /api/space/agents · /api/space/agent/<id>/events · POST /api/space/agent/…   the same, for the space's column: a film
                                  begun with a sentence, the agent working in the workspace (the clone), its record beside
                                  the console's info file until bin/vh new in it makes the film; then it is that film's
                                  (agents.Manager.adopt) and these addresses still reach it
  The desk's first addresses stay, for the project it was started for: /api/data (reader.read_project alone, as bin/vh desk
  data prints it), /api/status, /api/feedback, /p/<path>.

Only requests whose Host is this server's own address are answered (no DNS rebinding); a POST also needs this run's token,
a JSON body and, when the browser sends one, a same-origin Origin. So another web page open in the same browser can neither
read a project nor submit feedback in the reviewer's name.

The token is the only door. Nothing that holds it, or a way to it, is printed or written anywhere: not in the address
a desk prints, not in .desk.json or a log, not in bin/vh gate's message or --json. The desk makes Studio's window itself
(window.py): a Chromium-family browser named outright, with a profile of its own and --app (no address bar, no tabs, no
extensions, nobody's session), at an address carrying a one-time code that lives a minute. The page's script trades it
for the token (POST /api/claim) and keeps the token in its origin's storage (one port's; a cookie would reach every port
of 127.0.0.1); the code is spent then, so the copy that stays in the browser's command line (ps shows it) opens nothing.
A GET changes nothing: a browser may fetch an address more than once (a prefetch, an extension, the address handed to a
headless Chrome another tool left running, as happened on 2026-11-16), and none of that may cost the person their page.
The window counts as open only when its page connects back (GET /api/presence); else the desk tries once more, then a
tab of the default browser, and says so. POST /api/open, which bin/vh studio, the launcher icon, bin/vh gate and a page
that can only look call, needs no token: it shows the window and answers whether it did, nothing else. So a command an
agent runs in the project, which can read every file there, reach 127.0.0.1 and read the process list, finds nothing to
act with: the most it can do is bring Studio's window to the front. --print-address (a browser on another machine)
writes an address with a code that lives ten minutes and opens one page, once, to the terminal alone (/dev/tty: not
stdout, a log or --json), and is refused where there is none, as in an agent's shell. Which process sent a request on
the loopback the server cannot tell (a peer-port lookup is beaten by a double fork or a half-closed socket), so it does
not try.

What this is, said plainly: a guardrail, not a wall. It keeps an agent from approving its own requests by ordinary means:
reading files, logs and command output, calling the server. It does not stop a program of the same user that sets out to
dig: one that reads the window's profile (the token is in its storage), races the window for its code in the second
between the window's start and its page's claim (ps shows the code; the window whose page then finds its code spent
asks for renew, and the console changes the token and replaces the window, twice a run, never while that window's page
is connected; a program that also holds the window's presence stream blocks that), makes itself a terminal to read
--print-address (script(1) does), or synthesizes input. Against those the boundary is the agent's own mode and sandbox.
"""
import datetime, hashlib, html, http.server, json, mimetypes, os, re, secrets, signal, socket, socketserver, sys, tempfile, threading, time
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlsplit

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import feedback as F   # noqa: E402
import revisions as RV   # noqa: E402
import reader          # noqa: E402
import review          # noqa: E402  (tools/review.py: the gate view, the same markup as the static page)
import agents as A     # noqa: E402  (the agents the column talks to: one adapter process a kind, a session a conversation)

STATIC = {"ui.css": "text/css; charset=utf-8", "ui.js": "text/javascript; charset=utf-8",
          "studio.css": "text/css; charset=utf-8", "studio.js": "text/javascript; charset=utf-8",
          "modules.css": "text/css; charset=utf-8", "modules.js": "text/javascript; charset=utf-8", "core.js": "text/javascript; charset=utf-8",
          "agent.css": "text/css; charset=utf-8", "agent.js": "text/javascript; charset=utf-8",
          "reader.css": "text/css; charset=utf-8", "reader.js": "text/javascript; charset=utf-8"}
# GET /v/<key>/<path>: a project file on a page of its own (Studio's app opens the console's new-page links there)
VIEW = {"image": {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp"}, "video": {".mp4", ".mov", ".m4v", ".webm"},
        "audio": {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".oga", ".flac", ".opus"}, "page": {".html", ".htm"}, "markdown": {".md", ".markdown"},
        "text": {".txt", ".json", ".jsonl", ".csv", ".tsv", ".srt", ".vtt", ".ass", ".yaml", ".yml", ".toml", ".log", ".py", ".js", ".mjs",
                 ".ts", ".css", ".sh", ".tex", ".bib", ".xml", ".ini", ".cfg", ".lrc"}}
VIEW_TEXT_MAX = 2 << 20   # bytes of text shown on the page; longer: said so
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
        imgs = [p for p in (_inside(project, a.get("path")) for a in assets) if p and p.lower().endswith(IMG)]
        for p in [p for p in imgs if "sheet" not in Path(p).name.lower()]:   # a picture of the film, not a contact sheet
            return {"path": p, "kind": "image", "from": "gate"}
        for s in gate.get("segments") or []:
            for sh in (s.get("shots") or []) if isinstance(s, dict) else []:
                p = _inside(project, sh.get("frame")) if isinstance(sh, dict) else None
                if p:
                    return {"path": p, "kind": "image", "from": "gate"}
        if imgs:   # only a contact sheet: the cover or the film come first, the sheet when there is nothing else
            sheet = imgs[0]
            pic = picture_of(project, dict(row, state=None), None)
            return pic if pic and pic.get("from") != "sheet" else {"path": sheet, "kind": "image", "from": "gate"}
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


def first_words(project, n=24):
    """What the person first said in the conversation that made this film (begun on Studio's space), shortened; or None."""
    d = Path(project) / ".ovh" / "agents"
    try:
        heads = sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return None
    for h in heads:
        j = _load(h)
        if not (isinstance(j, dict) and j.get("space") and j.get("placed")):
            continue
        try:
            with open(h.with_suffix(".jsonl"), encoding="utf-8") as f:
                for line in f:
                    e = json.loads(line)
                    if isinstance(e, dict) and e.get("type") == "user" and isinstance(e.get("text"), str) and e["text"].strip():
                        x = " ".join(e["text"].split())
                        if len(x) <= n:
                            return x
                        cut = max(x.rfind(c, 0, n) for c in "，,。；;：: ")   # at a pause in the sentence when there is one past its middle
                        return (x[:cut] if cut > n // 2 else x[:n]).rstrip("，,。；;：: ") + "…"
        except (OSError, ValueError):
            continue
    return None


def film_title(project, title):
    """The film's name: BRIEF's (bin/vh status's title), else the newest gate page's title up to its stop's name
    ("片名 · 关卡 ③ 初版" → "片名"), else what the person first said when they asked for it on the space (shortened), else
    the folder's name."""
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
    return first_words(project) or title or name


def ask_of(row, gid, gate):
    """What a waiting project asks, in a line: the round's first question, else its summary. None when it waits for no one."""
    if row.get("state") != "waiting_person" or not gate:
        return None
    decs = [d for d in gate.get("decisions") or [] if isinstance(d, dict)]
    q = next((d.get("question") for d in decs if isinstance(d.get("question"), str) and d.get("question").strip()), None)
    s = gate.get("summary") if isinstance(gate.get("summary"), str) else ""
    qs = [d["question"].strip()[:80] for d in decs if isinstance(d.get("question"), str) and d["question"].strip()][:4]
    return {"gate": gid, "title": review.gate_title(gid, "zh"), "title_en": review.gate_title(gid, "en"),
            "question": (q or s or "").strip()[:160], "questions": qs, "summary": s.strip()[:160], "decisions": len(decs)}


def _load(p):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


_SOUND, _SOUND_LOCK = {}, threading.Lock()   # (real path, size, mtime) → whether that film has a sound track


def film_sound(project, rel):
    """Whether a film of the project has a sound track: True, False, or None when it cannot be told (no ffprobe, a file it
    cannot read). ffprobe looks once a file, as long as its size and time stay the same (a page's every refresh asks)."""
    try:
        p = Path(os.path.realpath(os.path.join(str(project), rel)))
        s = p.stat()
    except (OSError, TypeError, ValueError):
        return None
    key = (str(p), s.st_size, s.st_mtime_ns)
    with _SOUND_LOCK:
        if key in _SOUND:
            return _SOUND[key]
    try:
        import subprocess
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(p)],
                           capture_output=True, text=True, timeout=15)
        got = None if r.returncode else "audio" in r.stdout.split()
    except (OSError, subprocess.SubprocessError):
        got = None
    with _SOUND_LOCK:
        if len(_SOUND) > 2000:
            _SOUND.clear()
        _SOUND[key] = got
    return got


SILENT = re.compile(r"无声片|无声|不要声音|不带音轨|silent film|\bsilent\b|no sound|no audio", re.I)


def silent_by_brief(project):
    """The BRIEF asks for a film without sound (无声片, silent, no audio): its silent cut is the film, not a draft without sound."""
    try:
        return bool(SILENT.search(re.sub(r"<!--.*?-->", "", (Path(project) / "BRIEF.md").read_text(encoding="utf-8"), flags=re.S)))
    except OSError:
        return False


def _mtime(project, rel):
    try:
        return os.stat(os.path.join(str(project), rel)).st_mtime
    except (OSError, TypeError):
        return 0.0


def studio_extras(project, data):
    """What the cut module lays out, from what bin/vh has already made (nothing is run here): the resolved timeline (bin/vh
    timeline --resolved: shots, chapters, narration, captions, beats), the film's thumbnails and waveform peaks when bin/vh
    thumbs and peaks have made them, and the findings of its latest bin/vh check, each with its time. A part that is not there
    is None, and the page names the command that makes it."""
    st = data.get("status") or {}
    media = st.get("media") or {}
    out = {"timeline": None, "thumbs": None, "peaks": None, "findings": [], "check": None, "film": None, "film_missing": None, "sheet": None,
           "film_sound": None, "film_instead": None}
    # the film: this round's when its stop is the cut's (gate ③, E4, E5), else the one bin/vh status names, else its proxy
    named, want = [], []
    rounds = data.get("rounds") or []
    if rounds and re.match(r"(3|E4|E5)", str(rounds[-1].get("id", ""))):
        g = rounds[-1].get("data") or {}
        if isinstance(g.get("film"), str):
            named.append(g["film"])
        named += [a.get("path") for a in g.get("assets") or [] if isinstance(a, dict) and str(a.get("path", "")).lower().endswith(VID)]
    want += [media.get("film"), media.get("proxy")]
    clean = lambda xs: [w for w in xs if isinstance(w, str) and w.strip() and not re.match(r"(?i)https?://", w)]   # noqa: E731
    named, want = clean(named), clean(want)
    out["film"] = next((w for w in named + want if _inside(project, w)), None)
    if not out["film"] and named + want:
        out["film_missing"] = (named + want)[0]
    elif out["film"] and not any(_inside(project, w) for w in named) and film_sound(project, out["film"]) is False and not silent_by_brief(project):
        # the stop names no film and bin/vh status's has no sound (and the BRIEF does not want a silent film): a cut of the
        # film that has, at least as new as that one (the storyboard's animatic, a gate page's film or animatic, newest page
        # first), plays instead; what describes status's film (thumbs, peaks, findings, its version) is left out below.
        # bin/vh status itself is left as it is
        more = [(data.get("shots") or {}).get("video") if isinstance(data.get("shots"), dict) else None]
        for r in reversed(rounds):
            g = r.get("data") if isinstance(r, dict) and isinstance(r.get("data"), dict) else {}
            more += [g.get("film"), g.get("animatic")]
        more = [w for w in clean(more) if w.lower().endswith(VID) and _inside(project, w) and w not in want]
        newest = _mtime(project, out["film"])
        pick = next((w for w in dict.fromkeys(more) if _mtime(project, w) >= newest and film_sound(project, w)), None)
        if pick:
            out["film_instead"], out["film"] = out["film"], pick
    if out["film"]:
        out["film_sound"] = film_sound(project, out["film"])
    out["sheet"] = _newest(project, [f"out/check/*sheet*{e}" for e in IMG] + [f"out/check/*/*sheet*{e}" for e in IMG])   # a picture when there is no film
    try:
        import resolved
        out["timeline"] = resolved.document(Path(project), data.get("lang"))
        for sh in out["timeline"].get("shots") or []:   # a key frame that is not there is no key frame (and no 404)
            if isinstance(sh, dict) and sh.get("frame") and not re.match(r"(?i)https?://", str(sh["frame"])) and not _inside(project, sh["frame"]):
                sh["frame"] = None
    except (Exception, SystemExit) as e:   # one part's trouble is said, the rest is shown
        data["warnings"].append(f"bin/vh timeline --resolved: {type(e).__name__}: {e}")
    if out["film_instead"]:   # status's thumbs, peaks and check are of the film that does not play
        return out
    if media.get("thumbs"):
        t = _json_in(project, media["thumbs"])[0]   # inside the project only, as /f/ serves
        if isinstance(t, dict) and all(_inside(project, sh.get("file")) for sh in t.get("sheets") or [] if isinstance(sh, dict)):
            out["thumbs"] = {k: t.get(k) for k in ("duration", "tile", "shot", "sheets", "tiles")}
            out["thumbs"]["shots"] = [x for x in t.get("shots") or [] if isinstance(x, dict) and _inside(project, x.get("file"))]
    if media.get("peaks"):
        pk = _json_in(project, media["peaks"])[0]
        if isinstance(pk, dict) and isinstance(pk.get("peaks"), list):
            out["peaks"] = {"duration": pk.get("duration"), "peaks": pk["peaks"]}
    chk = st.get("check")
    if isinstance(chk, dict) and chk.get("record"):
        rec = _json_in(project, chk["record"])[0]
        if isinstance(rec, dict):
            out["check"] = {k: chk.get(k) for k in ("verdict", "video", "at", "stale", "counts")}
            out["findings"] = [{k: f.get(k) for k in ("kind", "severity", "message", "t", "t1")} for f in rec.get("findings") or []
                               if isinstance(f, dict) and f.get("severity") in ("fail", "warn")][:200]
    return out


SYSTEM_FONTS = re.compile(r"^(/System/Library/.*Font|/Library/Fonts/|~/Library/Fonts/|/usr/share/fonts/|[A-Za-z]:[\\/]Windows[\\/]Fonts[\\/])", re.I)


def _json_in(project, rel):
    """(the JSON of a file of the project, its path), read only when it is a file inside the project: a link that leads out
    is not followed, as /f/ does not serve one. (None, None) for anything else; raises nothing."""
    r = _inside(project, rel) if isinstance(rel, str) else None
    return (_load(Path(project) / r) if r else None), r


def _not_out(project, name, rel):
    """A file of a fixed name that is there but leads out of the project (a link): said, not read."""
    if not rel and os.path.lexists(Path(project) / name):
        raise ValueError(f"{name} is not a file inside the project (a link that leads out, or missing): not read")


def _texts(x):
    """A list of short texts from a list, or from one text written in place of one (a ledger's used_by by hand)."""
    if isinstance(x, str):
        return [x] if x.strip() else []
    return [str(v) for v in x if isinstance(v, (str, int, float)) and not isinstance(v, bool)] if isinstance(x, list) else []


def _list(x, what):
    if x is None:
        return []
    if not isinstance(x, list):
        raise ValueError(f"{what} is not a list")
    return x


def module_extras(project, data):
    """What the other modules lay out, from files bin/vh has already made (nothing is run here): the sound module's readouts
    (the latest bin/vh check's loudness and its silences, bin/vh pace's speech rates from the narration's timeline), its
    voice audition (bin/vh voices audition's audition.json) and the music's candidate lifts (bin/vh beats); the delivery
    module's covers, caption files and every finding of the check; the material module's asset ledger (bin/vh assets),
    references (bin/vh ref) and long-video transcripts (bin/vh ref digest). A part that is not there is empty, and the
    page names the command that makes it. Each part is read on its own: one that does not read is empty and `errors` names
    its file and why, while the others show. Only files inside the project are read (a link that leads out is not)."""
    project = Path(project)
    out = {"loudness": None, "silences": None, "checks": [], "pace": None, "voice": None, "audition": None, "lifts": [], "covers": [],
           "subs": [], "assets": None, "assets_notes": None, "refs": [], "digests": [], "errors": {}}
    where = {}

    def part(name, fn):
        try:
            fn()
        except Exception as e:   # one file that does not read never empties the other parts
            out["errors"][name] = f"{where.get(name) or name} · {type(e).__name__}: {e}"

    def narration():
        tl = (data.get("studio") or {}).get("timeline")
        narr = ((tl.get("sources") or {}).get("narration") or {}).get("path") if isinstance(tl, dict) else None
        ntl, where["pace"] = _json_in(project, narr)
        if not isinstance(ntl, dict):
            return
        if isinstance(ntl.get("voice"), str):
            out["voice"] = ntl["voice"]   # the voice the narration was read in (bin/vh tts)
        pc = ntl.get("pace")
        if isinstance(pc, dict):   # bin/vh pace's numbers: voice only, every pause of 0.12 s or more inside a line left out
            rates = pc.get("rates") if isinstance(pc.get("rates"), dict) else {}
            out["pace"] = {"reference": pc.get("reference"), "unit": pc.get("unit"), "speech": rates.get("speech"), "with_pauses": rates.get("with_pauses"),
                           "lines": [{k: x.get(k) for k in ("id", "units", "pace", "after", "tempo", "note")} for x in _list(pc.get("lines"), "pace.lines") if isinstance(x, dict)][:2000]}

    def check():
        chk = (data.get("status") or {}).get("check")
        rec, where["check"] = _json_in(project, chk.get("record")) if isinstance(chk, dict) else (None, None)
        if not isinstance(rec, dict):
            return
        F_ = [f for f in _list(rec.get("findings"), "findings") if isinstance(f, dict)]
        out["checks"] = [{k: f.get(k) for k in ("kind", "severity", "message", "t", "t1")} for f in F_][:300]
        ld = next((f for f in F_ if f.get("kind") == "check.loudness"), None)
        if ld:
            ev = ld.get("evidence") if isinstance(ld.get("evidence"), dict) else {}
            out["loudness"] = {k: ev.get(k) for k in ("integrated", "true_peak", "lra", "target")}
            out["loudness"]["severity"] = ld.get("severity")
        out["silences"] = sum(1 for f in F_ if "silence" in str(f.get("kind", "")) or str(f.get("message", "")).startswith("silence"))

    def audition():   # where bin/vh voices audition writes (audition-<text>/ beside the text, or --out): a few places, not a walk of out/
        cands = []
        for pat in ("audition.json", "audition-*/audition.json", "audio/audition.json", "audio/*/audition.json", "out/audition.json", "out/audition-*/audition.json"):
            for f in sorted(project.glob(pat)):
                r = _inside(project, f.relative_to(project).as_posix())
                if r:
                    cands.append((os.stat(project / r).st_mtime, r))
        if not cands:
            return
        r = max(cands)[1]
        a, where["audition"] = _json_in(project, r)
        if not isinstance(a, dict):
            raise ValueError("not a JSON object")
        rows, base = [], os.path.dirname(r)
        for v in _list(a.get("voices"), "voices"):
            if isinstance(v, dict) and v.get("voice"):
                f = v.get("file") if isinstance(v.get("file"), str) else ""
                take = _inside(project, os.path.relpath(os.path.join(os.path.realpath(project / base), f), os.path.realpath(project))) if f else None
                rows.append({"voice": str(v.get("voice")), "file": take, "duration": v.get("duration"), "pitch_hz": v.get("pitch_hz"),
                             "speech_rate": v.get("speech_rate"), "misread": v.get("misread") if isinstance(v.get("misread"), list) else None,
                             "error": v.get("error")})
        out["audition"] = {"file": r, "provider": a.get("provider"), "unit": a.get("unit"), "text": a.get("text"), "voices": rows}

    def lifts():
        cands = [r for f in sorted((project / "audio").glob("*.beats.json")) if (r := _inside(project, f.relative_to(project).as_posix()))] \
            if (project / "audio").is_dir() else []
        if not cands:
            return
        b, where["lifts"] = _json_in(project, max(cands, key=lambda r: os.stat(project / r).st_mtime))
        if isinstance(b, dict):
            out["lifts"] = [{k: x.get(k) for k in ("t", "strength", "depth_db", "rise_db", "on")} for x in _list(b.get("lifts"), "lifts") if isinstance(x, dict)][:40]

    def covers():
        pk = data.get("packaging") or {}
        where["covers"] = "PACKAGING.md"
        rows = [x for x in _list(pk.get("covers"), "covers") if isinstance(x, dict)]
        folders = [f.relative_to(project).as_posix() for d in ("out/covers", "out/final/covers") if (project / d).is_dir()
                   for f in sorted((project / d).iterdir()) if f.suffix.lower() in IMG]
        seen = set()
        for c in [x.get("image") for x in rows] + folders:   # PACKAGING.md's covers first, then the cover folders'
            r = _inside(project, c)
            if r and r not in seen:
                seen.add(r)
                ratio = review.image_ratio(project / r)
                row = next((x for x in rows if x.get("image") == c), {})
                out["covers"].append({"path": r, "ratio": round(ratio, 3) if ratio else None, "id": row.get("id", ""), "text": row.get("text", "")})

    def subs():
        out["subs"] = [r for d in ("out/final", "out", "audio") if (project / d).is_dir() for f in sorted((project / d).glob("*.srt"))
                       if (r := _inside(project, f.relative_to(project).as_posix()))][:20]

    def notes_ledger():   # no assets/ledger.json: the table NOTES.md kept before bin/vh assets (templates/NOTES.md until 2026-10-26), read only
        r = _inside(project, "NOTES.md")
        if not r:
            return
        where["assets"] = r
        body = reader.section(reader.strip_comments((Path(project) / r).read_text(encoding="utf-8", errors="replace")), r"素材台账", r"^assets?\b", r"asset (ledger|log)")
        tb = reader.first_table(body, "文件", "file")
        rows = []
        for row in tb.rows if tb else []:
            f, s, li = (reader.plain(tb.get(row, *k)) for k in (("文件", "file"), ("来源", "source"), ("许可", "licen")))
            if f or s or li:
                if "{" not in f + s + li:   # the template's empty row, or one not filled in yet
                    link = bool(re.match(r"[A-Za-z][A-Za-z0-9+.-]*://", f))   # a link has no file to be there or not
                    path = bool(re.fullmatch(r"[\w./~-]+\.\w{1,5}", f.strip("` ")))   # one file by its path; "字体", "屏幕壁纸" or a list with * says what, not where
                    rows.append({"file": f, "source": s, "license": li, "there": bool(_inside(project, f.strip("` "))) if path and not link else None})
        if rows:
            out["assets_notes"] = {"file": r, "rows": rows[:200]}

    def assets():
        led, where["assets"] = _json_in(project, "assets/ledger.json")
        _not_out(project, "assets/ledger.json", where["assets"])
        if not isinstance(led, dict):
            notes_ledger()
            return
        rows = []
        for r in _list(led.get("assets"), "assets"):
            if not isinstance(r, dict) or r.get("removed"):
                continue
            lic, src = r.get("license") if isinstance(r.get("license"), dict) else {}, r.get("source") if isinstance(r.get("source"), dict) else {}
            raw = r.get("path") if isinstance(r.get("path"), str) else ""
            rel = _inside(project, raw)   # there, and inside; else a name in the project (missing now), or a path outside it (bin/vh assets add takes one)
            named = bool(raw) and not raw.startswith(("/", "~", "\\")) and not re.match(r"[A-Za-z][A-Za-z0-9+.-]*:", raw) and ".." not in re.split(r"[/\\]", raw)
            system = not rel and bool(SYSTEM_FONTS.match(raw.strip()))   # a font the system has (macOS, Windows, Linux): there, not "outside"
            rows.append({"id": str(r.get("id") or ""), "kind": r.get("kind"), "path": rel or (raw.strip() if named else None), "outside": "" if rel or named or system else raw,
                         "there": bool(rel) or system, "system": system,
                         "license": lic.get("class") if isinstance(lic.get("class"), str) else "unknown", "license_name": lic.get("name") or lic.get("spdx") or "",
                         "source": src.get("title") or src.get("url") or src.get("tool") or src.get("kind") or "", "url": src.get("url") or "",
                         "aigc": bool(r.get("aigc")), "used_by": _texts(r.get("used_by")), "note": r.get("note") or ""})
        out["assets"] = rows

    def refs():
        rf, where["refs"] = _json_in(project, "research/refs.json")
        _not_out(project, "research/refs.json", where["refs"])
        items = (rf.get("refs") or rf.get("assets") or []) if isinstance(rf, dict) else rf if isinstance(rf, list) else []
        for r in _list(items, "refs"):
            if isinstance(r, dict) and r.get("id"):
                src = r.get("source") if isinstance(r.get("source"), dict) else {}
                lic = r.get("license") if isinstance(r.get("license"), dict) else {}
                out["refs"].append({"id": str(r.get("id")), "kind": r.get("kind"), "title": src.get("title") or r.get("note") or str(r.get("id")),
                                    "url": src.get("url") or "", "author": src.get("author") or "", "license": lic.get("class") or "unknown",
                                    "path": _inside(project, r.get("path")), "note": r.get("note") or ""})

    def digests():
        d = project / "research" / "digest"
        for f in sorted(d.glob("*/transcript.md")) if d.is_dir() else []:
            r = _inside(project, f.relative_to(project).as_posix())
            if r:
                out["digests"].append({"id": f.parent.name, "path": r, "bytes": os.stat(project / r).st_size})

    for name, fn in (("pace", narration), ("check", check), ("audition", audition), ("lifts", lifts), ("covers", covers), ("subs", subs),
                     ("assets", assets), ("refs", refs), ("digests", digests)):
        part(name, fn)
    return out


def _drop_missing(project, d, key):
    """d[key] when it names a file of the project that is there (or a URL); else "", the name kept in d[key + "_missing"]:
    a page never asks for a file that is not there."""
    v = d.get(key) if isinstance(d, dict) else None
    if isinstance(v, str) and v and not re.match(r"(?i)https?://", v) and not _inside(project, v):
        d[key], d[key + "_missing"] = "", v


def project_data(project, parts=("studio", "mods")):
    """A project's data as the console reads it (GET /api/p/<key>/data, less the key): reader.read_project, bin/vh status,
    the folder's identity, this round and whether it is open, and the parts asked for, what the cut module lays out (studio)
    and what the other modules read (mods). A static review page asks for what its stop's modules need (tools/review.py).
    Raises what read_project raises; a part that cannot be read is null, the reason in warnings."""
    revision_stamp = RV.stamp(project)
    data = reader.read_project(project)
    try:
        import status as S
        data["status"] = S.collect(project)
    except (Exception, SystemExit) as e:   # the page shows the rest without it
        data["status"] = None
        data["warnings"].append(f"bin/vh status: {type(e).__name__}: {e}")
    data["pid"] = pid_of(project)
    data["revision_stamp"] = revision_stamp
    _drop_missing(project, data.get("shots"), "video")   # the storyboard's animatic, and the pictures the gate pages name
    for r in data.get("rounds") or []:
        g = r.get("data") if isinstance(r, dict) and isinstance(r.get("data"), dict) else {}
        for dec in g.get("decisions") or []:
            for o in (dec.get("options") or []) if isinstance(dec, dict) else []:
                _drop_missing(project, o, "frame")
        for seg in g.get("segments") or []:
            for sh in (seg.get("shots") or []) if isinstance(seg, dict) else []:
                _drop_missing(project, sh, "frame")
    data["current"] = data["rounds"][-1]["id"] if data["rounds"] else None
    data["project"]["title"] = film_title(project, data["project"].get("title"))
    # this round is open until its stop is settled (passed or skipped): its decisions go with a submission, as before
    cur = next((x for x in (data.get("status") or {}).get("stations") or [] if data["current"] in (x.get("pages") or [])), None)
    data["round_open"] = bool(data["current"]) and not (cur and cur.get("state") in ("done", "skipped"))
    if "studio" in parts or "mods" in parts:
        data["studio"] = studio_extras(project, data)
    if "mods" in parts:
        try:
            data["mods"] = module_extras(project, data)
        except (Exception, SystemExit) as e:   # the other modules show their empty states; the reason is said
            data["mods"] = None
            data["warnings"].append(f"modules: {type(e).__name__}: {e}")
    return data


NEEDED = ("ffmpeg", "node", "uv", "git")   # the programs bin/vh doctor marks as needed that the space page names when missing
ADAPTERS = ("claude-agent-acp", "codex-acp", "dsh-acp")


def lacks(doctor):
    """From bin/vh doctor --json: what a person needs and this machine lacks, [{what, state}] (state missing or outdated):
    a needed program (FFmpeg, Node, uv, git), a browser to draw pages with, and an agent to talk to in the column (no
    adapter installed). Optional modules, services and keys are not named."""
    mods = {m.get("name"): m for m in doctor.get("modules") or [] if isinstance(m, dict)}
    out = [{"what": n, "state": mods[n].get("state")} for n in NEEDED if n in mods and mods[n].get("state") in ("missing", "outdated")]
    if any(c.get("name") == "browser" and c.get("state") == "missing" for c in doctor.get("checks") or [] if isinstance(c, dict)):
        out.append({"what": "browser", "state": "missing"})
    if all(n in mods for n in ADAPTERS) and not any(mods[n].get("state") in ("ok", "outdated") for n in ADAPTERS):
        out.append({"what": "agent", "state": "missing"})
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
        self.codes = {}        # one-time codes: code → (until, window): a page trades one for the token, once (POST /api/claim)
        self.windows = {}      # window id → "window" | "tab": what this desk opened (its address carries the id)
        self.present = {}      # window id → pages of it connected with the token (GET /api/presence)
        self.events = {}       # window id → what to tell it ({go})
        self.pcond = threading.Condition()
        self.window_lock = threading.Lock()   # one show at a time: two clicks, two terminals, still one window
        self.opened_at = []    # POST /api/open: twenty a minute
        self.spent = set()     # window ids whose code has been traded (by its page, or by whoever got to it first)
        self.renewed = 0       # windows replaced because their page could not trade its code (POST /api/open {renew}): twice a run
        self.window_name = "console-" + hashlib.sha1("\n".join(sorted(os.path.realpath(r) for r in roots)).encode()).hexdigest()[:10] \
            if self.project is None else "desk-" + pid_of(self.project)[:10]   # its window's profile: one desk, one window
        self.link_cmd = ""     # the line that stops this desk and starts it again with a new key (serve sets it)
        self._machine, self._machine_lock = None, threading.Lock()   # bin/vh doctor's answer, asked once a run (GET /api/machine)
        self.port = self.server_address[1]
        self.hosts = {f"{h}:{self.port}" for h in ("127.0.0.1", "localhost")}
        self.last = time.time()   # the last request: --idle stops a server nobody has asked anything for that long
        self._lock = threading.Lock()
        self._listing = (0.0, None)
        self._joined_m = 0
        self._keys = {self.own_key: self.project} if self.project else {}
        self.agents = A.Manager(self.url)   # starts nothing: an adapter starts the first time someone talks to it
        # a film begun on the space: the conversation's record in the person's own data folder until the film is made (one
        # for every console of theirs, whatever its roots), the agent working in the workspace (the clone, where CLAUDE.md
        # and bin/vh are); none for a desk of one project alone
        self.space = None if self.only else space_dir()
        self.agents.place = self.place
        self.agents.places = self.film_places
        self.agents.present = lambda: any(n > 0 for n in list(self.present.values()))
        self.agents.space_note = space_note(self.roots)

    # ---------- the window: one-time codes, presence, show ----------
    def mint(self, ttl, w=""):
        """A one-time code for one page, good for ttl seconds."""
        code = secrets.token_urlsafe(18)
        now = time.time()
        with self._lock:
            self.codes = {c: v for c, v in self.codes.items() if v[0] > now}
            self.codes[code] = (now + ttl, w)
        return code

    def claim(self, code):
        """Spend a code: True once, while it lives."""
        with self._lock:
            hit = next((c for c in self.codes if secrets.compare_digest(c.encode(), code.encode("utf-8", "replace"))), None)
            v = self.codes.pop(hit, None) if hit else None
            ok = bool(v) and v[0] > time.time()
            if ok and v[1]:
                self.spent.add(v[1])
        return ok

    def rotate(self):
        """A new token for this run: every page holding the old one can only look, and its streams end."""
        with self.pcond:
            self.token = secrets.token_urlsafe(24)
            self.present, self.events = {}, {}
            self.pcond.notify_all()

    def renew(self, w, at=""):
        """POST /api/open {renew: w}: the page of a window this desk made could not trade its code (spent by someone else
        first, or run out). When its code was spent, the token changes (whoever holds it can only look; its streams end);
        then a fresh window takes that one's place. Twice a run at most, then the page stays one that can only look. A
        window whose page is connected is never renewed (nothing changes, nothing counted: a plain POST with the window's
        id from ps cannot replace a working window). A window this run did not make: a plain show. → show()'s answer, and
        renewed."""
        with self.pcond:
            if self.present.get(w, 0) > 0:
                return {"opened": True, "renewed": False, "code": "connected", "why": "that window's page is connected"}
        with self._lock:
            known = w in self.windows
            if known and self.renewed >= 2:
                return {"opened": False, "renewed": False, "code": "taken",
                        "why": "another program on this computer connected before Studio's window did, twice: start Studio again"}
            if known:
                self.renewed += 1
            taken = known and w in self.spent
        if not known:
            return dict(self.show(at), renewed=False)
        if taken:
            self.rotate()   # no page is present after it: show() closes the window and makes a fresh one
        return dict(self.show(at), renewed=True)

    def live_window(self):
        """(id, kind) of this desk's window whose page is connected with the token, or (None, None). kind: shell (Studio's
        own app) or window (a browser's)."""
        with self.pcond:
            w = next((w for w, n in self.present.items() if n > 0 and self.windows.get(w) in ("shell", "window")), None)
        return (w, self.windows.get(w)) if w else (None, None)

    def _wait_present(self, w, secs):
        end = time.time() + secs
        with self.pcond:
            while self.present.get(w, 0) <= 0:
                left = end - time.time()
                if left <= 0:
                    return False
                self.pcond.wait(left)
        return True

    def push(self, w, ev):
        with self.pcond:
            self.events.setdefault(w, []).append(ev)
            self.pcond.notify_all()

    def _entry(self, code, w, at):
        return f"{self.url}?c={code}&w={w}" + (f"#{at}" if at else "")

    MACHINE_AGAIN = 60   # s: while something is missing, a later page asks doctor again at most this often (the person may have fixed it)

    def machine(self):
        """{lacks, platform} for the space page, from bin/vh doctor --json (it takes a few seconds; the page asks for it
        after it has drawn). Kept for the run when nothing is missing; while something is, asked again at most once a
        MACHINE_AGAIN; a run that could not tell is not kept ({lacks: [], error}). An agent adapter installed from the
        column since is taken off at once."""
        with self._machine_lock:
            m = self._machine
            if m is None or m["lacks"] and time.time() - m["at"] > self.MACHINE_AGAIN:
                import subprocess
                try:
                    r = subprocess.run([os.environ.get("OVH_BASH") or "bash", str(HERE.parent.parent / "bin" / "vh"), "doctor", "--json"],   # (bin/vh hands it the browser its finders find)
                                       capture_output=True, text=True, timeout=120, stdin=subprocess.DEVNULL)
                    d = json.loads(r.stdout)
                    if not isinstance(d, dict) or not isinstance(d.get("modules"), list):
                        raise ValueError("no modules in what doctor said")
                    m = self._machine = {"lacks": lacks(d), "platform": d.get("platform"), "at": time.time()}
                except (OSError, ValueError, subprocess.SubprocessError) as e:
                    return {"lacks": [], "platform": None, "error": f"doctor could not tell ({type(e).__name__})"}
            got = {k: v for k, v in m.items() if k != "at"}
        if any(A.installed(k) for k in A.ADAPTERS):
            got["lacks"] = [x for x in got["lacks"] if x["what"] != "agent"]
        return got

    def show(self, at=""):
        """Show Studio's window at that place of the page. The one whose page is connected comes to the front (and goes
        there). Else one new window, counted as open only once its page connects: Studio's own app when it is installed
        (tools/desk/shell: it raises itself, one window a desk), once more if its page does not connect; then a window of a
        Chromium-family browser (a leftover of ours with no page in it goes first, so there is never a second), once more;
        then a tab of the default browser. → {opened, how, why, code}: how is front (raised), open (there, but the system
        would not raise it), app (Studio's own app), window (a browser's), tab (the fallback); why and code say what did not
        work on the way."""
        import window as WIN
        with self.window_lock:
            prof = WIN.profile(self.window_name)
            app, app_why = WIN.shell()
            w, kind = self.live_window()
            if kind == "shell" and not (app and WIN.shell_pid(app)):   # its stream has not noticed yet (a ping every 5 s), but it is gone
                w = None
            if kind == "window" and WIN.main_pid(prof) is None:
                w = None
            if w:
                if at:
                    self.push(w, {"go": at})
                if kind == "shell":   # the running app takes the line and raises its window itself
                    return {"opened": True, "how": "front" if WIN.shell_send(app, {"url": self.url, "role": self.window_name}) else "open"}
                return {"opened": True, "how": "front" if WIN.raise_(prof) else "open"}
            why, code = None, None
            if app:
                why, code = "Studio's own app did not open", "no_app"
                for _ in range(2):
                    w = secrets.token_hex(6)
                    self.windows[w] = "shell"
                    line = {"url": self._entry(self.mint(60, w), w, at), "role": self.window_name, "w": w, "fresh": True}
                    said_ = []
                    if WIN.shell_send(app, line, said_) and self._wait_present(w, 15):
                        return {"opened": True, "how": "app"}
                    if said_ == ["moved"]:   # the app no longer finds this clone: no second try, and say what a person can do
                        why, code = ("Studio's own app no longer finds OpenVideoHarness where it was installed: ask your agent to "
                                     "put the Studio icon back"), "app_moved"
                        break
            elif app_why:
                why, code = app_why, "no_app"
            WIN.close(prof)
            prog = WIN.browser()
            if prog:
                for _ in range(2):
                    w = secrets.token_hex(6)
                    self.windows[w] = "window"
                    if WIN.launch(prog, prof, self._entry(self.mint(60, w), w, at)) and self._wait_present(w, 12):
                        return {"opened": True, "how": "window", "why": why, "code": code}
                    WIN.close(prof)
                why, code = (why + "; " if why else "") + "its window started, but the page in it did not connect", code or "no_connect"
            else:
                why, code = (why + "; " if why else "") + "no Chrome, Chromium, Edge or Brave here for a window of its own", code or "no_browser"
            w = secrets.token_hex(6)
            self.windows[w] = "tab"
            if WIN.tab(self._entry(self.mint(60, w), w, at)) and self._wait_present(w, 12):
                return {"opened": True, "how": "tab", "why": why, "code": code}
            return {"opened": False, "how": None, "why": why + ", and no browser tab connected either", "code": code}

    def close_window(self):
        """This desk's window goes with it (it is no use without the desk): the app's (it quits when it was its last) or
        the browser's."""
        if not self.windows:
            return
        try:
            import window as WIN
            if "shell" in self.windows.values():
                app, _ = WIN.shell()
                if app and WIN.shell_pid(app):
                    WIN.shell_send(app, {"close": self.window_name})
            if "window" in self.windows.values():
                WIN.close(WIN.profile(self.window_name), wait=4)
        except Exception:
            pass

    def handle_error(self, request, client_address):
        """A page that went away mid-answer (a window closed, a reload, a stream given up) is no error: no traceback for it."""
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError)):
            return
        super().handle_error(request, client_address)

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
            jm = self._joined_mtime()
            if rec is not None and not fresh and time.time() - when < LISTING_TTL and jm == self._joined_m:
                return rec
            self._joined_m = jm
            if self.only:
                rec = {"version": 1, "roots": [], "count": 1, "projects": [PJ.row(self.project, self.project.name, S, False)]}
            else:
                rec = PJ.listing(self.roots)
                extra = ([str(self.project)] if self.project else []) + self.joined()
                for x in extra:   # the project it was started for, and the films that joined this console
                    if not any(os.path.realpath(r["path"]) == os.path.realpath(x) for r in rec["projects"]):
                        rec["projects"].append(PJ.row(Path(x), Path(x).name, S, False))
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

    def joined(self):
        """The films outside the roots that joined this console (bin/vh studio or gate on such a film: join()), each a
        folder that is still a project (BRIEF.md). None for a desk of one project."""
        p = joined_path(self.roots) if self.project is None else None
        try:
            got = json.loads(p.read_text()) if p else []
        except (OSError, ValueError):
            return []
        return [x for x in got if isinstance(x, str) and os.path.isabs(x) and os.path.isfile(os.path.join(x, "BRIEF.md"))][:50]

    def _joined_mtime(self):
        p = joined_path(self.roots) if self.project is None else None
        try:
            return p.stat().st_mtime_ns if p else 0
        except OSError:
            return 0

    def film_places(self):
        """Where a film begun on the space may be made: this console's roots, $OVH_PROJECTS, the workspace's projects/."""
        out = list(self.roots) + ([os.path.expanduser(os.environ["OVH_PROJECTS"])] if os.environ.get("OVH_PROJECTS") else [])
        return out + [str(WORKSPACE / "projects")]

    def place(self, film):
        """A film a conversation begun on the space made → its key (a film outside the roots joins the space first), or None."""
        real = os.path.realpath(str(film))

        def find():
            rows = self.listing(fresh=True)["projects"]
            return next((r["key"] for r in rows if os.path.realpath(r["path"]) == real), None)
        k = find()
        if k is None and join(real, self.roots):
            k = find()
        return k

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

    def _error(self, code, msg, reason=None):
        """{error: msg} with the status; reason: a word the page says in the person's own language (the feedback route)."""
        self._json(dict({"error": msg}, **({"reason": reason} if reason else {})), code)

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
            # a GET changes nothing and gives nothing (a browser may fetch an address twice): the page's script trades the
            # code in its address for the token (POST /api/claim)
            page = (HERE / "static" / "index.html").read_text(encoding="utf-8").replace("{{TOKEN}}", "") \
                .replace("{{HOME}}", srv.own_key or "")
            return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8", {"Content-Security-Policy": CSP})
        if path.startswith("/static/") and path[8:] in STATIC:
            return self._send(200, (HERE / "static" / path[8:]).read_bytes(), STATIC[path[8:]])
        if path == "/api/projects":
            return self._projects()
        if path == "/api/hello":   # does the page hold this run's token? (one from an earlier run does not count); if not, why, and the way out
            given = self.headers.get("X-Desk-Token", "").encode("utf-8", "replace")
            ok = secrets.compare_digest(given, srv.token.encode("ascii"))
            return self._json({"ok": True} if ok else {"ok": False, "reopen": True}, 200 if ok else 403)
        if path == "/api/presence":
            return self._presence()
        if path == "/api/machine":   # what this machine still lacks for making films (the space page says it, only when something is missing)
            return self._json(srv.machine())
        m = re.fullmatch(r"/api/p/([^/]+)/(data|stage|status|gate/([A-Za-z0-9_-]{1,24}))", path)
        if m:
            key = unquote(m.group(1))
            project = srv.project_of(key)
            if project is None:
                return self._error(404, f"no project {key!r} under this desk's roots")
            what = m.group(2)
            if what == "data":
                return self._data(project, key)
            if what == "status":   # with this round's page: the console notices a new page the agent sent; and where the film stands now
                pages = review.gate_pages(project)
                try:
                    import status as S
                    o = S.collect(project, light=True)
                    now, plan = o.get("now"), o.get("plan")
                except (Exception, SystemExit):   # the page keeps what it has
                    now = plan = None
                return self._json(dict(F.listening(project), project=project.name, key=key, round=pages[-1].stem[5:] if pages else None,
                                       revision_stamp=RV.stamp(project), now=now, plan=plan))
            if what == "stage":
                return self._stage(project, key)
            lang = (parse_qs(urlsplit(self.path).query).get("lang") or [None])[0]
            return self._gate(project, key, m.group(3), lang if lang in ("zh", "en") else None)
        m = re.fullmatch(r"/api/space/agents|/api/space/agent/([a-f0-9]{32})/events", path)
        if m:   # the space's column: a film begun with a sentence, before (and while) it has a folder of its own
            if srv.space is None:
                return self._error(404, "this desk has no space")
            return self._agents(srv.space, None, space=True) if not m.group(1) else self._events(srv.space, None, m.group(1), space=True)
        m = re.fullmatch(r"/api/p/([^/]+)/agents|/api/p/([^/]+)/agent/([a-f0-9]{32})/events", path)
        if m:
            key = unquote(m.group(1) or m.group(2))
            project = srv.project_of(key)
            if project is None:
                return self._error(404, f"no project {key!r} under this desk's roots")
            if m.group(1):
                return self._agents(project, key)
            return self._events(project, key, m.group(3))
        if path.startswith("/f/") or path.startswith("/v/"):
            key, _, rel = path[3:].partition("/")
            project = srv.project_of(unquote(key))
            if project is None:
                return self._error(404, "no such project")
            return self._file(project, rel) if path.startswith("/f/") else self._view(project, key, rel)
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

    # ---------- the agent column ----------
    def _agents(self, project, key, space=False):
        """The agents this machine has (installed or how to install), the project's conversations, and who holds it. space:
        the conversations begun on the space that have made no film yet."""
        mgr = self.server.agents
        try:
            sessions = [x for x in mgr.listing(project) if not space or not x.get("placed")]
        except OSError as e:
            sessions, err = [], str(e)
        else:
            err = None
        lock = None if space else A.agentlock.read(project)
        auth = mgr.auth
        extra = {}
        if space:   # ?sid= a conversation this page had open: the film it went to, when it made one meanwhile
            sid = (parse_qs(urlsplit(self.path).query).get("sid") or [""])[0]
            film = mgr.went(sid, project) if sid else None
            rows = self.server.listing()["projects"] if film else []
            key = next((r["key"] for r in rows if os.path.realpath(r["path"]) == os.path.realpath(film)), None) if film else None
            if key:
                extra["went"] = {"id": sid, "key": key}
        elif not sessions and self.server.space:   # a new film with nothing in its column: a conversation from the space that may have made it
            strays = [{k: x.get(k) for k in ("id", "kind", "label", "first", "created", "running")} for x in mgr.strays(project, self.server.space)]
            if strays:
                extra["strays"] = strays[:3]
        return self._json({"agents": [dict(a, signed_in={"authenticated": True, "unauthenticated": False}.get(auth.get(a["kind"])), installing=mgr.install_state(a["kind"]), choices=mgr.choices(a["kind"])) for a in A.catalog()], "sessions": sessions, "pid": pid_of(project), "approval_timeout": A.APPROVAL_TIMEOUT,
                           "lock": {k: lock.get(k) for k in ("kind", "label", "session", "since")} if lock else None,
                           **extra, **({"error": err} if err else {})})

    def _presence(self):
        """GET /api/presence?token=&w=: a page with the token, as Server-Sent Events: while it is connected the desk knows
        that page (its window) is there; it is told where to go ({go}); a page that went away is noticed within a second
        (its connection, looked at each second: closed is readable and empty), and a comment every 5 s keeps the line."""
        q = parse_qs(urlsplit(self.path).query)
        given = (self.headers.get("X-Desk-Token") or (q.get("token") or [""])[0]).encode("utf-8", "replace")   # Studio's own app sends a header
        srv = self.server
        if not secrets.compare_digest(given, srv.token.encode("ascii")):
            return self._error(403, "no access")
        w = (q.get("w") or [""])[0]
        w = w if re.fullmatch(r"[a-f0-9]{1,24}", w) else ""
        self.send_response(200)
        for k, v in (("Content-Type", "text/event-stream; charset=utf-8"), ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff")):
            self.send_header(k, v)
        self.end_headers()
        self.close_connection = True
        with srv.pcond:
            mine = srv.token   # the stream ends when the token changes (Desk.rotate)
            srv.present[w] = srv.present.get(w, 0) + 1
            srv.pcond.notify_all()
        try:
            self.wfile.write(b"retry: 2000\nevent: hello\ndata: {}\n\n")
            self.wfile.flush()
            pinged = time.time()
            while not srv.agents.closed and srv.token == mine:
                with srv.pcond:
                    if not srv.events.get(w):
                        srv.pcond.wait(1)
                    evs = srv.events.pop(w, [])
                if not evs and time.time() - pinged < 5:
                    if _closed(self.connection):
                        break
                    continue
                self.wfile.write(("".join(f"data: {json.dumps(e)}\n\n" for e in evs) if evs else ": ping\n\n").encode("utf-8"))
                self.wfile.flush()
                pinged = srv.last = time.time()
        except (OSError, ValueError):
            pass   # the page went away: its window closed, or it reloaded
        finally:
            with srv.pcond:
                if srv.token == mine:   # after a rotation the count started again
                    srv.present[w] = srv.present.get(w, 1) - 1
                srv.pcond.notify_all()

    def _events(self, project, key, sid, space=False):
        """One conversation's events as Server-Sent Events: those after Last-Event-ID (or ?after=), then each as it comes;
        a comment every 5 s keeps the line (and the desk's --idle) alive, and finds a page that went away. Needs the page's token (?token=): the events are
        the conversation, file contents and commands included."""
        q = parse_qs(urlsplit(self.path).query)
        given = (self.headers.get("X-Desk-Token") or (q.get("token") or [""])[0]).encode("utf-8", "replace")   # Studio's own app sends a header
        mine = self.server.token
        if not secrets.compare_digest(given, mine.encode("ascii")):
            return self._error(403, "missing or wrong desk token: reload the page")
        s = self.server.agents.get(sid, project, key, space=space)
        if s is None:
            return self._error(404, "no such conversation in this project")
        try:
            after = int(self.headers.get("Last-Event-ID") or (q.get("after") or ["0"])[0])
        except ValueError:
            after = 0
        self.send_response(200)
        for k, v in (("Content-Type", "text/event-stream; charset=utf-8"), ("Cache-Control", "no-store"), ("X-Content-Type-Options", "nosniff"),
                     ("X-Accel-Buffering", "no"), ("Referrer-Policy", "no-referrer")):
            self.send_header(k, v)
        self.end_headers()
        self.close_connection = True
        mgr = self.server.agents
        with s.cond:
            s.subscribers += 1
        try:
            self.wfile.write(("retry: 2000\nevent: hello\ndata: " + json.dumps(dict(s.summary(), config=A.clean(s.config, s.root),
                                                                                   caps=mgr.caps.get(s.kind) or {}), ensure_ascii=False) + "\n\n").encode("utf-8"))
            self.wfile.flush()
            while not mgr.closed and self.server.token == mine:   # a new token (Desk.rotate) ends it
                evs = s.after(after)
                if evs:
                    out = "".join(f"id: {e['seq']}\ndata: {json.dumps(e, ensure_ascii=False)}\n\n" for e in evs)
                    after = evs[-1]["seq"]
                    self.wfile.write(out.encode("utf-8"))
                    self.wfile.flush()
                    self.server.last = time.time()
                    continue
                with s.cond:
                    if s.seq <= after and not mgr.closed:
                        s.cond.wait(5)
                if s.seq <= after:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    self.server.last = time.time()
        except (OSError, ValueError):
            pass   # the page went away
        finally:
            with s.cond:
                s.subscribers -= 1

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
            data = project_data(project)
        except Exception as e:
            return self._error(500, f"could not read the project: {type(e).__name__}: {e}")
        data["key"], data["home"], data["only"] = key, key == self.server.own_key, self.server.only
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

    def _view(self, project, key, rel):
        """GET /v/<key>/<path>: the file on a page of its own, with a slim bar (its name and where it is in the project):
        text and markdown as text (markdown through reader.render_md, everything escaped), a picture, a player, a page
        in a frame (still sandboxed by /f/'s header); a kind it cannot show, a sentence that says so and where it is.
        Studio's own app opens the console's new-page links here, so a link never gives an empty window."""
        f = self._resolve(project, rel)
        if not f:
            return self._error(404, "no such file in this project")
        name, ext = os.path.basename(f), os.path.splitext(f)[1].lower()
        where = os.path.relpath(f, project)
        src = "/f/" + key + "/" + rel
        kind = next((k for k, exts in VIEW.items() if ext in exts), None)
        e = html.escape
        if kind == "image":
            body = f'<main class="pic"><img src="{e(src)}" alt="{e(name)}"></main>'
        elif kind in ("video", "audio"):
            body = f'<main class="av"><{kind} controls preload="metadata" src="{e(src)}"></{kind}></main>'
        elif kind == "page":
            body = f'<main class="page"><iframe src="{e(src)}" title="{e(name)}"></iframe></main>'
        elif kind in ("markdown", "text") and os.path.getsize(f) <= VIEW_TEXT_MAX:
            text = Path(f).read_bytes().decode("utf-8", "replace")
            body = (f'<main class="text"><article class="md">{reader.render_md(text)}</article></main>' if kind == "markdown"
                    else f'<main class="text"><pre>{e(text)}</pre></main>')
        else:
            why = ("这份文本太长，这里不显示" if kind else "这种文件在这里显示不了") + f"：它在项目的 {where}。"
            why_en = ("This text is too long to show here" if kind else "Studio cannot show this kind of file here") + f": it is {where} in the project."
            body = f'<main class="none"><p>{e(why)}<br>{e(why_en)}</p></main>'
        page = (f'<!doctype html><html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                f'<title>{e(name)}</title><link rel="stylesheet" href="/static/ui.css"><link rel="stylesheet" href="/static/reader.css">'
                f'<script src="/static/reader.js"></script></head><body><header class="bar"><span class="name">{e(name)}</span>'
                f'<span class="path">{e(where)}</span></header>{body}</body></html>')
        return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8", {"Content-Security-Policy": CSP})

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
        a = re.fullmatch(r"/api/p/([^/]+)/agent/(new|install|([a-f0-9]{32})/(attach|say|answer|stop|mode|config|bring))", path)
        sp = re.fullmatch(r"/api/space/agent/(new|install|([a-f0-9]{32})/(attach|say|answer|stop|mode|config))", path)
        if sp:
            if self.server.space is None:
                return self._error(404, "this desk has no space")
            return self._agent_post(self.server.space, None, sp.group(2), sp.group(3) or sp.group(1), space=True)
        if m or a:
            project = self.server.project_of(unquote((m or a).group(1)))
            if project is None:
                return self._error(404, "no such project")
        elif path == "/api/feedback" and self.server.project:
            project = self.server.project
        elif path == "/api/claim":
            return self._claim()
        elif path == "/api/open":
            return self._open()
        else:
            return self._error(404, "not found")
        if a:
            return self._agent_post(project, unquote(a.group(1)), a.group(3), a.group(4) or a.group(2))
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc not in self.server.hosts:
            return self._error(403, "cross-origin request refused", "origin")
        given = self.headers.get("X-Desk-Token", "").encode("utf-8", "replace")   # bytes: a non-ASCII str would raise
        if not secrets.compare_digest(given, self.server.token.encode("ascii")):
            return self._error(403, "missing or wrong desk token: reload the page", "token")
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            return self._error(415, "send JSON", "format")
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > F.MAX_BODY:
            return self._error(413 if n > 0 else 400, f"empty, or larger than {F.MAX_BODY // 1024} KiB", "too_big" if n > 0 else "empty")
        try:
            body = self.rfile.read(n)
        except OSError:   # timed out waiting for the rest of the body
            self.close_connection = True
            return self._error(408, "the request body did not arrive", "slow")
        if len(body) < n:
            self.close_connection = True
            return self._error(400, f"the body is {len(body)} bytes, not the {n} its Content-Length says", "slow")
        try:
            raw = json.loads(body.decode("utf-8"))
            if m:   # the console's address: the page says which folder it was opened on, and it has to be this one
                if not isinstance(raw, dict) or raw.pop("pid", None) != pid_of(project):
                    return self._error(409, "this address names another project now than the page was opened on: reload it", "moved")
            fb = F.validate(project, raw)
        except (ValueError, TypeError, AttributeError, RecursionError) as e:   # UnicodeDecodeError is a ValueError
            why = str(e) or type(e).__name__   # a page that changed under the person (its gate file, a decision no longer on it), else something the page sent wrong
            return self._error(400, why, "page_changed" if re.search(r"there is no out/review/gate-|is not a decision and option", why) else "invalid")
        saved = F.save(project, fb)
        sys.stderr.write(f"desk: feedback saved → {saved} (also in REVIEW.md)\n")
        sys.stderr.flush()
        self._json(dict(F.listening(project), saved=os.path.relpath(saved, project)))

    def _claim(self):
        """POST /api/claim {c}: a one-time code → this run's token, once."""
        raw = self._body(4096, token=False)
        if raw is None:
            return
        c = raw.get("c") if isinstance(raw.get("c"), str) else ""
        if c and self.server.claim(c):
            return self._json({"ok": True, "token": self.server.token})
        return self._json({"ok": False}, 403)

    def _open(self):
        """POST /api/open {at, renew}: show Studio's window at that place (/p/<key>, and a module or a gate after it: a
        project this desk serves; else its home). No token: it shows the window and says whether it did. renew: the id of
        Studio's window whose page could not trade its code (Desk.renew). Twenty a minute."""
        raw = self._body(4096, token=False)
        if raw is None:
            return
        srv = self.server
        at = raw.get("at") or ""
        if not isinstance(at, str):
            return self._error(400, "at: a place of the page, as /p/<key>")
        at = at.strip()
        if at in ("", "/"):
            at = ""
        else:
            m = re.fullmatch(r"/p/([^/?#\s]{1,200})(/[^?#\s]{0,300})?", at)
            if not m or srv.project_of(unquote(m.group(1))) is None:
                at = ""   # a place this desk does not have: its home (the page that asked says nothing else)
        now = time.time()
        with srv._lock:
            srv.opened_at = [x for x in srv.opened_at if now - x < 60]
            if len(srv.opened_at) >= 20:
                return self._json({"ok": False, "opened": False, "why": "asked too often: try again in a minute"}, 429)
            srv.opened_at.append(now)
        renew = raw.get("renew")
        if isinstance(renew, str) and re.fullmatch(r"[a-f0-9]{1,24}", renew):
            return self._json(dict(srv.renew(renew, at), ok=True))
        r = srv.show(at)
        return self._json(dict(r, ok=True))

    def _body(self, max_bytes=None, token=True):
        """The checks every POST passes (same origin, this run's token, JSON, a whole body) → the parsed JSON, or None
        after the refusal is sent. token False: all but the token (POST /api/claim and /api/open need none)."""
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc not in self.server.hosts:
            self._error(403, "cross-origin request refused")
            return None
        given = self.headers.get("X-Desk-Token", "").encode("utf-8", "replace")
        if token and not secrets.compare_digest(given, self.server.token.encode("ascii")):
            self._error(403, "missing or wrong desk token: reload the page")
            return None
        if not self.headers.get("Content-Type", "").startswith("application/json"):
            self._error(415, "send JSON")
            return None
        limit = max_bytes or F.MAX_BODY
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > limit:
            self._error(413 if n > 0 else 400, f"empty, or larger than {limit // 1024} KiB")
            return None
        try:
            body = self.rfile.read(n)
        except OSError:
            self.close_connection = True
            self._error(408, "the request body did not arrive")
            return None
        if len(body) < n:
            self.close_connection = True
            self._error(400, f"the body is {len(body)} bytes, not the {n} its Content-Length says")
            return None
        try:
            raw = json.loads(body.decode("utf-8"))
        except (ValueError, RecursionError) as e:
            self._error(400, str(e) or type(e).__name__)
            return None
        if not isinstance(raw, dict):
            self._error(400, "send a JSON object")
            return None
        return raw

    def _agent_post(self, project, key, sid, what, space=False):
        """The person's actions in the agent column. Each carries the folder's identity (pid), like a submission: a page
        opened on another folder under this address is refused. Only the text in "text" is ever sent as the person's
        words; an answer must be one of the options the agent offered for a request that still waits."""
        raw = self._body(64 * 1024)
        if raw is None:
            return
        if raw.get("pid") != pid_of(project):
            return self._error(409, "this address names another project now than the page was opened on: reload it")
        mgr = self.server.agents
        try:
            if what == "install":   # the person's click: the console installs the adapter itself (bin/vh desk agents install); cancel stops it
                if not isinstance(raw.get("kind"), str) or raw["kind"] not in A.ADAPTERS:
                    return self._error(400, "unknown agent")
                return self._json({"ok": True, "installing": mgr.install(raw["kind"], cancel=raw.get("cancel") is True)})
            if what == "new":
                kind = raw.get("kind")
                if not isinstance(kind, str) or kind not in A.ADAPTERS:
                    return self._error(400, "unknown agent")
                s = mgr.open(project, key, kind, personal=raw.get("personal", True) is not False,   # model, effort: the person's choice in the new box
                             asked={r: raw.get(r) for r in ("model", "effort") if isinstance(raw.get(r), str)},
                             cwd=WORKSPACE if space else None)   # on the space: the agent starts where CLAUDE.md is
                try:
                    s.attach()   # the agent's mode, model and effort are on the page before the first word
                except A.Unavailable as e:
                    return self._json(dict(s.summary(), error=e.code, detail=str(e)[:500]), 503 if e.code != "not_installed" else 424)
                return self._json(dict(s.summary(), config=A.clean(s.config, s.root)))
            if what == "bring" and not space:   # the person's click on a new film's empty column: that conversation from the space comes here
                if not any(x["id"] == sid for x in mgr.strays(project, self.server.space)):
                    return self._error(409, "that conversation cannot have made this film")
                s = mgr.get(sid, self.server.space)
                return self._json({"ok": bool(s and mgr.adopt(s, project))})
            s = mgr.get(sid, project, key, space=space)
            if s is None:
                return self._error(404, "no such conversation in this project")
            if what == "attach":
                s.attach()
                return self._json(dict(s.summary(), config=A.clean(s.config, s.root)))
            if what == "say":
                text = raw.get("text")
                if not isinstance(text, str) or not text.strip():
                    return self._error(400, "say something")
                if len(text) > A.MAX_PROMPT:
                    return self._error(413, f"at most {A.MAX_PROMPT} characters at once")
                text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text).strip()
                scope = raw.get("scope") if isinstance(raw.get("scope"), dict) else None
                scope = {k: scope.get(k) for k in ("kind", "id", "t", "t1", "module", "label") if scope.get(k) is not None} if scope else None
                if scope and isinstance(scope.get("label"), str):
                    scope["label"] = scope["label"][:80]   # shown in the page with the message, never sent to the agent
                s.say(text, scope, despite=raw.get("despite") is True)
                return self._json({"ok": True})
            if what == "answer":
                s.answer(str(raw.get("request") or ""), str(raw.get("option") or ""))
                return self._json({"ok": True})
            if what == "stop":
                return self._json({"ok": True, "stopped": s.stop()})
            if what == "mode":
                s.set_mode(str(raw.get("mode") or ""))
                return self._json({"ok": True})
            if what == "config":
                s.set_config(str(raw.get("id") or ""), raw.get("value"))
                return self._json({"ok": True})
        except A.Busy as e:
            return self._json({"error": "busy", "who": e.who}, 409)
        except A.Unavailable as e:
            return self._json({"error": e.code, "detail": str(e)[:500]}, 424 if e.code == "not_installed" else 503)
        except ValueError as e:
            return self._error(400, str(e))
        return self._error(404, "not found")


# ---------- start: once per project, or one console ----------

WORKSPACE = HERE.parent.parent   # the clone: CLAUDE.md, bin/vh, projects/


def space_dir():
    """Where the conversations begun on Studio's space live until their film is made: the person's own data folder, beside
    Studio's app record (ovh-studio/), one for every console of theirs."""
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "ovh-studio" / "space"


def space_note(roots=()):
    """Studio's line after the first words of a film begun on the space: where the person follows it, and where the film
    goes when this console looks at a folder of its own (its first --root, else $OVH_PROJECTS, which the agent's clean
    environment does not carry). Built from the console's own settings, never from the page."""
    where = roots[0] if roots else os.environ.get("OVH_PROJECTS") or ""
    where = os.path.realpath(os.path.expanduser(where)) if where else ""
    import shlex   # (a folder with a space in its name reaches the agent as one argument)
    return ("(From Studio: the person wrote this in Studio's space to start a new film, and follows this conversation in "
            "Studio; review its stops there (bin/vh gate … --desk)." + (f" Make the film's folder under {where} (bin/vh new … --dir {shlex.quote(where)})." if where else "") + ")")


def _closed(conn):
    """Has the other end of this connection gone (a page that closed sends nothing more on a stream: readable means EOF)?"""
    import select
    try:
        if not select.select([conn], [], [], 0)[0]:
            return False
        return conn.recv(1, socket.MSG_PEEK) == b""
    except (OSError, ValueError):
        return True


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


def joined_path(roots=()):
    """The films a console shows beside its roots': the last fifty opened in Studio from outside them, a list beside its
    info file in this user's own folder in the temp folder (0700), so a restart (bin/vh desk link) keeps them."""
    p = _info_path(None, roots)
    return p.with_name(p.stem + ".films") if p else None   # (not *.json: what looks for console-*.json finds only info files)


def join(project, roots=()):
    """A film outside the console's roots joins its space (bin/vh studio <film>, bin/vh gate on the desk channel while
    Studio runs), so it opens in Studio's one window instead of a desk and window of its own. → True when it is in."""
    p = joined_path(roots)
    real = os.path.realpath(str(project))
    if p is None or not os.path.isfile(os.path.join(real, "BRIEF.md")):
        return False
    import fcntl
    try:
        with open(p.with_name(p.name + ".lock"), "a") as lock:   # two opens at once: neither loses the other's film
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                cur = [x for x in json.loads(p.read_text()) if isinstance(x, str)] if p.exists() else []
            except (OSError, ValueError):
                cur = []
            if cur[-1:] != [real]:   # opened again: the newest, so the list is the last fifty opened
                tmp = p.with_name(p.name + f".{os.getpid()}.tmp")
                tmp.write_text(json.dumps(([x for x in cur if x != real] + [real])[-50:]))
                os.replace(tmp, p)
    except OSError:
        return False
    return True


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
    info = running_info(project, roots)
    return info.get("url") if info else None


def running_info(project=None, roots=None):
    """What a running desk of this project (or console of these roots) wrote about itself: url, port, pid, how it was
    started (only, roots, idle, background); None when none runs."""
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
    return info


def link_cmd(project=None, roots=()):
    """The line that gives this desk a new link (bin/vh desk link): the project as a path, ~ for the home folder."""
    import shlex
    home = str(Path.home())

    def short(x):
        x = os.path.realpath(str(x))
        return "~" + x[len(home):] if home and len(home) > 1 and (x == home or x.startswith(home + os.sep)) and " " not in x else shlex.quote(x)
    return " ".join(["bin/vh desk link"] + ([short(project)] if project else []) + [w for r in roots for w in ("--root", short(r))])


def ask_open(url, at=""):
    """Ask the desk at url to show Studio's window at that place (POST /api/open). → {opened, how, why}."""
    import http.client
    u = urlsplit(url)
    try:
        c = http.client.HTTPConnection("127.0.0.1", u.port, timeout=120)
        c.request("POST", "/api/open", body=json.dumps({"at": at}).encode(), headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{u.port}"})
        r = c.getresponse()
        d = json.loads(r.read() or b"{}")
        c.close()
    except (OSError, ValueError, http.client.HTTPException) as e:
        return {"opened": False, "how": None, "why": f"Studio did not answer ({type(e).__name__})"}
    if not isinstance(d, dict):
        return {"opened": False, "how": None, "why": "Studio answered something else"}
    if r.status != 200:
        return {"opened": False, "how": None, "why": d.get("why") or d.get("error") or f"HTTP {r.status}"}
    return {"opened": bool(d.get("opened")), "how": d.get("how"), "why": d.get("why"), "code": d.get("code")}


NO_TERMINAL = ("--print-address writes the address to your terminal and nowhere else, and this has none (an agent's shell has "
               "none, nor has a pipe or a service): run it yourself in a terminal")


def has_terminal():
    """Has this process a terminal of its own (/dev/tty)? An agent's shell, a pipe or a service has none."""
    try:
        with open("/dev/tty", "w"):
            return True
    except OSError:
        return False


def to_terminal(text):
    """text to this process's own terminal only: never stdout, a log or a --json record (an address that opens a page
    goes only where a person sits). → False when there is none."""
    try:
        with open("/dev/tty", "w", encoding="utf-8") as t:
            t.write(text.rstrip("\n") + "\n")
        return True
    except OSError:
        return False


def address_words(url):
    """The lines --print-address writes to the terminal."""
    return (f"Studio's address, for a browser on another computer: {url}\n  it opens one page, once, within ten minutes; "
            "whoever opens it first can work in Studio, so keep it to yourself")


def said(r, icon=False):
    """What a person reads after a show: what happened, and what to do when it did not (icon: the launcher icon's dialog,
    where nobody has a terminal in front of them)."""
    if r.get("opened"):
        if r.get("how") == "window" and r.get("why"):   # Studio's own app is installed and did not open: a browser's window instead
            return f"Studio is open in a browser window ({r['why']})."
        return {"front": "Studio is open: its window is in front.", "open": "Studio is open in its window.",
                "app": "Studio is open in its own window.", "window": "Studio is open in its own window.",
                "tab": "Studio is open in a tab of your browser (" + (r.get("why") or "no window of its own") + ")."}.get(r.get("how"), "Studio is open.")
    why = r.get("why") or "no reason given"
    if icon:
        return f"Studio's window did not open ({why}). Click the OVH Studio icon again, or ask your agent to open Studio."
    return f"Studio's window did not open ({why}). Run bin/vh studio again; on a computer with no screen, bin/vh studio --print-address"


def serve(project=None, port=None, idle=None, roots=(), only=False, code=None, open_browser=False, print_address=False, owner=None):
    """Serve until stopped, or (idle: seconds) until nobody has asked anything for that long. project None: the console.
    port None: the first free of 8780–8799; 0: any free port. only: this project and nothing else under the roots (the desk
    bin/vh gate starts). code: a one-time code from the one who starts it (on stdin), which prints it (--print-address).
    open_browser: show Studio's window once it serves (a start from a terminal). print_address: print an address with a
    one-time code (ten minutes, one page), for a browser on another machine. owner: who started it ("icon": the launcher,
    which stops it when you quit it), in its info file. → exit code."""
    project = Path(project).resolve() if project else None
    url = running(project, roots)
    person = sys.stdout.isatty()   # a person's terminal reads no addresses; an agent's shell or a log gets this one (it opens nothing)
    if url:
        what = project.name if project else "the console"
        print(f"desk: already serving {what}" + ("" if person else f" at {url}"), flush=True)
        if print_address:   # a running desk has no address to print: one that opens a page comes with a start
            print(f"  an address for another computer comes only with a fresh start: bin/vh desk link {str(project) + ' ' if project else ''}"
                  "--print-address starts it again (its window closes) and writes one to your terminal", flush=True)
        elif open_browser:
            print("desk: " + said(ask_open(url)), flush=True)
        else:
            print("  bin/vh studio shows its window", flush=True)
        return 0
    if print_address and not has_terminal():
        print(f"desk: {NO_TERMINAL}", file=sys.stderr)
        return 2
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
    # how it was started, so that bin/vh desk link can start it again alike: never the key or the token
    info = {"pid": os.getpid(), "port": srv.port, "url": srv.url, "started": datetime.datetime.now().isoformat(timespec="seconds"), "since": time.time(),   # since: epoch seconds
            "roots": [os.path.realpath(r) for r in roots], "only": bool(only and project), "idle": idle, "owner": owner}
    if project:
        info["project"] = os.path.realpath(str(project))
    srv.link_cmd = link_cmd(project, roots)
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
    if code:
        with srv._lock:
            srv.codes[code] = (time.time() + 600, "")
    print("desk: " + ("" if person else f"{srv.url}  ·  ") + f"{what}  (Ctrl-C stops it"
          + (f"; it stops by itself after {idle:g} s without a request)" if idle else ")"), flush=True)
    if print_address:   # the one address that opens a page: to the terminal alone
        print("  the address for another computer is in your terminal" if to_terminal(address_words(f"{srv.url}?c={srv.mint(600)}"))
              else f"  {NO_TERMINAL}", flush=True)
    if open_browser:   # a start from a terminal: Studio's window, made by the desk itself
        threading.Thread(target=lambda: print("desk: " + said(srv.show()), flush=True), daemon=True).start()
    elif not print_address and not code:
        print("  bin/vh studio shows its window", flush=True)
    code = 0
    try:
        srv.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        code = 130
    finally:
        srv.agents.shutdown()   # waiting requests cancelled, every adapter stopped (TERM to its group if it lingers)
        srv.close_window()      # its window is no use without it
        srv.server_close()
        try:
            if info_p is not None and json.loads(info_p.read_text()).get("pid") == os.getpid():
                info_p.unlink()
        except (OSError, ValueError):
            pass
    return code


if __name__ == "__main__":
    sys.exit(serve(sys.argv[1] if len(sys.argv) > 1 else None, int(sys.argv[2]) if len(sys.argv) > 2 else None))
