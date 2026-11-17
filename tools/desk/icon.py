"""Studio's launcher icon, drawn by code (stdlib only: no Pillow, no SVG renderer, no iconutil), so that bin/vh studio
--install-icon works on a machine with nothing else installed. The PNGs and the .icns are made here at install time and
never committed: this file is the icon's source.

  python3 tools/desk/icon.py png <size> <out.png> [--design D]     one square PNG
  python3 tools/desk/icon.py icns <out.icns> [--design D]          the macOS icon, every size from 16 to 1024 in it
  python3 tools/desk/icon.py sheet <out.png>                       the designs side by side at 16, 32, 128 and 512 px, on a
                                                                   light and a dark ground, 16 and 32 also enlarged ×4

The mark is the project's own: the homepage's diamond (docs/site/index.html, .brand and its favicon), a rounded square
turned 45° in the cyan-violet-pink gradient, lit from inside on a dark tile. "viewfinder" (the one installed) frames it
with a camera's four corners; "diamond" is the diamond alone, which is also what every design keeps under 48 px, where
the corners would blur. Each pixel's colour comes from signed distances (exact coverage at the edges, no supersampling),
on Apple's icon grid: an 824 px tile in 1024, its corner 185, a soft shadow.
"""
import math, struct, sys, zlib
from pathlib import Path

DESIGNS = ("viewfinder", "diamond")
DEFAULT = "viewfinder"
IRI = ((0x7C, 0xF7, 0xFF), (0x9D, 0x8C, 0xFF), (0xF0, 0x7C, 0xFF))   # the homepage's gradient, top to bottom of the diamond
INK = (0xEC, 0xE9, 0xE3)
TOP, BOTTOM = (0x26, 0x26, 0x2C), (0x0B, 0x0B, 0x0E)   # the tile's light falls from above, as on every Dock icon
R2 = math.sqrt(2)


def iri(t):
    """The gradient at t (0 top, 1 bottom)."""
    t = min(1.0, max(0.0, t))
    a, b, u = (IRI[0], IRI[1], t * 2) if t < 0.5 else (IRI[1], IRI[2], t * 2 - 1)
    return tuple(a[i] + (b[i] - a[i]) * u for i in range(3))


def _box(px, py, cx, cy, hw, hh, r):
    """Signed distance from (px, py) to a rounded box (centre, half sizes, corner radius); < 0 inside."""
    qx = abs(px - cx) - hw + r
    qy = abs(py - cy) - hh + r
    ox, oy = max(qx, 0.0), max(qy, 0.0)
    return math.hypot(ox, oy) + min(max(qx, qy), 0.0) - r


def _diamond(px, py, cx, cy, h, r):
    """Signed distance to a rounded square of half side h turned 45° about its centre."""
    dx, dy = px - cx, py - cy
    return _box((dx + dy) / R2, (dy - dx) / R2, 0.0, 0.0, h, h, r)


def _corner(px, py, x, y, sx, sy, arm, w):
    """Signed distance to a viewfinder corner at (x, y): two strokes of width w with round ends, arm long, meeting there."""
    def seg(ax, ay, bx, by):
        vx, vy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
        return math.hypot(px - ax - vx * t, py - ay - vy * t)
    return min(seg(x - sx * arm, y, x, y), seg(x, y, x, y - sy * arm)) - w / 2


def layers(design, size):
    """What to draw, back to front, in 1024 units: (kind, params, alpha). Small sizes drop what would blur."""
    small = size < 48
    out = [("shadow", (512, 524, 412, 412, 185), 0.45),
           ("tile", (512, 512, 412, 412, 185), 1.0)]
    if design == "diamond" or small:
        out += [("diamond", (512, 512, 196, 44), 1.0)]
    else:
        out += [("bloom", (512, 512, 330), 1.0),
                ("glow", (512, 512, 120, 30), 0.6),
                ("diamond", (512, 512, 120, 30), 1.0)]
        inset, arm, w = 248, 112, 22   # the corners: where they sit from the tile's centre, how long, how thick
        out += [("corner", (512 + sx * inset, 512 + sy * inset, sx, sy, arm, w), 0.88) for sx in (-1, 1) for sy in (-1, 1)]
    return out + [("rim", (512, 512, 412, 412, 185), 1.0)]


def render(size, design=DEFAULT):
    """The icon at size × size px → bytes, RGBA rows."""
    k = size / 1024.0
    buf = [0.0] * (size * size * 4)   # premultiplied RGBA
    rim_w = max(1.0, 6 * k)
    for kind, p, alpha in layers(design, size):
        if kind in ("shadow", "tile", "rim"):
            cx, cy, hw, hh, r = (v * k for v in p)
            reach = hw + 34 * k + 2
            box = (cx - reach, cy - reach, cx + reach, cy + reach)
        elif kind == "bloom":
            cx, cy, rad = (v * k for v in p)
            box = (cx - rad, cy - rad, cx + rad, cy + rad)
        elif kind in ("diamond", "glow"):
            cx, cy, h, r = (v * k for v in p)
            sigma = 28 * k
            reach = h * R2 + (4 * sigma if kind == "glow" else 2)
            box = (cx - reach, cy - reach, cx + reach, cy + reach)
            top, span = cy - h * R2, 2 * h * R2   # the gradient runs from the square's top corner to its bottom one
        else:   # corner
            x, y, sx, sy, arm, w = p
            x, y, arm, w = x * k, y * k, arm * k, w * k
            box = (min(x, x - sx * arm) - w, min(y, y - sy * arm) - w, max(x, x - sx * arm) + w, max(y, y - sy * arm) + w)
        x0, y0 = max(0, int(box[0])), max(0, int(box[1]))
        x1, y1 = min(size, int(math.ceil(box[2]))), min(size, int(math.ceil(box[3])))
        for yy in range(y0, y1):
            py = yy + 0.5
            if kind == "tile":
                t = min(1.0, max(0.0, (py / size - 0.06) / 0.88))
                row = [TOP[i] + (BOTTOM[i] - TOP[i]) * t for i in range(3)]
            elif kind == "rim":   # brighter where the light falls, as an edge catches it
                t = min(1.0, max(0.0, (py / size - 0.06) / 0.88))
                ra = 0.22 + (0.04 - 0.22) * (t * 2) if t < 0.5 else 0.04 + (0.08 - 0.04) * (t * 2 - 1)
            elif kind in ("diamond", "glow"):
                row = iri((py - top) / span)
            for xx in range(x0, x1):
                px = xx + 0.5
                if kind == "shadow":
                    d = _box(px, py, cx, cy, hw, hh, r)
                    a = alpha * max(0.0, min(1.0, 0.5 - d / (34 * k or 1))) ** 2
                    c = (0, 0, 0)
                elif kind == "tile":
                    a, c = alpha * max(0.0, min(1.0, 0.5 - _box(px, py, cx, cy, hw, hh, r))), row
                elif kind == "rim":   # a hairline just inside the tile's edge: the edge reads on a dark Dock too
                    d = _box(px, py, cx, cy, hw, hh, r)
                    a, c = ra * max(0.0, min(1.0, 0.5 - d)) * max(0.0, min(1.0, 0.5 + d + rim_w)), (255, 255, 255)
                elif kind == "bloom":   # violet in the middle, a trace of cyan, nothing at the edge
                    u = math.hypot(px - cx, py - cy) / rad
                    if u >= 1.0:
                        continue
                    if u < 0.55:
                        f = u / 0.55
                        a = 0.34 + (0.08 - 0.34) * f
                        c = tuple(IRI[1][i] + (IRI[0][i] - IRI[1][i]) * f for i in range(3))
                    else:
                        a, c = 0.08 * (1.0 - (u - 0.55) / 0.45), IRI[0]
                elif kind == "glow":   # the diamond blurred (a Gaussian's edge, erfc), in its own colours
                    d = _diamond(px, py, cx, cy, h, r)
                    a, c = alpha * 0.5 * math.erfc(d / (sigma * R2)), row
                elif kind == "diamond":
                    a, c = alpha * max(0.0, min(1.0, 0.5 - _diamond(px, py, cx, cy, h, r))), row
                else:
                    a, c = alpha * max(0.0, min(1.0, 0.5 - _corner(px, py, x, y, sx, sy, arm, w))), INK
                if a <= 0.0:
                    continue
                i = (yy * size + xx) * 4
                inv = 1.0 - a
                buf[i] = c[0] / 255 * a + buf[i] * inv
                buf[i + 1] = c[1] / 255 * a + buf[i + 1] * inv
                buf[i + 2] = c[2] / 255 * a + buf[i + 2] * inv
                buf[i + 3] = a + buf[i + 3] * inv
    out = bytearray(size * size * 4)
    for i in range(0, len(buf), 4):
        a = buf[i + 3]
        if a > 0:
            out[i] = min(255, round(buf[i] / a * 255))
            out[i + 1] = min(255, round(buf[i + 1] / a * 255))
            out[i + 2] = min(255, round(buf[i + 2] / a * 255))
            out[i + 3] = min(255, round(a * 255))
    return bytes(out)


def png(width, height, rgba):
    """RGBA bytes → a PNG file's bytes."""
    raw = b"".join(b"\x00" + rgba[y * width * 4:(y + 1) * width * 4] for y in range(height))

    def chunk(t, data):
        return struct.pack(">I", len(data)) + t + data + struct.pack(">I", zlib.crc32(t + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


# the .icns entries: their type and the PNG size in each (macOS reads PNG in all of them since 10.7)
ICNS = (("icp4", 16), ("icp5", 32), ("ic11", 32), ("ic12", 64), ("ic07", 128), ("ic13", 256), ("ic08", 256),
        ("ic14", 512), ("ic09", 512), ("ic10", 1024))


def icns(design=DEFAULT):
    """The macOS icon file's bytes: each size drawn once, as a PNG in each entry that wants it."""
    pngs = {}
    body = b""
    for kind, n in ICNS:
        if n not in pngs:
            pngs[n] = png(n, n, render(n, design))
        body += kind.encode("ascii") + struct.pack(">I", len(pngs[n]) + 8) + pngs[n]
    return b"icns" + struct.pack(">I", len(body) + 8) + body


def sheet(sizes=(16, 32, 128, 512), zoom=(16, 32)):
    """Every design at each size on a light and a dark ground (a Dock in either mode), and the small ones enlarged ×4."""
    gap = 24
    cells = list(sizes) + [z * 4 for z in zoom]
    w = gap + sum(c + gap for c in cells)
    row_h = max(cells) + 2 * gap
    h = row_h * len(DESIGNS) * 2
    out = bytearray(w * h * 4)
    for di, d in enumerate(DESIGNS):
        pics = {n: render(n, d) for n in set(sizes) | set(zoom)}
        for gi, ground in enumerate(((0xEC, 0xEC, 0xEC), (0x26, 0x26, 0x28))):
            top = (di * 2 + gi) * row_h
            for y in range(top, top + row_h):
                for x in range(w):
                    j = (y * w + x) * 4
                    out[j:j + 4] = bytes(ground) + b"\xff"
            x = gap
            for ci, c in enumerate(cells):
                n, z = (c, 1) if ci < len(sizes) else (zoom[ci - len(sizes)], 4)
                src = pics[n]
                oy = top + gap + (max(cells) - c) // 2
                for yy in range(c):
                    for xx in range(c):
                        s = ((yy // z) * n + xx // z) * 4
                        a = src[s + 3] / 255
                        if a <= 0:
                            continue
                        j = ((oy + yy) * w + x + xx) * 4
                        for k in range(3):
                            out[j + k] = round(src[s + k] * a + out[j + k] * (1 - a))
                x += c + gap
    return png(w, h, bytes(out))


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="python3 tools/desk/icon.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="what", required=True)
    a1 = sub.add_parser("png")
    a1.add_argument("size", type=int)
    a1.add_argument("out")
    a1.add_argument("--design", choices=DESIGNS, default=DEFAULT)
    a2 = sub.add_parser("icns")
    a2.add_argument("out")
    a2.add_argument("--design", choices=DESIGNS, default=DEFAULT)
    a3 = sub.add_parser("sheet")
    a3.add_argument("out")
    a = ap.parse_args(argv)
    if a.what == "png":
        if not 8 <= a.size <= 2048:
            print("icon: a size from 8 to 2048", file=sys.stderr)
            return 2
        Path(a.out).write_bytes(png(a.size, a.size, render(a.size, a.design)))
    elif a.what == "icns":
        Path(a.out).write_bytes(icns(a.design))
    else:
        Path(a.out).write_bytes(sheet())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
