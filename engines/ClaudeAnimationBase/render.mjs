// render.mjs: renders studio.html in headless Chrome. Length, fps and audio come from PROJECT in src/config.js, which is
// also read in Node, so --encode needs no page; --fps=… and --audio=… override it.
//
//   Look at it (open the images with your image viewer / Read tool):
//     node render.mjs --sheet=0.5,1,1.5,2 [--cols=4] [--w=480] --out=out/check/a.jpg        contact sheet of chosen times
//     node render.mjs --strip=2.0:2.5 [--cols=6] [--w=320] --out=out/check/strip.jpg        EVERY frame in a stretch (motion)
//     node render.mjs --sheet=2.1,2.2 --crop=760,300,400,400 --w=600 --out=out/check/face.jpg full-res crops (details)
//     node render.mjs --strip=2.0:2.5 --crop-at=960,780,500,400 --out=out/check/feet.jpg       crops that follow a WORLD point
//         (x,y in world px, may be page expressions like PLK.MX(1.38); w,h in screen px) through each frame's camera
//     node render.mjs --stills=1.2,3.4 --out=out/stills                                     full-res PNGs
//   Make the video:
//     node render.mjs --clip [--range=0:4] --out=out/video.mp4                               straight to MP4 (one worker)
//     node render.mjs --frames [--range=0:8] --workers=4                                     JPEG frames → out/frames (parallel, resumable)
//     node render.mjs --encode --out=out/video.mp4                                           out/frames → MP4 (checks the frame count)
//   Standalone loops (LOOPS in the page): add --loop=<name> to any of the above (times are then loop times; --frames and
//   --encode use out/frames_loop_<name> and write out/loop_<name>.mp4), or
//     node render.mjs --loop=emotions --png --out=out/loop_emotions                          one cycle as PNGs (for GIFs)
//   Music: --audio=assets/song.mp3 (or PROJECT.audio) is muxed into --clip and --encode, trimmed or padded with silence
//   (with a warning) to the video's exact length, so no frame is lost. Other flags: --fps=24 (or PROJECT.fps; --encode
//   defaults to the fps the frames were rendered at), --chrome=<path to Chrome/Chromium>.
//   Chrome is, in order: --chrome, $CHROME_PATH, Google Chrome's standard install (Windows, macOS, /usr/bin/google-chrome),
//   /usr/bin/chromium, /usr/bin/chromium-browser, then Playwright's Chromium in $PLAYWRIGHT_BROWSERS_PATH and in
//   ~/.cache/ms-playwright (chromium-NNNN/chrome-linux64/chrome or chromium-NNNN/chrome-linux/chrome, newest first).
import puppeteer from 'puppeteer-core';
import { spawn, execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, readFileSync, existsSync, statSync, renameSync, readdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { homedir } from 'node:os';
import vm from 'node:vm';

const args = Object.fromEntries(process.argv.slice(2).map(a => { const [k, ...v] = a.replace(/^--/, '').split('='); return [k, v.length ? v.join('=') : true]; }));
const CHROMES = [args.chrome, process.env.CHROME_PATH, 'C:/Program Files/Google/Chrome/Application/chrome.exe', 'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  ...playwrightChromes()];
// Chromium builds Playwright downloaded ($PLAYWRIGHT_BROWSERS_PATH first, then ~/.cache/ms-playwright), newest first
function playwrightChromes() {
  return [process.env.PLAYWRIGHT_BROWSERS_PATH, `${homedir()}/.cache/ms-playwright`].filter(dir => dir && existsSync(dir))
    .flatMap(dir => readdirSync(dir).filter(n => /^chromium-\d+$/.test(n)).sort((a, b) => b.split('-')[1] - a.split('-')[1])
      .flatMap(n => [`${dir}/${n}/chrome-linux64/chrome`, `${dir}/${n}/chrome-linux/chrome`]));
}
const CHROME = CHROMES.find(p => p && existsSync(p));
if (!CHROME) { console.error('Chrome not found: pass --chrome=<path> or set CHROME_PATH'); process.exit(1); }
// PROJECT, read in Node: config.js is a plain script, so it runs in a bare context with window/self. Every mode, --encode
// included, then agrees on fps, length and audio without opening the page.
const PROJECT = (() => { try { const g = vm.createContext({ console }); g.window = g.self = g; vm.runInContext(readFileSync('src/config.js', 'utf8'), g, { filename: 'src/config.js' }); return vm.runInContext('typeof PROJECT == "object" && PROJECT || {}', g); } catch (e) { console.warn(`couldn't read PROJECT from src/config.js (${e.message}): using --fps / --audio / defaults`); return {}; } })();
// A loop's frames get their own folder. frames.json there records what --frames rendered: { fps, frames }.
const FRAMES_DIR = args.loop ? `out/frames_loop_${args.loop}` : 'out/frames', MADE = (() => { try { return JSON.parse(readFileSync(`${FRAMES_DIR}/frames.json`, 'utf8')); } catch { return {}; } })();
const fps = +(args.fps || (args.encode && MADE.fps) || PROJECT.fps || 24), nOf = len => Math.ceil(len * fps - 1e-6);   // nOf: frames in len seconds
const run = (cmd, a) => new Promise((ok, bad) => { const p = spawn(cmd, a, { stdio: 'inherit' }); p.on('close', c => c ? bad(new Error(cmd + ' exited ' + c)) : ok()); });
// ffmpeg args for the audio under a video span: from `from` s into the file, trimmed or padded with silence to exactly
// dur s, so every rendered frame is kept (-shortest used to cut the picture when the audio ran out). Padding is announced.
const audioIn = (audio, from, dur) => {
  let len = NaN; try { len = +execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', audio], { stdio: ['ignore', 'pipe', 'ignore'] }); } catch {}   // unreadable: ffmpeg says why
  const pad = Math.min(dur, dur - (len - from));
  if (pad > .001) console.warn(`warning: ${audio} runs out ${pad.toFixed(3)} s before the video ends: padded with ${pad.toFixed(3)} s of silence. The audio should set the length: make PROJECT.duration match it.`);
  return ['-ss', String(from), '-t', String(dur), '-i', audio, '-map', '0:v', '-map', '1:a', '-af', `apad,atrim=0:${dur}`, '-c:a', 'aac', '-b:a', '192k'];
};
const times = s => String(s).split(',').map(Number);
const span = s => String(s).split(':').map(Number);
// comma-separated fields, keeping commas inside parentheses ('PLK.MX(1.38),PLK.WL,500,300'); numbers stay numbers
const fields = s => { const out = []; let d = 0, cur = ''; for (const ch of String(s)) { if (ch === ',' && !d) { out.push(cur); cur = ''; continue; } d += ch === '(' ? 1 : ch === ')' ? -1 : 0; cur += ch; } out.push(cur); return out.map(v => isNaN(+v) ? v : +v); };

if (args.encode) {
  // From the first frame on disk. The video should have PROJECT.duration × fps frames (a loop: as many as --frames
  // rendered), so files past that end (stale, from a longer cut) are left out, and missing frames are listed.
  const out = args.out || `out/${args.loop ? 'loop_' + args.loop : 'video'}.mp4`, audio = args.audio || PROJECT.audio || '';
  if (args.fps && MADE.fps && fps !== MADE.fps) console.warn(`warning: these frames were rendered at ${MADE.fps} fps; encoding them at ${fps} fps changes their speed`);
  const have = existsSync(FRAMES_DIR) ? readdirSync(FRAMES_DIR).filter(f => /^f\d{5}\.jpg$/.test(f)).map(f => +f.slice(1, 6)).sort((a, b) => a - b) : [];
  const n = !args.loop && PROJECT.duration > 0 ? nOf(PROJECT.duration) : MADE.frames, inside = i => !n || i < n, on = new Set(have);
  const name = i => `f${String(i).padStart(5, '0')}`, list = ids => ids.reduce((r, i) => { const l = r.at(-1); if (l && l[1] === i - 1) l[1] = i; else r.push([i, i]); return r; }, [])
    .map(([a, b]) => a === b ? name(a) : `${name(a)}–${name(b)}`).join(', ');
  const first = have.find(inside), past = have.filter(i => !inside(i)), missing = [];
  if (first === undefined) { console.error(`no frames to encode in ${FRAMES_DIR}${past.length ? ` before frame ${n}` : ''}: render them with --frames`); process.exit(1); }
  let end = first; while (on.has(end) && inside(end)) end++;   // ffmpeg reads first, first + 1, … and stops at the first gap
  for (let i = 0; i < (n || have.at(-1) + 1); i++) if (!on.has(i)) missing.push(i);
  // a hole between rendered frames is an interrupted or failed render, not a --range choice: encoding would silently stop at it
  const lastIn = have.filter(inside).at(-1), holes = missing.filter(i => i > first && i < lastIn);
  if (holes.length) { console.error(`${holes.length} frames missing between ${name(first)} and ${name(lastIn)}: ${list(holes)}. Render them with --frames (it resumes), then encode.`); process.exit(1); }
  if (past.length) console.warn(`warning: left out ${past.length} frames past the end (${n} frames at ${fps} fps): ${list(past)}. Stale from a longer cut? Delete them.`);
  if (missing.length) console.warn(`warning: ${missing.length} frames missing: ${list(missing)}. This video covers only ${(first / fps).toFixed(2)}–${(end / fps).toFixed(2)} s; render the rest with --frames.`);
  console.log(`encoding ${name(first)}–${name(end - 1)} (${end - first} frames at ${fps} fps) → ${out}${audio ? ' with ' + audio : ''}`);
  mkdirSync(dirname(out), { recursive: true });
  await run('ffmpeg', ['-y', '-loglevel', 'error', '-stats', '-framerate', String(fps), '-start_number', String(first), '-i', `${FRAMES_DIR}/f%05d.jpg`,
    ...(audio ? audioIn(audio, first / fps, (end - first) / fps) : []),
    '-frames:v', String(end - first), '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]);
  console.log('wrote ' + out);
  process.exit(0);
}

// --soft-gl: no GPU on this machine; render WebGL in software (SwiftShader), which Chrome only allows when asked. It also
// keeps 2D canvases on the CPU: accelerated 2D canvas on SwiftShader made frames differ on every launch (~39 dB PSNR
// between runs); on the CPU they are pixel-identical across runs and render orders, and faster. On every path,
// CanvasNoise is off: Chrome adds per-launch noise to readbacks of GPU-accelerated 2D canvases (fingerprinting
// protection), which was most of that difference, and GPU machines accelerate 2D canvas too.
// --gpu-angle=vulkan|gl-egl: headless Linux on an NVIDIA GPU (e.g. a cloud or cluster node); plain --use-gl=angle gets
// no WebGL context there. Check which GPU Chrome actually lands on with gpu_probe.mjs.
const ANGLE = { vulkan: ['--use-angle=vulkan', '--enable-features=Vulkan'], 'gl-egl': ['--use-angle=gl-egl'] };
if (args['gpu-angle'] && !ANGLE[args['gpu-angle']]) { console.error(`--gpu-angle must be one of ${Object.keys(ANGLE)}`); process.exit(1); }
const gpu = args['soft-gl'] ? ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--disable-accelerated-2d-canvas']
  : args['gpu-angle'] ? ANGLE[args['gpu-angle']]
  : process.platform === 'win32' ? ['--use-angle=d3d11'] : process.platform === 'darwin' ? ['--use-angle=metal'] : ['--use-gl=angle'];
// Ubuntu 23.10+ blocks Chrome's user-namespace sandbox; headless rendering of local files doesn't need it.
const sandbox = process.platform === 'linux' ? ['--no-sandbox'] : [];
const browser = await puppeteer.launch({
  executablePath: CHROME, headless: true, protocolTimeout: 0,
  args: [...sandbox, '--allow-file-access-from-files', '--ignore-gpu-blocklist', ...gpu, '--enable-gpu-rasterization', '--disable-features=CanvasNoise', '--window-size=1920,1080', '--disable-renderer-backgrounding', '--disable-background-timer-throttling']
});
async function openPage(tag = '') {
  const page = await browser.newPage();
  page.on('console', m => { if (['error', 'warn'].includes(m.type())) console.log(`[page${tag}]`, m.text()); });
  page.on('pageerror', e => console.log(`[page error${tag}]`, e.message));
  await page.goto(pathToFileURL(resolve('studio.html')).href + '?render', { waitUntil: 'networkidle0' });
  await page.waitForFunction('window.ready === true', { timeout: 60000 });
  if (args.loop) {
    const ok = await page.evaluate(name => { if (!LOOPS[name]) return false; window.LOOP = LOOPS[name]; return true; }, args.loop);
    if (!ok) { console.error(`no loop named "${args.loop}"`); process.exit(1); }
  }
  return page;
}
const frameOf = async (page, t, type, q) => {
  const url = await page.evaluate((t, type, q) => window.renderAt(t, type, q), t, type, q);
  return Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
};
// the length of whatever is being rendered: a loop's .len, or the video's duration
const lengthOf = page => page.evaluate(() => window.LOOP ? window.LOOP.len : DUR);

if (args.sheet || args.strip) {
  const page = await openPage(), out = args.out || 'out/sheet.jpg'; mkdirSync(dirname(out), { recursive: true });
  let ts;
  if (args.strip) { const [a, b] = span(args.strip); ts = []; for (let i = Math.round(a * fps); i <= Math.round(b * fps); i++) ts.push(i / fps); }
  else ts = times(args.sheet);
  const crop = args.crop ? times(args.crop) : null, at = args['crop-at'] ? fields(args['crop-at']) : null;
  const { url, ms } = await page.evaluate((ts, c, w, crop, at) => window.renderSheet(ts, c, w, crop, at), ts, +(args.cols || (args.strip ? 6 : 3)), +(args.w || (args.strip ? 320 : 640)), crop, at);
  writeFileSync(out, Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
  console.log(`${out}  (${ts.length} frames)  ms/frame: ${ms.join(' ')}`);
} else if (args.stills) {
  const page = await openPage(), out = args.out || 'out/stills'; mkdirSync(out, { recursive: true });
  console.log('GPU:', await page.evaluate(() => window.gpuInfo()));
  for (const s of times(args.stills)) {
    const t0 = Date.now(), buf = await frameOf(page, s, 'image/png');
    const f = `${out}/t${s.toFixed(2).replace('.', '_')}.png`; writeFileSync(f, buf);
    console.log(`${f}  ${Date.now() - t0} ms`);
  }
} else if (args.png) {
  // PNG sequence (for GIFs): a loop's full cycle (frame n equals frame 0, so it isn't rendered), or --range=a:b.
  const probe = await openPage(), len = await lengthOf(probe); await probe.close();
  const [a, b] = args.range ? span(args.range) : [0, len], n = Math.round((b - a) * fps);
  const out = args.out || `out/${args.loop ? 'loop_' + args.loop : 'png'}`, workers = +(args.workers || 3); mkdirSync(out, { recursive: true });
  let next = 0; const start = Date.now();
  await Promise.all(Array.from({ length: workers }, async (_, w) => {
    const page = await openPage('#' + w);
    while (next < n) { const i = next++; writeFileSync(`${out}/f${String(i).padStart(4, '0')}.png`, await frameOf(page, a + i / fps, 'image/png')); }
  }));
  console.log(`${n} frames → ${out}  (${((Date.now() - start) / n).toFixed(0)} ms/frame)`);
} else if (args.frames) {
  // Parallel and resumable: each worker pulls the next missing frame; files are written atomically.
  if (MADE.fps && MADE.fps !== fps && readdirSync(FRAMES_DIR).some(f => f.endsWith('.jpg'))) { console.error(`${FRAMES_DIR} holds frames rendered at ${MADE.fps} fps, not ${fps}: pass --fps=${MADE.fps}, or delete them first`); process.exit(1); }
  const probe = await openPage(), len = await lengthOf(probe); await probe.close();
  const [a, b] = args.range ? span(args.range) : [0, len], workers = +(args.workers || 4);
  mkdirSync(FRAMES_DIR, { recursive: true }); writeFileSync(`${FRAMES_DIR}/frames.json`, JSON.stringify({ fps, frames: nOf(len) }) + '\n');
  const first = Math.round(a * fps), last = Math.min(nOf(len) - 1, Math.round(b * fps) - 1);
  const todo = []; for (let i = first; i <= last; i++) { const f = `${FRAMES_DIR}/f${String(i).padStart(5, '0')}.jpg`; if (!existsSync(f) || statSync(f).size < 1000) todo.push(i); }
  console.log(`${todo.length} frames to render (${last - first + 1 - todo.length} already done), ${workers} workers`);
  let next = 0, done = 0; const start = Date.now();
  await Promise.all(Array.from({ length: workers }, async (_, w) => {
    const page = await openPage('#' + w);
    while (next < todo.length) {
      const i = todo[next++], f = `${FRAMES_DIR}/f${String(i).padStart(5, '0')}.jpg`;
      const buf = await frameOf(page, i / fps, 'image/jpeg', .94);
      writeFileSync(f + '.tmp', buf); renameSync(f + '.tmp', f);
      if (++done % 24 === 0 || done === todo.length) {
        const el = (Date.now() - start) / 1000;
        console.log(`frame ${done}/${todo.length}  ${(el / done * 1000).toFixed(0)} ms/frame effective  eta ${((todo.length - done) * el / done / 60).toFixed(1)} min`);
      }
    }
  }));
} else if (args.clip) {
  const page = await openPage(), len = await lengthOf(page);
  const [a, b] = args.range ? span(args.range) : typeof args.clip === 'string' ? span(args.clip) : [0, len];
  const audio = args.audio || await page.evaluate(() => PROJECT.audio || '');
  const out = args.out || 'out/clip.mp4', n = Math.round((b - a) * fps); mkdirSync(dirname(out), { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
    ...(audio ? audioIn(audio, a, n / fps) : []),
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  let code = null; const done = new Promise(r => ff.on('close', (c, sig) => r(code = c ?? sig)));
  ff.stdin.on('error', () => {});   // ffmpeg quit early: stop feeding it (its exit code is reported below)
  const start = Date.now();
  for (let i = 0; i < n && code === null; i++) {
    const buf = await frameOf(page, a + i / fps, 'image/jpeg', .93);
    if (!ff.stdin.write(buf)) await Promise.race([new Promise(r => ff.stdin.once('drain', r)), done]);
    if (i % 24 === 0 || i === n - 1) console.log(`frame ${i + 1}/${n}  ${((Date.now() - start) / (i + 1)).toFixed(0)} ms/frame`);
  }
  ff.stdin.end(); await done;
  if (code) { console.error(`ffmpeg failed (${code}): ${out} is broken or incomplete`); process.exitCode = 1; } else console.log(`wrote ${out}`);
} else {
  console.log('nothing to do: see the usage notes at the top of render.mjs');
}
await browser.close();
