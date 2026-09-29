// monumental-scifi swatch — vast forms taller than the frame, one dominant light (amber haze behind them), sparse type.
//   0.0–0.8  three black monoliths already stand, cut off by the top of the frame; at 0.1 s the amber haze behind them
//            blooms and the horizon line draws out from the centre; the camera starts a slow push-and-crane
//   0.8–2.6  the title (76 px, wide-tracked caps) fades in letter by letter below the horizon; the Chinese line follows
//   2.0–4.0  the slabs light up one by one: outline (only its edges ignite), storyboard (seams), draft (an amber
//            slit); their names are engraved on their faces; a 52 px figure stands in front of the light; each beat
//            after 2.6 has an event: slit ignites 2.8, a pulse climbs the slit 3.2, the haze surges 3.6
//   4.0–5.0  fog push: the camera accelerates into the slit until the frame is fog, then the end card clears
let L = null;
export const fonts = ["Avenir Next", "PingFang SC"];

export async function setup(ctx, tokens, lib) {
  const fogC = lib.mixColor(lib.color(tokens, "extra.0"), lib.color(tokens, "accent"), 0.35), [fr, fgc, fb] = lib.rgb(fogC);
  const fogTex = (seed, sc, dens) => {
    const w = 480, h = 270, c = document.createElement("canvas"); c.width = w; c.height = h;
    const x = c.getContext("2d"), im = x.createImageData(w, h);
    for (let j = 0; j < h; j++) {
      const ramp = Math.pow(lib.smoothstep(0, 1, j / h), 1.6);
      for (let i = 0; i < w; i++) {
        const n = lib.clamp(0.55 + 0.9 * lib.fbm2(i / sc, j / (sc * 0.4), { octaves: 5, seed }), 0, 1), k = (j * w + i) * 4;
        im.data[k] = fr; im.data[k + 1] = fgc; im.data[k + 2] = fb; im.data[k + 3] = Math.round(255 * dens * ramp * (0.45 + 0.55 * n));
      }
    }
    x.putImageData(im, 0, 0); return c;
  };
  const motes = Array.from({ length: 70 }, (_, i) => ({ x: lib.hash(1, i) * 1920, y: lib.hash(2, i) * 1080, v: 4 + lib.hash(3, i) * 10, r: 0.8 + lib.hash(4, i) * 1.6, a: 0.10 + lib.hash(5, i) * 0.22 }));
  L = { fogA: fogTex(3, 70, 0.8), fogB: fogTex(7, 40, 0.9), motes, horizon: 720,
        slabs: [{ x: 400, w: 290 }, { x: 960, w: 330 }, { x: 1520, w: 300 }] };
}

function cam(t, lib) {                                    // slow push + crane, then the fog push into the slit
  const u1 = lib.ease.inOutSine(lib.seg(t, 0, 4)), u2 = lib.ease.inOutCubic(lib.seg(t, 4.0, 4.55));
  const k = (1 + 0.06 * u1) * (1 + 2.4 * u2);
  return { fx: lib.lerp(960, L.slabs[2].x, u2), fy: lib.lerp(700, 380, u2), k, dy: 36 * (1 - u1) };
}
function apply(ctx, c, depth) {
  const k = 1 + (c.k - 1) * (0.35 + 0.65 * depth);
  ctx.translate(c.fx, c.fy + c.dy * depth); ctx.scale(k, k); ctx.translate(-c.fx, -c.fy);
}

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  if (t < 4.5) world(ctx, t, tokens, lib); else endCard(ctx, t, tokens, lib);
  const fogUp = lib.ease.inCubic(lib.seg(t, 4.1, 4.5)), fogDown = 1 - lib.ease.outCubic(lib.seg(t, 4.5, 4.95)) * 0.72;
  const full = t < 4.5 ? fogUp : fogDown;
  if (full > 0) {
    ctx.save(); ctx.globalAlpha = full; ctx.fillStyle = lib.mixColor(C("extra.0"), C("accent"), 0.22); ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = full * 0.5; ctx.drawImage(L.fogA, -((t * 30) % 200), 0, W + 400, H); ctx.restore();
  }
  if (t < 4.5) type(ctx, t, tokens, lib, 1 - fogUp); else endText(ctx, t, tokens, lib);
  motes(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: 0.05, fps: 24, seed: 3 });
  lib.vignette(ctx, { strength: 0.45, inner: 0.45, color: "#000000" });
}

function haze(t, lib) {                                   // the one light: blooms at 0.1 s, surges at 3.6 s
  return 0.15 + 0.85 * lib.ease.outCubic(lib.seg(t, 0.08, 0.7)) + 0.35 * Math.exp(-Math.pow((t - 3.75) / 0.18, 2));
}
function world(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib, hy = L.horizon, c = cam(t, lib), acc = C("accent"), hz = haze(t, lib);
  // sky: deep black overhead, amber haze rising from behind the slabs
  ctx.save(); apply(ctx, c, 0);
  ctx.fillStyle = "#07080a"; ctx.fillRect(-500, -600, W + 1000, hy + 600);
  let g = ctx.createRadialGradient(W / 2, hy + 40, 0, W / 2, hy + 40, 1100);
  g.addColorStop(0, lib.rgba(lib.mixColor(acc, "#ffffff", 0.18), 0.95 * Math.min(1, hz))); g.addColorStop(0.35, lib.rgba(acc, 0.45 * hz)); g.addColorStop(1, lib.rgba(acc, 0));
  ctx.fillStyle = g; ctx.fillRect(-500, -600, W + 1000, hy + 600);
  ctx.globalAlpha = 0.5 * hz; ctx.drawImage(L.fogA, -((t * 16) % 480) - 260, hy - 420, W + 900, 460); ctx.globalAlpha = 1;
  const top = ctx.createLinearGradient(0, -200, 0, hy - 60);                            // the haze thins upward into black
  top.addColorStop(0, "rgba(7,8,10,0.92)"); top.addColorStop(0.55, "rgba(7,8,10,0.55)"); top.addColorStop(1, "rgba(7,8,10,0)");
  ctx.fillStyle = top; ctx.fillRect(-500, -600, W + 1000, hy + 540);
  ctx.restore();
  // ground: deep black with the haze reflected in a thin band
  ctx.save(); apply(ctx, c, 0.8);
  g = ctx.createLinearGradient(0, hy, 0, H + 300); g.addColorStop(0, lib.mixColor("#0c0b0a", acc, 0.28 * Math.min(1, hz))); g.addColorStop(0.1, "#0b0b0c"); g.addColorStop(1, "#050506");
  ctx.fillStyle = g; ctx.fillRect(-500, hy, W + 1000, H + 300);
  const hu = lib.ease.outCubic(lib.seg(t, 0.1, 0.5));
  ctx.fillStyle = acc; ctx.globalAlpha = 0.9; ctx.fillRect(W / 2 - hu * 1300, hy - 1, hu * 2600, 2); ctx.globalAlpha = 1;
  ctx.restore();
  // the slabs (taller than the frame) and the figure
  ctx.save(); apply(ctx, c, 0.7);
  L.slabs.forEach((s, k) => slab(ctx, t, tokens, lib, s, k, hz));
  // the figure: 52 px, black against the light, in front of the draft slab's spill
  const fx = L.slabs[2].x + 210, fh = 52;
  ctx.fillStyle = "#050506";
  ctx.beginPath(); ctx.arc(fx, hy - fh + 5, 5.5, 0, lib.TAU); ctx.fill();
  ctx.beginPath(); ctx.roundRect(fx - 6.5, hy - fh + 12, 13, fh - 24, 4); ctx.fill();
  ctx.fillRect(fx - 5, hy - 14, 4, 14); ctx.fillRect(fx + 1, hy - 14, 4, 14);
  const sl = 1 + 1.5 * Math.exp(-Math.pow((t - 3.75) / 0.2, 2));                 // shadow stretches with the surge
  ctx.globalAlpha = 0.6; ctx.beginPath(); ctx.ellipse(fx + 22 * sl, hy + 3, 24 * sl, 3, 0, 0, lib.TAU); ctx.fill(); ctx.globalAlpha = 1;
  // ground fog across the slabs' feet
  ctx.globalAlpha = 0.55; ctx.drawImage(L.fogB, -((t * 26) % 480) - 300, hy - 120, W + 1100, 170); ctx.globalAlpha = 1;
  ctx.restore();
}

function slab(ctx, t, tokens, lib, s, k, hz) {
  const C = (n) => lib.color(tokens, n), acc = C("accent"), cold = C("extra.2"), hy = L.horizon, x0 = s.x - s.w / 2, top = -500, h = hy - top;
  const lit = lib.ease.outCubic(lib.seg(t, 2.0 + k * 0.3, 2.45 + k * 0.3));
  ctx.save();
  if (k === 0) {                                          // outline: smoked glass, only the edges ignite (climbing up)
    ctx.fillStyle = "rgba(9,9,10,0.82)"; ctx.fillRect(x0, top, s.w, h);
    ctx.fillStyle = lib.rgba(cold, 0.9); ctx.shadowColor = cold; ctx.shadowBlur = 10 * lit;
    const eh = h * lit; ctx.fillRect(x0, hy - eh, 3, eh); ctx.fillRect(x0 + s.w - 3, hy - eh, 3, eh);
  } else {
    ctx.fillStyle = "#08080a"; ctx.fillRect(x0, top, s.w, h);
    ctx.fillStyle = lib.rgba(acc, 0.5 * hz); ctx.fillRect(x0 - 2, top, 2, h); ctx.fillRect(x0 + s.w, top, 2, h);     // backlit rim
    if (k === 1) {                                        // storyboard: three seams light up
      ctx.fillStyle = lib.rgba(cold, 0.7 * lit);
      for (let j = 0; j < 3; j++) ctx.fillRect(x0, 110 + j * 170, s.w * lit, 2);
    } else {                                              // draft: the amber slit ignites on the 2.8 s beat
      const ig = lib.ease.outCubic(lib.seg(t, 2.8, 2.95)) * 0.9 + 0.1 * lit, pulse = Math.exp(-Math.pow((t - 3.25) / 0.12, 2));
      const sy0 = 90, sy1 = 560;
      ctx.shadowColor = acc; ctx.shadowBlur = 30 * ig; ctx.fillStyle = lib.mixColor(acc, "#fff4e0", 0.25 * ig);
      ctx.globalAlpha = Math.max(0.05, ig); ctx.fillRect(s.x - 4, sy0, 8, sy1 - sy0); ctx.globalAlpha = 1;
      if (pulse > 0.01) {                                // a pulse climbs the slit (3.2 s)
        const py = lib.lerp(sy1, sy0, lib.seg(t, 3.12, 3.42));
        ctx.shadowBlur = 40; ctx.fillStyle = "#fff1d8"; ctx.globalAlpha = pulse; ctx.fillRect(s.x - 6, py - 40, 12, 80); ctx.globalAlpha = 1;
      }
      ctx.shadowBlur = 0; ctx.globalAlpha = 0.45 * ig;
      const sp = ctx.createRadialGradient(s.x, hy + 6, 0, s.x, hy + 6, 260); sp.addColorStop(0, acc); sp.addColorStop(1, lib.rgba(acc, 0));
      ctx.fillStyle = sp; ctx.fillRect(s.x - 260, hy, 520, 60); ctx.globalAlpha = 1;
    }
  }
  ctx.restore();
}

function type(ctx, t, tokens, lib, alpha) {
  const C = (k) => lib.color(tokens, k), { W } = lib;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha;
  // engraved names on the slab faces (they ride the slab layer's push)
  const c = cam(t, lib), kk = 1 + (c.k - 1) * (0.35 + 0.65 * 0.7), P = (x, y) => [c.fx + (x - c.fx) * kk, c.fy + c.dy * 0.7 + (y - c.fy) * kk];
  L.slabs.forEach((s, k) => {
    const a = lib.ease.outQuint(lib.seg(t, 2.05 + k * 0.3, 2.5 + k * 0.3)); if (a <= 0) return;
    ctx.globalAlpha = alpha * a;
    const [x1, y1] = P(s.x, 616), [, y2] = P(s.x, 680);
    lib.setFont(ctx, tokens, "display", 28, { weight: 500 }); ctx.fillStyle = "#cfc9be";
    lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), x1, y1, { align: "center", tracking: 28 * 0.34 });
    lib.setFont(ctx, tokens, "zh", 48, { weight: 400 }); ctx.fillStyle = "#e9e4da";
    lib.drawText(ctx, lib.MOTIF[k].zh, x1, y2, { align: "center", tracking: 48 * 0.25 });
  });
  ctx.globalAlpha = alpha;
  // title below the horizon, on the dark ground: 76 px wide-tracked caps, high contrast
  const en = lib.TITLE_EN.toUpperCase(), size = 76;
  lib.setFont(ctx, tokens, "display", size, { weight: 500 }); ctx.fillStyle = C("fg");
  const lay = lib.layoutText(ctx, en, { x: W / 2, y: 862, align: "center", tracking: size * 0.3 });
  lib.drawGlyphs(ctx, lay, (g, i) => { const t0 = 0.85 + i * 0.05, a = lib.ease.outQuint(lib.seg(t, t0, t0 + 0.4)); return a <= 0 ? null : { alpha: a, dy: (1 - a) * 8 }; });
  lib.setFont(ctx, tokens, "zh", 58, { weight: 400 }); ctx.fillStyle = C("fg");
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 952, align: "center", tracking: 58 * 0.24 });
  lib.drawGlyphs(ctx, zl, (g, i) => { const t0 = 1.45 + i * 0.08, a = lib.ease.outQuint(lib.seg(t, t0, t0 + 0.4)); return a <= 0 ? null : { alpha: a, dy: (1 - a) * 8 }; });
  ctx.restore();
}

function endCard(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W, H } = lib;
  ctx.fillStyle = "#07080a"; ctx.fillRect(0, 0, W, H);
  const g = ctx.createRadialGradient(W / 2, H * 0.55, 0, W / 2, H * 0.55, 900); g.addColorStop(0, lib.rgba(C("accent"), 0.5)); g.addColorStop(1, lib.rgba(C("accent"), 0));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const k = 1 + 0.03 * lib.seg(t, 4.5, 5.0);
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(k, k); ctx.translate(-W / 2, -H / 2);
  ctx.fillStyle = "#08080a"; ctx.fillRect(W / 2 - 360, -40, 720, H + 80);
  ctx.shadowColor = C("accent"); ctx.shadowBlur = 40; ctx.fillStyle = C("accent"); ctx.fillRect(W / 2 - 5, 120, 10, 600);
  ctx.restore();
}
function endText(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k), { W } = lib, a = lib.ease.outQuint(lib.seg(t, 4.62, 4.98));
  ctx.save(); ctx.globalAlpha = a;
  lib.setFont(ctx, tokens, "display", 56, { weight: 500 }); ctx.fillStyle = C("fg");
  lib.drawText(ctx, "MONUMENTAL SCI-FI", W / 2, 880, { align: "center", tracking: 56 * 0.34 });
  lib.setFont(ctx, tokens, "zh", 52, { weight: 400 });
  lib.drawText(ctx, "纪念碑科幻", W / 2, 960, { align: "center", tracking: 52 * 0.3 });
  ctx.restore();
}
function motes(ctx, t, tokens, lib) {
  const { W } = lib;
  ctx.save(); ctx.fillStyle = lib.color(tokens, "fg");
  for (const m of L.motes) {
    const x = ((m.x - t * m.v) % W + W) % W, y = m.y + Math.sin(t * 0.4 + m.x) * 6;
    ctx.globalAlpha = m.a; ctx.beginPath(); ctx.arc(x, y, m.r, 0, lib.TAU); ctx.fill();
  }
  ctx.restore();
}

// foley (events.json is generated from this list; times are the same ones the scene uses)
const px = (x) => Math.round((x / 960 - 1) * 100) / 100;
export const FOLEY = [
  { t: 0.1, sfx: "boom", gain_db: -6, pan: 0, dist: 3 },                                                 // the haze blooms behind the slabs
  { t: 2.05, sfx: "whoosh", gain_db: -12, pan: px(400), dist: 3 }, { t: 2.35, sfx: "whoosh", gain_db: -12, pan: 0, dist: 3 },   // edges, seams
  { t: 2.8, sfx: "boom", gain_db: -4, pan: px(1520), dist: 2 },                                           // the slit ignites
  { t: 3.25, sfx: "whoosh", gain_db: -12, pan: px(1520), dist: 2 },                                       // the pulse climbs
  { t: 3.75, sfx: "boom", gain_db: -10, pan: 0, dist: 4 },                                                // the haze surges
  { t: 4.3, sfx: "whoosh", gain_db: -8, pan: px(1520), dist: 1.5 },                                       // the push into the slit
];
