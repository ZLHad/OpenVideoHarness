// Hand-drawn strokes for the explainer-drawing swatches (whiteboard, chalkboard, gold-line-dark, era-media-relay).
// A stroke is a polyline that a hand draws in a set time. The hand does not move at one speed: it follows the
// minimum-jerk profile (Flash & Hogan 1985), slow off the mark, fastest in the middle, slowing into the end, so the
// pen head, the line's width and its sound all come from the same curve. Everything here is a pure function of t;
// prep() only resamples a path (call it in setup).
//
//   const st = prep([[x, y], …], { step: 4, wobble: 1.5, seed: 3 });   // resampled every 4 px, a little hand wobble
//   st.t0 = 1.2; st.dur = 0.4;                                           // or sequence(list, t0, { … })
//   drawStroke(ctx, st, t, (ctx, i, s, v) => { ctx.lineWidth = 8 - 2 * v; ctx.strokeStyle = ink; });
//   const h = pen(list, t, rest);                                        // where the pen head is, and whether it is down

const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const hash = (a, b) => { const s = Math.sin(a * 127.1 + b * 311.7) * 43758.5453; return s - Math.floor(s); };

/** minimum-jerk position (0..1 → 0..1) and its speed relative to the peak (0..1) */
export const mj = (u) => { u = clamp(u); return u * u * u * (10 - 15 * u + 6 * u * u); };
export const mjSpeed = (u) => { u = clamp(u); return 16 * u * u * (1 - u) * (1 - u); };   // 30u²(1-u)² / 1.875

/** Resample a polyline every `step` px, with a seeded low-frequency wobble across the line (a hand is not a ruler). */
export function prep(pts, { step = 4, wobble = 0, seed = 1, freq = 0.012, close = false } = {}) {
  const P = close ? [...pts, pts[0]] : pts;
  const out = [];
  for (let i = 0; i < P.length - 1; i++) {
    const [x0, y0] = P[i], [x1, y1] = P[i + 1];
    const n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / step));
    for (let k = 0; k < n; k++) out.push([x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n]);
  }
  out.push([...P[P.length - 1]]);
  const cum = [0];
  for (let i = 1; i < out.length; i++) cum.push(cum[i - 1] + Math.hypot(out[i][0] - out[i - 1][0], out[i][1] - out[i - 1][1]));
  if (wobble > 0) {
    // offset along the normal by a smooth noise of arclength (two octaves of value noise)
    const nz = (x) => { const i = Math.floor(x), f = x - i, s = f * f * (3 - 2 * f); return (hash(i, seed) * (1 - s) + hash(i + 1, seed) * s) * 2 - 1; };
    const w = out.map((_, i) => wobble * (nz(cum[i] * freq) + 0.4 * nz(cum[i] * freq * 3.1 + 17)));
    for (let i = 0; i < out.length; i++) {
      const a = out[Math.max(0, i - 1)], b = out[Math.min(out.length - 1, i + 1)];
      const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1;
      const taper = Math.min(1, cum[i] / 20, (cum[cum.length - 1] - cum[i]) / 20);   // ends stay where they were put
      out[i] = [out[i][0] - dy / l * w[i] * taper, out[i][1] + dx / l * w[i] * taper];
    }
    for (let i = 1; i < out.length; i++) cum[i] = cum[i - 1] + Math.hypot(out[i][0] - out[i - 1][0], out[i][1] - out[i - 1][1]);
  }
  return { pts: out, cum, len: cum[cum.length - 1], t0: 0, dur: 0.3 };
}

/** A polyline approximating an ellipse arc (a hand-drawn circle starts and ends a little past itself). */
export function ellipse(cx, cy, rx, ry, a0, a1, n = 64, rot = 0) {
  const c = Math.cos(rot), s = Math.sin(rot);
  return Array.from({ length: n + 1 }, (_, i) => {
    const a = a0 + (a1 - a0) * i / n, x = Math.cos(a) * rx, y = Math.sin(a) * ry;
    return [cx + x * c - y * s, cy + x * s + y * c];
  });
}

/** Give each stroke its time: it starts `gap` after the last one ends; the duration grows with length^0.6 (long lines
 * are drawn faster on average, as a hand does). opts: { gap, k, min, max } or a stroke's own .gap / .dur. */
export function sequence(list, t0, { gap = 0.08, k = 0.012, min = 0.08, max = 0.9 } = {}) {
  let t = t0;
  for (const st of list) {
    t += st.gap ?? 0;
    st.t0 = st.at ?? t;
    st.dur = st.fixed ?? clamp(k * Math.pow(st.len, 0.6), min, max);
    t = st.t0 + st.dur + gap;
  }
  return t;
}

/** share of the stroke's length drawn at t (0..1) */
export const drawn = (st, t) => mj((t - st.t0) / st.dur);

/** index in st.pts reached at arclength s (0..1) */
function indexAt(st, s) {
  const L = s * st.len, c = st.cum;
  let lo = 0, hi = c.length - 1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (c[m] <= L) lo = m; else hi = m - 1; }
  return lo;
}
/** point at arclength share s */
export function pointAt(st, s) {
  const i = indexAt(st, clamp(s)), c = st.cum, P = st.pts;
  if (i >= P.length - 1) return P[P.length - 1];
  const f = (s * st.len - c[i]) / Math.max(1e-6, c[i + 1] - c[i]);
  return [P[i][0] + (P[i + 1][0] - P[i][0]) * f, P[i][1] + (P[i + 1][1] - P[i][1]) * f];
}
/** when the hand passed arclength share s of the stroke (seconds) */
export function timeAtS(st, s) {
  let lo = 0, hi = 1;
  for (let k = 0; k < 18; k++) { const m = (lo + hi) / 2; if (mj(m) < s) lo = m; else hi = m; }
  return st.t0 + st.dur * (lo + hi) / 2;
}
/** the hand's speed (0..1 of its peak) when it passed arclength share s: invert the profile by bisection */
export function speedAtS(s) {
  let lo = 0, hi = 1;
  for (let k = 0; k < 18; k++) { const m = (lo + hi) / 2; if (mj(m) < s) lo = m; else hi = m; }
  return mjSpeed((lo + hi) / 2);
}

/**
 * Draw the stroke as far as it has got at t, one short segment at a time so each can have its own width and colour:
 * style(ctx, i, s, v) sets them, with i the segment, s its arclength share and v the hand's speed there (0..1).
 * With `whole: true` the path is stroked once (style is called once with v = 0.5): for a pattern brush (chalk).
 */
export function drawStroke(ctx, st, t, style, { whole = false, upto, from = 0 } = {}) {
  const s = upto ?? drawn(st, t);
  if (s <= 0 || s <= from) return 0;
  const P = st.pts, n = indexAt(st, s), end = pointAt(st, s);
  const i0 = from > 0 ? indexAt(st, from) + 1 : 0, start = from > 0 ? pointAt(st, from) : P[0];
  ctx.save(); ctx.lineCap = "round"; ctx.lineJoin = "round";
  if (whole) {
    style(ctx, 0, s, 0.5);
    ctx.beginPath(); ctx.moveTo(start[0], start[1]);
    for (let i = i0; i <= n; i++) ctx.lineTo(P[i][0], P[i][1]);
    ctx.lineTo(end[0], end[1]); ctx.stroke();
  } else {
    const every = 3;   // segments of three resampled steps: smooth enough, a third of the calls
    if (i0 > n) {      // `from` and the head inside one resampled step
      style(ctx, i0, from, speedAtS(from));
      ctx.beginPath(); ctx.moveTo(start[0], start[1]); ctx.lineTo(end[0], end[1]); ctx.stroke();
      ctx.restore(); return s;
    }
    if (i0 > 0) {      // the piece from `from` to the next resampled point
      style(ctx, i0, from, speedAtS(from));
      ctx.beginPath(); ctx.moveTo(start[0], start[1]); ctx.lineTo(...(i0 <= n ? P[i0] : end)); ctx.stroke();
    }
    for (let i = i0; i < n || i === i0; i += every) {
      const j = Math.min(i + every, n);
      const sj = st.cum[i] / st.len;
      style(ctx, i, sj, speedAtS(sj));
      ctx.beginPath(); ctx.moveTo(P[i][0], P[i][1]);
      for (let k = i + 1; k <= j; k++) ctx.lineTo(P[k][0], P[k][1]);
      if (j >= n) ctx.lineTo(end[0], end[1]);
      ctx.stroke();
      if (j >= n) break;
    }
  }
  ctx.restore();
  return s;
}

/**
 * Where the pen head is at t: on a stroke while it is drawn (down), else travelling through the air between the end of
 * one stroke and the start of the next (minimum jerk again, with a small lift). rest = { from: [x, y], to: [x, y] } is
 * where it waits before the first stroke and after the last. Returns { x, y, down, lift (0..1), st, vx, vy }.
 */
export function pen(list, t, rest, { lead = 0.35, tail = 0.45 } = {}) {
  const at = (x, y, down, lift, st, vx = 0, vy = 0) => ({ x, y, down, lift, st, vx, vy });
  const first = list[0], last = list[list.length - 1];
  const fly = (a, b, u) => {
    const m = mj(u), du = mjSpeed(u);
    return at(a[0] + (b[0] - a[0]) * m, a[1] + (b[1] - a[1]) * m, false, Math.sin(Math.PI * clamp(u)), null,
      (b[0] - a[0]) * du, (b[1] - a[1]) * du);
  };
  if (t < first.t0) {
    const u = (t - (first.t0 - lead)) / lead;
    return u <= 0 ? at(rest.from[0], rest.from[1], false, 0, null) : fly(rest.from, first.pts[0], u);
  }
  for (let i = 0; i < list.length; i++) {
    const st = list[i];
    if (t < st.t0 + st.dur) {
      if (t >= st.t0) {
        const s = drawn(st, t), p = pointAt(st, s), q = pointAt(st, Math.min(1, s + 0.02));
        const v = mjSpeed((t - st.t0) / st.dur);
        return at(p[0], p[1], true, 0, st, (q[0] - p[0]) * v, (q[1] - p[1]) * v);
      }
      const prev = list[i - 1], a = prev.pts[prev.pts.length - 1];
      return fly(a, st.pts[0], (t - (prev.t0 + prev.dur)) / Math.max(1e-3, st.t0 - (prev.t0 + prev.dur)));
    }
  }
  const a = last.pts[last.pts.length - 1], u = (t - (last.t0 + last.dur)) / tail;
  return u >= 1 ? at(rest.to[0], rest.to[1], false, 0, null) : fly(a, rest.to, u);
}

/**
 * Pen passes for writing a laid-out line (lib.layoutText) by hand: one pass per glyph, `per` seconds apart, each a
 * zigzag over the glyph that pen() can follow. drawn(pass, t) is how much of the glyph is shown (reveal it left to right).
 */
export function glyphPasses(lay, size, t0, per, { busy = 0.86, rows = 6 } = {}) {
  return lay.glyphs.map((gl, i) => {
    const x0 = gl.x - 2, x1 = gl.x + gl.w + 2, top = lay.y - size * 0.82;
    const pts = [];
    for (let k = 0; k <= rows; k++) pts.push([x0 + (x1 - x0) * k / rows, top + size * (k % 2 ? 0.25 : 0.7) + (k % 3) * 4]);
    return Object.assign(prep(pts, { step: 6 }), { t0: t0 + i * per, dur: per * busy, glyph: gl, write: true });
  });
}

/** Draw a full-frame canvas smeared along (dx, dy) px (a running average of copies a few px apart): a camera or a
 * board moving fast, with about half a frame of shutter. Returns how many copies it drew. */
export function smear(ctx, canvas, dx, dy, w, h, { every = 3, max = 32 } = {}) {
  const n = Math.min(max, Math.ceil(Math.hypot(dx, dy) / every));
  if (n < 2) { ctx.drawImage(canvas, 0, 0, w, h); return 1; }
  const a = ctx.globalAlpha;
  for (let i = 0; i < n; i++) {
    ctx.globalAlpha = a / (i + 1);
    const u = i / (n - 1) - 0.5;
    ctx.drawImage(canvas, u * dx, u * dy, w, h);
  }
  ctx.globalAlpha = a;
  return n;
}
