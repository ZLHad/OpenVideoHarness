// clockwork-map swatch: one continuous low flight over a parchment sheet; precise brass mechanisms rise out of it.
// Ground: "mode-7" rows — under a pitched camera (no roll, no yaw) each screen row is one straight segment of the
// map texture, so each row is one drawImage from the right mip level; pitch can go all the way to top-down.
// Everything else (hatch pits, ground gears, shafts, armillary rings, hinged panels) is real 3D points pushed through
// the same projection; the tower bodies are 2.5D cylinders built on the projected base/top.
//   0.0–0.8  the key light comes up on a deckled parchment sheet; the camera is already gliding (never stops, never cuts)
//   0.8–2.4  title stamped letter by letter into the dark above the map; Chinese follows; brass double rule
//   1.88–2.6 three hatches iris open over turning gears, brass shafts link the sites, towers lift and lock
//   2.32–2.98 linked chain: the armillary rings swing open (outline) → shaft 1 turns → the three panels flip up
//            (storyboard) → shaft 2 turns → the vermilion pennant pops (draft)
//   3.1–3.8  a vermilion route inks itself from site to site
//   4.0–4.8  pull-back: the camera rises and pitches to top-down; the whole sheet lies on the dark table
// Gears have involute teeth, mesh at pitch-radius distances with ratios = tooth ratios, and step like an escapement
// once per eighth note (90 BPM) with a small recoil at the end of every step.

let L = null;
const MW = 3200, MH = 3700;
const BPM = 90, EIGHTH = 60 / BPM / 2;
const RH = 228, RT = 132;                              // hatch radius, tower radius (map units)
const SITE_X = [448, 960, 1472];                       // screen x of the three sites at t = 3 s (lib.slots)

// ───────────────────────── gears ─────────────────────────
const _gear = new Map();
function gearOutline(z) {                              // involute spur gear, module 1, pressure angle 20°
  if (_gear.has(z)) return _gear.get(z);
  const r = z / 2, ra = r + 1, rf = r - 1.25, a0 = Math.PI / 9, rb = r * Math.cos(a0);
  const inv = (a) => Math.tan(a) - a, half = Math.PI / (2 * z), inv0 = inv(a0);
  const psi = (rho) => Math.max(half * 0.22, half + inv0 - inv(Math.acos(rb / Math.max(rho, rb))));
  const P = (rho, ang) => [rho * Math.cos(ang), rho * Math.sin(ang)];
  const r0 = Math.max(rf, rb), pts = [], n = 6;
  for (let i = 0; i < z; i++) {
    const c = (i * 2 * Math.PI) / z;
    if (rf < rb) pts.push(P(rf, c - psi(rb)));
    for (let s = 0; s <= n; s++) { const rho = r0 + ((ra - r0) * s) / n; pts.push(P(rho, c - psi(rho))); }
    pts.push(P(ra, c));
    for (let s = n; s >= 0; s--) { const rho = r0 + ((ra - r0) * s) / n; pts.push(P(rho, c + psi(rho))); }
    if (rf < rb) pts.push(P(rf, c + psi(rb)));
    const a1 = c + psi(r0), a2 = c + (2 * Math.PI) / z - psi(r0);
    for (let s = 1; s < 3; s++) pts.push(P(rf, a1 + ((a2 - a1) * s) / 3));
  }
  _gear.set(z, pts); return pts;
}
// angle of a driven gear (z2) meshing a driver (z1, angle a1) whose centre-to-centre direction is phi
const mesh = (a1, z1, z2, phi) => phi + Math.PI + Math.PI / z2 - (z1 / z2) * (a1 - phi);
// escapement: one tooth per eighth note, the step lands in ~2 frames and recoils ~9 % before settling
function escapement(t, lib, phase, teeth) {
  const b = t / EIGHTH + phase, k = Math.floor(b), tau = (b - k) * EIGHTH;
  return ((k + lib.spring(tau, SPR.esc)) * 2 * Math.PI) / teeth;
}

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const LAND = lib.rgb(P("extra.0")), SEA = lib.rgb(P("extra.1")), INK = lib.rgb(P("extra.2")), EDGE = [239, 227, 194];
  // ── deckled parchment sheet (alpha outside the torn edge), coast, echo lines, burn toward the edge
  const tex = document.createElement("canvas"); tex.width = MW; tex.height = MH;
  const x = tex.getContext("2d"), img = x.createImageData(MW, MH), d = img.data;
  const gw = 161, gh = 186, field = new Float32Array(gw * gh), blot = new Float32Array(gw * gh);
  for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
    const wx = i * 20, wy = j * 20, cxd = (wx - 1600) / 1500, cyd = (wy - 1900) / 1750;
    field[j * gw + i] = lib.fbm2(wx / 900, wy / 900, { octaves: 5, seed: 42 }) * 0.85 + 0.22 - 0.35 * (cxd * cxd + cyd * cyd);
    blot[j * gw + i] = lib.fbm2(wx / 260, wy / 260, { octaves: 3, seed: 7 });
  }
  const bil = (F, u, v) => { const i = Math.min(gw - 2, Math.floor(u)), j = Math.min(gh - 2, Math.floor(v)), fu = u - i, fv = v - j, k = j * gw + i;
    return (F[k] * (1 - fu) + F[k + 1] * fu) * (1 - fv) + (F[k + gw] * (1 - fu) + F[k + gw + 1] * fu) * fv; };
  const deck = (n, seed) => Float32Array.from({ length: n }, (_, s) => 44 + 40 * (0.6 * lib.noise1(s / 120, seed) + 0.3 * lib.noise1(s / 26, seed + 9) + 0.1 * lib.noise1(s / 5, seed + 17)));
  const top = deck(MW, 1), bot = deck(MW, 2), lft = deck(MH, 3), rgt = deck(MH, 4);
  for (let py = 0; py < MH; py++) for (let px = 0; px < MW; px++) {
    const o = (py * MW + px) * 4;
    const e = Math.min(px - lft[py], MW - 1 - rgt[py] - px, py - top[px], MH - 1 - bot[px] - py);
    if (e < -1) { d[o + 3] = 0; continue; }
    const f = bil(field, px / 20, py / 20), b = bil(blot, px / 20, py / 20);
    const burn = lib.clamp(1 - e / 150) ** 2;
    const c = f >= 0 ? LAND : SEA, m = 1 + 0.07 * b - 0.42 * burn;
    let r = c[0] * m, g = c[1] * m, bb = c[2] * m, inkA = 0;
    if (Math.abs(f) < 0.0065) inkA = 0.9;
    else if (f < 0) for (let k = 1; k <= 3; k++) if (Math.abs(f + 0.028 * k) < 0.0032) inkA = Math.max(inkA, 0.55 / k);
    if (inkA > 0) { r = lib.lerp(r, INK[0], inkA); g = lib.lerp(g, INK[1], inkA); bb = lib.lerp(bb, INK[2], inkA); }
    if (e < 4) { const q = 0.55 * (1 - e / 4); r = lib.lerp(r, EDGE[0], q); g = lib.lerp(g, EDGE[1], q); bb = lib.lerp(bb, EDGE[2], q); }   // the torn edge catches the light
    d[o] = r; d[o + 1] = g; d[o + 2] = bb; d[o + 3] = Math.round(255 * lib.clamp(e + 1));
  }
  x.putImageData(img, 0, 0);
  const dogEar = (cx, cy, sx, sy, L0) => {            // fold line from (cx + sx·L0, cy) to (cx, cy + sy·L0)
    x.save(); x.globalCompositeOperation = "destination-out"; x.beginPath(); x.moveTo(cx - sx * 80, cy - sy * 80); x.lineTo(cx + sx * L0, cy - sy * 80); x.lineTo(cx + sx * L0, cy); x.lineTo(cx, cy + sy * L0); x.lineTo(cx - sx * 80, cy + sy * L0); x.closePath(); x.fill(); x.restore();
    x.save(); x.shadowColor = "rgba(40,28,14,0.55)"; x.shadowBlur = 18; x.shadowOffsetX = -sx * 6; x.shadowOffsetY = sy * 6;
    const fg = x.createLinearGradient(cx + sx * L0 * 0.5, cy + sy * L0 * 0.5, cx + sx * L0, cy + sy * L0);
    fg.addColorStop(0, "#EFE3C2"); fg.addColorStop(1, "#CDB68A"); x.fillStyle = fg;
    x.beginPath(); x.moveTo(cx + sx * L0, cy); x.lineTo(cx, cy + sy * L0); x.lineTo(cx + sx * L0 * 0.93, cy + sy * L0 * 0.93); x.closePath(); x.fill(); x.restore();
    x.strokeStyle = "rgba(90,66,36,0.6)"; x.lineWidth = 2; x.beginPath(); x.moveTo(cx + sx * L0, cy); x.lineTo(cx, cy + sy * L0); x.stroke();
  };
  dogEar(MW - 40, 40, -1, 1, 300); dogEar(40, MH - 40, 1, -1, 220);
  x.save(); x.globalCompositeOperation = "source-atop";
  x.strokeStyle = lib.rgba(P("extra.2"), 0.3); x.lineWidth = 2.2;
  for (const [rx, ry] of [[1600, 1500], [700, 2800]]) for (let k = 0; k < 16; k++) { const a = (k / 16) * lib.TAU; x.beginPath(); x.moveTo(rx, ry); x.lineTo(rx + Math.cos(a) * 4000, ry + Math.sin(a) * 4000); x.stroke(); }
  const rose = (cx, cy, R) => { x.save(); x.translate(cx, cy);
    for (let k = 0; k < 8; k++) { const a = (k / 8) * lib.TAU, rr = k % 2 ? R * 0.55 : R; x.fillStyle = k % 2 ? lib.rgba(P("extra.2"), 0.5) : P("extra.2");
      x.beginPath(); x.moveTo(0, 0); x.lineTo(Math.cos(a - 0.2) * rr * 0.25, Math.sin(a - 0.2) * rr * 0.25); x.lineTo(Math.cos(a) * rr, Math.sin(a) * rr); x.lineTo(Math.cos(a + 0.2) * rr * 0.25, Math.sin(a + 0.2) * rr * 0.25); x.closePath(); x.fill(); }
    x.strokeStyle = P("extra.2"); x.lineWidth = 3; x.beginPath(); x.arc(0, 0, R * 0.72, 0, lib.TAU); x.stroke(); x.restore(); };
  rose(700, 2800, 170); rose(2650, 900, 110);
  x.restore();
  const mip = (src, s) => { const c = document.createElement("canvas"); c.width = src.width / s; c.height = src.height / s; const q = c.getContext("2d"); q.imageSmoothingQuality = "high"; q.drawImage(src, 0, 0, c.width, c.height); return c; };
  const tex2 = mip(tex, 2), tex4 = mip(tex2, 2);
  // sheet outline for the table shadow (inset rectangle, sampled)
  const outline = [];
  for (let s = 0; s < 40; s++) outline.push([40 + (s / 40) * (MW - 80), 40]);
  for (let s = 0; s < 32; s++) outline.push([MW - 40, 40 + (s / 32) * (MH - 80)]);
  for (let s = 0; s < 40; s++) outline.push([MW - 40 - (s / 40) * (MW - 80), MH - 40]);
  for (let s = 0; s < 32; s++) outline.push([40, MH - 40 - (s / 32) * (MH - 80)]);
  L = { tex, tex2, tex4, outline };
  const C3 = camera(3.0, lib);
  L.sites = [[SITE_X[0], 822], [SITE_X[1], 806], [SITE_X[2], 818]].map(([sx, sy]) => ground(C3, sx, sy));
}

// camera: pitch th, height h, focal f, principal point (960, cy); positioned so ground point T maps to screen yT
function camera(t, lib) {
  const u = lib.tween(t, ...T.pull, lib.ease.inOutCubic);
  const th = (lib.lerp(41, 90, u) * Math.PI) / 180, h = lib.lerp(1020, 4500, u), f = 1000, cy = lib.lerp(844, 540, u), yT = lib.lerp(740, 470, u);
  const TX = lib.lerp(1600 + 28 * (t - 3), 1600, u), TV = lib.lerp(2800 + 42 * (3 - t), 1850, u);
  const vs = (yT - cy) / f, s = h / (Math.sin(th) + vs * Math.cos(th)), dT = s * (Math.cos(th) - vs * Math.sin(th));
  return { th, h, f, cy, cx: 960, X: TX, Z: TV + dT, sn: Math.sin(th), cs: Math.cos(th) };
}
function ground(C, sx, sy) { const vs = (sy - C.cy) / C.f, s = C.h / (C.sn + vs * C.cs); return [C.X + (s * (sx - C.cx)) / C.f, C.Z - s * (C.cs - vs * C.sn)]; }
function project(C, X, Y, V) {                          // map point (X, height Y, V) → [screen x, screen y, px per unit, depth]
  const dx = X - C.X, dy = Y - C.h, dz = C.Z - V;
  const zc = -dy * C.sn + dz * C.cs, yc = -dy * C.cs - dz * C.sn;
  return [C.cx + (C.f * dx) / zc, C.cy + (C.f * yc) / zc, C.f / zc, zc];
}
const poly = (ctx, pts) => { ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); };
// a horizontal ring of points (radius r) at height Y around (X, V)
const hring = (C, X, Y, V, r, n = 48) => Array.from({ length: n }, (_, i) => { const a = (i / n) * Math.PI * 2; return project(C, X + r * Math.cos(a), Y, V + r * Math.sin(a)); });

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const C = camera(t, lib);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  const light = lib.tween(t, 0.0, 0.16, lib.ease.outCubic);
  // the desk: walnut plank seams receding to the horizon, a warm lamp pool behind the sheet
  ctx.save();
  const lamp = ctx.createRadialGradient(W / 2, 60, 40, W / 2, 60, 1100);
  lamp.addColorStop(0, `rgba(120,78,36,${0.55 * light})`); lamp.addColorStop(1, "rgba(22,18,13,0)");
  ctx.fillStyle = lamp; ctx.fillRect(0, 0, W, H);
  ctx.strokeStyle = `rgba(8,5,2,${0.55 * light})`;
  for (let i = 1; i < 40; i++) {
    const V = -i * i * 60, p0 = project(C, -6000, -3, V), p1 = project(C, 9000, -3, V);
    if (p0[3] < 50 || p1[3] < 50) continue;
    ctx.lineWidth = Math.max(0.6, 3 * p0[2]); ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke();
  }
  ctx.restore();
  // ── the sheet's shadow on the table (soft, offset away from the key light)
  ctx.save(); ctx.filter = `blur(${Math.max(6, 26 * project(C, 1600, 0, 1300)[2]).toFixed(1)}px)`; ctx.fillStyle = "rgba(4,3,2,0.75)";
  poly(ctx, L.outline.map(([X, V]) => project(C, X + 28, -2, V - 44))); ctx.fill(); ctx.restore();
  // ── ground, row by row (mode-7)
  ctx.save(); ctx.globalAlpha = 0.25 + 0.75 * light; ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
  for (let y = 0; y < H; y++) {
    const vs = (y + 0.5 - C.cy) / C.f, den = C.sn + vs * C.cs;
    if (den <= 0.002) continue;
    const s = C.h / den, V = C.Z - s * (C.cs - vs * C.sn);
    const u0 = C.X + (s * (0 - C.cx)) / C.f, u1 = C.X + (s * (W - C.cx)) / C.f, ratio = (u1 - u0) / W;
    const vs2 = (y + 1.5 - C.cy) / C.f, V2 = C.Z - (C.h / (C.sn + vs2 * C.cs)) * (C.cs - vs2 * C.sn), sh = Math.max(0.5, Math.abs(V2 - V));
    const [src, k] = ratio > 3.5 ? [L.tex4, 4] : ratio > 1.6 ? [L.tex2, 2] : [L.tex, 1];
    const sx0 = Math.max(0, u0), sx1 = Math.min(MW, u1), sv = V - sh / 2;
    if (sx1 <= sx0 || sv > MH || sv + sh < 0) continue;
    const dx0 = ((sx0 - u0) / (u1 - u0)) * W, dx1 = ((sx1 - u0) / (u1 - u0)) * W;
    ctx.drawImage(src, sx0 / k, Math.max(0, sv) / k, (sx1 - sx0) / k, Math.max(0.5, sh) / k, dx0, y, dx1 - dx0, 1.02);
  }
  ctx.restore();
  // ── one warm key light from the sheet's centre, falling off toward the edges
  const lc = project(C, 1600, 0, 1250);
  ctx.save(); const g = ctx.createRadialGradient(lc[0], Math.min(H, lc[1]), 80, lc[0], Math.min(H, lc[1]), 1300);
  g.addColorStop(0, "rgba(255,210,140,0.10)"); g.addColorStop(0.55, "rgba(22,18,13,0)"); g.addColorStop(1, "rgba(22,18,13,0.55)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // the lamp falls off toward the far edge of the sheet: the title sits in that shade, the map stays visible under it
  const shade = ctx.createLinearGradient(0, 0, 0, 380), sa = 1 - lib.seg(C.th * 180 / Math.PI, 50, 70);
  shade.addColorStop(0, lib.rgba(P("bg"), 0.82 * sa)); shade.addColorStop(0.6, lib.rgba(P("bg"), 0.55 * sa)); shade.addColorStop(1, lib.rgba(P("bg"), 0));
  ctx.fillStyle = shade; ctx.fillRect(0, 0, W, 380); ctx.restore();

  // ── hook (0.0–0.5 s): a brass compass ring drops onto the sheet and its bearing lines shoot out across it
  roseHook(ctx, t, tokens, lib, C);

  // ── route (vermilion ink) from site to site
  const ru = lib.tween(t, ...T.route, lib.ease.inOutSine);
  if (ru > 0) {
    const pts = [];
    for (let i = 0; i <= 60; i++) {
      const q = i / 60, sg = Math.min(1, Math.floor(q * 2)), w = q * 2 - sg, A = L.sites[sg], B = L.sites[sg + 1];
      const mx = (A[0] + B[0]) / 2, mv = (A[1] + B[1]) / 2 + 330;
      pts.push(project(C, (1 - w) ** 2 * A[0] + 2 * (1 - w) * w * mx + w * w * B[0], 0, (1 - w) ** 2 * A[1] + 2 * (1 - w) * w * mv + w * w * B[1]));
    }
    ctx.save(); ctx.strokeStyle = P("accent"); ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.setLineDash([22, 14]);
    ctx.lineWidth = Math.max(2.5, 14 * pts[30][2]); lib.strokePartial(ctx, pts.map((p) => [p[0], p[1]]), ru); ctx.restore();
  }

  // ── linked machinery: pits and gears first, shafts on the surface, then towers far → near
  for (let k = 0; k < 3; k++) pit(ctx, t, tokens, lib, C, k);
  for (let k = 0; k < 2; k++) shaft(ctx, t, tokens, lib, C, k);
  const order = [0, 1, 2].sort((a, b) => L.sites[a][1] - L.sites[b][1]);
  for (const k of order) tower(ctx, t, tokens, lib, C, k);
  for (const k of order) plate(ctx, t, tokens, lib, C, k);

  // ── title, stamped into the dark above the sheet
  const out = lib.tween(t, ...T.titleOut, lib.ease.inCubic);
  ctx.save(); ctx.globalAlpha = 1 - out;
  const fg = lib.rgb(P("fg")), stamp = (a) => { const c = [255, 241, 200].map((v, j) => Math.round(lib.lerp(v, fg[j], a))); return { scale: 1.12 - 0.12 * lib.ease.outCubic(a), fill: `rgb(${c.join(",")})` }; };
  lib.setFont(ctx, tokens, "display", 100, { weight: 600 });
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: W / 2, y: 150, align: "center", tracking: 0.04 * 100 });
  lib.drawGlyphs(ctx, lay, (gl, i) => { const a = lib.seg(t, T.letter0 + i * T.stag, T.letter0 + i * T.stag + T.stamp); return a <= 0 ? null : stamp(a); });
  lib.setFont(ctx, tokens, "zh", 62, { weight: 700 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 236, align: "center", tracking: 0.1 * 62 });
  lib.drawGlyphs(ctx, zl, (gl, i) => { const a = lib.seg(t, T.zh0 + i * T.zhStag, T.zh0 + i * T.zhStag + 0.15); return a <= 0 ? null : stamp(a); });
  ctx.strokeStyle = P("extra.3"); ctx.lineWidth = 2;
  const ru2 = lib.tween(t, 1.9, 2.4, lib.ease.outCubic);
  if (ru2 > 0) for (const yy of [268, 275]) lib.strokePartial(ctx, [[W / 2 - 360 * ru2, yy], [W / 2 + 360 * ru2, yy]], 1);
  ctx.restore();

  // ── end: name under the top-down sheet
  const ea = lib.tween(t, ...T.end, lib.ease.outCubic);
  if (ea > 0) {
    ctx.save(); ctx.globalAlpha = ea; ctx.fillStyle = P("fg");
    lib.setFont(ctx, tokens, "display", 60, { weight: 600 }); lib.drawText(ctx, "Clockwork Map", W / 2 - 20, 1004, { align: "right", tracking: 0.04 * 60 });
    lib.setFont(ctx, tokens, "zh", 50, { weight: 700 }); lib.drawText(ctx, "机械钟表地图", W / 2 + 20, 1002, { tracking: 0.1 * 50 });
    ctx.restore();
  }
  lib.grain(ctx, t, { amount: 0.035, fps: 12, seed: 5 });
}

function roseHook(ctx, t, tokens, lib, C) {
  const P = (q) => lib.color(tokens, q), B = brass(P);
  const cX = 1600, cV = (L.sites[0][1] + L.sites[1][1] + L.sites[2][1]) / 3 - 520;
  const drop = lib.spring(t - T.compass, SPR.compass), sc = lib.lerp(1.35, 1, drop);
  const grow = lib.ease.outExpo(lib.seg(t, ...T.bearings));
  const fade = 1 - 0.45 * lib.seg(t, 1.2, 2.0);                            // settles back into the map once the title is up
  ctx.save(); ctx.globalAlpha = fade;
  // bearing lines
  if (grow > 0) {
    ctx.strokeStyle = lib.rgba(P("extra.2"), 0.62); ctx.lineCap = "round";
    for (let i = 0; i < 32; i++) {
      const a = (i / 32) * lib.TAU, r0 = 520, r1 = lib.lerp(r0, 2900, grow);
      const p0 = project(C, cX + r0 * Math.cos(a), 0, cV + r0 * Math.sin(a)), p1 = project(C, cX + r1 * Math.cos(a), 0, cV + r1 * Math.sin(a));
      if (p1[3] < 50) continue;
      ctx.lineWidth = i % 4 === 0 ? 3.2 : 1.8; ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke();
    }
  }
  // the brass ring (with degree ticks) and the rotating compass star
  const ring = (r, n = 96) => Array.from({ length: n }, (_, i) => { const a = (i / n) * lib.TAU; return project(C, cX + r * sc * Math.cos(a), 0, cV + r * sc * Math.sin(a)); });
  const outer = ring(520), inner = ring(472);
  ctx.beginPath(); outer.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  inner.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  const xs = outer.map((p) => p[0]), ys = outer.map((p) => p[1]);
  ctx.fillStyle = brassFill(ctx, B, Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)); ctx.fill("evenodd");
  ctx.strokeStyle = B.DEEP; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.strokeStyle = lib.rgba(B.DEEP, 0.85);
  for (let i = 0; i < 72; i++) { const a = (i / 72) * lib.TAU, r0 = 472, r1 = i % 6 === 0 ? 420 : 445;
    const p0 = project(C, cX + r0 * sc * Math.cos(a), 0, cV + r0 * sc * Math.sin(a)), p1 = project(C, cX + r1 * sc * Math.cos(a), 0, cV + r1 * sc * Math.sin(a));
    ctx.lineWidth = i % 6 === 0 ? 2.4 : 1.2; ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke(); }
  const rot = -0.9 * (1 - lib.spring(t - 0.08, { w: 16, zeta: 0.55 }));
  for (let k = 0; k < 8; k++) {
    const a = rot + (k / 8) * lib.TAU - Math.PI / 2, rr = (k % 2 ? 230 : 390) * sc, wv = 0.16;
    const pts = [[0, 0], [rr * 0.22 * Math.cos(a - wv * 2), rr * 0.22 * Math.sin(a - wv * 2)], [rr * Math.cos(a), rr * Math.sin(a)], [rr * 0.22 * Math.cos(a + wv * 2), rr * 0.22 * Math.sin(a + wv * 2)]]
      .map(([dx, dv]) => project(C, cX + dx, 0, cV + dv));
    poly(ctx, pts); ctx.fillStyle = k % 2 ? lib.rgba(P("extra.2"), 0.75) : B.BR; ctx.fill(); ctx.strokeStyle = B.DEEP; ctx.lineWidth = 1.4; ctx.stroke();
  }
  ctx.restore();
}

// ───────────────────────── timings of the linked chain ─────────────────────────
// each tower is pushed up in three escapement steps on eighth notes (90 BPM: 1/3 s apart); tower 1 locks on the
// 2.0 s bar line, the others one eighth later each; the tops then open as a chain
const STEPS = [[4 / 3, 5 / 3, 2], [5 / 3, 2, 7 / 3], [2, 7 / 3, 8 / 3]];
const T = {
  hatch: (k) => STEPS[k][0] - 0.12, rise: (k) => STEPS[k][0], lock: (k) => STEPS[k][2],
  rings: [2.02, 2.34], shaft1: [2.24, 2.44], panels: [2.36, 2.62], shaft2: [2.5, 2.66], flag: 8 / 3,
  compass: -0.02, bearings: [0.04, 0.46], letter0: 0.86, stag: 0.06, stamp: 0.14, zh0: 1.5, zhStag: 0.09,
  route: [3.1, 3.8], pull: [4.0, 4.8], titleOut: [4.0, 4.3], end: [4.55, 4.85],
};
// spring parameters shared by the picture and the foley: a sound lands on the spring's first arrival at 1
const SPR = { compass: { w: 22, zeta: 0.6 }, step: { w: 60, zeta: 0.6 }, esc: { w: 80, zeta: 0.6 }, panel: { w: 24, zeta: 0.72 }, flag: { w: 30, zeta: 0.55 } };
const arrive = ({ w, zeta }) => { const r = Math.sqrt(1 - zeta * zeta); return (Math.PI - Math.atan(r / zeta)) / (w * r); };
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;   // pan = (2x/W − 1) · 0.7
const TITLE = "Every frame is code.";                                          // = lib.TITLE_EN; glyph index counts spaces
const words = [...TITLE].flatMap((ch, i) => (ch !== " " && (i === 0 || TITLE[i - 1] === " ") ? [i] : []));
const smooth = (u) => { u = Math.min(1, Math.max(0, u)); return u * u * (3 - 2 * u); };   // ≈ the pull-back's inOutCubic, only for tick distance
export const FOLEY = [
  { t: T.compass + arrive(SPR.compass), sfx: "impact", gain_db: -8 },                      // the brass compass lands on the sheet
  { t: 0.2, sfx: "whoosh", gain_db: -14 },                                                  // bearing lines shoot out
  ...[words[0], words[words.length - 1]].map((i) => ({ t: T.letter0 + i * T.stag + T.stamp, sfx: "click", gain_db: -14, pan: pan(960 + (i / (TITLE.length - 1) - 0.5) * 1150) })),   // first and last word stamped
  // tower escapement steps (eighth notes): tick on a step, click on a lock; pan = the site(s) moving
  ...[4 / 3, 5 / 3, 2, 7 / 3, 8 / 3].map((s0) => {
    const moving = [0, 1, 2].filter((k) => STEPS[k].includes(s0)), lock = [0, 1, 2].find((k) => T.lock(k) === s0);
    const x = lock != null ? SITE_X[lock] : moving.reduce((a, k) => a + SITE_X[k], 0) / moving.length;
    return { t: s0 + arrive(SPR.step), sfx: lock != null ? "click" : "tick", gain_db: lock != null ? -8 : -12, pan: pan(x) };
  }),
  { t: (T.rings[0] + T.rings[1]) / 2, sfx: "whoosh", gain_db: -16, pan: pan(SITE_X[0]) },  // armillary rings swing open
  { t: T.panels[0] + 0.07 + arrive(SPR.panel), sfx: "shutter", gain_db: -12, pan: pan(SITE_X[1]) },   // hinged panels stand up
  { t: T.flag + 0.02 + arrive(SPR.flag), sfx: "pop", gain_db: -10, pan: pan(SITE_X[2]) },            // the pennant
  // after the chain: the master escapement keeps ticking on eighths, receding as the camera climbs
  ...[9, 10, 11, 12, 13, 14].map((k) => { const t = k * EIGHTH + arrive(SPR.esc); return { t, sfx: "tick", gain_db: -18, dist: +(1 + 3.4 * smooth((t - T.pull[0]) / (T.pull[1] - T.pull[0]))).toFixed(2) }; }),
  { t: (T.pull[0] + T.pull[1]) / 2, sfx: "whoosh", gain_db: -12 },                          // pull-back to top-down
];
const brass = (P) => ({ BR: P("extra.3"), HI: P("extra.4"), SHD: P("extra.5"), INK: P("extra.2"), MID: "#8A6A3C", DEEP: "#4A3820", SPEC: "#FFF0C4" });

// brass fill for a projected shape: light from the upper left, darker to the lower right
function brassFill(ctx, B, x0, y0, x1, y1) {
  const g = ctx.createLinearGradient(x0, y0, x1, y1);
  g.addColorStop(0, B.HI); g.addColorStop(0.35, B.BR); g.addColorStop(0.75, B.MID); g.addColorStop(1, B.DEEP); return g;
}
// a gear drawn from projected points (ground gears) or screen-space (face gears): teeth + rim engraving + hub + holes
function gearShape(ctx, lib, B, pts, cen, rim, hub, holes) {
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
  ctx.fillStyle = brassFill(ctx, B, Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys));
  ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  holes.forEach((h) => { ctx.moveTo(h[0][0], h[0][1]); h.forEach((p) => ctx.lineTo(p[0], p[1])); ctx.closePath(); });
  ctx.fill("evenodd");
  ctx.strokeStyle = lib.rgba(B.DEEP, 0.9); ctx.lineWidth = 1.2; ctx.stroke();
  ctx.strokeStyle = lib.rgba(B.DEEP, 0.75); poly(ctx, rim); ctx.stroke();
  ctx.fillStyle = B.MID; poly(ctx, hub); ctx.fill(); ctx.strokeStyle = B.DEEP; ctx.stroke();
  ctx.fillStyle = B.SPEC; ctx.beginPath(); ctx.arc(cen[0] - 2, cen[1] - 2, 2.2, 0, lib.TAU); ctx.fill();
}
// a gear lying in the ground plane at (X, Y, V), module m (map units), z teeth, angle a
function groundGear(ctx, lib, B, C, X, Y, V, m, z, a) {
  const ol = gearOutline(z), ca = Math.cos(a), sa = Math.sin(a), r = (m * z) / 2;
  const pr = (px, py) => project(C, X + m * (px * ca - py * sa), Y, V + m * (px * sa + py * ca));
  const pts = ol.map(([px, py]) => pr(px, py)), circ = (rr, n = 32, off = 0) => Array.from({ length: n }, (_, i) => { const q = (i / n) * lib.TAU; return project(C, X + rr * Math.cos(q + off), Y, V + rr * Math.sin(q + off)); });
  const holes = [0, 1, 2, 3, 4].map((j) => { const q = a + (j / 5) * lib.TAU, hx = X + r * 0.52 * Math.cos(q), hv = V + r * 0.52 * Math.sin(q);
    return Array.from({ length: 16 }, (_, i) => { const w = (i / 16) * lib.TAU; return project(C, hx + r * 0.17 * Math.cos(w), Y, hv + r * 0.17 * Math.sin(w)); }); });
  gearShape(ctx, lib, B, pts, project(C, X, Y, V), circ(r * 0.8), circ(r * 0.22), holes);
}
// a gear in screen space (face plates)
function faceGear(ctx, lib, B, cx, cy, m, z, a) {
  const ol = gearOutline(z), ca = Math.cos(a), sa = Math.sin(a), r = (m * z) / 2;
  const pts = ol.map(([px, py]) => [cx + m * (px * ca - py * sa), cy + m * (px * sa + py * ca)]);
  const circ = (rr, n = 28) => Array.from({ length: n }, (_, i) => { const q = (i / n) * lib.TAU; return [cx + rr * Math.cos(q), cy + rr * Math.sin(q)]; });
  const holes = [0, 1, 2, 3].map((j) => { const q = a + (j / 4) * lib.TAU, hx = cx + r * 0.5 * Math.cos(q), hy = cy + r * 0.5 * Math.sin(q);
    return Array.from({ length: 12 }, (_, i) => { const w = (i / 12) * lib.TAU; return [hx + r * 0.16 * Math.cos(w), hy + r * 0.16 * Math.sin(w)]; }); });
  gearShape(ctx, lib, B, pts, [cx, cy], circ(r * 0.8), circ(r * 0.24), holes);
}

// hatch: an iris opening in the sheet; inside, two meshing gears turn in the dark
function pit(ctx, t, tokens, lib, C, k) {
  const P = (q) => lib.color(tokens, q), B = brass(P);
  const [X, V] = L.sites[k], op = lib.tween(t, T.hatch(k), T.hatch(k) + 0.16, lib.ease.outCubic);
  if (op <= 0) return;
  const R = RH * op, inner = hring(C, X, 0, V, R, 56);
  ctx.save();
  poly(ctx, inner); ctx.fillStyle = "#120C07"; ctx.fill(); ctx.clip();
  const zBig = 30, mBig = 11.2, zSm = 12, aBig = escapement(t, lib, k * 0.31, zBig), phi = -0.9;
  const dC = (mBig * (zBig + zSm)) / 2;
  groundGear(ctx, lib, B, C, X, -46, V, mBig, zBig, aBig);
  groundGear(ctx, lib, B, C, X + dC * Math.cos(phi), -46, V + dC * Math.sin(phi), mBig, zSm, mesh(aBig, zBig, zSm, phi));
  // the pit wall: occlusion falling off from the rim
  const cen = project(C, X, 0, V), rr = project(C, X + R, 0, V)[0] - cen[0];
  const ao = ctx.createRadialGradient(cen[0], cen[1], rr * 0.35, cen[0], cen[1], rr * 1.05);
  ao.addColorStop(0, "rgba(18,12,7,0)"); ao.addColorStop(1, "rgba(18,12,7,0.85)"); ctx.fillStyle = ao; ctx.fillRect(cen[0] - rr * 1.2, cen[1] - rr, rr * 2.4, rr * 2);
  ctx.restore();
  // brass rim with rivets
  const outer = hring(C, X, 0, V, R + 24, 56);
  ctx.save(); ctx.beginPath(); outer.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  inner.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath();
  const xs = outer.map((p) => p[0]), ys = outer.map((p) => p[1]);
  ctx.fillStyle = brassFill(ctx, B, Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)); ctx.fill("evenodd");
  ctx.strokeStyle = lib.rgba(B.DEEP, 0.8); ctx.lineWidth = 1.2; ctx.stroke();
  for (let j = 0; j < 12; j++) { const q = (j / 12) * lib.TAU, p = project(C, X + (R + 12) * Math.cos(q), 0, V + (R + 12) * Math.sin(q));
    ctx.fillStyle = B.DEEP; ctx.beginPath(); ctx.arc(p[0], p[1], Math.max(1.2, 5 * p[2]), 0, lib.TAU); ctx.fill();
    ctx.fillStyle = B.SPEC; ctx.beginPath(); ctx.arc(p[0] - 0.6, p[1] - 0.6, Math.max(0.6, 2 * p[2]), 0, lib.TAU); ctx.fill(); }
  ctx.restore();
}

// drive shafts on the surface between sites; knurled bands travel along them while they turn
function shaft(ctx, t, tokens, lib, C, k) {
  const P = (q) => lib.color(tokens, q), B = brass(P);
  const [X0, V0] = L.sites[k], [X1, V1] = L.sites[k + 1];
  const grow = lib.tween(t, T.hatch(k + 1), T.hatch(k + 1) + 0.25, lib.ease.outCubic);
  if (grow <= 0) return;
  const len = Math.hypot(X1 - X0, V1 - V0), ux = (X1 - X0) / len, uv = (V1 - V0) / len, a = RH + 24, b = len - RH - 24;
  const p0 = project(C, X0 + ux * a, 12, V0 + uv * a), p1 = project(C, X0 + ux * lib.lerp(a, b, grow), 12, V0 + uv * lib.lerp(a, b, grow));
  const w = 26 * (p0[2] + p1[2]) / 2;
  ctx.save(); ctx.lineCap = "butt";
  ctx.strokeStyle = B.DEEP; ctx.lineWidth = w + 3; ctx.beginPath(); ctx.moveTo(p0[0], p0[1]); ctx.lineTo(p1[0], p1[1]); ctx.stroke();
  ctx.strokeStyle = B.BR; ctx.lineWidth = w; ctx.stroke();
  ctx.strokeStyle = B.HI; ctx.lineWidth = w * 0.3; ctx.beginPath(); ctx.moveTo(p0[0], p0[1] - w * 0.2); ctx.lineTo(p1[0], p1[1] - w * 0.2); ctx.stroke();
  const win = k === 0 ? T.shaft1 : T.shaft2, spin = lib.tween(t, win[0], win[1], lib.ease.inOutSine) * 3 + (t > win[1] ? 0 : 0);
  ctx.strokeStyle = lib.rgba(B.DEEP, 0.85); ctx.lineWidth = w;
  for (let q = 0; q < 1; q += 1 / 14) {                       // knurl bands; they travel while the shaft turns
    const s = lib.lerp(a, lib.lerp(a, b, grow), lib.fract(q + spin / 14 * 3)), s2 = s + 10;
    if (s2 > lib.lerp(a, b, grow)) continue;
    const pa = project(C, X0 + ux * s, 12, V0 + uv * s), pb = project(C, X0 + ux * s2, 12, V0 + uv * s2);
    ctx.beginPath(); ctx.moveTo(pa[0], pa[1]); ctx.lineTo(pb[0], pb[1]); ctx.stroke();
  }
  ctx.restore();
}

function tower(ctx, t, tokens, lib, C, k) {
  const P = (q) => lib.color(tokens, q), B = brass(P);
  const [X, V] = L.sites[k], t0 = T.rise(k);
  if (t < t0) return;
  const rise = STEPS[k].reduce((sum, s0) => sum + lib.spring(t - s0, SPR.step) / 3, 0);   // three clicks, each with recoil
  const Hmax = [280, 262, 300][k], hgt = Hmax * rise;
  const base = project(C, X, 0, V), top = project(C, X, hgt, V), sc = base[2], w = 2 * RT * sc;
  const ryOf = (Y) => { const a = project(C, X, Y, V - RT), b = project(C, X, Y, V + RT); return Math.max(1.5, Math.abs(b[1] - a[1]) / 2); };
  const eb = ryOf(0), et = ryOf(hgt);
  const x0 = base[0] - w / 2, yTop = top[1], yBase = base[1];
  ctx.save();
  // contact shadow on the sheet
  ctx.fillStyle = "rgba(20,14,8,0.45)"; ctx.beginPath(); ctx.ellipse(base[0] + w * 0.35, yBase + eb * 0.3, w * 0.62, eb * 1.25, 0.1, 0, lib.TAU); ctx.fill();
  // a big exposed wheel behind the body, its teeth breaking the silhouette (turns with the escapement)
  if (yBase - yTop > w * 0.6) {
    const zS = 24, RS = w * 0.46, mS = (2 * RS) / zS, sx = k === 2 ? x0 - RS * 0.18 : x0 + w + RS * 0.18, sy = yTop + (yBase - yTop) * 0.46;
    faceGear(ctx, lib, B, sx, sy, mS, zS, (k === 2 ? 1 : -1) * escapement(t, lib, 0.2 + k * 0.1, 48));
  }
  if (yBase - yTop > 1) {
    // cylinder body: dark edge · mid · bright band · specular stripe · falloff · reflected rim
    const gr = ctx.createLinearGradient(x0, 0, x0 + w, 0);
    [[0, B.DEEP], [0.07, B.MID], [0.18, B.BR], [0.27, B.HI], [0.31, B.SPEC], [0.35, B.HI], [0.5, B.BR], [0.72, B.MID], [0.9, B.DEEP], [1, B.MID]].forEach(([s, c]) => gr.addColorStop(s, c));
    ctx.beginPath(); ctx.moveTo(x0, yTop); ctx.lineTo(x0, yBase); ctx.ellipse(base[0], yBase, w / 2, eb, 0, Math.PI, 0, true); ctx.lineTo(x0 + w, yTop); ctx.closePath();
    ctx.fillStyle = gr; ctx.fill();
    // ambient occlusion: toward the pit and under the cap
    const ao = ctx.createLinearGradient(0, yTop, 0, yBase + eb);
    ao.addColorStop(0, "rgba(28,18,8,0.45)"); ao.addColorStop(0.08, "rgba(28,18,8,0)"); ao.addColorStop(0.78, "rgba(28,18,8,0)"); ao.addColorStop(1, "rgba(28,18,8,0.6)");
    ctx.fillStyle = ao; ctx.fill();
    ctx.strokeStyle = lib.rgba(B.DEEP, 0.95); ctx.lineWidth = 1.5; ctx.stroke();
    // engraved bands with rivets
    const band = (f) => {
      const yy = yTop + (yBase - yTop) * f, ee = lib.lerp(et, eb, f);
      ctx.strokeStyle = lib.rgba(B.DEEP, 0.9); ctx.lineWidth = 1.6; ctx.beginPath(); ctx.ellipse(base[0], yy, w / 2, ee, 0, 0, Math.PI); ctx.stroke();
      ctx.strokeStyle = lib.rgba(B.SPEC, 0.55); ctx.lineWidth = 1; ctx.beginPath(); ctx.ellipse(base[0], yy + 2, w / 2 - 1, ee, 0, 0.1, Math.PI - 0.1); ctx.stroke();
      for (const ph of [-1.1, -0.55, 0, 0.55, 1.1]) { const rx = base[0] + (w / 2) * Math.sin(ph), ry = yy + ee * Math.cos(ph) - 5;
        ctx.fillStyle = B.DEEP; ctx.beginPath(); ctx.arc(rx, ry, Math.max(1.5, 4.5 * sc), 0, lib.TAU); ctx.fill();
        ctx.fillStyle = B.SPEC; ctx.beginPath(); ctx.arc(rx - 1, ry - 1, Math.max(0.8, 1.8 * sc), 0, lib.TAU); ctx.fill(); }
    };
    if (yBase - yTop > 40) { band(0.12); band(0.9); }
    // face plate with a meshing gear train (driver on the escapement, idler, output)
    const ph = (yBase - yTop) * 0.62, pw = w * 0.86;
    if (ph > 50) {
      const pcx = base[0] - w * 0.03, pcy = yTop + (yBase - yTop) * 0.52;
      ctx.fillStyle = "#3E2F1B"; ctx.beginPath(); ctx.roundRect(pcx - pw / 2, pcy - ph / 2, pw, ph, 8); ctx.fill();
      ctx.strokeStyle = lib.rgba(B.HI, 0.6); ctx.lineWidth = 1.2; ctx.stroke();
      const m = Math.min(pw / 36, ph / 22), z1 = 14, z2 = 8, z3 = 18, a1 = escapement(t, lib, k * 0.37, z1);
      const c1 = [pcx - 9.5 * m, pcy + 1.5 * m], phi12 = -0.62, d12 = (m * (z1 + z2)) / 2, c2 = [c1[0] + d12 * Math.cos(phi12), c1[1] + d12 * Math.sin(phi12)];
      const a2 = mesh(a1, z1, z2, phi12), phi23 = 0.42, d23 = (m * (z2 + z3)) / 2, c3 = [c2[0] + d23 * Math.cos(phi23), c2[1] + d23 * Math.sin(phi23)], a3 = mesh(a2, z2, z3, phi23);
      ctx.save(); ctx.beginPath(); ctx.roundRect(pcx - pw / 2, pcy - ph / 2, pw, ph, 8); ctx.clip();
      faceGear(ctx, lib, B, c1[0], c1[1], m, z1, a1); faceGear(ctx, lib, B, c2[0], c2[1], m, z2, a2); faceGear(ctx, lib, B, c3[0], c3[1], m, z3, a3);
      ctx.restore();
    }
  }
  // cap: domed, lit from the upper left, engraved rim
  const cg = ctx.createRadialGradient(base[0] - w * 0.18, yTop - et * 0.3, 2, base[0], yTop, w * 0.55);
  cg.addColorStop(0, B.SPEC); cg.addColorStop(0.35, B.HI); cg.addColorStop(1, B.MID);
  ctx.fillStyle = cg; ctx.beginPath(); ctx.ellipse(base[0], yTop, w / 2, et, 0, 0, lib.TAU); ctx.fill();
  ctx.strokeStyle = B.DEEP; ctx.lineWidth = 1.5; ctx.stroke();
  ctx.strokeStyle = lib.rgba(B.DEEP, 0.6); ctx.beginPath(); ctx.ellipse(base[0], yTop, w * 0.38, et * 0.76, 0, 0, lib.TAU); ctx.stroke();
  ctx.restore();
  if (k === 0) armillary(ctx, t, lib, B, C, X, hgt, V);
  if (k === 1) triptych(ctx, t, lib, B, C, X, hgt, V);
  if (k === 2) pennant(ctx, t, lib, B, C, X, hgt, V, P("accent"));
}

// outline: three armillary rings swing open about tilted axes, then step round with the escapement
function armillary(ctx, t, lib, B, C, X, H0, V) {
  const op = lib.tween(t, T.rings[0], T.rings[1], lib.ease.inOutCubic);
  const cY = H0 + 32 + 116 * op;
  const cen = project(C, X, cY, V);
  const turn = t > T.rings[1] ? escapement(t, lib, 0.5, 24) - escapement(T.rings[1], lib, 0.5, 24) : 0;
  const rings = [[192, 0.0, 1.35], [163, 2.09, 1.0], [134, 4.19, 0.62]];
  const segs = [];
  rings.forEach(([r, az, tilt], j) => {
    const ang = tilt * op, ax = [Math.cos(az + turn), 0, Math.sin(az + turn)];
    const pts = [];
    for (let i = 0; i <= 64; i++) {
      const s = (i / 64) * lib.TAU, p = [r * Math.cos(s), 0, r * Math.sin(s)];
      // Rodrigues rotation of p about ax by ang
      const c = Math.cos(ang), sn = Math.sin(ang), dot = p[0] * ax[0] + p[2] * ax[2];
      const cr = [ax[1] * p[2] - ax[2] * p[1], ax[2] * p[0] - ax[0] * p[2], ax[0] * p[1] - ax[1] * p[0]];
      const q = [0, 1, 2].map((d) => p[d] * c + cr[d] * sn + ax[d] * dot * (1 - c));
      pts.push(project(C, X + q[0], cY + q[1], V + q[2]));
    }
    // split the ring into runs that lie behind / in front of the centre, so the sphere sits between them
    let run = [pts[0]], back = pts[0][3] >= cen[3];
    for (let i = 1; i <= 64; i++) {
      const b2 = (pts[i - 1][3] + pts[i][3]) / 2 >= cen[3];
      if (b2 !== back) { segs.push({ pts: run, back, j }); run = [pts[i - 1]]; back = b2; }
      run.push(pts[i]);
    }
    segs.push({ pts: run, back, j });
  });
  const draw = (list) => { for (const s of list) {
    const w = 14 * s.pts[0][2];
    const path = () => { ctx.beginPath(); s.pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); };
    path(); ctx.strokeStyle = B.DEEP; ctx.lineWidth = w + 3; ctx.stroke();
    ctx.strokeStyle = s.j === 1 ? B.BR : B.HI; ctx.lineWidth = w; ctx.stroke();
    ctx.strokeStyle = lib.rgba(B.DEEP, 0.55); ctx.lineWidth = 1; ctx.setLineDash([2, 7]); ctx.stroke(); ctx.setLineDash([]);   // engraved degree ticks
    ctx.strokeStyle = lib.rgba(B.SPEC, 0.75); ctx.lineWidth = w * 0.22; ctx.stroke(); } };
  ctx.save(); ctx.lineCap = "round"; ctx.lineJoin = "round";
  draw(segs.filter((s) => s.back));
  // pillar and sphere at the centre
  const base = project(C, X, H0, V);
  ctx.strokeStyle = B.DEEP; ctx.lineWidth = 10 * cen[2]; ctx.beginPath(); ctx.moveTo(base[0], base[1]); ctx.lineTo(cen[0], cen[1]); ctx.stroke();
  const sr = 40 * cen[2], sg = ctx.createRadialGradient(cen[0] - sr * 0.35, cen[1] - sr * 0.35, 1, cen[0], cen[1], sr);
  sg.addColorStop(0, B.SPEC); sg.addColorStop(0.4, B.HI); sg.addColorStop(1, B.DEEP);
  ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(cen[0], cen[1], sr, 0, lib.TAU); ctx.fill();
  draw(segs.filter((s) => !s.back));
  ctx.restore();
}

// storyboard: three hinged panels flip up from the cap and fan out (left, centre, right), engraved frames
function triptych(ctx, t, lib, B, C, X, H0, V) {
  const pw = 180, ph = 214;
  const parts = [[-1, 0.62], [0, 0], [1, -0.62]];
  const quads = parts.map(([side, beta], i) => {
    const u = lib.clamp(lib.spring(t - (T.panels[0] + i * 0.07), SPR.panel), 0, 1.2);
    const flip = (Math.PI / 2) * u;                                      // 0 = lying on the cap, 90° = standing
    const hx = side * 174, hv = side === 0 ? 18 : 60;                    // hinge line centre (relative)
    const local = (x, l) => { const lx = x, ly = l * Math.sin(flip), lz = -l * Math.cos(flip) + 0;   // extends away from camera when lying
      const cb = Math.cos(beta), sb = Math.sin(beta); return project(C, X + hx + lx * cb - lz * sb, H0 + 6 + ly, V + hv + lx * sb + lz * cb); };
    const pts = [local(-pw / 2, 0), local(pw / 2, 0), local(pw / 2, ph), local(-pw / 2, ph)];
    const fr = [local(-pw * 0.36, ph * 0.16), local(pw * 0.36, ph * 0.16), local(pw * 0.36, ph * 0.62), local(-pw * 0.36, ph * 0.62)];
    return { pts, fr, u, z: pts.reduce((s, p) => s + p[3], 0) / 4, i };
  }).sort((a, b) => b.z - a.z);
  ctx.save();
  for (const q of quads) {
    if (q.u <= 0.001) continue;
    const xs = q.pts.map((p) => p[0]), ys = q.pts.map((p) => p[1]);
    poly(ctx, q.pts); ctx.fillStyle = brassFill(ctx, B, Math.min(...xs), Math.min(...ys), Math.max(...xs), Math.max(...ys)); ctx.fill();
    ctx.strokeStyle = B.DEEP; ctx.lineWidth = 2; ctx.stroke();
    poly(ctx, q.fr); ctx.fillStyle = lib.rgba("#3E2F1B", 0.85); ctx.fill(); ctx.strokeStyle = lib.rgba(B.SPEC, 0.6); ctx.lineWidth = 1.2; ctx.stroke();
    ctx.fillStyle = B.DEEP; for (const p of [q.pts[0], q.pts[1]]) { ctx.beginPath(); ctx.arc(p[0], p[1], Math.max(2, 6 * p[2]), 0, lib.TAU); ctx.fill(); }
  }
  ctx.restore();
}

// draft: the mast shoots up, then the one vermilion pennant pops out and flutters
function pennant(ctx, t, lib, B, C, X, H0, V, RED) {
  const ms = lib.tween(t, T.flag - 0.06, T.flag + 0.04, lib.ease.outCubic);
  if (ms <= 0) return;
  const top = project(C, X, H0 + 290 * ms, V), base = project(C, X, H0, V), sc = top[2];
  ctx.save(); ctx.lineCap = "round";
  ctx.strokeStyle = B.DEEP; ctx.lineWidth = 12 * sc; ctx.beginPath(); ctx.moveTo(base[0], base[1]); ctx.lineTo(top[0], top[1]); ctx.stroke();
  ctx.strokeStyle = B.HI; ctx.lineWidth = 5 * sc; ctx.beginPath(); ctx.moveTo(base[0] - 2 * sc, base[1]); ctx.lineTo(top[0] - 2 * sc, top[1]); ctx.stroke();
  const s = lib.spring(t - (T.flag + 0.02), SPR.flag);
  if (s > 0) {
    const L1 = 255 * sc * s, hh = 126 * sc * Math.min(1, s), wave = Math.sin(t * 8.5) * 10 * sc;
    const x0 = top[0], y0 = top[1] + 8 * sc;
    ctx.fillStyle = RED; ctx.beginPath(); ctx.moveTo(x0, y0);
    ctx.bezierCurveTo(x0 + L1 * 0.35, y0 - 10 * sc + wave, x0 + L1 * 0.7, y0 + 10 * sc - wave, x0 + L1, y0 + hh * 0.5 + wave * 0.5);
    ctx.bezierCurveTo(x0 + L1 * 0.7, y0 + hh * 0.75 - wave, x0 + L1 * 0.35, y0 + hh + wave, x0, y0 + hh); ctx.closePath(); ctx.fill();
    ctx.strokeStyle = "rgba(60,12,8,0.55)"; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(x0 + L1 * 0.4, y0 + 4 * sc); ctx.quadraticCurveTo(x0 + L1 * 0.55, y0 + hh * 0.5, x0 + L1 * 0.45, y0 + hh - 6 * sc); ctx.stroke();
  }
  const fin = 14 * sc, fg = ctx.createRadialGradient(top[0] - fin * 0.3, top[1] - fin * 0.3, 1, top[0], top[1], fin);
  fg.addColorStop(0, B.SPEC); fg.addColorStop(1, B.MID); ctx.fillStyle = fg; ctx.beginPath(); ctx.arc(top[0], top[1], fin, 0, lib.TAU); ctx.fill();
  ctx.restore();
}

// engraved brass plate with the name: flips up when the tower locks; fades as the camera goes top-down
function plate(ctx, t, tokens, lib, C, k) {
  const P = (q) => lib.color(tokens, q), B = brass(P);
  const [X, V] = L.sites[k], t0 = T.lock(k);
  const topdown = lib.seg((C.th * 180) / Math.PI, 55, 80);
  const pf = lib.tween(t, t0, t0 + 0.2, lib.ease.outCubic) * (1 - topdown);
  if (pf <= 0) return;
  const base = project(C, X, 0, V), pwid = 256, ph = 112, px = base[0] - pwid / 2, py = base[1] + 42;
  ctx.save(); ctx.translate(0, py); ctx.scale(1, pf); ctx.translate(0, -py);
  ctx.fillStyle = "rgba(20,14,8,0.55)"; ctx.fillRect(px + 6, py + 7, pwid, ph);
  ctx.fillStyle = brassFill(ctx, B, px, py, px + pwid, py + ph); ctx.fillRect(px, py, pwid, ph);
  ctx.strokeStyle = lib.rgba(B.DEEP, 0.9); ctx.lineWidth = 2; ctx.strokeRect(px + 6, py + 6, pwid - 12, ph - 12);
  for (const [rx, ry] of [[px + 14, py + 14], [px + pwid - 14, py + 14], [px + 14, py + ph - 14], [px + pwid - 14, py + ph - 14]]) { ctx.fillStyle = B.DEEP; ctx.beginPath(); ctx.arc(rx, ry, 3.5, 0, lib.TAU); ctx.fill(); }
  ctx.fillStyle = B.INK;
  lib.setFont(ctx, tokens, "body", 30, { weight: 700 }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), base[0], py + 42, { align: "center", tracking: 0.12 * 30 });
  lib.setFont(ctx, tokens, "zh", 48, { weight: 700 }); lib.drawText(ctx, lib.MOTIF[k].zh, base[0], py + 96, { align: "center", tracking: 0.2 * 48 });
  ctx.restore();
}
