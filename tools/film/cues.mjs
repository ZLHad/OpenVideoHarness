// cues: where a page's cues landed (window.film.cues, engines/CONTRACT.md): every time it hangs on the narration's words
// ("@b2:跟着走", "@a2>"), resolved in seconds, in order. With --save it keeps them in out/cues.json together with the
// sha256 of the timeline they were resolved on (window.film.timeline); when that file is there, a later run says which
// cues moved and by how much, which are new and which are gone: after a new take of the narration (pauses put in, a line
// rewritten), or after the page's own cues changed on the same take. Music references also record the
// loaded beat-map source and hash (window.film.music), so a changed score map is named on the next run; a time map's
// events ("@#id", mapAt) record the time map's (window.film.timemap) the same way.
//
// usage: node tools/film/cues.mjs <project | page.html> --browser <chrome> [--save] [--out out/cues.json] [--chapters] [--frame-timeout 120]
//
// --frame-timeout 120: a read of the page (its cues, timeline, music, time map, chapters) not back after this many
// seconds stops it (exit 2), as a frame does in bin/vh frames: a getter that never returns, or a page whose script is
// stuck. OVH_PAGE_TIMEOUT=S: how long the page may take to set window.film and to be ready (tools/film/host.mjs).
//
// --chapters: the film's chapters (window.film.chapters, the engine's own table) as the lines a video description takes,
// "0:00 title", each at least half a second before its chapter starts (whole seconds, rounded down: 0.5 to 1.5 s
// early; the first at 0:00), also
// written to out/chapters.txt; it says what YouTube needs before it shows them (at least three, the first at 0:00,
// each at least 10 s). After a new take of the narration, run it again.
//
// A project with an edit list (edit.json, engines/EDIT.md) has two layers, both listed and both saved: the edit list's own
// times (each entry's start and end, as written: seconds or a cue on the narration, the beats, a time map; its chapters),
// resolved by tools/edit.py; and each page entry's cues, in the film's seconds (a local-clock page's moved to where it
// plays), those inside the entry. The next run says which entries moved and by how much ("S03–S07 moved +0.420 s"), and
// which page cues moved, are new or gone. A local-clock page that hangs cues on the narration is said: they land in its
// own time, not the film's. --chapters takes the edit list's chapters, else its pages'.
// A cue that no longer resolves stops the page in ready, so the host's message names it and this exits 2.
// Exit: 0 listed · 2 could not open the page, it gives no window.film.cues, or --save cannot write the file.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { openFilm } from "./host.mjs";
import { allFacts, build as buildEdit, chaptersOf, cuesOf, editProject } from "./edit.mjs";   // edit lists (engines/EDIT.md)
import "./activity.mjs";   // bin/vh exec's into this: the run's end line in the project's activity log

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP.trimEnd() + "\n"); process.exit(argv.length ? 0 : 2); }
const die = (msg) => { console.error("cues: " + msg); process.exit(2); };
let target = null, out = null, browser = null, save = false, chapters = false, frameTimeout = 120;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], next = () => { const v = argv[++i]; if (v === undefined) die(`${a} needs a value`); return v; };
  if (a === "--out") out = next();
  else if (a === "--frame-timeout") { const v = next(); frameTimeout = Number(v); if (v === "" || !(frameTimeout >= 1)) die(`--frame-timeout: ${JSON.stringify(v)} is not a number of seconds ≥ 1`); }
  else if (a === "--save") save = true;
  else if (a === "--chapters") chapters = true;
  else if (a === "--browser") browser = next();
  else if (a.startsWith("-")) die(`unknown option ${a} (-h for the options)`);
  else if (target) die(`one project or page, got ${target} and ${a}`);
  else target = a;
}
if (!target) die("which project or page? (-h for the usage)");
if (!browser) die("no browser: pass --browser <chrome>, or run it as bin/vh cues");
const editRoot = editProject(target);
if (editRoot) { await editCues(editRoot); process.exit(0); }

// ---- an edit list: its own times, then each page entry's cues ----
async function editCues(root) {
  let doc, facts;
  try { doc = buildEdit(root, false); } catch (e) { die(e.message.replace(/^edit: /, "")); }
  try { facts = await allFacts(root, doc, { browser, frameTimeout }); } catch (e) { die(e.message); }
  const bad = Object.entries(facts).filter(([, f]) => f.error);
  if (bad.length) die(bad.map(([src, f]) => `${doc.files[src].path}: ${f.error}`).join("\n  "));
  const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
  const two = (x) => String(Math.floor(x)).padStart(2, "0"), mmss = (s) => (s >= 3600 ? `${Math.floor(s / 3600)}:${two((s % 3600) / 60)}:${two(s % 60)}` : `${Math.floor(s / 60)}:${two(s % 60)}`);
  if (chapters) {   // the description's chapter list, as for a page
    const chs = chaptersOf(doc, facts);
    if (!chs.length) die("the edit list has no chapters (edit.json's chapters, or its pages' window.film.chapters)");
    const at = chs.map((c, i) => (i === 0 ? 0 : Math.max(0, Math.floor(c.t - 0.5)))), lines = chs.map((c, i) => `${mmss(at[i])} ${c.title}`);
    console.log(`chapters: ${rel(path.join(root, "edit.json"))} · ${chs.length}, each 0.5 to 1.5 s before it starts (whole seconds; the first at 0:00)`);
    for (const l of lines) console.log("  " + l);
    if (chs.length < 3) console.log("  YouTube shows chapters only when there are at least three");
    for (const [i, s] of at.entries()) { const d = (i + 1 < at.length ? at[i + 1] : doc.frames / doc.fps) - s; if (d < 10) console.log(`  YouTube shows chapters only when each lasts 10 s or more: "${chs[i].title}" lasts ${d.toFixed(0)} s`); }
    const file = path.join(root, "out", "chapters.txt");
    try { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, lines.join("\n") + "\n"); console.log(`  written: ${rel(file)}`); } catch (e) { die(`cannot write ${rel(file)}: ${e.message}`); }
    return;
  }
  const entries = doc.entries.map((e) => ({ id: e.id, start: e.start, end: e.end, ...(e.ref ? { ref: e.ref } : {}) }));
  const pages = cuesOf(doc, facts);
  const tl = (doc.refs || []).find((r) => r.kind === "timeline");
  console.log(`cues: ${rel(path.join(root, "edit.json"))} · ${entries.length} entr${entries.length === 1 ? "y" : "ies"}, ${entries.filter((e) => e.ref && Object.values(e.ref).some((v) => typeof v !== "number")).length} hanging on references` +
    (tl ? ` (on ${tl.path}, sha256 ${tl.sha256.slice(0, 12)})` : " (edit.json's refs name no timeline)"));
  const w = Math.max(4, ...entries.map((e) => e.id.length));
  console.log(`  ${"start".padStart(8)}  ${"end".padStart(8)}  ${"id".padEnd(w)}  written`);
  for (const e of entries) console.log(`  ${e.start.toFixed(3).padStart(8)}  ${e.end.toFixed(3).padStart(8)}  ${e.id.padEnd(w)}  ${e.ref ? Object.entries(e.ref).map(([k, v]) => `${k} ${JSON.stringify(v)}`).join(", ") : "follows"}`);
  for (const c of doc.chapters || []) if (c.ref !== undefined) console.log(`  ${c.t.toFixed(3).padStart(8)}  ${"".padStart(8)}  ${"chapter".padEnd(w)}  ${c.title}: ${JSON.stringify(c.ref)}`);
  for (const p of pages) {
    console.log(`  ${p.entry}: ${p.path} (${p.clock} clock) · ${p.cues.length} cue${p.cues.length === 1 ? "" : "s"} inside the entry` + (p.all > p.cues.length ? ` (${p.all} on the page)` : ""));
    if (p.clock === "local" && p.all) console.log(`    ! ${p.path} is on its own clock and hangs ${p.all} cue${p.all === 1 ? "" : "s"} on the narration: they land in its own time, not the film's (did you mean "clock": "film"?)`);
    for (const c of p.cues) console.log(`    ${c.t.toFixed(3).padStart(8)}  ${String(c.cue).padEnd(w)}  ${c.ref}`);
  }
  // against the saved ones: entries that moved (a row moved by the same amount is one line), page cues moved, new, gone
  const file = path.resolve(out || path.join(root, "out", "cues.json"));
  let before = null;
  if (fs.existsSync(file)) {
    try { before = JSON.parse(fs.readFileSync(file, "utf8")); if (!before || !Array.isArray(before.entries)) throw new Error("not an edit list's"); }
    catch { before = null; console.log(`  ${rel(file)}: not readable as an edit list's saved cues, so not compared`); }
  }
  if (before) {
    const old = new Map(before.entries.map((e) => [e.id, e])), moved = [];
    entries.forEach((e, i) => {
      const p = old.get(e.id); if (!p) return;
      const d = +(e.start - p.start).toFixed(3);
      if (!d) return;
      const l = moved[moved.length - 1];
      if (l && l.d === d && l.i === i - 1) { l.to = e.id; l.i = i; } else moved.push({ from: e.id, to: e.id, d, i });
    });
    const tlOld = (before.refs || []).find((r) => r.kind === "timeline");
    const why = tl && tlOld && tl.sha256 !== tlOld.sha256 ? " (another take of the narration)" : "";
    const lines = moved.map((m) => `${m.from === m.to ? m.from : `${m.from}–${m.to}`} moved ${m.d > 0 ? "+" : "−"}${Math.abs(m.d).toFixed(3)} s${why}`);
    for (const e of entries) { const p = old.get(e.id); if (p && +(e.end - e.start).toFixed(3) !== +(p.end - p.start).toFixed(3)) lines.push(`${e.id} is ${e.end - e.start > p.end - p.start ? "longer" : "shorter"} by ${Math.abs((e.end - e.start) - (p.end - p.start)).toFixed(3)} s`); }
    for (const e of entries) if (!old.has(e.id)) lines.push(`${e.id} is new`);
    for (const id of old.keys()) if (!entries.some((e) => e.id === id)) lines.push(`${id} is gone`);
    const oc = new Map((before.pages || []).flatMap((p) => (p.cues || []).map((c) => [c.id, c]))), nc = new Map(pages.flatMap((p) => p.cues.map((c) => [c.id, c])));
    for (const [id, c] of nc) { const p = oc.get(id); if (p && Math.abs(p.t - c.t) >= 0.0005) lines.push(`${id} moved ${c.t > p.t ? "+" : "−"}${Math.abs(c.t - p.t).toFixed(3)} s (${p.t.toFixed(3)} → ${c.t.toFixed(3)})`); else if (!p) lines.push(`${id} is new`); }
    for (const id of oc.keys()) if (!nc.has(id)) lines.push(`${id} is gone`);
    console.log(`  since ${rel(file)}:${lines.length ? "" : " nothing moved"}`);
    for (const l of lines.slice(0, 30)) console.log(`    ${l}`);
    if (lines.length > 30) console.log(`    … and ${lines.length - 30} more`);
  }
  if (save) {
    try {
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, JSON.stringify({ note: "bin/vh cues --save: where an edit list's entries and its pages' cues landed, and the time sources they were resolved on",
        edit: path.relative(path.dirname(file), path.join(root, "edit.json")), edit_sha256: doc.edit.sha256, refs: doc.refs, entries,
        pages: pages.map(({ all, ...p }) => p) }, null, 1) + "\n");
    } catch (e) { die(`cannot write ${rel(file)}: ${e.message}`); }
    console.log(`  saved: ${rel(file)}`);
  }
}

let film;
try { film = await openFilm(target, { browser, runtime: "auto", frameTimeout }); } catch (e) { die(e.message); }
// each read of the page: back within --frame-timeout, or the run stops there and says which
const timely = (p, what) => {
  let timer;
  p.catch(() => { /* given up on */ });
  return Promise.race([p, new Promise((_, no) => { timer = setTimeout(() => no(Object.assign(new Error(`reading window.film.${what}: no answer after ${frameTimeout} s ` +
    "(--frame-timeout): a getter that never returns, or the page's script is stuck"), { stuck: true })), frameTimeout * 1000); })]).finally(() => clearTimeout(timer));
};
let cues, tlRel, musicSource, mapSource, chs = null;
try { cues = await timely(film.list("cues"), "cues"); tlRel = await timely(film.field("timeline"), "timeline").catch((e) => { if (e.stuck) throw e; return null; });
  musicSource = await timely(film.field("music"), "music"); mapSource = await timely(film.field("timemap"), "timemap").catch((e) => { if (e.stuck) throw e; return null; });
  if (chapters) chs = await timely(film.list("chapters"), "chapters"); }
catch (e) { await film.close(); die(e.message); }
const loadProblems = film.loadProblems, duration = film.duration;
await film.close();
const rel0 = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
if (chapters) {   // the description's chapter list, from the engine's own chapter table
  if (!chs || !chs.length) die(`${film.page} gives no window.film.chapters (canvas-film: CHAPTERS in src/50-shots.js)`);
  const two = (x) => String(Math.floor(x)).padStart(2, "0");
  const mmss = (s) => (s >= 3600 ? `${Math.floor(s / 3600)}:${two((s % 3600) / 60)}:${two(s % 60)}` : `${Math.floor(s / 60)}:${two(s % 60)}`);
  const at = chs.map((c, i) => (i === 0 ? 0 : Math.max(0, Math.floor(c.t - 0.5))));
  const lines = chs.map((c, i) => `${mmss(at[i])} ${c.title}`);
  console.log(`chapters: ${rel0(film.page)} · ${chs.length}, each 0.5 to 1.5 s before it starts (whole seconds; the first at 0:00)`);
  for (const l of lines) console.log("  " + l);
  const short = at.map((s, i) => [chs[i].title, (i + 1 < at.length ? at[i + 1] : duration) - s]).filter(([, d]) => d < 10);
  if (chs.length < 3) console.log("  YouTube shows chapters only when there are at least three");
  for (const [t, d] of short) console.log(`  YouTube shows chapters only when each lasts 10 s or more: "${t}" lasts ${d.toFixed(0)} s`);
  const file = path.join(film.root, "out", "chapters.txt");
  try { fs.mkdirSync(path.dirname(file), { recursive: true }); fs.writeFileSync(file, lines.join("\n") + "\n"); console.log(`  written: ${rel0(file)}`); }
  catch (e) { die(`cannot write ${rel0(file)}: ${e.message}`); }
  process.exit(0);   // the chapter list alone: bin/vh cues without --chapters lists the cues
}
if (!cues) die(`${film.page} gives no window.film.cues (engines/CONTRACT.md)`);

const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
const sec = (t) => (Number.isFinite(t) ? t.toFixed(3) : "—");
const tlFile = typeof tlRel === "string" && tlRel ? path.resolve(film.root, tlRel) : null;
const sha = tlFile && fs.existsSync(tlFile) ? createHash("sha256").update(fs.readFileSync(tlFile)).digest("hex") : null;
const ok = (c) => c && typeof c === "object";
const tv = (c) => (typeof c.t === "number" ? c.t : NaN);   // NaN arrives as null through JSON: not 0 s
const sorted = cues.filter(ok).sort((p, q) => (Number.isFinite(tv(p)) ? tv(p) : Infinity) - (Number.isFinite(tv(q)) ? tv(q) : Infinity) || String(p.id).localeCompare(String(q.id)));
console.log(`cues: ${rel(film.page)} · ${sorted.length} cue${sorted.length === 1 ? "" : "s"}` +
  (tlFile ? ` on ${rel(tlFile)}${sha ? ` (sha256 ${sha.slice(0, 12)})` : " (not found)"}` : " (the page names no timeline)"));
const music = musicSource && typeof musicSource.path === "string" && typeof musicSource.sha256 === "string" ? musicSource : null;
if (music) console.log(`  music: ${music.path} (loaded sha256 ${music.sha256.slice(0, 12)})`);
const timemap = mapSource && typeof mapSource.path === "string" && typeof mapSource.sha256 === "string" ? { path: mapSource.path, sha256: mapSource.sha256 } : null;
if (timemap) console.log(`  time map: ${timemap.path} (loaded sha256 ${timemap.sha256.slice(0, 12)})`);
for (const p of loadProblems) console.log(`  while loading: ${p}`);
const w = Math.max(4, ...sorted.map((c) => String(c.id).length));
console.log(`  ${"t".padStart(8)}  ${"id".padEnd(w)}  cue`);
for (const c of sorted) console.log(`  ${sec(tv(c)).padStart(8)}  ${String(c.id).padEnd(w)}  ${c.ref}`);

// against the cues saved last time: what moved, what is new, what is gone. The timeline's sha256 says why (another take
// of the narration), but the page's own cues can change on the same take too (a word changed, FILM.lead)
const file = path.resolve(out || path.join(film.root, "out", "cues.json"));
let before = null;
if (fs.existsSync(file)) {
  try { before = JSON.parse(fs.readFileSync(file, "utf8")); if (!before || !Array.isArray(before.cues)) throw new Error("no cues list"); }
  catch { before = null; console.log(`  ${rel(file)}: not readable as saved cues, so not compared`); }
}
if (before) {
  const musicMoved = !!(music && before.music && music.sha256 !== before.music.sha256);
  if (musicMoved) console.log("  music map changed since the saved cues");
  const mapMoved = !!(timemap && before.timemap && timemap.sha256 !== before.timemap.sha256);
  if (mapMoved) console.log("  time map changed since the saved cues");
  const was = before.cues.filter(ok), old = new Map(was.map((c) => [c.id, c])), now = new Map(sorted.map((c) => [c.id, c]));
  const moved = sorted.filter((c) => old.has(c.id) && !(Math.abs(tv(old.get(c.id)) - tv(c)) < 0.0005)).map((c) => [c, tv(c) - tv(old.get(c.id))]);
  const added = sorted.filter((c) => !old.has(c.id)), gone = was.filter((c) => !now.has(c.id));
  const take = before.timeline_sha256 && sha ? (before.timeline_sha256 === sha ? "same timeline" : "another take") : null;
  if (!moved.length && !added.length && !gone.length) console.log(`  since ${rel(file)}: nothing moved${take === "same timeline" ? " (saved on this same timeline)" : ""}`);
  else {
    const why = take === "another take" ? " (saved on another take of the narration)"
      : musicMoved ? (take ? " (same timeline: the music map changed)" : " (the music map changed)")
      : mapMoved ? (take ? " (same timeline: the time map changed)" : " (the time map changed)") : take ? " (same timeline: the page's cues changed)" : "";
    console.log(`  since ${rel(file)}${why}: ` +
      `${moved.length} moved, ${added.length} new, ${gone.length} gone`);
    const more = (n, k) => { if (n > k) console.log(`    … and ${n - k} more`); };
    for (const [c, d] of moved.sort((p, q) => (Math.abs(q[1]) || 0) - (Math.abs(p[1]) || 0)).slice(0, 20))
      console.log(`    ${String(c.id).padEnd(w)}  ${sec(tv(old.get(c.id)))} → ${sec(tv(c))} s  (${Number.isFinite(d) ? `${d >= 0 ? "+" : ""}${d.toFixed(3)}` : "—"})`);
    more(moved.length, 20);
    for (const c of added.slice(0, 10)) console.log(`    new   ${c.id}  ${c.ref}`);
    more(added.length, 10);
    for (const c of gone.slice(0, 10)) console.log(`    gone  ${c.id}  ${c.ref}`);
    more(gone.length, 10);
  }
}
if (save) {
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, JSON.stringify({ note: "bin/vh cues --save: where the cues landed, and the timeline they were resolved on",
      page: path.relative(path.dirname(file), film.page), timeline: tlFile ? path.relative(path.dirname(file), tlFile) : null,
      timeline_sha256: sha, ...(music ? { music } : {}), ...(timemap ? { timemap } : {}), cues: sorted }, null, 1) + "\n");
  } catch (e) { die(`cannot write ${rel(file)}: ${e.message}`); }
  console.log(`  saved: ${rel(file)}`);
}
