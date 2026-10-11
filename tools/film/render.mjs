// render: a page's film to an MP4 through the page contract (engines/CONTRACT.md), for the engines that are web pages
// and have no renderer of their own (the canvas engine; ClaudeAnimationBase also works, its render.mjs stays the
// documented path). Every frame of the span is drawn at t = k / fps in one of --workers browsers, each rendering a
// contiguous chunk, captured as JPEG (or PNG with --png) and piped into its own x264; the chunks are joined without
// re-encoding. Video only: put the sound on with bin/vh mux.
//
// usage: node tools/film/render.mjs <project | page.html> --browser <chrome> [--out out/film.mp4] [--fps 30]
//          [--range a:b] [--dpr 1] [--workers 4] [--crf 16] [--preset medium] [--gop 60] [--png] [--quality 95]
//          [--frame-timeout 120] [--force] [--real-clock] [--soft-gl]
//        (bin/vh render finds the browser: CHROME_PATH, HyperFrames' chrome-headless-shell, then Chrome or Chromium)
//
//   --out          default <project>/out/<page>.mp4; a lock file beside it stops a second render of the same file
//   --range a:b    only that span (frames a·fps up to b·fps); default the whole film
//   --dpr 2        twice the pixels (4K for a 1920x1080 page)
//   --gop 60       a keyframe every 60 frames exactly, from the span's first frame (default 2 s of frames); the chunks
//                  are whole GOPs, so a later patch can cut the video on keyframes
//   --png          lossless frames into the encoder (slower, larger pipes); default JPEG at --quality 95
//   --force        render a HyperFrames composition this way too (by default: use npx hyperframes render, the measured path)
//
// The colour: Chrome's frames are full-range RGB; the encode converts them to limited-range BT.709 with all four colour
// tags (what bin/vh check expects). Beside the video, <out>.render.json records how it was made (size, fps, frames,
// span, encoder settings, chunks, browser), for a later patch or re-render to match. Exit: 0 rendered and checked ·
// 1 a frame failed, the encoder failed, or the result has the wrong frame count · 2 could not start.
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { openFilm } from "./host.mjs";

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP); process.exit(argv.length ? 0 : 2); }
const die = (msg) => { console.error("render: " + msg); process.exit(2); };
const o = { fps: 30, dpr: 1, workers: 4, crf: 16, preset: "medium", quality: 95, frameTimeout: 120 };
let target = null, out = null, range = null, gop = null, png = false, force = false;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], [k, inline] = a.startsWith("--") && a.includes("=") ? [a.slice(0, a.indexOf("=")), a.slice(a.indexOf("=") + 1)] : [a, undefined];
  const val = () => { const v = inline !== undefined ? inline : argv[++i]; if (v === undefined) die(`${k} needs a value`); return v; };
  const num = (v, what, min) => { const x = Number(v); if (!Number.isFinite(x) || x < min) die(`${what}: ${v} is not a number ≥ ${min}`); return x; };
  if (k === "--out") out = val();
  else if (k === "--range") { range = val().split(":").map((v) => num(v, "--range", 0)); if (range.length !== 2 || range[1] <= range[0]) die("--range a:b, b > a"); }
  else if (k === "--fps") o.fps = num(val(), k, 1);
  else if (k === "--dpr") o.dpr = num(val(), k, 0.25);
  else if (k === "--workers") o.workers = Math.floor(num(val(), k, 1));
  else if (k === "--crf") o.crf = num(val(), k, 0);
  else if (k === "--preset") o.preset = val();
  else if (k === "--gop") gop = Math.floor(num(val(), k, 1));
  else if (k === "--quality") o.quality = Math.min(100, Math.floor(num(val(), k, 1)));
  else if (k === "--frame-timeout") o.frameTimeout = num(val(), k, 1);
  else if (k === "--png") png = true;
  else if (k === "--force") force = true;
  else if (k === "--browser") o.browser = val();
  else if (k === "--real-clock") o.realClock = true;
  else if (k === "--soft-gl") o.softGl = true;
  else if (k.startsWith("-")) die(`unknown option ${k} (-h for the options)`);
  else if (target) die(`one project or page, got ${target} and ${a}`);
  else target = a;
}
if (!target) die("which project or page? (-h for the usage)");
if (!o.browser) die("no browser: pass --browser <chrome>, or run it as bin/vh render");
for (const tool of ["ffmpeg", "ffprobe"]) if (spawnSync(tool, ["-version"]).status !== 0) die(`${tool} is not installed`);

const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
let first;
try { first = await openFilm(target, { ...o, runtime: "auto" }); } catch (e) { die(e.message); }
if (first.kind === "hyperframes" && !force) {
  await first.close();
  die("this is a HyperFrames composition: render it with npx hyperframes render (its renderer is the path this repo measured); --force renders it through the page contract anyway");
}
if (!(first.duration > 0)) { await first.close(); die("the page gives no duration"); }
const fps = o.fps, k0 = range ? Math.round(range[0] * fps) : 0;
const k1 = range ? Math.round(Math.min(range[1], first.duration) * fps) : Math.ceil(first.duration * fps - 1e-6);
const n = k1 - k0;
if (n <= 0) { await first.close(); die(`no frames in ${range ? range.join("–") + " s" : "the film"} (it is ${first.duration} s)`); }
gop = gop || Math.round(2 * fps);
const stem = path.basename(first.page, path.extname(first.page));
const outFile = path.resolve(out || path.join(first.root, "out", `${stem}.mp4`));
fs.mkdirSync(path.dirname(outFile), { recursive: true });

// one render per output file: a second one would interleave its chunks with ours
const lock = outFile + ".lock";
const alive = (pid) => { try { process.kill(pid, 0); return true; } catch (e) { return e.code === "EPERM"; } };
try { fs.writeFileSync(lock, String(process.pid), { flag: "wx" }); } catch {
  const pid = +fs.readFileSync(lock, "utf8");
  if (pid && alive(pid)) { await first.close(); die(`another render (pid ${pid}) is writing ${rel(outFile)}; wait for it, or delete ${rel(lock)} if it is gone`); }
  fs.writeFileSync(lock, String(process.pid));
}
const unlock = () => { try { if (+fs.readFileSync(lock, "utf8") === process.pid) fs.unlinkSync(lock); } catch { /* already gone */ } };
process.on("exit", unlock);

const parts = path.join(path.dirname(outFile), `.${path.basename(outFile)}.parts`);
fs.rmSync(parts, { recursive: true, force: true }); fs.mkdirSync(parts, { recursive: true });
// chunks are whole GOPs, so every keyframe of the joined video falls on the grid k0 + m·gop (a patch can cut there)
const chunk = Math.ceil(Math.ceil(n / Math.max(1, Math.min(o.workers, n))) / gop) * gop, K = Math.ceil(n / chunk);
const chunks = Array.from({ length: K }, (_, w) => [k0 + w * chunk, Math.min(k1, k0 + (w + 1) * chunk)]).filter(([a, b]) => b > a);
const COLOR = "colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv";
const vf = png ? `scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=${COLOR}`
  : `scale=in_color_matrix=bt601:in_range=pc:out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=${COLOR}`;
console.log(`render: ${rel(first.page)} · ${first.kind === "film" ? "window.film" : first.kind} · ${first.width}x${first.height}${o.dpr !== 1 ? ` @${o.dpr}x` : ""} · ` +
  `${n} frames at ${fps} fps (${(k0 / fps).toFixed(3)}–${(k1 / fps).toFixed(3)} s) · ${chunks.length} worker${chunks.length > 1 ? "s" : ""} · ${png ? "PNG" : `JPEG q${o.quality}`} → x264 crf ${o.crf} ${o.preset}, keyframe every ${gop} · ${first.version}`);
for (const p of first.loadProblems) console.log(`  while loading: ${p}`);

let failed = null, done = 0;
const T0 = Date.now(), problems = [];
const within = (p, s, what) => { let timer; return Promise.race([p, new Promise((_, no) => { timer = setTimeout(() => no(new Error(`${what}: no picture after ${s} s (--frame-timeout)`)), s * 1000); })]).finally(() => clearTimeout(timer)); };
const progress = setInterval(() => { if (done) console.log(`  ${done} / ${n} frames · ${((Date.now() - T0) / 1000).toFixed(0)} s · about ${(((Date.now() - T0) / done) * (n - done) / 1000).toFixed(0)} s to go`); }, 15000);
progress.unref();

async function worker(w, [a, b]) {
  let film = w === 0 ? first : null;
  const file = path.join(parts, `part${String(w).padStart(3, "0")}.mp4`);
  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-c:v", png ? "png" : "mjpeg", "-i", "-",
    "-vf", vf, "-c:v", "libx264", "-preset", o.preset, "-crf", String(o.crf), "-g", String(gop), "-keyint_min", String(gop), "-sc_threshold", "0",
    "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", String(fps), file], { stdio: ["pipe", "ignore", "pipe"] });
  let ffErr = ""; ff.stderr.on("data", (d) => { ffErr = (ffErr + d).slice(-2000); });
  const closed = new Promise((ok) => ff.on("close", ok));
  ff.stdin.on("error", () => { /* the encoder died: closed reports it */ });
  try {
    if (!film) film = await openFilm(target, { ...o, runtime: "auto" });
    const capture = png ? { format: "png" } : { format: "jpeg", quality: o.quality };
    for (let k = a; k < b && !failed; k++) {
      const t = k / fps;
      const { png: img } = await within(film.frame(t, capture), o.frameTimeout, `t=${t.toFixed(3)} s`);
      const later = film.problems();
      if (later.length) problems.push(`t=${t.toFixed(3)} s: ${later.join(" | ")}`);
      if (!ff.stdin.write(img)) await new Promise((ok) => ff.stdin.once("drain", ok));
      done++;
    }
  } catch (e) { failed = failed || e.message; }
  ff.stdin.end();
  const code = await closed;
  if (film) await film.close();
  if (code !== 0 && !failed) failed = `the encoder for frames ${a}–${b - 1} failed: ${ffErr.trim()}`;
  return file;
}

const files = await Promise.all(chunks.map((c, w) => worker(w, c)));
clearInterval(progress);
if (failed) { fs.rmSync(parts, { recursive: true, force: true }); console.error(`render: ${failed}`); process.exit(1); }
fs.writeFileSync(path.join(parts, "list.txt"), files.map((f) => `file '${path.basename(f)}'`).join("\n") + "\n");
const join = spawnSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", path.join(parts, "list.txt"), "-c", "copy", "-movflags", "+faststart", outFile], { encoding: "utf8" });
if (join.status !== 0) { console.error(`render: joining the chunks failed: ${join.stderr.trim()}`); process.exit(1); }
// the frame count the MP4 records (counting by decoding would take minutes on a long 4K film)
const probe = spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries",
  "stream=nb_frames,width,height,pix_fmt,color_range,color_space,color_primaries,color_transfer", "-of", "json", outFile], { encoding: "utf8" });
const st = JSON.parse(probe.stdout || "{}").streams?.[0] || {};
fs.rmSync(parts, { recursive: true, force: true });
const secs = (Date.now() - T0) / 1000;
const sidecar = {
  note: "how this video was made (bin/vh render); a patch or re-render should match these",
  page: (() => { const r = path.relative(path.dirname(outFile), first.page); return r.startsWith("..") ? first.page : r; })(),
  kind: first.kind, width: first.width, height: first.height, dpr: o.dpr, pixels: [st.width, st.height], fps, frames: n,
  span: [+(k0 / fps).toFixed(6), +(k1 / fps).toFixed(6)], first_frame: k0, capture: png ? "png" : `jpeg q${o.quality}`,
  encoder: { codec: "libx264", crf: o.crf, preset: o.preset, gop, keyint_min: gop, sc_threshold: 0, pix_fmt: st.pix_fmt, color: [st.color_range, st.color_space, st.color_primaries, st.color_transfer] },
  chunks: chunks.map(([a, b]) => [a, b]), browser: first.version, real_clock: !!o.realClock, seconds: +secs.toFixed(1),
};
fs.writeFileSync(outFile + ".render.json", JSON.stringify(sidecar, null, 1) + "\n");
const okCount = +st.nb_frames === n, okColor = st.pix_fmt === "yuv420p" && st.color_range === "tv" && st.color_space === "bt709";
console.log(`  ${rel(outFile)}: ${st.nb_frames} frames, ${st.width}x${st.height}, ${st.pix_fmt} ${st.color_range}/${st.color_space}, in ${secs.toFixed(0)} s` +
  ` (${(secs * 1000 / n).toFixed(0)} ms a frame); how it was made: ${rel(outFile + ".render.json")}`);
for (const p of problems) console.log(`  ${p}`);
if (!okCount) console.log(`  the video has ${st.nb_frames} frames, not ${n}`);
if (!okColor) console.log(`  the colour tags are not yuv420p tv/bt709`);
if (problems.length || !okCount || !okColor) process.exit(1);
console.log("render: done · the sound goes on with bin/vh mux");
