"""The style library (styles/): its families and tags, the list, the README's tables, the check, the swatch spec and
the swatch videos kept out of git. Stdlib only; ffmpeg/ffprobe for the media checks.

usage: python3 tools/styles.py list [--family F] [--type NN] [--pace P] [--aspect A] [--cost C] [--source S] [--json]
       python3 tools/styles.py readme [--check]        write styles/README.md's generated tables (--check: only compare)
       python3 tools/styles.py check [slug…] [--meta] [--text] [--json]
       python3 tools/styles.py spec <style folder> [--aspect landscape|portrait] [--shell]
       python3 tools/styles.py page <staged index.html> <slug> '<spec json>'   (render.sh: the stage's page)
       python3 tools/styles.py register <slug>… [--dry-run]

One truth: styles/families.json defines the families (id, names, one line, order) and the tag words; each style's own
styles/<slug>/tokens.json says which family it is in ("family"), what it suits ("video_types": the numbers of
video-types/NN-*.md), its tags ("tags": pace, aspect, cost, source), its swatch ("swatch": spec, duration …) and the
words of its README rows ("card"). Everything else is made from these two: styles/README.md's tables (readme), `bin/vh
style list` (list), and what `bin/vh style check` holds a style to (check). Adding a style is a folder and a rerun.

check: with no slug, every style. Each style's metadata (the fields above, against families.json and video-types/;
STYLE.md's title; the swatch's source) and, unless --meta, its media against the swatch spec of its tokens' "swatch":
duration, frame size, H.264, the loudness (-14 LUFS ± 1, true peak ≤ -1 dBTP), the size budget, the poster, the
2 s preview, the portrait version where the style suits portrait, the loop seam of spec 2. A style named on the command
line must have its media (rendered, or fetched with tools/fetch_media.sh styles); with no slug, a style whose video is
in the release but not here is said and skipped. --text also stages each swatch and runs `bin/vh textcheck` on it:
every text drawn stays inside the action-safe frame (5 % in from each edge), is not covered and has 3:1; and, when the
scene exports TEXTS, `bin/vh readcheck` on them. Exit 0 all good, 1 a problem (each said), 2 usage.

spec: the swatch spec a style folder's tokens.json asks for, the numbers render.sh renders it to (--shell: as shell
assignments for render.sh). Spec 1 is the original 5 s swatch every style had until 2026-11 (the same title and motif
in all of them); spec 2 is 5–10 s (default 8) in four beats, with sound at one loudness, a 2 s preview and a portrait
version for a style that suits portrait (styles/_swatch/README.md, "样片规格").

register: the spec-2 videos of a style (media/swatch.mp4, swatch-portrait.mp4) go into tools/media.txt as assets of the
release "styles-media" named <slug>[-portrait]-<sha256[:8]>.mp4 (a new render gets a new name, so a release copy main
still points at is never overwritten), and the commands that upload them are printed. Nothing is uploaded here.
"""
import argparse, json, math, os, re, shutil, subprocess, sys, tempfile, unicodedata
from pathlib import Path

ROOT = Path(os.environ.get("OVH_STYLES_ROOT") or Path(__file__).resolve().parent.parent)   # another root: tools/ci.sh's fixtures
STYLES = ROOT / "styles"
FAMILIES = STYLES / "families.json"
README = STYLES / "README.md"
MEDIA_TXT = ROOT / "tools" / "media.txt"
RELEASE = "styles-media"
REPO_URL = "https://github.com/ZLHad/OpenVideoHarness"

# ── the swatch spec ───────────────────────────────────────────────────────────────────────────────────────────────
FPS = 30
RENDER = {"landscape": (1920, 1080), "portrait": (1080, 1920)}
DELIVER = {"landscape": (1280, 720), "portrait": (720, 1280)}
PREVIEW = {"size": (854, 480), "seconds": 2.0, "bytes": 200_000}
LOUDNESS, LOUDNESS_TOL, TRUE_PEAK = -14.0, 1.0, -1.0   # the mix's profile=swatch target; every swatch so far is within 0.4 LU
MP4_PER_10S = 3_000_000                                # bytes for 10 s; a 5 s swatch gets 1.5 MB, an 8 s one 2.4 MB
SPECS = {
    1: {"min": 5.0, "max": 5.0, "default": 5.0, "poster_bytes": 200_000, "audio": False, "preview": False, "portrait": False},
    2: {"min": 5.0, "max": 10.0, "default": 8.0, "poster_bytes": 150_000, "audio": True, "preview": True, "portrait": True},
}
POSTER_T = 3.0
BEAT_FRACTIONS = (1.5 / 8, 4.5 / 8, 7 / 8)             # world | signature move | type | close, as parts of 8 s: the type
                                                       # beat's 2.5 s is what a title and a short caption need to be read once
BEAT_NAMES = ("world", "signature", "type", "close")
V1_SAMPLES = (12, 51, 90, 138)                         # render.sh's four check frames for the 5 s spec (t = 0.4/1.7/3.0/4.6)
V1_WARM = (0, 0.9, 1.8, 2.7, 3.0, 3.6, 4.5)
SEAM_LIMIT = 12.0                                      # spec 2: mean |last − first| of the luma at 160×90, out of 255


def spec_of(tokens, aspect="landscape"):
    """The swatch a tokens.json asks for: {spec, duration, frames, w, h, out_w, out_h, poster, beats, …}. Raises
    ValueError with the reason when its "swatch" block is not one the renderer can make."""
    sw = tokens.get("swatch") if isinstance(tokens.get("swatch"), dict) else {}
    ver = sw.get("spec", 1)
    if ver not in SPECS:
        raise ValueError(f'"swatch": spec {ver!r} is not one of {sorted(SPECS)}')
    S = SPECS[ver]
    dur = sw.get("duration", S["default"])
    if not isinstance(dur, (int, float)) or isinstance(dur, bool) or not S["min"] <= dur <= S["max"] or round(dur * FPS) != dur * FPS:
        raise ValueError(f'"swatch": duration {dur!r} — spec {ver} takes {S["min"]:g}–{S["max"]:g} s in whole frames at {FPS} fps')
    dur = float(dur)
    if aspect not in RENDER:
        raise ValueError(f"aspect {aspect!r}: landscape or portrait")
    aspects = ["landscape"] + (["portrait"] if S["portrait"] and (tokens.get("tags") or {}).get("aspect") in ("portrait", "both") else [])
    if aspect not in aspects:
        raise ValueError(f"this swatch has no {aspect} version (spec {ver}, tags.aspect {(tokens.get('tags') or {}).get('aspect')!r})")
    poster = sw.get("poster", POSTER_T)
    if not isinstance(poster, (int, float)) or not 0 <= poster < dur:
        raise ValueError(f'"swatch": poster {poster!r} must be a time inside the swatch (0–{dur:g} s)')
    frames = int(round(dur * FPS))
    if ver == 1:
        beats = None
        samples = list(V1_SAMPLES)
        warm = list(V1_WARM)
    else:
        cuts = sw.get("beats", [round(dur * f, 3) for f in BEAT_FRACTIONS])
        if (not isinstance(cuts, list) or len(cuts) != 3 or not all(isinstance(c, (int, float)) for c in cuts)
                or not 0 < cuts[0] < cuts[1] < cuts[2] < dur):
            raise ValueError(f'"swatch": beats {cuts!r} must be three times 0 < world end < signature end < type end < {dur:g}')
        edges = [0.0, *map(float, cuts), dur]
        beats = {n: [edges[i], edges[i + 1]] for i, n in enumerate(BEAT_NAMES)}
        samples = [min(frames - 1, int(round((a + b) / 2 * FPS))) for a, b in beats.values()]
        warm = sorted({round(dur * f / 8, 4) for f in range(8)} | {float(poster)})
    preview = None
    if S["preview"] and aspect == "landscape":
        start = sw.get("preview", max(0.0, min(dur - PREVIEW["seconds"], poster - PREVIEW["seconds"] / 2)))
        if not isinstance(start, (int, float)) or not 0 <= start <= dur - PREVIEW["seconds"]:
            raise ValueError(f'"swatch": preview {start!r} must start between 0 and {dur - PREVIEW["seconds"]:g} s')
        preview = float(start)
    w, h = RENDER[aspect]
    ow, oh = DELIVER[aspect]
    return {"spec": ver, "aspect": aspect, "aspects": aspects, "duration": dur, "fps": FPS, "frames": frames,
            "w": w, "h": h, "out_w": ow, "out_h": oh, "poster": float(poster), "poster_frame": int(round(poster * FPS)),
            "mp4_bytes": int(MP4_PER_10S * dur / 10), "poster_bytes": S["poster_bytes"], "audio": S["audio"],
            "preview": preview, "beats": beats, "samples": samples, "warm": warm}


def spec_shell(sp):
    """render.sh's variables (eval'd there): plain words and numbers only."""
    beats = json.dumps(sp["beats"], separators=(",", ":")) if sp["beats"] else "null"
    page = {"w": sp["w"], "h": sp["h"], "dur": sp["duration"], "fps": sp["fps"], "poster": sp["poster"], "spec": sp["spec"],
            "aspect": sp["aspect"], "beats": sp["beats"], "warm": sp["warm"]}
    lines = {
        "SPEC": sp["spec"], "ASPECTS": " ".join(sp["aspects"]), "FPS": sp["fps"], "DUR": f'{sp["duration"]:g}',
        "FRAMES": sp["frames"], "W": sp["w"], "H": sp["h"], "OUT_W": sp["out_w"], "OUT_H": sp["out_h"],
        "POSTER_FRAME": sp["poster_frame"], "MP4_LIMIT": sp["mp4_bytes"], "JPG_LIMIT": sp["poster_bytes"],
        "PREVIEW_T": "" if sp["preview"] is None else f'{sp["preview"]:g}', "PREVIEW_W": PREVIEW["size"][0],
        "PREVIEW_H": PREVIEW["size"][1], "PREVIEW_LIMIT": PREVIEW["bytes"], "SAMPLES": " ".join(map(str, sp["samples"])),
        "PAGE_SPEC": json.dumps(page, separators=(",", ":")), "BEATS": beats,
    }
    return "\n".join(f"{k}='{v}'" for k, v in lines.items())


def stage_page(text, slug, page):
    """styles/_swatch/index.html as render.sh stages it: the `style` variable's default set to the slug (hyperframes
    snapshot and preview take no --variables), the frame size and length set to the spec's (the shell is written for
    1920×1080 and 5 s, so a spec-1 landscape page keeps every byte but one added line), and the spec itself as
    window.__swatchSpec, which lib.js reads (a classic script, so it runs before any module)."""
    import html as H
    m = re.search(r"data-composition-variables='([^']*)'", text)
    v = json.loads(H.unescape(m.group(1)))
    for d in v:
        if d["id"] == "style":
            d["default"] = slug
    text = text[:m.start(1)] + json.dumps(v, ensure_ascii=False, separators=(",", ":")) + text[m.end(1):]
    size = {"1920": str(page["w"]), "1080": str(page["h"])}
    text = re.sub(r"(?<!\d)(1920|1080)(?!\d)", lambda m: size[m.group(1)], text)   # 1920px too, where \b would not cut
    text = text.replace('data-duration="5"', f'data-duration="{page["dur"]:g}"', 1)
    return text.replace("<script>", "<script>window.__swatchSpec = " + json.dumps(page, separators=(",", ":")) + ";</script>\n    <script>", 1)


def cmd_page(a):
    p = Path(a.page)
    p.write_text(stage_page(p.read_text(encoding="utf-8"), a.slug, json.loads(a.spec)), encoding="utf-8")
    return 0


# ── the library ─────────────────────────────────────────────────────────────────────────────────────────────────
def families():
    """(families in order, tag vocabulary) from styles/families.json; ValueError when it is malformed."""
    try:
        d = json.loads(FAMILIES.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"styles/families.json: {e}")
    fams, tags = d.get("families"), d.get("tags")
    bad = []
    if not isinstance(fams, list) or not fams:
        bad.append("no families list")
        fams = []
    seen = set()
    for i, f in enumerate(fams):
        if not isinstance(f, dict):
            bad.append(f"families[{i}] is not an object")
            continue
        for k in ("id", "zh", "en", "line_zh", "line_en"):
            if not isinstance(f.get(k), str) or not f[k].strip():
                bad.append(f"families[{i}] has no {k}")
        fid = f.get("id", "")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", str(fid)):
            bad.append(f"families[{i}]: id {fid!r} is not a lower-case slug")
        if fid in seen:
            bad.append(f"families: {fid} twice")
        seen.add(fid)
    if not isinstance(tags, dict) or not tags:
        bad.append("no tags")
        tags = {}
    for dim, t in tags.items():
        vals = t.get("values") if isinstance(t, dict) else None
        if not isinstance(vals, dict) or not vals or not all(isinstance(v, dict) and v.get("zh") and v.get("en") for v in vals.values()):
            bad.append(f"tags.{dim}: needs zh, en and values {{word: {{zh, en, line}}}}")
    if bad:
        raise ValueError("styles/families.json: " + "; ".join(bad))
    return fams, tags


def video_types():
    """{"01": "math-science-explainer", …} from video-types/NN-*.md."""
    return {p.name[:2]: p.stem[3:] for p in sorted((ROOT / "video-types").glob("[0-9][0-9]-*.md"))}


def style_dirs():
    return sorted(p for p in STYLES.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")) and
                  ((p / "STYLE.md").exists() or (p / "tokens.json").exists()))


def load(d):
    """{slug, dir, tokens or None, error or None} for one style folder."""
    try:
        return {"slug": d.name, "dir": d, "tokens": json.loads((d / "tokens.json").read_text(encoding="utf-8")), "error": None}
    except (OSError, ValueError) as e:
        return {"slug": d.name, "dir": d, "tokens": None, "error": f"tokens.json: {e}"}


def engine_of(st):
    if (st["dir"] / "swatch.py").exists() and not (st["dir"] / "swatch.js").exists():
        return "blender"
    return (st["tokens"] or {}).get("engine") or "canvas"


def registered():
    """{path in the repo: (asset, sha256)} from tools/media.txt."""
    out = {}
    for line in MEDIA_TXT.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            parts = line.split()
            if len(parts) == 3:
                out[parts[0]] = (parts[1], parts[2])
    return out


def media_state(st, reg=None):
    """'here' (the landscape swatch is on disk), 'release' (registered, not fetched), or '—'."""
    rel = f"styles/{st['slug']}/media/swatch.mp4"
    if (ROOT / rel).is_file():
        return "here"
    return "release" if rel in (reg if reg is not None else registered()) else "—"


def meta_problems(st, fams, tags, types):
    """What is wrong with one style's metadata (empty: nothing)."""
    s, d, t = st["slug"], st["dir"], st["tokens"]
    if t is None:
        return [st["error"]]
    bad = []
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", s):
        bad.append("the folder name is not a lower-case slug")
    if t.get("slug") != s:
        bad.append(f'tokens.json: slug {t.get("slug")!r}, but the folder is {s}')
    nm = t.get("name")
    if not isinstance(nm, dict) or not all(isinstance(nm.get(k), str) and nm[k].strip() for k in ("zh", "en")):
        bad.append('tokens.json: name needs {"zh", "en"}')
    ids = [f["id"] for f in fams]
    if t.get("family") not in ids:
        bad.append(f'tokens.json: family {t.get("family")!r} is no family in styles/families.json ({", ".join(ids)})')
    vt = t.get("video_types")
    if not isinstance(vt, list) or not vt:
        bad.append("tokens.json: video_types needs one or more video type numbers (video-types/NN-*.md)")
    else:
        unknown = [v for v in vt if v not in types]
        if unknown:
            bad.append(f"tokens.json: video_types {unknown} — the types are {', '.join(types)}")
        if len(set(map(str, vt))) != len(vt):
            bad.append("tokens.json: video_types lists a type twice")
    tg = t.get("tags")
    if not isinstance(tg, dict):
        bad.append(f'tokens.json: tags needs {{{", ".join(f"{k!r}: …" for k in tags)}}}')
    else:
        for dim, voc in tags.items():
            if tg.get(dim) not in voc["values"]:
                bad.append(f'tokens.json: tags.{dim} {tg.get(dim)!r} — one of {", ".join(voc["values"])} ({voc["zh"]})')
        for extra in sorted(set(tg) - set(tags)):
            bad.append(f"tokens.json: tags.{extra} is no tag in styles/families.json ({', '.join(tags)})")
        if tg.get("cost") == "blender" and engine_of(st) != "blender":
            bad.append("tokens.json: tags.cost is blender, but the swatch is not a Blender scene (swatch.py)")
    study = t.get("study")
    if not isinstance(study, list) or not study or not all(isinstance(x, dict) and x.get("work") for x in study):
        bad.append("tokens.json: study needs the works it learns from ([{work, year, by}])")
    card = t.get("card")
    need = ("learned_from", "line", "fit", "score", "instruments", "sounds_like")
    if not isinstance(card, dict) or [k for k in need if not isinstance(card.get(k), str) or not card[k].strip()]:
        bad.append(f"tokens.json: card needs {', '.join(need)} (the words of its rows in styles/README.md)")
    elif any("|" in card[k] or "\n" in card[k] for k in need):
        bad.append("tokens.json: card text may not hold | or a line break (they are table cells)")
    try:
        sp = spec_of(t)
    except ValueError as e:
        bad.append(f"tokens.json: {e}")
        sp = None
    md = d / "STYLE.md"
    if not md.is_file():
        bad.append("no STYLE.md")
    elif isinstance(nm, dict):
        head = md.read_text(encoding="utf-8").splitlines()[0] if md.read_text(encoding="utf-8") else ""
        if head.strip() != f"# {nm.get('zh')} · {s}":
            bad.append(f"STYLE.md's title is {head.strip()!r}, not '# {nm.get('zh')} · {s}' (tokens.json name.zh · slug)")
    if not (d / "swatch.js").exists() and not (d / "swatch.py").exists():
        bad.append("no swatch.js (or swatch.py for a Blender scene)")
    if sp and sp["audio"] and not (d / "score.json").exists():
        bad.append(f"spec {sp['spec']} swatches have sound: no score.json")
    return bad


# ── media ──────────────────────────────────────────────────────────────────────────────────────────────────────
def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,pix_fmt",
                        "-of", "json", str(path)], capture_output=True, text=True)
    if r.returncode:
        raise ValueError(r.stderr.strip() or "ffprobe failed")
    return json.loads(r.stdout)


def loudness(path):
    """(integrated LUFS, true peak dBTP) by ffmpeg's ebur128 (BS.1770)."""
    r = subprocess.run(["ffmpeg", "-nostats", "-hide_banner", "-i", str(path), "-map", "0:a:0", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], capture_output=True, text=True)
    tail = r.stderr[r.stderr.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+|-inf) LUFS", tail)
    p = re.search(r"Peak:\s+(-?[\d.]+|-inf) dBFS", tail)
    if not i:
        raise ValueError("ffmpeg ebur128 gave no loudness")
    f = lambda m: -math.inf if m is None or m.group(1) == "-inf" else float(m.group(1))
    return f(i), f(p)


def gray(path, t, w=160, h=90):
    """The frame at t as w×h luma bytes."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", str(path), "-frames:v", "1", "-vf",
                        f"scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"], capture_output=True)
    if r.returncode or len(r.stdout) != w * h:
        raise ValueError(f"could not read the frame at {t:.2f} s")
    return r.stdout


def seam(path, dur):
    """Mean |last frame − first frame| of the luma (0–255): how far the end is from looping back."""
    v = next(s for s in probe(path)["streams"] if s.get("codec_type") == "video")
    w, h = (90, 160) if v.get("height", 0) > v.get("width", 0) else (160, 90)
    a, b = gray(path, 0.0, w, h), gray(path, max(0.0, dur - 1.5 / FPS), w, h)
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


def video_problems(path, sp, label, want_audio):
    bad, info = [], {}
    try:
        p = probe(path)
    except ValueError as e:
        return [f"{label}: {e}"], info
    v = [s for s in p["streams"] if s.get("codec_type") == "video"]
    a = [s for s in p["streams"] if s.get("codec_type") == "audio"]
    dur = float(p.get("format", {}).get("duration") or 0)
    info.update(duration=round(dur, 3), bytes=path.stat().st_size)
    if not v:
        return [f"{label}: no video stream"], info
    v = v[0]
    if (v.get("width"), v.get("height")) != (sp["out_w"], sp["out_h"]):
        bad.append(f"{label}: {v.get('width')}×{v.get('height')}, the spec delivers {sp['out_w']}×{sp['out_h']}")
    if v.get("codec_name") != "h264" or v.get("pix_fmt") != "yuv420p":
        bad.append(f"{label}: {v.get('codec_name')} {v.get('pix_fmt')}, the spec delivers H.264 yuv420p")
    if abs(dur - sp["duration"]) > 0.06:
        bad.append(f"{label}: {dur:.2f} s long, its tokens.json asks for {sp['duration']:g} s")
    if info["bytes"] > sp["mp4_bytes"]:
        bad.append(f"{label}: {info['bytes'] / 1e6:.2f} MB, over the {sp['mp4_bytes'] / 1e6:.2f} MB budget "
                   f"({MP4_PER_10S / 1e6:g} MB per 10 s)")
    if a:
        try:
            lu, tp = loudness(path)
            info.update(lufs=lu, true_peak=tp)
            if abs(lu - LOUDNESS) > LOUDNESS_TOL:
                bad.append(f"{label}: {lu:.1f} LUFS, the swatches sit at {LOUDNESS:g} ± {LOUDNESS_TOL:g} (render.sh mixes them there)")
            if tp > TRUE_PEAK:
                bad.append(f"{label}: true peak {tp:.1f} dBTP, over {TRUE_PEAK:g}")
        except ValueError as e:
            bad.append(f"{label}: {e}")
    elif want_audio:
        bad.append(f"{label}: silent, and spec {sp['spec']} swatches have sound (score.json, mixed by render.sh)")
    return bad, info


def media_problems(st, need):
    """(problems, notes, numbers) for a style's swatch media; `need`: a missing video is a problem, not a note."""
    s, d, t = st["slug"], st["dir"], st["tokens"]
    bad, notes, nums = [], [], {}
    try:
        sp = spec_of(t)
    except ValueError:
        return bad, notes, nums          # meta_problems says why
    media, reg = d / "media", registered()
    poster = media / "poster.jpg"
    if not poster.is_file():
        bad.append("no media/poster.jpg (it stays in git: render the swatch)")
    else:
        nums["poster_bytes"] = poster.stat().st_size
        try:
            ps = probe(poster)["streams"][0]
            if (ps.get("width"), ps.get("height")) != DELIVER["landscape"]:
                bad.append(f"media/poster.jpg is {ps.get('width')}×{ps.get('height')}, not {DELIVER['landscape'][0]}×{DELIVER['landscape'][1]}")
        except (ValueError, IndexError) as e:
            bad.append(f"media/poster.jpg: {e}")
        if nums["poster_bytes"] > sp["poster_bytes"]:
            bad.append(f"media/poster.jpg is {nums['poster_bytes'] // 1000} KB, over {sp['poster_bytes'] // 1000} KB")
    tracked = set(subprocess.run(["git", "ls-files", f"styles/{s}/media"], cwd=ROOT, capture_output=True, text=True).stdout.split())
    for aspect in sp["aspects"]:
        a = spec_of(t, aspect)
        name = "swatch.mp4" if aspect == "landscape" else "swatch-portrait.mp4"
        rel, f = f"styles/{s}/media/{name}", media / name
        if sp["spec"] >= 2 and rel in tracked:
            bad.append(f"{rel} is in git: spec-2 swatches live in the release (git rm --cached {rel}; bin/vh style register {s})")
        if sp["spec"] >= 2 and f.is_file() and rel not in reg:
            bad.append(f"{rel} is not in tools/media.txt: bin/vh style register {s}")
        if not f.is_file():
            if rel in reg:
                (bad if need else notes).append(f"{rel} is in the release, not here: tools/fetch_media.sh {s}")
            else:
                bad.append(f"no {rel}: render it (bin/vh style {s})")
            continue
        if rel in reg and _sha(f) != reg[rel][1]:
            notes.append(f"{rel} differs from the release copy tools/media.txt names (a new render: bin/vh style register {s})")
        vb, vi = video_problems(f, a, f"media/{name}", sp["audio"])
        bad += vb
        nums[aspect] = vi
        if sp["spec"] >= 2 and vi.get("duration"):
            try:
                sm = seam(f, a["duration"])
                nums[aspect]["seam"] = round(sm, 1)
                if sm > SEAM_LIMIT:
                    bad.append(f"media/{name}: the last frame is {sm:.1f}/255 from the first (over {SEAM_LIMIT:g}): the close "
                               f"beat should land back on the opening picture, so the swatch loops")
            except ValueError as e:
                bad.append(f"media/{name}: {e}")
        if aspect == "portrait":
            pp = media / "poster-portrait.jpg"
            if not pp.is_file():
                bad.append("no media/poster-portrait.jpg")
            elif pp.stat().st_size > sp["poster_bytes"]:
                bad.append(f"media/poster-portrait.jpg is {pp.stat().st_size // 1000} KB, over {sp['poster_bytes'] // 1000} KB")
    pv = media / "preview.mp4"
    if sp["preview"] is not None or pv.is_file():
        if not pv.is_file():
            bad.append("no media/preview.mp4 (the 2 s, 480p loop for the gallery; render.sh writes it)")
        else:
            try:
                p = probe(pv)
                v = next(x for x in p["streams"] if x.get("codec_type") == "video")
                dur = float(p["format"]["duration"])
                nums["preview"] = {"bytes": pv.stat().st_size, "duration": round(dur, 3)}
                if (v.get("width"), v.get("height")) != PREVIEW["size"]:
                    bad.append(f"media/preview.mp4 is {v.get('width')}×{v.get('height')}, not {PREVIEW['size'][0]}×{PREVIEW['size'][1]}")
                if abs(dur - PREVIEW["seconds"]) > 0.06:
                    bad.append(f"media/preview.mp4 is {dur:.2f} s, not {PREVIEW['seconds']:g}")
                if pv.stat().st_size > PREVIEW["bytes"]:
                    bad.append(f"media/preview.mp4 is {pv.stat().st_size // 1000} KB, over {PREVIEW['bytes'] // 1000} KB")
            except (ValueError, StopIteration, KeyError) as e:
                bad.append(f"media/preview.mp4: {e}")
    return bad, notes, nums


def _sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ── text inside the safe frame ────────────────────────────────────────────────────────────────────────────────────
def text_problems(st, sp, keep=None):
    """Stage the swatch, run bin/vh textcheck on it, hold every text box to the action-safe frame; readcheck the
    scene's TEXTS when it exports them. (problems, notes)."""
    s = st["slug"]
    bad, notes = [], []
    vh = [os.environ.get("VH_BASH", "bash"), str(ROOT / "bin/vh")]
    if engine_of(st) == "blender":
        return blender_text_problems(st, vh, keep)
    for aspect in sp["aspects"]:
        a = spec_of(st["tokens"], aspect)
        r = subprocess.run([str(STYLES / "_swatch/render.sh"), s, "--stage-only", "--aspect", aspect], capture_output=True, text=True)
        if r.returncode:
            return [f"could not stage the swatch ({aspect}): {(r.stderr or r.stdout).strip().splitlines()[-1:]}"], notes
        key = s if aspect == "landscape" else f"{s}-portrait"
        page = STYLES / "_swatch/out/stage" / key / "index.html"
        out = Path(keep or tempfile.mkdtemp(prefix="vh-styletext.")) / key
        r = subprocess.run(vh + ["textcheck", str(page), "--out", str(out)], capture_output=True, text=True)
        rep = out / "textcheck.json"
        if not rep.is_file():
            bad.append(f"textcheck could not check the {aspect} swatch: {(r.stderr or r.stdout).strip().splitlines()[-1:] or r.returncode}")
            continue
        j = json.loads(rep.read_text(encoding="utf-8"))
        W, H = j.get("size") or (a["w"], a["h"])
        x0, y0, x1, y1 = W / 20, H / 20, W - W / 20, H - H / 20
        outside = {}
        for item in (j.get("reads") or []) + (j.get("extra") or []):
            for smp in (item.get("samples") or []) + ([item["sample"]] if item.get("sample") else []):
                b = smp.get("box")
                if b and (b[0] < x0 - 0.5 or b[1] < y0 - 0.5 or b[2] > x1 + 0.5 or b[3] > y1 + 0.5):
                    outside.setdefault(item.get("text", "?"), (smp.get("t"), [round(v) for v in b]))
        for text, (t, b) in outside.items():
            bad.append(f"{aspect}: \"{text[:40]}\" at {t:.2f} s is outside the action-safe frame ({b}; the frame is "
                       f"{round(x0)}–{round(x1)} × {round(y0)}–{round(y1)})")
        if r.returncode == 1:
            bad.append(f"{aspect}: bin/vh textcheck failed a read (covered, under 3:1, or cut by the frame): see {out}/textcheck.json")
        elif r.returncode:
            bad.append(f"{aspect}: bin/vh textcheck could not check: {(r.stderr or r.stdout).strip().splitlines()[-1:]}")
        texts = [{"text": x["text"], "start": x["start"], "end": x["end"], **({"read": x["read"]} if x.get("read") else {})}
                 for x in (j.get("reads") or []) if isinstance(x, dict) and {"text", "start", "end"} <= set(x)]
        if texts:
            tf = out / "texts.json"
            tf.write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
            rr = subprocess.run(vh + ["readcheck", str(tf), "--pace", "brisk"], capture_output=True, text=True)
            if rr.returncode == 1:
                bad.append(f"{aspect}: a text is not on screen long enough to read once (bin/vh readcheck {tf})")
        elif aspect == "landscape" and a["spec"] >= 2:
            notes.append("the scene exports no TEXTS, so readcheck had nothing to time (export them as the template does)")
    return bad, notes


def blender_text_problems(st, vh, keep=None):
    """A Blender scene's text is geometry in its frames, so textcheck (which reads canvas text calls) cannot see it: only
    the reads' timing is checked, from the scene's TEXTS (`python3 swatch.py --texts`, after blender_prep.py's scan),
    and the rest is said as a note. (problems, notes)"""
    py = st["dir"] / "swatch.py"
    r = subprocess.run([sys.executable, str(STYLES / "_swatch/blender_prep.py"), "scan", str(py)], capture_output=True, text=True)
    if r.returncode:
        return [f"blender_prep.py scan refuses swatch.py: {(r.stdout or r.stderr).strip().splitlines()[-1:]}"], []
    r = subprocess.run([sys.executable, "-I", str(py), "--texts"], capture_output=True, text=True,
                       env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1"})
    lines = [l for l in r.stdout.strip().splitlines() if l.strip()]
    try:
        texts = json.loads(lines[-1]) if lines else None
    except ValueError:
        texts = None
    notes = ["a Blender scene: its text is rendered geometry, so textcheck (safe frame, cover, 3:1) cannot see it; "
             "check the type on the frames"]
    if not isinstance(texts, list) or not texts:
        notes.append("swatch.py prints no TEXTS (`python3 swatch.py --texts`), so readcheck had nothing to time")
        return [], notes
    out = Path(keep or tempfile.mkdtemp(prefix="vh-styletext.")) / st["slug"]
    out.mkdir(parents=True, exist_ok=True)
    tf = out / "texts.json"
    tf.write_text(json.dumps(texts, ensure_ascii=False), encoding="utf-8")
    rr = subprocess.run(vh + ["readcheck", str(tf), "--pace", "brisk"], capture_output=True, text=True)
    bad = [f"a text is not on screen long enough to read once (bin/vh readcheck {tf})"] if rr.returncode == 1 else []
    return bad, notes


def pad(s, n):
    """s padded to n terminal columns (a CJK character takes two)."""
    w = sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)
    return s + " " * max(0, n - w)


# ── list ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def rows(filters=None):
    fams, tags = families()
    order = {f["id"]: i for i, f in enumerate(fams)}
    reg = registered()
    out = []
    for d in style_dirs():
        st = load(d)
        t = st["tokens"] or {}
        tg = t.get("tags") or {}
        sw = t.get("swatch") or {}
        r = {"slug": st["slug"], "family": t.get("family"), "zh": (t.get("name") or {}).get("zh", ""),
             "en": (t.get("name") or {}).get("en", ""), "video_types": t.get("video_types") or [], "tags": tg,
             "engine": engine_of(st), "swatch": {"spec": sw.get("spec", 1), "duration": sw.get("duration", 5),
                                                 "media": media_state(st, reg)}}
        if filters:
            f = filters
            if f.get("family") and r["family"] != f["family"]:
                continue
            if f.get("type") and f["type"] not in r["video_types"]:
                continue
            if any(f.get(k) and tg.get(k) != f[k] and not (k == "aspect" and tg.get(k) == "both" and f[k] != "both") for k in tags):
                continue
        out.append(r)
    out.sort(key=lambda r: (order.get(r["family"], len(order)), r["slug"]))
    return fams, tags, out


def cmd_list(a):
    fams, tags = families()
    flt = {"family": a.family, "type": a.type, **{k: getattr(a, k) for k in tags if getattr(a, k, None)}}
    for k, voc in tags.items():
        if flt.get(k) and flt[k] not in voc["values"]:
            return usage(f"--{k} {flt[k]}: one of {', '.join(voc['values'])}")
    if a.family and a.family not in {f["id"] for f in fams}:
        return usage(f"--family {a.family}: one of {', '.join(f['id'] for f in fams)}")
    if a.type and a.type not in video_types():
        return usage(f"--type {a.type}: one of {', '.join(video_types())}")
    fams, tags, rs = rows(flt)
    if a.json:
        print(json.dumps({"families": fams, "styles": rs}, ensure_ascii=False, indent=1))
        return 0
    word = lambda dim, v: tags[dim]["values"].get(v, {}).get("zh", v or "?")
    last = None
    for r in rs:
        if r["family"] != last:
            last = r["family"]
            f = next((x for x in fams if x["id"] == last), {"zh": "?", "en": last})
            n = sum(1 for x in rs if x["family"] == last)
            print(f"{f['zh']} · {last} ({n})")
        sw = r["swatch"]
        media = {"here": f"{sw['duration']:g}s swatch", "release": f"{sw['duration']:g}s in release", "—": "no swatch"}[sw["media"]]
        tg = " ".join(word(k, r["tags"].get(k)) for k in ("pace", "aspect", "cost"))
        print(f"  {r['slug']:22} {pad(r['zh'], 14)} {pad(tg, 16)} {' '.join(r['video_types']):14} {media}")
    if not rs:
        print("no style matches", file=sys.stderr)
        return 1
    if not any([a.family, a.type] + [getattr(a, k, None) for k in tags]):
        print(f"{len(rs)} styles in {len({r['family'] for r in rs})} families · tags: pace aspect cost · then video types "
              f"(video-types/NN) · filter: --family --type --pace --aspect --cost --source")
    return 0


# ── README ───────────────────────────────────────────────────────────────────────────────────────────────────────
BEGIN, END = "<!-- generated: styles by family", "<!-- end generated: styles by family -->"
SBEGIN, SEND = "<!-- generated: swatch sound", "<!-- end generated: swatch sound -->"


def readme_blocks():
    """(the family tables, the sound table) as styles/README.md holds them."""
    fams, tags, rs = rows()
    by = {s["slug"]: load(STYLES / s["slug"])["tokens"] or {} for s in rs}
    word = lambda dim, v: tags[dim]["values"].get(v, {}).get("zh", "?")
    a = [f"{BEGIN} — python3 tools/styles.py readme; edit styles/families.json and styles/<slug>/tokens.json, not these tables -->", ""]
    a.append("标签一栏：节奏 · 画幅 · 渲染成本 · 来源，第二行是它适合的视频类型（`video-types/` 的编号）。"
             "按家族、类型或标签筛：`bin/vh style list --family <id> --type <NN> --pace calm`。")
    for f in fams:
        mine = [r for r in rs if r["family"] == f["id"]]
        if not mine:
            continue
        a += ["", f"### {f['zh']}", "", f"`{f['id']}` · {f['line_zh']}", "",
              "| 风格 | 学习对象 | 一句话 | 适合 | 标签 |", "|---|---|---|---|---|"]
        for r in mine:
            c = by[r["slug"]].get("card") or {}
            tg = " · ".join(word(k, r["tags"].get(k)) for k in ("pace", "aspect", "cost", "source"))
            a.append(f"| [{r['zh']}]({r['slug']}/) `{r['slug']}` | {c.get('learned_from', '')} | {c.get('line', '')} | "
                     f"{c.get('fit', '')} | {tg}<br>{' '.join(r['video_types'])} |")
    a += ["", END]
    b = [f"{SBEGIN} — python3 tools/styles.py readme, from each tokens.json's card -->", "",
         "| 风格 | 配乐 | 签名乐器 | 听起来 |", "|---|---|---|---|"]
    for r in rs:
        c = by[r["slug"]].get("card") or {}
        b.append(f"| `{r['slug']}` | {c.get('score', '')} | {c.get('instruments', '')} | {c.get('sounds_like', '')} |")
    b += ["", SEND]
    return "\n".join(a), "\n".join(b)


def _splice(text, begin, end, new):
    i, j = text.find(begin), text.find(end)
    if i < 0 or j < i:
        raise ValueError(f"styles/README.md has no {begin} … {end} block")
    return text[:i] + new + text[j + len(end):]


def readme_problems():
    """What tools/readme.py check says about the styles README: its generated tables against the data."""
    try:
        text = README.read_text(encoding="utf-8")
        fam, snd = readme_blocks()
        want = _splice(_splice(text, BEGIN, END, fam), SBEGIN, SEND, snd)
    except ValueError as e:
        return [str(e)]
    if want == text:
        return []
    import difflib
    diff = [l for l in difflib.unified_diff(text.splitlines(), want.splitlines(), lineterm="", n=0) if l[:1] in "+-" and l[:3] not in ("+++", "---")]
    return ["styles/README.md: its style tables are not what styles/families.json and the tokens.json files say "
            "(python3 tools/styles.py readme rewrites them); first lines that differ: " + " | ".join(x[:110] for x in diff[:4])]


def cmd_readme(a):
    try:
        text = README.read_text(encoding="utf-8")
        fam, snd = readme_blocks()
        want = _splice(_splice(text, BEGIN, END, fam), SBEGIN, SEND, snd)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 1
    if a.check:
        bad = readme_problems()
        print("\n".join(bad) if bad else "styles/README.md's tables match the data")
        return 1 if bad else 0
    if want != text:
        README.write_text(want, encoding="utf-8")
        print("styles/README.md: tables rewritten from styles/families.json and the tokens.json files")
    else:
        print("styles/README.md: already up to date")
    return 0


def media_txt_problems():
    """tools/media.txt as tools/fetch_media.sh reads it: three fields a line, a sha256, a path git ignores and does not
    track, each path and asset once; a style swatch's line names a style, sits in the release styles-media and is
    called <slug>[-portrait]-<sha256[:8]>.mp4 (register writes it so)."""
    bad, paths, assets = [], set(), set()
    lines = [(i, l) for i, l in enumerate(MEDIA_TXT.read_text(encoding="utf-8").splitlines(), 1) if l.strip() and not l.startswith("#")]
    tracked = set(subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True).stdout.split("\0"))
    names = {d.name for d in style_dirs()}
    for i, l in lines:
        f = l.split()
        if len(f) != 3:
            bad.append(f"tools/media.txt line {i}: <path> <asset> <sha256>, not {len(f)} field(s)")
            continue
        path, asset, sha = f
        if not re.fullmatch(r"[0-9a-f]{64}", sha):
            bad.append(f"tools/media.txt line {i}: {sha[:20]}… is no sha256")
        if path.startswith("/") or ".." in path.split("/"):
            bad.append(f"tools/media.txt line {i}: {path} is not a path inside the repo")
        if not re.fullmatch(r"(?:[A-Za-z0-9._-]+/)?[A-Za-z0-9._-]+", asset):
            bad.append(f"tools/media.txt line {i}: asset {asset} is neither <name> nor <release>/<name>")
        if path in paths:
            bad.append(f"tools/media.txt line {i}: {path} twice")
        asset_key = asset if "/" in asset else f"media/{asset}"
        if asset_key in assets:
            bad.append(f"tools/media.txt line {i}: the asset {asset} twice")
        paths.add(path)
        assets.add(asset_key)
        if path in tracked:
            bad.append(f"tools/media.txt line {i}: {path} is in git as well (git rm --cached {path})")
        elif subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode != 0:
            bad.append(f"tools/media.txt line {i}: .gitignore does not cover {path}, so a fetched copy could be committed")
        m = re.fullmatch(r"styles/([^/]+)/media/swatch(-portrait)?\.mp4", path)
        if m:
            want = f"{RELEASE}/{m.group(1)}{m.group(2) or ''}-{sha[:8]}.mp4"
            if m.group(1) not in names:
                bad.append(f"tools/media.txt line {i}: {path} names no style in styles/")
            if asset != want:
                bad.append(f"tools/media.txt line {i}: a swatch's asset is {want} (bin/vh style register {m.group(1)}), not {asset}")
    return bad


def tracked_swatch_problems():
    """A full swatch video in git: only the spec-1 swatches still there from before 2026-11 may be."""
    bad = []
    for rel in subprocess.run(["git", "ls-files", "styles/*/media/*.mp4"], cwd=ROOT, capture_output=True, text=True).stdout.split():
        m = re.fullmatch(r"styles/([^/]+)/media/(swatch|swatch-portrait|preview)\.mp4", rel)
        if not m:
            bad.append(f"{rel}: a video in a style's media/ that is none of swatch.mp4, swatch-portrait.mp4, preview.mp4")
            continue
        if m.group(2) == "preview":
            continue
        t = load(STYLES / m.group(1))["tokens"] or {}
        if (t.get("swatch") or {}).get("spec", 1) != 1 or m.group(2) != "swatch":
            bad.append(f"{rel} is in git: a spec-2 swatch goes to the release (git rm --cached {rel}; bin/vh style register {m.group(1)})")
    return bad


# ── check ────────────────────────────────────────────────────────────────────────────────────────────────────────
def cmd_check(a):
    try:
        fams, tags = families()
    except ValueError as e:
        print(f"✗ {e}")
        return 1
    types = video_types()
    dirs = style_dirs()
    if a.slugs:
        names = {d.name for d in dirs}
        unknown = [s for s in a.slugs if s not in names]
        if unknown:
            return usage(f"no such style: {', '.join(unknown)} (bin/vh style list)")
        dirs = [d for d in dirs if d.name in a.slugs]
    media = not a.meta
    if media and not shutil.which("ffprobe"):
        if a.slugs:
            print("✗ the media checks need ffmpeg/ffprobe (or --meta for the metadata alone)")
            return 1
        media = False
        print("- media not checked: no ffmpeg/ffprobe here")
    report, fails = [], 0
    for d in dirs:
        st = load(d)
        bad = meta_problems(st, fams, tags, types)
        meta_ok = not bad
        notes, nums = [], {}
        if media and st["tokens"] is not None:
            mb, notes, nums = media_problems(st, need=bool(a.slugs))
            bad += mb
            if a.text and meta_ok:   # the page, not the videos: it runs whatever the media say
                try:
                    tb, tn = text_problems(st, spec_of(st["tokens"]))
                    bad += tb
                    notes += tn
                except ValueError:
                    pass
        fails += bool(bad)
        report.append({"slug": st["slug"], "problems": bad, "notes": notes, "media": nums})
        if not a.json:
            if bad:
                print(f"✗ {st['slug']}")
                for b in bad:
                    print(f"   {b}")
            for n in notes:
                print(f"   - {st['slug']}: {n}")
    if not a.slugs:   # the library as a whole: tools/media.txt and the videos in git
        lib_bad = media_txt_problems() + tracked_swatch_problems()
        fails += bool(lib_bad)
        report.append({"slug": "(library)", "problems": lib_bad, "notes": [], "media": {}})
        if lib_bad and not a.json:
            print("✗ the library")
            for b in lib_bad:
                print(f"   {b}")
    used = {(load(d)["tokens"] or {}).get("family") for d in style_dirs()}
    empty = [f["id"] for f in fams if f["id"] not in used]
    if a.json:
        print(json.dumps({"styles": report, "empty_families": empty}, ensure_ascii=False, indent=1))
    else:
        what = "metadata" + (", swatch media" if media else "") + (", text in the safe frame" if a.text and media else "")
        if fails:
            print(f"✗ {fails} of {len(dirs)} style{'s' if len(dirs) != 1 else ''}{' (or the library)' if not a.slugs else ''} with a problem ({what})")
        else:
            print(f"✓ {len(dirs)} style{'s' if len(dirs) != 1 else ''}: {what} as styles/families.json, video-types/ and the swatch spec say"
                  + ("; tools/media.txt and the videos in git" if not a.slugs else "")
                  + (f" · families with no style yet: {', '.join(empty)}" if empty and not a.slugs else ""))
    return 1 if fails else 0


# ── register: the swatch videos out of git ───────────────────────────────────────────────────────────────────────
def cmd_register(a):
    lines = MEDIA_TXT.read_text(encoding="utf-8").splitlines()
    names = {d.name for d in style_dirs()}
    todo, upload = [], []
    for s in a.slugs:
        if s not in names:
            return usage(f"no such style: {s}")
        t = load(STYLES / s)["tokens"]
        try:
            sp = spec_of(t)
        except (ValueError, AttributeError) as e:
            print(f"✗ {s}: {e}", file=sys.stderr)
            return 1
        if sp["spec"] < 2:
            print(f"✗ {s}: a spec-1 swatch stays in git until it is rendered again under spec 2", file=sys.stderr)
            return 1
        for aspect in sp["aspects"]:
            name = "swatch.mp4" if aspect == "landscape" else "swatch-portrait.mp4"
            rel, f = f"styles/{s}/media/{name}", STYLES / s / "media" / name
            if not f.is_file():
                print(f"✗ no {rel}: render it first (bin/vh style {s})", file=sys.stderr)
                return 1
            sha = _sha(f)
            asset = f"{s}{'' if aspect == 'landscape' else '-portrait'}-{sha[:8]}.mp4"
            todo.append((rel, f"{RELEASE}/{asset}", sha))
            upload.append((f, asset))
    keep = [l for l in lines if not (l.split() and l.split()[0] in {r for r, _, _ in todo})]
    new = keep + [" ".join(x) for x in todo]
    if not a.dry_run:
        MEDIA_TXT.write_text("\n".join(new) + "\n", encoding="utf-8")
    for rel, asset, sha in todo:
        print(f"{'would register' if a.dry_run else 'registered'}  {rel}  →  {asset}")
    print("\nupload (the maintainer, when the PR merges; nothing is uploaded here):")
    print(f"  gh release view {RELEASE} >/dev/null 2>&1 || gh release create {RELEASE} --latest=false --title 'Style swatches' "
          f"--notes 'Full style swatch videos (tools/media.txt, tools/fetch_media.sh styles)'")
    print("  d=$(mktemp -d)")
    for f, asset in upload:
        print(f"  cp {f.relative_to(ROOT)} \"$d/{asset}\"")
    print(f"  gh release upload {RELEASE} " + " ".join(f'"$d/{asset}"' for _, asset in upload))
    return 0


# ── spec ─────────────────────────────────────────────────────────────────────────────────────────────────────────
def cmd_spec(a):
    p = Path(a.folder)
    f = p / "tokens.json" if p.is_dir() else p
    try:
        t = json.loads(f.read_text(encoding="utf-8"))
        sp = spec_of(t, a.aspect)
    except (OSError, ValueError) as e:
        print(f"{f}: {e}", file=sys.stderr)
        return 1
    print(spec_shell(sp) if a.shell else json.dumps(sp, indent=1))
    return 0


def usage(msg):
    print(msg, file=sys.stderr)
    return 2


def main(argv):
    ap = argparse.ArgumentParser(prog="tools/styles.py", add_help=True)
    sub = ap.add_subparsers(dest="cmd")
    l = sub.add_parser("list")
    l.add_argument("--family")
    l.add_argument("--type")
    for k in ("pace", "aspect", "cost", "source"):
        l.add_argument(f"--{k}")
    l.add_argument("--json", action="store_true")
    r = sub.add_parser("readme")
    r.add_argument("--check", action="store_true")
    c = sub.add_parser("check")
    c.add_argument("slugs", nargs="*")
    c.add_argument("--meta", action="store_true")
    c.add_argument("--text", action="store_true")
    c.add_argument("--json", action="store_true")
    s = sub.add_parser("spec")
    s.add_argument("folder")
    s.add_argument("--aspect", default="landscape")
    s.add_argument("--shell", action="store_true")
    pg = sub.add_parser("page")
    pg.add_argument("page")
    pg.add_argument("slug")
    pg.add_argument("spec")
    g = sub.add_parser("register")
    g.add_argument("slugs", nargs="+")
    g.add_argument("--dry-run", action="store_true")
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.split("\n\n")[1])
        return 0 if argv else 2
    try:
        a = ap.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code else 0
    try:
        return {"list": cmd_list, "readme": cmd_readme, "check": cmd_check, "spec": cmd_spec, "register": cmd_register, "page": cmd_page}[a.cmd](a)
    except ValueError as e:   # families.json malformed
        print(f"✗ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
