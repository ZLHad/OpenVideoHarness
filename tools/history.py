"""bin/vh history: a safety net for the text people and agents write, in a project that may not be under git. Stdlib only.

usage: bin/vh history save <project> [--note text] [--json]
       bin/vh history list <project> [<file>] [--json]
       bin/vh history diff <project> [<file>] [--at <snapshot>] [--to <snapshot>] [--json]
       bin/vh history restore <project> <file> [--at <snapshot>] [--json]
<project> is a folder, or a name under $OVH_PROJECTS / projects/ (the date prefix optional). diff and restore also take the file alone,
by a path that leads into a project.

What is kept: the small text files tools/artifacts.json says a person or an agent writes (made_by person or agent; format
markdown, json or text; a file, not a folder of them; at most 1 MiB each, links left out): BRIEF.md, the other docs, shots.json, edit.json,
the gate pages' JSON, the script. Each by its content in .ovh/history/objects/<sha256>, and each snapshot a line of
.ovh/history/index.jsonl: {"version": 1, "id": "s3", "t", "at", "note", "files": {path: sha256}, "changed": [paths], "removed": [paths]}.
  save     a snapshot, if anything changed since the last; else nothing is written at all. bin/vh gate saves on every page that goes
           out; a failure to save never stops the page
  list     the snapshots, oldest first; with a file, those where it changed
  diff     a unified diff of a file (no file: of each that differs), from --at (default: the last snapshot) to --to (default: as it is now)
  restore  the file as it was at --at; without --at, in the newest snapshot where it differs from now. What is there now is saved first,
           so a restore can be undone: the record's undo says how. A file already as it was is left alone
--json: save {"version": 1, "tool", "project", "saved", "snapshot": {…} | null, "skipped": [{"path", "why"}]}; list {"version": 1, "tool", "project", "file",
"snapshots": [{"id", "t", "at", "note", "files": how many, "changed", "removed"}]}; diff {"version": 1, "tool", "project", "from", "to", "files": [paths that differ],
"diff": text}; restore {"version": 1, "tool", "project", "file", "from", "restored", "saved_first", "undo"}.
bin/vh clean leaves .ovh alone. Nothing here ever prunes: a snapshot of a project's text is small.
Exit: 0 · 1 no such snapshot, or no snapshot of that file · 2 usage, no project.
"""
import argparse, difflib, fcntl, hashlib, json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import activity, jsonerr   # noqa: E402,E401

MAX_FILE = 1 << 20
FORMATS = ("markdown", "json", "text")
SHA = re.compile(r"[0-9a-f]{64}\Z")
ID = re.compile(r"s[1-9][0-9]*\Z")


class Lost(Exception):
    """A snapshot or a file that is not there: exit 1."""


def store(project):
    return Path(project) / ".ovh" / "history"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tracked(project):
    """({path: bytes} of the files kept, [{path, why}] of those left out), by tools/artifacts.json."""
    import artifacts as A
    entries = A.table()["artifacts"]
    ids = {e["id"] for e in entries if e["made_by"] in ("person", "agent") and e["format"] in FORMATS and e["kind"] == "file"}
    held = A.holdings(project, A.Index(entries))
    files, skipped = {}, []
    for ident, paths in held.items():
        if ident not in ids:
            continue
        for rel in paths:
            f = Path(project) / rel
            try:
                if f.is_symlink():
                    skipped.append({"path": rel, "why": "a link"})
                elif f.stat().st_size > MAX_FILE:
                    skipped.append({"path": rel, "why": f"over {MAX_FILE >> 20} MiB"})
                else:
                    files[rel] = f.read_bytes()
            except OSError as e:
                skipped.append({"path": rel, "why": e.strerror or str(e)})
    return files, skipped


def snapshots(project):
    """The index's lines that can be read, oldest first."""
    try:
        raw = (store(project) / "index.jsonl").read_bytes()
    except OSError:
        return []
    out = []
    for line in raw.split(b"\n"):
        if not line.strip():
            continue
        try:
            r = json.loads(line.decode("utf-8", "replace"))
        except ValueError:
            continue
        if isinstance(r, dict) and r.get("version") == 1 and isinstance(r.get("id"), str) and isinstance(r.get("files"), dict):
            out.append(r)
    return out


class Lock:
    """The history's flock, around what reads its last line and adds the next."""

    def __init__(self, project):
        d = store(project)
        d.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(d / ".lock", os.O_WRONLY | os.O_CREAT, 0o644)

    def __enter__(self):
        fcntl.flock(self.fd, fcntl.LOCK_EX)
        return self

    def __exit__(self, *a):
        os.close(self.fd)


def put(project, sha, data):
    f = store(project) / "objects" / sha
    if f.is_file():
        return
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f".{sha}.{os.getpid()}")
    tmp.write_bytes(data)
    os.replace(tmp, f)


def get(project, sha):
    """An object's bytes. Lost when it is not there or not what its name says."""
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise Lost(f"the index names {sha!r} as a file's content")
    try:
        data = (store(project) / "objects" / sha).read_bytes()
    except OSError as e:
        raise Lost(f"{sha[:12]} is not in .ovh/history/objects ({e.strerror or e})") from None
    if digest(data) != sha:
        raise Lost(f".ovh/history/objects/{sha[:12]}… is not the content it was stored as")
    return data


def save(project, note=None):
    """A snapshot if anything changed. → (the snapshot or None, the files left out). OSError when it cannot be written."""
    files, skipped = tracked(project)
    hashes = {p: digest(b) for p, b in files.items()}
    left_out = {x["path"] for x in skipped}
    if not hashes and not store(project).is_dir():   # nothing to keep: not even the folder
        return None, skipped
    with Lock(project):
        snaps = snapshots(project)
        last = snaps[-1]["files"] if snaps else {}
        changed = sorted(p for p, h in hashes.items() if last.get(p) != h)
        removed = sorted(p for p in last if p not in hashes and p not in left_out)
        if not changed and not removed:
            return None, skipped
        for p in changed:
            put(project, hashes[p], files[p])
        now = time.time()
        n = 1 + max((int(s["id"][1:]) for s in snaps if ID.fullmatch(s["id"])), default=0)
        rec = {"version": 1, "id": f"s{n}", "t": round(now, 3), "at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)), "note": note, "files": hashes, "changed": changed, "removed": removed}
        fd = os.open(store(project) / "index.jsonl", os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
        try:
            os.write(fd, (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
        finally:
            os.close(fd)
    return rec, skipped


def by_id(snaps, ident):
    s = next((x for x in snaps if x["id"] == ident), None)
    if s is None:
        raise Lost(f"no snapshot {ident} (bin/vh history list has them)")
    return s


def safe(rel):
    """A path inside a project, as the index keeps it: relative, with no way out."""
    p = Path(rel)
    return not p.is_absolute() and ".." not in p.parts and rel not in ("", ".")


def text(data):
    return data.decode("utf-8", "replace").splitlines(keepends=True)


def one_diff(rel, a, b, a_name, b_name):
    lines = list(difflib.unified_diff(text(a), text(b), f"{rel} ({a_name})", f"{rel} ({b_name})"))
    return "".join(x if x.endswith("\n") else x + "\n" for x in lines)


def cmd_save(a, project):
    rec, skipped = save(project, a.note)
    if rec:
        activity.note(f"{rec['id']}: {len(rec['changed'])} changed, {len(rec['removed'])} gone" + (f" · {a.note}" if a.note else ""), [store(project) / "index.jsonl"])
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh history save", "project": str(project), "saved": bool(rec), "snapshot": rec, "skipped": skipped}, ensure_ascii=False, indent=1))
    else:
        print(f"history: {rec['id']}: {len(rec['changed'])} file(s) changed" + (f", {len(rec['removed'])} gone" if rec["removed"] else "") + f", of {len(rec['files'])}" if rec else "history: nothing changed since the last snapshot; nothing written")
        for x in skipped:
            print(f"  left out: {x['path']} ({x['why']})")
    return 0


def rel_in(project, word):
    """A file as the index keeps it, from what was typed: from the project, or a path that leads into it."""
    p = Path(word).expanduser()
    if not p.is_absolute() and (Path(project) / p).exists():
        return p.as_posix()
    try:
        return p.resolve().relative_to(Path(project).resolve()).as_posix() if p.exists() or p.is_absolute() else p.as_posix()
    except ValueError:
        return word


def cmd_list(a, project):
    rel = rel_in(project, a.file) if a.file else None
    snaps = snapshots(project)
    rows = [{"id": s["id"], "t": s.get("t"), "at": s.get("at"), "note": s.get("note"), "files": len(s["files"]), "changed": s.get("changed") or [], "removed": s.get("removed") or []}
            for s in snaps if rel is None or rel in (s.get("changed") or []) or rel in (s.get("removed") or [])]
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh history list", "project": str(project), "file": rel, "snapshots": rows}, ensure_ascii=False, indent=1))
        return 0
    if not rows:
        print("history: no snapshot yet" if rel is None else f"history: no snapshot changed {rel}")
    for r in rows:
        print(f"{r['id']:<5} {r['at'] or '?'}  {len(r['changed'])} changed of {r['files']}" + (f", {len(r['removed'])} gone" if r["removed"] else "") + (f"  {r['note']}" if r["note"] else ""))
    return 0


def cmd_diff(a, project):
    snaps = snapshots(project)
    frm = by_id(snaps, a.at) if a.at else (snaps[-1] if snaps else None)
    if frm is None:
        raise Lost("no snapshot yet: bin/vh history save makes one")
    to = by_id(snaps, a.to) if a.to else None
    now_files = None if to else tracked(project)[0]
    names = [rel_in(project, a.file)] if a.file else sorted(set(frm["files"]) | set(to["files"] if to else now_files))
    if a.file and names[0] not in frm["files"] and names[0] not in (to["files"] if to else now_files):
        raise Lost(f"{names[0]} is in neither")
    out, differ = [], []
    for rel in names:
        old = get(project, frm["files"][rel]) if rel in frm["files"] else b""
        if to:
            new = get(project, to["files"][rel]) if rel in to["files"] else b""
        else:
            new = now_files.get(rel, b"")
        if old != new:
            differ.append(rel)
            out.append(one_diff(rel, old, new, frm["id"], to["id"] if to else "now"))
    body = "".join(out)
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh history diff", "project": str(project), "from": frm["id"], "to": to["id"] if to else None, "files": differ, "diff": body}, ensure_ascii=False, indent=1))
    else:
        print(body if body else f"history: no difference from {frm['id']} to {to['id'] if to else 'now'}", end="" if body else "\n")
    return 0


def cmd_restore(a, project):
    rel = rel_in(project, a.file)
    if not safe(rel):
        return jsonerr.fail("usage", f"history: {a.file} is not a file of {project.name}")
    f = Path(project) / rel
    now = f.read_bytes() if f.is_file() else None
    snaps = snapshots(project)
    if a.at:
        snap = by_id(snaps, a.at)
        if rel not in snap["files"]:
            raise Lost(f"{rel} is not in {a.at}")
    else:
        having = [s for s in snaps if rel in s["files"]]
        if not having:
            raise Lost(f"no snapshot has {rel}")
        now_sha = digest(now) if now is not None else None
        snap = next((s for s in reversed(having) if s["files"][rel] != now_sha), None)
        if snap is None:
            snap = having[-1]
    data = get(project, snap["files"][rel])
    undo = None
    restored = now != data
    saved = None
    if restored:
        rec, _ = save(project, f"before restoring {rel} from {snap['id']}")
        saved = rec["id"] if rec else (snapshots(project) or [{}])[-1].get("id")
        f.parent.mkdir(parents=True, exist_ok=True)
        tmp = f.with_name(f".{f.name}.{os.getpid()}")
        tmp.write_bytes(data)
        if f.is_file():
            os.chmod(tmp, os.stat(f).st_mode & 0o7777)
        os.replace(tmp, f)
        undo = f"bin/vh history restore {project} {rel} --at {saved}" if saved and now is not None else None
        activity.note(f"{rel} as it was at {snap['id']}" + (f"; what was there is in {saved}" if saved else ""), [f])
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh history restore", "project": str(project), "file": rel, "from": snap["id"], "restored": restored, "saved_first": saved, "undo": undo}, ensure_ascii=False, indent=1))
    elif restored:
        print(f"history: {rel} is as it was at {snap['id']} ({snap.get('at')})" + (f"; undo: {undo}" if undo else ""))
    else:
        print(f"history: {rel} is already as it was at {snap['id']}; nothing written")
    return 0


def find_project(word):
    import gatecheck as G, review as R
    p = Path(word).expanduser()
    project = G.project_of(p) if p.exists() else None
    if project is None:
        project = R.find_project(word)
        if project is None:
            jsonerr.mark("no_project")
            return None
        if not (project / "BRIEF.md").is_file():
            jsonerr.fail("no_project", f"history: {project} is not a project (no BRIEF.md)")
            return None
    return project


def main(argv):
    if argv[:1] in (["-h"], ["--help"]):
        print(__doc__.strip())
        return 0
    if not argv or argv[0] not in ("save", "list", "diff", "restore"):
        return jsonerr.fail("usage", "bin/vh history save|list|diff|restore <project> … (bin/vh history -h)")
    p = argparse.ArgumentParser(prog=f"bin/vh history {argv[0]}", description=__doc__.split("\n\n")[0])
    p.add_argument("project")
    if argv[0] == "save":
        p.add_argument("--note")
    else:
        p.add_argument("file", nargs="?")
    if argv[0] in ("diff", "restore"):
        p.add_argument("--at")
    if argv[0] == "diff":
        p.add_argument("--to")
    p.add_argument("--json", action="store_true")
    a = p.parse_intermixed_args(argv[1:])   # (a file after an option: Python before 3.12 takes it only so)
    a.cmd = argv[0]
    if a.cmd in ("diff", "restore") and a.file is None and Path(a.project).is_file():   # the file alone: its project from its path
        a.file = str(Path(a.project).resolve())
    if a.cmd == "restore" and a.file is None:
        return jsonerr.fail("usage", "bin/vh history restore <project> <file> [--at <snapshot>]: which file?")
    project = find_project(a.project)
    if project is None:
        return 2
    try:
        return {"save": cmd_save, "list": cmd_list, "diff": cmd_diff, "restore": cmd_restore}[a.cmd](a, project)
    except Lost as e:
        return jsonerr.fail("not_found", f"history: {e}", rc=1)
    except OSError as e:
        return jsonerr.fail("failed", f"history: {e.strerror or e}: {getattr(e, 'filename', '') or ''}", rc=1)


if __name__ == "__main__":
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:
        sys.exit(0)
