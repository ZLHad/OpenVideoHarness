"""Studio's launcher icon, drawn by code (stdlib only: no Pillow, no SVG renderer, no iconutil), so that bin/vh studio
--install-icon works on a machine with nothing else installed. The PNGs and the .icns are made here at install time and
never committed: this file is the icon's source.

  python3 tools/desk/icon.py png <size> <out.png> [--design D]     one square PNG
  python3 tools/desk/icon.py icns <out.icns> [--design D]          the macOS icon, every size from 16 to 1024 in it
  python3 tools/desk/icon.py sheet <out.png>                       the designs side by side at 16, 32, 128 and 512 px, on a
                                                                   light and a dark ground, 16 and 32 also enlarged ×4

The designs are the console's mark: the dark ground (ui.css --bg #111) and the cyan square of its favicon
(tools/desk/static/index.html), the one thing that reads at 16 px. "viewfinder" (the one installed) frames the square
with a camera's four corners; "frame" is the favicon alone; "timeline" sets the square on a ruler with a playhead. Under
32 px the corners and the ruler go: what is left is the favicon. Each pixel's colour comes from signed distances (exact
coverage at the edges, no supersampling), on Apple's icon grid: an 824 px tile in 1024, its corner 185, a soft shadow.
"""
import math, struct, sys, zlib
from pathlib import Path

DESIGNS = ("viewfinder", "frame", "timeline")
DEFAULT = "viewfinder"
CYAN = (0x5E, 0xC9, 0xDC)
INK = (0xEB, 0xE8, 0xE2)
TOP, BOTTOM = (0x22, 0x22, 0x22), (0x0E, 0x0E, 0x0E)   # the tile's light falls from above, as on every Dock icon


def _box(px, py, cx, cy, hw, hh, r):
    """Signed distance from (px, py) to a rounded box (centre, half sizes, corner radius); < 0 inside."""
    qx = abs(px - cx) - hw + r
    qy = abs(py - cy) - hh + r
    ox, oy = max(qx, 0.0), max(qy, 0.0)
    return math.hypot(ox, oy) + min(max(qx, qy), 0.0) - r


def layers(design, size):
    """What to draw, back to front, in 1024 units: (kind, params, rgb, alpha). Small sizes drop what would blur."""
    small = size < 48
    out = [("shadow", (512, 524, 412, 412, 185), (0, 0, 0), 0.45),
           ("tile", (512, 512, 412, 412, 185), None, 1.0),
           ("rim", (512, 512, 412, 412, 185), (255, 255, 255), 0.10)]
    if design == "frame" or small:
        h = 168 if small else 150
        out.append(("box", (512, 512, h, h, 26), CYAN, 1.0))
        return out
    if design == "viewfinder":
        out.append(("box", (512, 512, 104, 104, 18), CYAN, 1.0))
        inset, arm, w = 236, 104, 26   # the corners: where they start from the tile's centre, how long, how thick
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = 512 + sx * inset, 512 + sy * inset
                out.append(("box", (x - sx * (arm / 2 - w / 2), y, arm / 2, w / 2, w / 2), INK, 0.86))
                out.append(("box", (x, y - sy * (arm / 2 - w / 2), w / 2, arm / 2, w / 2), INK, 0.86))
        return out
    # timeline: the square above a ruler, a playhead through both
    out.append(("box", (512, 440, 128, 128, 22), CYAN, 1.0))
    out.append(("box", (512, 690, 270, 9, 9), INK, 0.55))
    for i in range(7):
        out.append(("box", (242 + i * 90, 690, 6, 26 if i % 3 == 0 else 16, 6), INK, 0.55))
    out.append(("box", (602, 640, 9, 120, 9), CYAN, 1.0))
    return out


def render(size, design=DEFAULT):
    """The icon at size × size px → bytes, RGBA rows."""
    k = size / 1024.0
    buf = [0.0] * (size * size * 4)   # premultiplied RGBA
    for kind, (cx, cy, hw, hh, r), rgb, alpha in layers(design, size):
        cx, cy, hw, hh, r = cx * k, cy * k, hw * k, hh * k, r * k
        if size < 48 and kind != "shadow":   # small sizes: edges on whole pixels, or a 16 px square is a blur
            hw, hh = max(1, round(hw)), max(1, round(hh))
        blur = 34 * k if kind == "shadow" else 0
        pad = blur + 2
        x0, x1 = max(0, int(cx - hw - pad)), min(size, int(math.ceil(cx + hw + pad)))
        y0, y1 = max(0, int(cy - hh - pad)), min(size, int(math.ceil(cy + hh + pad)))
        rim_w = max(1.0, 6 * k)
        for y in range(y0, y1):
            py = y + 0.5
            if kind == "tile":
                t = min(1.0, max(0.0, (py / size - 0.06) / 0.88))
                col = [TOP[i] + (BOTTOM[i] - TOP[i]) * t for i in range(3)]
            for x in range(x0, x1):
                d = _box(x + 0.5, py, cx, cy, hw, hh, r)
                if kind == "shadow":
                    a = alpha * max(0.0, min(1.0, 0.5 - d / (blur or 1))) ** 2
                    c = (0, 0, 0)
                elif kind == "rim":   # a hairline just inside the tile's edge: the edge reads on a dark Dock too
                    a = alpha * max(0.0, min(1.0, 0.5 - d)) * max(0.0, min(1.0, 0.5 + d + rim_w))
                    c = rgb
                else:
                    a = alpha * max(0.0, min(1.0, 0.5 - d))
                    c = col if kind == "tile" else rgb
                if a <= 0.0:
                    continue
                i = (y * size + x) * 4
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
