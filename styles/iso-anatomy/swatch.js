// iso-anatomy swatch — the idea built as a small bench instrument that explains itself, then taken apart.
// The instrument is a cam timer: one shaft carries three cams, each cut to its own profile; the shaft indexes 72° a
// step, and each cam's lobe lifts a follower that raises one card out of its holder: outline → storyboard → draft.
// The cams' shapes are the program, so "every frame is code" is something you can see: the same shaft angle always
// gives the same three heights. Nothing is labelled inside the drawing; the legend and the readout sit on the plate.
// The geometry is real 3D: 56 convex parts in millimetres, posed per frame (shaft angle, follower lift, explode),
// projected orthographically (elevation 30°), shaded in four tones by facing (tops lightest, round parts continuous),
// painted back to front in an order solved from separating planes, outlined in hairlines that don't scale with zoom.
//   0.0–0.8  frame 0 is the instrument taken apart; from 0.10 s its assemblies come home inside-out, 35 ms apart,
//            on critically damped springs, while the camera settles from 58° to 32° azimuth (the hook); the title's
//            three slot lines draw meanwhile on the left
//   0.8–2.6  the title rises out of its slots glyph by glyph (critically damped, 35 ms apart); Chinese 0.2 s later;
//            1.72 s the legend's three rows rise, grey
//   2.0–4.0  the shaft indexes at 2.0, 2.4 and 2.8 s: each step lifts the next card; its cam-to-card chain is the one lit
//            part (accent) and its legend row turns the accent; 2.8–4.0 slow push, and the draft card's little cube turns
//            frame by frame (12 fps) while the shaft holds
//   4.0–5.0  the signature transition is the explode: assemblies leave outside-in, 35 ms apart, slightly under-damped,
//            still settling at 5.0 s; each pillow block's column (block, cap, post) moves out together

export const fonts = ["Helvetica Neue", "Menlo", "PingFang SC"];

const D2R = Math.PI / 180, FPS = 30;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const sine = (u) => 0.5 - 0.5 * Math.cos(Math.PI * clamp(u));            // in-out sine: the indexing step
const cubic = (u) => (u = clamp(u), u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);

// ───────── the model (mm; object frame: x right, y back, z up) ─────────
const SH = { y: -30, z: 90 };                         // the shaft's axis
const R1 = 24, R2 = 64;                               // cam base circle and lobe radius: 40 mm of follower travel
const NOSE = 9;                                       // the lobe's ends are rounded with this radius
const STEP = 72, STEPS = [2.0, 2.4, 2.8], STEP_DUR = 0.28;
const LOBE_END = 246;                                 // every lobe ends here (shaft deg): 30° of dwell past the last step
const CAM_X = [-120, 0, 120];
const lobeStart = (i) => STEP * (i + 1);              // cam i rises during step i and dwells from its end
const EXPLODE_AT = 4.0, ASSEMBLE_AT = 0.10, STAGGER = 0.035;

/** Shaft angle in degrees: three indexing steps, still in between. */
export function shaftAngle(t) { return STEPS.reduce((a, s) => a + STEP * sine(seg(t, s, s + STEP_DUR)), 0); }
/** Follower lift (mm): the drawn cam profile's support in +z at shaft angle th, minus the base circle. A flat-faced
 *  follower rests on the highest point, so lift and drawing come from the same polygon. */
function camLift(i, th) {
  const s = Math.sin(th * D2R), c = Math.cos(th * D2R);
  let m = -Infinity; for (const [u, v] of CAMS[i]) m = Math.max(m, u * s + v * c);
  return Math.max(0, m - R1);
}

// assemblies: explode order (outside first) and each one's move (mm). Closing runs the list backwards (inside out).
// Each pillow block's column (block, cap, post) moves out sideways together, the cap and post also lifting off it.
const ORDER = ["cards", "gear", "dial", "follow", "posts", "caps", "shaft", "blocks", "feet"];
const side = (x, z) => ({ L: [-x, 0, z], R: [x, 0, z] });
const columns = (x, post, cap) => { const o = {}; for (const [k, z] of [["posts", post], ["caps", cap], ["blocks", 0]]) { const m = side(x, z); o[k + "L"] = m.L; o[k + "R"] = m.R; } return o; };
const MOVE = {
  cards: [0, 0, 140], gear: [-115, 0, 0], dial: [100, 0, 0], follow: [0, 0, 85], ...columns(65, 60, 32),
  shaft: [0, -100, 10], feet: [0, 0, -22], base: [0, 0, 0],
};
// frame 0 is spread wider than the ending, mostly sideways, so the first move covers the right half of the frame
const OPEN = {
  cards: [0, 40, 180], gear: [-300, 0, 20], dial: [140, 0, 30], follow: [0, 30, 120], ...columns(150, 80, 50),
  shaft: [0, -200, 25], feet: [0, 0, -28], base: [0, 0, 0],
};
const slotOf = (asm) => ORDER.indexOf(asm.replace(/[LR]$/, ""));
const springK = (tau, w, zeta) => {                   // 0 → 1, closed form (lib.spring's maths, kept local for FOLEY)
  if (tau <= 0) return 0;
  if (zeta >= 1) return 1 - Math.exp(-w * tau) * (1 + w * tau);
  const wd = w * Math.sqrt(1 - zeta * zeta);
  return 1 - Math.exp(-zeta * w * tau) * (Math.cos(wd * tau) + (zeta * w / wd) * Math.sin(wd * tau));
};
/** How far apart an assembly is at t: 1 at frame 0, home by ~1 s, out again from 4.0 s. */
function apartOf(asm, t) {
  if (asm === "base") return 0;
  const k = slotOf(asm), n = ORDER.length;
  const close = 1 - springK(t - (ASSEMBLE_AT + (n - 1 - k) * STAGGER), 10, 1);         // inner ones first, no overshoot
  const open = springK(t - (EXPLODE_AT + k * STAGGER), 7.5, 0.89);                   // outer ones first, a hint of weight
  return t < EXPLODE_AT ? close : open;
}
const homeAt = ASSEMBLE_AT + (ORDER.length - 1) * STAGGER + 0.8;    // the last assembly (the cards) is within 0.5 mm of home

// ───────── timeline (shared by picture and FOLEY) ─────────
const TL = {
  slots: 0.15, title: 0.85, titleStag: 0.035, zh: 1.07, zhStag: 0.045, legend: 1.72,
  lit: (i) => [STEPS[i], i < 2 ? STEPS[i + 1] : EXPLODE_AT],
  hold: [STEPS[2] + STEP_DUR, EXPLODE_AT],
};
const pan = (x) => +(((2 * x) / 1920 - 1) * 0.7).toFixed(2);
export const FOLEY = [
  { t: 0.12, sfx: "air", gain_db: -8, dur: 0.6, dir: "down" },                          // the parts start home
  ...["blocks", "shaft", "follow", "cards"].map((a, j) => ({                          // four of them seat (clicks)
    t: +(ASSEMBLE_AT + (ORDER.length - 1 - slotOf(a)) * STAGGER + 0.42).toFixed(3), sfx: "click", gain_db: -7 + j * 0.5, pan: pan(1260), pitch: [-3, -1, 1, 4][j] })),
  { t: TL.title, sfx: "tick", gain_db: -3, pan: pan(300) },                            // the title starts to rise
  { t: TL.legend, sfx: "tick", gain_db: -6, pan: pan(320), pitch: 3 },                 // the legend's rows rise
  ...STEPS.map((s, i) => ({ t: s, sfx: "tick", gain_db: -5, pan: pan(1060 + i * 190), pitch: i * 2 })),   // each step
  ...STEPS.map((s, i) => ({ t: s + STEP_DUR, sfx: "click", gain_db: -10, pan: pan(1060 + i * 190), pitch: 3 + i })),   // lobe reached
  { t: EXPLODE_AT + 0.08, sfx: "whoosh", gain_db: -12, dur: 0.45, dir: "up", tone: 0.2, pan_from: 0, pan_to: 0.3 },     // apart
  { t: EXPLODE_AT + 0.02, sfx: "click", gain_db: -5, pan: pan(1260), pitch: -2 },      // the first assembly lets go
];

// ───────── vectors and camera ─────────
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const LIGHT = norm([-0.55, -0.62, 0.56]);             // front-left, above
const LIGHT_AZ = Math.atan2(LIGHT[1], LIGHT[0]);
const SCALE = 1.58;                                   // px per mm at zoom 1

function camera(t) {
  const u = springK(t - ASSEMBLE_AT, 6.5, 1), out = cubic(seg(t, EXPLODE_AT, 4.9));    // the camera settles with the parts
  const yaw = 58 + (32 - 58) * u - 5 * seg(t, 1.2, EXPLODE_AT) + 6 * out;
  const elev = 40 + (30 - 40) * u + 3 * out;
  const push = sine(seg(t, STEPS[2], EXPLODE_AT + 0.1));
  const zoom = (0.77 + 0.23 * u) * (1 + 0.08 * push) * (1 - 0.16 * out);
  const focus = [-20 * (1 - u), -20, 190 + 45 * (1 - u) + 25 * push * (1 - out) + 20 * out];
  const tc = (-90 + yaw) * D2R, ce = Math.cos(elev * D2R);
  const V = [ce * Math.cos(tc), ce * Math.sin(tc), Math.sin(elev * D2R)];
  const R = [-Math.sin(tc), Math.cos(tc), 0], U = cross(V, R);
  return { V, R, U, s: SCALE * zoom, f: focus, cx: 1290 + 70 * out, cy: 505 - 45 * (1 - u) + 10 * out };
}
const project = (cam, p) => { const d = sub(p, cam.f); return [cam.cx + cam.s * dot(d, cam.R), cam.cy - cam.s * dot(d, cam.U)]; };

// ───────── parts ─────────
// box: b = [x0, x1, y0, y1, z0, z1] · cyl: ax (0 x, 1 y, 2 z), c (a point on the axis), r, a0..a1 along the axis ·
// prism: like cyl with poly = [[u, v], …] around the axis (u, v = the other two coordinates in x-y-z order).
// spin: turns with the shaft · lift: follower index (rides its cam) · chain: lit with card `chain` · deco: surface marks.
const PARTS = [];
const part = (o) => { PARTS.push({ tone: "mid", mat: "paper", spin: false, lift: null, chain: -1, deco: [], smooth: true, ...o }); return PARTS[PARTS.length - 1]; };
const box = (id, asm, b, o = {}) => part({ id, asm, kind: "box", b, ...o });
const cyl = (id, asm, ax, c, r, a0, a1, o = {}) => part({ id, asm, kind: "cyl", ax, c, r, a0, a1, ...o });
const prism = (id, asm, ax, c, poly, a0, a1, o = {}) => part({ id, asm, kind: "prism", ax, c, poly, a0, a1, ...o });
const roundRect = (x0, x1, y0, y1, r, n = 6) => {
  const pts = [], cs = [[x1 - r, y0 + r, -90], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, 90], [x0 + r, y0 + r, 180]];
  for (const [cx, cy, a] of cs) for (let k = 0; k <= n; k++) { const q = (a + (90 * k) / n) * D2R; pts.push([cx + r * Math.cos(q), cy + r * Math.sin(q)]); }
  return pts;
};
function hull2(pts) {                                  // monotone chain, counter-clockwise
  const p = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const half = (arr) => { const h = []; for (const q of arr) { while (h.length >= 2 && (h[h.length - 1][0] - h[h.length - 2][0]) * (q[1] - h[h.length - 2][1]) - (h[h.length - 1][1] - h[h.length - 2][1]) * (q[0] - h[h.length - 2][0]) <= 0) h.pop(); h.push(q); } h.pop(); return h; };
  return half(p).concat(half(p.reverse()));
}
function camPoly(i) {                                  // body frame (y, z offsets from the axis): base circle ∪ lobe arc,
  const pts = [];                                      // the arc's two ends rounded by circles of NOSE
  for (let k = 0; k < 72; k++) { const q = (k * 5) * D2R; pts.push([R1 * Math.cos(q), R1 * Math.sin(q)]); }
  const p0 = 90 - LOBE_END, p1 = 90 - lobeStart(i);
  for (let a = p0; a <= p1 + 1e-9; a += (p1 - p0) / Math.ceil((p1 - p0) / 3)) pts.push([R2 * Math.cos(a * D2R), R2 * Math.sin(a * D2R)]);
  for (const a of [p0, p1]) for (let k = 0; k < 36; k++) {
    const q = k * 10 * D2R, cx = (R2 - NOSE) * Math.cos(a * D2R), cy = (R2 - NOSE) * Math.sin(a * D2R);
    pts.push([cx + NOSE * Math.cos(q), cy + NOSE * Math.sin(q)]);
  }
  return hull2(pts);
}
const CAMS = [0, 1, 2].map(camPoly);
const ring = (r, n, a0 = 0) => Array.from({ length: n }, (_, k) => [r * Math.cos(a0 + (k * 2 * Math.PI) / n), r * Math.sin(a0 + (k * 2 * Math.PI) / n)]);

// marks on a face, in the part's local coordinates: lines (polylines), dots (screws), fills; n = the face's normal
const L = (pts, n, o = {}) => ({ type: "line", pts, n, ...o });
const DOT = (p, n, o = {}) => ({ type: "dot", p, n, ...o });
const FILL = (pts, n, o = {}) => ({ type: "fill", pts, n, ...o });
const screw = (p, n) => DOT(p, n, { ring: true });

// base: a rounded plate on four rubber feet, a groove inset 6 mm, corner screws, a ruler strip along the front edge
{
  const X0 = -292, X1 = 292, Y0 = -114, Y1 = 84, top = 16, up = [0, 0, 1];
  const groove = roundRect(X0 + 7, X1 - 7, Y0 + 7, Y1 - 7, 5).map(([x, y]) => [x, y, top]);
  prism("base", "base", 2, [0, 0, 0], roundRect(X0, X1, Y0, Y1, 10), 0, top, { tone: "lo",
    deco: [L([...groove, groove[0]], up, { tone: "faint" }), ...[[X0 + 15, Y0 + 15], [X1 - 15, Y0 + 15], [X0 + 15, Y1 - 15], [X1 - 15, Y1 - 15]].map(([x, y]) => screw([x, y, top], up))] });
  for (const [x, y] of [[-262, -88], [262, -88], [-262, 58], [262, 58]]) cyl(`foot${x}${y}`, "feet", 2, [x, y, 0], 11, -7, 0, { mat: "rubber", tone: "lo" });
  const rx0 = -238, rx1 = 238, ry0 = -108, ry1 = -96, rz = top + 1.6, ticks = [];
  for (let x = rx0 + 4, k = 0; x <= rx1 - 4; x += 4, k++) ticks.push(L([[x, ry0, rz], [x, ry0 + (k % 5 === 0 ? 6.5 : 3.2), rz]], up, { tone: k % 5 === 0 ? "mid" : "lo" }));
  box("ruler", "base", [rx0, rx1, ry0, ry1, top, rz], { tone: "lo", deco: ticks });
}
// pillow blocks: a flange bolted down, a body, a cap over the shaft; posts on the caps carry the guide bar
for (const side of [-1, 1]) {
  const xi = side * 205, xo = side * 225, [xa, xb] = side < 0 ? [xo, xi] : [xi, xo], asm = side < 0 ? "blocksL" : "blocksR", up = [0, 0, 1];
  box(`flange${side}`, asm, [xa - side * 0, xb, -74, 14, 16, 25], { tone: "mid",
    deco: [screw([(xa + xb) / 2, -66, 25], up), screw([(xa + xb) / 2, 6, 25], up)] });
  box(`block${side}`, asm, [xa, xb, -60, 0, 25, SH.z], { tone: "mid",
    deco: [L([[xa, -60, 40], [xb, -60, 40]], [0, -1, 0], { tone: "faint" })] });              // a seam, edge to edge
  box(`cap${side}`, side < 0 ? "capsL" : "capsR", [xa, xb, -54, -6, SH.z, SH.z + 18], { tone: "mid",
    deco: [screw([(xa + xb) / 2, -47, SH.z + 18], up), screw([(xa + xb) / 2, -13, SH.z + 18], up)] });
  box(`post${side}`, side < 0 ? "postsL" : "postsR", [xa + side * 2, xb - side * 2, -42, -18, SH.z + 18, 170], { tone: "mid" });
}
// the guide bar: a groove runs end to end on its top; a collar where each rod passes through
box("guide", "follow", [-223, 223, -42, -18, 170, 186], { tone: "mid",
  deco: [L([[-223, -30, 186], [223, -30, 186]], [0, 0, 1], { tone: "faint" }), screw([-212, -30, 186], [0, 0, 1]), screw([212, -30, 186], [0, 0, 1])] });
// the shaft: segments between collars, cams and bearing rings, so no part passes through another
{
  cyl("stub", "gear", 0, [0, SH.y, SH.z], 7, -229, -225, { mat: "steel", spin: true });   // the gearbox's output shaft
  for (const side of [-1, 1]) cyl(`bearing${side}`, "shaft", 0, [0, SH.y, SH.z], 15, side < 0 ? -205 : 201, side < 0 ? -201 : 205, { mat: "steel", spin: true });
  let x = -201;
  CAM_X.forEach((cx, i) => {
    cyl(`seg${i}`, "shaft", 0, [0, SH.y, SH.z], 7, x, cx - 13, { mat: "steel", spin: true });
    for (const [a, b] of [[cx - 13, cx - 7], [cx + 7, cx + 13]]) cyl(`collar${i}${a}`, "shaft", 0, [0, SH.y, SH.z], 11, a, b, { mat: "steel", spin: true,
      deco: [DOT([(a + b) / 2, SH.y, SH.z + 11], [0, 0, 1])] });
    const boss = ring(17, 40).map(([u, v]) => [cx + 7, SH.y + u, SH.z + v]);         // the boss round the bore, outside the collar
    prism(`cam${i}`, "shaft", 0, [0, SH.y, SH.z], CAMS[i], cx - 7, cx + 7, { tone: "hi", spin: true, chain: i,
      deco: [L([...boss, boss[0]], [1, 0, 0], { tone: "mid" }), DOT([cx + 7, SH.y, SH.z + 14.5], [1, 0, 0], { r: 1.5 })] });
    x = cx + 13;
  });
  cyl("seg3", "shaft", 0, [0, SH.y, SH.z], 7, x, 201, { mat: "steel", spin: true });
}
// followers: a mushroom foot on the cam, a rod split at the guide bar and its collar, a holder, the card
CAM_X.forEach((cx, i) => {
  const ch = i, foot = SH.z + R1;
  cyl(`foot${i}`, "follow", 2, [cx, SH.y, 0], 15, foot, foot + 5, { mat: "steel", tone: "hi", lift: i, chain: ch });
  part({ id: `rodA${i}`, asm: "follow", kind: "cyl", ax: 2, c: [cx, SH.y, 0], r: 4.5, mat: "steel", tone: "hi", chain: ch,
    at: (st) => ({ a0: foot + 5 + st.lift[i], a1: 170 }) });
  cyl(`gcollar${i}`, "follow", 2, [cx, SH.y, 0], 9, 186, 192, { mat: "steel", tone: "mid",
    deco: [DOT([cx, SH.y - 9, 189], [0, -1, 0], { r: 1.3 })] });
  part({ id: `rodB${i}`, asm: "follow", kind: "cyl", ax: 2, c: [cx, SH.y, 0], r: 4.5, mat: "steel", tone: "hi", chain: ch,
    at: (st) => ({ a0: 192, a1: 202 + st.lift[i] }) });
  box(`holder${i}`, "follow", [cx - 24, cx + 24, -40, -20, 202, 213], { tone: "hi", lift: i, chain: ch,
    deco: [L([[cx - 24, -32.5, 213], [cx + 24, -32.5, 213]], [0, 0, 1], { tone: "faint" }), L([[cx - 24, -27.5, 213], [cx + 24, -27.5, 213]], [0, 0, 1], { tone: "faint" })] });
  const face = cardFace(i, cx - 52, -32, 309);                                         // the slot's two lips run edge to edge
  box(`card${i}`, "cards", [cx - 52, cx + 52, -32, -28, 213, 309], { tone: "hi", lift: i, chain: ch, smooth: false,
    deco: i < 2 ? face : (st) => [...face, ...cubeMarks(cx - 52, -32, 309, cubeAngle(st.t))] });
});
// the dial on the right block: ticks every 24° (a major every step of 72°), a needle and hub on the shaft's end
{
  const fx = 228.5, n = [1, 0, 0], ticks = [];
  for (let a = 0; a < 360; a += 24) {
    const major = a % 72 === 0, r0 = major ? 21 : 24, q = (90 - a) * D2R;
    ticks.push(L([[fx, SH.y + r0 * Math.cos(q), SH.z + r0 * Math.sin(q)], [fx, SH.y + 28 * Math.cos(q), SH.z + 28 * Math.sin(q)]], n, { tone: major ? "hi" : "mid" }));
  }
  const rim = ring(28.5, 60).map(([u, v]) => [fx, SH.y + u, SH.z + v]);
  cyl("dial", "dial", 0, [0, SH.y, SH.z], 31, 225, fx, { tone: "mid", deco: [...ticks, L([...rim, rim[0]], n, { tone: "faint" })] });
  prism("needle", "dial", 0, [0, SH.y, SH.z], [[-1.4, -5], [1.4, -5], [0.8, 26], [-0.8, 26]], fx, fx + 1.2, { tone: "hi", spin: true, smooth: false });
  cyl("hub", "dial", 0, [0, SH.y, SH.z], 5, fx + 1.2, fx + 5, { mat: "steel", spin: true });
}
// the drive on the left: a gearbox with a label plate, a motor can with ribs and an end bell
{
  const n = [0, -1, 0], up = [0, 0, 1], label = [], gx0 = -268, gx1 = -229;
  for (const [z, w] of [[96, 1], [90, 0.7], [84, 0.85]]) label.push(L([[-262, -65.6, z], [-262 + 26 * w, -65.6, z]], n, { tone: "mid", free: true }));
  box("gearbox", "gear", [gx0, gx1, -64, 4, 16, 120], { tone: "mid",
    deco: [screw([gx0 + 6, -64, 112], n), screw([gx1 - 6, -64, 112], n), screw([gx0 + 6, -64, 24], n), screw([gx1 - 6, -64, 24], n),
      L([[gx0, -40, 120], [gx1, -40, 120]], up, { tone: "faint" }), L([[gx0, -12, 120], [gx1, -12, 120]], up, { tone: "faint" })] });
  box("plate", "gear", [-264, -233, -66, -64, 78, 104], { tone: "hi", smooth: false, deco: [...label, screw([-261, -66, 101], n), screw([-236, -66, 81], n)] });
  cyl("motor", "gear", 1, [-248.5, 0, SH.z], 25, 4, 70, { mat: "steel", ribs: [14, 20, 26, 32, 38, 44, 50, 56] });
  cyl("bell", "gear", 1, [-248.5, 0, SH.z], 19, 70, 80, { mat: "steel", tone: "mid" });
}

// card faces: the outline's ruled lines, the storyboard's six panels, the draft's film frame
function cardFace(i, x0, y, z1) {
  const n = [0, -1, 0], yy = y - 0.01, P = (u, v) => [x0 + u, yy, z1 - v], out = [], ink = { tone: "ink" };
  const line = (pts, o = {}) => out.push(L(pts.map(([u, v]) => P(u, v)), n, { ...ink, ...o }));
  const rect = (u, v, w, h, o = {}) => line([[u, v], [u + w, v], [u + w, v + h], [u, v + h], [u, v]], o);
  if (i === 0) {
    out.push(FILL([[12, 12], [62, 12], [62, 19], [12, 19]].map(([u, v]) => P(u, v)), n, { tone: "ink", alpha: 0.85 }));
    [[30, 80, 0], [42, 64, 8], [54, 72, 8], [66, 52, 0], [78, 70, 8]].forEach(([v, len, ind]) => {
      out.push(DOT(P(14 + ind, v), n, { r: 1.5, tone: "ink" })); line([[20 + ind, v], [20 + ind + len - ind - 8, v]], { free: true });
    });
  } else if (i === 1) {
    for (let r = 0; r < 2; r++) for (let c = 0; c < 3; c++) {
      const u = 10 + c * 29, v = 12 + r * 40, w = 26, h = 26, k = r * 3 + c;
      rect(u, v, w, h);
      line([[u, v + h * (0.55 + 0.12 * Math.sin(k * 1.7))], [u + w, v + h * (0.62 - 0.1 * Math.cos(k * 2.3))]], { tone: "mid" });
      const cu = u + w * (0.3 + 0.4 * ((k * 0.37) % 1)), cv = v + h * 0.32;
      line(ring(3.2, 14).map(([a, b]) => [cu + a, cv + b]).concat([[cu + 3.2, cv]]), { tone: "mid" });
      line([[u, v + h + 6], [u + w * (0.55 + 0.3 * ((k * 0.61) % 1)), v + h + 6]], { tone: "mid", free: true });
    }
  } else {
    rect(8, 8, 88, 80);
    for (let k = 0; k < 8; k++) { rect(12 + k * 10.5, 11, 6, 4); rect(12 + k * 10.5, 81, 6, 4); }
    rect(14, 20, 76, 56);                              // the picture: a cube, drawn per frame by cubeMarks
  }
  return out;
}
/** The draft's picture: a small cube that turns in 12 fps steps while the shaft holds (each step is one more frame). */
const cubeAngle = (t) => 15 * Math.floor(Math.max(0, t - TL.hold[0]) * 12);
function cubeMarks(x0, y, z1, deg) {
  const n = [0, -1, 0], P = (u, v) => [x0 + u, y - 0.01, z1 - v], c = [52, 50], s = 13, q = deg * D2R, out = [];
  const rot = ([x, y2, z]) => [x * Math.cos(q) - y2 * Math.sin(q), x * Math.sin(q) + y2 * Math.cos(q), z];
  const iso = ([x, y2, z]) => [c[0] + (x - y2) * s * 0.866, c[1] + (x + y2) * s * 0.5 - z * s];
  const faces = [[[1, 0, 0], [[1, -1, -1], [1, 1, -1], [1, 1, 1], [1, -1, 1]]], [[-1, 0, 0], [[-1, -1, -1], [-1, 1, -1], [-1, 1, 1], [-1, -1, 1]]],
    [[0, 1, 0], [[-1, 1, -1], [1, 1, -1], [1, 1, 1], [-1, 1, 1]]], [[0, -1, 0], [[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1]]]];
  for (const [nrm, quad] of faces) {
    const m = rot(nrm); if (m[0] + m[1] <= 1e-6) continue;                  // faces toward the viewer of this little drawing
    const pts = quad.map((v) => iso(rot(v.map((a) => a * 0.5))));
    out.push(FILL(pts.map(([u, v]) => P(u, v)), n, { tone: m[0] - m[1] < 0 ? "shadeA" : "shadeB" }));
    out.push(L([...pts, pts[0]].map(([u, v]) => P(u, v)), n, { tone: "ink" }));
  }
  const top = [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]].map((v) => iso(rot(v.map((a) => a * 0.5))));
  out.push(FILL(top.map(([u, v]) => P(u, v)), n, { tone: "paper" }), L([...top, top[0]].map(([u, v]) => P(u, v)), n, { tone: "ink" }));
  return out;
}

// ───────── posing, ordering, drawing ─────────
function state(t) {
  const th = shaftAngle(t), lift = [0, 1, 2].map((i) => camLift(i, th));
  const apart = {}; for (const a of Object.keys(MOVE)) apart[a] = apartOf(a, t);
  let lit = -1; for (let i = 0; i < 3; i++) { const [a, b] = TL.lit(i); if (t >= a && t < b) lit = i; }
  return { t, th, lift, apart, lit };
}
function poser(p, st) {
  const th = p.spin ? st.th * D2R : 0, c = Math.cos(th), s = Math.sin(th);
  const lz = p.lift != null ? st.lift[p.lift] : 0, m = (st.t < EXPLODE_AT ? OPEN : MOVE)[p.asm], k = st.apart[p.asm];
  const off = [m[0] * k, m[1] * k, m[2] * k + lz];
  const pt = (q) => {
    let [x, y, z] = q;
    if (p.spin) { const dy = y - SH.y, dz = z - SH.z; y = SH.y + dy * c - dz * s; z = SH.z + dy * s + dz * c; }
    return [x + off[0], y + off[1], z + off[2]];
  };
  const nv = (n) => (p.spin ? [n[0], n[1] * c - n[2] * s, n[1] * s + n[2] * c] : n);
  return { pt, nv };
}
const axisPt = (ax, c, a, u, v) => (ax === 0 ? [a, c[1] + u, c[2] + v] : ax === 1 ? [c[0] + u, a, c[2] + v] : [c[0] + u, c[1] + v, a]);
const axisVec = (ax) => (ax === 0 ? [1, 0, 0] : ax === 1 ? [0, 1, 0] : [0, 0, 1]);
/** One part at state st: world vertices, faces with normals, its object-frame bounds, screen points. */
function mesh(p, st, cam) {
  const g = p.at ? { ...p, ...p.at(st) } : p, { pt, nv } = poser(p, st), faces = [];
  let V3;
  if (p.kind === "box") {
    const [x0, x1, y0, y1, z0, z1] = g.b;
    V3 = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]].map(pt);
    for (const [idx, n] of [[[0, 1, 5, 4], [0, -1, 0]], [[1, 2, 6, 5], [1, 0, 0]], [[2, 3, 7, 6], [0, 1, 0]], [[3, 0, 4, 7], [-1, 0, 0]], [[4, 5, 6, 7], [0, 0, 1]], [[0, 3, 2, 1], [0, 0, -1]]])
      faces.push({ idx, n: nv(n), cap: true });
  } else {
    const poly = p.kind === "cyl" ? ring(g.r, 48) : g.poly, n = poly.length;
    V3 = [...poly.map(([u, v]) => pt(axisPt(g.ax, g.c, g.a0, u, v))), ...poly.map(([u, v]) => pt(axisPt(g.ax, g.c, g.a1, u, v)))];
    const A = axisVec(g.ax);
    faces.push({ idx: poly.map((_, k) => k), n: nv(A.map((x) => -x)), cap: true, end: 0 });
    faces.push({ idx: poly.map((_, k) => n + k), n: nv(A), cap: true, end: 1 });
    for (let k = 0; k < n; k++) {
      const [u0, v0] = poly[k], [u1, v1] = poly[(k + 1) % n], du = u1 - u0, dv = v1 - v0;
      let nl = norm(axisPt(g.ax, [0, 0, 0], 0, dv, -du));                     // outward for a counter-clockwise ring
      if (p.kind === "prism" && dot(nl, axisPt(g.ax, [0, 0, 0], 0, (u0 + u1) / 2, (v0 + v1) / 2)) < 0) nl = nl.map((x) => -x);
      faces.push({ idx: [k, (k + 1) % n, n + (k + 1) % n, n + k], n: nv(nl), side: true });
    }
  }
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (const v of V3) for (let a = 0; a < 3; a++) { lo[a] = Math.min(lo[a], v[a]); hi[a] = Math.max(hi[a], v[a]); }
  const P2 = V3.map((v) => project(cam, v));
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const [x, y] of P2) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  const cen = [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2];
  return { p, g, V3, P2, faces, lo, hi, cen, depth: dot(cen, cam.V), sb: [x0, y0, x1, y1], pose: { pt, nv } };
}
/** Painter's order: for every pair that overlaps on screen, a separating axis plane says which is nearer. */
function order(ms, cam) {
  const n = ms.length, after = Array.from({ length: n }, () => []), indeg = new Array(n).fill(0), E = 0.05;
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
    const A = ms[i], B = ms[j];
    if (A.sb[2] < B.sb[0] - 2 || B.sb[2] < A.sb[0] - 2 || A.sb[3] < B.sb[1] - 2 || B.sb[3] < A.sb[1] - 2) continue;
    let best = null, score = -1;
    for (let a = 0; a < 3; a++) {
      const w = Math.abs(cam.V[a]);
      if (A.hi[a] <= B.lo[a] + E) { const sc = (B.lo[a] - A.hi[a] + 1) * w; if (sc > score) { score = sc; best = cam.V[a] > 0 ? [i, j] : [j, i]; } }
      if (B.hi[a] <= A.lo[a] + E) { const sc = (A.lo[a] - B.hi[a] + 1) * w; if (sc > score) { score = sc; best = cam.V[a] > 0 ? [j, i] : [i, j]; } }
    }
    if (!best) best = A.depth < B.depth ? [i, j] : [j, i];                     // touching on every axis: fall back to depth
    after[best[0]].push(best[1]); indeg[best[1]]++;                             // best[0] is drawn before best[1]
  }
  const out = [], done = new Array(n).fill(false);
  for (let k = 0; k < n; k++) {
    let pick = -1;
    for (let i = 0; i < n; i++) if (!done[i] && indeg[i] === 0 && (pick < 0 || ms[i].depth < ms[pick].depth || (ms[i].depth === ms[pick].depth && i < pick))) pick = i;
    if (pick < 0) for (let i = 0; i < n; i++) if (!done[i] && (pick < 0 || ms[i].depth < ms[pick].depth)) pick = i;   // a cycle: farthest first
    done[pick] = true; out.push(ms[pick]);
    for (const j of after[pick]) indeg[j]--;
  }
  return out;
}

let C = null;                                           // colours, read once from the tokens
function colours(tokens, lib) {
  const c = (k) => lib.color(tokens, k);
  const ramp = (m) => ({ top: c(`${m}.top`), shade: [0, 1, 2, 3].map((k) => c(`${m}.shade.${k}`)) });
  return { bg: c("bg"), page: c("page"), fg: c("fg"), text: c("text"), accent: c("accent"), halo: c("halo"),
    ink: { hi: c("ink.hi"), mid: c("ink.mid"), lo: c("ink.lo"), faint: c("ink.faint"), dot: c("ink.dot"), ink: c("ink.dot") },
    mat: { paper: ramp("paper"), steel: ramp("steel"), rubber: ramp("rubber") }, shine: c("steel.shine") };
}
/** 0..1 by facing: 1 = toward the light (azimuth), 0 = away. Flat faces quantise it to four tones; round parts don't. */
function facing(n) {
  let d = Math.abs(Math.atan2(n[1], n[0]) - LIGHT_AZ); if (d > Math.PI) d = 2 * Math.PI - d;
  return 1 - d / Math.PI;
}
function fillOf(lib, mat, n, flat, cam) {
  const M = C.mat[mat];
  const side = flat ? M.shade[Math.min(3, Math.floor(facing(n) * 4))] : lerpRamp(lib, M.shade, facing(n));
  let col = n[2] > 0.7 ? M.top : flat ? side : lib.mixColor(side, M.top, clamp((n[2] - 0.15) / 0.6));
  if (mat === "steel" && !flat) {
    const h = norm([LIGHT[0] + cam.V[0], LIGHT[1] + cam.V[1], LIGHT[2] + cam.V[2]]);
    col = lib.mixColor(col, C.shine, 0.75 * Math.pow(Math.max(0, dot(n, h)), 18));
  }
  return col;
}
const lerpRamp = (lib, r, u) => { const x = clamp(u) * 3, k = Math.min(2, Math.floor(x)); return lib.mixColor(r[k], r[k + 1], x - k); };

const LW = { outline: 1.3, detail: 1.0, lit: 2.2 };
function drawPart(ctx, m, st, cam, lib) {
  const { p, g, V3, P2, faces } = m, lit = p.chain >= 0 && p.chain === st.lit;
  const line = lit ? C.accent : C.ink[p.tone], lw = lit ? LW.lit : LW.outline;
  const tint = (col) => (lit ? lib.mixColor(col, C.accent, 0.1) : col);
  const path = (idx) => { ctx.beginPath(); idx.forEach((k, j) => (j ? ctx.lineTo(P2[k][0], P2[k][1]) : ctx.moveTo(P2[k][0], P2[k][1]))); ctx.closePath(); };
  const seen = (f) => dot(f.n, cam.V) > 1e-4;
  ctx.lineJoin = "round"; ctx.lineCap = "round";
  if (p.kind === "box") {
    for (const f of faces) if (seen(f)) {
      path(f.idx); ctx.fillStyle = tint(fillOf(lib, p.mat, f.n, true, cam)); ctx.fill();
      ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.stroke();
    }
  } else {
    const hull = hull2(P2.map((q) => [q[0], q[1]]));
    const sides = faces.filter((f) => f.side && seen(f));
    if (p.kind === "cyl" && sides.length) {                       // one gradient across the projected width
      const n = g.poly ? g.poly.length : 48, c0 = P2.slice(0, n).reduce((a, q) => [a[0] + q[0] / n, a[1] + q[1] / n], [0, 0]);
      const c1 = P2.slice(n).reduce((a, q) => [a[0] + q[0] / n, a[1] + q[1] / n], [0, 0]);
      let dx = c1[0] - c0[0], dy = c1[1] - c0[1], dl = Math.hypot(dx, dy);
      if (dl < 1e-3) { dx = 1; dy = 0; dl = 1; }
      const px = -dy / dl, py = dx / dl, off = (q) => (q[0] - c0[0]) * px + (q[1] - c0[1]) * py;
      const ws = P2.slice(0, n).map(off), w0 = Math.min(...ws), w1 = Math.max(...ws);
      const grad = ctx.createLinearGradient(c0[0] + px * w0, c0[1] + py * w0, c0[0] + px * w1, c0[1] + py * w1);
      const stops = sides.map((f) => [(off(P2[f.idx[0]]) + off(P2[f.idx[1]])) / 2, f.n]).sort((a, b) => a[0] - b[0]);
      grad.addColorStop(0, tint(fillOf(lib, p.mat, stops[0][1], false, cam)));
      for (const [o, nrm] of stops) grad.addColorStop(clamp((o - w0) / (w1 - w0 || 1)), tint(fillOf(lib, p.mat, nrm, false, cam)));
      grad.addColorStop(1, tint(fillOf(lib, p.mat, stops[stops.length - 1][1], false, cam)));
      ctx.beginPath(); hull.forEach((q, j) => (j ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.closePath();
      ctx.fillStyle = grad; ctx.fill();
    } else {
      for (const f of sides) {                                    // prisms: facet by facet (smooth or flat tones)
        path(f.idx); const col = tint(fillOf(lib, p.mat, f.n, !p.smooth, cam));
        ctx.fillStyle = col; ctx.fill(); ctx.strokeStyle = p.smooth ? col : line; ctx.lineWidth = p.smooth ? 0.8 : lw; ctx.stroke();
      }
    }
    for (const f of faces) if (f.cap && seen(f)) { path(f.idx); ctx.fillStyle = tint(fillOf(lib, p.mat, f.n, true, cam)); ctx.fill(); ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.stroke(); }
    if (p.ribs) {                                                 // ribs round a can: the visible half of each ring
      ctx.strokeStyle = C.ink.lo; ctx.lineWidth = LW.detail;
      for (const a of p.ribs) {
        const pts = ring(g.r, 48).map(([u, v]) => ({ q: project(cam, m.pose.pt(axisPt(g.ax, g.c, a, u, v))), n: m.pose.nv(norm(axisPt(g.ax, [0, 0, 0], 0, u, v))) }));
        ctx.beginPath(); let on = false;
        for (const { q, n } of [...pts, pts[0]]) { if (dot(n, cam.V) > 0.02) { if (on) ctx.lineTo(q[0], q[1]); else ctx.moveTo(q[0], q[1]); on = true; } else on = false; }
        ctx.stroke();
      }
    }
    ctx.beginPath(); hull.forEach((q, j) => (j ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1]))); ctx.closePath();
    ctx.strokeStyle = line; ctx.lineWidth = lw; ctx.stroke();
  }
  for (const d of typeof p.deco === "function" ? p.deco(st) : p.deco) {   // surface marks on faces that face the viewer
    if (dot(m.pose.nv(d.n), cam.V) <= 1e-3) continue;
    const col = d.tone === "ink" ? C.ink.dot : d.tone === "paper" ? C.mat.paper.top : d.tone === "shadeA" ? C.mat.paper.shade[2] : d.tone === "shadeB" ? C.mat.paper.shade[0] : C.ink[d.tone || "mid"];
    if (d.type === "line") {
      ctx.beginPath(); d.pts.forEach((q, j) => { const s = project(cam, m.pose.pt(q)); if (j) ctx.lineTo(s[0], s[1]); else ctx.moveTo(s[0], s[1]); });
      ctx.strokeStyle = col; ctx.lineWidth = LW.detail; ctx.stroke();
    } else if (d.type === "fill") {
      ctx.beginPath(); d.pts.forEach((q, j) => { const s = project(cam, m.pose.pt(q)); if (j) ctx.lineTo(s[0], s[1]); else ctx.moveTo(s[0], s[1]); });
      ctx.closePath(); ctx.globalAlpha = d.alpha ?? 1; ctx.fillStyle = col; ctx.fill(); ctx.globalAlpha = 1;
    } else {
      const s = project(cam, m.pose.pt(d.p)), r = (d.r ?? 1.1) * Math.sqrt(cam.s / SCALE);
      if (d.ring) { ctx.beginPath(); ctx.arc(s[0], s[1], r * 2.4, 0, 2 * Math.PI); ctx.strokeStyle = C.ink.lo; ctx.lineWidth = LW.detail; ctx.stroke(); }
      ctx.beginPath(); ctx.arc(s[0], s[1], r * 1.2, 0, 2 * Math.PI); ctx.fillStyle = C.ink.dot; ctx.fill();
    }
  }
}
function drawMachine(ctx, t, lib) {
  const st = state(t), cam = camera(t), ms = PARTS.map((p) => mesh(p, st, cam));
  // the halo under the base: its footprint, blurred
  const fp = [[-292, -114], [292, -114], [292, 84], [-292, 84]].map(([x, y]) => project(cam, [x, y + 6, -4]));
  ctx.save(); ctx.filter = `blur(${Math.round(18 * cam.s / SCALE)}px)`; ctx.globalAlpha = 0.32; ctx.fillStyle = C.halo;
  ctx.beginPath(); fp.forEach((q, j) => (j ? ctx.lineTo(q[0], q[1] + 10) : ctx.moveTo(q[0], q[1] + 10))); ctx.closePath(); ctx.fill(); ctx.restore();
  for (const m of order(ms, cam)) drawPart(ctx, m, st, cam, lib);
  return st;
}
/** How far the picture moves in one frame (px): the parts' centres between t ± half a frame. */
function speed(t) {
  const h = 0.5 / FPS, a = state(t - h), b = state(t + h), ca = camera(t - h), cb = camera(t + h);
  let m = 0;
  for (const p of PARTS) {
    const pa = poser(p, a).pt(p.kind === "box" ? [(p.b[0] + p.b[1]) / 2, (p.b[2] + p.b[3]) / 2, p.b[5]] : axisPt(p.ax, p.c, p.a1 ?? 0, 0, 0));
    const pb = poser(p, b).pt(p.kind === "box" ? [(p.b[0] + p.b[1]) / 2, (p.b[2] + p.b[3]) / 2, p.b[5]] : axisPt(p.ax, p.c, p.a1 ?? 0, 0, 0));
    const sa = project(ca, pa), sb = project(cb, pb);
    m = Math.max(m, Math.hypot(sa[0] - sb[0], sa[1] - sb[1]));
  }
  return m;
}

// ───────── the plate: frame, corner labels, title, legend ─────────
const PLATE = { x0: 64, y0: 40, x1: 1856, y1: 1040 };
function settle(t0, t, w = 18) { const tau = t - t0; return tau <= 0 ? 0 : 1 - Math.exp(-w * tau) * (1 + w * tau); }
/** Text rises out of a hairline slot: each glyph comes up from under the line on a critically damped spring. */
function slotText(ctx, lib, str, x, y, size, t0, stag, t, { color, tracking = 0 } = {}) {
  const lay = lib.layoutText(ctx, str, { x, y, tracking });
  ctx.save(); ctx.beginPath(); ctx.rect(x - 20, y - size * 1.4, lay.width + 40, size * 1.4 + size * 0.28); ctx.clip();
  ctx.fillStyle = color;
  lib.drawGlyphs(ctx, lay, (g, i) => { const u = settle(t0 + i * stag, t); return u <= 0 ? null : { dy: (1 - u) * size * 1.25 }; });
  ctx.restore();
  return lay;
}
function plate(ctx, t, tokens, lib, st) {
  const { x0, y0, x1, y1 } = PLATE, size = 44;                     // the desktop tier's floor for labels and readouts
  ctx.strokeStyle = C.ink.mid; ctx.lineWidth = 1.2; ctx.strokeRect(x0 + 0.5, y0 + 0.5, x1 - x0, y1 - y0);
  lib.setFont(ctx, tokens, "mono", size); ctx.textBaseline = "alphabetic";
  const tr = lib.tracking(tokens, "mono", size) * 0.5;
  const corner = (s, x, y, align, col) => { ctx.fillStyle = col; lib.drawText(ctx, s, x, y, { align, tracking: tr }); };
  corner("Fig 1", 104, 112, "left", C.fg);
  corner("CAM TIMER", x1 - 40, 112, "right", C.text);
  // hint: a phase word, read from where the parts are (the same instant as the readout)
  const stepping = t >= STEPS[0] && t < STEPS[2] + STEP_DUR;       // one phase for all three steps: no 4-frame flicker
  const parts = PARTS.length, asms = new Set(PARTS.map((p) => p.asm)).size;
  let hint, read;
  if (t < EXPLODE_AT) {
    hint = t < homeAt ? "CLOSING UP" : stepping ? "INDEXING" : t < STEPS[0] ? "1 SHAFT · 3 CAMS" : "HOLDING";
    read = `θ ${st.th.toFixed(1)}° · f ${String(Math.round(t * FPS)).padStart(3, "0")}`;
  } else {
    const settled = Object.keys(MOVE).every((a) => a === "base" || Math.abs(1 - st.apart[a]) < 0.02);
    hint = settled ? "TAKEN APART" : "TAKING APART";
    read = `${parts} parts · ${asms} assemblies`;
  }
  corner(hint, 104, y1 - 34, "left", C.text);
  corner(read, x1 - 40, y1 - 34, "right", C.fg);
}
function titles(ctx, t, tokens, lib, st) {
  const X = 192, EN = 88, ZH = 64, LEG = 44;
  // the slot lines the title rises out of
  const rule = (y, t0, w) => { const u = lib.ease.outCubic(seg(t, t0, t0 + 0.35)); if (u <= 0) return; ctx.strokeStyle = C.ink.lo; ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(X, y + 0.5); ctx.lineTo(X + w * u, y + 0.5); ctx.stroke(); };
  rule(LINES.en[0] + 20, TL.slots, 600); rule(LINES.en[1] + 20, TL.slots + 0.08, 600); rule(LINES.zh + 18, TL.slots + 0.16, 600);
  lib.setFont(ctx, tokens, "display", EN);
  const words = lib.TITLE_EN.split(" "), w1 = words.slice(0, 2).join(" "), w2 = words.slice(2).join(" "), trEn = lib.tracking(tokens, "display", EN);
  slotText(ctx, lib, w1, X, LINES.en[0], EN, TL.title, TL.titleStag, t, { color: C.fg, tracking: trEn });
  slotText(ctx, lib, w2, X, LINES.en[1], EN, TL.title + (w1.length + 1) * TL.titleStag, TL.titleStag, t, { color: C.fg, tracking: trEn });
  lib.setFont(ctx, tokens, "zh", ZH);
  slotText(ctx, lib, lib.TITLE_ZH, X, LINES.zh, ZH, TL.zh, TL.zhStag, t, { color: C.fg, tracking: lib.tracking(tokens, "zh", ZH) });
  // legend: the three rows rise together, grey, before the first step; the row of the lit card takes the accent
  lib.MOTIF.forEach((m, i) => {
    const t0 = TL.legend + i * 0.06, y = LINES.legend + i * 76, on = st.lit === i, col = on ? C.accent : C.fg;
    if (t < t0 - 0.12) return;
    rule(y + 18, t0 - 0.1, 470);
    const u = settle(t0, t, 16);
    ctx.save(); ctx.beginPath(); ctx.rect(X - 10, y - 60, 520, 78); ctx.clip(); ctx.translate(0, (1 - u) * 64);
    lib.setFont(ctx, tokens, "mono", LEG); ctx.fillStyle = on ? C.accent : C.text; lib.drawText(ctx, `0${i + 1}`, X, y);
    lib.setFont(ctx, tokens, "zh", 48); ctx.fillStyle = col; lib.drawText(ctx, m.zh, X + 84, y, { tracking: lib.tracking(tokens, "zh", 48) });
    lib.setFont(ctx, tokens, "body", LEG); ctx.fillStyle = on ? C.accent : C.text; lib.drawText(ctx, m.en, X + 204, y);
    ctx.restore();
  });
}
const LINES = { en: [300, 400], zh: 508, legend: 650 };

export async function setup(ctx, tokens, lib) { C = colours(tokens, lib); }

export function renderAt(t, ctx, tokens, lib) {
  if (!C) C = colours(tokens, lib);
  ctx.fillStyle = C.page; ctx.fillRect(0, 0, lib.W, lib.H);
  ctx.fillStyle = C.bg; ctx.fillRect(PLATE.x0, PLATE.y0, PLATE.x1 - PLATE.x0, PLATE.y1 - PLATE.y0);
  // the instrument, with motion blur sized to how far the picture moves this frame (holds get one sample)
  const n = clamp(Math.ceil(speed(t) * 0.5 / 1.6), 1, 24);
  let st = null;
  if (n <= 1) st = drawMachine(ctx, t, lib);
  else { lib.motionBlur(ctx, t, (ts, c) => { drawMachine(c, ts, lib); }, { samples: n, shutter: 0.5 }); st = state(t); }
  plate(ctx, t, tokens, lib, st);
  titles(ctx, t, tokens, lib, st);
}
