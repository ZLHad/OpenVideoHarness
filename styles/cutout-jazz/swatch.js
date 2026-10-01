// cutout-jazz swatch — mid-century cut-paper title grammar (150 BPM: 0.8 / 2.0 / 4.0 s fall on beats).
//   0.0–0.8  black ground: on the brass stab four cream bars cut in (0.1 s, ≥ 20 % of the frame), a second group on
//            0.5 (only the bass under it: the breath before the title)
//   0.8–2.0  hard cut on the downbeat to an ochre ground and a full-bleed black band across the middle (the title page,
//            centred). Cream paper letters are slapped onto the band two per step (on twos); the Chinese line follows
//            on a cream strip. On 2.0 the whole title block slides down to the bottom third and stops dead
//   2.0–4.0  the motif is ONE convergence, read left to right along the 30° diagonal: loose paper strips (outline) →
//            a disc still in five slices (storyboard) → the single vermilion disc (draft). Landings 2.2 / 2.4 / 2.6.
//            Then every beat the pieces gather: 2.8 strips advance and close up, slices close up; 3.2 a black bar
//            wipes the ground to cream; 3.6 second gather; 3.8 the slices close into one disc
//   4.0–5.0  the scissors: the whole frame is cut along the 30° diagonal into six equal strips (scissor edges, drop
//            shadows) that slide off along the diagonal, alternately up-right and down-left; the vermilion disc stays
//            where it is (match) on the black end card, and the name is slapped in beside it
// Paper pieces step on twos (lib.step(t, 15)); texture and grain stay at full rate. Edge noise is computed once per
// piece in its local space and cached (no crawling edges).

const BPM = 150, BEAT = 60 / BPM, E16 = BEAT / 4, STEP = 2 / 30;
// ── timing constants (picture and foley share them) ──
const T_BARS = [0.1, 0.5], T_CUT = 0.8, T_LET0 = T_CUT + STEP, T_ZH = 1.6, T_DOWN = 2.0;
const T_OUT = 2.2, T_SB = 2.4, T_DR = 2.6, T_G1 = 2.8, T_WIPE = 3.2, T_G2 = 3.6, T_G3 = 3.8, T_SCISSORS = 4.0;
const T_END = [4.4, 4.4 + E16, 4.4 + 2 * E16];
const ANG = Math.PI / 6, DX = Math.cos(ANG), DY = -Math.sin(ANG), NX = Math.sin(ANG), NY = Math.cos(ANG);   // the one diagonal
// ── layout ──
const BAND_H = 164, BAND_Y0 = 388, BAND_Y1 = 752;           // title band: centred page → bottom third
const OUT = { x: 392, y: 368 }, SB = { x: 922, y: 368, r: 168 }, DR = { x: 1462, y: 364, r: 206 };
const LABEL_EN = 630, LABEL_ZH = 692;
const STRIPS = [[300, -30, -2], [380, 24, -1], [330, -12, 0], [250, 34, 1], [190, -20, 2]];   // outline: length, slide, row

const px = (x) => Math.round((x / 960 - 1) * 100) / 100;
export const FOLEY = [
  { t: T_BARS[0], sfx: "pop", gain_db: -4, pan: px(400) }, { t: T_BARS[1], sfx: "pop", gain_db: -4, pan: px(1400) },   // bars land
  ...[0, 2, 4, 6, 8].map((m) => ({ t: T_LET0 + m * STEP, sfx: "pop", gain_db: -12, pan: px(420 + m * 135) })),        // letter slaps
  { t: T_ZH, sfx: "paper", gain_db: -14, pan: px(760), dur: 0.25 },                                                                // cream strip
  { t: T_DOWN, sfx: "click", gain_db: -8, pan: 0 },                                                                      // block lands low
  { t: T_OUT, sfx: "click", gain_db: -6, pan: px(OUT.x) }, { t: T_SB, sfx: "pop", gain_db: -8, pan: px(SB.x) },
  { t: T_DR, sfx: "pop", gain_db: -4, pan: px(DR.x) },                                                                   // the disc drops
  { t: T_G1, sfx: "tick", gain_db: -10, pan: px(600) }, { t: T_WIPE, sfx: "paper", gain_db: -10, pan: 0, dur: 0.2, bright: 0.3 },
  { t: T_G2, sfx: "tick", gain_db: -10, pan: px(600) }, { t: T_G3, sfx: "click", gain_db: -10, pan: px(SB.x) },
  { t: T_SCISSORS, sfx: "shutter", gain_db: -4, pan: 0, variant: 0 }, { t: T_SCISSORS + 0.25, sfx: "paper", gain_db: -12, pan: 0, dur: 0.6, dir: "down" },
  { t: T_END[0], sfx: "pop", gain_db: -6, pan: px(400) }, { t: T_END[1], sfx: "pop", gain_db: -8, pan: px(400) },
];
const CUT = new Map();          // cut polygons in local space, keyed by id (pure data, identical per worker)
let L = null;

export const fonts = ["Futura", "PingFang SC"];

export async function setup(ctx, tokens, lib) {
  const disp = (x, s) => lib.setFont(x, tokens, "display", s, { weight: 800, stretch: "condensed" });
  const text = lib.TITLE_EN.toUpperCase();
  const size = lib.fitText(ctx, text, 1420, (s) => disp(ctx, s), { min: 120, max: 168, tracking: 0.03 });
  disp(ctx, size);
  const cap = ctx.measureText("E").actualBoundingBoxAscent, base = Math.round((BAND_H + cap) / 2);   // letters centred in the band
  const lay = lib.layoutText(ctx, text, { x: lib.W / 2, y: 0, align: "center", tracking: size * 0.03 });
  // every letter is its own re-cut cream paper piece: edges roughened ONCE here, then only moved
  const glyphs = []; let k = 0;
  for (const g of lay.glyphs) {
    if (g.ch === " ") continue;
    const pad = 24, w = Math.ceil(g.w + pad * 2), h = Math.ceil(size * 1.15), oy = h - pad - size * 0.12;
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const paint = (x) => { disp(x, size); x.textAlign = "center"; x.textBaseline = "alphabetic"; x.fillStyle = "#F4EEDF"; x.fillText(g.ch, w / 2, oy); };
    lib.roughen(c.getContext("2d"), paint, { amount: 3.2, freq: 0.085, seed: 17 + k * 7 });
    glyphs.push({ k, cx: g.cx, img: c, w, oy }); k++;
  }
  lib.setFont(ctx, tokens, "zh", 58, { weight: 600 });
  const zhW = Math.round(ctx.measureText(lib.TITLE_ZH).width + 58 * 0.12 * 8 + 76);
  L = { size, base, glyphs, zhW };
}

// ───────── cut-paper helpers ─────────
function scissor(lib, id, base, amp, step = 10) {             // resample a closed polygon, push each point along the normal
  const key = `p${id}`; if (CUT.has(key)) return CUT.get(key);
  const pts = []; let k = 0;
  for (let e = 0; e < base.length; e++) {
    const [x0, y0] = base[e], [x1, y1] = base[(e + 1) % base.length], len = Math.hypot(x1 - x0, y1 - y0);
    if (len < 0.01) continue;
    const n = Math.max(1, Math.round(len / step)), nx = (y1 - y0) / len, ny = -(x1 - x0) / len;
    for (let s = 0; s < n; s++) {
      const u = s / n, notch = lib.hash(id, k, 9) < 0.025 ? -1.6 : 0, d = s === 0 ? 0 : amp * lib.noise1(k * 0.33, id) + notch;
      pts.push([x0 + (x1 - x0) * u + nx * d, y0 + (y1 - y0) * u + ny * d]); k++;
    }
  }
  CUT.set(key, pts); return pts;
}
const rectBase = (w, h) => [[0, 0], [w, 0], [w, h], [0, h]];
function cutCircle(lib, id, r, amp = 1.9) {
  const key = `c${id}:${r}`; if (CUT.has(key)) return CUT.get(key);
  const n = Math.round(lib.TAU * r / 9), pts = [];
  for (let i = 0; i < n; i++) { const a = i / n * lib.TAU, rr = r + amp * lib.noise1(i * 0.3, id); pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
  CUT.set(key, pts); return pts;
}
function slicePoly(lib, id, r, ya, yb) {                       // one horizontal slice of a disc (centre-relative)
  const base = [], n = 14;
  for (let i = 0; i <= n; i++) { const y = lib.lerp(ya, yb, i / n); base.push([-Math.sqrt(Math.max(0, r * r - y * y)), y]); }
  for (let i = n; i >= 0; i--) { const y = lib.lerp(ya, yb, i / n); base.push([Math.sqrt(Math.max(0, r * r - y * y)), y]); }
  return scissor(lib, id, base, 1.5, 9);
}
/** A paper piece: shadow + ground-colour gap first, then the flat ink on top. lift 0..1 = how far off the page. */
function piece(ctx, pts, x, y, fill, gap, { rot = 0, s = 1, lift = 0 } = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  ctx.beginPath(); pts.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py))); ctx.closePath();
  ctx.shadowColor = "rgba(24,16,8,0.30)"; ctx.shadowOffsetX = 3 + 7 * lift; ctx.shadowOffsetY = 4 + 9 * lift; ctx.shadowBlur = 4 + 10 * lift;
  ctx.fillStyle = gap; ctx.strokeStyle = gap; ctx.lineWidth = 4; ctx.lineJoin = "round"; ctx.fill(); ctx.stroke();
  ctx.shadowColor = "transparent"; ctx.fillStyle = fill; ctx.fill();
  ctx.restore();
}
/** Slide on twos: -1 before the move starts, then eased 0→1 across `frames` output frames, landing on tLand, stops dead. */
function slide(lib, t, tLand, frames, e) {
  const ts = lib.step(t, 15), t0 = tLand - frames / 30;
  if (ts < t0) return -1;
  return e(lib.seg(ts, t0, tLand));
}
const E_ = (lib, tokens) => lib.easeOf(tokens.ease.enter);
const gathered = (lib, t, E) => [T_G1, T_G2].reduce((a, tb) => a + E(lib.seg(lib.step(t, 15), tb - 4 / 30, tb)), 0);   // 0 → 2

// ───────── frame ─────────
export function renderAt(t, ctx, tokens, lib) {
  if (t < T_CUT) opening(ctx, t, tokens, lib);
  else if (t < T_SCISSORS) main(ctx, t, tokens, lib);
  else {
    const A = lib.offscreen("cj_main", (x) => main(x, T_SCISSORS - 0.001, tokens, lib));
    end(ctx, t, tokens, lib);
    scissors(ctx, t, tokens, lib, A);
  }
  ctx.save(); ctx.globalCompositeOperation = "multiply";
  lib.paper(ctx, { tone: "#FFFBF2", amount: 1, blotch: 0.07, tooth: 0.03, fiber: 0.9, seed: 21 });
  ctx.restore();
  lib.grain(ctx, t, { amount: 0.05, fps: 12, seed: 5 });
}

function opening(ctx, t, tokens, lib) {               // black ground; cream bars cut in on the 0.1 and 0.5 hits
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  ctx.fillStyle = C("fg"); ctx.fillRect(0, 0, W, H);
  const group = (bars, t0, id) => bars.forEach(([x, y, w, h], j) => {
    const u = slide(lib, t, t0 + j * STEP, 4, E_(lib, tokens)); if (u < 0) return;
    piece(ctx, scissor(lib, id + j, rectBase(w, h), 1.7), x, y - (1 - u) * 160, "#F4EEDF", C("fg"));
  });
  group([[150, 60, 150, 960], [340, 160, 110, 860], [500, 40, 190, 900], [742, 220, 92, 700]], T_BARS[0] - 0, 300);   // ≥ 20 % of the frame
  group([[1120, 120, 76, 840], [1250, 40, 160, 960], [1462, 180, 104, 800], [1620, 90, 128, 900]], T_BARS[1], 400);
}

function main(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), E = E_(lib, tokens), { W, H } = lib, ts = lib.step(t, 15);
  // ground: ochre from the cut; a black bar wipes it to cream on 3.2 (on twos)
  const ochre = C("extra.0"), cream = C("bg");
  ctx.fillStyle = ochre; ctx.fillRect(0, 0, W, H);
  const wu = lib.seg(ts, T_WIPE - 4 / 30, T_WIPE);
  if (wu > 0) {
    const bx = lib.lerp(-260, W, lib.ease.inOutCubic(wu));
    ctx.fillStyle = cream; ctx.fillRect(0, 0, bx, H);
    if (wu < 1) piece(ctx, scissor(lib, 60, rectBase(260, H + 40), 1.7), bx, -20, C("fg"), C("fg"));
  }
  const ground = wu >= 1 ? cream : ochre;
  motif(ctx, t, tokens, lib, ground);
  title(ctx, t, tokens, lib, ground);
}

function title(ctx, t, tokens, lib, ground) {
  const C = (k) => lib.color(tokens, k), E = E_(lib, tokens), { W } = lib, ts = lib.step(t, 15);
  const mv = Math.max(0, slide(lib, t, T_DOWN, 6, E)), y0 = lib.lerp(BAND_Y0, BAND_Y1, mv);   // 2.0: the block drops
  // the band: full bleed, there on the cut
  piece(ctx, scissor(lib, 1, rectBase(W + 80, BAND_H), 1.7), -40, y0, C("fg"), ground);
  // letters: two per step from the first step after the cut, slapped (lifted & big two steps before, flat on landing)
  for (const g of L.glyphs) {
    const tk = T_LET0 + Math.floor(g.k / 2) * STEP;
    if (ts < tk - 2 * STEP - 1e-6) continue;
    const ph = ts >= tk - 1e-6 ? 0 : ts >= tk - STEP - 1e-6 ? 1 : 2;
    const s = [1, 1.08, 1.22][ph], dy = [0, -12, -34][ph], lift = [0, 0.5, 1][ph];
    const rot = lib.hashS(7, g.k) * 0.8 * Math.PI / 180, jy = lib.hashS(8, g.k) * 2;
    ctx.save(); ctx.translate(g.cx, y0 + L.base + jy + dy); ctx.rotate(rot); ctx.scale(s, s);
    ctx.shadowColor = "rgba(0,0,0,0.55)"; ctx.shadowOffsetX = 3 + 7 * lift; ctx.shadowOffsetY = 4 + 9 * lift; ctx.shadowBlur = 4 + 10 * lift;
    ctx.drawImage(g.img, -g.w / 2, -g.oy); ctx.restore();
  }
  // Chinese: black on a cream strip under the band, wiped in from the left on twos
  const zw = L.zhW, zx = Math.round(W / 2 - zw / 2), zy = y0 + BAND_H + 14, zh = 86;
  const u = slide(lib, t, T_ZH, 8, E);
  if (u >= 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, zx + u * (zw + 24), lib.H); ctx.clip();
    piece(ctx, scissor(lib, 3, rectBase(zw, zh), 1.5), zx, zy, "#F4EEDF", ground);
    lib.setFont(ctx, tokens, "zh", 58, { weight: 600 }); ctx.fillStyle = C("fg");
    lib.drawText(ctx, lib.TITLE_ZH, W / 2, zy + 64, { align: "center", tracking: 58 * 0.12 });
    ctx.restore();
  }
}

// the motif: one convergence along the diagonal — loose strips → sliced disc → the vermilion disc
function motif(ctx, t, tokens, lib, ground) {
  const C = (k) => lib.color(tokens, k), E = E_(lib, tokens), ink = C("fg"), ts = lib.step(t, 15);
  const g = gathered(lib, t, E);                                                    // 0, 1 after 2.8, 2 after 3.6
  // OUTLINE: five loose strips on the 30° diagonal sweep in from the lower left (land 2.2); each gather pulls them
  // forward along the diagonal and closer together
  STRIPS.forEach(([len, sl, row], j) => {
    const v = slide(lib, t, T_OUT, 8, E); if (v < 0) return;
    const travel = (1 - v) * (620 + 60 * j), fwd = 34 * g, spread = 52 - 9 * g;
    const along = sl * (1 - 0.35 * g) + fwd - travel, off = row * spread;
    const cx = OUT.x + DX * along + NX * off, cy = OUT.y + DY * along + NY * off;
    piece(ctx, scissor(lib, 10 + j, rectBase(len, 26), 1.4), cx, cy, ink, ground, { rot: -ANG, s: 1 });
  });
  // STORYBOARD: the disc in five slices; they are dealt in from the right, odd slices a little further (land 2.4), close up on each
  // gather and shut into one disc on 3.8
  const shut = E(lib.seg(ts, T_G3 - 2 / 30, T_G3)), spread = (16 - 5 * g) * (1 - shut), n = 5, hh = 2 * SB.r / n;
  for (let k = 0; k < n; k++) {
    const v = slide(lib, t, T_SB, 8, E); if (v < 0) continue;
    const ya = -SB.r + k * hh, yb = ya + hh, jit = [-14, 12, -9, 16, -11][k] * (1 - 0.4 * g) * (1 - shut);
    const x = SB.x + jit + (1 - v) * (1040 + 150 * (k % 2)), y = SB.y + (k - 2) * spread;                 // dealt in from the right
    piece(ctx, slicePoly(lib, 20 + k, SB.r, ya, yb), x, y, ink, ground);
  }
  // DRAFT: the single vermilion disc drops in from above and stops dead (2.6)
  const dv = slide(lib, t, T_DR, 8, E);
  if (dv >= 0) piece(ctx, cutCircle(lib, 30, DR.r), DR.x, DR.y - (1 - dv) * 700, C("accent"), ground);
  // labels cut in with their part (they sit on the ground, flat, no shadow)
  [[OUT.x, T_OUT], [SB.x, T_SB], [DR.x, T_DR]].forEach(([x, tl], k) => {
    if (ts < tl - 1e-6) return;
    ctx.save(); ctx.fillStyle = ink;
    lib.setFont(ctx, tokens, "body", 34, { weight: 500 }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), x, LABEL_EN, { align: "center", tracking: 34 * 0.16 });
    lib.setFont(ctx, tokens, "zh", 52, { weight: 600 }); lib.drawText(ctx, lib.MOTIF[k].zh, x, LABEL_ZH, { align: "center", tracking: 52 * 0.2 });
    ctx.restore();
  });
}

// ───────── 4.0: scissors ─────────
// Six equal strips cut along the 30° diagonal. In (u, v) = (along, across) coordinates the frame spans
// u ∈ [−540, 1663], v ∈ [0, 1895]; cut k sits at v = k·1895/6 and wanders a little (scissor hand), computed once.
function cutLine(lib, k) {
  const key = `cut${k}`; if (CUT.has(key)) return CUT.get(key);
  const V = 1895 / 6 * k, pts = [];
  for (let u = -760; u <= 1880; u += 12) pts.push([u, V + (k === 0 ? -60 : k === 6 ? 60 : 2.6 * lib.noise1(u * 0.03, 900 + k) + 1.2 * lib.noise1(u * 0.21, 950 + k))]);
  CUT.set(key, pts); return pts;
}
const toXY = ([u, v]) => [u * DX + v * NX, u * DY + v * NY];
function scissors(ctx, t, tokens, lib, A) {
  const ts = lib.step(t, 15), f = lib.frame(ts), { W, H } = lib;
  for (let i = 0; i < 6; i++) {
    const u = lib.seg(ts, T_SCISSORS, T_SCISSORS + 10 / 30), o = (i % 2 ? -1 : 1) * 2900 * u * u;   // on twos, accelerating away
    if (Math.abs(o) > 2850) continue;
    // the strip = the frame ∩ the band between two cuts, cut out onto its own sheet so its shadow follows every edge
    const x = lib.layer("cj_strip"), a = cutLine(lib, i), b = cutLine(lib, i + 1);
    x.beginPath(); [...a, ...b.slice().reverse()].map(toXY).forEach(([px, py], j) => (j ? x.lineTo(px, py) : x.moveTo(px, py))); x.closePath();
    x.clip(); x.drawImage(A, 0, 0);
    const lift = f === 120 ? 0.3 : 1;                                                               // the cut frame: just lifted
    ctx.save(); ctx.shadowColor = "rgba(0,0,0,0.55)"; ctx.shadowOffsetX = 4 + 7 * lift; ctx.shadowOffsetY = 6 + 9 * lift; ctx.shadowBlur = 6 + 10 * lift;
    ctx.drawImage(x.canvas, Math.round(o * DX), Math.round(o * DY)); ctx.restore();
  }
  if (f === 120) {                                    // the scissor lines themselves, on the stab
    ctx.save(); ctx.strokeStyle = "#0d0c0a"; ctx.lineWidth = 4; ctx.lineJoin = "round";
    for (let k = 1; k < 6; k++) { ctx.beginPath(); cutLine(lib, k).map(toXY).forEach(([px, py], j) => (j ? ctx.lineTo(px, py) : ctx.moveTo(px, py))); ctx.stroke(); }
    ctx.restore();
  }
}

function end(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib, ts = lib.step(t, 15);
  ctx.fillStyle = C("fg"); ctx.fillRect(0, 0, W, H);
  piece(ctx, cutCircle(lib, 30, DR.r), DR.x, DR.y, C("accent"), C("fg"));        // the same piece, the same place
  const word = (str, tk, x, y, size, role, weight, stretch) => {
    if (ts < tk - STEP - 1e-6) return;
    const s = ts >= tk - 1e-6 ? 1 : 1.12, lift = s > 1 ? 1 : 0;
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    lib.setFont(ctx, tokens, role, size, { weight, stretch }); ctx.fillStyle = "#F4EEDF";
    ctx.shadowColor = "rgba(0,0,0,0.5)"; ctx.shadowOffsetX = 3 + 6 * lift; ctx.shadowOffsetY = 4 + 8 * lift; ctx.shadowBlur = 4 + 8 * lift;
    lib.drawText(ctx, str, 0, 0, { tracking: size * 0.03 });
    ctx.restore();
  };
  word("CUTOUT", T_END[0], 192, 600, 156, "display", 800, "condensed");
  word("JAZZ", T_END[1], 192, 756, 156, "display", 800, "condensed");
  word("剪纸爵士片头", T_END[2], 196, 846, 54, "zh", 600);
}
