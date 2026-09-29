// dunhuang-mural swatch · 敦煌（盛唐色板）
//   0.00–0.80  earthen wall (plaster, cracks, flaking); red-ochre register lines draw on; the scroll-vine border paints in
//   0.30–2.00  SIGNATURE: two flying ribbons (azurite, cinnabar) sweep in on long S-curves from both sides and converge
//              on the centre axis; each segment trails the head by 35 ms, flowers fall from them
//   0.85–2.55  title: every glyph appears as an ink outline first, then its colour fills in
//   2.00–3.05  motif: one narrative strip at three stages of mural painting: ink sketch → flat colour in three
//              compartments → banded shading (叠晕) and gold
//   4.00–4.75  SIGNATURE TRANSITION: a caisson (藻井) opens from the centre, square inside square, onto the end frame
// The border band scrolls right→left the whole time (横卷). Pure function of t.

export const fonts = ["Optima"];
const LAT = { fonts: { en: { family: ["Optima", "Avenir Next"], weight: 400 } } };
let L = null;

const TAU = Math.PI * 2;
function cloudPath(x, y, s, flip = 1) {        // 云头: a double spiral curl with a tail
  const p = new Path2D();
  p.moveTo(x - 46 * s * flip, y + 26 * s);
  p.bezierCurveTo(x - 50 * s * flip, y - 12 * s, x - 18 * s * flip, y - 34 * s, x + 4 * s * flip, y - 20 * s);
  p.bezierCurveTo(x + 22 * s * flip, y - 42 * s, x + 54 * s * flip, y - 26 * s, x + 48 * s * flip, y + 2 * s);
  p.bezierCurveTo(x + 44 * s * flip, y + 22 * s, x + 18 * s * flip, y + 24 * s, x + 16 * s * flip, y + 8 * s);
  p.bezierCurveTo(x + 14 * s * flip, y - 6 * s, x + 32 * s * flip, y - 8 * s, x + 30 * s * flip, y + 4 * s);
  p.lineTo(x + 8 * s * flip, y + 26 * s);
  p.closePath();
  return p;
}
function lotusPath(x, y, s) {                  // 莲: three petals on a base
  const p = new Path2D();
  const petal = (a, len, w) => {
    const ca = Math.cos(a), sa = Math.sin(a), tx = x + ca * len * s, ty = y + sa * len * s;
    p.moveTo(x, y);
    p.quadraticCurveTo(x + (ca * len * 0.5 - sa * w) * s, y + (sa * len * 0.5 + ca * w) * s, tx, ty);
    p.quadraticCurveTo(x + (ca * len * 0.5 + sa * w) * s, y + (sa * len * 0.5 - ca * w) * s, x, y);
  };
  petal(-Math.PI / 2, 62, 20); petal(-Math.PI / 2 - 0.62, 50, 16); petal(-Math.PI / 2 + 0.62, 50, 16);
  p.moveTo(x - 30 * s, y + 4 * s); p.quadraticCurveTo(x, y + 20 * s, x + 30 * s, y + 4 * s); p.quadraticCurveTo(x, y + 10 * s, x - 30 * s, y + 4 * s);
  return p;
}
function flowerPath(x, y, r, rot) {            // falling flower: four petals
  const p = new Path2D();
  for (let k = 0; k < 4; k++) { const a = rot + k * TAU / 4; p.moveTo(x, y); p.ellipse(x + Math.cos(a) * r * 0.6, y + Math.sin(a) * r * 0.6, r * 0.6, r * 0.32, a, 0, TAU); }
  return p;
}

function buildWall(lib, tokens) {
  const P = (k) => lib.color(tokens, k), W = lib.W, H = lib.H;
  const c = document.createElement("canvas"); c.width = W; c.height = H; const x = c.getContext("2d");
  x.fillStyle = P("bg"); x.fillRect(0, 0, W, H);
  lib.paper(x, { tone: P("bg"), amount: 1, blotch: 0.13, tooth: 0.045, fiber: 0.35, seed: 9 });
  // soot and age toward the top and the corners
  const g = x.createLinearGradient(0, 0, 0, H); g.addColorStop(0, "rgba(74,52,40,0.16)"); g.addColorStop(0.35, "rgba(74,52,40,0)"); g.addColorStop(1, "rgba(74,52,40,0.10)");
  x.fillStyle = g; x.fillRect(0, 0, W, H);
  // hairline cracks: seeded random walks
  const r = lib.rng(21);
  x.lineCap = "round";
  for (let k = 0; k < 26; k++) {
    let px = r() * W, py = r() * H, a = r() * TAU; x.beginPath(); x.moveTo(px, py);
    const n = 8 + Math.floor(r() * 18);
    for (let i = 0; i < n; i++) { a += (r() - 0.5) * 1.1; px += Math.cos(a) * (8 + r() * 16); py += Math.sin(a) * (8 + r() * 16); x.lineTo(px, py); }
    x.strokeStyle = `rgba(59,42,32,${0.18 + r() * 0.22})`; x.lineWidth = 0.8 + r() * 0.9; x.stroke();
  }
  return c;
}
// flaked patches: lighter bare plaster with a dark rim, kept away from text and motif areas
function buildFlakes(lib, keepOut) {
  const w = 960, h = 540, c = document.createElement("canvas"); c.width = w; c.height = h;
  const x = c.getContext("2d"), img = x.createImageData(w, h), D = img.data;
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const X = i * 2, Y = j * 2;
    if (keepOut.some(([x0, y0, x1, y1]) => X > x0 && X < x1 && Y > y0 && Y < y1)) continue;
    const v = lib.fbm2(i / 70, j / 70, { octaves: 5, seed: 33 }) * 0.5 + 0.5, k = (j * w + i) * 4;
    if (v > 0.765) { D[k] = 222; D[k + 1] = 204; D[k + 2] = 168; D[k + 3] = 255; }
    else if (v > 0.752) { D[k] = 120; D[k + 1] = 90; D[k + 2] = 66; D[k + 3] = 170; }
  }
  x.putImageData(img, 0, 0);
  const full = document.createElement("canvas"); full.width = lib.W; full.height = lib.H;
  const f = full.getContext("2d"); f.imageSmoothingQuality = "high"; f.drawImage(c, 0, 0, lib.W, lib.H);
  return full;
}
// scroll-vine (卷草) border tile, Tang: a wavy stem with alternating leaves and buds
function buildVine(lib, tokens) {
  const P = (k) => lib.color(tokens, k), lam = 180, n = 14, h = 110, c = document.createElement("canvas");
  c.width = lam * n; c.height = h; const x = c.getContext("2d");
  x.fillStyle = "#C6A97C"; x.fillRect(0, 0, c.width, h);
  x.lineCap = "round"; x.lineJoin = "round";
  const yc = h / 2, A = 22, ys = (px) => yc + A * Math.sin(px / lam * TAU);
  for (let k = 0; k < n * 2; k++) {                                     // leaves: one per half-wave, alternating sides
    const px = (k + 0.5) * lam / 2, py = ys(px), up = k % 2 ? 1 : -1;
    const leaf = new Path2D();
    leaf.moveTo(px, py);
    leaf.bezierCurveTo(px + 20, py + up * 4, px + 44, py + up * 26, px + 22, py + up * 38);
    leaf.bezierCurveTo(px + 8, py + up * 30, px - 6, py + up * 18, px, py);
    x.fillStyle = P("extra.0"); x.fill(leaf);
    x.save(); x.clip(leaf); x.strokeStyle = "#8FC4AE"; x.lineWidth = 6; x.stroke(leaf); x.restore();   // light edge band (叠晕)
    x.strokeStyle = P("fg"); x.lineWidth = 2; x.stroke(leaf);
    if (k % 2 === 0) { x.fillStyle = P("extra.1"); x.beginPath(); x.arc(px - 16, py - up * 18, 7, 0, TAU); x.fill(); x.lineWidth = 1.5; x.stroke(); }
  }
  x.strokeStyle = P("fg"); x.lineWidth = 3; x.beginPath();
  for (let px = 0; px <= c.width; px += 4) (px ? x.lineTo(px, ys(px)) : x.moveTo(px, ys(px)));
  x.stroke();
  return c;
}
// caisson (藻井) end frame artwork: nested squares, alternately rotated 45°, lotus at the centre
function buildCaisson(lib, tokens, size) {
  const P = (k) => lib.color(tokens, k), c = document.createElement("canvas"); c.width = c.height = size; const x = c.getContext("2d");
  x.translate(size / 2, size / 2);
  const rings = [[size / 2 - 6, 0, P("accent")], [size * 0.36, Math.PI / 4, P("extra.0")], [size * 0.25, 0, P("extra.2")], [size * 0.175, Math.PI / 4, P("accent")]];
  rings.forEach(([hs, rot, col], i) => {
    x.save(); x.rotate(rot);
    x.fillStyle = col; x.fillRect(-hs, -hs, hs * 2, hs * 2);
    x.strokeStyle = i % 2 ? "#8FC4AE" : "#6F9FBE"; x.lineWidth = 10; x.strokeRect(-hs + 12, -hs + 12, hs * 2 - 24, hs * 2 - 24);   // inner band (叠晕)
    x.strokeStyle = P("fg"); x.lineWidth = 3; x.strokeRect(-hs, -hs, hs * 2, hs * 2);
    x.strokeStyle = P("extra.4"); x.lineWidth = 2; x.strokeRect(-hs + 5, -hs + 5, hs * 2 - 10, hs * 2 - 10);                     // gold line
    x.restore();
  });
  x.fillStyle = P("extra.5"); x.beginPath(); x.arc(0, 0, size * 0.12, 0, TAU); x.fill();
  for (let k = 0; k < 8; k++) { x.save(); x.rotate(k * TAU / 8); const lp = lotusPath(0, -size * 0.02, 0.62); x.fillStyle = k % 2 ? P("extra.1") : P("extra.2"); x.fill(lp); x.strokeStyle = P("fg"); x.lineWidth = 1.6; x.stroke(lp); x.restore(); }
  x.fillStyle = P("extra.4"); x.beginPath(); x.arc(0, 0, 14, 0, TAU); x.fill(); x.strokeStyle = P("fg"); x.lineWidth = 2; x.stroke();
  return c;
}

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const panels = [560, 960, 1360].map((cx) => ({ cx, cy: 634, w: 330, h: 196 }));
  L = {
    P, wall: buildWall(lib, tokens), vine: buildVine(lib, tokens), caisson: buildCaisson(lib, tokens, 620), panels,
    flakes: buildFlakes(lib, [[300, 170, 1620, 420], [360, 500, 1560, 880]]),
    enY: 262, zhY: 380, bandTop: 486, bandBot: 884,
  };
}

// ── ribbons: each is a spine curve that unrolls from off-screen toward the centre axis (decelerating), with a curl
//    wave travelling from the head to the tail: segment i repeats the head's motion 35 ms later.
function bez(p, u) { const v = 1 - u; return [0, 1].map((k) => v * v * v * p[0][k] + 3 * v * v * u * p[1][k] + 3 * v * u * u * p[2][k] + u * u * u * p[3][k]); }
const SPINE = { left: [[-160, 300], [420, 560], [160, 60], [880, 104]], right: [[2080, 300], [1500, 560], [1760, 60], [1040, 104]] };
function ribbonPts(t, side, lib) {
  const sp = SPINE[side], head = lib.tween(t, 0.3, 1.5, lib.ease.outCubic), N = 60, pts = [];
  if (head <= 0) return pts;
  for (let i = 0; i <= N; i++) {
    const u = head * (1 - i / N), p = bez(sp, u), q = bez(sp, Math.min(1, u + 0.01)), dx = q[0] - p[0], dy = q[1] - p[1], l = Math.hypot(dx, dy) || 1;
    const lag = i / N * 34 * 0.035;                                         // 34 segments × 35 ms from head to tail
    const amp = 10 + 38 * (i / N);                                          // the free tail flutters most
    const w = amp * Math.sin(lib.TAU * (0.75 * (t - lag) - i / 22)) * Math.min(1, i / 8) + 8 * Math.sin(lib.TAU * (1.3 * (t - lag)) + 1);
    const twist = 0.45 + 0.55 * Math.abs(Math.cos(lib.TAU * (i / 26 - 0.35 * t)));   // the ribbon turns: edge-on → face-on
    pts.push({ x: p[0] - dy / l * w, y: p[1] + dx / l * w, nx: -dy / l, ny: dx / l, wid: (30 * (1 - 0.8 * i / N) + 4) * twist });
  }
  return pts;
}
function drawRibbon(ctx, lib, t, side, col, light) {
  const pts = ribbonPts(t, side, lib);
  if (pts.length < 3) return;
  const poly = (k) => { const p = new Path2D(); pts.forEach((q, i) => (i ? p.lineTo(q.x + q.nx * q.wid / 2 * k, q.y + q.ny * q.wid / 2 * k) : p.moveTo(q.x + q.nx * q.wid / 2 * k, q.y + q.ny * q.wid / 2 * k)));
    for (let i = pts.length - 1; i >= 0; i--) { const q = pts[i]; p.lineTo(q.x - q.nx * q.wid / 2 * k, q.y - q.ny * q.wid / 2 * k); } p.closePath(); return p; };
  const outer = poly(1), inner = poly(0.34);
  ctx.save(); ctx.lineJoin = "round";
  ctx.fillStyle = col; ctx.fill(outer); ctx.fillStyle = light; ctx.fill(inner);
  ctx.strokeStyle = L.P("fg"); ctx.lineWidth = 2; ctx.stroke(outer);
  const h = pts[0], a = Math.atan2(h.ny, h.nx) + Math.PI / 2;               // a cloud-scroll head leads each ribbon
  ctx.translate(h.x, h.y); ctx.rotate(a + (side === "left" ? 0 : Math.PI)); const cp = cloudPath(0, 0, 0.62, side === "left" ? 1 : -1);
  ctx.fillStyle = L.P("extra.5"); ctx.fill(cp); ctx.strokeStyle = L.P("fg"); ctx.lineWidth = 2; ctx.stroke(cp);
  ctx.restore();
}
function flowers(ctx, lib, t) {                                              // 散花: fall along the outer thirds, clear of the title
  const P = L.P, cols = [P("extra.1"), P("extra.0"), P("extra.5"), P("accent")];
  for (let k = 0; k < 16; k++) {
    const side = k % 2 ? "right" : "left", t0 = 0.7 + lib.hash(5, k) * 1.8; if (t < t0) continue;
    const u0 = 0.25 + 0.35 * lib.hash(9, k), p0 = bez(SPINE[side], u0), a = t - t0;
    const x = p0[0] + 26 * Math.sin(1.6 * a + k), y = p0[1] + 30 + a * (46 + 30 * lib.hash(7, k));
    if (y > L.bandTop - 18) continue;
    const pth = flowerPath(x, y, 10 + 5 * lib.hash(8, k), a * 1.4 + k);
    ctx.fillStyle = cols[k % 4]; ctx.fill(pth); ctx.strokeStyle = P("fg"); ctx.lineWidth = 1.2; ctx.stroke(pth);
  }
}

function registers(ctx, t, lib) {
  const P = L.P;
  const u = lib.tween(t, 0.1, 0.65, lib.ease.inOutSine);
  ctx.save(); ctx.strokeStyle = P("extra.2"); ctx.lineCap = "butt";
  for (const y of [L.bandTop, L.bandBot]) {
    ctx.lineWidth = 10; lib.strokePartial(ctx, [[96, y], [lib.W - 96, y]], u);
    ctx.lineWidth = 2; ctx.strokeStyle = P("fg"); lib.strokePartial(ctx, [[96, y - 8], [lib.W - 96, y - 8]], u); ctx.strokeStyle = P("extra.2");
  }
  ctx.restore();
  // border band: the scroll-vine, pigment revealed left→right, then scrolling right→left (横卷)
  const reveal = lib.tween(t, 0.25, 0.9, lib.ease.inOutSine), off = (t * 40) % (L.vine.width / 2);
  ctx.save(); ctx.beginPath(); ctx.rect(96, L.bandBot + 14, (lib.W - 192) * reveal, 110); ctx.clip();
  ctx.drawImage(L.vine, -off, L.bandBot + 14);
  ctx.restore();
}

function titles(ctx, t, tokens, lib) {
  const P = L.P;
  // outline first (0.12 s), then the fill (0.18 s) — per word for Latin, per character for Chinese
  const glyphState = (t0) => ({ outline: lib.clamp((t - t0) / 0.12), fill: lib.clamp((t - t0 - 0.1) / 0.18) });
  lib.setFont(ctx, LAT, "en", 72); ctx.fillStyle = P("fg");
  const en = lib.layoutText(ctx, lib.TITLE_EN, { x: lib.W / 2, y: L.enY, align: "center", tracking: 0.06 * 72 });
  let word = 0;
  const wordOf = en.glyphs.map((g) => { const w = word; if (g.ch === " ") word++; return w; });
  lib.drawGlyphs(ctx, en, (g, i) => {
    const s = glyphState(0.8 + wordOf[i] * 0.2); if (s.outline <= 0) return null;
    return { fill: s.fill > 0 ? lib.rgba(P("fg"), s.fill) : "none", stroke: s.fill < 1 ? lib.rgba(P("fg"), s.outline * (1 - s.fill)) : undefined, lineWidth: 1.5 };
  });
  lib.setFont(ctx, tokens, "zh", 88, { weight: 400 });
  const zh = lib.layoutText(ctx, lib.TITLE_ZH, { x: lib.W / 2, y: L.zhY, align: "center", tracking: 0.12 * 88 });
  lib.drawGlyphs(ctx, zh, (g, i) => {
    const s = glyphState(1.3 + i * 0.13); if (s.outline <= 0) return null;
    return { fill: s.fill > 0 ? lib.rgba(P("fg"), s.fill) : "none", stroke: s.fill < 1 ? lib.rgba(P("fg"), s.outline) : undefined, lineWidth: 2 };
  });
}

// one panel = one strip at a given stage of painting: 0 起稿 ink sketch · 1 平涂 flat colour · 2 叠晕 + 点金
function panel(ctx, t, tokens, lib, k) {
  const P = L.P, pn = L.panels[k], t0 = 2.0 + k * 0.2;
  if (t < t0) return;
  const x0 = pn.cx - pn.w / 2, y0 = pn.cy - pn.h / 2, cw = pn.w / 3;
  const shapes = [cloudPath(x0 + cw * 0.5, pn.cy + 6, 0.9, 1), lotusPath(pn.cx, pn.cy + 36, 1.05), cloudPath(x0 + cw * 2.5, pn.cy + 6, 0.9, -1)];
  const uLine = lib.tween(t, t0, t0 + 0.4, lib.ease.inOutSine);
  const uFill = k >= 1 ? lib.tween(t, t0 + 0.25, t0 + 0.55, lib.ease.inOutSine) : 0;
  const uBand = k === 2 ? lib.tween(t, t0 + 0.35, t0 + 0.55, lib.ease.inOutSine) : 0;
  const uGold = k === 2 ? lib.seg(t, t0 + 0.45, t0 + 0.6) : 0;
  const comp = [P("accent"), P("extra.2"), P("extra.0")], light = ["#5A8BAB", "#B8664A", "#72B096"], pale = ["#86AFC8", "#CF8C70", "#9CCAB5"];
  ctx.save();
  if (uFill > 0) {                                           // flat colour, one compartment per scene of the strip
    ctx.globalAlpha = uFill;
    comp.forEach((c, i) => { ctx.fillStyle = c; ctx.fillRect(x0 + i * cw, y0, cw, pn.h); });
    shapes.forEach((s) => { ctx.fillStyle = P("extra.5"); ctx.fill(s); });
    ctx.globalAlpha = 1;
  }
  if (uBand > 0) {                                           // 叠晕: bands of the same hue, dark at the edge → light inside
    ctx.globalAlpha = uBand;
    comp.forEach((c, i) => {
      ctx.fillStyle = light[i]; ctx.fillRect(x0 + i * cw + 12, y0 + 12, cw - 24, pn.h - 24);
      ctx.fillStyle = pale[i]; ctx.fillRect(x0 + i * cw + 24, y0 + 24, cw - 48, pn.h - 48);
    });
    shapes.forEach((s, i) => { ctx.fillStyle = P("extra.5"); ctx.fill(s); ctx.save(); ctx.clip(s); ctx.strokeStyle = [light[0], "#E8A488", light[2]][i]; ctx.lineWidth = 14; ctx.stroke(s); ctx.restore(); });
    ctx.globalAlpha = 1;
  }
  // ink line (铁线描): frame, compartment dividers, the three shapes — drawn on in painting order
  ctx.strokeStyle = P("fg"); ctx.lineWidth = 2.5; ctx.lineJoin = "round";
  lib.strokePartial(ctx, [[x0, y0], [x0 + pn.w, y0], [x0 + pn.w, y0 + pn.h], [x0, y0 + pn.h], [x0, y0]], uLine);
  if (uLine > 0.5) {
    ctx.globalAlpha = lib.clamp((uLine - 0.5) * 2);
    ctx.beginPath(); ctx.moveTo(x0 + cw, y0); ctx.lineTo(x0 + cw, y0 + pn.h); ctx.moveTo(x0 + 2 * cw, y0); ctx.lineTo(x0 + 2 * cw, y0 + pn.h); ctx.stroke();
    shapes.forEach((s) => ctx.stroke(s));
    ctx.globalAlpha = 1;
  }
  if (uGold > 0) {                                           // 点金: dotted gold border and a gold heart in the lotus
    ctx.fillStyle = P("extra.4");
    const n = Math.floor(uGold * 26 + 1e-9);
    for (let i = 0; i < n; i++) { const u = i / 26; const px = x0 + 8 + (pn.w - 16) * u; ctx.beginPath(); ctx.arc(px, y0 + 8, 3.5, 0, TAU); ctx.arc(px, y0 + pn.h - 8, 3.5, 0, TAU); ctx.fill(); }
    ctx.beginPath(); ctx.arc(pn.cx, pn.cy + 22, 8 * uGold, 0, TAU); ctx.fill();
  }
  // label
  const la = lib.tween(t, t0 + 0.15, t0 + 0.45, lib.ease.outCubic);
  ctx.globalAlpha = la; ctx.textAlign = "center"; ctx.fillStyle = P("fg");
  lib.setFont(ctx, tokens, "zh", 50, { weight: 400 }); ctx.fillText(lib.MOTIF[k].zh, pn.cx, pn.cy + pn.h / 2 + 76);
  lib.setFont(ctx, LAT, "en", 28); ctx.fillStyle = P("extra.6"); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), pn.cx, pn.cy + pn.h / 2 + 120, { align: "center", tracking: 4 });
  ctx.restore();
}

function scene(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.drawImage(L.wall, 0, 0);
  registers(ctx, t, lib);
  drawRibbon(ctx, lib, t, "left", P("accent"), "#6F9FBE");
  drawRibbon(ctx, lib, t, "right", P("extra.1"), "#D98A6E");
  flowers(ctx, lib, t);
  titles(ctx, t, tokens, lib);
  for (let k = 0; k < 3; k++) panel(ctx, t, tokens, lib, k);
  ctx.save(); ctx.globalAlpha = 0.9; ctx.drawImage(L.flakes, 0, 0); ctx.restore();   // time: flaked plaster over everything
}

function endFrame(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.drawImage(L.wall, 0, 0);
  const s = L.caisson.width;
  ctx.drawImage(L.caisson, (lib.W - s) / 2, (lib.H - s) / 2 - 40);
  ctx.textAlign = "center"; ctx.fillStyle = P("fg");
  lib.setFont(ctx, tokens, "zh", 50, { weight: 400 }); ctx.fillText("敦煌", lib.W / 2, lib.H / 2 + s / 2 + 34);
  ctx.save(); ctx.globalAlpha = 0.9; ctx.drawImage(L.flakes, 0, 0); ctx.restore();
}

export function renderAt(t, ctx, tokens, lib) {
  if (t < 4.0) { scene(ctx, t, tokens, lib); return; }
  // caisson iris: B opens inside a square (rotated 45°), its edge framed by three nested borders
  const P = L.P, u = lib.tween(t, 4.0, 4.75, lib.ease.inOutCubic), cx = lib.W / 2, cy = lib.H / 2 - 40;
  const hs = u * 1600, rot = Math.PI / 4 * (1 - u);
  scene(ctx, t, tokens, lib);
  if (hs < 1) return;
  const B = lib.offscreen("dh_B", (x) => endFrame(x, t, tokens, lib));
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(rot);
  ctx.beginPath(); ctx.rect(-hs, -hs, hs * 2, hs * 2); ctx.save(); ctx.clip();
  ctx.rotate(-rot); ctx.translate(-cx, -cy); ctx.drawImage(B, 0, 0); ctx.restore();
  [[0, P("extra.2"), 14], [16, P("extra.0"), 10], [28, P("extra.4"), 4], [36, P("fg"), 2]].forEach(([o, c, w]) => { ctx.strokeStyle = c; ctx.lineWidth = w; ctx.strokeRect(-hs - o, -hs - o, (hs + o) * 2, (hs + o) * 2); });
  ctx.restore();
}
