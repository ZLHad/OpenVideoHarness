"""Isolated-frame scan: a frame unlike both of its neighbours while the neighbours agree with each other.

usage: uv run --with numpy python tools/isoframes.py <video> [--allow t,t,…]
exit status: 0 none found (or only declared ones), 1 isolated frames found (times floored to the ms), 2 the video could not be read
  --allow  times in seconds of flashes you designed: a hit within one frame of one is listed as declared and does not fail

That is what a capture glitch looks like: a single frame that flashes another scene, or text drawn as garbage, between two
frames that are fine. The black/freeze/silence scan of `bin/vh check` cannot see it (it lasts one frame), and a snapshot
of the same time is clean, because the snapshot takes another capture path. Seen in a HyperFrames 0.8.82 render whose
drawElement capture failed its self-check and fell back to multi-worker screenshots with the browser GPU on.

Frames are decoded at 192x108 grey (108x192 for a portrait video) and compared three at a time. Frame i is isolated when
  - more than 1 % of its pixels differ by more than 12 grey levels from frame i-1,
  - the same holds against frame i+1,
  - and the share of pixels differing by more than 6 between frames i-1 and i+1 is under a quarter of the smaller of those.
A cut never qualifies (the frames on either side of it differ); a one-frame flash inside a shot does, intended or not.
What it cannot see: a glitch two or more frames long (a run of bad frames looks like motion), the first and last frame,
glitches under 1 % of the picture (a few garbled characters), and any frame whose neighbours already differ by a quarter
of the picture or more (particles, camera moves, line boil): those frames are counted and their stretches listed, so
strip-check them.
"""
import argparse, json, subprocess, sys
from fractions import Fraction
import numpy as np

STEP, CHANGED = 12, 0.01      # a pixel differs from a neighbour by more than STEP grey levels; frame differs: share > CHANGED
STEP_PN, MAX_PN = 6, 0.25     # the neighbours agree: their share over STEP_PN is under MAX_PN x the smaller of the two above

def die(msg):
    print(f"isoframes: {msg}", file=sys.stderr); sys.exit(2)

def probe(video):
    """→ (width, height, rate) of the first video stream; rate is the string ffmpeg would pick (r_frame_rate, or
    avg_frame_rate when r_frame_rate is a timebase rather than a frame rate), or None when neither is usable."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,avg_frame_rate,r_frame_rate", "-of", "json", video],
                         capture_output=True, text=True)
    st = (json.loads(out.stdout or "{}").get("streams") or [None])[0]
    if out.returncode or not st:
        die(f"no video stream in {video}: {out.stderr.strip() or 'ffprobe found none'}")
    for key in ("r_frame_rate", "avg_frame_rate"):
        num, _, den = st.get(key, "0/0").partition("/")
        if int(den or 0) > 0 and 0 < int(num) / int(den) <= 240:
            return st["width"], st["height"], st[key]
    return st["width"], st["height"], None

def frames(video, w, h, rate):
    """Decoded frames as int16 arrays, one at a time. The output is resampled to `rate` (a no-op for a constant-rate
    file), so frame i is at i / rate."""
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", video, "-map", "0:v:0", "-vf", f"scale={w}:{h},format=gray"]
    p = subprocess.Popen(cmd + (["-r", rate] if rate else []) + ["-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    while len(buf := p.stdout.read(w * h)) == w * h:
        yield np.frombuffer(buf, np.uint8).reshape(h, w).astype(np.int16)
    p.stdout.close()
    if p.wait():
        die(f"ffmpeg could not decode {video} (exit {p.returncode})")

def changed(a, b, step):
    return float((np.abs(a - b) > step).mean())

def runs(idx, gap):
    """[first, last] stretches of sorted frame numbers, joining neighbours up to `gap` frames apart."""
    out = []
    for i in idx:
        if out and i - out[-1][1] <= gap:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out

def scan(video):
    """→ (frames decoded, rate, hits [(frame, d_prev, d_next, d_pn)], blind [frames whose neighbours differ too much to judge])."""
    vw, vh, rate = probe(video)
    w, h = (108, 192) if vh > vw else (192, 108)
    hits, blind, n, prev, cur, d_prev = [], [], 0, None, None, 0.0
    for nxt in frames(video, w, h, rate):
        if cur is not None:
            d_next = changed(cur, nxt, STEP)
            if prev is not None:
                d_pn = changed(prev, nxt, STEP_PN)
                if d_pn >= MAX_PN:   # no glitch, however large, can pass the third test here
                    blind.append(n - 1)
                elif d_prev > CHANGED and d_next > CHANGED and d_pn < MAX_PN * min(d_prev, d_next):
                    hits.append((n - 1, d_prev, d_next, d_pn))
            d_prev = d_next
        prev, cur, n = cur, nxt, n + 1
    if n == 0:
        die(f"no frames decoded from {video}")
    return n, rate, hits, blind

def main():
    ap = argparse.ArgumentParser(prog="isoframes.py", usage=__doc__.split("\n\n")[1].split("\n")[0][7:])
    ap.add_argument("video")
    ap.add_argument("--allow", default="", help="times (s) of flashes you designed, comma-separated")
    a = ap.parse_args()
    try:
        allow = [float(x) for x in a.allow.split(",") if x.strip()]
    except ValueError:
        die(f"--allow takes seconds separated by commas, not {a.allow!r}")
    try:
        n, rate, hits, blind = scan(a.video)
    except OSError as e:   # ffprobe or ffmpeg missing: not a finding
        die(f"cannot run {e.filename or 'ffmpeg'}: {e.strerror}")
    fps = float(Fraction(rate)) if rate else None
    def t(i):   # floored to the ms, so `ffmpeg -ss <t> -i video` lands on this frame and not the next
        return f"{i * 1000 // Fraction(rate) / 1000:.3f}" if rate else f"frame {i}"
    def span(r):
        return f"{t(r[0])} s" if r[0] == r[1] else f"{t(r[0])}–{t(r[1])} s ({r[1] - r[0] + 1} frames)"
    declared = [x for x in hits if fps and any(abs(x[0] / fps - s) <= 1 / fps + 1e-6 for s in allow)]
    found = [x for x in hits if x not in declared]
    if found:
        print(f"{len(found)} isolated frame(s) in {n}: " + ", ".join(span(r) for r in runs([i for i, *_ in found], 2)))
        for i, d1, d2, d3 in found[:10]:
            print(f"  frame {i:>6}  {t(i):>9} s   differs from prev {d1:6.1%}, next {d2:6.1%}; prev vs next {d3:5.1%}")
        if len(found) > 10:
            print(f"  … {len(found) - 10} more")
    else:
        print(f"no isolated frames in {n} frames")
    if declared:
        print("  declared (--allow): " + ", ".join(span(r) for r in runs([i for i, *_ in declared], 2)))
    near = {j for i, *_ in hits for j in (i - 1, i + 1)}   # a flagged frame's neighbours see it, not motion
    rs = [r for r in runs([i for i in blind if i not in near], 3) if r[1] - r[0] + 1 >= max(3, round((fps or 30) / 2))]
    if rs:   # stretches of half a second or more; a cut makes one or two such frames, not listed
        k = sum(r[1] - r[0] + 1 for r in rs)
        more = f" (+{len(rs) - 6} more)" if len(rs) > 6 else ""
        print(f"  {k} of {n} frames ({k / n:.0%}) move too much to judge, strip-check them: "
              + ", ".join(span(r).split(" (")[0] for r in rs[:6]) + more)
    sys.exit(1 if found else 0)

if __name__ == "__main__":
    main()
