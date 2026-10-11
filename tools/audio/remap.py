"""Move the seconds in a file from one narration timeline to another (bin/vh remap).

usage: python3 tools/audio/remap.py --from old.timeline.json --to new.timeline.json <file.json>
         [--keys t,start,end,at,time] [--out new.json] [--skip-lint]

When the narration changes (a line rewritten, pauses put in, the pace changed), seconds written by hand into a sound
script or an events list (bin/vh sfx's events.json: its "t") still point at the old take. remap pairs the two
timelines: for every line whose id is in both, each word's start and end when the words are the same, else the line's
start and end. A time is moved through those pairs, linearly between two of them, and shifted with the nearest one
before the first or after the last; where two lines met and the new take puts a pause between them, a time on the
later line moves with it. Only numbers under the keys given (anywhere in the JSON, also lists of numbers under them)
change: durations ("dur") and the rest keep their values, and a whole number of seconds that does not move stays one.
Times picture and sound take from words (cues such as "@l4:风") need no remap: this is for the seconds someone typed.

It says which lines it could only pair by their ends (rewritten), which are gone from the new take or new in it, and
which run in another order there (their pairs are left out, so times on them follow their neighbours): each time that
falls on such a line is listed, to check by ear. A time that would move before 0 s becomes 0 s, and is listed too.

Writes --out, else the file itself with the original kept as <file>.bak (it refuses when a .bak is already there: an
earlier remap's original). The file is written with its indent width (none, or the spaces of its first nested line),
one value a line: a hand-aligned layout comes back as plain JSON. Both
timelines must pass bin/vh timeline (--skip-lint to go on anyway). Exit: 0 written · 1 a timeline fails its checks, or
no pair to map through · 2 a file is missing, not JSON or not a timeline, or the .bak is taken.
"""
import argparse, bisect, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import timeline_lint  # noqa: E402

num = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)
timed = lambda s: num(s.get("start")) and num(s.get("end"))

def anchors(old, new):
    """[(old seconds, new seconds)], forward in both, and what became of each old line: {id: words | same | ends | gone
    | order} (same: its text did not change, but there are no word times to pair; ends: it was rewritten; order: its
    pairs ran backwards in the new take and were left out), with the ids new in the new take"""
    by_id = {s.get("id"): s for s in new["segments"] if isinstance(s, dict) and s.get("id") and timed(s)}
    olds = [s for s in old["segments"] if isinstance(s, dict) and s.get("id") and timed(s)]
    pairs, how = [], {}
    for s in olds:
        n = by_id.get(s["id"])
        if not n:
            how[s["id"]] = "gone"; continue
        ow, nw = s.get("words") or [], n.get("words") or []
        if ow and len(ow) == len(nw) and all(isinstance(a, dict) and isinstance(b, dict) and a.get("w") == b.get("w") and
                                             all(num(x.get(k)) for x in (a, b) for k in ("start", "end")) for a, b in zip(ow, nw)):
            how[s["id"]] = "words"
            for a, b in zip(ow, nw):
                pairs += [(a["start"], b["start"], s["id"]), (a["end"], b["end"], s["id"])]
        else:                                     # only its ends correspond: no word times, or the line was rewritten
            said = lambda x: timeline_lint._plain(timeline_lint._text(x, old.get("lang")))
            how[s["id"]] = "same" if said(s) == said(n) else "ends"
            pairs += [(s["start"], n["start"], s["id"]), (s["end"], n["end"], s["id"])]
    pairs.sort()
    out, kept = [], {}
    for a, b, sid in pairs:                       # new times must not run backwards; one old time may step forward (two
        if out and b < out[-1][1] - 1e-9:         # lines that met, a pause put between them), so equal old times stay
            continue
        out.append((a, b)); kept[sid] = True
    for sid in {sid for _, _, sid in pairs} - set(kept):   # every pair of it left out: it moved past its neighbours
        how[sid] = "order"
    known = {s.get("id") for s in old["segments"] if isinstance(s, dict)}
    fresh = [s.get("id") for s in new["segments"] if isinstance(s, dict) and s.get("id") and s.get("id") not in known]
    return out, how, fresh, len(pairs) - len(out)

def mapper(pairs):
    xs = [a for a, _ in pairs]
    def f(t):
        i = bisect.bisect_right(xs, t)
        if i == 0:
            return t + pairs[0][1] - pairs[0][0]
        if i == len(pairs):
            return t + pairs[-1][1] - pairs[-1][0]
        (a0, b0), (a1, b1) = pairs[i - 1], pairs[i]   # a0 <= t < a1
        return b0 + (b1 - b0) * (t - a0) / (a1 - a0)
    return f

def walk(x, keys, f, moved, under=False):
    if isinstance(x, dict):
        return {k: walk(v, keys, f, moved, k in keys) for k, v in x.items()}
    if isinstance(x, list):
        return [walk(v, keys, f, moved, under) for v in x]
    if under and num(x):
        y = max(0.0, round(f(x), 3))
        if isinstance(x, int) and y == int(y):
            y = int(y)
        moved.append((x, y, f(x) < 0)); return y
    return x

def fail(msg, code):
    print(f"remap: {msg}", file=sys.stderr); sys.exit(code)

def main():
    ap = argparse.ArgumentParser(prog="bin/vh remap", description=__doc__.split("\n\n")[0])
    ap.add_argument("file"); ap.add_argument("--from", dest="old", required=True); ap.add_argument("--to", dest="new", required=True)
    ap.add_argument("--keys", default="t,start,end,at,time", help="the keys whose numbers are seconds (default t,start,end,at,time)")
    ap.add_argument("--out"); ap.add_argument("--skip-lint", action="store_true")
    a = ap.parse_args()
    tls = {}
    for name, f in (("--from", a.old), ("--to", a.new)):
        tl, why = timeline_lint.load(f)
        if why:
            fail(f"{name} {f}: {why}", 2)
        tls[name] = tl
    old, new = tls["--from"], tls["--to"]
    try:
        text = Path(a.file).read_text(encoding="utf-8"); data = json.loads(text)
    except (OSError, ValueError) as e:
        fail(f"{a.file}: {e}", 2)
    bak = Path(a.file + ".bak")
    if not a.out and bak.exists():
        fail(f"{bak} is there already (the original from an earlier remap?): move it away, or write elsewhere with --out", 2)
    for name, tl in (("--from", old), ("--to", new)):
        if (lint := timeline_lint.lint(tl, tl.get("lang"))) and not a.skip_lint:
            fail(f"the {name} timeline has {len(lint)} problem(s):\n{timeline_lint.report(lint)}\n(--skip-lint to go on anyway)", 1)
    pairs, how, fresh, dropped = anchors(old, new)
    if len(pairs) < 2:
        fail("the two timelines share no line (by id): nothing to map through" if not any(v != "gone" for v in how.values())
             else "the lines the two timelines share give fewer than two times to map through", 1)
    moved = []
    out = walk(data, {k.strip() for k in a.keys.split(",") if k.strip()}, mapper(pairs), moved)
    dest = Path(a.out or a.file)
    if not a.out:
        shutil.copyfile(a.file, bak)
    m = re.match(r"\s*[\[{]\s*?\n( +)\S", text)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=len(m.group(1)) if m else None) + "\n", encoding="utf-8")
    print(f"remap: {len(moved)} time(s) in {a.file} through {len(pairs)} pairs → {dest}" + ("" if a.out else f" (the original: {bak})"))
    if moved:
        big = max(moved, key=lambda m: abs(m[1] - m[0]))
        print(f"  moved by {min(y - x for x, y, _ in moved):+.3f} to {max(y - x for x, y, _ in moved):+.3f} s; the most: {big[0]} → {big[1]} s")
    said = {"ends": "rewritten (paired by their start and end only)", "gone": "not in the new take", "order": "in another order in the new take (left out)"}
    for kind, what in said.items():
        if ids := [i for i, v in how.items() if v == kind]:
            print(f"  lines {what}: {', '.join(ids[:12])}{f' … ({len(ids)})' if len(ids) > 12 else ''}")
    if dropped:
        print(f"  {dropped} of the paired times ran backwards in the new take and were left out (times near them follow the pairs around them)")
    if fresh:
        print(f"  lines new in the new take (nothing typed can point at them yet): {', '.join(fresh[:12])}{f' … ({len(fresh)})' if len(fresh) > 12 else ''}")
    spans = [(s["start"], s["end"], s["id"]) for s in old["segments"] if isinstance(s, dict) and s.get("id") and timed(s) and how.get(s["id"]) in said]
    check = [(x, y, sid) for x, y, _ in moved for a0, b0, sid in spans if a0 <= x <= b0]
    for x, y, sid in check[:12]:
        print(f"  check by ear: {x} → {y} s falls on line {sid}, {said[how[sid]].split(' (')[0]}")
    if len(check) > 12:
        print(f"  … and {len(check) - 12} more on such lines")
    if clipped := [x for x, _, neg in moved if neg]:
        print(f"  {len(clipped)} time(s) would move before 0 s and are 0 s now: {', '.join(map(str, clipped[:8]))}")

if __name__ == "__main__":
    main()
