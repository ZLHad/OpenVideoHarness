// canvas-film · transitions: how a shot comes in (its tin: a name, or [name, seconds]). The new shot starts its own clock
// at its cue and the old one keeps running under it until the transition ends. Each frame draws both in full (into
// offscreen buffers where a transition needs the whole picture of one), so nothing carries over from frame to frame.
// draw(p, n, t, v): p and n index SHOT_T (the old and the new shot), v goes 0 → 1 over the transition.
const TRANSITIONS = {
  cut: { d: 0 },
  // a cut that lands moving: the new shot settles from 1.06x to its size (no double exposure)
  settle: { d: 0.5, draw(p, n, t, v) {
    const k = lerp(1.06, 1, eOut(v));
    X.save(); X.translate(W / 2, H / 2); X.scale(k, k); X.translate(-W / 2, -H / 2); drawShot(n, t); X.restore();
  } },
  // down to dark and up into the new shot
  dim: { d: 1.0, draw(p, n, t, v) {
    if (v < 0.5) { drawShot(p, t); shade(eIn(v * 2), FILM.ui.dark); } else { drawShot(n, t); shade(1 - eOut((v - 0.5) * 2), FILM.ui.dark); }
  } },
  // the old shot swings away about its left edge, like a panel; the new one lies under it
  fold: { d: 0.85, draw(p, n, t, v) {
    const [A] = buffers(); renderTo(A, p, t);
    drawShot(n, t); shade(0.45 * (1 - eOut(v)));
    leaf(A, 0, W, eInOut(v) * Math.PI / 2 * 0.98, (r) => r, 1, 1, 0.7);
  } },
  // a book page: the right half of the old shot turns over to the left; its back is the new shot's left half
  turn: { d: 1.0, draw(p, n, t, v) {
    const [A, B] = buffers(); renderTo(A, p, t); renderTo(B, n, t);
    const ph = eInOut(v) * Math.PI;
    X.save(); X.beginPath(); X.rect(0, 0, W / 2, H); X.clip(); blit(A); X.restore();
    X.save(); X.beginPath(); X.rect(W / 2, 0, W / 2, H); X.clip(); blit(B); shade(0.35 * (1 - eOut(v))); X.restore();
    if (ph < Math.PI / 2) leaf(A, W / 2, W / 2, ph, (r) => W / 2 + r, 1, -1, 0.5);
    else leaf(B, W / 2, W / 2, ph, (r) => W / 2 - r, 1, -1, 0.5);
  } },
  // ink spreads from a few points over the old shot and opens onto the new one, soft-edged
  blot: { d: 1.2, draw(p, n, t, v) {
    const [, B, M] = buffers(); renderTo(B, n, t);
    drawShot(p, t);
    const path = blotPath(v);
    X.save(); X.filter = `blur(${10 * PRX}px)`; X.strokeStyle = `rgba(${FILM.ui.dark},0.45)`; X.lineWidth = 26; X.stroke(path); X.restore();
    const g = M.getContext("2d");
    g.reset(); g.setTransform(PRX, 0, 0, PRX, 0, 0); g.filter = `blur(${12 * PRX}px)`; g.fillStyle = "#fff"; g.fill(path);
    g.filter = "none"; g.setTransform(1, 0, 0, 1, 0, 0); g.globalCompositeOperation = "source-in"; g.drawImage(B, 0, 0);
    blit(M);
  } },
};

// three offscreen frames, made once at the frame's size and redrawn in full whenever they are used
let BUF = null;
function buffers() {
  if (!BUF) BUF = [0, 1, 2].map(() => { const c = document.createElement("canvas"); c.width = Math.round(W * PRX); c.height = Math.round(H * PRX); return c; });
  return BUF;
}
function renderTo(cv, i, t) {   // shot i at t into the buffer cv
  const g = cv.getContext("2d"), keep = X;
  g.reset(); g.setTransform(PRX, 0, 0, PRX, 0, 0); X = g;
  try { drawShot(i, t); } finally { X = keep; }
  return cv;
}
function blit(cv, a = 1) { X.save(); X.globalAlpha *= a; X.drawImage(cv, 0, 0, W, H); X.restore(); }
// a vertical leaf of the picture cv hinged on the line x = hx, turned by phi (0 flat, π/2 edge-on), in perspective: a
// point r px from the hinge shows the source column src(r). dir +1: the leaf lies right of the hinge when flat, -1 left;
// away +1: it turns into the screen, -1 towards the viewer. 48 slices, darker as it turns.
function leaf(cv, hx, R, phi, src, dir, away, dark = 0.55, f = 2600) {
  const N = 48, c = Math.cos(phi), s = Math.sin(phi);
  const P = (r) => { const k = f / (f + away * r * s); return [W / 2 + (hx + dir * r * c - W / 2) * k, k]; };
  for (let i = 0; i < N; i++) {
    const ra = R * i / N, rb = R * (i + 1) / N, [xa, ka] = P(ra), [xb, kb] = P(rb), k = (ka + kb) / 2;
    const sa = src(ra), sb = src(rb), dw = Math.abs(xb - xa) + 0.8;   // + 0.8: neighbouring slices overlap, no seams
    if (dw < 0.9) continue;
    X.drawImage(cv, Math.min(sa, sb) * PRX, 0, Math.abs(sb - sa) * PRX, H * PRX, Math.min(xa, xb), H / 2 - H / 2 * k, dw, H * k);
  }
  const a = dark * (1 - Math.abs(c));
  if (a > 0.005) {
    const [x0, k0] = P(0), [x1, k1] = P(R);
    X.save(); X.fillStyle = `rgba(0,0,0,${a})`; X.beginPath();
    X.moveTo(x0, H / 2 - H / 2 * k0); X.lineTo(x1, H / 2 - H / 2 * k1); X.lineTo(x1, H / 2 + H / 2 * k1); X.lineTo(x0, H / 2 + H / 2 * k0);
    X.closePath(); X.fill(); X.restore();
  }
}
// the ink at v: 26 ragged blots with hashed centres, sizes and delays; from v = 0.55 a last one from the centre covers the frame
function blotPath(v) {
  const p = new Path2D();
  for (let i = 0; i < 26; i++) {
    const delay = hash2(901, i) * 0.55, g = clamp((v - delay) / (1 - delay));
    if (g <= 0) continue;
    const r = Math.pow(g, 0.85) * (380 + hash2(903, i) * 720), cx = hash2(905, i) * W, cy = hash2(907, i) * H;
    for (let k = 0; k <= 48; k++) {
      const a = k / 48 * TAU, rr = r * (0.88 + 0.16 * (0.6 * hash2(909 + i, Math.floor(k / 2) % 24) + 0.4 * Math.sin(a * 3 + i)));
      if (k) p.lineTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr); else p.moveTo(cx + Math.cos(a) * rr, cy + Math.sin(a) * rr);
    }
    p.closePath();
  }
  const g = seg(v, 0.55, 1);
  if (g > 0) { const r = 1500 * eIn(g) + 1; p.moveTo(W / 2 + r, H / 2); p.arc(W / 2, H / 2, r, 0, TAU); }
  return p;
}
