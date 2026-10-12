// canvas-film · pieces films reuse: a label that counts as a read, a piece that drops in, a stamp; and what
// src/90-main.js draws over every frame: the chapter bar and the caption.

// a line of text that comes in at `at` (rising 12 px over o.fade s) and stays to the end of its shot, or fades out by
// o.until. From the moment it is fully in it is a read (window.film.texts, judged by bin/vh textcheck), unless
// o.texture. The other o go to txt().
function label(t, at, s, x, y, o = {}) {
  const fi = o.fade ?? 0.4, until = o.until ?? Infinity;
  if (!o.texture) read(s, at + fi, until - fi);
  const k = show(t, at, fi), a = Math.min(k, until === Infinity ? 1 : 1 - eIn(seg(t, until - fi, until)));
  if (a <= 0) return;
  txt(s, x, y + 12 * (1 - k), { ...o, alpha: a * (o.alpha ?? 1) });
}
// a piece that drops into place at `at`: fades in, falls o.fall px and settles its tilt over o.d s. fn(u) draws it
// about (cx, cy). An event (o.kind, default "drop") at `at`.
function drop(t, at, cx, cy, fn, o = {}) {
  cue(o.kind || "drop", at, { x: cx, y: cy });
  const u = eOut(seg(t, at, at + (o.d ?? 0.45)));
  if (u <= 0) return 0;
  X.save(); X.globalAlpha *= Math.min(1, u * 1.6);
  X.translate(cx, cy - (o.fall ?? 14) * (1 - u)); X.rotate((o.spin ?? 0.05) * (1 - u)); X.translate(-cx, -cy);
  fn(u); X.restore();
  return u;
}
// a stamp pressed at `at`: in 0.12 s from 1.25x down to its size, a framed word; an event (o.kind, default "stamp") and,
// once it has landed, a read
function stamp(t, at, cx, cy, s, o = {}) {
  cue(o.kind || "stamp", at, { x: cx, y: cy });
  read(s, at + 0.15, Infinity);
  const u = seg(t, at, at + 0.12);
  if (u <= 0) return;
  // the weights film.html declares: sans 400 and 600, serif 700 and 900
  const family = o.family || "sans", size = o.size || 56, f = { size, weight: o.weight ?? (family === "serif" ? 900 : 600), family };
  const col = o.color || FILM.ui.accent, k = lerp(1.25, 1, eOut(u));
  const w = measure(s, f) + 56, h = size * 1.5;
  X.save(); X.translate(cx, cy); X.rotate(o.rot ?? -0.07); X.scale(k, k);
  rect(-w / 2, -h / 2, w, h, { stroke: col, w: 5, r: 6 });
  txt(s, 0, size * 0.36, { ...f, color: col, align: "center" });
  X.restore();
}

// ---- the chapter bar (top): a cell per chapter, sized to its title; the current one fills as the chapter goes and its
// title always shows; every title shows for BAR.all s from each chapter's start (when they fit side by side) ----
const BAR = { y: 64, size: 44, gap: 20, pad: 56, all: 3.0, margin: 120 };
let BAR_CELLS = [], BAR_ALL = true;
function layoutBar() {   // once, in ready (it measures the titles)
  const n = CHAPTER_T.length;
  BAR_CELLS = [];
  if (n < 2) return;
  const ws = CHAPTER_T.map((c) => measure(c.title, { size: BAR.size }) + BAR.pad), room = W - 2 * BAR.margin;
  BAR_ALL = ws.reduce((s, w) => s + w, 0) + BAR.gap * (n - 1) <= room;
  const cw = BAR_ALL ? ws : ws.map(() => (room - BAR.gap * (n - 1)) / n);   // too many to name at once: even cells, the current title only
  let x = (W - cw.reduce((s, w) => s + w, 0) - BAR.gap * (n - 1)) / 2;
  for (const w of cw) { BAR_CELLS.push({ x, w }); x += w + BAR.gap; }
}
function chapterBar(t) {
  if (!BAR_CELLS.length) return;
  const vis = win(t, BAR_SPAN[0], BAR_SPAN[1], BAR_SPAN[0] > 0 ? 0.5 : 0, 0.6);   // already up on frame 0 when it starts the film
  if (vis <= 0) return;
  let ci = 0;
  CHAPTER_T.forEach((c, i) => { if (t >= c.t) ci = i; });
  let all = 0;
  if (BAR_ALL) for (const c of CHAPTER_T) all = Math.max(all, win(t, c.t - 0.2, c.t + BAR.all, c.t > 0 ? 0.4 : 0, 0.6));
  X.save(); X.globalAlpha *= vis;
  const g = X.createLinearGradient(0, 0, 0, 190);
  g.addColorStop(0, `rgba(${FILM.ui.dark},${0.55 + 0.15 * all})`); g.addColorStop(1, `rgba(${FILM.ui.dark},0)`);
  X.fillStyle = g; X.fillRect(0, 0, W, 190);
  CHAPTER_T.forEach((c, i) => {
    const { x, w } = BAR_CELLS[i], now = i === ci, p = i < ci ? 1 : now ? seg(t, c.t, c.b) : 0;
    rect(x, BAR.y, w, 4, { fill: FILM.ui.text, alpha: 0.28 });
    if (p > 0) rect(x, BAR.y, w * p, 4, { fill: now ? FILM.ui.accent : FILM.ui.text, alpha: now ? 1 : 0.8 });
    if (now) circle(x + w * p, BAR.y + 2, 7, { fill: FILM.ui.accent });
    const a = now ? 1 : 0.75 * all;
    if (a > 0.01) txt(c.title, x + w / 2, BAR.y + 58, { size: BAR.size, align: "center", alpha: a, stroke: 6, strokeColor: `rgba(${FILM.ui.dark},0.55)`, shadow: `rgba(${FILM.ui.dark},0.6)`, blur: 10 });
  });
  X.restore();
}

// ---- a cover's title: lines in the heaviest Chinese sans this machine has ("Film Heavy" in film.html), with a dark
// outline and a darker band behind them, so they read at the size of a feed tile. title: { text: [lines], size: [px per
// line] or px, x, y (the first line's baseline), align, color, band: true | false, gap } ----
function coverTitle(o) {
  const lines = [].concat(o.text || []), sizes = lines.map((_, i) => [].concat(o.size ?? 200)[i] ?? [].concat(o.size ?? 200).slice(-1)[0]);
  if (!lines.length) return;
  const x = o.x ?? 120, y0 = o.y ?? 700, gap = o.gap ?? 0.18, align = o.align || "left";
  const ys = []; let y = y0;
  sizes.forEach((s, i) => { if (i) y += s * (1 + gap); ys.push(y); });
  if (o.band !== false) {   // darker behind the block, fading out away from it
    const top = y0 - sizes[0] * 1.2, bottom = ys[ys.length - 1] + sizes[sizes.length - 1] * 0.5;
    const g = X.createLinearGradient(0, top - 120, 0, bottom + 120);
    g.addColorStop(0, `rgba(${FILM.ui.dark},0)`); g.addColorStop(0.25, `rgba(${FILM.ui.dark},0.55)`);
    g.addColorStop(0.75, `rgba(${FILM.ui.dark},0.55)`); g.addColorStop(1, `rgba(${FILM.ui.dark},0)`);
    X.fillStyle = g; X.fillRect(0, top - 120, W, bottom - top + 240);
  }
  lines.forEach((s, i) => txt(s, x, ys[i], { size: sizes[i], weight: 900, family: "heavy", align, color: o.color || FILM.ui.text,
    stroke: Math.max(8, sizes[i] * 0.06), strokeColor: `rgba(${FILM.ui.dark},0.85)`, shadow: `rgba(${FILM.ui.dark},0.6)`, blur: 18, dy: 4 }));
}

// ---- the caption (bottom): one line on a soft dark band; on a plate where the shot says light: true (a pale picture) ----
function captionBand(t) {
  const c = captionAt(t);
  if (!c) return;
  const C = FILM.caption, a = Math.min(c.joinPrev ? 1 : show(t, c.start, 0.15), c.joinNext ? 1 : 1 - eIn(seg(t, c.end - 0.12, c.end)));
  if (a <= 0) return;
  X.save(); X.globalAlpha *= a;
  if (SHOT_T[shotAt(t)].shot.light) {
    const w = measure(c.text, { size: C.size }) + 56;
    rect(W / 2 - w / 2, C.y - C.size - 4, w, C.size + 30, { fill: `rgba(${FILM.ui.dark},0.72)`, r: 14 });
  } else {
    const g = X.createLinearGradient(0, C.y - 100, 0, H);
    g.addColorStop(0, `rgba(${FILM.ui.dark},0)`); g.addColorStop(1, `rgba(${FILM.ui.dark},0.6)`);
    X.fillStyle = g; X.fillRect(0, C.y - 100, W, H - C.y + 100);
  }
  txt(c.text, W / 2, C.y, { size: C.size, align: "center", stroke: 6, strokeColor: `rgba(${FILM.ui.dark},0.55)`, shadow: `rgba(${FILM.ui.dark},0.5)`, blur: 8 });
  X.restore();
}
