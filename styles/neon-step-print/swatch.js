// neon-step-print swatch — neon night, step-printed motion smear, red/green with fixed meanings.
//   0.0–0.8  the street lights flicker on at 0.1 s; night street under green fluorescent light; the crowd and traffic already stream past, step-printed:
//            sampled at 8 fps, each sample a long exposure (12 sub-frames, 432° shutter), held 3–4 frames.
//            A still figure on the left third stays sharp. Handheld drift + 4° dutch tilt, stepped with the picture.
//   0.8–2.6  the timestamp flips digit by digit (23:59:57 → …); the title types in as warm-white subtitles
//   2.0–4.0  three neon signs ignite on the beats 2.0 / 2.4 / 2.8 and spill their colour onto the figure: outline,
//            storyboard (green), draft (a red neon film reel); the middle sign buzzes at 3.2, the cup comes up at 3.6
//   4.0–5.0  step-smear cut: the whole frame goes step-printed on a fast pan; at the longest trail it cuts to a
//            red freeze-frame (one long exposure held still)
// Subtitles and the timestamp are drawn after the smear, so they never blur.

const FPS_EFF = 8, SUB = 12, SHUTTER = 1.2;
let L = null;
export const fonts = ["DIN Condensed", "Avenir Next Condensed", "Songti SC"];

export async function setup(ctx, tokens, lib) {
  const r = lib.rng(5);
  const crowd = Array.from({ length: 15 }, (_, i) => {
    const z = r(), dir = r() < 0.75 ? -1 : 1;
    return { z, dir, x0: r() * 2400 - 240, v: (260 + 520 * z) * (0.8 + r() * 0.4), h: 170 + 230 * z, rim: r() < 0.7 ? "g" : "o", seed: i };
  }).sort((a, b) => a.z - b.z);
  // traffic: head/tail lights crossing fast behind the crowd → the long light trails
  const lights = Array.from({ length: 26 }, (_, i) => ({ x0: r() * 2600, y: 585 + r() * 90, v: (1500 + r() * 1100) * (i % 3 ? -1 : 1), r: 7 + r() * 7, c: ["accent", "extra.1", "extra.0", "fg"][i % 4] }));
  // building facades: regular window grids, some lit
  const windows = [];
  for (let b = 0; b < 7; b++) {
    const bx = -200 + b * 330 + r() * 60, bw = 200 + r() * 90, top = 90 + r() * 180, cols = Math.floor(bw / 40), rows = Math.floor((520 - top) / 46);
    for (let i = 0; i < cols; i++) for (let j = 0; j < rows; j++) if (r() < 0.38) windows.push({ x: bx + 10 + i * 40, y: top + 12 + j * 46, w: 24, h: 26, c: r() < 0.7 ? "extra.0" : "extra.1" });
  }
  L = { crowd, lights, windows };
}

const hand = (lib, tt) => ({ x: lib.noise1(tt * 1.1, 3) * 10, y: lib.noise1(tt * 0.9, 4) * 8, r: (4 + lib.noise1(tt * 1.4, 5) * 0.6) * Math.PI / 180 });
function camera(ctx, lib, tt, panX = 0) {
  const { W, H } = lib, h = hand(lib, tt);
  ctx.translate(W / 2, H / 2); ctx.rotate(h.r); ctx.scale(1.12, 1.12); ctx.translate(-W / 2 + h.x + panX, -H / 2 + h.y);
}

// ───────── world layers ─────────
function background(ctx, lib, tokens) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, "#071010"); g.addColorStop(0.55, C("extra.2")); g.addColorStop(0.62, "#0c2a24"); g.addColorStop(1, "#050a0a");
  ctx.fillStyle = g; ctx.fillRect(-600, -300, W + 1200, H + 600);
  for (const w of L.windows) { ctx.fillStyle = lib.rgba(C(w.c), 0.16); ctx.fillRect(w.x + 4, w.y + 4, w.w - 8, w.h - 8); }
  // a green fluorescent strip above the street and a red tube far off: the key light is green in this shot
  ctx.save(); ctx.shadowColor = C("extra.0"); ctx.shadowBlur = 40; ctx.fillStyle = lib.mixColor(C("extra.0"), "#ffffff", 0.35);
  ctx.fillRect(-300, 540, W + 600, 5); ctx.restore();
  ctx.save(); ctx.globalCompositeOperation = "screen";
  const pool = ctx.createRadialGradient(W * 0.45, 560, 0, W * 0.45, 560, 900); pool.addColorStop(0, lib.rgba(C("extra.0"), 0.22)); pool.addColorStop(1, lib.rgba(C("extra.0"), 0));
  ctx.fillStyle = pool; ctx.fillRect(-300, 0, W + 600, H); ctx.restore();
}
function trails(ctx, lib, tokens, t0, t1) { // point lights under a long shutter = continuous streaks
  const C = (k) => lib.color(tokens, k);
  const wrap = (x) => ((x % 2600) + 2600) % 2600 - 340;
  ctx.save(); ctx.lineCap = "round"; ctx.globalCompositeOperation = "lighter";
  for (const l of L.lights) {
    const xa = wrap(l.x0 + l.v * t0), d = l.v * (t1 - t0), xb = xa + d;
    ctx.strokeStyle = lib.mixColor(C(l.c), "#ffffff", 0.18); ctx.shadowColor = C(l.c); ctx.shadowBlur = 20;
    ctx.lineWidth = l.r * 1.6; ctx.globalAlpha = 0.85;
    ctx.beginPath(); ctx.moveTo(xa, l.y); ctx.lineTo(Math.abs(d) < 1 ? xa + 0.5 : xb, l.y); ctx.stroke();
  }
  ctx.restore();
}
function stream(ctx, lib, tokens, ts) {       // the crowd (sampled; its smear comes from accumulation)
  const C = (k) => lib.color(tokens, k);
  const wrap = (x) => ((x % 2600) + 2600) % 2600 - 340;
  ctx.save();
  for (const p of L.crowd) {
    const x = wrap(p.x0 + p.dir * p.v * ts), base = 700 + p.z * 330, h = p.h, w = h * 0.3;
    ctx.fillStyle = "#040808";
    ctx.beginPath(); ctx.roundRect(x - w / 2, base - h * 0.82, w, h * 0.82, w * 0.4); ctx.fill();
    ctx.beginPath(); ctx.arc(x, base - h * 0.9, w * 0.3, 0, lib.TAU); ctx.fill();
    ctx.fillStyle = lib.rgba(p.rim === "g" ? C("extra.0") : C("extra.1"), 0.8);            // rim light on one side
    ctx.fillRect(x + w / 2 - 4, base - h * 0.78, 4, h * 0.7);
  }
  ctx.restore();
}
function subject(ctx, lib, tokens, t) {        // the still figure: profile facing the signs, coat collar up, a paper cup
  const C = (k) => lib.color(tokens, k);
  const x = 430, base = 1030;
  const raise = lib.ease.inOutSine(lib.seg(t, 3.5, 3.75)) * 34;                 // 3.6 s: the cup comes up to the lips
  const P = new Path2D();
  P.moveTo(x - 190, base);                                                      // coat: back, shoulders, raised collar
  P.bezierCurveTo(x - 190, base - 250, x - 170, base - 400, x - 118, base - 430);
  P.lineTo(x - 70, base - 492); P.lineTo(x - 30, base - 456);                     // collar point at the nape
  P.bezierCurveTo(x - 30, base - 470, x + 10, base - 470, x + 28, base - 452);
  P.lineTo(x + 56, base - 470); P.lineTo(x + 70, base - 420);                     // collar front
  P.bezierCurveTo(x + 120, base - 400, x + 150, base - 330, x + 158, base);
  P.closePath();
  const H = new Path2D();                                                       // head in profile: brow, nose, lips, chin
  H.moveTo(x - 40, base - 470);
  H.bezierCurveTo(x - 86, base - 520, x - 80, base - 620, x - 10, base - 640);   // back of skull / hair
  H.bezierCurveTo(x + 50, base - 650, x + 76, base - 610, x + 74, base - 580);   // crown to brow
  H.lineTo(x + 80, base - 560); H.lineTo(x + 98, base - 530); H.lineTo(x + 80, base - 522);   // nose
  H.lineTo(x + 84, base - 506); H.lineTo(x + 76, base - 498); H.lineTo(x + 80, base - 486);   // lips
  H.bezierCurveTo(x + 76, base - 468, x + 56, base - 462, x + 36, base - 466);   // chin, jaw
  H.lineTo(x + 20, base - 452); H.closePath();
  ctx.save();
  ctx.fillStyle = "#030606"; ctx.fill(P); ctx.fill(H);
  // arm and cup
  const cx = x + 132, cy = base - 330 - raise;
  ctx.beginPath(); ctx.moveTo(x + 60, base - 360); ctx.quadraticCurveTo(x + 150, base - 240, cx - 6, cy + 34); ctx.lineTo(cx + 18, cy + 30); ctx.quadraticCurveTo(x + 176, base - 230, x + 96, base - 330); ctx.closePath(); ctx.fill();
  ctx.fillStyle = lib.mixColor(C("fg"), C("extra.0"), 0.25);
  ctx.beginPath(); ctx.moveTo(cx - 18, cy - 30); ctx.lineTo(cx + 22, cy - 30); ctx.lineTo(cx + 17, cy + 30); ctx.lineTo(cx - 13, cy + 30); ctx.closePath(); ctx.fill();
  ctx.fillStyle = "#0b1717"; ctx.fillRect(cx - 20, cy - 36, 44, 8);
  ctx.strokeStyle = lib.rgba(C("fg"), 0.35); ctx.lineWidth = 3; ctx.lineCap = "round";            // steam (seeded wisps, drifting)
  for (let k = 0; k < 2; k++) { ctx.beginPath(); for (let i = 0; i <= 12; i++) { const yy = cy - 44 - i * 9, xx = cx + k * 12 + Math.sin(i * 0.6 + t * 3 + k) * 7; i ? ctx.lineTo(xx, yy) : ctx.moveTo(xx, yy); } ctx.stroke(); }
  // rim light: red on the face (warmth), green on the back; the signs' colour spills onto the front as they light
  const spill = [2.0, 2.4].reduce((m, ts) => Math.max(m, lib.seg(t, ts, ts + 0.2)), 0), red = lib.seg(t, 2.8, 3.0);
  ctx.lineWidth = 5; ctx.shadowBlur = 18;
  ctx.strokeStyle = C("accent"); ctx.shadowColor = C("accent"); ctx.globalAlpha = 0.75 + 0.25 * red;
  ctx.save(); ctx.beginPath(); ctx.rect(x + 34, base - 700, 120, 260); ctx.clip(); ctx.stroke(H); ctx.restore();   // rim on the face side only
  ctx.strokeStyle = C("extra.0"); ctx.shadowColor = C("extra.0"); ctx.globalAlpha = 0.5 + 0.4 * spill;
  ctx.save(); ctx.beginPath(); ctx.rect(x - 220, base - 700, 190, 700); ctx.clip(); ctx.stroke(P); ctx.restore();
  ctx.shadowBlur = 0; ctx.globalAlpha = 1;
  ctx.save(); ctx.clip(P); const g = ctx.createRadialGradient(x + 200, base - 520, 0, x + 200, base - 520, 380);
  g.addColorStop(0, lib.rgba(lib.mixColor(C("extra.0"), C("accent"), red), 0.32 * Math.max(spill, red))); g.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = g; ctx.fillRect(x - 250, base - 700, 600, 700); ctx.restore();
  ctx.restore();
}
function signs(ctx, lib, tokens, t) {
  const C = (k) => lib.color(tokens, k);
  const xs = [820, 1150, 1480], y = 250;
  xs.forEach((x, k) => {
    const t0 = 2.0 + k * 0.4, f = lib.frame(t) - lib.frame(t0);
    if (f < 0) return;
    let on = f > 6 ? 1 : [1, 0, 0.6, 0, 1, 0.3, 1][f];
    if (k === 1) { const b = lib.frame(t) - 96; if (b >= 0 && b < 5) on = [0.2, 1, 0.1, 0.8, 1][b]; }        // 3.2 s: the middle sign buzzes
    const col = k === 2 ? C("accent") : C("extra.0");
    ctx.save();
    ctx.fillStyle = "#061010"; ctx.strokeStyle = "#1b2b2b"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(x - 120, y - 80, 240, 160, 10); ctx.fill(); ctx.stroke();
    ctx.globalAlpha = 0.25 + 0.75 * on; ctx.strokeStyle = lib.mixColor(col, "#ffffff", 0.35 * on); ctx.lineWidth = 7; ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.shadowColor = col; ctx.shadowBlur = 26 * on;
    ctx.beginPath();
    if (k === 0) for (let j = 0; j < 3; j++) { ctx.moveTo(x - 70, y - 40 + j * 40); ctx.lineTo(x + (j === 2 ? 20 : 70), y - 40 + j * 40); }
    else if (k === 1) for (let j = -1; j <= 1; j++) ctx.rect(x + j * 62 - 24, y - 40, 48, 80);
    else {                                                        // draft: a red neon film reel
      ctx.moveTo(x + 52, y); ctx.arc(x, y, 52, 0, lib.TAU);
      for (let j = 0; j < 5; j++) { const a = j / 5 * lib.TAU - Math.PI / 2, cx = x + Math.cos(a) * 28, cy = y + Math.sin(a) * 28; ctx.moveTo(cx + 10, cy); ctx.arc(cx, cy, 10, 0, lib.TAU); }
      ctx.moveTo(x + 52, y + 40); ctx.lineTo(x + 100, y + 48);
    }
    ctx.stroke(); ctx.stroke();
    ctx.restore();
  });
}
function occluder(ctx, lib) {                 // out-of-focus door frame, right edge + lintel
  const { W, H } = lib;
  ctx.save(); ctx.filter = "blur(16px)"; ctx.fillStyle = "#020404";
  ctx.fillRect(W - 170, -100, 400, H + 200); ctx.fillRect(-200, -120, W + 400, 150);
  ctx.restore();
}
function labels(ctx, lib, tokens, t) {        // sign captions (screen space, sharp)
  const C = (k) => lib.color(tokens, k);
  [820, 1150, 1480].forEach((x, k) => {
    const a = lib.seg(t, 2.05 + k * 0.4, 2.2 + k * 0.4);
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C("fg");
    ctx.shadowColor = "rgba(0,0,0,0.9)"; ctx.shadowBlur = 6;
    lib.setFont(ctx, tokens, "body", 28, { weight: 500, stretch: "condensed" }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), x, 392, { align: "center", tracking: 4 });
    lib.setFont(ctx, tokens, "zh", 46, { weight: 400 }); lib.drawText(ctx, lib.MOTIF[k].zh, x, 452, { align: "center", tracking: 6 });
    ctx.restore();
  });
}

// ───────── frame ─────────
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  if (t < 4.0) {
    const tq = Math.floor(lib.frame(t) * FPS_EFF / 30 + 1e-9) / FPS_EFF;        // the step-printed clock
    ctx.save(); camera(ctx, lib, tq); background(ctx, lib, tokens); signs(ctx, lib, tokens, t); trails(ctx, lib, tokens, tq, tq + SHUTTER / FPS_EFF); ctx.restore();
    ctx.drawImage(accumulate(lib, (x, ts) => { camera(x, lib, tq); stream(x, lib, tokens, ts); }, tq, SHUTTER), 0, 0);
    ctx.save(); camera(ctx, lib, tq); subject(ctx, lib, tokens, t); ctx.restore();
    occluder(ctx, lib);
    halation(ctx, lib, tokens);
    labels(ctx, lib, tokens, t);
    overlay(ctx, t, tokens, lib, { clock: 0 });
  } else if (t < 4.34) {                        // step-smear: the whole frame on a fast pan, shutter grows
    const tq = Math.floor(lib.frame(t) * FPS_EFF / 30 + 1e-9) / FPS_EFF, sh = SHUTTER * (1 + 3 * lib.seg(t, 4.0, 4.34));
    const pan = (ts) => -1800 * Math.pow(lib.seg(ts, 3.95, 4.5), 2);
    ctx.drawImage(accumulate(lib, (x, ts) => {
      camera(x, lib, tq, pan(ts)); background(x, lib, tokens); signs(x, lib, tokens, 3.99); trails(x, lib, tokens, ts, ts + 0.03); stream(x, lib, tokens, ts); subject(x, lib, tokens, 3.99);
    }, tq, sh), 0, 0);
    occluder(ctx, lib);
    overlay(ctx, t, tokens, lib, { clock: 0 });
  } else {                                      // freeze: one long exposure, held, red key light
    ctx.drawImage(lib.offscreen("nsp_freeze", (x) => {
      x.drawImage(accumulate(lib, (y, ts) => { camera(y, lib, 4.25, -300); background(y, lib, tokens); stream(y, lib, tokens, ts); }, 4.25, 4.5), 0, 0);
      x.globalCompositeOperation = "multiply"; x.fillStyle = "#ff6a6e"; x.fillRect(0, 0, W, H);
      x.globalCompositeOperation = "source-over"; x.save(); camera(x, lib, 4.25, -300); trails(x, lib, tokens, 4.25, 4.25 + 0.5); x.restore();
      x.globalCompositeOperation = "screen"; x.fillStyle = lib.rgba(lib.color(tokens, "accent"), 0.14); x.fillRect(0, 0, W, H);
    }), 0, 0);
    occluder(ctx, lib);
    overlay(ctx, t, tokens, lib, { end: true });
  }
  // hook: the street lights flicker on at 0.1 s (frames 0–2 dark, 3 on, 4 dim, 5 on)
  const f = lib.frame(t), dark = f < 3 ? 0.82 : f === 4 ? 0.55 : 0;
  if (dark > 0) { ctx.fillStyle = `rgba(0,3,3,${dark})`; ctx.fillRect(0, 0, W, H); }
  lib.grain(ctx, t, { amount: 0.11, fps: 24, seed: 8 });
  lib.vignette(ctx, { strength: 0.5, inner: 0.45, color: "#000000" });
}

/** Average SUB samples of draw(ctx, ts) across [t0, t0 + shutter/FPS_EFF] — premultiplied sum with "lighter". */
function accumulate(lib, draw, t0, shutter) {
  const acc = lib.layer("nsp_acc");
  for (let k = 0; k < SUB; k++) {
    const s = lib.layer("nsp_s"); draw(s, t0 + (k / SUB) * shutter / FPS_EFF);
    acc.globalCompositeOperation = "lighter"; acc.globalAlpha = 1 / SUB; acc.drawImage(s.canvas, 0, 0);
  }
  return acc.canvas;
}
function halation(ctx, lib, tokens) {         // red-shifted bloom from the brightest light only
  ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = 0.18;
  ctx.fillStyle = lib.rgba(lib.color(tokens, "accent"), 0.5); ctx.filter = "blur(30px)";
  ctx.fillRect(1480 - 110, 180, 220, 140);
  ctx.restore();
}

function overlay(ctx, t, tokens, lib, { end = false } = {}) {
  const C = (k) => lib.color(tokens, k), { W } = lib;
  // timestamp: seconds tick over midnight (on the half second); the digits that change flip over 2 frames
  const sec = 57 + Math.floor(t + 0.5 + 1e-9), prevSec = 57 + Math.floor(t + 0.5 - 2 / 30 + 1e-9);
  const fmt = (s) => { const m = Math.floor(s / 60), ss = s % 60; return m >= 1 ? `00:00:${String(ss).padStart(2, "0")}` : `23:59:${String(ss).padStart(2, "0")}`; };
  const now = fmt(sec), before = t < 2 / 30 ? now : fmt(prevSec);
  ctx.save(); ctx.fillStyle = C("fg"); ctx.shadowColor = "rgba(0,0,0,0.8)"; ctx.shadowBlur = 8;
  lib.setFont(ctx, tokens, "display", 76, { weight: 700, stretch: "condensed" });
  const lay = lib.layoutText(ctx, now, { x: 150, y: 176, tracking: 5 });
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const flipping = now[i] !== before[i];
    return flipping ? { sy: 0.35, dy: -12, alpha: 0.7 } : {};
  });
  ctx.restore();
  if (end) {
    ctx.save(); ctx.fillStyle = C("fg"); ctx.shadowColor = "rgba(0,0,0,0.85)"; ctx.shadowBlur = 10;
    lib.setFont(ctx, tokens, "zh", 72, { weight: 400 }); lib.drawText(ctx, "霓虹抽帧", W / 2 + 110, 872, { align: "center", tracking: 72 * 0.12 });
    lib.setFont(ctx, tokens, "body", 44, { weight: 500, stretch: "condensed" }); lib.drawText(ctx, "NEON STEP-PRINT", W / 2 + 110, 950, { align: "center", tracking: 44 * 0.12 });
    ctx.restore(); return;
  }
  // subtitles: typed in, warm white, never smeared; a soft dark band under them keeps them legible over the smear
  const zh = lib.typewriter(lib.TITLE_ZH, t, { start: 0.95, cps: 11 }), en = lib.typewriter(lib.TITLE_EN, t, { start: 1.35, cps: 22 });
  const band = lib.seg(t, 0.85, 1.1), cxs = W / 2 + 110;
  if (band > 0) { const g = ctx.createLinearGradient(0, 760, 0, 1080); g.addColorStop(0, "rgba(2,6,6,0)"); g.addColorStop(0.4, `rgba(2,6,6,${0.55 * band})`); g.addColorStop(1, `rgba(2,6,6,${0.7 * band})`); ctx.fillStyle = g; ctx.fillRect(560, 760, W - 560, 320); }
  ctx.save(); ctx.fillStyle = C("fg"); ctx.shadowColor = "rgba(0,0,0,0.9)"; ctx.shadowBlur = 10;
  lib.setFont(ctx, tokens, "zh", 78, { weight: 400 });
  const zw = lib.layoutText(ctx, lib.TITLE_ZH, { tracking: 78 * 0.08 }).width;
  lib.drawText(ctx, zh, cxs - zw / 2, 872, { tracking: 78 * 0.08 });
  lib.setFont(ctx, tokens, "body", 66, { weight: 500, stretch: "condensed" });
  const ew = lib.layoutText(ctx, lib.TITLE_EN, { tracking: 2 }).width;
  lib.drawText(ctx, en, cxs - ew / 2, 958, { tracking: 2 });
  ctx.restore();
}

// foley (events.json is generated from this list; times are the same ones the scene uses)
const px = (x) => Math.round((x / 960 - 1) * 100) / 100;
export const FOLEY = [
  { t: 0.1, sfx: "toggle", gain_db: -8, pan: 0 },                                                         // street lights flicker on
  ...[0.5, 1.5, 2.5, 3.5].map((t) => ({ t, sfx: "tick", gain_db: -12, pan: px(250) })),                  // the timestamp flips
  { t: 0.95, sfx: "typing", gain_db: -18, pan: px(1070) },                                               // subtitles type in
  ...[2.0, 2.4, 2.8].map((t, k) => ({ t, sfx: "toggle", gain_db: -8, pan: px([820, 1150, 1480][k]) })),   // signs ignite
  { t: 3.2, sfx: "glitch", gain_db: -16, pan: px(1150) },                                                // the middle sign buzzes
  { t: 4.2, sfx: "whoosh", gain_db: -6, pan: -0.3 }, { t: 4.34, sfx: "shutter", gain_db: -6, pan: 0 },    // smear pan; freeze
];
