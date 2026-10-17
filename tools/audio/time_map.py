"""Read a time map for project scripts and the sound tools (stdlib only).

A time map is film time against another axis (the days of a data series, steps, the seconds of an earlier cut): knots
[t, u] with straight lines between them, and events on that axis with ids. Whatever solved it (a project script now)
writes the file once; the film and these tools only look values up. The JS counterpart is
canvas-film/src/06-time-map.js; tools/audio/test_time_map.py checks that both read a map alike.

  TimeMap.load("data/time.map.json")
    .u(t)            film seconds → the axis then (before the first knot and after the last: the ends)
    .t(u)            the axis → the first film second it gets there (outside the axis: an error)
    .at(id, edge)    an event's film second; edge "end": its end
    .dur(u0, u1)     the film seconds a stretch of the axis takes · .rate(t) axis units per film second
    .day(iso)        a date axis: "YYYY-MM-DD" → u · .events: the events (copies) · .source: {path, sha256}

The file: {"version": 1, "axis": {"kind": "number" | "date" | "seconds", "origin": "YYYY-MM-DD" (date), "unit"},
"knots": [[t, u], …] (t rises, u never falls: a flat stretch is a hold), "events": [{"id", "u", "t", "end"?, "lane"?,
"text"?, "data"?}], and optionally "sources": [{"path", "sha256"}] (the narration take or beat map it was made on, paths
beside the map), "spec", "rebuild" (the command that remakes it) and "note".

usage: bin/vh timemap check <map.json> [--save] [--out FILE]
  Checks the map, lists its events, says whether a recorded source changed since the map was made, and, against the
  events saved last time (--out, default <map>.checked.json beside it), which events moved, which are new and which are
  gone. --save keeps this map's events there. Exit: 0 fine · 1 a source changed · 2 not a map, or a file is missing.
"""
import datetime
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ID = re.compile(r"[A-Za-z0-9_]+")
DAY = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
EPOCH = datetime.date(1970, 1, 1)


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def utc_days(iso):
    """'YYYY-MM-DD' → days since 1970-01-01, or None for something that is not a date"""
    m = DAY.fullmatch(iso) if isinstance(iso, str) else None
    if not m or int(m[1]) < 100:   # the JS reader cannot tell years 0–99 from 1900–1999 (Date.UTC), so neither takes them
        return None
    try:
        return (datetime.date(int(m[1]), int(m[2]), int(m[3])) - EPOCH).days
    except ValueError:
        return None


class TimeMap:
    def __init__(self, data):
        def fail(message):
            raise ValueError(f"time map: {message}")
        if not isinstance(data, dict):
            fail("expected an object with version, axis, knots and events")
        if not (number(data.get("version")) and data["version"] == 1):
            fail(f"version {json.dumps(data.get('version'))}: this engine reads version 1")
        axis = data.get("axis", {"kind": "number"})
        if axis is None:
            axis = {"kind": "number"}
        if not isinstance(axis, dict):
            fail("axis must be an object")
        kind = axis.get("kind", "number") if axis.get("kind") is not None else "number"
        if kind not in ("number", "date", "seconds"):
            fail(f"axis kind {json.dumps(kind)}: one of number, date, seconds")
        if kind == "date" and utc_days(axis.get("origin")) is None:
            fail('a date axis needs an origin "YYYY-MM-DD" (u is days after it)')
        if "unit" in axis and not isinstance(axis["unit"], str):
            fail("axis unit must be a string")
        self.axis = dict(axis, kind=kind)
        knots = data.get("knots")
        if not isinstance(knots, list) or len(knots) < 2:
            fail("knots must list at least two [t, u] pairs")
        out = []
        for i, k in enumerate(knots):
            if not isinstance(k, list) or len(k) != 2 or not number(k[0]) or not number(k[1]):
                fail(f"knot {i + 1}: expected [t, u], two finite numbers")
            if k[0] < 0:
                fail(f"knot {i + 1}: t {k[0]} is before the film starts")
            if i:
                p = knots[i - 1]
                if not k[0] > p[0]:
                    fail(f"knot {i + 1}: t {k[0]} does not come after {p[0]} (t must rise from knot to knot)")
                if k[1] < p[1]:
                    fail(f"knot {i + 1}: u {k[1]} is below {p[1]} (u may stand still, never go back)")
            out.append((k[0], k[1]))
        self.knots = tuple(out)
        events = data.get("events", [])
        if not isinstance(events, list):
            fail("events must be a list")
        self._events, self._by = [], {}
        for i, e in enumerate(events):
            if not isinstance(e, dict):
                fail(f"event {i + 1}: expected an object")
            if not isinstance(e.get("id"), str) or not ID.fullmatch(e["id"]):
                fail(f"event {i + 1}: id {json.dumps(e.get('id'), ensure_ascii=False)}: letters, digits and _")
            if e["id"] in self._by:
                fail(f"event {e['id']}: the id is used twice")
            if not number(e.get("u")) or not number(e.get("t")):
                fail(f"event {e['id']}: needs a finite u and t")
            if e["u"] < self.knots[0][1] or e["u"] > self.knots[-1][1]:
                fail(f"event {e['id']}: u {e['u']} is outside the axis ({self.knots[0][1]}–{self.knots[-1][1]})")
            lo, hi = self.reach(e["u"])
            if e["t"] < lo - 0.001 or e["t"] > hi + 0.001:
                fail(f"event {e['id']}: t {e['t']} s is not where the knots put u {e['u']} ({lo} s)" if lo == hi else
                     f"event {e['id']}: t {e['t']} s is not where the knots put u {e['u']} ({lo}–{hi} s)")
            if "end" in e and not (number(e["end"]) and e["end"] >= e["t"]):
                fail(f"event {e['id']}: end must be a number of seconds, not before t")
            for k in ("lane", "text"):
                if k in e and not isinstance(e[k], str):
                    fail(f"event {e['id']}: {k} must be a string")
            if "data" in e and not isinstance(e["data"], dict):
                fail(f"event {e['id']}: data must be an object")
            self._events.append(dict(e)); self._by[e["id"]] = self._events[-1]
        self.sources = [dict(s) for s in data.get("sources") or [] if isinstance(s, dict) and isinstance(s.get("path"), str) and isinstance(s.get("sha256"), str)]
        self.rebuild = data.get("rebuild") if isinstance(data.get("rebuild"), str) else None
        self.source = None

    @classmethod
    def load(cls, path):
        raw = Path(path).read_bytes()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"time map: {path} is not JSON ({e})") from None
        m = cls(data)
        m.source = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
        return m

    def reach(self, u):
        """the first and the last film second the axis stands at u (the same one unless u is a hold)"""
        K, t0 = self.knots, self.t(u)
        i, hi = 0, len(K) - 1
        while i < hi:   # the last knot at or below u
            m = (i + hi + 1) >> 1
            if K[m][1] <= u: i = m
            else: hi = m - 1
        return t0, (K[i][0] if K[i][1] == u else t0)

    def u(self, t):
        if not number(t):
            raise ValueError("time map: t must be finite seconds")
        K, n = self.knots, len(self.knots)
        if t <= K[0][0]: return K[0][1]
        if t >= K[n - 1][0]: return K[n - 1][1]
        lo, hi = 0, n - 1
        while hi - lo > 1:
            m = (lo + hi) >> 1
            if K[m][0] <= t: lo = m
            else: hi = m
        (ta, ua), (tb, ub) = K[lo], K[hi]
        return ua + (ub - ua) * ((t - ta) / (tb - ta))

    def t(self, u):
        if not number(u):
            raise ValueError('time map: u must be a finite number (a date axis: day("YYYY-MM-DD"))')
        K, n = self.knots, len(self.knots)
        if u < K[0][1] or u > K[n - 1][1]:
            raise ValueError(f"time map: u {u} is outside the axis ({K[0][1]}–{K[n - 1][1]})")
        lo, hi = 0, n - 1
        while lo < hi:   # the first knot at or past u
            m = (lo + hi) >> 1
            if K[m][1] >= u: hi = m
            else: lo = m + 1
        if K[lo][1] == u: return K[lo][0]
        (ta, ua), (tb, ub) = K[lo - 1], K[lo]
        return ta + (tb - ta) * ((u - ua) / (ub - ua))

    def at(self, id, edge="start"):
        e = self._by.get(id)
        if e is None:
            low = str(id).lower()
            near = [k for k in self._by if low in k.lower() or k.lower() in low][:3]
            raise ValueError(f'time map: no event "{id}" ({len(self._events)} events' + (f"; nearest: {', '.join(near)})" if near else ")"))
        if edge == "start": return e["t"]
        if edge != "end": raise ValueError(f'time map: edge {json.dumps(edge)}: "start" or "end"')
        if "end" not in e: raise ValueError(f"time map: event {id} has no end")
        return e["end"]

    def dur(self, u0, u1):
        return self.t(u1) - self.t(u0)

    def rate(self, t):
        if not number(t):
            raise ValueError("time map: t must be finite seconds")
        K = self.knots
        lo, hi = 0, len(K) - 1   # the segment K[lo]..K[lo + 1] that holds t
        while hi - lo > 1:
            m = (lo + hi) >> 1
            if K[m][0] <= t: lo = m
            else: hi = m
        return (K[lo + 1][1] - K[lo][1]) / (K[lo + 1][0] - K[lo][0])

    def day(self, iso):
        if self.axis["kind"] != "date":
            raise ValueError(f"time map: day() needs a date axis (this one is {self.axis['kind']})")
        d = utc_days(iso)
        if d is None:
            raise ValueError(f'time map: {json.dumps(iso)} is not a date "YYYY-MM-DD"')
        return d - utc_days(self.axis["origin"])

    @property
    def events(self):
        return [json.loads(json.dumps(e)) for e in self._events]

    def stale(self, files):
        """the recorded sources that differ from the files given as {resolved path: sha256}: [(path, recorded, now)]"""
        base = Path(self.source["path"]).resolve().parent if self.source else Path.cwd()
        out = []
        for s in self.sources:
            now = files.get(str((base / s["path"]).resolve()))
            if now is not None and now != s["sha256"]:
                out.append((s["path"], s["sha256"], now))
        return out

    def stale_message(self, stale):
        what = " and ".join(f"{p} (recorded sha256 {a[:12]}, now {b[:12]})" for p, a, b in stale)
        how = f"rebuild it: {self.rebuild}" if self.rebuild else 'rebuild it with the script that wrote it (its "rebuild" field can name the command)'
        return f"{self.source['path'] if self.source else 'the time map'} was made on another version of {what}: {how}"


def check(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="bin/vh timemap check", description="check a time map and list its events")
    ap.add_argument("map"); ap.add_argument("--save", action="store_true"); ap.add_argument("--out")
    a = ap.parse_args(argv)
    try:
        m = TimeMap.load(a.map)
    except (OSError, ValueError) as e:
        print(f"time map: {e}".replace("time map: time map:", "time map:"), file=sys.stderr); sys.exit(2)
    rel = lambda p: str(Path(p).resolve().relative_to(Path.cwd())) if Path(p).resolve().is_relative_to(Path.cwd()) else str(p)
    K, kind = m.knots, m.axis["kind"]
    def show(u):   # a date axis as dates (a part day as +0.50), any other as the number
        if kind != "date": return f"{u:g}"
        return datetime.date.fromordinal(EPOCH.toordinal() + utc_days(m.axis["origin"]) + math.floor(u)).isoformat() + (f"+{u % 1:.2f}" if u % 1 else "")
    print(f"time map: {rel(a.map)} · {len(K)} knots · film {K[0][0]:.3f}–{K[-1][0]:.3f} s · axis ({kind}) {show(K[0][1])} – {show(K[-1][1])} · "
          f"{len(m._events)} event{'s' * (len(m._events) != 1)} (sha256 {m.source['sha256'][:12]})")
    holds = sum(1 for i in range(1, len(K)) if K[i][1] == K[i - 1][1])
    if holds: print(f"  {holds} hold{'s' * (holds != 1)} (the axis stands still while the film runs on)")
    code = 0
    base = Path(a.map).resolve().parent
    for s in m.sources:
        p = base / s["path"]
        now = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
        if now != s["sha256"]:
            code = 1
            print(f"  source {s['path']}: {'missing' if now is None else 'changed since the map was made'}" +
                  (f": rebuild the map ({m.rebuild})" if m.rebuild else ": rebuild the map"))
        else: print(f"  source {s['path']}: as when the map was made")
    w = max([4] + [len(e["id"]) for e in m._events])
    if m._events: print(f"  {'t'.rjust(8)}  {'id'.ljust(w)}  u")
    for e in sorted(m._events, key=lambda e: (e["t"], e["id"])):
        extra = "".join(f"  {k} {e[k]}" for k in ("lane",) if k in e) + (f"  end {e['end']:.3f}" if "end" in e else "")
        print(f"  {e['t']:8.3f}  {e['id'].ljust(w)}  {show(e['u'])}{extra}")
    out = Path(a.out) if a.out else Path(str(Path(a.map).with_suffix("")) + ".checked.json")
    if out.resolve() == Path(a.map).resolve(): print("time map: --out is the map itself", file=sys.stderr); sys.exit(2)
    now = [{"id": e["id"], "t": e["t"], **({"end": e["end"]} if "end" in e else {})} for e in m._events]
    if out.exists():
        try:
            before = json.loads(out.read_text())
            was = {e["id"]: e for e in before["events"]}
        except (ValueError, KeyError, TypeError):
            print(f"  {rel(out)}: not readable as saved events, so not compared"); before = None
        if before is not None:
            here = {e["id"]: e for e in now}
            moved = sorted(((e, e["t"] - was[e["id"]]["t"]) for e in now if e["id"] in was and abs(e["t"] - was[e["id"]]["t"]) >= 0.0005), key=lambda x: -abs(x[1]))
            new = [e for e in now if e["id"] not in was]; gone = [i for i in was if i not in here]
            why = " (the map changed)" if before.get("sha256") != m.source["sha256"] else ""
            if not (moved or new or gone): print(f"  since {rel(out)}: nothing moved{why}")
            else:
                print(f"  since {rel(out)}{why}: {len(moved)} moved, {len(new)} new, {len(gone)} gone")
                for e, d in moved[:20]: print(f"    {e['id'].ljust(w)}  {was[e['id']]['t']:.3f} → {e['t']:.3f} s  ({d:+.3f})")
                if len(moved) > 20: print(f"    … and {len(moved) - 20} more")
                for e in new[:10]: print(f"    new   {e['id']}")
                for i in gone[:10]: print(f"    gone  {i}")
    if a.save:
        try:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps({"note": "time_map.py check --save: the events of the map as last checked", "map": str(Path(a.map).resolve().relative_to(out.resolve().parent)) if Path(a.map).resolve().is_relative_to(out.resolve().parent) else str(Path(a.map).resolve()),
                                       "sha256": m.source["sha256"], "events": now}, ensure_ascii=False, indent=1) + "\n")
        except OSError as e: print(f"time map: cannot write {out}: {e}", file=sys.stderr); sys.exit(2)
        print(f"  saved: {rel(out)}")
    sys.exit(code)


if __name__ == "__main__":
    if sys.argv[1:2] == ["check"]: check(sys.argv[2:])
    print(__doc__.strip()); sys.exit(0 if sys.argv[1:2] in (["-h"], ["--help"]) else 2)
