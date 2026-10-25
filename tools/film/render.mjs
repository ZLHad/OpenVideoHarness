// render: a page's film to an MP4 through the page contract (engines/CONTRACT.md), for the engines that are web pages
// and have no renderer of their own (the canvas engine; ClaudeAnimationBase also works, its render.mjs stays the
// documented path). Every frame of the span is drawn at t = k / fps and captured as JPEG (or PNG with --png). The span
// is cut into chunks of one GOP each; --workers browsers take the next chunk as they finish one (a slow chapter does not
// hold the others up), each chunk piped into an x264 of its own; the chunks are joined without re-encoding. Video only:
// put the sound on with bin/vh mux.
//
// usage: node tools/film/render.mjs <project | page.html> --browser <chrome> [--out out/film.mp4] [--fps 30]
//          [--range a:b | --frames k0:k1] [--dpr 1] [--workers 4] [--crf 16] [--preset medium] [--gop 60] [--png] [--quality 95]
//          [--frame-timeout 120] [--estimate | --no-estimate] [--note text] [--force] [--real-clock] [--soft-gl]
//        (bin/vh render finds the browser: CHROME_PATH, HyperFrames' chrome-headless-shell, then Chrome or Chromium)
//
//   --out          default <project>/out/<page>.mp4. A relative path is from the current folder, as every bin/vh path
//                  is (said when that puts the video outside the project); a lock file beside it stops a second render
//                  of the same file
//   --fps 30       the frame rate drawn. A page that gives its own (window.film.fps; canvas-film's FILM.fps, which steps
//                  its grain once a frame) is told apart when the two differ
//   --range a:b    only that span (frames a·fps up to b·fps); default the whole film
//   --frames k0:k1 only frames k0 up to k1 (k1 left out), frame k drawn at k / fps: exact, for bin/vh patch
//   --dpr 2        twice the pixels (4K for a 1920x1080 page)
//   --gop 60       a keyframe every 60 frames exactly, from the span's first frame (default 2 s of frames). Each chunk is
//                  one GOP, so a later patch can cut the video on keyframes, and the video does not depend on --workers
//   --png          lossless frames into the encoder (slower, larger pipes); default JPEG at --quality 95
//   --estimate     before a span of more than 600 frames to draw (--estimate: any span), a few frames spread over it are
//                  drawn and encoded first: the time a frame takes, the video's size and the disk it needs are printed,
//                  and a disk that cannot hold it stops the render (exit 2). A few seconds; --no-estimate skips it
//   --force        render a HyperFrames composition this way too (by default: use npx hyperframes render, the measured path)
//   --frame-timeout 120  a frame not drawn in this many seconds fails the render (the finished chunks are kept). Each
//                  browser's page may take as long to set window.film and to be ready (at least 30 s and 120 s a wait;
//                  OVH_PAGE_TIMEOUT=S sets those alone, tools/film/host.mjs)
//   --note text    a line for this version in the project's record (bin/vh versions)
//
// The colour: Chrome's frames are full-range RGB; the encode converts them to limited-range BT.709 with all four colour
// tags (what bin/vh check expects). Beside the video, <out>.render.json records how it was made (size, fps, frames,
// span, encoder settings, chunks, browser), for a later patch or re-render to match. Exit: 0 rendered and checked ·
// 1 a frame failed, the encoder stopped, or the result has the wrong frame count or colour tags; also when the page
// reported an error while drawing (the video is written then, and the errors are listed) · 2 could not start.
// Stopped (Ctrl-C or SIGTERM: exit 130, 143) or failed, a render keeps the chunks it finished in .<out>.parts beside
// the video: the same command again draws only the rest, while the page and every file it loaded, the options that shape
// the video (all but --workers, --frame-timeout and the estimate), the browser and these tools are unchanged; anything
// else changed, it says what and starts over. A chunk in which the page reported an error is never kept.
// Before drawing it checks the disk the render needs at its peak (the chunks it draws and the joined copy; on a resume,
// the chunks left and the joined copy, kept chunks included): it stops (exit 2) when even a flat film would not fit; the
// estimate above measures it. Its glyph check covers the frames it draws: on a resume it says the kept ones were not.
// A video inside a project is a version of its film (tools/versions.py, bin/vh versions): the film it replaces at that
// path is kept in out/versions/ first (while the disk can hold it; else it goes to the Trash, said), and the record gets
// the new one. The sidecar also keeps the page's shots and chapters (window.film.shots, chapters) when it gives them, and
// `files`: every file in the page's folder a browser of this render was sent and its sha256 (what a resume compares; the
// host's own scripts, outside the folder, stay in plan.json alone), by its path from that folder, null for one that could
// not be read; bin/vh assets check compares it with the project's ledger.
// bin/vh patch draws its frames through this tool with OVH_RENDER_PIECE=1: a piece of a patch is a step, so it ends without
// the "render: done" line (the patch's own last line says the job is done).
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { openFilm } from "./host.mjs";
import { HOOK, check as checkGlyphs, collectDom, merge as mergeGlyphs, report as glyphReport } from "./glyphs.mjs";
import { note as activityNote, progress as activityProgress } from "./activity.mjs";   // the project's activity log (bin/vh activity)
import { commit } from "./versions.mjs";                                                 // the project's versions (bin/vh versions)

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HERE = path.dirname(new URL(import.meta.url).pathname);
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP.trimEnd() + "\n"); process.exit(argv.length ? 0 : 2); }
const die = (msg) => { console.error("render: " + msg); process.exit(2); };
const o = { fps: 30, dpr: 1, workers: 4, crf: 16, preset: "medium", quality: 95, frameTimeout: 120, estimate: "auto" };
let target = null, out = null, range = null, frames = null, gop = null, png = false, force = false, fpsGiven = false, note = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], [k, inline] = a.startsWith("--") && a.includes("=") ? [a.slice(0, a.indexOf("=")), a.slice(a.indexOf("=") + 1)] : [a, undefined];
  const val = () => { const v = inline !== undefined ? inline : argv[++i]; if (v === undefined) die(`${k} needs a value`); return v; };
  const num = (v, what, min) => { const x = Number(v); if (v === "" || !Number.isFinite(x) || x < min) die(`${what}: ${JSON.stringify(v)} is not a number ≥ ${min}`); return x; };
  if (k === "--out") out = val();
  else if (k === "--range") { range = val().split(":").map((v) => num(v, "--range", 0)); if (range.length !== 2 || range[1] <= range[0]) die("--range a:b, b > a"); }
  else if (k === "--frames") { frames = val().split(":").map((v) => num(v, "--frames", 0)); if (frames.length !== 2 || !frames.every(Number.isInteger) || frames[1] <= frames[0]) die("--frames k0:k1, whole frame numbers, k1 > k0"); }
  else if (k === "--fps") { o.fps = num(val(), k, 1); fpsGiven = true; }
  else if (k === "--dpr") o.dpr = num(val(), k, 0.25);
  else if (k === "--workers") o.workers = Math.floor(num(val(), k, 1));
  else if (k === "--crf") o.crf = num(val(), k, 0);
  else if (k === "--preset") o.preset = val();
  else if (k === "--gop") gop = Math.floor(num(val(), k, 1));
  else if (k === "--quality") o.quality = Math.min(100, Math.floor(num(val(), k, 1)));
  else if (k === "--frame-timeout") o.frameTimeout = num(val(), k, 1);
  else if (k === "--estimate" || k === "--no-estimate") { const e = k === "--estimate" ? "on" : "off"; if (o.estimate !== "auto" && o.estimate !== e) die("--estimate or --no-estimate, not both"); o.estimate = e; }
  else if (k === "--png") png = true;
  else if (k === "--note") note = val();
  else if (k === "--force") force = true;
  else if (k === "--browser") o.browser = val();
  else if (k === "--real-clock") o.realClock = true;
  else if (k === "--soft-gl") o.softGl = true;
  else if (k.startsWith("-")) die(`unknown option ${k} (-h for the options)`);
  else if (target) die(`one project or page, got ${target} and ${a}`);
  else target = a;
}
if (!target) die("which project or page? (-h for the usage)");
if (range && frames) die("--range or --frames, not both");
if (out && fs.existsSync(out) && fs.statSync(out).isDirectory()) die(`--out ${out} is a folder: name the video file (…/film.mp4)`);
if (out && !/\.(mp4|mov)$/i.test(out)) die(`--out ${out}: the video file, .mp4 (or .mov)`);
if (!o.browser) die("no browser: pass --browser <chrome>, or run it as bin/vh render");
for (const tool of ["ffmpeg", "ffprobe"]) if (spawnSync(tool, ["-version"]).status !== 0) die(`${tool} is not installed`);

const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
let first;
try { first = await openFilm(target, { ...o, runtime: "auto", prelude: [HOOK] }); } catch (e) { die(e.message); }
if (first.kind === "hyperframes" && !force) {
  await first.close();
  die("this is a HyperFrames composition: render it with npx hyperframes render (its renderer is the path this repo measured); --force renders it through the page contract anyway");
}
if (!(first.duration > 0)) { await first.close(); die("the page gives no duration"); }
// the frame rate the page is made for: window.film.fps (engines/CONTRACT.md), else canvas-film's settings in a copy made
// before the engine gave it
let pageFps = null;
try { pageFps = +(await first.field("fps")) || +(await first.ev('typeof FILM === "object" && FILM && Number(FILM.fps) || 0', "reading FILM.fps")) || null; } catch { /* none */ }
// the page's shots and chapters, for the sidecar: what bin/vh patch names and bin/vh thumbs picks a frame for
const listOf = async (name) => { try { const x = await first.field(name); return Array.isArray(x) ? x : null; } catch { return null; } };
const fin = (x) => Number.isFinite(x);
const pageShots = ((await listOf("shots")) || []).filter((x) => x && fin(+x.start) && fin(+x.end) && +x.end > +x.start).map((x, i) => ({
  id: String(x.id ?? `S${String(i + 1).padStart(2, "0")}`), start: +x.start, end: +x.end,
  ...(x.transition && fin(+x.transition.duration) && +x.transition.duration > 0 ? { transition: +x.transition.duration } : {}) }));
const pageChapters = ((await listOf("chapters")) || []).filter((x) => x && fin(+x.t)).map((x) => ({ t: +x.t, title: String(x.title ?? ""), ...(x.id != null ? { id: String(x.id) } : {}) }));
const fps = o.fps, last = Math.ceil(first.duration * fps - 1e-6);   // the film's frame count: its last frame is last - 1
const k0 = frames ? frames[0] : range ? Math.round(range[0] * fps) : 0;
const k1 = frames ? Math.min(frames[1], last) : !range || range[1] >= first.duration ? last : Math.round(range[1] * fps);
const n = k1 - k0;
if (n <= 0) { await first.close(); die(`no frames in ${frames ? `frames ${frames.join("–")}` : range ? range.join("–") + " s" : "the film"} (it is ${first.duration} s, ${last} frames)`); }
gop = gop || Math.round(2 * fps);
const stem = path.basename(first.page, path.extname(first.page));
const outFile = path.resolve(out || path.join(first.root, "out", `${stem}.mp4`));
try { fs.mkdirSync(path.dirname(outFile), { recursive: true }); } catch (e) { await first.close(); die(`cannot make ${rel(path.dirname(outFile))}: ${e.message}`); }
// a relative --out is from the current folder; one that lands outside the project (bin/vh run from the harness with
// --out out/x.mp4) is said in full, as the short form would read as the project's own out/
const inside = (f, dir) => (f + path.sep).startsWith(dir + path.sep);
const outside = !!out && !path.isAbsolute(out) && !inside(fs.realpathSync(path.dirname(outFile)), first.root);
const shown = outside ? outFile : rel(outFile);
{   // a project's out/versions holds the earlier versions of its films (bin/vh versions): nothing is rendered over them
  const dir = fs.realpathSync(path.dirname(outFile));
  for (let d = dir; ; d = path.dirname(d)) {
    if (fs.existsSync(path.join(d, "BRIEF.md"))) {
      if (inside(dir, path.join(d, "out", "versions")) || dir === path.join(d, "out", "versions")) {
        await first.close(); die(`--out ${shown} is inside out/versions, where the earlier versions of the project's films are kept: write it elsewhere (bin/vh versions use brings a kept one back)`);
      }
      break;
    }
    if (path.dirname(d) === d) break;
  }
}

// one render per output file: a second one would interleave its chunks with ours. A lock whose render is gone (its pid
// no longer runs) is deleted and taken afresh; an empty one is a render that has not written its pid yet, unless it is old
const lock = outFile + ".lock";
const alive = (pid) => { try { process.kill(pid, 0); return true; } catch (e) { return e.code === "EPERM"; } };
function takeLock() {
  for (let tries = 0; tries < 5; tries++) {
    try { fs.writeFileSync(lock, String(process.pid), { flag: "wx" }); return null; } catch (e) {
      if (e.code !== "EEXIST") return `cannot write ${rel(lock)}: ${e.message}`;
      let pid = 0, age = 0;
      try { pid = +fs.readFileSync(lock, "utf8"); age = Date.now() - fs.statSync(lock).mtimeMs; } catch { continue; }   // gone meanwhile
      if (pid ? alive(pid) : age < 10000) return `another render${pid ? ` (pid ${pid})` : ""} is writing ${rel(outFile)}; wait for it, or delete ${rel(lock)} if it is gone`;
      try { fs.unlinkSync(lock); } catch { /* another render took it over first: try again */ }
    }
  }
  return `could not take ${rel(lock)}`;
}
// the disk (measured once the chunks an earlier render left are kept or cleared, below): OVH_FREE_BYTES pretends that much
// is free (for tests)
const freeOnDisk = () => process.env.OVH_FREE_BYTES ? +process.env.OVH_FREE_BYTES : (() => { try { const s = fs.statfsSync(path.dirname(outFile)); return s.bavail * s.bsize; } catch { return Infinity; } })();
const gb = (b) => (b / 1e9).toFixed(b < 1e8 ? 3 : 1);
const busy = takeLock();
if (busy) { await first.close(); die(busy); }
const unlock = () => { try { if (+fs.readFileSync(lock, "utf8") === process.pid) fs.unlinkSync(lock); } catch { /* already gone */ } };
process.on("exit", unlock);

// chunks are whole GOPs, one each, so every keyframe of the joined video falls on the grid k0 + m·gop (a patch can cut
// there) and a chunk's bytes depend on its own frames only, not on how many workers there were or which drew it
const plan = Array.from({ length: Math.ceil(n / gop) }, (_, i) => [k0 + i * gop, Math.min(k1, k0 + (i + 1) * gop)]);
const parts = path.join(path.dirname(outFile), `.${path.basename(outFile)}.parts`);
const kept = (i) => path.join(parts, `part${String(i).padStart(4, "0")}.mp4`);   // a chunk finished clean: kept for a resume
const isKept = (f) => /^part\d{4,}\.mp4$/.test(f);
const encoders = new Set();
// after a stop or a failure the finished chunks stay (and plan.json, which says what they were made from); the rest goes
const keepFinished = () => {
  let names = [];
  try { names = fs.readdirSync(parts); } catch { return 0; }
  const k = names.filter(isKept).length;
  if (!k) { fs.rmSync(parts, { recursive: true, force: true }); return 0; }
  for (const f of names) if (f !== "plan.json" && !isKept(f)) fs.rmSync(path.join(parts, f), { recursive: true, force: true });
  return k;
};
const keptSay = (k) => `${k} of ${plan.length} chunks are kept in ${rel(parts)}: the same command again draws only the rest (a changed page starts over)`;
for (const [sig, code] of [["SIGINT", 130], ["SIGTERM", 143]]) process.once(sig, () => {   // the lock goes on exit; the browsers and their profiles too (tools/textcheck/browser.mjs)
  for (const ff of encoders) ff.kill("SIGKILL");
  const k = keepFinished();
  console.error(`render: stopped (${sig}); ` + (k ? keptSay(k) : "the chunks so far are deleted"));
  process.exit(code);
});
const COLOR = "colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv";
// x264's yuv420p needs an even width and height: an odd one (1366 x 768 at --dpr 1.5 is 2049 x 1152) loses its last column or row
const EVEN = "crop=trunc(iw/2)*2:trunc(ih/2)*2", px = [Math.round(first.width * o.dpr), Math.round(first.height * o.dpr)];
const vf = png ? `${EVEN},scale=out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=${COLOR}`
  : `${EVEN},scale=in_color_matrix=bt601:in_range=pc:out_color_matrix=bt709:out_range=tv:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=${COLOR}`;
const x264 = (file) => spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(fps), "-c:v", png ? "png" : "mjpeg", "-i", "-",
  "-vf", vf, "-c:v", "libx264", "-preset", o.preset, "-crf", String(o.crf), "-g", String(gop), "-keyint_min", String(gop), "-sc_threshold", "0",
  "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-r", String(fps), file], { stdio: ["pipe", "ignore", "pipe"] });
const capture = png ? { format: "png" } : { format: "jpeg", quality: o.quality };

// ---- what the chunks are made from: a resume takes the finished ones only while all of it is the same ----
const sha = (f) => {
  const h = crypto.createHash("sha256"), fd = fs.openSync(f, "r"), buf = Buffer.alloc(1 << 22);
  try { for (let r; (r = fs.readSync(fd, buf, 0, buf.length, null)) > 0;) h.update(buf.subarray(0, r)); } finally { fs.closeSync(fd); }
  return h.digest("hex");
};
const recipe = {
  page: fs.realpathSync(first.page), kind: first.kind, width: first.width, height: first.height, dpr: o.dpr, fps, frames: [k0, k1], gop,
  capture: png ? "png" : `jpeg q${o.quality}`, crf: o.crf, preset: o.preset, vf, real_clock: !!o.realClock, soft_gl: !!o.softGl, browser: first.version,
  ffmpeg: (spawnSync("ffmpeg", ["-version"], { encoding: "utf8" }).stdout || "").split("\n")[0],
  tools: crypto.createHash("sha256").update(["render.mjs", "host.mjs", "clock.js", "glyphs.mjs"].map((f) => sha(path.join(HERE, f))).join()).digest("hex"),
};
const loaded = new Map();   // every file a browser of this render was sent, and its sha256
const planFile = path.join(parts, "plan.json");
const writePlan = (film) => {   // before a chunk is kept: the files its frames loaded are on record first
  for (const f of film.served()) if (!loaded.has(f)) { try { loaded.set(f, sha(f)); } catch { loaded.set(f, null); } }
  fs.writeFileSync(planFile, JSON.stringify({ note: "what bin/vh render's chunks here were made from; a render resumes from them only while all of it is the same", recipe, files: Object.fromEntries(loaded) }, null, 1) + "\n");
};
let reuse = new Set(), why = null;
{
  let old = null, names = [];
  try { names = fs.readdirSync(parts); old = JSON.parse(fs.readFileSync(planFile, "utf8")); } catch { /* none, or not ours */ }
  const done = names.filter(isKept);
  if (old && done.length) {
    const changed = Object.keys(recipe).filter((k) => JSON.stringify((old.recipe || {})[k]) !== JSON.stringify(recipe[k]));
    const files = Object.entries(old.files || {}).filter(([f, h]) => { try { return sha(f) !== h; } catch { return true; } }).map(([f]) => rel(f));
    if (!changed.length && !files.length) {
      for (const [f, h] of Object.entries(old.files)) loaded.set(f, h);
      reuse = new Set(plan.map((_, i) => i).filter((i) => done.includes(path.basename(kept(i))) && fs.statSync(kept(i)).size > 0));
    } else why = [...changed.map((k) => k === "frames" ? "the span" : k === "tools" ? "these tools" : k), ...files.slice(0, 3), ...(files.length > 3 ? [`${files.length - 3} more files`] : [])].join(", ");
  } else if (done.length) why = "no record of what they were made from";
  if (why) console.log(`  the ${done.length} chunks kept from an earlier render are not used (changed: ${why}); starting over`);
  if (reuse.size) { const keep = new Set([...reuse].map((i) => path.basename(kept(i)))); for (const f of names) if (f !== "plan.json" && !keep.has(f)) fs.rmSync(path.join(parts, f), { recursive: true, force: true }); }
  else { fs.rmSync(parts, { recursive: true, force: true }); fs.mkdirSync(parts, { recursive: true }); }
  writePlan(first);
}
const todo = plan.map((_, i) => i).filter((i) => !reuse.has(i)), nTodo = todo.reduce((s, i) => s + plan[i][1] - plan[i][0], 0);
// the disk at the peak is what this run writes on top of what is there: the chunks it draws, then the joined copy, which
// is the kept chunks' bytes (known) and those chunks again. x264 at these CRFs has made 0.04 bits a pixel (a flat test
// page) to 0.4 (4K 3D with grain): refuse only when even 0.01 does not fit, say so when 0.06–0.4 might not and nothing
// measured it (the estimate below measures it)
const keptBytes = [...reuse].reduce((s, i) => s + fs.statSync(kept(i)).size, 0), free = freeOnDisk();
const peak = (bpp) => keptBytes + 2 * px[0] * px[1] * nTodo * bpp / 8;
const peakOf = reuse.size ? `the ${nTodo} frames left to draw and the joined copy (${reuse.size} chunks kept, ${gb(keptBytes)} GB)` : `${n} frames`;
if (peak(0.01) > free) {
  await first.close(); keepFinished();
  die(`at least ${gb(peak(0.01))} GB needed at the peak for ${peakOf} at ${px[0]}x${px[1]} (likely ${gb(peak(0.06))}–${gb(peak(0.4))}), ${gb(free)} GB free on that disk`);
}
const W = Math.min(o.workers, todo.length);
console.log(`render: ${rel(first.page)} · ${first.kind === "film" ? "window.film" : first.kind} · ${first.width}x${first.height}${o.dpr !== 1 ? ` @${o.dpr}x` : ""} · ` +
  `${n} frames at ${fps} fps (${(k0 / fps).toFixed(3)}–${(k1 / fps).toFixed(3)} s) · ${plan.length} chunk${plan.length > 1 ? "s" : ""}, ${W} worker${W === 1 ? "" : "s"} · ${png ? "PNG" : `JPEG q${o.quality}`} → x264 crf ${o.crf} ${o.preset}, keyframe every ${gop} · ${first.version}`);
for (const p of first.loadProblems) console.log(`  while loading: ${p}`);
if (outside) console.log(`  --out ${out} is from the current folder: ${outFile}, outside the project (${first.root})`);
if (px[0] % 2 || px[1] % 2) console.log(`  note: ${px[0]}x${px[1]} pixels; x264 needs even sizes, so the video is ${px[0] - px[0] % 2}x${px[1] - px[1] % 2}`);
if (pageFps && Math.abs(pageFps - fps) > 1e-6) console.log(`  fps: drawn at ${fps} fps (${fpsGiven ? "--fps" : "the default; --fps sets it"}), the page says ${pageFps} (window.film.fps or FILM.fps): what it steps once a frame (grain) steps at its rate; make the two agree`);
if (reuse.size) console.log(`  resuming: ${reuse.size} of ${plan.length} chunks kept from the last render of this file (${plan.length - reuse.size} to draw)`);

let failed = null, done = 0;
// the first failure ends the render; the other workers finish the chunk they are on, so that it is kept for a resume
const failWith = (msg) => { if (failed) return; failed = msg; if (W > 1) console.log(`  stopping: ${msg} (the other workers finish their chunk first)`); };
const within = (p, s, what) => { let timer; return Promise.race([p, new Promise((_, no) => { timer = setTimeout(() => no(new Error(`${what}: no picture after ${s} s (--frame-timeout)`)), s * 1000); })]).finally(() => clearTimeout(timer)); };
const size = (b) => b >= 1e9 ? `${(b / 1e9).toFixed(1)} GB` : b >= 1e6 ? `${(b / 1e6).toFixed(0)} MB` : `${Math.ceil(b / 1e3)} kB`;
const ftime = (s) => s < 90 ? `${s.toFixed(0)} s` : s < 5400 ? `${(s / 60).toFixed(0)} min` : `${(s / 3600).toFixed(1)} h`;

// ---- the estimate: a few frames spread over the span, drawn and encoded as the render will ----
if (todo.length && (o.estimate === "on" || (o.estimate === "auto" && nTodo > 600))) {
  const S = Math.min(6, todo.length), at = [...new Set(Array.from({ length: S }, (_, i) => plan[todo[Math.floor((i + 0.5) * todo.length / S)]][0]))];
  const ms = [], runs = [];
  try {
    await within(first.frame(at[0] / fps, capture), o.frameTimeout, `t=${(at[0] / fps).toFixed(3)} s`);   // not timed: the first frame also compiles and decodes
    for (const k of at) {   // a keyframe and the two frames after it: what a GOP's first frame and its others cost
      const imgs = [];
      for (const kk of [k, k + 1, k + 2].filter((x) => x < k1)) {
        const t0 = performance.now();
        imgs.push((await within(first.frame(kk / fps, capture), o.frameTimeout, `t=${(kk / fps).toFixed(3)} s`)).png);
        ms.push(performance.now() - t0);
      }
      runs.push(imgs);
    }
  } catch (e) { await first.close(); console.error(`render: ${e.message} (drawing the estimate's frames)`); keepFinished(); process.exit(1); }
  first.problems();   // what these frames report, they report again when the render draws them
  const sizes = await Promise.all(runs.map((imgs, j) => new Promise((ok) => {
    const f = path.join(parts, `estimate${j}.mp4`), ff = x264(f);
    encoders.add(ff); ff.stdin.on("error", () => {}); ff.stderr.resume();
    for (const img of imgs) ff.stdin.write(img);
    ff.stdin.end();
    ff.on("close", (code) => {
      encoders.delete(ff);
      const p = code === 0 ? spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries", "packet=size", "-of", "csv=p=0", f], { encoding: "utf8" }) : null;
      fs.rmSync(f, { force: true });
      const b = p && p.status === 0 ? p.stdout.split(/\s+/).filter(Boolean).map(Number) : [];
      ok(b.length ? (b[0] + (gop - 1) * (b.length > 1 ? b.slice(1).reduce((x, y) => x + y, 0) / (b.length - 1) : b[0] / 4)) / gop : null);   // bytes a frame: the keyframe once a GOP, the others like those after it
    });
  })));
  const mean = ms.reduce((s, x) => s + x, 0) / ms.length, got = sizes.filter((x) => x !== null);
  const film = got.length ? n * got.reduce((s, x) => s + x, 0) / got.length : null;
  // a few places can miss the busiest stretches (measured: a film up to twice what its samples said), so it is a range
  const more = film === null ? null : Math.max(0, 2 * film - keptBytes);
  console.log(`  estimate (${ms.length} frames drawn in one browser, ${Math.min(...ms).toFixed(0)}–${Math.max(...ms).toFixed(0)} ms each): ${nTodo} frames in about ` +
    `${ftime(nTodo * mean / 1000 / W)} with ${W} worker${W === 1 ? "" : "s"} (more when they share a GPU or the machine is busy)` +
    (film === null ? "; the size could not be measured" : `; the video ${size(film)}–${size(2 * film)} (x264 crf ${o.crf} ${o.preset} on those frames), ` +
      `${size(more)}–${size(more + 2 * film)} more on that disk at the peak (the chunks, then the joined copy), ${size(free)} free${more + 2 * film > free ? ": it may not fit" : ""}`));
  if (more !== null && more > free) { await first.close(); keepFinished(); die(`about ${size(more)} is needed at the peak and ${size(free)} is free on that disk: free some, or a higher --crf; --no-estimate renders without measuring`); }
} else if (peak(0.4) > free) console.log(`  disk: about ${gb(peak(0.06))}–${gb(peak(0.4))} GB needed at the peak for ${peakOf} (more for grain, 3D, photos), ${gb(free)} GB free: it may not fit`);

const glyphs = [], fileOf = plan.map((_, i) => (reuse.has(i) ? kept(i) : null));
const T0 = Date.now(), problems = [];
activityProgress(0, nTodo, "frames");
const progress = setInterval(() => {
  if (done) console.log(`  ${done} / ${nTodo} frames · ${((Date.now() - T0) / 1000).toFixed(0)} s · about ${(((Date.now() - T0) / done) * (nTodo - done) / 1000).toFixed(0)} s to go`);
  activityProgress(done, nTodo, "frames");
}, 15000);
progress.unref();

// one chunk into its own encoder; → { encoded: a promise that settles once the encoder is done with it } (the browser goes
// on to the next chunk meanwhile). A chunk is kept for a resume only when every frame went in and the page reported nothing
async function chunk(film, i) {
  const [a, b] = plan[i], file = path.join(parts, `part${String(i).padStart(4, "0")}.new.mp4`), ff = x264(file);
  encoders.add(ff);
  let ffErr = ""; ff.stderr.on("data", (d) => { ffErr = (ffErr + d).slice(-2000); });
  const closed = new Promise((ok) => ff.on("close", (code, sig) => ok(code ?? sig)));
  // an encoder that stops early (a full disk, a frame it refuses) ends the render: nothing waits on a pipe no one reads
  let gone = false, wrote = 0, said = false;
  const exited = new Promise((ok) => ff.once("exit", () => { gone = true; encoders.delete(ff); ok(); }));
  ff.stdin.on("error", () => { /* the encoder is gone: exited says so */ });
  try {
    for (let k = a; k < b && !gone; k++) {
      const t = k / fps;
      const { png: img } = await within(film.frame(t, capture), o.frameTimeout, `t=${t.toFixed(3)} s`);
      const later = film.problems();
      if (later.length) { problems.push(`t=${t.toFixed(3)} s: ${later.join(" | ")}`); said = true; }
      if (!ff.stdin.write(img)) await Promise.race([new Promise((ok) => ff.stdin.once("drain", ok)), exited]);
      if (gone) break;
      wrote++; done++;
    }
  } catch (e) { failWith(e.message); }
  ff.stdin.end();
  return { encoded: closed.then((code) => {
    if (code !== 0 || wrote < b - a) return failWith(`the encoder for frames ${a}–${b - 1} ${wrote < b - a ? `stopped after ${wrote} of them` : "failed"} (exit ${code}): ${ffErr.trim() || "no message"}`);
    if (said) { fileOf[i] = file; return; }   // in this video, not for a resume: drawn again next time, and said again
    writePlan(film); fs.renameSync(file, kept(i)); fileOf[i] = kept(i);
  }) };
}
let next = 0;
async function worker(w) {
  let film = w === 0 ? first : null;
  const encoding = [];
  try {
    if (!film) film = await openFilm(target, { ...o, runtime: "auto", prelude: [HOOK] });
    while (!failed && next < todo.length) encoding.push((await chunk(film, todo[next++])).encoded);
  } catch (e) { failWith(e.message); }
  await Promise.all(encoding);
  // the characters this worker drew, each in the font it asked for? (tools/film/glyphs.mjs; a finding is reported, not fatal)
  // (canvas text is noted as it is drawn; the DOM's text as it stands after this worker's last frame)
  // (never in the way of the render: a minute at most, then it is said to be unchecked)
  if (film && !failed) {
    try { glyphs.push(await within((async () => { await collectDom(film); return checkGlyphs(film); })(), 60, "the glyph check")); }
    catch (e) { glyphs.push({ error: /no picture after/.test(e.message) ? "it did not finish within 60 s" : e.message }); }
  }
  if (film) await film.close();
}

await Promise.all(Array.from({ length: W }, (_, w) => worker(w)));
if (!W) await first.close();
clearInterval(progress);
const fail = (msg) => { const k = keepFinished(); console.error(`render: ${msg}`); if (k) console.error(`  ${keptSay(k)}`); process.exit(1); };
if (failed) fail(failed);
// each chunk's length in frames: an MP4's own duration is rounded to its movie timescale (1/1000 s), which would move the
// chunk after it by a few ticks when a GOP is not a whole number of milliseconds (--gop 20 at 30 fps)
fs.writeFileSync(path.join(parts, "list.txt"), plan.map(([a, b], i) => `file '${path.basename(fileOf[i])}'\nduration ${((b - a) / fps).toFixed(9)}`).join("\n") + "\n");
// joined inside the parts folder and moved onto <out> whole (through the project's versions): a join cut short (Ctrl-C)
// never replaces an earlier video
const joined = path.join(parts, `joined${path.extname(outFile)}`);
const join = spawnSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", path.join(parts, "list.txt"), "-c", "copy", "-movflags", "+faststart", joined], { encoding: "utf8" });
if (join.status !== 0) fail(`joining the chunks failed: ${(join.stderr || join.signal || "").toString().trim()}`);
// the frame count the MP4 records (counting by decoding would take minutes on a long 4K film)
const probe = spawnSync("ffprobe", ["-v", "error", "-select_streams", "v:0", "-show_entries",
  "stream=nb_frames,width,height,pix_fmt,color_range,color_space,color_primaries,color_transfer", "-of", "json", joined], { encoding: "utf8" });
const st = JSON.parse(probe.stdout || "{}").streams?.[0] || {};
const secs = (Date.now() - T0) / 1000;
const sidecar = {
  note: "how this video was made (bin/vh render); a patch or re-render should match these",
  // from the video's folder when the video is in the project (it moves with it), else where the page is
  page: (() => {   // first.root is a real path (host.mjs), so the video's folder is compared as one too (macOS /tmp is /private/tmp)
    const dir = fs.realpathSync(path.dirname(outFile)), page = path.join(first.root, path.basename(first.page));
    return inside(dir, first.root) ? path.relative(dir, page) : first.page;
  })(),
  kind: first.kind, width: first.width, height: first.height, dpr: o.dpr, pixels: [st.width, st.height], fps, frames: n,
  span: [+(k0 / fps).toFixed(6), +(k1 / fps).toFixed(6)], first_frame: k0, capture: png ? "png" : `jpeg q${o.quality}`,
  encoder: { codec: "libx264", crf: o.crf, preset: o.preset, gop, keyint_min: gop, sc_threshold: 0, pix_fmt: st.pix_fmt, color: [st.color_range, st.color_space, st.color_primaries, st.color_transfer] },
  chunks: plan.map(([a, b]) => [a, b]), reused_chunks: reuse.size, browser: first.version, real_clock: !!o.realClock, soft_gl: !!o.softGl, seconds: +secs.toFixed(1),
  ...(pageShots.length ? { shots: pageShots } : {}), ...(pageChapters.length ? { chapters: pageChapters } : {}),
  // the files the page loaded (plan.json's table, which goes with the parts): those in the page's folder, from it, sorted
  files: Object.fromEntries([...loaded].filter(([f]) => inside(f, first.root)).map(([f, h]) => [path.relative(first.root, f).split(path.sep).join("/"), h])
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))),
};
const sideTmp = joined + ".render.json";
fs.writeFileSync(sideTmp, JSON.stringify(sidecar, null, 1) + "\n");
const okCount = +st.nb_frames === n, okColor = st.pix_fmt === "yuv420p" && st.color_range === "tv" && st.color_space === "bt709";
// the new film in place: the one it replaces kept as an earlier version first (tools/film/versions.mjs)
const ver = commit({ film: outFile, new: joined, new_sidecar: sideTmp, made_by: "render", note, changed: { whole: true },
  problems: problems.length + (okCount ? 0 : 1) + (okColor ? 0 : 1) });
fs.rmSync(parts, { recursive: true, force: true });
const placed = ver.placed, placedShown = placed === outFile ? shown : rel(placed);
activityProgress(nTodo, nTodo, "frames");
activityNote(`${st.nb_frames} frames, ${st.width}x${st.height}, ${fps} fps, ${(k0 / fps).toFixed(2)}–${(k1 / fps).toFixed(2)} s, in ${secs.toFixed(0)} s` +
  (reuse.size ? ` (${reuse.size} chunk(s) kept from a stopped run)` : "") + (problems.length ? ` · ${problems.length} problem(s) reported` : "") +
  (ver.id ? ` · version ${ver.id}` : "") + (ver.error ? ` · ${ver.lines[0]}` : ""), [placed, placed + ".render.json"]);
console.log(`  ${placedShown}: ${st.nb_frames} frames, ${st.width}x${st.height}, ${st.pix_fmt} ${st.color_range}/${st.color_space}, in ${secs.toFixed(0)} s` +
  (nTodo ? ` (${(secs * 1000 / nTodo).toFixed(0)} ms a frame${reuse.size ? `, ${nTodo} of them drawn` : ""})` : " (every chunk kept)") + `; how it was made: ${outside ? placed + ".render.json" : rel(placed + ".render.json")}`);
for (const l of ver.lines) console.log(`  ${l}`);
for (const p of problems) console.log(`  ${p}`);
{   // a character in another font than it asks for, or in none: said, not fatal
  const okG = glyphs.filter((g) => !g.error), errG = glyphs.filter((g) => g.error);
  const [lines, wrong] = okG.length ? glyphReport(mergeGlyphs(okG)) : [[], false];
  if (wrong) { console.log("  glyphs: characters not drawn in the font they ask for (bin/vh fonts check lists them all):"); for (const l of lines.filter((x) => /^[✗!]/.test(x))) console.log("    " + l); }
  if (errG.length) console.log(`  glyphs: ${errG.length} of ${glyphs.length} worker(s) could not check theirs (${errG[0].error}); bin/vh fonts check does it on its own`);
  // a resume draws only the chunks left; the kept ones come from a render that stopped before its own check
  if (reuse.size && (!W || okG.some((g) => g.chars))) console.log(`  glyphs: ${W ? `checked in the ${nTodo} frames drawn now; the` : "not checked: every chunk was kept, so no frame was drawn; the"} ` +
    `${n - nTodo} frames of the ${reuse.size} kept chunk(s) were drawn by the render that stopped, before its check (bin/vh fonts check covers the whole film)`);
}
if (!okCount) console.log(`  the video has ${st.nb_frames} frames, not ${n}`);
if (!okColor) console.log(`  the colour tags are not yuv420p tv/bt709`);
if (problems.length || !okCount || !okColor || placed !== outFile) process.exit(1);
if (!process.env.OVH_RENDER_PIECE) console.log("render: done · the sound goes on with bin/vh mux");   // a piece of bin/vh patch is a step (patch sets it): patch says when it is done
