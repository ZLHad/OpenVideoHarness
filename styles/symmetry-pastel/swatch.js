// symmetry-pastel swatch — a centred, planimetric pastel dollhouse.
//   0.0–0.8  hook: frame 0 is a closed carmine stage curtain; it parts symmetrically from the centre line (0.03–0.42 s)
//            on the swish, revealing the cutaway room (floor slabs, side walls, windows, sconces) already trucking in
//            from the right on a rail (inOutQuad); it stops dead on the centre line
//   0.8–2.6  a chapter card cuts in (ivory, double rule, ~56 % of the width); its lines appear 150 ms apart; the
//            curtains draw open at 1.5 s; a slow push 1.00 → 1.03 runs from 1.2 s to 4.0 s
//   2.0–4.0  three framed pictures drop onto their nails on the beats 2.0 / 2.4 / 2.8 and swing to rest: outline,
//            storyboard, draft (a carmine rosette); the plaques flip at 3.2; both sconces light at 3.6
//   4.0–5.0  a 9-frame whip pan to the next chapter (mint), centred on the same axis
// Everything is laid out from cx = W/2 and mirrored.

let L = null;
export const fonts = ["Futura", "Baskerville", "Songti SC"];

export async function setup(ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  L = {
    cx: lib.W / 2,
    ch1: { wall: C("bg"), trim: C("extra.0"), accent: C("accent"), curtain: C("accent"), label: "CHAPTER ONE" },
    ch2: { wall: C("extra.2"), trim: C("extra.3"), accent: C("extra.4"), curtain: C("extra.4"), label: "CHAPTER TWO" },
    frames: [-420, 0, 420],
  };
}
const INK = (lib, tokens) => lib.color(tokens, "fg");
const IVORY = (lib, tokens) => lib.color(tokens, "extra.1");

export const CURTAIN = [1 / 30, 0.42];                         // frame 0 closed; parts from the centre line (ease-out: ~40 % open at 0.1 s)
export function renderAt(t, ctx, tokens, lib) {
  if (t < 4.0) { chapterOne(ctx, t, tokens, lib); if (t < CURTAIN[1]) curtain(ctx, t, tokens, lib); }
  else lib.whip(ctx, lib.seg(t, 4.0, 4.3), (x) => chapterOne(x, 3.99, tokens, lib), (x) => chapterTwo(x, t, tokens, lib),
    { dir: [-1, 0], duration: 0.3, shutter: 0.9, ease: lib.bezier(0.7, 0, 0.3, 1) });
  lib.grain(ctx, t, { amount: 0.05, fps: 12, seed: 4 });
}

// ───────── the hook: a symmetrical carmine curtain that parts from the centre line ─────────
function curtain(ctx, t, tokens, lib) {
  const { W, H } = lib, u = lib.ease.outCubic(lib.seg(t, CURTAIN[0], CURTAIN[1])), ink = INK(lib, tokens), ivory = IVORY(lib, tokens);
  const col = lib.color(tokens, "accent"), off = u * (W / 2 + 80);
  for (const s of [-1, 1]) {
    ctx.save(); ctx.translate(W / 2 + s * off, 0); ctx.scale(s, 1);          // right panel is the mirror of the left
    const g = ctx.createLinearGradient(-W / 2, 0, 0, 0);
    for (let k = 0; k <= 16; k++) g.addColorStop(k / 16, k % 2 ? col : lib.mixColor(col, "#000000", 0.28));   // velvet folds
    ctx.fillStyle = g; ctx.fillRect(-W / 2 - 80, 0, W / 2 + 80, H);
    ctx.fillStyle = ivory; ctx.fillRect(-W / 2 - 80, H - 70, W / 2 + 80, 14);                                    // hem trim
    ctx.fillStyle = ink; ctx.fillRect(-4, 0, 4, H);                                                              // the meeting edge
    ctx.restore();
  }
  ctx.fillStyle = lib.mixColor(col, "#000000", 0.35); ctx.fillRect(0, 0, W, 64);                                // valance
  ctx.fillStyle = ivory; ctx.fillRect(0, 58, W, 6);
}

// ───────── the cutaway room (mirrored about cx) ─────────
function room(ctx, t, lib, tokens, P, dx = 0, { curtains = 1, sconces = 0 } = {}) {
  const { W, H } = lib, ink = INK(lib, tokens), ivory = IVORY(lib, tokens);
  ctx.fillStyle = P.wall; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(dx, 0);
  // cutaway section: ceiling slab, floor slab, side walls (hatched), like a sliced dollhouse
  const slab = (x, y, w, h) => {
    ctx.fillStyle = ivory; ctx.fillRect(x, y, w, h);
    ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip(); ctx.strokeStyle = lib.rgba(ink, 0.22); ctx.lineWidth = 2;
    for (let k = -h; k < w + h; k += 22) { ctx.beginPath(); ctx.moveTo(x + k, y + h); ctx.lineTo(x + k + h, y); ctx.stroke(); }
    ctx.restore(); ctx.strokeStyle = ink; ctx.lineWidth = 3; ctx.strokeRect(x, y, w, h);
  };
  slab(-300, -4, W + 600, 40); slab(-300, 1000, W + 600, 90); slab(-60, 0, 90, 1004); slab(W - 30, 0, 90, 1004);
  ctx.fillStyle = P.trim; ctx.fillRect(30, 944, W - 60, 56); ctx.fillStyle = ink; ctx.fillRect(30, 940, W - 60, 4);
  for (const s of [-1, 1]) {
    // windows with muntins and curtains that draw open
    const wx = L.cx + s * 710, wy = 170, ww = 200, wh = 290;
    ctx.fillStyle = "#EAF3F4"; ctx.fillRect(wx - ww / 2, wy, ww, wh);
    ctx.strokeStyle = ink; ctx.lineWidth = 4; ctx.strokeRect(wx - ww / 2, wy, ww, wh);
    ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(wx, wy); ctx.lineTo(wx, wy + wh); ctx.moveTo(wx - ww / 2, wy + wh / 2); ctx.lineTo(wx + ww / 2, wy + wh / 2); ctx.stroke();
    const cw = lib.lerp(ww / 2, 26, curtains);
    ctx.fillStyle = P.curtain; ctx.fillRect(wx - ww / 2 - 8, wy - 12, cw, wh + 30); ctx.fillRect(wx + ww / 2 + 8 - cw, wy - 12, cw, wh + 30);
    ctx.fillStyle = ink; ctx.fillRect(wx - ww / 2 - 20, wy - 16, ww + 40, 6);
    // sconces below the windows
    const sx = wx, sy = 600;
    if (sconces > 0) { const g = ctx.createRadialGradient(sx, sy, 0, sx, sy, 170); g.addColorStop(0, `rgba(255,236,190,${0.75 * sconces})`); g.addColorStop(1, "rgba(255,236,190,0)"); ctx.fillStyle = g; ctx.fillRect(sx - 170, sy - 170, 340, 340); }
    ctx.fillStyle = ink; ctx.fillRect(sx - 3, sy + 10, 6, 50); ctx.fillRect(sx - 22, sy + 58, 44, 6);
    ctx.fillStyle = sconces > 0 ? lib.mixColor(ivory, "#FFE7B0", sconces) : ivory; ctx.beginPath(); ctx.moveTo(sx - 30, sy + 14); ctx.lineTo(sx + 30, sy + 14); ctx.lineTo(sx + 18, sy - 26); ctx.lineTo(sx - 18, sy - 26); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.stroke();
  }
  ctx.restore();
  return L.cx + dx;
}

function chapterCard(ctx, t, tokens, lib, P, cx, { t0, lines = true, title = lib.TITLE_EN, zh = lib.TITLE_ZH }) {
  const ink = INK(lib, tokens), ivory = IVORY(lib, tokens);
  const w = 1160, h = 410, x = cx - w / 2, y = 84;
  ctx.save();
  ctx.fillStyle = "rgba(43,45,92,0.12)"; ctx.fillRect(x + 8, y + 10, w, h);
  ctx.fillStyle = ivory; ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = ink; ctx.lineWidth = 3; ctx.strokeRect(x + 14, y + 14, w - 28, h - 28);
  ctx.lineWidth = 1; ctx.strokeRect(x + 26, y + 26, w - 52, h - 52);
  const line = (k) => (lines ? lib.easeOf(tokens.ease.enter)(lib.seg(t, t0 + k * 0.15, t0 + k * 0.15 + 8 / 30)) : 1);
  ctx.fillStyle = ink;
  let a = line(0);
  if (a > 0) { ctx.globalAlpha = a; lib.setFont(ctx, tokens, "display", 32, { weight: 500 }); lib.drawText(ctx, P.label, cx, y + 92, { align: "center", tracking: 32 * 0.2 }); }
  a = line(1);
  if (a > 0) { ctx.globalAlpha = a; lib.setFont(ctx, tokens, "display", 92, { weight: 700 }); lib.drawText(ctx, title, cx, y + 214, { align: "center", tracking: -92 * 0.01 }); }
  a = line(2);
  if (a > 0) { ctx.globalAlpha = a; ctx.fillStyle = P.accent; ctx.fillRect(cx - 90 * a, y + 250, 180 * a, 5); ctx.fillStyle = ink; }
  a = line(3);
  if (a > 0) { ctx.globalAlpha = a; lib.setFont(ctx, tokens, "zh", 64, { weight: 700 }); lib.drawText(ctx, zh, cx, y + 344, { align: "center", tracking: 64 * 0.08 }); }
  ctx.restore();
}

function picture(ctx, t, tokens, lib, P, cx, k) {
  const ink = INK(lib, tokens), ivory = IVORY(lib, tokens);
  const t0 = 2.0 + k * 0.4 - 8 / 30; if (t < t0) return;           // lands on the beat (2.0 / 2.4 / 2.8)
  const u = lib.easeOf(tokens.ease.enter)(lib.seg(t, t0, t0 + 8 / 30)), land = t0 + 8 / 30;
  const x = cx + L.frames[k], w = 300, h = 216, nailY = 516 - (1 - u) * 70, a = lib.clamp(u * 3);
  const swing = t > land ? 0.09 * Math.exp(-(t - land) * 4.2) * Math.sin((t - land) * 17) : 0;   // swings on the nail, settles
  ctx.save(); ctx.globalAlpha = a;
  ctx.translate(x, nailY); ctx.rotate(swing);
  ctx.strokeStyle = ink; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(-110, 62); ctx.lineTo(0, 0); ctx.lineTo(110, 62); ctx.stroke();
  const top = 56;
  ctx.fillStyle = "rgba(43,45,92,0.12)"; ctx.fillRect(-w / 2 + 7, top + 9, w, h);
  ctx.fillStyle = P.trim; ctx.fillRect(-w / 2, top, w, h);
  ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.strokeRect(-w / 2 + 1, top + 1, w - 2, h - 2);
  ctx.fillStyle = ivory; ctx.fillRect(-w / 2 + 22, top + 22, w - 44, h - 44); ctx.strokeRect(-w / 2 + 22, top + 22, w - 44, h - 44);
  const cy = top + h / 2;
  ctx.fillStyle = ink; ctx.strokeStyle = ink; ctx.lineWidth = 6; ctx.lineCap = "butt";
  if (k === 0) [[-80, 80], [-80, 80], [-80, 30]].forEach(([a0, a1], j) => { ctx.beginPath(); ctx.moveTo(a0, cy - 40 + j * 40); ctx.lineTo(a1, cy - 40 + j * 40); ctx.stroke(); });
  else if (k === 1) for (let j = -1; j <= 1; j++) { ctx.lineWidth = 4; ctx.strokeRect(j * 70 - 28, cy - 44, 56, 88); }
  else rosette(ctx, lib, 0, cy - 6, P.accent, ivory, ink);
  ctx.restore();
  // plaque (does not swing); flips over on 3.2 s
  ctx.save(); ctx.globalAlpha = a;
  const py = 516 + 56 + h + 26, pw = 240, ph = 118, fl = lib.seg(t, 3.2 - 5 / 30, 3.2 + 5 / 30);
  ctx.translate(x, py + ph / 2); ctx.scale(1, fl > 0 && fl < 1 ? Math.abs(Math.cos(fl * Math.PI)) : 1); ctx.translate(-x, -(py + ph / 2));
  ctx.fillStyle = ivory; ctx.fillRect(x - pw / 2, py, pw, ph);
  ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.strokeRect(x - pw / 2 + 6, py + 6, pw - 12, ph - 12);
  ctx.fillStyle = ink;
  lib.setFont(ctx, tokens, "display", 24, { weight: 500 }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), x, py + 42, { align: "center", tracking: 24 * 0.2 });
  lib.setFont(ctx, tokens, "zh", 48, { weight: 400 }); lib.drawText(ctx, lib.MOTIF[k].zh, x, py + 97, { align: "center", tracking: 48 * 0.2 });
  ctx.restore();
}
function rosette(ctx, lib, x, y, col, ivory, ink) {   // a symmetrical prize rosette: the finished draft
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = col;
  for (const s of [-1, 1]) { ctx.beginPath(); ctx.moveTo(s * 10, 10); ctx.lineTo(s * 34, 70); ctx.lineTo(s * 22, 62); ctx.lineTo(s * 14, 76); ctx.lineTo(s * -4, 16); ctx.closePath(); ctx.fill(); }
  for (let i = 0; i < 12; i++) { const a = i / 12 * lib.TAU; ctx.beginPath(); ctx.arc(Math.cos(a) * 34, Math.sin(a) * 34, 14, 0, lib.TAU); ctx.fill(); }
  ctx.fillStyle = ivory; ctx.beginPath(); ctx.arc(0, 0, 26, 0, lib.TAU); ctx.fill();
  ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = col; ctx.beginPath(); ctx.arc(0, 0, 12, 0, lib.TAU); ctx.fill();
  ctx.restore();
}

function chapterOne(ctx, t, tokens, lib) {
  const { W, H } = lib;
  const dx = 260 * (1 - lib.bezier(0.45, 0, 0.55, 1)(lib.seg(t, -0.15, 0.8)));      // already moving at frame 0
  const push = 1 + 0.03 * lib.ease.inOutSine(lib.seg(t, 1.2, 4.0));
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
  const cx = room(ctx, t, lib, tokens, L.ch1, dx, { curtains: lib.easeOf(tokens.ease.enter)(lib.seg(t, 1.5, 1.85)), sconces: lib.ease.outCubic(lib.seg(t, 3.6, 3.75)) });
  if (t >= 0.8) chapterCard(ctx, t, tokens, lib, L.ch1, cx, { t0: 0.82 });
  for (let k = 0; k < 3; k++) picture(ctx, t, tokens, lib, L.ch1, cx, k);
  ctx.restore();
}

function chapterTwo(ctx, t, tokens, lib) {
  const { W, H } = lib, k = 1 + 0.025 * lib.ease.outCubic(lib.seg(t, 4.2, 5.0));
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(k, k); ctx.translate(-W / 2, -H / 2);
  const cx = room(ctx, t, lib, tokens, L.ch2, 0, { curtains: 1, sconces: 1 });
  chapterCard(ctx, t, tokens, lib, L.ch2, cx, { t0: 0, lines: false, title: "Symmetry Pastel", zh: "对称粉彩绘本" });
  const ink = INK(lib, tokens), ivory = IVORY(lib, tokens), x = cx, cy = 720;       // the next chapter's crest, dead centre
  ctx.save();
  ctx.fillStyle = L.ch2.trim; ctx.beginPath(); ctx.arc(x, cy, 130, 0, lib.TAU); ctx.fill(); ctx.strokeStyle = ink; ctx.lineWidth = 3; ctx.stroke();
  ctx.fillStyle = ivory; ctx.beginPath(); ctx.arc(x, cy, 104, 0, lib.TAU); ctx.fill(); ctx.stroke();
  ctx.fillStyle = L.ch2.accent;                                                   // a tiny symmetrical house: the dollhouse
  ctx.beginPath(); ctx.moveTo(x - 56, cy - 4); ctx.lineTo(x, cy - 56); ctx.lineTo(x + 56, cy - 4); ctx.closePath(); ctx.fill();
  ctx.fillRect(x - 44, cy - 4, 88, 62); ctx.fillStyle = ivory; ctx.fillRect(x - 12, cy + 18, 24, 40);
  ctx.restore();
  ctx.restore();
}

// foley (events.json is generated from this list; times are the same ones the scene uses)
export const FOLEY = [
  { t: CURTAIN[0], sfx: "click", gain_db: -6, pan: 0 },                                                  // the curtain cord
  { t: (CURTAIN[0] + CURTAIN[1]) / 2, sfx: "swish_rev", gain_db: -4, pan: 0 },                            // the curtain parts
  { t: 0.82, sfx: "ding", gain_db: -10, pan: 0 },                                                         // the chapter card
  { t: 1.6, sfx: "swish_rev", gain_db: -16, pan: 0 },                                                     // curtains open
  ...[2.0, 2.4, 2.8].map((t, k) => ({ t, sfx: "tick", gain_db: -8, pan: [-0.44, 0, 0.44][k] })),         // pictures land and swing
  { t: 3.2, sfx: "toggle", gain_db: -12, pan: 0 }, { t: 3.6, sfx: "click", gain_db: -10, pan: 0 },       // plaques flip; sconces
  { t: 4.15, sfx: "whoosh", gain_db: -6, pan: 0.5 }, { t: 4.3, sfx: "ding", gain_db: -12, pan: 0 },      // whip pan; next chapter
];
