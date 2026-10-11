"""Move the seconds in a file from one narration timeline to another (bin/vh remap).

usage: python3 tools/audio/remap.py --from old.timeline.json --to new.timeline.json <file.json>
         [--keys t,start,end,at,time] [--out new.json] [--skip-lint]

When the narration changes (a line rewritten, pauses put in, the pace changed), seconds written into a sound script, an
events list or a score's section table still point at the old take. remap pairs the two timelines: for every line
whose id is in both, each word's start and end when the words are the same, else the line's start and end. A time is
moved through those pairs, linearly between two of them, and shifted with the nearest one before the first or after
the last. Only numbers under the keys given (anywhere in the JSON, also lists of numbers under them) change; the rest
is written back as it was. Times picture and sound take from words (cues such as "@l4:风") need no remap: this is for
the seconds someone typed.

Writes --out, else the file itself with the original kept as <file>.bak, and prints how far the times moved. Both
timelines must pass bin/vh timeline (--skip-lint to go on anyway). Exit: 0 written · 1 a timeline fails its checks, or
no line is in both · 2 a file is missing or not JSON.
"""
import argparse, bisect, json, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline_lint  # noqa: E402

def anchors(old, new):
    """[(old seconds, new seconds)], increasing in both"""
    by_id = {s.get("id"): s for s in new.get("segments") or [] if s.get("id")}
    pairs = []
    for s in old.get("segments") or []:
        n = by_id.get(s.get("id"))
        if not n:
            continue
        ow, nw = s.get("words") or [], n.get("words") or []
        if ow and len(ow) == len(nw) and all(a.get("w") == b.get("w") for a, b in zip(ow, nw)):
            for a, b in zip(ow, nw):
                pairs += [(a["start"], b["start"]), (a["end"], b["end"])]
        else:                                     # the line was rewritten: only its ends correspond
            pairs += [(s["start"], n["start"]), (s["end"], n["end"])]
    pairs.sort()
    out = []
    for a, b in pairs:                            # keep the pairs that run forward in both (a word time that slipped is left out)
        if out and (a <= out[-1][0] + 1e-9 or b < out[-1][1] - 1e-9):
            continue
        out.append((a, b))
    return out

def mapper(pairs):
    xs = [a for a, _ in pairs]
    def f(t):
        i = bisect.bisect_right(xs, t)
        if i == 0:
            return t + pairs[0][1] - pairs[0][0]
        if i == len(pairs):
            return t + pairs[-1][1] - pairs[-1][0]
        (a0, b0), (a1, b1) = pairs[i - 1], pairs[i]
        return b0 + (b1 - b0) * (t - a0) / (a1 - a0)
    return f

def walk(x, keys, f, moved, under=False):
    if isinstance(x, dict):
        return {k: walk(v, keys, f, moved, k in keys) for k, v in x.items()}
    if isinstance(x, list):
        return [walk(v, keys, f, moved, under) for v in x]
    if under and isinstance(x, (int, float)) and not isinstance(x, bool):
        y = round(f(x), 3); moved.append((x, y)); return y
    return x

def main():
    ap = argparse.ArgumentParser(prog="bin/vh remap", description=__doc__.split("\n\n")[0])
    ap.add_argument("file"); ap.add_argument("--from", dest="old", required=True); ap.add_argument("--to", dest="new", required=True)
    ap.add_argument("--keys", default="t,start,end,at,time", help="the keys whose numbers are seconds (default t,start,end,at,time)")
    ap.add_argument("--out"); ap.add_argument("--skip-lint", action="store_true")
    a = ap.parse_args()
    try:
        old, new, data = (json.loads(Path(p).read_text(encoding="utf-8")) for p in (a.old, a.new, a.file))
    except (OSError, ValueError) as e:
        print(f"remap: {e}", file=sys.stderr); sys.exit(2)
    for name, tl in (("--from", old), ("--to", new)):
        if (lint := timeline_lint.lint(tl, tl.get("lang"))) and not a.skip_lint:
            print(f"remap: the {name} timeline has {len(lint)} problem(s):\n{timeline_lint.report(lint)}\n(--skip-lint to go on anyway)", file=sys.stderr)
            sys.exit(1)
    pairs = anchors(old, new)
    if len(pairs) < 2:
        print("remap: the two timelines share no line (by id): nothing to map through", file=sys.stderr); sys.exit(1)
    moved = []
    out = walk(data, {k.strip() for k in a.keys.split(",") if k.strip()}, mapper(pairs), moved)
    dest = Path(a.out or a.file)
    if not a.out:
        shutil.copyfile(a.file, a.file + ".bak")
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    shifts = [b - x for x, b in moved]
    print(f"remap: {len(moved)} time(s) in {a.file} through {len(pairs)} anchor pairs → {dest}" + ("" if a.out else f" (the original: {a.file}.bak)"))
    if shifts:
        big = max(range(len(moved)), key=lambda i: abs(shifts[i]))
        print(f"  moved by {min(shifts):+.3f} to {max(shifts):+.3f} s; the most: {moved[big][0]} → {moved[big][1]} s")

if __name__ == "__main__":
    main()
