"""bin/vh proxy and bin/vh thumbs: what a client scrubs with. ffmpeg only; no browser for a film.

usage: bin/vh proxy <film | project> [--size 360] [--gop N] [--crf 28] [--full] [--out dir] [--json]
       bin/vh thumbs <film | project> [--every 2] [--width 160] [--shot-width 320] [--full] [--out dir] [--json]
A project means its film: the newest current version (bin/vh versions), else the newest video under out/ with a
.render.json, else the newest video under out/ (not out/check, out/review, out/proxy, out/versions); thumbs with no film
draws the page instead (bin/vh frames). The outputs go to <project>/out/proxy/ (outside a project: proxy/ beside the film),
named as bin/vh check names its records (out/review/sketch.mp4 → review-sketch).

proxy   <name>.mp4: the film at --size px on its short side (360; never larger than the film), H.264 with a keyframe every
        --gop frames (a fifth of a second by default: 6 at 30 fps) and no B-frames, tuned for fast decoding, the film's
        sound as AAC: a seek is never more than --gop frames of decoding. <name>.mp4.json records what it was made from.
        Run again: nothing to do while the film is the same; after patches in place (bin/vh versions: every step since
        the proxy's version a patch of that film), only the proxy's keyframe windows around the frames drawn again are
        encoded and joined in, the rest copied; anything else (a render, other settings, --full) makes it anew
thumbs  <name>.thumbs/: a tile every --every seconds (2), --width px wide (160), in sheets of 10 x 10 (sheet-01.jpg …), one
        picture a shot (shots/<id>.jpg, --shot-width px wide) at its `at` or 60 % into it (as bin/vh storyboard picks), and
        thumbs.json, the map: every tile's time, frame, sheet and x, y; every shot's time, frame, span and file. The shots:
        shots.json in the project, else, for a film, its .render.json (the page's window.film.shots when it was rendered:
        no browser is started for a film, so a film without them gets no shot pictures), and with no film, the page's.
        Frames come from a proxy made of this same film when there is one (fast), else the film, else the page.
        Run again after patches in place: only the tiles and shots in the frames drawn again are taken anew
JSON (--json prints the record; "version": 1): tools/desk/README.md, 给客户端的数据, has the fields.
Exit: 0 made or up to date · 1 ffmpeg or the page failed · 2 usage, no film (proxy) and nothing to draw (thumbs).
"""
import concurrent.futures as cf, json, math, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import versions as V   # noqa: E402
from timegrid import frame_at, frame_from   # noqa: E402  (seconds to frames, the one way)

VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
SKIP = {"check", "review", "proxy", "versions", "frames"}


class Usage(Exception):
    pass


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def probe(f):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=index,codec_type,width,height,r_frame_rate,nb_frames:format=duration",
             "-show_data_hash", "sha256", "-of", "json", str(f)])
    if r.returncode:
        raise RuntimeError(f"ffprobe cannot read {f}: {(r.stderr or '').strip()[:200]}")
    j = json.loads(r.stdout or "{}")
    v = next((s for s in j.get("streams") or [] if s.get("codec_type") == "video"), None)
    if not v:
        raise RuntimeError(f"{f} has no video")
    a, _, b = str(v.get("r_frame_rate", "0/1")).partition("/")
    fps = float(a) / float(b or 1) if float(b or 1) else 0
    dur = float((j.get("format") or {}).get("duration") or 0)
    n = int(v["nb_frames"]) if str(v.get("nb_frames", "")).isdigit() else (frame_from(dur, fps) if fps > 0 else 0)
    return {"width": v.get("width"), "height": v.get("height"), "fps": fps, "frames": n, "duration": dur,
            "audio": any(s.get("codec_type") == "audio" for s in j.get("streams") or []), "extradata": v.get("extradata_hash")}


def project_of(p):
    return V.project_of(p)


def rel(base, p):
    return V.rel(base, p) if base else str(p)


def name_of(film, project):
    """out/film.mp4 → film; out/review/sketch.mp4 → review-sketch (bin/vh check's record names)."""
    if project:
        parts = list(Path(os.path.relpath(Path(film).resolve(), Path(project).resolve())).with_suffix("").parts)
        if parts and parts[0] == "out":
            parts = parts[1:]
        return "-".join(parts)
    return Path(film).stem


def films_in(project):
    out = Path(project) / "out"
    found = []
    if out.is_dir():
        for d, dirs, files in os.walk(out):
            depth = Path(d).relative_to(out).parts
            dirs[:] = [x for x in dirs if not x.startswith(".") and not (not depth and x in SKIP) and len(depth) < 3]
            found += [Path(d) / f for f in files if Path(f).suffix.lower() in VIDEO and not f.startswith(".")]
    return sorted(found, key=lambda p: -p.stat().st_mtime)


def pick(target):
    """(film or None, project, page or None) for a film or a project."""
    p = Path(target).expanduser()
    if p.is_file() and p.suffix.lower() in VIDEO:
        return p.resolve(), project_of(p), None
    project = project_of(p) if p.exists() else None
    if project is None:
        import review
        project = review.find_project(target)
    if project is None:
        raise Usage(f"no film or project at {target}")
    film = None
    try:
        L = V.listing(project)
        cur = sorted((x for x in L["versions"] if x["state"] == "current"), key=lambda x: -(x.get("t") or 0))
        if cur:
            film = Path(project) / cur[0]["file"]
    except ValueError:
        pass
    if film is None:
        vids = films_in(project)
        film = next((f for f in vids if Path(str(f) + ".render.json").is_file()), vids[0] if vids else None)
    page = next((Path(project) / n for n in ("edit.json", "film.html", "index.html", "studio.html") if (Path(project) / n).is_file()), None)
    return (film.resolve() if film else None), Path(project), page


def out_dir(film, project, given):
    if given:
        return Path(given).resolve()
    return Path(project) / "out" / "proxy" if project else Path(film).parent / "proxy"


def ident(f):
    i = V.identity(f)
    return {"size": i[0], "mtime": i[1]} if i else None


def current_version(project, film):
    if not project:
        return None
    try:
        r = V.read(project)
    except ValueError:
        return None
    e = V.current_at(project, r, V.rel(project, film))
    return e["id"] if e else None


def windows(spans, g, n):
    """Film frames drawn again → the windows of whole GOPs (g frames) around them, merged where they meet."""
    out = []
    for a, b in sorted(spans):
        A, B = (a // g) * g, min(n, (b // g + 1) * g)
        if out and A <= out[-1][1]:
            out[-1][1] = max(out[-1][1], B)
        else:
            out.append([A, B])
    return out


def note(summary, outputs):
    try:
        import activity
        activity.note(summary, outputs)
    except Exception:
        pass


def save(path, rec):
    tmp = path.with_name(f".{path.name}.{os.getpid()}")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, path)


# ---- proxy ----

def scaled(w, h, short):
    if min(w, h) <= short:
        return w - w % 2, h - h % 2
    if w >= h:
        return 2 * round(w * short / h / 2), short - short % 2
    return short - short % 2, 2 * round(h * short / w / 2)


def x264(o):
    return ["-c:v", "libx264", "-preset", "veryfast", "-tune", "fastdecode", "-crf", str(o["crf"]), "-g", str(o["gop"]), "-keyint_min", str(o["gop"]),
            "-sc_threshold", "0", "-bf", "0", "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]


def make_proxy(film, info, o, dst):
    vf = f"scale={o['size'][0]}:{o['size'][1]}:flags=bilinear,setsar=1"
    tmp = dst.with_name(f".{dst.name}.tmp.mp4")
    r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(film), "-map", "0:v:0", "-map", "0:a:0?", "-vf", vf, *x264(o),
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(tmp)])
    if r.returncode or not tmp.is_file():
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg could not make the proxy: {(r.stderr or '').strip()[:300]}")
    os.replace(tmp, dst)


def refresh_proxy(film, info, o, dst, wins):
    """Encode the windows anew from the film and join them into the proxy, the rest of it copied. → None, or why not."""
    fps, n = info["fps"], info["frames"]
    vf = f"scale={o['size'][0]}:{o['size'][1]}:flags=bilinear,setsar=1"
    old = probe(dst)
    if old["frames"] != n:
        return f"the proxy has {old['frames']} frames, the film {n}"
    with tempfile.TemporaryDirectory(prefix=".proxy-", dir=dst.parent) as w:
        w = Path(w)
        pieces = {}
        for i, (A, B) in enumerate(wins):
            piece = w / f"piece{i}.mp4"
            ss = ["-ss", f"{(A - 0.5) / fps:.6f}"] if A > 0 else []
            r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", *ss, "-i", str(film), "-map", "0:v:0", "-frames:v", str(B - A), "-vf", vf, *x264(o), "-an", str(piece)])
            if r.returncode or not piece.is_file():
                return f"encoding frames {A}–{B - 1} failed ({(r.stderr or '').strip()[:120]})"
            pp = probe(piece)
            if pp["frames"] != B - A or pp["extradata"] != old["extradata"]:
                return f"frames {A}–{B - 1} did not come out as the proxy's ({pp['frames']} frames, {'same' if pp['extradata'] == old['extradata'] else 'another'} encoder setup)"
            pieces[A] = (piece, B - A)
        cuts = sorted({k for A, B in wins for k in (A, B) if 0 < k < n})
        bounds = [0, *cuts, n]
        parts = []
        if cuts:
            r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(dst), "-map", "0:v:0", "-c", "copy", "-f", "segment", "-segment_frames",
                     ",".join(map(str, cuts)), "-reset_timestamps", "1", str(w / "seg%d.mp4")])
            segs = sorted(w.glob("seg*.mp4"), key=lambda p: int(p.stem[3:]))
            if r.returncode or len(segs) != len(bounds) - 1:
                return "the proxy did not cut on its keyframes"
            for i in range(len(bounds) - 1):
                parts.append(pieces.get(bounds[i]) or (segs[i], bounds[i + 1] - bounds[i]))
        else:
            parts.append(pieces[0])
        (w / "list.txt").write_text("".join(f"file '{p.name}'\nduration {k / fps:.9f}\n" for p, k in parts))
        video, joined = w / "video.mp4", w / "joined.mp4"
        r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-f", "concat", "-safe", "0", "-i", str(w / "list.txt"), "-map", "0:v", "-c", "copy", str(video)])
        if r.returncode:
            return f"joining failed ({(r.stderr or '').strip()[:120]})"
        r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(video), "-i", str(dst), "-map", "0:v", "-map", "1:a?", "-c", "copy", "-movflags", "+faststart", str(joined)])
        if r.returncode or probe(joined)["frames"] != n:
            return "the joined proxy is not whole"
        os.replace(joined, dst)
    return None


def cmd_proxy(a):
    film, project, _ = pick(a["target"])
    if film is None:
        raise Usage(f"no film in {project} to make a proxy of: bin/vh render first (bin/vh thumbs draws the page)")
    info = probe(film)
    if not (info["fps"] > 0 and info["frames"] > 0):
        raise RuntimeError(f"{film}: no frame rate or frames")
    gop = a["gop"] or max(1, round(info["fps"] / 5))
    o = {"size": list(scaled(info["width"], info["height"], a["size"])), "gop": gop, "crf": a["crf"]}
    d = out_dir(film, project, a["out"]); d.mkdir(parents=True, exist_ok=True)
    name = name_of(film, project)
    dst, recf = d / f"{name}.mp4", d / f"{name}.mp4.json"
    old = V.load_json(recf) if recf.is_file() and dst.is_file() else None
    src_rel, ver, idn = rel(project, film), current_version(project, film), ident(film)
    T0, made, spans = time.time(), "full", None
    same_o = old and old.get("settings") == o and old.get("source") == src_rel
    why = None
    if same_o and old.get("source_ident") == idn and not a["full"]:
        made = "up to date"
    elif same_o and not a["full"] and old.get("source_version") and ver and project:
        spans = V.drawn_since(project, src_rel, old["source_version"])
        if spans:
            wins = windows(spans, gop, info["frames"])
            why = refresh_proxy(film, info, o, dst, wins)
            made = "refreshed" if why is None else "full"
        else:
            why = "a step since its version was not a patch in place"
    if made == "full":
        make_proxy(film, info, o, dst)
    if made != "up to date":
        rec = {"version": 1, "tool": "bin/vh proxy", "source": src_rel, "source_ident": idn, "source_version": ver, "proxy": rel(project, dst),
               "settings": o, "fps": info["fps"], "frames": info["frames"], "duration": info["duration"], "audio": info["audio"],
               "made": made, "windows": windows(spans, gop, info["frames"]) if made == "refreshed" else None,
               "t": round(time.time(), 3), "at": V.iso(time.time()), "seconds": round(time.time() - T0, 2)}
        save(recf, rec)
    else:
        rec = old
    if a["json"]:
        print(json.dumps(dict(rec, state=made), ensure_ascii=False, indent=1))
    else:
        what = "up to date (the film is the one it was made of)" if made == "up to date" else "made" + (f" anew ({why})" if why else "") if made == "full" else \
            f"refreshed: {len(rec['windows'])} window(s) of frames encoded anew, {sum(B - A for A, B in rec['windows'])} of {info['frames']} frames"
        print(f"proxy: {rel(project, dst)} · {o['size'][0]}x{o['size'][1]}, a keyframe every {gop} frames, {'with' if info['audio'] else 'no'} sound · {what}"
              + (f" · {rec['seconds']} s" if made != "up to date" else ""))
    if made != "up to date":
        note(f"{src_rel} → {rel(project, dst)}: {made}", [dst, recf])
    return 0


# ---- thumbs ----

def shot_table(project, film, side):
    """[(id, start, end, at)] in film seconds, and where they came from: an edit list's film, the entries and the shots
    inside its pages as its .render.json recorded them; else the project's shot table; else the page's shots there."""
    import shot_source
    off = (side or {}).get("first_frame", 0) / ((side or {}).get("fps") or 1) if side else 0
    raw = (side or {}).get("shots")
    if (side or {}).get("kind") == "edit" and isinstance(raw, list):
        return [(str(s["id"]), float(s["start"]) - off, float(s["end"]) - off, None) for s in raw
                if isinstance(s, dict) and isinstance(s.get("start"), (int, float)) and isinstance(s.get("end"), (int, float))], \
            f"{rel(project, str(film) + '.render.json')} (the edit list's entries and the pages' shots)"
    try:
        shots, table = shot_source.parsed(project) if project else ([], None)
    except SystemExit as e:
        print(f"thumbs: {e}; no shot pictures", file=sys.stderr)
        return [], None
    if table:
        return [(s["id"], s["start"] - off, s["end"] - off, s["at"] - off if s["at"] is not None else None) for s in shots], table.name
    if isinstance(raw, list) and raw:
        return [(str(s["id"]), float(s["start"]) - off, float(s["end"]) - off, None) for s in raw
                if isinstance(s, dict) and isinstance(s.get("start"), (int, float)) and isinstance(s.get("end"), (int, float))], \
            f"{rel(project, str(film) + '.render.json')} (window.film.shots)"
    return [], None


def even(x):
    return max(2, int(x / 2 + 0.5) * 2)


def grab(src, fps, k, size, dst):
    ss = ["-ss", f"{(k - 0.5) / fps:.6f}"] if k > 0 else []
    r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", *ss, "-i", str(src), "-frames:v", "1", "-vf", f"scale={size[0]}:{size[1]}:flags=bicubic", "-q:v", "4", str(dst)])
    if r.returncode or not Path(dst).is_file():
        raise RuntimeError(f"frame {k}: {(r.stderr or '').strip()[:200]}")


def from_png(png, size, dst):
    r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(png), "-vf", f"scale={size[0]}:{size[1]}:flags=bicubic", "-q:v", "4", str(dst)])
    if r.returncode:
        raise RuntimeError(f"{png}: {(r.stderr or '').strip()[:200]}")


def sheets(tdir, n, cols=10, rows=10):
    out = []
    per = cols * rows
    for j in range(math.ceil(n / per)):
        k = min(per, n - j * per)
        f = tdir / f"sheet-{j + 1:02d}.jpg"
        r = run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-framerate", "1", "-start_number", str(j * per + 1), "-i", str(tdir / "tiles" / "%05d.jpg"),
                 "-vf", f"tile={min(cols, k)}x{math.ceil(k / cols)}", "-frames:v", "1", "-q:v", "4", str(f)])
        if r.returncode or not f.is_file():
            raise RuntimeError(f"ffmpeg could not make {f.name}: {(r.stderr or '').strip()[:200]}")
        out.append((f, k))
    return out


def cmd_thumbs(a):
    film, project, page = pick(a["target"])
    if film is None and page is None:
        raise Usage(f"nothing to take pictures of in {project}: no film and no page (film.html, index.html, studio.html)")
    T0 = time.time()
    side = V.load_json(str(film) + ".render.json") if film else None
    if film:
        info = probe(film)
        fps, dur, nfr = info["fps"], info["duration"], info["frames"]
        aspect = info["width"] / info["height"]
        name, base = name_of(film, project), film
    else:
        if not a["browser"]:
            raise Usage("no film, and no headless Chrome to draw the page: run it as bin/vh thumbs, or set CHROME_PATH")
        import shot_source
        if shot_source.is_edit(page):   # an edit list with no film yet: its frames drawn as bin/vh frames draws them
            import edit
            try:
                doc = edit.resolve(project)
            except edit.EditError as e:
                raise Usage("edit.json does not resolve: " + "; ".join(e.problems[:3])) from None
            live = {"shots": None}
            fps, dur, aspect, nfr = float(doc["fps"]), doc["frames"] / doc["fps"], doc["size"][0] / doc["size"][1], doc["frames"]
        else:
            live = shot_source.live_page(page, a["browser"])
            fps, dur, aspect = 30.0, float(live["duration"] or 0), live["width"] / live["height"]
            nfr = frame_from(dur, fps)
        name, base = Path(page).stem, page
    if not (dur > 0):
        raise RuntimeError("no length to take pictures of")
    d = out_dir(base, project, a["out"]) / f"{name}.thumbs"
    (d / "tiles").mkdir(parents=True, exist_ok=True); (d / "shots").mkdir(exist_ok=True)
    recf = d / "thumbs.json"
    old = V.load_json(recf) if recf.is_file() else None
    every, W, SW = a["every"], a["width"], a["shot_width"]
    H, SH = even(W / aspect), even(SW / aspect)   # every picture at exactly this size: the map's x and y hold
    tiles = [(i, round(i * every, 6), min(nfr - 1, frame_at(i * every, fps))) for i in range(max(1, math.ceil(dur / every - 1e-9)))]
    if film:
        shots, shots_from = shot_table(project, film, side)
    else:
        import vhdraw
        raw = live.get("shots")
        shots = [] if not raw else [(s["id"], s["start"], s["end"], s["at"]) for s in vhdraw.parse_shots(raw, page)[0]]
        shots_from = f"{rel(project, page)} (window.film.shots)" if shots else None
        sh, table = shot_source.parsed(project) if project else ([], None)
        if table:
            shots, shots_from = [(s["id"], s["start"], s["end"], s["at"]) for s in sh], table.name
    pick_t = lambda s, e, at: min(max(0.0, at if at is not None else s + 0.6 * (e - s)), dur - 0.5 / fps)   # noqa: E731
    shot_rows = [(sid, s, e, round(pick_t(s, e, at), 6)) for sid, s, e, at in shots if e > 0 and s < dur]
    shot_rows = [(sid, s, e, t, min(nfr - 1, frame_at(t, fps)), re.sub(r"[^\w.-]+", "-", sid) or "shot") for sid, s, e, t in shot_rows]
    # the source of the pictures: a proxy made of this same film (fast), else the film, else the page
    src, frm = base, "page" if not film else "film"
    if film:
        pj = V.load_json(out_dir(film, project, None) / f"{name}.mp4.json")
        pf = out_dir(film, project, None) / f"{name}.mp4"
        if pj and pf.is_file() and pj.get("source_ident") == ident(film):
            src, frm = pf, "proxy"
    settings = {"every": every, "width": W, "shot_width": SW, "cols": 10, "rows": 10}
    ver, idn = (current_version(project, film), ident(film)) if film else (None, None)
    # what to take: everything, or after patches in place only the tiles and shots in the frames drawn again
    todo_t, todo_s, made, why = list(tiles), list(shot_rows), "full", None
    if old and not a["full"] and film and old.get("settings") == settings and old.get("source") == rel(project, film) and \
            len(old.get("tiles") or []) == len(tiles) and [(x["id"], x["frame"]) for x in old.get("shots") or []] == [(x[0], x[4]) for x in shot_rows] and \
            all((d / "tiles" / f"{i + 1:05d}.jpg").is_file() for i, _, _ in tiles) and all((d / "shots" / f"{x[5]}.jpg").is_file() for x in shot_rows):
        if old.get("source_ident") == idn:
            todo_t, todo_s, made = [], [], "up to date"
        elif old.get("source_version") and ver and project:
            spans = V.drawn_since(project, rel(project, film), old["source_version"])
            if spans:
                inside = lambda k: any(A <= k <= B for A, B in spans)   # noqa: E731
                todo_t = [x for x in tiles if inside(x[2])]
                todo_s = [x for x in shot_rows if inside(x[4])]
                made = "refreshed"
            else:
                why = "a step since its version was not a patch in place"
    if made == "full":
        for q in (d / "tiles").glob("*.jpg"):
            q.unlink()
        for q in (d / "shots").glob("*.jpg"):
            q.unlink()
    jobs = [(k, (W, H), d / "tiles" / f"{i + 1:05d}.jpg") for i, _, k in todo_t] + [(k, (SW, SH), d / "shots" / f"{fn}.jpg") for _, _, _, _, k, fn in todo_s]
    if jobs and frm != "page":
        fps_src = probe(src)["fps"] if frm == "proxy" else fps
        with cf.ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
            list(ex.map(lambda j: grab(src, fps_src, j[0], j[1], j[2]), jobs))
    elif jobs:   # the page, through bin/vh frames: every time at once, then each picture scaled
        with tempfile.TemporaryDirectory(prefix="vh-thumbs-") as tmp:
            at = sorted({round(k / fps, 3) for k, _, _ in jobs})
            r = run(["node", str(HERE / "film" / "frames.mjs"), str(page), "--browser", a["browser"], "--at", ",".join(f"{t:.3f}" for t in at), "--out", tmp])
            if r.returncode:
                raise RuntimeError(f"drawing the page failed: {(r.stderr or r.stdout or '').strip()[-400:]}")
            stem = Path(page).stem
            with cf.ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as ex:
                list(ex.map(lambda j: from_png(Path(tmp) / f"{stem}-t{round(j[0] / fps, 3):08.3f}.png", j[1], j[2]), jobs))
    changed_sheets = {i // 100 for i, _, _ in todo_t}
    sh = sheets(d, len(tiles)) if made == "full" or changed_sheets or not all((d / f"sheet-{j + 1:02d}.jpg").is_file() for j in range(math.ceil(len(tiles) / 100))) \
        else [(d / f"sheet-{j + 1:02d}.jpg", min(100, len(tiles) - j * 100)) for j in range(math.ceil(len(tiles) / 100))]
    for q in d.glob("sheet-*.jpg"):   # sheets of an earlier, longer film
        if int(q.stem[6:] or 0) > len(sh):
            q.unlink()
    rec = {"version": 1, "tool": "bin/vh thumbs", "source": rel(project, base), "from": frm, "source_ident": idn, "source_version": ver,
           "fps": fps, "duration": round(dur, 6), "frames": nfr, "settings": settings, "tile": [W, H], "shot": [SW, SH],
           "sheets": [{"file": rel(project, f), "tiles": k, "size": [min(10, k) * W, math.ceil(k / 10) * H]} for f, k in sh],
           "tiles": [{"i": i, "t": t, "frame": k, "sheet": i // 100, "x": (i % 100) % 10 * W, "y": (i % 100) // 10 * H} for i, t, k in tiles],
           "shots": [{"id": sid, "t": t, "frame": k, "start": round(s, 6), "end": round(e, 6), "file": rel(project, d / "shots" / f"{fn}.jpg")}
                     for sid, s, e, t, k, fn in shot_rows],
           "shots_from": shots_from, "made": made, "taken": {"tiles": len(todo_t), "shots": len(todo_s)},
           "t": round(time.time(), 3), "at": V.iso(time.time()), "seconds": round(time.time() - T0, 2)}
    if made != "up to date":
        save(recf, rec)
    else:
        rec = old
    if a["json"]:
        print(json.dumps(dict(rec, state=made), ensure_ascii=False, indent=1))
    else:
        print(f"thumbs: {rel(project, d)} · {len(tiles)} tiles every {every} s ({W}x{H}) in {len(sh)} sheet(s), {len(shot_rows)} shot picture(s)"
              + (f" ({shots_from})" if shots_from else " (no shots: shots.json, or a page that gives window.film.shots)")
              + f" · from the {frm} · " + {"full": "made" + (f" anew ({why})" if why else ""), "up to date": "up to date",
                                           "refreshed": f"refreshed: {len(todo_t)} tile(s) and {len(todo_s)} shot picture(s) taken anew"}[made]
              + (f" · {rec['seconds']} s" if made != "up to date" else ""))
    if made != "up to date":
        note(f"{rel(project, base)} → {rel(project, d)}: {made} ({len(todo_t)} tiles, {len(todo_s)} shots)", [recf])
    return 0


def parse(argv, cmd):
    a = {"target": None, "full": False, "json": False, "out": None, "browser": None, "size": 360, "gop": None, "crf": 28,
         "every": 2.0, "width": 160, "shot_width": 320}
    nums = {"proxy": {"--size": ("size", int, 16), "--gop": ("gop", int, 1), "--crf": ("crf", int, 0)},
            "thumbs": {"--every": ("every", float, 0.1), "--width": ("width", int, 16), "--shot-width": ("shot_width", int, 16)}}[cmd]
    i = 0
    while i < len(argv):
        x = argv[i]
        k, _, v = x.partition("=") if x.startswith("--") and "=" in x else (x, None, None)
        if k in nums or k in ("--out", "--browser"):
            if v is None:
                if i + 1 >= len(argv):
                    raise Usage(f"{k} needs a value")
                v = argv[i + 1]; i += 1
            if k in nums:
                key, typ, lo = nums[k]
                try:
                    val = typ(v)
                except ValueError:
                    raise Usage(f"{k} {v}: a number")
                if not (val >= lo) or (typ is float and not math.isfinite(val)):
                    raise Usage(f"{k} {v}: at least {lo}")
                a[key] = val
            else:
                a[k[2:]] = v
        elif x == "--full":
            a["full"] = True
        elif x == "--json":
            a["json"] = True
        elif x.startswith("-"):
            raise Usage(f"unknown option {x}")
        elif a["target"] is None:
            a["target"] = x
        else:
            raise Usage(f"one film or project, got {a['target']} and {x}")
        i += 1
    if not a["target"]:
        raise Usage(f"which film or project? (bin/vh {cmd} -h)")
    if a["crf"] > 51:
        raise Usage("--crf: 0 to 51")
    return a


def main(argv):
    if not argv or argv[0] not in ("proxy", "thumbs"):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    cmd = argv[0]
    if "-h" in argv[1:] or "--help" in argv[1:]:
        print(__doc__.strip())
        return 0
    try:
        a = parse(argv[1:], cmd)
        for tool in ("ffmpeg", "ffprobe"):
            if not shutil.which(tool):
                raise RuntimeError(f"{tool} is not installed")
        return (cmd_proxy if cmd == "proxy" else cmd_thumbs)(a)
    except Usage as e:
        print(f"{cmd}: {e}", file=sys.stderr)
        return 2
    except (RuntimeError, OSError, SystemExit) as e:
        print(f"{cmd}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
