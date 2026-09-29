// crt-terminal swatch: everything is a real character on a fixed grid, lit by one amber phosphor.
// The scene draws a greyscale "beam" canvas (brightness only, glyphs snapped to 24 × 48 px cells; double-width,
// double-height lines use 48 × 96), then a CRT shader does barrel curvature, bloom, the P3 amber ramp, scanlines,
// vignette, frame-seeded flicker, the rounded tube mask and the power-on / power-off collapse.
//   0.0–0.22 power-on: dot → line → full raster
//   0.2–0.9  boot log types at machine speed (dim)
//   0.85–2.6 "> title" command, then the title typed by a human (uneven, pauses at spaces); Chinese commits
//            in two IME chunks
//   2.0–3.0  three box-drawn windows (outline → storyboard → draft) draw row by row; progress bars fill in steps;
//            the draft window turns inverse-video READY
//   4.0–4.4  power-off: raster collapses to a line, then to a dot; the dot's afterglow decays
// The status line shows the real frame number of the frame being rendered.

let L = null;
const CW = 24, CH = 48, X0 = 120, Y0 = 84, COLS = 70, ROWS = 19;
const DIM = 0.42, NORM = 0.78, BOLD = 1.0, TAU_GLOW = 0.12;

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
  // the human typing schedule for the title: seeded per-character delays, pauses at spaces (pure data)
  const chars = lib.graphemes(lib.TITLE_EN), times = []; let tt = 1.22;
  chars.forEach((ch, i) => { times.push(tt); tt += 0.034 + 0.03 * lib.hash(5, i) + (ch === " " ? 0.07 : 0); });
  L = { fx: lib.shader(FRAG), titleTimes: times, titleDone: tt };
}

// ── grid drawing helpers (beam canvas: white = lit)
function put(g, lib, tokens, str, col, row, { b = NORM, dbl = false, inv = false, cjkSize } = {}) {
  const cw = dbl ? CW * 2 : CW, ch = dbl ? CH * 2 : CH;
  let c = col;
  for (const s of lib.graphemes(str)) {
    const cjk = lib.isCJK(s), span = cjk ? 2 : 1;
    const x = X0 + c * CW, y = Y0 + row * CH;
    if (inv) { g.fillStyle = `rgba(255,255,255,${b})`; g.fillRect(x, y + 2, cw * span, ch - 4); }
    if (s !== " ") {
      g.fillStyle = inv ? "#000" : `rgba(255,255,255,${b})`;
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
  screen(g, t, tokens, lib);
  // power-on (0–0.22) and power-off (4.0–4.36) as squeeze factors + brightness boost
  let sx = 1, sy = 1, boost = 1;
  if (t < 0.22) { sx = lib.lerp(0.004, 1, lib.ease.outExpo(lib.seg(t, 0.03, 0.12))); sy = lib.lerp(0.004, 1, lib.ease.outExpo(lib.seg(t, 0.1, 0.22))); boost = t < 0.03 ? 0 : 1 + 1.5 * (1 - lib.seg(t, 0.03, 0.22)); }
  if (t >= 4.0) {
    sy = lib.lerp(1, 0.004, lib.ease.inExpo(lib.seg(t, 4.0, 4.18)));
    sx = lib.lerp(1, 0.006, lib.ease.inExpo(lib.seg(t, 4.16, 4.36)));
    boost = 1 + 2.2 * lib.seg(t, 4.0, 4.36);
    if (t > 4.36) boost = 3.2 * Math.exp(-(t - 4.36) / 0.22);            // the dot's afterglow
  }
  const flick = 1 + 0.012 * lib.hashS(3, lib.frame(t));
  const img = L.fx.render(t, { u_sx: sx, u_sy: sy, u_boost: boost, u_flick: flick }, { u_tex0: g.canvas });
  ctx.drawImage(img, 0, 0);
  if (t >= 4.36) {                                                       // keep the collapsed dot visible as a point
    const a = Math.exp(-(t - 4.36) / 0.22);
    const gr = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, 26);
    gr.addColorStop(0, `rgba(255,227,163,${0.95 * a})`); gr.addColorStop(0.4, `rgba(255,176,0,${0.5 * a})`); gr.addColorStop(1, "rgba(255,176,0,0)");
    ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(W / 2, H / 2, 26, 0, lib.TAU); ctx.fill();
  }
}

function screen(g, t, tokens, lib) {
  if (t < 0.03) return;
  // boot log, machine speed (12–25 ms per character), dim
  const boot = ["OVH-TTY 0.8  READY", "MEM 65536K ......... OK", "STYLE crt-terminal .. OK", "PHOSPHOR P3 AMBER  TAU 0.12S"];
  boot.forEach((s, i) => put(g, lib, tokens, typed(lib, s, t, 0.2 + i * 0.12, 60), 0, i, { b: DIM }));
  // command line
  const cmd = "> title";
  let cur = null;
  if (t >= 0.85) { const s = typed(lib, cmd, t, 0.85, 22); put(g, lib, tokens, s, 0, 5); if (t < 1.22) cur = [s.length, 5, false]; }
  // title: human typing on a double-width, double-height line
  const tt = L.titleTimes, n = tt.filter((x) => x <= t).length;
  if (t >= 1.2) { put(g, lib, tokens, lib.graphemes(lib.TITLE_EN).slice(0, n).join(""), 0, 6, { b: BOLD, dbl: true }); if (t < 2.3) cur = [n * 2, 6, true]; }
  // Chinese: two IME commits
  const zh = t >= 2.52 ? lib.TITLE_ZH : t >= 2.32 ? "每一帧，" : "";
  if (zh) { put(g, lib, tokens, zh, 0, 8, { b: BOLD, dbl: true }); }
  if (t >= 2.3 && t < 2.62) cur = [lib.graphemes(zh).length * 4, 8, true];
  // three windows
  for (let k = 0; k < 3; k++) win(g, t, tokens, lib, k);
  // idle prompt with a blinking block cursor (afterglow on every switch-off)
  if (t >= 2.62) { put(g, lib, tokens, ">", 0, 17); cur = [2, 17, false, 2.62]; }
  if (cur) cursor(g, t, cur);
  // status line: inverse video, real frame number
  if (t >= 0.3) {
    const f = String(lib.frame(t)).padStart(3, "0");
    const s = ` TTY1  |  FRAME ${f}/150  |  crt-terminal`.padEnd(COLS, " ");
    put(g, lib, tokens, s, 0, 18, { b: 0.58, inv: true });
  }
}

function cursor(g, t, [col, row, dbl, since = 0]) {
  const cw = dbl ? CW * 2 : CW, ch = dbl ? CH * 2 : CH, x = X0 + col * CW, y = Y0 + row * CH;
  let a = 1;
  if (since) {                                   // blinking: 530 ms period; off-phase decays with the phosphor
    const ph = (t - since) % 0.53;
    a = ph < 0.265 ? 1 : Math.exp(-(ph - 0.265) / TAU_GLOW);
  }
  g.fillStyle = `rgba(255,255,255,${0.85 * a})`; g.fillRect(x + 2, y + 4, cw - 4, ch - 8);
}

function win(g, t, tokens, lib, k) {
  const t0 = 2.0 + k * 0.18, w = 20, c0 = 2 + k * 23, r0 = 11;
  if (t < t0) return;
  const rows = Math.min(6, Math.floor((t - t0) * 30) + 1);               // border draws one row per frame
  const bar = "─".repeat(w - 2);
  const lines = ["┌" + bar + "┐", "│" + " ".repeat(w - 2) + "│", "│" + " ".repeat(w - 2) + "│", "│" + " ".repeat(w - 2) + "│", "│" + " ".repeat(w - 2) + "│", "└" + bar + "┘"];
  for (let r = 0; r < rows; r++) put(g, lib, tokens, lines[r], c0, r0 + r, { b: NORM });
  if (rows < 6) return;
  const name = lib.MOTIF[k].en.toUpperCase();
  put(g, lib, tokens, typed(lib, name, t, t0 + 0.2, 60), c0 + 2, r0 + 1, { b: BOLD });
  if (t >= t0 + 0.26) put(g, lib, tokens, lib.MOTIF[k].zh, c0 + 2, r0 + 2, { b: BOLD });
  const p = Math.min(10, Math.max(0, Math.floor((t - (t0 + 0.28)) / 0.03)));  // progress in whole cells
  if (t >= t0 + 0.28) put(g, lib, tokens, "[" + "█".repeat(p) + "·".repeat(10 - p) + "]", c0 + 2, r0 + 3, { b: NORM });
  if (p >= 10) {
    if (k === 2) put(g, lib, tokens, " READY ", c0 + 2, r0 + 4, { b: BOLD, inv: true });
    else put(g, lib, tokens, "OK", c0 + 2, r0 + 4, { b: BOLD });
    if (k < 2) put(g, lib, tokens, "─►", c0 + w, r0 + 3, { b: NORM });
  }
}
