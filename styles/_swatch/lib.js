// lib.js — shared helpers for style swatch scenes. Everything here is a pure function of its arguments
// (t, seed, options). Caches only memoise deterministic results (textures, layouts), so frame N renders the same
// whether it is drawn first, last or alone. Scenes receive this module as `lib`; see README.md for the API table.

// ───────────────────────── frame, timing, content spec ─────────────────────────
export const W = 1920, H = 1080, FPS = 30, DUR = 5, FRAMES = 150, POSTER_T = 3.0;
/** Shared content spec (seconds). Every swatch follows it so the gallery compares like with like. */
export const SPEC = { establish: [0, 0.8], title: [0.8, 2.6], motif: [2.0, 4.0], outro: [4.0, 5.0], poster: 3.0 };
export const TITLE_EN = "Every frame is code.";
export const TITLE_ZH = "每一帧，都是代码。";
/** The 3-element motif, left to right: outline → storyboard → draft. */
export const MOTIF = [
  { key: "outline", en: "Outline", zh: "大纲" },
  { key: "storyboard", en: "Storyboard", zh: "分镜" },
  { key: "draft", en: "Draft", zh: "初版" },
];

function box(x0, y0, x1, y1) { return { x0, y0, x1, y1, x: x0, y: y0, w: x1 - x0, h: y1 - y0, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 }; }
/** action: EBU R95 90 % graphics-safe (text ≥ 96 px from the sides, ≥ 54 px from top/bottom). title: 80 % title-safe. */
export const SAFE = { action: box(96, 54, W - 96, H - 54), title: box(192, 108, W - 192, H - 108) };

/** 6×6 anchor grid over the action-safe box, cells A1 (top-left) … F6 (bottom-right): letter = column, digit = row. */
export function anchor(name, area = SAFE.action) {
  const c = name.toUpperCase().charCodeAt(0) - 65, r = parseInt(name.slice(1), 10) - 1;
  return { x: area.x0 + (c + 0.5) * area.w / 6, y: area.y0 + (r + 0.5) * area.h / 6 };
}
/** n evenly spaced slot centres across a band (default: 3 motif slots on the horizontal centre line). */
export function slots(n = 3, { area = SAFE.title, y = H / 2, gap = 0 } = {}) {
  const w = (area.w - gap * (n - 1)) / n;
  return Array.from({ length: n }, (_, i) => ({ x: area.x0 + i * (w + gap) + w / 2, y, w }));
}

export const frame = (t) => Math.round(t * FPS);
/** Hold time on a lower frame rate ("on twos" = step(t, 15)); returns the start time of the held step. */
export const step = (t, fps = 12) => Math.floor(frame(t) * fps / FPS + 1e-9) / fps;

// ───────────────────────── math ─────────────────────────
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, u) => a + (b - a) * u;
export const invlerp = (a, b, x) => (x - a) / (b - a);
export const remap = (x, a, b, c, d) => lerp(c, d, invlerp(a, b, x));
/** 0→1 progress of t across [a, b], clamped. */
export const seg = (t, a, b) => clamp((t - a) / (b - a));
export const smoothstep = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };
export const fract = (x) => x - Math.floor(x);
export const TAU = Math.PI * 2;
/** Opacity window: fade in over fi after a, fade out over fo before b. */
export const env = (t, a, b, fi = 0.3, fo = 0.3) => Math.min(fi > 0 ? seg(t, a, a + fi) : (t >= a ? 1 : 0), fo > 0 ? 1 - seg(t, b - fo, b) : (t < b ? 1 : 0));

// ───────────────────────── seeded hash, rng, noise ─────────────────────────
const _f64 = new Float64Array(1), _u32 = new Uint32Array(_f64.buffer);
function mix32(h, k) { k = Math.imul(k, 0xcc9e2d51); k = (k << 15) | (k >>> 17); k = Math.imul(k, 0x1b873593); h ^= k; h = (h << 13) | (h >>> 19); return (Math.imul(h, 5) + 0xe6546b64) | 0; }
function fmix32(h) { h ^= h >>> 16; h = Math.imul(h, 0x85ebca6b); h ^= h >>> 13; h = Math.imul(h, 0xc2b2ae35); h ^= h >>> 16; return h >>> 0; }
/** 32-bit hash of any numbers (bit-exact on every machine: uses the IEEE-754 bits, not Math.sin). */
export function hash32(...xs) {
  let h = 0x9e3779b9 ^ xs.length;
  for (let x of xs) { _f64[0] = x + 0; h = mix32(h, _u32[0]); h = mix32(h, _u32[1]); }
  return fmix32(h);
}
/** hash(...) → [0, 1). Use hash(seed, i, frame(t)) for per-element, per-frame randomness. */
export const hash = (...xs) => hash32(...xs) / 4294967296;
/** Signed variant → [-1, 1). */
export const hashS = (...xs) => hash(...xs) * 2 - 1;
/** mulberry32 stream. Only for setup-time generation or inside one call; never keep one alive across frames. */
export function rng(seed = 1) {
  let a = hash32(seed) | 0;
  return () => { a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
const fade5 = (u) => u * u * u * (u * (u * 6 - 15) + 10);
/** 1D gradient noise in [-1, 1]. */
export function noise1(x, seed = 0) {
  const i = Math.floor(x), f = x - i;
  const g0 = hashS(seed, i), g1 = hashS(seed, i + 1);
  return 2 * lerp(g0 * f, g1 * (f - 1), fade5(f));
}
/** 2D gradient (Perlin-style) noise in about [-1, 1]. */
export function noise2(x, y, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const g = (ix, iy, dx, dy) => { const a = hash(seed, ix, iy) * TAU; return Math.cos(a) * dx + Math.sin(a) * dy; };
  const u = fade5(xf), v = fade5(yf);
  const n0 = lerp(g(xi, yi, xf, yf), g(xi + 1, yi, xf - 1, yf), u);
  const n1 = lerp(g(xi, yi + 1, xf, yf - 1), g(xi + 1, yi + 1, xf - 1, yf - 1), u);
  return lerp(n0, n1, v) * 1.414;
}
/** Fractal sum of noise2. */
export function fbm2(x, y, { octaves = 4, lacunarity = 2, gain = 0.5, seed = 0 } = {}) {
  let s = 0, a = 1, f = 1, n = 0;
  for (let o = 0; o < octaves; o++) { s += a * noise2(x * f, y * f, seed + o * 101); n += a; a *= gain; f *= lacunarity; }
  return s / n;
}

// ───────────────────────── easing ─────────────────────────
/** cubic-bezier(x1, y1, x2, y2) → u ↦ eased u, same curve as CSS / After Effects. */
export function bezier(x1, y1, x2, y2) {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const sx = (s) => ((ax * s + bx) * s + cx) * s, sy = (s) => ((ay * s + by) * s + cy) * s, dx = (s) => (3 * ax * s + 2 * bx) * s + cx;
  return (u) => {
    if (u <= 0) return 0; if (u >= 1) return 1;
    let s = u;
    for (let i = 0; i < 8; i++) { const e = sx(s) - u; if (Math.abs(e) < 1e-7) return sy(s); const d = dx(s); if (Math.abs(d) < 1e-6) break; s -= e / d; }
    let lo = 0, hi = 1; s = u;
    for (let i = 0; i < 40; i++) { const x = sx(s); if (Math.abs(x - u) < 1e-7) break; if (x < u) lo = s; else hi = s; s = (lo + hi) / 2; }
    return sy(s);
  };
}
/** Named curves (playbook/03-motion-design.md §1). Enter with out*, exit with in*, move between points with inOut*. */
export const ease = {
  linear: (u) => clamp(u),
  outExpo: bezier(0.16, 1, 0.3, 1), outQuint: bezier(0.22, 1, 0.36, 1), outCubic: bezier(0.33, 1, 0.68, 1),
  inCubic: bezier(0.32, 0, 0.67, 0), inExpo: bezier(0.7, 0, 0.84, 0),
  inOutCubic: bezier(0.65, 0, 0.35, 1), inOutQuart: bezier(0.76, 0, 0.24, 1), inOutSine: bezier(0.37, 0, 0.63, 1),
  outBack: bezier(0.34, 1.56, 0.64, 1),
  /** steps(n): hard frames for typing, counters, stop-motion. */
  steps: (n) => (u) => Math.min(1, Math.floor(clamp(u) * n) / n),
};
const CSS_EASE = { ease: [0.25, 0.1, 0.25, 1], "ease-in": [0.42, 0, 1, 1], "ease-out": [0, 0, 0.58, 1], "ease-in-out": [0.42, 0, 0.58, 1] };
const _easeCache = new Map();
/**
 * Any easing spec → function: a lib.ease name ("outExpo"), a [x1,y1,x2,y2] array, a CSS string
 * ("cubic-bezier(0.76,0,0.24,1)", "ease-out", "linear", "steps(4)"), or a function. Unknown → fallback.
 */
export function easeOf(e, fallback = ease.outExpo) {
  if (typeof e === "function") return e;
  if (Array.isArray(e) && e.length === 4) return bezier(...e.map(Number));
  if (typeof e !== "string") return fallback;
  if (ease[e] && e !== "steps") return ease[e];
  if (_easeCache.has(e)) return _easeCache.get(e);
  const s = e.trim().toLowerCase(); let f = null, m;
  if (s === "linear") f = ease.linear;
  else if (CSS_EASE[s]) f = bezier(...CSS_EASE[s]);
  else if ((m = s.match(/^cubic-bezier\(([^)]*)\)$/))) { const v = m[1].split(",").map(Number); if (v.length === 4 && v.every(Number.isFinite)) f = bezier(...v); }
  else if ((m = s.match(/^steps\((\d+)/))) f = ease.steps(+m[1]);
  _easeCache.set(e, f || fallback);
  return f || fallback;
}
/** Eased progress across [a, b]. */
export const tween = (t, a, b, e = ease.outExpo) => easeOf(e)(seg(t, a, b));

/**
 * Closed-form spring step response: 0 for tau ≤ 0, settles at 1. Pure function of tau — no integration, no state.
 * Give either { w, zeta } (natural frequency rad/s, damping ratio) or { stiffness, damping, mass } (Remotion-style),
 * plus optional v0 (initial velocity toward the target, units/s). zeta = 1: no overshoot; 0.8–0.85: ~1–1.5 %.
 */
export function spring(tau, { w = 12, zeta = 1, stiffness, damping, mass = 1, v0 = 0 } = {}) {
  if (tau <= 0) return 0;
  if (stiffness != null) { w = Math.sqrt(stiffness / mass); zeta = (damping ?? 10) / (2 * Math.sqrt(stiffness * mass)); }
  const x0 = -1;
  if (Math.abs(zeta - 1) < 1e-6) return 1 + Math.exp(-w * tau) * (x0 + (v0 + w * x0) * tau);
  if (zeta < 1) {
    const wd = w * Math.sqrt(1 - zeta * zeta);
    return 1 + Math.exp(-zeta * w * tau) * (x0 * Math.cos(wd * tau) + ((v0 + zeta * w * x0) / wd) * Math.sin(wd * tau));
  }
  const s = w * Math.sqrt(zeta * zeta - 1), r1 = -zeta * w + s, r2 = -zeta * w - s;
  const c2 = (v0 - r1 * x0) / (r2 - r1), c1 = x0 - c2;
  return 1 + c1 * Math.exp(r1 * tau) + c2 * Math.exp(r2 * tau);
}
/** Retargeting without state: v(t) = v0 + Σ Δv_i · spring(t − t_i). keys = [{t, v}, …]. */
export function springTrack(t, keys, opts) {
  let v = keys[0].v;
  for (let i = 1; i < keys.length; i++) v += (keys[i].v - keys[i - 1].v) * spring(t - keys[i].t, opts);
  return v;
}

// ───────────────────────── colour & tokens ─────────────────────────
/** Deep get with fallback: tok(tokens, "palette.accent", "#f00"). */
export function tok(tokens, path, fallback) {
  let o = tokens;
  for (const k of path.split(".")) { if (o == null || typeof o !== "object") return fallback; o = o[k]; }
  return o ?? fallback;
}
/**
 * Palette colour from tokens.palette (or tokens.colors): color(tokens, "fg"), color(tokens, "extra.2").
 * Values may be "#hex" or { hex: "#…" }. Missing → fallback (magenta by default, so a typo is visible).
 */
export function color(tokens, name, fallback = "#ff00ff") {
  const p = (tokens && (tokens.palette || tokens.colors)) || {};
  const v = String(name).includes(".") ? tok(p, String(name), undefined) : p[name];
  if (typeof v === "string") return v;
  if (v && typeof v === "object") return v.hex || v.value || fallback;
  return fallback;
}
/** Every colour in the palette, flattened in order (bg, fg, accent, …extra). */
export function palette(tokens) {
  const p = (tokens && (tokens.palette || tokens.colors)) || {}, out = [];
  const add = (v) => { if (typeof v === "string") out.push(v); else if (Array.isArray(v)) v.forEach(add); else if (v && typeof v === "object") add(v.hex || v.value); };
  Object.values(p).forEach(add);
  return out;
}
export function rgb(hex) {
  let h = String(hex).replace("#", "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  const n = parseInt(h.slice(0, 6), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
export const rgba = (hex, a = 1) => { const [r, g, b] = rgb(hex); return `rgba(${r},${g},${b},${a})`; };
export function mixColor(a, b, u) {
  const A = rgb(a), B = rgb(b), c = A.map((x, i) => Math.round(lerp(x, B[i], clamp(u))));
  return "#" + c.map((x) => x.toString(16).padStart(2, "0")).join("");
}
/** Relative luminance 0..1 (for picking ink on a background). */
export function luminance(hex) {
  const l = rgb(hex).map((c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); });
  return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2];
}

// ───────────────────────── fonts & text ─────────────────────────
const GENERIC = new Set(["serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui"]);
const ROLE_FALLBACK = {
  display: ["Helvetica Neue", "PingFang SC", "sans-serif"], body: ["Helvetica Neue", "PingFang SC", "sans-serif"],
  zh: ["PingFang SC", "Hiragino Sans GB", "sans-serif"], mono: ["Menlo", "PingFang SC", "monospace"],
  serif: ["Songti SC", "Times New Roman", "serif"],
};
/** Families always preloaded by the runtime (the fallbacks above). */
export const FALLBACK_FAMILIES = ["Helvetica Neue", "PingFang SC", "Hiragino Sans GB", "Menlo", "Songti SC"];
function roleSpec(tokens, role) {
  const f = tokens && (tokens.fonts || tokens.type || tokens.typography);
  const v = f ? f[role] : undefined;
  if (Array.isArray(v) || typeof v === "string") return { family: v };
  return v && typeof v === "object" ? v : {};
}
function familyList(v) {
  const arr = Array.isArray(v) ? v : typeof v === "string" ? v.split(",") : [];
  return arr.map((s) => String(s).trim().replace(/^["']|["']$/g, "")).filter(Boolean);
}
/** CSS family list for a role from tokens.fonts[role] (array, "A, B" string, or {family|stack: …}) + safe fallbacks. */
export function fontStack(tokens, role = "display") {
  const spec = roleSpec(tokens, role);
  const fams = familyList(spec.family ?? spec.stack ?? spec.families);
  for (const x of ROLE_FALLBACK[role] || ROLE_FALLBACK.body) if (!fams.includes(x)) fams.push(x);
  return fams.map((q) => (GENERIC.has(q) ? q : `"${q}"`)).join(", ");
}
/**
 * CSS font shorthand for canvas: font(tokens, "display", 120) → '700 120px "Helvetica Neue", …'.
 * Role defaults (tokens.fonts[role].weight / .style / .stretch) apply unless opts override them.
 */
export function font(tokens, role, size, opts = {}) {
  const spec = roleSpec(tokens, role);
  const weight = opts.weight ?? spec.weight ?? 400, style = opts.style ?? spec.style ?? "normal";
  return `${style === "italic" ? "italic " : ""}${weight} ${size}px ${fontStack(tokens, role)}`;
}
/** Tracking (letter-spacing) for a role in px: tokens.fonts[role].tracking is in em (e.g. -0.02). */
export const tracking = (tokens, role, size, override) => (override ?? roleSpec(tokens, role).tracking ?? 0) * size;
/** Set ctx.font (+ stretch) for a role. Returns the size for chaining. */
export function setFont(ctx, tokens, role, size, opts = {}) {
  ctx.font = font(tokens, role, size, opts);
  const st = opts.stretch ?? roleSpec(tokens, role).stretch;
  ctx.fontStretch = st || "normal";
  ctx.letterSpacing = "0px";
  return size;
}
/** True if a family renders with its own glyphs (not a fallback). Compares widths against two generic fallbacks. */
export function fontAvailable(family, sample = "mmmmmmmmmmlli WWW 0123 永每帧") {
  const c = layer("__font_probe", 8, 8);
  const w = (f) => { c.font = `400 64px ${f}`; return c.measureText(sample).width; };
  const q = `"${String(family).replace(/"/g, "")}"`;
  return w(`${q}, monospace`) !== w("monospace") || w(`${q}, serif`) !== w("serif");
}
/** Every family named in tokens.fonts (all roles), de-duplicated. */
export function tokenFamilies(tokens) {
  const f = (tokens && (tokens.fonts || tokens.type || tokens.typography)) || {};
  const out = [];
  for (const role of Object.keys(f)) { const sp = roleSpec(tokens, role); for (const x of familyList(sp.family ?? sp.stack ?? sp.families)) if (!GENERIC.has(x) && !out.includes(x)) out.push(x); }
  return out;
}
let _seg;
/** Split into user-perceived characters (emoji, combining marks and CJK safe). */
export function graphemes(str) {
  _seg = _seg || new Intl.Segmenter(undefined, { granularity: "grapheme" });
  return Array.from(_seg.segment(String(str)), (s) => s.segment);
}
export const isCJK = (ch) => /[⺀-鿿豈-﫿＀-￯　-〿]/.test(ch);
const NO_LINE_START = "，。、；：？！）」』》〉”’,.;:?!)%";

const _layoutCache = new Map();
/**
 * Measured single-line layout with per-glyph boxes. Uses ctx.font as currently set.
 * opts: { x, y (baseline), align: "left"|"center"|"right", tracking (px) }.
 * Returns { glyphs: [{ ch, i, x, y, w, cx }], width, ascent, descent, x0, x1 }. Kerning is kept (positions come from
 * measured prefixes), so drawing glyph by glyph matches fillText of the whole string.
 */
export function layoutText(ctx, str, { x = 0, y = 0, align = "left", tracking: tr = 0 } = {}) {
  const key = `${ctx.font}|${ctx.fontStretch}|${tr}|${str}`;
  let base = _layoutCache.get(key);
  if (!base) {
    const ls = ctx.letterSpacing; ctx.letterSpacing = "0px";
    const gs = graphemes(str); let acc = "";
    const glyphs = gs.map((ch, i) => { const gx = ctx.measureText(acc).width + i * tr; acc += ch; return { ch, i, x: gx, w: ctx.measureText(ch).width }; });
    const m = ctx.measureText(str);
    base = { glyphs, width: m.width + Math.max(0, gs.length - 1) * tr, ascent: m.actualBoundingBoxAscent, descent: m.actualBoundingBoxDescent,
      fontAscent: m.fontBoundingBoxAscent, fontDescent: m.fontBoundingBoxDescent };
    ctx.letterSpacing = ls;
    _layoutCache.set(key, base);
  }
  const ox = x - (align === "center" ? base.width / 2 : align === "right" ? base.width : 0);
  return { ...base, x0: ox, x1: ox + base.width, y,
    glyphs: base.glyphs.map((g) => ({ ...g, x: ox + g.x, y, cx: ox + g.x + g.w / 2 })) };
}
/**
 * Draw a layout glyph by glyph. fn(glyph, index) may return { alpha, dx, dy, scale, sx, sy, rot, fill, stroke, lineWidth, ch }
 * or null to skip the glyph. A replacement `ch` (scramble) is centred in the original glyph's slot, so width never jumps.
 */
export function drawGlyphs(ctx, lay, fn = () => ({})) {
  ctx.save();
  ctx.textAlign = "center"; ctx.textBaseline = "alphabetic"; ctx.letterSpacing = "0px";
  const baseFill = ctx.fillStyle, baseAlpha = ctx.globalAlpha;
  for (const g of lay.glyphs) {
    const s = fn(g, g.i);
    if (s === null || s === false) continue;
    const o = s || {}; const a = o.alpha ?? 1;
    if (a <= 0) continue;
    const ch = o.ch ?? g.ch;
    if (!ch || ch === " ") continue;
    ctx.save();
    ctx.globalAlpha = baseAlpha * a;
    ctx.translate(g.cx + (o.dx || 0), g.y + (o.dy || 0));
    if (o.rot) ctx.rotate(o.rot);
    const sc = o.scale ?? 1; if (sc !== 1 || o.sx || o.sy) ctx.scale(o.sx ?? sc, o.sy ?? sc);
    ctx.fillStyle = o.fill ?? baseFill;
    if (o.fill !== "none") ctx.fillText(ch, 0, 0);
    if (o.stroke) { ctx.strokeStyle = o.stroke; ctx.lineWidth = o.lineWidth || 2; ctx.strokeText(ch, 0, 0); }
    ctx.restore();
  }
  ctx.restore();
}
/** Draw a whole string with tracking (simple case). */
export function drawText(ctx, str, x, y, { align = "left", tracking: tr = 0 } = {}) {
  drawGlyphs(ctx, layoutText(ctx, str, { x, y, align, tracking: tr }));
}
/** Largest font size in [min, max] at which str fits maxWidth. setSize(size) must set ctx.font. */
export function fitText(ctx, str, maxWidth, setSize, { min = 12, max = 400, tracking: trEm = 0 } = {}) {
  let lo = min, hi = max;
  for (let i = 0; i < 18; i++) { const mid = (lo + hi) / 2; setSize(mid); const w = ctx.measureText(str).width + trEm * mid * (graphemes(str).length - 1); if (w > maxWidth) hi = mid; else lo = mid; }
  setSize(lo); return lo;
}
/** Word wrap for Latin, per-character wrap for CJK (no line may start with ，。、 etc.). Uses ctx.font. */
export function wrapText(ctx, str, maxWidth) {
  const tokens = []; let buf = "";
  for (const ch of graphemes(str)) {
    if (isCJK(ch)) { if (buf) tokens.push(buf); buf = ""; tokens.push(ch); }
    else if (ch === " ") { tokens.push(buf + " "); buf = ""; }
    else buf += ch;
  }
  if (buf) tokens.push(buf);
  const lines = []; let line = "";
  for (const tk of tokens) {
    const test = line + tk;
    if (line && ctx.measureText(test.trimEnd()).width > maxWidth && !NO_LINE_START.includes(tk[0])) { lines.push(line.trimEnd()); line = tk.trimStart(); }
    else line = test;
  }
  if (line) lines.push(line.trimEnd());
  return lines;
}

export const GLYPHS_LATIN = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789#$%&*+=<>/\\|";
export const GLYPHS_CJK = "田由甲申电里男町画界留略番疆口回目日曰旦旧白百自首囗囚国图团围圆";
/**
 * Decode / scramble, seeded and frame-quantized. Glyph i starts scrambling at start + i·stagger and locks to its
 * real character settle seconds later. The random glyph changes `rate` times per second (rate should divide 30:
 * 30, 15, 10, 6, 5). Returns [{ ch, final, state: "hidden"|"scramble"|"done", u }] aligned with graphemes(str).
 */
export function scrambleGlyphs(str, t, { start = 0, stagger = 0.03, settle = 0.35, rate = 15, seed = 1,
  charset = GLYPHS_LATIN, charsetCJK = GLYPHS_CJK, before = "hidden" } = {}) {
  const k = Math.floor(frame(t) * rate / FPS + 1e-9);
  return graphemes(str).map((ch, i) => {
    if (/\s/.test(ch)) return { ch, final: ch, state: "done", u: 1 };
    const t0 = start + i * stagger;
    if (t < t0) return before === "hidden" ? { ch: "", final: ch, state: "hidden", u: 0 } : { ch: pick(ch, i, k), final: ch, state: "scramble", u: 0 };
    if (t >= t0 + settle) return { ch, final: ch, state: "done", u: 1 };
    return { ch: pick(ch, i, k), final: ch, state: "scramble", u: (t - t0) / settle };
  });
  function pick(ch, i, k) { const cs = isCJK(ch) ? charsetCJK : charset; return cs[Math.floor(hash(seed, i, k) * cs.length)]; }
}
/** String form of scrambleGlyphs (hidden glyphs become spaces). */
export const scramble = (str, t, opts) => scrambleGlyphs(str, t, opts).map((g) => g.ch || " ").join("");
/** Typewriter: visible prefix at t, cps characters per second, frame-quantized. */
export function typewriter(str, t, { start = 0, cps = 20 } = {}) {
  const gs = graphemes(str); const n = Math.floor(Math.max(0, frame(t) - frame(start)) * cps / FPS + 1e-9);
  return gs.slice(0, Math.min(gs.length, n)).join("");
}

// ───────────────────────── layers (offscreen canvases) ─────────────────────────
const _layers = new Map();
/** A named full-size offscreen canvas, cleared and state-reset on every call. Names are global: prefix yours. */
export function layer(name, w = W, h = H) {
  let c = _layers.get(name);
  if (!c || c.width !== w || c.height !== h) { c = document.createElement("canvas"); c.width = w; c.height = h; _layers.set(name, c); }
  const x = c.getContext("2d"); x.reset(); return x;
}
/** Run draw(ctx) into a fresh layer and return its canvas (to composite, mask, filter or feed a shader). */
export function offscreen(name, draw, w = W, h = H) { const x = layer(name, w, h); draw(x); return x.canvas; }

// ───────────────────────── textures ─────────────────────────
const _tex = new Map();
function cached(key, make) { let v = _tex.get(key); if (!v) { v = make(); _tex.set(key, v); } return v; }

/**
 * Film grain over the whole frame. Mid-grey noise tiles blended with `mode` (overlay by default), tile choice and
 * offset seeded by the frame step, refreshed `fps` times per second (24 = film cadence on a 30 fps timeline).
 */
export function grain(ctx, t, { amount = 0.08, size = 1, fps = 24, seed = 7, mode = "overlay", tiles = 6 } = {}) {
  if (amount <= 0) return;
  const T = 256;
  const set = cached(`grain:${seed}:${tiles}`, () => Array.from({ length: tiles }, (_, k) => {
    const c = document.createElement("canvas"); c.width = c.height = T;
    const x = c.getContext("2d"), img = x.createImageData(T, T), r = rng(hash32(seed, k));
    for (let i = 0; i < T * T; i++) { const v = 128 + ((r() + r() + r()) / 3 - 0.5) * 2 * 150; img.data[i * 4] = img.data[i * 4 + 1] = img.data[i * 4 + 2] = clamp(v, 0, 255); img.data[i * 4 + 3] = 255; }
    x.putImageData(img, 0, 0); return c;
  }));
  const s = Math.floor(frame(t) * fps / FPS + 1e-9);
  const tile = set[hash32(seed, s, 1) % tiles];
  ctx.save();
  const pat = ctx.createPattern(tile, "repeat");
  pat.setTransform(new DOMMatrix().translate(Math.floor(hash(seed, s, 2) * T), Math.floor(hash(seed, s, 3) * T)).scale(size));
  ctx.globalCompositeOperation = mode; ctx.globalAlpha = clamp(amount);
  ctx.fillStyle = pat; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

/** Static paper: base tone + low-frequency blotches + tooth + fibres. Generated once per option set, then cached. */
export function paper(ctx, { tone = "#f1ece1", amount = 1, blotch = 0.06, tooth = 0.025, fiber = 0.5, seed = 3 } = {}) {
  const key = `paper:${tone}:${blotch}:${tooth}:${fiber}:${seed}`;
  const c = cached(key, () => {
    const w = 960, h = 540, cv = document.createElement("canvas"); cv.width = w; cv.height = h;
    const x = cv.getContext("2d"), [R, G, B] = rgb(tone);
    // 1) blotches: fbm on a coarse grid, upscaled smoothly (cheap, and they are low-frequency anyway)
    const bw = 240, bh = 135, bc = document.createElement("canvas"); bc.width = bw; bc.height = bh;
    const bx = bc.getContext("2d"), bi = bx.createImageData(bw, bh);
    for (let j = 0; j < bh; j++) for (let i = 0; i < bw; i++) {
      const m = 1 + fbm2(i / 40, j / 40, { octaves: 4, seed }) * blotch, k = (j * bw + i) * 4;
      bi.data[k] = clamp(R * m, 0, 255); bi.data[k + 1] = clamp(G * m, 0, 255); bi.data[k + 2] = clamp(B * m, 0, 255); bi.data[k + 3] = 255;
    }
    bx.putImageData(bi, 0, 0); x.imageSmoothingQuality = "high"; x.drawImage(bc, 0, 0, w, h);
    // 2) tooth: per-pixel seeded noise
    const img = x.getImageData(0, 0, w, h), r = rng(seed + 5);
    for (let k = 0; k < img.data.length; k += 4) { const m = 1 + (r() - 0.5) * 2 * tooth; img.data[k] *= m; img.data[k + 1] *= m; img.data[k + 2] *= m; }
    x.putImageData(img, 0, 0);
    // 3) fibres
    const rf = rng(seed + 17), dark = rgba(mixColor(tone, "#000000", 0.35), 0.10 * fiber), light = rgba(mixColor(tone, "#ffffff", 0.6), 0.18 * fiber);
    x.lineCap = "round";
    for (let f = 0; f < 900 * fiber; f++) {
      const px = rf() * w, py = rf() * h, a = rf() * TAU, len = 3 + rf() * 14;
      x.strokeStyle = rf() < 0.5 ? dark : light; x.lineWidth = 0.35 + rf() * 0.5;
      x.beginPath(); x.moveTo(px, py); x.quadraticCurveTo(px + Math.cos(a) * len * 0.5 + (rf() - 0.5) * 4, py + Math.sin(a) * len * 0.5 + (rf() - 0.5) * 4, px + Math.cos(a) * len, py + Math.sin(a) * len); x.stroke();
    }
    return cv;
  });
  ctx.save(); ctx.globalAlpha = clamp(amount); ctx.imageSmoothingQuality = "high"; ctx.drawImage(c, 0, 0, W, H); ctx.restore();
}

/**
 * Halftone: dots whose area follows darkness. src is a canvas (luminance is sampled; dark = big dot) or a function
 * (x, y) → darkness 0..1. opts: { cell, angle (deg), color, shape: "dot"|"square"|"line", scale, invert, rect: {x,y,w,h} }.
 */
export function halftone(ctx, src, { cell = 12, angle = 45, color: col = "#111", shape = "dot", scale = 1, invert = false, rect = { x: 0, y: 0, w: W, h: H } } = {}) {
  let sample = src;
  if (typeof src !== "function") {
    const sw = Math.max(1, Math.ceil(rect.w / (cell / 2))), sh = Math.max(1, Math.ceil(rect.h / (cell / 2)));
    const sx = layer("__halftone_sample", sw, sh); sx.imageSmoothingQuality = "high";
    sx.drawImage(src, rect.x, rect.y, rect.w, rect.h, 0, 0, sw, sh);
    const d = sx.getImageData(0, 0, sw, sh).data;
    sample = (x, y) => {
      const i = clamp(Math.floor((x - rect.x) / rect.w * sw), 0, sw - 1), j = clamp(Math.floor((y - rect.y) / rect.h * sh), 0, sh - 1), k = (j * sw + i) * 4;
      const a = d[k + 3] / 255, l = (0.2126 * d[k] + 0.7152 * d[k + 1] + 0.0722 * d[k + 2]) / 255;
      return a * (1 - l);
    };
  }
  const a = angle * Math.PI / 180, ux = Math.cos(a) * cell, uy = Math.sin(a) * cell, vx = -uy, vy = ux;
  const cx = rect.x + rect.w / 2, cy = rect.y + rect.h / 2, R = Math.ceil(Math.hypot(rect.w, rect.h) / 2 / cell) + 1;
  ctx.save(); ctx.fillStyle = col; ctx.strokeStyle = col; ctx.beginPath();
  for (let j = -R; j <= R; j++) for (let i = -R; i <= R; i++) {
    const x = cx + i * ux + j * vx, y = cy + i * uy + j * vy;
    if (x < rect.x - cell || y < rect.y - cell || x > rect.x + rect.w + cell || y > rect.y + rect.h + cell) continue;
    let d = clamp(sample(x, y)); if (invert) d = 1 - d; d *= scale;
    if (d <= 0.01) continue;
    if (shape === "square") { const s = cell * Math.sqrt(d); ctx.rect(x - s / 2, y - s / 2, s, s); }
    else if (shape === "line") { const hw = cell * d * 0.5; ctx.moveTo(x - vx / 2 - ux * hw / cell, y - vy / 2 - uy * hw / cell); ctx.lineTo(x + vx / 2 - ux * hw / cell, y + vy / 2 - uy * hw / cell); ctx.lineTo(x + vx / 2 + ux * hw / cell, y + vy / 2 + uy * hw / cell); ctx.lineTo(x - vx / 2 + ux * hw / cell, y - vy / 2 + uy * hw / cell); ctx.closePath(); }
    else { const r = cell * 0.7071 * Math.sqrt(d); ctx.moveTo(x + r, y); ctx.arc(x, y, r, 0, TAU); }
  }
  ctx.fill(); ctx.restore();
}

/** CRT / video scanlines. roll = px per second the pattern drifts; flicker = per-frame alpha jitter (seeded). */
export function scanlines(ctx, t, { spacing = 4, thickness = 1.5, alpha = 0.25, color: col = "#000", roll = 0, flicker = 0, seed = 5 } = {}) {
  const tile = cached(`scan:${spacing}:${thickness}:${col}`, () => {
    const c = document.createElement("canvas"); c.width = 4; c.height = spacing;
    const x = c.getContext("2d"); x.fillStyle = col; x.fillRect(0, 0, 4, thickness); return c;
  });
  ctx.save();
  const pat = ctx.createPattern(tile, "repeat");
  pat.setTransform(new DOMMatrix().translate(0, ((t * roll) % spacing + spacing) % spacing));
  ctx.globalAlpha = clamp(alpha * (1 + flicker * hashS(seed, frame(t))));
  ctx.fillStyle = pat; ctx.fillRect(0, 0, W, H);
  ctx.restore();
}

/** Radial vignette: transparent inside `inner` (fraction of the half-diagonal), `strength` alpha at the corners. */
export function vignette(ctx, { strength = 0.5, inner = 0.55, color: col = "#000", cx = W / 2, cy = H / 2 } = {}) {
  const r = Math.hypot(W, H) / 2, g = ctx.createRadialGradient(cx, cy, r * inner, cx, cy, r);
  g.addColorStop(0, rgba(col, 0)); g.addColorStop(1, rgba(col, strength));
  ctx.save(); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H); ctx.restore();
}

/**
 * Ink bleed approximation: draw(ctx) into a layer, then blur + turbulence-displace + alpha-threshold it with the SVG
 * filter #ovh-ink. spread = blur px (how far ink creeps; keep it ≤ half the thinnest stroke or thin strokes vanish),
 * rough = edge displacement, sharp = edge hardness, seed = turbulence seed (change it per frame step for "boiling"
 * edges: seed: step(t, 8) * 8 + 1).
 */
export function inkBleed(ctx, draw, { spread = 2.5, rough = 1, freq = 0.04, seed = 1, sharp = 4 } = {}) {
  const src = offscreen("__ink_src", draw);
  const set = (id, attrs) => { const el = document.getElementById(id); if (el) for (const k in attrs) el.setAttribute(k, String(attrs[k])); };
  set("ovh-ink-turb", { baseFrequency: freq, seed: Math.round(seed) });
  set("ovh-ink-blur", { stdDeviation: spread });
  set("ovh-ink-disp", { scale: spread * 1.6 * rough });
  set("ovh-ink-alpha", { slope: sharp, intercept: -(sharp - 1) * 0.3 });   // edge sits near 30 % of the blurred alpha: ink spreads outward
  ctx.save(); ctx.filter = "url(#ovh-ink)"; ctx.drawImage(src, 0, 0); ctx.restore();
}
/** Roughen edges (hand-cut paper, woodcut): displaces whatever draw() paints. */
export function roughen(ctx, draw, { amount = 6, freq = 0.06, seed = 1 } = {}) {
  const src = offscreen("__rough_src", draw);
  const t = document.getElementById("ovh-rough-turb"), d = document.getElementById("ovh-rough-disp");
  if (t) { t.setAttribute("baseFrequency", String(freq)); t.setAttribute("seed", String(Math.round(seed))); }
  if (d) d.setAttribute("scale", String(amount));
  ctx.save(); ctx.filter = "url(#ovh-rough)"; ctx.drawImage(src, 0, 0); ctx.restore();
}
/** RGB split / misregistration: composites the red, green and blue channels of src with offsets. */
export function rgbSplit(ctx, src, { r = [4, 0], g = [0, 0], b = [-4, 0] } = {}) {
  const ch = (name, hex, [dx, dy]) => { const x = layer(name); x.drawImage(src, 0, 0); x.globalCompositeOperation = "multiply"; x.fillStyle = hex; x.fillRect(0, 0, W, H); x.globalCompositeOperation = "destination-in"; x.drawImage(src, 0, 0); return [x.canvas, dx, dy]; };
  const parts = [ch("__rgb_r", "#ff0000", r), ch("__rgb_g", "#00ff00", g), ch("__rgb_b", "#0000ff", b)];
  ctx.save(); ctx.fillStyle = "#000"; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = "lighter";
  for (const [c, dx, dy] of parts) ctx.drawImage(c, dx, dy);
  ctx.restore();
}

// ───────────────────────── shapes ─────────────────────────
/** Hand-drawn polyline: points get seeded wobble; pass seed: step(t, 8) to make it "boil" 8× per second. */
export function wobblePath(ctx, pts, { amp = 2, seg: segLen = 18, seed = 1, close = false } = {}) {
  const P = close ? [...pts, pts[0]] : pts; let k = 0;
  ctx.beginPath();
  for (let i = 0; i < P.length - 1; i++) {
    const [x0, y0] = P[i], [x1, y1] = P[i + 1], n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, y1 - y0) / segLen));
    for (let s = 0; s <= n; s++) {
      if (i > 0 && s === 0) continue;
      const u = s / n, x = lerp(x0, x1, u) + amp * hashS(seed, k, 1), y = lerp(y0, y1, u) + amp * hashS(seed, k, 2); k++;
      if (i === 0 && s === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
  }
  if (close) ctx.closePath();
}
/** Partial stroke of a polyline: draws the first u (0..1) of its length (for "drawing on" lines). */
export function strokePartial(ctx, pts, u) {
  const L = []; let tot = 0;
  for (let i = 1; i < pts.length; i++) { const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); L.push(l); tot += l; }
  let left = clamp(u) * tot; ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length && left > 0; i++) { const f = Math.min(1, left / L[i - 1]); ctx.lineTo(lerp(pts[i - 1][0], pts[i][0], f), lerp(pts[i - 1][1], pts[i][1], f)); left -= L[i - 1]; }
  ctx.stroke();
}

// ───────────────────────── transitions ─────────────────────────
// Each takes progress u (0→1; apply your own easing or pass `ease`) and two painters drawA(ctx) / drawB(ctx) that
// draw a FULL frame into the ctx they are given (a layer, not necessarily the main canvas).

/** Hard cut: A before u reaches 1 (or `at`), B after. */
export function cut(ctx, u, drawA, drawB, { at = 1 } = {}) { (u < at ? drawA : drawB)(ctx); }
/** Straight wipe. angle in degrees (0 = left→right, 90 = top→bottom); soft = edge feather px. */
export function wipe(ctx, u, drawA, drawB, { angle = 0, soft = 0, ease: e = ease.inOutCubic } = {}) {
  const p = easeOf(e)(clamp(u));
  if (p <= 0) return drawA(ctx);
  if (p >= 1) return drawB(ctx);
  drawA(ctx);
  const b = layer("__wipe_b"); drawB(b);
  const a = angle * Math.PI / 180, dx = Math.cos(a), dy = Math.sin(a);
  const half = (Math.abs(dx) * W + Math.abs(dy) * H) / 2 + soft;
  const pos = lerp(-half, half, p), cx = W / 2 + dx * pos, cy = H / 2 + dy * pos, s = Math.max(0.5, soft / 2);
  const g = b.createLinearGradient(cx - dx * s, cy - dy * s, cx + dx * s, cy + dy * s);
  g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0,0)");
  b.globalCompositeOperation = "destination-in"; b.fillStyle = g; b.fillRect(0, 0, W, H);
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over"; ctx.drawImage(b.canvas, 0, 0); ctx.restore();
}
/**
 * Iris. mode "open": B grows inside a circle over A. mode "close": A shrinks into a circle over B (classic iris-out
 * to an end card). shape "circle" | "square"; feather in px.
 */
export function iris(ctx, u, drawA, drawB, { cx = W / 2, cy = H / 2, mode = "close", shape = "circle", feather = 0, ease: e = ease.inOutCubic } = {}) {
  const p = easeOf(e)(clamp(u));
  const R = Math.max(Math.hypot(cx, cy), Math.hypot(W - cx, cy), Math.hypot(cx, H - cy), Math.hypot(W - cx, H - cy)) + feather;
  const [under, over, r] = mode === "open" ? [drawA, drawB, p * R] : [drawB, drawA, (1 - p) * R];
  if (r <= 0.5) return under(ctx);
  if (r >= R) return over(ctx);
  under(ctx);
  const o = layer("__iris_over"); over(o);
  o.globalCompositeOperation = "destination-in";
  if (feather > 0 && shape === "circle") {
    const g = o.createRadialGradient(cx, cy, Math.max(0, r - feather), cx, cy, r);
    g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0,0)"); o.fillStyle = g; o.fillRect(0, 0, W, H);
  } else {
    o.fillStyle = "#000"; o.beginPath();
    if (shape === "square") o.rect(cx - r * 0.7071, cy - r * 0.7071, r * 1.4142, r * 1.4142); else o.arc(cx, cy, r, 0, TAU);
    o.fill();
  }
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over"; ctx.drawImage(o.canvas, 0, 0); ctx.restore();
}
/**
 * Whip pan: A leaves and B arrives along dir with directional motion blur proportional to speed (sub-frame samples).
 * dir [1,0] = content moves right. samples "auto" = one sample per 3 px of smear (max 48); 1 = plain push. Pass duration (s) = the whip's real length so the blur
 * matches a `shutter` fraction of one frame.
 */
export function whip(ctx, u, drawA, drawB, { dir = [-1, 0], samples = "auto", shutter = 0.5, duration = 0.6, ease: e = ease.inOutQuart, dist } = {}) {
  const E = easeOf(e), p = E(clamp(u));
  if (u <= 0) return drawA(ctx);
  if (u >= 1) return drawB(ctx);
  const L = Math.hypot(dir[0], dir[1]) || 1, nx = dir[0] / L, ny = dir[1] / L, D = dist ?? (Math.abs(nx) * W + Math.abs(ny) * H);
  const A = offscreen("__whip_a", drawA), B = offscreen("__whip_b", drawB);
  const du = shutter / FPS / duration;                   // shutter window in u units (duration = whip length in s)
  const acc = layer("__whip_acc"); acc.fillStyle = "#000"; acc.fillRect(0, 0, W, H);
  const smear = Math.abs(E(clamp(u + du / 2)) - E(clamp(u - du / 2))) * D;   // blur length in px this frame
  const n = samples === "auto" ? clamp(Math.ceil(smear / 3), 1, 48) : Math.max(1, samples);
  for (let s = 0; s < n; s++) {
    const q = n === 1 ? p : E(clamp(u + (s / (n - 1) - 0.5) * du)), off = q * D;
    acc.globalAlpha = 1 / (s + 1);                       // running mean → equal weights
    const f = layer("__whip_f"); f.drawImage(A, nx * off, ny * off); f.drawImage(B, nx * (off - D), ny * (off - D));
    acc.drawImage(f.canvas, 0, 0);
  }
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = "source-over"; ctx.drawImage(acc.canvas, 0, 0); ctx.restore();
}
/** Sub-frame motion blur for anything: averages drawAt(t', ctx) over the shutter (fraction of a frame). */
export function motionBlur(ctx, t, drawAt, { samples = 8, shutter = 0.5 } = {}) {
  const acc = layer("__mb_acc");
  for (let s = 0; s < samples; s++) {
    const ts = t + (samples === 1 ? 0 : (s / (samples - 1) - 0.5) * shutter / FPS);
    const f = layer("__mb_f"); drawAt(ts, f);
    acc.globalAlpha = 1 / (s + 1); acc.drawImage(f.canvas, 0, 0);
  }
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.drawImage(acc.canvas, 0, 0); ctx.restore();
}

// ───────────────────────── optional WebGL ─────────────────────────
const FRAG_HEAD = `#version 300 es
precision highp float;
in vec2 v_uv;
out vec4 outColor;
uniform vec2 u_res;
uniform float u_time;
uniform float u_frame;
uniform sampler2D u_tex0;
uniform sampler2D u_tex1;
`;
/**
 * Fullscreen fragment shader on an offscreen WebGL2 canvas. frag is GLSL ES 3.00 BODY (header with v_uv, outColor,
 * u_res, u_time, u_frame, u_tex0, u_tex1 is prepended unless frag starts with #version).
 * const fx = lib.shader(src);  … in renderAt: ctx.drawImage(fx.render(t, { u_amount: 0.4 }, { u_tex0: someCanvas }), 0, 0);
 * Uniform values: number → float, [a,b] / [a,b,c] / [a,b,c,d] → vecN. Textures are canvases or images (uploaded per call,
 * v_uv (0,0) = bottom-left like GLSL; textures are flipped so they read upright).
 */
export function shader(frag, { width = W, height = H } = {}) {
  const canvas = document.createElement("canvas"); canvas.width = width; canvas.height = height;
  const gl = canvas.getContext("webgl2", { preserveDrawingBuffer: true, premultipliedAlpha: false, antialias: false, alpha: true });
  if (!gl) throw new Error("WebGL2 unavailable in this renderer");
  const compile = (type, src) => { const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error("shader: " + gl.getShaderInfoLog(s)); return s; };
  const prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, `#version 300 es\nin vec2 p; out vec2 v_uv; void main(){ v_uv = p * 0.5 + 0.5; gl_Position = vec4(p, 0.0, 1.0); }`));
  gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, frag.trimStart().startsWith("#version") ? frag : FRAG_HEAD + frag));
  gl.bindAttribLocation(prog, 0, "p"); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error("shader link: " + gl.getProgramInfoLog(prog));
  const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
  const vao = gl.createVertexArray(); gl.bindVertexArray(vao); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
  const texs = {};
  const texFor = (name) => texs[name] || (texs[name] = (() => { const tx = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tx); for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE]]) gl.texParameteri(gl.TEXTURE_2D, k, v); return tx; })());
  return {
    canvas, gl,
    render(t = 0, uniforms = {}, textures = {}) {
      gl.viewport(0, 0, width, height); gl.useProgram(prog); gl.bindVertexArray(vao);
      const U = (n) => gl.getUniformLocation(prog, n);
      gl.uniform2f(U("u_res"), width, height); gl.uniform1f(U("u_time"), t); gl.uniform1f(U("u_frame"), frame(t));
      for (const [n, v] of Object.entries(uniforms)) {
        const loc = U(n); if (!loc) continue;
        if (typeof v === "number") gl.uniform1f(loc, v);
        else if (Array.isArray(v)) gl[`uniform${v.length}fv`](loc, v);
      }
      let unit = 0;
      for (const [n, img] of Object.entries(textures)) {
        gl.activeTexture(gl.TEXTURE0 + unit); gl.bindTexture(gl.TEXTURE_2D, texFor(n));
        gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true); gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        gl.uniform1i(U(n), unit); unit++;
      }
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT); gl.drawArrays(gl.TRIANGLES, 0, 3);
      return canvas;
    },
  };
}
