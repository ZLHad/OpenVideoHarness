// determinism: is each of a page's frames a function of t (hard rule 1)? The same moments are drawn four ways and the
// lossless PNGs compared (engines/CONTRACT.md):
//   A  one browser, in order (the reference)
//   B  the same browser again, in reverse order, after a frame elsewhere: state carried between frames shows here
//   C  a second browser, in reverse order: what differs between processes (GPU rasterization, caches) shows here
//   D  a fresh browser without the host's clock (--real-clock): a page that reads Math.random, Date or timers shows
//      here; the host holds those at t, so A–C can agree while another renderer would not
// A difference is measured as PSNR over the RGB pixels; hard rule 1 allows a tolerance for the GPU (45 dB).
//
// usage: node tools/film/determinism.mjs <project | page.html> --browser <chrome> [--at t[,t…]] [--samples 6]
//          [--min-psnr 45] [--size WxH] [--dpr 1] [--soft-gl] [--runtime auto|on|off] [--out dir]
//        (bin/vh determinism finds the browser: CHROME_PATH, HyperFrames' chrome-headless-shell, then Chrome or Chromium)
//
// Without --at, --samples moments spread over the film. The PNGs go to <out> (default <project>/out/check/determinism).
// Exit: 0 A, B and C agree (identical, or above --min-psnr) · 1 they do not, or a frame failed · 2 could not draw.
// D only warns, its errors too: it tells whether the page leans on the host's clock.
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { openFilm } from "./host.mjs";

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP.trimEnd() + "\n"); process.exit(argv.length ? 0 : 2); }
const bail = (msg) => { console.error("determinism: " + msg); process.exit(2); };
const o = { samples: 6, minPsnr: 45, dpr: 1, runtime: "auto" };
let target = null, at = null, out = null, size = null;
const r3 = (t) => Math.round(t * 1000) / 1000;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], [k, inline] = a.startsWith("--") && a.includes("=") ? [a.slice(0, a.indexOf("=")), a.slice(a.indexOf("=") + 1)] : [a, undefined];
  const val = () => { const v = inline !== undefined ? inline : argv[++i]; if (v === undefined) bail(`${k} needs a value`); return v; };
  const num = (v, what, min) => { const x = Number(v); if (v === "" || !Number.isFinite(x) || x < min) bail(`${what}: ${v} is not a number ≥ ${min}`); return x; };
  if (k === "--at") at = [...new Set(val().split(",").map((v) => r3(num(v.trim(), "--at", 0))))];
  else if (k === "--samples") o.samples = Math.floor(num(val(), k, 1));
  else if (k === "--min-psnr") o.minPsnr = num(val(), k, 0);
  else if (k === "--dpr") o.dpr = num(val(), k, 0.25);
  else if (k === "--size") { const m = val().match(/^(\d+)x(\d+)$/); if (!m || !+m[1] || !+m[2]) bail("--size: write it as 1920x1080"); size = [+m[1], +m[2]]; }
  else if (k === "--out") out = val();
  else if (k === "--browser") o.browser = val();
  else if (k === "--soft-gl") o.softGl = true;
  else if (k === "--runtime") { o.runtime = val(); if (!["auto", "on", "off"].includes(o.runtime)) bail("--runtime: auto, on or off"); }
  else if (k.startsWith("-")) bail(`unknown option ${k} (-h for the options)`);
  else if (target) bail(`one project or page, got ${target} and ${a}`);
  else target = a;
}
if (!target) bail("which project or page? (-h for the usage)");
if (!o.browser) bail("no browser: pass --browser <chrome>, or run it as bin/vh determinism");
const opts = { ...o, width: size && size[0], height: size && size[1] };

const open = async (extra = {}) => { try { return await openFilm(target, { ...opts, ...extra }); } catch (e) { bail(e.message); } };
const A = await open();
if (!(A.duration > 0) && !at) { await A.close(); bail("the page gives no duration: pass --at"); }
const times = at || Array.from({ length: o.samples }, (_, k) => r3(A.duration * (k + 0.5) / o.samples));
const bad = times.filter((t) => t < 0 || (A.duration > 0 && t >= A.duration));
if (bad.length) { await A.close(); bail(`${bad.join(", ")} s: outside the film (0 up to ${A.duration} s)`); }
const outDir = path.resolve(out || path.join(A.root, "out", "check", "determinism"));
fs.mkdirSync(outDir, { recursive: true });
const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
console.log(`determinism: ${rel(A.page)} · ${A.kind === "film" ? "window.film" : A.kind === "__vh" ? "window.__vh" : "HyperFrames runtime"} · ${A.width}x${A.height}` +
  `${o.dpr !== 1 ? ` @${o.dpr}x` : ""} · ${times.length} moment${times.length > 1 ? "s" : ""} · ${A.version}`);

let failed = 0, dErrors = 0;
const ms = [], touched = new Set();
// draw the times in this order, write <way>-t<seconds>.png, return { t: file }. A frame that fails, or a page error,
// fails the check in A, B and C; in D (no host clock) it is a sign of the same thing D looks for, and only warns
const flag = (way, t, msg) => { if (way === "D") dErrors++; else failed++; console.log(`  ${way} t=${t} s: ${msg}${way === "D" ? " (warning: without the host's clock)" : ""}`); };
async function pass(film, way, order, warm) {
  const files = {};
  if (warm !== undefined) await film.frame(warm).catch(() => {});   // a frame elsewhere first, so carried state shows
  for (const t of order) {
    const t0 = Date.now();
    try {
      const { png, touched: tc } = await film.frame(t);
      if (way === "A") { ms.push(Date.now() - t0); tc.forEach((c) => touched.add(c)); }
      const f = path.join(outDir, `${way}-t${t.toFixed(3).padStart(8, "0")}.png`);
      fs.writeFileSync(f, png); files[t] = f;
      const p = film.problems(); if (p.length) flag(way, t, p.join(" | "));
    } catch (e) { flag(way, t, e.message); }
  }
  return files;
}
const rev = [...times].reverse(), elsewhere = r3((times[0] + (times[1] ?? times[0] + 1)) / 2);
const a = await pass(A, "A", times);
const b = await pass(A, "B", rev, A.duration > elsewhere ? elsewhere : 0);
await A.close();
const C = await open(); const c = await pass(C, "C", rev); await C.close();
const D = await open({ realClock: true }); const d = await pass(D, "D", rev); await D.close();

// "identical", or the PSNR in dB (ffmpeg's psnr filter over RGB)
function compare(x, y) {
  if (!x || !y) return null;
  if (Buffer.compare(fs.readFileSync(x), fs.readFileSync(y)) === 0) return Infinity;
  const r = spawnSync("ffmpeg", ["-v", "info", "-nostats", "-i", x, "-i", y, "-lavfi", "[0]format=rgb24[p];[1]format=rgb24[q];[p][q]psnr", "-f", "null", "-"], { encoding: "utf8" });
  const m = (r.stderr || "").match(/average:(inf|[\d.]+)/);
  return m ? (m[1] === "inf" ? Infinity : +m[1]) : NaN;
}
const say = (v) => (v === null ? "not drawn" : v === Infinity ? "identical" : Number.isNaN(v) ? "could not compare" : `${v.toFixed(1)} dB`);
let worst = Infinity, clockOnly = false;
console.log(`  ${"t".padStart(8)}   ${"same browser, reversed".padEnd(24)}${"other browser".padEnd(16)}without the host's clock`);
for (const t of times) {
  const vb = compare(a[t], b[t]), vc = compare(a[t], c[t]), vd = compare(a[t], d[t]);
  for (const v of [vb, vc]) if (v !== null && !(v >= o.minPsnr)) failed++;
  for (const v of [vb, vc]) if (v !== null && !Number.isNaN(v)) worst = Math.min(worst, v);
  if (vd !== null && !(vd >= o.minPsnr)) clockOnly = true;
  console.log(`  ${t.toFixed(3).padStart(8)}   ${say(vb).padEnd(24)}${say(vc).padEnd(16)}${say(vd)}`);
}
ms.sort((p, q) => p - q);
if (ms.length) console.log(`  a frame takes ${ms[Math.floor(ms.length / 2)]} ms (median: draw and capture)`);
if (dErrors) clockOnly = true;
if (clockOnly && !failed) {   // only when A–C agree: otherwise D differs for the same reason they do
  console.log(`  warning: without the host's clock the frames differ${dErrors ? " or fail" : ""}${touched.has("Math.random") ? " (the page reads Math.random)" : ""}: the page leans on the ` +
    `host holding its clocks at t. Hard rule 1: take time from t and randomness from a seeded hash, or a renderer that does not hold them will draw other frames.`);
}
console.log(`determinism: ${failed ? `does not hold (${failed} difference${failed > 1 ? "s" : ""} under ${o.minPsnr} dB or failed frames)` :
  `holds${worst === Infinity ? ", every frame identical" : `, worst ${worst.toFixed(1)} dB`}`} · PNGs in ${rel(outDir)}`);
process.exit(failed ? 1 : 0);
