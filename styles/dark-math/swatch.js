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
  const O = { x: 960, y: 700 }, U = 120;
  const dot = circle(s[0].x, 640, 26);
  const vec = resample(arrow(s[1].x - 140, 730, s[1].x + 140, 560, 11, 34, 52));
  const par = resample([[s[2].x - 180, 730], [s[2].x + 80, 730], [s[2].x + 180, 560], [s[2].x - 80, 560]]);
  const cen = (A) => A.reduce((c, p) => [c[0] + p[0] / A.length, c[1] + p[1] / A.length], [0, 0]);
  L = { s, O, U, dot, vec, par, cDot: cen(dot), cVec: cen(vec), cPar: cen(par), ball: circle(960, 470, 70) };
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

  const out = tween(t, 4.0, 4.35, smooth);                        // everything but the shapes fades out at the end
  // ── number plane: grid lines draw outward from the origin, then settle to a faint structure layer
  const { O, U } = L;
  ctx.save(); ctx.lineWidth = 2;
  const gridA = 0.22 * (1 - 0.55 * out);
  for (let k = -9; k <= 9; k++) {
    const x = O.x + k * U, u = tween(t, 0.1 + Math.abs(k) * 0.035, 0.55 + Math.abs(k) * 0.035, smooth);
    if (u > 0 && k !== 0 && x > -2 && x < W + 2) { ctx.strokeStyle = lib.rgba(BLUE, gridA); lib.strokePartial(ctx, [[x, O.y], [x, O.y - 700 * u]], 1); lib.strokePartial(ctx, [[x, O.y], [x, O.y + 700 * u]], 1); }
  }
  for (let k = -6; k <= 4; k++) {
    const y = O.y + k * U, u = tween(t, 0.1 + Math.abs(k) * 0.05, 0.55 + Math.abs(k) * 0.05, smooth);
    if (u > 0 && k !== 0 && y > -2 && y < H + 2) { ctx.strokeStyle = lib.rgba(BLUE, gridA); lib.strokePartial(ctx, [[O.x, y], [O.x - 1100 * u, y]], 1); lib.strokePartial(ctx, [[O.x, y], [O.x + 1100 * u, y]], 1); }
  }
  ctx.strokeStyle = lib.rgba(WHITE, 0.5 * (1 - 0.6 * out)); ctx.lineWidth = 3;
  const ax = tween(t, 0.1, 0.7, smooth);
  lib.strokePartial(ctx, [[O.x, O.y], [O.x - 1000 * ax, O.y]], 1); lib.strokePartial(ctx, [[O.x, O.y], [O.x + 1000 * ax, O.y]], 1);
  lib.strokePartial(ctx, [[O.x, O.y], [O.x, O.y - 720 * ax]], 1); lib.strokePartial(ctx, [[O.x, O.y], [O.x, O.y + 400 * ax]], 1);
  ctx.restore();
  // a dark band behind the title keeps the text off the grid (Manim's background rectangle)
  ctx.save(); const band = ctx.createLinearGradient(0, 60, 0, 450);
  band.addColorStop(0, "rgba(0,0,0,0)"); band.addColorStop(0.2, "rgba(0,0,0,0.88)"); band.addColorStop(0.78, "rgba(0,0,0,0.88)"); band.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = band; ctx.fillRect(0, 60, W, 390); ctx.restore();

  // ── title, hand-written
  ctx.save(); ctx.globalAlpha = 1 - out;
  lib.setFont(ctx, tokens, "display", 104, { weight: 500 });
  write(ctx, lib, lib.TITLE_EN, 960, 232, t, 0.85, 0.055, 0.42, WHITE, 104);
  lib.setFont(ctx, tokens, "zh", 62, { weight: 400 });
  write(ctx, lib, lib.TITLE_ZH, 960, 338, t, 1.55, 0.08, 0.42, WHITE, 62, 0.08 * 62);
  ctx.restore();

  // ── motif: point → vector → parallelogram (TransformFromCopy chain)
  const dIn = tween(t, 2.0, 2.25, smooth);
  const vU = tween(t, 2.22, 2.58, smooth), pU = tween(t, 2.52, 2.86, smooth);
  const endU = tween(t, 4.0, 4.4, smooth), sqU = tween(t, 4.35, 4.62, smooth);
  const ind = (k) => { const a = 3.2 + k * 0.2; const u = seg(t, a, a + 0.28); return 1 + 0.12 * Math.sin(Math.PI * u); };

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
  // labels in entity colours
  const labels = [[BLUE, 2.12], [GREEN, 2.5], [YEL, 2.8]];
  labels.forEach(([col, a0], k) => {
    const a = seg(t, a0, a0 + 0.16) * (1 - out);
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = col;
    lib.setFont(ctx, tokens, "display", 44, { style: "italic", weight: 400 });
    lib.drawText(ctx, lib.MOTIF[k].en, L.s[k].x, 830, { align: "center" });
    lib.setFont(ctx, tokens, "zh", 50, { weight: 400 });
    lib.drawText(ctx, lib.MOTIF[k].zh, L.s[k].x, 902, { align: "center", tracking: 0.1 * 50 });
    ctx.restore();
  });

  // ── end frame: the name is written next to the tombstone
  if (t >= 4.35) {
    ctx.save(); lib.setFont(ctx, tokens, "display", 120, { weight: 500 });
    ctx.textAlign = "left";
    write(ctx, lib, "Dark Math", L.endX + L.endW / 2, 560, t, 4.35, 0.03, 0.28, WHITE, 120);
    lib.setFont(ctx, tokens, "zh", 56, { weight: 400 });
    write(ctx, lib, "暗底数学", L.endX + L.endW / 2, 660, t, 4.45, 0.05, 0.25, lib.color(tokens, "extra.4"), 56, 0.2 * 56);
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
