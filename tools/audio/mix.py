"""Three-bus mix: voice + music + SFX → one track at −14 LUFS, music ducking under voice and key SFX.

usage (via bin/vh mix): python tools/audio/mix.py <out.wav> [voice=vo.wav] [music=m.wav] [sfx=s.wav]
                        [music_db=-6] [sfx_db=0] [voice_db=0] [duck=on|off] [lufs=-14]
Any bus may be omitted. With duck=on the music is side-chain compressed by (voice + sfx), so a narration line
or a "ding" is always heard; this is the "music makes way" rule from playbook/04-audio.md.
"""
import subprocess, sys

def main():
    out = sys.argv[1]; kv = dict(a.split("=", 1) for a in sys.argv[2:])
    buses = [(k, kv[k]) for k in ("voice", "music", "sfx") if kv.get(k)]
    if not buses: sys.exit("give at least one of voice= music= sfx=")
    ins, idx = [], {}
    for k, p in buses: idx[k] = len(ins) // 2; ins += ["-i", p]
    g = lambda k, d: float(kv.get(f"{k}_db", d))
    f = []
    for k, _ in buses:
        f.append(f"[{idx[k]}:a]aresample=48000,aformat=channel_layouts=mono,volume={g(k, -6 if k == 'music' else 0)}dB[{k}]")
    fg = [k for k, _ in buses if k != "music"]           # foreground buses that the music should make way for
    if "music" in idx and fg and kv.get("duck", "on") == "on":
        if len(fg) == 2:
            f.append("[voice]asplit[v1][v2]"); f.append("[sfx]asplit[s1][s2]")
            f.append("[v1][s1]amix=inputs=2:normalize=0[key]"); fg_out = ["[v2]", "[s2]"]
        else:
            f.append(f"[{fg[0]}]asplit[k0][f0]"); f.append("[k0]anull[key]"); fg_out = ["[f0]"]
        f.append("[music][key]sidechaincompress=threshold=0.02:ratio=6:attack=15:release=350:makeup=1[duck]")
        tracks = ["[duck]"] + fg_out
    else:
        tracks = [f"[{k}]" for k, _ in buses]
    lufs = kv.get("lufs", "-14")
    f.append("".join(tracks) + f"amix=inputs={len(tracks)}:duration=longest:normalize=0,loudnorm=I={lufs}:TP=-1.5:LRA=11[out]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(f), "-map", "[out]", "-ar", "48000", out]
    subprocess.run(cmd, check=True)
    print(f"{out}  ({' + '.join(k for k, _ in buses)}{', ducked' if 'music' in idx and fg and kv.get('duck', 'on') == 'on' else ''}, {lufs} LUFS)")

if __name__ == "__main__":
    main()
