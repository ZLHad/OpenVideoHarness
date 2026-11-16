// 暗棚实物 3D · dark-studio-3d — swatch spec 2 (8 s, four beats, landscape).
//
// A dark studio and one heavy machined part: a steel spur gear on a shaft, a ball bearing and a hex nut above it, on a
// black plinth. Softboxes show only as long reflections on the metal; two rim lights cut the silhouette out of the dark.
// The lights come up, the assembly explodes along its shaft and comes back down piece by piece with its weight (the
// gear lands, the bearing seats, the nut spins down), and a spec card beside it says what it is made of and what it
// weighs, the mass worked out from the model's own volume. The whole assembly turns 60° in the 8 s, a sixth of a turn,
// which is a symmetry of every part, so the last frame is the first.
//
//   0.0–1.5  world      dark, rim-lit silhouette; the key softbox comes up from 0.1 s and the camera dollies in
//   1.5–4.5  signature  explode up the shaft (1.5–2.4), then drop back with weight: gear 2.95, bearing 3.22, nut 3.52;
//                       the spec card slides in with a leader to the gear's rim
//   4.5–7.0  type       title and caption in the dark at left; read once
//   7.0–8.0  close      card and title go, the key light goes down, the camera eases back: the first frame again
//
// Three.js r186 (engines/canvas-film/three, copied into the stage by render.sh) renders into an offscreen WebGL canvas;
// the 2D canvas composites it with the card, the type and a little grain. Every model is built here from primitives.
let THREE = null;   // three.js, loaded in setup (a static import would break foley.mjs, which reads FOLEY in Node)

const T = {
  lights: [0.1, 1.0], dolly: [0.0, 1.5], explode: [1.5, 2.4], drops: [2.75, 3.02, 3.3], land: 0.2,
  card: [3.7, 4.15], title: 4.5, caption: 4.75, read: [4.95, 7.0], out: [7.0, 7.2], dim: [7.05, 7.9], back: [7.0, 7.97],
};
const LANDS = T.drops.map((t) => t + T.land);            // gear 2.95, bearing 3.22, nut 3.50
const DENSITY = 7.85;                                     // g/cm³: 42CrMo4 (EN 10083-3) as every structural steel, to two places
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;

export const FOLEY = [
  { t: 0.5, sfx: "swoosh_tonal", gain_db: -14, dur: 1.0, dir: "up", tone: 0.6, bright: -0.3, pan: 0.1 },        // the light comes up
  { t: 1.95, sfx: "whoosh", gain_db: -14, dur: 0.8, dir: "up", tone: 0.3, pan: 0.15 },                          // the parts lift apart
  { t: LANDS[0], sfx: "impact", gain_db: -6, role: "hero", pitch: -3, pan: pan(1150) },                         // the gear lands
  { t: LANDS[1], sfx: "click", gain_db: -7, role: "hero", pitch: -5, pan: pan(1150) },                          // the bearing seats
  { t: LANDS[2] - 0.12, sfx: "tick", gain_db: -12, pitch: 4, pan: pan(1150) },                                  // the nut spinning down
  { t: LANDS[2], sfx: "click", gain_db: -6, role: "hero", pitch: 2, pan: pan(1150) },                           // and seated
  { t: T.card[0] + 0.2, sfx: "swoosh_tonal", gain_db: -15, dur: 0.45, dir: "down", tone: 0.5, pan: -0.5 },      // the card
  { t: 7.5, sfx: "air", gain_db: -12, dur: 0.8, dir: "down", tone: 0.4, pan: 0 },                               // the light goes down
];

export function texts(lib) {
  return [
    { text: lib.TITLE_ZH, start: T.read[0], end: T.read[1] },
    { text: lib.TITLE_EN, start: T.read[0], end: T.read[1] },
    { text: lib.CAPTION_ZH, start: T.read[0], end: T.read[1] },
  ];
}

// ── the parts (units: cm) ───────────────────────────────────────────────────────────────────────────────────────
const Z = 40, MOD = 0.4, RP = (Z * MOD) / 2, RO = RP + MOD, RR = RP - 1.25 * MOD, GEAR_T = 2.4, BORE = 1.5;
const HOLES = { n: 6, r: 1.45, at: 4.7 }, HUB = { r: 2.6, h: 0.8 };
const STACK = { gear: 0.3, bearing: 0.3 + GEAR_T + HUB.h, nut: 0.3 + GEAR_T + HUB.h + 1.6 };   // where each sits, assembled
const LIFT = { gear: 2.2, bearing: 6.2, nut: 10.0 };                                            // how far each rises, exploded

/** The gear's outline: 40 teeth with straight flanks narrowing to a short top land (cm, in the plane). */
function gearOutline() {
  const pts = [], d = Math.PI / 180, p = (2 * Math.PI) / Z;
  for (let k = 0; k < Z; k++) {
    const c = k * p;
    for (const [r, a] of [[RR, -3.4], [RR + 0.12, -3.0], [RP - 0.1, -2.15], [RP + 0.2, -1.8], [RO - 0.05, -1.35], [RO, -1.0],
      [RO, 1.0], [RO - 0.05, 1.35], [RP + 0.2, 1.8], [RP - 0.1, 2.15], [RR + 0.12, 3.0], [RR, 3.4], [RR, 4.5]]) {
      pts.push([r * Math.cos(c + a * d), r * Math.sin(c + a * d)]);
    }
  }
  return pts;
}
const shoelace = (pts) => Math.abs(pts.reduce((s, [x, y], i) => { const [u, v] = pts[(i + 1) % pts.length]; return s + x * v - u * y; }, 0)) / 2;
/** The gear's mass from its own geometry: the outline's area less the bore and the six holes, times the thickness,
 *  plus the hub, at the density of the steel (kg). This is the number on the card. */
const MASS = (() => {
  const face = shoelace(gearOutline()) - Math.PI * BORE * BORE - HOLES.n * Math.PI * HOLES.r * HOLES.r;
  const hub = Math.PI * (HUB.r * HUB.r - BORE * BORE) * HUB.h;
  return ((face * GEAR_T + hub) * DENSITY) / 1000;
})();

let R = null;   // the renderer, the scene and its parts (setup)

function studioEnvironment(renderer) {
  // a dark room with three softboxes: one big overhead, two tall strips behind left and right (they are what the metal shows)
  const env = new THREE.Scene();
  const room = new THREE.Mesh(new THREE.BoxGeometry(60, 30, 60), new THREE.MeshBasicMaterial({ color: 0x0b0b0d, side: THREE.BackSide }));
  env.add(room);
  // the studio floor, dim: what the vertical faces (the teeth's flanks) mirror, so they read as dark metal, not a hole
  const fl = new THREE.Mesh(new THREE.PlaneGeometry(60, 60), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.16, 0.16, 0.17) }));
  fl.rotation.x = -Math.PI / 2; fl.position.y = -6; env.add(fl);
  // a softbox is brightest in the middle and falls off to its edges: the falloff is what draws a gradient across a face
  const fall = (() => {
    const c = document.createElement("canvas"); c.width = 256; c.height = 128; const x = c.getContext("2d");
    const g = x.createRadialGradient(128, 64, 4, 128, 64, 150); g.addColorStop(0, "#ffffff"); g.addColorStop(0.55, "#8a8a8a"); g.addColorStop(1, "#141414");
    x.fillStyle = g; x.fillRect(0, 0, 256, 128); const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.NoColorSpace; return t;
  })();
  const box = (w, h, x, y, z, k, warm) => {
    const m = new THREE.MeshBasicMaterial({ map: fall, color: new THREE.Color(warm ? 1.0 : 0.92, warm ? 0.93 : 0.96, warm ? 0.85 : 1.0).multiplyScalar(k), side: THREE.DoubleSide });
    const q = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m); q.position.set(x, y, z); q.lookAt(0, 0, 0); env.add(q);
  };
  // the camera looks from the front left (azimuth −35°, 24° up), so the flat faces mirror the room behind right,
  // about as high: the key softbox goes there; the strips stand left and right of the line of sight for the rims
  box(24, 11, 19, 13, -25, 4.2, true);       // the key: a softbox behind right, mirrored in every flat face
  box(30, 8, -2, 24, -2, 2.4, true);         // overhead, for the top bevels
  box(5, 22, 23, 6, 16, 8, false);           // the right strip (the rim on the near right edges)
  box(5, 22, -22, 6, -17, 7, false);         // the left strip behind (the rim on the far left edges)
  box(36, 3, -6, -1, 26, 0.35, true);        // a faint bounce in front
  const pm = new THREE.PMREMGenerator(renderer);
  const tex = pm.fromScene(env, 0.035).texture;
  pm.dispose();
  return tex;
}

/** Concentric machining rings for the turned faces (a roughness map, grey = roughness). */
function turnedTexture(lib) {
  const n = 1024, c = document.createElement("canvas"); c.width = c.height = n;
  const x = c.getContext("2d"), img = x.createImageData(n, n);
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const r = Math.hypot(i - n / 2, j - n / 2) / (n / 2), k = (j * n + i) * 4;
    const ring = 0.5 + 0.5 * Math.sin(r * 640 + lib.hash(Math.floor(r * 90)) * 6);
    const v = 70 + 26 * ring + 18 * (lib.hash(Math.floor(r * 220), 7) - 0.5);
    img.data[k] = img.data[k + 1] = img.data[k + 2] = v; img.data[k + 3] = 255;
  }
  x.putImageData(img, 0, 0);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.NoColorSpace; t.anisotropy = 4;
  return t;
}

export async function setup(ctx, tokens, lib) {
  const { W, H } = lib;
  THREE = await import(new URL("../../three/build/three.module.js", import.meta.url).href);
  const canvas = document.createElement("canvas"); canvas.width = W; canvas.height = H;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(1); renderer.setSize(W, H, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  const scene = new THREE.Scene();
  const bg = new THREE.Color(tokens.palette.bg);
  scene.background = bg; scene.fog = new THREE.Fog(bg, 60, 120);
  const env = studioEnvironment(renderer);
  const turned = turnedTexture(lib);
  turned.wrapS = turned.wrapT = THREE.ClampToEdgeWrapping;

  const steel = new THREE.MeshPhysicalMaterial({ color: 0x8c9196, metalness: 1, roughness: 0.36, roughnessMap: turned, envMap: env, envMapIntensity: 1, clearcoat: 0 });
  const chrome = new THREE.MeshPhysicalMaterial({ color: 0xd9dde2, metalness: 1, roughness: 0.1, envMap: env, envMapIntensity: 1 });
  const oxide = new THREE.MeshPhysicalMaterial({ color: 0x2b2c30, metalness: 0.9, roughness: 0.42, envMap: env, envMapIntensity: 1 });
  const plinthMat = new THREE.MeshPhysicalMaterial({ color: 0x0e0f11, metalness: 0, roughness: 0.38, clearcoat: 0.6, clearcoatRoughness: 0.25, envMap: env, envMapIntensity: 1 });
  const floorMat = new THREE.MeshPhysicalMaterial({ color: 0x050506, metalness: 0, roughness: 0.6, envMap: env, envMapIntensity: 0.35 });
  const mats = [steel, chrome, oxide, plinthMat, floorMat];
  mats.forEach((m) => { m.userData.env = m.envMapIntensity; });

  const root = new THREE.Group(); scene.add(root);
  // the floor and the plinth
  const floor = new THREE.Mesh(new THREE.CircleGeometry(80, 96), floorMat); floor.rotation.x = -Math.PI / 2; floor.position.y = -1.6; floor.receiveShadow = true; scene.add(floor);
  const plinth = new THREE.Mesh(new THREE.LatheGeometry([[0, -1.6], [10.6, -1.6], [10.6, -0.12], [10.48, 0], [0, 0]].map(([x, y]) => new THREE.Vector2(x, y)), 96), plinthMat);
  plinth.receiveShadow = true; plinth.castShadow = true; root.add(plinth);
  // the shaft with its collar
  const shaft = new THREE.Mesh(new THREE.LatheGeometry([[0, 0], [2.3, 0], [2.3, 0.26], [2.2, 0.3], [BORE - 0.05, 0.3], [BORE - 0.05, 9.3], [BORE - 0.2, 9.45], [0, 9.45]].map(([x, y]) => new THREE.Vector2(x, y)), 64), oxide);
  shaft.castShadow = true; shaft.receiveShadow = true; root.add(shaft);
  // the gear: the outline extruded with a chamfer, six lightening holes, the bore; a turned hub on top
  const shape = new THREE.Shape(gearOutline().map(([x, y]) => new THREE.Vector2(x, y)));
  const hole = (cx, cy, r) => { const h = new THREE.Path(); h.absarc(cx, cy, r, 0, Math.PI * 2, true); return h; };
  shape.holes.push(hole(0, 0, BORE));
  for (let k = 0; k < HOLES.n; k++) { const a = (k / HOLES.n) * Math.PI * 2 + Math.PI / 6; shape.holes.push(hole(HOLES.at * Math.cos(a), HOLES.at * Math.sin(a), HOLES.r)); }
  const gg = new THREE.ExtrudeGeometry(shape, { depth: GEAR_T - 0.24, bevelEnabled: true, bevelThickness: 0.12, bevelSize: 0.09, bevelSegments: 2, curveSegments: 18 });
  gg.rotateX(-Math.PI / 2); gg.translate(0, 0.12, 0);
  // the caps' UVs are the shape's coordinates: map the turned rings onto the disc
  turned.repeat.set(1 / (2 * RO), 1 / (2 * RO)); turned.offset.set(0.5, 0.5);
  const gear = new THREE.Group();
  const gm = new THREE.Mesh(gg, steel); gm.castShadow = true; gm.receiveShadow = true; gear.add(gm);
  const hub = new THREE.Mesh(new THREE.LatheGeometry([[BORE, GEAR_T], [HUB.r, GEAR_T], [HUB.r, GEAR_T + HUB.h - 0.1], [HUB.r - 0.1, GEAR_T + HUB.h], [BORE + 0.1, GEAR_T + HUB.h], [BORE, GEAR_T + HUB.h - 0.1]].map(([x, y]) => new THREE.Vector2(x, y)), 72), steel);
  hub.castShadow = true; gear.add(hub);
  root.add(gear);
  // the bearing: outer and inner rings, ten balls between them
  const bearing = new THREE.Group();
  const ring = (r0, r1, h) => new THREE.LatheGeometry([[r0, 0.06], [r0 + 0.06, 0], [r1 - 0.06, 0], [r1, 0.06], [r1, h - 0.06], [r1 - 0.06, h], [r0 + 0.06, h], [r0, h - 0.06], [r0, 0.06]].map(([x, y]) => new THREE.Vector2(x, y)), 72);
  const outer = new THREE.Mesh(ring(2.75, 3.1, 1.6), chrome), inner = new THREE.Mesh(ring(BORE, 1.95, 1.6), chrome);
  outer.castShadow = inner.castShadow = true; bearing.add(outer, inner);
  const ballG = new THREE.SphereGeometry(0.4, 28, 18);
  for (let k = 0; k < 10; k++) { const a = (k / 10) * Math.PI * 2; const b = new THREE.Mesh(ballG, chrome); b.position.set(2.35 * Math.cos(a), 0.8, 2.35 * Math.sin(a)); b.castShadow = true; bearing.add(b); }
  root.add(bearing);
  // the hex nut (60° symmetric), chamfered
  const hex = new THREE.Shape(); for (let k = 0; k < 6; k++) { const a = (k / 6) * Math.PI * 2; hex[k ? "lineTo" : "moveTo"](2.65 * Math.cos(a), 2.65 * Math.sin(a)); }
  hex.holes.push(hole(0, 0, BORE));
  const ng = new THREE.ExtrudeGeometry(hex, { depth: 1.7, bevelEnabled: true, bevelThickness: 0.15, bevelSize: 0.14, bevelSegments: 2, curveSegments: 24 });
  ng.rotateX(-Math.PI / 2); ng.translate(0, 0.15, 0);
  const nut = new THREE.Mesh(ng, oxide); nut.castShadow = true; root.add(nut);

  // lights: the key from above left (it casts the shadows), two rims behind, a weak fill
  const key = new THREE.SpotLight(0xfff1e0, 700, 90, 0.3, 0.9, 1.6);
  key.position.set(-16, 30, 14); key.target.position.set(0, 2, 0); key.castShadow = true;
  key.shadow.mapSize.set(1024, 1024); key.shadow.bias = -0.0004; key.shadow.radius = 4; key.shadow.camera.near = 10; key.shadow.camera.far = 70;
  scene.add(key, key.target);
  const rimL = new THREE.DirectionalLight(0xdfe8ff, 2.4); rimL.position.set(-18, 9, -20);
  const rimR = new THREE.DirectionalLight(0xffffff, 3.2); rimR.position.set(20, 11, -16);
  const fill = new THREE.HemisphereLight(0x1a1c22, 0x050505, 0.4);
  scene.add(rimL, rimR, fill);

  const camera = new THREE.PerspectiveCamera(26, W / H, 1, 200);
  R = { renderer, scene, camera, root, gear, bearing, nut, key, rimL, rimR, mats, canvas };
  // warm the shaders up once, so the first measured frame is not the one that compiles them
  renderer.compile(scene, camera);
}

// ── time ──────────────────────────────────────────────────────────────────────────────────────────────────────────
/** How high a part is above its seat: lifted in the explode, then dropped (accelerating) and settling with a small bounce. */
function height(t, k, lift, lib) {
  const { seg, ease } = lib;
  const up = ease.inOutCubic(seg(t, T.explode[0] + k * 0.12, T.explode[1] - (2 - k) * 0.05)) * lift;
  if (t < T.drops[k]) return up;
  const u = seg(t, T.drops[k], LANDS[k]);
  if (u < 1) return lift * (1 - u * u);                   // falls under gravity: slow off the top, fastest at the seat
  const dt = t - LANDS[k];
  return 0.22 * Math.exp(-dt * 16) * Math.abs(Math.sin(dt * 34));   // a small bounce, quickly gone: it is heavy
}

function pose(t, lib) {
  const { seg, lerp, ease, W, H } = lib;
  const turn = (t / lib.DUR) * (Math.PI / 3);                                          // a sixth of a turn in the swatch
  R.root.rotation.y = -turn;
  R.gear.position.y = STACK.gear + height(t, 0, LIFT.gear, lib);
  R.bearing.position.y = STACK.bearing + height(t, 1, LIFT.bearing, lib);
  R.nut.position.y = STACK.nut + height(t, 2, LIFT.nut, lib);
  // the nut spins down the thread as it falls: a third of a turn, which a hexagon cannot tell from none, so there is no jump
  const un = seg(t, T.drops[2], LANDS[2]);
  R.nut.rotation.y = t >= T.drops[2] && un < 1 ? ((2 * Math.PI) / 3) * (1 - un) : 0;
  // the key light comes up, and in the close goes down to the rims alone
  const keyOn = ease.inOutSine(seg(t, ...T.lights)) * (1 - ease.inOutSine(seg(t, ...T.dim)));
  R.key.intensity = 60 + 840 * keyOn;
  const envK = 0.18 + 0.82 * keyOn;
  R.mats.forEach((m) => { m.envMapIntensity = m.userData.env * envK; });
  // the camera: dollies in from a little further and higher, rises to see the explode, settles; and back for the close
  const back = ease.inOutCubic(seg(t, ...T.back));
  const din = ease.outCubic(seg(t, ...T.dolly)) * (1 - back);
  const up = ease.inOutSine(seg(t, 1.4, 2.4)) * (1 - ease.inOutSine(seg(t, 3.1, 4.3)));
  const dist = lerp(64, 50, din) + 6 * up, elev = (lerp(30, 24, din) + 3 * up) * Math.PI / 180, az = -0.62;
  const target = new THREE.Vector3(0, 3.2 + 3.6 * up, 0);
  R.camera.position.set(target.x + dist * Math.cos(elev) * Math.sin(az), target.y + dist * Math.sin(elev), target.z + dist * Math.cos(elev) * Math.cos(az));
  R.camera.lookAt(target);
  // the gear's landing shakes the camera a little
  const dt = t - LANDS[0];
  if (dt > 0 && dt < 0.4) R.camera.position.y += 0.18 * Math.exp(-dt * 14) * Math.sin(dt * 60);
  // frame the product right of centre: shift the view
  R.camera.setViewOffset(W, H, -W * 0.13, 0, W, H);
  R.camera.updateMatrixWorld();
}

// ── frame ─────────────────────────────────────────────────────────────────────────────────────────────────────────
export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  pose(t, lib);
  R.renderer.render(R.scene, R.camera);
  ctx.drawImage(R.canvas, 0, 0, W, H);
  card(ctx, t, tokens, lib);
  type(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 24, seed: 3 });
  lib.vignette(ctx, { strength: 0.42, inner: 0.5, color: "#000000" });
}

/** The spec card at left, a leader to the gear's rim: what it is, what it is made of, what it weighs. */
function card(ctx, t, tokens, lib) {
  const a = lib.ease.outCubic(lib.seg(t, ...T.card)) * (1 - lib.seg(t, ...T.out));
  if (a <= 0) return;
  const P = (k) => lib.color(tokens, k), { W, H } = lib;
  // where the rim is on screen: a point on the gear's outer radius, front left, projected
  const v = new THREE.Vector3(-RO * 0.95, STACK.gear + GEAR_T * 0.5, RO * 0.3).applyMatrix4(R.root.matrixWorld).project(R.camera);
  const rx = (v.x * 0.5 + 0.5) * W, ry = (-v.y * 0.5 + 0.5) * H;
  const x0 = 110 - (1 - a) * 60, y0 = 560, w = 590, h = 300;
  ctx.save(); ctx.globalAlpha = a;
  // the leader: from the card's right edge to the rim, with a dot on the metal
  const lu = lib.ease.inOutSine(lib.seg(t, T.card[0] + 0.15, T.card[1] + 0.1));
  ctx.strokeStyle = lib.rgba(P("hair"), 0.8); ctx.lineWidth = 1.5;
  const sx = x0 + w, sy = y0 + 56;
  ctx.beginPath(); ctx.moveTo(sx, sy); ctx.lineTo(sx + (rx - sx) * lu, sy + (ry - sy) * lu); ctx.stroke();
  if (lu > 0.98) { ctx.fillStyle = P("text"); ctx.beginPath(); ctx.arc(rx, ry, 5, 0, Math.PI * 2); ctx.fill(); ctx.strokeStyle = lib.rgba(P("text"), 0.5); ctx.beginPath(); ctx.arc(rx, ry, 12, 0, Math.PI * 2); ctx.stroke(); }
  // the card: smoked glass, a hairline, one accent tick
  ctx.fillStyle = lib.rgba(P("card"), 0.78); ctx.fillRect(x0, y0, w, h);
  ctx.strokeStyle = lib.rgba(P("hair"), 0.55); ctx.lineWidth = 1.2; ctx.strokeRect(x0 + 0.5, y0 + 0.5, w - 1, h - 1);
  ctx.fillStyle = P("accent"); ctx.fillRect(x0, y0, 6, h);
  ctx.textBaseline = "alphabetic"; ctx.textAlign = "left";
  lib.setFont(ctx, tokens, "mono", 26); ctx.fillStyle = P("muted");
  ctx.fillText("PART 03 · SPUR GEAR · Z40 M4", x0 + 40, y0 + 62);
  lib.setFont(ctx, tokens, "zh", 46); ctx.fillStyle = P("text");
  ctx.fillText("直齿轮 · 40 齿 · 模数 4", x0 + 40, y0 + 132);
  ctx.fillText("42CrMo4 合金钢", x0 + 40, y0 + 198);
  lib.setFont(ctx, tokens, "num", 40, { weight: 500 }); ctx.fillStyle = P("text");
  ctx.fillText(`${DENSITY.toFixed(2)} g/cm³  ·  ${MASS.toFixed(1)} kg`, x0 + 40, y0 + 262);
  ctx.restore();
}

/** Title at upper left in the dark; the caption low. */
function type(ctx, t, tokens, lib) {
  if (t < T.title) return;
  const out = 1 - lib.seg(t, ...T.out);
  if (out <= 0) return;
  const P = (k) => lib.color(tokens, k), { W, SAFE, TYPE } = lib;
  const x0 = 150, y = 300;
  ctx.save();
  lib.setFont(ctx, tokens, "zh", TYPE.title, { weight: 600 }); ctx.fillStyle = P("text"); ctx.textBaseline = "alphabetic";
  const lay = lib.layoutText(ctx, lib.TITLE_ZH, { x: x0, y, align: "left", tracking: lib.tracking(tokens, "zh", TYPE.title) });
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const t0 = T.title + i * 0.03; if (t < t0) return null;
    const p = lib.ease.outCubic(lib.seg(t, t0, t0 + 0.35));
    return { alpha: out * p, dx: (1 - p) * -14 };
  });
  lib.setFont(ctx, tokens, "en", TYPE.label, { weight: 300 }); ctx.fillStyle = P("muted");
  ctx.globalAlpha = out * lib.clamp((t - T.title - 0.25) / 0.25);
  ctx.fillText(lib.TITLE_EN, x0 + 2, y + TYPE.label * 1.55);
  ctx.globalAlpha = out * lib.clamp((t - T.caption) / 0.15);
  lib.setFont(ctx, tokens, "zh", TYPE.caption, { weight: 500 }); ctx.fillStyle = P("text"); ctx.textBaseline = "middle";
  lib.drawText(ctx, lib.CAPTION_ZH, W / 2, SAFE.title.y1 - TYPE.caption * 0.55, { align: "center", tracking: TYPE.caption * 0.06 });
  ctx.restore();
}
