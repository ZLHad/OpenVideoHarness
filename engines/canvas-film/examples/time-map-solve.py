#!/usr/bin/env python3
"""An example of solving a time map (stdlib only): a spec in, a map out, in the format src/06-time-map.js and
tools/audio/time_map.py read. A reference to copy into a project and change, not a bin/vh command: which strategies a
film uses, and their numbers, are the project's.

  python3 time-map-solve.py time-map-spec.json time.map.json
  bin/vh timemap check time.map.json --save       # the events; next time, which of them moved

The spec (time-map-spec.json beside this file is a synthetic one):
  axis      as in the map: {"kind": "date", "origin": "YYYY-MM-DD"} (places are dates) or {"kind": "number"}
  segments  [{"id", "from", "to", "t": [s, s]}] end to end along the axis; each end's film time is fixed
  events    [{"id", "at", "lane"?, "text"?, "need"?, "slow"?: {"s", "sigma"}, "pin"?: s, "data"?}]
  windows   [{"from", "to", "weight", "edge"}]: the axis runs 1 + weight times slower inside, edges soft over ~edge
  holds     [{"at", "s"}]: the axis stands still there for s seconds while the film runs on
  lanes     {"top": {"rows": 1, "gap": 0.5}}: a card must be read (need + gap) before the card `rows` later in its lane
  sigma     a slow-down's default width (axis units) · step: the knots' spacing (axis units)

How: the segment ends and the pinned events ("pin": the t a settled event keeps, copied from the map) cut the axis
into spans whose two ends have fixed film times. In a span, film time per axis unit is r·w(u) (w: the windows), plus
a Gaussian bump of s seconds at each slowed event, cut off at the span's edges, plus the holds; r takes what is left.
A span never borrows time from a neighbour, so an edit between two pins changes that span's knots and no others.
A card that is not read before the next one in its lane comes slows both events of the pair (unless pinned or on a
span's edge) and the span is solved again, at most 60 times; a pair across a pin is only reported. need: the event's
own, else the floor bin/vh readcheck uses; readcheck has the last word on reading time.
Exit: 0 written (shortfalls are said) · 1 a span cannot fit its slow-downs and holds · 2 a bad spec.
"""
import datetime, hashlib, json, math, os, sys
from pathlib import Path


def need(text):   # readcheck's floor: one brisk read, CJK ÷ 7 + other characters ÷ 20 + 0.8 s, never under 1.5 s
    cjk = sum(1 for c in text if "⺀" <= c <= "鿿" or "豈" <= c <= "﫿" or "＀" <= c <= "￯")
    return max(1.5, cjk / 7 + (sum(not c.isspace() for c in text) - cjk) / 20 + 0.8)


def solve(spec):
    axis = spec.get("axis", {"kind": "number"})
    origin = datetime.date.fromisoformat(axis["origin"]) if axis.get("kind") == "date" else None
    U = lambda v: float((datetime.date.fromisoformat(v) - origin).days) if isinstance(v, str) else float(v)
    step, lanes = spec.get("step", 1), spec.get("lanes", {})
    windows = [(U(w["from"]), U(w["to"]), w.get("weight", 1), w.get("edge", 1)) for w in spec.get("windows", [])]
    holds = {U(h["at"]): h["s"] for h in spec.get("holds", [])}
    soft = lambda x: 0.5 * (1 + math.tanh(x / 2))   # the logistic, without overflow far from the edge
    w = lambda u: 1 + sum(k * soft((u - a) / e) * soft((b - u) / e) for a, b, k, e in windows)
    Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))

    fixed = {}   # axis place → film second: the segment ends, then the pins
    for g in spec["segments"]:
        for u, t in zip((U(g["from"]), U(g["to"])), g["t"]):
            if fixed.setdefault(u, t) != t:
                raise ValueError(f"segment {g['id']} starts at {t} s where the one before ends at {fixed[u]} s (a pause there is a hold)")
    ev = []
    for e in spec.get("events", []):
        slow, read = e.get("slow") or {}, e.get("need", need(e["text"]) if "text" in e else 0)
        ev.append(dict(e, u=U(e["at"]), s=slow.get("s", 0), sigma=slow.get("sigma", spec.get("sigma", 3)),
                       read=read, gap=lanes.get(e.get("lane"), {}).get("gap", 0)))
        if "pin" in e and fixed.setdefault(ev[-1]["u"], e["pin"]) != e["pin"]:
            raise ValueError(f"event {e['id']} is pinned at {e['pin']} s on a segment end fixed at {fixed[ev[-1]['u']]} s")
    pts = sorted(fixed.items())
    for (ua, ta), (ub, tb) in zip(pts, pts[1:]):
        if tb <= ta:
            raise ValueError(f"the fixed times do not rise along the axis: {ta} s at {ua:g}, then {tb} s at {ub:g}")
    if any(not pts[0][0] <= e["u"] <= pts[-1][0] for e in ev):
        raise ValueError("an event lies outside the segments")
    for e in ev:
        e["edge"] = e["u"] in fixed   # pinned, or on a segment's end: its time is not the span's to move
    pairs = [(a, b) for name, L in lanes.items()
             for cards in [sorted((e for e in ev if e.get("lane") == name), key=lambda e: e["u"])]
             for a, b in zip(cards, cards[L.get("rows", 1):])]

    def span(ua, ta, ub, tb, mine, hold):   # knots and arrival times of one span, or None when it cannot fit
        grid = sorted({ua + k * step for k in range(int((ub - ua) / step))} | {ub} | {e["u"] for e in mine} | set(hold))
        base = [w((a + b) / 2) * (b - a) for a, b in zip(grid, grid[1:])]
        extra = [sum(e["s"] * (Phi((b - e["u"]) / e["sigma"]) - Phi((a - e["u"]) / e["sigma"])) for e in mine if e["s"])
                 for a, b in zip(grid, grid[1:])]
        r = (tb - ta - sum(hold.values()) - sum(extra)) / sum(base)
        if r <= 0:
            return None
        t, knots, at = ta, [], {}
        for i, u in enumerate(grid):
            t += r * base[i - 1] + extra[i - 1] if i else 0
            at.setdefault(u, t); knots.append([t, u])
            if u in hold:
                t += hold[u]; knots.append([t, u])
        knots[-1][0] = tb   # the fixed end exactly, not the sum's rounding
        return knots, at

    knots, at, slowed, short = [], {}, {}, []
    for k, ((ua, ta), (ub, tb)) in enumerate(zip(pts, pts[1:])):
        mine = [e for e in ev if ua <= e["u"] <= ub]
        hold = {u: s for u, s in holds.items() if ua < u <= ub or (k == 0 and u == ua)}
        inside = [(a, b) for a, b in pairs if a in mine and b in mine]
        sol, s0 = span(ua, ta, ub, tb, mine, hold), {e["id"]: e["s"] for e in mine}
        if sol is None:
            raise OverflowError(f"the span {ta:g}–{tb:g} s cannot fit its slow-downs and holds")
        for _ in range(60):   # the lane check: slow both events of a pair whose first card is not read in time
            late = [(a, b, a["read"] + a["gap"] - (sol[1][b["u"]] - sol[1][a["u"]])) for a, b in inside]
            late = [(a, b, d) for a, b, d in late if d > 0.001 and not (a["edge"] and b["edge"])]
            if not late:
                break
            keep = {e["id"]: e["s"] for e in mine}
            for a, b, d in late:
                for e in (a, b):
                    if not e["edge"]: e["s"] += d
            nxt = span(ua, ta, ub, tb, mine, hold)
            if nxt is None:   # no room left in this span: keep the last fit and say what is short
                for e in mine: e["s"] = keep[e["id"]]
                break
            sol = nxt
        slowed.update({e["id"]: e["s"] - s0[e["id"]] for e in mine if e["s"] > s0[e["id"]]})
        knots += sol[0][1:] if knots and sol[0][0] == knots[-1] else sol[0]
        for u, t in sol[1].items(): at.setdefault(u, t)
    for a, b in pairs:   # every pair, across pins too: what is still short
        if a["read"] + a["gap"] - (at[b["u"]] - at[a["u"]]) > 0.001:
            short.append(f"lane {a['lane']}: {a['id']} needs {a['read'] + a['gap']:.2f} s before {b['id']}, has {at[b['u']] - at[a['u']]:.2f} s")
    R = lambda x: round(x, 6)
    events = [{"id": e["id"], "u": R(e["u"]), "t": R(at[e["u"]]), **({"end": R(at[e["u"]] + e["read"])} if e["read"] else {}),
               **{k: e[k] for k in ("lane", "text", "data") if k in e}} for e in ev]
    return [[R(t), R(u)] for t, u in knots], events, pts, slowed, short


def main(argv):
    if len(argv) != 2 or argv[0] in ("-h", "--help"):
        print(__doc__.strip()); return 0 if argv[:1] in (["-h"], ["--help"]) else 2
    spec_path, out = Path(argv[0]), Path(argv[1])
    try:
        raw = spec_path.read_bytes(); spec = json.loads(raw)
        knots, events, pts, slowed, short = solve(spec)
    except OverflowError as e:
        print(f"time-map-solve: {e}", file=sys.stderr); return 1
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"time-map-solve: {spec_path}: {e!r}" if isinstance(e, KeyError) else f"time-map-solve: {spec_path}: {e}", file=sys.stderr); return 2
    out.write_text(json.dumps({
        "version": 1, "note": "written by time-map-solve.py from the spec named below; edit the spec, not this",
        "axis": spec.get("axis", {"kind": "number"}), "rebuild": f"python3 {sys.argv[0]} {argv[0]} {argv[1]}",
        "spec": {"path": os.path.relpath(spec_path, out.parent), "sha256": hashlib.sha256(raw).hexdigest()},
        "knots": knots, "events": events}, ensure_ascii=False, indent=1) + "\n")
    unit = spec.get("axis", {}).get("unit", "unit")
    print(f"time map: {spec_path} → {out} · {len(pts) - 1} spans · {len(events)} events · film {knots[0][0]:g}–{knots[-1][0]:g} s")
    rate = lambda a, b: (knots[b][1] - knots[a][1]) / (knots[b][0] - knots[a][0])
    for u, t in pts[1:-1]:   # how sharply the speed turns at each inner fixed point (a hold there: arriving, leaving)
        at_u = [k for k, (kt, ku) in enumerate(knots) if ku == u]
        print(f"  fixed {t:g} s: {rate(at_u[0] - 1, at_u[0]):.2f} → {rate(at_u[-1], at_u[-1] + 1):.2f} {unit}/s across it")
    if slowed:
        print("  slowed for reading: " + ", ".join(f"{k} +{v:.2f} s" for k, v in slowed.items()))
    for s in short:
        print(f"  short: {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
