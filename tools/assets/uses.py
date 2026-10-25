"""What a project's films and mixes used, read from the records the tools already keep, and how that squares with the
ledger. Stdlib only; nothing is hashed here (the records carry the sha256s).

  films   each video under out/ (three levels down, not out/versions/ or out/proxy/), renders/ and media/ whose
          .render.json has `files`: every file bin/vh render (or patch) sent the page, and its sha256, by its path from the
          page's folder. A film whose sidecar has no `files` (rendered before they were recorded) is named as one whose
          files are not known; a video with no sidecar (mux's, npx hyperframes render's, Manim's) is not a render here
  mixes   each <mix>.mix.json (bin/vh mix): its inputs, from the mix's folder, and their sha256
uses(project) → {"films": [{"film", "sidecar", "files": {path: sha256}}], "unknown": [films], "mixes": [{"mix", "inputs": {path:
sha256}}]}, every path relative to the project (absolute outside it).

compare(entries, used, policy) → the findings of the two directions, for the records not removed:
  unregistered  material a film's page loaded that no record covers (a record's path, or a folder record above it):
                fail. Material: images, video, sound, fonts, 3D models, tables (csv, tsv, xlsx, parquet, geojson);
                the page's code and its own JSON and text are not
  stale         a record whose file a film loaded with other bytes than the ledger has: warn (render again, or --update)
  unused        a record no film loaded, no mix used and nothing declares a use of (used_by): warn; said only when at
                least one film's files are known
  mix           the sound files a mix used that no record covers: one info line (a TTS take is AI-generated: register it)
overview(project) → the counts bin/vh status gives (version 1 of its "assets" field): records, uncleared, not_taken,
aigc, unregistered, policy, the budget and the spend.
"""
import json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budget, ledger, licenses   # noqa: E402,E401

VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
SKIP = {"frames", "node_modules", "__pycache__", ".venv", "venv"}
OUT_SKIP = {"versions", "proxy"}
MATERIAL = {e for e, k in ledger.EXT.items() if k in ("image", "video", "audio", "font", "model")} | {".csv", ".tsv", ".xlsx", ".xls", ".parquet", ".geojson"}


def _load(p):
    try:
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except (OSError, ValueError):
        return None


def films(project):
    """[(video, its .render.json)] under out/ (three levels, not out/versions or out/proxy), renders/ and media/."""
    out = []
    for top in ("out", "renders", "media"):
        base = Path(project) / top
        if not base.is_dir():
            continue
        for d, dirs, names in os.walk(base):
            depth = Path(d).relative_to(base).parts
            dirs[:] = sorted(x for x in dirs if x not in SKIP and not x.startswith(".") and len(depth) < 3 and not (top == "out" and not depth and x in OUT_SKIP))
            for n in sorted(names):
                if Path(n).suffix.lower() in VIDEO and not n.startswith("."):
                    out.append((Path(d) / n, Path(d) / (n + ".render.json")))
    return out


def uses(project):
    project = Path(project).resolve()
    res = {"films": [], "unknown": [], "mixes": []}
    for v, side in films(project):
        s = _load(side)
        files = s.get("files") if s else None
        if not isinstance(files, dict) or not isinstance(s.get("page"), str):
            if s is not None:   # a render's, from before the files were recorded (a film with no sidecar is a mux's or another tool's)
                res["unknown"].append(ledger.rel(project, v))
            continue
        page = Path(s["page"]) if os.path.isabs(s["page"]) else side.parent / s["page"]
        root = Path(os.path.realpath(page)).parent
        got = {}
        for k, h in files.items():
            if isinstance(k, str) and (h is None or isinstance(h, str)):
                got[ledger.rel(project, Path(k) if os.path.isabs(k) else root / k)] = h
        res["films"].append({"film": ledger.rel(project, v), "sidecar": ledger.rel(project, side), "files": got})
    for d, dirs, names in os.walk(project):
        depth = Path(d).relative_to(project).parts
        dirs[:] = sorted(x for x in dirs if x not in SKIP and not x.startswith(".") and len(depth) < 4 and not (depth[:1] == ("out",) and len(depth) == 1 and x in OUT_SKIP))
        for n in sorted(names):
            if not n.endswith(".mix.json"):
                continue
            m = _load(Path(d) / n)
            if not m or not isinstance(m.get("inputs"), list):
                continue
            ins = {}
            for i in m["inputs"]:
                if isinstance(i, dict) and isinstance(i.get("path"), str) and isinstance(i.get("sha256"), str):
                    ins[ledger.rel(project, Path(os.path.normpath(Path(d) / i["path"])))] = i["sha256"]
            res["mixes"].append({"mix": ledger.rel(project, Path(d) / n[:-len(".mix.json")]), "inputs": ins})
    return res


def _covering(path, by_path, folders):
    """The record whose path is this one, or the folder record it lies under (the deepest), or None."""
    if path in by_path:
        return by_path[path]
    hits = [r for r in folders if path.startswith(r["path"])]
    return max(hits, key=lambda r: len(r["path"])) if hits else None


def compare(entries, used, policy):
    live = [e["record"] for e in entries if "removed" not in e["record"] and isinstance(e["record"].get("path"), str) and e["record"].get("path")]
    by_path = {r["path"]: r for r in live}
    folders = [r for r in live if r["path"].endswith("/")]
    out, seen = [], set()
    def put(kind, sev, r, path, msg, **extra):
        out.append({"kind": kind, "severity": sev, "id": r.get("id") if r else None, "path": path, "message": msg, **extra})
    loaded = {}
    for f in used["films"]:
        for p, h in f["files"].items():
            loaded.setdefault(p, []).append((f["film"], h))
    for p in sorted(loaded):
        r = _covering(p, by_path, folders)
        if r is not None:
            seen.add(r["id"])
            if r["path"] == p and isinstance(r.get("sha256"), str):
                other = sorted({film for film, h in loaded[p] if h and h != r["sha256"]})
                if other:
                    put("stale", "warn", r, p, f"{', '.join(other)} was made with other bytes of it than the ledger has: render again, "
                        "or bin/vh assets add <project> <file> --update when the ledger is the one behind")
        elif Path(p).suffix.lower() in MATERIAL and not os.path.isabs(p) and not p.startswith(("node_modules/", "../")):
            put("unregistered", "fail", None, p, f"loaded by {', '.join(sorted({film for film, _ in loaded[p]}))}'s page and not in the ledger: "
                "bin/vh assets add <project> " + p + " with where it came from and its licence")
    mixed = {}
    for m in used["mixes"]:
        for p in m["inputs"]:
            mixed.setdefault(p, []).append(m["mix"])
    loose = []
    for p in sorted(mixed):
        r = _covering(p, by_path, folders)
        if r is not None:
            seen.add(r["id"])
        elif Path(p).suffix.lower() in MATERIAL and not os.path.isabs(p):
            loose.append(p)
    if loose:
        put("mix", "info", None, None, f"the mix ({', '.join(sorted({m for p in loose for m in mixed[p]}))}) also uses {len(loose)} sound file(s) the ledger "
            f"does not have: {', '.join(loose[:4])}{' …' if len(loose) > 4 else ''} (a TTS take is AI-generated: bin/vh assets add … --aigc --model <provider>)",
            paths=loose)
    if used["films"]:
        for r in live:
            if r["id"] not in seen and not r.get("used_by"):
                put("unused", "warn", r, r["path"], "on record, but no film's page loaded it, no mix used it and no used_by says what it is for "
                    "(bin/vh assets remove it, or --used-by)")
    return out


def overview(project):
    """bin/vh status's "assets" (version 1): {"ledger", "records", "removed", "uncleared", "not_taken", "aigc",
    "unregistered", "films_known", "policy", "policy_from", "budget", "budget_from", "spent", "left", "over", "error"}."""
    project = Path(project)
    o = {"ledger": None, "records": 0, "removed": 0, "uncleared": 0, "not_taken": 0, "aigc": 0, "unregistered": None, "films_known": 0,
         "policy": None, "policy_from": None, "budget": {}, "budget_from": None, "spent": {}, "left": {}, "over": [], "error": None}
    try:
        base, ents, f = ledger.entries(project, [])
    except ledger.LedgerError as e:
        o["error"] = str(e)
        ents, f = [], project / ledger.LEDGER
    o["policy"], o["policy_from"] = ledger.policy_of(project)
    if f.is_file() or ents:
        o["ledger"] = ledger.LEDGER.as_posix()
    for e in ents:
        r = e["record"]
        if "removed" in r:
            o["removed"] += 1
            continue
        o["records"] += 1
        cls = r["license"].get("class", "unknown") if isinstance(r.get("license"), dict) else "unknown"
        if licenses.risks(cls):
            o["uncleared"] += 1
            o["not_taken"] += 0 if licenses.accepted(cls, o["policy"]) else 1
        o["aigc"] += r.get("aigc") is True
    try:
        u = uses(project)
        o["films_known"] = len(u["films"])
        if u["films"]:
            o["unregistered"] = sum(1 for x in compare(ents, u, o["policy"]) if x["kind"] == "unregistered")
    except OSError:
        pass
    b = budget.summary(project)
    o.update({"budget": b["budget"], "budget_from": b["from"], "spent": b["spent"], "left": b["left"], "over": b["over"]})
    if b["error"] and not o["error"]:
        o["error"] = f"the Budget line: {b['error']}"
    return o
