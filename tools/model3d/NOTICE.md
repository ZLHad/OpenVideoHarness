# NOTICE: material from other projects in `tools/model3d/`

`tools/model3d/` is this repository's (MIT, [`../../LICENSE`](../../LICENSE)), but for the file below, which imports Blender's `bpy` and is therefore GPL-3.0-or-later as every such file here is (`engines/blender.md`, 许可证). Part of it is adapted from a project under the MIT License, whose one condition is that the copyright notice and the permission notice travel with the code: its licence, byte for byte from the commit named below, is in [`LICENSES/`](LICENSES/), and the file's header names what was taken.

## blender-skills (EL4CTEO)

- Upstream: <https://github.com/EL4CTEO/blender-skills>, commit `71d031dab8bc6729504d11a78cbe91945401045f` (2026-10-16)
- Copyright (c) 2026 EL4CTEO. MIT License
- Licence copy: [`LICENSES/MIT-blender-skills.txt`](LICENSES/MIT-blender-skills.txt)

| File here | Adapted from (upstream path at that commit) | What was taken |
|---|---|---|
| `blender_qa.py` | `skills/blender-asset-qa/scripts/qa_check.py` | the z-fighting search (sample points of each triangle, a BVH's nearest triangles within eps, parallel normals, the point projected into the other triangle, back-to-back faces told apart), the inside-out test (a closed island's signed volume) and the winding test (a directed edge used twice); rewritten for a glTF imported as it is: z-fighting on the unwelded mesh, the closed-island tests on a welded copy |

Not taken: the floating-part, topology, UV, scale, material and influence-count checks, the profiles and the review renders.
