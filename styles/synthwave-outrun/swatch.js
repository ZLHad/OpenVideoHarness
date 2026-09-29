// synthwave-outrun swatch · 合成器浪潮 (swatch grid 150 BPM: one grid line per beat, 0.4 s)
// Everything is painted on a 2D canvas, then played back "from a videotape on a CRT" by one WebGL pass
// (luma/chroma split with horizontal chroma bleed, red shift, 3 px scanlines, darkened corners, faint noise).
//   0.00–0.36  HOOK · CRT power-on: a dot, a line (0.00–0.07), then the picture opens vertically (a third open at 0.1 s)
//   0.20–0.90  the striped sun rises; the cyan grid starts rolling toward the camera, locked to the beat
//   0.80–2.10  title: chrome letters (with a white horizon band) rise 60 ms apart; a specular sweep at 2.00; four-point
//              glints on the beat at 1.60 and 2.80
//   1.20–1.70  the Chinese line flickers on like a neon tube
//   2.00–2.40  motif: objects of the era power on half a beat apart: a wireframe cassette (outline) → a chrome-edged
//              VHS sleeve with three panels (storyboard) → a chrome CRT playing a tiny sunset (draft); 2.8 / 3.2 / 3.6
//              one object flares per beat
//   4.40       "Outrun" in neon script (300 px) lands on the beat; the sun lifts 10 px with it
//   4.00–4.27  SIGNATURE TRANSITION: tracking noise (8 frames), then the end frame opens out of the horizon line

export const fonts = ["Avenir Next Condensed", "SignPainter", "Andale Mono", "Lantinghei SC"];
const F = { fonts: {
  chrome: { family: ["Avenir Next Condensed", "Futura"], weight: 900, style: "italic" },
  label: { family: ["Avenir Next Condensed", "Futura"], weight: 600 },
  script: { family: ["SignPainter", "Snell Roundhand"], weight: 600 },
  mono: { family: ["Andale Mono", "Menlo"], weight: 400 },
  zh: { family: ["Lantinghei SC", "PingFang SC"], weight: 900 },
  zhl: { family: ["PingFang SC", "Hiragino Sans GB"], weight: 600 },
} };
const TAU = Math.PI * 2, BEAT = 60 / 150, HY = 594, VX = 960;   // swatch at 150 BPM so 0.8 / 2.0 / 4.0 s are beats
let L = null, FX = null;

const POST = `
uniform float u_track;
float h1(float n){ return fract(sin(n * 12.9898) * 43758.5453); }
float h2(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233)) + u_frame * 1.618) * 43758.5453); }
vec3 yuv(vec3 c){ return vec3(dot(c, vec3(0.299, 0.587, 0.114)), dot(c, vec3(-0.169, -0.331, 0.5)), dot(c, vec3(0.5, -0.419, -0.081))); }
vec3 rgb(vec3 y){ return vec3(y.x + 1.402 * y.z, y.x - 0.344 * y.y - 0.714 * y.z, y.x + 1.772 * y.y); }
void main(){
  vec2 px = vec2(v_uv.x, 1.0 - v_uv.y) * u_res;
  float line = floor(px.y / 6.0);
  float dx = u_track * (h1(line + u_frame * 7.0) - 0.5) * 60.0 * step(0.55, h1(floor(px.y / 40.0) + u_frame));
  vec2 uv = v_uv + vec2(dx / u_res.x, 0.0);
  float Y = yuv(texture(u_tex0, uv).rgb).x;
  vec2 C = vec2(0.0);
  for (int k = -3; k <= 3; k++) C += yuv(texture(u_tex0, uv + vec2(float(k) * 1.4 / u_res.x, 0.0)).rgb).yz;   // chroma bleeds sideways
  C /= 7.0;
  float Cr = yuv(texture(u_tex0, uv - vec2(2.0 / u_res.x, 0.0)).rgb).z;                                         // red difference lags 2 px
  vec3 col = rgb(vec3(Y, C.x, mix(C.y, Cr, 0.5)));
  float ph = mod(px.y, 3.0) / 3.0;
  col *= 1.0 - 0.16 * (0.5 + 0.5 * cos(ph * 6.2832)) * (1.0 - 0.6 * Y);                                       // scanlines, thinner on bright
  vec2 q = v_uv * 2.0 - 1.0;
  col *= 1.0 - 0.28 * (2.0 * q.x * q.x * q.y * q.y + 0.25 * (q.x * q.x + q.y * q.y));                         // darkened corners
  col += (h2(floor(px / 2.0)) - 0.5) * 0.035;                                                                   // signal noise
  float band = u_track * smoothstep(40.0, 0.0, abs(px.y - mod(u_time * 2600.0, u_res.y)));
  col = mix(col, vec3(h2(px)), band * 0.7);                                                                     // rolling noise band
  outColor = vec4(clamp(col, 0.0, 1.0), 1.0);
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
export async function setup(ctx, tokens, lib) {
  [T, S] = await loadTimes();
  const P = (k) => lib.color(tokens, k);
  FX = lib.shader(POST);
  // stars and sky, once
  const sky = document.createElement("canvas"); sky.width = lib.W; sky.height = HY; const sx = sky.getContext("2d");
  const g = sx.createLinearGradient(0, 0, 0, HY); g.addColorStop(0, P("extra.4")); g.addColorStop(0.45, P("bg")); g.addColorStop(1, P("extra.3"));
  sx.fillStyle = g; sx.fillRect(0, 0, lib.W, HY);
  L = { P, sky, stars: Array.from({ length: 70 }, (_, i) => ({ x: lib.hash(1, i) * lib.W, y: lib.hash(2, i) * HY * 0.5, r: 0.8 + lib.hash(3, i) * 1.6, ph: lib.hash(4, i) })),
    ridge: Array.from({ length: 49 }, (_, i) => { const x = i * 40; const m = Math.abs(x - VX) < 330 ? 0.15 : 1; return [x, HY - m * (30 + 60 * Math.abs(lib.noise1(x / 160, 9)) + 26 * lib.hash(5, i))]; }),
    panelX: [560, 960, 1360], panelY: 752 };
}

function sun(ctx, lib, t, lift = 0) {
  const P = L.P, rise = lib.tween(t, 0.2, 0.95, lib.ease.outCubic), R = 238, cy = HY - 108 + (1 - rise) * 300 - lift;
  const s = lib.offscreen("sw_sun", (x) => {
    const g = x.createLinearGradient(0, cy - R, 0, cy + R); g.addColorStop(0, P("extra.2")); g.addColorStop(0.5, P("extra.1")); g.addColorStop(1, P("accent"));
    x.fillStyle = g; x.beginPath(); x.arc(VX, cy, R, 0, TAU); x.fill();
    x.globalCompositeOperation = "destination-out";
    for (let i = 0; i < 7; i++) { const y = cy + R * (0.06 + i * 0.13) + ((t / BEAT) % 1) * 0; const hgt = 2 + i * 2.7; x.fillRect(VX - R, y, 2 * R, hgt); }
    x.fillRect(0, HY, lib.W, lib.H);                                                  // the horizon hides its lower edge
  });
  ctx.save(); ctx.shadowColor = lib.rgba(P("accent"), 0.6); ctx.shadowBlur = 40; ctx.drawImage(s, 0, 0); ctx.restore();
}
function ground(ctx, lib, t) {
  const P = L.P, on = lib.tween(t, 0.3, 0.8, lib.ease.outCubic);
  const g = ctx.createLinearGradient(0, HY, 0, lib.H); g.addColorStop(0, P("extra.4")); g.addColorStop(1, P("bg"));
  ctx.fillStyle = g; ctx.fillRect(0, HY, lib.W, lib.H - HY);
  ctx.save(); ctx.strokeStyle = lib.rgba(P("extra.0"), on); ctx.shadowColor = P("extra.0"); ctx.shadowBlur = 10; ctx.lineCap = "butt";
  const off = (t / BEAT) % 1;                                                        // one line per beat
  for (let k = 1; k < 40; k++) {
    const z = k - off; if (z < 0.85) continue;
    const y = HY + 486 / z, w = Math.max(0.8, 2.4 / Math.sqrt(z));
    ctx.globalAlpha = on * Math.min(1, 2.2 / Math.sqrt(z)); ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(lib.W, y); ctx.stroke();
  }
  ctx.globalAlpha = on; ctx.lineWidth = 2;
  for (let j = -8; j <= 8; j++) { ctx.beginPath(); ctx.moveTo(VX + j * 6, HY); ctx.lineTo(VX + j * 230, lib.H); ctx.stroke(); }
  ctx.restore();
  // wireframe ridge on the horizon
  ctx.save(); ctx.fillStyle = P("extra.4"); ctx.strokeStyle = P("accent"); ctx.lineWidth = 2; ctx.shadowColor = P("accent"); ctx.shadowBlur = 8; ctx.globalAlpha = on;
  ctx.beginPath(); ctx.moveTo(0, HY); L.ridge.forEach(([x, y]) => ctx.lineTo(x, y)); ctx.lineTo(lib.W, HY); ctx.closePath(); ctx.fill(); ctx.stroke();
  ctx.lineWidth = 1; ctx.globalAlpha = on * 0.5; ctx.beginPath(); L.ridge.forEach(([x, y], i) => { if (i % 2 === 0 && y < HY - 20) { ctx.moveTo(x, y); ctx.lineTo(x + 30, HY); ctx.moveTo(x, y); ctx.lineTo(x - 30, HY); } }); ctx.stroke();
  ctx.restore();
}
function chrome(ctx, lib, t) {
  const P = L.P, size = 150;
  lib.setFont(ctx, F, "chrome", size);
  const txt = lib.TITLE_EN.toUpperCase(), lay = lib.layoutText(ctx, txt, { x: VX, y: 290, align: "center", tracking: 0.01 * size });
  const top = 290 - size * 0.74, bot = 290 + size * 0.02;
  const grad = ctx.createLinearGradient(0, top - 290, 0, bot - 290);   // glyphs are drawn in baseline-local coordinates
  [[P("extra.5"), 0], ["#CFEFFF", 0.36], ["#FFFFFF", 0.44], ["#FFFFFF", 0.49], [P("extra.6"), 0.5], ["#8B4BC2", 0.72], ["#FF9B5E", 1]].forEach(([c, s]) => grad.addColorStop(s, c));   // chrome: sky, a white horizon band, dark ground, sunset
  const st = (i) => { const t0 = 0.8 + i * 0.06; if (t < t0) return null; const p = lib.spring(t - t0, { stiffness: 220, damping: 24 }); return { dy: (1 - p) * 90, alpha: lib.clamp((t - t0) / 0.1) }; };
  lib.drawGlyphs(ctx, lay, (g, i) => { const s = st(i); return s && { ...s, fill: "none", stroke: "#1A0B2E", lineWidth: 10 }; });
  lib.drawGlyphs(ctx, lay, (g, i) => { const s = st(i); return s && { ...s, fill: grad }; });
  // specular sweep across the letters
  const u = lib.seg(t, 2.0, 2.35);
  if (u > 0 && u < 1) {
    const m = lib.offscreen("sw_sweep", (x) => { lib.setFont(x, F, "chrome", size); x.fillStyle = "#fff"; lib.drawGlyphs(x, lay, () => ({}));
      x.globalCompositeOperation = "source-in"; const bx = lib.lerp(lay.x0 - 200, lay.x1 + 200, u); const gg = x.createLinearGradient(bx - 90, 0, bx + 90, 0);
      gg.addColorStop(0, "rgba(255,255,255,0)"); gg.addColorStop(0.5, "rgba(255,255,255,0.9)"); gg.addColorStop(1, "rgba(255,255,255,0)"); x.fillStyle = gg; x.fillRect(0, 0, lib.W, lib.H); });
    ctx.drawImage(m, 0, 0);
  }
  for (const [tg, gi] of [[T.glint1, 0], [T.glint2, lay.glyphs.length - 2]]) {                 // four-point glints, on the beat
    const gl = lib.env(t, tg, tg + 8 / 30, 0.05, 0.16); if (gl <= 0) continue;
    const gx = lay.glyphs[gi].x + 18, gy = top + 16, r = 70 * gl; ctx.save(); ctx.fillStyle = "#fff"; ctx.shadowColor = "#fff"; ctx.shadowBlur = 20;
    ctx.beginPath(); ctx.moveTo(gx - r, gy); ctx.lineTo(gx, gy - 6); ctx.lineTo(gx + r, gy); ctx.lineTo(gx, gy + 6); ctx.closePath(); ctx.moveTo(gx, gy - r); ctx.lineTo(gx + 6, gy); ctx.lineTo(gx, gy + r); ctx.lineTo(gx - 6, gy); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.arc(gx, gy, 9 * gl, 0, TAU); ctx.fill(); ctx.restore();
  }
}
function neonZH(ctx, lib, t) {
  const P = L.P;
  lib.setFont(ctx, F, "zh", 72);
  const lay = lib.layoutText(ctx, lib.TITLE_ZH, { x: VX, y: 408, align: "center", tracking: 0.18 * 72 });
  const on = (i) => { const t0 = 1.2 + i * 0.05; if (t < t0) return 0; if (t > t0 + 0.3) return 1; return lib.hash(7, i, lib.frame(t)) > 0.45 ? 1 : 0.15; };   // tube flicker
  ctx.save();
  lib.drawGlyphs(ctx, lay, (g, i) => { const a = on(i); return a > 0 ? { alpha: a, fill: "none", stroke: "#1A0B2E", lineWidth: 12 } : null; });   // dark bed: legible over the sun
  ctx.shadowColor = P("accent"); ctx.shadowBlur = 14;
  lib.drawGlyphs(ctx, lay, (g, i) => { const a = on(i); return a > 0 ? { alpha: a, fill: "none", stroke: P("accent"), lineWidth: 5 } : null; });
  ctx.shadowBlur = 0;
  lib.drawGlyphs(ctx, lay, (g, i) => { const a = on(i); return a > 0 ? { alpha: a, fill: "#FFE3F1" } : null; });
  ctx.restore();
}
// the motif as objects of the era: a wireframe cassette (outline) → a VHS sleeve with three panels (storyboard) → a CRT
// television playing the sunset (draft); chrome bezels. They power on half a beat apart; after that one neon pulse per beat.
function chromeRect(ctx, x, y, w, h, r) {
  const g = ctx.createLinearGradient(0, y, 0, y + h); g.addColorStop(0, "#5EC8FF"); g.addColorStop(0.45, "#F2ECFF"); g.addColorStop(0.5, "#3A1E4A"); g.addColorStop(0.75, "#8B4BC2"); g.addColorStop(1, "#FF9B5E");
  ctx.fillStyle = g; ctx.beginPath(); ctx.roundRect(x, y, w, h, r); ctx.fill(); ctx.strokeStyle = "#1A0B2E"; ctx.lineWidth = 3; ctx.stroke();
}
function panels(ctx, lib, t) {
  const P = L.P, w = 270, h = 170;
  L.panelX.forEach((cx, k) => {
    const t0 = S.obj[k]; if (t < t0) return;
    const sy = lib.tween(t, t0, t0 + 6 / 30, lib.ease.outExpo), fl = t < t0 + 0.2 ? (lib.hash(9, k, lib.frame(t)) > 0.3 ? 1 : 0.3) : 1, cy = L.panelY;
    const pulse = 1 + 0.9 * Math.max(0, 1 - Math.abs(t - (2.8 + k * BEAT)) * 6);            // 2.8 / 3.2 / 3.6: one object flares per beat
    ctx.save(); ctx.translate(cx, cy); ctx.scale(1, sy); ctx.globalAlpha = fl;
    ctx.lineJoin = "round"; ctx.lineCap = "round";
    if (k === 0) {                                             // cassette, wireframe only
      ctx.strokeStyle = P("extra.0"); ctx.shadowColor = P("extra.0"); ctx.shadowBlur = 10 * pulse; ctx.lineWidth = 3;
      ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2 + 12, w, h - 24, 12); ctx.stroke();
      ctx.beginPath(); ctx.roundRect(-w / 2 + 34, -h / 2 + 34, w - 68, 56, 6); ctx.stroke();
      for (const dx of [-54, 54]) { ctx.beginPath(); ctx.arc(dx, -h / 2 + 62, 18, 0, TAU); ctx.stroke(); for (let s2 = 0; s2 < 6; s2++) { const a = s2 * TAU / 6 + t * 5; ctx.beginPath(); ctx.moveTo(dx + Math.cos(a) * 8, -h / 2 + 62 + Math.sin(a) * 8); ctx.lineTo(dx + Math.cos(a) * 16, -h / 2 + 62 + Math.sin(a) * 16); ctx.stroke(); } }
      ctx.beginPath(); ctx.moveTo(-w / 2 + 50, h / 2 - 12); ctx.lineTo(-w / 2 + 70, h / 2 - 40); ctx.lineTo(w / 2 - 70, h / 2 - 40); ctx.lineTo(w / 2 - 50, h / 2 - 12); ctx.stroke();
    } else if (k === 1) {                                      // VHS sleeve: chrome edge, cover art in three panels
      chromeRect(ctx, -w / 2 + 30, -h / 2, w - 60, h, 6);
      const px = -w / 2 + 44, pw = (w - 88 - 16) / 3;
      for (let i = 0; i < 3; i++) {
        const x = px + i * (pw + 8), gg = ctx.createLinearGradient(0, -h / 2 + 14, 0, h / 2 - 14);
        gg.addColorStop(0, P("extra.4")); gg.addColorStop(1, [P("extra.3"), P("accent"), P("extra.1")][i]);
        ctx.fillStyle = gg; ctx.fillRect(x, -h / 2 + 14, pw, h - 28);
        ctx.strokeStyle = P("extra.0"); ctx.lineWidth = 2; ctx.shadowColor = P("extra.0"); ctx.shadowBlur = 6 * pulse; ctx.beginPath(); ctx.moveTo(x, h / 2 - 40); ctx.lineTo(x + pw, h / 2 - 40); ctx.stroke(); ctx.shadowBlur = 0;
      }
    } else {                                                   // CRT television playing: chrome bezel, a tiny sunset on the tube
      chromeRect(ctx, -w / 2, -h / 2, w, h, 22);
      ctx.save(); ctx.beginPath(); ctx.roundRect(-w / 2 + 18, -h / 2 + 16, w - 70, h - 32, 18); ctx.clip();
      const sg = ctx.createLinearGradient(0, -h / 2, 0, h / 2); sg.addColorStop(0, P("extra.4")); sg.addColorStop(0.6, P("extra.3")); sg.addColorStop(1, P("extra.4"));
      ctx.fillStyle = sg; ctx.fillRect(-w / 2, -h / 2, w, h);
      const scx = -w / 2 + 18 + (w - 70) / 2, hz = 18;
      const su = ctx.createLinearGradient(0, hz - 46, 0, hz); su.addColorStop(0, P("extra.2")); su.addColorStop(1, P("accent"));
      ctx.fillStyle = su; ctx.beginPath(); ctx.arc(scx, hz, 44, Math.PI, TAU); ctx.fill();
      ctx.strokeStyle = P("extra.0"); ctx.lineWidth = 1.5; const off = (t / BEAT) % 1;
      for (let z = 1; z < 8; z++) { const y = hz + 40 / (z - off + 0.6); ctx.beginPath(); ctx.moveTo(-w / 2, y); ctx.lineTo(w / 2, y); ctx.stroke(); }
      ctx.fillStyle = "rgba(0,0,0,0.25)"; for (let y = -h / 2; y < h / 2; y += 4) ctx.fillRect(-w / 2, y, w, 1.5);
      ctx.restore();
      ctx.fillStyle = "#1A0B2E"; for (let i = 0; i < 3; i++) { ctx.beginPath(); ctx.arc(w / 2 - 26, -h / 2 + 40 + i * 30, 7, 0, TAU); ctx.fill(); }
      ctx.fillStyle = P("accent"); ctx.shadowColor = P("accent"); ctx.shadowBlur = 10 * pulse; ctx.beginPath(); ctx.arc(w / 2 - 26, h / 2 - 22, 5, 0, TAU); ctx.fill();
    }
    ctx.restore();
    ctx.save(); ctx.globalAlpha = lib.clamp((t - t0) * 6); ctx.textAlign = "center";
    lib.setFont(ctx, F, "zhl", 48); ctx.fillStyle = P("fg"); ctx.fillText(lib.MOTIF[k].zh, cx, cy + h / 2 + 62);
    lib.setFont(ctx, F, "label", 40); ctx.fillStyle = P("extra.0"); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), cx, cy + h / 2 + 110, { align: "center", tracking: 4 });
    ctx.restore();
  });
}
function osd(ctx, lib, t, label = "PLAY ▶") {
  const f = lib.frame(t), tc = `00:00:${String(Math.floor(t)).padStart(2, "0")}:${String(f % 30).padStart(2, "0")}`;
  ctx.save(); lib.setFont(ctx, F, "mono", 32); ctx.fillStyle = "rgba(242,236,255,0.85)"; ctx.fillText(label, 150, 120); ctx.textAlign = "right"; ctx.fillText(tc, lib.W - 150, 120); ctx.restore();
}
function scene(ctx, t, tokens, lib, end = false) {
  const P = L.P;
  ctx.drawImage(L.sky, 0, 0);
  for (const s of L.stars) { const tw = 0.5 + 0.5 * Math.sin(TAU * (lib.step(t, 6) * 0.7 + s.ph)); ctx.fillStyle = `rgba(242,236,255,${0.35 + 0.55 * tw})`; ctx.fillRect(s.x, s.y, s.r, s.r); }
  sun(ctx, lib, end ? 5 : t, end ? 10 * lib.tween(t, T.outrun, T.outrun + 0.2, lib.ease.outCubic) : 0);
  ground(ctx, lib, end ? 5 : t);
  if (!end) { chrome(ctx, lib, t); neonZH(ctx, lib, t); panels(ctx, lib, t); osd(ctx, lib, t); }
  else {
    const land = lib.tween(t, T.outrun, T.outrun + 5 / 30, lib.ease.outExpo);
    if (t >= T.outrun) { ctx.save(); ctx.textAlign = "center"; lib.setFont(ctx, F, "script", 300); ctx.globalAlpha = lib.clamp((t - T.outrun) * 15);
      ctx.translate(VX, 330 - 60 * (1 - land)); ctx.rotate(-0.08); ctx.scale(1.25 - 0.25 * land, 1.25 - 0.25 * land);
      ctx.lineWidth = 10; ctx.strokeStyle = P("accent"); ctx.shadowColor = P("accent"); ctx.shadowBlur = 30; ctx.strokeText("Outrun", 0, 0);
      ctx.shadowBlur = 12; ctx.fillStyle = "#FFE3F1"; ctx.fillText("Outrun", 0, 0); ctx.restore(); }
    osd(ctx, lib, t, "STOP ■");
  }
}

export function renderAt(t, ctx, tokens, lib) {
  const src = lib.offscreen("sw_src", (x) => {
    x.fillStyle = "#000"; x.fillRect(0, 0, lib.W, lib.H);
    if (t < 0.45) {                                                                  // CRT power-on
      const lineU = lib.seg(t, 0.0, T.crt), openU = lib.tween(t, T.crt, T.crt + 0.29, lib.ease.outCubic);   // the picture is a third open on the 0.1 s beat
      if (openU > 0) { x.save(); x.beginPath(); x.rect(0, lib.H / 2 - openU * lib.H / 2 - 2, lib.W, openU * lib.H + 4); x.clip(); scene(x, t, tokens, lib); x.restore(); }
      const a = 1 - openU, lw = lib.lerp(8, lib.W, lib.ease.outExpo(lineU));
      x.fillStyle = `rgba(235,240,255,${a})`; x.fillRect(VX - lw / 2, lib.H / 2 - 3 - openU * 30, lw, 6 + openU * 60);
    } else if (t < T.track) scene(x, t, tokens, lib);
    else {
      const open = lib.tween(t, T.track + 0.27, T.track + 0.72, lib.ease.inOutCubic);                   // end frame opens out of the horizon line
      scene(x, t, tokens, lib);
      if (open > 0) { x.save(); x.beginPath(); x.rect(0, HY - open * HY, lib.W, open * (lib.H) + 2); x.clip(); scene(x, t, tokens, lib, true); x.restore();
        x.save(); x.strokeStyle = L.P("accent"); x.lineWidth = 3; x.shadowColor = L.P("accent"); x.shadowBlur = 12; x.beginPath(); x.moveTo(0, HY - open * HY); x.lineTo(lib.W, HY - open * HY); x.moveTo(0, HY + open * (lib.H - HY)); x.lineTo(lib.W, HY + open * (lib.H - HY)); if (open < 1) x.stroke(); x.restore(); }
    }
  });
  const track = t >= T.track && t < T.track + 0.27 ? 1 : 0;
  ctx.drawImage(FX.render(t, { u_track: track }, { u_tex0: src }), 0, 0);
}
