"""Three-bus mix: voice + music + SFX → one stereo track at −14 LUFS, music ducking under voice and key SFX.

usage (via bin/vh mix): python tools/audio/mix.py <out.wav> [voice=vo.wav] [music=m.wav] [sfx=s.wav]
                        [music_db=-6] [sfx_db=0] [voice_db=0] [duck=on|voice|off] [duck_ratio=6] [lufs=-14] [tp=-1.5]
Any bus may be omitted. With duck=on the music is side-chain compressed by (voice + sfx), so a narration line
or a "ding" is always heard ("music makes way", playbook/04-audio.md). duck=voice keys on the voice only; with many
SFX and no voice use duck=off or a low duck_ratio (2–3), or the music pumps on every hit.
Stereo is preserved (mono buses are centred). Loudness uses TWO-PASS linear loudnorm: pass 1 measures, pass 2
applies one static gain (true-peak limited), so a cinematic score keeps its dynamics (LRA) instead of being
squashed by single-pass dynamic normalisation.
"""
import json, re, subprocess, sys

def main():
    out = sys.argv[1]; kv = dict(a.split("=", 1) for a in sys.argv[2:])
    buses = [(k, kv[k]) for k in ("voice", "music", "sfx") if kv.get(k)]
    if not buses: sys.exit("give at least one of voice= music= sfx=")
    ins, idx = [], {}
    for k, p in buses: idx[k] = len(ins) // 2; ins += ["-i", p]
    g = lambda k, d: float(kv.get(f"{k}_db", d))
    f = []
    for k, _ in buses:
        f.append(f"[{idx[k]}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g(k, -6 if k == 'music' else 0)}dB[{k}]")
    fg = [k for k, _ in buses if k != "music"]
    duck = kv.get("duck", "on"); keys = [k for k in fg if duck == "on" or (duck == "voice" and k == "voice")]
    ducked = "music" in idx and keys and duck != "off"
    if ducked:
        if len(keys) == 2:
            f += ["[voice]asplit[v1][v2]", "[sfx]asplit[s1][s2]", "[v1][s1]amix=inputs=2:normalize=0[key]"]; fg_out = ["[v2]", "[s2]"]
        else:
            f += [f"[{keys[0]}]asplit[key][f0]"]; fg_out = ["[f0]"] + [f"[{k}]" for k in fg if k not in keys]
        # apad: the compressor stops when its key ends, so a short voice/SFX bus used to cut the music off there
        f.append(f"[key]apad[keyp];[music][keyp]sidechaincompress=threshold=0.02:ratio={kv.get('duck_ratio', '6')}:attack=15:release=350:makeup=1[duck]")
        tracks = ["[duck]"] + fg_out
    else:
        tracks = [f"[{k}]" for k, _ in buses]
    pre = ";".join(f) + ";" + "".join(tracks) + f"amix=inputs={len(tracks)}:duration=longest:normalize=0"
    lufs, tp = kv.get("lufs", "-14"), kv.get("tp", "-1.5")
    # pass 1: measure
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", *ins, "-filter_complex",
                        pre + f",loudnorm=I={lufs}:TP={tp}:LRA=20:print_format=json[out]", "-map", "[out]", "-f", "null", "-"],
                       capture_output=True, text=True, check=True)
    m = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S).group(0))
    # pass 2: apply one linear gain (loudnorm linear mode), true-peak limited
    ln = (f"loudnorm=I={lufs}:TP={tp}:LRA=20:linear=true:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", pre + f",{ln}[out]", "-map", "[out]", "-ar", "48000", out], check=True)
    print(f"{out}  (stereo · {' + '.join(k for k, _ in buses)}{f', ducked by {chr(43).join(keys)}' if ducked else ''} · {lufs} LUFS two-pass linear · "
          f"input {m['input_i']} LUFS, LRA {m['input_lra']} LU)")

if __name__ == "__main__":
    main()
