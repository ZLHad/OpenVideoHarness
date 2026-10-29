// canvas-film · the Three.js layer (ENGINE_README.md, "Three.js 层"). src/07-three.js imports this module in ready when
// FILM.three is set: it loads the models (glTF files in the project), builds one world from the settings (camera, lights,
// environment, background, tone mapping) and lets FILM.three.build add what the files do not have. A shot with a three
// field then has its 3D drawn first, into the canvas the shot draws into (the frame, or a transition's buffer), so what
// its draw(t, s) paints lies over it, and the chapter bar and the caption go over both as ever.
//
// Hard rule 1. A frame starts from the world as ready left it: every object's position, rotation, scale and visibility,
// each light's colour and intensity, each mesh's morph weights are put back before anything is posed, so nothing a frame
// changes reaches the next. Each model's clips are stopped and played again for the frame, and the mixer is set to the
// film time with mixer.setTime(t): a clip's time is (t − at) × speed, wrapped or held as its loop says, never a sum of
// update(dt) steps. The camera is the shot's cam at t, else FILM.three.camera. pose(t, s, W3) may set anything after
// that; an object it adds or takes away stops the frame (build it in build(), show or hide it in pose()).
//
// three.js is pinned in ./build and ./addons (three.js r186, MIT: LICENSES/MIT-three.js.txt, NOTICE.md).
import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

export const REVISION = THREE.REVISION;
const DEG = Math.PI / 180;
const isNum = (x) => typeof x === "number" && Number.isFinite(x);
const lerp = (a, b, u) => a + (b - a) * u;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const EASE = {
  linear: (u) => u,
  sine: (u) => (1 - Math.cos(Math.PI * u)) / 2,
  inOut: (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2),
  in: (u) => u * u * u,
  out: (u) => 1 - Math.pow(1 - u, 3),
};
const TONES = { agx: THREE.AgXToneMapping, aces: THREE.ACESFilmicToneMapping, neutral: THREE.NeutralToneMapping, linear: THREE.LinearToneMapping, none: THREE.NoToneMapping };
const SETTINGS = ["models", "camera", "lights", "env", "envIntensity", "envRotation", "envLight", "background", "backgroundBlur", "tone", "exposure", "shadows", "antialias", "build"];
const VIEW = ["pos", "at", "fov", "lens", "near", "far", "roll"];
const SHOT = ["cam", "show", "play", "pose", "background"];
const PLAY = ["clip", "at", "speed", "loop", "weight", "hold"];
const fail = (msg) => { throw new Error(`canvas-film: ${msg}`); };
const unknown = (o, keys, what) => { const x = Object.keys(o).filter((k) => !keys.includes(k)); if (x.length) fail(`${what} has ${x.join(", ")}, which the layer does not read (${keys.join(", ")})`); };
function vec(a, what) {
  if (!Array.isArray(a) || a.length !== 3 || !a.every(isNum)) fail(`${what} is [x, y, z] in metres: ${JSON.stringify(a)}`);
  return a;
}
// a view: the camera's pos, at (where it looks), fov (vertical, degrees) or lens (mm on 36 mm film, as Blender's), near,
// far, roll (degrees about the line of sight); what a view leaves out is FILM.three.camera's
function view(o, what) {
  if (!o || typeof o !== "object" || Array.isArray(o)) fail(`${what} is a view: { pos: [x, y, z], at: [x, y, z], fov or lens, roll }`);
  unknown(o, VIEW, what);
  for (const k of ["pos", "at"]) if (o[k] !== undefined) vec(o[k], `${what}.${k}`);
  for (const k of ["fov", "lens", "near", "far", "roll"]) if (o[k] !== undefined && !isNum(o[k])) fail(`${what}.${k} is a number: ${JSON.stringify(o[k])}`);
  return o;
}
function place(obj, o, what) {   // pos (m), rot ([x, y, z] degrees, XYZ order), scale (a number or [x, y, z])
  if (o.pos !== undefined) obj.position.fromArray(vec(o.pos, `${what}.pos`));
  if (o.rot !== undefined) { const r = vec(o.rot, `${what}.rot`); obj.rotation.set(r[0] * DEG, r[1] * DEG, r[2] * DEG); }
  if (o.scale !== undefined) {
    if (isNum(o.scale)) obj.scale.setScalar(o.scale); else obj.scale.fromArray(vec(o.scale, `${what}.scale`));
  }
}
const colour = (c, what) => { try { return new THREE.Color(c); } catch { return fail(`${what}: ${JSON.stringify(c)} is not a colour`); } };

function light(L, i) {
  const what = `FILM.three.lights[${i}]`;
  if (!L || typeof L !== "object") fail(`${what} is { type: "sun" | "point" | "spot" | "hemi" | "ambient", … }`);
  unknown(L, ["type", "color", "intensity", "pos", "at", "shadow", "shadowArea", "shadowSize", "sky", "ground", "distance", "decay", "angle", "penumbra"], what);
  const c = L.color !== undefined ? colour(L.color, `${what}.color`) : new THREE.Color(0xffffff), k = L.intensity ?? 1;
  if (!isNum(k)) fail(`${what}.intensity is a number`);
  let l;
  switch (L.type) {
    case "ambient": l = new THREE.AmbientLight(c, k); break;
    case "hemi": l = new THREE.HemisphereLight(colour(L.sky ?? "#ffffff", `${what}.sky`), colour(L.ground ?? "#444444", `${what}.ground`), k); break;
    case "sun": case "directional": l = new THREE.DirectionalLight(c, k); break;
    case "point": l = new THREE.PointLight(c, k, L.distance ?? 0, L.decay ?? 2); break;
    case "spot": l = new THREE.SpotLight(c, k, L.distance ?? 0, (L.angle ?? 30) * DEG, L.penumbra ?? 0.3, L.decay ?? 2); break;
    default: fail(`${what}.type: sun, point, spot, hemi or ambient, not ${JSON.stringify(L.type)}`);
  }
  l.name = `light${i}`;
  if (L.pos !== undefined) l.position.fromArray(vec(L.pos, `${what}.pos`));
  else if (l.isDirectionalLight || l.isSpotLight) l.position.set(3, 6, 4);
  if (l.target) { l.target.position.fromArray(L.at !== undefined ? vec(L.at, `${what}.at`) : [0, 0, 0]); l.target.name = `light${i}.target`; }
  if (L.shadow && l.shadow) {
    l.castShadow = true;
    const n = L.shadowSize ?? 2048;
    l.shadow.mapSize.set(n, n);
    l.shadow.bias = -0.0002; l.shadow.normalBias = 0.02;
    if (l.isDirectionalLight) {   // an orthographic box shadowArea metres across, around the target
      const a = (L.shadowArea ?? 10) / 2, cam = l.shadow.camera, d = l.position.distanceTo(l.target.position);
      cam.left = -a; cam.right = a; cam.top = a; cam.bottom = -a; cam.near = 0.1; cam.far = Math.max(50, d * 3); cam.updateProjectionMatrix();
    }
  }
  return l;
}

// a smaller copy of an equirectangular map, at most w across, for the light: each texel the mean of the f × f of the map
// it stands for (f a whole number: Poly Haven's sizes halve), drawn once on the GPU in ready. → its render target
function shrink(renderer, map, w) {
  const f = Math.ceil(map.image.width / w), W = Math.floor(map.image.width / f), H = Math.floor(map.image.height / f);
  const rt = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: false, generateMipmaps: false,
    minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter });
  rt.texture.mapping = THREE.EquirectangularReflectionMapping;
  const mat = new THREE.ShaderMaterial({ uniforms: { map: { value: map }, f: { value: f } }, depthTest: false, depthWrite: false,
    vertexShader: "void main() { gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: `uniform sampler2D map; uniform int f;
      void main() {
        ivec2 o = ivec2(gl_FragCoord.xy) * f; vec4 s = vec4(0.0);
        for (int j = 0; j < f; j++) for (int i = 0; i < f; i++) s += texelFetch(map, o + ivec2(i, j), 0);
        gl_FragColor = vec4(s.rgb / float(f * f), 1.0);
      }` });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat), sc = new THREE.Scene(), cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  quad.frustumCulled = false;
  sc.add(quad);
  const before = renderer.getRenderTarget(), tone = renderer.toneMapping;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.setRenderTarget(rt); renderer.render(sc, cam); renderer.setRenderTarget(before);
  renderer.toneMapping = tone;
  quad.geometry.dispose(); mat.dispose();
  return rt;
}

// load(FILM.three, { width, height, dpr }) → the layer: { check(shots, problems), draw(ctx, t, s, three, o), models, revision }
export async function load(spec, { width, height, dpr }) {
  if (!spec || typeof spec !== "object" || Array.isArray(spec)) fail("FILM.three is { models, camera, lights, env, background, … } (ENGINE_README.md, Three.js 层)");
  unknown(spec, SETTINGS, "FILM.three");
  const canvas = document.createElement("canvas");
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: spec.antialias !== false, alpha: true, premultipliedAlpha: true, preserveDrawingBuffer: true, powerPreference: "high-performance" });
  } catch (e) {
    fail(`no WebGL2 for the Three.js layer in this browser (${e.message}): a machine without a GPU draws it in software, --soft-gl (bin/vh frames, render, determinism … --soft-gl)`);
  }
  // the drawing buffer as many pixels as the 2D canvas has (src/90-main.js: Math.round(W × dpr)), so at any dpr, 1.333
  // too, draw() copies it pixel for pixel
  renderer.setPixelRatio(1); renderer.setSize(Math.round(width * dpr), Math.round(height * dpr), false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const tone = spec.tone ?? "agx";
  if (!Object.hasOwn(TONES, tone)) fail(`FILM.three.tone: ${Object.keys(TONES).join(", ")}, not ${JSON.stringify(tone)}`);   // own names only: "constructor" is in every object
  renderer.toneMapping = TONES[tone];
  renderer.toneMappingExposure = spec.exposure ?? 1;
  renderer.shadowMap.enabled = !!spec.shadows;
  renderer.shadowMap.type = THREE.PCFShadowMap;   // soft since r182

  const scene = new THREE.Scene();
  const rot = new THREE.Euler(), r = spec.envRotation ?? 0;
  if (isNum(r)) rot.set(0, r * DEG, 0); else { const v = vec(r, "FILM.three.envRotation"); rot.set(v[0] * DEG, v[1] * DEG, v[2] * DEG); }
  const envIntensity = spec.envIntensity ?? 1;
  if (!isNum(envIntensity) || envIntensity < 0) fail("FILM.three.envIntensity is a number, 0 or more");
  const envLight = spec.envLight ?? 2048;
  if (!(Number.isInteger(envLight) && envLight >= 64)) fail("FILM.three.envLight is the widest map the light is made from, in pixels: a whole number, 64 or more");
  // env: the light (a PMREM map). envMap: what a sharp background "env" shows, the map itself, kept only while a shot
  // shows it (check() lets it go otherwise)
  let env = null, envMap = null;
  if (spec.env === "room") {   // a neutral studio three makes from a few boxes and lights: no file
    const pm = new THREE.PMREMGenerator(renderer), room = new RoomEnvironment();
    env = envMap = pm.fromScene(room, 0.04).texture;
    room.dispose(); pm.dispose();
  } else if (typeof spec.env === "string" && /\.(hdr|exr)$/i.test(spec.env)) {   // an equirectangular HDRI (bin/vh hdri get)
    const exr = /\.exr$/i.test(spec.env);
    const mod = await import(exr ? "three/addons/loaders/EXRLoader.js" : "three/addons/loaders/HDRLoader.js");
    let map;
    try { map = await new (exr ? mod.EXRLoader : mod.HDRLoader)().loadAsync(spec.env); }
    catch (e) { fail(`FILM.three.env: ${spec.env} did not load (${(e && e.message) || e}): bin/vh hdri get <project> <name> puts one in assets/hdri/`); }
    map.mapping = THREE.EquirectangularReflectionMapping;
    // the light from a copy at most envLight across: three's PMREM grows with the map (a quarter of its width a cube
    // face), and an 8k map would make a 400 MB light for what a 2k one lights as well
    const small = map.image.width > envLight ? shrink(renderer, map, envLight) : null;
    const pm = new THREE.PMREMGenerator(renderer);
    env = pm.fromEquirectangular(small ? small.texture : map).texture;
    pm.dispose();
    if (small) small.dispose();
    envMap = map;
  } else if (spec.env !== undefined && spec.env !== null) fail(`FILM.three.env: "room" (a neutral studio, no file), an .hdr or .exr file (bin/vh hdri get), or null, not ${JSON.stringify(spec.env)}`);

  for (const [i, L] of (spec.lights ?? (env ? [] : [{ type: "hemi", intensity: 1.2 }, { type: "sun", intensity: 2.5, pos: [3, 6, 4] }])).entries()) {
    const l = light(L, i);
    scene.add(l);
    if (l.target) scene.add(l.target);
  }

  // the models: every file loaded before ready resolves, each under a group of its own that the settings place
  const M = {}, loader = new GLTFLoader();
  const list = Object.entries(spec.models ?? {}).map(([key, m]) => {
    const o = typeof m === "string" ? { src: m } : m;
    if (!/^[A-Za-z_][A-Za-z0-9_]*$/.test(key)) fail(`FILM.three.models: "${key}" is not a name (letters, digits and _)`);
    if (!o || typeof o !== "object" || typeof o.src !== "string") fail(`FILM.three.models.${key}: a path ("assets/models/x.glb") or { src, pos, rot, scale }`);
    unknown(o, ["src", "pos", "rot", "scale", "cast", "receive"], `FILM.three.models.${key}`);
    return [key, o];
  });
  const got = await Promise.all(list.map(async ([key, o]) => {
    try { return [key, o, await loader.loadAsync(o.src)]; }
    catch (e) {   // a file that is not there comes back with its HTTP response; any other failure is the file's own
      const why = e && e.response ? "" : `; bin/vh model3d check ${o.src} says what is wrong with the file`;
      return fail(`model "${key}" (${o.src}, FILM.three.models) did not load: ${(e && e.message) || e}${why}`);
    }
  }));
  for (const [key, o, gltf] of got) {   // in the order the settings list them, whichever file arrived first
    const root = new THREE.Group();
    root.name = key;
    root.add(gltf.scene);
    place(root, o, `FILM.three.models.${key}`);
    gltf.scene.traverse((x) => {
      if (x.isMesh) { x.castShadow = o.cast ?? true; x.receiveShadow = o.receive ?? true; }
      if (x.isSkinnedMesh) x.frustumCulled = false;   // its bounding sphere would be taken once, from whatever pose it first drew in
    });
    const clips = Object.create(null);   // no prototype: a clip named constructor or toString is a clip like any other
    for (const c of gltf.animations) if (!(c.name in clips)) clips[c.name] = c;   // two of one name: the first (bin/vh model3d check says so)
    M[key] = { key, src: o.src, root, scene: gltf.scene, gltf, clips, mixer: new THREE.AnimationMixer(gltf.scene) };
    scene.add(root);
  }

  const cam0 = { pos: [0, 1.6, 6], at: [0, 1, 0], fov: 35, near: 0.05, far: 500, roll: 0, ...view(spec.camera ?? {}, "FILM.three.camera") };
  const camera = new THREE.PerspectiveCamera(cam0.fov, width / height, cam0.near, cam0.far);
  camera.filmGauge = 36;
  const W3 = { THREE, scene, camera, renderer, models: M, env };
  window.THREE = THREE;   // for src/50-shots.js: build() and pose() run after this
  if (spec.build !== undefined) {
    if (typeof spec.build !== "function") fail("FILM.three.build is a function: build(W3) adds what the files do not have");
    await spec.build(W3);
  }

  // the environment on every lit material (Standard, Physical, Lambert, Phong), so a material's own envMapIntensity
  // counts: lit by scene.environment alone, three uses the scene's intensity and ignores the material's
  if (env) {
    scene.environment = env; scene.environmentIntensity = envIntensity; scene.environmentRotation.copy(rot);
    const seen = new Set();
    scene.traverse((x) => {
      for (const m of [].concat(x.material || [])) {
        if (seen.has(m) || !(m.isMeshStandardMaterial || m.isMeshLambertMaterial || m.isMeshPhongMaterial) || m.envMap) continue;
        seen.add(m);
        m.envMap = env; m.envMapIntensity = (m.envMapIntensity ?? 1) * envIntensity; m.envMapRotation.copy(rot); m.needsUpdate = true;
      }
    });
  }
  scene.backgroundRotation.copy(rot);
  const blur = clamp(spec.backgroundBlur ?? 0);
  scene.backgroundBlurriness = blur;
  // background "env": sharp, the map itself; blurred, the light's map (three would make another PMREM of the whole map)
  const BG = (b, what) => {
    if (b === undefined || b === null) return null;
    if (b === "env") return (blur > 0 ? env : envMap) || fail(`${what}: "env" needs FILM.three.env`);
    return colour(b, what);
  };
  const bg0 = BG(spec.background, "FILM.three.background");

  // the world as ready leaves it: put back at the start of every frame
  const REST = [];
  scene.traverse((o) => REST.push({ o, p: o.position.clone(), q: o.quaternion.clone(), s: o.scale.clone(), v: o.visible,
    m: o.matrixAutoUpdate ? null : o.matrix.clone(), i: o.isLight ? o.intensity : undefined, c: o.isLight ? o.color.clone() : null,
    g: o.isHemisphereLight ? o.groundColor.clone() : null, w: o.morphTargetInfluences ? [...o.morphTargetInfluences] : null }));
  const restore = () => {
    for (const r of REST) {
      const o = r.o;
      o.position.copy(r.p); o.quaternion.copy(r.q); o.scale.copy(r.s); o.visible = r.v;
      if (r.m) { o.matrix.copy(r.m); o.matrixWorldNeedsUpdate = true; }
      if (r.i !== undefined) { o.intensity = r.i; o.color.copy(r.c); }
      if (r.g) o.groundColor.copy(r.g);
      if (r.w) for (let k = 0; k < r.w.length; k++) o.morphTargetInfluences[k] = r.w[k];
    }
  };
  const count = () => { let n = 0; scene.traverse(() => n++); return n; };

  function aim(v) {
    camera.position.fromArray(v.pos); camera.up.set(0, 1, 0); camera.lookAt(...v.at);
    if (v.roll) camera.rotateZ(v.roll * DEG);
    camera.near = v.near; camera.far = v.far;
    if (v.lens) camera.setFocalLength(v.lens); else camera.fov = v.fov;
    camera.updateProjectionMatrix(); camera.updateMatrixWorld();
  }
  // a view over the defaults: a fov given without a lens drops the default's lens (lens wins when both are there)
  const over = (o) => { const v = { ...cam0, ...o }; if (o.fov !== undefined && o.lens === undefined) delete v.lens; return v; };
  // a shot's cam at t: a view, keys [[t, view], …] (times resolved in ready), from/to over the shot, or a function
  function viewAt(t, s, N) {
    const c = N.cam;
    if (!c) return cam0;
    if (typeof c === "function") return over(view(c(t, s, W3) || {}, `shot ${s.id} three.cam(t)`));
    const keys = c.keys || (c.from ? [[s.t0, c.from], [s.t1, c.to]] : null);
    if (!keys) return over(c);
    const ease = EASE[c.ease ?? "sine"];
    if (t <= keys[0][0]) return over(keys[0][1]);
    for (let k = 0; k + 1 < keys.length; k++) {
      const [ta, A] = keys[k], [tb, B] = keys[k + 1];
      if (t > tb) continue;
      const u = ease(clamp((t - ta) / Math.max(1e-9, tb - ta))), a = over(A), b = over(B);
      const useLens = a.lens !== undefined || b.lens !== undefined;
      return { pos: a.pos.map((x, i) => lerp(x, b.pos[i], u)), at: a.at.map((x, i) => lerp(x, b.at[i], u)),
        fov: lerp(a.fov, b.fov, u), lens: useLens ? lerp(a.lens ?? lensOf(a.fov), b.lens ?? lensOf(b.fov), u) : undefined,
        near: lerp(a.near, b.near, u), far: lerp(a.far, b.far, u), roll: lerp(a.roll, b.roll, u) };
    }
    return over(keys[keys.length - 1][1]);
  }
  const lensOf = (fov) => (0.5 * camera.getFilmHeight()) / Math.tan(0.5 * fov * DEG);

  // a shot's three, checked and put in the form draw() uses (in ready, once its cues are seconds)
  const NORM = new WeakMap();
  function normalize(S, problems) {
    const sh = S.three, at = `shot ${S.id} (three`;
    const N = { show: null, plays: {}, cam: null, pose: null, background: undefined };
    if (!sh || typeof sh !== "object" || Array.isArray(sh)) { problems.push(`shot ${S.id}: three is { cam, show, play, pose, background }`); return N; }
    try { unknown(sh, SHOT, `shot ${S.id}'s three`); } catch (e) { problems.push(e.message.replace(/^canvas-film: /, "")); }   // said; the rest is checked all the same
    if (sh.show !== undefined) {
      if (!Array.isArray(sh.show)) problems.push(`${at}.show): a list of FILM.three.models names`);
      else {
        for (const k of sh.show) if (!Object.hasOwn(M, k)) problems.push(`${at}.show): no model "${k}" (FILM.three.models: ${Object.keys(M).join(", ") || "none"})`);
        N.show = new Set(sh.show);
      }
    }
    if (sh.pose !== undefined && typeof sh.pose !== "function") problems.push(`${at}.pose): a function, pose(t, s, W3)`);
    else N.pose = sh.pose || null;
    if (sh.background !== undefined) { try { N.background = BG(sh.background, `${at}.background)`); } catch (e) { problems.push(e.message.replace(/^canvas-film: /, "")); } }
    try {
      const c = sh.cam;
      if (c === undefined || typeof c === "function") N.cam = c || null;
      else if (c && typeof c === "object" && (c.keys || c.from || c.to)) {
        unknown(c, ["keys", "from", "to", "ease"], `${at}.cam)`);
        if (c.ease !== undefined && !Object.hasOwn(EASE, c.ease)) fail(`${at}.cam).ease: ${Object.keys(EASE).join(", ")}, not ${JSON.stringify(c.ease)}`);
        if (c.keys) {
          if (c.from || c.to) fail(`${at}.cam): keys, or from and to, not both`);
          if (!Array.isArray(c.keys) || c.keys.length < 2) fail(`${at}.cam).keys: two or more [time, view] (times are cues or seconds)`);
          c.keys.forEach((k, i) => {
            if (!Array.isArray(k) || k.length !== 2 || !isNum(k[0])) fail(`${at}.cam).keys[${i}] is [time, view], its time a cue or seconds: ${JSON.stringify(k)}`);
            view(k[1], `${at}.cam).keys[${i}][1]`);
            if (i && !(k[0] > c.keys[i - 1][0])) fail(`${at}.cam).keys[${i}]: ${k[0]} s does not come after ${c.keys[i - 1][0]} s`);
          });
        } else { view(c.from ?? fail(`${at}.cam): from needs to`), `${at}.cam).from`); view(c.to ?? fail(`${at}.cam): to needs from`), `${at}.cam).to`); }
        N.cam = c;
      } else N.cam = view(c, `${at}.cam)`);
    } catch (e) { problems.push(e.message.replace(/^canvas-film: /, "")); }
    // play: { model: clip | { clip, at, speed, loop, weight, hold } | [those] }. at defaults to the shot's start; loop
    // false (once, holding the last pose), true (a cycle) or "pingpong"
    const play = sh.play ?? {};
    if (!play || typeof play !== "object" || Array.isArray(play)) { problems.push(`${at}.play): { model: clip, … }`); return N; }
    for (const [key, v] of Object.entries(play)) {
      const m = Object.hasOwn(M, key) ? M[key] : null, seen = new Set();   // own names: "constructor" is in every object
      if (!m) { problems.push(`${at}.play): no model "${key}" (FILM.three.models: ${Object.keys(M).join(", ") || "none"})`); continue; }
      for (const raw of [].concat(v)) {
        const p = typeof raw === "string" ? { clip: raw } : raw, w = `${at}.play.${key})`;
        if (!p || typeof p !== "object") { problems.push(`${w}: a clip name, or { clip, at, speed, loop, weight, hold }`); continue; }
        try { unknown(p, PLAY, w); } catch (e) { problems.push(e.message.replace(/^canvas-film: /, "")); continue; }
        const clip = m.clips[p.clip];
        if (!clip) { problems.push(`${w}: ${m.src} has no clip "${p.clip}" (its clips: ${Object.keys(m.clips).join(", ") || "none"}; bin/vh model3d check ${m.src} lists them)`); continue; }
        if (seen.has(p.clip)) { problems.push(`${w}: "${p.clip}" twice in one shot (one action a clip: two plays of it would be one)`); continue; }
        seen.add(p.clip);
        const start = p.at ?? S.t0, speed = p.speed ?? 1, weight = p.weight ?? 1, loop = p.loop ?? false;
        if (!isNum(start)) continue;   // a cue that did not resolve: said above, with the shot and the cue
        if (!(isNum(speed) && speed > 0)) { problems.push(`${w}: speed is a number above 0`); continue; }
        if (!(isNum(weight) && weight >= 0 && weight <= 1)) { problems.push(`${w}: weight is 0 to 1`); continue; }
        if (![true, false, "pingpong"].includes(loop)) { problems.push(`${w}: loop is false (once), true (a cycle) or "pingpong"`); continue; }
        if (start >= S.t1) problems.push(`${w}: "${p.clip}" starts at ${start.toFixed(2)} s, when the shot is over (${S.t1.toFixed(2)} s): it never plays`);
        else if (loop === false && !p.hold && clip.duration > 0) {
          const end = start + clip.duration / speed;
          if (end < S.t1 - 0.01) problems.push(`${w}: "${p.clip}" is ${clip.duration.toFixed(2)} s; played once from ${start.toFixed(2)} s at speed ${speed} it ends at ${end.toFixed(2)} s, ` +
            `${(S.t1 - end).toFixed(2)} s before the shot does (${S.t1.toFixed(2)} s), and its last pose stands still: loop: true for a cycle, a lower speed, or hold: true to keep that pose`);
        }
        (N.plays[key] ||= []).push({ clip, at: start, speed, weight, loop });
      }
    }
    return N;
  }

  return {
    revision: THREE.REVISION,
    models: Object.values(M).map((m) => ({ key: m.key, src: m.src, clips: Object.fromEntries(Object.entries(m.clips).map(([n, c]) => [n, +c.duration.toFixed(4)])) })),
    // shots: [{ id, t0, t1 (its end, its transition out included), three (cues as seconds) }] → problems
    check(shots, problems) {
      for (const S of shots) NORM.set(S.three, normalize(S, problems));
      // the map itself only while a shot shows it sharp; else it goes now, from the GPU and the page
      const shown = new Set([bg0, ...shots.map((S) => NORM.get(S.three).background).filter((b) => b !== undefined)]);
      if (envMap && envMap !== env && !shown.has(envMap)) { envMap.dispose(); envMap = null; }
      // one render in ready on each background the shots show: the shaders compile now (an error in one is said while
      // loading), and what three makes on a first render (a skeleton's bone texture, a background's maps, each with a
      // random id) is made here, not in the first frame drawn
      aim(cam0);
      for (const b of shown) { scene.background = b; renderer.render(scene, camera); }
    },
    // the 3D of a shot at t into ctx at the frame's size (under ctx's transform); o.record: pose it, draw nothing (the
    // recorder's samples in ready)
    draw(ctx, t, s, three, o = {}) {
      const N = NORM.get(three);
      if (!N) fail(`shot ${s.id}: its three was not checked in ready`);
      restore();
      if (N.show) for (const m of Object.values(M)) m.root.visible = N.show.has(m.key);
      for (const m of Object.values(M)) {
        m.mixer.stopAllAction();   // every animated value back to what it was before the clips played
        if (!m.root.visible) continue;
        for (const p of N.plays[m.key] || []) {
          const a = m.mixer.clipAction(p.clip);
          a.reset();   // a fresh action: no loop count, finish or pause carried over from another frame
          a.setLoop(p.loop === "pingpong" ? THREE.LoopPingPong : p.loop ? THREE.LoopRepeat : THREE.LoopOnce, Infinity);
          a.clampWhenFinished = true; a.timeScale = p.speed; a.setEffectiveWeight(p.weight); a.startAt(p.at);
          a.play();
        }
        m.mixer.setTime(t);   // each clip at (t − at) × speed: before at, its first pose
      }
      aim(viewAt(t, s, N));
      if (N.pose) N.pose(t, s, W3);
      if (count() !== REST.length) fail(`shot ${s.id}: three.pose added or took away objects (${count()} now, ${REST.length} in ready): make them in FILM.three.build and show or hide them in pose`);
      const bg = N.background !== undefined ? N.background : bg0;
      scene.background = bg;
      if (!bg) renderer.setClearColor(0x000000, 0);
      if (o.record) return;
      renderer.render(scene, camera);
      ctx.drawImage(canvas, 0, 0, canvas.width / dpr, canvas.height / dpr);   // its pixels onto the 2D canvas's, one to one
    },
  };
}
