"""Voiceover synthesis with pluggable providers → per-line WAVs, a joined voiceover and a timeline.

usage (via bin/vh tts): python tools/audio/tts.py <project_dir> [--provider qwen] [--voice V] [--lang zh|en]
                                                 [--gap 0.25] [--instruct "calm, warm"]
                                                 [--beats music.beats.json [--snap beat|half|downbeat]] [--lead 0.0]
                                                 [--align gemini [--min-sim 0.85] [--vocab "术语,Term"]]
                                                 [--join none|block|all] [--resume]
       (via bin/vh voices): python tools/audio/tts.py voices list [lang] | design "<description>" | delete <voice_id>

Input  <project>/audio/script.txt — one spoken line per row (a line = one caption / cue unit).
       Blank lines and '#' comments are ignored. Optional id prefix "@hook ".
       Bilingual lines use " || ":   @hook 一句话，做出一支片子。 || One sentence in, one film out.
       Per-line direction in [brackets] right after the id, for the voices that can act (gemini; qwen 1.7B instruct):
                                      @hook [惊讶地抛出问题，语速快，"一句话"重读] 一句话，做出一支片子。 || …
       It is added to --instruct for that line only, and never reaches the captions.
       --beats: start every line on the next grid point of a beat map (bin/vh music / bin/vh beats output) instead of a
       fixed --gap, so narration rides the music; --snap picks the grid. --lead: the earliest start of line 1, with or
       without --beats (without, line 1 starts there after digital silence: a narration that comes in late).
       A single line can pick its own grid with @id:downbeat (or :beat, :half), e.g. the answer that lands on the drop.
       A map without the chosen grid is an error; when the narration outlives the grid, the lines past its end follow
       --gap, and that is said once.
       --lang picks which side is spoken (zh = left, en = right); both sides go into the timeline for captions.
       Without --lang it is zh, unless no line has a Chinese side: an English-only script is spoken in English
       (English voice, English ASR, voiceover.en.wav). A mixed script keeps one narrator, so it stays zh.
       A line with only one side is spoken as-is; for captions it is English when it has no CJK characters, else
       Chinese ("Claude Code ||" keeps a Latin-only line on the Chinese side; punctuation only, like "……", goes
       with the one-sided line before it).
       Dialogue (two speakers): a header line maps speaker labels to voices, then a line starts with its label
       (after the optional @id and [direction]; a [direction] right after the label works too, two are joined):
                                      @speakers A=Kore B=Puck
                                      @q1 A: 你猜这支片子手写了几行代码？ || Guess how many lines we wrote by hand?
                                      @a1 B: [压低声音，卖个关子] 一行都没有。 |oh| || Not a single one. |oh|
       Labels count only when declared in @speakers (header first), so an ordinary "注意：" line stays narration.
       Voice ids with a space (MiniMax's "Chinese (Mandarin)_…") cannot go into @speakers.
       "A=Tingting,B=Meijia" as --voice overrides the header (e.g. a `say` draft of a gemini dialogue).
       |reaction| markers (no space just inside the pipes) are listener backchannels that the other speaker voices in
       a gemini conversation; every other path and the captions drop them, like the <tags> below. Only a script with
       an @speakers header has backchannels: elsewhere |x| is ordinary text (范围是 |x| keeps it).
       Silence the provider leaves before and after a line (below −50 dBFS) is trimmed to 30 ms / 80 ms, so the gap
       between lines is --gap (or the beat grid) and a snapped line's voice starts on the beat; --keep-edges keeps it.
       With --join, only the edges of each block are trimmed; pauses inside a block are the delivery.
Output <project>/audio/vo/<lang>/NN.wav, audio/voiceover.<lang>.wav (mono 48 kHz, joined with --gap s silence),
       audio/timeline.<lang>.json, and audio/timeline.json + audio/voiceover.wav as copies of the latest run:
       {"provider","voice","lang","duration","segments":[{"id","text","zh","en","start","end","file","words"?,
        "speaker"?,"asr"?}]}
       start/end are exact (measured from each synthesized file). Captions: bin/vh captions <project>.

Alignment check (--align gemini, any provider): every line is transcribed by gemini-3.5-transcribe with word
       timestamps (GEMINI_API_KEY; ≈ $0.005 per audio minute on the paid tier, free on the free tier). It writes
       words [{w, start, end}] in script spelling (the same shape elevenlabs gives, so bin/vh captions can time cues),
       and asr {text, similarity, head, tail, flag?}. A line is flagged when the ASR text drifts from the script
       (similarity < --min-sim, default 0.85) or there is more than 1 s of audio before the first / after the last word
       (the local Qwen 0.6B once ran on for 10 s after a short English line). Flagged lines are re-transcribed once
       with custom_vocabulary (Latin terms from the script + --vocab) — the API rejects custom_vocabulary together with
       word timestamps, so it cannot be used in the timing pass. ASR timestamps come in 0.1 s steps; numbers may come
       back normalised ("二十六" → "26"), which lowers similarity without being an error. GEMINI_ASR_MODEL,
       GEMINI_ASR_LANGS (default cmn-Hans-CN / en-US) override the model and language hints.
       The key is checked before anything is synthesized. The voiceover and timeline are written right after synthesis,
       so a transcribe call that fails for good (a daily quota, the network, a bad file) cannot lose the take: the line
       keeps its measured timing and gets asr {"error"}, the command exits 1, and --resume continues that run: it
       synthesizes only the files the run did not get to (after a synthesis failure too), reuses the ASR of the lines
       that succeeded (vo/<lang>/*.asr.json) and redoes the rest; a file synthesized again gets a fresh transcription.
       The run's script, provider, voice, --instruct / GEMINI_TTS_STYLE and join mode are recorded in vo/<lang>/_run.json;
       --resume refuses a mismatch and names it (the timing flags may change). A plain run (no --align, no --join) that
       failed midway continues the same way, and a finished plain run gets --align gemini without synthesizing again.
Joined synthesis (--join block|all): consecutive lines go into one request — `block` = runs of lines between blank
       lines in script.txt, `all` = the whole script (8,192 input tokens per gemini request). Prosody flows across
       lines, but a line can no longer be re-run or beat-snapped on its own: only each block's start snaps to the grid
       (with its first line's @id:grid), lines inside keep their natural spacing. Line boundaries are recovered from
       word timestamps, so --join turns --align gemini on; vo/<lang>/NN.wav are then cuts of the block audio.
       A gemini dialogue defaults to --join block (mode "conversational", ≤ 2 speakers, library voices only);
       designed voice_… ids or a third speaker fall back to one request per turn. When the transcription of a block
       fails, the block is kept whole (vo/<lang>/_blockNN.wav; its lines share the block's span in the timeline, with
       asr {"error"}) and --resume re-transcribes and cuts it without synthesizing again.

Providers (API keys come from environment variables only, never from files):
  qwen        DEFAULT. Local open-source Qwen3-TTS (Apache-2.0) on Apple Silicon via mlx-audio, offline and free.
              Model: QWEN_TTS_MODEL (default mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit, ~2 GB download
              on first use). Voices — zh: Serena (warm female, default), Vivian, Uncle_Fu, Dylan (Beijing),
              Eric (Sichuan); en: Aiden (default), Ryan (slower, and the 0.6B model often runs on or mumbles
              for seconds with it). --instruct needs a 1.7B CustomVoice model.
  say         macOS built-in, offline, free, draft quality. zh: Tingting (default) … en: Samantha.
  edge        Microsoft Edge online voices via the unofficial edge-tts package (free; may break).
  dashscope   Cloud Qwen3-TTS on Alibaba Cloud Model Studio (阿里云百炼): DASHSCOPE_API_KEY,
              DASHSCOPE_TTS_MODEL (default qwen3-tts-flash), voice e.g. Cherry, DASHSCOPE_BASE_URL (intl).
  elevenlabs  ELEVENLABS_API_KEY; --voice <voice_id>; ELEVENLABS_MODEL (default eleven_multilingual_v2);
              returns character-level timing.
  gemini      Google Gemini 3.8 Flash TTS (gemini-3.8-flash-tts, released 2026-09-23): GEMINI_API_KEY from Google AI
              Studio. Free tier (its content may be used to improve Google products) and paid tier: $0.50 / 1M text
              tokens in, $9 / 1M audio tokens out (≈ $0.00225 per 10 s) through 2026-12-31, doubling to $1 / $18
              (≈ $0.0045 per 10 s) from 2027-01-01. 130 languages incl. Mandarin, detected from the text; 8,192 input
              tokens per request. --voice: one of the 30 studio voices (default Kore; Puck, Charon, Fenrir, Leda, Aoede,
              Zephyr …; each speaks every supported language), a library id or a designed voice_… id (bin/vh voices).
              --instruct / [direction] / GEMINI_TTS_STYLE become speech_metadata.style: keep it short and situational
              ("calm, confident documentary narrator"). Identity traits (age, gender, accent) belong to the voice
              (bin/vh voices design), not to style; long director's notes are the most common cause of voice drift.
              Point-in-time tags go inline, in English even in a Chinese script: <short pause> <long pause> <breath>
              <laugh> <sigh> <cough> … Other providers and the captions drop them: these six always, any other <word>
              unless it is glued to letters/digits on both sides (if x<y and y>z stays text). Every clip carries an
              inaudible SynthID watermark: disclose AI narration in NOTES.md. GEMINI_TTS_MODEL overrides the model id.
  gemini-lite gemini-3.8-flash-lite-tts: the same API, 101 languages, $0.50 / $6 per 1M (≈ $0.0015 per 10 s) through
              2026-12-31, $1 / $12 from 2027-01-01; for bulk single-speaker narration.
  minimax     MiniMax T2A v2 (speech-2.8-hd) on the international platform, POST https://api.minimax.io/v1/t2a_v2.
              Key: MINIMAX_TOKEN_PLAN_KEY (Token Plan subscription key, spends its credits) first, else MINIMAX_API_KEY
              (pay-as-you-go: "1008 insufficient balance" when the account has no balance). The China host
              api.minimaxi.com rejects international keys (2049); a China-platform key (platform.minimaxi.com) needs
              MINIMAX_BASE_URL=https://api.minimaxi.com.
              --voice: a system voice id (default zh "Chinese (Mandarin)_Reliable_Executive", en "English_expressive_narrator";
              the Chinese ones are "Chinese (Mandarin)_*", from POST /v1/get_voice {"voice_type": "system"}).
              MINIMAX_TTS_MODEL (default speech-2.8-hd), MINIMAX_TTS_SPEED (0.5–2, default 1), MINIMAX_TTS_VOL (0–10,
              default 1), MINIMAX_TTS_PITCH (−12–12, default 0). --instruct / [direction]: used only when it is one of
              MiniMax's emotions (happy sad angry fearful disgusted surprised calm fluent whisper).
              Word timing comes from the request's own subtitles (per character, ms), no ASR needed: --join block|all
              places the lines of a joined request by them, and --align gemini is off unless asked for.
              Pause marks <#0.4#> (seconds) inside a line are voiced; captions and the other providers drop them. In a
              joined request the lines are linked by a <#--gap#> mark, plus any mark written at a line's edge; a mark
              at the edge of a request is dropped (MiniMax wants one between two spoken words). --join all sends the
              whole script in one request (under 10,000 characters), so the voice cannot drift between blocks.
              "@pronounce 硖合/(xia2)(he2)" lines in script.txt (one entry each, or several without spaces) become
              pronunciation_dict.tone. text_normalization is on: "1953 年" is read 一千九百五十三年, so write years
              as 一九五三年 in the spoken text.
"""
import argparse, base64, difflib, json, os, re, shutil, subprocess, sys, tempfile, time, unicodedata
import urllib.error, urllib.parse, urllib.request, wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SR = 48000
GEMINI_API = "https://generativelanguage.googleapis.com/v1beta"

def run(cmd, **kw):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kw)

def to_wav(src: Path, dst: Path):
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-ac", "1", "-ar", str(SR), str(dst)])

def duration(p: Path) -> float:
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)

RATE_WAIT_MAX, RATE_TRIES = 90.0, 5   # a 429 asking for more than 90 s is a daily quota: waiting will not help
BODY_PARSE, BODY_SHOW = 8192, 500     # bytes of an error body read for the retry delay / repeated in the message

class GeminiError(RuntimeError):
    """A Gemini call that failed for good (after its retries). tts keeps what it has and reports it; voices exits."""

def retry_after(e, msg):
    """Seconds a 429 asks for: the Retry-After header, else "retry in 59s" / "retryDelay": "59s" in the body, else 60."""
    m = re.search(r'retry in ([0-9.]+)\s*s|"retryDelay":\s*"([0-9.]+)s"', msg)
    s = (e.headers.get("Retry-After") if e.headers else None) or (next(g for g in m.groups() if g) if m else 60)
    try:
        return float(s) + 1
    except ValueError:   # Retry-After as an HTTP date
        return 61.0

def gemini_call(path, body=None, method=None, query=None, timeout=180, tries=3):
    """One Gemini REST call. The key travels in a header only, never in the URL or an error message.
    5xx and network errors are retried twice: the TTS docs note rare 500s when the model returns text instead of audio.
    A 429 waits as long as the API asks and is retried up to 5 times: Tier 1 allows 10 transcribe calls a minute, so
    --align on 11 or more lines hits it. A 429 asking for more than 90 s (a daily quota) fails at once.
    The delay is read from the first 8 KB of the body: a long quota message puts "retry in Ns" past the first 500 bytes,
    which are all that the error message repeats. A call that fails for good raises GeminiError."""
    key = os.environ.get("GEMINI_API_KEY") or sys.exit("set GEMINI_API_KEY (Google AI Studio → Get API key)")
    url = f"{GEMINI_API}/{path}" + (f"?{urllib.parse.urlencode(query, doseq=True)}" if query else "")
    data = None if body is None else json.dumps(body).encode()
    k = limited = 0
    while True:
        req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                     headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            body = e.read()[:BODY_PARSE].decode(errors="replace")
            wait = retry_after(e, body) if e.code == 429 else None
            if wait is not None and wait <= RATE_WAIT_MAX and limited < RATE_TRIES:
                limited += 1
                print(f"  gemini rate limit ({path.split('/')[0]}): waiting {wait:.0f} s, then retrying", flush=True)
                time.sleep(wait); continue
            if e.code in (500, 502, 503, 504) and k < tries - 1:
                k += 1; time.sleep(3 * k); continue
            raise GeminiError(f"gemini {path.split('/')[0]} error {e.code}: {body[:BODY_SHOW]}")
        except (urllib.error.URLError, TimeoutError) as e:
            if k < tries - 1:
                k += 1; time.sleep(3 * k); continue
            raise GeminiError(f"gemini {path.split('/')[0]}: {e}")

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
    kw = dict(text=text, speaker=voice or ("Serena" if zh else "Aiden"), language="Chinese" if zh else "English")
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
    if not shutil.which("say"):                                      # macOS only: a clear exit, not a FileNotFoundError
        sys.exit(f"tts: the `say` provider is macOS-only (no `say` command on {sys.platform}); use "
                 f"{', '.join(p for p in PROVIDERS if p not in ('say', 'qwen'))} (qwen needs Apple Silicon)")
    aiff = tmp / "say.aiff"
    run(["say", "-v", voice or ("Tingting" if lang.startswith("zh") else "Samantha"), "-o", str(aiff), "--", text])   # "--": a line may start with "-"
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
    return char_words(a.get("characters", []), a.get("character_start_times_seconds", []), a.get("character_end_times_seconds", []))

def char_words(chars, starts, ends):
    """Per-character timestamps (elevenlabs `alignment`) → script-spelled words: a Latin word or number each, a CJK
    character each, punctuation kept on the word before it (the same units as --align). A word runs from the start
    of its first character to the end of its last."""
    n = min(len(chars), len(starts), len(ends))
    idx = [k for k in range(n) for _ in chars[k]]              # position in the joined text → character entry
    text = "".join(chars[:n])
    return [{"w": u["d"], "start": starts[idx[m.start()]], "end": max(ends[idx[m.end() - 1]], starts[idx[m.start()]])}
            for m, u in zip(UNIT.finditer(text), script_units(text))]

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

def gemini_model(provider):
    return os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-lite-tts" if provider == "gemini-lite" else "gemini-3.8-flash-tts")

def gemini_tts(turns, out: Path, tmp: Path, model, voice):
    """Interactions API (ai.google.dev/gemini-api/docs/speech-generation): WAV 24 kHz mono in steps[].content[].data.
    turns: [{"text", "style"?, "speaker"?}], one text item each with a speech_metadata annotation.
    voice: a voice name / id, or {speaker: voice} for a conversational request (≤ 2 speakers, library voices)."""
    content = []
    for tr in turns:
        item = {"type": "text", "text": tr["text"]}
        meta = {k: tr[k] for k in ("speaker", "style") if tr.get(k)}
        if meta:
            item["annotations"] = [{"type": "speech_metadata", **meta}]
        content.append(item)
    speech = ({"mode": "conversational", "speakers": [{"speaker": s, "voice": v} for s, v in voice.items()]}
              if isinstance(voice, dict) else [{"voice": voice or "Kore"}])
    body = {"model": model, "input": [{"type": "user_input", "content": content}],
            "response_format": {"type": "audio", "mime_type": "audio/wav", "sample_rate": 24000},
            "generation_config": {"speech_config": speech}}
    resp = gemini_call("interactions", body)
    audio = [c for st in resp.get("steps", []) if st.get("type") == "model_output"
             for c in st.get("content", []) if c.get("type") == "audio" and c.get("data")]
    if not audio:
        raise GeminiError(f"gemini: no audio in the response: {json.dumps(resp)[:500]}")
    raw = tmp / "gm.wav"; raw.write_bytes(base64.b64decode(audio[-1]["data"])); to_wav(raw, out)

def p_gemini(text, voice, out: Path, tmp: Path, lang, instruct=None, model=None):
    gemini_tts([{"text": text, "style": instruct or os.environ.get("GEMINI_TTS_STYLE")}], out, tmp,
               model or gemini_model("gemini"), voice)
    return None

def p_gemini_lite(text, voice, out: Path, tmp: Path, lang, instruct=None):
    return p_gemini(text, voice, out, tmp, lang, instruct, model=gemini_model("gemini-lite"))

MINIMAX_API = "https://api.minimax.io"       # international platform; a China-platform key needs MINIMAX_BASE_URL
MINIMAX_ENV = ("MINIMAX_TTS_MODEL", "MINIMAX_TTS_SPEED", "MINIMAX_TTS_VOL", "MINIMAX_TTS_PITCH")   # recorded for --resume
MINIMAX_EMOTIONS = ("happy", "sad", "angry", "fearful", "disgusted", "surprised", "calm", "fluent", "whisper")
MINIMAX_MAX_CHARS = 10000                    # per request
MINIMAX_RETRY = (1000, 1001, 1002, 1039)     # unknown error, timeout, rate limit, tokens-per-minute limit
PRONOUNCE = []                               # the script's @pronounce entries → pronunciation_dict.tone
_SAID = set()

class MinimaxError(RuntimeError):
    """A MiniMax call that failed for good (after its retries). The message names the key's variable, never the key."""

def minimax_key():
    """(key, its variable): the Token Plan key first, since only it spends Token Plan credits."""
    var = next((k for k in ("MINIMAX_TOKEN_PLAN_KEY", "MINIMAX_API_KEY") if os.environ.get(k)), None)
    return (os.environ[var], var) if var else (None, None)

def minimax_hint(code, base):
    if code in (1004, 2049):                                         # authentication failed / invalid api key
        return ("a key from the China platform (platform.minimaxi.com) needs MINIMAX_BASE_URL=https://api.minimaxi.com"
                if base == MINIMAX_API else f"MINIMAX_BASE_URL is {base}: a key from the international platform"
                f" (platform.minimax.io) works only on {MINIMAX_API}")
    if code == 1008:                                                 # insufficient balance
        return ("no balance on this key's billing: a pay-as-you-go key (MINIMAX_API_KEY) spends the account balance, Token"
                " Plan credits are spent only through the Token Plan key (MINIMAX_TOKEN_PLAN_KEY, tried first)")
    return None

def minimax_settings():
    """voice_setting numbers from MINIMAX_TTS_SPEED / _VOL / _PITCH, checked against the API's ranges (exits if out)."""
    out = {}
    for name, key, lo, hi, cast, default in (("speed", "MINIMAX_TTS_SPEED", 0.5, 2.0, float, 1.0), ("vol", "MINIMAX_TTS_VOL", 0.01, 10.0, float, 1.0),
                                             ("pitch", "MINIMAX_TTS_PITCH", -12, 12, int, 0)):
        raw = os.environ.get(key)
        try:
            v = cast(raw) if raw else default
        except ValueError:
            sys.exit(f"{key}={raw!r}: not a{'n integer' if cast is int else ' number'}")
        if not lo <= v <= hi:
            sys.exit(f"{key}={raw}: outside {lo}–{hi}")
        out[name] = v
    return out

def minimax_emotion(instruct):
    """--instruct / [direction] → voice_setting.emotion: the last "; "-separated part that is one of MiniMax's
    emotions (a line's [direction] comes after --instruct). Free-text direction is ignored, and that is said once."""
    parts = [p.strip().lower() for p in (instruct or "").split(";") if p.strip()]
    if any(p not in MINIMAX_EMOTIONS for p in parts) and "emotion" not in _SAID:
        _SAID.add("emotion")
        print(f"  note: minimax takes one emotion word, not free-text direction ({' '.join(MINIMAX_EMOTIONS)}); the rest of"
              f" --instruct / [direction] is ignored", flush=True)
    return next((p for p in reversed(parts) if p in MINIMAX_EMOTIONS), None)

def _minimax_get(url, timeout, tries=3):
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            if k == tries - 1:
                raise MinimaxError(f"minimax: could not download the subtitles: {e}")
            time.sleep(3 * (k + 1))

def minimax_tts(text, voice, lang, emotion=None, timeout=600, tries=3):
    """T2A v2 (platform.minimax.io/docs/api-reference/speech-t2a-http), one non-streaming request → (WAV bytes, the
    subtitle file's items). The key travels in the Authorization header only. 1000, 1001, 1002 and 1039, 5xx and
    network errors are retried twice; any other error fails at once, with a hint for a rejected key or no balance."""
    key, var = minimax_key()
    if not key:
        sys.exit("set MINIMAX_TOKEN_PLAN_KEY (Token Plan) or MINIMAX_API_KEY (pay-as-you-go), from platform.minimax.io")
    if len(text) > MINIMAX_MAX_CHARS:
        raise MinimaxError(f"minimax: {len(text)} characters in one request, over the limit of {MINIMAX_MAX_CHARS}: use --join block"
                           f" (blank lines in script.txt split it) or --join none")
    vs = {"voice_id": voice, **minimax_settings(), "text_normalization": True}
    if emotion:
        vs["emotion"] = emotion
    body = {"model": os.environ.get("MINIMAX_TTS_MODEL", "speech-2.8-hd"), "text": text, "stream": False, "voice_setting": vs,
            "audio_setting": {"sample_rate": 44100, "format": "wav", "channel": 1},
            "language_boost": "Chinese" if lang.startswith("zh") else "English",
            "subtitle_enable": True, "subtitle_type": "word", "output_format": "hex"}
    if PRONOUNCE:
        body["pronunciation_dict"] = {"tone": PRONOUNCE}
    base = os.environ.get("MINIMAX_BASE_URL", MINIMAX_API).rstrip("/"); url = base + "/v1/t2a_v2"
    for k in range(tries):
        last = k == tries - 1
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                resp = json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code >= 500 and not last:
                time.sleep(3 * (k + 1)); continue
            raise MinimaxError(f"minimax HTTP {e.code}: {e.read()[:BODY_SHOW].decode(errors='replace')}")
        except (urllib.error.URLError, TimeoutError) as e:
            if not last:
                time.sleep(3 * (k + 1)); continue
            raise MinimaxError(f"minimax: {e}")
        br = resp.get("base_resp") or {}
        code = br.get("status_code")
        if code in MINIMAX_RETRY and not last:
            time.sleep((10 if code in (1002, 1039) else 3) * (k + 1)); continue
        if code != 0:
            hint = minimax_hint(code, base)
            raise MinimaxError(f"minimax error {code}: {br.get('status_msg')} (key from {var})" + (f"; {hint}" if hint else ""))
        d = resp.get("data") or {}
        if not d.get("audio") or not d.get("subtitle_file"):
            raise MinimaxError(f"minimax: no audio or no subtitle file in the response: {json.dumps(resp)[:300]}")
        subs = json.loads(_minimax_get(d["subtitle_file"], 120))
        return bytes.fromhex(d["audio"]), (subs if isinstance(subs, list) else subs.get("subtitles") or [])

def minimax_words(subs, text):
    """MiniMax subtitle items → script-spelled words over `text` (what was sent, pause marks removed). An entry of
    timestamped_words names the text it was read from: "1953" spans the seven syllables of 一千九百五十三, a name in
    @pronounce its pinyin, "Claude" comes as C / la / ude. Entries are grouped back into those words and found in order
    in the text; the file's character offsets are not used (one file counted the pause marks in them, another did not).
    A character no word covers (a space) gets the end of the one before; when that is more than a tenth of the text,
    it says so. None when nothing matched."""
    groups = []
    for ii, it in enumerate(subs):
        tw = it.get("timestamped_words") or [{"word": it.get("text", ""), "time_begin": it.get("time_begin", 0), "time_end": it.get("time_end", 0)}]
        for w in tw:
            g = (ii, w.get("word_begin"), w.get("word"))
            if groups and g[1] is not None and groups[-1][3] == g:
                groups[-1][2] = w.get("time_end", groups[-1][2])
            else:
                groups.append([(w.get("word") or "").strip(), w.get("time_begin", 0), w.get("time_end", 0), g])
    t0s, t1s, k, hit, miss = [None] * len(text), [None] * len(text), 0, 0, 0
    for word, b, e, _ in groups:
        j = text.find(word, k, k + len(word) + 12 + 4 * miss) if word else -1   # the window widens after a miss to resync
        if j < 0:
            miss += bool(word); continue
        n = len(word); hit += 1; miss = 0
        for q in range(n):
            t0s[j + q], t1s[j + q] = (b + (e - b) * q / n) / 1000, (b + (e - b) * (q + 1) / n) / 1000
        k = j + n
    if not hit:
        return None
    bare = [i for i, ch in enumerate(text) if t0s[i] is None and not ch.isspace()]
    if len(bare) > 0.1 * len(text.replace(" ", "")):
        print(f"  warning: minimax's subtitles left {len(bare)} of {len(text)} characters without a time (from"
              f" “{text[bare[0]:bare[0] + 12]}”); their words take the time of the word before", flush=True)
    prev = 0.0
    for i in range(len(text)):
        if t0s[i] is None:
            t0s[i] = t1s[i] = prev
        else:
            prev = t1s[i]
    return char_words(list(text), t0s, t1s)

def p_minimax(text, voice, out: Path, tmp: Path, lang, instruct=None):
    text = split_pauses(text)[1]                                     # a mark must sit between two spoken words
    voice = voice or ("Chinese (Mandarin)_Reliable_Executive" if lang.startswith("zh") else "English_expressive_narrator")
    audio, subs = minimax_tts(text, voice, lang, minimax_emotion(instruct))
    raw = tmp / "mm.wav"; raw.write_bytes(audio); to_wav(raw, out)
    words = minimax_words(subs, strip_tags(text))
    if words is None:
        raise MinimaxError(f"minimax: the subtitle file does not match the text sent ({json.dumps(subs, ensure_ascii=False)[:300]})")
    return words

PROVIDERS = {"qwen": p_qwen, "say": p_say, "edge": p_edge, "dashscope": p_dashscope, "elevenlabs": p_elevenlabs,
             "gemini": p_gemini, "gemini-lite": p_gemini_lite, "minimax": p_minimax}
WORD_TIMED = ("minimax",)   # their own word timings place the lines of a joined request: --join needs no ASR

TAG = re.compile(r"\s*<([A-Za-z][A-Za-z _-]{0,30})>\s*")        # performance tags such as <short pause>, <breath>, <laugh>
TAGS = ("short pause", "long pause", "breath", "laugh", "sigh", "cough")   # the documented ones: always a tag
REACTION = re.compile(r"\s*\|(?=\S)[^|\n]{1,40}(?<=\S)\|\s*")   # dialogue backchannels such as |mhm|, |oh really?|
CJK_GAP = re.compile(r"(?<=[　-鿿＀-￯]) (?=[　-鿿＀-￯])")
PAUSES = re.compile(r"\s*(?:<#\s*\d+(?:\.\d+)?\s*#>\s*)+")       # a run of MiniMax pause marks such as <#0.4#> (seconds)

def _tag(m):
    """Another <word> glued to letters/digits on both sides is text, not a tag: `if x<y and y>z` keeps it."""
    s, a, b = m.string, m.start(1) - 1, m.end(1) + 1                       # "<" at a, ">" at b - 1
    glued = a > 0 and s[a - 1].isascii() and s[a - 1].isalnum() and b < len(s) and s[b].isascii() and s[b].isalnum()
    return m.group() if glued and m.group(1).lower() not in TAGS else " "

def _pause(m):
    """A dropped pause mark leaves a space where the text had one around it, or between two letters/digits."""
    s, a, b = m.string, m.start(), m.end()
    return " " if m.group() != m.group().strip() or (a > 0 and b < len(s) and s[a - 1].isalnum() and s[b].isalnum()) else ""

def pause_secs(run):
    return sum(float(x) for x in re.findall(r"\d+(?:\.\d+)?", run))

def pause_mark(sec, spaced=False):
    """One MiniMax pause mark (0.01–99.99 s); shorter is no mark. spaced: with a space on each side (English words)."""
    sp = " " if spaced else ""
    return f"{sp}<#{min(sec, 99.99):.2f}#>{sp}" if sec >= 0.01 else sp

def split_pauses(text):
    """→ (seconds of pause marks before a line's first word, the line with each run of marks merged into one mark,
    seconds after its last word). MiniMax rejects consecutive marks and wants each one between two spoken words."""
    text, lead, trail = text.strip(), 0.0, 0.0
    m = PAUSES.match(text)
    if m:
        lead, text = pause_secs(m.group()), text[m.end():]
    m = re.search(PAUSES.pattern + "$", text)
    if m:
        trail, text = pause_secs(m.group()), text[:m.start()]
    return lead, PAUSES.sub(lambda r: pause_mark(pause_secs(r.group()), r.group() != r.group().strip()), text), trail

def strip_tags(text: str, reactions=True, pauses=True) -> str:
    """Remove inline performance tags, MiniMax pause marks and (in a dialogue script) |reaction| markers: only gemini
    voices the tags and only minimax the pauses; every other provider would read them aloud, and captions must never
    show them. Outside a dialogue |x| is text."""
    text = TAG.sub(_tag, PAUSES.sub(_pause, text) if pauses else text)
    return CJK_GAP.sub("", re.sub(r" {2,}", " ", REACTION.sub(" ", text) if reactions else text)).strip()

def strip_reactions(text: str) -> str:
    """Remove |reaction| markers only (kept for a gemini conversation, where the other speaker voices them)."""
    return CJK_GAP.sub("", re.sub(r" {2,}", " ", REACTION.sub(" ", text))).strip() if REACTION.search(text) else text

# ---------- script ----------

def parse_script(path: Path):
    """→ (segments, speakers, pronounce). A blank line closes a block (the unit of --join block)."""
    segs, speakers, pronounce, block = [], {}, [], 0
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            if segs and segs[-1]["_block"] == block:
                block += 1
            continue
        if line.startswith("#"):
            continue
        head = re.fullmatch(r"@speakers((?:\s+[^\s=]+=\S+)+)", line)       # @speakers A=Kore B=Puck
        if head:
            speakers.update(p.split("=", 1) for p in head.group(1).split())
            continue
        head = re.fullmatch(r"@pronounce\s+(.+)", line)                  # @pronounce 硖合/(xia2)(he2) — minimax only
        if head:                                                         # several on a line when none has a space
            items = head.group(1).split()
            for x in (items if all("/" in x for x in items) else [head.group(1).strip()]):
                if "/" not in x:
                    sys.exit(f"{path.name}: @pronounce {x!r}: write text/reading, e.g. 硖合/(xia2)(he2)")
                pronounce.append(x)
            continue
        sid = style = spk = None
        if line.startswith("@") and " " in line:
            sid, line = line[1:].split(" ", 1)
        m = re.match(r"\[([^\]]+)\]\s*", line.strip())             # per-line performance direction
        if m:
            style, line = m.group(1).strip(), line.strip()[m.end():]
        m = re.match(r"(\S+?)\s*[:：]\s*", line.strip()) if speakers else None
        if m and m.group(1) in speakers:                             # "A: …" — only labels declared in @speakers
            spk, line = m.group(1), line.strip()[m.end():]
            m = re.match(r"\[([^\]]+)\]\s*", line)                   # "A: [direction] …" works too; "[d1] A: [d2]" → "d1; d2"
            if m:
                style, line = "; ".join(x for x in (style, m.group(1).strip()) if x), line[m.end():]
        zh, bar, en = (p.strip() for p in line.partition("||"))
        if spk:                                                      # "A: 中文 || A: English"
            en = re.sub(rf"^{re.escape(spk)}\s*[:：]\s*", "", en)
        snap = None
        if sid and ":" in sid:                                       # @id:downbeat — this line lands on that grid
            sid, snap = sid.split(":", 1)
        seg = {"id": sid or f"s{len(segs)+1:02d}", "zh": zh, "en": en}
        if snap:
            seg["snap"] = snap
        if style:
            seg["direction"] = style
        if spk:
            seg["speaker"] = spk
        seg["_block"] = block
        if not bar:                                                  # one side only: which language is it?
            seg["_one"] = "zh" if CJK_TEXT.search(zh) else "en" if re.search(r"[^\W_]", zh) else None
        segs.append(seg)
    one = next((s["_one"] for s in segs if s.get("_one")), "zh")
    for s in segs:                                                   # without CJK characters it is English; punctuation
        if "_one" in s:                                              # only ("……") goes with the one-sided line before it
            one = s.pop("_one") or one
            if one == "en":
                s["zh"], s["en"] = "", s["zh"]
    return segs, speakers, pronounce

def read_script(path: Path):
    return [{k: v for k, v in s.items() if not k.startswith("_")} for s in parse_script(path)[0]]

# ---------- alignment: gemini-3.5-transcribe word timestamps → script words + similarity ----------

_CJK = "぀-ヿ㐀-䶿一-鿿豈-﫿가-힯"
CJK_TEXT = re.compile(rf"[{_CJK}　-〿＀-￯]")                  # CJK characters, CJK / full-width punctuation
UNIT = re.compile(rf"[{_CJK}]|(?:(?![{_CJK}])[^\W_])+(?:['’.\-](?:(?![{_CJK}])[^\W_])+)*")   # one CJK char / one word
OPENERS = "“‘「『（《〈【"
ASR_LANGS = {"zh": "cmn-Hans-CN", "en": "en-US"}

HOMOPHONES = str.maketrans("她它祂牠地得作再象", "他他他他的的做在像")   # same syllable: ASR cannot tell them apart

def _norm(u):
    return unicodedata.normalize("NFKC", u).lower().replace("’", "'").translate(HOMOPHONES)

def script_units(text):
    """Speakable units (a CJK character or a Latin word / number) with their display text: trailing punctuation stays
    on the unit before it, opening quotes and brackets move to the unit after. The last unit keeps everything after it
    ("world ." → "world .", "Hi 👋" → "Hi 👋"); an interior tail is stripped of spaces ("a , b" → "a," "b")."""
    ms, out, lead = list(UNIT.finditer(text)), [], ""
    if ms:
        lead = text[:ms[0].start()].strip()
    for i, m in enumerate(ms):
        gap = text[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(text)]
        if i + 1 == len(ms):
            tail, nxt = gap.rstrip(), ""
        elif re.search(r"\s", gap):
            j = max(k for k, ch in enumerate(gap) if ch.isspace())
            tail, nxt = gap[:j].strip(), gap[j + 1:]
        else:
            j = len(gap)
            while j and gap[j - 1] in OPENERS:
                j -= 1
            tail, nxt = gap[:j], gap[j:]
        out.append({"n": _norm(m.group()), "u": m.group(), "d": lead + m.group() + tail, "cjk": bool(re.match(rf"[{_CJK}]", m.group()))})
        lead = nxt
    return out

def asr_units(words):
    """ASR words → units with times; a multi-character CJK word shares its span evenly."""
    out = []
    for g, w in enumerate(words):
        us = UNIT.findall(w["w"])
        step = (w["end"] - w["start"]) / max(len(us), 1)
        out += [(_norm(u), w["start"] + k * step, w["start"] + (k + 1) * step, g) for k, u in enumerate(us)]
    return out

def similarity(a, b):
    """0–1 token similarity (difflib ratio over CJK characters / Latin words, punctuation and case ignored)."""
    a = [x["n"] for x in script_units(a)] if isinstance(a, str) else a
    b = [x["n"] for x in script_units(b)] if isinstance(b, str) else b
    return round(difflib.SequenceMatcher(None, a, b, autojunk=False).ratio(), 3) if (a or b) else 1.0

def _match(s_norm, a):
    """Times for every script unit from the ASR units (difflib alignment); unmatched runs are interpolated."""
    t = [None] * len(s_norm)
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, s_norm, [x[0] for x in a], autojunk=False).get_opcodes():
        if tag == "equal" or (tag == "replace" and i2 - i1 == j2 - j1):
            for k in range(i2 - i1):
                t[i1 + k] = a[j1 + k][1:]
        elif tag == "replace":                                        # n script units heard as m other units
            s0, s1, n = a[j1][1], a[j2 - 1][2], i2 - i1
            for k in range(n):
                t[i1 + k] = (s0 + (s1 - s0) * k / n, s0 + (s1 - s0) * (k + 1) / n, a[j1 + k * (j2 - j1) // n][3])
    i = 0
    while i < len(t):
        if t[i] is not None:
            i += 1; continue
        j = i
        while j < len(t) and t[j] is None:
            j += 1
        lo = t[i - 1][1] if i else (a[0][1] if a else 0.0)
        hi = max(t[j][0] if j < len(t) else (a[-1][2] if a else lo), lo)
        for k in range(j - i):
            t[i + k] = (lo + (hi - lo) * k / (j - i), lo + (hi - lo) * (k + 1) / (j - i), None)
        i = j
    return t

def _words(units, times):
    """Script-spelled words: a Latin word each; CJK characters the ASR heard as one word stay together."""
    out = []
    for u, (s, e, g) in zip(units, times):
        if out and u["cjk"] and out[-1]["cjk"] and g is not None and g == out[-1]["g"]:
            out[-1]["w"] += u["d"]; out[-1]["end"] = e
        else:
            out.append({"w": u["d"], "start": s, "end": e, "g": g, "cjk": u["cjk"]})
    return [{"w": w["w"], "start": round(w["start"], 3), "end": round(max(w["end"], w["start"]), 3)} for w in out]

MIN_SPAN = 0.1    # a line nothing was heard for (skipped by the ASR, or "……") still gets this much: no zero-length cut, no
                  # zero-width cue, no header-only WAV in the re-check

def align_lines(texts, asr_words, dur, alts=None):
    """Map the script lines spoken in one audio file onto its ASR words → per line: speech span, cut points for
    splitting the file, script-spelled words and the similarity to what was heard inside the line's span
    (alts: the same lines with their |reaction| words kept, which the other speaker voices inside the turn).
    Lines nothing was heard for collapse to a point (between their neighbours' words, or the file's start / end);
    a run of them at one point gets MIN_SPAN each, in order, centred on it (a skipped line is flagged anyway:
    similarity 0). A "……" line then spans its own cut, as before."""
    lines = [script_units(t) for t in texts]
    a = asr_units(asr_words)
    times, res, k = _match([u["n"] for L in lines for u in L], a), [], 0
    for L in lines:
        tt = times[k:k + len(L)]; k += len(L)
        prev = res[-1]["end"] if res else 0.0
        res.append({"units": L, "times": tt, "start": tt[0][0] if tt else prev, "end": tt[-1][1] if tt else prev})
    unheard = lambda r: (not r["units"] or all(t[2] is None for t in r["times"])) and r["end"] - r["start"] < MIN_SPAN / 2
    i = 0
    while i < len(res):
        if not unheard(res[i]):
            i += 1; continue
        j = i
        while j + 1 < len(res) and unheard(res[j + 1]) and res[j + 1]["start"] <= res[j]["end"] + 1e-6:
            j += 1
        n = j - i + 1; mid = (res[i]["start"] + res[j]["end"]) / 2
        lo = max(0.0, min(mid - n * MIN_SPAN / 2, dur - n * MIN_SPAN)); w = min(MIN_SPAN, max(dur - lo, 0.0) / n)
        for m, r in enumerate(res[i:j + 1]):
            r["start"], r["end"] = lo + m * w, lo + (m + 1) * w
            if r["units"]:
                nu = len(r["units"]); r["times"] = [(r["start"] + q * w / nu, r["start"] + (q + 1) * w / nu, None) for q in range(nu)]
        i = j + 1
    for i, r in enumerate(res):
        r["cut0"] = 0.0 if i == 0 else (res[i - 1]["end"] + r["start"]) / 2
        r["cut1"] = dur if i == len(res) - 1 else (r["end"] + res[i + 1]["start"]) / 2
        heard = [w for w in asr_words if r["cut0"] <= (w["start"] + w["end"]) / 2 < r["cut1"]]
        r["heard"] = ("" if any(u["cjk"] for u in r["units"]) else " ").join(w["w"] for w in heard).strip()
        hn = [u[0] for u in asr_units(heard)]                  # a line without words ("……") scores 1.0 if nothing is heard
        r["sim"] = max(similarity(x, hn) for x in ([u["n"] for u in r["units"]], (alts or {}).get(i)) if x is not None)
        r["words"] = _words(r["units"], r["times"])
    for r in res:                                               # no words to time ("……"): the line spans its own cut
        if not r["units"]:
            r["start"], r["end"] = r["cut0"], r["cut1"]
    res[0]["head"] = round(asr_words[0]["start"] if asr_words else dur, 2)
    res[-1]["tail"] = round(dur - asr_words[-1]["end"] if asr_words else dur, 2)
    return res

def transcribe(wav: Path, lang, tmp: Path, vocab=None):
    """gemini-3.5-transcribe on one file → (text, [{"w","start","end"}]). Timestamps and custom_vocabulary exclude
    each other in the API, so a vocab call returns text only."""
    small = tmp / f"asr-{wav.stem}.wav"                     # 16 kHz mono: ≈ 10 min fits the 20 MB inline request limit
    run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-ac", "1", "-ar", "16000", str(small)])
    cfg = {"language_codes": [c for c in os.environ.get("GEMINI_ASR_LANGS", ASR_LANGS.get(lang, "")).split(",") if c]}
    if vocab:
        cfg["custom_vocabulary"] = vocab[:1000]
    else:
        cfg["mode"] = {"type": "verbatim", "timestamp_granularities": ["word"]}
    resp = gemini_call("interactions", {"model": os.environ.get("GEMINI_ASR_MODEL", "gemini-3.5-transcribe"),
                                        "input": [{"type": "audio", "mime_type": "audio/wav",
                                                   "data": base64.b64encode(small.read_bytes()).decode()}],
                                        "generation_config": {"transcription_config": cfg}}, timeout=300)
    sec = lambda v: float(str(v).rstrip("s") or 0)
    texts, words = [], []
    for st in resp.get("steps", []):
        for c in st.get("content", []):
            if c.get("type") != "text":
                continue
            texts.append(c.get("text", ""))
            words += [{"w": an.get("text", ""), "start": sec(an["start_offset"]), "end": sec(an.get("end_offset", an["start_offset"]))}
                      for an in c.get("annotations") or [] if an.get("type") == "word_info" and "start_offset" in an]
    return "".join(texts).strip(), words

def vocab_terms(texts, extra=""):
    """Terms for the custom-vocabulary re-check: Latin words in Chinese lines; names, acronyms, CamelCase and tokens
    with digits in English lines; plus --vocab. Common words (or whole lines) would only mask real misreads."""
    out = [x.strip() for x in re.split(r"[,，]", extra or "") if x.strip()]
    for t in texts:
        zh = re.search(rf"[{_CJK}]", t) is not None
        for m in re.finditer(r"[A-Za-z0-9][A-Za-z0-9.+#'’\-]*", t):
            w = m.group().rstrip(".'’-")
            sentence_start = not t[:m.start()].strip() or re.search(r"[.!?]\s*$", t[:m.start()])
            if len(w) > 1 and (zh or re.search(r"\d", w) or re.search(r"[A-Z]", w[1:]) or (w[0].isupper() and not sentence_start)):
                out.append(w)
    return list(dict.fromkeys(out))[:100]            # the docs: best results with up to 100 terms

def disputed(script, heard):
    """Script phrases the ASR text disagrees with (plus one unit of context each side, not across punctuation): the
    custom-vocabulary re-check biases only these spots toward the script, so a real misread elsewhere still shows."""
    su = script_units(script)
    stop = lambda u: re.search(r"[^\w\s]$", u["d"]) is not None     # the unit ends a clause
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, [u["n"] for u in su], [x["n"] for x in script_units(heard)],
                                                        autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            seg = su[i1 - (i1 > 0 and not stop(su[i1 - 1])): i2 + (i2 < len(su) and not stop(su[i2 - 1]))]
            out.append(("" if all(u["cjk"] for u in seg) else " ").join(u["u"] for u in seg))
    return out

def with_reactions(text):
    return strip_tags(REACTION.sub(lambda m: f" {m.group().strip()[1:-1]} ", text))

def asr_record(text, r, min_sim):
    rec = {"text": text, "similarity": r["sim"]}
    for k in ("head", "tail"):
        if k in r:
            rec[k] = r[k]
    return set_flag(rec, min_sim)

def set_flag(rec, min_sim):
    why = [f"similarity {rec['similarity']:.2f}"] if max(rec["similarity"], rec.get("recheck", {}).get("similarity", 0)) < min_sim else []
    why += [f"{rec[k]:.1f} s of audio {w} word" for k, w in (("head", "before the first"), ("tail", "after the last")) if rec.get(k, 0) > 1.0]
    rec.pop("flag", None)
    if why:
        rec["flag"] = "; ".join(why)
    return rec

def cut(src: Path, t0, t1, dst: Path):
    run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f"atrim=start={t0:.4f}:end={t1:.4f},asetpts=N/SR/TB", str(dst)])

TRIM_DB, TRIM_HEAD, TRIM_TAIL = -50.0, 0.03, 0.08     # edges quieter than −50 dBFS; keep 30 ms before the voice, 80 ms after

def trim_edges(wav: Path, tmp: Path):
    """Cut the silence a provider leaves before and after the voice (qwen's Ryan: ~0.45 s at the head of every line;
    edge: ~0.2 s before and ~0.85 s after), keeping a short margin so onsets and decays stay whole. Spacing then comes
    only from --gap or the beat grid. −50 dBFS, not −45: at −45 the soft start of an f or h (up to 70 ms between −60 and
    −45 dBFS) was cut. Breathing or mumbling above −50 dBFS before the first word is not silence and stays: that is
    what --align gemini's head check is for. Loudness is measured in 10 ms windows (RMS), and a loud window counts as
    voice only when a neighbouring window is loud too: a click or pop that stays inside one window does not stop the
    trim, before or after the voice (a burst across two windows still counts), and a noise floor below −50 dBFS is
    not voice.
    Returns the seconds cut from the head (to shift word timings) and from the tail; a file with no voice is left as is."""
    import array
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    x = array.array("h"); x.frombytes(raw[: len(raw) // 2 * 2])
    n = SR // 100; lim = (10 ** (TRIM_DB / 20) * 32768) ** 2 * n; wins = range(0, len(x), n)
    loud = lambda i: 0 <= i < len(x) and sum(v * v for v in x[i:i + n]) > lim
    voice = lambda i: loud(i) and (loud(i - n) or loud(i + n))      # part of a ≥ 20 ms run above the threshold
    first = next((i for i in wins if voice(i)), None)              # scan in from each end: stops at the voice
    if first is None:
        return 0.0, 0.0
    last = next(i for i in reversed(wins) if voice(i))
    dur = len(x) / SR
    t0, t1 = max(0.0, first / SR - TRIM_HEAD), min(dur, (last + n) / SR + TRIM_TAIL)
    if t0 < 0.005 and dur - t1 < 0.005:
        return 0.0, 0.0
    cut(wav, t0, t1, tmp / "trim.wav"); shutil.move(str(tmp / "trim.wav"), str(wav))
    return t0, dur - t1

# ---------- voices: the Gemini voice library and voice design ----------

STUDIO = ("Zephyr Puck Charon Kore Fenrir Leda Orus Aoede Callirrhoe Autonoe Enceladus Iapetus Umbriel Algieba Despina "
          "Erinome Algenib Rasalgethi Laomedeia Achernar Alnilam Schedar Gacrux Pulcherrima Achird Zubenelgenubi "
          "Vindemiatrix Sadachbia Sadaltager Sulafat").split()

def voices_main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh voices", description="Gemini TTS voices (GEMINI_API_KEY).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list", help="the voice library plus your designed voices; filter by language prefix")
    ls.add_argument("lang", nargs="?", help="language prefix: en, en-GB, ja, zh …")
    ls.add_argument("--search", help="substring of name or description"); ls.add_argument("--gender", choices=["female", "male", "neutral"])
    ls.add_argument("--type", choices=["prebuilt", "prompted", "replicated"]); ls.add_argument("--json", action="store_true")
    de = sub.add_parser("design", help="create a stored voice from a description; prints its voice_… id, saves the sample")
    de.add_argument("description", help="1–2 sentences: age, gender, timbre, accent, baseline delivery")
    de.add_argument("--out", help="sample WAV path (default ./<voice_id>.wav)"); de.add_argument("--name", help="display name")
    de.add_argument("--lang", help="BCP-47 code, e.g. zh-CN, en-US"); de.add_argument("--gender", choices=["female", "male", "neutral"])
    de.add_argument("--model", help="default GEMINI_TTS_MODEL or gemini-3.8-flash-tts")
    rm = sub.add_parser("delete", help="delete a stored voice (designed voices count toward 200 per project)")
    rm.add_argument("id")
    a = ap.parse_args(argv)
    if a.cmd == "list":
        q = {"page_size": 1000, **{k: v for k, v in (("search", a.search), ("gender", a.gender), ("type", a.type)) if v}}
        vs, tok = [], None
        while True:
            r = gemini_call("voices", query={**q, **({"page_token": tok} if tok else {})}, timeout=60)
            vs += r.get("voices", []); tok = r.get("next_page_token")
            if not tok:
                break
        langs = sorted({v.get("language_code") or "?" for v in vs})
        if a.lang:
            pre = ("zh", "cmn", "yue") if a.lang.lower() in ("zh", "cmn") else (a.lang.lower(),)
            vs = [v for v in vs if (v.get("language_code") or "").lower().startswith(pre)]
        if a.json:
            print(json.dumps(vs, ensure_ascii=False, indent=1)); return
        if not a.lang and not a.search and not a.gender and not a.type:
            by = {}
            for v in vs:
                by[v.get("language_code") or "?"] = by.get(v.get("language_code") or "?", 0) + 1
            print(f"{len(vs)} voices · " + ", ".join(f"{k} {n}" for k, n in sorted(by.items())))
            print("studio voices (any language — the TTS model detects it from the text): " + " ".join(STUDIO))
            mine = [v for v in vs if v.get("type") != "prebuilt"]
            if mine:
                print("your voices:")
                for v in mine:
                    print(f"  {v['id']:<28} {v.get('type',''):<10} {v.get('display_name','')}")
            print("narrow it: bin/vh voices list en-GB [--gender female] [--search narrator]  ·  --json for every field")
            return
        for v in vs:
            star = "*" if v.get("display_name") in STUDIO else " "
            print(f"{star}{v.get('id',''):<26} {v.get('language_code',''):<7} {v.get('gender',''):<7} {v.get('pitch',''):<6} "
                  f"{(v.get('accent') or '')[:22]:<22} {(v.get('description') or v.get('display_name') or '')[:90]}")
        print(f"{len(vs)} voice(s)" + (" · * = studio voice, speaks every supported language" if any(v.get("display_name") in STUDIO for v in vs) else ""))
        if a.lang and not vs:
            print(f"no library voice is tagged {a.lang!r} (library locales: {', '.join(langs)}).\n"
                  f"Gemini TTS detects the language from the text, so the 30 studio voices speak it too: {' '.join(STUDIO[:8])} …\n"
                  f"or design one: bin/vh voices design \"<age, timbre, accent, delivery>\" --lang <code>")
    elif a.cmd == "design":
        voice = {"model": a.model or os.environ.get("GEMINI_TTS_MODEL", "gemini-3.8-flash-tts"), "type": "prompted",
                 "display_name": a.name or a.description[:40], "prompted": {"input": a.description}}
        voice.update({k: v for k, v in (("language_code", a.lang), ("gender", a.gender)) if v})
        t0 = time.time()
        r = gemini_call("voices", {"store": True, "voice": voice}, timeout=180)
        v = r.get("voice", r)
        vid = v.get("id") or sys.exit(f"voices: no id in the response: {json.dumps(r)[:400]}")
        print(vid)
        sample = v.get("sample_audio") or {}
        if sample.get("data"):
            out = Path(a.out or f"{vid}.wav"); out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(base64.b64decode(sample["data"]))
            try:
                d = f", {duration(out):.1f} s"
            except Exception:
                d = ""
            print(f"  sample   → {out} ({sample.get('mime_type', '?')}{d})")
        use = v.get("usage") or {}
        print(f"  created in {time.time() - t0:.1f} s · tokens in/out {use.get('total_input_tokens', '?')}/{use.get('total_output_tokens', '?')}"
              f" · expires {v.get('expire_time', '?')} (stored voices: 200 per project, 1-year TTL)")
        print(f"  use it   : bin/vh tts <project> gemini {vid}   ·   remove: bin/vh voices delete {vid}")
    else:
        gemini_call(f"voices/{a.id}", method="DELETE", timeout=60, tries=1)
        print(f"deleted {a.id}")

# ---------- main ----------

def main():
    if sys.argv[1:2] == ["voices"] and (len(sys.argv) == 2 or sys.argv[2] in ("list", "design", "delete", "-h", "--help")):
        return voices_main(sys.argv[2:])
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--provider", choices=PROVIDERS, help="default qwen (with --resume: the run's provider)")
    ap.add_argument("--voice"); ap.add_argument("--lang", choices=["zh", "en"], help="spoken side (default zh; en for an English-only script)")
    ap.add_argument("--gap", type=float, default=0.25); ap.add_argument("--instruct")
    ap.add_argument("--keep-edges", action="store_true", help="keep the silence the provider puts before/after each line")
    ap.add_argument("--beats", help="beat map JSON: start each line on the next grid point")
    ap.add_argument("--snap", choices=["beat", "half", "downbeat"], help="with --beats: the grid (default beat)")
    ap.add_argument("--lead", type=float, default=0.0, help="earliest start of the first line (s)")
    ap.add_argument("--min-gap", type=float, default=0.12, help="with --beats: minimum breath before the next grid point")
    ap.add_argument("--align", default="none", choices=["none", "gemini"], help="word timestamps + ASR check per line")
    ap.add_argument("--min-sim", type=float, default=0.85, help="with --align: flag lines whose ASR similarity is lower")
    ap.add_argument("--vocab", default="", help="with --align: extra terms (comma-separated) for the re-check of flagged lines")
    ap.add_argument("--join", default="auto", choices=["auto", "none", "block", "all"],
                    help="synthesize consecutive lines in one request (block = lines between blank lines)")
    ap.add_argument("--resume", action="store_true",
                    help="continue the last run in vo/<lang> instead of starting over: synthesize only the missing files, reuse the "
                         "ASR of the lines that succeeded, redo the rest (a plain run that failed midway continues; a finished one can "
                         "get --align gemini this way). The script, provider, voice, delivery direction and join mode must be the run's "
                         "(recorded in vo/<lang>/_run.json); the timing flags may change")
    a = ap.parse_args()
    proj = Path(a.project).resolve(); audio = proj / "audio"; script = audio / "script.txt"
    if not script.exists():
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("# 一行一句（= 一条字幕 / 一个 cue）。双语用 ' || ' 分隔：中文 || English。可选 @id 前缀。\n"
                          "@hook 一句话，做出一支片子。 || One sentence in, one film out.\n", encoding="utf-8")
        sys.exit(f"wrote a sample {script} — edit it and re-run")
    segs, speakers, pronounce = parse_script(script)
    if a.lang is None:                                               # an English-only script is spoken in English
        a.lang = "en" if any(s["en"] for s in segs) and not any(s["zh"] for s in segs) else "zh"
        if a.lang == "en":
            print("  English-only script: speaking it in English (pass --lang zh for the Chinese voice)")
    reactions = bool(speakers)                                       # |…| is a backchannel only under an @speakers header
    if a.voice and "=" in a.voice:                                   # "A=Tingting,B=Meijia" overrides @speakers
        speakers.update(p.split("=", 1) for p in re.split(r"[,\s]+", a.voice) if "=" in p); a.voice = None
    vo = audio / "vo" / a.lang; man = None
    if a.resume:                                                     # the run being continued: what it was made with
        try:
            man = json.loads((vo / "_run.json").read_text(encoding="utf-8"))
        except OSError:
            sys.exit(f"--resume: no {vo.relative_to(proj)}/_run.json to continue from; run once without --resume")
        for k, v in (("provider", a.provider), ("voice", a.voice), ("instruct", a.instruct)):
            if v is not None and v != man.get(k):
                sys.exit(f"--resume: the run was made with {k} {man.get(k) or 'default'}, not {v}: re-run the same command with"
                         f" --resume, or drop --resume to start over")
        if speakers != man["speakers"]:
            sys.exit(f"--resume: the speaker voices changed (run: {man['speakers']}, now: {speakers}); drop --resume to start over")
        if os.environ.get("GEMINI_TTS_STYLE") != man.get("style_env"):
            sys.exit(f"--resume: GEMINI_TTS_STYLE was {man.get('style_env')!r} for the run, now {os.environ.get('GEMINI_TTS_STYLE')!r};"
                     f" set it back, or drop --resume to start over")
        a.provider, a.voice, a.instruct, a.keep_edges = man["provider"], man["voice"], man.get("instruct"), man["keep_edges"]
    a.provider = a.provider or "qwen"
    gemini = a.provider.startswith("gemini")
    timed = a.provider in WORD_TIMED                                 # word timing from the provider itself
    penv = {k: os.environ.get(k) for k in MINIMAX_ENV} if a.provider == "minimax" else {}
    if a.provider == "minimax":
        PRONOUNCE[:] = pronounce
    elif pronounce:
        print(f"  note: @pronounce is for minimax; {a.provider} reads the words as written (write a same-sound character instead)")
    for k, v in penv.items() if man else ():
        if man.get("env", {}).get(k) != v:
            sys.exit(f"--resume: {k} was {man['env'].get(k)!r} for the run, now {v!r}; set it back, or drop --resume to start over")
    if man and man.get("pronounce", []) != PRONOUNCE:
        sys.exit(f"--resume: the @pronounce entries changed (run: {man.get('pronounce', [])}, now: {PRONOUNCE}); drop --resume to start over")
    dialogue = any(s.get("speaker") for s in segs)
    join = a.join if a.join != "auto" else (man["join"] if man else ("block" if gemini and dialogue else "none"))
    if join != "none" and dialogue and not gemini:
        print("  note: a dialogue needs one voice per request outside gemini → one request per line (--join none)")
        join = "none"
    conversational = gemini and dialogue and join != "none"
    if conversational and (len(speakers) > 2 or any(v.startswith(("voice_", "voicekey_")) for v in speakers.values())):
        print("  note: a gemini conversation takes at most 2 speakers with library voices; designed voices are synthesized"
              " turn by turn → --join none")
        join, conversational = "none", False
    if man and join != man["join"]:
        sys.exit(f"--resume: the run used --join {man['join']}, now {join}: re-run the same command with --resume, or drop --resume to start over")
    align = a.align == "gemini" or (join != "none" and not timed)
    if join != "none" and a.align != "gemini" and not timed:
        print("  --join recovers line boundaries from word timestamps → --align gemini is on")
    if (gemini or align) and not os.environ.get("GEMINI_API_KEY"):     # before anything is synthesized or deleted
        sys.exit("set GEMINI_API_KEY (Google AI Studio → Get API key)" + ("" if gemini else ": --align gemini / --join transcribe with Gemini"))
    if a.provider == "minimax":
        minimax_settings()                                           # a value out of range exits here, not mid-run
        if not minimax_key()[0]:
            sys.exit("set MINIMAX_TOKEN_PLAN_KEY (Token Plan) or MINIMAX_API_KEY (pay-as-you-go), from platform.minimax.io")
    if not a.resume:
        shutil.rmtree(vo, ignore_errors=True); vo.mkdir(parents=True)
    grids = {}
    if a.beats:
        bm = json.loads(Path(a.beats).read_text())
        beats = sorted(bm.get("beats", []))
        grids = {"beat": beats, "downbeat": sorted(bm.get("downbeats", [])) or beats,
                 "half": sorted(beats + [(x + y) / 2 for x, y in zip(beats, beats[1:])])}
    elif a.snap or any(s.get("snap") for s in segs):                  # timing is unchanged; only say so
        print("  warning: --snap and @id:grid need --beats <music.beats.json>; without it every line follows --gap")
    for s in (x for x in segs if x.get("snap") not in (None, "beat", "half", "downbeat")):
        print(f"  warning: @{s['id']}:{s['snap']} — unknown grid (beat | half | downbeat); ignored, the line uses --snap {a.snap or 'beat'}")
    a.snap = a.snap or "beat"
    grid = grids.get(a.snap, [])
    if a.beats and not grid:
        have = ", ".join(k for k in ("beats", "downbeats") if bm.get(k)) or "neither beats nor downbeats"
        sys.exit(f"--beats {a.beats}: no '{a.snap}' grid in it (it has {have}); pass --snap downbeat, or a map written by bin/vh music or bin/vh beats")
    said = set()
    def next_start(first, t, which=None):
        """First point of the line's grid at or after its earliest start (--lead, else t + --min-gap). Past the end of
        the grid (the narration outlives the music) the line follows --gap instead, and that is said once per grid."""
        name = which if which in grids else a.snap; g = grids.get(name, grid); earliest = a.lead if first else t + a.min_gap
        x = next((x for x in g if x >= earliest - 1e-6), None)
        if x is None and a.beats and name not in said:
            said.add(name)
            print(f"  warning: the {name} grid " + (f"ends at {g[-1]:.2f} s" if g else f"is empty in {a.beats}") + f"; from here lines follow --gap {a.gap}", flush=True)
        return x if x is not None else (a.lead if first else t + a.gap)
    def silence(sec, k):
        f = vo / f"_gap{k:02d}.wav"
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"anullsrc=r={SR}:cl=mono", "-t", f"{max(sec, 0.001):.4f}", str(f)])
        return f
    def prepare(s, conv=False):  # → text for the provider; the segment keeps caption-clean sides
        raw = (s["zh"] if a.lang == "zh" else s["en"]) or s["zh"] or s["en"]
        s["text"] = strip_tags(raw, reactions)                       # what captions show
        if conv and REACTION.search(raw):
            s["_alt"] = with_reactions(raw)                          # what the ASR hears in that turn
        s["zh"], s["en"] = strip_tags(s["zh"], reactions), strip_tags(s["en"], reactions)
        if gemini:
            return PAUSES.sub(_pause, raw if conv or not reactions else strip_reactions(raw))
        return strip_tags(raw, reactions, pauses=False) if a.provider == "minimax" else s["text"]
    def style_of(s):
        return "; ".join(x for x in (a.instruct, s.get("direction")) if x) or None
    err = lambda e: str(e) if isinstance(e, (GeminiError, MinimaxError)) else f"{type(e).__name__}: {e}"
    # every line is prepared first, so the run can be recorded (vo/<lang>/_run.json) before the first provider call:
    # --resume checks the script against it and continues from whatever files that run left
    blocks = []
    for s in segs:
        if blocks and join != "none" and (join == "all" or blocks[-1][-1]["_block"] == s["_block"]):
            blocks[-1].append(s)
        else:
            blocks.append([s])
    convs = [conversational and any(s.get("speaker") for s in blk) for blk in blocks]   # a block without labels stays narration
    for bi, (blk, conv) in enumerate(zip(blocks, convs)):
        if conv and not all(s.get("speaker") for s in blk):
            sys.exit(f"block {bi+1} mixes narration and dialogue: in a gemini conversation every line needs a speaker"
                     f" label ({', '.join(s['id'] for s in blk if not s.get('speaker'))}). Put a blank line between"
                     f" them and use --join block, or use --join none.")
        for s in blk:
            s["_ptext"] = prepare(s, conv)
    lines = [{"id": s["id"], "text": s["_ptext"], "speaker": s.get("speaker"), "direction": s.get("direction"), "block": s["_block"]} for s in segs]
    if man:
        if len(man["lines"]) != len(lines):
            sys.exit(f"--resume: the script changed: the run had {len(man['lines'])} line(s), now {len(lines)}. --resume needs the run's script; drop it to start over")
        for k, (x, y) in enumerate(zip(man["lines"], lines)):
            if x != y:
                what = next(f for f in ("id", "text", "speaker", "direction", "block") if x.get(f) != y.get(f))
                sys.exit(f"--resume: the script changed at line {k+1} (@{y['id']}): {what} was {x.get(what)!r}, now {y.get(what)!r}."
                         f" --resume needs the run's script; drop it to start over")
    else:
        (vo / "_run.json").write_text(json.dumps({"provider": a.provider, "voice": a.voice, "speakers": speakers, "lang": a.lang, "join": join,
                                                  "keep_edges": a.keep_edges, "instruct": a.instruct, "style_env": os.environ.get("GEMINI_TTS_STYLE"),
                                                  **({"env": penv, "pronounce": PRONOUNCE} if a.provider == "minimax" else {}),
                                                  "lines": lines}, ensure_ascii=False, indent=1), encoding="utf-8")
    t, parts, asr_s, asr_n, trimmed = 0.0, [], 0.0, 0, 0.0
    joined = audio / f"voiceover.{a.lang}.wav"
    def write_outputs():
        """voiceover.<lang>.wav, timeline.<lang>.json and the timeline.json / voiceover.wav copies: right after synthesis
        (so a failing ASR call cannot lose the take) and again once the alignment is in."""
        lst = vo / "_concat.txt"; lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
        run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "pcm_s16le", str(joined)])
        tl = {"provider": a.provider, "voice": a.voice, "lang": a.lang, "duration": round(duration(joined), 3),
              **({"grid": {"beats": a.beats, "snap": a.snap, "lead": a.lead}} if grid else {}),
              **({"speakers": speakers} if dialogue else {}), **({"join": join} if join != "none" else {}),
              **({"align": {"model": os.environ.get("GEMINI_ASR_MODEL", "gemini-3.5-transcribe"), "min_sim": a.min_sim}} if align else {}),
              "segments": [{k: v for k, v in s.items() if not k.startswith("_")} for s in segs]}
        body = json.dumps(tl, ensure_ascii=False, indent=2)
        (audio / f"timeline.{a.lang}.json").write_text(body, encoding="utf-8")
        (audio / "timeline.json").write_text(body, encoding="utf-8")
        shutil.copyfile(joined, audio / "voiceover.wav")
        return tl
    def synth_failed(what, e, out, done, total):
        out.unlink(missing_ok=True)                                  # never leave a half-written file for --resume to trust
        sys.exit(f"{what}: synthesis failed: {err(e)}. {done} of {total} are in {vo.relative_to(proj)}; re-run the same command"
                 f" with --resume to synthesize the rest")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        made = []             # the transcribe calls actually made (a --resume that reuses every .asr.json makes none)
        def asr_words(wav):   # (text, words) of a file: from its .asr.json on --resume, else transcribed and saved for a later --resume
            side = wav.with_suffix(".asr.json")
            if a.resume and side.exists():
                c = json.loads(side.read_text(encoding="utf-8")); return c["text"], c["words"]
            txt, ws = transcribe(wav, a.lang, tmp); made.append(wav.name)
            side.write_text(json.dumps({"text": txt, "words": ws}, ensure_ascii=False), encoding="utf-8")
            return txt, ws
        def asr_recheck(wav, vocab):   # the text-only re-check, cached the same way (same vocabulary → same answer)
            side = wav.with_suffix(".asr.json"); c = json.loads(side.read_text(encoding="utf-8")) if side.exists() else {}
            if a.resume and c.get("recheck", {}).get("vocab") == vocab:
                return c["recheck"]["text"]
            txt, _ = transcribe(wav, a.lang, tmp, vocab=vocab); made.append(wav.name)
            c["recheck"] = {"vocab": vocab, "text": txt}; side.write_text(json.dumps(c, ensure_ascii=False), encoding="utf-8")
            return txt
        def shifted(words, h):  # word times after trim_edges cut h s from the head
            return [dict(w, start=max(0.0, w["start"] - h), end=max(0.0, w["end"] - h)) for w in words] if words and h else words
        def linked(blk):        # one minimax request for a block: the lines linked by a pause mark of --gap s, plus any
            text, carry = "", 0.0   # mark written at their edges
            for k, s in enumerate(blk):
                lead, core, trail = split_pauses(s["_ptext"])
                text += (pause_mark(carry + a.gap + lead, a.lang == "en") if k else "") + core; carry = trail
            return text
        if join == "none":
            for i, s in enumerate(segs):
                out = vo / f"{i+1:02d}.wav"; words = None; wfile = out.with_suffix(".words.json")
                if not (a.resume and out.exists() and (wfile.exists() or not timed)):   # --resume: only what the run did not get to
                    voice = speakers.get(s["speaker"], a.voice) if s.get("speaker") else a.voice
                    out.with_suffix(".asr.json").unlink(missing_ok=True)   # a new take gets a new transcription
                    try:
                        words = PROVIDERS[a.provider](s["_ptext"], voice, out, tmp, a.lang, style_of(s))
                        if not a.keep_edges:                           # the provider's own lead-in / tail silence
                            h, tail = trim_edges(out, tmp); trimmed += h + tail
                            words = shifted(words, h)
                        if timed:                                      # kept for --resume
                            wfile.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
                    except Exception as e:
                        synth_failed(f"line {i+1} (@{s['id']})", e, out, f"{i} line(s)", f"{len(segs)}")
                elif timed:
                    words = json.loads(wfile.read_text(encoding="utf-8"))
                d = duration(out); s["_cutlen"] = d
                start = next_start(i == 0, t, s.get("snap"))
                if start > t:
                    parts.append(silence(start - t, i))
                t = start
                s.update(start=round(t, 3), end=round(t + d, 3), file=str(out.relative_to(proj)))
                if words:
                    s["words"] = [{"w": w["w"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in words]
                parts.append(out); t += d
                print(f"  {s['id']:<8} {s['start']:6.2f}–{s['end']:6.2f}s  {(s['speaker'] + ': ') if s.get('speaker') else ''}{s['text']}", flush=True)
            if align:                                                  # every line in parallel, after synthesis
                write_outputs()                                        # the take is on disk before the first ASR call
                t0 = time.time()
                with ThreadPoolExecutor(4) as ex:
                    futs = [ex.submit(asr_words, proj / s["file"]) for s in segs]
                asr_s = time.time() - t0
                for s, f in zip(segs, futs):
                    try:
                        txt, ws = f.result()
                    except Exception as e:                             # quota, network, a bad file: the line keeps its timing
                        s["asr"] = {"error": err(e)}; continue
                    r = align_lines([s["text"]], ws, s["end"] - s["start"])[0]
                    s["asr"] = asr_record(txt, r, a.min_sim)
                    if "words" not in s:
                        s["words"] = [{"w": w["w"], "start": round(s["start"] + w["start"], 3),
                                       "end": round(s["start"] + w["end"], 3)} for w in r["words"]]
        else:
            n = 0
            for bi, (blk, conv) in enumerate(zip(blocks, convs)):
                bout = vo / f"_block{bi+1:02d}.wav"; bwords = bout.with_suffix(".words.json"); pw = None
                if not (a.resume and bout.exists() and (bwords.exists() or not timed)):   # --resume: only the blocks the run did not get to
                    bout.with_suffix(".asr.json").unlink(missing_ok=True)   # a new take gets a new transcription, and new cuts
                    for k in range(len(blk)):                                 # their own re-checks
                        (vo / f"{n + k + 1:02d}.asr.json").unlink(missing_ok=True)
                    try:
                        if gemini:
                            env_style = os.environ.get("GEMINI_TTS_STYLE")
                            turns = [{"text": s["_ptext"], "style": style_of(s) or env_style, "speaker": s.get("speaker") if conv else None} for s in blk]
                            gemini_tts(turns, bout, tmp, gemini_model(a.provider), dict(speakers) if conv else a.voice)
                        elif timed:
                            pw = PROVIDERS[a.provider](linked(blk), a.voice, bout, tmp, a.lang, a.instruct)
                        else:
                            PROVIDERS[a.provider](("" if a.lang == "zh" else " ").join(s["_ptext"] for s in blk), a.voice, bout, tmp, a.lang, a.instruct)
                        if not a.keep_edges:                           # only the block's own edges: pauses inside stay
                            h, tail = trim_edges(bout, tmp); trimmed += h + tail
                            pw = shifted(pw, h)
                        if timed:                                      # kept for --resume
                            bwords.write_text(json.dumps(pw, ensure_ascii=False), encoding="utf-8")
                    except Exception as e:
                        synth_failed(f"block {bi+1} ({', '.join(s['id'] for s in blk)})", e, bout, f"{bi} block(s)", f"{len(blocks)}")
                elif timed:
                    pw = json.loads(bwords.read_text(encoding="utf-8"))
                bd = duration(bout)
                fail = ws = None
                if align:
                    t0 = time.time()
                    try:
                        txt, ws = asr_words(bout)
                    except Exception as e:                             # without the provider's timing the block stays whole and
                        fail = err(e)                                  # its lines share its span; flagged either way
                    asr_s += time.time() - t0
                start = next_start(bi == 0, t, blk[0].get("snap"))
                if start > t:
                    parts.append(silence(start - t, bi))
                t = start
                print(f"  block {bi+1}: {len(blk)} line(s), {bd:.2f} s in one request" + (f" — not transcribed: {fail}" if fail else ""), flush=True)
                texts = [s["text"] for s in blk]
                heard = None if fail or not align else align_lines(texts, ws, bd, {i: s["_alt"] for i, s in enumerate(blk) if s.get("_alt")})
                res = align_lines(texts, pw, bd) if timed else heard or [None] * len(blk)   # line boundaries: the provider's
                for i, (s, r) in enumerate(zip(blk, res)):                                    # word times, else the ASR's
                    n += 1
                    if r is None:
                        s.update(start=round(t, 3), end=round(t + bd, 3), file=str(bout.relative_to(proj)), asr={"error": fail})
                        continue
                    out = vo / f"{n:02d}.wav"; cut(bout, r["cut0"], r["cut1"], out); s["_cutlen"] = r["cut1"] - r["cut0"]
                    s.update(start=round(t + r["start"], 3), end=round(t + r["end"], 3), file=str(out.relative_to(proj)),
                             words=[{"w": w["w"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in r["words"]])
                    if align:
                        s["asr"] = {"error": fail} if fail else asr_record(heard[i]["heard"], heard[i], a.min_sim)
                    print(f"  {s['id']:<8} {s['start']:6.2f}–{s['end']:6.2f}s  {(s['speaker'] + ': ') if s.get('speaker') else ''}{s['text']}", flush=True)
                parts.append(bout); t += bd
        if align:
            terms = vocab_terms([s["text"] for s in segs], a.vocab)
            for s in (x for x in segs if "similarity" in x["asr"].get("flag", "") and x.get("_cutlen", 1.0) >= 0.05 - 1e-6):   # < 50 ms: nothing to hear
                vocab = list(dict.fromkeys(disputed(s["text"], s["asr"]["text"]) + terms))[:100]   # text-only re-check with
                if not vocab:                                          # custom_vocabulary; only extra words heard: nothing to bias toward
                    continue
                t0 = time.time()
                try:
                    txt = asr_recheck(proj / s["file"], vocab)
                except Exception as e:                                 # the line stays flagged; the first pass is kept
                    s["asr"]["recheck"] = {"error": err(e), "vocab": vocab}; continue
                asr_s += time.time() - t0
                s["asr"]["recheck"] = {"text": txt, "similarity": max(similarity(x, txt) for x in (s["text"], s.get("_alt", ""))), "vocab": vocab}
                set_flag(s["asr"], a.min_sim)
    tl = write_outputs(); asr_n = len(made)
    failed = [s for s in segs if "error" in s["asr"]] if align else []
    rechecks = [s for s in segs if "error" in s["asr"].get("recheck", {})] if align else []
    if align:
        sim = lambda s: f"{max(s['asr']['similarity'], s['asr'].get('recheck', {}).get('similarity', 0)):.2f}" if "similarity" in s["asr"] else "none"
        print(f"align: {asr_n} transcribe call(s), {asr_s:.1f} s · similarity " + " ".join(f"{s['id']}={sim(s)}" for s in segs))
        for s in (x for x in segs if x["asr"].get("flag")):
            print(f"  FLAG {s['id']}: {s['asr']['flag']} — heard “{s['asr'].get('recheck', {}).get('text', s['asr']['text'])}”"
                  f" · listen to {s['file']}, then re-run or rewrite the line")
    if trimmed > 0.05:
        print(f"  trimmed {trimmed:.2f} s of provider silence at line edges (--keep-edges to keep it)")
    print(f"→ {joined.relative_to(proj)} ({tl['duration']}s) · audio/timeline.{a.lang}.json · captions: bin/vh captions {a.project}")
    if failed or rechecks:
        ids = lambda xs: ", ".join(s["id"] for s in xs)
        what = (f"{len(failed)} line(s) not transcribed ({ids(failed)}): {failed[0]['asr']['error']}" if failed
                else f"the re-check of {len(rechecks)} flagged line(s) failed ({ids(rechecks)}): {rechecks[0]['asr']['recheck']['error']}")
        kept = f"; the block audio is kept in {vo.relative_to(proj)}/_blockNN.wav and its lines share the block's span" if failed and join != "none" and not timed else ""
        sys.exit(f"align: {what}. The take is written (voiceover and timeline above{kept}); fix the cause, then re-run the same command with --resume to redo only what failed")

if __name__ == "__main__":
    try:
        main()
    except GeminiError as e:       # a voices call that failed for good (synthesis and transcription failures are handled in main)
        sys.exit(str(e))
