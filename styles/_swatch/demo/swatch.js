// Demo swatch: a neutral reference that exercises the scene API and follows the shared content spec.
// Not a style preset. Copy it as a starting point: styles/<slug>/swatch.js + tokens.json.
//
//   0.0–0.8  paper, grid rules draw on, grain            (establish)
//   0.8–2.6  title glyphs spring up; Chinese line decodes  (signature type animation)
//   2.0–4.0  outline → storyboard → draft cards + arrows   (motif)
//   4.0–5.0  iris closes on the draft card → end frame     (signature transition)

let L = null;   // layout computed once in setup (pure data: identical in every worker)

export async function setup(ctx, tokens, lib) {
  const { SAFE, W, H } = lib;
  lib.setFont(ctx, tokens, "display", 10);
  const size = lib.fitText(ctx, lib.TITLE_EN, 1320, (s) => lib.setFont(ctx, tokens, "display", s), { min: 60, max: 132 });
  const cards = lib.slots(3, { area: SAFE.title, y: 700, gap: 120 });
  L = { size, titleY: 330, zhY: 462, zhSize: 64, cards, cardW: 330, cardH: 220, barY: H - 78, W };
}

export function renderAt(t, ctx, tokens, lib) {
  const { seg, W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const c = L.cards[2];
  if (t < 4.0) main(ctx, t, tokens, lib);
  else lib.iris(ctx, seg(t, 4.0, 4.6), (x) => main(x, t, tokens, lib), (x) => end(x, t, tokens, lib),
    { cx: c.x, cy: L.cards[2].y, mode: "close", ease: lib.easeOf(tokens.motion.move) });
  // post: same texture over everything, including the end frame
  lib.grain(ctx, t, { amount: tokens.texture.grain, fps: 24, seed: 11 });
  lib.vignette(ctx, { strength: tokens.texture.vignette, inner: 0.5, color: P("ink") });
}

function main(ctx, t, tokens, lib) {
  const { SAFE, W, H, seg, clamp, tween, spring } = lib;
  const P = (k) => lib.color(tokens, k);
  const enter = lib.easeOf(tokens.motion.enter);

  // ── establish: paper + 6×6 grid rules drawing on, then settling back
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  lib.paper(ctx, { tone: P("bg"), amount: tokens.texture.paper, blotch: 0.05, fiber: 0.6, seed: 4 });
  const A = SAFE.action;
  ctx.save();
  ctx.strokeStyle = P("rule"); ctx.lineWidth = 1.5; ctx.globalAlpha = 1 - 0.6 * seg(t, 0.8, 1.4);
  for (let i = 1; i < 6; i++) {
    const u = enter(seg(t, 0.1 + i * 0.05, 0.6 + i * 0.05));
    lib.strokePartial(ctx, [[A.x0 + i * A.w / 6, A.y0], [A.x0 + i * A.w / 6, A.y1]], u);
    lib.strokePartial(ctx, [[A.x0, A.y0 + i * A.h / 6], [A.x1, A.y0 + i * A.h / 6]], u);
  }
  ctx.restore();

  // corner labels (mono)
  ctx.save();
  lib.setFont(ctx, tokens, "mono", 22); ctx.fillStyle = P("muted"); ctx.globalAlpha = lib.env(t, 0.15, 99, 0.3, 0);
  lib.drawText(ctx, "STYLE SWATCH · DEMO", A.x0, A.y0 + 40, { tracking: 2.5 });
  lib.drawText(ctx, `t ${t.toFixed(2)}  f ${String(lib.frame(t)).padStart(3, "0")}`, A.x1, A.y0 + 40, { align: "right", tracking: 1 });
  ctx.restore();

  // ── title: per-glyph spring rise
  lib.setFont(ctx, tokens, "display", L.size); ctx.fillStyle = P("ink");
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: W / 2, y: L.titleY, align: "center", tracking: lib.tracking(tokens, "display", L.size) });
  const st = tokens.motion.stagger;
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const t0 = 0.85 + i * st;
    if (t < t0) return null;
    const p = spring(t - t0, tokens.motion.spring);
    return { dy: (1 - p) * 70, alpha: clamp((t - t0) / 0.12) };
  });
  // accent rule under "code."
  const g0 = lay.glyphs[lay.glyphs.length - 5], gN = lay.glyphs[lay.glyphs.length - 1];
  ctx.save(); ctx.strokeStyle = P("accent"); ctx.lineWidth = 10; ctx.lineCap = "butt";
  lib.strokePartial(ctx, [[g0.x, L.titleY + 26], [gN.x + gN.w, L.titleY + 26]], tween(t, 1.75, 2.25, lib.ease.outCubic));
  ctx.restore();

  // ── Chinese line: seeded decode, quantized to 15 flips per second
  lib.setFont(ctx, tokens, "zh", L.zhSize);
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: W / 2, y: L.zhY, align: "center", tracking: lib.tracking(tokens, "zh", L.zhSize) });
  const sg = lib.scrambleGlyphs(lib.TITLE_ZH, t, { start: 1.35, stagger: 0.055, settle: 0.3, rate: 15, seed: 7 });
  lib.drawGlyphs(ctx, zl, (g, i) => sg[i].state === "hidden" ? null
    : { ch: sg[i].ch, fill: sg[i].state === "done" ? P("ink") : P("accent"), alpha: sg[i].state === "done" ? 1 : 0.85 });

  // ── motif: outline → storyboard → draft
  L.cards.forEach((c, k) => card(ctx, t, tokens, lib, c, k));
  for (let k = 0; k < 2; k++) {                          // arrows between cards
    const a = L.cards[k], b = L.cards[k + 1], t0 = 2.55 + k * 0.18, u = tween(t, t0, t0 + 0.4, lib.ease.outCubic);
    if (u <= 0) continue;
    const x0 = a.x + L.cardW / 2 + 18, x1 = b.x - L.cardW / 2 - 18, y = a.y;
    ctx.save(); ctx.strokeStyle = P("ink"); ctx.lineWidth = 4; ctx.lineCap = "round";
    lib.strokePartial(ctx, [[x0, y], [x1, y]], u);
    if (u > 0.9) { ctx.beginPath(); ctx.moveTo(x1 - 16, y - 12); ctx.lineTo(x1, y); ctx.lineTo(x1 - 16, y + 12); ctx.stroke(); }
    ctx.restore();
  }

  // ── content-spec ruler (teaching aid for preset authors)
  timeline(ctx, t, tokens, lib);
}

function card(ctx, t, tokens, lib, c, k) {
  const P = (n) => lib.color(tokens, n);
  const t0 = 2.0 + k * 0.16, p = lib.tween(t, t0, t0 + 0.55, tokens.motion.enter);
  if (p <= 0) return;
  const w = L.cardW, h = L.cardH, x = c.x - w / 2, y = c.y - h / 2 + (1 - p) * 60;
  ctx.save(); ctx.globalAlpha = p;
  ctx.fillStyle = lib.rgba(P("bg"), 0.92); ctx.strokeStyle = P("ink"); ctx.lineWidth = 4;
  ctx.beginPath(); ctx.roundRect(x, y, w, h, 18); ctx.fill(); ctx.stroke();
  const q = lib.tween(t, t0 + 0.2, t0 + 0.7, lib.ease.outCubic);   // icon draws on inside the card
  ctx.strokeStyle = P("ink"); ctx.fillStyle = P("ink"); ctx.lineWidth = 6; ctx.lineCap = "round";
  const ix = x + 44, iy = y + 44, iw = w - 88, ih = h - 88;
  if (k === 0) {                                          // outline: three bullet lines
    for (let r = 0; r < 3; r++) {
      const ly = iy + 16 + r * (ih - 32) / 2, u = lib.clamp(q * 3 - r);
      if (u <= 0) continue;
      ctx.beginPath(); ctx.arc(ix + 6, ly, 6, 0, lib.TAU); ctx.fill();
      lib.strokePartial(ctx, [[ix + 34, ly], [ix + 34 + (iw - 34) * (r === 2 ? 0.6 : 1), ly]], u);
    }
  } else if (k === 1) {                                   // storyboard: 3 panels
    for (let r = 0; r < 3; r++) {
      const u = lib.clamp(q * 3 - r); if (u <= 0) continue;
      const pw = (iw - 2 * 18) / 3; ctx.globalAlpha = p * u; ctx.lineWidth = 4;
      ctx.strokeRect(ix + r * (pw + 18), iy + 14, pw, ih - 28);
    }
  } else {                                                // draft: frame + play triangle (accent)
    ctx.lineWidth = 4; ctx.globalAlpha = p * q; ctx.strokeRect(ix, iy, iw, ih);
    ctx.fillStyle = P("accent"); ctx.beginPath();
    const cx = ix + iw / 2, cy = iy + ih / 2, s = 30 * lib.spring(t - t0 - 0.35, { w: 18, zeta: 0.6 });
    ctx.moveTo(cx - s * 0.8, cy - s); ctx.lineTo(cx + s, cy); ctx.lineTo(cx - s * 0.8, cy + s); ctx.closePath(); ctx.fill();
  }
  ctx.globalAlpha = p;
  lib.setFont(ctx, tokens, "display", 34, { weight: 500 }); ctx.fillStyle = P("ink");
  lib.drawText(ctx, lib.MOTIF[k].en, c.x, y + h + 58, { align: "center" });
  lib.setFont(ctx, tokens, "zh", 28, { weight: 400 }); ctx.fillStyle = P("muted");
  lib.drawText(ctx, lib.MOTIF[k].zh, c.x, y + h + 100, { align: "center", tracking: 4 });
  ctx.restore();
}

function timeline(ctx, t, tokens, lib) {
  const P = (n) => lib.color(tokens, n);
  const A = lib.SAFE.action, y = L.barY, X = (s) => lib.lerp(A.x0, A.x1, s / lib.DUR);
  const a = lib.env(t, 0.3, 99, 0.4, 0);
  if (a <= 0) return;
  ctx.save(); ctx.globalAlpha = a * 0.9;
  lib.setFont(ctx, tokens, "mono", 16);
  const S = lib.SPEC;
  [["establish", S.establish], ["title", S.title], ["motif", S.motif], ["outro", S.outro]].forEach(([n, [s0, s1]], i) => {
    const row = y - (i % 2) * 30;                         // overlapping segments alternate between two rows
    ctx.fillStyle = i === 2 ? P("accent") : P("muted");
    ctx.fillRect(X(s0), row, X(s1) - X(s0) - 4, 2);
    lib.drawText(ctx, `${n} ${s0.toFixed(1)}–${s1.toFixed(1)}`, X(s0), row - 8);
  });
  ctx.fillStyle = P("ink"); ctx.fillRect(X(S.poster) - 1, y - 58, 2, 64);
  lib.drawText(ctx, "poster 3.0", X(S.poster) + 8, y - 46);
  ctx.fillStyle = P("accent"); ctx.beginPath(); ctx.arc(X(t), y + 1, 7, 0, lib.TAU); ctx.fill();
  ctx.restore();
}

function end(ctx, t, tokens, lib) {
  const { W, H } = lib;
  const P = (n) => lib.color(tokens, n);
  ctx.fillStyle = P("ink"); ctx.fillRect(0, 0, W, H);
  const a = lib.tween(t, 4.45, 4.85, tokens.motion.enter);
  ctx.save(); ctx.globalAlpha = a;
  lib.setFont(ctx, tokens, "display", 96); ctx.fillStyle = P("bg");
  lib.drawText(ctx, "demo", W / 2, H / 2 + 10, { align: "center", tracking: lib.tracking(tokens, "display", 96) });
  ctx.fillStyle = P("accent"); ctx.beginPath(); ctx.arc(W / 2 + 150, H / 2 - 8, 12, 0, lib.TAU); ctx.fill();
  lib.setFont(ctx, tokens, "mono", 24); ctx.fillStyle = P("muted");
  lib.drawText(ctx, "OpenVideoHarness · style swatch", W / 2, H / 2 + 80, { align: "center", tracking: 2 });
  ctx.restore();
}
