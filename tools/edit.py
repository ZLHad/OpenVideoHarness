"""bin/vh edit: a film as an edit list. <project>/edit.json lays the film out as a row of entries, each drawn from a source:
a page (the page contract, engines/CONTRACT.md), a still image, a solid colour, footage (a clip folder bin/vh footage get
makes, or a video file that keeps the clip rules), a version of another project's film, or nothing yet (a slate: a grey
card with the entry's reads). Tracks after the first place sounds (a sound source each), and footage can bring its own
(off unless asked): bin/vh mix … edit= puts them in the mix. It is shots.json grown up: the rows keep shots.json's
fields (id, segment, reads, label, unsure, frame, at) and say where each entry's picture comes from (src). The format:
engines/EDIT.md. stdlib only (and ffprobe, for footage).

usage: bin/vh edit init <project> [--fps 30] [--size 1920x1080]
       bin/vh edit build <project> [--json] [--quiet]
       bin/vh edit check <project> [--json]
       bin/vh edit list <project> [--json]

  init   folds the project's shots.json into a new edit.json: every shot an entry with no source (a slate) and its fields
         as they were, timed as the shots were; shots.json is renamed shots.json.folded (kept, not deleted; .folded-2, -3 …
         when an earlier one is there). Then bin/vh render draws the whole film as slates timed to the plan: gate ②'s
         full-length animatic. fps and size:
         --fps and --size, else the BRIEF's Output line, else 30 and 1920x1080. Refused when edit.json is there, and when
         the shots do not follow one another (a gap or an overlap: said, nothing written)
  build  resolves edit.json into out/edit.resolved.json: every start and end, written in seconds or as a reference
         (narration cues "@l4>", {"$music": [24, 1]}, a time map's "@#id"; tools/audio/time_refs.py), in whole frames
         (frame_from, tools/timegrid.py), each entry's source, the runs render draws, footage's first frame (frame_at
         of its in), the sounds placed. With footage that speaks (sound role voice, clip.json's words), it also writes
         out/edit.timeline.<lang>.json: the narration with the footage's words, in film seconds (what bin/vh mix,
         captions and qa read). Prints what it found and, since the last build, which entries moved. bin/vh render
         builds it first, every time; nothing else needs a browser
  check  build's checks without writing, and: the files the sources name against the last build (changed since?), each
         source's licence against the BRIEF's Assets policy (bin/vh assets: strict refuses NC, ND and unknown, record
         says them; a clip folder is one record), a video file with no colour tags (it fails until it is tagged), the
         slates left; with a browser (bin/vh finds one), each page too: one shorter than its entry
         without "hold", a film-clock page reading another narration timeline, beat map or time map than edit.json's
         refs, a local-clock page whose cues hang on the narration
  list   the entries, one a line: frames, seconds, what draws each, segment, reads

--json: build prints the resolved document with "said" (its lines); check {"version": 1, "tool", "edit", "exit",
"findings": [{"severity", "kind", "entry", "message"}]}; list {"version": 1, "fps", "frames", "entries": [...]}.
Exit: 0 done (with notes) · 1 the entries do not fit (a gap or an overlap between two, an entry shorter than a frame,
out and end that disagree, footage too short for its entry; check: a licence strict refuses or a ledger it cannot read,
a page shorter than its entry, footage with no colour tags, a transition bin/vh render stops on, pages a browser could
not read) · 2 the file, its format or a reference (an unknown source or id, a time that does not resolve, a file that is
not there, footage that cannot be drawn as it is: all listed at once).
"""
import argparse, difflib, hashlib, json, math, os, re, shlex, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "audio"))
from timegrid import frame_from   # noqa: E402  (seconds to frames, the one way)
import time_refs as TR   # noqa: E402  (references: tools/audio/time_refs.py)

FILE = "edit.json"
REF_KEYS = ("timeline", "lead", "music", "timemap")   # an edit list's time sources (an events.json header also takes "edit": out/edit.resolved.json)
RESOLVED = Path("out") / "edit.resolved.json"
ID = re.compile(r"[A-Za-z0-9_]+\Z")
KEY = re.compile(r"[A-Za-z0-9_.-]+\Z")
COLOR = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\Z")
ENTRY_REF = re.compile(rf"@\|([A-Za-z0-9_]+)(>)?({TR.NUM})?\Z")
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".svg"}
TOP = ("v", "note", "fps", "size", "refs", "sources", "tracks", "chapters", "covers", "approval", "removed", "video")
KINDS = ("page", "image", "color", "clip", "film", "sound")
SOURCE_KEYS = {"page": ("clock",), "image": (), "color": (), "clip": ("sound", "sync"), "film": ("version", "sound"), "sound": ("role", "gain_db")}
HDR = ("smpte2084", "arib-std-b67")   # PQ, HLG: transfers an edit list does not draw (SDR only)
ROLES = ("voice", "ambience", "detail", "hero", "signal")   # the mix's buses: voice is the narration's, the rest the effects' classes
ENTRY = ("id", "src", "start", "end", "dur", "in", "out", "speed", "fit", "bg", "move", "hold", "sound", "transition", "inputs",
         "segment", "reads", "label", "unsure", "frame", "at", "why", "caption", "recipe", "seam", "quote", "snap", "note", "camera")
DRAW = {"page": "page", "image": "still", "color": "color", "clip": "clip", "film": "clip", None: "slate"}


class EditError(Exception):
    """The edit list does not resolve: code 2 (the file, its format, a reference) or 1 (the entries do not fit)."""

    def __init__(self, code, problems):
        super().__init__("; ".join(problems))
        self.code, self.problems = code, list(problems)


def r3(x):
    return round(x, 3) + 0.0   # milliseconds; + 0.0: never "-0.0"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def near(word, choices):
    got = difflib.get_close_matches(str(word), [str(c) for c in choices], n=1, cutoff=0.5)
    return f" (nearest: {got[0]})" if got else ""


def jd(x):
    return json.dumps(x, ensure_ascii=False)


def rate_text(r):
    """a frame rate as the resolved list keeps it: "25", "24000/1001" (tools/timegrid.py reads both)"""
    from timegrid import rate_of
    num, den = rate_of(r)
    return str(num) if den == 1 else f"{num}/{den}"


def probe(f):
    """{video: its stream, audio: bool, rate: "num/den", frames, duration} of a media file, or None; frames counted when
    the container does not say (a few seconds for a long file)"""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,nb_frames,color_range,"
                            "color_space,color_primaries,color_transfer:format=duration", "-of", "json", str(f)], capture_output=True, text=True, timeout=120)
        j = json.loads(r.stdout or "{}")
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    v = next((s for s in j.get("streams") or [] if s.get("codec_type") == "video"), None)
    out = {"video": v, "audio": any(s.get("codec_type") == "audio" for s in j.get("streams") or []),
           "duration": float((j.get("format") or {}).get("duration") or 0)}
    if v:
        try:
            out["rate"] = rate_text(v.get("r_frame_rate") or "0/1")
        except ValueError:
            return None
        n = v.get("nb_frames")
        if not str(n or "").isdigit():
            c = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries", "stream=nb_read_packets",
                                "-of", "csv=p=0", str(f)], capture_output=True, text=True)
            n = (c.stdout or "").strip()
        out["frames"] = int(n) if str(n).isdigit() else 0
    return out


# ---- where ----

def project_of(arg):
    """A project folder (one with edit.json, or a BRIEF.md), a name under projects/, or edit.json itself."""
    p = Path(arg).expanduser()
    if p.is_file() and p.name == FILE:
        return p.resolve().parent
    if p.is_dir():
        return p.resolve()
    import vhdraw
    try:
        return vhdraw.project_dir(arg)
    except vhdraw.Usage as e:
        raise EditError(2, [str(e)]) from None


def find(project):
    """<project>/edit.json, or None when the project has no edit list."""
    f = Path(project) / FILE
    return f if f.is_file() else None


# ---- reading edit.json ----

class Reader:
    """Reads and checks edit.json, collecting every problem: format ones (2) first, then the layout's (1)."""

    def __init__(self, project, doc=None, folding=False):
        self.project = Path(project).resolve()
        self.file = self.project / FILE
        self.p2, self.p1, self.notes, self.folding = [], [], [], folding   # folding: bin/vh edit init, shots.json still beside it
        if doc is None:
            try:
                raw = self.file.read_bytes()
            except OSError as e:
                raise EditError(2, [f"{FILE}: cannot be read ({e.strerror or e})"]) from None
            try:
                doc = json.loads(raw.decode("utf-8-sig"))
            except ValueError as e:
                raise EditError(2, [f"{FILE}: not valid JSON ({e})"]) from None
            self.sha = hashlib.sha256(raw).hexdigest()
        else:
            self.sha = hashlib.sha256(json.dumps(doc, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if not isinstance(doc, dict):
            raise EditError(2, [f"{FILE}: an object, {{\"v\": 1, \"fps\", \"size\", \"sources\", \"tracks\": [...]}} (engines/EDIT.md)"])
        self.doc = doc

    def bad(self, msg):
        self.p2.append(msg)

    def path_in(self, rel, what, inside=True):
        """A file named relative to edit.json, inside the project (what a browser loads: a page, an image) or anywhere (a
        sound, read by ffmpeg): its Path, or None (said)."""
        if not isinstance(rel, str) or not rel.strip():
            self.bad(f"{what}: a file path relative to {FILE}"); return None
        p = (self.project / rel).resolve()
        try:
            if inside:
                p.relative_to(self.project)
        except ValueError:
            self.bad(f"{what}: {rel} is outside the project (the pages are served from its folder, and nothing above it)"); return None
        if not p.is_file():
            self.bad(f"{what}: no such file {rel}"); return None
        return p

    def top(self):
        d = self.doc
        if (self.project / "shots.json").is_file() and not self.folding:
            self.bad(f"two shot tables here, {FILE} and shots.json: a project keeps one. The entries are the shots: fold shots.json's "
                     "into them by hand, then rename or delete shots.json")
        for k in d:
            if k not in TOP:
                self.bad(f"{FILE}: unknown key {k}{near(k, TOP)} (engines/EDIT.md lists them)")
        if d.get("v") != 1:
            self.bad(f"{FILE}: \"v\": 1 (the format's version), not {jd(d.get('v'))}")
        fps = d.get("fps")
        if not (isinstance(fps, int) and not isinstance(fps, bool) and 1 <= fps <= 240):
            self.bad(f"{FILE}: fps {jd(fps)}: a whole number of frames a second (24, 25, 30, 50, 60); 29.97 and the like are not taken")
            fps = None
        size = d.get("size")
        if not (isinstance(size, list) and len(size) == 2 and all(isinstance(x, int) and not isinstance(x, bool) and x > 0 for x in size)):
            self.bad(f"{FILE}: size {jd(size)}: [width, height] in CSS px, e.g. [1920, 1080]")
            size = None
        self.fps, self.size = fps, size
        if "note" in d and not isinstance(d["note"], str):
            self.bad(f"{FILE}: note: a line of text")
        if "video" in d and not isinstance(d["video"], str):
            self.bad(f"{FILE}: video: the path of the video storyboard plays")

    def refs(self):
        given = self.doc.get("refs") or {}
        if not isinstance(given, dict):
            self.bad(f"{FILE}: refs: an object naming the time sources (timeline, lead, music, timemap)"); given = {}
        for k in given:
            if k not in REF_KEYS:
                self.bad(f"{FILE}: refs.{k}: unknown{near(k, REF_KEYS)} (refs takes {', '.join(REF_KEYS)})")
        files = {}
        for k in ("timeline", "music", "timemap"):   # inside the project, as the sources are (and the pages that read them)
            if k in given:
                f = self.path_in(given[k], f"{FILE}: refs.{k}")
                if f is not None:
                    files[k] = str(f)
        at = files.get
        if len(files) < sum(k in given for k in ("timeline", "music", "timemap")):
            self.given_refs = given
            self.R = TR.Refs()
            return
        self.given_refs = given
        try:
            self.R = TR.Refs(timeline=at("timeline"), lead=given.get("lead", 0), music=at("music"), timemap=at("timemap"))
        except TR.RefError as e:
            self.bad(f"{FILE}: refs: {str(e).replace(str(self.project) + os.sep, '')}")
            self.R = TR.Refs()

    def sources(self):
        src = self.doc.get("sources")
        if not isinstance(src, dict):
            self.bad(f"{FILE}: sources: an object of {{key: source}} (a page, an image, a colour)"); src = {}
        self.src = {}
        for key, s in src.items():
            where = f"sources.{key}"
            if not KEY.match(key):
                self.bad(f"{where}: a key of letters, digits, _, . and -"); continue
            if not isinstance(s, dict):
                self.bad(f"{where}: an object, e.g. {{\"page\": \"ch1.html\", \"clock\": \"film\"}}"); continue
            kinds = [k for k in KINDS if k in s and k != "sound"] or (["sound"] if "sound" in s else [])   # footage's "sound" is its sound's settings
            if len(kinds) != 1:
                self.bad(f"{where}: one of {', '.join(KINDS)}" + (f", not {' and '.join(kinds)}" if kinds else "")); continue
            kind = kinds[0]
            for k in s:
                if k not in (kind, "asset", "sha256") + SOURCE_KEYS[kind]:
                    self.bad(f"{where}: {k} does not go with a {kind} source")
            if "asset" in s and not (isinstance(s["asset"], str) and s["asset"]):
                self.bad(f"{where}: asset: the id of its record in the asset ledger (bin/vh assets)")
            info = {"kind": kind}
            if kind == "page":
                f = self.path_in(s["page"], f"{where}.page")
                if f is not None and f.suffix.lower() not in (".html", ".htm"):
                    self.bad(f"{where}.page: {s['page']} is not a page (.html)")
                if s.get("clock") not in ("film", "local"):
                    self.bad(f"{where}: clock \"film\" (the page draws the film's time; its cues hang on the narration) or \"local\" "
                             "(it draws its own time from 0: a title card, a page from elsewhere): it has no default, as the wrong one shifts the whole picture")
                info.update(path=Path(s["page"]).as_posix() if isinstance(s.get("page"), str) else None, clock=s.get("clock"))
                if "sha256" in s and f is not None and f.is_file():   # the page file pinned (what it loads is the render's record)
                    info["sha256"] = sha256(f)
                    if s["sha256"] != info["sha256"]:
                        self.bad(f"{where}: {s['page']} is not the file pinned (sha256 {str(s['sha256'])[:12]}…, it is {info['sha256'][:12]}…)")
            elif kind == "image":
                f = self.path_in(s["image"], f"{where}.image")
                if f is not None and f.suffix.lower() not in IMAGE_EXT:
                    self.bad(f"{where}.image: {s['image']} is not an image the browser draws ({', '.join(sorted(IMAGE_EXT))})")
                info.update(path=Path(s["image"]).as_posix() if isinstance(s.get("image"), str) else None)
                if f is not None and f.is_file():
                    info["sha256"] = sha256(f)
                    if "sha256" in s and s["sha256"] != info["sha256"]:
                        self.bad(f"{where}: {s['image']} is not the file pinned (sha256 {str(s['sha256'])[:12]}…, it is {info['sha256'][:12]}…)")
            elif kind == "color":
                if "sha256" in s:
                    self.bad(f"{where}: sha256 pins a file, and a colour has none")
                if not (isinstance(s["color"], str) and COLOR.match(s["color"])):
                    self.bad(f"{where}: color {jd(s['color'])}: a hex colour, \"#000000\" or \"#000\"")
                info["color"] = s["color"].lower() if isinstance(s["color"], str) else None
            elif kind == "clip":
                got = self.clip(s["clip"], where)
                if got is None:
                    continue
                info.update(got)
            elif kind == "film":
                got = self.film(s, where)
                if got is None:
                    continue
                info.update(got)
            elif kind == "sound":
                f = self.path_in(s["sound"], f"{where}.sound", inside=False)
                if f is None:
                    continue
                pr = probe(f)
                if not pr or not pr.get("audio"):
                    self.bad(f"{where}: {s['sound']} has no sound ffmpeg can read"); continue
                info.update(path=self.rel(f), sha256=sha256(f), duration=pr["duration"])
            if kind in ("clip", "film", "sound") and "sha256" in s and s["sha256"] != info.get("sha256"):
                self.bad(f"{where}: not the file pinned (sha256 {str(s['sha256'])[:12]}…, it is {str(info.get('sha256'))[:12]}…)")
            if kind in ("clip", "film"):
                snd = self.sound_spec(s.get("sound"), f"{where}.sound") if "sound" in s else None
                if snd and not info.get("audio"):
                    self.bad(f"{where}: sound asked of {info['path']}, which has none")
                info["sound"] = snd
                if "sync" in s:
                    if not (isinstance(s["sync"], dict) and number(s["sync"].get("c")) and number(s["sync"].get("k", 1)) and s["sync"].get("k", 1) > 0):
                        self.bad(f"{where}: sync {{\"group\", \"c\": seconds, \"k\": 1}}: the clip's s = k·M + c on its group's clock M")
                    else:
                        info["sync"] = {"group": s["sync"].get("group"), "c": float(s["sync"]["c"]), "k": float(s["sync"].get("k", 1))}
            if kind == "sound":   # its role on the source (each entry can say its own)
                info["sound"] = self.sound_spec({"role": s["role"], **({"gain_db": s["gain_db"]} if "gain_db" in s else {})}, where) if "role" in s else None
            if s.get("asset"):
                info["asset"] = s["asset"]
            self.src[key] = info

    def rel(self, f):
        """a file's path as the resolved list keeps it: from the project when inside it, else as found (absolute)"""
        try:
            return Path(f).resolve().relative_to(self.project).as_posix()
        except ValueError:
            return str(Path(f).resolve())

    def clip(self, rel, where):
        """A clip source: a folder holding clip.json (bin/vh footage get writes it), or a video file probed as it is."""
        if not isinstance(rel, str) or not rel.strip():
            self.bad(f"{where}.clip: a clip folder (with clip.json) or a video file, relative to {FILE}"); return None
        p = (self.project / rel).resolve()
        if p.is_dir():
            cf = p / "clip.json"
            try:
                c = json.loads(cf.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                self.bad(f"{where}.clip: {rel}/clip.json cannot be read ({type(e).__name__}): a clip folder is what bin/vh footage get makes"); return None
            if not isinstance(c, dict) or c.get("v") != 1:
                self.bad(f"{where}.clip: {rel}/clip.json is not a clip's facts of version 1"); return None
            f = p / str(c.get("file") or "")
            if not f.is_file():
                self.bad(f"{where}.clip: {rel}/clip.json names {c.get('file')}, which is not there"); return None
            col = c.get("color")
            if not (isinstance(col, list) and len(col) == 4):
                self.bad(f"{where}.clip: {rel}/clip.json gives no colour tags (bin/vh footage get conforms them)"); return None
            if col[3] in HDR:
                self.bad(f"{where}.clip: {rel} is HDR ({col[3]}): an edit list draws SDR, and turning HDR into SDR is a creative choice "
                         "(bin/vh footage get --tonemap hable, or mobius, reinhard)"); return None
            try:
                rate = rate_text(c.get("rate"))
            except ValueError:
                self.bad(f"{where}.clip: {rel}/clip.json: rate {jd(c.get('rate'))} is not a frame rate"); return None
            if not (isinstance(c.get("frames"), int) and c["frames"] > 0):
                self.bad(f"{where}.clip: {rel}/clip.json gives no frame count"); return None
            audio = c.get("audio") if isinstance(c.get("audio"), dict) and (p / str(c["audio"].get("file") or "")).is_file() else None
            words = None
            if isinstance(c.get("words"), str) and c["words"]:
                words = self.rel(p / c["words"]) if (p / c["words"]).is_file() else None
                if words is None:
                    self.bad(f"{where}.clip: {rel}/clip.json names words {c['words']}, which is not there")
            h, frames = sha256(f), c["frames"]   # the file as it is now, never clip.json's word for it: what a chunk's key and bin/vh check compare
            if c.get("sha256") and c["sha256"] != h:   # clip.json describes another file: its rate and frames read from this one
                got = self.probe_rate(f, f"{where}.clip")
                if got is None:
                    return None
                rate, frames = got
                self.notes.append(("edit.changed", None, f"{where}: {self.rel(f)} is not the file its clip.json describes (another sha256): its rate "
                                   f"({rate}) and frames ({frames}) are read from the file; footage get or conform it again to bring clip.json up to date"))
            out = {"path": self.rel(f), "sha256": h, "rate": rate, "frames": frames, "size": c.get("size"),
                   "color": col, "folder": self.rel(p), **({"asset": c["asset"]} if c.get("asset") else {})}
            if audio:
                out["audio"] = {"path": self.rel(p / audio["file"]), "sha256": sha256(p / audio["file"])}
            if words:
                out["words"] = words
            if isinstance(c.get("sync"), dict):
                out["sync"] = {k: c["sync"][k] for k in ("group", "c", "k") if k in c["sync"]}
            if c.get("cuts"):
                out["cuts"] = c["cuts"]
            return out
        if p.is_file():
            return self.plain_clip(p, rel, where)
        self.bad(f"{where}.clip: no such clip folder or video {rel}"); return None

    def probe_rate(self, p, where):
        """(rate, frames) of a video file as ffprobe reads it (its packets counted), or None (said)"""
        sys.path.insert(0, str(HERE / "assets"))
        import footage as FT
        try:
            pr = FT.probe(p)
            if pr["video"] is None:
                raise FT.Failed("no video stream")
            rate, _ = FT.rate_of(pr["video"])
            return FT.frate(rate), int(pr["video"].get("nb_read_packets") or pr["video"].get("nb_frames") or 0)
        except FT.Failed as e:
            self.bad(f"{where}: {self.rel(p)}: {e}"); return None

    def plain_clip(self, p, rel, where):
        """A video file with no clip.json, taken as it is when it keeps the clip rules that decide which frame shows and
        how it looks (a constant rate, pts from 0, upright, square pixels, progressive, SDR; bin/vh footage get's own
        tests); refused otherwise, with the conform footage get would run. With no colour tags it is read as footage get
        reads it (BT.709 tv for HD, BT.601 for SD), said, and bin/vh edit check fails it until it is tagged."""
        sys.path.insert(0, str(HERE / "assets"))
        import footage as FT
        try:
            pr = FT.probe(p)
            v = pr["video"]
            rate, cfr = FT.rate_of(v) if v else (None, None)
            packets = FT.video_packets(p) if v else []
        except FT.Failed as e:
            self.bad(f"{where}.clip: {rel}: {e}"); return None
        if v is None:
            self.bad(f"{where}.clip: {rel} has no video stream"); return None
        col, assumed = FT.colour(v)
        off = FT.off_grid(packets, rate) if cfr and packets else 0.0   # every frame on the grid the picking counts in
        wrong = ([] if cfr else ["a variable frame rate"]) + \
                ([f"frames off a constant {FT.frate(rate)} fps grid (one {off:.2f} frames off: a variable rate its average hides)"] if off > 0.25 else []) + \
                (["pts not from 0"] if abs(float(v.get("start_time") or 0)) > 1e-4 or abs(float(pr["format"].get("start_time") or 0)) > 1e-4 else []) + \
                ([f"pixels not square ({v.get('sample_aspect_ratio')})"] if FT.sar_of(v) != 1 else []) + \
                ([f"rotated {FT.rotation(v)}°"] if FT.rotation(v) else []) + \
                ([f"interlaced ({v.get('field_order')})"] if v.get("field_order") not in (None, "progressive", "unknown") else []) + \
                ([f"HDR ({col[3]}), whose SDR is a creative choice (hable below is one; mobius, reinhard)"] if col[3] in HDR else [])
        cmd = None
        if wrong or assumed:
            try:
                argv = FT.conform_argv(p, p.with_name(p.stem + ".clip.mp4"), pr, "hable" if col[3] in HDR else None)[0]
                cmd = " ".join(shlex.quote(os.path.relpath(a, self.project) if a.startswith(str(p.parent)) else a) for a in argv)
            except FT.Failed:
                cmd = None
        if wrong:
            self.bad(f"{where}.clip: {rel} cannot be drawn as it is ({'; '.join(wrong)}): conform it as bin/vh footage get does, "
                     f"and point the source at the result{': ' + cmd if cmd else ''}"); return None
        frames = len(packets) or int(v.get("nb_read_packets") or v.get("nb_frames") or 0)
        if frames <= 0:
            self.bad(f"{where}.clip: {rel}: no frames counted"); return None
        out = {"path": self.rel(p), "sha256": sha256(p), "rate": FT.frate(rate), "frames": frames, "size": [v.get("width"), v.get("height")], "color": col}
        if assumed:
            out["assumed"] = assumed
            out["conform"] = cmd
            self.notes.append(("edit.untagged", None, f"{where}: {rel} has no colour tags ({'; '.join(assumed)}); bin/vh edit check fails it until "
                               "it is tagged: conform it as bin/vh footage get does" + (f" ({cmd})" if cmd else "")))
        if pr.get("audio"):
            out["audio"] = {"path": self.rel(p), "sha256": out["sha256"]}
        return out

    def film(self, s, where):
        """Another film: a version of another project's film (bin/vh versions), taken as a clip: no nested edit list."""
        proj, ver = s.get("film"), s.get("version")
        if not isinstance(proj, str) or not isinstance(ver, str) or not re.fullmatch(r"v\d+", ver or ""):
            self.bad(f"{where}: {{\"film\": \"../other-project\", \"version\": \"v7\"}}: a project and one of its versions (bin/vh versions)"); return None
        p = (self.project / proj).resolve()
        try:
            rec = json.loads((p / "out" / "versions" / "versions.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.bad(f"{where}: {proj} has no versions on record (bin/vh versions {proj})"); return None
        e = next((x for x in rec.get("versions") or [] if isinstance(x, dict) and x.get("id") == ver), None)
        if e is None or not e.get("file") or not (p / e["file"]).is_file():
            have = ", ".join(x.get("id") for x in rec.get("versions") or [] if isinstance(x, dict) and x.get("file") and (p / x["file"]).is_file())
            self.bad(f"{where}: {proj} has no film of version {ver} to take (it has {have or 'none'})"); return None
        f = p / e["file"]   # held to the rules of any video file taken as it is (a render of this repo keeps them)
        out = self.plain_clip(f, os.path.relpath(f, self.project), where)
        if out is not None:
            out["film"] = {"project": proj, "version": ver, "file": e["file"]}
        return out

    def sound_spec(self, v, where):
        """A sound's settings: {role, gain_db, fade: [in, out], lead, lag}; false or null: no sound (the default for footage)."""
        if v in (None, False):
            return None
        if not isinstance(v, dict):
            self.bad(f"{where}: {{\"role\": \"ambience\", \"gain_db\": -8}} (role: {', '.join(ROLES)}), or false"); return None
        bad = [k for k in v if k not in ("role", "gain_db", "fade", "lead", "lag")]
        if bad:
            self.bad(f"{where}: unknown {', '.join(bad)} (role, gain_db, fade, lead, lag)")
        if v.get("role") not in ROLES:
            self.bad(f"{where}: role {jd(v.get('role'))}: {', '.join(ROLES)} (voice joins the narration's bus, the others the effects' classes)"); return None
        fade = v.get("fade", [0.03, 0.03])
        fade = [fade, fade] if number(fade) else fade
        if not (isinstance(fade, list) and len(fade) == 2 and all(number(x) and x >= 0 for x in fade)):
            self.bad(f"{where}: fade: seconds, or [in, out]"); fade = [0.03, 0.03]
        out = {"role": v["role"], "gain_db": float(v.get("gain_db", 0)) if number(v.get("gain_db", 0)) else 0.0, "fade": [float(x) for x in fade],
               "lead": float(v.get("lead", 0)) if number(v.get("lead", 0)) else 0.0, "lag": float(v.get("lag", 0)) if number(v.get("lag", 0)) else 0.0}
        if out["lead"] < 0 or out["lag"] < 0:
            self.bad(f"{where}: lead and lag are seconds ≥ 0 (the sound in before the picture, out after it)")
        return out

    # a time: seconds, "0:12.5", a reference time_refs takes, or (chapters and covers) an entry's start or end
    def t(self, v, where, entries=None):
        if number(v):
            return float(v)
        if isinstance(v, str):
            s = TR.js_trim(v)
            m = ENTRY_REF.match(s)
            if s.startswith("@|"):
                if entries is None:
                    raise TR.RefError("a picture entry's own times do not hang on another entry (each one follows the one before it); "
                                      "@|id is for a sound track's entries, chapters, covers and the sound effects")
                if not m:
                    raise TR.RefError('not an entry cue: "@|id" (where the entry starts) or "@|id>" (where it ends), with an optional +0.3 or -0.2')
                if m[1] not in entries:
                    raise TR.RefError(f"no entry {m[1]}{near(m[1], entries)}")
                k = entries[m[1]][1 if m[2] else 0]
                return k / self.fps + (float(m[3]) if m[3] else 0)
            if not s.startswith("@"):
                import vhdraw
                x = vhdraw.seconds(s)
                if x is not None:
                    return x
        return self.R.t(v)

    def time(self, v, where, entries=None):
        try:
            x = self.t(v, where, entries)
        except TR.RefError as e:
            self.bad(f"{where} {jd(v)}: {e}"); return None
        if not number(x):
            self.bad(f"{where} {jd(v)}: not a time"); return None
        return x

    def entries(self):
        tracks = self.doc.get("tracks")
        if not (isinstance(tracks, list) and tracks and all(isinstance(x, dict) for x in tracks)):
            self.bad(f"{FILE}: tracks: a list of tracks, [{{\"id\": \"V1\", \"entries\": [...]}}]; the first is the picture"); return []
        out, ids = [], set()
        for ti, tr in enumerate(tracks):
            ents = tr.get("entries")
            if not isinstance(ents, list):
                self.bad(f"tracks[{ti}]: entries, a list"); continue
            if ti > 0 and any(isinstance(e, dict) and (self.src.get(e.get("src")) or {}).get("kind") != "sound" for e in ents):
                self.bad(f"tracks[{ti}] ({tr.get('id', '?')}): a track after the first takes sounds only (a sound source on each entry); "
                         "pictures over the first track come later")
                continue
            for i, e in enumerate(ents):
                where = f"{tr.get('id') or f'tracks[{ti}]'}[{i}]"
                if not isinstance(e, dict):
                    self.bad(f"{where}: an object, {{\"id\", \"src\", \"end\" …}}"); continue
                eid = e.get("id")
                if not (isinstance(eid, str) and ID.match(eid)):
                    self.bad(f"{where}: id {jd(eid)}: letters, digits and _ (S01)"); continue
                if eid in ids:
                    self.bad(f"{eid}: the id is used twice (every entry has its own; patch --shot and @|{eid} find it by it)"); continue
                ids.add(eid)
                for k in e:
                    if k not in ENTRY:
                        self.bad(f"{eid}: unknown field {k}{near(k, ENTRY)}")
                out.append((tr.get("id") or ("V1" if ti == 0 else f"A{ti}"), eid, e, ti))
        return out

    def resolve(self):
        self.top(); self.refs(); self.sources()
        rows = self.entries()
        fps, size = self.fps, self.size
        if fps is None or size is None:
            raise EditError(2, self.p2)
        ents, prev_end, prev, sounds, last_on = [], 0.0, None, [], {}
        for track, eid, e, ti in rows:
            src = e.get("src")
            if src is not None and src not in self.src:
                if src in (self.doc.get("sources") or {}):
                    continue   # said with its source
                self.bad(f"{eid}: src {jd(src)}: no such source{near(src, list(self.src))} (sources has {', '.join(self.src) or 'none'}; null for a slate)"); continue
            info = self.src.get(src) if src is not None else None
            kind = info["kind"] if info else None
            if ti > 0:   # a sound track
                snd = self.sound_entry(eid, e, info, last_on.get(ti, 0.0), track, {x["id"]: x["frames"] for x in ents})
                if snd:
                    sounds.append(snd); last_on[ti] = snd["end"]
                continue
            if kind == "sound":
                self.bad(f"{eid}: {src} is a sound: it goes on a track of its own after the first (the first track is the picture)"); continue
            clock = info.get("clock") if info else None
            local = kind == "page" and clock == "local"
            footage = kind in ("clip", "film")
            # what goes with what
            if kind != "page" and "hold" in e:
                self.bad(f"{eid}: hold is for a page (an image or a slate holds already; footage ends where it ends)")
            if "hold" in e and not isinstance(e["hold"], bool):
                self.bad(f"{eid}: hold: true or false")
            if not (local or footage):
                for k in ("in", "out", "speed"):
                    if k in e:
                        self.bad(f"{eid}: {k} is for footage, another film or a page on its own clock (\"clock\": \"local\")" +
                                 (": a film-clock page draws the film's time" if kind == "page" else ""))
            if kind not in ("image", "clip", "film"):
                for k in ("fit", "bg"):
                    if k in e:
                        self.bad(f"{eid}: {k} is for an image or footage")
            if "move" in e and kind != "image":
                self.bad(f"{eid}: move is for an image" + (" (a move over footage comes with pictures fed to a page, later)" if footage else ""))
            if "sound" in e and not footage:
                self.bad(f"{eid}: sound is for footage and other films (a sound of its own goes on a track after the first)")
            if "inputs" in e:
                self.bad(f"{eid}: inputs (pictures of other entries fed to a page) come later: one picture track, hard cuts")
            if "end" in e and "dur" in e:
                self.bad(f"{eid}: end or dur, not both")
            if "dur" in e and not (number(e["dur"]) and e["dur"] > 0):
                self.bad(f"{eid}: dur {jd(e['dur'])}: seconds, more than 0")
            # times
            start = self.time(e["start"], f"{eid}: start") if "start" in e else prev_end
            speed = e.get("speed", 1)
            if (local or footage) and not (number(speed) and 0.25 <= speed <= 4):
                self.bad(f"{eid}: speed {jd(speed)}: 0.25 to 4"); speed = 1
            tin = (self.source_time(e.get("in", 0), f"{eid}: in", info) if footage else self.local_time(e.get("in", 0), f"{eid}: in")) if (local or footage) else 0.0
            tout = (self.source_time(e["out"], f"{eid}: out", info) if footage else self.local_time(e["out"], f"{eid}: out")) if (local or footage) and "out" in e else None
            if tout is not None and tin is not None and tout <= tin:
                self.bad(f"{eid}: out {jd(e['out'])} is not after in {jd(e.get('in', 0))}")
            end = None
            if "end" in e:
                end = self.time(e["end"], f"{eid}: end")
            elif number(e.get("dur")) and start is not None:
                end = start + e["dur"]
            elif tout is not None and tin is not None and start is not None:
                end = start + (tout - tin) / speed
            elif not ("end" in e or "dur" in e or "out" in e):
                self.bad(f"{eid}: no length: write end (seconds or a cue such as \"@l4>\") or dur" +
                         (", or out" if local or footage else "") + (" (a page's own duration is not read: edit build opens no browser)" if kind == "page" else ""))
            if start is None or end is None:
                prev_end = end if end is not None else prev_end
                continue
            k0, k1 = frame_from(start, fps), frame_from(end, fps)
            if tout is not None and tin is not None and ("end" in e or "dur" in e):
                by_out = start + (tout - tin) / speed
                if abs(by_out - end) > 0.5 / fps + 1e-9:
                    self.p1.append(f"{eid} is said twice over: out {jd(e['out'])} makes it end at {by_out:.3f} s, " +
                                   (f"end {jd(e['end'])} at {end:.3f} s" if "end" in e else f"dur {jd(e['dur'])} at {end:.3f} s") +
                                   ": keep one of them")
            if k1 <= k0:
                self.p1.append(f"{eid} is shorter than a frame: {start:.3f}–{end:.3f} s" + (" (it ends before it starts)" if end < start else "") +
                               " (every entry has a frame or more)")
            pk = prev["frames"][1] if prev else 0
            if k0 > pk:
                gap = (k0 - pk) / fps
                self.p1.append((f"a gap between {prev['id']} and {eid}" if prev else f"{eid} starts at {start:.3f} s, not at 0") +
                               f": frames {pk}–{k0 - 1} ({gap:.3f} s) have nothing to draw. Let {eid} follow (leave out its start), "
                               "or put a colour entry there for a black")
            elif k0 < pk:
                self.p1.append(f"{eid} overlaps {prev['id']} by {pk - k0} frame{'s' * (pk - k0 != 1)} ({(pk - k0) / fps:.3f} s): "
                               f"{prev['id']} ends at frame {pk} ({pk / fps:.3f} s), {eid} starts at {start:.3f} s (frame {k0}). "
                               f"One picture track has one entry a frame: let {eid} follow (leave out its start)")
            row = {"id": eid, "track": track, "src": src, "kind": kind or "slate"}
            if clock:
                row["clock"] = clock
            row.update(frames=[k0, max(k0, k1)], start=r3(k0 / fps), end=r3(max(k0, k1) / fps))
            if local:
                row.update({"in": r3(tin or 0)}, speed=speed)
            if kind == "page":
                row["hold"] = bool(e.get("hold"))
            if kind == "image":
                row.update(self.framing(eid, e))
            if footage and tin is not None:
                row.update(self.footage_frames(eid, e, info, tin, speed, k0, max(k0, k1)))
                row.update(self.framing(eid, {k: v for k, v in e.items() if k != "move"}))
                snd = self.sound_spec(e["sound"], f"{eid}: sound") if "sound" in e else info.get("sound")
                if snd:
                    if not info.get("audio"):
                        self.bad(f"{eid}: sound asked of {info['path']}, which has none")
                    elif speed != 1:
                        self.bad(f"{eid}: footage with its sound plays at speed 1 (the sound is not stretched): speed 1, or \"sound\": false")
                    else:
                        sounds.append(self.footage_sound(eid, track, src, info, row, snd))
            ref = {k: e[k] for k in ("start", "end", "dur", "in", "out") if k in e}
            if ref:
                row["ref"] = ref
            if "at" in e:
                a = self.time(e["at"], f"{eid}: at")
                if a is not None:
                    row["at"] = r3(a)
            for k in ("segment", "reads", "label", "unsure", "frame", "why", "caption", "recipe", "seam", "quote", "snap", "note", "transition", "camera"):
                if k in e:
                    row[k] = e[k]
            if isinstance(e.get("transition"), dict) and number(e["transition"].get("duration")) and e["transition"]["duration"] > 0:
                row["transition_draw"] = True   # a transition to draw (not a note): render refuses it between two sources
            ents.append(row)
            prev, prev_end = row, end
        placed = sorted((x for x in sounds if "start" in x), key=lambda x: (x["track"], x["start"], x["end"]))   # a sound track's entries, by time
        for a, b in zip(placed, placed[1:]):
            if a["track"] == b["track"] and b["start"] < a["end"] - 1e-9:
                self.p1.append(f"{b['entry']} overlaps {a['entry']} on {a['track']} ({a['start']:.3f}–{a['end']:.3f} s and {b['start']:.3f}–{b['end']:.3f} s): "
                               "put one of them on a track of its own")
        if self.p2:
            raise EditError(2, self.p2)
        if not ents:
            raise EditError(2, [f"{FILE}: no entries on the first track"])
        frames = ents[-1]["frames"][1]
        for s in sounds:   # a sound that runs past the film is cut there
            if s["film"][0] >= frames / fps - 1e-9:
                self.p1.append(f"{s['entry']}: its sound starts at {s['film'][0]:.3f} s, after the film ends ({frames / fps:.3f} s)")
        by = {x["id"]: x["frames"] for x in ents}
        chapters = []
        for i, c in enumerate(self.doc.get("chapters") or []):
            if not (isinstance(c, dict) and "t" in c):
                self.bad(f"chapters[{i}]: {{\"t\": a time or \"@|S04\", \"title\": …}}"); continue
            t = self.time(c["t"], f"chapters[{i}].t", by)
            if t is not None:
                chapters.append({"t": r3(t), "title": str(c.get("title", "")), **({"id": str(c["id"])} if c.get("id") is not None else {}),
                                 **({"ref": c["t"]} if not number(c["t"]) else {})})
        covers = []
        for i, c in enumerate(self.doc.get("covers") or []):
            if not (isinstance(c, dict) and "t" in c and isinstance(c.get("id"), str)):
                self.bad(f"covers[{i}]: {{\"id\", \"t\": a time or \"@|S04\", \"title\"?}}"); continue
            t = self.time(c["t"], f"covers[{i}].t", by)
            if t is not None:
                covers.append({"id": c["id"], "t": r3(t), **({"title": str(c["title"])} if c.get("title") is not None else {}),
                               **({"ref": c["t"]} if not number(c["t"]) else {})})
        if self.p2:
            raise EditError(2, self.p2)
        if self.p1:
            raise EditError(1, self.p1)
        return self.document(ents, frames, chapters, covers, sounds)

    def source_time(self, v, where, info):
        """Footage's own time (in, out): seconds, {"f": n} (its frame n), or {"sync": M} (its group's clock: s = k·M + c)."""
        if isinstance(v, dict) and set(v) == {"f"} and isinstance(v["f"], int) and not isinstance(v["f"], bool) and v["f"] >= 0:
            from timegrid import rate_of
            num, den = rate_of(info["rate"])
            return v["f"] * den / num
        if isinstance(v, dict) and set(v) == {"sync"} and number(v["sync"]):
            sy = info.get("sync")
            if not sy:
                self.bad(f"{where} {jd(v)}: {info['path']} has no sync (bin/vh footage sync, or the source's \"sync\")"); return None
            t = sy.get("k", 1) * v["sync"] + sy["c"]
            if t < -1e-9:   # this camera was not rolling yet at M
                self.bad(f"{where} {jd(v)}: falls before the start of {info['path']} (s = {sy.get('k', 1):g}·{v['sync']:g} + {sy['c']:g} = {t:.3f} s): "
                         "start the entry later, where the clip has pictures"); return None
            return max(0.0, t)
        if number(v) and v >= 0:
            return round(float(v), 3)
        self.bad(f"{where} {jd(v)}: the footage's own seconds (≥ 0), {{\"f\": n}} (its frame n) or {{\"sync\": M}} (its group's clock)")
        return None

    def footage_frames(self, eid, e, info, tin, speed, k0, k1):
        """Where footage's frames come from: its first one (j0, frame_at of in, or {"f": n} as it is) and the rule
        j(k) = j0 + floor((k − K0) · speed · rate / fps + 1e-6); the clip must hold every one of them."""
        from timegrid import frame_at, rate_of
        num, den = rate_of(info["rate"])
        j0 = e["in"]["f"] if isinstance(e.get("in"), dict) and "f" in e["in"] else frame_at(tin, info["rate"])
        if j0 < 0:   # never drawn from before the clip's first frame (a decoder starts there whatever was asked)
            self.bad(f"{eid}: its first frame would be clip frame {j0}, before {info['path']} starts"); j0 = 0
        last = j0 + int(math.floor((k1 - 1 - k0) * speed * num / den / self.fps + 1e-6))
        if j0 >= info["frames"] or last >= info["frames"]:
            have = info["frames"] * den / num
            self.p1.append(f"{eid} needs {info['path']} up to frame {last} ({(last + 1) * den / num:.3f} s), and it has {info['frames']} frames "
                           f"({have:.3f} s): move its in earlier, or shorten it")
        out = {"in": r3(tin), "j0": j0, "speed": speed, "rate": info["rate"]}
        if num / den != self.fps * (1 if speed == 1 else speed):
            r = num / den / speed
            each = round(1 / abs(self.fps / r - 1)) if abs(self.fps / r - 1) > 1e-9 else 0
            self.notes.append(("edit.rate", eid, f"{eid} {e.get('src')}: {info['rate']} fps" + (f" at speed {speed}" if speed != 1 else "") +
                               f" into {self.fps} fps: {'one frame shown twice' if r < self.fps else 'one frame left out'} in about every {each or 1} "
                               "(fine for most footage; say so in DECISIONS.md if not)"))
        return out

    def footage_sound(self, eid, track, src, info, row, snd):
        """footage's own sound, placed with its picture: from the film time of its first frame, its own time from the
        frame it shows there; lead and lag move it in before and out after"""
        from timegrid import rate_of
        num, den = rate_of(info["rate"])
        t0, t1 = row["frames"][0] / self.fps, row["frames"][1] / self.fps
        sin = row["j0"] * den / num - snd["lead"]
        if sin < -1e-9:
            self.bad(f"{eid}: its sound's lead ({snd['lead']} s) reaches before the start of {info['path']}")
        return {"entry": eid, "track": track, "src": src, "file": info["audio"]["path"], "sha256": info["audio"].get("sha256"),
                "film": [r3(t0 - snd["lead"]), r3(t1 + snd["lag"])], "in": r3(max(0.0, sin)), "role": snd["role"], "gain_db": snd["gain_db"],
                "fade": snd["fade"], "lead": snd["lead"], "lag": snd["lag"], **({"words": info["words"]} if info.get("words") else {})}

    def sound_entry(self, eid, e, info, follows, track, picture):
        """an entry on a sound track: its source's sound from in, placed from start to end (or for its length); its start
        and end can hang on the picture's entries ("@|S04-0.4": the first track is resolved before it, so no loop)"""
        if info is None or info["kind"] != "sound":
            self.bad(f"{eid}: a sound track's entry takes a sound source"); return None
        for k in e:
            if k in ("fit", "bg", "move", "hold", "speed", "transition", "inputs"):
                self.bad(f"{eid}: {k} is not for a sound")
        if "end" in e and "dur" in e:
            self.bad(f"{eid}: end or dur, not both")
        if "dur" in e and not (number(e["dur"]) and e["dur"] > 0):
            self.bad(f"{eid}: dur {jd(e['dur'])}: seconds, more than 0"); return None
        snd = self.sound_spec(e["sound"], f"{eid}: sound") if "sound" in e else info.get("sound")
        if not snd:
            self.bad(f"{eid}: no role for its sound: \"sound\": {{\"role\": …}} on the entry or \"role\" on {e.get('src')}"); return None
        start = self.time(e["start"], f"{eid}: start", picture) if "start" in e else follows
        tin = self.local_time(e.get("in", 0), f"{eid}: in")
        tout = self.local_time(e["out"], f"{eid}: out") if "out" in e else None
        if start is None or tin is None:
            return None
        if "end" in e:
            end = self.time(e["end"], f"{eid}: end", picture)
        elif number(e.get("dur")):
            end = start + e["dur"]
        elif tout is not None:
            end = start + tout - tin
        else:
            end = start + info["duration"] - tin
        if end is None:
            return None
        if end <= start:
            self.p1.append(f"{eid}: its sound ends at {end:.3f} s, not after it starts ({start:.3f} s)"); return None
        if tin + (end - start) > info["duration"] + 0.5 / self.fps:
            self.p1.append(f"{eid} needs {info['path']} up to {tin + end - start:.3f} s, and it is {info['duration']:.3f} s long")
        return {"entry": eid, "track": track, "src": e.get("src"), "file": info["path"], "sha256": info["sha256"],
                "film": [r3(start - snd["lead"]), r3(end + snd["lag"])], "in": r3(max(0.0, tin - snd["lead"])), "role": snd["role"],
                "gain_db": snd["gain_db"], "fade": snd["fade"], "lead": snd["lead"], "lag": snd["lag"], "start": r3(start), "end": r3(end),
                **({k: e[k] for k in ("why", "note") if k in e})}

    def local_time(self, v, where):
        """A page's own time (in, out): seconds, or {"f": n}, its frame n at the film's rate."""
        if isinstance(v, dict) and set(v) == {"f"} and isinstance(v["f"], int) and not isinstance(v["f"], bool) and v["f"] >= 0:
            return v["f"] / self.fps
        if number(v) and v >= 0:
            return round(float(v), 3)
        self.bad(f"{where} {jd(v)}: the page's own seconds (≥ 0), or {{\"f\": n}}, its frame n")
        return None

    def framing(self, eid, e):
        out = {"fit": e.get("fit", "contain"), "bg": e.get("bg", "#000000")}
        if out["fit"] not in ("contain", "cover"):
            self.bad(f"{eid}: fit {jd(out['fit'])}: contain (the whole picture, the rest bg) or cover (it fills the frame)")
        if not (isinstance(out["bg"], str) and COLOR.match(out["bg"])):
            self.bad(f"{eid}: bg {jd(out['bg'])}: a hex colour")
        elif len(out["bg"]) == 4:   # #rgb as #rrggbb: what the pages and ffmpeg's pad both take
            out["bg"] = "#" + "".join(c * 2 for c in out["bg"][1:])
        if isinstance(out["bg"], str):
            out["bg"] = out["bg"].lower()
        if "move" in e:
            m = e["move"]
            ok = isinstance(m, dict) and all(isinstance(m.get(k), list) and len(m[k]) == 3 and all(number(x) for x in m[k]) for k in ("from", "to"))
            if ok:
                for k in ("from", "to"):
                    cx, cy, z = m[k]
                    if not (0 <= cx <= 1 and 0 <= cy <= 1 and z >= 1):
                        self.bad(f"{eid}: move.{k} {jd(m[k])}: [cx, cy, zoom], the centre 0–1 across and down the picture, zoom ≥ 1"); ok = False
                if m.get("ease", "linear") not in ("linear", "inOut"):
                    self.bad(f"{eid}: move.ease {jd(m.get('ease'))}: linear or inOut"); ok = False
                for k in m:
                    if k not in ("from", "to", "ease"):
                        self.bad(f"{eid}: move.{k}: unknown (from, to, ease)"); ok = False
            else:
                self.bad(f"{eid}: move: {{\"from\": [cx, cy, zoom], \"to\": [cx, cy, zoom], \"ease\": \"linear\" or \"inOut\"}}")
            if ok:
                out["move"] = {"from": [float(x) for x in m["from"]], "to": [float(x) for x in m["to"]], "ease": m.get("ease", "linear")}
        return out

    def document(self, ents, frames, chapters, covers, sounds=()):
        fps = self.fps
        files = {}
        for e in list(ents) + list(sounds):
            k = e.get("src")
            if k is not None and k not in files:
                files[k] = {x: v for x, v in self.src[k].items() if x != "sound"}
        runs = []
        for e in ents:
            r = {"frames": list(e["frames"]), "draw": DRAW[None if e["kind"] == "slate" else e["kind"]], "entry": e["id"]}
            if e["kind"] in ("clip", "film"):   # footage, decoded by ffmpeg: frame k shows j0 + floor((k − K0)·speed·rate/fps + 1e-6)
                f = files[e["src"]]
                r.update(src=e["src"], path=f["path"], sha256=f.get("sha256"), rate=f["rate"], nframes=f["frames"], size=f.get("size"),
                         color=f["color"], j0=e["j0"], speed=e["speed"], fit=e["fit"], bg=e["bg"])
            elif e["kind"] == "page":
                r.update(src=e["src"], path=files[e["src"]]["path"], clock=e["clock"], hold=e["hold"])
                if e["clock"] == "local":
                    r.update({"in": e["in"]}, speed=e["speed"])
            elif e["kind"] == "image":
                f = files[e["src"]]
                r.update(src=e["src"], path=f["path"], sha256=f.get("sha256"), fit=e["fit"], bg=e["bg"], **({"move": e["move"]} if "move" in e else {}))
            elif e["kind"] == "color":
                r.update(src=e["src"], color=files[e["src"]]["color"])
            else:
                reads = e.get("reads")
                r["slate"] = {"id": e["id"], "segment": str(e.get("segment") or ""), "label": str(e.get("label") or ""),
                              "reads": [str(x) for x in reads] if isinstance(reads, list) else ([str(reads)] if reads else []),
                              "unsure": None if e.get("unsure") in (None, False) else ("" if e.get("unsure") is True else str(e["unsure"]))}
            runs.append(r)
        kind_of = {str((self.project / v).resolve()): k for k, v in self.given_refs.items() if k in ("timeline", "music", "timemap") and isinstance(v, str)}
        sources = [{"kind": kind_of.get(s["path"], "ref"), "path": os.path.relpath(s["path"], self.project).replace(os.sep, "/"), "sha256": s["sha256"]}
                   for s in self.R.sources]
        doc = {"v": 1, "note": "bin/vh edit build: what edit.json resolves to; bin/vh render, patch and the shot tools read this",
               "edit": {"path": FILE, "sha256": self.sha}, "refs": sources, "fps": fps, "size": list(self.size),
               "frames": frames, "duration": r3(frames / fps), "files": files, "entries": ents, "runs": runs,
               "cuts": {e["id"]: [e["start"], e["end"]] for e in ents},
               "slates": [e["id"] for e in ents if e["kind"] == "slate"]}
        if sounds:   # the sounds the edit list places (footage's own, the sound tracks'): bin/vh mix … edit= takes them
            doc["sound"] = sorted(sounds, key=lambda s: (s["film"][0], s["entry"]))
        if chapters:
            doc["chapters"] = chapters
        if covers:
            doc["covers"] = covers
        if isinstance(self.doc.get("video"), str):
            doc["video"] = self.doc["video"]
        if self.notes:
            doc["notes"] = [{"kind": k, "entry": e, "text": t} for k, e, t in self.notes]
        return doc


def resolve(project, doc=None):
    """edit.json (or doc, an edit list already read) → the resolved document; raises EditError. Writes nothing."""
    return Reader(project, doc).resolve()


# ---- what changed since the last build ----

def changes(old, new):
    """Lines saying what moved, changed its length or its source, came or went since the old resolved document."""
    if not old or not isinstance(old.get("entries"), list):
        return []
    fps = new["fps"]
    o = {e.get("id"): e for e in old["entries"] if isinstance(e, dict)}
    n = {e["id"]: e for e in new["entries"]}
    src_of = lambda doc, e: (e.get("src"), json.dumps((doc.get("files") or {}).get(e.get("src")), sort_keys=True))   # noqa: E731
    moved, out = [], []   # [first id, last id, frames moved, index of the last]: a row moved by the same amount is one line
    for i, e in enumerate(new["entries"]):
        p = o.get(e["id"])
        if p is None or not isinstance(p.get("frames"), list):
            continue
        d = e["frames"][0] - p["frames"][0]
        if d:
            if moved and moved[-1][2] == d and moved[-1][3] == i - 1:
                moved[-1][1] = e["id"]; moved[-1][3] = i
            else:
                moved.append([e["id"], e["id"], d, i])
    why = ""
    oref = {r.get("path"): r.get("sha256") for r in old.get("refs") or [] if isinstance(r, dict)}
    nref = {r["path"]: r["sha256"] for r in new.get("refs") or []}
    changed_refs = [p for p in nref if p in oref and oref[p] != nref[p]]
    if changed_refs:
        why = f" ({', '.join(changed_refs)} changed)"
    for a, b, d, _ in moved:
        out.append(f"{a if a == b else f'{a}–{b}'} moved {'+' if d > 0 else '−'}{abs(d) / fps:.3f} s ({'+' if d > 0 else '−'}{abs(d)} frames){why}")
    for e in new["entries"]:
        p = o.get(e["id"])
        if p is None:
            out.append(f"{e['id']} is new"); continue
        if isinstance(p.get("frames"), list) and (e["frames"][1] - e["frames"][0]) != (p["frames"][1] - p["frames"][0]):
            dl = (e["frames"][1] - e["frames"][0]) - (p["frames"][1] - p["frames"][0])
            out.append(f"{e['id']} is {'longer' if dl > 0 else 'shorter'} by {abs(dl) / fps:.3f} s ({abs(dl)} frames)")
        if src_of(old, p) != src_of(new, e):
            out.append(f"{e['id']}'s source changed ({p.get('src') or 'a slate'} → {e['src'] or 'a slate'})" if p.get("src") != e["src"]
                       else f"{e['id']}'s source {e['src']} changed")
    for i in o:
        if i not in n:
            out.append(f"{i} is gone")
    return out


# ---- the report ----

def summary(doc):
    kinds = {}
    for e in doc["entries"]:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
    names = {"page": ("page", "pages"), "image": ("image", "images"), "color": ("colour", "colours"), "slate": ("slate", "slates"),
             "clip": ("clip", "clips"), "film": ("film", "films")}
    parts = [f"{n} {names[k][n != 1]}" for k, n in kinds.items()]
    snd = doc.get("sound") or []
    return (f"{doc['duration']} s · {doc['frames']} frames at {doc['fps']} fps · {len(doc['entries'])} entr{'y' if len(doc['entries']) == 1 else 'ies'} on V1 ({', '.join(parts)})"
            + (f" · {len(snd)} sound{'s' * (len(snd) != 1)} placed ({', '.join(sorted({s['role'] for s in snd}))})" if snd else ""))


def notes(doc):
    """[(kind, entry, line)]: the slates left, the transitions not drawn yet, what the build noticed (footage at another rate)."""
    out = []
    for e in doc["entries"]:
        if e["kind"] == "slate":
            out.append(("edit.slate", e["id"], f"{e['id']}: a slate, no source yet: bin/vh check and deliver refuse the film until it has one"))
        if e.get("transition_draw"):
            out.append(("edit.transition", e["id"], f"{e['id']}: a transition ({e['transition'].get('type', '?')} {e['transition'].get('duration')} s) is not drawn yet: "
                        "bin/vh render draws a hard cut where a slate is on either side, and stops between two sources"))
    for n in doc.get("notes") or []:
        out.append((n["kind"], n["entry"], n["text"]))
    return out


def write_resolved(project, doc):
    f = Path(project) / RESOLVED
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f".{f.name}.{os.getpid()}")
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, f)
    return f


def read_resolved(project):
    try:
        d = json.loads((Path(project) / RESOLVED).read_text(encoding="utf-8"))
        return d if isinstance(d, dict) else None
    except (OSError, ValueError):
        return None


def narration(doc, project):
    """(its language, the timeline as read) of the edit list's narration: the language from the file's name
    (timeline.<lang>.json), else its "lang", else zh. What the merged timeline, bin/vh mix … edit= and captions all go by."""
    tl = next((r for r in doc.get("refs") or [] if r.get("kind") == "timeline"), None)
    base = {"segments": []}
    if tl:
        try:
            base = json.loads((Path(project) / tl["path"]).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            base = {"segments": []}
    m = re.search(r"timeline\.([A-Za-z-]+)\.json$", tl["path"]) if tl else None
    return (m.group(1) if m else None) or (base.get("lang") if isinstance(base, dict) else None) or "zh", base


def merged_path(doc, project):
    """out/edit.timeline.<lang>.json, in the narration's language"""
    return Path(project) / "out" / f"edit.timeline.{narration(doc, project)[0]}.json"


CJK = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\uac00-\ud7af]")


def words_text(ws):
    """words joined as they are written: Chinese, Japanese, Korean ones run on, a space between two that are not"""
    out = ""
    for w in (str(x.get("w", "")) for x in ws):
        if out and w and not CJK.match(out[-1]) and not CJK.match(w[0]):
            out += " "
        out += w
    return out


def merged_timeline(doc, project):
    """The narration with the words of the footage whose sound is a voice, in film seconds, the shape bin/vh tts writes
    (each line {id, start, end, text, words: [{w, start, end}]}): what bin/vh mix (its timeline= by default with edit=),
    captions and qa read in an edit list's film. A footage's lines come from its clip's words file (clip.json's "words",
    the clip's own seconds, the same shape): a word is kept when it starts inside what the entry plays, moved by
    film start − in; the line's id is <entry>_<n>. None when nothing placed is a voice."""
    voice = [s for s in doc.get("sound") or [] if s["role"] == "voice"]
    if not voice:
        return None, None, []
    lang, base = narration(doc, project)
    side, said = ("zh" if lang.startswith("zh") else "en"), []   # the key a line's text goes under, as bin/vh tts writes it
    lead = 0.0
    try:
        lead = float(json.loads((Path(project) / FILE).read_text(encoding="utf-8")).get("refs", {}).get("lead", 0) or 0)
    except (OSError, ValueError, TypeError, AttributeError):
        pass
    shift = lambda w, d: {**w, "start": r3(w["start"] + d), "end": r3(w.get("end", w["start"]) + d)}   # noqa: E731
    lines = [{**s, "start": r3(s["start"] + lead), "end": r3(s["end"] + lead), **({"words": [shift(w, lead) for w in s["words"] if number(w.get("start"))]} if isinstance(s.get("words"), list) else {})}
             for s in base.get("segments") or [] if isinstance(s, dict) and number(s.get("start")) and number(s.get("end"))]
    for v in voice:
        if not v.get("words"):
            continue
        try:
            wd = json.loads((Path(project) / v["words"]).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        d, n = v["film"][0] - v["in"], 0
        span = v["in"] + (v["film"][1] - v["film"][0])

        lo = max(v["in"], -d)   # what plays, in the clip's seconds: from the film's start at the earliest (a lead before 0 is cut off)

        def kept(w):   # a word across a cut stays when more than half of it is inside what plays; then cut to it
            a, b = w["start"], w.get("end", w["start"]) if number(w.get("end")) else w["start"]
            inside = min(b, span) - max(a, lo)
            if not (inside > (b - a) / 2 or (b <= a and lo <= a < span)):
                return None
            return {**w, "start": max(a, lo), "end": min(max(a, b), span)}
        for s in wd.get("segments") or []:
            every = [w for w in s.get("words") or [] if isinstance(w, dict) and number(w.get("start"))]
            ws = [k for k in (kept(w) for w in every) if k]
            if not ws:
                continue
            n += 1
            text = words_text(ws)
            own = wd.get("lang") if isinstance(wd.get("lang"), str) else ("zh" if CJK.search(text) else "en")   # the language spoken
            own = "zh" if own.startswith("zh") else "en"
            whole = len(ws) == len(every)
            line = {"id": f"{v['entry']}_{n}", "start": r3(ws[0]["start"] + d), "end": r3(ws[-1]["end"] + d), "text": text, own: text,
                    **{k: s[k] for k in ("zh", "en") if k != own and isinstance(s.get(k), str) and whole},   # a translation, when all of it plays
                    "words": [shift(w, d) for w in ws], "from": v["entry"]}
            if side not in line:   # spoken in another language than the film's, with no translation: its captions show it as spoken
                line[side] = text
                said.append(f"{line['id']} is spoken in {own}, with no {side} for it in {v['words']} (a \"{side}\" on the segment): "
                            f"the {side} captions show it as spoken")
            lines.append(line)
    lines.sort(key=lambda s: (s["start"], s["id"]))
    out = {k: v for k, v in base.items() if k != "segments"} if isinstance(base, dict) else {}
    out.update(lang=lang, note="bin/vh edit build: the narration with the words of the footage placed as a voice, in film seconds", duration=doc["duration"], segments=lines)
    return out, merged_path(doc, project), said


def build(project, write=True):
    """→ (the resolved document, the lines said). Writes out/edit.resolved.json when write (and the merged timeline,
    out/edit.timeline.<lang>.json, when the edit list places a voice)."""
    doc = resolve(project)
    said = [line for kind, _, line in notes(doc) if kind != "edit.slate"]
    if doc["slates"]:
        s = doc["slates"]
        said.insert(0, (f"{s[0]}: a slate" if len(s) == 1 else f"{len(s)} slates ({', '.join(s[:8])}{' …' if len(s) > 8 else ''})") +
                    ", no source yet: bin/vh check and deliver refuse the film until " + ("it has one" if len(s) == 1 else "each has one"))
    moved = changes(read_resolved(project), doc)
    if moved:
        said.append("since the last build: " + "; ".join(moved))
    if write:
        write_resolved(project, doc)
        tl, f, spoken = merged_timeline(doc, project)
        said += spoken
        if tl is not None:
            tmp = f.with_name(f".{f.name}.{os.getpid()}")
            tmp.write_text(json.dumps(tl, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            os.replace(tmp, f)
            n = sum(1 for s in tl["segments"] if s.get("from"))
            said.append(f"{f.relative_to(Path(project)).as_posix()}: the narration with {n} line{'s' * (n != 1)} of the footage's words "
                        "(bin/vh mix … edit= takes it as its timeline, captions and qa read it)")
            said += voices_at_once(tl["segments"])
    return doc, said


def voices_at_once(lines):
    """the footage's lines that play over another voice (the narration or other footage): two voices at once, which
    captions cannot show and nobody follows; the merged timeline keeps them, its lint calls them out of order"""
    out = []
    for i, a in enumerate(lines):
        for b in lines[i + 1:]:
            if b["start"] >= a["end"]:
                break
            if (a.get("from") or b.get("from")) and a.get("from") != b.get("from"):
                out.append(f"{a['id']} ({a['start']:.3f}–{a['end']:.3f} s) and {b['id']} ({b['start']:.3f}–{b['end']:.3f} s) play at once: "
                           "two voices; move the cut, or give the footage's sound another role")
    return out[:3] + ([f"… {len(out) - 3} more"] if len(out) > 3 else [])


# ---- the shots it gives the shot tools ----

def shot_rows(doc):
    """The entries as shots.json rows (storyboard, rhythm, the review desk, thumbs): film seconds, every field kept."""
    rows = []
    for e in doc["entries"]:
        r = {k: v for k, v in e.items() if k not in ("frames", "ref", "track", "transition_draw")}
        rows.append(r)
    return rows


# ---- init ----

def brief_spec(project):
    """(fps, [w, h]) from the BRIEF's Output line, each None when it does not say (or says {placeholders})."""
    try:
        import speccheck
        text = (Path(project) / "BRIEF.md").read_text(encoding="utf-8")
        line = speccheck.spec_line(text, "Output") or ""
    except (OSError, ImportError):
        return None, None
    m = re.search(r"(\d{3,5})\s*[x×]\s*(\d{3,5})", line)
    f = re.search(r"(\d+(?:\.\d+)?)\s*fps", line, re.I)
    fps = float(f.group(1)) if f else None
    return (int(fps) if fps and fps.is_integer() else fps), ([int(m.group(1)), int(m.group(2))] if m else None)


def init(project, fps=None, size=None):
    project = Path(project)
    if find(project):
        raise EditError(2, [f"{FILE} is there already: edit it, or move it away to fold shots.json in again"])
    sj = project / "shots.json"
    if not sj.is_file():
        raise EditError(2, ["no shots.json to fold in: write edit.json by hand (engines/EDIT.md has the format)"])
    try:
        data = json.loads(sj.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise EditError(2, [f"shots.json: not readable JSON ({e})"]) from None
    import vhdraw
    try:
        shots, meta = vhdraw.parse_shots(data, sj)   # its own checks: start and end, unique ids
    except SystemExit as e:
        raise EditError(2, [str(e)]) from None
    raw = {str(s.get("id") or f"S{i + 1:02d}"): s for i, s in enumerate(data.get("shots") if isinstance(data, dict) else data)}
    bfps, bsize = brief_spec(project)
    fps = fps or bfps or 30
    if not (isinstance(fps, int) or (isinstance(fps, float) and fps.is_integer())):
        raise EditError(2, [f"the BRIEF's Output says {fps} fps: an edit list takes whole frame rates (--fps 30)"])
    fps, size = int(fps), size or bsize or [1920, 1080]
    entries, prev = [], 0.0
    for s in shots:
        r = raw.get(s["id"], {})
        e = {"id": s["id"], "src": None}
        if abs(s["start"] - prev) > 1e-6:
            e["start"] = s["start"]
        e["end"] = s["end"]
        for k in ("segment", "reads", "label", "unsure", "frame", "at", "why", "caption", "recipe", "seam", "transition", "note", "camera"):
            for alias in {"segment": ("segment", "stage", "section"), "reads": ("reads", "read", "what"),
                          "unsure": ("unsure", "flag", "risk"), "frame": ("frame", "image"), "at": ("at", "snapshot")}.get(k, (k,)):
                if r.get(alias) not in (None, ""):
                    e[k] = vhdraw.seconds(r[alias]) if k == "at" and vhdraw.seconds(r[alias]) is not None else r[alias]
                    break
        if not ID.match(e["id"]):
            raise EditError(2, [f"shots.json: shot id {e['id']!r}: an entry's id is letters, digits and _ (rename it there first)"])
        entries.append(e)
        prev = s["end"]
    doc = {"v": 1, "note": "the film as an edit list (engines/EDIT.md); folded in from shots.json by bin/vh edit init",
           "fps": fps, "size": size, "sources": {}, "tracks": [{"id": "V1", "entries": entries}]}
    if isinstance(meta.get("video"), str):
        doc["video"] = meta["video"]
    Reader(project, doc, folding=True).resolve()   # the shots must follow one another: nothing is written if they do not
    out = project / FILE
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    kept = folded_name(project)   # an earlier fold's copy stays as it was
    os.replace(sj, kept)
    return resolve(project), kept.name


def folded_name(project):
    """shots.json.folded, or shots.json.folded-2, -3 … when an earlier init kept one"""
    f, n = Path(project) / "shots.json.folded", 2
    while f.exists():
        f, n = Path(project) / f"shots.json.folded-{n}", n + 1
    return f


# ---- check ----

def page_facts(project, browser):
    """Each page source's facts, read by its own browser (tools/film/edit.mjs facts): {src: {...}} or an error string."""
    r = subprocess.run(["node", str(HERE / "film" / "edit.mjs"), "facts", str(project), "--browser", browser], capture_output=True, text=True, timeout=900)
    if r.returncode:
        return (r.stderr or r.stdout).strip().splitlines()[-1:] or ["the pages could not be read"]
    try:
        return json.loads(r.stdout)
    except ValueError:
        return ["the pages' facts were not JSON"]


def licence_findings(project, doc):
    out = []
    sys.path.insert(0, str(HERE / "assets"))
    import ledger as L, licenses as LI
    policy, where = L.policy_of(project)
    try:
        _, ents, _ = L.entries(project)   # no ledger is an empty one
    except Exception as e:   # one that cannot be read: under strict nothing on it can be taken as cleared
        return [("fail" if policy == "strict" else "warn", "edit.licence", None,
                 f"the asset ledger could not be read ({e}): bin/vh assets check; Assets: {policy} ({where})")]
    recs = [x["record"] for x in ents if "removed" not in x["record"]]
    by_id = {r.get("id"): r for r in recs}
    by_path = {r.get("path"): r for r in recs}
    for key, f in doc["files"].items():
        if not f.get("path") or f["kind"] == "page":
            continue
        users = [e["id"] for e in doc["entries"] if e["src"] == key]
        if f["kind"] == "film":   # a film of another project: its sources are on that project's ledger
            out.append(("info", "edit.licence", users[0] if users else None, f"{key}: a film of {f['film']['project']}: its sources' licences are "
                        f"that project's (bin/vh assets check {f['film']['project']})"))
            continue
        rec = by_id.get(f.get("asset")) if f.get("asset") else (by_path.get(f.get("folder")) or by_path.get(f["path"]))   # a clip folder is one record
        cls = L.class_of(rec) if rec else "unknown"
        if f.get("asset") and not rec:
            msg = f"{key}: no record {f['asset']} in the asset ledger"
        elif not rec:
            msg = f"{key}: {f['path']} is not on the asset ledger (bin/vh assets add)"
        else:
            msg = None
        bad = LI.risks(cls) if cls != "unknown" else ["unknown"]
        if msg or not LI.accepted(cls, "strict"):
            sev = "fail" if policy == "strict" else "warn"
            out.append((sev, "edit.licence", users[0] if users else None,
                        (msg or f"{key}: {f['path']} is {cls} ({', '.join(bad)})") + f", used by {', '.join(users)}; Assets: {policy} ({where})"))
    return out


def cut_findings(doc):
    """footage entries that play across a hard cut inside their clip (clip.json's cuts, scdet): a cut the edit list does not show"""
    from timegrid import rate_of
    out = []
    for r in doc["runs"]:
        cuts = [c for c in ((doc["files"].get(r.get("src")) or {}).get("cuts") or []) if number(c)] if r.get("draw") == "clip" else []
        if not cuts:
            continue
        num, den = rate_of(r["rate"])
        t0 = r["j0"] * den / num
        t1 = t0 + (r["frames"][1] - r["frames"][0]) * r["speed"] / doc["fps"]
        inside = [c for c in cuts if t0 + 0.5 * den / num < c < t1 - 0.5 * den / num]
        if inside:
            out.append(("warn", "edit.cut", r["entry"], f"{r['entry']}: plays across a cut inside {r['path']} (at {', '.join(f'{c:g}' for c in inside)} s of it, "
                        "clip.json's cuts): move its in or out to the cut, or make it two entries"))
    return out


def transitions_refused(doc):
    """the entries whose transition bin/vh render stops on: between two entries that both have a source (next to a slate
    it is drawn as a hard cut)"""
    ents = doc["entries"]
    return [e["id"] for p, e in zip(ents, ents[1:]) if e.get("transition_draw") and p["kind"] != "slate" and e["kind"] != "slate"]


def check(project, browser=None):
    """→ (exit, findings [(severity, kind, entry, message)], doc or None)."""
    found = []
    try:
        doc = resolve(project)
    except EditError as e:
        return e.code, [("fail", "edit.format" if e.code == 2 else "edit.layout", None, p) for p in e.problems], None
    stops = set(transitions_refused(doc))
    for kind, eid, line in notes(doc):
        if kind == "edit.transition" and eid in stops:   # render stops on it: the same words, a failure here too
            e = next(x for x in doc["entries"] if x["id"] == eid)
            found.append(("fail", kind, eid, f"{eid}: a transition ({e['transition'].get('type')} {e['transition'].get('duration')} s) is not drawn yet: "
                          "leave it out for a hard cut (one next to a slate is drawn as a hard cut); bin/vh render stops on it"))
        else:   # footage with no colour tags fails too: its colours are a guess until it is tagged
            found.append(("fail" if kind == "edit.untagged" else "warn", kind, eid, line))
    old = read_resolved(project)
    if old is None:
        found.append(("info", "edit.build", None, f"no {RESOLVED.as_posix()} yet: bin/vh edit build (bin/vh render builds it too)"))
    else:
        if (old.get("edit") or {}).get("sha256") != doc["edit"]["sha256"]:
            found.append(("warn", "edit.build", None, f"{FILE} changed since the last build: bin/vh edit build"))
        for key, f in doc["files"].items():
            was = (old.get("files") or {}).get(key) or {}
            if f.get("sha256") and was.get("sha256") and f["sha256"] != was["sha256"]:
                found.append(("warn", "edit.changed", None, f"{f['path']} changed since the last build ({key}): bin/vh edit build, then render the entries that use it"))
        for r in doc["refs"]:
            was = {x.get("path"): x.get("sha256") for x in old.get("refs") or [] if isinstance(x, dict)}
            if r["path"] in was and was[r["path"]] != r["sha256"]:
                found.append(("warn", "edit.changed", None, f"{r['path']} changed since the last build: the entries that hang on it may move (bin/vh edit build says which)"))
    found += licence_findings(project, doc) + cut_findings(doc)
    if browser:
        facts = page_facts(project, browser)
        if isinstance(facts, list):
            found.append(("fail", "edit.pages", None, f"the pages were not read, so their checks did not run (length, time sources, cues): {facts[0]}"))
        else:
            found += page_findings(doc, facts)
    elif any(f["kind"] == "page" for f in doc["files"].values()):
        found.append(("info", "edit.pages", None, "no browser: the pages themselves (their length, cues and time sources) were not read"))
    code = 1 if any(s == "fail" for s, *_ in found) else 0
    return code, found, doc


def page_findings(doc, facts):
    out, fps = [], doc["fps"]
    refs = {r.get("kind"): r for r in doc["refs"]}
    first = {}   # the first film-clock page's own time source of each kind, when edit.json names none: the others match it
    for e in doc["entries"]:
        if e["kind"] != "page":
            continue
        f = facts.get(e["src"])
        if not isinstance(f, dict):
            continue
        if f.get("error"):
            out.append(("fail", "edit.pages", e["id"], f"{e['id']} ({e['src']}): {f['error']}")); continue
        n = e["frames"][1] - e["frames"][0]   # the page's own time at the entry's last frame, before the page's end (as pageShort in edit.mjs)
        last = (e["frames"][1] - 1) / fps if e["clock"] == "film" else e["in"] + (n - 1) * e["speed"] / fps
        if not e.get("hold") and f.get("duration") is not None and last * fps >= f["duration"] * fps - 1e-6:
            out.append(("fail", "edit.layout", e["id"], f"{e['id']}: {e['src']} is {f['duration']:.3f} s long and the entry's last frame is at {last:.3f} s of it: "
                        "shorten the entry, or \"hold\": true to hold its last frame"))
        n = len(f.get("cues") or [])
        if e["clock"] == "local" and n:
            out.append(("warn", "edit.cues", e["id"], f"{e['id']}: {e['src']} is on its own clock and hangs {n} cue{'s' * (n != 1)} on the narration: "
                        "they land in its own time, not the film's (did you mean \"clock\": \"film\"?)"))
        if e["clock"] == "film":
            for what in ("timeline", "music", "timemap"):
                g = f.get(what)
                if not (isinstance(g, dict) and g.get("sha256")):
                    continue
                want = refs.get(what) or first.setdefault(what, {**g, "by": e["id"]})
                if g["sha256"] != want["sha256"]:
                    whose = "edit.json's refs" if what in refs else f"{want['by']}'s page ({want.get('path')})"
                    out.append(("fail", "edit.refs", e["id"], f"{e['id']}: {e['src']} reads another {what} ({g.get('path')}) than {whose}: "
                                "every film-clock page reads the same one; point them at one file, then bin/vh edit build"))
    return out


# ---- a film of an edit list (bin/vh check and deliver) ----

def film_facts(video):
    """What bin/vh check and deliver ask of a video that is an edit list's film: {"from", "entries", "slates", "changed"},
    or None when it is not one. From its .render.json (what it was rendered from) when it has one, else from the render
    record bin/vh mux kept in <film>.mux.json; a film with neither in a project with an edit list is taken as the edit
    list is now. slates: [{id, frames, t, t1}] inside the film's
    span; changed: the images it was drawn from that are no longer those bytes."""
    video = Path(video).resolve()
    side, side_dir, said = None, video.parent, "its .render.json"
    try:
        side = json.loads(Path(str(video) + ".render.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        try:   # a muxed film: its picture's render record as bin/vh mux kept it (the picture may have been rendered again since)
            mux = json.loads(Path(str(video) + ".mux.json").read_text(encoding="utf-8"))
            film = mux.get("film") or {}
            if film.get("size") is not None and film["size"] != video.stat().st_size:   # the record of another film at this path
                side, said = None, f"{FILE} as it is now (its .mux.json describes another file: {film['size']} bytes, this one {video.stat().st_size})"
            elif isinstance(mux.get("render"), dict) and isinstance(mux.get("video"), str):
                side, side_dir = mux["render"], (video.parent / mux["video"]).resolve().parent
                said = f"the render record of {mux['video']}, as bin/vh mux kept it"
        except (OSError, ValueError, AttributeError):
            side = None
    project = next((d for d in [video.parent, *video.parents] if (d / "BRIEF.md").is_file() or (d / FILE).is_file()), None)
    if isinstance(side, dict) and side.get("kind") == "edit" and isinstance(side.get("entries"), list):
        fps, entries, runs, src = side.get("fps") or 30, side["entries"], side.get("runs") or [], said
        span = [side.get("first_frame") or 0, (side.get("first_frame") or 0) + (side.get("frames") or 0)]
        base = (side_dir / side["page"]).resolve().parent if isinstance(side.get("page"), str) else project
    elif isinstance(side, dict) or project is None or not find(project):
        return None
    else:
        try:
            doc = resolve(project)
        except EditError as e:
            return {"from": f"{FILE} as it is now", "entries": [], "slates": [], "changed": [], "error": "; ".join(e.problems[:3])}
        fps, entries, runs, span, base = doc["fps"], doc["entries"], doc["runs"], [0, doc["frames"]], project
        src = said if "describes another file" in said else f"{FILE} as it is now (the film has no .render.json)"
    slates = [{"id": e["id"], "frames": [e["frames"][0], e["frames"][1] - 1], "t": r3(e["frames"][0] / fps), "t1": r3(e["frames"][1] / fps)}
              for e in entries if e.get("kind") == "slate" and e["frames"][0] < span[1] and e["frames"][1] > span[0]]
    changed = []
    for r in runs:
        if r.get("sha256") and r.get("path"):
            f = Path(base) / r["path"]
            try:
                now = sha256(f)
            except OSError:
                now = None
            if now != r["sha256"]:
                changed.append({"entry": r.get("entry"), "path": r["path"], "now": "gone" if now is None else "other bytes"})
    return {"from": src, "fps": fps, "entries": [{k: e.get(k) for k in ("id", "kind", "src", "frames", "start", "end")} for e in entries],
            "slates": slates, "changed": changed}


def film_main(argv):
    """python3 tools/edit.py _film <video> [--json f]: bin/vh check's step. Nothing said and 0 for a film that is not an
    edit list's; a line, and 1 while slates are left in it."""
    video, out = argv[0] if argv else None, argv[argv.index("--json") + 1] if "--json" in argv[:-1] else None
    if not video:
        print("usage: python3 tools/edit.py _film <video> [--json f]", file=sys.stderr)
        return 2
    f = film_facts(video)
    if f is None:
        return 0
    if out:
        try:
            Path(out).write_text(json.dumps(f, ensure_ascii=False), encoding="utf-8")
        except OSError as e:
            print(f"edit: could not write {out} ({e.strerror or e})", file=sys.stderr)
    s = f["slates"]
    if f.get("error"):
        print(f"edit list: {FILE} does not resolve ({f['error']}): bin/vh edit build")
        return 1
    head = (f"edit list ({f['from']}): {len(s)} slate{'s' * (len(s) != 1)} left, " + ", ".join(f"{x['id']} ({x['t']:.2f}–{x['t1']:.2f} s)" for x in s[:6]) +
            (" …" if len(s) > 6 else "") + ": an entry with no source yet is a placeholder, not a film to deliver") if s else \
        f"edit list ({f['from']}): {len(f['entries'])} entries, no slate left"
    print(head)
    for c in f["changed"]:
        print(f"  ! {c['path']} ({c['entry']}): {'gone' if c['now'] == 'gone' else 'not the bytes the film was drawn from'} (bin/vh edit build, then render it again)")
    return 1 if s else 0


# ---- the commands ----

def say_problems(e, prefix="edit"):
    print(f"{prefix}: {FILE} {'does not resolve' if e.code == 2 else 'does not fit'} ({len(e.problems)} problem{'s' * (len(e.problems) != 1)}):", file=sys.stderr)
    for p in e.problems[:30]:
        print(f"  {p}", file=sys.stderr)
    if len(e.problems) > 30:
        print(f"  … and {len(e.problems) - 30} more", file=sys.stderr)


def cmd_build(a):
    project = project_of(a.project)
    if not find(project):
        raise EditError(2, [f"no {FILE} in {project} (bin/vh edit init folds shots.json into one)"])
    doc, said = build(project, write=not a.no_write)
    if a.json:
        print(json.dumps(dict(doc, said=said), ensure_ascii=False))
    elif not a.quiet:
        print(f"edit: {FILE} → {RESOLVED.as_posix()} · {summary(doc)}")
        for line in said:
            print(f"  {line}")
    return 0


def cmd_check(a):
    project = project_of(a.project)
    if not find(project):
        raise EditError(2, [f"no {FILE} in {project}"])
    code, found, doc = check(project, a.browser)
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh edit check", "edit": str(project / FILE), "exit": code,
                          "findings": [{"severity": s, "kind": k, "entry": e, "message": m} for s, k, e, m in found]}, ensure_ascii=False, indent=1))
    else:
        mark = {"fail": "✗", "warn": "!", "info": "·"}
        print(f"edit check: {FILE}" + (f" · {summary(doc)}" if doc else ""))
        for s, _, _, m in found:
            print(f"  {mark[s]} {m}")
        if not found:
            print("  ✓ nothing to say")
    return code


def cmd_list(a):
    project = project_of(a.project)
    if not find(project):
        raise EditError(2, [f"no {FILE} in {project}"])
    doc = resolve(project)
    if a.json:
        print(json.dumps({"version": 1, "fps": doc["fps"], "frames": doc["frames"], "duration": doc["duration"], "entries": doc["entries"],
                          "slates": doc["slates"]}, ensure_ascii=False, indent=1))
        return 0
    print(f"edit: {FILE} · {summary(doc)}")
    w = max(len(e["id"]) for e in doc["entries"])
    for e in doc["entries"]:
        what = {"slate": "slate"}.get(e["kind"], f"{e['kind']} {e['src']}" + (f" ({e['clock']} clock)" if e.get("clock") else ""))
        reads = e.get("reads")
        reads = " / ".join(map(str, reads)) if isinstance(reads, list) else str(reads or "")
        bits = [str(e.get("segment") or ""), reads, ("? " + str(e["unsure"])) if e.get("unsure") not in (None, False) else ""]
        print(f"  {e['id']:<{w}}  {e['frames'][0]:>6}–{e['frames'][1] - 1:<6} {e['start']:>8.3f}–{e['end']:<8.3f}  {what:<28} "
              + " · ".join(b for b in bits if b))
    return 0


def cmd_init(a):
    project = project_of(a.project)
    size = None
    if a.size:
        m = re.fullmatch(r"(\d+)x(\d+)", a.size)
        if not m:
            raise EditError(2, ["--size: write it as 1920x1080"])
        size = [int(m.group(1)), int(m.group(2))]
    doc, kept = init(project, a.fps, size)
    write_resolved(project, doc)
    print(f"edit: shots.json folded into {FILE} (shots.json is {kept} now) · {summary(doc)}")
    print("  every entry is a slate: give each a source as its picture comes (engines/EDIT.md); bin/vh render draws it as it stands, gate ②'s animatic")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["_film"]:   # bin/vh check's and deliver's step (not a command of its own)
        return film_main(argv[1:])
    ap = argparse.ArgumentParser(prog="bin/vh edit", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=__doc__.split("\n\n", 1)[1])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("project"); p.add_argument("--fps", type=int); p.add_argument("--size")
    p = sub.add_parser("build"); p.add_argument("project"); p.add_argument("--json", action="store_true"); p.add_argument("--quiet", action="store_true")
    p.add_argument("--no-write", action="store_true", help=argparse.SUPPRESS)   # the page tools' read of it (edit.mjs facts): nothing written
    p = sub.add_parser("check"); p.add_argument("project"); p.add_argument("--json", action="store_true"); p.add_argument("--browser", help=argparse.SUPPRESS)
    p = sub.add_parser("list"); p.add_argument("project"); p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        return {"init": cmd_init, "build": cmd_build, "check": cmd_check, "list": cmd_list}[a.cmd](a)
    except EditError as e:
        say_problems(e)
        return e.code


if __name__ == "__main__":
    sys.exit(main())
