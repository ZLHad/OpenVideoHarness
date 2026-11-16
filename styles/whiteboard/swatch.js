// Whiteboard sketch: a dry-erase marker draws the explanation on one long white board; what is drawn stays drawn, and
// the camera moves on to clean board instead of cutting away.
//
//   0.0–1.5  world      the time axis is drawn under a still-empty board: white board, black marker, the hand's speed
//   1.5–4.5  signature  code → arrow → three frames with a ball in each, the hand fast in the middle of each stroke and slow
//                       at its ends, the colour changing only when the marker is lifted; the red circle closes the beat
//   4.5–9.0  type       the title, its English line and the caption are written out by hand, then held to be read
//   9.0–10   close      the camera slides along the board to a clean stretch: the last frame is the first again
//
// One table (T) drives the strokes, the foley (FOLEY → events.json; styles/_swatch/custom_sfx.py writes the marker
// sounds to the same durations) and the reads (texts()). Strokes come from styles/_swatch/vendor/hand.js.
import { prep, ellipse, drawStroke, pen, drawn, mj } from "../../vendor/hand.js";

export const fonts = ["Hannotate SC", "Noteworthy"];

// stroke durations come in four sizes so each has a marker sound of its own length (custom_sfx.py: whiteboard)
const XS = 0.07, S = 0.14, M = 0.34, L = 0.62;
const T = {
  axis: 0.10, head: 0.78, tV: 0.98, tH: 1.16, ticks: [1.28, 1.36, 1.44],                    // world
  box: 1.52, braceL: 1.90, braceR: 2.07, code: [2.25, 2.33, 2.41],                          // signature: the code card
  frames: [2.46, 2.84, 3.22], arrow: 3.60, arrowHead: 3.77, balls: [3.89, 4.07, 4.23],      //            frames, arrow, balls
  circle: 4.42,                                                                              // the red circle (into the type beat)
  title: [4.82, 0.11], en: [5.85, 0.30], caption: [6.20, 0.06],                              // type: start, s per glyph (en: whole line)
  read: 9.0,                                                                                 // the reads leave with the board
  pan: [9.0, 9.97],                                                                          // close
};
const DUR_OF = { axis: L, head: S, tV: S, tH: XS, box: M, braceL: S, braceR: S, frames: M, arrow: S, arrowHead: XS, balls: S, circle: M };
const pan = (u) => Math.round((2 * u - 1) * 70) / 100;

export const FOLEY = [
  { t: T.axis, sfx: "sfx/marker_L.wav", gain_db: -8, pan: pan(0.6), role: "detail" },
  { t: T.head, sfx: "sfx/marker_S_a.wav", gain_db: -9, pan: pan(0.83), role: "detail" },
  { t: T.tV, sfx: "sfx/marker_S_b.wav", gain_db: -10, pan: pan(0.85), role: "detail" },
  { t: T.ticks[0], sfx: "sfx/marker_taps.wav", gain_db: -10, pan: pan(0.6), role: "detail" },
  { t: T.box, sfx: "sfx/marker_M_a.wav", gain_db: -8, pan: pan(0.23), role: "detail" },
  { t: T.braceL, sfx: "sfx/marker_S_a.wav", gain_db: -10, pan: pan(0.19), role: "detail" },
  { t: T.braceR, sfx: "sfx/marker_S_b.wav", gain_db: -8, pan: pan(0.28), role: "detail" },
  { t: T.code[0], sfx: "sfx/marker_taps.wav", gain_db: -11, pan: pan(0.24), role: "detail" },
  ...T.frames.map((t, k) => ({ t, sfx: k === 1 ? "sfx/marker_M_b.wav" : "sfx/marker_M_a.wav", gain_db: -7, pan: pan(0.47 + 0.135 * k), role: "detail" })),
  { t: T.arrow, sfx: "sfx/marker_S_b.wav", gain_db: -9, pan: pan(0.36), role: "detail" },
  ...T.balls.map((t, k) => ({ t, sfx: k === 1 ? "sfx/marker_S_b.wav" : "sfx/marker_S_a.wav", gain_db: k === 1 ? -6 : -9, pan: pan(0.47 + 0.135 * k), role: "detail" })),
  { t: T.circle, sfx: "sfx/marker_M_b.wav", gain_db: -6, pan: pan(0.6), role: "hero" },
  { t: T.title[0], sfx: "sfx/marker_write_title.wav", gain_db: -8, pan: 0, role: "detail" },
  { t: T.caption[0], sfx: "sfx/marker_write_caption.wav", gain_db: -10, pan: 0, role: "detail" },
  { t: T.pan[0] + 0.05, sfx: "air", gain_db: -10, dur: 0.9, pan_from: 0.4, pan_to: -0.4 },     // the board slides by
];

export function texts(lib) {
  const done = (start, n, per) => +(start + n * per).toFixed(3);
  return [
    { text: lib.TITLE_ZH, start: done(T.title[0], [...lib.TITLE_ZH].length, T.title[1]), end: T.read },
    { text: lib.TITLE_EN, start: +(T.en[0] + T.en[1]).toFixed(3), end: T.read },
    { text: lib.CAPTION_ZH, start: done(T.caption[0], [...lib.CAPTION_ZH].length, T.caption[1]), end: T.read },
  ];
}

let G = null;   // geometry and textures, made once in setup (pure data)

export async function setup(ctx, tokens, lib) {
  const { W, H, PORTRAIT, SAFE, TYPE } = lib;
  const P = PORTRAIT;
  const shift = P ? 1200 : 1800;                               // how far the close slides: past everything drawn
  const st = (pts, o = {}) => prep(pts, { step: 4, wobble: o.wobble ?? 1.6, seed: o.seed ?? 1, close: o.close });
  const rect = (x0, y0, x1, y1, seed) => {
    // a hand-drawn box: one stroke from the top-left, round the corners, finishing a little past where it began
    const o = 6;
    return st([[x0 + o, y0], [x1, y0 + 2], [x1 - 2, y1], [x0, y1 - 2], [x0 + 3, y0 - 4], [x0 + 26, y0 - 3]], { seed, wobble: 2 });
  };
  const g = {};
  // the time axis, its head, the letter t, three ticks
  const ax = P ? { x0: 125, x1: 930, y: 1010 } : { x0: 790, x1: 1600, y: 470 };
  const fc = P ? [250, 540, 830] : [900, 1160, 1420], fy = P ? 830 : 300, fw = P ? 250 : 220, fh = P ? 190 : 180;
  g.axis = st([[ax.x0, ax.y], [ax.x1, ax.y - 3]], { seed: 2, wobble: 2.2 });
  g.head = st([[ax.x1 - 26, ax.y - 19], [ax.x1 + 2, ax.y - 3], [ax.x1 - 25, ax.y + 15]], { seed: 3 });
  const tx = ax.x1 + 40;
  g.tV = st([[tx, ax.y - 32], [tx, ax.y + 14], [tx + 3, ax.y + 20], [tx + 15, ax.y + 18]], { seed: 4, wobble: 0.6 });
  g.tH = st([[tx - 13, ax.y - 14], [tx + 14, ax.y - 16]], { seed: 5, wobble: 0.4 });
  g.ticks = fc.map((x, k) => st([[x, ax.y - 14], [x + 1, ax.y + 12]], { seed: 6 + k, wobble: 0.5 }));
  // the code card: a box, two braces, three lines of "code"
  const cc = P ? { x: 540, y: 440, w: 370, h: 230 } : { x: 450, y: 300, w: 300, h: 200 };
  g.box = rect(cc.x - cc.w / 2, cc.y - cc.h / 2, cc.x + cc.w / 2, cc.y + cc.h / 2, 9);
  const bx = cc.w * 0.36, bh = cc.h * 0.34;
  const brace = (x, d, seed) => st([[x + 12 * d, cc.y - bh], [x + 2 * d, cc.y - bh + 10], [x + 3 * d, cc.y - 14], [x - 9 * d, cc.y],
    [x + 3 * d, cc.y + 14], [x + 2 * d, cc.y + bh - 10], [x + 12 * d, cc.y + bh]], { seed, wobble: 0.8 });
  g.braceL = brace(cc.x - bx, 1, 10); g.braceR = brace(cc.x + bx, -1, 11);
  const lx = cc.x - bx + 36;
  g.code = [[0.62, -40], [0.42, 0], [0.54, 40]].map(([w, dy], k) =>
    st([[lx + (k === 1 ? 26 : 0), cc.y + dy], [lx + (k === 1 ? 26 : 0) + cc.w * w * 0.75, cc.y + dy + 1]], { seed: 12 + k, wobble: 0.6 }));
  // the arrow from the code to the frames
  const a0 = P ? [cc.x, cc.y + cc.h / 2 + 28] : [cc.x + cc.w / 2 + 28, cc.y];
  const a1 = P ? [cc.x, fy - fh / 2 - 26] : [fc[0] - fw / 2 - 26, cc.y];
  g.arrow = st([a0, a1], { seed: 15, wobble: 1.2 });
  const hd = P ? [[a1[0] - 17, a1[1] - 24], a1, [a1[0] + 17, a1[1] - 23]] : [[a1[0] - 24, a1[1] - 17], a1, [a1[0] - 23, a1[1] + 17]];
  g.arrowHead = st(hd, { seed: 16, wobble: 0.4 });
  // three frames, a ball in each: low, high, low, so the three read as one bounce
  g.frames = fc.map((x, k) => rect(x - fw / 2, fy - fh / 2, x + fw / 2, fy + fh / 2, 20 + k));
  const off = P ? 62 : 56, r = P ? 26 : 24;
  g.ballAt = fc.map((x, k) => [x + (k - 1) * off, fy + (k === 1 ? -0.24 : 0.25) * fh]);
  g.balls = g.ballAt.map(([x, y], k) => {
    // an outline, then a spiral that fills it in: how a marker fills a dot
    const pts = ellipse(x, y, r, r, -2.2, -2.2 + Math.PI * 2 + 0.3, 40);
    for (let i = 0; i <= 90; i++) { const a = -2.2 + 0.3 + i * 0.28, rr = r * (1 - i / 90) * 0.92; pts.push([x + Math.cos(a) * rr, y + Math.sin(a) * rr]); }
    return st(pts, { seed: 30 + k, wobble: 0.5 });
  });
  g.circle = st(ellipse(fc[1], fy + 4, fw / 2 + (P ? 46 : 52), fh / 2 + (P ? 44 : 46), -2.5, -2.5 + Math.PI * 2 + 0.55, 90, -0.07), { seed: 40, wobble: 3 });
  // the strokes in drawing order, with their times and inks
  const ink = tokens.palette;
  const seq = [
    [g.axis, T.axis, DUR_OF.axis, "ink"], [g.head, T.head, S, "ink"], [g.tV, T.tV, S, "ink"], [g.tH, T.tH, XS, "ink"],
    ...g.ticks.map((s, k) => [s, T.ticks[k], XS, "ink"]),
    [g.box, T.box, M, "ink"], [g.braceL, T.braceL, S, "ink"], [g.braceR, T.braceR, S, "ink"],
    ...g.code.map((s, k) => [s, T.code[k], XS, "ink"]),
    ...g.frames.map((s, k) => [s, T.frames[k], M, "ink"]),
    [g.arrow, T.arrow, S, "blue"], [g.arrowHead, T.arrowHead, XS, "blue"],
    ...g.balls.map((s, k) => [s, T.balls[k], S, "blue"]),
    [g.circle, T.circle, M, "red"],
  ];
  g.strokes = seq.map(([s, t0, dur, c]) => Object.assign(s, { t0, dur, ink: c }));
  // the text: sizes, places, and one pen pass per glyph (no ink: the glyph is revealed under it, left to right)
  const A = SAFE.title;
  lib.setFont(ctx, tokens, "zh", 10);
  const ts = lib.fitText(ctx, lib.TITLE_ZH, A.w * 0.92, (s) => lib.setFont(ctx, tokens, "zh", s), { min: 84, max: TYPE.title });
  const ty = P ? 1290 : 690, ey = ty + (P ? 92 : 78), cy = A.y1 - TYPE.caption * 0.6;
  const lineOf = (role, str, size, y, t0, per, whole) => {
    lib.setFont(ctx, tokens, role, size);
    const lay = lib.layoutText(ctx, str, { x: W / 2, y, align: "center", tracking: lib.tracking(tokens, role, size) });
    const n = lay.glyphs.length, step = whole ? per / n : per;
    const glyphs = lay.glyphs.map((gl, i) => {
      const x0 = gl.x - 2, x1 = gl.x + gl.w + 2, top = y - size * 0.82, h = size;
      const pts = [];   // a zigzag over the glyph: the pen's path while it is written
      for (let k = 0; k <= 6; k++) pts.push([x0 + (x1 - x0) * k / 6, top + h * (k % 2 ? 0.25 : 0.7) + (k % 3) * 4]);
      return Object.assign(prep(pts, { step: 6 }), { t0: t0 + i * step, dur: step * 0.86, glyph: gl, write: true });
    });
    return { role, size, y, str, lay, glyphs };
  };
  g.lines = [
    lineOf("zh", lib.TITLE_ZH, ts, ty, T.title[0], T.title[1], false),
    lineOf("display", lib.TITLE_EN, TYPE.label, ey, T.en[0], T.en[1], true),
    lineOf("zh", lib.CAPTION_ZH, TYPE.caption, cy, T.caption[0], T.caption[1], false),
  ];
  g.lines[1].ink = "blue"; g.lines[0].ink = g.lines[2].ink = "ink";
  g.penPath = [...g.strokes, ...g.lines.flatMap((l) => l.glyphs.map((s) => Object.assign(s, { ink: l.ink })))].sort((a, b) => a.t0 - b.t0);
  g.rest0 = P ? [175, 1095] : [835, 560];                        // where the marker waits at the start (and, after the slide, the end)
  g.park = P ? [860, 1440] : [1590, 600];                       // where it waits while the words are read: clear of them
  g.shift = shift;
  g.board = boardTexture(tokens, lib, shift);
  G = g;
}

/** The board's own marks: ghosts of earlier, half-erased drawings and the eraser's swirls, tiling every `shift` px so the
 * slide in the close lands on the same board it started on. */
function boardTexture(tokens, lib, shift) {
  const { H } = lib;
  const c = document.createElement("canvas"); c.width = shift; c.height = H;
  const x = c.getContext("2d");
  const rnd = lib.rng(71);
  const ghost = lib.color(tokens, "ghost");
  const at = (fn) => { for (const o of [-shift, 0, shift]) { x.save(); x.translate(o, 0); fn(); x.restore(); } };
  // eraser swirls: wide soft arcs
  x.filter = "blur(10px)";
  for (let i = 0; i < 9; i++) {
    const cx = rnd() * shift, cy = H * (0.1 + rnd() * 0.8), rr = 120 + rnd() * 220, a = rnd() * 6;
    const lw = 40 + rnd() * 70, al = 0.035 + rnd() * 0.04;
    at(() => { x.strokeStyle = lib.rgba(ghost, al); x.lineWidth = lw; x.beginPath(); x.ellipse(cx, cy, rr, rr * 0.45, a, 0, 2.6); x.stroke(); });
  }
  x.filter = "blur(1.2px)";
  // half-erased marker lines: thin, broken, very faint
  for (let i = 0; i < 22; i++) {
    const cx = rnd() * shift, cy = H * (0.08 + rnd() * 0.84), len = 60 + rnd() * 260, a = (rnd() - 0.5) * 0.6;
    const col = [lib.color(tokens, "ink"), lib.color(tokens, "blue"), lib.color(tokens, "red")][Math.floor(rnd() * 3)];
    const al = 0.035 + rnd() * 0.04, bend = (rnd() - 0.5) * 60;
    at(() => {
      x.strokeStyle = lib.rgba(col, al); x.lineWidth = 5; x.lineCap = "round"; x.setLineDash([20 + rnd() * 50, 8 + rnd() * 30]);
      x.beginPath(); x.moveTo(cx, cy); x.quadraticCurveTo(cx + len / 2, cy + bend, cx + len * Math.cos(a), cy + len * Math.sin(a)); x.stroke();
    });
  }
  x.setLineDash([]); x.filter = "none";
  return c;
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const camX = (t0) => G.shift * lib.ease.inOutCubic(lib.seg(t0, T.pan[0], T.pan[1]));
  const zoom = 1 + 0.02 * Math.sin(Math.PI * lib.clamp(t / T.pan[0]));   // a slow breath in and out while the board fills
  // the world (board, ink, words) into a layer, then slid by the camera, with a smear while it moves fast
  const world = lib.layer("wb:world");
  drawWorld(world, t, tokens, lib, camX(t), zoom);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  const v = camX(t) - camX(t - 1 / 30);
  const n = Math.min(32, Math.ceil(Math.abs(v) * 0.5 / 3));   // a copy every 3 px: thin marker lines stay a smear, not a stack
  if (n < 2) ctx.drawImage(world.canvas, 0, 0, W, H);
  else for (let i = 0; i < n; i++) {       // a running average of n copies across half a frame of travel
    ctx.globalAlpha = 1 / (i + 1);
    ctx.drawImage(world.canvas, (i / (n - 1) - 0.5) * v * 0.5, 0, W, H);
  }
  ctx.globalAlpha = 1;
  // the marker, over everything
  const h = penAt(t);
  const sx = (h.x - camX(t) - W / 2) * zoom + W / 2, sy = (h.y - H * 0.45) * zoom + H * 0.45;
  drawMarker(ctx, sx, sy, h, tokens, lib);
  // the room's light on the board: a soft sheen top left, the bottom a touch darker
  const g = ctx.createRadialGradient(W * 0.28, H * 0.12, 0, W * 0.28, H * 0.12, Math.max(W, H) * 0.75);
  g.addColorStop(0, "rgba(255,255,255,0.35)"); g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  lib.vignette(ctx, { strength: tokens.texture.vignette, inner: 0.55, color: P("shade") });
}

/** where the marker is: on the strokes and the writing, waiting at the park while the words are read, then sliding with
 * the board to where it began */
function penAt(t) {
  if (t >= T.pan[0]) {
    const u = mj(lib_seg(t, T.pan[0], T.pan[1]));
    const to = [G.rest0[0] + G.shift, G.rest0[1]];
    return { x: G.park[0] + (to[0] - G.park[0]) * u, y: G.park[1] + (to[1] - G.park[1]) * u, down: false, lift: 0.5 * Math.sin(Math.PI * u), st: null, vx: 0, vy: 0, ink: "ink" };
  }
  const h = pen(G.penPath, t, { from: G.rest0, to: G.park }, { lead: 0.1, tail: 0.55 });
  // which marker is in the hand: the ink of the stroke being drawn, or of the next one while it flies there
  const next = G.penPath.find((s) => s.t0 + s.dur > t) || G.penPath[G.penPath.length - 1];
  return { ...h, ink: h.st ? h.st.ink : (t < G.penPath[0].t0 ? "ink" : next.ink) };
}
const lib_seg = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));

function drawWorld(x, t, tokens, lib, camX, zoom) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  x.fillStyle = P("bg"); x.fillRect(0, 0, W, H);
  x.save();
  x.translate(W / 2, H * 0.45); x.scale(zoom, zoom); x.translate(-W / 2, -H * 0.45);
  x.translate(-camX, 0);
  // the board's ghosts, tiled
  const s = G.shift, k0 = Math.floor((camX - W) / s);
  for (let k = k0; k <= k0 + 4; k++) x.drawImage(G.board, k * s, 0);
  // the ink
  for (const st of G.strokes) {
    if (t < st.t0) continue;
    const col = P(st.ink);
    const blot = drawStroke(x, st, t, (c, i, sj, v) => {
      // a dry-erase marker: a little thinner and drier where the hand moves fast
      c.lineWidth = tokens.stroke.width * (1.08 - 0.22 * v);
      c.strokeStyle = lib.mixColor(col, P("bg"), 0.1 * v);
    });
    if (blot > 0) {   // where the nib first touched: a small dark bead
      x.fillStyle = col; x.beginPath(); x.arc(st.pts[0][0], st.pts[0][1], tokens.stroke.width * 0.62, 0, 7); x.fill();
    }
  }
  // the words, revealed left to right under the pen
  for (const line of G.lines) {
    lib.setFont(x, tokens, line.role, line.size);
    x.fillStyle = P(line.ink);
    line.glyphs.forEach((gs) => {
      const u = drawn(gs, t);
      if (u <= 0) return;
      const gl = gs.glyph;
      x.save();
      x.beginPath(); x.rect(gl.x - 6, line.y - line.size * 1.1, (gl.w + 12) * u, line.size * 1.5); x.clip();
      lib.drawGlyphs(x, { glyphs: [gl] }, () => ({}));
      x.restore();
    });
  }
  x.restore();
}

/** A dry-erase marker seen from above: nib at the pen point, barrel leaning down to the right (a right hand). The cap
 * colour says which ink is in the hand; lifted, it rises and its shadow falls further away. */
function drawMarker(ctx, x, y, h, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const ink = P(h.ink || "ink");
  const lift = h.down ? 0 : Math.max(0.25, h.lift || 0.25);
  const lean = Math.max(-0.12, Math.min(0.12, (h.vx || 0) * 0.004));
  const a = 0.74 + lean, sc = 1 + 0.05 * lift;
  ctx.save();
  ctx.translate(x, y - 14 * lift); ctx.rotate(a); ctx.scale(sc, sc);
  ctx.shadowColor = "rgba(30,32,40,0.28)"; ctx.shadowBlur = 14 + 22 * lift;
  ctx.shadowOffsetX = 10 + 34 * lift; ctx.shadowOffsetY = 12 + 30 * lift;
  // barrel
  const bg = ctx.createLinearGradient(0, -23, 0, 23);
  bg.addColorStop(0, "#FFFFFF"); bg.addColorStop(0.5, "#ECECE8"); bg.addColorStop(1, "#C9CBCE");
  ctx.fillStyle = bg; ctx.beginPath(); ctx.roundRect(46, -23, 270, 46, 10); ctx.fill();
  ctx.shadowColor = "transparent";
  ctx.strokeStyle = "rgba(60,64,72,0.35)"; ctx.lineWidth = 2; ctx.stroke();
  // collar and nib
  ctx.fillStyle = "#D9DADC"; ctx.beginPath(); ctx.roundRect(24, -15, 26, 30, 4); ctx.fill();
  ctx.fillStyle = ink; ctx.beginPath(); ctx.moveTo(-1, -5); ctx.lineTo(26, -10); ctx.lineTo(26, 10); ctx.lineTo(-1, 5); ctx.closePath(); ctx.fill();
  // the ink band and the end cap
  ctx.fillStyle = ink; ctx.fillRect(150, -23, 64, 46);
  ctx.beginPath(); ctx.roundRect(300, -25, 44, 50, 12); ctx.fill();
  ctx.fillStyle = "rgba(255,255,255,0.22)"; ctx.fillRect(48, -19, 266, 6);
  ctx.restore();
}
