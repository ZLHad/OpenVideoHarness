"""bin/vh cast: a project's cast, the settled references of what must look the same in every shot: its characters,
costumes, props and sets. One folder each, cast/<id>/, with its pictures and cast.json, which the tools read (image gen
--ref cast:<id>; a 3D model made from four views later). Stdlib only.

usage: bin/vh cast add <project> <id> [--kind character|costume|prop|set] [--name N] [--note TEXT] [--prompt TEXT]
                       [--ref picture[=view] …] [--source TEXT] [--license TEXT] [--final | --draft] [--force] [--json]
       bin/vh cast list <project> [--json]
       bin/vh cast check <project> [--json]
<project> as bin/vh assets takes it.

cast/<id>/cast.json ("version": 1; written by add, read by every tool, edited by hand too):
  id       the folder's name: a lowercase letter or digit, then letters, digits, - and _ (up to 40): what --ref cast:<id> names
  kind     character | costume | prop | set
  name     what it is called, in any language
  note     a line: what it is in the film, and what must not change about it
  prompt   the words that describe it to an image model, as its pictures show it (optional): the line to put in a prompt
           that sends them
  refs     the pictures in the folder, in the order image gen sends them: [{"file", "view", "sha256", "from", "source",
           "license"}]. view (optional): front, left, back, right, three-quarter, top, sheet, detail, pose, expression, or
           another lowercase word. from (optional): where add copied it from: {"path"} for a file of the project, with
           "asset", its ledger id, when assets/ledger.json has a record of those bytes; {"file"} for one from outside it,
           its name only (where it lay on this machine is not written down). source and license (optional): where it came
           from and on what terms, for a picture the ledger has no record of
  views    {"front", "left", "back", "right"}: which picture is which side, one picture a side (the subject's own left
           and right, not the viewer's), for a 3D model made from four separate views (model3d gen --views, to come: it is
           to read these four, and write the model to gen3d); a sheet with several views on it is a picture of refs, not
           a view
  status   draft | final: final once the person has settled it (gate ②, or the character stop E0 of the director modes)
  palette  [{"token", "hex"}] (optional); scale: a sentence or {"height_m": 1.2} (optional); gen3d: the folder a 3D
           model of it goes in, assets/gen3d/<id>/ (optional, for later)
  add      makes cast/<id>/, or adds to it: copies each --ref picture in (PNG, JPEG or WebP; picture=view names its view, and
           the copy is <view>.<ext> when that name is free, else its own name), records its sha256 and where it came from,
           a front/left/back/right view in views too, and writes cast.json. The fields given replace what was there, but
           not its kind: another --kind needs --force. A picture added as a side that another held takes that side over;
           the other keeps its place in refs, without a view. --source and --license go on the pictures of this add.
           Every picture is checked before anything is copied or written, so a refused add changes nothing. --final:
           settled; --draft (the default for a new entry): not yet
  list     the entries: kind, name, status, pictures and views
  check    every cast.json against its folder: its fields, each picture there with the bytes recorded (one changed since:
           a failure, as an image made from it would be another), views and refs agreeing on each side, the folder named
           by the id. Warned: a picture in the folder it does not list; a picture whose terms are on record nowhere (not in
           assets/ledger.json, not one bin/vh image gen made under assets/genimg/, no source and license in cast.json:
           bin/vh assets add it first); a final character, costume or prop without all four views (a 3D model from four
           views needs them); a picture on record in the ledger as made from an older version of one of its pictures, or
           from one it no longer has (make it again from the settled one, or keep it knowingly)
The pictures image gen --ref cast:<id> sends (cast:<id>:<view> sends that one) go to the vendor like any --ref: ask
first when one shows a real person or something confidential. Change a settled picture and every shot made from it
may need making again: check says which entry changed, and which pictures on record were made from it before.
--json: {"version": 1, "tool", "project", "entries": [{"id", "kind", "name", "status", "refs", "views", …}], "problems":
[{"id", "severity", "message"}]} (add: also "said", what it changed besides). Exit: 0 · 1 check or add found a failure ·
2 usage (no project, an id or a picture that is not there, a field that does not fit) · 3 an error in this tool itself,
not in the cast (said with its traceback).
"""
import argparse, hashlib, json, os, re, shutil, sys, traceback
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "assets"))
PROG = "bin/vh cast"
CAST = "cast"
FILE = "cast.json"
GENIMG = Path("assets") / "genimg"   # bin/vh image gen's pictures (tools/assets/image.py)
KINDS = ("character", "costume", "prop", "set")
MODELABLE = ("character", "costume", "prop")   # what a 3D model from four views is made of; a set is not asked for views
STATUS = ("draft", "final")
SIDES = ("front", "left", "back", "right")
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
VIEW = re.compile(r"^[a-z][a-z0-9-]{0,23}$")
NAME = re.compile(r"^[^./\\][^/\\]*$")   # a picture's file name in the folder: no path, not hidden
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
PICTURE = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
FIELDS = ("version", "id", "kind", "name", "note", "prompt", "refs", "views", "status", "palette", "scale", "gen3d")


class Usage(Exception):
    pass


def picture_problem(p):   # what is wrong with a picture by its bytes (tools/assets/image.py): a JPEG named .png, a text file
    from image import picture_problem as by_bytes   # named .png; None when name and bytes agree
    return by_bytes(p)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def project_of(arg):
    import assets as A
    try:
        return A.find(arg)
    except A.Usage as e:
        raise Usage(str(e))


def folder(project, cid):
    return Path(project) / CAST / cid


def read(project, cid):
    """cid's cast.json as it is, or None when there is none. Usage when it is not a JSON object."""
    f = folder(project, cid) / FILE
    if not f.is_file():
        return None
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Usage(f"{CAST}/{cid}/{FILE}: {e}")
    if not isinstance(d, dict):
        raise Usage(f"{CAST}/{cid}/{FILE}: not a JSON object")
    return d


def ids(project):
    """The entries' ids: the folders of cast/ that hold a cast.json, sorted."""
    root = Path(project) / CAST
    return sorted(p.parent.name for p in root.glob(f"*/{FILE}")) if root.is_dir() else []


def ledger_records(project):
    """The records of the project's ledger (assets/ledger.json), [] when there is none or it cannot be read."""
    try:
        import ledger
        _, ents, _ = ledger.entries(project)
    except Exception:   # no ledger, or one that cannot be read: nothing known from it
        return []
    return [e["record"] for e in ents if isinstance(e.get("record"), dict)]


def ledger_id(records, digest):
    """The ledger's id for these bytes, when it has a record of them (not removed); None when it has none."""
    return next((r.get("id") for r in records if r.get("sha256") == digest and "removed" not in r), None)


class Known:
    """What the project knows of where pictures came from, read once a command: the ledger's records, and the sha256s
    of image gen's pictures under assets/genimg/ (only those of a size one of the cast's pictures has are read)."""
    def __init__(self, project, sizes=()):
        self.records = ledger_records(project)
        self.ledgered = {r["sha256"] for r in self.records if isinstance(r.get("sha256"), str) and "removed" not in r}
        self.generated, sizes = set(), set(sizes)
        gen = Path(project) / GENIMG
        if sizes and gen.is_dir():
            for f in sorted(gen.rglob("*")):
                try:
                    if f.is_file() and f.suffix.lower() in PICTURE and f.stat().st_size in sizes:
                        self.generated.add(sha256(f))
                except OSError:
                    continue

    def has(self, digest):
        return digest in self.ledgered or digest in self.generated


def problems(project, cid, d, known=None):
    """[(severity, message)] of one entry: fail for what a tool cannot rely on, warn for what it can live with. known (a
    Known): also warn of the pictures whose terms are on record nowhere."""
    out, where = [], f"{CAST}/{cid}/{FILE}"
    fail = lambda m: out.append(("fail", f"{where}: {m}"))   # noqa: E731
    warn = lambda m: out.append(("warn", f"{where}: {m}"))   # noqa: E731
    for k in d:
        if k not in FIELDS:
            warn(f"an unknown field {k!r} (fields: {', '.join(FIELDS)})")
    if d.get("version") != 1:
        fail(f"version {d.get('version')!r}: 1")
    if d.get("id") != cid or not ID.match(str(cid)):
        fail(f"id {d.get('id')!r}: the folder's name, {cid!r} (a lowercase letter or digit, then letters, digits, - and _)")
    if d.get("kind") not in KINDS:
        fail(f"kind {d.get('kind')!r}: one of {', '.join(KINDS)}")
    if d.get("status") not in STATUS:
        fail(f"status {d.get('status')!r}: draft or final")
    for k in ("name", "note", "prompt", "gen3d"):
        if k in d and not isinstance(d[k], str):
            fail(f"{k}: a string")
    if not str(d.get("name") or "").strip():
        fail("name: what it is called")
    refs = d.get("refs")
    files, byfile = set(), {}
    if not isinstance(refs, list):
        fail("refs: a list of pictures [{file, view?, sha256}]")
        refs = []
    elif not refs:
        warn(f"no pictures yet (bin/vh cast add {cid} --ref picture=view)")
    for i, r in enumerate(refs):
        if not isinstance(r, dict) or not isinstance(r.get("file"), str) or not r["file"]:
            fail(f"refs[{i}]: {{\"file\": …}}"); continue
        f = r["file"]
        if not NAME.match(f):
            fail(f"refs[{i}]: {f!r}: a picture's file name in the folder (no path, not starting with a dot)"); continue
        if f in files:
            fail(f"refs[{i}]: {f} is listed twice")
        files.add(f); byfile.setdefault(f, r)
        p = folder(project, cid) / f
        if Path(f).suffix.lower() not in PICTURE:
            fail(f"refs[{i}]: {f} is not a PNG, JPEG or WebP")
        for k in ("source", "license"):
            if k in r and not isinstance(r[k], str):
                fail(f"refs[{i}]: {k}: a string")
        digest = None
        if not p.is_file():
            fail(f"refs[{i}]: {f} is not in the folder")
        elif Path(f).suffix.lower() in PICTURE and (why := picture_problem(p)):   # by its bytes, as image gen sends it
            fail(f"refs[{i}]: {f}: {why}")
        elif r.get("sha256") and (digest := sha256(p)) != r["sha256"]:
            fail(f"refs[{i}]: {f} is not the picture on record (its bytes changed): what was made from it may need making "
                 f"again; bin/vh cast add {cid} --ref {CAST}/{cid}/{f} records it as it is")
            digest = None
        elif not r.get("sha256"):
            warn(f"refs[{i}]: {f} has no sha256 (bin/vh cast add records it)")
        if "view" in r and not (isinstance(r["view"], str) and VIEW.match(r["view"])):
            fail(f"refs[{i}]: view {r['view']!r}: a lowercase word (front, left, back, right, three-quarter, sheet …)")
        said = all(isinstance(r.get(k), str) and r[k].strip() for k in ("source", "license"))
        if known is not None and digest and not said and not known.has(digest):
            warn(f"refs[{i}]: {f}: where it came from and on what terms is on record nowhere (not in assets/ledger.json, not "
                 f"made by bin/vh image gen): bin/vh assets add the file it came from first, or record both with bin/vh cast "
                 f"add {cid} --ref {CAST}/{cid}/{f} --source … --license …")
    views = d.get("views", {})
    if not isinstance(views, dict):
        fail("views: {front, left, back, right} → a picture of refs")
        views = {}
    for side, f in views.items():
        if side not in SIDES:
            fail(f"views: {side!r}: front, left, back or right")
        elif not isinstance(f, str):
            fail(f"views.{side}: a picture's file name, not {type(f).__name__} {json.dumps(f, ensure_ascii=False)[:40]}")
        elif f not in files:
            fail(f"views.{side}: {f!r} is not one of its refs")
        elif byfile[f].get("view") in SIDES and byfile[f]["view"] != side:
            fail(f"views.{side} is {f}, which refs give as the {byfile[f]['view']} view")
    for side in SIDES:   # one picture a side, the same in refs and in views
        claim = [r["file"] for r in refs if isinstance(r, dict) and isinstance(r.get("file"), str) and r.get("view") == side]
        if len(claim) > 1:
            fail(f"{', '.join(claim)} are all given as the {side} view: one picture a side (bin/vh cast add {cid} --ref "
                 f"{CAST}/{cid}/<one of them>={side} gives it to that one)")
        elif claim and views.get(side) != claim[0]:
            fail(f"refs give {claim[0]} as the {side} view, views {'has no ' + side if side not in views else 'gives ' + str(views[side])}")
    if d.get("status") == "final" and d.get("kind") in MODELABLE:
        missing = [s for s in SIDES if not isinstance(views.get(s), str)]
        if missing:
            warn(f"settled, without the {', '.join(missing)} view{'' if len(missing) == 1 else 's'}: a 3D model made from four "
                 f"views later needs all four, one picture each (the subject's own left and right)")
    pal = d.get("palette", [])
    if not isinstance(pal, list) or any(not isinstance(x, dict) or not isinstance(x.get("token"), str) or not HEX.match(str(x.get("hex", ""))) for x in pal):
        fail("palette: [{\"token\": …, \"hex\": \"#rrggbb\"}]")
    if "scale" in d and not isinstance(d["scale"], (str, dict)):
        fail("scale: a sentence, or {\"height_m\": 1.2}")
    root = folder(project, cid)
    if root.is_dir():
        extra = sorted(p.name for p in root.iterdir() if p.is_file() and p.suffix.lower() in PICTURE and p.name not in files)
        if extra:
            out.append(("warn", f"{CAST}/{cid}/: {', '.join(extra)} {'is' if len(extra) == 1 else 'are'} not in its refs (bin/vh cast add {cid} --ref {CAST}/{cid}/{extra[0]})"))
    return out


def checked(project, cid, d, known=None):
    """problems(), with anything it did not foresee in a hand-written cast.json said as a failure of that entry."""
    try:
        return problems(project, cid, d, known)
    except Exception as e:   # a shape no check expected: the entry cannot be relied on, and says why
        return [("fail", f"{CAST}/{cid}/{FILE}: could not be checked ({type(e).__name__}: {e}): mend it by hand, or make it "
                         f"again with bin/vh cast add")]


def older(cid, d, records):
    """[(warn, message)]: the ledger's records made from one of cid's pictures (their inputs) as it is no longer: other
    bytes than those on record now, or a picture the entry no longer lists."""
    refs = d.get("refs") if isinstance(d.get("refs"), list) else []
    now = {r["file"]: r.get("sha256") for r in refs if isinstance(r, dict) and isinstance(r.get("file"), str)}
    pre, out, seen = f"{CAST}/{cid}/", [], set()
    for rec in records:
        if "removed" in rec or not isinstance(rec.get("inputs"), list):
            continue
        for x in rec["inputs"]:
            if not isinstance(x, dict) or not isinstance(x.get("path"), str) or not x["path"].startswith(pre):
                continue
            f = x["path"][len(pre):]
            if (rec.get("id"), f) in seen:
                continue
            seen.add((rec.get("id"), f))
            made = f"{rec.get('id')} ({rec.get('path')})"
            if f not in now:
                out.append(("warn", f"{pre}{f}: {made} was made from it, and {cid} no longer has it among its pictures"))
            elif now[f] and x.get("sha256") and x["sha256"] != now[f]:
                out.append(("warn", f"{pre}{f}: {made} was made from an older version of it: make it again from this one, "
                                    f"or keep it knowingly"))
    return out


def summary(cid, d):
    refs = [r for r in d.get("refs") or [] if isinstance(r, dict)] if isinstance(d.get("refs"), list) else []
    return {"id": cid, "kind": d.get("kind"), "name": d.get("name"), "status": d.get("status"), "note": d.get("note", ""),
            "prompt": d.get("prompt", ""), "refs": [{k: r[k] for k in ("file", "view") if k in r} for r in refs],
            "views": d.get("views") if isinstance(d.get("views"), dict) else {}, "folder": f"{CAST}/{cid}/"}


def overview(project):
    """What bin/vh status says of the cast: None when the project has no cast/, else the entries by kind, how many are
    settled, and the failures check would find."""
    found = ids(project)
    if not (Path(project) / CAST).is_dir():
        return None
    by_kind, final, fails = {}, 0, 0
    for cid in found:
        try:
            d = read(project, cid)
        except Usage:
            fails += 1; continue
        k = str(d.get("kind"))
        by_kind[k] = by_kind.get(k, 0) + 1
        final += d.get("status") == "final"
        fails += sum(1 for s, _ in checked(project, cid, d) if s == "fail")
    return {"entries": len(found), "by_kind": by_kind, "final": final, "failures": fails}


def entry_for(project, spec):
    """--ref cast:<id>[:<view>] → (id, view or None, its cast.json). Usage when there is no such entry, or it fails check."""
    m = re.match(r"^cast:([^:]+)(?::(.+))?$", spec)
    if not m:
        raise Usage(f"--ref {spec}: cast:<id> or cast:<id>:<view>")
    cid, view = m.group(1), m.group(2)
    d = read(project, cid)
    if d is None:
        have = ids(project)
        raise Usage(f"--ref {spec}: no {CAST}/{cid}/{FILE}" + (f" (the cast: {', '.join(have)})" if have else " (bin/vh cast add makes one)"))
    bad = [m_ for s, m_ in checked(project, cid, d) if s == "fail"]
    if bad:
        raise Usage(f"--ref {spec}: {bad[0]} (bin/vh cast check {Path(project).name})")
    return cid, view, d


def refs_for(project, spec):
    """--ref cast:<id>[:<view>] (tools/assets/image.py): the pictures it names, in the entry's order: [(path, label)].
    Usage when the entry, its view or a picture is not there, or a picture is not the one on record."""
    cid, view, d = entry_for(project, spec)
    refs = [r for r in d["refs"] if not view or r.get("view") == view or (d.get("views") or {}).get(view) == r["file"]]
    if not refs:
        raise Usage(f"--ref {spec}: {cid} has no {view} picture (its views: {', '.join(sorted({r.get('view') for r in d['refs'] if r.get('view')})) or 'none named'})")
    label = f"cast:{cid} ({d['kind']}: {d['name']})"
    return [(folder(project, cid) / r["file"], label) for r in refs]


def cmd_add(a):
    project = project_of(a.project)
    if not ID.match(a.id):
        raise Usage(f"{a.id!r}: a lowercase letter or digit, then letters, digits, - and _ (up to 40)")
    if (a.source or a.license) and not a.ref:
        raise Usage("--source and --license go on the pictures of this add: give them with --ref")
    d = read(project, a.id)
    new, said = d is None, []
    if new:
        if not a.kind:
            raise Usage(f"a new entry needs --kind ({', '.join(KINDS)})")
        if not a.name:
            raise Usage("a new entry needs --name (what it is called)")
        d = {"version": 1, "id": a.id, "kind": a.kind, "name": a.name, "note": "", "refs": [], "views": {}, "status": "draft"}
    else:
        if a.kind and a.kind != d.get("kind"):
            if not a.force:
                raise Usage(f"{CAST}/{a.id}/ is a {d.get('kind')} ({d.get('name')}): --kind {a.kind} would make it another "
                            f"thing; --force to change it, or another id for the {a.kind}")
            said.append(f"kind {d.get('kind')} → {a.kind} (--force)")
        if a.name and a.name != d.get("name"):
            said.append(f"name {d.get('name')} → {a.name}")
    for k in ("kind", "name", "note", "prompt"):
        v = getattr(a, k)
        if v is not None:
            d[k] = v
    if a.final:
        d["status"] = "final"
    elif a.draft:
        d["status"] = "draft"
    root = folder(project, a.id)
    plans = []   # (source, view, as given)
    for spec in a.ref or []:
        src, view = spec, None
        m = re.match(r"^(.*)=([a-z][a-z0-9-]{0,23})$", spec)
        if m and not Path(spec).exists() and not (project / spec).exists():
            src, view = m.group(1), m.group(2)
        p = next((x for x in (Path(src), project / src) if x.is_file()), None)
        if p is None:
            raise Usage(f"--ref {spec}: no such picture (from here, nor in the project)")
        if p.suffix.lower() not in PICTURE:
            raise Usage(f"--ref {spec}: a PNG, JPEG or WebP")
        if why := picture_problem(p):   # by its bytes too: what image gen sends must be what it is named
            raise Usage(f"--ref {spec}: {why} (nothing was changed)")
        plans.append((p.resolve(), view, spec))
    # every picture's place in the folder, decided and checked before anything is copied or written
    planned, steps = {}, []   # name → the bytes it is to hold, in this add
    def holds(n, digest):
        return planned[n] == digest if n in planned else (root / n).is_file() and sha256(root / n) == digest
    def free(n):
        return n not in planned and not (root / n).exists()
    for p, view, spec in plans:
        digest = sha256(p)
        inside = p.parent == root.resolve()
        if inside:
            name = p.name
            if not NAME.match(name):
                raise Usage(f"--ref {spec}: {name} starts with a dot: rename it in {CAST}/{a.id}/ first (nothing was changed)")
        else:
            name = f"{view}{p.suffix.lower()}" if view else p.name.lstrip(".")
            if not NAME.match(name) or Path(name).suffix.lower() not in PICTURE:
                raise Usage(f"--ref {spec}: {p.name} makes no picture's file name (nothing was changed)")
            if not free(name) and not holds(name, digest):   # another picture by that name: the next free one
                stem, ext, k = Path(name).stem, Path(name).suffix.lower(), 2
                while not free(f"{stem}-{k}{ext}") and not holds(f"{stem}-{k}{ext}", digest):
                    k += 1
                name = f"{stem}-{k}{ext}"
        planned[name] = digest
        steps.append((p, view, name, digest, inside))
    records = ledger_records(project) if steps else []
    refs = [r for r in d.get("refs") or [] if isinstance(r, dict)] if isinstance(d.get("refs"), list) else []
    views = dict(d["views"]) if isinstance(d.get("views"), dict) else {}
    told = []
    for p, view, name, digest, inside in steps:
        rec = {"file": name, **({"view": view} if view else {}), "sha256": digest}
        if not inside:
            aid = ledger_id(records, digest)
            try:
                rec["from"] = {"path": p.relative_to(Path(project).resolve()).as_posix()}
            except ValueError:   # from outside the project: its name only, no path of this machine
                rec["from"] = {"file": p.name}
            if aid:
                rec["from"]["asset"] = aid
        for k in ("source", "license"):
            if getattr(a, k):
                rec[k] = getattr(a, k)
        old = next((r for r in refs if r.get("file") == name), None)
        if old is not None:
            for k in ("from", "view", "source", "license"):
                if k in old and k not in rec:
                    rec[k] = old[k]   # a picture recorded again where it lies keeps where it first came from, and its view
            refs[refs.index(old)] = rec
        else:
            refs.append(rec)
        side = rec.get("view")
        if side in SIDES:   # one picture a side: the one before gives it up, and keeps its place in refs
            for r in refs:
                if r is not rec and r.get("view") == side:
                    r.pop("view")
                    told.append(f"{name} is the {side} view now; {r['file']} keeps its place among the pictures, without a "
                                f"view (take it out of refs and the folder if it should not be sent)")
            if isinstance(views.get(side), str) and views[side] != name and not any(t.startswith(f"{name} is the {side}") for t in told):
                told.append(f"{name} is the {side} view now, not {views[side]}")
            views[side] = name
    for side in list(views):   # a picture given another side in this add no longer holds the old one
        r = next((x for x in refs if x.get("file") == views[side]), None) if isinstance(views[side], str) else None
        if r is not None and r.get("view") in SIDES and r["view"] != side:
            told.append(f"{views[side]} is the {r['view']} view now, no longer the {side}")
            del views[side]
    d["refs"], d["views"] = refs, views
    order = [k for k in FIELDS if k in d] + [k for k in d if k not in FIELDS]
    made_dir, copied = not root.exists(), []
    try:   # what this add writes; anything that fails on the way leaves the folder as it was
        root.mkdir(parents=True, exist_ok=True)
        for p, view, name, digest, inside in steps:
            if not inside and not (root / name).is_file():
                shutil.copyfile(p, root / name)
                copied.append(root / name)
        tmp = root / f".{FILE}.{os.getpid()}"
        tmp.write_text(json.dumps({k: d[k] for k in order}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        os.replace(tmp, root / FILE)
    except OSError as e:
        for f in copied:
            f.unlink(missing_ok=True)
        (root / f".{FILE}.{os.getpid()}").unlink(missing_ok=True)
        if made_dir:
            shutil.rmtree(root, ignore_errors=True)
        raise Usage(f"could not write {CAST}/{a.id}/: {e} (nothing kept)")
    said += told
    sizes = [(root / r["file"]).stat().st_size for r in refs if isinstance(r.get("file"), str) and NAME.match(r["file"]) and (root / r["file"]).is_file()]
    probs = checked(project, a.id, d, Known(project, sizes))
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} add", "project": str(project), "entries": [summary(a.id, d)], "said": said,
                          "problems": [{"id": a.id, "severity": s, "message": m} for s, m in probs]}, ensure_ascii=False, indent=1))
    else:
        recorded = [f"{name}" + (f" ({view})" if view else "") + (" as it is now" if inside else "")
                    for p, view, name, digest, inside in steps]
        print(f"cast: {'made' if new else 'updated'} {CAST}/{a.id}/ · {d['kind']} · {d['name']} · {d['status']} · "
              f"{len(refs)} picture{'' if len(refs) == 1 else 's'}" + (f" (recorded {', '.join(recorded)})" if recorded else ""))
        for x in said:
            print(f"  · {x}")
        for s, m in probs:
            print(f"  {'✗' if s == 'fail' else '!'} {m}")
    return 1 if any(s == "fail" for s, _ in probs) else 0


def gather(project):
    """[(id, cast.json or None, problems)] of every entry, and of a folder in cast/ with no cast.json (warned)."""
    rows, root = [], Path(project) / CAST
    for cid in ids(project):
        try:
            rows.append((cid, read(project, cid), None))
        except Usage as e:
            rows.append((cid, None, [("fail", str(e))]))
    sizes = []
    for cid, d, _ in rows:
        for r in (d.get("refs") if d is not None and isinstance(d.get("refs"), list) else []):
            f = folder(project, cid) / r["file"] if isinstance(r, dict) and isinstance(r.get("file"), str) and NAME.match(r["file"]) else None
            if f is not None and f.is_file():
                sizes.append(f.stat().st_size)
    known = Known(project, sizes)
    rows = [(cid, d, ps if d is None else checked(project, cid, d, known) + older(cid, d, known.records)) for cid, d, ps in rows]
    if root.is_dir():
        for p in sorted(x for x in root.iterdir() if x.is_dir() and not (x / FILE).exists()):
            rows.append((p.name, None, [("warn", f"{CAST}/{p.name}/ has no {FILE} (bin/vh cast add {p.name} --kind … --name …)")]))
    return rows


def cmd_list(a, check=False):
    project = project_of(a.project)
    rows = gather(project)
    probs = [{"id": cid, "severity": s, "message": m} for cid, _, ps in rows for s, m in ps]
    tool = f"{PROG} {'check' if check else 'list'}"
    if a.json:
        print(json.dumps({"version": 1, "tool": tool, "project": str(project), "entries": [summary(cid, d) for cid, d, _ in rows if d],
                          "problems": probs}, ensure_ascii=False, indent=1))
    else:
        if not rows:
            print(f"cast: {project.name} has no cast/ entries (bin/vh cast add <project> <id> --kind character --name … --ref a.png=front)")
        for cid, d, ps in rows:
            if d is not None and (not check or ps):
                refs = [r for r in d.get("refs") or [] if isinstance(r, dict)] if isinstance(d.get("refs"), list) else []
                views = d.get("views") if isinstance(d.get("views"), dict) else {}
                print(f"{cid:<16} {str(d.get('kind', '?')):<9} {str(d.get('status', '?')):<5} {d.get('name', '')}  · {len(refs)} picture{'' if len(refs) == 1 else 's'}"
                      + (f" · views {' '.join(k for k in SIDES if k in views)}" if views else ""))
            if check:
                for s, m in ps:
                    print(f"  {'✗' if s == 'fail' else '!'} {m}")
        if check:
            nf, ne = sum(1 for p in probs if p["severity"] == "fail"), sum(1 for r in rows if r[1] is not None)
            nw = len(probs) - nf
            print(f"cast check: {ne} entr{'y' if ne == 1 else 'ies'}, " + (f"{nf} failure{'' if nf == 1 else 's'}" if nf else "all hold")
                  + (f", {nw} warning{'' if nw == 1 else 's'}" if nw else ""))
    return 1 if check and any(p["severity"] == "fail" for p in probs) else 0


def parser():
    ap = argparse.ArgumentParser(prog=PROG, description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    sp = ap.add_subparsers(dest="cmd", metavar="{add,list,check}")
    p = sp.add_parser("add", prog=f"{PROG} add", help="make an entry, or add pictures and fields to one")
    p.add_argument("project")
    p.add_argument("id")
    p.add_argument("--kind", choices=KINDS)
    p.add_argument("--name")
    p.add_argument("--note")
    p.add_argument("--prompt")
    p.add_argument("--ref", action="append", help="a picture to copy in; picture=view names its view")
    p.add_argument("--source", help="where the pictures of this add came from (for pictures the ledger has no record of)")
    p.add_argument("--license", help="on what terms they may be used")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--final", action="store_true")
    g.add_argument("--draft", action="store_true")
    p.add_argument("--force", action="store_true", help="let --kind change the kind of an entry that is there")
    p.add_argument("--json", action="store_true")
    for name, what in (("list", "the entries"), ("check", "each cast.json against its folder")):
        q = sp.add_parser(name, prog=f"{PROG} {name}", help=what)
        q.add_argument("project")
        q.add_argument("--json", action="store_true")
    return ap


def main(argv):
    ap = parser()
    if not argv:
        ap.print_usage(sys.stderr)
        return 2
    a = ap.parse_args(argv)
    if a.cmd is None:
        ap.print_usage(sys.stderr)
        return 2
    try:
        if a.cmd == "add":
            return cmd_add(a)
        return cmd_list(a, check=a.cmd == "check")
    except Usage as e:
        print(f"{PROG} {a.cmd}: {e}", file=sys.stderr)
        return 2
    except Exception as e:   # a fault of this tool, not a check that failed (1) nor a usage (2): exit 3, with its traceback
        print(f"{PROG} {a.cmd}: an error in this tool itself, not in the cast ({type(e).__name__}: {e}); its traceback:\n"
              + traceback.format_exc().rstrip(), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
