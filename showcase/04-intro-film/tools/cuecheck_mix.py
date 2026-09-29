"""Cue check on the FINAL mix: every scored hit (music.beats.json) and every placed SFX (events.json)
must have an audible onset within 1 frame (33.3 ms) of its grid time. Writes audio/check/cuecheck-mix.txt."""
import json, numpy as np, librosa
y, sr = librosa.load("audio/mix.wav", sr=48000, mono=True)
on = librosa.onset.onset_detect(y=y, sr=sr, hop_length=128, backtrack=False, units="time", delta=0.04)
bm = json.load(open("audio/music.beats.json")); ev = json.load(open("audio/events.json"))
cues = [(h["t"], "music:" + h["what"]) for h in bm["hits"] if not any(k in h["what"] for k in ("riser", "swell"))]
cues += [(e["t"], "sfx:" + e["sfx"]) for e in ev if e.get("gain_db", 0) > -18 and e["sfx"] not in ("whoosh", "swish_rev", "riser")]  # swells have no transient onset
rows, errs = [], []
for t, what in sorted(cues):
    d = on - t; near = d[np.argmin(np.abs(d))] if len(d) else 9
    errs.append(abs(near)); rows.append(f"{t:8.3f}  {near*1000:+7.1f} ms  {abs(near)*30:5.2f} fr  {'OK ' if abs(near) <= 1/30 else 'OFF'}  {what}")
errs = np.array(errs)
head = f"cue check on audio/mix.wav: {len(errs)} cues, within 1 frame: {(errs <= 1/30).sum()}, median {np.median(errs)*1000:.1f} ms, max {errs.max()*1000:.1f} ms\n"
open("audio/check/cuecheck-mix.txt", "w").write(head + "\n".join(rows) + "\n"); print(head.strip())
print("\n".join(r for r in rows if "OFF" in r))
