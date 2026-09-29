// dark-math swatch: geometry on black, one colour per entity, change by continuous transformation.
//   0.0–0.8  number-plane grid and axes draw outward from the origin
//   0.8–2.6  title "written": glyph outlines trace, then fill (English, then Chinese)
//   2.0–2.9  outline → storyboard → draft as 0-D → 1-D → 2-D: a blue point; a copy of it transforms into a green
//            vector; a copy of that sweeps into a yellow parallelogram (each label in its entity colour)
//   3.2–3.8  indicate each object in turn (there-and-back scale)
//   4.0–4.9  all three transform into one yellow circle, which becomes the end-of-proof square next to the name
// Every shape is a 64-point polygon, so any shape can morph into any other by per-point lerp.

let L = null;
const N = 64;
// ONE timing table for the picture and the foley (FOLEY → events.json via styles/_swatch/foley.mjs)
const TL = {
  axes: [0.0, 0.42], grid: [0.0, 0.6], basis: [0.4, 0.47], title0: 0.85, stag: 0.055, write: 0.42, zh0: 1.55, zhStag: 0.08,
  dot: [2.0, 2.25], vec: [2.22, 2.58], par: [2.52, 2.86], labels: [2.12, 2.5, 2.8], beats: [3.0, 3.5], push: [2.6, 4.0],
  out: [4.0, 4.35], ball: [4.0, 4.4], sq: [4.35, 4.62], name: 4.35, nameZh: 4.45,
};
const SLOT_X = [448, 960, 1472];                                        // lib.slots(3, SAFE.title)
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;          // pan = (2x/W − 1) · 0.7
export const FOLEY = [
  ...TL.basis.map((t, k) => ({ t: t + 0.05, sfx: "tick", gain_db: -14, pan: pan(k ? 960 : 1020) })),   // î, then ĵ pop out of the origin
  { t: TL.title0 + 0.05, sfx: "tick", gain_db: -18, pan: pan(560) },                       // the pen touches down (English)
  { t: TL.zh0 + 0.05, sfx: "tick", gain_db: -18, pan: pan(700) },                          // …and again (Chinese)
  { t: TL.dot[0] + 0.12, sfx: "pop", gain_db: -12, pan: pan(SLOT_X[0]) },                 // the point appears
  // the two TransformFromCopy morphs stay silent: this style has no whoosh
  ...TL.beats.map((t) => ({ t, sfx: "ding", gain_db: -10 })),                              // indicate + flash
  { t: TL.sq[1], sfx: "click", gain_db: -8, pan: pan(1240) },                              // ∎ the tombstone lands
];

function resample(poly, n = N) {                       // closed polygon → n points evenly spaced by arc length
  const segs = []; let tot = 0;
  for (let i = 0; i < poly.length; i++) { const a = poly[i], b = poly[(i + 1) % poly.length]; const l = Math.hypot(b[0] - a[0], b[1] - a[1]); segs.push([a, b, l]); tot += l; }
  const out = []; let k = 0, acc = 0;
  for (let j = 0; j < n; j++) {
    const d = (j / n) * tot;
    while (acc + segs[k][2] < d) { acc += segs[k][2]; k++; }
    const [a, b, l] = segs[k], u = l ? (d - acc) / l : 0;
    out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]);
  }
  return out;
}
const circle = (cx, cy, r) => Array.from({ length: N }, (_, j) => { const a = -Math.PI / 2 + (j / N) * Math.PI * 2; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; });
function arrow(ax, ay, bx, by, w = 7, hw = 22, hl = 34) {  // a vector as one closed outline (shaft + head)
  const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy), ux = dx / len, uy = dy / len, nx = -uy, ny = ux;
  const hx = bx - ux * hl, hy = by - uy * hl;
  return [[ax + nx * w / 2, ay + ny * w / 2], [hx + nx * w / 2, hy + ny * w / 2], [hx + nx * hw / 2, hy + ny * hw / 2], [bx, by],
          [hx - nx * hw / 2, hy - ny * hw / 2], [hx - nx * w / 2, hy - ny * w / 2], [ax - nx * w / 2, ay - ny * w / 2]];
}
const lerpPts = (A, B, u) => A.map((p, i) => [p[0] + (B[i][0] - p[0]) * u, p[1] + (B[i][1] - p[1]) * u]);
const shift = (A, dx, dy) => A.map(([x, y]) => [x + dx, y + dy]);
const scaleAbout = (A, s, cx, cy) => A.map(([x, y]) => [cx + (x - cx) * s, cy + (y - cy) * s]);

export async function setup(ctx, tokens, lib) {
  const s = lib.slots(3, { area: lib.SAFE.title, y: 640 });
  const O = { x: 960, y: 800 }, U = 160;                              // the x axis is the motif's baseline
  const TOP = 400;                                                     // motif 400–800 (centre ≈ 0.55 H), 1.3× the old height
  const dot = circle(s[0].x, 610, 72);
  const vec = resample(arrow(s[1].x - 270, O.y, s[1].x + 270, TOP + 30, 22, 70, 104));   // tip kept clear of the Chinese line
  const par = resample([[s[2].x - 300, O.y], [s[2].x + 135, O.y], [s[2].x + 300, TOP], [s[2].x - 135, TOP]]);
  const iHat = arrow(O.x, O.y, O.x + U, O.y, 13, 40, 50), jHat = arrow(O.x, O.y, O.x, O.y - U, 13, 40, 50);
  const cen = (A) => A.reduce((c, p) => [c[0] + p[0] / A.length, c[1] + p[1] / A.length], [0, 0]);
  L = { s, O, U, dot, vec, par, iHat, jHat, cDot: cen(dot), cVec: cen(vec), cPar: cen(par), ball: circle(960, 470, 70) };
  // end frame layout: "Dark Math" + tombstone square
  lib.setFont(ctx, tokens, "display", 120, { weight: 500 });
  L.endW = ctx.measureText("Dark Math").width;
  const sq = 64, ex = 960 - (L.endW + 40 + sq) / 2;
  L.endX = ex; L.sq = resample([[ex + L.endW + 40, 560 - sq], [ex + L.endW + 40 + sq, 560 - sq], [ex + L.endW + 40 + sq, 560], [ex + L.endW + 40, 560]]);
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H, seg, clamp, tween } = lib;
  const P = (k) => lib.color(tokens, k);
  const smooth = lib.easeOf(tokens.ease.enter);
  const BLUE = P("extra.0"), RED = P("extra.1"), GREEN = P("extra.2"), YEL = P("accent"), WHITE = P("fg");
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);

  const out = tween(t, ...TL.out, smooth);                        // everything but the shapes fades out at the end
  // ── number plane: the whole grid sweeps out from the origin as a growing disc with a bright front (0–0.6 s),
  //    then settles to a ~25 % structure layer
  const { O, U } = L;
  ctx.save(); ctx.lineWidth = 2;
  const Rg = tween(t, ...TL.grid, lib.ease.outCubic) * 2100;
  const gridPath = () => {
    ctx.beginPath();
    for (let k = -6; k <= 6; k++) { const x = O.x + k * U; if (k) { ctx.moveTo(x, 0); ctx.lineTo(x, H); } }
    for (let k = -5; k <= 2; k++) { const y = O.y + k * U; if (k && y > 0 && y < H) { ctx.moveTo(0, y); ctx.lineTo(W, y); } }
  };
  if (Rg > 0) {
    ctx.save(); ctx.beginPath(); ctx.arc(O.x, O.y, Rg, 0, lib.TAU); ctx.clip();
    ctx.strokeStyle = lib.rgba(BLUE, 0.42 * (1 - 0.55 * out) * (1 - 0.3 * seg(t, 1.0, 1.6))); gridPath(); ctx.stroke();
    const front = 1 - seg(t, TL.grid[1] - 0.15, TL.grid[1] + 0.25);          // the last 120 px behind the sweep glow
    if (front > 0) {
      ctx.beginPath(); ctx.arc(O.x, O.y, Rg, 0, lib.TAU); ctx.arc(O.x, O.y, Math.max(0, Rg - 120), 0, lib.TAU); ctx.clip("evenodd");
      ctx.strokeStyle = lib.rgba(BLUE, 0.95 * front); ctx.lineWidth = 3; gridPath(); ctx.stroke();
    }
    ctx.restore();
  }
  ctx.strokeStyle = lib.rgba(WHITE, 0.62 * (1 - 0.6 * out)); ctx.lineWidth = 4;
  const ax = tween(t, ...TL.axes, lib.ease.outExpo);
  lib.strokePartial(ctx, [[O.x, O.y], [O.x - 1000 * ax, O.y]], 1); lib.strokePartial(ctx, [[O.x, O.y], [O.x + 1000 * ax, O.y]], 1);
  lib.strokePartial(ctx, [[O.x, O.y], [O.x, O.y - 720 * ax]], 1); lib.strokePartial(ctx, [[O.x, O.y], [O.x, O.y + 400 * ax]], 1);
  ctx.restore();
  // a dark band behind the title keeps the text off the grid (Manim's background rectangle)
  ctx.save(); const band = ctx.createLinearGradient(0, 60, 0, 450);
  band.addColorStop(0, "rgba(0,0,0,0)"); band.addColorStop(0.2, "rgba(0,0,0,0.88)"); band.addColorStop(0.78, "rgba(0,0,0,0.88)"); band.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = band; ctx.fillRect(0, 60, W, 390); ctx.restore();

  // ── basis vectors î (green) and ĵ (red) pop out of the origin, then clear the stage for the motif
  const hatOut = 1 - seg(t, TL.dot[0] - 0.15, TL.dot[0] + 0.15);
  [[L.iHat, GREEN, "î", [U + 8, 64]], [L.jHat, RED, "ĵ", [-54, -U + 30]]].forEach(([A, col, name, [lx, ly]], k) => {
    const sp = clamp(lib.spring(t - TL.basis[k], { w: 24, zeta: 0.5 }), 0, 1.4);
    if (sp <= 0 || hatOut <= 0) return;
    shape(ctx, scaleAbout(A, sp, O.x, O.y), col, hatOut);
    ctx.save(); ctx.globalAlpha = hatOut * clamp(sp); ctx.fillStyle = col;
    lib.setFont(ctx, tokens, "display", 76, { style: "italic", weight: 400 }); lib.drawText(ctx, name, O.x + lx, O.y + ly, { align: "center" });
    ctx.restore();
  });

  // ── title, hand-written
  ctx.save(); ctx.globalAlpha = 1 - out;
  lib.setFont(ctx, tokens, "display", 104, { weight: 500 });
  write(ctx, lib, lib.TITLE_EN, 960, 244, t, TL.title0, TL.stag, TL.write, WHITE, 104);
  lib.setFont(ctx, tokens, "zh", 62, { weight: 400 });
  write(ctx, lib, lib.TITLE_ZH, 960, 348, t, TL.zh0, TL.zhStag, TL.write, WHITE, 62, 0.08 * 62);
  ctx.restore();

  // ── motif: point → vector → parallelogram (TransformFromCopy chain)
  const dIn = tween(t, ...TL.dot, smooth);
  const vU = tween(t, ...TL.vec, smooth), pU = tween(t, ...TL.par, smooth);
  const endU = tween(t, ...TL.ball, smooth), sqU = tween(t, ...TL.sq, smooth);
  // indicate: every object pulses 1.2× with a flash on 3.0 s and 3.5 s (bell), plus a slow push-in while it holds
  const pulse = (a) => { const u = seg(t, a, a + 0.26); return Math.sin(Math.PI * u); };
  const ind = (k) => 1 + 0.2 * TL.beats.reduce((a, b) => a + pulse(b), 0) * (k === 2 ? 1 : 0.7);
  const push = 1 + 0.045 * lib.ease.inOutSine(seg(t, ...TL.push));
  ctx.save(); ctx.translate(960, 640); ctx.scale(push, push); ctx.translate(-960, -640);

  const toEnd = (A) => sqU > 0 ? lerpPts(L.ball, L.sq, sqU) : lerpPts(A, L.ball, endU);
  // point (stays at slot 1)
  if (dIn > 0) {
    let A = scaleAbout(L.dot, dIn * ind(0), L.cDot[0], L.cDot[1]);
    shape(ctx, toEnd(A), lib.mixColor(BLUE, YEL, endU), 1);
  }
  // copy → vector
  if (vU > 0) {
    const src = L.dot, dst = scaleAbout(L.vec, ind(1), L.cVec[0], L.cVec[1]);
    shape(ctx, toEnd(lerpPts(src, dst, vU)), lib.mixColor(lib.mixColor(BLUE, GREEN, vU), YEL, endU), 1);
  }
  // copy of the vector → parallelogram (fill fades in as it gains area)
  if (pU > 0) {
    const dst = scaleAbout(L.par, ind(2), L.cPar[0], L.cPar[1]);
    const col = lib.mixColor(GREEN, YEL, pU);
    const fa = lib.lerp(lib.lerp(1, 0.35, pU), 1, Math.max(endU, sqU));
    shape(ctx, toEnd(lerpPts(L.vec, dst, pU)), col, fa, 4 * pU * (1 - endU));
  }
  // flash: short yellow rays burst from each object on the two indicate beats
  for (const a0 of TL.beats) {
    const u = seg(t, a0, a0 + 0.3);
    if (u <= 0 || u >= 1) continue;
    [L.cDot, L.cVec, L.cPar].forEach((c, k) => {
      const r0 = [95, 215, 230][k] + 90 * lib.ease.outCubic(u), r1 = r0 + 40 * (1 - u);
      ctx.save(); ctx.strokeStyle = YEL; ctx.globalAlpha = 1 - u; ctx.lineWidth = 5; ctx.lineCap = "round";
      for (let i = 0; i < 10; i++) { const q = (i / 10) * lib.TAU; ctx.beginPath(); ctx.moveTo(c[0] + Math.cos(q) * r0, c[1] + Math.sin(q) * r0); ctx.lineTo(c[0] + Math.cos(q) * r1, c[1] + Math.sin(q) * r1); ctx.stroke(); }
      ctx.restore();
    });
  }
  ctx.restore();
  // labels in entity colours
  const labels = [[BLUE, TL.labels[0]], [GREEN, TL.labels[1]], [YEL, TL.labels[2]]];
  labels.forEach(([col, a0], k) => {
    const a = seg(t, a0, a0 + 0.16) * (1 - out);
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = col;
    lib.setFont(ctx, tokens, "display", 52, { style: "italic", weight: 400 });
    lib.drawText(ctx, lib.MOTIF[k].en, L.s[k].x, 878, { align: "center" });
    lib.setFont(ctx, tokens, "zh", 58, { weight: 400 });
    lib.drawText(ctx, lib.MOTIF[k].zh, L.s[k].x, 952, { align: "center", tracking: 0.1 * 58 });
    ctx.restore();
  });

  // ── end frame: the name is written next to the tombstone
  if (t >= TL.name) {
    ctx.save(); lib.setFont(ctx, tokens, "display", 120, { weight: 500 });
    ctx.textAlign = "left";
    write(ctx, lib, "Dark Math", L.endX + L.endW / 2, 560, t, TL.name, 0.03, 0.28, WHITE, 120);
    lib.setFont(ctx, tokens, "zh", 56, { weight: 400 });
    write(ctx, lib, "暗底数学", L.endX + L.endW / 2, 660, t, TL.nameZh, 0.05, 0.25, lib.color(tokens, "extra.4"), 56, 0.2 * 56);
    ctx.restore();
  }
}

function shape(ctx, pts, col, fillA, lw = 0) {
  ctx.save(); ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath();
  ctx.lineJoin = "round"; ctx.fillStyle = col; ctx.strokeStyle = col;
  ctx.globalAlpha = fillA; ctx.fill();
  if (lw > 0.2) { ctx.globalAlpha = 1; ctx.lineWidth = lw; ctx.stroke(); }
  ctx.restore();
}

// Hand-writing: each glyph's outline is traced with a growing dash, then the fill comes in over the last 45 %.
function write(ctx, lib, str, cx, y, t, t0, stagger, dur, col, size, trk = 0) {
  const lay = lib.layoutText(ctx, str, { x: cx, y, align: "center", tracking: trk });
  const Lmax = size * 5.5;
  ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "alphabetic"; ctx.letterSpacing = "0px";
  const base = ctx.globalAlpha; let n = 0;
  for (const g of lay.glyphs) {
    if (g.ch === " ") continue;
    const u = lib.seg(t, t0 + n * stagger, t0 + n * stagger + dur); n++;
    if (u <= 0) continue;
    if (u < 1) {
      ctx.setLineDash([Lmax * lib.ease.inOutSine(Math.min(1, u / 0.7)), 1e5]); ctx.lineDashOffset = 0;
      ctx.strokeStyle = col; ctx.lineWidth = Math.max(1.5, size / 45); ctx.strokeText(g.ch, g.cx, y);
      ctx.setLineDash([]);
    }
    const f = lib.smoothstep(0.55, 1, u);
    if (f > 0) { ctx.globalAlpha = base * f; ctx.fillStyle = col; ctx.fillText(g.ch, g.cx, y); ctx.globalAlpha = base; }
  }
  ctx.restore();
}
