"""What a client relies on, held to tools/schemas/output/: tools/ci.sh's contract_checks. No network, no paid call.

usage: python3 tools/test_contract.py <bash>     (bin/vh runs under this bash) a line each, ok<TAB>… or bad<TAB>…, and end<TAB>…

It makes a small project of each kind in a temporary folder (fixture below: a film with its records, an edit list, the review
desk's fixture with a page and a submission) and:
  - runs each command with --json and holds what it prints to its schema (tools/schemalite.py): a field the schema requires
    that is gone, or of another type, fails; a field the schema does not name fails too, where it names the object's fields, so
    a new field gets written down and its loss is seen from then on. A client takes fields it does not know: extra is allowed
    in the schema, and asked for here. Objects whose keys are data (a Spec, a map of films) name none;
  - takes every required field out of a real output in turn and expects the schema to notice;
  - runs each command's failures (failures() below) and holds each to the error's shape, its code and its exit status, and,
    without --json, to the same exit status and the same words.
"""
import glob, json, os, shutil, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import schemalite   # noqa: E402

SCHEMAS = HERE / "schemas" / "output"
ALL = ("status", "activity", "versions", "check", "commands", "desk-data", "edit-list", "edit-build", "assets-list", "artifacts-list", "projects", "error", "cancel", "peaks", "timeline", "history")


class VH:
    def __init__(self, sh, env=None):
        self.sh, self.env = sh, dict(os.environ, **(env or {}))

    def __call__(self, *args, **kw):
        return subprocess.run([self.sh, str(ROOT / "bin" / "vh"), *args], capture_output=True, text=True, stdin=subprocess.DEVNULL, env=self.env, **kw)


def write(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text, encoding="utf-8")


def line(path, **rec):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(dict({"v": 1}, **rec), ensure_ascii=False) + "\n")


def fixture(t, sh):
    """The projects: p (bin/vh new, a film, its render, check, version and delivery records, a ledger, a cast and research folder, a
    log with each kind of line), z (the desk's fixture with a page and a submission), e (an edit list), and bad things for the
    failures. → (vh, p, z, e, whether there is a film)."""
    vh = VH(sh, {"OVH_PROJECTS": f"{t}/projects"})
    r = vh("new", "math", "ci-contract")
    if r.returncode:
        raise SystemExit(f"bin/vh new: exit {r.returncode}: {r.stderr[-400:]}")
    p = glob.glob(f"{t}/projects/*-ci-contract")[0]
    z = f"{t}/projects/zh"
    shutil.copytree(ROOT / "tools" / "desk" / "fixtures" / "zh", z)
    os.makedirs(f"{p}/cast")
    os.makedirs(f"{p}/research")
    has_film = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
    if has_film:
        film = f"{p}/out/final.mp4"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=160x90:r=10:d=1", "-f", "lavfi", "-i", "sine=d=1", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", film], check=True)
        write(film + ".render.json", json.dumps({"version": 1, "frames": 10, "fps": 10, "pixels": [160, 90], "span": [0, 1], "seconds": 1, "patches": []}))
        s = os.stat(film)
        write(f"{p}/out/versions/versions.json", json.dumps({"version": 1, "next": 2, "versions": [{
            "id": "v1", "n": 1, "t": s.st_mtime, "at": "2026-11-06T10:00:00+0800", "film": "out/final.mp4", "file": "out/final.mp4", "sidecar": "out/final.mp4.render.json",
            "made_by": "render", "from": None, "note": None, "changed": {"whole": True}, "size": s.st_size, "mtime": s.st_mtime, "frames": 10, "fps": 10, "pixels": [160, 90], "span": [0, 1]}], "events": []}))
        shutil.copy(film, f"{p}/out/final.upload.mp4")
        u = os.stat(f"{p}/out/final.upload.mp4")
        write(f"{p}/out/final.upload.mp4.deliver.json", json.dumps({"version": 1, "tool": "bin/vh deliver", "output": "final.upload.mp4", "size": u.st_size, "mtime": u.st_mtime, "master": "final.mp4",
                                                                 "master_size": s.st_size, "master_mtime": s.st_mtime, "args": [], "time": "2026-11-06T10:00:00+0800"}))
    write(f"{p}/assets/a.bin", "x")
    r = vh("assets", "add", p, "assets/a.bin", "--kind", "data", "--license", "cc0", "--origin", "self")
    if r.returncode:
        raise SystemExit(f"bin/vh assets add: exit {r.returncode}: {r.stderr[-400:]}")
    # the log: a run with progress and with why it failed, a line outside any run
    log, now = f"{p}/.ovh/activity.jsonl", time.time()
    line(log, event="start", run="1-1", t=now - 9, cmd="render", args=["p"], cwd="/x", pid=1 << 22)
    line(log, event="progress", run="1-1", t=now - 8, cmd="render", done=5, total=10, unit="frames")
    line(log, event="note", run="1-1", t=now - 7, cmd="render", level="error", code="failed", summary="it stopped")
    line(log, event="end", run="1-1", t=now - 6, cmd="render", exit=1, duration=3)
    line(log, event="feedback", t=now - 5, round="1", file="out/review/feedback/x.json", items={"ok": 1})
    # a page out and a submission for it, in the desk's fixture
    r = vh("review", z, "1")
    if r.returncode:
        raise SystemExit(f"bin/vh review: exit {r.returncode}: {r.stderr[-400:]}")
    r = vh("history", "save", p, "--note", "the fixture")
    if r.returncode:
        raise SystemExit(f"bin/vh history save: exit {r.returncode}: {r.stderr[-400:]}")
    write(f"{z}/out/review/feedback/1-a.json", json.dumps({"version": 1, "round": "1", "at": "2026-11-06T10:00:00+0800", "decisions": {}, "defaulted": [], "general": "",
                                                           "items": [{"target": "time:1.5", "status": "ask", "label": "小样 0:01.5", "text": "这里看不清", "t": 1.5}]}, ensure_ascii=False))
    e = f"{t}/projects/e"
    write(f"{e}/BRIEF.md", "# BRIEF：剪辑表\n")
    write(f"{e}/edit.json", json.dumps({"v": 1, "fps": 30, "size": [320, 180], "sources": {"black": {"color": "#000000"}, "white": {"color": "#ffffff"}},
                                        "tracks": [{"id": "V1", "entries": [{"id": "S01", "src": "black", "dur": 1, "segment": "a", "reads": "x"}, {"id": "S02", "src": "white", "dur": 1},
                                                                            {"id": "S03", "src": None, "dur": 0.5, "unsure": "no picture yet"}]}],
                                        "chapters": [{"t": 0, "title": "one"}]}))
    # for the failures
    os.makedirs(f"{t}/plain")
    b = f"{t}/bad"
    for f in ("BRIEF.md", "REVIEW.md"):
        write(f"{b}/{f}", "# x\n")
    for f in ("out/versions/versions.json", "assets/ledger.json", "edit.json", "out/review/gate-1.json"):
        write(f"{b}/{f}", "not json")
    write(f"{b}/out/x.mp4", "no film here")
    return vh, p, z, e, has_film


def outputs(vh, p, z, e, has_film):
    """{name: [(the command as a line, what it printed)]}: each --json output of the fixture. Exit status 0, but a failed check's."""
    runs = [("status", ["status", p]), ("status", ["status", z]), ("activity", ["activity", p]), ("activity", ["activity", z]), ("versions", ["versions", p]),
            ("commands", ["commands"]), ("commands", ["commands", "--stage", "8"]), ("desk-data", ["desk", "data", z]), ("desk-data", ["desk", "data", p]),
            ("edit-list", ["edit", "list", e]), ("edit-build", ["edit", "build", e]), ("assets-list", ["assets", "list", p]), ("artifacts-list", ["artifacts", "list", p]),
            ("artifacts-list", ["artifacts", "list", z]), ("projects", ["projects"]), ("cancel", ["cancel", p]), ("timeline", ["timeline", p, "--resolved"]), ("timeline", ["timeline", z, "--resolved"]), ("timeline", ["timeline", e, "--resolved"]), ("history", ["history", "list", p])]
    if has_film:
        runs.insert(0, ("check", ["check", f"{p}/out/final.mp4"]))   # first: status and the others have its record
        runs.append(("peaks", ["peaks", f"{p}/out/final.mp4", "--bins", "8"]))
    out, bad = {}, []
    for name, args in runs:
        r = vh(*args, "--json")
        said = " ".join(args).replace(str(Path(p).parent), "…")
        if r.returncode not in ((0, 1) if name == "check" else (0,)):
            bad.append(f"{said} --json: exit {r.returncode}: {r.stderr[-300:]}")
            continue
        try:
            out.setdefault(name, []).append((said, json.loads(r.stdout)))
        except ValueError:
            bad.append(f"{said} --json: not JSON: {r.stdout[:200]!r}")
    return out, bad


def failures(t, p):
    """(the arguments without --json, the exit status, the code, the words are the same without --json)."""
    plain, broken = f"{t}/plain", f"{t}/bad"
    return [
        ("status", 2, "usage", False), ("status nope", 2, "no_project", True), (f"status {plain}", 2, "no_project", True),
        ("activity", 2, "usage", False), ("activity nope", 2, "no_project", True), (f"activity {plain}", 2, "no_project", True),
        ("versions", 2, "usage", True), ("versions nope", 2, "no_project", True), (f"versions {broken}", 2, "invalid", True), (f"versions compare {p} v8 v9 --t 1", 1, "not_found", True), (f"versions {p} --bogus", 2, "usage", True),
        ("check", 2, "usage", False), ("check --bogus", 2, "usage", True), (f"check {t}/nofile.mp4", 2, "not_found", True), (f"check {plain}", 2, "no_project", True), (f"check {broken}/out/x.mp4 --bogus", 2, "usage", True),
        (f"check {broken}/out/x.mp4 --against {t}/nofile.mp4", 2, "not_found", True), (f"check {t}/projects/e", 2, "not_found", True),
        ("assets list", 2, "usage", True), ("assets list nope", 2, "no_project", True), (f"assets list {plain}", 2, "no_project", True), (f"assets list {broken}", 2, "invalid", True), ("assets nope", 2, "no_project", True),
        ("edit", 2, "usage", False), ("edit list nope", 2, "no_project", True), (f"edit list {p}", 2, "not_found", True), (f"edit build {p}", 2, "not_found", True), (f"edit list {broken}", 2, "invalid", True), (f"edit build {broken}", 2, "invalid", True),
        ("proxy", 2, "usage", False), ("proxy nope", 2, "no_project", True), (f"proxy {plain}", 2, "not_found", True), (f"proxy {t}/projects/e --size nope", 2, "usage", True), (f"proxy {p} --bogus", 2, "usage", True),
        ("thumbs", 2, "usage", False), ("thumbs nope", 2, "no_project", True), (f"thumbs {broken}/out --every nope", 2, "usage", True),
        ("artifacts", 2, "usage", False), ("artifacts list", 2, "usage", True), ("artifacts list nope", 2, "no_project", True), ("artifacts spec --stage nope", 2, "usage", True), ("artifacts bogus", 2, "usage", True),
        ("projects --bogus", 2, "usage", True), (f"projects --root {t}/nope", 2, "not_found", True),
        ("commands --stage nope", 2, "usage", True), ("commands --bogus", 2, "usage", True),
        ("doctor --bogus", 2, "usage", True), (f"doctor {p}", 2, "usage", False),
        ("desk data", 2, "usage", True), ("desk data nope", 2, "no_project", True),
        ("gate", 2, "usage", False), ("gate nope", 2, "no_project", True), (f"gate {p} 1", 2, "invalid", True), (f"gate {broken} 1", 2, "invalid", True), (f"gate {p} 1 --wait", 2, "usage", False), (f"gate {p} 1 --init --wait", 2, "usage", True),
        ("new", 2, "usage", False), ("new short", 2, "usage", False), ("new nope x", 2, "usage", True), ("new short x --bogus", 2, "usage", True), ("new short x --effort nope", 2, "usage", True),
        ("new short x --from nope", 2, "no_project", True), ("new math ci-contract", 1, "exists", True),
        ("nope", 2, "usage", True), ("statu", 2, "usage", True),
        ("cancel", 2, "usage", False), ("cancel nope", 2, "no_project", True), (f"cancel {p} 7-7", 2, "not_found", True),
        ("timeline nope --resolved", 2, "no_project", False), (f"timeline {plain} --resolved", 2, "no_project", False), (f"timeline {p} xx! --resolved", 2, "usage", False),
        ("history", 2, "usage", False), ("history save", 2, "usage", True), ("history save nope", 2, "no_project", True), (f"history restore {p}", 2, "usage", True), (f"history restore {p} BRIEF.md --at s99", 1, "not_found", True),
        ("peaks", 2, "usage", False), ("peaks nope", 2, "no_project", True), (f"peaks {t}/projects/e", 2, "not_found", True), (f"peaks {p} --bins 0", 2, "usage", True),
    ]


NO_COLOUR = "\033[31m✗\033[0m "


def error_problems(sch, r, want, code):
    """What is wrong with a failure's JSON; [] when it is right."""
    try:
        d = json.loads(r.stdout)
    except ValueError:
        return [f"stdout is not JSON: {r.stdout[:120]!r}"]
    bad = schemalite.problems(sch, d)
    if r.returncode != want:
        bad.append(f"exit {r.returncode}, not {want}")
    if d.get("error", {}).get("code") != code:
        bad.append(f"code {d.get('error', {}).get('code')}, not {code}")
    if not r.stderr.strip():
        bad.append("nothing on stderr")
    return bad


def main(argv):
    if len(argv) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    sh = argv[0]

    def report(bad, good):
        print(("bad\t" + good + ": " + " · ".join(str(b).replace("\n", " ")[:300] for b in bad[:8]) + (f" … and {len(bad) - 8} more" if len(bad) > 8 else "")) if bad else ("ok\t" + good), flush=True)
    t = str(Path(tempfile.mkdtemp(prefix="vh-contract.")).resolve())
    try:
        vh, p, z, e, has_film = fixture(t, sh)
        out, bad = outputs(vh, p, z, e, has_film)
        schemas = {}
        for name in ALL:
            f = SCHEMAS / f"{name}.schema.json"
            try:
                schemas[name] = schemalite.load(f)
            except (OSError, ValueError) as x:
                bad.append(f"{f.name}: {x}")
                continue
            odd = schemalite.keywords(schemas[name])
            if odd:
                bad.append(f"{f.name}: keywords tools/schemalite.py does not read: {sorted(odd)}")
        extra = sorted({f.name[:-len(".schema.json")] for f in SCHEMAS.glob("*.schema.json")} - set(ALL))
        bad += [f"{x}.schema.json: no command here holds an output to it" for x in extra]
        n = 0
        for name, docs in out.items():
            sch = schemas.get(name)
            for said, doc in docs:
                n += 1
                if sch is None:
                    continue
                bad += [f"{said}: {x}" for x in schemalite.problems(sch, doc)[:6]]
                bad += [f"{said}: {x}: a field {name}.schema.json does not name: write it in, so its loss fails here" for x in schemalite.undeclared(sch, doc)[:6]]
        report(bad, f"output contracts: {n} outputs of {len(out)} commands fit tools/schemas/output/, and each field they have is written down there")
        # the schemas have teeth: every field a schema requires, taken out of a real output in turn, is noticed
        bad, n = [], 0
        for name, docs in out.items():
            sch = schemas.get(name)
            if sch is None:
                continue
            doc = docs[0][1]
            needed = set(sch.get("required", [])) | {k for one in sch.get("anyOf", []) for k in one.get("required", [])} - {"error"}
            for k in list(doc):
                if k in needed:
                    n += 1
                    if not schemalite.problems(sch, {x: v for x, v in doc.items() if x != k}):
                        bad.append(f"{name}: without {k} it still fits")
            if not needed - {"version", "v"}:
                bad.append(f"{name}: its schema requires nothing but the version")
        report(bad, f"output contracts: a field removed from an output fails ({n} top-level fields taken out, each noticed)")
        # every failure, with and without --json
        sch = schemas.get("error", True)
        bad, n = [], 0
        for args, want, code, same in failures(t, p):
            n += 1
            a = args.split()
            r = vh(*a, "--json")
            wrong = error_problems(sch, r, want, code)
            if wrong:
                bad.append(f"{args} --json: {'; '.join(wrong)}")
                continue
            msg = json.loads(r.stdout)["error"]["message"]
            if "\033" in msg or msg not in r.stderr.replace(NO_COLOUR, ""):
                bad.append(f"{args} --json: the message is not the line a person reads: {msg[:120]!r} / {r.stderr[-160:]!r}")
            q = vh(*a)
            if q.returncode != want or not q.stderr.strip() or (same and msg not in q.stderr.replace(NO_COLOUR, "")) or (('"error"' in q.stdout) != (a[:2] == ["desk", "data"])):
                bad.append(f"{args}: exit {q.returncode} (want {want}), stdout {q.stdout[:120]!r}, stderr {q.stderr[-160:]!r}")
        # a skeleton: --init says where, once, and then it exists; its placeholders refuse the page
        n += 3
        r = vh("gate", p, "2", "--init", "--json")
        d = json.loads(r.stdout) if r.returncode == 0 else {}
        if not (d.get("init") is True and d.get("gate") == "2" and d.get("path", "").endswith("out/review/gate-2.json")):
            bad.append(f"gate --init --json: exit {r.returncode}, {r.stdout[:200]!r}")
        for args, want, code in ((("gate", p, "2", "--init", "--json"), 2, "exists"), (("gate", p, "2", "--json"), 2, "invalid")):
            wrong = error_problems(sch, vh(*args), want, code)
            bad += [f"{' '.join(args[2:])}: {'; '.join(wrong)}"] if wrong else []
        # no python3: said the same way, by bin/vh itself; bin/vh doctor --json keeps its own record
        bare = f"{t}/bare"
        os.makedirs(bare)
        for d in os.environ["PATH"].split(os.pathsep):
            if os.path.isdir(d):
                for x in os.listdir(d):
                    if not x.startswith("python") and not os.path.lexists(os.path.join(bare, x)):
                        os.symlink(os.path.join(d, x), os.path.join(bare, x))
        real = shutil.which(sh) or sh
        nopy = VH(real, {"PATH": bare})
        n += 2
        r = nopy("status", p, "--json")
        wrong = error_problems(sch, r, 127, "missing_tool") + ([] if "python3" in r.stderr else ["no word of python3"])
        bad += [f"status --json without python3: {'; '.join(wrong)}"] if wrong else []
        r = nopy("doctor", "--json")
        if r.returncode != 0 or not isinstance(json.loads(r.stdout or "{}").get("modules"), list):
            bad.append(f"doctor --json without python3: exit {r.returncode}, {r.stdout[:200]!r}")
        report(bad, f"errors a program can read: {n} failures of the commands a client reads, each --json valid JSON in the one shape on stdout with the right code and exit status, the same exit and words without --json; before Python starts too, and with no python3")
    finally:
        shutil.rmtree(t, ignore_errors=True)
    print("end\t", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
