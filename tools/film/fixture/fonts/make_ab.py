"""Makes ab.ttf, the test font of tools/film/fixture/glyphs.html: "A" and "B" as plain boxes, a space, and an empty
.notdef. Nothing else, so any other character falls back to another font. Run: uv run --with fonttools python make_ab.py"""
from pathlib import Path
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen

def box(x0, y0, x1, y1, hole=None):
    """A filled rectangle, with a rectangular hole drawn the other way round."""
    p = TTGlyphPen(None)
    for pts in [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]] + ([[(hole[0], hole[1]), (hole[0], hole[3]), (hole[2], hole[3]), (hole[2], hole[1])]] if hole else []):
        p.moveTo(pts[0])
        for q in pts[1:]: p.lineTo(q)
        p.closePath()
    return p.glyph()

fb = FontBuilder(1000, isTTF=True)
fb.setupGlyphOrder([".notdef", "space", "A", "B"])
fb.setupCharacterMap({0x20: "space", 0x41: "A", 0x42: "B"})
empty = TTGlyphPen(None).glyph()
fb.setupGlyf({".notdef": empty, "space": empty, "A": box(60, 0, 540, 700), "B": box(60, 0, 540, 700, (180, 120, 420, 580))})
fb.setupHorizontalMetrics({".notdef": (600, 0), "space": (300, 0), "A": (600, 60), "B": (600, 60)})
fb.setupHorizontalHeader(ascent=800, descent=-200)
fb.setupNameTable({"familyName": "OVH Fixture AB", "styleName": "Regular", "psName": "OVHFixtureAB-Regular"})
fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
fb.setupPost()
fb.save(str(Path(__file__).with_name("ab.ttf")))
