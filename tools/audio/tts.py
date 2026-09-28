"""Voiceover synthesis with pluggable providers → per-line WAVs + voiceover.wav + timeline.json.

usage (via bin/vh tts): python tools/audio/tts.py <project_dir> [--provider say] [--voice V] [--gap 0.25] [--lang zh]

Input:  <project>/audio/script.txt — one spoken line per row (a line = a caption / cue unit).
        Blank lines and lines starting with '#' are ignored. Optional id prefix: "@hook 为什么信号会变调？".
Output: <project>/audio/vo/NN.wav, <project>/audio/voiceover.wav (mono 48 kHz, lines joined with --gap
        seconds of silence), and <project>/audio/timeline.json:
        {"provider","voice","duration","segments":[{"id","text","start","end","file","words":[...]?}]}
Segment start/end are exact (measured from each synthesized file). Word/char timing is filled when the
provider returns it (elevenlabs, edge); otherwise run a forced aligner later (see playbook/04-audio.md).

Providers (API keys are read from environment variables only, never from files):
  say         macOS built-in, offline, free. Voices: `say -v '?'` (zh: Tingting, Eddy, Flo …). Draft quality.
  edge        Microsoft Edge online voices via the unofficial edge-tts package (free; may break). zh-CN-XiaoxiaoNeural …
  elevenlabs  ELEVENLABS_API_KEY; voice = voice_id; model via ELEVENLABS_MODEL (default eleven_multilingual_v2).
              Uses /with-timestamps → character-level timing.
  dashscope   DASHSCOPE_API_KEY (Alibaba Cloud Model Studio / 阿里云百炼); model via DASHSCOPE_TTS_MODEL
              (default qwen3-tts-flash); voice e.g. Cherry; DASHSCOPE_BASE_URL for the international endpoint.
  mlx         Local Qwen3-TTS on Apple Silicon via mlx-audio. Needs MLX_TTS_MODEL
              (e.g. mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit) — downloads GB-scale weights on first use.
"""
import argparse, base64, json, os, shutil, subprocess, sys, tempfile, urllib.request
from pathlib import Path

SR = 48000

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)

def to_wav(src: Path, dst: Path):
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", str(SR), str(dst)])

def duration(p: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)

# ---------- providers: each writes a WAV at `out` and returns optional word/char timings ----------

def p_say(text, voice, out: Path, tmp: Path, lang):
    aiff = tmp / "say.aiff"
    run(["say", "-v", voice or ("Tingting" if lang.startswith("zh") else "Samantha"), "-o", str(aiff), text])
    to_wav(aiff, out)
    return None

def p_edge(text, voice, out: Path, tmp: Path, lang):
    mp3, vtt = tmp / "edge.mp3", tmp / "edge.vtt"
    voice = voice or ("zh-CN-XiaoxiaoNeural" if lang.startswith("zh") else "en-US-AriaNeural")
    run(["edge-tts", "--voice", voice, "--text", text, "--write-media", str(mp3), "--write-subtitles", str(vtt)])
    to_wav(mp3, out)
    return None  # edge-tts subtitles are sentence-level in recent versions; keep segment timing

def p_elevenlabs(text, voice, out: Path, tmp: Path, lang):
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

def p_dashscope(text, voice, out: Path, tmp: Path, lang):
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

def p_mlx(text, voice, out: Path, tmp: Path, lang):
    model = os.environ.get("MLX_TTS_MODEL") or sys.exit("set MLX_TTS_MODEL (e.g. mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit); first run downloads GB-scale weights")
    run([sys.executable, "-m", "mlx_audio.tts.generate", "--model", model, "--text", text,
         "--voice", voice or "Vivian", "--output_path", str(tmp), "--file_prefix", "mlx"])
    wav = sorted(tmp.glob("mlx*.wav"))[-1]; to_wav(wav, out)
    return None

PROVIDERS = {"say": p_say, "edge": p_edge, "elevenlabs": p_elevenlabs, "dashscope": p_dashscope, "mlx": p_mlx}

def read_script(path: Path):
    segs = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        sid = None
        if line.startswith("@") and " " in line:
            sid, line = line[1:].split(" ", 1)
        segs.append({"id": sid or f"s{len(segs)+1:02d}", "text": line.strip()})
    return segs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--provider", default="say", choices=PROVIDERS)
    ap.add_argument("--voice"); ap.add_argument("--gap", type=float, default=0.25); ap.add_argument("--lang", default="zh")
    a = ap.parse_args()
    proj = Path(a.project).resolve(); audio = proj / "audio"; script = audio / "script.txt"
    if not script.exists():
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("# 一行一句旁白（= 一条字幕 / 一个 cue）。可选 @id 前缀。\n@hook 为什么卫星的信号会变调？\n", encoding="utf-8")
        sys.exit(f"wrote a sample {script} — edit it and re-run")
    segs = read_script(script)
    vo = audio / "vo"; shutil.rmtree(vo, ignore_errors=True); vo.mkdir(parents=True)
    t, parts = 0.0, []
    silence = vo / "_gap.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", f"{a.gap}", str(silence)])
    with tempfile.TemporaryDirectory() as td:
        for i, s in enumerate(segs):
            out = vo / f"{i+1:02d}.wav"
            words = PROVIDERS[a.provider](s["text"], a.voice, out, Path(td), a.lang)
            d = duration(out)
            s.update(start=round(t, 3), end=round(t + d, 3), file=str(out.relative_to(proj)))
            if words:
                s["words"] = [{"w": w["w"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in words]
            parts += [out, silence]; t += d + a.gap
            print(f"  {s['id']:<8} {s['start']:6.2f}–{s['end']:6.2f}s  {s['text']}")
    lst = vo / "_concat.txt"; lst.write_text("".join(f"file '{p.name}'\n" for p in parts[:-1]))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "pcm_s16le", str(audio / "voiceover.wav")])
    tl = {"provider": a.provider, "voice": a.voice, "duration": round(duration(audio / "voiceover.wav"), 3), "segments": segs}
    (audio / "timeline.json").write_text(json.dumps(tl, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"→ {audio/'voiceover.wav'}  ({tl['duration']}s)   timeline: {audio/'timeline.json'}")

if __name__ == "__main__":
    main()
