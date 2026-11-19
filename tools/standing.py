"""Where a film stands, said to the person: one short sentence of what is happening, a line more when there is more to
say, and at most one thing the person may do. bin/vh status prints the English as its `now:` lines (and --json has the
whole record); Studio shows the same words (zh or en) above its column, the short form on the space's card, and the one
action as a button. Every word is in WORDS below, zh and en together.

Only what the disk can prove is said. The disk knows the last thing recorded and when (a command's start and end, a
hand-over, a Studio conversation's events, a change to the film's own files), whether a process runs now, whether a
listener and the agent it waits for are alive, how a Studio turn ended, and which agent program a run was started under
(bin/vh records it; while that program lives, an agent is open on the film). It cannot know that an agent is thinking
between two commands: a quiet film says when the last thing happened, never that nobody works on it; "stopped" needs a run
that ended with no end record and whose process is gone, or a Studio turn that was stopped or broke, with nothing after it;
and the offer to carry on is an offer.

Reads what bin/vh status has read (its record) and a few small things beside it: the review's listening flag
(tools/desk/feedback.py), the time the last submission was handed over (feedback/.consumed), the console's agent lock
(<project>/.ovh/agent.lock), the tail of the newest conversation log (<project>/.ovh/agents/*.jsonl), the newest change
among the film's own files (a walk of at most a few thousand entries, not out/, media/, renders/), and ps for the agent a
run recorded. It starts, asks and writes nothing else.

  now = {code, who, you, tone, say: {zh, en}, more: {zh, en} | None, short: {zh, en}, act, facts}
  who: whose move it is, as bin/vh status's waiting_on; you: what the person has to do with it (decide: it waits for them;
  nudge: it needs a word from them; offer: they may; none); tone: you | busy | quiet (the dot's colour)
  act = {kind: open | tell | none, mod, sub, label: {zh, en}, text: {zh, en}, confirm, secondary}
  (tell: the words the person's click sends; confirm: ask once more first, something happened lately; secondary: not the
  main thing to do, said as a quiet second line)
  facts.paths: the project's files the words name (Studio opens them; the terminal prints them as they are)

plan_line(): the film in one line from its BRIEF and its stops ("30 秒竖屏，有旁白，先看方向和初版"), or None.
"""
import json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECENT = 1800       # s: a sign of life this recent makes the offer to carry on ask once more
NOT_SOURCE = {"out", "media", "renders", "node_modules", ".ovh", ".git", "__pycache__", "cache", ".cache"}
NOT_AGENTS = {"REVIEW.md"}   # written by Studio for the person's own submission too: no sign of the agent

# ---------- the words: key → (zh, en); {x} are filled in ----------
WORDS = {
    # what the person sees at a stop, and how they take it in
    "seen.1": ("立意卡", "the concept cards"), "seen.2": ("分镜", "the storyboard"), "seen.3": ("初版", "the first cut"),
    "seen.E0": ("样帧", "the style frames"), "seen.E1": ("脚本", "the script"), "seen.E2": ("声音", "the sound"),
    "seen.E3": ("锁时的版本", "the timing lock"), "seen.E4": ("样板章", "the sample chapter"), "seen.E5": ("锁画面的版本", "the picture lock"),
    "seen.deliver": ("交付", "the delivery"),
    "take.look": ("看", "look at"), "take.listen": ("听", "listen to"),
    # a command: what it does (zh, en), and as a thing (en)
    "cmd.render": ("渲染", "rendering", "the render"), "cmd.patch": ("补渲", "patching the film", "the patch"),
    "cmd.tts": ("配音", "voicing", "the voice-over"), "cmd.mix": ("混音", "mixing", "the mix"), "cmd.check": ("检查", "checking", "the check"),
    "cmd.deliver": ("出上传版", "making the upload copy", "the upload copy"), "cmd.proxy": ("做代理", "making a proxy", "the proxy"),
    "cmd.thumbs": ("做缩略图", "making thumbnails", "the thumbnails"), "cmd.gate": ("出审阅页", "making the review page", "the review page"),
    "cmd.music": ("作曲", "composing", "the music"), "cmd.storyboard": ("画分镜关键帧", "drawing the storyboard frames", "the storyboard frames"),
    "cmd.qa": ("查声音", "checking the sound", "the sound check"), "cmd.mux": ("合音轨", "putting the sound on", "putting the sound on"),
    "cmd.frames": ("取帧", "taking frames", "taking frames"), "cmd.sheet": ("出联系表", "making a contact sheet", "the contact sheet"),
    "cmd.new": ("建项目", "making the project", "making the project"), "cmd.hf-init": ("装引擎", "setting up the engine", "the engine's setup"),
    "cmd.sfx": ("找音效", "finding sound effects", "the sound effects"), "cmd.image": ("生图", "making images", "the images"),
    "cmd.captions": ("做字幕", "making the subtitles", "the subtitles"), "cmd.cues": ("对时间", "lining up the timing", "the timing"),
    "cmd.readcheck": ("查读时", "checking the reading time", "the reading-time check"), "cmd.textcheck": ("查画面文字", "checking the text on screen", "the text check"),
    "cmd.timeline": ("排时间线", "laying out the timeline", "the timeline"), "cmd.peaks": ("画波形", "drawing the waveform", "the waveform"),
    "cmd.bgm": ("配乐", "picking the music", "the music"), "cmd.voices": ("试声音", "trying voices", "the voice trial"),
    "cmd.edit": ("排剪辑表", "laying out the edit", "the edit"), "cmd.footage": ("找素材", "finding footage", "the footage"),
    "cmd.rhythm": ("画节奏图", "drawing the rhythm chart", "the rhythm chart"), "cmd.beats": ("找节拍", "finding the beats", "the beats"),
    "cmd.determinism": ("查确定性", "checking the frames repeat", "the determinism check"), "cmd.hf": ("跑引擎", "running the engine", "the engine run"),
    "cmd.versions": ("换版本", "switching versions", "the version switch"), "cmd.assets": ("登记素材", "recording assets", "the asset record"),
    "cmd.review": ("出审阅页", "making the review page", "the review page"), "cmd.concept": ("出立意板", "making the concept board", "the concept board"),
    "cmd.cover-preview": ("出封面预览", "making the cover preview", "the cover preview"), "cmd.gif": ("出动图", "making the GIF", "the GIF"),
    "cmd.other": ("跑一条命令", "running a command", "a command"),
    "unit.frames": ("帧", "frames"), "unit.lines": ("句", "lines"), "unit.pictures": ("张", "pictures"),
    "progress": ("{d} / {t} {u}", "{d} of {t} {u}"), "progress.percent": ("{d}%", "{d}%"),
    "doing": ("{x}，{p}", "{x}, {p}"),
    # what was last seen happen on the film (a sign of life), by kind
    "sign.ok": ("{x}做完了", "{t} finished"), "sign.found": ("{x}结束时报了问题", "{t} ended reporting a problem"),
    "sign.check_found": ("检查查出 {n} 处要改", "the check found {n} thing(s) to fix"),
    "sign.stopped": ("{x}被停下了", "{t} was stopped"), "sign.gone": ("{x}中断了", "{t} was cut off"),
    "sign.gone_at": ("{x}到 {p}时中断了", "{t} was cut off at {p}"),
    "sign.page": ("发出了审阅页", "the review page went out"), "sign.wait": ("它开始等你的意见", "it began waiting for your notes"),
    "sign.handed": ("它取走了你的意见", "it picked up your notes"),
    "sign.talk_end_turn": ("Studio 里的对话做完一轮", "the Studio conversation finished a turn"),
    "sign.talk_cancelled": ("Studio 里的对话被停下了", "the Studio conversation was stopped"),
    "sign.talk_error": ("Studio 里的对话出错停了", "the Studio conversation ended with an error"),
    "sign.talk_cut": ("Studio 里的对话做到一半断了", "the Studio conversation was cut off mid-turn"),
    "sign.talk": ("Studio 里的对话有新内容", "the Studio conversation moved on"),
    "sign.file": ("改了 {f}", "{f} changed"),
    "last": ("上一次动静：{a}前，{x}。", "Last sign of life: {a} ago, {x}."),
    "ago.now": ("不到 1 分钟", "under a minute"), "ago.min": ("{n} 分钟", "{n} min"), "ago.hour": ("{n} 小时", "{n} hour"),
    "ago.hours": ("{n} 小时", "{n} hours"), "ago.days": ("{n} 天", "{n} days"),
    # the sentences, a code each: its short sentence, the card's few words (.short)
    "paused": ("你让这支片子先停着。", "You paused this film."), "paused.short": ("暂停了", "paused"),
    "revision_ready": ("照你说的改好了，等你复审。", "Changed as you said, for you to review."),
    "revision_ready.more": ("改前改后两版放在一起，在这里对照着看、听。", "The versions before and after are side by side here, to watch and listen to together."),
    "revision_ready.short": ("改好了，等你复审", "changed, for you to review"),
    "waiting_you": ("{s}出来了，等你{v}。", "{S} {be} out and {wait} for you."),
    "waiting_you.listening": ("你交了，agent 就接着做。", "Once you send your notes, the agent carries on by itself."),
    "waiting_you.alone": ("交了以后，要跟 agent 说一声。", "After you send your notes, tell the agent."),
    "waiting_you.short": ("{s} · 等你{v}", "{s} · for you"),
    "notes_unheard": ("你的意见存好了，还没有 agent 来取。", "Your notes are saved; no agent has picked them up yet."),
    "notes_unheard.more": ("跟 agent 说一声，它就来取。", "Tell the agent and it will fetch them."),
    "notes_unheard.busy": ("{x}还在跑，但你 {t} 交的这一份没人取。跟 agent 说一声。", "{X} still runs, but your notes of {t} have not been picked up. Tell the agent."),
    "notes_unheard.short": ("意见还没人取", "notes not picked up yet"),
    "notes_sent": ("你的意见交出去了，等着的 agent 正在取。", "Your notes went to the agent that was waiting; it is picking them up."),
    "notes_sent.short": ("意见交出去了", "notes sent"),
    "notes_taken": ("agent 拿到了你的意见，正在改。", "The agent has your notes and is working on them."),
    "notes_taken.short": ("在照你的意见改", "working on your notes"),
    "now_doing": ("正在{x}。", "{X}."), "in_studio": ("在 Studio 的对话里。", "In the Studio conversation."),
    "running": ("正在{x}。", "{X}."), "running.short": ("正在{x}", "{x}"),
    "working": ("agent 正在做。", "The agent is working."), "working.short": ("agent 在做", "the agent is working"),
    "delivered": ("已交付{d}。", "Delivered{d}."), "delivered.short": ("已交付{d}", "delivered{d}"),
    "delivered.film": ("成片：{f}", "The film: {f}"), "delivered.gone": ("（不在这台电脑上了）", " (no longer on this computer)"),
    "delivered.subs": ("字幕：{f}", "subtitles: {f}"), "delivered.version": ("交付的是 {v}", "version {v}"),
    "no_record": ("这支片子没有审阅记录。", "This film keeps no review record."),
    "no_record.more": ("看不出它停在哪一站。", "Where it stopped cannot be told."), "no_record.short": ("没有审阅记录", "no review record"),
    "stopped": ("agent 停下了：{x}。", "The agent stopped: {x}."), "stopped.short": ("停下了", "stopped"),
    "stopped.since": ("{a}前，{x}，之后没有别的动静。", "{X} {a} ago, and nothing has happened since."),
    "agent_open": ("现在没有命令在跑；上次做这支片子的 agent 还开着。", "No command runs now; the agent that last worked on this film is still open."),
    "agent_open.short": ("agent 开着", "an agent is open"),
    "idle": ("现在没有命令在跑。", "No command runs right now."), "idle.short": ("没有命令在跑", "nothing running"),
    "ship_missing": ("还没交付：{x}。", "Not delivered yet: {x}."), "ship_missing.short": ("还没交付", "not delivered yet"),
    "gap.cut": ("初版还没定", "the first cut is not decided yet"), "gap.check": ("成片没过检查", "the film has not passed its check"),
    "gap.final": ("正式版还没做好或还没检查", "the final is not made or not checked yet"),
    "setup": ("引擎还没装好。", "The engine is not set up yet."),
    "setup.more": ("agent 接着做时会先装它（要联网）。", "The agent sets it up first when it carries on (it needs the network)."),
    "setup.short": ("引擎还没装好", "engine not set up"),
    "unknown": ("读不出这支片子现在到哪了。", "Where this film stands could not be worked out."), "unknown.short": ("读不出", "unreadable"),
    # the facts in the line under a sentence
    "read_at": ("你 {t} 交的意见它读过了。", "It has read your notes of {t}."),
    "made": ("已经做好：{f}。", "Made so far: {f}."),
    "next": ("下一步是{s}。", "Next: {s}."), "next.notes": ("下一步：照你的意见改{s}。", "Next: {s}, changed as your notes say."),
    # the buttons, and the words a tell button sends (only these words, numbers and times: nothing else from the project)
    "act.look": ("去{v}{s}", "{V} {s}"), "act.revision": ("去复审", "Review the change"), "act.ship": ("打开交付", "Open the delivery"),
    "act.go_cut": ("去看初版", "Go to the first cut"), "act.go_ship": ("去看交付", "Go to the delivery"),
    "act.carry": ("让 agent 接着做", "Ask the agent to carry on"), "act.fetch": ("叫 agent 来看意见", "Tell the agent to read them"),
    "act.carry_open": ("它要是没反应，在这里叫一个 agent 接着做", "If it does not answer, ask an agent here to carry on"),
    "say.carry": ("接着做这支片子。先跑 bin/vh status 看下一步。", "Carry on with this film. Run bin/vh status first for the next step."),
    "say.stopped": ("接着做这支片子。上次{x}。先跑 bin/vh status 看下一步。", "Carry on with this film. Last time {x}. Run bin/vh status first for the next step."),
    "say.fetch": ("我在 Studio 交了这一站的意见。去取来看（bin/vh status 会说怎么取），然后接着做。",
                  "I sent my notes for this stop in Studio. Fetch and read them (bin/vh status says how), then carry on."),
    "say.resume": ("接着做这支片子：REVIEW.md 里写着暂停，现在恢复，在那里记一节恢复。先跑 bin/vh status 看下一步。",
                   "Carry on with this film: REVIEW.md says paused; it resumes now, so note that there. Run bin/vh status first for the next step."),
    # the film's plan
    "plan.secs": ("{n} 秒", "{n} s"), "plan.span": ("{a}–{b} 秒", "{a}–{b} s"), "plan.min": ("{m} 分钟", "{m} min"), "plan.min_s": ("{m} 分 {s} 秒", "{m} min {s} s"),
    "plan.vertical": ("竖屏", "vertical"), "plan.landscape": ("横屏", "landscape"), "plan.square": ("方屏", "square"),
    "plan.narrated": ("有旁白", "narrated"), "plan.silent": ("没有旁白", "no narration"), "plan.song": ("配一首歌", "set to a song"),
    "plan.none": ("中间不停，做完给你看", "no stops on the way: you see it finished"),
    "plan.13": ("先看方向和初版", "you see the direction and the first cut"),
    "plan.123": ("立意、分镜、初版都给你看", "you see the concept, the storyboard and the first cut"),
    "plan.at": ("停在{x}", "it stops at {x}"), "plan.sep": ("，", ", "), "plan.list": ("、", ", "),
    "stop.1": ("立意", "the concept"), "stop.2": ("分镜", "the storyboard"), "stop.3": ("初版", "the first cut"), "stop.E0": ("样帧", "the style frames"),
    "stop.E1": ("脚本", "the script"), "stop.E2": ("声音", "the sound"), "stop.E3": ("锁时", "the timing lock"), "stop.E4": ("样板章", "the sample chapter"),
    "stop.E5": ("锁画面", "the picture lock"),
}
MOD = {"1": "idea", "E0": "idea", "E1": "outline", "2": "board", "E2": "sound", "E3": "sound", "3": "cut", "E4": "cut", "E5": "cut", "deliver": "ship"}   # core.js's GATE_MOD
PLURAL = {"1", "E0"}     # the concept cards, the style frames
LISTEN = {"E2"}          # the sound: listened to
ORDER = ["1", "E0", "E1", "2", "E2", "E3", "3", "E4", "E5"]


def w(key, i, **x):
    """WORDS[key] in language i (0 zh, 1 en; 2 a command as a thing), filled in."""
    v = WORDS[key]
    return v[min(i, len(v) - 1)].format(**x)


def both(key, **x):
    return {"zh": w(key, 0, **x), "en": w(key, 1, **x)}


def two(zh, en):
    return {"zh": zh, "en": en}


def cap(s):
    return s[:1].upper() + s[1:]


def cmd_words(r):
    """A command in words: [zh, en doing, en thing]; one not in the table is "a command" (its name stays off the page)."""
    k = f"cmd.{r.get('cmd')}"
    return [w(k if k in WORDS else "cmd.other", i) for i in range(3)]


def progress(r):
    """[zh, en] of a run's last progress line ("340 / 900 帧", "340 of 900 frames"), or None."""
    p = r.get("progress") or {}
    d, t, u = p.get("done"), p.get("total"), p.get("unit")
    if not (isinstance(d, (int, float)) and isinstance(t, (int, float)) and t):
        return None
    if u == "percent":
        return [w("progress.percent", i, d=int(d)) for i in (0, 1)]
    unit = [w(f"unit.{u}", i) if f"unit.{u}" in WORDS else (u or "") for i in (0, 1)]
    return [w("progress", i, d=int(d), t=int(t), u=unit[i]).strip() for i in (0, 1)]


def doing(r):
    """A run that goes on: [zh, en] ("渲染，340 / 900 帧", "rendering, 340 of 900 frames")."""
    c, p = cmd_words(r), progress(r)
    return [w("doing", i, x=c[i], p=p[i]) for i in (0, 1)] if p else c[:2]


def ago(secs):
    m = int(max(0, secs) // 60)
    if m < 1:
        return [w("ago.now", i) for i in (0, 1)]
    if m < 60:
        return [w("ago.min", i, n=m) for i in (0, 1)]
    if m < 48 * 60:
        return [w("ago.hour" if m < 120 else "ago.hours", i, n=m // 60) for i in (0, 1)]
    return [w("ago.days", i, n=m // 1440) for i in (0, 1)]


def clock(t, now):
    """21:14 today, else 11-18 21:14."""
    a, b = time.localtime(t), time.localtime(now)
    return time.strftime("%H:%M" if a[:3] == b[:3] else "%m-%d %H:%M", a)


def conversation(project):
    """The newest Studio conversation on this film: {ended: end_turn | cancelled | error | cut | None, turn_t, t} (turn_t:
    its last turn event; t: its last event of any kind), or None. cut: a turn began and never ended."""
    try:
        logs = sorted((Path(project) / ".ovh" / "agents").glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    except OSError:
        return None
    if not logs:
        return None
    try:
        with open(logs[-1], "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 65536))
            lines = f.read().decode("utf-8", "replace").splitlines()
    except OSError:
        return None
    last, t = None, None
    for ln in lines:
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if isinstance(e, dict):
            if isinstance(e.get("t"), (int, float)):
                t = e["t"]
            if e.get("type") == "turn":
                last = e
    if last is None:
        return {"ended": None, "turn_t": None, "t": t}
    if last.get("state") == "start":
        return {"ended": "cut", "turn_t": last.get("t"), "t": t}
    stop = "error" if last.get("error") else str(last.get("stop") or "end_turn")
    ended = "cancelled" if stop == "cancelled" else "error" if stop in ("error", "refusal") else "end_turn"
    return {"ended": ended, "turn_t": last.get("t"), "t": t}


def _desk():
    d = str(HERE / "desk")
    if d not in sys.path:
        sys.path.insert(0, d)


def console_turn(project):
    """A Studio conversation holds the film's lock now (its turn runs)."""
    try:
        _desk()
        import agentlock
        return agentlock.read(project) is not None
    except Exception:
        return False


def listener(project):
    """An agent waits for this film's submission now (bin/vh desk wait, gate --wait): its flag, its process alive, and the
    agent it waits for alive."""
    try:
        _desk()
        import feedback as F
        return bool(F.listening(project).get("listening"))
    except Exception:
        return False


def newest_file(project, limit=3000):
    """(mtime, path from the project) of the newest change among the film's own files (not out/, media/, renders/ …), or None."""
    best, seen = None, 0
    stack = [(Path(project), 0)]
    while stack and seen < limit:
        d, depth = stack.pop()
        try:
            it = list(os.scandir(d))
        except OSError:
            continue
        for e in it:
            seen += 1
            if e.name.startswith("."):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if depth < 3 and e.name not in NOT_SOURCE:
                        stack.append((Path(e.path), depth + 1))
                elif e.is_file(follow_symlinks=False) and not (depth == 0 and e.name in NOT_AGENTS):
                    m = e.stat(follow_symlinks=False).st_mtime
                    if best is None or m > best[0]:
                        best = (m, os.path.relpath(e.path, project))
            except OSError:
                continue
    return best


def subtitles(project, film):
    """Subtitle files beside the delivered film (its stem), or in out/final/: paths from the project."""
    if not film:
        return []
    f = Path(project) / film
    out = set()
    for d in {f.parent, Path(project) / "out" / "final"}:
        try:
            for s in d.iterdir():
                if s.suffix.lower() in (".srt", ".vtt", ".ass") and (d != f.parent or s.stem.startswith(f.stem.split(".")[0])):
                    out.add(str(s.relative_to(project)))
        except (OSError, ValueError):
            pass
    return sorted(out)[:3]


def run_sign(r, o):
    """What a finished run says of the film: (t, [zh, en], kind[, short [zh, en]]) with kind ok | found | stopped | gone | page."""
    c = cmd_words(r)
    t = r.get("end") or max(r.get("start") or 0, (r.get("progress") or {}).get("t") or 0)   # a run cut off: when it was last heard from
    if r.get("cmd") == "gate" and "--wait" in (r.get("args") or []):
        return (r.get("start") or 0, [w("sign.page", 0), w("sign.page", 1)], "page")
    if r.get("state") == "gone":   # (the sentence says the short way, the line under it the long one)
        p = progress(r)
        k = "sign.gone_at" if p else "sign.gone"
        return (t, [w(k, 0, x=c[0], p=p[0] if p else ""), w(k, 1, t=c[2], p=p[1] if p else "")], "gone", [w("sign.gone", 0, x=c[0]), w("sign.gone", 1, t=c[2])])
    if r.get("cancelled") or r.get("exit") in (130, 143):
        return (t, [w("sign.stopped", 0, x=c[0]), w("sign.stopped", 1, t=c[2])], "stopped")
    if r.get("exit") == 0:
        return (t, [w("sign.ok", 0, x=c[0]), w("sign.ok", 1, t=c[2])], "ok")
    chk = o.get("check") or {}
    n = (chk.get("counts") or {}).get("fail")
    if r.get("cmd") == "check" and isinstance(n, int) and n > 0 and not chk.get("stale"):
        return (t, [w("sign.check_found", 0, n=n), w("sign.check_found", 1, n=n)], "found")
    return (t, [w("sign.found", 0, x=c[0]), w("sign.found", 1, t=c[2])], "found")


def signs(project, o, talk, took):
    """Every sign of life on the film the disk keeps, oldest first: [(t, [zh, en], kind, path, short [zh, en] or None)]."""
    act = o.get("activity") or {}
    out = []
    for r in (act.get("recent") or []) + (act.get("listening") or []):
        waiting = r.get("cmd") == "desk" and (r.get("args") or [""])[0] == "wait"
        if r.get("cmd") == "desk" and not waiting:
            continue   # the console itself is no work on the film
        if r.get("state") == "running":   # a wait for the person: when it began
            if r.get("start"):
                k = "sign.wait" if waiting else "sign.page"
                out.append((r["start"], [w(k, 0), w(k, 1)], "wait", None, None))
            continue
        if waiting:
            continue   # a finished wait: the hand-over says it (took)
        t, words, kind, *short = run_sign(r, o)
        if t:
            out.append((t, words, kind, None, short[0] if short else words))
    if took:
        out.append((took, [w("sign.handed", 0), w("sign.handed", 1)], "handed", None, None))
    if talk and talk.get("t"):
        last_is_turn = bool(talk.get("ended")) and talk.get("turn_t") == talk.get("t")
        k = f"sign.talk_{talk['ended']}" if last_is_turn else "sign.talk"
        out.append((talk["t"], [w(k, 0), w(k, 1)], f"talk_{talk['ended']}" if last_is_turn else "talk", None, None))
    f = newest_file(project)
    if f:
        out.append((f[0], [w("sign.file", 0, f=f[1]), w("sign.file", 1, f=f[1])], "file", f[1], None))
    return sorted(out, key=lambda x: x[0])


def open_agent(o):
    """The agent program the newest recorded run was started under, while that very process lives: (when it last ran
    something, its record), else None."""
    act = o.get("activity") or {}
    runs = [r for r in (act.get("running") or []) + (act.get("listening") or []) + (act.get("recent") or []) if isinstance(r.get("agent"), dict)]
    if not runs:
        return None
    r = max(runs, key=lambda x: x.get("end") or x.get("start") or 0)
    try:
        import activity
        return (r.get("end") or r.get("start"), r["agent"]) if activity.agent_alive(r["agent"]) else None
    except Exception:
        return None


def say(code, who, you, s, more=None, short=None, act=None, paths=(), tone=None, **facts):
    """s, short: {zh, en}; more: a list of {zh, en} (None skipped), joined into the line under the sentence."""
    parts = [m for m in more or [] if m]
    line = two("".join(m["zh"] for m in parts), " ".join(m["en"] for m in parts)) if parts else None
    tone = tone or ("you" if you in ("decide", "nudge") else "quiet")
    return {"code": code, "who": who, "you": you, "tone": tone, "say": s, "more": line, "short": short or both(code + ".short"),
            "act": act or {"kind": "none"}, "facts": dict(facts, paths=[p for p in dict.fromkeys(paths) if p])}


def act_open(mod, label, sub=None):
    return {"kind": "open", "mod": mod, "sub": sub, "label": label}


def act_tell(label, text, confirm=False, secondary=False):
    return {"kind": "tell", "label": label, "text": text, "confirm": bool(confirm), "secondary": bool(secondary)}


def of(project, o, now=None):
    """The record's `now` (see the module's doc). o: bin/vh status's record of this project."""
    now = time.time() if now is None else now
    project = Path(project)
    st = o.get("stations") or []
    act = o.get("activity") or {}
    working = act.get("running") or []
    who = o.get("waiting_on") if o.get("waiting_on") in ("person", "agent", "nobody", "unknown") else "unknown"
    listening = listener(project)   # the flag, its process, and the agent it waits for, alive: "it carries on by itself" is a promise
    turn = console_turn(project)
    talk = conversation(project)
    busy = bool(working) or turn    # something works on this film now: a command, or a Studio conversation's turn
    nxt = next((s for s in st if s["state"] in ("waiting_agent", "in_progress")), None)

    def seen(s):
        return both(f"seen.{s['id']}") if f"seen.{s['id']}" in WORDS else two(s["name"], s["name"])
    fb = (nxt or {}).get("feedback") or {}
    later = None
    if nxt:
        n, k = seen(nxt), "next.notes" if nxt["state"] == "waiting_agent" and fb.get("submitted") else "next"
        later = two(w(k, 0, s=n["zh"]), w(k, 1, s=n["en"]))

    if o.get("paused"):
        return say("paused", who, "decide", both("paused"), act=act_tell(both("act.carry"), both("say.resume")))
    revs = [r for r in (o.get("review") or {}).get("revisions") or [] if r.get("state") == "pending" and r.get("available")]
    if revs:
        return say("revision_ready", who, "decide", both("revision_ready"), [both("revision_ready.more")],
                   act=act_open("cut", both("act.revision"), "revisions"), revisions=len(revs))
    wait = next((s for s in st if s["state"] == "waiting_person"), None)
    if wait:
        n, many, ear = seen(wait), wait["id"] in PLURAL, wait["id"] in LISTEN
        v = [w("take.listen" if ear else "take.look", i) for i in (0, 1)]
        return say("waiting_you", who, "decide",
                   two(w("waiting_you", 0, s=n["zh"], v=v[0]), w("waiting_you", 1, S=cap(n["en"]), be="are" if many else "is", wait="wait" if many else "waits")),
                   [both("waiting_you.listening" if listening else "waiting_you.alone")],
                   two(w("waiting_you.short", 0, s=n["zh"], v=v[0]), w("waiting_you.short", 1, s=n["en"])),
                   act_open(MOD.get(wait["id"], "cut"), two(w("act.look", 0, v=v[0], s=n["zh"]), w("act.look", 1, V=cap(v[1]), s=n["en"]))),
                   stop=wait["id"], listening=listening)
    took = None   # when an agent was handed the person's submissions for this stop
    if fb.get("handed"):
        try:
            took = (project / "out" / "review" / "feedback" / ".consumed").stat().st_mtime
        except OSError:
            took = None
    if fb.get("pending"):   # the newest submission: nobody has it yet, whatever else runs
        if listening:   # a live listener (and its agent) takes it within the second
            return say("notes_sent", who, "none", both("notes_sent"), stop=nxt["id"])
        try:
            tl = clock((project / fb["last"]).stat().st_mtime, now)
        except (OSError, KeyError, TypeError):
            tl = clock(now, now)
        x = doing(working[0]) if working else None
        more = [two(w("notes_unheard.busy", 0, x=x[0], t=tl), w("notes_unheard.busy", 1, X=cap(x[1]), t=tl))] if x else [both("notes_unheard.more")]
        return say("notes_unheard", who, "nudge", both("notes_unheard"), more, act=act_tell(both("act.fetch"), both("say.fetch")),
                   stop=nxt["id"], pending=fb["pending"])
    if fb.get("handed") and busy:   # an agent has the submission, and something works on this film now
        x = doing(working[0]) if working else None
        return say("notes_taken", who, "none", both("notes_taken"), [two(w("now_doing", 0, x=x[0]), w("now_doing", 1, X=cap(x[1]))) if x else both("in_studio")],
                   tone="busy", cmd=working[0].get("cmd") if working else None)
    if working:
        x = doing(working[0])
        return say("running", who, "none", two(w("running", 0, x=x[0]), w("running", 1, X=cap(x[1]))),
                   short=two(w("running.short", 0, x=x[0]), w("running.short", 1, x=x[1])), tone="busy", cmd=working[0].get("cmd"))
    if turn:
        return say("working", who, "none", both("working"), [both("in_studio")], tone="busy")
    deliver = next((s for s in st if s["id"] == "deliver"), None)
    if deliver and deliver["state"] == "done":
        d = deliver.get("delivered") or {}
        dl = sorted(o.get("deliveries") or [], key=lambda x: x.get("time") or "")
        films = [dl[-1]["output"]] if dl else d.get("films") or [f for f in [(o.get("media") or {}).get("film")] if f]
        film = films[0] if films else None
        vers = o.get("versions") or {}
        vid = (vers.get("current") or {}).get(film) if film else None
        subs = subtitles(project, film)
        day = (d.get("date") or "")[5:]
        gone = bool(film) and not (project / film).exists()
        bits = []
        if film:
            bits.append(two(w("delivered.film", 0, f=film) + (w("delivered.gone", 0) if gone else ""), w("delivered.film", 1, f=film) + (w("delivered.gone", 1) if gone else "")))
        if subs:
            bits.append(both("delivered.subs", f=", ".join(subs)))
        if vid:
            bits.append(both("delivered.version", v=vid))
        line = two("；".join(b["zh"] for b in bits) + "。", "; ".join(b["en"] for b in bits) + ".") if bits else None
        dd = f" {day}" if day else ""
        return say("delivered", who, "none", two(w("delivered", 0, d=f"（{day}）" if day else ""), w("delivered", 1, d=dd)), [line],
                   two(w("delivered.short", 0, d=dd), w("delivered.short", 1, d=dd)), act_open("ship", both("act.ship")),
                   paths=([film] if film and not gone else []) + subs, film=film, subtitles=subs, version=vid)
    if any(s["state"] == "no_record" for s in st):
        return say("no_record", who, "none", both("no_record"), [both("no_record.more")])
    # the agent's move, and nothing works on the film now: the last thing seen and when; "stopped" only on positive evidence
    do = (o.get("next_step") or {}).get("do") or ""
    made = (o.get("media") or {}).get("film") or next((r["path"] for r in o.get("renders") or []), None)
    has = both("made", f=made) if made else None
    read = two(w("read_at", 0, t=clock(took, now)), w("read_at", 1, t=clock(took, now))) if took else None
    seen_all = signs(project, o, talk, took)
    last = seen_all[-1] if seen_all else None
    lastw = None
    if last:
        a = ago(now - last[0])
        lastw = two(w("last", 0, a=a[0], x=last[1][0]), w("last", 1, a=a[1], x=last[1][1]))
    paths = [made] + [s[3] for s in seen_all[-1:] if s[3]]
    agent = open_agent(o)
    recent = bool(last) and now - last[0] < RECENT
    carry = act_tell(both("act.carry"), both("say.carry"), confirm=recent, secondary=recent)   # something happened lately: an offer, said second
    if last and last[2] in ("gone", "talk_cancelled", "talk_error", "talk_cut") and not agent:   # it broke, and nothing came after
        a, why, short = ago(now - last[0]), last[1], last[4] or last[1]
        return say("stopped", who, "nudge", two(w("stopped", 0, x=short[0]), w("stopped", 1, x=short[1])),
                   [two(w("stopped.since", 0, a=a[0], x=why[0]), w("stopped.since", 1, a=a[1], X=cap(why[1]))), read, has, later],
                   act=act_tell(both("act.carry"), two(w("say.stopped", 0, x=why[0]), w("say.stopped", 1, x=why[1]))), paths=paths)   # (it broke: nothing to ask twice)
    if agent:
        return say("agent_open", who, "offer", both("agent_open"), [lastw, read, later],
                   act=act_tell(both("act.carry_open"), both("say.carry"), confirm=True, secondary=True), paths=paths)
    if nxt is not None and nxt["id"] == "deliver" and nxt["state"] == "in_progress":
        chk = o.get("check") or {}
        g = "cut" if "not decided" in ((deliver or {}).get("note") or "") else "check" if chk.get("verdict") == "fail" and not chk.get("stale") else "final"
        return say("ship_missing", who, "none", two(w("ship_missing", 0, x=w(f"gap.{g}", 0)), w("ship_missing", 1, x=w(f"gap.{g}", 1))), [has, lastw],
                   act=act_open("cut", both("act.go_cut")) if g == "cut" else act_open("ship", both("act.go_ship"), "check"), paths=paths)
    if do.startswith("the engine's scaffold is not there") or "the engine is not installed yet" in do:
        return say("setup", who, "offer", both("setup"), [both("setup.more"), lastw], act=carry, paths=paths)
    return say("idle", who, "offer", both("idle"), [lastw, read, later, has], act=carry, paths=paths)


def _seconds(out):
    """The Output line's length, when it is written plainly: (a, b) a span, (a, None) one length, else None. A part still
    the template's ({…}) gives none."""
    o = re.sub(r"\{[^}]*\}", " ", out or "")
    m = re.search(r"(?<![\d.])(\d+)\s*[–-]\s*(\d+)\s*s\b", o)
    if m:
        return int(m.group(1)), int(m.group(2))
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    try:
        import gatecheck as G
        s = G.film_seconds(o)
    except Exception:
        s = None
    return (int(round(s)), None) if s else None


def _narration(lang_line):
    """[zh, en] of the BRIEF's narration, when it says so plainly; else None (never guessed)."""
    m = re.search(r"narration:\s*([^{<|]+)", lang_line or "")
    v = m.group(1).strip().lower() if m else ""
    if not v:
        return None
    if re.search(r"\b(none|no|without)\b|无|没有|不要", v):
        k = "plan.silent"
    elif re.search(r"\bsong\b|歌", v):
        k = "plan.song"
    elif re.search(r"\b(tts|voice|voice-over|voiceover|narrat\w*|recording|recorded)\b|旁白|配音|录音|人声", v):
        k = "plan.narrated"
    else:
        return None
    return [w(k, 0), w(k, 1)]


def plan_line(o):
    """{zh, en}: what the film is planned to be and where it stops for the person, from the BRIEF's lines and the film's own
    stops (bin/vh status's stops: gates and checkpoints, never the effort level); None when the project says nothing of it
    yet. What cannot be read with certainty is left out."""
    spec = (o.get("project") or {}).get("spec") or {}
    out = spec.get("Output") or ""
    parts, size = [], ["", ""]
    s = _seconds(out)
    if s:
        a, b = s
        if b:
            size = [w("plan.span", i, a=a, b=b) for i in (0, 1)]
        elif a >= 120:
            size = [w("plan.min" if a % 60 == 0 else "plan.min_s", i, m=a // 60, s=a % 60) for i in (0, 1)]
        else:
            size = [w("plan.secs", i, n=a) for i in (0, 1)]
    m = re.search(r"(?<![{\w])(\d{3,4})\s*[x×]\s*(\d{3,4})", out)
    if m:
        wd, ht = int(m.group(1)), int(m.group(2))
        k = "plan.vertical" if ht > wd else "plan.landscape" if wd > ht else "plan.square"
        size = [size[0] + w(k, 0), (size[1] + " " + w(k, 1)).strip()]
    if size[0]:
        parts.append(size)
    v = _narration(spec.get("Language"))
    if v:
        parts.append(v)
    stops = o.get("stops") or {}
    every = [x for x in ORDER if x in set(stops.get("gates") or []) | set(stops.get("checkpoints") or [])]
    if not every:
        parts.append([w("plan.none", 0), w("plan.none", 1)])
    elif every == ["1", "2", "3"]:
        parts.append([w("plan.123", 0), w("plan.123", 1)])
    elif every == ["1", "3"]:
        parts.append([w("plan.13", 0), w("plan.13", 1)])
    else:
        parts.append([w("plan.at", i, x=w("plan.list", i).join(w(f"stop.{x}", i) if f"stop.{x}" in WORDS else x for x in every)) for i in (0, 1)])
    if not parts:
        return None
    return two(w("plan.sep", 0).join(p[0] for p in parts), cap(w("plan.sep", 1).join(p[1] for p in parts)))
