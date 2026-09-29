// clockwork-map swatch: one continuous low flight over a parchment map; brass mechanisms rise out of it.
// The ground is drawn "mode-7" style: under a pitched camera (no roll, no yaw) every screen row maps to one straight
// segment of the map texture, so each row is one drawImage from the right mip level. Pitch can go all the way to
// top-down with the same formula. Mechanisms use the same projection for their base and top.
//   0.0–0.8  the key light comes up on the map; the camera is already gliding (it never stops, never cuts)
//   0.8–2.4  title stamped letter by letter into the dark above the horizon; Chinese follows; a brass double rule
//   1.95–2.9 outline → storyboard → draft: a hatch opens, a brass tower lifts (easeInOutQuart), locks with a small
//            settle, its plate flips up; gears step like an escapement on every eighth note (90 BPM)
//   3.1–3.8  a vermilion route inks itself from site to site
//   4.0–4.8  pull-back: the camera rises and pitches to top-down; the whole map sits on the dark table

let L = null;
const MW = 3200, MH = 2600;
const BPM = 90, EIGHTH = 60 / BPM / 2;

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const LAND = lib.rgb(P("extra.0")), SEA = lib.rgb(P("extra.1")), INK = lib.rgb(P("extra.2"));
  // ── map texture (built once)
  const tex = document.createElement("canvas"); tex.width = MW; tex.height = MH;
  const x = tex.getContext("2d"), img = x.createImageData(MW, MH), d = img.data;
  const gw = 161, gh = 131, field = new Float32Array(gw * gh), blot = new Float32Array(gw * gh);
  for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
    const wx = i * 20, wy = j * 20;
    const cxd = (wx - 1600) / 1500, cyd = (wy - 1350) / 1250;
    field[j * gw + i] = lib.fbm2(wx / 900, wy / 900, { octaves: 5, seed: 42 }) * 0.85 + 0.22 - 0.35 * (cxd * cxd + cyd * cyd);
    blot[j * gw + i] = lib.fbm2(wx / 260, wy / 260, { octaves: 3, seed: 7 });
  }
  const bil = (F, u, v) => { const i = Math.min(gw - 2, Math.floor(u)), j = Math.min(gh - 2, Math.floor(v)), fu = u - i, fv = v - j, k = j * gw + i;
    return (F[k] * (1 - fu) + F[k + 1] * fu) * (1 - fv) + (F[k + gw] * (1 - fu) + F[k + gw + 1] * fu) * fv; };
  for (let py = 0; py < MH; py++) for (let px = 0; px < MW; px++) {
    const f = bil(field, px / 20, py / 20), b = bil(blot, px / 20, py / 20), o = (py * MW + px) * 4;
    const edge = Math.min(px, py, MW - px, MH - py), burn = lib.clamp(1 - edge / 140) ** 2;
    let c = f >= 0 ? LAND : SEA, m = 1 + 0.07 * b - 0.45 * burn;
    let r = c[0] * m, g = c[1] * m, bb = c[2] * m, inkA = 0;
    if (Math.abs(f) < 0.0065) inkA = 0.9;                                       // coastline
    else if (f < 0) for (let k = 1; k <= 3; k++) if (Math.abs(f + 0.028 * k) < 0.0032) inkA = Math.max(inkA, 0.55 / k);   // offshore echo lines
    if (inkA > 0) { r = lib.lerp(r, INK[0], inkA); g = lib.lerp(g, INK[1], inkA); bb = lib.lerp(bb, INK[2], inkA); }
    d[o] = r; d[o + 1] = g; d[o + 2] = bb; d[o + 3] = 255;
  }
  x.putImageData(img, 0, 0);
  // windrose bearing lines from two roses + one compass rose
  x.strokeStyle = lib.rgba(P("extra.2"), 0.32); x.lineWidth = 2.2;
  for (const [rx, ry] of [[1600, 900], [700, 1900]]) for (let k = 0; k < 16; k++) { const a = k / 16 * lib.TAU; x.beginPath(); x.moveTo(rx, ry); x.lineTo(rx + Math.cos(a) * 4000, ry + Math.sin(a) * 4000); x.stroke(); }
  const rose = (cx, cy, R) => { x.save(); x.translate(cx, cy);
    for (let k = 0; k < 8; k++) { const a = k / 8 * lib.TAU, r = k % 2 ? R * 0.55 : R; x.fillStyle = k % 2 ? lib.rgba(P("extra.2"), 0.5) : P("extra.2");
      x.beginPath(); x.moveTo(0, 0); x.lineTo(Math.cos(a - 0.2) * r * 0.25, Math.sin(a - 0.2) * r * 0.25); x.lineTo(Math.cos(a) * r, Math.sin(a) * r); x.lineTo(Math.cos(a + 0.2) * r * 0.25, Math.sin(a + 0.2) * r * 0.25); x.closePath(); x.fill(); }
    x.strokeStyle = P("extra.2"); x.lineWidth = 3; x.beginPath(); x.arc(0, 0, R * 0.72, 0, lib.TAU); x.stroke(); x.restore(); };
  rose(700, 1900, 170); rose(2650, 520, 110);
  const mip = (src, s) => { const c = document.createElement("canvas"); c.width = src.width / s; c.height = src.height / s; const q = c.getContext("2d"); q.imageSmoothingQuality = "high"; q.drawImage(src, 0, 0, c.width, c.height); return c; };
  const tex2 = mip(tex, 2), tex4 = mip(tex2, 2);
  L = { tex, tex2, tex4 };
  // ── sites: back-project the desired poster-frame positions (t = 3.0) onto the map
  const C3 = camera(3.0, lib);
  L.sites = [[448, 742], [960, 722], [1472, 736]].map(([sx, sy]) => ground(C3, sx, sy));
}

// camera: pitch th, height h, focal f, principal point (960, cy); positioned so the ground point T maps to screen yT
function camera(t, lib) {
  const u = lib.tween(t, 4.0, 4.8, lib.ease.inOutCubic);
  const th = lib.lerp(22, 90, u) * Math.PI / 180, h = lib.lerp(500, 3095, u), f = 1000, cy = lib.lerp(844, 540, u), yT = lib.lerp(740, 540, u);
  const TX = lib.lerp(1600 + 28 * (t - 3), 1600, u), TV = lib.lerp(1330 + 42 * (3 - t), 1486, u);
  const vs = (yT - cy) / f, s = h / (Math.sin(th) + vs * Math.cos(th)), dT = s * (Math.cos(th) - vs * Math.sin(th));
  return { th, h, f, cy, cx: 960, X: TX, Z: TV + dT, sn: Math.sin(th), cs: Math.cos(th) };
}
function ground(C, sx, sy) {                     // screen → map (X, V)
  const vs = (sy - C.cy) / C.f, s = C.h / (C.sn + vs * C.cs);
  return [C.X + s * (sx - C.cx) / C.f, C.Z - s * (C.cs - vs * C.sn)];
}
function project(C, X, Y, V) {                   // map point (X, height Y, V) → screen [x, y, pixels per unit]
  const dx = X - C.X, dy = Y - C.h, dz = C.Z - V;
  const zc = -dy * C.sn + dz * C.cs, yc = -dy * C.cs - dz * C.sn;
  return [C.cx + C.f * dx / zc, C.cy + C.f * yc / zc, C.f / zc];
}
function escapement(t, phase = 0, teeth = 12) {  // one tooth per eighth note: 4 frames of ease-out, then hold
  const b = t / EIGHTH + phase, k = Math.floor(b), fr = Math.min(1, (b - k) * EIGHTH * 30 / 4);
  return (k + (1 - (1 - fr) ** 3)) * Math.PI * 2 / teeth;
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const C = camera(t, lib);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  // ── ground, row by row
  const light = lib.tween(t, 0.0, 0.7, lib.ease.outCubic);
  ctx.save(); ctx.globalAlpha = 0.25 + 0.75 * light; ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
  let horizon = -1;
  for (let y = 0; y < H; y++) {
    const vs = (y + 0.5 - C.cy) / C.f, den = C.sn + vs * C.cs;
    if (den <= 0.002) { horizon = y; continue; }
    const s = C.h / den, V = C.Z - s * (C.cs - vs * C.sn);
    const u0 = C.X + s * (0 - C.cx) / C.f, u1 = C.X + s * (W - C.cx) / C.f, ratio = (u1 - u0) / W;
    const vs2 = (y + 1.5 - C.cy) / C.f, V2 = C.Z - (C.h / (C.sn + vs2 * C.cs)) * (C.cs - vs2 * C.sn), sh = Math.max(0.5, Math.abs(V2 - V));
    const [src, k] = ratio > 3.5 ? [L.tex4, 4] : ratio > 1.6 ? [L.tex2, 2] : [L.tex, 1];
    const sx0 = Math.max(0, u0), sx1 = Math.min(MW, u1), sv = V - sh / 2;
    if (sx1 <= sx0 || sv > MH || sv + sh < 0) continue;
    const dx0 = (sx0 - u0) / (u1 - u0) * W, dx1 = (sx1 - u0) / (u1 - u0) * W;
    ctx.drawImage(src, sx0 / k, Math.max(0, sv) / k, (sx1 - sx0) / k, Math.max(0.5, sh) / k, dx0, y, dx1 - dx0, 1.02);
  }
  ctx.restore();
  // ── light: one warm key from the map centre, falloff to the edges; haze toward the horizon
  const lc = project(C, 1600, 0, 1250);
  ctx.save(); const g = ctx.createRadialGradient(lc[0], Math.min(H, lc[1]), 80, lc[0], Math.min(H, lc[1]), 1300);
  g.addColorStop(0, "rgba(255,210,140,0.10)"); g.addColorStop(0.55, "rgba(22,18,13,0)"); g.addColorStop(1, "rgba(22,18,13,0.55)");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  if (horizon > -1) { const hz = ctx.createLinearGradient(0, horizon, 0, horizon + 320); hz.addColorStop(0, P("bg")); hz.addColorStop(1, lib.rgba(P("bg"), 0)); ctx.fillStyle = hz; ctx.fillRect(0, horizon, W, 320); }
  ctx.restore();

  // ── route (vermilion ink) drawn on the ground from site to site
  const ru = lib.tween(t, 3.1, 3.8, lib.ease.inOutSine);
  if (ru > 0) {
    const pts = [];
    for (let i = 0; i <= 60; i++) {
      const q = i / 60, seg = Math.min(1, Math.floor(q * 2)), w = q * 2 - seg, A = L.sites[seg], B = L.sites[seg + 1];
      const mx = (A[0] + B[0]) / 2, mv = (A[1] + B[1]) / 2 + 220;             // a bowed bearing between sites
      const X = (1 - w) ** 2 * A[0] + 2 * (1 - w) * w * mx + w * w * B[0], V = (1 - w) ** 2 * A[1] + 2 * (1 - w) * w * mv + w * w * B[1];
      pts.push(project(C, X, 0, V));
    }
    ctx.save(); ctx.strokeStyle = P("accent"); ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.setLineDash([22, 14]);
    ctx.lineWidth = Math.max(2.5, 14 * pts[30][2]); lib.strokePartial(ctx, pts.map((p) => [p[0], p[1]]), ru); ctx.restore();
  }

  // ── mechanisms, far to near
  const order = [0, 1, 2].sort((a, b) => L.sites[a][1] - L.sites[b][1]);
  for (const k of order) mechanism(ctx, t, tokens, lib, C, k);

  // ── title, stamped into the dark above the horizon
  const out = lib.tween(t, 4.0, 4.3, lib.ease.inCubic);
  ctx.save(); ctx.globalAlpha = 1 - out;
  lib.setFont(ctx, tokens, "display", 100, { weight: 600 });
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: W / 2, y: 206, align: "center", tracking: 0.04 * 100 });
  const fg = lib.rgb(P("fg"));
  lib.drawGlyphs(ctx, lay, (gl, i) => {
    const a = lib.seg(t, 0.86 + i * 0.06, 1.0 + i * 0.06);
    if (a <= 0) return null;
    const c = [255, 241, 200].map((v, j) => Math.round(lib.lerp(v, fg[j], a)));
    return { scale: 1.12 - 0.12 * lib.ease.outCubic(a), fill: `rgb(${c.join(",")})` };
  });
  lib.setFont(ctx, tokens, "zh", 62, { weight: 700 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 300, align: "center", tracking: 0.1 * 62 });
  lib.drawGlyphs(ctx, zl, (gl, i) => {
    const a = lib.seg(t, 1.5 + i * 0.09, 1.65 + i * 0.09);
    if (a <= 0) return null;
    const c = [255, 241, 200].map((v, j) => Math.round(lib.lerp(v, fg[j], a)));
    return { scale: 1.12 - 0.12 * lib.ease.outCubic(a), fill: `rgb(${c.join(",")})` };
  });
  ctx.strokeStyle = P("extra.3"); ctx.lineWidth = 2;
  const ru2 = lib.tween(t, 1.9, 2.4, lib.ease.outCubic);
  if (ru2 > 0) for (const yy of [336, 343]) lib.strokePartial(ctx, [[W / 2 - 360 * ru2, yy], [W / 2 + 360 * ru2, yy]], 1);
  ctx.restore();

  // ── end: name under the top-down map
  const ea = lib.tween(t, 4.55, 4.85, lib.ease.outCubic);
  if (ea > 0) {
    ctx.save(); ctx.globalAlpha = ea; ctx.fillStyle = P("fg");
    lib.setFont(ctx, tokens, "display", 60, { weight: 600 }); lib.drawText(ctx, "Clockwork Map", W / 2 - 20, 1000, { align: "right", tracking: 0.04 * 60 });
    lib.setFont(ctx, tokens, "zh", 50, { weight: 700 }); lib.drawText(ctx, "机械钟表地图", W / 2 + 20, 998, { tracking: 0.1 * 50 });
    ctx.restore();
  }
  lib.grain(ctx, t, { amount: 0.04, fps: 12, seed: 5 });
}

function gear(ctx, lib, cx, cy, R, teeth, ang, col, dark) {
  ctx.save(); ctx.translate(cx, cy); ctx.rotate(ang);
  ctx.fillStyle = col; ctx.beginPath();
  for (let i = 0; i < teeth * 2; i++) { const a0 = (i / (teeth * 2)) * lib.TAU, a1 = ((i + 1) / (teeth * 2)) * lib.TAU, r = i % 2 ? R * 0.8 : R;
    ctx.lineTo(Math.cos(a0 + 0.06) * r, Math.sin(a0 + 0.06) * r); ctx.lineTo(Math.cos(a1 - 0.06) * r, Math.sin(a1 - 0.06) * r); }
  ctx.closePath(); ctx.fill();
  ctx.fillStyle = dark; ctx.beginPath(); ctx.arc(0, 0, R * 0.28, 0, lib.TAU); ctx.fill();
  ctx.strokeStyle = dark; ctx.lineWidth = Math.max(1, R * 0.08); for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(0, 0); const a = i * Math.PI / 2; ctx.lineTo(Math.cos(a) * R * 0.7, Math.sin(a) * R * 0.7); ctx.stroke(); }
  ctx.restore();
}

function mechanism(ctx, t, tokens, lib, C, k) {
  const P = (q) => lib.color(tokens, q);
  const BR = P("extra.3"), HI = P("extra.4"), SHD = P("extra.5"), INK = P("extra.2");
  const [X, V] = L.sites[k], t0 = 1.95 + k * 0.22;
  if (t < t0) return;
  const hatch = lib.tween(t, t0, t0 + 0.14, lib.ease.outCubic);
  const rise = lib.tween(t, t0 + 0.08, t0 + 0.53, lib.easeOf(tokens.ease.enter));
  const settle = t > t0 + 0.53 ? lib.spring(t - (t0 + 0.53), tokens.ease.spring) : 1;          // ζ≈0.8: ~1.5 % settle
  const Hmax = [300, 270, 320][k], Wd = 200, hgt = Hmax * rise * (t > t0 + 0.53 ? settle : 1);
  const base = project(C, X, 0, V), top = project(C, X, hgt, V), sc = base[2], w = Wd * sc;
  const flat = C.sn;                                                                              // ellipse squash from pitch
  const eh = Math.max(2, w / 2 * Math.cos(C.th) * 0.9 + 1);
  const topdown = lib.seg(C.th * 180 / Math.PI, 60, 85);
  // hatch (dark opening in the map)
  ctx.save(); ctx.fillStyle = "rgba(20,14,8,0.85)"; ctx.beginPath(); ctx.ellipse(base[0], base[1], w * 0.62 * hatch, eh * 1.25 * hatch, 0, 0, lib.TAU); ctx.fill();
  // shadow cast forward-right by the key light
  if (hgt > 1) { ctx.fillStyle = "rgba(20,14,8,0.35)"; ctx.beginPath(); ctx.ellipse(base[0] + w * 0.5, base[1] + eh * 0.6, w * 0.55 + (base[1] - top[1]) * 0.18, eh * 1.1, 0.12, 0, lib.TAU); ctx.fill(); }
  // body: three-band brass (lit left, body, shadow right)
  const x0 = base[0] - w / 2, yTop = top[1], yBase = base[1];
  if (yBase - yTop > 1) {
    const gr = ctx.createLinearGradient(x0, 0, x0 + w, 0);
    gr.addColorStop(0, BR); gr.addColorStop(0.1, HI); gr.addColorStop(0.2, HI); gr.addColorStop(0.3, BR); gr.addColorStop(0.58, BR); gr.addColorStop(0.6, "#8A6A3C"); gr.addColorStop(0.78, "#8A6A3C"); gr.addColorStop(0.8, SHD); gr.addColorStop(1, SHD);
    ctx.fillStyle = gr; ctx.fillRect(x0, yTop, w, yBase - yTop);
    ctx.beginPath(); ctx.ellipse(base[0], yBase, w / 2, eh, 0, 0, Math.PI); ctx.fill();
    ctx.strokeStyle = lib.rgba(INK, 0.7); ctx.lineWidth = Math.max(1, 2.5 * sc);
    ctx.beginPath(); ctx.moveTo(x0, yTop); ctx.lineTo(x0, yBase); ctx.ellipse(base[0], yBase, w / 2, eh, 0, Math.PI, 0, true); ctx.lineTo(x0 + w, yTop); ctx.stroke();
    // riveted bands
    ctx.strokeStyle = lib.rgba(SHD, 0.8); ctx.lineWidth = Math.max(1, 3 * sc);
    for (const f of [0.18, 0.86]) { const yy = yTop + (yBase - yTop) * f; ctx.beginPath(); ctx.ellipse(base[0], yy, w / 2, eh, 0, 0, Math.PI); ctx.stroke(); }
    // escapement gear on the face + meshing pinion (opposite direction)
    const R = w * 0.3, gy = yTop + (yBase - yTop) * 0.52;
    if (yBase - yTop > R * 2.4) {
      const a = escapement(t, k * 0.37);
      gear(ctx, lib, base[0] - w * 0.08, gy, R, 12, a, HI, SHD);
      gear(ctx, lib, base[0] - w * 0.08 + R * 1.62, gy - R * 0.55, R * 0.62, 8, -a * 12 / 8 + Math.PI / 8, BR, SHD);
    }
  }
  // cap
  ctx.fillStyle = HI; ctx.beginPath(); ctx.ellipse(base[0], yTop, w / 2, eh, 0, 0, lib.TAU); ctx.fill();
  ctx.strokeStyle = SHD; ctx.lineWidth = Math.max(1, 3 * sc); ctx.stroke();
  // motif-specific tops
  const open = lib.tween(t, t0 + 0.45, t0 + 0.75, lib.easeOf(tokens.ease.enter));
  if (k === 0 && open > 0) {                         // outline: three stacked rings (the three bullet lines)
    for (let r = 0; r < 3; r++) { const yy = yTop - (18 + r * 22) * sc * open; ctx.fillStyle = r % 2 ? BR : HI; ctx.beginPath(); ctx.ellipse(base[0], yy, w * (0.46 - r * 0.08), eh * 0.8, 0, 0, lib.TAU); ctx.fill(); ctx.strokeStyle = SHD; ctx.lineWidth = Math.max(1, 2 * sc); ctx.stroke(); }
  }
  if (k === 1 && open > 0) {                         // storyboard: three hinged panels unfold into a triptych
    const pw = w * 0.56, ph = w * 0.7;
    [-1, 1, 0].forEach((s, i) => {
      const u = lib.clamp(open * 1.4 - i * 0.2), ang = s * 0.78 * u;
      ctx.save(); ctx.translate(base[0], yTop - 4 * sc); ctx.rotate(ang);
      ctx.fillStyle = i === 1 ? HI : BR; ctx.fillRect(-pw / 2, -ph * u - 2, pw, ph * u);
      ctx.strokeStyle = SHD; ctx.lineWidth = Math.max(1, 2.5 * sc); ctx.strokeRect(-pw / 2, -ph * u - 2, pw, ph * u);
      if (u > 0.6) { ctx.strokeStyle = lib.rgba(INK, 0.8); ctx.lineWidth = Math.max(1, 2 * sc); ctx.strokeRect(-pw / 2 + pw * 0.14, -ph * u + ph * 0.14, pw * 0.72, ph * 0.5); }
      ctx.restore();
    });
  }
  if (k === 2 && open > 0) {                         // draft: a mast with the one vermilion pennant
    const mh = 120 * sc * open, mx = base[0];
    ctx.strokeStyle = SHD; ctx.lineWidth = Math.max(1.5, 6 * sc); ctx.beginPath(); ctx.moveTo(mx, yTop); ctx.lineTo(mx, yTop - mh); ctx.stroke();
    const wave = Math.sin(t * 9) * 6 * sc;
    ctx.fillStyle = P("accent"); ctx.beginPath(); ctx.moveTo(mx, yTop - mh); ctx.quadraticCurveTo(mx + 50 * sc, yTop - mh + 12 * sc + wave, mx + 96 * sc * open, yTop - mh + 22 * sc); ctx.lineTo(mx, yTop - mh + 44 * sc); ctx.closePath(); ctx.fill();
  }
  ctx.restore();
  // brass plate with the engraved name: flips up when the mechanism locks; fades as the camera goes top-down
  const pf = lib.tween(t, t0 + 0.5, t0 + 0.72, lib.ease.outCubic) * (1 - topdown);
  if (pf > 0) {
    const pwid = 250, ph = 112, px = base[0] - pwid / 2, py = base[1] + 30;
    ctx.save(); ctx.translate(0, py); ctx.scale(1, pf); ctx.translate(0, -py);
    ctx.fillStyle = "rgba(20,14,8,0.55)"; ctx.fillRect(px + 5, py + 6, pwid, ph);
    ctx.fillStyle = BR; ctx.fillRect(px, py, pwid, ph); ctx.strokeStyle = HI; ctx.lineWidth = 2; ctx.strokeRect(px + 5, py + 5, pwid - 10, ph - 10);
    ctx.fillStyle = INK;
    lib.setFont(ctx, tokens, "body", 30, { weight: 700 }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), base[0], py + 42, { align: "center", tracking: 0.12 * 30 });
    lib.setFont(ctx, tokens, "zh", 48, { weight: 700 }); lib.drawText(ctx, lib.MOTIF[k].zh, base[0], py + 96, { align: "center", tracking: 0.2 * 48 });
    ctx.restore();
  }
  // top-down marker: a brass ring (+ vermilion for the current site)
  if (topdown > 0) {
    ctx.save(); ctx.globalAlpha = topdown; ctx.fillStyle = k === 2 ? P("accent") : BR; ctx.strokeStyle = INK; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(base[0], base[1], 14, 0, lib.TAU); ctx.fill(); ctx.stroke(); ctx.restore();
  }
}
