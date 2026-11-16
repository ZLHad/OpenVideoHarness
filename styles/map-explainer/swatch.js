// 立体地图解说 · map-explainer — swatch spec 2 (8 s, four beats, landscape and portrait).
//
// A shaded-relief map of a coast: mountains lit from the north-west, valleys, rivers running to the sea, a shelf of
// shallow water. The camera starts high over the whole region and pushes in, tilting down so the relief stands up; a
// route grows along the main river, over a pass and down to a lake, one leg at a time, each stop marked with its
// number and its height read off the terrain. The title sits in the map's legend box; in the close the route fades and
// the camera rises back to the first frame.
//
//   0.0–1.5  world      the whole region from high up; the push and the tilt begin at once (the first big move)
//   1.5–4.5  signature  the route grows leg by leg (river mouth → valley → pass → lake), the camera following its head
//   4.5–7.0  type       the legend box drops in with the title, a scale bar and north; the caption; read once
//   7.0–8.0  close      the route and labels fade; the camera rises back to the whole region
//
// The terrain is generated here (seeded noise, a mountain range, carved river valleys and a saddle), so there is no
// real place on it and no border to get wrong. The relief is a texture shaded once in setup; each frame lays it in
// perspective row by row. One timing table (T) drives picture, foley and reads.

const T = {
  legs: [[1.55, 2.35], [2.6, 3.4], [3.6, 4.3]], stops: [1.5, 2.35, 3.4, 4.3],
  legend: 4.45, title: 4.55, caption: 4.75, read: [4.95, 7.0], fade: [7.0, 7.3], rise: [7.0, 7.95],
};
const TW = 3072, TH = 1920, KM = 120;                     // the relief texture (px) and how many km it spans across
const STOPS = [   // texture fractions; the label and which side it sits on
  { at: [0.305, 0.635], zh: "河口", side: [-1, 1] },
  { at: [0.505, 0.522], zh: "河谷", side: [-1, -1] },
  { at: [0.672, 0.452], zh: "垭口", side: [1, -1] },
  { at: [0.842, 0.53], zh: "湖岸", side: [1, 1] },
];
const RIVER_MAIN = [[0.28, 0.66], [0.33, 0.62], [0.38, 0.6], [0.43, 0.55], [0.49, 0.52], [0.55, 0.47], [0.6, 0.43], [0.64, 0.4]];
const RIVERS = [RIVER_MAIN, [[0.12, 0.88], [0.18, 0.8], [0.25, 0.77], [0.33, 0.71], [0.41, 0.69], [0.47, 0.73], [0.53, 0.72]],
  [[0.36, 0.3], [0.41, 0.24], [0.47, 0.22], [0.52, 0.17], [0.58, 0.16]], [[0.95, 0.62], [0.9, 0.57], [0.865, 0.535]]];

const pan = (u) => Math.round((2 * u - 1) * 70) / 100;
export const FOLEY = [
  { t: 0.7, sfx: "air", gain_db: -11, dur: 1.6, dir: "down", tone: 0.2, bright: -0.3, pan: 0 },                 // high wind as we push in
  ...T.legs.map(([a, b], k) => ({ t: (a + b) / 2, sfx: "swoosh_tonal", gain_db: -13, dur: b - a, dir: "up", tone: 0.3, pan_from: pan(0.3 + k * 0.2), pan_to: pan(0.45 + k * 0.2) })),
  ...T.stops.map((t, k) => ({ t, sfx: "pop", gain_db: -9, role: "hero", pitch: [-2, 1, 4, 6][k], pan: pan([0.3, 0.5, 0.67, 0.84][k]) })),
  { t: T.legend + 0.18, sfx: "paper", gain_db: -10, dur: 0.25, bright: -0.2, pan: -0.5 },                       // the legend lands
  { t: 7.45, sfx: "air", gain_db: -11, dur: 0.9, dir: "up", tone: 0.2, pan: 0 },                                 // rising away
];

export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: T.read[0], end: T.read[1] },
    { text: lib.TITLE_EN, start: T.read[0], end: T.read[1] },
    { text: lib.CAPTION_ZH, start: T.read[0], end: T.read[1] },
  ];
}

// ── the terrain (setup) ───────────────────────────────────────────────────────────────────────────────────────────
let L = null;

function segDist(px, py, ax, ay, bx, by) {
  const dx = bx - ax, dy = by - ay, l2 = dx * dx + dy * dy, u = l2 ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / l2)) : 0;
  return Math.hypot(px - ax - u * dx, py - ay - u * dy);
}
function polyDist(px, py, pts) { let d = Infinity; for (let i = 1; i < pts.length; i++) d = Math.min(d, segDist(px, py, ...pts[i - 1], ...pts[i])); return d; }

/** Height (sea level 0, peaks about 1) on a coarse grid, in texture fractions. */
function heightGrid(lib, gw, gh) {
  const { fbm2, noise2, clamp } = lib, h = new Float32Array(gw * gh);
  const ridged = (x, y) => { let s = 0, a = 0.5, f = 1; for (let o = 0; o < 5; o++) { const n = 1 - Math.abs(noise2(x * f, y * f, 70 + o)); s += a * n * n; a *= 0.5; f *= 2.03; } return s; };
  for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
    const x = i / gw, y = j / gh, k = j * gw + i;
    // land rises to the east; the coast is ragged
    let base = (x - 0.3) * 1.25 + 0.18 * fbm2(x * 5, y * 5, { octaves: 5, seed: 2 }) + 0.12 * (y < 0.25 ? (0.25 - y) * 2 : 0);
    // a range running north-north-east, with a saddle where the route crosses
    const dr = segDist(x, y, 0.58, 0.02, 0.78, 0.98);
    const range = Math.exp(-((dr / 0.085) ** 2));
    const saddle = 1 - 0.55 * Math.exp(-(((x - 0.672) / 0.05) ** 2 + ((y - 0.452) / 0.07) ** 2));
    // spurs: ridged noise stretched along the crest, so its ridges run down the flanks (warped a little)
    const ca = 0.2, along = x * Math.sin(ca) + y * Math.cos(ca), across = x * Math.cos(ca) - y * Math.sin(ca);
    const wa = along + 0.07 * fbm2(x * 9, y * 9, { octaves: 3, seed: 31 }), wb = across + 0.05 * fbm2(x * 9 + 5, y * 9, { octaves: 3, seed: 32 });
    const spurs = ridged(wa * 10, wb * 6.5) * 0.55 + ridged(x * 8, y * 8) * 0.45;
    let v = base * 0.55 + range * saddle * (0.28 + 0.7 * spurs) + 0.06 * ridged(x * 13, y * 13) * clamp(base * 2);
    // carve the river valleys (the main one deeper), keep them above the sea until the mouth
    for (const [r, pts] of RIVERS.entries()) {
      const d = polyDist(x, y, pts), w = r === 0 ? 0.03 : 0.02;
      v -= (r === 0 ? 0.32 : 0.2) * Math.exp(-((d / w) ** 2)) * clamp(v * 1.4 + 0.2);
    }
    // the lake east of the pass
    v -= 0.42 * Math.exp(-(((x - 0.885) / 0.045) ** 2 + ((y - 0.56) / 0.04) ** 2));
    h[k] = v;
  }
  return h;
}

export async function setup(ctx, tokens, lib) {
  const { clamp, rgb, noise2 } = lib;
  const P = (k) => lib.color(tokens, k);
  const gw = 1536, gh = 960, hg = heightGrid(lib, gw, gh);
  const sample = (x, y) => {                                 // bilinear on the coarse grid (texture fractions)
    const fx = clamp(x, 0, 0.9999) * (gw - 1), fy = clamp(y, 0, 0.9999) * (gh - 1), i = Math.floor(fx), j = Math.floor(fy), u = fx - i, v = fy - j;
    const a = hg[j * gw + i], b = hg[j * gw + i + 1], c = hg[(j + 1) * gw + i], d = hg[(j + 1) * gw + i + 1];
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
  };
  L = { sample };
  // full-resolution height: the coarse field plus a fine octave on land
  const H = new Float32Array(TW * TH);
  for (let j = 0; j < TH; j++) for (let i = 0; i < TW; i++) {
    const x = i / TW, y = j / TH, v = sample(x, y);
    H[j * TW + i] = v + (v > 0 ? clamp(v * 8) * 0.006 * noise2(i / 14, j / 14, 91) : 0);   // fine relief, none at the shore
  }
  // shade: Imhof-style relief, light from the north-west, hypsometric tints, the sea by depth
  const img = new ImageData(TW, TH), tint = [
    [-0.4, P("sea_deep")], [-0.07, P("sea")], [0, P("shallow")], [0.01, P("sand")], [0.05, P("low")], [0.3, P("mid")], [0.6, P("high")], [0.9, P("rock")], [1.2, P("snow")],
  ].map(([h, c]) => [h, rgb(c)]);
  const tintAt = (h) => {
    if (h <= tint[0][0]) return tint[0][1];
    for (let k = 1; k < tint.length; k++) if (h <= tint[k][0]) { const [h0, c0] = tint[k - 1], [h1, c1] = tint[k], u = (h - h0) / (h1 - h0); return [0, 1, 2].map((n) => c0[n] + (c1[n] - c0[n]) * u); }
    return tint[tint.length - 1][1];
  };
  const LX = -0.62, LY = -0.62, LZ = 0.48, EX = 20;          // light from the north-west, 29° up; vertical exaggeration
  for (let j = 0; j < TH; j++) for (let i = 0; i < TW; i++) {
    const k = j * TW + i, h = H[k];
    const hx = H[j * TW + Math.min(TW - 1, i + 1)] - H[j * TW + Math.max(0, i - 1)], hy = H[Math.min(TH - 1, j + 1) * TW + i] - H[Math.max(0, j - 1) * TW + i];
    const nx = -hx * EX, ny = -hy * EX, nl = Math.hypot(nx, ny, 1), sh = clamp((nx * LX + ny * LY + LZ) / nl / 0.62);
    let c = tintAt(h);
    if (h > 0) {
      const contrast = 0.5 + 0.9 * clamp(h);                 // higher ground gets the harder light (Imhof's aerial perspective)
      const m = 1 + (sh - 0.62) * contrast * 1.25;
      c = [c[0] * m - (1 - sh) * 10, c[1] * m - (1 - sh) * 4, c[2] * m + (1 - sh) * 12];   // shadows lean blue
    } else {
      const m = 1 + (sh - 0.62) * 0.18;                      // the sea floor barely shows
      c = c.map((v) => v * m);
      if (h > -0.004) c = c.map((v) => v + 22 * (1 + h / 0.004));   // a faint surf line
    }
    img.data[k * 4] = clamp(c[0], 0, 255); img.data[k * 4 + 1] = clamp(c[1], 0, 255); img.data[k * 4 + 2] = clamp(c[2], 0, 255); img.data[k * 4 + 3] = 255;
  }
  const tex = document.createElement("canvas"); tex.width = TW; tex.height = TH;
  const x = tex.getContext("2d"); x.putImageData(img, 0, 0);
  // the rivers: thin and pale at the source, wider to the mouth
  x.lineCap = "round"; x.lineJoin = "round";
  for (const pts of RIVERS) {
    const fine = [];
    for (let i = 1; i < pts.length; i++) for (let s = 0; s < 12; s++) {
      const u = s / 12, px = pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * u, py = pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * u;
      fine.push([px * TW + 9 * noise2(px * 40, py * 40, 5), py * TH + 9 * noise2(px * 40, py * 40, 6)]);
    }
    fine.reverse();                                           // from the source down
    for (let i = 1; i < fine.length; i++) {
      const u = i / fine.length;
      x.strokeStyle = lib.rgba(P("river"), 0.6 + 0.4 * u); x.lineWidth = 1.6 + (pts === RIVER_MAIN ? 7 : 4.5) * u;
      x.beginPath(); x.moveTo(...fine[i - 1]); x.lineTo(...fine[i]); x.stroke();
    }
  }
  L.tex = tex;
  // the route: through the stops along the valley, smoothed; each leg its own polyline in texture px
  L.legs = [];
  const via = [[STOPS[0].at, [0.36, 0.625], [0.43, 0.57], STOPS[1].at], [STOPS[1].at, [0.56, 0.47], [0.62, 0.445], STOPS[2].at], [STOPS[2].at, [0.72, 0.47], [0.79, 0.5], STOPS[3].at]];
  for (const ctrl of via) {
    const pts = [];
    for (let i = 0; i < ctrl.length - 1; i++) {
      const p0 = ctrl[Math.max(0, i - 1)], p1 = ctrl[i], p2 = ctrl[i + 1], p3 = ctrl[Math.min(ctrl.length - 1, i + 2)];
      for (let s = 0; s < 14; s++) {
        const u = s / 14, u2 = u * u, u3 = u2 * u, f = (a, b, c, d) => 0.5 * (2 * b + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u2 + (-a + 3 * b - 3 * c + d) * u3);
        pts.push([f(p0[0], p1[0], p2[0], p3[0]) * TW, f(p0[1], p1[1], p2[1], p3[1]) * TH]);
      }
    }
    pts.push([ctrl[ctrl.length - 1][0] * TW, ctrl[ctrl.length - 1][1] * TH]);
    L.legs.push(pts);
  }
  // each stop's height, read off the terrain (metres; the scale is 2 800 m at h = 1)
  L.elev = STOPS.map((s) => Math.max(0, Math.round((sample(...s.at) * 2800) / 10) * 10));
  lib.setFont(ctx, tokens, "zh", lib.TYPE.title, { weight: 700 });
  L.titleW = ctx.measureText(lib.PORTRAIT ? "都是代码。" : lib.TITLE_ZH).width;
}

// ── camera ────────────────────────────────────────────────────────────────────────────────────────────────────────
function camera(t, lib) {
  const { seg, lerp, ease, PORTRAIT } = lib;
  // landscape: the whole region fills the frame; portrait: its full height does, and the camera follows the route east
  const s0 = PORTRAIT ? 1920 / TH : 1920 / TW;
  const K = PORTRAIT ? [
    [0, 0.42, 0.5, s0, 0], [1.5, 0.37, 0.58, s0 * 1.1, 12], [4.45, 0.75, 0.52, s0 * 1.4, 30], [7.0, 0.765, 0.52, s0 * 1.45, 32], [7.95, 0.42, 0.5, s0, 0],
  ] : [
    [0, 0.5, 0.5, s0, 0], [1.5, 0.42, 0.56, s0 * 1.28, 14], [4.45, 0.61, 0.5, s0 * 1.85, 35], [7.0, 0.625, 0.5, s0 * 1.92, 37], [7.95, 0.5, 0.5, s0, 0],
  ];
  let i = 0; while (i < K.length - 2 && t > K[i + 1][0]) i++;
  const [t0, u0, v0, z0, p0] = K[i], [t1, u1, v1, z1, p1] = K[i + 1];
  const e = i === 2 ? ease.inOutSine : ease.inOutCubic;
  const u = e(seg(t, t0, t1));
  // zoom eases in log space so the push feels even
  return { uc: lerp(u0, u1, u) * TW, vc: lerp(v0, v1, u) * TH, s: Math.exp(lerp(Math.log(z0), Math.log(z1), u)), p: (lerp(p0, p1, u) * Math.PI) / 180 };
}
/** Texture px → screen px for a camera, with the scale there (for widths). */
function projector(cam, lib) {
  const { W, H, PORTRAIT } = lib, F = 1500, cx = W / 2, cy = H * (PORTRAIT ? 0.5 : 0.52), sp = Math.sin(cam.p), cp = Math.cos(cam.p);
  return (u, v) => {
    const X = (u - cam.uc) * cam.s, Y = (v - cam.vc) * cam.s, g = F / (F - Y * sp);
    return [cx + X * g, cy + Y * cp * g, g * cam.s];
  };
}

// ── frame ─────────────────────────────────────────────────────────────────────────────────────────────────────────
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib, P = (k) => lib.color(tokens, k);
  const cam = camera(t, lib), pr = projector(cam, lib);
  ctx.fillStyle = P("haze"); ctx.fillRect(0, 0, W, H);       // beyond the map's far edge: haze, as at a horizon
  relief(ctx, cam, lib);
  haze(ctx, cam, tokens, lib);
  route(ctx, t, pr, tokens, lib);
  legend(ctx, t, cam, tokens, lib);
  caption(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 12, seed: 17 });
  lib.vignette(ctx, { strength: 0.32, inner: 0.55, color: "#0b1a22" });
}

/** The relief laid in perspective: one source row per two screen rows (a tilted plane, "mode 7"). */
function relief(ctx, cam, lib) {
  const { W, H, PORTRAIT } = lib, F = 1500, cx = W / 2, cy = H * (PORTRAIT ? 0.5 : 0.52), sp = Math.sin(cam.p), cp = Math.cos(cam.p), STEP = 2;
  ctx.save(); ctx.imageSmoothingQuality = "high";
  for (let y = 0; y < H; y += STEP) {
    const q = y + STEP / 2 - cy, Y = (q * F) / (F * cp + q * sp), g = F / (F - Y * sp);
    if (!(g > 0) || !Number.isFinite(g)) continue;
    const v = cam.vc + Y / cam.s, dv = (STEP / (cp * g)) / cam.s;
    const u0 = cam.uc + (0 - cx) / (g * cam.s), u1 = cam.uc + (W - cx) / (g * cam.s);
    // clip the source to the texture; the screen span follows
    const su0 = Math.max(0, u0), su1 = Math.min(TW, u1), sv = v - dv / 2;
    if (su1 <= su0 || sv + dv < 0 || sv > TH) continue;
    const x0 = ((su0 - u0) / (u1 - u0)) * W, x1 = ((su1 - u0) / (u1 - u0)) * W;
    ctx.drawImage(L.tex, su0, Math.max(0, sv), su1 - su0, Math.max(0.5, Math.min(dv, TH - sv)), x0, y, x1 - x0, STEP + 0.5);
  }
  ctx.restore();
}

/** Distance haze: the far (upper) part of a tilted map pales toward the sky. */
function haze(ctx, cam, tokens, lib) {
  const k = Math.sin(cam.p);
  if (k < 0.02) return;
  const { W, H } = lib, g = ctx.createLinearGradient(0, 0, 0, H * 0.55);
  g.addColorStop(0, lib.rgba(lib.color(tokens, "haze"), 0.75 * k)); g.addColorStop(1, lib.rgba(lib.color(tokens, "haze"), 0));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H * 0.55);
}

/** The route: a tapered band drawn leg by leg with an arrowhead at its head; numbered stops with their height. */
function route(ctx, t, pr, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const fade = 1 - lib.seg(t, ...T.fade);
  if (fade <= 0 || t < T.stops[0]) return;
  ctx.save(); ctx.globalAlpha = fade; ctx.lineCap = "round"; ctx.lineJoin = "round";
  T.legs.forEach(([a, b], k) => {
    const u = lib.ease.inOutSine(lib.seg(t, a, b));
    if (u <= 0) return;
    const pts = L.legs[k], n = Math.max(2, Math.ceil(u * (pts.length - 1)));
    const sp = pts.slice(0, n).map(([x, y]) => pr(x, y));
    // the band: a dark edge under a warm fill, width in map px times the local scale
    for (const [col, wmul] of [[P("route_edge"), 1.5], [P("route"), 1]]) {
      ctx.strokeStyle = col;
      for (let i = 1; i < sp.length; i++) {
        ctx.lineWidth = 10 * sp[i][2] * wmul + 2; ctx.beginPath(); ctx.moveTo(sp[i - 1][0], sp[i - 1][1]); ctx.lineTo(sp[i][0], sp[i][1]); ctx.stroke();
      }
    }
    if (u < 1 && sp.length > 2) {                             // the head
      const [hx, hy, hs] = sp[sp.length - 1], [bx, by] = sp[sp.length - 3], ang = Math.atan2(hy - by, hx - bx), r = 30 * hs + 12;
      ctx.fillStyle = P("route"); ctx.strokeStyle = P("route_edge"); ctx.lineWidth = 3;
      ctx.beginPath(); ctx.moveTo(hx + Math.cos(ang) * r, hy + Math.sin(ang) * r);
      ctx.lineTo(hx + Math.cos(ang + 2.5) * r * 0.8, hy + Math.sin(ang + 2.5) * r * 0.8); ctx.lineTo(hx + Math.cos(ang - 2.5) * r * 0.8, hy + Math.sin(ang - 2.5) * r * 0.8);
      ctx.closePath(); ctx.fill(); ctx.stroke();
    }
  });
  // the stops: a pin, the number, the name and the height off the terrain; names step back while the title reads
  const quiet = 1 - 0.7 * lib.ease.inOutSine(lib.seg(t, T.legend, T.legend + 0.4));
  STOPS.forEach((s, k) => {
    const t0 = T.stops[k]; if (t < t0) return;
    const [x, y] = pr(s.at[0] * TW, s.at[1] * TH), sc = lib.spring(t - t0, { w: 20, zeta: 0.55 });
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc);
    ctx.fillStyle = P("pin"); ctx.strokeStyle = P("route_edge"); ctx.lineWidth = 4;
    ctx.beginPath(); ctx.arc(0, 0, 21, 0, Math.PI * 2); ctx.fill(); ctx.stroke();
    lib.setFont(ctx, tokens, "num", 26, { weight: 700 }); ctx.fillStyle = P("route_edge"); ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(String(k + 1), 0, 1.5);
    ctx.restore();
    const a = lib.clamp((t - t0 - 0.12) / 0.2) * quiet;
    if (a <= 0) return;
    ctx.save(); ctx.globalAlpha = fade * a;
    // the label goes on its side, unless that side would leave the safe frame
    const A = lib.SAFE.action;
    lib.setFont(ctx, tokens, "zh", 46, { weight: 600 });
    const tw = Math.max(ctx.measureText(s.zh).width, 130);
    let side = s.side[0];
    if (side < 0 && x - 34 - tw < A.x0) side = 1; else if (side > 0 && x + 34 + tw > A.x1) side = -1;
    const lx = x + side * 34, ly = lib.clamp(y + s.side[1] * 50, A.y0 + 30, A.y1 - 90);
    ctx.textAlign = side > 0 ? "left" : "right"; ctx.textBaseline = "middle";
    ctx.lineJoin = "round"; ctx.strokeStyle = lib.rgba(P("halo"), 0.85); ctx.lineWidth = 8;
    ctx.strokeText(s.zh, lx, ly); ctx.fillStyle = P("label"); ctx.fillText(s.zh, lx, ly);
    lib.setFont(ctx, tokens, "num", 28, { weight: 600 });
    const ey = ly + 50, txt = `${L.elev[k].toLocaleString("en-US")} m`;
    ctx.lineWidth = 6; ctx.strokeText(txt, lx, ey); ctx.fillStyle = P("label"); ctx.fillText(txt, lx, ey);
    ctx.restore();
  });
  ctx.restore();
}

/** The legend box: title, the English line, a scale bar measured at the view's centre, a north arrow. */
function legend(ctx, t, cam, tokens, lib) {
  if (t < T.legend) return;
  const P = (k) => lib.color(tokens, k), { TYPE, SAFE, PORTRAIT } = lib;
  const out = 1 - lib.seg(t, T.fade[0] - 0.02, T.fade[0] + 0.2);
  if (out <= 0) return;
  const h = lib.spring(t - T.legend, { w: 18, zeta: 0.7 });
  const lines = PORTRAIT ? ["每一帧，", "都是代码。"] : [lib.TITLE_ZH];
  const bw = L.titleW + 120, bh = lines.length * TYPE.title * 1.18 + TYPE.label * 1.5 + 150;
  const x0 = SAFE.title.x0 - 30, y0 = PORTRAIT ? SAFE.title.y0 + 40 : SAFE.title.y0 - 20;
  ctx.save(); ctx.globalAlpha = out * lib.clamp((t - T.legend) / 0.1);
  ctx.translate(0, (1 - h) * -40);
  ctx.shadowColor = "rgba(10,20,25,0.45)"; ctx.shadowBlur = 24; ctx.shadowOffsetY = 8;
  ctx.fillStyle = lib.rgba(P("legend"), 0.94); ctx.fillRect(x0, y0, bw, bh);
  ctx.shadowColor = "transparent";
  ctx.strokeStyle = P("ink"); ctx.lineWidth = 2; ctx.strokeRect(x0 + 10, y0 + 10, bw - 20, bh - 20);
  // title and English line
  lib.setFont(ctx, tokens, "zh", TYPE.title, { weight: 700 }); ctx.fillStyle = P("ink"); ctx.textBaseline = "alphabetic";
  const tx = x0 + 60, ty = y0 + 40 + TYPE.title;
  lines.forEach((ln, i) => {
    const lay = lib.layoutText(ctx, ln, { x: tx, y: ty + i * TYPE.title * 1.18, align: "left" });
    lib.drawGlyphs(ctx, lay, (g, j) => { const t0 = T.title + (i * 5 + j) * 0.03; return t < t0 ? null : { alpha: lib.clamp((t - t0) / 0.14) }; });
  });
  const ey = ty + (lines.length - 1) * TYPE.title * 1.18 + TYPE.label * 1.45;
  lib.setFont(ctx, tokens, "en", TYPE.label, { style: "italic" }); ctx.fillStyle = P("ink_soft");
  ctx.globalAlpha = out * lib.clamp((t - T.title - 0.25) / 0.2);
  ctx.fillText(lib.TITLE_EN, tx, ey);
  // scale bar: 10 km at the view's centre, and north
  const km = (TW / KM) * cam.s, bar = 10 * km, by = y0 + bh - 46;
  ctx.globalAlpha = out;
  ctx.fillStyle = P("ink"); ctx.fillRect(tx, by, bar / 2, 8); ctx.strokeStyle = P("ink"); ctx.lineWidth = 2; ctx.strokeRect(tx, by, bar, 8);
  lib.setFont(ctx, tokens, "num", 26, { weight: 600 }); ctx.textBaseline = "middle"; ctx.fillText("10 km", tx + bar + 16, by + 4);
  const nx = x0 + bw - 70, ny = by - 6;
  ctx.beginPath(); ctx.moveTo(nx, ny - 34); ctx.lineTo(nx + 12, ny + 6); ctx.lineTo(nx, ny - 2); ctx.lineTo(nx - 12, ny + 6); ctx.closePath(); ctx.fill();
  ctx.textAlign = "center"; ctx.fillText("N", nx, ny - 52);
  ctx.restore();
}

function caption(ctx, t, tokens, lib) {
  const a = lib.clamp((t - T.caption) / 0.15) * (1 - lib.seg(t, T.fade[0] - 0.02, T.fade[0] + 0.2));
  if (a <= 0 || t < T.caption) return;
  const P = (k) => lib.color(tokens, k), { W, SAFE, TYPE } = lib;
  const y = SAFE.title.y1 - TYPE.caption * 0.55;
  ctx.save(); ctx.globalAlpha = a;
  lib.setFont(ctx, tokens, "zh", TYPE.caption, { weight: 500 });
  const w = ctx.measureText(lib.CAPTION_ZH).width + 70;
  ctx.fillStyle = lib.rgba(P("ink"), 0.62); ctx.fillRect(W / 2 - w / 2, y - TYPE.caption * 0.85, w, TYPE.caption * 1.7);
  ctx.fillStyle = P("legend"); ctx.textBaseline = "middle";
  lib.drawText(ctx, lib.CAPTION_ZH, W / 2, y, { align: "center" });
  ctx.restore();
}
