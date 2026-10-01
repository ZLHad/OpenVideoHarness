// scratched-type swatch — letters scratched into black film base by hand, not a distressed font.
// Every glyph (Latin and Chinese) gets a skeleton: the glyph is rasterised, thinned (Zhang–Suen) and traced into
// polylines once in setup. Each stroke is then scratched as 2–4 thin, uneven hairlines that wander along the
// skeleton, break, start with a pressure blot and throw off emulsion chips; the wander phase changes every 2 frames.
//   0.0–0.8  hook: on the taiko hit a scratch rips across the whole frame in 3 frames (with sparks), one dried-red
//            flash frame, a 2-frame macro at 0.4 s, then a punched leader hole flashes; gate weave, dust, scratches, grain
//   0.8–2.6  the title is carved stroke by stroke (≈ 8 frames per glyph), jittering, doubled, with a faint ghost
//   2.0–4.0  three separate film frames cut in, each slipping in the gate on its own; only a sliver of sprocket
//            holes shows at their edges; outline / storyboard / draft scratched into them (the draft is a red cue mark);
//            a 2–3 frame macro insert cuts in on every beat (2.0 / 2.4 / 2.8 / 3.2 / 3.6: glyph, perforations, gouge)
//   4.0–5.0  a red flash frame, 5 frames of double exposure, then the end card carved on black leader
// Red appears three times in total (the hook flash, the draft cue mark, the 4.0 s flash); ≤ 2 bright full-frame flashes
// per second (the perforation and gouge inserts are dark on purpose).

let L = null;
export const fonts = ["Helvetica Neue", "American Typewriter", "PingFang SC"];

// ───────── skeletons ─────────
function thin(img, w, h) {                       // Zhang–Suen thinning, in place (1 = ink)
  const del = [];
  for (let it = 0, changed = true; changed && it < 60; it++) {
    changed = false;
    for (let pass = 0; pass < 2; pass++) {
      del.length = 0;
      for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
        const i = y * w + x; if (!img[i]) continue;
        const p2 = img[i - w], p3 = img[i - w + 1], p4 = img[i + 1], p5 = img[i + w + 1], p6 = img[i + w], p7 = img[i + w - 1], p8 = img[i - 1], p9 = img[i - w - 1];
        const B = p2 + p3 + p4 + p5 + p6 + p7 + p8 + p9; if (B < 2 || B > 6) continue;
        const seq = [p2, p3, p4, p5, p6, p7, p8, p9, p2]; let A = 0; for (let k = 0; k < 8; k++) if (!seq[k] && seq[k + 1]) A++;
        if (A !== 1) continue;
        if (pass === 0 ? (p2 * p4 * p6 || p4 * p6 * p8) : (p2 * p4 * p8 || p2 * p6 * p8)) continue;
        del.push(i);
      }
      for (const i of del) img[i] = 0; if (del.length) changed = true;
    }
  }
}
function trace(img, w, h) {                      // skeleton pixels → polylines (junctions reusable, cycles closed)
  const N = (i) => {                             // 4-neighbours, plus diagonals only when no 4-path covers them
    const x = i % w, out = [], up = img[i - w], dn = img[i + w], lf = x > 0 && img[i - 1], rt = x < w - 1 && img[i + 1];
    if (up) out.push(i - w); if (dn) out.push(i + w); if (lf) out.push(i - 1); if (rt) out.push(i + 1);
    if (img[i - w - 1] && !up && !lf) out.push(i - w - 1); if (img[i - w + 1] && !up && !rt) out.push(i - w + 1);
    if (img[i + w - 1] && !dn && !lf) out.push(i + w - 1); if (img[i + w + 1] && !dn && !rt) out.push(i + w + 1);
    return out;
  };
  const deg = new Map(), used = new Set(), key = (a, b) => (a < b ? a * 1e7 + b : b * 1e7 + a), chains = [];
  for (let i = w; i < w * (h - 1); i++) if (img[i]) deg.set(i, N(i).length);
  const walk = (a, b) => {
    const c = [a, b]; used.add(key(a, b)); let prev = a, cur = b;
    while (deg.get(cur) === 2) { const nx = N(cur).find((n) => n !== prev && !used.has(key(cur, n))); if (nx === undefined) break; used.add(key(cur, nx)); c.push(nx); prev = cur; cur = nx; }
    return c;
  };
  for (const [i, d] of deg) if (d !== 2) for (const n of N(i)) if (!used.has(key(i, n))) chains.push(walk(i, n));
  for (const [i] of deg) for (const n of N(i)) if (!used.has(key(i, n))) chains.push(walk(i, n));
  return chains.filter((c) => c.length >= 4).map((c) => c.map((i) => [i % w, Math.floor(i / w)]));
}
function rdp(pts, eps) {
  if (pts.length < 3) return pts;
  const [ax, ay] = pts[0], [bx, by] = pts[pts.length - 1];
  if (Math.hypot(bx - ax, by - ay) < 2) {           // closed loop (o, e, 口): split at the point farthest from the start
    let im = 1, dm = 0; for (let i = 1; i < pts.length - 1; i++) { const d = Math.hypot(pts[i][0] - ax, pts[i][1] - ay); if (d > dm) { dm = d; im = i; } }
    return [...rdp(pts.slice(0, im + 1), eps).slice(0, -1), ...rdp(pts.slice(im), eps)];
  }
  const L2 = Math.hypot(bx - ax, by - ay);
  let dm = 0, im = 0;
  for (let i = 1; i < pts.length - 1; i++) { const d = Math.abs((by - ay) * pts[i][0] - (bx - ax) * pts[i][1] + bx * ay - by * ax) / L2; if (d > dm) { dm = d; im = i; } }
  return dm > eps ? [...rdp(pts.slice(0, im + 1), eps).slice(0, -1), ...rdp(pts.slice(im), eps)] : [pts[0], pts[pts.length - 1]];
}
/** Lay out a string and return per-glyph skeleton strokes in frame coordinates. */
function skeletonText(lib, tokens, text, { role, size, weight, x, y, tracking = 0, seed = 1 }) {
  const m = lib.layer("st_measure", 8, 8); lib.setFont(m, tokens, role, size, { weight });
  const lay = lib.layoutText(m, text, { x, y, tracking }), S = 2, out = [];
  lay.glyphs.forEach((g, gi) => {
    if (g.ch === " ") return;
    const pad = 12, w = Math.ceil((g.w + pad * 2) * S), h = Math.ceil(size * 1.45 * S), by = Math.round(size * 1.12 * S);
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const q = c.getContext("2d"); lib.setFont(q, tokens, role, size * S, { weight }); q.fillStyle = "#fff"; q.textAlign = "center"; q.fillText(g.ch, w / 2, by);
    const d = q.getImageData(0, 0, w, h).data, img = new Uint8Array(w * h);
    let sx = 0, sy = 0, sn = 0;
    for (let i = 0; i < w * h; i++) { img[i] = d[i * 4 + 3] > 110 ? 1 : 0; if (img[i]) { sx += i % w; sy += Math.floor(i / w); sn++; } }
    thin(img, w, h);
    let strokes = trace(img, w, h).map((c2) => rdp(c2, 1.1 * S).map(([px, py]) => [g.cx + (px - w / 2) / S, y + (py - by) / S]))
      .filter((s) => s.length > 1)
      .sort((a, b) => (a[0][1] - b[0][1]) * 0.6 + (a[0][0] - b[0][0]));   // carve roughly top-left first
    if (!strokes.length && sn) {                  // dots and small punctuation: a short gouge at the ink centroid
      const cx = g.cx + (sx / sn - w / 2) / S, cy = y + (sy / sn - by) / S;
      strokes = [[[cx - 2, cy - 2], [cx + 2, cy + 2]]];
    }
    if (!strokes.length) return;
    out.push({ ch: g.ch, strokes, word: 0, seed: seed * 100 + gi });
  });
  let wi = 0, k = 0; for (const ch of lib.graphemes(text)) { if (ch === " ") { wi++; continue; } out[k++].word = wi; }
  return out;
}

// ───────── scratching ─────────
const len = (s) => { let L = 0; for (let i = 1; i < s.length; i++) L += Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]); return L; };
/** Scratch one stroke up to arc length `upto`; `ph` = wander phase (changes every 2 frames). */
function scratch(ctx, lib, s, upto, ph, seed, color, { chips = true, scale = 1 } = {}) {
  const lines = 2 + Math.floor(lib.hash(seed, 1) * 3);
  const segs = [[], [], []];                        // three width buckets → three stroke() calls per line
  for (let l = 0; l < lines; l++) {
    const off = (lib.hash(seed, l, 2) - 0.5) * 3.4 * scale, wb = (0.6 + lib.hash(seed, l, 3) * 1.4) * scale;
    const a = l === 0 ? 0.95 : 0.3 + lib.hash(seed, l, 4) * 0.4;
    let d = 0; segs[0].length = segs[1].length = segs[2].length = 0;
    for (let i = 1; i < s.length && d < upto; i++) {
      const [x0, y0] = s[i - 1], [x1, y1] = s[i], sl = Math.hypot(x1 - x0, y1 - y0); if (sl < 0.01) continue;
      const nx = -(y1 - y0) / sl, ny = (x1 - x0) / sl, n = Math.max(1, Math.ceil(sl / 5));
      for (let k = 0; k < n && d < upto; k++) {
        const u0 = k / n, u1 = (k + 1) / n, da = d + sl * u0, db = Math.min(upto, d + sl * u1);
        if (lib.noise1(da / 13 + l * 7.3, seed + 3) > 0.62) continue;                      // breaks in the scratch
        const j0 = lib.noise1(da / 17 + ph * 1.7 + l * 5, seed) * 1.4 * scale + off, j1 = lib.noise1(db / 17 + ph * 1.7 + l * 5, seed) * 1.4 * scale + off;
        const ub = u0 + (db - da) / sl;
        const wv = wb * (0.45 + 1.1 * Math.abs(lib.noise1(da / 23 + l * 3.1, seed + 9)));
        segs[wv < 0.9 * scale ? 0 : wv < 1.6 * scale ? 1 : 2].push([x0 + (x1 - x0) * u0 + nx * j0, y0 + (y1 - y0) * u0 + ny * j0, x0 + (x1 - x0) * ub + nx * j1, y0 + (y1 - y0) * ub + ny * j1]);
      }
      d += sl;
    }
    ctx.strokeStyle = color; ctx.lineCap = "round"; ctx.globalAlpha = a;
    [0.7, 1.3, 2.2].forEach((wd, b) => {
      if (!segs[b].length) return; ctx.lineWidth = wd * scale; ctx.beginPath();
      for (const [ax, ay, bx, by] of segs[b]) { ctx.moveTo(ax, ay); ctx.lineTo(bx, by); } ctx.stroke();
    });
  }
  ctx.globalAlpha = 1; ctx.fillStyle = color;
  const [sx, sy] = s[0];                            // pressure blot where the point bit in
  if (lib.hash(seed, 4) < 0.55) { ctx.beginPath(); ctx.arc(sx + lib.hashS(seed, 5) * 1.2, sy + lib.hashS(seed, 6) * 1.2, (1.0 + lib.hash(seed, 7) * 1.4) * scale, 0, lib.TAU); ctx.fill(); }
  if (chips) {                                      // emulsion chips thrown off the stroke
    const n = Math.floor(Math.min(upto, len(s)) / 34);
    for (let c = 0; c < n; c++) {
      if (lib.hash(seed, c, 8) > 0.45) continue;
      const i = Math.min(s.length - 1, 1 + Math.floor(lib.hash(seed, c, 9) * (s.length - 1)));
      ctx.globalAlpha = 0.9; ctx.beginPath(); ctx.arc(s[i][0] + lib.hashS(seed, c, 10) * 5, s[i][1] + lib.hashS(seed, c, 11) * 5, (0.7 + lib.hash(seed, c, 12) * 1.4) * scale, 0, lib.TAU); ctx.fill();
    }
    ctx.globalAlpha = 1;
  }
}
/** Carve a whole string: glyph i starts at start + i·stagger and is carved over `carve` frames (2-frame steps). */
function carve(ctx, lib, t, glyphs, { start, stagger, carve = 8, seed = 1, color, alpha = 1, ghost = 0.28, scale = 1 }) {
  const f = lib.frame(t), ph = Math.floor(f / 2);
  const pass = (ox, oy, a, phase) => {
    ctx.save(); ctx.globalAlpha = a;
    for (let gi = 0; gi < glyphs.length; gi++) {
      const g = glyphs[gi], f0 = Math.round((start + gi * stagger) * 30); if (f < f0) continue;
      const u = Math.min(1, (Math.floor((f - f0) / 2) * 2 + 2) / carve);
      const tot = g.strokes.reduce((acc, s) => acc + len(s), 0); let budget = u * tot;
      const wx = lib.hashS(seed, g.word, phase, 1) * 2.6, wy = lib.hashS(seed, g.word, phase, 2) * 2.6, rot = lib.hashS(seed, g.word, phase, 3) * 0.6 * Math.PI / 180;
      let jx = 0, jy = 0; if (lib.hash(seed, f, 7) < 0.06) { jx = lib.hashS(seed, f, 8) * 24; jy = lib.hashS(seed, f, 9) * 9; }   // rare 1-frame jump
      const c0 = g.strokes[0][0];
      ctx.save(); ctx.translate(c0[0] + wx + jx + ox, c0[1] + wy + jy + oy); ctx.rotate(rot); ctx.translate(-c0[0], -c0[1]);
      g.strokes.forEach((s, si) => { if (budget <= 0) return; const L0 = len(s); scratch(ctx, lib, s, budget, phase, g.seed * 31 + si, color, { scale }); budget -= L0; });
      ctx.restore();
    }
    ctx.restore();
  };
  if (ghost > 0) { const k = Math.floor(f / 3); pass(6 + lib.hash(seed, k, 11) * 6, -3 + lib.hash(seed, k, 12) * 6, alpha * ghost, ph + 17); }
  pass(0, 0, alpha, ph);
}

// ───────── setup ─────────
export async function setup(ctx, tokens, lib) {
  const sk = (text, o) => skeletonText(lib, tokens, text, o);
  const slots = lib.slots(3, { area: lib.SAFE.title, y: 700, gap: 64 });
  L = {
    en: sk(lib.TITLE_EN, { role: "display", size: 128, weight: 400, x: 188, y: 318, tracking: 3, seed: 3 }),
    zh: sk(lib.TITLE_ZH, { role: "zh", size: 86, weight: 400, x: 196, y: 458, tracking: 10, seed: 9 }),
    lab: lib.MOTIF.map((m, k) => sk(m.zh, { role: "zh", size: 52, weight: 400, x: slots[k].x - 58, y: 955, tracking: 10, seed: 20 + k })),
    endT: sk("SCRATCHED TYPE", { role: "display", size: 104, weight: 400, x: 192, y: 560, tracking: 10, seed: 31 }),
    endZ: sk("刮擦字片头", { role: "zh", size: 66, weight: 400, x: 196, y: 662, tracking: 10, seed: 37 }),
    slots,
    // the ripping scratch of the hook: one long wobbly diagonal
    rip: Array.from({ length: 40 }, (_, i) => [-80 + i * 52, 170 + i * 19 + lib.noise1(i * 0.4, 5) * 26]),
  };
  const tex = document.createElement("canvas"); tex.width = 320; tex.height = 180;
  const tx = tex.getContext("2d"), im = tx.createImageData(320, 180), [R, G, B] = lib.rgb(lib.color(tokens, "extra.0"));
  for (let j = 0; j < 180; j++) for (let i = 0; i < 320; i++) {
    const m = 0.55 + 0.6 * lib.fbm2(i / 38, j / 38, { octaves: 5, seed: 13 }) + 0.25 * lib.fbm2(i / 6, j / 6, { octaves: 2, seed: 14 }), k = (j * 320 + i) * 4;
    im.data[k] = lib.clamp(R * m, 0, 255); im.data[k + 1] = lib.clamp(G * m, 0, 255); im.data[k + 2] = lib.clamp(B * m, 0, 255); im.data[k + 3] = 255;
  }
  tx.putImageData(im, 0, 0); L.tex = tex;
}

// macro inserts, one cut per beat from 2.0 s: [first frame, last frame, kind]; bright ones are kept ≥ 1 s apart
const INSERTS = [[12, 13, "glyph"], [36, 37, "scratch"], [60, 61, "glyph"], [72, 74, "sprocket"], [84, 85, "scratch"], [96, 97, "glyph"], [108, 110, "sprocket"]];

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k), f = lib.frame(t), { W, H } = lib;
  const wx = 1.5 * Math.sin(lib.TAU * 0.7 * t) + 0.6 * Math.sin(lib.TAU * 1.3 * t + 1), wy = 2 * Math.sin(lib.TAU * 0.55 * t + 2);
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(wx, wy);
  const ins = INSERTS.find(([a, b]) => f >= a && f <= b);
  if (ins) insert(ctx, t, lib, ins[2], tokens);
  else if (f === 6 || f === 120) { ctx.fillStyle = C("accent"); ctx.fillRect(-10, -10, W + 20, H + 20); }   // red flash frames
  else if (t < 4.0) { hook(ctx, t, tokens, lib); main(ctx, t, tokens, lib); }
  else if (f <= 126) {                          // double exposure: both images jitter, alternating dominance
    main(ctx, t, tokens, lib);
    ctx.globalAlpha = f % 2 ? 0.55 : 0.4; ctx.fillStyle = C("bg"); ctx.fillRect(-10, -10, W + 20, H + 20); ctx.globalAlpha = 1;
    ctx.globalCompositeOperation = "lighter"; end(ctx, t, tokens, lib, 0.8); ctx.globalCompositeOperation = "source-over";
  } else end(ctx, t, tokens, lib, 1);
  ctx.restore();
  film(ctx, t, tokens, lib);
}

function hook(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), f = lib.frame(t);
  // the rip: carved across the whole frame over frames 1–4, then it stays as a faint scar
  if (f >= 1) {
    const u = Math.min(1, f / 4), tot = len(L.rip);
    const scar = f <= 5 ? 1 : 1 - (f - 5) / 26; if (scar <= 0) return hookTail(ctx, t, tokens, lib);
    ctx.save(); ctx.globalAlpha = scar;
    ctx.shadowColor = C("fg"); ctx.shadowBlur = f <= 4 ? 18 : 0;
    scratch(ctx, lib, L.rip, u * tot, Math.floor(f / 2), 501, C("fg"), { scale: 3.0 });
    ctx.restore();
    if (f <= 4) {                               // sparks at the point of the tool
      const i = Math.min(L.rip.length - 1, Math.floor(u * (L.rip.length - 1))), [px, py] = L.rip[i];
      ctx.save(); ctx.fillStyle = C("fg");
      for (let k = 0; k < 26; k++) { ctx.globalAlpha = 0.9; ctx.beginPath(); ctx.arc(px - lib.hash(f, k, 1) * 120, py + lib.hashS(f, k, 2) * 60, 1 + lib.hash(f, k, 3) * 2.5, 0, lib.TAU); ctx.fill(); }
      ctx.restore();
    }
  }
  hookTail(ctx, t, tokens, lib);
}
function hookTail(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), f = lib.frame(t);
  // punched leader hole: flashes for 2 frames at 0.5 s, then a scratched cross stays
  if (f >= 15 && f <= 16) { ctx.save(); ctx.fillStyle = C("extra.2"); ctx.beginPath(); ctx.arc(1640, 180, 64, 0, lib.TAU); ctx.fill(); ctx.restore(); }
  if (f >= 17 && t < 2.0) {
    ctx.save(); ctx.globalAlpha = 0.6;
    scratch(ctx, lib, [[1590, 130], [1690, 230]], 999, Math.floor(f / 2), 601, C("extra.2"));
    scratch(ctx, lib, [[1690, 130], [1590, 230]], 999, Math.floor(f / 2), 602, C("extra.2"));
    ctx.restore();
  }
}

function main(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  carve(ctx, lib, t, L.en, { start: 0.82, stagger: 0.045, carve: 8, seed: 31, color: C("fg"), scale: 1.25, ghost: 0.2 });
  carve(ctx, lib, t, L.zh, { start: 1.6, stagger: 0.075, carve: 8, seed: 37, color: C("fg"), ghost: 0.1, scale: 0.95 });
  if (t >= 2.0) frames(ctx, t, tokens, lib);
}

// three loose film frames, each slipping in the gate on its own; only a sliver of sprocket holes at one edge
function frames(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), f = lib.frame(t), ph = Math.floor(f / 2);
  const fw = 400, fh = 236, base = [[-16, -1.6], [12, 1.1], [-5, -0.7]];
  L.slots.forEach((sl, k) => {
    const t0 = 2.0 + k * 0.2; if (t < t0) return;
    let jx = lib.hashS(71, k, ph, 1) * 3, jy = lib.hashS(71, k, ph, 2) * 3;
    if (lib.hash(72, k, f) < 0.07) jy += lib.hashS(73, k, f) * 16;                   // a frame slips for one frame
    ctx.save(); ctx.translate(sl.x + jx, 650 + base[k][0] + jy); ctx.rotate(base[k][1] * Math.PI / 180);
    ctx.fillStyle = "#050404"; ctx.fillRect(-fw / 2, -fh / 2, fw, fh);
    ctx.strokeStyle = lib.rgba(C("extra.2"), 0.35); ctx.lineWidth = 1.5; ctx.strokeRect(-fw / 2, -fh / 2, fw, fh);
    const side = k === 1 ? 1 : -1;                                                     // sprocket sliver: half-holes cut by the edge
    ctx.fillStyle = C("extra.1");
    for (let j = 0; j < 4; j++) { ctx.beginPath(); ctx.roundRect(side * fw / 2 - 11, -fh / 2 + 22 + j * 56, 22, 30, 5); ctx.fill(); }
    ctx.strokeStyle = lib.rgba(C("extra.2"), 0.5); ctx.lineWidth = 1;
    for (let j = 0; j < 4; j++) { ctx.beginPath(); ctx.roundRect(side * fw / 2 - 11, -fh / 2 + 22 + j * 56, 22, 30, 5); ctx.stroke(); }
    // the icon, scratched in over 10 frames
    const u = lib.clamp((Math.floor((f - Math.round(t0 * 30)) / 2) * 2 + 2) / 10);
    const fg = C("fg"), strokes = k === 0 ? [[[-120, -52], [120, -54]], [[-120, 0], [118, 2]], [[-120, 52], [30, 50]]]
      : k === 1 ? [-1, 0, 1].map((j) => [[j * 108 - 42, -62], [j * 108 + 42, -64], [j * 108 + 44, 62], [j * 108 - 40, 64], [j * 108 - 42, -62]])
      : [Array.from({ length: 25 }, (_, i) => { const a = i / 24 * lib.TAU; return [Math.cos(a) * (58 + lib.noise1(i * 0.7, 9) * 5), Math.sin(a) * (58 + lib.noise1(i * 0.7, 9) * 5)]; })];
    if (k === 2 && u >= 1) {                            // the draft: a red cue mark, the reel-change blot scratched into the frame
      ctx.fillStyle = C("accent"); ctx.globalAlpha = 0.92; ctx.beginPath();
      for (let i = 0; i <= 24; i++) { const a = i / 24 * lib.TAU, r = 52 + lib.noise1(i * 0.7, 9) * 5; i ? ctx.lineTo(Math.cos(a) * r, Math.sin(a) * r) : ctx.moveTo(r, 0); }
      ctx.closePath(); ctx.fill(); ctx.globalAlpha = 1;
    }
    const tot = strokes.reduce((a, s) => a + len(s), 0); let budget = u * tot;
    strokes.forEach((s, si) => { if (budget > 0) scratch(ctx, lib, s, budget, ph, 700 + k * 10 + si, fg, { scale: 1.5 }); budget -= len(s); });
    ctx.restore();
    // labels: typed English, scratched Chinese
    const lab = lib.typewriter(lib.MOTIF[k].en.toUpperCase(), t, { start: t0 + 0.12, cps: 30 });
    ctx.save(); lib.setFont(ctx, tokens, "body", 32, { weight: 400 }); ctx.fillStyle = fg;
    lib.drawText(ctx, lab, sl.x, 874, { align: "center", tracking: 5 }); ctx.restore();
    carve(ctx, lib, t, L.lab[k], { start: t0 + 0.28, stagger: 0.07, carve: 6, seed: 40 + k, color: C("extra.2"), ghost: 0 });
  });
}

function insert(ctx, t, lib, kind, tokens) {
  const { W, H } = lib, f = lib.frame(t), bone = lib.color(tokens, "extra.2");
  ctx.save(); ctx.imageSmoothingQuality = "high";
  if (kind === "glyph") {                           // sepia emulsion, extreme close-up of one carved glyph (bright)
    const z = 1.2 + 0.02 * f;
    ctx.drawImage(L.tex, -lib.hash(f, 3) * 200, -lib.hash(f, 4) * 120, W * z, H * z);
    const g = L.en[(f * 7) % L.en.length], c0 = g.strokes[0][0];
    ctx.translate(W / 2, H / 2); ctx.scale(5.5, 5.5); ctx.translate(-c0[0] - 30, -c0[1] + 50);
    g.strokes.forEach((s, si) => scratch(ctx, lib, s, 9999, Math.floor(f / 2), g.seed * 31 + si, "#f2ebdc", { chips: true }));
  } else if (kind === "sprocket") {                 // macro of the perforations sliding through the gate (dark)
    ctx.fillStyle = "#1a1714"; ctx.fillRect(0, 0, W, H);
    const off = (f * 90) % 420;
    for (let j = -1; j < 4; j++) { const y = j * 420 + off - 200; ctx.fillStyle = "#050404"; ctx.beginPath(); ctx.roundRect(W * 0.3, y, 520, 300, 60); ctx.fill(); ctx.strokeStyle = lib.rgba(bone, 0.5); ctx.lineWidth = 4; ctx.stroke(); }
    ctx.fillStyle = lib.rgba(bone, 0.15); ctx.fillRect(W * 0.3 - 80, 0, 6, H);
  } else {                                          // macro of one scratch being cut (dark with a bright gouge)
    ctx.fillStyle = "#0a0908"; ctx.fillRect(0, 0, W, H);
    ctx.translate(W / 2, H / 2); ctx.rotate(-0.35); ctx.scale(4, 4);
    scratch(ctx, lib, [[-260, 0], [-120, 6], [0, -4], [140, 8], [260, 2]], 9999, Math.floor(f / 2), 950 + f, bone, { chips: true });
  }
  ctx.restore();
}

function end(ctx, t, tokens, lib, alpha) {
  const C = (k) => lib.color(tokens, k), f = lib.frame(t);
  ctx.save(); ctx.globalAlpha = alpha * 0.7; scratch(ctx, lib, [[1480, 150], [1484, 520], [1480, 930]], 9999, Math.floor(f / 2), 90, C("extra.2"), { scale: 1.3 }); ctx.restore();
  carve(ctx, lib, t, L.endT, { start: 4.12, stagger: 0.03, carve: 6, seed: 43, color: C("fg"), alpha, ghost: 0.25, scale: 1.2 });
  carve(ctx, lib, t, L.endZ, { start: 4.4, stagger: 0.05, carve: 6, seed: 47, color: C("extra.2"), alpha, ghost: 0 });
}

function film(ctx, t, tokens, lib) {
  const { W, H } = lib, f = lib.frame(t), bone = lib.color(tokens, "extra.2");
  ctx.save();
  for (let s = 0; s < 2; s++) {                 // two running vertical scratches
    if (lib.hash(77, s, f) < 0.25) continue;
    const x = [612, 1333][s] + lib.hashS(78, s, f) * 3;
    ctx.globalAlpha = 0.14 + 0.1 * lib.hash(79, s, f); ctx.fillStyle = bone; ctx.fillRect(x, 0, 1.4, H);
  }
  for (let d = 0; d < 3; d++) {                 // dust and hairs, 1–2 frames each
    const k = Math.floor(f / 2) * 3 + d;
    if (lib.hash(80, k) > 0.35) continue;
    const x = lib.hash(81, k) * W, y = lib.hash(82, k) * H;
    ctx.globalAlpha = 0.55; ctx.strokeStyle = bone; ctx.fillStyle = bone; ctx.lineWidth = 1.3;
    if (lib.hash(83, k) < 0.5) { ctx.beginPath(); ctx.arc(x, y, 1.5 + lib.hash(84, k) * 3, 0, lib.TAU); ctx.fill(); }
    else { ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + 30, y + lib.hashS(85, k) * 40, x + 18 + lib.hash(86, k) * 50, y + lib.hashS(87, k) * 60); ctx.stroke(); }
  }
  ctx.restore();
  lib.grain(ctx, t, { amount: 0.12, fps: 24, seed: 9, size: 1.5 });
  lib.vignette(ctx, { strength: 0.55, inner: 0.45, color: "#000000" });
}

// foley (events.json is generated from this list; insert and flash frames are the INSERTS / flash constants above)
export const FOLEY = [
  { t: 4 / 30, sfx: "swish_rev", gain_db: -4, pan: 0.3, dur: 0.15, pan_from: -0.6, pan_to: 0.6 },                                                // the rip lands
  { t: 6 / 30, sfx: "impact", gain_db: -6, pan: 0 }, { t: 15 / 30, sfx: "shutter", gain_db: -8, pan: 0.7 },   // red flash; punch
  ...INSERTS.map(([a, , kind]) => ({ t: a / 30, sfx: kind === "sprocket" ? "shutter" : "glitch", gain_db: -12, pan: 0 })),
  ...[0.82, 1.045, 1.27, 1.36].map((t, k) => ({ t, sfx: "swish_rev", gain_db: -16, pan: [-0.7, -0.4, -0.05, 0.1][k], dur: 0.25, bright: 0.3 })),   // each word carved
  { t: 1.6, sfx: "swish_rev", gain_db: -16, pan: -0.6, dur: 0.25, bright: 0.3 },
  { t: 120 / 30, sfx: "impact", gain_db: -4, pan: 0 }, { t: 4.12, sfx: "tape", gain_db: -10, pan: -0.5, dur: 0.3, dir: "down" },
];
