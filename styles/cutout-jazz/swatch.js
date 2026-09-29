// cutout-jazz swatch — mid-century cut-paper title grammar (150 BPM: 0.8 / 2.0 / 4.0 s fall on beats).
//   0.0–0.8  black ground: on the brass stab at 0.0 four white paper bars cut in, a second group on 0.4 (only the
//            bass under it: the breath before the title); on 0.8 the picture cuts to cream paper
//   0.8–2.6  title letters are paper pieces slapped onto a black beam, one per sixteenth; the Chinese line arrives
//            on an ink strip wiped in from the left
//   2.0–4.0  the motif assembles into ONE cut-paper symbol, a camera: film bars (outline) feed a body of three
//            blocks (storyboard) with the vermilion lens (draft). Every beat after that: the film advances (2.8, 3.6),
//            the lens notch turns on each beat, a black bar wipes the ground to mustard (3.2), the whole symbol steps
//            right on 3.6 and 3.8
//   4.0–5.0  the frame is cut into 6 equal strips with scissor edges that slide off alternately; the lens stays (match)
// Paper pieces step at 15 fps (lib.step(t, 15)); texture and grain stay at full rate.

const BPM = 150, BEAT = 60 / BPM, E8 = BEAT / 2, E16 = BEAT / 4;
// foley (render.sh places events.json; generated from this list so the landing times share the constants above)
const px = (x) => Math.round((x / 960 - 1) * 100) / 100;
export const FOLEY = [
  { t: 0.1, sfx: "pop", gain_db: -4, pan: px(400) }, { t: 0.5, sfx: "pop", gain_db: -4, pan: px(1400) },            // white bars land
  ...Array.from({ length: 6 }, (_, i) => ({ t: 0.8 + 2 * i * E16, sfx: "pop", gain_db: -12, pan: px(260 + i * 150) })),  // every other letter slap
  { t: 1.9, sfx: "whoosh", gain_db: -14, pan: px(400) },                                                             // ink strip wipes in
  { t: 2.2, sfx: "click", gain_db: -8, pan: px(550) }, { t: 2.4, sfx: "pop", gain_db: -8, pan: px(940) }, { t: 2.6, sfx: "pop", gain_db: -6, pan: px(1318) },
  { t: 2.8, sfx: "tick", gain_db: -10, pan: px(550) }, { t: 3.2, sfx: "whoosh", gain_db: -10, pan: 0 },               // film advances; bar wipe
  { t: 3.6, sfx: "click", gain_db: -8, pan: px(1000) }, { t: 3.8, sfx: "click", gain_db: -10, pan: px(1040) },       // the symbol steps
  { t: 4.0, sfx: "shutter", gain_db: -4, pan: 0 },                                                                     // scissors: the strips
  { t: 4.4, sfx: "pop", gain_db: -6, pan: px(400) }, { t: 4.4 + E16, sfx: "pop", gain_db: -8, pan: px(400) },
];   // 150 BPM: 0.8 / 2.0 / 4.0 s all fall on beats
const CUT = new Map();          // cut polygons in local space, keyed by id + size (pure data, identical per worker)
let L = null;

export const fonts = ["Futura", "PingFang SC"];

export async function setup(ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const disp = (x, s) => lib.setFont(x, tokens, "display", s, { weight: 800, stretch: "condensed" });
  const text = lib.TITLE_EN.toUpperCase();
  const size = lib.fitText(ctx, text, 1330, (s) => disp(ctx, s), { min: 110, max: 158, tracking: 0.02 });
  disp(ctx, size);
  const x0 = 192, base = 296;
  const lay = lib.layoutText(ctx, text, { x: x0, y: base, tracking: size * 0.02 });
  // every letter becomes its own re-cut paper piece: ground-colour gap stroke + ink fill, edges roughened ONCE here
  const glyphs = [];
  let k = 0;
  for (const g of lay.glyphs) {
    if (g.ch === " ") continue;
    const pad = 24, w = Math.ceil(g.w + pad * 2), h = Math.ceil(size * 1.15);
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const gx = c.getContext("2d");
    const paint = (x) => {
      disp(x, size); x.textAlign = "center"; x.textBaseline = "alphabetic";
      x.fillStyle = C("fg"); x.fillText(g.ch, w / 2, h - pad - size * 0.12);
    };
    lib.roughen(gx, paint, { amount: 3.2, freq: 0.085, seed: 17 + k * 7 });
    glyphs.push({ ch: g.ch, k, cx: g.cx, img: c, w, h, oy: h - pad - size * 0.12 });
    k++;
  }
  disp(ctx, size);
  const titleX1 = lay.x1;
  // Chinese line on an ink strip
  lib.setFont(ctx, tokens, "zh", 62, { weight: 600 });
  const zhW = ctx.measureText(lib.TITLE_ZH).width + 62 * 0.06 * 8;
  L = { size, x0, base, glyphs, titleX1, zhW };
}

// ───────── cut-paper helpers ─────────
function cutRect(lib, id, w, h, amp = 1.7) {
  const key = `r${id}:${w}:${h}`; if (CUT.has(key)) return CUT.get(key);
  const cs = [[0, 0], [w, 0], [w, h], [0, h]], pts = []; let k = 0;
  for (let e = 0; e < 4; e++) {
    const [x0, y0] = cs[e], [x1, y1] = cs[(e + 1) % 4], len = Math.hypot(x1 - x0, y1 - y0), n = Math.max(1, Math.round(len / 10));
    const nx = (y1 - y0) / len, ny = -(x1 - x0) / len;
    for (let s = 0; s < n; s++) {
      const u = s / n, notch = lib.hash(id, k, 9) < 0.025 ? -1.6 : 0;
      const d = s === 0 ? 0 : amp * lib.noise1(k * 0.33, id) + notch;
      pts.push([x0 + (x1 - x0) * u + nx * d, y0 + (y1 - y0) * u + ny * d]); k++;
    }
  }
  CUT.set(key, pts); return pts;
}
function cutCircle(lib, id, r, amp = 1.9) {
  const key = `c${id}:${r}`; if (CUT.has(key)) return CUT.get(key);
  const n = Math.round(lib.TAU * r / 9), pts = [];
  for (let i = 0; i < n; i++) { const a = i / n * lib.TAU, rr = r + amp * lib.noise1(i * 0.3, id); pts.push([Math.cos(a) * rr, Math.sin(a) * rr]); }
  CUT.set(key, pts); return pts;
}
function cutPoly(lib, id, base, amp = 1.4) {
  const key = `p${id}`; if (CUT.has(key)) return CUT.get(key);
  const pts = []; let k = 0;
  for (let e = 0; e < base.length; e++) {
    const [x0, y0] = base[e], [x1, y1] = base[(e + 1) % base.length], len = Math.hypot(x1 - x0, y1 - y0), n = Math.max(1, Math.round(len / 9));
    const nx = (y1 - y0) / len, ny = -(x1 - x0) / len;
    for (let s = 0; s < n; s++) { const u = s / n, d = s === 0 ? 0 : amp * lib.noise1(k * 0.4, id); pts.push([x0 + (x1 - x0) * u + nx * d, y0 + (y1 - y0) * u + ny * d]); k++; }
  }
  CUT.set(key, pts); return pts;
}
/** A paper piece: shadow + ground-colour gap first, then the flat ink on top. lift 0..1 = how far off the page. */
function piece(ctx, pts, x, y, fill, gap, { rot = 0, s = 1, lift = 0 } = {}) {
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.scale(s, s);
  ctx.beginPath(); pts.forEach(([px, py], i) => (i ? ctx.lineTo(px, py) : ctx.moveTo(px, py))); ctx.closePath();
  ctx.shadowColor = "rgba(24,16,8,0.30)"; ctx.shadowOffsetX = 3 + 7 * lift; ctx.shadowOffsetY = 4 + 9 * lift; ctx.shadowBlur = 4 + 10 * lift;
  ctx.fillStyle = gap; ctx.strokeStyle = gap; ctx.lineWidth = 4; ctx.lineJoin = "round"; ctx.fill(); ctx.stroke();
  ctx.shadowColor = "transparent"; ctx.fillStyle = fill; ctx.fill();
  ctx.restore();
}
/** Slide-in on twos: 0 before t0, eased 0→1 across `frames` output frames, stepped at 15 fps, stops dead. */
function slide(lib, t, tLand, frames, e) {
  const ts = lib.step(t, 15), t0 = tLand - frames / 30;
  if (ts < t0) return -1;
  return e(lib.seg(ts, t0, tLand));
}

// ───────── scene ─────────
const MOT = { film: [[300, 604], [300, 670], [190, 736]], filmX: 700, body: { x: 712, y: 572, bw: 150, bh: 222, gap: 14 }, lens: { x: 1318, y: 683, r: 116 } };
const E_ = (lib, tokens) => lib.easeOf(tokens.ease.enter);

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  if (t < 0.8) opening(ctx, t, tokens, lib);
  else if (t < 4.0) main(ctx, t, tokens, lib);
  else {
    const A = lib.offscreen("cj_main", (x) => main(x, 3.99, tokens, lib));
    end(ctx, t, tokens, lib);
    // six equal strips with scissor-cut long edges; they leave alternately left / right on twos, 2 frames apart
    const n = 6, sh = H / n, ts = lib.step(t, 15), ein = lib.easeOf(tokens.ease.exit);
    for (let i = 0; i < n; i++) {
      const t0 = 4.0 + i * 2 / 30, u = ein(lib.seg(ts, t0, t0 + 0.34));
      if (u >= 1) continue;
      const dx = (i % 2 ? 1 : -1) * u * (W + 80), poly = stripPoly(lib, i, sh);
      ctx.save(); ctx.translate(dx, i * sh);
      ctx.beginPath(); poly.forEach(([px, py], j) => (j ? ctx.lineTo(px, py) : ctx.moveTo(px, py))); ctx.closePath();
      ctx.shadowColor = "rgba(0,0,0,0.45)"; ctx.shadowOffsetX = 4; ctx.shadowOffsetY = 7; ctx.shadowBlur = 10; ctx.fillStyle = "#000"; ctx.fill();
      ctx.shadowColor = "transparent"; ctx.clip(); ctx.drawImage(A, 0, -i * sh);
      ctx.restore();
    }
  }
  ctx.save(); ctx.globalCompositeOperation = "multiply";
  lib.paper(ctx, { tone: "#FFFBF2", amount: 1, blotch: 0.07, tooth: 0.03, fiber: 0.9, seed: 21 });
  ctx.restore();
  lib.grain(ctx, t, { amount: 0.05, fps: 12, seed: 5 });
}
function stripPoly(lib, i, sh) {                      // a strip cut with scissors: both long edges wander a little
  const key = `strip${i}`; if (CUT.has(key)) return CUT.get(key);
  const W = lib.W, pts = [], n = Math.ceil(W / 12);
  for (let k = 0; k <= n; k++) pts.push([k * W / n, (i === 0 ? -20 : 0) + 2.4 * lib.noise1(k * 0.35, 900 + i)]);
  for (let k = n; k >= 0; k--) pts.push([k * W / n, sh + (i === 5 ? 20 : 0) + 2.4 * lib.noise1(k * 0.35, 901 + i)]);
  CUT.set(key, pts); return pts;
}

function opening(ctx, t, tokens, lib) {               // black ground; white bars cut in on the 0.0 and 0.4 hits
  const C = (k) => lib.color(tokens, k), { W, H } = lib, ts = lib.step(t, 15);
  ctx.fillStyle = C("fg"); ctx.fillRect(0, 0, W, H);
  const white = "#F4EEDF";
  const group = (bars, t0, id) => bars.forEach(([x, y, w, h], j) => {
    const u = slide(lib, t, t0 + j * 2 / 30, 4, E_(lib, tokens)); if (u < 0) return;
    piece(ctx, cutRect(lib, id + j, w, h), x, y - (1 - u) * 160, white, C("fg"));
  });
  group([[150, 60, 120, 960], [330, 160, 90, 860], [470, 40, 150, 900], [680, 220, 70, 700]], 0.1, 300);     // first hit
  group([[1120, 120, 70, 840], [1250, 40, 150, 960], [1460, 180, 100, 800], [1620, 90, 120, 900]], 0.5, 400); // second hit
}

function main(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), E = E_(lib, tokens), { W, H } = lib;
  // ground: cream, then a black bar wipes it to mustard at 3.2 s (on twos)
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  const wu = lib.seg(lib.step(t, 15), 3.07, 3.2), mustard = C("extra.0");
  if (wu > 0) {
    const bx = lib.lerp(-260, W, lib.ease.inOutCubic(wu));
    ctx.fillStyle = mustard; ctx.fillRect(0, 0, bx, H);
    if (wu < 1) piece(ctx, cutRect(lib, 60, 260, H + 40), bx, -20, C("fg"), C("fg"));
  }
  const ground = wu >= 1 ? mustard : C("bg");
  // the beam and the three bars of the set (stop dead on sixteenths)
  const beamW = L.titleX1 - L.x0 + 48;
  let u = slide(lib, t, 0.9, 4, E);
  if (u >= 0) piece(ctx, cutRect(lib, 1, Math.round(beamW), 22), L.x0 - (1 - u) * (beamW + 240), L.base + 16, C("fg"), ground);
  [[1596, 28, 250], [1652, 44, 372], [1718, 22, 300]].forEach(([x, w, h], j) => {
    const v = slide(lib, t, 1.0 + j * E16, 6, E);
    if (v >= 0) piece(ctx, cutRect(lib, 2 + j * 50, w, h), x, 108 - (1 - v) * (h + 140), C("fg"), ground);
  });
  // title: one paper letter per sixteenth, slapped down (lifted & big two steps before, flat on the landing)
  const ts = lib.step(t, 15);
  for (const g of L.glyphs) {
    const tk = 0.8 + g.k * E16;
    if (ts < tk - 4 / 30) continue;
    const ph = ts >= tk ? 0 : ts >= tk - 2 / 30 ? 1 : 2;
    const s = [1, 1.08, 1.22][ph], dy = [0, -12, -34][ph], lift = [0, 0.5, 1][ph];
    const rot = lib.hashS(7, g.k) * 0.8 * Math.PI / 180, jy = lib.hashS(8, g.k) * 2;
    ctx.save(); ctx.translate(g.cx, L.base + jy + dy); ctx.rotate(rot); ctx.scale(s, s);
    ctx.shadowColor = "rgba(24,16,8,0.30)"; ctx.shadowOffsetX = 3 + 7 * lift; ctx.shadowOffsetY = 4 + 9 * lift; ctx.shadowBlur = 4 + 10 * lift;
    ctx.drawImage(g.img, -g.w / 2, -g.oy); ctx.restore();
  }
  // Chinese line on an ink strip, wiped in from the left on twos
  const zx = L.x0, zy = 364, zh = 96, zw = Math.round(L.zhW + 70);
  u = slide(lib, t, 1.9, 8, E);
  if (u >= 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, zx + u * (zw + 20), H); ctx.clip();
    piece(ctx, cutRect(lib, 3, zw, zh), zx, zy, C("fg"), ground);
    lib.setFont(ctx, tokens, "zh", 62, { weight: 600 }); ctx.fillStyle = "#F4EEDF";
    lib.drawText(ctx, lib.TITLE_ZH, zx + 34, zy + 72, { tracking: 62 * 0.06 });
    ctx.restore();
  }
  camera(ctx, t, tokens, lib, ground);
}

// the motif as one symbol: film bars → body blocks → vermilion lens
function symShift(t, lib, E) { return 40 * [3.6, 3.8].reduce((a, tb) => a + E(lib.seg(lib.step(t, 15), tb - 4 / 30, tb)), 0); }
function camera(ctx, t, tokens, lib, ground) {
  const C = (k) => lib.color(tokens, k), E = E_(lib, tokens), ink = C("fg");
  ctx.save(); ctx.translate(symShift(t, lib, E), 0);          // 3.6 / 3.8 s: the symbol steps right, stops dead
  const sub = (land, j) => slide(lib, t, land + j * 2 / 30, 6, E);
  // film (outline): three bars feeding the body from the left; they advance one step on 2.8 and 3.6 (on twos)
  const adv = [2.8, 3.6].reduce((a, tb) => a + E(lib.seg(lib.step(t, 15), tb - 4 / 30, tb)), 0);
  MOT.film.forEach(([w, y], j) => {
    const v = sub(2.2, j); if (v < 0) return;
    const shift = (j % 2 ? -1 : 1) * 26 * adv;                                    // the film steps along
    piece(ctx, cutRect(lib, 10 + j, w, 34), MOT.filmX - w + shift - (1 - v) * 420, y, ink, ground);
  });
  // body (storyboard): three blocks, fitted edge to edge
  const B = MOT.body;
  for (let j = 0; j < 3; j++) { const v = sub(2.4, j); if (v >= 0) piece(ctx, cutRect(lib, 20 + j, B.bw, B.bh), B.x + j * (B.bw + B.gap), B.y + (1 - v) * 360, ink, ground); }
  // lens (draft): the one vermilion circle, an ink ring and a cream notch that turns a quarter on every beat
  const lv = sub(2.6, 0);
  if (lv >= 0) {
    const lx = MOT.lens.x + (1 - lv) * 520, ly = MOT.lens.y;
    piece(ctx, cutCircle(lib, 30, MOT.lens.r), lx, ly, C("accent"), ground);
    piece(ctx, cutCircle(lib, 31, 54), lx, ly, ink, C("accent"));
    const beats = Math.max(0, Math.floor((lib.step(t, 15) - 2.6) / 0.4 + 1e-6));
    piece(ctx, cutPoly(lib, 32, [[-9, -50], [9, -50], [6, -18], [-6, -18]]), lx, ly, "#F4EEDF", ink, { rot: beats * Math.PI / 4 + Math.PI / 8 });
  }
  // labels, cut in with their part
  [[550, 2.2 + 4 / 30], [MOT.body.x + 1.5 * B.bw + B.gap, 2.4 + 4 / 30], [MOT.lens.x, 2.6]].forEach(([x, tl], k) => {
    if (lib.step(t, 15) < tl) return;
    ctx.save(); ctx.fillStyle = ink;
    lib.setFont(ctx, tokens, "body", 34, { weight: 500 }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), x, 872, { align: "center", tracking: 34 * 0.14 });
    lib.setFont(ctx, tokens, "zh", 52, { weight: 600 }); lib.drawText(ctx, lib.MOTIF[k].zh, x, 938, { align: "center", tracking: 52 * 0.2 });
    ctx.restore();
  });
  ctx.restore();
}

function end(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  ctx.fillStyle = C("fg"); ctx.fillRect(0, 0, W, H);
  const lx = MOT.lens.x + symShift(3.99, lib, E_(lib, tokens));
  piece(ctx, cutCircle(lib, 30, MOT.lens.r), lx, MOT.lens.y, C("accent"), C("fg"));      // same piece, same place
  piece(ctx, cutCircle(lib, 31, 54), lx, MOT.lens.y, C("fg"), C("accent"));
  const ts = lib.step(t, 15);
  const word = (str, tk, x, y, size, role, weight, stretch) => {
    if (ts < tk - 2 / 30) return;
    const s = ts >= tk ? 1 : 1.12;
    ctx.save(); ctx.translate(x, y); ctx.scale(s, s);
    lib.setFont(ctx, tokens, role, size, { weight, stretch }); ctx.fillStyle = C("bg");
    ctx.shadowColor = "rgba(0,0,0,0.5)"; ctx.shadowOffsetX = 3; ctx.shadowOffsetY = 4; ctx.shadowBlur = 4;
    lib.drawText(ctx, str, 0, 0, { tracking: size * 0.03 });
    ctx.restore();
  };
  word("CUTOUT", 4.4, 192, 640, 150, "display", 800, "condensed");
  word("JAZZ", 4.4 + E16, 192, 790, 150, "display", 800, "condensed");
  word("剪纸爵士片头", 4.4 + 2 * E16, 196, 880, 54, "zh", 600);
}
