"""bin/vh versions: every film bin/vh render and bin/vh patch made in a project, one version each, and the two things a
client does with them: compare a moment of two, and make an earlier one the current film again.

usage: bin/vh versions <project> [--json]
       bin/vh versions compare <project> <vA> <vB> --t <seconds> [--wipe [0.5]] [--out f.png] [--json]
       bin/vh versions use <project> <vN>
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

The record is <project>/out/versions/versions.json. Each render or patch of a video inside a project adds a version: an id
(v1, v2, …, never reused), when, the film's path (`film`) and where its bytes are now (`file`), its .render.json, how it
was made (render, patch, or found: a film that was already at the path, made by another tool or before versions were
recorded), the version it follows (`from`: the one it replaced at its path, or the one it was patched from), the spans
it changed (a render: the whole film; a patch: its frames and seconds, the frames drawn again to the keyframes, and the
shots and chapters they cross), an optional --note, and the check record of that file once there is one.
  list      the versions, oldest first; --json: {"version": 1, "project", "record", "keep", "current": {film: id},
            "kept_bytes", "versions": [...]} (tools/desk/README.md, 给客户端的数据, has every field)
  compare   the frame shown at --t seconds in each of two versions (decoded from the encoded films, so both carry x264's
            loss: the PSNR says how far apart the two films are there, not how far apart the pages draw), side by side
            (vA left) or, with --wipe, vA left of the line and vB right of it (at 0.5 of the width by default), each side
            at most 1920 px wide; the PSNR (dB, RGB; vB scaled to vA's size when they differ). Written to --out, default
            <project>/out/check/versions/<vA>-<vB>-t<seconds>.png
  use       make vN the current film at its path again: the film there now is kept first (moved into out/versions, never
            thrown away) and its check record goes with it, vN's file goes back with its .render.json and its own check
            record: the record at the path is vN's or none. Refused while bin/vh render or an in-place patch writes that
            film (their locks). Nothing is deleted
Earlier films are kept by moving them (no copy, no time): when a render or a patch replaces a film, the one it replaces
goes to out/versions/<id>/ with its .render.json and its check record. A disk-aware default: the replaced film is kept
while the disk keeps at least twice its size and 5 GB free after it, and up to OVH_KEEP_VERSIONS (default 3) earlier
versions of each film stay in the project; one beyond that, or one the disk cannot hold, goes to the Trash (said, in
the command's output, its activity note and this record), never deleted. Nothing in out/versions is ever overwritten,
and an output there is refused. A link at the film's path is replaced, never written through. A patch in place goes in
only over the film it cut (size and time); else it is put beside it. bin/vh clean prunes the kept ones with its own
rules (a list first; --yes to the Trash; --keep-versions N keeps the newest N of each film). OVH_VERSIONS=off records
nothing (a render then replaces the film as it did before versions). A video outside a project gets no record.
Exit: 0 · 1 a version that is not there or not kept, ffmpeg failed · 2 usage, no project, an unreadable record.
"""
import fcntl, json, os, re, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

RECORD = "versions.json"
KEEP_DEFAULT = 3
FLOOR = 5e9                        # bytes the disk keeps free after a kept film, at least (and twice the film's size)
VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}


class Usage(Exception):
    """A usage error: exit 2."""


def project_of(p):
    p = Path(p).resolve()
    for d in [p] + list(p.parents):
        if d.is_dir() and (d / "BRIEF.md").is_file():
            return d
    return None


def store(project):
    return Path(project) / "out" / "versions"


def place(p):
    """A path with its folders resolved but not its last part: a link stays the link (never what it points to)."""
    a = os.path.abspath(p)
    return Path(os.path.realpath(os.path.dirname(a))) / os.path.basename(a)


def rel(project, p):
    try:
        r = os.path.relpath(place(p), os.path.realpath(project))
        return Path(r).as_posix() if not r.startswith("..") else str(p)
    except ValueError:
        return str(p)


def absolute(project, r):
    return Path(r) if os.path.isabs(r) else Path(project) / r


def keep_count():
    try:
        n = int(os.environ.get("OVH_KEEP_VERSIONS", KEEP_DEFAULT))
        return n if n >= 0 else KEEP_DEFAULT
    except ValueError:
        return KEEP_DEFAULT


def free_bytes(d):
    if os.environ.get("OVH_FREE_BYTES"):   # tests (bin/vh render reads it too)
        try:
            return float(os.environ["OVH_FREE_BYTES"])
        except ValueError:
            pass
    try:
        s = os.statvfs(d)
        return s.f_bavail * s.f_frsize
    except OSError:
        return float("inf")


def human(n):
    return f"{n / 1e9:.1f} GB" if n >= 1e9 else f"{n / 1e6:.1f} MB" if n >= 1e5 else f"{n / 1e3:.0f} kB"


def identity(p):
    try:
        st = os.stat(p)
        return st.st_size, round(st.st_mtime, 6)
    except OSError:
        return None


def same(e, p):
    """Is the file at p still the bytes this version recorded (its size and modification time)?"""
    i = identity(p)
    return i is not None and i[0] == e.get("size") and abs(i[1] - (e.get("mtime") or 0)) < 0.002


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t))


# ---- the record ----

def empty():
    return {"version": 1, "note": "bin/vh render and patch: every film made in this project, one version each (bin/vh versions)",
            "next": 1, "versions": [], "events": []}


def read(project):
    """The record, or an empty one when there is none. A record that cannot be read raises ValueError."""
    f = store(project) / RECORD
    if not f.is_file():
        return empty()
    try:
        r = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"{rel(project, f)} cannot be read ({e})")
    if not isinstance(r, dict) or r.get("version") != 1 or not isinstance(r.get("versions"), list):
        raise ValueError(f"{rel(project, f)} is not a versions record (version 1)")
    r["versions"] = [e for e in r["versions"] if isinstance(e, dict) and isinstance(e.get("id"), str) and isinstance(e.get("film"), str)]
    r.setdefault("events", [])
    if not isinstance(r.get("next"), int):
        r["next"] = 1 + max([int(e["id"][1:]) for e in r["versions"] if re.fullmatch(r"v\d+", e["id"])] or [0])
    return r


def write(project, r):
    d = store(project)
    d.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".versions.", dir=d)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(json.dumps(r, ensure_ascii=False, indent=1) + "\n")
    os.replace(tmp, d / RECORD)


class Locked:
    """The record's read-modify-write under an flock on out/versions/.lock (render, patch, use and clean at once)."""
    def __init__(self, project):
        self.project = project

    def __enter__(self):
        d = store(self.project)
        d.mkdir(parents=True, exist_ok=True)
        self.f = open(d / ".lock", "a")
        fcntl.flock(self.f.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
        self.f.close()


def load_or_reset(project, said):
    """For a writer: the record, or, when it cannot be read, a new one (the old file kept as versions.json.bad-<time>,
    said), numbered on from the store's folders, so a render never fails for it."""
    try:
        return read(project)
    except ValueError as e:
        f = store(project) / RECORD
        bad = f.with_name(f"{RECORD}.bad-{time.strftime('%Y%m%d-%H%M%S')}")
        try:
            os.replace(f, bad)
        except OSError:
            pass
        said.append(f"{e}: kept as {rel(project, bad)}; a new record starts here")
        r = empty()
        ids = [int(p.name[1:]) for p in store(project).glob("v*") if re.fullmatch(r"v\d+", p.name)]
        r["next"] = 1 + max(ids or [0])
        return r


def state(project, e):
    """current (its film's path holds it), kept (in out/versions), trashed, gone (not where the record says), or changed
    (its path holds other bytes now: replaced outside bin/vh render and patch)."""
    f = e.get("file")
    if not f:
        return e.get("state") if e.get("state") in ("trashed", "gone") else "gone"
    p = absolute(project, f)
    if not os.path.lexists(p):
        return "gone"
    if not same(e, p):
        return "changed" if f == e["film"] else "gone"
    return "current" if f == e["film"] else "kept"


def current_at(project, r, film_rel):
    """The version whose bytes are at this path now, or None."""
    for e in reversed(r["versions"]):
        if e.get("file") == film_rel and state(project, e) == "current":
            return e
    return None


def sidecar_of(p):
    return Path(str(p) + ".render.json")


def load_json(p):
    try:
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except (OSError, ValueError):
        return None


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def from_sidecar(side):
    """What a .render.json says about the film: frames, fps, pixels, span, first frame; shots and chapters when the page gave them."""
    if not side:
        return {}
    pair = lambda x: x if isinstance(x, list) and len(x) == 2 and all(num(y) is not None for y in x) else None   # noqa: E731
    out = {"frames": num(side.get("frames")), "fps": num(side.get("fps")), "pixels": pair(side.get("pixels")), "span": pair(side.get("span"))}
    return {k: v for k, v in out.items() if v is not None}


def move_sidecar(src, dst):
    """Move a .render.json, its page path made relative to its new folder (bin/vh patch finds the page from it). Never
    over a file that is there; when the rewritten copy cannot be written (a full disk), the file is moved as it is."""
    if os.path.lexists(dst):
        raise OSError(f"{dst} is there already: not overwritten")
    side = load_json(src)
    if side and isinstance(side.get("page"), str) and not os.path.isabs(side["page"]):
        page = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(src)), side["page"]))
        side["page"] = os.path.relpath(page, os.path.dirname(os.path.abspath(dst)))
        try:
            Path(dst).write_text(json.dumps(side, indent=1) + "\n", encoding="utf-8")
            os.remove(src)
            return
        except OSError:
            try:
                os.remove(dst)
            except OSError:
                pass
    os.rename(src, dst)


def check_fits(j, video):
    """Is the check record j (parsed) of the bytes at video? By the size and mtime_ns the record kept of the film, so a film
    put back with an old modification time (cp -p, rsync -a, use) is not taken for the one checked; a record from before
    those were kept: made after the file was (1 s of slack)."""
    from checkrec import film_changed
    try:
        st = os.stat(video)
    except OSError:
        return False
    changed = film_changed(j, st)
    if changed is None:
        changed = not (isinstance(num(j.get("t")), (int, float)) and j["t"] >= st.st_mtime - 1)
    return not changed


def check_record(project, video):
    """The path of bin/vh check's record of this video (out/check/<name>.check.json) when there is one that is this file's
    (check_fits), else None."""
    from checkrec import record_path
    p = record_path(place(video), Path(project).resolve())
    j = load_json(p)
    return p if j and not os.path.islink(video) and check_fits(j, video) else None


def check_summary(p):
    j = load_json(p) if p else None
    if not j:
        return None
    counts = j.get("counts") if isinstance(j.get("counts"), dict) else {}
    return {"verdict": j.get("verdict") if isinstance(j.get("verdict"), str) else None, "at": j.get("at") if isinstance(j.get("at"), str) else None,
            "counts": {k: v for k, v in counts.items() if num(v) is not None}}


def new_entry(project, r, film_rel, made_by, **kw):
    n = r["next"]
    r["next"] = n + 1
    now = time.time()
    e = {"id": f"v{n}", "n": n, "t": round(now, 3), "at": iso(now), "film": film_rel, "file": film_rel, "sidecar": None,
         "made_by": made_by, "from": None, "note": None, "changed": None, "check": None, "state": "current"}
    e.update(kw)
    return e


def describe_file(project, e):
    """size, mtime and what the sidecar beside the file says, into the entry."""
    p = absolute(project, e["file"])
    i = identity(p)
    if i:
        e["size"], e["mtime"] = i
    s = sidecar_of(p)
    e["sidecar"] = rel(project, s) if s.is_file() else None
    e.update(from_sidecar(load_json(s)))


def adopt(project, r, film_rel, said):
    """A film already at the path with no version of its own: recorded as found, so it is kept like any."""
    for e in r["versions"]:   # an entry that says it is here, but the bytes here are others: those bytes are gone
        if e.get("file") == film_rel and state(project, e) == "changed":
            e["state"], e["file"], e["gone"] = "gone", None, {"at": iso(time.time()), "why": "replaced outside bin/vh render and patch"}
    e = new_entry(project, r, film_rel, "found")
    describe_file(project, e)
    r["versions"].append(e)
    said.append(f"{film_rel} was not made by bin/vh render or patch (or before versions were recorded): recorded as {e['id']} (found)")
    return e


def trash(project, e, why, said):
    """The version's file (its folder in out/versions, or the film at its path) to the Trash, as bin/vh clean moves a video."""
    import clean
    p = absolute(project, e["file"])
    d = store(project) / e["id"]
    left = None
    try:
        if p.parent == d:   # a kept version: its whole folder, named for the project and the version in the Trash
            named = d.with_name(f"{Path(project).name} {e['id']}")
            if os.path.lexists(named):
                raise OSError(f"{named.name} is there already")
            os.rename(d, named)
            try:
                clean.to_trash(named)
            except OSError:
                os.rename(named, d)
                raise
        else:
            clean.to_trash(p)   # the film first: the record follows the film's bytes
            try:
                if os.path.lexists(sidecar_of(p)):
                    clean.to_trash(sidecar_of(p))
            except OSError as x:
                left = f"its .render.json stays at {rel(project, sidecar_of(p))} ({x})"
    except OSError as x:
        said.append(f"  {e['id']} could not go to the Trash ({x}): kept in {rel(project, p.parent if p.parent == d else p)}")
        if p.parent != d and os.path.lexists(p):   # still at the film's path: keep it in the store after all, the new film takes the path
            keep(project, e, said, quiet=True)
        return False
    e.update(state="trashed", file=None, sidecar=None, gone={"at": iso(time.time()), "why": why})
    said.append(f"  {e['id']} to the Trash: {why}" + (f"; {left}" if left else ""))
    return True


def keep(project, e, said, quiet=False, move_check=False):
    """Move the version's film (and its .render.json and check record) from its path into out/versions/<id>/. Nothing
    there is overwritten. The record follows the film the moment it moves; a sidecar or a check record that cannot follow
    (a full disk) is said. move_check (bin/vh versions use): the check record at the film's path goes with it (moved, not
    copied), so the film put there next is not taken for checked; one made before this film was is moved aside too."""
    p = absolute(project, e["file"])
    d = store(project) / e["id"]
    q = d / p.name
    if os.path.lexists(q) or os.path.lexists(sidecar_of(q)):
        raise OSError(f"{rel(project, q)} is there already: an earlier film in out/versions is never overwritten")
    from checkrec import record_path
    rec = record_path(place(p), Path(project).resolve())
    chk = check_record(project, p)
    d.mkdir(parents=True, exist_ok=True)
    os.rename(p, q)
    e.update(file=rel(project, q), sidecar=None, state="kept")
    try:
        if sidecar_of(p).is_file():
            move_sidecar(sidecar_of(p), sidecar_of(q))
    except OSError as x:
        said.append(f"  {e['id']}: its .render.json stays at {rel(project, sidecar_of(p))} ({x})")
    e["sidecar"] = rel(project, sidecar_of(q)) if sidecar_of(q).is_file() else None
    try:
        if chk and move_check:
            os.rename(chk, d / chk.name)
        elif chk:
            shutil.copy2(chk, d / chk.name)
        elif move_check and os.path.lexists(rec):   # someone else's, older than this film: not the next film's either
            os.rename(rec, d / f"earlier.{rec.name}")
        if chk:
            e["check"] = rel(project, d / chk.name)
    except OSError as x:
        said.append(f"  {e['id']}: its check record could not follow it ({x})")
        if move_check and os.path.lexists(rec):
            raise OSError(f"the check record {rel(project, rec)} could not be moved aside ({x}): it would pass for the film put there next")
    if not quiet:
        said.append(f"  {e['id']} kept: {e['file']} ({human(e.get('size') or 0)}; bin/vh versions use brings it back)")


def make_room(project, r, e, said):
    """The film replaced: kept while the disk can hold it, else to the Trash (never deleted)."""
    n, size = keep_count(), e.get("size") or 0
    free = free_bytes(store(project))
    floor = max(FLOOR, 2 * size)
    why = "OVH_KEEP_VERSIONS is 0: no earlier version stays in the project" if n == 0 else \
        f"not kept: {human(free)} free on that disk, under {human(floor)} (twice its size, at least 5 GB)" if free < floor else None
    if why is None:
        keep(project, e, said)
        return
    try:   # into its own folder first, so the Trash shows "<project> vN" with its .render.json, not a bare film.mp4
        keep(project, e, said, quiet=True)
    except OSError:
        pass   # still at its path (keep moves the film first and the record follows it): trash takes it from there
    trash(project, e, why, said)


def prune(project, r, film_rel, said, protect=()):
    """Kept versions of this film beyond OVH_KEEP_VERSIONS, oldest first, to the Trash."""
    n = keep_count()
    kept = [e for e in r["versions"] if e["film"] == film_rel and e["id"] not in protect and state(project, e) == "kept"]
    for e in kept[:max(0, len(kept) - n)]:
        trash(project, e, f"more than {n} earlier version{'s' if n != 1 else ''} of {film_rel} (OVH_KEEP_VERSIONS)", said)


class Refused(Exception):
    """The new film does not go in at the path (render and patch put it beside, and say why)."""


def inside_store(project, p):
    return project is not None and (place(p).parent == store(project).resolve() or store(project).resolve() in place(p).parents)


def matches(p, expect):
    """Is the file at p the one expect ({size, mtime}) describes? (patch: the film it cut from; through a link, the file
    it points to, as the patch read it)"""
    i = identity(p)
    return i is not None and i[0] == expect.get("size") and abs(i[1] - float(expect.get("mtime") or 0)) < 0.002


def by_identity(project, r, expect):
    """The version whose bytes expect describes, wherever they are now (current or kept), or None."""
    for e in reversed(r["versions"]):
        if e.get("size") == expect.get("size") and abs((e.get("mtime") or 0) - float(expect.get("mtime") or 0)) < 0.002 \
                and state(project, e) in ("current", "kept"):
            return e
    return None


def reconcile(project, r):
    """The next id past every folder in out/versions too: an id is never given twice, even after a run that stopped
    between moving a film there and writing the record."""
    ids = [int(p.name[1:]) for p in store(project).glob("v*") if re.fullmatch(r"v\d+", p.name)] if store(project).is_dir() else []
    r["next"] = max(r["next"], 1 + max(ids or [0]), 1 + max([e.get("n") or 0 for e in r["versions"]] or [0]))


def commit(job, moved=None):
    """Put a new film in place (render and patch call this): the film at the path kept or sent to the Trash first, then
    the new one moved in with its .render.json, and its version added. job: film, new, new_sidecar, made_by, source
    (patch: the film it was made from), expect (patch: {size, mtime} of the film it cut; for --in-place the film at the
    path must still be it, for a patch to another file it names the version it came from), changed, note, problems.
    A link at the path is replaced, never written through: what it points to is left as it was. → {"id", "from",
    "lines"}; Refused when the film at the path is not the one the patch cut, or the path is a kept version's.
    moved: a dict; moved["away"] is set once the film that was at the path has left it (kept or in the Trash)."""
    film, new = place(job["film"]), Path(job["new"])
    side = Path(job["new_sidecar"]) if job.get("new_sidecar") else None
    project = project_of(film.parent)
    said, out = [], {"id": None, "from": None, "lines": []}
    moved = moved if moved is not None else {}
    off = os.environ.get("OVH_VERSIONS", "").lower() in ("off", "0", "no", "false")
    link = os.path.islink(film)
    linked = f"{rel(project, film) if project else film} was a link to {os.readlink(film)}: the link is replaced by the new film, what it points to is left as it was" if link else None
    if inside_store(project, film):
        raise Refused(f"{rel(project, film)} is inside out/versions, where the earlier versions are kept")
    if job.get("made_by") == "patch" and job.get("expect") and not job.get("source") and not matches(film, job["expect"]):
        raise Refused(f"the film at {rel(project, film) if project else film} is not the one the patch cut from (it changed while the patch "
                      "ran: another render, patch or bin/vh versions use)")
    if off or project is None:
        os.replace(new, film)   # a link: the link itself
        if side:
            os.replace(side, sidecar_of(film))
        out["lines"] = [linked] if linked else []
        return out
    with Locked(project):
        r = load_or_reset(project, said)
        reconcile(project, r)
        film_rel = rel(project, film)
        if job.get("made_by") == "patch" and job.get("expect") and not job.get("source") and not matches(film, job["expect"]):
            raise Refused(f"the film at {film_rel} is not the one the patch cut from (it changed while the patch ran: another render, patch or bin/vh versions use)")
        prev = None
        if link:
            said.append(linked)
        elif os.path.lexists(film):
            prev = current_at(project, r, film_rel) or adopt(project, r, film_rel, said)
            make_room(project, r, prev, said)
            if os.path.lexists(film):   # neither kept nor trashed (both failed): stop, the film as it was
                write(project, r)
                raise OSError(f"the film at {film_rel} could not be kept or moved to the Trash")
            moved["away"] = True
        os.replace(new, film)
        if side:
            os.replace(side, sidecar_of(film))
        src = None
        if job.get("source"):
            sp = place(job["source"])
            srel = rel(project, sp)
            if project_of(sp.parent) == project:   # the version the patch read: by its bytes, wherever they are now
                src = by_identity(project, r, job["expect"]) if job.get("expect") else None
                if src is None and (not job.get("expect") or matches(sp, job["expect"])):   # still the film the patch read
                    src = current_at(project, r, srel) or (adopt(project, r, srel, said) if sp.is_file() and not sp.is_symlink() else None)
                elif src is None:
                    said.append(f"  {srel} changed while the patch ran, and the film it read is not among the versions: where it came from is not known")
        e = new_entry(project, r, film_rel, job.get("made_by") or "render", note=job.get("note") or None, changed=job.get("changed"))
        e["from"] = (src or prev or {}).get("id")
        if job.get("problems"):
            e["problems"] = job["problems"]
        describe_file(project, e)
        r["versions"].append(e)
        prune(project, r, film_rel, said, protect=(e["id"],))
        write(project, r)
    head = f"version {e['id']}: {film_rel}" + (f" (from {e['from']})" if e["from"] else "")
    out.update(id=e["id"], **{"from": e["from"]}, lines=[head] + said)
    return out


# ---- what proxy and thumbs ask: the frames changed since a version ----

def drawn_since(project, film_rel, since_id):
    """The film frames drawn again between version since_id and the current one at this path, when every step between them
    is a patch in place ([[A, B], …], frames, both in); None when a step redrew the whole film, or the chain is broken."""
    try:
        r = read(project)
    except ValueError:
        return None
    by = {e["id"]: e for e in r["versions"]}
    cur = current_at(project, r, film_rel)
    if cur is None:
        return None
    spans, e = [], cur
    while e and e["id"] != since_id:
        ch = e.get("changed") or {}
        if e.get("made_by") != "patch" or ch.get("whole") or not isinstance(ch.get("drawn"), list) or e.get("film") != film_rel:
            return None
        spans += [s for s in ch["drawn"] if isinstance(s, list) and len(s) == 2]
        e = by.get(e.get("from"))
    return spans if e else None


# ---- the reader ----

def entry_view(project, e):
    from checkrec import film_changed
    st = state(project, e)
    out = {k: e.get(k) for k in ("id", "n", "t", "at", "film", "file", "sidecar", "made_by", "from", "note", "changed", "size",
                                 "frames", "fps", "pixels", "span", "problems", "gone")}
    out["state"] = st
    if st not in ("current", "kept"):
        out["file"] = out["sidecar"] = None
    chk = None
    if st == "current":
        chk = check_record(project, absolute(project, e["file"]))
    elif st == "kept" and e.get("check") and absolute(project, e["check"]).is_file():
        chk = absolute(project, e["check"])
        j = load_json(chk)
        try:
            if j and film_changed(j, os.stat(absolute(project, e["file"]))):   # a record that kept the film's size and mtime_ns, and they differ
                chk = None
        except OSError:
            chk = None
    out["check"] = dict(check_summary(chk), record=rel(project, chk)) if chk and check_summary(chk) else None
    return out


def listing(project):
    r = read(project)
    vs = [entry_view(project, e) for e in r["versions"]]
    cur = {v["film"]: v["id"] for v in vs if v["state"] == "current"}
    kept = sum(v.get("size") or 0 for v in vs if v["state"] == "kept")
    return {"version": 1, "project": str(project), "record": rel(project, store(project) / RECORD), "keep": keep_count(),
            "current": cur, "kept_bytes": kept, "versions": vs, "events": r.get("events") or []}


def changed_words(v):
    ch = v.get("changed") or {}
    if v.get("made_by") == "found":
        return "found at its path"
    if ch.get("whole") or not ch:
        return "the whole film"
    fr = ", ".join(f"{a}–{b}" for a, b in ch.get("frames") or [])
    secs = ", ".join(f"{a:.2f}–{b:.2f}" for a, b in ch.get("seconds") or [])
    shots = ch.get("shots") or []
    return f"frames {fr} ({secs} s)" + (f" · {', '.join(shots[:6])}{' …' if len(shots) > 6 else ''}" if shots else "")


def show(L):
    vs = L["versions"]
    print(f"versions · {Path(L['project']).name} · {len(vs)} version{'s' if len(vs) != 1 else ''} ({L['record']})")
    if not vs:
        print("  none yet: bin/vh render and bin/vh patch add one each")
        return
    w = max(len(v["film"]) for v in vs)
    for v in vs:
        where = {"current": "current", "kept": f"kept {v['file']}", "trashed": "in the Trash", "gone": "gone", "changed": "its path holds other bytes now"}[v["state"]]
        bits = [changed_words(v)]
        if v.get("pixels"):
            bits.append(f"{v.get('frames') or '?'} frames {v['pixels'][0]}x{v['pixels'][1]}")
        bits.append(where)
        if v.get("check") and v["check"].get("verdict"):
            bits.append(f"check {v['check']['verdict']}")
        if v.get("note"):
            bits.append(json.dumps(v["note"], ensure_ascii=False))
        print(f"  {v['id']:>4}  {(v.get('at') or '')[5:16].replace('T', ' ')}  {v['made_by']:<6} {v['film']:<{w}}  {('← ' + v['from']) if v.get('from') else '':<6} {' · '.join(bits)}")
    kept = [v for v in vs if v["state"] == "kept"]
    if kept:
        print(f"  kept earlier films: {len(kept)}, {human(L['kept_bytes'])} (up to {L['keep']} a film: OVH_KEEP_VERSIONS; bin/vh clean prunes them)")


# ---- compare ----

def ffprobe_fps(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate,width,height", "-of", "json", str(f)],
                       capture_output=True, text=True)
    s = (json.loads(r.stdout or "{}").get("streams") or [{}])[0]
    a, _, b = str(s.get("r_frame_rate", "0/1")).partition("/")
    try:
        fps = float(a) / float(b or 1)
    except (ValueError, ZeroDivisionError):
        fps = 0
    return fps, s.get("width"), s.get("height")


def grab(f, t, fps, out):
    """The frame shown at t (frame floor(t·fps)) as a PNG; → its frame number."""
    from timegrid import frame_at   # seconds to frames, the one way
    k = frame_at(t, fps)
    ss = max(0.0, (k - 0.5) / fps) if k > 0 else 0
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-ss", f"{ss:.6f}", "-i", str(f), "-frames:v", "1", "-f", "image2", str(out)],
                       capture_output=True, text=True)
    if r.returncode or not Path(out).is_file():
        raise RuntimeError(f"ffmpeg could not take the frame at {t} s from {f}: {(r.stderr or '').strip()[:300]}")
    return k


def secs(v):
    m = re.fullmatch(r"\s*(?:(\d+):)?(\d+):(\d+(?:\.\d+)?)\s*", str(v))
    try:
        x = (int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else float(v)
    except (TypeError, ValueError):
        raise Usage(f"--t {v}: seconds, such as 12.4 or 0:12.4")
    if not (x >= 0):
        raise Usage(f"--t {v}: seconds, such as 12.4 or 0:12.4")
    return x


def compare(project, a_id, b_id, t, wipe=None, out=None):
    L = listing(project)
    by = {v["id"]: v for v in L["versions"]}
    for i in (a_id, b_id):
        if i not in by:
            raise LookupError(f"no version {i} (the record has {', '.join(by) or 'none'})")
        if by[i]["state"] not in ("current", "kept"):
            raise LookupError(f"{i} is {by[i]['state']}: its film is not in the project to compare")
    A, B = by[a_id], by[b_id]
    fa, fb = absolute(project, A["file"]), absolute(project, B["file"])
    (pa, wa, ha), (pb, _, _) = ffprobe_fps(fa), ffprobe_fps(fb)
    if not (pa > 0 and pb > 0 and wa and ha):
        raise RuntimeError("ffprobe cannot read the frame rate and size of both films")
    out = Path(out) if out else Path(project) / "out" / "check" / "versions" / f"{a_id}-{b_id}-t{t:.3f}{'-wipe' if wipe is not None else ''}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vh-versions-") as tmp:
        ia, ib = Path(tmp) / "a.png", Path(tmp) / "b.png"
        ka, kb = grab(fa, t, pa, ia), grab(fb, t, pb, ib)
        sb = f"[1:v]scale={wa}:{ha}:flags=bicubic,format=rgb24[b]"
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostdin", "-i", str(ia), "-i", str(ib), "-lavfi", f"{sb};[0:v]format=rgb24[a];[a][b]psnr", "-f", "null", "-"],
                           capture_output=True, text=True)
        m = re.findall(r"average:(inf|[\d.]+)", r.stderr or "")
        psnr = None if not m else ("inf" if m[-1] == "inf" else round(float(m[-1]), 2))
        sc = "null" if wa <= 1920 else "scale=1920:-2:flags=bicubic"   # each side at most 1920 px wide
        if wipe is None:
            g = f"{sb};[b]{sc}[b2];[0:v]format=rgb24,{sc},pad=iw+8:ih:0:0:color=0x202020[a];[a][b2]hstack=inputs=2"
        else:
            x = max(0.0, min(1.0, wipe))
            cut = max(1, min(wa - 1, round(wa * x)))
            g = (f"{sb};[b]crop={wa - cut}:{ha}:{cut}:0[r];[0:v]format=rgb24[a];[a][r]overlay={cut}:0,"
                 f"drawbox=x={max(0, cut - 1)}:y=0:w=2:h={ha}:color=white@0.9:t=fill,{sc}")
        r2 = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-y", "-i", str(ia), "-i", str(ib), "-filter_complex", g, "-frames:v", "1", str(out)],
                            capture_output=True, text=True)
        if r2.returncode or not out.is_file():
            raise RuntimeError(f"ffmpeg could not make the picture: {(r2.stderr or '').strip()[:300]}")
    return {"version": 1, "project": str(project), "t": t, "a": {"id": a_id, "file": A["file"], "frame": ka, "fps": pa},
            "b": {"id": b_id, "file": B["file"], "frame": kb, "fps": pb}, "psnr": psnr, "layout": "wipe" if wipe is not None else "side by side",
            "wipe": wipe, "image": rel(project, out), "from": "the encoded films"}


# ---- use ----

def writer_at(film):
    """bin/vh render (<film>.lock) or an in-place bin/vh patch (<film>.patch.lock) writing this film now: (what, pid) or None."""
    for suffix, what in ((".lock", "bin/vh render"), (".patch.lock", "bin/vh patch")):
        try:
            pid = int(Path(str(film) + suffix).read_text().strip() or 0)
        except (OSError, ValueError):
            continue
        if pid > 0:
            try:
                os.kill(pid, 0)
            except PermissionError:
                return what, pid
            except OSError:
                continue
            return what, pid
    return None


def use(project, vid):
    said = []
    from checkrec import record_path
    with Locked(project):
        r = read(project)
        reconcile(project, r)
        e = next((x for x in r["versions"] if x["id"] == vid), None)
        if e is None:
            raise LookupError(f"no version {vid} (the record has {', '.join(x['id'] for x in r['versions']) or 'none'})")
        st = state(project, e)
        if st == "current":
            return {"id": vid, "film": e["film"], "already": True, "lines": [f"{vid} is the current film at {e['film']} already"]}
        if st != "kept":
            raise LookupError(f"{vid} is {st}: its film is not in the project to bring back")
        film = place(absolute(project, e["film"]))
        busy = writer_at(film)
        if busy:
            raise LookupError(f"{busy[0]} (pid {busy[1]}) is writing {e['film']}: wait for it, then use {vid}")
        rec = record_path(film, Path(project).resolve())
        displaced = None
        if os.path.islink(film):   # a link: replaced below, what it points to left as it was
            said.append(f"  {e['film']} was a link to {os.readlink(film)}: the link is replaced, what it points to is left as it was")
        elif os.path.lexists(film):
            displaced = current_at(project, r, e["film"]) or adopt(project, r, e["film"], said)
            try:
                keep(project, displaced, said, quiet=True, move_check=True)   # never to the Trash here; its check record goes with it
            except OSError:
                write(project, r)   # the record where the bytes are (keep moves the film first); vN stays kept
                raise
        if os.path.lexists(rec):   # a check record of no film here: it must not pass for vN's
            os.rename(rec, store(project) / f"{rec.name}.before-{vid}-{time.strftime('%Y%m%d-%H%M%S')}")
        src = absolute(project, e["file"])
        d = src.parent
        film.parent.mkdir(parents=True, exist_ok=True)
        os.replace(src, film)   # the path is free, or a link
        try:
            if sidecar_of(src).is_file():
                move_sidecar(sidecar_of(src), sidecar_of(film))
        except OSError as x:
            said.append(f"  {vid}: its .render.json stays at {rel(project, sidecar_of(src))} ({x})")
        if e.get("check") and absolute(project, e["check"]).is_file():   # its own check record back where bin/vh check keeps it
            rec.parent.mkdir(parents=True, exist_ok=True)
            os.rename(absolute(project, e["check"]), rec)
        try:
            d.rmdir()
        except OSError:
            pass
        e.update(file=e["film"], sidecar=rel(project, sidecar_of(film)) if sidecar_of(film).is_file() else None, state="current", check=None)
        now = time.time()
        r["events"].append({"t": round(now, 3), "at": iso(now), "event": "use", "id": vid, "film": e["film"], "displaced": displaced["id"] if displaced else None})
        write(project, r)
    return {"id": vid, "film": e["film"], "displaced": displaced["id"] if displaced else None,
            "lines": [f"{vid} is the current film at {e['film']} again" + (f"; {displaced['id']} is kept in {displaced['file']}" if displaced else "")] + said}


def mark_trashed(project, files, why):
    """bin/vh clean moved these files or folders of out/versions to the Trash: their versions say so."""
    try:
        with Locked(project):
            r = read(project)
            gone = {os.path.normpath(rel(project, f)) for f in files}
            hit = False
            for e in r["versions"]:
                if not e.get("file"):
                    continue
                f = os.path.normpath(e["file"])
                if f in gone or os.path.dirname(f) in gone:
                    e.update(state="trashed", file=None, sidecar=None, gone={"at": iso(time.time()), "why": why})
                    hit = True
            if hit:
                write(project, r)
    except (OSError, ValueError):
        pass


# ---- the command line ----

def find(arg):
    p = Path(arg).expanduser()
    if p.exists():
        return project_of(p)
    import review
    return review.find_project(arg)


def main(argv):
    import activity
    if argv and argv[0] == "_commit":   # render and patch: the job as JSON on stdin, the outcome as JSON on stdout
        import signal
        signal.signal(signal.SIGINT, signal.SIG_IGN)   # a Ctrl-C reaches render first, once the film is in place
        job, moved = json.loads(sys.stdin.read()), {}
        try:
            print(json.dumps(commit(job, moved), ensure_ascii=False))
            return 0
        except Refused as e:   # render and patch put the new film beside the path, and say why
            print(json.dumps({"error": str(e), "refused": True, "moved_away": False}, ensure_ascii=False))
            return 1
        except Exception as e:   # moved_away: the film at the path left it (kept or in the Trash), so the new one may take it
            print(json.dumps({"error": f"{type(e).__name__}: {e}", "moved_away": bool(moved.get("away"))}, ensure_ascii=False))
            return 1
    if not argv or "-h" in argv or "--help" in argv:
        print(__doc__.strip())
        return 0 if argv else 2
    sub = argv[0] if argv[0] in ("compare", "use", "list") else "list"
    rest = argv[1:] if argv[0] in ("compare", "use", "list") else argv
    js = "--json" in rest
    rest = [a for a in rest if a != "--json"]
    t = wipe = out = None
    pos, i = [], 0
    while i < len(rest):
        a = rest[i]
        if a in ("--t", "--at") or a.startswith(("--t=", "--at=")):
            v = a.split("=", 1)[1] if "=" in a else (rest[i + 1] if i + 1 < len(rest) else None)
            if v is None:
                raise Usage("--t needs the seconds")
            t = secs(v); i += 1 if "=" in a else 2
        elif a == "--wipe" or a.startswith("--wipe="):
            v = a.split("=", 1)[1] if "=" in a else (rest[i + 1] if i + 1 < len(rest) and re.fullmatch(r"\d*\.?\d+", rest[i + 1]) else None)
            if v is not None and not re.fullmatch(r"\d*\.?\d+", v.strip()) or v is not None and not 0 <= float(v) <= 1:
                raise Usage(f"--wipe {v}: where the line goes, a share of the width from 0 to 1 (0.5 by default)")
            wipe = float(v) if v is not None else 0.5
            i += 1 if "=" in a or v is None else 2
        elif a == "--out" or a.startswith("--out="):
            out = a.split("=", 1)[1] if "=" in a else (rest[i + 1] if i + 1 < len(rest) else None)
            if not out:
                raise Usage("--out needs a file (.png)")
            i += 1 if "=" in a else 2
        elif a.startswith("-"):
            raise Usage(f"unknown option {a}")
        else:
            pos.append(a); i += 1
    want = {"list": 1, "compare": 3, "use": 2}[sub]
    if len(pos) != want:
        raise Usage({"list": "bin/vh versions <project> [--json]", "compare": "bin/vh versions compare <project> <vA> <vB> --t <seconds> [--wipe [0.5]] [--out f.png] [--json]",
                     "use": "bin/vh versions use <project> <vN>"}[sub])
    project = find(pos[0])
    if project is None:
        print(f"versions: no project at {pos[0]} (a folder with BRIEF.md, or a name under projects/)", file=sys.stderr)
        return 2
    try:
        if sub == "list":
            L = listing(project)
            print(json.dumps(L, ensure_ascii=False, indent=1)) if js else show(L)
            return 0
        if sub == "compare":
            if t is None:
                raise Usage("compare needs --t <seconds>: the moment to compare")
            res = compare(project, pos[1], pos[2], t, wipe, out)
            if js:
                print(json.dumps(res, ensure_ascii=False, indent=1))
            else:
                p = res["psnr"]
                print(f"compare: {res['a']['id']} frame {res['a']['frame']} · {res['b']['id']} frame {res['b']['frame']} at {t:.3f} s · "
                      f"{res['layout']}{f' at {wipe}' if wipe is not None else ''} → {res['image']}")
                print(f"  PSNR {'∞ (the same pixels)' if p == 'inf' else f'{p} dB' if p is not None else 'not measured'} "
                      "(frames decoded from the two encoded films: both carry x264's loss, so this is how far apart the films are there, not the pages)")
            activity.note(f"{pos[1]} against {pos[2]} at {t:.3f} s: PSNR {res['psnr']}", [absolute(project, res["image"])])
            return 0
        res = use(project, pos[1])
        for line in res["lines"]:
            print(line)
        if not res.get("already"):
            activity.note(res["lines"][0], [absolute(project, res["film"])])
        return 0
    except ValueError as e:   # an unreadable record
        print(f"versions: {e}", file=sys.stderr)
        return 2
    except (LookupError, RuntimeError, OSError) as e:
        print(f"versions: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Usage as e:
        print(f"usage: {e}" if str(e).startswith("bin/vh") else f"versions: {e} (bin/vh versions -h)", file=sys.stderr)
        sys.exit(2)
    except BrokenPipeError:
        sys.exit(0)
