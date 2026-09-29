// risograph swatch: plates as narrative.
// One "plate canvas" holds ink densities: R = blue, G = fluorescent pink, B = yellow. source-over = knockout,
// "lighter" = overprint. A print shader turns each plate into screen-fixed halftone (blue 15°, yellow 0°, pink 75°),
// misregisters it (fixed per shot, a kick when the plate arrives), adds ink grain, pinholes and feed streaks, gates each
// plate behind a roller sweep, and multiplies the inks on warm paper.
//   0.1–0.6  blue plate rolls on: registration crosshairs, ground band
//   0.8–1.9  title printed on the blue plate by a local roller; Chinese follows
//   2.0–2.9  outline (blue only) → storyboard (+ yellow plate rolls on) → draft (+ pink plate: full overprint);
//            the pink plate also double-hits the title
//   4.0–4.45 overprint-grow: a pink disc swells out of the draft and turns everything under it into mixes
//   4.5      the print cuts (prints don't fade) to the end sheet: name printed in blue over solid pink

let L = null;
const PAPER = "#F4EFE4";
const FRAG = `
uniform vec2 u_ob, u_op, u_oy;          // plate offsets (px, y down)
uniform vec3 u_gate;                    // roller x position per plate (blue, pink, yellow), px
uniform float u_seed, u_period;
float h21(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float vnoise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), f.x), f.y); }
vec2 sh(vec2 o){ return vec2(o.x, -o.y) / u_res; }
float plate(int ch, vec2 off, float gate, float ang, vec2 px){
  vec4 s = texture(u_tex0, v_uv - sh(off));
  float d = ch == 0 ? s.r : (ch == 1 ? s.g : s.b);
  float x = v_uv.x * u_res.x;
  if (x > gate) return 0.0;
  d = min(1.0, d + 0.22 * d * exp(-(gate - x) / 38.0));        // heavier ink at the roller's leading edge
  float streak = vnoise(vec2(x / 900.0, (u_res.y - v_uv.y * u_res.y) / 9.0 + float(ch) * 7.0));
  float k = 0.82 + 0.12 * streak + 0.06 * vnoise(v_uv * 3.0 + float(ch));
  float c = cos(ang), sn = sin(ang);
  vec2 q = mat2(c, -sn, sn, c) * (v_uv * u_res) / u_period;
  vec2 cell = floor(q), f = fract(q) - 0.5;
  float n = h21(cell + float(ch) * 31.0);
  if (h21(cell + u_seed * 1.37 + float(ch)) < 0.35) n = h21(cell + u_seed * 5.1 + float(ch) * 3.0);   // 35 % of dots re-roll per print
  if (d >= 0.9) { float pin = vnoise((v_uv * u_res) / 3.0 + float(ch) * 11.0); return pin > 0.9 ? 0.0 : k; }
  if (d < 0.02) return 0.0;
  float r = sqrt(d) * 0.74 + (n - 0.5) * 0.16, aa = 0.9 / u_period;
  return k * (1.0 - smoothstep(r - aa, r + aa, length(f)));
}
void main(){
  vec2 px = v_uv * u_res;
  float b = plate(0, u_ob, u_gate.x, radians(15.0), px);
  float p = plate(1, u_op, u_gate.y, radians(75.0), px);
  float y = plate(2, u_oy, u_gate.z, radians(0.0), px);
  vec3 paper = vec3(0.957, 0.937, 0.894) * (0.99 + 0.02 * vnoise(px / 5.0));
  vec3 col = paper * mix(vec3(1.0), vec3(0.0, 0.47, 0.75), b) * mix(vec3(1.0), vec3(1.0, 0.282, 0.69), p) * mix(vec3(1.0), vec3(1.0, 0.91, 0.0), y);
  outColor = vec4(col, 1.0);
}`;

export async function setup(ctx, tokens, lib) {
  L = { fx: lib.shader(FRAG), slots: lib.slots(3, { area: lib.SAFE.title, y: 620 }) };
}

const ROLL = { blue: [0.1, 0.6], yellow: [2.08, 2.45], pink: [2.48, 2.85] };
const kick = (t, t0, A = 10) => (t < t0 ? 0 : A * Math.exp(-(t - t0) / 0.08) * Math.cos(2 * Math.PI * 6 * (t - t0)));
const ink = (b, p, y) => `rgb(${Math.round(b * 255)},${Math.round(p * 255)},${Math.round(y * 255)})`;

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const pl = lib.layer("riso_plates");
  pl.fillStyle = "#000"; pl.fillRect(0, 0, W, H);
  if (t < 4.5) mainSheet(pl, t, tokens, lib); else endSheet(pl, t, tokens, lib);
  crosshairs(pl, lib);
  const gate = (r) => lib.lerp(-60, W + 60, lib.tween(t, r[0], r[1], lib.ease.inOutSine));
  const cut = t >= 4.5;
  const gb = cut ? W + 60 : gate(ROLL.blue), gy = cut ? W + 60 : gate(ROLL.yellow), gp = cut ? W + 60 : gate(ROLL.pink);
  const kb = kick(t, 0.1) + kick(t, 4.5), ky = kick(t, 2.08), kp = kick(t, 2.48) + kick(t, 4.5, 7);
  const img = L.fx.render(t, {
    u_ob: [0 + kb, 0], u_oy: [3 + ky, -2 - ky * 0.5], u_op: [-3 - kp, 2 + kp * 0.6],
    u_gate: [gb, gp, gy], u_seed: Math.floor(t * 12 + 1e-6), u_period: 11,
  }, { u_tex0: pl.canvas });
  ctx.drawImage(img, 0, 0);
}

function crosshairs(pl, lib) {                        // on all three plates: they misregister visibly
  pl.save(); pl.globalCompositeOperation = "lighter"; pl.strokeStyle = ink(1, 1, 1); pl.lineWidth = 3;
  for (const [x, y] of [[132, 96], [1788, 96], [132, 984], [1788, 984]]) {
    pl.beginPath(); pl.arc(x, y, 18, 0, lib.TAU); pl.moveTo(x - 32, y); pl.lineTo(x + 32, y); pl.moveTo(x, y - 32); pl.lineTo(x, y + 32); pl.stroke();
  }
  pl.restore();
}

// local roller for text: reveals left → right between x0 and x1 over [a, b]
function rolled(pl, lib, t, a, b, x0, x1, draw) {
  const u = lib.tween(t, a, b, lib.ease.inOutSine);
  if (u <= 0) return;
  pl.save(); pl.beginPath(); pl.rect(0, 0, lib.lerp(x0, x1, u), lib.H); pl.clip(); draw(); pl.restore();
}

function mainSheet(pl, t, tokens, lib) {
  const { W } = lib;
  // ground band: blue 22 % tint
  pl.save(); pl.globalCompositeOperation = "lighter"; pl.fillStyle = ink(0.22, 0, 0); pl.fillRect(0, 1004, W, 76); pl.restore();
  // sun: yellow solid + pink 45 % tint (two plates, one tint) — appears with the yellow / pink rollers
  pl.save(); pl.globalCompositeOperation = "lighter"; pl.fillStyle = ink(0, 0, 1); pl.beginPath(); pl.arc(1690, 390, 140, 0, lib.TAU); pl.fill();
  pl.fillStyle = ink(0, 0.45, 0); pl.beginPath(); pl.arc(1690, 390, 140, 0, lib.TAU); pl.fill(); pl.restore();

  // title on the blue plate + pink double-hit (only visible once the pink plate rolls on)
  lib.setFont(pl, tokens, "display", 118, { weight: 700 });
  const lay = lib.layoutText(pl, lib.TITLE_EN, { x: 192, y: 250, tracking: -0.01 * 118 });
  pl.save(); pl.globalCompositeOperation = "lighter";
  rolled(pl, lib, t, 0.82, 1.5, 150, lay.x1 + 40, () => { pl.fillStyle = ink(1, 0, 0); lib.drawGlyphs(pl, lay); });
  pl.fillStyle = ink(0, 1, 0); pl.save(); pl.translate(9, 7); lib.drawGlyphs(pl, lay); pl.restore();
  lib.setFont(pl, tokens, "zh", 66, { weight: 600 });
  const zl = lib.layoutText(pl, lib.TITLE_ZH, { x: 196, y: 352, tracking: 0.06 * 66 });
  rolled(pl, lib, t, 1.35, 1.9, 150, zl.x1 + 40, () => { pl.fillStyle = ink(1, 0, 0); lib.drawGlyphs(pl, zl); });
  pl.restore();

  // motif: plates as story
  L.slots.forEach((s, k) => {
    const tq = lib.step(t, 12), t0 = 2.0 + k * 0.15;
    if (tq < t0) return;
    const sc = lib.clamp(lib.spring(tq - t0 + 1 / 12, { stiffness: 260, damping: 20 }), 0, 1.3);
    pl.save(); pl.translate(s.x, s.y); pl.scale(sc, sc); pl.globalCompositeOperation = "lighter";
    if (k === 0) {                                  // outline: one plate (blue), paper knocked out as three lines
      pl.fillStyle = ink(1, 0, 0); pl.beginPath(); pl.roundRect(-120, -120, 240, 240, 34); pl.fill();
      pl.globalCompositeOperation = "source-over"; pl.fillStyle = "#000";
      for (let r = 0; r < 3; r++) { pl.beginPath(); pl.roundRect(-76, -58 + r * 44, r === 2 ? 96 : 152, 20, 10); pl.fill(); }
    } else if (k === 1) {                           // storyboard: + yellow plate (solid) under a blue 55 % tint → green mix
      pl.fillStyle = ink(0, 0, 1); pl.beginPath(); pl.arc(38, 30, 118, 0, lib.TAU); pl.fill();
      pl.fillStyle = ink(0.55, 0, 0); pl.beginPath(); pl.roundRect(-128, -120, 200, 200, 26); pl.fill();
    } else {                                        // draft: all three plates overprint, play triangle knocked out
      pl.fillStyle = ink(1, 0, 0); pl.beginPath(); pl.arc(-44, 32, 104, 0, lib.TAU); pl.fill();
      pl.fillStyle = ink(0, 1, 0); pl.beginPath(); pl.arc(44, 32, 104, 0, lib.TAU); pl.fill();
      pl.fillStyle = ink(0, 0, 1); pl.beginPath(); pl.arc(0, -46, 104, 0, lib.TAU); pl.fill();
      pl.globalCompositeOperation = "source-over"; pl.fillStyle = "#000";
      pl.beginPath(); pl.moveTo(-22, -24); pl.lineTo(38, 8); pl.lineTo(-22, 40); pl.closePath(); pl.fill();
    }
    pl.restore();
    // labels on the blue plate
    if (tq >= t0 + 0.1) {
      pl.save(); pl.globalCompositeOperation = "lighter"; pl.fillStyle = ink(1, 0, 0);
      lib.setFont(pl, tokens, "display", 42, { weight: 700 }); lib.drawText(pl, lib.MOTIF[k].en, s.x, 830, { align: "center" });
      lib.setFont(pl, tokens, "zh", 54, { weight: 600 }); lib.drawText(pl, lib.MOTIF[k].zh, s.x, 904, { align: "center", tracking: 0.12 * 54 });
      pl.restore();
    }
  });

  // overprint-grow: a pink disc swells out of the draft and covers the sheet
  const g = lib.tween(t, 4.0, 4.45, lib.ease.inCubic);
  if (g > 0) { pl.save(); pl.globalCompositeOperation = "lighter"; pl.fillStyle = ink(0, 1, 0); pl.beginPath(); pl.arc(L.slots[2].x, L.slots[2].y, 60 + 2300 * g, 0, lib.TAU); pl.fill(); pl.restore(); }
}

function endSheet(pl, t, tokens, lib) {
  const { W, H } = lib;
  pl.save(); pl.globalCompositeOperation = "lighter"; pl.fillStyle = ink(0, 1, 0); pl.fillRect(0, 0, W, H);
  lib.setFont(pl, tokens, "display", 210, { weight: 700 });
  const lay = lib.layoutText(pl, "RISOGRAPH", { x: W / 2, y: 590, align: "center", tracking: 0.02 * 210 });
  rolled(pl, lib, t, 4.52, 4.8, lay.x0 - 30, lay.x1 + 30, () => { pl.fillStyle = ink(1, 0, 0); lib.drawGlyphs(pl, lay); });
  lib.setFont(pl, tokens, "zh", 72, { weight: 600 });
  const zl = lib.layoutText(pl, "孔版印刷", { x: W / 2, y: 700, align: "center", tracking: 0.3 * 72 });
  rolled(pl, lib, t, 4.6, 4.85, zl.x0 - 30, zl.x1 + 30, () => { pl.fillStyle = ink(1, 0, 0); lib.drawGlyphs(pl, zl); });
  pl.restore();
}
