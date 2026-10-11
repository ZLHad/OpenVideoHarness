// frames: still frames, a range or a strip of every frame, drawn from a page's source through the page contract
// (engines/CONTRACT.md), for any engine that is a web page: ClaudeAnimationBase (studio.html), a page that writes
// window.film, and HyperFrames compositions. No render and no video encode: each frame is the page drawn at t and
// captured as a lossless PNG.
//
// usage: node tools/film/frames.mjs <project | page.html> --browser <chrome>
//          (--at t[,t…] | --range a:b[:step] | --strip a:b) [--fps 30] [--cols 6] [--cell 320]
//          [--out dir] [--size WxH] [--dpr 1] [--real-clock] [--soft-gl] [--runtime auto|on|off] [--timeout 600]
//        (bin/vh frames finds the browser: CHROME_PATH, HyperFrames' chrome-headless-shell, then Chrome or Chromium)
//
//   --at 1.2,3.4        the frames at these seconds (to the millisecond)
//   --range 2:4[:0.5]   every 0.5 s (default 1 s) from 2 s to 4 s, the end left out when it is the film's end
//   --strip 2:2.5       every frame (--fps, default 30) from 2 s up to 2.5 s, and one picture of them all
//                       (--cols per row, each --cell px wide), left to right, top to bottom. When a falls on a frame,
//                       each is drawn at k / fps exactly, the t bin/vh render draws (an engine that floors t would
//                       draw another picture at a t rounded to the millisecond)
//   --size 1080x1920    the viewport; without it, HyperFrames' data-width and data-height, else the page's meta viewport,
//                       else 1920x1080. A page's window.film.width and height win over all of these
//   --dpr 2             the device pixel ratio: twice the pixels for a page that sizes its canvas by devicePixelRatio, as
//                       the contract asks (4K for a 1920x1080 page); a fixed-size canvas is only scaled up
//   --real-clock        no clock pinning (tools/film/clock.js), only window.filmHost: to see what a page does without it
//   --runtime           HyperFrames' runtime for a composition: auto (when it writes no window.film or window.__vh), on, off
//
// A project folder means its film.html, else index.html, else studio.html; the page is served from its own folder.
// Writes <out>/<page>-t<seconds>.png (out defaults to <project>/out/frames) and, for --strip, <out>/<page>-strip-<a>-<b>.jpg
// with the frames in a folder beside it. Exit: 0 drawn · 1 a frame threw, or the page reported an error or a failed
// load (while loading, while drawing, or just after the last frame) · 2 could not draw (no page, no window.film, not
// ready, no browser, a time outside the film).
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { openFilm } from "./host.mjs";

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP); process.exit(argv.length ? 0 : 2); }
let film = null;
// every way out closes the browser (and its profile folder) first
const finish = async (code, msg) => {
  if (msg) console.error("frames: " + msg);
  if (film) { const f = film; film = null; try { await f.close(); } catch { /* gone */ } }
  process.exit(code);
};
const die = (msg) => finish(2, msg);
process.on("unhandledRejection", (e) => finish(2, (e && e.message) || String(e)));
const o = { fps: 30, cols: 6, cell: 320, dpr: 1, timeout: 600, runtime: "auto" };
let target = null, at = null, range = null, strip = null, out = null, size = null;
const r3 = (t) => Math.round(t * 1000) / 1000;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], [k, inline] = a.startsWith("--") && a.includes("=") ? [a.slice(0, a.indexOf("=")), a.slice(a.indexOf("=") + 1)] : [a, undefined];
  const val = () => { const v = inline !== undefined ? inline : argv[++i]; if (v === undefined) bail(`${k} needs a value`); return v; };
  const num = (v, what, min = 0) => { const x = Number(v); if (v === "" || !Number.isFinite(x) || x < min) bail(`${what}: ${v === "" ? "(empty)" : v} is not a number ≥ ${min}`); return x; };
  if (k === "--at") { at = val().split(",").map((v) => r3(num(v.trim(), "--at"))); }
  else if (k === "--range") range = val().split(":").map((v) => num(v, "--range"));
  else if (k === "--strip") strip = val().split(":").map((v) => num(v, "--strip"));
  else if (["--fps", "--cols", "--cell", "--timeout"].includes(k)) o[k.slice(2)] = num(val(), k, 1);
  else if (k === "--dpr") o.dpr = num(val(), k, 0.25);
  else if (k === "--out") out = val();
  else if (k === "--size") { const m = val().match(/^(\d+)x(\d+)$/); if (!m || !+m[1] || !+m[2]) bail("--size: write it as 1920x1080"); size = [+m[1], +m[2]]; }
  else if (k === "--browser") o.browser = val();
  else if (k === "--real-clock") o.realClock = true;
  else if (k === "--soft-gl") o.softGl = true;
  else if (k === "--runtime") { o.runtime = val(); if (!["auto", "on", "off"].includes(o.runtime)) bail("--runtime: auto, on or off"); }
  else if (k.startsWith("-")) bail(`unknown option ${k} (-h for the options)`);
  else if (target) bail(`one project or page, got ${target} and ${a}`);
  else target = a;
}
// argument errors come before any browser: exit at once
function bail(msg) { console.error("frames: " + msg); process.exit(2); }
if (!target) bail("which project or page? (-h for the usage)");
if (!o.browser) bail("no browser: pass --browser <chrome>, or run it as bin/vh frames");
if ([at, range, strip].filter(Boolean).length !== 1) bail("say which frames: one of --at, --range or --strip");
if (at && !at.length) bail("--at needs at least one time");
if (range && (range.length < 2 || range.length > 3 || range[1] < range[0] || (range.length === 3 && !(range[2] > 0)))) bail("--range a:b[:step], b ≥ a, step > 0");
if (strip && (strip.length !== 2 || strip[1] <= strip[0])) bail("--strip a:b, b > a");

let times = at ? [...new Set(at)] : null;
if (range) { const step = range[2] || 1; times = []; for (let k = 0; range[0] + k * step <= range[1] + 1e-9; k++) times.push(r3(range[0] + k * step)); }
if (strip) {   // on render's frame grid when the strip starts on it: t = k / fps, not rounded
  const n = Math.max(1, Math.round((strip[1] - strip[0]) * o.fps)), f0 = strip[0] * o.fps, on = Math.abs(f0 - Math.round(f0)) < 1e-6;
  times = Array.from({ length: n }, (_, k) => (on ? (Math.round(f0) + k) / o.fps : strip[0] + k / o.fps));
}
if (times.length > 2000) bail(`${times.length} frames is a render, not a check: use a shorter span`);

const watchdog = setTimeout(() => finish(2, `stopped after ${o.timeout} s (--timeout); a frame function that never returns?`), o.timeout * 1000);
watchdog.unref();
try { film = await openFilm(target, { ...o, width: size && size[0], height: size && size[1] }); } catch (e) { await die(e.message); }
const stem = path.basename(film.page, path.extname(film.page));
const outDir = path.resolve(out || path.join(film.root, "out", "frames"));
try { fs.mkdirSync(outDir, { recursive: true }); } catch (e) { await die(`cannot write ${outDir}: ${e.message}`); }
const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
console.log(`frames: ${rel(film.page)} · ${film.kind === "film" ? "window.film" : film.kind === "__vh" ? "window.__vh" : "HyperFrames runtime"} · ` +
  `${film.width}x${film.height}${o.dpr !== 1 ? ` @${o.dpr}x` : ""} · ${film.duration ? film.duration + " s" : "no duration"} · ${film.version}`);
let failed = 0;
for (const p of film.loadProblems) { console.log(`  while loading: ${p}`); failed++; }
// the film's own end is not a frame (0 ≤ t < duration): a --range that reaches it leaves it out
if (range && film.duration > 0) times = times.filter((t) => t < film.duration || t !== r3(range[1]));
const bad = times.filter((t) => t < 0 || (film.duration > 0 && t >= film.duration));
if (bad.length) await die(`${bad.join(", ")} s: outside the film (0 up to ${film.duration} s)`);

const readers = new Map(), written = [];
const name = (t) => `${stem}-t${t.toFixed(3).padStart(8, "0")}.png`;
const at3 = (t) => +t.toFixed(3);   // a strip's t is k / fps exactly; messages show it to the millisecond
const stripDir = strip ? path.join(outDir, `${stem}-strip-${strip[0]}-${strip[1]}`) : null;
if (stripDir) { fs.rmSync(stripDir, { recursive: true, force: true }); fs.mkdirSync(stripDir); }
for (const t of times) {
  const t0 = Date.now();
  try {
    const { png, touched } = await film.frame(t);
    // strip frames are numbered by the frames written, so a failed one leaves no gap for the picture to stop at
    const f = stripDir ? path.join(stripDir, `${String(written.length + 1).padStart(4, "0")}.png`) : path.join(outDir, name(t));
    fs.writeFileSync(f, png); written.push(f);
    // Math.random only: libraries read the other clocks themselves (HyperFrames' runtime reads Date while it seeks)
    if (touched.includes("Math.random")) readers.set("Math.random", [...(readers.get("Math.random") || []), t]);
    const later = film.problems();
    if (later.length) { failed++; console.log(`  t=${at3(t)} s: ${later.join(" | ")}`); }
    if (!stripDir) console.log(`  ${rel(f)}  (${Date.now() - t0} ms)`);
  } catch (e) { failed++; console.log(`  t=${at3(t)} s: ${e.message}`); }
}
const late = await film.lateProblems();
if (late.length) { failed++; console.log(`  just after the last frame (an error a frame left behind, charged to no frame): ${late.join(" | ")}`); }
if (stripDir && written.length) {
  const cols = Math.min(o.cols, written.length), rows = Math.ceil(written.length / cols), pic = path.join(outDir, `${stem}-strip-${strip[0]}-${strip[1]}.jpg`);
  const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-framerate", "1", "-i", path.join(stripDir, "%04d.png"),
    "-vf", `scale=${o.cell}:-2,tile=${cols}x${rows}:padding=4:color=0x202020`, "-frames:v", "1", "-q:v", "3", pic], { encoding: "utf8" });
  if (r.status !== 0) { console.log(`  the strip picture failed (ffmpeg): ${(r.stderr || r.error || "").toString().trim()}`); failed++; }
  else console.log(`  ${rel(pic)}: ${written.length} frames at ${o.fps} fps, ${strip[0]}–${strip[1]} s, ${cols} a row (the frames are in ${rel(stripDir)}/)`);
}
for (const [c, ts] of readers) {
  console.log(`  warning: the page read ${c} while drawing (${ts.length} frame${ts.length > 1 ? "s" : ""}, first at ${at3(ts[0])} s). Hard rule 1: take ` +
    `randomness from a seeded hash; here the host held it at t, so the frames still agree, but a renderer that does not will not.`);
}
console.log(`frames: ${written.length} of ${times.length} drawn${failed ? `, ${failed} problem${failed > 1 ? "s" : ""}` : ""}`);
await finish(failed ? 1 : written.length ? 0 : 2);
