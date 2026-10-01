// bouncy-flat-2d swatch: flat shapes that act, on a cream stage.
//   0.0–0.8  the ground line draws, a mint hill and a mustard sun pop in, the tomato hero drops in and squashes
//   0.8–2.6  title letters fall one by one and squash on landing; Chinese characters pop with a small overshoot
//   2.0–2.4  outline → storyboard → draft pop out of the ground as three flat props
//   2.3–3.8  the hero hops across them: anticipation, stretched arc, squash on each landing, the prop dips under it
//   4.0–4.55 shape wipe: a tomato circle grows out of the hero and becomes the end frame
// Positions and squash are continuous; blinks and the hero's face change on 12 fps steps (limited animation).

let L = null;
const GROUND = 842, PK = 1.4, HK = 1.4, LEAP0 = 4.0, LEAP1 = 4.34;   // ground at 0.78 H; props and hero drawn 1.4×

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
// ONE timing table for the drawing and the foley (EVENTS → events.json is generated from this module)
export const TL = { hill: 0.03, sun: 0.2, drop: [0.1, 0.5], letter0: 0.84, stag: 0.045, fall: 0.14, zh0: 1.52, zhStag: 0.07, prop: (k) => 2.0 + k * 0.15, name: 4.4 };
const PROP_X = [448, 960, 1472], START_X = 214;                             // lib.slots(3, SAFE.title) centres
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;   // pan = (2x/W − 1) · 0.7
const TITLE = "Every frame is code.";                                          // = lib.TITLE_EN (glyph index i counts spaces, as drawGlyphs does)
const wordIdx = (str) => [...str].flatMap((ch, i) => (ch !== " " && (i === 0 || str[i - 1] === " ") ? [i] : []));
export const FOLEY = [
  { t: TL.hill + 0.1, sfx: "pop", gain_db: -8, pan: pan(250) },                         // the hill pops up
  { t: TL.sun + 0.12, sfx: "pop", gain_db: -12, pan: pan(1716) },                       // the sun pops in
  { t: TL.drop[1], sfx: "impact", gain_db: -10, pan: pan(START_X) },                     // the hero lands (with the score's clap)
  ...wordIdx(TITLE).map((i) => ({ t: TL.letter0 + i * TL.stag + TL.fall, sfx: "pop", gain_db: -16, pan: pan(960 + (i / (TITLE.length - 1) - 0.5) * 1240) })),   // first letter of each word lands
  ...PROP_X.map((x, k) => ({ t: TL.prop(k) + 0.12, sfx: "pop", gain_db: -10, pan: pan(x) })),    // props pop out of the ground
  ...HOPS.map(([t0, t1, k]) => ({ t: (t0 + t1) / 2, sfx: "whip", gain_db: -15, pan: pan(PROP_X[k]), dur: t1 - t0, dir: "up", pan_from: pan(k ? PROP_X[k - 1] : START_X), pan_to: pan(PROP_X[k]) })),   // air (a whip peaks mid-hop)
  ...HOPS.map(([, t1, k]) => ({ t: t1, sfx: "pop", gain_db: -6, pan: pan(PROP_X[k]) })),           // landing squash
  { t: LEAP0 + 0.1, sfx: "whip", gain_db: -8, pan: pan(PROP_X[2]), dur: LEAP1 - LEAP0, dir: "up", pitch: -3 },                  // the leap at the lens
  { t: LEAP1, sfx: "impact", gain_db: -8 },                                             // the body fills the frame
  { t: TL.name + 0.1, sfx: "ding", gain_db: -14 },                                      // conclusion: the name
];
function heroAt(t, lib, tokens) {
  const sp = tokens.ease.spring;
  const topOf = (k) => GROUND - PK * L.props[k].h * propScale(t, lib, k) * propDip(t, k);
  let x = L.start, yb = GROUND, sy = 1, from = -1;
  // intro drop: falls from above, lands at 0.46
  if (t < TL.drop[1]) { const u = lib.seg(t, ...TL.drop); yb = lib.lerp(-300, GROUND, u * u); sy = t < TL.drop[0] ? 1 : 1.3; }   // falls in, stretched
  else sy = squash(lib, t - TL.drop[1], 0.34, sp);                                  // lands on the 0.5 s beat (clap)
  for (const [t0, t1, k] of HOPS) {
    const fx = from < 0 ? L.start : L.s[from].x, fy = from < 0 ? GROUND : topOf(from);
    const tx = L.s[k].x, ty = topOf(k);
    if (t >= t1) { x = tx; yb = ty; sy = squash(lib, t - t1, 0.3, sp); from = k; continue; }
    if (t >= t0) {                                             // airborne: parabola, stretched along the motion
      const u = (t - t0) / (t1 - t0), hgt = 70;
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
  if (t >= 3.86 && t < LEAP0) sy = 1 - 0.2 * lib.ease.outCubic(lib.seg(t, 3.86, 3.96));   // anticipation before the leap
  const ts = lib.step(t, 12), blink = [1.24, 3.86].some((b) => ts >= b && ts < b + 0.17);
  return { x, yb, sy, lookX, blink };
}

function propScale(t, lib, k) { const t0 = TL.prop(k); return lib.tween(t, t0, t0 + 0.32, lib.ease.outBack); }
function propDip(t, k) { const land = HOPS.find((hp) => hp[2] === k)[1]; return t >= land ? 1 - 0.07 * Math.exp(-(t - land) * 9) * Math.cos((t - land) * 24) : 1; }

export function renderAt(t, ctx, tokens, lib) {
  const h = heroAt(t, lib, tokens);
  if (t >= LEAP1) return end(ctx, t, tokens, lib);                          // the hero's body now fills the frame
  stage(ctx, t, tokens, lib, h, t < LEAP0);
  if (t >= LEAP0) leap(ctx, t, tokens, lib, h);
}

// ending: the hero springs off the draft prop straight at the lens; a smear of its own body leads, then it fills the frame
function leap(ctx, t, tokens, lib, h) {
  const u = lib.seg(t, LEAP0, LEAP1), S = 1 + 13 * Math.pow(u, 2.1);
  const x0 = h.x, y0 = h.yb - (L.hero.h * HK) / 2;
  const cx = lib.lerp(x0, 960, lib.ease.inOutSine(u)), cy = lib.lerp(y0, 560, lib.ease.outCubic(u)) - 140 * Math.sin(Math.PI * Math.min(1, u * 1.6));
  const stretch = 1 + 0.35 * Math.sin(Math.PI * Math.min(1, u * 1.4));
  if (u > 0.08 && u < 0.6) for (const [f, a] of [[0.55, 0.3], [0.72, 0.45], [0.87, 0.65]]) {     // smear frames
    const q = Math.max(0, u - (1 - f) * 0.25), Sq = 1 + 13 * Math.pow(q, 2.1);
    const qx = lib.lerp(x0, 960, lib.ease.inOutSine(q)), qy = lib.lerp(y0, 560, lib.ease.outCubic(q)) - 140 * Math.sin(Math.PI * Math.min(1, q * 1.6));
    ctx.save(); ctx.globalAlpha = a; body(ctx, tokens, lib, qx, qy, Sq * HK, stretch, null); ctx.restore();
  }
  body(ctx, tokens, lib, cx, cy, S * HK, stretch, h);
}
function body(ctx, tokens, lib, cx, cy, sc, stretch, face) {
  const P = (k) => lib.color(tokens, k), { w, h: hh } = L.hero;
  ctx.save(); ctx.translate(cx, cy); ctx.scale(sc / stretch ** 0.5, sc * stretch);
  ctx.fillStyle = P("accent"); ctx.beginPath(); ctx.roundRect(-w / 2, -hh / 2, w, hh, [w / 2, w / 2, 26, 26]); ctx.fill();
  if (face) {
    ctx.fillStyle = P("fg");
    for (const s of [-1, 1]) { ctx.beginPath(); ctx.ellipse(s * 24, -hh / 2 + 64, 9, 17, 0, 0, lib.TAU); ctx.fill(); }
    ctx.strokeStyle = P("fg"); ctx.lineWidth = 5; ctx.lineCap = "round"; ctx.beginPath(); ctx.arc(0, -hh / 2 + 88, 18, 0.1 * Math.PI, 0.9 * Math.PI); ctx.stroke();
  }
  ctx.restore();
}

function stage(ctx, t, tokens, lib, h, showHero = true) {
  const { W, H, tween, ease } = lib;
  const P = (k) => lib.color(tokens, k);
  const INK = P("fg"), TOM = P("accent"), MUS = P("extra.0"), MINT = P("extra.1"), SKY = P("extra.2");
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);

  // sun + hill (flat colour blocks, pop with overshoot)
  const sun = tween(t, TL.sun, TL.sun + 0.32, ease.outBack);
  if (sun > 0) { ctx.fillStyle = MUS; ctx.beginPath(); ctx.arc(1716, 150, 74 * sun, 0, lib.TAU); ctx.fill(); }
  const hill = tween(t, TL.hill, TL.hill + 0.33, ease.outBack);                           // the hook: a big hill pops up on frame 1–10
  if (hill > 0) { ctx.save(); ctx.beginPath(); ctx.rect(0, 0, W, GROUND); ctx.clip(); ctx.fillStyle = MINT; ctx.beginPath(); ctx.ellipse(250, GROUND, 620 * Math.min(1, 0.6 + 0.4 * hill), 330 * hill, 0, 0, lib.TAU); ctx.fill(); ctx.restore(); }
  // ground line
  ctx.save(); ctx.strokeStyle = INK; ctx.lineWidth = 7; ctx.lineCap = "round";
  lib.strokePartial(ctx, [[0, GROUND], [W, GROUND]], tween(t, 0.05, 0.45, ease.outCubic)); ctx.restore();

  // ── title: letters fall and squash on landing (45 ms stagger)
  const TS = L.titleSize;
  lib.setFont(ctx, tokens, "display", TS, { weight: 700 }); ctx.fillStyle = INK;
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: W / 2, y: 200, align: "center", tracking: -0.01 * TS });
  const sp = tokens.ease.spring;
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const t0 = TL.letter0 + i * TL.stag, tl = t0 + TL.fall;
    if (t < t0) return null;
    if (t < tl) { const u = (t - t0) / 0.14; return { dy: -140 * (1 - u * u), sx: 0.9, sy: 1.14 }; }
    const s = squash(lib, t - tl, 0.3, sp);
    return { sx: 1 / s, sy: s };
  });
  // Chinese: pop with overshoot (70 ms stagger), anchored at the baseline
  lib.setFont(ctx, tokens, "zh", 72, { weight: 600 }); ctx.fillStyle = TOM;
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: 292, align: "center", tracking: 0.06 * 72 });
  lib.drawGlyphs(ctx, zl, (g, i) => {
    const s = tween(t, TL.zh0 + i * TL.zhStag, TL.zh0 + 0.32 + i * TL.zhStag, ease.outBack);
    return s <= 0 ? null : { scale: s, dy: 0 };
  });

  // ── the three props (pop out of the ground, dip when the hero lands)
  const cols = [MUS, SKY, MINT];
  L.s.forEach((c, k) => {
    const s = propScale(t, lib, k);
    if (s <= 0) return;
    const dip = propDip(t, k);
    const { w, h: hh } = L.props[k], sy = s * dip, sx = 1 / Math.max(0.6, dip);
    ctx.save(); ctx.translate(c.x, GROUND); ctx.scale(sx * PK, sy * PK);
    ctx.fillStyle = cols[k]; ctx.beginPath(); ctx.roundRect(-w / 2, -hh, w, hh, 26); ctx.fill();
    // icon, flat, in ink / cream
    ctx.fillStyle = k === 1 ? P("bg") : INK; ctx.strokeStyle = INK; ctx.lineCap = "round";
    if (k === 0) { ctx.lineWidth = 13; for (let r = 0; r < 3; r++) { ctx.beginPath(); ctx.moveTo(-72, -hh + 38 + r * 32); ctx.lineTo(r === 2 ? 20 : 72, -hh + 38 + r * 32); ctx.stroke(); } }
    else if (k === 1) { for (let r = 0; r < 3; r++) { ctx.beginPath(); ctx.roundRect(-102 + r * 70, -hh + 36, 58, 78, 10); ctx.fill(); } }
    else {                                                                   // draft: a finished little picture (sun over a hill)
      ctx.fillStyle = P("bg"); ctx.beginPath(); ctx.roundRect(-84, -hh + 26, 168, 110, 12); ctx.fill();
      ctx.save(); ctx.beginPath(); ctx.roundRect(-84, -hh + 26, 168, 110, 12); ctx.clip();
      ctx.fillStyle = SKY; ctx.beginPath(); ctx.moveTo(-96, -hh + 140); ctx.lineTo(-24, -hh + 70); ctx.lineTo(40, -hh + 140); ctx.closePath(); ctx.fill();
      ctx.fillStyle = MUS; ctx.beginPath(); ctx.moveTo(0, -hh + 140); ctx.lineTo(50, -hh + 92); ctx.lineTo(100, -hh + 140); ctx.closePath(); ctx.fill();
      ctx.fillStyle = TOM; ctx.beginPath(); ctx.arc(44, -hh + 58, 16, 0, lib.TAU); ctx.fill(); ctx.restore();
    }
    ctx.restore();
    // labels under the ground line
    const a = lib.seg(t, TL.prop(k) + 0.12, TL.prop(k) + 0.36);
    if (a > 0) {
      ctx.save(); ctx.globalAlpha = a;
      lib.setFont(ctx, tokens, "display", 40, { weight: 700 }); ctx.fillStyle = INK;
      lib.drawText(ctx, lib.MOTIF[k].en, c.x, GROUND + 62 + (1 - a) * 14, { align: "center" });
      lib.setFont(ctx, tokens, "zh", 52, { weight: 600 });
      lib.drawText(ctx, lib.MOTIF[k].zh, c.x, GROUND + 130 + (1 - a) * 14, { align: "center", tracking: 0.1 * 52 });
      ctx.restore();
    }
  });

  if (showHero) hero(ctx, t, tokens, lib, h);
}

function hero(ctx, t, tokens, lib, h) {
  if (t < TL.drop[0]) return;
  const P = (k) => lib.color(tokens, k);
  const { w, h: hh } = L.hero, sx = 1 / h.sy;
  ctx.save(); ctx.translate(h.x, h.yb); ctx.scale(sx * HK, h.sy * HK);           // anchor at the feet: area preserved
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
  const s = lib.tween(t, TL.name, TL.name + 0.3, lib.ease.outBack);
  if (s <= 0) return;
  ctx.save(); ctx.translate(W / 2, 560); ctx.scale(s, s);
  lib.setFont(ctx, tokens, "display", 128, { weight: 700 }); ctx.fillStyle = P("bg");
  lib.drawText(ctx, "Bouncy Flat 2D", 0, 0, { align: "center", tracking: -0.01 * 128 });
  lib.setFont(ctx, tokens, "zh", 60, { weight: 600 }); ctx.fillStyle = P("fg");
  lib.drawText(ctx, "弹性扁平 2D", 0, 100, { align: "center", tracking: 0.06 * 60 });
  ctx.restore();
}
