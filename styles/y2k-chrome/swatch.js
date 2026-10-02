// y2k-chrome swatch · Y2K 铬面 (150 BPM, beat 0.4 s; bars of 2 + 3 + 3 + 2 + 3 beats start at 0 / 0.8 / 2.0 / 3.2 / 4.0)
// One character carries the film: a blob of liquid chrome. It lands, spits out the title, stays on as a small blob,
// hops onto the three level tiles on the beat, is swept up by a chrome tube and comes back as "Y2K".
// Chrome is a WebGL pass: chrome objects are painted into a field canvas (R = coverage, thresholded at 0.5 in the shader;
// G = dome height from a wide blur, or a painted sphere for droplets; B = bevel height from a narrow blur, also cut at
// 0.2 for an ink keyline). The blob and the tube get their height analytically in the shader instead (an 8-bit ramp
// across a 600 px dome draws contour rings). The shader turns height into a normal and reflects it into a procedural
// studio: deep-blue sky, silver near a hard (anti-aliased) horizon, a black line, a dark-purple ground with a thin
// hot-pink edge at the very bottom, two oval softboxes and a soft black flag. On the title rows the elevation is
// blended with a screen-space term, so the horizon runs straight through each line of letters (airbrushed chrome)
// instead of dripping along every stroke. From 2.0 s the studio swings ±0.15 rad on every beat, so the highlights slide.
// Everything else (gel tiles, stickers, the score pill, sparkles) is Canvas2D.
//   0.00       HOOK · the blob lands on acid yellow mid-squash: fall streaks, a white shock ring, an anvil hit
//   0.08–0.40  it hops down-screen and lands below the title area (squash); the score pill drops in
//   0.40–1.48  the landing splashes the first word's droplets high into the air; then it swells and spits the rest
//              letter by letter: droplets arc up and swell into chrome letters with an overshoot; the four words land
//              on the eighth notes 0.8 / 1.0 / 1.2 / 1.4; the blob is left small (r 56)
//   1.52–1.80  it hops to a resting spot at the left; 1.60 the Chinese line on a die-cut sticker slaps down
//   2.00–2.40  three level tiles pop out of the floor on the eighths: 1-1 大纲 cyan gel → 1-2 分镜 magenta gel →
//              1-3 初版 silver chrome with a little monitor (the more finished, the shinier); the blob bobs to each pop
//   2.80 / 3.20 / 3.60  the blob hops onto each tile and lands on the beat: tile and blob squash, sparkles, a CLEAR
//              sticker on the tile's corner, the score ticks by 1000
//   3.62–4.08  stage clear: a hop runs through the title letters, left to right
//   4.00–4.60  SIGNATURE TRANSITION: a tilted chrome tube sweeps in from the right like a squeegee (a softbox runs across
//              it, a glint rides its crest), pushes the blob and swallows it; behind the tube, on a clean acid frame,
//              the blob drops out at the centre, swells, and at 4.40 bursts into chrome "Y2K"; a CHROME sticker slaps
//              on at 4.60; a glint at 4.80

const BEAT = 0.4;
const T = {
  slam: 0.0, hop: 0.4, hud: 0.4, gather: [0.42, 0.58],
  words: [0.8, 1.0, 1.2, 1.4], slap: 1.6, rest: 1.8, tiles: [2.0, 2.2, 2.4],
  lands: [2.8, 3.2, 3.6], wave: 3.62, wipe: [4.0, 4.6], endPop: 4.4, endSticker: 4.6, glint: 4.8,
};
const LAST = T.words[3] + 0.08;            // the last droplet has left; the blob is down to its small size
const FLIGHT = 0.22;                       // a droplet's flight to its letter (s); the first word's leave on the hop landing
const HOP = 0.24;                          // the small blob's air time per hop
const FLOOR = 934;                         // the blob stands on this line (the tiles' bottom edge)
const TILE = { y: 840, w: 300, h: 188, r: 46, xs: [520, 960, 1400] };
const TOP = TILE.y - TILE.h / 2;           // 706: the tiles' top edge
const STK = { x: 1180, y: 566, rot: -0.05 };   // the die-cut sticker
const BLOB = { x: 960, y: 540, R: 330, Rlow: 195, Rsmall: 56, rest: [200, FLOOR - 56] };
const END = { x: 960, y: 560 };            // where the blob drops out of the tube and turns into "Y2K"
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 75) / 100;          // pan = (2x/W − 1) · 0.75

let L = null, FX = null;

// ───────────────────────── chrome shader ─────────────────────────
const vec3 = (hex) => { const n = parseInt(hex.slice(1), 16); return `vec3(${[(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => (v / 255).toFixed(4)).join(",")})`; };
const FRAG = (P, M) => `
uniform float u_rot, u_kG, u_kB, u_rim, u_key;               // u_key: keyline threshold on the bevel blur (0 = none)
uniform vec4 u_blob;                                         // analytic blob: centre (canvas px), radius, lobe phase
uniform vec2 u_blobS;                                        // its squash (sx, sy)
uniform vec4 u_tube;                                         // analytic tube: centre-line x at y = 540, normal, half-width
uniform vec4 u_rows;                                         // title rows: centre y of row 1 and 2, half height, weight
const vec3 SKY_TOP = ${vec3(P("skyTop"))}, SKY_MID = ${vec3(P("skyMid"))}, SKY_LOW = ${vec3(P("skyLow"))};
const vec3 SILVER = ${vec3(P("silver"))}, GROUND = ${vec3(P("ground"))}, PURPLE = ${vec3(M)}, PINK = ${vec3(P("accent"))};
const vec3 CYA = ${vec3(P("cyan"))};
vec2 cpx(vec2 uv){ return vec2(uv.x, 1.0 - uv.y) * u_res; }      // canvas pixels, y down
float ana(vec2 uv){                                          // analytic heights (px): float precision, no 8-bit steps
  vec2 p = cpx(uv); float h = 0.0;
  if (u_blob.z > 0.5) {
    vec2 q = (p - u_blob.xy) / (u_blob.z * u_blobS);
    float th = atan(q.y, q.x), rr = 1.0 + 0.05 * sin(3.0 * th + u_blob.w) + 0.035 * sin(5.0 * th - 1.7 * u_blob.w);
    float rho = length(q) / rr; h += 0.62 * u_blob.z * sqrt(max(0.0, 1.0 - rho * rho));
  }
  if (u_tube.w > 0.5) { float d = dot(p - vec2(u_tube.x, 540.0), u_tube.yz) / u_tube.w; h += 0.8 * u_tube.w * sqrt(max(0.0, 1.0 - d * d)); }
  return h;
}
float box(vec2 p, vec2 c, vec2 h, float s){ vec2 d = abs(p - c) - h; return 1.0 - smoothstep(0.0, s, max(d.x, d.y)); }
float h21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec3 env(vec3 r, float pk){
  float e = r.y;                                             // elevation: + up
  float a = atan(r.x, r.z) + u_rot;                          // azimuth: 0 = straight back at the camera
  a = mod(a + 3.14159265, 6.2831853) - 3.14159265;
  const float HZ = -0.12;
  float s = clamp((e - HZ) / (1.0 - HZ), 0.0, 1.0), g = clamp((HZ - e) / (1.0 + HZ), 0.0, 1.0);
  vec3 sky = mix(SILVER, SKY_LOW, smoothstep(0.06, 0.22, s));             // silver just above the horizon, then the sky
  sky = mix(sky, SKY_MID, smoothstep(0.22, 0.45, s));
  sky = mix(sky, SKY_TOP, smoothstep(0.45, 0.95, s));
  sky = mix(sky, vec3(1.0), 1.0 - smoothstep(0.0, 0.05, s));               // a white line right on the horizon
  vec3 gnd = mix(GROUND, PURPLE, smoothstep(0.05, 0.35, g));              // a black line, then dark purple
  gnd = mix(gnd, PINK, smoothstep(pk, pk + 0.12, g));                    // hot pink only on the lowest edge
  vec3 col = mix(gnd, sky, smoothstep(HZ - 0.012, HZ + 0.012, e));        // a hard horizon, but anti-aliased
  float flag = box(vec2(a, e), vec2(0.62, 0.05), vec2(0.13, 0.75), 0.12);  // a soft black flag: a dark edge beside the light
  col = mix(col, GROUND, flag * 0.55);
  float sb = 1.0 - smoothstep(0.72, 1.0, length((vec2(a, e) - vec2(-0.85, 0.42)) / vec2(0.20, 0.24)));   // two oval softboxes
  sb = max(sb, 1.0 - smoothstep(0.65, 1.0, length((vec2(a, e) - vec2(1.05, 0.22)) / vec2(0.12, 0.12))));
  return mix(col, vec3(1.0), sb);
}
void main(){
  vec2 uv = clamp(v_uv, 24.0 / u_res, 1.0 - 24.0 / u_res);   // full-bleed chrome: blurred masks fade out at the frame edge
  vec4 c = texture(u_tex0, uv);
  float aa = max(fwidth(c.r) * 0.7, 0.012);
  float cov = smoothstep(0.5 - aa, 0.5 + aa, c.r);
  float ka = max(fwidth(c.b) * 0.7, 0.01);
  float key = u_key > 0.0 ? smoothstep(u_key - ka, u_key + ka, c.b) : 0.0;   // the bevel blur, cut lower = a dilated outline
  if (max(cov, key) <= 0.0) { outColor = vec4(0.0); return; }
  vec2 px = 1.0 / u_res;
  // dome (G) and bevel (B) gradients, each averaged over two stencils: 8-bit steps become noise that averages out
  vec2 ax = vec2(px.x, 0.0), ay = vec2(0.0, px.y);
  float gx = u_kG * 0.5 * ((texture(u_tex0, uv + 5.0 * ax).g - texture(u_tex0, uv - 5.0 * ax).g) / 10.0
                          + (texture(u_tex0, uv + 8.0 * ax).g - texture(u_tex0, uv - 8.0 * ax).g) / 16.0)
           + u_kB * 0.5 * ((texture(u_tex0, uv + 2.0 * ax).b - texture(u_tex0, uv - 2.0 * ax).b) / 4.0
                          + (texture(u_tex0, uv + 3.5 * ax).b - texture(u_tex0, uv - 3.5 * ax).b) / 7.0)
           + (ana(v_uv + ax) - ana(v_uv - ax)) / 2.0;
  float gy = u_kG * 0.5 * ((texture(u_tex0, uv + 5.0 * ay).g - texture(u_tex0, uv - 5.0 * ay).g) / 10.0
                          + (texture(u_tex0, uv + 8.0 * ay).g - texture(u_tex0, uv - 8.0 * ay).g) / 16.0)
           + u_kB * 0.5 * ((texture(u_tex0, uv + 2.0 * ay).b - texture(u_tex0, uv - 2.0 * ay).b) / 4.0
                          + (texture(u_tex0, uv + 3.5 * ay).b - texture(u_tex0, uv - 3.5 * ay).b) / 7.0)
           + (ana(v_uv + ay) - ana(v_uv - ay)) / 2.0;
  vec3 n = normalize(vec3(-gx, -gy, 1.0));
  vec3 r = reflect(vec3(0.0, 0.0, -1.0), n);
  float onAna = step(0.5, ana(v_uv));
  if (u_rows.w > 0.0 && onAna < 0.5) {                   // on a title row: a straight horizon through the letters
    float py = cpx(v_uv).y, d1 = py - u_rows.x, d2 = py - u_rows.y, d = abs(d1) < abs(d2) ? d1 : d2;
    if (abs(d) < u_rows.z * 2.2) r.y = mix(r.y, clamp(0.1 - d / u_rows.z * 0.7, -1.0, 1.0), u_rows.w);   // horizon ~2/3 down
  }
  vec3 col = env(r, mix(0.52, 0.9, onAna));
  float fr = clamp(pow(1.0 - n.z, 2.0), 0.0, 1.0);
  vec3 tint = mix(PINK, CYA, 0.5 + 0.5 * sin(atan(n.y, n.x) + 0.6));               // a faint holographic rim
  col = mix(col, col * 0.6 + tint * 0.5, fr * 0.25);
  col *= mix(u_rim, 1.0, smoothstep(0.5, 0.74, c.r));                              // a thin dark contour
  col += (h21(gl_FragCoord.xy) - 0.5) / 255.0;
  outColor = vec4(clamp(mix(GROUND, col, cov), 0.0, 1.0), max(cov, key));
}`;

// ───────────────────────── setup ─────────────────────────
export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  FX = lib.shader(FRAG(P, lib.mixColor(P("endBg"), P("accent"), 0.32)));
  // title: two lines, inflated chrome
  const size = 180, lw = Math.round(size * 0.075);
  lib.setFont(ctx, tokens, "display", size);
  const lines = ["Every frame", "is code."], ys = [294, 480];
  const glyphs = [];
  let word = 0;
  lines.forEach((s, li) => {
    const lay = lib.layoutText(ctx, s, { x: 960, y: ys[li], align: "center", tracking: size * 0.02 });
    lay.glyphs.forEach((g) => { if (g.ch === " ") { word++; return; } glyphs.push({ ...g, line: li, word }); });
    word++;
  });
  const capH = size * 0.72;
  const byWord = {};                                           // within a word, letters land a little apart around its eighth
  glyphs.forEach((g) => (byWord[g.word] ||= []).push(g));
  Object.values(byWord).forEach((ws) => ws.forEach((g, j) => {
    g.land = T.words[g.word] + (j - (ws.length - 1) / 2) * 0.026;
    g.leave = g.word ? g.land - FLIGHT : T.hop + 0.015 * j;     // the hop landing at 0.4 splashes out the whole first word
  }));
  glyphs.forEach((g, i) => {                                  // each glyph pops from its own ink centre (a period from the baseline)
    const m = ctx.measureText(g.ch);
    g.k = i; g.cy = g.y - (m.actualBoundingBoxAscent - m.actualBoundingBoxDescent) / 2; g.sx0 = BLOB.x + (lib.hash(3, i) - 0.5) * 120;
  });
  const rows = [ys[0] - capH / 2, ys[1] - capH / 2, capH / 2 + lw / 2];
  lib.setFont(ctx, tokens, "zh", 70);
  const zh = lib.layoutText(ctx, lib.TITLE_ZH, { x: 0, y: 25, align: "center", tracking: 70 * 0.06 });
  const sparkles = [                                           // [x, y, r, t0]: twinkles that land on beats
    [250, 215, 44, 0.0], [1690, 640, 52, 0.0], [1700, 210, 40, 0.4], [300, 560, 34, 1.2], [1630, 455, 38, 2.0],
    [150, 700, 30, 2.4], [1760, 900, 34, 2.8], [330, 440, 40, 3.2], [1690, 270, 46, 3.6], [1560, 140, 30, 3.6],
  ];
  lib.setFont(ctx, tokens, "ui", 64);
  const chromeWord = lib.layoutText(ctx, "CHROME", { x: 0, y: 23, align: "center", tracking: 64 * 0.08 });
  L = { P, size, lw, glyphs, capH, rows, zh, chromeWord, sparkles };
}

// ───────────────────────── shapes ─────────────────────────
function star4(ctx, x, y, r, rot = 0, pinch = 0.16) {        // a four-point sparkle with concave sides
  ctx.save(); ctx.translate(x, y); ctx.rotate(rot); ctx.beginPath();
  for (let i = 0; i < 4; i++) {
    const a = (i * Math.PI) / 2, b = a + Math.PI / 4, c = a + Math.PI / 2;
    if (i === 0) ctx.moveTo(Math.cos(a) * r, Math.sin(a) * r);
    ctx.quadraticCurveTo(Math.cos(b) * r * pinch, Math.sin(b) * r * pinch, Math.cos(c) * r, Math.sin(c) * r);
  }
  ctx.closePath(); ctx.restore();
}
function blobPath(ctx, b) {                                    // a liquid blob: a circle with slow lobes (same formula as the shader)
  ctx.beginPath();
  for (let i = 0; i <= 72; i++) {
    const a = (i / 72) * Math.PI * 2, rr = b.R * (1 + 0.05 * Math.sin(3 * a + b.ph) + 0.035 * Math.sin(5 * a - 1.7 * b.ph));
    const px = b.x + Math.cos(a) * rr * b.sx, py = b.y + Math.sin(a) * rr * b.sy;
    i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
  }
  ctx.closePath();
}
const SPHERE = [[0, 1], [0.3, 0.954], [0.5, 0.866], [0.7, 0.714], [0.82, 0.572], [0.9, 0.436], [0.96, 0.28], [1, 0]];
function domeFill(ctx, x, y, R) {                              // sphere height profile as an alpha ramp (droplets)
  const g = ctx.createRadialGradient(x, y, 0, x, y, R);
  SPHERE.forEach(([s, h]) => g.addColorStop(s, `rgba(255,255,255,${h})`));
  return g;
}

// ───────────────────────── chrome pass ─────────────────────────
// blurObjs(x): sharp white shapes whose height comes from blurring them (letters, the chrome tile).
// domeObjs(x, mode): "mask" fills the shapes white; "height" paints their sphere profile (droplets).
// blob / tube: height computed analytically in the shader; their coverage still comes through domeObjs(x, "mask").
function chromePass(ctx, t, lib, { blurObjs = () => {}, domeObjs = () => {}, shadow = true, rim = 0.2, key = 0.2, rotExtra = 0, blob = null, tube = null, rows = null }) {
  const P = L.P, W = lib.W, H = lib.H;
  const mB = lib.layer("y2k_mB"); blurObjs(mB);
  const mask = lib.layer("y2k_mask"); mask.drawImage(mB.canvas, 0, 0); domeObjs(mask, "mask");
  if (blob) { mask.fillStyle = "#fff"; blobPath(mask, blob); mask.fill(); }
  const tint = (src, blur, col, name = "y2k_tmp") => {
    const x = lib.layer(name); if (blur > 0) x.filter = `blur(${blur}px)`; x.drawImage(src, 0, 0); x.filter = "none";
    x.globalCompositeOperation = "source-in"; x.fillStyle = col; x.fillRect(0, 0, W, H); return x;
  };
  if (shadow) {
    const s = tint(mask.canvas, 11, P("shadow"));
    ctx.save(); ctx.globalAlpha = 0.42; ctx.drawImage(s.canvas, 16, 24); ctx.restore();
  }
  const hm = lib.layer("y2k_hm"); hm.fillStyle = "#000"; hm.fillRect(0, 0, W, H); hm.globalCompositeOperation = "lighter";
  hm.drawImage(tint(mask.canvas, 3, "#f00").canvas, 0, 0);
  hm.drawImage(tint(mask.canvas, 6, "#00f").canvas, 0, 0);
  const g = lib.layer("y2k_g"); g.filter = "blur(14px)"; g.drawImage(mB.canvas, 0, 0); g.filter = "none";
  domeObjs(g, "height");
  g.globalCompositeOperation = "source-in"; g.fillStyle = "#0f0"; g.fillRect(0, 0, W, H);
  hm.drawImage(g.canvas, 0, 0);
  const rot = 0.1 * Math.sin(t * 0.9) + beatSlide(t, lib) + rotExtra;
  ctx.drawImage(FX.render(t, { u_rot: rot, u_kG: 70, u_kB: 18, u_rim: rim, u_key: key,
    u_blob: blob ? [blob.x, blob.y, blob.R, blob.ph] : [0, 0, 0, 0], u_blobS: blob ? [blob.sx, blob.sy] : [1, 1],
    u_tube: tube ? [tube.X, tube.n[0], tube.n[1], tube.hw] : [0, 1, 0, 0], u_rows: rows || [0, 0, 1, 0] }, { u_tex0: hm.canvas }), 0, 0);
}
function beatSlide(t, lib) {                                   // from 2.0 s the studio swings ±0.15 rad, one way then back, on every beat
  let r = 0;                                                    // (a swing, not a spin: flat faces never turn into the flag or a softbox)
  for (let k = 0, b = 2.0; b < 5.0; k++, b += BEAT) r += (k === 0 ? 0.15 : k % 2 ? -0.3 : 0.3) * lib.tween(t, b, b + 0.18, lib.ease.outCubic);
  return r;
}

// ───────────────────────── the blob ─────────────────────────
const sqz = (t, t0, A, tau = 0.11, f = 4.2) => (t < t0 ? 0 : A * Math.exp(-(t - t0) / tau) * Math.cos(2 * Math.PI * f * (t - t0)));
// the small blob's hops after the title: [take-off, landing, from, to, arc height]
const HOPS = (() => {
  const onTile = (k) => [TILE.xs[k], TOP - BLOB.Rsmall];
  const h = [[LAST + 0.04, T.rest, [BLOB.x, FLOOR - BLOB.Rsmall], BLOB.rest, 150]];
  T.lands.forEach((l, k) => h.push([l - HOP, l, k ? onTile(k - 1) : BLOB.rest, onTile(k), k ? 110 : 150]));
  return h;
})();
function blobMain(t, lib) {
  let x = BLOB.x, y, R, s;
  if (t < T.hop) {                                             // the slam, then a hop down-screen, so the letters never touch it
    const u = lib.seg(t, 0.08, T.hop), air = t > 0.08 ? 1 : 0;
    R = lib.lerp(BLOB.R, BLOB.Rlow, u);
    y = lib.lerp(BLOB.y, FLOOR - BLOB.Rlow, u) - 150 * 4 * u * (1 - u) * air;
    s = sqz(t, T.slam, -0.3) + 0.1 * Math.sin(Math.PI * u) * air;
  } else if (t < HOPS[0][0]) {                                  // spitting: it swells, trembles and shrinks to its small size
    const k = lib.seg(t, T.hop, LAST);
    R = lib.lerp(BLOB.Rlow, BLOB.Rsmall, 1 - Math.pow(1 - k, 1.5)) * (1 + 0.08 * Math.sin(Math.PI * lib.seg(t, ...T.gather)));
    y = FLOOR - R;
    s = sqz(t, T.hop, -0.2) + 0.04 * Math.sin(2 * Math.PI * 9 * t) * (1 - k);
  } else {                                                     // the small blob: hops to rest, bobs, hops onto the tiles
    R = BLOB.Rsmall;
    let pos = HOPS[HOPS.length - 1][3]; s = 0;
    for (const [t0, t1, a, b, h] of HOPS) {
      if (t >= t0 && t < t1) { const u = (t - t0) / (t1 - t0); pos = [lib.lerp(a[0], b[0], u), lib.lerp(a[1], b[1], u) - h * 4 * u * (1 - u)]; s += 0.16 * Math.sin(Math.PI * u); break; }
      if (t < t0) { pos = a; break; }
    }
    [x, y] = pos;
    for (const [t0, t1] of HOPS) s += -0.16 * Math.sin(Math.PI * lib.seg(t, t0 - 0.08, t0)) + sqz(t, t1, -0.32);   // crouch, land
    for (const b of T.tiles) if (t < HOPS[1][0]) s += sqz(t, b, -0.1);              // bobs to each tile pop while it waits
  }
  const sy = 1 + s, sx = 1 / Math.sqrt(Math.max(0.4, sy));
  return { x, y: y + R * (1 - sy), R, sx, sy, ph: 2.1 * t };   // squash about the bottom: it stays on the floor
}
function glyphState(g, t, lib) {
  const t0 = g.leave;
  if (t < t0) return null;
  const u = lib.clamp((t - t0) / (g.land - t0));
  const b = blobMain(t0, lib);
  const sy0 = b.y - b.R * 0.6;
  const dropR = 24 * (u < 1 ? 1 : 1 - lib.clamp((t - g.land) / 0.09));
  const dx = lib.lerp(g.sx0, g.cx, u), dy = lib.lerp(sy0, g.cy, u) - (g.word ? 160 : 240) * 4 * u * (1 - u);
  const p = t >= g.land ? lib.spring(t - g.land, { w: 26, zeta: 0.38 }) : 0;
  return { drop: dropR > 0.5 ? { x: dx, y: dy, r: dropR } : null, scale: t >= g.land ? 0.25 + 0.75 * p : 0 };
}
function drawLetters(x, t, tokens, lib) {
  lib.setFont(x, tokens, "display", L.size);
  x.lineJoin = "round"; x.fillStyle = "#fff"; x.strokeStyle = "#fff"; x.lineWidth = L.lw;
  x.textAlign = "center"; x.textBaseline = "alphabetic";
  for (const g of L.glyphs) {
    const s = glyphState(g, t, lib);
    if (!s || s.scale <= 0) continue;
    const sc = s.scale, sxx = sc * (1 + 0.3 * (sc - 1)), syy = sc * (1 - 0.3 * (sc - 1));
    const wave = -24 * Math.sin(Math.PI * lib.clamp((t - T.wave - 0.016 * g.k) / 0.2));   // stage clear: a hop runs through the title
    x.save(); x.translate(g.cx, g.cy + wave); x.scale(sxx, syy); x.translate(0, g.y - g.cy);
    x.fillText(g.ch, 0, 0); x.strokeText(g.ch, 0, 0); x.restore();
  }
}
function drops(x, t, lib, mode) {
  for (const g of L.glyphs) {
    const s = glyphState(g, t, lib);
    if (!s || !s.drop) continue;
    x.fillStyle = mode === "mask" ? "#fff" : domeFill(x, s.drop.x, s.drop.y, s.drop.r);
    x.beginPath(); x.arc(s.drop.x, s.drop.y, s.drop.r, 0, Math.PI * 2); x.fill();
  }
}

// ───────────────────────── tiles ─────────────────────────
function tileState(k, t, lib) {
  const tf = T.tiles[k] - 0.09;                                 // pops up out of the floor: full size right on its eighth
  if (t < tf) return null;
  const p = lib.spring(t - tf, { w: 22, zeta: 0.4 });           // overshoots ~25 %, then a jelly settle
  let sx = p * (1 - 0.25 * (p - 1)), sy = p * (1 + 0.4 * (p - 1));
  const c = T.lands[k];
  if (t >= c) { const q = t - c, d = 0.12 * Math.exp(-q / 0.1) * Math.cos(2 * Math.PI * 6 * q); sx *= 1 + d * 0.5; sy *= 1 - d; }   // the blob lands on it
  return { cx: TILE.xs[k], cy: TILE.y, sx, sy };
}
function tilePath(x, s) {                                      // anchored at the tile's bottom edge (squash from the floor)
  const w = TILE.w * s.sx, h = TILE.h * s.sy, bot = s.cy + TILE.h / 2;
  x.beginPath(); x.roundRect(s.cx - w / 2, bot - h, w, h, TILE.r * Math.min(s.sx, s.sy));
  return { x0: s.cx - w / 2, y0: bot - h, w, h };
}
function gelTile(ctx, k, t, lib, base) {
  const s = tileState(k, t, lib); if (!s) return;
  const P = L.P;
  ctx.save();
  ctx.shadowColor = lib.rgba(P("shadow"), 0.45); ctx.shadowBlur = 18; ctx.shadowOffsetX = 12; ctx.shadowOffsetY = 18;
  const b = tilePath(ctx, s);
  const g = ctx.createLinearGradient(0, b.y0, 0, b.y0 + b.h);
  g.addColorStop(0, lib.mixColor(base, "#000000", 0.25)); g.addColorStop(0.55, base); g.addColorStop(1, lib.mixColor(base, "#ffffff", 0.45));
  ctx.globalAlpha = 0.9; ctx.fillStyle = g; ctx.fill();
  ctx.restore();
  ctx.save(); tilePath(ctx, s); ctx.clip();
  const rg = ctx.createRadialGradient(s.cx, b.y0 + b.h * 1.05, 10, s.cx, b.y0 + b.h * 1.05, b.w * 0.55);   // caustic glow at the bottom
  rg.addColorStop(0, "rgba(255,255,255,0.55)"); rg.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = rg; ctx.fillRect(b.x0, b.y0, b.w, b.h);
  const gl = ctx.createLinearGradient(0, b.y0, 0, b.y0 + b.h * 0.48);                              // the gel gloss
  gl.addColorStop(0, "rgba(255,255,255,0.92)"); gl.addColorStop(1, "rgba(255,255,255,0.12)");
  ctx.fillStyle = gl; ctx.beginPath(); ctx.roundRect(b.x0 + 14, b.y0 + 7, b.w - 28, b.h * 0.46, [TILE.r - 10, TILE.r - 10, 30, 30]); ctx.fill();
  ctx.restore();
  ctx.save(); tilePath(ctx, s); ctx.lineWidth = 3; ctx.strokeStyle = lib.mixColor(base, "#000000", 0.45); ctx.stroke(); ctx.restore();
  ctx.save(); ctx.translate(s.cx, b.y0 + b.h * 0.56); ctx.scale(s.sx, s.sy);                    // the icon, white, slightly sunk
  ctx.fillStyle = "#fff"; ctx.strokeStyle = "#fff"; ctx.shadowColor = lib.rgba(lib.mixColor(base, "#000000", 0.5), 0.6); ctx.shadowBlur = 4; ctx.shadowOffsetY = 3;
  if (k === 0) {                                              // outline: a bullet list
    ctx.lineWidth = 13; ctx.lineCap = "round";
    for (let r = 0; r < 3; r++) { const y = -42 + r * 36; ctx.beginPath(); ctx.arc(-76, y, 9, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-46, y); ctx.lineTo(r === 2 ? 30 : 82, y); ctx.stroke(); }
  } else {                                                    // storyboard: three panels
    for (let r = 0; r < 3; r++) { ctx.beginPath(); ctx.roundRect(-102 + r * 72, -44, 60, 86, 10); ctx.fill(); }
  }
  ctx.restore();
}
function chromeTileMask(x, t, lib) {
  const s = tileState(2, t, lib); if (!s) return;
  x.fillStyle = "#fff"; tilePath(x, s); x.fill();
}
function monitor(ctx, t, lib) {                                // 初版: a little monitor on the chrome tile, the finished frame on it
  const s = tileState(2, t, lib); if (!s) return;
  const P = L.P, cy = s.cy + TILE.h / 2 - TILE.h * s.sy * 0.52;
  ctx.save(); ctx.translate(s.cx, cy); ctx.scale(s.sx, s.sy);
  ctx.fillStyle = P("fg");
  ctx.beginPath(); ctx.roundRect(-14, 34, 28, 22, 4); ctx.roundRect(-46, 52, 92, 12, 6); ctx.fill();          // neck and foot
  ctx.beginPath(); ctx.roundRect(-84, -58, 168, 98, 18); ctx.fill();                                         // bezel
  ctx.fillStyle = P("bg"); ctx.beginPath(); ctx.roundRect(-72, -47, 144, 76, 10); ctx.fill();               // the acid frame
  const g = ctx.createLinearGradient(0, -34, 0, 20);                                                          // a tiny chrome blob
  g.addColorStop(0, P("skyTop")); g.addColorStop(0.45, P("skyLow")); g.addColorStop(0.5, "#ffffff"); g.addColorStop(0.53, P("ground"));
  g.addColorStop(0.85, lib.mixColor(P("endBg"), P("accent"), 0.22)); g.addColorStop(1, P("accent"));
  ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(-10, -7, 30, 26, 0, 0, Math.PI * 2); ctx.fill();
  ctx.strokeStyle = P("fg"); ctx.lineWidth = 3; ctx.stroke();
  ctx.fillStyle = "#fff"; ctx.lineWidth = 2.5; star4(ctx, 42, -24, 15, 0.2); ctx.fill(); ctx.stroke();
  ctx.restore();
}
function tileLabels(ctx, t, tokens, lib) {
  const P = L.P;
  for (let k = 0; k < 3; k++) {
    const s = tileState(k, t, lib); if (!s) continue;
    ctx.save(); ctx.globalAlpha = lib.clamp((t - T.tiles[k]) / 0.06);
    lib.setFont(ctx, tokens, "zh", 56); ctx.fillStyle = P("fg"); ctx.textAlign = "center";
    ctx.fillText(lib.MOTIF[k].zh, TILE.xs[k], TILE.y + TILE.h / 2 + 70);
    ctx.restore();
  }
}
function badges(ctx, t, tokens, lib) {                        // level numbers, stuck on each tile's top-left corner
  const P = L.P;
  for (let k = 0; k < 3; k++) {
    const s = tileState(k, t, lib); if (!s) continue;
    ctx.save(); ctx.globalAlpha = lib.clamp((t - T.tiles[k]) / 0.06);
    ctx.translate(TILE.xs[k] - TILE.w / 2 + 34, TOP + 2); ctx.rotate(-0.06);
    ctx.fillStyle = P("fg"); ctx.beginPath(); ctx.roundRect(-56, -34, 124, 66, 33); ctx.fill();
    lib.setFont(ctx, tokens, "ui", 48); ctx.fillStyle = P("bg"); ctx.textAlign = "center"; ctx.fillText(`1-${k + 1}`, 6, 17);
    ctx.restore();
  }
}
function clearStamp(ctx, k, t, tokens, lib) {                 // CLEAR, slapped on a corner of the tile the blob just cleared
  const c = T.lands[k] + 0.05; if (t < c) return;
  const P = L.P, q = t - c, sc = 1 + 0.5 * Math.exp(-q / 0.06) * Math.cos(2 * Math.PI * 5 * q);
  const last = k === 2;                                         // 1-3's top is busy (level number + the blob): lower-left corner
  ctx.save(); ctx.translate(last ? TILE.xs[k] - 160 : TILE.xs[k] + TILE.w / 2 - 8, last ? TILE.y + TILE.h / 2 - 4 : TOP + 6);
  ctx.rotate(last ? -0.12 : 0.14); ctx.scale(sc, sc);
  lib.setFont(ctx, tokens, "ui", 48); ctx.textAlign = "center";
  ctx.shadowColor = lib.rgba(P("shadow"), 0.5); ctx.shadowBlur = 6; ctx.shadowOffsetX = 4; ctx.shadowOffsetY = 6;
  ctx.fillStyle = P("sticker"); ctx.beginPath(); ctx.roundRect(-96, -38, 192, 72, 36); ctx.fill(); ctx.shadowColor = "transparent";
  ctx.fillStyle = P("accent"); ctx.fillText("CLEAR", 0, 16);
  ctx.restore();
}

// ───────────────────────── stickers, score, sparkles ─────────────────────────
// a white die-cut sticker: flies in from the lower right, slaps down on t0, settles with a visible wobble
function dieCut(ctx, t, tokens, lib, o) {
  const tf = o.t0 - 0.1;
  if (t < tf) return;
  const P = L.P;
  let sc = 1, rot = o.rot, dx = 0, dy = 0, off = 10;
  if (t < o.t0) { const u = (t - tf) / 0.1, e = u * u; sc = lib.lerp(1.35, 1, e); rot = lib.lerp(o.rot - 0.25, o.rot, e); dx = 320 * (1 - e); dy = 200 * (1 - e); off = lib.lerp(50, 10, u); }
  else {
    const q = t - o.t0; sc = 1 - 0.12 * Math.exp(-q / 0.1) * Math.cos(2 * Math.PI * 5 * q);
    rot += 0.06 * Math.exp(-q / 0.12) * Math.sin(2 * Math.PI * 5 * q);
    for (const b of o.wobbles || []) if (t >= b) rot += 0.025 * Math.exp(-(t - b) / 0.12) * Math.sin(2 * Math.PI * 6 * (t - b));
  }
  const s = lib.layer("y2k_stk");
  s.translate(o.x + dx, o.y + dy); s.rotate(rot); s.scale(sc, sc);
  lib.setFont(s, tokens, o.role, o.size); s.textAlign = "center"; s.lineJoin = "round";
  s.fillStyle = P("sticker"); s.beginPath(); s.roundRect(o.lay.x0 - 8, -o.size * 0.52, o.lay.width + 16, o.size * 1.14, o.size * 0.4); s.fill();
  lib.drawGlyphs(s, o.lay, () => ({ fill: "none", stroke: P("sticker"), lineWidth: o.size * 0.63 }));
  lib.drawGlyphs(s, o.lay, () => ({ fill: o.ink }));
  ctx.save(); ctx.shadowColor = lib.rgba(P("shadow"), 0.55); ctx.shadowBlur = 8 + off * 0.4; ctx.shadowOffsetX = off * 0.8; ctx.shadowOffsetY = off * 1.2;
  ctx.globalAlpha = lib.clamp((t - tf) / 0.04); ctx.drawImage(s.canvas, 0, 0); ctx.restore();
}
function scorePill(ctx, t, tokens, lib) {                      // the one game read-out: it counts the blob's landings
  if (t < T.hud - 0.05) return;
  const P = L.P, drop = 1 - lib.spring(t - T.hud + 0.05, { w: 24, zeta: 0.45 });
  const score = T.lands.reduce((s, c) => s + 1000 * lib.clamp((t - c) / 0.15), 0);
  const bump = T.lands.reduce((b, c) => b + (t >= c ? 0.25 * Math.exp(-(t - c) / 0.08) : 0), 1);
  const w = 400;
  ctx.save(); ctx.translate(120, 96 - drop * 170);
  ctx.fillStyle = P("fg"); ctx.beginPath(); ctx.roundRect(0, -38, w, 76, 38); ctx.fill();
  const gl = ctx.createLinearGradient(0, -38, 0, 0); gl.addColorStop(0, "rgba(255,255,255,0.35)"); gl.addColorStop(1, "rgba(255,255,255,0.04)");
  ctx.fillStyle = gl; ctx.beginPath(); ctx.roundRect(14, -35, w - 28, 33, 17); ctx.fill();
  lib.setFont(ctx, tokens, "ui", 44); ctx.fillStyle = P("bg"); lib.drawText(ctx, "SCORE", 32, 16, { tracking: 1 });
  ctx.save(); ctx.translate(w - 34, 19); ctx.scale(bump, bump);
  lib.setFont(ctx, tokens, "ui", 52); ctx.fillStyle = "#fff"; ctx.textAlign = "right"; ctx.fillText(String(Math.floor(score / 10) * 10).padStart(4, "0"), 0, 0); ctx.restore();
  ctx.restore();
}
function sparkles(ctx, t, lib, list) {
  const P = L.P;
  for (const [x, y, r, t0] of list) {
    const q = t - t0 + (t0 === 0 ? 0.12 : 0); if (q < 0 || q > 0.42) continue;
    const s = Math.sin(Math.PI * lib.clamp(q / 0.42)) * (1 + 0.25 * Math.exp(-q / 0.05));
    ctx.save(); ctx.fillStyle = "#fff"; ctx.strokeStyle = P("fg"); ctx.lineWidth = 3; ctx.lineJoin = "round";
    star4(ctx, x, y, r * s, 0.5 * q); ctx.fill(); ctx.stroke(); ctx.restore();
  }
}
function landBurst(ctx, t, lib) {                              // small sparkles fly out where the blob lands on a tile
  for (let k = 0; k < 3; k++) {
    const q = t - T.lands[k]; if (q < 0 || q > 0.45) continue;
    const u = lib.ease.outCubic(q / 0.45);
    for (let i = 0; i < 6; i++) {
      const a = -Math.PI / 2 + (i - 2.5) * 0.55, d = 90 + 150 * u, cx = TILE.xs[k] + Math.cos(a) * d * 1.3, cy = TOP - 20 + Math.sin(a) * d;
      ctx.save(); ctx.fillStyle = i % 2 ? L.P("cyan") : "#fff"; ctx.strokeStyle = L.P("fg"); ctx.lineWidth = 2.5;
      star4(ctx, cx, cy, 26 * (1 - u) + 4, u * 2); ctx.fill(); ctx.stroke(); ctx.restore();
    }
  }
}

// ───────────────────────── the tube ─────────────────────────
// a squeegee sweeping right → left; behind it (on its right), the end frame
const TILT = 0.5;                                              // radians from vertical
const SLANT = Math.tan(TILT), HALF = (hw) => hw / Math.cos(TILT);
function tubeGeom(t, lib) {
  const u = lib.tween(t, ...T.wipe, lib.bezier(0.37, 0, 0.63, 1));
  const X = lib.lerp(2320, -482, u);                             // its upper corner breaks in on the downbeat; out at the end
  return { X, n: [-Math.cos(TILT), Math.sin(TILT)], hw: 165 };   // n points ahead (to the left)
}
const tubeFront = (g, y) => g.X + SLANT * (y - 540) - HALF(g.hw);   // its leading (left) edge at height y
const tubeBack = (g, y) => g.X + SLANT * (y - 540) + HALF(g.hw);
function halfPlane(x, X, n, back) {                             // the side behind (back) or ahead of the tube's centre line
  const c = [X, 540], far = 4000, tx = -n[1], ty = n[0], s = back ? -1 : 1;
  x.beginPath();
  x.moveTo(c[0] + tx * far, c[1] + ty * far); x.lineTo(c[0] - tx * far, c[1] - ty * far);
  x.lineTo(c[0] - tx * far + s * n[0] * far, c[1] - ty * far + s * n[1] * far); x.lineTo(c[0] + tx * far + s * n[0] * far, c[1] + ty * far + s * n[1] * far);
  x.closePath();
}

// ───────────────────────── scenes ─────────────────────────
function acidField(ctx, lib) {                                  // the floor: acid yellow, lifted in the middle like a studio sweep
  const P = L.P, g = ctx.createRadialGradient(960, 470, 80, 960, 520, 1180);
  g.addColorStop(0, lib.mixColor(P("bg"), "#ffffff", 0.45)); g.addColorStop(0.5, P("bg")); g.addColorStop(1, P("bgEdge"));
  ctx.fillStyle = g; ctx.fillRect(0, 0, lib.W, lib.H);
}
function mainScene(ctx, t, tokens, lib) {
  const P = L.P;
  acidField(ctx, lib);
  const ru = lib.seg(t, T.slam, 0.36);                          // the shock ring of the slam
  if (ru < 1) { ctx.save(); ctx.strokeStyle = "#fff"; ctx.globalAlpha = 1 - ru; ctx.lineWidth = 46 * (1 - ru) + 2;
    ctx.beginPath(); ctx.ellipse(BLOB.x, BLOB.y + 150, 430 + 1100 * lib.ease.outCubic(ru), 150 + 420 * lib.ease.outCubic(ru), 0, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
  const su = lib.seg(t, T.slam, 0.2);                           // fall streaks above the landing
  if (su < 1) { ctx.save(); ctx.strokeStyle = "#fff"; ctx.lineCap = "round"; ctx.globalAlpha = 1 - su;
    [[-300, 26, 0.7], [-120, 36, 1], [80, 30, 0.85], [280, 22, 0.6]].forEach(([dx, w, l]) => { ctx.lineWidth = w * (1 - su);
      ctx.beginPath(); ctx.moveTo(BLOB.x + dx, 330 - 330 * l * (1 - 0.6 * su)); ctx.lineTo(BLOB.x + dx, 330 + 40 * su); ctx.stroke(); });
    ctx.restore(); }
  // the blob; from 4.0 the tube's leading edge pushes it and swallows it
  let b = blobMain(t, lib);
  if (t >= T.wipe[0]) {
    const xf = tubeFront(tubeGeom(t, lib), b.y), a = lib.clamp((b.x + b.R - xf) / (1.6 * b.R));
    if (a >= 1) b = null;
    else if (a > 0) { const R = b.R * Math.pow(1 - a, 0.7); b = { ...b, R, x: Math.min(b.x, xf - 0.55 * R), sx: b.sx * (1 - 0.3 * a), sy: b.sy * (1 + 0.2 * a), y: b.y + (b.R - R) }; }
  }
  const early = t < HOPS[0][0];                                // while it spits, the blob shares the letters' pass (droplets merge)
  gelTile(ctx, 0, t, lib, P("cyan"));
  gelTile(ctx, 1, t, lib, P("accent"));
  tileLabels(ctx, t, tokens, lib);
  chromePass(ctx, t, lib, {
    rows: [L.rows[0], L.rows[1], L.rows[2], 0.82],
    blurObjs: (x) => { drawLetters(x, t, tokens, lib); chromeTileMask(x, t, lib); },
    blob: early ? b : null,
    domeObjs: (x, mode) => drops(x, t, lib, mode),
  });
  monitor(ctx, t, lib);
  badges(ctx, t, tokens, lib);
  if (!early && b && b.R > 1) chromePass(ctx, t, lib, { blob: b });   // afterwards it hops over the tiles in its own pass, behind the sticker
  dieCut(ctx, t, tokens, lib, { t0: T.slap, x: STK.x, y: STK.y, rot: STK.rot, lay: L.zh, role: "zh", size: 70, ink: P("fg"), wobbles: T.lands });
  for (let k = 0; k < 3; k++) clearStamp(ctx, k, t, tokens, lib);
  landBurst(ctx, t, lib);
  sparkles(ctx, t, lib, L.sparkles);
  scorePill(ctx, t, tokens, lib);
}
function endScene(ctx, t, tokens, lib) {
  const P = L.P;
  acidField(ctx, lib);
  const q = t - T.endPop, gm = tubeGeom(t, lib);
  // the blob drops out of the back of the tube at the centre, swells, then bursts into "Y2K"
  const e = lib.clamp((END.x + 90 - tubeBack(gm, END.y)) / 160), shrink = lib.seg(t, T.endPop, T.endPop + 0.1);
  let b = null;
  if (e > 0 && shrink < 1) {
    const R = BLOB.Rsmall * lib.ease.outCubic(e) * (1 + 0.25 * lib.seg(t, 4.3, T.endPop)) * (1 - shrink);
    const sy = 1 + sqz(t, 4.31, -0.25) + 0.05 * Math.sin(2 * Math.PI * 11 * t) * lib.seg(t, 4.3, T.endPop);
    b = { x: END.x + 50 * (1 - e), y: END.y + 40, R, sx: 1 / Math.sqrt(sy), sy, ph: 2.1 * t };
  }
  chromePass(ctx, t, lib, {
    rows: [END.y + 40, END.y + 40, 132, 0.82], blob: b && b.R > 1 ? b : null,
    blurObjs: (x) => {
      if (q < 0) return;
      const sc = 0.15 + 0.85 * lib.spring(q, { w: 24, zeta: 0.36 });
      lib.setFont(x, tokens, "display", 330); x.textAlign = "center"; x.lineJoin = "round";
      x.fillStyle = "#fff"; x.strokeStyle = "#fff"; x.lineWidth = 26;
      x.save(); x.translate(END.x, END.y + 40); x.scale(sc * (1 + 0.3 * (sc - 1)), sc * (1 - 0.3 * (sc - 1))); x.translate(0, 119); x.fillText("Y2K", 0, 0); x.strokeText("Y2K", 0, 0); x.restore();
    },
  });
  const field = [[260, 210, 0], [1640, 180, 1], [420, 860, 2], [1520, 900, 3], [180, 560, 4], [1760, 600, 5], [760, 140, 6], [1180, 960, 7]];
  for (const [x, y, i] of field) {                               // sparkles twinkling in turn, two per beat
    const ph = lib.fract((t - 4.0) / 0.8 + i / 8), a = Math.sin(Math.PI * ph);
    ctx.save(); ctx.globalAlpha = a; ctx.fillStyle = ["#fff", P("cyan"), "#fff", P("accent")][i % 4]; ctx.strokeStyle = P("fg"); ctx.lineWidth = 2.5;
    star4(ctx, x, y, 12 + 18 * a, 0.3 * i); ctx.fill(); ctx.stroke(); ctx.restore();
  }
  dieCut(ctx, t, tokens, lib, { t0: T.endSticker, x: 1130, y: 830, rot: 0.07, lay: L.chromeWord, role: "ui", size: 64, ink: P("accent") });
  sparkles(ctx, t, lib, [[1310, 468, 70, T.glint], [560, 790, 40, T.endPop + 0.2]]);
}

export function renderAt(t, ctx, tokens, lib) {
  if (t < T.wipe[0]) return mainScene(ctx, t, tokens, lib);
  const gm = tubeGeom(t, lib), { X, n, hw } = gm;
  if (X < -480) return endScene(ctx, t, tokens, lib);
  mainScene(ctx, t, tokens, lib);
  const B = lib.layer("y2k_end"); endScene(B, t, tokens, lib);
  ctx.save(); halfPlane(ctx, X, n, true); ctx.clip(); ctx.drawImage(B.canvas, 0, 0);
  const bg = ctx.createLinearGradient(X - n[0] * hw, 540 - n[1] * hw, X - n[0] * (hw + 90), 540 - n[1] * (hw + 90));   // its shadow behind it
  bg.addColorStop(0, "rgba(40,45,0,0.4)"); bg.addColorStop(1, "rgba(40,45,0,0)"); ctx.fillStyle = bg; ctx.fillRect(0, 0, lib.W, lib.H); ctx.restore();
  ctx.save(); const sg = ctx.createLinearGradient(X + n[0] * hw, 540 + n[1] * hw, X + n[0] * (hw + 90), 540 + n[1] * (hw + 90));   // and ahead of it
  sg.addColorStop(0, "rgba(40,45,0,0.45)"); sg.addColorStop(1, "rgba(40,45,0,0)"); ctx.fillStyle = sg; halfPlane(ctx, X + n[0] * hw * 0.98, n, false); ctx.fill(); ctx.restore();
  chromePass(ctx, t, lib, {
    shadow: false, rim: 0.3, key: 0, rotExtra: lib.lerp(0.7, -0.7, lib.seg(t, ...T.wipe)), tube: gm,   // a softbox runs across it
    domeObjs: (x, mode) => {
      if (mode !== "mask") return;
      const tx = -n[1], ty = n[0], far = 2000;
      x.beginPath(); x.moveTo(X - n[0] * hw + tx * far, 540 - n[1] * hw + ty * far); x.lineTo(X - n[0] * hw - tx * far, 540 - n[1] * hw - ty * far);
      x.lineTo(X + n[0] * hw - tx * far, 540 + n[1] * hw - ty * far); x.lineTo(X + n[0] * hw + tx * far, 540 + n[1] * hw + ty * far); x.closePath();
      x.fillStyle = "#fff"; x.fill();
    },
  });
  const ga = 0.5 + 0.5 * Math.sin(t * 40);                          // a glint riding the tube's crest (centre line: x = X + SLANT·(y − 540))
  ctx.save(); ctx.fillStyle = "#fff"; ctx.strokeStyle = L.P("fg"); ctx.lineWidth = 3;
  star4(ctx, X + SLANT * (240 - 540) + 40, 240, 50 + 16 * ga, t * 3); ctx.fill(); ctx.stroke(); ctx.restore();
}

// ───────────────────────── foley (→ events.json via styles/_swatch/foley.mjs) ─────────────────────────
const WORD_X = [700, 1300, 640, 1110];
export const FOLEY = [
  { t: T.slam, sfx: "impact", gain_db: -7, pan: 0 },
  { t: T.slam, sfx: "click", gain_db: -6, pan: 0 },                 // a 1–4 kHz attack on the slam (the impact alone is all low end)
  { t: T.hop, sfx: "pop", gain_db: -10, pan: 0, pitch: -6 },
  { t: T.hop, sfx: "swoosh_tonal", gain_db: -10, pan: 0, dur: 0.3, dir: "up", bright: 0.6 },
  ...T.words.map((w, i) => ({ t: w, sfx: "pop", gain_db: -11, pan: pan(WORD_X[i]), pitch: i * 2 })),
  { t: T.slap, sfx: "paper", gain_db: -8, pan: pan(STK.x), dur: 0.12, bright: 0.5 },
  { t: T.rest, sfx: "pop", gain_db: -9, pan: pan(BLOB.rest[0]), pitch: -8 },
  ...T.tiles.map((w, k) => ({ t: w, sfx: "pop", gain_db: -10, pan: pan(TILE.xs[k]), pitch: -3 + k * 3 })),
  // a rubbery squash, higher each hop: it swells from the contact and peaks as the blob is flattest (~60 ms after)
  ...T.lands.map((c, k) => ({ t: c + 0.06, sfx: "swoosh_tonal", gain_db: -7, pan: pan(TILE.xs[k]), dur: 0.12, dir: "down", tone: 0.95, center: [360, 450, 560][k] })),
  { t: (T.wipe[0] + T.wipe[1]) / 2, sfx: "swoosh_tonal", gain_db: -9, dur: 0.5, bright: 0.7, pan_from: 0.8, pan_to: -0.8 },
  { t: T.endPop, sfx: "pop", gain_db: -8, pan: 0, pitch: -4 },
  { t: T.endSticker, sfx: "paper", gain_db: -8, pan: pan(1130), dur: 0.1, bright: 0.6 },
  { t: T.glint, sfx: "shimmer", gain_db: -14, pan: pan(1310) },
];
