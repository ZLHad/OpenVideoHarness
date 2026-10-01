# SPDX-License-Identifier: GPL-3.0-or-later
# It calls Blender's Python API, so it is distributed under the GPL (engines/blender.md, "许可证"); the rest of the repo is MIT.
"""桌面微缩剧场 · tabletop-miniature: the 5 s swatch, a Blender (Cycles) scene run by styles/_swatch/blender_render.py.

Night, a walnut desk under a window, everything at its real size: the felt puck is 2 cm tall, so the depth of field is
a few millimetres and the room behind it melts into blur. 0.1 s: a desk lamp off frame (top left) clicks on and floods
the desk. 0.8 s: the title card is flown in on two threads and settles on them. 2.0 / 2.4 / 2.8 s: the puck hops up
three wooden blocks, 大纲 → 分镜 → 初版, raw wood → half painted → lacquered, one note per landing. 4.15 s: the lamp
clicks off, a breath of moonlight, and 4.35–5.0 s the window brings the morning in, its bars throwing shadows across
the desk.

The puppets (puck, card, blocks) move on twos (15 fps) with a hand-placed jitter; the camera and the lights move on
ones, like a motion-control rig. No motion blur: a stop-motion camera has none. Every value is a function of t.
Units are metres.
"""
import json, math, sys

try:
    import bpy, bmesh
    from mathutils import Vector
except ImportError:          # plain python3 (foley.mjs reads FOLEY): no Blender here, and none needed
    bpy = None

# ── time: 150 BPM, a beat is 0.4 s (score.json uses the same grid and meters). Puppet times sit on even frames (twos).
LAMP_ON, LAMP_OFF = 0.1, 4.0                   # off on the downbeat of the last bar
WAKE = 10 / 30                                 # the wake take: squash, stretch up, eyes open, settle by 0.53 s
CARD_IN, CARD_DOWN = 0.56, 1.12                # lowered from above the frame (its edge shows at 0.8 s); the end of its lines
SCOOTS = [(36 / 30, 40 / 30), (42 / 30, 46 / 30)]   # two small steps along the desk to the first block
HOPS = [(52 / 30, 2.0), (64 / 30, 2.4), (78 / 30, 2.8)]   # (takeoff, landing) onto 大纲, 分镜, 初版: landings on the beat
GLEE = 3.2                                     # happy eyes ^ ^ and a wiggle
BOUNCE = (104 / 30, 3.6)                       # a small hop in place on 初版
LOOK_BACK = 91 / 30                            # looks back down the steps it climbed
TURN = 112 / 30                                # turns to the lamp
DAWN = (4.4, 4.8)                              # moonlight held a beat, the window light rises, the last frames hold
LOOK_WINDOW, SLEEP = 132 / 30, 4.8            # turns to the morning; eyes close on the last beat

# ── the set (metres)
BLOCK_X = (-0.025, 0.011, 0.047)
BLOCK_W = 0.028
BLOCK_H = (0.017, 0.024, 0.031)
PUCK_R, PUCK_H = 0.0115, 0.022
PUCK_X = (-0.092, -0.079, -0.066)              # asleep, after the first step, after the second (the foot of 大纲)
CARD = {"x": -0.028, "y": -0.0150, "z": 0.0768, "w": 0.100, "h": 0.034}   # bottom edge above every hop on screen
CAM_KEYS = [                                   # (t, camera, aim, ease into this key): a motion-control rig
    (0.0, (-0.082, -0.212, 0.021), (-0.086, 0.0, 0.0175), None),       # tight on the sleeping puck, at its eye height
    (0.3, (-0.081, -0.206, 0.021), (-0.085, 0.0, 0.0175), "out"),     # leans in a little as the lamp comes on
    (1.2, (-0.034, -0.327, 0.031), (-0.031, 0.0, 0.0485), "inout"),   # pulls back as the card comes down: the blocks appear
    (1.6, (-0.034, -0.327, 0.031), (-0.031, 0.0, 0.0485), "lin"),
    (2.5, (-0.006, -0.300, 0.032), (-0.003, 0.0, 0.0490), "inout"),   # follows the hops in and to the right
    (4.0, (-0.005, -0.293, 0.032), (-0.002, 0.0, 0.0488), "inout"),
    (4.4, (-0.005, -0.290, 0.032), (-0.002, 0.0, 0.0488), "lin"),     # the dark: still creeping in
    (5.0, (-0.003, -0.288, 0.0325), (0.003, 0.0, 0.0498), "inout"),   # a pan towards the morning window
]
ONES = (1.6, 86 / 30)                          # the puppet on ones while the camera follows it (or it ratchets back on screen)
                                               # and through the last, fastest hop (fast action on ones, holds on twos)
CUP = (-0.135, 0.17)                            # a real teacup behind the puck's bed: the scale of the world
FOCUS = (0.0, -0.0122, 0.03)                   # the puck's eyes; the block faces and the card sit within ±3.5 mm

FONTS = {"title": "Big Caslon", "zh": "Songti SC:weight=bold"}
FOLEY = [
    {"t": LAMP_ON, "sfx": "sfx/lamp_on.wav", "gain_db": -2, "pan": -0.55, "role": "hero"},
    {"t": WAKE + 4 / 30, "sfx": "sfx/felt_land_c.wav", "gain_db": -14, "pan": -0.6, "role": "detail"},       # the startled jump lands
    {"t": CARD_DOWN - 0.07, "sfx": "paper", "gain_db": -9, "pan": -0.1, "dur": 0.4, "dir": "down"},     # the card lowered
    {"t": CARD_DOWN, "sfx": "sfx/thread_tug.wav", "gain_db": -9, "pan": -0.1},                         # the end of its lines
    {"t": SCOOTS[0][1], "sfx": "sfx/felt_land_a.wav", "gain_db": -12, "pan": -0.7, "role": "detail"},  # two small steps
    {"t": SCOOTS[1][1], "sfx": "sfx/felt_land_c.wav", "gain_db": -11, "pan": -0.62, "role": "detail"},
    *[{"t": land, "sfx": f"sfx/felt_land_{'abc'[k]}.wav", "gain_db": -1, "pan": round(BLOCK_X[k] * 9, 2), "role": "detail"}
      for k, (_, land) in enumerate(HOPS)],
    {"t": BOUNCE[1], "sfx": "sfx/felt_land_b.wav", "gain_db": -9, "pan": round(BLOCK_X[2] * 9, 2), "role": "detail"},
    {"t": LAMP_OFF, "sfx": "sfx/lamp_off.wav", "gain_db": -1, "pan": -0.55, "role": "hero"},
    {"t": DAWN[0] + 0.3, "sfx": "air", "gain_db": -16, "pan": 0.45, "dur": 0.7, "dir": "up", "role": "ambience"},
    {"t": 4.72, "sfx": "sfx/bird.wav", "gain_db": -12, "pan": 0.75, "dist": 3, "role": "ambience"},
]

RENDER = {"final": {"samples": 32, "adaptive_threshold": 0.03}, "draft": {"samples": 20}}


# ── pure functions of t
def clamp(x, a=0.0, b=1.0): return min(b, max(a, x))
def lerp(a, b, u): return a + (b - a) * u
def seg(t, a, b): return clamp((t - a) / (b - a))
def smooth(u): return u * u * (3 - 2 * u)
def in_out(u): return 0.5 - 0.5 * math.cos(math.pi * clamp(u))
def out_cubic(u): return 1 - (1 - clamp(u)) ** 3
def lerp3(a, b, u): return tuple(lerp(p, q, u) for p, q in zip(a, b))
def twos(t): return math.floor(round(t * 30) / 2) * 2 / 30           # the puppets are re-posed every second frame
def pose_time(t): return t if ONES[0] <= t < ONES[1] else twos(t)    # … except while the camera follows them
def ring(t, t0, amp, tau, period):                                     # a damped wobble that starts at t0
    return 0.0 if t < t0 else amp * math.exp(-(t - t0) / tau) * math.sin(2 * math.pi * (t - t0) / period)
def kelvinish(warm): return (1.0, lerp(0.86, 0.62, warm), lerp(0.74, 0.34, warm))   # 3500 K … 2400 K, roughly


def lamp_level(t):
    """the desk lamp: a 3-frame filament warm-up with one flicker, steady, then off with two frames of afterglow"""
    if t < LAMP_ON - 1e-6: return 0.0
    if t < LAMP_OFF - 1e-6:
        return {0: 0.35, 1: 1.12, 2: 0.9}.get(round((t - LAMP_ON) * 30), 1.0)
    return {0: 0.30, 1: 0.08}.get(round((t - LAMP_OFF) * 30), 0.0)


def dawn(t): return in_out(seg(t, *DAWN))


def camera_at(t):
    """(camera, aim) of the motion-control rig: wide on the sleeping puck, a slow drift, then it follows the hops in
    and to the right, eases into a slow push, and holds once the lamp is off"""
    for (t0, c0, a0, _), (t1, c1, a1, ease) in zip(CAM_KEYS, CAM_KEYS[1:]):
        if t <= t1:
            u = seg(t, t0, t1); u = {"out": out_cubic(u), "inout": in_out(u)}.get(ease, u)
            return lerp3(c0, c1, u), lerp3(a0, a1, u)
    return CAM_KEYS[-1][1], CAM_KEYS[-1][2]


DRAW = 2 / 30                                                          # one drawing on twos


def landing(t, t1, depth=0.15):
    """scale z after a landing: one squashed drawing, a small overshoot, settled two drawings later"""
    return 1.0 if t < t1 else 1 - depth * math.exp(-(t - t1) / 0.06) * math.cos(2 * math.pi * (t - t1) / 0.2)


def arc(t, t0, t1, a, b, height, lean=9.0, stretch=0.08, crouch=0.88):
    """a hop from a to b ((x, z) feet): one crouched drawing before t0, then every drawing in the air (u from one
    drawing in to one drawing short of the landing), squash on t1. → x, z, scale z, lean° (None outside the hop)"""
    if t < t0 - DRAW or t >= t1: return None
    if t < t0: return a[0], a[1], crouch, -4.0                          # the crouch
    u = (t - t0 + DRAW) / (t1 - t0 + DRAW)
    return (lerp(a[0], b[0], u), lerp(a[1], b[1], u) + height * 4 * u * (1 - u),
            1 + stretch * math.sin(math.pi * u), lean * math.sin(math.pi * u))


def puck_pose(t):
    """(x, z, scale_z, rot_x, rot_y, rot_z) in metres and degrees: wake, two steps, three hops, a bounce, looks"""
    stands = [(PUCK_X[0], 0.0), (PUCK_X[1], 0.0), (PUCK_X[2], 0.0)] + [(BLOCK_X[k], BLOCK_H[k]) for k in range(3)]
    moves = [(SCOOTS[0], 0, 1, 0.003, 4.0, 0.04, 0.9, 0.08), (SCOOTS[1], 1, 2, 0.003, 4.0, 0.04, 0.9, 0.08),
             (HOPS[0], 2, 3, 0.0096, 9.0, 0.08, 0.88, 0.15), (HOPS[1], 3, 4, 0.0066, 9.0, 0.08, 0.88, 0.15),
             (HOPS[2], 4, 5, 0.0062, 11.0, 0.10, 0.78, 0.22),             # the climb to 初版: a deeper crouch, a harder landing
             (BOUNCE, 5, 5, 0.0035, 0.0, 0.05, 0.9, 0.08)]
    x, z = stands[0]; s = 1.0; rx = ry = rz = 0.0
    for (t0, t1), i, k, h, lean, st, crouch, depth in moves:
        hop = arc(t, t0, t1, stands[i], stands[k], h, lean, st, crouch)
        if hop: x, z, s, ry = hop; break
        if t >= t1: x, z = stands[k]; s = landing(t, t1, depth)
    # the wake take: squash, a startled jump stretched up 18 %, settle
    if WAKE <= t < WAKE + 0.2:
        f = round((t - WAKE) * 30); s *= {0: 0.85, 1: 0.85, 2: 1.18, 3: 1.18, 4: 0.94, 5: 0.94}.get(f, 1.0)
        z += 0.0025 if f in (2, 3) else 0.0
    rz += 14 * (seg(t, 0.53, 0.6) - seg(t, 0.66, 0.73))                         # glances right, at the blocks
    rx -= 13 * (smooth(seg(t, 0.73, 0.86)) - smooth(seg(t, 1.13, 1.2)))         # looks up as the card comes down
    rz += 10 * (smooth(seg(t, 1.13, 1.2)) - smooth(seg(t, 1.6, 1.667)))          # turned a little to the blocks while it walks
    rx -= 6 * (smooth(seg(t, 1.533, 1.6)) - smooth(seg(t, 1.667, 1.7333)))       # sizes up the first block
    if 74 / 30 <= t < 78 / 30: rx -= 9; rz += 6                                  # on 分镜, looks up at the red block before the climb
    if LOOK_BACK <= t < GLEE: rz -= 15 * smooth(seg(t, LOOK_BACK, LOOK_BACK + 0.1)); rx += 4  # down at the steps
    if GLEE <= t < GLEE + 0.24: rz += 9 * math.sin(2 * math.pi * (t - GLEE) / 0.12)   # a wiggle of joy
    turn = smooth(seg(t, TURN, TURN + 0.12)) * (1 - smooth(seg(t, LOOK_WINDOW, LOOK_WINDOW + 0.13)))
    rz += -26 * turn; rx += -9 * turn                                           # to the lamp, up and left
    win = smooth(seg(t, LOOK_WINDOW, LOOK_WINDOW + 0.13)); rz += 18 * win; rx += -5 * win   # then to the window
    s *= 1 - 0.035 * smooth(seg(t, SLEEP, SLEEP + 0.13))                        # settles as it falls asleep,
    ry += 2.0 * smooth(seg(t, SLEEP, SLEEP + 0.13)); rx += 3.0 * smooth(seg(t, SLEEP, SLEEP + 0.13))   # a small nod and lean
    return x, z, s, rx, ry, rz


def eyes(t):
    """'closed' (two arcs) | 'open' (glass beads) | 'happy' (^ ^)"""
    if t < WAKE + 2 / 30 or t >= SLEEP: return "closed"
    if SLEEP - 2 * DRAW <= t < SLEEP: return "half"                              # heavy lids before it falls asleep
    if GLEE - DRAW <= t < GLEE or TURN - DRAW <= t < TURN: return "closed"      # a blink between expressions
    if GLEE <= t < TURN: return "happy"
    return "open"


def card_offset(t):
    """(dx, dz, tilt°): lowered from 7.5 cm above (ease-in), a bounce on the lines, a sway that dies before 2.4 s"""
    if t < CARD_IN: return 0.0, 0.075, 0.0
    if t < CARD_DOWN: return 0.0, 0.075 * (1 - seg(t, CARD_IN, CARD_DOWN)) ** 2, 0.0
    return (ring(t, 0.95, 0.0022, 0.38, 0.7), -ring(t, CARD_DOWN, 0.0035, 0.18, 0.3), ring(t, 1.05, 2.4, 0.36, 0.7))


def block_rock(t, k):
    """the block the puck lands on rocks a little (degrees about y)"""
    r = ring(t, HOPS[k][1], 1.6, 0.08, 0.16)
    if k == 2: r += ring(t, BOUNCE[1], 0.9, 0.08, 0.16)
    return r


# ── building the scene (Blender only)
def lin(hexcol):
    h = hexcol.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def link(ob):
    bpy.context.scene.collection.objects.link(ob); return ob


def mesh_obj(name, verts, faces, mat=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.update()
    if smooth: me.shade_smooth()
    ob = link(bpy.data.objects.new(name, me))
    if mat: ob.data.materials.append(mat)
    return ob


def box(name, w, d, h, mat, bevel=0.0, origin="bottom"):
    z0 = 0.0 if origin == "bottom" else -h / 2
    v = [(x, y, z) for z in (z0, z0 + h) for y in (-d / 2, d / 2) for x in (-w / 2, w / 2)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = mesh_obj(name, v, f, mat)
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL"); m.width = bevel; m.segments = 4; m.harden_normals = True
        ob.data.shade_smooth()
    return ob


def lathe(name, profile, mat, segs=64):
    """a solid of revolution about z from (r, z) points, bottom to top; r = 0 ends close in a fan"""
    v, f, rings = [], [], []
    for r, z in profile:
        if r == 0: rings.append([len(v)]); v.append((0, 0, z)); continue
        rings.append(list(range(len(v), len(v) + segs)))
        v += [(r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs), z) for i in range(segs)]
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            if len(a) == 1: f.append((a[0], b[j], b[i]))
            elif len(b) == 1: f.append((a[i], a[j], b[0]))
            else: f.append((a[i], a[j], b[j], b[i]))
    return mesh_obj(name, v, f, mat, smooth=True)


def sock(coll, ident):
    """a node socket by identifier: the Mix node has three inputs named "A" (float, vector, colour)"""
    return next(s for s in coll if s.identifier == ident)


def principled(name, color, rough=0.5, **inputs):
    m = bpy.data.materials.new(name); b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*lin(color), 1); b.inputs["Roughness"].default_value = rough
    for k, val in inputs.items(): b.inputs[k.replace("_", " ")].default_value = val
    return m


def grain(m, dark, light, scale, bump=0.06, contrast=(0.32, 0.68), mask_z=None, paint=None):
    """wood: stretched noise as grain into the base colour and a faint bump; paint (hex) below object z = mask_z"""
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); mp = N.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = scale
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.62; nz.inputs["Distortion"].default_value = 0.35
    L.new(mp.outputs["Vector"], nz.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB"); el = ramp.color_ramp.elements
    el[0].position, el[1].position = contrast; el[0].color = (*lin(dark), 1); el[1].color = (*lin(light), 1)
    L.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    col = ramp.outputs["Color"]
    if paint:
        sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Object"], sep.inputs["Vector"])
        edge = N.new("ShaderNodeMath"); edge.operation = "LESS_THAN"; edge.inputs[1].default_value = mask_z
        L.new(sep.outputs["Z"], edge.inputs[0])
        mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; sock(mix.inputs, "B_Color").default_value = (*lin(paint), 1)
        L.new(edge.outputs[0], sock(mix.inputs, "Factor_Float")); L.new(col, sock(mix.inputs, "A_Color"))
        col = sock(mix.outputs, "Result_Color")
        rough = N.new("ShaderNodeMapRange"); rough.inputs["To Min"].default_value = 0.55; rough.inputs["To Max"].default_value = 0.32
        L.new(edge.outputs[0], rough.inputs["Value"]); L.new(rough.outputs["Result"], b.inputs["Roughness"])
    L.new(col, b.inputs["Base Color"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = bump; bp.inputs["Distance"].default_value = 0.0004
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def fuzz(m, scale, strength):
    """a fine fibre bump (felt, paper)"""
    nt = m.node_tree; N, L = nt.nodes, nt.links; b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord"); nz = N.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 10.0; L.new(tc.outputs["Object"], nz.inputs["Vector"])
    bp = N.new("ShaderNodeBump"); bp.inputs["Strength"].default_value = strength; bp.inputs["Distance"].default_value = 0.0002
    L.new(nz.outputs["Fac"], bp.inputs["Height"]); L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def text(name, body, font, size, loc, mat, tracking=1.0, align="CENTER", parent=None):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size
    if font: cu.font = font
    cu.align_x = align; cu.align_y = "CENTER"; cu.space_character = tracking
    ob = link(bpy.data.objects.new(name, cu)); ob.data.materials.append(mat)
    ob.location = loc; ob.rotation_euler = (math.radians(90), 0, 0)              # face −y, towards the camera
    if parent: ob.parent = parent
    return ob


def aim(ob, target):
    d = Vector(target) - ob.location; ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def build(env):
    sc = env.scene; tk = env.tokens["palette"]; S = {}
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    sc.view_settings.exposure = 0.0
    cy = sc.cycles
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = 4, 2, 2, 4
    cy.caustics_reflective = cy.caustics_refractive = False; cy.sample_clamp_indirect = 4.0

    ink = principled("ink", tk["ink"], 0.55)
    gold = principled("cream-paint", tk["gilt"], 0.45)

    # the desk: varnished walnut, grain along x
    desk = box("desk", 1.6, 1.2, 0.03, grain(principled("walnut", tk["walnut"], 0.42, Coat_Weight=0.35, Coat_Roughness=0.12),
                                             tk["walnut_dark"], tk["walnut"], (6, 160, 6), 0.05), origin="bottom")
    desk.location = (0, 0.15, -0.03)

    # the wall and its window (an opening with a cross of bars), the sky behind it
    plaster = fuzz(principled("plaster", tk["wall"], 0.9), 120, 0.15)
    wy, t_ = 0.30, 0.02
    for nm, w, h, x, z in [("wall-l", 0.80, 0.70, -0.38, -0.03), ("wall-r", 0.40, 0.70, 0.52, -0.03),
                           ("wall-b", 0.30, 0.065, 0.17, -0.03), ("wall-t", 0.30, 0.30, 0.17, 0.30)]:
        o = box(nm, w, t_, h, plaster); o.location = (x, wy + t_ / 2, z)
    frame = principled("window-frame", tk["window_frame"], 0.5)
    for nm, w, h, x, z in [("bar-v", 0.012, 0.30, 0.17, 0.035), ("bar-h", 0.30, 0.012, 0.17, 0.15),
                           ("sill", 0.34, 0.012, 0.17, 0.023)]:
        o = box(nm, w, 0.03 if nm != "sill" else 0.05, h, frame); o.location = (x, wy + (0.0 if nm != "sill" else -0.012), z)
    sky = bpy.data.materials.new("sky"); nt = sky.node_tree; N, L = nt.nodes, nt.links
    N.remove(N["Principled BSDF"]); out = N["Material Output"]
    tc = N.new("ShaderNodeTexCoord"); sep = N.new("ShaderNodeSeparateXYZ"); L.new(tc.outputs["Generated"], sep.inputs["Vector"])
    S["sky_night"] = N.new("ShaderNodeValToRGB"); S["sky_dawn"] = N.new("ShaderNodeValToRGB")
    for ramp, lo, hi in [(S["sky_night"], tk["night_low"], tk["night_high"]), (S["sky_dawn"], tk["dawn_low"], tk["dawn_high"])]:
        ramp.color_ramp.elements[0].color = (*lin(lo), 1); ramp.color_ramp.elements[1].color = (*lin(hi), 1)
        ramp.color_ramp.elements[0].position = 0.25; L.new(sep.outputs["Z"], ramp.inputs["Fac"])
    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"; S["sky_fac"] = sock(mix.inputs, "Factor_Float")
    L.new(S["sky_night"].outputs["Color"], sock(mix.inputs, "A_Color")); L.new(S["sky_dawn"].outputs["Color"], sock(mix.inputs, "B_Color"))
    vor = N.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = 70.0          # far windows of the town
    L.new(tc.outputs["Generated"], vor.inputs["Vector"])
    dots = N.new("ShaderNodeMapRange"); dots.inputs["From Min"].default_value = 0.05; dots.inputs["From Max"].default_value = 0.03
    L.new(vor.outputs["Distance"], dots.inputs["Value"])
    cell = N.new("ShaderNodeSeparateColor"); L.new(vor.outputs["Color"], cell.inputs["Color"])
    lit = N.new("ShaderNodeMapRange"); lit.inputs["From Min"].default_value = 0.55; lit.inputs["From Max"].default_value = 1.0
    L.new(cell.outputs[0], lit.inputs["Value"])                                          # about half the windows lit, each its own brightness
    dots2 = N.new("ShaderNodeMath"); dots2.operation = "MULTIPLY"; L.new(dots.outputs["Result"], dots2.inputs[0]); L.new(lit.outputs["Result"], dots2.inputs[1])
    town = N.new("ShaderNodeMath"); town.operation = "MULTIPLY"; S["town"] = town
    L.new(dots2.outputs[0], town.inputs[0])
    low = N.new("ShaderNodeMapRange"); low.inputs["From Min"].default_value = 0.45; low.inputs["From Max"].default_value = 0.3
    L.new(sep.outputs["Z"], low.inputs["Value"])
    town2 = N.new("ShaderNodeMath"); town2.operation = "MULTIPLY"; L.new(town.outputs[0], town2.inputs[0]); L.new(low.outputs["Result"], town2.inputs[1])
    em = N.new("ShaderNodeEmission"); S["sky_em"] = em; L.new(sock(mix.outputs, "Result_Color"), em.inputs["Color"])
    lights = N.new("ShaderNodeEmission"); lights.inputs["Color"].default_value = (*lin(tk["town_light"]), 1)
    L.new(town2.outputs[0], lights.inputs["Strength"])
    add = N.new("ShaderNodeAddShader"); L.new(em.outputs["Emission"], add.inputs[0]); L.new(lights.outputs["Emission"], add.inputs[1])
    L.new(add.outputs["Shader"], out.inputs["Surface"])
    skyp = box("sky", 1.6, 0.01, 0.9, sky, origin="bottom"); skyp.location = (0.2, 0.75, -0.2)
    skyp.visible_shadow = False

    # a teacup and saucer at their real size, out of focus behind where the puck sleeps
    glaze = principled("glaze", tk["glaze"], 0.12, Coat_Weight=0.6, Coat_Roughness=0.05)
    saucer = lathe("saucer", [(0, 0.001), (0.05, 0.002), (0.072, 0.011), (0.071, 0.013), (0.05, 0.005), (0, 0.004)], glaze)
    cup = lathe("cup", [(0, 0.004), (0.025, 0.004), (0.031, 0.008), (0.043, 0.055), (0.044, 0.062), (0.041, 0.062),
                        (0.039, 0.056), (0.028, 0.012), (0, 0.010)], glaze)
    for o in (saucer, cup): o.location = (*CUP, 0)
    tea = lathe("tea", [(0, 0.045), (0.0385, 0.045), (0.0385, 0.0452), (0, 0.0452)], principled("tea", tk["tea"], 0.05))
    tea.location = (*CUP, 0)

    # three wooden blocks: raw birch, half dipped in paint, lacquered
    S["blocks"] = []
    birch = lambda nm: grain(principled(nm, tk["birch"], 0.55), tk["birch_dark"], tk["birch"], (14, 14, 220), 0.04)
    mats = [birch("birch-1"),
            grain(principled("birch-2", tk["birch"], 0.55), tk["birch_dark"], tk["birch"], (14, 14, 220), 0.04,
                  mask_z=BLOCK_H[1] * 0.3, paint=tk["lacquer"]),   # the same red as 初版: how much is painted is the progress
            principled("lacquer", tk["lacquer"], 0.28, Coat_Weight=1.0, Coat_Roughness=0.06)]
    for k in range(3):
        b = box(f"block-{k}", BLOCK_W, BLOCK_W, BLOCK_H[k], mats[k], bevel=0.0011)
        b.location = (BLOCK_X[k], 0, 0); S["blocks"].append(b)
        m = gold if k == 2 else ink
        fy = -BLOCK_W / 2 - 0.00025
        text(f"label-zh-{k}", env.MOTIF[k]["zh"], env.fonts.get("zh"), 0.0088, (0, fy, BLOCK_H[k] * 0.55), m, 1.04, parent=b)

    # the title card on two threads, a double rule printed round it
    paper = fuzz(principled("paper", tk["paper"], 0.8, Sheen_Weight=0.15), 900, 0.05)
    pn = paper.node_tree.nodes; tr = pn.new("ShaderNodeBsdfTranslucent"); tr.inputs["Color"].default_value = (*lin(tk["paper"]), 1)
    ms = pn.new("ShaderNodeMixShader"); ms.inputs["Fac"].default_value = 0.35
    paper.node_tree.links.new(pn["Principled BSDF"].outputs["BSDF"], ms.inputs[1]); paper.node_tree.links.new(tr.outputs["BSDF"], ms.inputs[2])
    paper.node_tree.links.new(ms.outputs["Shader"], pn["Material Output"].inputs["Surface"])
    card = box("card", CARD["w"], 0.0006, CARD["h"], paper, origin="center")
    S["card"] = card
    fy = -0.00032
    text("title-en", env.TITLE_EN, env.fonts.get("title"), 0.0145, (0, fy, 0.0064), ink, 1.0, parent=card)
    text("title-zh", env.TITLE_ZH, env.fonts.get("zh"), 0.0104, (0, fy, -0.0083), ink, 1.04, parent=card)
    for i, inset in enumerate((0.0024, 0.0033)):
        w, h, th = CARD["w"] - 2 * inset, CARD["h"] - 2 * inset, 0.00028 if i == 0 else 0.00014
        for nm, bw, bh, x, z in [("t", w, th, 0, h / 2), ("b", w, th, 0, -h / 2), ("l", th, h, -w / 2, 0), ("r", th, h, w / 2, 0)]:
            o = box(f"rule-{i}{nm}", bw, 0.0001, bh, ink, origin="center"); o.location = (x, fy, z); o.parent = card
    thread = principled("thread", tk["thread"], 0.7)
    for side in (-1, 1):
        th_ = lathe(f"thread-{side}", [(0, 0), (0.00022, 0), (0.00022, 0.4), (0, 0.4)], thread, segs=8)
        th_.location = (side * (CARD["w"] / 2 - 0.006), 0, CARD["h"] / 2 - 0.0015); th_.parent = card

    # the puck: a felt marshmallow with two glass-bead eyes (and two stitched arcs for the happy eyes)
    felt = fuzz(principled("felt", tk["felt"], 1.0, Sheen_Weight=0.7, Sheen_Roughness=0.35), 2600, 0.35)
    rc = 0.0042; prof = [(0, 0)] + [(PUCK_R - rc + rc * math.sin(a), rc - rc * math.cos(a))
                                  for a in [math.pi / 2 * i / 6 for i in range(7)]]
    prof += [(PUCK_R - rc + rc * math.cos(a), PUCK_H - rc + rc * math.sin(a)) for a in [math.pi / 2 * i / 6 for i in range(7)]]
    prof += [(0, PUCK_H)]
    puck = lathe("puck", prof, felt); S["puck"] = puck
    glass = principled("bead", tk["bead"], 0.12, Coat_Weight=1.0, Coat_Roughness=0.03)
    S["eyes"], S["happy"], S["closed"] = [], [], []
    for side in (-1, 1):
        e = lathe(f"eye-{side}", [(0, -0.002)] + [(0.002 * math.sin(math.pi * i / 8), -0.002 * math.cos(math.pi * i / 8)) for i in range(1, 8)] + [(0, 0.002)], glass, segs=24)
        e.parent = puck; e.location = (side * 0.0047, -PUCK_R + 0.0008, 0.0141); e.scale = (1, 0.7, 1.15); S["eyes"].append(e)
        arc = bpy.data.curves.new(f"happy-{side}", "CURVE"); arc.dimensions = "3D"; arc.bevel_depth = 0.0005
        sp = arc.splines.new("POLY"); pts = [(-0.0024, 0, -0.0009), (0, 0, 0.0014), (0.0024, 0, -0.0009)]
        sp.points.add(len(pts) - 1)
        for p, co in zip(sp.points, pts): p.co = (*co, 1)
        h = link(bpy.data.objects.new(f"happy-{side}", arc)); h.data.materials.append(glass)
        h.parent = puck; h.location = (side * 0.0047, -PUCK_R - 0.0001, 0.0141); S["happy"].append(h)
        lid = bpy.data.curves.new(f"closed-{side}", "CURVE"); lid.dimensions = "3D"; lid.bevel_depth = 0.00045
        sp = lid.splines.new("POLY"); pts = [(-0.0023 + 0.0046 * i / 6, 0, -0.0011 * math.sin(math.pi * i / 6)) for i in range(7)]
        sp.points.add(len(pts) - 1)
        for p, co in zip(sp.points, pts): p.co = (*co, 1)
        c = link(bpy.data.objects.new(f"closed-{side}", lid)); c.data.materials.append(glass)
        c.parent = puck; c.location = (side * 0.0047, -PUCK_R - 0.0001, 0.0135); S["closed"].append(c)

    # light: the desk lamp (off frame, top left), its spill on the room, moonlight at the window, the morning sun
    lamp = link(bpy.data.objects.new("lamp", bpy.data.lights.new("lamp", "SPOT")))
    lamp.location = (-0.22, -0.2, 0.24); aim(lamp, (0.0, 0.02, 0.03))
    lamp.data.spot_size = math.radians(75); lamp.data.spot_blend = 0.85; lamp.data.shadow_soft_size = 0.03
    lamp.data.color = kelvinish(0.8); S["lamp"] = lamp
    spill = link(bpy.data.objects.new("spill", bpy.data.lights.new("spill", "AREA")))
    spill.location = (-0.3, -0.35, 0.35); aim(spill, (0.05, 0.2, 0.05)); spill.data.size = 0.4
    spill.data.color = kelvinish(0.7); S["spill"] = spill
    moon = link(bpy.data.objects.new("moon", bpy.data.lights.new("moon", "AREA")))
    moon.location = (0.17, wy + 0.06, 0.16); aim(moon, (0.0, 0.0, 0.0)); moon.data.size = 0.25
    moon.data.color = lin(tk["moon"]); S["moon"] = moon
    sun = link(bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")))
    sun.data.angle = math.radians(1.2); S["sun"] = sun
    moonfill = link(bpy.data.objects.new("moonfill", bpy.data.lights.new("moonfill", "AREA")))
    moonfill.location = (0.12, -0.45, 0.22); aim(moonfill, (0.0, 0.0, 0.03)); moonfill.data.size = 0.6
    moonfill.data.color = lin(tk["moon"]); S["moonfill"] = moonfill          # moonlight in the room: the dark is blue, never a void
    morning = link(bpy.data.objects.new("morning", bpy.data.lights.new("morning", "SPOT")))
    morning.location = (0.08, -0.5, 0.2); aim(morning, (0.047, 0.0, 0.046)); morning.data.shadow_soft_size = 0.08
    morning.data.spot_size = math.radians(9); morning.data.spot_blend = 0.9
    morning.data.color = lin(tk["dawn_sun_gold"]); S["morning"] = morning      # the room behind the camera, lit by the dawn
    world = bpy.data.worlds.new("room"); sc.world = world
    S["world_bg"] = world.node_tree.nodes["Background"]

    cam = link(bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))); sc.camera = cam
    cam.data.lens = 54; cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36
    cam.data.clip_start = 0.002; cam.data.clip_end = 5
    focus = link(bpy.data.objects.new("focus", None)); focus.location = FOCUS
    cam.data.dof.use_dof = True; cam.data.dof.focus_object = focus; cam.data.dof.aperture_fstop = 4.5
    cam.data.dof.aperture_blades = 0
    S["cam"] = cam
    env.S = S


def apply(t, env):
    S, tk = env.S, env.tokens["palette"]
    # camera and lights: on ones
    cam, at = camera_at(t)
    S["cam"].location = cam; aim(S["cam"], at)
    lv, d = lamp_level(t), dawn(t)
    S["lamp"].data.energy = 4.2 * lv; S["spill"].data.energy = 1.9 * lv
    S["moon"].data.energy = lerp(7.0, 0.0, d); S["moonfill"].data.energy = 0.9 * (1 - min(lv, 1.0)) * (1 - d)
    sun = S["sun"]; sun.data.energy = 8.5 * d ** 1.3; S["morning"].data.energy = 18.0 * d
    sun.data.color = lerp3(lin(tk["dawn_sun_pink"]), lin(tk["dawn_sun_gold"]), d)
    el, az = math.radians(lerp(9, 18, d)), math.radians(lerp(150, 157, d))      # from behind the window, to the left
    sun.rotation_euler = (math.pi / 2 - el, 0, az)
    S["sky_fac"].default_value = d
    S["sky_em"].inputs["Strength"].default_value = lerp(0.45, 2.4, d)
    S["town"].inputs[1].default_value = lerp(26.0, 0.0, d)
    S["world_bg"].inputs["Color"].default_value = (*lerp3(lin(tk["room_night"]), lin(tk["room_day"]), d), 1)
    S["world_bg"].inputs["Strength"].default_value = lerp(0.09, 0.5, d)      # night: moonlit, never a black void

    # the puppets: on twos, each pose placed by hand (a hash jitter per pose)
    tp = pose_time(t); k = round(twos(t) * 15); j = lambda i, a: (env.hash(k, i) - 0.5) * 2 * a   # jitter stays on twos
    x, z, s, rx, ry, rz = puck_pose(tp)
    p = S["puck"]; p.location = (x + j(1, 0.0003), j(2, 0.0002), z + abs(j(6, 0.0001)))
    p.rotation_euler = tuple(math.radians(v + j(3 + i, 0.6)) for i, v in enumerate((rx, ry, rz)))
    p.scale = (1 / math.sqrt(s), 1 / math.sqrt(s), s)
    state = eyes(tp)
    for e in S["eyes"]:
        e.hide_render = state not in ("open", "half"); e.scale = (1, 0.7, 1.15 * (0.45 if state == "half" else 1.0))
    for h in S["happy"]: h.hide_render = state != "happy"
    for c in S["closed"]: c.hide_render = state != "closed"
    dx, dz, tilt = card_offset(tp)
    moving = CARD_IN <= tp < 2.4
    c = S["card"]; c.location = (CARD["x"] + dx + (j(10, 0.00012) if moving else 0), CARD["y"], CARD["z"] + dz)
    c.rotation_euler = (0, math.radians(tilt + (j(11, 0.25) if moving else 0)), 0)
    for i, b in enumerate(S["blocks"]):
        b.rotation_euler = (0, math.radians(block_rock(tp, i)), 0)


if __name__ == "__main__":
    if "--foley" in sys.argv: print(json.dumps(FOLEY))
