"""bin/vh model3d: 3D models a film draws in the Three.js layer (engines/canvas-film/README.md, Three.js 层), or in
anything else that takes glTF. Stdlib only: nothing leaves the machine, nothing is paid for. (gen, a model made from
pictures by a paid service, comes later; it is not here yet.)

usage: bin/vh model3d check <model.glb|model.gltf> [--tier hero|prop] [--max-faces N] [--max-texture PX] [--json]

  check   what the model holds, against what a shot can carry: its triangles (as the scene draws them: a mesh used by
          two nodes counts twice), meshes and materials; each texture's size, format and bytes, and what uses it; skins
          and their joints; each clip's name and length, named as the Three.js layer names it (an unnamed one is
          animation_<i>, as three's GLTFLoader names it); the box it fills in metres, where its origin sits, and which
          way it is tallest (glTF is metres and +Y up by definition: a file cannot say otherwise, so a size far off for
          what it is says it was made in other units). Over the tier's triangles or texture size, an extension the
          Three.js layer cannot decode (Draco, meshopt, KTX2 / Basis: it has no decoders), or an image or buffer that
          is not beside the model fails it; a size over 100 m or under 1 cm across, two clips with one name, a clip
          of no length are warnings. A skinned mesh is measured in its bind pose.
  --tier  hero (default): 200,000 triangles, textures up to 4096 px a side · prop: 50,000 and 2048 px.
          --max-faces and --max-texture change the tier's numbers.
--json: {"version": 1, "tool", "file", "kind" (glb | gltf), "bytes", "generator", "tier", "limits": {"faces", "texture"},
"extensions": {"used", "required"}, "counts": {"nodes", "meshes", "primitives", "triangles", "triangles_in_meshes",
"vertices", "materials", "textures", "images", "skins", "joints", "animations", "morph_targets", "cameras", "lights"},
"meshes": [{"name", "primitives", "triangles", "vertices", "uses", "skinned", "morph_targets", "normals"}], "materials":
[{"name", "alpha", "double_sided", "textures": {slot: texture}, "extensions"}], "textures": [{"index", "image", "name",
"format", "width", "height", "bytes", "where", "used_by"}], "skins": [{"name", "joints", "joint_names"}], "animations":
[{"name", "duration", "start", "channels", "targets", "interpolations"}], "bbox": {"min", "max", "size", "center"} | null,
"tallest" (x | y | z), "origin" (base centre | centre | inside | outside), "findings": [{"kind", "severity" (fail | warn |
info), "message"}], "verdict" (pass | fail), "exit"}. The lines a person reads go to stderr with --json.
Exit: 0 · 1 a check failed, or the file is not a glTF 2.0 model it can read · 2 usage: no such file, a bad option.
"""
import json, math, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glb   # noqa: E402

PROG = "bin/vh model3d"
TIERS = {"hero": {"faces": 200_000, "texture": 4096}, "prop": {"faces": 50_000, "texture": 2048}}
# what three's GLTFLoader reads without a decoder the layer does not ship (engines/canvas-film/three/)
NEEDS_DECODER = {"KHR_draco_mesh_compression": "DRACOLoader", "EXT_meshopt_compression": "MeshoptDecoder",
                 "KHR_meshopt_compression": "MeshoptDecoder", "KHR_texture_basisu": "KTX2Loader"}
LOADER_KNOWS = {"KHR_lights_punctual", "KHR_materials_clearcoat", "KHR_materials_dispersion", "KHR_materials_ior", "KHR_materials_sheen",
                "KHR_materials_specular", "KHR_materials_transmission", "KHR_materials_iridescence", "KHR_materials_anisotropy",
                "KHR_materials_unlit", "KHR_materials_volume", "KHR_texture_transform", "KHR_mesh_quantization",
                "KHR_materials_emissive_strength", "EXT_materials_bump", "EXT_texture_webp", "EXT_texture_avif", "EXT_mesh_gpu_instancing",
                *NEEDS_DECODER}
OK, NO, WA = "\033[32m✓\033[0m", "\033[31m✗\033[0m", "\033[33m!\033[0m"


class Usage(Exception):
    """A usage error: exit 2."""


def num(x):
    return f"{x:,}"


def metres(x):
    return f"{x:.2f}" if abs(x) >= 0.01 or x == 0 else f"{x:.4f}"


def tex_refs(mat):
    """[(slot, texture index)] a material uses, its extensions' too: every {"index": n} under a key ending in Texture."""
    out = []
    def walk(v, key):
        if isinstance(v, dict):
            if key.endswith("Texture") and isinstance(v.get("index"), int):
                out.append((key[:-len("Texture")], v["index"]))
            for k, x in v.items():
                walk(x, k)
        elif isinstance(v, list):
            for x in v:
                walk(x, key)
    walk(mat, "")
    return out


def tex_source(t):
    """The image a texture shows: an extension's source (WebP, AVIF, Basis) before the plain one."""
    ext = t.get("extensions") or {}
    for k in ("KHR_texture_basisu", "EXT_texture_avif", "EXT_texture_webp"):
        if isinstance((ext.get(k) or {}).get("source"), int):
            return ext[k]["source"]
    return t.get("source")


def accessor_range(m, i):
    """(min, max) of an accessor, from its min and max (normalized integers scaled) or, without them, from its data."""
    a = m.get("accessors", i, "a primitive or an animation")
    lo, hi = a.get("min"), a.get("max")
    if isinstance(lo, list) and isinstance(hi, list) and lo and len(lo) == len(hi) and all(glb.finite(x) for x in lo + hi):
        if a.get("normalized") and a.get("componentType") in glb.NORM:
            k = glb.NORM[a["componentType"]]
            lo, hi = [max(x / k, -1.0) for x in lo], [max(x / k, -1.0) for x in hi]
        return list(lo), list(hi)
    data = m.accessor(i)
    if not data:
        return None, None
    cols = list(zip(*data))
    return [min(c) for c in cols], [max(c) for c in cols]


def check(path, tier, limits):
    """The report (a dict, as --json prints it) of one model."""
    rep = {"version": 1, "tool": f"{PROG} check", "file": str(path), "tier": tier, "limits": limits, "findings": []}
    say = lambda kind, sev, msg: rep["findings"].append({"kind": f"model3d.{kind}", "severity": sev, "message": msg})   # noqa: E731
    try:
        m = glb.Model(path)
        build(m, rep, say, limits)
    except glb.GltfError as e:
        say("read", "fail", f"not a glTF 2.0 model this can read: {e}")
    except (OSError, ValueError, KeyError, TypeError, IndexError, ArithmeticError) as e:   # a malformed file, a part that is not what glTF says
        say("read", "fail", f"a part of it is not what glTF 2.0 says ({type(e).__name__}: {e})")
    fails = [f for f in rep["findings"] if f["severity"] == "fail"]
    rep["verdict"], rep["exit"] = ("fail", 1) if fails else ("pass", 0)
    return rep


def build(m, rep, say, limits):
    J = m.json
    rep.update(kind=m.kind, bytes=m.bytes, generator=(J.get("asset") or {}).get("generator", ""))
    used, req = list(J.get("extensionsUsed") or []), list(J.get("extensionsRequired") or [])
    rep["extensions"] = {"used": used, "required": req}
    for e in req:
        if e in NEEDS_DECODER:
            say("extension", "fail", f"it needs {e}, and the Three.js layer has no {NEEDS_DECODER[e]}: write it out uncompressed (gltf-transform, or Blender's glTF export with compression off)")
        elif e not in LOADER_KNOWS:
            say("extension", "fail", f"it needs {e}, which three's GLTFLoader does not read")

    world = m.world()
    meshes = m.list("meshes")
    uses = [0] * len(meshes)
    for i, w in world.items():
        n = m.list("nodes")[i]
        if isinstance(n.get("mesh"), int) and 0 <= n["mesh"] < len(meshes):
            inst = ((n.get("extensions") or {}).get("EXT_mesh_gpu_instancing") or {}).get("attributes") or {}
            k = next((m.get("accessors", a, "an instanced node")["count"] for a in inst.values() if isinstance(a, int)), 1)
            uses[n["mesh"]] += k
    rows, tris_mesh, tris_drawn, verts, morphs = [], 0, 0, 0, 0
    skinned_meshes = {m.list("nodes")[i]["mesh"] for i in world if "skin" in m.list("nodes")[i] and isinstance(m.list("nodes")[i].get("mesh"), int)}
    for mi, mesh in enumerate(meshes):
        t = v = 0
        normals, targets = True, 0
        for p in mesh.get("primitives", []):
            attrs = p.get("attributes", {})
            vc = m.get("accessors", attrs["POSITION"], f"meshes[{mi}]")["count"] if "POSITION" in attrs else 0
            n = m.get("accessors", p["indices"], f"meshes[{mi}]")["count"] if "indices" in p else vc
            mode = p.get("mode", 4)
            t += n // 3 if mode == 4 else max(0, n - 2) if mode in (5, 6) else 0
            v += vc
            normals = normals and "NORMAL" in attrs
            targets = max(targets, len(p.get("targets", [])))
        rows.append({"name": mesh.get("name", f"mesh_{mi}"), "primitives": len(mesh.get("primitives", [])), "triangles": t, "vertices": v,
                     "uses": uses[mi], "skinned": mi in skinned_meshes, "morph_targets": targets, "normals": normals})
        tris_mesh += t; tris_drawn += t * uses[mi]; verts += v; morphs += targets
    rep["meshes"] = rows

    mats = m.list("materials")
    rep["materials"] = [{"name": x.get("name", f"material_{i}"), "alpha": x.get("alphaMode", "OPAQUE"), "double_sided": bool(x.get("doubleSided")),
                         "textures": {slot: ti for slot, ti in tex_refs(x)}, "extensions": sorted((x.get("extensions") or {}).keys())} for i, x in enumerate(mats)]
    used_by = {}
    for x in rep["materials"]:
        for slot, ti in x["textures"].items():
            used_by.setdefault(ti, []).append(f"{x['name']}.{slot}")
    texs = []
    for ti, t in enumerate(m.list("textures")):
        src = tex_source(t)
        row = {"index": ti, "image": src, "name": "", "format": "", "width": 0, "height": 0, "bytes": 0, "where": "", "used_by": used_by.get(ti, [])}
        if isinstance(src, int):
            data, mime, where = m.image(src)
            im = m.get("images", src, f"textures[{ti}]")
            fmt, w, h = glb.image_size(data)
            row.update(name=im.get("name") or (im.get("uri", "").rsplit("/", 1)[-1] if not str(im.get("uri", "")).startswith("data:") else ""),
                       format=fmt or mime.replace("image/", ""), width=w, height=h, bytes=len(data) if data else 0, where=where)
            if data is None:
                say("missing", "fail", f"texture {ti}'s image {where} is not beside the model: the layer would load it from there and fail")
        texs.append(row)
    rep["textures"] = texs
    big = [x for x in texs if max(x["width"], x["height"]) > limits["texture"]]
    for x in big:
        say("texture", "fail", f"texture {x['index']} ({x['name'] or x['where']}) is {x['width']}x{x['height']}: over {limits['texture']} px a side "
            f"(--max-texture raises it; scale it down, or bake it smaller in Blender)")
    for i, b in enumerate(m.list("buffers")):
        if "uri" in b and not str(b["uri"]).startswith("data:"):
            try:
                m.buffer(i)
            except glb.GltfError as e:
                say("missing", "fail", str(e))

    skins, joints = [], set()
    for s in m.list("skins"):
        js = [j for j in s.get("joints", []) if isinstance(j, int)]
        joints.update(js)
        skins.append({"name": s.get("name", ""), "joints": len(js), "joint_names": [m.list("nodes")[j].get("name", f"node_{j}") for j in js if j < len(m.list("nodes"))]})
    rep["skins"] = skins

    anims, names = [], {}
    for ai, a in enumerate(m.list("animations")):
        name = a.get("name") or f"animation_{ai}"   # three's GLTFLoader: animationDef.name or 'animation_' + index
        names[name] = names.get(name, 0) + 1
        lo, hi, targets, interp = math.inf, 0.0, [], set()
        samplers = a.get("samplers", [])
        for c in a.get("channels", []):
            s = samplers[c["sampler"]]
            r0, r1 = accessor_range(m, s["input"])
            if r0:
                lo, hi = min(lo, r0[0]), max(hi, r1[0])
            interp.add(s.get("interpolation", "LINEAR"))
            tg = c.get("target", {})
            node = tg.get("node")
            targets.append(f"{m.list('nodes')[node].get('name', f'node_{node}') if isinstance(node, int) and node < len(m.list('nodes')) else '?'}.{tg.get('path', '?')}")
        anims.append({"name": name, "duration": round(hi, 4), "start": round(lo, 4) if lo != math.inf else 0.0,
                      "channels": len(a.get("channels", [])), "targets": targets, "interpolations": sorted(interp)})
        if hi <= 0:
            say("names", "warn", f"clip {name} has no length: a play of it shows one pose")
    for name, k in names.items():
        if k > 1:
            say("names", "warn", f"{k} clips are named {name}: the Three.js layer plays the first of them; rename the others")
    rep["animations"] = anims

    rep["counts"] = {"nodes": len(m.list("nodes")), "meshes": len(meshes), "primitives": sum(r["primitives"] for r in rows),
                     "triangles": tris_drawn, "triangles_in_meshes": tris_mesh, "vertices": verts, "materials": len(mats),
                     "textures": len(texs), "images": len(m.list("images")), "skins": len(skins), "joints": len(joints),
                     "animations": len(anims), "morph_targets": morphs, "cameras": len(m.list("cameras")),
                     "lights": len(((J.get("extensions") or {}).get("KHR_lights_punctual") or {}).get("lights", []))}
    if tris_drawn > limits["faces"]:
        say("faces", "fail", f"{num(tris_drawn)} triangles: over {num(limits['faces'])} (--max-faces raises it; Blender's Decimate cuts it, engines/blender.md)")
    if not meshes:
        say("empty", "warn", "no meshes: nothing for a shot to show")

    bbox(m, rep, say, world)


def bbox(m, rep, say, world):
    """The box the default scene fills, in metres; where the origin sits; which way it is tallest."""
    nodes, lo, hi = m.list("nodes"), [math.inf] * 3, [-math.inf] * 3
    skins = m.list("skins")
    for i, w in world.items():
        n = nodes[i]
        if not isinstance(n.get("mesh"), int):
            continue
        mats = [w]
        if isinstance(n.get("skin"), int) and n["skin"] < len(skins):   # the node's own transform is ignored (glTF); each joint's
            s = skins[n["skin"]]
            ibm = m.accessor(s["inverseBindMatrices"]) if "inverseBindMatrices" in s else [glb.IDENTITY] * len(s.get("joints", []))
            mats = [glb.mul(world.get(j, glb.IDENTITY), tuple(b)) for j, b in zip(s.get("joints", []), ibm)] or [glb.IDENTITY]
            if all(glb.near_identity(x) for x in mats):
                mats = [glb.IDENTITY]
        inst = ((n.get("extensions") or {}).get("EXT_mesh_gpu_instancing") or {}).get("attributes") or {}
        if inst:
            tr = m.accessor(inst["TRANSLATION"]) if "TRANSLATION" in inst else None
            rt = m.accessor(inst["ROTATION"]) if "ROTATION" in inst else None
            sc = m.accessor(inst["SCALE"]) if "SCALE" in inst else None
            k = len(tr or rt or sc or [])
            mats = [glb.mul(x, glb.local({"translation": tr[j] if tr else (0, 0, 0), "rotation": rt[j] if rt else (0, 0, 0, 1),
                                           "scale": sc[j] if sc else (1, 1, 1)})) for x in mats for j in range(k)] or mats
        for p in m.list("meshes")[n["mesh"]].get("primitives", []):
            if "POSITION" not in p.get("attributes", {}):
                continue
            a, b = accessor_range(m, p["attributes"]["POSITION"])
            if not a:
                continue
            for mx in mats:
                for c in glb.corners(a, b):
                    q = glb.apply(mx, c)
                    lo, hi = [min(x, y) for x, y in zip(lo, q)], [max(x, y) for x, y in zip(hi, q)]
    if lo[0] == math.inf:
        rep.update(bbox=None, tallest=None, origin=None)
        return
    size = [b - a for a, b in zip(lo, hi)]
    centre = [(a + b) / 2 for a, b in zip(lo, hi)]
    r = lambda v: [round(x, 5) for x in v]   # noqa: E731
    rep["bbox"] = {"min": r(lo), "max": r(hi), "size": r(size), "center": r(centre)}
    rep["tallest"] = "xyz"[size.index(max(size))] if max(size) > 0 else None
    big = max(size)
    tol = max(big * 0.02, 1e-6)
    if abs(centre[0]) <= tol and abs(centre[2]) <= tol and abs(lo[1]) <= tol:
        rep["origin"] = "base centre"
    elif all(abs(c) <= tol for c in centre):
        rep["origin"] = "centre"
    elif all(a - tol <= 0 <= b + tol for a, b in zip(lo, hi)):
        rep["origin"] = "inside"
    else:
        rep["origin"] = "outside"
    if big > 100:
        say("scale", "warn", f"{metres(big)} m across: glTF is metres, and a model made in centimetres comes in 100 times its size "
            "(scale it in the layer's models entry, or apply the scale in Blender)")
    elif 0 < big < 0.01:
        say("scale", "warn", f"{metres(big)} m across: under 1 cm in glTF's metres; was it made in other units?")


def lines(rep):
    """The lines a person reads: what it holds, then the findings, then the verdict."""
    out = []
    if "kind" not in rep:   # could not read it
        out.append(f"{PROG} check: {rep['file']}")
    else:
        kb = rep["bytes"] / 1000
        out.append(f"{PROG} check: {Path(rep['file']).name} · {rep['kind']}, {kb:,.1f} kB" + (f" · from {rep['generator']}" if rep.get("generator") else ""))
        c = rep["counts"]
        geo = f"{c['meshes']} mesh{'es' if c['meshes'] != 1 else ''}, {c['primitives']} primitive{'s' if c['primitives'] != 1 else ''} · {num(c['triangles'])} triangles"
        if c["triangles"] != c["triangles_in_meshes"]:
            geo += f" drawn ({num(c['triangles_in_meshes'])} in the meshes)"
        geo += f" · {num(c['vertices'])} vertices · {c['materials']} material{'s' if c['materials'] != 1 else ''}"
        if c["morph_targets"]:
            geo += f" · up to {c['morph_targets']} morph targets"
        flat = [x["name"] for x in rep["meshes"] if not x["normals"]]
        if flat:
            geo += f" · no normals in {', '.join(flat[:3])}{' …' if len(flat) > 3 else ''} (three shades them flat)"
        out.append(f"  geometry    {geo}")
        if rep["textures"]:
            t = rep["textures"]
            shown = [f"{x['name'] or x['where'] or x['index']} {x['width']}x{x['height']} {x['format']}, {x['bytes'] / 1000:,.1f} kB, {x['where']}"
                     + (f" · {', '.join(x['used_by'][:3])}" if x["used_by"] else " · unused") for x in t[:6]]
            out.append(f"  textures    {len(t)}: " + "\n              ".join(shown) + (f"\n              … {len(t) - 6} more" if len(t) > 6 else ""))
        else:
            out.append("  textures    none")
        if rep["skins"]:
            out.append("  skins       " + " · ".join(f"{s['name'] or 'skin'}: {s['joints']} joints" + (f" ({', '.join(s['joint_names'][:4])}{' …' if s['joints'] > 4 else ''})" if s["joint_names"] else "")
                                               for s in rep["skins"]))
        if rep["animations"]:
            out.append("  animations  " + " · ".join(f"{a['name']} {a['duration']:.2f} s" + (f" (from {a['start']:.2f})" if a["start"] > 0 else "") for a in rep["animations"][:8])
                       + (f" · … {len(rep['animations']) - 8} more" if len(rep["animations"]) > 8 else ""))
        else:
            out.append("  animations  none")
        b = rep.get("bbox")
        if b:
            s = b["size"]
            out.append(f"  size        {metres(s[0])} x {metres(s[1])} x {metres(s[2])} m (x, y, z) · y from {metres(b['min'][1])} to {metres(b['max'][1])}"
                       f" · origin: {rep['origin']}" + ("" if rep["origin"] != "outside" else f" (its box's centre is at {', '.join(metres(x) for x in b['center'])})"))
            up = f"tallest along {rep['tallest']}" if rep["tallest"] else "flat"
            hint = ""
            if rep["tallest"] == "z" and s[1] * 2 < s[2] and s[1] <= min(s[0], s[2]):
                hint = ": if it should stand up, it may have been made Z-up and exported without converting"
            out.append(f"  units       metres and +Y up, as glTF defines them · {up}{hint}")
    for f in rep["findings"]:
        out.append(f"{ {'fail': NO, 'warn': WA}.get(f['severity'], '-') } {f['message']}")
    lim = rep["limits"]
    if rep["verdict"] == "pass" and "counts" in rep:
        side = max([max(x["width"], x["height"]) for x in rep["textures"]] or [0])
        out.append(f"{OK} within {rep['tier']}: {num(rep['counts']['triangles'])} of {num(lim['faces'])} triangles"
                   + (f", textures up to {side} of {lim['texture']} px" if rep["textures"] else ""))
    elif rep["verdict"] == "fail":
        out.append(f"{NO} {PROG} check: {sum(1 for f in rep['findings'] if f['severity'] == 'fail')} failed")
    return out


def main(argv):
    if not argv or "-h" in argv or "--help" in argv:
        print(__doc__.split("\n\n", 1)[1].rstrip(), file=sys.stdout if argv else sys.stderr)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd == "gen":
            raise Usage("gen (a model made from pictures by a paid service) comes later; check is here now")
        if cmd != "check":
            raise Usage(f"no subcommand {cmd!r}: check (bin/vh model3d -h)")
        path, tier, as_json, over = None, "hero", False, {}
        while rest:
            a = rest.pop(0)
            k, eq, v = a.partition("=")
            if k in ("--tier", "--max-faces", "--max-texture"):
                if not eq:
                    if not rest:
                        raise Usage(f"{k} needs a value")
                    v = rest.pop(0)
                if k == "--tier":
                    if v not in TIERS:
                        raise Usage(f"--tier: hero or prop, not {v!r}")
                    tier = v
                else:
                    try:
                        n = int(v)
                    except ValueError:
                        n = 0
                    if n < 1:
                        raise Usage(f"{k}: a whole number above 0, not {v!r}")
                    over["faces" if k == "--max-faces" else "texture"] = n
            elif a == "--json":
                as_json = True
            elif a.startswith("-"):
                raise Usage(f"unknown option {a} (bin/vh model3d -h)")
            elif path:
                raise Usage(f"one model at a time: {path} and {a}")
            else:
                path = a
        if not path:
            raise Usage("which model? check <model.glb|model.gltf>")
        if not Path(path).is_file():
            raise Usage(f"no such file: {path}")
        rep = check(Path(path), tier, {**TIERS[tier], **over})
    except Usage as e:
        print(f"{PROG} {cmd if cmd in ('check', 'gen') else ''}: {e}".replace("  ", " "), file=sys.stderr)
        return 2
    text = "\n".join(lines(rep))
    if as_json:
        print(text, file=sys.stderr)
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(text)
    return rep["exit"]


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
