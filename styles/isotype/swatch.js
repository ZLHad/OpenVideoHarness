// isotype swatch: a plate of pictorial statistics. Quantities are never shown by making a symbol bigger: one symbol
// is one unit, more means more symbols, and every change is ONE symbol added, removed or re-coloured on the beat.
// Symbols are flat silhouettes (no outline, no perspective, no shading), identical within a row, set in strict rows.
//   0.10       hook: this clip's own 150 frames as 25 film symbols (1 symbol = 6 frames) stamp down at once, a 5 × 5
//              block 160 px high filling the middle of the frame; black = still to come, red = already played
//   0.1–5.0    the playhead: one more symbol turns red every 6 frames (= every 8th note at 150 BPM) — the chart is
//              the clip's own clock, so something changes on every beat to the end
//   0.50–0.86  the block regroups (one row after another) into the top-right corner; the key lands under it
//   0.80–1.40  title, one word per 8th note (words slide 18 px into place in 3 frames, no fade)
//   1.50–2.30  Chinese title, one character per 16th note
//   2.0–2.8    motif, one row read left to right: 2 pencils (outline, black) → 3 easels (storyboard, blue) →
//              4 cameras (draft, red); one symbol per 16th note, each stamped down; counts tick with them;
//              a camera's reels turn 45° per 8th note once it is in
//   3.2 / 3.6  a 5th camera is added; a storyboard shot is cut (3 → 2) and the cameras close the gap
//   4.0–4.4    signature transition, the count-down: motif symbols and title units removed one per frame, right to
//              left (English words first, so the regrouping block never crosses the title), while the frame block
//              regroups row by row to the end plate (no empty frame)
//   4.40–5.0   end plate: the name and the key beside the block, which fills its last symbol at 4.8 s
// Every symbol here is drawn from scratch to the grammar, not traced from any Arntz symbol.

let L = null;

// ONE timing table for picture and foley (FOLEY → events.json via styles/_swatch/foley.mjs)
const T = {
  hook: 0.1, regroup: [0.5, 0.24, 0.03], key: 0.9, words: [0.8, 1.0, 1.2, 1.4], zh0: 1.5, zhStep: 0.1,
  motif: 2.0, step: 0.1, addCam: 3.2, cutShot: 3.6, close: 3.7, out: 4.0, outStep: 1 / 30,
  endGroup: [4.1, 0.24, 0.03], name: 4.4, nameZh: 4.5, endKey: 4.6,
};
const FRAMES_PER_SYMBOL = 6, N_FILM = 25;
const GROUPS = [                        // outline → storyboard → draft
  { kind: "pencil", n: 2, col: "fg", zh: "大纲", en: "Outline" },
  { kind: "easel", n: 3, col: "extra.0", zh: "分镜", en: "Storyboard" },
  { kind: "camera", n: 4, col: "accent", zh: "初版", en: "Draft" },
];
const ADDS = [];                         // add time of every motif symbol, one per 16th note from 2.0 s, + the 5th camera
{ let k = 0; GROUPS.forEach((g, gi) => { for (let i = 0; i < g.n; i++) ADDS.push({ g: gi, i, t: T.motif + T.step * k++ }); }); }
ADDS.push({ g: 2, i: 4, t: T.addCam });
const CUT = { g: 1, i: 2 };              // the storyboard shot that is cut at 3.6 s

const W_UNIT = { pencil: 70, easel: 80, camera: 100, film: 76 };     // widths in a 100-high unit box
const S_MOTIF = 150, S_FILM = 160;
const ROW = { x: 192, base: 800, gap: 24, groupGap: 60 };
// the film block in its three layouts: S = symbol height, px/py = pitch, x0/y0 = top-left
const BLOCK = {
  hook: { S: 160, px: 160, py: 184, x0: 579, y0: 92 },
  corner: { S: 72, px: 70, py: 84, x0: 1457, y0: 100 },
  end: { S: 120, px: 120, py: 138, x0: 1219, y0: 204 },
};
const DROP = [-24, -8, 3, 0];            // stamp-down offsets (px) on the first four frames of a symbol
const pan = (x) => Math.round(((2 * x) / 1920 - 1) * 70) / 100;

function motifLayout() {
  const g = [];
  let x = ROW.x;
  GROUPS.forEach((G, gi) => {
    const w = (W_UNIT[G.kind] * S_MOTIF) / 100, n = gi === 2 ? G.n + 1 : G.n, xs = [];
    for (let i = 0; i < n; i++) xs.push(Math.round(x + i * (w + ROW.gap)));
    g.push({ x0: Math.round(x), xs, w: Math.round(w), pitch: w + ROW.gap });
    x += G.n * (w + ROW.gap) - ROW.gap + ROW.groupGap;
  });
  return g;
}
const MOTIF = motifLayout();

export const FOLEY = [
  { t: T.hook, sfx: "boom", gain_db: -10 },                                                   // the block stamps down
  { t: T.hook, sfx: "pop", gain_db: -8 },
  { t: T.regroup[0] + 0.12, sfx: "whoosh", gain_db: -20, pan: 0.5 },                          // regroup to the corner
  ...T.words.map((t, i) => ({ t, sfx: "click", gain_db: -12, pan: pan(250 + i * 220) })),    // title words
  ...[0, 4].map((i) => ({ t: T.zh0 + i * T.zhStep, sfx: "tick", gain_db: -13, pan: pan(230 + i * 80) })),   // −13, not −16: the first was BURIED under the pizzicato
  ...GROUPS.map((G, gi) => ({ t: ADDS.find((a) => a.g === gi).t, sfx: "toggle", gain_db: -14, pan: pan(MOTIF[gi].x0 + 60) })),
  { t: T.addCam, sfx: "pop", gain_db: -12, pan: pan(MOTIF[2].xs[4]) },                        // + one camera
  { t: T.cutShot, sfx: "click", gain_db: -10, pan: pan(MOTIF[1].xs[2]) },                     // − one storyboard shot
  { t: T.out, sfx: "swish_rev", gain_db: -12, pan: 0.3 },                                     // count-down
  { t: T.name, sfx: "ding", gain_db: -14, pan: -0.4 },                                        // end plate
];

export const fonts = ["Futura", "PingFang SC"];

// ── pictograms: flat silhouettes in a 100-high unit box; holes cut with destination-out so the paper shows through
function cut(g, f) { g.save(); g.globalCompositeOperation = "destination-out"; g.fillStyle = "#000"; f(); g.restore(); }
function pencil(g) {                     // leaning 60°, point down-left
  g.save(); g.translate(8, 94); g.rotate(-Math.atan2(88, 52));
  const w = 21;
  g.beginPath(); g.moveTo(22, -w / 2); g.lineTo(22, w / 2); g.lineTo(0, 0); g.closePath(); g.fill();   // sharpened cone
  g.fillRect(22, -w / 2, 64, w);                                                            // painted body
  g.beginPath(); g.roundRect(88, -w / 2, 12, w, [0, 5, 5, 0]); g.fill();                    // eraser (gap = ferrule)
  cut(g, () => { g.fillRect(22, -w / 2 - 1, 2.5, w + 2); g.fillRect(27, -1.2, 56, 2.4); g.fillRect(8.5, -w / 2, 2.5, w); });
  g.restore();
}
function easel(g) {
  g.fillRect(36, 0, 8, 8);
  g.fillRect(4, 6, 72, 50);
  const leg = (x0, y0, x1, y1, w) => { g.lineWidth = w; g.lineCap = "butt"; g.beginPath(); g.moveTo(x0, y0); g.lineTo(x1, y1); g.stroke(); };
  leg(26, 56, 11, 100, 7); leg(54, 56, 69, 100, 7); leg(40, 56, 40, 97, 5);
  g.fillRect(14, 79, 52, 5);
  cut(g, () => {                                                   // the sketch on the board: two hills and a sun
    g.beginPath(); g.moveTo(12, 48); g.lineTo(29, 24); g.lineTo(44, 48); g.closePath(); g.fill();
    g.beginPath(); g.moveTo(35, 48); g.lineTo(51, 32); g.lineTo(68, 48); g.closePath(); g.fill();
    g.beginPath(); g.arc(59, 19, 6, 0, Math.PI * 2); g.fill();
  });
}
function camera(g, spoke = 0) {          // spoke: reel rotation step (× 45°)
  g.beginPath(); g.arc(27, 21, 18, 0, Math.PI * 2); g.fill();
  g.beginPath(); g.arc(66, 21, 18, 0, Math.PI * 2); g.fill();
  g.beginPath(); g.roundRect(12, 42, 62, 32, 3); g.fill();
  g.fillRect(74, 49, 10, 18);
  g.beginPath(); g.moveTo(84, 46); g.lineTo(99, 39); g.lineTo(99, 77); g.lineTo(84, 70); g.closePath(); g.fill();
  const leg = (x1, w) => { g.lineWidth = w; g.beginPath(); g.moveTo(43, 72); g.lineTo(x1, 100); g.stroke(); };
  leg(20, 6); leg(66, 6); leg(43, 5);
  cut(g, () => {
    for (const cx of [27, 66]) {
      g.beginPath(); g.arc(cx, 21, 5, 0, Math.PI * 2); g.fill();
      g.save(); g.translate(cx, 21); g.rotate((spoke * Math.PI) / 4); g.fillRect(-1.3, -15, 2.6, 10); g.fillRect(-1.3, 5, 2.6, 10); g.restore();
    }
    g.fillRect(12, 38.5, 62, 3.5);
  });
}
function film(g) {                       // a piece of film: two frames, sprocket holes on both edges
  g.beginPath(); g.roundRect(0, 0, 76, 100, 4); g.fill();
  cut(g, () => {
    for (let i = 0; i < 5; i++) { g.fillRect(5, 6 + i * 19.5, 9, 10); g.fillRect(62, 6 + i * 19.5, 9, 10); }
    g.fillRect(20, 48.5, 36, 3);
  });
}
const DRAW = { pencil, easel, camera, film };

function sprite(kind, color, size, variant) {        // rendered once in setup
  const s = size / 100, w = Math.ceil(W_UNIT[kind] * s) + 4, h = size + 4;
  const c = document.createElement("canvas"); c.width = w; c.height = h;
  const g = c.getContext("2d");
  g.translate(2, 2); g.scale(s, s); g.fillStyle = color; g.strokeStyle = color;
  DRAW[kind](g, variant);
  return c;
}

export async function setup(ctx, tokens, lib) {
  const P = (k) => lib.color(tokens, k);
  const spr = {};
  spr.pencil = sprite("pencil", P("fg"), S_MOTIF);
  spr.easel = sprite("easel", P("extra.0"), S_MOTIF);
  for (let v = 0; v < 4; v++) spr[`camera${v}`] = sprite("camera", P("accent"), S_MOTIF, v);
  spr.todo = sprite("film", P("fg"), S_FILM);
  spr.done = sprite("film", P("accent"), S_FILM);
  L = { spr, enter: lib.easeOf(tokens.ease.enter) };
}

// words slide 18 px from the right over 3 frames (no fade); symbols stamp down over 4 frames
const slide = (lib, t, t0) => Math.round(18 * (1 - L.enter(lib.seg(t, t0, t0 + 0.1))));
const drop = (lib, t, t0) => { const k = lib.frame(t) - lib.frame(t0); return k >= 0 && k < DROP.length ? DROP[k] : 0; };
function put(ctx, c, x, base) { ctx.drawImage(c, Math.round(x) - 2, Math.round(base - c.height + 2)); }

// the film block: symbol i in a layout → its box; between layouts each symbol moves on its own, one after another
function cell(lay, i) {
  const r = Math.floor(i / 5), c = i % 5;
  return { x: lay.x0 + c * lay.px, y: lay.y0 + r * lay.py, w: (W_UNIT.film * lay.S) / 100, h: lay.S };
}
function blockBox(lib, t, i) {
  const move = (a, b, [t0, dur, stag], rev) => {                   // a row moves as one; rev: bottom row first
    const r = rev ? 4 - Math.floor(i / 5) : Math.floor(i / 5), u = lib.ease.inOutCubic(lib.seg(t, t0 + r * stag, t0 + r * stag + dur)), A = cell(a, i), B = cell(b, i);
    return { x: lib.lerp(A.x, B.x, u), y: lib.lerp(A.y, B.y, u), w: lib.lerp(A.w, B.w, u), h: lib.lerp(A.h, B.h, u) };
  };
  return t < T.endGroup[0] ? move(BLOCK.hook, BLOCK.corner, T.regroup) : move(BLOCK.corner, BLOCK.end, T.endGroup, true);
}

export function renderAt(t, ctx, tokens, lib) {
  const { W, H } = lib;
  const P = (k) => lib.color(tokens, k);
  const f = lib.frame(t);
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, W, H);
  lib.paper(ctx, { tone: P("bg"), amount: 0.9, blotch: 0.035, tooth: 0.018, fiber: 0.35, seed: 31 });
  ctx.imageSmoothingQuality = "high";
  const out = (k) => T.out + k * T.outStep;                         // the count-down: k-th removal time

  // ── the film block: 25 symbols = 150 frames; symbol i turns red on frame 6·i (the playhead)
  if (t >= T.hook) {
    const dy = drop(lib, t, T.hook), src = L.spr.todo;
    for (let i = 0; i < N_FILM; i++) {
      const b = blockBox(lib, t, i), c = f >= i * FRAMES_PER_SYMBOL ? L.spr.done : L.spr.todo, s = b.h / S_FILM;
      ctx.drawImage(c, Math.round(b.x - 2 * s), Math.round(b.y + dy - 2 * s), Math.round(src.width * s), Math.round(src.height * s));
    }
  }
  // the key: under the corner block, then beside the block on the end plate
  const key = (x, y, t0, align) => {
    const dx = slide(lib, t, t0);
    lib.setFont(ctx, tokens, "zh", 52, { weight: 600 }); ctx.fillStyle = P("fg");
    lib.drawText(ctx, "每个符号 = 6 帧", x + dx, y, { align, tracking: 0.04 * 52 });
    lib.setFont(ctx, tokens, "body", 32, { weight: 500 }); ctx.fillStyle = P("extra.4");
    lib.drawText(ctx, "1 symbol = 6 frames · red = played", x + dx, y + 44, { align, tracking: 0.02 * 32 });
  };
  if (t >= T.key && t < T.endGroup[0]) key(1792, 570, T.key, "right");

  // ── title words and Chinese characters; removed from the end during the count-down (Chinese first)
  const words = lib.TITLE_EN.split(" ");
  lib.setFont(ctx, tokens, "display", 104, { weight: 700 }); ctx.fillStyle = P("fg");
  const lay = lib.layoutText(ctx, lib.TITLE_EN, { x: 192, y: 250, tracking: -0.01 * 104 });
  let wi = -1, prev = " ";
  const wOf = lay.glyphs.map((g) => { if (prev === " " && g.ch !== " ") wi++; prev = g.ch; return wi; });
  lib.drawGlyphs(ctx, lay, (g, i) => {
    const w = wOf[i], t0 = T.words[w];
    if (t < t0 || t >= out(words.length - 1 - w)) return null;          // English words go first
    return { dx: slide(lib, t, t0) };
  });
  lib.setFont(ctx, tokens, "zh", 78, { weight: 600 });
  const zl = lib.layoutText(ctx, lib.TITLE_ZH, { x: 196, y: 366, tracking: 0.04 * 78 });
  lib.drawGlyphs(ctx, zl, (g, i) => {
    const t0 = T.zh0 + i * T.zhStep;
    if (t < t0 || t >= out(words.length + 8 - i)) return null;
    return { dx: slide(lib, t, t0) };
  });

  // ── motif: one row, three groups; the cut shot leaves, then the cameras close the gap
  const items = ADDS.filter((a) => !(a.g === CUT.g && a.i === CUT.i && t >= T.cutShot));
  const shift = -Math.round(MOTIF[1].pitch * L.enter(lib.seg(t, T.close, T.close + 0.1)));
  const xOf = (a) => MOTIF[a.g].xs[a.i] + (a.g === 2 ? shift : 0);
  const order = [...items].sort((a, b) => xOf(b) - xOf(a));
  const tRemove = new Map(order.map((a, k) => [a, out(k)]));
  for (const a of items) {
    if (t < a.t || t >= tRemove.get(a)) continue;
    const kind = GROUPS[a.g].kind, k = kind === "camera" ? `camera${Math.floor((t - a.t) / 0.2) % 4}` : kind;   // reels turn per 8th
    put(ctx, L.spr[k], xOf(a), ROW.base + drop(lib, t, a.t));
  }
  GROUPS.forEach((G, gi) => {                                        // labels + live counts
    const mine = items.filter((a) => a.g === gi);
    const t0 = mine[0].t, tEnd = Math.max(...mine.map((a) => tRemove.get(a)));
    if (t < t0 || t >= tEnd) return;
    const n = mine.filter((a) => t >= a.t && t < tRemove.get(a)).length;
    const x = MOTIF[gi].x0 + (gi === 2 ? shift : 0);
    lib.setFont(ctx, tokens, "zh", 58, { weight: 600 }); ctx.fillStyle = P("fg");
    lib.drawText(ctx, G.zh, x, 892, { tracking: 0.06 * 58 });
    lib.setFont(ctx, tokens, "display", 66, { weight: 700 }); ctx.fillStyle = P(G.col);
    lib.drawText(ctx, String(n), x + 142, 892);
    lib.setFont(ctx, tokens, "body", 38, { weight: 500 }); ctx.fillStyle = P("extra.4");
    lib.drawText(ctx, G.en, x, 946, { tracking: 0.02 * 38 });
  });
  // the base rule the row stands on: to the end of the 5th camera slot, shortened with the gap
  const lastRemove = Math.max(...tRemove.values());
  if (t >= T.motif && t < lastRemove) {
    const x1 = MOTIF[2].xs[4] + MOTIF[2].w + shift;
    ctx.fillStyle = P("extra.5"); ctx.fillRect(ROW.x, ROW.base + 12, Math.round((x1 - ROW.x) * lib.seg(t, T.motif, T.motif + 0.1)), 3);
  }
  if (t >= T.motif + 0.2 && t < out(3)) {                          // the motif data are illustrative, and say so
    lib.setFont(ctx, tokens, "body", 26, { weight: 500 }); ctx.fillStyle = P("extra.4");
    lib.drawText(ctx, "Stage counts are illustrative", 1792, 1012, { align: "right", tracking: 0.02 * 26 });
  }

  // ── end plate: the name and the key on the left, the block (nearly all red) on the right
  if (t >= T.name) {
    lib.setFont(ctx, tokens, "display", 170, { weight: 700 }); ctx.fillStyle = P("fg");
    lib.drawText(ctx, "Isotype", 192 + slide(lib, t, T.name), 470, { tracking: 0.01 * 170 });
  }
  if (t >= T.nameZh) {
    lib.setFont(ctx, tokens, "zh", 76, { weight: 600 }); ctx.fillStyle = P("fg");
    lib.drawText(ctx, "图形统计", 198 + slide(lib, t, T.nameZh), 580, { tracking: 0.12 * 76 });
  }
  if (t >= T.endKey) key(198, 690, T.endKey, "left");
}
