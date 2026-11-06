"""bin/vh artifacts: the spec of every kind of file a film project holds (tools/artifacts.json), and one project against it.
Stdlib only; list only reads: no render, no browser, nothing written in the project.

usage: bin/vh artifacts spec [--stage S] [--json]
       bin/vh artifacts list <project> [--stage S] [--strict] [--json]
       bin/vh artifacts check [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional). --stage S:
a stage of tools/commands.json, by its id (0–9, env, any) or a part of its name: only the kinds used there.

  spec   the table: each kind's id, path, purpose, who makes it and when it must exist. --json: {"version": 1, "tool", "stage",
         "note", "artifacts": [the entries, every field; tools/artifacts.json's note says what each means]}
  list   what this project holds, kind by kind: the paths found, the version each says, the schema's result, whether it is out
         of date and why, the {…} left in a markdown file or a gate JSON, and what is required by now and missing. A path goes
         to the most specific entry that matches it. Out of date comes from what each record keeps: tools/audio/mixstate.py,
         the check record's film_changed, the sha256 values in a .render.json, out/cues.json, audio/captions.args.json and
         the others (their rules are STALE below); "not checked" where nothing can tell, or when telling would mean reading
         more than 1 GiB (the tool that owns it reads it all: bin/vh assets check, bin/vh mux).
         By now: new always; gate-1, gate-2, gate-3 once that stop is decided, or its page is out, or a later stop is
         (a stop skipped by Effort quick or the user's own words requires nothing); narration once there is a script, a
         voiceover or a timeline that is not the template's example; delivery once there is a final film or a delivery record.
         A stop already decided in REVIEW.md or with a page in out/review/gate-<n>*.html needs no gate JSON (projects from before
         bin/vh gate wrote one). Of the BRIEF's blanks only the ones tools rely on count (Output's size and fps, Resolution), once gate ① is reached
         or there is a film. --json: {"version": 1, "tool", "project", "stage", "reached": {milestone: true|false}, "counts":
         {"kinds", "found", "files", "stale", "not_checked", "schema_problems", "missing"}, "artifacts": [{"id", "kind",
         "required", "clean", "files": [{"path", "version", "schema": {"file", "ok", "problems"} | null, "stale": {"state":
         "fresh" | "stale" | "not_checked", "why"} | null, "placeholders": n | null}]}], only the kinds found; "missing":
         [{"id", "path", "required", "why"}]; "blanks": [{"file", "key", "value", "why", "required"}]}. stale is null for a kind
         that hangs on nothing the table knows of (it has neither stale nor made_from)
  check  tools/ci.sh's check of the table: its own rules; every writer and reader a real command (or page); every schema file
         there and every schema in tools/schemas/ with an entry; what the table says bin/vh clean does agrees with tools/clean.py
         on a temporary tree of made-up files; each <project>/… path in tools/commands.json's writes and reads matches an entry
         that lists that command, or (writes) the table's ignored_writes with a reason; and the other way: each writer an entry lists has a
         writes line that names the entry's path, or a line of NOT_SAID below with why. --json: {"version": 1, "tool", "exit", "problems"}
--json: the record on stdout, a line for a person on stderr. Exit: 0 (list is a report: what it finds is not a failure, unless
--strict) · 1 check found a problem; list --strict: something is missing by now, has a schema problem or is out of date ("not
checked" is none of these) · 2 usage, or no such project (a folder with no BRIEF.md is one when it holds a path of the table:
the BRIEF is then a missing item).
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TABLE = HERE / "artifacts.json"
SCHEMAS = HERE / "schemas"
for sub in (HERE, HERE / "desk", HERE / "audio", HERE / "assets"):
    sys.path.insert(0, str(sub))

VIDEO = "mp4|mov|webm|mkv|m4v|avi"   # tools/clean.py's VIDEO
HOLES = {"<lang>": r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,4})?", "<n>": r"[A-Za-z0-9_-]{1,24}", "<id>": r"[^/]+",
         "<film>": rf"(?:out|media|renders)/(?:[^/]+/)*[^/]*\.(?:{VIDEO})", "*": r"[^/]*"}
HOLE = re.compile(r"<[a-z]+>|\*")
MILESTONES = ("new", "gate-1", "gate-2", "gate-3", "narration", "delivery")
CLEAN = ("rebuilt", "versions", "renders", "sound", "film", "stays")
MADE_BY = ("person", "agent", "tool")
VERSION_KEYS = ("version", "v", None)
MAX_READ = 1 << 30       # bytes one list may hash: past it, "not checked"
MAX_JSON = 64 << 20      # a JSON file larger than this is not parsed
JSONL_TAIL = 4 << 20     # the last of a JSON Lines file that is read, as tools/activity.py reads its log
SHOWN = 5


def table(path=TABLE):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def stages_table():
    return json.loads((HERE / "commands.json").read_text(encoding="utf-8"))


def regex(pattern):
    """A table path as a compiled regular expression, matched whole; a folder's ends with /."""
    out, at = "", 0
    for m in HOLE.finditer(pattern):
        out += re.escape(pattern[at:m.start()]) + HOLES.get(m.group(0), re.escape(m.group(0)))
        at = m.end()
    return re.compile(out + re.escape(pattern[at:]) + r"\Z")


def literal(pattern):
    """How much of a table path is spelled out: the higher, the more specific."""
    return len(HOLE.sub("", pattern))


def sample(pattern):
    """A path that fits a table path, made up (tools/clean.py's versions go by the name v1)."""
    return HOLE.sub(lambda m: {"<lang>": "zh", "<n>": "1", "<id>": "v1", "<film>": "out/draft.mp4", "*": "x"}[m.group(0)], pattern)


def patterns(e):
    return [e["path"]] + list(e.get("also") or [])


class Index:
    """The table's paths, compiled: which entry a path of a project belongs to."""

    def __init__(self, entries):
        self.files, self.folders, all_paths = [], [], []
        for k, e in enumerate(entries):
            for p in patterns(e):
                all_paths.append(p)
                (self.folders if e["kind"] == "folder" else self.files).append((literal(p), -k, p, regex(p), e))
        self.files.sort(key=lambda x: (-x[0], -x[1]))    # the most literal first; then the table's order
        self.folders.sort(key=lambda x: (-x[0], -x[1]))
        # a folder nothing in the table lies below: no need to go in
        self.leaf = {p for _, _, p, _, e in self.folders if not any(q != p and q.startswith(p) for q in all_paths)}

    def folder(self, rel):
        """(entry, literal, its path) of the most specific folder entry for rel, a folder's path ending with /; or None."""
        for lit, _, p, rx, e in self.folders:
            if rx.match(rel):
                return e, lit, p
        return None

    def file(self, rel):
        for lit, _, p, rx, e in self.files:
            if rx.match(rel):
                return e, lit
        return None

    def owners(self, rel):
        """Every entry a made-up path fits: its own, and each folder entry above it."""
        rel = rel.rstrip("/")
        got = [e for _, _, _, rx, e in self.files if rx.match(rel)]
        parts = rel.split("/")
        for i in range(1, len(parts) + 1):
            d = "/".join(parts[:i]) + "/"
            got += [e for _, _, _, rx, e in self.folders if rx.match(d)]
        return got


def holdings(project, idx):
    """{entry id: [paths]} of the project, each path under its most specific entry. Skips .git and projects of their own,
    and does not go into a folder nothing in the table lies below."""
    found, above = {}, {"": -1}   # above: the most literal folder entry a folder lies in; a file's entry must say more than it
    project = Path(project)
    for d, dirs, files in os.walk(project):
        reld = Path(d).relative_to(project).as_posix()
        reld = "" if reld == "." else reld + "/"
        keep = []
        for name in sorted(dirs):
            q = os.path.join(d, name)
            if name == ".git" or os.path.islink(q) or os.path.isfile(os.path.join(q, "BRIEF.md")):
                continue
            hit = idx.folder(reld + name + "/")
            above[reld + name + "/"] = max(above[reld], hit[1] if hit else -1)
            if hit:
                found.setdefault(hit[0]["id"], []).append(reld + name + "/")
                if hit[2] in idx.leaf:
                    continue
            keep.append(name)
        dirs[:] = keep
        for name in sorted(files):
            hit = idx.file(reld + name)
            if hit and hit[1] > above[reld]:
                found.setdefault(hit[0]["id"], []).append(reld + name)
    return found


# ---- reading a file

def read_json(f):
    """(the value, None), or (None, why)."""
    try:
        if os.path.getsize(f) > MAX_JSON:
            return None, f"over {MAX_JSON >> 20} MB: not read"
        return json.loads(Path(f).read_text(encoding="utf-8-sig")), None
    except (OSError, ValueError) as e:
        return None, f"not JSON ({e})"


def read_jsonl(f):
    """[(line number within what was read, the value or None)]: the last JSONL_TAIL bytes, without the line cut in two."""
    with open(f, "rb") as fh:
        fh.seek(0, os.SEEK_END)
        size = fh.tell()
        fh.seek(max(0, size - JSONL_TAIL))
        raw = fh.read()
    if size > JSONL_TAIL:
        raw = raw.split(b"\n", 1)[-1]
    out = []
    for n, line in enumerate(raw.split(b"\n"), 1):
        if line.strip():
            try:
                out.append((n, json.loads(line.decode("utf-8", "replace"))))
            except ValueError:
                out.append((n, None))
    return out


class Reading:
    """One list's readers: what it hashed (once a file) and how much it may still read."""

    def __init__(self, project):
        self.project = Path(project)
        self.left = MAX_READ
        self.digests = {}
        self.records = None
        self.sent = None
        self.schemas = {}
        self.mixes = {}

    def rel(self, p):
        try:
            return Path(os.path.relpath(p, self.project)).as_posix()
        except ValueError:
            return str(p)

    def digest(self, f):
        """The file's sha256; None when it is not there; False when this list has read as much as it may."""
        f = str(f)
        if f in self.digests:
            return self.digests[f]
        try:
            size = os.path.getsize(f)
        except OSError:
            return None
        if size > self.left:
            return False
        self.left -= size
        h = hashlib.sha256()
        with open(f, "rb") as fh:
            for b in iter(lambda: fh.read(1 << 20), b""):
                h.update(b)
        self.digests[f] = h.hexdigest()
        return self.digests[f]

    def short(self, text):
        """A message with the project's own path taken out."""
        return str(text).replace(str(self.project) + os.sep, "")


FRESH, STALE_, NOT_CHECKED = "fresh", "stale", "not_checked"


def said(state, why):
    return {"state": state, "why": why}


# ---- out of date: what each record keeps. Every entry with a stale has a rule here (check holds the two to each other)

def captions_state(r, _rel):
    """tools/audio/capstate.py: the timeline and its sha256 that audio/captions.args.json kept (an .srt with no captions.json: none)."""
    import capstate
    got = capstate.state(r.project)
    return said(*got) if got else said(NOT_CHECKED, "no audio/captions.json beside it")


def mix_state(r, rel):
    """tools/audio/mixstate.py's own verdict, the one bin/vh mux goes by, for the audio or for its record; the audio without
    one is not attested (mixstate.py: a file made by hand)."""
    import mixstate
    record = r.project / (rel if rel.endswith(".mix.json") else rel + ".mix.json")
    if str(record) in r.mixes:
        return r.mixes[str(record)]
    if not record.is_file():
        return said(NOT_CHECKED, "no record of a bin/vh mix beside it")
    out = Path(str(record)[:-len(".mix.json")])
    d, err = read_json(record)
    if err or not isinstance(d, dict):
        return said(NOT_CHECKED, err or "not a mix record")
    inputs = d.get("inputs") if isinstance(d.get("inputs"), list) else []
    size = sum(os.path.getsize(out.parent / i["path"]) for i in inputs if isinstance(i, dict) and isinstance(i.get("path"), str)
               and (out.parent / i["path"]).is_file())
    if out.is_file():
        size += os.path.getsize(out)
    if size > r.left:
        return said(NOT_CHECKED, f"{size >> 20} MB to read: bin/vh mux verifies it")
    r.left -= size
    if not out.is_file():
        got = said(STALE_, f"{r.rel(out)} is not there")
    else:
        try:
            mixstate.validate(out, record)
            got = said(FRESH, f"{len(inputs)} input(s) and the audio are the ones it was built from")
        except mixstate.InvalidMix as e:
            got = said(STALE_, r.short(e))
    r.mixes[str(record)] = got
    return got


def check_state(r, rel):
    """status.py's reading of a check record: the size and mtime_ns it kept (checkrec.film_changed), a record older than those by time."""
    import status as S
    if r.records is None:
        r.records = {r.rel(p): c for c, p in S.check_records(r.project)}
    c = r.records.get(rel)
    if c is None:
        return said(NOT_CHECKED, "not a check record bin/vh status can read")
    if not c["video"]:
        return said(NOT_CHECKED, "it names no video")
    v = Path(c["video"]) if os.path.isabs(c["video"]) else r.project / c["video"]
    try:
        changed = S.film_changed(c, v.stat())
    except OSError:
        return said(NOT_CHECKED, f"{c['video']} is not there")
    if changed:
        return said(STALE_, f"{c['video']} is not the film this record checked (bin/vh check it again)")
    return said(FRESH, f"{c['verdict']}, on {c['video']} as it is")


def cues_state(r, rel):
    """The sha256 values bin/vh cues --save kept against the files now."""
    f = r.project / rel
    d, err = read_json(f)
    if err or not isinstance(d, dict):
        return said(NOT_CHECKED, err or "not what bin/vh cues --save writes")
    pairs = []
    if isinstance(d.get("timeline"), str) and d.get("timeline_sha256"):
        pairs.append((f.parent / d["timeline"], d["timeline_sha256"]))
    if isinstance(d.get("edit"), str) and d.get("edit_sha256"):
        pairs.append((f.parent / d["edit"], d["edit_sha256"]))
    for src in [d.get(k) for k in ("music", "timemap")] + (d["refs"] if isinstance(d.get("refs"), list) else []):
        if isinstance(src, dict) and isinstance(src.get("path"), str) and isinstance(src.get("sha256"), str):
            p = src["path"]
            pairs.append((Path(p) if os.path.isabs(p) else next((b / p for b in (r.project, f.parent) if (b / p).is_file()), r.project / p), src["sha256"]))
    if not pairs:
        return said(NOT_CHECKED, "it records no time source (the page names none)")
    return _against(r, pairs)


def _against(r, pairs):
    """[(file, sha256 on record)] against the files now: stale at the first that differs, not checked past the budget."""
    moved, unread = [], []
    for p, sha in pairs:
        now = r.digest(p)
        if now is False:
            unread.append(p)
        elif now != sha:
            moved.append(f"{r.rel(os.path.normpath(p))} {'is gone' if now is None else 'changed since'}")
    if moved:
        return said(STALE_, "; ".join(moved[:SHOWN]) + (f" … and {len(moved) - SHOWN} more" if len(moved) > SHOWN else ""))
    if unread:
        return said(NOT_CHECKED, f"{len(unread)} file(s) past the {MAX_READ >> 30} GiB this list reads")
    return said(FRESH, f"{len(pairs)} file(s) as recorded")


def film_state(r, rel):
    """The files the film's page loaded (its .render.json, or the one its .mux.json kept) against the files now."""
    film = r.project / rel
    side, base = None, film.parent
    if (Path(str(film) + ".render.json")).is_file():
        side, _ = read_json(str(film) + ".render.json")
    if not isinstance(side, dict):
        mux, _ = read_json(str(film) + ".mux.json") if Path(str(film) + ".mux.json").is_file() else (None, None)
        if isinstance(mux, dict) and isinstance(mux.get("render"), dict):
            side = mux["render"]
            if isinstance(mux.get("video"), str):
                base = Path(os.path.normpath(film.parent / mux["video"])).parent
    if not isinstance(side, dict):
        return said(NOT_CHECKED, "no .render.json or .mux.json beside it: nothing records what it was made from")
    files, page = side.get("files"), side.get("page")
    if not isinstance(files, dict) or not files or not isinstance(page, str):
        return said(NOT_CHECKED, "its record lists no files (rendered before they were recorded, or by another tool)")
    root = Path(os.path.normpath(base / page)).parent
    pairs = [(root / f, sha) for f, sha in files.items() if isinstance(sha, str)]
    edit = side.get("edit")
    if isinstance(edit, dict) and isinstance(edit.get("sha256"), str) and isinstance(edit.get("path"), str):
        pairs.append((root / edit["path"], edit["sha256"]))
    if not pairs:
        return said(NOT_CHECKED, "its record keeps no sha256 for the files")
    return _against(r, pairs)


def mux_state(r, rel):
    """<film>.mux.json keeps the film's size, and the names of what it was muxed from: a picture or sound newer than the film."""
    f = r.project / rel
    d, err = read_json(f)
    if err or not isinstance(d, dict):
        return said(NOT_CHECKED, err or "not a mux record")
    film = Path(str(f)[:-len(".mux.json")])
    if not film.is_file():
        return said(STALE_, f"{r.rel(film)} is not there")
    size = (d.get("film") or {}).get("size") if isinstance(d.get("film"), dict) else None
    if isinstance(size, int) and size != film.stat().st_size:
        return said(STALE_, f"{r.rel(film)} is not the film this record was written with (its size changed)")
    newer = []
    for k in ("video", "audio"):
        if isinstance(d.get(k), str):
            q = film.parent / d[k]
            if q.is_file() and q.stat().st_mtime > film.stat().st_mtime:
                newer.append(r.rel(os.path.normpath(q)))
    if newer:
        return said(STALE_, f"{', '.join(newer)} newer than the film: bin/vh mux again if it should follow")
    return said(FRESH, "its picture and sound are no newer than the film")


def deliver_state(r, rel):
    """tools/clean.py's reading of a delivery record: the copy and the master against the sizes and times it kept."""
    import clean
    if r.sent is None:
        r.sent = {Path(rec).as_posix(): notes for rec, _, notes in clean.deliveries(r.project)}
    rec = rel if rel.endswith(".deliver.json") else rel + ".deliver.json"
    if rec not in r.sent:
        return said(NOT_CHECKED, "no bin/vh deliver record beside it")
    notes = r.sent[rec]
    return said(STALE_, "; ".join(notes)) if notes else said(FRESH, "the copy and its master are the ones recorded")


def _source_state(r, d, err, what):
    """A proxy's or a thumbs' record against its source: the size and time it kept (tools/proxy.py's own comparison)."""
    import proxy as P
    if err or not isinstance(d, dict) or not isinstance(d.get("source"), str):
        return said(NOT_CHECKED, err or f"no record of what the {what} was made from")
    src = r.project / d["source"]
    now = P.ident(src)
    if now is None:
        return said(STALE_, f"{d['source']} is not there")
    if d.get("source_ident") != now:
        return said(STALE_, f"{d['source']} changed since (bin/vh {what} refreshes it)")
    return said(FRESH, f"made from {d['source']} as it is")


def proxy_state(r, rel):
    return _source_state(r, *read_json(str(r.project / rel) + ".json"), "proxy")


def thumbs_state(r, rel):
    return _source_state(r, *read_json(r.project / rel / "thumbs.json"), "thumbs")


def versions_state(r, _rel):
    import versions as V
    try:
        L = V.listing(r.project)
    except ValueError as e:
        return said(NOT_CHECKED, r.short(e))
    bad = [v for v in L["versions"] if v["state"] == "changed"]
    if bad:
        return said(STALE_, ", ".join(f"{v['id']} at {v['film']}" for v in bad[:SHOWN]) + ": replaced outside bin/vh render and patch (bin/vh versions)")
    return said(FRESH, f"{len(L['versions'])} version(s), each where the record says")


def resolved_state(r, rel):
    d, err = read_json(r.project / rel)
    want = (d.get("edit") or {}).get("sha256") if isinstance(d, dict) and isinstance(d.get("edit"), dict) else None
    if err or not want:
        return said(NOT_CHECKED, err or "it keeps no sha256 of the edit list")
    now = r.digest(r.project / "edit.json")
    if now is False:
        return said(NOT_CHECKED, "past what this list reads")
    if now is None:
        return said(STALE_, "edit.json is gone")
    return said(STALE_, "edit.json changed since (bin/vh render builds it first; bin/vh edit build does now)") if now != want else said(FRESH, "from edit.json as it is")


def cast_state(r, rel):
    """bin/vh cast check's failures: a picture changed since it was recorded is one."""
    import cast as CA
    cid = Path(rel).parent.name
    try:
        d = CA.read(r.project, cid)
    except CA.Usage as e:
        return said(NOT_CHECKED, r.short(e))
    fails = [m for s, m in CA.checked(r.project, cid, d) if s == "fail"]
    return said(STALE_, r.short(fails[0]) + (f" … and {len(fails) - 1} more (bin/vh cast check)" if len(fails) > 1 else "")) if fails else said(FRESH, "its pictures are the ones recorded")


def ledger_state(r, _rel):
    """bin/vh assets check's own findings on the record's files, when they are small enough to read here."""
    import assets as A, ledger as L
    try:
        base, ents, _ = L.entries(r.project)
    except L.LedgerError as e:
        return said(NOT_CHECKED, r.short(e))
    live = [e for e in ents if "removed" not in e["record"]]
    size = sum(e["record"]["bytes"] for e in live if isinstance(e["record"].get("bytes"), int))
    if size > r.left:
        return said(NOT_CHECKED, f"{size >> 20} MB to read: bin/vh assets check reads every file")
    r.left -= size
    fs = [f for f in A.findings(base, ents, L.policy_of(r.project)[0]) if f["kind"] in ("missing", "sha256")]
    if fs:
        return said(STALE_, f"{len(fs)} record(s) not the file on disk, the first {fs[0]['id']}: {r.short(fs[0]['message'])} (bin/vh assets check)")
    return said(FRESH, f"{len(live)} record(s), each the file on disk")


STALE = {"captions": captions_state, "captions-srt": captions_state, "mix": mix_state, "mix-record": mix_state, "check-record": check_state, "cues": cues_state,
         "render": film_state, "film-final": film_state, "mux-record": mux_state, "deliver-copy": deliver_state, "deliver-record": deliver_state,
         "proxy": proxy_state, "thumbs": thumbs_state, "versions-record": versions_state, "edit-resolved": resolved_state,
         "cast-record": cast_state, "ledger": ledger_state}


# ---- schema, version, placeholders

def schema_result(r, e, rel, value, lines, err):
    """The schema's result for one file; None when the kind has none."""
    if not e.get("schema"):
        return None
    out = {"file": e["schema"], "ok": True, "problems": []}
    if err:
        return dict(out, ok=False, problems=[err])
    if e["schema"].startswith("tools/assets/"):   # asset.schema.json: the ledger's own reader, which knows its record
        import ledger as L
        bad = []
        if not isinstance(value, dict) or value.get("v") != 1 or not isinstance(value.get("assets"), list):
            bad.append('not {"v": 1, "assets": […]}')
        else:
            for a in value["assets"]:
                bad += [f"{a.get('id') if isinstance(a, dict) else a}: {p}" for p in (L.validate(a) if isinstance(a, dict) else ["not an object"])]
        return dict(out, ok=not bad, problems=bad[:SHOWN])
    import schemalite
    sch = r.schemas.get(e["schema"])
    if sch is None:
        sch = r.schemas[e["schema"]] = schemalite.load(ROOT / e["schema"])
    if lines is not None:   # JSON Lines: each line against the schema
        bad = []
        for n, one in lines:
            bad += [f"line {n}: not JSON"] if one is None else [f"line {n}: {p}" for p in schemalite.problems(sch, one)]
        return dict(out, ok=not bad, problems=bad[:SHOWN])
    bad = schemalite.problems(sch, value)
    return dict(out, ok=not bad, problems=bad[:SHOWN])


def placeholders_of(e, rel, project, value):
    """How many {…} are left to fill: in a person's or an agent's markdown file, comments aside, the template's {none} a value
    and no blank (bin/vh status's count); in a gate JSON, bin/vh gate --init's {填：…}."""
    import status as S
    if e["format"] == "markdown" and e["made_by"] != "tool":
        text = S.reader.strip_comments(S.G.read(Path(project) / rel))
        return sum(1 for x in S.PLACEHOLDER.findall(text) if x[1:-1].strip().lower() != "none")
    if rel.startswith("out/review/gate-") and rel.endswith(".json"):
        return len(S.R.placeholders(value)) if value is not None else None
    return None


def details(r, e, rel):
    """One file of a kind: {path, version, schema, stale, placeholders}."""
    path, value, lines, err = r.project / rel, None, None, None
    if e["kind"] == "file" and (e.get("version_key") or e.get("schema") or e["id"] == "timeline" or rel.startswith("out/review/gate-")):
        if e["format"] == "jsonl":
            try:
                lines = read_jsonl(path)
            except OSError as x:
                err = str(x)
        elif e["format"] == "json":
            value, err = read_json(path)
    version = None
    if e.get("version_key"):
        src = value if lines is None else next((one for _, one in reversed(lines) if isinstance(one, dict)), None)
        version = src.get(e["version_key"]) if isinstance(src, dict) else None
    rule = STALE.get(e["id"])
    if rule and e.get("stale"):
        try:
            stale = rule(r, rel)
        except Exception as x:   # a record of a shape no rule foresaw is one that cannot be read; it never stops the list
            stale = said(NOT_CHECKED, r.short(f"could not be read ({type(x).__name__}: {x})"))
    elif e.get("made_from"):
        stale = said(NOT_CHECKED, f"nothing records what it was made from ({', '.join(e['made_from'])})")
        if e["id"] == "timeline" and isinstance(value, dict) and value.get("provider") == "example":
            stale = said(NOT_CHECKED, "the template's example, not a take")
    else:
        stale = None
    return {"path": rel, "version": version, "schema": schema_result(r, e, rel, value, lines, err), "stale": stale,
            "placeholders": placeholders_of(e, rel, r.project, value)}


# ---- by now

def narration_there(project, found):
    """A script, a voiceover, or a timeline that is not the template's example."""
    if found.get("script") or found.get("voiceover"):
        return True
    for rel in found.get("timeline", []):
        d, _ = read_json(Path(project) / rel)
        if isinstance(d, dict) and d.get("provider") != "example":
            return True
    return False


def the_film(project):
    """What bin/vh clean counts as the film: found in out/final, media/ or out/final*, named as a deliverable, or a delivery's copy and master."""
    import clean
    root = Path(project).resolve()
    films = clean.find_film(root, []) + clean.named_deliverables(root) + [f for _, fs, _ in clean.deliveries(root) for f in fs]
    return sorted({Path(f).as_posix() for f in films})


def stop_states(project):
    """{stop id: bin/vh status's state of it}; {} where REVIEW.md or the BRIEF is in a shape status cannot read."""
    import status as S
    try:
        proj = S.basics(project)
        rv = project / "REVIEW.md"
        text = S.G.strip_comments(S.G.read(rv)) if rv.is_file() else ""
        no_record = not rv.is_file() and proj["effort"] != "quick"
        st, _ = S.stops(project, text, rv.stat().st_mtime if rv.is_file() else 0, proj["effort"], S.director_stops(proj["director"]), proj["lang"], no_record)
        return {s["id"]: s["state"] for s in st}
    except Exception:   # no gate is taken as reached
        return {}


def passed_without_json(project, state):
    """The stops (1, 2, 3) that need no gate JSON for this rule: decided in REVIEW.md (status says done), or with a page in
    out/review/gate-<n>*.html. Projects from before bin/vh gate wrote the JSON have one or the other and no JSON."""
    import status as S
    paged = {S.G.stop_of(f.stem[5:]) for f in (Path(project) / "out" / "review").glob("gate-*.html")}
    return {n for n in "123" if state.get(n) == "done" or n in paged}


def milestones(project, found, state=None):
    """{milestone: reached?}, from the stops bin/vh status reads and what the project holds."""
    state = stop_states(project) if state is None else state
    out = {"new": True}
    reached = {n: state.get(n) in ("done", "waiting_person", "waiting_agent") for n in "123"}
    later = False
    for n in "321":   # a later stop reached: this one should have been too, unless it was skipped
        out[f"gate-{n}"] = reached[n] or (later and state.get(n) not in ("skipped", "no_record"))
        later = later or reached[n]
    out["narration"] = narration_there(project, found)
    out["delivery"] = bool(found.get("deliver-record") or the_film(project))
    return {m: out[m] for m in MILESTONES}


def blanks_of(project, found, reached):
    """The BRIEF's blanks tools rely on (tools/speccheck.py, tools/edit.py): Output's frame size and fps, Resolution."""
    import speccheck
    try:
        text = re.sub(r"<!--.*?-->", "", (Path(project) / "BRIEF.md").read_text(encoding="utf-8", errors="replace"), flags=re.S)
    except OSError:
        return []
    required = reached["gate-1"] or bool(found.get("render") or found.get("film-final"))
    out = []
    line = speccheck.spec_line(text, "Output")
    lacks = [w for w, pat in (("frame size", r"\d{3,5}\s*[x×]\s*\d{3,5}"), ("frame rate", r"\d+(?:\.\d+)?\s*fps")) if not re.search(pat, line or "", re.I)]
    if lacks:
        out.append({"file": "BRIEF.md", "key": "Output", "value": line, "required": required,
                    "why": f"it says no {' and no '.join(lacks)}: bin/vh check cannot compare the film with it, and bin/vh edit init cannot take it"})
    line = speccheck.spec_line(text, "Resolution")
    if line and "{" in line:
        out.append({"file": "BRIEF.md", "key": "Resolution", "value": line, "required": required, "why": "not filled: bin/vh check reads it as the deliveries to expect"})
    return out


def missing_of(project, entries, found, reached, no_json=()):
    """What is required by now and is not there. The film goes by what bin/vh clean counts as the film; its check record by that
    film: a record of a draft is no check of it."""
    import status as S
    out = []
    films = the_film(project)
    for e in entries:
        m = e.get("required")
        if not m or not reached.get(m):
            continue
        if m.startswith("gate-") and m[5:] in no_json:   # decided or paged before there was a gate JSON: the stop is passed
            continue
        if e["id"] == "film-final":
            if not films:
                out.append({"id": e["id"], "path": e["path"], "required": m, "why": "a delivery is on record, and no film is in the project (out/final/, out/final*, media/, Deliverables)"})
        elif e["id"] == "check-record":
            checked = {c["video"] for c, _ in S.check_records(project)}
            if films and not checked & set(films):
                out.append({"id": e["id"], "path": e["path"], "required": m, "why": f"no bin/vh check record of {films[0]}" + (f" or the other {len(films) - 1} film(s)" if len(films) > 1 else "")})
            elif not films and not found.get(e["id"]):
                out.append({"id": e["id"], "path": e["path"], "required": m, "why": f"required by {m}: not there"})
        elif not found.get(e["id"]):
            out.append({"id": e["id"], "path": e["path"], "required": m, "why": f"required by {m}: not there"})
    return out


# ---- the commands

def stage_of(word):
    """The stage --stage names, by tools/commands.py's rule; (None, an error line) when it is not one."""
    import commands as K
    t = stages_table()
    s, cands = K.find_stage(t, word)
    if s is None:
        some = cands or t["stages"]
        return None, f"bin/vh artifacts: {'more than one stage' if cands else 'no stage'} matches {word!r}: " + " · ".join(f"{x['id']} {x['name']}" for x in some)
    return s, None


def in_stage(entries, stage):
    return [e for e in entries if stage is None or stage["id"] in e["stages"]]


def cmd_spec(a):
    t = table()
    stage = None
    if a.stage is not None:
        stage, why = stage_of(a.stage)
        if stage is None:
            print(why, file=sys.stderr)
            return 2
    rows = in_stage(t["artifacts"], stage)
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh artifacts spec", "stage": stage["id"] if stage else None, "note": t["note"], "artifacts": rows}, ensure_ascii=False, indent=1))
        print(f"artifacts: {len(rows)} kinds of file" + (f", stage {stage['id']} {stage['name']}" if stage else ""), file=sys.stderr)
        return 0
    head = stages_table()["stages"]
    width = max((len(e["id"]) for e in rows), default=0)
    for s in head:
        here = [e for e in rows if e["stages"][0] == s["id"]]
        if here:
            print(f"{s['id']} {s['name']}")
        for e in here:
            bits = [e["made_by"]] + ([f"required by {e['required']}"] if e.get("required") else [])
            print(f"  {e['id']:<{width}}  {e['path']}  ({', '.join(bits)})  {e['purpose']}")
    print(f"{len(rows)} kinds of file (tools/artifacts.json; --json has every field)")
    return 0


def find_project(word, entries):
    """The project folder; a folder with no BRIEF.md is one still when it holds a path the table knows (the BRIEF is then a
    missing item of the report). None, with why on stderr, when there is no such folder or it holds none."""
    import gatecheck as G, review as R
    p = Path(word).expanduser()
    project = G.project_of(p) if p.exists() else None
    if project is None:
        project = R.find_project(word)
        if project is not None and not (project / "BRIEF.md").is_file():
            if not project.is_dir() or not holdings(project, Index(entries)):
                print(f"bin/vh artifacts: {project} is not a project (no BRIEF.md, and none of the files a project holds)", file=sys.stderr)
                return None
    return project


def report(project, entries_all, stage):
    """The record list --json prints."""
    idx = Index(entries_all)
    found = holdings(project, idx)
    r = Reading(project)
    entries = in_stage(entries_all, stage)
    state = stop_states(project)
    reached = milestones(project, found, state)
    rows = []
    for e in entries:
        if found.get(e["id"]):
            rows.append({"id": e["id"], "kind": e["kind"], "required": e.get("required"), "clean": e["clean"], "files": [details(r, e, rel) for rel in found[e["id"]]]})
    miss = missing_of(project, entries, found, reached, passed_without_json(project, state))
    if not (Path(project) / "BRIEF.md").is_file():   # a folder that is no project yet: the one thing to say is the BRIEF
        miss = [dict(m, why="required by new: not there (the folder holds files of a project, so it is listed; bin/vh new makes the rest)") for m in miss if m["id"] == "brief"]
    blanks = blanks_of(project, found, reached) if any(e["id"] == "brief" for e in entries) else []
    files = [f for x in rows for f in x["files"]]
    counts = {"kinds": len(entries), "found": len(rows), "files": len(files),
              "stale": sum(1 for f in files if f["stale"] and f["stale"]["state"] == STALE_),
              "not_checked": sum(1 for f in files if f["stale"] and f["stale"]["state"] == NOT_CHECKED),
              "schema_problems": sum(1 for f in files if f["schema"] and not f["schema"]["ok"]),
              "missing": len(miss) + sum(1 for b in blanks if b["required"])}
    return {"version": 1, "tool": "bin/vh artifacts", "project": str(project), "stage": stage["id"] if stage else None, "reached": reached, "counts": counts,
            "artifacts": rows, "missing": miss, "blanks": blanks}


def headline(rec):
    n = rec["counts"]
    return (f"{Path(rec['project']).name}: holds {n['found']} of {n['kinds']} kinds ({n['files']} files) · {n['stale']} out of date · {n['schema_problems']} schema problem(s) · "
            f"{n['missing']} missing by now")


def show(rec):
    print(headline(rec))
    print("reached: " + ", ".join(m for m, v in rec["reached"].items() if v))
    width = max((len(x["id"]) for x in rec["artifacts"]), default=0)
    for x in rec["artifacts"]:
        fs = x["files"]
        paths = fs[0]["path"] + (f" (+{len(fs) - 1} more)" if len(fs) > 1 else "")
        bits = []
        versions = sorted({str(f["version"]) for f in fs if f["version"] is not None})
        if versions:
            bits.append("v" + "/".join(versions))
        sch = [f for f in fs if f["schema"]]
        if sch and all(f["schema"]["ok"] for f in sch):
            bits.append("schema ok")
        n = sum(f["placeholders"] or 0 for f in fs)
        if n:
            bits.append(f"{n} {{…}} left")
        states = [f["stale"]["state"] for f in fs if f["stale"]]
        if states and all(x == FRESH for x in states):
            bits.append("up to date")
        elif NOT_CHECKED in states:
            why = next(f["stale"]["why"] for f in fs if f["stale"] and f["stale"]["state"] == NOT_CHECKED)
            n_not = states.count(NOT_CHECKED)
            bits.append(f"not checked{f' ({n_not} of {len(fs)})' if len(fs) > 1 else ''}: {why}")
        print(f"  {x['id']:<{width}}  {paths}" + (" · " + " · ".join(bits) if bits else ""))
        said_here = 0
        for f in fs:
            bad_schema = f["schema"] and not f["schema"]["ok"]
            bad_stale = f["stale"] and f["stale"]["state"] == STALE_
            if (bad_schema or bad_stale) and said_here >= SHOWN:
                said_here += 1
                continue
            if bad_schema:
                print(f"    ✗ {f['path']}: schema: " + "; ".join(f["schema"]["problems"][:3]))
            if bad_stale:
                print(f"    ! {f['path']}: out of date: {f['stale']['why']}")
            said_here += bool(bad_schema or bad_stale)
        if said_here > SHOWN:
            print(f"    … and {said_here - SHOWN} more (--json has them all)")
    if rec["missing"]:
        print("missing by now:")
        for m in rec["missing"]:
            print(f"  {m['id']}  {m['path']}: {m['why']}")
    blanks = [b for b in rec["blanks"]]
    if blanks:
        print("blanks tools rely on:")
        for b in blanks:
            print(f"  {b['file']} {b['key']}" + (" (required by now)" if b["required"] else "") + f": {b['why']}")


def cmd_list(a):
    t = table()
    stage = None
    if a.stage is not None:
        stage, why = stage_of(a.stage)
        if stage is None:
            print(why, file=sys.stderr)
            return 2
    project = find_project(a.project, t["artifacts"])
    if project is None:
        return 2
    rec = report(project, t["artifacts"], stage)
    if a.json:
        print(json.dumps(rec, ensure_ascii=False, indent=1))
        print(headline(rec), file=sys.stderr)
    else:
        show(rec)
    n = rec["counts"]
    return 1 if a.strict and (n["missing"] or n["schema_problems"] or n["stale"]) else 0


# ---- check: the table against its rules, the commands, the schemas and tools/clean.py

def own_rules(t, commands):
    bad = []
    if t.get("version") != 1 or not isinstance(t.get("artifacts"), list):
        return ['tools/artifacts.json: "version": 1 and a list of artifacts']
    stages = {s["id"] for s in stages_table()["stages"]}
    ids = [e.get("id") for e in t["artifacts"]]
    bad += [f"id {i!r} appears {ids.count(i)} times" for i in sorted({x for x in ids if ids.count(x) > 1}, key=str)]
    known = set(ids)
    seen = {}
    idx = Index([e for e in t["artifacts"] if isinstance(e.get("path"), str) and e.get("kind") in ("file", "folder")])
    need = ("id", "path", "kind", "format", "stages", "purpose", "made_by", "writers", "readers", "required", "version_key", "schema", "stale", "clean", "doc")
    for e in t["artifacts"]:
        w = f"{e.get('id')}:"
        lacking = [k for k in need if k not in e]
        if lacking:
            bad.append(f"{w} no {', '.join(lacking)}")
            continue
        if not re.fullmatch(r"[a-z][a-z0-9-]*", str(e["id"])):
            bad.append(f"{w} the id is not lower-case letters, digits and -")
        if e["kind"] not in ("file", "folder"):
            bad.append(f"{w} kind {e['kind']!r}: file or folder")
        for p in patterns(e):
            if e["kind"] == "folder" and not p.endswith("/") or e["kind"] == "file" and p.endswith("/"):
                bad.append(f"{w} {p}: a folder ends with /, a file does not")
            odd = [h for h in HOLE.findall(p) if h not in HOLES]
            if odd:
                bad.append(f"{w} {p}: {', '.join(odd)} is none of <lang>, <n>, <id>, <film>, *")
            if p in seen:
                bad.append(f"{w} {p} is {seen[p]}'s path too")
            seen[p] = e["id"]
        if not isinstance(e["format"], str) or not e["format"]:
            bad.append(f"{w} no format")
        if not isinstance(e["stages"], list) or not e["stages"] or not set(e["stages"]) <= stages or len(set(e["stages"])) != len(e["stages"]):
            bad.append(f"{w} stages {e['stages']!r} are not distinct ids of tools/commands.json's stages")
        if not isinstance(e["purpose"], str) or "\n" in e["purpose"] or not re.search(r"[一-鿿]", e["purpose"]):
            bad.append(f"{w} purpose: one plain Chinese line")
        if e["made_by"] not in MADE_BY:
            bad.append(f"{w} made_by {e['made_by']!r}: one of {', '.join(MADE_BY)}")
        if e["made_by"] == "tool" and not e["writers"]:
            bad.append(f"{w} made by a tool, and no writers")
        for k in ("writers", "readers"):
            for c in e[k]:
                if c not in commands and not (k == "readers" and c == "page") and not (k == "writers" and c == "*" and e["writers"] == ["*"]):
                    bad.append(f"{w} {k}: {c} is no command of tools/commands.json" + (", and only a reader can be page" if c == "page" else ""))
        if e["required"] is not None and e["required"] not in MILESTONES:
            bad.append(f"{w} required {e['required']!r}: null or one of {', '.join(MILESTONES)}")
        if e["version_key"] not in VERSION_KEYS:
            bad.append(f"{w} version_key {e['version_key']!r}: version, v or null")
        if e["clean"] not in CLEAN:
            bad.append(f"{w} clean {e['clean']!r}: one of {', '.join(CLEAN)}")
        st = e["stale"]
        if st is not None:
            if not isinstance(st, dict) or set(st) != {"from", "by", "recorded_in"}:
                bad.append(f"{w} stale: null or {{from, by, recorded_in}}")
            else:
                if st["by"] not in ("sha256", "size_mtime"):
                    bad.append(f"{w} stale.by {st['by']!r}: sha256 or size_mtime")
                gone = [x for x in st["from"] if x not in known]
                if gone or not st["from"]:
                    bad.append(f"{w} stale.from {gone or st['from']!r}: ids of this table")
                if not idx.owners(sample(st["recorded_in"])):
                    bad.append(f"{w} stale.recorded_in {st['recorded_in']!r} is no path of this table")
            if e["id"] not in STALE:
                bad.append(f"{w} it has a stale and tools/artifacts.py has no rule for it (STALE)")
        elif e["id"] in STALE:
            bad.append(f"{w} tools/artifacts.py has a rule for it (STALE) and its stale is null")
        made = e.get("made_from")
        if made is not None and (st is not None or not isinstance(made, list) or not made or not set(made) <= known):
            bad.append(f"{w} made_from {made!r}: ids of this table, for a kind with no stale (nothing records it)")
        bad += doc_problem(e)
    return bad


def doc_problem(e):
    doc = e["doc"]
    if not isinstance(doc, str) or not doc:
        return [f"{e['id']}: no doc"]
    f, _, sec = doc.partition("#")
    if not (ROOT / f).is_file():
        return [f"{e['id']}: doc {f} is not a file in the repo"]
    if sec:
        import know
        if not f.endswith(".md"):
            return [f"{e['id']}: doc {doc}: a #section only in a markdown file"]
        if know.show(doc)[1] is None:
            return [f"{e['id']}: doc {doc}: no such section (bin/vh know --show says which there are)"]
    return []


def schema_problems(t):
    import schemalite
    bad = []
    named = {e["schema"] for e in t["artifacts"] if e.get("schema")}
    for s in sorted(named):
        if not (ROOT / s).is_file():
            bad.append(f"schema {s}: no such file")
    for f in sorted(SCHEMAS.glob("*.schema.json")) if SCHEMAS.is_dir() else []:
        rel = f.relative_to(ROOT).as_posix()
        if rel not in named:
            bad.append(f"{rel}: no entry of tools/artifacts.json names it")
        try:
            odd = schemalite.keywords(schemalite.load(f))
        except ValueError as e:
            bad.append(f"{rel}: not JSON ({e})")
            continue
        if odd:
            bad.append(f"{rel}: keywords tools/schemalite.py does not read: {', '.join(sorted(odd))}")
    return bad


WRITE = re.compile(r"<project>/([^\s,;()]+)((?:,\s*(?!<project>)[^\s,;()]+)*)")


def written_paths(text, n="x1"):
    """The paths a command's writes line names inside the project, made up to fit (<n> as n): <project>/a/b.json, c.json is
    a/b.json and a/c.json; after a folder (<project>/a/, B.md) a name is from the project."""
    holes = {"<lang>": "zh", "<n>": n}
    s = text.replace("<project>", "\0")
    s = re.sub(r"<[^<>]*>", lambda m: holes.get(m.group(0), "x1"), s).replace("\0", "<project>")
    s = s.replace("…", "x")
    out = []
    for m in WRITE.finditer(s):
        first = re.sub(r"'s$", "", m.group(1))
        out.append(first)
        base = first.rpartition("/")[0] + "/" if "/" in first.rstrip("/") and not first.endswith("/") else ""
        for name in re.findall(r"[^\s,;()]+", m.group(2) or ""):
            if "." in name or name.endswith("/"):   # a file or a folder, not a word; one with a folder of its own is from the project
                out.append(name if "/" in name.rstrip("/") else base + name)
    return out


NS = ("x1", "1", "2", "3")   # what <n> is made up as: gate-<n> is gate-x1 (gate-other) and gate-1, 2, 3 (their own entries)

# Writers the free text of tools/commands.json's writes cannot name, each with why: (an entry id, or "format:<format>") and a command.
# Every line must still be needed: one that nothing needs any more fails the check.
NOT_SAID = [
    ("format:lock", "*", "a lock file is the flock around a write of the file its entry names; the command's writes line names that file, not the lock"),
]


def owners_of(t, idx, p):
    got = idx.owners(p.replace("*", "x"))
    if p.endswith("/"):   # a folder that is no entry of its own: what lies in it
        got = got or [e for e in t["artifacts"] if any(q.startswith(p) for q in patterns(e))]
    return got


def mentioned(e, text):
    """A writes line of free text that spells the last part of one of the entry's paths (audio/*.mix.json: ".mix.json"), where a
    command's line names a file by its name and the folder is the project's own. A path that is only a hole (<film>) says nothing."""
    for p in patterns(e):
        tail = p.rstrip("/").rpartition("/")[2]
        if len(HOLE.sub("", tail)) < 3:
            continue
        rx = "".join(r"[^\s,;()/]*" if HOLE.fullmatch(x) else re.escape(x) for x in re.split(r"(<[a-z]+>|\*)", tail) if x)
        if re.search(rx, text):
            return True
    return False


def paths_of(line):
    """Every path a writes line names, <n> made up each way in NS."""
    seen = []
    for n in NS:
        seen += [p for p in written_paths(line, n) if p not in seen]
    return seen


def writes_problems(t, commands):
    """Both ways. Each <project>/… path of the command table's writes and reads: an entry that lists that command (for a file, the
    most specific entry), or (writes) the table's ignored_writes; and each writer an entry lists: a writes line of that command
    that names a path of the entry, or a line of NOT_SAID. So a new kind of file cannot be added silently, and a writer cannot be
    changed or dropped silently. "*" as a writer is every command that works on a project."""
    bad = []
    idx = Index(t["artifacts"])
    ignored = t.get("ignored_writes") or []
    for g in ignored:
        if not isinstance(g, dict) or not g.get("path") or not g.get("why"):
            bad.append(f"ignored_writes: {g!r}: a path and why")
    used = set()
    lists = lambda e, side, name: name in e[side] or "*" in e[side]   # noqa: E731
    landed = set()
    for c in commands.values():
        for field, verb, side in (("writes", "writes", "writers"), ("reads", "reads", "readers")):
            for line in c[field]:
                for p in paths_of(line):
                    skip = next((g["path"] for g in ignored if isinstance(g, dict) and g.get("path") == p), None)
                    if skip and field == "writes":
                        used.add(skip)
                        continue
                    owners = owners_of(t, idx, p)
                    if field == "writes":
                        landed.update((e["id"], c["name"]) for e in owners)
                    if not owners:
                        bad.append(f"bin/vh {c['name']} {verb} <project>/{p}: no entry of tools/artifacts.json matches it (add one, or to its ignored_writes with a reason)")
                        continue
                    own = None if p.endswith("/") else idx.file(p.replace("*", "x"))
                    if own and not lists(own[0], side, c["name"]):   # a file goes by its most specific entry
                        bad.append(f"bin/vh {c['name']} {verb} <project>/{p}: {own[0]['id']} does not list it in {side}")
                    elif not any(lists(e, side, c["name"]) for e in owners):
                        bad.append(f"bin/vh {c['name']} {verb} <project>/{p}: {' or '.join(sorted({e['id'] for e in owners}))} does not list it in {side}")
    bad += [f"ignored_writes: {g['path']}: no command writes it now" for g in ignored if isinstance(g, dict) and g.get("path") and g["path"] not in used]
    spent = set()
    for e in t["artifacts"]:
        for w in e["writers"]:
            if w == "*" or (e["id"], w) in landed or mentioned(e, "\n".join(commands[w]["writes"])):
                continue
            ex = next((x for x in NOT_SAID if x[0] in (e["id"], "format:" + str(e.get("format"))) and x[1] in (w, "*")), None)
            if ex:
                spent.add(ex)
            else:
                bad.append(f"{e['id']}: writers lists {w}, and no writes line of bin/vh {w} in tools/commands.json names {e['path']}")
    bad += [f"NOT_SAID {x[0]} / {x[1]}: nothing needs it now" for x in NOT_SAID if x not in spent]
    return bad


# what the made-up tree needs beyond an empty file: a path, or a body, for the entries clean reads
TREE_PATHS = {"deliver-record": ["out/x.upload.mp4.deliver.json"]}
TREE_BODIES = {"out/x.upload.mp4.deliver.json": '{"output": "x.upload.mp4", "master": "finalx.mp4"}\n',
               "out/versions/versions.json": '{"version": 1, "next": 1, "versions": [], "events": []}\n',
               "assets/ledger.json": '{"v": 1, "assets": [], "events": []}\n'}
ALONE = "out/final/"   # tools/clean.py takes out/final*.<video> as the film only when out/final/ has none: these go in a tree of their own


def clean_listing(root):
    """What tools/clean.py --dry-run lists: {kind: [paths]}, the film's line aside."""
    r = subprocess.run([sys.executable, str(HERE / "clean.py"), str(root), "--dry-run"], capture_output=True, text=True)
    if r.returncode:
        raise ValueError(f"tools/clean.py --dry-run exit {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}")
    kinds, kind = {k: [] for k in ("rebuilt", "renders", "sound", "versions")}, None
    for line in r.stdout.splitlines():
        m = re.match(r"^  (rebuilt|renders|sound|versions) \(", line)
        if m:
            kind = m.group(1)
            continue
        if re.match(r"^  \S", line):
            kind = None
        elif kind:
            m = re.match(r"^\s+[\d.]+ (?:KB|MB|GB)  (.+)$", line)
            if m:
                kinds[kind].append(m.group(1).rstrip("/"))
            elif "more" in line and line.lstrip().startswith("…"):
                raise ValueError(f"the made-up tree lists over 25 of {kind}: tools/artifacts.py cannot read the rest")
    return kinds, r.stdout


def clean_problems(t):
    """Made-up files, one for each path of the table, and tools/clean.py's own list: does it do what the table says?"""
    bad = []
    wanted = []   # (entry, a made-up file, tree)
    for e in t["artifacts"]:
        for p in TREE_PATHS.get(e["id"]) or patterns(e):
            s = sample(p)
            if e["kind"] == "folder":
                s += "x.wav" if e["clean"] == "sound" else "x.bin"
            wanted.append((e, s, 1 if s.startswith(ALONE) else 0))
    for tree in (0, 1):
        d = Path(tempfile.mkdtemp(prefix="vh-artifacts-"))
        try:
            root = d / "p"
            root.mkdir()
            (root / "BRIEF.md").write_text("# BRIEF\n", encoding="utf-8")
            here = [w for w in wanted if w[2] == tree]
            for _, s, _t in here:
                f = root / s
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text(TREE_BODIES.get(s, ""), encoding="utf-8")
            kinds, text = clean_listing(root)
            for e, s, _t in here:
                ups = [s] + ["/".join(s.split("/")[:i]) for i in range(1, s.count("/") + 1)]
                did = next((k for k, xs in kinds.items() if any(u in xs for u in ups)), "stays")
                want = "stays" if e["clean"] == "film" else e["clean"]
                if did != want:
                    bad.append(f"{e['id']}: the table says clean {e['clean']}, and tools/clean.py {'keeps' if did == 'stays' else 'lists under ' + did} {s}")
                elif e["clean"] == "film" and s not in text:
                    bad.append(f"{e['id']}: the table says clean film, and tools/clean.py does not name {s} as the film")
        finally:
            shutil.rmtree(d, ignore_errors=True)
    return bad


def cmd_check(a):
    t = table()
    commands = {c["name"]: c for c in stages_table()["commands"]}
    bad = own_rules(t, commands)
    bad += schema_problems(t)
    bad += writes_problems(t, commands)
    try:
        bad += clean_problems(t)
    except (OSError, ValueError) as e:
        bad.append(f"the check against tools/clean.py did not run: {e}")
    line = f"tools/artifacts.json: {len(t['artifacts'])} kinds, {len({e['schema'] for e in t['artifacts'] if e.get('schema')})} schemas; writers and readers are real commands, every schema has an entry, " \
           "clean agrees with tools/clean.py on a made-up tree, every <project>/… path in tools/commands.json's writes has an entry, every writer an entry lists has a writes line naming it"
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh artifacts check", "exit": 1 if bad else 0, "problems": bad}, ensure_ascii=False, indent=1))
    for b in bad:
        print(b, file=sys.stderr if a.json else sys.stdout)
    if not bad:
        print(line, file=sys.stderr if a.json else sys.stdout)
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh artifacts", add_help=False, usage="bin/vh artifacts spec|list|check …  (bin/vh artifacts -h)")
    ap.add_argument("-h", "--help", action="store_true")
    subs = ap.add_subparsers(dest="what")
    for name in ("spec", "list", "check"):
        p = subs.add_parser(name, add_help=False)
        p.add_argument("-h", "--help", action="store_true")
        p.add_argument("--json", action="store_true")
        if name != "check":
            p.add_argument("--stage")
        if name == "list":
            p.add_argument("project", nargs="?")
            p.add_argument("--strict", action="store_true")
    a = ap.parse_args(argv)
    if a.help or not a.what:
        print(__doc__.strip(), file=sys.stdout if a.help else sys.stderr)
        return 0 if a.help else 2
    if a.what == "list" and not a.project:
        print("bin/vh artifacts list <project> [--stage S] [--strict] [--json]", file=sys.stderr)
        return 2
    return {"spec": cmd_spec, "list": cmd_list, "check": cmd_check}[a.what](a)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
