// lib.js — what style swatch scenes receive as `lib`: the component library (components/lib, the one library of the repo's
// motion and texture helpers; components/README.md) and the swatch's own content spec below. render.sh copies
// components/ into each stage beside this file. Everything is a pure function of its arguments (t, seed, options);
// caches only memoise deterministic results, so frame N renders the same whether it is drawn first, last or alone.
// Scenes receive this module as `lib`; see README.md for the API table.
import { safeBoxes } from "./components/lib/core.js";
export * from "./components/lib/index.js";

// ───────────────────────── the swatch: frame and content spec ─────────────────────────
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
/** action: EBU R95 90 % graphics-safe (text ≥ 96 px from the sides, ≥ 54 px from top/bottom). title: 80 % title-safe. */
export const SAFE = safeBoxes(W, H);
