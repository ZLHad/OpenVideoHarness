// guochao-festive swatch · 国潮 (swatch grid 150 BPM: beat 0.4 s, 16th 0.1 s, so 0.8 / 2.0 / 4.0 s are beats)
//   0.10–0.90  SIGNATURE: the gold meander (回纹) border prints itself module by module, one block per 16th note,
//              growing from the top centre down both sides at once (mirror symmetry)
//   0.80–2.00  title: Latin line slides in on steps; the Song Black characters slam in one per 16th note
//              (scale 1.4 → 1 in 4 frames), each printed over an offset deep-red key block (套色错位)
//   2.80       the seal stamps (the one element that breaks the symmetry), 2-frame shake
//   2.00–2.60  motif: three medallions pop in on the beat: guide-line sketch → three panels → finished medallion
//   4.00–4.44  SIGNATURE TRANSITION: the frame splits on the centre axis and slides open like double doors

export const fonts = ["Futura"];
const LAT = { fonts: { en: { family: ["Futura", "Avenir Next Condensed"], weight: 800, stretch: "75%" } } };
const TAU = Math.PI * 2, BEAT = 60 / 150, S16 = BEAT / 4;   // swatch runs at 150 BPM: 0.8, 2.0 and 4.0 s fall on beats
let L = null;

function meanderModule(ctx, x, y, s, rot) {       // one 回纹 block: a square spiral in an s×s cell
  const q = s / 48;
  ctx.save(); ctx.translate(x + s / 2, y + s / 2); ctx.rotate(rot); ctx.translate(-s / 2, -s / 2);
  ctx.beginPath();
  [[2, 46], [2, 2], [46, 2], [46, 46], [13, 46], [13, 13], [35, 13], [35, 35], [24, 35], [24, 24]].forEach(([a, b], i) => (i ? ctx.lineTo(a * q, b * q) : ctx.moveTo(a * q, b * q)));
  ctx.stroke(); ctx.restore();
}
function cloudPair(ctx, cx, cy, s) {               // mirrored 如意云 pair
  for (const f of [-1, 1]) {
    ctx.beginPath();
    ctx.moveTo(cx, cy + 22 * s);
    ctx.bezierCurveTo(cx + f * 10 * s, cy - 6 * s, cx + f * 44 * s, cy - 34 * s, cx + f * 58 * s, cy - 6 * s);
    ctx.bezierCurveTo(cx + f * 66 * s, cy + 14 * s, cx + f * 40 * s, cy + 22 * s, cx + f * 36 * s, cy + 6 * s);
    ctx.bezierCurveTo(cx + f * 34 * s, cy - 6 * s, cx + f * 50 * s, cy - 6 * s, cx + f * 48 * s, cy + 4 * s);
    ctx.stroke();
  }
}

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k), W = lib.W, H = lib.H, s = 48, m = 40;
  // border modules in perimeter order, starting at the top centre, clockwise and counter-clockwise
  const cells = [];
  const nx = Math.floor((W - 2 * m) / s), ny = Math.floor((H - 2 * m) / s) - 2;
  const ox = (W - nx * s) / 2, oy = (H - (ny + 2) * s) / 2;
  for (let i = 0; i < nx; i++) cells.push({ x: ox + i * s, y: oy, rot: 0, d: Math.abs(i + 0.5 - nx / 2) });                               // top
  for (let j = 1; j <= ny; j++) { cells.push({ x: ox, y: oy + j * s, rot: -Math.PI / 2, d: nx / 2 + j }); cells.push({ x: ox + (nx - 1) * s, y: oy + j * s, rot: Math.PI / 2, d: nx / 2 + j }); }
  for (let i = 0; i < nx; i++) cells.push({ x: ox + i * s, y: oy + (ny + 1) * s, rot: Math.PI, d: nx / 2 + ny + (nx / 2 - Math.abs(i + 0.5 - nx / 2)) });
  const dMax = Math.max(...cells.map((c) => c.d));
  cells.forEach((c) => { c.step = Math.floor(c.d / dMax * 7.999); });          // 8 steps on 16th notes
  const seal = document.createElement("canvas"); seal.width = seal.height = 140; const sx = seal.getContext("2d");
  sx.fillStyle = P("extra.0"); sx.fillRect(10, 10, 120, 120);
  lib.setFont(sx, tokens, "zh", 84, { weight: 700 }); sx.fillStyle = P("fg"); sx.textAlign = "center"; sx.textBaseline = "middle"; sx.fillText("码", 70, 76);
  sx.strokeStyle = P("fg"); sx.lineWidth = 4; sx.strokeRect(20, 20, 100, 100);
  sx.globalCompositeOperation = "destination-out"; const r = lib.rng(8);
  for (let k = 0; k < 90; k++) { sx.globalAlpha = 0.3 + r() * 0.6; sx.beginPath(); sx.arc(10 + r() * 120, 10 + r() * 120, 0.6 + r() * 1.8, 0, TAU); sx.fill(); }   // print speckle
  L = { P, cells, s, seal, mis: [[3, 2], [-2, -1]], med: [600, 960, 1320].map((x) => ({ x, y: 698 })), R: 106 };
}

function base(ctx, tokens, lib, colour) {
  ctx.fillStyle = colour; ctx.fillRect(0, 0, lib.W, lib.H);
  lib.paper(ctx, { tone: colour, amount: 0.6, blotch: 0.05, tooth: 0.03, fiber: 0.3, seed: 6 });
}
function border(ctx, t, lib, full = false) {
  const P = L.P, k = full ? 8 : Math.floor(Math.max(0, t - 0.1) / S16 + 1e-9);
  ctx.save(); ctx.strokeStyle = P("accent"); ctx.lineWidth = 5; ctx.lineCap = "square"; ctx.lineJoin = "miter";
  ctx.translate(...L.mis[0]);                                                  // the gold block is printed slightly off
  for (const c of L.cells) if (c.step < k) meanderModule(ctx, c.x, c.y, L.s, c.rot);
  ctx.restore();
}
function title(ctx, t, tokens, lib) {
  const P = L.P, W = lib.W;
  // Latin: slides in from the left on 6 steps, lands on the beat at 1.07
  const u = lib.easeOf("steps(6)")(lib.seg(t, 0.8, 1.0));
  if (t >= 0.8) {
    lib.setFont(ctx, LAT, "en", 64); ctx.fillStyle = P("accent");
    lib.drawText(ctx, lib.TITLE_EN.toUpperCase(), W / 2 - (1 - u) * 240, 262, { align: "center", tracking: 0.14 * 64 });
  }
  // Chinese: one character per 16th note, slammed in; deep-red key block printed under it, offset
  lib.setFont(ctx, tokens, "zh", 148, { weight: 900 });
  const lay = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 470, align: "center", tracking: 0.02 * 148 });
  const st = (i) => { const t0 = 1.2 + i * S16; if (t < t0) return null; const p = lib.tween(t, t0, t0 + 4 / 30, lib.ease.outExpo); return { scale: 1.4 - 0.4 * p, alpha: lib.clamp((t - t0) * 30 / 1.5) }; };
  lib.drawGlyphs(ctx, lay, (g, i) => { const s = st(i); return s && { ...s, dx: L.mis[0][0] + 5, dy: L.mis[0][1] + 5, fill: P("extra.0") }; });
  lib.drawGlyphs(ctx, lay, (g, i) => { const s = st(i); return s && { ...s, dx: L.mis[1][0], dy: L.mis[1][1], fill: P("fg") }; });
}
function seal(ctx, t, lib) {
  if (t < 2.8) return;
  const u = lib.tween(t, 2.8, 2.8 + 4 / 30, lib.ease.outExpo), sh = t < 2.8 + 6 / 30 && t > 2.8 + 3 / 30 ? 4 * lib.hashS(3, lib.frame(t)) : 0;
  ctx.save(); ctx.translate(1590 + sh, 790); ctx.rotate(-0.08); ctx.scale(1.35 - 0.35 * u, 1.35 - 0.35 * u);
  ctx.globalAlpha = lib.clamp(u * 2); ctx.drawImage(L.seal, -70, -70); ctx.restore();
}
function medallion(ctx, t, tokens, lib, k) {
  const P = L.P, md = L.med[k], R = L.R, t0 = 2.0 + k * BEAT / 2;
  if (t < t0) return;
  const sp = lib.spring(t - t0, { stiffness: 300, damping: 26 });
  ctx.save(); ctx.translate(md.x, md.y); ctx.scale(sp, sp);
  ctx.lineCap = "round"; ctx.lineJoin = "round";
  if (k === 0) {                                            // guide-line sketch: circle, cross, diagonals, dashed
    ctx.strokeStyle = P("accent"); ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.stroke();
    ctx.setLineDash([10, 10]); ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.moveTo(-R, 0); ctx.lineTo(R, 0); ctx.moveTo(0, -R); ctx.lineTo(0, R); ctx.stroke();
    ctx.beginPath(); ctx.arc(0, 0, R * 0.55, 0, TAU); ctx.stroke(); ctx.setLineDash([]);
  } else if (k === 1) {                                     // three panels inside the round frame
    ctx.save(); ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.clip();
    [P("fg"), P("accent"), P("fg")].forEach((c, i) => { ctx.fillStyle = c; ctx.fillRect(-R + i * (2 * R / 3) + 3, -R, 2 * R / 3 - 6, 2 * R); });
    ctx.restore();
    ctx.strokeStyle = P("accent"); ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.stroke();
  } else {                                                  // finished: ivory disc, meander ring, mirrored clouds, red heart
    ctx.fillStyle = P("fg"); ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.fill();
    ctx.strokeStyle = P("accent"); ctx.lineWidth = 8; ctx.beginPath(); ctx.arc(0, 0, R - 4, 0, TAU); ctx.stroke();
    ctx.lineWidth = 3; for (let i = 0; i < 16; i++) { const a = i * TAU / 16; ctx.beginPath(); ctx.moveTo(Math.cos(a) * (R - 16), Math.sin(a) * (R - 16)); ctx.lineTo(Math.cos(a) * (R - 26), Math.sin(a) * (R - 26)); ctx.stroke(); }
    ctx.strokeStyle = P("bg"); ctx.lineWidth = 7;                                    // four 如意 heads around the centre (柿蒂 layout)
    for (let q = 0; q < 4; q++) { ctx.save(); ctx.rotate(q * TAU / 4); cloudPair(ctx, 0, -46, 0.52); ctx.restore(); }
    ctx.fillStyle = P("accent"); ctx.beginPath(); ctx.arc(0, 0, 20, 0, TAU); ctx.fill();
    ctx.fillStyle = P("extra.2"); ctx.beginPath(); ctx.arc(0, 0, 8, 0, TAU); ctx.fill();
  }
  ctx.restore();
  const la = lib.clamp((t - t0) * 8);
  ctx.save(); ctx.globalAlpha = la; ctx.textAlign = "center";
  lib.setFont(ctx, tokens, "zh", 52, { weight: 700 }); ctx.fillStyle = P("fg"); ctx.fillText(lib.MOTIF[k].zh, md.x, md.y + R + 76);
  lib.setFont(ctx, LAT, "en", 28); ctx.fillStyle = P("accent"); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), md.x, md.y + R + 116, { align: "center", tracking: 4 });
  ctx.restore();
}
function scene(ctx, t, tokens, lib) {
  base(ctx, tokens, lib, L.P("bg"));
  border(ctx, t, lib);
  title(ctx, t, tokens, lib);
  for (let k = 0; k < 3; k++) medallion(ctx, t, tokens, lib, k);
  seal(ctx, t, lib);
}
function endFrame(ctx, t, tokens, lib) {
  const P = L.P;
  base(ctx, tokens, lib, P("extra.0"));
  border(ctx, t, lib, true);
  ctx.textAlign = "center";
  lib.setFont(ctx, tokens, "zh", 230, { weight: 900 }); ctx.fillStyle = P("bg"); ctx.fillText("国潮", lib.W / 2 + 6, 626);
  ctx.fillStyle = P("fg"); ctx.fillText("国潮", lib.W / 2, 620);
  lib.setFont(ctx, LAT, "en", 34); ctx.fillStyle = P("accent"); lib.drawText(ctx, "GUOCHAO · FESTIVE", lib.W / 2, 720, { align: "center", tracking: 10 });
}

export function renderAt(t, ctx, tokens, lib) {
  // 2-frame punch-ins on the first slam and on the seal
  const punch = [1.2, 2.8].some((tp) => t >= tp && t < tp + 2 / 30) ? 1.08 : 1;
  const draw = (x) => { if (punch !== 1) { x.translate(lib.W / 2, lib.H / 2); x.scale(punch, punch); x.translate(-lib.W / 2, -lib.H / 2); } scene(x, t, tokens, lib); };
  if (t < 4.0) { ctx.save(); draw(ctx); ctx.restore(); return; }
  // double doors: the frame splits on the centre axis
  const u = lib.tween(t, 4.0, 4.44, lib.ease.inOutCubic), W = lib.W, H = lib.H, off = u * (W / 2 + 40);
  endFrame(ctx, t, tokens, lib);
  if (u >= 1) return;
  const A = lib.offscreen("gc_A", (x) => scene(x, t, tokens, lib));
  ctx.save();
  ctx.shadowColor = "rgba(40,0,0,0.55)"; ctx.shadowBlur = 30;
  ctx.drawImage(A, 0, 0, W / 2, H, -off, 0, W / 2, H);
  ctx.drawImage(A, W / 2, 0, W / 2, H, W / 2 + off, 0, W / 2, H);
  ctx.shadowBlur = 0; ctx.fillStyle = L.P("accent");
  ctx.fillRect(W / 2 - off - 6, 0, 6, H); ctx.fillRect(W / 2 + off, 0, 6, H);                                          // gold door edges
  ctx.restore();
}
