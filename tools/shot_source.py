"""The project's shot table, for every tool that reads one (storyboard, rhythm, the review desk, thumbs, looks); live
registries stay in memory. tools/film/shot_source.mjs is its mirror for the page tools (bin/vh patch --shot): the two
find the table the same way, so where it lives is said in one place each."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import vhdraw as V


TWO = ("shots: two shot tables in {p}, edit.json and shots.json: a project keeps one. An edit list's entries are its shots "
       "(bin/vh edit init folds a shots.json into a new one); fold the shots in by hand, then rename or delete shots.json")


def table(project):
    """The project's shot table: <project>/edit.json (an edit list, engines/EDIT.md: its entries are the shots), or
    <project>/shots.json, or None when there is none. Both there: SystemExit (a project keeps one)."""
    e, s = Path(project) / "edit.json", Path(project) / "shots.json"
    if e.is_file() and s.is_file():
        raise SystemExit(TWO.format(p=project))
    return e if e.is_file() else s if s.is_file() else None


def is_edit(path):
    return Path(path).name == "edit.json"


def edit_rows(project):
    """An edit list's entries as shot rows (film seconds; every field kept, with "kind": what draws it) and its meta;
    SystemExit with tools/edit.py's problems when it does not resolve. Reads, never writes (no browser either)."""
    import edit
    try:
        doc = edit.resolve(project)
    except edit.EditError as e:
        raise SystemExit("shots: edit.json does not resolve:\n  " + "\n  ".join(e.problems[:12]) +
                         (f"\n  … and {len(e.problems) - 12} more" if len(e.problems) > 12 else "")) from None
    return edit.shot_rows(doc), ({"video": doc["video"]} if doc.get("video") else {}), doc


def rows(project):
    """(the table's rows as written, its meta, its path), ([], {}, None) when there is none: shots.json's list, or an
    edit list's entries with their resolved start and end. For readers that keep every field (the review desk, looks).
    ValueError when shots.json is not JSON; SystemExit when edit.json does not resolve."""
    p = table(project)
    if p is None:
        return [], {}, None
    if is_edit(p):
        r, meta, _ = edit_rows(project)
        return r, meta, p
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    raw = d.get("shots") if isinstance(d, dict) else d
    return (raw if isinstance(raw, list) else None), (d if isinstance(d, dict) else {}), p


def edit_shots(project):
    """An edit list's entries parsed as shots (vhdraw.parse_shots), each with its "kind"; and its meta."""
    r, meta, _ = edit_rows(project)
    shots, _ = V.parse_shots(r, Path(project) / "edit.json")
    kinds = {x["id"]: x.get("kind") for x in r}
    for s in shots:
        s["kind"] = kinds.get(s["id"])
    return shots, meta


def parsed(project):
    """(shots as vhdraw.parse_shots gives them, the table's path), or ([], None): the project's table without a
    browser (thumbs). An edit list's shots carry their "kind"."""
    p = table(project)
    if p is None:
        return [], None
    if not is_edit(p):
        return V.load_shots(p)[0], p
    return edit_shots(project)[0], p


def live_page(page, browser, capture=None):
    if not browser:
        raise SystemExit("shots: a live page needs headless Chrome; run bin/vh storyboard/rhythm or set CHROME_PATH")
    cmd = ["node", str(Path(__file__).parent / "film" / "shots.mjs"), str(page), "--browser", browser]
    if capture is not None:
        cmd.append("--capture")
    # past the reader's own watchdogs (120 s to ready, 60 s a frame), only as a backstop
    limit = 150 + 70 * len(capture["frames"] if capture else [])
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE if capture is not None else subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except OSError as e:
        raise SystemExit(f"shots: cannot read {page}: {e}") from e
    try:
        out, err = proc.communicate(json.dumps(capture) if capture is not None else None, timeout=limit)
    except (KeyboardInterrupt, subprocess.TimeoutExpired) as e:
        # Ctrl-C reached node too, and a timeout sends it SIGTERM: either way let it close Chrome and remove its
        # profile (subprocess.run would kill it after 0.25 s and leave the profile behind)
        if isinstance(e, subprocess.TimeoutExpired):
            proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        if isinstance(e, KeyboardInterrupt):
            raise
        raise SystemExit(f"shots: stopped reading {page} after {limit} s") from e
    if proc.returncode:
        raise SystemExit((err or out).strip() or f"shots: page reader exited {proc.returncode}")
    if err:
        print(err.strip(), file=sys.stderr)
    try:
        return json.loads(out)
    except ValueError as e:
        raise SystemExit(f"shots: page reader did not return JSON for {page}") from e


def load(project, explicit=None, browser=None, required=True):
    """Explicit JSON/page > the project's table (edit.json's entries, or a hand-written shots.json) > live film.html;
    return shots, meta, path, live page. An edit list's shots carry "kind" (page, image, color, slate)."""
    if explicit:
        source = Path(explicit)
        if not source.is_absolute() and not source.exists():
            source = project / source
    elif table(project):
        source = table(project)
    elif (project / "film.html").exists():
        source = project / "film.html"
    elif not required:
        return [], {}, None, None
    else:
        raise SystemExit(f"shots: no shot table (edit.json or shots.json) or film.html in {project}; write a shot table:\n{V.SHOTS_SCHEMA}")
    if not source.is_file():
        raise SystemExit(f"shots: no such file: {source}")
    source = source.resolve()
    if is_edit(source):
        shots, meta = edit_shots(source.parent)
        return shots, meta, source, None
    if source.suffix.lower() not in (".html", ".htm"):
        shots, meta = V.load_shots(source)
        return shots, meta, source, None
    if not browser and not required and not explicit:
        # an optional lane read from the page by default (rhythm), on a machine without Chrome: draw the rest.
        # A page that fails ready or gives a malformed table still stops the run.
        print(f"! no headless Chrome to read {source.name}'s shots; the shots lane is left out (set CHROME_PATH)", file=sys.stderr)
        return [], {}, None, None
    data = live_page(source, browser)
    if data["shots"] is None:
        if not required and not explicit:
            return [], {}, None, None
        raise SystemExit(f"shots: {source} gives no window.film.shots; update the copied engine or supply --shots shots.json")
    shots, meta = V.parse_shots(data["shots"], source)
    return shots, meta, source, source


def label(source, page, project):
    return V.relpath(source, project) + (" (window.film.shots)" if page else "")


def capture(page, browser, want, dst):
    """Capture [(id, filename, seconds)] privately; publish only after the page and every frame pass.
    Returns the frames, the aspect, the ids past the page's end (not drawn) and the page's duration."""
    with tempfile.TemporaryDirectory(prefix="vh-shot-frames-") as tmp:
        data = live_page(page, browser, {"out": tmp, "frames": [{"name": name, "t": t} for _, name, t in want]})
        late = set(data.get("late") or [])
        frames = {}
        for sid, name, _ in want:
            if name in late:
                continue
            target = dst / name
            target.write_bytes((Path(tmp) / name).read_bytes())
            frames[sid] = target
    return frames, data["width"] / data["height"], [sid for sid, name, _ in want if name in late], data["duration"]
