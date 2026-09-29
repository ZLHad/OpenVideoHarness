// fui-hud swatch — a fictional film interface where every readout is real: the frame number, t, the 5 s timeline.
//   0.0–0.8  24 px dot grid; the FRAME readout panel boots (frame drawn from a corner in 6 frames, data fills in 4);
//            a scan line reveals the timeline schematic
//   0.8–2.6  the title decodes left → right (≤ 9 frames per glyph), then the Chinese line
//   2.0–4.0  three stage panels boot 3 frames apart: 01 outline, 02 storyboard (done), 03 draft (running); the
//            orange brackets — the one alert colour — blink twice at 2 Hz on the draft, then stay on
//   4.0–5.0  panel-expand: the draft panel grows to full frame and becomes the end card
// Numbers are Menlo (SF Mono is not a registered system font on this machine) with tabular figures.

const G = 24;
let L = null;
export const fonts = ["DIN Condensed", "Menlo", "PingFang SC"];

export async function setup(ctx, tokens, lib) {
  const dots = document.createElement("canvas"); dots.width = G; dots.height = G;
  const d = dots.getContext("2d"); d.fillStyle = lib.color(tokens, "extra.1"); d.beginPath(); d.arc(G / 2, G / 2, 1.2, 0, lib.TAU); d.fill();
  L = { dots, readout: { x: 56 * G, y: 6 * G, w: 19 * G, h: 11 * G }, panels: [0, 1, 2].map((k) => ({ x: 6 * G + k * 23 * G, y: 24 * G, w: 21 * G, h: 13 * G })) };
}

const C = (lib, tokens, k) => lib.color(tokens, k);
/** Panel boot: frame lines grow from the top-left corner (linear, 6 frames), then content alpha (4 frames). */
function panelFrame(ctx, lib, tokens, p, f0, f, { bright = 1 } = {}) {
  const u = lib.clamp((f - f0) / 6); if (u <= 0) return 0;
  ctx.save(); ctx.strokeStyle = lib.rgba(C(lib, tokens, "fg"), 0.55 * bright); ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(p.x, p.y + p.h * u); ctx.lineTo(p.x, p.y); ctx.lineTo(p.x + p.w * u, p.y);
  if (u >= 1) { ctx.lineTo(p.x + p.w, p.y + p.h); ctx.lineTo(p.x, p.y + p.h); ctx.closePath(); }
  ctx.stroke();
  // L-shaped corner ticks only on panels that carry data
  ctx.strokeStyle = C(lib, tokens, "fg"); ctx.lineWidth = 2.5; const k = 14;
  ctx.beginPath(); ctx.moveTo(p.x, p.y + k); ctx.lineTo(p.x, p.y); ctx.lineTo(p.x + k, p.y); ctx.stroke();
  ctx.restore();
  return lib.clamp((f - f0 - 6) / 4);
}
function brackets(ctx, lib, tokens, p, pad = 10) {
  const o = C(lib, tokens, "accent"), k = 26;
  ctx.save(); ctx.strokeStyle = o; ctx.lineWidth = 3; ctx.shadowColor = o; ctx.shadowBlur = 14;
  for (const [sx, sy] of [[0, 0], [1, 0], [0, 1], [1, 1]]) {
    const x = p.x - pad + sx * (p.w + 2 * pad), y = p.y - pad + sy * (p.h + 2 * pad), dx = sx ? -k : k, dy = sy ? -k : k;
    ctx.beginPath(); ctx.moveTo(x + dx, y); ctx.lineTo(x, y); ctx.lineTo(x, y + dy); ctx.stroke();
  }
  ctx.restore();
}

function hud(ctx, t, tokens, lib, { fade = 1 } = {}) {
  const f = lib.frame(t), fg = C(lib, tokens, "fg"), dim = C(lib, tokens, "extra.0");
  ctx.save(); ctx.globalAlpha = fade;
  // ── FRAME readout (real data: this frame's own index and time)
  const R = L.readout, a = panelFrame(ctx, lib, tokens, R, 4, f);
  if (a > 0) {
    ctx.globalAlpha = fade * a; ctx.fillStyle = dim;
    lib.setFont(ctx, tokens, "display", 32, { weight: 700 }); lib.drawText(ctx, "FRAME", R.x + 30, R.y + 50, { tracking: 32 * 0.14 });
    lib.drawText(ctx, "30 FPS", R.x + R.w - 30, R.y + 50, { align: "right", tracking: 32 * 0.14 });
    ctx.fillStyle = fg; lib.setFont(ctx, tokens, "mono", 150, { weight: 400 });
    ctx.fontVariantNumeric = "tabular-nums";
    lib.drawText(ctx, String(f).padStart(3, "0"), R.x + 26, R.y + 190);
    lib.setFont(ctx, tokens, "mono", 30); ctx.fillStyle = dim;
    lib.drawText(ctx, `t ${t.toFixed(2)} s  / 5.00`, R.x + 30, R.y + 244);
    ctx.globalAlpha = fade;
  }
  // ── timeline schematic, revealed by a scan line (linear, 0.3–1.1 s)
  const y = 20 * G, x0 = 6 * G, x1 = 74 * G, scan = lib.lerp(x0 - 60, x1 + 60, lib.seg(t, 0.3, 1.1));
  const vis = (x) => lib.smoothstep(scan, scan - 60, x) * 0.75 + 0.25 * (scan > x ? 1 : 0);
  const X = (s) => lib.lerp(x0, x1, s / 5);
  if (t > 0.3) {
    ctx.fillStyle = fg;
    for (let s = 0; s <= 50; s++) {
      const x = X(s / 10), major = s % 10 === 0, v = scan > x ? 1 : 0;
      if (!v) continue;
      ctx.globalAlpha = fade * (major ? 0.9 : 0.35); ctx.fillRect(x, y - (major ? 18 : 8), 1.5, major ? 18 : 8);
      if (major) { lib.setFont(ctx, tokens, "mono", 24); ctx.fillStyle = dim; lib.drawText(ctx, `${s / 10}s`, x + 6, y + 28); ctx.fillStyle = fg; }
    }
    ctx.globalAlpha = fade * 0.6; ctx.fillRect(x0, y, Math.max(0, Math.min(scan, x1) - x0), 1.5);
    if (scan < x1 + 60) { ctx.globalAlpha = fade * 0.8; ctx.fillRect(scan, y - 40, 2, 56); }
    // playhead = t (real)
    ctx.globalAlpha = fade; ctx.fillStyle = fg; const px = X(t);
    if (scan > px) { ctx.beginPath(); ctx.moveTo(px - 8, y - 30); ctx.lineTo(px + 8, y - 30); ctx.lineTo(px, y - 20); ctx.closePath(); ctx.fill(); ctx.fillRect(px - 0.75, y - 20, 1.5, 22); }
  }
  ctx.globalAlpha = fade;
  // ── title: decode, then hold
  lib.setFont(ctx, tokens, "display", 132, { weight: 700 }); ctx.fillStyle = fg;
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: 6 * G, y: 12 * G, tracking: 2 });
  const sg = lib.scrambleGlyphs(lib.TITLE_EN, t, { start: 0.85, stagger: 0.03, settle: 0.3, rate: 15, seed: 3 });
  lib.drawGlyphs(ctx, lay, (g, i) => sg[i].state === "hidden" ? null : { ch: sg[i].ch, alpha: sg[i].state === "done" ? 1 : 0.6 });
  lib.setFont(ctx, tokens, "zh", 64, { weight: 500 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: 6 * G, y: 16 * G, tracking: 6 });
  const zg = lib.scrambleGlyphs(lib.TITLE_ZH, t, { start: 1.3, stagger: 0.06, settle: 0.3, rate: 15, seed: 5 });
  lib.drawGlyphs(ctx, zl, (g, i) => zg[i].state === "hidden" ? null : { ch: zg[i].ch, alpha: zg[i].state === "done" ? 1 : 0.55 });
  // ── stage panels
  L.panels.forEach((p, k) => stage(ctx, t, tokens, lib, p, k, fade));
  ctx.restore();
}

function stage(ctx, t, tokens, lib, p, k, fade) {
  const f = lib.frame(t), fg = C(lib, tokens, "fg"), dim = C(lib, tokens, "extra.0"), acc = C(lib, tokens, "accent");
  const a = panelFrame(ctx, lib, tokens, p, 60 + k * 3, f);
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = fade * a;
  ctx.fillStyle = dim; lib.setFont(ctx, tokens, "mono", 30); lib.drawText(ctx, `0${k + 1}`, p.x + 28, p.y + 58);
  ctx.fillStyle = fg; lib.setFont(ctx, tokens, "display", 44, { weight: 700 }); lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), p.x + 86, p.y + 60, { tracking: 44 * 0.1 });
  lib.setFont(ctx, tokens, "zh", 50, { weight: 500 }); lib.drawText(ctx, lib.MOTIF[k].zh, p.x + 28, p.y + 136, { tracking: 6 });
  // wireframe icon on the right
  const ix = p.x + p.w - 176, iy = p.y + 92;
  ctx.strokeStyle = lib.rgba(fg, 0.6); ctx.lineWidth = 1.5; ctx.beginPath();
  if (k === 0) for (let j = 0; j < 3; j++) { ctx.moveTo(ix, iy + 12 + j * 26); ctx.lineTo(ix + (j === 2 ? 90 : 148), iy + 12 + j * 26); }
  else if (k === 1) for (let j = 0; j < 3; j++) ctx.rect(ix + j * 52, iy, 42, 78);
  else { ctx.moveTo(ix + 50, iy); ctx.lineTo(ix + 116, iy + 39); ctx.lineTo(ix + 50, iy + 78); ctx.closePath(); }
  ctx.stroke();
  // progress: stages 1–2 done, stage 3 running (value counts in steps)
  const pct = k < 2 ? 100 : Math.round(100 * lib.ease.outCubic(lib.seg(t, 2.3, 3.6)) * 0.99);
  const by = p.y + 222, bw = p.w - 56;
  ctx.fillStyle = lib.rgba(fg, 0.2); ctx.fillRect(p.x + 28, by, bw, 3);
  ctx.fillStyle = k === 2 ? acc : fg; ctx.fillRect(p.x + 28, by, bw * pct / 100, 3);
  lib.setFont(ctx, tokens, "mono", 28); ctx.fillStyle = k === 2 ? fg : dim;
  lib.drawText(ctx, k < 2 ? "DONE" : "RUNNING", p.x + 28, by + 52);
  lib.drawText(ctx, `${String(pct).padStart(3, " ")}%`, p.x + p.w - 28, by + 52, { align: "right" });
  ctx.restore();
  // the alert: brackets blink twice at 2 Hz, then stay on (visible at the 3.0 s poster)
  if (k === 2) {
    const on = (t >= 2.3 && t < 2.47) || (t >= 2.63 && t < 2.8) || t >= 2.9;
    if (on) { ctx.save(); ctx.globalAlpha = fade; brackets(ctx, lib, tokens, p); ctx.restore(); }
  }
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
  ctx.save(); ctx.fillStyle = ctx.createPattern(L.dots, "repeat"); ctx.fillRect(0, 0, W, H); ctx.restore();
  if (t < 4.0) hud(ctx, t, tokens, lib);
  else {
    // panel-expand: the draft panel grows to the full frame (easeOutExpo, 10 frames); the rest exits (easeInExpo, 6)
    const e = lib.easeOf(tokens.ease.enter)(lib.seg(t, 4.0, 4.0 + 10 / 30)), x = lib.easeOf(tokens.ease.exit)(lib.seg(t, 4.0, 4.2));
    if (x < 1) hud(ctx, 3.99, tokens, lib, { fade: 1 - x });
    const p0 = L.panels[2], p1 = { x: 72, y: 72, w: W - 144, h: H - 144 };
    const p = { x: lib.lerp(p0.x, p1.x, e), y: lib.lerp(p0.y, p1.y, e), w: lib.lerp(p0.w, p1.w, e), h: lib.lerp(p0.h, p1.h, e) };
    endCard(ctx, t, tokens, lib, p);
  }
  lib.scanlines(ctx, t, { spacing: 3, thickness: 1, alpha: 0.08 * 2.2, color: "#000000" });
}
