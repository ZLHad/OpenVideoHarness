"""Colour match in CIELAB: bake the difference between two frames into a 33x33x33 .cube LUT.

usage (from the repo root): uv run --with numpy --with pillow python tools/match_grade.py ref.png src.png out.cube [--strength 1.0]

ref is a frame from the code-rendered footage (the look to match), src a frame from the generated clip. Measure background
only: crop or mask the subject out of both first. Per channel in CIELAB (D65), the mean and standard deviation of src are
moved to those of ref (Reinhard et al. 2001). --strength 0 leaves the clip alone, 1 matches fully; start at 0.5-0.8 on real
footage, where the whole-frame statistics also push skin tones and highlights. sRGB in and out, R varies fastest in the .cube.
Use one LUT for the whole clip (a LUT per frame flickers):
  ffmpeg -i clip.mp4 -vf "lut3d=file=out.cube:interp=tetrahedral" ...
Prints the Lab mean and std of both frames. Checked on synthetic frames only (playbook/05-hybrid-genvideo.md).
"""
import argparse
import numpy as np
from PIL import Image

M = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WP = np.array([0.95047, 1.0, 1.08883])  # sRGB primaries, D65 white


def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def enc(c): c = np.clip(c, 0, 1); return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)
def f(t): d = 6 / 29; return np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4 / 29)
def finv(t): d = 6 / 29; return np.where(t > d, t ** 3, 3 * d * d * (t - 4 / 29))


def to_lab(rgb):  # rgb in 0-1, shape (..., 3)
    fx = f(lin(rgb) @ M.T / WP)
    return np.stack([116 * fx[..., 1] - 16, 500 * (fx[..., 0] - fx[..., 1]), 200 * (fx[..., 1] - fx[..., 2])], -1)


def to_rgb(lab):
    fy = (lab[..., 0] + 16) / 116
    fx, fz = fy + lab[..., 1] / 500, fy - lab[..., 2] / 200
    return enc((np.stack([finv(fx), finv(fy), finv(fz)], -1) * WP) @ np.linalg.inv(M).T)


def stats(path):
    lab = to_lab(np.asarray(Image.open(path).convert("RGB"), np.float64) / 255).reshape(-1, 3)
    return lab.mean(0), lab.std(0)


def main():
    ap = argparse.ArgumentParser(description="match one frame's Lab statistics to another's and write a .cube LUT")
    ap.add_argument("ref", help="frame with the look to match (code-rendered)")
    ap.add_argument("src", help="frame from the generated clip")
    ap.add_argument("out", help="the .cube file to write")
    ap.add_argument("--strength", type=float, default=1.0, help="0 = no change, 1 = full match (default 1)")
    a = ap.parse_args()
    (mr, sr), (ms, ss) = stats(a.ref), stats(a.src)
    gain = 1 + (np.where(ss > 1e-6, sr / ss, 1.0) - 1) * a.strength  # pull the std towards ref per channel ...
    target = ms + (mr - ms) * a.strength                               # ... then the mean
    n = 33
    g = np.linspace(0, 1, n)
    B, G, R = np.meshgrid(g, g, g, indexing="ij")                      # .cube order: R fastest, B slowest
    rgb = to_rgb((to_lab(np.stack([R, G, B], -1).reshape(-1, 3)) - ms) * gain + target)
    with open(a.out, "w") as fh:
        fh.write(f'TITLE "match_grade"\nLUT_3D_SIZE {n}\nDOMAIN_MIN 0 0 0\nDOMAIN_MAX 1 1 1\n')
        fh.writelines(f"{r:.6f} {g_:.6f} {b:.6f}\n" for r, g_, b in rgb)
    print("ref", mr.round(1), sr.round(1), "src", ms.round(1), ss.round(1))


if __name__ == "__main__":
    main()
