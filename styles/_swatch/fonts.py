#!/usr/bin/env python3
"""Regenerate fonts.css: @font-face local() faces for the curated macOS system fonts that exist on THIS machine.

    python3 styles/_swatch/fonts.py            # writes styles/_swatch/fonts.css, prints a summary
    python3 styles/_swatch/fonts.py --list     # print "family<TAB>weights<TAB>where" and exit

Why: in `hyperframes render`, bare family names and generic families are not reliable (a `ui-monospace` stack
came out proportional in showcase 00). Every face is declared under its real family name with
`src: local("<PostScript name>"), local("<full name>")`, so a token like "Helvetica Neue" or "Songti SC" resolves
to the exact face and weight. Nothing is copied or redistributed: local() only reads fonts installed on the machine.
Needs fontconfig's `fc-list` (brew install fontconfig). The render-time probe in README.md shows which faces load.
"""
import re, subprocess, sys
from pathlib import Path

# Curated: families a style preset may plausibly want. Grouped for the README list.
CURATED = {
    "sans": ["Helvetica Neue", "Helvetica", "Arial", "Arial Black", "Arial Narrow", "Arial Rounded MT Bold", "Avenir",
             "Avenir Next", "Avenir Next Condensed", "Futura", "Gill Sans", "DIN Alternate", "DIN Condensed", "Optima",
             "Seravek", "Skia", "Trebuchet MS", "Verdana", "Tahoma", "Lucida Grande", "Geneva", "PT Sans",
             "PT Sans Narrow", "Impact"],
    "serif": ["Times New Roman", "Times", "Georgia", "Baskerville", "Big Caslon", "Bodoni 72", "Bodoni 72 Oldstyle",
              "Bodoni 72 Smallcaps", "Didot", "Hoefler Text", "Palatino", "Iowan Old Style", "Charter", "Cochin",
              "Athelas", "Superclarendon", "Rockwell", "American Typewriter", "PT Serif", "STIX Two Text", "Marion"],
    "mono": ["Menlo", "Monaco", "Courier New", "Courier", "Andale Mono", "PT Mono"],
    "display": ["Copperplate", "Phosphate", "Chalkduster", "Chalkboard SE", "Marker Felt", "Noteworthy", "Bradley Hand",
                "Snell Roundhand", "Zapfino", "SignPainter", "Savoye LET", "Trattatello", "Herculanum", "Luminari",
                "Party LET", "Academy Engraved LET", "Papyrus", "Brush Script MT", "Apple Chancery", "Comic Sans MS",
                "Krungthep", "Silom"],
    "zh": ["PingFang SC", "PingFang TC", "Hiragino Sans GB", "Heiti SC", "STHeiti", "Lantinghei SC", "Songti SC",
           "Songti TC", "STSong", "SimSong", "Kaiti SC", "Kaiti TC", "STKaiti", "STFangsong", "Libian SC", "Xingkai SC",
           "Yuanti SC", "Wawati SC", "HanziPen SC", "Hannotate SC", "Baoli SC", "LingWai SC", "Yuppy SC",
           "LXGW WenKai"],
    "ja": ["Hiragino Sans", "Hiragino Kaku Gothic ProN", "Hiragino Mincho ProN", "Hiragino Maru Gothic ProN",
           "Toppan Bunkyu Mincho", "Toppan Bunkyu Gothic", "Toppan Bunkyu Midashi Mincho",
           "Toppan Bunkyu Midashi Gothic", "YuMincho", "YuGothic", "Klee", "Tsukushi A Round Gothic", "BIZ UDMincho"],
    "ko": ["Apple SD Gothic Neo", "Nanum Myeongjo", "Nanum Gothic", "Nanum Brush Script", "Nanum Pen Script", "BM Jua"],
}

KEYWORD_WEIGHT = [  # the style name wins over fontconfig's number (variable fonts report 0; Kaiti SC Bold reports 80)
    (r"extra ?black|ultra ?black", 950), (r"black|heavy", 900), (r"extra ?bold|ultra ?bold", 800),
    (r"semi ?bold|demi ?bold|\bdemi\b", 600), (r"\bbold", 700), (r"medium", 500), (r"ultra ?light|extra ?light", 100),
    (r"thin|hairline", 200), (r"light", 300), (r"\bw3\b", 300), (r"\bw6\b", 600),
]
KEYWORD_WIDTH = [(r"ultra ?condensed|compressed", 50), (r"extra ?condensed", 63), (r"semi ?condensed", 87),
                 (r"condensed|narrow", 75), (r"extended|expanded", 125)]
# Faces fontconfig lists but Chrome's local() cannot open (found with `render.sh fontprobe`, macOS 15).
EXCLUDE_PS = {"STIXTwoTextItalic-MediumItalic", "STIXTwoTextItalic-SemiBoldItalic", "STIXTwoTextItalic-BoldItalic"}

def css_weight(fc_w: float, style: str) -> int:
    s = style.lower()
    for pat, w in KEYWORD_WEIGHT:
        if re.search(pat, s):
            return w
    table = [(0, 100), (40, 200), (50, 300), (55, 350), (75, 400), (80, 400), (100, 500), (180, 600), (200, 700),
             (205, 800), (210, 900), (215, 950)]
    if fc_w == 0:
        return 400   # a variable font's unnamed default instance
    return min(table, key=lambda p: abs(p[0] - fc_w))[1]

def css_stretch(fc_width: float, style: str) -> int:
    if int(fc_width) != 100:
        return int(fc_width)
    for pat, w in KEYWORD_WIDTH:
        if re.search(pat, style.lower()):
            return w
    return 100

def faces():
    fmt = "%{family[0]}|%{style[0]}|%{weight}|%{slant}|%{width}|%{postscriptname}|%{fullname[0]}|%{file}\n"
    out = subprocess.run(["fc-list", "--format", fmt], capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        p = line.split("|")
        if len(p) != 8:
            continue
        fam, style, w, slant, width, ps, full, path = p
        try:
            yield dict(family=fam, style=style, weight=css_weight(float(w), style), italic=float(slant) >= 100,
                       stretch=css_stretch(float(width), style), ps=ps, full=full, path=path)
        except ValueError:
            continue

def where(path: str) -> str:
    if "/AssetsV2/" in path: return "macOS on-demand asset (downloaded)"
    if path.startswith(str(Path.home())): return "user-installed (~/Library/Fonts, not portable)"
    return "macOS system"

def main():
    wanted = {f: g for g, fams in CURATED.items() for f in fams}
    seen, rows = set(), []
    for f in faces():
        if f["family"] not in wanted or not f["ps"] or f["ps"] in EXCLUDE_PS:
            continue
        key = (f["family"], f["weight"], f["italic"], f["stretch"])
        if key in seen:
            continue
        seen.add(key); rows.append(f)
    order = {f: i for i, f in enumerate(wanted)}
    rows.sort(key=lambda r: (order[r["family"]], r["stretch"], r["italic"], r["weight"]))
    if "--list" in sys.argv:
        fams = {}
        for r in rows:
            fams.setdefault(r["family"], []).append(r)
        for fam, rs in fams.items():
            ws = sorted({r["weight"] for r in rs})
            print(f"{wanted[fam]}\t{fam}\t{','.join(map(str, ws))}\t{where(rs[0]['path'])}")
        return
    css = ["/* GENERATED by fonts.py from fc-list on this machine. local() only: nothing is copied or redistributed. */",
           "/* Every face keeps its real family name, so a tokens.json stack like [\"Songti SC\", \"STSong\"] resolves. */"]
    count = {}
    for r in rows:
        count[r["family"]] = count.get(r["family"], 0) + 1
    for r in rows:
        src = [f'local("{r["ps"]}")']
        if r["full"] and r["full"] != r["ps"]:
            src.append(f'local("{r["full"]}")')
        stretch = "" if r["stretch"] == 100 else f' font-stretch: {r["stretch"]}%;'
        weight = "1 1000" if count[r["family"]] == 1 else r["weight"]   # single-face family: never synthesise bold
        css.append(f'@font-face {{ font-family: "{r["family"]}"; src: {", ".join(src)}; font-weight: {weight};'
                   f' font-style: {"italic" if r["italic"] else "normal"};{stretch} }}')
    dst = Path(__file__).with_name("fonts.css")
    dst.write_text("\n".join(css) + "\n")
    missing = [f for f in wanted if f not in {r["family"] for r in rows}]
    print(f"wrote {dst} ({len(rows)} faces, {len({r['family'] for r in rows})} families)")
    if missing:
        print("not installed here:", ", ".join(missing))

if __name__ == "__main__":
    main()
