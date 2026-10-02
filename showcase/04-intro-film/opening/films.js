// The films on the waterfall cards: 28 procedural shots (cosmos, glass, landscapes …) rendered once into an atlas at build,
// plus look/assets/films.jpg (41 cuts of this repo's own swatches and showcases, tools/look/film_atlas.py).
// Atlas layout for both: one film per row, 16 frames per row, 256x144 per tile.
// Procedural shots loop seamlessly over their 16 frames (all motion is periodic in ph = 2π·k/16); real cuts ping-pong.
import * as THREE from "three";

export const TW = 256, TH = 144, NF = 16, FPS = 8;
export const PROC = ["nebula", "galaxy", "blackhole", "planet", "glass", "prism", "aurora", "ocean", "dunes", "bokeh",
  "fire", "ink", "geode", "sun", "warp", "forest", "chrome", "bloom", "underwater", "lake", "jelly", "storm", "snow",
  "trails", "mesh", "rain", "twinsuns", "earth"];

const FRAG = /* glsl */ `
precision highp float;
uniform float uFilm; uniform float uK; varying vec2 vUv;
#define PI 3.14159265
#define TAU 6.2831853
float h21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec2 h22(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
float h31(vec3 p){ p = fract(p * 0.1031); p += dot(p, p.zyx + 31.32); return fract((p.x + p.y) * p.z); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f * f * (3. - 2. * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y); }
float vn3(vec3 p){ vec3 i = floor(p), f = fract(p); vec3 u = f * f * (3. - 2. * f);
  float a = mix(mix(h31(i), h31(i + vec3(1,0,0)), u.x), mix(h31(i + vec3(0,1,0)), h31(i + vec3(1,1,0)), u.x), u.y);
  float b = mix(mix(h31(i + vec3(0,0,1)), h31(i + vec3(1,0,1)), u.x), mix(h31(i + vec3(0,1,1)), h31(i + vec3(1,1,1)), u.x), u.y);
  return mix(a, b, u.z); }
float fbm(vec2 p){ float a = .5, s = 0.; mat2 m = mat2(1.6, 1.2, -1.2, 1.6); for (int i = 0; i < 6; i++) { s += a * vn(p); p = m * p; a *= .5; } return s; }
float fbm3(vec3 p){ float a = .5, s = 0.; for (int i = 0; i < 5; i++) { s += a * vn3(p); p = p * 2.03 + vec3(1.7, 9.2, 3.1); a *= .5; } return s; }
mat2 rot(float a){ float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
vec3 hue(float h){ return clamp(abs(mod(h * 6. + vec3(0, 4, 2), 6.) - 3.) - 1., 0., 1.); }
float stars(vec2 p, float d, float ph, float sd){ vec2 g = p * d; vec2 i = floor(g), f = fract(g); vec2 o = h22(i + sd);
  float r = length(f - o); float b = pow(h21(i + 7.1 + sd), 9.) * (0.75 + 0.25 * sin(ph + h21(i) * 30.)); return b * smoothstep(0.08, 0.0, r) * 2.2; }
float tri(vec2 p, float r){ const float k = sqrt(3.0); p.x = abs(p.x) - r; p.y = p.y + r / k; if (p.x + k * p.y > 0.) p = vec2(p.x - k * p.y, -k * p.x - p.y) / 2.; p.x -= clamp(p.x, -2. * r, 0.); return -length(p) * sign(p.y); }

vec3 nebula(vec2 p, vec2 c, float ph){
  vec2 q = p * 1.5 + c * 0.12; float w = fbm(q * 1.3 + 3.1);
  float n = fbm(q + w * 1.4), m = fbm(q * 2.2 - 4.0 + w);
  vec3 col = mix(vec3(0.01, 0.015, 0.04), vec3(0.06, 0.18, 0.36), smoothstep(0.32, 0.78, n));
  col = mix(col, vec3(0.95, 0.42, 0.16), smoothstep(0.52, 0.86, m) * smoothstep(0.38, 0.72, n));
  col += vec3(1.0, 0.85, 0.7) * pow(smoothstep(0.55, 0.95, n * m * 1.7), 3.) * 1.1;
  return col + stars(p, 40., ph, 0.) + stars(p, 90., ph * 2., 3.) * 0.6;
}
vec3 galaxy(vec2 p, float ph){
  p *= rot(0.4); p.y *= 2.1; float r = length(p), a = atan(p.y, p.x) + ph * 0.5;
  float arm = pow(max(0.5 + 0.5 * cos(2. * (a - log(r + 0.02) * 2.6)), 0.), 3.);
  float dust = fbm(p * 7.0 + 2.0);
  float d = exp(-r * 4.2) * (0.35 + 1.4 * arm * smoothstep(0.02, 0.2, r)) * (0.6 + 0.6 * dust);
  vec3 col = mix(vec3(0.35, 0.55, 1.0), vec3(1.0, 0.82, 0.6), exp(-r * 6.0)) * d * 2.2;
  col += vec3(1.0, 0.9, 0.75) * exp(-r * r * 260.) * 2.5;
  col *= 1. - 0.6 * smoothstep(0.5, 0.75, dust) * arm * smoothstep(0.05, 0.3, r);
  return col + stars(p * vec2(1., 0.48), 50., ph, 1.);
}
vec3 blackhole(vec2 p, float ph){
  float r = length(p); vec2 q = p * vec2(1., 3.6); float e = length(q), a = atan(q.y, q.x);
  float turb = fbm(vec2(cos(a + ph * 0.5), sin(a + ph * 0.5)) * 2.5 + e * 5.);
  float disk = smoothstep(0.85, 0.42, e) * smoothstep(0.24, 0.34, e) * (0.5 + 0.9 * turb);
  float dop = 1.0 - 0.75 * clamp(p.x / max(e, 0.05) * 1.2, -1., 1.);
  vec3 dc = mix(vec3(1.0, 0.45, 0.12), vec3(1.0, 0.92, 0.8), smoothstep(0.6, 0.3, e)) * disk * dop * 1.6;
  float arc = exp(-pow((r - 0.255) / 0.035, 2.)) * (0.55 + 0.6 * turb) * smoothstep(-0.12, 0.1, p.y);
  float ring = exp(-pow((r - 0.205) / 0.008, 2.)) * 1.4;
  float shadow = smoothstep(0.19, 0.205, r);
  vec2 lp = p * (1. + 0.05 / max(r * r, 0.01));
  vec3 bg = stars(lp, 45., ph, 2.) * vec3(0.8, 0.9, 1.) + vec3(0.03, 0.04, 0.08) * fbm(lp * 3.);
  vec3 col = bg * shadow + (vec3(1.0, 0.7, 0.4) * arc + vec3(1.0, 0.85, 0.65) * ring) * 1.4;
  float front = step(p.y, 0.0);
  col = mix(col * shadow, col, 0.) + dc * mix(shadow, 1.0, front);
  return col;
}
vec3 planet(vec2 p, float ph){
  vec3 col = vec3(0.005, 0.008, 0.02) + stars(p, 60., ph, 4.);
  vec2 c = vec2(0.22, -0.08); float R = 0.42; vec2 d = (p - c) / R; float rr = dot(d, d);
  vec2 rp = (p - c) * rot(-0.35); float re = length(rp * vec2(1., 4.2)) / R;
  float ringB = smoothstep(1.35, 1.4, re) * smoothstep(2.25, 2.15, re) * (0.55 + 0.45 * sin(re * 60.)) * (0.6 + 0.4 * vn(vec2(re * 40., 0.)));
  vec3 ringC = vec3(0.85, 0.75, 0.6) * ringB * 0.9;
  if (rp.y > 0.0) col += ringC;                                                     // far half of the ring, behind the planet
  if (rr < 1.0) {
    vec3 n = vec3(d, sqrt(1. - rr)); vec3 L = normalize(vec3(-0.8, 0.35, 0.45));
    float lat = n.y, lon = atan(n.x, n.z) + 0.15 * sin(ph);
    float bands = fbm(vec2(lat * 9. + 0.3 * fbm(vec2(lon * 3., lat * 20.)), lon * 1.2));
    vec3 base = mix(vec3(0.55, 0.38, 0.24), vec3(0.92, 0.8, 0.62), bands);
    float dif = max(dot(n, L), 0.); col = base * (0.02 + 1.2 * pow(dif, 0.8));
    col += vec3(0.4, 0.6, 1.0) * pow(1. - n.z, 3.) * dif * 0.8;
    float sh = smoothstep(0.02, -0.02, abs(rp.y * 4.2 / R + 0.0) - 0.05) * 0.;
    col *= 1. - sh;
  }
  col += vec3(0.4, 0.6, 1.0) * exp(-pow((sqrt(rr) - 1.0) / 0.05, 2.)) * 0.6 * smoothstep(0.2, -0.6, d.x);
  if (rp.y <= 0.0 || rr >= 1.0) col += ringC * step(rp.y, 0.0);
  return col;
}
float smin(float a, float b, float k){ float h = clamp(0.5 + 0.5 * (b - a) / k, 0., 1.); return mix(b, a, h) - k * h * (1. - h); }
float blobs(vec3 q, float ph){ float d = 1e9;
  for (int i = 0; i < 4; i++) { float fi = float(i);
    vec3 c = vec3(cos(ph + fi * 1.7) * 0.55, sin(ph + fi * 2.3) * 0.32, sin(ph + fi * 1.1) * 0.25);
    d = smin(d, length(q - c) - (0.3 + 0.06 * fi), 0.32); } return d; }
vec3 studio(vec3 d){ float a = smoothstep(0.6, 0.95, d.y) * 1.8 + smoothstep(0.3, 0.0, abs(d.x - 0.7)) * smoothstep(-0.2, 0.3, d.y) * 1.4;
  return vec3(0.02, 0.025, 0.04) + vec3(1.0, 0.82, 0.62) * a + vec3(0.25, 0.45, 0.9) * smoothstep(0.2, -0.9, d.x) * 0.5; }
vec3 glass(vec2 p, float ph){
  vec3 ro = vec3(0., 0., -2.6), rd = normalize(vec3(p, 1.5)); float t = 0.; float hit = 0.;
  for (int i = 0; i < 56; i++) { float d = blobs(ro + rd * t, ph); if (d < 0.002) { hit = 1.; break; } t += d; if (t > 6.) break; }
  vec3 bg = mix(vec3(0.03, 0.035, 0.05), vec3(0.12, 0.09, 0.08), smoothstep(-0.6, 0.5, p.y)) + vec3(1.0, 0.75, 0.5) * exp(-pow((p.x - 0.55) / 0.08, 2.)) * 0.25;
  if (hit < 0.5) return bg;
  vec3 pos = ro + rd * t; vec2 e = vec2(0.002, 0.);
  vec3 n = normalize(vec3(blobs(pos + e.xyy, ph) - blobs(pos - e.xyy, ph), blobs(pos + e.yxy, ph) - blobs(pos - e.yxy, ph), blobs(pos + e.yyx, ph) - blobs(pos - e.yyx, ph)));
  float fr = pow(1. - max(dot(-rd, n), 0.), 3.);
  vec3 rc = vec3(studio(refract(rd, n, 0.62)).r, studio(refract(rd, n, 0.66)).g, studio(refract(rd, n, 0.70)).b);
  vec3 col = rc * vec3(0.75, 0.88, 1.0) + studio(reflect(rd, n)) * (0.08 + 0.9 * fr);
  return col + pow(max(dot(reflect(rd, n), normalize(vec3(0.5, 0.8, -0.3))), 0.), 80.) * 3.;
}
vec3 prism(vec2 p, float ph){
  vec3 col = vec3(0.012, 0.012, 0.018);
  float d = tri(p * rot(0.05 * sin(ph)), 0.2);
  float beam = exp(-pow((p.y - 0.12 * (p.x + 0.9) * 0.15 - 0.0) / 0.012, 2.)) * step(p.x, -0.1) * 2.2;
  float ang = atan(p.y + 0.02, p.x - 0.08);
  float fan = step(0.08, p.x) * smoothstep(0.55, 0.0, abs(ang + 0.12) - 0.0) * smoothstep(-0.38, -0.26, ang) * smoothstep(0.12, 0.0, ang);
  vec3 spec = hue(clamp((ang + 0.38) / 0.5, 0., 1.) * 0.8) * fan * (1.1 + 0.2 * sin(ph)) * smoothstep(1.2, 0.2, p.x);
  col += vec3(1.) * beam + spec;
  float edge = exp(-abs(d) * 200.) * 1.2, inside = smoothstep(0.003, -0.003, d);
  col = mix(col, vec3(0.06, 0.07, 0.09) + spec * 0.4, inside * 0.7) + vec3(0.9, 0.95, 1.0) * edge;
  return col;
}
vec3 aurora(vec2 p, vec2 uv, float ph){
  vec3 col = mix(vec3(0.01, 0.02, 0.05), vec3(0.0, 0.05, 0.09), uv.y) + stars(p, 70., ph, 5.) * 0.8;
  vec2 q = uv; bool refl = q.y < 0.24; if (refl) q.y = 0.48 - q.y + 0.004 * sin(q.x * 80. + ph * 2.);
  vec3 a = vec3(0.);
  for (int i = 0; i < 3; i++) { float fi = float(i);
    float y0 = 0.55 + 0.08 * fi + 0.06 * sin(q.x * 4. + ph + fi * 2.) + 0.05 * fbm(vec2(q.x * 3. + fi, fi));
    float dy = q.y - y0; float curtain = exp(-max(-dy, 0.) * 60.) * exp(-max(dy, 0.) * (5. - fi)) * (0.4 + 0.8 * fbm(vec2(q.x * 30. + fi * 7., q.y * 2. + sin(ph) * 0.2)));
    a += mix(vec3(0.1, 1.0, 0.55), vec3(0.75, 0.25, 0.9), smoothstep(0.0, 0.2, dy)) * curtain * (0.9 - 0.2 * fi); }
  col += a * (refl ? 0.45 : 1.0);
  float ridge = 0.26 + 0.12 * fbm(vec2(uv.x * 2.6, 1.)) + 0.04 * fbm(vec2(uv.x * 12., 2.));
  if (!refl && uv.y < ridge) col = vec3(0.004, 0.006, 0.012) + a * 0.02;
  if (refl) { float rr = 0.48 - ridge; if (uv.y > rr) col = vec3(0.004, 0.006, 0.012); col *= vec3(0.6, 0.75, 0.9); }
  return col;
}
vec3 ocean(vec2 p, vec2 uv, float ph){
  float hz = 0.42; vec3 col;
  vec2 sp = vec2(0.5, 0.47);
  if (uv.y > hz) {
    float y = (uv.y - hz) / (1. - hz);
    col = mix(vec3(1.0, 0.45, 0.16), vec3(0.18, 0.12, 0.32), pow(y, 0.6));
    float cl = fbm(vec2(uv.x * 3. + 0.05 * sin(ph), y * 9.)); col = mix(col, vec3(0.98, 0.55, 0.35) * (0.5 + y), smoothstep(0.55, 0.75, cl) * 0.6);
    float sd = length((uv - sp) * vec2(1.78, 1.)); col += vec3(1.0, 0.85, 0.55) * (smoothstep(0.075, 0.068, sd) * 2.5 + exp(-sd * 9.) * 0.6);
  } else {
    float z = 1. / (hz - uv.y + 0.02); vec2 w = vec2(uv.x * z * 0.6, z);
    float wv = vn(w * vec2(3., 0.6) + vec2(0.3 * sin(ph), 0.3 * cos(ph))) + 0.5 * vn(w * vec2(9., 2.) - vec2(0.2 * cos(ph), 0.2 * sin(ph)));
    col = mix(vec3(0.02, 0.04, 0.09), vec3(0.25, 0.12, 0.2), smoothstep(0.0, hz, uv.y));
    float glit = smoothstep(0.75, 1.0, wv * 0.7 + 0.3 * h21(floor(w * vec2(40., 8.)) + floor(uK / 2.))) * exp(-pow((uv.x - sp.x) / (0.05 + 0.25 * (hz - uv.y)), 2.));
    col += vec3(1.0, 0.7, 0.35) * glit * 2.2 + vec3(1.0, 0.5, 0.25) * exp(-pow((uv.x - 0.5) / 0.3, 2.)) * smoothstep(0.1, hz, uv.y) * 0.25;
  }
  return col;
}
vec3 dunes(vec2 uv, float ph){
  vec3 col = mix(vec3(1.0, 0.72, 0.45), vec3(0.42, 0.55, 0.78), pow(uv.y, 0.8));
  col += vec3(1.0, 0.9, 0.7) * exp(-length((uv - vec2(0.8, 0.62)) * vec2(1.78, 1.)) * 6.) * 0.8;
  for (int i = 0; i < 5; i++) { float fi = float(i); float base = 0.62 - fi * 0.13;
    float x = uv.x * (1.2 + fi * 0.6) + fi * 3.7 + 0.01 * sin(ph);
    float h = base + 0.08 * sin(x * 2.2) + 0.05 * sin(x * 5.1 + fi) + 0.02 * fbm(vec2(x * 3., fi));
    if (uv.y < h) { float slope = cos(x * 2.2) * 0.17 + cos(x * 5.1 + fi) * 0.25;
      vec3 lit = mix(vec3(0.95, 0.6, 0.32), vec3(0.75, 0.38, 0.22), fi / 5.), shd = mix(vec3(0.38, 0.25, 0.35), vec3(0.18, 0.12, 0.2), fi / 5.);
      col = mix(shd, lit, smoothstep(-0.05, 0.05, -slope)) * (1. - 0.1 * fbm(vec2(uv.x * 60., uv.y * 300.))); col = mix(col, vec3(1.0, 0.75, 0.55), 0.18 * (4. - fi) / 4.); }
  }
  return col;
}
vec3 bokeh(vec2 p, float ph){
  vec3 col = vec3(0.012, 0.01, 0.018);
  for (int i = 0; i < 26; i++) { float fi = float(i); vec2 c = vec2(h21(vec2(fi, 1.)) * 2. - 1., h21(vec2(fi, 2.)) - 0.5) * vec2(0.95, 0.6);
    c += 0.04 * vec2(cos(ph + fi), sin(ph * 1. + fi * 1.3)); float r = 0.04 + 0.12 * pow(h21(vec2(fi, 3.)), 2.);
    float d = length(p - c); float disk = smoothstep(r, r - 0.006, d) * (0.45 + 0.55 * smoothstep(r * 0.6, r, d));
    vec3 tint = mix(vec3(1.0, 0.62, 0.25), mix(vec3(1.0, 0.25, 0.2), vec3(0.4, 0.6, 1.0), step(0.5, h21(vec2(fi, 5.)))), step(0.6, h21(vec2(fi, 4.))));
    col += tint * disk * (0.35 + 0.5 * h21(vec2(fi, 6.))); }
  return col;
}
vec3 fire(vec2 p, vec2 uv, float ph){
  vec3 q = vec3(p.x * 3.2, uv.y * 3.0 - 0.0, 0.) + vec3(0., 0.5 * cos(ph), 0.5 * sin(ph));
  float n = fbm3(q + vec3(0., -uv.y * 1.5, 0.));
  float f = clamp(n * 1.6 - uv.y * 1.25 + 0.15 - abs(p.x) * 0.7, 0., 1.);
  vec3 col = vec3(1.5, 0.45, 0.06) * smoothstep(0.1, 0.5, f) + vec3(1.0, 0.9, 0.5) * smoothstep(0.45, 0.85, f);
  for (int i = 0; i < 20; i++) { float fi = float(i); float y = fract(h21(vec2(fi, 9.)) + uK / 16. * (1. + floor(h21(vec2(fi, 8.)) * 2.)));
    vec2 e = vec2((h21(vec2(fi, 7.)) - 0.5) * 1.2 + 0.05 * sin(y * 12. + fi), y * 1.1 - 0.5);
    col += vec3(1.0, 0.55, 0.15) * smoothstep(0.012, 0.0, length(p - e)) * 1.5; }
  return col + vec3(0.03, 0.01, 0.0);
}
vec3 ink(vec2 p, float ph){
  vec3 col = vec3(0.95, 0.93, 0.89);
  vec2 q = p * 1.6; vec3 o = vec3(0.4 * cos(ph), 0.4 * sin(ph), 0.);
  float w = fbm3(vec3(q, 0.) + o); float a = fbm3(vec3(q * 1.3 + w * 1.6, 2.) + o * 0.7), b = fbm3(vec3(q * 1.1 - w * 1.4, 5.) - o * 0.6);
  col = mix(col, vec3(0.12, 0.16, 0.45), smoothstep(0.5, 0.72, a) * 0.95);
  col = mix(col, vec3(0.8, 0.12, 0.18), smoothstep(0.52, 0.75, b) * 0.9);
  col = mix(col, vec3(0.95, 0.65, 0.2), smoothstep(0.6, 0.8, a * b * 1.8) * 0.6);
  return col;
}
vec3 geode(vec2 p, float ph){
  vec2 g = p * 7.; vec2 i = floor(g), f = fract(g); float md = 8., md2 = 8.; vec2 mc;
  for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) { vec2 o = vec2(x, y); vec2 r = o + h22(i + o) - f; float d = dot(r, r);
    if (d < md) { md2 = md; md = d; mc = i + o; } else if (d < md2) md2 = d; }
  float edge = sqrt(md2) - sqrt(md); float r = length(p);
  float k = h21(mc); vec3 c = mix(vec3(0.35, 0.12, 0.55), vec3(0.85, 0.55, 0.95), k) * smoothstep(0.65, 0.1, r);
  c = mix(c, vec3(1.0, 0.75, 0.35), smoothstep(0.42, 0.55, r) * 0.9);
  c *= 0.55 + 0.6 * smoothstep(0.0, 0.25, edge);
  c += vec3(1.) * pow(max(sin(ph + k * TAU), 0.), 24.) * smoothstep(0.1, 0.0, md) * 1.5;
  return c * smoothstep(0.75, 0.6, r) + vec3(0.04, 0.03, 0.03) * step(0.6, r);
}
vec3 sun(vec2 p, float ph){
  vec2 c = vec2(-0.1, -1.05); float R = 0.95; float r = length(p - c);
  vec3 col = vec3(0.01, 0.005, 0.0);
  if (r < R) { vec2 q = (p - c) * 10.; float g = fbm(q + vec2(0.3 * cos(ph), 0.3 * sin(ph))) ; float limb = pow(1. - (r / R) * (r / R), 0.35);
    col = mix(vec3(1.0, 0.35, 0.03), vec3(1.0, 0.85, 0.4), g) * (0.6 + 1.1 * limb); }
  col += vec3(1.0, 0.45, 0.1) * exp(-(r - R) * 9.) * step(R, r) * 0.9;
  vec2 pc = vec2(0.15, -0.02); float a = atan(p.y - pc.y + 0.12, p.x - pc.x) ; float rr = length((p - pc) * vec2(1., 1.25));
  float loop = exp(-pow((rr - 0.22) / (0.025 + 0.02 * fbm(vec2(a * 4., ph * 0.0 + 1.))), 2.)) * step(-0.08, p.y - pc.y) ;
  col += vec3(1.0, 0.4, 0.12) * loop * (0.7 + 0.5 * fbm(vec2(a * 9. + 0.3 * sin(ph), rr * 20.))) * 1.3;
  return col;
}
vec3 warp(vec2 p, float ph){
  float a = atan(p.y, p.x), r = length(p); vec3 col = vec3(0.005, 0.008, 0.02);
  for (int i = 0; i < 3; i++) { float fi = float(i); float n = 90. + 60. * fi; float ai = floor((a / TAU + 0.5) * n);
    float s = h21(vec2(ai, fi)); float z = fract(s * 7.3 - uK / 16. * (1. + fi));
    float rr = 0.05 + pow(z, 2.2) * 1.3; float len = 0.02 + 0.3 * pow(z, 2.);
    float da = abs(fract((a / TAU + 0.5) * n) - 0.5) / n * TAU * r;
    col += mix(vec3(0.5, 0.7, 1.0), vec3(1.0), s) * smoothstep(0.004 + 0.003 * z, 0.0, da) * smoothstep(rr - len, rr, r) * step(r, rr) * (0.6 + 1.5 * z); }
  return col + vec3(0.6, 0.75, 1.0) * exp(-r * 6.) * 0.6;
}
vec3 forest(vec2 p, vec2 uv, float ph){
  vec3 col = mix(vec3(0.65, 0.72, 0.5), vec3(0.95, 0.85, 0.55), uv.y);
  vec2 L = vec2(-0.6, 0.55); vec2 d = normalize(p - L);
  float ray = pow(fbm(vec2(atan(d.y, d.x) * 14., 1.)), 2.) * smoothstep(1.6, 0.2, length(p - L));
  for (int i = 0; i < 4; i++) { float fi = float(i); float depth = 1. - fi / 4.;
    float x = uv.x * (5. + fi * 3.) + fi * 13.1; float id = floor(x); float fx = fract(x) - 0.5;
    float w = 0.06 + 0.08 * h21(vec2(id, fi)) + 0.05 * depth; float trunk = smoothstep(w, w - 0.02, abs(fx + 0.15 * (h21(vec2(id, fi + 3.)) - 0.5)));
    col = mix(col, mix(vec3(0.05, 0.08, 0.05), vec3(0.45, 0.5, 0.35), fi / 4.), trunk * (0.6 + 0.4 * depth)); }
  col += vec3(1.0, 0.92, 0.65) * ray * 0.55;
  for (int i = 0; i < 18; i++) { float fi = float(i); vec2 m = vec2(h21(vec2(fi, 1.)) * 2. - 1., h21(vec2(fi, 2.)) - 0.5) + 0.02 * vec2(sin(ph + fi), cos(ph + fi * 1.4));
    col += vec3(1.0, 0.95, 0.75) * smoothstep(0.006, 0.0, length(p - m)) * 0.8; }
  return col;
}
vec3 chrome(vec2 p, float ph){
  vec2 q = p * 1.8; vec3 o = vec3(0.35 * cos(ph), 0.35 * sin(ph), 0.);
  float h0 = fbm3(vec3(q, 0.) + o + fbm3(vec3(q * 1.5, 3.) - o) * 1.2);
  vec2 e = vec2(0.01, 0.);
  float hx = fbm3(vec3(q + e.xy, 0.) + o + fbm3(vec3((q + e.xy) * 1.5, 3.) - o) * 1.2);
  float hy = fbm3(vec3(q + e.yx, 0.) + o + fbm3(vec3((q + e.yx) * 1.5, 3.) - o) * 1.2);
  vec3 n = normalize(vec3(h0 - hx, h0 - hy, 0.015));
  vec3 r = reflect(vec3(0., 0., -1.), n);
  vec3 env = mix(vec3(0.06, 0.07, 0.09), vec3(0.75, 0.82, 0.95), smoothstep(-0.2, 0.6, r.y)) + vec3(1.0, 0.6, 0.3) * smoothstep(0.7, 0.95, r.x) * 1.2;
  return env * (0.5 + 0.7 * h0) + pow(max(r.y, 0.), 30.) * 1.5;
}
vec3 bloomf(vec2 p, float ph){
  vec3 col = mix(vec3(0.98, 0.86, 0.84), vec3(0.95, 0.75, 0.7), length(p));
  p *= rot(0.12 * sin(ph)); float a = atan(p.y, p.x), r = length(p);
  for (int i = 0; i < 3; i++) { float fi = float(i); float k = 5. + fi * 3.; float open = 0.92 + 0.08 * sin(ph);
    float pr = (0.42 - fi * 0.11) * open * (0.55 + 0.45 * pow(abs(cos(k * 0.5 * a + fi)) + 1e-4, 0.7));
    float inside = smoothstep(pr, pr - 0.01, r);
    vec3 pc = mix(vec3(0.95, 0.42, 0.5), vec3(1.0, 0.8, 0.7), fi / 2.) * (0.6 + 0.4 * r / pr);
    col = mix(col, pc, inside); }
  col = mix(col, vec3(1.0, 0.85, 0.35), smoothstep(0.06, 0.03, r));
  return col;
}
vec3 underwater(vec2 p, vec2 uv, float ph){
  vec3 col = mix(vec3(0.0, 0.05, 0.12), vec3(0.05, 0.4, 0.6), pow(uv.y, 1.4));
  vec2 q = p * 6.; float c = 0.;
  for (int i = 0; i < 3; i++) { float fi = float(i); c += abs(sin(q.x * (1. + fi * 0.4) + sin(q.y * 1.3 + ph + fi) * 1.5 + ph)) ; }
  c = pow(1. - c / 3., 6.) * smoothstep(0.2, 1.0, uv.y);
  col += vec3(0.6, 0.95, 1.0) * c * 1.2;
  float ray = pow(fbm(vec2(p.x * 6. - p.y * 1.5, 0.5 * sin(ph))), 3.) * smoothstep(0.0, 1.0, uv.y);
  col += vec3(0.5, 0.85, 1.0) * ray * 0.8;
  for (int i = 0; i < 14; i++) { float fi = float(i); float y = fract(h21(vec2(fi, 3.)) + uK / 16.); vec2 b = vec2(h21(vec2(fi, 4.)) * 1.6 - 0.8 + 0.02 * sin(y * 20.), y * 1.0 - 0.5);
    float d = length(p - b); col += vec3(0.8, 0.95, 1.0) * smoothstep(0.012, 0.009, d) * smoothstep(0.004, 0.009, d) * 1.2; }
  return col;
}
vec3 lake(vec2 uv, float ph){
  float hz = 0.4; vec2 q = uv; bool refl = q.y < hz; if (refl) q.y = 2. * hz - q.y + 0.003 * sin(uv.x * 120. + ph * 2.) * (hz - uv.y) * 6.;
  vec3 col = mix(vec3(1.0, 0.62, 0.45), vec3(0.35, 0.45, 0.75), pow((q.y - hz) / (1. - hz), 0.7));
  for (int i = 0; i < 4; i++) { float fi = float(i); float ridge = hz + 0.06 + 0.22 * (1. - fi / 4.) * (0.4 + 0.6 * abs(fbm(vec2(q.x * (2. + fi), fi * 3.)) * 1.6 - 0.6));
    vec3 mc = mix(vec3(0.16, 0.12, 0.22), vec3(0.85, 0.55, 0.55), fi / 4.); if (q.y < ridge) col = mix(mc, col, 0.15 * fi); }
  if (refl) col = col * vec3(0.7, 0.75, 0.85) + 0.03;
  col += vec3(1., 0.85, 0.75) * exp(-abs(uv.y - hz) * 60.) * 0.25;
  return col;
}
vec3 jelly(vec2 p, float ph){
  vec3 col = mix(vec3(0.0, 0.01, 0.04), vec3(0.0, 0.04, 0.1), p.y + 0.5);
  vec2 c = vec2(0.0, 0.12 + 0.03 * sin(ph)); vec2 q = p - c; float pulse = 1. + 0.08 * sin(ph);
  float bell = length(q * vec2(1. / pulse, 1.5)) ; float top = step(-0.02, q.y);
  float b = smoothstep(0.3, 0.28, bell) * top; float rim = exp(-pow((bell - 0.29) / 0.02, 2.)) * top;
  col += vec3(0.95, 0.4, 0.75) * b * 0.35 + vec3(1.0, 0.7, 0.9) * rim * 1.4;
  for (int i = 0; i < 9; i++) { float fi = float(i); float x0 = (fi / 8. - 0.5) * 0.48 * pulse;
    float x = x0 + 0.04 * sin(q.y * 14. - ph * 1. + fi) * (-q.y); float tent = smoothstep(0.006, 0.0, abs(q.x - x)) * step(q.y, 0.0) * step(-0.55 + 0.1 * h21(vec2(fi, 1.)), q.y);
    col += vec3(0.6, 0.8, 1.0) * tent * (0.6 + 0.6 * q.y + 0.3); }
  return col + stars(p, 35., ph, 9.) * 0.3 * vec3(0.4, 0.8, 1.0);
}
vec3 storm(vec2 p, vec2 uv, float ph){
  float k = uK; float fl = (k == 3. || k == 4. ? 1. : 0.) * (k == 4. ? 0.45 : 1.) + (k == 11. ? 0.7 : 0.);
  float cl = fbm(p * 2.5 + vec2(0.1 * cos(ph), 0.1 * sin(ph)));
  vec3 col = mix(vec3(0.03, 0.03, 0.06), vec3(0.18, 0.18, 0.28), cl) * (1. + fl * 2.5 * cl);
  float x = 0.1 + 0.05 * sin(uv.y * 30.) + 0.03 * sin(uv.y * 71. + 1.) + 0.02 * (vn(vec2(uv.y * 40., 0.)) - 0.5) * 4.;
  float bolt = smoothstep(0.006, 0.0, abs(uv.x - 0.5 - x)) * step(0.15, uv.y) * step(uv.y, 0.85) * step(0.5, fl);
  col += vec3(0.85, 0.85, 1.0) * bolt * 3.0 + vec3(0.5, 0.5, 0.9) * fl * exp(-abs(uv.x - 0.5 - x) * 12.) * 0.6;
  return col * mix(1., 0.5, smoothstep(0.2, 0.0, uv.y));
}
vec3 snow(vec2 p, vec2 uv, float ph){
  vec3 col = mix(vec3(0.42, 0.5, 0.75), vec3(0.08, 0.1, 0.22), uv.y);
  for (int i = 0; i < 3; i++) { float fi = float(i); float x = uv.x * (4. + fi * 4.) + fi * 7.; float id = floor(x), fx = fract(x) - 0.5;
    float h = 0.2 + 0.2 * h21(vec2(id, fi)) - fi * 0.06; float y = uv.y - (0.05 + 0.08 * fi * 0.0);
    float tree = step(y, h) * step(abs(fx), (h - y) * 0.45 * (0.8 + 0.4 * fract((h - y) * 12.)));
    col = mix(col, mix(vec3(0.02, 0.03, 0.06), vec3(0.2, 0.24, 0.38), fi / 3.), tree); }
  col = mix(col, vec3(0.75, 0.8, 0.95), step(uv.y, 0.06));
  col += vec3(1.0, 0.7, 0.3) * smoothstep(0.012, 0.0, max(abs(p.x - 0.35), abs(p.y + 0.36))) * 1.5;
  for (int i = 0; i < 40; i++) { float fi = float(i); float y = fract(h21(vec2(fi, 1.)) - uK / 16.); vec2 s = vec2(h21(vec2(fi, 2.)) * 1.9 - 0.95 + 0.02 * sin(ph + fi), y - 0.5);
    col += vec3(1.) * smoothstep(0.006, 0.0, length(p - s)) * 0.9; }
  return col;
}
vec3 trails(vec2 p, vec2 uv, float ph){
  vec3 col = vec3(0.01, 0.012, 0.025) + vec3(0.25, 0.12, 0.05) * smoothstep(0.6, 1.0, uv.y);
  for (int i = 0; i < 8; i++) { float fi = float(i); float lane = (fi - 3.5) * 0.04;
    float y = 0.3 + lane + 0.25 * sin(p.x * 1.6 + 0.6) * 0.5 + 0.12 * p.x;
    float d = abs(uv.y - y); vec3 c = fi < 4. ? vec3(1.0, 0.18, 0.1) : vec3(1.0, 0.9, 0.75);
    float dash = 0.75 + 0.25 * sin(p.x * 40. + (fi < 4. ? 1. : -1.) * ph * 3.);
    col += c * smoothstep(0.004, 0.0, d) * dash * 1.4 + c * exp(-d * 120.) * 0.15; }
  for (int i = 0; i < 40; i++) { float fi = float(i); vec2 w = vec2(h21(vec2(fi, 1.)) * 2. - 1., 0.12 + 0.35 * h21(vec2(fi, 2.)));
    col += vec3(1.0, 0.8, 0.5) * smoothstep(0.006, 0.0, length(p - w)) * (0.4 + 0.6 * h21(vec2(fi, 3.))); }
  return col;
}
vec3 mesh(vec2 p, float ph){
  vec3 col = vec3(0.98, 0.95, 0.92); float ws = 0.;
  vec3 cs[4]; cs[0] = vec3(1.0, 0.45, 0.2); cs[1] = vec3(0.95, 0.3, 0.55); cs[2] = vec3(0.25, 0.45, 1.0); cs[3] = vec3(1.0, 0.8, 0.3);
  vec3 acc = vec3(0.);
  for (int i = 0; i < 4; i++) { float fi = float(i); vec2 c = vec2(cos(ph + fi * 1.6) * 0.45, sin(ph * 1. + fi * 2.2) * 0.25);
    float w = exp(-dot(p - c, p - c) * 4.); acc += cs[i] * w; ws += w; }
  col = mix(col, acc / max(ws, 1e-3), clamp(ws, 0., 1.));
  return col * (0.95 + 0.05 * h21(floor(p * 400.)));
}
vec3 rain(vec2 p, vec2 uv, float ph){
  vec3 bg = bokeh(p * 0.9, ph) * 1.2 + vec3(0.05, 0.04, 0.06);
  vec2 g = p * vec2(9., 6.); vec2 i = floor(g), f = fract(g) - 0.5; vec2 o = (h22(i) - 0.5) * 0.6;
  float r = 0.12 + 0.18 * h21(i + 3.); float d = length((f - o) * vec2(1., 0.8));
  float drop = smoothstep(r, r - 0.04, d);
  vec3 refr = bokeh((p - (f - o) * 0.25) * 2.5, ph) * 1.5 + 0.06;
  vec3 col = mix(bg * 0.45, refr, drop) + vec3(1.) * smoothstep(0.05, 0.0, length(f - o + vec2(0.04, -0.05))) * drop * 0.8;
  float st = smoothstep(0.03, 0.0, abs(f.x - o.x)) * step(f.y, o.y) * smoothstep(-0.5, o.y, f.y) * step(0.7, h21(i + 9.));
  return col + vec3(0.6) * st * 0.4;
}
vec3 twinsuns(vec2 uv, float ph){
  vec3 col = mix(vec3(1.0, 0.55, 0.35), vec3(0.35, 0.25, 0.45), pow(uv.y, 0.8));
  vec2 s1 = vec2(0.36, 0.55), s2 = vec2(0.47, 0.62);
  col += vec3(1.0, 0.85, 0.6) * (smoothstep(0.05, 0.045, length((uv - s1) * vec2(1.78, 1.))) * 2.0 + exp(-length((uv - s1) * vec2(1.78, 1.)) * 6.) * 0.5);
  col += vec3(1.0, 0.7, 0.5) * (smoothstep(0.03, 0.026, length((uv - s2) * vec2(1.78, 1.))) * 2.0 + exp(-length((uv - s2) * vec2(1.78, 1.)) * 8.) * 0.4);
  float ground = 0.3 + 0.03 * fbm(vec2(uv.x * 6., 1.));
  float arch = 0.;
  { vec2 q = (uv - vec2(0.72, 0.3)) * vec2(1.78, 1.); float r = length(q); arch = step(0., q.y) * smoothstep(0.24, 0.23, r) * smoothstep(0.15, 0.16, r + 0.02 * fbm(q * 9.)); }
  float mesa = step(uv.y, 0.3 + 0.2 * step(abs(uv.x - 0.12), 0.08) * (1. - smoothstep(0.08, 0.1, abs(uv.x - 0.12))) + 0.0);
  if (uv.y < ground || arch > 0.5 || mesa > 0.5) col = mix(vec3(0.22, 0.1, 0.08), vec3(0.45, 0.2, 0.12), uv.y * 2.) * (0.8 + 0.2 * fbm(uv * 30.));
  return col + vec3(1.0, 0.7, 0.45) * 0.08 * fbm(uv * vec2(3., 10.) + vec2(0.05 * sin(ph), 0.));
}
vec3 earth(vec2 p, vec2 uv, float ph){
  vec3 col = vec3(0.0, 0.0, 0.01) + stars(p, 70., ph, 11.) * 0.7;
  vec2 c = vec2(0.0, -2.05); float R = 1.85; vec2 d = (p - c) / R; float rr = dot(d, d);
  vec3 L = normalize(vec3(0.85, 0.28, 0.45));
  if (rr < 1.) {
    vec3 n = vec3(d, sqrt(1. - rr));
    float a = 0.035 * sin(ph); vec3 m = vec3(n.x * cos(a) - n.z * sin(a), n.y, n.x * sin(a) + n.z * cos(a));   // a slow periodic turn
    vec3 q = m * 2.4 + vec3(3.1, 1.7, 0.0);
    float cont = fbm3(q + 0.5 * fbm3(q * 1.7));
    float land = smoothstep(0.50, 0.53, cont);
    float desert = smoothstep(0.45, 0.65, fbm3(q * 2.3 + 7.0)) * land;
    float cl = fbm3(m * 5.0 + vec3(0.2 * cos(ph), 0.0, 0.2 * sin(ph)) + fbm3(m * 9.0) * 0.6);
    float clouds = smoothstep(0.50, 0.78, cl);
    float dif = max(dot(n, L), 0.);
    vec3 ocean = mix(vec3(0.004, 0.02, 0.07), vec3(0.01, 0.07, 0.16), smoothstep(0.35, 0.5, cont));
    vec3 ground = mix(vec3(0.06, 0.12, 0.04), vec3(0.42, 0.33, 0.2), desert);
    vec3 surf = mix(ocean, ground, land);
    vec3 V = vec3(0., 0., 1.); vec3 H = normalize(L + V);
    float glint = pow(max(dot(n, H), 0.), 80.) * (1. - land) * (1. - clouds);
    col = surf * (0.04 + 1.25 * dif) + vec3(1.0, 0.9, 0.75) * glint * 1.6;
    col = mix(col, vec3(0.95, 0.97, 1.0) * (0.06 + 1.15 * dif), clouds * 0.9);
    col *= 1.0 - 0.35 * clouds * smoothstep(0.5, 0.7, fbm3(m * 5.0 + vec3(0.03, -0.02, 0.0)));    // cloud shadows
    float night = smoothstep(0.12, -0.08, dot(n, L));
    float cities = land * (1. - desert * 0.7) * step(0.72, h31(floor(m * 140.))) * smoothstep(0.4, 0.7, fbm3(q * 6.));
    col += vec3(1.0, 0.68, 0.32) * cities * night * 1.4;
    col += vec3(0.25, 0.5, 1.0) * pow(1. - n.z, 3.) * (0.25 + 0.9 * dif) * 0.9;                       // atmosphere toward the limb
  }
  float rl = sqrt(rr);
  float rim = exp(-pow((rl - 1.0) / 0.01, 2.)) + exp(-max(rl - 1.0, 0.) * 35.) * 0.55 * step(1.0, rl);
  col += vec3(0.3, 0.58, 1.0) * rim * 0.85 * smoothstep(-0.9, 0.6, d.x);
  col += vec3(1.0, 0.9, 0.75) * exp(-length(p - vec2(0.62, -0.2)) * 9.) * 1.5;
  return col;
}

void main(){
  vec2 uv = vUv; vec2 p = (uv - 0.5) * vec2(16. / 9., 1.);
  float ph = TAU * uK / 16.; vec2 c = vec2(cos(ph), sin(ph));
  int f = int(uFilm + 0.5); vec3 col;
  if (f == 0) col = nebula(p, c, ph);
  else if (f == 1) col = galaxy(p, ph);
  else if (f == 2) col = blackhole(p, ph);
  else if (f == 3) col = planet(p, ph);
  else if (f == 4) col = glass(p, ph);
  else if (f == 5) col = prism(p, ph);
  else if (f == 6) col = aurora(p, uv, ph);
  else if (f == 7) col = ocean(p, uv, ph);
  else if (f == 8) col = dunes(uv, ph);
  else if (f == 9) col = bokeh(p, ph);
  else if (f == 10) col = fire(p, uv, ph);
  else if (f == 11) col = ink(p, ph);
  else if (f == 12) col = geode(p, ph);
  else if (f == 13) col = sun(p, ph);
  else if (f == 14) col = warp(p, ph);
  else if (f == 15) col = forest(p, uv, ph);
  else if (f == 16) col = chrome(p, ph);
  else if (f == 17) col = bloomf(p, ph);
  else if (f == 18) col = underwater(p, uv, ph);
  else if (f == 19) col = lake(uv, ph);
  else if (f == 20) col = jelly(p, ph);
  else if (f == 21) col = storm(p, uv, ph);
  else if (f == 22) col = snow(p, uv, ph);
  else if (f == 23) col = trails(p, uv, ph);
  else if (f == 24) col = mesh(p, ph);
  else if (f == 25) col = rain(p, uv, ph);
  else if (f == 26) col = twinsuns(uv, ph);
  else col = earth(p, uv, ph);
  col = col / (1. + col * 0.35);                          // soft shoulder: films are screens, not light sources
  gl_FragColor = vec4(pow(clamp(col, 0., 1.), vec3(1. / 2.2)), 1.);   // stored as sRGB, like the jpg atlas
}`;

// one film at any size (look-hero/ exports the opening film at 1024x576 with it)
export function filmMaterial() {
  return new THREE.ShaderMaterial({ uniforms: { uFilm: { value: 0 }, uK: { value: 0 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }", fragmentShader: FRAG, depthTest: false, depthWrite: false });
}

// renders the procedural atlas once; returns a texture of NF x PROC.length tiles
export function renderProcAtlas(renderer) {
  const W = TW * NF, H = TH * PROC.length;
  const rt = new THREE.WebGLRenderTarget(W, H, { depthBuffer: false, generateMipmaps: true, minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter });
  // stored gamma-encoded in 8 bits with no colour-space tag; cards.js decodes it (pow 2.2), the jpg is decoded by the GPU
  const mat = new THREE.ShaderMaterial({ uniforms: { uFilm: { value: 0 }, uK: { value: 0 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }", fragmentShader: FRAG, depthTest: false, depthWrite: false });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat), scene = new THREE.Scene(); scene.add(quad);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const prevRT = renderer.getRenderTarget(), prevAuto = renderer.autoClear, vp = new THREE.Vector4();
  renderer.setRenderTarget(rt); renderer.autoClear = false; renderer.clear();
  for (let f = 0; f < PROC.length; f++) for (let k = 0; k < NF; k++) {
    mat.uniforms.uFilm.value = f; mat.uniforms.uK.value = k;
    // atlas row f from the top (v = 1 - (f+1)/rows), like the jpg atlas
    rt.viewport.set(k * TW, H - (f + 1) * TH, TW, TH); renderer.setRenderTarget(rt);
    renderer.render(scene, cam);
  }
  renderer.setRenderTarget(prevRT); renderer.autoClear = prevAuto;
  rt.viewport.set(0, 0, W, H);
  mat.dispose(); quad.geometry.dispose();
  return { tex: rt.texture, rt, rows: PROC.length };
}

export async function loadRealAtlas() {
  const meta = await (await fetch("assets/films.json")).json();
  const tex = await new THREE.TextureLoader().loadAsync("assets/films.jpg");
  tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8; tex.generateMipmaps = true; tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.flipY = true;
  return { tex, rows: meta.films.length, names: meta.films };
}
