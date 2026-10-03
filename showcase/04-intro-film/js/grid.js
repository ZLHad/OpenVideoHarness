// The opening from 15 s on, in WebGL: the film grid under the stars, the title, the rows collapsing into the terminal's
// lines. It takes over from the Blender plate with the same cards, films and camera (exported from blender/galaxy.py by
// tools/export_state.py), so the hand-over is a dissolve between two renders of one scene.
// Blender is Z-up with a horizontal field of view; three.js is Y-up with a vertical one: (x, y, z) → (x, z, −y).
import * as THREE from "three";

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const seg = (t, a, b) => clamp((t - a) / (b - a));
const smooth = (u) => { u = clamp(u); return u * u * (3 - 2 * u); };
const lerp = (a, b, u) => a + (b - a) * u;
const B2T = (x, y, z) => new THREE.Vector3(x, z, -y);

const VERT = /* glsl */ `
attribute vec4 aFilm;   // kind (0 procedural, 1 footage, 2 AI), row, phase, line width factor (for the collapse)
varying vec2 vUv; varying vec4 vFilm;
void main(){ vUv = uv; vFilm = aFilm; gl_Position = projectionMatrix * modelViewMatrix * instanceMatrix * vec4(position, 1.0); }`;
const FRAG = /* glsl */ `
uniform sampler2D tProc, tReal, tAI; uniform float uRows0, uRows1, uRows2, uT, uVis, uAmber, uGray;
varying vec2 vUv; varying vec4 vFilm;
vec3 tap(float kind, float row, float fr, vec2 uv){
  float rows = kind < 0.5 ? uRows0 : (kind < 1.5 ? uRows1 : uRows2);
  vec2 a = vec2((fr + 0.5 + (uv.x - 0.5) * 0.992) / 16.0, 1.0 - (row + 0.5 - (uv.y - 0.5) * 0.99) / rows);
  if (kind < 0.5) return pow(texture2D(tProc, a).rgb, vec3(2.2));            // stored gamma-encoded, no colour tag (as in Blender)
  if (kind < 1.5) return texture2D(tReal, a).rgb;
  return texture2D(tAI, a).rgb;
}
float frameOf(float k, float kind){ float m = mod(k, 30.0); return kind > 0.5 ? (m < 16.0 ? m : 30.0 - m) : mod(k, 16.0); }
void main(){
  float fpos = uT * 8.0 + vFilm.z; float k0 = floor(fpos); float fm = fpos - k0;
  vec3 c = mix(tap(vFilm.x, vFilm.y, frameOf(k0, vFilm.x), vUv), tap(vFilm.x, vFilm.y, frameOf(k0 + 1.0, vFilm.x), vUv), fm);
  float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
  c = mix(c, vec3(l), uGray);
  c = mix(c, vec3(l) * vec3(1.0, 0.62, 0.12), uAmber);
  gl_FragColor = vec4(c * 2.2 * uVis, 1.0);
  #include <tonemapping_fragment>
  #include <colorspace_fragment>
}`;

export async function makeGrid(canvas) {
  const S = await (await fetch("assets/state.json")).json();
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(Math.max(1, Math.round(window.devicePixelRatio || 1))); renderer.setSize(1920, 1080, false);   // 2 at --resolution 4k
  renderer.outputColorSpace = THREE.SRGBColorSpace; renderer.toneMapping = THREE.AgXToneMapping; renderer.toneMappingExposure = 1.0;
  const scene = new THREE.Scene(); scene.background = new THREE.Color(0, 0, 0);
  const camera = new THREE.PerspectiveCamera(40, 1920 / 1080, 0.3, 4000);
  const load = (u, srgb) => new Promise((res) => new THREE.TextureLoader().load(u, (t) => {
    t.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace; t.anisotropy = renderer.capabilities.getMaxAnisotropy();
    t.generateMipmaps = true; t.minFilter = THREE.LinearMipmapLinearFilter; res(t); }));
  const [tProc, tReal, tAI] = await Promise.all([load("assets/films-proc.png", false), load("assets/films.jpg", true), load("assets/films-ai.jpg", true)]);

  // cards: one instanced quad each, lying on the Blender plane (z = 0.003) at its grid slot
  const C = S.cards, N = C.sx.length, CW = S.grid.CW, w = CW * 0.86, h = w * 9 / 16;
  const geo = new THREE.PlaneGeometry(1, 1); geo.rotateX(-Math.PI / 2);         // a three.js XZ quad = a Blender XY quad
  const aFilm = new Float32Array(N * 4);
  for (let i = 0; i < N; i++) aFilm.set([C.kind[i], C.row[i], C.ph[i], 0.45 + 0.55 * 0.5 * (1 + Math.sin(C.sy[i] * 7.1))], i * 4);
  geo.setAttribute("aFilm", new THREE.InstancedBufferAttribute(aFilm, 4));
  const mat = new THREE.ShaderMaterial({ vertexShader: VERT, fragmentShader: FRAG,
    uniforms: { tProc: { value: tProc }, tReal: { value: tReal }, tAI: { value: tAI }, uRows0: { value: 28 }, uRows1: { value: 41 }, uRows2: { value: S.nai },
      uT: { value: 0 }, uVis: { value: 1 }, uAmber: { value: 0.14 }, uGray: { value: 0.78 } } });
  const cards = new THREE.InstancedMesh(geo, mat, N); cards.frustumCulled = false; scene.add(cards);
  const m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), sc = new THREE.Vector3(), p = new THREE.Vector3();
  function placeCards(col) {
    for (let i = 0; i < N; i++) {
      const wf = lerp(1, aFilm[i * 4 + 3], col);
      p.copy(B2T(C.sx[i], C.sy[i], 0.003)); sc.set(w * wf, 1, h * lerp(1, 0.1, col));   // Blender width → x, height → −y
      m4.compose(p, q, sc); cards.setMatrixAt(i, m4);
    }
    cards.instanceMatrix.needsUpdate = true;
  }
  // grid hairlines (amber), as in Blender: every row and column boundary
  const GC = S.grid.GC, GR = Math.ceil(N / GC), xs = [], ys = [];
  for (let k = 0; k <= GC; k++) xs.push((k - GC / 2) * CW);
  for (let r = 0; r <= GR; r++) ys.push(-24.0 - S.grid.CH / 2 + r * S.grid.CH);
  // hairlines as thin quads on the plane (0.035 wide, as in Blender), so they keep their width with distance
  const lp = [], lw = 0.035, quad = (a, b, c, d) => lp.push(...a, ...b, ...c, ...a, ...c, ...d);
  for (const x of xs) quad(B2T(x - lw, ys[0], 0.006).toArray(), B2T(x + lw, ys[0], 0.006).toArray(), B2T(x + lw, ys[ys.length - 1], 0.006).toArray(), B2T(x - lw, ys[ys.length - 1], 0.006).toArray());
  for (const y of ys) quad(B2T(xs[0], y - lw, 0.006).toArray(), B2T(xs[xs.length - 1], y - lw, 0.006).toArray(), B2T(xs[xs.length - 1], y + lw, 0.006).toArray(), B2T(xs[0], y + lw, 0.006).toArray());
  const lg = new THREE.BufferGeometry(); lg.setAttribute("position", new THREE.Float32BufferAttribute(lp, 3));
  const lineMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.0, 0.62, 0.12), transparent: true, opacity: 0.5, side: THREE.DoubleSide, depthWrite: false });
  const lines = new THREE.Mesh(lg, lineMat); lines.frustumCulled = false; lines.renderOrder = 2; scene.add(lines);
  // the far sky (the upper half of Blender's: same seeds)
  const sky = S.sky, sp = new Float32Array(sky.length * 3), scol = new Float32Array(sky.length * 3);
  sky.forEach((s, i) => { const v = B2T(s[0], s[1], s[2]).multiplyScalar(1400); sp.set(v.toArray(), i * 3); const b = Math.min(1.8, 0.25 + s[4] * s[3] * s[3] * 0.3); scol.set([b * 0.85, b * 0.9, b], i * 3); });
  const sg = new THREE.BufferGeometry(); sg.setAttribute("position", new THREE.BufferAttribute(sp, 3)); sg.setAttribute("color", new THREE.BufferAttribute(scol, 3));
  const dome = new THREE.Mesh(new THREE.SphereGeometry(1800, 48, 24), new THREE.ShaderMaterial({ side: THREE.BackSide, depthWrite: false,
    vertexShader: "varying vec3 vD; void main(){ vD = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: `varying vec3 vD; void main(){ float h = vD.y; vec3 c = mix(vec3(0.0016, 0.0015, 0.0019), vec3(0.0003, 0.0004, 0.0008), smoothstep(0.0, 0.35, h));
      c += vec3(0.16, 0.11, 0.05) * exp(-abs(h) * 24.0) * 0.09; gl_FragColor = vec4(c, 1.0);   // linear: matches the Blender sky (sRGB ~1 above, ~33 at the horizon)
      #include <tonemapping_fragment>
      #include <colorspace_fragment>
    }` }));
  dome.frustumCulled = false; dome.renderOrder = -2; scene.add(dome);
  const stars = new THREE.Points(sg, new THREE.PointsMaterial({ size: 2.6, sizeAttenuation: false, vertexColors: true, transparent: true, depthWrite: false }));
  stars.frustumCulled = false; stars.renderOrder = -1; scene.add(stars);

  const up = new THREE.Vector3(), fw = new THREE.Vector3(), rt = new THREE.Vector3(), mm = new THREE.Matrix4();
  return (t, ta = t) => {   // t: the story's time; ta: the film's own time (the cards' films keep playing in a stretched hold)
    const n = clamp(Math.round((t - S.cam_t0) * 30), 0, S.cam.length - 1), c = S.cam[n];
    camera.position.copy(B2T(c[0], c[1], c[2]));
    fw.copy(B2T(c[3], c[4], c[5])).normalize(); up.copy(B2T(c[6], c[7], c[8]));
    rt.crossVectors(fw, up).normalize(); up.crossVectors(rt, fw).normalize();
    const roll = c[9], cr = Math.cos(roll), sr = Math.sin(roll);
    const r2 = rt.clone().multiplyScalar(cr).addScaledVector(up, sr), u2 = up.clone().multiplyScalar(cr).addScaledVector(rt, -sr);
    mm.makeBasis(r2, u2, fw.clone().negate()); camera.quaternion.setFromRotationMatrix(mm);
    const hf = THREE.MathUtils.degToRad(c[10]); camera.fov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(hf / 2) / (1920 / 1080))); camera.updateProjectionMatrix();
    const col = smooth(seg(t, 18.55, 19.1));
    placeCards(col);
    const U = mat.uniforms; U.uT.value = ta;
    U.uVis.value = 0.95 * lerp(1.0, 0.62, smooth(seg(t, 15.6, 16.6))) * lerp(1.0, 1.25, col);
    U.uAmber.value = Math.min(1, 0.14 + 0.7 * col); U.uGray.value = lerp(0.78, 0.45, smooth(seg(t, 15.6, 16.8))) + 0.4 * col;
    lineMat.opacity = 0.42 * (1 - 0.6 * smooth(seg(t, 18.6, 19.2)));
    renderer.render(scene, camera);
  };
}
