// symmetry-pastel swatch — centred, planimetric pastel storybook.
//   0.0–0.8  a symmetrical pink room trucks in from the right on a rail (inOutQuad) and stops dead on the centre line
//   0.8–2.6  a chapter card cuts in (ivory, double rule); its lines appear one by one, 150 ms apart
//   2.0–4.0  three framed pictures drop onto their nails, left → right: outline, storyboard, draft (carmine);
//            each has a brass-style plaque
//   4.0–5.0  a 9-frame whip pan to the next chapter (mint), which is centred on the same axis
// Everything is laid out from cx = W/2 and mirrored.

let L = null;
export const fonts = ["Futura", "Baskerville", "Songti SC"];

export async function setup(ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  L = {
    cx: lib.W / 2,
    ch1: { wall: C("bg"), trim: C("extra.0"), accent: C("accent"), label: "CHAPTER ONE" },
    ch2: { wall: C("extra.2"), trim: C("extra.3"), accent: C("extra.4"), label: "CHAPTER TWO" },
    frames: [-420, 0, 420],
  };
}

const INK = (lib, tokens) => lib.color(tokens, "fg");
const IVORY = (lib, tokens) => lib.color(tokens, "extra.1");

export function renderAt(t, ctx, tokens, lib) {
  if (t < 4.0) chapterOne(ctx, t, tokens, lib);
  else lib.whip(ctx, lib.seg(t, 4.0, 4.3), (x) => chapterOne(x, 3.99, tokens, lib), (x) => chapterTwo(x, t, tokens, lib),
    { dir: [-1, 0], duration: 0.3, shutter: 0.9, ease: lib.bezier(0.7, 0, 0.3, 1) });
  lib.grain(ctx, t, { amount: 0.05, fps: 12, seed: 4 });
}

// ───────── the room (mirrored about cx) ─────────
function room(ctx, lib, tokens, P, dx = 0) {
  const { W, H } = lib, cx = L.cx + dx, ink = INK(lib, tokens), ivory = IVORY(lib, tokens);
  ctx.fillStyle = P.wall; ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(dx, 0);
  // wainscot + rules
  ctx.fillStyle = P.trim; ctx.fillRect(-300, 944, W + 600, H - 944);
  ctx.fillStyle = ink; ctx.fillRect(-300, 940, W + 600, 4);
  ctx.fillStyle = ivory; ctx.fillRect(-300, 954, W + 600, 3);
  // pilasters, cornice and a centred lamp — all symmetric
  for (const s of [-1, 1]) {
    const x = L.cx + s * 866;
    ctx.fillStyle = P.trim; ctx.fillRect(x - 46, 0, 92, 944);
    ctx.fillStyle = ivory; ctx.fillRect(x - 46, 0, 8, 944); ctx.fillRect(x + 38, 0, 8, 944);
    ctx.fillStyle = ink; ctx.fillRect(x - 60, 890, 120, 10);
  }
  ctx.fillStyle = P.trim; ctx.fillRect(-300, 0, W + 600, 34);
  ctx.fillStyle = ink; ctx.fillRect(-300, 34, W + 600, 3);
  ctx.restore();
  return cx;
}

function chapterCard(ctx, t, tokens, lib, P, cx, { t0, lines = true, title = lib.TITLE_EN, zh = lib.TITLE_ZH }) {
  const ink = INK(lib, tokens), ivory = IVORY(lib, tokens);
  const w = 1080, h = 400, x = cx - w / 2, y = 88;
  ctx.save();
  ctx.fillStyle = "rgba(43,45,92,0.12)"; ctx.fillRect(x + 8, y + 10, w, h);          // flat drop shadow (no blur)
  ctx.fillStyle = ivory; ctx.fillRect(x, y, w, h);
  ctx.strokeStyle = ink; ctx.lineWidth = 3; ctx.strokeRect(x + 14, y + 14, w - 28, h - 28);
  ctx.lineWidth = 1; ctx.strokeRect(x + 26, y + 26, w - 52, h - 52);
  const line = (k) => (lines ? lib.easeOf(tokens.ease.enter)(lib.seg(t, t0 + k * 0.15, t0 + k * 0.15 + 8 / 30)) : 1);
  ctx.fillStyle = ink;
  let a = line(0);
  if (a > 0) { ctx.globalAlpha = a; lib.setFont(ctx, tokens, "display", 30, { weight: 500 }); lib.drawText(ctx, P.label, cx, y + 96, { align: "center", tracking: 30 * 0.2 }); }
  a = line(1);
  if (a > 0) { ctx.globalAlpha = a; lib.setFont(ctx, tokens, "display", 86, { weight: 700 }); lib.drawText(ctx, title, cx, y + 214, { align: "center", tracking: -86 * 0.01 }); }
  a = line(2);
  if (a > 0) { ctx.globalAlpha = a; ctx.fillStyle = P.accent; ctx.fillRect(cx - 90 * a, y + 250, 180 * a, 5); ctx.fillStyle = ink; }
  a = line(3);
  if (a > 0) { ctx.globalAlpha = a; lib.setFont(ctx, tokens, "zh", 58, { weight: 700 }); lib.drawText(ctx, zh, cx, y + 336, { align: "center", tracking: 58 * 0.08 }); }
  ctx.restore();
}

function picture(ctx, t, tokens, lib, P, cx, k) {
  const ink = INK(lib, tokens), ivory = IVORY(lib, tokens);
  const t0 = 2.0 + k * 0.15, u = lib.easeOf(tokens.ease.enter)(lib.seg(t, t0, t0 + 10 / 30));
  if (t < t0) return;
  const x = cx + L.frames[k], w = 300, h = 216, top = 572 - (1 - u) * 70, a = lib.clamp(u * 3);
  ctx.save(); ctx.globalAlpha = a;
  // nail + picture wire (symmetric triangle)
  ctx.strokeStyle = ink; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(x - 110, top + 6); ctx.lineTo(x, top - 54); ctx.lineTo(x + 110, top + 6); ctx.stroke();
  ctx.fillStyle = ink; ctx.beginPath(); ctx.arc(x, top - 56, 6, 0, lib.TAU); ctx.fill();
  // frame: trim colour, navy hairline, ivory mat
  ctx.fillStyle = "rgba(43,45,92,0.12)"; ctx.fillRect(x - w / 2 + 7, top + 9, w, h);
  ctx.fillStyle = P.trim; ctx.fillRect(x - w / 2, top, w, h);
  ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.strokeRect(x - w / 2 + 1, top + 1, w - 2, h - 2);
  ctx.fillStyle = ivory; ctx.fillRect(x - w / 2 + 22, top + 22, w - 44, h - 44);
  ctx.strokeRect(x - w / 2 + 22, top + 22, w - 44, h - 44);
  // the picture itself, centred
  const cy = top + h / 2;
  ctx.fillStyle = ink; ctx.strokeStyle = ink; ctx.lineWidth = 6; ctx.lineCap = "butt";
  if (k === 0) [[-80, 80], [-80, 80], [-80, 30]].forEach(([a0, a1], j) => { ctx.beginPath(); ctx.moveTo(x + a0, cy - 40 + j * 40); ctx.lineTo(x + a1, cy - 40 + j * 40); ctx.stroke(); });
  else if (k === 1) for (let j = -1; j <= 1; j++) { ctx.lineWidth = 4; ctx.strokeRect(x + j * 70 - 28, cy - 44, 56, 88); }
  else { ctx.fillStyle = P.accent; ctx.beginPath(); ctx.moveTo(x - 36, cy - 46); ctx.lineTo(x + 50, cy); ctx.lineTo(x - 36, cy + 46); ctx.closePath(); ctx.fill(); }
  // plaque
  const py = top + h + 26, pw = 240, ph = 118;
  ctx.fillStyle = ivory; ctx.fillRect(x - pw / 2, py, pw, ph);
  ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.strokeRect(x - pw / 2 + 6, py + 6, pw - 12, ph - 12);
  ctx.fillStyle = ink;
  lib.setFont(ctx, tokens, "display", 24, { weight: 500 }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), x, py + 42, { align: "center", tracking: 24 * 0.2 });
  lib.setFont(ctx, tokens, "zh", 46, { weight: 400 }); lib.drawText(ctx, lib.MOTIF[k].zh, x, py + 96, { align: "center", tracking: 46 * 0.2 });
  ctx.restore();
}

function chapterOne(ctx, t, tokens, lib) {
  // establishing: the room trucks in from the right on a rail and stops dead, centred
  const dx = 260 * (1 - lib.bezier(0.45, 0, 0.55, 1)(lib.seg(t, 0.1, 0.8)));
  const cx = room(ctx, lib, tokens, L.ch1, dx);
  if (t >= 0.8) chapterCard(ctx, t, tokens, lib, L.ch1, cx, { t0: 0.82 });
  for (let k = 0; k < 3; k++) picture(ctx, t, tokens, lib, L.ch1, cx, k);
}

function chapterTwo(ctx, t, tokens, lib) {
  const cx = room(ctx, lib, tokens, L.ch2, 0);
  chapterCard(ctx, t, tokens, lib, L.ch2, cx, { t0: 0, lines: false, title: "Symmetry Pastel", zh: "对称粉彩绘本" });
  // the next chapter's single object, hung dead centre
  const ink = INK(lib, tokens), x = cx, top = 600;
  ctx.save();
  ctx.fillStyle = L.ch2.trim; ctx.beginPath(); ctx.arc(x, top + 120, 120, 0, lib.TAU); ctx.fill();
  ctx.strokeStyle = ink; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = IVORY(lib, tokens); ctx.beginPath(); ctx.arc(x, top + 120, 96, 0, lib.TAU); ctx.fill(); ctx.stroke();
  ctx.fillStyle = L.ch2.accent; ctx.beginPath(); ctx.moveTo(x - 30, top + 82); ctx.lineTo(x + 44, top + 120); ctx.lineTo(x - 30, top + 158); ctx.closePath(); ctx.fill();
  ctx.restore();
}
