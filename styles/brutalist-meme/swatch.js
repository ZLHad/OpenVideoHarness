// brutalist-meme swatch · 野兽派梗 (swatch grid 150 BPM: a beat is 0.4 s; every cut and punch-in lands on it)
//   0.00–0.40  HOOK: a full-frame raw terminal from frame 0: the REAL output of `bin/vh style list` scrolls in on 12 fps steps
//   0.40       HARD CUT on the beat to one row of it (brutalist-meme) at 96 px, underlined raw in the accent
//   0.80       HARD CUT + 2-frame punch-in (115 %): a visible 12-column grid; the Latin title types in on steps
//   1.60       HARD CUT + punch-in: the Chinese line types in
//   2.00–2.40  motif: three raw screenshots of real repo material slam in on eighth notes, 0 px corners:
//              templates/BRIEF.md (outline) · a crop of styles/gallery.jpg (storyboard) · real render.sh output (draft,
//              typed in line by line); the third breaks the grid (3°). Labels mix system fonts on purpose
//              (Times New Roman italic · Arial Black · Menlo); the gallery crop is a q28 JPEG drawn 1:1
//   2.00 / 2.40 / 2.80  a hand-drawn mouse arrow hops to the next window, a 115 % punch-in on each beat
//   3.27–3.60  held breath: the frame freezes after the 3.2 punch-in (the sound keeps a low bed; no digital silence)
//   3.60       punchline: a hand-drawn orange box around DRAFT in 3 steps + label
//   4.00–4.20  SIGNATURE TRANSITION: 5 frames of glitch (RGB split + slices), hard cut to the end frame; punch-ins on 4.2 and 4.4

export const fonts = ["Times New Roman", "Arial Black"];
const TAU = Math.PI * 2;
let L = null;

// real repo material (no invented UI): shown as raw screenshots
const STYLE_LIST = [   // `bin/vh style list`, first rows, verbatim
  "archival-pan-zoom      film          档案推拉           swatch", "blueprint              retro         工程蓝图           swatch",
  "bouncy-flat-2d         illustration  弹性扁平 2D        swatch", "brutalist-meme         brand         野兽派梗           swatch",
  "bubble-chart-story     data          气泡图现场讲         swatch", "clockwork-map          film          机械钟表地图         swatch",
  "crt-terminal           retro         CRT 终端         swatch", "cutout-jazz            film          剪纸爵士片头         swatch",
  "dark-math              data          暗底数学           swatch", "dunhuang-mural         chinese       敦煌             swatch",
  "editorial-data         data          编辑部数据叙事        swatch", "fui-hud                data          电影界面 HUD       swatch",
  "guochao-festive        chinese       国潮             swatch", "halftone-comic         illustration  半调漫画           swatch",
];
const BRIEF = [        // templates/BRIEF.md, verbatim lines (wrapped to the window)
  ["## Content", 1], ["- Spine (one line): {the story in one", 0], ["  sentence: X wants/asks ___, but ___,", 0], ["  so ___}", 0],
  ["- Recurring motif: {one object/visual", 0], ["  that evolves and pays off}", 0], ["## Style", 1], ["- Refs (2–3 named works): {…}", 0],
];
const RENDER = [       // styles/_swatch/render.sh output from an earlier run of this very swatch, verbatim
  "$ styles/_swatch/render.sh brutalist-meme", "✓ 150 frames at 1920x1080, canvas drew,", "  no error card (6s render)",
  "✓ styles/brutalist-meme/media/swatch.mp4", "  0.37 MB  (crf 18, +music)", "✓ styles/brutalist-meme/media/poster.jpg",
  "  76 KB (q 2)",
];
// Action times come from events.json, the file render.sh uses to place the foley, so picture and sound share one number
// per action: T[id] for single actions (entries sharing an id layer sounds on one action and must share t), S[series]
// for repeated ones (sorted, de-duplicated times).
let T = null, S = null;
async function loadTimes() {
  const ev = await (await fetch(new URL("./events.json", import.meta.url))).json(), t = {}, s = {};
  for (const e of ev) {
    if (e.id) { if (e.id in t && t[e.id] !== e.t) throw new Error(`events.json: "${e.id}" has two times`); t[e.id] = e.t; }
    if (e.series) (s[e.series] ||= []).push(e.t);
  }
  for (const k in s) s[k] = [...new Set(s[k])].sort((a, b) => a - b);
  return [t, s];
}
export async function setup(ctx, tokens, lib) {
  [T, S] = await loadTimes();
  const P = (k) => lib.color(tokens, k);
  const x0 = 96, x1 = lib.W - 96, col = (x1 - x0) / 12;
  const img = new Image(); img.src = new URL("./assets/gallery-crop.jpg", import.meta.url); await img.decode();   // a crop of styles/gallery.jpg, pre-scaled to 404×216
  const gal = document.createElement("canvas"); gal.width = img.width; gal.height = img.height; gal.getContext("2d").drawImage(img, 0, 0);   // copied once: frames draw it 1:1 at integer positions (no per-frame resampling)
  L = { P, x0, x1, col, gallery: gal, cards: [0, 1, 2].map((k) => ({ x: 192 + k * 528, y: 540, w: 480, h: 292 })) };
}
// every cut and punch-in is an events.json "cut" (0.4 0.8 1.6 2.0 2.2 2.4 2.8 3.2 3.6 4.2 4.4, all on the 150 BPM grid)
function punch(t) { return S.cut.some((p) => t >= p && t < p + 2 / 30) ? 1.15 : 1; }
const stepU = (t, a, b, n) => Math.floor(Math.max(0, Math.min(1, (t - a) / (b - a))) * n + 1e-9) / n;

function grid(ctx, t, lib) {
  const P = L.P, u = stepU(t, 0.1, 0.6, 4);
  ctx.save(); ctx.strokeStyle = P("extra.0"); ctx.lineWidth = 1;
  for (let i = 0; i <= 12; i++) { const x = Math.round(L.x0 + i * L.col) + 0.5; ctx.beginPath(); ctx.moveTo(x, 54); ctx.lineTo(x, 54 + (lib.H - 108) * u); ctx.stroke(); }
  for (let j = 0; j <= 10; j++) { const y = Math.round(54 + j * 97.2) + 0.5; ctx.beginPath(); ctx.moveTo(L.x0, y); ctx.lineTo(L.x0 + (L.x1 - L.x0) * u, y); ctx.stroke(); }
  ctx.restore();
}
function label(ctx, t, tokens, lib) {
  const P = L.P, sec = t < S.cut[3] ? "01 / SETUP" : t < S.cut[8] ? "02 / MOTIF" : "03 / PUNCHLINE", t0 = t < S.cut[3] ? 0.2 : t < S.cut[8] ? S.cut[3] : S.cut[8];
  const txt = lib.typewriter(`[ ${sec} ]`, t, { start: t0, cps: 40 });
  ctx.save(); lib.setFont(ctx, tokens, "mono", 28, { weight: 700 }); ctx.fillStyle = t >= S.cut[8] ? P("accent") : P("extra.2");
  lib.drawText(ctx, txt, 192, 130, { tracking: 2 }); ctx.restore();
}
function cursor(ctx, t, x, y, h) { if (Math.floor(t * 4) % 2 === 0) { ctx.fillStyle = L.P("fg"); ctx.fillRect(x + 8, y - h, h * 0.55, h); } }
function titles(ctx, t, tokens, lib) {
  const P = L.P;
  if (t >= S.cut[1]) {
    lib.setFont(ctx, tokens, "display", 150, { weight: 700 }); ctx.fillStyle = P("fg");
    const s = lib.typewriter(lib.TITLE_EN, t, { start: S.cut[1], cps: 45 });
    lib.drawText(ctx, s, 192, 330, { tracking: -0.03 * 150 });
    if (t < S.cut[2]) cursor(ctx, t, 192 + ctx.measureText(s).width - 0.03 * 150 * s.length, 330, 110);
  }
  if (t >= S.cut[2]) {
    lib.setFont(ctx, tokens, "zh", 80, { weight: 600 }); ctx.fillStyle = P("fg");
    const s = lib.typewriter(lib.TITLE_ZH, t, { start: S.cut[2], cps: 24 });
    lib.drawText(ctx, s, 196, 462, { tracking: 4 });
    if (t < S.cut[3]) cursor(ctx, t, 196 + ctx.measureText(s).width + 4 * s.length, 462, 66);
  }
}
function windowChrome(ctx, lib, tokens, x, y, w, h, title) {
  const P = L.P;
  ctx.fillStyle = "#0C0C0C"; ctx.fillRect(x, y, w, h);
  ctx.fillStyle = P("extra.2"); ctx.fillRect(x, y, w, 30);
  ctx.fillStyle = "#111"; for (let i = 0; i < 3; i++) ctx.fillRect(x + 10 + i * 20, y + 9, 12, 12);
  lib.setFont(ctx, tokens, "mono", 16, { weight: 700 }); ctx.fillStyle = "#111"; ctx.fillText(title, x + 84, y + 21);
  ctx.strokeStyle = P("fg"); ctx.lineWidth = 2; ctx.strokeRect(x + 1, y + 1, w - 2, h - 2);
}
function terminal(ctx, t, tokens, lib) {                 // 0.0–0.4: the real style list, full frame; 0.4 hard cut to one row at 3×
  if (t >= S.cut[1]) return;
  const P = L.P;
  if (t < S.cut[0]) {
    const x = 40, y = 40, w = lib.W - 80, h = lib.H - 80, n = Math.min(STYLE_LIST.length, Math.floor(lib.step(t, 12) * 12 * 3 + 1e-6) + 3);
    windowChrome(ctx, lib, tokens, x, y, w, h, "zsh — bin/vh style list");
    lib.setFont(ctx, tokens, "mono", 40, { weight: 700 }); ctx.fillStyle = P("fg"); ctx.fillText("$ bin/vh style list", x + 40, y + 96);
    lib.setFont(ctx, tokens, "mono", 36, { weight: 400 }); ctx.fillStyle = "#C8C8C8";
    for (let i = 0; i < n; i++) ctx.fillText(STYLE_LIST[i], x + 40, y + 160 + i * 56);
  } else {
    windowChrome(ctx, lib, tokens, -20, 300, lib.W + 40, 420, "zsh — bin/vh style list");
    lib.setFont(ctx, tokens, "mono", 96, { weight: 700 }); ctx.fillStyle = P("fg"); ctx.fillText(STYLE_LIST[3].replace(/\s+/g, "  "), 60, 560);
    ctx.fillStyle = P("accent"); ctx.fillRect(60, 596, 860 * lib.clamp((t - S.cut[0]) * 6), 10);                        // the row gets underlined, raw
  }
}
function card(ctx, t, tokens, lib, k) {
  const P = L.P, c = L.cards[k], t0 = S.cut[3 + k];
  if (t < t0) return;
  ctx.save();
  if (k === 2) { ctx.translate(c.x + c.w / 2, c.y + c.h / 2); ctx.rotate(0.052); ctx.translate(-(c.x + c.w / 2), -(c.y + c.h / 2)); }   // the one element that breaks the grid
  windowChrome(ctx, lib, tokens, c.x, c.y, c.w, c.h, ["templates/BRIEF.md", "styles/gallery.jpg", "zsh — render.sh"][k]);
  const bx = c.x + 18, by = c.y + 30;
  if (k === 0) {                                          // outline: the real BRIEF template
    BRIEF.forEach(([ln, head], r) => { lib.setFont(ctx, tokens, "mono", 17, { weight: head ? 700 : 400 }); ctx.fillStyle = head ? P("fg") : "#A8A8A8"; ctx.fillText(ln, bx, by + 34 + r * 30); });
  } else if (k === 1) {                                   // storyboard: a crop of the real gallery (1/4 of styles/gallery.jpg), drawn 1:1
    ctx.save(); ctx.beginPath(); ctx.rect(c.x + 2, by, c.w - 4, c.h - 32); ctx.clip();
    ctx.drawImage(L.gallery, Math.round(c.x + (c.w - L.gallery.width) / 2), Math.round(by + 12)); ctx.restore();
  } else {                                                // draft: real render output, typed in line by line (steps)
    const n = Math.min(RENDER.length, Math.floor((t - t0) * 30 / 3) + 1);
    lib.setFont(ctx, tokens, "mono", 17, { weight: 400 });
    for (let r = 0; r < n; r++) { ctx.fillStyle = r === 0 ? P("fg") : "#B8B8B8"; ctx.fillText(RENDER[r], bx, by + 34 + r * 30); }
    if (n < RENDER.length && Math.floor(t * 4) % 2 === 0) { ctx.fillStyle = P("fg"); ctx.fillRect(bx, by + 34 + n * 30 - 15, 10, 18); }
  }
  ctx.restore();
  ctx.save(); ctx.fillStyle = P("fg");
  lib.setFont(ctx, tokens, "zh", 52, { weight: 600 }); ctx.fillText(lib.MOTIF[k].zh, c.x, c.y + c.h + 72);
  const LBL = { fonts: { a: { family: ["Times New Roman"], weight: 700, style: "italic" }, b: { family: ["Arial Black"], weight: 900 } } };
  if (k === 0) lib.setFont(ctx, LBL, "a", 42); else if (k === 1) lib.setFont(ctx, LBL, "b", 34); else lib.setFont(ctx, tokens, "mono", 36, { weight: 700 });   // mixed system fonts on purpose
  ctx.fillStyle = P("extra.2"); lib.drawText(ctx, `0${k + 1} ${lib.MOTIF[k].en.toUpperCase()}`, c.x + 130, c.y + c.h + 68, { tracking: 1.5 });
  ctx.restore();
}
function cursorArrow(ctx, t, lib) {
  if (t < S.cut[3] || t >= S.cut[8]) return;
  const k = [S.cut[3], S.cut[5], S.cut[6]].filter((c) => t >= c).length - 1,   // hops on the 2.0 / 2.4 / 2.8 cuts
        c = L.cards[k], x = c.x + c.w - 70, y = c.y + c.h - 40, j = lib.step(t, 8);
  ctx.save(); ctx.strokeStyle = "#F0F0F0"; ctx.lineWidth = 5; ctx.lineCap = "round"; ctx.lineJoin = "round";
  lib.wobblePath(ctx, [[x + 90, y + 70], [x + 10, y + 8]], { amp: 3, seed: 40 + k + j, seg: 20 }); ctx.stroke();
  lib.wobblePath(ctx, [[x + 34, y + 4], [x + 6, y + 6], [x + 10, y + 34]], { amp: 2.5, seed: 50 + k + j, seg: 12 }); ctx.stroke();
  ctx.restore();
}
function punchline(ctx, t, tokens, lib) {
  if (t < S.cut[8]) return;
  const P = L.P, c = L.cards[2], n = Math.min(3, Math.floor((t - S.cut[8]) * 30 / 2) + 1);        // the box draws itself in 3 steps
  const pts = [[c.x - 34, c.y - 30], [c.x + c.w + 38, c.y - 44], [c.x + c.w + 30, c.y + c.h + 36], [c.x - 40, c.y + c.h + 24], [c.x - 30, c.y - 38]];
  ctx.save(); ctx.strokeStyle = P("accent"); ctx.lineWidth = 7; ctx.lineJoin = "round"; ctx.lineCap = "round";
  lib.wobblePath(ctx, pts.slice(0, 1 + Math.ceil(n * 4 / 3)), { amp: 5, seed: 17, seg: 40 }); ctx.stroke();
  if (n === 3) { lib.setFont(ctx, tokens, "mono", 34, { weight: 700 }); ctx.fillStyle = P("accent"); lib.drawText(ctx, "← SHIP IT", c.x + c.w - 150, c.y - 70, { tracking: 2 }); }
  ctx.restore();
}
function scene(ctx, t, tokens, lib) {
  ctx.fillStyle = L.P("bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  grid(ctx, t, lib); terminal(ctx, t, tokens, lib); label(ctx, t, tokens, lib); titles(ctx, t, tokens, lib);
  for (let k = 0; k < 3; k++) card(ctx, t, tokens, lib, k);
  cursorArrow(ctx, t, lib);
  punchline(ctx, t, tokens, lib);
}
function endFrame(ctx, t, tokens, lib) {
  const P = L.P;
  ctx.fillStyle = P("bg"); ctx.fillRect(0, 0, lib.W, lib.H);
  grid(ctx, 5, lib);
  lib.setFont(ctx, tokens, "display", 520, { weight: 700 }); ctx.fillStyle = P("fg");
  lib.drawText(ctx, "BRUTAL.", 150, 690, { tracking: -0.05 * 520 });                                  // bleeds off the right edge on purpose
  ctx.fillStyle = P("accent"); ctx.fillRect(192, 760, 144, 24);
  lib.setFont(ctx, tokens, "mono", 30, { weight: 700 }); ctx.fillStyle = P("extra.2"); lib.drawText(ctx, "[ brutalist-meme ]", 360, 782, { tracking: 2 });
}

export function renderAt(t, ctx, tokens, lib) {
  const fz = T.freeze, tt = t >= fz && t < S.cut[8] ? fz : t;                                                         // held breath: the frame freezes after the 3.2 punch
  const draw = (x, time) => { const s = punch(time); if (s !== 1) { x.translate(lib.W / 2, lib.H / 2); x.scale(s, s); x.translate(-lib.W / 2, -lib.H / 2); } (time >= T.glitch + 0.2 ? endFrame : scene)(x, time, tokens, lib); };
  if (t >= T.glitch && t < T.glitch + 0.2) {                                                          // glitch: RGB split + sliced rows
    const src = lib.offscreen("bm_src", (x) => scene(x, T.glitch - 0.01, tokens, lib));
    const k = lib.frame(t);
    const sl = lib.offscreen("bm_sl", (x) => { x.drawImage(src, 0, 0); for (let i = 0; i < 9; i++) { const y = Math.floor(lib.hash(3, i, k) * lib.H), h = 20 + Math.floor(lib.hash(4, i, k) * 90), dx = Math.round(lib.hashS(5, i, k) * 140); x.drawImage(src, 0, y, lib.W, h, dx, y, lib.W, h); } });
    lib.rgbSplit(ctx, sl, { r: [12 + (k % 2) * 8, 0], g: [0, 0], b: [-14, 2] });
    return;
  }
  ctx.save(); draw(ctx, tt); ctx.restore();
}
