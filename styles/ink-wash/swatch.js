// ink-wash swatch · 水墨
//   0.00–0.07  HOOK: one ink drop falls and lands (events.json "drop"); its water jumps out to ~20 % of the frame by 0.1 s
//   0.07–1.90  SIGNATURE: the ink follows the water (水先行，墨随后): a feathered wet edge with capillary fingers, a dark
//              tide line and a paling blot, growing into three layered ranges
//   0.85–2.50  title: Latin line and a vertical Chinese column soak in glyph by glyph (wet → dry); seal stamps 2.60
//   2.00–3.00  motif: three peaks = the same painting at three stages (dry contour → washes → dark accents & moss)
//   3.00–4.00  stillness that breathes: mist drifts, the far ranges pan right-to-left
//   3.84–5.00  SIGNATURE TRANSITION: a second drop falls, lands at 4.00, and the end frame grows inside its bloom (tide line at the edge)
// Every frame is a pure function of t. Heavy textures are built once in setup().

export const fonts = ["Baskerville"];

const LAT = { fonts: { en: { family: ["Baskerville", "Georgia"], style: "italic", weight: 400 } } };
let L = null, FX = null;

const FRAG = `
uniform vec2 u_c; uniform float u_r; uniform float u_an; uniform float u_seed;
uniform float u_rc; uniform float u_ca; uniform float u_tide; uniform float u_hasA; uniform float u_wash; uniform vec3 u_ink;
uniform float u_rw; uniform float u_ww;
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7)) + u_seed * 17.0) * 43758.5453); }
float vn(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h(i), h(i + vec2(1.0, 0.0)), f.x), mix(h(i + vec2(0.0, 1.0)), h(i + vec2(1.0, 1.0)), f.x), f.y); }
float fbm(vec2 p){ float s = 0.0, a = 0.5; for (int k = 0; k < 4; k++) { s += a * vn(p); p *= 2.03; a *= 0.5; } return s; }
vec4 over(vec4 dst, vec3 c, float a){ return vec4(dst.rgb * (1.0 - a) + c * a, dst.a * (1.0 - a) + a); }
void main(){
  vec2 px = vec2(v_uv.x, 1.0 - v_uv.y) * u_res;
  vec2 d = px - u_c; d.y *= u_an;
  float n = fbm(px * 0.0055 + u_seed);
  float n2 = fbm(px * 0.035 + 7.0);
  float dd = length(d) * (0.78 + 0.5 * n) + 26.0 * (n2 - 0.5);                // capillary fingers at the wet edge
  float inside = smoothstep(u_r + 20.0, u_r - 20.0, dd);                        // feathered, not a cut edge
  float band = dd < u_r ? exp(-(u_r - dd) / 22.0) : exp(-pow((dd - u_r) / 7.0, 2.0));
  float ring = u_r > 1.0 ? band * (0.75 + 0.5 * fbm(px * 0.03)) : 0.0;
  vec4 A = texture(u_tex0, v_uv) * u_hasA, B = texture(u_tex1, v_uv);
  vec4 Ap = vec4(A.rgb * A.a, A.a), Bp = vec4(B.rgb * B.a, B.a);
  vec4 O = mix(Ap, Bp, inside);
  O = over(O, u_ink, clamp(u_wash * inside * (0.8 + 0.4 * n), 0.0, 1.0));      // the wet area, darker while it is wet
  float wf = smoothstep(u_rw + 34.0, u_rw - 34.0, dd) * (1.0 - inside);          // water runs ahead of the pigment (水先行, 墨随后)
  float wl = exp(-pow((dd - u_rw) / 6.0, 2.0)) * (1.0 - inside);                // faint line where the water front stops
  O = over(O, u_ink, clamp(u_ww * (wf * (0.75 + 0.5 * n) + 0.8 * wl), 0.0, 1.0));
  O = over(O, u_ink, clamp(u_tide * ring, 0.0, 1.0));                         // tide line: pigment piles up at the wet edge
  float cd = length(px - u_c) * (0.82 + 0.36 * fbm(px * 0.02 + 3.0));
  float blot = smoothstep(u_rc + 12.0, u_rc - 12.0, cd + 18.0 * (n2 - 0.5)) * (0.5 + 0.5 * exp(-(u_rc - cd) / 14.0)) * (0.88 + 0.12 * smoothstep(0.0, u_rc, cd));   // wet blot: soft edge, pigment piled at the rim, a slightly paler heart
  O = over(O, u_ink, clamp(u_ca * blot, 0.0, 1.0));                            // the drop itself: a blot with a darker rim, paling as it spreads
  outColor = O.a > 0.0 ? vec4(O.rgb / O.a, O.a) : vec4(0.0);
}`;

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
// ── ink colour: cool grey when thin, warm black when loaded
const COOL = [133, 140, 148], WARM = [24, 21, 19];
const inkRGB = (d) => { const u = Math.min(1, Math.max(0, (d - 0.1) / 0.8)); const s = u * u * (3 - 2 * u); return COOL.map((c, i) => Math.round(c + (WARM[i] - c) * s)); };
const inkCss = (d, a) => { const [r, g, b] = inkRGB(d); return `rgba(${r},${g},${b},${a})`; };

// ── brush strokes: centreline + pressure profile + bristle tracks (flying white). Geometry built once.
function makeStroke(lib, pts, w, { prof = "brush", dry = 0.3, seed = 1, nb = 7, dens = 0.8 } = {}) {
  // resample by arc length
  const P = [pts[0]]; let acc = 0;
  for (let i = 1; i < pts.length; i++) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i], l = Math.hypot(x1 - x0, y1 - y0), n = Math.max(1, Math.ceil(l / 4));
    for (let k = 1; k <= n; k++) P.push([x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n]);
  }
  const S = [0]; for (let i = 1; i < P.length; i++) { acc += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); S.push(acc); }
  const N = P.map((p, i) => { const a = P[Math.max(0, i - 1)], b = P[Math.min(P.length - 1, i + 1)]; const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [-dy / l, dx / l]; });
  const pr = (s) => prof === "tip" ? Math.min(1, s * 6) * Math.pow(1 - s, 0.9) + 0.05
    : prof === "even" ? Math.min(1, s * 10, (1 - s) * 10) : Math.min(1, s * 8) * (1 - 0.75 * s) + 0.08;   // brush: press in, taper out
  const Wd = S.map((s) => w * pr(s / acc) * (1 + 0.22 * lib.noise1(s / 23, seed)));
  const bristles = Array.from({ length: nb }, (_, b) => ({ off: (b / (nb - 1 || 1) - 0.5) * 0.9, seed: seed * 31 + b, load: 0.55 + 0.45 * lib.hash(seed, b, 9) }));
  return { P, S, N, Wd, len: acc, dry, dens, bristles, seed };
}
function drawStroke(ctx, lib, st, u = 1, alpha = 1) {
  if (u <= 0) return;
  const n = Math.max(2, Math.round(1 + (st.P.length - 1) * Math.min(1, u)));
  const body = (1 - st.dry) ** 1.6;
  if (body > 0.02) {
    ctx.beginPath();
    for (let i = 0; i < n; i++) { const p = st.P[i], q = st.N[i], w = st.Wd[i] / 2; i ? ctx.lineTo(p[0] + q[0] * w, p[1] + q[1] * w) : ctx.moveTo(p[0] + q[0] * w, p[1] + q[1] * w); }
    for (let i = n - 1; i >= 0; i--) { const p = st.P[i], q = st.N[i], w = st.Wd[i] / 2; ctx.lineTo(p[0] - q[0] * w, p[1] - q[1] * w); }
    ctx.closePath(); ctx.fillStyle = inkCss(st.dens, alpha * body * 0.9); ctx.fill();
  }
  // bristles: ink load drops along the stroke; long-scale noise decides where each one breaks (arc-length based, stable)
  ctx.lineCap = "round";
  for (const b of st.bristles) {
    ctx.beginPath(); let on = false;
    for (let i = 0; i < n; i += 2) {
      const s = st.S[i] / st.len, brk = lib.noise1(st.S[i] / 40, b.seed) * 0.5 + 0.5;
      const alive = brk < 1.05 - st.dry * (0.35 + 0.9 * s) * (1.2 - b.load);
      const p = st.P[i], q = st.N[i], w = st.Wd[i] * b.off, x = p[0] + q[0] * w, y = p[1] + q[1] * w;
      if (alive) { on ? ctx.lineTo(x, y) : ctx.moveTo(x, y); on = true; } else on = false;
    }
    ctx.strokeStyle = inkCss(st.dens, alpha * (0.35 + 0.5 * b.load)); ctx.lineWidth = Math.max(1, st.Wd.reduce((a, c) => Math.max(a, c), 0) / st.bristles.length * 0.9); ctx.stroke();
  }
}

// ── the three ranges: per-pixel at half resolution, once
function buildRanges(lib) {
  const w = 960, h = 540, cv = document.createElement("canvas"); cv.width = w; cv.height = h;
  const x = cv.getContext("2d"), img = x.createImageData(w, h), D = img.data;
  const R = [
    { base: 250, amp: 120, tone: 0.22, fall: 80, x0: 60, x1: 780, seed: 3, peaks: [[120, 0.5, 50, 70], [290, 1, 55, 90], [455, 0.72, 70, 45], [640, 0.86, 45, 80]] },
    { base: 292, amp: 78, tone: 0.42, fall: 42, x0: 150, x1: 700, seed: 7, peaks: [[230, 0.75, 40, 60], [372, 1, 50, 38], [540, 0.55, 45, 70]] },
    { base: 314, amp: 46, tone: 0.62, fall: 24, x0: 470, x1: 770, seed: 11, peaks: [[560, 1, 38, 30], [690, 0.7, 34, 44]] },
  ];
  const ridge = (r, px) => {
    let m = 0; for (const [cx, a, wl, wr] of r.peaks) { const q = px < cx ? (cx - px) / wl : (px - cx) / wr; m = Math.max(m, a * (0.6 * Math.exp(-q) + 0.4 * Math.exp(-q * q))); }
    return r.base - r.amp * m - 11 * lib.fbm2(px / 16, r.seed, { octaves: 3, seed: r.seed });
  };
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    let a = 0, dens = 0;
    for (const r of R) {
      const y0 = ridge(r, i), d = j - y0; if (d < 0) continue;
      const edge = Math.min(1, (i - r.x0) / 60, (r.x1 - i) / 60); if (edge <= 0) continue;
      const tex = 0.8 + 0.4 * (lib.fbm2(i / 7, j / 26, { octaves: 2, seed: r.seed + 1 }) * 0.5 + 0.5);
      const mist = 1 - 0.55 * Math.max(0, Math.sin((j - r.base) / 9)) * Math.min(1, d / r.fall);
      const ai = r.tone * (0.42 + 0.58 * Math.exp(-d / 10)) * Math.exp(-d / r.fall) * tex * mist * edge;
      a = a + ai * (1 - a); dens = Math.max(dens, r.tone * 1.3);
    }
    const [cr, cg, cb] = inkRGB(dens), k = (j * w + i) * 4;
    D[k] = cr; D[k + 1] = cg; D[k + 2] = cb; D[k + 3] = Math.round(Math.min(1, a) * 255);
  }
  x.putImageData(img, 0, 0);
  const full = document.createElement("canvas"); full.width = lib.W; full.height = lib.H;
  const f = full.getContext("2d"); f.imageSmoothingQuality = "high"; f.drawImage(cv, 0, 0, lib.W, lib.H);
  // 苔点 moss dots along both ridges
  const rr = lib.rng(41);
  for (const [ri, count, dens] of [[0, 14, 0.55], [1, 30, 0.9], [2, 18, 1]]) {
    const r = R[ri];
    for (let k = 0; k < count; k++) {
      const px = r.x0 + 40 + rr() * (r.x1 - r.x0 - 80), py = ridge(r, px) + rr() * 5;
      f.fillStyle = inkCss(dens, 0.5 + rr() * 0.4); f.beginPath(); f.ellipse(px * 2, py * 2, 2.5 + rr() * 3, 1.8 + rr() * 2, rr() * 3, 0, lib.TAU); f.fill();
    }
  }
  return full;
}

// ── a small peak in local coords (same painting, three stages): contour strokes, wash sprite, 焦墨 accents, moss dots
function buildPeak(lib, k) {
  const seed = 200;                                   // identical shape for all three stages
  const left = [[-156, 10], [-120, -30], [-86, -78], [-52, -112], [-30, -150], [-8, -184], [8, -176]];
  const right = [[8, -176], [30, -142], [52, -150], [74, -112], [100, -70], [128, -30], [156, 10]];
  const front = [[-96, 16], [-52, -14], [-8, -26], [40, -14], [96, 16]];   // a low front hill
  const light = [makeStroke(lib, left, 10, { dry: 0.55, seed, nb: 7, dens: 0.66 }), makeStroke(lib, right, 9, { dry: 0.6, seed: seed + 1, nb: 7, dens: 0.66 })];
  const heavy = [makeStroke(lib, left, 17, { dry: 0.28, seed: seed + 2, nb: 8, dens: 0.93 }), makeStroke(lib, right, 15, { dry: 0.3, seed: seed + 3, nb: 8, dens: 0.93 }),
    makeStroke(lib, front, 11, { dry: 0.35, seed: seed + 4, nb: 6, dens: 0.9 })];
  const poly = [...left, ...right.slice(1), [156, 24], [-156, 24]];
  const wash = document.createElement("canvas"); wash.width = 440; wash.height = 320;
  const x = wash.getContext("2d"); x.translate(220, 250);
  x.filter = "blur(6px)";
  const g = x.createLinearGradient(0, -184, 0, 24); g.addColorStop(0, inkCss(0.4, 0.62)); g.addColorStop(0.5, inkCss(0.34, 0.34)); g.addColorStop(1, inkCss(0.25, 0.04));
  x.fillStyle = g; x.beginPath(); poly.forEach(([a, b], i) => (i ? x.lineTo(a, b) : x.moveTo(a, b))); x.closePath(); x.fill();
  x.fillStyle = inkCss(0.55, 0.32); x.beginPath(); x.moveTo(8, -176); x.lineTo(52, -150); x.lineTo(110, -58); x.lineTo(60, -10); x.lineTo(18, -70); x.closePath(); x.fill();   // shadow side
  x.fillStyle = inkCss(0.5, 0.3); x.beginPath(); front.forEach(([a, b], i) => (i ? x.lineTo(a, b) : x.moveTo(a, b))); x.closePath(); x.fill();
  x.filter = "none";
  const accents = [
    [[-44, -128], [-56, -96], [-66, -60]], [[24, -140], [38, -108], [46, -78]], [[-100, -60], [-110, -30], [-116, -4]],
    [[84, -96], [94, -66], [102, -34]], [[-14, -110], [-20, -80]], [[58, -130], [66, -104]],
  ].map((p, i) => makeStroke(lib, p, 8, { prof: "tip", dry: 0.3, seed: seed + 10 + i, nb: 4, dens: 1 }));
  const r = lib.rng(seed + 9), dots = Array.from({ length: 16 }, () => { const u = r() * 2 - 1; return [u * 110, -176 + Math.abs(u) * 150 + r() * 12, 3 + r() * 4]; });
  return { light, heavy, wash, accents, dots };
}

// ── seal: 白文 (the character is carved out of a red square)
function buildSeal(lib, tokens, size, ch) {
  const c = document.createElement("canvas"); c.width = c.height = size + 12;
  const x = c.getContext("2d"), col = lib.color(tokens, "accent"), r = lib.rng(77);
  x.translate(6, 6); x.fillStyle = col;
  x.beginPath(); const pts = [[0, 0], [size, 0], [size, size], [0, size]];
  for (let i = 0; i < 4; i++) { const [a, b] = pts[i], [c2, d] = pts[(i + 1) % 4]; for (let k = 0; k < 6; k++) { const u = k / 6; x.lineTo(a + (c2 - a) * u + (r() - 0.5) * 3, b + (d - b) * u + (r() - 0.5) * 3); } }
  x.closePath(); x.fill();
  x.globalCompositeOperation = "destination-out";
  lib.setFont(x, tokens, "zh", size * 0.74, { weight: 700 }); x.textAlign = "center"; x.textBaseline = "middle"; x.fillStyle = "#000";
  x.fillText(ch, size / 2, size / 2 + size * 0.04);
  for (let k = 0; k < 60; k++) { x.globalAlpha = 0.25 + r() * 0.5; x.beginPath(); x.arc(r() * size, r() * size, 0.6 + r() * 1.4, 0, lib.TAU); x.fill(); }   // ink-paste speckle
  return c;
}

export async function setup(ctx, tokens, lib) {
  [T, S] = await loadTimes();
  const P = (k) => lib.color(tokens, k);
  L = {
    ranges: buildRanges(lib),
    peaks: [0, 1, 2].map((k) => buildPeak(lib, k)),
    peakX: [470, 860, 1250], peakY: 830,
    seal: buildSeal(lib, tokens, 74, "帧"), sealEnd: buildSeal(lib, tokens, 64, "墨"),
    drop: [800, 560], drop2: [960, 520],
    zhSize: 76, zhX: 1636, zhY0: 206, zhStep: 90,
    enSize: 96, enX: 196, enY: 236,
    horizon: makeStroke(lib, [[560, 610], [800, 600], [1060, 606], [1360, 596]], 7, { prof: "even", dry: 0.55, seed: 901, nb: 7, dens: 0.4 }),
    shore: makeStroke(lib, [[300, 852], [620, 846], [980, 852], [1330, 844], [1470, 850]], 9, { prof: "even", dry: 0.62, seed: 777, nb: 8, dens: 0.55 }),
    ink: inkRGB(0.95).map((c) => c / 255),
  };
  FX = lib.shader(FRAG);
  L.P = P;
}

// ── painters
function paperBase(ctx, tokens, lib) {
  ctx.fillStyle = lib.color(tokens, "bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  lib.paper(ctx, { tone: lib.color(tokens, "bg"), amount: 1, blotch: 0.05, tooth: 0.03, fiber: 1.0, seed: 4 });
}
function bloomUniforms(t, t0, c, { R, tau, an, tide, tideTau = 0.55, seed, core = 0, coreR = 110, coreTau = 0.8, wash = 0, washTau = 0.4, water = null }) {
  const a = Math.max(0, t - t0), on = t >= t0;
  const w = water && on ? water : null;                   // water halo: a fast jump (the splash) plus a slow creep, drying as it goes
  return {
    u_rw: w ? w.Rf * (1 - Math.exp(-a / w.tauF)) + w.R * (1 - Math.exp(-a / w.tau)) : 0, u_ww: w ? w.amt * Math.exp(-a / w.dry) : 0,
    u_c: c, u_r: on ? R * (1 - Math.exp(-a / tau)) : 0, u_an: an, u_seed: seed,
    u_rc: 16 + coreR * (1 - Math.exp(-a / 0.3)), u_ca: on ? core * Math.exp(-a / coreTau) : 0,
    u_tide: on ? tide * Math.exp(-a / tideTau) : 0, u_wash: on ? wash * Math.exp(-a / washTau) : 0, u_hasA: 0, u_ink: L.ink,
  };
}
function fallingDrop(ctx, lib, t, t0, t1, [cx, cy]) {
  if (t < t0 || t >= t1) return;
  const u = lib.seg(t, t0, t1), y = cy - (t1 - t0 < 0.1 ? 120 : 360) * (1 - u * u);
  ctx.save(); ctx.fillStyle = inkCss(0.95, 0.92);
  ctx.beginPath(); ctx.ellipse(cx, y, 9, 12 + 10 * u, 0, 0, lib.TAU); ctx.fill(); ctx.restore();
}

function scene(ctx, t, tokens, lib) {
  const { seg, W, H } = lib, P = L.P;
  paperBase(ctx, tokens, lib);

  // ranges: bloom out of the drop (0.30 → ~1.8), then drift slowly right-to-left
  const pan = -22 * Math.max(0, t - 1.6);
  if (t >= T.drop) {
    const src = lib.offscreen("iw_rng", (x) => x.drawImage(L.ranges, pan, 0));
    const out = FX.render(t, bloomUniforms(t, T.drop, L.drop, { R: 1300, tau: 0.42, an: 2.3, tide: 0.4, tideTau: 0.55, seed: 3.1, core: 0.95, coreR: 150, coreTau: 0.28, wash: 0.4, washTau: 0.45, water: { Rf: 720, tauF: 0.028, R: 1300, tau: 0.5, amt: 0.15, dry: 0.5 } }), { u_tex0: src, u_tex1: src });
    ctx.drawImage(out, 0, 0);
  }
  fallingDrop(ctx, lib, t, 0.0, T.drop, L.drop);
  fallingDrop(ctx, lib, t, T.drop2 - 0.16, T.drop2, L.drop2);             // the transition's drop starts falling inside the scene

  // mist bands drifting left→right over the ranges (they are paper: 留白 that moves)
  for (let k = 0; k < 3; k++) {
    const y = 520 + k * 44, x = ((t * (8 + k * 4) + k * 520) % 1400) + 100;
    const g = ctx.createLinearGradient(0, y - 18, 0, y + 18);
    g.addColorStop(0, lib.rgba(P("bg"), 0)); g.addColorStop(0.5, lib.rgba(P("bg"), 0.55 * lib.env(t, 1.2, 99, 0.8, 0))); g.addColorStop(1, lib.rgba(P("bg"), 0));
    ctx.fillStyle = g; ctx.fillRect(x - 500, y - 18, 1400, 36);
  }

  // motif: the same painting at three stages
  L.peaks.forEach((pk, k) => peak(ctx, t, tokens, lib, pk, k));

  // after the motif is in, one small brush event per beat: 2.8 a dry shore stroke, 3.2 and 3.6 birds cross the far ranges
  drawStroke(ctx, lib, L.shore, lib.tween(t, T.shoreEnd - 0.35, T.shoreEnd, lib.ease.inOutCubic), 0.75);   // its swish swells to the lift-off
  for (const [t0, y0, k] of [[3.2, 430, 0], [3.2, 452, 1], [3.6, 410, 2]]) {
    if (t < t0) continue;
    const a = t - t0, x = 1480 - a * 240 - k * 40, y = y0 + 6 * Math.sin(a * 5 + k), fl = 7 * Math.sin(lib.step(t, 12) * 18 + k);
    ctx.save(); ctx.strokeStyle = inkCss(0.95, lib.clamp(a * 5)); ctx.lineWidth = 3; ctx.lineCap = "round";
    ctx.beginPath(); ctx.moveTo(x - 16, y - fl); ctx.quadraticCurveTo(x - 7, y - 3, x, y); ctx.quadraticCurveTo(x + 7, y - 3, x + 16, y - fl); ctx.stroke(); ctx.restore();
  }

  // titles
  titles(ctx, t, tokens, lib);
}

function peak(ctx, t, tokens, lib, pk, k) {
  const P = L.P, t0 = 2.0 + k * 0.2;
  if (t < t0) return;
  ctx.save(); ctx.translate(L.peakX[k], L.peakY);
  const uC = lib.tween(t, t0, t0 + 0.34, lib.ease.inOutCubic);
  if (k >= 1) {                                                  // 分镜 & 初版: washes, painted downward from the ridge
    const uw = lib.tween(t, t0 + 0.2, t0 + 0.55, lib.ease.outCubic);
    if (uw > 0) { ctx.save(); ctx.beginPath(); ctx.rect(-220, -250, 440, 60 + 260 * uw); ctx.clip(); ctx.globalAlpha = uw * (k === 2 ? 1 : 0.85); ctx.drawImage(pk.wash, -220, -250); ctx.restore(); }
  }
  if (k < 2) pk.light.forEach((st, i) => drawStroke(ctx, lib, st, lib.clamp(uC * 2 - i), 0.95));   // 大纲: a dry, pale contour
  else {                                                         // 初版: loaded strokes, 焦墨 accents, moss dots stepping in
    pk.heavy.forEach((st, i) => drawStroke(ctx, lib, st, lib.clamp(uC * 3 - i)));
    pk.accents.forEach((st, i) => drawStroke(ctx, lib, st, lib.tween(t, t0 + 0.32 + i * 0.04, t0 + 0.5 + i * 0.04, lib.ease.outCubic)));
    const nd = Math.floor(lib.seg(t, t0 + 0.45, t0 + 0.75) * pk.dots.length + 1e-9);
    for (let i = 0; i < nd; i++) { const [x, y, r] = pk.dots[i]; ctx.fillStyle = inkCss(1, 0.92); ctx.beginPath(); ctx.ellipse(x, y, r, r * 0.7, i, 0, lib.TAU); ctx.fill(); }
  }
  const la = lib.tween(t, t0 + 0.15, t0 + 0.5, lib.ease.outCubic);   // label soaks in with the contour
  ctx.globalAlpha = la; ctx.textAlign = "center";
  lib.setFont(ctx, tokens, "zh", 50, { weight: 400 }); ctx.fillStyle = P("extra.0");
  ctx.fillText(lib.MOTIF[k].zh, 0, 100);
  lib.setFont(ctx, LAT, "en", 42); ctx.fillStyle = P("extra.0");
  ctx.fillText(lib.MOTIF[k].en, 0, 150);
  ctx.restore();
}

function titles(ctx, t, tokens, lib) {
  const P = L.P;
  // Latin line: glyphs soak in left→right; recently arrived glyphs are wet (drawn through the ink-bleed filter)
  lib.setFont(ctx, LAT, "en", L.enSize); ctx.fillStyle = P("fg");
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: L.enX, y: L.enY, align: "left", tracking: 0 });
  const wetEN = [], dryEN = [];
  lay.glyphs.forEach((g, i) => { const t0 = 0.8 + i * 0.045; if (t < t0) return; (t - t0 < 0.32 ? wetEN : dryEN).push([g, t - t0]); });
  // Chinese column: vertical, top to bottom; punctuation sits in the upper-right of its cell (vertical typesetting)
  lib.setFont(ctx, tokens, "zh", L.zhSize, { weight: 400 });
  const zh = lib.graphemes(lib.TITLE_ZH), wetZH = [], dryZH = [];
  zh.forEach((ch, i) => { const t0 = 1.25 + i * 0.12; if (t < t0) return; (t - t0 < 0.34 ? wetZH : dryZH).push([ch, i, t - t0]); });
  const zhPos = (ch, i) => { const punct = "，。".includes(ch); return [L.zhX + (punct ? L.zhSize * 0.36 : 0), L.zhY0 + i * L.zhStep - (punct ? L.zhSize * 0.52 : 0)]; };
  const drawZH = (x, ch, i, clipU) => {
    const [cx, cy] = zhPos(ch, i); x.save();
    if (clipU < 1) { x.beginPath(); x.rect(cx - 60, cy - 60, 120, 20 + 110 * clipU); x.clip(); }
    x.fillText(ch, cx, cy); x.restore();
  };
  ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  dryZH.forEach(([ch, i]) => drawZH(ctx, ch, i, 1));
  ctx.restore();
  lib.drawGlyphs(ctx, lay, (g, i) => (dryEN.some(([h]) => h === g) ? {} : null));
  if (wetEN.length || wetZH.length) {
    lib.inkBleed(ctx, (x) => {
      lib.setFont(x, LAT, "en", L.enSize); x.fillStyle = P("fg");
      lib.drawGlyphs(x, lay, (g) => { const w = wetEN.find(([h]) => h === g); return w ? { alpha: lib.clamp(w[1] / 0.12) } : null; });
      lib.setFont(x, tokens, "zh", L.zhSize, { weight: 400 }); x.fillStyle = P("fg"); x.textAlign = "center"; x.textBaseline = "middle";
      wetZH.forEach(([ch, i, a]) => drawZH(x, ch, i, lib.ease.outCubic(lib.clamp(a / 0.22))));
    }, { spread: 1.6, rough: 1.2, freq: 0.05, seed: 3 + lib.step(t, 10) * 10, sharp: 5 });
  }
  // seal stamps (3 frames: slightly large, then pressed)
  if (t >= T.seal) {
    const u = lib.seg(t, T.seal, T.seal + 0.1), s = 1.14 - 0.14 * lib.ease.outCubic(u);
    ctx.save(); ctx.globalAlpha = 0.25 + 0.75 * lib.clamp(u * 2); ctx.translate(L.zhX - 96, L.zhY0 + 8 * L.zhStep - 10); ctx.scale(s, s);
    ctx.drawImage(L.seal, -L.seal.width / 2, -L.seal.height / 2); ctx.restore();
  }
}

function endFrame(ctx, t, tokens, lib) {
  const P = L.P;
  paperBase(ctx, tokens, lib);
  drawStroke(ctx, lib, L.horizon, lib.tween(t, 4.25, 4.8, lib.ease.inOutCubic), 0.8);
  lib.setFont(ctx, tokens, "zh", 96, { weight: 400 }); ctx.fillStyle = P("fg"); ctx.textAlign = "center"; ctx.textBaseline = "middle";
  ctx.fillText("水", 960, 400); ctx.fillText("墨", 960, 506);
  ctx.drawImage(L.sealEnd, 1036 - L.sealEnd.width / 2, 536 - L.sealEnd.height / 2);
  lib.setFont(ctx, LAT, "en", 108, { weight: 600 }); ctx.fillStyle = P("fg"); ctx.fillText("ink-wash", 960, 736);   // dark ink, ≥ 44 px x-height at 1080p
}

export function renderAt(t, ctx, tokens, lib) {
  if (t < T.drop2) { scene(ctx, t, tokens, lib); return; }
  // transition: a second drop falls onto the painting; the end frame grows inside its bloom
  const A = lib.offscreen("iw_A", (x) => scene(x, t, tokens, lib));
  const B = lib.offscreen("iw_B", (x) => endFrame(x, t, tokens, lib));
  const u = bloomUniforms(t, T.drop2, L.drop2, { R: 2700, tau: 0.5, an: 1.0, tide: 0.85, tideTau: 0.8, seed: 7.7, core: 0.97, coreR: 260, coreTau: 0.14, wash: 0.22, washTau: 0.18 });
  u.u_hasA = 1;
  ctx.drawImage(FX.render(t, u, { u_tex0: A, u_tex1: B }), 0, 0);
}
