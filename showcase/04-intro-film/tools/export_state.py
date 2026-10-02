"""Export what the WebGL grid scene (js/grid.js) needs to take over from Blender at 15 s, from blender/galaxy.py itself
(the same seeds and functions, run without Blender: bpy and mathutils are stubbed; nothing is rendered):
  - every film card: grid slot (sx, sy), film (kind 0 procedural / 1 footage / 2 AI, atlas row, playback phase), snap time
  - the camera for every frame from 14.0 to 23.0 s: position, forward, up, roll, fov
  - the far sky: 30 000 star directions and brightnesses (the same seeds as the Blender sky)
usage (from the project root): uv run --no-project --with numpy python tools/export_state.py
"""
import json
import math
import sys
import types
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for m in ("bpy", "mathutils", "nodexpr"):
    sys.modules[m] = types.ModuleType(m)
sys.modules["mathutils"].Vector = object; sys.modules["mathutils"].Quaternion = object; sys.modules["mathutils"].Matrix = object
sys.modules["nodexpr"].bind = None; sys.modules["nodexpr"].Compiler = None
src = (ROOT / "blender/galaxy.py").read_text().rsplit("\nmain()", 1)[0]
sys.argv = ["galaxy.py", "--", "--fx", "C"]
import os
os.chdir(ROOT)
g = {"__name__": "galaxy"}
exec(compile(src, "galaxy.py", "exec"), g)
F, NC = g["F"], g["NC"]
kind = np.where(F["ai"], 2, np.where(F["real"], 1, 0))
cards = {"sx": np.round(F["sx"], 4).tolist(), "sy": np.round(F["sy"], 4).tolist(), "kind": kind.tolist(), "row": F["row"].astype(int).tolist(),
         "ph": np.round(F["ph"], 4).tolist(), "ts": np.round(F["ts"], 4).tolist()}
cam = []
for n in range(14 * 30, 23 * 30 + 1):
    t = n / 30; pos, fwd, up, roll, fov, *_ = g["cam_at"](t)
    cam.append([round(float(x), 5) for x in (*pos, *fwd, *up, roll, fov)])
rs = np.random.default_rng(5).normal(size=(30000, 3)); rs /= np.linalg.norm(rs, axis=1, keepdims=True)
rad = 0.6 + 1.4 * np.random.default_rng(6).random(30000) ** 6
lum = np.exp(np.random.default_rng(7).normal(-0.5, 1.0, 30000)) * 2.5
up = rs[:, 2] >= 0
sky = np.concatenate([rs[up], rad[up, None], lum[up, None]], 1)
out = ROOT / "assets"; out.mkdir(parents=True, exist_ok=True)
(out / "state.json").write_text(json.dumps({"grid": {"GC": g["GC"], "CW": g["CW"], "CH": g["CH"]}, "scan": [g["SCAN0"], g["SCAN1"]],
                                            "nai": int(g["NAI"]), "cards": cards, "cam_t0": 14.0, "cam": cam,
                                            "sky": np.round(sky, 4).tolist()}, separators=(",", ":")))
print(f"{NC} cards, {len(cam)} camera frames, {int(up.sum())} sky stars → {out / 'state.json'}")
