// scratched-type swatch — hand-scratched, jittery industrial title grammar.
//   0.0–0.8  warm black film base: gate weave, grain, dust, running scratches; a 2-frame macro insert
//   0.8–2.6  a bone splice flash, then every glyph is etched in stroke by stroke (6–10 frames), doubled hairlines,
//            broken gaps and slips; words jitter every 2 frames, a faint double-exposed ghost, rare 1-frame jumps
//   2.0–4.0  a strip of three film frames cut in; outline / storyboard / draft scratched into them (the draft wedge
//            is the dried red); typed labels; 2–3 frame macro inserts keep the cutting rhythm
//   4.0–5.0  one dried-red flash frame, 5 frames of double exposure, then the end card etched on black leader
// Randomness: setup uses lib.rng (layout, glyph damage); per-frame jitter uses lib.hash on the frame index.

let L = null;

export const fonts = ["Helvetica Neue", "American Typewriter", "Kaiti SC"];

// scratch one string into per-glyph canvases (damage is baked once; only jitter happens per frame)
function etchText(lib, tokens, text, { role, size, weight, seed, color, x, y, tracking = 0 }) {
  const ctx = lib.layer("st_measure", 8, 8);
  lib.setFont(ctx, tokens, role, size, { weight });
  const lay = lib.layoutText(ctx, text, { x, y, tracking });
  const r = lib.rng(seed), out = [];
  for (const g of lay.glyphs) {
    if (g.ch === " ") continue;
    const pad = 44, w = Math.ceil(g.w + pad * 2), h = Math.ceil(size * 1.5 + pad);
    const c = document.createElement("canvas"); c.width = w; c.height = h;
    const q = c.getContext("2d"), cx = w / 2, by = size * 1.1 + pad * 0.5;
    lib.setFont(q, tokens, role, size, { weight }); q.textAlign = "center"; q.textBaseline = "alphabetic";
    q.fillStyle = color; q.strokeStyle = color;
    q.globalAlpha = 0.95; q.fillText(g.ch, cx, by);
    q.globalAlpha = 0.6; q.lineWidth = 1.3; q.strokeText(g.ch, cx + 1.7, by - 1.1);        // doubled hairlines
    q.globalAlpha = 0.38; q.lineWidth = 0.9; q.strokeText(g.ch, cx - 1.3, by + 1.5);
    q.globalCompositeOperation = "destination-out"; q.globalAlpha = 1; q.lineCap = "butt";   // breaks in the stroke
    const nGap = Math.round(g.w * size / 900) + 3;
    for (let i = 0; i < nGap; i++) {
      const gx = cx + (r() - 0.5) * g.w, gy = by - r() * size * 0.75, a = r() * Math.PI, len = 4 + r() * 7;
      q.lineWidth = 2 + r() * 1.6; q.beginPath(); q.moveTo(gx - Math.cos(a) * len / 2, gy - Math.sin(a) * len / 2); q.lineTo(gx + Math.cos(a) * len / 2, gy + Math.sin(a) * len / 2); q.stroke();
    }
    q.globalCompositeOperation = "source-over";
    if (r() < 0.4) {                                                               // the slip at the stroke end
      const sx = cx + (r() - 0.3) * g.w * 0.7, sy = by - r() * size * 0.25, a = (r() - 0.5) * 0.7, len = 12 + r() * 30;
      q.globalAlpha = 0.8; q.lineWidth = 1.2; q.beginPath(); q.moveTo(sx, sy); q.lineTo(sx + Math.cos(a) * len, sy + Math.sin(a) * len); q.stroke();
    }
    out.push({ ch: g.ch, img: c, x: g.cx - w / 2, y: y - by, w, h, word: 0 });
  }
  // word index for word-level jitter
  let wi = 0, gi = 0;
  for (const ch of lib.graphemes(text)) { if (ch === " ") { wi++; continue; } out[gi++].word = wi; }
  return out;
}

export async function setup(ctx, tokens, lib) {
  const fg = lib.color(tokens, "fg"), bone = lib.color(tokens, "extra.2");
  const en = etchText(lib, tokens, lib.TITLE_EN, { role: "display", size: 132, weight: 300, seed: 3, color: fg, x: 190, y: 322, tracking: 2 });
  const zh = etchText(lib, tokens, lib.TITLE_ZH, { role: "zh", size: 78, weight: 400, seed: 9, color: fg, x: 196, y: 452, tracking: 6 });
  const endT = etchText(lib, tokens, "SCRATCHED TYPE", { role: "display", size: 96, weight: 300, seed: 21, color: fg, x: 192, y: 560, tracking: 10 });
  const endZ = etchText(lib, tokens, "刮擦字片头", { role: "zh", size: 64, weight: 400, seed: 23, color: bone, x: 196, y: 660, tracking: 8 });
  // macro insert texture (sepia emulsion, low-res then scaled up)
  const tex = document.createElement("canvas"); tex.width = 320; tex.height = 180;
  const tx = tex.getContext("2d"), im = tx.createImageData(320, 180), [R, G, B] = lib.rgb(lib.color(tokens, "extra.0"));
  for (let j = 0; j < 180; j++) for (let i = 0; i < 320; i++) {
    const m = 0.55 + 0.6 * lib.fbm2(i / 38, j / 38, { octaves: 5, seed: 13 }) + 0.25 * lib.fbm2(i / 6, j / 6, { octaves: 2, seed: 14 }), k = (j * 320 + i) * 4;
    im.data[k] = lib.clamp(R * m, 0, 255); im.data[k + 1] = lib.clamp(G * m, 0, 255); im.data[k + 2] = lib.clamp(B * m, 0, 255); im.data[k + 3] = 255;
  }
  tx.putImageData(im, 0, 0);
  const slots = lib.slots(3, { area: lib.SAFE.title, y: 702, gap: 64 });
  L = { en, zh, endT, endZ, tex, slots };
}

const FRAME_IN = [0.85, 1.62];          // title: first glyph etch start, Chinese start
const INSERTS = [[13, 14, "tex"], [55, 57, "macro"], [101, 103, "tex"], [111, 112, "macro"]];   // [first, last frame]

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const f = lib.frame(t), { W, H } = lib;
  // gate weave: two slow sines, the whole picture shifts
  const wx = 1.5 * Math.sin(lib.TAU * 0.7 * t) + 0.6 * Math.sin(lib.TAU * 1.3 * t + 1), wy = 2 * Math.sin(lib.TAU * 0.55 * t + 2);
  const ins = INSERTS.find(([a, b]) => f >= a && f <= b);
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  ctx.save(); ctx.translate(wx, wy);
  if (ins) insert(ctx, t, tokens, lib, ins[2]);
  else if (f === 24) { ctx.fillStyle = C("extra.2"); ctx.globalAlpha = 0.85; ctx.fillRect(-10, -10, W + 20, H + 20); }   // splice flash (bone)
  else if (f === 120) { ctx.fillStyle = C("accent"); ctx.fillRect(-10, -10, W + 20, H + 20); }                        // the red flash
  else if (t < 4.0) main(ctx, t, tokens, lib);
  else if (f <= 126) {                          // double exposure: both frames jitter, alternating dominance
    const a = (f % 2 ? 0.55 : 0.4);
    ctx.globalAlpha = 1; main(ctx, t, tokens, lib);
    ctx.globalAlpha = a; ctx.fillStyle = C("bg"); ctx.fillRect(-10, -10, W + 20, H + 20);
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = "lighter"; end(ctx, t, tokens, lib, 0.8);
    ctx.globalCompositeOperation = "source-over";
  } else end(ctx, t, tokens, lib, 1);
  ctx.restore();
  film(ctx, t, tokens, lib);
}

function jit(lib, seed, k, t) {                 // jitter every 2 frames, rare 1-frame jumps
  const j = Math.floor(lib.frame(t) / 2);
  let dx = lib.hashS(seed, k, j, 1) * 3, dy = lib.hashS(seed, k, j, 2) * 3, rot = lib.hashS(seed, k, j, 3) * 0.6 * Math.PI / 180;
  if (lib.hash(seed, lib.frame(t), 7) < 0.07) { dx += lib.hashS(seed, lib.frame(t), 8) * 26; dy += lib.hashS(seed, lib.frame(t), 9) * 10; }
  return { dx, dy, rot };
}
/** Draw etched glyphs; each glyph is carved top→bottom over `etch` frames (2-frame steps) starting at start + i·stagger. */
function drawEtched(ctx, lib, t, glyphs, { start, stagger, etch = 8, seed = 1, alpha = 1, ghost = 0.3 }) {
  const f = lib.frame(t);
  const draw = (ox, oy, a) => {
    for (let i = 0; i < glyphs.length; i++) {
      const g = glyphs[i], f0 = Math.round((start + i * stagger) * 30);
      if (f < f0) continue;
      const u = Math.min(1, (Math.floor((f - f0) / 2) * 2 + 2) / etch);
      const J = jit(lib, seed, g.word, t), gj = lib.hashS(seed, i, Math.floor(f / 2), 5);
      ctx.save(); ctx.globalAlpha = a;
      ctx.translate(g.x + g.w / 2 + J.dx + gj + ox, g.y + g.h / 2 + J.dy + oy); ctx.rotate(J.rot);
      ctx.beginPath(); ctx.rect(-g.w / 2, -g.h / 2, g.w, g.h * u); ctx.clip();
      ctx.drawImage(g.img, -g.w / 2, -g.h / 2);
      ctx.restore();
    }
  };
  if (ghost > 0) { const k = Math.floor(f / 3); draw(6 + lib.hash(seed, k, 11) * 7, -3 + lib.hash(seed, k, 12) * 6, alpha * ghost); }
  draw(0, 0, alpha);
}

function main(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  drawEtched(ctx, lib, t, L.en, { start: FRAME_IN[0], stagger: 0.043, seed: 31 });
  drawEtched(ctx, lib, t, L.zh, { start: FRAME_IN[1], stagger: 0.07, seed: 37, ghost: 0.22 });
  if (t >= 1.97) strip(ctx, t, tokens, lib);
}

function strip(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const f = lib.frame(t), J = jit(lib, 41, 0, t);
  const y0 = 590, h = 226, x0 = 150, x1 = lib.W - 150;
  ctx.save(); ctx.translate(J.dx * 0.5, J.dy * 0.5);
  ctx.fillStyle = C("extra.1"); ctx.fillRect(x0, y0, x1 - x0, h);                       // leader
  ctx.fillStyle = C("bg");
  for (let x = x0 + 20; x < x1 - 20; x += 46) { ctx.beginPath(); ctx.roundRect(x, y0 + 10, 22, 16, 4); ctx.roundRect(x, y0 + h - 26, 22, 16, 4); ctx.fill(); }
  const fw = 400, fh = 150;
  L.slots.forEach((sl, k) => {
    const fx = sl.x - fw / 2, fy = y0 + (h - fh) / 2;
    ctx.fillStyle = C("bg"); ctx.fillRect(fx, fy, fw, fh);
    const f0 = Math.round((2.05 + k * 0.2) * 30);
    if (f < f0) return;
    const u = lib.clamp((Math.floor((f - f0) / 2) * 2 + 2) / 10);           // scratched in over 10 frames, 2-frame steps
    ctx.save(); ctx.beginPath(); ctx.rect(fx, fy, fw * u, fh); ctx.clip();
    icon(ctx, lib, tokens, k, sl.x, fy + fh / 2, f);
    ctx.restore();
    // typed label, then the Chinese scratched in bone
    const lab = lib.typewriter(lib.MOTIF[k].en.toUpperCase(), t, { start: 2.15 + k * 0.2, cps: 30 });
    lib.setFont(ctx, tokens, "body", 32, { weight: 400 }); ctx.fillStyle = C("fg");
    lib.drawText(ctx, lab, sl.x, y0 + h + 62, { align: "center", tracking: 5 });
    if (t >= 2.3 + k * 0.2) { lib.setFont(ctx, tokens, "zh", 50, { weight: 400 }); ctx.fillStyle = C("extra.2"); lib.drawText(ctx, lib.MOTIF[k].zh, sl.x, y0 + h + 130, { align: "center", tracking: 10 }); }
  });
  ctx.restore();
}

function scratchLine(ctx, lib, pts, seed, color, width = 2) {   // a doubled, broken hand-scratched line
  ctx.strokeStyle = color; ctx.lineCap = "round";
  for (let p = 0; p < 2; p++) {
    ctx.globalAlpha = p ? 0.45 : 0.95; ctx.lineWidth = p ? width * 0.6 : width;
    lib.wobblePath(ctx, pts.map(([x, y]) => [x + p * 1.8, y - p * 1.2]), { amp: 1.4, seed: seed + p * 7, seg: 12 });
    ctx.setLineDash([22 + lib.hash(seed, 1) * 30, 4 + lib.hash(seed, 2) * 5]); ctx.stroke(); ctx.setLineDash([]);
  }
  ctx.globalAlpha = 1;
}
function icon(ctx, lib, tokens, k, cx, cy, f) {
  const fg = lib.color(tokens, "fg"), red = lib.color(tokens, "accent");
  if (k === 0) [[150, -44], [150, 0], [90, 44]].forEach(([w, dy], j) => scratchLine(ctx, lib, [[cx - 120, cy + dy], [cx - 120 + w * 1.6, cy + dy + lib.hashS(k, j) * 3]], 50 + j, fg, 3));
  else if (k === 1) for (let j = 0; j < 3; j++) { const x = cx - 150 + j * 105; scratchLine(ctx, lib, [[x, cy - 48], [x + 90, cy - 50], [x + 92, cy + 48], [x - 2, cy + 50], [x, cy - 48]], 60 + j, fg, 2.5); }
  else {
    ctx.save(); ctx.fillStyle = red; ctx.globalAlpha = 0.95; ctx.beginPath(); ctx.moveTo(cx - 40, cy - 52); ctx.lineTo(cx + 58, cy); ctx.lineTo(cx - 40, cy + 52); ctx.closePath(); ctx.fill(); ctx.restore();
    scratchLine(ctx, lib, [[cx - 44, cy - 58], [cx + 64, cy], [cx - 44, cy + 58], [cx - 44, cy - 58]], 70, fg, 2.5);
  }
}

function insert(ctx, t, tokens, lib, kind) {
  const { W, H } = lib, f = lib.frame(t);
  ctx.save(); ctx.imageSmoothingQuality = "high";
  const z = 1.2 + 0.02 * f, ox = -lib.hash(f, 3) * 200, oy = -lib.hash(f, 4) * 120;
  ctx.drawImage(L.tex, ox, oy, W * z, H * z);
  if (kind === "macro") {                    // extreme close-up of one scratched letter of the title
    const g = L.en[(f * 7) % L.en.length];
    ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = 0.9;
    ctx.drawImage(g.img, W / 2 - g.w * 3.2 + lib.hashS(f, 5) * 60, H / 2 - g.h * 3.4, g.w * 6.4, g.h * 6.4);
  }
  ctx.restore();
}

function end(ctx, t, tokens, lib, alpha) {
  const C = (k) => lib.color(tokens, k);
  const f = lib.frame(t);
  // a splice: vertical scratched line down the middle-right, and the name etched in
  scratchLine(ctx, lib, [[1480, 150], [1486, 930]], 90 + (f >> 2), C("extra.2"), 2);
  drawEtched(ctx, lib, t, L.endT, { start: 4.12, stagger: 0.03, seed: 43, alpha, ghost: 0.25 });
  drawEtched(ctx, lib, t, L.endZ, { start: 4.4, stagger: 0.05, seed: 47, alpha, ghost: 0 });
}

function film(ctx, t, tokens, lib) {
  const { W, H } = lib, f = lib.frame(t), bone = lib.color(tokens, "extra.2");
  ctx.save();
  // two running vertical scratches, visible most frames
  for (let s = 0; s < 2; s++) {
    if (lib.hash(77, s, f) < 0.25) continue;
    const x = [612, 1333][s] + lib.hashS(78, s, f) * 3;
    ctx.globalAlpha = 0.16 + 0.1 * lib.hash(79, s, f); ctx.fillStyle = bone; ctx.fillRect(x, 0, 1.4, H);
  }
  // dust and hairs: a few per second, each lives 1–2 frames
  for (let d = 0; d < 3; d++) {
    const k = Math.floor(f / 2) * 3 + d;
    if (lib.hash(80, k) > 0.35) continue;
    const x = lib.hash(81, k) * W, y = lib.hash(82, k) * H;
    ctx.globalAlpha = 0.55; ctx.strokeStyle = bone; ctx.fillStyle = bone; ctx.lineWidth = 1.3;
    if (lib.hash(83, k) < 0.5) { ctx.beginPath(); ctx.arc(x, y, 1.5 + lib.hash(84, k) * 3, 0, lib.TAU); ctx.fill(); }
    else { ctx.beginPath(); ctx.moveTo(x, y); ctx.quadraticCurveTo(x + 30, y + lib.hashS(85, k) * 40, x + 18 + lib.hash(86, k) * 50, y + lib.hashS(87, k) * 60); ctx.stroke(); }
  }
  ctx.restore();
  lib.grain(ctx, t, { amount: 0.13, fps: 24, seed: 9, size: 1.5 });
  lib.vignette(ctx, { strength: 0.55, inner: 0.45, color: "#000000" });
}
