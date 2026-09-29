// silhouette-papercut swatch · 剪影剪纸
// Five paper layers in front of one amber-tinted backdrop: far hills · middle hills with a path · a walker ·
// the near ground with three cut-paper houses · a lace foreground frame. Each layer casts a soft paper shadow.
// Characters, letters and layer wobble step at 12 fps (on a 30 fps timeline); the parallax pan moves on every frame.
//   0.00–0.80  backdrop warms up, layers slide into place on steps
//   0.30–4.00  SIGNATURE: parallax pan + a stepped walker crossing the middle path, disappearing behind the houses
//   0.85–2.50  title: cut-out letters pop in one per 12 fps step (1.15 for one step, then 1)
//   2.00–2.70  motif: three houses rise from the ground on steps: hollow outline → three windows → full lace with the
//              only red object (a paper lantern)
//   4.00–4.80  SIGNATURE TRANSITION: a silent-film iris closes on the red lantern, then the end card

export const fonts = ["Didot"];
const LAT = { fonts: { en: { family: ["Didot", "Bodoni 72"], weight: 400 }, it: { family: ["Didot", "Bodoni 72"], weight: 400, style: "italic" } } };
const TAU = Math.PI * 2;
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
function withShadow(lib, src, dx = 6, dy = 6, blur = 6) {       // bake the paper shadow into the sprite
  const [c, x] = canvas(src.width + 40, src.height + 40);
  x.shadowColor = "rgba(20,10,5,0.38)"; x.shadowOffsetX = dx; x.shadowOffsetY = dy; x.shadowBlur = blur; x.drawImage(src, 14, 14);
  return c;
}

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  L = {
    P,
    far: withShadow(lib, hills(lib, P("extra.1"), 700, 60, 0.004, 1, [[300, 90, "cone"], [760, 70, "round"], [1500, 100, "cone"], [1880, 80, "round"]]), 4, 4, 5),
    mid: withShadow(lib, hills(lib, P("extra.0"), 790, 34, 0.0032, 4, [[160, 150, "cone"], [1260, 120, "round"], [1760, 170, "cone"]])),
    ground: withShadow(lib, ground(lib, P("fg")), 0, -4, 8),
    br: [withShadow(lib, branch(lib, P("fg"), false, 5)), withShadow(lib, branch(lib, P("fg"), true, 9))],
    houses: [0, 1, 2].map((k) => withShadow(lib, house(lib, k, P("fg"), P("accent")))),
    hx: [560, 960, 1360], groundY: 872,
  };
}

const pathY = (x) => 790 - 34 * (0.6 * Math.sin(x * 0.0032 + 4) + 0.4 * Math.sin(x * 0.0032 * 2.3 + 8));
function walker(ctx, lib, t, x, col) {                          // stepped walk cycle, profile facing right
  const tp = lib.step(t, 12), ph = (tp * 12) % 8 / 8 * TAU, y = pathY(x + 60) - 2 - Math.abs(Math.sin(ph)) * 3;
  ctx.save(); ctx.translate(x, y); ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineCap = "round";
  const leg = (a, w) => { ctx.lineWidth = w; ctx.beginPath(); ctx.moveTo(0, -46); ctx.lineTo(Math.sin(a) * 26, -24); ctx.lineTo(Math.sin(a) * 30 + (a > 0 ? 4 : -2), 0); ctx.stroke(); };
  leg(0.55 * Math.sin(ph), 8); leg(-0.55 * Math.sin(ph), 8);
  ctx.beginPath(); ctx.moveTo(-14, -44); ctx.lineTo(14, -44); ctx.lineTo(10, -96); ctx.lineTo(-12, -96); ctx.closePath(); ctx.fill();       // coat
  ctx.beginPath(); ctx.arc(2, -108, 11, 0, TAU); ctx.fill();                                                                             // head
  ctx.beginPath(); ctx.moveTo(-26, -112); ctx.quadraticCurveTo(2, -136, 30, -112); ctx.closePath(); ctx.fill();                         // wide hat
  ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(6, -88); ctx.lineTo(20 + 8 * Math.sin(ph), -60); ctx.stroke();                          // arm
  ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(22 + 8 * Math.sin(ph), -64); ctx.lineTo(34 + 10 * Math.sin(ph), 2); ctx.stroke();       // walking stick
  ctx.restore();
}

function backdrop(ctx, lib, t) {
  const P = L.P, g = ctx.createRadialGradient(960, 560, 60, 960, 560, 1150);
  g.addColorStop(0, "#F4C877"); g.addColorStop(0.45, P("bg")); g.addColorStop(1, "#B8792A");
  ctx.fillStyle = g; ctx.fillRect(0, 0, lib.W, lib.H);
  lib.paper(ctx, { tone: P("bg"), amount: 0.35, blotch: 0.06, tooth: 0.03, fiber: 0.5, seed: 2 });
}
function layer(ctx, lib, img, x, y, t, seed, rotAmp = 0.003) {  // stepped wobble: each paper layer trembles a little, 12 fps
  const tp = lib.step(t, 12), r = rotAmp * Math.sin(tp * 5.3 + seed) , j = lib.hashS(seed, Math.round(tp * 12));
  ctx.save(); ctx.translate(x + img.width / 2, y + img.height); ctx.rotate(r); ctx.drawImage(img, -img.width / 2, -img.height + j * 0.8); ctx.restore();
}

function scene(ctx, t, tokens, lib) {
  const P = L.P, pan = t * 22, slide = (d) => (1 - lib.easeOf("steps(6)")(lib.seg(t, 0.05 + d, 0.55 + d))) * 90;
  backdrop(ctx, lib, t);
  layer(ctx, lib, L.far, -140 - pan * 0.35, slide(0) - 14, t, 1);
  layer(ctx, lib, L.mid, -140 - pan * 0.6, slide(0.1) - 14, t, 2);
  if (t >= 0.3) walker(ctx, lib, t, 60 + lib.step(t, 12) * 246 - pan * 0.6, P("fg"));   // at 3.0 s it stands in the gap between the first two houses
  // near: the ground band and the three houses standing on it
  const nx = -pan;
  L.houses.forEach((h, k) => {
    const t0 = 2.0 + k * 0.2; if (t < t0) return;
    const st = Math.floor((lib.step(t, 12) - lib.step(t0, 12)) * 12 + 1e-6), sy = st >= 4 ? (st === 4 ? 1.12 : 1) : (st + 1) / 4;   // rises in 4 steps, one-step pop
    ctx.save(); ctx.translate(L.hx[k] + nx, L.groundY + 10); ctx.scale(sy > 1 ? 1.06 : 1, sy); ctx.drawImage(h, -h.width / 2 + 6, -h.height + 22); ctx.restore();
  });
  layer(ctx, lib, L.ground, -140 + nx, L.groundY - 36 + slide(0.2), t, 3, 0.0015);
  // labels: cut out of the black ground, so the backdrop colour shows through
  L.houses.forEach((h, k) => {
    const t0 = 2.1 + k * 0.2; if (t < t0) return;
    ctx.save(); ctx.fillStyle = "#E9A94A"; ctx.textAlign = "center"; ctx.globalAlpha = lib.clamp((lib.step(t, 12) - t0) * 12 / 2 + 0.5);
    lib.setFont(ctx, tokens, "zh", 50, { weight: 700 }); ctx.fillText(lib.MOTIF[k].zh, L.hx[k] + nx, 956);
    lib.setFont(ctx, LAT, "it", 28); ctx.fillText(lib.MOTIF[k].en, L.hx[k] + nx, 1000);
    ctx.restore();
  });
  // lace foreground frame, top corners
  layer(ctx, lib, L.br[0], -30 - pan * 1.4 + slide(0.05) * -2, -40 - slide(0.05), t, 4, 0.02);
  layer(ctx, lib, L.br[1], lib.W - 520 + 30 - pan * 1.4 + slide(0.05) * 2, -40 - slide(0.05), t, 5, 0.02);
  title(ctx, t, tokens, lib);
}

function title(ctx, t, tokens, lib) {
  const P = L.P, tp = lib.step(t, 12), pop = (t0) => { if (tp < t0 - 1e-6) return null; const k = Math.round((tp - t0) * 12); return { scale: k === 0 ? 1.15 : 1 }; };
  ctx.save(); ctx.shadowColor = "rgba(20,10,5,0.35)"; ctx.shadowOffsetX = 4; ctx.shadowOffsetY = 4; ctx.shadowBlur = 5;
  lib.setFont(ctx, LAT, "en", 112); ctx.fillStyle = P("fg");
  const en = lib.layoutText(ctx, lib.TITLE_EN, { x: lib.W / 2, y: 290, align: "center", tracking: -0.01 * 112 });
  lib.drawGlyphs(ctx, en, (g, i) => pop(Math.round((0.8 + i / 12) * 12) / 12));
  lib.setFont(ctx, tokens, "zh", 74, { weight: 700 }); ctx.fillStyle = P("fg");
  const zh = lib.layoutText(ctx, lib.TITLE_ZH, { x: lib.W / 2, y: 402, align: "center", tracking: 0.14 * 74 });
  lib.drawGlyphs(ctx, zh, (g, i) => pop(Math.round((1.4 + i * 2 / 12) * 12) / 12));
  ctx.restore();
}

function endCard(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.fillStyle = P("fg"); ctx.fillRect(0, 0, lib.W, lib.H);
  const tp = lib.step(t, 12); if (tp < 4.72) return;
  ctx.fillStyle = "#E9A94A"; ctx.textAlign = "center";
  lib.setFont(ctx, tokens, "zh", 96, { weight: 700 });
  const zh = lib.layoutText(ctx, "剪影 · 剪纸", { x: lib.W / 2, y: 560, align: "center", tracking: 12 });
  lib.drawGlyphs(ctx, zh, (g, i) => (tp >= 4.72 + i / 24 ? { scale: Math.round((tp - 4.72 - i / 24) * 12) === 0 ? 1.15 : 1 } : null));
  if (tp >= 4.8) { lib.setFont(ctx, LAT, "it", 34); ctx.fillText("silhouette-papercut", lib.W / 2, 640); }
}

export function renderAt(t, ctx, tokens, lib) {
  if (t < 4.0) { scene(ctx, t, tokens, lib); return; }
  // silent-film iris on the lantern: close to a small circle, hold a beat, shut; then the end card
  const pan = t * 22, cx = L.hx[2] - pan + 52, cy = L.groundY + 10 - 96;   // lantern centre (sprite offset + baked shadow margin)
  const u = lib.seg(t, 4.0, 4.5), r = t < 4.5 ? lib.lerp(1500, 90, lib.ease.inOutCubic(u)) : t < 4.62 ? 90 : Math.max(0, 90 * (1 - lib.seg(t, 4.62, 4.72)));
  endCard(ctx, t, tokens, lib);
  if (r <= 0.5) return;
  const A = lib.offscreen("sp_A", (x) => scene(x, t, tokens, lib));
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, r, 0, TAU); ctx.clip(); ctx.drawImage(A, 0, 0); ctx.restore();
}
