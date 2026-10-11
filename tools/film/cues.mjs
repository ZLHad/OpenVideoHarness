// cues: where a page's cues landed (window.film.cues, engines/CONTRACT.md): every time it hangs on the narration's words
// ("@b2:跟着走", "@a2>"), resolved in seconds, in order. With --save it keeps them in out/cues.json together with the
// sha256 of the timeline they were resolved on (window.film.timeline); when that file is there, a later run says which
// cues moved and by how much, which are new and which are gone: after a new take of the narration (pauses put in, a line
// rewritten), or after the page's own cues changed on the same take.
//
// usage: node tools/film/cues.mjs <project | page.html> --browser <chrome> [--save] [--out out/cues.json]
//
// A cue that no longer resolves stops the page in ready, so the host's message names it and this exits 2.
// Exit: 0 listed · 2 could not open the page, or it gives no window.film.cues.
import fs from "node:fs";
import path from "node:path";
import { createHash } from "node:crypto";
import { openFilm } from "./host.mjs";

process.stdout.on("error", (e) => { if (e.code !== "EPIPE") throw e; });
const HELP = fs.readFileSync(new URL(import.meta.url), "utf8").split("\nimport ")[0].replace(/^\/\/ ?/gm, "");
const argv = process.argv.slice(2);
if (!argv.length || argv.includes("-h") || argv.includes("--help")) { process.stdout.write(HELP.trimEnd() + "\n"); process.exit(argv.length ? 0 : 2); }
const die = (msg) => { console.error("cues: " + msg); process.exit(2); };
let target = null, out = null, browser = null, save = false;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i], next = () => { const v = argv[++i]; if (v === undefined) die(`${a} needs a value`); return v; };
  if (a === "--out") out = next();
  else if (a === "--save") save = true;
  else if (a === "--browser") browser = next();
  else if (a.startsWith("-")) die(`unknown option ${a} (-h for the options)`);
  else if (target) die(`one project or page, got ${target} and ${a}`);
  else target = a;
}
if (!target) die("which project or page? (-h for the usage)");
if (!browser) die("no browser: pass --browser <chrome>, or run it as bin/vh cues");

let film;
try { film = await openFilm(target, { browser, runtime: "auto" }); } catch (e) { die(e.message); }
let cues, tlRel;
try { cues = await film.list("cues"); tlRel = await film.field("timeline").catch(() => null); }
catch (e) { await film.close(); die(e.message); }
const loadProblems = film.loadProblems;
await film.close();
if (!cues) die(`${film.page} gives no window.film.cues (engines/CONTRACT.md)`);

const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
const sec = (t) => (Number.isFinite(t) ? t.toFixed(3) : "—");
const tlFile = typeof tlRel === "string" && tlRel ? path.resolve(film.root, tlRel) : null;
const sha = tlFile && fs.existsSync(tlFile) ? createHash("sha256").update(fs.readFileSync(tlFile)).digest("hex") : null;
const ok = (c) => c && typeof c === "object";
const sorted = cues.filter(ok).sort((p, q) => (+p.t || 0) - (+q.t || 0) || String(p.id).localeCompare(String(q.id)));
console.log(`cues: ${rel(film.page)} · ${sorted.length} cue${sorted.length === 1 ? "" : "s"}` +
  (tlFile ? ` on ${rel(tlFile)}${sha ? ` (sha256 ${sha.slice(0, 12)})` : " (not found)"}` : " (the page names no timeline)"));
for (const p of loadProblems) console.log(`  while loading: ${p}`);
const w = Math.max(4, ...sorted.map((c) => String(c.id).length));
console.log(`  ${"t".padStart(8)}  ${"id".padEnd(w)}  cue`);
for (const c of sorted) console.log(`  ${sec(+c.t).padStart(8)}  ${String(c.id).padEnd(w)}  ${c.ref}`);

// against the cues saved last time: what moved, what is new, what is gone. The timeline's sha256 says why (another take
// of the narration), but the page's own cues can change on the same take too (a word changed, FILM.lead)
const file = path.resolve(out || path.join(film.root, "out", "cues.json"));
let before = null;
if (fs.existsSync(file)) {
  try { before = JSON.parse(fs.readFileSync(file, "utf8")); if (!before || !Array.isArray(before.cues)) throw new Error("no cues list"); }
  catch { before = null; console.log(`  ${rel(file)}: not readable as saved cues, so not compared`); }
}
if (before) {
  const was = before.cues.filter(ok), old = new Map(was.map((c) => [c.id, c])), now = new Map(sorted.map((c) => [c.id, c]));
  const moved = sorted.filter((c) => old.has(c.id) && !(Math.abs(old.get(c.id).t - c.t) < 0.0005)).map((c) => [c, c.t - old.get(c.id).t]);
  const added = sorted.filter((c) => !old.has(c.id)), gone = was.filter((c) => !now.has(c.id));
  const take = before.timeline_sha256 && sha ? (before.timeline_sha256 === sha ? "same timeline" : "another take") : null;
  if (!moved.length && !added.length && !gone.length) console.log(`  since ${rel(file)}: nothing moved${take === "same timeline" ? " (saved on this same timeline)" : ""}`);
  else {
    console.log(`  since ${rel(file)}${take === "another take" ? " (saved on another take of the narration)" : take ? " (same timeline: the page's cues changed)" : ""}: ` +
      `${moved.length} moved, ${added.length} new, ${gone.length} gone`);
    const more = (n, k) => { if (n > k) console.log(`    … and ${n - k} more`); };
    for (const [c, d] of moved.sort((p, q) => (Math.abs(q[1]) || 0) - (Math.abs(p[1]) || 0)).slice(0, 20))
      console.log(`    ${String(c.id).padEnd(w)}  ${sec(+old.get(c.id).t)} → ${sec(+c.t)} s  (${Number.isFinite(d) ? `${d >= 0 ? "+" : ""}${d.toFixed(3)}` : "—"})`);
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
      timeline_sha256: sha, cues: sorted }, null, 1) + "\n");
  } catch (e) { die(`cannot write ${rel(file)}: ${e.message}`); }
  console.log(`  saved: ${rel(file)}`);
}
