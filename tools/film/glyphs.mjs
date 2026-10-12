// glyphs: is every character a page draws in the font it asks for? A font that lacks a character does not fail: the
// browser draws that character in another font on the machine (a fallback), or, when no font has it, as the font's
// empty "missing" glyph (often a blank, so nothing shows). Both are silent. This finds them.
//
// HOOK goes into the page before its own scripts (openFilm's prelude): every fillText and strokeText on a canvas is noted
// with its font and the film time it was drawn at (the host's clock says which), and glyphsDom() adds the DOM's text
// with its computed font. check(film) then asks the browser itself, through the DevTools protocol, which platform font
// draws each character (CSS.getPlatformFontsForNode: the same font matching and fallback the page's text gets), and
// draws each character next to a character no font has (U+10FFFD): the same picture and width means "no font has it".
//
// A character is in its font when the font that draws it is the first family the font asks for: for an @font-face
// family, one of its local() faces (by PostScript or full name; a url() face counts as itself); for a family installed
// on the machine, that family. A generic first family (sans-serif …) asks for no font in particular, so only "no font
// has it" is checked there. Whitespace and invisible format characters are not checked.

export const HOOK = `(() => {
  if (window.__vhGlyphs) return;
  const G = (window.__vhGlyphs = { fonts: new Map(), t: null, chars: 0 });
  const H = window.filmHost;
  if (H && H.time) { const time = H.time; H.time = (t) => { G.t = t; return time(t); }; }   // the film time of the frame being drawn
  // one key per font without its size (40px stands for any): "600 40px \\"Film Sans\\", sans-serif"
  const key = (font) => String(font).replace(/(^|\\s)[\\d.]+(px|pt|pc|em|rem|ex|ch|vw|vh|%|in|cm|mm|q)(\\/\\S+)?(?=\\s)/i, "$1 40px").replace(/\\s+/g, " ").trim();
  const SKIP = /[\\s\\p{Cc}\\p{Cf}\\p{Zs}\\p{Zl}\\p{Zp}\\p{M}]/u;   // whitespace, controls, format characters, combining marks
  G.note = (font, s, via) => {
    s = String(s); if (!s) return;
    const k = key(font); let m = G.fonts.get(k);
    if (!m) G.fonts.set(k, (m = new Map()));
    for (const ch of s) {
      if (SKIP.test(ch)) continue;
      const had = m.get(ch);   // first seen while drawing a frame, when it can be (a page's ready draws without a film time)
      if (had ? had[0] === null && G.t !== null : G.chars < 50000) { if (!had) G.chars++; m.set(ch, [G.t, s.length > 60 ? s.slice(0, 59) + "…" : s, via]); }
    }
  };
  for (const C of [window.CanvasRenderingContext2D, window.OffscreenCanvasRenderingContext2D]) {
    if (!C) continue;
    for (const op of ["fillText", "strokeText"]) {
      const orig = C.prototype[op];
      C.prototype[op] = function (s, ...a) { try { G.note(this.font, s, "canvas"); } catch (e) { /* never in the way of drawing */ } return orig.call(this, s, ...a); };
    }
  }
})();`;

// the DOM's text with its computed font: only what is laid out now (display: none is left out), or all of it inside
// a HyperFrames composition (its clips are hidden while they are off)
const DOM = `((all) => {
  const G = window.__vhGlyphs; if (!G || !document.body) return 0;
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n, k = 0;
  while ((n = w.nextNode())) {
    const el = n.parentElement, s = n.nodeValue;
    if (!el || !/\\S/.test(s) || el.closest("script, style, noscript, template, #__vhglyphs")) continue;
    if (!(all && el.closest("[data-composition-id]")) && !el.getClientRects().length) continue;
    const cs = getComputedStyle(el), tt = cs.textTransform;
    // spelled as a canvas spells its font, so the same font from both is one entry: no "normal", no weight 400
    G.note((cs.fontStyle !== "normal" ? cs.fontStyle + " " : "") + (cs.fontWeight !== "400" ? cs.fontWeight + " " : "") + "40px " + cs.fontFamily, tt === "uppercase" ? s.toUpperCase() : tt === "lowercase" ? s.toLowerCase() : s, "dom"); k++;
  }
  return k;
})`;

// in the page: one element per font with all its characters, one per character, the @font-face rules and their state,
// and the characters that draw exactly like U+10FFFD (no font has them)
const PROBE = `(async () => {
  const G = window.__vhGlyphs; if (!G) return null;
  document.getElementById("__vhglyphs")?.remove();
  const box = document.createElement("div"); box.id = "__vhglyphs";
  box.style.cssText = "position:fixed;left:0;top:0;visibility:hidden;pointer-events:none;white-space:pre;contain:layout";
  const groups = [...G.fonts].map(([font, m], i) => {
    const row = document.createElement("div"); row.style.font = font; row.dataset.g = i; box.appendChild(row);
    const chars = [...m.keys()];
    for (const [j, ch] of chars.entries()) { const sp = document.createElement("span"); sp.textContent = ch; sp.dataset.c = i + ":" + j; row.appendChild(sp); }
    return { font, chars, seen: chars.map((c) => m.get(c)), family: "" };
  });
  document.body.appendChild(box);
  await document.fonts.ready;
  box.getBoundingClientRect();
  [...box.children].forEach((row, i) => { groups[i].family = getComputedStyle(row).fontFamily; });
  // the characters no font has: drawn like a character no font has, at the same width
  const cv = document.createElement("canvas"); cv.width = cv.height = 56;
  const x = cv.getContext("2d", { willReadFrequently: true });
  const pic = (font, ch) => { x.clearRect(0, 0, 56, 56); x.font = font; x.textBaseline = "middle"; x.fillStyle = "#000"; x.fillText(ch, 4, 28);
    const d = x.getImageData(0, 0, 56, 56).data; let h = 0; for (let i = 3; i < d.length; i += 4) h = (Math.imul(h, 31) + d[i]) | 0; return h + ":" + x.measureText(ch).width.toFixed(2); };
  for (const g of groups) { const none = pic(g.font, "\\u{10FFFD}"); g.tofu = g.chars.filter((c) => pic(g.font, c) === none); }
  const faces = [];
  const rules = (sheet) => { try { return [...sheet.cssRules]; } catch (e) { return []; } };
  const walk = (list) => { for (const r of list) { if (r instanceof CSSFontFaceRule) faces.push({ family: r.style.getPropertyValue("font-family"), weight: r.style.getPropertyValue("font-weight") || "400", style: r.style.getPropertyValue("font-style") || "normal", src: r.style.getPropertyValue("src") }); else if (r.cssRules) walk([...r.cssRules]); } };
  for (const sh of document.styleSheets) walk(rules(sh));
  const status = [...document.fonts].map((f) => ({ family: f.family, weight: String(f.weight), style: f.style, status: f.status }));
  return { groups, faces, status };
})()`;

const GENERIC = new Set(["serif", "sans-serif", "monospace", "cursive", "fantasy", "system-ui", "ui-serif", "ui-sans-serif", "ui-monospace", "ui-rounded", "emoji", "math", "fangsong", "-apple-system", "blinkmacsystemfont"]);
const norm = (s) => String(s || "").replace(/^\s*["']|["']\s*$/g, "").toLowerCase().replace(/[\s_-]/g, "");
// a platform font's name is one of the names asked for, or one of them with style words after it: a variable font's
// instance reports itself as "Noto Sans SC Thin" (NotoSansSC-Thin_ExtraBold) when "Noto Sans SC" was asked for
const STYLE = /^(thin|hairline|extralight|ultralight|light|regular|book|normal|roman|medium|semibold|demibold|bold|extrabold|ultrabold|black|heavy|italic|oblique|w\d|\d+)*$/;
const same = (names, n) => { const x = norm(n); return !!x && [...names].some((w) => w && (x === w || (x.startsWith(w) && STYLE.test(x.slice(w.length))))); };
const families = (list) => (String(list).match(/"[^"]*"|'[^']*'|[^,]+/g) || []).map((f) => f.trim().replace(/^["']|["']$/g, "")).filter(Boolean);
const locals = (src) => [...String(src).matchAll(/local\(\s*(?:"([^"]*)"|'([^']*)'|([^)]*?))\s*\)/g)].map((m) => (m[1] ?? m[2] ?? m[3]).trim());

// collect the DOM's text now (call it after drawing a frame); all: the whole composition, shown or not
export const collectDom = (film, all = false) => film.ev(`${DOM}(${all ? "true" : "false"})`).catch(() => 0);

// check(film, { allow }) → { fonts: [{ font, family, first, expect, chars, fallback: [{ ch, by, seen }], tofu: [{ ch,
// seen }], allowed: [...], missingFace }], chars } where seen = [t, text, via]. allow: platform family names a fallback
// may go to without counting (an emoji font). The page must have run HOOK.
export async function check(film, { allow = [] } = {}) {
  const r = await film.ev(PROBE);
  if (!r) throw new Error("the glyph hook is not in this page (tools/film/glyphs.mjs HOOK)");
  await film.send("DOM.enable"); await film.send("CSS.enable");
  const { root } = await film.send("DOM.getDocument", { depth: 0 });
  const box = await film.send("DOM.querySelector", { nodeId: root.nodeId, selector: "#__vhglyphs" });
  const spans = box.nodeId ? (await film.send("DOM.querySelectorAll", { nodeId: box.nodeId, selector: "span" })).nodeIds : [];
  const allowed = new Set(allow.map(norm));
  const out = [];
  for (const [i, g] of r.groups.entries()) {
    const fams = families(g.family), first = fams[0] || "";
    const own = r.faces.filter((f) => norm(f.family) === norm(first));
    let expect = null, custom = false, missingFace = false;
    if (own.length) {
      expect = new Set(own.flatMap((f) => locals(f.src)).map(norm));
      custom = own.some((f) => /url\(/.test(f.src));
      const tried = r.status.filter((f) => norm(f.family) === norm(first) && f.status !== "unloaded");   // the faces the text asked for
      missingFace = tried.length > 0 && tried.every((f) => f.status === "error");
    } else if (first && !GENERIC.has(first.toLowerCase())) expect = new Set([norm(first)]);
    const mine = (p) => expect && (custom && p.isCustomFont || [p.postScriptName, p.familyName].some((n) => same(expect, n)));
    const tofu = new Set(g.tofu), fallback = [], allowedHere = [];
    if (expect) {
      for (let j = 0; j < g.chars.length; j++) {
        const ch = g.chars[j];
        if (tofu.has(ch)) continue;
        const id = spans[r.groups.slice(0, i).reduce((n, x) => n + x.chars.length, 0) + j];
        if (!id) continue;
        const fonts = (await film.send("CSS.getPlatformFontsForNode", { nodeId: id })).fonts || [];
        if (!fonts.length || fonts.some(mine)) continue;
        const by = fonts[0];
        (allowed.has(norm(by.familyName)) ? allowedHere : fallback).push({ ch, by: `${by.familyName}${by.postScriptName && by.postScriptName !== by.familyName ? ` (${by.postScriptName})` : ""}`, seen: g.seen[j] });
      }
    }
    out.push({ font: g.font, family: g.family, first, expect: expect ? [...expect] : null, chars: g.chars.length, missingFace,
      fallback, tofu: g.chars.map((ch, j) => [ch, j]).filter(([ch]) => tofu.has(ch)).map(([ch, j]) => ({ ch, seen: g.seen[j] })), allowed: allowedHere,
      all: g.chars.join("") });
  }
  await film.ev(`document.getElementById("__vhglyphs")?.remove()`).catch(() => {});
  return { fonts: out, chars: out.reduce((n, f) => n + f.chars, 0) };
}

const code = (ch) => "U+" + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, "0");
const at = (seen) => (seen && seen[0] !== null && seen[0] !== undefined ? ` at ${(+seen[0]).toFixed(2)} s` : "");
const eg = (seen) => (seen ? ` (e.g. "${seen[1]}"${at(seen)}${seen[2] === "dom" ? ", DOM" : ""})` : "");
const list = (xs, n = 24) => xs.slice(0, n).join(" ") + (xs.length > n ? ` … (${xs.length})` : "");

// the report as lines, and whether any character is out of its font: [lines, bad]
export function report(res) {
  const lines = [];
  let bad = false;
  for (const f of res.fonts.slice().sort((a, b) => (b.fallback.length + b.tofu.length) - (a.fallback.length + a.tofu.length) || a.font.localeCompare(b.font))) {
    const name = f.font.replace(/(^| )40px /, "$1").trim();
    if (f.missingFace) { bad = true; lines.push(`✗ ${name}: none of the faces of "${f.first}" is on this machine, so all ${f.chars} characters drawn in it fell back`); }
    if (f.tofu.length) {
      bad = true;
      lines.push(`✗ ${name}: no font on this machine has ${f.tofu.length} character${f.tofu.length > 1 ? "s" : ""}, drawn as the empty "missing" glyph: ` +
        list(f.tofu.map((x) => `${x.ch} ${code(x.ch)}`), 12) + eg(f.tofu[0].seen));
    }
    if (f.fallback.length && !f.missingFace) {
      bad = true;
      const by = new Map();
      for (const x of f.fallback) by.set(x.by, [...(by.get(x.by) || []), x]);
      for (const [font, xs] of by) lines.push(`✗ ${name}: ${xs.length} character${xs.length > 1 ? "s" : ""} not in "${f.first}", drawn in ${font}: ${list(xs.map((x) => x.ch))}${eg(xs[0].seen)}`);
    }
    if (f.allowed.length) lines.push(`  ${name}: ${f.allowed.length} character${f.allowed.length > 1 ? "s" : ""} in an allowed fallback (${[...new Set(f.allowed.map((x) => x.by))].join(", ")}): ${list(f.allowed.map((x) => x.ch))}`);
    if (!f.missingFace && !f.tofu.length && !f.fallback.length) lines.push(`✓ ${name}: ${f.chars} character${f.chars > 1 ? "s" : ""}${f.expect ? `, all in "${f.first}"` : ` (a generic family: only checked that some font has them)`}`);
  }
  return [lines, bad];
}

// the results of several checks of one film (bin/vh render's workers, each with its own frames) as one
export function merge(results) {
  const by = new Map();
  for (const r of results) for (const f of r.fonts) {
    const m = by.get(f.font);
    if (!m) { by.set(f.font, { ...f, fallback: [...f.fallback], tofu: [...f.tofu], allowed: [...f.allowed] }); continue; }
    const add = (list, xs) => { for (const x of xs) if (!list.some((y) => y.ch === x.ch)) list.push(x); };
    add(m.fallback, f.fallback); add(m.tofu, f.tofu); add(m.allowed, f.allowed);
    m.missingFace = m.missingFace || f.missingFace;
    m.all = [...new Set([...m.all, ...f.all])].join(""); m.chars = [...m.all].length;
  }
  const fonts = [...by.values()];
  return { fonts, chars: fonts.reduce((n, f) => n + f.chars, 0) };
}
