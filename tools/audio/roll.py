"""Pictures of a score for `bin/vh music … --roll`: judge the melody and the dynamics by eye, since nobody here can
listen for you.

<out>.roll/overview.png   every part on one time axis: its notes (a small piano roll) and its loudness (dBFS line),
                          under the sections and chords; at the bottom the mix's loudness against the score's "energy"
<out>.roll/NN-<part>.png   one per part: a piano roll in rows of 8 bars (only the rows it plays in), note names on the
                          left, chords and sections above each bar, velocity as colour depth, loudness under each row

Loudness is the RMS of the part's own stem in 50 ms windows, scaled to the file (small-signal: the master's soft clip
is left out), so the lines read in dBFS. Deterministic: the same score gives the same PNG bytes.
"""
import math, os, re, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import vhdraw as V

SR, HOP = 48000, 2400   # 50 ms windows
NAMES_SHARP = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NAMES_FLAT = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]
PART = [(43, 92, 158), (200, 120, 30), (58, 138, 116), (122, 85, 165), (46, 143, 163), (170, 64, 120), (110, 128, 56), (150, 110, 60)]
FLOOR = -60.0

class Envelopes(dict):
    """A stems dict for music.render that keeps only each stem's RMS per 50 ms (power averaged over the channels)."""
    def __setitem__(self, k, stem):
        p = np.asarray(stem, dtype=np.float64) ** 2
        p = p.mean(0) if p.ndim == 2 else p
        n = len(p) // HOP
        super().__setitem__(k, np.sqrt(p[:n * HOP].reshape(n, HOP).mean(1)) if n else np.zeros(0))

def envelope(mix):
    p = np.asarray(mix, dtype=np.float64) ** 2
    p = p.mean(1) if p.ndim == 2 else p
    n = len(p) // HOP
    return np.sqrt(p[:n * HOP].reshape(n, HOP).mean(1)) if n else np.zeros(0)

def db(x):
    return np.maximum(FLOOR, 20 * np.log10(np.maximum(x, 1e-9)))

def names_for(score):
    key, mode = str(score.get("key", "C")), str(score.get("mode", "minor"))
    flat = ("b" in key[1:]) or (key in ("F", "Bb", "Eb", "Ab", "Db", "Gb") and mode != "minor") or \
           (key in ("D", "G", "C", "F", "Bb", "Eb") and mode in ("minor", "dorian", "phrygian", "aeolian"))
    return NAMES_FLAT if flat else NAMES_SHARP

def note_name(m, names):
    m = int(round(m)); return f"{names[m % 12]}{m // 12 - 1}"

def chord_name(ch, names):
    """A music.Chord (pc, intervals) → 'Bm', 'G7', 'F#°' …"""
    iv = set(ch.iv)
    if 3 in iv and 6 in iv and 7 not in iv:   # diminished: ° / °7 / ø7 (half-diminished)
        return names[ch.pc] + ("ø7" if 10 in iv else "°7" if 9 in iv else "°")
    if 4 in iv and 8 in iv and 7 not in iv:
        return names[ch.pc] + "+"
    q = "m" if 3 in iv else ("sus4" if 5 in iv and 4 not in iv else "sus2" if 2 in iv and 4 not in iv else "5" if 4 not in iv else "")
    if 11 in iv: q += "maj7"
    elif 10 in iv: q += "7"
    elif 9 in iv: q += "6"
    return names[ch.pc] + q

def bar_chords(cx, score, names):
    """[(bar, [(beat, 'vi Bm'), …])]: the roman symbols as written plus the chord they make in this key."""
    out, k = [], 0
    for s in score["sections"]:
        syms = s.get("chords", ["i"])
        for b in range(s["bars"]):
            B = cx.grid[k]; written = str(syms[b % len(syms)]).split()
            out.append((B, [(pos, f"{w} {chord_name(ch, names)}", chord_name(ch, names)) for (pos, ch), w in zip(B.chords, written)]))
            k += 1
    return out

class Axis:
    def __init__(self, t0, t1, x0, x1):
        self.t0, self.t1, self.x0, self.x1 = t0, t1, x0, x1
    def x(self, t):
        return self.x0 + (t - self.t0) / max(self.t1 - self.t0, 1e-9) * (self.x1 - self.x0)

def smooth(env, k):
    """RMS over k windows (power averaged), same length: a line that shows the swell, not every note."""
    if k <= 1 or not len(env): return env
    p = np.convolve(env ** 2, np.ones(k) / k, mode="same")
    return np.sqrt(p)

def curve(d, ax, env, gain, y0, y1, color, width=2, t0=None, t1=None, k=1):
    """The loudness line (FLOOR..0 dBFS → y1..y0) over [t0, t1]; k: smoothing in 50 ms windows."""
    if env is None or not len(env): return
    t0 = ax.t0 if t0 is None else t0; t1 = ax.t1 if t1 is None else t1
    a, b = max(0, int(t0 * SR / HOP)), min(len(env), int(math.ceil(t1 * SR / HOP)))
    if b - a < 2: return
    v = db(smooth(env, k)[a:b] * gain)
    pts = [(ax.x((a + i + 0.5) * HOP / SR), y1 - (x - FLOOR) / -FLOOR * (y1 - y0)) for i, x in enumerate(v)]
    d.line(pts, fill=color, width=width, joint="curve")

def draw(score, score_path, out_wav, mix, beatmap, stems, notes, info, cx):
    names = names_for(score)
    folder = Path(out_wav).with_suffix(".roll")
    folder.mkdir(parents=True, exist_ok=True)
    for old in list(folder.glob("*.png")): old.unlink()   # parts that left the score
    gain = float(info.get("gain", 1.0)) if info else 1.0
    chords = bar_chords(cx, score, names)
    written = [overview(score, score_path, mix, beatmap, stems, notes, gain, chords, names, folder / "overview.png")]
    for i, (label, n) in enumerate(notes.items()):
        written.append(part_page(score, label, n, stems.get(label), gain, chords, names, i, folder / f"{i + 1:02d}-{re.sub(r'[^A-Za-z0-9_-]+', '-', label)}.png"))
    return [V.shown(p) for p in written]

def header(d, score, score_path, beatmap, W, pad, title):
    dur = beatmap.get("duration", 0)
    V.text(d, (pad, 22), title, V.font(32, bold=True), V.INK)
    sub = (f"{Path(score_path).name} · {score.get('bpm')} bpm · {score.get('key', 'C')} {score.get('mode', 'minor')} · "
           f"{sum(s['bars'] for s in score['sections'])} bars · {dur:g} s" + (f" · fade {beatmap['fade']['start']:g}–{beatmap['fade']['end']:g} s" if beatmap.get("fade") else ""))
    V.text(d, (pad, 66), V.fit(d, sub, V.font(20), W - 2 * pad), V.font(20), V.MUTED)

def overview(score, score_path, mix, beatmap, stems, notes, gain, chords, names, path):
    W, pad, lab = 2000, 32, 230
    T1 = float(beatmap.get("duration") or 1)
    ax = Axis(0.0, T1, pad + lab, W - pad)
    lane_h = 92
    parts = list(notes.items())
    H = 110 + 40 + 36 + 30 + len(parts) * (lane_h + 14) + 150 + 60
    img = Image.new("RGB", (W, H), V.BG); d = ImageDraw.Draw(img)
    header(d, score, score_path, beatmap, W, pad, "配乐总览 · 音符与响度" if any(V.has_cjk(s["name"]) for s in score["sections"]) else "Score overview · notes and loudness")
    y = 110
    # sections with their energy, bar lines
    for i, s in enumerate(beatmap.get("sections", [])):
        xa, xb = ax.x(s["start"]), ax.x(min(s["end"], T1))
        d.rectangle([xa, y, xb - 1, y + 34], fill=V.mix(V.seg_color(i), (255, 255, 255), 0.55))
        sec = next((x for x in score["sections"] if x["name"] == s["name"]), {})
        lab_s = s["name"] + (f"  e {sec['energy']:g}" if "energy" in sec else "")
        V.text(d, (xa + 6, y + 17), V.fit(d, lab_s, V.font(18, bold=True), xb - xa - 8), V.font(18, bold=True), V.INK, "lm")
    y += 40
    fc = V.font(15)
    last_x = -1e9
    for B, cs in chords:   # chord names, skipped where they would collide
        for pos, _, name in cs:
            t = B.tb + pos * cx_beat(score)
            if t >= T1: continue
            x = ax.x(t)
            if x - last_x > V.tw(d, name, fc) + 8:
                V.text(d, (x + 2, y + 12), name, fc, V.BLUE, "lm"); last_x = x
    V.text(d, (pad, y + 12), "chords", V.font(18), V.MUTED, "lm")
    y += 36
    grid_top = y
    for b in beatmap.get("downbeats", []):
        x = ax.x(b); d.line([(x, grid_top), (x, H - 110)], fill=V.FAINT, width=1)
    for i, (label, n) in enumerate(parts):
        col = PART[i % len(PART)]
        ly0, ly1 = y, y + lane_h
        d.rectangle([ax.x0, ly0, ax.x1, ly1], outline=V.RULE)
        V.text(d, (pad, ly0 + 22), V.fit(d, label, V.font(20, bold=True), lab - 12), V.font(20, bold=True), col, "lm")
        ev = [e for e in n["events"] if e[2]]
        if ev:
            lo = min(min(e[2]) for e in ev); hi = max(max(e[2]) for e in ev)
            rng = f"{note_name(lo, names)}–{note_name(hi, names)}" if hi > lo else note_name(lo, names)
            V.text(d, (pad, ly0 + 50), f"{n['inst']} · {rng}", V.font(16), V.MUTED, "lm")
            span = max(hi - lo, 11); mid = (hi + lo) / 2; lo2, hi2 = mid - span / 2 - 1, mid + span / 2 + 1
            for t, dur, ps, vel, _ in ev:
                for m in ps:
                    yy = ly1 - 6 - (m - lo2) / (hi2 - lo2) * (lane_h - 12)
                    xa, xb = ax.x(t), max(ax.x(t) + 2, ax.x(t + dur))
                    d.rectangle([xa, yy - 2, xb, yy + 2], fill=V.mix(col, (255, 255, 255), 0.65 - 0.55 * min(1.0, vel)))
        else:
            V.text(d, (pad, ly0 + 50), f"{n['inst']} · {'texture' if n['kind'] == 'texture' else 'hits'}", V.font(16), V.MUTED, "lm")
            for t, dur, ps, vel, _ in n["events"]:   # drums: a tick per hit, taller = harder
                x = ax.x(t); h = 8 + 30 * min(1.0, vel)
                d.line([(x, ly1 - 6), (x, ly1 - 6 - h)], fill=V.mix(col, (255, 255, 255), 0.3), width=1)
        curve(d, ax, stems.get(label), gain, ly0 + 4, ly1 - 4, (70, 70, 78), 2, k=8)   # 0.4 s: the swell, not each note
        y += lane_h + 14
    # the mix: loudness against the score's energy
    my0, my1 = y + 10, y + 140
    d.rectangle([ax.x0, my0, ax.x1, my1], outline=V.RULE)
    V.text(d, (pad, my0 + 24), "mix", V.font(20, bold=True), V.INK, "lm")
    V.text(d, (pad, my0 + 52), "RMS dBFS (line)", V.font(15), V.MUTED, "lm")
    V.text(d, (pad, my0 + 74), "score energy (dashed)", V.font(15), V.MUTED, "lm")
    for db_mark in (-12, -24, -36, -48):
        yy = my1 - (db_mark - FLOOR) / -FLOOR * (my1 - my0)
        d.line([(ax.x0, yy), (ax.x1, yy)], fill=V.FAINT); V.text(d, (ax.x0 - 6, yy), f"{db_mark}", V.font(13), V.MUTED, "rm")
    curve(d, ax, envelope(mix), 1.0, my0, my1, V.RED, 2, k=8)
    for s in beatmap.get("sections", []):
        sec = next((x for x in score["sections"] if x["name"] == s["name"]), {})
        if "energy" in sec:
            yy = my1 - float(sec["energy"]) * (my1 - my0)
            V.dashed_hline(d, ax.x(s["start"]), ax.x(min(s["end"], T1)), yy, V.BLUE, 6, 5, 2)
    if beatmap.get("fade"):
        xa = ax.x(beatmap["fade"]["start"]); d.polygon([(xa, my0), (ax.x(beatmap["fade"]["end"]), my1), (ax.x(beatmap["fade"]["end"]), my0)], outline=V.MUTED)
    # time axis
    step = next(s for s in (1, 2, 5, 10, 15, 30, 60) if T1 / s <= 20)
    t = 0.0
    while t <= T1 + 1e-9:
        x = ax.x(t); V.text(d, (x, my1 + 10), f"{t:g}", V.font(16), V.MUTED, "ma"); t += step
    V.text(d, (pad, H - 26), "grey line = the part's loudness over 0.4 s (-60 ... 0 dBFS, lane height); note shade = velocity; parts: "
           + ", ".join(f"{k} ({v['inst']})" for k, v in parts), V.font(15), V.MUTED, "ls")
    return V.save(img, path)

def cx_beat(score):
    return 60.0 / float(score["bpm"])

def part_page(score, label, n, env, gain, chords, names, idx, path):
    beat = cx_beat(score); col = PART[idx % len(PART)]
    per = 8
    mine = [B for B, _ in chords if B.sec in n["sections"]] or [B for B, _ in chords]
    runs = []   # consecutive bars it plays in; each run starts a new row, 8 bars a row
    for B in mine:
        if runs and runs[-1][-1].i == B.i - 1: runs[-1].append(B)
        else: runs.append([B])
    rows = [r[i:i + per] for r in runs for i in range(0, len(r), per)]
    ev = n["events"]
    pitched = [e for e in ev if e[2]]
    W, pad, lab = 2000, 32, 90
    if pitched:
        lo = int(math.floor(min(min(e[2]) for e in pitched))) - 2; hi = int(math.ceil(max(max(e[2]) for e in pitched))) + 2
        if hi - lo < 14: lo -= (14 - (hi - lo)) // 2; hi = lo + 14
    else:
        lo, hi = 0, 1
    semi = 14 if pitched else 0
    roll_h = (hi - lo) * semi if pitched else 70
    row_h = 40 + roll_h + 70 + 36
    H = 110 + len(rows) * row_h + 50
    img = Image.new("RGB", (W, H), V.BG); d = ImageDraw.Draw(img)
    rng = f" · {note_name(lo + 2, names)}–{note_name(hi - 2, names)}" if pitched else ""
    V.text(d, (pad, 22), f"{label} · {n['inst']}", V.font(32, bold=True), col)
    V.text(d, (pad, 66), f"{len(ev)} notes{rng} · plays in: {', '.join(n['sections'])} · {score.get('bpm')} bpm, "
           f"{score.get('key', 'C')} {score.get('mode', 'minor')} · rows of {per} bars", V.font(20), V.MUTED)
    y = 110
    chord_of = {B.i: cs for B, cs in chords}
    for r in rows:
        t0 = r[0].tb; t1 = r[-1].tb + r[-1].nb * beat
        ax = Axis(t0, t0 + per * max(B.nb for B in r) * beat, pad + lab, W - pad)   # a short last row keeps the bar width
        # chords and sections above the bars
        prev_sec = None
        for B in r:
            x = ax.x(B.tb)
            if B.sec != prev_sec:
                V.text(d, (x + 2, y + 2), B.sec, V.font(17, bold=True), V.INK); prev_sec = B.sec
            V.text(d, (x + 2, y + 22), f"{B.i + 1}", V.font(13), V.MUTED)
            for pos, name, _ in chord_of.get(B.i, []):
                V.text(d, (ax.x(B.tb + pos * beat) + 26, y + 22), name, V.font(15), V.BLUE)
        ry0, ry1 = y + 40, y + 40 + roll_h
        if pitched:
            for m in range(lo, hi):
                yy0 = ry1 - (m - lo + 1) * semi
                if m % 12 in (1, 3, 6, 8, 10):
                    d.rectangle([ax.x0, yy0, ax.x(t1), yy0 + semi], fill=(236, 233, 225))
                if m % 12 == 0 or any(abs(p - m) < 0.5 for e in pitched for p in e[2] if t0 - 1e-6 <= e[0] < t1):
                    V.text(d, (ax.x0 - 8, yy0 + semi / 2), note_name(m, names), V.font(12), V.MUTED if m % 12 else V.INK, "rm")
        d.rectangle([ax.x0, ry0, ax.x(t1), ry1], outline=V.RULE)
        for B in r:   # bar and beat lines
            x = ax.x(B.tb); d.line([(x, ry0), (x, ry1)], fill=V.RULE, width=2)
            for q in range(1, B.nb):
                xq = ax.x(B.tb + q * beat); d.line([(xq, ry0), (xq, ry1)], fill=V.FAINT, width=1)
        for t, dur, ps, vel, _ in ev:
            if not t0 - 1e-6 <= t < t1 - 1e-6: continue
            xa, xb = ax.x(t), max(ax.x(t) + 3, ax.x(min(t + dur, t1)) - 1)
            shade = V.mix(col, (255, 255, 255), 0.7 - 0.6 * min(1.0, vel))
            if pitched and ps:
                for m in ps:
                    yy = ry1 - (m - lo + 1) * semi
                    d.rounded_rectangle([xa, yy + 1, xb, yy + semi - 1], radius=3, fill=shade, outline=col)
            else:   # drums: a bar per hit, taller = harder
                h = 10 + (roll_h - 16) * min(1.0, vel)
                d.rectangle([xa, ry1 - h, xa + 3, ry1 - 2], fill=shade)
        # loudness under the row
        ly0, ly1 = ry1 + 12, ry1 + 70
        d.rectangle([ax.x0, ly0, ax.x(t1), ly1], outline=V.RULE)
        for dbm in (-20, -40):
            yy = ly1 - (dbm - FLOOR) / -FLOOR * (ly1 - ly0); d.line([(ax.x0, yy), (ax.x(t1), yy)], fill=V.FAINT)
            V.text(d, (ax.x0 - 8, yy), f"{dbm}", V.font(12), V.MUTED, "rm")
        curve(d, ax, env, gain, ly0, ly1, V.INK, 2, t0, t1, k=4)
        V.text(d, (ax.x(t1), ly1 + 4), f"{t0:.1f}–{t1:.1f} s", V.font(14), V.MUTED, "ra")
        y += row_h
    V.text(d, (pad, H - 22), "shade = velocity · under each row: this part's loudness over 0.2 s, -60 ... 0 dBFS · bar numbers are the score's",
           V.font(15), V.MUTED, "ls")
    return V.save(img, path)
