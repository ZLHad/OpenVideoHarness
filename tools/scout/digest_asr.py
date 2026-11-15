"""One chunk of bin/vh ref digest transcribed by a local Whisper (mlx-whisper, Apple Silicon); bin/vh runs it through uv.

usage: uv run --no-project --with mlx-whisper python tools/scout/digest_asr.py <chunk.wav> [lang]
Prints {"language", "segments": [{"start", "end", "text"}]}: Whisper's own segments, times from the chunk's start. The
model is WHISPER_MODEL (default mlx-community/whisper-large-v3-turbo, the one bin/vh tts --align local uses); digest sets
HF_HUB_OFFLINE=1 unless --fetch-model, so a model not on this machine fails here instead of downloading. Each previous
segment is not fed into the next (condition_on_previous_text off), which keeps one misheard line from running on.
"""
import json, os, sys

import mlx_whisper


def main():
    wav, lang = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "") or None
    r = mlx_whisper.transcribe(wav, path_or_hf_repo=os.environ.get("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo"),
                               language=lang, condition_on_previous_text=False)
    segs = [{"start": round(float(s["start"]), 3), "end": round(float(s["end"]), 3), "text": str(s["text"]).strip()}
            for s in r.get("segments", []) if str(s.get("text", "")).strip()]
    print(json.dumps({"language": r.get("language"), "segments": segs}, ensure_ascii=False))


if __name__ == "__main__":
    main()
