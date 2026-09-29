// silhouette-papercut swatch · 剪影剪纸
// Five paper layers in front of an indigo night backdrop: far hills · middle hills · the near ground (a slightly
// lighter paper) with a walker and three cut-paper houses standing on it · a lace foreground frame. Each layer casts a soft paper shadow.
// Characters, letters and layer wobble step at 12 fps (on a 30 fps timeline); the parallax pan moves on every frame.
//   0.00–0.83  HOOK: a full-height foreground lace hedge slides right→left across the frame (29 % of it at 0.1 s);
//              behind it the paper layers pop up from below on 12 fps steps (ground first), lace branches drop in
//   0.10–5.00  SIGNATURE: night register — indigo papers, cream paper houses, a 310 px RED paper walker who steps in
//              at 0.1 s and keeps walking the whole film (15 fps, one step per eighth note), contact shadow + paper shadow
//   0.85–2.50  title: cut-out letters pop in one per 12 fps step (1.15 for one step, then 1)
//   2.00–2.70  motif: three houses rise from the ground on steps: hollow outline → three windows → full lace with the
//              only red object (a paper lantern)
//   4.00–4.42  SIGNATURE TRANSITION: a silent-film iris closes on the red lantern; the end card is fully out by 4.58

export const fonts = ["Didot"];
const LAT = { fonts: { en: { family: ["Didot", "Bodoni 72"], weight: 400 }, it: { family: ["Didot", "Bodoni 72"], weight: 400, style: "italic" } } };
const TAU = Math.PI * 2;
const N = { sky0: "#3E5F92", sky1: "#17223F", far: "#2C3F6D", mid: "#1D2B50", ground: "#121A33", lace: "#0B1126", red: "#C8232A", cream: "#EFE3C6", gold: "#F2C14E" };
let L = null;

function canvas(w, h) { const c = document.createElement("canvas"); c.width = w; c.height = h; return [c, c.getContext("2d")]; }
function wobbly(ctx, pts, lib, seed, amp = 1.2) {            // hand-cut edge: resample and nudge along the normal
  ctx.beginPath(); let k = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x0, y0] = pts[i], [x1, y1] = pts[(i + 1) % pts.length], n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / 14));
    for (let s = 0; s < n; s++) { const u = s / n; const x = x0 + (x1 - x0) * u + amp * lib.hashS(seed, k, 1), y = y0 + (y1 - y0) * u + amp * lib.hashS(seed, k, 2); k++ ? ctx.lineTo(x, y) : ctx.moveTo(x, y); }
  }
  ctx.closePath();
}
function hills(lib, col, base, amp, freq, seed, trees) {
  const [c, x] = canvas(2200, 1080); x.fillStyle = col;
  const pts = [[0, 1080]];
  for (let px = 0; px <= 2200; px += 20) pts.push([px, base - amp * (0.6 * Math.sin(px * freq + seed) + 0.4 * Math.sin(px * freq * 2.3 + seed * 2)) - 10 * lib.noise1(px / 90, seed)]);
  pts.push([2200, 1080]);
  wobbly(x, pts, lib, seed, 0.8); x.fill();
  const r = lib.rng(seed + 3);
  for (const [tx, h, kind] of trees) {
    const ty = base - amp * (0.6 * Math.sin(tx * freq + seed) + 0.4 * Math.sin(tx * freq * 2.3 + seed * 2)) - 10 * lib.noise1(tx / 90, seed) + 4;
    x.fillRect(tx - 3, ty - h * 0.45, 6, h * 0.45 + 6);
    if (kind === "round") { x.beginPath(); x.ellipse(tx, ty - h * 0.62, h * 0.3, h * 0.36, 0, 0, TAU); x.fill(); }
    else { x.beginPath(); x.moveTo(tx, ty - h); x.lineTo(tx + h * 0.2, ty - h * 0.3); x.lineTo(tx - h * 0.2, ty - h * 0.3); x.closePath(); x.fill(); }
    x.save(); x.globalCompositeOperation = "destination-out";                  // lace: little leaf holes in each crown
    for (let k = 0; k < 7; k++) { x.beginPath(); x.ellipse(tx + (r() - 0.5) * h * 0.3, ty - h * (0.45 + r() * 0.35), 2.5 + r() * 2, 5 + r() * 3, r() * 3, 0, TAU); x.fill(); }
    x.restore();
  }
  return c;
}
function ground(lib, col) {                                     // near ground band with a sawtooth grass edge
  const [c, x] = canvas(2200, 260); x.fillStyle = col;
  const pts = [[0, 260]];
  for (let px = 0; px <= 2200; px += 12) pts.push([px, 30 - (px / 12 % 2 ? 22 * (0.5 + 0.5 * lib.hash(4, px)) : 0) + 6 * Math.sin(px / 140)]);
  pts.push([2200, 260]); wobbly(x, pts, lib, 12, 0.6); x.fill();
  return c;
}
function branch(lib, col, flip, seed) {                         // lace foreground frame: a hanging branch with cut leaves
  const [c, x] = canvas(520, 440); x.fillStyle = col; x.strokeStyle = col; x.lineCap = "round";
  if (flip) { x.translate(520, 0); x.scale(-1, 1); }
  const r = lib.rng(seed);
  const spine = (u) => [u * 420, 20 + 260 * u * u + 40 * Math.sin(u * 5)];
  x.lineWidth = 14; x.beginPath(); for (let i = 0; i <= 40; i++) { const [a, b] = spine(i / 40); i ? x.lineTo(a, b) : x.moveTo(a, b); } x.stroke();
  for (let k = 0; k < 16; k++) {
    const u = 0.1 + k / 18, [a, b] = spine(u), side = k % 2 ? 1 : -1, ang = 1.1 * side + (r() - 0.5) * 0.5, len = 34 + r() * 26;
    x.lineWidth = 5 * (1 - u) + 2; x.beginPath(); x.moveTo(a, b); const lx = a + Math.cos(ang) * len * 0.6, ly = b + Math.sin(ang) * len * 0.6 + 16; x.lineTo(lx, ly); x.stroke();
    x.save(); x.translate(lx, ly); x.rotate(ang + Math.PI / 2 * side * 0.2); x.beginPath(); x.ellipse(0, 12, 12, 26, 0, 0, TAU); x.fill();
    x.globalCompositeOperation = "destination-out"; x.lineWidth = 2.2; x.beginPath(); x.moveTo(0, -6); x.lineTo(0, 30); x.stroke();   // cut vein
    for (let v = 0; v < 3; v++) { x.beginPath(); x.moveTo(0, 2 + v * 9); x.lineTo(6, -2 + v * 9); x.moveTo(0, 2 + v * 9); x.lineTo(-6, -2 + v * 9); x.stroke(); }
    x.restore();
  }
  return c;
}
// houses: 0 hollow outline · 1 solid with three windows · 2 full lace with door, lattice, sawtooth eaves and a red lantern
function house(lib, k, col, red) {
  const [c, x] = canvas(320, 300); x.translate(160, 290); x.fillStyle = col;
  const shape = [[-120, 0], [-120, -130], [-150, -130], [0, -240], [150, -130], [120, -130], [120, 0]];
  wobbly(x, shape, lib, 30 + k, 0.9); x.fill();
  x.save(); x.globalCompositeOperation = "destination-out";
  if (k === 0) { wobbly(x, [[-106, -12], [-106, -142], [-116, -142], [0, -224], [116, -142], [106, -142], [106, -12]], lib, 40, 0.9); x.fill(); }
  else if (k === 1) { for (let i = 0; i < 3; i++) { wobbly(x, [[-96 + i * 68, -110], [-50 + i * 68, -110], [-50 + i * 68, -46], [-96 + i * 68, -46]], lib, 50 + i, 0.7); x.fill(); } }
  else {
    wobbly(x, [[-24, 0], [-24, -84], [24, -84], [24, 0]], lib, 60, 0.6); x.fill();                                     // door
    for (const wx of [-86, 50]) for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) x.fillRect(wx + i * 13, -112 + j * 13, 9, 9);   // lattice windows
    for (let i = -7; i <= 7; i++) { x.beginPath(); x.moveTo(i * 18 - 7, -128); x.lineTo(i * 18 + 7, -128); x.lineTo(i * 18, -116); x.closePath(); x.fill(); }   // sawtooth eave
    x.beginPath(); x.arc(0, -170, 18, 0, TAU); x.fill();                                                                  // round gable window
    x.fillStyle = "#000"; for (let a = 0; a < 6; a++) { x.beginPath(); x.ellipse(Math.cos(a) * 30, -170 + Math.sin(a) * 30, 4, 8, a, 0, TAU); x.fill(); }
  }
  x.restore();
  if (k === 2) {                                                                                                          // the one red object
    x.strokeStyle = col; x.lineWidth = 3; x.beginPath(); x.moveTo(52, -130); x.lineTo(52, -104); x.stroke();
    x.fillStyle = red; x.beginPath(); x.ellipse(52, -82, 17, 22, 0, 0, TAU); x.fill();
    x.fillStyle = col; x.fillRect(42, -106, 20, 5); x.fillRect(42, -62, 20, 5);
    x.save(); x.globalCompositeOperation = "destination-out"; x.lineWidth = 1.6; x.beginPath(); x.moveTo(52, -100); x.lineTo(52, -64); x.moveTo(44, -96); x.quadraticCurveTo(40, -82, 44, -68); x.moveTo(60, -96); x.quadraticCurveTo(64, -82, 60, -68); x.stroke(); x.restore();
  }
  return c;
}
function hedgeSprite(lib) {                                         // dense cut-paper hedge: scalloped sides, 锯齿 leaf tips, crescent rows, a rosette
  const [c, x] = canvas(1300, 1140), pts = [];
  for (let y = 1140; y >= 120; y -= 20) pts.push([60 + 36 * Math.sin(y / 52) + 20 * lib.noise1(y / 90, 3), y]);
  for (let k = 0; k <= 15; k++) { const px = 80 + k * 76; pts.push([px - 34, 120 + 24 * lib.hash(5, k)], [px, 20 + 90 * lib.hash(6, k)]); }
  for (let y = 120; y <= 1140; y += 20) pts.push([1240 - 36 * Math.sin(y / 47 + 1) - 20 * lib.noise1(y / 90, 4), y]);
  x.fillStyle = N.lace; wobbly(x, pts, lib, 81, 1.0); x.fill();
  x.globalCompositeOperation = "destination-out";
  for (let r = 0; r < 12; r++) for (let q = 0; q < 11; q++) {                // 月牙纹: rows of crescents, offset every other row, punched dots between
    const cx = 150 + q * 100 + (r % 2) * 50, cy = 200 + r * 80; if (Math.hypot(cx - 650, cy - 600) < 200 || cx > 1180) continue;
    x.beginPath(); x.arc(cx, cy, 24, 0.1 * Math.PI, 0.9 * Math.PI); x.arc(cx, cy - 12, 20, 0.85 * Math.PI, 0.15 * Math.PI, true); x.closePath(); x.fill();
    x.beginPath(); x.arc(cx + 50, cy - 40, 5, 0, TAU); x.fill();
  }
  for (let i = 0; i < 8; i++) { const a = i / 8 * TAU; x.beginPath(); x.ellipse(650 + 95 * Math.cos(a), 600 + 95 * Math.sin(a), 64, 24, a, 0, TAU); x.fill(); }   // 团花
  x.beginPath(); x.arc(650, 600, 26, 0, TAU); x.fill();
  return c;
}
function moonSprite(lib) {
  const [c, x] = canvas(260, 260); x.fillStyle = N.cream; wobbly(x, Array.from({ length: 40 }, (_, i) => [130 + 118 * Math.cos(i / 40 * TAU), 130 + 118 * Math.sin(i / 40 * TAU)]), lib, 71, 0.8); x.fill();
  x.globalCompositeOperation = "destination-out"; x.lineCap = "round"; x.lineWidth = 7;
  for (let i = 0; i < 18; i++) { const a = i / 18 * TAU; x.beginPath(); x.arc(130 + 98 * Math.cos(a), 130 + 98 * Math.sin(a), 5, 0, TAU); x.fill(); }   // a ring of punched holes
  for (let i = 0; i < 8; i++) {                                                // an eight-petal cut rosette in the middle
    const a = i / 8 * TAU; x.beginPath(); x.ellipse(130 + 34 * Math.cos(a), 130 + 34 * Math.sin(a), 17, 7, a, 0, TAU); x.fill();
  }
  return c;
}
function withShadow(lib, src, dx = 6, dy = 6, blur = 6) {       // bake the paper shadow into the sprite
  const [c, x] = canvas(src.width + 40, src.height + 40);
  x.shadowColor = "rgba(3,5,14,0.55)"; x.shadowOffsetX = dx; x.shadowOffsetY = dy; x.shadowBlur = blur; x.drawImage(src, 14, 14);
  return c;
}

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
  L = {
    P,
    far: withShadow(lib, hills(lib, N.far, 700, 60, 0.004, 1, [[300, 90, "cone"], [760, 70, "round"], [1500, 100, "cone"], [1880, 80, "round"]]), 4, 4, 5),
    mid: withShadow(lib, hills(lib, N.mid, 790, 34, 0.0032, 4, [[160, 150, "cone"], [1260, 120, "round"], [1760, 170, "cone"]])),
    ground: withShadow(lib, ground(lib, N.ground), 0, -4, 8),
    br: [withShadow(lib, branch(lib, N.lace, false, 5)), withShadow(lib, branch(lib, N.lace, true, 9))],
    houses: [0, 1, 2].map((k) => withShadow(lib, house(lib, k, N.cream, N.red))),
    moon: moonSprite(lib), hedge: withShadow(lib, hedgeSprite(lib), 10, 8, 8),
    hx: [756, 1146, 1536], HS: 1.25, groundY: 872,   // world x; the near layer pans 22 px/s, so at 3.0 s they sit at 690 / 1080 / 1470
  };
}

// the walker: feet on the near path, 12 fps walk cycle, stops at 1.9 s and stands (stepped weight shift)
function walkerPose(t, lib) {
  // 3 drawings per step, so the eighth-note footfalls in events.json ("step") set the rate: 0.2 s → 15 fps, a 6-drawing
  // cycle of 0.4 s; drawing 1 and 4 are the contact poses and land exactly on the footfalls
  const dt = S.step[1] - S.step[0], fps = 3 / dt, tp = lib.step(t, fps), i = ((Math.round((tp - S.step[0]) * fps) + 1) % 6 + 6) % 6;
  return { x: -80 + 309 * Math.max(0, tp - T.pop), walking: true, ph: i / 6 * TAU, idle: 0, tp };
}
function drawWalker(ctx, lib, p, col) {                          // local units: feet at 0, about 150 tall; drawn at S = 2.1
  const S = 2.1, ph = p.ph, sw = p.walking ? Math.sin(ph) : 0;
  const bob = p.walking ? -Math.abs(Math.sin(ph)) * 2.2 : p.idle * 0.6;
  ctx.save(); ctx.scale(S, S); ctx.translate(0, bob); ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineCap = "round"; ctx.lineJoin = "round";
  const leg = (a, w) => { const kx = Math.sin(a) * 22, fx = Math.sin(a) * 30; ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(0, -72); ctx.lineTo(kx + 3, -38); ctx.lineTo(fx, -4); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(fx - 4, -6); ctx.lineTo(fx + 13, -4); ctx.lineTo(fx + 13, 0); ctx.lineTo(fx - 6, 0); ctx.closePath(); ctx.fill(); };   // boot
  if (p.walking) { leg(0.5 * sw, 9); leg(-0.5 * sw, 9); } else { leg(0.16, 9); leg(-0.12, 9); }
  ctx.beginPath(); ctx.moveTo(-16, -68); ctx.lineTo(16, -66); ctx.lineTo(19, -40); ctx.lineTo(4, -44); ctx.lineTo(-18, -38); ctx.lineTo(-14, -70);                  // coat skirt
  ctx.moveTo(-14, -70); ctx.lineTo(14, -70); ctx.lineTo(11, -118); ctx.lineTo(-12, -118); ctx.closePath(); ctx.fill();                                             // coat
  ctx.beginPath(); ctx.arc(2, -129, 11, 0, TAU); ctx.fill();                                                                                                        // head
  ctx.beginPath(); ctx.moveTo(10, -130); ctx.lineTo(16, -126); ctx.lineTo(10, -123); ctx.fill();                                                                     // nose
  ctx.beginPath(); ctx.moveTo(-28, -134); ctx.quadraticCurveTo(2, -160, 32, -134); ctx.lineTo(34, -131); ctx.lineTo(-30, -131); ctx.closePath(); ctx.fill();       // wide hat
  ctx.save(); ctx.globalCompositeOperation = "destination-out"; ctx.beginPath(); ctx.ellipse(-2, -137, 9, 2.2, 0, 0, TAU); ctx.fill(); ctx.restore();              // a cut in the hat band
  const hx = p.walking ? 22 + 7 * sw : 24, hy = p.walking ? -82 : -84;
  ctx.lineWidth = 7; ctx.beginPath(); ctx.moveTo(6, -110); ctx.lineTo(14, -96); ctx.lineTo(hx, hy); ctx.stroke();                                                   // arm
  ctx.lineWidth = 3.4; ctx.beginPath(); ctx.moveTo(hx, hy - 6); ctx.lineTo(hx + 12 + (p.walking ? 6 * sw : 0), 0); ctx.stroke();                                  // walking stick
  ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(-6, -110); ctx.lineTo(-14, -90 - 6 * sw); ctx.lineTo(-10 - 8 * sw, -74); ctx.stroke();                            // far arm
  ctx.restore();
}
function walker(ctx, lib, t, nx, up = 0) {
  if (t < T.pop) return;
  const p = walkerPose(t, lib), x = p.x + nx, y = L.groundY + 20 + up;                 // rides up with the ground layer
  // contact shadow on the path: a soft dark patch under the feet (paper resting on paper)
  ctx.save(); ctx.filter = "blur(3px)"; ctx.fillStyle = "rgba(2,3,10,0.75)"; ctx.beginPath(); ctx.ellipse(x + 8, y + 2, 74, 8, 0, 0, TAU); ctx.fill(); ctx.restore();
  const w = lib.offscreen("spc_walker", (c) => { c.translate(x, y); drawWalker(c, lib, p, N.red); });
  ctx.save(); ctx.shadowColor = "rgba(3,5,14,0.6)"; ctx.shadowOffsetX = 6; ctx.shadowOffsetY = 5; ctx.shadowBlur = 6; ctx.drawImage(w, 0, 0); ctx.restore();
}

function backdrop(ctx, lib, t) {
  const P = L.P, g = ctx.createRadialGradient(960, 560, 60, 960, 560, 1150);
  g.addColorStop(0, N.sky0); g.addColorStop(0.5, "#27396A"); g.addColorStop(1, N.sky1);
  ctx.fillStyle = g; ctx.fillRect(0, 0, lib.W, lib.H);
  lib.paper(ctx, { tone: "#2A3B66", amount: 0.3, blotch: 0.06, tooth: 0.03, fiber: 0.5, seed: 2 });
}
function layer(ctx, lib, img, x, y, t, seed, rotAmp = 0.003) {  // stepped wobble: each paper layer trembles a little, 12 fps
  const tp = lib.step(t, 12), r = rotAmp * Math.sin(tp * 5.3 + seed) , j = lib.hashS(seed, Math.round(tp * 12));
  ctx.save(); ctx.translate(x + img.width / 2, y + img.height); ctx.rotate(r); ctx.drawImage(img, -img.width / 2, -img.height + j * 0.8); ctx.restore();
}

function moon(ctx, lib, t, dn) {                                  // a cream paper moon let down on a thread, behind the right-hand lace branch
  const x = 1660 - t * 22 * 0.2, y = 196 - dn, r = 118;
  ctx.save(); ctx.strokeStyle = "rgba(239,227,198,0.55)"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, y - r); ctx.stroke();
  ctx.shadowColor = "rgba(3,5,14,0.55)"; ctx.shadowOffsetX = 6; ctx.shadowOffsetY = 6; ctx.shadowBlur = 8;
  ctx.drawImage(L.moon, Math.round(x - L.moon.width / 2), Math.round(y - L.moon.height / 2)); ctx.restore();
}
function scene(ctx, t, tokens, lib) {
  // the hook: at 0.1 s the paper layers pop up from below the frame like a pop-up book, one 12 fps step at a time,
  // nearest first (ground 3 steps, hills 4–5 steps, one-step overshoot); the lace branches drop from the top
  const pop = (dist, seq) => { if (t < T.pop) return dist; const k = Math.floor((t - T.pop) * 12 + 1e-6); return k < seq.length ? dist * seq[k] : 0; };
  const P = L.P, pan = t * 22;
  const gUp = pop(420, [0.12, -0.03]), mUp = pop(520, [0.4, 0.14, 0.02, -0.02]), fUp = pop(560, [0.5, 0.28, 0.12, 0.03, -0.01]), bDn = pop(320, [0.35, 0.1, -0.05]);
  backdrop(ctx, lib, t);
  moon(ctx, lib, t, pop(560, [0.45, 0.15, -0.04]));
  layer(ctx, lib, L.far, -140 - pan * 0.35, fUp - 14, t, 1);
  layer(ctx, lib, L.mid, -140 - pan * 0.6, mUp - 14, t, 2);
  // near: the ground band and the three houses standing on it
  const nx = -pan;
  L.houses.forEach((h, k) => {
    const t0 = T["house" + k]; if (t < t0) return;   // rises on its scissors snip
    const st = Math.floor((lib.step(t, 12) - lib.step(t0, 12)) * 12 + 1e-6), sy = st >= 4 ? (st === 4 ? 1.12 : 1) : (st + 1) / 4;   // rises in 4 steps, one-step pop
    ctx.save(); ctx.translate(L.hx[k] + nx, L.groundY + 10); ctx.scale(L.HS * (sy > 1 ? 1.06 : 1), L.HS * sy);
    if (k === 2) {                                                                   // the finished house is lit: its cut door and windows show lamplight
      const flick = 0.9 + 0.1 * Math.sin(lib.step(t, 12) * 17);
      const g = ctx.createRadialGradient(20, -90, 10, 20, -90, 170); g.addColorStop(0, N.gold); g.addColorStop(1, "#B8782A");
      ctx.globalAlpha = flick; ctx.fillStyle = g; ctx.beginPath(); [[-112, -14], [-112, -138], [-136, -138], [0, -240], [136, -138], [112, -138], [112, -14]].forEach(([x, y], i) => (i ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath(); ctx.fill(); ctx.globalAlpha = 1;
    }
    ctx.drawImage(h, -h.width / 2 + 6, -h.height + 22); ctx.restore();
  });
  layer(ctx, lib, L.ground, -140 + nx, L.groundY - 36 + gUp, t, 3, 0.0015);
  walker(ctx, lib, t, nx, gUp);
  // labels: cut out of the black ground, so the backdrop colour shows through
  L.houses.forEach((h, k) => {
    const t0 = T["house" + k] + 0.1; if (t < t0) return;
    ctx.save(); ctx.fillStyle = N.cream; ctx.textAlign = "center"; ctx.globalAlpha = lib.clamp((lib.step(t, 12) - t0) * 12 / 2 + 0.5);
    lib.setFont(ctx, tokens, "zh", 50, { weight: 700 }); ctx.fillText(lib.MOTIF[k].zh, L.hx[k] + nx, 956);
    lib.setFont(ctx, LAT, "it", 38); ctx.fillText(lib.MOTIF[k].en, L.hx[k] + nx, 1006);
    ctx.restore();
  });
  // lace foreground frame, top corners
  layer(ctx, lib, L.br[0], -30 - pan * 1.4, -40 - bDn, t, 4, 0.02);
  layer(ctx, lib, L.br[1], lib.W - 520 + 30 - pan * 1.4, -40 - bDn, t, 5, 0.02);
  title(ctx, t, tokens, lib);
  // the hook: a full-height foreground lace hedge slides right→left across the frame like a camera passing a bush
  // (parallax 1.4, 3500 px/s): a quarter of the frame at 0.1 s, its centre crossing the frame centre on "hedgeMid"
  const hx0 = 310 - 3500 * (t - T.hedgeMid);
  if (hx0 < lib.W && hx0 + L.hedge.width > 0) ctx.drawImage(L.hedge, Math.round(hx0), -30);
}

function title(ctx, t, tokens, lib) {
  const P = L.P, tp = lib.step(t, 12), pop = (t0) => { if (tp < t0 - 1e-6) return null; const k = Math.round((tp - t0) * 12); return { scale: k === 0 ? 1.15 : 1 }; };
  ctx.save(); ctx.shadowColor = "rgba(3,5,14,0.6)"; ctx.shadowOffsetX = 4; ctx.shadowOffsetY = 4; ctx.shadowBlur = 5;
  lib.setFont(ctx, LAT, "en", 112); ctx.fillStyle = N.cream;
  const en = lib.layoutText(ctx, lib.TITLE_EN, { x: lib.W / 2, y: 290, align: "center", tracking: -0.01 * 112 });
  lib.drawGlyphs(ctx, en, (g, i) => pop(Math.round((0.8 + i / 12) * 12) / 12));
  lib.setFont(ctx, tokens, "zh", 74, { weight: 700 }); ctx.fillStyle = N.cream;
  const zh = lib.layoutText(ctx, lib.TITLE_ZH, { x: lib.W / 2, y: 402, align: "center", tracking: 0.14 * 74 });
  lib.drawGlyphs(ctx, zh, (g, i) => pop(Math.round((1.4 + i * 2 / 12) * 12) / 12));
  ctx.restore();
}

function endCard(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.fillStyle = "#0B1022"; ctx.fillRect(0, 0, lib.W, lib.H);
  const tp = lib.step(t, 12); if (tp < 4.41) return;
  ctx.fillStyle = N.cream; ctx.textAlign = "center";
  lib.setFont(ctx, tokens, "zh", 96, { weight: 700 });
  const zh = lib.layoutText(ctx, "剪影 · 剪纸", { x: lib.W / 2, y: 560, align: "center", tracking: 12 });
  const t0 = (i) => (i < 4 ? 53 : 54) / 12;                                     // two steps: 剪影 · | 剪纸 (4.42, 4.50)
  lib.drawGlyphs(ctx, zh, (g, i) => (tp >= t0(i) - 1e-6 ? { scale: Math.round((tp - t0(i)) * 12) === 0 ? 1.15 : 1 } : null));
  if (tp >= 55 / 12 - 1e-6) { lib.setFont(ctx, LAT, "it", 48); ctx.fillText("silhouette-papercut", lib.W / 2, 656); }
}

export function renderAt(t, ctx, tokens, lib) {
  if (t < 4.0) { scene(ctx, t, tokens, lib); return; }
  // silent-film iris on the lantern: close to a small circle, hold a beat, shut; then the end card
  const pan = t * 22, cx = L.hx[2] - pan + 52 * L.HS, cy = L.groundY + 10 - 96 * L.HS;   // lantern centre (sprite offset + baked shadow margin) × house scale
  const u = lib.seg(t, 4.0, 4.3), r = t < 4.3 ? lib.lerp(1600, 96, lib.ease.inOutCubic(u)) : t < T.irisShut - 0.06 ? 96 : Math.max(0, 96 * (1 - lib.seg(t, T.irisShut - 0.06, T.irisShut)));   // shuts on the shutter sound
  endCard(ctx, t, tokens, lib);
  if (r <= 0.5) return;
  const A = lib.offscreen("sp_A", (x) => scene(x, t, tokens, lib));
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.clip(); ctx.drawImage(A, 0, 0); ctx.restore();
}
