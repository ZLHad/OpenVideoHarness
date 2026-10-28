// build-up — a set of pieces (bricks, the floors of a building, the spans of a bridge, the parts of a machine) that
// appear one after another by a rule until the whole stands. The rule is an order (by height, by distance from a point,
// by index, or shuffled with a seed; pieces whose keys fall in one bucket start together), a rhythm (the gap between
// one rank and the next, a seeded jitter, how long each piece takes and its ease) and a way in (rising from below,
// dropping from above, growing from its base, fading in). state(params, t) is geometry and time only; two painters draw
// it: canvas (2.5D blocks in an isometric view, for the sample and for films without 3D) and three (the matrices of a
// Three.js InstancedMesh: canvas-film's Three.js layer, or any Three.js scene; three is passed in, not imported).
import { clamp, easeOf, hash, seg } from "../lib/core.js";

export const defaults = {
  pieces: [],           // [{ x, y, z, w, h, d, color? }]: each box's centre and size (y up), in the scene's units
  order: "height",      // height (its base, low first), distance (its centre from `from`, near first), index, random
  from: [0, 0, 0],      // the point the distance order measures from
  reverse: false,       // the order turned round (high first, far first, the last index first)
  bucket: 0,            // > 0: keys rounded down to this step, so a whole floor (bucket = a floor's height) starts as one
  start: 0,             // s: when the first rank starts
  stagger: 0.08,        // s: from one rank's start to the next's
  jitter: 0,            // s: each piece starts up to this much later, by a hash of seed and its index
  dur: 0.5,             // s: how long one piece takes to come in
  ease: "outCubic",     // its curve: a lib/core.js ease name, a CSS curve or [x1, y1, x2, y2]
  appear: "rise",       // rise (from lift below), drop (from lift above), grow (from its base), fade
  lift: 1,              // how far a rising or dropping piece travels, in the scene's units
  seed: 1,              // for the random order and the jitter
};
const opts = (p) => ({ ...defaults, ...p });
const ORDERS = ["height", "distance", "index", "random"], WAYS = ["rise", "drop", "grow", "fade"];

// each params object's ranks and start times, worked out once (they depend on params alone: change a copy, not the object)
const PLANS = new WeakMap();
/** → { t0: [each piece's start], rank: [each piece's rank], ranks, end (s: when the last piece is in) }. */
export function plan(params) {
  if (params && PLANS.has(params)) return PLANS.get(params);
  const p = opts(params), n = p.pieces.length;
  if (!ORDERS.includes(p.order)) throw new Error(`build-up: order is ${ORDERS.join(", ")}, not ${JSON.stringify(p.order)}`);
  if (!WAYS.includes(p.appear)) throw new Error(`build-up: appear is ${WAYS.join(", ")}, not ${JSON.stringify(p.appear)}`);
  const key = p.pieces.map((q, i) => {
    let k = p.order === "height" ? q.y - q.h / 2 : p.order === "distance" ? Math.hypot(q.x - p.from[0], q.y - p.from[1], q.z - p.from[2])
      : p.order === "index" ? i : hash(p.seed, i, 101);
    if (p.bucket > 0) k = Math.floor(k / p.bucket + 1e-9);
    return p.reverse ? -k : k;
  });
  const ids = key.map((_, i) => i).sort((a, b) => key[a] - key[b] || a - b);
  const rank = new Array(n);
  let r = -1;
  ids.forEach((i, k) => { if (k === 0 || key[i] !== key[ids[k - 1]]) r++; rank[i] = r; });   // one rank a distinct key
  const t0 = rank.map((rk, i) => p.start + rk * p.stagger + (p.jitter > 0 ? p.jitter * hash(p.seed, i, 202) : 0));
  const out = { t0, rank, ranks: r + 1, end: n ? Math.max(...t0) + p.dur : p.start };
  if (params) PLANS.set(params, out);
  return out;
}

/** How long the whole build takes from t = 0 (the last piece in): for a shot's length, or a cue's place. */
export const duration = (params) => plan(params).end;

/**
 * The build at t: { t, n, started, done, pieces: [{ i, rank, t0, u (0 → 1, eased), on (u > 0), box: { x, y, z, w, h, d }
 * (where it is drawn now), alpha, color }] }. A piece before its start is off; a grown one grows from its base.
 */
export function state(params, t) {
  const p = opts(params), P = plan(params), e = easeOf(p.ease);
  let started = 0, done = 0;
  const pieces = p.pieces.map((q, i) => {
    const v = seg(t, P.t0[i], P.t0[i] + p.dur), u = clamp(e(v));
    if (v > 0) started++;
    if (v >= 1) done++;
    let { x, y, z, w, h, d } = q, alpha = 1;
    if (p.appear === "rise") y -= (1 - u) * p.lift;
    else if (p.appear === "drop") y += (1 - u) * p.lift;
    else if (p.appear === "grow") { const base = y - h / 2; w *= u; d *= u; h *= u; y = base + h / 2; }
    else alpha = u;
    return { i, rank: P.rank[i], t0: P.t0[i], u, on: v > 0, box: { x, y, z, w, h, d }, alpha, color: q.color };
  });
  return { t, n: pieces.length, started, done, pieces };
}

// ---- canvas: 2.5D blocks, seen from (+x, +y, +z) ----
// view: { origin: [x, y] (px: where the scene's 0, 0, 0 is drawn), scale (px a unit), angle (degrees the ground's axes
// rise from the horizontal, 30 for true isometric), color (a piece's colour when it has none), shade [top, +x face,
// +z face] (multipliers), edge (an outline colour, or null) }
const VIEW = { origin: [960, 760], scale: 60, angle: 30, color: "#c8643c", shade: [1.12, 0.92, 0.7], edge: null };
const rgb = (hex) => { const h = hex.replace("#", ""), v = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16); return [(v >> 16) & 255, (v >> 8) & 255, v & 255]; };
const tone = (hex, k) => `rgb(${rgb(hex).map((c) => Math.round(clamp(c * k, 0, 255))).join(",")})`;

/** Where a point of the scene lands on screen in this view: [x, y] px. */
export function project(view, x, y, z) {
  const v = { ...VIEW, ...view }, a = (v.angle * Math.PI) / 180, s = v.scale;
  return [v.origin[0] + (x - z) * Math.cos(a) * s, v.origin[1] + ((x + z) * Math.sin(a) - y) * s];
}

/** Canvas painter: each piece that is on, as a block with its top and its two faces toward the viewer, far ones first. */
export function canvas(ctx, st, params, view = {}) {
  const v = { ...VIEW, ...view };
  const on = st.pieces.filter((q) => q.on && q.alpha > 0 && q.box.w > 0 && q.box.h > 0 && q.box.d > 0);
  on.sort((a, b) => (a.box.x + a.box.y + a.box.z) - (b.box.x + b.box.y + b.box.z) || a.i - b.i);
  for (const q of on) {
    const { x, y, z, w, h, d } = q.box, x0 = x - w / 2, x1 = x + w / 2, y0 = y - h / 2, y1 = y + h / 2, z0 = z - d / 2, z1 = z + d / 2;
    const P = (a, b, c) => project(v, a, b, c), col = q.color || v.color;
    const faces = [
      [[P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)], v.shade[0]],   // top
      [[P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1)], v.shade[1]],   // the +x face
      [[P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)], v.shade[2]],   // the +z face
    ];
    ctx.save();
    ctx.globalAlpha *= q.alpha;
    for (const [pts, k] of faces) {
      ctx.beginPath(); pts.forEach(([px, py], j) => (j ? ctx.lineTo(px, py) : ctx.moveTo(px, py))); ctx.closePath();
      ctx.fillStyle = tone(col, k); ctx.fill();
      if (v.edge) { ctx.strokeStyle = v.edge; ctx.lineWidth = 1.5; ctx.lineJoin = "round"; ctx.stroke(); }
    }
    ctx.restore();
  }
}

/**
 * Three.js painter: the matrices of an InstancedMesh of a unit box (THREE.BoxGeometry(1, 1, 1)) with params.pieces.length
 * instances, set for every piece every frame (a piece that is off is scaled to nothing), and each piece's colour when it
 * has one. THREE is the three.js namespace (window.THREE in canvas-film's layer). An InstancedMesh has no opacity of its
 * own a piece: fade draws as grow there. Culling is turned off: three would take the instances' bounds once, from the
 * frame it first drew.
 */
export function three(mesh, st, params, THREE) {
  const m = new THREE.Matrix4(), pos = new THREE.Vector3(), scl = new THREE.Vector3(), rot = new THREE.Quaternion(), c = new THREE.Color();
  const fade = opts(params).appear === "fade", grow = (q) => {   // fade as grow: about its base, by u
    const { x, y, z, w, h, d } = q.box, base = y - h / 2;
    return { x, y: base + (h * q.u) / 2, z, w: w * q.u, h: h * q.u, d: d * q.u };
  };
  for (const q of st.pieces) {
    const b = fade ? grow(q) : q.box, k = q.on ? 1 : 0;
    m.compose(pos.set(b.x, b.y, b.z), rot, scl.set(b.w * k, b.h * k, b.d * k));
    mesh.setMatrixAt(q.i, m);
    if (q.color) mesh.setColorAt(q.i, c.set(q.color));
  }
  mesh.instanceMatrix.needsUpdate = true;
  if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
  mesh.frustumCulled = false;
}
