// blueprint swatch: one cyanotype sheet, drawn in drafting order; the camera reads it like an eye.
//   0.0–0.8  sheet (mottled Prussian blue, coating streaks, folds, bleached edge) and the border draw on
//   0.8–2.5  guide lines, then the title lettered stroke by stroke with a bright nib; Chinese in long Fangsong
//   2.0–2.95 FIG. 1 outline (centre + construction lines) → FIG. 2 storyboard (outline + hidden lines)
//            → FIG. 3 draft (section hatching, live dimension, balloon)
//   3.1–3.7  FIG. 3 stretches; its dimension follows and counts 280 → 340 inside a reviewer-yellow revision cloud
//   4.0–4.8  fig-pan: the camera pans and pushes to the title block (end frame)
// Everything is drawn in sheet coordinates under one camera transform; line widths scale as zoom^0.6.

let L = null;
const SW = 2400, SH = 1350;
const TB = { x: 1880, y: 1100, w: 480, h: 210 };            // title block (sheet coords)

export const fonts = ["STFangsong", "DIN Alternate"];

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  // ── the sheet, built once: fbm mottling + coating streaks + folds + bleached edge + specks
  const c = document.createElement("canvas"); c.width = SW; c.height = SH;
  const x = c.getContext("2d");
  const gw = 240, gh = 135, g = document.createElement("canvas"); g.width = gw; g.height = gh;
  const gx = g.getContext("2d"), img = gx.createImageData(gw, gh), A = lib.rgb(P("bg")), B = lib.rgb(P("extra.0"));
  for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
    const n = 0.5 + 0.55 * lib.fbm2(i / 38, j / 38, { octaves: 4, seed: 5 }) + 0.12 * (i / gw - 0.5), k = (j * gw + i) * 4;
    for (let ch = 0; ch < 3; ch++) img.data[k + ch] = lib.lerp(A[ch], B[ch], lib.clamp(n));
    img.data[k + 3] = 255;
  }
  gx.putImageData(img, 0, 0); x.imageSmoothingQuality = "high"; x.drawImage(g, 0, 0, SW, SH);
  const r = lib.rng(8);
  for (let s = 0; s < 110; s++) {                                        // uneven coating streaks (short, soft, irregular)
    const y = r() * SH, a = 0.018 + 0.035 * r(), light = r() < 0.5, x0 = r() * SW, len = 300 + 1500 * r(), th = 2 + 10 * r();
    const gr = x.createLinearGradient(x0, 0, x0 + len, 0), c = light ? "120,160,215" : "8,24,56";
    gr.addColorStop(0, `rgba(${c},0)`); gr.addColorStop(0.5, `rgba(${c},${a})`); gr.addColorStop(1, `rgba(${c},0)`);
    x.fillStyle = gr; x.fillRect(x0, y, len, th);
  }
  const edge = (x0, y0, x1, y1, w) => { const gr = x.createLinearGradient(x0, y0, x1, y1); gr.addColorStop(0, lib.rgba(P("extra.2"), 0.55)); gr.addColorStop(1, lib.rgba(P("extra.2"), 0)); x.fillStyle = gr; return w; };
  edge(0, 0, 60, 0); x.fillRect(0, 0, 60, SH); edge(SW, 0, SW - 60, 0); x.fillRect(SW - 60, 0, 60, SH);
  edge(0, 0, 0, 60); x.fillRect(0, 0, SW, 60); edge(0, SH, 0, SH - 60); x.fillRect(0, SH - 60, SW, 60);
  for (const [x0, y0, x1, y1, dx, dy] of [[SW / 2, 0, SW / 2, SH, 3, 0], [0, SH / 2, SW, SH / 2, 0, 3]]) {   // folds
    x.strokeStyle = lib.rgba(P("extra.2"), 0.55); x.lineWidth = 2; x.beginPath(); x.moveTo(x0, y0); x.lineTo(x1, y1); x.stroke();
    x.strokeStyle = "rgba(6,18,44,0.35)"; x.lineWidth = 3; x.beginPath(); x.moveTo(x0 + dx, y0 + dy); x.lineTo(x1 + dx, y1 + dy); x.stroke();
  }
  for (let s = 0; s < 500; s++) { x.fillStyle = `rgba(200,220,245,${0.08 + 0.12 * r()})`; x.beginPath(); x.arc(r() * SW, r() * SH, 0.6 + 1.4 * r(), 0, lib.TAU); x.fill(); }
  L = { paper: c, slots: lib.slots(3, { area: lib.SAFE.title, y: 690 }) };
}

// camera: sheet → screen. Holds on the drawing area, then pans + pushes to the title block (4.0–4.8).
function cam(t, lib) {
  const u = lib.tween(t, 4.0, 4.8, lib.ease.inOutCubic);
  return { cx: lib.lerp(960 + 6 * lib.seg(t, 0, 4), TB.x + TB.w / 2, u), cy: lib.lerp(540, TB.y + TB.h / 2, u), z: lib.lerp(1, 2.15, u) };
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const C = cam(t, lib);
  ctx.fillStyle = P("extra.3"); ctx.fillRect(0, 0, W, H);
  ctx.save();
  ctx.translate(W / 2, H / 2); ctx.scale(C.z, C.z); ctx.translate(-C.cx, -C.cy);
  const lw = (w) => w * Math.pow(C.z, 0.6) / C.z;                        // screen width = w · zoom^0.6
  ctx.save(); ctx.shadowColor = "rgba(0,0,0,0.6)"; ctx.shadowBlur = 40; ctx.shadowOffsetX = 10; ctx.shadowOffsetY = 14;
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, SW, SH); ctx.restore();
  ctx.drawImage(L.paper, 0, 0);
  ctx.shadowColor = "rgba(232,241,250,0.35)"; ctx.shadowBlur = 3;         // a touch of ink bleed on every line
  drawSheet(ctx, t, tokens, lib, lw);
  ctx.restore();
}

// polyline drawn on up to u (0..1); returns the tip so a nib can sit on it
function drawOn(ctx, pts, u) {
  let tot = 0; const Ls = [];
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); Ls.push(l); tot += l; }
  let left = Math.max(0, Math.min(1, u)) * tot, tip = pts[0];
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length && left > 0; i++) {
    const f = Math.min(1, left / Ls[i - 1]); tip = [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
    ctx.lineTo(tip[0], tip[1]); left -= Ls[i - 1];
  }
  ctx.stroke(); return tip;
}
function nib(ctx, lib, p, a = 1) {
  if (a <= 0) return;
  ctx.save(); ctx.shadowBlur = 0; const g = ctx.createRadialGradient(p[0], p[1], 0, p[0], p[1], 14);
  g.addColorStop(0, `rgba(255,255,255,${0.95 * a})`); g.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = g; ctx.beginPath(); ctx.arc(p[0], p[1], 14, 0, lib.TAU); ctx.fill(); ctx.restore();
}

function drawSheet(ctx, t, tokens, lib, lw) {
  const P = (k) => lib.color(tokens, k);
  const WHITE = P("fg"), PALE = P("extra.1"), YEL = P("accent");
  const E = lib.easeOf(tokens.ease.enter);
  // border (inset 40) + title block frame
  ctx.strokeStyle = WHITE; ctx.lineWidth = lw(3);
  const b = [[40, 40], [SW - 40, 40], [SW - 40, SH - 40], [40, SH - 40], [40, 40]];
  const bu = E(lib.seg(t, 0.1, 0.75)); if (bu > 0) { const tip = drawOn(ctx, b, bu); if (bu < 1) nib(ctx, lib, tip); }
  const PALE_ = PALE;
  if (t > 0.5) titleBlock(ctx, t, tokens, lib, lw);

  // ── title: guide lines, then lettering stroke by stroke
  const T0 = 0.8;
  guide(ctx, lib, 192, 232, 1260, 232 - 0.72 * 132, lib.seg(t, T0, T0 + 0.25), PALE, lw);
  lib.setFont(ctx, tokens, "display", 132, { weight: 700 });
  const tip = letter(ctx, lib, lib.TITLE_EN, 192, 232, t, T0 + 0.18, 0.045, 0.3, WHITE, 132, 0.02 * 132, 1, lw);
  guide(ctx, lib, 192, 330, 700, 330 - 0.82 * 62, lib.seg(t, 1.55, 1.8), PALE, lw);
  lib.setFont(ctx, tokens, "zh", 62, { weight: 400 });
  const tip2 = letter(ctx, lib, lib.TITLE_ZH, 192, 330, t, 1.7, 0.07, 0.26, WHITE, 62, 0.14 * 62, 0.72, lw);
  if (tip) nib(ctx, lib, tip); if (tip2) nib(ctx, lib, tip2);

  // ── the three figures
  L.slots.forEach((s, k) => figure(ctx, t, tokens, lib, lw, s.x, 650, k));
  // general notes, top right (lettered in pale blue-white, texture more than text)
  const na = lib.seg(t, 1.3, 1.8);
  if (na > 0) {
    ctx.save(); ctx.shadowBlur = 0; ctx.fillStyle = PALE; ctx.globalAlpha = na * 0.85;
    lib.setFont(ctx, tokens, "body", 26, { weight: 700 });
    ["GENERAL NOTES", "1. ALL DIMENSIONS IN MM.", "2. DO NOT SCALE DRAWING."].forEach((q, i) => lib.drawText(ctx, q, 1420, 150 + i * 40, { tracking: 0.08 * 26 }));
    ctx.restore();
  }
}

function guide(ctx, lib, x0, yb, x1, yc, u, col, lw) {
  if (u <= 0) return;
  ctx.save(); ctx.strokeStyle = col; ctx.globalAlpha = 0.45; ctx.lineWidth = lw(1); ctx.shadowBlur = 0;
  drawOn(ctx, [[x0 - 20, yb], [x1, yb]], u); drawOn(ctx, [[x0 - 20, yc], [x1, yc]], u); ctx.restore();
}

// engineering lettering: glyph outline traced by a growing dash, fill comes in at the end; sx < 1 = long Fangsong
function letter(ctx, lib, str, x, y, t, t0, stag, dur, col, size, tr, sx, lw) {
  const lay = lib.layoutText(ctx, str, { x: 0, y, tracking: tr });
  ctx.save(); ctx.textAlign = "center"; ctx.textBaseline = "alphabetic"; ctx.strokeStyle = col; ctx.fillStyle = col;
  ctx.lineWidth = lw(1.6); let n = 0, tip = null;
  for (const g of lay.glyphs) {
    if (g.ch === " ") continue;
    const u = lib.seg(t, t0 + n * stag, t0 + n * stag + dur); n++;
    if (u <= 0) continue;
    const gx = x + g.cx * sx;
    ctx.save(); ctx.translate(gx, y); ctx.scale(sx, 1);
    if (u < 1) { ctx.setLineDash([size * 5 * lib.ease.inOutSine(Math.min(1, u / 0.75)), 1e5]); ctx.strokeText(g.ch, 0, 0); ctx.setLineDash([]); tip = [gx + (u - 0.5) * g.w * sx, y - size * 0.35]; }
    const f = lib.smoothstep(0.6, 1, u); if (f > 0) { ctx.globalAlpha = f; ctx.fillText(g.ch, 0, 0); }
    ctx.restore();
  }
  ctx.restore(); return tip;
}

function dashLine(ctx, pts, u, dash) { ctx.save(); ctx.setLineDash(dash); drawOn(ctx, pts, u); ctx.restore(); }

function figure(ctx, t, tokens, lib, lw, cx, cy, k) {
  const P = (q) => lib.color(tokens, q);
  const WHITE = P("fg"), PALE = P("extra.1"), YEL = P("accent");
  const E = lib.easeOf(tokens.ease.enter);
  const base = 2.0 + k * 0.15;
  const stretch = k === 2 ? lib.tween(t, 3.1, 3.7, lib.ease.inOutCubic) : 0;
  const w = 340 + 70 * stretch, h = 190, x0 = cx - 170 - (k === 2 ? 35 * stretch : 0), y0 = cy - h / 2, hx = x0 + w / 2, R = 50;
  // centre lines (dash-dot), all figures
  const cu = E(lib.seg(t, base, base + 0.3));
  if (cu > 0) {
    ctx.strokeStyle = PALE; ctx.lineWidth = lw(1.2);
    dashLine(ctx, [[x0 - 30, cy], [x0 + w + 30, cy]], cu, [24, 6, 4, 6]);
    dashLine(ctx, [[hx, y0 - 30], [hx, y0 + h + 30]], cu, [24, 6, 4, 6]);
  }
  if (k === 0) {                                                          // FIG. 1: construction lines only
    const u = E(lib.seg(t, base + 0.1, base + 0.45));
    if (u > 0) {
      ctx.save(); ctx.strokeStyle = PALE; ctx.globalAlpha = 0.5; ctx.lineWidth = lw(1);
      for (const yy of [y0, y0 + h]) drawOn(ctx, [[x0 - 50, yy], [x0 + w + 50, yy]], u);
      for (const xx of [x0, x0 + w]) drawOn(ctx, [[xx, y0 - 50], [xx, y0 + h + 50]], u);
      ctx.beginPath(); ctx.arc(hx, cy, R, -Math.PI / 2, -Math.PI / 2 + lib.TAU * u); ctx.stroke();
      ctx.restore();
    }
  } else {
    const ou = E(lib.seg(t, base + 0.12, base + 0.42));
    if (ou > 0) {                                                         // outline (3 px) + hole
      ctx.strokeStyle = WHITE; ctx.lineWidth = lw(3);
      const tip = drawOn(ctx, [[x0, y0], [x0 + w, y0], [x0 + w, y0 + h], [x0, y0 + h], [x0, y0]], ou);
      ctx.lineWidth = lw(2); ctx.beginPath(); ctx.arc(hx, cy, R, -Math.PI / 2, -Math.PI / 2 + lib.TAU * ou); ctx.stroke();
      if (ou < 1) nib(ctx, lib, tip);
    }
    if (k === 1) {                                                        // FIG. 2: hidden lines of a counterbore
      const hu = E(lib.seg(t, base + 0.3, base + 0.5));
      if (hu > 0) { ctx.strokeStyle = WHITE; ctx.lineWidth = lw(1.6); for (const xx of [hx - 64, hx + 64]) dashLine(ctx, [[xx, y0], [xx, y0 + h]], hu, [10, 6]); }
    }
    if (k === 2) {                                                        // FIG. 3: hatching, dimension, balloon
      const su = lib.seg(t, base + 0.3, base + 0.55);
      if (su > 0) {
        ctx.save(); ctx.beginPath(); ctx.rect(x0, y0, w, h); ctx.arc(hx, cy, R, 0, lib.TAU, true); ctx.clip("evenodd");
        ctx.beginPath(); ctx.rect(x0, y0, w * su, h); ctx.clip();
        ctx.strokeStyle = WHITE; ctx.globalAlpha = 0.8; ctx.lineWidth = lw(1.1); ctx.shadowBlur = 0;
        for (let d = -h; d < w + h; d += 16) { ctx.beginPath(); ctx.moveTo(x0 + d, y0 + h); ctx.lineTo(x0 + d + h, y0); ctx.stroke(); }
        ctx.restore();
      }
      const du = E(lib.seg(t, base + 0.45, base + 0.7));
      if (du > 0) {
        const yd = y0 + h + 58;
        ctx.strokeStyle = PALE; ctx.fillStyle = PALE; ctx.lineWidth = lw(1.2);
        drawOn(ctx, [[x0, y0 + h + 8], [x0, yd + 12]], du); drawOn(ctx, [[x0 + w, y0 + h + 8], [x0 + w, yd + 12]], du);
        drawOn(ctx, [[x0, yd], [x0 + w, yd]], du);
        if (du >= 1) for (const [ax, dir] of [[x0, 1], [x0 + w, -1]]) { ctx.beginPath(); ctx.moveTo(ax, yd); ctx.lineTo(ax + dir * 18, yd - 6); ctx.lineTo(ax + dir * 18, yd + 6); ctx.closePath(); ctx.fill(); }
        // the live number, whole millimetres
        ctx.save(); ctx.globalAlpha = lib.seg(t, base + 0.6, base + 0.75); ctx.shadowBlur = 0;
        lib.setFont(ctx, tokens, "body", 38, { weight: 700 }); ctx.fillStyle = stretch > 0 && stretch < 1 ? YEL : WHITE;
        lib.drawText(ctx, String(Math.round(w)), x0 + w / 2, yd - 12, { align: "center" });
        ctx.restore();
        // revision cloud (reviewer yellow, once) around the changing dimension
        const rc = lib.env(t, 3.05, 3.95, 0.2, 0.25);
        if (rc > 0) {
          ctx.save(); ctx.strokeStyle = YEL; ctx.lineWidth = lw(2.4); ctx.globalAlpha = rc; ctx.shadowBlur = 0;
          const ex = x0 + w / 2, ey = yd - 26, rx = 74, ry = 34, n = 12;
          ctx.beginPath();
          for (let i = 0; i < n; i++) { const a0 = (i / n) * lib.TAU, a1 = ((i + 1) / n) * lib.TAU, am = (a0 + a1) / 2;
            const p0 = [ex + rx * Math.cos(a0), ey + ry * Math.sin(a0)], p1 = [ex + rx * Math.cos(a1), ey + ry * Math.sin(a1)], bulge = [ex + (rx + 14) * Math.cos(am), ey + (ry + 14) * Math.sin(am)];
            if (i === 0) ctx.moveTo(p0[0], p0[1]); ctx.quadraticCurveTo(bulge[0], bulge[1], p1[0], p1[1]); }
          ctx.stroke(); ctx.restore();
        }
      }
      const bu = E(lib.seg(t, base + 0.42, base + 0.58));                   // balloon 3 with a leader
      if (bu > 0) {
        ctx.strokeStyle = WHITE; ctx.lineWidth = lw(1.2);
        const bx = x0 + w + 70, by = y0 - 40;
        drawOn(ctx, [[x0 + w - 18, y0 + 18], [bx - 18, by + 16]], bu);
        if (bu >= 1) { ctx.beginPath(); ctx.arc(bx, by, 24, 0, lib.TAU); ctx.stroke();
          ctx.save(); ctx.shadowBlur = 0; lib.setFont(ctx, tokens, "body", 30, { weight: 700 }); ctx.fillStyle = WHITE; lib.drawText(ctx, "3", bx, by + 11, { align: "center" }); ctx.restore(); }
      }
    }
  }
  // label: FIG. n · NAME, then the Chinese in long Fangsong
  const la = lib.seg(t, base + 0.3, base + 0.5);
  if (la > 0) {
    ctx.save(); ctx.globalAlpha = la; ctx.shadowBlur = 0; ctx.fillStyle = WHITE;
    lib.setFont(ctx, tokens, "display", 44, { weight: 700 });
    lib.drawText(ctx, `FIG. ${k + 1} · ${lib.MOTIF[k].en.toUpperCase()}`, cx, 880, { align: "center", tracking: 0.06 * 44 });
    lib.setFont(ctx, tokens, "zh", 54, { weight: 400 });
    const s = lib.MOTIF[k].zh, gw = 54 * 0.72 + 10, x = cx - (gw * s.length - 10) / 2;
    [...s].forEach((ch, i) => { ctx.save(); ctx.translate(x + i * gw + 54 * 0.36, 952); ctx.scale(0.72, 1); ctx.textAlign = "center"; ctx.fillText(ch, 0, 0); ctx.restore(); });
    ctx.restore();
  }
}

function titleBlock(ctx, t, tokens, lib, lw) {
  const P = (k) => lib.color(tokens, k);
  const WHITE = P("fg"), PALE = P("extra.1"), YEL = P("accent");
  const u = lib.easeOf(tokens.ease.enter)(lib.seg(t, 0.5, 1.2));
  ctx.strokeStyle = WHITE; ctx.lineWidth = lw(2.4);
  const { x, y, w, h } = TB;
  drawOn(ctx, [[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]], u);
  ctx.lineWidth = lw(1.2);
  drawOn(ctx, [[x, y + 120], [x + w, y + 120]], u); drawOn(ctx, [[x + 330, y + 120], [x + 330, y + h]], u);
  ctx.save(); ctx.shadowBlur = 0; ctx.fillStyle = WHITE; ctx.globalAlpha = lib.seg(t, 1.0, 1.4);
  lib.setFont(ctx, tokens, "display", 74, { weight: 700 }); lib.drawText(ctx, "BLUEPRINT", x + 24, y + 92, { tracking: 0.06 * 74 });
  lib.setFont(ctx, tokens, "zh", 46, { weight: 400 });
  [..."工程蓝图"].forEach((ch, i) => { ctx.save(); ctx.translate(x + 24 + i * 44 + 17, y + 180); ctx.scale(0.72, 1); ctx.textAlign = "center"; ctx.fillText(ch, 0, 0); ctx.restore(); });
  lib.setFont(ctx, tokens, "body", 26, { weight: 700 }); ctx.fillStyle = PALE; lib.drawText(ctx, "SHEET 1/1", x + 350, y + 152);
  // revision triangle: the end shot's one yellow mark
  ctx.strokeStyle = YEL; ctx.fillStyle = YEL; ctx.lineWidth = lw(2); ctx.globalAlpha = lib.seg(t, 4.5, 4.75);
  ctx.beginPath(); ctx.moveTo(x + 400, y + 170); ctx.lineTo(x + 422, y + 196); ctx.lineTo(x + 378, y + 196); ctx.closePath(); ctx.stroke();
  lib.setFont(ctx, tokens, "body", 20, { weight: 700 }); lib.drawText(ctx, "A", x + 400, y + 192, { align: "center" });
  ctx.restore();
}
