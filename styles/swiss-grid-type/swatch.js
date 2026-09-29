// swiss-grid-type swatch — International Typographic Style in motion. 150 BPM: 1 beat = 12 frames, 1/16 = 3 frames
// (the swatch's section points 0.8 / 2.0 / 4.0 s all fall on beats; STYLE.md's 112.5 BPM is the long-form default).
//   0.0–0.8  hook: the 12-column grid shoots down the frame in 6 frames from frame 2 (bands + 2 px edges); a 700 px
//            numeral climbs into cols 10–12 in four eased steps and lands on the 0.4 s beat
//   0.8–2.6  headline words rise out of clip boxes from the baseline, one per sixteenth, landing on the beat; the
//            Chinese line follows in three word groups; a 2 px rule is drawn across cols 1–9
//   2.0–4.0  motif on cols 1–3 / 4–6 / 7–9: outline bars grow along their length; the storyboard is pure type, "01 02
//            03" stepping up the type scale and rising from the baseline; the draft is the one red block (lands 2.4 s);
//            labels rise from the baseline. Then one event per beat: 2.8 the short bar snaps to the top row; 3.03 the
//            big numeral steps up; 3.2 the red block breaks the grid (linear, grows, readout 'off grid', drums out);
//            3.6 the storyboard numerals step up one size each, nearest the red block first
//   4.0–5.0  wipe-left: ink fills the columns right → left, one column per frame; the end card rises on black
// Only two curves: easeInOutQuart for snaps, linear for lines. No fades, no bounce, no shadow, no grain.

const M = 96, COL = 122, GUT = 24, BL = 24;
// foley: dry, close letterpress sounds; frame numbers are the same constants the snaps use (frame / 30)
const fx = (x) => Math.round((x / 960 - 1) * 100) / 100, F = (f) => f / 30;
export const FOLEY = [
  { t: F(2), sfx: "swish_rev", gain_db: -14, pan: 0 },                                                               // the grid shoots down
  ...[6, 12].map((f) => ({ t: F(f), sfx: "tick", gain_db: -10, pan: fx(1600) })),                                        // numeral steps (lands f12)
  ...[24, 27, 30, 33].map((f, k) => ({ t: F(f), sfx: "click", gain_db: -8, pan: fx(300 + k * 300) })),               // headline words land
  ...[36, 42, 48].map((f, k) => ({ t: F(f), sfx: "click", gain_db: -10, pan: fx(200 + k * 250) })),                   // Chinese groups
  ...[66, 69].map((f, k) => ({ t: F(f), sfx: "click", gain_db: -8, pan: fx(560 + k * 110) })),                     // storyboard numerals
  { t: F(72), sfx: "pop", gain_db: -4, pan: fx(1170) },                                                                // "03" + the red block
  { t: F(84), sfx: "click", gain_db: -8, pan: fx(300) }, { t: F(94), sfx: "click", gain_db: -6, pan: fx(1600) },     // bar reorder; numeral snap
  { t: F(108), sfx: "whoosh", gain_db: -14, pan: fx(1300) },                                                          // the exception leaves the grid
  ...[105, 108, 111].map((f, k) => ({ t: F(f + 3), sfx: "tick", gain_db: -12, pan: fx(860 - k * 150) })),           // numerals step up, nearest first
  { t: F(120), sfx: "shutter", gain_db: -6, pan: fx(1700) }, { t: F(138), sfx: "click", gain_db: -8, pan: fx(300) },
];
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
  // hook: the grid itself. From frame 2 every column band and its two edges shoot down the frame (linear, 6 frames,
  // staggered one frame per two columns); bands alternate tints so the module reads at phone size
  for (let n = 1; n <= 12; n++) {
    const u = lib.clamp((f - 2 - Math.floor((n - 1) / 2)) / 6); if (u <= 0) continue;
    ctx.fillStyle = n % 2 ? "#E6E3DB" : "#ECEAE3"; ctx.fillRect(colX(n), 54, COL, (1026 - 54) * u);
    ctx.fillStyle = C("extra.0"); ctx.fillRect(colX(n), 54, 2, (1026 - 54) * u); ctx.fillRect(colX(n) + COL - 2, 54, 2, (1026 - 54) * u);
  }
  [108, 972].forEach((y, j) => { const u = lib.clamp((f - 4 - j * 2) / 8); if (u > 0) { ctx.fillStyle = C("extra.0"); ctx.fillRect(M, y, (W - 2 * M) * u, 2); } });

  // giant numeral: climbs into cols 10–12 in four steps (one module each), bottom-aligned at 792
  const nx = colX(10), top = 288, bot = 792;
  lib.setFont(ctx, tokens, "display", 700, { weight: 700 });
  const m = ctx.measureText("3"), steps = [0, 3, 6, 9];                  // lands on frame 12 = 0.4 s
  let done = 0; for (const s of steps) done += SNAP(lib)(lib.clamp((f - s) / 3));
  if (done > 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(nx - 20, top - 40, spanW(10, 12) + 40, bot - top + 64); ctx.clip();
    const up = SNAP(lib)(lib.clamp((f - 91) / 3)) * 2 * BL;                     // 3.03 s: the numeral snaps up one module
    ctx.fillStyle = C("fg"); ctx.fillText("3", nx + m.actualBoundingBoxLeft, bot - up + (4 - done) / 4 * (bot - top + 40));
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
  const ro = SNAP(lib)(lib.clamp((f - 81) / 3));                          // 2.8 s: the short bar snaps to the top row
  [[1, 3], [1, 3], [1, 2]].forEach(([a, b], j) => {
    const u = lib.clamp((f - 60 - j * 3) / 3); if (u <= 0) return;
    const row = j === 2 ? lib.lerp(2, 0, ro) : j + ro;
    ctx.fillStyle = C("fg"); ctx.fillRect(colX(a), y0 + 12 + row * 56, spanW(a, b) * u, 32);
  });
  // storyboard: pure type, no pictogram. "01 02 03" stepping up the type scale (60 / 108 / 156 px: 2.5 / 4.5 / 6.5
  // baselines), flush left on col 4 (optically aligned), all on the module baseline; each rises out of its clip box on
  // a sixteenth (lands f66 / f69 / f72). 3.6 s ripple: each steps up one size (72 / 120 / 168), nearest the red block
  // first, and the line re-flows into the space the exception has just left
  const sbBase = 30 * BL, SCALE = [[60, 72], [108, 120], [156, 168]];
  let sx = colX(4);
  for (let j = 0; j < 3; j++) {
    const rip = SNAP(lib)(lib.clamp((f - 105 - (2 - j) * 3) / 3)), sz = lib.lerp(SCALE[j][0], SCALE[j][1], rip), str = `0${j + 1}`;
    lib.setFont(ctx, tokens, "display", sz, { weight: 700 });
    const m = ctx.measureText(str), tr = sz >= 90 ? -0.02 * sz : 0, x0 = sx + (j === 0 ? m.actualBoundingBoxLeft : 0);
    rise(ctx, lib, t, 63 + j * 3, 3, x0, sbBase, sz, () => { lib.setFont(ctx, tokens, "display", sz, { weight: 700 }); ctx.fillStyle = C("fg"); lib.drawText(ctx, str, x0, sbBase, { tracking: tr }); });
    sx = x0 + m.width + tr + GUT;
  }
  // draft: the one red element, wiped in from the left (frame 69 → lands on 72 = beat 6, 2.4 s)
  const du = SNAP(lib)(lib.clamp((f - 69) / 3));
  if (du > 0) {
    // the one exception: at 3.2 s the red block leaves the grid in a straight line (linear, no snap) and grows;
    // it pauses for one eighth mid-flight (a glance back); drums drop for this bar in score.json
    const e0 = lib.clamp((f - 96) / 9), e1 = lib.clamp((f - 108) / 9), ex = 0.5 * e0 + 0.5 * e1;
    const bx = colX(7) + ex * 64, by = y0 + 12 - ex * 40, bw = spanW(7, 9) * (1 + 0.12 * ex), bhh = (bh - 12) * (1 + 0.12 * ex);
    ctx.fillStyle = C("accent"); ctx.fillRect(bx, by, bw * du, bhh);
    if (f >= 96) {
      lib.setFont(ctx, tokens, "display", 24, { weight: 500 }); ctx.fillStyle = ex > 0.02 ? C("accent") : C("fg");
      lib.drawText(ctx, ex > 0.02 ? `col ${(7 + ex * 0.44).toFixed(2)}  row ${(-ex * 1.67).toFixed(2)}  off grid` : "col 7.00  row 0.00  on grid", colX(7), y0 - 16);
    }
  }
  // labels rise from the baseline, flush left on each module
  [[1, 60], [4, 66], [7, 69]].forEach(([c, f0], k) => {
    rise(ctx, lib, t, f0 + 3, 3, colX(c), 33 * BL, 30, () => { lib.setFont(ctx, tokens, "display", 30, { weight: 500 }); ctx.fillStyle = C("fg"); lib.drawText(ctx, lib.MOTIF[k].en, colX(c), 33 * BL); });
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
