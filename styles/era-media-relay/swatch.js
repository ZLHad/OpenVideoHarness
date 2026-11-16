// Era media relay: the same thing drawn again and again, each time with the tools of another age. What changes is the
// pen, not the place: the swallow stays where it is while the brush, the woodblock, the cathode-ray beam and the pixel
// grid take it over one after another, and each takeover is that tool's own way of making a picture.
//
//   0.0–1.5  world      a brush paints a swallow on rice paper in four strokes (wet ink, dry hairs at the ends)
//   1.5–4.5  signature  the relay: a roller prints it as a woodblock (and the seal goes down); a scan beam redraws it in
//                       green phosphor; the screen coarsens into pixels and the swallow becomes a two-frame sprite
//   4.5–7.5  type       the title, its English line and the caption are typed in pixels under the flapping sprite
//   7.5–9.0  close      a drop of water lands and blooms out across the screen into blank rice paper; the brush comes
//                       back to where it began: the last frame is the first again
//
// One table (T) drives the picture, the foley (FOLEY → events.json) and the reads. Strokes: styles/_swatch/vendor/hand.js.
import { prep, pen, drawn, mj } from "../../vendor/hand.js";

export const fonts = ["Hiragino Sans GB", "Silom"];

const T = {
  body: [0.10, 0.46], wingUp: [0.62, 0.40], wingDn: [1.06, 0.26], tail: [1.36, 0.10],   // brush: [start, duration]
  roller: [1.5, 2.25], seal: 2.45,                                                       // → woodblock print
  beam: [2.8, 3.35], jolt: 3.5,                                                          // → cathode-ray screen
  pixel: [3.72, 4.3], flap: 6,                                                           // → pixels; the sprite flaps at 6 fps
  title: [4.60, 0.055], en: [4.80, 0.45], caption: [5.05, 0.04],                          // typed
  read: 7.5,
  drop: [7.5, 7.72], bloom: [7.72, 8.75], brushBack: [8.25, 8.95],                       // close
};
const pan = (u) => Math.round((2 * u - 1) * 70) / 100;
export const FOLEY = [
  { t: T.body[0], sfx: "sfx/brush_L.wav", gain_db: -4, pan: pan(0.55), role: "detail" },
  { t: T.wingUp[0], sfx: "sfx/brush_M.wav", gain_db: -5, pan: pan(0.5), role: "detail" },
  { t: T.wingDn[0], sfx: "sfx/brush_S.wav", gain_db: -6, pan: pan(0.52), role: "detail" },
  { t: T.roller[0], sfx: "sfx/roller.wav", gain_db: -5, pan_from: -0.6, pan_to: 0.6, role: "hero" },
  { t: T.seal, sfx: "sfx/seal.wav", gain_db: -6, pan: pan(0.78), role: "detail" },
  { t: T.beam[0], sfx: "sfx/crt_on.wav", gain_db: -6, pan: 0, role: "hero" },
  { t: T.jolt, sfx: "glitch", gain_db: -14, pan: 0.1 },
  { t: T.pixel[0], sfx: "sfx/pixel_down.wav", gain_db: -7, pan: 0, role: "detail" },
  { t: T.title[0], sfx: "sfx/chip_type.wav", gain_db: -5, pan: 0, role: "detail" },
  { t: T.drop[1], sfx: "sfx/drop.wav", gain_db: -4, pan: 0, role: "hero" },
  { t: T.bloom[0] + 0.1, sfx: "air", gain_db: -12, dur: 1.0, dir: "up", pan: 0 },
];

export function texts(lib) {
  const n = (s) => [...s].length;
  return [
    { text: lib.TITLE_ZH, start: +(T.title[0] + n(lib.TITLE_ZH) * T.title[1]).toFixed(3), end: T.read },
    { text: lib.TITLE_EN, start: +(T.en[0] + T.en[1]).toFixed(3), end: T.read },
    { text: lib.CAPTION_ZH, start: +(T.caption[0] + n(lib.CAPTION_ZH) * T.caption[1]).toFixed(3), end: T.read },
  ];
}

// the swallow, in units of its own size: beak to the right, two scythe wings swept back, a deep forked tail
const SWALLOW = [[0.44, 0.00], [0.36, -0.045], [0.24, -0.05], [0.16, -0.05], [0.10, -0.20], [-0.02, -0.33], [-0.26, -0.44],
  [-0.14, -0.30], [-0.06, -0.16], [-0.06, -0.05], [-0.16, -0.03], [-0.40, -0.10], [-0.58, -0.14], [-0.34, 0.01], [-0.56, 0.17],
  [-0.38, 0.09], [-0.16, 0.05], [-0.06, 0.06], [-0.08, 0.16], [-0.14, 0.27], [-0.22, 0.38], [-0.02, 0.26], [0.08, 0.14],
  [0.14, 0.06], [0.30, 0.045]];
const WING = new Set([4, 5, 6, 7, 8, 18, 19, 20, 21, 22]);
const LEVEL = SWALLOW.map(([x, y], i) => (WING.has(i) ? [x + 0.03 * Math.abs(y) / 0.4, y * 1.16] : [x, y]));   // the other flap: wings lifted wider, still crescents
const FEATHERS = [   // lines along the feathers: carved in the woodblock, traced on the screen
  [[0.08, -0.08], [-0.04, -0.24], [-0.20, -0.38]], [[0.02, -0.07], [-0.08, -0.20], [-0.14, -0.29]],
  [[0.06, 0.08], [-0.04, 0.20], [-0.16, 0.33]], [[-0.18, -0.01], [-0.36, -0.07], [-0.50, -0.12]],
  [[-0.18, 0.04], [-0.34, 0.10], [-0.48, 0.15]], [[0.30, -0.01], [0.20, 0.01]],
];

let G = null;

export async function setup(ctx, tokens, lib) {
  const { W, H, PORTRAIT: P, SAFE, TYPE } = lib;
  const g = {};
  g.S = P ? 760 : 620; g.cx = W / 2; g.cy = P ? 720 : 390;
  const at = ([x, y]) => [g.cx + x * g.S, g.cy + y * g.S];
  g.poly = SWALLOW.map(at); g.level = LEVEL.map(at); g.feathers = FEATHERS.map((f) => f.map(at));
  // the brush strokes: a path and a width along it (heavy where the brush is pressed, a dry taper at the end)
  const st = (pts, w0, w1, seed) => Object.assign(prep(pts.map(at), { step: 3, wobble: 1.2, seed }), { w0: w0 * g.S, w1: w1 * g.S });
  g.strokes = [
    Object.assign(st([[0.43, 0.0], [0.33, -0.01], [0.18, 0.005], [0.0, 0.01], [-0.20, -0.02], [-0.40, -0.09], [-0.57, -0.14]], 0.085, 0.01, 3), { t0: T.body[0], dur: T.body[1] }),
    Object.assign(st([[0.13, -0.05], [0.07, -0.17], [-0.03, -0.29], [-0.14, -0.37], [-0.25, -0.43]], 0.08, 0.006, 4), { t0: T.wingUp[0], dur: T.wingUp[1] }),
    Object.assign(st([[0.11, 0.06], [0.02, 0.17], [-0.10, 0.28], [-0.21, 0.37]], 0.065, 0.006, 5), { t0: T.wingDn[0], dur: T.wingDn[1] }),
    Object.assign(st([[-0.18, 0.04], [-0.36, 0.10], [-0.55, 0.165]], 0.032, 0.005, 6), { t0: T.tail[0], dur: T.tail[1] }),
  ];
  g.rest0 = at([0.52, -0.22]);
  // the pixel sprite: the swallow rasterised on a grid, two frames (wings swept, wings level)
  g.cell = P ? 24 : 20;
  g.sprites = [g.poly, g.level].map((poly) => raster(poly, g.cell, W, H));
  g.spriteLift = P ? -2 : -1;   // cells the sprite rises once it is a sprite
  g.grain = woodGrain(lib, W, H);
  // text: typed in pixels (drawn crisp on a full-size layer, then the layer is quantised to the pixel grid)
  const A = SAFE.title;
  lib.setFont(ctx, tokens, "zh", 10);
  const ts = lib.fitText(ctx, lib.TITLE_ZH, A.w * 0.9, (s) => lib.setFont(ctx, tokens, "zh", s), { min: 84, max: TYPE.title });
  const ty = P ? 1320 : 790;
  const mk = (role, str, size, y, t0, per, total) => {
    lib.setFont(ctx, tokens, role, size);
    const lay = lib.layoutText(ctx, str, { x: W / 2, y, align: "center", tracking: lib.tracking(tokens, role, size) });
    const n = lay.glyphs.length;
    return { role, size, y, lay, t0, per: total ? total / n : per };
  };
  g.lines = [
    mk("zh", lib.TITLE_ZH, ts, ty, T.title[0], T.title[1]),
    mk("display", lib.TITLE_EN, TYPE.label, ty + (P ? 92 : 72), T.en[0], 0, T.en[1]),
    mk("zh", lib.CAPTION_ZH, TYPE.caption, A.y1 - TYPE.caption * 0.6, T.caption[0], T.caption[1]),
  ];
  G = g;
}

function raster(poly, c, W, H) {
  const inside = (x, y) => {
    let k = false;
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [xi, yi] = poly[i], [xj, yj] = poly[j];
      if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) k = !k;
    }
    return k;
  };
  const cols = Math.ceil(W / c), rows = Math.ceil(H / c), on = new Set();
  for (let r = 0; r < rows; r++) for (let q = 0; q < cols; q++) if (inside((q + 0.5) * c, (r + 0.5) * c)) on.add(r * cols + q);
  const cells = [];
  for (const k of on) {
    const r = Math.floor(k / cols), q = k % cols;
    const edge = [[1, 0], [-1, 0], [0, 1], [0, -1]].some(([dq, dr]) => !on.has((r + dr) * cols + q + dq));
    cells.push([q, r, edge]);
  }
  return { cols, cells };
}

function woodGrain(lib, W, H) {
  const c = document.createElement("canvas"); c.width = W; c.height = H;
  const x = c.getContext("2d"), r = lib.rng(41);
  x.strokeStyle = "rgba(0,0,0,1)"; x.lineCap = "round";
  for (let i = 0; i < 160; i++) {   // the block's grain, printed as fine pale streaks through the black
    const y = r() * H, a = 3 + r() * 8, f = 0.002 + r() * 0.004, ph = r() * 6;
    x.lineWidth = 0.8 + r() * 1.6; x.globalAlpha = 0.25 + r() * 0.35;
    x.beginPath();
    for (let px = 0; px <= W; px += 24) x.lineTo(px, y + Math.sin(px * f + ph) * a + Math.sin(px * f * 3.7) * a * 0.3);
    x.stroke();
  }
  return c;
}

const sg = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const polyPath = (x, pts, close = true) => { x.beginPath(); pts.forEach(([px, py], i) => (i ? x.lineTo(px, py) : x.moveTo(px, py))); if (close) x.closePath(); };

// ── the four eras, each a full-frame painter ──────────────────────────────────────────────────────────────────────
function paintBrush(x, t, tokens, lib, inkT) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  x.fillStyle = C("paper"); x.fillRect(0, 0, W, H);
  lib.paper(x, { tone: C("paper"), amount: 1, blotch: 0.05, fiber: 0.9, seed: 9 });
  if (inkT <= 0) return;
  const wet = lib.layer("em:wet");
  for (const s of G.strokes) brushStroke(wet, s, inkT, C("ink"), lib);
  x.save(); x.filter = "blur(3px)"; x.globalAlpha = 0.35; x.drawImage(wet.canvas, 0, 0, W, H); x.restore();   // the wet halo
  x.drawImage(wet.canvas, 0, 0, W, H);
}

/** a brush stroke as bristles: each hair a fine line across the width; toward the end the dry hairs drop out */
function brushStroke(x, s, t, ink, lib) {
  const u = drawn(s, t);
  if (u <= 0) return;
  const P = s.pts, n = Math.floor(u * (P.length - 1)), N = 11;
  x.fillStyle = ink;
  for (let i = 0; i <= n; i += 1) {
    const f = s.cum[i] / s.len, w = (s.w0 + (s.w1 - s.w0) * Math.pow(f, 1.4) + s.w0 * 0.25 * Math.sin(Math.PI * Math.min(1, f * 4))) * (0.5 + 0.5 * Math.sqrt(Math.min(1, f / 0.07)));   // the tip lands, then the brush presses
    const a = P[Math.max(0, i - 1)], b = P[Math.min(P.length - 1, i + 1)], dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
    const nx = -dy / l, ny = dx / l, dry = Math.max(0, f - 0.45) * 1.6;
    for (let j = 0; j < N; j++) {
      if (lib.hash(j, 17, s.t0 * 10) < dry * (0.5 + 0.5 * Math.abs(j / (N - 1) - 0.5) * 2)) continue;
      const o = (j / (N - 1) - 0.5) * w;
      x.globalAlpha = 0.82 - dry * 0.3;
      x.beginPath(); x.arc(P[i][0] + nx * o, P[i][1] + ny * o, Math.max(1.2, w / N * 0.9), 0, 7); x.fill();
    }
  }
  x.globalAlpha = 1;
}

function paintPrint(x, t, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  x.fillStyle = C("cream"); x.fillRect(0, 0, W, H);
  lib.paper(x, { tone: C("cream"), amount: 1, blotch: 0.08, fiber: 0.4, seed: 12 });
  // the impression: the block's black, its grain, the carved feathers
  const im = lib.layer("em:print");
  im.fillStyle = C("ink"); polyPath(im, G.poly); im.fill();
  im.globalCompositeOperation = "destination-out";
  im.globalAlpha = 0.5; im.drawImage(G.grain, 0, 0, W, H); im.globalAlpha = 1;
  im.lineCap = "round"; im.strokeStyle = "#000"; im.fillStyle = "#000";
  G.feathers.forEach((f, k) => { im.lineWidth = 5 - (k % 2); polyPath(im, f, false); im.stroke(); });
  const e = G.poly[1]; im.beginPath(); im.arc(e[0] - 6, e[1] + 14, 6, 0, 7); im.fill();   // the eye, carved out
  im.globalCompositeOperation = "source-over";
  x.save(); x.filter = "blur(0.6px)"; x.globalAlpha = 0.94; x.drawImage(im.canvas, 0, 0, W, H); x.restore();
  // the seal, stamped once the print is pulled
  const s = sg(t, T.seal - 0.08, T.seal);
  if (s > 0) {
    const sx = G.cx + G.S * 0.36, sy = G.cy + G.S * 0.30, z = 1 + (1 - s) * 0.5, a = Math.min(1, s * 2);
    x.save(); x.translate(sx, sy); x.scale(z, z); x.globalAlpha = a * 0.9; x.fillStyle = C("seal");
    x.fillRect(-34, -34, 68, 68);
    x.fillStyle = C("cream"); x.fillRect(-24, -24, 8, 48); x.fillRect(16, -24, 8, 48);   // a seal mark, not a word
    x.beginPath(); x.arc(0, 0, 10, 0, 7); x.fill(); x.fillRect(-16, -4, 32, 8);
    x.restore();
  }
}

function paintScreen(x, t, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  x.fillStyle = C("glass"); x.fillRect(0, 0, W, H);
  const g = x.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.6);
  g.addColorStop(0, lib.rgba(C("phosphor"), 0.10)); g.addColorStop(1, lib.rgba(C("phosphor"), 0));
  x.fillStyle = g; x.fillRect(0, 0, W, H);
  const jolt = t >= T.jolt ? Math.exp(-(t - T.jolt) / 0.05) : 0;
  const ln = lib.layer("em:vector");
  ln.strokeStyle = C("phosphor"); ln.lineJoin = "round"; ln.lineCap = "round"; ln.lineWidth = 4;
  ln.save(); ln.translate(jolt * 26, 0);
  polyPath(ln, G.poly); ln.stroke();
  ln.lineWidth = 3; G.feathers.forEach((f) => { polyPath(ln, f, false); ln.stroke(); });
  ln.restore();
  const flick = 0.92 + 0.08 * Math.sin(t * 60 * Math.PI);
  x.save(); x.globalCompositeOperation = "lighter";
  x.filter = "blur(10px)"; x.globalAlpha = 0.8 * flick; x.drawImage(ln.canvas, 0, 0, W, H);
  x.filter = "blur(2px)"; x.globalAlpha = 0.9; x.drawImage(ln.canvas, 0, 0, W, H);
  x.filter = "none"; x.globalAlpha = flick; x.drawImage(ln.canvas, 0, 0, W, H);
  x.restore();
  lib.scanlines(x, t, { spacing: 4, alpha: 0.22, roll: 0, flicker: 0 });
  bezel(x, W, H);
}

function bezel(x, W, H) {   // the tube's dark edge
  const g = x.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.42, W / 2, H / 2, Math.hypot(W, H) * 0.56);
  g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, "rgba(0,0,0,0.85)");
  x.fillStyle = g; x.fillRect(0, 0, W, H);
}

function paintPixel(x, t, tokens, lib, withText) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  const c = G.cell;
  x.fillStyle = C("night"); x.fillRect(0, 0, W, H);
  x.fillStyle = lib.rgba(C("grid"), 0.5);   // the grid's corners
  for (let yy = c; yy < H; yy += c * 2) for (let xx = c; xx < W; xx += c * 2) x.fillRect(xx - 1, yy - 1, 3, 3);
  // the sprite: two frames, stepped; it rises a cell or two once it is a sprite
  const sp = G.sprites[Math.floor(t * T.flap) % 2], lift = Math.round(G.spriteLift * mj(sg(t, T.pixel[1], T.pixel[1] + 0.3)));
  for (const [q, r, edge] of sp.cells) {
    x.fillStyle = edge ? C("outline") : C("white");
    x.fillRect(q * c, (r + lift) * c, c, c);
  }
  const eye = G.poly[1];
  x.fillStyle = C("night"); x.fillRect(Math.floor((eye[0] - 8) / c) * c, (Math.floor((eye[1] + 12) / c) + lift) * c, c, c);
  if (withText) typed(x, t, tokens, lib);
}

/** the words, typed one glyph at a time, then snapped to a 3 px grid so they are made of pixels too */
function typed(x, t, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  const tl = lib.layer("em:text");
  let any = false;
  G.lines.forEach((ln, li) => {
    if (t < ln.t0) return;
    lib.setFont(tl, tokens, ln.role, ln.size);
    tl.fillStyle = li === 1 ? C("outline") : C("white");
    lib.drawGlyphs(tl, ln.lay, (g, i) => (t >= ln.t0 + i * ln.per ? {} : null));
    any = true;
  });
  if (!any) return;
  const k = 3, sw = Math.ceil(W / k), sh = Math.ceil(H / k);
  const sm = lib.layer("em:textsmall", sw, sh);
  sm.imageSmoothingEnabled = true; sm.drawImage(tl.canvas, 0, 0, sw, sh);
  x.save(); x.imageSmoothingEnabled = false;
  x.globalAlpha = 0.9; x.filter = "brightness(0)"; x.drawImage(sm.canvas, k, k, sw * k, sh * k); x.filter = "none";   // a hard drop shadow
  x.globalAlpha = 1; x.drawImage(sm.canvas, 0, 0, sw * k, sh * k);
  x.restore();
}

// ── the relay ────────────────────────────────────────────────────────────────────────────────────────────────────
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  const B = lib.layer("em:B");
  if (t < T.roller[0]) {
    paintBrush(ctx, t, tokens, lib, t);
  } else if (t < T.roller[1]) {                       // a roller pulls the print across the painting
    const u = lib.ease.inOutCubic(sg(t, ...T.roller)), xr = -80 + (W + 160) * u;
    paintBrush(ctx, t, tokens, lib, 9);
    paintPrint(B, t, tokens, lib);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, Math.max(0, xr), H); ctx.clip(); ctx.drawImage(B.canvas, 0, 0, W, H); ctx.restore();
    roller(ctx, xr, H);
  } else if (t < T.beam[0]) {
    paintPrint(ctx, t, tokens, lib);
  } else if (t < T.beam[1]) {                         // the beam scans the screen down over the print
    const yb = H * sg(t, ...T.beam);
    paintPrint(ctx, t, tokens, lib);
    paintScreen(B, t, tokens, lib);
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, yb); ctx.clip(); ctx.drawImage(B.canvas, 0, 0, W, H); ctx.restore();
    const gb = ctx.createLinearGradient(0, yb - 60, 0, yb + 6);
    gb.addColorStop(0, lib.rgba(C("phosphor"), 0)); gb.addColorStop(0.85, lib.rgba(C("phosphor"), 0.55)); gb.addColorStop(1, lib.rgba("#FFFFFF", 0.9));
    ctx.fillStyle = gb; ctx.fillRect(0, yb - 60, W, 66);
  } else if (t < T.pixel[0]) {
    paintScreen(ctx, t, tokens, lib);
  } else if (t < T.pixel[1]) {                        // the screen coarsens into blocks, then the blocks become the sprite
    const A = lib.layer("em:A");
    const u = sg(t, ...T.pixel), b = Math.max(1, Math.round(1 + (G.cell - 1) * lib.ease.inCubic(Math.min(1, u * 1.25))));
    paintScreen(A, t, tokens, lib);
    const sw = Math.ceil(W / b), sh = Math.ceil(H / b);
    const sm = lib.layer("em:mosaic", sw, sh);
    sm.imageSmoothingEnabled = true; sm.drawImage(A.canvas, 0, 0, sw, sh);
    ctx.save(); ctx.imageSmoothingEnabled = false; ctx.drawImage(sm.canvas, 0, 0, sw * b, sh * b); ctx.restore();
    const swap = sg(u, 0.78, 1);
    if (swap > 0) { paintPixel(B, t, tokens, lib, false); ctx.globalAlpha = swap; ctx.drawImage(B.canvas, 0, 0, W, H); ctx.globalAlpha = 1; }
  } else if (t < T.bloom[0]) {
    paintPixel(ctx, t, tokens, lib, true);
    if (t >= T.drop[0]) drop(ctx, t, lib);
  } else {                                            // a drop of water blooms out into rice paper
    paintPixel(ctx, t, tokens, lib, true);
    const R = Math.hypot(W, H) * 0.56 * lib.ease.outCubic(sg(t, ...T.bloom));
    const rim = (a, rr) => rr * (1 + 0.07 * lib.noise1(Math.cos(a) * 3 + 7, 3) + 0.03 * lib.noise1(a * 9, 5));
    const ring = (x, rr) => {
      x.beginPath();
      for (let i = 0; i <= 160; i++) {
        const a = i / 160 * Math.PI * 2, r = rim(a, rr), px = W / 2 + Math.cos(a) * r, py = H / 2 + Math.sin(a) * r;
        if (i) x.lineTo(px, py); else x.moveTo(px, py);
      }
      x.closePath();
    };
    paintBrush(B, t, tokens, lib, 0);
    const m = lib.layer("em:bloom");
    m.fillStyle = "#fff"; ring(m, R); m.fill();
    m.globalCompositeOperation = "source-in"; m.drawImage(B.canvas, 0, 0, W, H); m.globalCompositeOperation = "source-over";
    ctx.drawImage(m.canvas, 0, 0, W, H);
    if (R > 0 && R < Math.hypot(W, H) * 0.55) {      // the wet edge of the bloom
      ctx.save(); ctx.strokeStyle = lib.rgba(C("wash"), 0.45); ctx.lineWidth = 16; ctx.filter = "blur(6px)";
      ring(ctx, Math.max(1, R - 8)); ctx.stroke(); ctx.restore();
    }
  }
  const b = brushAt(t);
  if (b) drawBrush(ctx, b.x, b.y, b.lift, tokens, lib);
}

function brushAt(t) {
  if (t < T.roller[0] + 0.5) {
    const h = pen(G.strokes, t, { from: G.rest0, to: [G.rest0[0] + 260, -260] }, { lead: 0.1, tail: 0.5 });
    return { x: h.x, y: h.y, lift: h.down ? 0 : Math.max(0.2, h.lift) };
  }
  if (t >= T.brushBack[0]) {
    const u = mj(sg(t, ...T.brushBack));
    return { x: G.rest0[0] + 260 * (1 - u), y: -260 + (G.rest0[1] + 260) * u, lift: 0.2 + 0.8 * (1 - u) };
  }
  return null;
}

/** a calligraphy brush, nearly upright: bamboo shaft, the hair wet with ink at the tip */
function drawBrush(ctx, x, y, lift, tokens, lib) {
  ctx.save();
  ctx.translate(x, y - 10 * lift); ctx.rotate(-0.42);
  ctx.shadowColor = "rgba(40,30,20,0.3)"; ctx.shadowBlur = 12 + 20 * lift; ctx.shadowOffsetX = 12 + 30 * lift; ctx.shadowOffsetY = 8 + 20 * lift;
  const sh = ctx.createLinearGradient(-10, 0, 10, 0);
  sh.addColorStop(0, "#9C7A45"); sh.addColorStop(0.5, "#D8B676"); sh.addColorStop(1, "#8A6A3A");
  ctx.fillStyle = sh; ctx.fillRect(-9, -330, 18, 270);
  ctx.shadowColor = "transparent";
  ctx.fillStyle = "#6E5530"; ctx.fillRect(-9, -250, 18, 5); ctx.fillRect(-9, -150, 18, 5);   // the bamboo's nodes
  ctx.fillStyle = "#2E2A24"; ctx.fillRect(-11, -70, 22, 16);                                    // the ferrule
  ctx.fillStyle = lib.color(tokens, "ink");
  ctx.beginPath(); ctx.moveTo(-11, -56); ctx.bezierCurveTo(-13, -26, -5, -8, 0, 0); ctx.bezierCurveTo(5, -8, 13, -26, 11, -56); ctx.closePath(); ctx.fill();
  ctx.restore();
}

function roller(ctx, x, H) {   // a printer's roller seen from above, rolling left to right
  ctx.save();
  ctx.shadowColor = "rgba(0,0,0,0.35)"; ctx.shadowBlur = 24; ctx.shadowOffsetX = 18;
  const g = ctx.createLinearGradient(x - 40, 0, x + 40, 0);
  g.addColorStop(0, "#1D1B19"); g.addColorStop(0.45, "#4A4642"); g.addColorStop(0.55, "#5A5550"); g.addColorStop(1, "#151311");
  ctx.fillStyle = g; ctx.fillRect(x - 40, -10, 80, H + 20);
  ctx.shadowColor = "transparent";
  ctx.fillStyle = "rgba(255,255,255,0.12)"; ctx.fillRect(x - 6, -10, 8, H + 20);
  ctx.restore();
}

function drop(ctx, t, lib) {   // a drop of water falling onto the screen
  const { W, H } = lib;
  const u = sg(t, ...T.drop), y = -40 + (H / 2 + 40) * u * u;
  if (u >= 1) return;
  ctx.save(); ctx.fillStyle = "rgba(210,230,255,0.75)"; ctx.strokeStyle = "rgba(255,255,255,0.8)"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.moveTo(W / 2, y - 34); ctx.bezierCurveTo(W / 2 + 16, y - 6, W / 2 + 14, y + 12, W / 2, y + 14);
  ctx.bezierCurveTo(W / 2 - 14, y + 12, W / 2 - 16, y - 6, W / 2, y - 34); ctx.fill(); ctx.stroke(); ctx.restore();
}
