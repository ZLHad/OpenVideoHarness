// walk-in-world swatch — the subject built as a place, and one unbroken move through it.
// The place: still water at dusk. Three picture frames stand over it, each one stage of the same picture (a morning
// over water): OUTLINE is a line drawing you can see the dusk through, STORYBOARD is six flat panels, DRAFT is a door
// that opens onto the real morning. A road of frame-shaped tiles runs under the camera to that door.
// The move: the camera travels along one straight line for the whole film and only turns its head.
//   0.0–0.8  already moving: low over the water, out of focus, through a small floating frame; the far door is dead
//            ahead against the afterglow, ajar, a hairline of light between its leaves. The focus lands and the head
//            turns left to take the place in
//   0.8–2.6  the title comes into focus word by word in the dark top of the sky; we keep walking, so the three frames
//            grow and slide apart
//   2.0–4.0  the frames wake left to right: the outline draws itself (2.0), the six panels fill (2.4), the door's
//            leaves part (2.8) and its light starts across the water along the road, tile by tile, to reach our feet
//            at 4.0. 3.2–4.0: a playhead walks the panels
//   4.0–5.0  the light reaches us and we go: head back to the door, straight through it into the morning (a second
//            palette, light and weather), the name of the style in that sky, the road running on to the next door
// World and light are one fullscreen fragment shader (analytic rays: no marching, no textures); the floating frames
// and the type are Canvas 2D, placed with the same pinhole camera, so nothing can drift apart.
const T_OUT = 2.0, T_SB = 2.4, T_DOOR = 2.8, T_ROAD = 3.2, T_GO = 4.0;
const AX = 0.2725;                              // the travel axis, radians from +z
const CRUISE = 3.2;                             // metres per second, the whole way
const L3 = 49;                                  // metres along the axis from where the film starts to the door
const RUSH = 43.7;                              // extra metres covered after T_GO, most of them in 0.4 s
const OPEN0 = 0.014;                            // the door stands ajar until T_DOOR (half the gap, as a share of its half width)
const FOCAL = 1 / Math.tan(20 * Math.PI / 180); // 40° vertical field of view
const FPX = FOCAL * 540;
const PORT = [                                  // centre, yaw (the camera's convention), half size
  { p: [-3.03, 2.2, 29.42], yaw: -0.2, s: [3.2, 1.8] },
  { p: [3.57, 2.2, 36.42], yaw: 0.0, s: [3.2, 1.8] },
  { p: [L3 * Math.sin(AX), 2.7, L3 * Math.cos(AX)], yaw: AX, s: [4.0, 2.25] },
];
const HERO = { s: 3.6, y: 1.0, w: 2.8 };       // the small frame the camera passes through in the first half second
// the place goes on: other frames stand far off over the same water, and past the door the road runs to the next one
const along = (s, l, y) => [Math.sin(AX) * s + Math.cos(AX) * l, y, Math.cos(AX) * s - Math.sin(AX) * l];
const FAR_DUSK = [[-68.6, 132], [47.4, 107], [88.4, 162], [-27.1, 222]].map(([x, z], i) => ({ p: [x, 2.3, z], yaw: (i % 3 - 1) * 0.25, hw: 3.2, hh: 1.8 }));
const NEXT = { p: along(L3 + 140, 0, 2.7), yaw: AX, hw: 4, hh: 2.25 };          // the next door, in the next world's colour
let L = null;
export const fonts = ["Baskerville", "Songti SC"];

const rushS = (x) => (x <= 0 ? 0 : x >= 1 ? 1 : 1 - Math.pow(1 - x * x, 7));
const travel = (t, lib) => CRUISE * t + 2.4 * lib.ease.outCubic(lib.clamp(t, 0, 1)) + RUSH * rushS(t - T_GO);

function cam(t, lib) {
  const { ease, seg, lerp } = lib, d = travel(t, lib);
  const yaw = AX * (1 - ease.inOutCubic(seg(t, 0.2, 1.25))) + AX * ease.inOutCubic(seg(t, 3.9, 4.3));
  const pitch = (lerp(-2.5, 3, ease.outCubic(seg(t, 0, 1.1))) - 2.6 * ease.inOutCubic(seg(t, 3.95, 4.35)) + 1.6 * ease.outCubic(seg(t, 4.45, 5))) * Math.PI / 180;
  const h = 0.75 + 0.75 * ease.outCubic(seg(t, 0, 1.1)) + 1.15 * ease.inOutCubic(seg(t, 4.0, 4.4)) - 0.5 * ease.outCubic(seg(t, 4.45, 5));
  const c = [Math.sin(AX) * d, h, Math.cos(AX) * d];
  const cp = Math.cos(pitch), sp = Math.sin(pitch), cy = Math.cos(yaw), sy = Math.sin(yaw);
  const f = [sy * cp, sp, cy * cp], r = [cy, 0, -sy];
  const u = [f[1] * r[2] - f[2] * r[1], f[2] * r[0] - f[0] * r[2], f[0] * r[1] - f[1] * r[0]];
  return { c, f, r, u, d };
}
function project(K, P) {
  const dx = P[0] - K.c[0], dy = P[1] - K.c[1], dz = P[2] - K.c[2];
  const z = dx * K.f[0] + dy * K.f[1] + dz * K.f[2], k = FPX / z;
  return { x: 960 + (dx * K.r[0] + dy * K.r[1] + dz * K.r[2]) * k, y: 540 - (dx * K.u[0] + dy * K.u[1] + dz * K.u[2]) * k, z };
}
// is world point P hidden behind one of the frames, seen from the camera? (returns how much of it shows: 0, 0.55 or 1)
function shows(K, P) {
  for (let k = 0; k < 3; k++) {
    const q = PORT[k], n = [Math.sin(q.yaw), 0, Math.cos(q.yaw)], r = [Math.cos(q.yaw), 0, -Math.sin(q.yaw)];
    const dc = (q.p[0] - K.c[0]) * n[0] + (q.p[2] - K.c[2]) * n[2], dp = (P[0] - K.c[0]) * n[0] + (P[2] - K.c[2]) * n[2];
    if (dc <= 0 || dp <= dc) continue;
    const s = dc / dp, hx = K.c[0] + (P[0] - K.c[0]) * s - q.p[0], hy = K.c[1] + (P[1] - K.c[1]) * s - q.p[1], hz = K.c[2] + (P[2] - K.c[2]) * s - q.p[2];
    if (Math.abs(hx * r[0] + hz * r[2]) < q.s[0] && Math.abs(hy) < q.s[1]) return k === 0 ? 0.55 : 0;
  }
  return 1;
}

// ───────────────────────── the world (GLSL ES 3.00 body; lib.shader adds the header) ─────────────────────────
function fragment(tokens, lib) {
  const n = (x) => (Number.isInteger(x) ? x.toFixed(1) : x.toFixed(5));
  const v3 = (a) => `vec3(${a.map(n).join(",")})`, v2 = (a) => `vec2(${a.map(n).join(",")})`;
  const C = (k) => v3(lib.rgb(lib.color(tokens, k)).map((x) => x / 255));
  return `
uniform vec3 u_c, u_r, u_u, u_f;
uniform vec4 u_cam;   // x focal, y exposure, z which world the camera is in (0 dusk, 1 morning)
uniform vec4 u_on;    // x outline drawn, y storyboard panels filled, z door open, w storyboard playhead (-1 off, else 0..6)
uniform vec4 u_lit;   // x the door's light, y metres of road lit, counted back from the door
const float AX = ${n(AX)}, L3 = ${n(L3)};
const vec3 P1 = ${v3(PORT[0].p)}, P2 = ${v3(PORT[1].p)}, P3 = ${v3(PORT[2].p)};
const vec2 S1 = ${v2(PORT[0].s)}, S2 = ${v2(PORT[1].s)}, S3 = ${v2(PORT[2].s)};
const float Y1 = ${n(PORT[0].yaw)}, Y2 = ${n(PORT[1].yaw)}, Y3 = ${n(PORT[2].yaw)};
const vec3 DZEN = ${C("dusk_zenith")}, DMID = ${C("dusk_mid")}, DVIO = ${C("dusk_violet")}, DROSE = ${C("dusk_rose")}, DPEACH = ${C("dusk_peach")}, DWATER = ${C("dusk_water")};
const vec3 DR1 = ${C("dusk_ridge_far")}, DR2 = ${C("dusk_ridge_mid")}, DR3 = ${C("dusk_ridge_near")};
const vec3 MZEN = ${C("morn_zenith")}, MMINT = ${C("morn_mint")}, MCREAM = ${C("morn_cream")}, MSUN = ${C("morn_sun")}, MWATER = ${C("morn_water")};
const vec3 MH1 = ${C("morn_hill_far")}, MH2 = ${C("morn_hill_mid")}, MH3 = ${C("morn_hill_near")};
const vec3 FCOOL = ${C("frame_cool")}, FIVORY = ${C("frame_ivory")}, FGOLD = ${C("frame_gold")}, LIGHT = ${C("light")};
const float SUN_AZ = AX + 0.07, SUN_E = 0.055, SUN_R = 0.024;

float h11(float p){ p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p); }
float h21(vec2 p){ vec3 q = fract(vec3(p.xyx) * 0.1031); q += dot(q, q.yzx + 33.33); return fract((q.x + q.y) * q.z); }
float n1(float x){ float i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(h11(i), h11(i + 1.0), f); }
float n2(vec2 x){ vec2 i = floor(x), f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
float fbm1(float x){ float a = 0.5, s = 0.0; for (int i = 0; i < 4; i++) { s += a * n1(x); x = x * 2.03 + 17.1; a *= 0.5; } return s; }
float fbm2(vec2 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 4; i++) { s += a * n2(p); p = p * 2.02 + vec2(13.1, 7.7); a *= 0.5; } return s; }
float pixAt(float d){ return d * 2.0 / (u_cam.x * u_res.y); }               // metres one pixel covers at distance d
float ln(float d, float w, float aa){ return 1.0 - smoothstep(w - aa, w + aa, d); }

// ── the morning (what the pictures are of, and where the door leads)
vec3 skyMorn(vec3 rd){
  float e = rd.y / max(length(rd.xz), 1e-4), az = atan(rd.x, rd.z), da = az - SUN_AZ, y = max(e, 0.0);
  float sd = length(vec2(da, e - SUN_E));
  vec3 c = mix(MCREAM, MMINT, smoothstep(0.0, 0.13, y));
  c = mix(c, MZEN, smoothstep(0.08, 0.42, y));
  float cl = fbm2(vec2(az * 2.2 + u_time * 0.004, e * 30.0 + 9.0));
  c = mix(c, MSUN, 0.5 * smoothstep(0.52, 0.76, cl) * smoothstep(0.03, 0.10, e) * smoothstep(0.42, 0.16, e));
  float ang = atan(e - SUN_E, da);
  float ray = pow(n2(vec2(cos(ang), sin(ang)) * 3.2 + vec2(5.0 + u_time * 0.05, 1.0)), 2.0);
  c += vec3(1.0, 0.80, 0.46) * (0.12 * exp(-sd * 9.0) + 0.12 * ray * exp(-sd * 3.2));
  c = mix(c, MSUN, 0.36 * exp(-sd * 26.0));
  c = mix(c, vec3(1.06, 1.03, 0.94), smoothstep(SUN_R + 0.0015, SUN_R - 0.0015, sd));
  float gap = mix(0.10, 1.0, smoothstep(0.015, 0.10, abs(da)));                 // the hills part where the sun stands
  float h1 = (0.030 + 0.090 * (fbm1(az * 4.5 + 5.0) - 0.30)) * gap;
  float h2 = (0.016 + 0.066 * (fbm1(az * 8.0 + 23.0) - 0.36)) * gap;
  float h3 = (0.005 + 0.046 * (fbm1(az * 13.0 + 51.0) - 0.40)) * gap;
  c = mix(c, mix(MCREAM, MH1, 0.66 + 0.34 * smoothstep(0.0, 0.05, e)), 1.0 - smoothstep(h1 - 0.0012, h1 + 0.0012, e));
  c = mix(c, mix(MCREAM, MH2, 0.72 + 0.28 * smoothstep(0.0, 0.035, e)), 1.0 - smoothstep(h2 - 0.0012, h2 + 0.0012, e));
  c = mix(c, mix(MCREAM, MH3, 0.80 + 0.20 * smoothstep(0.0, 0.02, e)), 1.0 - smoothstep(h3 - 0.0012, h3 + 0.0012, e));
  return mix(c, MCREAM, 0.42 * exp(-y * 52.0));
}
vec3 wnorm(vec2 q, float d){
  float t = u_time, k = 1.0 / (1.0 + d * 0.035);
  float a = n2(q * vec2(0.55, 1.9) + vec2(t * 0.18, t * 0.33)) - 0.5;
  float b = n2(q * vec2(1.7, 5.3) + vec2(9.0 - t * 0.22, t * 0.61)) - 0.5;
  float c = n2(q * vec2(0.8, 2.6) + vec2(4.0 + t * 0.12, -t * 0.27)) - 0.5;
  return normalize(vec3((a * 0.07 + b * 0.03) * k, 1.0, (c * 0.22 + b * 0.08) * k));
}
// the road: frame-shaped tiles lying on the water along the travel axis. Returns (line, fill, how far along the axis)
vec3 road(vec2 xz, float d, float ry){
  float s = dot(xz, vec2(sin(AX), cos(AX))), l = dot(xz, vec2(cos(AX), -sin(AX)));
  float per = 2.5, i = floor(s / per), fs = (fract(s / per) - 0.5) * per, sc = (i + 0.5) * per;
  float aaL = pixAt(d) * 1.3, aaS = aaL / max(-ry, 0.04);
  float dx = abs(l) - 1.02, ds = abs(fs) - 0.575;                             // 2.04 × 1.15 m: 16:9
  float inside = (1.0 - smoothstep(-aaL, aaL, dx)) * (1.0 - smoothstep(-aaS, aaS, ds));
  float inner = (1.0 - smoothstep(-aaL, aaL, dx + 0.07)) * (1.0 - smoothstep(-aaS, aaS, ds + 0.07));
  float keep = step(1.0, sc) * (1.0 - smoothstep(L3 - 3.2, L3 - 2.2, sc) * (1.0 - smoothstep(L3 + 2.2, L3 + 3.2, sc)));
  float thin = 1.0 / (1.0 + aaS * 9.0);                                        // far tiles fade instead of shimmering
  return vec3(clamp(inside - inner, 0.0, 1.0) * thin, inner, sc) * vec3(keep, keep, 1.0);
}
vec3 waterMorn(vec3 ro, vec3 rd, float tw){
  vec3 p = ro + rd * tw, n = wnorm(p.xz, tw);
  vec3 r = reflect(rd, n); r.y = abs(r.y) + 0.003; r = normalize(r);
  float fres = pow(1.0 - clamp(dot(-rd, n), 0.0, 1.0), 2.5);
  vec3 c = mix(MWATER, skyMorn(r), 0.46 + 0.50 * fres);
  vec3 sun = normalize(vec3(sin(SUN_AZ), SUN_E, cos(SUN_AZ)));
  c += vec3(1.0, 0.90, 0.66) * 1.3 * pow(max(dot(r, sun), 0.0), 240.0);
  vec3 rdv = road(p.xz, tw, rd.y);
  c += vec3(1.0, 0.95, 0.80) * (0.72 * rdv.x + 0.07 * rdv.y);
  return mix(c, mix(MCREAM, MMINT, 0.45), 1.0 - exp(-tw * 0.008));
}
vec3 mornScene(vec3 ro, vec3 rd){ return rd.y < -1e-4 ? waterMorn(ro, rd, -ro.y / rd.y) : skyMorn(rd); }

// ── the same morning as a flat picture (x in ±1.78, y in ±1): the outline traces it, the storyboard blocks it in
float ridgeA(float x){ return -0.30 + 0.46 * fbm1(x * 1.3 + 2.0); }
float ridgeB(float x){ return -0.36 + 0.34 * fbm1(x * 2.1 + 9.0); }
const vec2 PSUN = vec2(0.52, 0.24);
vec3 flatMorn(vec2 p){
  vec3 c = p.y > 0.42 ? MZEN : (p.y > 0.05 ? MMINT : MCREAM);
  if (length(p - PSUN) < 0.27) c = MSUN;
  if (p.y < ridgeA(p.x)) c = MH1;
  if (p.y < ridgeB(p.x)) c = MH3;
  if (p.y < -0.40) c = p.y < -0.72 ? MH3 : MWATER;
  return c;
}
vec4 outlinePic(vec2 q, float d){
  float on = u_on.x, aa = pixAt(d) / S1.y * 1.2, w = 0.013 + aa * 0.5;
  vec2 p = vec2(q.x * 1.7778, q.y);
  float ra = ridgeA(p.x), rb = ridgeB(p.x), l = 0.0;
  l = max(l, ln(abs(length(p - PSUN) - 0.27), w, aa) * step(max(ra, rb), p.y));
  l = max(l, ln(abs(p.y - ra), w, aa) * step(rb, p.y));
  l = max(l, ln(abs(p.y - rb), w, aa) * step(-0.40, p.y));
  l = max(l, ln(abs(p.y + 0.40), w, aa));
  float k = (-0.40 - p.y) / 0.15, row = floor(k);
  l = max(l, ln(abs(fract(k) - 0.5) * 0.15, w * 0.8, aa) * step(0.42, fract(p.x * (0.8 + 0.25 * row) + h11(row) * 7.0)) * step(p.y, -0.43));
  l *= smoothstep(0.0, 0.10, on * 1.2 - (q.x * 0.5 + 0.5));                    // drawn left to right
  vec2 b = (1.0 - abs(q)) * S1; float bd = min(b.x, b.y), aw = pixAt(d) * 1.2;
  float border = (1.0 - smoothstep(0.06 - aw, 0.06 + aw, bd)) * (0.42 + 0.58 * on);
  float a = max(border, l);
  return vec4(mix(DZEN * 1.3, FCOOL, a), mix(0.34 + 0.22 * on, 1.0, a) * smoothstep(0.0, aw, bd));
}
const vec3 SHOT[6] = vec3[6](vec3(0.0, 0.0, 1.0), vec3(0.40, 0.20, 0.46), vec3(-0.85, -0.05, 0.62),
                              vec3(0.40, -0.62, 0.50), vec3(0.25, 0.30, 1.30), vec3(0.95, -0.10, 0.78));
vec4 storyPic(vec2 q, float d){
  float on = u_on.y, aw = pixAt(d) * 1.2;
  vec2 g = vec2((q.x * 0.5 + 0.5) * 3.0, (q.y * 0.5 + 0.5) * 2.0), id = min(floor(g), vec2(2.0, 1.0)), f = g - id;
  float k = id.x + (1.0 - id.y) * 3.0;
  vec2 e2 = min(f, 1.0 - f) * vec2(S2.x * 2.0 / 3.0, S2.y);
  float pane = smoothstep(0.11 - aw, 0.11 + aw, min(e2.x, e2.y)) * clamp(on * 7.0 - k, 0.0, 1.0);
  vec3 sh = SHOT[int(k)];
  vec3 pc = flatMorn(vec2((f.x - 0.5) * 3.5556, (f.y - 0.5) * 2.0) * sh.z + sh.xy);
  float cur = step(abs(k + 0.5 - u_on.w), 0.5), run = step(0.0, u_on.w);
  pc = mix(pc * mix(1.0, 0.66, run * (1.0 - cur)), vec3(1.0), 0.16 * cur);
  vec2 b = (1.0 - abs(q)) * S2; float bd = min(b.x, b.y);
  float border = (1.0 - smoothstep(0.075 - aw, 0.075 + aw, bd)) * (0.42 + 0.58 * on);
  vec4 c = mix(vec4(DZEN * 1.3, 0.34), vec4(pc, 1.0), pane);
  c = mix(c, vec4(FIVORY, 1.0), border);
  return vec4(c.rgb, c.a * smoothstep(0.0, aw, bd));
}
vec4 doorPic(vec2 q, float d, vec3 ro, vec3 rd){
  float open = u_on.z, aw = pixAt(d) * 1.2, ax = abs(q.x);
  vec2 b = (1.0 - abs(q)) * S3; float bd = min(b.x, b.y);
  vec4 c = vec4(DZEN * 0.9, 0.92);                                             // the two leaves, a panel on each
  float u = (ax - open) / max(1.0 - open, 1e-3);                               // across a leaf: 0 at its edge, 1 at the frame
  float pd = abs(max((abs(u - 0.5) - 0.34) * (1.0 - open) * S3.x, (abs(q.y) - 0.74) * S3.y));
  c.rgb = mix(c.rgb, FGOLD * 0.55, 0.5 * ln(pd, 0.03 + aw * 0.5, aw) * step(open, ax));
  float gap = smoothstep(open + 0.004, open - 0.004, ax) * step(0.002, open);
  if (gap > 0.0) c = mix(c, vec4(mornScene(ro, rd), 1.0), gap);
  c.rgb += FGOLD * 0.9 * exp(-abs(ax - open) * 34.0) * step(0.002, open) * (1.0 - smoothstep(0.86, 1.0, open));
  float border = 1.0 - smoothstep(0.12 - aw, 0.12 + aw, bd);
  c = mix(c, vec4(mix(FGOLD * 0.42, min(FGOLD * 1.2, vec3(1.0)), open), 1.0), border);
  return vec4(c.rgb, c.a * smoothstep(0.0, aw, bd));
}
vec4 hitQuad(vec3 ro, vec3 rd, vec3 P, float yaw, vec2 S){
  vec3 n = vec3(sin(yaw), 0.0, cos(yaw)), r = vec3(cos(yaw), 0.0, -sin(yaw));
  float dn = dot(rd, n); if (abs(dn) < 1e-5) return vec4(0.0);
  float th = dot(P - ro, n) / dn; if (th <= 0.0) return vec4(0.0);
  vec3 h = ro + rd * th - P; vec2 q = vec2(dot(h, r), h.y) / S;
  if (abs(q.x) > 1.0 || abs(q.y) > 1.0) return vec4(0.0);
  return vec4(q, th, 1.0);
}
vec3 overFrames(vec3 base, vec3 ro, vec3 rd, float tmax, float d0){
  vec4 h, c;
  h = hitQuad(ro, rd, P3, Y3, S3); if (h.w > 0.5 && h.z < tmax) { c = doorPic(h.xy, d0 + h.z, ro, rd); base = mix(base, c.rgb, c.a); }
  h = hitQuad(ro, rd, P2, Y2, S2); if (h.w > 0.5 && h.z < tmax) { c = storyPic(h.xy, d0 + h.z); base = mix(base, c.rgb, c.a); }
  h = hitQuad(ro, rd, P1, Y1, S1); if (h.w > 0.5 && h.z < tmax) { c = outlinePic(h.xy, d0 + h.z); base = mix(base, c.rgb, c.a); }
  return base;
}

// ── the dusk the frames stand in
vec3 hazeDusk(float az){ float g = 0.5 + 0.5 * cos(az - AX); return mix(DVIO * 0.9, DPEACH, g * g * g); }
vec3 skyDusk(vec3 rd){
  float e = rd.y / max(length(rd.xz), 1e-4), az = atan(rd.x, rd.z), y = max(e, 0.0);
  float g = 0.5 + 0.5 * cos(az - AX); g = g * g * g;                           // 1 towards the afterglow (behind the door)
  vec3 hor = hazeDusk(az), low = mix(DVIO, DROSE, g);
  vec3 c = mix(hor, low, smoothstep(0.0, 0.075, y));
  c = mix(c, DMID, smoothstep(0.045, 0.20, y));
  c = mix(c, DZEN, smoothstep(0.16, 0.56, y));
  vec2 sg = vec2(az * 58.0, e * 58.0), si = floor(sg);                         // a few stars high up
  float st = step(0.955, h21(si)) * smoothstep(0.16, 0.0, length(fract(sg) - 0.5 - (vec2(h21(si + 3.1), h21(si + 7.7)) - 0.5) * 0.6));
  c += vec3(0.9, 0.88, 1.0) * st * smoothstep(0.14, 0.34, e) * (0.45 + 0.55 * h21(si + 1.7));
  float cl = fbm2(vec2(az * 2.6 + u_time * 0.006, e * 26.0 + 3.0));              // long clouds, lit from below near the glow
  cl = smoothstep(0.43, 0.68, cl) * smoothstep(0.02, 0.07, e) * smoothstep(0.36, 0.13, e);
  c = mix(c, mix(DMID * 1.35, mix(DROSE, DPEACH, 0.6), (0.25 + 0.75 * g) * smoothstep(0.24, 0.04, e)), cl * 0.62);
  float h1 = 0.032 + 0.105 * (fbm1(az * 4.0 + 11.0) - 0.30);
  float h2 = 0.019 + 0.078 * (fbm1(az * 7.5 + 37.0) - 0.34);
  float h3 = 0.007 + 0.052 * (fbm1(az * 12.0 + 71.0) - 0.38);
  c = mix(c, mix(hor, DR1, 0.50 + 0.35 * smoothstep(0.0, 0.06, e)), 1.0 - smoothstep(h1 - 0.0012, h1 + 0.0012, e));
  c = mix(c, mix(hor, DR2, 0.62 + 0.38 * smoothstep(0.0, 0.04, e)), 1.0 - smoothstep(h2 - 0.0012, h2 + 0.0012, e));
  c = mix(c, mix(hor, DR3, 0.75 + 0.25 * smoothstep(0.0, 0.025, e)), 1.0 - smoothstep(h3 - 0.0012, h3 + 0.0012, e));
  float mist = 0.45 + 0.35 * n2(vec2(az * 7.0 + u_time * 0.02, 1.0));
  return mix(c, hor, mist * exp(-y * 50.0));
}
vec3 waterDusk(vec3 ro, vec3 rd, float tw){
  vec3 p = ro + rd * tw, n = wnorm(p.xz, tw);
  vec3 r = reflect(rd, n); r.y = abs(r.y) + 0.003; r = normalize(r);
  vec3 refl = overFrames(skyDusk(r), p, r, 1e9, tw);
  float fres = pow(1.0 - clamp(dot(-rd, n), 0.0, 1.0), 2.5);
  vec3 c = mix(DWATER, refl, 0.44 + 0.54 * fres);
  float glit = pow(max(dot(r, normalize(P3 - vec3(0.0, 0.8, 0.0) - p)), 0.0), 150.0);    // the door's light on the water
  float reach = L3 - u_lit.y;                                                  // how far along the road the light has come
  c += LIGHT * max(u_lit.x, 0.5) * 1.25 * glit * smoothstep(-3.0, 1.0, dot(p.xz, vec2(sin(AX), cos(AX))) - reach);
  vec3 rdv = road(p.xz, tw, rd.y);
  float lit = smoothstep(0.0, 1.2, rdv.z - reach);                             // and the tiles it has reached
  c += mix(FCOOL * 0.20, LIGHT * 1.1, lit) * rdv.x + LIGHT * 0.22 * lit * rdv.y;
  return mix(c, hazeDusk(atan(rd.x, rd.z)) * 0.86, 1.0 - exp(-tw * 0.010));
}
vec3 duskScene(vec3 ro, vec3 rd, vec2 ndc){
  float tw = rd.y < -1e-4 ? -ro.y / rd.y : 1e9;
  vec3 c = tw < 1e8 ? waterDusk(ro, rd, tw) : skyDusk(rd);
  c = overFrames(c, ro, rd, tw, 0.0);
  float e = rd.y / max(length(rd.xz), 1e-4), az = atan(rd.x, rd.z);            // thin mist low over the water, in front of the frames' feet
  c = mix(c, hazeDusk(az), 0.34 * exp(-abs(e + 0.012) * 42.0) * (0.35 + 0.65 * n2(vec2(az * 9.0 + u_time * 0.035, 2.0))));
  vec3 d3 = P3 - ro; float z3 = dot(d3, u_f);                                  // light in the air between us and the door
  if (z3 > 0.2 && u_lit.x > 0.001) {
    vec2 v = ndc - vec2(dot(d3, u_r), dot(d3, u_u)) / z3 * u_cam.x;
    float r = length(v) * max(length(d3), 4.0) / 38.0, ang = atan(v.y, v.x);
    vec2 cs = vec2(cos(ang), sin(ang));
    float ray = n2(cs * 3.0 + vec2(u_time * 0.07, 3.0)) * 0.6 + n2(cs * 8.0 - vec2(1.0, u_time * 0.11)) * 0.4;
    ray = pow(ray, 2.4) * 2.2;
    float up = mix(0.45, 1.0, smoothstep(0.12, -0.20, v.y));                   // less of it climbs into the sky, where a label sits
    c += LIGHT * u_lit.x * (0.34 * exp(-r * r * 8.0) * smoothstep(0.08, 0.36, r) + 0.46 * ray * exp(-r * 2.5) * smoothstep(0.12, 0.34, r)) * up;
  }
  return c;
}
void main(){
  vec2 ndc = (v_uv * 2.0 - 1.0) * vec2(u_res.x / u_res.y, 1.0);
  vec3 rd = normalize(u_r * ndc.x + u_u * ndc.y + u_f * u_cam.x);
  vec3 c = (u_cam.z < 0.5 ? duskScene(u_c, rd, ndc) : mornScene(u_c, rd)) * u_cam.y;
  c = mix(c, 0.88 + 0.12 * tanh((c - 0.88) / 0.12), step(0.88, c));          // a soft shoulder instead of a clip
  c += (h21(gl_FragCoord.xy) - 0.5) / 170.0;                                  // fixed dither: no banding in the skies
  outColor = vec4(c, 1.0);
}`;
}

// speed: a radial blur towards the point we are heading for, jittered per pixel so it smears instead of ghosting
const STREAK = `
uniform vec2 u_ctr; uniform float u_amt;
float h21(vec2 p){ vec3 q = fract(vec3(p.xyx) * 0.1031); q += dot(q, q.yzx + 33.33); return fract((q.x + q.y) * q.z); }
void main(){
  vec2 d = v_uv - u_ctr; float j = h21(gl_FragCoord.xy); vec3 a = vec3(0.0);
  for (int i = 0; i < 28; i++) a += texture(u_tex0, u_ctr + d * (1.0 - u_amt * (float(i) + j) / 28.0)).rgb;
  outColor = vec4(a / 28.0, 1.0);
}`;

// ───────────────────────── setup: shader, sprites, the things adrift ─────────────────────────
function sprite(color, blur) {                           // one small 16:9 frame, 96 × 54, at one amount of defocus
  const pad = Math.ceil(6 + blur * 3), w = 96 + pad * 2, h = 54 + pad * 2, c = document.createElement("canvas");
  c.width = w; c.height = h;
  const x = c.getContext("2d");
  if (blur) x.filter = `blur(${blur}px)`;
  x.strokeStyle = color; x.lineWidth = 5; x.strokeRect(pad + 2.5, pad + 2.5, 91, 49);
  x.fillStyle = color; x.globalAlpha = 0.14; x.fillRect(pad + 5, pad + 5, 86, 44);
  return { c, w, h };
}
const BLURS = [0, 1.5, 4, 9, 18];
export async function setup(ctx, tokens, lib) {
  const fx = lib.shader(fragment(tokens, lib)), streak = lib.shader(STREAK);
  const spr = {};
  for (const [k, col] of [["cool", lib.color(tokens, "frame_cool")], ["warm", lib.color(tokens, "light")], ["gold", "#FFE9B8"]]) spr[k] = BLURS.map((b) => sprite(col, b));
  const H = lib.hash, ax = [Math.sin(AX), Math.cos(AX)], pe = [Math.cos(AX), -Math.sin(AX)];
  const adrift = (n, s0, s1, seed, wide) => Array.from({ length: n }, (_, i) => {
    let l = (H(seed, 2, i) * 2 - 1) * wide; if (Math.abs(l) < 0.9) l += l < 0 ? -1.2 : 1.2;        // keep the lens's own path clear
    const s = lib.lerp(s0, s1, H(seed, 1, i));
    return { x: ax[0] * s + pe[0] * l, z: ax[1] * s + pe[1] * l, y: 0.25 + 5.6 * Math.pow(H(seed, 3, i), 1.7), w: 0.15 + 0.36 * H(seed, 4, i),
      spin: H(seed, 5, i) * 6.283, vs: 0.3 + 0.9 * H(seed, 6, i), roll: (H(seed, 7, i) - 0.5) * 0.7, rise: 0.06 + 0.16 * H(seed, 8, i),
      ph: H(seed, 9, i) * 6.283, a: 0.35 + 0.6 * H(seed, 10, i) };
  });
  let lo = T_GO, hi = 5;                                 // the frame on which the camera is through the door
  for (let i = 0; i < 40; i++) { const m = (lo + hi) / 2; if (travel(m, lib) < L3) lo = m; else hi = m; }
  L = { fx, streak, spr, dusk: adrift(220, 0.5, L3 - 1.5, 11, 12).concat(adrift(80, 1, 30, 17, 4.5)), morn: adrift(70, L3 + 2, L3 + 34, 23, 12).concat(adrift(30, L3 + 3, L3 + 22, 29, 4.5)), tCross: hi };
}

// ───────────────────────── a frame ─────────────────────────
export function renderAt(t, ctx, tokens, lib) {
  const { W, H, seg, ease, clamp } = lib, K = cam(t, lib), inMorn = K.d >= L3;
  const parted = ease.outCubic(seg(t, T_DOOR, T_DOOR + 0.42)), open = OPEN0 + (1 - OPEN0) * parted;
  const light = 0.1 + parted * (0.9 + 0.5 * Math.exp(-Math.max(0, t - T_DOOR) / 0.28) + 0.35 * ease.inCubic(seg(t, T_ROAD, T_GO)));
  const uni = {
    u_c: K.c, u_r: K.r, u_u: K.u, u_f: K.f,
    u_cam: [FOCAL, 0.8 + 0.2 * ease.outCubic(seg(t, 0, 0.6)), inMorn ? 1 : 0, 0],
    u_on: [ease.inOutCubic(seg(t, T_OUT, T_OUT + 0.5)), seg(t, T_SB, T_SB + 0.42), open,
      t >= T_ROAD && t < T_GO ? Math.min(5.999, (t - T_ROAD) / (T_GO - T_ROAD) * 6) : -1],
    u_lit: [light, 2.5 + (L3 - travel(T_GO, lib) - 1) * Math.pow(seg(t, T_DOOR, T_GO), 1.7) + (t >= T_GO ? 60 : 0), 0, 0],
  };
  // 1  the world, then what drifts in it, on one layer the lens can work on
  const w = lib.layer("wiw-world");
  w.drawImage(L.fx.render(t, uni), 0, 0, W, H);
  farFrames(w, t, K, inMorn, tokens, lib);
  adriftDraw(w, t, K, inMorn, light, keepClear(t, K, inMorn, lib), lib);
  if (!inMorn) heroFrame(w, t, K, tokens, lib);
  // 2  the lens: focus lands in the first half second; speed pulls the picture into streaks around the door; a soft glow
  const defocus = 10 * (1 - ease.outCubic(seg(t, 0.03, 0.5)));
  const speed = (travel(t + 1 / 60, lib) - travel(t - 1 / 60, lib)) * 30;      // metres per second
  const streak = clamp((speed - 6) / 90, 0, 1);
  let img = w.canvas;
  if (streak > 0.01) {
    const v = project(K, PORT[2].p), ahead = v.z > 0.5;
    img = L.streak.render(t, { u_ctr: [ahead ? clamp(v.x / W, 0.2, 0.8) : 0.5, ahead ? clamp(1 - v.y / H, 0.25, 0.75) : 0.5], u_amt: 0.26 * streak }, { u_tex0: w.canvas });
  }
  ctx.save();
  if (defocus > 0.3) ctx.filter = `blur(${defocus.toFixed(2)}px)`;
  ctx.drawImage(img, 0, 0, W, H);
  ctx.restore();
  ctx.save(); ctx.globalCompositeOperation = "screen"; ctx.globalAlpha = 0.20; ctx.filter = "blur(26px)"; ctx.drawImage(img, 0, 0, W, H); ctx.restore();
  if (defocus > 0.3) lib.grain(ctx, 0, { amount: 0.035 * Math.min(1, defocus / 5), fps: 24, seed: 5 });   // t = 0: the same grain on every frame
  lib.vignette(ctx, { strength: inMorn ? 0.12 : 0.34, inner: 0.5, color: inMorn ? "#1f4f52" : "#04051a" });
  const flare = Math.exp(-Math.pow((t - L.tCross) / 0.09, 2)) * 0.42;          // crossing the threshold
  if (flare > 0.004) { ctx.fillStyle = lib.rgba(lib.color(tokens, "morn_sun"), flare); ctx.fillRect(0, 0, W, H); }
  // 3  type
  if (!inMorn) duskType(ctx, t, K, tokens, lib); else mornType(ctx, t, tokens, lib);
}

function keepClear(t, K, inMorn, lib) {                  // where the type is at t: [x0, y0, x1, y1, how present]
  if (inMorn) return [[560, 190, 1360, 400, lib.seg(t, L.tCross - 0.05, L.tCross + 0.2)]];
  const out = [[520, 84, 1400, 286, lib.seg(t, 0.7, 1.0)]];
  PORT.forEach((q, k) => {
    const top = project(K, [q.p[0], q.p[1] + q.s[1], q.p[2]]), a = lib.seg(t, [T_OUT, T_SB, T_DOOR][k] - 0.25, [T_OUT, T_SB, T_DOOR][k] + 0.05);
    if (top.z > 1 && a > 0) out.push([top.x - 86, top.y - 98, top.x + 96, top.y - 6, a]);
  });
  return out;
}
function adriftDraw(w, t, K, inMorn, light, keep, lib) {
  const list = inMorn ? L.morn : L.dusk, focus = inMorn ? 30 : 22;
  w.save(); w.globalCompositeOperation = "lighter";
  const put = (P, m, sp, a, flip) => {
    const q = project(K, P); if (q.z < 0.35 || q.z > 70 || a < 0.01) return;
    const px = m.w * FPX / q.z, sc = px / 96;
    if (q.x < -px * 2 || q.x > 1920 + px * 2 || q.y < -px * 2 || q.y > 1080 + px * 2) return;
    const blur = Math.min(30, Math.abs(1 / q.z - 1 / focus) * 300) / sc + (flip ? 2.5 : 0);
    let bi = 0; for (let i = 1; i < BLURS.length; i++) if (Math.abs(BLURS[i] - blur) < Math.abs(BLURS[bi] - blur)) bi = i;
    let near = lib.smoothstep(0.35, 1.4, q.z) * (1 - lib.smoothstep(46, 68, q.z));
    for (const r of keep) near *= 1 - r[4] * (1 - lib.smoothstep(6, 46, Math.hypot(Math.max(r[0] - q.x, 0, q.x - r[2]), Math.max(r[1] - q.y, 0, q.y - r[3]))));
    const s = sp[bi];
    w.save(); w.globalAlpha = Math.min(1, a * near * (bi >= 3 ? 0.55 : 1));
    w.translate(q.x, q.y); w.rotate(m.roll + 0.25 * Math.sin(t * 0.6 + m.ph));
    w.scale(sc * Math.cos(m.spin + t * m.vs), sc * (flip ? -1 : 1));
    w.drawImage(s.c, -s.w / 2, -s.h / 2); w.restore();
  };
  for (const m of list) {
    const y = m.y + m.rise * t + 0.12 * Math.sin(t * 0.9 + m.ph);
    const P = [m.x + 0.25 * Math.sin(t * 0.5 + m.ph), y, m.z + 0.2 * Math.cos(t * 0.4 + m.ph)];
    const vis = shows(K, P); if (!vis) continue;
    const tw = 0.72 + 0.28 * Math.sin(t * 2.1 + m.ph * 3), a = m.a * tw * vis;
    if (inMorn) { put(P, m, L.spr.gold, a * 0.8, false); continue; }
    const warm = lib.clamp(light * 0.75, 0, 1) * Math.exp(-Math.hypot(P[0] - PORT[2].p[0], P[2] - PORT[2].p[2]) / 30);
    put(P, m, L.spr.cool, a * (1 - warm), false);
    if (warm > 0.02) put(P, m, L.spr.warm, a * warm * 1.2, false);
    if (y < 3.2) put([P[0] + 0.05 * Math.sin(t * 3 + m.ph), -y, P[2]], m, L.spr.cool, a * 0.30, true);     // on the water
  }
  w.restore();
}
function farFrames(w, t, K, inMorn, tokens, lib) {
  w.save(); w.lineJoin = "miter";
  for (const f of inMorn ? [NEXT] : FAR_DUSK) {
    if (!shows(K, f.p)) continue;
    const r = [Math.cos(f.yaw), 0, -Math.sin(f.yaw)];
    const quad = (up) => [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => project(K, [f.p[0] + r[0] * a * f.hw, up * (f.p[1] + b * f.hh), f.p[2] + r[2] * a * f.hw]));
    const q = quad(1); if (q.some((p) => p.z < 4)) continue;
    const path = (pts) => { w.beginPath(); pts.forEach((p, i) => (i ? w.lineTo(p.x, p.y) : w.moveTo(p.x, p.y))); w.closePath(); };
    w.lineWidth = Math.max(1.5, 0.12 * FPX / q[0].z);
    if (inMorn) {                                        // a small coral door under the sun, and its colour on the water
      const coral = lib.color(tokens, "next_door"), cx = (q[0].x + q[2].x) / 2, cy = (q[0].y + q[2].y) / 2, rr = Math.abs(q[1].x - q[0].x) * 2.2;
      const halo = w.createRadialGradient(cx, cy, 0, cx, cy, rr); halo.addColorStop(0, lib.rgba(coral, 0.5)); halo.addColorStop(1, lib.rgba(coral, 0));
      w.globalAlpha = 1; w.fillStyle = halo; w.fillRect(cx - rr, cy - rr, rr * 2, rr * 2);
      w.fillStyle = coral; w.strokeStyle = lib.color(tokens, "ink");
      path(q); w.globalAlpha = 0.95; w.fill(); w.globalAlpha = 0.8; w.stroke();
      const m = quad(-1), x0 = Math.min(m[0].x, m[3].x), x1 = Math.max(m[1].x, m[2].x), y0 = Math.min(m[0].y, m[1].y), y1 = Math.max(m[2].y, m[3].y);
      for (let i = 0; i < 9; i++) {
        const sway = 2.2 * Math.sin(i * 1.9 + t * 3.1) * (1 + i * 0.3);
        w.globalAlpha = 0.34 * (1 - i / 10); w.fillRect(x0 + sway, y0 + (y1 - y0) * 1.5 * i / 9, x1 - x0, (y1 - y0) * 1.5 / 9 * 0.62);
      }
    } else {                                             // thin, far, unlit: other people's frames
      w.strokeStyle = lib.color(tokens, "frame_cool");
      path(q); w.globalAlpha = 0.42 * Math.exp(-q[0].z / 300); w.stroke();
      path(quad(-1)); w.globalAlpha *= 0.3; w.stroke();
    }
  }
  w.restore();
}
function heroFrame(w, t, K, tokens, lib) {               // the first thing in the film: a frame, and we go through it
  const c = [Math.sin(AX) * HERO.s, HERO.y, Math.cos(AX) * HERO.s], hw = HERO.w / 2, hh = hw * 9 / 16;
  const r = [Math.cos(AX), 0, -Math.sin(AX)];
  const pts = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([a, b]) => project(K, [c[0] + r[0] * a * hw, c[1] + b * hh, c[2] + r[2] * a * hw]));
  if (pts.some((p) => p.z < 0.12)) return;
  const z = pts[0].z, blur = Math.min(26, 4 + 16 / z);
  w.save(); w.globalCompositeOperation = "lighter"; w.filter = `blur(${blur.toFixed(2)}px)`;
  w.strokeStyle = lib.color(tokens, "frame_cool"); w.lineWidth = Math.max(6, 60 / z); w.lineJoin = "miter";
  w.globalAlpha = 0.85 * lib.smoothstep(0.12, 0.5, z);
  w.beginPath(); pts.forEach((p, i) => (i ? w.lineTo(p.x, p.y) : w.moveTo(p.x, p.y))); w.closePath(); w.stroke();
  w.restore();
}

// each word comes into focus: blurred and faint, then sharp
function focusWords(ctx, lay, groups, t, t0, gap, lib) {
  groups.forEach(([a, b], k) => {
    const u = lib.ease.outCubic(lib.seg(t, t0 + k * gap, t0 + k * gap + 0.5)); if (u <= 0) return;
    ctx.save(); ctx.globalAlpha *= u;
    const bl = 12 * (1 - u); if (bl > 0.25) ctx.filter = `blur(${bl.toFixed(2)}px)`;
    lib.drawGlyphs(ctx, lay, (g) => (g.i >= a && g.i < b ? {} : null));
    ctx.restore();
  });
}
const wordsOf = (str, lib) => { const gs = lib.graphemes(str), out = []; let a = 0; gs.forEach((ch, i) => { if (ch === " ") { out.push([a, i]); a = i + 1; } }); out.push([a, gs.length]); return out; };

function duskType(ctx, t, K, tokens, lib) {
  const fade = 1 - lib.seg(t, T_GO, T_GO + 0.13); if (fade <= 0) return;
  const fg = lib.color(tokens, "fg");
  ctx.save(); ctx.globalAlpha = fade; ctx.fillStyle = fg; ctx.shadowColor = "rgba(4,5,26,0.85)"; ctx.shadowBlur = 22;
  // the title, in the dark top of the sky; the water below is left to the picture
  lib.setFont(ctx, tokens, "display", 96, { weight: 400 });
  const en = lib.layoutText(ctx, lib.TITLE_EN, { x: 960, y: 176, align: "center", tracking: 1.5 });
  focusWords(ctx, en, wordsOf(lib.TITLE_EN, lib), t, 0.85, 0.13, lib);
  lib.setFont(ctx, tokens, "zh", 60, { weight: 700 });
  const zh = lib.layoutText(ctx, lib.TITLE_ZH, { x: 964, y: 258, align: "center", tracking: 8 });
  focusWords(ctx, zh, [[0, 4], [4, 9]], t, 1.5, 0.26, lib);
  // a name over each frame, riding on it
  PORT.forEach((q, k) => {
    const t0 = [T_OUT, T_SB, T_DOOR][k] + 0.04, u = lib.ease.outQuint(lib.seg(t, t0, t0 + 0.26)); if (u <= 0) return;
    const top = project(K, [q.p[0], q.p[1] + q.s[1], q.p[2]]); if (top.z < 1) return;
    const x = lib.clamp(top.x, 176, 1744), y = top.y - 28 + 10 * (1 - u);
    ctx.save(); ctx.globalAlpha = fade * u;
    const bl = 8 * (1 - u); if (bl > 0.25) ctx.filter = `blur(${bl.toFixed(2)}px)`;
    ctx.fillStyle = k === 2 ? lib.mixColor(fg, lib.color(tokens, "accent"), 0.35) : fg;
    lib.setFont(ctx, tokens, "zh", 60, { weight: 700 });             // one word per frame, well above the label size floor
    lib.drawText(ctx, lib.MOTIF[k].zh, x + 5, y, { align: "center", tracking: 10 });
    ctx.restore();
  });
  ctx.restore();
}
function mornType(ctx, t, tokens, lib) {
  const u = lib.ease.outCubic(lib.seg(t, L.tCross - 0.02, L.tCross + 0.26)); if (u <= 0) return;
  ctx.save(); ctx.globalAlpha = u; ctx.fillStyle = lib.color(tokens, "ink");
  const bl = 10 * (1 - u); if (bl > 0.25) ctx.filter = `blur(${bl.toFixed(2)}px)`;
  lib.setFont(ctx, tokens, "zh", 88, { weight: 700 });
  lib.drawText(ctx, "走进去的世界", 960 + 7, 292, { align: "center", tracking: 14 });
  lib.setFont(ctx, tokens, "display", 48, { weight: 600 });
  lib.drawText(ctx, "WALK-IN WORLD", 960 + 7, 376, { align: "center", tracking: 48 * 0.26 });
  ctx.restore();
}

// foley (events.json is generated from this list; the times are the scene's own constants)
const pan = (x) => Math.round(Math.max(-1, Math.min(1, (x / 960 - 1) * 0.7)) * 100) / 100;
export const FOLEY = [
  { t: 0.3, sfx: "whoosh", gain_db: -9, pan: 0, dist: 1.5, dur: 0.7, tone: 0.3 },                       // through the first frame
  { t: T_OUT, sfx: "paper", gain_db: -7, pan: pan(440), dist: 2, dur: 0.45 },                            // the outline draws itself
  // T_SB: the six panels are six celesta notes in the score, no foley on top of them
  { t: T_DOOR, sfx: "shimmer", gain_db: -6, pan: pan(1375), dist: 2 },                                   // the door opens
  { t: 4.36, sfx: "whoosh", gain_db: -5, pan_from: pan(1375), pan_to: 0, dist: 1, dur: 0.9, dir: "up", tone: 0.6 },   // through it
];
