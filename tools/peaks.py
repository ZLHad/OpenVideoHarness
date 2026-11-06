"""bin/vh peaks: a waveform a client can draw, as min and max per bin. ffmpeg and the standard library.

usage: bin/vh peaks <audio | film | project> [--bins 1000] [--json]
A project means its current film, the one bin/vh status --json has as media.film. The sound is decoded at 48 kHz with every channel kept, and read
in chunks: a bin's min and max are across the channels, so one channel alone or two in opposite phase read as they are, and two hours take half a minute
and some 130 MB, as little as ten minutes do. What it can miss: a peak between two samples (an inter-sample peak: the true peak of bin/vh check's loudness can be higher), and what lies
above 24 kHz. The record goes beside the proxies (<project>/out/proxy/<name>.peaks.json; outside a project: proxy/
beside the file; another --bins: <name>.peaks-<N>.json), named as bin/vh proxy names its files, with the source's size and
modification time: while they are the same, and the record is one this tool writes, a repeat reads the record and starts no ffmpeg. A folder that
takes no file: the record is still printed, and it says so on stderr.
JSON (--json prints the record, one line, and state: made or "up to date"): {"version": 1, "tool", "source", "source_ident":
{"size", "mtime"}, "asked", "bins", "rate", "channels", "samples" (per channel), "duration", "peaks": [[min, max], …] in -1…1 (4 decimals), "t", "at"}. bins is less
than asked when there are fewer samples than that.
Exit: 0 · 1 ffmpeg failed, or it has no sound · 2 usage, no such file or project, or a project with no film.
"""
import array, json, os, re, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import activity, jsonerr, proxy as P, versions as V   # noqa: E402,E401

RATE = 48000
DEFAULT_BINS = 1000
MAX_BINS = 200000
CHUNK = 1 << 20          # bytes read from ffmpeg at a time
MAX_BLOCKS = 1 << 21     # blocks of samples whose min and max are kept: the memory it takes, whatever the length


def record_path(f, project, bins):
    d = P.out_dir(f, project, None)
    return d / f"{P.name_of(f, project)}.peaks{'' if bins == DEFAULT_BINS else f'-{bins}'}.json"


def blocks(read, cap=MAX_BLOCKS):
    """(each block's min, each block's max, samples in all) of the 16-bit samples read(n) gives, all channels as one stream. A block starts as one sample and
    doubles when there would be more than cap of them (cap even), so a long film takes what a few minutes take."""
    mins, maxs, rest = array.array("h"), array.array("h"), array.array("h")
    step, total = 1, 0
    while True:
        raw = read(CHUNK)
        if not raw:
            break
        a = array.array("h")
        a.frombytes(raw[:len(raw) & ~1])
        if sys.byteorder == "big":
            a.byteswap()
        total += len(a)
        if rest:
            rest.extend(a)
            a = rest
        i = 0
        while i + step <= len(a):
            if len(mins) == cap:
                mins = array.array("h", map(min, mins[::2], mins[1::2]))
                maxs = array.array("h", map(max, maxs[::2], maxs[1::2]))
                step *= 2
            elif step == 1:
                part = a[i:i + cap - len(mins)]
                mins.extend(part)
                maxs.extend(part)
                i += len(part)
            else:
                seg = a[i:i + step]
                mins.append(min(seg))
                maxs.append(max(seg))
                i += step
        rest = a[i:]
    if rest:
        mins.append(min(rest))
        maxs.append(max(rest))
    return mins, maxs, total


def decode(f):
    """(blocks' mins, maxs, samples per channel, channels) of the first sound. RuntimeError when ffmpeg cannot; LookupError when there is no sound."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "csv=p=0", str(f)], capture_output=True, text=True, errors="replace")
    if r.returncode:
        raise RuntimeError(f"ffprobe could not read {f}: {r.stderr.strip()[-300:]}")
    m = re.match(r"\d+", r.stdout.strip())
    if not m:
        raise LookupError(f"{f} has no sound")
    channels = int(m.group(0)) or 1
    with tempfile.TemporaryFile() as err:
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-nostdin", "-i", str(f), "-map", "0:a:0", "-ar", str(RATE), "-f", "s16le", "-"], stdout=subprocess.PIPE, stderr=err)
        try:
            mins, maxs, total = blocks(p.stdout.read)
            p.wait()
        except BaseException:   # a Ctrl-C: ffmpeg goes too
            p.kill()
            p.wait()
            raise
        finally:
            p.stdout.close()
        if p.returncode:
            err.seek(0)
            words = err.read().decode("utf-8", "replace").strip()
            if "matches no streams" in words or "does not contain any stream" in words:
                raise LookupError(f"{f} has no sound")
            raise RuntimeError(f"ffmpeg could not read {f}: {words[-300:]}")
    return mins, maxs, total // channels, channels


def bins_of(mins, maxs, bins):
    """[[min, max], …] of the blocks in each of the bins, in -1…1."""
    n = len(mins)
    bins = min(bins, n)
    out = []
    for i in range(bins):
        a, b = i * n // bins, (i + 1) * n // bins
        out.append([round(min(mins[a:b]) / 32768, 4), round(max(maxs[a:b]) / 32768, 4)])
    return out


def holds(old, now, bins):
    """Is a record there this one: of this source and this count, at this rate, and of the shape this tool writes?"""
    if not (isinstance(old, dict) and old.get("version") == 1 and old.get("source_ident") == now and old.get("asked") == bins and old.get("rate") == RATE and isinstance(old.get("channels"), int)):
        return False
    if not all(k in old for k in ("source", "samples", "duration")):
        return False
    peaks = old.get("peaks")
    return isinstance(peaks, list) and len(peaks) == old.get("bins") and all(isinstance(x, list) and len(x) == 2 and all(isinstance(v, (int, float)) for v in x) for x in peaks)


def make(f, project, bins):
    """The record (made anew, or the one there while its source is the same) → (record, state, its path, is it kept there)."""
    path = record_path(f, project, bins)
    now = P.ident(f)
    old = V.load_json(path) if path.is_file() else None
    if holds(old, now, bins):
        return old, "up to date", path, True
    mins, maxs, samples, channels = decode(f)
    if not mins:
        raise LookupError(f"{f} has no sound")
    peaks = bins_of(mins, maxs, bins)
    rec = {"version": 1, "tool": "bin/vh peaks", "source": P.rel(project, f), "source_ident": now, "asked": bins, "bins": len(peaks), "rate": RATE, "channels": channels, "samples": samples,
           "duration": round(samples / RATE, 3), "peaks": peaks, "t": round(time.time(), 3), "at": V.iso(time.time())}
    tmp = path.with_name(f".{path.name}.{os.getpid()}")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
        os.replace(tmp, path)
    except OSError as e:   # a read-only folder: the waveform is made all the same
        print(f"peaks: the record could not be kept at {path} ({e.strerror or e}); it is made again next time", file=sys.stderr)
        return rec, "made", path, False
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
    return rec, "made", path, True


def target(word):
    """(the file, its project or None)."""
    p = Path(word).expanduser()
    if p.is_file():
        return p.resolve(), V.project_of(p)
    project = V.project_of(p) if p.exists() else None
    if project is None:
        import review
        project = review.find_project(word)
        if project is None:
            raise P.Usage(f"no audio, film or project at {word}", "no_project")
    film = P.current_film(project)[0]
    if film is None:
        raise P.Usage(f"no film in {project} to read the sound of: bin/vh render first, or name the audio file", "not_found")
    return film, Path(project)


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
        rec, state, path, kept = make(f, project, a.bins)
    except P.Usage as e:
        return jsonerr.fail(e.code, f"peaks: {e}")
    except FileNotFoundError:
        return jsonerr.fail("missing_tool", "peaks: ffmpeg is not installed", "bin/vh doctor says how to get it", rc=1)
    except LookupError as e:
        return jsonerr.fail("not_found", f"peaks: {e}", rc=1)
    except (RuntimeError, OSError) as e:
        return jsonerr.fail("failed", f"peaks: {e}", rc=1)
    if state != "up to date":
        activity.note(f"{rec['source']}: {rec['bins']} bins, {rec['duration']} s", [path] if kept else [])
    if a.json:
        print(json.dumps(dict(rec, state=state), ensure_ascii=False, separators=(",", ":")))
    else:
        print(f"peaks: {P.rel(project, path)}{'' if kept else ' (not kept)'} · {rec['bins']} bins of {rec['duration']} s · {state}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:
        sys.exit(0)
