// pastel-ui swatch — a light UI explainer: a pastel mesh wallpaper, white cards with soft shadows, one blue-violet
// accent for what the interface does, one colour per concept carried from start to end, a monospace step readout,
// a caption at the bottom with its key word in the accent. Motion is an OS's: springs with a percent or two of
// overshoot, things typed and sent, a focus that moves from card to card, a card that opens into the screen.
//
//   0.0–0.8  frame 0 is the pastel wallpaper; at 0.1 s an input bar switches on mid-frame and a capsule grows out of
//            it in three segments, the three concept colours (coral, mint, sunflower); a thin ring in the same three
//            colours keeps turning round the bar while "Every frame is code." is typed (0.15–0.73 s)
//   0.8–2.6  sent on the bar line at 0.8 s: the line becomes a blue-violet bubble that flies up as the title; the reply
//            shows typing dots, then streams in token by token as the caption, 代码 in the accent; skeleton cards hold
//            the middle while the answer arrives
//   2.0–4.0  three cards lift in over the skeletons (大纲 coral, 分镜 mint, 初版 sunflower); a dot walks a stepper rail
//            under them and on each beat (2.4 / 2.8 / 3.2 s) the focus moves: that card grows to 1.2×, the others step
//            back to 60 %; STEP n/3 counts. The draft renders as the dot walks to it, then plays back (a ball hops
//            across its preview, which is a small copy of this very wallpaper); 3.6 s a pulse runs along the rail
//   4.0–5.0  container transform: the draft card opens to full screen, its preview becomes the picture, the ball
//            finishes its last hop and lands, "Pastel UI / 浅色界面讲解" settles inside it over a three-colour scrubber
// Everything is a pure function of t. FOLEY (bottom) reads the same time constants as the picture.

export const fonts = ["Avenir Next", "PingFang SC", "Menlo"];

// ── one clock for picture and sound
const T_WAKE = 0.1;                                  // the input switches on; the colour capsule grows out of it
const T_TYPE = 0.15;                                 // first key
const T_SEND = 0.8;                                  // send, on the bar line
const T_DOTS = 1.0;                                  // reply: typing dots
const ZH_TOKENS = ["每一帧", "，", "都是", "代码", "。"];
const T_TOKEN = [1.24, 1.31, 1.38, 1.46, 1.53];      // the reply streams in
const T_SKEL = 1.1;                                  // skeleton cards hold the middle while the answer arrives
const T_CARD = [2.0, 2.12, 2.24];                    // cards lift in
const T_RAIL = 2.06;                                 // the stepper rail draws
const T_CHECK = [2.4, 2.8, 3.2];                     // the dot arrives, the focus moves (on the beat)
const HOPS = [[3.3, 3.6, 0.06, 0.32, 0.8], [3.6, 3.88, 0.32, 0.56, 0.8], [4.02, 4.5, 0.56, 0.8, 0.95]];   // the draft plays: [t0, t1, u0, u1, height]
const T_PLAY = HOPS[0][0], T_LAND = HOPS[2][1];
const T_DONE = 3.6;                                  // all three done: a pulse runs along the rail
const T_PUSH = 4.0, PUSH_DUR = 0.5;                  // the draft card opens to full screen
const T_NAME = 4.52;                                 // the name settles inside the picture

let L = null;      // layout, computed once in setup (pure data)
let MESH = null;   // this frame's wallpaper canvas (set at the start of each frame, read later in the same frame)

export async function setup(ctx, tokens, lib) {
  const { W } = lib;
  lib.setFont(ctx, tokens, "display", 92);
  const tLay = lib.layoutText(ctx, lib.TITLE_EN, { x: 0, y: 0, tracking: lib.tracking(tokens, "display", 92) });
  lib.setFont(ctx, tokens, "body", 72);
  const iLay = lib.layoutText(ctx, lib.TITLE_EN, { x: 0, y: 0 });
  lib.setFont(ctx, tokens, "zh", 60);
  const zLay = lib.layoutText(ctx, lib.TITLE_ZH, { x: 0, y: 0, align: "center", tracking: lib.tracking(tokens, "zh", 60) });
  // key frames: a little quicker than one key a frame, half a frame more after each space
  const keyF = [], f0 = Math.ceil(T_TYPE * lib.FPS - 1e-6); let sp = 0;
  lib.graphemes(lib.TITLE_EN).forEach((ch, i) => { keyF.push(f0 + Math.floor(i * 0.85 + sp * 0.5)); if (ch === " ") sp++; });
  const tokOf = []; ZH_TOKENS.forEach((s, k) => lib.graphemes(s).forEach(() => tokOf.push(k)));
  const tokRight = ZH_TOKENS.map((_, k) => Math.max(...zLay.glyphs.filter((g) => tokOf[g.i] === k).map((g) => g.x + g.w)));
  const cards = lib.slots(3, { area: { x0: 168, w: 1584 }, gap: 72 }).map((s) => ({ cx: s.x, x: s.x - s.w / 2, y: 388, w: s.w, h: 324 }));
  L = {
    inputW: iLay.width, zhX0: zLay.x0, tokRight, keyF, tokOf, cards,
    bubble: { cx: W / 2, cy: 246, w: tLay.width + 120, h: 156 },
    pill: { cx: W / 2, cy: 590, w: 1320, h: 150, size: 72, pad: 84, btn: 54 },
    cap: { cx: W / 2, cy: 924, h: 108 },
    railY: 800,
  };
}

// ───────── helpers
const P = (tokens, lib, k) => lib.color(tokens, k);
const entity = (tokens, lib, k) => P(tokens, lib, `entity.${k}`);
function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, Math.max(0, r)); }
const lerpRect = (a, b, u, lib) => ({ x: lib.lerp(a.x, b.x, u), y: lib.lerp(a.y, b.y, u), w: lib.lerp(a.w, b.w, u), h: lib.lerp(a.h, b.h, u) });
/** A rounded box with the two-layer soft shadow (violet-tinted); lift deepens it. */
function softBox(ctx, tokens, lib, x, y, w, h, r, fill, lift = 0) {
  const sh = P(tokens, lib, "shadow"), { ambient: A, key: K } = tokens.shadow;
  ctx.save(); ctx.fillStyle = fill;
  ctx.shadowColor = lib.rgba(sh, A.alpha); ctx.shadowBlur = A.blur + lift * 2.2; ctx.shadowOffsetY = A.y + lift * 1.2;
  rr(ctx, x, y, w, h, r); ctx.fill();
  ctx.shadowColor = lib.rgba(sh, K.alpha); ctx.shadowBlur = K.blur + lift * 0.5; ctx.shadowOffsetY = K.y + lift * 0.3;
  ctx.fill();
  ctx.restore();
}
/** The three concept colours around a centre, as hard-edged thirds (a conic gradient), rotated by rot. */
function thirds(ctx, tokens, lib, cx, cy, rot) {
  const g = ctx.createConicGradient(rot, cx, cy), E = [0, 1, 2].map((k) => entity(tokens, lib, k));
  [[0, 0], [0.32, 0], [0.345, 1], [0.655, 1], [0.68, 2], [0.985, 2], [1, 0]].forEach(([o, k]) => g.addColorStop(o, E[k]));
  return g;
}

// ───────── wallpaper: a pastel mesh, drifting; drawn opaque into a layer so the soft gradients don't band
function ground(ctx, t, tokens, lib) {
  const { W, H } = lib, m = lib.layer("pastel-ui_mesh");
  m.fillStyle = P(tokens, lib, "bg"); m.fillRect(0, 0, W, H);
  const blobs = [
    ["wash_lavender", 330, 210, 1120, 0.0], ["wash_peach", 1650, 280, 980, 1.7],
    ["wash_mint", 470, 1010, 960, 3.1], ["wash_lilac", 1530, 1000, 820, 4.4], ["wash_lavender", 960, 600, 620, 2.2],
  ];
  for (const [k, x0, y0, r, ph] of blobs) {
    const x = x0 + 46 * Math.sin(0.85 * t + ph), y = y0 + 34 * Math.cos(0.7 * t + ph * 1.3);
    const c = P(tokens, lib, k), g = m.createRadialGradient(x, y, 0, x, y, r);
    tokens.texture.falloff_stops.forEach((al, i, a) => g.addColorStop(i / (a.length - 1), lib.rgba(c, al)));   // ≈ gaussian: no knee
    m.fillStyle = g; m.fillRect(0, 0, W, H);
  }
  lib.grain(m, 0, { amount: tokens.texture.dither, seed: 9, mode: "source-over" });   // static dither (±1.5 levels): no 8-bit bands
  ctx.drawImage(m.canvas, 0, 0);
  MESH = m.canvas;
}

// ───────── the opening: the input switches on, the three colours grow out of it, then keep turning round it
const pillOn = (t, tokens, lib) => lib.spring(t - (T_WAKE - 1 / 30), tokens.ease.spring);
function capsule(ctx, t, tokens, lib) {
  const p = L.pill, t0 = T_WAKE - 1 / 30;
  for (const [d, wMax, hMax, lw0, lw1, aMul] of [[0, 1860, 620, 46, 14, 1], [0.07, 1620, 400, 22, 8, 0.9]]) {
    const u = lib.seg(t, t0 + d, t0 + d + 0.55);
    if (u <= 0 || u >= 1) continue;
    const e = lib.ease.outExpo(u), w = lib.lerp(p.w, wMax, e), h = lib.lerp(p.h, hMax, e);
    ctx.save(); ctx.globalAlpha *= aMul * (1 - lib.smoothstep(0.5, 1, u));
    if (d === 0) { ctx.fillStyle = "rgba(255,255,255,0.2)"; rr(ctx, p.cx - w / 2, p.cy - h / 2, w, h, h / 2); ctx.fill(); }   // a lit area, not a glow
    ctx.strokeStyle = thirds(ctx, tokens, lib, p.cx, p.cy, -Math.PI / 2 + 1.2 * u); ctx.lineWidth = lib.lerp(lw0, lw1, e);
    rr(ctx, p.cx - w / 2, p.cy - h / 2, w, h, h / 2); ctx.stroke(); ctx.restore();
  }
  const a = lib.tween(t, t0 + 0.2, t0 + 0.4, lib.ease.outCubic) * (1 - lib.tween(t, T_SEND, T_SEND + 0.12, lib.ease.outCubic));
  if (a <= 0) return;
  const sc = lib.lerp(0.86, 1, pillOn(t, tokens, lib)), w = p.w * sc + 22, h = p.h * sc + 22;
  ctx.save(); ctx.globalAlpha *= a;
  ctx.strokeStyle = thirds(ctx, tokens, lib, p.cx, p.cy, -Math.PI / 2 + 2.4 * t); ctx.lineWidth = 5;
  rr(ctx, p.cx - w / 2, p.cy - h / 2, w, h, h / 2); ctx.stroke(); ctx.restore();
}
function inputPill(ctx, t, tokens, lib) {
  const C = (k) => P(tokens, lib, k), p = L.pill;
  const rise = pillOn(t, tokens, lib), out = lib.tween(t, T_SEND + 0.04, T_SEND + 0.26, lib.easeOf(tokens.ease.exit));
  if (out >= 1 || rise <= 0) return;
  const typed = t < T_SEND ? L.keyF.filter((f) => f <= lib.frame(t)).length : 0;
  const y = p.cy + (1 - rise) * 36 + out * 90, sc = lib.lerp(0.86, 1, rise), x0 = p.cx - p.w / 2, y0 = y - p.h / 2;
  ctx.save(); ctx.globalAlpha *= Math.min(1, rise * 1.6) * (1 - out);
  ctx.translate(p.cx, y); ctx.scale(sc, sc); ctx.translate(-p.cx, -y);
  softBox(ctx, tokens, lib, x0, y0, p.w, p.h, p.h / 2, C("card"));
  const tx = x0 + p.pad; lib.setFont(ctx, tokens, "body", p.size); ctx.fillStyle = C("ink");
  const lay = lib.layoutText(ctx, lib.graphemes(lib.TITLE_EN).slice(0, typed).join(""), { x: tx, y: y + p.size * 0.36 });
  lib.drawGlyphs(ctx, lay, (g, i) => ({ dy: i === typed - 1 ? -6 * (1 - lib.seg(lib.frame(t) - L.keyF[i], 0, 2)) : 0 }));
  const idle = t < T_TYPE || typed === L.keyF.length;
  if (t < T_SEND && (!idle || Math.floor(lib.frame(t) / 8) % 2 === 0)) {                      // caret
    ctx.fillStyle = C("accent"); rr(ctx, tx + lay.width + 6, y - p.size * 0.58, p.size / 10, p.size * 1.16, p.size / 20); ctx.fill();
  }
  // send: grey until there is text, then the accent; it dips when pressed
  const bx = x0 + p.w - p.pad, on = lib.tween(t, T_TYPE, T_TYPE + 0.12, lib.ease.outCubic);
  const press = t >= T_SEND ? 1 - 0.14 * Math.exp(-14 * (t - T_SEND)) * Math.cos(10 * (t - T_SEND)) : 1;
  ctx.translate(bx, y); ctx.scale(press * p.btn / 42, press * p.btn / 42);
  ctx.fillStyle = lib.mixColor(C("line"), C("accent"), on); ctx.beginPath(); ctx.arc(0, 0, 42, 0, lib.TAU); ctx.fill();
  ctx.strokeStyle = "#FFFFFF"; ctx.lineWidth = 6; ctx.lineCap = "round"; ctx.lineJoin = "round";
  ctx.beginPath(); ctx.moveTo(0, 17); ctx.lineTo(0, -16); ctx.moveTo(-14, -2); ctx.lineTo(0, -16); ctx.lineTo(14, -2); ctx.stroke();
  ctx.restore();
}

// ───────── title bubble and the streamed reply (the caption)
function bubble(ctx, t, tokens, lib) {
  if (t < T_SEND) return;
  const C = (k) => P(tokens, lib, k), b = L.bubble, p = L.pill, s0 = p.size / 92;
  const u = lib.spring(t - T_SEND, tokens.ease.spring), ux = lib.spring(t - T_SEND - 0.04, tokens.ease.spring_settle);   // y leads x: a curve
  const fromX = p.cx - p.w / 2 + p.pad + L.inputW / 2;
  const cx = lib.lerp(fromX, b.cx, ux), cy = lib.lerp(p.cy, b.cy, u), sc = lib.lerp(s0, 1, u);
  const bg = lib.tween(t, T_SEND, T_SEND + 0.12, lib.ease.outCubic), a0 = ctx.globalAlpha;
  ctx.save(); ctx.translate(cx, cy); ctx.scale(sc, sc);
  const x0 = -b.w / 2, y0 = -b.h / 2, x1 = b.w / 2, y1 = b.h / 2;
  ctx.save(); ctx.globalAlpha = a0 * bg; ctx.fillStyle = C("accent");
  ctx.shadowColor = lib.rgba(C("accent"), 0.28); ctx.shadowBlur = 48; ctx.shadowOffsetY = 18;
  rr(ctx, x0, y0, b.w, b.h, 56); ctx.fill();
  ctx.beginPath(); ctx.moveTo(x1 - 70, y1 - 2); ctx.quadraticCurveTo(x1 - 8, y1 + 2, x1 + 16, y1 + 22);   // the tail: a message from "me"
  ctx.quadraticCurveTo(x1 - 2, y1 - 6, x1 - 8, y1 - 52); ctx.lineTo(x1 - 70, y1 - 52); ctx.closePath(); ctx.fill();
  ctx.restore();
  lib.setFont(ctx, tokens, "display", 92);
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: 0, y: 32, align: "center", tracking: lib.tracking(tokens, "display", 92) });
  ctx.fillStyle = lib.mixColor(C("ink"), "#FFFFFF", bg); lib.drawGlyphs(ctx, lay);
  ctx.restore();
}
function caption(ctx, t, tokens, lib) {
  if (t < T_DOTS) return;
  const C = (k) => P(tokens, lib, k), c = L.cap, h = c.h, pad = 56, left = L.zhX0 - pad;
  const appear = lib.spring(t - T_DOTS, tokens.ease.spring);
  let w = 172;                                       // the pill grows to each token's right edge just before the token
  ZH_TOKENS.forEach((_, k) => { w += (L.tokRight[k] + pad - left - (k ? L.tokRight[k - 1] + pad - left : 172)) * lib.spring(t - T_TOKEN[k] + 0.09, { w: 30, zeta: 0.9 }); });
  const sc = lib.lerp(0.72, 1, appear);
  ctx.save(); ctx.translate(c.cx + left, c.cy); ctx.scale(sc, sc); ctx.translate(-left, 0);
  ctx.globalAlpha *= Math.min(1, appear * 1.5);
  softBox(ctx, tokens, lib, left, -h / 2, w, h, h / 2, lib.rgba("#FFFFFF", 0.94));
  const dotsA = 1 - lib.seg(t, T_TOKEN[0] - 0.06, T_TOKEN[0] + 0.04);
  if (dotsA > 0) for (let i = 0; i < 3; i++) {                                        // typing dots
    const ph = lib.fract(t * 2.2 - i * 0.16), dy = -12 * Math.max(0, Math.sin(ph * lib.TAU)) * (ph < 0.5 ? 1 : 0);
    ctx.fillStyle = lib.rgba(C("muted"), dotsA * (dy < -6 ? 0.8 : 0.5));
    ctx.beginPath(); ctx.arc(left + 54 + i * 32, dy, 10, 0, lib.TAU); ctx.fill();
  }
  rr(ctx, left, -h / 2, w, h, h / 2); ctx.clip();
  lib.setFont(ctx, tokens, "zh", 60);
  const lay = lib.layoutText(ctx, lib.TITLE_ZH, { x: 0, y: 21, align: "center", tracking: lib.tracking(tokens, "zh", 60) });
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const k = L.tokOf[i], u = lib.tween(t, T_TOKEN[k], T_TOKEN[k] + 0.14, lib.easeOf(tokens.ease.enter));
    return u <= 0 ? null : { alpha: u, dy: (1 - u) * 12, fill: ZH_TOKENS[k] === "代码" ? C("accent") : C("ink") };
  });
  ctx.restore();
}

// ───────── cards: skeletons first, then the three concepts; the focus moves with the dot
function skeletons(ctx, t, tokens, lib) {
  L.cards.forEach((cd, k) => {
    const a = lib.tween(t, T_SKEL + k * 0.05, T_SKEL + 0.2 + k * 0.05, lib.ease.outCubic) * (1 - lib.clamp((t - T_CARD[k]) / 0.16));
    if (a <= 0) return;
    const { x, y, w, h } = cd;
    ctx.save(); ctx.globalAlpha *= a;
    ctx.fillStyle = "rgba(255,255,255,0.42)"; rr(ctx, x, y + 24, w, h, 36); ctx.fill();
    ctx.strokeStyle = "rgba(255,255,255,0.75)"; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,0.5)"; rr(ctx, x + 22, y + 46, w - 44, 190, 24); ctx.fill();
    rr(ctx, x + 32, y + 268, 120, 30, 15); ctx.fill(); rr(ctx, x + w - 172, y + 268, 140, 30, 15); ctx.fill();
    const sx = x - 200 + lib.fract((t - T_SKEL) * 1.4 + k * 0.18) * (w + 400);     // loading shimmer
    const g = ctx.createLinearGradient(sx - 120, 0, sx + 120, 0);
    g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, "rgba(255,255,255,0.55)"); g.addColorStop(1, "rgba(255,255,255,0)");
    rr(ctx, x, y + 24, w, h, 36); ctx.clip(); ctx.fillStyle = g; ctx.fillRect(x, y, w, h + 48);
    ctx.restore();
  });
}
function focusOf(t, k, tokens, lib) {               // 0…1 (with a little spring overshoot): this card is the current step
  const sp = tokens.ease.spring, on = lib.spring(t - (T_CHECK[k] - 0.06), sp);
  return on - (k < 2 ? lib.spring(t - (T_CHECK[k + 1] - 0.06), sp) : 0);
}
function cardRect(t, k, tokens, lib) {
  const cd = L.cards[k], F = tokens.focus, p = lib.spring(t - T_CARD[k], tokens.ease.spring);
  const f = focusOf(t, k, tokens, lib), back = Math.max(0, lib.spring(t - (T_CHECK[0] - 0.06), tokens.ease.spring) - Math.max(0, f));
  const pre = k === 2 ? lib.ease.inOutSine(lib.seg(t, T_PLAY + 0.05, T_PUSH)) : 0;   // the draft is picked up (straight up) while it plays
  const s = 1 + (F.scale - 1) * f - (1 - F.others_scale) * back + 0.1 * pre, cy = cd.y + cd.h / 2 + (1 - p) * 70 - 30 * pre, cx = cd.cx;
  return { x: cx - cd.w * s / 2, y: cy - cd.h * s / 2, w: cd.w * s, h: cd.h * s, f: Math.max(0, f),
    alpha: lib.clamp((t - T_CARD[k]) / 0.14) * (1 - (1 - F.others_opacity) * back) };
}
function drawCard(ctx, t, k, R, tokens, lib, e = 0) {
  const C = (n) => P(tokens, lib, n), col = entity(tokens, lib, k), s = R.w / 480;
  ctx.save(); ctx.globalAlpha *= R.alpha;
  softBox(ctx, tokens, lib, R.x, R.y, R.w, R.h, 36 * s * (1 - e), C("card"), 18 * R.f);
  const inner = 1 - lib.seg(e, 0, 0.3);              // the card's own content; it goes as the card opens
  if (inner > 0) {
    ctx.save(); ctx.globalAlpha *= inner; ctx.translate(R.x, R.y); ctx.scale(s, s);
    ctx.fillStyle = lib.mixColor("#FFFFFF", col, 0.16); rr(ctx, 22, 22, 436, 190, 24); ctx.fill();
    if (k === 0) illusOutline(ctx, t, 22, 22, 436, col, lib);
    else if (k === 1) illusBoard(ctx, t, 22, 22, 436, 190, col, lib);
    else draftBar(ctx, t, col, tokens, lib);
    const by = 274;                                   // label row: colour chip · 中文 ……… English
    ctx.fillStyle = col; ctx.beginPath(); ctx.arc(44, by - 20, 12, 0, lib.TAU); ctx.fill();
    lib.setFont(ctx, tokens, "zh", 56); ctx.fillStyle = C("ink"); lib.drawText(ctx, lib.MOTIF[k].zh, 68, by, { tracking: lib.tracking(tokens, "zh", 56) });
    lib.setFont(ctx, tokens, "body", 44); ctx.fillStyle = C("muted"); lib.drawText(ctx, lib.MOTIF[k].en, 446, by, { align: "right" });
    ctx.restore();
  }
  if (k === 2) {                                     // the draft's preview: in screen space, so it can become the screen
    const p0 = { x: R.x + 40 * s, y: R.y + 40 * s, w: 400 * s, h: 118 * s };
    preview(ctx, t, lerpRect(p0, R, e, lib), 16 * s * (1 - e), e, tokens, lib);
  }
  ctx.restore();
}
function illusOutline(ctx, t, rx, ry, rw, col, lib) {           // a bulleted outline, its lines drawn on
  [1, 0.78, 0.56].forEach((wf, i) => {
    const y = ry + 50 + i * 46, u = lib.tween(t, T_CARD[0] + 0.2 + i * 0.07, T_CARD[0] + 0.55 + i * 0.07, lib.ease.outCubic);
    if (u <= 0) return;
    ctx.fillStyle = col; ctx.beginPath(); ctx.arc(rx + 40, y, 9 * Math.min(1, u * 2), 0, lib.TAU); ctx.fill();
    ctx.fillStyle = lib.mixColor("#FFFFFF", col, 0.5); rr(ctx, rx + 64, y - 8, Math.max(16, (rw - 98) * wf * u), 16, 8); ctx.fill();
  });
}
function illusBoard(ctx, t, rx, ry, rw, rh, col, lib) {         // six storyboard frames, a ball advancing through them
  const pad = 18, gap = 12, tw = (rw - 2 * pad - 2 * gap) / 3, th = (rh - 2 * pad - gap) / 2;
  for (let j = 0; j < 6; j++) {
    const s = lib.spring(t - (T_CARD[1] + 0.2 + j * 0.05), { w: 18, zeta: 0.7 });
    if (s <= 0) continue;
    const x = rx + pad + (j % 3) * (tw + gap), y = ry + pad + Math.floor(j / 3) * (th + gap), u = j / 5;
    ctx.save(); ctx.translate(x + tw / 2, y + th / 2); ctx.scale(s, s); ctx.translate(-tw / 2, -th / 2);
    ctx.fillStyle = lib.mixColor("#FFFFFF", col, 0.42); rr(ctx, 0, 0, tw, th, 12); ctx.fill();
    ctx.fillStyle = lib.mixColor("#FFFFFF", col, 0.62); ctx.fillRect(10, th - 14, tw - 20, 3);
    ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(24 + u * (tw - 48), th * 0.7 - Math.sin(u * Math.PI) * th * 0.42, 10, 0, lib.TAU); ctx.fill();
    ctx.restore();
  }
}
const renderProg = (t, lib) => lib.tween(t, T_CHECK[1] + 0.02, T_CHECK[2], lib.ease.inOutSine);   // renders as the dot walks to it
const playProg = (t, lib) => lib.seg(t, T_PLAY, T_LAND);
function draftBar(ctx, t, col, tokens, lib) {          // in the card: render progress, then a scrubber with a playhead
  const y = 186, x0 = 40, w = 400, prog = renderProg(t, lib);
  ctx.fillStyle = lib.mixColor("#FFFFFF", col, 0.35); rr(ctx, x0, y - 6, w, 12, 6); ctx.fill();
  ctx.fillStyle = col; rr(ctx, x0, y - 6, Math.max(12, w * prog), 12, 6); ctx.fill();
  if (t >= T_PLAY - 0.1) {
    const hs = lib.spring(t - (T_PLAY - 0.1), { w: 18, zeta: 0.7 }), hx = x0 + 6 + (w - 12) * playProg(t, lib);
    ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(hx, y, 13 * hs, 0, lib.TAU); ctx.fill();
    ctx.strokeStyle = P(tokens, lib, "accent"); ctx.lineWidth = 4; ctx.stroke();
  }
}
function ballAt(t, lib) {                              // the draft's little film: three hops, the last one at full screen
  let u = HOPS[0][2], land = -9;
  for (const [a, b, u0, u1, hgt] of HOPS) {
    if (t >= b) { u = u1; land = b; continue; }
    if (t >= a) { const s = lib.seg(t, a, b); return { u: lib.lerp(u0, u1, s), h: Math.sin(Math.PI * s) * hgt, s, hop: [a, b, u0, u1, hgt] }; }
    break;
  }
  return { u, h: 0, land };
}
/** The draft's preview: a small copy of this very wallpaper (the film's own frame), a ground line, a ball; it renders
 *  behind a skeleton, plays back, and when the card opens it becomes the screen and carries the name. */
function preview(ctx, t, R, rad, e, tokens, lib) {
  const C = (n) => P(tokens, lib, n);
  ctx.save(); rr(ctx, R.x, R.y, R.w, R.h, rad); ctx.clip();
  ctx.drawImage(MESH, R.x, R.y, R.w, R.h);
  const gy = R.y + R.h * 0.8, r = R.h * lib.lerp(0.1, 0.045, e), ballAtY = (b) => gy - r - b.h * R.h * 0.5;
  ctx.fillStyle = "rgba(255,255,255,0.9)"; ctx.fillRect(R.x + R.w * 0.04, gy, R.w * 0.92, Math.max(2, R.h * 0.008));
  const b = ballAt(t, lib);
  if (b.hop) for (let j = 3; j >= 1; j--) {           // a short trail while it hops
    const s = b.s - j * 0.05; if (s <= 0) continue;
    const [, , u0, u1, hgt] = b.hop, q = { u: lib.lerp(u0, u1, s), h: Math.sin(Math.PI * s) * hgt };
    ctx.fillStyle = lib.rgba("#FFFFFF", 0.2 * (4 - j) / 3); ctx.beginPath(); ctx.arc(R.x + q.u * R.w, ballAtY(q), r, 0, lib.TAU); ctx.fill();
  }
  const k = lib.seg(t, b.land, b.land + 0.16), sq = b.land > 0 ? 0.22 * Math.sin(Math.PI * k) : 0;   // squash on landing
  ctx.save(); ctx.shadowColor = lib.rgba(C("shadow"), 0.22); ctx.shadowBlur = 6 + 30 * e; ctx.shadowOffsetY = 2 + 10 * e;
  ctx.fillStyle = "#FFFFFF"; ctx.beginPath();
  ctx.ellipse(R.x + b.u * R.w, gy - r * (1 - sq) - b.h * R.h * 0.5, r * (1 + sq * 0.6), r * (1 - sq), 0, 0, lib.TAU); ctx.fill(); ctx.restore();
  const shown = 0.06 + 0.94 * renderProg(t, lib), ex = R.x + R.w * shown;
  if (shown < 1) {                                   // the part not rendered yet: a skeleton with a loading shimmer
    ctx.fillStyle = "rgba(255,255,255,0.72)"; ctx.fillRect(ex, R.y, R.x + R.w - ex, R.h);
    const sx = R.x + lib.fract((t - T_CARD[2]) * 1.6) * (R.w + 240) - 120, g = ctx.createLinearGradient(sx - 110, 0, sx + 110, 0);
    g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, "rgba(255,255,255,0.8)"); g.addColorStop(1, "rgba(255,255,255,0)");
    ctx.save(); ctx.beginPath(); ctx.rect(ex, R.y, R.x + R.w - ex, R.h); ctx.clip(); ctx.fillStyle = g; ctx.fillRect(R.x, R.y, R.w, R.h); ctx.restore();
  }
  const ks = R.w / lib.W;                             // the full-screen page: a three-colour scrubber, then the name
  const sa = lib.tween(t, T_PUSH + 0.25, T_PUSH + 0.5, lib.ease.outCubic);
  if (sa > 0) {
    ctx.save(); ctx.globalAlpha *= sa;
    const x0 = R.x + R.w * 0.1, x1 = R.x + R.w * 0.9, y = R.y + R.h * 0.92, sw = (x1 - x0 - 2 * 12 * ks) / 3, ph = x0 + (x1 - x0) * playProg(t, lib);
    for (let j = 0; j < 3; j++) {
      const a = x0 + j * (sw + 12 * ks);
      ctx.fillStyle = "rgba(255,255,255,0.7)"; rr(ctx, a, y - 6 * ks, sw, 12 * ks, 6 * ks); ctx.fill();
      ctx.fillStyle = entity(tokens, lib, j); rr(ctx, a, y - 6 * ks, lib.clamp(ph - a, 0, sw), 12 * ks, 6 * ks); ctx.fill();
    }
    ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(ph, y, 16 * ks, 0, lib.TAU); ctx.fill();
    ctx.strokeStyle = C("accent"); ctx.lineWidth = 5 * ks; ctx.stroke();
    ctx.restore();
  }
  const na = lib.tween(t, T_NAME, T_NAME + 0.28, lib.easeOf(tokens.ease.enter));
  if (na > 0) {
    ctx.save(); ctx.globalAlpha *= na; const dy = (1 - na) * 18 * ks;
    lib.setFont(ctx, tokens, "display", 124 * ks); ctx.fillStyle = C("ink");
    lib.drawText(ctx, "Pastel UI", R.x + R.w / 2, R.y + R.h * 0.43 + dy, { align: "center", tracking: lib.tracking(tokens, "display", 124 * ks) });
    lib.setFont(ctx, tokens, "zh", 64 * ks); ctx.fillStyle = C("muted");
    lib.drawText(ctx, "浅色界面讲解", R.x + R.w / 2, R.y + R.h * 0.43 + 96 * ks + dy, { align: "center", tracking: 64 * ks * 0.08 });
    ctx.restore();
    lib.setFont(ctx, tokens, "zh", 56 * ks);           // the three concepts gather under the name, each in its own colour
    const cw = 250 * ks, ch = 98 * ks, gap = 30 * ks, cy = R.y + R.h * 0.43 + 236 * ks;
    for (let j = 0; j < 3; j++) {
      const q = lib.spring(t - (T_NAME + 0.06 + j * 0.06), tokens.ease.pop);
      if (q <= 0) continue;
      const cx = R.x + R.w / 2 + (j - 1) * (cw + gap);
      ctx.save(); ctx.translate(cx, cy); ctx.scale(q, q);
      softBox(ctx, tokens, lib, -cw / 2, -ch / 2, cw, ch, ch / 2, C("card"));
      ctx.fillStyle = entity(tokens, lib, j); ctx.beginPath(); ctx.arc(-cw / 2 + 52 * ks, 0, 16 * ks, 0, lib.TAU); ctx.fill();
      ctx.fillStyle = C("ink"); lib.drawText(ctx, lib.MOTIF[j].zh, -cw / 2 + 88 * ks, 20 * ks, { tracking: 56 * ks * 0.04 });
      ctx.restore();
    }
  }
  ctx.restore();
}

// ───────── the stepper rail
function dotX(t, lib) {
  const xs = L.cards.map((c) => c.cx);
  if (t < T_CHECK[1] - 0.36) return xs[0];
  if (t < T_CHECK[2] - 0.36) return lib.lerp(xs[0], xs[1], lib.ease.inOutCubic(lib.seg(t, T_CHECK[1] - 0.36, T_CHECK[1])));
  return lib.lerp(xs[1], xs[2], lib.ease.inOutCubic(lib.seg(t, T_CHECK[2] - 0.36, T_CHECK[2])));
}
function rail(ctx, t, tokens, lib) {
  if (t < T_RAIL) return;
  const C = (k) => P(tokens, lib, k), y = L.railY, xs = L.cards.map((c) => c.cx);
  ctx.save(); ctx.lineCap = "round";
  ctx.strokeStyle = lib.rgba("#FFFFFF", 0.9); ctx.lineWidth = 10;
  lib.strokePartial(ctx, [[xs[0], y], [xs[2], y]], lib.tween(t, T_RAIL, T_RAIL + 0.36, lib.easeOf(tokens.ease.enter)));
  const dx = t >= T_CHECK[0] - 0.12 ? dotX(t, lib) : xs[0];
  if (dx > xs[0] + 1) {                              // progress in the three colours, short blends at the nodes
    const g = ctx.createLinearGradient(xs[0], 0, xs[2], 0);
    [[0, 0], [0.4, 0], [0.5, 1], [0.9, 1], [1, 2]].forEach(([o, k]) => g.addColorStop(o, entity(tokens, lib, k)));
    ctx.strokeStyle = g; ctx.lineWidth = 10; ctx.beginPath(); ctx.moveTo(xs[0], y); ctx.lineTo(dx, y); ctx.stroke();
  }
  xs.forEach((x, k) => {                             // nodes: white until reached, then the stage's colour + a ring
    const appear = lib.spring(t - (T_RAIL + 0.36 * (x - xs[0]) / (xs[2] - xs[0])), { w: 18, zeta: 0.7 });
    if (appear <= 0) return;
    const reached = t >= T_CHECK[k];
    ctx.fillStyle = reached ? entity(tokens, lib, k) : "#FFFFFF";
    ctx.beginPath(); ctx.arc(x, y, 15 * appear, 0, lib.TAU); ctx.fill();
    if (!reached) { ctx.strokeStyle = C("line"); ctx.lineWidth = 4; ctx.stroke(); }
    for (const t1 of [T_CHECK[k], T_DONE + k * 0.07]) {   // a ring on arrival, and again in the "all done" pulse
      const ring = lib.seg(t, t1, t1 + 0.45);
      if (ring <= 0 || ring >= 1) continue;
      ctx.strokeStyle = lib.rgba(entity(tokens, lib, k), 0.6 * (1 - ring)); ctx.lineWidth = 5;
      ctx.beginPath(); ctx.arc(x, y, 15 + 34 * lib.ease.outCubic(ring), 0, lib.TAU); ctx.stroke();
    }
  });
  const da = lib.spring(t - (T_CHECK[0] - 0.12), { w: 18, zeta: 0.7 });
  if (da > 0) {                                      // the walking dot
    ctx.save(); ctx.shadowColor = lib.rgba(C("accent"), 0.4); ctx.shadowBlur = 18; ctx.shadowOffsetY = 4;
    ctx.fillStyle = "#FFFFFF"; ctx.beginPath(); ctx.arc(dx, y, 19 * da, 0, lib.TAU); ctx.fill(); ctx.restore();
    ctx.strokeStyle = C("accent"); ctx.lineWidth = 6; ctx.beginPath(); ctx.arc(dx, y, 16 * da, 0, lib.TAU); ctx.stroke();
  }
  ctx.restore();
}

// ───────── the one readout: STEP n/3 (the digit rolls up)
function hud(ctx, t, e, tokens, lib) {
  const C = (k) => P(tokens, lib, k), a = lib.tween(t, 0.15, 0.5, lib.ease.outCubic) * (1 - lib.seg(e, 0, 0.4));
  if (a <= 0) return;
  const n = T_CHECK.filter((c) => t >= c).length, last = n ? T_CHECK[n - 1] : -9, r = lib.tween(t, last, last + 0.2, lib.easeOf(tokens.ease.enter));
  const x = 120, y = 108;
  ctx.save(); ctx.globalAlpha *= a;
  lib.setFont(ctx, tokens, "mono", 46); ctx.fillStyle = C("muted"); lib.drawText(ctx, "STEP", x, y);
  const nx = x + ctx.measureText("STEP ").width, dw = ctx.measureText("0").width;
  ctx.save(); ctx.beginPath(); ctx.rect(nx - 4, y - 48, dw + 8, 64); ctx.clip(); ctx.fillStyle = C("ink");
  const a0 = ctx.globalAlpha;
  if (n && r < 1) { ctx.globalAlpha = a0 * (1 - r); lib.drawText(ctx, String(n - 1), nx, y - 40 * r); }
  ctx.globalAlpha = a0 * (n ? r : 1); lib.drawText(ctx, String(n), nx, y + 40 * (1 - (n ? r : 1)));
  ctx.restore();
  ctx.fillStyle = C("muted"); lib.drawText(ctx, "/3", nx + dw, y);
  ctx.restore();
}

export function renderAt(t, ctx, tokens, lib) {
  const e = t >= T_PUSH ? lib.easeOf(tokens.ease.emphasized)(lib.seg(t, T_PUSH, T_PUSH + PUSH_DUR)) : 0;
  ground(ctx, t, tokens, lib);
  const back = 1 - lib.smoothstep(0, 0.6, e);       // everything but the opening card steps away
  if (back > 0) {
    ctx.save(); ctx.globalAlpha = back;
    skeletons(ctx, t, tokens, lib); rail(ctx, t, tokens, lib); caption(ctx, t, tokens, lib);
    const ks = [0, 1, 2].filter((k) => t >= T_CARD[k] && !(k === 2 && e > 0)).map((k) => ({ k, R: cardRect(t, k, tokens, lib) }));
    ks.sort((a, b) => a.R.f - b.R.f).forEach(({ k, R }) => drawCard(ctx, t, k, R, tokens, lib));   // the focused card on top
    ctx.restore();
  }
  capsule(ctx, t, tokens, lib);
  inputPill(ctx, t, tokens, lib);
  if (back > 0) { ctx.save(); ctx.globalAlpha = back; bubble(ctx, t, tokens, lib); ctx.restore(); }
  if (e > 0) {                                       // container transform: the draft card opens into the screen
    const R0 = cardRect(t, 2, tokens, lib), R = lerpRect(R0, { x: 0, y: 0, w: lib.W, h: lib.H }, e, lib);
    drawCard(ctx, t, 2, { ...R, f: 1, alpha: 1 }, tokens, lib, e);
  }
  hud(ctx, t, e, tokens, lib);
}

// foley: events.json is generated from this list (node styles/_swatch/foley.mjs pastel-ui); pan = the sound's x on screen
const panX = (x) => Math.round((2 * x / 1920 - 1) * 0.75 * 100) / 100;
const CARD_X = [408, 960, 1512];
export const FOLEY = [
  { t: T_WAKE, sfx: "air", gain_db: -8, pan: 0, dur: 0.5, dir: "up", bright: 0.35 },                       // the colours grow out
  { t: T_TYPE, sfx: "typing", gain_db: 0, pan: panX(680), dur: 0.6 },                                      // the title typed
  { t: T_SEND, sfx: "click", gain_db: -8, pan: panX(1536) },                                               // send
  { t: T_SEND + 0.02, sfx: "swoosh_tonal", gain_db: -7, pan: 0.3, dur: 0.38, dir: "up", bright: 0.3, pan_from: 0.45, pan_to: 0 },   // it flies up
  { t: T_DOTS, sfx: "pop", gain_db: -5, pan: 0, pitch: 3 },                                               // the reply starts typing
  { t: T_TOKEN[3], sfx: "tick", gain_db: -2, pan: 0.05 },                                                  // 代码 lands
  ...T_CARD.map((tc, k) => ({ t: tc + 0.06, sfx: "pop", gain_db: k === 2 ? -1 : -4, pan: panX(CARD_X[k]) })),   // cards land
  ...T_CHECK.map((tc, k) => ({ t: tc, sfx: "toggle", gain_db: k ? -6 : -4, pan: panX(CARD_X[k]) })),       // the focus moves
  { t: T_PLAY, sfx: "tick", gain_db: -3, pan: panX(1400) },                                                // the draft plays
  { t: T_PUSH, sfx: "whoosh", gain_db: -9, pan: 0.2, dur: 0.5, dir: "up", bright: 0.4, tone: 0.2, pan_from: 0.45, pan_to: 0 },  // the card opens
  { t: T_LAND, sfx: "pop", gain_db: -5, pan: panX(1574), pitch: -2 },                                      // the ball lands
  { t: T_NAME + 0.08, sfx: "shimmer", gain_db: -10, pan: 0, dur: 0.8, pitch: -7 },                         // the name settles (in D)
];
