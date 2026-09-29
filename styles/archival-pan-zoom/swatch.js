// archival-pan-zoom swatch — slow, purposeful camera moves over still photographs; restrained serif captions.
// Both "photographs" are generated in setup (no downloaded images): a board with three pinned documents and a
// landscape print, drawn in grey, then graded to one warm monochrome with baked grain, vignette, scratches and dust.
//   0.0–0.8  already in motion: a pan across the handwritten outline page, slowly pulling back
//   0.8–2.6  captions fade in lower left, one line at a time (place · date in small caps, the title, the Chinese)
//   2.0–4.0  the pull-back reveals the whole board: outline page → storyboard sheet → draft print, each with a
//            typed tag; the camera keeps panning right and starts a slow push toward the draft; one faded-red
//            circle is drawn around it
//   4.0–5.0  an in-motion dissolve (21 frames) to a second still moving the same way, then the style name
// Camera = focus point + zoom in photo coordinates; every move is already moving at the cut (middle 70 % of the curve).

const PW = 2400, PH = 1350, BASE = 1920 / PW;
let L = null;
export const fonts = ["Baskerville", "Songti SC", "American Typewriter"];

export async function setup(ctx, tokens, lib) {
  const board = makeBoard(lib, tokens), land = makeLandscape(lib);
  L = { board: sepia(lib, tokens, board, 11), land: sepia(lib, tokens, land, 12) };
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
  const c = canvas(PW, PH), x = c.getContext("2d");
  // wall of vertical boards: low-res wood grain, upscaled
  const lw = 600, lh = 338, lc = canvas(lw, lh), lx = lc.getContext("2d"), im = lx.createImageData(lw, lh);
  for (let j = 0; j < lh; j++) for (let i = 0; i < lw; i++) {
    const v = 0.44 + 0.07 * lib.fbm2(i / 4, j / 70, { octaves: 3, seed: 2 }) + 0.04 * lib.fbm2(i / 40, j / 40, { octaves: 2, seed: 3 }), k = (j * lw + i) * 4;
    im.data[k] = im.data[k + 1] = im.data[k + 2] = 255 * v; im.data[k + 3] = 255;
  }
  lx.putImageData(im, 0, 0); x.imageSmoothingQuality = "high"; x.drawImage(lc, 0, 0, PW, PH);
  x.fillStyle = "rgba(0,0,0,0.28)"; for (let bx = 150; bx < PW; bx += 240) x.fillRect(bx, 0, 4, PH);
  const paperAt = (cx, cy, w, h, rot, tone, draw) => {
    x.save(); x.translate(cx, cy); x.rotate(rot * Math.PI / 180);
    x.fillStyle = "rgba(0,0,0,0.35)"; x.fillRect(-w / 2 + 10, -h / 2 + 14, w, h);
    x.fillStyle = tone; x.fillRect(-w / 2, -h / 2, w, h);
    draw(-w / 2, -h / 2, w, h); x.restore();
    x.fillStyle = "#3a3a3a"; x.beginPath(); x.arc(cx, cy - h / 2 + 22, 11, 0, lib.TAU); x.fill();       // pin
    x.fillStyle = "#cfcfcf"; x.beginPath(); x.arc(cx - 3, cy - h / 2 + 18, 3.5, 0, lib.TAU); x.fill();
  };
  // outline page: handwritten lines with bullets
  paperAt(480, 455, 460, 610, -2, "#dcdcd6", (ox, oy, w) => {
    x.strokeStyle = "#2e2e2e"; x.lineWidth = 3.2; x.lineCap = "round";
    scribbleLine(x, lib, ox + 50, oy + 90, 250, 1, 16); x.fillStyle = "#2e2e2e"; x.fillRect(ox + 50, oy + 104, 250, 3);
    for (let r = 0; r < 9; r++) { x.beginPath(); x.arc(ox + 58, oy + 170 + r * 46, 5, 0, lib.TAU); x.fill(); scribbleLine(x, lib, ox + 80, oy + 172 + r * 46, 220 + lib.hash(5, r) * 110, 10 + r, 9); }
  });
  // storyboard sheet: 2 × 3 panels with sketches
  paperAt(1210, 450, 540, 540, 1.2, "#d6d6d0", (ox, oy) => {
    x.strokeStyle = "#333"; x.lineWidth = 3;
    for (let r = 0; r < 2; r++) for (let q = 0; q < 3; q++) {
      const px = ox + 30 + q * 165, py = oy + 50 + r * 230;
      x.strokeRect(px, py, 150, 170);
      x.lineWidth = 2.4; x.beginPath();
      const s = r * 3 + q;
      x.arc(px + 50 + lib.hash(s, 1) * 50, py + 70, 18, 0, lib.TAU);                                  // head
      x.moveTo(px + 20, py + 140); x.lineTo(px + 130, py + 120 + lib.hashS(s, 2) * 20);                // ground
      x.moveTo(px + 60 + lib.hash(s, 1) * 50, py + 88); x.lineTo(px + 58 + lib.hash(s, 1) * 50, py + 132);
      x.stroke(); x.lineWidth = 3;
    }
  });
  // draft print: a small landscape with a white border
  paperAt(1900, 430, 500, 400, -1.5, "#e2e2de", (ox, oy, w, h) => {
    const ix = ox + 26, iy = oy + 26, iw = w - 52, ih = h - 52;
    const g = x.createLinearGradient(0, iy, 0, iy + ih); g.addColorStop(0, "#9a9a9a"); g.addColorStop(0.55, "#c8c8c8"); g.addColorStop(0.56, "#5a5a5a"); g.addColorStop(1, "#3a3a3a");
    x.fillStyle = g; x.fillRect(ix, iy, iw, ih);
    x.fillStyle = "#6a6a6a"; x.beginPath(); x.moveTo(ix, iy + ih * 0.56);
    for (let k = 0; k <= 20; k++) x.lineTo(ix + k * iw / 20, iy + ih * (0.46 + 0.07 * lib.noise1(k * 0.5, 4))); x.lineTo(ix + iw, iy + ih * 0.56); x.fill();
    x.fillStyle = "#222"; x.fillRect(ix + iw * 0.66, iy + ih * 0.44, 5, ih * 0.14); x.beginPath(); x.arc(ix + iw * 0.66 + 2.5, iy + ih * 0.4, 26, 0, lib.TAU); x.fill();
    x.fillRect(ix + iw * 0.3, iy + ih * 0.5, 4, 16); x.beginPath(); x.arc(ix + iw * 0.3 + 2, iy + ih * 0.49, 3.5, 0, lib.TAU); x.fill();
  });
  // typed tags under each document (English typed, Chinese in Song)
  [[480, 0], [1210, 1], [1900, 2]].forEach(([cx, k]) => {
    x.save(); x.translate(cx, 0); x.rotate((k - 1) * 0.6 * Math.PI / 180);
    x.fillStyle = "rgba(0,0,0,0.3)"; x.fillRect(-180 + 6, 818, 360, 132);
    x.fillStyle = "#e4e4de"; x.fillRect(-180, 812, 360, 132);
    x.fillStyle = "#262626"; x.textAlign = "center";
    lib.setFont(x, tokens, "mono", 42, { weight: 400 }); x.fillText(lib.MOTIF[k].en.toUpperCase(), 0, 866);
    lib.setFont(x, tokens, "zh", 58, { weight: 400 }); x.fillText(lib.MOTIF[k].zh, 0, 928);
    x.restore();
  });
  return c;
}
function makeLandscape(lib) {
  const c = canvas(PW, PH), x = c.getContext("2d");
  const g = x.createLinearGradient(0, 0, 0, PH); g.addColorStop(0, "#8a8a8a"); g.addColorStop(0.5, "#d2d2d2"); g.addColorStop(0.52, "#6e6e6e"); g.addColorStop(1, "#2c2c2c");
  x.fillStyle = g; x.fillRect(0, 0, PW, PH);
  for (let layer = 0; layer < 3; layer++) {
    x.fillStyle = ["#9c9c9c", "#7a7a7a", "#565656"][layer]; x.beginPath(); x.moveTo(0, PH);
    for (let i = 0; i <= 60; i++) x.lineTo(i * PW / 60, PH * (0.46 + layer * 0.04) - 90 * (1 - layer * 0.3) * (0.5 + 0.5 * lib.fbm2(i / 9, layer, { octaves: 3, seed: 20 + layer })));
    x.lineTo(PW, PH); x.fill();
  }
  x.fillStyle = "#1c1c1c"; x.fillRect(1700, 520, 14, 150);
  x.beginPath(); x.ellipse(1707, 470, 90, 80, 0, 0, lib.TAU); x.fill();
  x.fillRect(1180, 640, 8, 38); x.beginPath(); x.arc(1184, 634, 7, 0, lib.TAU); x.fill();
  return c;
}
function sepia(lib, tokens, src, seed) {       // one warm monochrome + baked grain, vignette, scratches, dust
  const c = canvas(PW, PH), x = c.getContext("2d");
  x.filter = "blur(0.9px)"; x.drawImage(src, 0, 0); x.filter = "none";      // lens softness: a print, not a vector drawing
  const im = x.getImageData(0, 0, PW, PH), d = im.data, r = lib.rng(seed);
  const lo = lib.rgb(lib.color(tokens, "extra.4")), hi = lib.rgb(lib.color(tokens, "extra.3"));
  for (let j = 0; j < PH; j++) {
    const vy = (j / PH - 0.5) * 2;
    for (let i = 0; i < PW; i++) {
      const k = (j * PW + i) * 4, vx = (i / PW - 0.5) * 2;
      let l = (0.2126 * d[k] + 0.7152 * d[k + 1] + 0.0722 * d[k + 2]) / 255;
      l = l * l * (3 - 2 * l) * 0.85 + l * 0.15;                    // gentle S-curve
      l *= 1 - 0.38 * Math.pow(Math.min(1, (vx * vx + vy * vy) / 2), 1.2);   // print vignette
      l = lib.clamp(l + (r() - 0.5) * 0.05);
      d[k] = lo[0] + (hi[0] - lo[0]) * l; d[k + 1] = lo[1] + (hi[1] - lo[1]) * l; d[k + 2] = lo[2] + (hi[2] - lo[2]) * l;
    }
  }
  x.putImageData(im, 0, 0);
  x.strokeStyle = lib.rgba(lib.color(tokens, "extra.3"), 0.35); x.lineWidth = 1.2;
  for (let s = 0; s < 7; s++) { const sx = r() * PW; x.beginPath(); x.moveTo(sx, r() * PH * 0.3); x.lineTo(sx + (r() - 0.5) * 60, PH * (0.5 + r() * 0.5)); x.stroke(); }
  x.fillStyle = lib.rgba(lib.color(tokens, "extra.4"), 0.6);
  for (let s = 0; s < 60; s++) { x.beginPath(); x.arc(r() * PW, r() * PH, 0.8 + r() * 2.2, 0, lib.TAU); x.fill(); }
  return c;
}

// ───────── camera ─────────
const mid = (lib, u) => 0.15 + 0.7 * lib.ease.inOutSine(lib.clamp(u));      // moving at both cut points
function view(lib, t) {
  const pull = lib.clamp(t / 2.6), push = lib.clamp((t - 2.6) / 1.4);
  const z = t < 2.6 ? 1.0 + 0.26 * Math.pow(1 - lib.ease.inOutSine(pull), 2) : 1.0 + 0.07 * lib.ease.inOutSine(push);
  let fx = lib.lerp(620, 1330, mid(lib, t / 4.7)), fy = lib.lerp(520, 660, mid(lib, t / 3.0));
  const s = BASE * z, hw = 960 / s, hh = 540 / s;
  fx = lib.clamp(fx, hw, PW - hw); fy = lib.clamp(fy, hh, PH - hh);
  return { fx, fy, s };
}
function drawStill(ctx, lib, img, v) {
  ctx.save(); ctx.imageSmoothingQuality = "high";
  ctx.setTransform(v.s, 0, 0, v.s, 960 - v.fx * v.s, 540 - v.fy * v.s);
  ctx.drawImage(img, 0, 0); ctx.restore();
}
function board(ctx, lib, tokens, t) {
  const v = view(lib, t);
  drawStill(ctx, lib, L.board, v);
  // the one faded-red mark: a hand-drawn ring around the draft print, drawn on 2.5–2.9 s (in photo space)
  const u = lib.ease.inOutSine(lib.seg(t, 2.5, 2.9));
  if (u > 0) {
    ctx.save(); ctx.setTransform(v.s, 0, 0, v.s, 960 - v.fx * v.s, 540 - v.fy * v.s);
    const pts = []; for (let i = 0; i <= 64; i++) { const a = -2.2 + i / 64 * (lib.TAU + 0.5); pts.push([1900 + Math.cos(a) * (300 + 8 * Math.sin(a * 3)), 430 + Math.sin(a) * (250 + 6 * Math.cos(a * 2))]); }
    ctx.strokeStyle = lib.rgba(lib.color(tokens, "accent"), 0.85); ctx.lineWidth = 7; ctx.lineCap = "round";
    lib.strokePartial(ctx, pts, u);
    ctx.restore();
  }
}
function landscape(ctx, lib, t) {             // second still, panning right at the same speed
  const s = BASE * 1.08, fx = lib.lerp(1000, 1500, mid(lib, (t - 3.6) / 1.6)), fy = 690;
  drawStill(ctx, lib, L.land, { fx, fy, s });
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
  const C = (k) => lib.color(tokens, k);
  const line = (t0, t1, draw) => {
    const a = Math.min(lib.seg(t, t0, t0 + 12 / 30), 1 - lib.seg(t, t1, t1 + 10 / 30));
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C("fg");
    ctx.shadowColor = "rgba(0,0,0,0.4)"; ctx.shadowBlur = 10; ctx.shadowOffsetY = 2;
    draw(); ctx.restore();
  };
  const x = 112;
  line(0.85, 3.9, () => { lib.setFont(ctx, tokens, "body", 30, { weight: 400 }); lib.drawText(ctx, "OPENVIDEOHARNESS · 2026", x, 842, { tracking: 30 * 0.1 }); });
  line(1.0, 3.9, () => { lib.setFont(ctx, tokens, "display", 66, { weight: 400 }); lib.drawText(ctx, lib.TITLE_EN, x, 922); });
  line(1.15, 3.9, () => { lib.setFont(ctx, tokens, "zh", 52, { weight: 400 }); lib.drawText(ctx, lib.TITLE_ZH, x, 992, { tracking: 52 * 0.06 }); });
  line(4.45, 99, () => { lib.setFont(ctx, tokens, "body", 30, { weight: 400 }); lib.drawText(ctx, "ARCHIVAL PAN & ZOOM", x, 922, { tracking: 30 * 0.1 }); });
  line(4.6, 99, () => { lib.setFont(ctx, tokens, "zh", 52, { weight: 400 }); lib.drawText(ctx, "档案推拉", x, 992, { tracking: 52 * 0.1 }); });
}
