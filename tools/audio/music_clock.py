"""Read bin/vh music's bars for project scripts (stdlib only).

MusicClock.load('audio/music.beats.json').at(bar, beat=1, offset=0) gives seconds.
Bar and beat are 1-based; fractional beats are allowed. The map's seconds are
already placed, so its beat-detection `offset` is not added again. This is not a
tempo estimator or a warp. The JS counterpart is canvas-film/src/05-music-clock.js.
"""
import hashlib
import json
import math
from pathlib import Path


def number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


class MusicClock:
    def __init__(self, data):
        def fail(message):
            raise ValueError(f"music clock: {message}")
        if not isinstance(data, dict) or not number(data.get("bpm")) or data["bpm"] <= 0 or not number(data.get("duration")) or data["duration"] <= 0:
            fail("a beat map needs positive bpm and duration")
        if not isinstance(data.get("bars"), list) or not data["bars"]:
            fail("no bars table; regenerate the beat map with bin/vh music (an analysed audio beat map is not a score)")
        self.beat, self.duration = 60 / data["bpm"], data["duration"]
        bars = []
        for i, row in enumerate(data["bars"]):
            if not isinstance(row, list) or len(row) != 3:
                fail(f"bar {i + 1}: expected [number, start, beats]")
            ident, start, beats = row
            if not number(ident) or ident != i + 1 or not number(start) or not 0 <= start < self.duration or not number(beats) or int(beats) != beats or beats < 1:
                fail(f"bar {i + 1}: invalid number, start or beat count")
            if i:
                prev = bars[-1]
                if start <= prev[1] or abs(start - prev[1] - prev[2] * self.beat) > 0.002:
                    fail(f"bar {ident}: start disagrees with the preceding bar and bpm")
            bars.append(tuple(row))
        self.bars = tuple(bars)
        self._notes = None
        if "notes" in data:
            if not isinstance(data["notes"], list):
                fail("notes must be a list")
            notes = []
            for i, n in enumerate(data["notes"]):
                if not isinstance(n, dict) or not number(n.get("t")) or not number(n.get("end")) or n["end"] < n["t"] or not isinstance(n.get("part"), str) or not n["part"]:
                    fail(f"note {i + 1}: expected part, finite t and end >= t")
                notes.append(dict(n))
            self._notes = sorted(notes, key=lambda n: n["t"])
        self.source = None

    @classmethod
    def load(cls, path):
        raw = Path(path).read_bytes()
        clock = cls(json.loads(raw))
        clock.source = {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest()}
        return clock

    def at(self, bar, beat=1, offset=0):
        if not number(bar) or int(bar) != bar or not 1 <= bar <= len(self.bars):
            raise ValueError(f"music clock: no bar {bar} (1–{len(self.bars)})")
        bar = int(bar)
        row = self.bars[bar - 1]
        if not number(beat) or not 1 <= beat <= row[2] + 1:
            raise ValueError(f"music clock: bar {bar} beat {beat} is outside 1–{row[2] + 1} (the last value is the boundary)")
        if not number(offset):
            raise ValueError("music clock: offset must be finite seconds")
        t = (self.bars[bar][1] if beat == row[2] + 1 and bar < len(self.bars) else row[1] + (beat - 1) * self.beat) + offset
        if t < -1e-9 or t > self.duration + 0.001:
            raise ValueError(f"music clock: {t} s is outside the rendered music (0–{self.duration} s)")
        return max(0, min(self.duration, t))

    def notes(self, part):
        if self._notes is None:
            raise ValueError('music clock: no notes table; set "note_map": true on the score part and regenerate the music')
        return [dict(n) for n in self._notes if n["part"] == part]
