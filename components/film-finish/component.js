// film-finish — the last pass over a picture drawn by code. A render comes out too clean: no grain, light that stops at
// its edge, corners as bright as the centre, colours that meet exactly, far things as crisp as near ones. A compositor
// finishing a CG shot adds those back, in a fixed order and in small amounts; this pass does the same, in the order light
// travels from the scene to the film:
//   1. air      far things toward a haze colour and greyer (needs a depth picture: white = far)
//   2. lens     red and blue a little apart toward the corners (radial chromatic aberration); the corners darker
//   3. light    what is still brighter than a threshold after 1 and 2 spills: a neutral bloom and a red-orange halation
//   4. medium   grain, new every frame by default, strongest in the mid-tones
// The idea and the order follow a compositor's habit (light first, defects last, each kept small); the code is this
// repository's own. state(params, t) is uniforms only (the grain's seed from the frame: hard rule 1). canvas() runs five
// WebGL2 passes (components/lib/gl.js): air and lens at full size; then, at a quarter, every pixel's light above the
// threshold gathered (each source pixel read once, so a light one pixel wide is never missed) and blurred by a separable
// Gaussian; then the spill and the grain at full size. playbook/08 成片的收尾.
import { FRAME, frame, clamp, hash32, rgb } from "../lib/core.js";
import { shader } from "../lib/gl.js";

export const defaults = {
  amount: 1,            // the whole pass: 0 = off, 1 = as set, up to 2 for a look-dev "harder" preset
  haze: 0,              // air: how far the farthest things go toward hazeColor (0 = off; needs a depth picture)
  hazeColor: "#9aa7b4", // air: the colour of the air (the sky's, at the horizon)
  hazeDesat: 0.5,       // air: how much colour the farthest things lose
  aberration: 0.0012,   // lens: red and blue apart at the corners, a fraction of the frame's width
  vignette: 0.16,       // lens: how much the corners darken
  bloom: 0.10,          // light: neutral glow round what passes the threshold
  halation: 0.08,       // light: red-orange halo round it (film's)
  threshold: 0.8,       // light: the luma above which light spills (keep text that must be read under it)
  radius: 0.012,        // light: how far it spills, a fraction of the frame's width (up to 0.05)
  grain: 0.02,          // medium: the grain's standard deviation in the mid-tones (0..1 of full scale; 0.02 ≈ 5 levels)
  grainSize: 1.3,       // medium: a grain's size in CSS px
  grainFps: 0,          // medium: new grain this many times a second; 0 = every frame (see slots.json on 24)
  seed: 11,             // medium: a new seed, a new grain pattern
};
const opts = (p) => ({ ...defaults, ...p });

/** The pass at t: its uniforms. Pure: the grain's seed comes from the frame, or from the grain step when grainFps is set. */
export function state(params, t) {
  const p = opts(params), k = clamp(p.amount, 0, 2);
  const step = p.grainFps > 0 ? Math.floor(frame(t) * p.grainFps / FRAME.fps + 1e-9) : frame(t);
  return {
    amount: clamp(k, 0, 1),
    haze: clamp(p.haze * k), hazeColor: rgb(p.hazeColor).map((v) => v / 255), hazeDesat: clamp(p.hazeDesat),
    aberration: Math.max(0, p.aberration * k), vignette: clamp(p.vignette * k),
    bloom: Math.max(0, p.bloom * k), halation: Math.max(0, p.halation * k), threshold: clamp(p.threshold, 0, 0.99),
    radius: clamp(p.radius, 0, 0.05),
    grain: Math.max(0, p.grain * k), grainSize: Math.max(0.5, p.grainSize), step,
    grainSeed: hash32(p.seed, step) & 0xffffff,   // < 2^24: exact as a float uniform
  };
}

const LUMA = `float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }\n`;

// pass 1, full size: air, then the lens (aberration and vignette)
const LENS = LUMA + `
uniform float u_haze, u_hazeDesat, u_hasDepth, u_ab, u_vig, u_aspect;
uniform vec3 u_hazeColor;
uniform sampler2D u_depth;
vec3 scene(vec2 uv) {
  vec3 c = texture(u_tex0, uv).rgb;
  if (u_hasDepth > 0.5 && u_haze > 0.0) {
    float f = u_haze * texture(u_depth, uv).r;
    c = mix(c, vec3(luma(c)), f * u_hazeDesat);
    c = mix(c, u_hazeColor, f);
  }
  return c;
}
void main() {
  vec2 d = v_uv - 0.5;
  float r2 = dot(d * vec2(u_aspect, 1.0), d * vec2(u_aspect, 1.0)) / (0.25 * u_aspect * u_aspect + 0.25);   // 0 centre, 1 corner
  vec2 shift = d * r2 * u_ab * 2.0 * vec2(1.0, u_aspect);
  vec3 c = vec3(scene(v_uv + shift).r, scene(v_uv).g, scene(v_uv - shift).b);
  c *= 1.0 - u_vig * smoothstep(0.15, 1.0, r2);
  outColor = vec4(c, 1.0);
}`;

// pass 2, quarter size: each output pixel is the mean of its block of source pixels, each thresholded first (soft knee)
const GATHER = LUMA + `
uniform float u_thr;
void main() {
  ivec2 full = textureSize(u_tex0, 0);
  vec2 scale = vec2(full) / u_res;
  ivec2 o = ivec2(floor(floor(gl_FragCoord.xy) * scale));
  ivec2 n = max(ivec2(1), ivec2(ceil(scale)));
  vec3 acc = vec3(0.0); float cnt = 0.0;
  for (int j = 0; j < 8; j++) { if (j >= n.y) break;
    for (int i = 0; i < 8; i++) { if (i >= n.x) break;
      vec3 c = texelFetch(u_tex0, clamp(o + ivec2(i, j), ivec2(0), full - 1), 0).rgb;
      float k = clamp((luma(c) - u_thr) / (1.0 - u_thr), 0.0, 1.0);
      acc += c * k * k; cnt += 1.0;
    } }
  outColor = vec4(acc / cnt, 1.0);
}`;

// passes 3 and 4, quarter size: a Gaussian along one axis (u_dir), every texel within 2.5 sigma read once
const BLUR = `
uniform vec2 u_dir; uniform float u_sigma;
void main() {
  vec2 px = u_dir / u_res;
  int n = int(ceil(2.5 * u_sigma));
  vec3 acc = vec3(0.0); float wsum = 0.0;
  for (int i = -64; i <= 64; i++) { if (i < -n || i > n) continue;
    float w = exp(-0.5 * float(i * i) / (u_sigma * u_sigma));
    acc += texture(u_tex0, v_uv + px * float(i)).rgb * w; wsum += w;
  }
  outColor = vec4(acc / wsum, 1.0);
}`;

// pass 5, full size: the spill over the lensed picture, then grain; mixed with the untouched picture by amount
const FINISH = LUMA + `
uniform float u_amount, u_bloom, u_hal, u_grain, u_grainSize, u_seed, u_dpr;
uniform sampler2D u_glow; uniform sampler2D u_raw;
uint pcg(uint v) { uint s = v * 747796405u + 2891336453u; uint w = ((s >> ((s >> 28u) + 4u)) ^ s) * 277803737u; return (w >> 22u) ^ w; }
float rnd(uvec3 p) { return float(pcg(p.x ^ pcg(p.y ^ pcg(p.z)))) * (1.0 / 4294967295.0); }
void main() {
  vec3 c = texture(u_tex0, v_uv).rgb;
  vec3 g = texture(u_glow, v_uv).rgb;
  vec3 add = g * u_bloom + g * vec3(1.0, 0.36, 0.14) * u_hal * 2.2;
  c = 1.0 - (1.0 - c) * (1.0 - clamp(add, 0.0, 1.0));   // screen: light adds without clipping
  uvec2 cell = uvec2(floor(gl_FragCoord.xy / (u_grainSize * u_dpr)));
  uint s = uint(u_seed);
  float n = (rnd(uvec3(cell, s)) + rnd(uvec3(cell, s ^ 0x9e3779b9u)) - 1.0) * 2.4494897;   // triangular, standard deviation 1
  float l = luma(c);
  c += n * u_grain * (0.3 + 2.8 * l * (1.0 - l));   // the weight is 1 at mid-grey: grain is the mid-tones' deviation
  outColor = vec4(mix(texture(u_raw, v_uv).rgb, clamp(c, 0.0, 1.0), u_amount), 1.0);
}`;

const _sh = new Map();
const sh = (key, src, w, h) => { const k = `${key}:${w}x${h}`; let s = _sh.get(k); if (!s) { s = shader(src, { width: w, height: h }); _sh.set(k, s); } return s; };

/**
 * Canvas painter: draws src (a full-frame canvas at any pixel ratio: a 2D canvas, or a Three.js renderer's canvas right
 * after its render) through the pass into ctx at the frame's CSS size. depth (optional): a full-frame canvas, white =
 * far, for the air. Draw the text that must be read after this, on top: the pass is for the picture.
 */
export function canvas(ctx, st, src, { depth } = {}) {
  const W = FRAME.w, H = FRAME.h;
  if (st.amount <= 0) { ctx.drawImage(src, 0, 0, W, H); return; }
  const pw = Math.round(W * FRAME.dpr), ph = Math.round(H * FRAME.dpr), aspect = W / H;
  const qw = Math.max(1, Math.round(pw / 4)), qh = Math.max(1, Math.round(ph / 4));
  const lensTex = { u_tex0: src };
  if (depth) lensTex.u_depth = depth;
  const lensed = sh("ff-lens", LENS, pw, ph).render(0, {
    u_haze: st.haze, u_hazeDesat: st.hazeDesat, u_hazeColor: st.hazeColor, u_hasDepth: depth ? 1 : 0,
    u_ab: st.aberration, u_vig: st.vignette, u_aspect: aspect,
  }, lensTex);
  let glow = null;
  if (st.bloom > 0 || st.halation > 0) {
    const sigma = Math.max(0.5, st.radius * qw / 2);   // the spill's reach (radius) is about two sigma
    const gathered = sh("ff-gather", GATHER, qw, qh).render(0, { u_thr: st.threshold }, { u_tex0: lensed });
    const across = sh("ff-blur-x", BLUR, qw, qh).render(0, { u_dir: [1, 0], u_sigma: sigma }, { u_tex0: gathered });
    glow = sh("ff-blur-y", BLUR, qw, qh).render(0, { u_dir: [0, 1], u_sigma: sigma }, { u_tex0: across });
  }
  const out = sh("ff-finish", FINISH, pw, ph).render(0, {
    u_amount: st.amount, u_bloom: glow ? st.bloom : 0, u_hal: glow ? st.halation : 0,
    u_grain: st.grain, u_grainSize: st.grainSize, u_seed: st.grainSeed, u_dpr: FRAME.dpr,
  }, { u_tex0: lensed, u_glow: glow || lensed, u_raw: src });
  ctx.drawImage(out, 0, 0, W, H);
}
