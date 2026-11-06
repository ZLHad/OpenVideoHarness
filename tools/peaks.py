"""bin/vh peaks: a waveform a client can draw, as min and max per bin. ffmpeg and the standard library.

usage: bin/vh peaks <audio | film | project> [--bins 1000] [--json]
A project means its current film (tools/proxy.py). The sound is decoded to mono at 8 kHz, so a two-hour film takes seconds and
some 100 MB while it runs. The record goes beside the proxies (<project>/out/proxy/<name>.peaks.json; outside a project: proxy/
beside the file; another --bins: <name>.peaks-<N>.json), named as bin/vh proxy names its files, with the source's size and
modification time: while they are the same a repeat reads the record and starts no ffmpeg.
JSON (--json prints the record, one line, and state: made or "up to date"): {"version": 1, "tool", "source", "source_ident":
{"size", "mtime"}, "bins", "rate", "samples", "duration", "peaks": [[min, max], …] in -1…1 (4 decimals), "t", "at"}. bins is less
than was asked for when there are fewer samples than that.
Exit: 0 · 1 ffmpeg failed, or it has no sound · 2 usage, no such file or project, or a project with no film.
"""
import array, json, os, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import activity, jsonerr, proxy as P, versions as V   # noqa: E402,E401

RATE = 8000
DEFAULT_BINS = 1000
MAX_BINS = 200000


def record_path(f, project, bins):
    d = P.out_dir(f, project, None)
    return d / f"{P.name_of(f, project)}.peaks{'' if bins == DEFAULT_BINS else f'-{bins}'}.json"


def decode(f):
    """The sound as an array of 16-bit samples at RATE, mono. RuntimeError when ffmpeg cannot; LookupError when there is no sound."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(f), "-map", "0:a:0", "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"], capture_output=True)
    if r.returncode:
        err = r.stderr.decode("utf-8", "replace").strip()
        if "matches no streams" in err or "does not contain any stream" in err:
            raise LookupError(f"{f} has no sound")
        raise RuntimeError(f"ffmpeg could not read {f}: {err[-300:]}")
    a = array.array("h")
    a.frombytes(r.stdout[:len(r.stdout) & ~1])
    if sys.byteorder == "big":
        a.byteswap()
    return a


def bins_of(a, bins):
    """[[min, max], …] of the samples in each of the bins, in -1…1."""
    n = len(a)
    bins = min(bins, n)
    out = []
    for i in range(bins):
        seg = a[i * n // bins:(i + 1) * n // bins]
        out.append([round(min(seg) / 32768, 4), round(max(seg) / 32768, 4)])
    return out


def make(f, project, bins):
    """The record (made anew, or the one there while its source is the same) → (record, state, its path)."""
    path = record_path(f, project, bins)
    now = P.ident(f)
    old = V.load_json(path) if path.is_file() else None
    if old and old.get("source_ident") == now and old.get("asked") == bins and isinstance(old.get("peaks"), list):
        return old, "up to date", path
    a = decode(f)
    if not a:
        raise LookupError(f"{f} has no sound")
    peaks = bins_of(a, bins)
    rec = {"version": 1, "tool": "bin/vh peaks", "source": P.rel(project, f), "source_ident": now, "asked": bins, "bins": len(peaks), "rate": RATE, "samples": len(a),
           "duration": round(len(a) / RATE, 3), "peaks": peaks, "t": round(time.time(), 3), "at": V.iso(time.time())}
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}")
    tmp.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return rec, "made", path


def target(word):
    """(the file, its project or None)."""
    p = Path(word).expanduser()
    if p.is_file():
        return p.resolve(), V.project_of(p)
    film, project, _ = P.pick(word)
    if film is None:
        raise P.Usage(f"no film in {project} to read the sound of: bin/vh render first, or name the audio file", "not_found")
    return film, project


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="bin/vh peaks", description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split("\n\n", 1)[1])
    ap.add_argument("target", help="an audio file, a film, or a project (its current film)")
    ap.add_argument("--bins", type=int, default=DEFAULT_BINS, help=f"how many (default {DEFAULT_BINS})")
    ap.add_argument("--json", action="store_true", help="the record, on one line (version 1)")
    a = ap.parse_args(argv)
    if not 1 <= a.bins <= MAX_BINS:
        return jsonerr.fail("usage", f"peaks: --bins {a.bins}: 1 to {MAX_BINS}")
    try:
        f, project = target(a.target)
        rec, state, path = make(f, project, a.bins)
    except P.Usage as e:
        return jsonerr.fail(e.code, f"peaks: {e}")
    except FileNotFoundError:
        return jsonerr.fail("missing_tool", "peaks: ffmpeg is not installed", "bin/vh doctor says how to get it", rc=1)
    except LookupError as e:
        return jsonerr.fail("not_found", f"peaks: {e}", rc=1)
    except (RuntimeError, OSError) as e:
        return jsonerr.fail("failed", f"peaks: {e}", rc=1)
    if state != "up to date":
        activity.note(f"{rec['source']}: {rec['bins']} bins, {rec['duration']} s", [path])
    if a.json:
        print(json.dumps(dict(rec, state=state), ensure_ascii=False, separators=(",", ":")))
    else:
        print(f"peaks: {P.rel(project, path)} · {rec['bins']} bins of {rec['duration']} s · {state}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:
        sys.exit(0)
