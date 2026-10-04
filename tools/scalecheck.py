"""Scale check: does a higher-resolution render (4K) show the same picture as the reference it was made from (the
approved 1080p cut)?

usage: uv run --with numpy python tools/scalecheck.py <video> <reference> [--sheet DIR]
exit status: 0 the same picture (WARN spans allowed), 1 a stretch that differs (FAIL), or frame counts / aspect / fps
             that differ, 2 a video could not be read

Why: rendering at device scale 2 (HyperFrames `--resolution 4k`) is not a resize. DOM text, CSS and SVG scale by
themselves; canvas and WebGL code has to multiply by devicePixelRatio itself, and any code that reads a canvas's pixel
size (canvas.width, image.width, getImageData) to place or size things draws them at twice the size at 4K. At 1080p the
ratio is 1, so the bug never shows until the 4K render. A crop "to check sharpness" misses it: the label is sharp, only
too big. This check catches it (the intro film's first 4K render: 11 stretches; the fixed one: none).

How: both videos are scaled to 480 px wide with an area filter (that averages away grain, sampling noise and
anti-aliasing, which differ between resolutions and are fine) and compared frame by frame on an 8x6 grid; a frame's
score is its worst tile's PSNR. Half a second or more of consecutive frames under FAIL_DB is a FAIL, under WARN_DB a
WARN to look at. --sheet writes, for each such stretch, the reference, the video scaled down and their difference side by
side. The thresholds come from two films and synthetic clips (2026-10-04): correct renders scored 30-41 dB at the median
and above 18 everywhere; layout bugs fell to 2-16 dB. Glow radii, 1-pixel WebGL lines and blur are expected to differ a
little at 4K (they are measured in device pixels): they show up as WARN, not FAIL.
"""
import argparse, json, subprocess, sys
from fractions import Fraction
from pathlib import Path
import numpy as np

W, GX, GY = 480, 8, 6
FAIL_DB, WARN_DB = 18.0, 24.0

def die(msg, code=2):
    print(f"scalecheck: {msg}", file=sys.stderr); sys.exit(code)

def probe(v):
    out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate,nb_read_packets", "-of", "json", v], capture_output=True, text=True)
    st = (json.loads(out.stdout or "{}").get("streams") or [None])[0]
    if out.returncode or not st:
        die(f"no video stream in {v}")
    return st["width"], st["height"], Fraction(st["r_frame_rate"]), int(st.get("nb_read_packets") or 0)

def frames(v, w, h):
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", v, "-map", "0:v:0",
                          "-vf", f"scale={w}:{h}:flags=area,format=gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    n = w * h
    while len(b := p.stdout.read(n)) == n:
        yield np.frombuffer(b, np.uint8).astype(np.float32).reshape(h, w)
    p.stdout.close(); p.wait()

def spans(score, below, least):
    """[first, last] runs of consecutive frames where score < below, at least `least` frames long. A layout bug holds
    for as long as the element is on screen; a glow or a flash dips and recovers, and stays under a run's length."""
    out = []
    for i in np.flatnonzero(score < below):
        if out and i - out[-1][1] == 1:
            out[-1][1] = int(i)
        else:
            out.append([int(i), int(i)])
    return [r for r in out if r[1] - r[0] + 1 >= least]

def main():
    ap = argparse.ArgumentParser(prog="scalecheck.py", usage="uv run --with numpy python tools/scalecheck.py <video> <reference> [--sheet DIR]")
    ap.add_argument("video"); ap.add_argument("reference"); ap.add_argument("--sheet", help="write a comparison image per flagged stretch here")
    a = ap.parse_args()
    try:
        vw, vh, vfps, vn = probe(a.video); rw, rh, rfps, rn = probe(a.reference)
    except OSError as e:
        die(f"cannot run {e.filename or 'ffprobe'}: {e.strerror}")
    print(f"{Path(a.video).name}: {vw}x{vh}, {float(vfps):g} fps, {vn} frames; reference {Path(a.reference).name}: {rw}x{rh}, {float(rfps):g} fps, {rn} frames")
    bad = []
    if abs(vw / vh - rw / rh) > 0.01:
        bad.append(f"different aspect ({vw}x{vh} vs {rw}x{rh})")
    if vfps != rfps:
        bad.append(f"different frame rate ({vfps} vs {rfps})")
    if vn != rn:
        bad.append(f"different frame counts ({vn} vs {rn})")
    if bad:
        for b in bad: print(f"FAIL {b}: not the same cut, nothing compared")
        sys.exit(1)
    w = min(W, rw // 2 * 2); h = round(w * rh / rw / 2) * 2   # never upscale the reference
    th, tw = h // GY, w // GX
    score = []
    for x, y in zip(frames(a.video, w, h), frames(a.reference, w, h)):
        d = ((x - y) ** 2)[: th * GY, : tw * GX].reshape(GY, th, GX, tw).mean(axis=(1, 3))
        m = float(d.max())
        score.append(99.0 if m < 1e-10 else 10 * np.log10(255 ** 2 / m))
    score = np.array(score)
    if len(score) == 0:
        die("no frames decoded")
    fps = float(rfps); least = max(3, round(fps / 2))
    fail, warn = spans(score, FAIL_DB, least), spans(score, WARN_DB, least)
    warn = [r for r in warn if not any(f[0] <= r[1] and r[0] <= f[1] for f in fail)]
    t = lambda i: f"{i / fps:.2f}"
    print(f"worst-tile PSNR at {w}x{h} ({GX}x{GY} tiles): median {np.median(score):.1f} dB, 5th percentile {np.percentile(score, 5):.1f}, "
          f"lowest {score.min():.1f} at {t(int(score.argmin()))} s")
    for name, rs in (("FAIL", fail), ("WARN", warn)):
        for r in rs[:10]:
            print(f"{name} {t(r[0])}–{t(r[1] + 1)} s: the picture differs (lowest {score[r[0]:r[1] + 1].min():.1f} dB, "
                  f"under {FAIL_DB if name == 'FAIL' else WARN_DB:g} for {r[1] - r[0] + 1} frames)")
        if len(rs) > 10: print(f"{name} … {len(rs) - 10} more")
    if a.sheet and (fail or warn):
        out = Path(a.sheet); out.mkdir(parents=True, exist_ok=True)
        for name, r in [("fail", r) for r in fail[:8]] + [("warn", r) for r in warn[:8]]:
            i = r[0] + int(score[r[0]:r[1] + 1].argmin()); ts = f"{i / fps:.3f}"
            f = out / f"scale-{name}-{ts}s.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", ts, "-i", a.reference, "-ss", ts, "-i", a.video, "-frames:v", "1", "-filter_complex",
                            "[0:v]scale=640:-2,format=rgb24,split[a][a2];[1:v]scale=640:-2:flags=area,format=rgb24,split[b][b2];"
                            "[a2][b2]blend=all_mode=difference,eq=brightness=0.1:contrast=4[d];[a][b][d]hstack=3", str(f)], check=False)
            print(f"  {f}  (reference | video scaled down | difference)")
    if not fail and not warn:
        print("ok: the same picture throughout")
    elif not fail:
        print("ok, with WARN stretches: look at them (glow, 1 px lines and blur differ a little by design; a shifted or resized element does not)")
    sys.exit(1 if fail else 0)

if __name__ == "__main__":
    main()
