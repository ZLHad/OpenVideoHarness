// bouncy-flat-2d swatch: flat shapes that act, on a cream stage.
//   0.0–0.8  the ground line draws, a mint hill and a mustard sun pop in, the tomato hero drops in and squashes
//   0.8–2.6  title letters fall one by one and squash on landing; Chinese characters pop with a small overshoot
//   2.0–2.4  outline → storyboard → draft pop out of the ground as three flat props
//   2.3–3.8  the hero hops across them: anticipation, stretched arc, squash on each landing, the prop dips under it
//   4.0–4.55 shape wipe: a tomato circle grows out of the hero and becomes the end frame
// Positions and squash are continuous; blinks and the hero's face change on 12 fps steps (limited animation).

let L = null;
const GROUND = 800;

export async function setup(ctx, tokens, lib) {
  const s = lib.slots(3, { area: lib.SAFE.title, y: GROUND });
  L = {
    s,
    props: [{ w: 236, h: 138 }, { w: 276, h: 148 }, { w: 246, h: 160 }],
    hero: { w: 140, h: 162 },
    titleSize: lib.fitText(ctx, lib.TITLE_EN, 1240, (z) => lib.setFont(ctx, tokens, "display", z, { weight: 700 }), { min: 80, max: 124 }),
    start: 214,
  };
}

// damped landing squash: 1 at tau<=0, dips to 1-A on impact, springs back (hero ζ≈0.62)
function squash(lib, tau, A, spring) {
  if (tau < 0) return 1;
  const w = Math.sqrt(spring.stiffness), z = spring.damping / (2 * w), wd = w * Math.sqrt(1 - z * z);
  return 1 - A * Math.exp(-z * w * tau) * Math.cos(wd * tau);
}

// hero state as a pure function of t: { x, yb (bottom), sy, lookX, blink }
const HOPS = [[2.42, 2.72, 0], [2.92, 3.22, 1], [3.42, 3.72, 2]];   // [takeoff, landing, target prop]
function heroAt(t, lib, tokens) {
  const sp = tokens.ease.spring;
  const topOf = (k) => GROUND - L.props[k].h * propScale(t, lib, k) * propDip(t, k);
  let x = L.start, yb = GROUND, sy = 1, from = -1;
  // intro drop: falls from above, lands at 0.46
  if (t < 0.46) { const u = lib.clamp((t - 0.16) / 0.3); yb = lib.lerp(-200, GROUND, u * u); sy = t < 0.16 ? 1 : 1.18; }
  else sy = squash(lib, t - 0.46, 0.32, sp);
  for (const [t0, t1, k] of HOPS) {
    const fx = from < 0 ? L.start : L.s[from].x, fy = from < 0 ? GROUND : topOf(from);
    const tx = L.s[k].x, ty = topOf(k);
    if (t >= t1) { x = tx; yb = ty; sy = squash(lib, t - t1, 0.3, sp); from = k; continue; }
    if (t >= t0) {                                             // airborne: parabola, stretched along the motion
      const u = (t - t0) / (t1 - t0), hgt = 90;
      x = lib.lerp(fx, tx, u); yb = lib.lerp(fy, ty, u) - 4 * hgt * u * (1 - u);
      sy = 1 + 0.2 * Math.abs(1 - 2 * u) + 0.05; break;
    }
    if (t >= t0 - 0.2) {                                       // anticipation: squash to 0.85, hold, go
      x = fx; yb = fy; sy = 1 - 0.15 * lib.ease.outCubic(lib.clamp((t - (t0 - 0.2)) / 0.14)); break;
    }
    if (from >= 0) { x = fx; yb = fy; }
    break;
  }
  const next = HOPS.find((h) => t < h[1]);
  const lookX = next ? Math.sign(L.s[next[2]].x - x) * 6 : 0;
  const ts = lib.step(t, 12), blink = [1.24, 3.86].some((b) => ts >= b && ts < b + 0.17);
  return { x, yb, sy, lookX, blink };
}

function propScale(t, lib, k) { const t0 = 2.0 + k * 0.15; return lib.tween(t, t0, t0 + 0.32, lib.ease.outBack); }
function propDip(t, k) { const land = HOPS.find((hp) => hp[2] === k)[1]; return t >= land ? 1 - 0.07 * Math.exp(-(t - land) * 9) * Math.cos((t - land) * 24) : 1; }

export function renderAt(t, ctx, tokens, lib) {
  const h = heroAt(t, lib, tokens);
  const cx = h.x, cy = h.yb - L.hero.h / 2;
  lib.iris(ctx, lib.seg(t, 4.0, 4.55), (x) => stage(x, t, tokens, lib, h), (x) => end(x, t, tokens, lib),
    { cx, cy, mode: "open", ease: lib.ease.inCubic });
}

function stage(ctx, t, tokens, lib, h) {
  const { W, H, tween, ease } = lib;
  const P = (k) => lib.color(tokens, k);
  const INK = P("fg"), TOM = P("accent"), MUS = P("extra.0"), MINT = P("extra.1"), SKY = P("extra.2");
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);

  // sun + hill (flat colour blocks, pop with overshoot)
  const sun = tween(t, 0.22, 0.6, ease.outBack);
  if (sun > 0) { ctx.fillStyle = MUS; ctx.beginPath(); ctx.arc(1716, 150, 74 * sun, 0, lib.TAU); ctx.fill(); }
  const hill = tween(t, 0.1, 0.5, ease.outBack);
  if (hill > 0) { ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, GROUND); ctx.clip(); ctx.fillStyle = MINT; ctx.beginPath(); ctx.ellipse(170, GROUND, 330, 190 * hill, 0, 0, lib.TAU); ctx.fill(); ctx.restore(); }
  // ground line
  ctx.save(); ctx.strokeStyle = INK; ctx.lineWidth = 7; ctx.lineCap = "round";
  lib.strokePartial(ctx, [[0, GROUND], [W, GROUND]], tween(t, 0.05, 0.45, ease.outCubic)); ctx.restore();

  // ── title: letters fall and squash on landing (45 ms stagger)
  const TS = L.titleSize;
  lib.setFont(ctx, tokens, "display", TS, { weight: 700 }); ctx.fillStyle = INK;
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: W / 2, y: 236, align: "center", tracking: -0.01 * TS });
  const sp = tokens.ease.spring;
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const t0 = 0.84 + i * 0.045, tl = t0 + 0.14;
    if (t < t0) return null;
    if (t < tl) { const u = (t - t0) / 0.14; return { dy: -140 * (1 - u * u), sx: 0.9, sy: 1.14 }; }
    const s = squash(lib, t - tl, 0.3, sp);
    return { sx: 1 / s, sy: s };
  });
  // Chinese: pop with overshoot (70 ms stagger), anchored at the baseline
  lib.setFont(ctx, tokens, "zh", 72, { weight: 600 }); ctx.fillStyle = TOM;
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 336, align: "center", tracking: 0.06 * 72 });
  lib.drawGlyphs(ctx, zl, (g, i) => {
    const s = tween(t, 1.52 + i * 0.07, 1.84 + i * 0.07, ease.outBack);
    return s <= 0 ? null : { scale: s, dy: 0 };
  });

  // ── the three props (pop out of the ground, dip when the hero lands)
  const cols = [MUS, SKY, MINT];
  L.s.forEach((c, k) => {
    const s = propScale(t, lib, k);
    if (s <= 0) return;
    const dip = propDip(t, k);
    const { w, h: hh } = L.props[k], sy = s * dip, sx = 1 / Math.max(0.6, dip);
    ctx.save(); ctx.translate(c.x, GROUND); ctx.scale(sx, sy);
    ctx.fillStyle = cols[k]; ctx.beginPath(); ctx.roundRect(-w / 2, -hh, w, hh, 26); ctx.fill();
    // icon, flat, in ink / cream
    ctx.fillStyle = k === 1 ? P("bg") : INK; ctx.strokeStyle = INK; ctx.lineCap = "round";
    if (k === 0) { ctx.lineWidth = 13; for (let r = 0; r < 3; r++) { ctx.beginPath(); ctx.moveTo(-72, -hh + 38 + r * 32); ctx.lineTo(r === 2 ? 20 : 72, -hh + 38 + r * 32); ctx.stroke(); } }
    else if (k === 1) { for (let r = 0; r < 3; r++) { ctx.beginPath(); ctx.roundRect(-102 + r * 70, -hh + 36, 58, 78, 10); ctx.fill(); } }
    else { ctx.fillStyle = P("bg"); ctx.beginPath(); ctx.moveTo(-30, -hh + 40); ctx.lineTo(44, -hh + 80); ctx.lineTo(-30, -hh + 120); ctx.closePath(); ctx.fill(); }
    ctx.restore();
    // labels under the ground line
    const a = lib.seg(t, 2.12 + k * 0.15, 2.36 + k * 0.15);
    if (a > 0) {
      ctx.save(); ctx.globalAlpha = a;
      lib.setFont(ctx, tokens, "display", 40, { weight: 700 }); ctx.fillStyle = INK;
      lib.drawText(ctx, lib.MOTIF[k].en, c.x, GROUND + 62 + (1 - a) * 14, { align: "center" });
      lib.setFont(ctx, tokens, "zh", 52, { weight: 600 });
      lib.drawText(ctx, lib.MOTIF[k].zh, c.x, GROUND + 130 + (1 - a) * 14, { align: "center", tracking: 0.1 * 52 });
      ctx.restore();
    }
  });

  hero(ctx, t, tokens, lib, h);
}

function hero(ctx, t, tokens, lib, h) {
  if (t < 0.16) return;
  const P = (k) => lib.color(tokens, k);
  const { w, h: hh } = L.hero, sx = 1 / h.sy;
  ctx.save(); ctx.translate(h.x, h.yb); ctx.scale(sx, h.sy);           // anchor at the feet: area preserved
  ctx.fillStyle = P("accent"); ctx.beginPath(); ctx.roundRect(-w / 2, -hh, w, hh, [w / 2, w / 2, 26, 26]); ctx.fill();
  // face (12 fps): two tall eyes looking toward the next jump, small smile
  const ex = h.lookX, ey = -hh + 64;
  ctx.fillStyle = P("fg");
  for (const s of [-1, 1]) {
    ctx.beginPath();
    if (h.blink) ctx.roundRect(s * 24 + ex - 10, ey - 2, 20, 6, 3); else ctx.ellipse(s * 24 + ex, ey, 9, 17, 0, 0, lib.TAU);
    ctx.fill();
  }
  ctx.strokeStyle = P("fg"); ctx.lineWidth = 5; ctx.lineCap = "round";
  ctx.beginPath(); ctx.arc(ex, ey + 26, 15, 0.2 * Math.PI, 0.8 * Math.PI); ctx.stroke();
  ctx.restore();
}

function end(ctx, t, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  ctx.fillStyle = P("accent"); ctx.fillRect(0, 0, W, H);
  const s = lib.tween(t, 4.42, 4.72, lib.ease.outBack);
  if (s <= 0) return;
  ctx.save(); ctx.translate(W / 2, 560); ctx.scale(s, s);
  lib.setFont(ctx, tokens, "display", 128, { weight: 700 }); ctx.fillStyle = P("bg");
  lib.drawText(ctx, "Bouncy Flat 2D", 0, 0, { align: "center", tracking: -0.01 * 128 });
  lib.setFont(ctx, tokens, "zh", 60, { weight: 600 }); ctx.fillStyle = P("fg");
  lib.drawText(ctx, "弹性扁平 2D", 0, 100, { align: "center", tracking: 0.06 * 60 });
  ctx.restore();
}
