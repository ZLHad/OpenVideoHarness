// archival-pan-zoom swatch — slow, purposeful camera moves over still photographs; restrained serif captions.
// Both "photographs" are generated in setup (nothing downloaded): a board with three pinned documents (a handwritten
// outline page with a signature, a storyboard sheet, a portrait print) and a landscape print. They are drawn in grey
// with depth (the wall is softer than the papers), then graded to one warm monochrome with grain, vignette, scratches.
//   0.0–0.8  in motion from frame 0: a 2.3× close-up of the handwriting and signature, pulling focus in 0.05–0.35 s
//   0.8–2.6  the pull-back reveals the board; captions fade in one line at a time on a darkened band
//   2.0–4.0  the pan carries the portrait print into frame (2.0–2.6); a faded-red ring is drawn around the face
//            (done at 2.8), the caption line turns to "初版 · DRAFT" at 3.2, the push toward the face gathers at 3.6
//   4.0–5.0  an in-motion dissolve (21 frames) to the landscape, panning the same way, then the style name
// Camera = focus point + zoom in photo coordinates, Catmull–Rom through keys, already moving at every cut.

const BW = 2800, LW = 2400, PH = 1350, BASE = 1920 / 2400;
let L = null;
export const fonts = ["Baskerville", "Songti SC", "American Typewriter"];

export async function setup(ctx, tokens, lib) {
  L = { board: sepia(lib, tokens, makeBoard(lib, tokens), BW, 11), land: sepia(lib, tokens, makeLandscape(lib), LW, 12) };
}

// ───────── photograph generation (greyscale drawing → graded) ─────────
function canvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return c; }
function scribbleLine(x, lib, x0, y, len, seed, h = 10) {       // a line of "handwriting": joined loops
  x.beginPath(); x.moveTo(x0, y);
  const n = Math.floor(len / 9);
  for (let i = 1; i <= n; i++) {
    const px = x0 + i * 9, up = (i % 2 ? -1 : 0.35) * h * (0.5 + lib.hash(seed, i));
    x.quadraticCurveTo(px - 4, y + up, px, y + lib.hashS(seed, i, 2) * 2);
    if (lib.hash(seed, i, 3) < 0.08) { x.moveTo(px + 14, y); i += 1; }
  }
  x.stroke();
}
function makeBoard(lib, tokens) {
  const c = canvas(BW, PH), x = c.getContext("2d");
  // wall of vertical boards, drawn soft (it sits behind the focus plane)
  const lw = 700, lh = 338, lc = canvas(lw, lh), lx = lc.getContext("2d"), im = lx.createImageData(lw, lh);
  for (let j = 0; j < lh; j++) for (let i = 0; i < lw; i++) {
    const v = 0.40 + 0.07 * lib.fbm2(i / 4, j / 70, { octaves: 3, seed: 2 }) + 0.05 * lib.fbm2(i / 40, j / 40, { octaves: 2, seed: 3 }), k = (j * lw + i) * 4;
    im.data[k] = im.data[k + 1] = im.data[k + 2] = 255 * v; im.data[k + 3] = 255;
  }
  lx.putImageData(im, 0, 0);
  x.filter = "blur(2.2px)"; x.imageSmoothingQuality = "high"; x.drawImage(lc, 0, 0, BW, PH);
  x.fillStyle = "rgba(0,0,0,0.26)"; for (let bx = 150; bx < BW; bx += 240) x.fillRect(bx, 0, 5, PH);
  x.filter = "none";
  // window light from the top left
  const wl = x.createLinearGradient(0, 0, BW, PH); wl.addColorStop(0, "rgba(255,255,255,0.10)"); wl.addColorStop(1, "rgba(0,0,0,0.18)");
  x.fillStyle = wl; x.fillRect(0, 0, BW, PH);
  const paperAt = (cx, cy, w, h, rot, tone, draw) => {
    x.save(); x.translate(cx, cy); x.rotate(rot * Math.PI / 180);
    x.filter = "blur(10px)"; x.fillStyle = "rgba(0,0,0,0.42)"; x.fillRect(-w / 2 + 12, -h / 2 + 16, w, h); x.filter = "none";
    const g = x.createLinearGradient(-w / 2, -h / 2, w / 2, h / 2); g.addColorStop(0, tone); g.addColorStop(1, lib.mixColor(tone, "#000000", 0.14));
    x.fillStyle = g; x.fillRect(-w / 2, -h / 2, w, h);
    draw(-w / 2, -h / 2, w, h); x.restore();
    x.fillStyle = "#3a3a3a"; x.beginPath(); x.arc(cx, cy - h / 2 + 22, 11, 0, lib.TAU); x.fill();       // pin
    x.fillStyle = "#cfcfcf"; x.beginPath(); x.arc(cx - 3, cy - h / 2 + 18, 3.5, 0, lib.TAU); x.fill();
  };
  // outline page: handwritten lines with bullets, and a signature at the foot
  paperAt(520, 470, 470, 640, -2, "#dcdcd6", (ox, oy, w, h) => {
    x.strokeStyle = "#2a2a2a"; x.lineWidth = 3.2; x.lineCap = "round";
    scribbleLine(x, lib, ox + 50, oy + 90, 250, 1, 16); x.fillStyle = "#2a2a2a"; x.fillRect(ox + 50, oy + 104, 250, 3);
    for (let r = 0; r < 8; r++) { x.beginPath(); x.arc(ox + 58, oy + 170 + r * 46, 5, 0, lib.TAU); x.fill(); scribbleLine(x, lib, ox + 80, oy + 172 + r * 46, 220 + lib.hash(5, r) * 110, 10 + r, 9); }
    x.lineWidth = 3.6; x.beginPath();                                     // the signature: one looping flourish
    const sx = ox + 210, sy = oy + h - 70;
    x.moveTo(sx, sy); x.bezierCurveTo(sx + 20, sy - 70, sx + 50, sy - 60, sx + 40, sy + 4); x.bezierCurveTo(sx + 32, sy + 40, sx + 70, sy - 30, sx + 90, sy - 6);
    x.bezierCurveTo(sx + 110, sy + 18, sx + 120, sy - 40, sx + 150, sy - 8); x.bezierCurveTo(sx + 170, sy + 12, sx + 200, sy - 4, sx + 230, sy - 18); x.stroke();
    x.lineWidth = 2; x.beginPath(); x.moveTo(sx - 10, sy + 22); x.quadraticCurveTo(sx + 110, sy + 34, sx + 240, sy + 14); x.stroke();
  });
  // storyboard sheet: 2 × 3 panels with sketches
  paperAt(1300, 455, 560, 540, 1.2, "#d6d6d0", (ox, oy) => {
    x.strokeStyle = "#333"; x.lineWidth = 3;
    for (let r = 0; r < 2; r++) for (let q = 0; q < 3; q++) {
      const px = ox + 32 + q * 170, py = oy + 50 + r * 230, s = r * 3 + q;
      x.strokeRect(px, py, 154, 170);
      x.lineWidth = 2.4; x.beginPath();
      x.arc(px + 50 + lib.hash(s, 1) * 50, py + 70, 18, 0, lib.TAU);
      x.moveTo(px + 20, py + 140); x.lineTo(px + 130, py + 120 + lib.hashS(s, 2) * 20);
      x.moveTo(px + 60 + lib.hash(s, 1) * 50, py + 88); x.lineTo(px + 58 + lib.hash(s, 1) * 50, py + 132);
      x.stroke(); x.lineWidth = 3;
    }
  });
  // draft: a portrait print (a face worth discovering), white border
  paperAt(2270, 440, 420, 520, -1.5, "#e2e2de", (ox, oy, w, h) => {
    const ix = ox + 26, iy = oy + 26, iw = w - 52, ih = h - 52, cx = ix + iw * 0.5;
    const bg = x.createRadialGradient(ix + iw * 0.3, iy + ih * 0.3, 10, ix + iw * 0.5, iy + ih * 0.5, iw); bg.addColorStop(0, "#b8b8b8"); bg.addColorStop(1, "#4a4a4a");
    x.fillStyle = bg; x.fillRect(ix, iy, iw, ih);
    x.save(); x.beginPath(); x.rect(ix, iy, iw, ih); x.clip();
    x.filter = "blur(2.4px)";                                                                                            // a photograph, not a drawing
    x.fillStyle = "#1e1e1e"; x.beginPath(); x.moveTo(ix - 10, iy + ih); x.bezierCurveTo(ix + 20, iy + ih * 0.66, cx - 40, iy + ih * 0.62, cx, iy + ih * 0.62);   // shoulders / coat
    x.bezierCurveTo(cx + 40, iy + ih * 0.62, ix + iw - 20, iy + ih * 0.66, ix + iw + 10, iy + ih); x.fill();
    x.fillStyle = "#6e6e6e"; x.fillRect(cx - 22, iy + ih * 0.5, 44, ih * 0.14);                                                        // neck
    const face = x.createLinearGradient(cx - 70, 0, cx + 70, 0); face.addColorStop(0, "#d6d6d6"); face.addColorStop(0.5, "#a4a4a4"); face.addColorStop(1, "#4a4a4a");
    x.fillStyle = face; x.beginPath(); x.ellipse(cx, iy + ih * 0.38, 64, 84, 0, 0, lib.TAU); x.fill();                              // side-lit face
    x.fillStyle = "rgba(40,40,40,0.55)"; x.beginPath(); x.ellipse(cx - 24, iy + ih * 0.365, 16, 9, 0, 0, lib.TAU); x.ellipse(cx + 24, iy + ih * 0.365, 16, 9, 0, 0, lib.TAU); x.fill();   // eye sockets
    x.fillStyle = "rgba(60,60,60,0.35)"; x.beginPath(); x.ellipse(cx + 6, iy + ih * 0.44, 9, 16, 0, 0, lib.TAU); x.fill();           // nose shadow
    x.fillStyle = "rgba(50,50,50,0.4)"; x.beginPath(); x.ellipse(cx, iy + ih * 0.495, 20, 5, 0, 0, lib.TAU); x.fill();                // mouth shadow
    x.fillStyle = "#222"; x.beginPath(); x.moveTo(cx - 72, iy + ih * 0.42); x.bezierCurveTo(cx - 84, iy + ih * 0.16, cx + 80, iy + ih * 0.12, cx + 74, iy + ih * 0.4);   // hair
    x.bezierCurveTo(cx + 60, iy + ih * 0.26, cx - 50, iy + ih * 0.22, cx - 72, iy + ih * 0.42); x.fill();
    x.filter = "none";
    x.restore();
  });
  // typed tags under each document (English typed, Chinese in Song)
  [[520, 0], [1300, 1], [2270, 2]].forEach(([cx, k]) => {
    x.save(); x.translate(cx, 0); x.rotate((k - 1) * 0.6 * Math.PI / 180);
    x.fillStyle = "rgba(0,0,0,0.3)"; x.fillRect(-180 + 6, 834, 360, 132);
    x.fillStyle = "#e4e4de"; x.fillRect(-180, 828, 360, 132);
    x.fillStyle = "#262626"; x.textAlign = "center";
    lib.setFont(x, tokens, "mono", 42, { weight: 400 }); x.fillText(lib.MOTIF[k].en.toUpperCase(), 0, 882);
    lib.setFont(x, tokens, "zh", 60, { weight: 400 }); x.fillText(lib.MOTIF[k].zh, 0, 946);
    x.restore();
  });
  return c;
}
function makeLandscape(lib) {
  const c = canvas(LW, PH), x = c.getContext("2d");
  const g = x.createLinearGradient(0, 0, 0, PH); g.addColorStop(0, "#8a8a8a"); g.addColorStop(0.5, "#d2d2d2"); g.addColorStop(0.52, "#6e6e6e"); g.addColorStop(1, "#2c2c2c");
  x.fillStyle = g; x.fillRect(0, 0, LW, PH);
  for (let layer = 0; layer < 3; layer++) {
    x.fillStyle = ["#9c9c9c", "#7a7a7a", "#565656"][layer]; x.beginPath(); x.moveTo(0, PH);
    for (let i = 0; i <= 60; i++) x.lineTo(i * LW / 60, PH * (0.46 + layer * 0.04) - 90 * (1 - layer * 0.3) * (0.5 + 0.5 * lib.fbm2(i / 9, layer, { octaves: 3, seed: 20 + layer })));
    x.lineTo(LW, PH); x.fill();
  }
  x.fillStyle = "#1c1c1c"; x.fillRect(1700, 520, 14, 150);
  x.beginPath(); x.ellipse(1707, 470, 90, 80, 0, 0, lib.TAU); x.fill();
  x.fillRect(1180, 640, 8, 38); x.beginPath(); x.arc(1184, 634, 7, 0, lib.TAU); x.fill();
  return c;
}
function sepia(lib, tokens, src, PW, seed) {       // one warm monochrome + baked grain, vignette, scratches, dust
  const c = canvas(PW, PH), x = c.getContext("2d");
  x.filter = "blur(0.8px)"; x.drawImage(src, 0, 0); x.filter = "none";
  const im = x.getImageData(0, 0, PW, PH), d = im.data, r = lib.rng(seed);
  const lo = lib.rgb(lib.color(tokens, "extra.4")), hi = lib.rgb(lib.color(tokens, "extra.3"));
  for (let j = 0; j < PH; j++) {
    const vy = (j / PH - 0.5) * 2;
    for (let i = 0; i < PW; i++) {
      const k = (j * PW + i) * 4, vx = (i / PW - 0.5) * 2;
      let l = (0.2126 * d[k] + 0.7152 * d[k + 1] + 0.0722 * d[k + 2]) / 255;
      l = l * l * (3 - 2 * l) * 0.85 + l * 0.15;
      l *= 1 - 0.34 * Math.pow(Math.min(1, (vx * vx + vy * vy) / 2), 1.2);
      l = lib.clamp(l + (r() - 0.5) * 0.06);
      d[k] = lo[0] + (hi[0] - lo[0]) * l; d[k + 1] = lo[1] + (hi[1] - lo[1]) * l; d[k + 2] = lo[2] + (hi[2] - lo[2]) * l;
    }
  }
  x.putImageData(im, 0, 0);
  x.strokeStyle = lib.rgba(lib.color(tokens, "extra.3"), 0.35); x.lineWidth = 1.2;
  for (let s = 0; s < 8; s++) { const sx = r() * PW; x.beginPath(); x.moveTo(sx, r() * PH * 0.3); x.lineTo(sx + (r() - 0.5) * 60, PH * (0.5 + r() * 0.5)); x.stroke(); }
  x.fillStyle = lib.rgba(lib.color(tokens, "extra.4"), 0.6);
  for (let s = 0; s < 70; s++) { x.beginPath(); x.arc(r() * PW, r() * PH, 0.8 + r() * 2.2, 0, lib.TAU); x.fill(); }
  return c;
}

// ───────── camera: Catmull–Rom through keys (log zoom); ends extrapolated so it moves at t = 0 ─────────
const KEYS = [   // t, fx, fy, zoom
  [-0.6, 470, 700, 2.55], [0.0, 540, 720, 2.3], [1.0, 800, 690, 1.55], [2.0, 1170, 675, 1.02],
  [2.6, 1400, 690, 1.0], [3.3, 1470, 700, 1.04], [4.0, 1560, 705, 1.12], [4.8, 1640, 705, 1.18], [5.6, 1720, 705, 1.24],
];
function catmull(p0, p1, p2, p3, u) { const u2 = u * u, u3 = u2 * u; return 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3); }
function view(lib, t) {
  let i = 1; while (i < KEYS.length - 3 && t > KEYS[i + 1][0]) i++;
  const [a, b, c, d] = [KEYS[i - 1], KEYS[i], KEYS[i + 1], KEYS[i + 2]], u = lib.clamp((t - b[0]) / (c[0] - b[0]), -0.5, 1.5);
  let fx = catmull(a[1], b[1], c[1], d[1], u), fy = catmull(a[2], b[2], c[2], d[2], u);
  const z = Math.exp(catmull(Math.log(a[3]), Math.log(b[3]), Math.log(c[3]), Math.log(d[3]), u));
  const s = BASE * z, hw = 960 / s, hh = 540 / s;
  fx = lib.clamp(fx, hw, BW - hw); fy = lib.clamp(fy, hh, PH - hh);
  return { fx, fy, s };
}
function drawStill(ctx, img, v) {
  ctx.save(); ctx.imageSmoothingQuality = "high";
  ctx.setTransform(v.s, 0, 0, v.s, 960 - v.fx * v.s, 540 - v.fy * v.s);
  ctx.drawImage(img, 0, 0); ctx.restore();
}
function board(ctx, lib, tokens, t) {
  const v = view(lib, t), blur = 7 * (1 - lib.ease.outCubic(lib.seg(t, 0.05, 0.35)));
  if (blur > 0.05) { ctx.save(); ctx.filter = `blur(${blur.toFixed(2)}px)`; drawStill(ctx, L.board, v); ctx.restore(); }   // focus pull
  else drawStill(ctx, L.board, v);
  // the one faded-red mark: a hand-drawn ring around the face in the portrait, drawn 2.45–2.8 s (photo space)
  const u = lib.ease.inOutSine(lib.seg(t, 2.45, 2.8));
  if (u > 0) {
    ctx.save(); ctx.setTransform(v.s, 0, 0, v.s, 960 - v.fx * v.s, 540 - v.fy * v.s);
    const pts = []; for (let i = 0; i <= 64; i++) { const a = -2.2 + i / 64 * (lib.TAU + 0.5); pts.push([2272 + Math.cos(a) * (122 + 6 * Math.sin(a * 3)), 395 + Math.sin(a) * (150 + 5 * Math.cos(a * 2))]); }
    ctx.strokeStyle = lib.rgba(lib.color(tokens, "accent"), 0.88); ctx.lineWidth = 7; ctx.lineCap = "round";
    lib.strokePartial(ctx, pts, u);
    ctx.restore();
  }
}
function landscape(ctx, lib, t) {             // second still, panning right at the same speed; stays inside the print
  const s = BASE * 1.1, hw = 960 / s, fx = lib.clamp(lib.lerp(1000, 1320, lib.seg(t, 3.6, 5.0)), hw, LW - hw);
  drawStill(ctx, L.land, { fx, fy: 690, s });
}

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  if (t < 4.0) board(ctx, lib, tokens, t);
  else {
    const u = lib.seg(t, 4.0, 4.7);                                         // in-motion dissolve
    landscape(ctx, lib, t);
    if (u < 1) { ctx.save(); ctx.globalAlpha = 1 - lib.ease.inOutSine(u); board(ctx, lib, tokens, t); ctx.restore(); }
  }
  captions(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: 0.05, fps: 24, seed: 6 });
}

function captions(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  // a darkened band under the captions (a print margin in shadow), fades in with the first line
  const ba = lib.ease.inOutSine(lib.seg(t, 0.7, 1.2));
  if (ba > 0) {
    const g = ctx.createLinearGradient(0, 700, 0, H); g.addColorStop(0, "rgba(10,9,8,0)"); g.addColorStop(0.45, "rgba(10,9,8,0.62)"); g.addColorStop(1, "rgba(10,9,8,0.78)");
    ctx.save(); ctx.globalAlpha = ba; ctx.fillStyle = g; ctx.fillRect(0, 700, W, H - 700); ctx.restore();
  }
  const line = (t0, t1, draw) => {
    const a = Math.min(lib.seg(t, t0, t0 + 12 / 30), 1 - lib.seg(t, t1, t1 + 10 / 30));
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C("fg");
    ctx.shadowColor = "rgba(0,0,0,0.5)"; ctx.shadowBlur = 10; ctx.shadowOffsetY = 2;
    draw(); ctx.restore();
  };
  const x = 112;
  line(0.85, 3.2, () => { lib.setFont(ctx, tokens, "body", 32, { weight: 400 }); lib.drawText(ctx, "OPENVIDEOHARNESS · 2026", x, 818, { tracking: 32 * 0.1 }); });
  line(3.2, 3.9, () => { lib.setFont(ctx, tokens, "body", 32, { weight: 400 }); ctx.fillStyle = C("extra.0"); lib.drawText(ctx, "DRAFT · 初版 · FRAME 096", x, 818, { tracking: 32 * 0.1 }); });
  line(1.0, 3.9, () => { lib.setFont(ctx, tokens, "display", 90, { weight: 400 }); lib.drawText(ctx, lib.TITLE_EN, x, 912); });
  line(1.15, 3.9, () => { lib.setFont(ctx, tokens, "zh", 60, { weight: 400 }); lib.drawText(ctx, lib.TITLE_ZH, x, 994, { tracking: 60 * 0.06 }); });
  line(4.45, 99, () => { lib.setFont(ctx, tokens, "body", 34, { weight: 400 }); lib.drawText(ctx, "ARCHIVAL PAN & ZOOM", x, 912, { tracking: 34 * 0.1 }); });
  line(4.6, 99, () => { lib.setFont(ctx, tokens, "zh", 60, { weight: 400 }); lib.drawText(ctx, "档案推拉", x, 994, { tracking: 60 * 0.1 }); });
}

// foley (events.json is generated from this list; times are the same ones the scene uses) — kept sparse
export const FOLEY = [
  { t: 0.1, sfx: "shutter", gain_db: -8, pan: -0.4 },                                                     // the first look
  { t: 2.45, sfx: "air", gain_db: -13, pan: 0.4, dur: 0.7 },                                               // the red ring is drawn
  { t: 4.0, sfx: "shutter", gain_db: -8, pan: 0.2 },                                                      // the dissolve to the next print
];
