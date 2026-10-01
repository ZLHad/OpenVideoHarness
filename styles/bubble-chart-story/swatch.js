// bubble-chart-story swatch: one bubble chart, time performed by a narrator. ILLUSTRATIVE DATA (fictional entities).
//   0.0–0.4  hook: axes shoot out, the huge year watermark rolls in, 44 bubbles pop in at 1950 and time starts at once
//   0.1–2.08 time races (30 years/s) and eases out into 2000; the year rolls like an odometer
//   0.8–2.6  title word by word, Chinese character by character
//   2.08–2.5 time holds: other bubbles dim to 20 %, a pointer stick (the narrator) taps outline → storyboard → draft;
//            each focus bubble keeps a dotted trail and gets a direct label
//   2.5–3.0  signature rewind: "wait, back to 1985" — the odometer rolls backward, trails retract
//   3.0–3.5  hold on 1985, the pointer taps twice;  3.5–4.0 time races forward to 2020
//   4.0–4.6  ending: time rewinds 2020 → 2000 while the axes rescale (zoom into the story), the end title appears
// Easing lives only in the year(t) mapping; bubbles interpolate linearly between 5-year data points (income in log space).

let L = null;
const Y0 = 1950, Y1 = 2020, STEP = 5;
const PLOT = { x0: 300, x1: 1700, y0: 330, y1: 900 };
const INC0 = 500, OCT = 7;
// axis domain (doublings above $500, life expectancy) — rescaled in the ending
let DOM = { lo: 0, hi: 7, l0: 30, l1: 85 };
const X = (inc) => PLOT.x0 + ((Math.log2(inc / INC0) - DOM.lo) / (DOM.hi - DOM.lo)) * (PLOT.x1 - PLOT.x0);
const Yl = (life) => PLOT.y1 - ((life - DOM.l0) / (DOM.l1 - DOM.l0)) * (PLOT.y1 - PLOT.y0);

// year(t): keyframes; easing only here, never on the data
const KEYS = [[0.1, 1950, "lin"], [1.6, 1995, "lin"], [2.08, 2000, "out"], [2.5, 2000, "hold"], [3.0, 1985, "io"], [3.5, 1985, "hold"], [4.0, 2020, "in"], [4.5, 2000, "io"]];
// ONE timing table for picture and foley (EVENTS → events.json is generated from this module)
const HOLD = KEYS[2][0];                                        // time stops on 2000: the narrator steps in
export const TL = {
  axes: [0.0, 0.2], grow: [0.02, 0.3], focus: (k) => HOLD + k * 0.18,      // pointer hops to focus bubble k
  taps: [[HOLD + 0.16, 0], [HOLD + 0.34, 1], [HOLD + 0.52, 2], [3.12, 2], [3.37, 2]],   // tap rings (last two: double tap in 1985)
  rescale: [4.08, 4.6], titleOut: 4.0, end: 4.4,
};
const FOCUS_A = [[[600, 36], [900, 44], [1500, 55], [3200, 64]], [[1200, 46], [2600, 57], [6000, 68], [11000, 74]], [[900, 41], [4000, 60], [24000, 77], [42000, 81]]];
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;   // pan = (2x/W − 1) · 0.7
const panInc = (inc) => pan(300 + (Math.log2(inc / 500) / 7) * 1400);   // X() in the opening domain
const incAt = (k, yr) => { const A = [1950, 1975, 2000, 2020], j = yr > 1975 ? (yr > 2000 ? 2 : 1) : 0, u = (yr - A[j]) / (A[j + 1] - A[j]); return 2 ** ((1 - u) * Math.log2(FOCUS_A[k][j][0]) + u * Math.log2(FOCUS_A[k][j + 1][0])); };
// decade crossings of year(t), solved on the same KEYS (the odometer's tens digit lands); "io" only at its midpoint
function decadeTimes() {
  const out = [];
  for (let i = 1; i < KEYS.length; i++) {
    const [t0, y0] = KEYS[i - 1], [t1, y1, e] = KEYS[i];
    if (e === "hold") continue;
    for (let d = 1950; d <= 2020; d += 10) {
      const f = (d - y0) / (y1 - y0);
      if (!(f > 0 && f < 1)) continue;
      const u = e === "lin" ? f : e === "out" ? 1 - Math.sqrt(1 - f) : e === "in" ? Math.sqrt(f) : f === 0.5 ? 0.5 : null;
      if (u != null) out.push(t0 + u * (t1 - t0));
    }
  }
  return out;
}
export const FOLEY = [
  { t: 0.08, sfx: "whoosh", gain_db: -12 },                                               // axes shoot out
  { t: TL.grow[0] + 0.18, sfx: "pop", gain_db: -10 },                                     // 44 bubbles pop (outBack peak)
  ...decadeTimes().map((t) => ({ t, sfx: "tick", gain_db: -11, pan: pan(1040) })),         // odometer rolls a decade (−11, not −16: the race to 2020 buried them under the marimba)
  { t: HOLD, sfx: "click", gain_db: -8, pan: pan(1040) },                                  // time stops on 2000
  ...TL.taps.map(([t, k], i) => ({ t, sfx: "pop", gain_db: i < 3 ? -12 : -14, pan: panInc(incAt(k, KEYS[i < 3 ? 2 : 4][1])) })),   // pointer taps
  { t: KEYS[4][0], sfx: "swish_rev", gain_db: -8 },                                        // "wait — back to 1985" lands
  { t: KEYS[6][0], sfx: "click", gain_db: -10, pan: pan(1040) },                           // races into 2020…
  { t: KEYS[7][0], sfx: "swish_rev", gain_db: -10 },                                       // …and rewinds to 2000 while the axes zoom
  { t: TL.end + 0.2, sfx: "ding", gain_db: -8 },                                           // end title: the one hero (at −16 it sat 6 LU under the hero range)
];
function yearAt(t, lib) {
  if (t <= KEYS[0][0]) return KEYS[0][1];
  for (let i = 1; i < KEYS.length; i++) {
    const [t1, y1, e] = KEYS[i], [t0, y0] = KEYS[i - 1];
    if (t <= t1) { const u = (t - t0) / (t1 - t0); const f = e === "out" ? 1 - (1 - u) ** 2 : e === "in" ? u * u : e === "io" ? lib.ease.inOutCubic(u) : e === "hold" ? 0 : u; return lib.lerp(y0, y1, f); }
  }
  return KEYS[KEYS.length - 1][1];
}

export async function setup(ctx, tokens, lib) {
  const lifeOf = (inc, yr, j) => lib.clamp(28 + 52 / (1 + Math.exp(-(Math.log2(inc / INC0) - 2.3) * 1.15)) + (yr - Y0) * 0.07 + j, 31, 84);
  const prof = [[0.2, 1.4, 0.62], [0.0, 1.3, 0.2], [1.3, 2.8, 0.36], [2.6, 4.0, 0.42]];   // region: log2 start range, growth / decade
  const ents = [];
  for (let i = 0; i < 44; i++) {
    const r = i % 4, [a, b, g] = prof[r], h = (k) => lib.hash(17, i, k);
    const l0 = a + (b - a) * h(1), gr = g * (0.6 + 0.8 * h(2)), jl = (h(3) - 0.5) * 7, rad = 9 + 30 * h(4) * h(4);
    const pts = [];
    for (let yr = Y0; yr <= Y1; yr += STEP) {
      const l2 = Math.min(OCT - 0.2, l0 + gr * (yr - Y0) / 10 + 0.12 * lib.hashS(19, i, yr));
      const inc = INC0 * 2 ** l2;
      pts.push({ inc, life: lifeOf(inc, yr, jl + 1.2 * lib.hashS(23, i, yr)), rad: rad * Math.sqrt(1 + 0.6 * (yr - Y0) / 70) });
    }
    ents.push({ id: i, region: r, pts });
  }
  // the three narrated entities (left → right at 2000): anchors at 1950, 1975, 2000, 2020
  const focus = [
    { region: 1, a: FOCUS_A[0], rad: 44 },
    { region: 2, a: FOCUS_A[1], rad: 38 },
    { region: 0, a: FOCUS_A[2], rad: 52 },
  ].map((f, k) => {
    const anchors = [1950, 1975, 2000, 2020], pts = [];
    for (let yr = Y0; yr <= Y1; yr += STEP) {
      let j = 0; while (j < 2 && yr > anchors[j + 1]) j++;
      const u = (yr - anchors[j]) / (anchors[j + 1] - anchors[j]);
      pts.push({ inc: 2 ** lib.lerp(Math.log2(f.a[j][0]), Math.log2(f.a[j + 1][0]), u), life: lib.lerp(f.a[j][1], f.a[j + 1][1], u), rad: f.rad * Math.sqrt(1 + 0.5 * (yr - Y0) / 70) });
    }
    return { id: 100 + k, region: f.region, pts, focus: k };
  });
  L = { ents: [...ents, ...focus], focus };
  lib.setFont(ctx, tokens, "display", 420, { weight: 100 });
  L.digitW = ctx.measureText("0").width;
}

function at(e, yr, lib) {                                      // linear interpolation between 5-year data points
  const f = (yr - Y0) / STEP, i = Math.min(e.pts.length - 2, Math.max(0, Math.floor(f))), u = lib.clamp(f - i);
  const a = e.pts[i], b = e.pts[i + 1];
  return { x: X(2 ** lib.lerp(Math.log2(a.inc), Math.log2(b.inc), u)), y: Yl(lib.lerp(a.life, b.life, u)), r: lib.lerp(a.rad, b.rad, u) };
}

export function renderAt(t, ctx, tokens, lib) {
  const rs = lib.tween(t, ...TL.rescale, lib.ease.inOutCubic);
  DOM = { lo: lib.lerp(0, 0.8, rs), hi: lib.lerp(7, 6.1, rs), l0: lib.lerp(30, 40, rs), l1: 85 };
  chart(ctx, t, yearAt(t, lib), tokens, lib, rs);
}

function chart(ctx, t, yr, tokens, lib, rs) {
  const { W, H, seg, tween, ease } = lib;
  const P = (k) => lib.color(tokens, k);
  const INK = P("fg"), AX = P("extra.4"), REG = [P("accent"), P("extra.0"), P("extra.1"), P("extra.2")];
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);

  // ── year watermark (odometer; rolls both ways)
  const wa = seg(t, 0.02, 0.2);
  if (wa > 0) {
    ctx.save(); ctx.globalAlpha = wa; ctx.fillStyle = P("extra.3");
    lib.setFont(ctx, tokens, "display", 420, { weight: 100 });
    ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
    const dw = L.digitW, x0 = 1040 - 2 * dw, base = 830, hgt = 360, fy = Math.floor(yr), roll = lib.smoothstep(0.55, 1, yr - fy);
    ctx.beginPath(); ctx.rect(x0 - 10, base - hgt, 4 * dw + 20, hgt + 40); ctx.clip();
    for (let k = 0; k < 4; k++) {
      const p = 10 ** (3 - k), d = Math.floor(fy / p) % 10, rolls = (fy % p) === p - 1 && fy < 2020 ? roll : 0, cx = x0 + (k + 0.5) * dw;
      ctx.fillText(String(d), cx, base - rolls * hgt);
      if (rolls > 0) ctx.fillText(String((d + 1) % 10), cx, base + (1 - rolls) * hgt);
    }
    ctx.restore();
  }

  // ── axes shoot out on frame 1–6, ticks re-labelled as the domain rescales
  ctx.save(); ctx.strokeStyle = AX; ctx.lineWidth = 3;
  lib.strokePartial(ctx, [[PLOT.x0, PLOT.y1], [PLOT.x1, PLOT.y1]], tween(t, ...TL.axes, ease.outExpo));
  lib.strokePartial(ctx, [[PLOT.x0, PLOT.y1], [PLOT.x0, PLOT.y0]], tween(t, TL.axes[0] + 0.03, TL.axes[1] + 0.03, ease.outExpo));
  lib.setFont(ctx, tokens, "body", 36, { weight: 500 }); ctx.fillStyle = AX; ctx.globalAlpha = seg(t, 0.15, 0.4);
  const names = ["$500", "1k", "2k", "4k", "8k", "16k", "32k", "64k"];
  for (let k = 0; k <= 7; k++) { const x = X(INC0 * 2 ** k); if (x < PLOT.x0 - 2 || x > PLOT.x1 + 2) continue; ctx.fillRect(x - 1, PLOT.y1, 2, 10); lib.drawText(ctx, names[k], x, PLOT.y1 + 48, { align: "center" }); }
  for (const v of [40, 50, 60, 70, 80]) { const y = Yl(v); if (y > PLOT.y1 + 1 || y < PLOT.y0 - 1 || (v % 20 && rs < 0.5)) continue; ctx.fillRect(PLOT.x0 - 10, y - 1, 10, 2); lib.drawText(ctx, String(v), PLOT.x0 - 20, y + 12, { align: "right" }); }
  lib.setFont(ctx, tokens, "body", 32, { weight: 500 });
  lib.drawText(ctx, "Income per person, log scale →", PLOT.x1, PLOT.y1 + 100, { align: "right" });
  lib.drawText(ctx, "↑ Life expectancy, years", PLOT.x0 - 20, PLOT.y0 - 22);
  ctx.restore();

  // ── bubbles: sorted big → small; clipped to the plot while the axes rescale
  const grow = tween(t, ...TL.grow, ease.outBack), dim = lib.lerp(1, 0.2, tween(t, HOLD, HOLD + 0.27, ease.outCubic)) * (1 - 0.5 * rs);
  const list = L.ents.map((e) => ({ e, ...at(e, yr, lib) })).sort((a, b) => b.r - a.r || a.e.id - b.e.id);
  ctx.save(); ctx.beginPath(); ctx.rect(PLOT.x0 + 2, PLOT.y0 - 60, PLOT.x1 - PLOT.x0 + 60, PLOT.y1 - PLOT.y0 + 58); ctx.clip();
  for (const f of L.focus) {                                   // trails (retract when time rewinds)
    const ta = seg(t, TL.focus(f.focus) + 0.07, TL.focus(f.focus) + 0.27);
    if (ta <= 0) continue;
    ctx.save(); ctx.fillStyle = REG[f.region]; ctx.globalAlpha = 0.5 * ta;
    for (let y = Y0; y <= Math.floor(yr); y += STEP) { const p = at(f, y, lib); ctx.beginPath(); ctx.arc(p.x, p.y, 6, 0, lib.TAU); ctx.fill(); }
    ctx.restore();
  }
  for (const b of list) {
    const isF = b.e.focus != null, r = b.r * grow;
    if (r <= 0.5) continue;
    ctx.save(); ctx.globalAlpha = isF ? 0.92 : 0.85 * dim;
    ctx.fillStyle = REG[b.e.region]; ctx.beginPath(); ctx.arc(b.x, b.y, r, 0, lib.TAU); ctx.fill();
    ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 2; ctx.stroke();
    if (isF && t > HOLD) { ctx.globalAlpha = seg(t, TL.focus(b.e.focus) + 0.02, TL.focus(b.e.focus) + 0.16); ctx.strokeStyle = INK; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(b.x, b.y, r + 5, 0, lib.TAU); ctx.stroke(); }
    ctx.restore();
  }
  ctx.restore();

  // ── direct labels for the three narrated bubbles
  L.focus.forEach((f, k) => {
    const a = seg(t, TL.focus(k) + 0.07, TL.focus(k) + 0.22);
    if (a <= 0) return;
    const p = at(f, yr, lib);
    ctx.save(); ctx.globalAlpha = a;
    const lx = p.x - p.r - 18, ly = p.y - p.r - 24;
    lib.setFont(ctx, tokens, "zh", 58, { weight: 600 }); ctx.fillStyle = INK;
    lib.drawText(ctx, lib.MOTIF[k].zh, lx, ly, { align: "right", tracking: 0.06 * 58 });
    lib.setFont(ctx, tokens, "body", 32, { weight: 600 }); ctx.fillStyle = REG[f.region];
    lib.drawText(ctx, lib.MOTIF[k].en, lx, ly + 40, { align: "right" });
    ctx.restore();
  });

  // ── the narrator's pointer stick: reaches in from the lower right, taps each focus bubble, rides the rewind
  const pin = tween(t, 2.05, 2.22, ease.outCubic), pout = tween(t, 3.55, 3.85, ease.inCubic);
  if (pin > 0 && pout < 1) {
    const hop = (k) => tween(t, TL.focus(k), TL.focus(k) + 0.16, ease.inOutCubic);
    const tg = [0, 1, 2].map((k) => { const p = at(L.focus[k], yr, lib); return [p.x + (p.r + 12) * 0.7, p.y + (p.r + 12) * 0.7]; });
    let tip = tg[0];
    for (let k = 1; k < 3; k++) tip = [lib.lerp(tip[0], tg[k][0], hop(k)), lib.lerp(tip[1], tg[k][1], hop(k))];
    const base = [1900, 1150], s = pin * (1 - pout);
    const tap = 10 * TL.taps.slice(3).reduce((s, [a]) => s + Math.max(0, Math.sin(Math.PI * seg(t, a - 0.12, a + 0.06))), 0);
    const dx = tip[0] - base[0], dy = tip[1] - base[1], len = Math.hypot(dx, dy), ux = dx / len, uy = dy / len;
    const tx = lib.lerp(base[0], tip[0], s) - ux * tap, ty = lib.lerp(base[1], tip[1], s) - uy * tap, nx = -uy, ny = ux;
    ctx.save();                                                // a tapered wooden stick with a brass tip
    ctx.fillStyle = "#6B4A2B"; ctx.beginPath(); ctx.moveTo(base[0] + nx * 11, base[1] + ny * 11); ctx.lineTo(tx + nx * 3.5, ty + ny * 3.5); ctx.lineTo(tx - nx * 3.5, ty - ny * 3.5); ctx.lineTo(base[0] - nx * 11, base[1] - ny * 11); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = "rgba(255,235,200,0.55)"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(base[0] + nx * 5, base[1] + ny * 5); ctx.lineTo(tx + nx * 1.5, ty + ny * 1.5); ctx.stroke();
    ctx.fillStyle = "#C9A15A"; ctx.beginPath(); ctx.arc(tx, ty, 8, 0, lib.TAU); ctx.fill(); ctx.strokeStyle = INK; ctx.lineWidth = 2; ctx.stroke();
    ctx.restore();
    for (const [a0, k] of TL.taps) {                                                        // tap rings
      const u = seg(t, a0, a0 + 0.35); if (u <= 0 || u >= 1) continue;
      const p = at(L.focus[k], yr, lib);
      ctx.save(); ctx.strokeStyle = INK; ctx.globalAlpha = 0.6 * (1 - u); ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(p.x, p.y, p.r + 10 + 40 * u, 0, lib.TAU); ctx.stroke(); ctx.restore();
    }
  }

  // ── title (fades as the ending takes over) and the end title
  const out = tween(t, TL.titleOut, TL.titleOut + 0.3, ease.inCubic);
  ctx.save(); ctx.globalAlpha = 1 - out;
  lib.setFont(ctx, tokens, "display", 78, { weight: 600 }); ctx.fillStyle = INK;
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: 192, y: 170, tracking: -0.01 * 78 });
  let w = -1, prev = " ";
  const wi = lay.glyphs.map((g) => { if (prev === " " && g.ch !== " ") w++; prev = g.ch; return w; });
  lib.drawGlyphs(ctx, lay, (g, i) => { const a = tween(t, 0.85 + wi[i] * 0.09, 1.2 + wi[i] * 0.09, ease.outCubic); return a <= 0 ? null : { alpha: a, dy: (1 - a) * 14 }; });
  lib.setFont(ctx, tokens, "zh", 60, { weight: 600 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: 192, y: 252, tracking: 0.04 * 60 });
  lib.drawGlyphs(ctx, zl, (g, i) => { const a = tween(t, 1.3 + i * 0.06, 1.6 + i * 0.06, ease.outCubic); return a <= 0 ? null : { alpha: a, dy: (1 - a) * 10 }; });
  ctx.restore();
  const ea = tween(t, TL.end, TL.end + 0.35, ease.outCubic);
  if (ea > 0) {
    ctx.save(); ctx.globalAlpha = ea; ctx.fillStyle = INK;
    lib.setFont(ctx, tokens, "display", 96, { weight: 600 }); lib.drawText(ctx, "Bubble Chart Story", 192, 190 + (1 - ea) * 16, { tracking: -0.01 * 96 });
    lib.setFont(ctx, tokens, "zh", 60, { weight: 600 }); ctx.fillStyle = P("accent"); lib.drawText(ctx, "气泡图现场讲", 192, 272 + (1 - ea) * 16, { tracking: 0.08 * 60 });
    ctx.restore();
  }

  // source line
  ctx.save(); lib.setFont(ctx, tokens, "body", 28, { weight: 400 }); ctx.fillStyle = AX; ctx.globalAlpha = 0.7 * seg(t, 0.3, 0.6);
  lib.drawText(ctx, "Illustrative data · area = population · colour = region", 192, PLOT.y1 + 100); ctx.restore();
}
