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
// family, one of its local() faces (by PostScript or full name); for a url() face or one added through the FontFace API,
// the web font that family alone draws with (probed on its own); for a family installed on the machine, that family. A
// character drawn by a family named later in the same stack ("Helvetica Neue", "PingFang SC") went where the stack sends
// it: said, and a failure only with strict. A generic first family (sans-serif …) asks for no font in particular, so only
// "no font has it" is checked there. Whitespace, invisible format characters and combining marks are not checked.

export const HOOK = `(() => {
  if (window.__vhGlyphs) return;
  const G = (window.__vhGlyphs = { fonts: new Map(), t: null, chars: 0, capped: false });
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
      if (!had && G.chars >= 50000) { G.capped = true; continue; }   // more distinct characters than any film has: said in the report
      if (!had || (had[0] === null && G.t !== null)) { if (!had) G.chars++; m.set(ch, [G.t, s.length > 60 ? s.slice(0, 59) + "…" : s, via]); }
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
    if (!el || !/\\S/.test(s) || el.closest("script, style, noscript, template, vh-glyphs")) continue;
    if (!(all && el.closest("[data-composition-id]")) && !el.getClientRects().length) continue;
    const cs = getComputedStyle(el), tt = cs.textTransform;
    // spelled as a canvas spells its font, so the same font from both is one entry: no "normal", no weight 400
    G.note((cs.fontStyle !== "normal" ? cs.fontStyle + " " : "") + (cs.fontWeight !== "400" ? cs.fontWeight + " " : "") + "40px " + cs.fontFamily, tt === "uppercase" ? s.toUpperCase() : tt === "lowercase" ? s.toLowerCase() : s, "dom"); k++;
  }
  return k;
})`;

// in the page: for each font, one element per character (custom elements with every property set inline and !important,
// so no rule of the page reaches them), and one with all its characters in the first family alone (which web font that
// family is); the @font-face rules and their state; and the characters that draw exactly like U+10FFFD (no font has them)
const PROBE = `(async () => {
  const G = window.__vhGlyphs; if (!G) return null;
  document.querySelector("vh-glyphs")?.remove();
  const box = document.createElement("vh-glyphs");
  box.style.cssText = "all: initial !important; display: block !important; position: fixed !important; left: 0 !important; top: 0 !important; visibility: hidden !important; pointer-events: none !important; contain: layout !important";
  const css = (font) => \`all: initial !important; display: block !important; white-space: pre !important; font: \${font} !important\`;
  const first = (font) => { const m = font.match(/^(.*?\\d+px\\s+)("[^"]*"|'[^']*'|[^,]+)/); return m ? m[1] + m[2] : font; };
  const wait = (p, ms) => Promise.race([p, new Promise((ok) => setTimeout(ok, ms))]);
  const groups = [...G.fonts].map(([font, m], i) => {
    const chars = [...m.keys()];
    const row = document.createElement("vh-g"); row.style.cssText = css(font); row.dataset.g = i; box.appendChild(row);
    for (const ch of chars) { const c = document.createElement("vh-c"); c.style.cssText = "all: inherit !important; display: inline !important"; c.textContent = ch; row.appendChild(c); }
    const solo = document.createElement("vh-s"); solo.style.cssText = css(first(font)); solo.dataset.g = i; solo.textContent = chars.join(""); box.appendChild(solo);
    return { font, solo: first(font), chars, seen: chars.map((c) => m.get(c)), family: "" };
  });
  document.body.appendChild(box);
  box.getBoundingClientRect();   // laid out first, so every load the probe needs has started; then wait for them (not for ever)
  await wait(Promise.all(groups.flatMap((g) => [g.font, g.solo].map((f) => document.fonts.load(f, g.chars.join("")).catch(() => null)))), 15000);
  await wait(document.fonts.ready, 15000);
  box.getBoundingClientRect();
  [...box.querySelectorAll("vh-g")].forEach((row, i) => { groups[i].family = getComputedStyle(row).fontFamily; });
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
  return { groups, faces, status, capped: G.capped };
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

// check(film, { allow, strict }) → { fonts: [{ font, family, first, expect, chars, fallback: [{ ch, by, seen }], later:
// [...], tofu: [{ ch, seen }], allowed: [...], missingFace }], chars, capped } where seen = [t, text, via]. allow: platform
// family names a fallback may go to without counting (an emoji font); strict: a character drawn by a later family of its
// stack counts as a fallback too. The page must have run HOOK.
export async function check(film, { allow = [], strict = false } = {}) {
  const r = await film.ev(PROBE);
  if (!r) throw new Error("the glyph hook is not in this page (tools/film/glyphs.mjs HOOK)");
  await film.send("DOM.enable"); await film.send("CSS.enable");
  const { root } = await film.send("DOM.getDocument", { depth: 0 });
  const box = await film.send("DOM.querySelector", { nodeId: root.nodeId, selector: "vh-glyphs" });
  const pick = async (sel) => (box.nodeId ? (await film.send("DOM.querySelectorAll", { nodeId: box.nodeId, selector: sel })).nodeIds : []);
  const cells = await pick("vh-c"), solos = await pick("vh-s");
  const platform = async (id) => (id ? (await film.send("CSS.getPlatformFontsForNode", { nodeId: id })).fonts || [] : []);
  const allowed = new Set(allow.map(norm));
  const name = (p) => `${p.familyName}${p.postScriptName && p.postScriptName !== p.familyName ? ` (${p.postScriptName})` : ""}`;
  // what a family is: its local() names, whether it has url() or FontFace faces, whether all its faces it tried failed
  const kind = (fam) => {
    if (!fam || GENERIC.has(fam.toLowerCase())) return null;
    const own = r.faces.filter((f) => norm(f.family) === norm(fam)), st = r.status.filter((f) => norm(f.family) === norm(fam));
    if (!own.length && !st.length) return { names: new Set([norm(fam)]), web: false, missing: false };   // installed on the machine
    const tried = st.filter((f) => f.status !== "unloaded");
    return { names: new Set(own.flatMap((f) => locals(f.src)).map(norm)), web: own.some((f) => /url\(/.test(f.src)) || st.length > own.length,
      missing: tried.length > 0 && tried.every((f) => f.status === "error") };
  };
  const out = [];
  let at = 0;
  for (const [i, g] of r.groups.entries()) {
    const ids = cells.slice(at, at + g.chars.length); at += g.chars.length;
    const fams = families(g.family), first = fams[0] || "", k1 = kind(first);
    // a web font's own name is in the font file: the web fonts the first family alone draws with are that family
    const webNames = new Set();
    if (k1 && k1.web) for (const p of await platform(solos[i])) if (p.isCustomFont) webNames.add(p.postScriptName || p.familyName);
    const isFirst = (p) => !!k1 && ([p.postScriptName, p.familyName].some((n) => same(k1.names, n)) || (p.isCustomFont && webNames.has(p.postScriptName || p.familyName)));
    const laterKinds = fams.slice(1).map(kind).filter(Boolean);
    const isLater = (p) => laterKinds.some((k) => [p.postScriptName, p.familyName].some((n) => same(k.names, n)) || (k.web && p.isCustomFont && !webNames.has(p.postScriptName || p.familyName)));
    const tofu = new Set(g.tofu), fallback = [], later = [], allowedHere = [];
    if (k1) {
      for (let j = 0; j < g.chars.length; j++) {
        const ch = g.chars[j];
        if (tofu.has(ch)) continue;
        const fonts = await platform(ids[j]);
        if (!fonts.length || fonts.some(isFirst)) continue;
        const by = fonts[0], x = { ch, by: name(by), seen: g.seen[j] };
        if (allowed.has(norm(by.familyName))) allowedHere.push(x);
        else if (!strict && !k1.missing && fonts.some(isLater)) later.push(x);
        else fallback.push(x);
      }
    }
    out.push({ font: g.font, family: g.family, first, expect: k1 ? [...k1.names, ...webNames] : null, chars: g.chars.length, missingFace: !!(k1 && k1.missing),
      fallback, later, tofu: g.chars.map((ch, j) => [ch, j]).filter(([ch]) => tofu.has(ch)).map(([ch, j]) => ({ ch, seen: g.seen[j] })), allowed: allowedHere,
      all: g.chars.join("") });
  }
  await film.ev(`document.querySelector("vh-glyphs")?.remove()`).catch(() => {});
  return { fonts: out, chars: out.reduce((n, f) => n + f.chars, 0), capped: !!r.capped };
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
    if (f.missingFace) { bad = true; lines.push(`✗ ${name}: "${f.first}" could not be loaded (no local() face of it on this machine, or its url() failed), so all ${f.chars} characters drawn in it fell back`); }
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
    if (f.later.length) {
      const by = [...new Set(f.later.map((x) => x.by))];
      lines.push(`  ${name}: ${f.later.length} character${f.later.length > 1 ? "s" : ""} not in "${f.first}", drawn by a later family of the stack, as written (${by.join(", ")}): ${list(f.later.map((x) => x.ch))}`);
    }
    if (f.allowed.length) lines.push(`  ${name}: ${f.allowed.length} character${f.allowed.length > 1 ? "s" : ""} in an allowed fallback (${[...new Set(f.allowed.map((x) => x.by))].join(", ")}): ${list(f.allowed.map((x) => x.ch))}`);
    if (!f.missingFace && !f.tofu.length && !f.fallback.length) lines.push(`✓ ${name}: ${f.chars} character${f.chars > 1 ? "s" : ""}` +
      (!f.expect ? " (a generic family: only checked that some font has them)" : f.later.length ? ` in its stack` : `, all in "${f.first}"`));
  }
  if (res.capped) lines.push("! over 50000 distinct characters: the ones after that were not noted, so not checked");
  return [lines, bad];
}

// the results of several checks of one film (bin/vh render's workers, each with its own frames) as one
export function merge(results) {
  const by = new Map();
  for (const r of results) for (const f of r.fonts) {
    const m = by.get(f.font);
    if (!m) { by.set(f.font, { ...f, fallback: [...f.fallback], later: [...f.later], tofu: [...f.tofu], allowed: [...f.allowed] }); continue; }
    const add = (list, xs) => { for (const x of xs) if (!list.some((y) => y.ch === x.ch)) list.push(x); };
    add(m.fallback, f.fallback); add(m.later, f.later); add(m.tofu, f.tofu); add(m.allowed, f.allowed);
    m.missingFace = m.missingFace || f.missingFace;
    m.all = [...new Set([...m.all, ...f.all])].join(""); m.chars = [...m.all].length;
  }
  const fonts = [...by.values()];
  return { fonts, chars: fonts.reduce((n, f) => n + f.chars, 0), capped: results.some((r) => r.capped) };
}
