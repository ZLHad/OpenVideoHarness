// product-keynote swatch — one idea per frame on a seamless stage; the object settles, then the type.
//   0.0–0.8  warm-white seamless stage lights up; the hero object (a fictional rounded device in the one accent
//            colour) glides in from the right, turning from 26° to 10°, and comes to rest (easeOutQuart, 18 frames)
//   0.8–2.6  0.3 s after it rests, the headline rises 16 px and fades in; the Chinese line 6 frames later
//   2.0–4.0  the hero slides to the third slot; beside it appear its earlier stages: a hairline outline and a
//            three-part storyboard assembly; labels only after each object has settled; a slow light sweep
//   4.0–5.0  light-sweep transition: a soft band of light crosses the frame, and behind it is the dark stage with the
//            finished object alone
// No overshoot anywhere; springs are critically damped (stiffness 170, damping 26).

let L = null;
export const fonts = ["Avenir Next", "PingFang SC"];

export async function setup(ctx, tokens, lib) {
  L = { slots: [480, 960, 1440], cy: 610, w: 300, h: 172, d: 64 };
}

const E_IN = (lib, tokens) => lib.easeOf(tokens.ease.enter);
const MOVE = (lib) => lib.ease.inOutQuart;

// ───────── the object (2D, faked turn: front face narrows, side face appears) ─────────
function body(ctx, lib, tokens, cx, cy, s, ang, kind, sweep = -1, dark = false) {
  const acc = lib.color(tokens, "accent");
  const w = L.w * s * Math.cos(ang), h = L.h * s, dw = L.d * s * Math.sin(ang), r = h * 0.3;
  const x0 = cx - (w + dw) / 2, y0 = cy - h / 2;
  if (kind === "outline") {
    ctx.save(); ctx.strokeStyle = lib.color(tokens, "extra.0"); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.roundRect(x0, y0, w, h, r); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x0 + w, y0 + r * 0.6); ctx.lineTo(x0 + w + dw, y0 + r * 0.9); ctx.lineTo(x0 + w + dw, y0 + h - r * 0.9); ctx.lineTo(x0 + w, y0 + h - r * 0.6); ctx.stroke();
    ctx.setLineDash([6, 8]); ctx.beginPath(); ctx.moveTo(x0 - 30, cy); ctx.lineTo(x0 + w + dw + 30, cy); ctx.moveTo(x0 + w / 2, y0 - 30); ctx.lineTo(x0 + w / 2, y0 + h + 30); ctx.stroke();
    ctx.restore(); return;
  }
  const base = kind === "draft" ? acc : lib.color(tokens, "extra.1");
  // side face
  ctx.save();
  if (dw > 0.5) {
    const sg = ctx.createLinearGradient(x0 + w - r * 0.3, 0, x0 + w + dw, 0);
    sg.addColorStop(0, lib.mixColor(base, "#000000", 0.18)); sg.addColorStop(1, lib.mixColor(base, "#000000", 0.42));
    ctx.fillStyle = sg;
    ctx.beginPath(); ctx.moveTo(x0 + w - r * 0.3, y0 + 2); ctx.lineTo(x0 + w + dw, y0 + r * 0.35); ctx.lineTo(x0 + w + dw, y0 + h - r * 0.35); ctx.lineTo(x0 + w - r * 0.3, y0 + h - 2); ctx.closePath(); ctx.fill();
  }
  // front face: top-lit gradient, rim light, glass highlight
  const g = ctx.createLinearGradient(0, y0, 0, y0 + h);
  g.addColorStop(0, lib.mixColor(base, "#ffffff", 0.28)); g.addColorStop(0.45, base); g.addColorStop(1, lib.mixColor(base, "#000000", 0.22));
  ctx.fillStyle = g; ctx.beginPath(); ctx.roundRect(x0, y0, w, h, r); ctx.fill();
  ctx.save(); ctx.clip();
  const hl = ctx.createLinearGradient(0, y0, 0, y0 + h * 0.4); hl.addColorStop(0, "rgba(255,255,255,0.45)"); hl.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = hl; ctx.fillRect(x0, y0, w, h * 0.4);
  if (sweep >= 0 && sweep <= 1) {                                   // light band crossing the object
    const sx = lib.lerp(x0 - w * 0.6, x0 + w * 1.6, sweep), band = ctx.createLinearGradient(sx - 90, 0, sx + 90, 0);
    band.addColorStop(0, "rgba(255,255,255,0)"); band.addColorStop(0.5, "rgba(255,255,255,0.42)"); band.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = band; ctx.fillRect(x0, y0, w, h);
  }
  ctx.restore();
  ctx.strokeStyle = dark ? "rgba(255,255,255,0.55)" : "rgba(255,255,255,0.7)"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(x0 + 1, y0 + 1, w - 2, h - 2, r); ctx.stroke();
  ctx.fillStyle = lib.mixColor(base, "#000000", 0.45); ctx.beginPath(); ctx.arc(x0 + w * 0.78, cy, h * 0.09, 0, lib.TAU); ctx.fill();   // one control
  ctx.restore();
}
function object(ctx, lib, tokens, cx, cy, s, ang, kind, opts = {}) {
  const { W } = lib, floor = cy + L.h * s / 2;
  // soft contact shadow
  const sh = ctx.createRadialGradient(cx, floor + 6, 0, cx, floor + 6, L.w * s * 0.7);
  sh.addColorStop(0, opts.dark ? "rgba(0,0,0,0.5)" : "rgba(40,40,30,0.22)"); sh.addColorStop(1, "rgba(0,0,0,0)");
  ctx.save(); ctx.fillStyle = sh; ctx.translate(cx, floor + 6); ctx.scale(1, 0.12); ctx.translate(-cx, -(floor + 6));
  ctx.fillRect(cx - L.w * s, floor - 60, L.w * s * 2, 130); ctx.restore();
  // floor reflection: the object flipped, faded out over 90 px
  if (kind !== "outline") {
    const ref = lib.layer("pk_ref");
    ref.translate(0, floor * 2); ref.scale(1, -1); body(ref, lib, tokens, cx, cy, s, ang, kind, -1, opts.dark);
    ref.setTransform(1, 0, 0, 1, 0, 0); ref.globalCompositeOperation = "destination-in";
    const m = ref.createLinearGradient(0, floor, 0, floor + 90); m.addColorStop(0, "rgba(0,0,0,0.2)"); m.addColorStop(1, "rgba(0,0,0,0)");
    ref.fillStyle = m; ref.fillRect(0, floor, W, 90);
    ctx.drawImage(ref.canvas, 0, 0);
  }
  body(ctx, lib, tokens, cx, cy, s, ang, kind, opts.sweep ?? -1, opts.dark);
}
function storyboard(ctx, lib, tokens, cx, cy, t) {  // three parts settle into one body, leaving seams
  const u = lib.tween(t, 2.15, 2.75, E_IN(lib, tokens)), s = 0.86, w = L.w * s, h = L.h * s;
  for (let k = 0; k < 3; k++) {
    const pw = (w - 24) / 3, px = cx - w / 2 + k * (pw + 12) + (k - 1) * (1 - u) * 60, py = cy - h / 2 - (1 - u) * (k === 1 ? 40 : -20);
    ctx.save(); ctx.globalAlpha = lib.clamp(u * 2);
    const g = ctx.createLinearGradient(0, py, 0, py + h);
    g.addColorStop(0, "#EFEFF0"); g.addColorStop(1, "#C9C9CD");
    ctx.fillStyle = g; ctx.beginPath(); ctx.roundRect(px, py, pw, h, k === 1 ? 6 : [k === 0 ? h * 0.3 : 6, k === 2 ? h * 0.3 : 6, k === 2 ? h * 0.3 : 6, k === 0 ? h * 0.3 : 6]); ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.8)"; ctx.lineWidth = 1.5; ctx.stroke();
    ctx.restore();
  }
}

// ───────── scene ─────────
function stage(ctx, lib, tokens, dark, lift = 1) {
  const { W, H } = lib;
  const g = ctx.createRadialGradient(W / 2, H * 0.42, 0, W / 2, H * 0.42, W * 0.75);
  if (dark) { g.addColorStop(0, lib.color(tokens, "extra.3")); g.addColorStop(1, lib.color(tokens, "extra.2")); }
  else { g.addColorStop(0, lib.mixColor("#FBFBF8", lib.color(tokens, "bg"), 1 - lift)); g.addColorStop(1, lib.mixColor("#E6E6E1", "#D8D8D2", 1 - lift)); }
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
}
function scene(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W } = lib, E = E_IN(lib, tokens);
  stage(ctx, lib, tokens, false, lib.ease.outCubic(lib.seg(t, 0, 0.8)));
  // hero: glides in big (macro, ~30 % of the frame width) and settles (0.1–0.7); a light sweep; then it steps
  // back to slot 3 at 0.86× (2.0–2.5)
  const inU = lib.tween(t, 0.1, 0.7, E), toSlot = MOVE(lib)(lib.seg(t, 2.0, 2.5));
  const hx = lib.lerp(lib.lerp(W + 520, 960, inU), L.slots[2], toSlot), hs = lib.lerp(1.9, 0.86, toSlot);
  const ang = lib.lerp(lib.lerp(26, 10, inU), 14, toSlot) * Math.PI / 180;
  const sweep = t < 2.0 ? lib.seg(t, 1.25, 1.95) : lib.seg(t, 2.65, 3.45);
  if (t >= 0.1) object(ctx, lib, tokens, hx, lib.lerp(660, L.cy, toSlot), hs, ang, "draft", { sweep: sweep > 0 && sweep < 1 ? sweep : -1 });
  // earlier stages appear beside it
  const ou = lib.seg(t, 2.1, 2.6);
  if (ou > 0) { ctx.save(); ctx.globalAlpha = lib.ease.outCubic(ou); object(ctx, lib, tokens, L.slots[0], L.cy, 0.86, 14 * Math.PI / 180, "outline"); ctx.restore(); }
  if (t >= 2.15) storyboard(ctx, lib, tokens, L.slots[1], L.cy, t);
  // headline: 0.3 s after the hero rests
  const tu = lib.tween(t, 1.0, 1.6, E), zu = lib.tween(t, 1.2, 1.8, E);
  ctx.save(); ctx.fillStyle = C("fg");
  if (tu > 0) { ctx.globalAlpha = tu; lib.setFont(ctx, tokens, "display", 108, { weight: 600 }); lib.drawText(ctx, lib.TITLE_EN, W / 2, 246 + (1 - tu) * 16, { align: "center", tracking: -108 * 0.02 }); }
  if (zu > 0) { ctx.globalAlpha = zu; ctx.fillStyle = C("extra.0"); lib.setFont(ctx, tokens, "zh", 58, { weight: 500 }); lib.drawText(ctx, lib.TITLE_ZH, W / 2, 336 + (1 - zu) * 16, { align: "center", tracking: 58 * 0.04 }); }
  // labels, after each object settles
  [2.6, 2.75, 2.5].forEach((t0, k) => {
    const a = lib.tween(t, t0, t0 + 0.4, E); if (a <= 0) return;
    ctx.globalAlpha = a; ctx.fillStyle = k === 2 ? C("fg") : C("extra.0");
    lib.setFont(ctx, tokens, "display", 36, { weight: 600 }); lib.drawText(ctx, lib.MOTIF[k].en, L.slots[k], 860 + (1 - a) * 12, { align: "center" });
    lib.setFont(ctx, tokens, "zh", 46, { weight: 400 }); ctx.fillStyle = C("extra.0"); lib.drawText(ctx, lib.MOTIF[k].zh, L.slots[k], 922 + (1 - a) * 12, { align: "center", tracking: 4 });
  });
  ctx.restore();
}
function endFrame(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W } = lib;
  stage(ctx, lib, tokens, true);
  object(ctx, lib, tokens, W / 2, 560, 1.2, 12 * Math.PI / 180, "draft", { dark: true });
  const a = lib.tween(t, 4.55, 4.95, E_IN(lib, tokens));
  if (a > 0) {
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C("extra.4");
    lib.setFont(ctx, tokens, "display", 64, { weight: 600 }); lib.drawText(ctx, "Product Keynote", W / 2, 850 + (1 - a) * 16, { align: "center", tracking: -64 * 0.02 });
    ctx.fillStyle = C("extra.0"); lib.setFont(ctx, tokens, "zh", 46, { weight: 400 }); lib.drawText(ctx, "产品发布片", W / 2, 920 + (1 - a) * 16, { align: "center", tracking: 6 });
    ctx.restore();
  }
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  if (t < 4.0) return scene(ctx, t, tokens, lib);
  // light-sweep transition: B is revealed behind a soft diagonal band of light moving left → right
  const u = lib.ease.inOutQuart(lib.seg(t, 4.0, 4.6)), ang = 18 * Math.PI / 180;
  const dx = Math.cos(ang), dy = Math.sin(ang), half = (Math.abs(dx) * W + Math.abs(dy) * H) / 2 + 260;
  const pos = lib.lerp(-half, half, u), fx = W / 2 + dx * pos, fy = H / 2 + dy * pos;
  if (u >= 1) return endFrame(ctx, t, tokens, lib);
  scene(ctx, 3.99, tokens, lib);
  const b = lib.layer("pk_b"); endFrame(b, t, tokens, lib);
  b.globalCompositeOperation = "destination-in";
  const m = b.createLinearGradient(fx - dx * 120, fy - dy * 120, fx + dx * 120, fy + dy * 120);
  m.addColorStop(0, "rgba(0,0,0,1)"); m.addColorStop(1, "rgba(0,0,0,0)");
  b.fillStyle = m; b.fillRect(0, 0, W, H);
  ctx.drawImage(b.canvas, 0, 0);
  // the band of light itself (screen), no brighter than the type
  ctx.save(); ctx.globalCompositeOperation = "screen";
  const g = ctx.createLinearGradient(fx - dx * 260, fy - dy * 260, fx + dx * 260, fy + dy * 260);
  g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, "rgba(255,248,240,0.55)"); g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}
