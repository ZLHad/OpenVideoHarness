// cues: where a page's cues landed (window.film.cues, engines/CONTRACT.md): every time it hangs on the narration's words
// ("@b2:跟着走", "@a2>"), resolved in seconds, in order. With --save it keeps them in out/cues.json together with the
// sha256 of the timeline they were resolved on (window.film.timeline); when that file is there and the narration has
// changed since (a new take, pauses put in, a line rewritten), it says which cues moved and by how much.
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
const cues = await film.list("cues").catch((e) => die(e.message));
const tlRel = await film.field("timeline").catch(() => null);
const loadProblems = film.loadProblems;
await film.close();
if (!cues) die(`${film.page} gives no window.film.cues (engines/CONTRACT.md)`);

const rel = (f) => { const r = path.relative(process.cwd(), f); return r && !r.startsWith("..") ? r : f; };
const tlFile = typeof tlRel === "string" && tlRel ? path.resolve(film.root, tlRel) : null;
const sha = tlFile && fs.existsSync(tlFile) ? createHash("sha256").update(fs.readFileSync(tlFile)).digest("hex") : null;
const sorted = [...cues].sort((p, q) => p.t - q.t || String(p.id).localeCompare(String(q.id)));
console.log(`cues: ${rel(film.page)} · ${cues.length} cue${cues.length === 1 ? "" : "s"}` +
  (tlFile ? ` on ${rel(tlFile)}${sha ? ` (sha256 ${sha.slice(0, 12)})` : " (not found)"}` : " (no timeline: a silent film)"));
for (const p of loadProblems) console.log(`  while loading: ${p}`);
const w = Math.max(4, ...sorted.map((c) => String(c.id).length));
console.log(`  ${"t".padStart(8)}  ${"id".padEnd(w)}  cue`);
for (const c of sorted) console.log(`  ${(+c.t).toFixed(3).padStart(8)}  ${String(c.id).padEnd(w)}  ${c.ref}`);

// against the cues saved last time
const file = path.resolve(out || path.join(film.root, "out", "cues.json"));
let before = null;
try { before = JSON.parse(fs.readFileSync(file, "utf8")); } catch { /* none yet, or unreadable: nothing to compare */ }
if (before && Array.isArray(before.cues)) {
  if (before.timeline_sha256 && sha && before.timeline_sha256 === sha) console.log(`  ${rel(file)}: saved on this same timeline`);
  else {
    const old = new Map(before.cues.map((c) => [c.id, c])), now = new Map(cues.map((c) => [c.id, c]));
    const moved = cues.filter((c) => old.has(c.id) && Math.abs(old.get(c.id).t - c.t) >= 0.0005).map((c) => [c, c.t - old.get(c.id).t]);
    const added = cues.filter((c) => !old.has(c.id)), gone = before.cues.filter((c) => !now.has(c.id));
    console.log(`  since ${rel(file)}${before.timeline_sha256 && sha ? " (saved on another take of the narration)" : ""}: ` +
      `${moved.length} moved, ${added.length} new, ${gone.length} gone`);
    for (const [c, d] of moved.sort((p, q) => Math.abs(q[1]) - Math.abs(p[1])).slice(0, 20))
      console.log(`    ${String(c.id).padEnd(w)}  ${(+old.get(c.id).t).toFixed(3)} → ${(+c.t).toFixed(3)} s  (${d >= 0 ? "+" : ""}${d.toFixed(3)})`);
    if (moved.length > 20) console.log(`    … and ${moved.length - 20} more`);
    for (const c of added.slice(0, 10)) console.log(`    new   ${c.id}  ${c.ref}`);
    for (const c of gone.slice(0, 10)) console.log(`    gone  ${c.id}  ${c.ref}`);
  }
}
if (save) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, JSON.stringify({ note: "bin/vh cues --save: where the cues landed, and the timeline they were resolved on",
    page: path.relative(path.dirname(file), film.page), timeline: tlFile ? path.relative(path.dirname(file), tlFile) : null,
    timeline_sha256: sha, cues: sorted }, null, 1) + "\n");
  console.log(`  saved: ${rel(file)}`);
}
