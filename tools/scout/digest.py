"""bin/vh ref digest and ref look: a long video (an interview, a lecture, a documentary, a long reference film) read as
a timed transcript, then looked at where the transcript says to look. The tool takes the speech, the agent writes what
is on the screen. Stdlib, ffmpeg; yt-dlp for a URL; a local Whisper only when there are no subtitles.

usage: bin/vh ref digest <project> <id|url|file> [--subs FILE] [--from auto|subs|asr] [--lang zh] [--chunk 600]
                         [--redo N,N…|all] [--video] [--height 720] [--fetch-model] [--labels zh|en] [--json]
       bin/vh ref look <project> <id> <a-b>[,<a-b>…] [--every S] [--cols 6] [--json]

  digest  a reference's speech as research/digest/<id>/transcript.md, one Markdown file for a person and an agent: a
          section for each chunk of the video (at most --chunk seconds, default 600), and in it the speech as said
          lines, each with its time as a link back to that second (YouTube ?t=, Bilibili ?t=, a file #t=). A URL or a
          file not on record yet is recorded first, as bin/vh ref add records it. A Bilibili part past the first (?p=2)
          is a transcript of its own, <id>-p2, under the one reference; its links keep the part. Where the speech comes
          from, first found: --subs FILE (SRT, WebVTT, Bilibili's subtitle JSON); a file's subtitles beside it
          (<name>.<lang>.srt first with --lang, then <name>.srt, .vtt) or inside it (a text subtitle stream, the one
          tagged with --lang's language when there is one); a URL's own subtitles through yt-dlp (the uploader's
          first, then Bilibili's AI subtitles or the platform's automatic captions, but only in the language spoken: an
          automatic translation is not what was said, and a translated track the uploader made is marked as one; a
          track matches --lang exactly, else by its main language, en for en-US); then a local Whisper on the audio
          (mlx-whisper, Apple Silicon, the model bin/vh tts --align local uses: WHISPER_MODEL, default
          mlx-community/whisper-large-v3-turbo). --from subs never transcribes; --from asr transcribes even when there
          are subtitles (and so does not go with --subs). The model is never downloaded unasked: when it is not in the Hugging Face cache the run stops and
          says so, and --fetch-model lets it fetch (about 1.6 GB, once). Where ffmpeg cannot find the pauses, that run's
          chunks end on their marks and nothing of it is cached. A URL that is transcribed has its audio alone
          downloaded (research/digest/<id>/media/); --video also downloads the video (at most --height, default 720),
          so ref look reads it instead of fetching each span.
          Each chunk is cached in chunks/NNN.json under what made it (the subtitles' sha256, or the model, the language
          and the speech: a file's sha256, a URL's platform and id, so a run with or without --video, which changes the
          file that carries the sound, transcribes nothing again): a run again redoes only the chunks that are missing, failed (chunks/NNN.err) or made from
          something else, so a run cut short goes on where it stopped and a chunk that failed is the only one redone.
          --redo N,N…|all redoes those. A Whisper chunk ends in the longest pause within 30 s of its mark, not
          mid-word. Whisper's habit of repeating a line over silence or music is counted and said, not removed.
          transcript.md is written again on every run from the chunks and keeps everything you wrote in it. The tool
          knows its own lines exactly: plan.json keeps the head lines and an id of each 口播 and 看帧 line (said and
          frames under --labels en) it wrote the last two times; those, and its section headings ("## 1 · 00:00–10:00"),
          are written anew. Every other line is yours: a line "- [mm:ss](link) **tag** text" is sorted into its place by
          time with the lines under it, even one tagged 口播 you edited or added (it stays beside the tool's own, and the
          run says so); any other line, a heading of your own too, goes with the line before it; lines you add to the
          head stay at its end. Tags to use: 画面 (what is in the picture), 屏幕字 (text on the screen, as written), 动作 (what moves,
          what someone does), 注 (a note); picture, on screen, action, note under --labels en.
          Also: said.json (every cue as read: start, end, text), plan.json (the source, the chunks, the looks).
  look    frames of the spans you picked from the transcript (12:30-13:10, 750-790, 1:02:03-1:02:20; several with
          commas): every --every seconds (default the span ÷ 24, at least 0.5 s; at most 60 frames a span; --every
          0.04 is a frame-by-frame strip of a short span), each at its source time, into research/digest/<id>/look/
          <a>-<b>/ (t00751.50.jpg: the second it shows) with a contact sheet labelled by source time (sheet.jpg; pillow
          through uv, else an unlabelled ffmpeg tile). The frames come from the file, from media/video.* when --video
          fetched it, else from that span alone downloaded through yt-dlp (--download-sections, cut at the exact
          second). A frame is taken no later than the video stream's last one (a longer sound, a slide video at 2 fps);
          one that still gives no picture is left out and said. The transcript gets a 看帧 line at the span's start
          linking the sheet; what you see goes under it in your own lines. Needs ref digest first: read the whole transcript, then pick what to look at.
bin/vh clean leaves research/ alone: media/ and a span's clip.* in look/ can be deleted by hand once read (a run again
fetches them); the transcript, the chunks and the frames are what the work is. A reference is studied, not shown:
reading it does not clear its picture or its sound for the film. A quote goes into NOTES.md's 素材清单 word for word
with its time and source, as the sound has it (subtitles can be the script); a frame or a clip on screen is material: clear it
and register it with bin/vh assets add. Platforms that need a login (Bilibili's AI subtitles, Douyin, WeChat Channels)
are not read through the browser's cookies: download the video or its subtitles yourself and give the file or --subs.
yt-dlp runs with the user's own config (a proxy in it keeps working) but always with --no-cookies and
--no-cookies-from-browser, which win over a config's cookies. OVH_YTDLP: a command line instead of the yt-dlp on PATH
("uvx yt-dlp"). OVH_DIGEST_ASR: a command line that transcribes
one chunk instead of mlx-whisper (another local ASR; the tests): it gets the WAV and the language and prints
{"segments": [{"start", "end", "text"}]}. Exit: 0 · 1 a chunk failed, no speech to read, a download or a frame failed
(what is done is kept) · 2 usage.
"""
import hashlib, html, json, os, platform, re, shlex, shutil, subprocess, sys, time, unicodedata, urllib.parse
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
    """Seconds as mm:ss (h:mm:ss when the video is an hour or longer), the second it is in; frac: rounded to the tenth
    (750.95 is 12:31, not 12:30.0)."""
    t = max(0.0, t)
    if frac:
        t = round(t * 10) / 10
    whole = int(t)
    h, m, s = whole // 3600, whole // 60 % 60, whole % 60
    tenth = int(round((t - whole) * 10)) if frac else 0
    return (f"{h}:{m:02d}:{s:02d}" if long or h else f"{m:02d}:{s:02d}") + (f".{tenth}" if tenth else "")


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

TIMING = re.compile(r"^\s*((?:\d+:)?\d{1,2}:\d{2}(?:[.,]\d+)?)\s*-->\s*((?:\d+:)?\d{1,2}:\d{2}(?:[.,]\d+)?)(?:\s.*)?$")


def clean(raw):
    """A subtitle line without its tags, styling and entities; the words as they are."""
    line = re.sub(r"<[^>]*>", "", raw)
    line = re.sub(r"\{\\[^}]*\}", "", line)
    return html.unescape(line).replace("\u200b", "").strip()


def parse_subs(text):
    """SRT, WebVTT or Bilibili's subtitle JSON → [{start, end, text}]. A cue's time line is a time, -->, a time (a "-->"
    among the words is words); a cue ends at an empty line (a line of spaces, as YouTube writes them, is inside it).
    Rolling captions, where a cue's first line repeats the last line of the cue before it (YouTube's automatic captions,
    two-line scrolling subtitles in SRT or any format), keep each line once: that first line is dropped when the cue
    has a line after it, lasts under 0.1 s, or is in YouTube's own format. A single line said again in the next cue
    stays twice. Tags, styling and entities are taken out; the words are not touched."""
    text = text.lstrip("\ufeff")
    if text.lstrip().startswith("{"):
        try:
            d = json.loads(text)
        except ValueError:
            raise Usage("a subtitle file that starts with { is not JSON")
        return [{"start": float(c["from"]), "end": float(c["to"]), "text": str(c["content"]).strip()}
                for c in d.get("body", []) if str(c.get("content", "")).strip()]
    youtube = "<c>" in text or bool(re.search(r"-->.*align:start position:0%", text))
    blocks, cur = [], None
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        m = TIMING.match(raw)
        if m:
            try:
                cur = (secs(m.group(1)), secs(m.group(2)), [])
                blocks.append(cur)
            except Usage:
                cur = None
            continue
        if raw == "":
            cur = None
        elif cur is not None:   # not a header, a cue's number or name, a NOTE
            cur[2].append(raw)
    cues, prev = [], []
    for start, end, raws in blocks:
        lines = [x for x in map(clean, raws) if x]
        said = lines
        if lines and prev and lines[0] == prev[-1] and (len(lines) > 1 or youtube or end - start < 0.1):
            said = lines[1:]
        cues += [{"start": round(start, 3), "end": round(end, 3), "text": x} for x in said]
        prev = lines or prev
    return cues


def joiner(a, b):
    """What goes between two cues joined into one said line: nothing between Chinese (or Japanese, Korean) text where
    a punctuation mark already parts them (……开始。为什么……), a space where none does (unpunctuated automatic or AI
    subtitles: 第1个问题 今天我们来聊一聊), so each cue's edge stays readable; a space between any other words. No
    word or mark is added or changed."""
    if not (a and b):
        return ""
    if CJK.search(a[-1]) and CJK.search(b[0]):
        punct = unicodedata.category(a[-1]).startswith("P") or unicodedata.category(b[0]).startswith("P")
        return "" if punct else " "
    return " "


def paragraphs(cues):
    """Cues joined into said lines: a new line after a pause of 2 s or more, at a sentence's end once a line holds 12 s,
    and at 30 s whatever comes. The words are as the cues have them; what goes between two is joiner's."""
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


NO_COOKIES = ["--no-cookies", "--no-cookies-from-browser"]


def ytdlp():
    """yt-dlp as the user has it (OVH_YTDLP, else PATH), with their config (a proxy keeps working) but never a cookie:
    the two flags win over a config's --cookies-from-browser or --cookies."""
    return shlex.split(os.environ.get("OVH_YTDLP") or "yt-dlp") + NO_COOKIES


LOGIN = ("Platforms that need a login (Bilibili's AI subtitles, Douyin, WeChat Channels) are not read through the "
         "browser's cookies: download the video or its subtitles yourself and give the file, or --subs FILE")


def probe(path):
    """(duration, has video, has audio, [(text subtitle stream index, its language tag)]) of a media file."""
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=index,codec_type,codec_name:stream_tags=language", "-of", "json", str(path)],
            f"ffprobe {path}")
    d = json.loads(r.stdout or "{}")
    st = d.get("streams") or []
    try:
        dur = float((d.get("format") or {}).get("duration"))
    except (TypeError, ValueError):
        raise Fail(f"{path}: not a video or audio file ffprobe can read")
    text_subs = [(s["index"], ((s.get("tags") or {}).get("language") or "").lower()) for s in st if s.get("codec_type") == "subtitle"
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


def page_of(url):
    """A Bilibili video's part (?p=N), 1 when it names none."""
    try:
        return max(1, int((urllib.parse.parse_qs(urllib.parse.urlsplit(url).query).get("p") or ["1"])[0]))
    except ValueError:
        return 1


def source_of(project, rec, page=1):
    """{kind: file|url, file, url, platform, id, page, title} for a record; a Bilibili part past the first has its URL."""
    src = rec.get("source") or {}
    if src.get("url"):
        url = src["url"]
        if src.get("provider") == "bilibili" and src.get("provider_id") and page > 1:
            url = f"https://www.bilibili.com/video/{src['provider_id']}?p={page}"
        return {"kind": "url", "url": url, "platform": src.get("provider"), "id": src.get("provider_id"), "page": page,
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
            p = src.get("page") or 1
            return f"https://www.bilibili.com/video/{src['id']}?{f'p={p}&' if p > 1 else ''}t={s}"
        return u
    rel = os.path.relpath(src["file"], folder)
    return urllib.parse.quote(Path(rel).as_posix()) + f"#t={s}"


# ---- where the speech comes from ----

def info_of(src, folder):
    """yt-dlp's -J for a URL, the parts digest reads, cached in info.json."""
    f = folder / "info.json"
    if read_json(f) is not None:
        return read_json(f)
    r = run(ytdlp() + ["-J", "--no-playlist", "--no-warnings", "--", src["url"]], f"yt-dlp on {src['url']}", timeout=300)
    try:
        d = json.loads(r.stdout)
    except ValueError:
        raise Fail(f"yt-dlp on {src['url']} printed no JSON")
    keep = {"title": d.get("title"), "duration": d.get("duration"), "language": d.get("language"), "uploader": d.get("uploader"),
            "subtitles": {k: [x.get("ext") for x in v] for k, v in (d.get("subtitles") or {}).items()},
            "automatic_captions": sorted((d.get("automatic_captions") or {}).keys())}
    write_json(f, keep)
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
                   "-o", str(d / "track.%(ext)s"), "--", src["url"]], f"yt-dlp subtitles {key} of {src['url']}", timeout=300)
    got = [p for p in d.glob(f"track.{glob_escape(key)}.*") if p.suffix.lower() in (".vtt", ".srt", ".json")] or \
          [p for p in d.glob("track.*") if p.suffix.lower() in (".vtt", ".srt", ".json")]
    if not got:
        raise Fail(f"yt-dlp wrote no {key} subtitles for {src['url']}")
    return got[0]


def sidecar_subs(f, lang):
    """Subtitles beside a file: with --lang, <name>.<lang>.srt (or .vtt; zh-Hans counts for zh) first; then <name>.srt,
    <name>.vtt, then any <name>.<tag>.srt."""
    f = Path(f)
    tagged = sorted(p for e in ("srt", "vtt") for p in f.parent.glob(f"{glob_escape(f.stem)}.*.{e}") if p.is_file())
    tag = lambda p: p.name[len(f.stem) + 1:].rsplit(".", 1)[0]
    if lang:
        hit = [p for p in tagged if tag(p).lower() == lang.lower()] + [p for p in tagged if base(tag(p)) == base(lang)]
        if hit:
            return hit[0]
    return next((p for p in [f.with_suffix(".srt"), f.with_suffix(".vtt")] + tagged if p.is_file()), None)


LANG3 = {"zh": ("zh", "chi", "zho"), "en": ("en", "eng"), "ja": ("ja", "jpn"), "ko": ("ko", "kor"), "fr": ("fr", "fre", "fra"),
         "de": ("de", "ger", "deu"), "es": ("es", "spa"), "ru": ("ru", "rus"), "pt": ("pt", "por"), "it": ("it", "ita")}


def pick_stream(text_subs, lang):
    """(index, note) of the subtitle stream inside a file to read: with --lang, the one its language tag names (eng for
    en); else the first."""
    if lang:
        names = LANG3.get(base(lang), (base(lang),))
        hit = next((i for i, tag in text_subs if base(tag) in names or tag in names), None)
        if hit is not None:
            return hit, None
        return text_subs[0][0], {"en": f"no subtitle track inside the file is tagged {lang}: the first one read ({text_subs[0][1] or 'untagged'})",
                                 "zh": f"文件里没有标着 {lang} 的字幕轨：读的是第一条（{text_subs[0][1] or '没标语言'}）"}
    return text_subs[0][0], None


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
    argv = ytdlp() + ["-f", fmt, "--no-playlist", "--no-warnings", "--continue", "-o", str(d / f"{stem}.%(ext)s")]
    argv += (["--merge-output-format", "mp4"] if video else []) + ["--", src["url"]]
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
    """(the pauses of a media file's sound [(start, end)], None) cached in silences.json under key, or ([], why) when
    ffmpeg could not tell them: nothing is cached then, the chunks end on their marks this time, and a run again tries
    once more."""
    f = folder / "silences.json"
    d = read_json(f)
    if d and d.get("key") == key:
        return [tuple(x) for x in d["silences"]], None
    try:
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostats", "-i", str(media), "-vn", "-af", "silencedetect=noise=-35dB:d=0.3",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=3600, errors="replace")
    except FileNotFoundError:
        return [], "no ffmpeg on PATH"
    except subprocess.TimeoutExpired:
        return [], "ffmpeg took over an hour to find the pauses"
    if r.returncode != 0:
        last = next((x for x in reversed(r.stderr.strip().splitlines()) if x.strip()), f"exit {r.returncode}")
        return [], f"ffmpeg could not read the sound: {last.strip()[:200]}"
    res, start = [], None
    for line in r.stderr.splitlines():
        m = re.search(r"silence_start: (-?[\d.]+)", line)
        if m:
            start = max(0.0, float(m.group(1)))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and start is not None:
            res.append((start, float(m.group(1))))
            start = None
    write_json(f, {"key": key, "silences": res})
    return res, None


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
TOOL_SECTION = re.compile(r"## \d+ · ((?:\d+:)?\d+:\d{2})–(?:\d+:)?\d+:\d{2}")


def line_id(line):
    return hashlib.sha1(line.encode("utf-8")).hexdigest()[:12]


def kept_entries(path, prev):
    """What you wrote in transcript.md: ([(time, [lines])], [head lines], tool-tagged lines the tool did not write).
    prev: the tool's own lines the last two times it wrote the file ({"head": [lines], "written": [ids]}, plan.json),
    or None for a transcript with no such record (then the head's tool lines go by their prefix). The body starts at
    the first section heading the tool writes ("## 1 · 00:00–10:00"). There, a line "- [mm:ss](link) **tag** …" starts
    an entry at its time when the tool did not write it, whatever its tag (one you edited or added with 口播 is kept
    too, and counted); any other line that is not the tool's goes with the entry before it, or after the tool line
    before it at that line's time. A blank line is spacing. Above the body, every line the tool did not write is kept."""
    if not path.is_file():
        return [], [], 0
    head_tool = set(prev["head"]) if prev and prev.get("head") is not None else None
    written = set(prev["written"]) if prev and prev.get("written") is not None else None
    res, head, cur, anchor, body, hand = [], [], None, 0.0, False, 0
    for line in path.read_text(encoding="utf-8").splitlines():
        sec = TOOL_SECTION.fullmatch(line)
        if sec:
            body, cur, anchor = True, None, secs(sec.group(1))
            continue
        if not body:
            if line.strip() and (line not in head_tool if head_tool is not None else not line.startswith(HEAD_TOOL)):
                head.append(line)
            continue
        if not line.strip():
            continue
        m = ENTRY.match(line)
        if m and m.group(2).strip() in TOOL_TAGS and (written is None or line_id(line) in written):
            anchor, cur = secs(m.group(1)), None
            continue
        if m:
            hand += m.group(2).strip() in TOOL_TAGS
            cur = (secs(m.group(1)), [line])
            res.append(cur)
            continue
        if cur is None:
            cur = (anchor, [])
            res.append(cur)
        cur[1].append(line)
    return res, head, hand


def write_transcript(folder, plan, chunks, labels, prev):
    """transcript.md from the chunks, the looks and what you wrote (kept_entries, prev from the plan before this run).
    → (path, entries of yours kept, tool-tagged lines kept as yours, {"head", "written", "written_before"}: what to keep
    in plan.json so the next run tells the tool's lines from yours)."""
    L = LABELS[labels]
    src, long = plan["source"], plan["duration"] >= 3600
    path = folder / "transcript.md"
    yours, head_yours, hand = kept_entries(path, prev)
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
    tool_head = [x for x in head if x.strip()]
    if head_yours:
        head += [""] + head_yours
    body = []
    for i, (a, b) in enumerate(plan["chunks"]):
        body += ["", f"## {i + 1} · {stamp(a, long)}–{stamp(b, long)}", ""]
        last = i == len(plan["chunks"]) - 1
        for t, _, lines in rows:
            if a <= t < b or (last and t >= b) or (i == 0 and t < a):
                body += lines
    write_text(path, "\n".join(head + body) + "\n")
    written = [line_id(x) for _, order, lines in rows if order < 2 for x in lines]
    return path, len(yours) + bool(head_yours), hand, {"head": tool_head, "head_before": (prev or {}).get("last_head") or [],
                                                       "written": written, "written_before": (prev or {}).get("last_written") or []}


def prev_of(plan):
    """What the last two runs wrote as the tool (kept_entries' prev), or None for a plan with no record of it."""
    if not plan or plan.get("written") is None:
        return None
    return {"head": list(plan.get("head") or []) + list(plan.get("head_before") or []),
            "written": list(plan.get("written") or []) + list(plan.get("written_before") or []),
            "last_head": plan.get("head") or [], "last_written": plan.get("written") or []}


# ---- digest ----

def write_text(f, text):
    """A file written whole or not at all (a run cut short leaves the old one)."""
    tmp = f.with_name(f".{f.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, f)


def write_json(f, d):
    write_text(f, json.dumps(d, ensure_ascii=False, indent=1) + "\n")


def read_json(f):
    """A JSON file of ours, or None when it is not there or not whole (written by a version before writes were atomic)."""
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_plan(folder):
    return read_json(folder / "plan.json")


def cmd_digest(a, project):
    if a.chunk < 60:
        raise Usage("--chunk is at least 60 seconds")
    if a.subs and a.from_ == "asr":
        raise Usage("--subs and --from asr ask for opposite things: --from asr transcribes even when there are subtitles; give one")
    target = a.target.strip()
    page, earlier = 1, load_plan(Path(project) / FOLDER / target) if re.fullmatch(r"[\w.-]+", target) else None
    if earlier and earlier.get("ref"):   # a transcript's own id (bili-BV…-p2): its reference and part
        target, page = earlier["ref"], (earlier.get("source") or {}).get("page") or 1
    elif target.startswith(("http://", "https://")) and re.search(r"bilibili\.com/video/", target):
        page = page_of(target)
    rec = ensure_ref(project, target, a)
    if rec.get("kind") not in ("video", None) and (rec.get("ref") or {}).get("type") != "video":
        raise Usage(f"{rec['id']} is a {(rec.get('ref') or {}).get('type') or rec.get('kind')}, not a video")
    src = source_of(project, rec, page)
    if src["kind"] == "url" and "…" in src["url"]:
        raise Fail(f"{rec['id']}: the URL on record is shortened ({src['url']}: ref add keeps a page's query out of the record); "
                   "download the video and give the file")
    did = rec["id"] + (f"-p{page}" if page > 1 else "")   # one transcript a part; one reference a video
    folder = Path(project) / FOLDER / did
    (folder / "chunks").mkdir(parents=True, exist_ok=True)
    old = load_plan(folder) or {}
    labels = a.labels or old.get("labels") or "zh"
    warnings = []
    say(f"{did} · {src.get('title') or src.get('url') or src.get('file')}" + (f" · part {page}" if page > 1 else ""))

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
                idx, note = pick_stream(text_subs, a.lang)
                subs = embedded_subs(src["file"], folder, idx)
                tag = dict(text_subs)[idx]
                speech_note = (f"the file's own subtitle track ({tag or 'untagged'})" if labels == "en" else f"文件自带的字幕轨（{tag or '没标语言'}）")
                if note:
                    warnings.append(note[labels])
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
            # the sound is the source's, whichever file carries it: the audio when there is one (a run with --video
            # keeps transcribing it), else the video; the cache key names the source, not the container
            have = finished(folder / "media", "audio") or finished(folder / "media", "video")
            try:
                media = have[0] if have else fetch_media(src, folder, a.video, a.height)
            except Fail as e:
                raise Fail(f"{e}. {LOGIN}")
            duration = probe(media)[0]
            speech = "url:" + (f"{src['platform']}:{src['id']}" if src.get("id") else src["url"]) + (f":p{page}" if page > 1 else "")
        elif not has_a:
            raise Fail(f"{src['file']} has no sound to transcribe")
        else:
            speech = sha(media)
        model = "cmd:" + os.environ["OVH_DIGEST_ASR"] if os.environ.get("OVH_DIGEST_ASR") else os.environ.get("WHISPER_MODEL", DEFAULT_MODEL)
        key = f"asr:{model}:{a.lang or 'auto'}:{speech}"
        pauses, why = silences(media, folder, speech)
        if why:
            warnings.append((f"the pauses were not found ({why}): this run's chunks end on their marks, maybe mid-word" if labels == "en"
                             else f"没找到停顿（{why}）：这一次的段界落在整点上，可能切在词中间"))
        plan_chunks = bounds(duration, a.chunk, pauses)
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
            c = read_json(f) or {}
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
            write_text(ferr, str(x) + "\n")
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

    plan = {"v": 1, "ref": rec["id"], "id": did, "source": src, "duration": round(duration, 3), "chunk": a.chunk, "chunks": plan_chunks,
            "from": key, "speech_note": speech_note, "lang": a.lang, "labels": labels, "warnings": warnings,
            "media": ledger.rel(project, media) if media is not None and src["kind"] == "url" else None, "height": a.height,
            "looks": [lk for lk in old.get("looks", []) if lk["b"] <= duration + 1], "at": ledger.iso()}
    allc = [x for i in sorted(chunks) for x in chunks[i].get("lines", [])]
    write_json(folder / "said.json", {"v": 1, "ref": rec["id"], "from": key, "cues": allc})
    path, kept, hand, wrote = write_transcript(folder, plan, chunks, labels, prev_of(old))
    plan.update(wrote)
    write_json(folder / "plan.json", plan)
    n_said = sum(len(paragraphs(c.get("lines", []))) for c in chunks.values())
    say(f"✓ {ledger.rel(project, path)} · {len(plan_chunks)} chunk{'s' if len(plan_chunks) != 1 else ''} "
        f"({made} made, {len(plan_chunks) - made - len(failed)} from the cache{f', {len(failed)} failed' if failed else ''}) · "
        f"{n_said} said lines · {kept} of yours kept · {stamp(duration)}")
    say(f"  speech: {speech_note}")
    for w in warnings:
        say(f"  ! {w}")
    if hand:
        say(f"  ! {hand} line{'s' if hand != 1 else ''} tagged {LABELS[labels]['said']} or {LABELS[labels]['frames']} the tool did not write "
            "(edited or added by hand): kept as written, beside the tool's own; a note reads clearer tagged 注")
    if failed:
        say(f"  chunks {', '.join(map(str, failed))} failed (chunks/NNN.err): run the same command again, only those are redone")
    else:
        say(f"  next: read it all, then bin/vh ref look {Path(project).name} {did} <a-b>[,<a-b>…] where the picture matters")
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
                   "--force-keyframes-at-cuts", "-o", str(dest / "clip.%(ext)s"), "--", src["url"]],
        f"yt-dlp {stamp(a_)}–{stamp(b_)} of {src['url']}", timeout=1800)
    got = finished(dest, "clip")
    if not got:
        raise Fail(f"yt-dlp wrote no clip for {stamp(a_)}–{stamp(b_)}")
    write_text(mark, span + "\n")
    return got[0]


def last_frame(video):
    """When the video stream's last frame starts, in the file's own seconds (its latest packet time), or None. The
    container can run longer (a longer sound), and at a low frame rate (slides, a screen recording) the last frame
    starts well before the end: a seek past it gives no picture."""
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration:format=duration",
                            "-of", "json", str(video)], capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout or "{}")
        st = (d.get("streams") or [{}])[0]
        dur = float(st.get("duration") or (d.get("format") or {}).get("duration") or 0)
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-read_intervals", f"{max(0.0, dur - 30):.3f}%",
                            "-show_entries", "packet=pts_time", "-of", "csv=p=0", str(video)], capture_output=True, text=True, timeout=120)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return None
    times = [float(x) for x in re.findall(r"^\s*(-?[\d.]+)", r.stdout, re.M)]
    return max(times) if times else None


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
            lf = last_frame(src_video)
            last = max(a_, min(b_, plan["duration"]) - 0.05)   # a seek past the last frame gives none
            if lf is not None:
                lf = int((lf + base) * 100) / 100   # in source seconds, down to the hundredth: a seek to it lands on it
                if a_ > lf + 2:
                    raise Fail(f"no picture in this span: the video's last frame is at {stamp(lf, frac=True)}")
                last = min(last, lf)
            if last < a_:   # the span is after the last frame, which is what the screen holds then: that frame, at its time
                times = [last]
            else:
                times = sorted({round(min(a_ + (k + 0.5) * every, last), 2) for k in range(n)})
            names, caps, missed = [], {}, []
            for t in times:
                nm = f"t{t:08.2f}.jpg"
                try:
                    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{max(0.0, t - base):.3f}", "-i", str(src_video), "-frames:v", "1",
                         "-vf", "scale='min(1280,iw)':-2", "-q:v", "3", str(dest / nm)], f"ffmpeg frame at {stamp(t, frac=True)}")
                except Fail:
                    pass
                if not (dest / nm).is_file():
                    missed.append(stamp(t, frac=True))
                    continue
                names.append(nm)
                caps[nm] = stamp(t, plan["duration"] >= 3600, frac=True)
            if not names:
                raise Fail(f"no frame in this span (tried {', '.join(missed[:4])}{' …' if len(missed) > 4 else ''})")
            if missed:
                say(f"  ! no frame at {', '.join(missed)}: left out")
            write_json(dest / "captions.json", caps)
            sh, labelled = sheet(dest, a.cols, names)
        except Fail as e:
            failed.append(name)
            if not any(dest.iterdir()):
                dest.rmdir()
            say(f"✗ {stamp(a_)}–{stamp(b_)}: {e}")
            if src["kind"] == "url" and video is None:
                say(f"  {LOGIN}")
            continue
        lk = {"a": a_, "b": b_, "every": every, "dir": f"look/{name}", "sheet": f"look/{name}/sheet.jpg", "frames": names,
              "labelled": labelled, "from": "file" if src["kind"] == "file" else ("media" if video is not None else "section"), "at": ledger.iso()}
        plan["looks"] = [x for x in plan.get("looks", []) if x.get("dir") != lk["dir"]] + [lk]
        done.append(lk)
        say(f"✓ {stamp(a_)}–{stamp(b_)} · {len(names)} frame{'s' if len(names) != 1 else ''} every {every:g} s · {ledger.rel(project, sh)}"
            + ("" if labelled else " (no time labels: no uv for pillow; the frame names are the seconds)"))
    plan["looks"].sort(key=lambda x: x["a"])
    chunks = {}
    for i in range(len(plan["chunks"])):
        f, ferr = folder / "chunks" / f"{i + 1:03d}.json", folder / "chunks" / f"{i + 1:03d}.err"
        chunks[i] = read_json(f) or {"error": ferr.read_text(encoding="utf-8").strip() if ferr.is_file() else ""}
    path, _, _, wrote = write_transcript(folder, plan, chunks, plan.get("labels") or "zh", prev_of(plan))
    plan.update(wrote)
    write_json(folder / "plan.json", plan)
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
