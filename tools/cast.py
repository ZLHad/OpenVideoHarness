"""bin/vh cast: a project's cast, the settled references of what must look the same in every shot: its characters,
costumes, props and sets. One folder each, cast/<id>/, with its pictures and cast.json, which the tools read (image gen
--ref cast:<id>; a 3D model made from four views later). Stdlib only.

usage: bin/vh cast add <project> <id> [--kind character|costume|prop|set] [--name N] [--note TEXT] [--prompt TEXT]
                       [--ref picture[=view] …] [--final | --draft] [--json]
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
  refs     the pictures in the folder, in the order image gen sends them: [{"file", "view", "sha256", "from"}]. view
           (optional): front, left, back, right, three-quarter, top, sheet, detail, pose, expression, or another lowercase
           word; from (optional): where add copied it from, {"path", "asset"} (the project path, and its ledger id when
           assets/ledger.json has a record of those bytes)
  views    {"front", "left", "back", "right"}: which picture is which side (the files), for a 3D model made from four
           views (model3d gen --views, to come: it is to read these four, and write the model to gen3d)
  status   draft | final: final once the person has settled it (gate ②, or the character stop E0 of the director modes)
  palette  [{"token", "hex"}] (optional); scale: a sentence or {"height_m": 1.2} (optional); gen3d: the folder a 3D
           model of it goes in, assets/gen3d/<id>/ (optional, for later)
  add      makes cast/<id>/, or adds to it: copies each --ref picture in (PNG, JPEG or WebP; picture=view names its view, and
           the copy is <view>.<ext> when that name is free), records its sha256 and where it came from, a front/left/back/
           right view in views too, and writes cast.json; the fields given replace what was there. --final: settled;
           --draft (the default for a new entry): not yet
  list     the entries: kind, name, status, pictures and views
  check    every cast.json against its folder: its fields, each picture there with the bytes recorded (one changed since:
           a failure, as an image made from it would be another), views naming pictures it has, the folder named by the
           id; a picture in the folder it does not list is said (a warning)
The pictures image gen --ref cast:<id> sends (cast:<id>:<view> sends that one) go to the vendor like any --ref: ask
first when one shows a real person or something confidential. Change a settled picture and every shot made from it
may need making again: check says which entry changed.
--json: {"version": 1, "tool", "project", "entries": [{"id", "kind", "name", "status", "refs", "views", …}], "problems":
[{"id", "severity", "message"}]}. Exit: 0 · 1 check found a failure · 2 usage (no project, an id or a picture that is not
there, a field that does not fit).
"""
import argparse, hashlib, json, re, shutil, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "assets"))
PROG = "bin/vh cast"
CAST = "cast"
FILE = "cast.json"
KINDS = ("character", "costume", "prop", "set")
STATUS = ("draft", "final")
SIDES = ("front", "left", "back", "right")
ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,39}$")
VIEW = re.compile(r"^[a-z][a-z0-9-]{0,23}$")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
PICTURE = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
FIELDS = ("version", "id", "kind", "name", "note", "prompt", "refs", "views", "status", "palette", "scale", "gen3d")


class Usage(Exception):
    pass


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


def problems(project, cid, d):
    """[(severity, message)] of one entry: fail for what a tool cannot rely on, warn for what it can live with."""
    out, where = [], f"{CAST}/{cid}/{FILE}"
    fail = lambda m: out.append(("fail", f"{where}: {m}"))   # noqa: E731
    for k in d:
        if k not in FIELDS:
            out.append(("warn", f"{where}: an unknown field {k!r} (fields: {', '.join(FIELDS)})"))
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
    files = set()
    if not isinstance(refs, list):
        fail("refs: a list of pictures [{file, view?, sha256}]")
        refs = []
    for i, r in enumerate(refs):
        if not isinstance(r, dict) or not isinstance(r.get("file"), str) or not r["file"]:
            fail(f"refs[{i}]: {{\"file\": …}}"); continue
        f = r["file"]
        if "/" in f or "\\" in f or f.startswith("."):
            fail(f"refs[{i}]: {f!r} is a picture in the folder: a file name, no path"); continue
        if f in files:
            fail(f"refs[{i}]: {f} is listed twice")
        files.add(f)
        p = folder(project, cid) / f
        if Path(f).suffix.lower() not in PICTURE:
            fail(f"refs[{i}]: {f} is not a PNG, JPEG or WebP")
        if not p.is_file():
            fail(f"refs[{i}]: {f} is not in the folder")
        elif r.get("sha256") and sha256(p) != r["sha256"]:
            fail(f"refs[{i}]: {f} is not the picture on record (its bytes changed): what was made from it may need making "
                 f"again; bin/vh cast add {cid} --ref {CAST}/{cid}/{f} records it as it is")
        elif not r.get("sha256"):
            out.append(("warn", f"{where}: refs[{i}]: {f} has no sha256 (bin/vh cast add records it)"))
        if "view" in r and not (isinstance(r["view"], str) and VIEW.match(r["view"])):
            fail(f"refs[{i}]: view {r['view']!r}: a lowercase word (front, left, back, right, three-quarter, sheet …)")
    views = d.get("views", {})
    if not isinstance(views, dict):
        fail("views: {front, left, back, right} → a picture of refs")
        views = {}
    for side, f in views.items():
        if side not in SIDES:
            fail(f"views: {side!r}: front, left, back or right")
        elif f not in files:
            fail(f"views.{side}: {f!r} is not one of its refs")
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


def summary(cid, d):
    refs = [r for r in d.get("refs") or [] if isinstance(r, dict)]
    return {"id": cid, "kind": d.get("kind"), "name": d.get("name"), "status": d.get("status"), "note": d.get("note", ""),
            "prompt": d.get("prompt", ""), "refs": [{k: r[k] for k in ("file", "view") if k in r} for r in refs],
            "views": d.get("views") if isinstance(d.get("views"), dict) else {}, "folder": f"{CAST}/{cid}/"}


def overview(project):
    """What bin/vh status --json says of the cast: None when the project has no cast/, else the entries by kind, how
    many are settled, and the failures check would find."""
    found = ids(project)
    if not (Path(project) / CAST).is_dir():
        return None
    by_kind, final, fails = {}, 0, 0
    for cid in found:
        try:
            d = read(project, cid)
        except Usage:
            fails += 1; continue
        by_kind[d.get("kind")] = by_kind.get(d.get("kind"), 0) + 1
        final += d.get("status") == "final"
        fails += sum(1 for s, _ in problems(project, cid, d) if s == "fail")
    return {"entries": len(found), "by_kind": by_kind, "final": final, "failures": fails}


def refs_for(project, spec):
    """--ref cast:<id>[:<view>] (tools/assets/image.py): the pictures it names, in the entry's order: [(path, label)].
    Usage when the entry, its view or a picture is not there, or a picture is not the one on record."""
    m = re.match(r"^cast:([^:]+)(?::(.+))?$", spec)
    if not m:
        raise Usage(f"--ref {spec}: cast:<id> or cast:<id>:<view>")
    cid, view = m.group(1), m.group(2)
    d = read(project, cid)
    if d is None:
        have = ids(project)
        raise Usage(f"--ref {spec}: no {CAST}/{cid}/{FILE}" + (f" (the cast: {', '.join(have)})" if have else " (bin/vh cast add makes one)"))
    bad = [m_ for s, m_ in problems(project, cid, d) if s == "fail"]
    if bad:
        raise Usage(f"--ref {spec}: {bad[0]} (bin/vh cast check {project.name})")
    refs = [r for r in d["refs"] if not view or r.get("view") == view or (d.get("views") or {}).get(view) == r["file"]]
    if not refs:
        raise Usage(f"--ref {spec}: {cid} has no {view} picture (its views: {', '.join(sorted({r.get('view') for r in d['refs'] if r.get('view')})) or 'none named'})")
    label = f"cast:{cid} ({d['kind']}: {d['name']})"
    return [(folder(project, cid) / r["file"], label) for r in refs]


def ledger_id(project, digest):
    """The ledger's id for these bytes, when assets/ledger.json has a record of them; None when it has none (or no ledger)."""
    try:
        import ledger
        _, ents, _ = ledger.entries(project)
    except Exception:   # no ledger, or one that cannot be read: the copy just has no ledger id
        return None
    for e in ents:
        r = e["record"]
        if r.get("sha256") == digest and "removed" not in r:
            return r.get("id")
    return None


def cmd_add(a):
    project = project_of(a.project)
    if not ID.match(a.id):
        raise Usage(f"{a.id!r}: a lowercase letter or digit, then letters, digits, - and _ (up to 40)")
    d = read(project, a.id)
    new = d is None
    if new:
        if not a.kind:
            raise Usage(f"a new entry needs --kind ({', '.join(KINDS)})")
        if not a.name:
            raise Usage("a new entry needs --name (what it is called)")
        d = {"version": 1, "id": a.id, "kind": a.kind, "name": a.name, "note": "", "refs": [], "views": {}, "status": "draft"}
    for k in ("kind", "name", "note", "prompt"):
        v = getattr(a, k)
        if v is not None:
            d[k] = v
    if a.final:
        d["status"] = "final"
    elif a.draft:
        d["status"] = "draft"
    root = folder(project, a.id)
    plans = []   # (source, view)
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
        plans.append((p.resolve(), view))
    root.mkdir(parents=True, exist_ok=True)
    refs = [r for r in d.get("refs") or [] if isinstance(r, dict)]
    said = []
    for p, view in plans:
        digest = sha256(p)
        inside = p.parent == root.resolve()
        name = p.name if inside else (f"{view}{p.suffix.lower()}" if view else p.name)
        if not inside:
            target = root / name
            if target.exists() and sha256(target) != digest:   # another picture by that name: the next free one
                stem, k = Path(name).stem, 2
                while (root / f"{stem}-{k}{p.suffix.lower()}").exists():
                    k += 1
                name = f"{stem}-{k}{p.suffix.lower()}"
            shutil.copyfile(p, root / name)
        rec = {"file": name, **({"view": view} if view else {}), "sha256": digest}
        if not inside:
            try:
                rel = p.relative_to(Path(project).resolve()).as_posix()
            except ValueError:
                rel = str(p)
            aid = ledger_id(project, digest)
            rec["from"] = {"path": rel, **({"asset": aid} if aid else {})}
        old = next((r for r in refs if r.get("file") == name), None)
        if old is not None:
            if "from" in old and "from" not in rec:
                rec["from"] = old["from"]   # a picture recorded again where it lies keeps where it first came from
            if view is None and "view" in old:
                rec["view"] = old["view"]
            refs[refs.index(old)] = rec
        else:
            refs.append(rec)
        if (view or rec.get("view")) in SIDES:
            d.setdefault("views", {})[view or rec["view"]] = name
        said.append(f"{name}" + (f" ({rec['view']})" if rec.get("view") else "") + (" as it is now" if inside else f" from {rec['from']['path']}"))
    d["refs"] = refs
    d.setdefault("views", {})
    order = [k for k in FIELDS if k in d] + [k for k in d if k not in FIELDS]
    (root / FILE).write_text(json.dumps({k: d[k] for k in order}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    probs = problems(project, a.id, d)
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} add", "project": str(project), "entries": [summary(a.id, d)],
                          "problems": [{"id": a.id, "severity": s, "message": m} for s, m in probs]}, ensure_ascii=False, indent=1))
    else:
        print(f"cast: {'made' if new else 'updated'} {CAST}/{a.id}/ · {d['kind']} · {d['name']} · {d['status']} · "
              f"{len(refs)} picture{'' if len(refs) == 1 else 's'}" + (f" (recorded {', '.join(said)})" if said else ""))
        for s, m in probs:
            print(f"  {'✗' if s == 'fail' else '!'} {m}")
    return 1 if any(s == "fail" for s, _ in probs) else 0


def gather(project):
    """[(id, cast.json or None, problems)] of every entry, and of a folder in cast/ with no cast.json (warned)."""
    rows = []
    root = Path(project) / CAST
    for cid in ids(project):
        try:
            d = read(project, cid)
        except Usage as e:
            rows.append((cid, None, [("fail", str(e))])); continue
        rows.append((cid, d, problems(project, cid, d)))
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
                refs = [r for r in d.get("refs") or [] if isinstance(r, dict)]
                views = d.get("views") if isinstance(d.get("views"), dict) else {}
                print(f"{cid:<16} {d.get('kind', '?'):<9} {d.get('status', '?'):<5} {d.get('name', '')}  · {len(refs)} picture{'' if len(refs) == 1 else 's'}"
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
    g = p.add_mutually_exclusive_group()
    g.add_argument("--final", action="store_true")
    g.add_argument("--draft", action="store_true")
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


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
