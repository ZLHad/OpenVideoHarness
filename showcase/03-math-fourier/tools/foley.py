"""Sound for the Fourier film: let the viewer hear the partial sums.

A 3b1b-style explainer wants almost no effects, so the "foley" here is a sonification tied to the picture: a tone on D4
(the tonic of the planned D major bed) whose waveform IS the curve on screen at that moment.
  A  the grey target draws → the square wave itself, a hollow, clarinet-like tone (band-limited, softened)
  B  one blue sine        → a pure sine
  D3/D5/D7 the new harmonic draws along the axis → its own partial, n·f0, quieter (it is 1/n as tall);
           it merges into the yellow sum → the sum tone with that harmonic added (a little brighter, a little squarer)
  D∞ N runs 7 → 25        → the sum tone's harmonics fade in with the same continuous term count w the scene uses
Then two quiet marks: the zoom panel opening, and a bell on "≈ 9% of the jump". Times are the play()/wait() timings of
scenes/fourier.py (cited per event). All sounds sit at gain_db ≤ −18 (they swell, they are not hits).

usage (from the repo root):
  uv run -q --with numpy --with scipy python showcase/03-math-fourier/tools/foley.py
  bin/vh sfx lib showcase/03-math-fourier/audio/sfx
  bin/vh sfx place showcase/03-math-fourier/audio/events.json showcase/03-math-fourier/audio/sfx.wav 25 \
      --lib showcase/03-math-fourier/audio/sfx
Seeded, no downloads, the same bytes on every run. The tones carry "layer": "sonification"; tools/build_audio.sh
--no-sonify leaves them out (the zoom whoosh and the bell stay).
"""
import json, math, wave
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
FILM = Path(__file__).resolve().parent.parent
OUT = FILM / "audio" / "sfx"
F0 = 293.66                                            # D4

def smooth(t, inflection=10.0):                        # manim.utils.rate_functions.smooth
    s = lambda x: 1 / (1 + math.exp(-x)); err = s(-inflection / 2)
    return min(max((s(inflection * (t - 0.5)) - err) / (1 - 2 * err), 0), 1)

def T(d): return np.arange(int(round(d * SR))) / SR
def env(d, a, r):                                      # raised-cosine attack a and release r over d seconds
    t = T(d); up = np.where(t < a, 0.5 - 0.5 * np.cos(np.pi * t / a), 1.0)
    return up * np.where(t > d - r, 0.5 + 0.5 * np.cos(np.pi * (t - (d - r)) / r), 1.0)
def partials(d, weights, f0=F0):
    """Σ_k weights[k](t) · (4/π)·sin(2π(2k+1)f0 t)/(2k+1): the scene's partial_sum with term k weighted like its w"""
    t = T(d); y = np.zeros_like(t)
    for k, wk in enumerate(weights):
        n = 2 * k + 1
        if n * f0 < 16000:
            y += np.broadcast_to(wk, t.shape) * 4 / (math.pi * n) * np.sin(2 * np.pi * n * f0 * t)
    return y
def lowpass(x, f): return sosfilt(butter(2, f / (SR / 2), "low", output="sos"), x)
def write(name, x):
    x = np.clip(np.asarray(x, float) / max(1e-9, np.abs(x).max()) * 0.89, -1, 1)
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f"{name}.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())

def sum_tone(N, d, a=0.12, r=0.5):  # S_N with every term at weight 1
    return partials(d, [1.0] * ((N + 1) // 2)) * env(d, a, r)

def main():
    sounds, ev = {}, []
    def add(t, sfx, gain_db, why, layer="sonification"):
        ev.append({"t": round(float(t), 3), "sfx": sfx, "gain_db": gain_db, **({"layer": layer} if layer else {}), "why": why})

    # A · 0.2–1.4 the target draws, hold to 2.1: the square wave itself (29 odd partials ≈ 8.5 kHz), softened
    sounds["target_square"] = lowpass(partials(1.9, [1.0] * 15), 2500) * env(1.9, 0.35, 0.5)
    add(0.2, "target_square", -26, "A: grey square wave draws 0.2–1.4 (self.wait(0.2); play 1.2 s), holds to 2.1")
    # B · 2.1–3.3 one sine draws, holds, turns yellow 3.9–4.3
    sounds["sum_1"] = sum_tone(1, 2.9, 0.4, 0.7)
    add(2.1, "sum_1", -22, "B: blue (4/π) sin x draws 2.1–3.3, hold 0.6 s, turns yellow 3.9–4.3")
    # D3 / D5 / D7: add_term(k, …, t_draw, h1, t_lift, t_merge, h2), start times from the play() chain
    for n, t_draw0, lift_end, merge_end, next_start in [(3, 8.1, 10.2, 10.6, 11.0), (5, 11.0, 12.5, 12.85, 13.1), (7, 13.1, 14.4, 14.7, 14.9)]:
        d = lift_end - t_draw0 + 0.1
        sounds[f"harmonic_{n}"] = np.sin(2 * np.pi * n * F0 * T(d)) * env(d, 0.15, 0.35)
        add(t_draw0, f"harmonic_{n}", -22 - 2 * (n // 3), f"D{n}: blue sin({n}x)/{n} draws on the axis from {t_draw0} and lifts onto the sum until {lift_end}")
        d = next_start - lift_end + 0.6
        sounds[f"sum_{n}"] = sum_tone(n, d, 0.08, 0.5)
        add(lift_end, f"sum_{n}", -22, f"D{n}: the yellow sum absorbs it {lift_end}–{merge_end}: S_{n} (corners sharper)")
    # D∞ · 15.5–16.7 w 4 → 13 (N 7 → 25) with manim's smooth, hold to 17.2
    t0, d = 15.3, 2.2
    tt = T(d) + t0
    w = np.array([4 + 9 * smooth(min(1, max(0, (x - 15.5) / 1.2))) for x in tt[::48]]).repeat(48)[: len(tt)]
    sounds["sum_sweep"] = partials(d, [np.clip(w - k, 0, 1) for k in range(13)]) * env(d, 0.2, 0.5)
    add(t0, "sum_sweep", -23, "D∞: N runs 7 → 25 over 15.5–16.7 (w 4 → 13, smooth), hold to 17.2")
    # E · 17.2–18.9: parent shrinks, magnifier box, zoom panel grows 18.0–18.7
    add(18.35, "whoosh", -19, "E: the zoom panel grows out of the magnifier box, 18.0–18.7 (whoosh peaks at t)", None)
    # F · brace + '≈ 9% of the jump' fade in 21.8–22.4
    t = T(2.0)
    sounds["bell_a5"] = sum(a * np.sin(2 * np.pi * 880 * k * t) * np.exp(-t / dec) for k, a, dec in [(1, 1, .7), (2.76, .25, .25), (5.4, .08, .1)]) * np.minimum(1, t / 0.003)
    add(21.8, "bell_a5", -20, "F: red brace + '≈ 9% of the jump' fade in 21.8–22.4 (the payoff)", None)

    for k, v in sounds.items():
        write(k, v)
    ev.sort(key=lambda e: e["t"])
    (FILM / "audio").mkdir(exist_ok=True)
    (FILM / "audio" / "events.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(sounds)} custom sounds → {OUT.relative_to(FILM)}/, {len(ev)} events → audio/events.json")

if __name__ == "__main__":
    main()
