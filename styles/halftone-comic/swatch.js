// halftone-comic swatch: a printed comic page in motion.
// Pipeline per page: C/M/Y ink densities are painted into two canvases (near = R,G,B + alpha mask, far = background),
// a print shader turns them into screen-fixed Ben-Day dots (C 15°, M 75°, Y 0°), misregisters each plate (far layers
// more than near ones, a kick on every hit) and multiplies the inks on newsprint; the black plate (keylines, lettering,
// speed lines) is drawn afterwards as vectors, always in register.
//   0.0–0.8  the title panel slams in: yellow + magenta dots, speed lines on twos
//   0.8–2.6  title letters slam in on twos (12 fps poses); Chinese in a yellow caption box
//   2.0–3.0  three panels: pencils (outline) → inks (storyboard) → colours (draft) with a "BAM!" that kicks the plates
//   4.0–4.55 a diagonal panel split slides the end panel in (smooth, every frame)

let L = null;
const PAPER = [245, 238, 220];
const ink = (c, m, y) => `rgb(${Math.round(c * 255)},${Math.round(m * 255)},${Math.round(y * 255)})`;

const FRAG = `
uniform vec2 u_cn, u_mn, u_yn, u_cf, u_mf, u_yf;   // plate offsets in screen px (y down): near / far
uniform float u_period;
float hash(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec2 sh(vec2 o){ return vec2(o.x, -o.y) / u_res; }
float dens(int ch, vec2 on, vec2 of){
  vec4 n = texture(u_tex0, v_uv - sh(on));
  vec4 f = texture(u_tex1, v_uv - sh(of));
  float dn = ch == 0 ? n.r : (ch == 1 ? n.g : n.b);
  float df = ch == 0 ? f.r : (ch == 1 ? f.g : f.b);
  return mix(df, dn, n.a);
}
float cov(vec2 px, float d, float ang){
  if (d < 0.04) return 0.0;
  if (d > 0.9) return 1.0;
  float c = cos(ang), s = sin(ang);
  vec2 q = mat2(c, -s, s, c) * px / u_period;
  vec2 f = fract(q) - 0.5;
  float r = sqrt(d) * 0.74, aa = 0.9 / u_period;
  return 1.0 - smoothstep(r - aa, r + aa, length(f));
}
void main(){
  vec2 px = v_uv * u_res;
  float c = cov(px, dens(0, u_cn, u_cf), radians(15.0));
  float m = cov(px, dens(1, u_mn, u_mf), radians(75.0));
  float y = cov(px, dens(2, u_yn, u_yf), radians(0.0));
  vec3 paper = vec3(${PAPER.map((v) => (v / 255).toFixed(4)).join(",")});
  vec3 col = paper * mix(vec3(1.0), vec3(0.0, 0.639, 0.878), c * 0.95) * mix(vec3(1.0), vec3(0.898, 0.157, 0.482), m * 0.95) * mix(vec3(1.0), vec3(1.0, 0.831, 0.0), y * 0.95);
  outColor = vec4(col, 1.0);
}`;

export const fonts = ["HanziPen SC", "Avenir Next Condensed", "Futura"];

export async function setup(ctx, tokens, lib) {
  const fx = lib.shader(FRAG);
  const top = { x: 96, y: 66, w: 1728, h: 404 };
  const pw = (1728 - 2 * 18) / 3;
  const panels = [0, 1, 2].map((k) => ({ x: 96 + k * (pw + 18), y: 500, w: pw, h: 490 }));
  L = { fx, top, panels };
}

const kick = (t, t0, A = 8) => (t < t0 ? 0 : A * Math.exp(-(t - t0) / 0.08) * Math.cos(2 * Math.PI * 6 * (t - t0)));
const HITS = [0.15, 2.58, 4.0];

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const u = lib.tween(t, 4.0, 4.55, lib.ease.inOutCubic);
  if (u <= 0) return page(ctx, t, tokens, lib, mainPage);
  if (u >= 1) return page(ctx, t, tokens, lib, endPage);
  const A = lib.layer("htc_A"); page(A, t, tokens, lib, mainPage);
  const B = lib.layer("htc_B"); page(B, t, tokens, lib, endPage);
  ctx.drawImage(A.canvas, 0, 0);
  // diagonal panel split: boundary n·p = d moves from the lower-right corner to beyond the upper-left
  const n = [0.857, 0.514], dMax = W * n[0] + H * n[1], d = lib.lerp(dMax + 20, -40, u);
  const poly = (dd) => { const p = []; const far = 4000; const ox = n[0] * dd, oy = n[1] * dd, tx = -n[1], ty = n[0];
    p.push([ox + tx * far, oy + ty * far], [ox - tx * far, oy - ty * far], [ox - tx * far + n[0] * far, oy - ty * far + n[1] * far], [ox + tx * far + n[0] * far, oy + ty * far + n[1] * far]); return p; };
  const path = (pts) => { ctx.beginPath(); pts.forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath(); };
  ctx.save(); path(poly(d - 12)); ctx.fillStyle = `rgb(${PAPER.join(",")})`; ctx.fill(); ctx.restore();       // gutter
  ctx.save(); path(poly(d + 12)); ctx.clip(); ctx.drawImage(B.canvas, 0, 0); ctx.restore();
  ctx.save(); ctx.strokeStyle = "#1A1A1A"; ctx.lineWidth = 7; path(poly(d + 12)); ctx.stroke(); path(poly(d - 12)); ctx.stroke(); ctx.restore();
}

// one page: densities → print shader → black plate on top
function page(ctx, t, tokens, lib, content) {
  const { W, H } = lib;
  const near = lib.layer("htc_near"), far = lib.layer("htc_far");
  far.fillStyle = ink(0, 0, 0); far.fillRect(0, 0, W, H);
  const z = 1, dolly = (c) => { c.translate(W / 2, H / 2); c.scale(z, z); c.translate(-W / 2, -H / 2); };
  near.save(); far.save(); dolly(near); dolly(far);
  const k = { draw: null };
  content(t, tokens, lib, near, far, null);
  near.restore(); far.restore();
  const kk = HITS.reduce((s, h) => s + kick(t, h), 0);
  const img = L.fx.render(t, {
    u_period: 17,
    u_cn: [2 + kk, -1 - kk * 0.4], u_mn: [-2 - kk, 1 + kk * 0.5], u_yn: [0, 0],
    u_cf: [6 + kk, -3], u_mf: [-6 - kk, 3], u_yf: [2, 2],
  }, { u_tex0: near.canvas, u_tex1: far.canvas });
  ctx.drawImage(img, 0, 0);
  ctx.save(); dolly(ctx); content(t, tokens, lib, null, null, ctx); ctx.restore();
}

// ── shared bits
function glyphPose(t, lib, t0, sp) {             // a letter slams in: poses on twos, overshoot allowed
  const tq = lib.step(t, 12);
  if (tq < t0) return null;
  const s = 1 + 0.7 * (1 - lib.spring(tq - t0 + 1 / 12, sp));
  return { scale: s };
}
function speedLines(K, lib, t, cx, cy, rx, ry, clip, seed, n = 56, holes = [], fps = 12) {
  const s = fps ? lib.step(t, fps) * fps : 0;
  K.save(); K.beginPath(); K.rect(clip.x, clip.y, clip.w, clip.h); for (const h of holes) K.rect(h.x, h.y, h.w, h.h); K.clip("evenodd"); K.fillStyle = "#1A1A1A";
  for (let i = 0; i < n; i++) {
    const a = (i / n) * lib.TAU + 0.08 * lib.hashS(seed, i, s), w = 0.006 + 0.012 * lib.hash(seed, i, s + 1), len = 0.55 + 0.4 * lib.hash(seed, i, s + 2);
    const r0 = 1 + 0.15 * lib.hash(seed, i, s + 3), R = 1400;
    const p = (ang, r) => [cx + Math.cos(ang) * rx * r, cy + Math.sin(ang) * ry * r];
    K.beginPath(); const [x0, y0] = p(a, r0), [x1, y1] = [cx + Math.cos(a - w) * R, cy + Math.sin(a - w) * R], [x2, y2] = [cx + Math.cos(a + w) * R, cy + Math.sin(a + w) * R];
    K.moveTo(x0, y0); K.lineTo(lib.lerp(x0, x1, len) , lib.lerp(y0, y1, len)); K.lineTo(lib.lerp(x0, x2, len), lib.lerp(y0, y2, len)); K.closePath(); K.fill();
  }
  K.restore();
}
function captionBox(N, K, lib, tokens, x, y, zh, en, t, t0, center = false, zs = 50) {
  const tq = lib.step(t, 12); if (tq < t0) return;
  const s = 1 + 0.25 * (1 - lib.spring(tq - t0 + 1 / 12, { stiffness: 400, damping: 24 }));
  const setZ = (c) => lib.setFont(c, { fonts: { zh: ["HanziPen SC", "PingFang SC"] } }, "zh", zs, { weight: 700 });
  const setE = (c) => lib.setFont(c, tokens, "body", 30, { weight: 600 });
  const c0 = N || K; setZ(c0); const zw = c0.measureText(zh).width; setE(c0); const ew = en ? c0.measureText(en).width + 22 : 0;
  const w = zw + ew + 40, h = zs + 24; if (center) x -= w / 2;
  const tf = (c) => { c.translate(x, y); c.scale(s, s); };
  if (N) { N.save(); tf(N); N.fillStyle = ink(0, 0, 1); N.fillRect(0, 0, w, h); N.restore(); }
  if (K) { K.save(); tf(K); K.strokeStyle = "#1A1A1A"; K.lineWidth = 5; K.strokeRect(0, 0, w, h); K.fillStyle = "#1A1A1A";
    setZ(K); lib.drawText(K, zh, 20, zs + 4); if (en) { setE(K); lib.drawText(K, en, 20 + zw + 22, zs); } K.restore(); }
}
function panelFrame(K, lib, p, t, t0) {
  const tq = lib.step(t, 12); if (tq < t0) return false;
  if (K) { const s = 1 + 0.06 * (1 - lib.spring(tq - t0 + 1 / 12, { stiffness: 400, damping: 24 }));
    K.save(); K.translate(p.x + p.w / 2, p.y + p.h / 2); K.scale(s, s); K.strokeStyle = "#1A1A1A"; K.lineWidth = 7; K.strokeRect(-p.w / 2, -p.h / 2, p.w, p.h); K.restore(); }
  return true;
}

function mainPage(t, tokens, lib, N, F, K) {
  const { W } = lib, P = L.top, sp = tokens.ease.spring, tq = lib.step(t, 12);
  // ── title panel: yellow solid + magenta dots crowding the edges
  if (tq >= 0.15) {
    if (F) { const g = F.createRadialGradient(W / 2, 250, 120, W / 2, 250, 980); g.addColorStop(0, ink(0, 0.08, 1)); g.addColorStop(1, ink(0, 0.62, 1));
      F.fillStyle = g; F.fillRect(P.x, P.y, P.w, P.h); }
    if (K) speedLines(K, lib, t, W / 2, 262, 640, 120, P, 3, 48, [{ x: 196, y: 128, w: 1528, h: 190 }, { x: 610, y: 318, w: 700, h: 106 }]);
    panelFrame(K, lib, P, t, 0.15);
  }
  // title: knockout letters (paper), red offset shadow on the colour plates, black outline on the key plate
  const setT = (c) => lib.setFont(c, tokens, "display", 176, { weight: 800, stretch: "condensed" });
  const c0 = N || K; setT(c0);
  const lay = lib.layoutText(c0, lib.TITLE_EN, { x: W / 2, y: 292, align: "center", tracking: 0.01 * 176 });
  const pose = (i) => glyphPose(t, lib, 0.84 + i * 0.045, sp);
  if (N) { setT(N);
    lib.drawGlyphs(N, lay, (g, i) => { const p = pose(i); return p && { ...p, dx: 11, dy: 11, fill: ink(0, 1, 1) }; });
    lib.drawGlyphs(N, lay, (g, i) => { const p = pose(i); return p && { ...p, fill: ink(0, 0, 0) }; }); }
  if (K) { setT(K); K.lineJoin = "round";
    lib.drawGlyphs(K, lay, (g, i) => { const p = pose(i); return p && { ...p, fill: "none", stroke: "#1A1A1A", lineWidth: 8 }; }); }
  // Chinese caption box
  captionBox(N, K, lib, tokens, W / 2, 330, lib.TITLE_ZH, "", t, 1.5, true, 62);

  // ── three panels: pencils → inks → colours
  L.panels.forEach((p, k) => {
    const t0 = 2.0 + k * 0.12;
    if (tq < t0) return;
    if (F && k === 1) { F.fillStyle = ink(0.1, 0, 0); F.fillRect(p.x, p.y, p.w, p.h); }
    if (F && k === 2) { const g = F.createRadialGradient(p.x + p.w / 2, p.y + p.h / 2 + 20, 60, p.x + p.w / 2, p.y + p.h / 2, 420); g.addColorStop(0, ink(0.05, 0.12, 0)); g.addColorStop(1, ink(0.1, 0.6, 0)); F.fillStyle = g; F.fillRect(p.x, p.y, p.w, p.h); }
    art(t, lib, p, k, N, K, t0);
    panelFrame(K, lib, p, t, t0);
    captionBox(N, K, lib, tokens, p.x + 16, p.y + 16, lib.MOTIF[k].zh, lib.MOTIF[k].en.toUpperCase(), t, t0 + 0.08);
  });
}

// the same object in three production stages: a starburst behind a screen with a play triangle
function art(t, lib, p, k, N, K, t0) {
  const cx = p.x + p.w / 2, cy = p.y + p.h / 2 + 46;
  const shake = k === 2 ? 6 * Math.exp(-Math.max(0, lib.step(t, 12) - 2.58) / 0.15) * (lib.step(t, 12) >= 2.58 ? Math.sin(lib.step(t, 12) * 90) : 0) : 0;
  const star = [], nS = 14;
  for (let i = 0; i < 2 * nS; i++) { const a = (i / (2 * nS)) * lib.TAU - Math.PI / 2, r = i % 2 ? 108 : 176 + 10 * lib.hashS(k, i); star.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r * 0.86]); }
  const scr = { x: cx - 112 + shake, y: cy - 78, w: 224, h: 156 };
  const tri = [[cx - 26 + shake, cy - 40], [cx + 44 + shake, cy], [cx - 26 + shake, cy + 40]];
  const poly = (c, pts) => { c.beginPath(); pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y))); c.closePath(); };
  const u = lib.seg(lib.step(t, 12), t0 + 0.05, t0 + 0.4);                      // drawing progress, on twos
  if (k === 0 || k === 1) {                                                      // pencils (non-photo blue, not printed)
    if (K) { K.save(); K.strokeStyle = k === 0 ? "#6FB6DE" : "rgba(111,182,222,0.45)"; K.lineWidth = 3; K.lineCap = "round";
      const seed = lib.step(t, 12) * 12 + k * 100;
      lib.wobblePath(K, star, { amp: 2.2, seed, close: true }); if (u > 0) { K.setLineDash([2400 * u, 1e5]); K.stroke(); K.setLineDash([]); }
      if (u > 0.4) { lib.wobblePath(K, [[scr.x, scr.y], [scr.x + scr.w, scr.y], [scr.x + scr.w, scr.y + scr.h], [scr.x, scr.y + scr.h]], { amp: 2.2, seed: seed + 7, close: true }); K.stroke(); }
      if (u > 0.7) { lib.wobblePath(K, tri, { amp: 1.8, seed: seed + 9, close: true }); K.stroke(); }
      K.beginPath(); K.ellipse(cx, cy, 190, 165, 0, 0, lib.TAU); K.globalAlpha = 0.35; K.stroke(); K.restore(); }
  }
  if (k === 1 && K) {                                                            // inks: clean black keylines
    K.save(); K.strokeStyle = "#1A1A1A"; K.lineJoin = "round"; K.lineWidth = 6;
    poly(K, star); K.setLineDash([2400 * u, 1e5]); K.stroke(); K.setLineDash([]);
    if (u > 0.45) { K.beginPath(); K.roundRect(scr.x, scr.y, scr.w, scr.h, 14); K.fillStyle = "rgba(0,0,0,0)"; K.stroke(); }
    if (u > 0.75) { K.lineWidth = 5; poly(K, tri); K.stroke(); }
    K.restore();
  }
  if (k === 2) {                                                                 // colours + halftone + BAM
    if (N) {
      N.fillStyle = ink(0, 0.35, 1); poly(N, star); N.fill();
      N.fillStyle = ink(0.62, 0, 0); N.beginPath(); N.roundRect(scr.x, scr.y, scr.w, scr.h, 14); N.fill();
      N.fillStyle = ink(0, 0, 0); N.beginPath(); N.roundRect(scr.x + 18, scr.y + 16, 60, 18, 9); N.fill();   // highlight = bare paper
      N.fillStyle = ink(0, 1, 1); poly(N, tri); N.fill();
    }
    if (K) { K.save(); K.strokeStyle = "#1A1A1A"; K.lineJoin = "round"; K.lineWidth = 6; poly(K, star); K.stroke();
      K.beginPath(); K.roundRect(scr.x, scr.y, scr.w, scr.h, 14); K.stroke(); K.lineWidth = 5; poly(K, tri); K.stroke(); K.restore(); }
    // BAM! pops 30 % → 115 % → 100 % in 6 frames (on twos), tilted
    const tq = lib.step(t, 12), b0 = 2.58;
    if (tq >= b0) {
      const s = lib.clamp(0.3 + (1 - lib.spring(tq - b0 + 1 / 12, { stiffness: 400, damping: 24 })) * -0.7 + 0.7, 0, 2);
      const setB = (c) => lib.setFont(c, { fonts: { d: ["Futura"] } }, "d", 112, { weight: 800, stretch: "condensed" });
      const bx = p.x + p.w - 150, by = p.y + p.h - 44;
      const draw = (c, f) => { c.save(); c.translate(bx, by); c.rotate(-0.14); c.scale(s, s); setB(c); c.textAlign = "center"; f(c); c.restore(); };
      if (N) draw(N, (c) => { c.fillStyle = ink(0, 1, 1); c.fillText("BAM!", 8, 8); c.fillStyle = ink(0, 0, 1); c.fillText("BAM!", 0, 0); });
      if (K) draw(K, (c) => { c.lineJoin = "round"; c.strokeStyle = "#1A1A1A"; c.lineWidth = 6; c.strokeText("BAM!", 0, 0); });
    }
    if (K && tq >= 2.58) speedLines(K, lib, t, cx, cy, 250, 215, p, 11, 36);
  }
}

function endPage(t, tokens, lib, N, F, K) {
  const { W, H } = lib;
  if (F) { const g = F.createRadialGradient(W / 2, 520, 150, W / 2, 520, 1100); g.addColorStop(0, ink(0, 0.06, 1)); g.addColorStop(1, ink(0, 0.66, 1)); F.fillStyle = g; F.fillRect(0, 0, W, H); }
  if (K) speedLines(K, lib, t, W / 2, 520, 780, 230, { x: 0, y: 0, w: W, h: H }, 21, 64, [{ x: 280, y: 380, w: 1360, h: 390 }], 0);
  const setT = (c) => lib.setFont(c, tokens, "display", 200, { weight: 800, stretch: "condensed" });
  const c0 = N || K; setT(c0);
  const lay = lib.layoutText(c0, "HALFTONE COMIC", { x: W / 2, y: 580, align: "center", tracking: 0.02 * 200 });
  if (N) { setT(N); lib.drawGlyphs(N, lay, () => ({ dx: 12, dy: 12, fill: ink(0, 1, 1) })); lib.drawGlyphs(N, lay, () => ({ fill: ink(0, 0, 0) })); }
  if (K) { setT(K); K.lineJoin = "round"; lib.drawGlyphs(K, lay, () => ({ fill: "none", stroke: "#1A1A1A", lineWidth: 9 })); }
  captionBox(N, K, lib, tokens, W / 2, 650, "半调漫画", "", t, 0, true, 66);
}
