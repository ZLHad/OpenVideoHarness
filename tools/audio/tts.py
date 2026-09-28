"""Voiceover synthesis with pluggable providers → per-line WAVs, a joined voiceover and a timeline.

usage (via bin/vh tts): python tools/audio/tts.py <project_dir> [--provider qwen] [--voice V] [--lang zh|en]
                                                 [--gap 0.25] [--instruct "calm, warm"]

Input  <project>/audio/script.txt — one spoken line per row (a line = one caption / cue unit).
       Blank lines and '#' comments are ignored. Optional id prefix "@hook ".
       Bilingual lines use " || ":   @hook 一句话，做出一支片子。 || One sentence in, one film out.
       --lang picks which side is spoken (zh = left, en = right); both sides go into the timeline for captions.
       A line with only one side is spoken as-is.
Output <project>/audio/vo/<lang>/NN.wav, audio/voiceover.<lang>.wav (mono 48 kHz, joined with --gap s silence),
       audio/timeline.<lang>.json, and audio/timeline.json + audio/voiceover.wav as copies of the latest run:
       {"provider","voice","lang","duration","segments":[{"id","text","zh","en","start","end","file","words"?}]}
       start/end are exact (measured from each synthesized file). Captions: bin/vh captions <project>.

Providers (API keys come from environment variables only, never from files):
  qwen        DEFAULT. Local open-source Qwen3-TTS (Apache-2.0) on Apple Silicon via mlx-audio, offline and free.
              Model: QWEN_TTS_MODEL (default mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit, ~2 GB download
              on first use). Voices — zh: Serena (warm female, default), Vivian, Uncle_Fu, Dylan (Beijing),
              Eric (Sichuan); en: Ryan (default), Aiden. --instruct needs a 1.7B CustomVoice model.
  say         macOS built-in, offline, free, draft quality. zh: Tingting (default) … en: Samantha.
  edge        Microsoft Edge online voices via the unofficial edge-tts package (free; may break).
  dashscope   Cloud Qwen3-TTS on Alibaba Cloud Model Studio (阿里云百炼): DASHSCOPE_API_KEY,
              DASHSCOPE_TTS_MODEL (default qwen3-tts-flash), voice e.g. Cherry, DASHSCOPE_BASE_URL (intl).
  elevenlabs  ELEVENLABS_API_KEY; --voice <voice_id>; ELEVENLABS_MODEL (default eleven_multilingual_v2);
              returns character-level timing.
"""
import argparse, base64, json, os, shutil, subprocess, sys, tempfile, urllib.request, wave
from pathlib import Path

SR = 48000

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)

def to_wav(src: Path, dst: Path):
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", str(SR), str(dst)])

def duration(p: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)

# ---------- providers: each writes a WAV at `out` and may return word/char timings ----------

_QWEN = {}
def p_qwen(text, voice, out: Path, tmp: Path, lang, instruct=None):
    import numpy as np
    from mlx_audio.tts.utils import load_model  # provided by `uv run --with mlx-audio`
    model_id = os.environ.get("QWEN_TTS_MODEL", "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit")
    if model_id not in _QWEN:
        print(f"  loading {model_id} (first run downloads it) …", flush=True)
        _QWEN[model_id] = load_model(model_id)
    model = _QWEN[model_id]
    zh = lang.startswith("zh")
    kw = dict(text=text, speaker=voice or ("Serena" if zh else "Ryan"), language="Chinese" if zh else "English")
    if instruct:
        kw["instruct"] = instruct
    results = list(model.generate_custom_voice(**kw))
    audio = np.concatenate([np.asarray(r.audio, dtype=np.float32).reshape(-1) for r in results])
    sr = int(getattr(results[0], "sample_rate", 0) or getattr(model, "sample_rate", 24000))
    raw = tmp / "qwen.wav"
    with wave.open(str(raw), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
    to_wav(raw, out)
    return None

def p_say(text, voice, out: Path, tmp: Path, lang, instruct=None):
    aiff = tmp / "say.aiff"
    run(["say", "-v", voice or ("Tingting" if lang.startswith("zh") else "Samantha"), "-o", str(aiff), text])
    to_wav(aiff, out)
    return None

def p_edge(text, voice, out: Path, tmp: Path, lang, instruct=None):
    mp3 = tmp / "edge.mp3"
    voice = voice or ("zh-CN-XiaoxiaoNeural" if lang.startswith("zh") else "en-US-AriaNeural")
    run(["edge-tts", "--voice", voice, "--text", text, "--write-media", str(mp3)])
    to_wav(mp3, out)
    return None

def p_elevenlabs(text, voice, out: Path, tmp: Path, lang, instruct=None):
    key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit("set ELEVENLABS_API_KEY")
    voice = voice or sys.exit("--voice <voice_id> is required for elevenlabs")
    body = json.dumps({"text": text, "model_id": os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")}).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128",
                                 data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    mp3 = tmp / "el.mp3"; mp3.write_bytes(base64.b64decode(resp["audio_base64"])); to_wav(mp3, out)
    a = resp.get("alignment") or {}
    return [{"w": c, "start": s, "end": e} for c, s, e in
            zip(a.get("characters", []), a.get("character_start_times_seconds", []), a.get("character_end_times_seconds", []))
            if c.strip()]

def p_dashscope(text, voice, out: Path, tmp: Path, lang, instruct=None):
    import dashscope  # provided by `uv run --with dashscope`
    key = os.environ.get("DASHSCOPE_API_KEY") or sys.exit("set DASHSCOPE_API_KEY")
    if os.environ.get("DASHSCOPE_BASE_URL"):
        dashscope.base_http_api_url = os.environ["DASHSCOPE_BASE_URL"]
    resp = dashscope.MultiModalConversation.call(
        model=os.environ.get("DASHSCOPE_TTS_MODEL", "qwen3-tts-flash"), api_key=key, text=text,
        voice=voice or "Cherry", language_type="Chinese" if lang.startswith("zh") else "English", stream=False)
    url = resp.output.audio.url if getattr(resp, "output", None) else sys.exit(f"dashscope error: {resp}")
    raw = tmp / "ds.wav"; urllib.request.urlretrieve(url, raw); to_wav(raw, out)
    return None

PROVIDERS = {"qwen": p_qwen, "say": p_say, "edge": p_edge, "dashscope": p_dashscope, "elevenlabs": p_elevenlabs}

def read_script(path: Path):
    segs = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        sid = None
        if line.startswith("@") and " " in line:
            sid, line = line[1:].split(" ", 1)
        zh, _, en = (p.strip() for p in line.partition("||"))
        segs.append({"id": sid or f"s{len(segs)+1:02d}", "zh": zh, "en": en})
    return segs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--provider", default="qwen", choices=PROVIDERS)
    ap.add_argument("--voice"); ap.add_argument("--lang", default="zh", choices=["zh", "en"])
    ap.add_argument("--gap", type=float, default=0.25); ap.add_argument("--instruct")
    a = ap.parse_args()
    proj = Path(a.project).resolve(); audio = proj / "audio"; script = audio / "script.txt"
    if not script.exists():
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("# 一行一句（= 一条字幕 / 一个 cue）。双语用 ' || ' 分隔：中文 || English。可选 @id 前缀。\n"
                          "@hook 一句话，做出一支片子。 || One sentence in, one film out.\n", encoding="utf-8")
        sys.exit(f"wrote a sample {script} — edit it and re-run")
    segs = read_script(script)
    vo = audio / "vo" / a.lang; shutil.rmtree(vo, ignore_errors=True); vo.mkdir(parents=True)
    silence = vo / "_gap.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", f"{a.gap}", str(silence)])
    t, parts = 0.0, []
    with tempfile.TemporaryDirectory() as td:
        for i, s in enumerate(segs):
            spoken = (s["zh"] if a.lang == "zh" else s["en"]) or s["zh"] or s["en"]
            out = vo / f"{i+1:02d}.wav"
            words = PROVIDERS[a.provider](spoken, a.voice, out, Path(td), a.lang, a.instruct)
            d = duration(out)
            s.update(text=spoken, start=round(t, 3), end=round(t + d, 3), file=str(out.relative_to(proj)))
            if words:
                s["words"] = [{"w": w["w"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in words]
            parts += [out, silence]; t += d + a.gap
            print(f"  {s['id']:<8} {s['start']:6.2f}–{s['end']:6.2f}s  {spoken}", flush=True)
    lst = vo / "_concat.txt"; lst.write_text("".join(f"file '{p.name}'\n" for p in parts[:-1]))
    joined = audio / f"voiceover.{a.lang}.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "pcm_s16le", str(joined)])
    tl = {"provider": a.provider, "voice": a.voice, "lang": a.lang, "duration": round(duration(joined), 3), "segments": segs}
    body = json.dumps(tl, ensure_ascii=False, indent=2)
    (audio / f"timeline.{a.lang}.json").write_text(body, encoding="utf-8")
    (audio / "timeline.json").write_text(body, encoding="utf-8")
    shutil.copyfile(joined, audio / "voiceover.wav")
    print(f"→ {joined.relative_to(proj)} ({tl['duration']}s) · audio/timeline.{a.lang}.json · captions: bin/vh captions {a.project}")

if __name__ == "__main__":
    main()
