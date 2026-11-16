// Demo swatch: the starting template for a new style (swatch spec 2: 8 s in four beats, landscape and portrait).
// Not a style preset. Copy it and its tokens.json, score.json and events.json to styles/<slug>/, then make every beat
// this style's own (styles/_swatch/README.md, "样片规格"):
//
//   0.0–1.5  world      the world stands: palette and texture at a glance; the first big move at 0.1 s
//   1.5–4.5  signature  the move or transition this style is known by (here: three cards spring in, then a wipe)
//   4.5–7.0  type       a title and one caption line at the sizes a film would use (lib.TYPE), held to be read once
//   7.0–8.0  close      it settles, and the last frame is the first again, so the swatch loops
//
// One timing table (T) drives the picture, the foley (FOLEY → events.json: node styles/_swatch/foley.mjs <slug>) and
// the texts to check (texts() → bin/vh style check --text). tokens.json's "swatch" says the length and the beats; keep
// T in step with them (the defaults for 8 s are 1.5 / 4.5 / 7.0). bin/vh style check --text times the reads with
// readcheck: the title and caption must be fully shown for one read at a brisk pace (here about 2.1 s). Everything is laid out from lib.W, lib.H and
// lib.SAFE, so the same code draws the portrait version (lib.PORTRAIT; render.sh --aspect portrait).

const T = {
  grid: [0.1, 0.9], band: [0.1, 0.6], rule: [0.6, 1.4],   // world
  cards: [1.6, 1.95, 2.3], arrows: [2.65, 2.95], push: [3.05, 3.95], wipe: [3.95, 4.55],   // signature
  title: 4.4, caption: 4.7, read: [4.95, 7.15],          // type (the wipe already shows the title coming in; read: fully shown → starts to leave)
  out: [7.15, 7.5], retract: [7.3, 7.95],                // close
};
const pan = (u) => Math.round((2 * u - 1) * 70) / 100;   // u = x / W, so landscape and portrait pan alike
export const FOLEY = [
  { t: T.grid[0], sfx: "whoosh", gain_db: -10, pan: -0.3 },                              // the band sweeps in
  ...T.cards.map((t, k) => ({ t: t + 0.08, sfx: "pop", gain_db: -10, pan: pan(0.25 + k * 0.25) })),   // each card lands
  ...T.arrows.map((t) => ({ t: t + 0.3, sfx: "tick", gain_db: -14, pan: 0.1 })),         // each arrow arrives
  { t: T.wipe[0] + 0.05, sfx: "whoosh", gain_db: -9, pan: 0.2 },                         // the signature wipe
  { t: T.title + 0.1, sfx: "click", gain_db: -10, pan: 0 },                              // the title lands
  { t: T.out[0] + 0.05, sfx: "paper", gain_db: -14, pan: 0 },                            // the page clears
];

/** The reads of the type beat, for bin/vh textcheck and readcheck (readcheck's format: start = fully shown). */
export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: T.read[0], end: T.read[1] },
    { text: lib.TITLE_EN, start: T.read[0], end: T.read[1] },
    { text: lib.CAPTION_ZH, start: T.read[0], end: T.read[1] },
  ];
}

let L = null;   // layout, computed once in setup (pure data: the same in every worker)

export async function setup(ctx, tokens, lib) {
  const { SAFE, W, H, PORTRAIT, TYPE } = lib;
  const A = SAFE.title;
  const n = 3, gap = PORTRAIT ? 60 : 110;
  const cw = PORTRAIT ? Math.min(560, A.w * 0.62) : (A.w - gap * (n - 1)) / n * 0.82;
  const ch = PORTRAIT ? (A.h * 0.62 - gap * (n - 1)) / n : cw * 0.66;
  const cards = Array.from({ length: n }, (_, k) => PORTRAIT
    ? { x: W / 2, y: H * 0.5 + (k - 1) * (ch + gap) }
    : { x: A.x0 + (A.w / n) * (k + 0.5), y: H * 0.5 });
  lib.setFont(ctx, tokens, "zh", 10);
  const title = lib.fitText(ctx, lib.TITLE_ZH, A.w * 0.92, (s) => lib.setFont(ctx, tokens, "zh", s), { min: 84, max: TYPE.title });
  L = { cards, cw, ch, title, cap: TYPE.caption, en: TYPE.label, ty: H * (PORTRAIT ? 0.44 : 0.42) };
}

export function renderAt(t, ctx, tokens, lib) {
  const { seg } = lib;
  const P = (k) => lib.color(tokens, k);
  if (t < T.wipe[0]) page(ctx, t, tokens, lib, cardsLayer);
  else if (t < T.wipe[1]) lib.wipe(ctx, lib.easeOf(tokens.motion.move)(seg(t, T.wipe[0], T.wipe[1])),
    (x) => page(x, t, tokens, lib, cardsLayer), (x) => page(x, t, tokens, lib, typeLayer), { angle: 0, soft: 0.04 });
  else page(ctx, t, tokens, lib, typeLayer);
  // post: the same texture over every beat, so the wipe does not double it
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 24, seed: 11 });
  lib.vignette(ctx, { strength: tokens.texture.vignette, inner: 0.5, color: P("ink") });
}

/** The paper and the grid (the world), then one layer on top. */
function page(ctx, t, tokens, lib, layer) {
  const { SAFE, W, H, seg } = lib;
  const P = (k) => lib.color(tokens, k);
  const enter = lib.easeOf(tokens.motion.enter);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  lib.paper(ctx, { tone: P("bg"), amount: tokens.texture.paper, blotch: 0.05, fiber: 0.6, seed: 4 });
  // grid rules draw on at 0.1 s and draw back in the close, so the last frame is the first
  const A = SAFE.action;
  const grow = (i) => enter(seg(t, T.grid[0] + i * 0.05, T.grid[1] - 0.25 + i * 0.05)) * (1 - lib.easeOf(tokens.motion.move)(seg(t, T.retract[0] + i * 0.04, T.retract[1] - 0.2 + i * 0.04)));
  ctx.save(); ctx.strokeStyle = P("rule"); ctx.lineWidth = 2;
  for (let i = 1; i < 6; i++) {
    const u = grow(i);
    if (u <= 0) continue;
    lib.strokePartial(ctx, [[A.x0 + i * A.w / 6, A.y0], [A.x0 + i * A.w / 6, A.y1]], u);
    lib.strokePartial(ctx, [[A.x0, A.y0 + i * A.h / 6], [A.x1, A.y0 + i * A.h / 6]], u);
  }
  ctx.restore();
  // the accent band: the first big move (over a fifth of the frame) sweeps in, then narrows into the margin rule that
  // stays for the whole swatch, and is drawn back up in the close
  const b = enter(seg(t, T.band[0], T.band[1])), r = lib.ease.inOutCubic(seg(t, T.rule[0], T.rule[1]));
  const back = 1 - lib.easeOf(tokens.motion.move)(seg(t, T.retract[0], T.retract[1]));
  if (b > 0 && back > 0) {
    const x = lib.lerp(lib.lerp(-0.3 * W, 0.2 * W, b), A.x0 - 28, r), w = lib.lerp(0.28 * W, 8, r);
    const y0 = lib.lerp(0, A.y0, r), y1 = lib.lerp(H, A.y1, r);
    ctx.save(); ctx.fillStyle = P("accent");
    ctx.fillRect(x, y0, w, (y1 - y0) * back); ctx.restore();
  }
  layer(ctx, t, tokens, lib);
}

/** Signature: outline → storyboard → draft, each card springing in, then joined, then a slow push. */
function cardsLayer(ctx, t, tokens, lib) {
  const { W, H, PORTRAIT } = lib;
  const P = (k) => lib.color(tokens, k);
  const s = 1 + 0.04 * lib.ease.inOutSine(lib.seg(t, T.push[0], T.push[1]));   // no frozen stretch after the cards land
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(s, s); ctx.translate(-W / 2, -H / 2);
  L.cards.forEach((c, k) => card(ctx, t, tokens, lib, c, k));
  T.arrows.forEach((t0, k) => {
    const a = L.cards[k], z = L.cards[k + 1], u = lib.tween(t, t0, t0 + 0.4, lib.ease.outCubic);
    if (u <= 0) return;
    const p0 = PORTRAIT ? [a.x, a.y + L.ch / 2 + 14] : [a.x + L.cw / 2 + 14, a.y];
    const p1 = PORTRAIT ? [z.x, z.y - L.ch / 2 - 14] : [z.x - L.cw / 2 - 14, z.y];
    ctx.save(); ctx.strokeStyle = P("ink"); ctx.lineWidth = 5; ctx.lineCap = "round";
    lib.strokePartial(ctx, [p0, p1], u);
    ctx.restore();
  });
  ctx.restore();
}

function card(ctx, t, tokens, lib, c, k) {
  const P = (n) => lib.color(tokens, n);
  const t0 = T.cards[k], p = lib.spring(t - t0, tokens.motion.spring);
  if (t < t0) return;
  const w = L.cw, h = L.ch, x = c.x - w / 2, y = c.y - h / 2 + (1 - p) * 80;
  ctx.save(); ctx.globalAlpha = lib.clamp((t - t0) / 0.12);
  ctx.fillStyle = lib.rgba(P("bg"), 0.94); ctx.strokeStyle = P("ink"); ctx.lineWidth = 5;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 20); ctx.fill(); ctx.stroke();
  const q = lib.tween(t, t0 + 0.15, t0 + 0.7, lib.ease.outCubic);   // the icon draws on inside the card
  ctx.strokeStyle = P("ink"); ctx.fillStyle = P("ink"); ctx.lineWidth = 7; ctx.lineCap = "round";
  const ix = x + w * 0.16, iy = y + h * 0.2, iw = w * 0.68, ih = h * 0.6;
  if (k === 0) {                                          // outline: three lines
    for (let r = 0; r < 3; r++) {
      const ly = iy + r * ih / 2, u = lib.clamp(q * 3 - r);
      if (u > 0) lib.strokePartial(ctx, [[ix, ly], [ix + iw * (r === 2 ? 0.6 : 1), ly]], u);
    }
  } else if (k === 1) {                                   // storyboard: three panels
    for (let r = 0; r < 3; r++) {
      const u = lib.clamp(q * 3 - r); if (u <= 0) continue;
      const pw = (iw - 2 * 16) / 3; ctx.globalAlpha = u; ctx.lineWidth = 5;
      ctx.strokeRect(ix + r * (pw + 16), iy, pw, ih);
    }
  } else {                                                // draft: the one accent mark, a filled frame
    ctx.globalAlpha = q; ctx.fillStyle = P("accent");
    ctx.beginPath(); ctx.roundRect(ix, iy, iw, ih, 10); ctx.fill();
  }
  ctx.restore();
}

/** Type: the title and one caption line at real sizes, then they leave before the close. */
function typeLayer(ctx, t, tokens, lib) {
  const { W, H, SAFE } = lib;
  const P = (k) => lib.color(tokens, k);
  const out = 1 - lib.seg(t, T.out[0], T.out[1]);
  if (out <= 0) return;
  ctx.save(); ctx.globalAlpha = out;
  lib.setFont(ctx, tokens, "zh", L.title); ctx.fillStyle = P("ink");
  const lay = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: L.ty, align: "center", tracking: lib.tracking(tokens, "zh", L.title) });
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const t0 = T.title + i * tokens.motion.stagger;
    if (t < t0) return null;
    const p = lib.spring(t - t0, tokens.motion.spring);
    return { dy: (1 - p) * 40, alpha: lib.clamp((t - t0) / 0.1) };
  });
  lib.setFont(ctx, tokens, "display", L.en); ctx.fillStyle = P("muted");
  ctx.globalAlpha = out * lib.clamp((t - T.title - 0.2) / 0.2);
  lib.drawText(ctx, lib.TITLE_EN, W / 2, L.ty + L.title * 0.95, { align: "center", tracking: lib.tracking(tokens, "display", L.en) });
  // the caption sits where a film's caption would: the lower third, inside title-safe
  const cy = SAFE.title.y1 - L.cap * 0.6;
  lib.setFont(ctx, tokens, "zh", L.cap); ctx.fillStyle = P("ink");
  ctx.globalAlpha = out * lib.clamp((t - T.caption) / 0.15);
  lib.drawText(ctx, lib.CAPTION_ZH, W / 2, cy, { align: "center" });
  ctx.restore();
}
