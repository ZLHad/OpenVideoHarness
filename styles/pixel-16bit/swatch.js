// pixel-16bit swatch: a 16-bit console screen. Everything is drawn into an INDEXED 320 × 180 framebuffer (one byte
// per pixel = an index into a fixed 24-colour palette), converted through a brightness LUT and blown up ×6 with
// nearest-neighbour to 1920 × 1080 (×4 at the 1280 × 720 delivery size: both integers, so pixels stay square).
// No anti-aliasing, no alpha, no sub-pixel positions: every coordinate is an integer function of the frame number.
//   0.10–0.37  the tile map loads: 8 × 8 tiles pop in along a diagonal from the bottom-left, the load front flashing
//              gold for one frame (hook, ≥ 20 % of the frame at 0.1 s); meanwhile the camera arrives with a
//              decelerating parallax pan (≈ 11 → 1 px per frame by 0.9 s), then keeps scrolling 1 px per frame
//   0.2–2.3    a flock of three birds crosses the sky (wings at 7.5 fps); 0.40–0.60 a shooting star
//   0.80–1.57  a message window opens in 4 stepped frames; the title prints two characters per frame, then the
//              Chinese line one character per frame; ▼ (advance marker) bobs from 1.67 s
//   2.0–2.8    motif, the pixel artist's pipeline: OUTLINE (the three keyframes as ink sketches, traced on
//              plain paper) → STORYBOARD (the same three keyframes in flat colour) → DRAFT (the shaded
//              sprite materialises in the world and walks); path dots palette-cycle between the stations
//   2.8–4.0    the sheet's highlight follows the pose the sprite is showing; hops + sparkles on 3.2 and 3.6
//   4.0–4.4    hardware-style MOSAIC 2 → 16 px with brightness steps; at the peak the world stops, switches to the
//              night palette and the name window appears; clean again at 4.4 s; the sprite walks on
// Only the Chinese glyphs come from a system font (Hiragino Sans GB 16 px, rasterised once in setup on a CPU canvas and
// thresholded to 1 bit); the Latin fonts and all art are defined below as pixel data.

const LW = 320, LH = 180, SC = 6;

// ── ONE timing table for picture and foley (frames at 30 fps; FOLEY → events.json via styles/_swatch/foley.mjs)
const F = { boot: 3, star: 12, win: 24, en0: 28, zh0: 39, more: 50, p1: 60, dots1: 63, p2: 72, keys: [72, 75, 78],
            dots2: 75, hero: 84, hops: [96, 108], mos: 120, swap: 126, clean: 132, bird: 6 };
const s = (f) => Math.round((f / 30) * 1000) / 1000;
const pan = (x) => Math.round(((2 * x) / LW - 1) * 70) / 100;          // pan = (2x/W − 1) · 0.7, x in logical px

// ── palette: 24 fixed colours, stored as BGR555 like the console's CGRAM (5 bits per channel)
// order = names below; tokens.json carries the same hexes (bg, fg, accent, extra[0..20])
const NAMES = ["ink", "night", "indigo", "violet", "plum", "rose", "coral", "amber", "gold", "cream", "mist", "slate",
               "pine", "leaf", "grass", "lime", "soil", "clay", "tan", "skin", "skinsh", "red", "wine", "blue"];
const C = Object.fromEntries(NAMES.map((n, i) => [n, i]));
const FROM_TOKENS = ["extra.0", "bg", "extra.1", "extra.2", "extra.3", "extra.4", "extra.5", "extra.6", "extra.7", "fg",
                     "extra.8", "extra.9", "extra.10", "extra.11", "extra.12", "extra.13", "extra.14", "extra.15",
                     "extra.16", "extra.17", "extra.18", "accent", "extra.19", "extra.20"];
// night palette table for the palette switch at the mosaic peak (index → index); cream/gold/red are protected
const NIGHT = { night: "ink", indigo: "night", violet: "indigo", plum: "violet", rose: "plum", coral: "plum",
                amber: "violet", gold: "plum", slate: "indigo", mist: "slate", pine: "night", leaf: "pine", grass: "leaf",
                lime: "grass", clay: "soil", tan: "clay", red: "wine" };   // applied to the world layer only (UI and sprite keep theirs)

// ── fonts: a bold 15-row title font (cap 12, x-height 8, descender 3) and a 5 × 7 caps font, both original
const BIG = {
  "E": ["########","########","##......","##......","##......","#######.","#######.","##......","##......","##......","########","########","........","........","........"],
  "v": ["........","........","........","........","##....##","##....##","##....##",".##..##.",".##..##.","..####..","..####..","...##...","........","........","........"],
  "e": ["........","........","........","........",".######.","##....##","##....##","########","##......","##......","##....##",".######.","........","........","........"],
  "r": [".......",".......",".......",".......","##.####","####..#","###....","##.....","##.....","##.....","##.....","##.....",".......",".......","......."],
  "y": ["........","........","........","........","##....##","##....##","##....##","##....##","##....##","##...###",".#######","......##","......##","##...##.",".#####.."],
  "f": ["..####",".##...",".##...",".##...","#####.",".##...",".##...",".##...",".##...",".##...",".##...",".##...","......","......","......"],
  "a": ["........","........","........","........",".######.","......##","......##",".#######","##....##","##....##","##...###",".####.##","........","........","........"],
  "m": ["..........","..........","..........","..........","####.###..","##.###.##.","##..##..##","##..##..##","##..##..##","##..##..##","##..##..##","##..##..##","..........","..........",".........."],
  "i": ["##","##","..","..","##","##","##","##","##","##","##","##","..","..",".."],
  "s": ["........","........","........","........",".#######","##......","##......",".######.","......##","......##","......##","#######.","........","........","........"],
  "c": ["........","........","........","........",".######.","##....##","##......","##......","##......","##......","##....##",".######.","........","........","........"],
  "o": ["........","........","........","........",".######.","##....##","##....##","##....##","##....##","##....##","##....##",".######.","........","........","........"],
  "d": ["......##","......##","......##","......##",".#######","##....##","##....##","##....##","##....##","##....##","##...###",".####.##","........","........","........"],
  ".": ["..","..","..","..","..","..","..","..","..","..","##","##","..","..",".."],
  " ": ["....","....","....","....","....","....","....","....","....","....","....","....","....","....","...."],
  "P": ["#######.","########","##....##","##....##","##....##","########","#######.","##......","##......","##......","##......","##......","........","........","........"],
  "I": ["######","######","..##..","..##..","..##..","..##..","..##..","..##..","..##..","..##..","######","######","......","......","......"],
  "X": ["##....##","##....##",".##..##.",".##..##.","..####..","...##...","...##...","..####..",".##..##.",".##..##.","##....##","##....##","........","........","........"],
  "L": ["##......","##......","##......","##......","##......","##......","##......","##......","##......","##......","########","########","........","........","........"],
  "B": ["#######.","########","##....##","##....##","##...##.","#######.","########","##....##","##....##","##....##","########","#######.","........","........","........"],
  "T": ["########","########","...##...","...##...","...##...","...##...","...##...","...##...","...##...","...##...","...##...","...##...","........","........","........"],
  "1": ["..##..",".###..","####..","..##..","..##..","..##..","..##..","..##..","..##..","..##..","######","######","......","......","......"],
  "6": ["..#####.",".##.....","##......","##......","#######.","########","##....##","##....##","##....##","##....##","########",".######.","........","........","........"],
  "-": ["......","......","......","......","......","......","######","######","......","......","......","......","......","......","......"],
};
const SMALL_SRC = {                                                  // 5 × 7 caps, rows top → bottom
  A: [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"], B: ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
  D: ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."], E: ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
  F: ["#####", "#....", "#....", "####.", "#....", "#....", "#...."], I: [".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."],
  L: ["#....", "#....", "#....", "#....", "#....", "#....", "#####"], N: ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
  O: [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."], R: ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
  S: [".####", "#....", "#....", ".###.", "....#", "....#", "####."], T: ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
  U: ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."], Y: ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
};

// ── the sprite: 24 × 32, side view facing right; three keyframes share the head, differ in torso and legs
const KEY = { K: "ink", H: "clay", h: "tan", j: "soil", S: "skin", s: "skinsh", W: "cream", R: "red", r: "wine",
              B: "blue", b: "indigo", T: "tan", C: "clay", D: "soil" };
const FLAT = { h: "H", j: "H", s: "S", r: "R", b: "B", D: "C" };           // keyframe sheet: no shading, base colours
const HEAD = [
  "........................", ".........K...KK.........", "........KhK.KhhK........", ".......KhHKKhHHhKK......",
  "......KhHHhhHHHHHhK.....", ".....KhHHHHHHHHHHHHK....", "....KjHHHHHHHHHHHHHHK...", "...KjHHHHHHHHHHHHhHHHK..",
  "..KjjHHHHHHHHSHHHSHHHK..", "..KjjHHHHHHHSSSHSSSSSK..", "...KjHHHHHHsSSSSSSKSSK..", "...KjjHHHHssSSSSSSKSSSK.",
  "....KjHHHHssSSSSSSSSSK..", "....KjjHHHKsSSSSSSSSK...", ".....KKjjKKKsSSSSSKK....", ".......KKRRRRRRRRRK.....",
  ".....KKrRRRRRRRRRRRK....", "...KKrrRRRRRRRRRRRRK....",
];
const TORSO = {
  down: ["..KrrRRKKbBBBBBBBBK.....", ".KrRRKK.KbBBBbBBBBK.....", ".KRRK...KbBBBbBBBBK.....", "..KK....KbBBBbBBBBK.....",
         "........KbBBBbSSSBK.....", "........KTTTTKsSsKK.....", "........KbBBBBKKKBK.....", "........KKbbBBBBBKK....."],
  back: ["..KrrRRKKbBBBBBBBBK.....", ".KrRRKK.KbBBbBBBBBK.....", ".KRRK...KbBbBBBBBBK.....", "..KK...KSsbBBBBBBBK.....",
         ".......KsSKBBBBBBBK.....", "........KKTTTTTTTTK.....", "........KbBBBBBBBBK.....", "........KKbbBBBBBKK....."],
  fwd:  ["..KrrRRKKbBBBBBBBBK.....", ".KrRRKK.KbBBBBbBBBK.....", ".KRRK...KbBBBBBbBBK.....", "..KK....KbBBBBBBbBKK....",
         "........KbBBBBBBBKSSK...", "........KTTTTTTTTKsSK...", "........KbBBBBBBBBKK....", "........KKbbBBBBBKK....."],
};
const LEGS = {
  pass: [".........KCCKKCCCK......", ".........KCCK.KCCK......", ".........KCCK.KCCK......", ".........KDCCK.KDCCK....",
         "........KDDDDKKDDDDK....", "........KKKKKKKKKKKK...."],
  A:    [".........KDDKKCCK.......", "........KDDK.KCCK.......", "......KDDDK...KCCK......", ".....KDDDK.....KDCCCK...",
         ".....KKKKK.....KKKKKK..."],
  B:    [".........KCCKKDDK.......", "........KCCK.KDDK.......", "......KCCCK...KDDK......", ".....KDCCK.....KDDDDK...",
         ".....KKKKK.....KKKKKK..."],
};
const POSE_ROWS = {   // contact poses are one pixel lower (shorter legs): the body bobs down on each footfall
  A: ["........................", ...HEAD, ...TORSO.back, ...LEGS.A],
  P: [...HEAD, ...TORSO.down, ...LEGS.pass],
  B: ["........................", ...HEAD, ...TORSO.fwd, ...LEGS.B],
};
const CYCLE = ["A", "P", "B", "P"];            // 10 poses per second: one 4-pose cycle = 0.4 s = one beat at 150 BPM
const SHEET = ["A", "P", "B"];                  // the storyboard: three keyframes
const HOP = [-4, -8, -11, -12, -11, -8, -4];    // pixel offsets, one per 30 fps frame

// ── layout (logical pixels)
const WIN = { x: 70, y: 10, w: 180, h: 48 };
const EN = { x: 84, y: 16 }, ZH = { x: 84, y: 34 };
const SLOT = [74, 176, 262];
const PANEL1 = { x: 32, y: 104, w: 84, h: 38 }, PANEL2 = { x: 134, y: 104, w: 84, h: 38 };
const HERO0 = { x: 250, y: 116 };
const END_WIN = { x: 98, y: 30, w: 124, h: 48 };
const GROUND = 148;

export const FOLEY = [
  { t: s(F.boot), sfx: "boom", gain_db: -12, pan: pan(40) },                              // the tile map loads
  { t: s(F.boot + 2), sfx: "whip", gain_db: -13, pan: pan(160), dur: 0.25 },
  { t: s(F.star + 3), sfx: "ding", gain_db: -20, pan: pan(90) },                           // shooting star
  { t: s(F.win), sfx: "pop", gain_db: -12, pan: 0 },                                       // window opens
  ...[0, 6, 12].map((i) => ({ t: s(F.en0 + Math.floor(i / 2)), sfx: "tick", gain_db: -17, pan: pan(EN.x + i * 8) })),   // text blips per word
  ...[0, 4].map((i) => ({ t: s(F.zh0 + i), sfx: "tick", gain_db: -17, pan: pan(ZH.x + i * 17) })),
  { t: s(F.more), sfx: "click", gain_db: -18, pan: pan(240) },                             // ▼
  { t: s(F.p1), sfx: "pop", gain_db: -12, pan: pan(SLOT[0]) },                             // OUTLINE panel
  { t: s(F.p2), sfx: "pop", gain_db: -12, pan: pan(SLOT[1]) },                             // STORYBOARD panel
  ...F.keys.slice(1).map((f, k) => ({ t: s(f), sfx: "tick", gain_db: -16, pan: pan(SLOT[1] + (k ? 27 : 0)) })),
  { t: s(F.hero), sfx: "success", gain_db: -10, pan: pan(SLOT[2]) },                       // DRAFT: the sprite is alive
  ...F.hops.map((f) => ({ t: s(f), sfx: "pop", gain_db: -14, pan: pan(SLOT[2]) })),       // hops
  { t: s(F.mos + 5), sfx: "swoosh_tonal", gain_db: -14, pan: 0, dur: 0.4, dir: "down", bright: 0.3 },                                // mosaic peak
  { t: s(F.clean), sfx: "ding", gain_db: -14, pan: 0 },                                    // mosaic clears on the night scene
];

export const fonts = ["Hiragino Sans GB", "Heiti SC"];

// ─────────────────────────────── setup: pure data only ───────────────────────────────
let D = null;

function parseSprite(rows, map = (ch) => ch) {
  const h = rows.length, w = rows[0].length, px = new Int8Array(w * h).fill(-1);
  rows.forEach((r, y) => [...r].forEach((ch, x) => { if (ch !== ".") px[y * w + x] = C[KEY[map(ch)]]; }));
  return { w, h, px };
}
function parseBig(rows) {
  const h = rows.length, w = rows[0].length, m = new Uint8Array(w * h);
  rows.forEach((r, y) => [...r].forEach((ch, x) => { m[y * w + x] = ch === "#" ? 1 : 0; }));
  return { w, h, m };
}
function parseSmall(rows) { return parseBig(rows); }

// Chinese: rasterise each character once on a CPU-backed canvas (willReadFrequently) and threshold at 50 % coverage
function rasterCJK(lib, tokens, chars, size) {
  const c = document.createElement("canvas"); c.width = size + 8; c.height = size + 8;
  const g = c.getContext("2d", { willReadFrequently: true });
  const raw = {};
  let top = 99, bot = -1;
  for (const ch of chars) {
    g.reset(); lib.setFont(g, tokens, "zh", size, { weight: 300 });
    g.fillStyle = "#fff"; g.textBaseline = "alphabetic"; g.fillText(ch, 2, size);
    const d = g.getImageData(0, 0, c.width, c.height).data, m = new Uint8Array(c.width * c.height);
    for (let i = 0; i < m.length; i++) if (d[i * 4 + 3] >= 128) { m[i] = 1; const y = Math.floor(i / c.width); top = Math.min(top, y); bot = Math.max(bot, y); }
    raw[ch] = m;
  }
  const out = {}, h = bot - top + 1, w = size + 1;
  for (const ch of chars) {
    const m = new Uint8Array(w * h);
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) m[y * w + x] = raw[ch][(y + top) * c.width + x + 2] || 0;
    out[ch] = { w, h, m };
  }
  return out;
}

export async function setup(ctx, tokens, lib) {
  // palette → BGR555 → brightness LUTs (16 levels, like the console's master brightness register)
  const q = (v) => Math.round((v * 31) / 255), up = (v5) => (v5 << 3) | (v5 >> 2);
  const pal = FROM_TOKENS.map((k) => lib.rgb(lib.color(tokens, k)).map(q));
  const lut = [];
  for (let b = 0; b <= 15; b++) {
    const row = new Uint32Array(24);
    pal.forEach(([r, g, bl], i) => { const f = (v) => up(Math.floor((v * b) / 15)); row[i] = (255 << 24) | (f(bl) << 16) | (f(g) << 8) | f(r); });
    lut.push(row);
  }
  const night = new Uint8Array(24).map((_, i) => (NIGHT[NAMES[i]] ? C[NIGHT[NAMES[i]]] : i));

  const big = Object.fromEntries(Object.entries(BIG).map(([k, v]) => [k, parseBig(v)]));
  const small = Object.fromEntries(Object.entries(SMALL_SRC).map(([k, v]) => [k, parseSmall(v)]));
  const cjk = rasterCJK(lib, tokens, [...new Set([...lib.TITLE_ZH, ..."大纲分镜初版十六位像素"])], 16);

  const poses = {}, flat = {};
  for (const k of ["A", "P", "B"]) { poses[k] = parseSprite(POSE_ROWS[k]); flat[k] = parseSprite(POSE_ROWS[k], (ch) => FLAT[ch] || ch); }
  // the outlines: every ink pixel of each keyframe, ordered clockwise from 12 o'clock (the trace order)
  const outlines = SHEET.map((k) => {
    const A = poses[k], o = [];
    for (let y = 0; y < A.h; y++) for (let x = 0; x < A.w; x++) if (A.px[y * A.w + x] === C.ink) o.push([x, y, (Math.atan2(x - 12, -(y - 16)) + Math.PI * 2) % (Math.PI * 2)]);
    return o.sort((a, b) => a[2] - b[2] || a[1] - b[1] || a[0] - b[0]);
  });

  // parallax layers: periodic height maps (period = LW so the scroll wraps seamlessly)
  const TAU = Math.PI * 2, mount = new Int16Array(LW), hills = new Int16Array(LW);
  for (let x = 0; x < LW; x++) {
    const u = x / LW;
    mount[x] = Math.round(104 - 7 * Math.sin(TAU * 2 * u + 0.6) - 5 * Math.sin(TAU * 5 * u + 1.9) - 3 * Math.abs(Math.sin(TAU * 11 * u)));
    let hy = 132 - 3 * Math.sin(TAU * 3 * u + 0.3);
    for (let k = 0; k < 16; k++) {                                   // round tree canopies on the hill line
      const cx = (k * 20 + 7 * ((k * 5) % 3)) % LW, r = 5 + ((k * 7) % 3);
      let dx = Math.abs(x - cx); dx = Math.min(dx, LW - dx);
      if (dx <= r) hy = Math.min(hy, 128 - Math.sqrt(r * r - dx * dx) * 0.9 - (k % 2) * 2);
    }
    hills[x] = Math.round(hy);
  }
  // ground tile, 32 px wide: grass lip, hanging blades, speckled soil with pebbles
  const gt = new Uint8Array(32 * (LH - GROUND));
  for (let y = 0; y < LH - GROUND; y++) for (let x = 0; x < 32; x++) {
    let c = C.clay;
    if (y === 0) c = x % 8 === 3 ? C.grass : C.lime;
    else if (y <= 3) c = (x + y) % 11 === 0 ? C.leaf : C.grass;
    else if (y === 4) c = x % 5 !== 2 ? C.grass : C.leaf;
    else if (y === 5) c = x % 5 === 0 || x % 7 === 3 ? C.leaf : C.soil;
    else { const h = lib.hash(x, y, 77); c = h < 0.09 ? C.soil : h > 0.97 ? C.tan : C.clay; }
    gt[y * 32 + x] = c;
  }
  // foreground bush line, 160-px period: 0 (gap) or a rounded bump 5–10 px tall
  const fg = new Int16Array(160);
  for (const [cx, r, h] of [[18, 16, 9], [44, 11, 6], [96, 20, 10], [130, 9, 5]])
    for (let x = cx - r; x <= cx + r; x++) { const i = ((x % 160) + 160) % 160, d = (x - cx) / r; fg[i] = Math.max(fg[i], Math.round(h * Math.sqrt(1 - d * d))); }
  // stars (upper sky) and clouds (row spans)
  const stars = Array.from({ length: 46 }, (_, i) => [Math.floor(lib.hash(i, 1) * LW), Math.floor(lib.hash(i, 2) * 46), lib.hash(i, 3)]);
  const CL = { r: C.rose, c: C.coral, a: C.amber, p: C.plum };
  const shape = (rows) => rows.map((r) => [...r].map((ch) => (ch === "." ? -1 : CL[ch])));
  const cBig = shape(["..........rrrrrr..................", ".....rrrrrrrrrrrrr....rrrrr.......", "..rrrrrrrrrrrrrrrrrrrrrrrrrrrr....",
                     "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr", "cccccccccccccccccccccccccccccccccc", "..aaaaaaaaaaaaaaa..aaaaaaaaaa....."]);
  const cSmall = shape(["......rrrrr.........", "..rrrrrrrrrrr.rrr...", "rrrrrrrrrrrrrrrrrrrr", "cccccccccccccccccccc", ".aaaaaaaa..aaaaaa..."]);
  const clouds = [{ x: 10, y: 60, s: cBig }, { x: 150, y: 64, s: cSmall }, { x: 226, y: 58, s: cBig }, { x: 96, y: 44, s: cSmall }];
  const cv = document.createElement("canvas"); cv.width = LW; cv.height = LH;
  const cx = cv.getContext("2d", { willReadFrequently: true });
  const img = cx.createImageData(LW, LH);
  D = { lut, night, big, small, cjk, poses, flat, outlines, mount, hills, gt, fg, stars, clouds, cv, cx, img,
        u32: new Uint32Array(img.data.buffer), fb: new Uint8Array(LW * LH), tmp: new Uint8Array(LW * LH) };
}

// ─────────────────────────────── framebuffer primitives ───────────────────────────────
function px(x, y, c) { if (x >= 0 && y >= 0 && x < LW && y < LH) D.fb[y * LW + x] = c; }
function rect(x, y, w, h, c) {
  const x0 = Math.max(0, x), y0 = Math.max(0, y), x1 = Math.min(LW, x + w), y1 = Math.min(LH, y + h);
  for (let j = y0; j < y1; j++) D.fb.fill(c, j * LW + x0, j * LW + x1);
}
function blit(spr, x, y, recolor) {
  for (let j = 0; j < spr.h; j++) for (let i = 0; i < spr.w; i++) {
    const c = spr.px[j * spr.w + i]; if (c >= 0) px(x + i, y + j, recolor === undefined ? c : recolor);
  }
}
function mask(g, x, y, fill, { outline, shadow } = {}) {       // 1-bit glyph; fill = index or (row) => index
  const on = (i, j) => i >= 0 && j >= 0 && i < g.w && j < g.h && g.m[j * g.w + i];
  if (outline !== undefined) for (let j = -1; j <= g.h; j++) for (let i = -1; i <= g.w; i++)
    if (!on(i, j) && (on(i - 1, j) || on(i + 1, j) || on(i, j - 1) || on(i, j + 1) || on(i - 1, j - 1) || on(i + 1, j - 1) || on(i - 1, j + 1) || on(i + 1, j + 1))) px(x + i, y + j, outline);
  if (shadow !== undefined) for (let j = 0; j < g.h; j++) for (let i = 0; i < g.w; i++) if (on(i, j) && !on(i + 1, j + 1)) px(x + i + 1, y + j + 1, shadow);
  for (let j = 0; j < g.h; j++) for (let i = 0; i < g.w; i++) if (on(i, j)) px(x + i, y + j, typeof fill === "function" ? fill(j) : fill);
}
const bigW = (str) => [...str].reduce((a, ch) => a + D.big[ch].w + 1, -1);
function bigText(str, x, y, n = Infinity) {                    // banded fill cream → gold → amber, 8-neighbour ink outline
  const band = (j) => (j < 4 ? C.cream : j < 8 ? C.gold : j < 12 ? C.amber : C.coral);
  [...str].slice(0, n).forEach((ch) => { mask(D.big[ch], x, y, band, { outline: C.ink }); x += D.big[ch].w + 1; });
}
function smallText(str, x, y, c, outline = C.ink) {
  for (const ch of str) { if (ch !== " ") mask(D.small[ch], x, y, c, { outline }); x += 6; }
}
function cjkText(str, x, y, c, { n = Infinity, outline, shadow } = {}) {
  [...str].slice(0, n).forEach((ch) => { mask(D.cjk[ch], x, y, c, { outline, shadow }); x += 17; });
}

// ─────────────────────────────── the world ───────────────────────────────
const SKY = [[0, "night"], [24, "indigo"], [42, "violet"], [58, "plum"], [72, "rose"], [86, "coral"], [98, "amber"], [108, "gold"]];
const B2 = [[0, 2], [3, 1]];
function sky() {
  for (let y = 0; y < GROUND; y++) {
    let k = 0; while (k + 1 < SKY.length && SKY[k + 1][0] <= y) k++;
    const c0 = C[SKY[k][1]], nxt = SKY[k + 1], c1 = nxt ? C[nxt[1]] : c0;
    const left = nxt ? nxt[0] - y : 99;                                  // 3 dither rows before each band edge: 25/50/75 %
    for (let x = 0; x < LW; x++) D.fb[y * LW + x] = left <= 3 && B2[y & 1][x & 1] < 4 - left ? c1 : c0;
  }
}
function stars(f) {
  const tw = Math.floor(f / 7);                                           // twinkle ~4 times per second
  D.stars.forEach(([x, y, r], i) => {
    const on = ((i * 7 + tw) % 5) !== 0;
    if (r > 0.86 && on) { px(x, y, C.cream); px(x - 1, y, C.mist); px(x + 1, y, C.mist); px(x, y - 1, C.mist); px(x, y + 1, C.mist); }
    else if (on) px(x, y, r > 0.5 ? C.cream : C.mist);
  });
}
// the camera: arrives with a decelerating pan (≈ 11 → 1 px per frame over 0.9 s), then 1 px per frame; it stops at the
// mosaic peak (hidden by the mosaic) so the end scene has a still world and a walking sprite
function cam(f) {
  const g = (k) => k + Math.round(90 * (1 - Math.pow(1 - Math.min(1, k / 27), 3)));
  return g(Math.min(f, F.swap));
}
function clouds(f) {                                                 // lit from below by the low sun
  const off = Math.floor(f / 10), P = LW + 60;
  D.clouds.forEach((cl) => cl.s.forEach((row, j) => row.forEach((c, i) => {
    if (c >= 0) px(((((cl.x + i - off) % P) + P) % P) - 30, cl.y + j, c);
  })));
}
function mountains(f) {
  const o = Math.floor(cam(f) / 6);
  for (let x = 0; x < LW; x++) {
    const i = (x + o) % LW, h = D.mount[i], hl = D.mount[(i + LW - 1) % LW];
    for (let y = h; y < GROUND; y++) D.fb[y * LW + x] = C.slate;
    px(x, h, h > hl ? C.slate : C.mist); if (h < 99) { px(x, h + 1, C.mist); }
  }
}
function hillLayer(f) {
  const o = Math.floor(cam(f) / 3);
  for (let x = 0; x < LW; x++) {
    const i = (x + o) % LW, h = D.hills[i], hr = D.hills[(i + 1) % LW];
    for (let y = h; y < GROUND; y++) D.fb[y * LW + x] = (y - h) % 9 === 4 && (x + o) % 6 === 0 ? C.leaf : C.pine;
    px(x, h, h <= hr ? C.leaf : C.pine);
  }
}
const DECO = [  // 64-px period, drawn above the grass line and scrolled with the ground: [x, rows bottom → top]
  [5, ["g.g", "lgl", ".l."]], [23, [".l.", ".R.", "RYR", ".R."]], [30, ["l.l", ".l."]], [44, ["mmmm", ".nn."]],
  [52, [".l.", ".W.", "WYW", ".W."]],
];
const DC = { g: "grass", l: "lime", R: "red", Y: "gold", W: "cream", m: "slate", n: "mist" };
function ground(f) {
  const g = cam(f);
  for (let y = GROUND; y < LH; y++) for (let x = 0; x < LW; x++) D.fb[y * LW + x] = D.gt[(y - GROUND) * 32 + ((x + g) & 31)];
  for (let base = -64; base < LW + 64; base += 64) for (const [dx, rows] of DECO) {
    const x0 = base + dx - (g % 64);
    rows.forEach((r, j) => [...r].forEach((ch, i) => { if (ch !== ".") px(x0 + i, GROUND - 1 - j, C[DC[ch]]); }));
  }
}
function foreground(f) {                                             // nearest layer: bushes along the bottom edge, 2 px/frame
  const o = 2 * cam(f);
  for (let x = 0; x < LW; x++) {
    const i = (((x + o) % 160) + 160) % 160, h = D.fg[i];
    for (let y = LH - h; y < LH; y++) D.fb[y * LW + x] = y === LH - h || (y === LH - h + 1 && i % 3 === 0) ? C.leaf : ((i * 5 + y * 3) % 13 === 0 ? C.night : C.pine);
  }
}
function world(f) { sky(); stars(f); clouds(f); mountains(f); hillLayer(f); ground(f); foreground(f); }

// ─────────────────────────────── UI ───────────────────────────────
function frameBox(x, y, w, h, fill) {                               // ink / cream / ink border, clipped corners
  rect(x + 1, y, w - 2, h, C.ink); rect(x, y + 1, w, h - 2, C.ink);
  rect(x + 1, y + 1, w - 2, h - 2, C.cream);
  rect(x + 2, y + 2, w - 4, h - 4, C.ink);
  if (fill) fill(x + 3, y + 3, w - 6, h - 6);
}
function windowFill(x, y, w, h) {                                   // indigo → night, dithered steps
  for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) {
    const u = j / h, d = B2[j & 1][i & 1] / 4;
    px(x + i, y + j, u + d * 0.25 < 0.45 ? C.indigo : u + d * 0.25 < 0.55 ? (d < 0.5 ? C.night : C.indigo) : C.night);
  }
}
function checker(x, y, w, h) { for (let j = 0; j < h; j++) for (let i = 0; i < w; i++) px(x + i, y + j, ((i >> 2) + (j >> 2)) & 1 ? C.mist : C.cream); }
function opening(f, f0, b, fill) {                                 // stepped open: a line, 1/3, 2/3, full (one per frame)
  const k = f - f0; if (k < 0) return false;
  if (k >= 3) { frameBox(b.x, b.y, b.w, b.h, fill); return true; }
  const h = [4, Math.round(b.h / 3), Math.round((2 * b.h) / 3)][k], y = b.y + Math.floor((b.h - h) / 2);
  frameBox(b.x, y, b.w, h, h > 6 ? fill : null); return false;
}

function ui(f, tokens, lib) {
  // message window + title
  if (opening(f, F.win, WIN, windowFill)) {
    bigText(lib.TITLE_EN, EN.x, EN.y, Math.max(0, 2 * (f - F.en0 + 1)));          // two characters per frame
    const nz = f - F.zh0 + 1;                                         // one character per frame
    if (nz > 0) cjkText(lib.TITLE_ZH, ZH.x, ZH.y, C.cream, { n: nz, shadow: C.ink });
    if (f >= F.more) {                                                // ▼ advance marker, 2-pose bob at 4 fps
      const y = WIN.y + WIN.h - 9 + (Math.floor((f - F.more) / 8) % 2);
      for (let j = 0; j < 3; j++) rect(WIN.x + WIN.w - 14 + j, y + j, 5 - 2 * j, 1, C.gold);
    }
  }
  // OUTLINE: the three keyframes as ink line sketches, traced on the transparency checker in 12 fps steps
  if (opening(f, F.p1, PANEL1, (x, y, w, h) => rect(x, y, w, h, C.cream))) {   // sketches on plain paper
    const u = Math.min(1, Math.floor(((f - F.p1 - 3) * 12) / 30 + 1) / 4);
    D.outlines.forEach((o, s) => {
      const n = Math.round(o.length * u);
      for (let i = 0; i < n; i++) px(PANEL1.x + 3 + s * 26 + o[i][0], PANEL1.y + 3 + o[i][1], C.ink);
    });
  }
  if (f >= F.p1) label(0);
  // STORYBOARD: three flat keyframes; after the sprite is alive, a gold box marks the pose it is showing
  if (opening(f, F.p2, PANEL2, checker)) {
    SHEET.forEach((k, i) => { if (f >= F.keys[i] + 1) blit(D.flat[k], PANEL2.x + 3 + i * 26, PANEL2.y + 3); });
    if (f >= F.hero + 4) {
      const pose = poseAt(f), i = SHEET.indexOf(pose), x = PANEL2.x + 2 + i * 26, y = PANEL2.y + 2;
      rect(x, y, 26, 1, C.gold); rect(x, y + 33, 26, 1, C.gold); rect(x, y, 1, 34, C.gold); rect(x + 25, y, 1, 34, C.gold);
    }
  }
  if (f >= F.p2) label(1);
  if (f >= F.hero) label(2);
  // path dots between the stations, palette-cycled (the colour moves, the dots don't)
  const dot = (x, k, f0) => {
    if (f < f0 + k) return;
    const c = [C.cream, C.gold, C.amber, C.gold][(((k - Math.floor(f / 3)) % 4) + 4) % 4];
    rect(x + 1, 125, 2, 2, C.ink); rect(x, 124, 2, 2, c);
  };
  for (let k = 0; k < 4; k++) dot(PANEL1.x + PANEL1.w + 3 + k * 4, k, F.dots1);
  for (let k = 0; k < 7; k++) dot(PANEL2.x + PANEL2.w + 4 + k * 4, k, F.dots2);
}
function label(i) {
  const zh = ["大纲", "分镜", "初版"][i], en = ["OUTLINE", "STORYBOARD", "DRAFT"][i];
  cjkText(zh, SLOT[i] - 17, 72, C.cream, { outline: C.ink });
  smallText(en, SLOT[i] - Math.floor((en.length * 6 - 1) / 2), 92, C.gold);
}
const poseAt = (f) => CYCLE[Math.floor(Math.max(0, f - F.hero) / 3) % 4];

function hero(f) {
  if (f < F.hero) return;
  const k = f - F.hero, HERO = { x: HERO0.x + Math.max(0, f - F.swap), y: HERO0.y };   // walks on once the world stops
  let dy = 0, pose = poseAt(f);
  for (const h of F.hops) if (f >= h && f < h + HOP.length) { dy = HOP[f - h]; pose = "P"; }
  // shadow on the grass (shrinks while airborne)
  const sw = dy ? 10 : 14; rect(HERO.x + 12 - sw / 2, GROUND - 1, sw, 2, C.leaf);
  const spr = k < 2 ? D.poses[pose] : k < 4 ? D.flat[pose] : D.poses[pose];
  blit(spr, HERO.x, HERO.y + dy, k < 2 ? C.cream : undefined);      // materialise: white → flat → shaded
  for (const f0 of [F.hero, ...F.hops]) sparkle(f - f0, HERO.x + 22, HERO.y + 2 + (f0 === F.hero ? 0 : dy));
}
function sparkle(k, x, y) {                                         // 4-point star, 6 frames
  if (k < 0 || k > 5) return;
  const r = [1, 2, 4, 3, 2, 1][k], c = k < 3 ? C.cream : C.gold;
  for (let i = -r; i <= r; i++) { px(x + i, y, c); px(x, y + i, c); }
  if (r >= 3) { px(x - 1, y - 1, C.gold); px(x + 1, y - 1, C.gold); px(x - 1, y + 1, C.gold); px(x + 1, y + 1, C.gold); }
}
const BIRD = [["K.....K", ".K...K.", "..KKK..", "...K..."], [".......", "KKK.KKK", "..KKK..", "...K..."]];
function birds(f) {                                                  // a small flock crosses the sky 0.2–2.3 s, wings at 7.5 fps
  if (f < F.bird || f > F.bird + 70) return;
  const k = f - F.bird, x0 = -10 + 5 * k, y0 = 92 - Math.floor(k / 5);
  [[0, 0, 0], [-11, -5, 1], [-20, 3, 0]].forEach(([dx, dy, ph]) => {
    BIRD[(Math.floor(f / 4) + ph) % 2].forEach((r, j) => [...r].forEach((ch, i) => { if (ch === "K") px(x0 + dx + i, y0 + dy + j, C.ink); }));
  });
}
function shootingStar(f) {
  const k = f - F.star; if (k < 0 || k > 6) return;
  const hx = 34 + k * 16, hy = 8 + k * 5;
  [C.cream, C.cream, C.gold, C.amber, C.plum].forEach((c, j) => { px(hx - j * 3, hy - j, c); px(hx - j * 3 - 1, hy - j, c); px(hx - j * 3 - 2, hy - j - 1, j < 2 ? c : C.plum); });
}
function tileLoad(f) {                                              // the hook: 8 × 8 tiles load along a diagonal
  if (f >= 12) return;
  for (let ty = 0; ty < 23; ty++) for (let tx = 0; tx < 40; tx++) {
    const v = 22 - ty + 0.35 * tx, lf = F.boot + Math.max(0, Math.ceil((v - 12) / 3.2));
    if (f > lf || (f === lf && v < 8.8)) continue;                   // loaded: the art shows
    rect(tx * 8, ty * 8, 8, 8, f === lf ? C.gold : C.ink);           // the load front flashes gold for one frame
  }
}
function endCard(f, lib) {                                          // the name, in the same message window
  frameBox(END_WIN.x, END_WIN.y, END_WIN.w, END_WIN.h, windowFill);
  const title = "PIXEL 16-BIT", w = bigW(title);
  bigText(title, END_WIN.x + Math.floor((END_WIN.w - w) / 2), END_WIN.y + 6);
  cjkText("十六位像素", END_WIN.x + Math.floor((END_WIN.w - 84) / 2), END_WIN.y + 25, C.cream, { shadow: C.ink });
}

// ─────────────────────────────── frame ───────────────────────────────
export function renderAt(t, ctx, tokens, lib) {
  const f = lib.frame(t);
  D.fb.fill(C.ink);
  const end = f >= F.swap;
  world(f);
  if (f < F.win) shootingStar(f);
  birds(f);
  if (end) for (let i = 0; i < D.fb.length; i++) D.fb[i] = D.night[D.fb[i]];   // palette switch on the BG (index → index)
  if (!end) ui(f, tokens, lib); else endCard(f, lib);
  hero(f);
  tileLoad(f);

  // mosaic 2 → 16 → 1 (block size steps every frame; the scene switches on the 2nd 16) + master brightness 15 → 9 → 15
  const MOS = [2, 4, 6, 8, 12, 16, 16, 12, 8, 6, 4, 2];              // clean again at F.clean = 4.4 s
  const k = f - F.mos, m = k >= 0 && k < MOS.length ? MOS[k] : 1;
  const bright = k >= 0 && k < MOS.length ? 15 - Math.min(6, k < 6 ? k + 1 : MOS.length - k) : 15;
  const lut = D.lut[bright], fb = D.fb, out = D.u32;
  if (m === 1) for (let i = 0; i < fb.length; i++) out[i] = lut[fb[i]];
  else for (let y = 0; y < LH; y++) { const sy = y - (y % m); for (let x = 0; x < LW; x++) out[y * LW + x] = lut[fb[sy * LW + x - (x % m)]]; }
  D.cx.putImageData(D.img, 0, 0);
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(D.cv, 0, 0, LW * SC, LH * SC);
}
