"""Three-bus mix: voice + music + SFX → one stereo track at −14 LUFS.

usage (via bin/vh mix):
  python tools/audio/mix.py <out.wav> [voice=vo.wav] [music=m.wav] [sfx=s.wav] [music_db=-6] [sfx_db=0] [voice_db=0]
                            [duck=voice|on|off] [duck_ratio=1.6] [lufs=-14] [tp=-1.5]                 the default chain
  python tools/audio/mix.py <out.wav> profile=explainer|short|promo|cartoon|mv|swatch [voice=vo.wav] [music=m.wav]
                            [events=events.json [lib=DIR] [root=DIR] [roles=roles.json] [keep=t1,t2] | sfx=s.wav]
                            [timeline=timeline.json] [stems=DIR] [dur=S] [fade=S] [music_db=-6] [sfx_db=0] [voice_db=0]
                            [lufs=-14] [tp=-1.65]                                                             a mix profile

THE DEFAULT CHAIN (no profile=, or profile=none; ffmpeg only)
Any bus may be omitted. The default is duck=voice when there is a voice bus (the music is side-chain compressed by
the voice, so a narration line is always heard: "music makes way", playbook/04-audio.md), else duck=off.
duck_ratio=1.6 lets the music dip under the voice without dropping out in the ~0.25 s pauses between lines;
6 and 3 did (bin/vh qa pumping) in a listening test on 2026-09-30.
duck=on keys on voice + SFX so a "ding" pushes the music down too: then keep duck_ratio low (2–3), or the music
pumps on every hit.
Stereo is preserved (mono buses are centred). Loudness is ONE static gain, so a cinematic score keeps its dynamics
(LRA) instead of being squashed by dynamic normalisation: pass 1 measures the integrated loudness and the 4×-oversampled
peaks, pass 2 applies gain = target − measured with `volume`; only if that gain would push the true peak above tp does
a true-peak limiter follow (4× oversampled alimiter at the ceiling; the gain is re-measured and topped up for the
loudness it takes), and a last pass measures the file written. The report says which of the two it was and prints the
measured output. (loudnorm linear=true is not used: it silently falls back to dynamic mode whenever the gain would
push the true peak over tp.)
Every bus is padded with silence or trimmed to the longest one before the mix, the ducker's two inputs come from ONE
stream (amerge → asplit) padded 1 s past that length, and the ducked music is trimmed back: with ffmpeg 8.0.1,
sidechaincompress ends its output as soon as its main input's frames are consumed and drops what its sidechain FIFO has
not matched yet, so when the two inputs came from separate decoder threads the ducked music lost a run-dependent tail
(up to ~1.2 s here), the last part of a mix whose voice ended early came out silent, and the loudness pass measured a
truncated mix. Repeated runs are now byte-identical and the output is exactly as long as the longest bus.

A MIX PROFILE (profile=…; numpy + scipy, so bin/vh mix runs it through uv)
Every level is set relative to ONE anchor: the narration's median line loudness, or without a voice the music's 3 s
short-term loudness (floored 8 LU under its integrated loudness, so SFX follow the scene but do not vanish in a
break). The order is voice anchor → music VMR → SFX classes → depth → master:
  voice   front plane, dry and centred: HPF 80 Hz; each line moved 60 % of the way to the median line (≤ ±3 dB, the
          step sits in the pause before the line); true peaks ≤ anchor + 10.5 dB.
  music   back plane: HPF 30 Hz, the profile's EQ, side +1.5–2 dB above 200 Hz, a hall "air" return when the score is
          narrow (L/R correlation 250 Hz–4 kHz > 0.75), bus peaks ≤ its own loudness + 12 dB. Under narration a
          look-ahead fader ride instead of a compressor: each line's depth is solved in a closed loop until the line
          sits at the profile's VMR (voice − music, LU); it starts `pre` s before the line, holds across pauses shorter
          than `hold` (a pause < 1.5 s keeps half of it) and releases over `release` s; plus a 1–4 kHz carve only as
          deep as the words need (Chinese narration, from the timeline's lang: 250 Hz–1 kHz takes 60 % of it). No
          narration: hero hits get a short dip instead.
  sfx     middle plane. events= are placed as `bin/vh sfx place` places them, each classed hero / detail / ambience /
          signal ("role" in events.json or roles=, else "layer": "sonification" → signal, else a name hint), and moved
          half way to its class centre re the anchor, clamped 0.5 LU inside the class range (loud outliers come down
          most, the designer's order is kept); a gesture (≤ 60 ms) and a busy passage (≤ 0.2 s chains) move as one;
          a hit with > 60 % of its energy under 150 Hz is never raised; ±9 dB at most. A hero stays under a speaking
          voice, ambience ducks 4 dB under speech, one short shared room (RT60 0.25–0.3 s) puts the SFX just behind the
          dry voice, a presence carve clears the words an SFX would cover, bus peaks ≤ anchor + 11 dB (cartoon + 9).
          sfx= (one pre-placed bus, no events) is mixed as a single detail layer: nothing to class.
  master  fade, one static gain to lufs= on a BS.1770 meter (ffmpeg's ebur128 agrees; loudnorm differs on short clips,
          −0.2 LU on a 25 s film, +0.3 on a 5 s swatch), then a look-ahead true-peak limiter only if needed. tp defaults to
          −1.65 dBTP: 0.15 dB of margin for the AAC encode (+0.03–0.2 dB), so the mp4 stays at or under −1.5.
  music_db / sfx_db / voice_db   the build's starting balance: SFX are judged from it (default −6 / 0 / 0; swatch 0 / −3)
  keep=   cue times whose passage keeps its designed SFX level (a synced onset the class moves made undetectable)
  stems=  a folder for the buses as heard at the final gain (voice, music, sfx, sfx_<class>.wav) and meta.json with
          every decision and each event's level: `bin/vh qa mix --stems DIR` reads it.
Deterministic (seeded room IRs, no threads, no ffmpeg filters in the signal path; ffmpeg only decodes and, for a
non-WAV out, encodes): the same inputs give the same bytes. About 3–4 s for a 25 s film on an M3 Max.
"""
import json, os, re, subprocess, sys, time

try:   # the profile path only: the default chain needs nothing but ffmpeg
    import numpy as np
    from scipy.io import wavfile
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    from scipy.signal import butter, fftconvolve, resample_poly, sosfilt, sosfiltfilt
except ImportError:
    np = None

def loudness(stderr):  # loudnorm's print_format=json block → {"input_i", "input_tp", "input_lra", …}
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr, re.S).group(0))

USAGE = ("usage: bin/vh mix <out.wav> [voice=vo.wav] [music=m.wav] [sfx=s.wav] [music_db=-6] [sfx_db=0] [voice_db=0] "
         "[duck=voice|on|off] [duck_ratio=1.6] [lufs=-14] [tp=-1.5]\n"
         "       bin/vh mix <out.wav> profile=explainer|short|promo|cartoon|mv|swatch [voice=vo.wav] [music=m.wav] "
         "[events=events.json [lib=DIR] [root=DIR] [roles=roles.json] [keep=t1,t2] | sfx=s.wav] [timeline=timeline.json] "
         "[stems=DIR] [dur=S] [fade=S] [music_db=-6] [sfx_db=0] [voice_db=0] [lufs=-14] [tp=-1.65]")
PROFILE_KEYS = ("profile", "events", "lib", "root", "timeline", "roles", "stems", "keep", "dur", "fade")
KEYS = ("voice", "music", "sfx", "music_db", "sfx_db", "voice_db", "duck", "duck_ratio", "lufs", "tp") + PROFILE_KEYS

def main():
    if sys.argv[1:2] in (["-h"], ["--help"]): print(USAGE); sys.exit(0)
    if len(sys.argv) < 2: sys.exit(USAGE)
    bad = [a for a in sys.argv[2:] if "=" not in a or a.split("=", 1)[0] not in KEYS]   # a bare path or a typo, not a traceback
    if bad: sys.exit(f"{USAGE}\nnot key=value, or not a known key: {' '.join(bad)}")
    out = sys.argv[1]; kv = dict(a.split("=", 1) for a in sys.argv[2:])
    for k in ("music_db", "sfx_db", "voice_db", "duck_ratio", "lufs", "tp", "dur", "fade"):
        if k in kv:
            try: float(kv[k])
            except ValueError: sys.exit(f"{k}={kv[k]}: not a number")
    if kv.get("profile", "none") == "none":
        extra = [k for k in PROFILE_KEYS[1:] if k in kv]
        if extra: sys.exit(f"{' '.join(k + '=' for k in extra)}: only with a mix profile (profile={'|'.join(PROFILES)})")
        return default_chain(out, kv)
    return layered(out, kv)

def default_chain(out, kv):   # ffmpeg only; byte-identical to the chain before mix profiles existed
    if kv.get("duck", "voice") not in ("voice", "on", "off"): sys.exit(f"duck={kv['duck']}: use duck=voice, duck=on or duck=off")
    buses = [(k, kv[k]) for k in ("voice", "music", "sfx") if kv.get(k)]
    if not buses: sys.exit("give at least one of voice= music= sfx=")
    ins, idx = [], {}
    for k, p in buses: idx[k] = len(ins) // 2; ins += ["-i", p]
    g = lambda k, d: float(kv.get(f"{k}_db", d))
    secs = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], capture_output=True, text=True, check=True).stdout)
    N = max(round(secs(p) * 48000) for _, p in buses)   # every bus becomes exactly N samples: one EOF for amix and the ducker
    f = []
    for k, _ in buses:
        f.append(f"[{idx[k]}:a]aresample=48000,aformat=channel_layouts=stereo,apad=whole_len={N},atrim=end_sample={N},volume={g(k, -6 if k == 'music' else 0)}dB[{k}]")
    fg = [k for k, _ in buses if k != "music"]
    duck = kv.get("duck", "voice" if "voice" in idx else "off"); keys = [k for k in fg if duck == "on" or (duck == "voice" and k == "voice")]
    ducked = "music" in idx and keys and duck != "off"
    if ducked:
        if len(keys) == 2:
            f += ["[voice]asplit[v1][v2]", "[sfx]asplit[s1][s2]", "[v1][s1]amix=inputs=2:normalize=0[key]"]; fg_out = ["[v2]", "[s2]"]
        else:
            f += [f"[{keys[0]}]asplit[key][f0]"]; fg_out = ["[f0]"] + [f"[{k}]" for k in fg if k not in keys]
        # music and key merged into one stream and split again, so sidechaincompress gets both in lockstep (one frame of
        # skew at most, whatever the decoder threads do); both padded 1 s past N so what the filter drops at EOF is padding
        P = 48000
        f.append(f"[music]apad=pad_len={P}[mp];[key]apad=pad_len={P}[kp];[mp][kp]amerge=inputs=2,asplit[mk1][mk2];"
                 f"[mk1]pan=stereo|c0=c0|c1=c1[m2];[mk2]pan=stereo|c0=c2|c1=c3[k2];"
                 f"[m2][k2]sidechaincompress=threshold=0.02:ratio={kv.get('duck_ratio', '1.6')}:attack=15:release=350:makeup=1,atrim=end_sample={N}[duck]")
        tracks = ["[duck]"] + fg_out
    else:
        tracks = [f"[{k}]" for k, _ in buses]
    # aformat pins the mix to 48 kHz: loudnorm (pass 1's meter) only takes 192 kHz, and without the pin libavfilter
    # negotiates that rate backwards through the whole graph, so pass 1 would process the mix at 192 kHz and every
    # sample count above (apad, atrim) would mean a quarter of the intended time; with it both passes run the same
    # graph and the conversion sits right before loudnorm
    pre = ";".join(f) + ";" + "".join(tracks) + f"amix=inputs={len(tracks)}:duration=longest:dropout_transition=0:normalize=0,aformat=sample_rates=48000"
    lufs, tp = float(kv.get("lufs", -14)), float(kv.get("tp", -1.5))
    ln = f"loudnorm=I={lufs}:TP={tp}:LRA=20:print_format=json"          # used only as a meter (BS.1770 I, true peak, LRA)
    # pass 1: measure loudness, and the peak of every 10 ms at 4× oversampling (≈ true peak) to see what the gain hits
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *ins, "-filter_complex",
                        pre + f",asplit[a][b];[a]{ln}[out];[b]aresample=192000,asetnsamples=1920,astats=metadata=1:reset=1:"
                        "measure_perchannel=none:measure_overall=Peak_level,ametadata=print:key=lavfi.astats.Overall.Peak_level,anullsink",
                        "-map", "[out]", "-f", "null", "-"], capture_output=True, text=True, check=True)
    m = loudness(r.stderr)
    peaks = [float(v) for v in re.findall(r"Overall\.Peak_level=(\S+)", r.stderr)] or [float(m["input_tp"])]
    gain, ceil, last = lufs - float(m["input_i"]), tp, None
    for k in range(4):   # pass 2: one static gain; a limiter only where it would cross tp (then top up what it took)
        over = [p + gain > ceil for p in peaks]
        n = sum(1 for i, o in enumerate(over) if o and not (i and over[i - 1]))   # peaks = runs of 10 ms blocks over it
        chain = f"volume={gain:.3f}dB" + (f",aresample=192000,alimiter=limit={10 ** (ceil / 20):.6f}:level=false:latency=true,aresample=48000" if n else "") + f",apad=whole_len={N},atrim=end_sample={N}"
        subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", pre + f",{chain}[out]", "-map", "[out]", "-ar", "48000", out], check=True)
        o = loudness(subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", out, "-af", ln, "-f", "null", "-"],
                                    capture_output=True, text=True, check=True).stderr)   # last pass: measure the file
        i, t = float(o["input_i"]), float(o["input_tp"])
        if k == 3 or (abs(i - lufs) <= .2 and t <= tp + .05) or (not n and t <= tp + .1):
            break
        ceil -= max(0, t - tp + .03)                                   # going back to 48 kHz adds ~0.2 dB between samples
        slope = min(1, max(.2, (i - last[1]) / (gain - last[0]))) if last and gain != last[0] else 1   # limiting eats part of each dB
        last, gain = (gain, i), gain + (lufs - i) / slope
    how = f"static gain {gain:+.2f} dB" + (f" + true-peak limiter ({n} peak{'s' * (n > 1)}, up to {max(peaks) + gain - ceil:.1f} dB of reduction)" if n else "")
    print(f"{out}  (stereo · {' + '.join(k for k, _ in buses)}{f', ducked by {chr(43).join(keys)}' if ducked else ''} · {how} · "
          f"measured {o['input_i']} LUFS, true peak {o['input_tp']} dBTP, LRA {o['input_lra']} LU · input {m['input_i']} LUFS, LRA {m['input_lra']} LU)")

# ═════════════════════════════════════════════ mix profiles ═════════════════════════════════════════════
# The numbers are LU re the anchor unless noted. Designed and measured in the mix lab (2026-10-01): the narrated
# showcase films sat 8 LU over the music with lines down to 1.3 LU, 27–41 % of their words under 6 dB of 1–4 kHz SNR,
# and SFX a few LU over the music in one film and 20 LU under it in another. One table serves the mixer (the targets)
# and `bin/vh qa mix` (the checks), so they cannot drift apart.
CLASSES = ("hero", "detail", "ambience", "signal")
BASE = {
    "balance": (-6.0, 0.0),        # the build's starting music_db / sfx_db (bin/vh mix's defaults): SFX are judged from it
    "voice": {"hpf": 80, "level": 0.6, "level_max": 3.0, "plr": 10.5},
    "music": {"vmr": None, "hold": 0.8, "pre": 0.15, "release": 0.6, "duck_min": 2.0, "duck_max": 12.0, "carve_snr": 12.0,
              "carve_max": 9.0, "body": 2.0, "body_share": 0.35, "eq": [(300, -2.0, 1.0)], "width_db": 2.0, "hpf": 30,
              "air_db": -18.0, "air_if_corr": 0.75, "plr": 12.0, "gap_keep": 0.5},
    "sfx": {"classes": {}, "hero_under_voice": -4.0, "carve_snr": 10.0, "carve_max": 8.0, "amb_duck": 4.0, "max_move": 9.0,
            "plr": 11.0, "room": {"rt60": 0.30, "pre": 0.006, "send": {"hero": -17, "detail": -14, "ambience": -9, "signal": -15}}},
    "hero_dip": 0.0, "local_floor": 8.0,
    # bin/vh qa mix: a line under vmr_fail is a hard fail (the OK range is the music vmr floor…ceiling); a word whose
    # 1–4 kHz SNR is under `snr` dB is at risk, more than `risk` of them fails; a pause's music rising > gap_rise LU
    # over the music under its lines warns; an event > `buried` dB under the local bed warns
    "check": {"vmr_fail": 9, "snr": 6, "risk": 0.10, "gap_rise": 4, "buried": -14},
}
PROFILES = {
    # knowledge / maths explainer: the narration is the programme (3Blue1Brown register)
    "explainer": {"music": {"vmr": (13.0, 11.0, 18.0), "hold": 0.9, "carve_snr": 10.0, "carve_max": 7.0},
                  "sfx": {"classes": {"hero": (-9, -2), "detail": (-18, -8), "ambience": (-28, -16), "signal": (-12, -4)}}},
    # knowledge short: faster, the music keeps more drive, still voice-first
    "short":     {"music": {"vmr": (11.5, 10.0, 16.0), "pre": 0.12, "release": 0.5, "carve_snr": 9.0, "carve_max": 6.0},
                  "sfx": {"classes": {"hero": (-7, -1), "detail": (-16, -7), "ambience": (-26, -14), "signal": (-8, -2)},
                          "hero_under_voice": -3.0}, "hero_dip": 2.0,
                  "check": {"vmr_fail": 8, "gap_rise": 5}},
    # promo / kinetic type: music-forward with hero SFX (anchor = the music unless narrated)
    "promo":     {"music": {"vmr": (10.0, 8.0, 16.0), "eq": [], "width_db": 1.5, "air_db": None},
                  "sfx": {"classes": {"hero": (-4, 2), "detail": (-11, -3), "ambience": (-20, -10), "signal": (-10, -3)},
                          "hero_under_voice": -2.0}, "hero_dip": 2.5,
                  "check": {"vmr_fail": 6, "snr": 4, "risk": 0.15, "gap_rise": 8}},
    # cartoon: foley-forward, the foley is the character's voice
    "cartoon":   {"music": {"vmr": (10.0, 8.0, 16.0), "eq": [], "width_db": 2.0, "air_db": -20.0},
                  "sfx": {"classes": {"hero": (-2, 4), "detail": (-6, 0), "ambience": (-16, -8), "signal": (-6, 0)},
                          "plr": 9.0, "hero_under_voice": -2.0}, "hero_dip": 2.0,
                  "check": {"vmr_fail": 6, "snr": 4, "risk": 0.15, "gap_rise": 8}},
    # music video: the music is the track
    "mv":        {"music": {"vmr": (6.0, 4.0, 12.0), "eq": [], "width_db": 0.0, "air_db": None},
                  "sfx": {"classes": {"hero": (-8, -2), "detail": (-16, -8), "ambience": (-26, -14), "signal": (-12, -5)}},
                  "check": {"vmr_fail": 3, "snr": 3, "risk": 0.25, "gap_rise": 10, "buried": -16}},
    # 5 s style swatch: music + foley, no voice; render.sh's old balance (music 0 dB, foley −3 dB) is the starting point
    "swatch":    {"balance": (0.0, -3.0),
                  "music": {"vmr": (10.0, 8.0, 16.0), "eq": [], "width_db": 1.5, "air_db": None},
                  "sfx": {"classes": {"hero": (-5, 1), "detail": (-11, -4), "ambience": (-19, -11), "signal": (-10, -3)},
                          "room": {"rt60": 0.25, "pre": 0.005, "send": {"hero": -18, "detail": -15, "ambience": -10, "signal": -16}}},
                  "hero_dip": 2.0, "check": {"vmr_fail": 6, "snr": 4, "risk": 0.15, "gap_rise": 8}},
}
ZH = {"music": {"body": 3.0, "body_share": 0.6}}   # Mandarin: tones live in 250 Hz–1 kHz too, so the carve reaches down there

def profile(name, zh=False):
    """the full settings of a profile: BASE, the profile's changes, and the Chinese-narration carve"""
    import copy
    P = copy.deepcopy(BASE)
    for over in (PROFILES[name], ZH if zh else {}):
        for k, v in over.items():
            if isinstance(v, dict): P[k].update(copy.deepcopy(v))
            else: P[k] = v
    P["name"], P["zh"] = name, bool(zh)
    return P

# ── io, meters (BS.1770), true peak
SR, HOP = 48000, 0.01
KW = ((1.53512485958697, -2.69169618940638, 1.19839281085285, 1.0, -1.69065929318241, 0.73248077421585),
      (1.0, -2.0, 1.0, 1.0, -1.99004745483398, 0.99007225036621))   # BS.1770 K-weighting at 48 kHz (two biquads)

def load(path):
    """any file ffmpeg decodes → float64 (n, channels) at 48 kHz"""
    st = json.loads(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=channels", "-of", "json",
                                    str(path)], capture_output=True, text=True, check=True).stdout)["streams"][0]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ar", str(SR), "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, "<f4").reshape(-1, int(st["channels"])).astype(np.float64)

def save(path, x):
    """(n, 2) float → a 32-bit float WAV (another extension: encoded by ffmpeg from the same samples)"""
    x = np.ascontiguousarray(x, np.float32)
    if str(path).lower().endswith(".wav"): wavfile.write(str(path), SR, x); return
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-", str(path)],
                   input=x.tobytes(), check=True)

def fitn(x, n):
    return x[:n] if len(x) >= n else np.concatenate([x, np.zeros((n - len(x),) + x.shape[1:])])

def as_stereo(x):
    """(n,) or (n, 1) → centred stereo, −3 dB a side (ffmpeg's upmix: loudness kept); stereo passes through"""
    x = x[:, None] if x.ndim == 1 else x
    return x if x.shape[1] == 2 else np.repeat(x[:, :1] * np.sqrt(0.5), 2, 1)

def kpow(x):
    """K-weighted power per sample, summed over the channels (BS.1770: G = 1 for L and R)"""
    y = sosfilt(KW, x if x.ndim == 2 else x[:, None], axis=0); np.square(y, out=y); return y.sum(1)

def lufs(p): return -0.691 + 10 * np.log10(np.maximum(p, 1e-15))

def frames(p, win, hop=HOP, n=None):
    """mean of the per-sample power p over `win` s windows centred every `hop` s → (centre times, means)"""
    w, h = int(round(win * SR)), int(round(hop * SR)); n = n or len(p)
    c = np.concatenate([[0.0], np.cumsum(p[:n])]); ctr = np.arange(0, n, h); a = np.clip(ctr - w // 2, 0, n); b = np.clip(ctr + w - w // 2, 0, n)
    return ctr / SR, (c[b] - c[a]) / np.maximum(b - a, 1)

def win_mean(p, win, hop=HOP, n=None): return frames(p, win, hop, n)[1]

def integrated(p, a=0, b=None, gate=True):
    """BS.1770-4 integrated loudness of the K-power p over samples [a, b): 400 ms blocks, 75 % overlap, −70 LUFS absolute
    and −10 LU relative gates (gate=False: the plain energy mean, for a bed whose quiet stretches are part of what is heard)"""
    b = len(p) if b is None else b; seg = p[a:b]; w, h = int(0.4 * SR), int(0.1 * SR)
    if not gate or len(seg) < w: return float(lufs(seg.mean())) if len(seg) else -120.0
    c = np.concatenate([[0.0], np.cumsum(seg)]); s = np.arange(0, len(seg) - w + 1, h); z = (c[s + w] - c[s]) / w
    z = z[lufs(z) > -70]
    if not len(z): return -120.0
    return float(lufs(z[lufs(z) > lufs(z.mean()) - 10].mean()))

def tp_per_sample(x, block=1 << 18):
    """true-peak envelope: 4× oversampled |x|, the max over channels and over the 4 sub-samples of each sample; in
    blocks with 256 samples of context each side (the interpolator reaches ~10), the same values as one pass, bounded memory"""
    x = x if x.ndim == 2 else x[:, None]; n = len(x); out = np.empty(n)
    for a in range(0, n, block):
        b = min(n, a + block); lo, hi = max(0, a - 256), min(n, b + 256)
        up = np.abs(resample_poly(x[lo:hi], 4, 1, axis=0)).max(1)
        out[a:b] = up[(a - lo) * 4:(b - lo) * 4].reshape(-1, 4).max(1)
    return out

def true_peak(x): return float(20 * np.log10(max(tp_per_sample(as_stereo(x)).max(), 1e-9))) if len(x) else -120.0

def stft_band(m, lo, hi, nfft=2048):
    """power of the mono signal m in [lo, hi) Hz every HOP s (Hann frames centred on k·HOP), in blocks: bounded memory"""
    hop = int(HOP * SR); pad = np.concatenate([np.zeros(nfft // 2), m, np.zeros(nfft)]); n = 1 + (len(m) - 1) // hop
    f = np.fft.rfftfreq(nfft, 1 / SR); sel = (f >= lo) & (f < hi); out = np.empty(n); win = np.hanning(nfft)
    for a in range(0, n, 512):
        b = min(n, a + 512); idx = np.arange(nfft)[None, :] + hop * np.arange(a, b)[:, None]
        out[a:b] = (np.abs(np.fft.rfft(pad[idx] * win, axis=1)[:, sel]) ** 2).sum(1)
    return out

# ── DSP blocks
def sos_hp(f, o=2): return butter(o, f / (SR / 2), "high", output="sos")
def sos_lp(f, o=2): return butter(o, f / (SR / 2), "low", output="sos")

def split4(x):
    """zero-phase complementary split: low < 250 Hz, body 250–1k, presence 1k–4k, air > 4k; the four sum to x exactly"""
    low = sosfiltfilt(sos_lp(250), x, axis=0); r = x - low
    body = sosfiltfilt(sos_lp(1000), r, axis=0); r = r - body
    pres = sosfiltfilt(sos_lp(4000), r, axis=0); return low, body, pres, r - pres

def peaking(x, f0, gain_db, q):
    """RBJ peaking EQ, zero-phase (filtfilt of a half-gain biquad: the full gain at f0, no phase shift)"""
    A = 10 ** (gain_db / 80); w = 2 * np.pi * f0 / SR; al = np.sin(w) / (2 * q)
    b = np.array([1 + al * A, -2 * np.cos(w), 1 - al * A]); a = np.array([1 + al / A, -2 * np.cos(w), 1 - al / A])
    return sosfiltfilt(np.concatenate([b / a[0], a / a[0]])[None, :], x, axis=0)

def widen(x, side_db, fc=200.0):
    """side +side_db above fc; the lows keep their mid/side balance (mono-safe bass)"""
    if not side_db or x.shape[1] < 2: return x
    m, s = (x[:, 0] + x[:, 1]) / 2, (x[:, 0] - x[:, 1]) / 2
    sh = sosfiltfilt(sos_hp(fc), s); s = s + sh * (10 ** (side_db / 20) - 1)
    return np.stack([m + s, m - s], 1)

def room_ir(rt60, pre, seed, ch, er=True):
    """a short synthetic room: decorrelated noise with an exponential decay (highs faster), 6 early reflections and a
    pre-delay; fixed seed per (seed, channel), so the same room on every run; unit energy"""
    g = np.random.default_rng([4217, seed, ch]); n = int(rt60 * SR); t = np.arange(n) / SR; tau = rt60 / 6.91
    nz = g.standard_normal(n); lo = sosfilt(sos_lp(3500), nz)
    ir = lo * np.exp(-t / tau) + (nz - lo) * np.exp(-t / (tau * 0.5)); ir *= 1 - np.exp(-t / 0.004)
    if er:
        for k in range(6): ir[int(g.uniform(0.002, 0.025) * SR)] += g.choice([-1, 1]) * 2.5 / (1 + k)
    ir = np.concatenate([np.zeros(int(pre * SR)), ir]); return ir / np.sqrt((ir ** 2).sum())

def send_return(x, rt60, pre, send_db, seed, hp=250, lp=7000):
    """(n, 2) → the wet return (n, 2): HP/LP the send, each side through its own IR, scaled by send_db"""
    s = sosfilt(sos_lp(lp), sosfilt(sos_hp(hp), x, axis=0), axis=0)
    return np.stack([fftconvolve(s[:, c], room_ir(rt60, pre, seed, c))[:len(x)] for c in range(2)], 1) * 10 ** (send_db / 20)

def cone(need, att, rel):
    """a reduction envelope (dB, ≥ need everywhere) with linear-in-dB ramps: it reaches each value early at slope `att`
    per frame and falls back at `rel` per frame after it (max-plus dilation, vectorised)"""
    i = np.arange(len(need), dtype=np.float64)
    fwd = np.maximum.accumulate(need + rel * i) - rel * i
    bwd = np.maximum.accumulate((need - att * i)[::-1])[::-1] + att * i
    return np.maximum(fwd, bwd)

def close_gaps(mask, gap_frames):
    """fill the False runs shorter than gap_frames between True runs (hold across short pauses)"""
    m = mask.copy(); idx = np.nonzero(mask)[0]
    if len(idx) < 2: return m
    d = np.diff(idx)
    for k in np.nonzero((d > 1) & (d <= gap_frames + 1))[0]: m[idx[k]:idx[k + 1]] = True
    return m

def to_samples(env, n):
    """a HOP-rate envelope → per sample (linear between frame centres)"""
    return np.interp(np.arange(n) / SR, np.arange(len(env)) * HOP, env)

def tp_limit(x, ceil_db, look=0.0015, rel=0.08):
    """look-ahead true-peak limiter: need = the reduction that brings each sample's 4× peak to the ceiling; a cone with a
    `look` s attack and a 12 dB per 1.5·rel s release, on a ±0.5 ms plateau and smoothed over the same ±0.5 ms, so the
    gain never gives back less than the need → (x limited, most reduction dB, number of peaks)"""
    need = np.maximum(0.0, 20 * np.log10(np.maximum(tp_per_sample(x), 1e-12)) - ceil_db)
    if need.max() <= 0: return x, 0.0, 0
    L = max(1, int(look * SR)); need = maximum_filter1d(need, 49)
    r = cone(need, need.max() / L, 12.0 / (rel * SR * 1.5))
    r = uniform_filter1d(r, 49)
    return x * 10 ** (-r / 20)[:, None], float(need.max()), int(((need[1:] > 0) & (need[:-1] <= 0)).sum())

# ── SFX: classes and one event's own levels
HINTS = (("ambience", ("whirr", "gust", "wind", "rain", "room", "hum", "drone", "hiss", "creak", "air", "vinyl", "tape")),
         ("hero", ("impact", "boom", "braam", "stomp", "thunk", "slam", "crash", "gong", "success", "error", "ding", "bell",
                   "take", "snap", "reveal", "drop", "hit", "lock")),
         ("detail", ("click", "tick", "pop", "toggle", "typing", "keys", "step", "tiptoe", "thock", "count", "pat", "ping",
                     "sparkle", "hearts", "shutter", "glitch", "skid", "zip", "whoosh", "swish", "riser", "crank", "run",
                     "blip", "iris")))

def sfx_class(e):
    """an event's class and why: its "role", else "signal" for a sonification layer, else the first name hint that starts
    one of the name's words ("clock_tick" is a tick, not a lock), else detail"""
    if e.get("role"): return e["role"], "role"
    if e.get("layer") == "sonification": return "signal", "layer"
    n = re.sub(r"\.[A-Za-z0-9]+$", "", str(e.get("sfx", "")).lower().rsplit("/", 1)[-1])
    words = [w for w in re.split(r"[^a-z]+", n) if w]
    for cls, hints in HINTS:
        hit = next((h for h in hints if any(w.startswith(h) for w in words)), None)
        if hit: return cls, f"name '{hit}'"
    return "detail", "default"

def event_levels(y):
    """one event alone, (m, 2): fast = its loudest 100 ms (K-weighted LUFS), m400 = loudest 400 ms, tp = true peak (dBTP),
    at = where the fast max is (s from the start of y), on = its first 5 ms step within 10 dB of that, len / len10 = how
    long it stays within 20 / 10 dB of it (len10 decides whether it collides with speech), lf = share of its energy
    under 150 Hz (> 0.6: a hit that phone and laptop speakers barely play)"""
    k = kpow(y); L = lufs(win_mean(k, 0.1, 0.005)); im = int(np.argmax(L))
    on = np.nonzero(L >= L[im] - 20)[0]; on10 = np.nonzero(L >= L[im] - 10)[0]
    lo = sosfilt(sos_lp(150, 4), y.mean(1)); lf = float((lo ** 2).sum() / max((y.mean(1) ** 2).sum(), 1e-15))
    return {"fast": float(L[im]), "m400": float(lufs(win_mean(k, 0.4, 0.01)).max()), "tp": true_peak(y), "at": im * 0.005,
            "on": float(on10[0] * 0.005) if len(on10) else 0.0, "len": float((on[-1] - on[0]) * 0.005 + 0.1) if len(on) else 0.1,
            "len10": float((on10[-1] - im) * 0.005 + 0.05) if len(on10) else 0.05, "lf": lf}

def place(e, lib=None, root=None, cache=None):
    """one event the way `bin/vh sfx place` puts it on the track → (first sample, (m, 2) array)"""
    import sfx
    cache = {} if cache is None else cache; name = e["sfx"]
    if name not in cache: cache[name] = sfx.source(name, lib, root, e.get("t"))
    y = sfx.spatial(cache[name] * 10 ** (e.get("gain_db", 0) / 20), e.get("pan", 0), e.get("dist", 1))
    i = int(round((e["t"] - sfx.LANDMARK.get(name, 0.0)) * SR))
    if i < 0: y, i = y[-i:], 0
    return i, y

def narration_is_zh(timeline, voice_path):
    """Chinese narration? the timeline's lang (bin/vh tts writes it), else its text, else a .zh. in the voice file name"""
    if isinstance(timeline, dict) and timeline.get("lang"): return str(timeline["lang"]).lower().startswith("zh")
    segs = (timeline.get("segments") if isinstance(timeline, dict) else timeline) or []
    text = "".join(str(s.get("text") or "") for s in segs if isinstance(s, dict))
    if text: return sum("\u4e00" <= c <= "\u9fff" for c in text) > 0.5 * max(1, sum(c.isalpha() for c in text))
    return bool(re.search(r"(^|[._-])zh([._-]|$)", os.path.basename(voice_path or "")))

# ── the layered mix
def mixdown(P, voice=None, music=None, events=(), lib=None, root=None, sfx_bus=None, timeline=None, dur=None, fade=0.0,
            target=-14.0, tp=-1.65, roles=None, music_db=-6.0, sfx_db=0.0, keep=(), say=print, class_stems=True):
    """→ (mix (n, 2), stems {voice, music, sfx[, sfx_<class>]} before the master gain g, g, meta). class_stems=False:
    no per-class SFX stems after the bus is summed (they never feed the mix; less memory and time)"""
    T0 = time.time(); meta = {"profile": P["name"], "params": P, "decisions": []}
    def note(s): meta["decisions"].append(s); say("  " + s)
    lens = [len(x) for x in (voice, music, sfx_bus) if x is not None]
    placed_end, cache = 0, {}
    if not lens and not dur:   # events only: long enough for the last one
        for e in events: i, y = place(e, lib, root, cache); placed_end = max(placed_end, i + len(y))
    n = int(round(dur * SR)) if dur else max(lens) if lens else placed_end
    if n <= 0: sys.exit("mix: nothing to mix (no audio, and no events inside the duration)")
    nf = 1 + (n - 1) // int(HOP * SR)
    zero2 = np.zeros((n, 2))
    if P.get("zh"): note("voice: Chinese narration: the presence carve reaches 250 Hz–1 kHz too (body 3 dB, 60 % of the carve)")
    # ── voice: the front plane and the anchor
    lines, anchor, act, V = [], None, np.zeros(nf, bool), zero2
    if voice is not None:
        Pv = P["voice"]
        v = fitn(voice.mean(1) if voice.ndim == 2 else voice, n)
        v = sosfiltfilt(sos_hp(Pv["hpf"]), v)
        segs = (timeline.get("segments") if isinstance(timeline, dict) else timeline) if timeline else None
        if segs:   # lines inside the mix only
            segs = [s for s in segs if float(s["end"]) > float(s["start"]) and float(s["start"]) < n / SR]
        kv = kpow(np.stack([v, v], 1) * np.sqrt(0.5))
        if not segs:   # voiced runs; a gap > 0.35 s splits two lines
            e = lufs(win_mean(kv, 0.1)); on = np.nonzero(e > np.percentile(e, 97) - 25)[0]; segs = []
            if len(on) and e.max() > -70:
                st = on[0]
                for a_, b_ in zip(on[:-1], on[1:]):
                    if b_ - a_ > 35: segs.append({"start": st * HOP, "end": a_ * HOP}); st = b_
                segs.append({"start": st * HOP, "end": on[-1] * HOP})
        if segs:
            L = [integrated(kv, int(s["start"] * SR), int(min(float(s["end"]), n / SR) * SR)) for s in segs]
            med = float(np.median(L)); gain = np.zeros(n)
            for s, l in zip(segs, L):   # each line toward the median; the step sits in the pause before the line
                g = float(np.clip((med - l) * Pv["level"], -Pv["level_max"], Pv["level_max"]))
                a_, b_ = int(max(0, s["start"] - 0.08) * SR), int(min(n / SR, s["end"] + 0.15) * SR); gain[a_:b_] = g
                lines.append({"start": float(s["start"]), "end": float(s["end"]), "text": s.get("text", ""), "raw": l, "gain": g})
            gain = uniform_filter1d(gain, int(0.06 * SR))          # 60 ms crossfades between line gains
            v = v * 10 ** (gain / 20)
        V = np.stack([v, v], 1) * np.sqrt(0.5)                     # centred (−3 dB a side, as ffmpeg's upmix)
        kv = kpow(V)
        if lines:
            for ln in lines: ln["voice"] = integrated(kv, int(ln["start"] * SR), int(min(ln["end"], n / SR) * SR))
            anchor = float(np.median([ln["voice"] for ln in lines]))
            if Pv.get("plr"):   # dialogue peak control: true peaks ≤ anchor + plr, so the master limiter rarely works on words
                V, vl, vn = tp_limit(V, anchor + Pv["plr"], look=0.002, rel=0.05)
                if vl > 0: note(f"voice: peak control at anchor +{Pv['plr']:.0f} dB: {vn} peak(s), up to {vl:.1f} dB"); kv = kpow(V)
            vf = lufs(win_mean(kv, 0.1, HOP, n))[:nf]
            act = vf > anchor - 20
            inl = np.zeros(nf, bool)
            for ln in lines: inl[int(ln["start"] / HOP):int(ln["end"] / HOP) + 1] = True
            act &= inl
            gains = ", ".join("%+.1f" % ln["gain"] for ln in lines); span = max(ln["voice"] for ln in lines) - min(ln["voice"] for ln in lines)
            note(f"voice: {len(lines)} lines, raw span {max(L) - min(L):.1f} LU → levelled span {span:.1f} LU (gains {gains}); anchor {anchor:.1f} LUFS")
        else:
            note("voice: no speech found (no timeline lines, no voiced runs): the voice is mixed but anchors nothing")
    has_voice, has_music = anchor is not None, music is not None
    voice = v = kv = None                                           # the bus is V from here on: free the raw take
    pv = stft_band(V.mean(1), 1000, 4000)[:nf] if has_voice else np.zeros(nf)
    # ── music: the back plane (static chain)
    Pm = P["music"]; corr_mid = I_music = None
    M = fitn(music, n) * 10 ** (music_db / 20) if has_music else zero2.copy()   # start from the build's balance
    music = None
    if M.ndim == 1 or M.shape[1] == 1: M = np.repeat(M.reshape(n, -1)[:, :1] * np.sqrt(0.5), 2, 1)
    if has_music:
        M = sosfiltfilt(sos_hp(Pm["hpf"]), M, axis=0)
        for f0, gdb, q in Pm["eq"]: M = peaking(M, f0, gdb, q)
        bm = sosfilt(butter(4, [250 / (SR / 2), 4000 / (SR / 2)], "band", output="sos"), M, axis=0)
        corr_mid = float((bm[:, 0] * bm[:, 1]).sum() / max(np.sqrt((bm[:, 0] ** 2).sum() * (bm[:, 1] ** 2).sum()), 1e-15))
        M = widen(M, Pm["width_db"])
        if Pm.get("air_db") is not None and corr_mid > Pm["air_if_corr"]:
            w = send_return(M, 1.6, 0.02, Pm["air_db"], 7, hp=300, lp=6000); meta["music_air_dB"] = round(10 * np.log10((M ** 2).sum() / (w ** 2).sum()), 1)
            M = M + w
            note(f"music: L/R correlation 250 Hz–4 kHz {corr_mid:.2f} > {Pm['air_if_corr']}: hall air return at {Pm['air_db']:.0f} dB")
        note(f"music: HPF {Pm['hpf']} Hz, EQ {Pm['eq'] or 'flat'}, side +{Pm['width_db']} dB above 200 Hz")
    kM = kpow(M)
    if has_music:
        I_music = integrated(kM)
        if Pm.get("plr"):   # a score whose peaks sit > plr dB over its loudness is tamed on its own bus, not by the master limiter
            M, ml, mn = tp_limit(M, I_music + Pm["plr"], look=0.002, rel=0.12)
            if ml > 0: note(f"music: bus peak control at +{Pm['plr']:.0f} dB over its loudness: {mn} peak(s), up to {ml:.1f} dB"); kM = kpow(M)
    if not has_voice and has_music:   # no voice: the music's own loudness is the reference
        st = lufs(win_mean(kM, 3.0, HOP, n))[:nf]; local = np.maximum(st, I_music - P["local_floor"])
        anchor_t = lambda t: float(local[min(nf - 1, int(round(t / HOP)))])
        note(f"anchor: music {I_music:.1f} LUFS integrated; local anchor = 3 s short-term, floored at −{P['local_floor']:.0f} LU")
    else:
        anchor_t = (lambda t: anchor) if has_voice else None
    # ── SFX: each event alone, classed, moved toward its class
    evs = sorted([dict(e, _i=k) for k, e in enumerate(events)], key=lambda e: e["t"])
    rolemap = roles or {}; placed = []
    for e in evs:
        if e["t"] >= n / SR: continue
        if str(e["_i"]) in rolemap: e["role"] = rolemap[str(e["_i"])]
        elif e["sfx"] in rolemap: e["role"] = rolemap[e["sfx"]]
        c, why = sfx_class(e)
        i, y = place(e, lib, root, cache); j = min(n, i + len(y)); y = y[:j - i] * 10 ** (sfx_db / 20)   # the build's SFX gain
        if not len(y): continue
        lv = event_levels(y); lv["at"] += i / SR
        placed.append({"e": e, "c": c, "why": why, "i": i, "y": y, "lv": lv, "re": lv["fast"] - anchor_t(lv["at"]) if anchor_t else None})
    classes = P["sfx"]["classes"]; moves = {}
    if placed and not anchor_t:
        note("sfx: no voice and no music to anchor on: the events keep their designed levels")
    for c in CLASSES:
        grp = [p for p in placed if p["c"] == c]
        if not grp or c not in classes or not anchor_t: continue
        lo, hi = classes[c]; ctr = (lo + hi) / 2; med = float(np.median([p["re"] for p in grp]))
        # every event moves HALF WAY to the class centre (the class is compressed toward its target, not translated): loud
        # outliers come down most, buried ones come up most, the designer's order is kept; then it is clamped 0.5 LU
        # inside the range. A gesture (same-class events starting within 0.06 s: they blend into one onset) moves as one.
        grp.sort(key=lambda p: p["e"]["t"]); gestures = [[grp[0]]]
        for p in grp[1:]:
            (gestures[-1].append(p) if p["e"]["t"] - gestures[-1][-1]["e"]["t"] <= 0.06 else gestures.append([p]))
        nclamp = 0
        for gs in gestures:
            r = float(np.mean([p["re"] for p in gs])); g = 0.5 * (ctr - r)
            top, bot = max(p["re"] for p in gs) + g, min(p["re"] for p in gs) + g
            if top > hi - 0.5: g -= top - (hi - 0.5); nclamp += 1
            elif bot < lo + 0.5 and top < hi - 0.5: g += min(lo + 0.5 - bot, hi - 0.5 - top); nclamp += 1
            g = float(np.clip(g, -P["sfx"]["max_move"], P["sfx"]["max_move"]))
            for p in gs:   # a low-frequency hit (> 60 % of its energy under 150 Hz) is never pushed UP on its K-weighted
                           # level (phones and laptops barely play it), only pulled down when too loud
                p["g"] = min(g, 0.0) if p["lv"]["lf"] > 0.6 else g
        new_med = float(np.median([p["re"] + p["g"] for p in grp])); moves[c] = new_med - med
        note(f"sfx {c}: n={len(grp)} in {len(gestures)} gesture(s), median {med:+.1f} → {new_med:+.1f} LU re anchor "
             f"(range {lo}…{hi}, centre {ctr:+.1f}; half way per event, {nclamp} gesture(s) clamped at an edge)")
    # a busy passage (events chained ≤ 0.2 s apart: a count-up under a whoosh, a hook of word thocks) keeps the designer's
    # inner balance: rebalancing inside a 200 ms burst is sound design, not mixing, so the passage moves as ONE by the
    # mean of its members' class gains (an LF hit still never goes up)
    if placed:
        order = sorted(placed, key=lambda p: p["e"]["t"]); runs_ = [[order[0]]]
        for p in order[1:]:
            (runs_[-1].append(p) if p["e"]["t"] - runs_[-1][-1]["e"]["t"] <= 0.2 else runs_.append([p]))
        nb = 0
        for rn in runs_:
            if len(rn) < 2: continue
            gm = float(np.mean([p.get("g", 0.0) for p in rn])); nb += 1
            for p in rn: p["g"] = min(gm, 0.0) if p["lv"]["lf"] > 0.6 else gm
        if nb and anchor_t: note(f"sfx: {nb} busy passage(s) (events ≤ 0.2 s apart) moved as one, their inner balance kept")
        for t_keep in keep or ():   # cue-preserving: the passage holding a synced cue whose onset got lost keeps its level
            for rn in runs_:
                if rn[0]["e"]["t"] - 0.05 <= t_keep <= rn[-1]["e"]["t"] + 0.05:
                    for p in rn: p["g"] = 0.0
                    note(f"sfx: passage {rn[0]['e']['t']:.2f}–{rn[-1]['e']['t']:.2f} s keeps its designed level (cue at {t_keep:.3f} s)")
    # a hero that overlaps speech stays under the voice
    vM = lufs(win_mean(kpow(V), 0.4, HOP, n))[:nf] if has_voice else None
    for p in placed:
        p.setdefault("g", 0.0)
        if has_voice:
            a_, b_ = max(0, int((p["lv"]["at"] - 0.05) / HOP)), int((p["lv"]["at"] + min(p["lv"]["len10"], 1.0)) / HOP) + 1
            p["speaking"] = bool(act[a_:b_].any())
            if p["speaking"] and p["c"] == "hero":
                cap = float(vM[a_:b_][act[a_:b_]].min()) + P["sfx"]["hero_under_voice"]
                over = p["lv"]["fast"] + p["g"] - cap
                if over > 0: p["g"] -= over; note(f"sfx hero {p['e']['sfx']} at {p['e']['t']:.2f} s overlaps speech: −{over:.1f} dB (≤ voice {P['sfx']['hero_under_voice']:+.0f} LU)")
    cls_stem = {c: np.zeros((n, 2)) for c in CLASSES if any(p["c"] == c for p in placed) or (c == "detail" and sfx_bus is not None and not placed)}
    for p in placed:   # (a class with no event gets no stem: adding its zeros changed nothing but memory)
        y = p["y"] * 10 ** (p["g"] / 20); cls_stem[p["c"]][p["i"]:p["i"] + len(y)] += y
    if sfx_bus is not None and not placed:   # no events: the pre-placed bus is one detail layer
        cls_stem["detail"] += as_stereo(fitn(sfx_bus, n)) * 10 ** (sfx_db / 20)
    # ambience makes way for the voice
    if has_voice and P["sfx"]["amb_duck"] and "ambience" in cls_stem and cls_stem["ambience"].any():
        r = cone(np.where(close_gaps(act, int(P["music"]["hold"] / HOP)), P["sfx"]["amb_duck"], 0.0), P["sfx"]["amb_duck"] / 12, P["sfx"]["amb_duck"] / 40)
        cls_stem["ambience"] *= 10 ** (-to_samples(r, n) / 20)[:, None]
    # the middle plane: one short shared room, a send per class
    rm = P["sfx"]["room"]; e_dry = e_wet = 0.0
    for c, x in cls_stem.items():
        if x.any() and rm["send"].get(c) is not None:
            w = send_return(x, rm["rt60"], rm["pre"], rm["send"][c], 11); e_dry += float((x ** 2).sum()); e_wet += float((w ** 2).sum())
            cls_stem[c] = x + w
    meta["wet_dry_dB"] = {"voice": None}
    if e_wet > 0: meta["wet_dry_dB"]["sfx"] = round(10 * np.log10(e_dry / e_wet), 1)
    S = sum(cls_stem.values()) if cls_stem else zero2.copy()
    if not class_stems: cls_stem = {}
    ref = anchor if has_voice else I_music
    if ref is not None and P["sfx"].get("plr") and S.any():   # SFX bus peak control: no hit more than plr dB over the anchor
        S2, sl, sn = tp_limit(S, ref + P["sfx"]["plr"], look=0.0015, rel=0.06)
        if sl > 0:
            r = S2 / np.where(np.abs(S) > 1e-12, S, 1.0); r = np.where(np.abs(S) > 1e-12, r, 1.0)
            for c in cls_stem: cls_stem[c] = cls_stem[c] * r
            S = S2; note(f"sfx: bus peak control at anchor +{P['sfx']['plr']:.0f} dB: {sn} peak(s), up to {sl:.1f} dB")
            del r
        del S2
    # a voice-keyed presence carve on the SFX bus, where an SFX covers words
    if has_voice and S.any():
        ps = stft_band(S.mean(1), 1000, 4000)[:nf]
        cut = np.where(act, np.clip(P["sfx"]["carve_snr"] - 10 * np.log10((pv + 1e-12) / (ps + 1e-12)), 0, P["sfx"]["carve_max"]), 0.0)
        cut = uniform_filter1d(cone(cut, P["sfx"]["carve_max"] / 1, P["sfx"]["carve_max"] / 15), 3)
        if cut.max() > 0.1:
            cs = to_samples(cut, n)
            def carved(x):
                lo_, bo_, pr_, ai_ = split4(x)
                return lo_ + bo_ * 10 ** (-0.5 * cs / 20)[:, None] + pr_ * 10 ** (-cs / 20)[:, None] + ai_ * 10 ** (-0.5 * cs / 20)[:, None]
            S = carved(S)
            for c in cls_stem:   # the class stems stay consistent with the bus: the same carve on each
                if cls_stem[c].any(): cls_stem[c] = carved(cls_stem[c])
            note(f"sfx: presence carve under speech, up to −{cut.max():.1f} dB on {(cut > 0.5).sum() * HOP:.2f} s")
            del cs
    # ── music makes way: per-line ducking and a presence carve under narration, or hero dips without one
    Gm, bb_db, carve_db = 0.0, np.zeros(nf), np.zeros(nf)
    heroes = [p for p in placed if p["c"] == "hero"]
    if has_music:
        bands = split4(M)
        pm = stft_band(M.mean(1), 1000, 4000)[:nf]
        M = None                                                    # the bands add up to it; the ride renders from them
        held = close_gaps(act, int(Pm["hold"] / HOP)) if has_voice else np.zeros(nf, bool)
        pre_f, rel_f = max(1, int(Pm["pre"] / HOP)), max(1, int(Pm["release"] / HOP))
        def render_gain(depths):
            """per-line broadband depth (dB) → frame envelope: held regions take the line's depth (a bridged pause takes
            the deeper neighbour), then the look-ahead and release cones"""
            need = np.zeros(nf)
            if has_voice:
                owner = np.full(nf, -1)
                for k, ln in enumerate(lines): owner[int(ln["start"] / HOP):int(ln["end"] / HOP) + 1] = k
                idx = np.nonzero(held)[0]
                if len(idx):
                    lab = owner[idx]; last = -1
                    for q in range(len(idx)):   # forward fill, then the max with the backward fill (the deeper neighbour)
                        if lab[q] >= 0: last = lab[q]
                        lab[q] = last if lab[q] < 0 else lab[q]
                    lab2 = owner[idx].copy(); nxt = -1
                    for q in range(len(idx) - 1, -1, -1):
                        if lab2[q] >= 0: nxt = lab2[q]
                        lab2[q] = nxt if lab2[q] < 0 else lab2[q]
                    need[idx] = np.array([max(depths[a] if a >= 0 else 0, depths[b] if b >= 0 else 0) for a, b in zip(lab, lab2)])
            if has_voice and Pm.get("gap_keep") and lines:   # an unbridged pause < 1.5 s keeps gap_keep of the shallower side
                for k in range(len(lines) - 1):
                    a0, b0 = int(lines[k]["end"] / HOP) + 1, int(lines[k + 1]["start"] / HOP)
                    if 0 < (b0 - a0) * HOP < 1.5:
                        need[a0:b0] = np.maximum(need[a0:b0], Pm["gap_keep"] * min(depths[k], depths[k + 1]))
            dmax = max(max(depths) if len(depths) else 0.0, 1e-3)
            env = cone(need, dmax / pre_f, dmax / rel_f)
            if P["hero_dip"] and heroes:   # a short dip at each hero hit where nobody speaks
                hd = np.zeros(nf)
                for p in heroes:   # from the hit's onset (its first frame within 10 dB of its max), not its loudest 100 ms
                    a_ = max(0, int((p["i"] / SR + p["lv"]["on"]) / HOP) - 1); b_ = a_ + max(2, int(min(p["lv"]["len"], 0.25) / HOP))
                    if not act[max(0, a_ - 5):b_ + 5].any(): hd[a_:b_] = P["hero_dip"]
                env = np.maximum(env, cone(hd, P["hero_dip"], P["hero_dip"] / 25))
            return uniform_filter1d(env, 3)
        def carve_env(bb):
            """a presence cut on voiced frames only (nothing to unmask in a pause), as deep as the 1–4 kHz SNR needs"""
            if not has_voice: return np.zeros(nf)
            pvs, pms = (np.maximum(uniform_filter1d(x, 10), 0) for x in (pv, pm * 10 ** (-bb / 10)))   # 100 ms: syllable level
            snr = 10 * np.log10((pvs + 1e-12) / (pms + 1e-12))
            c = np.where(act, np.clip(Pm["carve_snr"] - snr, 0, Pm["carve_max"]), 0.0)
            c = uniform_filter1d(maximum_filter1d(c, 9), 15)            # a word shares one cut; no 10 ms flutter
            rel = Pm["carve_max"] / (Pm["hold"] / HOP)                  # held pauses keep most of it: no timbre breathing
            return uniform_filter1d(cone(c, Pm["carve_max"] / 4, rel), 3)
        def apply(bb, cv, Gm):
            b_s, c_s = to_samples(bb, n), to_samples(cv, n); act_s = to_samples((act | held).astype(float) if has_voice else np.zeros(nf), n)
            g = lambda extra: 10 ** ((Gm - b_s - extra) / 20)[:, None]
            lo_, bo_, pr_, ai_ = bands
            out = lo_ * g(0); out += bo_ * g(Pm["body"] * act_s + Pm["body_share"] * c_s); out += pr_ * g(c_s); out += ai_ * g(0.35 * c_s)
            return out                                               # (the same sum, left to right, without the temporaries)
        if has_voice and Pm["vmr"]:
            tgt, vmin, vmax = Pm["vmr"]
            raw = [ln["voice"] - integrated(kM, int(ln["start"] * SR), int(ln["end"] * SR), gate=False) for ln in lines]
            d0, c0 = 6.0, 1.0   # model: VMR_k = raw_k − Gm + duck_k + ~1 LU from the carve
            Gm = float(np.median(raw) + d0 + c0 - tgt)                  # the median line on target with a 6 dB duck
            Gm = min(Gm, float(min(raw) + Pm["duck_max"] + c0 - vmin))   # … and the worst line reachable (≥ vmin)
            depths = [float(np.clip(tgt - (r - Gm) - c0, Pm["duck_min"], Pm["duck_max"])) for r in raw]
            for it in range(5):   # closed loop on the rendered music: every line toward the target
                bb_db = render_gain(depths); carve_db = carve_env(bb_db); Mo = apply(bb_db, carve_db, Gm); kMo = kpow(Mo)
                got = [ln["voice"] - integrated(kMo, int(ln["start"] * SR), int(ln["end"] * SR), gate=False) for ln in lines]
                err = [tgt - g_ for g_ in got]
                new = [float(np.clip(d + e_, Pm["duck_min"], Pm["duck_max"])) for d, e_ in zip(depths, err)]
                if max(abs(a_ - b_) for a_, b_ in zip(new, depths)) < 0.25: break
                if it < 4: depths = new
            M = Mo; del Mo, kMo
            for ln, d, g_ in zip(lines, depths, got): ln.update(duck=d, vmr=g_)
            note(f"music: static gain {Gm:+.1f} dB; per-line duck {', '.join(f'{d:.1f}' for d in depths)} dB → VMR "
                 f"{', '.join(f'{g_:.1f}' for g_ in got)} LU (target {tgt}); presence carve up to −{carve_db.max():.1f} dB "
                 f"(mean −{carve_db[held].mean() if held.any() else 0:.1f} dB under speech)")
        else:
            bb_db = render_gain([]); carve_db = np.zeros(nf); M = apply(bb_db, carve_db, 0.0)
            if bb_db.max() > 0: note(f"music: hero dips {P['hero_dip']:.1f} dB at {len(heroes)} hero hit(s) (none under speech)")
        del bands, kM
    meta["music_gain_dB"] = Gm
    # ── fade, sum, one static gain, true peak
    fd = np.ones(n)
    if fade: m_ = int(fade * SR); fd[n - m_:] = np.linspace(1, 0, m_)
    V, M, S = V * fd[:, None], M * fd[:, None], S * fd[:, None]
    for c in cls_stem: cls_stem[c] = cls_stem[c] * fd[:, None]
    Z, g, I2, TP, lim, npk = master(V + M + S, target, tp)
    how = f"static gain {20 * np.log10(g):+.2f} dB" + (f" + true-peak limiter ({npk} peak{'s' * (npk != 1)}, up to {lim:.1f} dB)" if lim > 0 else "")
    note(f"master: {how} → {I2:.2f} LUFS, {TP:.2f} dBTP")
    stems = {"voice": V, "music": M, "sfx": S, **{f"sfx_{c}": cls_stem.get(c, zero2) for c in CLASSES}}   # × g when written
    # each event as heard (for bin/vh qa mix): alone, with its final class gain and the master gain
    lv_out = []
    for p in placed:
        lv = event_levels(p["y"] * 10 ** (p["g"] / 20) * g); lv["at"] += p["i"] / SR; lv["class"] = p["c"]
        lv_out.append((p["e"], lv, p))
    meta.update(anchor=anchor, music_I=I_music, music_corr_mid=corr_mid, lines=lines, sfx_moves=moves, master_gain_dB=float(20 * np.log10(g)),
                limiter_dB=lim, limiter_peaks=npk, lufs=I2, tp=TP, how=how, seconds=round(time.time() - T0, 2),
                events=[{k: v for k, v in q[0].items() if k != "_i"} for q in lv_out], event_levels=[dict(q[1]) for q in lv_out],
                event_gains=[{"i": q[0]["_i"], "t": q[0]["t"], "sfx": q[0]["sfx"], "class": q[2]["c"], "why": q[2]["why"], "gain_dB": round(q[2]["g"], 2),
                              "re_anchor_before": None if q[2]["re"] is None else round(q[2]["re"], 2)} for q in lv_out])
    if timeline: meta["timeline"] = timeline
    return Z, stems, g, meta

def master(X, target, tp):
    """one static gain to `target` LUFS, then the true-peak limiter only if a peak would cross `tp` dBTP (the ceiling is
    lowered and the gain topped up until both hold) → (mix, gain, LUFS, dBTP, most reduction dB, peaks)"""
    I = integrated(kpow(X)); g = 10 ** ((target - I) / 20); Y = X * g
    ceil, lim, npk = tp, 0.0, 0
    for it in range(6):
        Z, lim, npk = tp_limit(Y, ceil)
        TP = 20 * np.log10(max(tp_per_sample(Z).max(), 1e-12)); I2 = integrated(kpow(Z))
        if TP <= tp + 0.02 and abs(I2 - target) <= 0.1: break
        if TP > tp + 0.02: ceil -= TP - tp + 0.02
        if abs(I2 - target) > 0.1: g *= 10 ** ((target - I2) / 20); Y = X * g
    return Z, g, I2, TP, lim, npk

def layered(out, kv):
    if np is None: sys.exit("profile= needs numpy and scipy: run it as bin/vh mix … profile=… (uv provides them)")
    name = kv["profile"]
    if name not in PROFILES: sys.exit(f"profile={name}: use one of {', '.join(PROFILES)}, or none for the default chain")
    if "duck" in kv or "duck_ratio" in kv: sys.exit("duck= / duck_ratio= belong to the default chain: a profile rides the music under each line itself")
    if "events" in kv and "sfx" in kv: sys.exit("give events= (each event classed and levelled) or sfx= (one pre-placed bus), not both")
    for k, need in (("lib", "events"), ("root", "events"), ("roles", "events"), ("keep", "events"), ("timeline", "voice")):
        if k in kv and need not in kv: sys.exit(f"{k}= goes with {need}=")
    if not any(k in kv for k in ("voice", "music", "sfx", "events")): sys.exit("give at least one of voice= music= sfx= events=")
    for k in ("voice", "music", "sfx", "events", "timeline", "roles"):
        if k in kv and not os.path.isfile(kv[k]): sys.exit(f"{k}={kv[k]}: no such file")
    for k in ("lib", "root"):
        if k in kv and not os.path.isdir(kv[k]): sys.exit(f"{k}={kv[k]}: no such folder")
    try: keep = [float(x) for x in kv.get("keep", "").split(",") if x.strip()]
    except ValueError: sys.exit(f"keep={kv['keep']}: comma-separated cue times in seconds")
    dur = float(kv["dur"]) if "dur" in kv else None; fade = float(kv.get("fade", 0))
    if dur is not None and dur <= 0: sys.exit(f"dur={kv['dur']}: must be > 0")
    if fade < 0 or (dur is not None and fade >= dur): sys.exit(f"fade={kv['fade']}: must be ≥ 0 and shorter than dur")
    events = json.load(open(kv["events"])) if "events" in kv else []
    if not isinstance(events, list) or not all(isinstance(e, dict) and "t" in e and "sfx" in e for e in events):
        sys.exit(f"events={kv['events']}: a JSON list of {{\"t\", \"sfx\", …}} events")
    roles = json.load(open(kv["roles"])) if "roles" in kv else None
    if roles is not None and not isinstance(roles, dict): sys.exit(f"roles={kv['roles']}: a JSON object {{\"<event index or sfx name>\": \"hero\", …}}")
    for where, r in [(f"event {k} ({e['sfx']})", e.get("role")) for k, e in enumerate(events)] + [(f"roles {k}", v) for k, v in (roles or {}).items()]:
        if r is not None and r not in CLASSES: sys.exit(f"{where}: role {r!r} is not one of {', '.join(CLASSES)}")
    timeline = json.load(open(kv["timeline"])) if "timeline" in kv else None
    segs = (timeline.get("segments") if isinstance(timeline, dict) else timeline) if timeline is not None else []
    if not isinstance(segs, list) or not all(isinstance(x, dict) and isinstance(x.get("start"), (int, float)) and isinstance(x.get("end"), (int, float)) for x in segs):
        sys.exit(f"timeline={kv['timeline']}: bin/vh tts's timeline.json, or a list of {{\"start\", \"end\", \"text\"}} lines")
    zh = narration_is_zh(timeline, kv.get("voice")) if "voice" in kv else False
    P = profile(name, zh)
    mdb, sdb = float(kv.get("music_db", P["balance"][0])), float(kv.get("sfx_db", P["balance"][1]))
    vdb = float(kv.get("voice_db", 0))
    rd = lambda k: load(kv[k]) if k in kv else None
    buses = {k: rd(k) for k in ("voice", "music", "sfx")}
    for k, x in buses.items():
        if x is not None and x.shape[1] > 2: sys.exit(f"{k}={kv[k]}: {x.shape[1]} channels; give a mono or stereo file")
    if buses["voice"] is not None and vdb: buses["voice"] = buses["voice"] * 10 ** (vdb / 20)
    t0 = time.time()
    Z, stems, g, meta = mixdown(P, buses.pop("voice"), buses.pop("music"), events, kv.get("lib"), kv.get("root"), buses.pop("sfx"), timeline, dur, fade,
                             float(kv.get("lufs", -14)), float(kv.get("tp", -1.65)), roles, mdb, sdb, keep, class_stems="stems" in kv)
    save(out, Z)
    meta.update(balance={"music_db": mdb, "sfx_db": sdb, "voice_db": vdb}, zh=zh, keep=keep, lib=kv.get("lib"), root=kv.get("root"),
                inputs={k: kv[k] for k in ("voice", "music", "sfx", "events", "timeline", "roles") if k in kv})
    if "stems" in kv:
        d = kv["stems"]; os.makedirs(d, exist_ok=True)
        names = ["voice", "music", "sfx"] + [f"sfx_{c}" for c in CLASSES]
        for k in names:   # only what this mix has: a stale stem from an earlier run would mislead qa mix
            p = os.path.join(d, f"{k}.wav")
            if stems[k].any(): save(p, stems[k] * g)
            elif os.path.exists(p): os.remove(p)
        meta["mix"] = os.path.relpath(os.path.abspath(out), os.path.abspath(d))
        with open(os.path.join(d, "meta.json"), "w") as fh:
            json.dump(meta, fh, ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
    what = " + ".join([k for k in ("voice", "music") if k in kv] + ([f"{len(meta['events'])} SFX events"] if events else ["sfx"] if "sfx" in kv else []))
    print(f"{out}  (stereo · profile {name} · {what} · {meta['how']} · measured {meta['lufs']:.2f} LUFS (BS.1770), "
          f"true peak {meta['tp']:.2f} dBTP · {time.time() - t0:.1f} s)" + (f" · stems {kv['stems']}" if "stems" in kv else ""))

if __name__ == "__main__":
    main()
