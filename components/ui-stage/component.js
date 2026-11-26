// ui-stage — the pieces of an operated scene, for a tutorial whose operations are rebuilt in code instead of recorded
// (video-types/12-product-tutorial.md): a window (a terminal, a browser or an app's frame) whose lines are printed,
// pasted or typed by hand (pinyin through an input method's composition and candidate box), a keyboard whose keys go
// down as the lines are typed, a cursor with its presses, a step chip, and a player for real captures of an interface:
// one picture a small step, cross-faded, with a camera in the pictures' own pixels, a spotlight and a ring of light.
// state(params, t) is a function of t and the params only; canvas() draws it into a 2D canvas, build() + dom() move DOM
// elements (the DOM painter can tilt the capture in 3D). Rewritten from the typing, keyboard and interface player of a
// 2026-11 tutorial film made with this repository.
import { clamp, hash, lerp, seg, ease } from "../lib/core.js";
import { cursorPath, presses } from "../lib/motion.js";

export const defaults = {
  window: null,          // { kind: "terminal" | "browser" | "app", x, y, w, h, title, url }: a frame in stage px; null: none
  lines: [],             // the window's lines, top to bottom: { at, text, how, prompt, cps, parts, color, enter } (see slots.json)
  size: 44,              // the lines' text size (px): 44 is the desktop floor for text that is read (playbook/03 §4)
  leading: 1.6,          // line height ÷ size
  pad: 36,               // the window body's margin (px)
  keyboard: null,        // { x, y, w }: a keyboard whose keys go down as the lines are typed; null: none
  cursor: null,          // { keys: [[t, x, y]], clicks: [t], drags: [[t0, t1]], space: "stage" | "capture" | "screen", size }
  steps: [],             // [[t, "1", "复制，粘贴，回车"], …]: the step chip; empty: none
  chip: [96, 886],       // the chip's top-left corner (screen px)
  capture: null,         // { states: [[t, name]], fade, size: [w, h], at: [x, y], camera: [[t, cx, cy, zoom, rx, ry]], src }
  marks: [],             // [{ t0, t1, box: [x, y, w, h], kind: "spot" | "ring", space }]: the rest dimmed, or a ring of light
  camera: [],            // [[t, cx, cy, zoom]]: the stage's camera (the window and keyboard move with it); empty: still
  colors: { window: "#121211", bar: "#1c1c1a", edge: "#34322e", text: "#ebe8e2", dim: "#8e8a82", prompt: "#8fbf95",
    accent: "#ffd93b", paste: "#5ec9dc", error: "#e85a50", light: "#e9e7e2", ink: "#1d1c1a", shade: "4,6,10" },
  font: '"PingFang SC", "Helvetica Neue", sans-serif',
  mono: '"SF Mono", Menlo, "PingFang SC", monospace',
  seed: 1,
};
const opts = (p) => ({ ...defaults, ...p, colors: { ...defaults.colors, ...(p && p.colors) } });
const W0 = 1920, H0 = 1080;
const fail = (msg) => { throw new Error(`ui-stage: ${msg}`); };
const chars = (s) => Array.from(String(s ?? ""));
const io = ease.inOutCubic, out = ease.outExpo;
const KEY_DOWN = 0.05, KEY_UP = 0.32;   // a key goes down 0.05 s before its letter shows and comes back over 0.32 s
const RING = 0.45;                      // a press's ring of light, s
const ENTER_AFTER = 0.25;               // a line typed by hand: the beat before its Enter
const PASTE_HOLD = 0.6, PASTE_FADE = 0.7;
const PUNCT = /[，。：；？！、,.;:?!]/;

// ── timing: when each letter of a line shows ────────────────────────────────────────────────────────────────────────
/**
 * A line's plan: when its prompt and each letter show, when it is done, its Enter, and the keys that went down
 * ([[t, key]]). how: print (cps 60, even), paste (all at once), type (by hand: cps 14, uneven, longer after
 * punctuation), ime (parts [[hanzi, pinyin], …] at cps letters a second: the letters compose under the caret with a
 * candidate box, a space commits them; a part whose two are the same, or one letter long, is typed as it is).
 */
export function planLine(line, i = 0, seed = 1) {
  if (!line || typeof line !== "object" || !Number.isFinite(line.at)) fail(`lines[${i}] needs at (s), not ${JSON.stringify(line)}`.slice(0, 160));
  const how = line.how || (line.parts ? "ime" : "print"), at = line.at, keys = [];
  if (!["print", "paste", "type", "ime"].includes(how)) fail(`lines[${i}].how is print, paste, type or ime, not ${JSON.stringify(how)}`);
  if (how === "ime") {
    if (!Array.isArray(line.parts) || !line.parts.every((p) => Array.isArray(p) && p.length === 2)) fail(`lines[${i}].parts is [[hanzi, pinyin], …]`);
    const lps = line.cps || 16; let t = at;
    const parts = line.parts.map(([hz, py], k) => {
      const L = chars(py), a = [];
      L.forEach((c, j) => { t += (1 / lps) * (0.6 + 0.8 * hash(seed, i, k, j)); a.push(t); keys.push([t, c]); });
      const own = hz === py || L.length === 1;
      if (!own) { t += 0.09; keys.push([t, " "]); }
      const e = t; t += 0.05 + 0.05 * hash(seed, i, k, 99);
      return { hz: chars(hz), py: L, a, e, own };
    });
    const end = parts.length ? parts[parts.length - 1].e : at;
    const enter = line.enter ? end + ENTER_AFTER : null;
    if (enter != null) keys.push([enter, "⏎"]);
    return { how, at, parts, end, enter, keys, text: line.parts.map((p) => p[0]).join("") };
  }
  const cs = chars(line.text), times = [];
  if (how === "paste") cs.forEach(() => times.push(at));
  else if (how === "type") {
    const cps = line.cps || 14; let t = at;
    cs.forEach((c, j) => { t += (1 / cps) * (0.55 + 0.9 * hash(seed, i, j)) * (PUNCT.test(c) ? 1.9 : 1); times.push(t); keys.push([t, c]); });
  } else { const cps = line.cps || 60; cs.forEach((c, j) => times.push(at + (j + 1) / cps)); }
  const end = times.length ? times[times.length - 1] : at;
  const enter = line.enter ? end + (how === "type" ? ENTER_AFTER : 0.1) : null;
  if (enter != null) keys.push([enter, "⏎"]);
  if (how === "paste") keys.push([at - 0.02, "⌘"], [at, "v"]);
  return { how, at, times, end, enter, keys, text: cs.join("") };
}
const plans = (p) => {   // lines in the order they begin: the caret and the scroll follow the last one that has begun
  p.lines.forEach((l, i) => { if (i && l && p.lines[i - 1] && Number.isFinite(l.at) && l.at < p.lines[i - 1].at) fail(`lines[${i}] begins at ${l.at} s, before lines[${i - 1}] (${p.lines[i - 1].at} s): give them in the order they begin`); });
  if (p.capture && !(Array.isArray(p.capture.states) && p.capture.states.length)) fail("capture needs states: [[t, name], …]");
  return p.lines.map((l, i) => planLine(l, i, p.seed));
};

/** What the scene sounds like, from the params alone: [{ t, kind }] (key, space, enter, paste, line, click, drag, step),
 *  in time order, for the sound pass (audio/events.json). */
export function events(params) {
  const p = opts(params), ev = [];
  plans(p).forEach((pl) => {
    if (pl.how === "print") ev.push({ t: pl.at, kind: "line" });
    for (const [t, k] of pl.keys) if (k !== "⌘") ev.push({ t, kind: k === " " ? "space" : k === "⏎" ? "enter" : pl.how === "paste" ? "paste" : "key" });
  });
  const c = p.cursor; if (c) { (c.clicks || []).forEach((t) => ev.push({ t, kind: "click" })); (c.drags || []).forEach(([a]) => ev.push({ t: a, kind: "drag" })); }
  p.steps.forEach(([t]) => ev.push({ t, kind: "step" }));
  return ev.sort((a, b) => a.t - b.t);
}

// ── cameras ─────────────────────────────────────────────────────────────────────────────────────────────────────────
/** A camera's keys [[t, cx, cy, zoom, rx, ry]] at t: eased between keys (inOutCubic), held after the last. */
export function cameraAt(keys, t, fit) {
  if (!keys || !keys.length) return { ...fit };
  let i = 0; while (i + 1 < keys.length && t >= keys[i + 1][0]) i++;
  const a = keys[i], b = keys[Math.min(i + 1, keys.length - 1)], u = a === b || t <= a[0] ? 0 : io(seg(t, a[0], b[0]));
  const v = (j, d) => lerp(a[j] ?? d, b[j] ?? d, u);
  return { cx: v(1, fit.cx), cy: v(2, fit.cy), z: v(3, fit.z), rx: v(4, 0), ry: v(5, 0) };
}
const stageFit = { cx: W0 / 2, cy: H0 / 2, z: 1 };
const captureFit = (c) => { const [w, h] = c.size || [1440, 900]; return { cx: w / 2, cy: h / 2, z: Math.min(1800 / w, 960 / h) }; };
/** Where a point lands on the screen: through the stage's camera ("stage"), the capture's ("capture"), or as it is. */
export function project(st, x, y, space = "stage") {
  const c = space === "capture" ? st.capture && st.capture.cam : space === "stage" ? st.cam : null;
  if (!c) return [x, y];
  const o = space === "capture" ? st.capture.at : [W0 / 2, H0 / 2];
  return [o[0] + (x - c.cx) * c.z, o[1] + (y - c.cy) * c.z];
}

// ── the keyboard's keys (param-derived: the same w gives the same rectangles) ──────────────────────────────────────
const ROWS = ["`1234567890-=⌫", "⇥qwertyuiop[]\\", "⇪asdfghjkl;'⏎", "⇧zxcvbnm,./⇧"];
const WIDE = { "⌫": 1.5, "⇥": 1.5, "⇪": 1.8, "⏎": 2.2, "⇧": 2.4 };
const BOTTOM = [["⌃", 1], ["⌥", 1.2], ["⌘", 1.5], [" ", 7], ["⌘", 1.5], ["⌥", 1.2], ["←", 1], ["→", 1]];
const ALIAS = { "，": ",", "。": ".", "：": ";", ":": ";", "；": ";", "“": "'", "”": "'", "'": "'", "？": "/", "?": "/", "！": "1", "!": "1" };
/** The keyboard's keys in its own px: [{ key, label, x, y, w, h }] and its size { w, h }; gap and margin scale with w. */
export function keyLayout(w = 1800) {
  const gap = Math.round(w * 0.0072), m = Math.round(w * 0.0144), keys = [];
  const rows = ROWS.map((r) => Array.from(r).map((c) => [c, WIDE[c] || 1])).concat([BOTTOM]);
  const u0 = (w - 2 * m - gap * (rows[0].length - 1)) / rows[0].reduce((s, k) => s + k[1], 0), kh = Math.round(u0 * 0.92);
  rows.forEach((row, r) => {
    const u = (w - 2 * m - gap * (row.length - 1)) / row.reduce((s, k) => s + k[1], 0); let x = m;
    for (const [c, f] of row) {
      const label = c === "⏎" ? "⏎" : c === " " ? "" : /[a-z]/.test(c) ? c.toUpperCase() : c;
      keys.push({ key: c, label, x, y: m + r * (kh + gap), w: u * f, h: kh }); x += u * f + gap;
    }
  });
  return { keys, w, h: 2 * m + rows.length * kh + (rows.length - 1) * gap };
}
const keyOf = (c) => { const k = String(c).toLowerCase(); return ALIAS[k] || k; };

// ── the state at t ──────────────────────────────────────────────────────────────────────────────────────────────────
/**
 * The scene at t: { cam, window, lines: [{ i, y, prompt, text, progress?, comp, cand, hl, color, caret, how }], scroll,
 * keys: { key: 0..1 }, cursor: { x, y, press, rings: [{ r, a }] } | null, step: { n, text, k, slide } | null,
 * capture: { a, b, q, cam, at, size } | null, marks: [{ kind, x, y, w, h, a }] }. Screen px, except the window's
 * lines and the keyboard, which are in stage px and drawn through cam.
 */
export function state(params, t) {
  const p = opts(params), C = p.colors, lh = p.size * p.leading, pl = plans(p);
  const st = { t, cam: cameraAt(p.camera, t, stageFit), window: p.window, lines: [], scroll: 0, keys: {}, cursor: null, step: null, capture: null, marks: [] };
  // the lines: what shows of each, the caret on the last one that has begun
  let act = -1; pl.forEach((q, i) => { if (t >= q.at) act = i; });
  pl.forEach((q, i) => {
    if (t < q.at) return;
    const src = p.lines[i], L = { i, how: q.how, y: i * lh, prompt: src.prompt || "", color: src.color || C.text, comp: "", cand: "", hl: 0, caret: "off", text: "" };
    if (q.how === "ime") {
      let done = "";
      for (const s of q.parts) {
        if (t >= s.e) { done += s.hz.join(""); continue; }
        const n = s.a.filter((v) => t >= v).length; if (!n) break;
        if (s.own) done += s.hz.slice(0, n).join(""); else { L.comp = s.py.slice(0, n).join(""); L.cand = s.hz.join(""); }
        break;
      }
      L.text = done;
    } else if (q.how === "print") { L.progress = (t - q.at) * (src.cps || 60); L.text = q.text; }
    else { const n = q.times.filter((v) => t >= v).length; L.text = chars(q.text).slice(0, n).join(""); }
    if (q.how === "paste") L.hl = t < q.at + PASTE_HOLD ? 1 : 1 - seg(t, q.at + PASTE_HOLD, q.at + PASTE_HOLD + PASTE_FADE);
    if (i === act && q.how !== "print") L.caret = t < q.end ? "solid" : ((t - q.end) * 1.9) % 1 < 0.55 ? "on" : "off";   // printed output has no caret
    st.lines.push(L);
  });
  // scroll: the last line that has begun stays inside the body
  if (p.window) {
    const room = p.window.h - (p.window.kind === "app" ? 0 : 60) - 2 * p.pad, need = (k) => Math.max(0, (k + 1) * lh - room);
    let s = 0; pl.forEach((q, k) => { if (t >= q.at) s = lerp(k ? need(k - 1) : 0, need(k), io(seg(t, q.at, q.at + 0.25))); });
    st.scroll = s;
  }
  // the keys that are down now
  for (const q of pl) for (const [kt, c] of q.keys) {
    const d = t - kt; if (d < -KEY_DOWN || d > KEY_UP) continue;
    const k = keyOf(c), v = d < 0 ? 1 + d / KEY_DOWN : 1 - d / KEY_UP; st.keys[k] = Math.max(st.keys[k] || 0, v);
  }
  // the step chip
  let si = -1; p.steps.forEach((s, k) => { if (t >= s[0]) si = k; });
  if (si >= 0) { const d = t - p.steps[si][0]; st.step = { n: String(p.steps[si][1]), text: String(p.steps[si][2]), k: out(seg(d, 0, 0.4)), slide: si === 0 ? out(seg(d, 0, 0.5)) : 1 }; }
  // the capture player: the state on screen, the one it fades from, the camera
  const c = p.capture;
  if (c && c.states && c.states.length) {
    let i = -1; c.states.forEach((s, k) => { if (t >= s[0]) i = k; });
    if (i < 0) i = 0;
    const fade = c.fade ?? 0.09, q = i > 0 && c.states[i - 1][1] !== c.states[i][1] ? seg(t, c.states[i][0], c.states[i][0] + fade) : 1;
    st.capture = { a: i > 0 ? c.states[i - 1][1] : null, b: c.states[i][1], q, cam: cameraAt(c.camera, t, captureFit(c)), at: c.at || [W0 / 2, H0 / 2], size: c.size || [1440, 900], view: c.view || null };
  }
  // marks: a spotlight dims the rest, a ring of light circles its box
  for (const m of p.marks) {
    const a = Math.min(seg(t, m.t0, m.t0 + 0.25), 1 - seg(t, m.t1 - 0.25, m.t1)); if (a <= 0) continue;
    const [x, y, w, h] = m.box, sp = m.space || (st.capture ? "capture" : "stage"), [x0, y0] = project(st, x, y, sp), [x1, y1] = project(st, x + w, y + h, sp);
    st.marks.push({ kind: m.kind || "spot", x: x0, y: y0, w: x1 - x0, h: y1 - y0, a: io(a) });
  }
  // the cursor, through its space's camera
  const cu = p.cursor;
  if (cu && cu.keys && cu.keys.length) {
    const pt = cursorPath(cu.keys)(t), pr = presses(cu.clicks || [], cu.drags || [])(t), [x, y] = project(st, pt.x, pt.y, cu.space || "stage");
    const rings = (cu.clicks || []).map((c0) => t - c0).filter((d) => d >= 0 && d < RING).map((d) => ({ r: 14 + 70 * out(d / RING), a: 0.9 * (1 - d / RING) }));
    st.cursor = { x, y, press: clamp(pr), rings, size: cu.size || 74 };
  }
  return st;
}
/** The capture states the painters need at this state (preload them before painting: the canvas painter does not wait). */
export const needs = (st) => (st.capture ? [st.capture.a, st.capture.b].filter((n, i) => n && (i === 1 || st.capture.q < 1)) : []);
/**
 * Pictures by name for the canvas painter, loaded when a frame asks for them and kept a few at a time, for a page whose
 * frame(t) returns a Promise (engines/CONTRACT.md): const pics = loader("assets/ui/{name}.jpg"); in frame(t):
 * st = state(P, t); await pics.load(needs(st)); canvas(ctx, st, P, pics.get). A hundred 3x captures decoded at once do
 * not fit in memory; keep holds the most recently used. It caches decoded pictures by name only, so what a frame draws
 * never depends on what was drawn before it. A picture that does not load is an error that names it.
 */
export function loader(src = "assets/ui/{name}.jpg", keep = 8) {
  const cache = new Map(), ready = new Map(), get = (n) => ready.get(n);
  async function load(names) {
    for (const n of names) {
      if (cache.has(n)) { const v = cache.get(n); cache.delete(n); cache.set(n, v); continue; }   // most recently used last
      cache.set(n, fetch(src.replace("{name}", n)).then((r) => { if (!r.ok) throw new Error(`ui-stage: no picture ${n} (${src}: ${r.status})`); return r.blob(); })
        .then((b) => createImageBitmap(b)).then((b) => { ready.set(n, b); return b; }));
    }
    await Promise.all(names.map((n) => cache.get(n)));
    while (cache.size > Math.max(keep, names.length)) {
      const [k, v] = cache.entries().next().value; cache.delete(k); ready.delete(k);
      v.then((b) => b.close && b.close()).catch(() => {});
    }
    return get;
  }
  return { load, get };
}

// ── canvas painter ──────────────────────────────────────────────────────────────────────────────────────────────────
const ARROW = "M5 3l0 19 5-4.6 3.4 7.6 3.2-1.4-3.4-7.5 6.8 0z";   // the arrow, in a 28-unit box
let CUR = null; const arrow = () => (CUR ??= new Path2D(ARROW));   // made on the first paint: node loads this file to check it
const pic = (pics, n) => (typeof pics === "function" ? pics(n) : pics && pics[n]);
/**
 * Draws st into ctx (1920 × 1080 px; scale the context first for 4K): the capture (pics: { name: drawable } or
 * name => drawable, an Image, ImageBitmap or canvas already loaded; a state with no picture is left out), the window
 * and its lines, the keyboard, the marks, the step chip and the cursor. The canvas painter does not tilt (rx, ry).
 */
export function canvas(ctx, st, params, pics = {}) {
  const p = opts(params), C = p.colors;
  if (st.capture) drawCapture(ctx, st.capture, pics);
  if (p.window || p.keyboard) {
    const k = st.cam; ctx.save(); ctx.translate(W0 / 2, H0 / 2); ctx.scale(k.z, k.z); ctx.translate(-k.cx, -k.cy);
    if (p.window) drawWindow(ctx, st, p);
    if (p.keyboard) drawKeyboard(ctx, st, p);
    ctx.restore();
  }
  for (const m of st.marks) {
    ctx.save(); ctx.globalAlpha *= m.a;
    if (m.kind === "ring") { ctx.strokeStyle = C.accent; ctx.lineWidth = 6; ctx.shadowColor = C.accent; ctx.shadowBlur = 26; ctx.beginPath(); ctx.roundRect(m.x - 6, m.y - 6, m.w + 12, m.h + 12, 14); ctx.stroke(); }
    else { ctx.fillStyle = `rgba(${C.shade},0.62)`; ctx.beginPath(); ctx.rect(0, 0, W0, H0); ctx.roundRect(m.x, m.y, m.w, m.h, 16); ctx.fill("evenodd"); }
    ctx.restore();
  }
  if (st.step) drawChip(ctx, st.step, p);
  if (st.cursor) {
    const c = st.cursor;
    for (const r of c.rings) { ctx.save(); ctx.strokeStyle = C.accent; ctx.globalAlpha *= r.a; ctx.lineWidth = 5; ctx.beginPath(); ctx.arc(c.x, c.y, r.r, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
    const s = c.size / 28 * (1 - 0.16 * c.press);
    ctx.save(); ctx.translate(c.x - 5 * s, c.y - 3 * s); ctx.scale(s, s); ctx.shadowColor = "rgba(0,0,0,0.5)"; ctx.shadowBlur = 8 / s; ctx.shadowOffsetY = 6;
    ctx.fillStyle = "#fff"; ctx.fill(arrow()); ctx.shadowColor = "transparent"; ctx.lineWidth = 1.5; ctx.strokeStyle = "#111"; ctx.lineJoin = "round"; ctx.stroke(arrow()); ctx.restore();
  }
}
// the capture in view, drawn at the context's own pixels: the picture's full resolution reaches the screen, however far the
// camera pushes in (the DOM painter draws it the same way, into a full-frame canvas: see build())
function drawCapture(ctx, c, pics) {
  const [w, h] = c.size, z = c.cam.z, x = c.at[0] - c.cam.cx * z, y = c.at[1] - c.cam.cy * z;
  ctx.save(); if (c.view) { ctx.beginPath(); ctx.roundRect(...c.view, 18); ctx.clip(); }
  ctx.beginPath(); ctx.roundRect(x, y, w * z, h * z, 14 * Math.min(z, 2)); ctx.clip();
  ctx.imageSmoothingQuality = "high";
  const ok = (im) => im && (im.complete === undefined || (im.complete && im.naturalWidth > 0));   // an <img> not loaded yet draws nothing
  const A = c.a && c.q < 1 ? pic(pics, c.a) : null, B = pic(pics, c.b);
  if (ok(A)) ctx.drawImage(A, x, y, w * z, h * z);
  if (ok(B)) { ctx.globalAlpha = ok(A) ? c.q : 1; ctx.drawImage(B, x, y, w * z, h * z); }
  ctx.restore();
}
function drawWindow(ctx, st, p) {
  const C = p.colors, w = p.window, kind = w.kind || "terminal", light = kind === "browser", bar = kind === "app" ? 0 : 60;
  ctx.save(); ctx.shadowColor = "rgba(0,0,0,0.55)"; ctx.shadowBlur = 80; ctx.shadowOffsetY = 30;
  ctx.fillStyle = light ? "#ffffff" : C.window; ctx.beginPath(); ctx.roundRect(w.x, w.y, w.w, w.h, 18); ctx.fill(); ctx.restore();
  ctx.save(); ctx.beginPath(); ctx.roundRect(w.x, w.y, w.w, w.h, 18); ctx.clip();
  if (bar) {
    ctx.fillStyle = light ? C.light : C.bar; ctx.fillRect(w.x, w.y, w.w, bar);
    ["#ff5f57", "#febc2e", "#28c840"].forEach((c, i) => { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(w.x + 34 + i * 30, w.y + bar / 2, 9, 0, Math.PI * 2); ctx.fill(); });
    ctx.font = `500 26px ${p.font}`; ctx.textBaseline = "middle";
    if (light) { ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.roundRect(w.x + 150, w.y + 10, w.w - 190, bar - 20, (bar - 20) / 2); ctx.fill(); ctx.fillStyle = "#3b3833"; ctx.fillText(w.url || "", w.x + 176, w.y + bar / 2 + 1); }
    else { ctx.fillStyle = C.dim; ctx.fillText(w.title || "", w.x + 140, w.y + bar / 2 + 1); }
  }
  const x0 = w.x + p.pad, top = w.y + bar + p.pad, lh = p.size * p.leading;
  ctx.beginPath(); ctx.rect(w.x, w.y + bar, w.w, w.h - bar); ctx.clip();
  ctx.font = `500 ${p.size}px ${p.mono}`; ctx.textBaseline = "alphabetic";
  const ink = light ? C.ink : C.text, pops = [];
  for (const L of st.lines) {
    const base = top + L.y - st.scroll + p.size * 1.05;
    let x = x0;
    if (L.prompt) { ctx.fillStyle = C.prompt; ctx.fillText(L.prompt, x, base); x += ctx.measureText(L.prompt).width; }
    const full = L.text, tw = ctx.measureText(full).width;
    if (L.hl > 0) { ctx.save(); ctx.globalAlpha *= 0.45 * L.hl; ctx.fillStyle = C.paste; ctx.fillRect(x - 6, base - p.size * 0.95, tw + 12, p.size * 1.3); ctx.restore(); }
    ctx.fillStyle = L.color === C.text ? ink : L.color;
    if (L.how === "print") {   // each letter rises 16 px and fades in over the five letters behind the head
      let cx = x;
      for (const [j, ch] of Array.from(full).entries()) {
        const a = clamp((L.progress - j) / 5); if (a <= 0) break;
        ctx.save(); ctx.globalAlpha *= a; ctx.fillText(ch, cx, base - 16 * (1 - a)); ctx.restore(); cx += ctx.measureText(ch).width;
      }
    } else ctx.fillText(full, x, base);
    let cx = x + tw;
    if (L.comp) {
      const cw = ctx.measureText(L.comp).width; ctx.fillStyle = ink; ctx.fillText(L.comp, cx, base);
      ctx.fillStyle = C.paste; ctx.fillRect(cx, base + 8, cw, 3);
      pops.push([L.cand, cx, base + 22]); cx += cw;
    }
    if (L.caret === "solid" || L.caret === "on") { ctx.fillStyle = ink; ctx.fillRect(cx + 3, base - p.size * 0.86, p.size * 0.55, p.size * 1.05); }
  }
  ctx.restore();
  for (const [cand, x, y] of pops) drawCandidates(ctx, cand, x, y, p);   // over the window's edge, as an input method's box is
}
function drawCandidates(ctx, cand, x, y, p) {
  const C = p.colors, s = Math.round(p.size * 0.92), first = Array.from(cand)[0] || "";
  ctx.save(); ctx.font = `500 ${s}px ${p.font}`;
  const items = [["1", cand], ["2", first]], wsum = items.reduce((a, [n, c]) => a + ctx.measureText(`${n} ${c}`).width, 0) + 70;
  ctx.shadowColor = "rgba(0,0,0,0.5)"; ctx.shadowBlur = 30; ctx.shadowOffsetY = 12; ctx.fillStyle = "#f7f4ee";
  ctx.beginPath(); ctx.roundRect(x - 8, y, wsum, s * 1.6, 12); ctx.fill(); ctx.shadowColor = "transparent";
  let cx = x + 14; const by = y + s * 1.15;
  items.forEach(([n, c], i) => { ctx.fillStyle = i ? "#a39f95" : "#2f7f92"; ctx.fillText(n, cx, by); cx += ctx.measureText(`${n} `).width; ctx.fillStyle = C.ink; ctx.fillText(c, cx, by); cx += ctx.measureText(c).width + 36; });
  ctx.restore();
}
function drawKeyboard(ctx, st, p) {
  const C = p.colors, kb = p.keyboard, lay = keyLayout(kb.w || 1800);
  ctx.save(); ctx.translate(kb.x, kb.y);
  const g = ctx.createLinearGradient(0, 0, 0, lay.h); g.addColorStop(0, "#3a3936"); g.addColorStop(1, "#222120");
  ctx.shadowColor = "rgba(0,0,0,0.8)"; ctx.shadowBlur = 120; ctx.shadowOffsetY = 60; ctx.fillStyle = g; ctx.beginPath(); ctx.roundRect(0, 0, lay.w, lay.h, lay.w * 0.017); ctx.fill(); ctx.shadowColor = "transparent";
  const fs = Math.round(lay.keys[0].h * 0.33); ctx.font = `600 ${fs}px ${p.font}`; ctx.textAlign = "center"; ctx.textBaseline = "middle";
  const ac = hex(C.accent);
  for (const k of lay.keys) {
    const v = st.keys[keyOf(k.key)] || 0, dy = 7 * v, r = k.h * 0.14;
    ctx.fillStyle = "#0c0c0b"; ctx.beginPath(); ctx.roundRect(k.x, k.y + 8, k.w, k.h, r); ctx.fill();
    ctx.fillStyle = v > 0.02 ? `rgb(${lerp(90, ac[0], v) | 0},${lerp(89, ac[1], v) | 0},${lerp(84, ac[2], v) | 0})` : "#5c5b56";
    if (v > 0.02) { ctx.shadowColor = `rgba(${ac.join(",")},${0.8 * v})`; ctx.shadowBlur = 50 * v; }
    ctx.beginPath(); ctx.roundRect(k.x, k.y + dy, k.w, k.h, r); ctx.fill(); ctx.shadowColor = "transparent";
    ctx.fillStyle = v > 0.4 ? "#161616" : "#f4f1e8"; ctx.fillText(k.label, k.x + k.w / 2, k.y + dy + k.h / 2);
  }
  ctx.restore();
}
function drawChip(ctx, s, p) {
  const C = p.colors, [x, y] = p.chip, h = 84, fs = 44;
  ctx.save(); ctx.font = `600 ${fs}px ${p.font}`;
  const w = ctx.measureText(s.text).width + h + 40, dx = (1 - s.slide) * -(w + x + 40);
  ctx.translate(x + dx, y); ctx.fillStyle = "rgba(24,24,22,0.94)"; ctx.shadowColor = "rgba(0,0,0,0.35)"; ctx.shadowBlur = 30; ctx.shadowOffsetY = 10;
  ctx.beginPath(); ctx.roundRect(0, 0, w, h, h / 2); ctx.fill(); ctx.shadowColor = "transparent"; ctx.clip();
  const up = (1 - s.k) * 60; ctx.textBaseline = "middle";
  ctx.fillStyle = C.accent; ctx.beginPath(); ctx.arc(h / 2, h / 2 + up, h / 2 - 12, 0, Math.PI * 2); ctx.fill();
  ctx.textAlign = "center"; ctx.fillStyle = "#111"; ctx.font = `700 ${fs * 0.8}px ${p.font}`; ctx.fillText(s.n, h / 2, h / 2 + up + 2);
  ctx.textAlign = "left"; ctx.fillStyle = C.text; ctx.font = `600 ${fs}px ${p.font}`; ctx.fillText(s.text, h + 14, h / 2 + up + 2);
  ctx.restore();
}
const hex = (c) => { const m = /^#?([0-9a-f]{6})$/i.exec(String(c)); const n = m ? parseInt(m[1], 16) : 0xffd93b; return [n >> 16, (n >> 8) & 255, n & 255]; };

// ── DOM painter ─────────────────────────────────────────────────────────────────────────────────────────────────────
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
/**
 * build(root, params) makes the elements once inside root (absolutely placed, 1920 × 1080): a full-frame canvas the
 * capture is drawn into at the output's own pixels (an Image a state from capture.src, "assets/ui/{name}.jpg"; els.ready
 * resolves once they are decoded, so await it before the first frame), the stage (window, keyboard), the marks, the chip
 * and the cursor. dom(els, st, pics) changes only transforms, opacity, sizes and the lines' text, and redraws the capture
 * canvas; pics defaults to the Images build loaded; with many states pass loader().get instead and await its load().
 * The capture is not an element enlarged with a CSS scale: a layer under a 3D transform can be rasterised at its own
 * size and then enlarged (a 2026-11 film's player, a canvas in a CSS-scaled box, blurred the interface's small type that
 * way at a 2–3× push), so the picture is drawn at the output's pixels, as canvas() does. A tilt (rx, ry) is a small CSS 3D
 * on the whole drawn canvas, which stays sharp.
 */
export function build(root, params) {
  const p = opts(params), C = p.colors, doc = root.ownerDocument;
  const el = (css, parent = root, html) => { const d = doc.createElement("div"); d.style.cssText = "position:absolute;" + css; if (html != null) d.innerHTML = html; parent.append(d); return d; };
  const els = { p, root };
  plans(p);   // a wrong line or capture is an error that names it, here as in state()
  const dpr = (doc.defaultView && doc.defaultView.devicePixelRatio) >= 1.5 ? 2 : 1;   // a 4K render draws at its own pixels
  els.dpr = dpr;
  if (p.capture) {   // not an element scaled up with CSS (that blurs): a full-frame canvas the capture is drawn into, as canvas() does
    const src = p.capture.src || "assets/ui/{name}.jpg";
    els.cap = doc.createElement("canvas"); els.cap.width = W0 * dpr; els.cap.height = H0 * dpr;
    els.cap.style.cssText = `position:absolute;left:0;top:0;width:${W0}px;height:${H0}px;`; root.append(els.cap);
    els.pics = {};
    for (const n of new Set(p.capture.states.map((s) => s[1]))) { const im = new Image(); im.decoding = "async"; im.src = src.replace("{name}", n); els.pics[n] = im; }
    els.ready = Promise.all(Object.values(els.pics).map((im) => im.decode().catch(() => { throw new Error(`ui-stage: picture ${im.src} did not load`); })));
  } else els.ready = Promise.resolve();
  els.stage = el(`left:0;top:0;width:${W0}px;height:${H0}px;transform-origin:0 0;`);
  if (p.window) {
    const w = p.window, kind = w.kind || "terminal", light = kind === "browser", bar = kind === "app" ? 0 : 60;
    els.win = el(`left:${w.x}px;top:${w.y}px;width:${w.w}px;height:${w.h}px;border-radius:18px;overflow:hidden;background:${light ? "#fff" : C.window};box-shadow:0 30px 80px rgba(0,0,0,.55);`, els.stage);
    if (bar) {
      const dots = ["#ff5f57", "#febc2e", "#28c840"].map((c) => `<span style="display:inline-block;width:18px;height:18px;border-radius:9px;margin-right:12px;background:${c}"></span>`).join("");
      const label = light ? `<span style="margin-left:24px;flex:1;height:40px;border-radius:20px;background:#fff;color:#3b3833;display:flex;align-items:center;padding:0 24px">${esc(w.url || "")}</span>` : `<span style="margin-left:24px;color:${C.dim}">${esc(w.title || "")}</span>`;
      el(`left:0;top:0;right:0;height:${bar}px;background:${light ? C.light : C.bar};display:flex;align-items:center;padding:0 25px;font:500 26px ${p.font};`, els.win, dots + label);
    }
    els.body = el(`left:${p.pad}px;top:${bar + p.pad}px;right:${p.pad}px;bottom:0;font:500 ${p.size}px/${p.leading} ${p.mono};color:${light ? C.ink : C.text};white-space:pre;`, els.win);
    els.rows = p.lines.map((_, i) => el(`left:0;top:${i * p.size * p.leading}px;`, els.body));
  }
  if (p.keyboard) {
    const kb = p.keyboard, lay = keyLayout(kb.w || 1800);
    els.kb = el(`left:${kb.x}px;top:${kb.y}px;width:${lay.w}px;height:${lay.h}px;border-radius:${lay.w * 0.017}px;background:linear-gradient(#3a3936,#222120);box-shadow:0 60px 120px rgba(0,0,0,.8);`, els.stage);
    els.keys = lay.keys.map((k) => ({ key: keyOf(k.key), e: el(`left:${k.x}px;top:${k.y}px;width:${k.w}px;height:${k.h}px;border-radius:${k.h * 0.14}px;background:#5c5b56;color:#f4f1e8;box-shadow:0 8px 0 #0c0c0b;display:flex;align-items:center;justify-content:center;font:600 ${Math.round(k.h * 0.33)}px ${p.font};`, els.kb, esc(k.label)) }));
  }
  els.marks = p.marks.map(() => el("left:0;top:0;width:0;height:0;display:none;border-radius:16px;"));
  if (p.steps.length) els.chip = el(`left:${p.chip[0]}px;top:${p.chip[1]}px;height:84px;border-radius:42px;background:rgba(24,24,22,.94);color:${C.text};display:flex;align-items:center;gap:14px;padding:0 40px 0 12px;font:600 44px ${p.font};white-space:nowrap;overflow:hidden;box-shadow:0 10px 30px rgba(0,0,0,.35);`,
    root, `<b style="width:60px;height:60px;border-radius:30px;background:${C.accent};color:#111;display:flex;align-items:center;justify-content:center;font-size:35px"></b><span></span>`);
  if (p.cursor) els.cur = el(`left:0;top:0;width:74px;height:74px;transform-origin:${(5 * 74 / 28).toFixed(2)}px ${(3 * 74 / 28).toFixed(2)}px;filter:drop-shadow(0 6px 8px rgba(0,0,0,.5));`, root, `<svg viewBox="0 0 28 28" width="100%" height="100%"><path d="${ARROW}" fill="#fff" stroke="#111" stroke-width="1.5" stroke-linejoin="round"/></svg>`);
  els.rings = doc.createElement("canvas"); els.rings.width = W0 * dpr; els.rings.height = H0 * dpr;
  els.rings.style.cssText = `position:absolute;left:0;top:0;width:${W0}px;height:${H0}px;pointer-events:none;`; root.append(els.rings);
  return els;
}
export function dom(els, st, pics = els.pics) {
  const p = els.p, C = p.colors;
  if (els.cap) {
    const x = els.cap.getContext("2d"); x.setTransform(els.dpr, 0, 0, els.dpr, 0, 0); x.clearRect(0, 0, W0, H0);
    if (st.capture) {
      const c = st.capture; drawCapture(x, c, pics);
      const tilt = Math.abs(c.cam.rx) + Math.abs(c.cam.ry) > 1e-3;   // a small tilt of the whole drawn frame: barely resampled, stays sharp
      els.cap.style.transformOrigin = `${c.at[0]}px ${c.at[1]}px`;
      els.cap.style.transform = tilt ? `perspective(2400px) rotateX(${c.cam.rx}deg) rotateY(${c.cam.ry}deg)` : "";
    }
  }
  const k = st.cam; els.stage.style.transform = `translate(${W0 / 2}px,${H0 / 2}px) scale(${k.z}) translate(${-k.cx}px,${-k.cy}px)`;
  if (els.rows) {
    els.body.style.transform = `translateY(${-st.scroll}px)`;
    const byI = new Map(st.lines.map((L) => [L.i, L]));
    els.rows.forEach((r, i) => {
      const L = byI.get(i);
      if (!L) { r.innerHTML = ""; return; }
      const ink = p.window.kind === "browser" ? C.ink : C.text, col = L.color === C.text ? ink : L.color;
      let h = L.prompt ? `<span style="color:${C.prompt}">${esc(L.prompt)}</span>` : "";
      const txt = L.how === "print" ? Array.from(L.text).map((ch, j) => { const a = clamp((L.progress - j) / 5); return a <= 0 ? "" : `<span style="opacity:${a.toFixed(3)};position:relative;top:${(-16 * (1 - a)).toFixed(1)}px">${esc(ch)}</span>`; }).join("") : esc(L.text);
      h += `<span style="color:${col};${L.hl > 0 ? `background:rgba(${hex(C.paste).join(",")},${(0.45 * L.hl).toFixed(3)});border-radius:6px;` : ""}">${txt}</span>`;
      if (L.comp) h += `<span style="position:relative;border-bottom:3px solid ${C.paste}">${esc(L.comp)}<span style="position:absolute;left:-8px;top:calc(100% + 12px);background:#f7f4ee;color:${C.ink};border-radius:12px;padding:4px 18px;font:500 .92em ${p.font};box-shadow:0 12px 30px rgba(0,0,0,.5)"><b style="color:#2f7f92">1</b> ${esc(L.cand)}<i style="font-style:normal;color:#a39f95;margin-left:30px">2</i> ${esc(Array.from(L.cand)[0] || "")}</span></span>`;
      if (L.caret !== "off" && L.caret) h += `<span style="display:inline-block;width:.55em;height:1.05em;background:${p.window.kind === "browser" ? C.ink : C.text};vertical-align:-.16em;margin-left:3px"></span>`;
      if (r._h !== h) { r.innerHTML = h; r._h = h; }   // a cache of what this element shows, not state between frames
    });
  }
  if (els.keys) {
    const ac = hex(C.accent);
    for (const { key, e } of els.keys) {
      const v = st.keys[key] || 0;
      e.style.transform = `translateY(${(7 * v).toFixed(2)}px)`;
      e.style.background = v > 0.02 ? `rgb(${lerp(92, ac[0], v) | 0},${lerp(91, ac[1], v) | 0},${lerp(86, ac[2], v) | 0})` : "#5c5b56";
      e.style.color = v > 0.4 ? "#161616" : "#f4f1e8";
      e.style.boxShadow = v > 0.02 ? `0 ${(8 - 7 * v).toFixed(1)}px 0 #0c0c0b,0 0 ${(50 * v).toFixed(0)}px rgba(${ac.join(",")},${(0.8 * v).toFixed(2)})` : "0 8px 0 #0c0c0b";
    }
  }
  els.marks.forEach((e, i) => {
    const m = st.marks[i];
    if (!m) { e.style.display = "none"; return; }
    e.style.display = ""; e.style.opacity = m.a.toFixed(3);
    Object.assign(e.style, { left: `${m.x}px`, top: `${m.y}px`, width: `${m.w}px`, height: `${m.h}px` });
    e.style.boxShadow = m.kind === "ring" ? `0 0 0 6px ${C.accent},0 0 26px 6px ${C.accent}` : `0 0 0 4000px rgba(${C.shade},0.62)`;
  });
  if (els.chip) {
    els.chip.style.display = st.step ? "flex" : "none";
    if (st.step) {
      const [b, s] = els.chip.children, up = `translateY(${((1 - st.step.k) * 60).toFixed(1)}px)`;
      b.textContent = st.step.n; s.textContent = st.step.text; b.style.transform = up; s.style.transform = up;
      els.chip.style.transform = `translateX(${((1 - st.step.slide) * -(els.chip.offsetWidth + p.chip[0] + 40)).toFixed(1)}px)`;   // out of the frame, however long the text
    }
  }
  const x = els.rings.getContext("2d"); x.setTransform(els.dpr, 0, 0, els.dpr, 0, 0); x.clearRect(0, 0, W0, H0);
  if (els.cur) {
    els.cur.style.display = st.cursor ? "" : "none";
    if (st.cursor) {
      const c = st.cursor, s = c.size / 74;
      els.cur.style.transform = `translate(${(c.x - 5 * 74 / 28).toFixed(2)}px,${(c.y - 3 * 74 / 28).toFixed(2)}px) scale(${(s * (1 - 0.16 * c.press)).toFixed(3)})`;   // the tip is the origin: it stays on the point at any size and press
      for (const r of c.rings) { x.save(); x.strokeStyle = C.accent; x.globalAlpha = r.a; x.lineWidth = 5; x.beginPath(); x.arc(c.x, c.y, r.r, 0, Math.PI * 2); x.stroke(); x.restore(); }
    }
  }
}
