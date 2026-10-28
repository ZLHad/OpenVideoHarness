"""bin/vh model3d: 3D models a film draws in the Three.js layer (engines/canvas-film/README.md, Three.js 层), or in
anything else that takes glTF. Stdlib only: nothing leaves the machine, nothing is paid for. (gen, a model made from
pictures by a paid service, comes later; it is not here yet.)

usage: bin/vh model3d check <model.glb|model.gltf> [--tier hero|prop] [--max-faces N] [--max-texture PX] [--blender]
                 [--json]

  check   what the model holds, against what a shot can carry: its triangles (as the scene draws them: a mesh used by
          two nodes counts twice), meshes and materials; each texture's size, format and bytes, and what uses it; skins
          and their joints; each clip's name and length, named as the Three.js layer names it (an unnamed one is
          animation_<i>, as three's GLTFLoader names it); the box it fills in metres, where its origin sits, and which
          way it is tallest (glTF is metres and +Y up by definition: a file cannot say otherwise, so a size far off for
          what it is says it was made in other units). Over the tier's triangles or texture size, an extension the
          Three.js layer cannot decode (Draco, meshopt, KTX2 / Basis: it has no decoders; Draco even when it is only
          listed as used, since three's loader then stops without one), or an image or buffer that is not beside the
          model fails it, and so does a skinned mesh with a vertex bound to no bone, weights that do not sum to 1 (three
          does not normalize them: the mesh shrinks or swells as it moves) or a weight on a joint its skin does not have
          (read from the file: what three skins with); a size over 100 m or under 1 cm across, two clips with one name,
          a clip of no length, bytes after the end a GLB's header gives are warnings. A skinned mesh is measured where
          its joints hold it in the file: its box through each joint's world matrix times that joint's inverse bind
          matrix. In the bind pose those are all the identity (the mesh as it was modelled) or one matrix (the rig placed
          as a whole), and the box is the mesh's; when the file holds another pose, the box holds the mesh as each joint
          would move all of it, so it comes out larger than the mesh.
          A file whose parts point outside it (a bufferView past its buffer, an accessor past its bufferView, a type
          or component type glTF does not have, a top-level list that is not one, a reference to nothing) fails with
          the part named. That is a cheap pass, not a validator: Khronos's glTF-Validator
          (github.com/KhronosGroup/glTF-Validator) checks a file against the whole glTF 2.0 spec.
  --tier  hero (default): 200,000 triangles, textures up to 4096 px a side · prop: 50,000 and 2048 px.
          --max-faces and --max-texture change the tier's numbers.
  --blender  two more checks, in Blender (tools/model3d/blender_qa.py; BLENDER, else blender on the PATH, else the
          macOS app): z-fighting (triangles facing the same way within 1 mm that overlap: they flicker as the camera
          moves), and faces pointing inward (closed parts inside out) or wound against their neighbours. Blender runs
          with no environment of ours (no key reaches it), and on macOS in a sandbox: no network, nothing written
          outside its own scratch folder, nothing read in the home folder but this repo and the model's folder.
          Without Blender they are skipped and said; the rest of the check stands. z-fighting and inward faces fail;
          faces glued back to back and opposite winding are warnings.
--json: {"version": 1, "tool", "file", "kind" (glb | gltf), "bytes", "generator", "tier", "limits": {"faces", "texture"},
"extensions": {"used", "required"}, "counts": {"nodes", "meshes", "primitives", "triangles", "triangles_in_meshes",
"vertices", "materials", "textures", "images", "skins", "joints", "animations", "morph_targets", "cameras", "lights"},
"meshes": [{"name", "primitives", "triangles", "vertices", "uses", "skinned", "morph_targets", "normals", "weights"?: {"verts",
"unweighted", "not_one", "worst", "beyond"}}], "materials":
[{"name", "alpha", "double_sided", "textures": {slot: texture}, "extensions"}], "textures": [{"index", "image", "name",
"format", "width", "height", "bytes", "where", "used_by"}], "skins": [{"name", "joints", "joint_names"}], "animations":
[{"name", "duration", "start", "channels", "targets", "interpolations"}], "bbox": {"min", "max", "size", "center"} | null,
"tallest" (x | y | z), "origin" (base centre | centre | inside | outside), "blender" (with --blender: {"state" (ran |
skipped | failed), "note", "version", "seconds", "meshes", "triangles", "zfighting": [{"where", "tri_pairs"}],
"back_to_back", "inside_out": [{"object", "parts"}], "winding": [{"object", "edges"}], "skipped"}), "findings": [{"kind",
"severity" (fail | warn | info), "message"}], "verdict" (pass | fail), "exit"}. A file it cannot read has what was read
before it stopped (version, tool, file, tier, limits, findings, verdict, exit; kind, bytes, generator and extensions if it
got that far). The lines a person reads go to stderr with --json.
Exit: 0 · 1 a check failed, or the file is not a glTF 2.0 model it can read · 2 usage: no such file, a bad option.
"""
import json, math, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import glb   # noqa: E402

PROG = "bin/vh model3d"
TIERS = {"hero": {"faces": 200_000, "texture": 4096}, "prop": {"faces": 50_000, "texture": 2048}}
# what three's GLTFLoader reads without a decoder the layer does not ship (engines/canvas-film/three/)
DRACO = "KHR_draco_mesh_compression"
NEEDS_DECODER = {DRACO: "DRACOLoader", "EXT_meshopt_compression": "MeshoptDecoder",
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
    if "bufferView" not in a and not a.get("sparse"):   # all zeros (glTF): no list of them is made
        return [0.0] * glb.COUNT[a["type"]], [0.0] * glb.COUNT[a["type"]]
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
        rep.update(kind=m.kind, bytes=m.bytes, generator=str(m.json["asset"].get("generator", "")))
        for kind, msg in m.notes:
            say(kind, "warn", msg)
        bad = m.problems()
        for msg in bad:
            say("structure", "fail", msg)
        if not bad:
            build(m, rep, say, limits)
    except glb.GltfError as e:
        say("read", "fail", f"not a glTF 2.0 model this can read: {e}")
    except Exception as e:   # anything else in a file that is not what glTF says: a line, never a traceback
        say("read", "fail", f"a part of it is not what glTF 2.0 says ({type(e).__name__}: {e})")
    return judge(rep)


def judge(rep):
    """The verdict and the exit status from the findings: a fail fails it."""
    fails = [f for f in rep["findings"] if f["severity"] == "fail"]
    rep["verdict"], rep["exit"] = ("fail", 1) if fails else ("pass", 0)
    return rep


def build(m, rep, say, limits):
    J = m.json
    used, req = list(J.get("extensionsUsed") or []), list(J.get("extensionsRequired") or [])
    rep["extensions"] = {"used": used, "required": req}
    out = "write it out uncompressed (gltf-transform, or Blender's glTF export with compression off)"
    for e in req:
        if e in NEEDS_DECODER:
            say("extension", "fail", f"it needs {e}, and the Three.js layer has no {NEEDS_DECODER[e]}: {out}")
        elif e not in LOADER_KNOWS:
            say("extension", "fail", f"it needs {e}, which three's GLTFLoader does not read")
    if DRACO in used and DRACO not in req:   # three's GLTFLoader stops at a Draco listed as used, with no DRACOLoader
        say("extension", "fail", f"it lists {DRACO} as used: three's GLTFLoader stops at that without a DRACOLoader, "
            f"and the Three.js layer has none (even if every mesh has a fallback): {out}")

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
            if not (glb.whole(ti) and ti < len(m.list("textures"))):
                say("structure", "fail", f"material {x['name']}'s {slot} texture points at textures[{ti}], and there are {len(m.list('textures'))}")
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
    weights(m, rep, say, world)

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


def weights(m, rep, say, world):
    """Each skinned mesh's vertex weights as the file holds them (what three skins with: it does not normalize them): a
    vertex whose weights are all 0 is bound to no bone; one whose weights do not sum to 1 within 0.01 shrinks or swells
    the mesh as it moves; a weight on a joint the skin does not have points at nothing. Into rep["meshes"][i]["weights"]."""
    nodes, skins = m.list("nodes"), m.list("skins")
    done = set()
    for i in world:
        n = nodes[i]
        mi, si = n.get("mesh"), n.get("skin")
        if not (isinstance(mi, int) and isinstance(si, int) and si < len(skins)) or mi in done:
            continue
        done.add(mi)
        njoints = len(skins[si].get("joints", []))
        verts = unbound = off = beyond = 0
        worst = 1.0
        for p in m.list("meshes")[mi].get("primitives", []):
            at = p.get("attributes", {})
            sets = [(at[f"JOINTS_{k}"], at[f"WEIGHTS_{k}"]) for k in range(8) if f"JOINTS_{k}" in at and f"WEIGHTS_{k}" in at]
            if not sets:
                continue
            data = [(m.accessor(j), m.accessor(w)) for j, w in sets]
            for v in range(len(data[0][1])):
                s, far = 0.0, False
                for js, ws in data:
                    for jj, ww in zip(js[v], ws[v]):
                        s += ww
                        far = far or (ww > 0 and jj >= njoints)
                verts += 1
                beyond += far
                if s < 1e-6:
                    unbound += 1
                elif abs(s - 1) > 0.01:
                    off += 1
                    worst = s if abs(s - 1) > abs(worst - 1) else worst
        if not verts:
            continue
        name = rep["meshes"][mi]["name"]
        rep["meshes"][mi]["weights"] = {"verts": verts, "unweighted": unbound, "not_one": off, "worst": round(worst, 4), "beyond": beyond}
        if unbound:
            say("weights", "fail", f"{name}: {unbound} of {verts} vertices bound to no bone (their weights are all 0): they stay put while the rig moves")
        if off:
            say("weights", "fail", f"{name}: {off} of {verts} vertices whose weights do not sum to 1 (one sums to {round(worst, 4)}): three does not "
                "normalize them, so the mesh shrinks or swells as it moves (Blender: Weights > Normalize All, then export again)")
        if beyond:
            say("weights", "fail", f"{name}: {beyond} vertices weighted to a joint its skin does not have ({njoints} joints)")


def bbox(m, rep, say, world):
    """The box the default scene fills, in metres; where the origin sits; which way it is tallest."""
    nodes, lo, hi = m.list("nodes"), [math.inf] * 3, [-math.inf] * 3
    skins = m.list("skins")
    for i, w in world.items():
        n = nodes[i]
        if not isinstance(n.get("mesh"), int):
            continue
        mats = [w]
        # skinned: the node's own transform is ignored (glTF); each joint's world matrix times its inverse bind matrix,
        # all of them identity in the bind pose (the mesh as modelled), one shared matrix if the rig is placed as a whole;
        # if they differ (the file holds another pose), the box is the union of the mesh under each, larger than the mesh
        if isinstance(n.get("skin"), int) and n["skin"] < len(skins):
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


MAC_BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"


def find_blender():
    """(the Blender to run, or None, and why not): BLENDER, else blender on the PATH, else the macOS app (as
    styles/_swatch/render.sh finds it)."""
    b = os.environ.get("BLENDER")
    if b:
        return (b, "") if os.path.isfile(b) and os.access(b, os.X_OK) else (None, f"BLENDER is {b}, which is not a program here")
    b = shutil.which("blender") or (MAC_BLENDER if os.access(MAC_BLENDER, os.X_OK) else None)
    return (b, "") if b else (None, "Blender is not installed here (macOS: brew install --cask blender; or BLENDER=/path/to/blender)")


def sbq(p):
    return '"' + str(p).replace("\\", "\\\\").replace('"', '\\"') + '"'


def sandbox(scratch, model_dir, blender):
    """A macOS sandbox profile for Blender reading one model (as styles/_swatch/render.sh's bl_profile): no network, no
    other app; writes only in its scratch folder and Blender's own cache; nothing read in the home folder but this repo,
    the model's folder and the fonts. None when Blender's install folder holds the home folder (a sandbox reading it
    would read everything)."""
    home = os.path.realpath(os.path.expanduser("~"))
    real = os.path.realpath(blender)
    app = real.split("/Contents/MacOS/")[0] if "/Contents/MacOS/" in real else os.path.dirname(real)
    if (home + "/").startswith(app.rstrip("/") + "/"):
        return None
    try:
        cache = os.path.realpath(subprocess.run(["getconf", "DARWIN_USER_CACHE_DIR"], capture_output=True, text=True).stdout.strip())
    except OSError:
        cache = ""
    reads = [HERE.parent.parent, model_dir, scratch, app, os.path.join(home, "Library", "Fonts")]
    return "\n".join(["(version 1)", "(allow default)", "(deny network*)", "(deny lsopen)", "(deny appleevent-send)", "(deny file-write*)",
                      f"(allow file-write* (subpath {sbq(scratch)})" + (f" (subpath {sbq(os.path.join(cache, 'org.blenderfoundation.blender'))})" if cache else "")
                      + ' (literal "/dev/null") (literal "/dev/dtracehelper"))',
                      f"(deny file-read* (subpath {sbq(home)}))",
                      "(allow file-read* " + " ".join(f"(subpath {sbq(os.path.realpath(p))})" for p in reads) + f" (literal {sbq(real)}))", ""])


def run_blender(path, timeout=600):
    """tools/model3d/blender_qa.py on the model in a Blender with no environment of ours (and on macOS in a sandbox) →
    {"state": ran | skipped | failed, "note", …the report's fields}."""
    bl, why = find_blender()
    if not bl:
        return {"state": "skipped", "note": why}
    scratch = os.path.realpath(tempfile.mkdtemp(prefix="vh-model3d-"))
    try:
        for d in ("home", "tmp"):
            os.mkdir(os.path.join(scratch, d))
        out = os.path.join(scratch, "report.json")
        cmd = [bl, "-b", "--factory-startup", "--python-exit-code", "1", "--python", str(HERE / "blender_qa.py"), "--",
               os.path.realpath(path), out]
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": os.path.join(scratch, "home"), "TMPDIR": os.path.join(scratch, "tmp") + "/",
               "LANG": "en_US.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
        if sys.platform == "darwin" and shutil.which("sandbox-exec"):
            prof = sandbox(scratch, os.path.dirname(os.path.realpath(path)), bl)
            if prof is None:
                return {"state": "failed", "note": "Blender's install folder holds the home folder: not run (install Blender elsewhere)"}
            with open(os.path.join(scratch, "blender.sb"), "w") as f:
                f.write(prof)
            cmd = ["sandbox-exec", "-f", os.path.join(scratch, "blender.sb")] + cmd
        t0 = time.monotonic()
        try:
            r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=timeout, errors="replace")
        except subprocess.TimeoutExpired:
            return {"state": "failed", "note": f"Blender gave no report in {timeout} s"}
        secs = round(time.monotonic() - t0, 1)
        try:
            qa = json.loads(Path(out).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            tail = [x for x in (r.stderr + r.stdout).splitlines() if x.strip()][-3:]
            return {"state": "failed", "note": f"Blender exited {r.returncode} with no report" + (f": {' | '.join(tail)}" if tail else "")}
        return {"state": "ran", "seconds": secs, "version": qa.get("blender"), **{k: v for k, v in qa.items() if k not in ("version", "blender")}}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def blender_findings(rep, b):
    """The Blender checks' report into the model's report: rep["blender"] and its findings (also for the tests: b is what
    run_blender gives)."""
    rep["blender"] = b
    say = lambda kind, sev, msg: rep["findings"].append({"kind": f"model3d.{kind}", "severity": sev, "message": msg})   # noqa: E731
    if b.get("state") != "ran":
        say("blender", "info" if b.get("state") == "skipped" else "warn", f"the --blender checks did not run: {b.get('note', '')}")
        return
    if b.get("error"):
        say("blender", "warn", f"Blender could not check it: {b['error']}")
    for z in b.get("zfighting") or []:
        say("zfighting", "fail", f"{z['where']}: {z['tri_pairs']} pairs of triangles face the same way within 1 mm and overlap: they flicker as "
            "the camera moves (delete the hidden one, or move it 2–5 mm along its normal)")
    for z in b.get("back_to_back") or []:
        say("hidden", "warn", f"{z['where']}: {z['tri_pairs']} pairs of faces glued back to back: hidden, and drawn for nothing (delete them)")
    for x in b.get("inside_out") or []:
        say("normals", "fail", f"{x['object']}: {x['parts']} closed part{'s' if x['parts'] != 1 else ''} with the faces pointing inward: lit wrong "
            "and culled away in three (Blender: Mesh > Normals > Recalculate Outside)")
    for x in b.get("winding") or []:
        say("normals", "warn", f"{x['object']}: {x['edges']} edges between faces wound opposite ways (recalculate the normals; a single-sided "
            "material shows the holes)")
    for s in b.get("skipped") or []:
        say("blender", "info", s)


def lines(rep):
    """The lines a person reads: what it holds (as far as it got: a file it could not read through has fewer of them),
    then the findings, then the verdict."""
    if "kind" not in rep:   # could not read it
        out = [f"{PROG} check: {rep['file']}"]
    else:
        out = [f"{PROG} check: {Path(rep['file']).name} · {rep['kind']}, {rep['bytes'] / 1000:,.1f} kB" + (f" · from {rep['generator']}" if rep.get("generator") else "")]
    c = rep.get("counts")
    if c:
        geo = f"{c['meshes']} mesh{'es' if c['meshes'] != 1 else ''}, {c['primitives']} primitive{'s' if c['primitives'] != 1 else ''} · {num(c['triangles'])} triangles"
        if c["triangles"] != c["triangles_in_meshes"]:
            geo += f" drawn ({num(c['triangles_in_meshes'])} in the meshes)"
        geo += f" · {num(c['vertices'])} vertices · {c['materials']} material{'s' if c['materials'] != 1 else ''}"
        if c["morph_targets"]:
            geo += f" · up to {c['morph_targets']} morph targets"
        flat = [x["name"] for x in rep.get("meshes", []) if not x["normals"]]
        if flat:
            geo += f" · no normals in {', '.join(flat[:3])}{' …' if len(flat) > 3 else ''} (three shades them flat)"
        out.append(f"  geometry    {geo}")
    t = rep.get("textures")
    if t:
        shown = [f"{x['name'] or x['where'] or x['index']} {x['width']}x{x['height']} {x['format']}, {x['bytes'] / 1000:,.1f} kB, {x['where']}"
                 + (f" · {', '.join(x['used_by'][:3])}" if x["used_by"] else " · unused") for x in t[:6]]
        out.append(f"  textures    {len(t)}: " + "\n              ".join(shown) + (f"\n              … {len(t) - 6} more" if len(t) > 6 else ""))
    elif t is not None:
        out.append("  textures    none")
    if rep.get("skins"):
        out.append("  skins       " + " · ".join(f"{s['name'] or 'skin'}: {s['joints']} joints" + (f" ({', '.join(s['joint_names'][:4])}{' …' if s['joints'] > 4 else ''})" if s["joint_names"] else "")
                                           for s in rep["skins"]))
    an = rep.get("animations")
    if an:
        out.append("  animations  " + " · ".join(f"{a['name']} {a['duration']:.2f} s" + (f" (from {a['start']:.2f})" if a["start"] > 0 else "") for a in an[:8])
                   + (f" · … {len(an) - 8} more" if len(an) > 8 else ""))
    elif an is not None:
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
    b = rep.get("blender") or {}
    if b.get("state") == "ran":
        clean = not any(b.get(k) for k in ("zfighting", "back_to_back", "inside_out", "winding", "error"))
        out.append(f"  blender     {b.get('version')}: {b.get('meshes', 0)} mesh{'es' if b.get('meshes') != 1 else ''}, {num(b.get('triangles', 0))} triangles"
                   + f" · {b.get('seconds')} s" + (" · no z-fighting, every face outward" if clean else ""))
    for f in rep["findings"]:
        out.append(f"{ {'fail': NO, 'warn': WA}.get(f['severity'], '-') } {f['message']}")
    lim = rep["limits"]
    if rep["verdict"] == "pass" and c:
        side = max([max(x["width"], x["height"]) for x in t or []] or [0])
        out.append(f"{OK} within {rep['tier']}: {num(c['triangles'])} of {num(lim['faces'])} triangles"
                   + (f", textures up to {side} of {lim['texture']} px" if t else ""))
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
        path, tier, as_json, over, use_blender = None, "hero", False, {}, False
        while rest:
            a = rest.pop(0)
            k, eq, v = a.partition("=")
            if a == "--blender":
                use_blender = True
                continue
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
        if use_blender:
            if not any(f["kind"] in ("model3d.read", "model3d.structure") for f in rep["findings"]):   # read through: Blender can take it
                if not as_json:
                    print(f"{PROG} check: reading it in Blender too …", flush=True)
                blender_findings(rep, run_blender(path))
            else:
                rep["blender"] = {"state": "skipped", "note": "the file could not be read: Blender was not asked"}
            judge(rep)
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
