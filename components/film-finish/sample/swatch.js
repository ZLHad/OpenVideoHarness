// film-finish's sample: a night road drawn cleanly in code (flat sky, a ground, a huge structure on the horizon, lamps,
// three far red lights, a near post), the camera drifting. The pass comes in a layer at a time: air (from a depth picture
// drawn alongside), lens, light, grain; then the clean picture and the finished one side by side. The labels are drawn
// after the pass, as text that must be read should be. Render: bin/vh components sample film-finish.
import { state, canvas, defaults } from "../../components/film-finish/component.js";

// the scene in world units: x across, z away from the camera (1 near … 40 far); y up from the ground
const LAMPS = [-14, -7, 0, 7, 14, 21].map((x, i) => ({ x, z: 6 + i * 3.2 }));
const REDS = [{ x: -9, z: 34 }, { x: -6.5, z: 35 }, { x: 11, z: 33 }];

function project(x, y, z, cam) {   // a pinhole: horizon at 58 % of the height, focal 900 px
  const s = 900 / z;
  return [960 + (x - cam) * s, 0.58 * 1080 - y * s, s];
}

// mode "color" paints the scene; mode "depth" paints each thing in grey by its distance (white = far)
function paint(x, mode, cam) {
  const depth = mode === "depth", g = (z) => { const v = Math.round(255 * Math.min(1, (z - 1) / 39)); return `rgb(${v},${v},${v})`; };
  // sky and ground
  if (depth) { x.fillStyle = "#fff"; x.fillRect(0, 0, 1920, 1080); }
  else { const sk = x.createLinearGradient(0, 0, 0, 630); sk.addColorStop(0, "#0b1424"); sk.addColorStop(1, "#22324a"); x.fillStyle = sk; x.fillRect(0, 0, 1920, 1080); }
  const gr = x.createLinearGradient(0, 626, 0, 1080);
  if (depth) { gr.addColorStop(0, "#fff"); gr.addColorStop(1, "#000"); } else { gr.addColorStop(0, "#1d2532"); gr.addColorStop(1, "#0d1118"); }
  x.fillStyle = gr; x.fillRect(0, 626, 1920, 454);
  // the structure on the horizon: a tall dark slab with a ring, far away
  const [sx, sy, ss] = project(4, 0, 40, cam * 0.15);
  x.fillStyle = depth ? g(40) : "#141c2a";
  x.beginPath(); x.moveTo(sx - 9 * ss, sy); x.lineTo(sx - 5 * ss, sy - 26 * ss); x.lineTo(sx + 6 * ss, sy - 30 * ss); x.lineTo(sx + 10 * ss, sy); x.closePath(); x.fill();
  x.lineWidth = 1.2 * ss; x.strokeStyle = depth ? g(40) : "#1b2638"; x.beginPath(); x.ellipse(sx, sy - 16 * ss, 16 * ss, 4 * ss, -0.1, 0, Math.PI * 2); x.stroke();
  // far red lights
  for (const r of REDS) { const [px, py, s] = project(r.x, 0.6, r.z, cam); x.fillStyle = depth ? g(r.z) : "#ff3b2a"; x.beginPath(); x.arc(px, py, Math.max(2, 0.22 * s), 0, Math.PI * 2); x.fill(); }
  // lamps, far to near: a pole and a bright warm head
  for (const L of [...LAMPS].sort((a, b) => b.z - a.z)) {
    const [px, py, s] = project(L.x, 0, L.z, cam), top = py - 4.2 * s;
    x.fillStyle = depth ? g(L.z) : "#2a313c"; x.fillRect(px - 0.06 * s, top, 0.12 * s, 4.2 * s);
    if (!depth) {   // a pool of light on the ground: a radial gradient squashed into an ellipse, soft to its edge
      x.save(); x.translate(px, py); x.scale(1, 0.22);
      const pool = x.createRadialGradient(0, 0, 0, 0, 0, 2.4 * s); pool.addColorStop(0, "rgba(255,196,120,0.30)"); pool.addColorStop(1, "rgba(255,196,120,0)");
      x.fillStyle = pool; x.beginPath(); x.arc(0, 0, 2.4 * s, 0, Math.PI * 2); x.fill(); x.restore();
    }
    x.fillStyle = depth ? g(L.z) : "#fff6e2"; x.beginPath(); x.ellipse(px, top, 0.42 * s, 0.18 * s, 0, 0, Math.PI * 2); x.fill();
  }
  // a near post at the right, cut by the frame
  const [nx, ny, ns] = project(3.2, 0, 2.2, cam);
  x.fillStyle = depth ? g(2.2) : "#30353d"; x.fillRect(nx, ny - 3 * ns, 0.18 * ns, 3 * ns);
  if (!depth) { x.fillStyle = "#e9eef5"; x.fillRect(nx + 0.03 * ns, ny - 3 * ns, 0.05 * ns, 3 * ns); }   // a lit edge
}

// the layers' times: each comes in over 0.5 s; from 3.6 s the clean picture on the left, the finished on the right
const ON = { air: 1.0, lens: 1.8, light: 2.6, grain: 3.1 }, SPLIT = 3.6;
const ramp = (t, a) => Math.min(1, Math.max(0, (t - a) / 0.5));
// the sample turns the defaults up a little, so a contact sheet at 480 px still shows each layer
const P = { ...defaults, haze: 0.4, hazeColor: "#3a4a62", aberration: 0.0022, vignette: 0.32, bloom: 0.3, halation: 0.36, threshold: 0.7, grain: 0.04 };
const ZOOM = 4.3;   // from 4.3 s: a 3x crop round the nearest lamp head, clean left, finished right

export function renderAt(t, ctx, tokens, lib) {
  const cam = -1.2 + 0.6 * t;   // a slow drift to the right
  const src = lib.offscreen("ff_src", (x) => paint(x, "color", cam));
  const depth = lib.offscreen("ff_depth", (x) => paint(x, "depth", cam));
  const a = ramp(t, ON.air), l = ramp(t, ON.lens), g = ramp(t, ON.light), n = ramp(t, ON.grain);
  const params = { ...P, haze: P.haze * a, aberration: P.aberration * l, vignette: P.vignette * l, bloom: P.bloom * g, halation: P.halation * g, grain: P.grain * n };
  const fin = lib.offscreen("ff_fin", (x) => canvas(x, state(params, t), src, { depth }));
  if (t < ZOOM) {
    ctx.drawImage(fin, 0, 0, 1920, 1080);
    if (t >= SPLIT) {   // the clean picture back over the left half, a hairline between
      const w = 960 * Math.min(1, (t - SPLIT) / 0.4);
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, w, 1080); ctx.clip(); ctx.drawImage(src, 0, 0, 1920, 1080); ctx.restore();
      ctx.fillStyle = "rgba(239,231,218,0.8)"; ctx.fillRect(w - 1, 0, 2, 1080);
    }
  } else {   // the same crop of both, side by side, nearest-neighbour so the grain stays grain
    const [hx, hy, hs] = project(LAMPS[2].x, 4.2, LAMPS[2].z, cam), cx = hx - 160, cy = hy - 90;
    ctx.fillStyle = "#0c0a09"; ctx.fillRect(0, 0, 1920, 1080); ctx.imageSmoothingEnabled = false;
    ctx.drawImage(src, cx, cy, 320, 360, 0, 0, 956, 1080);
    ctx.drawImage(fin, cx, cy, 320, 360, 964, 0, 956, 1080);
    ctx.imageSmoothingEnabled = true; void hs;
  }
  // labels, after the pass: which layers are on
  const fg = lib.color(tokens, "fg"), dim = lib.color(tokens, "extra.1");
  lib.setFont(ctx, tokens, "zh", 44, { weight: 600 });
  const names = [["空气", a], ["镜头", l], ["光", g], ["颗粒", n]];
  let x0 = 120;
  for (const [s, v] of names) { ctx.fillStyle = v > 0.5 ? fg : dim; ctx.fillText(s, x0, 1000); x0 += ctx.measureText(s).width + 48; }
  if (t >= SPLIT) { ctx.fillStyle = fg; ctx.fillText(t >= ZOOM ? "原样 · 放大 3×" : "原样", 120, 110); ctx.textAlign = "right"; ctx.fillText("收尾后", 1800, 110); ctx.textAlign = "left"; }
}
