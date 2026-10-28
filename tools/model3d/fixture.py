"""The test model, written on the spot (nothing downloaded, no binary in the repo): a column of two stacked cubes, 0.5 m
square and 2 m tall, skinned to two bones (Root at its foot, Tip at its middle), a 4x4 checker texture, and two clips:
"bend" (Tip turns 45 degrees about Z and back, 1 s) and "lift" (Root rises 0.5 m and comes down, 2 s). bin/vh model3d
check and the Three.js layer's test page (tools/ci.sh) both read it. Stdlib only.

usage: python3 tools/model3d/fixture.py <out.glb> [--scale K] [--json]
       python3 tools/model3d/fixture.py --film <canvas-film project made with --three>
  --scale K   every length times K (100: a model made in centimetres and read as metres)
  --json      print what it wrote: {"path", "bytes", "triangles", "vertices", "joints", "animations": {name: seconds}}
  --film P    the model as P/assets/models/box.glb and the layer's test film as P/src/50-shots.js (FILM below): 160 x 90,
              silent, 3 s. S01 holds the camera while the column bends in a loop, so t = 0.25 and t = 1.25 (clip time 0.25
              both) are the same picture and t = 0.5 is not; from 0.4 s to 1 s its pose() moves the column 0.5 m right,
              which a frame drawn after 0.5 keeps only if the layer does not put the world back each frame. S02 lifts it
              once from 1.5 s while the camera moves. Both draw a white square at (4, 4), 12 px, over the 3D's opaque
              background (#203040)
build(scale) → (the glTF JSON, the BIN chunk's bytes), for a test that changes a part before writing it (glb.write_glb).
"""
import json, math, struct, sys, zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import glb   # noqa: E402

W, H = 0.25, 2.0   # half the width, the height (metres)


def rgbe(w, h, pixel):
    """A w x h Radiance .hdr (RGBE, flat scanlines; three's HDRLoader and Blender read it); pixel(x, y) → (r, g, b) floats.
    For a test sky: synthetic, nobody's photograph."""
    def enc(r, g, b):
        v = max(r, g, b)
        if v < 1e-32:
            return bytes(4)
        m, e = math.frexp(v)
        k = m * 256 / v
        return bytes((int(r * k), int(g * k), int(b * k), e + 128))
    head = f"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n-Y {h} +X {w}\n".encode()
    return head + b"".join(enc(*pixel(x, y)) for y in range(h) for x in range(w))


def sky(w, h):
    """The test sky as pixel(x, y) for rgbe(w, h, …): a blue gradient down to a warm horizon, a dark ground, a bright sun to
    one side. Three's PMREM wants a map 64 px wide or more (a smaller one lights and blurs to black): 128 x 64 does."""
    def pixel(x, y):
        v = y / (h - 1)
        r, g, b = (0.25 + 0.6 * v, 0.35 + 0.4 * v, 0.9 - 0.4 * v) if v < 0.5 else (0.12, 0.1, 0.08)
        near = abs(x - w // 4) <= w // 64 and abs(y - h // 6) <= h // 32
        return (r + 6.0, g + 5.0, b + 3.5) if near else (r, g, b)
    return pixel


def png(w, h, pixel):
    """A w x h RGB PNG; pixel(x, y) → (r, g, b). Stored without compression, so the bytes are the same on every zlib."""
    raw = b"".join(b"\0" + bytes(c for x in range(w) for c in pixel(x, y)) for y in range(h))
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)   # noqa: E731
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 0)) + chunk(b"IEND", b""))


def build(scale=1.0):
    pos, nor, uv, jnt, wgt, idx = [], [], [], [], [], []
    rows = [(0, (0, 0), (1, 0)), (1, (0, 1), (0.5, 0.5)), (2, (1, 0), (1, 0))]   # y, joints, weights of each ring
    # four sides, each two quads high; right × up = the outward normal, so the triangles wind counter-clockwise seen from outside
    for n, right in (((1, 0, 0), (0, 0, -1)), ((-1, 0, 0), (0, 0, 1)), ((0, 0, 1), (1, 0, 0)), ((0, 0, -1), (-1, 0, 0))):
        base = len(pos)
        for y, j, w in rows:
            for side in (-1, 1):   # left, then right, seen from outside
                pos.append((scale * W * (n[0] + side * right[0]), scale * y, scale * W * (n[2] + side * right[2])))
                nor.append(n); uv.append(((side + 1) / 2, y / 2)); jnt.append(j + (0, 0)); wgt.append(w + (0.0, 0.0))
        for r in (0, 2):
            a, b, c, d = base + r, base + r + 1, base + r + 3, base + r + 2
            idx += [a, b, c, a, c, d]
    # the caps: top (+Y, the Tip's) and bottom (-Y, the Root's)
    for y, n, jn, zs in ((H, (0, 1, 0), 1, (1, 1, -1, -1)), (0.0, (0, -1, 0), 0, (-1, -1, 1, 1))):
        base = len(pos)
        for x, z in zip((-1, 1, 1, -1), zs):
            pos.append((scale * W * x, scale * y, scale * W * z)); nor.append(n); uv.append(((x + 1) / 2, (z + 1) / 2))
            jnt.append((jn, 0, 0, 0)); wgt.append((1.0, 0.0, 0.0, 0.0))
        idx += [base, base + 1, base + 2, base, base + 2, base + 3]

    blob, views, accessors = bytearray(), [], []

    def add(data, target=None):
        while len(blob) % 4:
            blob.append(0)
        views.append({"buffer": 0, "byteOffset": len(blob), "byteLength": len(data), **({"target": target} if target else {})})
        blob.extend(data)
        return len(views) - 1

    def acc(values, comp, typ, target=None, minmax=False):
        fmt = {5126: "f", 5121: "B", 5123: "H"}[comp]
        flat = [x for v in values for x in (v if isinstance(v, tuple) else (v,))]
        a = {"bufferView": add(struct.pack(f"<{len(flat)}{fmt}", *flat), target), "componentType": comp, "count": len(values), "type": typ}
        if minmax:
            cols = list(zip(*[v if isinstance(v, tuple) else (v,) for v in values]))
            a["min"], a["max"] = [min(c) for c in cols], [max(c) for c in cols]
        accessors.append(a)
        return len(accessors) - 1

    ap = acc(pos, 5126, "VEC3", 34962, minmax=True)
    an, at, aj, aw = acc(nor, 5126, "VEC3", 34962), acc(uv, 5126, "VEC2", 34962), acc(jnt, 5121, "VEC4", 34962), acc(wgt, 5126, "VEC4", 34962)
    ai = acc(idx, 5123, "SCALAR", 34963)
    ibm = [glb.IDENTITY, glb.IDENTITY[:13] + (-scale * 1.0,) + glb.IDENTITY[14:]]   # the joints at (0, 0, 0) and (0, 1, 0)
    aibm = acc(ibm, 5126, "MAT4")
    s45 = math.sin(math.radians(22.5)), math.cos(math.radians(22.5))
    bend_t, bend_q = acc([0.0, 0.5, 1.0], 5126, "SCALAR", minmax=True), acc([(0.0, 0.0, 0.0, 1.0), (0.0, 0.0, s45[0], s45[1]), (0.0, 0.0, 0.0, 1.0)], 5126, "VEC4")
    lift_t, lift_p = acc([0.0, 1.0, 2.0], 5126, "SCALAR", minmax=True), acc([(0.0, 0.0, 0.0), (0.0, 0.5 * scale, 0.0), (0.0, 0.0, 0.0)], 5126, "VEC3")
    checker = png(4, 4, lambda x, y: (224, 102, 46) if (x + y) % 2 else (242, 232, 213))
    image_view = add(checker)

    gltf = {
        "asset": {"version": "2.0", "generator": "OpenVideoHarness tools/model3d/fixture.py"},
        "scene": 0, "scenes": [{"name": "Scene", "nodes": [3]}],
        "nodes": [
            {"name": "Column", "mesh": 0, "skin": 0},
            {"name": "Root", "children": [2]},
            {"name": "Tip", "translation": [0.0, 1.0 * scale, 0.0]},
            {"name": "Rig", "children": [0, 1]},
        ],
        "meshes": [{"name": "Column", "primitives": [{"attributes": {"POSITION": ap, "NORMAL": an, "TEXCOORD_0": at, "JOINTS_0": aj, "WEIGHTS_0": aw},
                                                      "indices": ai, "material": 0, "mode": 4}]}],
        "skins": [{"name": "Rig", "joints": [1, 2], "inverseBindMatrices": aibm, "skeleton": 1}],
        "materials": [{"name": "Paint", "pbrMetallicRoughness": {"baseColorFactor": [1, 1, 1, 1], "baseColorTexture": {"index": 0},
                                                                 "metallicFactor": 0.0, "roughnessFactor": 0.6}}],
        "samplers": [{"magFilter": 9728, "minFilter": 9728, "wrapS": 10497, "wrapT": 10497}],
        "images": [{"name": "checker", "bufferView": image_view, "mimeType": "image/png"}],
        "textures": [{"sampler": 0, "source": 0}],
        "animations": [
            {"name": "bend", "channels": [{"sampler": 0, "target": {"node": 2, "path": "rotation"}}],
             "samplers": [{"input": bend_t, "output": bend_q, "interpolation": "LINEAR"}]},
            {"name": "lift", "channels": [{"sampler": 0, "target": {"node": 1, "path": "translation"}}],
             "samplers": [{"input": lift_t, "output": lift_p, "interpolation": "LINEAR"}]},
        ],
        "accessors": accessors, "bufferViews": views, "buffers": [{"byteLength": len(blob) + (-len(blob) % 4)}],
    }
    return gltf, bytes(blob)


FILM = """// the Three.js layer's test film, written by tools/model3d/fixture.py --film (its docstring says what each frame shows)
Object.assign(FILM, {
  width: 160, height: 90, timeline: false, duration: 3, grain: 0, fadeOut: 0, images: {},
  three: {
    models: { box: "assets/models/box.glb" },
    camera: { pos: [0, 1.2, 4.2], at: [0, 1, 0], fov: 40 },
    lights: [{ type: "hemi", sky: "#ffffff", ground: "#3a3530", intensity: 1.4 }, { type: "sun", intensity: 2.2, pos: [2, 4, 3] }],
    background: "#203040",
  },
});
const square = () => { X.fillStyle = "#ffffff"; X.fillRect(4, 4, 12, 12); };
const SHOTS = [
  { id: "S01", at: 0, three: { play: { box: { clip: "bend", loop: true } },
    pose(t, s, { models }) { if (t > 0.4 && t < 1) models.box.root.position.x = 0.5; } }, draw: square },
  { id: "S02", at: 1.5, three: { play: { box: { clip: "lift", at: 1.5 } }, cam: { from: { pos: [0, 1.5, 4.6] }, to: { pos: [1.2, 1.4, 3.8], lens: 40 } } },
    draw: square },
];
"""


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__.strip(), file=sys.stdout if argv else sys.stderr)
        return 0 if argv else 2
    if argv[0] == "--film":
        if len(argv) != 2 or not (Path(argv[1]) / "three" / "layer.js").is_file():
            print("fixture.py: --film <a canvas-film project made with --three>", file=sys.stderr); return 2
        p = Path(argv[1])
        (p / "assets" / "models").mkdir(parents=True, exist_ok=True)
        glb.write_glb(p / "assets" / "models" / "box.glb", *build())
        (p / "src" / "50-shots.js").write_text(FILM, encoding="utf-8")
        return 0
    out, scale, as_json, rest = None, 1.0, False, list(argv)
    while rest:
        a = rest.pop(0)
        if a == "--scale" and rest:
            try:
                scale = float(rest.pop(0))
            except ValueError:
                print("fixture.py: --scale takes a number", file=sys.stderr); return 2
        elif a == "--json":
            as_json = True
        elif a.startswith("-") or out:
            print(f"fixture.py: {a}? (-h for the usage)", file=sys.stderr); return 2
        else:
            out = a
    if not out or not (scale > 0):
        print("fixture.py: an output path, and a --scale above 0", file=sys.stderr); return 2
    gltf, blob = build(scale)
    n = glb.write_glb(out, gltf, blob)
    if as_json:
        print(json.dumps({"path": out, "bytes": n, "triangles": 20, "vertices": 32, "joints": 2, "animations": {"bend": 1.0, "lift": 2.0}}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
