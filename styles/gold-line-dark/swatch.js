// Gold line on dark: one warm-gold line of light draws a whole scene on near-black, the way a light pen draws in a
// long exposure: a hot spark at its head, the trail cooling to gold behind it. The words are thin gold too.
//
//   0.0–1.5  world      a spark crosses the dark and leaves a mountain ridge behind it
//   1.5–4.5  signature  the same line runs on: the shore and its ripples, a small boat, then up into the sky where it
//                       strings five phases of the moon along one arc (time as one line)
//   4.5–7.5  type       the title is laid in gold leaf (revealed under a gleam), the English line and the caption follow
//   7.5–9.0  close      the line burns out in the order it was drawn, the words drift off as gold dust, and the spark
//                       relights where it began: the last frame is the first again
//
// One table (T) drives the strokes, the foley (FOLEY → events.json) and the reads. Strokes: styles/_swatch/vendor/hand.js.
import { prep, ellipse, drawStroke, pen, drawn, mj, timeAtS } from "../../vendor/hand.js";

export const fonts = ["Songti SC", "Didot"];

const T = {
  ridge: [0.10, 1.15], shore: [1.30, 0.62], boat: [2.02, 0.42], moons: [2.52, 1.92],   // [start, duration]
  title: [4.55, 0.75], en: [5.0, 0.45], caption: [5.1, 0.32],                           // gold-leaf reveals
  gleam: 6.3, read: 7.5,
  burn: [7.5, 8.55], dust: [7.5, 8.2], relight: [8.5, 8.85],                            // close
};
const pan = (u) => Math.round((2 * u - 1) * 70) / 100;
export const FOLEY = [
  { t: T.ridge[0], sfx: "sfx/spark_L.wav", gain_db: -6, pan_from: -0.6, pan_to: 0.6, role: "hero" },
  { t: T.shore[0], sfx: "sfx/spark_M.wav", gain_db: -9, pan_from: 0.6, pan_to: -0.4, role: "detail" },
  { t: T.boat[0], sfx: "sfx/spark_S.wav", gain_db: -9, pan: pan(0.4), role: "detail" },
  ...[0, 1, 2, 3, 4].map((k) => ({ t: +(T.moons[0] + 0.12 + k * T.moons[1] / 5).toFixed(3), sfx: "shimmer", gain_db: -12 + (k === 2 ? 2 : 0), pan: pan(0.22 + k * 0.14), pitch: [0, 2, 4, 7, 9][k], dur: 0.7 })),
  { t: T.title[0], sfx: "sfx/gleam.wav", gain_db: -8, pan: 0, role: "detail" },
  { t: T.burn[0] + 0.02, sfx: "air", gain_db: -12, dur: 1.0, dir: "down", pan_from: -0.5, pan_to: 0.5 },
];

export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: +(T.title[0] + T.title[1]).toFixed(3), end: T.read },
    { text: lib.TITLE_EN, start: +(T.en[0] + T.en[1]).toFixed(3), end: T.read },
    { text: lib.CAPTION_ZH, start: +(T.caption[0] + T.caption[1]).toFixed(3), end: T.read },
  ];
}

let G = null;

/** a Catmull-Rom curve through the points, n samples per span */
function smooth(pts, n = 10) {
  const out = [];
  for (let i = 0; i < pts.length - 1; i++) {
    const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
    for (let k = 0; k < n; k++) {
      const u = k / n, u2 = u * u, u3 = u2 * u;
      out.push([0, 1].map((d) => 0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * u + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * u2 + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * u3)));
    }
  }
  out.push(pts[pts.length - 1]);
  return out;
}

export async function setup(ctx, tokens, lib) {
  const { W, H, PORTRAIT: P, SAFE, TYPE } = lib;
  const g = {};
  const st = (pts, o = {}) => prep(pts, { step: 4, wobble: o.wobble ?? 0.8, seed: o.seed ?? 1 });
  // the ridge: a long line of peaks across the frame
  const ridgeL = [[100, 560], [250, 492], [330, 515], [470, 420], [560, 470], [640, 446], [770, 528], [900, 478], [1010, 506],
    [1140, 392], [1250, 466], [1330, 446], [1460, 522], [1580, 474], [1700, 506], [1820, 536]];
  const ridgeP = [[50, 1000], [140, 930], [210, 952], [330, 850], [420, 906], [500, 884], [600, 960], [700, 915], [800, 940],
    [880, 862], [960, 922], [1030, 990]];
  g.ridge = st(smooth(P ? ridgeP : ridgeL, 8), { seed: 2 });
  // the shore: from the ridge's foot back across the water in long lazy ripples
  const wy = P ? 1050 : 612, wx0 = P ? 1000 : 1790, wx1 = P ? 80 : 420;
  const shore = [];
  for (let i = 0; i <= 120; i++) {
    const u = i / 120, x = wx0 + (wx1 - wx0) * u;
    shore.push([x, wy + Math.sin(u * Math.PI * 9) * (10 - 7 * u) + u * 18 - (i < 8 ? (8 - i) * 9 : 0)]);
  }
  g.shore = st(shore, { seed: 3, wobble: 0.4 });
  // a small boat: hull, mast, sail, in one line
  const bx = P ? 360 : 760, by = P ? 1092 : 640, bw = P ? 74 : 84;
  g.boat = st([[bx - bw, by - 8], [bx + bw, by - 8], [bx + bw * 0.72, by + 24], [bx - bw * 0.72, by + 24], [bx - bw, by - 8], [bx, by - 8],
    [bx, by - 112], [bx + bw * 0.62, by - 22], [bx, by - 22]], { seed: 4, wobble: 0.5 });
  // five phases of the moon along one arc, strung on a thread: new crescent, half, full, half, old crescent
  const r = P ? 40 : 40;
  const mx = P ? [170, 355, 540, 725, 910] : [430, 695, 960, 1225, 1490];
  const my = (k) => (P ? 640 - 120 * Math.sin(Math.PI * k / 4) : 320 - 132 * Math.sin(Math.PI * k / 4));
  const phase = [0.62, 0.0, null, -0.0, -0.62];   // terminator ellipse rx as a share of r (sign: which side is lit)
  const moon = [], thread = [];   // the first moon starts at its own edge: the spark flies up from the boat dark
  g.moonAt = mx.map((x, k) => [x, my(k)]); g.moonR = r;
  g.moonParts = [];
  for (let k = 0; k < 5; k++) {
    const [x, y] = g.moonAt[k];
    thread.push([x - r, y]);
    const pts = [...thread];
    // round the moon from its left edge, then its terminator from top to bottom
    pts.push(...ellipse(x, y, r, r, Math.PI, Math.PI * 3, 40).slice(1));
    if (phase[k] !== null) {
      const f = phase[k], dir = k < 2 ? 1 : -1;
      pts.push(...ellipse(x, y, r * Math.abs(f), r, -Math.PI / 2, Math.PI / 2, 20).map(([px, py]) => [x + (px - x) * dir * (k === 1 || k === 3 ? 0.04 : 1), py]));
    }
    moon.push(pts.length);
    g.moonParts.push(pts);
    thread.length = 0; thread.push(pts[pts.length - 1]);
  }
  g.moons = g.moonParts.map((pts, k) => st(pts, { seed: 10 + k, wobble: 0.3 }));
  const per = T.moons[1] / 5;
  g.moons.forEach((m, k) => Object.assign(m, { t0: T.moons[0] + k * per, dur: per * 0.94, thread: true }));
  Object.assign(g.ridge, { t0: T.ridge[0], dur: T.ridge[1] });
  Object.assign(g.shore, { t0: T.shore[0], dur: T.shore[1] });
  Object.assign(g.boat, { t0: T.boat[0], dur: T.boat[1] });
  g.strokes = [g.ridge, g.shore, g.boat, ...g.moons];
  // when each burns out in the close: in the order drawn, overlapping
  g.strokes.forEach((s, i) => { s.burn = [T.burn[0] + i * 0.08, T.burn[0] + i * 0.08 + 0.5]; });
  g.start = g.ridge.pts[0];
  // stars: fixed places, each with its own slow twinkle
  const rnd = lib.rng(31);
  g.stars = Array.from({ length: 70 }, () => [rnd() * W, rnd() * H * (P ? 0.45 : 0.55), 0.6 + rnd() * 1.4, rnd() * 6.28, 0.6 + rnd() * 1.8]);
  g.glints = Array.from({ length: 14 }, (_, i) => { const p = g.shore.pts[Math.floor((0.08 + 0.06 * i) * g.shore.pts.length)]; return [p[0], p[1] + 14 + (i % 3) * 10, 18 + (i % 4) * 8, i * 1.7]; });
  // text
  const A = SAFE.title;
  lib.setFont(ctx, tokens, "zh", 10);
  const ts = lib.fitText(ctx, lib.TITLE_ZH, A.w * 0.9, (s) => lib.setFont(ctx, tokens, "zh", s), { min: 84, max: TYPE.title });
  const ty = P ? 1330 : 790;
  const mk = (role, str, size, y, win, ink) => {
    lib.setFont(ctx, tokens, role, size);
    const lay = lib.layoutText(ctx, str, { x: W / 2, y, align: "center", tracking: lib.tracking(tokens, role, size) });
    return { role, size, y, lay, win, ink, str };
  };
  g.lines = [
    mk("zh", lib.TITLE_ZH, ts, ty, T.title, "gold"),
    mk("display", lib.TITLE_EN, TYPE.label, ty + (P ? 92 : 70), T.en, "muted"),
    mk("zh", lib.CAPTION_ZH, TYPE.caption, A.y1 - TYPE.caption * 0.6, T.caption, "pale"),
  ];
  G = g;
}

const sg = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  // the dark: warm black, a faint lift in the middle, slow twinkling stars
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  const rg = ctx.createRadialGradient(W / 2, H * 0.45, 0, W / 2, H * 0.45, Math.max(W, H) * 0.7);
  rg.addColorStop(0, lib.rgba(C("lift"), 0.55)); rg.addColorStop(1, lib.rgba(C("lift"), 0));
  ctx.fillStyle = rg; ctx.fillRect(0, 0, W, H);
  for (const [x, y, rr, ph, w] of G.stars) {
    ctx.fillStyle = lib.rgba(C("gold"), 0.18 + 0.16 * Math.sin(t * w + ph));
    ctx.beginPath(); ctx.arc(x, y, rr, 0, 7); ctx.fill();
  }
  // the line: drawn on a layer, glowing additively, then the crisp core
  const L = lib.layer("gl:lines");
  for (const s of G.strokes) {
    if (t < s.t0) continue;
    const from = mj(sg(t, ...s.burn));
    if (from >= 1) continue;
    drawStroke(L, s, t, (c, i, sj) => {
      const age = t - timeAtS(s, sj);
      const hot = 1 - Math.min(1, Math.max(0, age / 0.45));
      c.strokeStyle = lib.mixColor(C("gold"), C("hot"), hot);
      c.lineWidth = (s.thread ? 2.2 : 2.8) + 1.6 * hot;
      c.globalAlpha = s.thread ? 0.85 : 1;
    }, { from });
  }
  // the lit part of each moon, washed in once its outline is closed
  G.moons.forEach((m, k) => {
    const a = sg(t, m.t0 + m.dur * 0.9, m.t0 + m.dur + 0.35) * (1 - mj(sg(t, ...m.burn)));
    if (a <= 0) return;
    const [x, y] = G.moonAt[k], r = G.moonR, f = [0.62, 0, null, 0, 0.62][k], right = k < 2;
    L.fillStyle = lib.rgba(C("gold"), 0.26 * a); L.beginPath();
    if (f === null) L.arc(x, y, r, 0, 7);
    else {
      L.arc(x, y, r, -Math.PI / 2, Math.PI / 2, !right);
      L.ellipse(x, y, Math.max(0.01, r * f), r, 0, Math.PI / 2, -Math.PI / 2, right ? true : false);
    }
    L.fill();
  });
  // the water's glints, once the shore is there
  const shoreOn = drawn(G.shore, t) * (1 - mj(sg(t, ...G.shore.burn)));
  if (shoreOn > 0.5) {
    L.lineCap = "round";
    for (const [x, y, len, ph] of G.glints) {
      L.strokeStyle = lib.rgba(C("gold"), (0.25 + 0.3 * (0.5 + 0.5 * Math.sin(t * 2.4 + ph))) * Math.min(1, (shoreOn - 0.5) * 3));
      L.lineWidth = 2; L.beginPath(); L.moveTo(x - len / 2, y); L.lineTo(x + len / 2, y); L.stroke();
    }
  }
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  ctx.filter = "blur(9px)"; ctx.globalAlpha = 0.9; ctx.drawImage(L.canvas, 0, 0, W, H);
  ctx.filter = "blur(2.5px)"; ctx.globalAlpha = 0.7; ctx.drawImage(L.canvas, 0, 0, W, H);
  ctx.restore();
  ctx.drawImage(L.canvas, 0, 0, W, H);
  // the words in gold leaf
  drawWords(ctx, t, tokens, lib);
  // the spark at the head of the line
  spark(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 12, seed: 5 });
  lib.vignette(ctx, { strength: tokens.texture.vignette, inner: 0.5, color: "#000" });
}

function spark(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  let x, y, a, size;
  if (t >= T.burn[0]) {   // out with the line, then lit again where it all began
    a = mj(sg(t, ...T.relight)); [x, y] = G.start; size = 1;
  } else {
    const h = pen(G.strokes, t, { from: G.start, to: G.strokes[G.strokes.length - 1].pts.at(-1) }, { lead: 0.1, tail: 0.3 });
    x = h.x; y = h.y;
    const last = G.strokes[G.strokes.length - 1];
    const done = t > last.t0 + last.dur;
    a = h.down ? 1 : done ? 1 - sg(t, last.t0 + last.dur, last.t0 + last.dur + 0.5) : 0.35;
    size = h.down ? 1 + 0.3 * Math.hypot(h.vx, h.vy) / 60 : 0.8;
  }
  if (a <= 0) return;
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  const r = 46 * size;
  const g = ctx.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, lib.rgba(C("hot"), 0.95 * a)); g.addColorStop(0.18, lib.rgba(C("hot"), 0.45 * a));
  g.addColorStop(0.5, lib.rgba(C("gold"), 0.12 * a)); g.addColorStop(1, lib.rgba(C("gold"), 0));
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.fill();
  ctx.strokeStyle = lib.rgba(C("hot"), 0.5 * a); ctx.lineWidth = 1.4;   // a small four-point flare
  const f = 26 * size * (0.8 + 0.2 * Math.sin(t * 40));
  ctx.beginPath(); ctx.moveTo(x - f, y); ctx.lineTo(x + f, y); ctx.moveTo(x, y - f * 0.7); ctx.lineTo(x, y + f * 0.7); ctx.stroke();
  ctx.fillStyle = lib.rgba("#FFFFFF", a); ctx.beginPath(); ctx.arc(x, y, 3.2, 0, 7); ctx.fill();
  ctx.restore();
}

function drawWords(ctx, t, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  G.lines.forEach((ln, li) => {
    const u = sg(t, ln.win[0], ln.win[0] + ln.win[1]);
    if (u <= 0) return;
    const tl = lib.layer("gl:text" + li);   // one layer per line: the masks below touch the whole layer
    lib.setFont(tl, tokens, ln.role, ln.size);
    tl.fillStyle = C(ln.ink);
    lib.drawGlyphs(tl, ln.lay, (gl, i) => {
      const n = ln.lay.glyphs.length, d0 = T.dust[0] + (i / n) * 0.35;
      const out = mj(sg(t, d0, d0 + 0.3));
      return out >= 1 ? null : { alpha: 1 - out, dy: -14 * out };
    });
    // the reveal: everything left of the leaf's edge, which moves across the line with a soft front
    const x0 = ln.lay.x0 - 40, x1 = ln.lay.x1 + 40;
    if (u < 1) {
      const edge = x0 + (x1 - x0) * lib.ease.outCubic(u) + 1;
      const m = tl.createLinearGradient(edge - 90, 0, edge, 0);
      m.addColorStop(0, "rgba(0,0,0,1)"); m.addColorStop(1, "rgba(0,0,0,0)");
      tl.save(); tl.globalCompositeOperation = "destination-in"; tl.fillStyle = m; tl.fillRect(0, 0, W, H); tl.restore();
    }
    // the gleam: a bright band crossing the glyphs as they are laid, and once more while they are read
    const lag = li === 0 ? 0 : 0.25;
    for (const w of [[ln.win[0] + ln.win[1] * 0.2, ln.win[0] + ln.win[1] + 0.35], [T.gleam + lag, T.gleam + 0.9 + lag]]) {
      const v = sg(t, ...w);
      if (v <= 0 || v >= 1) continue;
      const gx = x0 + (x1 - x0) * v;
      const band = tl.createLinearGradient(gx - 120, 0, gx + 120, 0);
      band.addColorStop(0, lib.rgba(C("hot"), 0)); band.addColorStop(0.5, lib.rgba(C("hot"), 0.85)); band.addColorStop(1, lib.rgba(C("hot"), 0));
      tl.save(); tl.globalCompositeOperation = "source-atop"; tl.fillStyle = band;
      tl.fillRect(gx - 120, ln.y - ln.size * 1.2, 240, ln.size * 1.7); tl.restore();
    }
    ctx.drawImage(tl.canvas, 0, 0, W, H);
  });
  // gold dust lifting off the words as they go
  if (t > T.dust[0] && t < T.dust[1] + 0.6) {
    ctx.save(); ctx.globalCompositeOperation = "lighter";
    G.lines.forEach((ln, li) => ln.lay.glyphs.forEach((gl, i) => {
      const n = ln.lay.glyphs.length, d0 = T.dust[0] + (i / n) * 0.35;
      for (let k = 0; k < 5; k++) {
        const age = t - d0 - k * 0.04;
        if (age < 0 || age > 0.7) continue;
        const hx = lib.hash(li, i, k, 1), hy = lib.hash(li, i, k, 2);
        const x = gl.x + hx * gl.w + (hy - 0.5) * 30 * age, y = ln.y - ln.size * 0.4 * hy - 70 * age - 40 * age * age;
        ctx.fillStyle = lib.rgba(C("gold"), 0.7 * (1 - age / 0.7));
        ctx.beginPath(); ctx.arc(x, y, 1.2 + 1.6 * lib.hash(li, i, k, 3), 0, 7); ctx.fill();
      }
    }));
    ctx.restore();
  }
}
