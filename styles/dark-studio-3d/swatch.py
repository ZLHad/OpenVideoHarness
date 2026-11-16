# SPDX-License-Identifier: GPL-3.0-or-later
# It calls Blender's Python API, so it is distributed under the GPL (engines/blender.md, "许可证"); the rest of the repo is MIT.
"""暗棚实物 3D · dark-studio-3d: the 8 s swatch (spec 2), a Blender (Cycles) scene run by styles/_swatch/blender_render.py.

A dark studio and one heavy machined part, at its real size: a steel spur gear (40 teeth, module 4, 16.8 cm across) on
a shaft, a ball bearing and a hex nut above it, on a black lacquer plinth. Softboxes show as long graded reflections
in the metal; strips and a kicker behind draw the teeth out of the dark; everything is path traced, so the parts
mirror each other and sit in soft contact shadows, and a 105 mm lens at f/4 keeps the focus on the gear's front teeth
(it racks to the nut as the nut seats). The lights come up, the assembly explodes along its shaft and comes back down
piece by piece with its weight, and a spec card says what the gear is, what it is made of and what it weighs (the mass
worked out from the model's own volume). The assembly turns 60° in the 8 s, a symmetry of every part, so the last
frame is the first.

  0.0–1.5  world      rim-lit silhouette; the key comes up from 0.1 s and the camera dollies in
  1.5–4.5  signature  explode (1.5–2.4), drop back: gear 2.95, bearing 3.22, nut 3.50; the card at 3.7 with its leader
  4.5–7.0  type       title, English line and caption at left in the dark; read once
  7.0–8.0  close      card and type go, the key goes down, the camera eases back: the first frame again

The card, the title and the caption are text in the scene, on a frame that rides with the camera at the focus distance
(so they are sharp) and that no ray but the camera's sees. Every value is a function of t. Units are metres.
"""
import json, math, sys

try:
    import bpy, bmesh
    from mathutils import Vector
except ImportError:          # plain python3 (foley.mjs reads FOLEY, tools/styles.py reads TEXTS): no Blender needed
    bpy = None

# ── time (seconds), as the four beats of the spec
T = {"lights": (0.1, 1.0), "dolly": (0.0, 1.5), "explode": (1.5, 2.4), "drops": (2.75, 3.02, 3.3), "land": 0.2,
     "card": (3.7, 4.15), "title": 4.5, "caption": 4.75, "read": (4.95, 7.0), "out": (7.0, 7.2), "dim": (7.05, 7.9),
     "back": (7.0, 7.97), "rack": (3.05, 3.35, 3.6, 3.95)}
LANDS = [t + T["land"] for t in T["drops"]]               # gear 2.95, bearing 3.22, nut 3.50

FOLEY = [
    {"t": 0.5, "sfx": "swoosh_tonal", "gain_db": -14, "dur": 1.0, "dir": "up", "tone": 0.6, "bright": -0.3, "pan": 0.1},
    {"t": 1.95, "sfx": "whoosh", "gain_db": -14, "dur": 0.8, "dir": "up", "tone": 0.3, "pan": 0.15},
    {"t": LANDS[0], "sfx": "impact", "gain_db": -6, "role": "hero", "pitch": -3, "pan": 0.14},
    {"t": LANDS[1], "sfx": "click", "gain_db": -7, "role": "hero", "pitch": -5, "pan": 0.14},
    {"t": round(LANDS[2] - 0.12, 3), "sfx": "tick", "gain_db": -12, "pitch": 4, "pan": 0.14},
    {"t": LANDS[2], "sfx": "click", "gain_db": -6, "role": "hero", "pitch": 2, "pan": 0.14},
    {"t": T["card"][0] + 0.2, "sfx": "swoosh_tonal", "gain_db": -15, "dur": 0.45, "dir": "down", "tone": 0.5, "pan": -0.5},
    {"t": 7.5, "sfx": "air", "gain_db": -12, "dur": 0.8, "dir": "down", "tone": 0.4, "pan": 0},
]
# the type beat's reads (the shared title and caption of spec 2: styles/_swatch/lib.js TITLE_ZH, TITLE_EN, CAPTION_ZH)
TITLE_ZH, TITLE_EN, CAPTION_ZH = "每一帧，都是代码。", "Every frame is code.", "一份代码，改到成片。"
TEXTS = [{"text": s, "start": T["read"][0], "end": T["read"][1]} for s in (TITLE_ZH, TITLE_EN, CAPTION_ZH)]

FONTS = {"zh": "PingFang SC:weight=semibold", "en": "Helvetica Neue:weight=light", "num": "Avenir Next:weight=medium", "mono": "Menlo"}
RENDER = {"final": {"samples": 32, "adaptive_threshold": 0.02}, "draft": {"samples": 16}}

# ── the parts (metres)
Z, MOD = 40, 0.004
RP = Z * MOD / 2
RO, RR = RP + MOD, RP - 1.25 * MOD
GEAR_T, BORE, HUB_R, HUB_H = 0.024, 0.015, 0.026, 0.008
HOLES = [(0.047 * math.cos(k * math.pi / 3 + math.pi / 6), 0.047 * math.sin(k * math.pi / 3 + math.pi / 6), 0.0145) for k in range(6)]
STACK = {"gear": 0.003, "bearing": 0.003 + GEAR_T + HUB_H, "nut": 0.003 + GEAR_T + HUB_H + 0.016}
LIFT = {"gear": 0.022, "bearing": 0.062, "nut": 0.10}
DENSITY = 7.85                                            # g/cm³: 42CrMo4 (EN 10083-3), as every structural steel to two places
CAM = {"lens": 105, "sensor": 36, "shift": -0.13, "fstop": 4.0, "az": -35}


def outline():
    """The gear's outline: 40 teeth, straight flanks narrowing to a short top land (metres, in the plane)."""
    pts, p, d = [], 2 * math.pi / Z, math.pi / 180
    for k in range(Z):
        c = k * p
        for r, a in ((RR, -3.4), (RR + 0.0012, -3.0), (RP - 0.001, -2.15), (RP + 0.002, -1.8), (RO - 0.0005, -1.35), (RO, -1.0),
                     (RO, 1.0), (RO - 0.0005, 1.35), (RP + 0.002, 1.8), (RP - 0.001, 2.15), (RR + 0.0012, 3.0), (RR, 3.4), (RR, 4.5)):
            pts.append((r * math.cos(c + a * d), r * math.sin(c + a * d)))
    return pts


def gear_mass():
    """The gear's mass in kg from its geometry: the outline's area less the bore and the holes, times the thickness,
    plus the hub, at the steel's density. The number on the card."""
    pts = outline()
    area = abs(sum(x * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * y for i, (x, y) in enumerate(pts))) / 2
    area -= math.pi * BORE ** 2 + sum(math.pi * r * r for _, _, r in HOLES)
    vol = area * GEAR_T + math.pi * (HUB_R ** 2 - BORE ** 2) * HUB_H          # m³
    return vol * 1e6 * DENSITY / 1000


CARD_LINES = [("mono", 26, "PART 03 · SPUR GEAR · Z40 M4", "muted"), ("zh", 46, "直齿轮 · 40 齿 · 模数 4", "text"),
              ("zh", 46, "42CrMo4 合金钢", "text"), ("num", 40, f"{DENSITY:.2f} g/cm³  ·  {gear_mass():.1f} kg", "text")]


# ── small maths
def clamp(x, a=0.0, b=1.0): return min(b, max(a, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def lerp(a, b, u): return a + (b - a) * u
def in_out(u): u = clamp(u); return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2
def in_out_sine(u): return 0.5 - 0.5 * math.cos(math.pi * clamp(u))
def out_cubic(u): return 1 - (1 - clamp(u)) ** 3


def lin(hexcol):
    h = hexcol.lstrip("#"); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ── building
def link(ob):
    bpy.context.scene.collection.objects.link(ob); return ob


def mesh(name, bm, mat=None):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = link(bpy.data.objects.new(name, me))
    if mat: ob.data.materials.append(mat)
    return ob


def prism(name, pts, h, mat):
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, 0)) for x, y in pts])
    r = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, vec=(0, 0, h), verts=[e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh(name, bm, mat)


def cutter(name, items, h):
    bm = bmesh.new()
    for x, y, r in items:
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=72, radius1=r, radius2=r, depth=h * 3)
        bmesh.ops.translate(bm, vec=(x, y, h / 2), verts=g["verts"])
    ob = mesh(name, bm); ob.hide_render = True; ob.hide_viewport = True
    return ob


def finish(ob, holes, bevel_w):
    m = ob.modifiers.new("holes", "BOOLEAN"); m.operation = "DIFFERENCE"; m.object = holes; m.solver = "EXACT"
    b = ob.modifiers.new("bevel", "BEVEL"); b.width = bevel_w; b.segments = 3; b.limit_method = "ANGLE"; b.harden_normals = True
    ob.modifiers.new("normals", "WEIGHTED_NORMAL").keep_sharp = True
    ob.data.shade_smooth()


def lathe(name, profile, mat, segs=96):
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
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f)
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
    me.shade_smooth()
    ob = link(bpy.data.objects.new(name, me)); ob.data.materials.append(mat)
    return ob


def metal(name, col, rough, aniso=0.0):
    m = bpy.data.materials.new(name); b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    if aniso:                                             # turned faces: the scratches run round the axis
        N, L = m.node_tree.nodes, m.node_tree.links
        b.inputs["Anisotropic"].default_value = aniso
        tg = N.new("ShaderNodeTangent"); tg.direction_type = "RADIAL"; tg.axis = "Z"
        L.new(tg.outputs["Tangent"], b.inputs["Tangent"])
    return m


def dielectric(name, col, rough, coat=0.0, spec=0.5):
    m = bpy.data.materials.new(name); b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = spec
    if coat: b.inputs["Coat Weight"].default_value = coat; b.inputs["Coat Roughness"].default_value = 0.16
    return m


def glow(name, hexcol, strength=1.0):
    """An emitting, fading material for the card and the type: its Mix factor is the opacity (set in apply)."""
    m = bpy.data.materials.new(name); N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N): N.remove(n)
    out = N.new("ShaderNodeOutputMaterial"); em = N.new("ShaderNodeEmission"); tr = N.new("ShaderNodeBsdfTransparent")
    mix = N.new("ShaderNodeMixShader")
    em.inputs["Color"].default_value = (*lin(hexcol), 1); em.inputs["Strength"].default_value = strength
    L.new(tr.outputs[0], mix.inputs[1]); L.new(em.outputs[0], mix.inputs[2]); L.new(mix.outputs[0], out.inputs["Surface"])
    mix.inputs["Fac"].default_value = 0.0
    return m


def area(name, size, loc, power, col=(1, 0.97, 0.93), target=(0, 0, 0.03), spread=180):
    li = bpy.data.lights.new(name, "AREA"); li.shape = "RECTANGLE"; li.size, li.size_y = size; li.energy = power; li.color = col
    li.spread = math.radians(spread)
    ob = link(bpy.data.objects.new(name, li)); ob.location = loc
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()
    return ob


def hud_only(ob):
    """Seen by the camera, by no other ray: no shadow, no reflection, no light on anything."""
    ob.visible_shadow = False; ob.visible_glossy = False; ob.visible_diffuse = False; ob.visible_transmission = False
    ob.visible_volume_scatter = False


def plate(name, w, h, mat, parent, x, y):
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in ((0, 0, 0), (w, 0, 0), (w, -h, 0), (0, -h, 0))]
    bm.faces.new(vs)
    ob = mesh(name, bm, mat); ob.parent = parent; ob.location = (x, y, 0); hud_only(ob)
    return ob


def text(name, body, font, size, mat, parent, x, y):
    cu = bpy.data.curves.new(name, "FONT"); cu.body = body; cu.size = size
    if font: cu.font = font
    cu.align_x = "LEFT"; cu.align_y = "BOTTOM_BASELINE"
    ob = link(bpy.data.objects.new(name, cu)); ob.data.materials.append(mat); ob.parent = parent; ob.location = (x, y, 0.2)
    hud_only(ob)
    return ob


def build(env):
    sc = env.scene; S = {}; tk = env.tokens["palette"]
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    cy = sc.cycles; cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transparent_max_bounces = 8, 2, 4, 8
    cy.sample_clamp_indirect = 5.0; cy.caustics_reflective = cy.caustics_refractive = False
    steel = metal("steel", (0.5, 0.51, 0.525), 0.26, aniso=0.6)
    chrome = metal("chrome", (0.82, 0.82, 0.84), 0.07)
    oxide = metal("oxide", (0.045, 0.045, 0.05), 0.3)
    plinth_m = dielectric("plinth", (0.008, 0.008, 0.009), 0.34, coat=0.45)
    floor_m = dielectric("floor", (0.0025, 0.0025, 0.003), 0.85, spec=0.05)
    back_m = dielectric("backdrop", (0.014, 0.0145, 0.016), 0.9, spec=0.1)

    root = link(bpy.data.objects.new("root", None)); S["root"] = root
    # the studio: the plinth on a black pedestal that runs down out of frame (so nothing stands between the camera and
    # the type at the focus distance), a dark backdrop far behind (the light falls off on it), the floor far below
    bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in ((-4, -4, -1.4), (4, -4, -1.4), (4, 4, -1.4), (-4, 4, -1.4))])
    mesh("floor", bm, floor_m)
    lathe("pedestal", [(0, -1.4), (0.098, -1.4), (0.098, -0.0175), (0, -0.0175)], floor_m)
    bm = bmesh.new(); bm.faces.new([bm.verts.new(p) for p in ((-3, 0, -1.4), (3, 0, -1.4), (3, 0, 2.2), (-3, 0, 2.2))])
    bd = mesh("backdrop", bm, back_m); bd.location = (0.75, 1.05, 0); bd.rotation_euler = (0, 0, math.radians(-35))
    pl = lathe("plinth", [(0, -0.016), (0.106, -0.016), (0.106, -0.0012), (0.1048, 0), (0, 0)], plinth_m); pl.parent = root
    sh = lathe("shaft", [(0, 0), (0.023, 0), (0.023, 0.0026), (0.022, 0.003), (BORE - 0.0005, 0.003), (BORE - 0.0005, 0.0945),
                         (BORE - 0.002, 0.0948), (0, 0.0948)], oxide)
    sh.parent = root
    # the gear: the outline as a prism, the bore and six holes cut, every edge chamfered; a turned hub on top
    gear = prism("gear", outline(), GEAR_T, steel)
    finish(gear, cutter("gear-holes", [(0, 0, BORE)] + HOLES, GEAR_T), 0.0009)
    hub = lathe("hub", [(BORE, GEAR_T), (HUB_R, GEAR_T), (HUB_R, GEAR_T + HUB_H - 0.001), (HUB_R - 0.001, GEAR_T + HUB_H),
                        (BORE + 0.001, GEAR_T + HUB_H), (BORE, GEAR_T + HUB_H - 0.001)], steel)
    hub.parent = gear; gear.parent = root; S["gear"] = gear
    # the bearing: two rings, ten balls
    br = link(bpy.data.objects.new("bearing", None)); br.parent = root; S["bearing"] = br
    ring = lambda r0, r1, h: [(r0, 0.0006), (r0 + 0.0006, 0), (r1 - 0.0006, 0), (r1, 0.0006), (r1, h - 0.0006), (r1 - 0.0006, h),
                              (r0 + 0.0006, h), (r0, h - 0.0006), (r0, 0.0006)]
    lathe("outer", ring(0.0275, 0.031, 0.016), chrome).parent = br
    lathe("inner", ring(BORE, 0.0195, 0.016), chrome).parent = br
    for k in range(10):
        bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=0.004)
        b = mesh(f"ball{k}", bm, chrome); b.data.shade_smooth(); b.parent = br
        a = k * 2 * math.pi / 10; b.location = (0.0235 * math.cos(a), 0.0235 * math.sin(a), 0.008)
    # the nut (60° symmetric), chamfered
    nut = prism("nut", [(0.0265 * math.cos(k * math.pi / 3), 0.0265 * math.sin(k * math.pi / 3)) for k in range(6)], 0.02, oxide)
    finish(nut, cutter("nut-hole", [(0, 0, BORE)], 0.02), 0.0014)
    nut.parent = root; S["nut"] = nut

    # light: the key softbox behind right (what the flat faces mirror), a top strip, two rim strips, a kicker behind,
    # a low glow on the backdrop. Only the key comes up and goes down
    S["key"] = area("key", (0.9, 0.45), (0.9, 1.3, 0.75), 60, spread=70)
    S["top"] = area("top", (0.8, 0.25), (-0.05, 0.05, 1.4), 7, spread=60)
    area("rimR", (0.1, 0.8), (1.2, -0.7, 0.32), 46, (0.92, 0.96, 1.0), spread=45)
    area("rimL", (0.1, 0.8), (-1.2, 0.8, 0.32), 36, (0.92, 0.96, 1.0), spread=45)
    area("kick", (0.25, 0.25), (0.35, 1.4, 0.18), 30, (0.95, 0.97, 1.0), target=(0, 0, 0.015), spread=30)
    S["glow"] = area("backglow", (1.6, 0.8), (0.1, 0.45, 0.9), 22, (1.0, 0.96, 0.9), target=(0.75, 1.05, 0.25), spread=50)
    world = bpy.data.worlds.new("studio"); sc.world = world
    bgn = world.node_tree.nodes["Background"]; bgn.inputs["Color"].default_value = (0.0015, 0.0015, 0.0018, 1)

    cam = link(bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))); sc.camera = cam
    cam.data.lens = CAM["lens"]; cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = CAM["sensor"]
    cam.data.clip_start = 0.01; cam.data.clip_end = 30; cam.data.shift_x = CAM["shift"]
    cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = CAM["fstop"]; cam.data.dof.aperture_blades = 7
    S["cam"] = cam

    # the card and the type: a frame that rides with the camera at the focus distance, laid out in screen pixels
    hud = link(bpy.data.objects.new("hud", None)); hud.parent = cam; S["hud"] = hud
    f = env.fonts
    S["card_bg"] = glow("card-bg", tk["card"], 1.0); S["card_ac"] = glow("card-accent", tk["accent"], 2.4)
    S["card_hair"] = glow("card-hair", tk["hair"], 1.6)
    plate("card", 590, 300, S["card_bg"], hud, 110, -560)
    plate("card-accent", 6, 300, S["card_ac"], hud, 110, -560)
    for nm, x, y, w, h in (("hair-t", 110, -560, 590, 1.4), ("hair-b", 110, -858.6, 590, 1.4), ("hair-r", 698.6, -560, 1.4, 300)):
        plate(nm, w, h, S["card_hair"], hud, x, y)
    S["card_txt"] = []
    for k, (role, size, body, col) in enumerate(CARD_LINES):
        m = glow(f"card-text-{k}", tk[col], 2.6)
        text(f"card-{k}", body, f.get(role), size, m, hud, 150, -(560 + (62, 132, 198, 262)[k]))
        S["card_txt"].append(m)
    S["title"] = glow("title", tk["text"], 3.0); S["title_en"] = glow("title-en", tk["muted"], 2.4); S["caption"] = glow("caption", tk["text"], 3.0)
    text("title-zh", TITLE_ZH, f.get("zh"), 96, S["title"], hud, 150, -300)
    text("title-en", TITLE_EN, f.get("en"), 44, S["title_en"], hud, 152, -368)
    # the caption sits low at the left, under the type: the part takes the right and the bottom of the frame
    text("caption", CAPTION_ZH, f.get("zh"), 48, S["caption"], hud, 150, -946)
    # the leader: a thin bar from the card's edge to the gear's teeth (laid out in apply), and a dot on the metal
    S["lead_m"] = glow("leader", tk["hair"], 2.0)
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0); S["lead"] = mesh("leader", bm, S["lead_m"]); hud_only(S["lead"])
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.5); S["dot"] = mesh("dot", bm, S["lead_m"]); hud_only(S["dot"])
    env.S = S


# ── time
def height(t, k, lift):
    up = in_out(seg(t, T["explode"][0] + k * 0.12, T["explode"][1] - (2 - k) * 0.05)) * lift
    if t < T["drops"][k]: return up
    u = seg(t, T["drops"][k], LANDS[k])
    if u < 1: return lift * (1 - u * u)                   # falls under gravity: slow off the top, fastest at the seat
    dt = t - LANDS[k]
    return 0.0022 * math.exp(-dt * 16) * abs(math.sin(dt * 34))   # one small bounce, quickly gone: it is heavy


def fade(m, a):
    m.node_tree.nodes["Mix Shader"].inputs["Fac"].default_value = clamp(a)


def apply(t, env):
    S = env.S
    root = S["root"]; root.rotation_euler = (0, 0, -(t / env.DUR) * math.pi / 3)        # a sixth of a turn: the loop
    S["gear"].location = (0, 0, STACK["gear"] + height(t, 0, LIFT["gear"]))
    S["bearing"].location = (0, 0, STACK["bearing"] + height(t, 1, LIFT["bearing"]))
    un = seg(t, T["drops"][2], LANDS[2])                   # the nut spins down a third of a turn (a hexagon can't tell)
    S["nut"].location = (0, 0, STACK["nut"] + height(t, 2, LIFT["nut"]))
    S["nut"].rotation_euler = (0, 0, (2 * math.pi / 3) * (1 - un) if T["drops"][2] <= t and un < 1 else 0)
    # the key comes up, and in the close goes down to the rims alone
    key_on = in_out_sine(seg(t, *T["lights"])) * (1 - in_out_sine(seg(t, *T["dim"])))
    S["key"].data.energy = 1 + 59 * key_on
    S["top"].data.energy = 7 * key_on; S["glow"].data.energy = 3 + 19 * key_on      # the rims and the kicker stay: the silhouette
    # the camera: dollies in, rises a little for the explode, back for the close
    back = in_out(seg(t, *T["back"])); din = out_cubic(seg(t, *T["dolly"])) * (1 - back)
    up = in_out_sine(seg(t, 1.4, 2.4)) * (1 - in_out_sine(seg(t, 3.1, 4.3)))
    dist, elev, az = lerp(1.85, 1.45, din) + 0.17 * up, math.radians(lerp(30, 24, din) + 3 * up), math.radians(CAM["az"])
    target = Vector((0, 0, 0.032 + 0.036 * up))
    cam = S["cam"]
    cam.location = target + Vector((dist * math.cos(elev) * math.sin(az), -dist * math.cos(elev) * math.cos(az), dist * math.sin(elev)))
    dt = t - LANDS[0]
    if 0 < dt < 0.4: cam.location.z += 0.0018 * math.exp(-dt * 14) * math.sin(dt * 60)   # the gear's landing
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    # focus: the gear's front teeth; it racks to the nut as it seats and back for the card
    rot = root.matrix_world
    teeth = rot @ Vector((-RO * 0.55, -RO * 0.75, STACK["gear"] + GEAR_T))
    nut_top = S["nut"].matrix_world @ Vector((0, 0, 0.02))
    rk = T["rack"]
    to_nut = in_out_sine(seg(t, rk[0], rk[1])) * (1 - in_out_sine(seg(t, rk[2], rk[3])))
    fd = lerp((teeth - cam.location).length, (nut_top - cam.location).length, to_nut)
    cam.data.dof.focus_distance = fd
    # the screen frame at the focus distance: 1 unit = 1 px of the 1920-wide frame, y up, origin at the top left
    wd = fd * CAM["sensor"] / CAM["lens"]
    s = wd / 1920
    hud = S["hud"]; hud.location = ((CAM["shift"] - 0.5) * wd, wd * (1080 / 1920) / 2, -fd); hud.scale = (s, s, s)
    # the card and the type fade in and out
    a_card = out_cubic(seg(t, *T["card"])) * (1 - seg(t, *T["out"]))
    for m, k in ((S["card_bg"], 0.82), (S["card_ac"], 1), (S["card_hair"], 0.6)): fade(m, a_card * k)
    for m in S["card_txt"]: fade(m, a_card)
    a_out = 1 - seg(t, *T["out"])
    fade(S["title"], seg(t, T["title"], T["title"] + 0.35) * a_out)
    fade(S["title_en"], seg(t, T["title"] + 0.25, T["title"] + 0.5) * a_out)
    fade(S["caption"], seg(t, T["caption"], T["caption"] + 0.15) * a_out)
    # the leader: from the card's right edge to the front teeth (at the focus, so both ends are sharp)
    bpy.context.view_layer.update()
    lu = in_out_sine(seg(t, T["card"][0] + 0.15, T["card"][1] + 0.1)) * a_card
    p0 = hud.matrix_world @ Vector((700, -616, 0.1))
    p1 = rot @ Vector((-RO * 0.95, -RO * 0.3, STACK["gear"] + GEAR_T * 0.5))
    p1 = p0 + (p1 - p0) * max(lu, 1e-4)
    mid, d = (p0 + p1) / 2, (p1 - p0)
    ld = S["lead"]; ld.location = mid; ld.rotation_euler = d.to_track_quat("X", "Z").to_euler()
    th = 1.8 * s; ld.scale = (max(d.length, 1e-5), th, th)
    S["dot"].location = p1; S["dot"].scale = (10 * s * (lu > 0.98),) * 3
    fade(S["lead_m"], 0.85 * (lu > 0.01) * a_card)


if __name__ == "__main__":
    if "--foley" in sys.argv: print(json.dumps(FOLEY))
    if "--texts" in sys.argv: print(json.dumps(TEXTS, ensure_ascii=False))
