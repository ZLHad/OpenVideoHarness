"""Motifs for tools/audio/music.py: define a phrase once in the score's "motifs" block, call it from any note list.

  "motifs": {"A": {"notes": [[0, 1, "d1"], [1, 2, "d5"], [3, 1, "d4"], [4, 1, "d3"]]},
             "R": {"notes": [[1, 1, "c0"], [2, 1, "c2"]], "len": 4}}
  "pattern": [{"motif": "A", "at": 8}, {"motif": "A", "at": 16, "transform": ["shift:+2", "augment:2"]}, [24, 2, "d1"]]

A call is replaced, in place, by the motif's notes after its transforms. The result is an ordinary note list, so
everything downstream (loop, swing, humanize, tremolo, hits) treats it like hand-written notes. A motif may call other
motifs, but not itself (directly or through others). "len" (beats, optional) is the motif's length when it starts or
ends with a rest: retro mirrors within it and repeat spaces the copies by it; without it both use the notes' span.

A call's keys run in this order:
  1. take, drop, slice (as keys)
  2. "transform": ["op:arg", …], in the order written (any op below, take / drop / slice too)
  3. the ops as keys, always in this order: shift transpose octave mode invert retro augment diminish rhythm legato
  4. vels, then vel
  5. repeat, with every, shift_each, transpose_each and vel_each
  6. at, a beat offset (negative: a pickup)
Ops:
  shift:n        n scale steps: d and s tokens move n steps, c tokens n chord tones; other pitches (absolute, MIDI,
                 +k, "chord") move n steps along the part's scale once they resolve (a note between two scale notes
                 keeps its distance from the one below)
  transpose:n    n semitones
  octave:n       n octaves
  invert         mirror around the first note in list order, per token kind: d and s in scale steps, c in chord-tone
                 index, absolute and +k pitches in semitones; rests, "chord" and null stay as they are
  retro          reverse in time (within "len" when the motif has one)
  augment:k      beats and lengths × k       diminish:k   ÷ k       (k > 0)
  rhythm:x       every note x beats long, one after another; or a list of lengths taken in turn, cycled when it is
                 shorter than the notes: "rhythm": [1.5, 0.5] dots a motif, [2, 2, 4, 6] rewrites it
  take:n  drop:n  slice:a-b     a fragment, notes counted from 1 ("slice": "2-4", 3 or [2, 4]); its first note
                 moves to beat 0, and it must keep at least one note
  mode:name      the scale this call's d and s tokens, and any waiting shift, resolve in (dorian, phrygian, penta,
                 yu …), wherever it stands in the list: it picks a scale, it does not move pitches
  legato:k       lengths × k
Counts (shift, transpose, octave, take, drop, slice, repeat, shift_each, transpose_each) are whole numbers, and an op
without its value is an error. Pitch ops apply in the order written: where a token cannot be rewritten (shift on "E4",
transpose on "d3"), the op waits on the note and runs, in order with the ones after it, once the pitch has resolved.
vel: a number sets every note, "*0.8" scales, "+0.1" / "-0.1" adds (a note without a velocity counts as 0.8); vels:
one velocity per note. repeat: N copies, "every" beats apart (default: the motif's length), each shift_each steps
higher, transpose_each semitones higher and vel_each ("+0.04", "-0.04", a number, or "*1.1") louder than the one
before: sequences and ostinati. "every": 0 stacks the copies ("shift_each": 2 gives parallel thirds). Slots a call had
to fill in come back out: [0, 1, "d1"] stays three long.
"""
import math
import re
import sys

TOK = re.compile(r"^([csd])(-?\d+)([',]*)$")
SEMI = re.compile(r"^([+-]\d+)([',]*)$")
NOTE_NAME = re.compile(r"^([A-G])([#b]?)(-?\d+)([',]*)$")
PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8,
      "A": 9, "A#": 10, "Bb": 10, "B": 11}
RESTS = ("", ".", "r", "-", "_")
FRAG = ("take", "drop", "slice")
SHORT = ("shift", "transpose", "octave", "mode", "invert", "retro", "augment", "diminish", "rhythm", "legato")
CALL_KEYS = {"motif", "at", "transform", "vel", "vels", "repeat", "every", "shift_each", "transpose_each", "vel_each", *FRAG, *SHORT}
EXAMPLE = {"shift": "+2", "transpose": "+5", "octave": "+1", "augment": "2", "diminish": "2", "rhythm": "0.5", "take": "3",
           "drop": "1", "slice": "2-4", "mode": "dorian", "legato": "1.1"}
KNOBS = ("_ops", "_scale")   # carried in a note's art dict; music.note_list applies and removes them


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


def expand(notes, motifs, where, stack=()):
    out = []
    for e in notes:
        if is_call(e): out += call(e, motifs, where, stack)
        elif isinstance(e, dict): _err(f"{where}: an object in a note list must be a motif call {{\"motif\": …}}, not {e!r}")
        else: out.append(list(e))
    return out


def motif_notes(motifs, name, where, stack=()):
    """A motif's notes with its own calls unfolded, and its "len" (or None). stack: the motifs being unfolded."""
    if not isinstance(name, str): _err(f"{where}: a motif is called by its name, a string ({{\"motif\": \"A\"}}), not {name!r}")
    if not isinstance(motifs, dict) or name not in motifs:
        _err(f"{where}: no motif named {name!r}" + (f" (motifs: {', '.join(map(str, motifs))})" if isinstance(motifs, dict) and motifs else " (the score has no \"motifs\")"))
    if name in stack: _err(f"{where}: motif {name!r} calls itself: {' → '.join(stack[stack.index(name):] + (name,))}")
    m = motifs[name]; notes = m.get("notes") if isinstance(m, dict) else m
    if not isinstance(notes, list) or not notes:
        _err(f"{where}: motif {name!r} needs \"notes\": [[beat, beats, pitch, vel, art], …]")
    for j, n in enumerate(notes):
        if not is_call(n) and (not isinstance(n, (list, tuple)) or len(n) < 2):
            _err(f"{where}: motif {name!r} note {j} is {n!r}; write [beat, beats, pitch, vel, art]")
    L = m.get("len") if isinstance(m, dict) else None
    if L is not None:
        L = _num(L, "len", f"{where}: motif {name!r}")
        if L <= 0: _err(f"{where}: motif {name!r}: len needs a number of beats > 0")
    out = expand(notes, motifs, f"{where} → motif {name!r}", stack + (name,))
    if L is not None and max(float(n[0]) + float(n[1]) for n in out) > L + 1e-9:
        _err(f"{where}: motif {name!r}: its notes run to beat {max(float(n[0]) + float(n[1]) for n in out):g}, past its len {L:g}")
    return out, L


def _num(v, what, where):
    if v is None or isinstance(v, bool): _err(f"{where}: {what} needs a number, not {v!r}")
    try: x = float(v)
    except (TypeError, ValueError): _err(f"{where}: {what} needs a number, not {v!r}")
    if not math.isfinite(x): _err(f"{where}: {what} needs a finite number, not {v!r}")
    return x


def _int(v, what, where, lo=None):
    x = _num(v, what, where)
    if x != int(x): _err(f"{where}: {what} needs a whole number, not {v!r}")
    if lo is not None and x < lo: _err(f"{where}: {what} needs a whole number ≥ {lo}, not {v!r}")
    return int(x)


def _parse(step, where):
    if isinstance(step, (list, tuple)) and len(step) == 2: return str(step[0]).strip(), step[1]
    if not isinstance(step, str): _err(f"{where}: a transform is a string such as \"shift:+2\", not {step!r}")
    op, sep, arg = step.partition(":")
    return op.strip(), (arg.strip() if sep else None)


def _toks(n): return n[2] if isinstance(n[2], list) else [n[2]]
def _map_tok(tok, fn): return [fn(t) for t in tok] if isinstance(tok, list) else fn(tok)
def _rest(t): return isinstance(t, str) and t.strip() in RESTS
def _isnum(t): return isinstance(t, (int, float)) and not isinstance(t, bool)
def _marks(m): return m.count("'") - m.count(",")


def _art(n):   # a note's 5th slot as a dict of knobs (a drum stroke is kept as _stroke)
    a = n[4]
    return dict(a) if isinstance(a, dict) else ({} if not a else {"_stroke": a})


def _pending(n): return isinstance(n[4], dict) and bool(n[4].get("_ops"))


def _queue(n, op, v):
    """Leave a pitch op on the note, after the ones already waiting (music.note_list runs them once the pitch resolves)."""
    art = _art(n); ops = []
    for o, x in [*art.get("_ops", []), [op, v]]:
        if ops and ops[-1][0] == o: ops[-1][1] += x
        else: ops.append([o, x])
        if not ops[-1][1]: ops.pop()
    art.pop("_ops", None)
    if ops: art["_ops"] = ops
    n[4] = art or None


def _shift(notes, k):
    out = []
    for n in notes:
        n = list(n)
        if not k: pass
        elif not _pending(n) and all(_rest(t) or (isinstance(t, str) and TOK.match(t.strip())) for t in _toks(n)):
            def one(t):
                if _rest(t): return t
                m = TOK.match(t.strip()); return f"{m.group(1)}{int(m.group(2)) + k}{m.group(3)}"
            n[2] = _map_tok(n[2], one)
        else: _queue(n, "shift", k)
        out.append(n)
    return out


def _semi_ok(t):   # a token a transpose can rewrite: a MIDI number, +k, a note name
    if _isnum(t): return True
    return isinstance(t, str) and bool(SEMI.match(t.strip()) or NOTE_NAME.match(t.strip()) or t.strip().isdigit())


def _transpose(notes, k):
    out = []
    for n in notes:
        n = list(n)
        if not k: pass
        elif not _pending(n) and all(_rest(t) or _semi_ok(t) for t in _toks(n)):
            def one(t):
                if _rest(t): return t
                if _isnum(t): return t + k
                s = t.strip(); m = SEMI.match(s)
                if m: return f"{int(m.group(1)) + k:+d}{m.group(2)}"
                m = NOTE_NAME.match(s)
                if m: return 12 * (int(m.group(3)) + 1) + PC[m.group(1) + m.group(2)] + k + 12 * _marks(m.group(4))
                return int(s) + k
            n[2] = _map_tok(n[2], one)
        else: _queue(n, "semis", k)
        out.append(n)
    return out


def _octave(notes, k):   # octaves commute with the other pitch ops, so the marks are always rewritten when they can be
    out = []
    for n in notes:
        n = list(n)
        if not k: pass
        elif all(_rest(t) or _isnum(t) or (isinstance(t, str) and t.strip() != "chord") for t in _toks(n)):
            n[2] = _map_tok(n[2], lambda t: t if _rest(t) else t + 12 * k if _isnum(t) else t.strip() + ("'" * k if k > 0 else "," * -k))
        else: _queue(n, "semis", 12 * k)
        out.append(n)
    return out


def _parts(t):
    """A token's (kind, number, octave marks) for invert, or None. d, s, c keep their marks apart (a scale's octave is
    not always 7 steps); semitone and absolute pitches fold them in."""
    if _isnum(t): return ("abs", t, 0)
    if not isinstance(t, str): return None
    s = t.strip(); m = TOK.match(s)
    if m: return (m.group(1), int(m.group(2)), _marks(m.group(3)))
    m = SEMI.match(s)
    if m: return ("semi", int(m.group(1)) + 12 * _marks(m.group(2)), 0)
    m = NOTE_NAME.match(s)
    if m: return ("abs", 12 * (int(m.group(3)) + 1) + PC[m.group(1) + m.group(2)] + 12 * _marks(m.group(4)), 0)
    if s.isdigit(): return ("abs", int(s), 0)
    return None


def _invert(notes, where):
    pivot = {}
    for n in notes:
        for t in _toks(n):
            v = None if _rest(t) else _parts(t)
            if v and v[0] not in pivot: pivot[v[0]] = v[1:]
    out = []
    for n in notes:
        n = list(n)
        def one(t):
            if t is None or _rest(t) or (isinstance(t, str) and t.strip() == "chord"): return t
            v = _parts(t)
            if not v: _err(f"{where}: invert cannot read the pitch {t!r}")
            kind, x, mk = v; px, pm = pivot[kind]; y, ym = 2 * px - x, 2 * pm - mk
            if kind in "dsc": return f"{kind}{y}" + ("'" * ym if ym > 0 else "," * -ym)
            return f"{y:+d}" if kind == "semi" else y
        n[2] = _map_tok(n[2], one)
        out.append(n)
    return out


def _retro(notes, L):
    end = L if L is not None else max(n[0] + n[1] for n in notes)
    return sorted(([round(end - (n[0] + n[1]), 9), n[1], *n[2:]] for n in notes), key=lambda n: n[0])


def _time(notes, f):   # beats and lengths through f, rounded so 12 ÷ 3 lands on beat 4, not 3.9999999999999996
    return [[round(f(n[0]), 9), round(f(n[1]), 9), *n[2:]] for n in notes]


def _rhythm(notes, x, where):
    """Every note x beats long, one after another; or a list of lengths, taken in turn (and cycled): [0.75, 0.25]."""
    if isinstance(x, str) and re.search(r"[\s,]", x.strip()): x = [v for v in re.split(r"[\s,]+", x.strip()) if v]
    if not isinstance(x, (list, tuple)):
        x = _num(x, "rhythm", where)
        if x <= 0: _err(f"{where}: rhythm needs a length > 0")
        return [[round(i * x, 9), x, *n[2:]] for i, n in enumerate(notes)]
    xs = [_num(v, "rhythm", where) for v in x]
    if not xs or min(xs) <= 0: _err(f"{where}: rhythm needs lengths > 0, not {x!r}")
    out, t = [], 0.0
    for i, n in enumerate(notes):
        out.append([round(t, 9), xs[i % len(xs)], *n[2:]]); t += xs[i % len(xs)]
    return out


def _fragment(notes, op, arg, where):
    n = len(notes)
    if op == "take":
        k = _int(arg, "take", where, 1)
        if k > n: _err(f"{where}: take {k}: the motif has {n} notes")
        lo, hi = 0, k
    elif op == "drop":
        k = _int(arg, "drop", where, 0)
        if k >= n: _err(f"{where}: drop {k} leaves nothing: the motif has {n} notes")
        lo, hi = k, n
    else:
        if isinstance(arg, (list, tuple)) and len(arg) == 2: a, b = arg
        elif isinstance(arg, str) and "-" in arg.strip()[1:]: a, b = arg.strip().split("-", 1)
        else: a = b = arg
        a, b = _int(a, "slice", where, 1), _int(b, "slice", where, 1)
        if b < a or b > n: _err(f"{where}: slice {a}-{b}: the motif has {n} notes, counted from 1")
        lo, hi = a - 1, b
    frag = notes[lo:hi]; b0 = frag[0][0]
    return [[round(x[0] - b0, 9), *x[1:]] for x in frag]


def _vel(notes, spec, where):
    if isinstance(spec, str) and spec.strip()[:1] in "*+-": op, x = spec.strip()[0], _num(spec.strip()[1:], "vel", where)
    else: op, x = "=", _num(spec, "vel", where)
    out = []
    for n in notes:
        n = list(n); v = 0.8 if n[3] is None else float(n[3])
        v = x if op == "=" else v * x if op == "*" else v + x if op == "+" else v - x
        n[3] = round(max(0.0, v), 6); out.append(n)
    return out


def _step(notes, L, op, arg, where):
    """One op → (notes, the motif's length afterwards, or None once it no longer applies)."""
    if op in ("invert", "retro"):
        if arg is False or arg == "false": return notes, L
        if arg not in (None, True, "", "true"): _err(f"{where}: {op} takes no value (or true / false), not {arg!r}")
        return (_invert(notes, where) if op == "invert" else _retro(notes, L)), L
    if op not in EXAMPLE:
        hint = " (vel, vels and repeat are keys of the call, not transforms)" if op in CALL_KEYS else ""
        _err(f"{where}: unknown transform {op!r}{hint}; use {' '.join(['invert', 'retro', *EXAMPLE])}")
    if arg is None or arg is True or arg == "": _err(f"{where}: {op} needs a value, e.g. \"{op}:{EXAMPLE[op]}\"")
    if op == "shift": return _shift(notes, _int(arg, "shift", where)), L
    if op == "transpose": return _transpose(notes, _int(arg, "transpose", where)), L
    if op == "octave": return _octave(notes, _int(arg, "octave", where)), L
    if op in ("augment", "diminish", "legato"):
        k = _num(arg, op, where)
        if k <= 0: _err(f"{where}: {op} needs a number > 0, not {arg!r}")
        if op == "legato": return [[n[0], round(n[1] * k, 9), *n[2:]] for n in notes], L
        f = (lambda x: x * k) if op == "augment" else (lambda x: x / k)
        return _time(notes, f), (None if L is None else f(L))
    if op == "rhythm": return _rhythm(notes, arg, where), None
    if op == "mode":
        if not isinstance(arg, str) or not arg.strip(): _err(f"{where}: mode needs a scale name, e.g. \"mode:dorian\"")
        out = []
        for n in notes:
            n = list(n); art = _art(n); art["_scale"] = arg.strip(); n[4] = art; out.append(n)
        return out, L
    return _fragment(notes, op, arg, where), None


def call(c, motifs, where, stack=()):
    """One motif call → plain notes [[beat, beats, pitch, vel, art], …]."""
    bad = set(c) - CALL_KEYS
    if bad: _err(f"{where}: unknown key(s) {sorted(bad)} in a motif call; use {', '.join(sorted(CALL_KEYS))}")
    name = c["motif"]; w = f"{where} (motif call {name!r})"
    raw, L = motif_notes(motifs, name, where, stack)
    notes = [list(n) + [None] * (5 - len(n)) for n in raw]
    for key in FRAG:
        if key in c: notes, L = _step(notes, L, key, c[key], w)
    tr = c.get("transform", [])
    for s in (tr if isinstance(tr, list) else [tr]):
        op, arg = _parse(s, w); notes, L = _step(notes, L, op, arg, w)
    for key in SHORT:
        if key in c: notes, L = _step(notes, L, key, c[key], w)
    if "vels" in c:
        vs = c["vels"]
        if not isinstance(vs, list) or len(vs) != len(notes):
            _err(f"{w}: \"vels\" needs one velocity per note ({len(notes)}), not {vs!r}")
        notes = [[*n[:3], _num(v, "vels", w), n[4]] for n, v in zip(notes, vs)]
    if "vel" in c: notes = _vel(notes, c["vel"], w)
    reps = _int(c.get("repeat", 1), "repeat", w, 1)
    if "every" in c:
        every = _num(c["every"], "every", w)
        if every < 0: _err(f"{w}: every needs a number of beats ≥ 0")
    else: every = L if L is not None else max(n[0] + n[1] for n in notes)
    sh, tp, at = _int(c.get("shift_each", 0), "shift_each", w), _int(c.get("transpose_each", 0), "transpose_each", w), _num(c.get("at", 0), "at", w)
    ve = c.get("vel_each")
    if ve is not None:   # "+0.04" (also a plain number), "-0.04" or "*1.1", applied once more on every copy
        vop, vx = (ve.strip()[0], _num(ve.strip()[1:], "vel_each", w)) if isinstance(ve, str) and ve.strip()[:1] in "*+-" else ("+", _num(ve, "vel_each", w))
    out = []
    for r in range(reps):
        ns = notes
        if r and sh: ns = _shift(ns, r * sh)
        if r and tp: ns = _transpose(ns, r * tp)
        if r and ve is not None: ns = _vel(ns, f"*{vx ** r}" if vop == "*" else f"{vop}{vx * r}", w)
        off = at + r * every
        out += [[round(n[0] + off, 9) if off else n[0], n[1], *n[2:]] for n in ns]
    for n in out:   # drop the empty slots this call filled in: [0, 1, "d1", None, None] → [0, 1, "d1"]
        while len(n) > 2 and n[-1] is None: n.pop()
    return out
