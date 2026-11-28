// source-plate — a plate that says where something comes from: a person (the name, who they are), a paper (its title;
// authors, venue and year; its DOI), a dataset, or a quote's source. Its words are the source's own, copied as they are
// (hard rule 5); what the component adds is one look for every plate in a film and the two floors a plate tends to
// break: it stays up as long as the BRIEF's pace needs to read all of it, counted the way bin/vh readcheck counts
// (playbook/03 §4), never under the floor, and no line is drawn under the label floor of where the film is watched.
// layout() wraps the lines once (measure from a canvas or the DOM); state() is a function of t; texts() gives
// window.film.texts its lines, so bin/vh readcheck and textcheck measure them; boxes() gives window.film.ui(t) its box.
// Canvas and DOM painters.
import { FRAME, seg, safeBoxes, ease, luminance } from "../lib/core.js";

export const defaults = {
  kind: "source",              // person | paper | data | quote | source: what the tag says unless tag is given
  title: "",                   // the first line: a name, a paper's title, a dataset, the quoted words, as the source has them
  detail: "",                  // the second line: who they are; authors · venue · year; publisher · edition; who said it, where
  ref: "",                     // a third line, monospaced, optional: a DOI, an arXiv id, a page, a URL's host and path
  tag: null,                   // the label over the title; null: by kind and lang; "" for none
  lang: "zh",                  // the tags' language: zh 人物 论文 数据 原话 出处 · en Speaker Paper Data Quote Source
  t: 0,                        // when it starts coming in (s)
  hold: null,                  // how long it is fully up (s); null: what the pace needs to read all of it; never under the floor
  pace: "normal",              // relaxed | normal | brisk: the BRIEF's Pace (brisk is the floor)
  in: 0.45, out: 0.35,         // the move in and the move out (s)
  anchor: "lower-left",        // lower-left | lower-right | upper-left | upper-right
  margin: null,                // [from the side, from the top or bottom] in px; null: the title-safe box (10 % in)
  width: 1000,                 // the widest a line runs before it wraps (px)
  size: 52, detailSize: 44, refSize: 44, tagSize: 44,
  floor: 44,                   // no line under this (px at 1080p): Watch on's label floor (playbook/03 §4: 44 desktop and phone, 80 feed)
  colors: { plate: "13,17,23", alpha: 0.82, text: "#f4f6fb", detail: "#c9d1d9", ref: "#9aa4b2", accent: "#e4572e" },
  font: '"Helvetica Neue", "PingFang SC", "Noto Sans CJK SC", sans-serif', weight: 700, detailWeight: 500,
  mono: 'Menlo, "SF Mono", "Noto Sans Mono", monospace',
};
const TAGS = { zh: { person: "人物", paper: "论文", data: "数据", quote: "原话", source: "出处" },
  en: { person: "Speaker", paper: "Paper", data: "Data", quote: "Quote", source: "Source" } };
const opts = (p) => ({ ...defaults, ...p, colors: { ...defaults.colors, ...(p && p.colors) } });
// the tag's letters on its chip: near-black or white, whichever reads better on the accent (WCAG contrast)
const onChip = (bg) => { const L = luminance(bg); return (L + 0.05) / 0.06 >= 1.05 / (L + 0.05) ? "#111111" : "#ffffff"; };

// ── reading time, as tools/readcheck.py counts it: CJK characters at one rate, other non-space characters at another,
// plus the time to find the text; the floor is one brisk read and never under 1.5 s ──
const CJK = [[0x3040, 0x30FF], [0x31F0, 0x31FF], [0x3400, 0x4DBF], [0x4E00, 0x9FFF], [0xF900, 0xFAFF], [0xAC00, 0xD7AF], [0x1100, 0x11FF], [0x3130, 0x318F], [0x20000, 0x2FA1F]];
const PACES = { relaxed: [4.5, 15, 1.0], normal: [6, 18, 0.8], brisk: [7, 20, 0.8] };
const isCJK = (ch) => { const o = ch.codePointAt(0); return CJK.some(([a, b]) => o >= a && o <= b); };
/** Seconds to read text once at a pace (relaxed | normal | brisk), as bin/vh readcheck counts; at least 1.5 s. */
export function readSeconds(text, pace = "normal") {
  const [cjk, lat, pad] = PACES[pace] || PACES.normal;
  let a = 0, b = 0;
  for (const ch of String(text)) { if (/\s/.test(ch)) continue; if (isCJK(ch)) a++; else b++; }
  return Math.max(1.5, a / cjk + b / lat + pad);
}

// a line may not start with these (as components/lib/text.js wraps)
const NO_START = "，。、；：？！）」』》〉”’,.;:?!)%";
/** Greedy wrap: a CJK character is a unit, a Latin word is one; width(s) measures a candidate line in px. */
function wrap(str, max, width) {
  const units = []; let buf = "";
  for (const ch of String(str)) {
    if (isCJK(ch) || NO_START.includes(ch) && buf === "") { if (buf) units.push(buf); buf = ""; units.push(ch); }
    else if (ch === " ") { units.push(buf + " "); buf = ""; }
    else buf += ch;
  }
  if (buf) units.push(buf);
  const lines = []; let line = "";
  for (const u of units) {
    const test = line + u;
    if (line && width(test.trimEnd()) > max && !NO_START.includes(u[0])) { lines.push(line.trimEnd()); line = u.trimStart(); }
    else line = test;
  }
  if (line.trim()) lines.push(line.trimEnd());
  return lines;
}

/**
 * The plate, once (setup, ready): measure(text, font) gives a line's width in px (a canvas's measureText with ctx.font =
 * font, or a DOM element's width). → { box: [x0, y0, x1, y1], fromLeft, rows: [{ part, text, x, y, font, size, color }],
 * bar: [x, y, w, h], start, shown, end, gone, hold, need }: start comes in, shown is fully up, end starts out, gone is gone.
 */
export function layout(params, measure) {
  const p = opts(params), C = p.colors, F = (s) => Math.max(p.floor, s);
  const tag = p.tag ?? (TAGS[p.lang] || TAGS.zh)[p.kind] ?? "";
  const parts = [
    ["tag", tag, F(p.tagSize), `${p.weight} ${F(p.tagSize)}px ${p.font}`, onChip(C.accent)],
    ["title", p.title, F(p.size), `${p.weight} ${F(p.size)}px ${p.font}`, C.text],
    ["detail", p.detail, F(p.detailSize), `${p.detailWeight} ${F(p.detailSize)}px ${p.font}`, C.detail],
    ["ref", p.ref, F(p.refSize), `400 ${F(p.refSize)}px ${p.mono}`, C.ref],
  ].filter(([, s]) => String(s || "").trim());
  const padX = 34, padY = 26, gap = 12, barW = 8, chip = 12;   // chip: the tag's own padding on its accent chip
  const rows = []; let y = 0, w = 0;
  for (const [part, s, size, font, color] of parts) {
    if (rows.length) y += gap;
    for (const line of wrap(s, p.width, (x) => measure(x, font))) {
      y += size * 1.18;
      rows.push({ part, text: line, y, font, size, color, w: measure(line, font) });
      w = Math.max(w, measure(line, font) + (part === "tag" ? 2 * chip : 0));
    }
  }
  const tb = safeBoxes(FRAME.w, FRAME.h).title, m = p.margin || [tb.x0, tb.y0];
  const bw = barW + padX * 2 + w, bh = y + padY * 2 + Math.round((rows.at(-1)?.size || 0) * 0.28);
  const fromLeft = !String(p.anchor).endsWith("right"), top = String(p.anchor).startsWith("upper");
  const x0 = fromLeft ? m[0] : FRAME.w - m[0] - bw, y0 = top ? m[1] : FRAME.h - m[1] - bh;
  const tx = x0 + (fromLeft ? barW : 0) + padX;
  for (const r of rows) {
    r.x = tx + (r.part === "tag" ? chip : 0); r.y = y0 + padY + r.y;
    if (r.part === "tag") r.chip = [tx, r.y - r.size * 0.95, r.w + 2 * chip, r.size * 1.2];   // the accent behind the tag's letters
  }
  const all = parts.map(([, s]) => s).join(" ");
  const need = readSeconds(all, p.pace), floor = readSeconds(all, "brisk");
  const hold = Math.max(p.hold ?? need, floor);   // the floor is not a choice; a hold between it and the pace's need is
  const start = p.t, shown = start + p.in, end = shown + hold, gone = end + p.out;
  return { box: [x0, y0, x0 + bw, y0 + bh], fromLeft, rows, bar: [fromLeft ? x0 : x0 + bw - barW, y0, barW, bh],
    start, shown, end, gone, hold, need, floor };
}

/**
 * The plate at t: { vis (0 before it starts and after it is gone), reveal (how much of the plate shows, from its bar's
 * side), bar (how far the bar has grown), dx (its slide on the way out), rows: [{ ...row, a (opacity), dy }] }.
 */
export function state(params, t, lay) {
  const p = opts(params);
  if (!lay.rows.length || t < lay.start || t >= lay.gone) return { vis: 0, reveal: 0, bar: 0, dx: 0, rows: [] };
  const u = seg(t, lay.start, lay.shown), o = ease.inCubic(seg(t, lay.end, lay.gone));
  const bar = ease.outExpo(seg(u, 0, 0.45)), reveal = ease.outQuint(seg(u, 0.15, 1));
  const n = lay.rows.length;
  const rows = lay.rows.map((r, i) => {   // the lines come up one after another while the plate opens
    const k = ease.outCubic(seg(u, 0.12 + 0.3 * (i / Math.max(1, n)), 0.5 + 0.3 * (i / Math.max(1, n))));   // never an empty plate
    return { ...r, a: k, dy: (1 - k) * 14 };
  });
  return { vis: 1 - o, reveal, bar, dx: (lay.fromLeft ? -1 : 1) * 24 * o, rows };
}

/** window.film.texts' entries for this plate: each part fully shown from shown to end (bin/vh readcheck, textcheck). */
export function texts(params, lay) {
  const by = new Map();
  for (const r of lay.rows) by.set(r.part, [...(by.get(r.part) || []), r.text]);
  return [...by.values()].map((lines) => ({ text: lines.length > 1 ? lines : lines[0], start: +lay.shown.toFixed(3), end: +lay.end.toFixed(3) }));
}

/** Where the plate puts its ink (engines/CONTRACT.md ui(t)): [{ name, box }], empty while it is not up. */
export function boxes(params, st, lay) {
  return st.vis > 0.05 ? [{ name: "source plate", box: lay.box.map((v, i) => +(v + (i % 2 ? 0 : st.dx)).toFixed(1)) }] : [];
}

/** Canvas painter: the plate (opening from its bar's side), the bar, then the lines (the tag on its accent chip). */
export function canvas(ctx, st, params, lay) {
  if (st.vis <= 0) return;
  const C = opts(params).colors, [x0, y0, x1, y1] = lay.box, w = (x1 - x0) * st.reveal;
  ctx.save();
  ctx.globalAlpha *= st.vis; ctx.translate(st.dx, 0);
  ctx.save();
  ctx.beginPath(); ctx.rect(lay.fromLeft ? x0 : x1 - w, y0, w, y1 - y0); ctx.clip();
  ctx.fillStyle = `rgba(${C.plate},${C.alpha})`; ctx.fillRect(x0, y0, x1 - x0, y1 - y0);
  ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
  for (const r of st.rows) {
    if (r.a <= 0) continue;
    ctx.save(); ctx.globalAlpha *= r.a;
    if (r.chip) { ctx.fillStyle = C.accent; ctx.fillRect(r.chip[0], r.chip[1] + r.dy, r.chip[2], r.chip[3]); }
    ctx.font = r.font; ctx.fillStyle = r.color; ctx.fillText(r.text, r.x, r.y + r.dy); ctx.restore();
  }
  ctx.restore();
  const [bx, by, bw, bh] = lay.bar, h = bh * st.bar;
  ctx.fillStyle = C.accent; ctx.fillRect(bx, by + (bh - h) / 2, bw, h);
  ctx.restore();
}

/**
 * DOM painter. build(root, params, lay) makes the elements once (the plate, its bar and a line a row) inside root,
 * absolutely placed; dom(els, st) moves them. Only transform, opacity and clip-path change.
 */
export function build(root, params, lay) {
  const C = opts(params).colors, doc = root.ownerDocument, [x0, y0, x1, y1] = lay.box;
  const el = (css, parent) => { const d = doc.createElement("div"); d.style.cssText = "position:absolute;" + css; parent.append(d); return d; };
  const wrapEl = el(`left:0;top:0;width:${FRAME.w}px;height:${FRAME.h}px;pointer-events:none;`, root);
  const plate = el(`left:${x0}px;top:${y0}px;width:${x1 - x0}px;height:${y1 - y0}px;background:rgba(${C.plate},${C.alpha});`, wrapEl);
  const rows = lay.rows.map((r) => {
    const box = r.chip ? el(`left:${r.chip[0] - x0}px;top:${r.chip[1] - y0}px;width:${r.chip[2]}px;height:${r.chip[3]}px;background:${C.accent};`, plate) : null;
    const d = el(`left:${r.x - x0}px;top:${r.y - y0}px;transform:translateY(-100%);white-space:nowrap;font:${r.font};line-height:1.18;color:${r.color};`, plate);
    d.textContent = r.text; return { d, box };
  });
  const [bx, by, bw, bh] = lay.bar;
  const bar = el(`left:${bx}px;top:${by}px;width:${bw}px;height:${bh}px;background:${C.accent};transform-origin:50% 50%;`, wrapEl);
  return { wrap: wrapEl, plate, rows, bar, lay };
}
export function dom(els, st) {
  const lay = els.lay;
  els.wrap.style.display = st.vis <= 0 ? "none" : "";
  els.wrap.style.opacity = st.vis.toFixed(4);
  els.wrap.style.transform = `translateX(${st.dx.toFixed(3)}px)`;
  const hide = ((1 - st.reveal) * 100).toFixed(3);
  els.plate.style.clipPath = lay.fromLeft ? `inset(0 ${hide}% 0 0)` : `inset(0 0 0 ${hide}%)`;
  els.bar.style.transform = `scaleY(${st.bar.toFixed(4)})`;
  st.rows.forEach((r, i) => {
    const e = els.rows[i];
    e.d.style.opacity = r.a.toFixed(4); e.d.style.transform = `translateY(calc(-100% + ${r.dy.toFixed(3)}px))`;
    if (e.box) { e.box.style.opacity = r.a.toFixed(4); e.box.style.transform = `translateY(${r.dy.toFixed(3)}px)`; }
  });
}
