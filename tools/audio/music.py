"""Code-composed soundtrack: a JSON score → a deterministic WAV + an exact beat/section map.

usage (via bin/vh music): python tools/audio/music.py <score.json> <out.wav>      (writes <out>.beats.json too)
       python tools/audio/music.py --example > score.json                       (print a starter score)

Why: "even the soundtrack is code". The score is versioned with the film, sections line up with shots,
and because we composed it, the beat grid is exact — no beat detection needed for cuts and hits.

Score fields
  bpm, key ("C".."B", optional "#"/"b"), mode ("minor"|"major"), seed, master_db (peak, default -1)
  sections: [{ "name", "bars", "chords": ["i","VI","III","VII"] (roman, cycled per bar),
               "layers": subset of kick clap hats bass pad arp lead,
               "energy": 0..1 (layer gain + filter brightness),
               "riser": true  (noise+tone rise over this section, into the next),
               "impact": true (boom on this section's first downbeat),
               "fill": true   (drop the kick on the last beat for a breath) }]
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

def render(score):
    rng = np.random.default_rng(score.get("seed", 7))
    bpm = float(score["bpm"]); beat = 60.0 / bpm; bar = 4 * beat
    root = NOTE[score.get("key", "C")]; mode = score.get("mode", "minor")
    total_bars = sum(s["bars"] for s in score["sections"])
    out = np.zeros(int((total_bars * bar + 3.0) * SR))
    sidechain = np.ones_like(out)
    beats, downbeats, secs, hits = [], [], [], []
    K = kick(); t0 = 0.0
    for s in score["sections"]:
        e = float(s.get("energy", 0.7)); L = set(s.get("layers", [])); chords = s.get("chords", ["i"])
        secs.append({"name": s["name"], "start": round(t0, 3), "end": round(t0 + s["bars"] * bar, 3), "bars": s["bars"]})
        if s.get("impact"):
            add(out, impact(rng) * (0.6 + 0.4 * e), t0); hits.append({"t": round(t0, 3), "what": f"impact:{s['name']}"})
        for b in range(s["bars"]):
            tb = t0 + b * bar; notes = chord_notes(root, mode, chords[b % len(chords)])
            downbeats.append(round(tb, 3))
            if "pad" in L: add(out, pad(notes, bar + 0.4, e), tb)
            for q in range(4):
                tq = tb + q * beat; beats.append(round(tq, 3))
                last_beat = s.get("fill") and b == s["bars"] - 1 and q == 3
                if "kick" in L and not last_beat:
                    add(out, K * (0.7 + 0.3 * e), tq)
                    i = int(tq * SR); m = min(len(out), i + int(0.22 * SR))
                    sidechain[i:m] = np.minimum(sidechain[i:m], 0.35 + 0.65 * np.linspace(0, 1, m - i) ** 0.7)
                if "clap" in L and q in (1, 3): add(out, clap(rng) * e, tq)
                if "hats" in L:
                    add(out, hat(rng) * e, tq + beat / 2)
                    if e > 0.8: add(out, hat(rng) * 0.5 * e, tq + beat / 4); add(out, hat(rng) * 0.5 * e, tq + 3 * beat / 4)
                if "bass" in L:
                    for h in (0, 0.5):
                        add(out, bass(mtof(notes[0] - 24), beat / 2 * 0.9) * (0.6 + 0.4 * e), tq + h * beat)
            if "arp" in L:
                seq = notes + [notes[0] + 12]
                for k16 in range(16):
                    add(out, pluck(mtof(seq[k16 % 4] + 12), beat / 2, e) * (0.5 + 0.5 * e), tb + k16 * beat / 4)
            if "lead" in L and b % 2 == 0:
                phrase = [notes[2] + 12, notes[1] + 12, notes[0] + 12, notes[1] + 12]
                for k, m in enumerate(phrase): add(out, lead(mtof(m), beat * 0.95, e), tb + k * beat * 2)
        if s.get("riser"):
            dur = s["bars"] * bar; add(out, riser(dur, rng), t0)
            hits.append({"t": round(t0 + dur, 3), "what": f"riser-peak:{s['name']}"})
        t0 += s["bars"] * bar
    # pump everything except kick/impact would need stems; a gentle global pump reads as sidechain
    out *= 0.6 + 0.4 * sidechain
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
    return mix, beatmap

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        print(json.dumps(EXAMPLE, indent=2)); return
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
