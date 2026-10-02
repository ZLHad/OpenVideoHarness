# SPDX-License-Identifier: GPL-3.0-or-later
# It calls Blender's Python API, so it is distributed under the GPL (engines/blender.md, "许可证"); the rest of the repo is MIT.
#
# The intro film's opening (Blender 5.2, Cycles on Metal): "a galaxy of films". Every star is a film; near the camera
# the stars resolve into glass screens playing their film. Renders 0–15.8 s (frames 0–474); the film takes over at 15.4 s.
#
#   tools/bl.sh -b --factory-startup --python-exit-code 1 --python blender/galaxy.py -- \
#       --frames 0,60,120 [--draft] [--fx B|C] [--out blender/out/frames] [--name f]
#   tools/bl_render.sh 0 474 final2          (the whole opening, in resumable chunks of 30 frames)
#
#   0.0–4.2   a close-up of one glass film; the camera pulls back "powers of ten" style: it is one star of a galaxy
#   4.2–8.0   the galaxy spins faster and faster while the camera spirals down onto it (vertigo)
#   7.2–8.0   the galaxy collapses into the core
#   8.0       supernova; the camera is knocked back
#   9.0–10.4  the two-dimensional foil: a ring front runs across the plane and flattens the debris onto it
#   10.4–13.8 "What's missing?" above the flat, glowing disc
#   14.0–15.8 an amber scan sorts the films into a grid (the WebGL grid, js/grid.js, takes it from here)
# Every frame is a pure function of t = n / 30: numpy computes every star, card and parameter from seeds and t. Motion
# blur: a velocity attribute (central difference across the shutter) on stars and cards, and per-frame camera keyframes.
import bpy, numpy as np, sys, os, time, math
sys.path.insert(0, os.path.join(os.getcwd(), "blender"))
from nodexpr import bind, Compiler
from mathutils import Vector, Quaternion, Matrix

FPS, W, H = 30, 1920, 1080
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default
DRAFT = "--draft" in argv
FX = arg("--fx", "C")
VK = {"B": 1.0, "C": 1.45}[FX]                       # vertigo strength (the look-dev variable)
OUT = arg("--out", "blender/out/frames")
ROOT = os.getcwd()                                   # bl.sh runs Blender from the project root
SHUTTER = 0.5
T_BURST, FR0 = 8.0, 9.0
CORE = np.array([0.0, 0.0, 0.0])

# ---------------------------------------------------------------- helpers (mirror look/js/world.js)
def clamp(x, a=0.0, b=1.0): return np.minimum(b, np.maximum(a, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def lerp(a, b, u): return a + (b - a) * u
def e_out(u): return 1 - (1 - u) ** 3
def e_in(u): return u ** 3
def smooth(u): u = clamp(u); return u * u * (3 - 2 * u)
def sstep(a, b, x): return smooth((x - a) / (b - a))

def track(keys):
    """monotone cubic through [(t, v)…] (Fritsch–Carlson), constant outside"""
    T = np.array([k[0] for k in keys], float); V = np.array([k[1] for k in keys], float); n = len(T)
    d = np.diff(V) / np.diff(T); m = np.zeros(n); m[0] = d[0]; m[-1] = d[-1]
    for i in range(1, n - 1): m[i] = 0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2
    for i in range(n - 1):
        if d[i] == 0: m[i] = m[i + 1] = 0; continue
        a, b = m[i] / d[i], m[i + 1] / d[i]; s = a * a + b * b
        if s > 9: k = 3 / math.sqrt(s); m[i] = k * a * d[i]; m[i + 1] = k * b * d[i]
    def f(t):
        if t <= T[0]: return float(V[0])
        if t >= T[-1]: return float(V[-1])
        i = int(np.searchsorted(T, t) - 1); h = T[i + 1] - T[i]; u = (t - T[i]) / h
        return float((2*u**3 - 3*u**2 + 1) * V[i] + (u**3 - 2*u**2 + u) * h * m[i] + (-2*u**3 + 3*u**2) * V[i + 1] + (u**3 - u**2) * h * m[i + 1])
    return f

def nrm(v): v = np.asarray(v, float); return v / max(np.linalg.norm(v), 1e-9)
def slerp_dir(a, b, w):
    a, b = nrm(a), nrm(b); om = math.acos(float(np.clip(np.dot(a, b), -1, 1)))
    if om < 1e-5: return a
    return nrm((math.sin((1 - w) * om) * a + math.sin(w * om) * b) / math.sin(om))

# ---------------------------------------------------------------- the galaxy (seeded, built once)
RNG = np.random.default_rng(20261002)
N_DISC, N_BULGE, N_HALO = 900_000, 220_000, 60_000
RD, RMAX, PITCH = 24.0, 115.0, math.radians(21.0)
ARMS = np.array([0.0, math.pi, 0.5 * math.pi, 1.5 * math.pi]); ARM_W = np.array([1.0, 1.0, 0.45, 0.45])
def arm_phase(r): return np.log(np.maximum(r, 0.5) / 4.0) / math.tan(PITCH)
def omega(r): return 1.65 / np.maximum(r, 6.0)                       # rad/s: a flat rotation curve, sped up for the film
def spin_v(t): return 0.22 * VK * max(0.0, min(t, 8.0) - 4.0) ** 2.3  # the vertigo: the whole galaxy spins up

def disc_sample(n, inarm_p, rng):
    u = rng.random(n); r = np.minimum(-RD * np.log(1 - u * 0.985) + 2.0, RMAX)
    k = rng.choice(len(ARMS), n, p=ARM_W / ARM_W.sum()); inarm = rng.random(n) < inarm_p
    phi = ARMS[k] + arm_phase(r) + rng.normal(0, 0.10 + 0.0016 * r, n)
    phi = np.where(inarm, phi, rng.random(n) * 2 * math.pi)
    z = rng.normal(0, 0.35 + 0.012 * r, n) * rng.choice([1.0, 2.5], n, p=[0.85, 0.15])
    return r, phi, z, inarm

def burst_params(D, rng):
    """where each body flies after the supernova, and when the 2-D foil front catches it"""
    n = len(D["r0"])
    D["az"] = rng.random(n) * 2 * math.pi
    D["el"] = np.clip(rng.normal(0, 0.42, n), -1.1, 1.1)
    D["sp"] = 2.0 + 120.0 * rng.random(n) ** 1.7
    D["imp0"] = 7.2 + 0.3 * rng.random(n)
    # front radius rf(t) = 80(1 − e^{−(t−FR0)/0.55}); horizontal distance h(t) = sp·cos(el)·0.6(1 − e^{−(t−8)/0.6}); fixed point for tf
    hfin = D["sp"] * np.cos(D["el"]) * 0.6
    tf = np.full(n, FR0 + 0.4)
    for _ in range(8):
        h = hfin * (1 - np.exp(-(tf - T_BURST) / 0.6))
        tf = np.clip(FR0 - 0.55 * np.log(np.clip(1 - h / 80.0, 1e-4, 1)), FR0, 12.5)
    D["tf"] = tf
    return D

def make_stars():
    r, phi, z, inarm = disc_sample(N_DISC, 0.8, RNG)
    rb = np.abs(RNG.normal(0, 6.5, N_BULGE)); pb = RNG.random(N_BULGE) * 2 * math.pi; cb = RNG.uniform(-1, 1, N_BULGE)
    xb = rb * np.sqrt(1 - cb * cb) * np.cos(pb); yb = rb * np.sqrt(1 - cb * cb) * np.sin(pb); zb = rb * cb * 0.55
    rh = 20 + RNG.random(N_HALO) * 160; ph = RNG.random(N_HALO) * 2 * math.pi; ch = RNG.uniform(-1, 1, N_HALO)
    xh = rh * np.sqrt(1 - ch * ch) * np.cos(ph); yh = rh * np.sqrt(1 - ch * ch) * np.sin(ph); zh = rh * ch * 0.7
    x = np.concatenate([r * np.cos(phi), xb, xh]); y = np.concatenate([r * np.sin(phi), yb, yh]); zz = np.concatenate([z, zb, zh])
    kind = np.concatenate([np.where(inarm, 1, 0), np.full(N_BULGE, 2), np.full(N_HALO, 3)]); n = len(x)
    temp = np.where(kind == 1, RNG.choice([0, 1, 2], n, p=[0.45, 0.4, 0.15]), np.where(kind == 2, RNG.choice([2, 3], n, p=[0.35, 0.65]), RNG.choice([1, 2, 3], n)))
    pal = np.array([[0.45, 0.62, 1.0], [0.85, 0.9, 1.0], [1.0, 0.8, 0.55], [1.0, 0.55, 0.3]], np.float32)
    col = pal[temp] * (0.9 + 0.2 * RNG.random((n, 1)))
    lum = np.exp(RNG.normal(-0.3, 1.25, n)) * np.where(kind == 2, 0.6, 1.0) * np.where(kind == 3, 0.5, 1.0)
    rad = 0.012 + 0.02 * RNG.random(n) ** 4
    hii = (kind == 1) & (RNG.random(n) < 0.012); col[hii] = (1.0, 0.42, 0.62); lum[hii] *= 2.2; rad[hii] *= 1.8
    return burst_params(dict(r0=np.hypot(x, y), phi0=np.arctan2(y, x), z0=zz, col=col.astype(np.float32),
                             lum=lum.astype(np.float32), rad=rad.astype(np.float32)), RNG)

S = make_stars(); NS = len(S["r0"])

# film stars: a sparser population that follows the same galaxy; near the camera they are glass screens
NFILM = 16000
FRG = np.random.default_rng(777)
fr_r, fr_phi, fr_z, _ = disc_sample(NFILM, 0.9, FRG)
F = dict(r0=fr_r, phi0=fr_phi, z0=fr_z * 0.8)
HR = 34.0; HPHI = float(arm_phase(HR)) + 0.02                         # the hero: the film we open on
F["r0"][0], F["phi0"][0], F["z0"][0] = HR, HPHI, 0.25
ASPECTS = np.array([16 / 9, 16 / 9, 16 / 9, 16 / 9, 4 / 3, 1.0, 9 / 16, 2.39])
F["asp"] = ASPECTS[FRG.integers(0, len(ASPECTS), NFILM)]; F["asp"][0] = 16 / 9
F["w"] = np.where(F["asp"] < 1, 0.26, 0.38) * (0.8 + 0.6 * FRG.random(NFILM)); F["w"][0] = 0.40
import json as _json
NAI = len(_json.load(open(os.path.join(ROOT, "assets/films-ai.json")))["films"])
_kr = FRG.random(NFILM)
F["ai"] = _kr < 0.38; F["real"] = (_kr >= 0.38) & (_kr < 0.62); F["ai"][0] = False; F["real"][0] = False
F["row"] = np.where(F["ai"], FRG.integers(0, NAI, NFILM), np.where(F["real"], FRG.integers(0, 41, NFILM), FRG.integers(0, 28, NFILM))); F["row"][0] = 27   # earth
F["ph"] = FRG.random(NFILM) * 16
q = FRG.normal(size=(NFILM, 4)); q /= np.linalg.norm(q, axis=1, keepdims=True); F["q"] = q
F = burst_params(F, FRG)
F["col"] = np.tile(np.array([[0.9, 0.92, 1.0]], np.float32), (NFILM, 1)); F["lum"] = (2.5 + 2.0 * FRG.random(NFILM)).astype(np.float32)
F["rad"] = np.full(NFILM, 0.03, np.float32)

def body_pos(D, t):
    """positions of a population (stars or film stars) at t: rotation → implosion → burst → flatten"""
    r0, p0, z0 = D["r0"], D["phi0"], D["z0"]
    th = p0 + omega(r0) * min(t, T_BURST) + spin_v(t)
    x, y, z = r0 * np.cos(th), r0 * np.sin(th), np.array(z0, float)
    if t > 7.2 and t < T_BURST:
        im = e_in(seg(t, D["imp0"], T_BURST))
        th2 = th + 5.0 * im; rr = r0 * (1 - im)
        x, y, z = rr * np.cos(th2), rr * np.sin(th2), z * (1 - im)
    if t >= T_BURST:
        tt = np.minimum(t, D["tf"]); dist = D["sp"] * 0.6 * (1 - np.exp(-(tt - T_BURST) / 0.6))
        ce = np.cos(D["el"])
        x = dist * ce * np.cos(D["az"]); y = dist * ce * np.sin(D["az"]); z = dist * np.sin(D["el"])
        fl = e_out(seg(t, D["tf"], D["tf"] + 0.15))
        slide = 1.2 * (1 - np.exp(-np.maximum(0, t - D["tf"]) / 0.3)) * (t > D["tf"])
        x = x + slide * np.cos(D["az"]) * fl; y = y + slide * np.sin(D["az"]) * fl; z = z * (1 - fl)
    return np.stack([x, y, z], 1)

# ---------------------------------------------------------------- the camera: (pos, target, roll, fov, focus, fstop) at t
def hero_pos(t): return body_pos({k: F[k][:1] for k in F}, t)[0]
O_VIEW = np.array([0.0, -178.0, 112.0])
DIR0 = nrm([-math.sin(HPHI) * 0.7 + math.cos(HPHI) * 0.25, math.cos(HPHI) * 0.7 + math.sin(HPHI) * 0.25, 0.35])

def arm_point(r, t, side=0.10, zz=2.0):
    ph = float(arm_phase(r)) + side + float(omega(r)) * t
    return np.array([r * math.cos(ph), r * math.sin(ph), zz])

def sph(az, el, d): return d * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
def e_el(az, el): return np.array([-math.sin(el) * math.cos(az), -math.sin(el) * math.sin(az), math.cos(el)])   # "up" of a camera looking at the core
AZ0, EL0, D0 = -math.pi / 2, math.radians(32.2), 210.3
S0 = sph(AZ0, EL0, D0)                                                # the overview: where the pull-back ends and the dive starts
T_PULL = 4.2
def ease_pull(s):
    """0→1, zero slope at both ends; in log-distance space it brakes like (1 − s)^3, so the real speed glides to a stop"""
    s = float(clamp(s)); sm = s * s * (3 - 2 * s); q = 1 - (1 - s) ** 4
    return sm * (1 - s) + q * s

def cam_pre(t):
    """→ pos, forward, up hint, roll, fov, focus, f-stop"""
    if t < T_PULL:
        H = hero_pos(t); s = seg(t, 0.15, T_PULL)
        d0, d1 = 0.78, float(np.linalg.norm(S0 - hero_pos(T_PULL)))
        d = d0 * (d1 / d0) ** ease_pull(s)
        w = float(smooth(seg(t, 0.5, 3.6))); dr = slerp_dir(DIR0, S0 - H, w)
        pos = H + dr * d
        tgt = lerp(H, CORE, float(smooth(seg(t, 1.3, 3.8))))
        fwd = nrm(tgt - pos)
        up = nrm(lerp(np.array([0, 0, 1.0]), e_el(AZ0, EL0), float(smooth(seg(t, 3.0, T_PULL)))))
        fov = lerp(38.0, 50.0, float(smooth(seg(t, 0.4, 3.9))))
        focus = float(np.linalg.norm(pos - H)); fstop = lerp(1.8, 11.0, float(smooth(seg(t, 0.2, 2.6))))
        return pos, fwd, up, 0.0, fov, focus, fstop
    u = float(seg(t, T_PULL, T_BURST))
    dist = D0 * (13.0 / D0) ** float(smooth(u) * 0.55 + u ** 1.6 * 0.45)
    el = math.radians(lerp(32.2, 89.0, float(smooth(seg(t, 4.35, 6.9)))))
    az = AZ0 - 1.2 * VK * u ** 1.5
    pos = sph(az, el, dist); fwd = nrm(CORE - pos); up = e_el(az, el)
    roll = VK * (0.6 * float(smooth(seg(t, 4.4, 5.5))) + 2.2 * float(smooth(seg(t, 5.0, 8.4))) * float(seg(t, 5.0, 8.0)) ** 0.6)
    fov = lerp(50.0, 50.0 + 50.0 * VK, float(smooth(seg(t, 5.0, 7.95))))
    return pos, fwd, up, roll, fov, dist, 16.0

POST = None
def cam_post(t):
    global POST
    if POST is None:
        p8, f8w, up8, r8, fov8, _, _ = cam_pre(T_BURST - 1e-4)
        k = [(8.0, p8), (8.35, np.array([0, -6.0, 36.0])), (9.2, np.array([0, -40.0, 44.0])), (10.4, np.array([0, -40.0, 23.0])),
             (13.8, np.array([0, -37.0, 21.0])), (17.9, np.array([0, -31.0, 18.0])), (19.15, np.array([0, 2.0, 15.0])), (23.0, np.array([0, 2.0, 12.5]))]
        POST = ([track([(a, b[i]) for a, b in k]) for i in range(3)], r8, up8,
                track([(8.0, fov8), (8.3, 58.0), (9.0, 50.0), (10.4, 46.0), (17.9, 44.0), (19.15, 50.0), (23.0, 50.0)]))
    pk, r8, up8, fk = POST
    pos = np.array([f(t) for f in pk])
    tgt = np.array([0.0, lerp(lerp(0.0, 34.0, float(smooth(seg(t, 9.0, 10.6)))), 2.6, float(smooth(seg(t, 17.9, 19.15)))), 0.0])
    fwd = nrm(tgt - pos)
    # leaving the straight-down view: keep the dive's up vector, then hand over to world up once the camera has tilted
    up = nrm(lerp(up8, np.array([0, 0, 1.0]), float(smooth(seg(t, 8.0, 9.3)))))
    if t > 17.9: up = nrm(lerp(np.array([0, 0, 1.0]), np.array([0, 1.0, 0]), float(smooth(seg(t, 17.9, 19.15)))))
    roll = lerp(r8, 2 * math.pi, float(smooth(seg(t, 8.0, 9.9))))
    return pos, fwd, up, roll, fk(t), float(np.linalg.norm(pos - tgt)), 16.0

def smooth_noise(t, seed, freqs):
    return sum(math.sin(t * f * 2 * math.pi + seed * 1.7 + i * 2.1) / (i + 1) for i, f in enumerate(freqs)) / 1.83

def cam_at(t):
    pos, fwd, up, roll, fov, focus, fstop = cam_pre(t) if t < T_BURST else cam_post(t)
    if t >= T_BURST:                                                       # the blast: a decaying, smooth shake (no per-frame jitter)
        a = 0.45 * VK * math.exp(-(t - T_BURST) / 0.32)
        pos = pos + a * np.array([smooth_noise(t, 1, (5.1, 8.3, 12.2)), smooth_noise(t, 2, (4.7, 7.9, 11.6)), smooth_noise(t, 3, (5.5, 9.1, 13.0))])
    return pos, fwd, up, roll, fov, focus, fstop

# ---------------------------------------------------------------- materials, volumes, compositor
VOL = {}
def image(path):
    im = bpy.data.images.load(os.path.join(ROOT, path)); im.colorspace_settings.name = "sRGB"; return im

def build_volume(sc):
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=124, depth=22, location=(0, 0, 0))
    ob = bpy.context.active_object; ob.name = "galaxy-volume"
    mat = bpy.data.materials.new("galaxy-volume"); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    cd = nt.nodes.new("ShaderNodeCameraData")
    env = {"x": sx.outputs[0], "y": sx.outputs[1], "z": sx.outputs[2], "vd": cd.outputs["View Distance"]}
    for k, v in (("T", 0.0), ("GLOW", 1.0), ("DUST", 1.0), ("SQUEEZE", 1.0), ("SPIN", 0.0)):
        n = nt.nodes.new("ShaderNodeValue"); n.name = k; n.outputs[0].default_value = v; VOL[k] = n; env[k.lower()] = n.outputs[0]
    bind(nt, env, [
        ("r", "sqrt(x * x + y * y) * squeeze + 0.001"),
        ("phi0", "atan2(y, x) - 1.65 / max(r, 6) * t - spin"),
        ("s", f"log(r / 4) / {math.tan(PITCH):.6f}"),
        ("a2", "cos(2 * (phi0 - s))"),
        ("arms", "pow(max((1 + a2) / 2, 0), 3) + 0.45 * pow(max((1 - a2) / 2, 0), 5)"),
        ("radial", "exp(-r / 21) * (1 - smooth(80, 120, r))"),
        ("vert", "exp(-abs(z) / (0.55 + 0.022 * r))"),
        ("n1", "noise(x, y, z * 2.5, 0.075, 6, 0.62)"),
        ("n2", "noise(x + 31, y - 17, z * 3, 0.16, 5, 0.7)"),
        ("n3", "noise(x - 7, y + 41, z * 2, 0.5, 3, 0.5)"),
        ("core", "exp(-(r * r + z * z * 5) / 34)"),
        ("hii", "smooth(0.68, 0.8, n3) * pow(max((1 + a2) / 2, 0), 6) * radial * vert * 9"),
        ("g", "glow * (radial * vert * (0.08 + 1.7 * arms) * pow(n1 + 0.15, 2.4) * 0.9 + core * 2.6)"),
        ("d2", "cos(2 * (phi0 - s + 0.42))"),
        ("dd", "dust * pow(max((1 + d2) / 2, 0), 7) * smooth(5, 14, r) * (1 - smooth(60, 100, r)) * exp(-abs(z) / 0.45) * smooth(0.3, 0.72, n2) * 7"),
        ("warm", "exp(-r / 12)"),
        ("cr", "mix(0.42, 1.0, warm) + hii * 0.9"), ("cg", "mix(0.55, 0.7, warm) + hii * 0.3"), ("cb", "mix(1.0, 0.4, warm) + hii * 0.5"),
        ("strength", "g * (1 + hii * 1.5) * smooth(4, 60, vd)"),
    ], Compiler(nt))
    cc = nt.nodes.new("ShaderNodeCombineColor")
    for i, k in enumerate(("cr", "cg", "cb")): nt.links.new(env[k], cc.inputs[i])
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(cc.outputs[0], em.inputs["Color"]); nt.links.new(env["strength"], em.inputs["Strength"])
    ab = nt.nodes.new("ShaderNodeVolumeAbsorption"); ab.inputs["Color"].default_value = (0.55, 0.36, 0.25, 1); nt.links.new(env["dd"], ab.inputs["Density"])
    ad = nt.nodes.new("ShaderNodeAddShader"); nt.links.new(em.outputs[0], ad.inputs[0]); nt.links.new(ab.outputs[0], ad.inputs[1])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(ad.outputs[0], out.inputs["Volume"])
    ob.data.materials.append(mat); VOL["ob"] = ob

def build_nova(sc):
    """the supernova: a sphere of glowing, turbulent gas whose shell races outward and cools"""
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(0, 0, 0))
    ob = bpy.context.active_object; ob.name = "nova"
    mat = bpy.data.materials.new("nova"); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    env = {"x": sx.outputs[0], "y": sx.outputs[1], "z": sx.outputs[2]}
    for k, v in (("AGE", 0.0), ("HEAT", 0.0), ("TEMP", 9000.0)):
        n = nt.nodes.new("ShaderNodeValue"); n.name = k; n.outputs[0].default_value = v; VOL["N" + k] = n; env[k.lower()] = n.outputs[0]
    bind(nt, env, [
        ("rl", "sqrt(x * x + y * y + z * z)"),
        ("turb", "noise(x, y, z, 2.6, 10, 0.68, age * 0.9)"),
        ("fil", "pow(smooth(0.42, 0.78, turb), 2)"),
        ("shell", "smooth(mix(0.0, 0.72, smooth(0, 0.35, age)), 0.9, rl + 0.3 * (turb - 0.5)) * (1 - smooth(0.88, 1.0, rl + 0.1 * (turb - 0.5)))"),
        ("dens", "heat * shell * (0.08 + 2.4 * fil)"),
    ], Compiler(nt))
    bind(nt, env, [("hue", "smooth(0.35, 0.65, noise(x + 9, y - 3, z, 1.3, 4, 0.6, age * 0.6))"),
                   ("outer", "smooth(0.45, 0.85, rl)"),
                   ("fr", "mix(1.0, mix(0.95, 0.2, hue), outer)"), ("fg", "mix(1.0, mix(0.25, 0.75, hue), outer)"), ("fb", "mix(1.0, mix(0.2, 0.85, hue), outer)")], Compiler(nt))
    bb = nt.nodes.new("ShaderNodeBlackbody"); nt.links.new(env["temp"], bb.inputs[0])
    tint = nt.nodes.new("ShaderNodeCombineColor")
    for i, k in enumerate(("fr", "fg", "fb")): nt.links.new(env[k], tint.inputs[i])
    mixc = nt.nodes.new("ShaderNodeMix"); mixc.data_type = "RGBA"; mixc.blend_type = "MULTIPLY"; mixc.inputs["Factor"].default_value = 1.0
    nt.links.new(bb.outputs[0], mixc.inputs["A"]); nt.links.new(tint.outputs[0], mixc.inputs["B"])
    em = nt.nodes.new("ShaderNodeEmission"); nt.links.new(mixc.outputs["Result"], em.inputs["Color"]); nt.links.new(env["dens"], em.inputs["Strength"])
    out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs["Volume"])
    ob.data.materials.append(mat); VOL["nova"] = ob

def emission_mat(name, strength_attr=None, color=(1, 1, 1), k=1.0, col_attr=None):
    mat = bpy.data.materials.new(name); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission"); oo = nt.nodes.new("ShaderNodeOutputMaterial")
    if col_attr:
        ac = nt.nodes.new("ShaderNodeAttribute"); ac.attribute_type = "GEOMETRY"; ac.attribute_name = col_attr; nt.links.new(ac.outputs["Color"], em.inputs["Color"])
    else: em.inputs["Color"].default_value = (*color, 1)
    if strength_attr:
        al = nt.nodes.new("ShaderNodeAttribute"); al.attribute_type = "GEOMETRY"; al.attribute_name = strength_attr
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = k
        nt.links.new(al.outputs["Fac"], mul.inputs[0]); nt.links.new(mul.outputs[0], em.inputs["Strength"])
    else: em.inputs["Strength"].default_value = k
    nt.links.new(em.outputs[0], oo.inputs["Surface"])
    return mat

def points_object(sc, name, n, mat):
    me = bpy.data.meshes.new(name); me.vertices.add(n)
    for a, kind in (("radius", "FLOAT"), ("lum", "FLOAT")): me.attributes.new(a, kind, "POINT")
    me.attributes.new("col", "FLOAT_COLOR", "POINT"); me.attributes.new("velocity", "FLOAT_VECTOR", "POINT")
    ob = bpy.data.objects.new(name, me); sc.collection.objects.link(ob)
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket(name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket(name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); go = ng.nodes.new("NodeGroupOutput"); m2p = ng.nodes.new("GeometryNodeMeshToPoints")
    ra = ng.nodes.new("GeometryNodeInputNamedAttribute"); ra.data_type = "FLOAT"; ra.inputs["Name"].default_value = "radius"
    sm = ng.nodes.new("GeometryNodeSetMaterial"); sm.inputs["Material"].default_value = mat
    ng.links.new(gi.outputs[0], m2p.inputs["Mesh"]); ng.links.new(ra.outputs["Attribute"], m2p.inputs["Radius"])
    ng.links.new(m2p.outputs[0], sm.inputs["Geometry"]); ng.links.new(sm.outputs[0], go.inputs[0])
    ob.modifiers.new(name, "NODES").node_group = ng
    return ob, me

def build_grid_lines(sc):
    """amber hairlines of the grid, drawn only behind the scan (y < SCAN)"""
    rows = int(math.ceil(NC / GC)); xs = (np.arange(GC + 1) - GC / 2) * CW; ys = -24.0 - CH / 2 + np.arange(rows + 1) * CH
    v, f = [], []
    def quad(a, b, c_, d_): n = len(v); v.extend([a, b, c_, d_]); f.append((n, n + 1, n + 2, n + 3))
    lw = 0.035
    for x in xs: quad((x - lw, ys[0], 0.0), (x + lw, ys[0], 0.0), (x + lw, ys[-1], 0.0), (x - lw, ys[-1], 0.0))
    for y in ys: quad((xs[0], y - lw, 0.0), (xs[-1], y - lw, 0.0), (xs[-1], y + lw, 0.0), (xs[0], y + lw, 0.0))
    me = bpy.data.meshes.new("grid"); me.from_pydata(v, [], f); me.update()
    mat = bpy.data.materials.new("grid"); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
    tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sx.inputs[0])
    env = {"y": sx.outputs[1]}
    for k in ("SCAN", "GRIDK"):
        n = nt.nodes.new("ShaderNodeValue"); n.name = k; VOL[k] = n; env[k.lower()] = n.outputs[0]
    bind(nt, env, [("m", "gridk * ((1 - smooth(scan - 1.0, scan + 0.4, y)) * 0.5 + exp(-abs(y - scan) / 0.8) * 4)")], Compiler(nt))
    em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (1.0, 0.62, 0.12, 1); nt.links.new(env["m"], em.inputs["Strength"])
    oo = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], oo.inputs["Surface"]); me.materials.append(mat)
    ob = bpy.data.objects.new("grid", me); ob.location.z = 0.006; sc.collection.objects.link(ob); VOL["grid"] = ob

def build_world(sc):
    """black to the camera; to reflections, a soft studio of light (warm key upper right, cool fill left) so the glass shines"""
    w = bpy.data.worlds.new("void"); w.use_nodes = True; nt = w.node_tree; nt.nodes.clear(); sc.world = w
    tc = nt.nodes.new("ShaderNodeTexCoord"); sx = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sx.inputs[0])
    env = {"x": sx.outputs[0], "y": sx.outputs[1], "z": sx.outputs[2]}
    bind(nt, env, [("key", "pow(max(0.6 * x + 0.3 * y + 0.75 * z, 0), 28) * 9"), ("fill", "pow(max(-0.8 * x + 0.2 * z, 0), 12) * 1.4"), ("top", "smooth(0.6, 0.95, z) * 0.25"),
                   ("cr", "key * 1.0 + fill * 0.55 + top * 0.8"), ("cg", "key * 0.86 + fill * 0.7 + top * 0.85"), ("cb", "key * 0.7 + fill * 1.0 + top * 1.0")], Compiler(nt))
    cc = nt.nodes.new("ShaderNodeCombineColor")
    for i, k in enumerate(("cr", "cg", "cb")): nt.links.new(env[k], cc.inputs[i])
    bg = nt.nodes.new("ShaderNodeBackground"); nt.links.new(cc.outputs[0], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
    black = nt.nodes.new("ShaderNodeBackground"); black.inputs["Strength"].default_value = 0.0
    lp = nt.nodes.new("ShaderNodeLightPath"); mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Glossy Ray"], mx.inputs[0]); nt.links.new(black.outputs[0], mx.inputs[1]); nt.links.new(bg.outputs[0], mx.inputs[2])
    out = nt.nodes.new("ShaderNodeOutputWorld"); nt.links.new(mx.outputs[0], out.inputs["Surface"])

def build_compositor(sc):
    ng = bpy.data.node_groups.new("comp", "CompositorNodeTree")
    ng.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    rl = ng.nodes.new("CompositorNodeRLayers"); go = ng.nodes.new("NodeGroupOutput"); gl = ng.nodes.new("CompositorNodeGlare")
    for v in ("Bloom", "BLOOM"):
        try: gl.inputs["Type"].default_value = v; break
        except Exception: pass
    gl.inputs["Threshold"].default_value = 1.6; gl.inputs["Strength"].default_value = 0.5; gl.inputs["Size"].default_value = 0.8
    VOL["glare"] = gl
    st = ng.nodes.new("CompositorNodeGlare")
    for v in ("Streaks", "STREAKS"):
        try: st.inputs["Type"].default_value = v; break
        except Exception: pass
    for k, v in (("Threshold", 3.0), ("Strength", 0.0), ("Streaks", 2), ("Size", 0.9)):
        try: st.inputs[k].default_value = v
        except Exception: pass
    VOL["streak"] = st
    ng.links.new(rl.outputs["Image"], gl.inputs["Image"]); ng.links.new(gl.outputs["Image"], st.inputs["Image"]); ng.links.new(st.outputs["Image"], go.inputs[0])
    sc.compositing_node_group = ng; sc.render.use_compositing = True

# ---------------------------------------------------------------- cards: glass slabs with a film screen inside
# a veil of films the camera falls through (5–7.6 s): placed beside its descending path at the moment it passes,
# then carried by the galaxy's spin, so they swirl past the lens; afterwards they collapse, burst and flatten like the rest
NV = 260
VRG = np.random.default_rng(4242)
_tv = 5.0 + 2.6 * VRG.random(NV); _pts = []
for _i in range(NV):
    _p = cam_pre(float(_tv[_i]))[0]; _fwd = nrm(-_p)
    _side = nrm(np.cross(_fwd, [0, 0, 1.0]) if abs(_fwd[2]) < 0.99 else np.cross(_fwd, [1.0, 0, 0])); _up = np.cross(_side, _fwd)
    _a = VRG.random() * 2 * math.pi; _rad = 1.6 + 5.0 * VRG.random()
    _pts.append(_p + _fwd * (2.0 + 6.0 * VRG.random()) + (_side * math.cos(_a) + _up * math.sin(_a)) * _rad)
_pts = np.array(_pts); _r = np.hypot(_pts[:, 0], _pts[:, 1])
V_ = dict(r0=_r, phi0=np.arctan2(_pts[:, 1], _pts[:, 0]) - omega(_r) * _tv - np.array([spin_v(float(x)) for x in _tv]), z0=_pts[:, 2])
V_["asp"] = ASPECTS[VRG.integers(0, len(ASPECTS), NV)]; V_["w"] = np.where(V_["asp"] < 1, 0.34, 0.5) * (0.8 + 0.6 * VRG.random(NV))
_vk = VRG.random(NV); V_["ai"] = _vk < 0.45; V_["real"] = (_vk >= 0.45) & (_vk < 0.65)
V_["row"] = np.where(V_["ai"], VRG.integers(0, NAI, NV), np.where(V_["real"], VRG.integers(0, 41, NV), VRG.integers(0, 28, NV))); V_["ph"] = VRG.random(NV) * 16
_q = VRG.normal(size=(NV, 4)); V_["q"] = _q / np.linalg.norm(_q, axis=1, keepdims=True)
V_ = burst_params(V_, VRG)
V_["col"] = np.tile(np.array([[0.9, 0.92, 1.0]], np.float32), (NV, 1)); V_["lum"] = (2.5 + 2.0 * VRG.random(NV)).astype(np.float32); V_["rad"] = np.full(NV, 0.03, np.float32)
for _k in list(F.keys()):
    if _k in V_: F[_k] = np.concatenate([F[_k], V_[_k]])
NFILM = len(F["r0"])

NC = NFILM
def build_cards(sc):
    proc, real, hero, ai = image("assets/films-proc.png"), image("assets/films.jpg"), image("assets/hero-earth.png"), image("assets/films-ai.jpg")
    proc_s, real_s, ai_s = image("assets/films-proc-small.png"), image("assets/films-small.jpg"), image("assets/films-ai-small.jpg")
    verts = np.zeros((NC * 4, 3)); faces = [(4 * i, 4 * i + 1, 4 * i + 2, 4 * i + 3) for i in range(NC)]
    me = bpy.data.meshes.new("screens"); me.from_pydata(verts.tolist(), [], faces); me.update()
    me.uv_layers.new(name="UVMap"); me.uv_layers.new(name="UVNext"); me.attributes.new("fmix", "FLOAT", "POINT"); me.attributes.new("vis", "FLOAT", "POINT"); me.attributes.new("velocity", "FLOAT_VECTOR", "POINT")
    me.attributes.new("gray", "FLOAT", "POINT"); me.attributes.new("amber", "FLOAT", "POINT")
    for img, nm in ((proc, "screen-proc"), (real, "screen-real"), (hero, "screen-hero"), (ai, "screen-ai"), (proc_s, "screen-proc-s"), (real_s, "screen-real-s"), (ai_s, "screen-ai-s")):
        mat = bpy.data.materials.new(nm); mat.use_nodes = True; nt = mat.node_tree; nt.nodes.clear()
        t0 = nt.nodes.new("ShaderNodeTexImage"); t0.image = img; t0.interpolation = "Cubic"
        t1 = nt.nodes.new("ShaderNodeTexImage"); t1.image = img; t1.interpolation = "Cubic"
        m0 = nt.nodes.new("ShaderNodeUVMap"); m0.uv_map = "UVMap"; m1 = nt.nodes.new("ShaderNodeUVMap"); m1.uv_map = "UVNext"
        nt.links.new(m0.outputs["UV"], t0.inputs["Vector"]); nt.links.new(m1.outputs["UV"], t1.inputs["Vector"])
        af = nt.nodes.new("ShaderNodeAttribute"); af.attribute_type = "GEOMETRY"; af.attribute_name = "fmix"
        tx = nt.nodes.new("ShaderNodeMix"); tx.data_type = "RGBA"; nt.links.new(af.outputs["Fac"], tx.inputs["Factor"])
        nt.links.new(t0.outputs["Color"], tx.inputs["A"]); nt.links.new(t1.outputs["Color"], tx.inputs["B"])
        av = nt.nodes.new("ShaderNodeAttribute"); av.attribute_type = "GEOMETRY"; av.attribute_name = "vis"
        ag = nt.nodes.new("ShaderNodeAttribute"); ag.attribute_type = "GEOMETRY"; ag.attribute_name = "gray"
        aa = nt.nodes.new("ShaderNodeAttribute"); aa.attribute_type = "GEOMETRY"; aa.attribute_name = "amber"
        bw = nt.nodes.new("ShaderNodeRGBToBW"); nt.links.new(tx.outputs["Result"], bw.inputs[0])
        mg = nt.nodes.new("ShaderNodeMix"); mg.data_type = "RGBA"; nt.links.new(ag.outputs["Fac"], mg.inputs["Factor"])
        nt.links.new(tx.outputs["Result"], mg.inputs["A"]); nt.links.new(bw.outputs[0], mg.inputs["B"])
        am = nt.nodes.new("ShaderNodeMix"); am.data_type = "RGBA"; am.blend_type = "MULTIPLY"; am.inputs["Factor"].default_value = 1.0
        nt.links.new(bw.outputs[0], am.inputs["A"]); am.inputs["B"].default_value = (1.0, 0.62, 0.12, 1)
        m2 = nt.nodes.new("ShaderNodeMix"); m2.data_type = "RGBA"; nt.links.new(aa.outputs["Fac"], m2.inputs["Factor"])
        nt.links.new(mg.outputs["Result"], m2.inputs["A"]); nt.links.new(am.outputs["Result"], m2.inputs["B"])
        mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = 2.2
        em = nt.nodes.new("ShaderNodeEmission"); oo = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(m2.outputs["Result"], em.inputs["Color"]); nt.links.new(av.outputs["Fac"], mul.inputs[0]); nt.links.new(mul.outputs[0], em.inputs["Strength"])
        nt.links.new(em.outputs[0], oo.inputs["Surface"]); me.materials.append(mat)
    me.polygons.foreach_set("material_index", card_material(0.0, np.zeros(3), 50.0, None))
    ob = bpy.data.objects.new("screens", me); sc.collection.objects.link(ob)
    sv = np.zeros((NC * 8, 3)); sf = []
    for i in range(NC):
        b = 8 * i
        sf += [(b, b + 1, b + 2, b + 3), (b + 7, b + 6, b + 5, b + 4), (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2), (b + 2, b + 6, b + 7, b + 3), (b + 3, b + 7, b + 4, b)]
    ms = bpy.data.meshes.new("slabs"); ms.from_pydata(sv.tolist(), [], sf); ms.update(); ms.attributes.new("velocity", "FLOAT_VECTOR", "POINT")
    mat = bpy.data.materials.new("glass"); mat.use_nodes = True; nt = mat.node_tree
    bs = nt.nodes["Principled BSDF"]; bs.inputs["Base Color"].default_value = (0.92, 0.96, 1.0, 1); bs.inputs["Roughness"].default_value = 0.03
    bs.inputs["IOR"].default_value = 1.5; bs.inputs["Transmission Weight"].default_value = 1.0
    bv = nt.nodes.new("ShaderNodeBevel"); bv.inputs["Radius"].default_value = 0.012; bv.samples = 6
    nt.links.new(bv.outputs["Normal"], bs.inputs["Normal"])
    ms.materials.append(mat)
    os_ = bpy.data.objects.new("slabs", ms); sc.collection.objects.link(os_)
    return me, ms

def quat_mul(a, b):
    w1, x1, y1, z1 = a.T; w2, x2, y2, z2 = b.T
    return np.stack([w1*w2 - x1*x2 - y1*y2 - z1*z2, w1*x2 + x1*w2 + y1*z2 - z1*y2, w1*y2 - x1*z2 + y1*w2 + z1*x2, w1*z2 + x1*y2 - y1*x2 + z1*w2], 1)
def quat_axes(q):
    w, x, y, z = q.T
    R = np.stack([1 - 2*(y*y + z*z), 2*(x*y + z*w), 2*(x*z - y*w)], 1)
    U = np.stack([2*(x*y - z*w), 1 - 2*(x*x + z*z), 2*(y*z + x*w)], 1)
    N = np.stack([2*(x*z + y*w), 2*(y*z - x*w), 1 - 2*(x*x + y*y)], 1)
    return R, U, N

def card_frame(t, cam):
    """→ centres, right, up, normal, width, height, visibility for every card at t"""
    c = body_pos(F, t)
    spin = omega(F["r0"]) * min(t, T_BURST) + spin_v(t)
    qz = np.stack([np.cos(spin / 2), np.zeros(NC), np.zeros(NC), np.sin(spin / 2)], 1)
    q = quat_mul(qz, F["q"])
    if t >= T_BURST:                                                       # tumbling shards, then flat on the plane
        tb = min(t, 13.0) - T_BURST; ang = (F["ph"] - 8) * 1.2 * (1 - math.exp(-tb / 0.6))
        qt = np.stack([np.cos(ang / 2), np.sin(ang / 2) * 0.6, np.sin(ang / 2) * 0.8, np.zeros(NC)], 1)
        q = quat_mul(qt, q)
        fl = e_out(seg(t, F["tf"], F["tf"] + 0.15))[:, None]
        flat = np.stack([np.cos(F["az"] / 2), np.zeros(NC), np.zeros(NC), np.sin(F["az"] / 2)], 1)
        q = q * (1 - fl) + flat * fl * np.sign(np.sum(q * flat, 1, keepdims=True) + 1e-9)
        q /= np.linalg.norm(q, axis=1, keepdims=True)
    R, U, N = quat_axes(q)
    if t < 5.0:                                                            # the hero faces the opening camera
        sd = nrm(np.cross([0, 0, 1], DIR0)); n0 = nrm(DIR0 + 0.2 * sd - 0.08 * np.array([0, 0, 1.0])); r0 = nrm(np.cross([0, 0, 1], n0)); u0 = np.cross(n0, r0)
        R[0], U[0], N[0] = r0, u0, n0
    w = F["w"].copy(); h = w / F["asp"]
    d = np.linalg.norm(c - cam, axis=1); flat = np.zeros(NC); F["_sn"] = np.zeros(NC)
    if t < T_BURST: vis = (1 - sstep(26, 44, d)) * sstep(0.12, 0.3, d)
    else:
        fl = e_out(seg(t, F["tf"], F["tf"] + 0.25)); flat = fl
        vis = ((1 - sstep(170, 260, d)) * sstep(0.2, 0.5, d)) * (1 + 0.5 * fl); g = 1.25 + 3.2 * fl; w = w * g; h = h * g
        c = c + np.stack([np.zeros(NC), np.zeros(NC), 0.004 * (np.arange(NC) % 41) * fl], 1)
        vis = vis * lerp(1.0, 0.32, float(smooth(seg(t, 10.4, 11.3))))       # a quiet bed under the question
        sn = 1 - np.power(2.0, -10 * seg(t, F["ts"], F["ts"] + 0.5)); sn = np.where(t >= F["ts"], sn, 0.0)
        if t >= SCAN0:
            c = c * (1 - sn[:, None]) + np.stack([F["sx"], F["sy"], np.full(NC, 0.003)], 1) * sn[:, None]
            R = R * (1 - sn[:, None]) + np.array([1.0, 0, 0]) * sn[:, None]; U = U * (1 - sn[:, None]) + np.array([0, 1.0, 0]) * sn[:, None]
            R /= np.linalg.norm(R, axis=1, keepdims=True); U /= np.linalg.norm(U, axis=1, keepdims=True)
            w = lerp(w, CW * 0.86, sn); h = lerp(h, CW * 0.86 * 9 / 16, sn)
            pulse = np.exp(-np.maximum(0, t - F["ts"]) / 0.22) * (t >= F["ts"])
            vis = vis * (1 - sn) + sn * (0.95 + 0.6 * pulse) * lerp(1.0, 0.62, float(smooth(seg(t, 15.6, 16.6))))
            col = float(smooth(seg(t, 18.55, 19.1)))                              # rows collapse into lines of "text"
            h = h * lerp(1.0, 0.1, col); w = w * lerp(1.0, 0.45 + 0.55 * 0.5 * (1 + np.sin(F["sy"] * 7.1)), col)
            vis = vis * lerp(1.0, 1.25, col)                                    # the lines glow: the terminal must not sit on black
        F["_sn"] = sn
    return c, R, U, N, w, h, vis, flat

def card_verts(t, cam):
    c, R, U, N, w, h, vis, flat = card_frame(t, cam)
    hw, hh, th = (w * 0.5)[:, None], (h * 0.5)[:, None], 0.016
    on = (vis > 0.002)[:, None, None]
    sq = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    scr = np.stack([c + R * hw * a + U * hh * b for a, b in sq], 1)
    sl = np.stack([c + (R * (hw + 0.012) * a + U * (hh + 0.012) * b) + N * th * s for s in (-1, 1) for a, b in sq], 1)
    slab_on = on & ((flat < 0.3) & (F["_sn"] < 0.05) & (t < 12.0))[:, None, None]                              # flattened films lose their glass: layered slabs would swallow the rays
    scr = np.where(on, scr, c[:, None, :]); sl = np.where(slab_on, sl, c[:, None, :])
    return scr.reshape(-1, 3), sl.reshape(-1, 3), vis

def card_uv(t):
    """→ UVs of the current frame, of the next frame, and the mix between them (films play smoothly, not at 8 steps a second)"""
    fpos = t * 8.0 + F["ph"]; k0 = np.floor(fpos); fm = fpos - k0
    pp = F["real"] | F["ai"]                                               # footage and AI stills ping-pong; procedural films loop
    def frame(k): m = np.mod(k, 30); return np.where(pp, np.where(m < 16, m, 30 - m), np.mod(k, 16))
    rows = np.where(F["ai"], NAI, np.where(F["real"], 41, 28))
    a = np.where(F.get("_sn", np.zeros(NC)) > 0.5, 16 / 9, F["asp"]); ta = 16 / 9
    sx = np.where(a < ta, a / ta, 1.0); sy = np.where(a < ta, 1.0, ta / a)
    corners = np.array([(-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)])
    def uv(fr, hk):
        u = (fr[:, None] + 0.5 + corners[None, :, 0] * sx[:, None] * 0.992) / 16
        v = 1 - (F["row"][:, None] + 0.5 - corners[None, :, 1] * sy[:, None] * 0.99) / rows[:, None]
        f0 = int(np.mod(hk, 16))                                           # the opening film: a 4 x 4 sheet of 1024 x 576 frames
        u[0] = ((f0 % 4) + 0.5 + corners[:, 0] * 0.996) / 4; v[0] = 1 - ((f0 // 4) + 0.5 - corners[:, 1] * 0.996) / 4
        return np.stack([u, v], 2).reshape(-1, 2)
    return uv(frame(k0), k0[0]), uv(frame(k0 + 1), k0[0] + 1), fm

def card_material(t, cam_pos, fov, vis):
    """material slot per card: 0 procedural, 1 footage, 2 the opening film, 3 AI; +4 (5, 6, 7 → 4, 5, 6 for 0, 1, 3) a 1/4-size atlas for far, small cards"""
    base = np.where(F["ai"], 3, np.where(F["real"], 1, 0)); base[0] = 2
    if t >= T_BURST:
        c = body_pos(F, t); d = np.linalg.norm(c - cam_pos, axis=1) + 1e-3
        fpx = (W / 2) / math.tan(math.radians(fov) / 2); px = F["w"] * 3.0 * fpx / d
        small = (px < 70) & (base != 2)
        base = np.where(small, np.where(base == 3, 6, base + 4), base)
    return base.astype(np.int32)

# ---------------------------------------------------------------- the harness: an amber scan sorts the films into a grid
SCAN0, SCAN1, SCANY0, SCANY1 = 14.0, 14.9, -34.0, 170.0
GC, CW, CH = 96, 2.3, 1.42
def scan_y(t): return SCANY0 + (SCANY1 - SCANY0) * float(smooth(seg(t, SCAN0, SCAN1)) ** 1.3)
_flat = body_pos(F, 12.5)
_order = np.argsort(_flat[:, 1])                       # near rows first (the camera looks toward +y)
F["sx"] = np.zeros(NC); F["sy"] = np.zeros(NC)
for r in range(int(math.ceil(NC / GC))):
    ids = _order[r * GC:(r + 1) * GC]; ids = ids[np.argsort(_flat[ids, 0])]
    F["sx"][ids] = (np.arange(len(ids)) - (GC - 1) / 2) * CW; F["sy"][ids] = -24.0 + r * CH
_ys = np.linspace(SCANY0, SCANY1, 4001); _ts = SCAN0 + (SCAN1 - SCAN0) * np.linspace(0, 1, 4001)
_scan = np.array([scan_y(x) for x in _ts])
F["ts"] = np.interp(_flat[:, 1], _scan, _ts)           # when the scan passes the film

# ---------------------------------------------------------------- sparks (supernova debris light)
NSP = 12000
SPR = np.random.default_rng(99)
SPd = SPR.normal(size=(NSP, 3)); SPd /= np.linalg.norm(SPd, axis=1, keepdims=True); SPd[:, 2] *= 0.35
SPs = 20 + 140 * SPR.random(NSP) ** 2.2; SPtau = 0.3 + 0.7 * SPR.random(NSP)
def spark_pos(t):
    tb = max(0.0, t - T_BURST); d = SPs * SPtau * (1 - np.exp(-tb / SPtau))
    return SPd * d[:, None] - np.array([0, 0, 0.6]) * tb * tb

# ---------------------------------------------------------------- build
def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"; prefs.get_devices()
    for d in prefs.devices: d.use = d.type == "METAL"
    sc.cycles.device = "GPU"
    sc.cycles.samples = int(arg("--spp", "48" if DRAFT else "64"))
    sc.cycles.use_adaptive_sampling = False; sc.cycles.use_denoising = False
    sc.cycles.seed = 20261002; sc.cycles.use_animated_seed = True
    sc.cycles.max_bounces = 12; sc.cycles.transmission_bounces = 12; sc.cycles.glossy_bounces = 4; sc.cycles.volume_bounces = 0
    sc.cycles.diffuse_bounces = 1; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
    sc.cycles.volume_step_rate = 2.0 if DRAFT else 1.0; sc.cycles.volume_max_steps = 512
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.resolution_percentage = 50 if DRAFT else 100
    sc.render.fps = FPS; sc.frame_start, sc.frame_end = 0, 689
    sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = SHUTTER
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_depth = "8"
    sc.view_settings.view_transform = "AgX"
    looks = [i.identifier for i in sc.view_settings.bl_rna.properties["look"].enum_items]
    for want in ("AgX - Punchy", "Punchy"):
        if want in looks: sc.view_settings.look = want; break
    build_world(sc)
    ob, me = points_object(sc, "stars", NS, emission_mat("star", "lum", k=3.2, col_attr="col"))
    me.attributes["col"].data.foreach_set("color", np.concatenate([S["col"], np.ones((NS, 1), np.float32)], 1).ravel())
    fob, fme = points_object(sc, "film-stars", NFILM, emission_mat("film-star", "lum", k=3.2, col_attr="col"))
    fme.attributes["col"].data.foreach_set("color", np.concatenate([F["col"], np.ones((NFILM, 1), np.float32)], 1).ravel())
    sob, sme = points_object(sc, "sparks", NSP, emission_mat("spark", "lum", k=1.0, col_attr="col"))
    build_volume(sc); build_nova(sc); build_compositor(sc)
    scr, slb = build_cards(sc)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.004, major_segments=256, minor_segments=8)
    ring = bpy.context.active_object; ring.name = "ring"
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.012, major_segments=256, minor_segments=8)
    shock = bpy.context.active_object; shock.name = "shock"
    shock.data.materials.append(emission_mat("shock", color=(0.75, 0.85, 1.0), k=0.0)); VOL["shock"] = shock
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.03, major_segments=256, minor_segments=12)
    shock2 = bpy.context.active_object; shock2.name = "shock2"
    shock2.data.materials.append(emission_mat("shock2", color=(1.0, 0.62, 0.35), k=0.0)); VOL["shock2"] = shock2
    ring.data.materials.append(emission_mat("ring", color=(1.0, 0.78, 0.5), k=0.0)); VOL["ring"] = ring
    bpy.ops.mesh.primitive_cube_add(size=1.0); bar = bpy.context.active_object; bar.name = "scan"; bar.scale = (420, 0.22, 0.05)
    bar.data.materials.append(emission_mat("scan", color=(1.0, 0.66, 0.16), k=0.0)); VOL["scan"] = bar
    build_grid_lines(sc)
    skp = np.random.default_rng(5).normal(size=(30000, 3)); skp = skp / np.linalg.norm(skp, axis=1, keepdims=True) * 1400
    kob, kme = points_object(sc, "sky", 30000, emission_mat("sky", "lum", k=1.0, col_attr="col"))
    kme.vertices.foreach_set("co", skp.astype(np.float32).ravel())
    kme.attributes["radius"].data.foreach_set("value", (0.6 + 1.4 * np.random.default_rng(6).random(30000) ** 6).astype(np.float32))
    VOL["sky_lum"] = (np.exp(np.random.default_rng(7).normal(-0.5, 1.0, 30000)) * 2.5).astype(np.float32); VOL["sky_low"] = skp[:, 2] < 0; VOL["sky_me"] = kme
    kme.attributes["lum"].data.foreach_set("value", VOL["sky_lum"])
    kme.attributes["col"].data.foreach_set("color", np.tile(np.array([0.85, 0.9, 1.0, 1.0], np.float32), 30000))
    kme.attributes["velocity"].data.foreach_set("vector", np.zeros(90000, np.float32)); kme.update()
    cam = bpy.data.cameras.new("cam"); co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
    cam.clip_start = 0.02; cam.clip_end = 5000; cam.sensor_fit = "HORIZONTAL"; cam.sensor_width = 36.0
    cam.dof.use_dof = True; cam.dof.aperture_blades = 7; cam.dof.aperture_rotation = 0.3
    key_camera(sc, co)
    return dict(sc=sc, me=me, fme=fme, sme=sme, sob=sob, scr=scr, slb=slb, co=co)

def key_camera(sc, co):
    """one keyframe per frame (and the lens, focus and f-stop): the camera's motion blur interpolates between them"""
    co.rotation_mode = "QUATERNION"; qprev = None
    for n in range(0, 690):
        t = n / FPS; pos, fwd, up, roll, fov, focus, fstop = cam_at(t)
        f = Vector(fwd).normalized(); r = f.cross(Vector(up)).normalized(); u = r.cross(f)
        q = Matrix((r, u, -f)).transposed().to_quaternion() @ Quaternion((0, 0, 1), roll)
        if qprev is not None and q.dot(qprev) < 0: q.negate()            # the short way round between keys (motion blur interpolates them)
        qprev = q.copy()
        p = Vector(pos); co.location = p; co.rotation_quaternion = q
        co.data.angle = math.radians(fov); co.data.dof.focus_distance = max(focus, 0.05); co.data.dof.aperture_fstop = fstop
        co.keyframe_insert("location", frame=n); co.keyframe_insert("rotation_quaternion", frame=n)
        co.data.keyframe_insert("lens", frame=n); co.data.dof.keyframe_insert("focus_distance", frame=n); co.data.dof.keyframe_insert("aperture_fstop", frame=n)

# ---------------------------------------------------------------- apply(t)
def apply(t, R):
    me, fme, sme = R["me"], R["fme"], R["sme"]
    dt = SHUTTER / FPS * 0.5
    cam = cam_at(t)[0]
    p = body_pos(S, t); v = (body_pos(S, t + dt) - body_pos(S, t - dt)) / (2 * dt)
    dcam = np.linalg.norm(p - cam, axis=1)
    near = sstep(1.0, 5.0, dcam) if t > 3.0 else sstep(2.5, 9.0, dcam)    # no star right in front of the lens (wider in the close-up)
    dim = 0.25 + 0.75 * sstep(3.0, 40.0, dcam)                             # close stars are dust streaking past, not lamps
    post = 1.0 if t < T_BURST else (0.025 + 0.12 * math.exp(-(t - T_BURST) / 0.35)) * (1 - float(smooth(seg(t, SCAN0, SCAN0 + 1.2))))
    imp = (1.0 + 0.6 * float(e_in(seg(t, 7.4, 8.0)))) * (1 - 0.65 * float(smooth(seg(t, 7.3, 7.95))))
    me.vertices.foreach_set("co", p.astype(np.float32).ravel())
    me.attributes["velocity"].data.foreach_set("vector", v.astype(np.float32).ravel())
    me.attributes["radius"].data.foreach_set("value", (S["rad"] * near).astype(np.float32))
    me.attributes["lum"].data.foreach_set("value", (S["lum"] * post * imp * dim).astype(np.float32))
    me.update()
    fp = body_pos(F, t); fv = (body_pos(F, t + dt) - body_pos(F, t - dt)) / (2 * dt)
    scr, slb, vis = card_verts(t, cam)
    fnear = sstep(1.0, 5.0, np.linalg.norm(fp - cam, axis=1))
    fme.vertices.foreach_set("co", fp.astype(np.float32).ravel())
    fme.attributes["velocity"].data.foreach_set("vector", fv.astype(np.float32).ravel())
    fme.attributes["radius"].data.foreach_set("value", (F["rad"] * (1 - vis) * fnear).astype(np.float32))
    fpost = 1.0 if t < T_BURST else float(1 - smooth(seg(t, T_BURST, T_BURST + 0.6)))   # after the blast the films are cards, not stars
    fme.attributes["lum"].data.foreach_set("value", (F["lum"] * (1 - np.minimum(vis, 1.0)) * imp * fpost).astype(np.float32))
    fme.update()
    scr0, slb0, _ = card_verts(t - dt, cam_at(t - dt)[0]); scr1, slb1, _ = card_verts(t + dt, cam_at(t + dt)[0])
    sm, sl = R["scr"], R["slb"]
    sm.vertices.foreach_set("co", scr.astype(np.float32).ravel())
    sm.attributes["velocity"].data.foreach_set("vector", ((scr1 - scr0) / (2 * dt)).astype(np.float32).ravel())
    sm.attributes["vis"].data.foreach_set("value", np.repeat(vis, 4).astype(np.float32))
    sn = F["_sn"]; colp = float(smooth(seg(t, 18.55, 19.1)))
    sm.attributes["gray"].data.foreach_set("value", np.repeat(0.78 * sn, 4).astype(np.float32))
    sm.attributes["amber"].data.foreach_set("value", np.repeat(np.minimum(1.0, 0.14 * sn + 0.7 * colp * sn), 4).astype(np.float32))
    uv0, uv1, fm = card_uv(t)
    sm.uv_layers["UVMap"].data.foreach_set("uv", uv0.astype(np.float32).ravel()); sm.uv_layers["UVNext"].data.foreach_set("uv", uv1.astype(np.float32).ravel())
    sm.attributes["fmix"].data.foreach_set("value", np.repeat(fm, 4).astype(np.float32))
    camp, _, _, _, cfov, _, _ = cam_at(t)
    sm.polygons.foreach_set("material_index", card_material(t, camp, cfov, vis))
    sm.update()
    sl.vertices.foreach_set("co", slb.astype(np.float32).ravel())
    sl.attributes["velocity"].data.foreach_set("vector", ((slb1 - slb0) / (2 * dt)).astype(np.float32).ravel())
    sl.update()
    R["sob"].hide_render = t < T_BURST
    if t >= T_BURST:
        sp = spark_pos(t); sv = (spark_pos(t + dt) - spark_pos(t - dt)) / (2 * dt); tb = t - T_BURST
        heat = np.exp(-tb / (0.2 + 0.35 * SPtau))
        sme.vertices.foreach_set("co", sp.astype(np.float32).ravel()); sme.attributes["velocity"].data.foreach_set("vector", sv.astype(np.float32).ravel())
        sme.attributes["radius"].data.foreach_set("value", np.full(NSP, 0.05, np.float32))
        sme.attributes["lum"].data.foreach_set("value", (heat * 6).astype(np.float32))
        col = np.stack([np.ones(NSP), 0.35 + 0.55 * heat, 0.12 + 0.8 * heat ** 2, np.ones(NSP)], 1)
        sme.attributes["col"].data.foreach_set("color", col.astype(np.float32).ravel()); sme.update()
    # galaxy volume: glows, then drains into the core with the stars
    VOL["T"].outputs[0].default_value = min(t, T_BURST); VOL["SPIN"].outputs[0].default_value = spin_v(t)
    VOL["GLOW"].outputs[0].default_value = float(1 - smooth(seg(t, 7.3, 7.95))) if t < T_BURST else 0.0
    VOL["DUST"].outputs[0].default_value = float(1 - smooth(seg(t, 7.2, 7.8)))
    VOL["SQUEEZE"].outputs[0].default_value = 1.0 / max(1 - 0.85 * float(e_in(seg(t, 7.3, 8.0))), 0.15) if t < T_BURST else 1.0
    VOL["ob"].hide_render = t >= T_BURST
    tb = t - T_BURST; nova = VOL["nova"]                                  # supernova
    nova.hide_render = not (0 <= tb < 1.9)
    if 0 <= tb < 1.9:
        rr = 0.6 + 16 * (1 - math.exp(-tb / 0.45)); nova.scale = (rr, rr, rr * 0.75)
        VOL["NAGE"].outputs[0].default_value = tb
        VOL["NHEAT"].outputs[0].default_value = (6 * math.exp(-tb / 0.08) + 1.1 * math.exp(-tb / 0.45)) * (1 - float(smooth(seg(tb, 1.1, 1.9))))
        VOL["NTEMP"].outputs[0].default_value = 9000 * math.exp(-tb / 0.3) + 4200
    sh = VOL["shock"]; sh.hide_render = not (0 <= tb < 1.2)
    if 0 <= tb < 1.2:
        rs = 1.0 + 75 * (1 - math.exp(-tb / 0.4)); sh.scale = (rs, rs, max(1.0, rs * 0.25))
        sh.data.materials[0].node_tree.nodes["Emission"].inputs["Strength"].default_value = 90 * (1 - tb / 1.2) ** 2
    s2 = VOL["shock2"]; s2.hide_render = not (0.05 <= tb < 1.8)
    if 0.05 <= tb < 1.8:
        r2 = 1.0 + 48 * (1 - math.exp(-(tb - 0.05) / 0.6)); s2.scale = (r2, r2, max(1.0, r2 * 0.35))
        s2.data.materials[0].node_tree.nodes["Emission"].inputs["Strength"].default_value = 26 * (1 - (tb - 0.05) / 1.75) ** 2
    VOL["streak"].inputs["Strength"].default_value = (0.9 * math.exp(-tb / 0.35) if tb >= 0 else 0.0) if "Strength" in VOL["streak"].inputs else 0
    ring = VOL["ring"]; rf = 80 * (1 - math.exp(-max(0.0, t - FR0) / 0.55))   # the foil front
    ring.hide_render = not (FR0 <= t < 11.4); ring.scale = (max(rf, 0.01), max(rf, 0.01), 1.0)
    ring.data.materials[0].node_tree.nodes["Emission"].inputs["Strength"].default_value = 60.0 * (1 - float(smooth(seg(t, 10.2, 11.3))))
    lowk = 1 - float(smooth(seg(t, SCAN0, SCAN0 + 1.0)))
    VOL["sky_me"].attributes["lum"].data.foreach_set("value", np.where(VOL["sky_low"], VOL["sky_lum"] * lowk, VOL["sky_lum"]).astype(np.float32)); VOL["sky_me"].update()
    sy = scan_y(t); VOL["scan"].hide_render = not (SCAN0 <= t < SCAN1 + 0.1); VOL["scan"].location = (0, sy, 0.02)
    VOL["scan"].data.materials[0].node_tree.nodes["Emission"].inputs["Strength"].default_value = 40.0 * (1 - float(smooth(seg(t, SCAN1 - 0.1, SCAN1 + 0.1))))
    VOL["SCAN"].outputs[0].default_value = sy if t >= SCAN0 else -999.0
    VOL["GRIDK"].outputs[0].default_value = float(seg(t, SCAN0, SCAN0 + 0.2)) * (1 - 0.6 * float(smooth(seg(t, 18.6, 19.2))))
    VOL["grid"].hide_render = t < SCAN0
    VOL["glare"].inputs["Strength"].default_value = 0.5 + (0.5 * math.exp(-tb / 0.4) if tb >= 0 else 0)

def main():
    frames = [int(f) for f in arg("--frames", "0").split(",") if f.strip()]
    t0 = time.time(); R = build(); print(f"[galaxy] build {time.time() - t0:.1f} s", flush=True)
    os.makedirs(os.path.join(ROOT, OUT), exist_ok=True)
    for n in frames:
        dst = os.path.join(ROOT, OUT, (arg("--name") or "f") + f"_{n:04d}.png")
        if "--resume" in argv and os.path.exists(dst) and os.path.getsize(dst) > 0: continue
        t = n / FPS; R["sc"].frame_set(n); a0 = time.time(); apply(t, R); a1 = time.time()
        if "--spp" not in argv: R["sc"].cycles.samples = 48 if DRAFT else (96 if t < 2.6 else 64)
        for nm in (arg("--hide") or "").split(","):
            if nm: bpy.data.objects[nm].hide_render = True
        R["sc"].render.filepath = os.path.join(ROOT, OUT, (arg("--name") or "f") + f"_{n:04d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"[galaxy] frame {n} t={t:.2f} apply {a1 - a0:.1f} s render {time.time() - a1:.1f} s", flush=True)

main()
