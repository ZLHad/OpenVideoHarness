// An edit list's film (engines/EDIT.md) for the page tools: bin/vh render, frames, determinism, cues and patch draw it
// through this. <project>/edit.json is resolved by tools/edit.py (python3 tools/edit.py build --json: every entry in
// whole frames, the runs to draw); each run is drawn its own way, and a frame of the film is the frame of the run it falls
// in, at that run's own time:
//   page   the entry's page through the host (tools/film/host.mjs), served from the edit list's folder: a film-clock page
//          at the film's t = k / fps (as if it were rendered alone), a local-clock page at u = in + (k − K0) · speed / fps
//          (K0: the entry's first frame); past the page's end only with "hold" (its last frame), else refused
//   still  an image, by the host's own page tools/film/pages/still.html (its fit and its move at p = (k − K0) / its frames)
//   slate  an entry with no source yet: tools/film/pages/slate.html, a grey card with its id and reads
//   color  tools/film/pages/color.html
// A film is a pure function of its frame: which run it is in and that run's time are data (the resolved edit list), and
// each way of drawing is a pure function of its time. One EditFilm keeps up to two pages open at a time (each its own
// browser), the least used closed first; the host's own pages are opened once and given each run's params.
//
// node tools/film/edit.mjs facts <project> --browser <chrome>: each page source's length, size, cues, time sources, shots
// and chapters as JSON (bin/vh edit check reads them).
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { openFilm, HostError } from "./host.mjs";
import { frameAt, frameFrom } from "./timegrid.mjs";

const HERE = path.dirname(new URL(import.meta.url).pathname);
export const EDIT = "edit.json";
export const PAGES_DIR = path.join(HERE, "pages");
export class EditError extends Error { constructor(msg, code = 2) { super(msg); this.code = code; } }

// the project an edit list lays out, for a target: a folder with edit.json, or edit.json itself; null for anything else
// (a page given by its file is that page alone). A folder with shots.json as well has two shot tables: refused
export function editProject(target) {
  let p;
  try { p = path.resolve(target); } catch { return null; }
  let st; try { st = fs.statSync(p); } catch { return null; }
  if (st.isFile()) return path.basename(p) === EDIT ? fs.realpathSync(path.dirname(p)) : null;
  if (!st.isDirectory() || !fs.existsSync(path.join(p, EDIT))) return null;
  return fs.realpathSync(p);
}

// the resolved edit list (tools/edit.py build --json), written to out/edit.resolved.json on the way; EditError (its
// problems as tools/edit.py printed them, its exit code) when it does not resolve
export function build(project, write = true) {
  const r = spawnSync("python3", [path.join(HERE, "..", "edit.py"), "build", project, "--json", ...(write ? [] : ["--no-write"])], { encoding: "utf8", maxBuffer: 1 << 28 });
  if (r.status !== 0) throw new EditError((r.stderr || r.stdout || `tools/edit.py exited ${r.status}`).trim(), r.status === 1 ? 1 : 2);
  try { return JSON.parse(r.stdout); } catch { throw new EditError("tools/edit.py build gave no JSON"); }
}

export const sha256 = (f) => {
  const h = crypto.createHash("sha256"), fd = fs.openSync(f, "r"), buf = Buffer.alloc(1 << 22);
  try { for (let n; (n = fs.readSync(fd, buf, 0, buf.length, null)) > 0;) h.update(buf.subarray(0, n)); } finally { fs.closeSync(fd); }
  return h.digest("hex");
};
const urlOf = (rel) => "/" + rel.split("/").map(encodeURIComponent).join("/");
const cjk = (s) => /[㐀-鿿豈-﫿]/.test(String(s || ""));

// how a run draws its frames, without where it sits: two runs with the same key and the same index for a frame draw the
// same picture there (bin/vh patch compares the runs outside what it draws again; the chunk keys hold it too). The index
// is the film's frame for a film-clock page, the frame from the run's start for everything else
export function drawingKey(run) {
  const n = run.frames[1] - run.frames[0];
  if (run.draw === "page") return run.clock === "film" ? { draw: "page", path: run.path, clock: "film", hold: !!run.hold }
    : { draw: "page", path: run.path, clock: "local", in: run.in, speed: run.speed, hold: !!run.hold };
  if (run.draw === "still") return { draw: "still", path: run.path, sha256: run.sha256, fit: run.fit, bg: run.bg, move: run.move || null, n };
  if (run.draw === "slate") return { draw: "slate", slate: run.slate, n };
  return { draw: run.draw, color: run.color, n };
}
export const indexOf = (run, k) => (run.draw === "page" && run.clock === "film" ? k : k - run.frames[0]);
// the window of frames [a, b) where two lists of runs draw anything differently, or null when they draw the same
export function differences(oldRuns, newRuns) {
  const at = (runs, k) => runs.find((r) => k >= r.frames[0] && k < r.frames[1]);
  const cuts = [...new Set([...oldRuns, ...newRuns].flatMap((r) => r.frames))].sort((x, y) => x - y);
  const out = [];
  for (let i = 0; i + 1 < cuts.length; i++) {
    const [a, b] = [cuts[i], cuts[i + 1]], p = at(oldRuns, a), q = at(newRuns, a);
    const same = p && q && JSON.stringify(drawingKey(p)) === JSON.stringify(drawingKey(q)) && indexOf(p, a) === indexOf(q, a);
    if (!same) { const l = out[out.length - 1]; if (l && l[1] === a) l[1] = b; else out.push([a, b]); }
  }
  return out;
}

// a page's facts: its length and size, how many cues it hangs on the narration, the time sources it reads (each with the
// sha256 of what it loaded), its shots and chapters as it gives them
export async function pageFacts(film, project) {
  const get = async (name) => { try { return await film.field(name); } catch { return null; } };
  const cues = await get("cues"), tl = await get("timeline"), music = await get("music"), map = await get("timemap");
  const pageDir = path.dirname(film.page), rel = (f) => path.relative(project, f).split(path.sep).join("/");
  let timeline = null;
  if (typeof tl === "string" && tl) { const f = path.resolve(pageDir, tl); try { timeline = { path: rel(f), sha256: sha256(f) }; } catch { timeline = { path: rel(f), sha256: null }; } }
  const src = (x) => (x && typeof x.path === "string" && typeof x.sha256 === "string" ? { path: rel(path.resolve(pageDir, x.path)), sha256: x.sha256 } : null);
  const fpsOf = +(await get("fps")) || null;
  return { duration: film.duration, width: film.width, height: film.height, fps: fpsOf, cues: Array.isArray(cues) ? cues.filter((c) => c && typeof c === "object") : [],
    timeline, music: src(music), timemap: src(map), shots: Array.isArray(await get("shots")) ? await get("shots") : null,
    chapters: Array.isArray(await get("chapters")) ? await get("chapters") : null, loadProblems: [...(film.loadProblems || [])] };
}

// every film-clock page reads the same narration timeline, beat map and time map as the edit list's refs (when it names
// one; else as the first such page): a line each that does not (tools/edit.py's check says the same)
export function timeSourceProblems(doc, facts) {
  const refs = Object.fromEntries((doc.refs || []).map((r) => [r.kind, r])), first = {}, out = [];
  for (const e of doc.entries) {
    const f = e.kind === "page" && e.clock === "film" ? facts[e.src] : null;
    if (!f || f.error) continue;
    for (const what of ["timeline", "music", "timemap"]) {
      const g = f[what];
      if (!g || !g.sha256) continue;
      const want = refs[what] || (first[what] ||= { ...g, by: e.id });
      if (g.sha256 !== want.sha256) out.push(`${e.id}: ${e.src} reads another ${what} (${g.path}) than ${refs[what] ? "edit.json's refs" : `${want.by}'s page (${want.path})`}: ` +
        "every film-clock page reads the same one; point them at one file, then bin/vh edit build");
    }
  }
  return out;
}

// what a page run needs of its page: up to the end of the entry, unless it holds its last frame
// → the page's own time at the entry's last frame when the page has ended by then (null: long enough, or held). A page draws
// its times before its duration, as frame_from counts them (a frame at its very end is past it)
export function pageShort(run, duration, fps) {
  if (run.hold) return null;
  const n = run.frames[1] - run.frames[0];
  const last = run.clock === "film" ? (run.frames[1] - 1) / fps : run.in + (n - 1) * run.speed / fps;
  return last * fps >= duration * fps - 1e-6 ? last : null;
}

export class EditFilm {
  // doc: the resolved edit list; o: openFilm's options (browser, dpr, realClock, softGl, prelude, frameTimeout)
  constructor(project, doc, o = {}) {
    this.project = project; this.doc = doc; this.o = o;
    this.root = project; this.page = path.join(project, EDIT); this.kind = "edit";
    this.fps = doc.fps; [this.width, this.height] = doc.size; this.duration = doc.frames / doc.fps; this.frames = doc.frames;
    this.version = null; this.loadProblems = [];
    this.open = new Map(); this.max = o.maxOpen || 2; this.tick = 0;
    this._served = new Set(); this._problems = []; this.checked = new Set(); this.durations = new Map();
    this.servedBy = new Map();   // a source (page:<path>, still, slate, color) → the files its page was sent, once it is closed
  }

  runAt(k) {
    const runs = this.doc.runs;
    let lo = 0, hi = runs.length - 1;
    while (lo < hi) { const mid = (lo + hi + 1) >> 1; if (runs[mid].frames[0] <= k) lo = mid; else hi = mid - 1; }
    const r = runs[lo];
    if (!r || k < r.frames[0] || k >= r.frames[1]) throw new EditError(`frame ${k} is outside the film (frames 0–${this.doc.frames - 1})`);
    return r;
  }
  sourceKey(run) { return run.draw === "page" ? `page:${run.path}` : run.draw; }
  isOpen(run) { return this.open.has(this.sourceKey(run)); }

  async film(run) {
    const key = this.sourceKey(run);
    let slot = this.open.get(key);
    if (!slot) {
      while (this.open.size >= this.max) {   // the least used one goes
        const [k, s] = [...this.open].sort((a, b) => a[1].used - b[1].used)[0];
        this.open.delete(k); await this.retire(s.film, k);
      }
      const file = run.draw === "page" ? path.join(this.project, run.path) : path.join(PAGES_DIR, `${run.draw}.html`);
      const film = await openFilm(file, { ...this.o, root: this.project, width: this.width, height: this.height, runtime: "auto",
        ...(run.draw === "page" ? {} : { params: this.params(run) }) });
      this.version = this.version || film.version;
      // what went wrong while it loaded is said with the first frame drawn from it (a page opens when a frame needs it)
      for (const p of film.loadProblems) this._problems.push(`while loading ${run.draw === "page" ? run.path : `the ${run.draw} page`}: ${p}`);
      if (run.draw === "page") this.durations.set(run.path, film.duration);
      slot = { film, used: 0, params: run.draw === "page" ? null : JSON.stringify(this.params(run)) };
      this.open.set(key, slot);
    }
    slot.used = ++this.tick;
    if (run.draw === "page" && !this.checked.has(run.entry)) {
      const short = pageShort(run, slot.film.duration, this.fps);
      if (short !== null) throw new EditError(`${run.entry}: ${run.path} is ${slot.film.duration} s long and the entry's last frame is at ${short.toFixed(3)} s of it: ` +
        "shorten the entry, or \"hold\": true to hold its last frame", 1);
      this.checked.add(run.entry);
    }
    if (run.draw !== "page") {
      const p = JSON.stringify(this.params(run));
      if (slot.params !== p) { await slot.film.setParams(this.params(run)); slot.params = p; }
    }
    return slot.film;
  }

  params(run) {
    const n = run.frames[1] - run.frames[0], base = { frames: n, fps: this.fps };
    if (run.draw === "still") return { ...base, image: urlOf(run.path), fit: run.fit, bg: run.bg, move: run.move || null };
    if (run.draw === "slate") return { ...base, ...run.slate, lang: cjk([run.slate.segment, run.slate.label, ...(run.slate.reads || []), run.slate.unsure].join(" ")) ? "zh" : "en" };
    return { ...base, color: run.color };
  }

  // the time a run's source is drawn at for film frame k (exact: render's), or for film seconds t (bin/vh frames --at)
  localK(run, k) {
    const K0 = run.frames[0];
    if (run.draw !== "page") return (k - K0) / this.fps;
    return this.hold(run, run.clock === "film" ? k / this.fps : run.in + (k - K0) * run.speed / this.fps);
  }
  localT(run, t) {
    const K0 = run.frames[0];
    if (run.draw !== "page") return Math.max(0, t - K0 / this.fps);
    return this.hold(run, run.clock === "film" ? t : run.in + (t - K0 / this.fps) * run.speed);
  }
  hold(run, u) {   // past a held page's end: its last frame, as the page drawn alone at this frame rate ends
    const d = this.durations.get(run.path);
    if (!run.hold || !(d > 0)) return u;
    const last = (frameFrom(d, this.fps) - 1) / this.fps;
    return u > last ? last : u;
  }

  async frameK(k, capture) { const run = this.runAt(k), f = await this.film(run); return f.frame(this.localK(run, k), capture); }
  // a moment on a frame is that frame, drawn as render draws it (the same float for a local clock's u = in + (k − K0)·speed/fps:
  // the other way round, in + (t − K0/fps)·speed, can differ in its last digit and floor to the frame before)
  async frame(t, capture) {
    const k = Math.round(t * this.fps);
    if (Math.abs(t * this.fps - k) < 1e-6) return this.frameK(k, capture);
    const run = this.runAt(frameAt(t, this.fps)), f = await this.film(run);
    return f.frame(this.localT(run, t), capture);
  }
  // a page closed (the least used, or all at the end): what it sent and reported is kept; o.onRetire(film) first (render's glyph check)
  async retire(film, key) {
    this._problems.push(...film.problems());   // what its frames reported, before the check below runs in it
    if (!this.servedBy.has(key)) this.servedBy.set(key, new Set());
    for (const x of film.served()) { this._served.add(x); this.servedBy.get(key).add(x); }
    if (this.o.onRetire) {
      try { await this.o.onRetire(film); } catch { /* said by the caller's own check */ }
      film.problems();   // the check's own DevTools reads (CSS.enable fetches the styles again: no-store, a cache miss) are not the film's
    }
    try { await film.close(); } catch { /* gone */ }
  }
  problems() { const out = this._problems.splice(0); for (const { film } of this.open.values()) out.push(...film.problems()); return out; }
  served() { const out = new Set(this._served); for (const { film } of this.open.values()) for (const x of film.served()) out.add(x); return [...out]; }
  async lateProblems() { const out = []; for (const { film } of this.open.values()) out.push(...(await film.lateProblems())); return out; }
  async field() { return null; }   // the edit list's own data is the resolved document; a page's fields: pageFacts
  async list() { return null; }
  send(method, params) { return Promise.all([...this.open.values()].map(({ film }) => film.send(method, params))); }
  async close() { for (const [k, s] of [...this.open]) { this.open.delete(k); await this.retire(s.film, k); } }
}

// an EditFilm with its first run's page open (the browser's version known), or a HostError / EditError
export async function openEdit(project, o = {}) {
  const doc = o.doc || build(project);
  const ef = new EditFilm(project, doc, o);
  try { await ef.film(doc.runs[0]); } catch (e) { await ef.close(); throw e; }
  return ef;
}

// the target as a film to draw: an edit list's EditFilm, or the page (host.mjs openFilm)
export async function openTarget(target, o = {}) {
  const project = editProject(target);
  return project ? openEdit(project, o) : openFilm(target, o);
}

// the entries as shots, then the shots inside the page entries, in the film's seconds (a local-clock page's moved to
// where it plays, cut to its entry); ids of the inner ones are <entry>.<shot>
export function shotsOf(doc, facts) {
  const fps = doc.fps, out = doc.entries.map((e) => ({ id: e.id, start: e.frames[0] / fps, end: e.frames[1] / fps, kind: e.kind, ...(e.at !== undefined ? { at: e.at } : {}) }));   // at: a storyboard tile's moment
  for (const e of doc.entries) {
    const f = e.kind === "page" ? facts[e.src] : null;
    if (!f || !Array.isArray(f.shots)) continue;
    const [a, b] = [e.frames[0] / fps, e.frames[1] / fps], to = (s) => (e.clock === "film" ? s : a + (s - e.in) / e.speed);
    for (const [i, s] of f.shots.entries()) {
      if (!s || !Number.isFinite(+s.start) || !Number.isFinite(+s.end)) continue;
      const s0 = Math.max(a, to(+s.start)), s1 = Math.min(b, to(+s.end));
      if (s1 > s0 + 1e-9) out.push({ id: `${e.id}.${s.id ?? `S${String(i + 1).padStart(2, "0")}`}`, start: +s0.toFixed(6), end: +s1.toFixed(6), kind: "shot" });
    }
  }
  return out;
}
// each page entry's cues in the film's seconds (a local-clock page's moved to where it plays), those inside the entry:
// [{ entry, src, path, clock, cues: [{ id: <entry>.<cue>, cue, ref, t }] }]
export function cuesOf(doc, facts) {
  const fps = doc.fps, out = [];
  for (const e of doc.entries) {
    const f = e.kind === "page" ? facts[e.src] : null;
    if (!f || f.error) continue;
    const [a, b] = [e.frames[0] / fps, e.frames[1] / fps], to = (u) => (e.clock === "film" ? u : a + (u - e.in) / e.speed);
    const cues = (f.cues || []).filter((c) => typeof c.t === "number" && Number.isFinite(c.t)).map((c) => ({ id: `${e.id}.${c.id}`, cue: c.id, ref: c.ref, t: +to(c.t).toFixed(6) }))
      .filter((c) => c.t >= a - 1e-9 && c.t < b);
    out.push({ entry: e.id, src: e.src, path: doc.files[e.src].path, clock: e.clock, all: (f.cues || []).length, cues, timeline: f.timeline || null });
  }
  return out;
}

// the film's chapters: the edit list's own, else each page entry's own, in the film's seconds, inside the entry
export function chaptersOf(doc, facts) {
  if (Array.isArray(doc.chapters) && doc.chapters.length) return doc.chapters.map((c) => ({ t: c.t, title: c.title, ...(c.id != null ? { id: c.id } : {}) }));
  const fps = doc.fps, out = [];
  for (const e of doc.entries) {
    const f = e.kind === "page" ? facts[e.src] : null;
    if (!f || !Array.isArray(f.chapters)) continue;
    const [a, b] = [e.frames[0] / fps, e.frames[1] / fps];
    for (const c of f.chapters) {
      if (!c || !Number.isFinite(+c.t)) continue;
      const t = e.clock === "film" ? +c.t : a + (+c.t - e.in) / e.speed;
      if (t >= a - 1e-9 && t < b) out.push({ t: +t.toFixed(6), title: String(c.title ?? ""), ...(c.id != null ? { id: String(c.id) } : {}) });
    }
  }
  return out.sort((p, q) => p.t - q.t);
}

// every page source once: {src: facts | {error}}
export async function allFacts(project, doc, o) {
  const out = {};
  for (const [src, f] of Object.entries(doc.files)) {
    if (f.kind !== "page") continue;
    let film = null;
    try { film = await openFilm(path.join(project, f.path), { ...o, root: project, width: doc.size[0], height: doc.size[1], runtime: "auto" }); out[src] = await pageFacts(film, project); }
    catch (e) { out[src] = { error: e.message.split("\n")[0] }; }
    finally { if (film) await film.close(); }
  }
  return out;
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const [cmd, target, flag, browser] = process.argv.slice(2);
  if (cmd !== "facts" || !target || flag !== "--browser" || !browser) { console.error("usage: node tools/film/edit.mjs facts <project> --browser <chrome>"); process.exit(2); }
  const project = editProject(target);
  if (!project) { console.error(`edit: no ${EDIT} in ${target}`); process.exit(2); }
  try { const doc = build(project, false); process.stdout.write(JSON.stringify(await allFacts(project, doc, { browser })) + "\n"); }
  catch (e) { console.error(`edit: ${e.message}`); process.exit(e instanceof HostError || e instanceof EditError ? 2 : 1); }
}
