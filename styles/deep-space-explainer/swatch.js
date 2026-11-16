// Deep-space explainer: a dark field where every kind of thing keeps one colour for the whole film. Light is gold,
// matter is coral, we (the observers, our planet's air and instruments) are blue; the legend says so once and the
// picture keeps its word. The big shots are shaders: a black hole whose disk is lensed over and under its shadow, and
// the Earth at night.
//
//   0.0–1.5  world      deep space: stars on three depths, a faint band of galaxy; a front of gold light enters and
//                       the camera drifts in after it
//   1.5–4.5  signature  the black hole (a ray-marched shader): the gold rays bend round it, one falls in; the camera
//                       follows one bent ray across the dark to the Earth, where it lands and a blue ring answers
//   4.5–7.5  type       the title over the Earth's limb, its English line, the caption on a soft band
//   7.5–9.0  close      the camera pulls away into the stars; the last frame is the first again (the star field
//                       repeats every 12 000 px of travel, and the camera has travelled exactly that)
//
// One table (T) drives camera, rays, foley and reads.

import { smear } from "../../vendor/hand.js";

export const fonts = ["Songti SC", "Avenir Next", "PingFang SC"];

const T = {
  rays: 0.1, v: 1850,                                   // the light front leaves at 0.1 s, at 1850 world px a second
  legend: [1.7, 0.18], land: 4.58,                      // the colour key, item by item; the ray lands on the Earth
  title: [4.6, 0.5], en: [4.95, 0.4], caption: [5.05, 0.35],   // [start, how long the focus pull takes]
  read: 7.5, away: [7.5, 8.97],
};
const PX = 12000;                                        // the camera's whole journey; the stars repeat after it
export const FOLEY = [
  { t: T.rays, sfx: "sfx/light_front.wav", gain_db: -6, pan_from: -0.7, pan_to: 0.2, role: "hero" },
  { t: 2.15, sfx: "sfx/hole_hum.wav", gain_db: -16, pan: 0.1, role: "ambience" },
  { t: 2.62, sfx: "swish_rev", gain_db: -11, dur: 0.5, pan: 0.0 },                       // the captured ray goes in
  { t: 3.45, sfx: "whoosh", gain_db: -9, dur: 1.0, dir: "down", pan_from: -0.3, pan_to: 0.5 },   // the camera follows the ray
  { t: T.land, sfx: "sfx/detect.wav", gain_db: -5, pan: 0.2, role: "hero" },
  ...[0, 1, 2].map((k) => ({ t: +(T.legend[0] + k * T.legend[1]).toFixed(3), sfx: "tick", gain_db: -5, pan: -0.6, role: "detail" })),
  { t: T.away[0] + 0.05, sfx: "air", gain_db: -12, dur: 1.2, dir: "down", pan_from: 0.4, pan_to: -0.4 },
];

export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: +(T.title[0] + T.title[1]).toFixed(3), end: T.read },
    { text: lib.TITLE_EN, start: +(T.en[0] + T.en[1]).toFixed(3), end: T.read },
    { text: lib.CAPTION_ZH, start: +(T.caption[0] + T.caption[1]).toFixed(3), end: T.read },
  ];
}

// ── shaders ─────────────────────────────────────────────────────────────────────────────────────────────────────────
// The black hole: rays from the camera are bent by x'' = -1.5 h² x / r⁵ (units of the Schwarzschild radius; a photon's
// path round a non-spinning hole), stepped until they cross the disk plane, fall below r = 1, or escape. The disk is
// matter, so it is coral; the shadow is black; nothing else is drawn (the stars behind are the 2D layer).
const HOLE = `
uniform float u_incl, u_dist, u_fov, u_spin;
uniform vec3 u_hot, u_mat;
float h21(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
  return mix(mix(h21(i), h21(i+vec2(1,0)), f.x), mix(h21(i+vec2(0,1)), h21(i+vec2(1,1)), f.x), f.y); }
void main(){
  vec2 p = (v_uv - 0.5) * u_fov;
  vec3 ro = vec3(0.0, sin(u_incl), cos(u_incl)) * u_dist;
  vec3 fw = normalize(-ro), rt = normalize(cross(fw, vec3(0,1,0))), up = cross(rt, fw);
  vec3 pos = ro, vel = normalize(fw + p.x*rt + p.y*up);
  float h2 = dot(cross(pos, vel), cross(pos, vel));
  vec3 col = vec3(0.0); float tr = 1.0;
  for (int i = 0; i < 96; i++) {
    float r2 = dot(pos, pos), r = sqrt(r2);
    if (r < 1.0) { tr = 0.0; break; }
    float st = clamp(0.12 * r, 0.04, 1.2);
    vel += -1.5 * h2 * pos / (r2 * r2 * r) * st;
    vec3 np = pos + vel * st;
    if (pos.y * np.y < 0.0) {
      vec3 hit = mix(pos, np, pos.y / (pos.y - np.y));
      float rr = length(hit.xz);
      if (rr > 3.0 && rr < 10.5) {
        float ph = atan(hit.z, hit.x) + u_spin * 2.2 / pow(rr, 1.5);
        float band = 0.55 + 0.45 * vn(vec2(rr * 2.6, ph * 3.0)) * vn(vec2(rr * 7.0, ph * 9.0 + 3.0));
        vec3 vd = normalize(vec3(-sin(atan(hit.z, hit.x)), 0.0, cos(atan(hit.z, hit.x))));
        float beam = clamp(1.0 + 1.6 * dot(vd, -normalize(vel)) * inversesqrt(rr), 0.25, 2.4);   // the side coming at us is brighter
        float heat = smoothstep(10.5, 3.0, rr);
        vec3 c = mix(u_mat, u_hot, heat * heat) * band * beam * (0.35 + 1.1 * heat);
        float a = smoothstep(3.0, 3.6, rr) * smoothstep(10.5, 8.5, rr) * 0.92;
        col += tr * a * c; tr *= 1.0 - a;
      }
    }
    pos = np;
    if (r > 60.0 && dot(pos, vel) > 0.0) break;
  }
  float al = 1.0 - tr;
  outColor = vec4(al > 0.0 ? col / max(al, 1e-4) : vec3(0.0), al);
}`;

// The Earth at night, lit from the upper left: dim slate land and dark sea from 3D value noise, a little ice and cloud,
// the cities on the night side and the air at the rim in the observers' blue.
const EARTH = `
uniform vec2 u_c; uniform float u_r, u_rot; uniform vec3 u_sun, u_blue;
float h31(vec3 p){ return fract(sin(dot(p, vec3(127.1, 311.7, 74.7))) * 43758.5453); }
float vn3(vec3 p){ vec3 i = floor(p), f = fract(p); f = f*f*(3.0-2.0*f);
  float a = mix(mix(h31(i), h31(i+vec3(1,0,0)), f.x), mix(h31(i+vec3(0,1,0)), h31(i+vec3(1,1,0)), f.x), f.y);
  float b = mix(mix(h31(i+vec3(0,0,1)), h31(i+vec3(1,0,1)), f.x), mix(h31(i+vec3(0,1,1)), h31(i+vec3(1,1,1)), f.x), f.y);
  return mix(a, b, f.z); }
float fbm(vec3 p){ float s = 0.0, a = 0.5; for (int i = 0; i < 5; i++){ s += a * vn3(p); p *= 2.03; a *= 0.5; } return s; }
void main(){
  vec2 q = (gl_FragCoord.xy - u_c) / u_r;
  float d = length(q);
  vec3 sun = normalize(u_sun);
  if (d > 1.0) {   // the air beyond the limb
    float g = exp(-(d - 1.0) * 22.0) * 0.75 + exp(-(d - 1.0) * 6.0) * 0.12;
    float lit = clamp(dot(normalize(vec3(q, 0.0)), sun) * 0.6 + 0.45, 0.08, 1.0);
    outColor = vec4(u_blue, clamp(g * lit, 0.0, 1.0)); return;
  }
  vec3 n = vec3(q, sqrt(1.0 - d * d));
  float c = cos(u_rot), s = sin(u_rot);
  vec3 m = vec3(c * n.x + s * n.z, n.y, -s * n.x + c * n.z);
  m = vec3(m.x, 0.92 * m.y - 0.39 * m.z, 0.39 * m.y + 0.92 * m.z);        // a tilted axis
  float land = smoothstep(0.50, 0.53, fbm(m * 2.2 + 3.0));
  float ice = smoothstep(0.82, 0.9, abs(m.y));
  float cloud = smoothstep(0.55, 0.75, fbm(m * 4.0 + vec3(u_rot * 0.4, 0.0, 7.0)));
  vec3 base = mix(vec3(0.035, 0.07, 0.12), vec3(0.20, 0.22, 0.25), land);
  base = mix(base, vec3(0.62, 0.66, 0.70), ice);
  float l = dot(n, sun), day = smoothstep(-0.08, 0.25, l);
  vec3 col = base * (0.06 + 1.05 * max(l, 0.0)) + vec3(0.85) * cloud * 0.55 * day;
  float city = land * (1.0 - day) * step(0.86, h31(floor(m * 140.0))) * (0.5 + 0.5 * h31(floor(m * 140.0) + 9.0));
  col += u_blue * city * 1.2;                                                 // the night side's lights: observers
  float rim = pow(1.0 - n.z, 3.0);
  col = mix(col, u_blue * (0.25 + 0.9 * day), rim * 0.65);
  outColor = vec4(col, 1.0);
}`;

let G = null;

export async function setup(ctx, tokens, lib) {
  const { W, H, PORTRAIT: P } = lib;
  const g = {};
  g.k = 63.5;                 // world px per Schwarzschild radius (the shadow is about 2.6 of them)
  g.Sb = 760;                 // the hole's shader covers ±Sb world px
  g.hole = lib.shader(HOLE, { width: 640, height: 640 });
  g.earthFx = lib.shader(EARTH, { width: Math.round(W / 2), height: Math.round(H / 2) });
  // the light: a front of rays, integrated once round the hole (same equation, in the plane)
  const bs = [-9.4, -7.6, -6.2, 1.9, 7.2, 9.6];   // impact parameters (rs): one falls in, the rest bend
  g.rays = bs.map((b) => {
    let x = -4200 / g.k, y = b, vx = 1, vy = 0; const pts = [[x * g.k, y * g.k]];
    const h2 = b * b; let fell = false;
    for (let i = 0; i < 6000; i++) {
      const r2 = x * x + y * y, r = Math.sqrt(r2);
      if (r < 1.05) { fell = true; break; }
      const st = Math.min(0.5, Math.max(0.02, 0.06 * r));
      vx += -1.5 * h2 * x / (r2 * r2 * r) * st; vy += -1.5 * h2 * y / (r2 * r2 * r) * st;
      const vl = Math.hypot(vx, vy); vx /= vl; vy /= vl;
      x += vx * st; y += vy * st;
      pts.push([x * g.k, y * g.k]);
      if (x * g.k > 9000) break;
    }
    const cum = [0];
    for (let i = 1; i < pts.length; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    return { b, pts, cum, fell };
  });
  // the Earth: where the first ray (the one bent down the most toward it) will be at the landing time
  g.R = P ? 1000 : 1100;
  const ray = g.rays[0];
  g.landAt = at(ray, (T.land - T.rays) * T.v);
  const dir = [0.42, 0.91];
  g.E = [g.landAt[0] + dir[0] * g.R, g.landAt[1] + dir[1] * g.R];
  for (const r of g.rays) {   // light stops where it meets the Earth
    const i = r.pts.findIndex(([x, y]) => Math.hypot(x - g.E[0], y - g.E[1]) < g.R);
    if (i > 0) { r.pts.length = i + 1; r.cum.length = i + 1; r.landed = true; }
  }
  g.earthScreen = P ? [W / 2 + 120, H + 360] : [W / 2 + 250, H + 520];
  g.camE = [g.E[0] - (g.earthScreen[0] - W / 2), g.E[1] - (g.earthScreen[1] - H / 2), 1];
  g.cam0 = [-2600, 0, P ? 0.5 : 0.6];
  g.keys = [
    [0, g.cam0], [1.5, [-700, 0, P ? 0.62 : 0.75]], [2.45, [0, 0, P ? 0.85 : 1.0]], [3.35, [260, 40, P ? 0.85 : 1.0]],
    [4.62, g.camE], [7.5, [g.camE[0] + 60, g.camE[1] - 10, 1.0]], [8.97, [g.cam0[0] + PX, 0, g.cam0[2]]],
  ];
  // stars on three depths: each layer repeats every PX * depth, so a journey of PX brings every layer back
  const rnd = lib.rng(7);
  g.stars = [[0.35, 1300], [0.6, 900], [1.0, 520]].map(([p, n]) => Array.from({ length: n }, () => {
    const per = PX * p;
    return [rnd() * per, (rnd() - 0.5) * 3600, 0.5 + rnd() * (p > 0.9 ? 1.8 : 1.1), 0.35 + rnd() * 0.6, rnd() * 6.28, p, per];
  }));
  // a band of galaxy on its own depth (0.2): a tile one period wide (PX * 0.2), so the journey brings it back too
  g.bandP = 0.2; g.bandW = PX * g.bandP; g.bandH = H + 700;
  g.band = (() => {
    const c = document.createElement("canvas"); c.width = g.bandW; c.height = g.bandH; const x = c.getContext("2d");
    const cy0 = g.bandH / 2, wave = (u) => cy0 + Math.sin(u / g.bandW * Math.PI * 2) * 50 + Math.sin(u / g.bandW * Math.PI * 6 + 1) * 18;
    const each = (fn) => { for (const o of [-g.bandW, 0, g.bandW]) fn(o); };   // drawn three times, so the tile has no seam
    x.filter = "blur(70px)";                                     // the wide faint halo
    for (let i = 0; i < 30; i++) { const u = rnd() * g.bandW, v = wave(u) + (rnd() - 0.5) * 120, a = 0.02 + rnd() * 0.02, rx = 260 + rnd() * 300;
      each((o) => { x.fillStyle = `rgba(160,150,185,${a})`; x.beginPath(); x.ellipse(u + o, v, rx, 130, 0, 0, 7); x.fill(); }); }
    x.filter = "blur(26px)";                                     // the brighter, thinner core
    for (let i = 0; i < 70; i++) { const u = rnd() * g.bandW, v = wave(u) + (rnd() - 0.5) * 40, a = 0.03 + rnd() * 0.04, rx = 80 + rnd() * 160;
      each((o) => { x.fillStyle = `rgba(${200 + rnd() * 40},${185 + rnd() * 30},${200 + rnd() * 40},${a})`; x.beginPath(); x.ellipse(u + o, v, rx, 22 + rnd() * 20, 0, 0, 7); x.fill(); }); }
    x.filter = "blur(10px)";                                     // dark lanes of dust across it
    for (let i = 0; i < 22; i++) { const u = rnd() * g.bandW, v = wave(u) + (rnd() - 0.5) * 30, rx = 60 + rnd() * 140, rot = (rnd() - 0.5) * 0.5;
      each((o) => { x.fillStyle = "rgba(2,4,8,0.55)"; x.beginPath(); x.ellipse(u + o, v, rx, 6 + rnd() * 10, rot, 0, 7); x.fill(); }); }
    x.filter = "none";                                           // and the band's own crowd of faint stars
    for (let i = 0; i < 2600; i++) { const u = rnd() * g.bandW, v = wave(u) + (rnd() + rnd() + rnd() - 1.5) * 90, a = 0.12 + rnd() * 0.35, r = 0.6 + rnd() * 0.9;
      each((o) => { x.fillStyle = `rgba(230,232,245,${a})`; x.fillRect(u + o, v, r, r); }); }
    return c;
  })();
  // type
  const SAFE = lib.SAFE, TYPE = lib.TYPE;
  lib.setFont(ctx, tokens, "zh", 10);
  const ts = lib.fitText(ctx, lib.TITLE_ZH, SAFE.title.w * 0.9, (s) => lib.setFont(ctx, tokens, "zh", s), { min: 84, max: TYPE.title });
  const ty = P ? 760 : 300;
  const mk = (role, str, size, y, win, ink) => {
    lib.setFont(ctx, tokens, role, size);
    return { role, size, y, win, ink, lay: lib.layoutText(ctx, str, { x: W / 2, y, align: "center", tracking: lib.tracking(tokens, role, size) }) };
  };
  g.lines = [
    mk("zh", lib.TITLE_ZH, ts, ty, T.title, "white"),
    mk("display", lib.TITLE_EN, TYPE.label, ty + (P ? 96 : 76), T.en, "dim"),
    mk("body", lib.CAPTION_ZH, TYPE.caption, SAFE.title.y1 - TYPE.caption * 0.6, T.caption, "white"),
  ];
  g.legend = [["光", "light"], ["物质", "matter"], ["观测", "blue"]];
  G = g;
}

/** a point along a ray at arclength s (world px) */
function at(ray, s) {
  const c = ray.cum, P = ray.pts;
  if (s <= 0) return P[0];
  if (s >= c[c.length - 1]) return P[P.length - 1];
  let lo = 0, hi = c.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (c[m] <= s) lo = m; else hi = m - 1; }
  const f = (s - c[lo]) / Math.max(1e-6, c[lo + 1] - c[lo]);
  return [P[lo][0] + (P[lo + 1][0] - P[lo][0]) * f, P[lo][1] + (P[lo + 1][1] - P[lo][1]) * f];
}

const sg = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
const sm5 = (u) => u * u * u * (u * (u * 6 - 15) + 10);

/** the camera: [x, y, zoom], eased between keys */
function camAt(t) {
  const K = G.keys;
  let i = 0;
  while (i < K.length - 2 && t >= K[i + 1][0]) i++;
  const x = sg(t, K[i][0], K[i + 1][0]), u = i === 0 ? 1 - (1 - x) * (1 - x) : sm5(x);   // already drifting at the first frame
  const [, a] = K[i], [, b] = K[i + 1];
  return [0, 1, 2].map((d) => a[d] + (b[d] - a[d]) * u);
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  const sc = lib.layer("ds:scene");
  scene(sc, t, tokens, lib);
  // a fast camera smears the scene along its own motion (half a frame of shutter)
  const [ax, ay, az] = camAt(t), [bx, by] = camAt(t - 1 / 30);
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  smear(ctx, sc.canvas, -(ax - bx) * az * 0.5, -(ay - by) * az * 0.5, W, H);
  legend(ctx, t, tokens, lib);
  words(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 12, seed: 3 });
  lib.vignette(ctx, { strength: tokens.texture.vignette, inner: 0.55, color: "#000" });
}

function scene(ctx, t, tokens, lib) {
  const { W, H } = lib;
  const C = (k) => lib.color(tokens, k);
  const [cx, cy, z] = camAt(t);
  const S = (x, y) => [W / 2 + (x - cx) * z, H / 2 + (y - cy) * z];
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, W, H);
  { // the galaxy band, on its own depth
    const p = G.bandP, ze = 1 + (z - 1) * p, off = -(((cx * p) % G.bandW) + G.bandW) % G.bandW;
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(lib.PORTRAIT ? -0.9 : -0.26); ctx.scale(ze, ze);
    for (let k = -1; k <= 1; k++) ctx.drawImage(G.band, off + k * G.bandW - G.bandW / 2, -G.bandH / 2 - cy * p);
    ctx.restore();
  }
  // stars
  for (const layer of G.stars) for (const [u, v, r, a, ph, p, per] of layer) {
    const ze = 1 + (z - 1) * p;
    let dx = ((u - cx * p) % per + per) % per; if (dx > per / 2) dx -= per;
    const x = W / 2 + dx * ze, y = H / 2 + (v - cy * p) * ze;
    if (x < -4 || x > W + 4 || y < -4 || y > H + 4) continue;
    ctx.fillStyle = `rgba(232,236,245,${Math.min(1, a * 1.3) * (0.75 + 0.25 * Math.sin(t * 1.7 + ph))})`;
    ctx.fillRect(x - r / 2, y - r / 2, r, r);
  }
  // the hole
  const [hx, hy] = S(0, 0), hs = G.Sb * z;
  if (hx + hs > 0 && hx - hs < W && hy + hs > 0 && hy - hs < H) {
    const img = G.hole.render(t, {
      u_incl: 0.11 + 0.05 * Math.sin(t * 0.5), u_dist: 24, u_fov: 1.05, u_spin: t,
      u_hot: rgb3(C("hot")), u_mat: rgb3(C("matter")),
    });
    ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.filter = "blur(18px)"; ctx.globalAlpha = 0.55;
    ctx.drawImage(img, hx - hs, hy - hs, hs * 2, hs * 2); ctx.restore();
    ctx.drawImage(img, hx - hs, hy - hs, hs * 2, hs * 2);
  }
  // the Earth
  const [ex, ey] = S(G.E[0], G.E[1]), er = G.R * z;
  if (ex + er * 1.3 > 0 && ex - er * 1.3 < W && ey - er * 1.3 < H && ey + er * 1.3 > 0) {
    const img = G.earthFx.render(t, { u_c: [ex / 2, (H - ey) / 2], u_r: er / 2, u_rot: 0.6 + t * 0.05, u_sun: [-0.6, 0.55, 0.6], u_blue: rgb3(C("blue")) });
    ctx.drawImage(img, 0, 0, W, H);
  }
  // the light
  const L = lib.layer("ds:light");
  const s = (t - T.rays) * T.v;
  for (const ray of G.rays) {
    if (s <= 0) break;
    const end = Math.min(s, ray.cum[ray.cum.length - 1]);
    const fade = (ray.fell ? 1 - sg(s - ray.cum[ray.cum.length - 1], 0, 900) : 1) * (1 - sg(t, T.away[0] + 0.1, T.away[0] + 0.8));
    if (fade <= 0) continue;
    L.save(); L.lineCap = "round"; L.lineJoin = "round";
    L.strokeStyle = lib.rgba(C("light"), 0.9 * fade); L.lineWidth = 3;
    L.beginPath();
    let first = true;
    for (let i = 0; i < ray.pts.length && ray.cum[i] <= end; i += 2) {
      const [x, y] = S(ray.pts[i][0], ray.pts[i][1]);
      if (first) { L.moveTo(x, y); first = false; } else L.lineTo(x, y);
    }
    const hp = S(...at(ray, end)); L.lineTo(hp[0], hp[1]); L.stroke();
    if (end < ray.cum[ray.cum.length - 1]) {   // the head of the front
      const gr = L.createRadialGradient(hp[0], hp[1], 0, hp[0], hp[1], 26);
      gr.addColorStop(0, lib.rgba("#FFFFFF", 0.95 * fade)); gr.addColorStop(0.3, lib.rgba(C("light"), 0.6 * fade)); gr.addColorStop(1, lib.rgba(C("light"), 0));
      L.fillStyle = gr; L.beginPath(); L.arc(hp[0], hp[1], 26, 0, 7); L.fill();
    }
    L.restore();
  }
  ctx.save(); ctx.globalCompositeOperation = "lighter"; ctx.filter = "blur(6px)"; ctx.drawImage(L.canvas, 0, 0, W, H); ctx.restore();
  ctx.drawImage(L.canvas, 0, 0, W, H);
  // where the light lands: a blue ring answers (an observer)
  if (t >= T.land) {
    const [lx, ly] = S(...G.landAt), age = t - T.land;
    ctx.save(); ctx.strokeStyle = lib.rgba(C("blue"), Math.max(0, 0.9 - age * 0.9)); ctx.lineWidth = 3;
    for (let k = 0; k < 2; k++) { const a = age - k * 0.35; if (a > 0) { ctx.beginPath(); ctx.arc(lx, ly, 10 + a * 90, 0, 7); ctx.stroke(); } }
    ctx.fillStyle = lib.rgba(C("blue"), 0.95); ctx.beginPath(); ctx.arc(lx, ly, 7, 0, 7); ctx.fill();
    ctx.restore();
  }
}

function rgb3(hex) { return [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255); }

/** the colour key, top left: what each colour is, said once */
function legend(ctx, t, tokens, lib) {
  const { SAFE, TYPE } = lib;
  const out = 1 - sg(t, T.away[0], T.away[0] + 0.4);
  if (out <= 0) return;
  const x0 = SAFE.title.x0, y0 = SAFE.title.y0 + 30, gap = TYPE.label * 1.5;
  G.legend.forEach(([word, key], k) => {
    const a = sg(t, T.legend[0] + k * T.legend[1], T.legend[0] + k * T.legend[1] + 0.25) * out;
    if (a <= 0) return;
    const y = y0 + k * gap, col = lib.color(tokens, key);
    ctx.save(); ctx.globalAlpha = a;
    ctx.strokeStyle = col; ctx.lineWidth = 5; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(x0, y - TYPE.label * 0.32); ctx.lineTo(x0 + 46 * a, y - TYPE.label * 0.32); ctx.stroke();
    lib.setFont(ctx, tokens, "body", TYPE.label); ctx.fillStyle = col;
    lib.drawText(ctx, word, x0 + 66, y, {});
    ctx.restore();
  });
}

/** the words come into focus: each glyph from a soft blur to sharp, staggered */
function words(ctx, t, tokens, lib) {
  const { W, H, SAFE, TYPE } = lib;
  const C = (k) => lib.color(tokens, k);
  const out = 1 - sg(t, T.away[0], T.away[0] + 0.45);
  if (out <= 0) return;
  const cap = G.lines[2], ca = sg(t, cap.win[0], cap.win[0] + 0.2) * out;
  if (ca > 0) {   // the caption's soft dark band
    const y = cap.y - TYPE.caption * 0.4, g = ctx.createLinearGradient(0, y - 70, 0, y + 70);
    g.addColorStop(0, "rgba(2,4,8,0)"); g.addColorStop(0.5, `rgba(2,4,8,${0.62 * ca})`); g.addColorStop(1, "rgba(2,4,8,0)");
    ctx.fillStyle = g; ctx.fillRect(0, y - 70, W, 140);
  }
  for (const ln of G.lines) {
    if (t < ln.win[0]) continue;
    lib.setFont(ctx, tokens, ln.role, ln.size);
    ctx.save(); ctx.fillStyle = C(ln.ink);
    const n = ln.lay.glyphs.length;
    lib.drawGlyphs(ctx, ln.lay, (g, i) => {
      const t0 = ln.win[0] + (i / Math.max(1, n - 1)) * ln.win[1] * 0.6, u = sg(t, t0, t0 + ln.win[1] * 0.4);
      if (u <= 0) return null;
      return { alpha: u * out, dy: (1 - sm5(u)) * 10 };
    });
    ctx.restore();
  }
}
