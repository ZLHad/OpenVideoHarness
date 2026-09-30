"""A cover as it shows in real feeds, and whether its words survive that size.

usage: bin/vh cover-preview <image> [more …] [--text-px N[,M]] [--only bili,douyin,youtube,xhs] [--out PNG]

One row per cover. The cover is drawn at the real size of each feed slot, in CSS pixels (points on a phone), cropped
the way the slot crops it, with the platform's own overlay where it covers the picture (Bilibili's stats bar,
YouTube's and Bilibili's duration badge, Douyin's like count). Sizes, measured on 2026-10-01 logged out:
  Bilibili   home feed, 1920 px window 312×176 · home feed on a 375 pt phone 172×97 · watch page "related" 141×80
  YouTube    phone feed and search 375×211 · watch page "up next", 1280 px window 220×124
  Douyin     web 精选 400×225 · profile grid on a 375 pt phone 124×166 (3:4 crop; three columns, computed)
  Xiaohongshu  discover feed on a 375 pt phone 180×240 (3:4; a landscape cover shows at 4:3)
Feeds change their layout often: take these as today's, not forever.

The legibility check finds the lines of text in the cover (edges → words → lines; the boxes are drawn on the first
tile so you can see what was measured), or takes their height from --text-px (glyph height in the cover's pixels,
e.g. --text-px 96,28 for a 96 px title and a 28 px label). For each slot it gives the smallest and largest text
height as shown, against a rule of thumb taken from the smallest text size Apple's Human Interface Guidelines allow
(11 pt): 11 px and up reads, 8–11 px only when you know what it says, under 8 px does not read. It also gives the
text's contrast against the pixels around it (WCAG ratio: 4.5 good, 3 the floor for large text), whether a crop cuts
a line, and whether an overlay sits on one. It cannot read the words: a picture with lots of fine lines may show a
box that is not text; --text-px replaces the guess.

Output: --out, else <project>/out/check/cover-preview-<name>.png for a cover inside a project, else
./out/check/cover-preview-<name>.png under the current folder. Tiles are 1× CSS size: view the PNG at 100 % to see the
real size. A transparent cover is flattened onto white (a light feed page) and the output says so. Deterministic.
"""
import argparse, os, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vhdraw as V

# (key, platform, where zh, where en, w, h, aspect rule, overlay)
SLOTS = [
    ("bili-home", "bili", "首页推荐 · 1920 窗口", "home feed · 1920 window", 312, 176, "16:9", "bili"),
    ("bili-phone", "bili", "手机首页 · 双列", "phone home · 2 columns", 172, 97, "16:9", "bili"),
    ("bili-related", "bili", "播放页相关推荐", "watch page · related", 141, 80, "16:9", "badge"),
    ("yt-phone", "youtube", "手机信息流 / 搜索", "phone feed / search", 375, 211, "16:9", "badge"),
    ("yt-upnext", "youtube", "播放页 Up next · 1280 窗口", "watch page · up next", 220, 124, "16:9", "badge"),
    ("dy-web", "douyin", "电脑版精选", "web 精选", 400, 225, "16:9", None),
    ("dy-grid", "douyin", "手机主页 · 三列 3:4", "profile grid · 3:4", 124, 166, "3:4", "likes"),
    ("xhs-phone", "xhs", "手机发现页 · 双列", "discover · 2 columns", 180, 240, "xhs", None),
]
PLATFORM = {"bili": ("B站", "Bilibili"), "youtube": ("YouTube", "YouTube"), "douyin": ("抖音", "Douyin"), "xhs": ("小红书", "Xiaohongshu")}
READ_OK, READ_MIN = 11.0, 8.0

# ---------- text lines ----------
def _lin(a):
    c = a / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

def rel_lum(a):
    c = _lin(a)
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]

def text_lines(im):
    """[(x0, y0, x1, y1)] in the cover's pixels: lines of glyphs, found from edges merged along the line."""
    W0, H0 = im.size; f = min(1.0, 960 / max(W0, H0))
    small = im.resize((round(W0 * f), round(H0 * f)), Image.LANCZOS) if f < 1 else im
    L = rel_lum(np.asarray(small, dtype=np.float64)) ** (1 / 2.2)
    H, W = L.shape
    G = np.hypot(ndi.sobel(L, 1), ndi.sobel(L, 0))
    edge = G > max(0.35, np.percentile(G, 97) * 0.4)
    closed = ndi.binary_closing(edge, structure=np.ones((3, max(3, int(0.015 * max(W, H))))))
    lab, _ = ndi.label(closed)
    comps = []
    for i, sl in enumerate(ndi.find_objects(lab)):
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop; h, w = y1 - y0, x1 - x0
        if not (0.012 * H <= h <= 0.4 * H) or w < 0.1 * h: continue
        m = lab[sl] == i + 1; ys, xs = np.nonzero(m)
        fill = m.mean(); dens = edge[sl][m].mean()
        cols = m.any(0); top = np.argmax(m, 0); bot = h - np.argmax(m[::-1], 0)
        colspan = float(((bot - top) / h)[cols].mean()) if cols.any() else 0.0
        corr = abs(float(np.corrcoef(xs, ys)[0, 1])) if xs.std() > 0 and ys.std() > 0 else 0.0
        if dens < 0.12 or corr >= 0.8 or colspan < 0.4 or fill / max(colspan, 1e-6) < 0.3: continue   # lines, waves, outlines
        if fill > 0.95 and w > 8 * h: continue   # a solid bar
        comps.append([x0, y0, x1, y1, 1])
    comps.sort()
    lines = []
    for c in comps:   # glyphs → a line: overlapping heights, a small gap, similar size
        for ln in lines:
            h1, h2 = ln[3] - ln[1], c[3] - c[1]
            if (min(ln[3], c[3]) - max(ln[1], c[1]) >= 0.6 * min(h1, h2) and c[0] - ln[2] <= 1.2 * max(h1, h2)
                    and max(h1, h2) <= 1.8 * min(h1, h2)):
                ln[:] = [min(ln[0], c[0]), min(ln[1], c[1]), max(ln[2], c[2]), max(ln[3], c[3]), ln[4] + 1]; break
        else:
            lines.append(list(c))
    keep = []
    for x0, y0, x1, y1, n in lines:
        h, w = y1 - y0, x1 - x0
        if (n == 1 and w < 1.5 * h) or (h < 0.02 * H and w < 3 * h): continue
        keep.append((x0, y0, x1, y1))
    keep = [b for b in keep if not any(o != b and b[0] <= o[0] and b[1] <= o[1] and b[2] >= o[2] and b[3] >= o[3] for o in keep)]   # frames around text
    return [(x0 / f, y0 / f, x1 / f, y1 / f) for x0, y0, x1, y1 in keep]

def contrast(im, box):
    """WCAG contrast of a text line: the lighter and darker pixel groups inside its box."""
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    a = np.asarray(im.crop((x0, y0, max(x0 + 1, x1), max(y0 + 1, y1))), dtype=np.float64)
    Y = rel_lum(a).ravel()
    if Y.size < 4: return None
    t = np.median(Y); lo, hi = Y[Y <= t], Y[Y > t]
    if not len(hi): return 1.0
    a_, b_ = np.percentile(lo, 30), np.percentile(hi, 70)   # the cores of the two groups, not the anti-aliased rims
    return (max(a_, b_) + 0.05) / (min(a_, b_) + 0.05)

# ---------- slots ----------
def crop_for(W, H, rule):
    """(box in the cover, aspect label) for a slot's aspect rule."""
    if rule == "xhs": ar = 3 / 4 if W < H * 0.999 else (4 / 3 if W > H * 1.001 else 1.0)
    else: a, b = rule.split(":"); ar = int(a) / int(b)
    if W / H > ar: w = H * ar; return ((W - w) / 2, 0, (W + w) / 2, H), ar
    h = W / ar; return (0, (H - h) / 2, W, (H + h) / 2), ar

def overlay(d, x, y, w, h, kind):
    """The platform UI that sits on the picture (drawn roughly, in its real place and size); returns its box."""
    if kind == "bili":   # a dark gradient at the bottom with counts and the duration, 38 px at 176
        bh = round(h * 38 / 176)
        for i in range(bh):
            a = int(200 * (i / bh))
            d.line([(x, y + h - bh + i), (x + w, y + h - bh + i)], fill=(0, 0, 0, a))
        f = V.font(max(9, round(13 * h / 176)))
        V.text(d, (x + 6, y + h - bh / 2 + 2), "播放 1.2万  弹幕 356", f, (255, 255, 255, 235), "lm")
        V.text(d, (x + w - 6, y + h - bh / 2 + 2), "12:41", f, (255, 255, 255, 235), "rm")
        return (x, y + h - bh, x + w, y + h)
    if kind == "badge":   # a duration badge in the bottom-right corner, about 38×20 at 220 px wide
        bw, bh = max(26, round(w * 38 / 220)), max(13, round(h * 20 / 124))
        box = (x + w - bw - 5, y + h - bh - 5, x + w - 5, y + h - 5)
        d.rounded_rectangle(box, radius=3, fill=(0, 0, 0, 205))
        V.text(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), "12:41", V.font(max(8, round(bh * 0.62))), (255, 255, 255, 240), "mm")
        return box
    if kind == "likes":   # the like count in the bottom-left corner of a Douyin grid tile
        bh = round(h * 0.16)
        for i in range(bh):
            d.line([(x, y + h - bh + i), (x + w, y + h - bh + i)], fill=(0, 0, 0, int(150 * i / bh)))
        V.text(d, (x + 6, y + h - bh / 2), "赞 1.2w", V.font(max(9, round(h * 0.075))), (255, 255, 255, 240), "lm")
        return (x, y + h - bh, x + w * 0.6, y + h)
    return None

def verdict(px):
    return "ok" if px >= READ_OK else ("small" if px >= READ_MIN else "no")

# ---------- one cover ----------
def analyse(im, text_px):
    W, H = im.size
    lines = text_lines(im)
    heights = sorted(set(text_px)) if text_px else sorted(b[3] - b[1] for b in lines)
    cons = [c for c in (contrast(im, b) for b in lines) if c is not None]
    return {"lines": lines, "heights": heights, "contrast": min(cons) if cons else None,
            "title_contrast": contrast(im, max(lines, key=lambda b: b[3] - b[1])) if lines else None, "size": (W, H)}

def main():
    ap = argparse.ArgumentParser(prog="bin/vh cover-preview", description=__doc__.split("\n\n")[0])
    ap.add_argument("images", nargs="+")
    ap.add_argument("--text-px", default="", help="glyph heights in the cover's pixels, e.g. 96,28 (default: measured)")
    ap.add_argument("--only", default="", help="platforms to show: bili,douyin,youtube,xhs (default all)")
    ap.add_argument("--lang", choices=("zh", "en"), help="labels (default zh)")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        text_px = [float(x) for x in a.text_px.split(",") if x.strip()]
    except ValueError:
        ap.error("--text-px takes numbers, e.g. 96,28")
    if any(v <= 0 for v in text_px): ap.error("--text-px must be > 0")
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    bad = only - set(PLATFORM)
    if bad: ap.error(f"--only: unknown platform(s) {', '.join(sorted(bad))} (bili, douyin, youtube, xhs)")
    slots = [s for s in SLOTS if not only or s[1] in only]
    paths = [Path(p) for p in a.images]
    for p in paths:
        if not p.exists(): raise SystemExit(f"cover-preview: no such image: {p}")
    lang = a.lang or "zh"; zh = lang == "zh"
    covers, flat = [], []
    for p in paths:
        try:
            with Image.open(p) as im:
                im.load()
                if im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info):
                    rgba = im.convert("RGBA")   # a feed shows its own page behind transparent pixels: white here, not black
                    if rgba.getextrema()[3][0] < 255:
                        flat.append(p.name)
                    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255)); bg.alpha_composite(rgba); covers.append(bg.convert("RGB"))
                else:
                    covers.append(im.convert("RGB"))
        except (OSError, ValueError, SyntaxError):
            raise SystemExit(f"cover-preview: {p} is not an image")
    infos = [analyse(im, text_px) for im in covers]
    pad, gap, first_w = 28, 26, 300
    lab_h, rep_h = 58, 120
    rows_h = [max(max(s[5] for s in slots), first_w * im.size[1] // im.size[0]) + lab_h + rep_h for im in covers]
    W = pad * 2 + first_w + gap + sum(s[4] for s in slots) + gap * len(slots)
    H = 108 + sum(h + 34 for h in rows_h) + 20
    img = Image.new("RGB", (W, H), V.BG); d = ImageDraw.Draw(img, "RGBA")
    V.text(d, (pad, 22), "封面在信息流里的真实大小" if zh else "Covers at real feed size", V.font(30, bold=True), V.INK)
    V.text(d, (pad, 64), ("按 100 % 查看：每格就是该位置的实际像素（CSS px / 手机 pt）；红框 = 测到的文字行；"
                          f"字高 ≥ {READ_OK:g} px 读得清，{READ_MIN:g}–{READ_OK:g} px 勉强，< {READ_MIN:g} px 读不出")
           if zh else (f"View at 100 %: every tile is the slot's real size (CSS px / phone pt); red boxes = text lines measured; "
                       f"text >= {READ_OK:g} px reads, {READ_MIN:g}-{READ_OK:g} px barely, < {READ_MIN:g} px does not"),
           V.font(18), V.MUTED)
    report = []
    y = 108
    for ci, (im, info, p) in enumerate(zip(covers, infos, paths)):
        if ci: y += rows_h[ci - 1] + 34
        Wc, Hc = im.size
        # the cover itself, with the measured lines boxed
        fw = first_w; fh = round(fw * Hc / Wc)
        big = im.resize((fw, fh), Image.LANCZOS); bd = ImageDraw.Draw(big)
        for x0, y0, x1, y1 in info["lines"]:
            s = fw / Wc; bd.rectangle([x0 * s, y0 * s, x1 * s, y1 * s], outline=V.RED, width=2)
        img.paste(big, (pad, y + lab_h))
        V.text(d, (pad, y + 4), V.fit(d, p.name, V.font(22, bold=True), first_w), V.font(22, bold=True), V.INK)
        V.text(d, (pad, y + 32), f"{Wc}×{Hc}", V.font(17), V.MUTED)
        hs = info["heights"]
        lines_txt = []
        if hs:
            src = ("--text-px" if text_px else ("测到" if zh else "measured"))
            lines_txt.append((f"文字行 {len(info['lines'])} 条（{src}）" if zh else f"{len(info['lines'])} text line(s) ({src})") if not text_px else src)
            lines_txt.append((f"字高 {hs[0]:.0f}–{hs[-1]:.0f} px" if zh else f"glyph height {hs[0]:.0f}-{hs[-1]:.0f} px"))
        else:
            lines_txt.append("没测到文字行（可用 --text-px）" if zh else "no text line found (use --text-px)")
        if info["contrast"] is not None:
            c = info["contrast"]
            lines_txt.append((f"最低对比度 {c:.1f}:1" if zh else f"lowest contrast {c:.1f}:1") + ("" if c >= 4.5 else (" · 偏低" if zh else " · low") if c >= 3 else (" · 太低" if zh else " · too low")))
        ry = y + lab_h + fh + 10
        for t in lines_txt:
            V.text(d, (pad, ry), t, V.font(17), V.RED if ("太低" in t or "too low" in t) else V.INK); ry += 24
        x = pad + first_w + gap
        worst = []
        for key, plat, where_zh, where_en, sw, sh, rule, ov in slots:
            box, ar = crop_for(Wc, Hc, rule)
            if rule == "xhs" and ar > 1: sh = round(sw / ar)
            if rule == "xhs" and ar == 1.0: sh = sw
            tile = im.crop(tuple(int(round(v)) for v in box)).resize((sw, sh), Image.LANCZOS)
            img.paste(tile, (x, y + lab_h))
            ob = overlay(d, x, y + lab_h, sw, sh, ov)
            cropped = abs((box[2] - box[0]) - Wc) > 1 or abs((box[3] - box[1]) - Hc) > 1
            V.text(d, (x, y + 4), f"{PLATFORM[plat][0 if zh else 1]}", V.font(20, bold=True), V.INK)
            V.text(d, (x + sw, y + 9), f"{sw}×{sh}", V.font(14), V.MUTED, "ra")
            V.text(d, (x, y + 32), V.fit(d, where_zh if zh else where_en, V.font(14), sw), V.font(14), V.MUTED)
            s = sw / (box[2] - box[0])
            notes = []
            if hs:
                lo, hi = hs[0] * s, hs[-1] * s
                v = verdict(lo)
                col = {"ok": V.INK, "small": V.AMBER, "no": V.RED}[v]
                mark = {"ok": "○", "small": "△", "no": "×"}[v]   # marks every CJK font has
                notes.append((f"{mark} " + ("字高 " if zh else "") + f"{lo:.1f}" + (f"–{hi:.0f}" if hi - lo >= 1 else "") + " px", col))
                worst.append((lo, f"{PLATFORM[plat][1]} {where_en} ({sw}×{sh})"))
            if cropped:
                cut = [b for b in info["lines"] if b[0] < box[0] - 1 or b[2] > box[2] + 1 or b[1] < box[1] - 1 or b[3] > box[3] + 1]
                notes.append(((f"裁成 {rule if rule != 'xhs' else ('3:4' if ar < 1 else '4:3' if ar > 1 else '1:1')}" if zh else "cropped")
                              + ((f"，切到 {len(cut)} 行字" if zh else f", {len(cut)} text line(s) cut") if cut else ""), V.RED if cut else V.MUTED))
            if ob and info["lines"]:
                ox0, oy0, ox1, oy1 = [(v - (x if i % 2 == 0 else y + lab_h)) / s + (box[0] if i % 2 == 0 else box[1]) for i, v in enumerate(ob)]
                hit = [b for b in info["lines"] if min(b[2], ox1) - max(b[0], ox0) > 0 and min(b[3], oy1) - max(b[1], oy0) > 0.2 * (b[3] - b[1])]
                if hit: notes.append((f"UI 挡住 {len(hit)} 行字" if zh else f"UI covers {len(hit)} line(s)", V.RED))
            ny = y + lab_h + sh + 8
            for t, c in notes:
                for line in V.wrap(d, t, V.font(15), sw, 2):
                    V.text(d, (x, ny), line, V.font(15), c); ny += 20
            x += sw + gap
        if worst:
            lo, where = min(worst)
            report.append(f"{p.name}: smallest text {hs[0]:.0f} px → {lo:.1f} px on {where} ({verdict(lo)})"
                          + (f"; lowest contrast {info['contrast']:.1f}:1" if info["contrast"] else ""))
        else:
            report.append(f"{p.name}: no text line found; pass --text-px to check sizes")
    if a.out:
        out = Path(a.out)
    else:   # into the cover's project, else ./out/check/ here: never next to the image (it may sit in the repo's styles/)
        first = paths[0].resolve(); proj = next((q for q in first.parents if (q / "BRIEF.md").exists()), None)
        out = (proj or Path.cwd()) / "out" / "check" / f"cover-preview-{first.stem}.png"
    V.check_glyphs(["字"] if zh else [])
    V.save(img, out)
    print(f"cover-preview: {V.shown(out)}")
    for name in flat:
        print(f"  {name} has transparent pixels: flattened onto white, as a light feed page shows them")
    for r in report:
        print("  " + r)

if __name__ == "__main__":
    main()
