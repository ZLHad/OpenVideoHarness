// guochao-festive swatch · 国潮 (swatch grid 150 BPM: beat 0.4 s, 16th 0.1 s, so 0.8 / 2.0 / 4.0 s are beats)
//   0.00       HOOK: the big drum lands and the red sheet slams down over deep red (4 frames, 2-frame shake)
//   0.10–1.70  SIGNATURE: the gold meander (回纹) border prints itself module by module, one block per 16th note,
//              growing from the top centre down both sides at once, one block per eighth note (mirror symmetry);
//              a yellow block printed 3 px off under the gold (套色错位)
//   0.80–2.00  title: Latin line slides in on steps; the Song Black characters slam in one per 16th note
//              (scale 1.4 → 1 in 4 frames), each printed over an offset deep-red key block (套色错位)
//   2.80       the seal stamps (the one element that breaks the symmetry), 2-frame shake
//   2.80 / 3.20 / 3.60  corner flowers (角花) print in pairs, one pair per beat; punch-ins on 3.2 and 3.6; 3.6–4.0 the drums drop
//              out (fill) and the frame draws a small breath in before the doors
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
  const P = L.P, k = full ? 8 : Math.floor(Math.max(0, t - 0.1) / (BEAT / 2) + 1e-9) + (t >= 0.1 ? 1 : 0);   // one step per eighth note from 0.1 s
  for (const [col, off, a] of [["#F2C94C", [4, 3], 0.7], [P("accent"), L.mis[0], 1]]) {            // yellow block 3–4 px off, then the gold
    ctx.save(); ctx.strokeStyle = col; ctx.globalAlpha = a; ctx.lineWidth = 5; ctx.lineCap = "square"; ctx.lineJoin = "miter";
    ctx.translate(...off);
    for (const c of L.cells) if (c.step < k) meanderModule(ctx, c.x, c.y, L.s, c.rot);
    ctx.restore();
  }
}
// corner flowers (角花): four 如意 quarter-rosettes inside the border, printed in pairs on 2.8 / 3.2 / 3.6
function cornerFlowers(ctx, t, lib) {
  const P = L.P, spots = [[[150, 150, 0], [1770, 150, 1]], [[150, 930, 3], [1770, 930, 2]], [[150, 540, 3.5], [1770, 540, 1.5]]];
  spots.forEach((pair, k) => {
    const t0 = S.flower[k]; if (t < t0) return;
    const sp = lib.spring(t - t0, { stiffness: 300, damping: 26 });
    for (const [x, y, q] of pair) {
      ctx.save(); ctx.translate(x, y); ctx.rotate(q * Math.PI / 2); ctx.scale(sp, sp);
      for (const [col, dx] of [["#F2C94C", 3], [P("accent"), 0]]) { ctx.save(); ctx.translate(dx, dx); ctx.strokeStyle = col; ctx.lineWidth = 6; ctx.lineCap = "round"; for (let r = 0; r < 3; r++) { ctx.save(); ctx.rotate(r * Math.PI / 4); cloudPair(ctx, 0, -52, 0.6); ctx.restore(); } ctx.restore(); }
      ctx.fillStyle = P("fg"); ctx.beginPath(); ctx.arc(0, 0, 9, 0, TAU); ctx.fill();
      ctx.restore();
    }
  });
}
function title(ctx, t, tokens, lib) {
  const P = L.P, W = lib.W;
  // Latin: slides in from the left on 6 steps, lands on the beat at 1.07
  const u = lib.easeOf("steps(6)")(lib.seg(t, 0.8, 1.0));
  if (t >= 0.8) {
    lib.setFont(ctx, LAT, "en", 80); ctx.fillStyle = "#F2C94C"; lib.drawText(ctx, lib.TITLE_EN.toUpperCase(), W / 2 - (1 - u) * 240 + 4, 262 + 3, { align: "center", tracking: 0.12 * 80 });   // yellow block, off
    ctx.fillStyle = P("accent"); lib.drawText(ctx, lib.TITLE_EN.toUpperCase(), W / 2 - (1 - u) * 240, 262, { align: "center", tracking: 0.12 * 80 });
  }
  // Chinese: one character per 16th note, slammed in; deep-red key block printed under it, offset
  lib.setFont(ctx, tokens, "zh", 148, { weight: 900 });
  const lay = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 470, align: "center", tracking: 0.02 * 148 });
  const st = (i) => { const t0 = T.slam + i * S16; if (t < t0) return null; const p = lib.tween(t, t0, t0 + 4 / 30, lib.ease.outExpo); return { scale: 1.4 - 0.4 * p, alpha: lib.clamp((t - t0) * 30 / 1.5) }; };
  lib.drawGlyphs(ctx, lay, (g, i) => { const s = st(i); return s && { ...s, dx: -4, dy: 3, fill: P("extra.3") }; });                       // green block, off the other way
  lib.drawGlyphs(ctx, lay, (g, i) => { const s = st(i); return s && { ...s, dx: L.mis[0][0] + 5, dy: L.mis[0][1] + 5, fill: P("extra.0") }; });
  lib.drawGlyphs(ctx, lay, (g, i) => { const s = st(i); return s && { ...s, dx: L.mis[1][0], dy: L.mis[1][1], fill: P("fg") }; });
}
function seal(ctx, t, lib) {
  if (t < T.seal) return;
  const u = lib.tween(t, T.seal, T.seal + 4 / 30, lib.ease.outExpo), sh = t < T.seal + 6 / 30 && t > T.seal + 3 / 30 ? 4 * lib.hashS(3, lib.frame(t)) : 0;
  ctx.save(); ctx.translate(1590 + sh, 790); ctx.rotate(-0.08); ctx.scale(1.35 - 0.35 * u, 1.35 - 0.35 * u);
  ctx.globalAlpha = lib.clamp(u * 2); ctx.drawImage(L.seal, -70, -70); ctx.restore();
}
function misreg(ctx, R) { ctx.fillStyle = L.P("extra.3"); ctx.beginPath(); ctx.arc(5, 4, R, 0, TAU); ctx.fill(); }   // green plate printed 5 px / 4 px off (年画套色错位)
function medallion(ctx, t, tokens, lib, k) {
  const P = L.P, md = L.med[k], R = L.R, t0 = T["med" + k];
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
    misreg(ctx, R);
    ctx.save(); ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.clip();
    [P("fg"), P("accent"), P("fg")].forEach((c, i) => { ctx.fillStyle = c; ctx.fillRect(-R + i * (2 * R / 3) + 3, -R, 2 * R / 3 - 6, 2 * R); });
    ctx.restore();
    ctx.strokeStyle = P("accent"); ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(0, 0, R, 0, TAU); ctx.stroke();
  } else {                                                  // finished: ivory disc, meander ring, mirrored clouds, red heart
    misreg(ctx, R);
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
  lib.setFont(ctx, LAT, "en", 48); ctx.fillStyle = P("accent"); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), md.x, md.y + R + 128, { align: "center", tracking: 2 });
  ctx.restore();
}
function scene(ctx, t, tokens, lib) {
  base(ctx, tokens, lib, L.P("bg"));
  border(ctx, t, lib);
  title(ctx, t, tokens, lib);
  for (let k = 0; k < 3; k++) medallion(ctx, t, tokens, lib, k);
  cornerFlowers(ctx, t, lib);
  seal(ctx, t, lib);
}
function endFrame(ctx, t, tokens, lib) {
  const P = L.P;
  base(ctx, tokens, lib, P("extra.0"));
  border(ctx, t, lib, true);
  ctx.textAlign = "center";
  lib.setFont(ctx, tokens, "zh", 230, { weight: 900 }); ctx.fillStyle = P("bg"); ctx.fillText("国潮", lib.W / 2 + 6, 626);
  ctx.fillStyle = P("fg"); ctx.fillText("国潮", lib.W / 2, 620);
  lib.setFont(ctx, LAT, "en", 52); ctx.fillStyle = P("accent"); lib.drawText(ctx, "GUOCHAO · FESTIVE", lib.W / 2, 730, { align: "center", tracking: 10 });
}

export function renderAt(t, ctx, tokens, lib) {
  // 2-frame punch-ins on the first slam, the seal, 3.2 and 3.6; 3.6–4.0 a breath in (the drums drop out, fill) before the doors
  const punch = [T.slam, T.seal, S.flower[1], S.flower[2]].some((tp) => t >= tp && t < tp + 2 / 30) ? 1.08 : 1;
  const breath = 1 - 0.018 * lib.ease.inOutSine(lib.seg(t, S.flower[2], T.doors));
  // hook: the bright red sheet drops onto deep red in 4 frames on the first drum hit, then a 2-frame shake
  const drop = t < T.sheet ? -lib.H * (1 - lib.ease.outExpo(t / T.sheet)) : 0, shake = t >= T.sheet && t < T.sheet + 2 / 30 ? 6 * lib.hashS(2, lib.frame(t)) : 0;
  const draw = (x) => { const sc = punch * breath; x.translate(shake, drop); if (sc !== 1) { x.translate(lib.W / 2, lib.H / 2); x.scale(sc, sc); x.translate(-lib.W / 2, -lib.H / 2); } scene(x, t, tokens, lib); };
  if (t < T.sheet) { base(ctx, tokens, lib, L.P("extra.0")); ctx.fillStyle = "rgba(0,0,0,0.25)"; ctx.fillRect(0, lib.H + drop, lib.W, 40); }   // deep red under the falling sheet, with its shadow
  if (t < T.doors) { ctx.save(); draw(ctx); ctx.restore(); return; }
  // double doors: the frame splits on the centre axis
  const u = lib.tween(t, T.doors, T.doors + 0.44, lib.ease.inOutCubic), W = lib.W, H = lib.H, off = u * (W / 2 + 40);
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
