// product-keynote swatch — a macro product shot: one hero object, lit like a studio, the idea on its own screen.
// The device is ray-marched in a WebGL2 fragment shader (lib.shader): a rounded slab (SDF, rounded extrusion) with an
// anodized-aluminium body in the one accent colour and a glass front; lighting is an analytic studio environment
// (a large overhead softbox, two rim strips behind, an optional moving strip for the sweep), a soft contact shadow and
// a faint floor reflection on a warm-white seamless. 2×2 supersampling. Everything is a pure function of the uniforms.
//   0.0–0.8  from frame 0 the camera pulls out of a macro on the corner chamfer (softbox highlight, anodised grain) to
//            the full view by 0.85 s while the device turns 18° on a turntable (critically damped spring) and rests
//   0.8–2.6  0.3 s after it rests, the headline rises 16 px and fades in; the Chinese line 6 frames later
//   2.0–4.0  its screen wakes; outline → storyboard → draft (a giant "1.0") light up one after another; the storyboard
//            tile's orange outline pulses at 2.8, a render pass sweeps the draft at 3.2, a strip light glides across the
//            metal, and from 2.9 the camera pushes 4.5 % while the turntable turns another 12.6° (never crosses the type)
//   4.0–5.0  light-sweep transition to the dark stage, where the same device is carved out by rim light

const TEX_W = 1600, TEX_H = 1000;
let FX = null, SCREEN = null;
export const fonts = ["Avenir Next", "PingFang SC"];

const FRAG = `
uniform float u_yaw, u_dark, u_sweep, u_on, u_lift;
uniform vec3 u_ro, u_ta;
const float BX = 1.60, BY = 1.00, BZ = 0.16, RXY = 0.22, RE = 0.07, TILT = 0.13, FLOOR = -1.0;
const vec3 ACC = vec3(0.64, 0.092, 0.030);          // anodized accent (linear)

float sdRR(vec2 p, vec2 b, float r) { vec2 q = abs(p) - b + r; return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r; }
vec3 toLocal(vec3 p) {                                   // world → device space (origin = device centre)
  vec3 q = p - vec3(0.0, FLOOR, 0.0);
  float c = cos(-u_yaw), s = sin(-u_yaw); q = vec3(c * q.x + s * q.z, q.y, -s * q.x + c * q.z);
  float ct = cos(TILT), st = sin(TILT); q = vec3(q.x, ct * q.y - st * q.z, st * q.y + ct * q.z);
  return q - vec3(0.0, BY + 0.004, 0.0);
}
float sdDev(vec3 p) {
  vec3 q = toLocal(p);
  float d2 = sdRR(q.xy, vec2(BX, BY) - RE, RXY);
  vec2 w = vec2(d2, abs(q.z) - (BZ - RE));
  return min(max(w.x, w.y), 0.0) + length(max(w, 0.0)) - RE;
}
vec3 nrm(vec3 p) { vec2 e = vec2(0.0008, 0.0); return normalize(vec3(sdDev(p + e.xyy) - sdDev(p - e.xyy), sdDev(p + e.yxy) - sdDev(p - e.yxy), sdDev(p + e.yyx) - sdDev(p - e.yyx))); }
float march(vec3 ro, vec3 rd, float tmax) {
  // bounding sphere first
  vec3 oc = ro - vec3(0.0, 0.0, 0.0); float b = dot(oc, rd), c = dot(oc, oc) - 2.1 * 2.1, h = b * b - c;
  if (h < 0.0) return -1.0;
  float t = max(0.0, -b - sqrt(h)), t1 = min(tmax, -b + sqrt(h));
  for (int i = 0; i < 96; i++) { float d = sdDev(ro + rd * t); if (d < 0.0004) return t; t += d; if (t > t1) break; }
  return -1.0;
}
vec3 stageCol() { return mix(vec3(0.86, 0.86, 0.83) * u_lift, vec3(0.0055, 0.0055, 0.0065), u_dark); }
vec3 env(vec3 d) {
  float el = asin(clamp(d.y, -1.0, 1.0)), az = atan(d.x, d.z);
  vec3 c = stageCol() * (0.30 + 0.70 * smoothstep(-0.35, 0.55, d.y));
  float sb = smoothstep(0.26, 0.40, el) * (1.0 - smoothstep(1.20, 1.34, el)) * (1.0 - smoothstep(0.70, 0.95, abs(az)));
  c += vec3(1.0, 0.985, 0.96) * sb * mix(2.6 * u_lift, 0.9, u_dark);
  float rs = (1.0 - smoothstep(0.05, 0.13, abs(abs(az) - 2.25))) * smoothstep(-0.25, -0.05, el) * (1.0 - smoothstep(0.85, 1.0, el));
  c += vec3(1.0) * rs * mix(1.8, 6.0, u_dark);
  if (u_sweep > -9.0) {
    float sw = (1.0 - smoothstep(0.04, 0.16, abs(az - u_sweep))) * smoothstep(-0.3, -0.1, el) * (1.0 - smoothstep(1.0, 1.25, el));
    c += vec3(1.0, 0.97, 0.92) * sw * 1.5;
  }
  return c;
}
float fres(float c) { return 0.04 + 0.96 * pow(1.0 - clamp(c, 0.0, 1.0), 5.0); }
float hash2(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
// shade a device hit
vec3 shadeDev(vec3 p, vec3 rd, bool cheap) {
  vec3 n = nrm(p), q = toLocal(p), r = reflect(rd, n);
  float c = cos(-u_yaw), s = sin(-u_yaw); vec3 nl = vec3(c * n.x + s * n.z, n.y, -s * n.x + c * n.z);
  float ct = cos(TILT), st = sin(TILT); nl = vec3(nl.x, ct * nl.y - st * nl.z, st * nl.y + ct * nl.z);
  float F = fres(dot(-rd, n));
  if (nl.z > 0.93 && q.z > 0.0) {                         // the glass front
    vec3 col = vec3(0.004);
    vec2 sc = vec2(BX - 0.13, BY - 0.13);
    if (abs(q.x) < sc.x && abs(q.y) < sc.y) {
      vec2 uv = vec2(q.x / sc.x, q.y / sc.y) * 0.5 + 0.5;
      vec3 tx = cheap ? vec3(0.02) : pow(texture(u_tex0, uv).rgb, vec3(2.2));
      col += tx * u_on;
    }
    return col + env(r) * F * 0.85;
  }
  // anodized aluminium: coloured metal reflection + a thin clear-coat sheen + a little diffuse
  float grain = 0.985 + 0.03 * hash2(floor(q.xy * 900.0));
  vec3 spec = env(r) * mix(ACC, vec3(1.0), 0.10) * grain;
  vec3 diff = ACC * stageCol() * (0.18 + 0.30 * max(0.0, n.y));
  return diff + spec * 0.85 + env(r) * F * 0.25;
}
float softShadow(vec3 ro, vec3 rd) {
  float res = 1.0, t = 0.02;
  for (int i = 0; i < 40; i++) { float h = sdDev(ro + rd * t); res = min(res, 10.0 * h / t); t += clamp(h, 0.02, 0.25); if (res < 0.001 || t > 5.0) break; }
  return clamp(res, 0.0, 1.0);
}
vec3 render(vec2 frag) {
  vec3 ro = u_ro, ta = u_ta;
  vec3 cw = normalize(ta - ro), cu = normalize(cross(cw, vec3(0.0, 1.0, 0.0))), cv = cross(cu, cw);
  vec2 uv = (frag - 0.5 * u_res) / u_res.y;
  vec3 rd = normalize(uv.x * cu + uv.y * cv + 2.05 * cw);
  float tf = rd.y < 0.0 ? (FLOOR - ro.y) / rd.y : 1e9;
  float td = march(ro, rd, min(tf, 40.0));
  if (td > 0.0) return shadeDev(ro + rd * td, rd, false);
  vec3 bg = stageCol() * (1.0 + 0.10 * (1.0 - length(uv * vec2(0.8, 1.2))));
  if (tf < 1e8) {
    vec3 p = ro + rd * tf;
    float ao = clamp(sdDev(p) / 0.45, 0.0, 1.0);
    float sh = softShadow(p + vec3(0.0, 0.001, 0.0), normalize(vec3(-0.15, 1.0, 0.42)));
    vec3 fl = stageCol() * (0.62 + 0.38 * sh) * (1.0 - 0.55 * pow(1.0 - ao, 2.0));
    // faint floor reflection of the device
    vec3 rr = reflect(rd, vec3(0.0, 1.0, 0.0));
    float tr = march(p + rr * 0.002, rr, 3.0);
    if (tr > 0.0) fl = mix(fl, shadeDev(p + rr * tr, rr, true), 0.16 * (1.0 - tr / 3.0));
    float fog = smoothstep(9.0, 22.0, tf);                 // seamless: floor dissolves into the cyc
    return mix(fl, bg, fog);
  }
  return bg;
}
void main() {
  vec2 f = v_uv * u_res;
  vec3 c = vec3(0.0);
  c += render(f + vec2(-0.25, -0.25)); c += render(f + vec2(0.25, -0.25));
  c += render(f + vec2(-0.25, 0.25)); c += render(f + vec2(0.25, 0.25));
  c *= 0.25;
  c = c / (1.0 + 0.12 * c);                               // gentle shoulder, keeps the softbox from clipping hard
  outColor = vec4(pow(c, vec3(1.0 / 2.2)), 1.0);
}`;

export async function setup(ctx, tokens, lib) {
  FX = lib.shader(FRAG);
  SCREEN = document.createElement("canvas"); SCREEN.width = TEX_W; SCREEN.height = TEX_H;
}

// ───────── the device's screen (2D canvas → texture) ─────────
function drawScreen(t, tokens, lib, { endCard = false } = {}) {
  const x = SCREEN.getContext("2d"), C = (k) => lib.color(tokens, k), E = lib.easeOf(tokens.ease.enter);
  x.reset();
  const g = x.createRadialGradient(TEX_W / 2, TEX_H * 0.4, 0, TEX_W / 2, TEX_H * 0.4, TEX_W * 0.7);
  g.addColorStop(0, "#1b1c20"); g.addColorStop(1, "#0b0b0d");
  x.fillStyle = g; x.fillRect(0, 0, TEX_W, TEX_H);
  if (endCard) {                                         // the finished draft, full screen
    lib.setFont(x, tokens, "display", 420, { weight: 600 }); x.fillStyle = C("accent"); lib.drawText(x, "1.0", TEX_W / 2, 650, { align: "center", tracking: -420 * 0.03 });
    return;
  }
  const tiles = [80, 580, 1080], ty = 150, tw = 440, th = 430;
  tiles.forEach((tx, k) => {
    const a = E(lib.seg(t, 2.0 + k * 0.3, 2.0 + k * 0.3 + 0.5));
    if (a <= 0) return;
    x.save(); x.globalAlpha = a; x.translate(0, (1 - a) * 24);
    x.fillStyle = k === 2 ? "#26211f" : "#1f2024"; x.beginPath(); x.roundRect(tx, ty, tw, th, 34); x.fill();
    const pulse = k === 1 ? Math.exp(-Math.pow((t - 2.85) / 0.12, 2)) : 0;
    x.strokeStyle = k === 0 ? "rgba(255,255,255,0.18)" : C("accent"); x.lineWidth = k === 0 ? 3 : k === 1 ? 4 + 8 * pulse : 6; x.globalAlpha = a * (k === 1 ? 0.6 + 0.4 * pulse : 1); x.stroke(); x.globalAlpha = a;
    x.strokeStyle = "rgba(245,245,240,0.85)"; x.fillStyle = "rgba(245,245,240,0.85)"; x.lineWidth = 12; x.lineCap = "round";
    const cx = tx + tw / 2, cy = ty + th / 2;
    if (k === 0) [[1, 1], [1, 1], [0.6, 1]].forEach(([w], j) => { x.beginPath(); x.moveTo(cx - 130, cy - 80 + j * 80); x.lineTo(cx - 130 + 260 * w, cy - 80 + j * 80); x.stroke(); });
    else if (k === 1) for (let j = -1; j <= 1; j++) { x.lineWidth = 8; x.strokeRect(cx + j * 118 - 48, cy - 90, 96, 180); }
    else {                                              // draft: the one giant number of a keynote
      lib.setFont(x, tokens, "display", 230, { weight: 600 }); x.fillStyle = C("accent");
      lib.drawText(x, "1.0", cx, cy + 82, { align: "center", tracking: -230 * 0.03 });
      const rs = lib.seg(t, 3.15, 3.45);                  // 3.2 s: a render pass sweeps the tile
      if (rs > 0 && rs < 1) { const sx = tx + rs * tw, g = x.createLinearGradient(sx - 60, 0, sx + 60, 0); g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, "rgba(255,255,255,0.35)"); g.addColorStop(1, "rgba(255,255,255,0)"); x.save(); x.beginPath(); x.roundRect(tx, ty, tw, th, 34); x.clip(); x.fillStyle = g; x.fillRect(tx, ty, tw, th); x.restore(); }
    }
    lib.setFont(x, tokens, "display", 76, { weight: 600 }); x.fillStyle = k === 2 ? "#ffffff" : "rgba(245,245,240,0.94)";
    lib.drawText(x, lib.MOTIF[k].en, cx, ty + th + 104, { align: "center" });
    lib.setFont(x, tokens, "zh", 92, { weight: 500 }); x.fillStyle = "rgba(245,245,240,0.82)";
    lib.drawText(x, lib.MOTIF[k].zh, cx, ty + th + 216, { align: "center", tracking: 8 });
    x.restore();
    if (k < 2 && a >= 1) { x.fillStyle = "rgba(245,245,240,0.35)"; x.beginPath(); const ax = tx + tw + 30; x.moveTo(ax, ty + th / 2 - 16); x.lineTo(ax + 22, ty + th / 2); x.lineTo(ax, ty + th / 2 + 16); x.closePath(); x.fill(); }
  });
}

// ───────── frame ─────────
const YAW0 = -0.73, YAW1 = -0.415;                        // turns 18°: −41.8° → −23.8°
function yawAt(t, lib) { return YAW0 + (YAW1 - YAW0) * lib.spring(t - 0.12, { stiffness: 170, damping: 26 }) + 0.22 * lib.ease.inOutSine(lib.seg(t, 2.9, 4.0)); }
const RO = [0, 0.95, 7.3], TA = [0, 0.34, 0], TA0 = [1.05, 0.72, 0.25], RO0 = [1.6, 1.25, 2.3];   // wide rest / macro on the corner chamfer
function camAt(t, lib) {
  const u = lib.ease.inOutCubic(lib.seg(t, -0.12, 0.85)), push = 0.07 * lib.ease.inOutSine(lib.seg(t, 1.0, 4.0));
  const ta = TA.map((v, i) => lib.lerp(TA0[i], v, u)), ro0 = RO.map((v, i) => lib.lerp(RO0[i], v, u));
  return { ro: ro0.map((v, i) => ta[i] + (v - ta[i]) * (1 - push)), ta };
}

function lightStage(t, tokens, lib) {
  const sweep = t >= 2.75 && t < 3.9 ? lib.lerp(-1.4, 1.4, lib.ease.inOutSine(lib.seg(t, 2.75, 3.9))) : -10;
  drawScreen(t, tokens, lib);
  const on = lib.ease.outCubic(lib.seg(t, 1.75, 2.1));
  const lift = 0.62 + 0.38 * lib.ease.outCubic(lib.seg(t, 0.0, 0.7));                // the stage lights come up
  const cm = camAt(t, lib);
  return FX.render(t, { u_yaw: yawAt(t, lib), u_dark: 0, u_sweep: sweep, u_on: on, u_lift: lift, u_ro: cm.ro, u_ta: cm.ta }, { u_tex0: SCREEN });
}
function darkStage(t, tokens, lib) {
  drawScreen(t, tokens, lib, { endCard: true });
  return FX.render(t, { u_yaw: YAW1, u_dark: 1, u_sweep: -10, u_on: 1, u_lift: 1, u_ro: RO, u_ta: TA }, { u_tex0: SCREEN });
}
function type(ctx, t, tokens, lib, alpha = 1) {
  const C = (k) => lib.color(tokens, k), { W } = lib, E = lib.easeOf(tokens.ease.enter);
  const tu = lib.tween(t, 1.05, 1.65, E), zu = lib.tween(t, 1.25, 1.85, E);   // device rests ≈ 0.75 s → +0.3 s
  ctx.save(); ctx.fillStyle = C("fg");
  if (tu > 0) { ctx.globalAlpha = tu * alpha; lib.setFont(ctx, tokens, "display", 100, { weight: 600 }); lib.drawText(ctx, lib.TITLE_EN, W / 2, 170 + (1 - tu) * 16, { align: "center", tracking: -100 * 0.02 }); }
  if (zu > 0) { ctx.globalAlpha = zu * alpha; ctx.fillStyle = C("extra.0"); lib.setFont(ctx, tokens, "zh", 56, { weight: 500 }); lib.drawText(ctx, lib.TITLE_ZH, W / 2, 252 + (1 - zu) * 16, { align: "center", tracking: 56 * 0.05 }); }
  ctx.restore();
}
function endType(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W } = lib, a = lib.tween(t, 4.55, 4.95, lib.easeOf(tokens.ease.enter));
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = C("extra.4");
  lib.setFont(ctx, tokens, "display", 72, { weight: 600 }); lib.drawText(ctx, "Product Keynote", W / 2, 170 + (1 - a) * 16, { align: "center", tracking: -72 * 0.02 });
  ctx.fillStyle = C("extra.0"); lib.setFont(ctx, tokens, "zh", 50, { weight: 500 }); lib.drawText(ctx, "产品发布片", W / 2, 244 + (1 - a) * 16, { align: "center", tracking: 6 });
  ctx.restore();
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  if (t < 4.0) { ctx.drawImage(lightStage(t, tokens, lib), 0, 0); type(ctx, t, tokens, lib); return; }
  // light-sweep transition: a soft diagonal band of light; behind it, the dark stage
  const u = lib.ease.inOutQuart(lib.seg(t, 4.0, 4.6));
  if (u >= 1) { ctx.drawImage(darkStage(t, tokens, lib), 0, 0); endType(ctx, t, tokens, lib); return; }
  const a = lib.layer("pk_a"); a.drawImage(lightStage(3.99, tokens, lib), 0, 0); type(a, 3.99, tokens, lib, 1 - lib.seg(t, 4.0, 4.3));
  ctx.drawImage(a.canvas, 0, 0);
  const ang = 18 * Math.PI / 180, dx = Math.cos(ang), dy = Math.sin(ang), half = (Math.abs(dx) * W + Math.abs(dy) * H) / 2 + 260;
  const pos = lib.lerp(-half, half, u), fx = W / 2 + dx * pos, fy = H / 2 + dy * pos;
  const b = lib.layer("pk_b"); b.drawImage(darkStage(t, tokens, lib), 0, 0);
  b.globalCompositeOperation = "destination-in";
  const m = b.createLinearGradient(fx - dx * 120, fy - dy * 120, fx + dx * 120, fy + dy * 120);
  m.addColorStop(0, "rgba(0,0,0,1)"); m.addColorStop(1, "rgba(0,0,0,0)");
  b.fillStyle = m; b.fillRect(0, 0, W, H);
  ctx.drawImage(b.canvas, 0, 0);
  ctx.save(); ctx.globalCompositeOperation = "screen";
  const g = ctx.createLinearGradient(fx - dx * 240, fy - dy * 240, fx + dx * 240, fy + dy * 240);
  g.addColorStop(0, "rgba(255,255,255,0)"); g.addColorStop(0.5, "rgba(255,246,236,0.32)"); g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}

// foley (events.json is generated from this list; times are the same ones the scene uses)
export const FOLEY = [
  { t: 0.75, sfx: "pop", gain_db: -20, pan: 0 },                                                          // the device comes to rest
  ...[2.0, 2.3, 2.6].map((t, k) => ({ t, sfx: "tick", gain_db: -12, pan: [-0.3, 0, 0.3][k] })),          // tiles light
  { t: 2.85, sfx: "tick", gain_db: -14, pan: 0 },                                                         // storyboard outline pulse
  { t: 3.3, sfx: "whoosh", gain_db: -16, pan: 0.3 },                                                      // render pass / strip light
  { t: 4.3, sfx: "whoosh", gain_db: -8, pan: 0 },                                                         // the light sweep
  { t: 4.6, sfx: "ding", gain_db: -10, pan: 0 },                                                          // the one chime: the name
];
