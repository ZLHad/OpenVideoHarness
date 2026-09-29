// v3 FX stack. Every effect is a pure function of t (and of the camera state that is itself a pure function of t).
// Preset is chosen by the HyperFrames variable `fx`: "v2" (off) | "A" restrained cinematic | "B" blockbuster | "C" cyber-glitch.
// Why each effect exists in THIS film (the "because X, so Y" rule) is documented in NOTES.md, section v3.

export const PRESETS = {
  v2: { grade: 0, contrast: 1.0, bloom: 0.62, streak: 0.045, rays: 0, whip: 0, mblur: 0, shake: 1, hand: 0, fovPunch: 0, pulse: 0, ca: 0, ring: 0, sparks: 0, streams: 0, warp: 0, decode: 0, sweep: 0, glitchExit: 0, rgb: 0, scan: 0, hud: 0, glitchFrame: 0, flash: 0 },
  A: { grade: 1, contrast: 1.12, bloom: 0.95, streak: 0.11, rays: 0.75, whip: 0.55, mblur: 0.25, shake: 1.0, hand: 0.5, fovPunch: 0.5, pulse: 0.5, ca: 0.3, ring: 0.4, sparks: 0.5, streams: 0.6, warp: 0, decode: 0, sweep: 1, glitchExit: 0, rgb: 0, scan: 0, hud: 0, glitchFrame: 0, flash: 0.5 },
  B: { grade: 1, contrast: 1.2, bloom: 1.0, streak: 0.17, rays: 1.0, whip: 1.0, mblur: 1.0, shake: 1.7, hand: 1.0, fovPunch: 1.0, pulse: 1.0, ca: 1.0, ring: 1.0, sparks: 1.0, streams: 1.0, warp: 1.0, decode: 1, sweep: 1, glitchExit: 0.35, rgb: 0, scan: 0, hud: 0.5, glitchFrame: 0, flash: 1 },
  C: { grade: 1, contrast: 1.22, bloom: 1.0, streak: 0.17, rays: 1.0, whip: 1.0, mblur: 1.0, shake: 1.7, hand: 1.0, fovPunch: 1.0, pulse: 1.0, ca: 1.0, ring: 1.0, sparks: 1.0, streams: 1.0, warp: 1.0, decode: 1, sweep: 1, glitchExit: 1, rgb: 1, scan: 1, hud: 1, glitchFrame: 1, flash: 1 },
};
export function readPreset() {
  let id = "B";
  try { const v = window.__hyperframes && window.__hyperframes.getVariables && window.__hyperframes.getVariables(); if (v && typeof v.fx === "string" && PRESETS[v.fx]) id = v.fx; } catch (e) {}
  try { const q = new URLSearchParams(location.search).get("fx"); if (q && PRESETS[q]) id = q; } catch (e) {} // debug override in a plain browser
  return { id, P: PRESETS[id] };
}

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const hash = (i) => { const s = Math.sin(i * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };

// ---------------------------------------------------------------------------------------------
// camera speed ramp: remap camera time inside short windows around section changes (slow–FAST–slow)
// E(u) = u^k / (u^k + (1-u)^k): slope k at the centre; blended with identity by `a` so edges keep (1-a) speed.
export function makeWarp(whips, amount) {
  const E = (u, k) => { const a = Math.pow(u, k), b = Math.pow(1 - u, k); return a / (a + b); };
  return (t) => {
    if (!amount) return t;
    for (const w of whips) {
      const a0 = w.t - w.h, a1 = w.t + w.h;
      // slope 1 at both window edges (no jerk entering or leaving), 0.49× in the shoulders, 1.9× at the centre
      if (t > a0 && t < a1) { const u = (t - a0) / (a1 - a0), A = 0.45 * amount; return a0 + (a1 - a0) * (u + A * (Math.sin(4 * Math.PI * u) / (4 * Math.PI) - Math.sin(2 * Math.PI * u) / (2 * Math.PI))); }
    }
    return t;
  };
}

// ---------------------------------------------------------------------------------------------
// beat / hit envelopes from the score's own beat map (sound and light from one source)
export function makePulses(BEATS, bar, big = [bar(3), bar(9), bar(23), bar(29)]) { // big: corridor reveal, braam, hall, title
  const downs = (BEATS && BEATS.downbeats) || [];
  const hits = ((BEATS && BEATS.hits) || []).filter((h) => (h.kind || "transient") === "transient");
  const decay = (t, list, tau, win = 1.5) => { let s = 0; for (const x of list) { const u = t - x; if (u >= 0 && u < win) s += Math.exp(-u / tau); } return s; };
  return {
    down: (t) => Math.min(1, decay(t, downs, 0.16, 0.8)),
    hit: (t) => Math.min(1, decay(t, hits.map((h) => h.t), 0.1, 0.5) * 0.6),
    big: (t) => Math.min(1, decay(t, big, 0.35, 2.0)),
    bigList: big,
    flash: (t) => { let s = 0; for (const x of big) { const u = t - x; if (u >= 0 && u < 0.2) s = Math.max(s, Math.exp(-u / 0.045)); } return s; }, // <= 4 flashes per film (<= 3/s rule)
  };
}

// ---------------------------------------------------------------------------------------------
// post chain: motion pass (linear, before OutputPass) + grade pass (display space, after OutputPass)
export function motionShader() {
  return {
    uniforms: {
      tDiffuse: { value: null }, uZoom: { value: 0 }, uPan: { value: [0, 0] }, uLight: { value: [0.5, 0.5] }, uRays: { value: 0 },
      uStreak: { value: 0.045 }, uCA: { value: 0 }, uRing: { value: [0.5, 0.5, 0, 0] },
    },
    vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uZoom, uRays, uStreak, uCA; uniform vec2 uPan, uLight; uniform vec4 uRing; varying vec2 vUv;
      vec3 hot(vec2 uv){ vec3 c = texture2D(tDiffuse, uv).rgb; float l = max(c.r, max(c.g, c.b)); return c * smoothstep(0.82, 1.0, l) * step(c.b * 1.6, c.r); }
      vec3 bright(vec2 uv){ vec3 c = texture2D(tDiffuse, uv).rgb; return max(c - 0.45, 0.0); }
      void main(){
        vec2 uv = vUv;
        // shockwave: a refracting, glowing ring expanding from uRing.xy (radius uRing.z, strength uRing.w)
        vec2 rd = (uv - uRing.xy) * vec2(1.7778, 1.0); float rl = length(rd);
        float band = uRing.w * exp(-pow((rl - uRing.z) / 0.018, 2.0));
        uv -= normalize(rd + 1e-5) / vec2(1.7778, 1.0) * band * 0.012;
        // camera-velocity motion blur: radial (forward speed) + directional (pan)
        vec3 c = vec3(0.0); float wsum = 0.0;
        for (int i = 0; i < 10; i++) {
          float f = float(i) / 9.0 - 0.5; float w = 1.0 - abs(f);
          vec2 q = 0.5 + (uv - 0.5) * (1.0 - uZoom * f) + uPan * f;
          vec2 d = q - 0.5; vec2 off = d * dot(d, d) * (0.012 + uCA * 0.06);
          c += vec3(texture2D(tDiffuse, q + off).r, texture2D(tDiffuse, q).g, texture2D(tDiffuse, q - off).b) * w; wsum += w;
        }
        c /= wsum;
        // volumetric light scattering (god rays) toward the key light
        if (uRays > 0.001) {
          vec2 dv = (uv - uLight) / 40.0; vec2 q = uv; float dec = 1.0; vec3 r = vec3(0.0);
          for (int i = 0; i < 40; i++) { q -= dv; r += bright(q) * dec; dec *= 0.955; }
          c += r * vec3(1.0, 0.78, 0.45) * uRays * 0.055;
        }
        // anamorphic streaks on amber highlights
        vec3 st = vec3(0.0);
        for (int i = 1; i <= 24; i++) { float o = float(i) * 0.0065; float w = exp(-float(i) * 0.14); st += (hot(uv + vec2(o, 0.0)) + hot(uv - vec2(o, 0.0))) * w; }
        c += st * vec3(1.0, 0.72, 0.30) * uStreak;
        c += vec3(1.0, 0.8, 0.5) * band * 0.9;
        gl_FragColor = vec4(c, 1.0);
      }`,
  };
}
export function gradeShader() {
  return {
    uniforms: { tDiffuse: { value: null }, uGrade: { value: 0 }, uContrast: { value: 1 }, uExposure: { value: 1 }, uFlash: { value: 0 },
      uScan: { value: 0 }, uGlitch: { value: 0 }, uRGB: { value: 0 }, uFrame: { value: 0 }, uGrain: { value: 0.035 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
    fragmentShader: `uniform sampler2D tDiffuse; uniform float uGrade, uContrast, uExposure, uFlash, uScan, uGlitch, uRGB, uFrame, uGrain; varying vec2 vUv;
      float h(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233)) + uFrame*0.618)*43758.5453); }
      float h1(float n){ return fract(sin(n)*43758.5453); }
      void main(){
        vec2 uv = vUv;
        // glitch slices (C, and exit accents): horizontal bands displaced on seeded frames
        float bandI = floor(uv.y * 28.0); float gOn = step(1.0 - uGlitch * 0.22, h1(bandI * 3.7 + uFrame * 1.31));
        uv.x += gOn * (h1(bandI * 9.1 + uFrame) - 0.5) * 0.06 * uGlitch;
        float split = (uRGB * 0.0025 + gOn * uGlitch * 0.006);
        vec3 c = vec3(texture2D(tDiffuse, uv + vec2(split, 0.0)).r, texture2D(tDiffuse, uv).g, texture2D(tDiffuse, uv - vec2(split, 0.0)).b);
        c *= uExposure;
        if (uGrade > 0.0) {
          float lum = dot(c, vec3(0.2126, 0.7152, 0.0722));
          vec3 teal = vec3(-0.012, 0.018, 0.028), amber = vec3(0.05, 0.012, -0.045);
          vec3 g = c + teal * pow(1.0 - clamp(lum * 1.6, 0.0, 1.0), 2.0) + amber * pow(clamp(lum, 0.0, 1.0), 2.0);
          g = clamp((g - 0.035) / 0.965, 0.0, 1.0);                                   // deeper blacks
          g = mix(g, g * g * (3.0 - 2.0 * g), clamp(uContrast - 1.0, 0.0, 1.0) * 1.6); // S-curve
          float l2 = dot(g, vec3(0.2126, 0.7152, 0.0722)); g = mix(vec3(l2), g, 1.08);
          c = mix(c, g, uGrade);
        }
        c += vec3(1.0, 0.93, 0.82) * uFlash * 0.28;
        c *= 1.0 - uScan * 0.07 * (0.5 + 0.5 * sin(vUv.y * 1080.0 * 3.14159));
        float n = h(floor(vUv * vec2(1920.0, 1080.0))) - 0.5;
        gl_FragColor = vec4(c + n * uGrain, 1.0);
      }`,
  };
}

// ---------------------------------------------------------------------------------------------
// particles: depth sparks along the camera path (lit, beat-pulsed) + data streams along the t-axis + warp lines
export function makeSparks(THREE, samplesAlongPath, count, softTexHint) {
  const N = count, pos = new Float32Array(N * 3), seed = new Float32Array(N), size = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    const p = samplesAlongPath[Math.floor(hash(i * 1.3) * samplesAlongPath.length)];
    const a = hash(i * 2.1) * Math.PI * 2, r = 1.2 + Math.pow(hash(i * 3.3), 0.7) * 9;
    pos[3 * i] = p.x + Math.cos(a) * r; pos[3 * i + 1] = p.y + Math.sin(a) * r * 0.6; pos[3 * i + 2] = p.z + (hash(i * 5.7) - 0.5) * 8;
    seed[i] = hash(i * 7.9); size[i] = 0.5 + 1.5 * Math.pow(hash(i * 9.1), 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3)); g.setAttribute("aSeed", new THREE.BufferAttribute(seed, 1)); g.setAttribute("aSize", new THREE.BufferAttribute(size, 1));
  const m = new THREE.ShaderMaterial({
    uniforms: { uTime: { value: 0 }, uPulse: { value: 0 }, uAmt: { value: 1 }, uFog: { value: 0.02 } },
    vertexShader: `attribute float aSeed; attribute float aSize; uniform float uTime, uPulse, uFog; varying float vA; varying float vS;
      void main(){ vec3 p = position; p.y += sin(uTime * (0.3 + aSeed) + aSeed * 40.0) * 0.25 + uPulse * 0.12 * (aSeed - 0.3); p.x += cos(uTime * 0.21 + aSeed * 17.0) * 0.18;
        vec4 mv = modelViewMatrix * vec4(p, 1.0); float d = -mv.z; gl_Position = projectionMatrix * mv;
        gl_PointSize = min(22.0, aSize * (1.0 + uPulse * 0.8) * 200.0 / max(d, 0.5));
        vA = exp(-uFog * uFog * d * d * 0.6) * smoothstep(0.3, 1.5, d); vS = aSeed; }`,
    fragmentShader: `uniform float uAmt, uPulse; varying float vA; varying float vS;
      void main(){ vec2 q = gl_PointCoord - 0.5; float r = length(q); float a = smoothstep(0.5, 0.0, r); a *= a;
        vec3 col = mix(vec3(1.0, 0.72, 0.28), vec3(1.0, 0.95, 0.85), step(0.7, vS)) * (1.2 + uPulse * 1.6);
        gl_FragColor = vec4(col, a * vA * uAmt * (0.35 + 0.65 * step(0.4, vS))); }`,
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false,
  });
  const pts = new THREE.Points(g, m); pts.frustumCulled = false; return pts;
}
export function makeStreams(THREE, n = 900, len = 300) {
  const pos = new Float32Array(n * 6), g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.LineBasicMaterial({ color: new THREE.Color(2.2, 1.55, 0.4), transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
  const lines = new THREE.LineSegments(g, mat); lines.frustumCulled = false;
  lines.userData.update = (t, amt, zEnd) => {
    for (let i = 0; i < n; i++) {
      const lane = Math.floor(hash(i * 1.7) * 6), ang = lane / 6 * Math.PI * 2 + 0.3, rr = 0.05 + 0.08 * hash(i * 2.9);
      const speed = 18 + 30 * hash(i * 3.1), ph = hash(i * 4.3) * len;
      const z = -(((t * speed + ph) % len)) - 1; const L = 0.25 + speed * 0.02;
      const x = Math.cos(ang) * rr, y = Math.sin(ang) * rr;
      pos[6 * i] = x; pos[6 * i + 1] = y; pos[6 * i + 2] = z; pos[6 * i + 3] = x; pos[6 * i + 4] = y; pos[6 * i + 5] = z - L;
    }
    g.attributes.position.needsUpdate = true; mat.opacity = 0.75 * amt; lines.visible = amt > 0.01 && t < zEnd;
  };
  return lines;
}
export function makeWarpLines(THREE, n = 520) {
  const pos = new Float32Array(n * 6), g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const mat = new THREE.LineBasicMaterial({ color: new THREE.Color(1.5, 1.35, 1.1), transparent: true, opacity: 0, blending: THREE.AdditiveBlending, depthWrite: false, depthTest: false, toneMapped: false });
  const lines = new THREE.LineSegments(g, mat); lines.frustumCulled = false; lines.renderOrder = 5;
  lines.userData.update = (t, speed, amt) => { // camera-space: lines stream past the lens, length ~ camera speed
    const k = clamp((speed - 9) / 40) * amt, L = 0.4 + speed * 0.06;
    for (let i = 0; i < n; i++) {
      const a = hash(i * 1.9) * Math.PI * 2, r = 0.9 + hash(i * 2.7) * 3.2;
      const z = -(2 + ((t * (14 + speed * 1.2) + hash(i * 3.9) * 40) % 40));
      pos[6 * i] = Math.cos(a) * r; pos[6 * i + 1] = Math.sin(a) * r * 0.62; pos[6 * i + 2] = z;
      pos[6 * i + 3] = pos[6 * i]; pos[6 * i + 4] = pos[6 * i + 1]; pos[6 * i + 5] = z - L;
    }
    g.attributes.position.needsUpdate = true; mat.opacity = 0.55 * k; lines.visible = k > 0.01;
  };
  return lines;
}

// ---------------------------------------------------------------------------------------------
// kinetic type: seeded decode/scramble + tracking-in + light sweep + glitch exit, redrawn only when its state changes
const GLYPHS = "01<>/\\|[]{}#%&*+=-_:;ABCDEFHKMNRSTXZ▮▯";
export function textMaterial(THREE, tex) {
  const mat = new THREE.ShaderMaterial({
    uniforms: { map: { value: tex }, uOpacity: { value: 0 }, uSweep: { value: -1 }, uGlitch: { value: 0 }, uFrame: { value: 0 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
    fragmentShader: `uniform sampler2D map; uniform float uOpacity, uSweep, uGlitch, uFrame; varying vec2 vUv;
      float h1(float n){ return fract(sin(n)*43758.5453); }
      void main(){
        vec2 uv = vUv; float b = floor(uv.y * 14.0); float on = step(1.0 - uGlitch * 0.5, h1(b * 5.3 + uFrame * 0.77));
        uv.x += on * (h1(b * 11.7 + uFrame) - 0.5) * 0.08 * uGlitch;
        vec4 c = texture2D(map, uv);
        float rs = uGlitch * 0.006 * on; c.r = texture2D(map, uv + vec2(rs, 0.0)).r; c.b = texture2D(map, uv - vec2(rs, 0.0)).b;
        float sw = exp(-pow((vUv.x - uSweep) / 0.07, 2.0));
        c.rgb = mix(c.rgb, vec3(1.0, 0.8, 0.45) * max(max(c.r, c.g), c.b), sw * 0.6); // a gold band across the glyphs; never brighter than the glyph
        gl_FragColor = vec4(c.rgb, c.a * uOpacity);
      }`,
    transparent: true, depthWrite: false, toneMapped: false,
  });
  Object.defineProperty(mat, "opacity", { get() { return mat.uniforms.uOpacity.value; }, set(v) { if (mat.uniforms) mat.uniforms.uOpacity.value = v; } });
  return mat;
}
// lines: [{text,size,weight,font,color,track}] → { canvas, tex, draw(key, tRel), contentFrac }
export function makeDynText(THREE, lines, { pad = 24, lineGap = 0.4, spread = 0.22, fontStr, decodeDur = 0.3, seed = 1 }) { // Phase B: must-read text resolves in <= 0.3 s
  const c = document.createElement("canvas"), g = c.getContext("2d");
  let w = 0, h = pad * 2;
  const L = lines.map((l, i) => {
    g.font = fontStr(l); g.letterSpacing = "0px";
    const chars = [...l.text], xs = []; let acc = 0; const tr = (l.track || 0) * l.size;
    chars.forEach((ch, k) => { xs.push(acc); acc += g.measureText(ch).width + tr; });
    const lw = acc; w = Math.max(w, lw); const lh = l.size * 1.12 + (i ? l.size * lineGap : 0); h += lh;
    return { ...l, chars, xs, lw };
  });
  const M = 1 + spread; c.width = Math.ceil(w * M + pad * 2); c.height = Math.ceil(h);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 8; tex.minFilter = THREE.LinearMipmapLinearFilter;
  const total = L.reduce((s, l) => s + l.chars.length, 0);
  let lastKey = null;
  function draw(tRel, P) {
    // state: decoded fraction per char + tracking amount; key changes every 2 frames during the decode window only
    const dec = P.decode > 0 && tRel < decodeDur + 0.05, trk = P.decode > 0 && tRel < 0.5;
    const key = tRel < 0 ? "pre" : dec || trk ? `d${Math.floor(tRel * 15)}` : "final";
    if (key === lastKey) return false; lastKey = key;
    if (key !== "final") tRel = Math.floor(Math.max(0, tRel) * 15) / 15 + (tRel < 0 ? -1 : 0); // state is a pure function of the key (order-independent rendering)
    g.clearRect(0, 0, c.width, c.height);
    const ease = 1 - Math.pow(1 - clamp(tRel / 0.5), 3); const sp = trk ? spread * 0.9 * (1 - ease) : 0;
    let y = pad, gi = 0;
    L.forEach((l, li) => {
      if (li) y += l.size * lineGap;
      g.font = fontStr(l); g.textBaseline = "top"; g.letterSpacing = "0px";
      const x0 = (c.width - l.lw) / 2, cx = c.width / 2;
      l.chars.forEach((ch, k) => {
        const idx = gi + k, thr = decodeDur * (0.75 * (idx / Math.max(1, total)) + 0.25 * hash(idx * 7.3 + seed));
        const resolved = !dec || tRel >= thr || ch === " ";
        const bucket = Math.floor(Math.max(0, tRel) * 15);
        let glyph = ch, col = l.color || "#EDEDEF";
        if (!resolved) {
          const pool = /[㐀-鿿]/.test(ch) ? l.text.replace(/\s/g, "") : GLYPHS;
          glyph = pool[Math.floor(hash(idx * 13.1 + bucket * 1.7 + seed) * pool.length)] || "▮"; col = "#FFB224";
          if (tRel < 0) glyph = "";
        }
        const x = cx + (x0 + l.xs[k] - cx) * (1 + sp);
        g.fillStyle = col; g.globalAlpha = resolved ? 1 : 0.8; g.fillText(glyph, x, y + l.size * 0.06);
      });
      g.globalAlpha = 1; gi += l.chars.length; y += l.size * 1.12;
    });
    tex.needsUpdate = true; return true;
  }
  draw(99, { decode: 0 });
  return { canvas: c, tex, draw, contentFrac: (w + pad * 2) / c.width };
}

// ---------------------------------------------------------------------------------------------
// energy conduit: a tube whose lit part (uFill, 0..1 along its length) and bright head are set from t
export function tubeMat(THREE, dim = 0.18) {
  return new THREE.ShaderMaterial({
    uniforms: { uFill: { value: 0 }, uHead: { value: 1 }, uDim: { value: dim }, uGain: { value: 1 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }",
    fragmentShader: `uniform float uFill, uHead, uDim, uGain; varying vec2 vUv;
      void main(){ float on = step(vUv.x, uFill); float head = exp(-pow((vUv.x - uFill) / 0.012, 2.0)) * uHead * step(0.001, uFill) * step(uFill, 0.999);
        vec3 amber = vec3(1.0, 0.7, 0.14); vec3 c = mix(vec3(uDim), amber * 1.12 * uGain, on) + amber * 2.2 * head; gl_FragColor = vec4(c, 1.0); }`,
    toneMapped: false,
  });
}
