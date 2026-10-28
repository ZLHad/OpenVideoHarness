# SPDX-License-Identifier: GPL-3.0-or-later
# (it imports bpy: this repository's files that do are GPL-3.0-or-later, engines/blender.md, 许可证)
"""bin/vh model3d check --blender, inside Blender: the model imported into an empty scene and two checks over its meshes,
in the shape the file holds them. tools/model3d/model3d.py runs it (blender -b --factory-startup, no environment, and on
macOS in a sandbox: no network, writes only to the report's folder):

  blender -b --factory-startup --python-exit-code 1 --python tools/model3d/blender_qa.py -- <model.glb|gltf> <report.json>
          [--eps 0.001] [--max-tris 300000]

  z-fighting   two triangles that face the same way, lie within eps (1 mm) of each other and overlap: the depth buffer
               cannot tell them apart and they flicker from frame to frame as the camera moves. Faces glued back to back
               (opposite normals) are hidden ones: said, not failed. Skipped over max-tris triangles
  normals      closed parts (each mesh's seams welded first) whose faces point inward (a negative signed volume): lit
               wrong and culled away; and edges whose two faces wind opposite ways

The skin weights are read from the file by bin/vh model3d check itself, not here: Blender's glTF importer binds a vertex
whose weights are all 0 to the first joint, so an unbound vertex cannot be seen after the import (Blender 5.2.2).

The report (JSON): {"version": 1, "blender", "meshes", "triangles", "zfighting": [{"where", "tri_pairs"}],
"back_to_back": [{"where", "tri_pairs"}], "inside_out": [{"object", "parts"}], "winding": [{"object", "edges"}],
"skipped": [why], "error": null | why}.

The z-fighting search (sample points of each triangle, a BVH's nearest triangles within eps, parallel normals, the point
projected into the other triangle) and the inside-out and winding tests are adapted from EL4CTEO/blender-skills,
skills/blender-asset-qa/scripts/qa_check.py at 71d031d (MIT, Copyright (c) 2026 EL4CTEO; its licence in
tools/model3d/LICENSES/MIT-blender-skills.txt, tools/model3d/NOTICE.md). Rewritten for a glTF imported as it is (its
vertices unwelded at seams, so z-fighting is looked for there, and the closed-part test runs on a welded copy).
"""
import json
import sys
from collections import Counter, defaultdict

import bmesh
import bpy
from mathutils.bvhtree import BVHTree


def point_in_tri(p, a, b, c, n):
    for u, v in ((a, b), (b, c), (c, a)):
        if (v - u).cross(p - u).dot(n) < -1e-9:
            return False
    return True


def world_bmesh(ob):
    """The mesh as stored (its rest pose, no modifiers: the shape the file holds) in world space."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    return bm


def islands(bm):
    parent = list(range(len(bm.verts)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for e in bm.edges:
        a, b = find(e.verts[0].index), find(e.verts[1].index)
        if a != b:
            parent[a] = b
    return [find(i) for i in range(len(bm.verts))]


def normals(ob):
    """(closed parts facing inward, edges wound opposite ways) of one mesh, its seams welded on a copy."""
    bm = world_bmesh(ob)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    isl = islands(bm)
    closed = defaultdict(lambda: True)
    for e in bm.edges:
        if len(e.link_faces) != 2:
            closed[isl[e.verts[0].index]] = False
    directed = Counter((loop.vert.index, loop.link_loop_next.vert.index) for f in bm.faces for loop in f.loops)
    winding = sum(1 for c in directed.values() if c > 1)
    vol = defaultdict(float)
    tri = bm.copy()
    bmesh.ops.triangulate(tri, faces=tri.faces[:])
    for f in tri.faces:
        a, b, c = (v.co for v in f.verts)
        vol[isl[f.verts[0].index]] += a.dot(b.cross(c)) / 6.0
    tri.free()
    bm.free()
    inside = sum(1 for g in set(isl) if closed[g] and vol[g] < -1e-12)
    return inside, winding


def zfighting(obs, eps, max_tris, rep):
    verts, tris, meta = [], [], []   # meta: (object index, the triangle's normal)
    for oi, ob in enumerate(obs):
        bm = world_bmesh(ob)
        base = len(verts)
        verts.extend(v.co.copy() for v in bm.verts)
        tri = bm.copy()
        bmesh.ops.triangulate(tri, faces=tri.faces[:])
        for f in tri.faces:
            tris.append(tuple(base + v.index for v in f.verts))
            meta.append((oi, f.normal.copy()))
        tri.free()
        bm.free()
    rep["triangles"] = len(tris)
    if len(tris) > max_tris:
        rep["skipped"].append(f"z-fighting: {len(tris)} triangles, over {max_tris}: check the parts one at a time")
        return
    if not tris:
        return
    bvh = BVHTree.FromPolygons(verts, tris, epsilon=0.0)
    sets = [set(t) for t in tris]
    same, back = set(), set()
    for ti, t in enumerate(tris):
        a, b, c = (verts[i] for i in t)
        n = meta[ti][1]
        if n.length < 0.5:
            continue
        cen = (a + b + c) / 3
        for p in (cen, cen.lerp(a, 0.6), cen.lerp(b, 0.6), cen.lerp(c, 0.6)):
            for _, _, tj, _ in bvh.find_nearest_range(p, eps):
                if tj is None or tj == ti or sets[ti] & sets[tj]:
                    continue
                n2 = meta[tj][1]
                d = n.dot(n2)
                if abs(d) < 0.999:
                    continue
                a2, b2, c2 = (verts[i] for i in tris[tj])
                q = p - n2 * n2.dot(p - a2)
                if point_in_tri(q, a2, b2, c2, n2):
                    (same if d > 0 else back).add((min(ti, tj), max(ti, tj)))

    def describe(pairs):
        out = Counter()
        for i, j in pairs:
            x, y = obs[meta[i][0]].name, obs[meta[j][0]].name
            out[f"{x} <-> {y}" if x != y else x] += 1
        return [{"where": k, "tri_pairs": v} for k, v in out.most_common(20)]
    rep["zfighting"], rep["back_to_back"] = describe(same), describe(back)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(argv) < 2:
        print("blender_qa.py: -- <model> <report.json> [--eps 0.001] [--max-tris 300000]", file=sys.stderr)
        sys.exit(2)
    model, out = argv[0], argv[1]
    opt = lambda k, d: float(argv[argv.index(k) + 1]) if k in argv else d   # noqa: E731
    eps, max_tris = opt("--eps", 0.001), int(opt("--max-tris", 300000))
    rep = {"version": 1, "blender": bpy.app.version_string, "meshes": 0, "triangles": 0, "zfighting": [], "back_to_back": [],
           "inside_out": [], "winding": [], "skipped": [], "error": None}
    try:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=model)
        # the importer's bone display shapes (an icosphere an armature) are not the model
        shapes = {pb.custom_shape for o in bpy.context.scene.objects if o.type == "ARMATURE" for pb in o.pose.bones if pb.custom_shape}
        obs = [o for o in bpy.context.scene.objects if o.type == "MESH" and o.data.polygons and o not in shapes]
        rep["meshes"] = len(obs)
        zfighting(obs, eps, max_tris, rep)
        for ob in obs:
            inside, wind = normals(ob)
            if inside:
                rep["inside_out"].append({"object": ob.name, "parts": inside})
            if wind:
                rep["winding"].append({"object": ob.name, "edges": wind})
    except Exception as e:   # said in the report: the command turns it into a line
        rep["error"] = f"{type(e).__name__}: {e}"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f)


main()
