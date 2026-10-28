"""A glTF 2.0 model read with the standard library alone: a .glb (its JSON chunk and BIN chunk), or a .gltf with its
buffers and images beside it or in data: URIs. Accessors come out as numbers, nodes as world matrices, images as
their format and size read from their own headers. bin/vh model3d check (tools/model3d/model3d.py) reports from it;
tools/model3d/fixture.py writes the test model with its write_glb().

Model(path) → .json (the glTF), .kind ("glb" or "gltf"), .bytes (the file's size), .accessor(i) → [tuple…],
.buffer(i), .image(i) → (bytes or None, mime, where), .world() → {node: matrix} for the default scene, .roots().
Nothing is decoded that the report does not need: no meshes are built, no images decompressed.
"""
import base64, json, math, struct, urllib.parse
from pathlib import Path

MAGIC, JSON_CHUNK, BIN_CHUNK = 0x46546C67, 0x4E4F534A, 0x004E4942   # "glTF", "JSON", "BIN\0"
COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NORM = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}   # a normalized integer's range (signed: max(c / n, -1))
COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)   # column-major, as glTF writes it


class GltfError(Exception):
    """The file is not a glTF 2.0 model this reader can take, or a part of it points nowhere."""


class Model:
    def __init__(self, path):
        self.path = Path(path)
        data = self.path.read_bytes()
        self.bytes, self.bin, self._buffers = len(data), None, {}
        if data[:4] == b"glTF":
            self.kind = "glb"
            if len(data) < 20:
                raise GltfError("a GLB header is 12 bytes and its JSON chunk follows: this file is shorter")
            magic, version, length = struct.unpack_from("<III", data, 0)
            if version != 2:
                raise GltfError(f"GLB version {version}: glTF 2.0 files are version 2 (a glTF 1.0 file needs converting)")
            if length != len(data):
                raise GltfError(f"the GLB header says {length} bytes, the file has {len(data)} (cut short, or something appended)")
            chunks, at = [], 12
            while at + 8 <= len(data):
                n, kind = struct.unpack_from("<II", data, at)
                if at + 8 + n > len(data):
                    raise GltfError(f"a chunk at byte {at} says {n} bytes, past the end of the file")
                chunks.append((kind, data[at + 8:at + 8 + n]))
                at += 8 + n
            if not chunks or chunks[0][0] != JSON_CHUNK:
                raise GltfError("the first chunk of a GLB must be its JSON")
            text = chunks[0][1]
            bins = [c for k, c in chunks[1:] if k == BIN_CHUNK]
            self.bin = bins[0] if bins else None
        else:
            self.kind = "gltf"
            text = data
        try:
            self.json = json.loads(text.decode("utf-8").rstrip(" \t\r\n\0"))
        except (UnicodeDecodeError, ValueError) as e:
            raise GltfError(f"its JSON does not parse: {e}") from None
        if not isinstance(self.json, dict):
            raise GltfError("its JSON is not an object")
        ver = str((self.json.get("asset") or {}).get("version", ""))
        if not ver.startswith("2."):
            raise GltfError(f"asset.version is {ver or 'missing'}: this reads glTF 2.0")

    # ---- what the JSON points at ----
    def list(self, key):
        v = self.json.get(key)
        return v if isinstance(v, list) else []

    def get(self, key, i, what):
        items = self.list(key)
        if not isinstance(i, int) or not 0 <= i < len(items):
            raise GltfError(f"{what} points at {key}[{i}], and there are {len(items)}")
        return items[i]

    def _uri(self, uri, what):
        """The bytes of a URI: a data: URI, or a file beside the model (percent-encoding undone)."""
        if uri.startswith("data:"):
            head, _, body = uri.partition(",")
            return base64.b64decode(body) if head.endswith(";base64") else urllib.parse.unquote_to_bytes(body)
        f = self.path.parent / urllib.parse.unquote(uri)
        try:
            return f.read_bytes()
        except OSError:
            raise GltfError(f"{what}: {uri} is not beside the model ({f})") from None

    def buffer(self, i):
        if i not in self._buffers:
            b = self.get("buffers", i, "a bufferView")
            if "uri" in b:
                data = self._uri(b["uri"], f"buffers[{i}]")
            elif i == 0 and self.bin is not None:
                data = self.bin
            else:
                raise GltfError(f"buffers[{i}] has no uri and is not the GLB's BIN chunk")
            if len(data) < b.get("byteLength", 0):
                raise GltfError(f"buffers[{i}] says {b.get('byteLength')} bytes, has {len(data)}")
            self._buffers[i] = data
        return self._buffers[i]

    def view(self, i):
        """(bytes, stride or None) of a bufferView."""
        v = self.get("bufferViews", i, "an accessor or an image")
        data, at, n = self.buffer(v.get("buffer", -1)), v.get("byteOffset", 0), v.get("byteLength", 0)
        if at + n > len(data):
            raise GltfError(f"bufferViews[{i}] runs {at + n - len(data)} bytes past the end of its buffer")
        return data[at:at + n], v.get("byteStride")

    def accessor(self, i):
        """An accessor's elements as tuples of numbers (normalized integers as floats in 0..1 or -1..1), sparse values in."""
        a = self.get("accessors", i, "a mesh, a skin or an animation")
        comp, typ, count = a.get("componentType"), a.get("type"), a.get("count", 0)
        if comp not in COMPONENT or typ not in COUNT:
            raise GltfError(f"accessors[{i}]: component type {comp} or type {typ} is not glTF's")
        fmt, size = COMPONENT[comp]
        n = COUNT[typ]
        # a matrix of 1- or 2-byte components starts each column on a 4-byte boundary
        rows = {"MAT2": 2, "MAT3": 3, "MAT4": 4}.get(typ)
        col = -(-(rows * size) // 4) * 4 if rows and size < 4 else None
        elem = col * rows if col else n * size
        out = []
        if "bufferView" in a:
            data, stride = self.view(a["bufferView"])
            stride, base = stride or elem, a.get("byteOffset", 0)
            if count and base + stride * (count - 1) + elem > len(data):
                raise GltfError(f"accessors[{i}]: {count} elements run past the end of bufferViews[{a['bufferView']}]")
            for k in range(count):
                at = base + k * stride
                if col:
                    out.append(tuple(x for c in range(rows) for x in struct.unpack_from(f"<{rows}{fmt}", data, at + c * col)))
                else:
                    out.append(struct.unpack_from(f"<{n}{fmt}", data, at))
        else:
            out = [(0,) * n] * count
        sp = a.get("sparse")
        if sp:
            idx = _plain(self, sp["indices"], sp["count"], 1)
            val = _plain(self, {**sp["values"], "componentType": comp}, sp["count"], n)
            out = list(out)
            for j, v in zip(idx, val):
                if 0 <= j[0] < count:
                    out[j[0]] = v
        if a.get("normalized") and comp in NORM:
            m = NORM[comp]
            out = [tuple(max(x / m, -1.0) for x in e) for e in out]
        return out

    def image(self, i):
        """(its bytes or None, its MIME type, where it is: "embedded", "data URI", the file name)."""
        im = self.get("images", i, "a texture")
        if "bufferView" in im:
            return self.view(im["bufferView"])[0], im.get("mimeType", ""), "embedded"
        uri = im.get("uri", "")
        if not uri:
            return None, im.get("mimeType", ""), "nowhere"
        try:
            data = self._uri(uri, f"images[{i}]")
        except GltfError:
            return None, im.get("mimeType", ""), urllib.parse.unquote(uri)
        mime = im.get("mimeType") or ("image/png" if uri.lower().endswith(".png") else "image/jpeg" if uri.lower().endswith((".jpg", ".jpeg")) else "")
        return data, mime, "data URI" if uri.startswith("data:") else urllib.parse.unquote(uri)

    # ---- the scene graph ----
    def roots(self):
        """The default scene's root nodes; with no scene, every node that is no other node's child."""
        scenes = self.list("scenes")
        if scenes:
            s = self.json.get("scene", 0)
            return list((scenes[s] if isinstance(s, int) and 0 <= s < len(scenes) else scenes[0]).get("nodes", []))
        kids = {c for n in self.list("nodes") for c in n.get("children", [])}
        return [i for i in range(len(self.list("nodes"))) if i not in kids]

    def world(self):
        """{node index: its world matrix (column-major tuple)} for every node of the default scene."""
        out, nodes = {}, self.list("nodes")
        stack = [(r, IDENTITY) for r in reversed(self.roots())]
        while stack:
            i, parent = stack.pop()
            if i in out or not 0 <= i < len(nodes):
                continue   # a node reached twice (a malformed graph) is taken once
            m = mul(parent, local(nodes[i]))
            out[i] = m
            stack += [(c, m) for c in reversed(nodes[i].get("children", []))]
        return out


def _plain(model, ref, count, n):
    """A sparse block's indices or values: count elements of n components from a bufferView, tightly packed."""
    fmt, size = COMPONENT[ref["componentType"]]
    data, _ = model.view(ref["bufferView"])
    at = ref.get("byteOffset", 0)
    return [struct.unpack_from(f"<{n}{fmt}", data, at + k * n * size) for k in range(count)]


# ---- 4x4 matrices, column-major tuples as glTF writes them ----
def mul(a, b):
    return tuple(sum(a[r + 4 * k] * b[k + 4 * c] for k in range(4)) for c in range(4) for r in range(4))


def local(node):
    """A node's own matrix: its matrix, or translation × rotation × scale."""
    if "matrix" in node:
        return tuple(float(x) for x in node["matrix"])
    tx, ty, tz = node.get("translation", (0, 0, 0))
    x, y, z, w = node.get("rotation", (0, 0, 0, 1))
    sx, sy, sz = node.get("scale", (1, 1, 1))
    r = (1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w),
         2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w),
         2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y))
    return (r[0] * sx, r[1] * sx, r[2] * sx, 0.0, r[3] * sy, r[4] * sy, r[5] * sy, 0.0,
            r[6] * sz, r[7] * sz, r[8] * sz, 0.0, float(tx), float(ty), float(tz), 1.0)


def apply(m, p):
    x, y, z = p
    return (m[0] * x + m[4] * y + m[8] * z + m[12], m[1] * x + m[5] * y + m[9] * z + m[13], m[2] * x + m[6] * y + m[10] * z + m[14])


def near_identity(m, eps=1e-4):
    return all(abs(a - b) <= eps for a, b in zip(m, IDENTITY))


def corners(lo, hi):
    return [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]


# ---- images: the format and the size from the first bytes ----
def image_size(data):
    """(format, width, height) from an image's header: png, jpeg, webp, ktx2, avif; (format or "", 0, 0) otherwise."""
    if not data:
        return "", 0, 0
    if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24:
        w, h = struct.unpack_from(">II", data, 16)
        return "png", w, h
    if data[:2] == b"\xff\xd8":
        at = 2
        while at + 9 < len(data):
            if data[at] != 0xFF:
                at += 1
                continue
            marker = data[at + 1]
            if marker == 0xFF:   # a fill byte before the marker
                at += 1
                continue
            if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
                at += 2
                continue
            n = struct.unpack_from(">H", data, at + 2)[0]
            if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
                h, w = struct.unpack_from(">HH", data, at + 5)
                return "jpeg", w, h
            at += 2 + n
        return "jpeg", 0, 0
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP" and len(data) >= 30:
        kind = data[12:16]
        if kind == b"VP8 ":
            w, h = struct.unpack_from("<HH", data, 26)
            return "webp", w & 0x3FFF, h & 0x3FFF
        if kind == b"VP8L":
            b = data[21:25]
            return "webp", 1 + (((b[1] & 0x3F) << 8) | b[0]), 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
        if kind == b"VP8X":
            return "webp", 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
        return "webp", 0, 0
    if data[:12] == b"\xabKTX 20\xbb\r\n\x1a\n" and len(data) >= 28:
        w, h = struct.unpack_from("<II", data, 20)
        return "ktx2", w, h
    if data[4:8] == b"ftyp" and b"avif" in data[8:32]:
        at = data.find(b"ispe")
        if at > 0 and at + 16 <= len(data):
            w, h = struct.unpack_from(">II", data, at + 8)
            return "avif", w, h
        return "avif", 0, 0
    return "", 0, 0


# ---- writing one (the test model, tools/model3d/fixture.py) ----
def write_glb(path, gltf, binary):
    """A GLB of the JSON and the BIN chunk: each chunk padded to 4 bytes (the JSON with spaces, the BIN with zeros)."""
    js = json.dumps(gltf, separators=(",", ":")).encode("utf-8")
    js += b" " * (-len(js) % 4)
    binary = bytes(binary) + b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(js) + (8 + len(binary) if binary else 0)
    out = struct.pack("<III", MAGIC, 2, total) + struct.pack("<II", len(js), JSON_CHUNK) + js
    if binary:
        out += struct.pack("<II", len(binary), BIN_CHUNK) + binary
    Path(path).write_bytes(out)
    return total


def finite(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
