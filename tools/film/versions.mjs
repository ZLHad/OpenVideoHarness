// versions: the last step of bin/vh render and bin/vh patch, putting the new film in place through tools/versions.py,
// which keeps (or sends to the Trash) the film it replaces and adds the new one's version to the project's record
// (<project>/out/versions/versions.json; bin/vh versions reads it). Outside a project, or with OVH_VERSIONS=off, the
// new film just takes the path, as it did before versions; a link at the path is replaced, never written through. The
// film is never deleted or overwritten: when the record step refuses (the film at the path is not the one a patch cut,
// or the path is a kept version's) or fails before the film it replaces is out of the way, the new film goes beside it
// under a name nothing has (<stem>.new.mp4, <stem>.new-2.mp4 …) and the caller says so and exits 1.
import fs from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const HERE = path.dirname(new URL(import.meta.url).pathname);
const PY = path.join(HERE, "..", "versions.py");
export const there = (f) => { try { fs.lstatSync(f); return true; } catch { return false; } };   // a dangling link is there too

// a name beside the film that nothing has, with room for its .render.json: <stem>.<tag>.mp4, <stem>.<tag>-2.mp4 …
// (tag: new, here; bin/vh patch keeps a film whose check failed as .failed)
export function besideName(film, tag = "new") {
  const ext = path.extname(film), stem = path.join(path.dirname(film), path.basename(film, ext));
  for (let k = 1; ; k++) {
    const f = `${stem}.${tag}${k > 1 ? `-${k}` : ""}${ext}`;
    if (!there(f) && !there(f + ".render.json")) return f;
  }
}

// job: { film, new, new_sidecar, made_by, source?, expect?, changed?, note?, problems? } → { id, from, lines, placed, error? }
// placed: where the new film is now (the film's path, or a free name beside it)
export function commit(job) {
  const r = spawnSync("python3", [PY, "_commit"], { input: JSON.stringify(job), encoding: "utf8", maxBuffer: 1 << 24 });
  let res = null;
  try { res = JSON.parse((r.stdout || "").trim().split("\n").pop() || "null"); } catch { /* none */ }
  if (r.status === 0 && res && !res.error) return { ...res, placed: job.film };
  const why = (res && res.error) || (r.error ? r.error.message : (r.stderr || "").trim().split("\n").pop()) || `exit ${r.status}`;
  const side = job.new_sidecar, sideOf = (f) => f + ".render.json";
  if (!there(job.new)) return { id: null, from: null, lines: [`the version record step failed (${why})`], placed: job.film, error: why };
  // the path is free (its film was moved away first, or there was none) and nothing refused it: the new film takes it
  if (!(res && res.refused) && !there(job.film) && !(side && there(sideOf(job.film)))) {
    fs.renameSync(job.new, job.film);
    if (side && there(side)) fs.renameSync(side, sideOf(job.film));
    return { id: null, from: null, lines: [`the version record could not be written (${why}); the film is in place`], placed: job.film, error: why };
  }
  const beside = besideName(job.film);
  fs.renameSync(job.new, beside);
  if (side && there(side)) fs.renameSync(side, sideOf(beside));
  return { id: null, from: null, placed: beside, error: why,
    lines: [`${why}: what is at ${job.film} is left as it is, and the new film is beside it, ${beside}`] };
}
