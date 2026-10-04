"""Isolated-frame scan: a frame unlike both of its neighbours while the neighbours agree with each other.

usage: uv run --with numpy python tools/isoframes.py <video>
exit status: 0 none found, 1 isolated frames found (one line each on stdout, times floored to the ms), 2 the video could not be read

That is what a capture glitch looks like: a single frame that flashes another scene, or text drawn as garbage, between two
frames that are fine. The black/freeze/silence scan of `bin/vh check` cannot see it (it lasts one frame), and a snapshot
of the same time is clean, because the snapshot takes another capture path. Seen in a HyperFrames 0.8.82 render whose
drawElement capture failed its self-check and fell back to multi-worker screenshots with the browser GPU on.

Frames are decoded at 192x108 grey (108x192 for a portrait video) and compared three at a time. Frame i is isolated when
  - more than 1 % of its pixels differ by more than 12 grey levels from frame i-1,
  - the same holds against frame i+1,
  - and the share of pixels differing by more than 6 between frames i-1 and i+1 is under a quarter of the smaller of those.
A cut never qualifies (the frames on either side of it differ); a one-frame flash inside a shot does, intended or not.
"""
import json, subprocess, sys
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

def main():
    if len(sys.argv) != 2 or sys.argv[1].startswith("-"):
        print(__doc__.split("\n\n")[1]); sys.exit(0 if sys.argv[1:] in (["-h"], ["--help"]) else 2)
    video = sys.argv[1]
    vw, vh, rate = probe(video)
    w, h = (108, 192) if vh > vw else (192, 108)
    hits, n, prev, cur, d_prev = [], 0, None, None, 0.0
    for nxt in frames(video, w, h, rate):
        if cur is not None:
            d_next = changed(cur, nxt, STEP)
            if prev is not None and d_prev > CHANGED and d_next > CHANGED:
                d_pn = changed(prev, nxt, STEP_PN)
                if d_pn < MAX_PN * min(d_prev, d_next):
                    hits.append((n - 1, d_prev, d_next, d_pn))
            d_prev = d_next
        prev, cur, n = cur, nxt, n + 1
    if n == 0:
        die(f"no frames decoded from {video}")
    def at(i):   # floored to the ms, so `ffmpeg -ss <t> -i video` lands on this frame and not the next
        return f"{i * 1000 // Fraction(rate) / 1000:.3f} s" if rate else f"frame {i}"
    if not hits:
        print(f"no isolated frames in {n} frames"); return
    print(f"{len(hits)} isolated frame(s) in {n}: " + ", ".join(at(i) for i, *_ in hits))
    for i, a, b, c in hits:
        print(f"  frame {i:>6}  {at(i):>11}   differs from prev {a:6.1%}, next {b:6.1%}; prev vs next {c:5.1%}")
    sys.exit(1)

if __name__ == "__main__":
    main()
