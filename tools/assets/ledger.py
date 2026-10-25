"""Asset records and the collections that hold them (tools/assets/asset.schema.json has the record). Stdlib only.

A collection is one of:
  <project>/assets/ledger.json   the project's: {"v": 1, "note", "assets": [record…], "events": [{"t", "at", "event", "id",
                       "sha256", "by", "why"}]}. Written whole under an flock on assets/.ledger.lock, through a temporary file
                       and os.replace, the way out/versions/versions.json is. A change appends its event and never drops a
                       record: remove marks one removed (kept on record, left out of check and credits); an update replaces
                       its fields and keeps its added_at. Ids are never reused
  <folder>/ledger.jsonl  a library's, outside the repo (a sound library, the cross-film look ledger): one record a line,
                       appended in one write with O_APPEND (as .ovh/activity.jsonl); a later line with the same id supersedes
                       an earlier one
  <project>/assets/genclips/<id>/ledger.json   a generated clip's, in the shape references/genvideo-ledger.md gave it
                       before v1 (no "v"): read as a record (origin generated, aigc, license generated; its terms, marks and
                       inputs kept as they are), never rewritten. A record in the project's ledger with its id or its path
                       supersedes it: bin/vh assets add <project> <its clip> --id <its id> moves it over. A clip's ledger.json
                       that is a v1 record or a v1 ledger already is read as that
A record's path is relative to its collection's base: the project folder for the project's ledger and the clips' (as
their output.file always was), the library's folder for a library's.
"""
import fcntl, hashlib, json, os, re, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import licenses   # noqa: E402

LEDGER = Path("assets") / "ledger.json"
LOCK = Path("assets") / ".ledger.lock"
GENCLIPS = "assets/genclips/*/ledger.json"
KINDS = ("image", "video", "audio", "font", "model", "data", "other")
ORIGINS = ("download", "generated", "self", "user", "library", "purchased")
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
SHA = re.compile(r"^[0-9a-f]{64}$")
CURRENCY = re.compile(r"^[A-Z][A-Z0-9-]{1,23}$")
EXT = {}
for _k, _e in (("image", ".png .jpg .jpeg .gif .webp .avif .svg .bmp .tif .tiff .exr .hdr .heic"),
               ("video", ".mp4 .mov .webm .mkv .m4v .avi .mxf"),
               ("audio", ".wav .mp3 .m4a .aac .flac .ogg .opus .aif .aiff"),
               ("font", ".woff2 .woff .ttf .otf .ttc"),
               ("model", ".glb .gltf .usd .usdz .usda .usdc .fbx .obj .blend .abc .ply .stl .vdb"),
               ("data", ".csv .tsv .json .geojson .xlsx .xls .parquet .txt .srt .vtt .xml")):
    EXT.update(dict.fromkeys(_e.split(), _k))
STR_FIELDS = ("attribution", "model", "prompt", "prompt_file", "added_at", "updated_at", "derived_from", "note")


class LedgerError(ValueError):
    """A collection that cannot be read (bad JSON, another version): bin/vh assets exits 2."""


class Refused(ValueError):
    """An add or a remove the ledger does not make (an id or a path on record already, an id it does not have)."""


def iso(t=None):
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(time.time() if t is None else t))


def project_of(p):
    """The nearest folder at or above p that holds a BRIEF.md, or None."""
    p = Path(p).resolve()
    for d in [p] + list(p.parents):
        if d.is_dir() and (d / "BRIEF.md").is_file():
            return d
    return None


def rel(base, p):
    """p as a record writes it: POSIX, relative to base when inside it (links resolved when that is what puts it there),
    else absolute; a folder ends with /."""
    a, b = Path(os.path.abspath(p)), Path(os.path.realpath(base))
    for x in (a, Path(os.path.realpath(a))):
        try:
            out = x.relative_to(b).as_posix()
            break
        except ValueError:
            continue
    else:
        out = a.as_posix()
    return out + "/" if Path(p).is_dir() and not out.endswith("/") else out


def absolute(base, path):
    return Path(path) if os.path.isabs(path) else Path(base) / path.rstrip("/")


# ---- the BRIEF's lines, and this machine's defaults ----

def local_md():
    """The harness's LOCAL.md, or the file OVH_LOCAL_MD names (as tools/gatecheck.py reads it; tests use one of their own)."""
    return Path(os.environ.get("OVH_LOCAL_MD") or HERE.parent.parent / "LOCAL.md")


def spec_lines(project, brief_pat, local_pat):
    """[(value, "BRIEF" or "LOCAL.md")]: the line BRIEF.md has (comments left out), then LOCAL.md's; a file without one, none."""
    out = []
    for f, pat, where in ((Path(project) / "BRIEF.md", brief_pat, "BRIEF"), (local_md(), local_pat, "LOCAL.md")):
        try:
            m = re.search(pat, re.sub(r"<!--.*?-->", "", f.read_text(encoding="utf-8", errors="replace"), flags=re.S), re.I | re.M)
        except OSError:
            continue
        if m:
            out.append((m.group(1).strip().strip("*`").strip(), where))
    return out


POLICY_BRIEF = r"^\s*[-*]\s*(?:\*\*)?Assets(?:\*\*)?\s*[:：]\s*(.*?)\s*$"
POLICY_LOCAL = r"^\s*[-*]?\s*(?:\*\*)?(?:素材许可|许可策略|assets(?:\s+policy)?)(?:\*\*)?\s*[:：]\s*(.*?)\s*$"


def policy_of(project):
    """(strict or record, where it comes from): the BRIEF's Assets line, else LOCAL.md's 素材许可 (or Assets) line, else
    strict. default, an empty line or a template's {…} goes on to the next."""
    for raw, where in spec_lines(project, POLICY_BRIEF, POLICY_LOCAL):
        m = re.match(r"(strict|record)\b", raw, re.I)
        if m:
            return m.group(1).lower(), where
    return "strict", "the default"


# ---- bytes ----

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tree(folder):
    """(sha256, files, bytes) of a folder: the sha256 of its listing, one '<relative path>\\t<sha256>\\n' line a file, in
    code-point order of the paths; files and folders whose names start with a dot are left out."""
    lines, size = [], 0
    for top, dirs, names in os.walk(folder):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for n in names:
            p = Path(top, n)
            if n.startswith(".") or not p.is_file():
                continue
            lines.append((p.relative_to(folder).as_posix(), sha256_file(p)))
            size += p.stat().st_size
    lines.sort()
    return hashlib.sha256("".join(f"{r}\t{h}\n" for r, h in lines).encode("utf-8")).hexdigest(), len(lines), size


def digest(p):
    """(sha256, bytes) of a file or a folder (its tree hash)."""
    p = Path(p)
    if p.is_dir():
        h, _, size = tree(p)
        return h, size
    return sha256_file(p), p.stat().st_size


def guess_kind(p):
    """The kind a file's extension says; a folder: the kind most of its files have."""
    p = Path(p)
    if p.is_dir():
        seen = {}
        for top, _, names in os.walk(p):
            for n in names:
                if not n.startswith("."):
                    k = EXT.get(Path(n).suffix.lower(), "other")
                    seen[k] = seen.get(k, 0) + 1
        return max(seen, key=seen.get) if seen else "other"
    return EXT.get(p.suffix.lower(), "other")


# ---- one record ----

def validate(r):
    """What is wrong with a record against asset.schema.json (v 1), as short lines; [] when nothing is."""
    if not isinstance(r, dict):
        return ["not a JSON object"]
    bad = []
    def is_str(x):
        return isinstance(x, str)
    def is_num(x):
        return isinstance(x, (int, float)) and not isinstance(x, bool)
    if r.get("v") != 1:
        bad.append(f"v is {r.get('v')!r}, not 1")
    for k in ("id", "kind", "path", "sha256", "license", "source", "aigc", "added_at"):
        if k not in r:
            bad.append(f"no {k}")
    if "id" in r and not (is_str(r["id"]) and ID.match(r["id"])):
        bad.append(f"id {r['id']!r}: letters, digits, . _ - (up to 64, not starting with . _ -)")
    if "kind" in r and r["kind"] not in KINDS:
        bad.append(f"kind {r['kind']!r} is not one of {', '.join(KINDS)}")
    if "path" in r:
        p = r["path"]
        if not is_str(p) or not p or "\\" in p or ".." in p.rstrip("/").split("/"):
            bad.append(f"path {p!r}: a POSIX path without .. parts")
    if "sha256" in r and not (is_str(r["sha256"]) and SHA.match(r["sha256"])):
        bad.append("sha256 is not 64 lower-case hex digits")
    if "bytes" in r and not (isinstance(r["bytes"], int) and not isinstance(r["bytes"], bool) and r["bytes"] >= 0):
        bad.append("bytes is not a whole number ≥ 0")
    lic = r.get("license")
    if "license" in r:
        if not isinstance(lic, dict) or lic.get("class") not in licenses.CLASSES:
            bad.append(f"license.class is not one of {', '.join(licenses.CLASSES)}")
        else:
            bad += [f"license.{k} is not a string" for k in ("name", "url") if k in lic and not is_str(lic[k])]
            if "by" in lic and lic["by"] not in ("classifier", "given"):
                bad.append("license.by is not classifier or given")
    src = r.get("source")
    if "source" in r:
        if not isinstance(src, dict) or src.get("origin") not in ORIGINS:
            bad.append(f"source.origin is not one of {', '.join(ORIGINS)}")
        else:
            bad += [f"source.{k} is not a string" for k in ("url", "file_url", "provider", "provider_id", "title", "author", "retrieved", "library")
                    if k in src and not is_str(src[k])]
            if "range" in src and not (isinstance(src["range"], list) and len(src["range"]) == 2 and all(is_num(x) and x >= 0 for x in src["range"])):
                bad.append("source.range is not [start, end] in seconds")
    if "aigc" in r and not isinstance(r["aigc"], bool):
        bad.append("aigc is not true or false")
    bad += [f"{k} is not a string" for k in STR_FIELDS if k in r and not is_str(r[k])]
    if "seed" in r and not (isinstance(r["seed"], (int, str)) and not isinstance(r["seed"], bool)):
        bad.append("seed is not a whole number or a string")
    c = r.get("cost")
    if "cost" in r and not (isinstance(c, dict) and set(c) == {"amount", "currency"} and is_num(c["amount"]) and c["amount"] >= 0
                            and is_str(c["currency"]) and CURRENCY.match(c["currency"])):
        bad.append("cost is not {amount ≥ 0, currency: USD, CNY …}")
    for k in ("used_by", "tags"):
        if k in r and not (isinstance(r[k], list) and all(is_str(x) for x in r[k])):
            bad.append(f"{k} is not a list of strings")
    rm = r.get("removed")
    if "removed" in r and not (isinstance(rm, dict) and is_str(rm.get("at")) and is_str(rm.get("why", ""))):
        bad.append("removed is not {at, why}")
    return bad


def from_genclip(o, where):
    """A record from a generated clip's ledger.json in the shape before v1 (references/genvideo-ledger.md)."""
    out = o.get("output") if isinstance(o.get("output"), dict) else {}
    terms = o.get("terms") if isinstance(o.get("terms"), dict) else {}
    vendor, route, ver = (o.get(k) if isinstance(o.get(k), str) else "" for k in ("vendor", "route", "model_version"))
    r = {"v": 1, "id": str(o.get("id") or Path(where).parent.name), "kind": "video", "path": out.get("file") or "",
         "sha256": out.get("sha256") or "", "license": {"class": "generated", "name": str(terms.get("tier") or "the vendor's terms"), "by": "given"},
         "source": {"origin": "generated"}, "aigc": True, "added_at": str(o.get("requested_at") or "")}
    if isinstance(terms.get("url"), str):
        r["license"]["url"] = terms["url"]
    if vendor:
        r["source"]["provider"] = vendor
    model = "/".join(x for x in (vendor, route) if x) + (f" ({ver})" if ver else "")
    if model:
        r["model"] = model
    for k in ("prompt_file", "seed"):
        if k in o:
            r[k] = o[k]
    if isinstance(o.get("cost_usd"), (int, float)) and not isinstance(o.get("cost_usd"), bool):
        r["cost"] = {"amount": o["cost_usd"], "currency": "USD"}
    if isinstance(o.get("purpose"), str):
        r["note"] = o["purpose"]
    for k, v in o.items():   # the vendor's terms, marks, inputs, the request: kept as they are
        if k not in ("id", "output", "vendor", "route", "model_version", "requested_at", "prompt_file", "seed", "cost_usd", "purpose") and k not in r:
            r[k] = v
    if out:
        r["output"] = out
    r["legacy"] = "genclip-ledger"
    return r


# ---- collections ----

def empty():
    return {"v": 1, "note": "the project's material, one record a file (bin/vh assets; tools/assets/asset.schema.json)", "assets": [], "events": []}


def read_ledger(path):
    """The ledger document at path, or an empty one when there is none. Raises LedgerError when it cannot be read."""
    path = Path(path)
    if not path.is_file():
        return empty()
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise LedgerError(f"{path} cannot be read ({e})")
    if not isinstance(d, dict) or d.get("v") != 1 or not isinstance(d.get("assets"), list):
        raise LedgerError(f"{path} is not an asset ledger (v 1, with an assets list)")
    if not isinstance(d.get("events"), list):
        d["events"] = []
    return d


def write_ledger(path, d):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ledger.", suffix=".tmp", dir=path.parent)
    try:
        mask = os.umask(0)
        os.umask(mask)
        os.chmod(tmp, 0o666 & ~mask)   # mkstemp's 0600 would stay through os.replace
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False, indent=1) + "\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def read_jsonl(path, said=None):
    """A library's records: the last line of each id, in the order the ids first came. A line that is not a JSON object is
    skipped (said)."""
    out = {}
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        raise LedgerError(f"{path} cannot be read ({e})")
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except ValueError:
            r = None
        if not isinstance(r, dict) or not isinstance(r.get("id"), str):
            if said is not None:
                said.append(f"{path}:{n}: not a record, skipped")
            continue
        out[r["id"]] = r
    return list(out.values())


def append_jsonl(path, rec):
    """One record appended to a library's ledger.jsonl: one write, O_APPEND (several writers never interleave lines)."""
    data = (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def _clip(f, said):
    """The records of one generated clip's ledger.json (any of its three shapes)."""
    try:
        o = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        said.append(f"{f}: cannot be read ({e}), left out")
        return []
    if isinstance(o, dict) and o.get("v") == 1 and isinstance(o.get("assets"), list):
        return [r for r in o["assets"] if isinstance(r, dict)]
    if isinstance(o, dict) and o.get("v") == 1:
        return [o]
    if isinstance(o, dict):
        return [from_genclip(o, f)]
    said.append(f"{f}: not a clip's ledger, left out")
    return []


def entries(target, said=None):
    """(base, [{"record", "from", "problems"}], the collection's file) for a project (its ledger, then the generated clips'
    the ledger does not supersede) or a collection file (a ledger.json or a .jsonl). Raises LedgerError."""
    said = [] if said is None else said
    t = Path(target)
    if t.is_file() and t.suffix == ".jsonl":
        return t.parent, [{"record": r, "from": t.name, "problems": validate(r)} for r in read_jsonl(t, said)], t
    if t.is_file():
        d = read_ledger(t)
        return t.parent, [{"record": r, "from": t.name, "problems": validate(r)} for r in d["assets"]], t
    base, f = t, t / LEDGER
    d = read_ledger(f)
    out = [{"record": r, "from": LEDGER.as_posix(), "problems": validate(r)} for r in d["assets"]]
    ids = {r.get("id") for r in d["assets"] if isinstance(r, dict)}
    paths = {r.get("path") for r in d["assets"] if isinstance(r, dict)}
    for clip in sorted(base.glob(GENCLIPS)):
        for r in _clip(clip, said):
            if r.get("id") in ids or r.get("path") in paths:
                continue   # the project's ledger has it now
            out.append({"record": r, "from": clip.relative_to(base).as_posix(), "problems": validate(r)})
    return base, out, f


class Locked:
    """The project ledger's read-modify-write under an flock on assets/.ledger.lock (two adds at once)."""
    def __init__(self, project):
        self.f = Path(project) / LOCK

    def __enter__(self):
        self.f.parent.mkdir(parents=True, exist_ok=True)
        self.h = open(self.f, "a")
        fcntl.flock(self.h.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.h.fileno(), fcntl.LOCK_UN)
        self.h.close()


def slug(name):
    s = re.sub(r"[^a-z0-9._-]+", "-", name.lower()).strip("-._")[:40].strip("-._")
    return s or "asset"


def _event(d, event, rec, by, why=None):
    t = time.time()
    e = {"t": round(t, 3), "at": iso(t), "event": event, "id": rec["id"], "sha256": rec.get("sha256"), "by": by}
    if why:
        e["why"] = why
    d["events"].append(e)


def add(project, file, *, id=None, kind=None, license=None, license_url=None, license_class=None, source=None,
        attribution=None, aigc=None, model=None, prompt=None, prompt_file=None, seed=None, cost=None, used_by=None,
        tags=None, derived_from=None, note=None, extra=None, update=False, by="bin/vh assets add"):
    """Register a file or a folder (a relative path is from the current folder) in the project's ledger: its sha256 and
    size, its licence classified (license_class, when given, wins), and the fields given. → (record, the previous record
    or None). update=True replaces the fields of the record with this id or this path (the ones not given are kept, and
    so is added_at); else an id or a path already on record is refused (Refused). FileNotFoundError: no such file;
    ValueError: the record would not be valid (said why)."""
    project = Path(project).resolve()
    f = Path(file)
    if not f.exists():
        raise FileNotFoundError(f"no such file or folder: {file}")
    path = rel(project, f)
    if path in (LEDGER.as_posix(), LOCK.as_posix(), "assets/spend.jsonl") or path.startswith((".ovh/", "out/versions/")):
        raise ValueError(f"{path} is a record of the tools, not material")
    if f.is_dir() and path in ("./", "assets/", ".ovh/") or path.endswith("/") and LEDGER.as_posix().startswith(path):
        raise ValueError(f"{path} holds the ledger itself: register the files or the folders in it")
    h, size = digest(f)
    with Locked(project):
        d = read_ledger(project / LEDGER)
        recs = [r for r in d["assets"] if isinstance(r, dict)]
        by_id = {r.get("id"): r for r in recs}
        at_path = next((r for r in recs if r.get("path") == path and "removed" not in r), None)
        old = None
        if update:
            old = by_id.get(id) if id else at_path
            if old is None:
                _, ent, _ = entries(project)   # a generated clip's record, moved over by this update
                old = next((e["record"] for e in ent if e["from"] != LEDGER.as_posix() and (e["record"].get("id") == id or (not id and e["record"].get("path") == path))), None)
                if old is None:
                    raise Refused(f"nothing to update: no record {'with id ' + id if id else 'for ' + path}")
            if at_path is not None and at_path is not old:
                raise Refused(f"{path} is on record as {at_path['id']}: update that one")
            old = dict(old)
        else:
            if at_path is not None:
                raise Refused(f"{path} is on record already as {at_path['id']} (--update to change its record)")
            taken = set(by_id)
            _, ent, _ = entries(project)
            taken |= {e["record"].get("id") for e in ent}
            if id and id in taken:
                raise Refused(f"the id {id} is taken (ids are never reused): another --id, or --update")
            if not id:
                base = slug(Path(path.rstrip("/")).stem)
                id, n = base, 1
                while id in taken:
                    n += 1
                    id = f"{base}-{n}"
        rec = {k: v for k, v in (old or {}).items() if k not in ("removed", "legacy", "output")} if old else {}
        rec.update({"v": 1, "id": old["id"] if old else id, "kind": kind or (old or {}).get("kind") or guess_kind(f),
                    "path": path, "sha256": h, "bytes": size})
        if old and old.get("output") and old.get("legacy"):
            rec["output"] = old["output"]   # a clip's media facts, kept when it moves over
        lic = dict(rec.get("license") or {})
        if license is not None or license_url is not None:
            if license is not None:
                lic["name"] = license
            if license_url is not None:
                lic["url"] = license_url
            lic["class"], _ = licenses.classify(lic.get("name", ""), lic.get("url"))
            lic["by"] = "classifier"
        if license_class:
            lic["class"], lic["by"] = license_class, "given"
        src = dict(rec.get("source") or {})
        src.update({k: v for k, v in (source or {}).items() if v is not None})
        if not src.get("origin"):
            src["origin"] = ("download" if src.get("url") or src.get("file_url") else "generated" if (aigc or model)
                             else "self" if lic.get("class") == "own" else None)
            if not src["origin"]:
                raise ValueError("where it came from is not said: --origin download|self|user|library|purchased, or --source-url")
        if not lic.get("class"):
            lic["class"], lic["by"] = ("generated" if src["origin"] == "generated" else "own" if src["origin"] == "self" and license is None else "unknown"), "classifier"
        rec["license"], rec["source"] = lic, src
        rec["aigc"] = bool(aigc) if aigc is not None else rec.get("aigc", src["origin"] == "generated")
        for k, v in (("attribution", attribution), ("model", model), ("prompt", prompt), ("prompt_file", prompt_file),
                     ("seed", seed), ("cost", cost), ("used_by", used_by), ("tags", tags), ("derived_from", derived_from), ("note", note)):
            if v is not None:
                rec[k] = v
        if prompt_file is not None:
            rec["prompt_file"] = rel(project, prompt_file)
        rec.update(extra or {})
        now = iso()
        rec["added_at"] = (old or {}).get("added_at") or now
        if old:
            rec["updated_at"] = now
        bad = validate(rec)
        if bad:
            raise ValueError("; ".join(bad))
        if old and any(r is not None and r.get("id") == rec["id"] for r in recs):
            d["assets"] = [rec if r.get("id") == rec["id"] else r for r in d["assets"]]
        else:
            d["assets"].append(rec)
        _event(d, "update" if old else "add", rec, by)
        write_ledger(project / LEDGER, d)
    return rec, old


def remove(project, id, why=None, by="bin/vh assets remove"):
    """Mark a record removed: kept on record, out of check and credits. A generated clip's record is moved into the
    project's ledger to be marked. → (record, False), or (record, True) when it was removed already. Refused: no such id."""
    project = Path(project).resolve()
    with Locked(project):
        d = read_ledger(project / LEDGER)
        rec = next((r for r in d["assets"] if isinstance(r, dict) and r.get("id") == id), None)
        if rec is None:
            _, ent, _ = entries(project)
            old = next((e["record"] for e in ent if e["record"].get("id") == id), None)
            if old is None:
                raise Refused(f"no record with id {id}")
            rec = dict(old)
            d["assets"].append(rec)
        if "removed" in rec:
            return rec, True
        rec["removed"] = {"at": iso(), **({"why": why} if why else {})}
        _event(d, "remove", rec, by, why)
        write_ledger(project / LEDGER, d)
    return rec, False
