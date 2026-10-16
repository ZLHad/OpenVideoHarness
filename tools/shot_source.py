"""Shared shot selection for storyboard and rhythm; live registries stay in memory."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import vhdraw as V


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
    """Explicit JSON/page > hand-written shots.json > live film.html; return shots, meta, path, live page."""
    if explicit:
        source = Path(explicit)
        if not source.is_absolute() and not source.exists():
            source = project / source
    elif (project / "shots.json").exists():
        source = project / "shots.json"
    elif (project / "film.html").exists():
        source = project / "film.html"
    elif not required:
        return [], {}, None, None
    else:
        raise SystemExit(f"shots: no shots.json or film.html in {project}; write a shot table:\n{V.SHOTS_SCHEMA}")
    if not source.is_file():
        raise SystemExit(f"shots: no such file: {source}")
    source = source.resolve()
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
