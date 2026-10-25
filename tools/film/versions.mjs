// versions: the last step of bin/vh render and bin/vh patch, putting the new film in place through tools/versions.py,
// which keeps (or sends to the Trash) the film it replaces and adds the new one's version to the project's record
// (<project>/out/versions/versions.json; bin/vh versions reads it). Outside a project, or with OVH_VERSIONS=off, the
// new film just takes the path, as it did before versions. The film is never deleted: when the record step fails before
// the film it replaces is out of the way, the new film goes beside it (<stem>.new.mp4) and the caller says so.
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const HERE = path.dirname(new URL(import.meta.url).pathname);
const PY = path.join(HERE, "..", "versions.py");

// job: { film, new, new_sidecar, made_by, source?, changed?, note?, problems? } → { id, from, lines, placed, error? }
// placed: where the new film is now (the film's path, or the .new file beside it)
export function commit(job) {
  const r = spawnSync("python3", [PY, "_commit"], { input: JSON.stringify(job), encoding: "utf8", maxBuffer: 1 << 24 });
  let res = null;
  try { res = JSON.parse((r.stdout || "").trim().split("\n").pop() || "null"); } catch { /* none */ }
  if (r.status === 0 && res && !res.error) return { ...res, placed: job.film };
  const why = (res && res.error) || (r.error ? r.error.message : (r.stderr || "").trim().split("\n").pop()) || `exit ${r.status}`;
  const side = job.new_sidecar, sideOf = (f) => f + ".render.json";
  if (!fs.existsSync(job.film) && fs.existsSync(job.new)) {   // the film it replaces was moved away first: take its path
    fs.renameSync(job.new, job.film);
    if (side && fs.existsSync(side)) fs.renameSync(side, sideOf(job.film));
    return { id: null, from: null, lines: [`the version record could not be written (${why}); the film is in place`], placed: job.film, error: why };
  }
  if (!fs.existsSync(job.new)) return { id: null, from: null, lines: [`the version record step failed (${why})`], placed: job.film, error: why };
  const ext = path.extname(job.film), beside = path.join(path.dirname(job.film), `${path.basename(job.film, ext)}.new${ext}`);
  fs.renameSync(job.new, beside);
  if (side && fs.existsSync(side)) fs.renameSync(side, sideOf(beside));
  return { id: null, from: null, placed: beside, error: why,
    lines: [`the film at ${job.film} could not be kept (${why}): it is as it was, and the new film is beside it, ${beside}`] };
}
