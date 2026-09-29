// cutout-jazz swatch — mid-century cut-paper title grammar.
//   0.0–0.8  cream paper; a black beam slides in from the left and a black post drops, both stop dead (on twos)
//   0.8–2.6  title letters are paper pieces that slap onto the beam one per sixteenth (150 BPM); the Chinese
//            line arrives on an ochre strip wiped in from the left
//   2.0–4.0  motif: outline (3 bars) → storyboard (3 panels) → draft (the one vermilion circle), sliding in L→R
//   4.0–5.0  the frame is cut into strips that slide off alternately; the vermilion circle stays put (match)
// Paper pieces step at 15 fps (lib.step(t, 15)); texture and grain stay at full rate.

const BPM = 150, BEAT = 60 / BPM, E8 = BEAT / 2, E16 = BEAT / 4;   // 150 BPM: 0.8 / 2.0 / 4.0 s all fall on beats
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
      x.lineJoin = "round"; x.strokeStyle = C("bg"); x.lineWidth = 5; x.strokeText(g.ch, w / 2, h - pad - size * 0.12);
      x.fillStyle = C("fg"); x.fillText(g.ch, w / 2, h - pad - size * 0.12);
    };
    lib.roughen(gx, paint, { amount: 3.2, freq: 0.085, seed: 17 + k * 7 });
    glyphs.push({ ch: g.ch, k, cx: g.cx, img: c, w, h, oy: h - pad - size * 0.12 });
    k++;
  }
  disp(ctx, size);
  const titleX1 = lay.x1;
  // Chinese line on an ochre strip
  lib.setFont(ctx, tokens, "zh", 62, { weight: 600 });
  const zhW = ctx.measureText(lib.TITLE_ZH).width + 62 * 0.06 * 8;
  const slots = lib.slots(3, { area: lib.SAFE.title, y: 676, gap: 96 });
  L = { size, x0, base, glyphs, titleX1, zhW, slots };
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
export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  if (t < 4.0) main(ctx, t, tokens, lib);
  else {
    const A = lib.offscreen("cj_main", (x) => main(x, 3.99, tokens, lib));
    end(ctx, t, tokens, lib);
    // cut the finished frame into 6 strips; they leave alternately left/right, on twos, 2 frames apart
    const n = 6, sh = lib.H / n, ts = lib.step(t, 15), ein = lib.easeOf(tokens.ease.exit);
    for (let i = 0; i < n; i++) {
      const t0 = 4.0 + i * 2 / 30, u = ein(lib.seg(ts, t0, t0 + 0.34));
      if (u >= 1) continue;
      const dx = (i % 2 ? 1 : -1) * u * (lib.W + 60);
      ctx.save();
      ctx.shadowColor = "rgba(0,0,0,0.35)"; ctx.shadowOffsetX = 4; ctx.shadowOffsetY = 6; ctx.shadowBlur = 8;
      ctx.drawImage(A, 0, i * sh, lib.W, sh + 1, dx, i * sh, lib.W, sh + 1);
      ctx.restore();
    }
  }
  // texture over everything: paper tooth multiplied, light grain at 12 fps
  ctx.save(); ctx.globalCompositeOperation = "multiply";
  lib.paper(ctx, { tone: "#FFFBF2", amount: 1, blotch: 0.07, tooth: 0.03, fiber: 0.9, seed: 21 });
  ctx.restore();
  lib.grain(ctx, t, { amount: 0.05, fps: 12, seed: 5 });
}

function main(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const E = lib.easeOf(tokens.ease.enter);
  const { W, H } = lib;
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);

  // establish: the beam (credits sit on it) and a post on the right, stop dead
  const beamW = L.titleX1 - L.x0 + 48;
  let u = slide(lib, t, 0.40, 8, E);
  if (u >= 0) piece(ctx, cutRect(lib, 1, Math.round(beamW), 22), L.x0 - (1 - u) * (beamW + 240), L.base + 16, C("fg"), C("bg"));
  // three bars of the set drop in on eighth notes at the right edge (heights differ, like credits of unequal weight)
  [[1596, 28, 250], [1652, 44, 372], [1718, 22, 300]].forEach(([x, w, h], j) => {
    const v = slide(lib, t, 0.5 + j * E16, 8, E);
    if (v >= 0) piece(ctx, cutRect(lib, 2 + j * 50, w, h), x, 108 - (1 - v) * (h + 140), C("fg"), C("bg"));
  });

  // title: one paper letter per sixteenth, slapped down (lifted & big two steps before, flat on the landing)
  const ts = lib.step(t, 15);
  for (const g of L.glyphs) {
    const tk = 0.8 + g.k * E16;
    if (ts < tk - 4 / 30) continue;
    const ph = ts >= tk ? 0 : ts >= tk - 2 / 30 ? 1 : 2;
    const s = [1, 1.08, 1.22][ph], dy = [0, -12, -34][ph], lift = [0, 0.5, 1][ph];
    const rot = lib.hashS(7, g.k) * 0.8 * Math.PI / 180, jy = lib.hashS(8, g.k) * 2;
    ctx.save();
    ctx.translate(g.cx, L.base + jy + dy); ctx.rotate(rot); ctx.scale(s, s);
    ctx.shadowColor = "rgba(24,16,8,0.30)"; ctx.shadowOffsetX = 3 + 7 * lift; ctx.shadowOffsetY = 4 + 9 * lift; ctx.shadowBlur = 4 + 10 * lift;
    ctx.drawImage(g.img, -g.w / 2, -g.oy);
    ctx.restore();
  }

  // Chinese line on an ochre strip, wiped in from the left on twos
  const zx = L.x0, zy = 364, zh = 96, zw = Math.round(L.zhW + 70);
  u = slide(lib, t, 1.9, 8, E);
  if (u >= 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(0, 0, zx + u * (zw + 20), H); ctx.clip();
    piece(ctx, cutRect(lib, 3, zw, zh), zx, zy, C("extra.0"), C("bg"));
    lib.setFont(ctx, tokens, "zh", 62, { weight: 600 }); ctx.fillStyle = C("fg");
    lib.drawText(ctx, lib.TITLE_ZH, zx + 34, zy + 72, { tracking: 62 * 0.06 });
    ctx.restore();
  }

  // motif: outline → storyboard → draft, each slides in from the left and stops dead on an eighth note
  L.slots.forEach((sl, k) => motif(ctx, t, tokens, lib, sl, k));
}

function motif(ctx, t, tokens, lib, sl, k) {
  const C = (n) => lib.color(tokens, n);
  const E = lib.easeOf(tokens.ease.enter);
  const land = 2.2 + k * E8, cx = sl.x, cy = sl.y;
  const sub = (j) => slide(lib, t, land + j * 2 / 30, 8, E);
  const off = (u) => -(1 - u) * 360;
  if (k === 0) {                                   // outline: three bars, the last one short
    [300, 300, 188].forEach((w, j) => { const u = sub(j); if (u >= 0) piece(ctx, cutRect(lib, 10 + j, w, 30), cx - 150 + off(u), cy - 86 + j * 70, C("fg"), C("bg")); });
  } else if (k === 1) {                            // storyboard: three panels
    for (let j = 0; j < 3; j++) { const u = sub(j); if (u >= 0) piece(ctx, cutRect(lib, 20 + j, 90, 164), cx - 150 + j * 105 + off(u), cy - 86, C("fg"), C("bg")); }
  } else {                                         // draft: the one vermilion circle, a black play wedge cut on top
    const u = sub(0);
    if (u >= 0) piece(ctx, cutCircle(lib, 30, 104), cx + off(u), cy, C("accent"), C("bg"));
    const v = sub(1);
    if (v >= 0) piece(ctx, cutPoly(lib, 31, [[-30, -46], [52, 0], [-30, 46]]), cx + 8 + off(v), cy, C("fg"), C("accent"));
  }
  // labels arrive with the last piece of the group
  if (sub(k === 2 ? 1 : 2) >= 1) {
    ctx.save();
    lib.setFont(ctx, tokens, "body", 32, { weight: 500 }); ctx.fillStyle = C("fg");
    lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), cx, cy + 176, { align: "center", tracking: 32 * 0.14 });
    lib.setFont(ctx, tokens, "zh", 50, { weight: 600 });
    lib.drawText(ctx, lib.MOTIF[k].zh, cx, cy + 240, { align: "center", tracking: 50 * 0.2 });
    ctx.restore();
  }
}

function end(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const { W, H } = lib;
  ctx.fillStyle = C("fg"); ctx.fillRect(0, 0, W, H);
  const d = L.slots[2];
  piece(ctx, cutCircle(lib, 30, 104), d.x, d.y, C("accent"), C("fg"));             // same piece, same place: match
  piece(ctx, cutPoly(lib, 31, [[-30, -46], [52, 0], [-30, 46]]), d.x + 8, d.y, C("fg"), C("accent"));
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
