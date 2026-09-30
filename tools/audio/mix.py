"""Three-bus mix: voice + music + SFX → one stereo track at −14 LUFS, music ducking under the voice.

usage (via bin/vh mix): python tools/audio/mix.py <out.wav> [voice=vo.wav] [music=m.wav] [sfx=s.wav]
                        [music_db=-6] [sfx_db=0] [voice_db=0] [duck=voice|on|off] [duck_ratio=1.6] [lufs=-14] [tp=-1.5]
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
"""
import json, re, subprocess, sys

def loudness(stderr):  # loudnorm's print_format=json block → {"input_i", "input_tp", "input_lra", …}
    return json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", stderr, re.S).group(0))

USAGE = ("usage: bin/vh mix <out.wav> [voice=vo.wav] [music=m.wav] [sfx=s.wav] [music_db=-6] [sfx_db=0] [voice_db=0] "
         "[duck=voice|on|off] [duck_ratio=1.6] [lufs=-14] [tp=-1.5]")
KEYS = ("voice", "music", "sfx", "music_db", "sfx_db", "voice_db", "duck", "duck_ratio", "lufs", "tp")

def main():
    if sys.argv[1:2] in (["-h"], ["--help"]): print(USAGE); sys.exit(0)
    if len(sys.argv) < 2: sys.exit(USAGE)
    bad = [a for a in sys.argv[2:] if "=" not in a or a.split("=", 1)[0] not in KEYS]   # a bare path or a typo, not a traceback
    if bad: sys.exit(f"{USAGE}\nnot key=value, or not a known key: {' '.join(bad)}")
    out = sys.argv[1]; kv = dict(a.split("=", 1) for a in sys.argv[2:])
    for k in ("music_db", "sfx_db", "voice_db", "duck_ratio", "lufs", "tp"):
        if k in kv:
            try: float(kv[k])
            except ValueError: sys.exit(f"{k}={kv[k]}: not a number")
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

if __name__ == "__main__":
    main()
