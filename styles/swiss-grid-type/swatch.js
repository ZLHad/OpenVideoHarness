// swiss-grid-type swatch — International Typographic Style in motion. 150 BPM: 1 beat = 12 frames, 1/16 = 3 frames
// (the swatch's section points 0.8 / 2.0 / 4.0 s all fall on beats; STYLE.md's 112.5 BPM is the long-form default).
//   0.0–0.8  the 12-column grid draws down one line per frame (linear); a 700 px numeral climbs into cols 10–12 in
//            four eased steps, one module per sixteenth (frames 9–21)
//   0.8–2.6  headline words rise out of clip boxes from the baseline, one per sixteenth, landing on the beat; the
//            Chinese line follows in three word groups; a 2 px rule is drawn across cols 1–9
//   2.0–4.0  motif on cols 1–3 / 4–6 / 7–9: outline bars grow along their length, storyboard blocks wipe down, the
//            draft is the one red block; labels rise from the baseline
//   4.0–5.0  wipe-left: ink fills the columns right → left, one column per frame; the end card rises on black
// Only two curves: easeInOutQuart for snaps, linear for lines. No fades, no bounce, no shadow, no grain.

const M = 96, COL = 122, GUT = 24, BL = 24;
const colX = (n) => M + (n - 1) * (COL + GUT);                  // left edge of column n (1-based)
const spanW = (a, b) => colX(b) + COL - colX(a);
let L = null;

export async function setup(ctx, tokens, lib) {
  const disp = (x, s) => lib.setFont(x, tokens, "display", s, { weight: 700 });
  const size = lib.fitText(ctx, lib.TITLE_EN, spanW(1, 9) - 20, (s) => disp(ctx, s), { min: 80, max: 124, tracking: -0.02 });
  L = { size };
}

const SNAP = (lib) => lib.ease.inOutQuart;
const fr = (lib, t) => lib.frame(t);
/** Rise from a clip box: text sits on baseline y; before f0 it is below the box, lands at f0 + dur. */
function rise(ctx, lib, t, f0, dur, x, y, h, draw) {
  const f = fr(lib, t); if (f < f0) return;
  const u = SNAP(lib)(lib.clamp((f - f0) / dur));
  ctx.save(); ctx.beginPath(); ctx.rect(x - 4, y - h, 4000, h + Math.round(h * 0.28)); ctx.clip();
  ctx.translate(0, (1 - u) * h * 1.25); draw(); ctx.restore();
}

function page(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib, f = fr(lib, t);
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  // grid: both edges of every column, drawn down one line per frame from f3 (linear)
  ctx.fillStyle = C("extra.0");
  for (let i = 0; i < 24; i++) {
    const n = (i >> 1) + 1, x = i % 2 ? colX(n) + COL - 1 : colX(n), u = lib.clamp((f - 3 - i) / 8);
    if (u > 0) ctx.fillRect(x, 54, 1, (1026 - 54) * u);
  }
  [108, 972].forEach((y, j) => { const u = lib.clamp((f - 6 - j * 4) / 16); if (u > 0) ctx.fillRect(M, y, (W - 2 * M) * u, 1); });

  // giant numeral: climbs into cols 10–12 in four steps (one module each), bottom-aligned at 792
  const nx = colX(10), top = 288, bot = 792;
  lib.setFont(ctx, tokens, "display", 700, { weight: 700 });
  const m = ctx.measureText("3"), steps = [9, 12, 15, 18];
  let done = 0; for (const s of steps) done += SNAP(lib)(lib.clamp((f - s) / 3));
  if (done > 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(nx - 20, top - 40, spanW(10, 12) + 40, bot - top + 64); ctx.clip();
    ctx.fillStyle = C("fg"); ctx.fillText("3", nx + m.actualBoundingBoxLeft, bot + (4 - done) / 4 * (bot - top + 40));
    ctx.restore();
  }

  // headline: one word per sixteenth; the first lands on beat 2 (frame 24 = 0.8 s)
  const size = L.size, base = 13 * BL;
  lib.setFont(ctx, tokens, "display", size, { weight: 700 }); ctx.fillStyle = C("fg");
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: colX(1), y: base, tracking: -size * 0.02 });
  const words = []; let cur = null;
  for (const g of lay.glyphs) { if (g.ch === " ") { cur = null; continue; } if (!cur) { cur = { x: g.x, str: "" }; words.push(cur); } cur.str += g.ch; }
  words.forEach((w, k) => rise(ctx, lib, t, 21 + k * 3, 3, w.x, base, size, () => { lib.setFont(ctx, tokens, "display", size, { weight: 700 }); ctx.fillStyle = C("fg"); lib.drawText(ctx, w.str, w.x, base, { tracking: -size * 0.02 }); }));
  // Chinese in three word groups
  const zb = 17 * BL, zs = 72;
  lib.setFont(ctx, tokens, "zh", zs, { weight: 600 });
  let zx = colX(1);
  ["每一帧，", "都是", "代码。"].forEach((g, k) => {
    const x0 = zx; zx += ctx.measureText(g).width + (k === 0 ? 0 : 4);
    rise(ctx, lib, t, 33 + k * 6, 3, x0, zb, zs, () => { lib.setFont(ctx, tokens, "zh", zs, { weight: 600 }); ctx.fillStyle = C("fg"); lib.drawText(ctx, g, x0, zb); });
    lib.setFont(ctx, tokens, "zh", zs, { weight: 600 });
  });
  // rule across cols 1–9 (linear)
  const ru = lib.clamp((f - 48) / 12);
  if (ru > 0) { ctx.fillStyle = C("fg"); ctx.fillRect(colX(1), 20 * BL, spanW(1, 9) * ru, 2); }

  // motif
  const y0 = 23 * BL, bh = 7 * BL;                                         // band 552–720
  // outline: three bars grow along their length (linear), one per sixteenth
  [[1, 3], [1, 3], [1, 2]].forEach(([a, b], j) => {
    const u = lib.clamp((f - 60 - j * 3) / 3); if (u <= 0) return;
    ctx.fillStyle = C("fg"); ctx.fillRect(colX(a), y0 + 12 + j * 56, spanW(a, b) * u, 32);
  });
  // storyboard: three blocks, one per column, wiped down
  for (let j = 0; j < 3; j++) {
    const u = SNAP(lib)(lib.clamp((f - 63 - j * 3) / 3)); if (u <= 0) continue;
    ctx.fillStyle = C("fg"); ctx.fillRect(colX(4 + j), y0 + 12, COL, (bh - 12) * u);
  }
  // draft: the one red element, wiped in from the left (frame 69 → lands on 72 = beat 6, 2.4 s)
  const du = SNAP(lib)(lib.clamp((f - 69) / 3));
  if (du > 0) {
    ctx.fillStyle = C("accent"); ctx.fillRect(colX(7), y0 + 12, spanW(7, 9) * du, bh - 12);
    if (du >= 1) { ctx.fillStyle = C("extra.2"); ctx.beginPath(); const cx = colX(8) + COL / 2, cy = y0 + 12 + (bh - 12) / 2; ctx.moveTo(cx - 30, cy - 38); ctx.lineTo(cx + 40, cy); ctx.lineTo(cx - 30, cy + 38); ctx.closePath(); ctx.fill(); }
  }
  // labels rise from the baseline, flush left on each module
  [[1, 60], [4, 66], [7, 69]].forEach(([c, f0], k) => {
    rise(ctx, lib, t, f0 + 3, 3, colX(c), 33 * BL, 30, () => { lib.setFont(ctx, tokens, "display", 30, { weight: 500 }); ctx.fillStyle = C("fg"); lib.drawText(ctx, `0${k + 1}  ${lib.MOTIF[k].en}`, colX(c), 33 * BL); });
    rise(ctx, lib, t, f0 + 6, 3, colX(c), 36 * BL, 46, () => { lib.setFont(ctx, tokens, "zh", 46, { weight: 400 }); ctx.fillStyle = C("fg"); lib.drawText(ctx, lib.MOTIF[k].zh, colX(c), 36 * BL); });
  });
}

function endCard(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), f = fr(lib, t);
  ctx.fillStyle = "#3a3a3a";
  for (let n = 1; n <= 12; n++) { ctx.fillRect(colX(n), 54, 1, 972); ctx.fillRect(colX(n) + COL - 1, 54, 1, 972); }
  rise(ctx, lib, t, 135, 3, colX(1), 21 * BL, 96, () => { lib.setFont(ctx, tokens, "display", 96, { weight: 700 }); ctx.fillStyle = C("extra.2"); lib.drawText(ctx, "Swiss Grid Type", colX(1), 21 * BL, { tracking: -96 * 0.02 }); });
  rise(ctx, lib, t, 138, 3, colX(1), 24 * BL, 56, () => { lib.setFont(ctx, tokens, "zh", 56, { weight: 600 }); ctx.fillStyle = C("extra.2"); lib.drawText(ctx, "瑞士网格动态字", colX(1), 24 * BL); });
  const ru = lib.clamp((f - 141) / 6);
  if (ru > 0) { ctx.fillStyle = C("accent"); ctx.fillRect(colX(1), 26 * BL, spanW(1, 2) * ru, 12); }
}

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib, f = fr(lib, t);
  page(ctx, Math.min(t, 3.99), tokens, lib);
  if (f < 120) return;
  // wipe-left: columns fill with ink, right → left, one per frame, each wiped down over 4 frames
  ctx.fillStyle = C("fg");
  let all = true;
  for (let n = 12; n >= 1; n--) {
    const u = SNAP(lib)(lib.clamp((f - 120 - (12 - n)) / 4)); if (u < 1) all = false; if (u <= 0) continue;
    const x0 = n === 1 ? 0 : colX(n) - GUT / 2, x1 = n === 12 ? W : colX(n) + COL + GUT / 2;
    ctx.fillRect(x0, 0, x1 - x0, H * u);
  }
  if (all) { ctx.fillStyle = C("fg"); ctx.fillRect(0, 0, W, H); endCard(ctx, t, tokens, lib); }
}
