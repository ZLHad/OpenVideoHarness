// blueprint swatch: one cyanotype sheet, drawn in drafting order; the camera reads it like an eye.
//   0.0–0.3  hook: the sheet unrolls down the frame (roll slap on the first beat)
//   0.3–0.7  a thick datum centre line shoots in from off-frame, the vertical one drops, a crosshair clicks onto them
//   0.6–2.1  guide lines, then the title lettered stroke by stroke with a bright nib; Chinese in long Fangsong
//   2.0–2.95 FIG. 1 outline (centre + construction lines) → FIG. 2 storyboard (outline + hidden lines, then a
//            cutting plane sweeps it) → FIG. 3 draft (section hatching, live dimension, balloon)
//   3.1–3.7  FIG. 3 stretches; its dimension follows and counts 440 → 520 in whole mm inside a reviewer-yellow cloud
//   4.0–4.8  fig-pan: the camera pans and pushes toward the title block, clamped so the frame never leaves the sheet
// Everything is drawn in sheet coordinates under one camera transform; line widths scale as zoom^0.6.

let L = null;
const SW = 2400, SH = 1350;
const TB = { x: 1880, y: 1100, w: 480, h: 210 };            // title block (sheet coords)

export const fonts = ["STFangsong", "DIN Alternate"];

// ONE timing table: the drawing below and the foley (EVENTS → events.json, generated from this module) both read it
export const TL = {
  roll: [0.0, 0.3], hLine: [0.3, 0.5], vLine: [0.38, 0.56], cross: [0.55, 0.7],
  title: 0.6, letter0: 0.72, stag: 0.045, zhGuide: 1.3, zh: 1.4, zhStag: 0.07,
  fig: (k) => 2.0 + k * 0.15, sweep: [2.62, 3.0], stretch: [3.1, 3.7], cloud: 3.02, pan: [4.0, 4.8], rev: 4.5,
};
const FIG_X = [448, 960, 1472], FIG_Y = 575;                              // lib.slots(3, SAFE.title) centres
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;   // pan = (2x/W − 1) · 0.7
const wordStarts = (str, t0, stag) => { const out = []; let n = 0, prev = " "; for (const ch of str) { if (ch !== " ") { if (prev === " ") out.push(t0 + n * stag); n++; } prev = ch; } return out; };
export const FOLEY = [
  { t: TL.roll[0] + 0.6 * (TL.roll[1] - TL.roll[0]), sfx: "whoosh", gain_db: -12 },      // the sheet unrolls
  { t: TL.roll[1], sfx: "click", gain_db: -8 },                                           // …and lands
  // the ticks sit 8 dB higher than first written (12 for the figure ticks): the marimbas' 16ths cover 1–4 kHz, and
  // at the old gains every tick was 15–21 dB under the bed (qa mix: BURIED), the figure ticks only a faint match
  { t: TL.hLine[0], sfx: "tick", gain_db: -4, pan: -0.7 },                             // the pen touches down
  { t: TL.cross[1], sfx: "click", gain_db: -6, pan: 0 },                                  // crosshair clicks into place
  ...wordStarts("Every frame is code.", TL.letter0, TL.stag).map((t, i) => ({ t, sfx: "tick", gain_db: -10, pan: pan(260 + i * 300) })),
  { t: TL.zh, sfx: "tick", gain_db: -10, pan: pan(260) },
  ...FIG_X.map((x, k) => ({ t: TL.fig(k), sfx: "tick", gain_db: -2, pan: pan(x) })),     // each figure's first centre line
  { t: TL.fig(2) + 0.6, sfx: "click", gain_db: -10, pan: pan(FIG_X[2]) },                 // the dimension number appears
  { t: TL.sweep[1], sfx: "swish_rev", gain_db: -14, pan: pan(FIG_X[1]) },                 // cutting plane A–A lands
  { t: TL.cloud, sfx: "toggle", gain_db: -10, pan: pan(FIG_X[2]) },                       // revision cloud
  ...[0, 1, 2, 3].map((i) => ({ t: TL.stretch[0] + ((i + 0.5) * (TL.stretch[1] - TL.stretch[0])) / 4, sfx: "tick", gain_db: -8, pan: pan(FIG_X[2]) })),    // the count
  { t: TL.pan[0] + 0.4, sfx: "whoosh", gain_db: -12, pan: 0.3 },                          // fig-pan to the title block
  { t: TL.rev, sfx: "click", gain_db: -8, pan: 0.45 },                                    // revision triangle
];

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  // ── the sheet, built once: fbm mottling + coating streaks + folds + bleached edge + specks
  const c = document.createElement("canvas"); c.width = SW; c.height = SH;
  const x = c.getContext("2d");
  const gw = 240, gh = 135, g = document.createElement("canvas"); g.width = gw; g.height = gh;
  const gx = g.getContext("2d"), img = gx.createImageData(gw, gh), A = lib.rgb(P("bg")), B = lib.rgb(P("extra.0"));
  for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
    const n = 0.5 + 0.55 * lib.fbm2(i / 38, j / 38, { octaves: 4, seed: 5 }) + 0.12 * (i / gw - 0.5), k = (j * gw + i) * 4;
    for (let ch = 0; ch < 3; ch++) img.data[k + ch] = lib.lerp(A[ch], B[ch], lib.clamp(n));
    img.data[k + 3] = 255;
  }
  gx.putImageData(img, 0, 0); x.imageSmoothingQuality = "high"; x.drawImage(g, 0, 0, SW, SH);
  const r = lib.rng(8);
  for (let s = 0; s < 110; s++) {                                        // uneven coating streaks (short, soft, irregular)
    const y = r() * SH, a = 0.018 + 0.035 * r(), light = r() < 0.5, x0 = r() * SW, len = 300 + 1500 * r(), th = 2 + 10 * r();
    const gr = x.createLinearGradient(x0, 0, x0 + len, 0), c = light ? "120,160,215" : "8,24,56";
    gr.addColorStop(0, `rgba(${c},0)`); gr.addColorStop(0.5, `rgba(${c},${a})`); gr.addColorStop(1, `rgba(${c},0)`);
    x.fillStyle = gr; x.fillRect(x0, y, len, th);
  }
  const edge = (x0, y0, x1, y1, w) => { const gr = x.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, lib.rgba(P("extra.2"), 0.55)); gr.addColorStop(1, lib.rgba(P("extra.2"), 0)); x.fillStyle = gr; return w; };
  edge(0, 0, 60, 0); x.fillRect(0, 0, 60, SH); edge(SW, 0, SW - 60, 0); x.fillRect(SW - 60, 0, 60, SH);
  edge(0, 0, 0, 60); x.fillRect(0, 0, SW, 60); edge(0, SH, 0, SH - 60); x.fillRect(0, SH - 60, SW, 60);
  for (const [x0, y0, x1, y1, dx, dy] of [[SW / 2, 0, SW / 2, SH, 3, 0], [0, SH / 2, SW, SH / 2, 0, 3]]) {   // folds
    x.strokeStyle = lib.rgba(P("extra.2"), 0.55); x.lineWidth = 2; x.beginPath(); x.moveTo(x0, y0); x.lineTo(x1, y1); x.stroke();
    x.strokeStyle = "rgba(6,18,44,0.35)"; x.lineWidth = 3; x.beginPath(); x.moveTo(x0 + dx, y0 + dy); x.lineTo(x1 + dx, y1 + dy); x.stroke();
  }
  for (let s = 0; s < 500; s++) { x.fillStyle = `rgba(200,220,245,${0.08 + 0.12 * r()})`; x.beginPath(); x.arc(r() * SW, r() * SH, 0.6 + 1.4 * r(), 0, lib.TAU); x.fill(); }
  L = { paper: c, slots: lib.slots(3, { area: lib.SAFE.title, y: 690 }) };
}

// camera: sheet → screen. Holds on the drawing area, then pans + pushes to the title block (4.0–4.8).
function cam(t, lib) {
  const u = lib.tween(t, TL.pan[0], TL.pan[1], lib.ease.inOutCubic), Z = 1.7;
  const ex = Math.min(TB.x + TB.w / 2, SW - 960 / Z), ey = Math.min(TB.y + TB.h / 2, SH - 540 / Z);   // never show the table
  return { cx: lib.lerp(960, ex, u), cy: lib.lerp(540, ey, u), z: lib.lerp(1, Z, u) };
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const C = cam(t, lib);
  ctx.fillStyle = P("extra.3"); ctx.fillRect(0, 0, W, H);
  // hook: the sheet unrolls from the top edge (0.0–0.3 s)
  const rollY = lib.lerp(70, H + 90, lib.ease.outCubic(lib.seg(t, TL.roll[0], TL.roll[1])));
  ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, Math.max(0, rollY)); ctx.clip();
  ctx.save();
  ctx.translate(W / 2, H / 2); ctx.scale(C.z, C.z); ctx.translate(-C.cx, -C.cy);
  const lw = (w) => w * Math.pow(C.z, 0.6) / C.z;                        // screen width = w · zoom^0.6
  ctx.save(); ctx.shadowColor = "rgba(0,0,0,0.6)"; ctx.shadowBlur = 40; ctx.shadowOffsetX = 10; ctx.shadowOffsetY = 14;
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, SW, SH); ctx.restore();
  ctx.drawImage(L.paper, 0, 0);
  ctx.shadowColor = "rgba(232,241,250,0.35)"; ctx.shadowBlur = 3;         // a touch of ink bleed on every line
  drawSheet(ctx, t, tokens, lib, lw);
  ctx.restore(); ctx.restore();
  if (rollY < H + 60) {                                                     // the roll itself, with its shadow on the table
    const sh = ctx.createLinearGradient(0, rollY + 30, 0, rollY + 90); sh.addColorStop(0, "rgba(0,0,0,0.55)"); sh.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = sh; ctx.fillRect(0, rollY + 30, W, 60);
    const rg = ctx.createLinearGradient(0, rollY - 38, 0, rollY + 38);
    [[0, "#0F2A52"], [0.25, P("extra.0")], [0.42, "#9DBDE6"], [0.55, P("extra.0")], [1, "#0B1F3E"]].forEach(([q, c]) => rg.addColorStop(q, c));
    ctx.fillStyle = rg; ctx.fillRect(0, rollY - 38, W, 76);
    ctx.fillStyle = "rgba(232,241,250,0.5)"; ctx.fillRect(0, rollY - 38, W, 2);
  }
}

// polyline drawn on up to u (0..1); returns the tip so a nib can sit on it
function drawOn(ctx, pts, u) {
  let tot = 0; const Ls = [];
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); Ls.push(l); tot += l; }
  let left = Math.max(0, Math.min(1, u)) * tot, tip = pts[0];
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length && left > 0; i++) {
    const f = Math.min(1, left / Ls[i - 1]); tip = [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
    ctx.lineTo(tip[0], tip[1]); left -= Ls[i - 1];
  }
  ctx.stroke(); return tip;
}
function nib(ctx, lib, p, a = 1) {
  if (a <= 0) return;
  ctx.save(); ctx.shadowBlur = 0; const g = ctx.createRadialGradient(p[0], p[1], 0, p[0], p[1], 14);
  g.addColorStop(0, `rgba(255,255,255,${0.95 * a})`); g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p[0], p[1], 14, 0, lib.TAU); ctx.fill(); ctx.restore();
}

function drawSheet(ctx, t, tokens, lib, lw) {
  const P = (k) => lib.color(tokens, k);
  const WHITE = P("fg"), PALE = P("extra.1"), YEL = P("accent");
  const E = lib.easeOf(tokens.ease.enter);
  // border (inset 40) + title block frame
  ctx.strokeStyle = WHITE; ctx.lineWidth = lw(3);
  const b = [[40, 40], [SW - 40, 40], [SW - 40, SH - 40], [40, SH - 40], [40, 40]];
  const bu = E(lib.seg(t, 0.2, 0.8)); if (bu > 0) { const tip = drawOn(ctx, b, bu); if (bu < 1) nib(ctx, lib, tip); }
  const PALE_ = PALE;
  if (t > 0.5) titleBlock(ctx, t, tokens, lib, lw);
  // hook: the datum centre line shoots in from off-frame, the vertical centre line drops, a crosshair lands on them
  {
    const hot = 1 - lib.seg(t, 0.9, 1.4), col = lib.mixColor(PALE, WHITE, hot), fast = lib.ease.outExpo, DY = FIG_Y;
    ctx.save(); ctx.strokeStyle = col; ctx.globalAlpha = lib.lerp(0.7, 1, hot) * (1 - 0.6 * lib.seg(t, 1.9, 2.3)); ctx.lineWidth = lw(lib.lerp(2, 5, hot));
    const hu = fast(lib.seg(t, ...TL.hLine)), vu = fast(lib.seg(t, ...TL.vLine));
    let tipH = null, tipV = null;
    if (hu > 0) { ctx.setLineDash([34, 8, 6, 8]); tipH = drawOn(ctx, [[-160, DY], [SW + 40, DY]], hu); ctx.setLineDash([]); }
    if (vu > 0) { ctx.setLineDash([34, 8, 6, 8]); tipV = drawOn(ctx, [[960, -140], [960, SH + 40]], vu); ctx.setLineDash([]); }
    const cu = lib.ease.outCubic(lib.seg(t, ...TL.cross));
    if (cu > 0) {
      ctx.lineWidth = lw(lib.lerp(2, 5, hot)); ctx.beginPath(); ctx.arc(960, DY, 70, -Math.PI / 2, -Math.PI / 2 + lib.TAU * cu); ctx.stroke();
      ctx.beginPath(); ctx.arc(960, DY, 28, 0, lib.TAU * cu); ctx.stroke();
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { ctx.beginPath(); ctx.moveTo(960 + dx * 84, DY + dy * 84); ctx.lineTo(960 + dx * (84 + 34 * cu), DY + dy * (84 + 34 * cu)); ctx.stroke(); }
    }
    ctx.restore();
    if (hu > 0 && hu < 1 && tipH) nib(ctx, lib, tipH); if (vu > 0 && vu < 1 && tipV) nib(ctx, lib, tipV);
    const fl = lib.env(t, 0.55, 0.85, 0.04, 0.24); if (fl > 0) nib(ctx, lib, [960, DY], fl * 1.6);
  }

  // ── title: guide lines, then lettering stroke by stroke
  const T0 = TL.title;
  guide(ctx, lib, 192, 232, 1260, 232 - 0.72 * 132, lib.seg(t, T0, T0 + 0.2), PALE, lw);
  lib.setFont(ctx, tokens, "display", 132, { weight: 700 });
  const tip = letter(ctx, lib, lib.TITLE_EN, 192, 232, t, TL.letter0, TL.stag, 0.3, WHITE, 132, 0.02 * 132, 1, lw);
  guide(ctx, lib, 192, 330, 700, 330 - 0.82 * 62, lib.seg(t, TL.zhGuide, TL.zhGuide + 0.2), PALE, lw);
  lib.setFont(ctx, tokens, "zh", 62, { weight: 400 });
  const tip2 = letter(ctx, lib, lib.TITLE_ZH, 192, 330, t, TL.zh, TL.zhStag, 0.26, WHITE, 62, 0.14 * 62, 0.72, lw);
  if (tip) nib(ctx, lib, tip); if (tip2) nib(ctx, lib, tip2);

  // ── the three figures
  FIG_X.forEach((x, k) => figure(ctx, t, tokens, lib, lw, x, FIG_Y, k));
  // general notes, top right (lettered in pale blue-white, texture more than text)
  const na = lib.seg(t, 1.1, 1.5);
  if (na > 0) {
    ctx.save(); ctx.shadowBlur = 0; ctx.fillStyle = PALE; ctx.globalAlpha = na * 0.85;
    lib.setFont(ctx, tokens, "body", 26, { weight: 700 });
    ["GENERAL NOTES", "1. ALL DIMENSIONS IN MM.", "2. DO NOT SCALE DRAWING."].forEach((q, i) => lib.drawText(ctx, q, 1420, 150 + i * 40, { tracking: 0.08 * 26 }));
    ctx.restore();
  }
}

function guide(ctx, lib, x0, yb, x1, yc, u, col, lw) {
  if (u <= 0) return;
  ctx.save(); ctx.strokeStyle = col; ctx.globalAlpha = 0.45; ctx.lineWidth = lw(1); ctx.shadowBlur = 0;
  drawOn(ctx, [[x0 - 20, yb], [x1, yb]], u); drawOn(ctx, [[x0 - 20, yc], [x1, yc]], u); ctx.restore();
}

// engineering lettering: glyph outline traced by a growing dash, fill comes in at the end; sx < 1 = long Fangsong
function letter(ctx, lib, str, x, y, t, t0, stag, dur, col, size, tr, sx, lw) {
  const lay = lib.layoutText(ctx, str, { x: 0, y, tracking: tr });
  ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "alphabetic"; ctx.strokeStyle = col; ctx.fillStyle = col;
  ctx.lineWidth = lw(1.6); let n = 0, tip = null;
  for (const g of lay.glyphs) {
    if (g.ch === " ") continue;
    const u = lib.seg(t, t0 + n * stag, t0 + n * stag + dur); n++;
    if (u <= 0) continue;
    const gx = x + g.cx * sx;
    ctx.save(); ctx.translate(gx, y); ctx.scale(sx, 1);
    if (u < 1) { ctx.setLineDash([size * 5 * lib.ease.inOutSine(Math.min(1, u / 0.75)), 1e5]); ctx.strokeText(g.ch, 0, 0); ctx.setLineDash([]); tip = [gx + (u - 0.5) * g.w * sx, y - size * 0.35]; }
    const f = lib.smoothstep(0.6, 1, u); if (f > 0) { ctx.globalAlpha = f; ctx.fillText(g.ch, 0, 0); }
    ctx.restore();
  }
  ctx.restore(); return tip;
}

function dashLine(ctx, pts, u, dash) { ctx.save(); ctx.setLineDash(dash); drawOn(ctx, pts, u); ctx.restore(); }

function figure(ctx, t, tokens, lib, lw, cx, cy, k) {
  const P = (q) => lib.color(tokens, q);
  const WHITE = P("fg"), PALE = P("extra.1"), YEL = P("accent");
  const E = lib.easeOf(tokens.ease.enter);
  const base = TL.fig(k);
  const stretch = k === 2 ? lib.tween(t, TL.stretch[0], TL.stretch[1], lib.ease.inOutCubic) : 0;
  const w = 440 + 80 * stretch, h = 280, x0 = cx - w / 2, y0 = cy - h / 2, hx = cx, R = 72, yd = y0 + h + 84;
  const cu = E(lib.seg(t, base, base + 0.3));
  if (cu > 0) {                                                           // centre lines (dash-dot)
    ctx.strokeStyle = PALE; ctx.lineWidth = lw(2.2);
    dashLine(ctx, [[x0 - 30, cy], [x0 + w + 30, cy]], cu, [30, 7, 5, 7]);
    dashLine(ctx, [[hx, y0 - 30], [hx, y0 + h + 30]], cu, [30, 7, 5, 7]);
  }
  if (k === 0) {                                                          // FIG. 1: construction lines only
    const u = E(lib.seg(t, base + 0.1, base + 0.45));
    if (u > 0) {
      ctx.save(); ctx.strokeStyle = PALE; ctx.globalAlpha = 0.6; ctx.lineWidth = lw(1.8);
      for (const yy of [y0, y0 + h]) drawOn(ctx, [[x0 - 30, yy], [x0 + w + 30, yy]], u);
      for (const xx of [x0, x0 + w]) drawOn(ctx, [[xx, y0 - 30], [xx, y0 + h + 30]], u);
      ctx.beginPath(); ctx.arc(hx, cy, R, -Math.PI / 2, -Math.PI / 2 + lib.TAU * u); ctx.stroke();
      ctx.restore();
    }
  } else {
    const ou = E(lib.seg(t, base + 0.12, base + 0.42));
    if (ou > 0) {                                                         // outline + hole
      ctx.strokeStyle = WHITE; ctx.lineWidth = lw(4.5);
      const tip = drawOn(ctx, [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h], [x0, y0]], ou);
      ctx.lineWidth = lw(3.5); ctx.beginPath(); ctx.arc(hx, cy, R, -Math.PI / 2, -Math.PI / 2 + lib.TAU * ou); ctx.stroke();
      if (ou < 1) nib(ctx, lib, tip);
    }
    if (k === 1) {                                                        // FIG. 2: hidden lines, then a cutting plane sweeps
      const hu = E(lib.seg(t, base + 0.3, base + 0.5));
      if (hu > 0) { ctx.strokeStyle = WHITE; ctx.lineWidth = lw(3); for (const xx of [hx - 100, hx + 100]) dashLine(ctx, [[xx, y0], [xx, y0 + h]], hu, [14, 8]); }
      const sw = lib.ease.outCubic(lib.seg(t, ...TL.sweep));
      if (sw > 0) {
        const sx = lib.lerp(x0 - 60, hx + 150, sw);
        ctx.save(); ctx.strokeStyle = WHITE; ctx.lineWidth = lw(3.2); ctx.setLineDash([36, 7, 6, 7, 6, 7]);
        ctx.beginPath(); ctx.moveTo(sx, y0 - 56); ctx.lineTo(sx, y0 + h + 56); ctx.stroke(); ctx.setLineDash([]);
        const aa = lib.seg(t, 2.95, 3.1);
        if (aa > 0) { ctx.globalAlpha = aa; ctx.fillStyle = WHITE; ctx.shadowBlur = 0;
          for (const yy of [y0 - 56, y0 + h + 56]) { ctx.beginPath(); ctx.moveTo(sx - 40, yy); ctx.lineTo(sx - 12, yy - 12); ctx.lineTo(sx - 12, yy + 12); ctx.closePath(); ctx.fill(); ctx.fillRect(sx - 14, yy - 2, 14, 4);
            lib.setFont(ctx, tokens, "display", 44, { weight: 700 }); lib.drawText(ctx, "A", sx + 26, yy + 16, { align: "center" }); } }
        ctx.restore();
      }
    }
    if (k === 2) {                                                        // FIG. 3: hatching, live dimension, balloon
      const su = lib.seg(t, base + 0.3, base + 0.55);
      if (su > 0) {
        ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, w, h); ctx.arc(hx, cy, R, 0, lib.TAU, true); ctx.clip("evenodd");
        ctx.beginPath(); ctx.rect(x0, y0, w * su, h); ctx.clip();
        ctx.strokeStyle = WHITE; ctx.globalAlpha = 0.85; ctx.lineWidth = lw(2); ctx.shadowBlur = 0;
        for (let d = -h; d < w + h; d += 22) { ctx.beginPath(); ctx.moveTo(x0 + d, y0 + h); ctx.lineTo(x0 + d + h, y0); ctx.stroke(); }
        ctx.restore();
      }
      const du = E(lib.seg(t, base + 0.45, base + 0.7));
      if (du > 0) {
        ctx.strokeStyle = PALE; ctx.fillStyle = PALE; ctx.lineWidth = lw(2.4);
        drawOn(ctx, [[x0, y0 + h + 10], [x0, yd + 14]], du); drawOn(ctx, [[x0 + w, y0 + h + 10], [x0 + w, yd + 14]], du);
        drawOn(ctx, [[x0, yd], [x0 + w, yd]], du);
        if (du >= 1) for (const [ax, dir] of [[x0, 1], [x0 + w, -1]]) { ctx.beginPath(); ctx.moveTo(ax, yd); ctx.lineTo(ax + dir * 26, yd - 9); ctx.lineTo(ax + dir * 26, yd + 9); ctx.closePath(); ctx.fill(); }
        // the live number, whole millimetres, big enough to read on a phone
        ctx.save(); ctx.globalAlpha = lib.seg(t, base + 0.6, base + 0.75); ctx.shadowBlur = 0;
        const changing = stretch > 0 && stretch < 1;
        lib.setFont(ctx, tokens, "body", 58, { weight: 700 }); ctx.fillStyle = changing ? YEL : WHITE;
        lib.drawText(ctx, String(Math.round(w)), x0 + w / 2, yd - 16, { align: "center" });
        ctx.restore();
        const rc = lib.env(t, TL.cloud, 3.95, 0.16, 0.25);
        if (rc > 0) {                                                     // revision cloud (reviewer yellow, once)
          ctx.save(); ctx.strokeStyle = YEL; ctx.lineWidth = lw(3.2); ctx.globalAlpha = rc; ctx.shadowBlur = 0;
          const ex = x0 + w / 2, ey = yd - 36, rx = 124, ry = 50, n = 14;
          ctx.beginPath();
          for (let i = 0; i < n; i++) { const a0 = (i / n) * lib.TAU, a1 = ((i + 1) / n) * lib.TAU, am = (a0 + a1) / 2;
            const p0 = [ex + rx * Math.cos(a0), ey + ry * Math.sin(a0)], p1 = [ex + rx * Math.cos(a1), ey + ry * Math.sin(a1)], bulge = [ex + (rx + 18) * Math.cos(am), ey + (ry + 18) * Math.sin(am)];
            if (i === 0) ctx.moveTo(p0[0], p0[1]); ctx.quadraticCurveTo(bulge[0], bulge[1], p1[0], p1[1]); }
          ctx.stroke(); ctx.restore();
        }
      }
      const bu = E(lib.seg(t, base + 0.42, base + 0.58));                   // balloon 3 with a leader
      if (bu > 0) {
        ctx.strokeStyle = WHITE; ctx.lineWidth = lw(2);
        const bx = x0 + w - 30, by = y0 - 64;
        drawOn(ctx, [[x0 + w - 70, y0 + 30], [bx - 12, by + 26]], bu);
        if (bu >= 1) { ctx.beginPath(); ctx.arc(bx, by, 30, 0, lib.TAU); ctx.stroke();
          ctx.save(); ctx.shadowBlur = 0; lib.setFont(ctx, tokens, "body", 38, { weight: 700 }); ctx.fillStyle = WHITE; lib.drawText(ctx, "3", bx, by + 14, { align: "center" }); ctx.restore(); }
      }
    }
  }
  // label: FIG. n · NAME, then the Chinese in long Fangsong
  const la = lib.seg(t, base + 0.3, base + 0.5);
  if (la > 0) {
    ctx.save(); ctx.globalAlpha = la; ctx.shadowBlur = 0; ctx.fillStyle = WHITE;
    lib.setFont(ctx, tokens, "display", 48, { weight: 700 });
    lib.drawText(ctx, `FIG. ${k + 1} · ${lib.MOTIF[k].en.toUpperCase()}`, cx, yd + 76, { align: "center", tracking: 0.06 * 48 });
    lib.setFont(ctx, tokens, "zh", 58, { weight: 400 });
    const str = lib.MOTIF[k].zh, gw = 58 * 0.72 + 12, x = cx - (gw * str.length - 12) / 2;
    [...str].forEach((ch, i) => { ctx.save(); ctx.translate(x + i * gw + 58 * 0.36, yd + 144); ctx.scale(0.72, 1); ctx.textAlign = "center"; ctx.fillText(ch, 0, 0); ctx.restore(); });
    ctx.restore();
  }
}

function titleBlock(ctx, t, tokens, lib, lw) {
  const P = (k) => lib.color(tokens, k);
  const WHITE = P("fg"), PALE = P("extra.1"), YEL = P("accent");
  const u = lib.easeOf(tokens.ease.enter)(lib.seg(t, 0.5, 1.2));
  ctx.strokeStyle = WHITE; ctx.lineWidth = lw(2.4);
  const { x, y, w, h } = TB;
  drawOn(ctx, [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], u);
  ctx.lineWidth = lw(1.2);
  drawOn(ctx, [[x, y + 120], [x + w, y + 120]], u); drawOn(ctx, [[x + 330, y + 120], [x + 330, y + h]], u);
  ctx.save(); ctx.shadowBlur = 0; ctx.fillStyle = WHITE; ctx.globalAlpha = lib.seg(t, 1.0, 1.4);
  lib.setFont(ctx, tokens, "display", 74, { weight: 700 }); lib.drawText(ctx, "BLUEPRINT", x + 24, y + 92, { tracking: 0.06 * 74 });
  lib.setFont(ctx, tokens, "zh", 46, { weight: 400 });
  [..."工程蓝图"].forEach((ch, i) => { ctx.save(); ctx.translate(x + 24 + i * 44 + 17, y + 180); ctx.scale(0.72, 1); ctx.textAlign = "center"; ctx.fillText(ch, 0, 0); ctx.restore(); });
  lib.setFont(ctx, tokens, "body", 26, { weight: 700 }); ctx.fillStyle = PALE; lib.drawText(ctx, "SHEET 1/1", x + 350, y + 152);
  // revision triangle: the end shot's one yellow mark
  ctx.strokeStyle = YEL; ctx.fillStyle = YEL; ctx.lineWidth = lw(2); ctx.globalAlpha = lib.seg(t, TL.rev, TL.rev + 0.25);
  ctx.beginPath(); ctx.moveTo(x + 400, y + 170); ctx.lineTo(x + 422, y + 196); ctx.lineTo(x + 378, y + 196); ctx.closePath(); ctx.stroke();
  lib.setFont(ctx, tokens, "body", 20, { weight: 700 }); lib.drawText(ctx, "A", x + 400, y + 192, { align: "center" });
  ctx.restore();
}
