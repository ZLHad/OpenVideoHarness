// shadow-puppet swatch · 皮影
// Image model: frame = lampLight(x, y, t) × transmission(x, y). Every puppet piece is a dyed, carved, translucent hide
// sprite multiplied onto a white cloth; carved holes stay white (brightest), overlapping pieces darken.
//   0.00–0.80  a match flares behind the cloth, the oil lamp catches (overshoot, then a living flicker)
//   0.35–1.20  SIGNATURE: a jointed puppet presses onto the cloth from big and blurry to sharp, glides and stops —
//              its legs and hat tassel keep swinging (damped pendulums, closed form)
//   0.80–1.33  title: a dark hide plaque with the words cut out presses on; it hangs from a pin and swings to rest
//   2.00–2.80  motif: three carved cards on rods press on at 2.0 / 2.2 / 2.4 as the puppet points at each
//              (hollow outline frame → three coloured panes → a densely carved, fully dyed medallion)
//   4.00–4.80  SIGNATURE TRANSITION: the lamp gutters out and relights on the puppet alone, in its closing pose

export const fonts = ["Baskerville", "Libian SC"];
const LAT = { fonts: { en: { family: ["Baskerville", "Georgia"], weight: 600 }, zh: { family: ["Libian SC", "Kaiti SC"], weight: 400 } } };
const TAU = Math.PI * 2;
let L = null;

// ───────── carving toolkit (setup only)
function pip(pts, x, y) { let c = false; for (let i = 0, j = pts.length - 1; i < pts.length; j = i++) { const [xi, yi] = pts[i], [xj, yj] = pts[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; }
function pathOf(pts) { const p = new Path2D(); pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); return p; }
function scaledPts(pts, k, [cx, cy]) { return pts.map(([x, y]) => [cx + (x - cx) * k, cy + (y - cy) * k]); }
const HOLES = {
  crescent: (p, x, y, r) => { p.moveTo(x + r * Math.cos(0.3), y + r * Math.sin(0.3)); p.arc(x, y, r, 0.3, Math.PI - 0.3); p.arc(x, y - r * 0.55, r * 0.9, Math.PI - 0.45, 0.45, true); p.closePath(); },
  diamond: (p, x, y, r) => { p.moveTo(x, y - r); p.lineTo(x + r * 0.7, y); p.lineTo(x, y + r); p.lineTo(x - r * 0.7, y); p.closePath(); },
  coin: (p, x, y, r) => { p.moveTo(x + r, y); p.arc(x, y, r, 0, TAU); p.moveTo(x - r * 0.38, y - r * 0.38); p.lineTo(x - r * 0.38, y + r * 0.38); p.lineTo(x + r * 0.38, y + r * 0.38); p.lineTo(x + r * 0.38, y - r * 0.38); p.closePath(); },
  petal: (p, x, y, r, a = 0) => { p.moveTo(x, y); p.ellipse(x + Math.cos(a) * r, y + Math.sin(a) * r, r, r * 0.42, a, 0, TAU); },
};
function hideTexture(lib) {
  const s = 256, c = document.createElement("canvas"); c.width = c.height = s; const x = c.getContext("2d"), img = x.createImageData(s, s);
  for (let j = 0; j < s; j++) for (let i = 0; i < s; i++) {
    const v = 0.86 + 0.14 * (lib.fbm2(i / 22, j / 22, { octaves: 3, seed: 5 }) * 0.5 + 0.5) + 0.05 * lib.hashS(i, j, 7), k = (j * s + i) * 4;
    img.data[k] = img.data[k + 1] = img.data[k + 2] = Math.round(Math.min(1, v) * 255); img.data[k + 3] = 255;
  }
  x.putImageData(img, 0, 0); return c;
}
// piece: {shape: pts (local, pivot at 0,0), color, holes: [{kind, region: pts, cell, r}], extra(ctx)} → sprite
function makePiece(lib, tex, spec) {
  const xs = spec.shape.map((p) => p[0]), ys = spec.shape.map((p) => p[1]), pad = 6;
  const x0 = Math.floor(Math.min(...xs)) - pad, y0 = Math.floor(Math.min(...ys)) - pad, w = Math.ceil(Math.max(...xs)) + pad - x0, h = Math.ceil(Math.max(...ys)) + pad - y0;
  const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d");
  x.translate(-x0, -y0);
  const body = pathOf(spec.shape);
  x.fillStyle = spec.color; x.fill(body);
  if (spec.paint) spec.paint(x);
  x.save(); x.clip(body); x.globalCompositeOperation = "multiply"; x.drawImage(tex, x0, y0, Math.max(w, 256), Math.max(h, 256)); x.restore();
  x.strokeStyle = "#1C120B"; x.lineWidth = 2.6; x.stroke(body);
  const holes = new Path2D();
  for (const hs of spec.holes || []) {
    const rx = hs.region.map((p) => p[0]), ry = hs.region.map((p) => p[1]);
    const hp = new Path2D();
    for (let yy = Math.min(...ry) + hs.cell / 2, row = 0; yy < Math.max(...ry); yy += hs.cell, row++)
      for (let xx = Math.min(...rx) + hs.cell / 2 + (row % 2 ? hs.cell / 2 : 0); xx < Math.max(...rx); xx += hs.cell)
        if (pip(hs.region, xx, yy) && pip(hs.region, xx + hs.r, yy) && pip(hs.region, xx - hs.r, yy) && pip(hs.region, xx, yy - hs.r) && pip(hs.region, xx, yy + hs.r)) HOLES[hs.kind](hp, xx, yy, hs.r);
    holes.addPath(hp);
  }
  if (spec.cut) spec.cut(holes);
  x.lineWidth = 2; x.stroke(holes);
  x.globalCompositeOperation = "destination-out"; x.fillStyle = "#000"; x.fill(holes, "evenodd");
  if (spec.after) { x.globalCompositeOperation = "source-over"; spec.after(x); }
  return { c, x0, y0 };
}
function plaque(lib, tex, w, h, lines, tokens) {
  const c = document.createElement("canvas"); c.width = w; c.height = h; const x = c.getContext("2d");
  x.fillStyle = "#3B2414"; x.fillRect(0, 0, w, h);
  x.globalCompositeOperation = "multiply"; x.drawImage(tex, 0, 0, w, h); x.globalCompositeOperation = "source-over";
  x.strokeStyle = "#B8261B"; x.lineWidth = 14; x.strokeRect(10, 10, w - 20, h - 20);                       // red border band…
  x.strokeStyle = "#1C120B"; x.lineWidth = 2; x.strokeRect(3, 3, w - 6, h - 6); x.strokeRect(18, 18, w - 36, h - 36);
  x.globalCompositeOperation = "destination-out"; x.fillStyle = "#000";
  const hp = new Path2D(); for (let u = 36; u < w - 30; u += 26) { HOLES.diamond(hp, u, 10, 4); HOLES.diamond(hp, u, h - 10, 4); } for (let v = 36; v < h - 30; v += 26) { HOLES.diamond(hp, 10, v, 4); HOLES.diamond(hp, w - 10, v, 4); }
  x.fill(hp);                                                                                               // …with carved diamonds
  x.textAlign = "center"; x.textBaseline = "alphabetic";
  for (const ln of lines) { lib.setFont(x, LAT, ln.role, ln.size, ln.opts || {}); lib.drawText(x, ln.text, w / 2, ln.y, { align: "center", tracking: ln.tr || 0 }); }
  return c;
}

// ───────── the puppet (faces right). Body coords: hip at (0,0), y down.
function buildPuppet(lib, tex) {
  const V = "#B8261B", G = "#2F7A45", Y = "#D9A02B", B = "#245E7A", HIDE = "#D8B07A", K = "#1C120B";
  const torso = [[8, -152], [40, -140], [50, -84], [42, -8], [-40, -8], [-34, -90], [-30, -140]];
  const skirt = [[-40, -12], [42, -12], [74, 150], [-70, 150]];
  const face = [[-22, 0], [-30, -40], [-26, -78], [8, -92], [26, -74], [30, -58], [42, -48], [30, -41], [34, -31], [26, -23], [29, -12], [14, -2]];
  const hat = [[-36, -70], [-30, -96], [-8, -126], [14, -118], [34, -80], [30, -72], [-4, -86]];
  const upper = [[-15, -8], [15, -8], [17, 78], [-17, 78]];
  const fore = [[-14, -6], [14, -6], [12, 70], [20, 84], [10, 98], [-8, 94], [-12, 70]];
  const leg = [[-14, 0], [14, 0], [16, 62], [44, 68], [44, 86], [-18, 86]];
  const tassel = [[-4, 0], [4, 0], [10, 58], [0, 70], [-10, 58]];
  const P = {
    skirt: makePiece(lib, tex, { shape: skirt, color: G, holes: [{ kind: "diamond", region: [[-30, 10], [36, 10], [62, 128], [-58, 128]], cell: 22, r: 7 }],
      after: (x) => { x.fillStyle = Y; x.fillRect(-72, 132, 148, 16); } }),
    torso: makePiece(lib, tex, { shape: torso, color: V, holes: [{ kind: "crescent", region: [[0, -136], [36, -128], [42, -84], [34, -26], [-30, -26], [-26, -126]], cell: 18, r: 7 }],
      paint: (x) => { x.fillStyle = Y; x.fillRect(-42, -30, 86, 22); } }),
    head: makePiece(lib, tex, { shape: face, color: HIDE, cut: (h) => h.addPath(pathOf(scaledPts(face, 0.72, [6, -44]))),   // open-cut face: only the contour, brow and eye strips remain
      after: (x) => { x.strokeStyle = K; x.lineWidth = 5; x.lineCap = "round";
        x.beginPath(); x.moveTo(4, -62); x.quadraticCurveTo(16, -68, 28, -60); x.stroke();                          // brow strip
        x.fillStyle = K; x.beginPath(); x.ellipse(18, -52, 9, 3.4, -0.12, 0, TAU); x.fill();                        // eye strip
        x.lineWidth = 3; x.beginPath(); x.moveTo(-2, -20); x.quadraticCurveTo(10, -12, 22, -16); x.stroke(); } }),
    hat: makePiece(lib, tex, { shape: hat, color: K, holes: [{ kind: "coin", region: [[-26, -94], [-8, -118], [10, -110], [26, -82], [-4, -90]], cell: 16, r: 6 }],
      after: (x) => { x.fillStyle = Y; x.beginPath(); x.moveTo(-36, -70); x.lineTo(34, -80); x.lineTo(33, -72); x.lineTo(-34, -63); x.closePath(); x.fill(); } }),
    tassel: makePiece(lib, tex, { shape: tassel, color: V, holes: [{ kind: "diamond", region: [[-6, 12], [6, 12], [8, 52], [-8, 52]], cell: 12, r: 4 }] }),
    upperN: makePiece(lib, tex, { shape: upper, color: Y, holes: [{ kind: "petal", region: [[-11, 4], [11, 4], [12, 68], [-12, 68]], cell: 20, r: 5 }] }),
    foreN: makePiece(lib, tex, { shape: fore, color: Y, holes: [{ kind: "diamond", region: [[-10, 4], [10, 4], [9, 62], [-9, 62]], cell: 16, r: 5 }],
      after: (x) => { x.fillStyle = HIDE; x.beginPath(); x.moveTo(-10, 70); x.lineTo(12, 70); x.lineTo(20, 84); x.lineTo(10, 98); x.lineTo(-8, 94); x.closePath(); x.fill(); x.strokeStyle = K; x.lineWidth = 2; x.stroke(); } }),
    upperF: makePiece(lib, tex, { shape: upper, color: "#B9861F", holes: [] }),
    foreF: makePiece(lib, tex, { shape: fore, color: "#B9861F", holes: [] }),
    leg: makePiece(lib, tex, { shape: leg, color: B, holes: [{ kind: "diamond", region: [[-10, 4], [10, 4], [11, 40], [-11, 40]], cell: 14, r: 5 }],
      after: (x) => { x.fillStyle = K; x.beginPath(); x.moveTo(-17, 44); x.lineTo(16, 44); x.lineTo(16, 62); x.lineTo(44, 68); x.lineTo(44, 78); x.lineTo(-18, 78); x.closePath(); x.fill();
        x.fillStyle = "#F1E4C8"; x.fillRect(-18, 78, 62, 8); } }),                                                                     // boot + white sole
  };
  return P;
}
function drawSprite(x, sp, tf) {       // tf: DOMMatrix for the pivot
  x.save(); x.setTransform(tf); x.drawImage(sp.c, sp.x0, sp.y0); x.restore();
}
const pend = (d, amp, w = 7.5, z = 0.22) => d <= 0 ? 0 : amp * Math.exp(-z * w * d) * Math.cos(w * Math.sqrt(1 - z * z) * d);

// pose at time t for the scene ("main") or the end frame ("end")
function pose(t, lib, mode) {
  const tr = (k, a = 0.018) => a * lib.noise1(t * 1.3 + k * 7.1, 40 + k);               // hand tremor
  if (mode === "end") {
    const d = t - 4.4;
    return { x: 900 + tr(1, 3), y: 590 + tr(2, 3), s: 1.4, blur: 0, rot: -0.04 + tr(3),
      shN: 2.35 + tr(4) + pend(d, 0.12, 9), elN: -0.5 + pend(d, 0.2, 10), shF: 1.75 + tr(5) + pend(d, 0.1, 8), elF: -0.4,
      legA: 0.16 + pend(d, 0.1), legB: -0.12 + pend(d - 0.05, -0.1), tassel: pend(d, 0.5, 7), head: -0.12 };
  }
  const press = lib.tween(t, 0.35, 0.88, lib.ease.outCubic);
  const glide = lib.tween(t, 0.88, 1.2, lib.ease.inOutCubic);
  // pointing at the three cards (2.0 → 2.25 → 2.5), then easing back
  const aim = lib.springTrack(t, [{ t: 0, v: 0.25 }, { t: 1.9, v: 1.38 }, { t: 2.1, v: 1.48 }, { t: 2.3, v: 1.6 }, { t: 3.3, v: 0.95 }], { w: 11, zeta: 0.75 });
  const lean = 0.06 * lib.tween(t, 1.9, 2.2, lib.ease.outCubic) * (1 - lib.tween(t, 3.3, 3.7, lib.ease.inOutCubic));
  const kick = (tk) => pend(t - tk, 1, 8, 0.25);
  const swing = 0.3 * kick(1.2) + 0.08 * (kick(2.1) + kick(2.3) + kick(3.6));
  return { x: 320 + 60 * glide + tr(1, 3), y: 610 + tr(2, 2.5), s: 1.3 * (1.8 - 0.8 * press), blur: 24 * (1 - press), rot: lean + tr(3),
    shN: aim + tr(4), elN: -0.25 + 0.12 * Math.sin(aim), shF: 0.35 + swing * 0.6 + tr(5), elF: 0.1 + swing * 0.4,
    legA: 0.1 + swing, legB: -0.06 + 0.8 * swing + 0.06 * kick(1.28), tassel: 0.7 * kick(1.2) + 0.3 * (kick(2.1) + kick(2.3)) + 0.1 * Math.sin(1.7 * t), head: 0.05 * Math.sin(0.8 * t) };
}
function drawPuppet(T, lib, p) {
  const Pp = L.pup, M = (m) => m;
  const base = new DOMMatrix().translate(p.x, p.y).scale(p.s).rotate(p.rot * 180 / Math.PI);
  const at = (m, x, y, a) => m.translate(x, y).rotate(a * 180 / Math.PI);
  const arm = (sh, el, up, fo, sx) => { const m1 = at(new DOMMatrix(base.toString()), sx, -130, -sh); drawSprite(T, up, m1); drawSprite(T, fo, at(m1, 0, 74, -el)); return at(m1, 0, 74, -el).translate(8, 92); };
  T.save(); if (p.blur > 0.3) T.filter = `blur(${p.blur.toFixed(2)}px)`;
  const handF = arm(p.shF, p.elF, Pp.upperF, Pp.foreF, 2);                                   // far arm behind
  drawSprite(T, Pp.leg, at(base, -12, 100, p.legB));
  drawSprite(T, Pp.leg, at(base, 10, 100, p.legA));
  drawSprite(T, Pp.skirt, base);
  drawSprite(T, Pp.torso, base);
  const head = at(new DOMMatrix(base.toString()), 8, -152, p.head);
  drawSprite(T, Pp.tassel, at(new DOMMatrix(head.toString()), -30, -96, p.tassel));
  drawSprite(T, Pp.head, head); drawSprite(T, Pp.hat, head);
  const handN = arm(p.shN, p.elN, Pp.upperN, Pp.foreN, 18);                                 // near arm in front
  T.restore();
  return { neck: head.transformPoint(new DOMPoint(14, 4)), hands: [handN.transformPoint(new DOMPoint(0, 0)), handF.transformPoint(new DOMPoint(0, 0))] };
}
function rods(T, pts, bottom, blur = 0) {
  T.save(); T.strokeStyle = "rgba(70,55,40,0.55)"; T.lineWidth = 3.2; T.lineCap = "round"; T.filter = `blur(${1.6 + blur}px)`;
  for (const q of pts) { T.beginPath(); T.moveTo(q.x, q.y); T.lineTo(q.x + (q.x - 960) * 0.08, bottom + 20); T.stroke(); }
  T.restore();
}

// ───────── motif cards: hollow outline → three panes → fully carved and dyed
function buildCards(lib, tex, tokens) {
  const w = 220, h = 176, frame = [[-w / 2, -h], [w / 2, -h], [w / 2, 0], [-w / 2, 0]];
  const inner = (m) => [[-w / 2 + m, -h + m], [w / 2 - m, -h + m], [w / 2 - m, -m], [-w / 2 + m, -m]];
  const outline = makePiece(lib, tex, { shape: frame, color: "#D8B07A", holes: [{ kind: "coin", region: [[-w / 2 + 2, -h + 2], [w / 2 - 2, -h + 2], [w / 2 - 2, -h + 16], [-w / 2 + 2, -h + 16]], cell: 18, r: 5 }],
    cut: (hp) => hp.addPath(pathOf(inner(16))) });
  const panes = makePiece(lib, tex, { shape: frame, color: "#D8B07A", cut: (hp) => { for (let i = 0; i < 3; i++) { const cw = (w - 32 - 16) / 3, x0 = -w / 2 + 16 + i * (cw + 8); hp.addPath(pathOf([[x0, -h + 16], [x0 + cw, -h + 16], [x0 + cw, -16], [x0, -16]])); } },
    after: (x) => { const cols = ["#245E7A", "#2F7A45", "#D9A02B"]; for (let i = 0; i < 3; i++) { const cw = (w - 32 - 16) / 3, x0 = -w / 2 + 16 + i * (cw + 8);
      x.fillStyle = cols[i]; x.globalAlpha = 0.9; x.fillRect(x0, -h + 16, cw, h - 32); x.globalAlpha = 1;
      x.save(); x.globalCompositeOperation = "destination-out"; const hp = new Path2D(); for (let yy = -h + 32; yy < -24; yy += 22) for (let xx = x0 + 12; xx < x0 + cw - 6; xx += 20) HOLES.diamond(hp, xx, yy, 5); x.fill(hp); x.restore();
      x.strokeStyle = "#1C120B"; x.lineWidth = 2; x.strokeRect(x0, -h + 16, cw, h - 32); } } });
  const full = makePiece(lib, tex, { shape: frame, color: "#2F7A45", holes: [{ kind: "crescent", region: inner(8), cell: 20, r: 7 }],
    after: (x) => {
      x.fillStyle = "#B8261B"; x.beginPath(); x.arc(0, -h / 2, 62, 0, TAU); x.fill(); x.strokeStyle = "#1C120B"; x.lineWidth = 2.4; x.stroke();
      x.fillStyle = "#D9A02B"; x.beginPath(); x.arc(0, -h / 2, 24, 0, TAU); x.fill(); x.stroke();
      x.save(); x.globalCompositeOperation = "destination-out"; const hp = new Path2D();
      for (let k = 0; k < 10; k++) HOLES.petal(hp, 0, -h / 2, 20, k * TAU / 10); for (let k = 0; k < 10; k++) { const a = (k + 0.5) * TAU / 10; HOLES.coin(hp, Math.cos(a) * 46, -h / 2 + Math.sin(a) * 46, 6); }
      HOLES.coin(hp, 0, -h / 2, 9); x.fill(hp, "evenodd"); x.restore(); } });
  const tag = (k) => plaque(lib, tex, 250, 110, [{ role: "zh", size: 52, text: lib.MOTIF[k].zh, y: 58, tr: 6 }, { role: "en", size: 24, text: lib.MOTIF[k].en.toUpperCase(), y: 92, tr: 1 }], tokens);
  return [outline, panes, full].map((pc, k) => ({ pc, tag: tag(k) }));
}

export async function setup(ctx, tokens, lib) {
  const tex = hideTexture(lib);
  // cloth: near-white weave with low-frequency density, used as the transmission base
  const cloth = document.createElement("canvas"); cloth.width = lib.W; cloth.height = lib.H;
  const cx = cloth.getContext("2d"); lib.paper(cx, { tone: "#F6EEE0", amount: 1, blotch: 0.05, tooth: 0.05, fiber: 0.2, seed: 12 });
  const weave = document.createElement("canvas"); weave.width = weave.height = 8; const wx = weave.getContext("2d");
  wx.fillStyle = "#fff"; wx.fillRect(0, 0, 8, 8); wx.fillStyle = "rgba(120,100,80,0.18)"; wx.fillRect(0, 0, 8, 1); wx.fillRect(0, 4, 8, 1); wx.fillRect(0, 0, 1, 8); wx.fillRect(4, 0, 1, 8);
  cx.globalCompositeOperation = "multiply"; cx.fillStyle = cx.createPattern(weave, "repeat"); cx.fillRect(0, 0, lib.W, lib.H);
  L = {
    tex, cloth, pup: buildPuppet(lib, tex), cards: buildCards(lib, tex, tokens),
    title: plaque(lib, tex, 1120, 250, [{ role: "en", size: 66, text: lib.TITLE_EN, y: 104, tr: 2 }, { role: "zh", size: 92, text: lib.TITLE_ZH, y: 208, tr: 10 }], tokens),
    screen: { x0: 110, y0: 70, x1: 1810, y1: 930 }, cardX: [900, 1220, 1540], cardY: 760,
  };
}

// lamp intensity: match flare, catch with overshoot, then a living flicker; gutter and relight for the transition
function lamp(t, lib) {
  const fl = 1 + 0.06 * lib.noise1(t * 7, 3) + 0.02 * Math.sin(TAU * 23 * t);
  if (t < 4.0) {
    const on = t < 0.12 ? 0.03 : 0.03 + 0.97 * lib.spring(t - 0.12, { w: 9, zeta: 0.55 });
    return Math.max(0.03, on * fl);
  }
  if (t < 4.28) { const u = lib.seg(t, 4.0, 4.28); return Math.max(0.02, (1 - u) * (1 + 0.45 * lib.hashS(9, lib.frame(t)))); }   // gutters: fast flicker down
  if (t < 4.42) return 0.02;
  return 0.02 + 0.98 * lib.spring(t - 4.42, { w: 12, zeta: 0.5 }) * fl;                                                    // relights with overshoot
}
function lampField(ctx, lib, I) {
  const S = L.screen;
  ctx.fillStyle = "#24140A"; ctx.fillRect(0, 0, lib.W, lib.H);
  ctx.save(); ctx.globalCompositeOperation = "lighter";
  const g = ctx.createRadialGradient(960, 360, 0, 960, 420, 1250);
  const a = (v) => Math.max(0, Math.min(1, v * I));
  g.addColorStop(0, `rgba(255,222,165,${a(1)})`); g.addColorStop(0.35, `rgba(245,196,125,${a(0.9)})`); g.addColorStop(0.75, `rgba(190,120,60,${a(0.6)})`); g.addColorStop(1, `rgba(110,62,28,${a(0.4)})`);
  ctx.fillStyle = g; ctx.fillRect(S.x0, S.y0, S.x1 - S.x0, S.y1 - S.y0);
  const hsp = ctx.createRadialGradient(960, 330, 0, 960, 330, 240); hsp.addColorStop(0, `rgba(255,236,200,${a(0.35)})`); hsp.addColorStop(1, "rgba(255,236,200,0)");
  ctx.fillStyle = hsp; ctx.fillRect(S.x0, S.y0, S.x1 - S.x0, S.y1 - S.y0);
  ctx.restore();
}
function stageFrame(ctx, lib) {
  const S = L.screen;
  ctx.save(); ctx.fillStyle = "#1A0F08";
  ctx.fillRect(0, 0, lib.W, S.y0); ctx.fillRect(0, S.y1, lib.W, lib.H - S.y1); ctx.fillRect(0, 0, S.x0, lib.H); ctx.fillRect(S.x1, 0, lib.W - S.x1, lib.H);
  ctx.strokeStyle = "#6E1A12"; ctx.lineWidth = 12; ctx.strokeRect(S.x0 - 8, S.y0 - 8, S.x1 - S.x0 + 16, S.y1 - S.y0 + 16);
  ctx.strokeStyle = "#A8812F"; ctx.lineWidth = 2; ctx.strokeRect(S.x0 - 16, S.y0 - 16, S.x1 - S.x0 + 32, S.y1 - S.y0 + 32);
  ctx.restore();
}

function pressState(t, t0, dur = 0.53) { const u = lib_tw(t, t0, t0 + dur); return { s: 1.8 - 0.8 * u, blur: 24 * (1 - u), on: t >= t0 }; }
let lib_tw = null;

function transmission(lib, t, tokens, mode) {
  const T = lib.layer("sp_T");
  T.drawImage(L.cloth, 0, 0);
  T.globalCompositeOperation = "multiply";
  if (mode === "main") {
    // title plaque: pinned at its top centre, presses on, then swings to rest
    const ps = pressState(t, 0.8);
    if (ps.on) {
      const sw = 0.035 * Math.exp(-2.2 * Math.max(0, t - 1.38)) * Math.sin(8 * Math.max(0, t - 1.38)) + 0.004 * lib.noise1(t, 11);
      T.save(); if (ps.blur > 0.3) T.filter = `blur(${ps.blur.toFixed(2)}px)`;
      T.setTransform(new DOMMatrix().translate(1010, 104).scale(ps.s).rotate(sw * 180 / Math.PI));
      T.drawImage(L.title, -L.title.width / 2, 0); T.restore();
    }
    // cards on rods, pressing on as the puppet points
    const rodPts = [];
    L.cards.forEach((cd, k) => {
      const t0 = 2.0 + k * 0.2, st = pressState(t, t0, 0.4); if (!st.on) return;
      const sw = 0.09 * Math.exp(-2.6 * Math.max(0, t - t0 - 0.4)) * Math.sin(9 * Math.max(0, t - t0 - 0.4)) + 0.006 * lib.noise1(t * 1.2, 20 + k);
      const m = new DOMMatrix().translate(L.cardX[k], L.cardY - 40).scale(st.s).rotate(sw * 180 / Math.PI);
      T.save(); if (st.blur > 0.3) T.filter = `blur(${st.blur.toFixed(2)}px)`;
      drawSprite(T, cd.pc, m);
      T.setTransform(m.translate(0, 20)); T.drawImage(cd.tag, -cd.tag.width / 2, 0); T.restore();
      rodPts.push(m.transformPoint(new DOMPoint(0, 128)));
    });
    const p = pose(t, lib, "main"); const an = drawPuppet(T, lib, p);
    rods(T, [an.neck, ...an.hands], L.screen.y1, p.blur * 0.5);
    rods(T, rodPts, L.screen.y1);
  } else {
    const p = pose(t, lib, "end"); const an = drawPuppet(T, lib, p);
    rods(T, [an.neck, ...an.hands], L.screen.y1);
  }
  return T.canvas;
}

export function renderAt(t, ctx, tokens, lib) {
  lib_tw = (t, a, b) => lib.tween(t, a, b, lib.ease.outCubic);
  const mode = t < 4.35 ? "main" : "end";
  lampField(ctx, lib, lamp(t, lib));
  ctx.save(); ctx.globalCompositeOperation = "multiply"; ctx.drawImage(transmission(lib, t, tokens, mode), 0, 0); ctx.restore();
  if (t < 0.4) {                                                        // the match flaring behind the cloth
    const a = lib.env(t, 0.05, 0.4, 0.04, 0.2);
    const g = ctx.createRadialGradient(960, 360, 0, 960, 360, 140); g.addColorStop(0, `rgba(255,236,190,${0.9 * a})`); g.addColorStop(1, "rgba(255,200,120,0)");
    ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.fillStyle = g; ctx.fillRect(820, 220, 280, 280); ctx.restore();
  }
  lib.vignette(ctx, { strength: 0.45, inner: 0.45, color: "#4A2A12" });
  stageFrame(ctx, lib);
  lib.grain(ctx, t, { amount: 0.05, fps: 12, seed: 3 });
}
