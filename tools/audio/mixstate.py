"""A mix's latest build attempt and the files it actually depends on (stdlib only).

The previous audio stays usable as a backup when a build fails, but its path is not
evidence that the latest attempt succeeded. mux holds the same lock while checking
and reading a tracked mix. Legacy/external audio has no record and is not attested.
"""
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import tempfile


class InvalidMix(ValueError):
    pass


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def json_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def record_path(out):
    return Path(str(Path(out).resolve()) + ".mix.json")


def as_created(path):
    # mkstemp makes 0600 files and os.replace keeps the mode: give the file the mode ffmpeg would have (the umask's)
    mask = os.umask(0)
    os.umask(mask)
    os.chmod(path, 0o666 & ~mask)


def write_record(path, value):
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        as_created(name)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextlib.contextmanager
def locked(out, shared=False):
    # Do not unlink lock files: another process could still hold the old inode.
    # mix holds it alone; any number of muxes share it (one mix onto a 4K and a 1080p picture at once).
    p = Path(str(Path(out).resolve()) + ".mix.lock")
    with p.open("a+b") as f:
        try:
            fcntl.flock(f, (fcntl.LOCK_SH if shared else fcntl.LOCK_EX) | fcntl.LOCK_NB)
        except BlockingIOError as e:
            raise InvalidMix(f"{out}: " + ("a mix is writing this audio" if shared else "another mix or mux is using this audio")
                             + "; wait for it to finish") from e
        try:
            yield
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def dependencies(kv, directory):
    paths = {Path(os.path.abspath(kv[k])) for k in ("voice", "music", "sfx", "events", "timeline", "roles") if kv.get(k)}
    event_hash = None
    if kv.get("events"):
        if not Path(kv["events"]).is_file():
            raise InvalidMix(f"events={kv['events']}: no such file")
        raw = Path(kv["events"]).read_bytes()
        event_hash = hashlib.sha256(raw).hexdigest()
        events = json.loads(raw)
        if not isinstance(events, list):
            raise InvalidMix("events: expected a list of sound events")
        for e in events:
            if not isinstance(e, dict) or not isinstance(e.get("sfx"), str):
                raise InvalidMix("events: each event needs an sfx name")
            # Track lookup candidates as well as existing recordings: a newly added
            # local/library recording can shadow what used to be a built-in sound.
            paths.add(Path(os.path.abspath(Path(kv.get("root", ".")) / e["sfx"])))
            if kv.get("lib"):
                paths.add(Path(os.path.abspath(Path(kv["lib"]) / (e["sfx"] + ".wav"))))
        if kv.get("lib"):
            paths.add(Path(os.path.abspath(Path(kv["lib"]) / "sfx-lib.json")))
    return [{"path": os.path.relpath(p, directory),
             "sha256": event_hash if event_hash and p == Path(os.path.abspath(kv["events"])) else digest(p) if p.is_file() else None}
            for p in sorted(paths)]


def changed(inputs, directory):
    for item in inputs:
        p = directory / item["path"]
        try:
            current = digest(p) if p.is_file() else None
        except OSError:
            current = "unreadable"
        if current != item["sha256"]:
            return str(p)
    return None


class Build:
    def __init__(self, out, args):
        self.out = Path(out).resolve()
        self.record = record_path(self.out)
        self.state = {"version": 1, "status": "building", "args": list(args), "args_sha256": json_hash(list(args))}
        self.temp = None
        self.discard = False

    def __enter__(self):
        self.lock = locked(self.out)
        self.lock.__enter__()
        try:
            self.had_record = self.record.exists()
            write_record(self.record, self.state)
            fd, name = tempfile.mkstemp(prefix=f".{self.out.stem}.mix-", suffix=self.out.suffix, dir=self.out.parent)
            os.close(fd)
            as_created(name)
            self.temp = name
        except BaseException:
            self.lock.__exit__(None, None, None)
            raise
        return self

    def snapshot(self, kv):
        self.state["inputs"] = dependencies(kv, self.out.parent)
        if any((self.out.parent / i["path"]).resolve() == self.out for i in self.state["inputs"]):
            self.discard = not self.had_record   # an input is not a mix: leave no record that would make mux refuse it
            raise InvalidMix("the mix output is also an input; choose a different output")
        self.state["inputs_sha256"] = json_hash(self.state["inputs"])
        write_record(self.record, self.state)

    def commit(self):
        old = changed(self.state["inputs"], self.out.parent)
        if old:
            raise InvalidMix(f"input changed while mixing: {old}; run mix again")
        self.state["output_sha256"] = digest(self.temp)
        # Mark success only after the complete audio is in place. An interruption
        # between these writes leaves 'building', which mux refuses.
        os.replace(self.temp, self.out)
        self.state["status"] = "complete"
        write_record(self.record, self.state)

    def __exit__(self, kind, exc, tb):
        try:
            if self.discard:
                self.record.unlink(missing_ok=True)
            elif kind is not None or self.state["status"] != "complete":
                self.state["status"] = "failed"
                self.state["error"] = str(exc) if exc is not None else "mix did not complete"
                write_record(self.record, self.state)
        finally:
            if self.temp and os.path.exists(self.temp):
                os.unlink(self.temp)
            self.lock.__exit__(kind, exc, tb)


def validate(out, record):
    try:
        with record.open(encoding="utf-8") as f:
            state = json.load(f)
        if state["version"] != 1:
            raise InvalidMix(f"{record}: unsupported mix record version; rebuild the mix")
        if state["status"] != "complete":
            raise InvalidMix(f"{out}: latest mix is {state['status']}; the old audio is not this build. Run mix successfully before mux")
        if not isinstance(state["inputs"], list) or not state["inputs"]:
            raise InvalidMix(f"{record}: no recorded inputs; rebuild the mix")
        if state["args_sha256"] != json_hash(state["args"]) or state["inputs_sha256"] != json_hash(state["inputs"]):
            raise InvalidMix(f"{record}: mix record changed; rebuild the mix")
        old = changed(state["inputs"], out.parent)
        if old:
            raise InvalidMix(f"{out}: input changed or is missing: {old}; rebuild the mix before mux")
        if digest(out) != state["output_sha256"]:
            raise InvalidMix(f"{out}: audio changed since the successful mix; rebuild it before mux "
                             "(an edit made on purpose: save it under another name and mux that file, which has no mix record)")
        return state
    except (OSError, KeyError, TypeError, json.JSONDecodeError) as e:
        raise InvalidMix(f"{record}: cannot verify this mix ({e}); rebuild it before mux") from e


@contextlib.contextmanager
def verified(out):
    out = Path(out).resolve()
    record = record_path(out)
    if not record.exists():
        yield False
        if record.exists():
            raise InvalidMix(f"{out}: a mix build started during mux; run mux again")
        return
    with locked(out, shared=True):
        state = validate(out, record)
        yield True
        # Sources can be edited by tools that do not use the mix lock. Check again
        # before mux publishes its temporary result.
        if state != validate(out, record):
            raise InvalidMix(f"{record}: mix record changed during mux; run mux again")
