// Catalog: a visual test card for lib.js (not a style, not the content spec). Render it after changing lib.js:
//   styles/_swatch/render.sh catalog --draft   → styles/_swatch/out/catalog/sheet.png
// 0.0–2.4 s: one labelled cell per helper. 2.4–5.0 s: the transitions, full frame (wipe, iris, whip, cut).

let FX = null, CELLS = null;

const SHADER = `
float h(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3.0-2.0*f);
  return mix(mix(h(i), h(i+vec2(1,0)), u.x), mix(h(i+vec2(0,1)), h(i+vec2(1,1)), u.x), u.y); }
void main(){
  vec2 p = v_uv * vec2(u_res.x / u_res.y, 1.0) * 4.0;
  float v = n(p + vec2(u_time * 0.8, 0.0)) * 0.6 + n(p * 2.3 - u_time * 0.5) * 0.4;
  vec3 a = vec3(0.10, 0.12, 0.30), b = vec3(0.95, 0.55, 0.20);
  outColor = vec4(mix(a, b, smoothstep(0.35, 0.75, v)), 1.0);
}`;

export async function setup(ctx, tokens, lib) {
  FX = lib.shader(SHADER, { width: 480, height: 300 });
  const A = lib.SAFE.action, cols = 4, rows = 3, gx = 24, gy = 56;
  const cw = (A.w - gx * (cols - 1)) / cols, ch = (A.h - 40 - gy * rows) / rows;
  const names = ["grain", "paper", "halftone", "scanlines", "vignette", "inkBleed", "roughen", "rgbSplit",
    "scramble · typewriter", "spring · bezier", "wobblePath · strokePartial", "shader (WebGL2)"];
  CELLS = names.map((name, i) => ({ name, x: A.x0 + (i % cols) * (cw + gx), y: A.y0 + 40 + Math.floor(i / cols) * (ch + gy) + gy - 16, w: cw, h: ch }));
}

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const scene = (label, bg) => (x) => {
    x.fillStyle = bg; x.fillRect(0, 0, lib.W, lib.H);
    lib.setFont(x, tokens, "display", 220); x.fillStyle = C("ink");
    lib.drawText(x, label, lib.W / 2, lib.H / 2 + 80, { align: "center" });
    lib.setFont(x, tokens, "mono", 28); lib.drawText(x, "lib transitions", lib.W / 2, lib.H / 2 + 170, { align: "center" });
  };
  const grid = (x) => cells(x, Math.min(t, 2.4), tokens, lib);
  if (t < 2.5) return grid(ctx);
  if (t < 3.2) return lib.wipe(ctx, lib.seg(t, 2.5, 3.1), grid, scene("wipe", C("a")), { angle: 20, soft: 80 });
  if (t < 3.9) return lib.iris(ctx, lib.seg(t, 3.2, 3.8), scene("wipe", C("a")), scene("iris", C("b")), { mode: "open", feather: 30 });
  if (t < 4.6) return lib.whip(ctx, lib.seg(t, 3.9, 4.5), scene("iris", C("b")), scene("whip", C("c")), { dir: [-1, 0], duration: 0.6 });
  lib.cut(ctx, t >= 4.7 ? 1 : 0, scene("whip", C("c")), scene("cut", C("d")));
}

function cells(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  ctx.fillStyle = C("bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  lib.setFont(ctx, tokens, "mono", 26); ctx.fillStyle = C("ink");
  lib.drawText(ctx, `lib.js catalog · t ${t.toFixed(2)}`, lib.SAFE.action.x0, lib.SAFE.action.y0 + 28);
  for (const c of CELLS) {
    ctx.save();
    ctx.beginPath(); ctx.rect(c.x, c.y, c.w, c.h); ctx.clip();
    ctx.fillStyle = "#808080"; ctx.fillRect(c.x, c.y, c.w, c.h);
    try { draw(c, ctx, t, tokens, lib); } finally { ctx.restore(); }
    ctx.strokeStyle = C("ink"); ctx.lineWidth = 2; ctx.strokeRect(c.x, c.y, c.w, c.h);
    lib.setFont(ctx, tokens, "mono", 20); ctx.fillStyle = C("ink");
    lib.drawText(ctx, c.name, c.x, c.y - 10);
  }
}

function draw(c, ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), cx = c.x + c.w / 2, cy = c.y + c.h / 2;
  const blob = (x) => { x.fillStyle = "#111"; x.beginPath(); x.arc(cx, cy, 70 + 20 * Math.sin(t * 3), 0, lib.TAU); x.fill();
    lib.setFont(x, tokens, "zh", 64, { weight: 600 }); lib.drawText(x, "墨 ink", cx, cy + c.h * 0.36, { align: "center" }); };
  switch (c.name) {
    case "grain": lib.grain(ctx, t, { amount: 0.35, fps: 24, seed: 3 }); break;
    case "paper": lib.paper(ctx, { tone: "#efe6d2", blotch: 0.08, fiber: 1, seed: 2 }); break;
    case "halftone": {
      const src = lib.offscreen("cat_ht", (x) => {
        const g = x.createLinearGradient(c.x, 0, c.x + c.w, 0); g.addColorStop(0, "#fff"); g.addColorStop(1, "#000");
        x.fillStyle = g; x.fillRect(c.x, c.y, c.w, c.h); x.fillStyle = "#000"; x.beginPath(); x.arc(cx - 60, cy, 60, 0, lib.TAU); x.fill(); });
      ctx.fillStyle = "#f4f0e6"; ctx.fillRect(c.x, c.y, c.w, c.h);
      lib.halftone(ctx, src, { cell: 14, angle: 15 + t * 10, color: "#1a1a1a", rect: c }); break;
    }
    case "scanlines": {
      const g = ctx.createLinearGradient(c.x, c.y, c.x, c.y + c.h); g.addColorStop(0, "#1ee07f"); g.addColorStop(1, "#063");
      ctx.fillStyle = g; ctx.fillRect(c.x, c.y, c.w, c.h);
      lib.scanlines(ctx, t, { spacing: 5, alpha: 0.45, roll: 20, flicker: 0.2 }); break;
    }
    case "vignette": ctx.fillStyle = "#e8d9b8"; ctx.fillRect(c.x, c.y, c.w, c.h); lib.vignette(ctx, { strength: 0.9, inner: 0.05, cx, cy }); break;
    case "inkBleed": ctx.fillStyle = "#f3efe4"; ctx.fillRect(c.x, c.y, c.w, c.h);
      lib.inkBleed(ctx, blob, { spread: 1 + 3 * lib.seg(t, 0, 2), rough: 1.2, seed: lib.step(t, 8) * 8 + 1 }); break;
    case "roughen": ctx.fillStyle = "#f3efe4"; ctx.fillRect(c.x, c.y, c.w, c.h);
      lib.roughen(ctx, (x) => { x.fillStyle = "#c0392b"; x.fillRect(cx - 120, cy - 70, 240, 140); }, { amount: 10, seed: lib.step(t, 6) + 1 }); break;
    case "rgbSplit": {
      const src = lib.offscreen("cat_rgb", (x) => { x.fillStyle = "#fff"; lib.setFont(x, tokens, "display", 110); lib.drawText(x, "RGB", cx, cy + 40, { align: "center" }); });
      const k = 6 + 6 * Math.sin(t * 4); lib.rgbSplit(ctx, src, { r: [k, 0], g: [0, 0], b: [-k, 0] }); break;
    }
    case "scramble · typewriter": {
      ctx.fillStyle = "#101418"; ctx.fillRect(c.x, c.y, c.w, c.h);
      lib.setFont(ctx, tokens, "mono", 34); ctx.fillStyle = "#7dff9b";
      lib.drawText(ctx, lib.scramble("DECODE ME", t, { start: 0.2, stagger: 0.06, settle: 0.5, rate: 15, seed: 4 }), c.x + 24, c.y + 70);
      lib.setFont(ctx, tokens, "zh", 40, { weight: 600 });
      lib.drawText(ctx, lib.scramble(lib.TITLE_ZH, t, { start: 0.6, stagger: 0.08, settle: 0.4, rate: 10, seed: 9 }), c.x + 24, c.y + 150);
      lib.setFont(ctx, tokens, "mono", 28); ctx.fillStyle = "#ffffff";
      lib.drawText(ctx, lib.typewriter(lib.TITLE_EN, t, { start: 0.3, cps: 12 }) + (lib.frame(t) % 16 < 8 ? "▌" : ""), c.x + 24, c.y + 220);
      break;
    }
    case "spring · bezier": {
      ctx.fillStyle = "#fbfaf7"; ctx.fillRect(c.x, c.y, c.w, c.h);
      const curves = [["#1b1b1f", (u) => lib.spring(u * 0.8, { w: 14, zeta: 1 })], ["#e4572e", (u) => lib.spring(u * 0.8, { w: 14, zeta: 0.6 })],
        ["#2a7de1", (u) => lib.spring(u * 0.8, { stiffness: 170, damping: 26 })], ["#23a26d", lib.ease.outExpo], ["#9b59b6", lib.ease.inOutCubic]];
      const X = (u) => c.x + 20 + u * (c.w - 40), Y = (v) => c.y + c.h - 30 - v * (c.h - 80);
      ctx.lineWidth = 3;
      for (const [col, f] of curves) { ctx.strokeStyle = col; ctx.beginPath(); for (let i = 0; i <= 60; i++) { const u = i / 60; i ? ctx.lineTo(X(u), Y(f(u))) : ctx.moveTo(X(u), Y(f(u))); } ctx.stroke();
        const u = lib.fract(t / 2); ctx.fillStyle = col; ctx.beginPath(); ctx.arc(X(u), Y(f(u)), 6, 0, lib.TAU); ctx.fill(); }
      break;
    }
    case "wobblePath · strokePartial": {
      ctx.fillStyle = "#fbfaf7"; ctx.fillRect(c.x, c.y, c.w, c.h);
      ctx.strokeStyle = "#1b1b1f"; ctx.lineWidth = 4; ctx.lineJoin = "round";
      lib.wobblePath(ctx, [[c.x + 40, c.y + 40], [c.x + c.w - 40, c.y + 40], [c.x + c.w - 40, c.y + c.h - 40], [c.x + 40, c.y + c.h - 40]], { amp: 3, seed: lib.step(t, 8), close: true }); ctx.stroke();
      ctx.strokeStyle = "#e4572e"; ctx.lineWidth = 8; ctx.lineCap = "round";
      lib.strokePartial(ctx, [[c.x + 70, cy + 30], [cx - 20, cy + 70], [c.x + c.w - 70, cy - 60]], lib.tween(t, 0.2, 1.4, lib.ease.inOutCubic));
      break;
    }
    case "shader (WebGL2)": ctx.drawImage(FX.render(t), c.x, c.y, c.w, c.h); break;
  }
}
