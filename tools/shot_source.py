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
    try:
        result = subprocess.run(cmd, input=json.dumps(capture) if capture is not None else None,
                                capture_output=True, text=True, timeout=150)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise SystemExit(f"shots: cannot read {page}: {e}") from e
    if result.returncode:
        raise SystemExit((result.stderr or result.stdout).strip() or f"shots: page reader exited {result.returncode}")
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    try:
        return json.loads(result.stdout)
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
    """Capture [(id, filename, seconds)] privately; publish only after the page and every frame pass."""
    with tempfile.TemporaryDirectory(prefix="vh-shot-frames-") as tmp:
        data = live_page(page, browser, {"out": tmp, "frames": [{"name": name, "t": t} for _, name, t in want]})
        frames = {}
        for sid, name, _ in want:
            target = dst / name
            target.write_bytes((Path(tmp) / name).read_bytes())
            frames[sid] = target
    return frames, data["width"] / data["height"]
