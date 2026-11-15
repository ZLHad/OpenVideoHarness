"""bin/vh ref digest and ref look: a long video (an interview, a lecture, a documentary, a long reference film) read as
a timed transcript, then looked at where the transcript says to look. The tool takes the speech, the agent writes what
is on the screen. Stdlib, ffmpeg; yt-dlp for a URL; a local Whisper only when there are no subtitles.

usage: bin/vh ref digest <project> <id|url|file> [--subs FILE] [--from auto|subs|asr] [--lang zh] [--chunk 600]
                         [--redo N,N…|all] [--video] [--height 720] [--fetch-model] [--labels zh|en] [--json]
       bin/vh ref look <project> <id> <a-b>[,<a-b>…] [--every S] [--cols 6] [--json]

  digest  a reference's speech as research/digest/<id>/transcript.md, one Markdown file for a person and an agent: a
          section for each chunk of the video (at most --chunk seconds, default 600), and in it the speech as said
          lines, each with its time as a link back to that second (YouTube ?t=, Bilibili ?t=, a file #t=). A URL or a
          file not on record yet is recorded first, as bin/vh ref add records it. Where the speech comes from, first
          found: --subs FILE (SRT, WebVTT, Bilibili's subtitle JSON); a file's subtitles beside it (<name>.srt, .vtt,
          <name>.<lang>.srt) or inside it (a text subtitle stream); a URL's own subtitles through yt-dlp (the uploader's
          first, then Bilibili's AI subtitles or the platform's automatic captions, but only in the language spoken: an
          automatic translation is not what was said, and a translated track the uploader made is marked as one; a
          track matches --lang exactly, else by its main language, en for en-US); then a local Whisper on the audio
          (mlx-whisper, Apple Silicon, the model bin/vh tts --align local uses: WHISPER_MODEL, default
          mlx-community/whisper-large-v3-turbo). --from subs never transcribes; --from asr transcribes even when there
          are subtitles. The model is never downloaded unasked: when it is not in the Hugging Face cache the run stops and
          says so, and --fetch-model lets it fetch (about 1.6 GB, once). A URL that is transcribed has its audio alone
          downloaded (research/digest/<id>/media/); --video also downloads the video (at most --height, default 720),
          so ref look reads it instead of fetching each span.
          Each chunk is cached in chunks/NNN.json under what made it (the subtitles' sha256, or the model, language and
          audio's sha256): a run again redoes only the chunks that are missing, failed (chunks/NNN.err) or made from
          something else, so a run cut short goes on where it stopped and a chunk that failed is the only one redone.
          --redo N,N…|all redoes those. A Whisper chunk ends in the quietest pause within 30 s of its mark, not
          mid-word. Whisper's habit of repeating a line over silence or music is counted and said, not removed.
          transcript.md is written again on every run from the chunks and keeps what you wrote in it. The tool's own
          lines are its head (title, 来源, 口播来自, 注意, 许可, 怎么写), the section headings and the lines tagged 口播
          and 看帧 (said and frames under --labels en); those are written anew. A line "- [mm:ss](link) **tag** text"
          with another tag is yours and is sorted into its place by time, with the lines under it; any other line you
          add goes with the line before it (after a tool line, at that line's time); lines you add to the head stay at
          its end. Tags to use: 画面 (what is in the picture), 屏幕字 (text on the screen, as written), 动作 (what moves,
          what someone does), 注 (a note); picture, on screen, action, note under --labels en.
          Also: said.json (every cue as read: start, end, text), plan.json (the source, the chunks, the looks).
  look    frames of the spans you picked from the transcript (12:30-13:10, 750-790, 1:02:03-1:02:20; several with
          commas): every --every seconds (default the span ÷ 24, at least 0.5 s; at most 60 frames a span; --every
          0.04 is a frame-by-frame strip of a short span), each at its source time, into research/digest/<id>/look/
          <a>-<b>/ (t00751.50.jpg: the second it shows) with a contact sheet labelled by source time (sheet.jpg; pillow
          through uv, else an unlabelled ffmpeg tile). The frames come from the file, from media/video.* when --video
          fetched it, else from that span alone downloaded through yt-dlp (--download-sections, cut at the exact
          second). The transcript gets a 看帧 line at the span's start linking the sheet; what you see goes under it
          in your own lines. Needs ref digest first: read the whole transcript, then pick what to look at.
bin/vh clean leaves research/ alone: media/ and a span's clip.* in look/ can be deleted by hand once read (a run again
fetches them); the transcript, the chunks and the frames are what the work is. A reference is studied, not shown:
reading it does not clear its picture or its sound for the film. A quote goes into NOTES.md's 素材清单 word for word
with its time and source, as the sound has it (subtitles can be the script); a frame or a clip on screen is material: clear it
and register it with bin/vh assets add. Platforms that need a login (Bilibili's AI subtitles, Douyin, WeChat Channels)
are not read through the browser's cookies: download the video or its subtitles yourself and give the file or --subs.
OVH_YTDLP: a command line instead of the yt-dlp on PATH ("uvx yt-dlp"). OVH_DIGEST_ASR: a command line that transcribes
one chunk instead of mlx-whisper (another local ASR; the tests): it gets the WAV and the language and prints
{"segments": [{"start", "end", "text"}]}. Exit: 0 · 1 a chunk failed, no speech to read, a download or a frame failed
(what is done is kept) · 2 usage.
"""
import html, json, os, platform, re, shlex, shutil, subprocess, sys, time, urllib.parse
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "assets"))
import ledger   # noqa: E402

FOLDER = Path("research") / "digest"
DEFAULT_MODEL = "mlx-community/whisper-large-v3-turbo"
out = sys.stdout
LABELS = {
    "zh": {"said": "口播", "frames": "看帧", "kept": ("画面", "屏幕字", "动作", "注"), "source": "来源", "speech": "口播来自",
           "licence": "许可", "how": "怎么写", "length": "时长", "failed": "这一段没读出来", "sheet": "联系表", "every": "每",
           "frames_n": "帧"},
    "en": {"said": "said", "frames": "frames", "kept": ("picture", "on screen", "action", "note"), "source": "Source",
           "speech": "Speech from", "licence": "Licence", "how": "How to add", "length": "length", "failed": "not read",
           "sheet": "contact sheet", "every": "every", "frames_n": "frames"},
}
TOOL_TAGS = {LABELS[k]["said"] for k in LABELS} | {LABELS[k]["frames"] for k in LABELS}
ENTRY = re.compile(r"^- \[((?:\d+:)?\d{1,2}:\d{2}(?:\.\d+)?)(?:[–-][\d:.]+)?\](?:\([^)]*\))? \*\*([^*]+)\*\*")
TIME = re.compile(r"(?:(\d+):)?(\d{1,2}):(\d{1,2}(?:[.,]\d+)?)")
CJK = re.compile(r"[\u3000-\u303f\u3040-\u30ff\u3400-\u9fff\uf900-\ufaff\uac00-\ud7af\uff00-\uffef]")
END = re.compile(r"[.?!。？！…」』”\"]$")


class Usage(Exception):
    """A usage error: exit 2."""


class Fail(Exception):
    """A failure the run cannot get past: exit 1, what is done is kept."""


def say(*a):
    print(*a, file=out, flush=True)


# ---- times ----

def secs(s):
    """'12:30', '1:02:03', '750', '750.5', '12:30.5' → seconds."""
    s = str(s).strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return float(s)
    m = TIME.fullmatch(s)
    if not m:
        raise Usage(f"not a time: {s} (12:30, 1:02:03 or seconds)")
    h, mi, se = m.groups()
    return int(h or 0) * 3600 + int(mi) * 60 + float(se.replace(",", "."))


def stamp(t, long=False, frac=False):
    """Seconds as mm:ss (h:mm:ss when the video is an hour or longer); frac keeps a tenth."""
    t = max(0.0, t)
    whole = int(t)
    h, m, s = whole // 3600, whole // 60 % 60, whole % 60
    tail = f".{int(round((t - whole) * 10)) % 10}" if frac and abs(t - round(t)) > 0.04 else ""
    return (f"{h}:{m:02d}:{s:02d}" if long or h else f"{m:02d}:{s:02d}") + tail


def spans(arg):
    """'12:30-13:10,750-790' → [(750.0, 790.0), …]."""
    res = []
    for part in arg.split(","):
        a, sep, b = part.strip().partition("-")
        if not sep:
            raise Usage(f"a span is a-b: {part}")
        x, y = secs(a), secs(b)
        if y <= x:
            raise Usage(f"a span ends after it starts: {part}")
        res.append((x, y))
    return res


# ---- subtitles ----

def parse_subs(text):
    """SRT, WebVTT (YouTube's rolling automatic captions too) or Bilibili's subtitle JSON → [{start, end, text}]. Tags,
    styling and entities are taken out; in a rolling caption, a line repeated from the cue before is kept once (elsewhere
    a line said twice stays twice). The words are not touched."""
    text = text.lstrip("\ufeff")
    if text.lstrip().startswith("{"):
        try:
            d = json.loads(text)
        except ValueError:
            raise Usage("a subtitle file that starts with { is not JSON")
        return [{"start": float(c["from"]), "end": float(c["to"]), "text": str(c["content"]).strip()}
                for c in d.get("body", []) if str(c.get("content", "")).strip()]
    rolling = "<c>" in text or bool(re.search(r"-->.*align:start position:0%", text))   # YouTube's automatic captions
    cues, last, cur = [], None, None
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if "-->" in raw:
            a, _, b = raw.partition("-->")
            try:
                cur = (secs(a.strip()), secs(b.strip().split()[0]))
            except (Usage, IndexError):
                cur = None
            continue
        if raw == "":   # a cue ends at an empty line; a line of spaces (YouTube's rolling captions) is inside it
            cur = None
            continue
        if cur is None:   # a header, a cue's number or name, a NOTE
            continue
        line = re.sub(r"<[^>]*>", "", raw)
        line = re.sub(r"\{\\[^}]*\}", "", line)
        line = html.unescape(line).replace("\u200b", "").strip()
        if not line or (rolling and line == last):
            continue
        cues.append({"start": round(cur[0], 3), "end": round(cur[1], 3), "text": line})
        last = line
    return cues


def joiner(a, b):
    return "" if a and b and CJK.search(a[-1]) and CJK.search(b[0]) else " "


def paragraphs(cues):
    """Cues joined into said lines: a new line after a pause of 2 s or more, at a sentence's end once a line holds 12 s,
    and at 30 s whatever comes. The words are as the cues have them."""
    paras, cur = [], None
    for c in cues:
        if cur and (c["start"] - cur["end"] >= 2.0 or c["start"] - cur["start"] >= 30
                    or (c["start"] - cur["start"] >= 12 and END.search(cur["text"]))):
            paras.append(cur)
            cur = None
        if cur is None:
            cur = dict(c)
        else:
            cur["text"] += joiner(cur["text"], c["text"]) + c["text"]
            cur["end"] = max(cur["end"], c["end"])
    if cur:
        paras.append(cur)
    return paras


def repeats(cues):
    """How many lines repeat the line before them, three or more in a row (Whisper over silence or music)."""
    n, run = 0, 1
    for x, y in zip(cues, cues[1:]):
        run = run + 1 if x["text"].strip() == y["text"].strip() else 1
        n += run >= 3
    return n


# ---- outside programs ----

def run(argv, what, timeout=None):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise Fail(f"{what}: no {argv[0]} on PATH (bin/vh doctor says how to install it)")
    except subprocess.TimeoutExpired:
        raise Fail(f"{what}: took over {timeout} s")
    if r.returncode != 0:
        last = next((l for l in reversed((r.stderr or r.stdout).strip().splitlines()) if l.strip()), "no message")
        raise Fail(f"{what}: {last.strip()[:300]}")
    return r


def ytdlp():
    return shlex.split(os.environ.get("OVH_YTDLP") or "yt-dlp")


LOGIN = ("Platforms that need a login (Bilibili's AI subtitles, Douyin, WeChat Channels) are not read through the "
         "browser's cookies: download the video or its subtitles yourself and give the file, or --subs FILE")


def probe(path):
    """(duration, has video, has audio, [text subtitle stream index]) of a media file."""
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,codec_name", "-of", "json", str(path)],
            f"ffprobe {path}")
    d = json.loads(r.stdout or "{}")
    st = d.get("streams") or []
    try:
        dur = float((d.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        raise Fail(f"{path}: not a video or audio file ffprobe can read")
    text_subs = [s["index"] for s in st if s.get("codec_type") == "subtitle"
                 and s.get("codec_name") in ("subrip", "ass", "ssa", "mov_text", "webvtt", "text")]
    return dur, any(s.get("codec_type") == "video" for s in st), any(s.get("codec_type") == "audio" for s in st), text_subs


def sha(p):
    return ledger.sha256_file(p)


# ---- the reference ----

def ensure_ref(project, target, a):
    """The reference's record: by id, or by URL or file (recorded first, as ref add does)."""
    import refs, sources
    d = refs.read(project)
    recs = [r for r in d["assets"] if isinstance(r, dict)]
    by_id = {r.get("id"): r for r in recs}
    if target in by_id:
        return by_id[target]
    if target.startswith(("http://", "https://")):
        try:
            plat, _, nid = sources.platform_of(target)
        except sources.SourceError as e:
            raise Usage(str(e))
        for r in recs:
            s = r.get("source") or {}
            if s.get("url") == target or (nid and s.get("provider") == plat and s.get("provider_id") == nid):
                return r
    else:
        f = ledger.find_file(project, target)
        if f is None:
            raise Usage(f"{target}: not a reference id ({', '.join(sorted(by_id)) or 'none on record'}), a URL or a file")
        same = next((r for r in recs if r.get("path") == ledger.rel(project, f)), None)
        if same:
            return same
    argv = ["add", str(project), target, "--type", "video"]
    for flag, v in (("--title", a.title), ("--why", a.why)):
        if v:
            argv += [flag, v]
    refs.out = out
    try:
        refs.cmd_add(refs.parser().parse_args(argv))
    except refs.Usage as e:
        raise Usage(str(e))
    after = refs.read(project)["assets"]
    if len(after) <= len(d["assets"]):
        raise Fail(f"{target} could not be recorded (bin/vh ref add said why above)")
    return after[-1]


def source_of(project, rec):
    """{kind: file|url, file, url, platform, id, title} for a record."""
    src = rec.get("source") or {}
    if src.get("url"):
        return {"kind": "url", "url": src["url"], "platform": src.get("provider"), "id": src.get("provider_id"),
                "title": src.get("title"), "ref": rec["id"]}
    p = Path(rec["path"])
    f = p if p.is_absolute() else Path(project) / p
    return {"kind": "file", "file": str(f.resolve()), "title": src.get("title") or f.stem, "ref": rec["id"]}


def link(src, t, folder):
    """The time as a link back to that second."""
    s = int(t)
    if src["kind"] == "url":
        u, plat = src["url"], src.get("platform")
        if plat == "youtube" and src.get("id"):
            return f"https://www.youtube.com/watch?v={src['id']}&t={s}s"
        if plat == "bilibili" and src.get("id"):
            return f"https://www.bilibili.com/video/{src['id']}?t={s}"
        return u
    rel = os.path.relpath(src["file"], folder)
    return urllib.parse.quote(Path(rel).as_posix()) + f"#t={s}"


# ---- where the speech comes from ----

def info_of(src, folder):
    """yt-dlp's -J for a URL, the parts digest reads, cached in info.json."""
    f = folder / "info.json"
    if f.is_file():
        return json.loads(f.read_text(encoding="utf-8"))
    r = run(ytdlp() + ["-J", "--no-playlist", "--no-warnings", src["url"]], f"yt-dlp on {src['url']}", timeout=300)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        raise Fail(f"yt-dlp on {src['url']} printed no JSON")
    keep = {"title": d.get("title"), "duration": d.get("duration"), "language": d.get("language"), "uploader": d.get("uploader"),
            "subtitles": {k: [x.get("ext") for x in v] for k, v in (d.get("subtitles") or {}).items()},
            "automatic_captions": sorted((d.get("automatic_captions") or {}).keys())}
    f.write_text(json.dumps(keep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return keep


def base(k):
    """A track's main language: en for en-US and en-orig, zh for zh-Hans and Bilibili's ai-zh."""
    k = (k or "").lower()
    return (k[3:] if k.startswith("ai-") else k).split("-")[0]


MACHINE = {"en": "these captions are a machine transcription: listen to the seconds of a quote before using it",
           "zh": "这份字幕是机器转写的：引用前回原片听那几秒"}


def pick_track(info, lang):
    """(kind, key, note) of the track to read, or (None, None, why). kind: 'subtitles' (the uploader's), 'ai' (Bilibili's
    AI subtitles, listed among them) or 'automatic' (the platform's automatic captions, only in the language spoken: in
    another one they are a machine translation). A track matches a language exactly first, then by its main language
    (en for en-US). A note is {"en", "zh"}: it goes into the transcript's head in its labels' language."""
    spoken = info.get("language")
    autos = info.get("automatic_captions") or []
    spoken = spoken or next((k[:-5] for k in autos if k.endswith("-orig")), None)
    listed = [k for k in (info.get("subtitles") or {}) if k not in ("danmaku", "live_chat", "rechat")]
    ai = [k for k in listed if k.lower().startswith("ai-")]
    human = [k for k in listed if k not in ai]
    want = lang or spoken

    def first(keys, lng):
        if not lng:
            return None
        return next((k for k in keys if k.lower() == lng.lower()), None) or next((k for k in keys if base(k) == base(lng)), None)

    k = first(human, want)
    if k:
        if spoken and base(k) != base(spoken):
            return "subtitles", k, {"en": f"a translation the uploader gave ({k}), not the words as spoken ({spoken}): quote the spoken language",
                                    "zh": f"上传者给的译文字幕（{k}），不是原话（说的是 {spoken}）：引用要用原话"}
        return "subtitles", k, None
    if spoken and lang and base(lang) != base(spoken):
        k = first(human, spoken)
        if k:
            return "subtitles", k, {"en": f"no {lang} subtitles: the spoken language's ({k})", "zh": f"没有 {lang} 字幕，读的是原话的字幕（{k}）"}
    if not spoken and not lang and human:
        k = human[0]
        return "subtitles", k, (None if len(human) == 1 else
                                {"en": f"the language spoken is not stated: {k} read, of {', '.join(human)} (--lang picks another)",
                                 "zh": f"平台没说讲的是什么语言：读的是 {k}（还有 {', '.join(x for x in human if x != k)}，--lang 可换）"})
    if not lang or not spoken or base(lang) == base(spoken):
        k = first(ai, spoken or lang) or (ai[0] if ai and not (spoken or lang) else None)
        if k:
            return "ai", k, MACHINE
        for k in ((f"{spoken}-orig", spoken) if spoken else ()):
            if k in autos:
                return "automatic", k, MACHINE
    why = "no subtitles"
    if lang and spoken and base(lang) != base(spoken) and autos:
        why = f"no {lang} subtitles; the automatic {lang} captions are a machine translation of the {spoken} speech, not what was said"
    elif "danmaku" in (info.get("subtitles") or {}) and not listed:
        why = "no subtitles (Bilibili's danmaku are comments; its AI subtitles need a login)"
    return None, None, why


def fetch_track(src, folder, kind, key):
    """The track as yt-dlp writes it (subs/track.<key>.<ext>); one fetched before is read again, not fetched."""
    d = folder / "subs"
    d.mkdir(parents=True, exist_ok=True)
    had = [p for p in d.glob(f"track.{glob_escape(key)}.*") if p.suffix.lower() in (".vtt", ".srt", ".json")]
    if had:
        return had[0]
    for old in d.glob("track.*"):
        old.unlink()
    flag = "--write-auto-subs" if kind == "automatic" else "--write-subs"
    run(ytdlp() + ["--skip-download", "--no-playlist", "--no-warnings", flag, "--sub-langs", key, "--sub-format", "vtt/srt/best",
                   "-o", str(d / "track.%(ext)s"), src["url"]], f"yt-dlp subtitles {key} of {src['url']}", timeout=300)
    got = [p for p in d.glob(f"track.{glob_escape(key)}.*") if p.suffix.lower() in (".vtt", ".srt", ".json")] or \
          [p for p in d.glob("track.*") if p.suffix.lower() in (".vtt", ".srt", ".json")]
    if not got:
        raise Fail(f"yt-dlp wrote no {key} subtitles for {src['url']}")
    return got[0]


def sidecar_subs(f, lang):
    """Subtitles beside a file: <name>.srt / .vtt, <name>.<lang>.srt …"""
    f = Path(f)
    cands = [f.with_suffix(e) for e in (".srt", ".vtt")]
    for e in ("srt", "vtt"):
        cands += sorted(f.parent.glob(f"{glob_escape(f.stem)}.*.{e}"), key=lambda p: (lang and f".{lang}" not in p.name, p.name))
    return next((p for p in cands if p.is_file()), None)


def glob_escape(s):
    return re.sub(r"([*?\[])", r"[\1]", s)


def embedded_subs(f, folder, idx):
    d = folder / "subs"
    d.mkdir(parents=True, exist_ok=True)
    dst = d / "embedded.srt"
    run(["ffmpeg", "-v", "error", "-y", "-i", str(f), "-map", f"0:{idx}", "-f", "srt", str(dst)], f"ffmpeg subtitles of {f}")
    return dst


def finished(d, stem):
    """The files yt-dlp finished as <stem>.<ext> in d (not a .part, not a format it has yet to merge, <stem>.f399.mp4)."""
    return sorted(p for p in d.glob(f"{stem}.*") if re.fullmatch(rf"{stem}\.[A-Za-z0-9]+", p.name) and p.suffix not in (".part", ".ytdl")) if d.is_dir() else []


def fetch_media(src, folder, video, height):
    """A URL's audio (or its video, --video) in media/, as yt-dlp names it; a download cut short goes on (yt-dlp's
    .part)."""
    d = folder / "media"
    d.mkdir(parents=True, exist_ok=True)
    stem = "video" if video else "audio"
    done = finished(d, stem)
    if done:
        return done[0]
    fmt = f"bv*[height<={height}]+ba/b[height<={height}]/b" if video else "ba/b"
    argv = ytdlp() + ["-f", fmt, "--no-playlist", "--no-warnings", "--continue", "-o", str(d / f"{stem}.%(ext)s"), src["url"]]
    if video:
        argv[-1:-1] = ["--merge-output-format", "mp4"]
    say(f"  downloading the {stem} of {src['url']} (yt-dlp) …")
    run(argv, f"yt-dlp {stem} of {src['url']}", timeout=6 * 3600)
    done = finished(d, stem)
    if not done:
        raise Fail(f"yt-dlp wrote no {stem} for {src['url']}")
    return done[0]


def hf_snapshot(model):
    hub = os.environ.get("HF_HUB_CACHE") or os.path.join(os.environ.get("HF_HOME") or os.path.expanduser("~/.cache/huggingface"), "hub")
    base = Path(hub) / ("models--" + model.replace("/", "--")) / "snapshots"
    for snap in sorted(base.glob("*")) if base.is_dir() else []:
        if any(snap.glob("*.safetensors")) or any(snap.glob("*.npz")):
            return snap
    return None


def asr_ready(fetch_model):
    """None when a transcription can start here, else what is missing."""
    if os.environ.get("OVH_DIGEST_ASR"):
        return None
    if not (sys.platform == "darwin" and platform.machine() == "arm64"):
        return ("the local Whisper here is mlx-whisper, for Apple Silicon only; on this machine transcribe with whisper.cpp "
                "or FunASR (playbook/04-audio.md) and give the SRT with --subs, or set OVH_DIGEST_ASR to a command that does it")
    if not shutil.which("uv"):
        return "uv runs mlx-whisper and is not on PATH (bin/vh doctor says how to install it), or give subtitles with --subs"
    model = os.environ.get("WHISPER_MODEL", DEFAULT_MODEL)
    if not fetch_model and "/" in model and not Path(model).exists() and hf_snapshot(model) is None:
        return (f"the Whisper model {model} is not on this machine (about 1.6 GB for the default): run again with "
                "--fetch-model to download it once, or give subtitles with --subs")
    return None


def asr_chunk(wav, lang, fetch_model, timeout):
    env = dict(os.environ)
    cmd = os.environ.get("OVH_DIGEST_ASR")
    if cmd:
        argv = shlex.split(cmd) + [str(wav), lang or ""]
    else:
        argv = ["uv", "run", "-q", "--no-project", "--with", "mlx-whisper", "python", str(HERE / "digest_asr.py"), str(wav), lang or ""]
        if not fetch_model:
            env["HF_HUB_OFFLINE"] = "1"
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        raise Fail(f"the transcription took over {timeout} s")
    except FileNotFoundError:
        raise Fail(f"no {argv[0]} on PATH")
    if r.returncode != 0:
        last = next((l for l in reversed(r.stderr.strip().splitlines()) if l.strip()), f"exit {r.returncode}")
        raise Fail(f"the transcription failed: {last.strip()[:300]}")
    try:
        d = json.loads(r.stdout)
        return [{"start": float(s["start"]), "end": float(s["end"]), "text": str(s["text"]).strip()} for s in d["segments"] if str(s.get("text", "")).strip()]
    except (ValueError, KeyError, TypeError):
        raise Fail("the transcription printed no {\"segments\": […]}")


def silences(media, folder, key):
    """The pauses of a media file's sound, [(start, end)], cached in plan.json's way (silences.json under its key)."""
    f = folder / "silences.json"
    if f.is_file():
        d = json.loads(f.read_text(encoding="utf-8"))
        if d.get("key") == key:
            return [tuple(x) for x in d["silences"]]
    r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(media), "-vn", "-af", "silencedetect=noise=-35dB:d=0.3", "-f", "null", "-"],
                       capture_output=True, text=True)
    res, start = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and start is not None:
            res.append((start, float(m.group(1))))
            start = None
    f.write_text(json.dumps({"key": key, "silences": res}) + "\n", encoding="utf-8")
    return res


def bounds(duration, chunk, pauses=None):
    """[(start, end)] chunks of at most about chunk seconds; with pauses each mark moves to the middle of the longest
    pause within 30 s of it."""
    marks, t = [], chunk
    while t < duration - min(60, chunk / 4):
        m = t
        if pauses:
            near = [(e - s, (s + e) / 2) for s, e in pauses if abs((s + e) / 2 - t) <= 30]
            if near:
                m = max(near)[1]
        marks.append(round(m, 3))
        t = m + chunk
    edges = [0.0] + marks + [round(duration, 3)]
    return list(zip(edges, edges[1:]))


# ---- the transcript ----

HEAD_TOOL = ("# ", "<!--", "- 来源：", "- 口播来自：", "- 注意：", "- 许可：", "- 怎么写：",
             "- Source: ", "- Speech from: ", "- Mind: ", "- Licence: ", "- How to add: ")
SECTION = re.compile(r"^## \d+ · ((?:\d+:)?\d+:\d{2})")


def kept_entries(path):
    """What you wrote in transcript.md: ([(time, [lines])], [head lines]). In the sections, an entry "- [mm:ss](link)
    **tag** …" whose tag is not the tool's starts one at its time; any other line that is not the tool's (a section
    heading, a said or frames line, a blank line) goes with the entry before it, or after the tool line before it at
    that line's time, so nothing written there is lost. Above the first section, the lines the tool does not write."""
    if not path.is_file():
        return [], []
    res, head, cur, anchor, body = [], [], None, 0.0, False
    for line in path.read_text(encoding="utf-8").splitlines():
        sec = SECTION.match(line)
        if sec or line.startswith("## "):
            body, cur = True, None
            anchor = secs(sec.group(1)) if sec else anchor
            continue
        if not body:
            if line.strip() and not line.startswith(HEAD_TOOL):
                head.append(line)
            continue
        if not line.strip():
            continue
        m = ENTRY.match(line)
        if m and m.group(2).strip() in TOOL_TAGS:
            anchor, cur = secs(m.group(1)), None
            continue
        if m:
            cur = (secs(m.group(1)), [line])
            res.append(cur)
            continue
        if cur is None:
            cur = (anchor, [])
            res.append(cur)
        cur[1].append(line)
    return res, head


def write_transcript(folder, plan, chunks, labels):
    L = LABELS[labels]
    src, long = plan["source"], plan["duration"] >= 3600
    path = folder / "transcript.md"
    yours, head_yours = kept_entries(path)
    rows = []   # (time, order, [lines])
    for i, (a, b) in enumerate(plan["chunks"]):
        c = chunks.get(i)
        if c and "lines" in c:
            for p in paragraphs(c["lines"]):
                rows.append((p["start"], 0, [f"- [{stamp(p['start'], long)}]({link(src, p['start'], folder)}) **{L['said']}** {p['text']}"]))
        else:
            err = (c or {}).get("error", "")
            why = (f"（{L['failed']}：{err}）" if err else f"（{L['failed']}）") if labels == "zh" else (f"({L['failed']}: {err})" if err else f"({L['failed']})")
            rows.append((a, 0, [f"- [{stamp(a, long)}]({link(src, a, folder)}) **{L['said']}** {why}"]))
    for lk in plan.get("looks", []):
        rows.append((lk["a"], 1, [f"- [{stamp(lk['a'], long)}–{stamp(lk['b'], long)}]({link(src, lk['a'], folder)}) **{L['frames']}** "
                                  f"{len(lk['frames'])} {L['frames_n']}，{L['every']} {lk['every']:g} s · [{L['sheet']}]({lk['sheet']})"]))
    for t, lines in yours:
        rows.append((t, 2, lines))
    rows.sort(key=lambda r: (int(r[0]), r[1], r[0]))   # by the second a line shows: yours after the tool's in that second
    title = src.get("title") or plan["ref"]
    where = f"[{title}]({src['url']})" if src["kind"] == "url" else f"[{title}]({urllib.parse.quote(Path(os.path.relpath(src['file'], folder)).as_posix())})"
    if labels == "zh":
        head = [f"# {title}", "",
                "<!-- bin/vh ref digest：每次运行都按 chunks/ 重写这份文件。标 口播、看帧 的行是工具写的；其余形如 "
                "\"- [mm:ss](链接) **标签** 内容\" 的行是你写的，连同它下面的行一起保留，按时间排回原处；别的行跟着它前面那一行走。"
                "页头（这一段到第一节之间）除了工具写的几行，你加的也保留。 -->", "",
                f"- {L['source']}：{where} · `{plan['ref']}` · {L['length']} {stamp(plan['duration'], long)}",
                f"- {L['speech']}：{plan['speech_note']}"]
        head += [f"- 注意：{n}" for n in plan.get("warnings", [])]
        head += [f"- {L['licence']}：读过不等于能用。原话进 NOTES.md 的素材清单要逐字照抄、带时间码和出处，以原片的声音为准（字幕可能是讲稿，转写可能听错），引用前听那几秒；画面或声音要上屏，先 `bin/vh assets add` 登记许可。",
                 f"- {L['how']}：先读完整份文稿，挑要看的片段 `bin/vh ref look <项目> {plan['ref']} 12:30-13:10`；看完帧，在那个时间下面加 "
                 "`- [mm:ss](链接) **画面** …`（标签：画面、屏幕字、动作、注）。"]
    else:
        head = [f"# {title}", "",
                "<!-- bin/vh ref digest: this file is written again from chunks/ on every run. Lines tagged said and frames are "
                "the tool's; any other line of the form \"- [mm:ss](link) **tag** text\" is yours, kept with the lines under it "
                "and sorted back into place by time; any other line goes with the line before it. Lines you add to this head are "
                "kept too. -->", "",
                f"- {L['source']}: {where} · `{plan['ref']}` · {L['length']} {stamp(plan['duration'], long)}",
                f"- {L['speech']}: {plan['speech_note']}"]
        head += [f"- Mind: {n}" for n in plan.get("warnings", [])]
        head += [f"- {L['licence']}: read is not cleared. A quote goes into NOTES.md word for word with its time and source, as the sound has it "
                 "(subtitles can be the script, a transcription can mishear): listen to those seconds first. A frame or a sound on screen is "
                 "material: `bin/vh assets add` first.",
                 f"- {L['how']}: read the whole transcript, pick spans with `bin/vh ref look <project> {plan['ref']} 12:30-13:10`; after "
                 "the frames, add `- [mm:ss](link) **picture** …` under that time (tags: picture, on screen, action, note)."]
    if head_yours:
        head += [""] + head_yours
    body = []
    for i, (a, b) in enumerate(plan["chunks"]):
        body += ["", f"## {i + 1} · {stamp(a, long)}–{stamp(b, long)}", ""]
        last = i == len(plan["chunks"]) - 1
        for t, _, lines in rows:
            if a <= t < b or (last and t >= b) or (i == 0 and t < a):
                body += lines
    tmp = path.with_suffix(".md.tmp")
    tmp.write_text("\n".join(head + body) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path, len(yours) + bool(head_yours)


# ---- digest ----

def write_json(f, d):
    tmp = f.with_suffix(f.suffix + ".tmp")
    tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, f)


def load_plan(folder):
    f = folder / "plan.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


def cmd_digest(a, project):
    if a.chunk < 60:
        raise Usage("--chunk is at least 60 seconds")
    rec = ensure_ref(project, a.target.strip(), a)
    if rec.get("kind") not in ("video", None) and (rec.get("ref") or {}).get("type") != "video":
        raise Usage(f"{rec['id']} is a {(rec.get('ref') or {}).get('type') or rec.get('kind')}, not a video")
    src = source_of(project, rec)
    if src["kind"] == "url" and "…" in src["url"]:
        raise Fail(f"{rec['id']}: the URL on record is shortened ({src['url']}: ref add keeps a page's query out of the record); "
                   "download the video and give the file")
    folder = Path(project) / FOLDER / rec["id"]
    (folder / "chunks").mkdir(parents=True, exist_ok=True)
    old = load_plan(folder) or {}
    labels = a.labels or old.get("labels") or "zh"
    warnings = []
    say(f"{rec['id']} · {src.get('title') or src.get('url') or src.get('file')}")

    # where the speech comes from
    subs, speech_note, media, duration = None, None, None, None
    if src["kind"] == "file":
        if not Path(src["file"]).is_file():
            raise Fail(f"{src['file']}: the file on record is not there")
        duration, has_v, has_a, text_subs = probe(src["file"])
        media = Path(src["file"])
    if a.subs:
        subs = Path(a.subs).expanduser()
        if not subs.is_file():
            raise Usage(f"--subs {a.subs}: no such file")
        speech_note = f"the subtitles given ({subs.name})" if labels == "en" else f"给的字幕文件（{subs.name}）"
    elif a.from_ != "asr":
        if src["kind"] == "file":
            side = sidecar_subs(src["file"], a.lang)
            if side:
                subs = side
                speech_note = f"the subtitles beside the file ({side.name})" if labels == "en" else f"文件旁边的字幕（{side.name}）"
            elif text_subs:
                subs = embedded_subs(src["file"], folder, text_subs[0])
                speech_note = "the file's own subtitle track" if labels == "en" else "文件自带的字幕轨"
        else:
            try:
                info = info_of(src, folder)
            except Fail as e:
                raise Fail(f"{e}. {LOGIN}")
            duration = float(info.get("duration") or 0) or None
            kind, key, note = pick_track(info, a.lang)
            if kind:
                subs = fetch_track(src, folder, kind, key)
                what = {"subtitles": ("the uploader's subtitles", "上传者的字幕"), "ai": ("the platform's AI subtitles", "平台的 AI 字幕"),
                        "automatic": ("the platform's automatic captions", "平台的自动字幕")}[kind]
                speech_note = f"{what[0]} ({key}, yt-dlp)" if labels == "en" else f"{what[1]}（{key}，yt-dlp）"
                if note:
                    warnings.append(note[labels])
            else:
                say(f"  {note}")
                if a.from_ == "subs":
                    raise Fail(f"{note}. {LOGIN}")
    if subs is None and a.from_ == "subs":
        raise Fail(f"no subtitles found for {rec['id']} (--from subs never transcribes): give them with --subs FILE")

    if subs is not None:
        cues = sorted(parse_subs(subs.read_text(encoding="utf-8", errors="replace")), key=lambda c: c["start"])
        if not cues:
            raise Fail(f"{subs}: no cues read (SRT, WebVTT or Bilibili's subtitle JSON)")
        key = "subs:" + sha(subs)
        if duration is None:
            duration = max(c["end"] for c in cues)
        plan_chunks = bounds(duration, a.chunk)
    else:
        why = asr_ready(a.fetch_model)
        if why:
            raise Fail(f"no subtitles, and no transcription here: {why}")
        if src["kind"] == "url":
            try:
                media = fetch_media(src, folder, a.video, a.height)
            except Fail as e:
                raise Fail(f"{e}. {LOGIN}")
            duration = probe(media)[0]
        elif not has_a:
            raise Fail(f"{src['file']} has no sound to transcribe")
        model = "cmd:" + os.environ["OVH_DIGEST_ASR"] if os.environ.get("OVH_DIGEST_ASR") else os.environ.get("WHISPER_MODEL", DEFAULT_MODEL)
        msha = sha(media)
        key = f"asr:{model}:{a.lang or 'auto'}:{msha}"
        plan_chunks = bounds(duration, a.chunk, silences(media, folder, msha))
        speech_note = (f"a local transcription ({model.rsplit('/', 1)[-1]}; check a quote against the sound)" if labels == "en"
                       else f"本机转写（{model.rsplit('/', 1)[-1]}；引用前听原片核对）")
    if src["kind"] == "url" and a.video:
        try:
            fetch_media(src, folder, True, a.height)
        except Fail as e:
            warnings.append(f"the video was not downloaded: {e}")

    # the chunks
    redo = set(range(len(plan_chunks))) if a.redo == "all" else {int(x) - 1 for x in (a.redo or "").split(",") if x.strip().isdigit()}
    chunks, failed, made = {}, [], 0
    for i, (s, e) in enumerate(plan_chunks):
        f, ferr = folder / "chunks" / f"{i + 1:03d}.json", folder / "chunks" / f"{i + 1:03d}.err"
        if i not in redo and f.is_file():
            c = json.loads(f.read_text(encoding="utf-8"))
            if c.get("from") == key and c.get("start") == s and c.get("end") == e:
                chunks[i] = c
                ferr.unlink(missing_ok=True)
                continue
        try:
            if subs is not None:
                last = i == len(plan_chunks) - 1
                lines = [c for c in cues if s <= c["start"] < e or (last and c["start"] >= e)]
            else:
                wav = folder / "chunks" / f"{i + 1:03d}.wav"
                run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", str(media), "-vn", "-ac", "1", "-ar", "16000", str(wav)],
                    f"ffmpeg chunk {i + 1}")
                t0 = time.time()
                say(f"  chunk {i + 1}/{len(plan_chunks)} · {stamp(s)}–{stamp(e)} · transcribing …")
                segs = asr_chunk(wav, a.lang, a.fetch_model, timeout=int(max(600, (e - s) * 4)))
                wav.unlink(missing_ok=True)
                lines = [{"start": round(s + x["start"], 3), "end": round(s + x["end"], 3), "text": x["text"]} for x in segs]
                say(f"    {len(lines)} lines in {time.time() - t0:.0f} s")
            c = {"v": 1, "i": i + 1, "start": s, "end": e, "from": key, "lines": lines, "repeats": repeats(lines), "at": ledger.iso()}
            write_json(f, c)
            ferr.unlink(missing_ok=True)
            chunks[i] = c
            made += 1
        except Fail as x:
            ferr.write_text(str(x) + "\n", encoding="utf-8")
            f.unlink(missing_ok=True)
            chunks[i] = {"error": str(x)}
            failed.append(i + 1)
            say(f"  ✗ chunk {i + 1}: {x}")
    for extra in sorted((folder / "chunks").glob("*.*")):   # chunks of an older, longer plan
        if extra.suffix in (".json", ".err", ".wav") and (not extra.stem.isdigit() or int(extra.stem) > len(plan_chunks)):
            extra.unlink()
    rep = [(i + 1, c["repeats"]) for i, c in chunks.items() if c.get("repeats")]
    if rep:
        warnings.append(("lines repeated three or more times in a row (chunk: count) " if labels == "en" else "连续重复三次以上的句子（段：处）")
                        + ", ".join(f"{i}: {n}" for i, n in rep)
                        + (" — Whisper does this over silence or music: listen before quoting" if labels == "en" else "，Whisper 在静音或音乐上常这样，引用前听原片"))

    plan = {"v": 1, "ref": rec["id"], "source": src, "duration": round(duration, 3), "chunk": a.chunk, "chunks": plan_chunks,
            "from": key, "speech_note": speech_note, "lang": a.lang, "labels": labels, "warnings": warnings,
            "media": ledger.rel(project, media) if media is not None and src["kind"] == "url" else None, "height": a.height,
            "looks": [lk for lk in old.get("looks", []) if lk["b"] <= duration + 1], "at": ledger.iso()}
    write_json(folder / "plan.json", plan)
    allc = [x for i in sorted(chunks) for x in chunks[i].get("lines", [])]
    write_json(folder / "said.json", {"v": 1, "ref": rec["id"], "from": key, "cues": allc})
    path, kept = write_transcript(folder, plan, chunks, labels)
    n_said = sum(len(paragraphs(c.get("lines", []))) for c in chunks.values())
    say(f"✓ {ledger.rel(project, path)} · {len(plan_chunks)} chunk{'s' if len(plan_chunks) != 1 else ''} "
        f"({made} made, {len(plan_chunks) - made - len(failed)} from the cache{f', {len(failed)} failed' if failed else ''}) · "
        f"{n_said} said lines · {kept} of yours kept · {stamp(duration)}")
    say(f"  speech: {speech_note}")
    for w in warnings:
        say(f"  ! {w}")
    if failed:
        say(f"  chunks {', '.join(map(str, failed))} failed (chunks/NNN.err): run the same command again, only those are redone")
    else:
        say(f"  next: read it all, then bin/vh ref look {Path(project).name} {rec['id']} <a-b>[,<a-b>…] where the picture matters")
    if a.json:
        print(json.dumps({"version": 1, "project": str(project), "transcript": str(path), "plan": plan, "failed": failed, "made": made},
                         ensure_ascii=False, indent=1))
    return 1 if failed else 0


# ---- look ----

def section(src, folder, a_, b_, dest):
    """One span of a URL's video, cut at the exact second (yt-dlp --download-sections, keyframes forced at the cuts)."""
    span, mark = f"{a_:.3f}-{b_:.3f}", dest / "clip.span"
    got = finished(dest, "clip")
    if got and got[0].stat().st_size and mark.is_file() and mark.read_text().strip() == span:
        return got[0]
    for old in got:
        old.unlink()
    h = (load_plan(folder) or {}).get("height") or 720
    run(ytdlp() + ["-f", f"bv*[height<={h}]/b[height<={h}]/b", "--no-playlist", "--no-warnings", "--download-sections", f"*{a_:.3f}-{b_:.3f}",
                   "--force-keyframes-at-cuts", "-o", str(dest / "clip.%(ext)s"), src["url"]],
        f"yt-dlp {stamp(a_)}–{stamp(b_)} of {src['url']}", timeout=1800)
    got = finished(dest, "clip")
    if not got:
        raise Fail(f"yt-dlp wrote no clip for {stamp(a_)}–{stamp(b_)}")
    mark.write_text(span + "\n")
    return got[0]


def sheet(dest, cols, names):
    """sheet.jpg from the frames: tools/sheet.py's folder mode through uv (captions: the source times), else ffmpeg's tile."""
    out_, png = dest / "sheet.jpg", dest.parent / f".{dest.name}-sheet.png"
    out_.unlink(missing_ok=True)   # not a tile of the next sheet
    if shutil.which("uv"):
        r = subprocess.run(["uv", "run", "-q", "--no-project", "--with", "pillow", "python", str(ROOT / "tools" / "sheet.py"), str(dest),
                            str(png), str(cols), "-", "320"], capture_output=True, text=True)
        if r.returncode == 0 and png.is_file():
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-q:v", "3", str(out_)], capture_output=True)
            png.unlink(missing_ok=True)
            if out_.is_file():
                return out_, True
    rows = max(1, -(-len(names) // cols))
    run(["ffmpeg", "-v", "error", "-y", "-pattern_type", "glob", "-i", str(dest / "t*.jpg"), "-vf",
         f"scale=320:-2,tile={cols}x{rows}", "-frames:v", "1", "-q:v", "3", str(out_)], "ffmpeg contact sheet")
    return out_, False


def cmd_look(a, project):
    folder = Path(project) / FOLDER / a.id
    plan = load_plan(folder)
    if plan is None:
        raise Usage(f"no transcript for {a.id}: bin/vh ref digest {Path(project).name} {a.id} first (read it, then pick spans)")
    src, failed, done = plan["source"], [], []
    want = spans(a.spans)
    for a_, b_ in want:
        if a_ >= plan["duration"]:
            raise Usage(f"{stamp(a_)} is past the video's end ({stamp(plan['duration'])})")
    if src["kind"] == "file":
        video = Path(src["file"])
    else:
        vids = finished(folder / "media", "video")
        video = vids[0] if vids else None
    for a_, b_ in want:
        b_ = min(b_, plan["duration"])
        span = b_ - a_
        every = min(a.every or max(0.5, round(span / 24, 1)), span)
        n = max(1, int(span / every + 1e-9))
        if n > 60:
            every, n = round(span / 60, 2), 60
        name = f"{int(a_):05d}-{int(-(-b_ // 1)):05d}"
        dest = folder / "look" / name
        dest.mkdir(parents=True, exist_ok=True)
        for old in dest.glob("t*.jpg"):
            old.unlink()
        try:
            src_video, base = video, 0.0
            if src_video is None:
                src_video, base = section(src, folder, a_, b_, dest), a_
            last = max(a_, min(b_, plan["duration"]) - 0.05)   # a seek past the last frame gives none
            times = sorted({round(min(a_ + (k + 0.5) * every, last), 2) for k in range(n)})
            names, caps = [], {}
            for t in times:
                nm = f"t{t:08.2f}.jpg"
                run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, t - base):.3f}", "-i", str(src_video), "-frames:v", "1",
                     "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", str(dest / nm)], f"ffmpeg frame at {stamp(t, frac=True)}")
                if not (dest / nm).is_file():
                    raise Fail(f"no frame at {stamp(t, frac=True)}")
                names.append(nm)
                caps[nm] = stamp(t, plan["duration"] >= 3600, frac=True)
            (dest / "captions.json").write_text(json.dumps(caps, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            sh, labelled = sheet(dest, a.cols, names)
        except Fail as e:
            failed.append(name)
            say(f"✗ {stamp(a_)}–{stamp(b_)}: {e}")
            if src["kind"] == "url" and video is None:
                say(f"  {LOGIN}")
            continue
        lk = {"a": a_, "b": b_, "every": every, "dir": f"look/{name}", "sheet": f"look/{name}/sheet.jpg", "frames": names,
              "labelled": labelled, "from": "file" if src["kind"] == "file" else ("media" if video is not None else "section"), "at": ledger.iso()}
        plan["looks"] = [x for x in plan.get("looks", []) if x.get("dir") != lk["dir"]] + [lk]
        done.append(lk)
        say(f"✓ {stamp(a_)}–{stamp(b_)} · {len(names)} frames every {every:g} s · {ledger.rel(project, sh)}"
            + ("" if labelled else " (no time labels: no uv for pillow; the frame names are the seconds)"))
    plan["looks"].sort(key=lambda x: x["a"])
    write_json(folder / "plan.json", plan)
    chunks = {}
    for i in range(len(plan["chunks"])):
        f, ferr = folder / "chunks" / f"{i + 1:03d}.json", folder / "chunks" / f"{i + 1:03d}.err"
        chunks[i] = json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {"error": ferr.read_text(encoding="utf-8").strip() if ferr.is_file() else ""}
    path, _ = write_transcript(folder, plan, chunks, plan.get("labels") or "zh")
    if done:
        say(f"  {ledger.rel(project, path)}: a {LABELS[plan.get('labels') or 'zh']['frames']} line at each span; read the sheet (and a frame "
            "at full size), then write what you see under it: 画面 / 屏幕字 / 动作 / 注")
    if a.json:
        print(json.dumps({"version": 1, "project": str(project), "transcript": str(path), "looks": done, "failed": failed}, ensure_ascii=False, indent=1))
    return 1 if failed else 0


def add_parsers(sp, prog):
    p = sp.add_parser("digest", prog=f"{prog} digest", help="a long video as a timed transcript")
    p.add_argument("project")
    p.add_argument("target", metavar="id|url|file")
    p.add_argument("--subs", metavar="FILE", help="subtitles to read (SRT, WebVTT, Bilibili's JSON)")
    p.add_argument("--from", dest="from_", choices=("auto", "subs", "asr"), default="auto")
    p.add_argument("--lang", help="the language to read (zh, en …): the subtitles' and Whisper's")
    p.add_argument("--chunk", type=int, default=600, help="seconds a chunk, at most (default 600)")
    p.add_argument("--redo", metavar="N,N…|all")
    p.add_argument("--video", action="store_true", help="a URL: download the video too (for ref look)")
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--fetch-model", action="store_true", help="let the Whisper model download (about 1.6 GB, once)")
    p.add_argument("--labels", choices=("zh", "en"))
    p.add_argument("--title")
    p.add_argument("--why")
    p.add_argument("--json", action="store_true")
    p = sp.add_parser("look", prog=f"{prog} look", help="frames of the spans picked from a transcript")
    p.add_argument("project")
    p.add_argument("id")
    p.add_argument("spans", metavar="a-b[,a-b…]")
    p.add_argument("--every", type=float, help="seconds between frames (default the span ÷ 24, at least 0.5)")
    p.add_argument("--cols", type=int, default=6)
    p.add_argument("--json", action="store_true")


def main(a, project):
    global out
    if a.json:
        out = sys.stderr
    if a.cmd == "look" and a.every is not None and a.every <= 0:
        raise Usage("--every is more than 0")
    return cmd_digest(a, project) if a.cmd == "digest" else cmd_look(a, project)
