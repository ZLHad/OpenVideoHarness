"""Noise sigma of a clip: how much grain it has, in 8-bit luma levels.

usage (from the repo root): uv run --with numpy python tools/grain_est.py clip.mp4 [seconds]

Two estimates on the first few seconds (default 2), in grey. Spatial: Immerkaer 1996, a 3x3 kernel that also reacts to
texture, so measure a flat area or a flat test clip. Temporal: the frame difference divided by sqrt 2, only valid on a static
shot. Used to match the grain of a generated clip and the code-rendered layers (playbook/05-hybrid-genvideo.md); sigma moves
with the encoder settings, so measure with the settings you will deliver with. Checked on synthetic clips only.
"""
import argparse
import subprocess
import sys
import numpy as np


def immerkaer(a):  # kernel [[1,-2,1],[-2,4,-2],[1,-2,1]]
    h, w = a.shape
    c = (a[:-2, :-2] - 2 * a[:-2, 1:-1] + a[:-2, 2:] - 2 * a[1:-1, :-2] + 4 * a[1:-1, 1:-1] - 2 * a[1:-1, 2:]
         + a[2:, :-2] - 2 * a[2:, 1:-1] + a[2:, 2:])
    return np.sqrt(np.pi / 2) * np.abs(c).sum() / (6 * (h - 2) * (w - 2))


def main():
    ap = argparse.ArgumentParser(description="spatial and temporal noise sigma of a clip, in 8-bit luma levels")
    ap.add_argument("clip")
    ap.add_argument("seconds", nargs="?", default="2", help="how much of the clip to read (default 2)")
    a = ap.parse_args()
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0:s=x", a.clip], capture_output=True, text=True).stdout.strip()
    try:
        w, h = map(int, probe.split("x"))
    except ValueError:
        sys.exit(f"grain_est.py: ffprobe found no video stream in {a.clip}")
    raw = subprocess.run(["ffmpeg", "-v", "error", "-t", a.seconds, "-i", a.clip, "-vf", "format=gray", "-f", "rawvideo",
                          "-pix_fmt", "gray", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float64)
    if len(fr) < 2:
        sys.exit("grain_est.py: need at least 2 frames")
    spatial = np.mean([immerkaer(x) for x in fr])
    temporal = np.median(np.std(fr[1:] - fr[:-1], axis=(1, 2))) / np.sqrt(2)
    print(f"frames={len(fr)} spatial_sigma={spatial:.2f} temporal_sigma={temporal:.2f}")


if __name__ == "__main__":
    main()
