"""Code-composed soundtrack: a JSON score → a deterministic WAV + an exact beat/section map.

usage (via bin/vh music): python tools/audio/music.py <score.json> <out.wav>      (writes <out>.beats.json too)
       python tools/audio/music.py --example > score.json                       (print a starter score)
       python tools/audio/music.py --example zh > score.json                    (Chinese colour: bell zheng dizi taiko)

Why: "even the soundtrack is code". The score is versioned with the film, sections line up with shots,
and because we composed it, the beat grid is exact — no beat detection needed for cuts and hits.

Score fields
  bpm, key ("C".."B", optional "#"/"b"), mode ("minor"|"major"), seed, master_db (peak, default -1)
  meters (optional): {"11": 6} makes bar 11 (1-based, counted over the whole score) a 6/4 bar; default 4/4.
    With meters the beat map also carries "bars": [[bar, start_s, beats_in_bar], …] so visuals use one bar(k).
  sections: [{ "name", "bars", "chords": ["i","VI","III","VII"] (roman, cycled per bar),
               "layers": subset of kick clap hats bass pad arp lead  +  bell zheng dizi taiko (Chinese colour:
                 bianzhong-like bell, Karplus–Strong guzheng, breathy dizi, taiko; melodic ones use the key's
                 pentatonic — minor → 羽 1 b3 4 5 b7, major → 宫 1 2 3 5 6 — and share their own hall reverb),
               "energy": 0..1 (layer gain + filter brightness),
               "riser": true  (noise+tone rise over this section, into the next),
               "impact": true (boom on this section's first downbeat),
               "fill": true   (drop the kick and taiko on the last beat for a breath),
               "bend": true   (zheng: every 2nd bar ends on a 按弦上滑 press-up note) }]
Beat map (<out>.beats.json): {"bpm","offset":0,"beats":[…],"downbeats":[…],
  "sections":[{"name","start","end","bars"}], "hits":[{"t","what"}]}  — engines read it for cuts and punches.
Timbres are simple subtractive/percussive synthesis (numpy + scipy); ~1–3 s to render a minute on Apple Silicon.
"""
import json, sys, wave
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve

SR = 48000
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
        "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
DEG = {"i": 0, "ii": 2, "iii": 3, "iv": 5, "v": 7, "vi": 8, "vii": 10}          # natural minor
DEG_MAJ = {"i": 0, "ii": 2, "iii": 4, "iv": 5, "v": 7, "vi": 9, "vii": 11}

EXAMPLE = {
    "bpm": 112, "key": "F", "mode": "minor", "seed": 7,
    "sections": [
        {"name": "intro", "bars": 4, "chords": ["i", "VI", "III", "VII"], "layers": ["pad", "arp"], "energy": 0.35},
        {"name": "build", "bars": 4, "chords": ["i", "VI", "III", "VII"], "layers": ["pad", "arp", "hats", "bass"], "energy": 0.6, "riser": True, "fill": True},
        {"name": "drop", "bars": 8, "chords": ["i", "VI", "III", "VII"], "layers": ["kick", "clap", "hats", "bass", "pad", "arp", "lead"], "energy": 1.0, "impact": True},
        {"name": "outro", "bars": 4, "chords": ["VI", "VII", "i", "i"], "layers": ["pad", "arp"], "energy": 0.3},
    ],
}
EXAMPLE_ZH = {   # D 羽 pentatonic (D F G A C), ~57 s
    "bpm": 84, "key": "D", "mode": "minor", "seed": 12,
    "sections": [
        {"name": "dawn", "bars": 4, "chords": ["i", "i", "VI", "VII"], "layers": ["bell", "pad"], "energy": 0.3},
        {"name": "theme", "bars": 4, "chords": ["i", "VII", "VI", "VII"], "layers": ["zheng", "dizi", "pad", "bell"], "energy": 0.5, "bend": True},
        {"name": "drums", "bars": 4, "chords": ["i", "VI", "VII", "i"], "layers": ["taiko", "zheng", "bass", "pad"], "energy": 0.8, "riser": True, "fill": True},
        {"name": "climax", "bars": 4, "chords": ["i", "VII", "VI", "VII"], "layers": ["taiko", "bell", "zheng", "dizi", "bass", "pad"], "energy": 1.0, "impact": True, "bend": True},
        {"name": "coda", "bars": 4, "chords": ["VI", "VII", "i", "i"], "layers": ["bell", "dizi", "pad"], "energy": 0.3},
    ],
}

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

def chord_notes(root_pc, mode, roman, octave=4):
    r = roman.strip()
    minor_quality = r.islower()
    deg = (DEG if mode == "minor" else DEG_MAJ)[r.lower()]
    base = 12 * (octave + 1) + root_pc + deg
    third = 3 if minor_quality else 4
    return [base, base + third, base + 7]

def env(n, a, d, sustain=0.0, r=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4))
    decay = sustain + (1 - sustain) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    e = e * np.where(t > a, decay, 1.0)
    if r > 0:
        e *= np.clip((n / SR - t) / r, 0, 1)
    return e

def lp(x, fc, order=2):
    b, a = butter(order, min(fc, SR * 0.45) / (SR / 2), "low"); return lfilter(b, a, x)

def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "high"); return lfilter(b, a, x)

def saw(f, n, phase=0.0):
    t = np.arange(n) / SR; return 2 * ((f * t + phase) % 1.0) - 1

def add(buf, x, at):
    i = int(round(at * SR)); j = min(len(buf), i + len(x))
    if i < len(buf): buf[i:j] += x[: j - i]

# ---------- instruments ----------
def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR; f = 45 + 110 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16) * 0.95

def clap(rng):
    n = int(0.25 * SR); x = hp(rng.standard_normal(n), 900) * env(n, 0.002, 0.07)
    for k in (0.012, 0.024): x[int(k * SR):] += 0.6 * x[: n - int(k * SR)]
    return lp(x, 7000) * 0.35

def hat(rng, open_=False):
    n = int((0.18 if open_ else 0.05) * SR); return hp(rng.standard_normal(n), 7000) * env(n, 0.001, 0.06 if open_ else 0.015) * 0.18

def pluck(freq, dur, bright):
    n = int(dur * SR); x = saw(freq, n) * 0.6 + saw(freq * 1.003, n) * 0.4
    return lp(x, 900 + 4500 * bright) * env(n, 0.003, 0.18) * 0.22

def pad(notes, dur, bright):
    n = int(dur * SR); x = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0.0, 0.08):
            x += saw(mtof(m + det), n, phase=(m % 7) / 7)
    return lp(x / (3 * len(notes)), 500 + 2200 * bright) * env(n, 0.35, 10, 1.0, 0.4) * 0.5

def bass(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) * 0.8 + lp(saw(freq, n), 400) * 0.35
    return x * env(n, 0.005, 0.25, 0.4, 0.03) * 0.45

def lead(freq, dur, bright):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.2, 0, 1)
    x = saw(freq, n) * 0.5 + np.sign(np.sin(2 * np.pi * freq * vib * t)) * 0.25
    return lp(x, 1800 + 3000 * bright) * env(n, 0.02, 0.5, 0.6, 0.08) * 0.16

def riser(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; k = t / dur
    noise = hp(rng.standard_normal(n), 300) * k ** 2 * 0.25
    tone = np.sin(2 * np.pi * np.cumsum(200 + 1600 * k ** 2) / SR) * k ** 3 * 0.12
    return lp(noise, 12000) + tone

def impact(rng):
    n = int(2.2 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.9) * 0.9
    return boom + lp(rng.standard_normal(n), 1500) * np.exp(-t / 0.35) * 0.3

# ---------- Chinese colour: bell zheng dizi taiko (each note has its own seeded rng, so adding a layer never changes the others) ----------
BELL = [(0.5, .25, 1.4), (1.0, 1.0, 1.0), (1.19, .6, .75), (2.0, .3, .5), (2.76, .35, .32), (3.9, .2, .2), (5.4, .12, .12), (6.9, .07, .08)]

def penta(root_pc, mode):  # pentatonic MIDI notes: minor → 羽 (1 b3 4 5 b7), major → 宫 (1 2 3 5 6)
    # up to MIDI 111: dizi grace notes sit ~2 octaves above the chord's scale note, so B minor or high chords need the headroom
    return [m for m in range(36, 112) if (m - root_pc) % 12 in ((0, 3, 5, 7, 10) if mode == "minor" else (0, 2, 4, 7, 9))]

def near(scale, m): return min(range(len(scale)), key=lambda i: (abs(scale[i] - m), -scale[i]))

def bell(freq, rng, T=3.2):  # bianzhong-like: inharmonic partials (1.19 = the 侧鼓音 a minor third up), slow beating, long decay
    n = int(6.0 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for r, a, d in BELL:
        if freq * r < SR * 0.45:
            x += a * (np.sin(2 * np.pi * freq * r * t + rng.uniform(0, 2 * np.pi)) + 0.35 * np.sin(2 * np.pi * freq * r * 1.0016 * t)) * np.exp(-t / (T * d))
    x += lp(hp(rng.standard_normal(n), 700), 5000) * np.exp(-t / 0.006) * 0.5          # mallet
    return x * np.minimum(1, t / 0.0015) * np.clip((6.0 - t) / 0.5, 0, 1) * 0.18

def ks(f, n, t60, bright, rng):
    """Karplus–Strong string; f in Hz, scalar or per-sample (a bend). Vectorised one period-block at a time."""
    f = np.broadcast_to(np.asarray(f, float), (n,)); D = SR / f - 0.5; M = D.astype(int); q = D - M   # loop = M + q + ½
    rho = 10 ** (-3 / (t60 * f)); P = int(M.max()) + 3; N0 = int(SR / f[0]); c = 0.6 - 0.45 * bright
    x = lfilter([1 - c], [1, -c], rng.uniform(-1, 1, N0)); k = int(N0 * 0.15)
    x = x - np.concatenate([np.zeros(k), x[:-k]]); y = np.zeros(n + P); y[P:P + N0] = x - x.mean()   # pluck near the bridge
    for s in range(0, n, int(M.min())):
        e = min(n, s + int(M.min())); j = np.arange(s, e) - M[s:e] + P
        y[P + s:P + e] += rho[s:e] * 0.5 * ((1 - q[s:e]) * y[j] + y[j - 1] + q[s:e] * y[j - 2])
    return y[P:]

def zheng(f, dur, bright, rng):  # guzheng pluck; f may be a per-sample curve (按弦上滑)
    n = int(dur * SR); f0 = float(np.asarray(f).flat[0]); t60 = float(np.clip(2.6 * (262 / f0) ** 0.5, 0.8, 3.5))
    return lp(ks(f, n, t60, bright, rng), 2500 + 5000 * bright) * np.clip((dur - np.arange(n) / SR) / 0.05, 0, 1) * 0.64

def press(f0, semis, n, at=0.12, over=0.18):  # 按弦上滑: smooth press up by `semis` after the pluck, then a little 揉弦
    t = np.arange(n) / SR; u = np.clip((t - at) / over, 0, 1); u = u * u * (3 - 2 * u)
    return f0 * 2 ** ((semis * u + 0.12 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - at - over) / 0.2, 0, 1)) / 12)

def dizi(freq, dur, bright, rng, grace=None):  # bamboo flute: sine + triangle, band-passed breath, delayed vibrato, 倚音 grace
    n = int(dur * SR); t = np.arange(n) / SR
    fv = freq * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.3) / 0.4, 0, 1)) * (1 - 0.015 * np.exp(-t / 0.05))
    if grace: fv = np.where(t < 0.07, grace, fv)
    ph = 2 * np.pi * np.cumsum(fv) / SR; nz = rng.standard_normal(n)
    tone = 0.7 * np.sin(ph) + 0.25 * (2 / np.pi) * np.arcsin(np.sin(ph)) + 0.08 * np.sin(2 * ph)
    breath = lp(hp(nz, 1200), 6000) * (0.10 + 0.2 * np.exp(-t / 0.07)) + lp(hp(nz, freq * 0.8), freq * 1.25) * 0.6
    return lp(tone + breath, 2500 + 5000 * bright) * env(n, 0.06, 0.4, 0.85, 0.1) * 0.18

def taiko(rng, big=True):  # big drum: pitch-dropping sine + skin noise + stick
    n = int(1.3 * SR); t = np.arange(n) / SR; f0 = 55 if big else 85
    body = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.9 * np.exp(-t / 0.04))) / SR) * np.exp(-t / (0.55 if big else 0.3))
    skin = lp(hp(rng.standard_normal(n), 90), 700) * np.exp(-t / 0.08) * 0.7
    return (body + skin + hp(rng.standard_normal(n), 1500) * np.exp(-t / 0.003) * 0.3) * np.minimum(1, t / 0.001) * 0.6

ZHENG = [0, 1, 2, 4, 3, 2, 1, 2]                      # 8th-note pentatonic steps above the chord's scale note (cycled)
DIZI = [[(0, 1.5, 2), (1.5, 0.5, 3), (2, 2, 4), (4, 1, 3), (5, 1, 2), (6, 2, 0)],     # 2-bar phrases: (beat, beats, step)
        [(0, 1, 4), (1, 1, 5), (2, 1.5, 4), (3.5, 0.5, 3), (4, 3, 2), (7, 1, 1)]]
ZH = {"bell": 0.45, "zheng": 0.25, "dizi": 0.3, "taiko": 0.12}   # reverb send per layer (own hall, no kick pumping)

def render(score):
    rng = np.random.default_rng(score.get("seed", 7))
    sub = lambda *k: np.random.default_rng([int(score.get("seed", 7)), *k])   # per-note streams for the new layers
    bpm = float(score["bpm"]); beat = 60.0 / bpm
    meters = {int(k): int(v) for k, v in score.get("meters", {}).items()}   # {"11": 6}: bar 11 (1-based, whole score) is 6/4
    root = NOTE[score.get("key", "C")]; mode = score.get("mode", "minor"); scale = penta(root, mode)
    total_bars = sum(s["bars"] for s in score["sections"])
    out = np.zeros(int((sum(meters.get(k, 4) for k in range(1, total_bars + 1)) * beat + 3.0) * SR))
    sidechain = np.ones_like(out); zh, send = np.zeros_like(out), np.zeros_like(out); cache = {}
    beats, downbeats, secs, hits, bars = [], [], [], [], []
    K = kick(); t0 = 0.0
    def put(layer, x, at): add(zh, x, at); add(send, x * ZH[layer], at)
    for s in score["sections"]:
        e = float(s.get("energy", 0.7)); L = set(s.get("layers", [])); chords = s.get("chords", ["i"])
        nbs = [meters.get(len(bars) + b + 1, 4) for b in range(s["bars"])]; sec = sum(nbs) * beat
        secs.append({"name": s["name"], "start": round(t0, 3), "end": round(t0 + sec, 3), "bars": s["bars"]})
        if s.get("impact"):
            add(out, impact(rng) * (0.6 + 0.4 * e), t0); hits.append({"t": round(t0, 3), "what": f"impact:{s['name']}"})
        for b in range(s["bars"]):
            nb = nbs[b]; tb = t0 + sum(nbs[:b]) * beat; notes = chord_notes(root, mode, chords[b % len(chords)])
            downbeats.append(round(tb, 3)); bars.append([len(bars) + 1, round(tb, 3), nb])
            if "pad" in L: add(out, pad(notes, nb * beat + 0.4, e), tb)
            for q in range(nb):
                tq = tb + q * beat; beats.append(round(tq, 3))
                last_beat = s.get("fill") and b == s["bars"] - 1 and q == nb - 1
                if "kick" in L and not last_beat:
                    add(out, K * (0.7 + 0.3 * e), tq)
                    i = int(tq * SR); m = min(len(out), i + int(0.22 * SR))
                    sidechain[i:m] = np.minimum(sidechain[i:m], 0.35 + 0.65 * np.linspace(0, 1, m - i) ** 0.7)
                if "clap" in L and q % 2 == 1: add(out, clap(rng) * e, tq)
                if "hats" in L:
                    add(out, hat(rng) * e, tq + beat / 2)
                    if e > 0.8: add(out, hat(rng) * 0.5 * e, tq + beat / 4); add(out, hat(rng) * 0.5 * e, tq + 3 * beat / 4)
                if "bass" in L:
                    for h in (0, 0.5):
                        add(out, bass(mtof(notes[0] - 24), beat / 2 * 0.9) * (0.6 + 0.4 * e), tq + h * beat)
                if "taiko" in L and not last_beat:   # big drum every other beat, 8th pickups, a 16th roll into a riser peak
                    if s.get("riser") and b == s["bars"] - 1 and q >= nb - 2:
                        taps = [(r / 4, r == 0 and q % 2 == 0, 0.35 + 0.65 * (q - nb + 2 + r / 4) / 2) for r in range(4)]
                    else:
                        taps = ([(0, True, 1.0)] if q % 2 == 0 else []) + \
                               ([(0.5, False, 0.55)] if (e >= 0.75 and q == nb - 1) or (e >= 0.9 and q == 1) else [])
                    for h, big, g in taps:
                        v = len(beats) % 3; key = ("taiko", big, v)
                        if key not in cache: cache[key] = taiko(sub(4, int(big), v), big)
                        put("taiko", cache[key] * g * (0.6 + 0.4 * e), tq + h * beat)
            if "arp" in L:
                seq = notes + [notes[0] + 12]
                for k16 in range(4 * nb):
                    add(out, pluck(mtof(seq[k16 % 4] + 12), beat / 2, e) * (0.5 + 0.5 * e), tb + k16 * beat / 4)
            if "lead" in L and b % 2 == 0:
                phrase = [notes[2] + 12, notes[1] + 12, notes[0] + 12, notes[1] + 12]
                for k, m in enumerate(phrase): add(out, lead(mtof(m), beat * 0.95, e), tb + k * beat * 2)
            a = near(scale, notes[0])
            if "bell" in L:   # strike the chord's scale note on the downbeat; a higher bell mid-bar when energy is high
                for at, i, g in [(0, a, 1.0)] + ([(nb // 2 * beat, a + 2, 0.45)] if e >= 0.7 and nb >= 3 else []):
                    if ("bell", i) not in cache: cache[("bell", i)] = bell(mtof(scale[i]), sub(2, scale[i]))
                    put("bell", cache[("bell", i)] * g * (0.5 + 0.5 * e), tb + at)
            if "zheng" in L:  # flowing 8ths (quarters when calm); with "bend", every 2nd bar ends on a pressed-up note
                bent = s.get("bend") and b % 2 == 1
                for k8 in range(2 * nb - (2 if bent else 0)):
                    if e < 0.5 and k8 % 2: continue
                    m = scale[a + ZHENG[k8 % 8]]; key = ("zheng", m, k8 % 3)
                    if key not in cache: cache[key] = zheng(mtof(m), 1.8, e, sub(1, m, k8 % 3))
                    put("zheng", cache[key] * (0.55 + 0.45 * e) * (1.0 if k8 % 2 == 0 else 0.8), tb + k8 * beat / 2)
                if bent:
                    lo, hi = scale[a + 1], scale[a + 2]; n = int(2.2 * SR)
                    put("zheng", zheng(press(mtof(lo), hi - lo, n), 2.2, e, sub(5, len(bars))) * (0.8 + 0.5 * e), tb + (nb - 1) * beat)
            if "dizi" in L and b % 2 == 0:   # 2-bar phrases on the scale around the chord, grace notes on long notes
                for at, ln, st in DIZI[(b // 2) % 2]:
                    if e < 0.5 and ln < 1.5: continue
                    m = scale[a + 5 + st]
                    put("dizi", dizi(mtof(m), ln * beat * 0.97, e, sub(3, len(bars), int(at * 2)),
                                     mtof(scale[a + 6 + st]) if ln >= 2 else None) * (0.6 + 0.4 * e), tb + at * beat)
        if s.get("riser"):
            add(out, riser(sec, rng), t0)
            hits.append({"t": round(t0 + sec, 3), "what": f"riser-peak:{s['name']}"})
        t0 += sec
    # pump everything except kick/impact would need stems; a gentle global pump reads as sidechain
    out *= 0.6 + 0.4 * sidechain
    if cache:   # the new layers skip the pump and get their own hall (RT60 ≈ 2.8 s, send high-passed so drums stay dry)
        hn = int(2.8 * SR); hr = sub(9).standard_normal(hn) * np.exp(-np.arange(hn) / SR / 0.41); hr[: int(0.025 * SR)] = 0
        out += zh + fftconvolve(hp(send, 180), lp(hr, 5000) / np.sqrt(np.sum(hr ** 2)))[: len(out)] * 0.7
    ir_n = int(1.6 * SR); ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR / 0.45)
    wet = fftconvolve(lp(out, 6000), ir)[: len(out)] * 0.012
    mix = out + wet
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    peak = np.max(np.abs(mix)) or 1.0
    mix *= 10 ** (score.get("master_db", -1.0) / 20) / peak
    end = int((t0 + 2.5) * SR); mix = mix[:end]
    fade = int(1.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
    beatmap = {"bpm": bpm, "offset": 0.0, "beats": beats, "downbeats": downbeats, "sections": secs, "hits": hits,
               "duration": round(len(mix) / SR, 3)}
    if "meters" in score: beatmap.update(bars=bars, bars_note="[bar number (1-based, whole score), start (s), beats in bar]")
    return mix, beatmap

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        print(json.dumps(EXAMPLE_ZH if sys.argv[2:3] == ["zh"] else EXAMPLE, indent=2)); return
    score = json.load(open(sys.argv[1])); out = sys.argv[2]
    mix, beatmap = render(score)
    with wave.open(out, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    bm = out.rsplit(".", 1)[0] + ".beats.json"
    json.dump(beatmap, open(bm, "w"), indent=2)
    print(f"{out} ({beatmap['duration']}s, {score['bpm']} bpm, {len(beatmap['sections'])} sections) · beat map {bm}")

if __name__ == "__main__":
    main()
