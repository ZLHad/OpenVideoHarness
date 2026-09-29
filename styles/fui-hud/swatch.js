// fui-hud swatch — a fictional film interface where every readout is real: this frame's index, t, the swatch's own
// content spec, and the times at which each stage boots.
//   0.0–0.8  the FRAME counter runs big in the centre of the dot grid from frame 1; at 0.65–0.95 s it flies to its
//            corner panel and the panel frame draws around it
//   0.8–2.6  the title decodes left → right (≤ 9 frames per glyph), then the Chinese line; a scan line reveals the
//            spec schematic (four Gantt bars: establish / title / motif / outro) with the playhead at t
//   2.0–4.0  a trajectory schematic: three waypoints boot on 2.0 / 2.2 / 2.4 s (circle drawn, then data), each with a
//            wireframe icon and its real boot time; the orange brackets — the one alert colour — lock onto the draft
//            waypoint (blink twice at 2 Hz, music drops to the drone); scan sweeps at 2.8 and 3.2; the marker locks
//            on at 3.6
//   4.0–5.0  the draft waypoint's bracket box expands to the full frame and becomes the end card
// Depth: a slow camera drift with the dot grid at 0.9×, the HUD at 1.0× and a faint reticle foreground at 1.1×.
// Numbers are Menlo (SF Mono is not a registered system font on this machine) with tabular figures.

const G = 24;
let L = null;
export const fonts = ["DIN Condensed", "Menlo", "PingFang SC"];

export async function setup(ctx, tokens, lib) {
  const dots = document.createElement("canvas"); dots.width = G; dots.height = G;
  const d = dots.getContext("2d"); d.fillStyle = lib.color(tokens, "extra.1"); d.beginPath(); d.arc(G / 2, G / 2, 1.3, 0, lib.TAU); d.fill();
  const path = []; for (let i = 0; i <= 80; i++) { const u = i / 80; path.push([lib.lerp(200, 1720, u), 846 - Math.sin(u * Math.PI) * 70 + Math.sin(u * 9) * 6]); }
  const at = (u) => path[Math.round(u * 80)];
  L = { dots, readout: { x: 56 * G, y: 5 * G, w: 19 * G, h: 10 * G }, path, wps: [0.09, 0.5, 0.91].map((u) => ({ u, p: at(u) })) };
}
const C = (lib, tokens, k) => lib.color(tokens, k);
const drift = (t) => -22 * t / 5;                            // slow camera drift (px) for parallax

function brackets(ctx, lib, tokens, b, pad = 10, k = 26) {
  const o = C(lib, tokens, "accent");
  ctx.save(); ctx.strokeStyle = o; ctx.lineWidth = 3; ctx.shadowColor = o; ctx.shadowBlur = 14;
  for (const [sx, sy] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
    const x = b.x - pad + sx * (b.w + 2 * pad), y = b.y - pad + sy * (b.h + 2 * pad), dx = sx ? -k : k, dy = sy ? -k : k;
    ctx.beginPath(); ctx.moveTo(x + dx, y); ctx.lineTo(x, y); ctx.lineTo(x, y + dy); ctx.stroke();
  }
  ctx.restore();
}

// ───────── layers ─────────
function frameCounter(ctx, t, tokens, lib) {
  const f = lib.frame(t), fg = C(lib, tokens, "fg"), dim = C(lib, tokens, "extra.0"), R = L.readout;
  const fly = lib.easeOf(tokens.ease.enter)(lib.seg(t, 0.65, 0.95));
  const big = { x: 960, y: 560, s: 2.1 }, small = { x: R.x + 26 + 160, y: R.y + 186, s: 1 };
  const cx = lib.lerp(big.x, small.x, fly), cy = lib.lerp(big.y, small.y, fly), s = lib.lerp(big.s, small.s, fly);
  if (t >= 1 / 30) {
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s, s);
    lib.setFont(ctx, tokens, "mono", 150, { weight: 400 }); ctx.fillStyle = fg;
    lib.drawText(ctx, String(f).padStart(3, "0"), -160, 0);
    ctx.restore();
  }
  // the panel frame draws around it once it has landed
  const u = lib.clamp((f - 27) / 6); if (u <= 0) return;
  ctx.save(); ctx.strokeStyle = lib.rgba(fg, 0.55); ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(R.x, R.y + R.h * u); ctx.lineTo(R.x, R.y); ctx.lineTo(R.x + R.w * u, R.y);
  if (u >= 1) { ctx.lineTo(R.x + R.w, R.y + R.h); ctx.lineTo(R.x, R.y + R.h); ctx.closePath(); } ctx.stroke();
  const a = lib.clamp((f - 33) / 4);
  if (a > 0) {
    ctx.globalAlpha = a; ctx.fillStyle = dim; lib.setFont(ctx, tokens, "display", 32, { weight: 700 });
    lib.drawText(ctx, "FRAME", R.x + 30, R.y + 50, { tracking: 32 * 0.14 }); lib.drawText(ctx, "30 FPS", R.x + R.w - 30, R.y + 50, { align: "right", tracking: 32 * 0.14 });
    lib.setFont(ctx, tokens, "mono", 30); lib.drawText(ctx, `t ${t.toFixed(2)} s  / 5.00`, R.x + 30, R.y + 222);
  }
  ctx.restore();
}
function specSchematic(ctx, t, tokens, lib) {              // the swatch's own content spec as a Gantt, playhead = t
  const fg = C(lib, tokens, "fg"), dim = C(lib, tokens, "extra.0"), y0 = 19 * G, x0 = 6 * G, x1 = 74 * G, X = (s) => lib.lerp(x0, x1, s / 5);
  const scan = lib.lerp(x0 - 60, x1 + 60, lib.seg(t, 0.3, 1.1)); if (t < 0.3) return;
  const S = lib.SPEC, rows = [["ESTABLISH", S.establish], ["TITLE", S.title], ["MOTIF", S.motif], ["OUTRO", S.outro]];
  ctx.save();
  rows.forEach(([name, [a, b]], i) => {
    const y = y0 + i * 16, xa = X(a), xb = Math.min(X(b), scan); if (xb <= xa) return;
    const on = t >= a && t < b;
    ctx.fillStyle = on ? lib.rgba(fg, 0.8) : lib.rgba(fg, 0.25); ctx.fillRect(xa, y, xb - xa, 6);
  });
  ctx.fillStyle = lib.rgba(fg, 0.5);
  for (let s = 0; s <= 50; s++) { const x = X(s / 10); if (x > scan) break; const major = s % 10 === 0; ctx.fillRect(x, y0 + 70, 1.5, major ? 14 : 6); if (major) { lib.setFont(ctx, tokens, "mono", 22); ctx.fillStyle = dim; lib.drawText(ctx, `${s / 10}s`, x + 5, y0 + 104); ctx.fillStyle = lib.rgba(fg, 0.5); } }
  if (scan < x1 + 60) { ctx.fillStyle = lib.rgba(fg, 0.85); ctx.fillRect(scan, y0 - 20, 2, 110); }
  const px = X(t); if (scan > px) { ctx.fillStyle = fg; ctx.fillRect(px - 1, y0 - 14, 2, 100); ctx.beginPath(); ctx.moveTo(px - 8, y0 - 22); ctx.lineTo(px + 8, y0 - 22); ctx.lineTo(px, y0 - 12); ctx.closePath(); ctx.fill(); }
  ctx.restore();
}
function trajectory(ctx, t, tokens, lib) {
  const f = lib.frame(t), fg = C(lib, tokens, "fg"), dim = C(lib, tokens, "extra.0"), acc = C(lib, tokens, "accent");
  const pu = lib.clamp((f - 57) / 8); if (pu <= 0) return;
  // the path (linear draw), then waypoints boot on 2.0 / 2.2 / 2.4 s
  ctx.save(); ctx.strokeStyle = lib.rgba(fg, 0.45); ctx.lineWidth = 1.5; ctx.setLineDash([10, 8]); lib.strokePartial(ctx, L.path, pu); ctx.setLineDash([]); ctx.restore();
  const sweeps = [2.8, 3.2].map((ts) => lib.seg(t, ts, ts + 0.18));
  L.wps.forEach((w, k) => {
    const f0 = 60 + k * 6, u = lib.clamp((f - f0) / 6), a = lib.clamp((f - f0 - 6) / 4); if (u <= 0) return;
    const [x, y] = w.p;
    const lit = sweeps.reduce((m, s) => Math.max(m, s > 0 && s < 1 ? 1 - Math.abs(s - (x - 200) / 1520) * 4 : 0), 0);   // scan line passing
    ctx.save(); ctx.strokeStyle = lib.rgba(fg, 0.6 + 0.4 * Math.max(0, lit)); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(x, y, 34, -Math.PI / 2, -Math.PI / 2 + lib.TAU * u); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x - 46, y); ctx.lineTo(x - 22, y); ctx.moveTo(x + 22, y); ctx.lineTo(x + 46, y); ctx.moveTo(x, y - 46); ctx.lineTo(x, y - 22); ctx.moveTo(x, y + 22); ctx.lineTo(x, y + 46); ctx.stroke();
    if (a > 0) {
      ctx.globalAlpha = a;
      // wireframe icon above the waypoint (no play button: the draft is a rendered film frame)
      const ix = x - 60, iy = y - 128; ctx.strokeStyle = lib.rgba(fg, 0.75); ctx.lineWidth = 1.5; ctx.beginPath();
      if (k === 0) for (let j = 0; j < 3; j++) { ctx.moveTo(ix, iy + 14 + j * 24); ctx.lineTo(ix + (j === 2 ? 70 : 120), iy + 14 + j * 24); }
      else if (k === 1) for (let j = 0; j < 3; j++) ctx.rect(ix + j * 42, iy, 34, 70);
      else { ctx.rect(ix, iy, 120, 70); for (let j = 0; j < 5; j++) { ctx.rect(ix + 6 + j * 23, iy + 4, 10, 6); ctx.rect(ix + 6 + j * 23, iy + 60, 10, 6); } ctx.moveTo(ix + 20, iy + 55); ctx.lineTo(ix + 50, iy + 28); ctx.lineTo(ix + 70, iy + 44); ctx.lineTo(ix + 100, iy + 18); }
      ctx.stroke();
      // label and its real boot time
      ctx.fillStyle = fg; lib.setFont(ctx, tokens, "display", 44, { weight: 700 });
      lib.drawText(ctx, `0${k + 1} ${lib.MOTIF[k].en.toUpperCase()}`, x, y + 92, { align: "center", tracking: 44 * 0.08 });
      lib.setFont(ctx, tokens, "zh", 50, { weight: 500 }); lib.drawText(ctx, lib.MOTIF[k].zh, x, y + 152, { align: "center", tracking: 6 });
      lib.setFont(ctx, tokens, "mono", 26); ctx.fillStyle = dim;
      const jit = lit > 0.2 ? lib.hash(k, f) * 9 | 0 : 0;                          // readouts flicker while scanned
      lib.drawText(ctx, `T+${(f0 / 30).toFixed(2)}s  f ${String(f0).padStart(3, "0")}${jit ? " ·" + jit : ""}`, k === 2 ? x - 50 : x + 50, y - 12, { align: k === 2 ? "right" : "left" });
    }
    ctx.restore();
  });
  // the marker travels the path with t (2.0 → 3.6 s) and locks on the draft
  const mu = lib.ease.inOutCubic(lib.seg(t, 2.0, 3.6)), mp = L.path[Math.round(lib.lerp(L.wps[0].u, L.wps[2].u, mu) * 80)];
  if (t >= 2.0) { ctx.save(); ctx.fillStyle = fg; ctx.beginPath(); ctx.moveTo(mp[0], mp[1] - 12); ctx.lineTo(mp[0] + 9, mp[1]); ctx.lineTo(mp[0], mp[1] + 12); ctx.lineTo(mp[0] - 9, mp[1]); ctx.closePath(); ctx.fill(); ctx.restore(); }
  // alert: brackets blink twice at 2 Hz from 2.4 s, stay on from 2.9 s, flash on the lock at 3.6 s
  const on = (t >= 2.4 && t < 2.53) || (t >= 2.66 && t < 2.79) || t >= 2.9;
  if (on) {
    const [x, y] = L.wps[2].p, lock = Math.exp(-Math.pow((t - 3.65) / 0.08, 2));
    ctx.save(); ctx.globalAlpha = 0.85 + 0.15 * lock; brackets(ctx, lib, tokens, { x: x - 150, y: y - 150, w: 300, h: 330 }, 6 + 10 * lock); ctx.restore();
    if (t >= 3.6) { ctx.save(); ctx.fillStyle = acc; lib.setFont(ctx, tokens, "mono", 26); lib.drawText(ctx, "LOCK", x + 110, y - 164); ctx.restore(); }
  }
  // scan sweeps (2.8 and 3.2): a bright vertical line crosses the schematic in 0.25 s
  sweeps.forEach((s) => { if (s <= 0 || s >= 1) return; const sx = lib.lerp(160, 1760, s); ctx.save(); ctx.fillStyle = lib.rgba(fg, 0.7); ctx.shadowColor = fg; ctx.shadowBlur = 16; ctx.fillRect(sx, 600, 2, 420); ctx.restore(); });
}
function title(ctx, t, tokens, lib) {
  const fg = C(lib, tokens, "fg");
  lib.setFont(ctx, tokens, "display", 132, { weight: 700 }); ctx.fillStyle = fg;
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: 6 * G, y: 11 * G, tracking: 2 });
  const sg = lib.scrambleGlyphs(lib.TITLE_EN, t, { start: 0.85, stagger: 0.03, settle: 0.3, rate: 15, seed: 3 });
  lib.drawGlyphs(ctx, lay, (g, i) => sg[i].state === "hidden" ? null : { ch: sg[i].ch, alpha: sg[i].state === "done" ? 1 : 0.6 });
  lib.setFont(ctx, tokens, "zh", 64, { weight: 500 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: 6 * G, y: 15 * G + 6, tracking: 6 });
  const zg = lib.scrambleGlyphs(lib.TITLE_ZH, t, { start: 1.3, stagger: 0.06, settle: 0.3, rate: 15, seed: 5 });
  lib.drawGlyphs(ctx, zl, (g, i) => zg[i].state === "hidden" ? null : { ch: zg[i].ch, alpha: zg[i].state === "done" ? 1 : 0.55 });
}
function foreground(ctx, t, tokens, lib) {                  // faint reticle glass nearer the lens (1.1× parallax, soft)
  const fg = C(lib, tokens, "fg"), [x, y] = L.wps[2].p, a = lib.clamp((lib.frame(t) - 4) / 10);
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = 0.14 * a; ctx.strokeStyle = fg; ctx.lineWidth = 3; ctx.filter = "blur(1.6px)";
  ctx.beginPath(); ctx.arc(x + 40, y - 40, 420, Math.PI * 0.95, Math.PI * 1.6); ctx.stroke();
  ctx.beginPath(); ctx.arc(x + 40, y - 40, 470, Math.PI * 1.0, Math.PI * 1.45); ctx.stroke();
  for (let k = 0; k < 14; k++) { const ang = Math.PI * (1.0 + k * 0.04), r0 = 470, r1 = k % 3 ? 486 : 500; ctx.beginPath(); ctx.moveTo(x + 40 + Math.cos(ang) * r0, y - 40 + Math.sin(ang) * r0); ctx.lineTo(x + 40 + Math.cos(ang) * r1, y - 40 + Math.sin(ang) * r1); ctx.stroke(); }
  ctx.restore();
}

function hud(ctx, t, tokens, lib, { fade = 1 } = {}) {
  const dx = drift(t);
  ctx.save(); ctx.globalAlpha = fade; ctx.translate(dx, 0);
  specSchematic(ctx, t, tokens, lib);
  title(ctx, t, tokens, lib);
  trajectory(ctx, t, tokens, lib);
  frameCounter(ctx, t, tokens, lib);
  ctx.restore();
  ctx.save(); ctx.globalAlpha = fade; ctx.translate(dx * 1.1 + 12, 0); foreground(ctx, t, tokens, lib); ctx.restore();
}

function endCard(ctx, t, tokens, lib, p) {
  const fg = C(lib, tokens, "fg"), dim = C(lib, tokens, "extra.0");
  ctx.save(); ctx.strokeStyle = lib.rgba(fg, 0.55); ctx.lineWidth = 1.5; ctx.strokeRect(p.x, p.y, p.w, p.h); ctx.restore();
  brackets(ctx, lib, tokens, p, -6);
  if (t < 4.36) return;
  const { W } = lib;
  lib.setFont(ctx, tokens, "display", 150, { weight: 700 }); ctx.fillStyle = fg;
  const name = "FUI / HUD", lay = lib.layoutText(ctx, name, { x: W / 2, y: 560, align: "center", tracking: 150 * 0.06 });
  const sg = lib.scrambleGlyphs(name, t, { start: 4.36, stagger: 0.025, settle: 0.25, rate: 15, seed: 9 });
  lib.drawGlyphs(ctx, lay, (g, i) => sg[i].state === "hidden" ? null : { ch: sg[i].ch, alpha: sg[i].state === "done" ? 1 : 0.6 });
  if (t >= 4.55) {
    lib.setFont(ctx, tokens, "zh", 56, { weight: 500 }); lib.drawText(ctx, "电影界面 HUD", W / 2, 660, { align: "center", tracking: 8 });
    lib.setFont(ctx, tokens, "mono", 32); ctx.fillStyle = dim;
    lib.drawText(ctx, `f ${String(lib.frame(t)).padStart(3, "0")} / 150`, W / 2, 740, { align: "center" });
  }
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  ctx.fillStyle = C(lib, tokens, "bg"); ctx.fillRect(0, 0, W, H);
  ctx.save(); const pat = ctx.createPattern(L.dots, "repeat"); pat.setTransform(new DOMMatrix().translate(drift(Math.min(t, 4)) * 0.9, 0)); ctx.fillStyle = pat; ctx.fillRect(0, 0, W, H); ctx.restore();
  if (t < 4.0) hud(ctx, t, tokens, lib);
  else {
    const e = lib.easeOf(tokens.ease.enter)(lib.seg(t, 4.0, 4.0 + 10 / 30)), x = lib.easeOf(tokens.ease.exit)(lib.seg(t, 4.0, 4.2));
    if (x < 1) hud(ctx, 3.99, tokens, lib, { fade: 1 - x });
    const [wx, wy] = L.wps[2].p, d = drift(3.99);
    const p0 = { x: wx - 150 + d, y: wy - 150, w: 300, h: 330 }, p1 = { x: 72, y: 72, w: W - 144, h: H - 144 };
    const p = { x: lib.lerp(p0.x, p1.x, e), y: lib.lerp(p0.y, p1.y, e), w: lib.lerp(p0.w, p1.w, e), h: lib.lerp(p0.h, p1.h, e) };
    endCard(ctx, t, tokens, lib, p);
  }
  lib.scanlines(ctx, t, { spacing: 3, thickness: 1, alpha: 0.12, color: "#000000" });
}

// foley (events.json is generated from this list; times are the same ones the scene uses)
const px = (x) => Math.round((x / 960 - 1) * 100) / 100;
export const FOLEY = [
  ...[0.1, 0.4, 0.7].map((t) => ({ t, sfx: "tick", gain_db: -12, pan: 0 })),                        // the counter runs
  { t: 0.85, sfx: "whoosh", gain_db: -16, pan: 0.5 }, { t: 0.86, sfx: "typing", gain_db: -18, pan: -0.5 },   // flies to its corner; decode
  ...[2.0, 2.2, 2.4].map((t, k) => ({ t: t + 0.2, sfx: "toggle", gain_db: -10, pan: px([337, 960, 1583][k]) })),   // waypoints boot
  { t: 2.66, sfx: "tick", gain_db: -10, pan: px(1583) },                                              // second alert blink
  { t: 2.9, sfx: "swish_rev", gain_db: -18, pan: 0 }, { t: 3.3, sfx: "swish_rev", gain_db: -18, pan: 0 },   // scan sweeps land
  { t: 3.6, sfx: "success", gain_db: -12, pan: px(1583) },                                               // lock
  { t: 4.1, sfx: "whoosh", gain_db: -10, pan: 0.4 },                                                      // the panel expands
];
