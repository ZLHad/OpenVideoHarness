// Chalkboard: chalk on a slate-green board in a lecture hall. The felt eraser is half the style: it wipes, and what it
// wipes stays behind as a pale haze of dust, under whatever is written next.
//
//   0.0–1.5  world      the eraser drags a long swath through yesterday's ghosts (dust falls), and the axes go up
//   1.5–4.5  signature  a first guess (a straight line) is drawn, scrubbed out, and the right curve is drawn over its
//                       dust in yellow chalk; three dots and their times
//   4.5–9.0  type       the title, its English line and the caption are chalked, then held to be read
//   9.0–10   close      the board slides up (a double sliding board) and the next panel comes up with the same
//                       ghosts; the eraser is back where it started: the last frame is the first again
//
// One table (T) drives strokes, eraser, foley (FOLEY → events.json; custom_sfx.py makes the chalk sounds to the same
// durations) and reads. Strokes and the pen come from styles/_swatch/vendor/hand.js.
import { prep, ellipse, drawStroke, pen, drawn, mj, glyphPasses, smear } from "../../vendor/hand.js";

export const fonts = ["HanziPen SC", "Chalkduster"];

const XS = 0.07, S = 0.14, M = 0.35, L = 0.5;
const T = {
  sweep: [0.10, 0.95], away1: [0.95, 1.45],                              // world: the long wipe, then the eraser goes
  yAxis: 0.92, xAxis: 1.22, hLab: 1.62, tLab: 1.80,                       // axes and their letters
  guess: 2.00, scrubIn: [2.25, 2.45], scrub: [2.45, 3.05], away2: [3.05, 3.5],   // the wrong line, scrubbed out
  curve: 3.12, dots: [3.70, 3.84, 3.98], drops: [4.08, 4.20, 4.32],       // the right curve, three moments, their times
  title: [4.60, 0.11], en: [5.66, 0.32], caption: [6.09, 0.06],           // type
  read: 9.0,
  slide: [9.0, 9.95], back: [9.15, 9.95],                                 // close: the board slides, the eraser returns
};
const pan = (u) => Math.round((2 * u - 1) * 70) / 100;

export const FOLEY = [
  { t: T.sweep[0], sfx: "sfx/eraser_sweep.wav", gain_db: -5, pan: -0.2, role: "hero" },
  { t: T.yAxis, sfx: "sfx/chalk_M_a.wav", gain_db: -8, pan: pan(0.17), role: "detail" },
  { t: T.xAxis, sfx: "sfx/chalk_M_b.wav", gain_db: -8, pan: pan(0.35), role: "detail" },
  { t: T.hLab, sfx: "sfx/chalk_S_a.wav", gain_db: -10, pan: pan(0.16), role: "detail" },
  { t: T.tLab, sfx: "sfx/chalk_S_b.wav", gain_db: -10, pan: pan(0.57), role: "detail" },
  { t: T.guess, sfx: "sfx/chalk_M_a.wav", gain_db: -7, pan: pan(0.34), role: "detail" },
  { t: T.scrub[0], sfx: "sfx/eraser_scrub.wav", gain_db: -5, pan: pan(0.34), role: "hero" },
  { t: T.curve, sfx: "sfx/chalk_L.wav", gain_db: -7, pan: pan(0.36), role: "detail" },
  { t: T.dots[0], sfx: "sfx/chalk_taps.wav", gain_db: -8, pan: pan(0.36), role: "detail" },
  { t: T.drops[0], sfx: "sfx/chalk_taps_b.wav", gain_db: -10, pan: pan(0.36), role: "detail" },
  { t: T.title[0], sfx: "sfx/chalk_write_title.wav", gain_db: -8, pan: pan(0.7), role: "detail" },
  { t: T.caption[0], sfx: "sfx/chalk_write_caption.wav", gain_db: -6, pan: 0, role: "detail" },
  { t: T.slide[0] + 0.05, sfx: "whoosh", gain_db: -9, dur: 0.9, center: 380, dir: "down", tone: 0.2, pan: 0 },   // the panel rolls up
];

export function texts(lib) {
  const n = (s) => [...s].length;
  return [
    { text: lib.TITLE_ZH, start: +(T.title[0] + n(lib.TITLE_ZH) * T.title[1]).toFixed(3), end: T.read },
    { text: lib.TITLE_EN, start: +(T.en[0] + T.en[1]).toFixed(3), end: T.read },
    { text: lib.CAPTION_ZH, start: +(T.caption[0] + n(lib.CAPTION_ZH) * T.caption[1]).toFixed(3), end: T.read },
  ];
}

let G = null;

export async function setup(ctx, tokens, lib) {
  const { W, H, PORTRAIT: P, SAFE, TYPE } = lib;
  const g = { rail: 44 };
  const st = (pts, o = {}) => prep(pts, { step: 4, wobble: o.wobble ?? 1.4, seed: o.seed ?? 1 });
  // the plot: axes, a wrong straight guess, the right curve (a throw: height over time), three moments on it
  const O = P ? { x: 170, y: 900, top: 430, right: 930 } : { x: 330, y: 560, top: 165, right: 1060 };
  g.yAxis = st([[O.x, O.y + 8], [O.x - 2, O.top]], { seed: 2, wobble: 1.8 });
  g.xAxis = st([[O.x - 8, O.y], [O.right, O.y - 4]], { seed: 3, wobble: 2 });
  const hx = O.x - 32, hy = O.top + 4;
  g.hLab = st([[hx, hy - 30], [hx, hy + 18], [hx, hy - 2], [hx + 8, hy - 9], [hx + 17, hy - 6], [hx + 19, hy + 18]], { seed: 4, wobble: 0.5 });
  const tx = O.right + 30, ty = O.y + 4;
  g.tLab = st([[tx, ty - 30], [tx, ty + 12], [tx + 4, ty + 18], [tx + 14, ty + 16], [tx + 15, ty + 10], [tx - 10, ty - 16], [tx + 14, ty - 18]], { seed: 5, wobble: 0.4 });
  const x0 = O.x + 14, x1 = O.right - 20, xm = (x0 + x1) / 2, span = (x1 - x0) / 2, hgt = (O.y - O.top) * 0.82;
  const yOf = (x) => O.y - 6 - (1 - ((x - xm) / span) ** 2) * hgt;
  g.guess = st([[x0, O.y - 12], [x1 - 60, O.top + 50]], { seed: 6, wobble: 2.2 });
  g.curve = st(Array.from({ length: 41 }, (_, i) => { const x = x0 + (x1 - x0) * i / 40; return [x, yOf(x)]; }), { seed: 7, wobble: 1.6 });
  const dx = [xm - span * 0.62, xm, xm + span * 0.62];
  g.dotAt = dx.map((x) => [x, yOf(x)]);
  g.dots = g.dotAt.map(([x, y], k) => {
    const pts = ellipse(x, y, 9, 9, 0, Math.PI * 2 + 0.6, 18);
    for (let i = 0; i <= 24; i++) { const a = i * 0.9, r = 8 * (1 - i / 24); pts.push([x + Math.cos(a) * r, y + Math.sin(a) * r]); }
    return st(pts, { seed: 8 + k, wobble: 0.3 });
  });
  g.drops = g.dotAt.map(([x, y], k) => Object.assign(st([[x, y + 18], [x + 1, O.y - 6]], { seed: 12 + k, wobble: 0.6 }), { dash: true }));
  const seq = [
    [g.yAxis, T.yAxis, M, "chalk"], [g.xAxis, T.xAxis, M, "chalk"], [g.hLab, T.hLab, S, "chalk"], [g.tLab, T.tLab, S, "chalk"],
    [g.guess, T.guess, M, "chalk"], [g.curve, T.curve, L, "yellow"],
    ...g.dots.map((s, k) => [s, T.dots[k], XS, "pink"]), ...g.drops.map((s, k) => [s, T.drops[k], XS, "pink"]),
  ];
  g.strokes = seq.map(([s, t0, dur, c]) => Object.assign(s, { t0, dur, ink: c }));
  // the eraser: a long wipe through the ghosts, then a scrub along the wrong line
  const A = SAFE.action;
  g.eStart = P ? [230, 560] : [230, 330];
  g.sweep = st(P ? [g.eStart, [520, 600], [880, 560], [1000, 610]] : [g.eStart, [700, 380], [1150, 320], [1560, 360]], { seed: 20, wobble: 6 });
  const a = g.guess.pts[0], b = g.guess.pts[g.guess.pts.length - 1];
  const zig = [];
  for (let i = 0; i <= 10; i++) {
    const u = i / 10, side = (i % 2 ? 1 : -1) * 34;
    zig.push([a[0] + (b[0] - a[0]) * u + side * 0.5, a[1] + (b[1] - a[1]) * u + side]);
  }
  g.scrub = st(zig, { seed: 21, wobble: 3 });
  g.eSize = P ? [210, 86] : [230, 92];
  g.offL = [-320, P ? 1300 : 900];                                   // where the eraser goes when it is put down
  // text: the title in two lines beside the plot (landscape) or under it (portrait)
  lib.setFont(ctx, tokens, "zh", 10);
  const tsz = P ? TYPE.title : TYPE.title;
  const lines = [];
  const mk = (role, str, size, x, y, align, t0, per, ink) => {
    lib.setFont(ctx, tokens, role, size);
    const lay = lib.layoutText(ctx, str, { x, y, align, tracking: lib.tracking(tokens, role, size) });
    const passes = glyphPasses(lay, size, t0, per);
    passes.forEach((p) => (p.ink = ink));
    lines.push({ role, size, lay, passes, ink });
    return passes.length;
  };
  const [l1, l2] = ["每一帧，", "都是代码。"];
  const ok = lib.TITLE_ZH === l1 + l2;
  const halves = ok ? [l1, l2] : [lib.TITLE_ZH, ""];
  const tx0 = P ? W / 2 : 1180, align = P ? "center" : "left";
  const y1 = P ? 1170 : 330, y2 = y1 + tsz * 1.25;
  const n1 = mk("zh", halves[0], tsz, tx0, y1, align, T.title[0], T.title[1], "chalk");
  if (halves[1]) mk("zh", halves[1], tsz, tx0, y2, align, T.title[0] + n1 * T.title[1], T.title[1], "chalk");
  const enN = [...lib.TITLE_EN].length;
  mk("display", lib.TITLE_EN, TYPE.label, tx0, (halves[1] ? y2 : y1) + (P ? 100 : 86), align, T.en[0], T.en[1] / enN, "blue");
  mk("zh", lib.CAPTION_ZH, TYPE.caption, W / 2, SAFE.title.y1 - TYPE.caption * 0.6, "center", T.caption[0], T.caption[1], "chalk");
  g.lines = lines;
  g.penPath = [...g.strokes, ...lines.flatMap((l) => l.passes)].sort((p, q) => p.t0 - q.t0);
  g.rest0 = P ? [300, 1000] : [480, 640];
  g.park = P ? [880, 1500] : [1640, 640];
  // textures, made once: the board (slate green, mottled), yesterday's ghosts, the dust of a wipe, chalk grain
  g.base = boardBase(tokens, lib);
  g.ghosts = ghostLayer(tokens, lib);
  g.streaks = streakLayer(tokens, lib);
  g.grain = {};
  for (const k of ["chalk", "yellow", "pink", "blue"]) g.grain[k] = grainTile(lib.color(tokens, k), 77 + k.length);
  g.holes = holeTile();
  G = g;
}

function canvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }

function boardBase(tokens, lib) {
  const { W, H } = lib;
  const c = canvas(W, H), x = c.getContext("2d"), r = lib.rng(5);
  x.fillStyle = lib.color(tokens, "bg"); x.fillRect(0, 0, W, H);
  x.filter = "blur(40px)";
  for (let i = 0; i < 26; i++) {
    x.fillStyle = r() < 0.5 ? "rgba(0,0,0,0.07)" : "rgba(255,255,255,0.035)";
    x.beginPath(); x.ellipse(r() * W, r() * H, 120 + r() * 300, 60 + r() * 160, r() * 3, 0, 7); x.fill();
  }
  x.filter = "none";
  const img = x.getImageData(0, 0, W, H), d = img.data;
  for (let i = 0; i < d.length; i += 4) { const n = (r() - 0.5) * 10; d[i] += n; d[i + 1] += n; d[i + 2] += n; }
  x.putImageData(img, 0, 0);
  return c;
}

/** yesterday's lesson, wiped: blurred curves, a few formula-like squiggles and the long arcs of the eraser */
function ghostLayer(tokens, lib) {
  const { W, H } = lib;
  const c = canvas(W, H), x = c.getContext("2d"), r = lib.rng(19);
  const dust = lib.color(tokens, "dust");
  x.lineCap = "round";
  x.filter = "blur(3px)";
  for (let i = 0; i < 16; i++) {           // squiggles: the shapes of old writing, unreadable
    const cx = 80 + r() * (W - 160), cy = 60 + r() * (H - 120), n = 4 + Math.floor(r() * 8);
    x.strokeStyle = lib.rgba(dust, 0.06 + r() * 0.07); x.lineWidth = 5;
    x.beginPath(); x.moveTo(cx, cy);
    for (let k = 0; k < n; k++) x.quadraticCurveTo(cx + k * 34 + 12, cy - 30 + r() * 60, cx + (k + 1) * 34, cy + (r() - 0.5) * 24);
    x.stroke();
  }
  for (let i = 0; i < 5; i++) {            // a few old curves and lines
    x.strokeStyle = lib.rgba(dust, 0.05 + r() * 0.05); x.lineWidth = 6;
    const ax = r() * W, ay = r() * H;
    x.beginPath(); x.moveTo(ax, ay); x.bezierCurveTo(ax + 200, ay - 200 * r(), ax + 400, ay + 200 * r(), ax + 600 * r() + 200, ay); x.stroke();
  }
  x.filter = "blur(14px)";
  for (let i = 0; i < 9; i++) {            // the eraser's arcs: wide, soft
    x.strokeStyle = lib.rgba(dust, 0.03 + r() * 0.035); x.lineWidth = 70 + r() * 50;
    const cx = r() * W, cy = r() * H, rr = 200 + r() * 400;
    x.beginPath(); x.ellipse(cx, cy, rr, rr * 0.35, (r() - 0.5) * 0.4, 3.4, 6.0); x.stroke();
  }
  x.filter = "none";
  return c;
}

/** the dust a fresh wipe leaves: fine horizontal striations, the felt's grain dragged across the board */
function streakLayer(tokens, lib) {
  const { W, H } = lib;
  const c = canvas(W, H), x = c.getContext("2d"), r = lib.rng(23);
  const dust = lib.color(tokens, "dust");
  x.filter = "blur(1.5px)";
  for (let i = 0; i < 900; i++) {
    const y = r() * H, x0 = r() * W, len = 60 + r() * 380;
    x.strokeStyle = lib.rgba(dust, 0.04 + r() * 0.09); x.lineWidth = 1 + r() * 2.5;
    x.beginPath(); x.moveTo(x0, y); x.quadraticCurveTo(x0 + len / 2, y + (r() - 0.5) * 10, x0 + len, y + (r() - 0.5) * 16); x.stroke();
  }
  x.filter = "blur(10px)";
  x.fillStyle = lib.rgba(dust, 0.045); x.fillRect(0, 0, W, H);
  x.filter = "none";
  return c;
}

/** chalk: a colour with holes where the stick skipped over the board's tooth */
function grainTile(col, seed) {
  const c = canvas(96, 96), x = c.getContext("2d"), img = x.createImageData(96, 96), d = img.data;
  const [R, Gc, B] = [1, 3, 5].map((i) => parseInt(col.slice(i, i + 2), 16));
  let s = seed * 2654435761 >>> 0;
  const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let i = 0; i < d.length; i += 4) {
    const v = rnd();
    d[i] = R; d[i + 1] = Gc; d[i + 2] = B; d[i + 3] = v < 0.12 ? 0 : v < 0.26 ? 140 : 245;
  }
  x.putImageData(img, 0, 0);
  return c;
}
function holeTile() {
  const c = canvas(64, 64), x = c.getContext("2d"), img = x.createImageData(64, 64), d = img.data;
  let s = 99;
  const rnd = () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  for (let i = 0; i < d.length; i += 4) { d[i + 3] = rnd() < 0.16 ? 255 : rnd() < 0.2 ? 90 : 0; }
  x.putImageData(img, 0, 0);
  return c;
}

// ── time → state ─────────────────────────────────────────────────────────────────────────────────────────────────
const sg = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const lerp2 = (p, q, u) => [p[0] + (q[0] - p[0]) * u, p[1] + (q[1] - p[1]) * u];

/** where the eraser is, and how far along each of its two wipes it has got */
function eraserAt(t) {
  const w = G.sweep, s = G.scrub, last = (st) => st.pts[st.pts.length - 1];
  const along = (st, u) => { const i = Math.min(st.pts.length - 1, Math.floor(mj(u) * (st.pts.length - 1))); return st.pts[i]; };
  if (t < T.sweep[0]) return { p: G.eStart, lift: 0 };
  if (t < T.sweep[1]) return { p: along(w, sg(t, ...T.sweep)), lift: 0, rub: true };
  if (t < T.away1[1]) return { p: lerp2(last(w), G.offL, mj(sg(t, ...T.away1))), lift: sg(t, ...T.away1) };
  if (t < T.scrubIn[0]) return { p: G.offL, lift: 1 };
  if (t < T.scrubIn[1]) return { p: lerp2(G.offL, s.pts[0], mj(sg(t, ...T.scrubIn))), lift: 1 - sg(t, ...T.scrubIn) };
  if (t < T.scrub[1]) return { p: along(s, sg(t, ...T.scrub)), lift: 0, rub: true };
  if (t < T.away2[1]) return { p: lerp2(last(s), G.offL, mj(sg(t, ...T.away2))), lift: sg(t, ...T.away2) };
  if (t < T.back[0]) return { p: G.offL, lift: 1 };
  // back during the slide: it rides in with the new panel, to where it began
  return { p: lerp2([G.offL[0], G.eStart[1] + 500], G.eStart, mj(sg(t, ...T.back))), lift: 1 - sg(t, ...T.back) };
}

/** the eraser's footprints along a path, up to u (mask: opaque where it has wiped) */
function wipeMask(lib, name, st, u) {
  const m = lib.layer(name);
  if (u <= 0) return m;
  const n = Math.max(1, Math.floor(mj(u) * (st.pts.length - 1)));
  const [w, h] = G.eSize;
  m.fillStyle = "#fff"; m.filter = "blur(5px)";
  m.beginPath();
  for (let i = 0; i <= n; i += 2) { const [x, y] = st.pts[i]; m.roundRect(x - w / 2 + 6, y - h / 2 + 4, w - 12, h - 8, h / 2.4); }
  m.fill(); m.filter = "none";
  return m;
}

/** chalk dust falling from the eraser while it rubs: each mote is born on the path and falls; no state */
function dust(ctx, t, lib, tokens, st, win, seed) {
  const N = 70, life = 0.9;
  ctx.fillStyle = lib.color(tokens, "dust");
  for (let i = 0; i < N; i++) {
    const tb = win[0] + (win[1] - win[0]) * (i / N), age = t - tb;
    if (age < 0 || age > life) continue;
    const idx = Math.min(st.pts.length - 1, Math.floor(mj(i / N) * (st.pts.length - 1)));
    const [px, py] = st.pts[idx];
    const ox = (lib.hash(seed, i, 1) - 0.5) * G.eSize[0], oy = G.eSize[1] * 0.4;
    const vx = (lib.hash(seed, i, 2) - 0.5) * 40, vy = 20 + lib.hash(seed, i, 3) * 60;
    ctx.globalAlpha = 0.55 * (1 - age / life);
    const r = 1.2 + lib.hash(seed, i, 4) * 2.2;
    ctx.beginPath(); ctx.arc(px + ox + vx * age, py + oy + vy * age + 700 * age * age, r, 0, 7); ctx.fill();
  }
  ctx.globalAlpha = 1;
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const slideY = (t0) => -(H + G.rail) * lib.ease.inOutCubic(sg(t0, ...T.slide));
  const oy = slideY(t);
  const world = lib.layer("cb:world");
  drawPanel(world, t, tokens, lib, oy);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  smear(ctx, world.canvas, 0, (oy - slideY(t - 1 / 30)) * 0.5, W, H);
  // the tools over the board
  const e = eraserAt(t);
  drawEraser(ctx, e.p[0], e.p[1] + (t >= T.back[0] ? 0 : 0), e.lift, tokens, lib);
  const h = penAt(t);
  drawChalk(ctx, h.x, h.y + (t >= T.slide[0] && t < T.slide[1] ? 0 : 0), h, tokens, lib);
  // the hall's light: a little brighter in the middle of the board
  lib.vignette(ctx, { strength: tokens.texture.vignette, inner: 0.45, color: "#000" });
}

function penAt(t) {
  if (t >= T.slide[0]) {   // the chalk rides up with the board's motion a little, then is back where it began
    const u = mj(sg(t, T.slide[0], T.slide[1]));
    return { x: G.park[0] + (G.rest0[0] - G.park[0]) * u, y: G.park[1] + (G.rest0[1] - G.park[1]) * u, down: false, lift: 0.6 * Math.sin(Math.PI * u), ink: "chalk" };
  }
  const h = pen(G.penPath, t, { from: G.rest0, to: G.park }, { lead: 0.3, tail: 0.5 });
  const next = G.penPath.find((s) => s.t0 + s.dur > t) || G.penPath[G.penPath.length - 1];
  return { ...h, ink: h.st ? h.st.ink : next.ink };
}

function drawPanel(x, t, tokens, lib, oy) {
  const { W, H } = lib;
  x.save(); x.translate(0, oy);
  // this panel: the board, its ghosts (thinned where the long wipe went), the fresh dust of the wipes
  x.drawImage(G.base, 0, 0);
  const sw = sg(t, ...T.sweep);
  const gl = lib.layer("cb:ghost");
  gl.drawImage(G.ghosts, 0, 0);
  const mw = wipeMask(lib, "cb:mw", G.sweep, sw);
  gl.globalCompositeOperation = "destination-out"; gl.globalAlpha = 0.8; gl.drawImage(mw.canvas, 0, 0, W, H);
  gl.globalCompositeOperation = "source-over"; gl.globalAlpha = 1;
  x.drawImage(gl.canvas, 0, 0, W, H);
  const fresh = (mask, t0) => {
    const f = lib.layer("cb:fresh");
    f.drawImage(G.streaks, 0, 0);
    f.globalCompositeOperation = "destination-in"; f.drawImage(mask.canvas, 0, 0, W, H); f.globalCompositeOperation = "source-over";
    x.globalAlpha = 0.4 + 0.6 * Math.exp(-Math.max(0, t - t0) / 0.7);   // the haze settles but never leaves
    x.drawImage(f.canvas, 0, 0, W, H); x.globalAlpha = 1;
  };
  if (sw > 0) fresh(mw, T.sweep[1]);
  // the wrong guess: on its own layer, so the scrub takes it and nothing drawn after it
  const ss = sg(t, ...T.scrub);
  const gs = lib.layer("cb:guess");
  chalkStroke(gs, G.strokes.find((s) => s === G.guess), t, tokens, lib);
  if (ss > 0) {
    const ms = wipeMask(lib, "cb:ms", G.scrub, ss);
    const ghost = lib.layer("cb:guessghost");   // what a scrub leaves of a line: a blur of it
    ghost.filter = "blur(4px)"; ghost.globalAlpha = 0.3; ghost.drawImage(gs.canvas, 0, 0, W, H); ghost.filter = "none"; ghost.globalAlpha = 1;
    gs.globalCompositeOperation = "destination-out"; gs.drawImage(ms.canvas, 0, 0, W, H); gs.globalCompositeOperation = "source-over";
    ghost.globalCompositeOperation = "destination-in"; ghost.drawImage(ms.canvas, 0, 0, W, H); ghost.globalCompositeOperation = "source-over";
    x.drawImage(ghost.canvas, 0, 0, W, H);
    fresh(ms, T.scrub[1]);
  }
  x.drawImage(gs.canvas, 0, 0, W, H);
  // the rest of the chalk
  for (const st of G.strokes) if (st !== G.guess) chalkStroke(x, st, t, tokens, lib);
  // the words, with the board's tooth showing through them
  const tl = lib.layer("cb:text");
  for (const line of G.lines) {
    lib.setFont(tl, tokens, line.role, line.size);
    tl.fillStyle = lib.color(tokens, line.ink);
    for (const ps of line.passes) {
      const u = drawn(ps, t);
      if (u <= 0) continue;
      const gl2 = ps.glyph;
      tl.save(); tl.beginPath(); tl.rect(gl2.x - 6, line.lay.y - line.size * 1.1, (gl2.w + 12) * u, line.size * 1.5); tl.clip();
      lib.drawGlyphs(tl, { glyphs: [gl2] }, () => ({}));
      tl.restore();
    }
  }
  tl.globalCompositeOperation = "destination-out"; tl.fillStyle = tl.createPattern(G.holes, "repeat"); tl.fillRect(0, 0, W, H);
  tl.globalCompositeOperation = "source-over";
  x.drawImage(tl.canvas, 0, 0, W, H);
  // dust motes under the eraser
  dust(x, t, lib, tokens, G.sweep, T.sweep, 3);
  dust(x, t, lib, tokens, G.scrub, T.scrub, 4);
  // the frame between the two panels of the sliding board, and the next panel, ghosts and all
  if (oy < 0) {
    const rg = x.createLinearGradient(0, H, 0, H + G.rail);
    rg.addColorStop(0, "#5E6366"); rg.addColorStop(0.35, "#B9BEC1"); rg.addColorStop(0.6, "#8D9295"); rg.addColorStop(1, "#3E4245");
    x.fillStyle = rg; x.fillRect(0, H, W, G.rail);
    x.drawImage(G.base, 0, H + G.rail); x.drawImage(G.ghosts, 0, H + G.rail);
    x.fillStyle = "rgba(0,0,0,0.35)"; x.fillRect(0, H + G.rail, W, 10);
  }
  x.restore();
}

function chalkStroke(x, st, t, tokens, lib) {
  if (t < st.t0) return;
  const pat = x.createPattern(G.grain[st.ink], "repeat");
  drawStroke(x, st, t, (c, i, s, v) => {
    // chalk: the faster the hand, the more the stick skips over the board
    c.lineCap = "butt";
    c.strokeStyle = pat; c.lineWidth = tokens.stroke.width * (1.05 - 0.18 * v);
    c.globalAlpha = 1 - 0.28 * v;
    if (st.dash) c.setLineDash([10, 9]);
  }, { whole: !!st.dash });
}

/** a stick of chalk, its tip on the board; the colour of the stick is the colour being written */
function drawChalk(ctx, x, y, h, tokens, lib) {
  const col = lib.color(tokens, h.ink || "chalk");
  const lift = h.down ? 0 : Math.max(0.25, h.lift || 0.25);
  ctx.save();
  ctx.translate(x, y - 10 * lift); ctx.rotate(0.95 + Math.max(-0.1, Math.min(0.1, (h.vx || 0) * 0.003)));
  ctx.shadowColor = "rgba(0,0,0,0.45)"; ctx.shadowBlur = 10 + 18 * lift; ctx.shadowOffsetX = 8 + 24 * lift; ctx.shadowOffsetY = 10 + 22 * lift;
  const gr = ctx.createLinearGradient(0, -12, 0, 12);
  gr.addColorStop(0, lib.mixColor(col, "#ffffff", 0.4)); gr.addColorStop(0.55, col); gr.addColorStop(1, lib.mixColor(col, "#000000", 0.25));
  ctx.fillStyle = gr; ctx.beginPath(); ctx.roundRect(6, -12, 150, 24, 5); ctx.fill();
  ctx.shadowColor = "transparent";
  ctx.beginPath(); ctx.moveTo(0, -6); ctx.lineTo(10, -12); ctx.lineTo(10, 12); ctx.lineTo(0, 6); ctx.closePath(); ctx.fill();
  ctx.fillStyle = "rgba(255,255,255,0.25)"; ctx.fillRect(12, -9, 140, 4);
  ctx.restore();
}

/** a felt board eraser seen from above: a wooden back, the grey felt showing along one edge, white with dust */
function drawEraser(ctx, x, y, lift, tokens, lib) {
  const [w, h] = G.eSize;
  ctx.save();
  ctx.translate(x, y - 12 * lift); ctx.rotate(-0.06);
  ctx.shadowColor = "rgba(0,0,0,0.5)"; ctx.shadowBlur = 14 + 30 * lift; ctx.shadowOffsetX = 10 + 30 * lift; ctx.shadowOffsetY = 14 + 34 * lift;
  ctx.fillStyle = "#6C6C6A"; ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2 + 8, w, h - 4, 10); ctx.fill();   // the felt
  ctx.shadowColor = "transparent";
  ctx.fillStyle = "rgba(232,230,221,0.55)"; ctx.fillRect(-w / 2 + 4, h / 2 - 12, w - 8, 8);                 // dust on it
  const wg = ctx.createLinearGradient(0, -h / 2, 0, h / 2 - 12);
  wg.addColorStop(0, "#C08A57"); wg.addColorStop(1, "#8E5F37");
  ctx.fillStyle = wg; ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2, w, h - 14, 10); ctx.fill();               // the wooden back
  ctx.strokeStyle = "rgba(70,40,20,0.35)"; ctx.lineWidth = 2;
  for (let k = 0; k < 4; k++) {
    ctx.beginPath(); ctx.moveTo(-w / 2 + 14, -h / 2 + 14 + k * 15);
    ctx.bezierCurveTo(-w / 6, -h / 2 + 8 + k * 15, w / 6, -h / 2 + 22 + k * 15, w / 2 - 14, -h / 2 + 12 + k * 15); ctx.stroke();
  }
  ctx.restore();
}
