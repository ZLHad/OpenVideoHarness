// The project's shot table for the page tools (bin/vh patch --shot): the mirror of tools/shot_source.py, which the
// Python tools read it through (storyboard, rhythm, the review desk, thumbs, looks). Both find it the same way, so where
// it lives is said in one place each.
import fs from "node:fs";
import path from "node:path";

// 12.5, "12.5", "0:12.5" or "1:02:03" → seconds; null when it is none of these
export const secs = (x) => {
  if (typeof x === "number") return Number.isFinite(x) ? x : null;
  const m = String(x ?? "").match(/^\s*(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)\s*$/);
  const y = m ? +(m[1] || 0) * 3600 + +m[2] * 60 + +m[3] : String(x ?? "").trim() === "" ? NaN : Number(x);
  return Number.isFinite(y) ? y : null;
};

// as bin/vh storyboard reads them: start / t0, end / t1, an id or S01 …; a transition's length when it has one
export const tidyShots = (raw) => raw.map((s, i) => {
  const pick = (...ks) => ks.map((kk) => s && s[kk]).find((x) => x !== undefined && x !== null && x !== "");
  const d = s && s.transition && typeof s.transition === "object" ? +s.transition.duration : typeof (s && s.transition) === "number" ? s.transition : NaN;
  return { id: String((s && s.id) || `S${String(i + 1).padStart(2, "0")}`), start: secs(pick("start", "t0")), end: secs(pick("end", "t1")), ...(d > 0 ? { transition: d } : {}) };
}).filter((s) => s.start !== null && s.end !== null && s.end > s.start).sort((p, q) => p.start - q.start);

// the project's hand-written shot table: <project>/shots.json, or null when there is none
export function findTable(project) {
  if (!project) return null;
  const f = path.join(project, "shots.json");
  try { return fs.statSync(f).isFile() ? f : null; } catch { return null; }
}

// the table's shots, tidied; throws when it cannot be read (the message says why; the caller names the file)
export function readTable(file) {
  const j = JSON.parse(fs.readFileSync(file, "utf8"));
  const raw = Array.isArray(j) ? j : j && j.shots;
  if (!Array.isArray(raw)) throw new Error('a list of shots, or {"shots": [...]} (bin/vh storyboard -h)');
  return tidyShots(raw);
}
