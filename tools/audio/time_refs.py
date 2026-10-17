"""Times written as references, for the sound tools and project scripts (stdlib only).

The film (canvas-film's src/00-core.js) and these tools read the same references, so a sound can hang on what the
picture hangs on instead of on typed seconds:

  12.5                                   film seconds
  "@a2", "@a2:词", "@a2>"                narration line a2 starts, "词" in it is spoken, it ends (any + or - seconds:
                                          "@a2:跟着走-0.3"); the timeline is bin/vh tts's, its times plus lead
  {"$music": [12, 3], "offset": -0.05}   bar 12, beat 3 of bin/vh music's beat map (musicAt(12, 3, -0.05) in the film)
  "@#e2", "@#e2>"                        event e2 of the time map and its end (tools/audio/time_map.py), ± seconds too
  {"$map": 40, "offset": 0}              the first moment the time map's axis reaches 40 (mapAt(40); a date axis takes
                                          "YYYY-MM-DD")

  refs = Refs(timeline="audio/timeline.zh.json", lead=0, music="audio/music.beats.json", timemap="data/time.map.json")
  refs.t("@a2>")  → seconds;  refs.sources → [{"path", "sha256"}] of the files it read

A word is found the way the film finds it: letters only (punctuation, symbols and spaces left out, NFKC, lower case),
each letter timed by the aligned words. tools/audio/test_time_map.py checks the two agree.

events.json (bin/vh sfx place, bin/vh mix … events=, bin/vh qa) is a plain list of {t, sfx, …} with t in seconds, or, to
write t as a reference, the same list under a header naming the files the references read (paths beside events.json):

  {"refs": {"timeline": "timeline.zh.json", "lead": 0, "music": "music.beats.json", "timemap": "../data/time.map.json"},
   "events": [{"id": "hit1", "t": "@#e2", "sfx": "impact"}, {"t": "@a4>", "sfx": "whoosh"}, {"t": 12.5, "sfx": "click"}]}

load_events(path) → (events with t in seconds and what was written kept in "ref", sources, refs). An event may carry an
"id" (letters, digits and _), so a correction (mix keep=, roles) can name it instead of a time or an index.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path

from music_clock import MusicClock, number
from time_map import ID, TimeMap


class RefError(ValueError):
    pass


# JS's \s (and what String.prototype.trim strips): Python's isspace() differs (it takes \x1c–\x1f, not ﻿)
JS_SPACE = frozenset("\t\n\v\f\r       　﻿" + "".join(map(chr, range(0x2000, 0x200b))))
NOT_EOL = r"[^\n\r  ]"   # JS's "." (Python's also takes \r and the two separators)
NUM = r"[+-](?:[0-9]+\.?[0-9]*|\.[0-9]+)"   # JS's \d is ASCII; Python's takes every script's digits
CUE = re.compile(rf"@([A-Za-z0-9_]+)(?:(>)|:({NOT_EOL}+?))?({NUM})?\Z")
MAP_CUE = re.compile(rf"@#([A-Za-z0-9_]+)(>)?({NUM})?\Z")


def js_trim(s):
    a, b = 0, len(s)
    while a < b and s[a] in JS_SPACE: a += 1
    while b > a and s[b - 1] in JS_SPACE: b -= 1
    return s[a:b]


def letters(s):
    """a text's letters: whitespace, punctuation and symbols left out (the script's "，" or "“" are not in the aligned words)"""
    s = unicodedata.normalize("NFKC", str(s))
    return "".join(c for c in s if c not in JS_SPACE and unicodedata.category(c)[0] not in "PS").lower()


def lcs(a, b):
    row = [0] * (len(b) + 1)
    for i in range(len(a) - 1, -1, -1):
        nx = [0] * (len(b) + 1)
        for j in range(len(b) - 1, -1, -1):
            nx[j] = row[j + 1] + 1 if a[i] == b[j] else max(row[j], nx[j + 1])
        row = nx
    return row[0]


class Narration:
    """the lines of bin/vh tts's timeline, in film seconds (lead added), as src/00-core.js's initTimeline reads them"""

    def __init__(self, tl, lead=0):
        self.lines, self.ids, problems = {}, [], []
        segs = tl.get("segments") if isinstance(tl, dict) else None
        for i, s in enumerate(segs if isinstance(segs, list) else []):
            if not isinstance(s, dict) or not s.get("id") or not number(s.get("start")) or not number(s.get("end")):
                problems.append(f"timeline line {i + 1}" + (f" ({s['id']})" if isinstance(s, dict) and s.get("id") else "") + ": no id, start or end"); continue
            if s["id"] in self.lines:
                problems.append(f"timeline line {i + 1}: the id {s['id']} is used twice (a cue on it would mean one of them)"); continue
            raw = s.get("words") or []
            words = [w for w in raw if isinstance(w, dict) and number(w.get("start"))]
            if len(words) < len(raw): problems.append(f"timeline line {s['id']}: {len(raw) - len(words)} word(s) without a start")
            text = next((s[k] for k in ("text", "zh", "en") if s.get(k) is not None), "")
            self.lines[s["id"]] = {"id": s["id"], "a": s["start"] + lead, "b": s["end"] + lead, "text": text,
                                   "words": [{"w": str(w["w"]) if w.get("w") is not None else "", "a": w["start"] + lead,
                                              "b": (w["end"] if number(w.get("end")) else w["start"]) + lead} for w in words]}
            self.ids.append(s["id"])
        if not self.ids and not problems: problems.append("the timeline has no lines (segments)")
        if problems: raise RefError("; ".join(problems[:12]) + (f" … {len(problems) - 12} more" if len(problems) > 12 else ""))

    @staticmethod
    def letter_times(L):
        """when each letter of a line is spoken (src/00-core.js's letterTimes, step for step)"""
        if "map" in L: return L["map"]
        a, hc, ht = list(letters(L["text"])), [], []
        for w in L["words"]:
            cs = list(letters(w["w"]))
            for j, c in enumerate(cs):
                hc.append(c); ht.append(w["a"] + (w["b"] - w["a"]) * j / len(cs))
        n, m = len(a), len(hc)
        D = [[0] * (m + 1) for _ in range(n + 1)]
        for i in range(n - 1, -1, -1):
            for j in range(m - 1, -1, -1):
                D[i][j] = D[i + 1][j + 1] + 1 if a[i] == hc[j] else max(D[i + 1][j], D[i][j + 1])
        anchors, i, j = [(-1, L["a"])], 0, 0
        while i < n and j < m:
            if a[i] == hc[j]: anchors.append((i, ht[j])); i += 1; j += 1
            elif D[i + 1][j] >= D[i][j + 1]: i += 1
            else: j += 1
        anchors.append((n, L["b"]))
        T = [None] * n
        for k in range(len(anchors) - 1):
            (i0, t0), (i1, t1) = anchors[k], anchors[k + 1]
            for q in range(i0 + 1, i1): T[q] = t0 + (t1 - t0) * (q - i0) / (i1 - i0)
            if i1 < n: T[i1] = t1
        L["map"] = T
        return T

    def line(self, id):
        if id in self.lines: return self.lines[id]
        near = [k for _, k in sorted(((lcs(k, id), k) for k in self.ids), key=lambda x: -x[0]) if _ > 0][:3]
        short = ", ".join(self.ids[:12]) + (f" … ({len(self.ids)})" if len(self.ids) > 12 else "")
        raise RefError(f'no narration line "{id}" (the lines: {short}' + (f"; nearest: {', '.join(near)})" if near else ")"))

    def word(self, L, word):
        T, k = letters(L["text"]), letters(word)
        if not k: raise RefError(f'"{word}" has no letters to find')
        i = T.find(k)
        if i < 0: raise RefError(f'line {L["id"]} has no "{word}"; it now reads "{L["text"]}"')
        return self.letter_times(L)[i]

    def cue(self, c):
        m = CUE.match(c)
        if not m:
            raise RefError('not a cue: write "@id" (the line starts), "@id:词" (that word is spoken) or "@id>" (the line ends), with an optional +0.3 or -0.2; ids are letters, digits and _')
        L = self.line(m[1])
        if m[3] is not None and m[4] and letters(m[3] + m[4]) in letters(L["text"]):
            dec = m[4] + ("0" if "." in m[4] else ".0")
            raise RefError(f'"{c}" reads two ways, as line {m[1]} says "{m[3]}{m[4]}": write "@{m[1]}:{m[3]}{m[4]}+0" for that word, or "@{m[1]}:{m[3]}{dec}" for {m[4][1:]} s {"before" if m[4][0] == "-" else "after"} "{m[3]}"')
        return (L["b"] if m[2] else self.word(L, m[3]) if m[3] is not None else L["a"]) + (float(m[4]) if m[4] else 0)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Refs:
    """the files references read: a narration timeline (with the film's lead), a beat map, a time map; each optional"""

    def __init__(self, timeline=None, lead=0, music=None, timemap=None):
        if not number(lead): raise RefError(f"lead {json.dumps(lead)}: seconds, a finite number")
        self.narration = self.music = self.timemap = None
        self.sources, files = [], {}

        def read(path, what):
            p = Path(path)
            if not p.is_file(): raise RefError(f"no {path} ({what})")
            self.sources.append({"path": str(p.resolve()), "sha256": sha256(p)}); files[str(p.resolve())] = self.sources[-1]["sha256"]
            return p
        if timeline is not None:
            p = read(timeline, "the narration timeline")
            try: tl = json.loads(p.read_text(encoding="utf-8"))
            except ValueError as e: raise RefError(f"{timeline}: not JSON ({e})") from None
            try: self.narration = Narration(tl, lead)
            except RefError as e: raise RefError(f"{timeline}: {e}") from None
        if music is not None:
            p = read(music, "the beat map")
            try: self.music = MusicClock.load(p)
            except ValueError as e: raise RefError(f"{music}: {e}") from None
        if timemap is not None:
            p = read(timemap, "the time map")
            try: self.timemap = TimeMap.load(p)
            except ValueError as e: raise RefError(f"{timemap}: {e}") from None
            stale = self.timemap.stale(files)
            if stale: raise RefError(self.timemap.stale_message(stale))

    def t(self, ref):
        """a reference → film seconds (a RefError says why it does not resolve)"""
        if number(ref): return ref
        if isinstance(ref, dict) and "$music" in ref:
            v = ref["$music"]
            if not isinstance(v, list) or len(v) != 2: raise RefError("invalid musicAt reference")
            if self.music is None: raise RefError('no beat map: the refs name no "music" (bin/vh music\'s *.beats.json)')
            try: return self.music.at(*v, ref["offset"] if ref.get("offset") is not None else 0)
            except ValueError as e: raise RefError(str(e)) from None
        if isinstance(ref, dict) and "$map" in ref:
            off = ref["offset"] if ref.get("offset") is not None else 0
            if not number(off): raise RefError("mapAt: offset must be finite seconds")
            return self.map_t(ref["$map"]) + off
        if isinstance(ref, str) and ref[:1] == "@" and not ref.startswith("@@"):
            c = js_trim(ref)
            if c.startswith("@#"):
                m = MAP_CUE.match(c)
                if not m: raise RefError('not an event cue: write "@#id" (the event\'s time) or "@#id>" (its end), with an optional +0.3 or -0.2; ids are letters, digits and _')
                try: return self.need_map().at(m[1], "end" if m[2] else "start") + (float(m[3]) if m[3] else 0)
                except ValueError as e: raise RefError(str(e).removeprefix("time map: ")) from None
            if self.narration is None: raise RefError(f'no narration line "{c[1:].split(":")[0].rstrip(">")}": the refs name no "timeline"')
            return self.narration.cue(c)
        raise RefError(f'not a time: {json.dumps(ref, ensure_ascii=False)} (seconds, or a cue: "@id", "@id:词", "@id>", "@#id", {{"$music": [bar, beat]}}, {{"$map": u}})')

    def need_map(self):
        if self.timemap is None: raise RefError('no time map: the refs name no "timemap"')
        return self.timemap

    def map_t(self, u):
        m = self.need_map()
        try: return m.t(m.day(u) if isinstance(u, str) else u)
        except ValueError as e: raise RefError(str(e).removeprefix("time map: ")) from None


HEADER = ("refs", "events", "note")
REF_KEYS = ("timeline", "lead", "music", "timemap")


def load_events(path):
    """events.json → (events, sources, refs): a plain list as it is (its t must be seconds), or the header form with each
    t resolved (what was written kept in "ref"), the files it read and the Refs that read them (None for a plain list)"""
    try: data = json.loads(Path(path).read_text(encoding="utf-8"))
    except ValueError as e: raise RefError(f"{path}: not JSON ({e})") from None
    if isinstance(data, list):
        for k, e in enumerate(data):
            if isinstance(e, dict) and isinstance(e.get("t"), (str, dict)):
                raise RefError(f"{path}: event {k} ({e.get('sfx')}): t {json.dumps(e['t'], ensure_ascii=False)} is a reference, and a plain list "
                               'takes seconds: put the list under a header naming the files references read, {"refs": {"timeline": …, '
                               '"music": …, "timemap": …}, "events": [ … ]} (tools/audio/time_refs.py)')
        return data, [], None
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        raise RefError(f'{path}: a JSON list of {{"t", "sfx", …}} events, or {{"refs": {{…}}, "events": [ … ]}}')
    bad = [k for k in data if k not in HEADER] + [f"refs.{k}" for k in (data.get("refs") or {}) if k not in REF_KEYS]
    if not isinstance(data.get("refs", {}), dict): bad.append("refs (an object)")
    if bad: raise RefError(f"{path}: unknown key(s) {', '.join(bad)} (the header takes refs: {', '.join(REF_KEYS)}; and events)")
    base, given = Path(path).resolve().parent, data.get("refs") or {}
    at = lambda k: base / given[k] if given.get(k) is not None else None
    refs = Refs(timeline=at("timeline"), lead=given.get("lead", 0), music=at("music"), timemap=at("timemap"))
    out, problems, ids = [], [], set()
    for k, e in enumerate(data["events"]):
        if not isinstance(e, dict) or "t" not in e:
            problems.append(f"event {k}: expected an object with t"); continue
        if "id" in e:
            if not isinstance(e["id"], str) or not ID.fullmatch(e["id"]): problems.append(f"event {k}: id {json.dumps(e['id'], ensure_ascii=False)}: letters, digits and _")
            elif e["id"] in ids: problems.append(f"event {k}: the id {e['id']} is used twice")
            else: ids.add(e["id"])
        if number(e["t"]): out.append(e); continue
        try: out.append(dict(e, t=refs.t(e["t"]), ref=e["t"]))
        except RefError as x: problems.append(f"event {k} ({e.get('sfx')}), t {json.dumps(e['t'], ensure_ascii=False)}: {x}")
    if problems:
        raise RefError(f"{path}: {len(problems)} problem{'s' * (len(problems) != 1)}:\n  " + "\n  ".join(problems[:12]) +
                       (f"\n  … {len(problems) - 12} more" if len(problems) > 12 else ""))
    return out, refs.sources, refs
