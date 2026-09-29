// dunhuang-mural swatch · 敦煌（盛唐色板）
//   0.00       a bronze bell; a torch-like pool of light sweeps across the dark cave wall (0.0–0.8, whole frame)
//   0.10–3.60  SIGNATURE: a PAIR of flying figures (飞天: head, bare torso with a sash, long skirt, feet, arms, one holding
//              flowers), first drawn in iron-wire line (0.1–0.6), then coloured (0.45–0.95); each glides along a long
//              S-arc from the outer edge and the two heads meet on the centre axis on the bell at 3.6. Their silk scarves
//              (披帛) trail along the flight path, 3.5× the body length, with a fixed S-wave along their length (no jitter)
//   0.80–2.40  title: every glyph appears as an ink outline first, then its colour fills in
//   2.00–3.05  motif: ONE horizontal narrative strip (横卷) in three sections — ink sketch → flat colour → banded shading
//              (叠晕) and gold; 2.8 / 3.2 / 3.6 add gold dots, lotus hearts and gold rules, one per beat
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

function bez(p, u) { const v = 1 - u; return [0, 1].map((k) => v * v * v * p[0][k] + 3 * v * v * u * p[1][k] + 3 * v * u * u * p[2][k] + u * u * u * p[3][k]); }
function arcTable(ctrl, n = 600) {            // sample the flight curve by arc length (setup only)
  const pts = [], S = [0];
  for (let i = 0; i <= n; i++) pts.push(bez(ctrl, i / n));
  for (let i = 1; i <= n; i++) S.push(S[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
  return { pts, S, len: S[n] };
}
function atArc(tb, s) {                        // point + unit tangent at arc length s (clamped; extrapolated before 0)
  const S = tb.S, n = S.length - 1;
  if (s <= 0) { const [a, b] = [tb.pts[0], tb.pts[1]], l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1, tx = (b[0] - a[0]) / l, ty = (b[1] - a[1]) / l; return { x: a[0] + tx * s, y: a[1] + ty * s, tx, ty }; }
  let lo = 0, hi = n; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (S[m] < s) lo = m; else hi = m; }
  const i = Math.min(hi, n), f = (s - S[i - 1]) / ((S[i] - S[i - 1]) || 1), a = tb.pts[i - 1], b = tb.pts[i];
  const l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
  return { x: a[0] + (b[0] - a[0]) * f, y: a[1] + (b[1] - a[1]) * f, tx: (b[0] - a[0]) / l, ty: (b[1] - a[1]) / l };
}
// Action times come from events.json, the file render.sh uses to place the foley, so picture and sound share one number
// per action: T[id] for single actions (entries sharing an id layer sounds on one action and must share t), S[series]
// for repeated ones (sorted, de-duplicated times).
let T = null, S = null;
async function loadTimes() {
  const ev = await (await fetch(new URL("./events.json", import.meta.url))).json(), t = {}, s = {};
  for (const e of ev) {
    if (e.id) { if (e.id in t && t[e.id] !== e.t) throw new Error(`events.json: "${e.id}" has two times`); t[e.id] = e.t; }
    if (e.series) (s[e.series] ||= []).push(e.t);
  }
  for (const k in s) s[k] = [...new Set(s[k])].sort((a, b) => a - b);
  return [t, s];
}
export async function setup(ctx, tokens, lib) {
  [T, S] = await loadTimes();
  const P = (k) => lib.color(tokens, k);
  const left = arcTable([[-700, 440], [300, 480], [230, 90], [790, 176]]);
  const right = arcTable([[2620, 440], [1620, 480], [1690, 90], [1130, 176]]);
  const entry = (tb) => { let s = 0; while (s < tb.len && atArc(tb, s).x < 150) s += 4; return s; };     // on screen at 0.1 s
  const entryR = (tb) => { let s = 0; while (s < tb.len && atArc(tb, s).x > 1770) s += 4; return s; };
  L = {
    P, wall: buildWall(lib, tokens), vine: buildVine(lib, tokens), caisson: buildCaisson(lib, tokens, 620),
    flakes: buildFlakes(lib, [[300, 170, 1620, 430], [170, 490, 1750, 880]]),
    enY: 292, zhY: 408, bandTop: 486, bandBot: 884,
    strip: { x: 192, y: 506, w: 1536, h: 254 },
    fly: { left: { tb: left, s0: entry(left) }, right: { tb: right, s0: entryR(right) } },
  };
}

// ── the flying figures (飞天). Local frame: +x = direction of flight, y down, origin at the chest; drawn at scale 1.15.
// prone, chest down, the head leading slightly low; legs and the long skirt sweep UP behind (the classic flying arc)
const SKC = (u) => [-4 - 214 * u, -6 - 40 * Math.pow(u, 1.6)];
const SK = (() => { const top = [], bot = []; for (let i = 0; i <= 16; i++) { const u = i / 16, [x, y] = SKC(u), [x2, y2] = SKC(Math.min(1, u + 0.02)), l = Math.hypot(x2 - x, y2 - y) || 1, nx = -(y2 - y) / l, ny = (x2 - x) / l;
  const w = 34 * (1 - u) + 12 + 16 * Math.exp(-Math.pow((u - 0.82) / 0.1, 2)); top.push([x + nx * w / 2, y + ny * w / 2]); bot.push([x - nx * w / 2, y - ny * w / 2]); } return [...top, ...bot.reverse()]; })();
const TORSO = [[52, -8], [34, -17], [4, -16], [-10, -12], [-8, 10], [22, 14], [50, 10]];
function pathOf(pts) { const p = new Path2D(); pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); return p; }
function flightS(t, f, lib) { return f.s0 + (f.tb.len - f.s0) * lib.ease.inOutSine(lib.seg(t, 0.1, T.meet)); }   // the heads meet on the axis on events.json "meet"
function drawScarf(ctx, lib, t, f, sHead, len, off, w0, col, light, ph) {
  const N = 70, pts = [];
  for (let i = 0; i <= N; i++) {
    const sig = i / N * len, q = atArc(f.tb, sHead - 30 - sig), nx = -q.ty, ny = q.tx;
    const o = off + (14 + 30 * (i / N)) * Math.sin(sig / 190 + ph + 0.35 * t) * Math.min(1, i / 10);   // fixed S-wave along the scarf, drifting slowly
    const tw = 0.45 + 0.55 * Math.abs(Math.cos(sig / 150 + ph));                                          // edge-on ↔ face-on
    pts.push({ x: q.x + nx * o, y: q.y + ny * o, nx, ny, w: (w0 * (1 - 0.55 * i / N)) * tw });
  }
  const poly = (k) => { const p = new Path2D(); pts.forEach((q, i) => (i ? p.lineTo(q.x + q.nx * q.w / 2 * k, q.y + q.ny * q.w / 2 * k) : p.moveTo(q.x + q.nx * q.w / 2 * k, q.y + q.ny * q.w / 2 * k)));
    for (let i = pts.length - 1; i >= 0; i--) { const q = pts[i]; p.lineTo(q.x - q.nx * q.w / 2 * k, q.y - q.ny * q.w / 2 * k); } p.closePath(); return p; };
  return { outer: poly(1), inner: poly(0.36), col, light };
}
function strokeReveal(ctx, path, u) { if (u <= 0) return; ctx.save(); if (u < 1) { ctx.setLineDash([2400 * u, 4000]); } ctx.stroke(path); ctx.restore(); }
function apsara(ctx, lib, t, side) {
  if (t < 0.1) return;
  const P = L.P, f = L.fly[side], sHead = flightS(t, f, lib), q = atArc(f.tb, sHead);
  const line = lib.tween(t, 0.1, 0.6, lib.ease.inOutSine), paint = lib.tween(t, 0.45, 0.95, lib.ease.inOutSine);
  const skirtC = side === "left" ? P("accent") : P("extra.1"), skirtL = side === "left" ? "#6F9FBE" : "#D98A6E";
  const scarfC = side === "left" ? P("extra.1") : P("accent"), scarfL = side === "left" ? "#D98A6E" : "#6F9FBE";
  const bob = 3 * Math.sin(1.1 * t + (side === "left" ? 0 : 1.5));
  // scarves first (behind the body): two, 3.5× and 3× the ~300 px body
  const sc = [drawScarf(ctx, lib, t, f, sHead, 1050, 12, 20, scarfC, scarfL, 0.3), drawScarf(ctx, lib, t, f, sHead, 900, -16, 16, P("extra.0"), "#8FC4AE", 2.1)];
  ctx.save(); ctx.lineJoin = "round"; ctx.strokeStyle = P("fg"); ctx.lineWidth = 2;
  for (const r of sc) { if (paint > 0) { ctx.globalAlpha = paint; ctx.fillStyle = r.col; ctx.fill(r.outer); ctx.fillStyle = r.light; ctx.fill(r.inner); ctx.globalAlpha = 1; } strokeReveal(ctx, r.outer, line); }
  ctx.restore();
  // the figure, rigid, oriented along the flight tangent (mirrored for the right-hand figure so both face the axis)
  const ang = Math.atan2(q.ty, q.tx);
  ctx.save(); ctx.translate(q.x, q.y + bob); ctx.rotate(ang); if (side === "right") ctx.scale(1, -1); ctx.rotate(0.02); ctx.scale(1.2, 1.2);   // level, nose barely down
  ctx.lineJoin = "round"; ctx.lineCap = "round"; ctx.strokeStyle = P("fg"); ctx.lineWidth = 1.8;
  const skin = P("extra.5"), limb = (pts, w) => { const p = new Path2D(); pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y)));
    ctx.save(); ctx.lineWidth = w + 3.6; strokeReveal(ctx, p, line); ctx.restore();
    if (paint > 0) { ctx.save(); ctx.globalAlpha = paint; ctx.strokeStyle = skin; ctx.lineWidth = w; ctx.stroke(p); ctx.restore(); } };
  limb([[30, -14], [14, -40], [34, -60]], 7);                                                               // back arm, raised behind the head
  const skirt = pathOf(SK), torso = pathOf(TORSO);
  if (paint > 0) {
    ctx.save(); ctx.globalAlpha = paint;
    ctx.fillStyle = skirtC; ctx.fill(skirt); ctx.save(); ctx.clip(skirt); ctx.strokeStyle = skirtL; ctx.lineWidth = 12; ctx.stroke(skirt); ctx.restore();   // 叠晕 on the skirt
    { const [fx, fy] = SKC(1); ctx.fillStyle = skin; ctx.beginPath(); ctx.moveTo(fx + 4, fy + 4); ctx.lineTo(fx - 22, fy - 14); ctx.lineTo(fx - 6, fy + 8); ctx.closePath(); ctx.fill(); ctx.stroke(); }   // feet
    ctx.fillStyle = skin; ctx.fill(torso);
    ctx.strokeStyle = P("extra.0"); ctx.lineWidth = 8; ctx.beginPath(); ctx.moveTo(40, -17); ctx.lineTo(6, 13); ctx.stroke();                            // sash
    ctx.fillStyle = skin; ctx.beginPath(); ctx.arc(72, 2, 17, 0, TAU); ctx.fill();                                                                       // head
    ctx.fillStyle = P("fg"); ctx.beginPath(); ctx.ellipse(64, -10, 15, 10, -0.2, 0, TAU); ctx.fill(); ctx.beginPath(); ctx.arc(70, -24, 7, 0, TAU); ctx.fill();   // hair, high topknot
    ctx.restore();
  }
  strokeReveal(ctx, skirt, line); strokeReveal(ctx, torso, line);
  if (line > 0.3) {
    ctx.beginPath(); ctx.arc(72, 2, 17, 0, TAU); ctx.stroke();
    ctx.beginPath(); for (const off of [-6, 6]) { for (let i = 1; i <= 14; i++) { const u = i / 16, [x, y] = SKC(u); i === 1 ? ctx.moveTo(x, y + off * (1 - u)) : ctx.lineTo(x, y + off * (1 - u)); } } ctx.stroke();   // skirt folds
    ctx.beginPath(); ctx.moveTo(78, 2); ctx.lineTo(84, 4); ctx.stroke();                                                                                 // eye, looking ahead and down
  }
  limb([[46, 4], [70, 22], [98, 18]], 7);                                                                   // front arm, reaching forward with flowers
  if (paint > 0) { ctx.save(); ctx.globalAlpha = paint; ctx.fillStyle = P("extra.4"); ctx.beginPath(); ctx.ellipse(106, 14, 14, 5, 0, 0, TAU); ctx.fill(); ctx.fillStyle = P("extra.1"); ctx.beginPath(); ctx.arc(104, 7, 6, 0, TAU); ctx.fill(); ctx.stroke(); ctx.restore(); }
  ctx.restore();
}
function flowers(ctx, lib, t) {                                              // 散花 from the figures' hands, falling on the outer thirds
  const P = L.P, cols = [P("extra.1"), P("extra.0"), P("extra.5"), P("accent")];
  for (let k = 0; k < 18; k++) {
    const side = k % 2 ? "right" : "left", t0 = 0.8 + lib.hash(5, k) * 2.4; if (t < t0) continue;
    const f = L.fly[side], q = atArc(f.tb, flightS(t0, f, lib)), a = t - t0;
    const x = q.x + (side === "left" ? -1 : 1) * (40 + a * 30) + 18 * Math.sin(1.6 * a + k), y = q.y + 20 + a * (60 + 30 * lib.hash(7, k));
    if (y > L.bandTop - 18 || (x > 470 && x < 1450 && y > 200)) continue;   // keep the title clear
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

// the motif: ONE narrative strip (横卷) in three sections, each the same three scenes (cloud · lotus · cloud) at a later
// stage of mural painting: 0 起稿 ink sketch · 1 平涂 flat colour · 2 叠晕 banded shading + 点金 gold
function section(ctx, t, tokens, lib, k) {
  const P = L.P, st = L.strip, sw = st.w / 3, x0 = st.x + k * sw + 8, y0 = st.y, w = sw - 16, h = st.h, t0 = 2.0 + k * 0.2;
  if (t < t0) return;
  const cw = w / 3, cy = y0 + h / 2;
  const shapes = [cloudPath(x0 + cw * 0.5, cy + 8, 1.25, 1), lotusPath(x0 + w / 2, cy + 46, 1.45), cloudPath(x0 + cw * 2.5, cy + 8, 1.25, -1)];
  const uLine = lib.tween(t, t0, t0 + 0.4, lib.ease.inOutSine);
  const uFill = k >= 1 ? lib.tween(t, t0 + 0.2, t0 + 0.5, lib.ease.inOutSine) : 0;
  const uBand = k === 2 ? lib.tween(t, t0 + 0.3, t0 + 0.55, lib.ease.inOutSine) : 0;
  const comp = [P("accent"), P("extra.2"), P("extra.0")], light = ["#5A8BAB", "#B8664A", "#72B096"], pale = ["#86AFC8", "#CF8C70", "#9CCAB5"];
  ctx.save();
  if (uFill > 0) { ctx.globalAlpha = uFill; comp.forEach((c, i) => { ctx.fillStyle = c; ctx.fillRect(x0 + i * cw, y0, cw, h); }); shapes.forEach((sh) => { ctx.fillStyle = P("extra.5"); ctx.fill(sh); }); ctx.globalAlpha = 1; }
  if (uBand > 0) {
    ctx.globalAlpha = uBand;
    comp.forEach((c, i) => { ctx.fillStyle = light[i]; ctx.fillRect(x0 + i * cw + 14, y0 + 14, cw - 28, h - 28); ctx.fillStyle = pale[i]; ctx.fillRect(x0 + i * cw + 28, y0 + 28, cw - 56, h - 56); });
    shapes.forEach((sh, i) => { ctx.fillStyle = P("extra.5"); ctx.fill(sh); ctx.save(); ctx.clip(sh); ctx.strokeStyle = [light[0], "#E8A488", light[2]][i]; ctx.lineWidth = 18; ctx.stroke(sh); ctx.restore(); });
    ctx.globalAlpha = 1;
  }
  ctx.strokeStyle = P("fg"); ctx.lineWidth = 2.6; ctx.lineJoin = "round";
  lib.strokePartial(ctx, [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h], [x0, y0]], uLine);
  if (uLine > 0.5) {
    ctx.globalAlpha = lib.clamp((uLine - 0.5) * 2);
    ctx.beginPath(); ctx.moveTo(x0 + cw, y0); ctx.lineTo(x0 + cw, y0 + h); ctx.moveTo(x0 + 2 * cw, y0); ctx.lineTo(x0 + 2 * cw, y0 + h); ctx.stroke();
    shapes.forEach((sh) => ctx.stroke(sh));
    ctx.globalAlpha = 1;
  }
  if (k === 2) {                                               // 点金, one layer per beat: 2.8 border dots · 3.2 lotus heart · 3.6 gold rules
    ctx.fillStyle = P("extra.4"); ctx.strokeStyle = P("extra.4");
    if (t >= 2.8) { const n = Math.min(24, Math.floor((t - 2.8) * 30 * 3) + 1); for (let i = 0; i < n; i++) { const px = x0 + 10 + (w - 20) * i / 23; ctx.beginPath(); ctx.arc(px, y0 + 8, 4, 0, TAU); ctx.arc(px, y0 + h - 8, 4, 0, TAU); ctx.fill(); } }
    if (t >= 3.2) { const r = 11 * lib.spring(t - 3.2, { w: 20, zeta: 0.8 }); ctx.beginPath(); ctx.arc(x0 + w / 2, cy + 26, r, 0, TAU); ctx.fill(); }
    if (t >= 3.6) { ctx.lineWidth = 3; const u = lib.tween(t, 3.6, 3.8, lib.ease.outCubic); ctx.beginPath(); ctx.moveTo(x0 + cw, y0 + h * (0.5 - 0.5 * u)); ctx.lineTo(x0 + cw, y0 + h * (0.5 + 0.5 * u)); ctx.moveTo(x0 + 2 * cw, y0 + h * (0.5 - 0.5 * u)); ctx.lineTo(x0 + 2 * cw, y0 + h * (0.5 + 0.5 * u)); ctx.stroke(); }
  }
  const la = lib.tween(t, t0 + 0.12, t0 + 0.4, lib.ease.outCubic);
  ctx.globalAlpha = la; ctx.textAlign = "center"; ctx.fillStyle = P("fg");
  lib.setFont(ctx, tokens, "zh", 52, { weight: 400 }); ctx.fillText(lib.MOTIF[k].zh, x0 + w / 2, y0 + h + 54);
  lib.setFont(ctx, LAT, "en", 40); ctx.fillStyle = P("extra.6"); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), x0 + w / 2, y0 + h + 100, { align: "center", tracking: 3 });
  ctx.restore();
}
// cave light: at 0.0 the wall is dark except a warm pool of light that sweeps left→right and opens up (whole frame)
function caveLight(ctx, t, lib) {
  if (t >= 0.85) return;
  const u = lib.ease.inOutSine(lib.seg(t, 0, 0.85)), cx = lib.lerp(260, 960, u), r = lib.lerp(260, 2300, u);
  const g = ctx.createRadialGradient(cx, 420, r * 0.25, cx, 420, r);
  g.addColorStop(0, "rgba(40,24,14,0)"); g.addColorStop(1, `rgba(40,24,14,${0.78 * (1 - u)})`);
  ctx.fillStyle = g; ctx.fillRect(0, 0, lib.W, lib.H);
}

function scene(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.drawImage(L.wall, 0, 0);
  registers(ctx, t, lib);
  apsara(ctx, lib, t, "left"); apsara(ctx, lib, t, "right");
  flowers(ctx, lib, t);
  titles(ctx, t, tokens, lib);
  for (let k = 0; k < 3; k++) section(ctx, t, tokens, lib, k);
  ctx.save(); ctx.globalAlpha = 0.9; ctx.drawImage(L.flakes, 0, 0); ctx.restore();   // time: flaked plaster over everything
  caveLight(ctx, t, lib);
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
  if (t < T.caisson) { scene(ctx, t, tokens, lib); return; }
  // caisson iris: B opens inside a square (rotated 45°), its edge framed by three nested borders
  const P = L.P, u = lib.tween(t, T.caisson, T.caisson + 0.75, lib.ease.inOutCubic), cx = lib.W / 2, cy = lib.H / 2 - 40;
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
