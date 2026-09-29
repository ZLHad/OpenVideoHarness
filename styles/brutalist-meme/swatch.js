// brutalist-meme swatch · 野兽派梗 (swatch grid 150 BPM: a beat is 0.4 s; every cut and punch-in lands on it)
//   0.10–0.60  a visible 12-column grid prints itself in 4 steps; the section label types in
//   0.80       HARD CUT + 2-frame punch-in (115 %): the Latin title types in on steps
//   1.60       HARD CUT + punch-in: the Chinese line types in
//   2.00–2.40  motif: three raw "screenshot" windows slam in on eighth notes, 0 px corners; the third breaks the grid (3°)
//   3.20–3.60  held breath: the frame freezes (the sound keeps a low bed; no digital silence)
//   3.60       punchline: a hand-drawn orange box around DRAFT in 3 steps + label
//   4.00–4.20  SIGNATURE TRANSITION: 5 frames of glitch (RGB split + slices), hard cut to the end frame, punch-in

const TAU = Math.PI * 2;
let L = null;

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const x0 = 96, x1 = lib.W - 96, col = (x1 - x0) / 12;
  L = { P, x0, x1, col, cards: [0, 1, 2].map((k) => ({ x: 192 + k * 558, y: 560, w: 420, h: 250 })) };
}
const punchAt = [0.8, 1.6, 2.0, 2.2, 2.4, 3.6, 4.2];   // all on the 150 BPM grid (beat 0.4 s)
function punch(t) { return punchAt.some((p) => t >= p && t < p + 2 / 30) ? 1.15 : 1; }
const stepU = (t, a, b, n) => Math.floor(Math.max(0, Math.min(1, (t - a) / (b - a))) * n + 1e-9) / n;

function grid(ctx, t, lib) {
  const P = L.P, u = stepU(t, 0.1, 0.6, 4);
  ctx.save(); ctx.strokeStyle = P("extra.0"); ctx.lineWidth = 1;
  for (let i = 0; i <= 12; i++) { const x = Math.round(L.x0 + i * L.col) + 0.5; ctx.beginPath(); ctx.moveTo(x, 54); ctx.lineTo(x, 54 + (lib.H - 108) * u); ctx.stroke(); }
  for (let j = 0; j <= 10; j++) { const y = Math.round(54 + j * 97.2) + 0.5; ctx.beginPath(); ctx.moveTo(L.x0, y); ctx.lineTo(L.x0 + (L.x1 - L.x0) * u, y); ctx.stroke(); }
  ctx.restore();
}
function label(ctx, t, tokens, lib) {
  const P = L.P, sec = t < 2.0 ? "01 / SETUP" : t < 3.6 ? "02 / MOTIF" : "03 / PUNCHLINE", t0 = t < 2.0 ? 0.2 : t < 3.6 ? 2.0 : 3.6;
  const txt = lib.typewriter(`[ ${sec} ]`, t, { start: t0, cps: 40 });
  ctx.save(); lib.setFont(ctx, tokens, "mono", 28, { weight: 700 }); ctx.fillStyle = t >= 3.6 ? P("accent") : P("extra.2");
  lib.drawText(ctx, txt, 192, 130, { tracking: 2 }); ctx.restore();
}
function cursor(ctx, t, x, y, h) { if (Math.floor(t * 4) % 2 === 0) { ctx.fillStyle = L.P("fg"); ctx.fillRect(x + 8, y - h, h * 0.55, h); } }
function titles(ctx, t, tokens, lib) {
  const P = L.P;
  if (t >= 0.8) {
    lib.setFont(ctx, tokens, "display", 150, { weight: 700 }); ctx.fillStyle = P("fg");
    const s = lib.typewriter(lib.TITLE_EN, t, { start: 0.8, cps: 45 });
    lib.drawText(ctx, s, 192, 330, { tracking: -0.03 * 150 });
    if (t < 1.6) cursor(ctx, t, 192 + ctx.measureText(s).width - 0.03 * 150 * s.length, 330, 110);
  }
  if (t >= 1.6) {
    lib.setFont(ctx, tokens, "zh", 80, { weight: 600 }); ctx.fillStyle = P("fg");
    const s = lib.typewriter(lib.TITLE_ZH, t, { start: 1.6, cps: 24 });
    lib.drawText(ctx, s, 196, 462, { tracking: 4 });
    if (t < 2.0) cursor(ctx, t, 196 + ctx.measureText(s).width + 4 * s.length, 462, 66);
  }
}
function card(ctx, t, tokens, lib, k) {
  const P = L.P, c = L.cards[k], t0 = 2.0 + k * 0.2;
  if (t < t0) return;
  ctx.save();
  if (k === 2) { ctx.translate(c.x + c.w / 2, c.y + c.h / 2); ctx.rotate(0.052); ctx.translate(-(c.x + c.w / 2), -(c.y + c.h / 2)); }   // the one element that breaks the grid
  ctx.fillStyle = "#1C1C1C"; ctx.fillRect(c.x, c.y, c.w, c.h);
  ctx.fillStyle = P("extra.2"); ctx.fillRect(c.x, c.y, c.w, 30);                                                                        // raw window chrome
  ctx.fillStyle = "#111"; for (let i = 0; i < 3; i++) ctx.fillRect(c.x + 10 + i * 20, c.y + 9, 12, 12);
  ctx.strokeStyle = P("fg"); ctx.lineWidth = 2; ctx.strokeRect(c.x + 1, c.y + 1, c.w - 2, c.h - 2);
  const ix = c.x + 26, iy = c.y + 56, iw = c.w - 52, ih = c.h - 80;
  ctx.fillStyle = P("extra.1");
  if (k === 0) { [1, 0.82, 0.9, 0.55].forEach((f, r) => ctx.fillRect(ix, iy + r * 40, iw * f, 18)); }                                   // abstract grey text bars
  else if (k === 1) { for (let i = 0; i < 3; i++) { ctx.fillRect(ix + i * (iw + 16) / 3, iy, (iw - 32) / 3, ih - 44); ctx.fillRect(ix + i * (iw + 16) / 3, iy + ih - 30, (iw - 32) / 3 * 0.7, 12); } }
  else { ctx.fillStyle = "#000"; ctx.fillRect(ix, iy, iw, ih); ctx.fillStyle = P("accent"); ctx.beginPath(); ctx.moveTo(c.x + c.w / 2 - 30, iy + ih / 2 - 38); ctx.lineTo(c.x + c.w / 2 + 40, iy + ih / 2); ctx.lineTo(c.x + c.w / 2 - 30, iy + ih / 2 + 38); ctx.closePath(); ctx.fill(); }
  ctx.restore();
  ctx.save(); ctx.fillStyle = P("fg");
  lib.setFont(ctx, tokens, "zh", 52, { weight: 600 }); ctx.fillText(lib.MOTIF[k].zh, c.x, c.y + c.h + 76);
  lib.setFont(ctx, tokens, "mono", 26, { weight: 700 }); ctx.fillStyle = P("extra.2"); lib.drawText(ctx, `0${k + 1} ${lib.MOTIF[k].en.toUpperCase()}`, c.x + 130, c.y + c.h + 72, { tracking: 1.5 });
  ctx.restore();
}
function punchline(ctx, t, tokens, lib) {
  if (t < 3.6) return;
  const P = L.P, c = L.cards[2], n = Math.min(3, Math.floor((t - 3.6) * 30 / 2) + 1);        // the box draws itself in 3 steps
  const pts = [[c.x - 34, c.y - 30], [c.x + c.w + 38, c.y - 44], [c.x + c.w + 30, c.y + c.h + 36], [c.x - 40, c.y + c.h + 24], [c.x - 30, c.y - 38]];
  ctx.save(); ctx.strokeStyle = P("accent"); ctx.lineWidth = 7; ctx.lineJoin = "round"; ctx.lineCap = "round";
  lib.wobblePath(ctx, pts.slice(0, 1 + Math.ceil(n * 4 / 3)), { amp: 5, seed: 17, seg: 40 }); ctx.stroke();
  if (n === 3) { lib.setFont(ctx, tokens, "mono", 34, { weight: 700 }); ctx.fillStyle = P("accent"); lib.drawText(ctx, "← SHIP IT", c.x + c.w - 150, c.y - 70, { tracking: 2 }); }
  ctx.restore();
}
function scene(ctx, t, tokens, lib) {
  ctx.fillStyle = L.P("bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  grid(ctx, t, lib); label(ctx, t, tokens, lib); titles(ctx, t, tokens, lib);
  for (let k = 0; k < 3; k++) card(ctx, t, tokens, lib, k);
  punchline(ctx, t, tokens, lib);
}
function endFrame(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  grid(ctx, 5, lib);
  lib.setFont(ctx, tokens, "display", 520, { weight: 700 }); ctx.fillStyle = P("fg");
  lib.drawText(ctx, "BRUTAL.", 150, 690, { tracking: -0.05 * 520 });                                  // bleeds off the right edge on purpose
  ctx.fillStyle = P("accent"); ctx.fillRect(192, 760, 144, 24);
  lib.setFont(ctx, tokens, "mono", 30, { weight: 700 }); ctx.fillStyle = P("extra.2"); lib.drawText(ctx, "[ brutalist-meme ]", 360, 782, { tracking: 2 });
}

export function renderAt(t, ctx, tokens, lib) {
  const tt = t >= 3.2 && t < 3.6 ? 3.2 : t;                                                            // held breath: the frame freezes
  const draw = (x, time) => { const s = punch(time); if (s !== 1) { x.translate(lib.W / 2, lib.H / 2); x.scale(s, s); x.translate(-lib.W / 2, -lib.H / 2); } (time >= 4.2 ? endFrame : scene)(x, time, tokens, lib); };
  if (t >= 4.0 && t < 4.2) {                                                                          // glitch: RGB split + sliced rows
    const src = lib.offscreen("bm_src", (x) => scene(x, 3.99, tokens, lib));
    const k = lib.frame(t);
    const sl = lib.offscreen("bm_sl", (x) => { x.drawImage(src, 0, 0); for (let i = 0; i < 9; i++) { const y = Math.floor(lib.hash(3, i, k) * lib.H), h = 20 + Math.floor(lib.hash(4, i, k) * 90), dx = Math.round(lib.hashS(5, i, k) * 140); x.drawImage(src, 0, y, lib.W, h, dx, y, lib.W, h); } });
    lib.rgbSplit(ctx, sl, { r: [12 + (k % 2) * 8, 0], g: [0, 0], b: [-14, 2] });
    return;
  }
  ctx.save(); draw(ctx, tt); ctx.restore();
}
