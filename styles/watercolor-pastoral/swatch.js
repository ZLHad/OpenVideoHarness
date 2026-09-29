// watercolor-pastoral swatch · 水彩田园
//   0.10–0.42  HOOK: one visible wet brush stroke sweeps across the sky; 0.30–0.90 the sky wash paints itself downward
//              (wet edge, back-run blooms), then far hills, treeline and meadow wash in, far to near; paper multiplied over all
//   0.30–4.00  SIGNATURE: wind travels left→right as a wave through the grass (one wave per 1.2 s, 1100 px wavelength,
//              8–13° with gusts);
//              each tree's 4 leaf clumps answer 0.4 s later (sway, lean, squash, a light upwind rim when the leaves
//              flip); petals and loose leaves ride the same wind; clouds drift with their cool shadows
//   0.85–2.40  title: handwritten reveal (soft wet edge moving left→right), Latin then Chinese
//   2.00–2.95  motif: one tree at three stages: pencil sketch → flat washes → layered light, cool shadow, warm glint
//   4.00–5.00  SIGNATURE TRANSITION: warm light blooms from the sun to paper white (12 frames) and recedes (18 frames)

export const fonts = ["Palatino"];
const LAT = { fonts: { en: { family: ["Palatino", "Georgia"], weight: 400, style: "italic" } } };
const TAU = Math.PI * 2;
let L = null;

function cv(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return [c, c.getContext("2d")]; }
function grainTile(lib) {
  const [c, x] = cv(256, 256), img = x.createImageData(256, 256);
  for (let j = 0; j < 256; j++) for (let i = 0; i < 256; i++) { const v = 0.78 + 0.22 * (lib.fbm2(i / 5, j / 5, { octaves: 2, seed: 8 }) * 0.5 + 0.5) + 0.06 * lib.hashS(i, j, 3), k = (j * 256 + i) * 4; img.data[k] = img.data[k + 1] = img.data[k + 2] = Math.min(255, v * 255); img.data[k + 3] = 255; }
  x.putImageData(img, 0, 0); return c;
}
// a watercolour wash: soft fill, pooled darker edge, pigment granulation
function wash(x, path, col, a, lib, { edge = 0.35, blur = 1.6, gran = 0.3 } = {}) {
  x.save(); x.filter = `blur(${blur}px)`; x.globalAlpha = a; x.fillStyle = col; x.fill(path); x.restore();
  x.save(); x.filter = `blur(${blur * 0.8}px)`; x.globalAlpha = a * edge; x.strokeStyle = lib.mixColor(col, "#202030", 0.25); x.lineWidth = 3; x.stroke(path); x.restore();
  if (gran > 0) { x.save(); x.clip(path); x.globalCompositeOperation = "multiply"; x.globalAlpha = gran; x.fillStyle = x.createPattern(L.grain, "repeat"); x.fill(path); x.restore(); }
}
function unionEdge(x, path, col, a) {                    // pooled edge along the outer silhouette only
  const [c, ox] = cv(x.canvas.width, x.canvas.height); ox.setTransform(x.getTransform()); ox.filter = "blur(1.2px)"; ox.strokeStyle = col; ox.lineWidth = 4; ox.stroke(path);
  ox.filter = "none"; ox.globalCompositeOperation = "destination-out"; ox.fill(path);
  x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.globalAlpha = a; x.drawImage(c, 0, 0); x.restore();
}
function ridgePath(lib, y0, amp, freq, seed, bottom = 1080, w = 2100) {
  const p = new Path2D(); p.moveTo(-60, bottom);
  for (let px = -60; px <= w; px += 16) p.lineTo(px, y0 - amp * (0.55 * Math.sin(px * freq + seed) + 0.45 * Math.sin(px * freq * 2.7 + seed * 3)) - 14 * lib.fbm2(px / 60, seed, { octaves: 3, seed }));
  p.lineTo(w, bottom); p.closePath(); return p;
}
function lumps(lib, y0, n, r, seed, w = 2100) {               // a treeline: overlapping round lumps
  const p = new Path2D(); const rr = lib.rng(seed);
  for (let k = 0; k < n; k++) { const x = -40 + k * (w / n) + rr() * 30, rad = r * (0.7 + rr() * 0.6); p.moveTo(x + rad, y0); p.ellipse(x, y0 - rad * 0.4, rad, rad * 0.8, 0, 0, TAU); }
  p.rect(-60, y0, w + 120, 60); return p;
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
  L = { P, grain: grainTile(lib) };
  // sky: two wet-in-wet horizontal washes, warmer near the horizon
  const [sky, sx] = cv(1920, 700);
  const g = sx.createLinearGradient(0, 0, 0, 700); g.addColorStop(0, lib.rgba(P("extra.0"), 0.9)); g.addColorStop(0.55, lib.rgba(P("extra.0"), 0.45)); g.addColorStop(1, lib.rgba("#F3DDB0", 0.35));
  const skyPath = new Path2D(); skyPath.moveTo(-20, -20); skyPath.lineTo(1940, -20);
  for (let px = 1940; px >= -20; px -= 20) skyPath.lineTo(px, 640 + 24 * lib.fbm2(px / 90, 2, { octaves: 3, seed: 2 }));
  skyPath.closePath();
  sx.save(); sx.filter = "blur(3px)"; sx.fillStyle = g; sx.fill(skyPath); sx.restore();
  sx.save(); sx.clip(skyPath); sx.globalCompositeOperation = "multiply"; sx.globalAlpha = 0.22; sx.fillStyle = sx.createPattern(L.grain, "repeat"); sx.fillRect(0, 0, 1920, 700); sx.restore();
  for (let k = 0; k < 7; k++) {                              // back-runs (cauliflowers): paler blooms inside the wash
    const x = lib.hash(11, k) * 1920, y = 60 + lib.hash(12, k) * 300, r = 60 + lib.hash(13, k) * 90;
    sx.save(); sx.filter = "blur(8px)"; sx.globalAlpha = 0.18; sx.fillStyle = "#F4EEDF"; sx.beginPath(); sx.ellipse(x, y, r * 1.6, r * 0.6, 0, 0, TAU); sx.fill(); sx.restore();
  }
  L.sky = sky;
  { // one wide wet stroke of sky colour across the top: the first thing painted (0.1 s)
    const [c, x] = cv(1920, 360), r = lib.rng(71), top = [], bot = [];
    for (let px = -20; px <= 1940; px += 24) { top.push([px, 40 + 26 * lib.fbm2(px / 140, 1, { octaves: 3, seed: 3 })]); bot.push([px, 330 + 34 * lib.fbm2(px / 120, 2, { octaves: 3, seed: 4 })]); }
    const band = new Path2D(); [...top, ...bot.reverse()].forEach(([a, b], i) => (i ? band.lineTo(a, b) : band.moveTo(a, b))); band.closePath();
    x.save(); x.filter = "blur(2px)"; x.fillStyle = lib.rgba(P("extra.0"), 0.7); x.fill(band); x.restore();
    x.save(); x.clip(band); for (let k = 0; k < 80; k++) { const y = 40 + r() * 300; x.strokeStyle = r() < 0.5 ? "rgba(90,130,170,0.22)" : "rgba(244,238,223,0.35)"; x.lineWidth = 1 + r() * 3; x.beginPath(); x.moveTo(-10, y); x.bezierCurveTo(600, y + (r() - 0.5) * 20, 1300, y + (r() - 0.5) * 20, 1930, y + (r() - 0.5) * 16); x.stroke(); }   // bristle streaks
    x.globalCompositeOperation = "multiply"; x.globalAlpha = 0.45; x.fillStyle = x.createPattern(L.grain, "repeat"); x.fill(band); x.restore();
    x.save(); x.filter = "blur(1px)"; x.strokeStyle = "rgba(80,120,160,0.4)"; x.lineWidth = 3; x.stroke(band); x.restore();   // pooled wet edge
    L.stroke = c;
  }
  { const [c, x] = cv(1920, 1080); lib.paper(x, { tone: "#F1ECE2", amount: 1, blotch: 0.09, tooth: 0.07, fiber: 1.0, seed: 17 }); L.paperMul = c; }
  // clouds: lifted pigment (paper colour) with a soft grey underside
  L.clouds = [0, 1, 2].map((k) => {
    const [c, x] = cv(560, 220), rr = lib.rng(20 + k);
    x.filter = "blur(10px)";
    for (let i = 0; i < 9; i++) { x.fillStyle = "rgba(244,238,223,0.75)"; x.beginPath(); x.ellipse(120 + rr() * 320, 90 + rr() * 50, 60 + rr() * 60, 36 + rr() * 26, 0, 0, TAU); x.fill(); }
    x.fillStyle = "rgba(142,143,181,0.18)"; x.beginPath(); x.ellipse(280, 150, 220, 26, 0, 0, TAU); x.fill();
    x.filter = "blur(1.5px)"; const r2 = lib.rng(40 + k);                                    // blooms: a thin darker tide mark where the water pushed pigment out
    for (let i = 0; i < 7; i++) { x.strokeStyle = "rgba(120,140,170,0.12)"; x.lineWidth = 1.6; x.beginPath(); x.ellipse(120 + r2() * 320, 90 + r2() * 50, 66 + r2() * 60, 40 + r2() * 26, 0, Math.PI * (0.9 + r2() * 0.2), Math.PI * (2.0 + r2() * 0.3)); x.stroke(); }
    return c;
  });
  // landscape layers (wider than the frame for the pan)
  const layer = (draw) => { const [c, x] = cv(2100, 1080); draw(x); return c; };
  L.far = layer((x) => wash(x, ridgePath(lib, 600, 60, 0.004, 1), P("extra.1"), 0.75, lib, { gran: 0.5, edge: 0.7 }));
  L.mid = layer((x) => { wash(x, lumps(lib, 700, 34, 34, 5), lib.mixColor(P("extra.2"), P("extra.1"), 0.35), 0.62, lib, { gran: 0.35, edge: 0.15 }); wash(x, lumps(lib, 712, 22, 22, 6), lib.mixColor(P("extra.2"), P("extra.4"), 0.4), 0.5, lib, { gran: 0.3 }); });
  L.meadow = layer((x) => {
    wash(x, ridgePath(lib, 760, 18, 0.002, 3), P("extra.3"), 0.85, lib, { gran: 0.5, edge: 0.6 });
    const warm = x.createRadialGradient(700, 800, 40, 700, 800, 700); warm.addColorStop(0, "rgba(242,196,109,0.2)"); warm.addColorStop(1, "rgba(242,196,109,0)");
    x.save(); x.clip(ridgePath(lib, 760, 18, 0.002, 3)); x.fillStyle = warm; x.fillRect(0, 700, 2100, 380); x.restore();   // light pooling where the sun lands
  });
  // grass: blade roots fixed with hash (positions never change)
  L.blades = Array.from({ length: 260 }, (_, i) => ({ x: -20 + i * 7.6 + lib.hash(3, i) * 6, y: 1066 + lib.hash(4, i) * 30, h: 46 + lib.hash(5, i) * 60, w: 3 + lib.hash(6, i) * 3, c: lib.hash(7, i) }));
  L.tufts = Array.from({ length: 90 }, (_, i) => ({ x: lib.hash(8, i) * 2000, y: 800 + lib.hash(9, i) * 90, h: 14 + lib.hash(10, i) * 20 }));
  // the motif tree, pre-rendered at three stages (canopy and trunk separate so the canopy can sway)
  L.tree = buildTree(lib, P);
  L.treeX = [540, 960, 1380]; L.treeY = 872; L.treeS = 1.32;
}

// the canopy is 4 leaf clumps (drawn back to front), each its own sprite so the wind can move them separately
const CLUMPS = [
  { x: -4, y: -214, lobes: [[0, 0, 60, 46], [32, 10, 40, 32]] },
  { x: -62, y: -160, lobes: [[0, 0, 54, 46], [-14, 22, 38, 30]] },
  { x: 58, y: -166, lobes: [[0, 0, 54, 44], [16, 22, 36, 28]] },
  { x: 6, y: -130, lobes: [[0, 0, 66, 38], [-40, 6, 34, 26], [42, 8, 30, 24]] },
];
function clumpPath(c) { const p = new Path2D(); for (const [x, y, rx, ry] of c.lobes) { p.moveTo(x + rx, y); p.ellipse(x, y, rx, ry, 0, 0, TAU); } return p; }
function trunkPath() { const p = new Path2D(); p.moveTo(-12, 0); p.quadraticCurveTo(-8, -60, -14, -110); p.lineTo(8, -112); p.quadraticCurveTo(4, -60, 12, 0); p.closePath(); return p; }
function outline(x, path, col, w, dx = 0, dy = 0) {           // outer silhouette only (no inner arcs), via stroke − fill
  const [oc, ox] = cv(x.canvas.width, x.canvas.height); ox.setTransform(x.getTransform()); ox.translate(dx, dy);
  ox.strokeStyle = col; ox.lineWidth = w; ox.lineCap = "round"; ox.stroke(path); ox.globalCompositeOperation = "destination-out"; ox.fill(path);
  x.save(); x.setTransform(1, 0, 0, 1, 0, 0); x.drawImage(oc, 0, 0); x.restore();
}
function buildTree(lib, P) {
  const trunkC = "#7A5A40", leaf = P("extra.3"), leafDk = P("extra.4"), shade = P("extra.5"), warm = P("accent"), pen = "rgba(90,86,80,0.85)";
  const mkT = (draw) => { const [c, x] = cv(360, 360); x.translate(180, 330); draw(x); return c; };
  const mkC = (draw) => { const [c, x] = cv(240, 200); x.translate(120, 100); draw(x); return c; };
  const rimOf = (c, col, a) => mkC((x) => {                     // leaves flipped by the gust: a light band on the upwind (left) edge
    const p = clumpPath(c); x.save(); x.clip(p); x.filter = "blur(2px)"; x.strokeStyle = col; x.globalAlpha = a; x.lineWidth = 16; x.stroke(p); x.restore();
    x.globalCompositeOperation = "destination-in"; const g = x.createLinearGradient(-90, 0, 30, 0); g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0,0)"); x.fillStyle = g; x.fillRect(-120, -100, 240, 200);
  });
  const stage = (k) => ({
    trunk: k === 0
      ? mkT((x) => { x.strokeStyle = pen; x.lineWidth = 1.6; x.stroke(trunkPath()); x.save(); x.translate(1.5, -1); x.stroke(trunkPath()); x.restore(); x.beginPath(); x.moveTo(-90, 2); x.lineTo(96, 0); x.stroke(); })
      : mkT((x) => { wash(x, trunkPath(), trunkC, 0.93, lib, { gran: 0.2 });
          if (k === 2) { x.save(); x.clip(trunkPath()); x.globalAlpha = 0.5; x.fillStyle = shade; x.fillRect(0, -120, 20, 130); x.restore();
            x.save(); x.filter = "blur(4px)"; x.globalAlpha = 0.35; x.fillStyle = shade; x.beginPath(); x.ellipse(40, 4, 110, 14, 0, 0, TAU); x.fill(); x.restore(); } }),
    clumps: CLUMPS.map((c, j) => ({
      c,
      img: mkC((x) => {
        const p = clumpPath(c);
        if (k === 0) { outline(x, p, pen, 3.2); outline(x, p, "rgba(90,86,80,0.5)", 2.4, 1.5, -1); return; }
        wash(x, p, lib.mixColor(leaf, leafDk, k === 1 ? 0.35 : 0.28 + 0.06 * j), 0.9, lib, { gran: 0.32, edge: 0 });
        unionEdge(x, p, lib.mixColor(leafDk, "#202030", 0.2), 0.5);
        if (k === 1) { outline(x, p, "rgba(90,86,80,0.4)", 2.4); return; }
        x.save(); x.clip(p); x.filter = "blur(6px)";
        x.globalAlpha = 0.55; x.fillStyle = lib.mixColor(leafDk, shade, 0.35); x.beginPath(); x.ellipse(24, 22, 60, 36, 0.3, 0, TAU); x.fill();     // shadow side (cool)
        x.globalAlpha = 0.5; x.fillStyle = lib.mixColor(leaf, warm, 0.45); x.beginPath(); x.ellipse(-22, -20, 40, 26, -0.3, 0, TAU); x.fill();       // lit side (warm)
        x.filter = "none"; x.globalAlpha = 0.8; x.fillStyle = leafDk;
        const rr = lib.rng(31 + j); for (let q = 0; q < 8; q++) { x.beginPath(); x.ellipse(-44 + rr() * 90, -30 + rr() * 60, 4 + rr() * 4, 3 + rr() * 2, rr() * 3, 0, TAU); x.fill(); }
        x.restore();
        if (j === 0 || j === 1) { x.fillStyle = "rgba(255,244,210,0.85)"; for (let q = 0; q < 4; q++) { x.beginPath(); x.arc(-34 + q * 11, -24 + (q % 2) * 8, 2.4, 0, TAU); x.fill(); } }
      }),
      rim: k === 0 ? null : rimOf(c, "#EEF4BC", k === 1 ? 0.6 : 0.85),
    })),
  });
  return [stage(0), stage(1), stage(2)];
}

// wind: one field for grass, tufts, trees and the gust sound
const gust = (t, lib) => 0.6 + 0.4 * (lib.noise1(t * 0.9, 5) * 0.5 + 0.5);
// one wave per gust in events.json (every 1.2 s), left→right, λ 1100 px: each crest passes the centre on its whoosh
const windAt = (x, t, lib) => (5 + 3 * gust(t, lib)) * Math.PI / 180 * 1.6 * Math.cos(TAU * ((t - S.gust[0]) / (S.gust[1] - S.gust[0]) - (x - 960) / 1100));

function landscape(ctx, t, lib, reveal = 1) {
  const P = L.P, pan = 14 * t;
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  lib.paper(ctx, { tone: P("bg"), amount: 1, blotch: 0.035, tooth: 0.045, fiber: 0.7, seed: 5 });
  // sky paints downward with a soft wet edge
  // one wide wet brush stroke of sky colour whips across the top (soft leading edge), fastest on events.json "stroke"
  // (≈ 70 % across, ~20 % of the frame, at 0.1 s), then the wash spreads down
  const bx = lib.tween(t, T.stroke - 0.1, T.stroke + 0.2, lib.ease.outCubic) * 2200 - 140;
  if (t >= T.stroke - 0.1) {
    const m = lib.offscreen("wc_stroke", (x) => { x.drawImage(L.stroke, 0, 0); x.globalCompositeOperation = "destination-in"; const gg = x.createLinearGradient(bx - 160, 0, bx, 0); gg.addColorStop(0, "rgba(0,0,0,1)"); gg.addColorStop(1, "rgba(0,0,0,0)"); x.fillStyle = gg; x.fillRect(0, 0, lib.W, 360); });
    ctx.drawImage(m, 0, 0);
  }
  const sy = lib.tween(t, 0.3, 0.9, lib.ease.outQuint) * 760;
  if (sy > 0) {
    const m = lib.offscreen("wc_sky", (x) => { x.drawImage(L.sky, 0, 0); x.globalCompositeOperation = "destination-in";
      const gg = x.createLinearGradient(0, sy - 90, 0, sy); gg.addColorStop(0, "rgba(0,0,0,1)"); gg.addColorStop(1, "rgba(0,0,0,0)"); x.fillStyle = gg; x.fillRect(0, 0, lib.W, lib.H); });
    ctx.drawImage(m, 0, 0);
  }
  // sun: warm light, upper left
  const sg = ctx.createRadialGradient(330, 170, 10, 330, 170, 460); sg.addColorStop(0, "rgba(255,226,160,0.75)"); sg.addColorStop(1, "rgba(255,226,160,0)");
  ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.fillStyle = sg; ctx.fillRect(0, 0, 900, 700); ctx.restore();   // light adds (no yellow-over-blue mud)
  // clouds drift left→right
  L.clouds.forEach((c, k) => ctx.drawImage(c, ((k * 700 + t * (10 + 3 * k)) % 2300) - 380, 60 + k * 90));
  const inL = (a, b) => lib.tween(t, a, b, lib.ease.outCubic);
  ctx.save(); ctx.globalAlpha = inL(0.3, 0.75); ctx.drawImage(L.far, -pan * 0.3, 0); ctx.restore();
  ctx.save(); ctx.globalAlpha = inL(0.42, 0.85); ctx.drawImage(L.mid, -pan * 0.5, 0); ctx.restore();
  ctx.save(); ctx.globalAlpha = inL(0.5, 0.95); ctx.drawImage(L.meadow, -pan, 0); ctx.restore();
  // cloud shadows sliding over the meadow (cool, multiplied), same speed as the clouds
  ctx.save(); ctx.globalCompositeOperation = "multiply"; ctx.globalAlpha = inL(0.5, 0.95);
  for (let k = 0; k < 2; k++) { const x = ((k * 900 + t * 28) % 2400) - 400, g = ctx.createRadialGradient(x, 860, 20, x, 860, 320); g.addColorStop(0, lib.rgba(P("extra.5"), 0.3)); g.addColorStop(1, lib.rgba(P("extra.5"), 0)); ctx.fillStyle = g; ctx.fillRect(x - 330, 740, 660, 260); }
  ctx.restore();
  // meadow tufts sway with the wind
  ctx.save(); ctx.globalAlpha = inL(0.5, 0.95); ctx.strokeStyle = lib.rgba(P("extra.4"), 0.55); ctx.lineCap = "round"; ctx.lineWidth = 2;
  for (const f of L.tufts) { const x = f.x - pan, a = windAt(x, t, lib) * 0.7; ctx.beginPath(); ctx.moveTo(x, f.y); ctx.lineTo(x + Math.sin(a) * f.h, f.y - Math.cos(a) * f.h); ctx.stroke(); }
  ctx.restore();
}
function grass(ctx, t, lib) {
  const P = L.P, rise = lib.tween(t, 0.55, 1.1, lib.ease.outCubic);
  if (rise <= 0) return;
  ctx.save(); ctx.lineCap = "round";
  for (const b of L.blades) {
    const x = b.x, a = windAt(x, t, lib) + 0.12, h = b.h * rise, tipx = x + Math.sin(a) * h, tipy = b.y - Math.cos(a) * h;
    const sheen = lib.clamp((a - 0.12) / 0.2) * 0.55;                                    // blades bent by the passing wave catch the light
    ctx.strokeStyle = lib.rgba(lib.mixColor(b.c < 0.5 ? P("extra.4") : lib.mixColor(P("extra.4"), P("extra.3"), 0.45), "#E8EFA8", sheen), 0.85);
    ctx.lineWidth = b.w; ctx.beginPath(); ctx.moveTo(x, b.y); ctx.quadraticCurveTo(x + Math.sin(a) * h * 0.4, b.y - h * 0.55, tipx, tipy); ctx.stroke();
  }
  ctx.restore();
}
const WMAX = 10 * Math.PI / 180 * 1.6;
function trees(ctx, t, lib) {
  L.tree.forEach((st, k) => {
    const t0 = 2.0 + k * 0.2; if (t < t0) return;
    const x = L.treeX[k], y = L.treeY, a = lib.tween(t, t0, t0 + 0.45, lib.ease.outQuint), S = L.treeS;
    ctx.save(); ctx.globalAlpha = a; ctx.translate(x, y); ctx.scale(S, S);
    ctx.drawImage(st.trunk, -180, -330);
    st.clumps.forEach(({ c, img, rim }, j) => {
      // each clump answers the wave where it stands, 0.4 s after the grass (plus a little per clump): sway, lean, squash
      const w = windAt(x + c.x * S, t - 0.4 - 0.05 * j, lib) / WMAX, hgt = (-c.y - 110) / 100;
      ctx.save(); ctx.translate(c.x + 15 * w * (0.6 + 0.6 * hgt), c.y - 3 * Math.abs(w)); ctx.rotate(0.07 * w); ctx.scale(1 + 0.05 * w, 1 - 0.04 * Math.abs(w));
      ctx.drawImage(img, -120, -100);
      if (rim && w > 0.12) { ctx.globalAlpha = a * Math.min(1, (w - 0.12) / 0.6); ctx.drawImage(rim, -120, -100); }
      ctx.restore();
    });
    ctx.restore();
  });
}
// petals and loose leaves carried left→right by the same wind (they cross the frame; none over the title band)
function petals(ctx, t, lib) {
  const P = L.P, cols = [P("extra.6"), lib.mixColor(P("extra.3"), P("extra.4"), 0.4), "#F2D27A"];
  for (let i = 0; i < 16; i++) {
    const ts = 0.9 + (i % 8) * 0.38 + Math.floor(i / 8) * 0.19, a = t - ts; if (a < 0) continue;
    const g = gust(t, lib), x = -40 + lib.hash(21, i) * 260 + a * (170 + 90 * lib.hash(22, i)) * (0.8 + 0.3 * g), y = 470 + lib.hash(23, i) * 360 + a * 22 + 18 * Math.sin(TAU * 0.6 * a + i);
    if (x > lib.W + 40) continue;
    ctx.save(); ctx.translate(x, y); ctx.rotate(a * (2 + lib.hash(24, i) * 3) + i); ctx.scale(1, 0.35 + 0.65 * Math.abs(Math.cos(a * 4 + i)));   // tumbling
    ctx.fillStyle = cols[i % 3]; ctx.globalAlpha = 0.9; ctx.beginPath(); ctx.ellipse(0, 0, 9 + 4 * lib.hash(25, i), 4.5, 0, 0, TAU); ctx.fill(); ctx.restore();
  }
}
function labels(ctx, t, tokens, lib) {
  const P = L.P;
  L.tree.forEach((st, k) => {
    const t0 = 2.0 + k * 0.2; if (t < t0) return;
    const x = L.treeX[k], y = L.treeY;
    ctx.save(); ctx.globalAlpha = lib.tween(t, t0 + 0.12, t0 + 0.5, lib.ease.outCubic); ctx.textAlign = "center";
    ctx.shadowColor = lib.rgba(P("bg"), 1); ctx.shadowBlur = 16;
    lib.setFont(ctx, tokens, "zh", 50, { weight: 400 }); ctx.fillStyle = P("fg"); ctx.fillText(lib.MOTIF[k].zh, x, y + 62); ctx.fillText(lib.MOTIF[k].zh, x, y + 62);
    lib.setFont(ctx, LAT, "en", 40); ctx.fillText(lib.MOTIF[k].en, x, y + 108); ctx.fillText(lib.MOTIF[k].en, x, y + 108);
    ctx.restore();
  });
}
function titles(ctx, t, tokens, lib) {
  const P = L.P;
  const line = (draw, x0, x1, ta, tb) => {                         // a soft wet edge moves left→right over the line
    const u = lib.tween(t, ta, tb, lib.ease.inOutSine); if (u <= 0) return;
    const edge = lib.lerp(x0 - 60, x1 + 60, u);
    const c = lib.offscreen("wc_title", (x) => { draw(x); x.globalCompositeOperation = "destination-in"; const g = x.createLinearGradient(edge - 70, 0, edge, 0); g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0,0)"); x.fillStyle = g; x.fillRect(0, 0, lib.W, lib.H); });
    ctx.drawImage(c, 0, 0);
  };
  lib.setFont(ctx, LAT, "en", 96); const wEN = ctx.measureText(lib.TITLE_EN).width;
  line((x) => { lib.setFont(x, LAT, "en", 96); x.fillStyle = P("fg"); x.textAlign = "center"; x.fillText(lib.TITLE_EN, lib.W / 2, 250); }, lib.W / 2 - wEN / 2, lib.W / 2 + wEN / 2, 0.8, 1.7);
  lib.setFont(ctx, tokens, "zh", 66); const wZH = ctx.measureText(lib.TITLE_ZH).width + 8 * 12;
  line((x) => { lib.setFont(x, tokens, "zh", 66); x.fillStyle = P("fg"); lib.drawText(x, lib.TITLE_ZH, lib.W / 2, 352, { align: "center", tracking: 12 }); }, lib.W / 2 - wZH / 2, lib.W / 2 + wZH / 2, 1.45, 2.35);
}

function scene(ctx, t, tokens, lib) { landscape(ctx, t, lib); titles(ctx, t, tokens, lib); trees(ctx, t, lib); grass(ctx, t, lib); petals(ctx, t, lib); labels(ctx, t, tokens, lib); }
function endFrame(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  lib.paper(ctx, { tone: P("bg"), amount: 1, blotch: 0.035, tooth: 0.045, fiber: 0.7, seed: 5 });
  ctx.save(); ctx.globalAlpha = 0.55; ctx.drawImage(L.far, -120, 40); ctx.restore();
  ctx.textAlign = "center"; ctx.fillStyle = P("fg");
  lib.setFont(ctx, tokens, "zh", 76); lib.drawText(ctx, "水彩田园", lib.W / 2, 470, { align: "center", tracking: 16 });
  lib.setFont(ctx, LAT, "en", 44); ctx.fillText("watercolor-pastoral", lib.W / 2, 546);
}

export function renderAt(t, ctx, tokens, lib) {
  if (t < T.bloom) scene(ctx, t, tokens, lib); else endFrame(ctx, t, tokens, lib);
  ctx.save(); ctx.globalCompositeOperation = "multiply"; ctx.globalAlpha = 0.55; ctx.drawImage(L.paperMul, 0, 0); ctx.restore();   // paper tooth and fibres over everything
  if (t >= T.bloom - 0.4) {                                              // light bloom: sun → warm paper white (on "bloom") → recede
    const up = lib.tween(t, T.bloom - 0.4, T.bloom, lib.ease.inOutSine), down = lib.tween(t, T.bloom, 5.0, lib.ease.outCubic), k = t < T.bloom ? up : 1 - down;
    const r = 200 + 2400 * (t < T.bloom ? up : 1);
    const g = ctx.createRadialGradient(330, 170, 0, 330, 170, r);
    g.addColorStop(0, `rgba(255,246,222,${k})`); g.addColorStop(0.6, `rgba(250,236,200,${k * 0.96})`); g.addColorStop(1, `rgba(250,236,200,${k * 0.6})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, lib.W, lib.H);
  }
}
