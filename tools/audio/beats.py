"""Beat grid for a music track → beats.json (feeds bpm/offset in engines and cut timing).

usage (via bin/vh beats): python tools/audio/beats.py <audio> [out.json]
Output: {"bpm","offset","beats":[s…],"downbeats":[s…],"duration","note"}
downbeats assume 4/4 and start on the first detected beat — check them against the music and shift if needed.
On calm music the detected BPM is an imposed metronome; don't hard-cut to it (see playbook/04-audio.md).
For higher-accuracy downbeats use beat_this (CPJKU) instead.
"""
import json, sys
from pathlib import Path
import librosa  # provided by `uv run --with librosa`

def main():
    src = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(src).with_suffix(".beats.json")
    y, sr = librosa.load(src, sr=22050, mono=True)
    tempo, frames = librosa.beat.beat_track(y=y, sr=sr, units="frames")
    beats = [round(float(t), 3) for t in librosa.frames_to_time(frames, sr=sr)]
    bpm = round(float(tempo[0] if hasattr(tempo, "__len__") else tempo), 2)
    res = {"bpm": bpm, "offset": beats[0] if beats else 0.0, "beats": beats, "downbeats": beats[::4],
           "duration": round(len(y) / sr, 3),
           "note": "downbeats assume 4/4 from the first beat; verify by ear and shift if needed"}
    out.write_text(json.dumps(res, indent=2))
    print(f"bpm {bpm}  offset {res['offset']}s  {len(beats)} beats → {out}")

if __name__ == "__main__":
    main()
