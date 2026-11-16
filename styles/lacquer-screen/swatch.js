// 漆金螺钿屏风 · lacquer-screen — swatch spec 2 (8 s, four beats, landscape).
//
// A six-panel folding screen of black lacquer stands in a dark room. It unfolds; its panels zigzag in perspective, the
// lit ones warm, the turned-away ones deep, a soft window reflection sliding across each as the angle changes. A brush
// with a wet gold tip writes one line across the panels (a rise, a dip, a surge), and where the line turns, pieces of
// mother-of-pearl are set in and catch the light. The title is gold over the screen, with one small vermilion seal; in
// the close the gold sinks back into the lacquer and the screen folds shut, as it stood in the first frame.
//
//   0.0–1.5  world      the screen unfolds from almost shut (the first big move at 0.1 s); the brush comes in
//   1.5–4.5  signature  the brush writes the gold line across the folds; five mother-of-pearl nodes set in as it passes
//   4.5–7.0  type       the screen opens flatter; title in gold, the seal, the caption; read once
//   7.0–8.0  close      gold and title sink into the lacquer; the screen folds back to the first frame
//
// Everything is drawn here: the screen's face is a flat "art" canvas (lacquer, gold dust, the plum branch, the line),
// mapped every frame onto six panels in perspective by vertical strips. One timing table (T) drives picture, foley, reads.

const T = {
  open: [0.0, 1.35], brushIn: [1.0, 1.5], write: [1.5, 4.2], brushOut: [4.2, 4.6],
  flatten: [4.3, 5.1], title: 4.45, caption: 4.7, seal: 5.25, glint: [5.7, 6.5], read: [4.95, 7.0],
  sink: [7.0, 7.45], fold: [7.12, 7.97],
};
const THETA = { shut: 80, open: 34, flat: 20 };          // each panel's turn out of the screen's plane, degrees
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;

// ── the line the brush writes: a rise, a dip, a surge, a pull-back, the last surge (face px; pure, so FOLEY can use it)
const PA = 300, N = 6, AW = PA * N, AH = 840;            // the face: six panels of PA × AH px
const VALUES = [0.06, 0.13, 0.27, 0.37, 0.30, 0.47, 0.63, 0.52, 0.44, 0.71, 0.96];
const TURNS = [3, 4, 6, 8, 10];                           // the points where a mother-of-pearl node is set
const LINE = (() => {
  const raw = VALUES.map((y, i) => [140 + (i / (VALUES.length - 1)) * 1520, 712 - y * 390]);
  const pts = [];
  for (let i = 0; i < raw.length - 1; i++) {                 // Catmull–Rom through the points
    const p0 = raw[Math.max(0, i - 1)], p1 = raw[i], p2 = raw[i + 1], p3 = raw[Math.min(raw.length - 1, i + 2)];
    for (let s = 0; s < 16; s++) {
      const u = s / 16, u2 = u * u, u3 = u2 * u;
      const f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u2 + (-a + 3 * b - 3 * c + d) * u3);
      pts.push([f(p0[0], p1[0], p2[0], p3[0]), f(p0[1], p1[1], p2[1], p3[1])]);
    }
  }
  pts.push(raw[raw.length - 1]);
  const acc = [0];
  for (let i = 1; i < pts.length; i++) acc.push(acc[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  const len = acc[acc.length - 1];
  return { pts, acc, len, turns: TURNS.map((k) => acc[Math.min(pts.length - 1, k * 16)] / len) };
})();
/** When the brush, moving along the line on an in-out sine, reaches the fraction u of its length. */
const reach = (u) => T.write[0] + (Math.acos(1 - 2 * u) / Math.PI) * (T.write[1] - T.write[0]);

export const FOLEY = [
  { t: 0.55, sfx: "air", gain_db: -10, dur: 1.2, dir: "down", tone: 0.35, pan: 0 },               // the panels swing open
  { t: T.open[1] - 0.05, sfx: "click", gain_db: -14, pitch: -7, pan: -0.1 },                       // the hinges come to rest
  { t: T.write[0] + 0.02, sfx: "paper", gain_db: -18, dur: 2.6, bright: 0.2, tone: 0.15, pan_from: -0.6, pan_to: 0.6 },   // the brush drags
  ...LINE.turns.map((u, k) => ({ t: Math.round(reach(u) * 1000) / 1000, sfx: "tick", gain_db: -6, role: "hero", pitch: 9 + (k % 3) * 2, pan: pan(250 + u * 1420) })),
  // the gold title has no sound of its own: the qin's harmonic on the bar line (4.5 s) carries it
  { t: T.seal, sfx: "impact", gain_db: -20, pitch: 12, pan: 0.15 },                                 // the seal
  { t: T.fold[0] + 0.45, sfx: "air", gain_db: -11, dur: 0.8, dir: "down", tone: 0.3, pan: 0 },     // folding shut
];

export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: T.read[0], end: T.read[1] },
    { text: lib.TITLE_EN, start: T.read[0], end: T.read[1] },
    { text: lib.CAPTION_ZH, start: T.read[0], end: T.read[1] },
  ];
}

// ── the screen's face (setup) ───────────────────────────────────────────────────────────────────────────────────
const PG = 320, F = 1750;                                  // a panel's width on screen when flat, focal length (px)
let L = null;

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  L = {};
  L.base = faceBase(lib, P);
  L.blossoms = blossoms(lib);
  L.art = document.createElement("canvas"); L.art.width = AW; L.art.height = AH;
  L.gold = (x) => { const g = x.createLinearGradient(0, 0, AW * 0.6, AH); g.addColorStop(0, P("gold_hi")); g.addColorStop(0.45, P("gold")); g.addColorStop(1, P("gold_lo")); return g; };
  lib.setFont(ctx, tokens, "zh", lib.TYPE.title);
  L.titleW = ctx.measureText(lib.TITLE_ZH).width;
}

/** Black lacquer with its frame, panel borders, a cloud of gold dust and the plum branch (static parts only). */
function faceBase(lib, P) {
  const { rgb, clamp, fbm2, hash, rng, rgba } = lib;
  const c = document.createElement("canvas"); c.width = AW; c.height = AH;
  const x = c.getContext("2d");
  // lacquer: near black, warm, with a very soft depth (lacquer is smooth: no grain)
  const img = x.createImageData(AW, AH), a = rgb(P("lacquer")), b = rgb(P("lacquer2"));
  for (let j = 0; j < AH; j++) for (let i = 0; i < AW; i++) {
    const m = clamp(0.5 + 0.5 * fbm2(i / 520, j / 380, { octaves: 3, seed: 3 }) + (hash(i, j, 5) - 0.5) * 0.04), k = (j * AW + i) * 4;
    for (let n = 0; n < 3; n++) img.data[k + n] = a[n] + (b[n] - a[n]) * m;
    img.data[k + 3] = 255;
  }
  x.putImageData(img, 0, 0);
  // gold dust (nashiji): two drifting clouds of fine flecks, densest at their hearts
  const r = rng(41);
  const cloud = (cx, cy, rx, ry, n) => {
    for (let q = 0; q < n; q++) {
      const ang = r() * Math.PI * 2, rad = Math.pow(r(), 0.7);
      const px = cx + Math.cos(ang) * rx * rad + (r() - 0.5) * 40, py = cy + Math.sin(ang) * ry * rad;
      x.fillStyle = rgba(r() < 0.25 ? P("gold_hi") : P("gold"), (0.25 + r() * 0.6) * (1 - rad * 0.7));
      const s = 0.7 + r() * 1.6; x.fillRect(px, py, s, s);
    }
  };
  cloud(330, 735, 330, 60, 5200); cloud(1520, 760, 300, 55, 4200); cloud(1450, 120, 380, 70, 3800);
  // a band of waves (seigaiha) in fine gold along the foot of the screen
  x.save(); x.strokeStyle = rgba(P("gold"), 0.32); x.lineWidth = 1.3;
  for (let row = 0; row < 3; row++) for (let i = -1; i < AW / 56 + 1; i++) {
    const cx = i * 56 + (row % 2) * 28, cy = AH - 40 - row * 14;
    for (let rr = 26; rr > 6; rr -= 7) { x.beginPath(); x.arc(cx, cy, rr, Math.PI, 0); x.stroke(); }
  }
  x.restore();
  // the plum branch in gold maki-e, top right: a few brushy strokes
  x.save(); x.lineCap = "round"; x.lineJoin = "round";
  const br = [[[1790, 40], [1660, 105], [1560, 150], [1430, 230], [1340, 262]], [[1560, 150], [1530, 95], [1475, 60]],
    [[1660, 105], [1690, 175], [1655, 250]], [[1430, 230], [1395, 300], [1410, 345]]];
  br.forEach((pts, k) => {
    for (let pass = 0; pass < 2; pass++) {
      x.strokeStyle = pass ? rgba(P("gold_hi"), 0.55) : P("gold_lo"); x.lineWidth = (k ? 5 : 9) - pass * 3;
      x.beginPath(); pts.forEach(([px, py], i) => (i ? x.lineTo(px + (pass ? -1 : 0), py + (pass ? -1 : 0)) : x.moveTo(px, py))); x.stroke();
    }
  });
  x.restore();
  // panel borders and the frame: a lacquer rim with a fine gold line inside
  x.save();
  for (let k = 0; k <= N; k++) {
    const px = k * PA;
    x.fillStyle = "rgba(0,0,0,0.55)"; x.fillRect(px - 9, 0, 18, AH);
    x.strokeStyle = rgba(P("gold"), 0.55); x.lineWidth = 1.4;
    if (k > 0) { x.beginPath(); x.moveTo(px - 12, 22); x.lineTo(px - 12, AH - 22); x.stroke(); }
    if (k < N) { x.beginPath(); x.moveTo(px + 12, 22); x.lineTo(px + 12, AH - 22); x.stroke(); }
  }
  x.fillStyle = "rgba(0,0,0,0.55)"; x.fillRect(0, 0, AW, 18); x.fillRect(0, AH - 18, AW, 18);
  x.strokeStyle = rgba(P("gold"), 0.55); x.lineWidth = 1.4;
  x.beginPath(); x.moveTo(0, 22); x.lineTo(AW, 22); x.moveTo(0, AH - 22); x.lineTo(AW, AH - 22); x.stroke();
  // hinge fittings: small gold plates at each fold
  for (let k = 1; k < N; k++) for (const hy of [110, AH - 110]) {
    const g = x.createLinearGradient(k * PA - 10, hy - 22, k * PA + 10, hy + 22);
    g.addColorStop(0, P("gold_lo")); g.addColorStop(0.5, P("gold_hi")); g.addColorStop(1, P("gold_lo"));
    x.fillStyle = g; x.fillRect(k * PA - 8, hy - 22, 16, 44);
  }
  x.restore();
  return c;
}

function lineAt(u) {
  const { pts, acc, len } = LINE, s = Math.max(0, Math.min(1, u)) * len;
  let i = 1; while (i < pts.length - 1 && acc[i] < s) i++;
  const f = (s - acc[i - 1]) / Math.max(1e-6, acc[i] - acc[i - 1]);
  return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f, i];
}

/** Mother-of-pearl plum blossoms on the branch: each petal a shell piece (placed once). */
function blossoms(lib) {
  const at = [[1745, 62], [1610, 128], [1505, 182], [1385, 250], [1520, 98], [1480, 60], [1688, 182], [1650, 250], [1400, 320], [1340, 262]];
  return at.map(([x, y], k) => ({ x, y, r: 13 + lib.hash(k, 3) * 7, rot: lib.hash(k, 4) * Math.PI }));
}

// ── shimmer ─────────────────────────────────────────────────────────────────────────────────────────────────────────
/** Mother-of-pearl colour at a face point: the hue walks with position, the panels' angle and a slow 8 s cycle. */
function nacre(lib, x, y, k, theta, t) {
  const ph = 0.0042 * x + 0.006 * y + k * 1.7 + theta * 0.06 + Math.sin((2 * Math.PI * t) / 8) * 0.9;
  const hue = 190 + 95 * Math.sin(ph), light = 74 + 10 * Math.sin(ph * 1.7 + 1), sat = 38 + 18 * Math.cos(ph * 0.8);
  return `hsl(${hue.toFixed(1)} ${sat.toFixed(1)}% ${light.toFixed(1)}%)`;
}
function shell(x, cx, cy, r, rot, fill, lib) {          // one irregular shell piece
  x.save(); x.translate(cx, cy); x.rotate(rot); x.fillStyle = fill;
  x.beginPath(); x.moveTo(0, -r); x.quadraticCurveTo(r * 0.75, -r * 0.4, r * 0.55, r * 0.35); x.lineTo(0, r * 0.7);
  x.quadraticCurveTo(-r * 0.7, r * 0.3, -r * 0.5, -r * 0.45); x.closePath(); x.fill();
  x.strokeStyle = "rgba(255,255,255,0.35)"; x.lineWidth = 0.8; x.beginPath(); x.moveTo(-r * 0.2, -r * 0.5); x.lineTo(r * 0.25, r * 0.3); x.stroke();
  x.restore();
}

// ── frame ───────────────────────────────────────────────────────────────────────────────────────────────────────────
function thetaAt(t, lib) {
  const { seg, lerp, ease } = lib;
  if (t < T.flatten[0]) return lerp(THETA.shut, THETA.open, ease.outCubic(seg(t, ...T.open)));
  if (t < T.fold[0]) return lerp(THETA.open, THETA.flat, ease.inOutSine(seg(t, ...T.flatten)));
  return lerp(THETA.flat, THETA.shut, ease.inOutCubic(seg(t, ...T.fold)));
}

/** The panels in perspective for a fold angle: hinge points (x, z), and a mapper from face px to screen px. */
function geometry(theta, lib) {
  const { W, H } = lib, th = (theta * Math.PI) / 180;
  const hinge = [[0, 0]];
  for (let i = 0; i < N; i++) { const s = i % 2 ? -1 : 1; hinge.push([hinge[i][0] + PG * Math.cos(th), hinge[i][1] + s * PG * Math.sin(th)]); }
  const mx = hinge[N][0] / 2, mz = hinge.reduce((a, h) => a + h[1], 0) / hinge.length;
  const hs = hinge.map(([x, z]) => [x - mx, z - mz]);
  const cx = W / 2, cy = H / 2 + 6;
  const proj = (X, Z) => { const g = F / (F + Z); return { x: cx + X * g, g }; };
  const map = (ax, ay) => {
    const i = Math.max(0, Math.min(N - 1, Math.floor(ax / PA))), u = ax / PA - i;
    const X = hs[i][0] + (hs[i + 1][0] - hs[i][0]) * u, Z = hs[i][1] + (hs[i + 1][1] - hs[i][1]) * u, p = proj(X, Z);
    return [p.x, cy + (ay - AH / 2) * p.g, p.g];
  };
  return { hs, proj, map, cx, cy, th };
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const theta = thetaAt(t, lib), G = geometry(theta, lib);
  room(ctx, G, tokens, lib);
  face(t, theta, tokens, lib);
  panels(ctx, t, G, tokens, lib);
  floor(ctx, G, lib);
  pool(ctx, lib);
  brush(ctx, t, G, tokens, lib);
  type(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 12, seed: 5 });
  lib.vignette(ctx, { strength: 0.5, inner: 0.45, color: "#000000" });
}

/** A glossy floor: the bottom of the screen mirrored below it, fading fast. */
function floor(ctx, G, lib) {
  const { W, H } = lib, y = Math.round(G.cy + (AH / 2) * F / (F - 1) + 2), h = H - y;
  if (h <= 0) return;
  const src = lib.layer("lacquer-screen:floor", W, h);
  src.save(); src.translate(0, h); src.scale(1, -1); src.drawImage(ctx.canvas, 0, y - h, W, h, 0, 0, W, h); src.restore();
  src.globalCompositeOperation = "destination-in";
  const fg = src.createLinearGradient(0, 0, 0, h); fg.addColorStop(0, "rgba(0,0,0,0.22)"); fg.addColorStop(1, "rgba(0,0,0,0)");
  src.fillStyle = fg; src.fillRect(0, 0, W, h);
  ctx.drawImage(src.canvas, 0, y);
}
/** The key light's warm pool on the screen, falling off to the sides. */
function pool(ctx, lib) {
  const { W, H } = lib, g = ctx.createRadialGradient(W * 0.42, H * 0.38, 0, W * 0.45, H * 0.45, W * 0.62);
  g.addColorStop(0, "rgba(255,214,160,0.10)"); g.addColorStop(0.6, "rgba(255,214,160,0.02)"); g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}

function room(ctx, G, tokens, lib) {
  const { W, H } = lib;
  const g = ctx.createRadialGradient(W * 0.4, H * 0.35, 0, W * 0.5, H * 0.5, W * 0.75);
  g.addColorStop(0, lib.color(tokens, "room_hi")); g.addColorStop(1, lib.color(tokens, "room"));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // the floor line and the screen's soft contact shadow
  const x0 = G.map(0, AH)[0], x1 = G.map(AW - 0.01, AH)[0], y = G.cy + AH / 2 + 4;
  const s = ctx.createRadialGradient((x0 + x1) / 2, y, 0, (x0 + x1) / 2, y, (x1 - x0) * 0.6 + 40);
  s.addColorStop(0, "rgba(0,0,0,0.75)"); s.addColorStop(1, "rgba(0,0,0,0)");
  ctx.save(); ctx.translate(0, y); ctx.scale(1, 0.08); ctx.translate(0, -y); ctx.fillStyle = s; ctx.fillRect(0, y - 800, W, 1600); ctx.restore();
}

/** The face for this frame: the static lacquer, the written line, the nodes, the blossoms' shimmer. */
function face(t, theta, tokens, lib) {
  const x = L.art.getContext("2d"), P = (k) => lib.color(tokens, k);
  x.globalCompositeOperation = "source-over"; x.globalAlpha = 1; x.filter = "none";
  x.drawImage(L.base, 0, 0);
  // the blossoms: mother-of-pearl petals round a gold heart (always there, shimmering)
  for (const [k, b] of L.blossoms.entries()) {
    for (let p = 0; p < 5; p++) {
      const a = b.rot + (p / 5) * Math.PI * 2, px = b.x + Math.cos(a) * b.r * 0.9, py = b.y + Math.sin(a) * b.r * 0.9;
      shell(x, px, py, b.r * 0.62, a + Math.PI / 2, nacre(lib, px, py, k + p, theta, t), lib);
    }
    x.fillStyle = P("gold_hi"); x.beginPath(); x.arc(b.x, b.y, 3.2, 0, Math.PI * 2); x.fill();
  }
  // the line, as far as the brush has written it; it sinks back into the lacquer in the close
  const u = lib.seg(t, ...T.write), sink = 1 - lib.ease.inOutSine(lib.seg(t, ...T.sink));
  if (u > 0 && sink > 0) {
    const pts = LINE.pts, [hx, hy, hi] = lineAt(lib.ease.inOutSine(u));
    const part = pts.slice(0, hi).concat([[hx, hy]]);
    x.save(); x.globalAlpha = sink; x.lineCap = "round"; x.lineJoin = "round";
    x.shadowColor = lib.rgba(P("gold"), 0.55); x.shadowBlur = 16;
    x.strokeStyle = L.gold(x); x.lineWidth = 12; strokePts(x, part);
    x.shadowBlur = 0; x.strokeStyle = lib.rgba(P("gold_hi"), 0.8); x.lineWidth = 3;
    x.translate(-1, -2); strokePts(x, part); x.translate(1, 2);
    // the nodes: mother-of-pearl set in where the line turns, a flash as each goes in
    LINE.turns.forEach((nu, k) => {
      const tn = reach(nu);
      if (t < tn) return;
      const [nx, ny] = lineAt(nu), s = lib.spring(t - tn, { w: 22, zeta: 0.5 });
      for (let p = 0; p < 4; p++) {
        const a = p * Math.PI / 2 + 0.3, r = 21 * s;
        shell(x, nx + Math.cos(a) * r * 0.75, ny + Math.sin(a) * r * 0.75, r * 0.8, a + Math.PI / 2, nacre(lib, nx, ny, k * 3 + p, theta, t), lib);
      }
      const flash = Math.exp(-(t - tn) * 7);
      if (flash > 0.02) {
        const fg = x.createRadialGradient(nx, ny, 0, nx, ny, 18 + 46 * (1 - flash));
        fg.addColorStop(0, `rgba(255,252,240,${(0.95 * flash).toFixed(3)})`); fg.addColorStop(1, "rgba(255,240,200,0)");
        x.fillStyle = fg; x.beginPath(); x.arc(nx, ny, 18 + 46 * (1 - flash), 0, Math.PI * 2); x.fill();
      }
    });
    x.restore();
  }
}
function strokePts(x, pts) { x.beginPath(); pts.forEach(([px, py], i) => (i ? x.lineTo(px, py) : x.moveTo(px, py))); x.stroke(); }

/** Map the face onto the six panels by vertical strips, then light each panel by the way it faces. */
function panels(ctx, t, G, tokens, lib) {
  const STRIPS = 30, light = [-0.55, 0.835];
  for (let i = 0; i < N; i++) {
    const [X0, Z0] = G.hs[i], [X1, Z1] = G.hs[i + 1];
    for (let s = 0; s < STRIPS; s++) {
      const u0 = s / STRIPS, u1 = (s + 1) / STRIPS, um = (u0 + u1) / 2;
      const p0 = G.proj(X0 + (X1 - X0) * u0, Z0 + (Z1 - Z0) * u0), p1 = G.proj(X0 + (X1 - X0) * u1, Z0 + (Z1 - Z0) * u1);
      const g = G.proj(X0 + (X1 - X0) * um, Z0 + (Z1 - Z0) * um).g, h = AH * g;
      const w = Math.abs(p1.x - p0.x) + 0.6;                 // a hair of overlap: no seams between strips
      ctx.drawImage(L.art, i * PA + u0 * PA, 0, PA / STRIPS, AH, Math.min(p0.x, p1.x) - 0.3, G.cy - h / 2, w, h);
    }
    // light: the panel's normal against a key from the front left
    const s = i % 2 ? -1 : 1, nx = -s * Math.sin(G.th), nz = Math.cos(G.th);
    const lit = Math.max(0, nx * light[0] + nz * light[1]), shade = 0.5 + 0.5 * lit;
    const a = G.proj(X0, Z0), b = G.proj(X1, Z1);
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(a.x, G.cy - (AH / 2) * a.g); ctx.lineTo(b.x, G.cy - (AH / 2) * b.g);
    ctx.lineTo(b.x, G.cy + (AH / 2) * b.g); ctx.lineTo(a.x, G.cy + (AH / 2) * a.g); ctx.closePath();
    ctx.fillStyle = `rgba(0,0,0,${(1 - shade).toFixed(3)})`; ctx.fill();
    // the window's reflection: a soft band whose place on the panel follows the panel's angle
    // lacquer mirrors the room: a ceiling glow at the top of every panel, stronger on the lit ones
    const vg = ctx.createLinearGradient(0, G.cy - (AH / 2) * Math.max(a.g, b.g), 0, G.cy + (AH / 2) * Math.max(a.g, b.g));
    vg.addColorStop(0, `rgba(255,228,190,${(0.025 + 0.05 * lit).toFixed(3)})`); vg.addColorStop(0.3, "rgba(255,228,190,0)");
    vg.addColorStop(0.85, "rgba(0,0,0,0)"); vg.addColorStop(1, `rgba(255,210,150,${(0.03 + 0.04 * lit).toFixed(3)})`);
    ctx.fillStyle = vg; ctx.globalCompositeOperation = "screen"; ctx.fill(); ctx.globalCompositeOperation = "source-over";
    const us = 0.5 + 1.6 * (nx + 0.18), k = 0.2 * lit;
    if (k > 0.005) {
      const gr = ctx.createLinearGradient(a.x, 0, b.x, 0);
      const st = (q, al) => gr.addColorStop(Math.max(0, Math.min(1, q)), `rgba(255,236,205,${al.toFixed(3)})`);
      st(0, 0); st(us - 0.16, 0); st(us - 0.04, k * 0.8); st(us + 0.01, k * 2.2); st(us + 0.05, k * 0.8); st(us + 0.18, 0); st(1, 0);
      ctx.fillStyle = gr; ctx.globalCompositeOperation = "screen"; ctx.fill();
    }
    // the near edge of each fold catches a thin line of light
    ctx.globalCompositeOperation = "source-over";
    ctx.strokeStyle = `rgba(255,225,170,${(0.10 + 0.25 * lit).toFixed(3)})`; ctx.lineWidth = 1.5;
    const e = s > 0 ? a : b;
    ctx.beginPath(); ctx.moveTo(e.x, G.cy - (AH / 2) * e.g); ctx.lineTo(e.x, G.cy + (AH / 2) * e.g); ctx.stroke();
    ctx.restore();
  }
}

/** The brush: bamboo shaft, black ferrule, hair wet with gold at the tip; its reflection in the lacquer below. */
function brush(ctx, t, G, tokens, lib) {
  const { seg, lerp, ease } = lib;
  let tip = null, lift = 0;
  const start = G.map(...lineAt(0).slice(0, 2)), end = G.map(...lineAt(1).slice(0, 2));
  const away = [lib.W * 0.86, -520];
  if (t >= T.brushIn[0] && t < T.brushIn[1]) { const u = ease.outCubic(seg(t, ...T.brushIn)); tip = [lerp(away[0], start[0], u), lerp(away[1], start[1], u)]; lift = 1 - u; }
  else if (t >= T.write[0] && t < T.write[1]) { const [ax, ay] = lineAt(ease.inOutSine(seg(t, ...T.write))); tip = G.map(ax, ay); }
  else if (t >= T.brushOut[0] && t < T.brushOut[1]) { const u = ease.inCubic(seg(t, ...T.brushOut)); tip = [lerp(end[0], away[0] + 200, u), lerp(end[1], away[1], u)]; lift = u; }
  if (!tip) return;
  const P = (k) => lib.color(tokens, k);
  const press = t >= T.write[0] && t < T.write[1] ? 1 + 0.08 * Math.sin(t * 13) : 1;
  const draw = (alpha) => {
    ctx.save(); ctx.globalAlpha = alpha;
    ctx.translate(tip[0], tip[1] - 8 * lift); ctx.rotate(0.2);
    // hair: a cone, darker up, wet gold at the very tip
    const hg = ctx.createLinearGradient(0, 0, 0, -86);
    hg.addColorStop(0, P("gold_hi")); hg.addColorStop(0.18, P("gold")); hg.addColorStop(0.32, "#3a2a1c"); hg.addColorStop(1, "#1b140f");
    ctx.fillStyle = hg; ctx.beginPath(); ctx.moveTo(0, 2); ctx.quadraticCurveTo(15 * press, -36, 13, -86); ctx.lineTo(-13, -86); ctx.quadraticCurveTo(-15 * press, -36, 0, 2); ctx.fill();
    // ferrule
    ctx.fillStyle = "#0d0b0a"; ctx.fillRect(-15, -112, 30, 28);
    ctx.fillStyle = "rgba(255,230,190,0.25)"; ctx.fillRect(-9, -110, 4, 24);
    // bamboo shaft with two nodes
    const sg = ctx.createLinearGradient(-12, 0, 12, 0);
    sg.addColorStop(0, "#5b4126"); sg.addColorStop(0.35, "#c9a46a"); sg.addColorStop(0.7, "#8a6a3e"); sg.addColorStop(1, "#4a3420");
    ctx.fillStyle = sg; ctx.fillRect(-11, -560, 22, 450);
    ctx.fillStyle = "#3e2c1a"; for (const ny of [-250, -430]) ctx.fillRect(-12, ny, 24, 5);
    ctx.restore();
  };
  // shadow on the lacquer, offset right; then the brush
  ctx.save(); ctx.filter = "blur(10px)"; ctx.translate(26 + 40 * lift, 18 + 30 * lift); draw(0.35 - 0.2 * lift); ctx.restore();
  draw(1);
}

/** The title in gold over the screen, a small vermilion seal, the caption. */
function type(ctx, t, tokens, lib) {
  if (t < T.title) return;
  const P = (k) => lib.color(tokens, k);
  const { TYPE, SAFE, W } = lib;
  const out = 1 - lib.seg(t, T.sink[0] - 0.02, T.sink[0] + 0.22);
  if (out <= 0) return;
  const x0 = 250, y = 300;
  ctx.save();
  // a soft darkening behind the title so the gold reads on any panel
  const back = ctx.createRadialGradient(x0 + L.titleW / 2, y - 30, 10, x0 + L.titleW / 2, y - 30, L.titleW * 0.75);
  back.addColorStop(0, `rgba(0,0,0,${(0.55 * out).toFixed(3)})`); back.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = back; ctx.fillRect(0, 0, W, lib.H);
  // the title: gold leaf, glyphs in from a little below, staggered
  lib.setFont(ctx, tokens, "zh", TYPE.title);
  const g = ctx.createLinearGradient(0, y - TYPE.title, 0, y + 10);
  g.addColorStop(0, P("gold_hi")); g.addColorStop(0.55, P("gold")); g.addColorStop(1, P("gold_lo"));
  ctx.fillStyle = g; ctx.shadowColor = "rgba(0,0,0,0.6)"; ctx.shadowBlur = 8; ctx.shadowOffsetY = 3;
  const lay = lib.layoutText(ctx, lib.TITLE_ZH, { x: x0, y, align: "left", tracking: lib.tracking(tokens, "zh", TYPE.title) });
  lib.drawGlyphs(ctx, lay, (gl, i) => {
    const t0 = T.title + i * 0.035; if (t < t0) return null;
    const p = lib.ease.outCubic(lib.seg(t, t0, t0 + 0.32));
    return { alpha: out * p, dy: (1 - p) * 18 };
  });
  // the glint: a narrow band of light runs across the gold once
  const gu = lib.seg(t, ...T.glint);
  if (gu > 0 && gu < 1) {
    const gx = x0 - 120 + (L.titleW + 240) * lib.ease.inOutSine(gu);
    const gg = ctx.createLinearGradient(gx - 70, 0, gx + 70, 0);
    gg.addColorStop(0, "rgba(255,248,225,0)"); gg.addColorStop(0.5, "rgba(255,248,225,0.55)"); gg.addColorStop(1, "rgba(255,248,225,0)");
    ctx.save(); ctx.shadowColor = "transparent"; ctx.fillStyle = gg; ctx.globalAlpha = out;
    lib.drawGlyphs(ctx, lay, () => ({}));   // the glint is the title again, filled with the moving light
    ctx.restore();
  }
  ctx.shadowColor = "transparent";
  // English line under it
  lib.setFont(ctx, tokens, "en", TYPE.label, { style: "italic" }); ctx.fillStyle = P("ivory");
  ctx.globalAlpha = out * lib.clamp((t - T.title - 0.25) / 0.25);
  lib.drawText(ctx, lib.TITLE_EN, x0 + 4, y + TYPE.label * 1.5, { align: "left", tracking: TYPE.label * 0.04 });
  // the seal: one vermilion square, pressed after the title stands
  if (t >= T.seal) {
    const s = 1 + 0.25 * Math.exp(-(t - T.seal) * 16), sx = x0 + L.titleW + 46, sy = y - TYPE.title * 0.42;
    ctx.save(); ctx.globalAlpha = out * lib.clamp((t - T.seal) / 0.05); ctx.translate(sx, sy); ctx.scale(s, s); ctx.rotate(-0.04);
    ctx.fillStyle = P("vermilion"); ctx.fillRect(-27, -27, 54, 54);
    lib.setFont(ctx, tokens, "seal", 34); ctx.fillStyle = P("lacquer"); ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText("帧", 0, 2);
    ctx.restore();
  }
  // the caption, low, in ivory
  ctx.globalAlpha = out * lib.clamp((t - T.caption) / 0.15);
  lib.setFont(ctx, tokens, "zh", TYPE.caption, { weight: 400 }); ctx.fillStyle = P("ivory"); ctx.textBaseline = "middle";
  const cy = SAFE.title.y1 - TYPE.caption * 0.55;
  const cb = ctx.createLinearGradient(0, cy - 60, 0, cy + 60);
  cb.addColorStop(0, "rgba(0,0,0,0)"); cb.addColorStop(0.5, "rgba(0,0,0,0.45)"); cb.addColorStop(1, "rgba(0,0,0,0)");
  ctx.save(); ctx.fillStyle = cb; ctx.fillRect(W / 2 - 420, cy - 60, 840, 120); ctx.restore();
  lib.drawText(ctx, lib.CAPTION_ZH, W / 2, cy, { align: "center", tracking: TYPE.caption * 0.08 });
  ctx.restore();
}
