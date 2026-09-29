// monumental-scifi swatch — vast forms, layered fog, one amber light, sparse wide-tracked type.
//   0.0–0.8  fog drifts over a colossal slab whose top leaves the frame; the amber horizon line draws out
//   0.8–2.6  title letters fade in 60 ms apart (wide-tracked caps), the Chinese line 80 ms per character
//   2.0–4.0  three monoliths emerge from the ground fog: outline (edges only) → storyboard (seamed panels) →
//            draft (solid, an amber slit of light). A 36 px figure at the draft's foot gives the scale.
//   4.0–5.0  fog push: the camera accelerates into the draft's slit until the frame is fog, then the end
//            card clears out of it
// The camera is one continuous slow push (easeInOutSine), with parallax per depth layer.

let L = null;

export const fonts = ["Avenir Next", "PingFang SC"];

export async function setup(ctx, tokens, lib) {
  // two fog noise sheets (alpha only), low-res then scaled; drifting them is a pure function of t
  // fog sheets: fog-coloured, alpha = noise × a soft vertical ramp (thin at the top, dense at the bottom)
  const [fr, fgc, fb] = lib.rgb(lib.color(tokens, "extra.0"));
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
  const motes = Array.from({ length: 70 }, (_, i) => ({ x: lib.hash(1, i) * 1920, y: lib.hash(2, i) * 1080, v: 4 + lib.hash(3, i) * 10, r: 0.8 + lib.hash(4, i) * 1.6, a: 0.12 + lib.hash(5, i) * 0.25 }));
  L = { fogA: fogTex(3, 70, 0.75), fogB: fogTex(7, 40, 0.85), fogC: fogTex(5, 90, 1.0), motes, horizon: 780, slabs: [480, 960, 1440] };
}

const EASE_S = (lib, u) => lib.ease.inOutSine(u);
function cam(t, lib) {                          // focus point + zoom; slow push, then the fog push into the slit
  const u1 = EASE_S(lib, lib.seg(t, 0, 4)), u2 = lib.ease.inOutCubic(lib.seg(t, 4.0, 4.55));
  const k = (1 + 0.05 * u1) * (1 + 2.4 * u2);
  return { fx: lib.lerp(960, L.slabs[2], u2), fy: lib.lerp(600, 560, u2), k };
}
function apply(ctx, c, depth) {                 // parallax: near layers scale more
  const k = 1 + (c.k - 1) * (0.35 + 0.65 * depth);
  ctx.translate(c.fx, c.fy); ctx.scale(k, k); ctx.translate(-c.fx, -c.fy);
}

export function renderAt(t, ctx, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const { W, H } = lib;
  if (t < 4.5) world(ctx, t, tokens, lib);
  else endCard(ctx, t, tokens, lib);
  // fog that swallows the frame during the push, then thins out over the end card
  const fogUp = lib.ease.inCubic(lib.seg(t, 4.1, 4.5)), fogDown = 1 - lib.ease.outCubic(lib.seg(t, 4.5, 4.95)) * 0.7;
  const full = t < 4.5 ? fogUp : fogDown;
  if (full > 0) {
    ctx.save(); ctx.globalAlpha = full; ctx.fillStyle = lib.mixColor(C("extra.0"), C("accent"), 0.08); ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = full * 0.5; ctx.drawImage(L.fogA, -((t * 30) % 200), 0, W + 400, H); ctx.restore();
  }
  if (t < 4.5) type(ctx, t, tokens, lib, 1 - fogUp); else endText(ctx, t, tokens, lib);
  motes(ctx, t, tokens, lib);
  lib.grain(ctx, t, { amount: 0.06, fps: 24, seed: 3 });
  lib.vignette(ctx, { strength: 0.35, inner: 0.5, color: "#000000" });
}

function world(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const { W, H } = lib, hy = L.horizon, c = cam(t, lib);
  const fog = C("extra.0"), steel = C("extra.1");
  // sky: deep space fading into a warm haze at the horizon
  ctx.save(); apply(ctx, c, 0);
  let g = ctx.createLinearGradient(0, -200, 0, hy);
  g.addColorStop(0, C("bg")); g.addColorStop(0.42, "#161718"); g.addColorStop(0.8, lib.mixColor("#35312d", C("accent"), 0.06)); g.addColorStop(1, "#4a443d");
  ctx.fillStyle = g; ctx.fillRect(-400, -400, W + 800, hy + 400);
  // far megastructures, almost dissolved into the haze
  ctx.fillStyle = lib.mixColor("#2a2724", fog, 0.35); ctx.globalAlpha = 0.55;
  for (let i = 0; i < 9; i++) {
    const x = -300 + i * 290 + lib.hash(11, i) * 80, w = 70 + lib.hash(12, i) * 120, h = 40 + lib.hash(13, i) * 90;
    ctx.fillRect(x, hy - h, w, h);
  }
  ctx.restore();
  // the colossal slab: a dark silhouette against the haze, top out of frame, base lost in fog
  ctx.save(); apply(ctx, c, 0.25);
  const a = lib.ease.outCubic(lib.seg(t, 0.05, 1.1));
  g = ctx.createLinearGradient(0, -100, 0, hy);
  g.addColorStop(0, "#1a1b1d"); g.addColorStop(0.75, "#1c1d1f"); g.addColorStop(1, lib.mixColor("#1c1d1f", fog, 0.4));
  ctx.globalAlpha = a; ctx.fillStyle = g; ctx.fillRect(600, -260, 720, hy + 260);
  ctx.fillStyle = lib.rgba(C("extra.2"), 0.22); ctx.fillRect(1317, -260, 3, hy + 260);                 // one cold lit edge
  ctx.fillStyle = lib.rgba(C("extra.2"), 0.06); ctx.fillRect(600, -260, 2, hy + 260);
  ctx.globalAlpha = 1;
  ctx.drawImage(L.fogC, -((t * 10) % 480) - 300, hy - 520, W + 1000, 560);                            // haze eats its base
  ctx.restore();
  // fog bank between the colossus and the monoliths
  ctx.save(); apply(ctx, c, 0.45);
  ctx.globalAlpha = 0.55;
  ctx.drawImage(L.fogA, -((t * 18) % 480) - 260, hy - 300, W + 900, 330);
  ctx.restore();
  // ground
  ctx.save(); apply(ctx, c, 0.6);
  g = ctx.createLinearGradient(0, hy, 0, H + 200);
  g.addColorStop(0, "#35322e"); g.addColorStop(0.12, "#1a1a1a"); g.addColorStop(1, "#0b0c0d");
  ctx.fillStyle = g; ctx.fillRect(-400, hy, W + 800, H);
  // amber horizon line draws out from the centre
  const hu = lib.ease.outCubic(lib.seg(t, 0.15, 1.0));
  ctx.fillStyle = C("accent"); ctx.globalAlpha = 0.85; ctx.fillRect(W / 2 - hu * 1200, hy - 1, hu * 2400, 1.6);
  ctx.globalAlpha = 1;
  // monoliths
  L.slabs.forEach((x, k) => monolith(ctx, t, tokens, lib, x, k));
  // ground fog over the monoliths' feet
  ctx.globalAlpha = 0.8;
  ctx.drawImage(L.fogB, -((t * 26) % 480) - 300, hy - 170, W + 1100, 200);
  ctx.restore();
}

function monolith(ctx, t, tokens, lib, x, k) {
  const C = (n) => lib.color(tokens, n);
  const hy = L.horizon, w = 150, h = 430, top = hy - h;
  const u = lib.ease.inOutSine(lib.seg(t, 2.0 + k * 0.25, 2.75 + k * 0.25));
  if (u <= 0) return;
  const fog = C("extra.0"), steel = C("extra.1");
  const fogMix = 1 - 0.78 * u;                          // emerges: less fog in front of it
  ctx.save();
  if (k === 0) {                                        // outline: edges only
    ctx.strokeStyle = lib.rgba(lib.mixColor(C("extra.2"), fog, fogMix), 0.9); ctx.lineWidth = 2;
    ctx.strokeRect(x - w / 2, top, w, h);
    ctx.fillStyle = lib.rgba(C("accent"), 0.7 * u); ctx.fillRect(x - w / 2, top - 1, w, 2);     // light on the top edge
  } else if (k === 1) {                                 // storyboard: seamed panels
    ctx.fillStyle = lib.mixColor("#232527", fog, fogMix); ctx.fillRect(x - w / 2, top, w, h);
    ctx.fillStyle = lib.rgba(lib.mixColor(C("extra.2"), fog, fogMix), 0.55);
    for (let j = 1; j < 3; j++) ctx.fillRect(x - w / 2, top + j * h / 3, w, 2);
    ctx.fillRect(x - w / 2, top, 2, h);
  } else {                                              // draft: solid, with the amber slit
    ctx.fillStyle = lib.mixColor("#141516", fog, fogMix); ctx.fillRect(x - w / 2, top, w, h);
    const s = lib.ease.outCubic(lib.seg(t, 2.55, 2.95));
    ctx.shadowColor = C("accent"); ctx.shadowBlur = 26;
    ctx.fillStyle = C("accent"); ctx.fillRect(x - 3, top + h * 0.22, 6, h * 0.58 * s);
    ctx.shadowBlur = 0; ctx.globalAlpha = 0.35 * s;                          // spill on the ground
    const g = ctx.createRadialGradient(x, hy + 6, 0, x, hy + 6, 180); g.addColorStop(0, C("accent")); g.addColorStop(1, lib.rgba(C("accent"), 0));
    ctx.fillStyle = g; ctx.fillRect(x - 180, hy, 360, 40);
    // the only human-scale reference: a 36 px figure at the foot
    ctx.globalAlpha = u; ctx.fillStyle = "#0a0a0b";
    const fx = x + 118, fh = 36;
    ctx.beginPath(); ctx.arc(fx, hy - fh + 4, 4, 0, lib.TAU); ctx.fill();
    ctx.beginPath(); ctx.roundRect(fx - 4.5, hy - fh + 9, 9, fh - 9, 3); ctx.fill();
  }
  ctx.restore();
}

function type(ctx, t, tokens, lib, alpha) {
  const C = (k) => lib.color(tokens, k);
  const { W } = lib;
  if (alpha <= 0) return;
  ctx.save(); ctx.globalAlpha = alpha;
  const en = lib.TITLE_EN.toUpperCase(), size = 62;
  lib.setFont(ctx, tokens, "display", size, { weight: 400 }); ctx.fillStyle = C("fg");
  const lay = lib.layoutText(ctx, en, { x: W / 2, y: 196, align: "center", tracking: size * 0.36 });
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const t0 = 0.85 + i * 0.06, a = lib.ease.outQuint(lib.seg(t, t0, t0 + 0.42));
    return a <= 0 ? null : { alpha: a, dy: (1 - a) * 8 };
  });
  const lu = lib.ease.outCubic(lib.seg(t, 2.05, 2.6));                 // the amber line under the title
  ctx.fillStyle = C("accent"); ctx.fillRect(W / 2 - 70 * lu, 226, 140 * lu, 1.6);
  lib.setFont(ctx, tokens, "zh", 50, { weight: 300 }); ctx.fillStyle = C("fg");
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 296, align: "center", tracking: 50 * 0.22 });
  lib.drawGlyphs(ctx, zl, (g, i) => {
    const t0 = 1.45 + i * 0.08, a = lib.ease.outQuint(lib.seg(t, t0, t0 + 0.42));
    return a <= 0 ? null : { alpha: a * 0.92, dy: (1 - a) * 8 };
  });
  // labels under the monoliths (screen space, they do not ride the parallax)
  L.slabs.forEach((x, k) => {
    const a = lib.ease.outQuint(lib.seg(t, 2.25 + k * 0.18, 2.6 + k * 0.18));
    if (a <= 0) return;
    const c = cam(t, lib), kk = 1 + (c.k - 1) * (0.35 + 0.65 * 0.6), sx = c.fx + (x - c.fx) * kk;
    ctx.globalAlpha = alpha * a * 0.9;
    lib.setFont(ctx, tokens, "display", 26, { weight: 500 }); ctx.fillStyle = C("fg");
    lib.drawText(ctx, lib.MOTIF[k].en.toUpperCase(), sx, 862, { align: "center", tracking: 26 * 0.34 });
    lib.setFont(ctx, tokens, "zh", 46, { weight: 300 });
    lib.drawText(ctx, lib.MOTIF[k].zh, sx, 930, { align: "center", tracking: 46 * 0.25 });
  });
  ctx.restore();
}

function endCard(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const { W, H } = lib;
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, C("bg")); g.addColorStop(1, "#171716");
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  // the draft slab seen from its foot: fills the frame height, the slit is the only light
  const k = 1 + 0.03 * lib.seg(t, 4.5, 5.0);
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(k, k); ctx.translate(-W / 2, -H / 2);
  ctx.fillStyle = "#121314"; ctx.fillRect(W / 2 - 330, -40, 660, H + 80);
  ctx.shadowColor = C("accent"); ctx.shadowBlur = 40; ctx.fillStyle = C("accent");
  ctx.fillRect(W / 2 - 5, 150, 10, 640);
  ctx.restore();
}

function endText(ctx, t, tokens, lib) {
  const C = (k) => lib.color(tokens, k);
  const { W } = lib;
  const a = lib.ease.outQuint(lib.seg(t, 4.62, 4.98));
  ctx.save(); ctx.globalAlpha = a;
  lib.setFont(ctx, tokens, "display", 40, { weight: 400 }); ctx.fillStyle = C("fg");
  lib.drawText(ctx, "MONUMENTAL SCI-FI", W / 2, 918, { align: "center", tracking: 40 * 0.42 });
  lib.setFont(ctx, tokens, "zh", 46, { weight: 300 });
  lib.drawText(ctx, "纪念碑科幻", W / 2, 984, { align: "center", tracking: 46 * 0.3 });
  ctx.restore();
}

function motes(ctx, t, tokens, lib) {
  const { W, H } = lib;
  ctx.save(); ctx.fillStyle = lib.color(tokens, "fg");
  for (const m of L.motes) {
    const x = ((m.x - t * m.v) % W + W) % W, y = m.y + Math.sin(t * 0.4 + m.x) * 6;
    ctx.globalAlpha = m.a; ctx.beginPath(); ctx.arc(x, y, m.r, 0, lib.TAU); ctx.fill();
  }
  ctx.restore();
}
