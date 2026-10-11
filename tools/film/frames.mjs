// frames: still frames, a range or a strip of every frame, drawn from a page's source through the page contract
// (engines/CONTRACT.md), for any engine that is a web page: the self-built canvas engine, ClaudeAnimationBase (studio.html)
// and HyperFrames compositions. No render and no video encode: each frame is the page drawn at t and captured as a
// lossless PNG.
//
// usage: node tools/film/frames.mjs <project | page.html> --browser <chrome>
//          (--at t[,t…] | --range a:b[:step] | --strip a:b) [--fps 30] [--cols 6] [--cell 320]
//          [--out dir] [--size WxH] [--dpr 1] [--real-clock] [--soft-gl] [--runtime auto|on|off] [--timeout 600]
//        (bin/vh frames finds the browser: CHROME_PATH, HyperFrames' chrome-headless-shell, then Chrome or Chromium)
//
//   --at 1.2,3.4        the frames at these seconds
//   --range 2:4[:0.5]   every 0.5 s (default 1 s) from 2 s to 4 s
//   --strip 2:2.5       every frame (--fps, default 30) from 2 s up to 2.5 s, and one picture of them all
//                       (--cols per row, each --cell px wide), left to right, top to bottom
//   --size 1080x1920    the viewport, when the page does not say it (its meta viewport, HyperFrames' data-width and
//                       data-height, or window.film.width and height; else 1920x1080); --dpr 2 draws at twice the
//                       pixels (4K for a 1920x1080 page)
//   --real-clock        no clock pinning (tools/film/clock.js), only window.filmHost: to see what a page does without it
//   --runtime           HyperFrames' runtime for a composition: auto (when it writes no window.film or window.__vh), on, off
//
// A project folder means its film.html, else index.html, else studio.html. Writes <out>/<page>-t<seconds>.png (out
// defaults to <project>/out/frames) and, for --strip, <out>/<page>-strip-<a>-<b>.jpg. Exit: 0 drawn · 1 a frame threw,
// or the page reported an error while drawing · 2 could not draw (no page, no window.film, not ready, no browser,
// a time outside the film).
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { HostError, openFilm } from "./host.mjs";

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP); process.exit(argv.length ? 0 : 2); }
const die = (msg) => { console.error("frames: " + msg); process.exit(2); };
const o = { fps: 30, cols: 6, cell: 320, dpr: 1, timeout: 600, runtime: "auto" };
let target = null, at = null, range = null, strip = null, out = null, size = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], [k, inline] = a.startsWith("--") && a.includes("=") ? [a.slice(0, a.indexOf("=")), a.slice(a.indexOf("=") + 1)] : [a, undefined];
  const val = () => { const v = inline !== undefined ? inline : argv[++i]; if (v === undefined) die(`${k} needs a value`); return v; };
  const num = (v, what, min = 0) => { const x = Number(v); if (!Number.isFinite(x) || x < min) die(`${what}: ${v} is not a number ≥ ${min}`); return x; };
  if (k === "--at") at = val().split(",").filter(Boolean).map((v) => num(v, "--at"));
  else if (k === "--range") range = val().split(":").map((v) => num(v, "--range"));
  else if (k === "--strip") strip = val().split(":").map((v) => num(v, "--strip"));
  else if (["--fps", "--cols", "--cell", "--dpr", "--timeout"].includes(k)) o[k.slice(2)] = num(val(), k, k === "--dpr" ? 0.25 : 1);
  else if (k === "--out") out = val();
  else if (k === "--size") { const m = val().match(/^(\d+)x(\d+)$/); if (!m) die("--size: write it as 1920x1080"); size = [+m[1], +m[2]]; }
  else if (k === "--browser") o.browser = val();
  else if (k === "--real-clock") o.realClock = true;
  else if (k === "--soft-gl") o.softGl = true;
  else if (k === "--runtime") { o.runtime = val(); if (!["auto", "on", "off"].includes(o.runtime)) die("--runtime: auto, on or off"); }
  else if (k.startsWith("-")) die(`unknown option ${k} (-h for the options)`);
  else if (target) die(`one project or page, got ${target} and ${a}`);
  else target = a;
}
if (!target) die("which project or page? (-h for the usage)");
if (!o.browser) die("no browser: pass --browser <chrome>, or run it as bin/vh frames");
if ([at, range, strip].filter(Boolean).length !== 1) die("say which frames: one of --at, --range or --strip");
if (range && (range.length < 2 || range.length > 3 || range[1] < range[0])) die("--range a:b[:step], b ≥ a");
if (strip && (strip.length !== 2 || strip[1] <= strip[0])) die("--strip a:b, b > a");

const r3 = (t) => Math.round(t * 1000) / 1000;
let times = at;
if (range) { const step = range[2] || 1; times = []; for (let t = range[0]; t <= range[1] + 1e-9; t += step) times.push(r3(t)); }
if (strip) { const n = Math.max(1, Math.round((strip[1] - strip[0]) * o.fps)); times = Array.from({ length: n }, (_, k) => r3(strip[0] + k / o.fps)); }
if (times.length > 2000) die(`${times.length} frames is a render, not a check: use a shorter span`);

const watchdog = setTimeout(() => { console.error(`frames: stopped after ${o.timeout} s (--timeout); a frame function that never returns?`); process.exit(2); }, o.timeout * 1000);
watchdog.unref();
let film;
try {
  film = await openFilm(target, { ...o, width: size && size[0], height: size && size[1] });
} catch (e) { die(e.message); }
const stem = path.basename(film.page, path.extname(film.page));
const outDir = path.resolve(out || path.join(film.root, "out", "frames"));
fs.mkdirSync(outDir, { recursive: true });
const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
console.log(`frames: ${rel(film.page)} · ${film.kind === "film" ? "window.film" : film.kind === "__vh" ? "window.__vh" : "HyperFrames runtime"} · ` +
  `${film.width}x${film.height}${o.dpr !== 1 ? ` @${o.dpr}x` : ""} · ${film.duration ? film.duration + " s" : "no duration"} · ${film.version}`);
for (const p of film.loadProblems) console.log(`  while loading: ${p}`);
const bad = times.filter((t) => t < 0 || (film.duration > 0 && t >= film.duration));
if (bad.length) { await film.close(); die(`${bad.join(", ")} s: outside the film (0 to ${film.duration} s)`); }

let failed = 0;
const readers = new Map(), written = [];
const name = (t) => `${stem}-t${t.toFixed(3).padStart(8, "0")}.png`;
const stripDir = strip ? path.join(outDir, `${stem}-strip-${strip[0]}-${strip[1]}`) : null;
if (stripDir) { fs.rmSync(stripDir, { recursive: true, force: true }); fs.mkdirSync(stripDir); }
for (const [i, t] of times.entries()) {
  const t0 = Date.now();
  try {
    const { png, touched } = await film.frame(t);
    const f = stripDir ? path.join(stripDir, `${String(i + 1).padStart(4, "0")}.png`) : path.join(outDir, name(t));
    fs.writeFileSync(f, png); written.push(f);
    // Math.random only: libraries read the clocks themselves (HyperFrames' runtime reads Date while it seeks)
    for (const c of touched.filter((c) => c === "Math.random")) readers.set(c, [...(readers.get(c) || []), t]);
    const later = film.problems();
    if (later.length) { failed++; console.log(`  t=${t} s: ${later.join(" | ")}`); }
    if (!stripDir) console.log(`  ${rel(f)}  (${Date.now() - t0} ms)`);
  } catch (e) { failed++; console.log(`  t=${t} s: ${e.message}`); }
}
await film.close();
if (stripDir && written.length) {
  const cols = Math.min(o.cols, written.length), rows = Math.ceil(written.length / cols), pic = path.join(outDir, `${stem}-strip-${strip[0]}-${strip[1]}.jpg`);
  const r = spawnSync("ffmpeg", ["-v", "error", "-y", "-framerate", "1", "-i", path.join(stripDir, "%04d.png"),
    "-vf", `scale=${o.cell}:-2,tile=${cols}x${rows}:padding=4:color=0x202020`, "-frames:v", "1", "-q:v", "3", pic], { encoding: "utf8" });
  if (r.status !== 0) { console.log(`  the strip picture failed (ffmpeg): ${(r.stderr || r.error || "").toString().trim()}`); failed++; }
  else console.log(`  ${rel(pic)}: ${written.length} frames at ${o.fps} fps, ${strip[0]}–${strip[1]} s, ${cols} a row (the frames are in ${rel(stripDir)}/)`);
}
for (const [c, ts] of readers) {
  console.log(`  warning: the page read ${c} while drawing (${ts.length} frame${ts.length > 1 ? "s" : ""}, first at ${ts[0]} s). Hard rule 1: take time from t ` +
    `and randomness from a seeded hash; here the host held it at t, so the frames still agree, but a renderer that does not will not.`);
}
console.log(`frames: ${written.length} of ${times.length} drawn${failed ? `, ${failed} with problems` : ""}`);
process.exit(failed ? 1 : written.length ? 0 : 2);
