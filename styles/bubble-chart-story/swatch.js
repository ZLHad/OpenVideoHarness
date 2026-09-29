// bubble-chart-story swatch: one bubble chart, time performed by a narrator. ILLUSTRATIVE DATA (fictional entities).
//   0.0–0.8  axes, log ticks and the pale year watermark come in; bubbles grow in at 1950
//   0.25–2.1 time races (30 years/s) and eases out into 2000; the year rolls like an odometer
//   0.8–2.6  title word by word, Chinese character by character
//   2.1–3.6  time holds: other bubbles dim to 20 %, a pointer (the narrator) visits outline → storyboard → draft,
//            each focus bubble keeps a dotted trail and gets a direct label
//   3.6–4.45 time resumes and scrubs to 2020 (signature transition, part 1)
//   4.45–4.95 the draft bubble opens into the end frame (iris from the bubble)
// Easing lives only in the year(t) mapping; bubbles interpolate linearly between 5-year data points (income in log space).

let L = null;
const Y0 = 1950, Y1 = 2020, STEP = 5;
const PLOT = { x0: 300, x1: 1700, y0: 330, y1: 900 };
const INC0 = 500, OCT = 7;                                    // x axis: $500 … $64k, one tick per doubling
const LIFE0 = 30, LIFE1 = 85;

const X = (inc) => PLOT.x0 + (Math.log2(inc / INC0) / OCT) * (PLOT.x1 - PLOT.x0);
const Yl = (life) => PLOT.y1 - ((life - LIFE0) / (LIFE1 - LIFE0)) * (PLOT.y1 - PLOT.y0);

function yearAt(t, lib) {
  if (t < 0.25) return Y0;
  if (t < 1.75) return lib.lerp(1950, 1995, (t - 0.25) / 1.5);                       // 30 y/s
  if (t < 2.083) { const u = (t - 1.75) / 0.333; return 1995 + 5 * (1 - (1 - u) * (1 - u)); }   // ease out (matching speed)
  if (t < 3.6) return 2000;                                                           // the narrator holds time
  if (t < 3.933) { const u = (t - 3.6) / 0.333; return 2000 + 5 * u * u; }                       // ease in
  if (t < 4.433) return lib.lerp(2005, 2020, (t - 3.933) / 0.5);
  return 2020;
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
    { region: 1, a: [[600, 36], [900, 44], [1500, 55], [3200, 64]], rad: 44 },
    { region: 2, a: [[1200, 46], [2600, 57], [6000, 68], [11000, 74]], rad: 38 },
    { region: 0, a: [[900, 41], [4000, 60], [24000, 77], [42000, 81]], rad: 52 },
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
  const yr = yearAt(t, lib);
  const f3 = at(L.focus[2], yr, lib);
  lib.iris(ctx, lib.seg(t, 4.45, 4.95), (x) => chart(x, t, yr, tokens, lib), (x) => end(x, t, tokens, lib),
    { cx: f3.x, cy: f3.y, mode: "open", ease: lib.ease.inOutCubic });
}

function chart(ctx, t, yr, tokens, lib) {
  const { W, H, seg, tween, ease } = lib;
  const P = (k) => lib.color(tokens, k);
  const INK = P("fg"), AX = P("extra.4"), REG = [P("accent"), P("extra.0"), P("extra.1"), P("extra.2")];
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);

  // ── year watermark (odometer)
  const wa = seg(t, 0.1, 0.6);
  if (wa > 0) {
    ctx.save(); ctx.globalAlpha = wa; ctx.fillStyle = P("extra.3");
    lib.setFont(ctx, tokens, "display", 420, { weight: 100 });
    ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";
    const dw = L.digitW, x0 = 1040 - 2 * dw, base = 830, hgt = 360, fy = Math.floor(yr), roll = lib.smoothstep(0.7, 1, yr - fy);
    ctx.beginPath(); ctx.rect(x0 - 10, base - hgt, 4 * dw + 20, hgt + 40); ctx.clip();
    for (let k = 0; k < 4; k++) {
      const p = 10 ** (3 - k), d = Math.floor(fy / p) % 10, rolls = (fy % p) === p - 1 && fy < 2020 ? roll : 0;
      const cx = x0 + (k + 0.5) * dw;
      ctx.fillText(String(d), cx, base - rolls * hgt);
      if (rolls > 0) ctx.fillText(String((d + 1) % 10), cx, base + (1 - rolls) * hgt);
    }
    ctx.restore();
  }

  // ── axes + log ticks (one per doubling) + plain-language titles
  ctx.save(); ctx.strokeStyle = AX; ctx.lineWidth = 2;
  lib.strokePartial(ctx, [[PLOT.x0, PLOT.y1], [PLOT.x1, PLOT.y1]], tween(t, 0.05, 0.5, ease.outCubic));
  lib.strokePartial(ctx, [[PLOT.x0, PLOT.y1], [PLOT.x0, PLOT.y0]], tween(t, 0.1, 0.55, ease.outCubic));
  lib.setFont(ctx, tokens, "body", 24, { weight: 500 }); ctx.fillStyle = AX; ctx.globalAlpha = seg(t, 0.3, 0.7);
  ["$500", "1k", "2k", "4k", "8k", "16k", "32k", "64k"].forEach((s, k) => {
    const x = PLOT.x0 + k * (PLOT.x1 - PLOT.x0) / OCT;
    ctx.fillRect(x - 1, PLOT.y1, 2, 10); lib.drawText(ctx, s, x, PLOT.y1 + 40, { align: "center" });
  });
  [40, 60, 80].forEach((v) => { const y = Yl(v); ctx.fillRect(PLOT.x0 - 10, y - 1, 10, 2); lib.drawText(ctx, String(v), PLOT.x0 - 20, y + 9, { align: "right" }); });
  lib.drawText(ctx, "Income per person, log scale →", PLOT.x1, PLOT.y1 + 82, { align: "right" });
  lib.drawText(ctx, "↑ Life expectancy, years", PLOT.x0 - 20, PLOT.y0 - 22);
  ctx.restore();

  // ── bubbles: sorted big → small; others dim to 20 % while the narrator holds time
  const grow = tween(t, 0.2, 0.7, ease.outCubic), dim = lib.lerp(1, 0.2, tween(t, 2.08, 2.4, ease.outCubic));
  const list = L.ents.map((e) => ({ e, ...at(e, yr, lib) })).sort((a, b) => b.r - a.r || a.e.id - b.e.id);
  // trails first (focus only), then bubbles
  for (const f of L.focus) {
    const ta = seg(t, 2.2 + f.focus * 0.3, 2.45 + f.focus * 0.3);
    if (ta <= 0) continue;
    ctx.save(); ctx.fillStyle = REG[f.region]; ctx.globalAlpha = 0.45 * ta;
    for (let y = Y0; y <= Math.floor(yr); y += STEP) { const p = at(f, y, lib); ctx.beginPath(); ctx.arc(p.x, p.y, 5, 0, lib.TAU); ctx.fill(); }
    ctx.restore();
  }
  for (const b of list) {
    const isF = b.e.focus != null, r = b.r * grow;
    if (r <= 0.5) continue;
    ctx.save(); ctx.globalAlpha = isF ? 0.92 : 0.85 * dim;
    ctx.fillStyle = REG[b.e.region]; ctx.beginPath(); ctx.arc(b.x, b.y, r, 0, lib.TAU); ctx.fill();
    ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 2; ctx.stroke();
    if (isF && t > 2.1) { ctx.globalAlpha = seg(t, 2.1 + b.e.focus * 0.3, 2.28 + b.e.focus * 0.3); ctx.strokeStyle = INK; ctx.lineWidth = 3.5; ctx.beginPath(); ctx.arc(b.x, b.y, r + 4, 0, lib.TAU); ctx.stroke(); }
    ctx.restore();
  }

  // ── direct labels for the three narrated bubbles
  L.focus.forEach((f, k) => {
    const a = seg(t, 2.2 + k * 0.3, 2.38 + k * 0.3);
    if (a <= 0) return;
    const p = at(f, yr, lib);
    ctx.save(); ctx.globalAlpha = a;
    const lx = p.x - p.r - 18, ly = p.y - p.r - 22;
    lib.setFont(ctx, tokens, "zh", 50, { weight: 600 }); ctx.fillStyle = INK;
    lib.drawText(ctx, lib.MOTIF[k].zh, lx, ly, { align: "right", tracking: 0.06 * 50 });
    lib.setFont(ctx, tokens, "body", 30, { weight: 600 }); ctx.fillStyle = lib.color(tokens, k === 2 ? "accent" : k === 1 ? "extra.1" : "extra.0");
    lib.drawText(ctx, lib.MOTIF[k].en, lx, ly + 38, { align: "right" });
    ctx.restore();
  });

  // ── the narrator's pointer: reaches in from the lower right, hops between the three focus bubbles
  const pin = tween(t, 2.1, 2.35, ease.outCubic), pout = tween(t, 3.62, 3.9, ease.inCubic);
  if (pin > 0 && pout < 1) {
    const hop = (k) => tween(t, 2.1 + k * 0.3, 2.36 + k * 0.3, ease.inOutCubic);
    const tg = [0, 1, 2].map((k) => { const p = at(L.focus[k], yr, lib); return [p.x + (p.r + 10) * 0.7, p.y + (p.r + 10) * 0.7]; });
    let tip = tg[0];
    for (let k = 1; k < 3; k++) tip = [lib.lerp(tip[0], tg[k][0], hop(k)), lib.lerp(tip[1], tg[k][1], hop(k))];
    const base = [1860, 1130], s = pin * (1 - pout);
    const tx = lib.lerp(base[0], tip[0], s), ty = lib.lerp(base[1], tip[1], s);
    ctx.save(); ctx.strokeStyle = INK; ctx.lineWidth = 5; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(base[0], base[1]); ctx.lineTo(tx, ty); ctx.stroke();
    ctx.fillStyle = INK; ctx.beginPath(); ctx.arc(tx, ty, 9, 0, lib.TAU); ctx.fill(); ctx.restore();
  }

  // ── title, top-left: word by word; Chinese character by character
  lib.setFont(ctx, tokens, "display", 78, { weight: 600 }); ctx.fillStyle = INK;
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: 192, y: 170, tracking: -0.01 * 78 });
  let w = -1, prev = " ";
  const wi = lay.glyphs.map((g) => { if (prev === " " && g.ch !== " ") w++; prev = g.ch; return w; });
  lib.drawGlyphs(ctx, lay, (g, i) => { const a = tween(t, 0.85 + wi[i] * 0.09, 1.2 + wi[i] * 0.09, ease.outCubic); return a <= 0 ? null : { alpha: a, dy: (1 - a) * 14 }; });
  lib.setFont(ctx, tokens, "zh", 54, { weight: 600 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: 192, y: 248, tracking: 0.04 * 54 });
  lib.drawGlyphs(ctx, zl, (g, i) => { const a = tween(t, 1.3 + i * 0.06, 1.6 + i * 0.06, ease.outCubic); return a <= 0 ? null : { alpha: a, dy: (1 - a) * 10 }; });

  // source line
  ctx.save(); lib.setFont(ctx, tokens, "body", 24, { weight: 400 }); ctx.fillStyle = AX; ctx.globalAlpha = 0.6 * seg(t, 0.5, 0.9);
  lib.drawText(ctx, "Illustrative data · bubble area = population · colour = region", 192, 1010); ctx.restore();
}

function end(ctx, t, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  ctx.fillStyle = P("accent"); ctx.fillRect(0, 0, W, H);
  const a = lib.tween(t, 4.62, 4.9, lib.ease.outCubic);
  ctx.save(); ctx.globalAlpha = a;
  lib.setFont(ctx, tokens, "display", 116, { weight: 600 }); ctx.fillStyle = P("bg");
  lib.drawText(ctx, "Bubble Chart Story", W / 2, 560 + (1 - a) * 16, { align: "center", tracking: -0.01 * 116 });
  lib.setFont(ctx, tokens, "zh", 58, { weight: 600 });
  lib.drawText(ctx, "气泡图现场讲", W / 2, 660 + (1 - a) * 16, { align: "center", tracking: 0.08 * 58 });
  ctx.restore();
}
