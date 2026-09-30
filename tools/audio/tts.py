"""Voiceover synthesis with pluggable providers → per-line WAVs, a joined voiceover and a timeline.

usage (via bin/vh tts): python tools/audio/tts.py <project_dir> [--provider qwen] [--voice V] [--lang zh|en]
                                                 [--gap 0.25] [--instruct "calm, warm"]
                                                 [--beats music.beats.json [--snap beat|half|downbeat] [--lead 0.0]]
                                                 [--align gemini [--min-sim 0.85] [--vocab "术语,Term"]]
                                                 [--join none|block|all]
       (via bin/vh voices): python tools/audio/tts.py voices list [lang] | design "<description>" | delete <voice_id>

Input  <project>/audio/script.txt — one spoken line per row (a line = one caption / cue unit).
       Blank lines and '#' comments are ignored. Optional id prefix "@hook ".
       Bilingual lines use " || ":   @hook 一句话，做出一支片子。 || One sentence in, one film out.
       Per-line direction in [brackets] right after the id, for the voices that can act (gemini; qwen 1.7B instruct):
                                      @hook [惊讶地抛出问题，语速快，"一句话"重读] 一句话，做出一支片子。 || …
       It is added to --instruct for that line only, and never reaches the captions.
       --beats: start every line on the next grid point of a beat map (bin/vh music / bin/vh beats output) instead of a
       fixed --gap, so narration rides the music; --snap picks the grid, --lead the earliest start of line 1.
       A single line can pick its own grid with @id:downbeat (or :beat, :half), e.g. the answer that lands on the drop.
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
       "A=Tingting,B=Meijia" as --voice overrides the header (e.g. a `say` draft of a gemini dialogue).
       |reaction| markers (no space just inside the pipes) are listener backchannels that the other speaker voices in
       a gemini conversation; every other path and the captions drop them, like the <tags> below. Only a script with
       an @speakers header has backchannels: elsewhere |x| is ordinary text (范围是 |x| keeps it).
       Silence the provider leaves before and after a line (below −45 dBFS) is trimmed to 30 ms / 80 ms, so the gap
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
Joined synthesis (--join block|all): consecutive lines go into one request — `block` = runs of lines between blank
       lines in script.txt, `all` = the whole script (8,192 input tokens per gemini request). Prosody flows across
       lines, but a line can no longer be re-run or beat-snapped on its own: only each block's start snaps to the grid
       (with its first line's @id:grid), lines inside keep their natural spacing. Line boundaries are recovered from
       word timestamps, so --join turns --align gemini on; vo/<lang>/NN.wav are then cuts of the block audio.
       A gemini dialogue defaults to --join block (mode "conversational", ≤ 2 speakers, library voices only);
       designed voice_… ids or a third speaker fall back to one request per turn.

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

def gemini_call(path, body=None, method=None, query=None, timeout=180, tries=3):
    """One Gemini REST call. The key travels in a header only, never in the URL or an error message.
    429 / 5xx are retried twice: the TTS docs note rare 500s when the model returns text instead of audio."""
    key = os.environ.get("GEMINI_API_KEY") or sys.exit("set GEMINI_API_KEY (Google AI Studio → Get API key)")
    url = f"{GEMINI_API}/{path}" + (f"?{urllib.parse.urlencode(query, doseq=True)}" if query else "")
    data = None if body is None else json.dumps(body).encode()
    for k in range(tries):
        req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                     headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as e:
            msg = e.read()[:500].decode(errors="replace")
            if e.code in (429, 500, 502, 503, 504) and k < tries - 1:
                time.sleep(3 * (k + 1)); continue
            sys.exit(f"gemini {path.split('/')[0]} error {e.code}: {msg}")
        except (urllib.error.URLError, TimeoutError) as e:
            if k < tries - 1:
                time.sleep(3 * (k + 1)); continue
            sys.exit(f"gemini {path.split('/')[0]}: {e}")

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
    if not shutil.which("say"):                                      # macOS only: a clear exit, not a FileNotFoundError
        sys.exit(f"tts: the `say` provider is macOS-only (no `say` command on {sys.platform}); use "
                 f"{', '.join(p for p in PROVIDERS if p not in ('say', 'qwen'))} (qwen needs Apple Silicon)")
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
        sys.exit(f"gemini: no audio in the response: {json.dumps(resp)[:500]}")
    raw = tmp / "gm.wav"; raw.write_bytes(base64.b64decode(audio[-1]["data"])); to_wav(raw, out)

def p_gemini(text, voice, out: Path, tmp: Path, lang, instruct=None, model=None):
    gemini_tts([{"text": text, "style": instruct or os.environ.get("GEMINI_TTS_STYLE")}], out, tmp,
               model or gemini_model("gemini"), voice)
    return None

def p_gemini_lite(text, voice, out: Path, tmp: Path, lang, instruct=None):
    return p_gemini(text, voice, out, tmp, lang, instruct, model=gemini_model("gemini-lite"))

PROVIDERS = {"qwen": p_qwen, "say": p_say, "edge": p_edge, "dashscope": p_dashscope, "elevenlabs": p_elevenlabs,
             "gemini": p_gemini, "gemini-lite": p_gemini_lite}

TAG = re.compile(r"\s*<([A-Za-z][A-Za-z _-]{0,30})>\s*")        # performance tags such as <short pause>, <breath>, <laugh>
TAGS = ("short pause", "long pause", "breath", "laugh", "sigh", "cough")   # the documented ones: always a tag
REACTION = re.compile(r"\s*\|(?=\S)[^|\n]{1,40}(?<=\S)\|\s*")   # dialogue backchannels such as |mhm|, |oh really?|
CJK_GAP = re.compile(r"(?<=[　-鿿＀-￯]) (?=[　-鿿＀-￯])")

def _tag(m):
    """Another <word> glued to letters/digits on both sides is text, not a tag: `if x<y and y>z` keeps it."""
    s, a, b = m.string, m.start(1) - 1, m.end(1) + 1                       # "<" at a, ">" at b - 1
    glued = a > 0 and s[a - 1].isascii() and s[a - 1].isalnum() and b < len(s) and s[b].isascii() and s[b].isalnum()
    return m.group() if glued and m.group(1).lower() not in TAGS else " "

def strip_tags(text: str, reactions=True) -> str:
    """Remove inline performance tags and (in a dialogue script) |reaction| markers: only gemini voices them; every
    other provider would read them aloud, and captions must never show them. Outside a dialogue |x| is text."""
    text = TAG.sub(_tag, text)
    return CJK_GAP.sub("", re.sub(r" {2,}", " ", REACTION.sub(" ", text) if reactions else text)).strip()

def strip_reactions(text: str) -> str:
    """Remove |reaction| markers only (kept for a gemini conversation, where the other speaker voices them)."""
    return CJK_GAP.sub("", re.sub(r" {2,}", " ", REACTION.sub(" ", text))).strip() if REACTION.search(text) else text

# ---------- script ----------

def parse_script(path: Path):
    """→ (segments, speakers). A blank line closes a block (the unit of --join block)."""
    segs, speakers, block = [], {}, 0
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
    return segs, speakers

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
    on the unit before it, opening quotes and brackets move to the unit after."""
    ms, out, lead = list(UNIT.finditer(text)), [], ""
    if ms:
        lead = text[:ms[0].start()].strip()
    for i, m in enumerate(ms):
        gap = text[m.end(): ms[i + 1].start() if i + 1 < len(ms) else len(text)]
        if re.search(r"\s", gap):
            j = max(k for k, ch in enumerate(gap) if ch.isspace())
            tail, nxt = gap[:j].rstrip(), gap[j + 1:]
        else:
            j = len(gap)
            while j and gap[j - 1] in OPENERS and i + 1 < len(ms):
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

def align_lines(texts, asr_words, dur, alts=None):
    """Map the script lines spoken in one audio file onto its ASR words → per line: speech span, cut points for
    splitting the file, script-spelled words and the similarity to what was heard inside the line's span
    (alts: the same lines with their |reaction| words kept, which the other speaker voices inside the turn)."""
    lines = [script_units(t) for t in texts]
    a = asr_units(asr_words)
    times, res, k = _match([u["n"] for L in lines for u in L], a), [], 0
    for L in lines:
        tt = times[k:k + len(L)]; k += len(L)
        prev = res[-1]["end"] if res else 0.0
        res.append({"units": L, "times": tt, "start": tt[0][0] if tt else prev, "end": tt[-1][1] if tt else prev})
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

TRIM_DB, TRIM_HEAD, TRIM_TAIL = -45.0, 0.03, 0.08     # edges quieter than −45 dBFS; keep 30 ms before the voice, 80 ms after

def trim_edges(wav: Path, tmp: Path):
    """Cut the silence a provider leaves before and after the voice (qwen's Ryan: ~0.43 s, sometimes 2.8 s, at the
    head of every line), keeping a short margin so onsets and decays stay whole. Spacing then comes only from --gap
    or the beat grid. Loudness is measured in 10 ms windows (RMS), so a click or a noise floor does not count as voice.
    Returns the seconds cut from the head (to shift word timings) and from the tail; a file with no voice is left as is."""
    import array
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(wav), "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         check=True, capture_output=True).stdout
    x = array.array("h"); x.frombytes(raw[: len(raw) // 2 * 2])
    n = SR // 100; lim = (10 ** (TRIM_DB / 20) * 32768) ** 2 * n; wins = range(0, len(x), n)
    loud = lambda i: sum(v * v for v in x[i:i + n]) > lim
    first = next((i for i in wins if loud(i)), None)               # scan in from each end: stops at the voice
    if first is None:
        return 0.0, 0.0
    last = next(i for i in reversed(wins) if loud(i))
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
    ap.add_argument("project"); ap.add_argument("--provider", default="qwen", choices=PROVIDERS)
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
    a = ap.parse_args()
    proj = Path(a.project).resolve(); audio = proj / "audio"; script = audio / "script.txt"
    if not script.exists():
        script.parent.mkdir(parents=True, exist_ok=True)
        script.write_text("# 一行一句（= 一条字幕 / 一个 cue）。双语用 ' || ' 分隔：中文 || English。可选 @id 前缀。\n"
                          "@hook 一句话，做出一支片子。 || One sentence in, one film out.\n", encoding="utf-8")
        sys.exit(f"wrote a sample {script} — edit it and re-run")
    segs, speakers = parse_script(script)
    if a.lang is None:                                               # an English-only script is spoken in English
        a.lang = "en" if any(s["en"] for s in segs) and not any(s["zh"] for s in segs) else "zh"
        if a.lang == "en":
            print("  English-only script: speaking it in English (pass --lang zh for the Chinese voice)")
    reactions = bool(speakers)                                       # |…| is a backchannel only under an @speakers header
    if a.voice and "=" in a.voice:                                   # "A=Tingting,B=Meijia" overrides @speakers
        speakers.update(p.split("=", 1) for p in re.split(r"[,\s]+", a.voice) if "=" in p); a.voice = None
    gemini = a.provider.startswith("gemini")
    dialogue = any(s.get("speaker") for s in segs)
    join = a.join if a.join != "auto" else ("block" if gemini and dialogue else "none")
    if join != "none" and dialogue and not gemini:
        print("  note: a dialogue needs one voice per request outside gemini → one request per line (--join none)")
        join = "none"
    conversational = gemini and dialogue and join != "none"
    if conversational and (len(speakers) > 2 or any(v.startswith(("voice_", "voicekey_")) for v in speakers.values())):
        print("  note: a gemini conversation takes at most 2 speakers with library voices; designed voices are synthesized"
              " turn by turn → --join none")
        join, conversational = "none", False
    align = a.align == "gemini" or join != "none"
    if join != "none" and a.align != "gemini":
        print("  --join recovers line boundaries from word timestamps → --align gemini is on")
    vo = audio / "vo" / a.lang; shutil.rmtree(vo, ignore_errors=True); vo.mkdir(parents=True)
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
    def next_start(earliest, which=None):  # first point of the chosen grid at or after `earliest` (past its end: as is)
        g = grids.get(which or a.snap, grid)
        return next((x for x in g if x >= earliest - 1e-6), earliest)
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
        return (raw if conv or not reactions else strip_reactions(raw)) if gemini else s["text"]
    def style_of(s):
        return "; ".join(x for x in (a.instruct, s.get("direction")) if x) or None
    t, parts, asr_s, asr_n, trimmed = 0.0, [], 0.0, 0, 0.0
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        if join == "none":
            for i, s in enumerate(segs):
                text = prepare(s)
                out = vo / f"{i+1:02d}.wav"
                voice = speakers.get(s["speaker"], a.voice) if s.get("speaker") else a.voice
                words = PROVIDERS[a.provider](text, voice, out, tmp, a.lang, style_of(s))
                if not a.keep_edges:                                   # the provider's own lead-in / tail silence
                    h, tl = trim_edges(out, tmp); trimmed += h + tl
                    if words and h:
                        words = [dict(w, start=max(0.0, w["start"] - h), end=max(0.0, w["end"] - h)) for w in words]
                d = duration(out)
                start = (next_start(a.lead if i == 0 else t + a.min_gap, s.get("snap")) if grid
                         else (a.lead if i == 0 else t + a.gap))
                if start > t:
                    parts.append(silence(start - t, i))
                t = start
                s.update(start=round(t, 3), end=round(t + d, 3), file=str(out.relative_to(proj)))
                if words:
                    s["words"] = [{"w": w["w"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in words]
                parts.append(out); t += d
                print(f"  {s['id']:<8} {s['start']:6.2f}–{s['end']:6.2f}s  {(s['speaker'] + ': ') if s.get('speaker') else ''}{s['text']}", flush=True)
            if align:                                                  # every line in parallel, after synthesis
                t0 = time.time()
                with ThreadPoolExecutor(4) as ex:
                    heard = list(ex.map(lambda s: transcribe(proj / s["file"], a.lang, tmp), segs))
                asr_s, asr_n = time.time() - t0, len(segs)
                for s, (txt, ws) in zip(segs, heard):
                    r = align_lines([s["text"]], ws, s["end"] - s["start"])[0]
                    s["asr"] = asr_record(txt, r, a.min_sim)
                    if "words" not in s:
                        s["words"] = [{"w": w["w"], "start": round(s["start"] + w["start"], 3),
                                       "end": round(s["start"] + w["end"], 3)} for w in r["words"]]
        else:
            blocks = []
            for s in segs:
                if blocks and (join == "all" or blocks[-1][-1]["_block"] == s["_block"]):
                    blocks[-1].append(s)
                else:
                    blocks.append([s])
            n = 0
            for bi, blk in enumerate(blocks):
                conv = conversational and any(s.get("speaker") for s in blk)   # a block without labels stays narration
                if conv and not all(s.get("speaker") for s in blk):
                    sys.exit(f"block {bi+1} mixes narration and dialogue: in a gemini conversation every line needs a speaker"
                             f" label ({', '.join(s['id'] for s in blk if not s.get('speaker'))}). Put a blank line between"
                             f" them and use --join block, or use --join none.")
                texts = [prepare(s, conv) for s in blk]
                bout = vo / f"_block{bi+1:02d}.wav"
                if gemini:
                    env_style = os.environ.get("GEMINI_TTS_STYLE")
                    turns = [{"text": x, "style": style_of(s) or env_style, "speaker": s.get("speaker") if conv else None}
                             for x, s in zip(texts, blk)]
                    gemini_tts(turns, bout, tmp, gemini_model(a.provider), dict(speakers) if conv else a.voice)
                else:
                    PROVIDERS[a.provider](("" if a.lang == "zh" else " ").join(texts), a.voice, bout, tmp, a.lang, a.instruct)
                if not a.keep_edges:                                   # only the block's own edges: pauses inside stay
                    h, tl = trim_edges(bout, tmp); trimmed += h + tl
                bd = duration(bout)
                t0 = time.time()
                txt, ws = transcribe(bout, a.lang, tmp)
                asr_s += time.time() - t0; asr_n += 1
                res = align_lines([s["text"] for s in blk], ws, bd, {i: s["_alt"] for i, s in enumerate(blk) if s.get("_alt")})
                start = (next_start(a.lead if bi == 0 else t + a.min_gap, blk[0].get("snap")) if grid
                         else (a.lead if bi == 0 else t + a.gap))
                if start > t:
                    parts.append(silence(start - t, bi))
                t = start
                print(f"  block {bi+1}: {len(blk)} line(s), {bd:.2f} s in one request", flush=True)
                for s, r in zip(blk, res):
                    n += 1
                    out = vo / f"{n:02d}.wav"; cut(bout, r["cut0"], r["cut1"], out)
                    s.update(start=round(t + r["start"], 3), end=round(t + r["end"], 3), file=str(out.relative_to(proj)),
                             words=[{"w": w["w"], "start": round(t + w["start"], 3), "end": round(t + w["end"], 3)} for w in r["words"]])
                    s["asr"] = asr_record(r["heard"], r, a.min_sim)
                    print(f"  {s['id']:<8} {s['start']:6.2f}–{s['end']:6.2f}s  {(s['speaker'] + ': ') if s.get('speaker') else ''}{s['text']}", flush=True)
                parts.append(bout); t += bd
        if align:
            terms = vocab_terms([s["text"] for s in segs], a.vocab)
            for s in (x for x in segs if "similarity" in x["asr"].get("flag", "")):   # text-only re-check with custom_vocabulary
                vocab = list(dict.fromkeys(disputed(s["text"], s["asr"]["text"]) + terms))[:100]
                if not vocab:                                          # only extra words heard: nothing to bias toward
                    continue
                t0 = time.time()
                txt, _ = transcribe(proj / s["file"], a.lang, tmp, vocab=vocab)
                asr_s += time.time() - t0; asr_n += 1
                s["asr"]["recheck"] = {"text": txt, "similarity": max(similarity(x, txt) for x in (s["text"], s.get("_alt", ""))), "vocab": vocab}
                set_flag(s["asr"], a.min_sim)
    for s in segs:
        s.pop("_block", None); s.pop("_alt", None)
    lst = vo / "_concat.txt"; lst.write_text("".join(f"file '{p.name}'\n" for p in parts))
    joined = audio / f"voiceover.{a.lang}.wav"
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "pcm_s16le", str(joined)])
    tl = {"provider": a.provider, "voice": a.voice, "lang": a.lang, "duration": round(duration(joined), 3),
          **({"grid": {"beats": a.beats, "snap": a.snap, "lead": a.lead}} if grid else {}),
          **({"speakers": speakers} if dialogue else {}), **({"join": join} if join != "none" else {}),
          **({"align": {"model": os.environ.get("GEMINI_ASR_MODEL", "gemini-3.5-transcribe"), "min_sim": a.min_sim}} if align else {}),
          "segments": segs}
    body = json.dumps(tl, ensure_ascii=False, indent=2)
    (audio / f"timeline.{a.lang}.json").write_text(body, encoding="utf-8")
    (audio / "timeline.json").write_text(body, encoding="utf-8")
    shutil.copyfile(joined, audio / "voiceover.wav")
    if align:
        print(f"align: {asr_n} transcribe call(s), {asr_s:.1f} s · similarity " +
              " ".join(f"{s['id']}={max(s['asr']['similarity'], s['asr'].get('recheck', {}).get('similarity', 0)):.2f}" for s in segs))
        for s in (x for x in segs if x["asr"].get("flag")):
            print(f"  FLAG {s['id']}: {s['asr']['flag']} — heard “{s['asr'].get('recheck', s['asr'])['text']}”"
                  f" · listen to {s['file']}, then re-run or rewrite the line")
    if trimmed > 0.05:
        print(f"  trimmed {trimmed:.2f} s of provider silence at line edges (--keep-edges to keep it)")
    print(f"→ {joined.relative_to(proj)} ({tl['duration']}s) · audio/timeline.{a.lang}.json · captions: bin/vh captions {a.project}")

if __name__ == "__main__":
    main()
