"""bin/vh breakdown: a reference film taken apart in one command. Its first run with --beats auto (the default when the
film has sound and uv is here) downloads librosa through uv, over the network, unless uv has it cached; --beats off
stays offline. playbook/07's frame grabbing and first layers: the film's frame-to-frame change, where each transition
starts, how the cuts sit on the music's beat grid, a contact strip of each transition, each segment's keyframe and
where its motion is, and a "what to swap" table to fill in.

usage: bin/vh breakdown <video> [--out DIR] [--fps 30] [--beats auto|off|beats.json] [--json]

  change       the mean absolute difference of each frame from the one before, at --fps (at most the film's own), on
               a 64×36 grey copy: 0–255
  transitions  a cut: one frame whose change stands out (over 3× the median change of the second around it, and 20 or
               more) and is the largest within 2 frames; a soft transition (a dissolve, a whip, a quick push): 2 to 12
               frames in a row over 2× that median and 6 or more; a longer run is motion inside a segment, not a
               transition. Each: its start (s and frame), its kind, its strength (the change at its peak)
  segments     between transitions: start, end, length, mean change (how much moves), the keyframe (the middle
               frame) and a heat map of where the change is
  beats        with --beats auto (the default when the film has sound and uv is here): bin/vh beats on its audio; a
               beats.json of bin/vh beats can be given instead. Each cut's offset from the nearest beat, how many
               land within one frame of a beat and of a downbeat, the median offset
  out          <out>/breakdown.json (v 1, below), change.png (the change over time, transitions and beats marked),
               cuts.jpg (five frames round each transition: two before, the first after, two more), segments.jpg
               (each segment's keyframe and heat map), swap.md (the "what to swap" table: each segment's measured
               timing to keep, and empty cells for what it does and what to swap). Default <out>: in a project, its
               research/breakdown/<video name>/, else <video name>-breakdown/ beside the video
breakdown.json: {"v": 1, "video", "fps", "frames", "duration", "change": [per frame], "transitions": [{"t", "frame",
"kind": "cut"|"soft", "frames", "strength"}], "segments": [{"i", "start", "end", "length", "motion", "keyframe"}],
"stats": {"cuts", "soft", "asl", "median", "shortest", "longest"}, "beats": {"bpm", "on_beat", "on_downbeat", "of",
"median_offset_ms", "offsets_ms"} | null}. --json prints it. Needs ffmpeg; the pictures need pillow (bin/vh runs this
through uv). Exit: 0 · 1 a film it cannot read · 2 usage.
"""
import argparse, json, math, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
GW, GH = 64, 36


class Usage(Exception):
    """A usage error: exit 2."""


def probe(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,r_frame_rate:format=duration", "-of", "json", str(video)],
                       capture_output=True, text=True)
    try:
        d = json.loads(r.stdout)
        dur = float(d["format"]["duration"])
    except (ValueError, KeyError, TypeError):
        raise Usage(f"{video}: not a video ffprobe can read")
    rate, audio = None, False
    for s in d.get("streams", []):
        if s.get("codec_type") == "video" and rate is None:
            n, _, m = str(s.get("r_frame_rate", "0/1")).partition("/")
            rate = float(n) / float(m or 1) if float(m or 1) else None
        audio = audio or s.get("codec_type") == "audio"
    if not rate:
        raise Usage(f"{video}: no video stream")
    return dur, rate, audio


def grey(video, fps):
    """The film at fps as 64×36 grey frames (bytes each)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={GW}:{GH}:flags=area,format=gray", "-f", "rawvideo", "-"],
                       capture_output=True)
    n = GW * GH
    return [r.stdout[i:i + n] for i in range(0, len(r.stdout) - n + 1, n)]


def median(xs):
    xs = sorted(xs)
    if not xs:
        return 0.0
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


def transitions(change, fps):
    """[(frame, kind, frames, strength)]: the cuts and soft transitions of a change curve (change[k]: frame k against k-1)."""
    n, half = len(change), max(1, int(fps / 2))
    local = [median(change[max(1, k - half):k + half + 1]) for k in range(n)]
    out, k = [], 1
    while k < n:
        c, base = change[k], local[k]
        if c >= max(20.0, 3 * base) and c == max(change[max(1, k - 2):k + 3]):
            out.append((k, "cut", 1, round(c, 1)))
            k += 3
            continue
        run = 0
        while k + run < n and change[k + run] >= max(6.0, 2 * local[k + run]):
            run += 1
        if 2 <= run <= 12:
            out.append((k, "soft", run, round(max(change[k:k + run]), 1)))
        k += max(run, 1)
    merged = []   # one event from those that start within 0.3 s of the last one's end: a flash and its cut, a push and its settle
    for ev in out:
        if merged and ev[0] - (merged[-1][0] + merged[-1][2]) <= round(0.3 * fps):
            f0, kind, nf, st = merged[-1]
            merged[-1] = (f0, "cut" if "cut" in (kind, ev[1]) else "soft", ev[0] + ev[2] - f0, max(st, ev[3]))
        else:
            merged.append(ev)
    return merged


def beat_fit(cuts_t, beats, downbeats, fps):
    if not beats or not cuts_t:
        return None
    frame = 1 / fps
    offs = [min((t - b for b in beats), key=abs) for t in cuts_t]
    on = sum(1 for o in offs if abs(o) <= frame + 1e-6)
    on_down = sum(1 for t in cuts_t if downbeats and min(abs(t - b) for b in downbeats) <= frame + 1e-6)
    return {"on_beat": on, "on_downbeat": on_down, "of": len(cuts_t), "median_offset_ms": round(median(offs) * 1000),
            "offsets_ms": [round(o * 1000) for o in offs]}


def run_beats(video, dur, tmp):
    """bin/vh beats on the film's audio, through uv (librosa); None when it cannot run."""
    if not shutil.which("uv"):
        return None, "no uv (bin/vh beats needs librosa)"
    wav = Path(tmp) / "audio.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "22050", str(wav)], capture_output=True)
    if not wav.is_file():
        return None, "the audio could not be read"
    out = Path(tmp) / "beats.json"
    r = subprocess.run(["uv", "run", "-q", "--no-project", "--with", "librosa", "python", str(ROOT / "tools" / "audio" / "beats.py"), str(wav), str(out), "--no-drums"],
                       capture_output=True, text=True, timeout=600)
    if r.returncode or not out.is_file():
        return None, f"bin/vh beats failed: {(r.stderr or r.stdout).strip()[-200:]}"
    return json.loads(out.read_text(encoding="utf-8")), None


def frames_at(video, times, width, rate):
    """PIL images of the film at these times (seconds), width px wide: the frames picked by number in one decode."""
    from PIL import Image
    want = sorted({max(0, round(t * rate)) for t in times})
    got = {}
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(0, len(want), 400):   # a select expression of 400 terms at most
            part = want[i:i + 400]
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf", "select='" + "+".join(f"eq(n\\,{n})" for n in part) + f"',scale={width}:-2",
                            "-fps_mode", "passthrough", str(Path(tmp) / f"{i:06d}-%05d.png")], capture_output=True)
            files = sorted(Path(tmp).glob(f"{i:06d}-*.png"))
            for n, f in zip(part, files):
                got[n] = Image.open(f).convert("RGB")
                got[n].load()
    return [got.get(max(0, round(t * rate))) for t in times]


def pictures(video, data, gray, out):
    from PIL import Image, ImageDraw
    import vhdraw as V
    fps, n = data["fps"], len(data["change"])
    # change.png: the curve, the transitions (red: cut, amber: soft), the beats (ticks along the bottom)
    w, h, pad = 1600, 360, 40
    img = Image.new("RGB", (w, h), V.BG)
    d = ImageDraw.Draw(img)
    top = max(30.0, max(data["change"]) if data["change"] else 30.0)
    xs = lambda k: pad + (w - 2 * pad) * k / max(1, n - 1)   # noqa: E731
    ys = lambda v: h - pad - (h - 2 * pad - 20) * min(1.0, v / top)   # noqa: E731
    for tr in data["transitions"]:
        d.line([(xs(tr["frame"]), pad), (xs(tr["frame"]), h - pad)], fill=V.RED if tr["kind"] == "cut" else V.AMBER, width=2)
    d.line([(xs(k), ys(v)) for k, v in enumerate(data["change"])], fill=V.INK, width=1)
    for b in (data.get("beats") or {}).get("_beats", []):
        d.line([(xs(b * fps), h - pad + 4), (xs(b * fps), h - pad + 12)], fill=V.BLUE, width=1)
    f = V.font(18)
    V.text(d, (pad, 8), f"change per frame (0–{top:.0f}) · {len(data['transitions'])} transitions · {data['duration']:.1f} s", f, fill=V.MUTED)
    for s in range(0, int(data["duration"]) + 1, 10):
        V.text(d, (xs(s * fps), h - pad + 16), f"{s}s", V.font(14), fill=V.MUTED, anchor="ma")
    V.save(img, out / "change.png")
    # cuts.jpg: a row of five frames round each transition (at most 40 rows)
    rows = data["transitions"][:40]
    tw, lab = 240, 26
    if rows:
        th = tw * 9 // 16
        sheet = Image.new("RGB", (5 * tw + 6 * 6 + 150, len(rows) * (th + 6) + 6), (24, 24, 26))
        d = ImageDraw.Draw(sheet)
        strips = frames_at(video, [(tr["frame"] + o) / fps for tr in rows for o in (-2, -1, 0, 1, 2)], tw, data["rate"])
        for r, tr in enumerate(rows):
            k = tr["frame"]
            ims = strips[r * 5:r * 5 + 5]
            y = 6 + r * (th + 6)
            V.text(d, (8, y + 8), f"{tr['t']:.2f} s", V.font(20, bold=True), fill=(255, 220, 0))
            V.text(d, (8, y + 36), f"{tr['kind']} · {tr['strength']}", V.font(16), fill=(220, 220, 220))
            for i, im in enumerate(ims):
                if im is not None:
                    im = im.resize((tw, th))
                    sheet.paste(im, (150 + 6 + i * (tw + 6), y))
                if i == 2:
                    d.rectangle([150 + 6 + i * (tw + 6) - 2, y - 2, 150 + 6 + i * (tw + 6) + tw + 1, y + th + 1], outline=(214, 151, 26), width=2)
        sheet.save(out / "cuts.jpg", "JPEG", quality=85)   # rows of real frames: a JPEG, a tenth of the PNG
    # segments.jpg: each segment's keyframe with its heat map beside it
    segs = data["segments"][:60]
    if segs:
        kw, kh = 320, 180
        cols = 3
        cell_w, cell_h = 2 * kw + 18, kh + lab + 14
        sheet = Image.new("RGB", (cols * cell_w + 6, math.ceil(len(segs) / cols) * cell_h + 6), (24, 24, 26))
        d = ImageDraw.Draw(sheet)
        keys = frames_at(video, [s["keyframe"] for s in segs], kw, data["rate"])
        for i, s in enumerate(segs):
            x, y = 6 + (i % cols) * cell_w, 6 + (i // cols) * cell_h
            if keys[i] is not None:
                sheet.paste(keys[i].resize((kw, kh)), (x, y))
            a, b = int(s["start"] * fps), max(int(s["start"] * fps) + 1, int(s["end"] * fps))
            acc = [0] * (GW * GH)
            for k in range(max(1, a), min(b, len(gray))):
                p, q = gray[k - 1], gray[k]
                for j in range(GW * GH):
                    acc[j] += abs(q[j] - p[j])
            m = max(acc) or 1
            heat = Image.new("RGB", (GW, GH))
            heat.putdata([(int(255 * v / m), int(120 * v / m), int(40 + 60 * (1 - v / m))) for v in acc])
            sheet.paste(heat.resize((kw, kh), Image.NEAREST), (x + kw + 6, y))
            V.text(d, (x, y + kh + 4), f"#{s['i']}  {s['start']:.2f}–{s['end']:.2f} s ({s['length']:.2f} s) · motion {s['motion']}", V.font(17), fill=(235, 235, 235))
        sheet.save(out / "segments.jpg", "JPEG", quality=85)


def swap_table(data):
    lines = ["# 换什么 · " + Path(data["video"]).name, "",
             f"{data['duration']:.1f} s · {data['stats']['cuts']} cuts, {data['stats']['soft']} soft transitions · average shot {data['stats']['asl']} s"
             + (f" · cuts on the beat {data['beats']['on_beat']}/{data['beats']['of']}" if data.get("beats") else ""), "",
             "留下的是量出来的结构（时长、切点、运动多少），换的是内容。后三列由看片的人填：这一段在做什么、复刻时保留什么、换成什么。", "",
             "| # | 时间 | 时长 | 转场出 | 运动 | 在做什么 | 留 | 换 |", "|---|---|---|---|---|---|---|---|"]
    trs = {round(t["t"], 2): t for t in data["transitions"]}
    for s in data["segments"]:
        out = trs.get(round(s["end"], 2))
        lines.append(f"| {s['i']} | {s['start']:.2f}–{s['end']:.2f} | {s['length']:.2f} s | {out['kind'] if out else '片尾'} | {s['motion']} | {{…}} | {{…}} | {{…}} |")
    return "\n".join(lines) + "\n"


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh breakdown", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    ap.add_argument("video")
    ap.add_argument("--out")
    ap.add_argument("--fps", type=float, default=30)
    ap.add_argument("--beats", default="auto", help="auto, off, or a beats.json of bin/vh beats")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    say = (lambda *x: print(*x, file=sys.stderr)) if a.json else print
    video = Path(a.video).expanduser()
    if not video.is_file():
        print(f"bin/vh breakdown: no such video: {a.video}", file=sys.stderr)
        return 2
    if a.beats not in ("auto", "off") and not Path(a.beats).is_file():
        print(f"bin/vh breakdown: --beats is auto, off or a beats.json (no {a.beats})", file=sys.stderr)
        return 2
    if a.fps <= 0:
        print("bin/vh breakdown: --fps is more than 0", file=sys.stderr)
        return 2
    try:
        dur, rate, audio = probe(video)
    except Usage as e:
        print(f"bin/vh breakdown: {e}", file=sys.stderr)
        return 1
    fps = min(a.fps, rate)
    gray = grey(video, fps)
    if len(gray) < 3:
        print(f"bin/vh breakdown: {video}: too few frames to read", file=sys.stderr)
        return 1
    change = [0.0] + [round(sum(abs(q[j] - p[j]) for j in range(GW * GH)) / (GW * GH), 2) for p, q in zip(gray, gray[1:])]
    trs = transitions(change, fps)
    marks = [0] + [k for k, *_ in trs] + [len(gray)]
    segs = []
    for i, (a_, b_) in enumerate(zip(marks, marks[1:])):
        if b_ <= a_:
            continue
        segs.append({"i": len(segs) + 1, "start": round(a_ / fps, 3), "end": round(b_ / fps, 3), "length": round((b_ - a_) / fps, 3),
                     "motion": round(sum(change[a_ + 1:b_]) / max(1, b_ - a_ - 1), 2), "keyframe": round((a_ + b_) / 2 / fps, 3)})
    lens = [s["length"] for s in segs]
    data = {"v": 1, "video": str(video.resolve()), "fps": fps, "rate": rate, "frames": len(gray), "duration": round(dur, 3), "change": change,
            "transitions": [{"t": round(k / fps, 3), "frame": k, "kind": kind, "frames": nfr, "strength": st} for k, kind, nfr, st in trs],
            "segments": segs, "stats": {"cuts": sum(1 for t in trs if t[1] == "cut"), "soft": sum(1 for t in trs if t[1] == "soft"),
                                        "asl": round(sum(lens) / len(lens), 2) if lens else None, "median": round(median(lens), 2) if lens else None,
                                        "shortest": min(lens) if lens else None, "longest": max(lens) if lens else None},
            "beats": None}
    note = None
    with tempfile.TemporaryDirectory() as tmp:
        bm = None
        if a.beats not in ("auto", "off"):
            bm = json.loads(Path(a.beats).read_text(encoding="utf-8"))
        elif a.beats == "auto" and audio:
            bm, note = run_beats(video, dur, tmp)
        elif a.beats == "auto":
            note = "no sound"
        if bm:
            fit = beat_fit([t["t"] for t in data["transitions"]], bm.get("beats") or [], bm.get("downbeats") or [], fps)
            if fit:
                data["beats"] = dict(fit, bpm=bm.get("bpm"))
    if a.out:
        out = Path(a.out).expanduser()
    else:
        sys.path.insert(0, str(ROOT / "tools" / "assets"))
        import ledger
        proj = ledger.project_of(video.parent)
        out = proj / "research" / "breakdown" / video.stem if proj else video.parent / f"{video.stem}-breakdown"
    out.mkdir(parents=True, exist_ok=True)
    try:
        if data.get("beats"):
            data["beats"]["_beats"] = (bm or {}).get("beats") or []
        pictures(video, data, gray, out)
    except ImportError:
        note = (note + "; " if note else "") + "no pictures: pillow is missing (bin/vh breakdown runs it through uv)"
    finally:
        if data.get("beats"):
            data["beats"].pop("_beats", None)
    (out / "breakdown.json").write_text(json.dumps(data, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "swap.md").write_text(swap_table(data), encoding="utf-8")
    st = data["stats"]
    say(f"{video.name} · {dur:.1f} s at {fps:g} fps · {st['cuts']} cuts, {st['soft']} soft transitions · {len(segs)} segments,"
        f" average {st['asl']} s (median {st['median']}, {st['shortest']}–{st['longest']})")
    for t in data["transitions"]:
        say(f"  {t['t']:>7.2f} s  {t['kind']:<4} {t['strength']:>6}" + (f"  ({t['frames']} frames)" if t["frames"] > 1 else ""))
    if data["beats"]:
        b = data["beats"]
        say(f"  beats {b['bpm']} bpm: {b['on_beat']} of {b['of']} transitions within a frame of a beat, {b['on_downbeat']} of a downbeat, median offset {b['median_offset_ms']} ms")
    elif note:
        say(f"  beats: {note}")
    say(f"→ {out}: breakdown.json, change.png, cuts.jpg, segments.jpg, swap.md")
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
