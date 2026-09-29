// editorial-data swatch: a newspaper graphics desk page.
//   0.0–0.8  newsprint, baseline + two faint rules draw on, grey context series draw linearly
//   0.8–2.6  serif headline word by word; Chinese line character by character
//   1.5–2.8  "what you might expect" dashed guess → the real series draws linearly in brick red, and the three
//            annotations (outline → storyboard → draft) appear as the line reaches their points
//   3.0      poster: headline, Chinese, red line breaking out of the frame, three pinned notes
//   3.3–3.9  staged rescale: y domain 0–100 → 0–150, every note stays pinned to its data point
//   4.0–4.75 the whole page scrolls up to the next "section" (end frame)
// Data are illustrative (labelled on screen).

let L = null;
const ZHF = { fonts: { zh: ["PingFang SC", "Hiragino Sans GB"] } };   // annotation Chinese (tokens.zh is the serif headline face)
export const fonts = ["PingFang SC"];

const YEARS = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026];
const RED = [14, 17, 21, 26, 31, 38, 46, 55, 66, 84, 122];
const GREY = [
  [30, 32, 31, 33, 35, 34, 36, 35, 37, 38, 37],
  [22, 21, 23, 24, 23, 25, 24, 26, 27, 26, 28],
  [44, 42, 45, 43, 44, 46, 45, 47, 46, 48, 49],
  [11, 12, 12, 13, 12, 14, 15, 14, 15, 16, 16],
];
const GUESS = [14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34];
const NOTES = [
  { i: 2, up: 168, align: "left" },
  { i: 5, up: 128, align: "left" },
  { i: 8, up: 124, align: "right" },
];

export async function setup(ctx, tokens, lib) {
  const plot = { x0: 192, x1: 1500, y0: 432, y1: 872 };
  L = { plot };
}

const X = (i) => L.plot.x0 + (L.plot.x1 - L.plot.x0) * i / (YEARS.length - 1);
function Y(v, max) { return L.plot.y1 - (L.plot.y1 - L.plot.y0) * v / max; }

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const u = lib.tween(t, 4.0, 4.75, lib.ease.inOutCubic);
  if (u <= 0) return page(ctx, t, tokens, lib, 0);
  ctx.save(); ctx.translate(0, -H * u); page(ctx, t, tokens, lib, 0); ctx.restore();
  ctx.save(); ctx.translate(0, H * (1 - u)); endPage(ctx, t, tokens, lib); ctx.restore();
}

function page(ctx, t, tokens, lib) {
  const { W, H, seg, clamp } = lib;
  const P = (k) => lib.color(tokens, k);
  const ink = P("fg"), red = P("accent"), grey = P("extra.1"), rule = P("extra.2"), muted = P("extra.3");
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  lib.paper(ctx, { tone: P("bg"), amount: 0.7, blotch: 0.02, tooth: 0.012, fiber: 0.25, seed: 9 });

  // y domain: 100 → 150 (staged rescale 3.3–3.9)
  const max = lib.lerp(100, 150, lib.tween(t, 3.3, 3.9, lib.ease.inOutCubic));
  const p = L.plot;

  // ── rules + tick labels (value multiples of 50; 150 fades in with the rescale)
  ctx.save();
  lib.setFont(ctx, tokens, "body", 24, { weight: 400 });
  for (const v of [50, 100, 150]) {
    const y = Y(v, max);
    const a = v === 150 ? seg(t, 3.55, 3.9) : lib.tween(t, 0.3 + v / 500, 0.75 + v / 500, lib.ease.outCubic);
    if (a <= 0 || y < p.y0 - 60) continue;
    ctx.globalAlpha = v === 150 ? a : 1; ctx.strokeStyle = rule; ctx.lineWidth = 1.5;
    lib.strokePartial(ctx, [[p.x0, y], [p.x1 + 40, y]], v === 150 ? 1 : a);
    ctx.fillStyle = muted; ctx.globalAlpha = (v === 150 ? a : clamp(a * 2 - 1)) * 1;
    lib.drawText(ctx, String(v), p.x0, y - 12);
  }
  ctx.restore();
  // baseline + year labels
  ctx.save(); ctx.strokeStyle = ink; ctx.lineWidth = 2;
  lib.strokePartial(ctx, [[p.x0, p.y1], [p.x1 + 40, p.y1]], lib.tween(t, 0.15, 0.6, lib.ease.outCubic));
  lib.setFont(ctx, tokens, "body", 24, { weight: 400 }); ctx.fillStyle = muted; ctx.globalAlpha = seg(t, 0.45, 0.8);
  for (const i of [0, 5, 10]) lib.drawText(ctx, String(YEARS[i]), X(i), p.y1 + 40, { align: i === 0 ? "left" : i === 10 ? "right" : "center" });
  lib.drawText(ctx, "0", p.x0, p.y1 - 12);
  ctx.restore();

  // ── grey context series: draw linearly (time is the x axis)
  GREY.forEach((s, k) => series(ctx, s, max, lib.seg(t, 0.4 + k * 0.1, 1.3 + k * 0.1), grey, 2.5));
  // ── the guess: dashed grey, then kept at 35 % as a reference
  const gu = seg(t, 1.5, 1.9);
  if (gu > 0) {
    ctx.save(); ctx.setLineDash([12, 9]); ctx.globalAlpha = t < 2.0 ? 1 : lib.lerp(1, 0.55, seg(t, 2.0, 2.4));
    series(ctx, GUESS, max, gu, ink, 2.5, true); ctx.setLineDash([]);
    lib.setFont(ctx, tokens, "body", 26, { weight: 500 }); ctx.fillStyle = ink; ctx.globalAlpha *= seg(t, 1.8, 2.0);
    lib.drawText(ctx, "expected", X(10) + 18, Y(GUESS[10], max) + 9);
    ctx.restore();
  }
  // ── the real series, brick red, linear in x
  const ru = seg(t, 1.95, 2.75);
  series(ctx, RED, max, ru, red, 5.5);
  if (ru >= 1) {                                                   // end dot + direct label
    const x = X(10), y = Y(RED[10], max);
    ctx.save(); ctx.fillStyle = red; ctx.beginPath(); ctx.arc(x, y, 8, 0, lib.TAU); ctx.fill();
    lib.setFont(ctx, tokens, "body", 30, { weight: 700 }); ctx.globalAlpha = seg(t, 2.75, 2.95);
    lib.drawText(ctx, "Code", x + 22, y + 11);
    ctx.restore();
  }
  // ── annotations pinned in data space
  NOTES.forEach((n, k) => note(ctx, t, tokens, lib, n, k, max));

  // ── headline: serif, word by word (80 ms), 12 px rise
  lib.setFont(ctx, tokens, "display", 80, { weight: 700 }); ctx.fillStyle = ink;
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: 192, y: 205, tracking: -0.01 * 80 });
  let w = -1, prev = " ";
  const wi = lay.glyphs.map((g) => { if (prev === " " && g.ch !== " ") w++; prev = g.ch; return w; });
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const a = lib.tween(t, 0.85 + wi[i] * 0.08, 1.25 + wi[i] * 0.08, lib.ease.outCubic);
    return a <= 0 ? null : { alpha: a, dy: (1 - a) * 12 };
  });
  // Chinese headline (Songti SC Bold), 60 ms per character
  lib.setFont(ctx, tokens, "zh", 58, { weight: 700 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: 192, y: 300, tracking: 0.04 * 58 });
  lib.drawGlyphs(ctx, zl, (g, i) => {
    const a = lib.tween(t, 1.3 + i * 0.06, 1.62 + i * 0.06, lib.ease.outCubic);
    return a <= 0 ? null : { alpha: a, dy: (1 - a) * 10 };
  });
  // thin rule under the headline block, like a section break in print
  ctx.save(); ctx.strokeStyle = ink; ctx.lineWidth = 1.5;
  lib.strokePartial(ctx, [[192, 346], [700, 346]], lib.tween(t, 1.6, 2.0, lib.ease.outCubic)); ctx.restore();

  // ── source line, bottom-left, 60 %
  ctx.save(); lib.setFont(ctx, tokens, "body", 24, { weight: 400 }); ctx.fillStyle = muted; ctx.globalAlpha = 0.6 * seg(t, 0.5, 0.9);
  lib.drawText(ctx, "Illustrative data · OpenVideoHarness style swatch", 192, 1000);
  ctx.restore();
}

function series(ctx, vals, max, u, col, lw, noDots) {
  if (u <= 0) return;
  const n = vals.length - 1, f = u * n, k = Math.floor(f);
  const pts = [];
  for (let i = 0; i <= Math.min(k, n); i++) pts.push([X(i), Y(vals[i], max)]);
  if (k < n) { const r = f - k; pts.push([X(k) + (X(k + 1) - X(k)) * r, Y(vals[k] + (vals[k + 1] - vals[k]) * r, max)]); }
  ctx.save(); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineJoin = "round"; ctx.lineCap = "round";
  ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.stroke();
  ctx.restore();
}

function note(ctx, t, tokens, lib, n, k, max) {
  const t0 = 1.95 + 0.8 * n.i / (RED.length - 1);               // the red line reaches this point at t0
  const a = lib.seg(t, t0, t0 + 0.3);
  if (a <= 0) return;
  const P = (q) => lib.color(tokens, q);
  const x = X(n.i), y = Y(RED[n.i], max), ty = y - n.up;
  ctx.save();
  lib.setFont(ctx, ZHF, "zh", 46, { weight: 600 }); const zw = ctx.measureText(lib.MOTIF[k].zh).width + 0.06 * 46 * 1;
  lib.setFont(ctx, tokens, "body", 28, { weight: 500 }); const ew = ctx.measureText(lib.MOTIF[k].en).width;
  const tot = zw + 18 + ew, sx = n.align === "right" ? x + 12 - tot : x - 12;
  ctx.strokeStyle = P("fg"); ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.arc(x, y, 9, 0, lib.TAU); ctx.stroke();                       // ring on the data point
  lib.strokePartial(ctx, [[x, y - 9], [x, ty + 16]], lib.ease.outCubic(a));           // leader
  const b = lib.seg(t, t0 + 0.12, t0 + 0.4);
  ctx.globalAlpha = b;
  lib.setFont(ctx, ZHF, "zh", 46, { weight: 600 }); ctx.fillStyle = P("fg");
  lib.drawText(ctx, lib.MOTIF[k].zh, sx, ty + (1 - b) * 8, { tracking: 0.06 * 46 });
  lib.setFont(ctx, tokens, "body", 28, { weight: 500 }); ctx.fillStyle = P("extra.3");
  lib.drawText(ctx, lib.MOTIF[k].en, sx + zw + 18, ty - 2 + (1 - b) * 8);
  ctx.restore();
}

function endPage(ctx, t, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  lib.paper(ctx, { tone: P("bg"), amount: 0.7, blotch: 0.02, tooth: 0.012, fiber: 0.25, seed: 9 });
  ctx.fillStyle = P("accent"); ctx.fillRect(192, 430, 120, 10);
  lib.setFont(ctx, tokens, "display", 110, { weight: 700 }); ctx.fillStyle = P("fg");
  lib.drawText(ctx, "Editorial Data", 192, 580, { tracking: -0.01 * 110 });
  lib.setFont(ctx, tokens, "zh", 60, { weight: 700 });
  lib.drawText(ctx, "编辑部数据叙事", 192, 675, { tracking: 0.04 * 60 });
}
