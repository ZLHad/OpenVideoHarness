// OpenVideoHarness intro film: one continuous camera through one world.
// Every frame is a pure function of t (HyperFrames publishes t via "hf-seek").
// Grid: 80 BPM in v5 (90 in v3), 30 fps -> beat = 22.5 frames, bar = 90 frames; 30 bars (bar 11 in 6/4) = 91.5 s. v5 shows it from bar 10 on.
// Sections: S1 hook 1–3 · S2 program 4–6 · S3 problem 7–8 · S4 braam 9 · S5 architecture 10–13 (arch.js) · S6 workflow 14–18 (pipeline.js)
//           S7 features 19–21 + S8 cases 22 (features.js) · S9 proof hall 23–26 · S10 reveal 27–28 · S11 title 29–30.
import { EffectComposer } from "three/addons/postprocessing/EffectComposer.js";
import { RenderPass } from "three/addons/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/addons/postprocessing/UnrealBloomPass.js";
import { ShaderPass } from "three/addons/postprocessing/ShaderPass.js";
import { OutputPass } from "three/addons/postprocessing/OutputPass.js";
import { readPreset, makeWarp, makePulses, motionShader, gradeShader, makeSparks, makeStreams, makeWarpLines, textMaterial, makeDynText, tubeMat } from "./fx.js";
import { buildArch } from "./arch.js";
import { buildPipeline } from "./pipeline.js";
import { buildFeatures } from "./features.js";

export const BPM = 80, BEAT = 60 / BPM, BAR = 4 * BEAT, FPS = 30, S16 = BEAT / 4;
// bar k (1-based), beat offset b (0-based, may be fractional). Bar 11 is a 6/4 bar (the 8-type list holds 2 extra beats),
// so every bar from 12 on starts 2 beats later than a plain 4/4 grid: 30 bars = 81.333 s = 2440 frames.
export const bar = (k, b = 0) => (k - 1) * BAR + b * BEAT + (k >= 12 ? 2 * BEAT : 0);
export const DUR = bar(31);
const barBeat = (t) => { // the true bar.beat under the 6/4 bar (for the HUD)
  if (t < bar(11)) { const bi = Math.floor(t / BEAT + 1e-6); return [Math.floor(bi / 4) + 1, (bi % 4) + 1]; }
  if (t < bar(12)) return [11, Math.floor((t - bar(11)) / BEAT + 1e-6) + 1];
  const bi = Math.floor((t - bar(12)) / BEAT + 1e-6); return [12 + Math.floor(bi / 4), (bi % 4) + 1];
};

// ---------- math ----------
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, u) => a + (b - a) * u;
const seg = (t, a, b) => clamp((t - a) / (b - a));
const eOutExpo = (u) => (u >= 1 ? 1 : 1 - Math.pow(2, -10 * u));
const eOutCubic = (u) => 1 - Math.pow(1 - u, 3);
const eInCubic = (u) => u * u * u;
const eInOut = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const hash = (i) => { const s = Math.sin(i * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const q16 = (x) => Math.round(x / S16) * S16; // snap a time to the 16th grid
// opacity window: fade in over fi after a, fade out over fo before b
const win = (t, a, b, fi = 0.45, fo = 0.45) => Math.min(eOutCubic(seg(t, a, a + fi)), 1 - eInCubic(seg(t, b - fo, b)));

const AMBER = [1.0, 0.698, 0.141];
const FG = "#EDEDEF", ZH = "#A9A9B1", MUTED = "#8B8B94", DIM = "#55555D", AMB = "#FFB224";

export function boot(THREE) {
  window.__hf = window.__hf || {};
  window.__hf.buildReady = window.__hf.buildReady || {};
  let renderAt = () => {};
  // v5: the film's time tn → the story's old time (js/tmap.js stretches the holds); ambient motion keeps the film's time
  const seek = (tn) => {
    const old = window.__tOld || ((x) => x), to = old(tn); if (to < (window.__BODY_FROM ?? -1)) return;
    const T0 = window.__T0 || 0, rate = (to - old(tn - 1 / 30)) * 30;   // story seconds per film second at tn (< 1 in a stretched hold)
    renderAt(T0 + to, T0 + tn, rate);
  };
  const ready = build(THREE).then((fn) => { renderAt = fn; seek(window.__hfThreeTime || 0); if (window.__introReady) window.__introReady(); },
    (e) => { console.error("intro-world: build failed:", e && e.stack || e); throw e; });   // never a silent black film
  if (!window.__introReady) window.__hf.buildReady["intro-world"] = ready;
  window.addEventListener("hf-seek", (e) => seek(e.detail.time));
}

async function build(THREE) {
  const DATA = await (await fetch("assets/data.json")).json();
  const { id: FXID, P } = readPreset();
  let BEATS = null; try { const r = await fetch("audio/music.beats.json"); if (r.ok) BEATS = await r.json(); } catch (e) {}
  const PUL = makePulses(BEATS, bar);
  let ONSCREEN = [];
  try { const r = await fetch("audio/onscreen-code.txt"); if (r.ok) ONSCREEN = (await r.text()).split("\n").filter((l) => l.trim()); } catch (e) {}
  let WAVE = null;
  try { const r = await fetch("assets/wave.json"); if (r.ok) WAVE = await r.json(); } catch (e) {}
  await document.fonts.ready;

  const canvas = document.getElementById("gl");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(1);
  renderer.setSize(1920, 1080, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const BG = new THREE.Color(0x08090a);
  scene.background = BG;
  scene.fog = new THREE.FogExp2(0x101114, 0.02);
  const camera = new THREE.PerspectiveCamera(40, 1920 / 1080, 0.05, 900);

  const loader = new THREE.TextureLoader();
  const loadTex = (url) => new Promise((res) => loader.load(url, (tx) => { tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8; res(tx); }, undefined, () => res(null)));
  const [atlas, selfSheet, sb02, draft02, loop02] = await Promise.all(["atlas.jpg", "self-sheet.png", "02-storyboard.png", "02-draft-sheet.png", "02-loop.png"].map((f) => loadTex("assets/tex/" + f)));
  // the gates show the request's own artifacts (showcase 02, the vertical short the terminal asked for; tools/request_tex.py)
  const outlineTex = (() => { // gate ① art: 02's outline, its STORYBOARD.md shot list (texture, not a read)
    const c = document.createElement("canvas"); c.width = 1600; c.height = 900; const g = c.getContext("2d");
    g.fillStyle = "#0d0d10"; g.fillRect(0, 0, 1600, 900); g.strokeStyle = "#3a3a40"; g.lineWidth = 4; g.strokeRect(2, 2, 1596, 896);
    g.fillStyle = "#8b8b94"; g.font = '400 40px "SF Mono", Menlo, monospace'; g.fillText("BRIEF.md · outline · 02 低轨卫星的多普勒", 90, 110);
    const rows = [["S1", "钩子", "卫星信号会变调"], ["S2", "飞得快", "低轨卫星，飞得极快"], ["S3", "靠近", "波变密，频率升高"], ["S4", "过顶", "频移归零"], ["S5", "远离", "波变疏，频率降低"], ["S6", "量级", "2 GHz ±50 kHz；20 GHz 再大 10 倍"], ["S7", "补偿", "轨道已知，能提前算出"]];   // showcase/02's STORYBOARD.md shots
    rows.forEach(([n, a, r], i) => { const y = 215 + i * 96; g.fillStyle = "#FFB224"; g.font = '500 46px "SF Mono", Menlo, monospace'; g.fillText(n, 90, y);
      g.fillStyle = "#EDEDEF"; g.font = '500 52px "PingFang SC", sans-serif'; g.fillText(a, 190, y);
      g.fillStyle = "#C4C4CC"; g.font = '400 48px "PingFang SC", sans-serif'; g.fillText(r, 520, y); });
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8; return tx; })();

  // ---------- text planes (canvas → texture) ----------
  const FONT_EN = '"SF Pro Display", system-ui, -apple-system, sans-serif';
  const FONT_ZH = '"PingFang SC", "Hiragino Sans GB", sans-serif';
  const FONT_MONO = '"SF Mono", "LF Mono", Menlo, monospace';
  // lines: [{text, size(px), weight, font, color, track(em)}]; h = world height per 100 px
  function textPlane(lines, { pxPerUnit = 100, width = 0, align = "center", pad = 24, lineGap = 0.28, fog = false } = {}) {
    const c = document.createElement("canvas"), g = c.getContext("2d");
    const fontStr = (l) => `${l.weight || 600} ${l.size}px ${l.font || FONT_EN}`;
    let w = 0, h = pad * 2;
    const metrics = lines.map((l, i) => { g.font = fontStr(l); g.letterSpacing = "0px"; const m = g.measureText(l.text); const lw = m.width + Math.abs(l.track || 0) * l.size * l.text.length; w = Math.max(w, lw); h += l.size * 1.12 + (i ? l.size * lineGap : 0); return lw; });
    c.width = Math.ceil(w + pad * 2); c.height = Math.ceil(h);
    let y = pad;
    lines.forEach((l, i) => {
      if (i) y += l.size * lineGap;
      g.font = fontStr(l); g.fillStyle = l.color || FG; g.textBaseline = "top";
      if (l.track) g.letterSpacing = `${l.track}em`; else g.letterSpacing = "0px";
      const x = align === "center" ? (c.width - metrics[i]) / 2 : align === "right" ? c.width - pad - metrics[i] : pad;
      g.fillText(l.text, x, y + l.size * 0.06);
      y += l.size * 1.12;
    });
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8; tx.minFilter = THREE.LinearMipmapLinearFilter;
    const mat = new THREE.MeshBasicMaterial({ map: tx, transparent: true, depthWrite: false, fog, toneMapped: false, opacity: 0 });
    if (width) pxPerUnit = c.width / width;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(c.width / pxPerUnit, c.height / pxPerUnit), mat);
    mesh.userData.base = mesh.position.clone();
    return mesh;
  }
  const onTop = (m) => { m.material.depthTest = false; m.renderOrder = 10; return m; };
  const quietTex = (() => { const c = document.createElement("canvas"); c.width = 256; c.height = 128; const g = c.getContext("2d");
    // an ellipse that fades to nothing on all four sides (the old circle was cut by the canvas top and bottom: it read as a box)
    const gr = g.createRadialGradient(128, 128, 8, 128, 128, 128); gr.addColorStop(0, "rgba(6,7,8,0.94)"); gr.addColorStop(0.62, "rgba(6,7,8,0.82)"); gr.addColorStop(1, "rgba(6,7,8,0)");
    g.setTransform(1, 0, 0, 0.5, 0, 0); g.fillStyle = gr; g.fillRect(0, 0, 256, 256); const tx = new THREE.CanvasTexture(c); return tx; })();
  function quiet(m, k = 1.5) { // the background goes quiet under big type (a soft dark plate behind it, in the world)
    const w = m.geometry.parameters.width, h = m.geometry.parameters.height;
    const q = new THREE.Mesh(new THREE.PlaneGeometry(w * k, h * (k + 0.5)), new THREE.MeshBasicMaterial({ map: quietTex, transparent: true, opacity: 0, depthTest: false, depthWrite: false, toneMapped: false }));
    q.renderOrder = 9; q.position.z = -0.02; m.add(q); m.userData.quiet = q; return m;
  }
  const fontStr = (l) => `${l.weight || 600} ${l.size}px ${l.font || FONT_EN}`;
  let dynSeed = 1;
  function dynPlane(lines, { pxPerUnit = 100, lineGap = 0.4, decodeDur = 0.2 } = {}) { // decode/scramble type (v3); falls back to a static look when P.decode = 0
    const D = makeDynText(THREE, lines, { lineGap, fontStr, spread: P.decode ? 0.22 : 0.0001, seed: (dynSeed += 17), decodeDur });
    const mat = textMaterial(THREE, D.tex); mat.depthTest = false;
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(D.canvas.width / pxPerUnit, D.canvas.height / pxPerUnit), mat);
    mesh.renderOrder = 10; mesh.userData.base = mesh.position.clone(); mesh.userData.dyn = D; mesh.userData.contentFrac = D.contentFrac; return mesh;
  }
  const hero = (en, zh, { enSize = 150, zhSize = 0, enColor = FG } = {}) =>
    quiet(dynPlane([...en.split("\n").map((l) => ({ text: l, size: enSize, weight: 600, color: enColor, track: -0.025 })), ...(zh ? [{ text: zh, size: zhSize || Math.round(enSize * 0.62), weight: 500, font: FONT_ZH, color: "#D6D6DC" }] : [])]));
  // kinetic "slam": rise + settle scale on entry (easeOutExpo), fade out at exit
  const NODEC = { decode: 0 };   // draw state for type that lands without the decode scramble
  function slam(m, t, tIn, tOut, { rise = 0.25, sc = 1.08, fi = 0.5, fo = 0.6, maxO = 1, nodec = 0 } = {}) {
    const u = eOutExpo(seg(t, tIn, tIn + 0.9));
    m.material.opacity = maxO * win(t, tIn, tOut, fi, fo);
    m.visible = m.material.opacity > 0.001;
    if (m.userData.quiet) m.userData.quiet.material.opacity = 0.62 * m.material.opacity;
    const b = m.userData.base;
    m.userData.riseOff = rise * (1 - u);
    m.position.set(b.x, b.y - m.userData.riseOff, b.z);
    const s = lerp(sc, 1, u) * (m.userData.fit || 1); m.scale.set(s, s, 1);
    const D = m.userData.dyn;
    if (D && m.visible) {
      D.draw(t - tIn, nodec ? NODEC : P);
      const U = m.material.uniforms;
      U.uSweep.value = P.sweep ? lerp(-0.25, 1.25, seg(t, tIn + 0.35, tIn + 1.05)) : -1;
      U.uGlitch.value = P.glitchExit * seg(t, tOut - 0.22, tOut) + (P.glitchFrame ? 0.25 * seg(t, tIn, tIn + 0.12) * (1 - seg(t, tIn + 0.12, tIn + 0.3)) : 0);
      U.uFrame.value = Math.round(t * FPS);
    }
  }
  const _f = new THREE.Vector3(), _u = new THREE.Vector3(), _r = new THREE.Vector3();
  function rideView(m, d, frac, dx = 0, dy = 0) {
    if (m.parent !== scene) scene.add(m); // camera-stable text lives in world space, not in the lane frame
    _f.set(0, 0, -1).applyQuaternion(camera.quaternion); _u.set(0, 1, 0).applyQuaternion(camera.quaternion); _r.set(1, 0, 0).applyQuaternion(camera.quaternion);
    const visW = 2 * d * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect;
    const fit = frac * visW / (m.geometry.parameters.width * (m.userData.contentFrac || 1)), s = m.scale.x / (m.userData.fit || 1) * fit;
    m.userData.fit = fit; m.scale.set(s, s, 1);
    m.position.copy(camera.position).addScaledVector(_f, d).addScaledVector(_u, dy * visW / camera.aspect / 2 - (m.userData.riseOff || 0) * 0.3).addScaledVector(_r, dx * visW / 2);
    m.quaternion.copy(camera.quaternion);
  }
  const slamView = (m, t, tIn, tOut, d, frac, dx = 0, dy = 0, nodec = 0) => { slam(m, t, tIn, tOut, { fo: 0.35, nodec }); if (m.visible) rideView(m, d, frac, dx, dy); };
  // pin: a camera-facing label anchored to a world point, sized in screen pixels (k = screen px per canvas px),
  // offset (dx, dy) in screen px; ax/ay choose which edge of the label sits on the offset point. Returns a near-fade 0..1.
  const _pf = new THREE.Vector3(), _pu = new THREE.Vector3(), _pr = new THREE.Vector3(), _pd = new THREE.Vector3();
  function pin(m, a, { dx = 0, dy = 0, ax = "c", ay = "c", k = 1 } = {}) {
    if (m.parent !== scene) scene.add(m);
    _pf.set(0, 0, -1).applyQuaternion(camera.quaternion); _pu.set(0, 1, 0).applyQuaternion(camera.quaternion); _pr.set(1, 0, 0).applyQuaternion(camera.quaternion);
    const d = _pd.copy(a).sub(camera.position).dot(_pf);
    if (d < 0.8) return 0;
    const wpp = 2 * d * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) / 1080;
    const img = m.userData.dyn ? m.userData.dyn.canvas : m.material.map.image, cw = img.width, ch = img.height;
    const s = k * wpp * cw / m.geometry.parameters.width; m.scale.set(s, s, 1);
    const wpx = (m.userData.contentFrac || 1) * cw * k, hpx = ch * k;
    let ox = dx + (ax === "l" ? wpx / 2 : ax === "r" ? -wpx / 2 : 0), oy = dy + (ay === "b" ? hpx / 2 : ay === "t" ? -hpx / 2 : 0);
    // keep the whole label inside the graphics-safe box (x 96–1824, y 54–1026): slide it along the frame edge
    const sx = _pd.copy(a).project(camera).x * 960, sy = _pd.y * 540;
    const hw = wpx / 2 - 24 * k, hh = hpx / 2 - 20 * k;
    const ox0 = ox, oy0 = oy;
    ox = clamp(sx + ox, -864 + hw, 864 - hw) - sx; oy = clamp(sy + oy, -486 + hh, 486 - hh) - sy;
    const pushed = Math.hypot(ox - ox0, oy - oy0); // a label shoved far from its node belongs to a node that is leaving: fade it
    m.position.copy(a).addScaledVector(_pr, ox * wpp).addScaledVector(_pu, oy * wpp);
    m.quaternion.copy(camera.quaternion);
    // a label whose node has left the frame fades out instead of piling up against the edge
    const out = Math.max(Math.abs(sx) - 900, Math.abs(sy) - 500, 0);
    return clamp((d - 0.8) / 2.5) * clamp(1 - out / 80) * clamp(1 - (pushed - 50) / 90);
  }
  const ride = (m, t, tIn, tOut, d0, d1) => { const u = seg(t, tIn - 0.5, tOut); m.position.z = camera.position.z - lerp(d0, d1, u); };
  const place = (m, x, y, z, ry = 0, parent = scene) => { m.position.set(x, y, z); m.rotation.y = ry; m.userData.base = m.position.clone(); parent.add(m); return m; };

  // ---------- glow sprites ----------
  function radialTex(inner = "rgba(255,240,210,1)", mid = "rgba(255,178,36,0.55)") {
    const c = document.createElement("canvas"); c.width = c.height = 128; const g = c.getContext("2d");
    const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64);
    gr.addColorStop(0, inner); gr.addColorStop(0.18, mid); gr.addColorStop(1, "rgba(255,178,36,0)");
    g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
  }
  const glowTex = radialTex();
  const softTex = radialTex("rgba(255,190,90,0.35)", "rgba(255,178,36,0.12)");
  const neutralTex = (() => { const c = document.createElement("canvas"); c.width = c.height = 128; const g = c.getContext("2d"); const gr = g.createRadialGradient(64, 64, 0, 64, 64, 64); gr.addColorStop(0, "rgba(210,214,222,0.35)"); gr.addColorStop(0.3, "rgba(170,176,188,0.12)"); gr.addColorStop(1, "rgba(150,156,170,0)"); g.fillStyle = gr; g.fillRect(0, 0, 128, 128); const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx; })();
  const sprite = (tex = glowTex, s = 1) => { const m = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, fog: false, toneMapped: false })); m.scale.set(s, s, 1); scene.add(m); return m; };
  // vertical light shaft (volumetric feel): additive gradient plane
  function shaftTex() {
    const c = document.createElement("canvas"); c.width = 64; c.height = 256; const g = c.getContext("2d");
    const gr = g.createLinearGradient(0, 0, 0, 256); gr.addColorStop(0, "rgba(255,200,120,0.0)"); gr.addColorStop(0.35, "rgba(255,190,100,0.35)"); gr.addColorStop(1, "rgba(255,178,36,0.0)");
    g.fillStyle = gr; g.fillRect(0, 0, 64, 256);
    const gx = g.createLinearGradient(0, 0, 64, 0); gx.addColorStop(0, "rgba(0,0,0,1)"); gx.addColorStop(0.5, "rgba(0,0,0,0)"); gx.addColorStop(1, "rgba(0,0,0,1)");
    g.globalCompositeOperation = "destination-out"; g.fillStyle = gx; g.fillRect(0, 0, 64, 256);
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
  }
  const shaftT = shaftTex();
  const shaft = (w, h) => new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: shaftT, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, fog: false, toneMapped: false, opacity: 0 }));

  // emissive bar (lines of light); color multiplied above 1 so bloom picks it up
  const barMat = (k = 2.2) => new THREE.MeshBasicMaterial({ color: new THREE.Color(AMBER[0] * k, AMBER[1] * k, AMBER[2] * k), toneMapped: false, fog: false, transparent: true, opacity: 1 });
  const setAmber = (mat, k) => mat.color.setRGB(AMBER[0] * k, AMBER[1] * k, AMBER[2] * k);

  // ---------- frame plates (instanced; atlas of real showcase frames) ----------
  function plateMaterial() {
    return new THREE.ShaderMaterial({
      uniforms: { uAtlas: { value: atlas }, uTime: { value: 0 }, uFog: { value: 0.02 }, uFogColor: { value: new THREE.Color(0x101114) }, uFlicker: { value: 0 }, uGlobal: { value: 1 }, uLitGain: { value: 0.35 } },
      vertexShader: `attribute vec2 aCell; attribute float aLit; attribute float aSeed;
        varying vec2 vUv; varying vec2 vCell; varying float vLit; varying float vSeed; varying float vDepth;
        void main(){ vUv=uv; vCell=aCell; vLit=aLit; vSeed=aSeed; vec4 mv=modelViewMatrix*instanceMatrix*vec4(position,1.0); vDepth=-mv.z; gl_Position=projectionMatrix*mv; }`,
      fragmentShader: `uniform sampler2D uAtlas; uniform float uTime, uFog, uFlicker, uGlobal, uLitGain; uniform vec3 uFogColor;
        varying vec2 vUv; varying vec2 vCell; varying float vLit; varying float vSeed; varying float vDepth;
        float h(float n){ return fract(sin(n)*43758.5453); }
        void main(){
          vec2 auv = vec2((vCell.x + vUv.x)/8.0, 1.0 - (vCell.y + 1.0 - vUv.y)/8.0);
          vec3 img = texture2D(uAtlas, auv).rgb;
          float age = uTime - vLit; float lit = step(0.0, age);
          float flash = lit * exp(-max(age,0.0)/0.30);
          float fl = 1.0 - uFlicker * step(0.55, h(vSeed*91.7 + floor(uTime*15.0)*7.13));
          float b = (lit * uLitGain + 1.1 * flash) * fl;
          float d = min(min(vUv.x, 1.0 - vUv.x) * 1.7778, min(vUv.y, 1.0 - vUv.y));
          float edge = 1.0 - smoothstep(0.0, 0.018, d);
          vec3 col = img * b + edge * (vec3(0.13,0.13,0.15) + vec3(1.0,0.7,0.14) * flash * 0.9);
          col *= uGlobal;
          float f = 1.0 - exp(-uFog*uFog*vDepth*vDepth);
          gl_FragColor = vec4(mix(col, uFogColor * uGlobal, f), 1.0);
        }`,
    });
  }
  function plateField(list) {
    const geo = new THREE.PlaneGeometry(1.6, 0.9);
    const mat = plateMaterial();
    const mesh = new THREE.InstancedMesh(geo, mat, list.length);
    const cell = new Float32Array(list.length * 2), lit = new Float32Array(list.length), seed = new Float32Array(list.length);
    const o = new THREE.Object3D();
    list.forEach((p, i) => { o.position.set(p.x, p.y, p.z); o.rotation.set(0, p.ry || 0, 0); o.scale.setScalar(p.s || 1); o.updateMatrix(); mesh.setMatrixAt(i, o.matrix); cell[2 * i] = p.cx; cell[2 * i + 1] = p.cy; lit[i] = p.lit; seed[i] = i + 0.5; });
    geo.setAttribute("aCell", new THREE.InstancedBufferAttribute(cell, 2));
    geo.setAttribute("aLit", new THREE.InstancedBufferAttribute(lit, 1));
    geo.setAttribute("aSeed", new THREE.InstancedBufferAttribute(seed, 1));
    mesh.frustumCulled = false; scene.add(mesh); return mesh;
  }

  // =====================================================================
  // WORLD
  // =====================================================================
  // --- the t-axis: a line of light from the spark at the origin, running to -z ---
  const axisMat = barMat(2.4);
  const axis = new THREE.Mesh(new THREE.BoxGeometry(0.014, 0.014, 1), axisMat); scene.add(axis);
  const axisGlowMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.55, 0.36, 0.08), blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, fog: false, toneMapped: false });
  const axisGlow = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.035, 1), axisGlowMat); scene.add(axisGlow);
  const spark = sprite(glowTex, 0.6);
  const sparkHalo = sprite(softTex, 1.2);

  // --- S1: the archive of frames (corridor) ---
  const plates1 = [];
  for (let k = 0; k < 64; k++) for (let side = -1; side <= 1; side += 2) for (let c = 0; c < 5; c++) for (let r = 0; r < 5; r++) {
    const i = plates1.length, hz = hash(i * 3.1);
    const x = side * (3.2 + c * 1.9 + (hz - 0.5) * 0.3), y = -1.4 + r * 1.08, z = -4 - k * 1.7 - hash(i) * 0.4;
    // near frames tick in on the 16th grid of bar 2; the rest ripple outward during the reveal
    const litT = k < 10 ? bar(2) + Math.floor(hash(i * 7.7) * 15) * S16 + S16 : q16(bar(3) + k * 0.075 + hash(i * 5.3) * 0.9);
    const cellI = Math.floor(hash(i * 1.37) * 64);
    plates1.push({ x, y, z, ry: side * -0.32, cx: cellI % 8, cy: Math.floor(cellI / 8), lit: litT });
  }
  const field1 = plateField(plates1);

  // floor grid (blueprint), faint
  const grid = new THREE.GridHelper(2400, 600, 0x1c1d21, 0x141518); grid.position.set(0, -2.2, -600); grid.material.transparent = true; grid.material.opacity = 0.8; scene.add(grid);

  // dust: seeded points drifting as a function of t (depth + parallax), along the whole path
  const NDUST = 7000, dpos = new Float32Array(NDUST * 3), dvel = [];
  for (let i = 0; i < NDUST; i++) { dpos[3 * i] = (hash(i * 1.1) - 0.5) * 60; dpos[3 * i + 1] = (hash(i * 2.3) - 0.3) * 22; dpos[3 * i + 2] = 20 - hash(i * 3.7) * 720; dvel.push([(hash(i * 4.1) - 0.5) * 0.08, (hash(i * 5.9) - 0.5) * 0.05]); }
  const dustGeo = new THREE.BufferGeometry(); dustGeo.setAttribute("position", new THREE.BufferAttribute(dpos.slice(), 3));
  const dust = new THREE.Points(dustGeo, new THREE.PointsMaterial({ size: 0.035, color: 0x9a8f7a, transparent: true, opacity: 0.55, depthWrite: false, sizeAttenuation: true, fog: true }));
  dust.frustumCulled = false; scene.add(dust);

  // S1 type
  const fx = place(quiet(dynPlane([{ text: "// OpenVideoHarness", size: 60, weight: 400, font: FONT_MONO, color: "#C9A25A" }, { text: "frame = f(t)", size: 96, weight: 400, font: FONT_MONO, color: "#FFD27A" }], { pxPerUnit: 400, lineGap: 0.3 })), 0.0, 0.16, -2.2);
  const T1 = place(hero("EVERY FRAME", null, { enSize: 220 }), 0, 1.7, -36);
  const T2 = place(hero("IS A FUNCTION OF TIME", "每一帧，都是时间的函数。", { enSize: 170 }), 0, 1.55, -66);

  // --- S2: the program (request → code canyon → film) ---
  const req = (() => {
    const c = document.createElement("canvas"), g = c.getContext("2d");
    const L = [
      { t: "REQUEST · showcase/02-short-leo-doppler", f: `400 38px ${FONT_MONO}`, col: "#9A9AA3", h: 38 },
      { t: "为什么低轨卫星的信号会“变调”？——多普勒频移", f: `500 96px ${FONT_ZH}`, col: "#F2F2F4", h: 96 },
      { t: "Why does a LEO satellite's signal change pitch?", f: `400 88px ${FONT_EN}`, col: "#C6C6CD", h: 88 },
    ];
    let w = 0; L.forEach((l) => { g.font = l.f; w = Math.max(w, g.measureText(l.t).width); });
    c.width = Math.ceil(w + 180); c.height = 470; g.fillStyle = "rgba(17,17,19,0.94)"; g.fillRect(0, 0, c.width, c.height);
    g.strokeStyle = "#3f3f46"; g.lineWidth = 3; g.strokeRect(1.5, 1.5, c.width - 3, c.height - 3);
    g.fillStyle = "#FFB224"; g.fillRect(40, 40, 12, c.height - 80);
    let y = 58; L.forEach((l, i) => { g.font = l.f; g.fillStyle = l.col; g.textBaseline = "top"; g.fillText(l.t, 96, y); y += l.h * 1.25 + (i === 0 ? 26 : 18); });
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; tx.anisotropy = 8;
    const W = 6.6, m = new THREE.Mesh(new THREE.PlaneGeometry(W, W * c.height / c.width), new THREE.MeshBasicMaterial({ map: tx, transparent: true, opacity: 0, depthTest: false, toneMapped: false, fog: false }));
    m.renderOrder = 12; scene.add(m); m.userData.base = m.position.clone(); return m;
  })();
  // code walls: real lines of showcase/02 draw(t), in strips that type in on the 16th grid
  const codeStrips = [];
  const CODE = DATA.code;
  for (let side = -1; side <= 1; side += 2) {
    for (let sidx = 0; sidx < 7; sidx++) {
      const lines = CODE.slice((side < 0 ? 0 : 50) + sidx * 7, (side < 0 ? 0 : 50) + sidx * 7 + 7).map((l) => ({ text: l || " ", size: 30, weight: 400, font: FONT_MONO, color: "#D9D9E0" }));
      const m = textPlane(lines, { pxPerUnit: 130, align: "left", lineGap: 0.22, fog: true });
      m.material.fog = true;
      place(m, side * 3.7, 1.5, -84 - sidx * 6.4, side * -1.38);
      m.userData.tIn = q16(bar(5) + (sidx * 0.3 + (side > 0 ? 0.15 : 0)));
      codeStrips.push(m);
    }
  }
  const T34 = place(hero("Claude Opus 5.5 doesn't paint pixels.\nIt writes the program.", "Claude Opus 5.5 不直接画像素。它写程序。", { enSize: 140 }), 0, 1.55, -102);
  // the film assembles from tiles, then plays (vertical screen = showcase 02)
  const VIDTEX = [];
  const v02a = document.getElementById("v02a");
  const tex02a = new THREE.VideoTexture(v02a); tex02a.colorSpace = THREE.SRGBColorSpace; VIDTEX.push(tex02a);
  const SCR2 = { x: 0.9, y: 1.05, z: -142, w: 2.6, h: 4.62 };
  const tiles2 = [];
  const TCOLS = 6, TROWS = 10;
  for (let r = 0; r < TROWS; r++) for (let c = 0; c < TCOLS; c++) {
    const g = new THREE.PlaneGeometry(SCR2.w / TCOLS, SCR2.h / TROWS);
    const uv = g.attributes.uv; for (let i = 0; i < uv.count; i++) uv.setXY(i, (c + uv.getX(i)) / TCOLS, 1 - (r + 1 - uv.getY(i)) / TROWS);
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: tex02a, transparent: true, opacity: 0, toneMapped: false, fog: false }));
    const i = tiles2.length;
    m.userData.home = new THREE.Vector3(SCR2.x - SCR2.w / 2 + (c + 0.5) * SCR2.w / TCOLS, SCR2.y + SCR2.h / 2 - (r + 0.5) * SCR2.h / TROWS, SCR2.z);
    m.userData.from = new THREE.Vector3((hash(i * 2.2) - 0.5) * 9, (hash(i * 3.3) - 0.3) * 6, SCR2.z + 6 + hash(i * 4.4) * 14);
    m.userData.tIn = bar(6) + Math.floor(hash(i * 9.1) * 4) * S16; // lands in scrambled order on the 16ths of 6:1
    scene.add(m); tiles2.push(m);
  }
  const scr2Frame = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(SCR2.w + 0.04, SCR2.h + 0.04)), new THREE.LineBasicMaterial({ color: 0x3a3a40, transparent: true, opacity: 0 }));
  scr2Frame.position.set(SCR2.x, SCR2.y, SCR2.z - 0.01); scene.add(scr2Frame);
  const T5 = place(hero("One sentence in.\nA film out.", "一句话进去，一支片子出来。", { enSize: 150 }), -2.95, 1.35, -141.6, 0.25);

  // --- S3: the problem (unstable archive, three failures stamped FAIL) ---
  const plates3 = [];
  for (let k = 0; k < 26; k++) for (let side = -1; side <= 1; side += 2) for (let c = 0; c < 3; c++) for (let r = 0; r < 5; r++) {
    const i = plates3.length;
    plates3.push({ x: side * (3.4 + c * 1.9), y: -1.4 + r * 1.08, z: -146 - k * 1.8, ry: side * -0.3, cx: Math.floor(hash(i * 8.8) * 8), cy: Math.floor(hash(i * 6.6) * 8), lit: -10 });
  }
  const field3 = plateField(plates3);
  function failCanvas(kind, greyed = false) {
    const c = document.createElement("canvas"); c.width = 800; c.height = 450; const g = c.getContext("2d");
    if (greyed) g.filter = "grayscale(1) brightness(0.55)";
    g.fillStyle = "#101012"; g.fillRect(0, 0, 800, 450);
    if (kind === 11) { // everything dumped on screen at once, then frozen
      g.fillStyle = "#cfcfd6"; g.font = `500 26px ${FONT_EN}`;
      const words = ["8 video types", "3 review gates", "20 taste checks", "10 stages", "HyperFrames", "Manim", "p5.brush", "Remotion", "reads", "contact sheets", "strips", "crops", "−14 LUFS", "safe box", "easing", "captions", "beat map", "storyboard"];
      for (let i = 0; i < 36; i++) g.fillText(words[i % words.length], 20 + (i % 3) * 262, 40 + Math.floor(i / 3) * 34);
    } else if (kind === 10) { // the slop look, on purpose
      const gr = g.createLinearGradient(0, 0, 800, 450); gr.addColorStop(0, "#6d28d9"); gr.addColorStop(1, "#06b6d4"); g.fillStyle = gr; g.fillRect(0, 0, 800, 450);
      const rg = g.createRadialGradient(400, 225, 10, 400, 225, 230); rg.addColorStop(0, "rgba(255,255,255,0.9)"); rg.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = rg; g.fillRect(0, 0, 800, 450);
      g.fillStyle = "#fff"; g.font = `700 64px ${FONT_EN}`; g.textAlign = "center"; g.fillText("✨ AI-powered ✨", 400, 250);
    } else { // a wrong number
      g.fillStyle = "#000"; g.fillRect(0, 0, 800, 450);
      g.strokeStyle = "#ffff00"; g.lineWidth = 4; g.beginPath(); g.moveTo(40, 330); g.lineTo(120, 330); g.lineTo(125, 90); g.lineTo(132, 150); g.lineTo(140, 110); for (let x = 140; x < 760; x += 10) g.lineTo(x, 118 + Math.sin(x * 0.3) * 6 * Math.exp(-(x - 140) / 120)); g.stroke();
      g.fillStyle = "#FC6255"; g.font = `500 44px ${FONT_EN}`; g.fillText("overshoot ≈ 18% of the jump", 200, 260);
    }
    const tx = new THREE.CanvasTexture(c); tx.colorSpace = THREE.SRGBColorSpace; return tx;
  }
  const fails = [11, 10, 19].map((kind, i) => {
    const grp = new THREE.Group();
    const grey = failCanvas(kind, true);
    const img = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 1.35), new THREE.MeshBasicMaterial({ map: failCanvas(kind), transparent: true, opacity: 0, toneMapped: false, fog: false }));
    const stamp = textPlane([{ text: `#${kind} FAIL`, size: 64, weight: 600, font: FONT_MONO, color: AMB, track: 0.04 }], { width: 1.7 });
    [img, stamp].forEach((mm) => { mm.material.depthTest = false; mm.renderOrder = 11; });
    stamp.position.set(0, -0.33, 0.02); stamp.userData.base = stamp.position.clone();
    const box = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(2.48, 1.43)), new THREE.LineBasicMaterial({ color: new THREE.Color(AMBER[0] * 2, AMBER[1] * 2, AMBER[2] * 2), transparent: true, opacity: 0, toneMapped: false }));
    grp.add(img, stamp, box);
    grp.userData.x = [-2.6, 0, 2.6][i]; scene.add(grp);
    return { grp, img, stamp, box, grey, col: img.material.map, tIn: bar(7, 1 + i) };
  });
  const T6 = place(hero("Stunning, once.", "惊艳，一次。", { enSize: 150 }), 0, 2.25, -172);
  const T7 = place(hero("Dependable? Not yet.", "稳定？还不行。", { enSize: 150 }), 0, 1.75, -188);

  // --- S4: the harness appears (rings of light) ---
  const rings = [];
  for (let i = 0; i < 9; i++) {
    const g = new THREE.Group(); const W = 17, H = 9.56, T = 0.07, mat = barMat(0);
    [[0, H / 2, W, T], [0, -H / 2, W, T], [-W / 2, 0, T, H], [W / 2, 0, T, H]].forEach(([x, y, w, h]) => { const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, T), mat); b.position.set(x, y, 0); g.add(b); });
    g.position.set(0, 2.2, -202 - i * 5.6); g.userData.mat = mat; g.userData.tIn = bar(9) + i * S16 * 0.5; scene.add(g); rings.push(g);
  }
  const shafts4 = [];
  for (let i = 0; i < 6; i++) { const s = shaft(3.2, 16); s.position.set((i - 2.5) * 3.1, 4.5, -206 - i * 1.3); scene.add(s); shafts4.push(s); }
  const T8 = place(dynPlane([
    { text: "OpenVideoHarness", size: 270, weight: 600, color: FG, track: -0.03 },
    { text: "turns Claude Code & Codex into a video studio", size: 104, weight: 400, color: "#D8D8DE" },
    { text: "把 Claude Code 和 Codex 变成一间视频工作室", size: 96, weight: 500, font: FONT_ZH, color: "#DADAE0" },
  ], { lineGap: 0.36 }), 0, 1.95, -206); quiet(T8, 1.3);

  // =====================================================================
  // CAMERA keyframes (t, position, look-at, fov); Hermite through real time; "stop" keys hold still
  // =====================================================================
  const V = (x, y, z) => new THREE.Vector3(x, y, z);
  const K = [];
  const key = (t, p, l, fov = 40, stop = false, tm = null) => K.push({ t, p, l, fov, stop, tm });

  // --- S5–S8 live in their own modules (they add their camera keys) ---
  const film02 = new THREE.VideoTexture(document.getElementById("v02k")); film02.colorSpace = THREE.SRGBColorSpace; VIDTEX.push(film02);   // the final cut: 02 itself
  const X = { gateTex: { R1: outlineTex, R2: sb02, R3: draft02, K: film02, LOOP: loop02 }, scene, key, V, textPlane, dynPlane, quiet, hero, slamView, barMat, setAmber, sprite, glowTex, softTex, FONT_MONO, FONT_ZH, FONT_EN, P, bar, BEAT, S16, seg, win, lerp, eOutExpo, eOutCubic, eInOut, clamp, hash, pin, tubeMat, WAVE, DUR };
  const ARCH = buildArch(THREE, X);
  const PIPE = buildPipeline(THREE, X);
  const FEAT = buildFeatures(THREE, X);

  // --- S9–S11 frame of reference: the old lane-02 frame, re-anchored after the star map ---
  const FORK = new THREE.Vector3(28.6, 0, -491);
  const A2 = THREE.MathUtils.degToRad(-25), D2 = new THREE.Vector3(Math.sin(A2), 0, -Math.cos(A2)), R2 = new THREE.Vector3(Math.cos(A2), 0, Math.sin(A2));
  const L2 = (x, y, s) => FORK.clone().addScaledVector(D2, s).addScaledVector(R2, x).setY(y);
  const lane2 = new THREE.Group(); lane2.position.copy(FORK); lane2.rotation.y = -A2; scene.add(lane2);
  const inLane = (m, x, y, s, ry = 0) => { m.position.set(x, y, -s); m.rotation.y = ry; m.userData.base = m.position.clone(); lane2.add(m); return m; };

  // --- S9: the proof hall: four monolith screens (real showcase films as video textures), one every 3 beats ---
  const HX = 9.5, FD = 3 * BEAT;
  const vt = (id) => { const tx = new THREE.VideoTexture(document.getElementById(id)); tx.colorSpace = THREE.SRGBColorSpace; VIDTEX.push(tx); return tx; };
  const MON = [
    { id: "v01", x: HX - 6.8, y: 2.3, s: 100, ry: 0.42, w: 7.2, h: 4.05, n: "01", type: "HAND-DRAWN SHORT", meta: "p5.brush · 12 s · 1080p24 | 57 s render · 3 review rounds", tFocus: bar(24, 0) },
    { id: "v03", x: HX + 6.8, y: 2.6, s: 116, ry: -0.42, w: 7.2, h: 4.05, n: "03", type: "3B1B-STYLE MATH EXPLAINER", meta: "Manim CE 0.21 · 25 s · 1080p30 | 24 s render", tFocus: bar(24, 3) },
    { id: "v02", x: HX - 5.6, y: 3.1, s: 132, ry: 0.38, w: 3.3, h: 5.87, n: "02", type: "VERTICAL SCIENCE SHORT", meta: "HyperFrames · 24.8 s · 1080×1920 | 46 s render", tFocus: bar(25, 2) },
    { id: "v00", x: HX + 6.4, y: 2.3, s: 148, ry: -0.42, w: 7.2, h: 4.05, n: "00", type: "LAUNCH SHORT", meta: "HyperFrames · 20 s · 1920×1080 | ~30 s render", tFocus: bar(26, 1) },
  ].map((m) => {
    const grp = new THREE.Group();
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(m.w, m.h), new THREE.MeshBasicMaterial({ map: vt(m.id), color: new THREE.Color().setScalar(m.id === "v00" ? 0.95 : 1.15), toneMapped: false, fog: false })); // lifted (the films are the evidence); 00 is white-on-black, kept under the bloom threshold
    const frame = new THREE.LineSegments(new THREE.EdgesGeometry(new THREE.PlaneGeometry(m.w + 0.08, m.h + 0.08)), new THREE.LineBasicMaterial({ color: 0x3a3a40, fog: true }));
    const back = new THREE.Mesh(new THREE.BoxGeometry(m.w + 0.3, m.h + 0.3, 0.4), new THREE.MeshBasicMaterial({ color: 0x0c0c0e, fog: true })); back.position.z = -0.25;
    const halo = new THREE.Mesh(new THREE.PlaneGeometry(m.w * 2.6, m.h * 2.6), new THREE.MeshBasicMaterial({ map: neutralTex, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, opacity: 0.0, toneMapped: false, fog: false })); halo.position.z = -0.6;
    grp.add(halo, back, scr, frame);
    const vk = m.h > m.w ? 1.25 : 1; // the vertical film is narrower: its caption gets the same screen size as the others
    const lab = onTop(textPlane([
      { text: `${m.n}  ${m.type}`, size: Math.round(62 * vk), weight: 600, color: FG, track: 0.04 },
      ...m.meta.split(" | ").map((ln) => ({ text: ln, size: Math.round(48 * vk), weight: 400, font: FONT_MONO, color: "#B4B4BC" })),
    ], { pxPerUnit: 160, align: "left", lineGap: 0.35 }));
    lab.position.set(-m.w / 2 + lab.geometry.parameters.width / 2 - 0.1, -m.h / 2 - 0.15 - lab.geometry.parameters.height / 2, 0.05); lab.userData.base = lab.position.clone();
    const sh = shaft(m.w * 0.9, 18); sh.position.set(0, 3.5, -1.2); sh.material.opacity = 0.1; grp.add(sh);
    const pool = new THREE.Mesh(new THREE.PlaneGeometry(m.w * 1.8, m.w * 0.9), new THREE.MeshBasicMaterial({ map: neutralTex, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false, opacity: 0.55, toneMapped: false, fog: false })); pool.rotation.x = -Math.PI / 2; pool.position.set(0, -m.h / 2 - 1.2, 1.2); grp.add(pool);
    grp.add(lab);
    let link = null;
    if (m.id === "v02") { // 02 is the answer to the request typed at the start: say so, in the empty side of the frame
      link = onTop(textPlane([{ text: "The request", size: 64, weight: 600, color: FG, track: -0.01 }, { text: "from the start", size: 64, weight: 600, color: FG, track: -0.01 }, { text: "→ this film.", size: 64, weight: 600, color: FG, track: -0.01 },   // white: amber vanished into the hall's amber streak
        { text: "开头那句需求", size: 54, weight: 500, font: FONT_ZH, color: "#D6D6DC" }, { text: "就是这支片子。", size: 54, weight: 500, font: FONT_ZH, color: "#D6D6DC" }], { pxPerUnit: 150, align: "right", lineGap: 0.28 }));
      link.position.set(-m.w / 2 - 0.45 - link.geometry.parameters.width / 2, 0.9, 0.05); grp.add(link);
    }
    inLane(grp, m.x, m.y, m.s, m.ry);
    return { ...m, grp, scr, halo, lab, link };
  });
  const T13 = inLane(hero("Made by an agent\nfrom this repo's docs alone.", "都是 agent 只照本仓库的文档做的。", { enSize: 150 }), HX, 6.4, 106);

  // --- S10: this film's own contact sheet as a monument; the score as code; S11 the title ---
  const MW = { x: HX, y: 9.8, s: 196, cols: 10, rows: 6, tw: 4.2, th: 2.3625, gap: 0.18 };
  const mwTiles = [];
  const mwTex = selfSheet || atlas;
  for (let r = 0; r < MW.rows; r++) for (let c = 0; c < MW.cols; c++) {
    const i = r * MW.cols + c, g = new THREE.PlaneGeometry(MW.tw, MW.th);
    const uv = g.attributes.uv;
    const cc = selfSheet ? c : i % 8, rr = selfSheet ? r : Math.floor(i / 8) % 8, cols = selfSheet ? MW.cols : 8, rows = selfSheet ? MW.rows : 8;
    for (let k = 0; k < uv.count; k++) uv.setXY(k, (cc + uv.getX(k)) / cols, 1 - (rr + 1 - uv.getY(k)) / rows);
    const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ map: mwTex, toneMapped: false, fog: true, transparent: true, opacity: 0 }));
    inLane(m, MW.x - (MW.cols - 1) / 2 * (MW.tw + MW.gap) + c * (MW.tw + MW.gap), MW.y + (MW.rows - 1) / 2 * (MW.th + MW.gap) - r * (MW.th + MW.gap), MW.s);
    m.userData.tIn = bar(27) + Math.floor(hash(i * 2.9) * 12) * S16 * 0.5;
    { const e = ((c - 4.5) / 3.6) ** 2 + ((r - 2.6) / 2.0) ** 2; m.userData.ell = 0.08 + 0.92 * clamp(e - 0.55); } mwTiles.push(m);
  }
  const T14 = inLane(hero("This film, too.", "这支片子也是。", { enSize: 150 }), HX, 8.6, MW.s - 10);
  const T15 = inLane(hero("Even the soundtrack is code.", "连配乐都是代码。", { enSize: 150 }), HX, 10.05, MW.s - 10);
  const codeLines = (ONSCREEN.length ? ONSCREEN : ["kick: taiko(t)", "bass: sub(root, t)", "hats: shaker(16ths, t)", "lead: additive(odd harmonics, t)"]).slice(0, 4).map((l, i) => {
    const m = textPlane([{ text: l, size: 46, weight: 400, font: FONT_MONO, color: "#D8D8DE" }], { pxPerUnit: 158, align: "left" });
    m.material.depthTest = false; m.renderOrder = 10;
    inLane(m, HX - 4.9 + m.geometry.parameters.width / 2, 8.45 - i * 0.6, MW.s - 9.9);
    m.userData.tIn = bar(28, i); return m;
  });
  const codeMarks = codeLines.map((m, i) => { const b = new THREE.Mesh(new THREE.BoxGeometry(0.04, 0.34, 0.03), barMat(2.2)); lane2.add(b); b.position.set(HX - 5.15, 8.45 - i * 0.6, -(MW.s - 9.85)); return b; });
  // waveform ridge: the music itself, as geometry
  let waveLine = null;
  if (WAVE && WAVE.rms) {
    const N = WAVE.rms.length, pts = [];
    for (let i = 0; i < N; i++) { const x = HX - 9.5 + (19 * i) / (N - 1); const a = WAVE.rms[i]; pts.push(new THREE.Vector3(x, 5.45 + a * 0.7, -(MW.s - 9.6)), new THREE.Vector3(x, 5.45 - a * 0.7, -(MW.s - 9.6))); }
    const g = new THREE.BufferGeometry().setFromPoints(pts);
    waveLine = new THREE.LineSegments(g, new THREE.LineBasicMaterial({ color: new THREE.Color(AMBER[0] * 1.3, AMBER[1] * 1.3, AMBER[2] * 1.3), transparent: true, opacity: 0, toneMapped: false }));
    lane2.add(waveLine);
  }
  const playhead = new THREE.Mesh(new THREE.BoxGeometry(0.035, 1.7, 0.03), barMat(2.6)); lane2.add(playhead);
  const TITLE = inLane(textPlane([{ text: "OpenVideoHarness", size: 220, weight: 600, color: FG, track: -0.03 }], { pxPerUnit: 118 }), HX, 10.35, MW.s - 0.5);
  const TAG = inLane(textPlane([{ text: "Video as code, for coding agents.", size: 100, weight: 400, color: "#D4D4DA" }, { text: "给 coding agent 的视频工作台", size: 100, weight: 400, font: FONT_ZH, color: "#C4C4CC" }], { pxPerUnit: 118, lineGap: 0.35 }), HX, 7.95, MW.s - 0.5);
  const CTA = inLane(textPlane([
    { text: "$ bin/vh new <type> <slug>", size: 86, weight: 400, font: FONT_MONO, color: FG },
    { text: "github.com/ZLHad/OpenVideoHarness", size: 86, weight: 400, font: FONT_MONO, color: AMB },
  ], { pxPerUnit: 118, lineGap: 0.5 }), HX, 5.75, MW.s - 0.5);
  const titleBar = new THREE.Mesh(new THREE.BoxGeometry(0.1, 1.9, 0.05), barMat(1.7)); lane2.add(titleBar);
  // the CTA types in on the score's 8 typing 16ths (29:4 → 30:1.75); same layout as textPlane, so nothing shifts
  const CTA_L = [{ text: "$ bin/vh new <type> <slug>", color: FG }, { text: "github.com/ZLHad/OpenVideoHarness", color: AMB }];
  const ctaC = CTA.material.map.image, ctaG = ctaC.getContext("2d"); let ctaKey = null;
  function drawCTA(t) {
    const total = CTA_L[0].text.length + CTA_L[1].text.length;
    const k = t < bar(29, 2) ? 0 : Math.min(8, Math.floor((t - bar(29, 2)) / S16 + 1e-6) + 1), n = Math.round(total * k / 8);
    const cur = k < 8 ? Math.floor(t * 5) % 2 : 0, key = `${n}|${cur}`; if (key === ctaKey) return; ctaKey = key;
    ctaG.clearRect(0, 0, ctaC.width, ctaC.height); ctaG.font = `400 86px ${FONT_MONO}`; ctaG.textBaseline = "top"; ctaG.letterSpacing = "0px";
    let y = 24, left = n;
    CTA_L.forEach((l, i) => {
      if (i) y += 86 * 0.5;
      const x = (ctaC.width - ctaG.measureText(l.text).width) / 2, s = l.text.slice(0, clamp(left, 0, l.text.length));
      ctaG.fillStyle = l.color; ctaG.fillText(s, x, y + 86 * 0.06);
      if (cur && left >= 0 && left < l.text.length) { ctaG.fillStyle = AMB; ctaG.fillRect(x + ctaG.measureText(s).width + 4, y + 8, 44, 90); }
      left -= l.text.length; y += 86 * 1.12;
    });
    CTA.material.map.needsUpdate = true;
  }

  // --- camera: S1 hook (compressed to 3 bars) → S2 → S3 → S4 ---
  key(0.0, V(0.34, 0.08, 1.05), V(0, 0.0, -2), 30);
  key(bar(2), V(0.5, 0.26, 0.4), V(0, 0.1, -9), 33);
  key(bar(3), V(0.2, 3.3, 5.5), V(0, 1.5, -36), 40);
  key(bar(4), V(0, 1.35, -44), V(0, 1.2, -80), 40);
  key(bar(5), V(0, 1.1, -68), V(0, 1.1, -100), 40);
  key(bar(5, 2), V(0, 1.2, -88), V(0, 1.4, -120), 40);
  key(bar(6), V(0, 1.15, -112), V(0, 1.1, -142), 40);
  key(bar(7) - 0.6, V(0, 1.0, -135.5), V(0, 1.0, -150), 40);
  key(bar(7) + 0.3, V(0, 1.1, -146), V(0, 1.2, -170), 40);
  key(bar(8), V(0, 1.3, -160), V(0, 1.5, -190), 40);
  key(bar(9) - 0.66, V(0, 1.45, -172), V(0, 1.6, -205), 40);
  key(bar(9), V(0, 1.55, -178), V(0, 1.9, -214), 42);
  key(bar(10) - 0.35, V(0, 1.95, -187), V(0, 2.0, -232), 42);
  // S9 proof hall (after the star map), a slow slide past each screen (the tall film from further back: its caption stays inside the safe frame)
  key(bar(23, 1.2), L2(HX, 4.6, 86), L2(HX, 2.6, 128), 44);
  const camFor = (m, d, dy = -0.45) => [L2(m.x + Math.sin(m.ry) * d, m.y + dy + 0.2, m.s - Math.cos(m.ry) * d), L2(m.x, m.y + dy, m.s)];
  MON.forEach((m) => { const vert = m.h > m.w; const [p0, l0] = camFor(m, vert ? 11.8 : 8.9, vert ? -1.1 : -0.85); const [p1, l1] = camFor(m, vert ? 11.3 : 8.3, vert ? -1.1 : -0.85); key(m.tFocus + 0.45 * BEAT, p0, l0, 40, false, "f"); key(m.tFocus + 2.55 * BEAT, p1, l1, 40, false, "b"); });
  // S10 reveal: rise and pull back to the monument
  key(bar(27, 2), L2(HX, 5.2, 163), L2(HX, 8.2, MW.s), 46);
  key(bar(28), L2(HX, 7.3, 174.5), L2(HX, 7.5, MW.s), 44);
  key(bar(28, 2.9), L2(HX, 7.4, 175.2), L2(HX, 7.5, MW.s), 44);
  key(bar(29), L2(HX, 7.4, 175.5), L2(HX, 7.5, MW.s), 44);
  key(bar(29, 1.5), L2(HX, 8.3, 171.5), L2(HX, 8.5, MW.s), 42);
  // S11 title: settle and hold
  key(bar(30), L2(HX, 8.55, 173.5), L2(HX, 8.55, MW.s), 42);
  key(bar(30, 2.5), L2(HX, 8.5, 175.5), L2(HX, 8.5, MW.s), 42, true);
  key(DUR + 1, L2(HX, 8.5, 175.6), L2(HX, 8.5, MW.s), 42, true);

  K.sort((a, b) => a.t - b.t);
  const WHIPS = [[bar(3) - 0.1, 0.45], [bar(4), 0.4], [bar(7) - 0.15, 0.4], [bar(9) - 0.08, 0.3], ...ARCH.whips, ...PIPE.whips, ...FEAT.whips,
    [bar(23) + 0.1, 0.5], ...MON.slice(1).map((m) => [m.tFocus - 0.07, 0.4]), [bar(27, 1), 0.5], [bar(29) + 0.7, 0.4]].map(([t, h]) => ({ t, h }));
  const warp = makeWarp(WHIPS, P.whip);
  // the three big moves keep the lens streaks (the dive into the repo, into the proof hall, into "this film, too"); the
  // other whips are plain camera moves (round 3: one streak-whip repeated twelve times)
  const BIGT = [bar(10) + 0.15, bar(23) + 0.1, bar(27, 1)], BIGW = (t) => Math.max(0, ...BIGT.map((w) => Math.exp(-(((t - w) / 0.6) ** 2))));
  const camP = (t) => herm((k) => k.p, warp(t)), camL = (t) => herm((k) => k.l, warp(t)), camF = (t) => herm((k) => k.fov, warp(t));
  function fitAt(m, tq, frac) { // size a world-fixed text so it spans `frac` of the frame width at its read moment
    scene.updateMatrixWorld(true);
    const pos = new THREE.Vector3(); m.getWorldPosition(pos);
    const cp = camP(tq), cl = camL(tq), fov = camF(tq);
    const d = pos.clone().sub(cp).dot(cl.clone().sub(cp).normalize());
    m.userData.fit = frac * (2 * d * Math.tan(THREE.MathUtils.degToRad(fov / 2)) * (1920 / 1080)) / (m.geometry.parameters.width * (m.userData.contentFrac || 1));
  }
  function tangent(i, f) {
    if (K[i].stop) return f(K[i]).clone ? f(K[i]).clone().multiplyScalar(0) : 0;
    let a = K[Math.max(0, i - 1)], b = K[Math.min(K.length - 1, i + 1)];
    if (K[i].tm === "f") a = K[i]; else if (K[i].tm === "b") b = K[i];
    if (a === b) return f(K[i]).clone ? f(K[i]).clone().multiplyScalar(0) : 0;
    const fa = f(a), fb = f(b), dt = b.t - a.t;
    return fa.clone ? fb.clone().sub(fa).multiplyScalar(1 / dt) : (fb - fa) / dt;
  }
  function herm(f, t) {
    let i = 0; while (i < K.length - 2 && K[i + 1].t <= t) i++;
    const a = K[i], b = K[i + 1], h = b.t - a.t, u = clamp((t - a.t) / h);
    const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2;
    const pa = f(a), pb = f(b), ma = tangent(i, f), mb = tangent(i + 1, f);
    if (pa.clone) return pa.clone().multiplyScalar(h00).addScaledVector(ma, h10 * h).addScaledVector(pb, h01).addScaledVector(mb, h11 * h);
    return pa * h00 + ma * h10 * h + pb * h01 + mb * h11 * h;
  }
  const SHAKES = [[bar(3), 0.012], [bar(9), 0.05], [bar(23), 0.02], [bar(29), 0.022], [bar(30), 0.012], ...ARCH.shakes, ...PIPE.shakes, ...FEAT.shakes];
  const shake = (t) => { // decaying shake on the big hits (+ downbeat micro-shake in the drops); seeded, deterministic
    let s = 0; for (const [th, amp] of SHAKES) { const u = t - th; if (u >= 0 && u < 1.6) s += amp * Math.exp(-u / 0.3); }
    s *= P.shake; if (P.pulse && t > bar(9) && t < bar(27)) s += 0.005 * P.pulse * PUL.down(t);
    return V(Math.sin(t * 61.7) * s + Math.sin(t * 23.1 + 0.4) * s * 0.5, Math.sin(t * 47.3 + 1.3) * s, 0);
  };
  const hand = (t) => V(0.018 * Math.sin(0.9 * t + 1.1) + 0.01 * Math.sin(2.3 * t + 0.3), 0.012 * Math.sin(1.1 * t + 2.2) + 0.007 * Math.sin(2.9 * t), 0).multiplyScalar(P.hand);
  const PUNCHES = [...PUL.bigList, ...ARCH.punches, ...PIPE.punches, ...FEAT.punches];

  [[T1, 4.0, 0.46], [T14, bar(27, 1) + 0.9, 0.5], [T15, bar(28) + 0.6, 0.7]].forEach(([m, tq, fr]) => fitAt(m, tq, fr));
  // ---------- post: bloom + motion + grade ----------
  const composer = new EffectComposer(renderer);
  composer.setPixelRatio(1); composer.setSize(1920, 1080);
  composer.addPass(new RenderPass(scene, camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1920, 1080), P.bloom, 0.5, 1.0); composer.addPass(bloom);
  let GRAIN = 0.035; try { const v = window.__hyperframes && window.__hyperframes.getVariables && window.__hyperframes.getVariables(); if (v && typeof v.grain === "number") GRAIN = v.grain; } catch (e) {}
  const grainPass = new ShaderPass({
    uniforms: { tDiffuse: { value: null }, uFrame: { value: 0 }, uAmt: { value: GRAIN } },
    vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uFrame, uAmt; varying vec2 vUv;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uFrame*0.618)*43758.5453); }
      vec3 hot(vec2 uv){ vec3 c = texture2D(tDiffuse, uv).rgb; float l = max(c.r, max(c.g, c.b)); return c * smoothstep(0.82, 1.0, l) * step(c.b * 1.6, c.r); }
      void main(){
        vec2 d = vUv - 0.5; float r2 = dot(d, d);
        vec2 off = d * r2 * 0.012;
        vec3 c = vec3(texture2D(tDiffuse, vUv + off).r, texture2D(tDiffuse, vUv).g, texture2D(tDiffuse, vUv - off).b);
        vec3 st = vec3(0.0);
        for (int i = 1; i <= 24; i++) { float o = float(i) * 0.0065; float w = exp(-float(i) * 0.16); st += (hot(vUv + vec2(o, 0.0)) + hot(vUv - vec2(o, 0.0))) * w; }
        c += st * vec3(1.0, 0.72, 0.28) * 0.045;
        float n = h(floor(vUv * vec2(1920.0, 1080.0))) - 0.5;
        gl_FragColor = vec4(c + n * uAmt, 1.0);
      }`,
  });
  const motionPass = new ShaderPass(motionShader()); const gradePass = new ShaderPass(gradeShader());
  if (FXID === "v2") { composer.addPass(grainPass); composer.addPass(new OutputPass()); }
  else { composer.addPass(motionPass); composer.addPass(new OutputPass()); composer.addPass(gradePass); gradePass.uniforms.uGrain.value = GRAIN; }
  // particles: depth sparks along the whole camera path, data streams on the t-axis, warp lines at the lens
  const pathSamples = []; for (let i = 0; i <= 480; i++) pathSamples.push(camP((i / 480) * DUR)); [ARCH, PIPE, FEAT].forEach((M) => M.samples.forEach((q) => pathSamples.push(q)));
  const sparks = makeSparks(THREE, pathSamples, 9000); scene.add(sparks); sparks.visible = P.sparks > 0; sparks.material.uniforms.uAmt.value = P.sparks;
  // v5: the archive is made of films. Small frames of the opening's films (the same atlases) drift beside the camera path,
  // so "every star is a film" carries on into the body. Instanced billboards; each plays its film from t.
  const filmField = await (async () => {
    const [tP, tR, tA] = await Promise.all([loadTex("assets/films-proc.png"), loadTex("assets/films.jpg"), loadTex("assets/films-ai.jpg")]);
    if (!tP || !tR || !tA) return null;
    tP.colorSpace = THREE.NoColorSpace;                    // stored gamma-encoded without a tag (decoded in the shader)
    const NF = 1000, geo = new THREE.PlaneGeometry(1, 0.5625);
    const pos = new Float32Array(NF * 3), film = new Float32Array(NF * 4);
    for (let i = 0; i < NF; i++) {
      const q = pathSamples[Math.floor(hash(i * 2.37 + 0.3) * pathSamples.length)];
      const a = hash(i * 3.11 + 0.7) * Math.PI * 2, r = 2.8 + 9 * Math.pow(hash(i * 4.29 + 0.1), 0.8);
      pos.set([q.x + Math.cos(a) * r, q.y + Math.sin(a) * r * 0.6, q.z + (hash(i * 5.73) - 0.5) * 6], i * 3);
      const k = hash(i * 6.91 + 0.2), kind = k < 0.4 ? 2 : k < 0.65 ? 1 : 0;
      film.set([kind, Math.floor(hash(i * 7.77 + 0.4) * (kind === 2 ? 40 : kind === 1 ? 41 : 28)), hash(i * 8.13) * 16, 0.45 + 0.7 * hash(i * 9.37)], i * 4);
    }
    geo.setAttribute("aPos", new THREE.InstancedBufferAttribute(pos, 3)); geo.setAttribute("aFilm", new THREE.InstancedBufferAttribute(film, 4));
    const mat = new THREE.ShaderMaterial({ transparent: true, depthWrite: false, toneMapped: false,
      uniforms: { tP: { value: tP }, tR: { value: tR }, tA: { value: tA }, uT: { value: 0 }, uAmt: { value: 0 }, uFog: { value: 0.02 } },
      vertexShader: `attribute vec3 aPos; attribute vec4 aFilm; varying vec2 vUv; varying vec4 vFilm; varying float vFade;
        void main(){ vUv = uv; vFilm = aFilm; vec4 mv = modelViewMatrix * vec4(aPos, 1.0); mv.xy += position.xy * aFilm.w;
          float d = -mv.z; vFade = exp(-0.012 * d * d * 0.02) * smoothstep(4.0, 9.0, d); gl_Position = projectionMatrix * mv; }`,
      fragmentShader: `uniform sampler2D tP, tR, tA; uniform float uT, uAmt; varying vec2 vUv; varying vec4 vFilm; varying float vFade;
        vec3 tap(float fr){ float kind = vFilm.x, rows = kind < 0.5 ? 28.0 : (kind < 1.5 ? 41.0 : 40.0);
          vec2 a = vec2((fr + 0.5 + (vUv.x - 0.5) * 0.99) / 16.0, 1.0 - (vFilm.y + 0.5 - (vUv.y - 0.5) * 0.99) / rows);
          if (kind < 0.5) return pow(texture2D(tP, a).rgb, vec3(2.2)); if (kind < 1.5) return texture2D(tR, a).rgb; return texture2D(tA, a).rgb; }
        float frameOf(float k){ float m = mod(k, 30.0); return vFilm.x > 0.5 ? (m < 16.0 ? m : 30.0 - m) : mod(k, 16.0); }
        void main(){ float f = uT * 8.0 + vFilm.z, k0 = floor(f); vec3 c = mix(tap(frameOf(k0)), tap(frameOf(k0 + 1.0)), f - k0);
          vec2 e = min(vUv, 1.0 - vUv); float edge = 1.0 - smoothstep(0.0, 0.03, min(e.x * 1.78, e.y));
          c = c * 0.36 + vec3(1.0, 0.72, 0.3) * edge * 0.2;
          gl_FragColor = vec4(c, uAmt * vFade); }` });
    const mesh = new THREE.InstancedMesh(geo, mat, NF); mesh.frustumCulled = false; mesh.renderOrder = -100; scene.add(mesh); return mesh;
  })();
  const streams = makeStreams(THREE); scene.add(streams);
  const warpLines = makeWarpLines(THREE); camera.add(warpLines); scene.add(camera);
  const hudx = document.getElementById("hudx");
  const hud = document.getElementById("hud"), fade = document.getElementById("fade");
  const HEROES = [fx, T1, T2, T34, T5, T6, T7, T8, T13, T14, T15, ...MON.map((m) => m.lab), ...ARCH.labels, ...PIPE.heroes, ...PIPE.labels, ...FEAT.heroes];
  const TITLE_LW = L2(HX - 8.8, 10.35, MW.s - 0.6);

  // =====================================================================
  // RENDER AT t
  // =====================================================================
  return function renderAt(t, ta = t, rate = 1) {   // t: the story's time (old, stretched holds); ta: ambient time (the film's own clock)
    // the film's time (ta) is on the frame grid; the story's time is continuous: snapping it too would make a stretched
    // hold (where it runs at a fraction of real speed) hold still for frames and then step (judder)
    t = clamp(t, 0, DUR) + 1e-4;
    const frame = Math.round(ta * FPS);
    // camera: keyframed path through speed-ramped time + seeded shake + handheld drift + FOV punch on the big hits
    const p = camP(t).add(shake(t)).add(hand(ta)), l = camL(t);
    let punch = 0; for (const h of PUNCHES) { const u = t - h; if (u >= 0 && u < 1.2) punch += 3.5 * Math.exp(-u / 0.22); }
    camera.position.copy(p); camera.fov = camF(t) - punch * P.fovPunch; camera.updateProjectionMatrix(); camera.lookAt(l);
    if (P.hand) camera.rotateZ(0.004 * P.hand * Math.sin(0.7 * ta + 0.5));
    camera.updateMatrixWorld(true);

    // global light level: blackout before the braam
    const black = Math.max(1 - seg(t, 0.0, 0.25), seg(t, bar(9) - 0.66, bar(9) - 0.62) * (1 - seg(t, bar(9), bar(9) + 0.02)));
    fade.style.opacity = (t < 1 ? black : (P.whip ? 0.5 : 0.84) * black).toFixed(3);
    scene.fog.density = t < bar(9) ? lerp(0.028, 0.02, seg(t, bar(3), bar(4))) : t < bar(23) ? 0.013 : 0.011;

    // spark + axis (S1–S4); the axis hands over to the rings at the braam
    const grow = eOutExpo(seg(t, 0.7, 3.0));
    const axLen = 2 + 900 * grow;
    axis.scale.set(1, 1, axLen); axis.position.set(0, 0, -axLen / 2); axisGlow.scale.copy(axis.scale); axisGlow.position.copy(axis.position);
    const axisK = 1.7 * lerp(0.55, 1, seg(t, 0.6, bar(2)));
    const axOn = t < bar(10) + 0.3 && !(t > bar(8, 3) && t < bar(9));
    setAmber(axisMat, axisK); axis.visible = axisGlow.visible = axOn; axisGlowMat.opacity = 0.3;
    spark.position.set(0, 0, 0); spark.scale.setScalar(0.05 + 0.1 * eOutExpo(seg(t, 0.1, 0.6)) + 0.06 * Math.exp(-((t - 0.7) ** 2) / 0.02));
    const sparkD = camera.position.length(), sparkNear = clamp((sparkD - 0.55) / 0.35); // no white-out when the lens passes the spark
    sparkHalo.scale.setScalar(0.7); sparkHalo.material.opacity = 0.22 * (1 - seg(t, bar(3), bar(4))) * sparkNear;
    spark.material.opacity = t < bar(4) ? sparkNear : 0; spark.visible = sparkHalo.visible = t < bar(4);

    // S1: plates render in (field1); the formula; the fly-through words
    field1.material.uniforms.uTime.value = t; field1.material.uniforms.uFog.value = scene.fog.density; field1.material.uniforms.uGlobal.value = t < bar(4) ? 1 : t < bar(9) ? lerp(1, 0.45, seg(t, bar(4), bar(5))) : 0.4;
    field1.visible = t < bar(10);
    fx.material.opacity = win(t, 0.35, bar(2) - 0.12, 0.4, 0.4); fx.visible = fx.material.opacity > 0; if (fx.visible) { fx.userData.dyn.draw(t - 0.3, P); fx.material.uniforms.uSweep.value = P.sweep ? lerp(-0.25, 1.25, seg(t, 0.9, 1.6)) : -1; fx.material.uniforms.uGlitch.value = P.glitchExit * seg(t, bar(2) - 0.35, bar(2) - 0.12); fx.material.uniforms.uFrame.value = frame; } fx.userData.quiet.material.opacity = 0.5 * fx.material.opacity; if (fx.visible) rideView(fx, 2.0, 0.4, 0, 0.22);
    slam(T1, t, bar(2), bar(3) - 0.1, { sc: 1.04, rise: 0.3, fo: 0.4 });
    slam(T2, t, bar(3), bar(4) - 0.12, { sc: 1.05, rise: 0.35, fo: 0.4 }); if (T2.visible) rideView(T2, 12, 0.62, 0, 0.26);

    // dust drifts with t
    const pos = dustGeo.attributes.position;
    for (let i = 0; i < NDUST; i++) { pos.array[3 * i] = dpos[3 * i] + dvel[i][0] * t; pos.array[3 * i + 1] = dpos[3 * i + 1] + dvel[i][1] * t; }
    pos.needsUpdate = true;

    // S2
    { // rides ahead (held, readable), then stays put and the camera flies through it
      const tHold = bar(4, 3.3), zHold = herm((k) => k.p, tHold).z - 5.8;
      const z = t < tHold ? camera.position.z - lerp(7.0, 5.8, seg(t, bar(4, 0.3), tHold)) : zHold;
      const dz = camera.position.z - z;
      req.position.set(0, (t < tHold ? camera.position.y : herm((k) => k.p, tHold).y) - 0.22, z);
      req.material.opacity = eOutCubic(seg(t, bar(4, 0.25), bar(4, 0.9))) * clamp((dz - 2.6) / 1.9);
    }
    req.visible = req.material.opacity > 0.001;
    codeStrips.forEach((m) => { m.material.opacity = 0.9 * win(t, m.userData.tIn, bar(7), 0.25, 0.4); m.visible = m.material.opacity > 0; });
    slam(T34, t, bar(5), bar(6) - 0.1, { fo: 0.35 }); if (T34.visible) rideView(T34, 11, 0.62, 0, 0.14);
    tiles2.forEach((m) => {
      const u = eOutExpo(seg(t, m.userData.tIn - 0.55, m.userData.tIn));
      m.position.lerpVectors(m.userData.from, m.userData.home, u);
      m.material.opacity = seg(t, m.userData.tIn - 0.55, m.userData.tIn - 0.3) * (1 - seg(t, bar(7) + 0.4, bar(7) + 0.7));
      m.visible = m.material.opacity > 0;
    });
    scr2Frame.material.opacity = win(t, bar(6, 0.5), bar(7) + 0.6, 0.3, 0.2);
    slam(T5, t, bar(6, 0.75), bar(7) - 0.25, { sc: 1.03, fo: 0.3 }); if (T5.visible) rideView(T5, 8, 0.4, -0.5, 0.1);

    // S3
    field3.material.uniforms.uTime.value = t; field3.material.uniforms.uFog.value = scene.fog.density;
    field3.material.uniforms.uFlicker.value = t > bar(7) ? 0.75 * seg(t, bar(7), bar(7, 1)) : 0;
    field3.material.uniforms.uGlobal.value = t < bar(9) ? 0.6 : 0.3;
    field3.visible = t > bar(6) && t < bar(10);
    fails.forEach((f) => {
      const on = win(t, f.tIn - 0.2, bar(9) - 0.66, 0.08, 0.12);
      f.img.material.opacity = on * (t > bar(8) ? 0.55 : 1); f.grp.visible = on > 0;
      const gm = t >= f.tIn + 0.2 ? f.grey : f.col; if (f.img.material.map !== gm) { f.img.material.map = gm; f.img.material.needsUpdate = true; }
      f.grp.position.set(f.grp.userData.x, camera.position.y - 1.05, camera.position.z - 9.8); f.grp.rotation.set(0, 0, 0);
      const st = t >= f.tIn ? 1 : 0; // the stamp lands on the beat
      f.stamp.material.opacity = st * on; f.box.material.opacity = st * on;
      const s = lerp(1.35, 1, eOutExpo(seg(t, f.tIn, f.tIn + 0.25))); f.stamp.scale.set(s, s, 1);
    });
    slam(T6, t, bar(7), bar(8) + 0.05, { fo: 0.3 }); if (T6.visible) rideView(T6, 10, 0.45, 0, 0.34);
    slam(T7, t, bar(8), bar(9) - 0.66, { fo: 0.12 }); if (T7.visible) rideView(T7, 10, 0.55, 0, 0.34);

    // S4: rings light in a wave on the braam
    rings.forEach((r) => { const a = t - r.userData.tIn; const k = a < 0 ? 0 : 1.1 + 3.2 * Math.exp(-a / 0.4); setAmber(r.userData.mat, k * 0.75); r.visible = t > bar(9) - 0.01 && t < bar(10, 2); });
    shafts4.forEach((s, i) => { s.material.opacity = 0.55 * win(t, bar(9) + i * 0.05, bar(10, 1), 0.3, 0.8); s.visible = s.material.opacity > 0; });
    slam(T8, t, bar(9), bar(10) - 0.12, { sc: 1.12, rise: 0.1, fi: 0.25, fo: 0.35 }); if (window.__T0) T8.visible = false; if (T8.visible) { rideView(T8, 12, 0.68, 0, 0.02); T8.userData.quiet.material.opacity = 0.85 * T8.material.opacity; }

    // S5–S8 modules
    ARCH.update(t, { frame, PUL });
    PIPE.update(t, { camera, frame, PUL });
    FEAT.update(t, { frame, PUL, ta });

    // S9 proof hall
    MON.forEach((m) => {
      const focus = 1 - Math.min(1, Math.abs(t - (m.tFocus + FD / 2)) / (FD * 0.9));
      m.halo.material.opacity = 0.1 + 0.25 * focus;
      m.lab.material.opacity = win(t, m.tFocus - 0.15, m.tFocus + FD + 0.05, 0.3, 0.3);
      m.lab.visible = m.lab.material.opacity > 0;
      if (m.link) { m.link.material.opacity = win(t, m.tFocus + 0.1, m.tFocus + FD + 0.05, 0.3, 0.3); m.link.visible = m.link.material.opacity > 0; }
      m.grp.visible = t > bar(22, 2) && t < bar(28);
    });
    slam(T13, t, bar(23, 0.35), bar(24) - 0.1, { fo: 0.4 }); if (T13.visible) rideView(T13, 12, 0.6, 0, 0.44);

    // S10 monument + code + waveform; S11 title
    const titleDim = (1 - 0.9 * seg(t, bar(29) - 0.1, bar(29) + 0.4)) * (1 - 0.68 * win(t, bar(27, 1), bar(29), 0.5, 0.3));
    const typeOn = Math.max(win(t, bar(27, 1), bar(29) - 0.5, 0.5, 0.3), seg(t, bar(29) - 0.2, bar(29) + 0.3));
    mwTiles.forEach((m) => { m.material.opacity = 0.92 * eOutCubic(seg(t, m.userData.tIn, m.userData.tIn + 0.35)) * titleDim * (1 - typeOn * (1 - m.userData.ell)); m.visible = m.material.opacity > 0.001; });
    slam(T14, t, bar(27, 1) + 0.45, bar(28) - 0.05, { fo: 0.3, nodec: 1 });   // lands after the whip, no scramble
    const revealEnd = bar(29) - 0.04; // the 4th code line (stem:lead, 28:4) gets its read before the title lands
    slam(T15, t, bar(28), revealEnd, { fo: 0.25 });
    codeLines.forEach((m, i) => { const a = m.userData.tIn - 1 / FPS; m.material.opacity = t >= a ? win(t, a, revealEnd, 0.1, 0.25) : 0; m.visible = m.material.opacity > 0; codeMarks[i].visible = t >= m.userData.tIn && t < revealEnd; });
    if (waveLine) { waveLine.material.opacity = 0.85 * win(t, bar(27, 2), revealEnd, 0.8, 0.25); waveLine.visible = waveLine.material.opacity > 0; }
    playhead.visible = t > bar(27, 2) && t < revealEnd;
    playhead.position.set(HX - 9.5 + 19 * clamp((ta - (window.__T0 || 0)) / ((WAVE && WAVE.duration) || DUR)), 5.45, -(MW.s - 9.55)); // the playhead sits on the film's own time in the waveform
    { const u = eOutExpo(seg(t, bar(29), bar(29) + 1.0)); const s2 = lerp(1.1, 1, u); TITLE.scale.set(s2, s2, 1); }
    TITLE.material.opacity = t >= bar(29) ? eOutCubic(seg(t, bar(29) - 1 / FPS, bar(29) + 0.3)) : 0; TITLE.visible = TITLE.material.opacity > 0;
    TAG.material.opacity = win(t, bar(29, 1), DUR + 5, 0.5, 0.1); TAG.visible = TAG.material.opacity > 0;
    CTA.material.opacity = t >= bar(29, 2) ? 1 : 0; CTA.visible = CTA.material.opacity > 0; if (CTA.visible) drawCTA(t);
    const tw = TITLE.geometry.parameters.width * TITLE.scale.x;
    titleBar.position.set(HX - tw / 2 - 0.75, 10.35, -(MW.s - 0.6)); titleBar.visible = t >= bar(29);
    setAmber(titleBar.material, 1.7 + 1.6 * Math.exp(-Math.max(0, t - bar(29)) / 0.3)); // the bar's flare must never reach the O

    // footage: re-upload the frame HyperFrames seeked for this t
    VIDTEX.forEach((tx) => { const v = tx.image; if (v && v.readyState >= 2) tx.needsUpdate = true; });
    // FX: particles, pulses, motion blur, rays, shockwave, CA, grade (all from t and the camera state at t)
    const down = PUL.down(t), big = PUL.big(t);
    if (filmField) { filmField.material.uniforms.uT.value = ta; filmField.material.uniforms.uAmt.value = (window.__T0 ? 1 : 0) * win(t, bar(10) - 0.3, bar(27, 2), 0.6, 0.8); filmField.visible = filmField.material.uniforms.uAmt.value > 0.002; }
    sparks.material.uniforms.uTime.value = ta; sparks.material.uniforms.uPulse.value = P.pulse * (0.6 * down + big); sparks.material.uniforms.uFog.value = scene.fog.density;
    streams.userData.update(t, P.streams * (t < bar(9) ? win(t, 1.5, bar(9) - 0.7, 1.0, 0.4) : 0), bar(9));
    const dtS = rate / FPS, pPrev = camP(Math.max(0, t - dtS)), lPrev = camL(Math.max(0, t - dtS));   // one film frame ago, in story time
    const fwd = l.clone().sub(p).normalize(), fwdPrev = lPrev.clone().sub(pPrev).normalize();
    const vel = p.clone().sub(pPrev).multiplyScalar(FPS), speed = vel.length(), vFwd = vel.dot(fwd);
    warpLines.userData.update(t, speed, P.warp * (0.15 + 0.85 * BIGW(t)));   // the lens streaks only on the three big moves
    if (FXID === "v2") { grainPass.uniforms.uFrame.value = frame; }
    else {
      const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion), up = new THREE.Vector3(0, 1, 0).applyQuaternion(camera.quaternion);
      const dd = fwd.clone().sub(fwdPrev), kk = 0.5 / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
      const M = motionPass.uniforms;
      const guardO = Math.max(0, ...HEROES.map((m) => (m.visible ? m.material.opacity : 0)));
      const guard = 1 - 0.95 * guardO; // type stays crisp through whips (no smear while a read is on screen)
      M.uZoom.value = P.mblur * guard * clamp(vFwd * 0.0022, -0.1, 0.12);
      M.uPan.value = [clamp(-dd.dot(right) * kk * 1.2, -0.05, 0.05) * P.mblur * guard, clamp(-dd.dot(up) * kk * 1.2 * 1.7778, -0.05, 0.05) * P.mblur * guard];
      // key light for god rays, per section
      const LW = t < bar(4) ? new THREE.Vector3(0, 0, 0) : t < bar(9) - 0.66 ? p.clone().addScaledVector(fwd, 80) : t < bar(10) ? new THREE.Vector3(0, 2.2, -202)
        : t < bar(14) ? ARCH.light(t) : t < bar(19) ? PIPE.light(t) : t < bar(23) ? FEAT.light(t) : t < bar(29) - 0.2 ? p.clone().addScaledVector(fwd, 40) : TITLE_LW;
      const ndc = LW.clone().project(camera), inFront = LW.clone().sub(p).dot(fwd) > 0;
      M.uLight.value = [ndc.x * 0.5 + 0.5, ndc.y * 0.5 + 0.5];
      const rayEnv = t < bar(3) ? 0.45 + 0.45 * seg(t, bar(2) + 0.3, bar(3)) : t < bar(9) - 0.66 ? 0.25 : t < bar(10) ? 0.45 + 0.35 * big : t < bar(14) ? ARCH.rays(t) : t < bar(19) ? PIPE.rays(t) : t < bar(23) ? FEAT.rays(t) : t < bar(29) - 0.2 ? 0.25 : 0.32 + 0.45 * big;
      M.uRays.value = inFront ? P.rays * rayEnv : 0;
      const netSec = t > bar(10) && t < bar(23);
      M.uStreak.value = P.streak * (netSec ? 0.5 : 1) * (1 + 1.2 * big + 0.5 * PUL.hit(t)) * (1 - 0.8 * seg(t, bar(29, 1.4), bar(29, 2))); // the URL must stay clean
      M.uCA.value = P.ca * (0.1 + 0.35 * down + 1.2 * big + PIPE.ca(t)) * (1 - 0.95 * guardO);
      let ring = [0.5, 0.5, 0, 0];
      for (const h of PUNCHES) { const u = (t - h) / 0.75; if (u >= 0 && u < 1 && h < bar(28)) ring = [M.uLight.value[0], M.uLight.value[1], 0.03 + 1.3 * Math.pow(u, 0.7), 0.6 * P.ring * (1 - u)]; }
      M.uRing.value = ring;
      bloom.strength = P.bloom * (1 + 0.2 * P.pulse * down + 0.3 * big);
      const G = gradePass.uniforms;
      G.uGrade.value = P.grade; G.uContrast.value = P.contrast; G.uExposure.value = 1 + 0.12 * P.pulse * down; G.uFlash.value = P.flash * PUL.flash(t) * (t > bar(10) ? 0.3 : 1);
      G.uScan.value = P.scan; G.uRGB.value = P.rgb; G.uGlitch.value = P.glitchFrame * (0.12 + 0.9 * Math.max(0, ...WHIPS.map((w) => 1 - Math.abs(t - w.t) / 0.12)));
      G.uFrame.value = frame;
      if (hudx) {
        const show = P.hud > 0;
        hudx.style.display = show ? "block" : "none";
        if (show) {
          const rx = M.uLight.value[0] * 1920, ry = (1 - M.uLight.value[1]) * 1080;
          const retOn = inFront && rayEnv * P.rays > 0.45 ? 1 : 0;
          hudx.querySelector(".ret").style.transform = `translate(${rx.toFixed(1)}px, ${ry.toFixed(1)}px) rotate(${(t * 40) % 360}deg)`;
          hudx.querySelector(".ret").style.opacity = (retOn * (P.hud > 0.9 ? 0.85 : 0.5)).toFixed(2);
          hudx.querySelector(".frame").style.opacity = (P.hud > 0.9 ? 0.75 : 0).toFixed(2);
          hudx.querySelector(".rec").style.opacity = P.hud > 0.9 ? "1" : "0"; hudx.querySelector(".rec").textContent = `● REC  FX ${FXID}  ${String(frame).padStart(4, "0")}/${Math.round(DUR * FPS)}  ${(speed).toFixed(1).padStart(5, " ")} m/s`;
        }
      }
    }
    composer.render();

    // HUD: the timecode motif (film t, frame, bar.beat)
    const [bb, be] = barBeat(t);
    const tf = t - (window.__T0 || 0), ff = Math.round(tf * FPS); hud.textContent = `t ${tf.toFixed(2).padStart(5, "0")} · f ${String(ff).padStart(4, "0")} · ♩ ${String(Math.min(30, bb)).padStart(2, "0")}.${be}`;
    hud.style.opacity = (t > bar(29, 2) ? 1 - seg(t, bar(29, 2), bar(30)) * 0.6 : 1 - win(t, bar(23) + 0.2, bar(27), 0.3, 0.3)).toFixed(3);
  };
}
