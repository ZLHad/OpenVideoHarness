// crt-terminal swatch: everything is a real character on a fixed grid, lit by one amber phosphor.
// The scene draws a greyscale "beam" canvas (brightness only, glyphs snapped to 24 × 48 px cells; double-width,
// double-height lines use 48 × 96), then a CRT shader does barrel curvature, bloom, the P3 amber ramp, scanlines,
// vignette, frame-seeded flicker, the rounded tube mask and the power-on / power-off collapse.
//   0.05–0.25 power-on: a full-width line flashes and blooms open to the full raster (overexposed, then settles)
//   0.2–0.8  boot log at double size, machine speed; 0.8 s the rows clear top → bottom with afterglow
//   0.95–2.6 "> title", then the title typed by a human (uneven, pauses at spaces); Chinese commits in two IME chunks
//   2.0–3.62 motif: `$ tree film/` prints an ASCII tree outline/ → storyboard/ → draft.mp4; the draft render bar
//            fills in whole cells to 100 % at 3.6 s and READY flips to inverse video; a render log scrolls every 0.4 s;
//            the prompt cursor blinks every 0.5 s
//   4.0–4.36 power-off: line, then a dot (≤ 0.16 s of afterglow); 4.36 the tube comes back in inverse video with the name
// The status line shows the real frame number of the frame being rendered.

let L = null;
const CW = 24, CH = 48, X0 = 120, Y0 = 84, COLS = 70, ROWS = 19;
const DIM = 0.42, NORM = 0.78, BOLD = 1.0, TAU_GLOW = 0.12;

// ONE timing table for the picture and the foley (FOLEY → events.json via styles/_swatch/foley.mjs)
const TL = {
  on: [0.05, 0.25], boot0: 0.22, bootStag: 0.16, clear: 0.8, cmd: 0.95, title0: 1.22, ime: [2.32, 2.52],
  tree: 2.0, treeLine: 2.18, barStart: 2.7, barStep: 0.09, ready: 3.62, log: 2.6, prompt: 2.62,
  off: 4.0, dot: 4.2, reOn: 4.36,
};
const TITLE = "Every frame is code.";                                  // = lib.TITLE_EN (ASCII, one grapheme per char)
const h1 = (i) => { let x = Math.imul(i ^ 0x9e3779b9, 0x85ebca6b); x ^= x >>> 13; x = Math.imul(x, 0xc2b2ae35); x ^= x >>> 16; return (x >>> 0) / 4294967296; };
// the human typing schedule for the title: seeded per-character delays, pauses at spaces (pure data)
const TITLE_TIMES = [...TITLE].reduce((a, ch, i) => { a.push(i ? a[i - 1] + 0.034 + 0.03 * h1(i - 1) + (TITLE[i - 1] === " " ? 0.07 : 0) : TL.title0); return a; }, []);
const colX = (col) => X0 + col * CW;
const BOOT = ["OVH-TTY 0.8", "MEM 65536K .. OK", "P3 AMBER ONLINE"];
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;   // pan = (2x/W − 1) · 0.7
export const FOLEY = [
  { t: TL.on[0], sfx: "boom", gain_db: -9 },                                              // the tube thumps on
  ...BOOT.map((s, i) => ({ t: TL.boot0 + i * TL.bootStag + s.length / 70, sfx: "tick", gain_db: -16, pan: pan(colX(2 * s.length)) })),   // machine output: one tick per line end
  { t: TL.clear, sfx: "toggle", gain_db: -16, pan: pan(colX(10)) },                        // rows clear
  { t: TL.cmd, sfx: "typing", gain_db: -18, pan: pan(colX(3)) },                           // "> title"
  ...[...TITLE].flatMap((ch, i) => (ch !== " " && (i === 0 || TITLE[i - 1] === " ") ? [{ t: TITLE_TIMES[i], sfx: "typing", gain_db: -14, pan: pan(colX(2 * i + 4)) }] : [])),   // a human types each word
  ...TL.ime.map((t, k) => ({ t, sfx: "click", gain_db: -10, pan: pan(colX(k ? 36 : 16)) })),   // IME commits
  { t: TL.tree + "$ tree film/".length / 80, sfx: "tick", gain_db: -16, pan: pan(colX(12)) },   // `$ tree film/` (machine speed)
  { t: TL.log, sfx: "tick", gain_db: -18, pan: pan(colX(14)) },                            // render log starts
  ...[2, 4, 6, 8].map((P) => ({ t: TL.barStart + P * TL.barStep, sfx: "tick", gain_db: -14, pan: pan(colX(27 + P)) })),   // bar fills (every 2nd cell)
  { t: TL.ready, sfx: "success", gain_db: -12, pan: pan(colX(48)) },                       // READY flips to inverse video
  { t: TL.off + 0.02, sfx: "glitch", gain_db: -14 },                                       // power-off
  { t: TL.dot, sfx: "swish_rev", gain_db: -12 },                                           // collapses into the dot
  { t: TL.reOn, sfx: "click", gain_db: -8 },                                               // back on, inverse video (short: a boom tail would be cut at 5 s)
];

const FRAG = `
uniform float u_sx, u_sy, u_boost, u_flick;
float h21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float lum(vec2 uv){ return texture(u_tex0, uv).r; }
void main(){
  vec2 c = v_uv * 2.0 - 1.0;
  float r2 = dot(c, c);
  vec2 w = c * (1.0 + 0.045 * r2);                     // barrel curvature
  vec2 q = w / vec2(u_sx, u_sy);                        // power-on / off squeeze
  vec2 uv = q * 0.5 + 0.5;
  // rounded tube mask (in warped space)
  vec2 e = abs(w) - vec2(0.955, 0.935);
  float box = length(max(e + 0.06, 0.0)) - 0.06;
  float inside = 1.0 - smoothstep(-0.004, 0.004, box);
  vec3 glass = vec3(0.051, 0.031, 0.016);
  vec3 col = glass;
  if (inside > 0.0 && uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0) {
    vec2 px = 1.0 / u_res;
    float core = lum(uv);
    float b1 = 0.0, b2 = 0.0, b3 = 0.0;
    for (int i = 0; i < 8; i++) {
      float a = float(i) * 0.785398;
      vec2 d = vec2(cos(a), sin(a));
      b1 += lum(uv + d * px * 3.0); b2 += lum(uv + d * px * 8.0); b3 += lum(uv + d * px * 18.0);
    }
    float L = core + 0.22 * b1 / 8.0 + 0.2 * b2 / 8.0 + 0.16 * b3 / 8.0;
    L *= u_boost * u_flick;
    vec3 amber = vec3(1.0, 0.690, 0.0), hot = vec3(1.0, 0.890, 0.639);
    vec3 ph = amber * min(L, 1.0) * 0.96 + (hot - amber) * smoothstep(0.9, 1.6, L);
    float row = mod(gl_FragCoord.y, 3.0);
    float scan = row < 1.0 ? 1.0 - 0.3 * (1.0 - 0.5 * min(L, 1.0)) : 1.0;
    col = glass + min(ph * scan, hot);
  }
  float vig = 1.0 - 0.32 * r2;
  col *= vig;
  col += vec3(0.02, 0.014, 0.008) * smoothstep(0.9, 0.0, length(c - vec2(-0.55, 0.6))) * inside;   // faint reflection
  col = mix(vec3(0.02, 0.013, 0.008), col, inside);
  col += (h21(gl_FragCoord.xy) - 0.5) * 0.012;           // static glass noise
  outColor = vec4(col, 1.0);
}`;

export const fonts = ["Menlo"];

export async function setup(ctx, tokens, lib) {
  L = { fx: lib.shader(FRAG), titleTimes: TITLE_TIMES };
}

// ── grid drawing helpers (beam canvas: white = lit)
function put(g, lib, tokens, str, col, row, { b = NORM, dbl = false, inv = false, cjkSize, ink } = {}) {
  const cw = dbl ? CW * 2 : CW, ch = dbl ? CH * 2 : CH;
  let c = col;
  for (const s of lib.graphemes(str)) {
    const cjk = lib.isCJK(s), span = cjk ? 2 : 1;
    const x = X0 + c * CW, y = Y0 + row * CH;
    if (inv) { g.fillStyle = `rgba(255,255,255,${b})`; g.fillRect(x, y + 2, cw * span, ch - 4); }
    if (s !== " ") {
      g.fillStyle = ink || (inv ? "#000" : `rgba(255,255,255,${b})`);
      if (cjk) { lib.setFont(g, tokens, "zh", cjkSize || (dbl ? 86 : 46), { weight: 400 }); g.textAlign = "center"; g.fillText(s, x + cw * span / 2, y + ch * 0.8); }
      else { lib.setFont(g, tokens, "mono", dbl ? 80 : 40, { weight: b >= BOLD ? 700 : 400 }); g.textAlign = "center"; g.fillText(s, x + cw / 2, y + ch * 0.74); }
    }
    c += span * (dbl ? 2 : 1);
  }
  return c;
}
const typed = (lib, str, t, t0, cps) => lib.typewriter(str, t, { start: t0, cps });

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const g = lib.layer("crt_beam");
  g.fillStyle = "#000"; g.fillRect(0, 0, W, H); g.textBaseline = "alphabetic";
  if (t < TL.reOn) screen(g, t, tokens, lib); else endScreen(g, t, tokens, lib);
  // squeeze factors + brightness boost: power-on 0.05–0.25, power-off 4.0–4.2, dot until 4.36, power-on again 4.36–4.5
  let sx = 1, sy = 1, boost = 1;
  const on = (t0, t1) => { sx = 1; sy = lib.lerp(0.006, 1, lib.ease.outExpo(lib.seg(t, t0, t1))); boost = 1 + 2.4 * (1 - lib.seg(t, t0, t1 + 0.18)); };
  if (t < TL.on[0]) { boost = 0; }
  else if (t < 0.45) on(...TL.on);                                          // a full-width line that blooms open
  if (t >= TL.off && t < TL.reOn) {
    sy = lib.lerp(1, 0.004, lib.ease.inExpo(lib.seg(t, TL.off, TL.off + 0.1)));
    sx = lib.lerp(1, 0.006, lib.ease.inExpo(lib.seg(t, TL.off + 0.08, TL.dot)));
    boost = 1 + 2.2 * lib.seg(t, TL.off, TL.dot);
    if (t > TL.dot) boost = 3.2 * Math.exp(-(t - TL.dot) / 0.12);           // the dot's afterglow (≤ 0.16 s)
  }
  if (t >= TL.reOn) on(TL.reOn, TL.reOn + 0.14);
  const flick = 1 + 0.012 * lib.hashS(3, lib.frame(t));
  const img = L.fx.render(t, { u_sx: sx, u_sy: sy, u_boost: boost, u_flick: flick }, { u_tex0: g.canvas });
  ctx.drawImage(img, 0, 0);
  if (t >= TL.dot && t < TL.reOn) {                                         // keep the collapsed dot visible as a point
    const a = Math.exp(-(t - TL.dot) / 0.12);
    const gr = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, 26);
    gr.addColorStop(0, `rgba(255,227,163,${0.95 * a})`); gr.addColorStop(0.4, `rgba(255,176,0,${0.5 * a})`); gr.addColorStop(1, "rgba(255,176,0,0)");
    ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(W / 2, H / 2, 26, 0, lib.TAU); ctx.fill();
  }
}

// rows cleared line by line (top → bottom, 2 frames per double row) leave a phosphor afterglow
function afterglow(t, tClear) { return t < tClear ? 1 : Math.exp(-(t - tClear) / TAU_GLOW); }

function screen(g, t, tokens, lib) {
  if (t < TL.on[0]) return;
  const warm = 1 - lib.seg(t, TL.on[0], TL.on[0] + 0.25);                                   // the whole raster glows as the tube warms up
  if (warm > 0) { g.fillStyle = `rgba(255,255,255,${0.62 * warm})`; g.fillRect(X0 - 24, Y0 - 12, COLS * CW + 48, 19 * CH + 24); }
  // boot log at double size, machine speed; cleared row by row at 0.8 s
  BOOT.forEach((s, i) => {
    const a = afterglow(t, TL.clear + i * 0.05);
    if (a < 0.02) return;
    put(g, lib, tokens, typed(lib, s, t, TL.boot0 + i * TL.bootStag, 70), 0, i * 2, { b: NORM * a, dbl: true });
  });
  let cur = null;
  if (t >= TL.cmd) {                                                        // command line
    const s = typed(lib, "> title", t, TL.cmd, 26); put(g, lib, tokens, s, 0, 0); if (t < TL.title0) cur = [s.length, 0, false];
  }
  const tt = L.titleTimes, n = tt.filter((x) => x <= t).length;             // title: a human typing, double size
  if (t >= 1.2) { put(g, lib, tokens, lib.graphemes(lib.TITLE_EN).slice(0, n).join(""), 0, 1, { b: BOLD, dbl: true }); if (t < 2.3) cur = [n * 2, 1, true]; }
  const zh = t >= TL.ime[1] ? lib.TITLE_ZH : t >= TL.ime[0] ? "每一帧，" : "";   // Chinese: two IME commits
  if (zh) put(g, lib, tokens, zh, 0, 3, { b: BOLD, dbl: true });
  if (t >= 2.3 && t < TL.prompt) cur = [lib.graphemes(zh).length * 4, 3, true];
  // motif: an ASCII tree, output line by line at machine speed
  if (t >= TL.tree) put(g, lib, tokens, typed(lib, "$ tree film/", t, TL.tree, 80), 0, 6, { b: NORM });
  const P = Math.min(10, Math.max(0, Math.floor((t - TL.barStart) / TL.barStep)));   // draft render: 10 cells, 100 % at 3.6 s
  const pct = String(P * 10).padStart(3, " ");
  const tree = [
    ["film/", DIM], ["├── outline/        大纲", BOLD], ["│   └── brief.md", DIM], ["├── storyboard/     分镜", BOLD], ["│   └── shots.json", DIM],
    ["└── draft.mp4       初版  [" + "█".repeat(P) + "·".repeat(10 - P) + "] " + pct + "%", BOLD],
  ];
  tree.forEach(([s, b], i) => { if (t >= TL.treeLine + i * 0.08) put(g, lib, tokens, s, 0, 7 + i, { b }); });
  if (t >= TL.ready) put(g, lib, tokens, " READY ", 45, 12, { b: BOLD, inv: true });
  // render log: one new line every 0.4 s, scrolling (real frame numbers)
  if (t >= TL.log) {
    const k = Math.floor((t - TL.log) / 0.4), lines = [];
    for (let j = Math.max(0, k - 2); j <= k; j++) { const tj = TL.log + j * 0.4; lines.push(`[render] frame ${String(lib.frame(tj)).padStart(3, "0")}/150  ok`); }
    lines.forEach((s, i) => put(g, lib, tokens, s, 0, 14 + i + (3 - lines.length), { b: DIM }));
  }
  if (t >= TL.prompt) { put(g, lib, tokens, ">", 0, 17); cur = [2, 17, false, TL.prompt]; }
  if (cur) cursor(g, t, cur);
  if (t >= 0.3) {                                                           // status line, inverse video, real frame number
    const f = String(lib.frame(t)).padStart(3, "0");
    put(g, lib, tokens, ` TTY1  |  FRAME ${f}/150  |  crt-terminal`.padEnd(COLS, " "), 0, 18, { b: 0.58, inv: true });
  }
}

// end: the tube comes back on in inverse video with the style name
function endScreen(g, t, tokens, lib) {
  const { W, H } = lib;
  g.fillStyle = "rgba(255,255,255,0.5)"; g.fillRect(X0 - 24, Y0 - 12, COLS * CW + 48, 19 * CH + 24);
  g.fillStyle = "#000";
  const name = "CRT TERMINAL", cols = name.length * 2, c0 = Math.floor((COLS - cols) / 2);
  put(g, lib, tokens, name, c0, 7, { b: 1, dbl: true, ink: "#000" });
  put(g, lib, tokens, "CRT 终端", Math.floor((COLS - 16) / 2), 10, { b: 1, dbl: true, ink: "#000" });
}

function cursor(g, t, [col, row, dbl, since = 0]) {
  const cw = dbl ? CW * 2 : CW, ch = dbl ? CH * 2 : CH, x = X0 + col * CW, y = Y0 + row * CH;
  let a = 1;
  if (since) {                                   // blinking: 500 ms period; off-phase decays with the phosphor
    const ph = (t - since) % 0.5;
    a = ph < 0.25 ? 1 : Math.exp(-(ph - 0.25) / TAU_GLOW);
  }
  g.fillStyle = `rgba(255,255,255,${0.85 * a})`; g.fillRect(x + 2, y + 4, cw - 4, ch - 8);
}
