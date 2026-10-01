# SPDX-License-Identifier: GPL-3.0-or-later
# It calls Blender's Python API, so it is distributed under the GPL (engines/blender.md, "许可证"); the rest of the repo is MIT.
"""Render a Blender swatch scene (styles/<slug>/swatch.py) to PNG frames. render.sh runs it inside Blender:

  blender -b --factory-startup --python-exit-code 1 --python styles/_swatch/blender_render.py -- \
      <scene_dir> <out_dir> --frames 0-149 [--quality final|draft] [--fonts fonts.json] [--hud]

  --frames   a comma list of frames and ranges ("0-149", "149,90,12"), rendered in that order into
             <out_dir>/frame_NNNN.png
  --quality  final (default): Cycles on the CPU, the same pixels on every run and in any frame order;
             draft: Cycles on the GPU (Metal, OptiX, CUDA, HIP or oneAPI, else the CPU) with fewer samples
  --fonts    the role → font file map that blender_fonts.py wrote (a .ttc face is extracted to its own file first)
  --hud      burn the frame number and time into the bottom edge (Blender's stamp; for checking only)

The scene module is plain Python. It imports bpy only where Blender runs it, so `python3 swatch.py --foley` works anywhere:
  FOLEY = [{"t", "sfx", "gain_db", "pan", …}]   the foley list (foley.mjs writes events.json from it)
  FONTS = {"role": "fontconfig pattern"}        e.g. {"zh": "Songti SC:weight=bold"}; env.fonts["zh"] is the loaded font
  RENDER = {"final": {…}, "draft": {…}}         optional overrides of RENDER_DEFAULTS below
  def build(env): …                             once per Blender process: the whole scene, from tokens and constants only
  def apply(t, env): …                          every animated property at t = k/30 s, set directly: a pure function of
                                                t. No keyframes, so no motion blur (a stop-motion camera has none), and
                                                no state carried from one frame to the next.
"""
import importlib.util, json, os, struct, sys, time, traceback, zlib
from types import SimpleNamespace

import bpy

# mirror of lib.js (the content spec every swatch follows; styles/_swatch/README.md, "统一内容规格")
W, H, FPS, DUR, FRAMES, POSTER_T = 1920, 1080, 30, 5, 150, 3.0
SPEC = {"establish": (0, 0.8), "title": (0.8, 2.6), "motif": (2.0, 4.0), "outro": (4.0, 5.0), "poster": 3.0}
TITLE_EN = "Every frame is code."
TITLE_ZH = "每一帧，都是代码。"
MOTIF = [{"key": "outline", "en": "Outline", "zh": "大纲"},
         {"key": "storyboard", "en": "Storyboard", "zh": "分镜"},
         {"key": "draft", "en": "Draft", "zh": "初版"}]

RENDER_DEFAULTS = {
    "final": {"device": "CPU", "samples": 64, "adaptive_threshold": 0.02, "denoise": True},
    "draft": {"device": "GPU", "samples": 16, "adaptive_threshold": 0.05, "denoise": True},
}


def hash01(*xs):
    """[0, 1) from any numbers: the same on every machine (IEEE doubles hashed with crc32, like lib.hash)."""
    return zlib.crc32(struct.pack(f"<{len(xs)}d", *map(float, xs))) / 4294967296


def parse_frames(spec):
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part: continue
        if "-" in part[1:]:
            a, b = part.split("-", 1); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    bad = [k for k in out if not 0 <= k < FRAMES]
    if bad: raise SystemExit(f"[swatch] frames out of range 0–{FRAMES - 1}: {bad[:5]}")
    return out


def args():
    a = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    o = SimpleNamespace(scene=None, out=None, frames=f"0-{FRAMES - 1}", quality="final", fonts=None, hud=False)
    pos, i = [], 0
    while i < len(a):
        if a[i] in ("--frames", "--quality", "--fonts"): setattr(o, a[i][2:], a[i + 1]); i += 2
        elif a[i] == "--hud": o.hud = True; i += 1
        else: pos.append(a[i]); i += 1
    if len(pos) != 2: raise SystemExit("usage: blender -b --python blender_render.py -- <scene_dir> <out_dir> [--frames …]")
    o.scene, o.out = pos
    if o.quality not in RENDER_DEFAULTS: raise SystemExit(f"[swatch] --quality is final or draft, not {o.quality}")
    return o


def use_gpu(cy):
    """the first GPU backend Cycles finds (Metal on a Mac), else the CPU; returns the device name used"""
    p = bpy.context.preferences.addons["cycles"].preferences
    for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
        try: p.compute_device_type = kind
        except TypeError: continue
        p.refresh_devices()
        gpus = [d for d in p.devices if d.type == kind]
        if gpus:
            for d in p.devices: d.use = d.type == kind
            cy.device = "GPU"; return f"{kind} ({gpus[0].name})"
    cy.device = "CPU"; return "CPU (no GPU backend found)"


def setup_render(sc, q, hud):
    r = sc.render
    r.engine = "CYCLES"; r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
    r.fps, r.fps_base = FPS, 1.0
    r.image_settings.file_format = "PNG"; r.image_settings.color_mode = "RGB"
    r.image_settings.color_depth = "8"; r.image_settings.compression = 15
    # persistent data stays off: with it, Cycles on the CPU kept state from earlier frames (tabletop-miniature's teacup came out
    # black on frames 27–44 of an in-order render and grey when those frames were rendered alone), so a frame depended on
    # which frames came before it. determinism.sh caught it (frame 30, 24.5 dB)
    r.film_transparent = False; r.use_persistent_data = False; r.use_motion_blur = False
    cy = sc.cycles
    cy.samples = q["samples"]; cy.use_adaptive_sampling = True; cy.adaptive_threshold = q["adaptive_threshold"]
    cy.use_denoising = q["denoise"]; cy.denoiser = "OPENIMAGEDENOISE"
    cy.seed = 0; cy.use_animated_seed = True              # the noise follows the frame number: still a function of t
    device = use_gpu(cy) if q["device"] == "GPU" else "CPU"
    if q["device"] == "CPU": cy.device = "CPU"
    if hasattr(cy, "denoising_use_gpu"): cy.denoising_use_gpu = q["device"] == "GPU"
    r.use_stamp = hud
    if hud:
        for k in dir(r):
            if k.startswith("use_stamp_"): setattr(r, k, k in ("use_stamp_frame", "use_stamp_time"))
        r.stamp_font_size = 28
    return device


def load_fonts(path):
    fonts = {}
    if not path: return fonts
    for role, f in json.load(open(path)).items():
        fonts[role] = bpy.data.fonts.load(f["file"], check_existing=True)
        print(f"[swatch] font {role}: {f['pattern']} → {fonts[role].name} ({os.path.basename(f['source'])}"
              f"{', face %d' % f['index'] if f['index'] else ''})", flush=True)
    return fonts


def main():
    o = args()
    os.makedirs(o.out, exist_ok=True)
    spec = importlib.util.spec_from_file_location("swatch_scene", os.path.join(o.scene, "swatch.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    for fn in ("build", "apply"):
        if not callable(getattr(mod, fn, None)): raise SystemExit(f"[swatch] swatch.py has no {fn}(env)")
    q = {**RENDER_DEFAULTS[o.quality], **getattr(mod, "RENDER", {}).get(o.quality, {})}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    device = setup_render(sc, q, o.hud)
    env = SimpleNamespace(W=W, H=H, FPS=FPS, DUR=DUR, FRAMES=FRAMES, POSTER_T=POSTER_T, SPEC=SPEC, TITLE_EN=TITLE_EN,
                          TITLE_ZH=TITLE_ZH, MOTIF=MOTIF, tokens=json.load(open(os.path.join(o.scene, "tokens.json"))),
                          quality=o.quality, scene_dir=o.scene, fonts=load_fonts(o.fonts), scene=sc, hash=hash01)
    t0 = time.time(); mod.build(env)
    frames = parse_frames(o.frames)
    print(f"[swatch] built in {time.time() - t0:.1f}s · {o.quality}: {device}, {q['samples']} samples · "
          f"{len(frames)} frame(s) → {o.out}", flush=True)
    for k in frames:
        t1 = time.time()
        sc.frame_set(k)                                   # no keyframes in the scene: this only sets the frame number
        mod.apply(k / FPS, env)
        sc.render.filepath = os.path.join(o.out, f"frame_{k:04d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"[swatch] frame {k:3d} t={k / FPS:.3f} {time.time() - t1:5.1f}s", flush=True)


try:
    main()
except SystemExit as e:
    if e.code not in (None, 0): print(e.code if isinstance(e.code, str) else f"[swatch] exit {e.code}", flush=True)
    sys.exit(1 if e.code not in (None, 0) else 0)
except Exception:
    print("[swatch] ERROR in the Blender scene:\n" + traceback.format_exc(), flush=True)
    sys.exit(1)
