"""bin/vh footage: real footage and pictures from Internet Archive, Wikimedia Commons and NASA. Search them, see an item's
files, get one into the project (whole, or only the seconds needed) with its licence and source on record, keep a sync
table for several cameras of one event, and bake frames named by the film's frame numbers. Stdlib only, and ffmpeg.

usage: bin/vh footage search <archive|commons|nasa> <query> [--type video|image|any] [-n 15] [--project P] [--json]
                  [--offline DIR]
       bin/vh footage files <ref> [--json] [--offline DIR]
       bin/vh footage get <project> <ref|url> [--id ID] [--file NAME] [--rendition orig|large|medium|small|mobile]
                  [--range a:b] [--max-mb 800] [--rate 2M] [--license TEXT] [--license-url U] [--class C] [--author A]
                  [--title T] [--page URL] [--attribution TEXT] [--used-by S03,S05] [--note TEXT] [--tonemap hable]
                  [--offline DIR] [--json]
       bin/vh footage list <project> [--json]
       bin/vh footage sync <project> [<id> (--group G --c SECONDS [--k FACTOR] [--by TEXT] | --clear)] [--json]
       bin/vh footage frames <project> <id> --film a:b [--fps F] (--t0 T | --at S) [--size WxH] [--fit cover|contain]
                  [--vf FILTERS] [--name N] [--png] [--json]
<ref>: archive:<identifier>[/<file>], commons:File:<name> (or commons:<name>), nasa:<nasa_id>, or the https URL of a
file (then --license, --license-url and --page say what the tools cannot read). <project> as bin/vh assets takes it.

  search   one site's results: the ref to get, the date, the title, the licence as the site writes it and the class it
           falls in (tools/assets/licenses.py, with the site's own rules below). --project: say which ones its Assets
           policy takes; without one, which ones strict takes
  files    what an item has: an Archive item's files (name, size, format, original or derivative), a NASA item's
           renditions, a Commons file's size, length and type
  get      download it into the project and register it in assets/ledger.json. A video becomes a clip folder in the
           shape the edit list reads (docs: engines/CONTRACT.md's 在序列里 when it lands; the design is the edit list's
           §9): assets/footage/<id>/orig.<ext> (as downloaded, never changed), clip.mp4 (the working clip: CFR at the
           footage's own rate, pts from 0, every keyframe closed and at most 1 s apart, H.264 High yuv420p crf 12,
           BT.709 tv with its four tags, square pixels, upright, +faststart; not made when orig is all that already),
           clip.json (the clip's facts, below), audio.wav (its sound as 48 kHz PCM, from the first picture on, when it
           has sound). The folder is one record (its tree hash). A picture goes to assets/img/<id>.<ext>.
           --range a:b: only those seconds of the original (a video): ffmpeg reads the file through tools/assets/
           fetch.py's local range proxy (serve), from the keyframe at or before a, stream-copied: orig is the original's
           own packets, its range on record from that keyframe. --max-mb: a whole download over this is refused before
           it starts (default 800; --range is not capped). --rate: a cap, 2M = 2 MB a second.
           --license/--license-url: the licence as its page writes it, classified; --class: the class outright (when
           the page says what the table cannot read). Under the project's Assets: strict (tools/assets/ledger.py
           policy_of), what strict does not take is refused before anything is downloaded (exit 1); under record it is
           downloaded and its risk said. HDR footage (PQ, HLG) is converted to SDR only with --tonemap (hable, mobius,
           reinhard: zscale's tone mapping; the choice is a creative one and goes into clip.json)
  list     the project's clips: id, rate, size, length, the range taken, sync, licence class
  sync     the sync table: a clip of a group is on the group's clock M (mission time, the event's own seconds) by
           s = k·M + c (s: the clip's own seconds; k: a slow-motion factor, 1 for real time). --group, --c, --k set a
           clip's row in its clip.json (--by: how it was measured, e.g. "ignition flash at s 12.345 + the call ‘booster’"),
           --clear takes it out; the clip's record is updated with it. Without an id: the table
  frames   bake the frames a page loads, named by the film's frame number: film frame n of --fps F (default the
           BRIEF's frame rate, else 30) for n in [frame_from(a), frame_from(b)) shows clip frame j = ⌊s·rate + 10⁻⁶⌋, s
           from the sync table with the group's zero at film time --t0 (M = t − T0), or s = S + (t − a) with --at S for a
           clip with no sync. The page draws assets/frames/<name>/<n>.jpg (5 digits) for t = n / F: the sync is in the
           file names, not in the page (hard rule 1). --size WxH scales (lanczos; --fit cover crops to fill, contain
           pads), --vf adds an ffmpeg filter chain after it (a grade, delogo, crop, transpose), --png bakes lossless
           PNGs. frames.json in the folder records the mapping; the folder is one record, derived_from the clip
The licence, site by site (what get and search read; an explicit --class wins):
  archive  the item's licenseurl, else its rights statement. An item that is a re-upload from a video site (an
           identifier youtube-…, the mirrortube collection) is unknown whatever it says: its origin is not on record
  commons  the file page's LicenseShortName and LicenseUrl. "No restrictions" (a statement, not a licence) is unknown;
           the page's Restrictions (trademarked, personality rights) go into the record's note
  nasa     public domain: NASA's own media are works of the U.S. government (NASA's media usage guidelines). An item
           whose description or credit names another holder (©, copyright, courtesy of, used with permission) is
           unknown: read its page. NASA asks for a credit; its insignia are not graphics, and the film does not suggest
           NASA endorses it (the record's note says so)
  a URL    what --license and --license-url say; nothing said is unknown
clip.json, version 1: {"v", "id", "asset" (the ledger id), "file" (clip.mp4, or orig.<ext>), "sha256", "rate" (a rational,
"30000/1001"), "frames" (counted in the file, not length × rate), "duration", "size", "sar", "color" ([range, matrix,
primaries, transfer], as render's sidecar has them), "assumed" (what was taken for missing tags), "gop", "audio" ({file, sha256, rate, channels} or
null), "from" ({file, sha256, range, conform: the command as run}), "crop" (black bars measured, [w, h, x, y], not cut;
null), "cuts" (hard cuts inside it, seconds; scdet), "words" (null), "sync" ({group, c, k, by} or null), "source"
(provider, ref, page)}.
--json: {"version": 1, "tool", …}; the lines go to stderr. --offline DIR: the answers from DIR/responses.json, recorded
before (CONTRIBUTING.md, 联网的命令): no network; tools/assets/fixtures/footage has the ones the tests use.
Exit: 0 · 1 a download, a conform or a licence refused · 2 usage: no project, no such ref, an id on record already.
This file adapts lemo-opuscar's footage.py and grab.py (styles/countdown/demo/tools/ at a401d6c; MIT, Copyright (c) 2026
LemoLab, its licence in recipes/LICENSES/MIT-lemo-opuscar.txt):
the three sites' search and file APIs, the NASA rendition order, the per-site licence rules and the sync table with
frames baked by film frame number come from there; the code is written anew around tools/assets.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile, time, urllib.parse
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import assets as A, fetch, ledger, licenses   # noqa: E402,E401

PROG = "bin/vh footage"
SUB = ("search", "files", "get", "list", "sync", "frames")
SITES = ("archive", "commons", "nasa")
FOOTAGE = Path("assets") / "footage"
FRAMES = Path("assets") / "frames"
VIDEO_EXT = (".mp4", ".m4v", ".mov", ".webm", ".mkv", ".ogv", ".mpeg", ".mpg", ".mpeg4", ".avi")   # and .ogg when its page says video
IMAGE_EXT = (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".gif")
NASA_ORDER = ("orig", "large", "medium", "small", "mobile", "preview")
NASA_LICENCE = ("Public domain in the U.S.: a work of NASA (NASA's media usage guidelines)",
                "https://www.nasa.gov/nasa-brand-center/images-and-media/")
NASA_NOTE = "NASA asks for a credit; no NASA insignia as a graphic, and the film does not suggest NASA endorses it"
HOLDER = re.compile(r"©|\bcopyright\b|\bcourtesy of\b|used with permission|all rights reserved", re.I)
CREDIT = re.compile(r"\bcredits?\s*:\s*([^\n]{1,100})", re.I)
OTHERS = re.compile(r"\b(?:ESA|CSA|JAXA|Roscosmos|SpaceX|Boeing|Blue Origin|Getty|AP|Reuters|AFP|Shutterstock)\b")
REUPLOAD = re.compile(r"^youtube-|mirrortube", re.I)
COMMONS_META = "LicenseShortName|LicenseUrl|Artist|Credit|DateTimeOriginal|AttributionRequired|Restrictions|UsageTerms|Copyrighted|ObjectName"
out = sys.stdout   # the lines; stderr under --json


class Usage(A.Usage):
    pass


class Failed(Exception):
    """A download, a conform or a licence refused: exit 1."""


def say(*a):
    print(*a, file=out)


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(s or ""))).strip()


# ---- the three sites ----

def archive_search(q, n, kind):
    mt = {"video": " AND mediatype:(movies)", "image": " AND mediatype:(image)"}.get(kind, "")
    fl = ("identifier", "title", "year", "date", "creator", "licenseurl", "rights", "collection", "mediatype")
    return "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode([("q", f"({q}){mt}")] + [("fl[]", f) for f in fl]
                                                                              + [("rows", n), ("output", "json")])


def commons_search(q, n, kind):
    ft = {"video": " filetype:video", "image": " filetype:bitmap"}.get(kind, "")
    return "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode([
        ("action", "query"), ("format", "json"), ("generator", "search"), ("gsrsearch", q + ft), ("gsrnamespace", 6), ("gsrlimit", n),
        ("prop", "imageinfo"), ("iiprop", "url|size|mime|mediatype|extmetadata"), ("iiextmetadatafilter", COMMONS_META)])


def commons_file(title):
    return "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode([
        ("action", "query"), ("format", "json"), ("titles", title), ("prop", "imageinfo"),
        ("iiprop", "url|size|mime|mediatype|extmetadata"), ("iiextmetadatafilter", COMMONS_META)])


def nasa_search(q, n, kind):
    mt = {"video": "video", "image": "image"}.get(kind, "image,video")
    return "https://images-api.nasa.gov/search?" + urllib.parse.urlencode([("q", q), ("media_type", mt), ("page_size", n)])


def first(x):
    return x[0] if isinstance(x, list) and x else x


def judge(site, meta):
    """(class, why, by) of an item: the site's rules (the module's note), then tools/assets/licenses.py."""
    name, url = meta.get("license") or "", meta.get("license_url") or ""
    if site == "archive" and (REUPLOAD.search(meta.get("id") or "") or any(REUPLOAD.search(c) for c in meta.get("collection") or [])):
        return "unknown", "a re-upload from a video site (youtube-…, mirrortube): its origin is not on record", "site"
    if site == "nasa":   # another holder named where a credit is given (an astronaut of CSA in the description is no credit)
        text = " ".join(str(meta.get(k) or "") for k in ("description", "photographer", "secondary_creator"))
        hit = HOLDER.search(text)
        credits = [m.group(1).strip() for m in CREDIT.finditer(text)] + [str(meta.get(k)) for k in ("photographer", "secondary_creator") if meta.get(k)]
        other = next((c for c in credits if OTHERS.search(c)), None)
        if hit or other:
            return "unknown", f"the item names another holder ({(hit.group(0) if hit else other)[:60]!r}): read its page before using it", "site"
        return "pd", "NASA's own media: a U.S. government work", "site"
    if not name and not url:
        return "unknown", "no licence on the item's record", "classifier"
    cls, why = licenses.classify(name, url)
    return cls, why or licenses.NAMES.get(cls, cls), "classifier"


def archive_item(d):
    col = d.get("collection")
    return {"site": "archive", "ref": f"archive:{d.get('identifier')}", "id": d.get("identifier"), "title": strip_html(first(d.get("title"))),
            "date": str(d.get("date") or d.get("year") or "")[:10], "author": strip_html(first(d.get("creator"))),
            "license": strip_html(first(d.get("rights"))) if not d.get("licenseurl") else "", "license_url": first(d.get("licenseurl")) or "",
            "collection": col if isinstance(col, list) else [col] if col else [], "kind": {"movies": "video", "image": "image"}.get(d.get("mediatype"), d.get("mediatype") or ""),
            "page": f"https://archive.org/details/{d.get('identifier')}"}


def commons_item(p):
    ii = (p.get("imageinfo") or [{}])[0]
    em = ii.get("extmetadata") or {}
    v = lambda k: strip_html((em.get(k) or {}).get("value", ""))   # noqa: E731
    mime = ii.get("mime") or ""
    return {"site": "commons", "ref": f"commons:{p.get('title')}", "id": p.get("title"), "title": v("ObjectName") or str(p.get("title", "")).removeprefix("File:"),
            "date": (re.search(r"\d{4}-\d{2}-\d{2}|\d{4}", v("DateTimeOriginal")) or re.match("", "")).group(0), "author": v("Artist") or v("Credit"), "license": v("LicenseShortName"), "license_url": v("LicenseUrl"),
            "restrictions": v("Restrictions"), "kind": "video" if mime.startswith("video/") or ii.get("mediatype") == "VIDEO" else "image" if mime.startswith("image/") else mime,
            "size": [ii.get("width"), ii.get("height")] if ii.get("width") else None, "duration": ii.get("duration"), "bytes": ii.get("size"),
            "mime": mime, "file_url": ii.get("url"), "page": ii.get("descriptionurl") or f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(str(p.get('title', '')))}"}


def nasa_item(it):
    d = (it.get("data") or [{}])[0]
    return {"site": "nasa", "ref": f"nasa:{d.get('nasa_id')}", "id": d.get("nasa_id"), "title": strip_html(d.get("title")), "date": str(d.get("date_created") or "")[:10],
            "author": strip_html(d.get("photographer") or d.get("secondary_creator") or (f"NASA {d['center']}" if d.get("center") else "NASA")),
            "description": strip_html(d.get("description") or d.get("description_508")), "photographer": d.get("photographer"),
            "secondary_creator": d.get("secondary_creator"), "credit": "", "license": NASA_LICENCE[0], "license_url": NASA_LICENCE[1],
            "kind": d.get("media_type") or "", "page": f"https://images.nasa.gov/details/{urllib.parse.quote(str(d.get('nasa_id', '')))}"}


def search(site, q, n, kind, opener):
    if site == "archive":
        docs = fetch.get_json(archive_search(q, n, kind), opener).get("response", {}).get("docs", [])
        items = [archive_item(d) for d in docs]
    elif site == "commons":
        pages = fetch.get_json(commons_search(q, n, kind), opener).get("query", {}).get("pages", {})
        items = [commons_item(p) for p in sorted(pages.values(), key=lambda p: p.get("index", 0))]
    else:
        got = fetch.get_json(nasa_search(q, n, kind), opener).get("collection", {}).get("items", [])
        items = [nasa_item(it) for it in got[:n]]
    for it in items:
        it["class"], it["why"], _ = judge(site, it)
    return items


def parse_ref(ref):
    """(site, key, file) of a ref; ("url", url, None) for an https URL. Usage when it is neither."""
    m = re.match(r"(archive|commons|nasa):(.+)$", ref.strip())
    if m:
        site, rest = m.group(1), m.group(2).strip().strip('"\'')
        if site == "archive":
            ident, _, fname = rest.partition("/")
            return site, ident, fname or None
        if site == "commons":
            return site, rest if rest.startswith("File:") else "File:" + rest, None
        return site, rest, None
    if re.match(r"https://", ref, re.I):
        return "url", ref, None
    if re.match(r"http://", ref, re.I):
        raise Usage(f"{fetch.redact(ref)}: an http address; footage downloads over https only")
    raise Usage(f"{ref!r} is not a ref: archive:<identifier>[/<file>], commons:File:<name>, nasa:<nasa_id> or an https URL")


def archive_files(ident, opener):
    md = fetch.get_json(f"https://archive.org/metadata/{urllib.parse.quote(ident)}", opener)
    if not md or not isinstance(md, dict) or not md.get("metadata"):
        raise Failed(f"archive:{ident}: no such item (archive.org/metadata answered nothing)")
    files = [f for f in md.get("files") or [] if isinstance(f, dict) and f.get("source") in ("original", "derivative")]
    return md, files


def nasa_renditions(nid, opener):
    got = fetch.get_json(f"https://images-api.nasa.gov/asset/{urllib.parse.quote(nid)}", opener).get("collection", {}).get("items", [])
    return [str(i.get("href", "")).replace("http://", "https://", 1) for i in got if i.get("href")]


def files(ref, opener):
    """What an item has: [{"name", "bytes", "format", "source", "url"}]."""
    site, key, _ = parse_ref(ref)
    if site == "archive":
        _, fs = archive_files(key, opener)
        return [{"name": f["name"], "bytes": int(f.get("size") or 0) or None, "format": f.get("format"), "source": f.get("source"),
                 "url": f"https://archive.org/download/{urllib.parse.quote(key)}/{urllib.parse.quote(f['name'])}"} for f in fs]
    if site == "nasa":
        return [{"name": urllib.parse.unquote(h.rsplit("/", 1)[-1]), "bytes": None, "format": Path(urllib.parse.urlsplit(h).path).suffix.lstrip("."),
                 "source": "rendition", "url": h} for h in nasa_renditions(key, opener)]
    if site == "commons":
        it = commons_one(key, opener)
        return [{"name": key, "bytes": it.get("bytes"), "format": it.get("mime"), "source": "original", "url": it.get("file_url"),
                 "size": it.get("size"), "duration": it.get("duration")}]
    raise Usage("files takes a ref of a site (archive:, commons:, nasa:), not a URL")


def commons_one(title, opener):
    pages = fetch.get_json(commons_file(title), opener).get("query", {}).get("pages", {})
    p = next(iter(pages.values()), {}) if pages else {}
    if not p or "imageinfo" not in p:
        raise Failed(f"commons:{title}: no such file on Commons")
    return commons_item(p)


def resolve(ref, opener, file=None, rendition=None):
    """The item a ref names, with the one file to fetch: {site, ref, id, title, date, author, license, license_url, page,
    file_url, kind, ext, notes}."""
    site, key, fname = parse_ref(ref)
    fname = file or fname
    notes = []
    if site == "archive":
        md, fs = archive_files(key, opener)
        m = md.get("metadata") or {}
        it = archive_item(dict(m, identifier=key))
        if fname:
            f = next((f for f in fs if f["name"] == fname), None)
            if f is None:
                raise Usage(f"archive:{key} has no file {fname!r}: bin/vh footage files archive:{key}")
        else:
            vids = [f for f in fs if f["name"].lower().endswith(VIDEO_EXT)] or [f for f in fs if f["name"].lower().endswith(IMAGE_EXT)]
            if not vids:
                raise Failed(f"archive:{key} has no video or picture file: bin/vh footage files archive:{key}, then --file")
            vids.sort(key=lambda f: (f.get("source") == "original", int(f.get("size") or 0)), reverse=True)
            f = vids[0]
            if len(vids) > 1:
                notes.append(f"took {f['name']} (the largest {'original' if f.get('source') == 'original' else 'file'}); --file picks another")
        it["file_url"] = f"https://archive.org/download/{urllib.parse.quote(key)}/{urllib.parse.quote(f['name'])}"
        it["bytes"] = int(f.get("size") or 0) or None
        it["file"] = f["name"]
    elif site == "commons":
        it = commons_one(key, opener)
    elif site == "nasa":
        hs = nasa_renditions(key, opener)
        meta = fetch.get_json(f"https://images-api.nasa.gov/search?nasa_id={urllib.parse.quote(key)}", opener).get("collection", {}).get("items", [])
        if not meta:
            raise Failed(f"nasa:{key}: no such item")
        it = nasa_item(meta[0])
        pick, order = None, ([rendition] if rendition else list(NASA_ORDER))
        for want in order:
            for ext in (".mp4", ".mov", ".jpg", ".png", ".tif"):
                pick = next((h for h in hs if urllib.parse.unquote(h).endswith(f"~{want}{ext}")), None)
                if pick:
                    break
            if pick:
                break
        if not pick:
            raise Failed(f"nasa:{key}: no {'~' + rendition if rendition else 'video or picture'} rendition among {len(hs)}: bin/vh footage files nasa:{key}")
        it["file_url"], it["file"] = pick, urllib.parse.unquote(pick.rsplit("/", 1)[-1])
        if not rendition and "~orig." not in it["file"]:
            notes.append(f"took {it['file']}: no ~orig rendition")
    else:
        it = {"site": "url", "ref": key, "id": Path(urllib.parse.urlsplit(key).path).stem, "title": "", "date": "", "author": "", "license": "",
              "license_url": "", "page": "", "file_url": key, "kind": "", "file": urllib.parse.unquote(Path(urllib.parse.urlsplit(key).path).name)}
    u = urllib.parse.urlsplit(it["file_url"] or "")   # Commons tags its file links with utm_ parameters: the file is the same without them
    q = [(k, v) for k, v in urllib.parse.parse_qsl(u.query, keep_blank_values=True) if not k.startswith("utm_")]
    it["file_url"] = urllib.parse.urlunsplit((u.scheme, u.netloc, u.path, urllib.parse.urlencode(q), u.fragment))
    ext = Path(u.path).suffix.lower()
    it["ext"] = ".mp4" if ext in (".mpeg4", ".m4v") else ext or ".bin"
    if it.get("kind") not in ("video", "image"):
        it["kind"] = "video" if it["ext"] in VIDEO_EXT else "image" if it["ext"] in IMAGE_EXT else ""
    if not it["kind"]:
        raise Failed(f"{ref}: {it.get('file') or it['file_url']} is neither a video nor a picture footage knows ({', '.join(VIDEO_EXT + IMAGE_EXT)})")
    it["notes"] = notes
    return it


# ---- ffmpeg ----

def run(argv, what):
    r = subprocess.run(argv, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise Failed(f"{what}: {argv[0]} exit {r.returncode}: {r.stderr.strip()[-600:]}")
    return r


def probe(path):
    """ffprobe's streams and format of a file or a URL, with the video stream's packets counted."""
    r = run(["ffprobe", "-v", "error", "-count_packets", "-show_streams", "-show_format", "-of", "json", str(path)], f"ffprobe {Path(str(path)).name}")
    try:
        j = json.loads(r.stdout)
    except ValueError:
        raise Failed(f"ffprobe {path}: not its JSON")
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video" and not (s.get("disposition") or {}).get("attached_pic")), None)
    a = next((s for s in j.get("streams", []) if s.get("codec_type") == "audio"), None)
    return {"video": v, "audio": a, "format": j.get("format") or {}}


def video_packets(path):
    """[(pts seconds, key)] of the video stream, in file order (no decoding)."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,flags", "-of", "csv=p=0", str(path)], "ffprobe packets")
    outp = []
    for line in r.stdout.splitlines():
        t, _, fl = line.partition(",")
        try:
            outp.append((float(t), "K" in fl))
        except ValueError:
            continue
    return outp


def rate_of(v):
    """The video stream's nominal rate as a Fraction, and whether it is constant."""
    def fr(s):
        try:
            n, _, d = str(s or "0/0").partition("/")
            return Fraction(int(n), int(d or 1)) if int(d or 1) else Fraction(0)
        except (ValueError, ZeroDivisionError):
            return Fraction(0)
    r, avg = fr(v.get("r_frame_rate")), fr(v.get("avg_frame_rate"))
    rate = r if r else avg
    if not rate:
        raise Failed("the video says no frame rate")
    return rate, (not avg or abs(float(avg) - float(r)) < 0.01 * float(r))


def frate(f):
    return f"{f.numerator}/{f.denominator}" if f.denominator != 1 else str(f.numerator)


def colour(v):
    """(range, matrix, primaries, transfer) to read the footage with (the order of render's sidecar), and what was assumed."""
    assumed = []
    hd = (v.get("height") or 0) >= 720
    rng = v.get("color_range")
    if rng not in ("tv", "pc"):
        rng = "pc" if str(v.get("pix_fmt", "")).startswith("yuvj") else "tv"
        assumed.append(f"no colour range tag: read as {rng}")
    mtx = v.get("color_space")
    if mtx in (None, "unknown", "reserved", ""):
        mtx = "bt709" if hd else "smpte170m"
        assumed.append(f"no colour matrix tag: read as {'BT.709 (HD)' if hd else 'BT.601 (SD)'}")
    trc, pri = v.get("color_transfer") or "unknown", v.get("color_primaries") or "unknown"
    return [rng, mtx, pri, trc], assumed


SWS_MATRIX = {"bt709": "bt709", "smpte170m": "bt601", "bt470bg": "bt601", "fcc": "fcc", "smpte240m": "smpte240m", "bt2020nc": "bt2020", "bt2020c": "bt2020"}
HDR = ("smpte2084", "arib-std-b67")


def rotation(v):
    for sd in v.get("side_data_list") or []:
        if "rotation" in sd:
            try:
                return int(round(float(sd["rotation"]))) % 360
            except (TypeError, ValueError):
                pass
    try:
        return int((v.get("tags") or {}).get("rotate", 0)) % 360
    except ValueError:
        return 0


def sar_of(v):
    m = re.match(r"(\d+):(\d+)$", str(v.get("sample_aspect_ratio") or ""))
    return Fraction(int(m.group(1)), int(m.group(2))) if m and int(m.group(1)) and int(m.group(2)) else Fraction(1)


def moov_first(path):
    """Is an MP4's index before its data (+faststart)?"""
    try:
        with open(path, "rb") as f:
            pos, seen = 0, []
            size = os.path.getsize(path)
            while pos + 8 <= size and len(seen) < 16:
                f.seek(pos)
                h = f.read(16)
                n, typ = int.from_bytes(h[:4], "big"), h[4:8]
                if n == 1:
                    n = int.from_bytes(h[8:16], "big")
                if typ in (b"moov", b"mdat"):
                    return typ == b"moov"
                if n < 8:
                    return False
                pos += n
                seen.append(typ)
    except OSError:
        pass
    return False


def unfit(path, p, packets):
    """Why orig cannot be the working clip as it is ([] when it can)."""
    v, why = p["video"], []
    rate, cfr = rate_of(v)
    if Path(path).suffix.lower() != ".mp4" or not moov_first(path):
        why.append("not an MP4 with its index first")
    if v.get("codec_name") != "h264" or v.get("profile") not in ("High", "Main", "Constrained Baseline"):
        why.append(f"{v.get('codec_name')} {v.get('profile') or ''}".strip() + ", not H.264")
    if v.get("pix_fmt") != "yuv420p":
        why.append(f"pixel format {v.get('pix_fmt')}")
    if [v.get("color_range"), v.get("color_space"), v.get("color_primaries"), v.get("color_transfer")] != ["tv", "bt709", "bt709", "bt709"]:
        why.append("not tagged BT.709 tv")
    if not cfr:
        why.append("a variable frame rate")
    if abs(float(v.get("start_time") or 0)) > 1e-4 or abs(float(p["format"].get("start_time") or 0)) > 1e-4:
        why.append("pts not from 0")
    if sar_of(v) != 1:
        why.append(f"pixels not square ({v.get('sample_aspect_ratio')})")
    if rotation(v):
        why.append(f"rotated {rotation(v)}°")
    if v.get("field_order") not in (None, "progressive", "unknown"):
        why.append(f"interlaced ({v.get('field_order')})")
    keys = [t for t, k in packets if k]
    if not packets or not packets[0][1]:
        why.append("its first packet is no keyframe")
    elif any(b - a > 1.0 + 1e-3 for a, b in zip(keys, keys[1:] + [max(t for t, _ in packets)])):
        why.append("keyframes more than 1 s apart")
    return why


def conform_argv(src, dst, p, tonemap=None):
    """(argv, assumed, notes) of the conform that makes clip.mp4 from orig: the module's note says what it gives."""
    v = p["video"]
    rate, cfr = rate_of(v)
    (rng, mtx, pri, trc), assumed = colour(v)
    notes = []
    w, h = int(v.get("width") or 0), int(v.get("height") or 0)
    sar = sar_of(v)
    if sar != 1:
        w = int(round(w * sar / 2)) * 2
        notes.append(f"non-square pixels ({v.get('sample_aspect_ratio')}) scaled to square: {w}×{h}")
    rot = rotation(v)
    if rot in (90, 270):
        w, h = h, w
    if rot:
        notes.append(f"turned upright ({rot}°)")
    w, h = w - w % 2, h - h % 2
    chain = []
    if v.get("field_order") not in (None, "progressive", "unknown"):
        chain.append("bwdif=mode=send_frame:parity=auto:deint=interlaced")
        notes.append(f"deinterlaced ({v.get('field_order')}, bwdif)")
    if trc in HDR:
        if not tonemap:
            raise Failed(f"HDR footage ({trc}): converting it to SDR is a creative choice: --tonemap hable (or mobius, reinhard), or keep it out")
        chain.append(f"zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap={tonemap}:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
        notes.append(f"HDR ({trc}) tone-mapped to SDR BT.709 with {tonemap}")
    chain.append(f"scale={w}:{h}:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix={SWS_MATRIX.get(mtx, 'bt709')}:in_range={rng}"
                 ":out_color_matrix=bt709:out_range=tv,setsar=1,format=yuv420p,setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv")
    if not cfr:
        notes.append(f"a variable frame rate made constant at {frate(rate)}")
    gop = max(1, math.floor(float(rate)))
    vstart = float(v.get("start_time") or 0) - float(p["format"].get("start_time") or 0)
    argv = ["ffmpeg", "-v", "error", "-y"] + (["-ss", f"{vstart:.6f}"] if vstart > 5e-4 else []) + ["-i", str(src), "-map", "0:v:0"]
    if p["audio"]:
        argv += ["-map", "0:a:0"]
    argv += ["-vf", ",".join(chain), "-fps_mode", "cfr", "-r", frate(rate), "-c:v", "libx264", "-profile:v", "high", "-preset", "medium", "-crf", "12",
             "-g", str(gop), "-keyint_min", str(gop), "-sc_threshold", "0", "-flags", "+cgop",
             "-color_range", "tv", "-colorspace", "bt709", "-color_trc", "bt709", "-color_primaries", "bt709"]
    if p["audio"]:
        argv += ["-af", "aresample=48000:async=1:first_pts=0", "-c:a", "aac", "-b:a", "256k"]
    argv += ["-movflags", "+faststart", str(dst)]
    return argv, assumed, notes, gop, rate


def scan(path):
    """(crop [w, h, x, y] or None, the hard cuts' times) of a clip, in one decode: cropdetect and scdet (playbook/05)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-v", "info", "-i", str(path), "-map", "0:v:0", "-vf",
                        "cropdetect=limit=24:round=2:reset=0,scdet=t=10:s=1", "-an", "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    crops = re.findall(r"crop=(\d+):(\d+):(\d+):(\d+)", r.stderr)
    cuts = sorted({round(float(t), 3) for t in re.findall(r"lavfi\.scd\.time:\s*([\d.]+)", r.stderr)})
    return ([int(x) for x in crops[-1]] if crops else None), cuts


def facts(folder, orig, conformed, rel_range, conform_cmd, assumed, gop, audio, source):
    """clip.json's content."""
    clip = folder / ("clip.mp4" if conformed else orig.name)
    p = probe(clip)
    v = p["video"]
    rate, _ = rate_of(v)
    nframes = int(v.get("nb_read_packets") or v.get("nb_frames") or 0)
    crop, cuts = scan(clip)
    w, h = int(v.get("width")), int(v.get("height"))
    if crop and crop == [w, h, 0, 0]:
        crop = None
    col, more = colour(v)
    return {"v": 1, "id": source["id"], "asset": source["id"], "file": clip.name, "sha256": ledger.sha256_file(clip), "rate": frate(rate), "frames": nframes,
            "duration": round(nframes / float(rate), 3) if nframes else round(float(p["format"].get("duration") or 0), 3), "size": [w, h],
            "sar": "1:1" if sar_of(v) == 1 else str(v.get("sample_aspect_ratio")), "color": col, "assumed": assumed + ([] if conformed else more),
            "gop": gop, "audio": audio, "from": {"file": orig.name, "sha256": ledger.sha256_file(orig), "range": rel_range, "conform": conform_cmd},
            "crop": crop, "cuts": cuts, "words": None, "sync": None, "source": {k: source[k] for k in ("site", "ref", "page") if source.get(k)}}


def keyframe_at(url, a):
    """The time of the video keyframe at or before a, in the file's own seconds (ffprobe seeks backward to it)."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-read_intervals", f"{a:.6f}%+2", "-show_entries", "packet=pts_time,flags",
             "-of", "csv=p=0", url], "ffprobe (finding the keyframe)")
    for line in r.stdout.splitlines():
        t, _, fl = line.partition(",")
        if "K" in fl:
            try:
                return float(t)
            except ValueError:
                break
    raise Failed(f"no keyframe found at or before {a} s")


def range_copy(url, dest, a, b, opener, rate):
    """orig as the seconds [keyframe ≤ a, b] of the remote file, its own packets (stream copy) in Matroska, read through
    fetch.serve. Matroska, whatever the source's container: an MP4 would hide the keyframe under an edit list (the copy
    starts a hair after it, so the seek lands on it and not on the one before), and the conform would lose that frame.
    → (the range taken, in the file's seconds; bytes read; the file's size or None)."""
    tmp = dest.with_name(f".{dest.stem}.part{dest.suffix}")
    with fetch.serve(url, opener=opener, rate=rate) as (local, st):
        k = keyframe_at(local, a)
        if k > a + 1e-3:
            raise Failed(f"the keyframe found ({k:.3f} s) is after {a} s")
        try:
            run(["ffmpeg", "-v", "error", "-y", "-ss", f"{k + 0.0005:.6f}", "-i", local, "-t", f"{b - k:.6f}", "-map", "0:v:0", "-map", "0:a:0?",
                 "-c", "copy", str(tmp)], f"ffmpeg (taking {a}–{b} s)")
        except Failed:
            tmp.unlink(missing_ok=True)
            if st["errors"]:
                raise Failed(st["errors"][-1])
            raise
    os.replace(tmp, dest)
    d = float(probe(dest)["format"].get("duration") or 0)
    return [round(k, 3), round(k + d, 3)], st["bytes"], st["size"]


def conform(folder, orig, tonemap=None, force=False):
    """clip.mp4 (when orig is not fit as it is, or force: a range copy, whose first frame may sit under an edit list) and
    audio.wav beside orig → (conformed, the command, assumed, notes, gop, audio, p)."""
    p = probe(orig)
    if p["video"] is None:
        raise Failed(f"{orig.name}: no video stream")
    why = unfit(orig, p, video_packets(orig)) or (["a range copy"] if force else [])
    conformed, cmd, assumed, notes = bool(why), None, [], []
    rate, _ = rate_of(p["video"])
    gop = None
    if conformed:
        tmp = folder / ".clip.part.mp4"
        argv, assumed, notes, gop, rate = conform_argv(orig, tmp, p, tonemap)
        try:
            run(argv, "the conform (clip.mp4)")
        except Failed:
            tmp.unlink(missing_ok=True)
            raise
        os.replace(tmp, folder / "clip.mp4")
        cmd = " ".join(argv[:-1] + ["clip.mp4"]).replace(str(orig), orig.name)
        notes = [f"conformed: {', '.join(why)}"] + notes
    else:
        keys = [t for t, k in video_packets(orig) if k]
        gop = max(1, round(min((b - a for a, b in zip(keys, keys[1:])), default=1) * float(rate)))
    audio = None
    if p["audio"]:
        v = p["video"]
        vstart = float(v.get("start_time") or 0) - float(p["format"].get("start_time") or 0)
        ch = int(p["audio"].get("channels") or 2)
        tmp = folder / ".audio.part.wav"
        run(["ffmpeg", "-v", "error", "-y"] + (["-ss", f"{vstart:.6f}"] if vstart > 5e-4 else []) + ["-i", str(orig), "-map", "0:a:0", "-vn",
             "-af", "aresample=48000:async=1:first_pts=0", "-c:a", "pcm_s16le"] + (["-ac", "2"] if ch > 2 else []) + [str(tmp)], "the sound (audio.wav)")
        os.replace(tmp, folder / "audio.wav")
        audio = {"file": "audio.wav", "sha256": ledger.sha256_file(folder / "audio.wav"), "rate": 48000, "channels": min(ch, 2)}
    return conformed, cmd, assumed, notes, gop, audio, p


# ---- the frame grid (the edit list's two functions; tools/timegrid.py when it lands) ----

def frame_from(t, fps):
    """The first frame at or after t: ⌈t·fps − 10⁻⁶⌉ (render.mjs's total)."""
    return math.ceil(t * fps - 1e-6)


def frame_at(t, rate):
    """The frame on screen at t: ⌊t·rate + 10⁻⁶⌋."""
    return math.floor(t * rate + 1e-6)


# ---- commands ----

def read_clip(project, cid):
    f = project / FOOTAGE / cid / "clip.json"
    try:
        c = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Usage(f"no clip {cid} in {FOOTAGE.as_posix()}/ ({e.__class__.__name__}): bin/vh footage list {A.shown(project, project)}")
    if c.get("v") != 1:
        raise Usage(f"{f}: not a clip.json of version 1")
    return c, f


def clips(project):
    out_ = []
    base = project / FOOTAGE
    if base.is_dir():
        for d in sorted(base.iterdir()):
            f = d / "clip.json"
            if f.is_file():
                try:
                    out_.append(json.loads(f.read_text(encoding="utf-8")))
                except ValueError:
                    continue
    return out_


def write_json(f, d):
    tmp = f.with_name(f".{f.name}.{os.getpid()}")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, f)


def rerecord(project, cid, why):
    """The clip folder's record, its tree hash taken again after clip.json changed."""
    rec, _, _ = ledger.add(project, (project / FOOTAGE / cid).as_posix() + "/", id=cid, update=True, by=f"{PROG} {why}")
    return rec


def note_activity(what, paths):
    try:
        import activity
        activity.note(what, [str(p) for p in paths])
    except Exception:   # the log never fails a command
        pass


def policy_line(cls, policy):
    return "taken" if licenses.accepted(cls, policy) else f"not taken under {policy}"


def cmd_search(a):
    opener = fetch.opener_from(a.offline)
    policy = ledger.policy_of(A.find(a.project))[0] if a.project else "strict"
    try:
        items = search(a.site, a.query, a.n, a.type, opener)
    except fetch.FetchError as e:
        raise Failed(str(e))
    for it in items:
        it["taken"] = licenses.accepted(it["class"], policy)
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} search", "site": a.site, "query": a.query, "type": a.type, "policy": policy,
                          "results": items}, ensure_ascii=False, indent=1))
    say(f"footage search {a.site}: {len(items)} result(s) for {a.query!r}" + (f" ({a.type})" if a.type != "any" else "") + f" · Assets: {policy}")
    for it in items:
        bits = [x for x in (it.get("date"), it.get("kind"), f"{it['size'][0]}×{it['size'][1]}" if it.get("size") and all(it["size"]) else "",
                            f"{float(it['duration']):.0f} s" if it.get("duration") else "") if x]
        lic = it.get("license") or it.get("license_url") or "no licence on record"
        mark = " " if it["taken"] else "!"
        say(f" {mark} {it['ref']}  {it.get('title', '')[:70]}" + (f"  · {' · '.join(bits)}" if bits else ""))
        say(f"     {it['class']}: {lic[:90]}" + ("" if it["taken"] else f" ({policy_line(it['class'], policy)}: {it['why']})"))
    return 0


def cmd_files(a):
    try:
        fs = files(a.ref, fetch.opener_from(a.offline))
    except fetch.FetchError as e:
        raise Failed(str(e))
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} files", "ref": a.ref, "files": fs}, ensure_ascii=False, indent=1))
    say(f"footage files {a.ref}: {len(fs)}")
    for f in fs:
        size = f"{f['bytes'] / 1e6:,.1f} MB" if f.get("bytes") else ""
        say(f"  {f['name']}" + "".join(f"  · {x}" for x in (size, f.get("format"), f.get("source")) if x))
    return 0


def parse_range(s):
    m = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*[:-]\s*(\d+(?:\.\d+)?)\s*", s or "")
    if not m or float(m.group(1)) >= float(m.group(2)):
        raise Usage(f"{s!r}: start:end in seconds, start before end (12.5:20)")
    return float(m.group(1)), float(m.group(2))


def default_id(it):
    base = {"archive": "ia", "commons": "wc", "nasa": "nasa"}.get(it["site"], "ft") + "-" + (it.get("id") or "clip").removeprefix("File:")
    return ledger.slug(re.sub(r"\.[A-Za-z0-9]{2,5}$", "", base))


def cmd_get(a):
    project = A.find(a.project)
    rng = parse_range(a.range) if a.range else None
    if a.license_class and a.license_class not in licenses.CLASSES:
        raise Usage(f"--class {a.license_class}: one of {', '.join(licenses.CLASSES)}")
    if a.id and not ledger.ID.match(a.id):
        raise Usage(f"--id {a.id}: letters, digits, . _ - (up to 64, not starting with . _ -)")
    try:
        rate = fetch.rate_of(a.rate)
    except ValueError as e:
        raise Usage(str(e))
    opener = fetch.opener_from(a.offline)
    media_opener = opener if isinstance(opener, fetch.Replay) else fetch.Live()   # a recording keeps no one's footage
    try:
        it = resolve(a.ref, opener, file=a.file, rendition=a.rendition)
    except fetch.FetchError as e:
        raise Failed(str(e))
    for k in ("title", "author", "page"):
        if getattr(a, k):
            it[k] = getattr(a, k)
    if a.license is not None or a.license_url is not None:
        it["license"], it["license_url"] = a.license or "", a.license_url or ""
        cls, why = licenses.classify(it["license"], it["license_url"])
        by = "classifier"
    else:
        cls, why, by = judge(it["site"], it)
    if a.license_class:
        cls, why, by = a.license_class, "given with --class", "given"
    policy, pfrom = ledger.policy_of(project)
    if not licenses.accepted(cls, policy):
        raise Failed(f"{it['ref']}: {cls} ({it.get('license') or it.get('license_url') or 'no licence'}): {why}. Assets: {policy} ({pfrom}) does not take it: "
                     "nothing downloaded. Another item; --class when its page says what this cannot read; or, if the user takes the risk, their "
                     "BRIEF says Assets: record")
    if rng and it["kind"] != "video":
        raise Usage(f"--range is for a video; {it['ref']} is a picture")
    cid = a.id or default_id(it)
    _, ents, _ = ledger.entries(project)
    if any(e["record"].get("id") == cid for e in ents):
        raise Usage(f"the id {cid} is on record already: --id another (ids are never reused)")
    note = "; ".join(x for x in ([NASA_NOTE] if it["site"] == "nasa" else []) + ([f"restrictions: {it['restrictions']}"] if it.get("restrictions") else [])
                     + ([a.note] if a.note else []) if x) or None
    src = {"origin": "download", "url": it.get("page") or None, "file_url": it["file_url"], "provider": {"archive": "internet-archive", "commons": "wikimedia-commons",
           "nasa": "nasa"}.get(it["site"]), "provider_id": it.get("id") if it["site"] != "url" else None, "title": it.get("title") or None,
           "author": it.get("author") or None, "retrieved": time.strftime("%Y-%m-%d")}
    differs = by == "site" and licenses.classify(it.get("license") or "", it.get("license_url") or "")[0] != cls   # the site's rule overrules the text
    lic = {"license": it.get("license") or None, "license_url": it.get("license_url") or None, "license_class": cls if by == "given" or differs else None}
    if by == "site" and not lic["license"]:
        lic["license"] = licenses.NAMES[cls]
    for n in it["notes"]:
        say(f"  · {n}")
    t0 = time.monotonic()
    got = {}
    try:
        if it["kind"] == "image":
            dest = project / "assets" / "img" / f"{cid}{it['ext']}"
            if dest.exists():
                raise Usage(f"{ledger.rel(project, dest)} is there already: --id another")
            dl = fetch.download(it["file_url"], dest, rate=rate, opener=media_opener, max_bytes=int(a.max_mb * 1e6))
            got = {"bytes": dl["bytes"]}
            target = dest
        else:
            folder = project / FOOTAGE / cid
            if (folder / "clip.json").exists():
                raise Usage(f"{ledger.rel(project, folder)}/ is there already: --id another")
            folder.mkdir(parents=True, exist_ok=True)
            orig = folder / ("orig.mkv" if rng else f"orig{it['ext']}")
            if orig.exists() and not rng:   # a get that stopped after the download (orig is only ever there whole)
                say(f"  · {ledger.rel(project, orig)} is there from a get that stopped: kept, not downloaded again")
                taken, got = None, {"bytes": 0}
            elif rng:   # a range is cheap to take again, and its keyframe is known only then
                taken, nbytes, size = range_copy(it["file_url"], orig, rng[0], rng[1], media_opener, rate)
                src["range"] = taken
                got = {"bytes": nbytes, "size": size, "range": taken}
            else:
                dl = fetch.download(it["file_url"], orig, rate=rate, opener=media_opener, max_bytes=int(a.max_mb * 1e6))
                got = {"bytes": dl["bytes"]}
                taken = None
            conformed, cmd, assumed, cnotes, gop, audio, _ = conform(folder, orig, a.tonemap, force=bool(rng))
            fx = facts(folder, orig, conformed, taken, cmd, assumed, gop, audio, dict(it, id=cid))
            fx["notes"] = cnotes
            write_json(folder / "clip.json", fx)
            got["clip"] = fx
            target = folder
    except fetch.FetchError as e:
        raise Failed(str(e))
    try:
        rec, _, _ = ledger.add(project, str(target), id=cid, kind=it["kind"], license=lic["license"], license_url=lic["license_url"],
                               license_class=lic["license_class"], source=src, attribution=a.attribution, used_by=[x.strip() for x in a.used_by.split(",") if x.strip()] if a.used_by else None,
                               tags=["footage", it["site"]], note=note, by=f"{PROG} get")
    except (ledger.Refused, ValueError, ledger.LedgerError) as e:
        raise Usage(f"downloaded to {ledger.rel(project, target)}, but not registered: {e}")
    note_activity(f"got {cid} ({it['ref']}, {rec['license']['class']})", [project / ledger.LEDGER, target])
    secs = time.monotonic() - t0
    c = got.get("clip")
    say(f"got {cid}: {it['kind']} {rec['path']} · {rec['license']['class']}" + (f" ({rec['license'].get('name')})" if rec["license"].get("name") else "")
        + (f" · {it['title'][:60]}" if it.get("title") else "") + f" · {secs:.0f} s")
    if got.get("range"):
        say(f"  took {got['range'][0]:.3f}–{got['range'][1]:.3f} s of the original (from the keyframe at or before {rng[0]} s): read {fetch.size_of(got['bytes'])}"
            + (f" of its {fetch.size_of(got['size'])}" if got.get("size") else ""))
    if c:
        say(f"  clip: {c['file']} · {c['size'][0]}×{c['size'][1]} · {c['rate']} fps · {c['frames']} frames ({c['duration']:.3f} s) · gop {c['gop']}"
            + (" · sound → audio.wav" if c["audio"] else " · no sound") + (f" · black bars {c['crop']}" if c["crop"] else "") + (f" · {len(c['cuts'])} cut(s) inside" if c["cuts"] else ""))
        for x in c.get("notes", []) + c["assumed"]:
            say(f"  · {x}")
    if licenses.risks(rec["license"]["class"]):
        say(f"  ! {', '.join(licenses.RISK_WORDS[k] for k in licenses.risks(rec['license']['class']))}: listed by bin/vh assets check (Assets: {policy})")
    if licenses.attribution(rec["license"]["class"]) == "required" and not (rec.get("attribution") or rec["source"].get("author")):
        say("  ! its licence asks for a credit and no author is on record: bin/vh assets add … --update --author A")
    if note:
        say(f"  · {note}")
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} get", "project": str(project), "record": rec, "item": {k: v for k, v in it.items() if k != "notes"},
                          "download": {k: v for k, v in got.items() if k != "clip"}, "clip": c}, ensure_ascii=False, indent=1))
    return 0


def cmd_list(a):
    project = A.find(a.project)
    cs = clips(project)
    _, ents, _ = ledger.entries(project)
    by_id = {e["record"].get("id"): e["record"] for e in ents}
    rows = []
    for c in cs:
        r = by_id.get(c.get("asset")) or {}
        rows.append({"clip": c, "class": ledger.class_of(r) if r else None, "on_record": bool(r)})
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} list", "project": str(project), "clips": rows}, ensure_ascii=False, indent=1))
    say(f"footage: {len(cs)} clip(s) in {FOOTAGE.as_posix()}/")
    for x in rows:
        c = x["clip"]
        s = c.get("sync")
        rng = (c.get("from") or {}).get("range")
        say(f"  {c.get('id')}  {c.get('size', ['?', '?'])[0]}×{c.get('size', ['?', '?'])[1]} · {c.get('rate')} fps · {c.get('duration', 0):.3f} s"
            + (f" · {rng[0]}–{rng[1]} s of the original" if rng else "") + (f" · sync {s['group']}: s = {s['k']:g}·M + {s['c']:g}" if s else " · no sync")
            + (f" · {x['class']}" if x["class"] else " · ! not on record"))
    return 0


def cmd_sync(a):
    project = A.find(a.project)
    if a.id:
        c, f = read_clip(project, a.id)
        if a.clear:
            c["sync"] = None
        else:
            if a.group is None or a.c is None:
                raise Usage("--group and --c set a clip's row (--clear takes it out)")
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", a.group):
                raise Usage(f"--group {a.group!r}: letters, digits, _ and -")
            if a.k <= 0:
                raise Usage("--k is the slow-motion factor (2.5 for a 2.5× slow source; 1 for real time)")
            c["sync"] = {"group": a.group, "c": round(a.c, 4), "k": a.k, **({"by": a.by} if a.by else {})}
        write_json(f, c)
        rerecord(project, a.id, "sync")
        note_activity(f"sync {a.id}: {'cleared' if a.clear else 's = {}·M + {}'.format(a.k, a.c)}", [f])
    elif a.group or a.c is not None or a.clear:
        raise Usage("a clip's id first: bin/vh footage sync <project> <id> --group G --c C")
    cs = [c for c in clips(project) if c.get("sync")]
    groups = {}
    for c in cs:
        groups.setdefault(c["sync"]["group"], []).append(c)
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} sync", "project": str(project), "groups": {g: [{"id": c["id"], **c["sync"], "rate": c["rate"],
                          "duration": c["duration"]} for c in v] for g, v in groups.items()}}, ensure_ascii=False, indent=1))
    say(f"footage sync: {len(cs)} clip(s) in {len(groups)} group(s): s = k·M + c (s: the clip's seconds, M: the group's clock)")
    for g, v in groups.items():
        say(f"  {g}")
        for c in v:
            s = c["sync"]
            lo, hi = (0 - s["c"]) / s["k"], (c["duration"] - s["c"]) / s["k"]
            say(f"    {c['id']:<24} s = {s['k']:g}·M + {s['c']:g}   covers M {lo:+.3f} … {hi:+.3f}" + (f"   ({s['by']})" if s.get("by") else ""))
    return 0


def brief_fps(project):
    try:
        s = (project / "BRIEF.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"^\s*[-*]\s*(?:Frame ?rate|fps|帧率)\s*[:：]\s*(\d+)", s, re.M | re.I) or re.search(r"(\d{2})\s*fps", s, re.I)
    return int(m.group(1)) if m else None


def cmd_frames(a):
    project = A.find(a.project)
    c, _ = read_clip(project, a.id)
    fa, fb = parse_range(a.film)
    fps = a.fps or brief_fps(project) or 30
    if a.t0 is None and a.at is None:
        raise Usage("say how film time maps to the clip: --t0 T (the group's zero is at film time T: needs the clip's sync), or --at S (the clip's second at film time a)")
    if a.t0 is not None and a.at is not None:
        raise Usage("--t0 or --at, not both")
    if a.t0 is not None and not c.get("sync"):
        raise Usage(f"{a.id} has no sync row: bin/vh footage sync <project> {a.id} --group G --c C, or --at S")
    rate = Fraction(c["rate"])
    k0, k1 = frame_from(fa, fps), frame_from(fb, fps)
    if k1 <= k0:
        raise Usage(f"--film {a.film}: no frame at {fps} fps")
    def src_time(n):
        t = n / fps
        if a.t0 is not None:
            s = c["sync"]
            return s["k"] * (t - a.t0) + s["c"]
        return a.at + (t - fa)
    pick = {n: frame_at(src_time(n), float(rate)) for n in range(k0, k1)}
    lo, hi = min(pick.values()), max(pick.values())
    if lo < 0 or hi >= c["frames"]:
        bad = [n for n, j in pick.items() if j < 0 or j >= c["frames"]]
        raise Failed(f"film {bad[0] / fps:.3f}–{(bad[-1] + 1) / fps:.3f} s fall outside {a.id} (clip frames 0–{c['frames'] - 1}, "
                     f"{c['duration']:.3f} s): {'it begins later' if lo < 0 else 'it ends sooner'}; a shorter --film, or another --t0 / --at")
    name = a.name or a.id
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,50}", name):
        raise Usage(f"--name {name!r}: letters, digits, . _ -")
    dest = project / FRAMES / name
    ext = ".png" if a.png else ".jpg"
    width = max(5, len(str(k1 - 1)))
    rng_, mtx = c["color"][0], SWS_MATRIX.get(c["color"][1], "bt709")
    size = None
    if a.size:
        m = re.fullmatch(r"(\d+)[x×:](\d+)", a.size)
        if not m:
            raise Usage(f"--size {a.size!r}: WxH (1920x1080)")
        size = (int(m.group(1)), int(m.group(2)))
    W, H = size or tuple(c["size"])
    scl = f"scale={W}:{H}:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix={mtx}:in_range={rng_}:out_color_matrix=bt601:out_range=pc"
    if size and a.fit == "cover":
        scl = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix={mtx}:in_range={rng_}"
               f":out_color_matrix=bt601:out_range=pc,crop={W}:{H}")
    elif size:
        scl = (f"scale={W}:{H}:force_original_aspect_ratio=decrease:flags=lanczos+accurate_rnd+full_chroma_int:in_color_matrix={mtx}:in_range={rng_}"
               f":out_color_matrix=bt601:out_range=pc,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black")
    chain = scl + (f",{a.vf}" if a.vf else "") + (",format=rgb24" if a.png else ",format=yuvj444p")
    clip = project / FOOTAGE / a.id / c["file"]
    (project / FRAMES).mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=".frames-", dir=project / FRAMES))
    try:
        ss = (lo - 0.5) / float(rate)
        argv = ["ffmpeg", "-v", "error", "-y"] + (["-ss", f"{ss:.6f}"] if lo > 0 else []) + ["-i", str(clip), "-map", "0:v:0", "-vf", chain,
                "-frames:v", str(hi - lo + 1), "-fps_mode", "passthrough", "-start_number", str(lo)] + ([] if a.png else ["-q:v", "2"]) + [str(tmp / f"%07d{ext}")]
        run(argv, "ffmpeg (decoding the frames)")
        made = sorted(tmp.glob(f"*{ext}"))
        if len(made) != hi - lo + 1:
            raise Failed(f"decoded {len(made)} frames of the {hi - lo + 1} asked for ({lo}–{hi})")
        new = dest.with_name(f".{name}.new")
        shutil.rmtree(new, ignore_errors=True)
        new.mkdir(parents=True)
        for n, j in pick.items():
            shutil.copyfile(tmp / f"{j:07d}{ext}", new / f"{n:0{width}d}{ext}")
        spec = {"v": 1, "clip": a.id, "clip_sha256": c["sha256"], "fps": fps, "film": [fa, fb], "frames": [k0, k1], "name": f"%0{width}d{ext}",
                "map": {"t0": a.t0, "sync": c["sync"]} if a.t0 is not None else {"at": a.at}, "clip_frames": [lo, hi], "size": [W, H],
                "fit": a.fit if size else None, "vf": a.vf, "format": ext[1:], "made_by": f"{PROG} frames"}
        write_json(new / "frames.json", spec)
        if dest.exists():
            shutil.rmtree(dest)
        os.replace(new, dest)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    _, ents, _ = ledger.entries(project)
    by_id = {e["record"].get("id"): e["record"] for e in ents}
    srcrec = by_id.get(c.get("asset")) or {}
    fid = f"{name}.frames"
    lic = srcrec.get("license") or {"class": "unknown"}
    src = dict(srcrec.get("source") or {"origin": "download"})
    try:
        rec, old, _ = ledger.add(project, dest.as_posix() + "/", id=fid, kind="image", license=lic.get("name"), license_url=lic.get("url"),
                                 license_class=lic.get("class"), source=src, derived_from=c.get("asset"),
                                 tags=["frames"], note=f"film frames {k0}–{k1 - 1} at {fps} fps, baked from {a.id} by {PROG} frames", update=fid in by_id,
                                 by=f"{PROG} frames")
    except (ledger.Refused, ValueError, ledger.LedgerError) as e:
        raise Usage(f"baked into {ledger.rel(project, dest)}/, but not registered: {e}")
    note_activity(f"baked {k1 - k0} frames of {a.id} → {ledger.rel(project, dest)}/", [project / ledger.LEDGER, dest])
    dup = (k1 - k0) - len(set(pick.values()))
    say(f"frames: {a.id} → {ledger.rel(project, dest)} · film frames {k0}–{k1 - 1} at {fps} fps ({fa}–{fb} s) from clip frames {lo}–{hi}"
        + (f" · {dup} shown twice ({c['rate']} into {fps})" if dup > 0 else "") + f" · {W}×{H} {ext[1:]} · {'updated' if old else 'registered'} as {fid}")
    say(f"  the page draws {FRAMES.as_posix()}/{name}/${{String(Math.floor(t * {fps} + 1e-6)).padStart({width}, '0')}}{ext} at film time t")
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} frames", "project": str(project), "frames": spec, "record": rec}, ensure_ascii=False, indent=1))
    return 0


def parser():
    ap = argparse.ArgumentParser(prog=PROG, description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    sp = ap.add_subparsers(dest="cmd", metavar="{" + ",".join(SUB) + "}")
    p = sp.add_parser("search", prog=f"{PROG} search", help="one site's results, with their licence classes")
    p.add_argument("site", choices=SITES)
    p.add_argument("query")
    p.add_argument("--type", default="any", choices=("any", "video", "image"))
    p.add_argument("-n", type=int, default=15)
    p.add_argument("--project", help="say which results its Assets policy takes")
    p.add_argument("--json", action="store_true")
    p.add_argument("--offline")
    p = sp.add_parser("files", prog=f"{PROG} files", help="what an item has")
    p.add_argument("ref")
    p.add_argument("--json", action="store_true")
    p.add_argument("--offline")
    p = sp.add_parser("get", prog=f"{PROG} get", help="download into the project and register it")
    p.add_argument("project")
    p.add_argument("ref", metavar="ref|url")
    for flag, h in (("--id", None), ("--file", "an Archive item's file (footage files)"), ("--rendition", "a NASA rendition: " + ", ".join(NASA_ORDER)),
                    ("--range", "a:b, seconds of the original"), ("--rate", "a cap: 2M, 500K"), ("--license", "the licence as its page writes it"),
                    ("--license-url", None), ("--author", None), ("--title", None), ("--page", "the item's page (for a URL)"),
                    ("--attribution", "the credit line exactly as it must appear"), ("--used-by", "what it is for: S03,S05"), ("--note", None),
                    ("--tonemap", "HDR to SDR: hable, mobius or reinhard"), ("--offline", "DIR: the recorded answers")):
        p.add_argument(flag, help=h)
    p.add_argument("--class", dest="license_class", help="the licence class outright: " + ", ".join(licenses.CLASSES))
    p.add_argument("--max-mb", type=float, default=800.0)
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("list", prog=f"{PROG} list", help="the project's clips")
    p.add_argument("project")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("sync", prog=f"{PROG} sync", help="the sync table: s = k·M + c")
    p.add_argument("project")
    p.add_argument("id", nargs="?")
    p.add_argument("--group")
    p.add_argument("--c", type=float, help="the clip's second at the group's zero (M = 0)")
    p.add_argument("--k", type=float, default=1.0, help="slow motion: the source's seconds per second of the event")
    p.add_argument("--by", help="how it was measured")
    p.add_argument("--clear", action="store_true")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("frames", prog=f"{PROG} frames", help="bake frames named by the film's frame numbers")
    p.add_argument("project")
    p.add_argument("id")
    p.add_argument("--film", required=True, help="a:b, film seconds")
    p.add_argument("--fps", type=int)
    p.add_argument("--t0", type=float, help="the film time of the sync group's zero")
    p.add_argument("--at", type=float, help="the clip's second at film time a (a clip with no sync)")
    p.add_argument("--size")
    p.add_argument("--fit", choices=("cover", "contain"), default="cover")
    p.add_argument("--vf")
    p.add_argument("--name")
    p.add_argument("--png", action="store_true")
    p.add_argument("--json", action="store_true")
    return ap


def main(argv):
    global out
    if not argv:
        parser().print_usage(sys.stderr)
        print(f"{PROG}: a subcommand ({', '.join(SUB)})", file=sys.stderr)
        return 2
    a = parser().parse_args(argv)
    if a.cmd is None:
        parser().print_usage(sys.stderr)
        return 2
    if getattr(a, "json", False):
        out = sys.stderr
        A.out = sys.stderr
    if a.cmd in ("get", "frames") and not shutil.which("ffmpeg"):
        print(f"{PROG} {a.cmd}: needs ffmpeg and ffprobe (bin/vh doctor)", file=sys.stderr)
        return 2
    try:
        return {"search": cmd_search, "files": cmd_files, "get": cmd_get, "list": cmd_list, "sync": cmd_sync, "frames": cmd_frames}[a.cmd](a)
    except (Usage, A.Usage) as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 2
    except (Failed, fetch.FetchError) as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
