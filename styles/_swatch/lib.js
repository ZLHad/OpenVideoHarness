// lib.js — what style swatch scenes receive as `lib`: the component library (components/lib, the one library of the repo's
// motion and texture helpers; components/README.md) and the swatch's own content spec below. render.sh copies
// components/ into each stage beside this file. Everything is a pure function of its arguments (t, seed, options);
// caches only memoise deterministic results, so frame N renders the same whether it is drawn first, last or alone.
// Scenes receive this module as `lib`; see README.md for the API table.
import { safeBoxes, setFrame } from "./components/lib/core.js";
export * from "./components/lib/index.js";

// ───────────────────────── the swatch: frame and content spec ─────────────────────────
// render.sh writes the spec the style's tokens.json asks for into the staged page (window.__swatchSpec; tools/styles.py
// spec). Without it, and for every spec-1 swatch, these are the original 5 s at 1920×1080.
const S = (typeof window !== "undefined" && window.__swatchSpec) || {};
export const W = S.w || 1920, H = S.h || 1080, FPS = 30, DUR = S.dur || 5, FRAMES = Math.round(DUR * FPS), POSTER_T = S.poster ?? 3.0;
export const SPEC_VERSION = S.spec || 1;
export const PORTRAIT = H > W, ASPECT = PORTRAIT ? "portrait" : "landscape";
if (W !== 1920 || H !== 1080) setFrame({ w: W, h: H, fps: FPS });   // anchor() and slots() then default to this frame
/** Spec 1's content spec (seconds): every 5 s swatch tells the same thing, so the gallery compares like with like. */
export const SPEC = { establish: [0, 0.8], title: [0.8, 2.6], motif: [2.0, 4.0], outro: [4.0, 5.0], poster: 3.0 };
/** Spec 2's four beats, [start, end] in seconds, scaled to DUR (or as tokens.json's swatch.beats sets them):
 *  world: the world stands, palette and texture at a glance · signature: the move or transition this style is known by ·
 *  type: a title and one caption line at real sizes (TYPE) · close: it settles, and the last frame leads back to the first. */
export const BEATS = S.beats || null;
/** Spec 2's type beat at the sizes a film would use (playbook/03-motion-design.md §4: desktop for landscape, phone for
 *  portrait), px on this canvas: the title, a caption line, and the smallest label. */
export const TYPE = PORTRAIT ? { title: 130, caption: 65, label: 44 } : { title: 96, caption: 48, label: 44 };
/** The caption line every spec-2 swatch sets under its title, so the gallery compares type like with like. */
export const CAPTION_EN = "One piece of code, edited into a film.";
export const CAPTION_ZH = "一份代码，改到成片。";   // short enough to be read once in the type beat, one line at 65 px in portrait
export const TITLE_EN = "Every frame is code.";
export const TITLE_ZH = "每一帧，都是代码。";
/** The 3-element motif, left to right: outline → storyboard → draft. */
export const MOTIF = [
  { key: "outline", en: "Outline", zh: "大纲" },
  { key: "storyboard", en: "Storyboard", zh: "分镜" },
  { key: "draft", en: "Draft", zh: "初版" },
];
/** action: EBU R95 90 % graphics-safe (text ≥ 96 px from the sides, ≥ 54 px from top/bottom). title: 80 % title-safe. */
export const SAFE = safeBoxes(W, H);
