"""Motifs for tools/audio/music.py: define a phrase once in the score's "motifs" block, call it from any note list.

  "motifs": {"A": {"notes": [[0, 1, "d1"], [1, 2, "d5"], [3, 1, "d4"], [4, 1, "d3"]]}, "B": [[0, 0.5, "c0"], …]}
  "pattern": [{"motif": "A", "at": 8}, {"motif": "A", "at": 16, "transform": ["shift:+2", "augment:2"]}, [24, 2, "d1"]]

A call is replaced, in place, by the motif's notes after its transforms. The result is an ordinary note list, so
everything downstream (loop, swing, humanize, tremolo, hits) treats it like hand-written notes.
Call keys: motif, at (beat offset, default 0), transform [...], the shorthands below, vel, vels, repeat, every,
shift_each, transpose_each, vel_each. Order: take / drop / slice, then the transform list, then the other shorthands
in this order: shift transpose octave mode invert retro augment diminish rhythm legato; then vels, then vel, then
repeat, then at.
Transforms ("op:arg" strings; every one also works as a key of the call, e.g. "take": 3):
  shift:+n        n scale steps: d and s tokens move n steps, c tokens n chord tones; other pitches move n steps in
                  the part's scale when they resolve
  transpose:+n    n semitones (absolute notes, MIDI numbers and +k tokens are rewritten; d, s, c move after resolving)
  octave:+n       n octaves (the ' and , marks)
  invert          mirror each token kind around the call's first note of that kind (scale steps; semitones for
                  absolute notes)
  retro           reverse in time
  augment:k       beats and lengths × k       diminish:k   ÷ k
  rhythm:x        every note x beats long, one after another (a motif turned into an even figure); a list of
                  lengths is taken in turn and cycled: "rhythm": [1.5, 0.5] dots it, [2, 2, 4, 6] rewrites it
  take:n  drop:n  slice:a-b (1-based)          fragments; a fragment's first note moves to beat 0
  mode:name       resolve this call's d and s tokens in another scale (dorian, phrygian, penta, yu …)
  legato:k        lengths × k
vel: a number sets every note, "*0.8" scales, "+0.1" / "-0.1" adds (notes without a velocity count as 0.8); vels: a
list, one velocity per note. repeat: N copies, every E beats (default: the motif's length), each shift_each steps
higher, transpose_each semitones higher and vel_each ("+0.04", a number, or "*1.1") louder than the one before:
sequences and ostinati. A motif may call another motif. Slots a call had to fill in come back out: [0, 1, "d1"] stays
three long.
"""
import re
import sys

TOK = re.compile(r"^([csd])(-?\d+)([',]*)$")
SEMI = re.compile(r"^([+-]\d+)([',]*)$")
NOTE_NAME = re.compile(r"^([A-G])([#b]?)(-?\d+)([',]*)$")
PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8,
      "A": 9, "A#": 10, "Bb": 10, "B": 11}
SHORT = ("shift", "transpose", "octave", "mode", "invert", "retro", "augment", "diminish", "rhythm", "legato")
CALL_KEYS = {"motif", "at", "transform", "take", "drop", "slice", "vel", "vels", "repeat", "every", "shift_each",
             "transpose_each", "vel_each", *SHORT}
KNOBS = ("_shift", "_semis", "_scale")   # carried in a note's art dict; music.note_list applies and removes them


def _err(msg):
    sys.exit(f"music: {msg}")


def is_call(e):
    return isinstance(e, dict) and "motif" in e


def has_calls(pat):
    if is_call(pat): return True
    if isinstance(pat, list): return any(is_call(e) for e in pat)
    if isinstance(pat, dict): return any(has_calls(v) for v in pat.values())
    return False


def expand_pattern(pat, motifs, where):
    """Unfold every motif call in a part's pattern (a note list, a single call, or a dict by beats per bar). A pattern
    without calls comes back as the very same object."""
    if not has_calls(pat): return pat
    if is_call(pat): return expand([pat], motifs, where)
    if isinstance(pat, dict): return {k: expand_pattern(v, motifs, f"{where} (pattern {k!r})") for k, v in pat.items()}
    return expand(pat, motifs, where)


def expand(notes, motifs, where, depth=0):
    out = []
    for e in notes:
        if is_call(e): out += call(e, motifs, where, depth)
        elif isinstance(e, dict): _err(f"{where}: an object in a note list must be a motif call {{\"motif\": …}}, not {e!r}")
        else: out.append(list(e))
    return out


def motif_notes(motifs, name, where, depth):
    if not isinstance(motifs, dict) or name not in motifs:
        _err(f"{where}: no motif named {name!r}" + (f" (motifs: {', '.join(map(str, motifs))})" if isinstance(motifs, dict) and motifs else " (the score has no \"motifs\")"))
    if depth > 8: _err(f"{where}: motif {name!r} calls itself (a cycle through its calls)")
    m = motifs[name]; notes = m.get("notes") if isinstance(m, dict) else m
    if not isinstance(notes, list) or not notes:
        _err(f"{where}: motif {name!r} needs \"notes\": [[beat, beats, pitch, vel, art], …]")
    for j, n in enumerate(notes):
        if not is_call(n) and (not isinstance(n, (list, tuple)) or len(n) < 2):
            _err(f"{where}: motif {name!r} note {j} is {n!r}; write [beat, beats, pitch, vel, art]")
    return expand(notes, motifs, f"{where} → motif {name!r}", depth + 1)


def _parse(step, where):
    if isinstance(step, (list, tuple)) and len(step) == 2: return step[0], step[1]
    if not isinstance(step, str): _err(f"{where}: a transform is a string such as \"shift:+2\", not {step!r}")
    op, _, arg = step.partition(":")
    return op.strip(), (arg.strip() if arg else True)


def _num(v, what, where):
    try: return float(v)
    except (TypeError, ValueError): _err(f"{where}: {what} needs a number, not {v!r}")


def _knob(n, key, add):   # add to a note's private knob (the 5th slot becomes a dict)
    art = n[4] if isinstance(n[4], dict) else ({} if not n[4] else {"_stroke": n[4]})
    art = dict(art); art[key] = art.get(key, 0) + add if key != "_scale" else add; n[4] = art


def _map_tok(tok, fn):
    return [fn(t) for t in tok] if isinstance(tok, list) else fn(tok)


def _shift(notes, k, where):
    out = []
    for n in notes:
        n = list(n); rest = []
        def one(t):
            if isinstance(t, str):
                m = TOK.match(t.strip())
                if m: return f"{m.group(1)}{int(m.group(2)) + k}{m.group(3)}"
            if t is None: return t
            rest.append(1); return t
        n[2] = _map_tok(n[2], one)
        if rest and k: _knob(n, "_shift", k)
        out.append(n)
    return out


def _transpose(notes, k, where):
    out = []
    for n in notes:
        n = list(n); rest = []
        def one(t):
            if isinstance(t, (int, float)) and not isinstance(t, bool): return t + k
            if isinstance(t, str):
                s = t.strip(); m = SEMI.match(s)
                if m: return f"{int(m.group(1)) + k:+d}{m.group(2)}"
                m = NOTE_NAME.match(s)
                if m: return 12 * (int(m.group(3)) + 1) + PC[m.group(1) + m.group(2)] + k + 12 * (m.group(4).count("'") - m.group(4).count(","))
                if s.isdigit(): return int(s) + k
            if t is None: return t
            rest.append(1); return t
        n[2] = _map_tok(n[2], one)
        if rest and k: _knob(n, "_semis", k)
        out.append(n)
    return out


def _octave(notes, k, where):
    k = int(k); out = []
    for n in notes:
        n = list(n); rest = []
        def one(t):
            if isinstance(t, (int, float)) and not isinstance(t, bool): return t + 12 * k
            if isinstance(t, str) and t != "chord": return t + ("'" * k if k > 0 else "," * -k)
            if t is None: return t
            rest.append(1); return t
        n[2] = _map_tok(n[2], one)
        if rest and k: _knob(n, "_semis", 12 * k)
        out.append(n)
    return out


def _marks(m): return m.count("'") - m.count(",")


def _parts(t):
    """A token's (kind, number, octave marks) for invert, or None. d, s, c keep their marks apart (a scale's octave is
    not always 7 steps); semitone and absolute pitches fold them in."""
    if isinstance(t, (int, float)) and not isinstance(t, bool): return ("abs", t, 0)
    if not isinstance(t, str): return None
    s = t.strip(); m = TOK.match(s)
    if m: return (m.group(1), int(m.group(2)), _marks(m.group(3)))
    m = SEMI.match(s)
    if m: return ("semi", int(m.group(1)) + 12 * _marks(m.group(2)), 0)
    m = NOTE_NAME.match(s)
    if m: return ("abs", 12 * (int(m.group(3)) + 1) + PC[m.group(1) + m.group(2)] + 12 * _marks(m.group(4)), 0)
    if s.isdigit(): return ("abs", int(s), 0)
    return None


def _invert(notes, arg, where):
    pivot = {}
    for n in notes:
        for t in (n[2] if isinstance(n[2], list) else [n[2]]):
            v = _parts(t)
            if v and v[0] not in pivot: pivot[v[0]] = v[1:]
    out = []
    for n in notes:
        n = list(n)
        def one(t):
            v = _parts(t)
            if not v:
                if t is None or t == "chord": return t
                _err(f"{where}: invert cannot read the pitch {t!r}")
            kind, x, mk = v; px, pm = pivot[kind]; y, ym = 2 * px - x, 2 * pm - mk
            if kind in "dsc": return f"{kind}{y}" + ("'" * ym if ym > 0 else "," * -ym)
            return f"{y:+d}" if kind == "semi" else y
        n[2] = _map_tok(n[2], one)
        if isinstance(n[4], dict):
            art = dict(n[4])
            for key in ("_shift", "_semis"):
                if key in art: art[key] = -art[key]
            n[4] = art
        out.append(n)
    return out


def _retro(notes, arg, where):
    end = max(n[0] + n[1] for n in notes)
    return sorted(([end - (n[0] + n[1]), n[1], *n[2:]] for n in notes), key=lambda n: n[0])


def _scale_time(notes, k, where):
    return [[n[0] * k, n[1] * k, *n[2:]] for n in notes]


def _rhythm(notes, x, where):
    """Every note x beats long, one after another; or a list of lengths, taken in turn (and cycled): [0.75, 0.25]."""
    if isinstance(x, str) and re.search(r"[\s,]", x.strip()): x = re.split(r"[\s,]+", x.strip())
    if not isinstance(x, (list, tuple)):
        x = _num(x, "rhythm", where)
        if x <= 0: _err(f"{where}: rhythm needs a length > 0")
        return [[i * x, x, *n[2:]] for i, n in enumerate(notes)]
    xs = [_num(v, "rhythm", where) for v in x if v != ""]
    if not xs or min(xs) <= 0: _err(f"{where}: rhythm needs lengths > 0, not {x!r}")
    out, t = [], 0.0
    for i, n in enumerate(notes):
        out.append([round(t, 9), xs[i % len(xs)], *n[2:]]); t += xs[i % len(xs)]
    return out


def _fragment(notes, lo, hi):
    frag = notes[lo:hi]
    if not frag: return []
    b0 = frag[0][0]; return [[n[0] - b0, *n[1:]] for n in frag]


def _mode(notes, name, where):
    out = []
    for n in notes:
        n = list(n); _knob(n, "_scale", str(name)); out.append(n)
    return out


def _legato(notes, k, where):
    return [[n[0], n[1] * k, *n[2:]] for n in notes]


def _vel(notes, spec, where):
    out = []
    for n in notes:
        n = list(n); v = 0.8 if n[3] is None else float(n[3])
        if isinstance(spec, str) and spec.strip()[:1] in "*+-":
            s = spec.strip(); x = _num(s[1:], "vel", where)
            v = v * x if s[0] == "*" else v + x if s[0] == "+" else v - x
        else: v = _num(spec, "vel", where)
        n[3] = round(max(0.0, v), 6); out.append(n)
    return out


def _step(notes, op, arg, where):
    if op == "shift": return _shift(notes, int(_num(arg, "shift", where)), where)
    if op == "transpose": return _transpose(notes, int(_num(arg, "transpose", where)), where)
    if op == "octave": return _octave(notes, int(_num(arg, "octave", where)), where)
    if op == "invert": return _invert(notes, arg, where) if arg is not False else notes
    if op == "retro": return _retro(notes, arg, where) if arg is not False else notes
    if op == "augment": return _scale_time(notes, _num(arg, "augment", where), where)
    if op == "diminish":
        k = _num(arg, "diminish", where)
        if k <= 0: _err(f"{where}: diminish needs a number > 0")
        return _scale_time(notes, 1 / k, where)
    if op == "rhythm": return _rhythm(notes, arg, where)
    if op == "legato": return _legato(notes, _num(arg, "legato", where), where)
    if op == "mode": return _mode(notes, arg, where)
    if op == "take": return _fragment(notes, 0, int(_num(arg, "take", where)))
    if op == "drop": return _fragment(notes, int(_num(arg, "drop", where)), None)
    if op == "slice":
        a, _, b = str(arg).partition("-")
        return _fragment(notes, int(_num(a, "slice", where)) - 1, int(_num(b or a, "slice", where)))
    _err(f"{where}: unknown transform {op!r}; use shift transpose octave invert retro augment diminish rhythm take drop slice mode legato")


def call(c, motifs, where, depth=0):
    """One motif call → plain notes [[beat, beats, pitch, vel, art], …]."""
    bad = set(c) - CALL_KEYS
    if bad: _err(f"{where}: unknown key(s) {sorted(bad)} in a motif call; use {', '.join(sorted(CALL_KEYS))}")
    name = c["motif"]; w = f"{where} (motif call {name!r})"
    notes = [list(n) + [None] * (5 - len(n)) for n in motif_notes(motifs, name, where, depth)]
    for key in ("take", "drop", "slice"):
        if key in c: notes = _step(notes, key, c[key], w)
    tr = c.get("transform", [])
    for s in (tr if isinstance(tr, list) else [tr]):
        op, arg = _parse(s, w); notes = _step(notes, op, arg, w)
    for key in SHORT:
        if key in c: notes = _step(notes, key, c[key], w)
    if "vels" in c:
        vs = c["vels"]
        if not isinstance(vs, list) or len(vs) != len(notes):
            _err(f"{w}: \"vels\" needs one velocity per note ({len(notes)}), not {vs!r}")
        notes = [[*n[:3], _num(v, "vels", w), n[4]] for n, v in zip(notes, vs)]
    if "vel" in c: notes = _vel(notes, c["vel"], w)
    if not notes: return []
    reps = int(_num(c.get("repeat", 1), "repeat", w))
    if reps < 1: _err(f"{w}: repeat needs a whole number ≥ 1")
    every = _num(c["every"], "every", w) if "every" in c else max(n[0] + n[1] for n in notes)
    sh, tp, at = int(_num(c.get("shift_each", 0), "shift_each", w)), int(_num(c.get("transpose_each", 0), "transpose_each", w)), _num(c.get("at", 0), "at", w)
    ve = c.get("vel_each")
    if ve is not None:   # "+0.04" (also a plain number), "-0.04" or "*1.1", applied once more on every copy
        ve = ve.strip() if isinstance(ve, str) else f"+{_num(ve, 'vel_each', w)}"
        if ve[:1] not in "*+-": ve = "+" + ve
        vx = _num(ve[1:], "vel_each", w)
    out = []
    for r in range(reps):
        ns = notes
        if r and sh: ns = _shift(ns, r * sh, w)
        if r and tp: ns = _transpose(ns, r * tp, w)
        if r and ve is not None: ns = _vel(ns, f"*{vx ** r}" if ve[0] == "*" else f"{ve[0]}{vx * r}", w)
        off = at + r * every
        out += [[round(n[0] + off, 9) if off else n[0], n[1], *n[2:]] for n in ns]
    for n in out:   # drop the empty slots this call filled in: [0, 1, "d1", None, None] → [0, 1, "d1"]
        while len(n) > 2 and n[-1] is None: n.pop()
    return out
