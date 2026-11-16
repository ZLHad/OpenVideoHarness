// 纸桌档案 · paper-desk-dossier — swatch spec 2 (9 s, four beats, landscape and portrait).
//
// (9 s: a longer swatch than the default 8, so the slide along the sheet can take 1.2 s.)
// A long cream sheet on a dark wooden desk, seen from above; the camera travels along it. Real things land on the sheet
// one after another with their weight (a big soft shadow that tightens as they touch down): an archival photograph,
// an index card that types itself, a rubber stamp, a second photograph under a clip, and a red pen that circles the
// detail and writes the note. Then the camera slides on to a clean stretch where the title lands as a pasted slip, and
// in the close it travels past the end of the sheet to bare desk again, the same desk as the first frame (the wood is
// periodic in the travel, so the loop is exact).
//
//   0.0–1.25  world      the camera runs in from bare desk; the sheet's head comes into view and settles
//   1.5–4.2   signature  photo · card (typed) · stamp · second photo · red pen circle, arrow, note
//   4.2–7.78  type       the camera slides on (4.2–5.4, slow enough to follow); the title slip lands; title and caption read once
//   7.78–8.95 close      the camera runs past the tail of the sheet to bare desk (= frame 0)
//
// Photographs: Carleton E. Watkins, "Half Dome, Yosemite Valley" and "Merced River, Yosemite Valley" (ca. 1865), public
// domain, via the Library of Congress / Wikimedia Commons (STYLE.md, "素材"). Everything else is drawn here.
// One timing table (T) drives the picture, the foley (FOLEY → events.json) and the reads (texts()).

const T = {
  run: [0.0, 1.25],                       // the camera runs in and settles on the head of the sheet
  photo: 1.12, tape: 1.34, card: 1.6, type: [1.8, 3.2], photo2: 2.25,
  stampDown: [2.45, 2.66], stamp: 2.66, stampUp: [2.66, 2.9],
  penIn: [2.72, 3.0], circle: [3.0, 3.42], arrow: [3.42, 3.66], note: [3.72, 4.12], penOut: [4.12, 4.42],
  slide: [4.2, 5.4], slip: 5.12, caption: 5.38, read: [5.5, 7.75],   // the slide takes 1.2 s: the change stays legible
  penIn2: [5.55, 5.9], underline: [5.9, 6.3], penOut2: [6.3, 6.65],
  out: [7.78, 8.95],
};
const WRITE = "约 1865 年";        // the red note: the date the photograph was taken (Library of Congress: "ca. 1865")
const CARD = ["HALF DOME, YOSEMITE", "C. E. WATKINS, CA. 1865", "LIBRARY OF CONGRESS"];
const STAMP = "已核对";
const CPS = 46;                    // the card types itself at this many characters a second

const pan = (u) => Math.round((2 * u - 1) * 70) / 100;
export const FOLEY = [
  { t: 0.45, sfx: "paper", gain_db: -9, dur: 0.9, pan_from: 0.6, pan_to: -0.1 },                 // the sheet slides in
  { t: T.photo + 0.11, sfx: "paper", gain_db: -8, dur: 0.22, bright: -0.4, pan: -0.45 },          // the photo lands
  { t: T.card + 0.11, sfx: "paper", gain_db: -10, dur: 0.18, bright: -0.1, pan: 0.05 },           // the card lands
  { t: T.type[0], sfx: "typing", gain_db: -13, dur: T.type[1] - T.type[0], pan: 0.05 },                             // it types itself
  { t: T.photo2 + 0.11, sfx: "paper", gain_db: -11, dur: 0.2, bright: -0.2, pan: 0.5 },           // the second photo
  { t: T.stamp, sfx: "impact", gain_db: -15, pitch: 9, pan: 0.15 },                                 // the stamp's thud
  { t: T.circle[0] + 0.05, sfx: "paper", gain_db: -19, dur: 0.38, bright: 0.8, tone: 0.1, pan: -0.25 },   // pen on the photo
  { t: T.note[0] + 0.05, sfx: "paper", gain_db: -19, dur: 0.4, bright: 0.9, tone: 0.1, pan: -0.05 },      // pen writes the note
  { t: (T.slide[0] + T.slide[1]) / 2, sfx: "air", gain_db: -12, dur: 1.1, pan_from: 0.5, pan_to: -0.5 },  // the camera slides on
  { t: T.slip + 0.25, sfx: "paper", gain_db: -10, dur: 0.2, bright: -0.3, pan: 0 },               // the title slip lands
  { t: T.underline[0] + 0.05, sfx: "paper", gain_db: -20, dur: 0.35, bright: 0.9, tone: 0.1, pan: 0 },    // the red underline
  { t: 8.5, sfx: "paper", gain_db: -10, dur: 0.9, pan_from: 0.4, pan_to: -0.7 },                  // the sheet runs out
];

/** The reads of the type beat (readcheck's format: start = fully shown). */
export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: T.read[0], end: T.read[1] },
    { text: lib.TITLE_EN, start: T.read[0], end: T.read[1] },
    { text: lib.CAPTION_ZH, start: T.read[0], end: T.read[1] },
  ];
}

// ── layout (setup) ────────────────────────────────────────────────────────────────────────────────────────────────
// Paper coordinates: u runs along the sheet (its head is u = 0), v across it in screen px. Landscape lays u along x,
// portrait along y; the camera is c, the u at the screen's leading edge.
const LEN = 3960;                       // the sheet's length
const C0 = -1950, C1 = -80, C2 = -10, C5 = LEN + 40;   // camera stops (u at the leading edge); C3, C4 per aspect (setup)
let C3 = 1820, C4 = 1865;               // after the slide: the signature's things are just off screen, the tail not yet in
const PERIOD = C5 - C0;                 // the desk's wood repeats over the whole travel: the last frame is the first
let L = null, IMG = {};

async function loadImage(name) {
  const im = new Image();
  im.src = new URL(`./${name}`, import.meta.url);
  await im.decode();
  return im;
}

export async function setup(ctx, tokens, lib) {
  const { W, H, PORTRAIT } = lib;
  IMG.dome = await loadImage("photo-half-dome.jpg");
  IMG.river = await loadImage("photo-merced-river.jpg");
  const P = (k) => lib.color(tokens, k);
  // the sheet's band across the travel (screen px), and where everything sits on it
  const band = PORTRAIT ? [84, 996] : [96, 838];
  const it = PORTRAIT ? {
    photo: { u: 650, v: 520, w: 690, rot: -0.034 },
    note: { u: 238, v: 760, size: 52 },
    card: { u: 1185, v: 560, w: 600, h: 300, rot: 0.024 },
    stamp: { u: 1272, v: 790, rot: -0.15 },
    photo2: { u: 1600, v: 600, w: 470, rot: 0.05 },
    slip: { u: 2760, v: 540, rot: -0.012 },
  } : {
    photo: { u: 470, v: 425, w: 560, rot: -0.038 },
    note: { u: 1000, v: 252, size: 48 },
    card: { u: 1080, v: 560, w: 470, h: 290, rot: 0.026 },
    stamp: { u: 1210, v: 655, rot: -0.15 },
    photo2: { u: 1560, v: 395, w: 380, rot: 0.06 },
    slip: { u: 2780, v: 450, rot: -0.012 },
  };
  L = { band, it, PORTRAIT };
  if (PORTRAIT) { C3 = 1900; C4 = 1945; }
  L.wood = woodTexture(lib, PORTRAIT ? W : H, P);
  L.paper = paperTexture(lib, band[1] - band[0], P);
  L.stampImg = stampTexture(lib, tokens, P);
  L.photo = toned(IMG.dome, lib, P);
  L.photo2 = toned(IMG.river, lib, P);
  // the title slip: sized to the title at the type beat's real size (lib.TYPE)
  lib.setFont(ctx, tokens, "zh", lib.TYPE.title);
  const lines = PORTRAIT ? ["每一帧，", "都是代码。"] : [lib.TITLE_ZH];
  const tw = Math.max(...lines.map((s) => ctx.measureText(s).width));
  L.slip = { lines, w: tw + (PORTRAIT ? 120 : 130), h: lines.length * lib.TYPE.title * 1.22 + lib.TYPE.label * 1.4 + 110 };
  L.slipLW = tw;
  lib.setFont(ctx, tokens, "hand", it.note.size);
  L.noteW = ctx.measureText(WRITE).width;
}

/** Dark walnut desk, planks along the travel; periodic over PERIOD so the last frame is the first. */
function woodTexture(lib, across, P) {
  const { hash, fbm2, clamp, rgb, TAU } = lib;
  const k = 2, A = Math.ceil(PERIOD / k), B = Math.ceil(across / k);   // generated at half size, drawn up
  const c = document.createElement("canvas");
  const portrait = L.PORTRAIT;
  c.width = portrait ? B : A; c.height = portrait ? A : B;
  const x = c.getContext("2d"), img = x.createImageData(c.width, c.height);
  const dark = rgb(P("desk")), light = rgb(P("desk2"));
  const plankW = 118;                     // half-size px across
  const R1 = A / (TAU * 150), R2 = A / (TAU * 520);   // noise on a circle in the run: periodic, never visibly repeating
  for (let b = 0; b < B; b++) {
    const plank = Math.floor((b + 40) / plankW), lb = (b + 40) - plank * plankW;
    const tint = (hash(31, plank) - 0.5) * 0.16;
    const fib = (hash(7, b) - 0.5) * 0.06 + (hash(8, Math.floor(b / 3)) - 0.5) * 0.05;   // long fibres: constant along the run
    for (let a = 0; a < A; a++) {
      const ph = TAU * a / A, cs = Math.cos(ph), sn = Math.sin(ph);
      const n1 = fbm2(R1 * cs + lb / 46, R1 * sn + plank * 7.3, { octaves: 3, seed: 4 });
      const n2 = fbm2(R2 * cs + plank * 3.1, R2 * sn + lb / 140, { octaves: 2, seed: 9 });
      const grain = 0.5 + 0.5 * Math.sin(TAU * (lb / 7.2 + 1.7 * n1 + 0.5 * n2));
      let m = 0.48 + 0.42 * n2 + tint + fib - 0.30 * Math.pow(grain, 5) + 0.10 * Math.pow(1 - grain, 8);
      const seam = lb < 2 ? 0.5 : lb < 4 ? 0.8 : 1;
      const tooth = 1 + (hash(a, b, 3) - 0.5) * 0.05;
      const i = (portrait ? (a * B + b) : (b * A + a)) * 4;
      for (let ch = 0; ch < 3; ch++) img.data[i + ch] = clamp((dark[ch] + (light[ch] - dark[ch]) * clamp(m)) * seam * tooth, 0, 255);
      img.data[i + 3] = 255;
    }
  }
  x.putImageData(img, 0, 0);
  const full = document.createElement("canvas");
  full.width = portrait ? across : PERIOD; full.height = portrait ? PERIOD : across;
  const f = full.getContext("2d"); f.imageSmoothingQuality = "high";
  f.drawImage(c, 0, 0, full.width, full.height);
  return full;
}

/** The cream sheet, LEN long: soft blotches, tooth, a few fibres, a faint fold. */
function paperTexture(lib, across, P) {
  const { fbm2, hash, clamp, rgb, rng, rgba, mixColor } = lib;
  const portrait = L.PORTRAIT;
  const c = document.createElement("canvas");
  c.width = portrait ? across : LEN; c.height = portrait ? LEN : across;
  const x = c.getContext("2d");
  // blotches on a coarse grid, drawn up smoothly
  const k = 6, cw = Math.ceil(c.width / k), ch = Math.ceil(c.height / k);
  const bc = document.createElement("canvas"); bc.width = cw; bc.height = ch;
  const bx = bc.getContext("2d"), bi = bx.createImageData(cw, ch), base = rgb(P("paper"));
  for (let j = 0; j < ch; j++) for (let i = 0; i < cw; i++) {
    const m = 1 + fbm2(i / 26, j / 26, { octaves: 4, seed: 12 }) * 0.045, q = (j * cw + i) * 4;
    for (let n = 0; n < 3; n++) bi.data[q + n] = clamp(base[n] * m, 0, 255);
    bi.data[q + 3] = 255;
  }
  bx.putImageData(bi, 0, 0);
  x.imageSmoothingQuality = "high"; x.drawImage(bc, 0, 0, c.width, c.height);
  // tooth
  const img = x.getImageData(0, 0, c.width, c.height);
  for (let p = 0, q = 0; q < img.data.length; p++, q += 4) {
    const m = 1 + (hash(p, 9) - 0.5) * 0.035;
    img.data[q] *= m; img.data[q + 1] *= m; img.data[q + 2] *= m;
  }
  x.putImageData(img, 0, 0);
  // fibres
  const r = rng(77), dark = rgba(mixColor(P("paper"), "#000000", 0.4), 0.09), light = rgba("#ffffff", 0.16);
  x.lineCap = "round";
  for (let f = 0; f < c.width * c.height / 2600; f++) {
    const px = r() * c.width, py = r() * c.height, a = r() * Math.PI * 2, len = 4 + r() * 16;
    x.strokeStyle = r() < 0.5 ? dark : light; x.lineWidth = 0.4 + r() * 0.6;
    x.beginPath(); x.moveTo(px, py); x.lineTo(px + Math.cos(a) * len, py + Math.sin(a) * len); x.stroke();
  }
  // a faint fold across the sheet, and the cut edges a shade darker
  const fold = (u) => {
    const g = portrait ? x.createLinearGradient(0, u - 14, 0, u + 14) : x.createLinearGradient(u - 14, 0, u + 14, 0);
    g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(0.48, "rgba(80,60,30,0.07)"); g.addColorStop(0.52, "rgba(255,255,255,0.14)"); g.addColorStop(1, "rgba(0,0,0,0)");
    x.fillStyle = g; portrait ? x.fillRect(0, u - 14, c.width, 28) : x.fillRect(u - 14, 0, 28, c.height);
  };
  fold(1395); fold(3020);
  x.strokeStyle = "rgba(90,70,40,0.22)"; x.lineWidth = 2; x.strokeRect(1, 1, c.width - 2, c.height - 2);
  return c;
}

/** The archival photograph mounted on its white border, toned to the sheet's warmth (once, in setup). */
function toned(im, lib, P) {
  const c = document.createElement("canvas"); c.width = im.naturalWidth; c.height = im.naturalHeight;
  const x = c.getContext("2d");
  x.filter = "sepia(0.25) contrast(1.06) brightness(0.98)";
  x.drawImage(im, 0, 0);
  return c;
}

/** The rubber-stamp impression: a double frame and three characters, the ink uneven (once, in setup). */
function stampTexture(lib, tokens, P) {
  const { hash, rgba } = lib;
  const w = 300, h = 136, c = document.createElement("canvas"); c.width = w + 20; c.height = h + 20;
  const x = c.getContext("2d"); x.translate(10, 10);
  x.strokeStyle = P("stamp"); x.fillStyle = P("stamp");
  x.lineWidth = 7; x.strokeRect(4, 4, w - 8, h - 8);
  x.lineWidth = 2.5; x.strokeRect(16, 16, w - 32, h - 32);
  lib.setFont(x, tokens, "zh", 74, { weight: 900 });
  x.textAlign = "center"; x.textBaseline = "middle"; x.letterSpacing = "10px";
  x.fillText(STAMP, w / 2 + 5, h / 2 + 4);
  // uneven ink: knock out specks and a dry patch, keep it pure (seeded)
  x.globalCompositeOperation = "destination-out";
  for (let i = 0; i < 2600; i++) {
    const px = hash(i, 1) * w, py = hash(i, 2) * h, r = 0.6 + hash(i, 3) * 1.8;
    x.fillStyle = rgba("#000", 0.35 + hash(i, 4) * 0.65);
    x.beginPath(); x.arc(px, py, r, 0, Math.PI * 2); x.fill();
  }
  const g = x.createLinearGradient(0, 0, w, h);
  g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(0.7, "rgba(0,0,0,0.05)"); g.addColorStop(1, "rgba(0,0,0,0.45)");
  x.fillStyle = g; x.fillRect(0, 0, w, h);
  return c;
}

// ── time ──────────────────────────────────────────────────────────────────────────────────────────────────────────
/** The camera: the u at the screen's leading edge. */
function camera(t, lib) {
  const { seg, lerp, ease } = lib;
  if (t < T.run[1]) return lerp(C0, C1, ease.outCubic(seg(t, T.run[0], T.run[1])));
  if (t < T.slide[0]) return lerp(C1, C2, ease.inOutSine(seg(t, T.run[1], T.slide[0])));
  if (t < T.slide[1]) return lerp(C2, C3, ease.inOutSine(seg(t, T.slide[0], T.slide[1])));
  if (t < T.out[0]) return lerp(C3, C4, ease.inOutSine(seg(t, T.slide[1], T.out[0])));
  return lerp(C4, C5, ease.inCubic(seg(t, T.out[0], T.out[1])));
}
const moving = (t) => t < 1.0 || (t > T.slide[0] && t < T.slide[1]) || t > T.out[0];

/** How far up an item still is as it lands at t0 (1 → 0, a little below 0 as it settles). */
function lift(t, t0, lib) {
  if (t < t0) return null;
  return 1 - lib.spring(t - t0, { w: 17, zeta: 0.58 });
}

// ── frame ─────────────────────────────────────────────────────────────────────────────────────────────────────────
export function renderAt(t, ctx, tokens, lib) {
  // a little motion blur where the camera moves fast; through the slide only a quarter shutter, so the sheet stays legible
  const sliding = t > T.slide[0] && t < T.slide[1];
  if (moving(t)) lib.motionBlur(ctx, t, (ts, x) => world(x, ts, tokens, lib, false), { samples: sliding ? 4 : 6, shutter: sliding ? 0.25 : 0.5 });
  else world(ctx, t, tokens, lib, true);
  // the lamp: a warm pool of light upper left, the corners falling off; then a fine grain
  const { W, H } = lib;
  ctx.save();
  const g = ctx.createRadialGradient(W * 0.38, H * 0.34, 0, W * 0.38, H * 0.34, Math.hypot(W, H) * 0.72);
  g.addColorStop(0, "rgba(255,226,170,0.10)"); g.addColorStop(0.55, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(10,5,2,0.42)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.restore();
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 12, seed: 23 });
}

function world(ctx, t, tokens, lib, crisp) {
  const { W, H, PORTRAIT } = lib;
  const c = camera(t, lib);
  // the stamp's thud: the camera gives a little
  const thud = t > T.stamp ? 3.2 * Math.exp(-(t - T.stamp) * 18) * Math.sin((t - T.stamp) * 55) : 0;
  ctx.save();
  ctx.translate(PORTRAIT ? 0 : thud * 0.3, PORTRAIT ? thud * 0.3 : thud);
  desk(ctx, c, lib);
  sheet(ctx, t, c, tokens, lib);
  ctx.restore();
  // the caption is the film's, not the paper's: it stays on screen while the read lasts
  caption(ctx, t, tokens, lib, crisp);
}

function desk(ctx, c, lib) {
  const { W, H, PORTRAIT } = lib;
  const span = PORTRAIT ? H : W, wood = L.wood;
  let a = ((c - C0) % PERIOD + PERIOD) % PERIOD;
  // draw [a, a + span) of the periodic wood, in up to two pieces
  const first = Math.min(span, PERIOD - a);
  if (PORTRAIT) {
    ctx.drawImage(wood, 0, a, W, first, 0, 0, W, first);
    if (first < span) ctx.drawImage(wood, 0, 0, W, span - first, 0, first, W, span - first);
  } else {
    ctx.drawImage(wood, a, 0, first, H, 0, 0, first, H);
    if (first < span) ctx.drawImage(wood, 0, 0, span - first, H, first, 0, span - first, H);
  }
}

/** Paper (u, v) → screen, given the camera. */
const S = (u, v, c) => (L.PORTRAIT ? [v, u - c] : [u - c, v]);

function sheet(ctx, t, c, tokens, lib) {
  const { W, H, PORTRAIT } = lib;
  const [v0, v1] = L.band, span = PORTRAIT ? H : W;
  const a = Math.max(0, c - 40), b = Math.min(LEN, c + span + 40);
  if (b <= a) return;
  // the sheet's shadow on the desk, then the visible piece of the sheet
  const [x0, y0] = S(a, v0, c), [x1, y1] = S(b, v1, c);
  ctx.save();
  ctx.shadowColor = "rgba(8,4,2,0.55)"; ctx.shadowBlur = 26; ctx.shadowOffsetX = 5; ctx.shadowOffsetY = 12;
  ctx.fillStyle = lib.color(tokens, "paper");
  ctx.fillRect(Math.min(x0, x1), Math.min(y0, y1), Math.abs(x1 - x0), Math.abs(y1 - y0));
  ctx.restore();
  if (PORTRAIT) ctx.drawImage(L.paper, 0, a, v1 - v0, b - a, v0, a - c, v1 - v0, b - a);
  else ctx.drawImage(L.paper, a, 0, b - a, v1 - v0, a - c, v0, b - a, v1 - v0);
  // things on the sheet, in the order they land
  const it = L.it;
  photo(ctx, t, c, it.photo, L.photo, T.photo, tokens, lib, { tape: T.tape });
  note(ctx, t, c, tokens, lib);
  card(ctx, t, c, tokens, lib);
  photo(ctx, t, c, it.photo2, L.photo2, T.photo2, tokens, lib, { clip: true });
  stamp(ctx, t, c, tokens, lib);
  slip(ctx, t, c, tokens, lib);
  const st = strokes(c, t, tokens, lib);
  marks(ctx, t, st, tokens, lib);
  penBody(ctx, penTip(t, st, lib), tokens, lib);
}

/** Put the context at an item's place, with its drop: scale, rotation and shadow follow how far up it still is. */
function place(ctx, t, c, item, t0, lib, draw) {
  const h = lift(t, t0, lib);
  if (h === null) return;
  const [x, y] = S(item.u, item.v, c);
  const k = Math.max(0, h);
  ctx.save();
  ctx.translate(x, y + (L.PORTRAIT ? 0 : 0));
  ctx.rotate(item.rot + 0.05 * h);
  const s = 1 + 0.13 * h;
  ctx.scale(s, s);
  ctx.globalAlpha = lib.clamp((t - t0) / 0.07);
  draw(ctx, {
    shadow: (fn) => {
      ctx.save();
      ctx.shadowColor = `rgba(18,10,4,${0.42 - 0.22 * k})`;
      ctx.shadowBlur = 7 + 40 * k; ctx.shadowOffsetX = 4 + 26 * k; ctx.shadowOffsetY = 7 + 34 * k;
      fn(); ctx.restore();
    },
  });
  ctx.restore();
}

function photo(ctx, t, c, item, img, t0, tokens, lib, opt = {}) {
  const P = (k) => lib.color(tokens, k);
  const iw = item.w, ih = iw * img.height / img.width, bd = Math.round(iw * 0.04), w = iw + 2 * bd, h = ih + 2 * bd + bd * 0.4;
  place(ctx, t, c, item, t0, lib, (x, { shadow }) => {
    shadow(() => { x.fillStyle = P("border"); x.fillRect(-w / 2, -h / 2, w, h); });
    x.drawImage(img, -iw / 2, -h / 2 + bd, iw, ih);
    // a slight gloss and the inner edge of the print
    x.strokeStyle = "rgba(60,45,30,0.25)"; x.lineWidth = 1.5; x.strokeRect(-iw / 2, -h / 2 + bd, iw, ih);
    const g = x.createLinearGradient(-w / 2, -h / 2, w / 2, h / 2);
    g.addColorStop(0, "rgba(255,255,255,0.07)"); g.addColorStop(0.5, "rgba(255,255,255,0)"); g.addColorStop(1, "rgba(0,0,0,0.05)");
    x.fillStyle = g; x.fillRect(-w / 2, -h / 2, w, h);
    if (opt.tape) {                                   // two strips of tape press down a beat after it lands
      const u = lib.clamp((t - opt.tape) / 0.12);
      if (u > 0) for (const sx of [-1, 1]) {
        x.save(); x.translate(sx * (w / 2 - 34), -h / 2 + 6); x.rotate(sx * 0.62); x.globalAlpha *= u;
        x.fillStyle = lib.rgba(P("tape"), 0.72); x.fillRect(-58, -17, 116, 34);
        x.strokeStyle = "rgba(120,100,60,0.18)"; x.lineWidth = 1; x.strokeRect(-58, -17, 116, 34);
        x.restore();
      }
    }
    if (opt.clip) {                                   // a paper clip over its top edge
      x.save(); x.translate(-w * 0.18, -h / 2 - 6); x.strokeStyle = P("clip"); x.lineWidth = 5; x.lineCap = "round";
      x.beginPath(); x.moveTo(0, 70); x.lineTo(0, -18); x.arc(13, -18, 13, Math.PI, 0); x.lineTo(26, 92); x.arc(17, 92, 9, 0, Math.PI);
      x.lineTo(8, 4); x.stroke();
      x.strokeStyle = "rgba(255,255,255,0.45)"; x.lineWidth = 1.6; x.beginPath(); x.moveTo(-1.5, 60); x.lineTo(-1.5, -16); x.stroke();
      x.restore();
    }
  });
}

function card(ctx, t, c, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const it = L.it.card, w = it.w, h = it.h;
  place(ctx, t, c, it, T.card, lib, (x, { shadow }) => {
    shadow(() => { x.fillStyle = P("card"); x.fillRect(-w / 2, -h / 2, w, h); });
    // index-card rules: one red head rule, blue lines
    x.strokeStyle = lib.rgba(P("pen"), 0.55); x.lineWidth = 2;
    x.beginPath(); x.moveTo(-w / 2, -h / 2 + 64); x.lineTo(w / 2, -h / 2 + 64); x.stroke();
    x.strokeStyle = "rgba(70,110,160,0.28)"; x.lineWidth = 1.4;
    for (let k = 1; k < 5; k++) { const y = -h / 2 + 64 + k * 46; x.beginPath(); x.moveTo(-w / 2, y); x.lineTo(w / 2, y); x.stroke(); }
    // the typed lines, one character at a time on a 15-char/s clock
    lib.setFont(x, tokens, "type", 27); x.fillStyle = P("ink"); x.textBaseline = "alphabetic";
    x.fillText("No. 07", -w / 2 + 26, -h / 2 + 46);
    let start = T.type[0];
    CARD.forEach((line, i) => {
      const n = Math.floor(lib.clamp((t - start) * CPS, 0, line.length));
      if (n > 0) x.fillText(line.slice(0, n), -w / 2 + 26, -h / 2 + 64 + (i + 1) * 46 - 10);
      start += line.length / CPS + 0.04;
    });
  });
}

function stamp(ctx, t, c, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const it = L.it.stamp, [x, y] = S(it.u, it.v, c);
  const img = L.stampImg;
  // the impression stays after the press
  if (t >= T.stamp) {
    ctx.save(); ctx.translate(x, y); ctx.rotate(it.rot);
    ctx.globalAlpha = 0.86; ctx.globalCompositeOperation = "multiply";
    const s = 0.8;
    ctx.drawImage(img, -img.width * s / 2, -img.height * s / 2, img.width * s, img.height * s);
    ctx.restore();
  }
  // the stamp itself, seen from above: down, a press, and up again
  let k = null;
  if (t >= T.stampDown[0] && t < T.stamp) k = 1 - lib.ease.inCubic(lib.seg(t, T.stampDown[0], T.stamp));
  else if (t >= T.stamp && t < T.stampUp[1]) k = lib.ease.outCubic(lib.seg(t, T.stampUp[0], T.stampUp[1]));
  if (k === null) return;
  ctx.save(); ctx.translate(x + 30 * k, y - 40 * k); ctx.rotate(it.rot);
  const s = 1 + 0.35 * k;
  ctx.scale(s, s); ctx.globalAlpha = 1 - lib.smoothstep(0.75, 1, k);
  ctx.shadowColor = `rgba(15,8,3,${0.5 - 0.25 * k})`; ctx.shadowBlur = 10 + 50 * k; ctx.shadowOffsetX = 6 + 40 * k; ctx.shadowOffsetY = 10 + 50 * k;
  ctx.fillStyle = P("rubber"); ctx.beginPath(); ctx.roundRect(-128, -60, 256, 120, 10); ctx.fill();
  ctx.shadowColor = "transparent";
  const g = ctx.createRadialGradient(-20, -18, 4, 0, 0, 62);
  g.addColorStop(0, "#9a6a43"); g.addColorStop(0.65, "#5e3a22"); g.addColorStop(1, "#3a2414");
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, 54, 0, Math.PI * 2); ctx.fill();
  ctx.fillStyle = "rgba(255,240,220,0.18)"; ctx.beginPath(); ctx.ellipse(-16, -18, 20, 12, -0.6, 0, Math.PI * 2); ctx.fill();
  ctx.restore();
}

// ── the red pen ─────────────────────────────────────────────────────────────────────────────────────────────────────
// Every red mark is one stroke of one pen: the ellipse round the dome, the arrow, the note, the underline. strokes(c)
// lays them out in screen px for the camera c; the pen's tip follows the stroke being drawn and lifts between strokes.

function polyLen(pts) { let l = 0; for (let i = 1; i < pts.length; i++) l += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return l; }
/** The point at fraction u of a polyline's length (the same measure as lib.strokePartial). */
function pointAt(pts, u) {
  let left = Math.max(0, Math.min(1, u)) * polyLen(pts);
  for (let i = 1; i < pts.length; i++) {
    const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
    if (left <= l || i === pts.length - 1) { const f = l ? Math.min(1, left / l) : 0; return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f]; }
    left -= l;
  }
  return pts[pts.length - 1];
}

function strokes(c, t, tokens, lib) {
  const ph = L.it.photo, nt = L.it.note, sl = L.it.slip;
  // the dome sits at about (0.79, 0.21) of the print; the ellipse is drawn in the print's own (rotated) frame
  const iw = ph.w, ih = iw * L.photo.height / L.photo.width, bd = Math.round(iw * 0.04), hh = ih + 2 * bd + bd * 0.4;
  const ex = (0.79 - 0.5) * iw, ey = -hh / 2 + bd + 0.21 * ih;
  const [px, py] = S(ph.u, ph.v, c), cs = Math.cos(ph.rot), sn = Math.sin(ph.rot);
  const E = (dx, dy) => [px + dx * cs - dy * sn, py + dx * sn + dy * cs];
  const rx = iw * 0.16, ry = ih * 0.17, ellipse = [];
  for (let i = 0; i <= 44; i++) {
    const a = -2.2 + (i / 44) * (Math.PI * 2 + 0.55), r = 1 + 0.06 * Math.sin(i * 0.9);
    ellipse.push(E(ex + Math.cos(a) * rx * r, ey + Math.sin(a) * ry * r));
  }
  // the arrow: from the ellipse out to the note (landscape: right, to the margin above the card; portrait: up)
  const from = L.PORTRAIT ? E(ex - rx * 0.1, ey - ry * 1.05) : E(ex + rx * 1.05, ey - ry * 0.25);
  const [nx, ny] = S(nt.u, nt.v, c);
  const to = L.PORTRAIT ? [nx - 40, ny + 46] : [nx - 150, ny - 14];
  const mid = [(from[0] + to[0]) / 2 + (L.PORTRAIT ? 40 : 0), (from[1] + to[1]) / 2 - (L.PORTRAIT ? 0 : 36)];
  const arrow = [];
  for (let i = 0; i <= 16; i++) { const u = i / 16; arrow.push([(1 - u) * (1 - u) * from[0] + 2 * u * (1 - u) * mid[0] + u * u * to[0], (1 - u) * (1 - u) * from[1] + 2 * u * (1 - u) * mid[1] + u * u * to[1]]); }
  // the note's baseline, where the pen runs while it writes
  const nw = L.noteW, noteLine = [[nx - nw / 2, ny + nt.size * 0.18], [nx + nw / 2, ny + nt.size * 0.18]];
  // the underline under the Chinese title, in the slip's frame
  const [sx, sy] = S(sl.u, sl.v, c), sc = Math.cos(sl.rot), ss = Math.sin(sl.rot);
  const TY = lib.TYPE, top = -L.slip.h / 2 + 52 + TY.title * 0.9, yl = top + (L.slip.lines.length - 1) * TY.title * 1.22 + TY.title * 0.3;
  const under = [];
  for (let i = 0; i <= 20; i++) {
    const u = i / 20, dx = -L.slipLW / 2 + u * L.slipLW, dy = yl + Math.sin(u * 5.2) * 3 + u * 4;
    under.push([sx + dx * sc - dy * ss, sy + dx * ss + dy * sc]);
  }
  return { ellipse, arrow, noteLine, under };
}

/** Where the pen's tip is at t and how far it is lifted (0 on the paper, 1 out of reach), or null when it is away. */
function penTip(t, st, lib) {
  const { W, H, seg, lerp, ease } = lib;
  const away = L.PORTRAIT ? [W + 260, H * 0.62] : [W + 240, H + 260];
  const go = (a, b, u, arc = 0.5) => { const e = ease.inOutCubic(u); return { x: lerp(a[0], b[0], e), y: lerp(a[1], b[1], e), lift: Math.max(arc * Math.sin(Math.PI * e), 0) }; };
  const on = (pts, u) => { const [x, y] = pointAt(pts, u); return { x, y, lift: 0 }; };
  const ends = (pts) => [pts[0], pts[pts.length - 1]];
  if (t < T.penIn[0]) return null;
  if (t < T.penIn[1]) { const r = go(away, st.ellipse[0], seg(t, ...T.penIn), 0); r.lift = 1 - ease.outCubic(seg(t, ...T.penIn)); return r; }
  if (t < T.circle[1]) return on(st.ellipse, ease.inOutSine(seg(t, ...T.circle)));
  if (t < T.arrow[1]) return on(st.arrow, ease.outCubic(seg(t, ...T.arrow)));
  if (t < T.note[0]) return go(ends(st.arrow)[1], st.noteLine[0], seg(t, T.arrow[1], T.note[0]), 0.35);
  if (t < T.note[1]) { const r = on(st.noteLine, ease.inOutSine(seg(t, ...T.note))); r.y += Math.sin(seg(t, ...T.note) * 46) * 9 - 6; return r; }
  if (t < T.penOut[1]) { const r = go(st.noteLine[1], away, seg(t, ...T.penOut), 0); r.lift = ease.inCubic(seg(t, ...T.penOut)); return r; }
  if (t < T.penIn2[0]) return null;
  if (t < T.penIn2[1]) { const r = go(away, st.under[0], seg(t, ...T.penIn2), 0); r.lift = 1 - ease.outCubic(seg(t, ...T.penIn2)); return r; }
  if (t < T.underline[1]) return on(st.under, ease.inOutSine(seg(t, ...T.underline)));
  if (t < T.penOut2[1]) { const r = go(st.under[st.under.length - 1], away, seg(t, ...T.penOut2), 0); r.lift = ease.inCubic(seg(t, ...T.penOut2)); return r; }
  return null;
}

/** The red marks drawn so far (under the pen). */
function marks(ctx, t, st, tokens, lib) {
  if (t < T.circle[0]) return;
  const P = (k) => lib.color(tokens, k);
  ctx.save();
  ctx.strokeStyle = P("pen"); ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.globalAlpha = 0.93;
  ctx.lineWidth = 5.5; lib.strokePartial(ctx, st.ellipse, lib.ease.inOutSine(lib.seg(t, ...T.circle)));
  const ua = lib.ease.outCubic(lib.seg(t, ...T.arrow));
  if (ua > 0) {
    ctx.lineWidth = 4.5; lib.strokePartial(ctx, st.arrow, ua);
    if (ua > 0.92) {                                    // the head
      const n = st.arrow.length - 1, [ax, ay] = st.arrow[n], [bx, by] = st.arrow[n - 3], ang = Math.atan2(ay - by, ax - bx);
      ctx.beginPath(); ctx.moveTo(ax + Math.cos(ang + 2.6) * 22, ay + Math.sin(ang + 2.6) * 22); ctx.lineTo(ax, ay);
      ctx.lineTo(ax + Math.cos(ang - 2.6) * 22, ay + Math.sin(ang - 2.6) * 22); ctx.stroke();
    }
  }
  const uu = lib.ease.inOutSine(lib.seg(t, ...T.underline));
  if (uu > 0) { ctx.lineWidth = 5; lib.strokePartial(ctx, st.under, uu); }
  ctx.restore();
}

/** The pen itself, seen from above: a red barrel lying down-right from its tip, its shadow wider as it lifts. */
function penBody(ctx, tip, tokens, lib) {
  if (!tip) return;
  const k = tip.lift, ang = L.PORTRAIT ? 0.95 : 0.7;
  const draw = (x, shade) => {
    x.beginPath();
    x.moveTo(0, 0); x.lineTo(36, -8); x.lineTo(110, -10); x.lineTo(340, -11); x.arc(340, 0, 11, -Math.PI / 2, Math.PI / 2); x.lineTo(110, 10); x.lineTo(36, 8); x.closePath();
    if (shade) { x.fill(); return; }
  };
  ctx.save();
  // the shadow falls down-right of the pen and drifts further out as it lifts
  ctx.save();
  ctx.translate(tip.x + 10 + 46 * k, tip.y + 16 + 58 * k); ctx.rotate(ang);
  ctx.filter = `blur(${(3 + 14 * k).toFixed(1)}px)`; ctx.fillStyle = `rgba(20,10,4,${(0.42 - 0.2 * k).toFixed(3)})`;
  draw(ctx, true); ctx.restore();
  ctx.translate(tip.x, tip.y); ctx.rotate(ang); const s = 1 + 0.07 * k; ctx.scale(s, s);
  // nib, grip, barrel, clip
  ctx.fillStyle = "#C9C2B6"; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(36, -8); ctx.lineTo(36, 8); ctx.closePath(); ctx.fill();
  ctx.fillStyle = lib.color(tokens, "pen"); ctx.beginPath(); ctx.arc(1.5, 0, 2.2, 0, Math.PI * 2); ctx.fill();
  const g = ctx.createLinearGradient(0, -11, 0, 11);
  g.addColorStop(0, "#E4574B"); g.addColorStop(0.35, "#B4231B"); g.addColorStop(1, "#5E100C");
  ctx.fillStyle = "#2A1714"; ctx.fillRect(36, -9.5, 74, 19);
  ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(110, -11); ctx.lineTo(340, -11); ctx.arc(340, 0, 11, -Math.PI / 2, Math.PI / 2); ctx.lineTo(110, 11); ctx.closePath(); ctx.fill();
  ctx.fillStyle = "rgba(255,235,225,0.45)"; ctx.fillRect(116, -7.5, 214, 2.6);
  ctx.strokeStyle = "#B9BCC1"; ctx.lineWidth = 3.5; ctx.lineCap = "round";
  ctx.beginPath(); ctx.moveTo(262, -14); ctx.lineTo(332, -14); ctx.stroke();
  ctx.restore();
}

/** The red note in the margin, written left to right (a clip that follows the pen). */
function note(ctx, t, c, tokens, lib) {
  if (t < T.note[0]) return;
  const P = (k) => lib.color(tokens, k);
  const nt = L.it.note, [x, y] = S(nt.u, nt.v, c);
  ctx.save();
  lib.setFont(ctx, tokens, "hand", nt.size);
  const w = L.noteW, x0 = x - w / 2;
  const u = lib.ease.inOutSine(lib.seg(t, T.note[0], T.note[1]));
  ctx.beginPath(); ctx.rect(x0 - 10, y - nt.size, (w + 20) * u, nt.size * 1.6); ctx.clip();
  ctx.translate(x, y); ctx.rotate(-0.04);
  ctx.fillStyle = P("pen"); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText(WRITE, 0, 0);
  ctx.restore();
}

/** The title slip: pasted onto a clean stretch of the sheet; the red pen underlines it once it has been read a moment. */
function slip(ctx, t, c, tokens, lib) {
  if (t < T.slip) return;
  const P = (k) => lib.color(tokens, k);
  const it = L.it.slip, sl = L.slip, w = sl.w, h = sl.h, TY = lib.TYPE;
  place(ctx, t, c, it, T.slip, lib, (x, { shadow }) => {
    shadow(() => { x.fillStyle = P("card"); x.fillRect(-w / 2, -h / 2, w, h); });
    x.strokeStyle = "rgba(90,70,40,0.18)"; x.lineWidth = 1.5; x.strokeRect(-w / 2 + 0.75, -h / 2 + 0.75, w - 1.5, h - 1.5);
    lib.setFont(x, tokens, "zh", TY.title); x.fillStyle = P("ink"); x.textAlign = "center"; x.textBaseline = "alphabetic";
    const top = -h / 2 + 52 + TY.title * 0.9;
    sl.lines.forEach((line, i) => x.fillText(line, 0, top + i * TY.title * 1.22));
    const yEn = top + (sl.lines.length - 1) * TY.title * 1.22 + TY.label * 1.55;
    lib.setFont(x, tokens, "en", TY.label, { style: "italic" }); x.fillStyle = P("muted");
    x.fillText(lib.TITLE_EN, 0, yEn);
  });
}

/** The caption: where a film's would be (landscape: on the desk below the sheet; portrait: on the sheet), held for the read. */
function caption(ctx, t, tokens, lib, crisp) {
  const a = lib.clamp((t - T.caption) / 0.12) * (1 - lib.seg(t, T.out[0] - 0.02, T.out[0] + 0.14));
  if (a <= 0) return;
  const P = (k) => lib.color(tokens, k);
  const { W, SAFE, TYPE, PORTRAIT } = lib;
  const y = SAFE.title.y1 - TYPE.caption * 0.55;
  ctx.save(); ctx.globalAlpha = a;
  lib.setFont(ctx, tokens, "zh", TYPE.caption, { weight: 500 });
  ctx.fillStyle = PORTRAIT ? P("ink") : P("caption");
  ctx.textBaseline = "middle";
  lib.drawText(ctx, lib.CAPTION_ZH, W / 2, y, { align: "center", tracking: TYPE.caption * 0.06 });
  ctx.restore();
}
