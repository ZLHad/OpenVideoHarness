"""A project's identity: <project>/.ovh/project.json, {"version": 1, "id", "created"}. Stdlib only.

usage: python3 tools/identity.py <project>     the id, written first if the project has none (bin/vh new; bin/vh projects --assign)

The id is random, says nothing of the path and never changes, so a folder that moves keeps it and a client can hold on to
it. created is when the id was made: bin/vh new's time, or for an older project the time of bin/vh projects --assign. A
command that only reads never writes this file: read() gives None until a command that writes asks (ensure). A folder
copied whole carries the id with it: bin/vh projects says so (same_id_as); take .ovh/project.json out of the copy, and
--assign gives it its own. A file there that is no such record is moved aside (project.json.bad-<time>), never overwritten; one of
a later version is a later bin/vh's, and is left as it is, with an OSError that says so.
Exit: 0 · 1 it could not be written · 2 usage.
"""
import json, os, sys, time, uuid
from pathlib import Path


def path(project):
    return Path(project) / ".ovh" / "project.json"


def read(project):
    """The record, or None: no file, or one that is not {"version": 1, "id": "…"}. Never raises, never writes."""
    try:
        d = json.loads(path(project).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return d if isinstance(d, dict) and d.get("version") == 1 and isinstance(d.get("id"), str) and d["id"] else None


def id_of(project):
    rec = read(project)
    return rec["id"] if rec else None


def later_version(f):
    """The version of a record this bin/vh is too old to read, else None."""
    try:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    v = d.get("version") if isinstance(d, dict) else None
    return v if isinstance(v, int) and not isinstance(v, bool) and v > 1 else None


def ensure(project):
    """(the record, was it written now): the project's own, or a new one. OSError when it cannot be written. O_EXCL: two
    commands at once end up with one id, the first one's."""
    rec = read(project)
    if rec:
        return rec, False
    f = path(project)
    f.parent.mkdir(exist_ok=True)
    if f.exists():
        later = later_version(f)
        if later:
            raise OSError(f"it is of version {later}, a later bin/vh's: left as it is")
        os.replace(f, f.with_name(f"{f.name}.bad-{int(time.time())}"))   # a hand edit or a tool's bug: kept to look at
    rec = {"version": 1, "id": uuid.uuid4().hex, "created": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
    try:
        fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError:
        return read(project) or rec, False
    try:
        os.write(fd, (json.dumps(rec) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    return rec, True


def main(argv):
    if len(argv) != 1 or argv[0].startswith("-"):
        print(__doc__.strip(), file=sys.stderr if argv[:1] not in (["-h"], ["--help"]) else sys.stdout)
        return 0 if argv[:1] in (["-h"], ["--help"]) else 2
    try:
        print(ensure(argv[0])[0]["id"])
    except OSError as e:
        print(f"identity: {path(argv[0])}: {e.strerror or e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
