"""A glTF 2.0 model read with the standard library alone: a .glb (its JSON chunk and BIN chunk), or a .gltf with its
buffers and images beside it or in data: URIs. Accessors come out as numbers, nodes as world matrices, images as
their format and size read from their own headers. bin/vh model3d check (tools/model3d/model3d.py) reports from it;
tools/model3d/fixture.py writes the test model with its write_glb().

Model(path) → .json (the glTF), .kind ("glb" or "gltf"), .bytes (the file's size), .notes ([(kind, message)]: what
reads but is off), .problems() → [line…] (what points outside the file), .accessor(i) → [tuple…], .buffer(i),
.image(i) → (bytes or None, mime, where), .world() → {node: matrix} for the default scene, .roots().
Nothing is decoded that the report does not need: no meshes are built, no images decompressed.
"""
import base64, json, math, struct, urllib.parse
from pathlib import Path

MAGIC, JSON_CHUNK, BIN_CHUNK = 0x46546C67, 0x4E4F534A, 0x004E4942   # "glTF", "JSON", "BIN\0"
COMPONENT = {5120: ("b", 1), 5121: ("B", 1), 5122: ("h", 2), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
NORM = {5120: 127.0, 5121: 255.0, 5122: 32767.0, 5123: 65535.0}   # a normalized integer's range (signed: max(c / n, -1))
COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT2": 4, "MAT3": 9, "MAT4": 16}
IDENTITY = (1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0)   # column-major, as glTF writes it
LISTS = ("accessors", "animations", "buffers", "bufferViews", "cameras", "images", "materials", "meshes", "nodes", "samplers",
         "scenes", "skins", "textures")
ZEROS = 1 << 24   # an accessor with no bufferView is that many zeros: more than any model holds is a broken count, not data


class GltfError(Exception):
    """The file is not a glTF 2.0 model this reader can take, or a part of it points nowhere."""


def kind_of(v):
    return {dict: "an object", list: "a list", str: "a string", bool: "true or false", type(None): "null"}.get(type(v), "a number")


def whole(v, lo=0):
    return isinstance(v, int) and not isinstance(v, bool) and v >= lo


def short(v):
    return json.dumps(v)[:60]


class Model:
    def __init__(self, path):
        self.path = Path(path)
        data = self.path.read_bytes()
        self.bytes, self.bin, self._buffers, self.notes = len(data), None, {}, []
        if data[:4] == b"glTF":
            self.kind = "glb"
            if len(data) < 20:
                raise GltfError("a GLB header is 12 bytes and its JSON chunk follows: this file is shorter")
            magic, version, length = struct.unpack_from("<III", data, 0)
            if version != 2:
                raise GltfError(f"GLB version {version}: glTF 2.0 files are version 2 (a glTF 1.0 file needs converting)")
            if length > len(data):
                raise GltfError(f"the GLB header says {length} bytes, the file has {len(data)}: it was cut short")
            if length < len(data):   # three reads up to the header's length, so the file loads
                self.notes.append(("trailing", f"{len(data) - length:,} bytes after the {length:,} the GLB header gives: three reads up to its length and drops them"))
                data = data[:length]
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
        asset = self.json.get("asset")
        if not isinstance(asset, dict):
            raise GltfError(f"asset is {kind_of(asset) if 'asset' in self.json else 'missing'}: a glTF 2.0 file says {{\"asset\": {{\"version\": \"2.0\"}}}}")
        ver = str(asset.get("version", ""))
        if not ver.startswith("2."):
            raise GltfError(f"asset.version is {ver or 'missing'}: this reads glTF 2.0")

    def problems(self):
        """What points outside the file, or is not the kind of thing glTF says, a line each (the first 20): the top-level
        lists and their entries, each reference from one to another, the nodes as trees (no node its own ancestor, none
        with two parents), each buffer's bytes, each bufferView inside its buffer, each accessor's type, component type
        and count and its elements inside its bufferView, a sparse accessor's blocks inside theirs and its indices below
        its count, in increasing order. One pass over the JSON; of the data, only sparse indices are read. It is not the
        whole glTF 2.0 spec: Khronos's glTF-Validator checks a file against that."""
        J, out = self.json, []
        for k in LISTS:
            v = J.get(k, [])
            if not isinstance(v, list):
                out.append(f"{k} is {kind_of(v)}: glTF's {k} is a list of objects")
                continue
            odd = [i for i, x in enumerate(v) if not isinstance(x, dict)]
            if odd:
                out.append(f"{k}[{odd[0]}] is {kind_of(v[odd[0]])}, not an object" + (f" (and {len(odd) - 1} more of the {k})" if len(odd) > 1 else ""))
        for k in ("extensionsUsed", "extensionsRequired"):
            v = J.get(k, [])
            if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
                out.append(f"{k} is a list of extension names: {short(v)}")
        if out:
            return out   # what follows walks these lists
        many = {k: len(self.list(k)) for k in LISTS}

        def ref(v, k, where):
            if whole(v) and v < many[k]:
                return True
            out.append(f"{where} points at {k}[{short(v)}], and there are {many[k]}")
            return False

        def items(o, key, where, objects=False):
            v = o.get(key, [])
            if not isinstance(v, list):
                out.append(f"{where} is {kind_of(v)}: a list")
                return []
            if objects and not all(isinstance(x, dict) for x in v):
                out.append(f"{where} is a list of objects: {short(v)}")
                return []
            return v

        if "scene" in J:
            ref(J["scene"], "scenes", "scene")
        for i, s in enumerate(self.list("scenes")):
            for r in items(s, "nodes", f"scenes[{i}].nodes"):
                ref(r, "nodes", f"scenes[{i}].nodes")
        nodes, parent = self.list("nodes"), {}
        for i, n in enumerate(nodes):
            for c in items(n, "children", f"nodes[{i}].children"):
                if not ref(c, "nodes", f"nodes[{i}].children"):
                    continue
                if c in parent and parent[c] != i:
                    out.append(f"nodes[{c}] is a child of nodes[{parent[c]}] and of nodes[{i}]: glTF's nodes are trees, one parent each")
                parent.setdefault(c, i)
        loops = []
        for i in range(len(nodes)):   # up from each node: one that comes back to itself is in a loop
            path, x = [], i
            while x in parent and x not in path:
                path.append(x)
                x = parent[x]
            if x in path and set(path[path.index(x):]) not in loops:
                loops.append(set(path[path.index(x):]))
                ring = list(reversed(path[path.index(x):]))
                out.append("nodes " + " → ".join(f"{k} ({nodes[k].get('name', 'unnamed')})" for k in ring + ring[:1])
                           + ": each the child of the one before, a loop; glTF's nodes are trees, and three's loader goes round it without end")
            for k, lst in (("mesh", "meshes"), ("skin", "skins"), ("camera", "cameras")):
                if k in n:
                    ref(n[k], lst, f"nodes[{i}].{k}")
            for k, want in (("matrix", 16), ("translation", 3), ("rotation", 4), ("scale", 3)):
                if k in n and not (isinstance(n[k], list) and len(n[k]) == want and all(finite(x) for x in n[k])):
                    out.append(f"nodes[{i}].{k} is {want} numbers: {short(n[k])}")
        for i, me in enumerate(self.list("meshes")):
            for j, p in enumerate(items(me, "primitives", f"meshes[{i}].primitives", True)):
                w, at = f"meshes[{i}].primitives[{j}]", p.get("attributes", {})
                for name, a in (at.items() if isinstance(at, dict) else ()):
                    ref(a, "accessors", f"{w}.attributes.{name}")
                if not isinstance(at, dict):
                    out.append(f"{w}.attributes is {kind_of(at)}: an object, attribute → accessor")
                for k, lst in (("indices", "accessors"), ("material", "materials")):
                    if k in p:
                        ref(p[k], lst, f"{w}.{k}")
                if "mode" in p and not (whole(p["mode"]) and p["mode"] <= 6):
                    out.append(f"{w}.mode is 0 to 6 (4: triangles), not {short(p['mode'])}")
                for k, tg in enumerate(items(p, "targets", f"{w}.targets", True)):
                    for name, a in tg.items():
                        ref(a, "accessors", f"{w}.targets[{k}].{name}")
        for i, s in enumerate(self.list("skins")):
            joints = items(s, "joints", f"skins[{i}].joints")
            for j in joints:
                ref(j, "nodes", f"skins[{i}].joints")
            if "skeleton" in s:
                ref(s["skeleton"], "nodes", f"skins[{i}].skeleton")
            if "inverseBindMatrices" in s and ref(s["inverseBindMatrices"], "accessors", f"skins[{i}].inverseBindMatrices"):
                a = self.list("accessors")[s["inverseBindMatrices"]]
                if a.get("type") != "MAT4" or not whole(a.get("count"), len(joints)):
                    out.append(f"skins[{i}].inverseBindMatrices is accessors[{s['inverseBindMatrices']}], {short(a.get('count'))} of {short(a.get('type'))}: "
                               f"glTF wants a MAT4 for each of its {len(joints)} joints")
        for i, an in enumerate(self.list("animations")):
            samplers = items(an, "samplers", f"animations[{i}].samplers", True)
            for j, s in enumerate(samplers):
                ref(s.get("input"), "accessors", f"animations[{i}].samplers[{j}].input")
                ref(s.get("output"), "accessors", f"animations[{i}].samplers[{j}].output")
            for j, c in enumerate(items(an, "channels", f"animations[{i}].channels", True)):
                if not (whole(c.get("sampler")) and c["sampler"] < len(samplers)):
                    out.append(f"animations[{i}].channels[{j}].sampler points at its samplers[{short(c.get('sampler'))}], and it has {len(samplers)}")
                tg = c.get("target")
                if not isinstance(tg, dict):
                    out.append(f"animations[{i}].channels[{j}].target is {kind_of(tg)}: {{node, path}}")
                elif "node" in tg:
                    ref(tg["node"], "nodes", f"animations[{i}].channels[{j}].target.node")
        for i, t in enumerate(self.list("textures")):
            for k, lst in (("source", "images"), ("sampler", "samplers")):
                if k in t:
                    ref(t[k], lst, f"textures[{i}].{k}")
        for i, im in enumerate(self.list("images")):
            if "bufferView" in im:
                ref(im["bufferView"], "bufferViews", f"images[{i}].bufferView")
            elif not isinstance(im.get("uri", ""), str):
                out.append(f"images[{i}].uri is {kind_of(im['uri'])}: a file name or a data: URI")

        blen = []   # each buffer's bytes, as it says them (None: said above)
        for i, b in enumerate(self.list("buffers")):
            n = b.get("byteLength")
            blen.append(n if whole(n, 1) else None)
            if not whole(n, 1):
                out.append(f"buffers[{i}].byteLength is a whole number of bytes, 1 or more: {short(n)}")
            elif "uri" in b:
                if not isinstance(b["uri"], str):
                    out.append(f"buffers[{i}].uri is {kind_of(b['uri'])}: a file name or a data: URI")
            elif i == 0 and self.bin is not None:
                if len(self.bin) < n:
                    out.append(f"buffers[0] says {n:,} bytes, and the GLB's BIN chunk has {len(self.bin):,}")
            else:
                out.append(f"buffers[{i}] has no uri and is not the GLB's BIN chunk")
        vlen = []   # each bufferView's bytes (None: said above)
        for i, v in enumerate(self.list("bufferViews")):
            n, at, st = v.get("byteLength"), v.get("byteOffset", 0), v.get("byteStride")
            vlen.append(None)
            if not ref(v.get("buffer"), "buffers", f"bufferViews[{i}].buffer"):
                continue
            if not (whole(n, 1) and whole(at)):
                out.append(f"bufferViews[{i}]: byteLength (1 or more) and byteOffset (0 or more) are whole numbers of bytes: {short(n)}, {short(at)}")
                continue
            vlen[i], b = n, blen[v["buffer"]]
            if b is not None and at + n > b:
                out.append(f"bufferViews[{i}] runs {at + n - b:,} bytes past the end of buffers[{v['buffer']}] (from byte {at:,}, {n:,} bytes, of {b:,})")
            if st is not None and not (whole(st, 4) and st <= 252 and st % 4 == 0):
                out.append(f"bufferViews[{i}].byteStride is 4 to 252, a multiple of 4: {short(st)}")
        for i, a in enumerate(self.list("accessors")):
            w, comp, typ, count, at = f"accessors[{i}]", a.get("componentType"), a.get("type"), a.get("count"), a.get("byteOffset", 0)
            if not (whole(comp) and comp in COMPONENT and isinstance(typ, str) and typ in COUNT):
                out.append(f"{w}: componentType {short(comp)}, type {short(typ)}: glTF's are 5120, 5121, 5122, 5123, 5125, 5126 and SCALAR, VEC2–4, MAT2–4")
                continue
            if not (whole(count, 1) and whole(at)):
                out.append(f"{w}: count (1 or more) and byteOffset (0 or more) are whole numbers: {short(count)}, {short(at)}")
                continue
            size, elem = COMPONENT[comp][1], element(typ, COMPONENT[comp][1])
            if "bufferView" in a:
                if not ref(a["bufferView"], "bufferViews", f"{w}.bufferView") or vlen[a["bufferView"]] is None:
                    continue
                st = self.list("bufferViews")[a["bufferView"]].get("byteStride")
                st = st if whole(st, 1) else elem
                end, have = at + st * (count - 1) + elem, vlen[a["bufferView"]]
                if end > have:
                    out.append(f"{w}: {count:,} elements of {elem} bytes" + (f" every {st}" if st != elem else "") +
                               f" from byte {at:,} run past the end of bufferViews[{a['bufferView']}] ({end:,} bytes of {have:,})")
                if at % size:
                    out.append(f"{w}.byteOffset {at} is not a multiple of {size}, its component's bytes: three cannot read it")
            elif count > ZEROS:
                out.append(f"{w}: {count:,} elements and no bufferView (zeros): more than any model holds, a broken count")
            sp = a.get("sparse")
            if sp is None:
                continue
            if not (isinstance(sp, dict) and whole(sp.get("count"), 1) and sp["count"] <= count and isinstance(sp.get("indices"), dict) and isinstance(sp.get("values"), dict)):
                out.append(f"{w}.sparse is {{count (1 to {count:,}), indices, values}}: {short(sp)}")
                continue
            ic = sp["indices"].get("componentType")
            if not (whole(ic) and ic in (5121, 5123, 5125)):
                out.append(f"{w}.sparse.indices.componentType is 5121, 5123 or 5125: {short(ic)}")
                continue
            inside = True
            for part, nbytes in (("indices", COMPONENT[ic][1]), ("values", COUNT[typ] * size)):
                r, wp = sp[part], f"{w}.sparse.{part}"
                if not ref(r.get("bufferView"), "bufferViews", f"{wp}.bufferView") or vlen[r["bufferView"]] is None:
                    inside = False
                    continue
                o = r.get("byteOffset", 0)
                if not whole(o):
                    out.append(f"{wp}.byteOffset is a whole number, 0 or more: {short(o)}")
                    inside = False
                    continue
                end = o + sp["count"] * nbytes
                if end > vlen[r["bufferView"]]:
                    out.append(f"{wp}: {sp['count']:,} of them run past the end of bufferViews[{r['bufferView']}] ({end:,} bytes of {vlen[r['bufferView']]:,})")
                    inside = False
            if inside and not any(b is None for b in blen):   # the indices: each below the count, each above the one before
                try:
                    idx = [j[0] for j in _plain(self, {**sp["indices"], "componentType": ic}, sp["count"], 1)]
                except (GltfError, struct.error):
                    continue
                past = [j for j in idx if j >= count]
                if past:
                    out.append(f"{w}.sparse.indices: {past[0]:,} is past its {count:,} elements" + (f" (and {len(past) - 1} more)" if len(past) > 1 else "")
                               + ": glTF's sparse indices are each below the accessor's count")
                elif any(b <= a for a, b in zip(idx, idx[1:])):
                    out.append(f"{w}.sparse.indices are not in increasing order: glTF wants each above the one before")
        return out[:20] + ([f"… and {len(out) - 20} more like these"] if len(out) > 20 else [])

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
        if not (whole(comp) and comp in COMPONENT and isinstance(typ, str) and typ in COUNT and whole(count)):
            raise GltfError(f"accessors[{i}]: component type {short(comp)}, type {short(typ)} or count {short(count)} is not glTF's")
        fmt, size = COMPONENT[comp]
        n = COUNT[typ]
        rows, col = {"MAT2": 2, "MAT3": 3, "MAT4": 4}.get(typ), None
        if rows and size < 4:
            col = -(-(rows * size) // 4) * 4
        elem = element(typ, size)
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
        elif count > ZEROS:
            raise GltfError(f"accessors[{i}]: {count:,} elements and no bufferView (zeros): more than any model holds, a broken count")
        else:
            out = [(0,) * n] * count   # glTF: no bufferView is zeros, a sparse block may set some
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


def element(typ, size):
    """An accessor element's bytes: its components, a matrix of 1- or 2-byte ones with each column on a 4-byte boundary."""
    rows = {"MAT2": 2, "MAT3": 3, "MAT4": 4}.get(typ)
    if rows and size < 4:
        return -(-(rows * size) // 4) * 4 * rows
    return COUNT[typ] * size


# ---- 4x4 matrices, column-major tuples as glTF writes them ----
def mul(a, b):
    return tuple(sum(a[r + 4 * k] * b[k + 4 * c] for k in range(4)) for c in range(4) for r in range(4))


def local(node):
    """A node's own matrix: its matrix, or translation × rotation × scale."""
    if "matrix" in node:
        return tuple(float(x) for x in node["matrix"])
    tx, ty, tz = node.get("translation", (0, 0, 0))
    x, y, z, w = node.get("rotation", (0, 0, 0, 1))
    k = math.sqrt(x * x + y * y + z * z + w * w)
    if k > 0:   # glTF's rotations are unit quaternions; one that is not is taken as the turn it points at (all zeros: none)
        x, y, z, w = x / k, y / k, z / k, w / k
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
