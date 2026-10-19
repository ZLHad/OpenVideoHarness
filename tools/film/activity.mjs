// activity: the page tools' lines in the project's activity log (<project>/.ovh/activity.jsonl; tools/activity.py has the
// format and reads it). bin/vh writes a run's start and hands the run over in OVH_ACTIVITY_*; it exec's into these tools,
// so the process with the run's pid writes the run's end on exit (with its exit status), and any tool adds note and
// progress lines. Without OVH_ACTIVITY_* (run by hand, or outside a project) every call does nothing. A line is one
// append (O_APPEND), under 4 KiB; a failure to write it is ignored: a render never fails because of its log.
import fs from "node:fs";
import path from "node:path";

const E = process.env, LOG = E.OVH_ACTIVITY_LOG, RUN = E.OVH_ACTIVITY_RUN, CMD = E.OVH_ACTIVITY_CMD || "";
const on = !!(LOG && RUN);
const now = () => Math.round(Date.now()) / 1000;

function write(rec) {
  if (!on) return;
  try {
    let line = JSON.stringify({ v: 1, ...rec }) + "\n";
    if (Buffer.byteLength(line) > 3800) {
      if (Array.isArray(rec.outputs)) rec.outputs = rec.outputs.slice(0, 5);
      if (typeof rec.summary === "string") rec.summary = rec.summary.slice(0, 300);
      line = JSON.stringify({ v: 1, ...rec }) + "\n";
      if (Buffer.byteLength(line) > 3800) return;
    }
    fs.mkdirSync(path.dirname(LOG), { recursive: true });
    fs.appendFileSync(LOG, line);
  } catch { /* the work goes on without its line */ }
}

function rel(p) {   // relative to the project when inside it, else absolute
  try {
    const proj = fs.realpathSync(path.dirname(path.dirname(LOG)));
    let a = path.resolve(String(p));
    try { a = path.join(fs.realpathSync(path.dirname(a)), path.basename(a)); } catch { /* not there yet */ }
    const r = path.relative(proj, a);
    return r && !r.startsWith("..") && !path.isAbsolute(r) ? r : a;
  } catch { return String(p); }
}

// what this command made: one line, and the files it wrote
export function note(summary, outputs = []) {
  write({ event: "note", run: RUN, t: now(), cmd: CMD, ...(summary ? { summary: String(summary).replace(/\s+/g, " ").slice(0, 300) } : {}),
    ...(outputs.length ? { outputs: outputs.filter(Boolean).map(rel).slice(0, 20) } : {}) });
}

// how far a long command has come (render: frames)
export function progress(done, total, unit) {
  write({ event: "progress", run: RUN, t: now(), cmd: CMD, done, ...(total != null ? { total } : {}), ...(unit ? { unit } : {}) });
}

// the run's end, from the process bin/vh exec'd into (the same pid): its exit status and how long it took
if (on && E.OVH_ACTIVITY_PID === String(process.pid)) {
  let done = false;
  process.on("exit", (code) => {
    if (done) return;
    done = true;
    const t0 = Number(E.OVH_ACTIVITY_T0), t = now();
    write({ event: "end", run: RUN, t, cmd: CMD, exit: code ?? 0, duration: Number.isFinite(t0) ? Math.max(0, Math.round((t - t0) * 1000) / 1000) : null });
  });
}
