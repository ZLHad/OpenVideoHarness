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

Reads what bin/vh status has read (its record) and a few small things beside it: saved review feedback (tools/review_feedback.py), the time the last submission was handed over (feedback/.consumed), and the tail of the newest saved conversation log (<project>/.ovh/agents/*.jsonl), the newest change
among the film's own files (a walk of at most a few thousand entries, not out/, media/, renders/), and ps for the agent a
run recorded. It starts, asks and writes nothing else.

  now = {code, who, you, tone, say: {zh, en}, more: {zh, en} | None, short: {zh, en}, act, facts}
  who: whose move it is, as bin/vh status's waiting_on; you: what the person has to do with it (decide: it waits for them;
  nudge: it needs a word from them; offer: they may; none); tone: you | busy | quiet (the dot's colour)
  act = {kind: open | tell | none, mod, sub, label: {zh, en}, text: {zh, en}, confirm, secondary}
  (tell: the words the person's click sends; confirm: ask once more first, something happened lately; secondary: not the
  main thing to do, said as a quiet second line)
  facts.paths: the project's files the words name (Studio opens them; the terminal prints them as they are)

plan_line(): the film in one line from its BRIEF and its stops ("30 秒竖屏，有旁白，中间停两次给你看：立意和初版"), or None.
"""
import json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECENT = 1800       # s: a sign of life this recent makes the offer to carry on ask once more
NOT_SOURCE = {"out", "media", "renders", "node_modules", ".ovh", ".git", "__pycache__", "cache", ".cache"}
NOT_AGENTS = {"REVIEW.md"}
HEAVY = {"assets", "audio", "sound", "sounds", "sfx", "music", "footage", "frames", "images", "img", "photos", "video", "videos", "clips", "fonts"}
BIG = 300            # entries: a folder this full is judged by its own time
OPEN_FOR = 6 * 3600  # s: an agent program still running counts as open on a film it worked on within this, or on the film it worked on last   # written by Studio for the person's own submission too: no sign of the agent

# ---------- the words: key → (zh, en); {x} are filled in ----------
WORDS = {
    # what the person sees at a stop, and how they take it in
    "seen.1": ("立意卡", "the concept cards"), "seen.2": ("分镜", "the storyboard"), "seen.3": ("初版", "the first draft"),
    "seen.E0": ("画风样张", "the style frames"), "seen.E1": ("文案", "the script"), "seen.E2": ("配乐安排", "the sound plan"),
    "seen.E3": ("最终的声音", "the final sound"), "seen.E4": ("第一章样片", "the first chapter"), "seen.E5": ("定画面的版本", "the picture lock"),
    "seen.deliver": ("交付", "the delivery"),
    "take.look": ("看", "look at"), "take.listen": ("听", "listen to"),
    # a command: what it does (zh, en), and as a thing (en)
    "cmd.render": ("渲染", "rendering", "the render"), "cmd.patch": ("重渲改过的几段", "re-rendering the changed parts", "the re-render of the changed parts"),
    "cmd.tts": ("配音", "voicing", "the voice-over"), "cmd.mix": ("混音", "mixing", "the mix"), "cmd.check": ("检查", "checking", "the check"),
    "cmd.deliver": ("出上传版", "making the upload copy", "the upload copy"), "cmd.proxy": ("做预览版", "making a preview copy", "the preview copy"),
    "cmd.thumbs": ("做缩略图", "making thumbnails", "the thumbnails"), "cmd.gate": ("出审阅页", "making the review page", "the review page"),
    "cmd.music": ("作曲", "composing", "the music"), "cmd.storyboard": ("画分镜关键帧", "drawing the storyboard frames", "the storyboard frames"),
    "cmd.qa": ("查声音", "checking the sound", "the sound check"), "cmd.mux": ("合音轨", "putting the sound on", "putting the sound on"),
    "cmd.frames": ("截取画面", "taking frames", "taking frames"), "cmd.sheet": ("出联系表", "making a contact sheet", "the contact sheet"),
    "cmd.new": ("新建片子", "starting the film", "starting the film"), "cmd.hf-init": ("装引擎", "setting up the engine", "the engine's setup"),
    "cmd.sfx": ("找音效", "finding sound effects", "the sound effects"), "cmd.image": ("出图", "making images", "the images"),
    "cmd.captions": ("做字幕", "making the subtitles", "the subtitles"), "cmd.cues": ("对时间", "lining up the timing", "the timing"),
    "cmd.readcheck": ("查字停得够不够久", "checking the words stay long enough to read", "the reading-time check"), "cmd.textcheck": ("查画面文字", "checking the text on screen", "the text check"),
    "cmd.timeline": ("排时间线", "laying out the timeline", "the timeline"), "cmd.peaks": ("画波形", "drawing the waveform", "the waveform"),
    "cmd.bgm": ("配乐", "picking the music", "the music"), "cmd.voices": ("试听声音", "trying voices", "the voice trial"), "cmd.pace": ("调配音的快慢", "evening out the voice's pace", "the voice's pace"),
    "cmd.edit": ("排剪辑表", "laying out the edit", "the edit"), "cmd.footage": ("找素材", "finding footage", "the footage"),
    "cmd.rhythm": ("画节奏图", "drawing the rhythm chart", "the rhythm chart"), "cmd.beats": ("找节拍", "finding the beats", "the beats"),
    "cmd.determinism": ("查同一帧重渲是否一样", "checking a frame renders the same twice", "the same-frame check"), "cmd.hf": ("跑引擎", "running the engine", "the engine run"),
    "cmd.versions": ("换版本", "switching versions", "the version switch"), "cmd.assets": ("登记素材", "recording assets", "the asset record"),
    "cmd.review": ("出审阅页", "making the review page", "the review page"), "cmd.concept": ("出立意卡", "making the concept cards", "the concept cards"),
    "cmd.cover-preview": ("出封面预览", "making the cover preview", "the cover preview"), "cmd.gif": ("出动图", "making the GIF", "the GIF"),
    "cmd.other": ("跑一条命令", "running a command", "a command"),
    "unit.frames": ("帧", "frames"), "unit.lines": ("句", "lines"), "unit.pictures": ("张", "pictures"),
    "progress": ("{d} / {t} {u}", "{d} of {t} {u}"), "progress.percent": ("{d}%", "{d}%"),
    "doing": ("{x}，{p}", "{x}, {p}"),
    # what was last seen happen on the film (a sign of life), by kind
    "sign.ok": ("{x}做完了", "{t} finished"), "sign.found": ("{x}结束时报了问题", "{t} ended reporting a problem"),
    "sign.check_found": ("检查查出 {n} 处要改", "the check found {n} {things} to fix"),
    "sign.stopped": ("{x}被停下了", "{t} was stopped"), "sign.gone": ("{x}中断了", "{t} was cut off"),
    "sign.gone_at": ("{x}到 {p}时中断了", "{t} was cut off at {p}"),
    "sign.page": ("发出了审阅页", "the review page went out"), "sign.wait": ("它开始等你的意见", "it began waiting for your notes"),
    "sign.handed": ("它取走了你的意见", "it picked up your notes"),
    "sign.talk_end_turn": ("Studio 里的对话做完一轮", "the Studio chat finished a turn"),
    "sign.talk_cancelled": ("Studio 里的对话被停下了", "the Studio chat was stopped"),
    "sign.talk_error": ("Studio 里的对话出错停了", "the Studio chat ended with an error"),
    "sign.talk_cut": ("Studio 里的对话做到一半断了", "the Studio chat was cut off mid-turn"),
    "sign.talk": ("Studio 里的对话有新内容", "the Studio chat moved on"),
    "sign.file": ("改了{f}", "{f} changed"),
    "last": ("{a}前，{x}。", "{A} ago, {x}."),
    "last.partial": ("{a}前，{x}（文件太多，没有一一看过）。", "{A} ago, {x} (too many files to look through them all)."),
    "ago.now": ("不到 1 分钟", "under a minute"), "ago.min": ("{n} 分钟", "{n} min"), "ago.hour": ("{n} 小时", "{n} hour"),
    "ago.hours": ("{n} 小时", "{n} hours"), "ago.days": ("{n} 天", "{n} days"),
    # the sentences, a code each: its short sentence, the card's few words (.short)
    "paused": ("你让这支片子先停着。", "You paused this film."), "paused.short": ("暂停了", "paused"),
    "revision_ready": ("照你说的改好了，等你复审。", "Changed as you said, for you to review."),
    "revision_ready.more": ("改前改后两版放在一起，在这里对照着看、听。", "The versions before and after are side by side here, to watch and listen to together."),
    "revision_ready.short": ("改好了，等你复审", "changed, for you to review"),
    "waiting_you": ("{s}出来了，等你{v}。", "{S} {be} out and {wait} for you."),
    "waiting_you.listening": ("{a} 在等着，你一发，它就接着做。", "{A} is waiting: send your notes and it carries on."),
    "waiting_you.alone": ("发出去以后，回到{a}那边说一句“我发了”。", "Once sent, tell {a} \u201cI've sent it\u201d over there."),
    "who.film": ("做这支片子的 AI ", "the AI making the film"),
    "waiting_you.short": ("{s} · 等你{v}", "{s} · for you"),
    "notes_unheard": ("你的意见存好了，还没有 AI 来取。", "Your notes are saved; no AI has picked them up yet."),
    "notes_unheard.more": ("跟做这支片子的 AI 说一声，它就来取。", "Tell the AI making the film and it will fetch them."),
    "notes_unheard.busy": ("{x}还在跑（{p}），但你 {t} 发的这一份还没人取。跟做这支片子的 AI 说一声。", "{X} is still running ({p}), but nobody has picked up the notes you sent at {t}. Tell the AI making the film."),
    "notes_unheard.busy0": ("{x}还在跑，但你 {t} 发的这一份还没人取。跟做这支片子的 AI 说一声。", "{X} is still running, but nobody has picked up the notes you sent at {t}. Tell the AI making the film."),
    "notes_unheard.short": ("意见还没人取", "notes not picked up yet"),
    "notes_sent": ("你的意见发出去了，等着的 {a} 正在取。", "{A} was waiting and is picking up your notes."),
    "notes_sent.short": ("意见发出去了", "notes sent"),
    "notes_taken": ("AI 拿到了你的意见，正在改。", "The AI has your notes and is working on them."),
    "notes_taken.short": ("在照你的意见改", "working on your notes"),
    "now_doing": ("正在{x}。", "{X}."), "in_studio": ("在 Studio 的对话里。", "In the Studio chat."),
    "running": ("正在{x}。", "{X}."), "running.short": ("正在{x}", "{x}"),
    "working": ("AI 正在做。", "The AI is working."), "working.short": ("AI 在做", "the AI is working"),
    "delivered": ("已交付{d}。", "Delivered{d}."), "delivered.short": ("已交付{d}", "delivered{d}"),
    "delivered.film": ("成片：{f}", "The film: {f}"), "delivered.gone": ("（不在这台电脑上了）", " (no longer on this computer)"),
    "delivered.subs": ("字幕：{f}", "subtitles: {f}"), "delivered.version": ("交付的是 {v}", "version {v}"),
    "no_record": ("这支片子没有审阅记录。", "This film keeps no review record."),
    "no_record.more": ("看不出它停在哪一步。", "Where it stopped cannot be told."), "no_record.short": ("没有审阅记录", "no review record"),
    "stopped": ("AI 停下了：{x}。", "The AI stopped: {x}."), "stopped.short": ("停下了", "stopped"),
    "stopped.since": ("{a}前，{x}，之后再没有变化。", "{X} {a} ago, and nothing has happened since."),
    "stopped.at": ("{a}前，{x}。", "{X} {a} ago."),
    "agent_away": ("做过它的 AI 程序还开着，可能在忙别的片子。", "The AI program that worked on it is still open, and may be busy with another film."),
    "agent_open": ("现在没在做什么；上次做这支片子的 {a} 还开着。", "Nothing is running now; {a}, which last worked on this film, is still open."),
    "agent_open.short": ("AI 开着", "an AI is open"),
    "idle": ("现在没有命令在跑。", "No command runs right now."), "idle.short": ("没有命令在跑", "nothing running"),
    "ship_missing": ("还没交付：{x}。", "Not delivered yet: {x}."), "ship_missing.short": ("还没交付", "not delivered yet"),
    "gap.cut": ("初版还没定", "the first draft is not decided yet"), "gap.check": ("成片没过检查", "the film has not passed its check"),
    "gap.final": ("正式版还没做好或还没检查", "the final is not made or not checked yet"),
    "setup": ("引擎还没装好。", "The engine is not set up yet."),
    # a command stopped because a service's API Key is not set, and it still is not (tools/keys.py)
    "needs_key": ("{x}停下了：还没有 {s} 的 API Key。", "{T} stopped: there's no {s} API Key yet."),
    "needs_key.more": ("在设置 → 服务里填上，再让 AI 接着做。", "Set it up in Settings → Services, then ask the AI to carry on."),
    "needs_key.voice": ("不想用在线服务，也可以让 AI 换成这台电脑上的声音。", "Or ask the AI to use this computer's own voice, with no service."),
    "needs_key.voice_say": ("不想用在线服务，也可以让 AI 换成 macOS 自带的声音（够打草稿）。", "Or ask the AI to use macOS's own voice, with no service (good enough for a draft)."),
    "needs_key.image_codex": ("也可以让 AI 用 Codex 出图，走 ChatGPT 的订阅，不用 API Key。", "Or ask the AI to make the pictures with Codex, on the ChatGPT plan, with no API Key."),
    "needs_key.only": ("这台电脑上没有不用 API Key 的办法。", "This computer has no way to do it without an API Key."),
    "needs_key.timing": ("不想用在线服务，也可以让 AI 在这台电脑上对时间。", "Or ask the AI to time the words on this computer, with no service."),
    "needs_key.music": ("不想用在线服务，也可以让 AI 在这台电脑上作曲。", "Or ask the AI to compose the music on this computer, with no service."),
    "needs_key.short": ("等 API Key", "waiting for an API Key"),
    "svc.gemini": ("Gemini", "Gemini"), "svc.minimax": ("MiniMax", "MiniMax"), "svc.elevenlabs": ("ElevenLabs", "ElevenLabs"),
    "svc.dashscope": ("阿里云百炼", "Alibaba Cloud Model Studio"),
    "setup.more": ("AI 接着做时会先装它（要联网）。", "The AI sets it up first when it carries on (it needs the network)."),
    "setup.short": ("引擎还没装好", "engine not set up"),
    "unknown": ("读不出这支片子现在到哪了。", "Where this film stands could not be worked out."), "unknown.short": ("读不出", "unreadable"),
    # the facts in the line under a sentence
    "read_at": ("你 {t} 发的意见它读过了。", "It has read the notes you sent at {t}."),
    "made": ("已经做好：{f}。", "Made so far: {f}."),
    "next": ("下一步是{s}。", "Next: {s}."), "next.notes": ("下一步：照你的意见改{s}。", "Next: {s}, changed as your notes say."),
    # the buttons, and the words a tell button sends (only these words, numbers and times: nothing else from the project)
    "act.look": ("去{v}{s}", "{V} {s}"), "act.revision": ("去复审", "Review the change"), "act.ship": ("打开交付", "Open the delivery"),
    "act.settings": ("去设置 → 服务", "Open Settings → Services"),
    "act.go_cut": ("去看初版", "Go to the first draft"), "act.go_ship": ("去看交付", "Go to the delivery"),
    "act.carry": ("让 AI 接着做", "Ask the AI to carry on"), "act.fetch": ("让 AI 来取意见", "Ask the AI to fetch your notes"),
    "act.carry_open": ("它没反应的话，在这里另开一个 AI 接着做", "If it doesn't answer, start another AI here to carry on"),
    "say.carry": ("接着做这支片子。先跑 bin/vh status 看下一步。", "Carry on with this film. Run bin/vh status first for the next step."),
    "say.stopped": ("接着做这支片子。上次{x}。先跑 bin/vh status 看下一步。", "Carry on with this film. Last time {x}. Run bin/vh status first for the next step."),
    "say.fetch": ("我在 Studio 发了这一步的意见。去取来看（bin/vh status 会说怎么取），然后接着做。",
                  "I sent my notes for this step in Studio. Fetch and read them (bin/vh status says how), then carry on."),
    "say.resume": ("接着做这支片子：REVIEW.md 里写着暂停，现在恢复，在那里记一节恢复。先跑 bin/vh status 看下一步。",
                   "Carry on with this film: REVIEW.md says paused; it resumes now, so note that there. Run bin/vh status first for the next step."),
    # the person's notes nobody has taken, and who holds the film outside Studio's window (new words: the agent by its name
    # when known, else "AI"; the step by name; never a file name)
    "seen.outline": ("大纲", "the outline"), "seen.script": ("文案", "the script"),
    "step.1": ("立意", "the concept"), "step.outline": ("大纲", "the outline"), "step.E0": ("画风样张", "the style frames"),
    "step.E1": ("文案", "the script"), "step.2": ("分镜", "the storyboard"), "step.E2": ("配乐安排", "the sound plan"),
    "step.E3": ("最终的声音", "the final sound"), "step.3": ("初版", "the first draft"), "step.E4": ("第一章样片", "the first chapter"),
    "step.E5": ("定画面的版本", "the picture lock"), "step.notes": ("随手写的意见", "your loose notes"), "step.other": ("这一页", "this page"),
    "prog.claude": ("Claude Code", "Claude Code"), "prog.codex": ("Codex", "Codex"), "prog.dsh": ("DeepSeek Harness", "DeepSeek Harness"), "prog.ai": ("AI", "the AI"),
    "notes_late": ("{s}那一轮被取走以后，你又发了 {n} 条，还没有 AI 来取。", "After {s} was picked up you sent {n} more {n_notes}; no AI has picked them up yet."),
    "notes_late.short": ("补发的意见还没人取", "later notes not picked up"),
    "notes_left": ("你发的 {n} 份意见还没有 AI 来取（{s}）。", "{N} {n_subs} you sent {are} not picked up by any AI yet ({s})."),
    "notes_left.short": ("意见还没人取", "notes not picked up yet"),
    "notes_left.live": ("正在等的 {a} 马上会取。", "The {a} that is waiting picks them up at once."),
    "notes_left.outside": ("这支片子开在这个窗口外面的 {a} 里：回到它那边说一声“我发了”，它就会来取。", "This film is open in {A} outside this window: tell it \u201cI've sent it\u201d over there and it picks them up."),
    "notes_left.next": ("现在没有 AI 在等。下次有 AI 接着做这支片子，会先拿到它们。", "No AI is waiting right now. The next AI to carry on with this film gets them first."),
    "notes_left.also": ("{s}也出来了，等你{v}。", "{S} {be} out for you too."),
    "agent_outside": ("这支片子开在这个窗口外面的 {a} 里；在这里打的字，它收不到。", "This film is open in {A} outside this window; what you type here does not reach it."),
    "agent_outside.more": ("要它接着做，回到它那边说一句。", "To have it carry on, say so over there."),
    "agent_outside.short": ("开在窗口外面", "open outside this window"),
    "act.second": ("在这里另起一个 AI 做这支片子", "Start a second AI on this film here"),
    "act.second_sure": ("确定，另起一个", "Yes, start a second one"),
    "act.second_note": ("外面那个 {a} 还开着。两个一起做，可能改到同一处。", "{A} outside is still open. Two working at once may change the same thing."),
    # the film's plan
    "plan.secs": ("{n} 秒", "{n} s"), "plan.span": ("{a}–{b} 秒", "{a}–{b} s"), "plan.min": ("{m} 分钟", "{m} min"), "plan.min_s": ("{m} 分 {s} 秒", "{m} min {s} s"),
    "plan.vertical": ("竖屏", "vertical"), "plan.landscape": ("横屏", "landscape"), "plan.square": ("方屏", "square"),
    "plan.narrated": ("有旁白", "narrated"), "plan.silent": ("没有旁白", "no narration"), "plan.song": ("配一首歌", "set to a song"),
    "plan.none": ("中间不停，做完给你看", "no stops on the way: you see it finished"),
    "plan.13": ("中间停两次给你看：立意和初版", "it stops twice for you: the concept and the first draft"),
    "plan.123": ("中间停三次给你看：立意、分镜、初版", "it stops three times for you: the concept, the storyboard and the first draft"),
    "plan.at": ("中间停下给你看：{x}", "it stops for you at {x}"), "plan.sep": ("，", ", "), "plan.list": ("、", ", "),
    "stop.1": ("立意", "the concept"), "stop.2": ("分镜", "the storyboard"), "stop.3": ("初版", "the first draft"), "stop.E0": ("画风样张", "the style frames"),
    "stop.E1": ("文案", "the script"), "stop.E2": ("配乐安排", "the sound plan"), "stop.E3": ("定声音", "the final sound"), "stop.E4": ("第一章样片", "the first chapter"),
    "stop.E5": ("定画面", "the picture lock"),
}
# a film's own documents by what they are, in what the person reads (core.js FILE_WORDS says the same)
FILE_WORDS = {"REVIEW.md": ("审阅记录", "the review record"), "BRIEF.md": ("简报", "the brief"), "DECISIONS.md": ("决定记录", "the decision record"),
              "LESSONS.md": ("经验记录", "the lessons"), "NOTES.md": ("笔记", "the notes"), "SCRIPT.md": ("文案", "the script"), "STORYBOARD.md": ("分镜表", "the storyboard"),
              "PACKAGING.md": ("标题和封面", "the titles and covers"), "STYLE.md": ("风格说明", "the style notes"), "shots.json": ("镜头表", "the shot table")}
MOD = {"1": "idea", "E0": "idea", "E1": "outline", "2": "board", "E2": "sound", "E3": "sound", "3": "cut", "E4": "cut", "E5": "cut", "deliver": "ship"}   # core.js's GATE_MOD
PLURAL = {"1", "E0"}     # the concept cards, the style frames
LISTEN = {"E3"}          # the final sound: listened to (the sound plan, E2, is a cue sheet: looked at)
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
    """A span, to the nearest whole minute, hour or day."""
    m = max(0.0, secs) / 60
    if m < 1:
        return [w("ago.now", i) for i in (0, 1)]
    if m < 59.5:
        return [w("ago.min", i, n=int(round(m))) for i in (0, 1)]
    if m < 47.5 * 60:
        h = int(round(m / 60))
        return [w("ago.hour" if h == 1 else "ago.hours", i, n=h) for i in (0, 1)]
    return [w("ago.days", i, n=int(round(m / 1440))) for i in (0, 1)]


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


def unread(project):
    """Saved feedback that still needs a decision."""
    try:
        import review_feedback
        return review_feedback.unread(project)
    except (OSError, ValueError):
        return []


def program_of(agent):
    """The agent program's name (claude, codex …) of a run's agent record, or None."""
    try:
        import activity
        name = os.path.basename(activity._ps(int(agent["pid"]), "comm=") or "")
        if name in activity.RUNTIMES:
            name = next((os.path.basename(x) for x in activity._ps(int(agent["pid"]), "command=").split() if activity.AGENT_PROGRAMS.match(os.path.basename(x))), name)
        return name if activity.AGENT_PROGRAMS.match(name) else None
    except Exception:
        return None


def in_studio(agent):
    """Is this agent program one Studio's own column started (it runs under a desk server: tools/desk/desk.py among its
    parents)? None when that cannot be told."""
    try:
        import activity
        p = int(agent["pid"])
        for _ in range(16):
            if p <= 1:
                return False
            line = activity._ps(p, "ppid=,command=").split(None, 1)
            if len(line) < 2 or not line[0].isdigit():
                return None
            if re.search(r"tools/desk/desk\.py\b", line[1]):
                return True
            p = int(line[0])
        return False
    except Exception:
        return None


def prog_words(name):
    """[zh, en] of an agent program for the person: Claude Code, Codex, else AI."""
    k = f"prog.{name}" if f"prog.{name}" in WORDS else "prog.ai"
    return [w(k, 0), w(k, 1)]


def has_cards(project, pid):
    """Does this review page hold concept cards (an option with a picture: its frame)? A gate ① page without them is about
    the outline."""
    try:
        d = json.loads((Path(project) / "out" / "review" / f"gate-{pid}.json").read_text(encoding="utf-8-sig"))
        return any(isinstance(o, dict) and o.get("frame") for x in d.get("decisions") or [] if isinstance(x, dict) for o in x.get("options") or [])
    except (OSError, ValueError, AttributeError, TypeError):
        return True


def page_of(s):
    """The page id a station is at (its latest page), else its own id."""
    return Path(s["page"]).stem[5:] if s.get("page") else s["id"]


def stop_place(project, s):
    """(module, tab, seen-words key) of what a stop's page asks the person about: a gate ① page with concept cards is the
    concept, one without is the outline; E1 is the script, on the outline's script tab; the rest as MOD says."""
    pid = page_of(s)
    if s["id"] == "1" and not has_cards(project, pid):
        return "outline", None, "seen.outline"
    if s["id"] == "E1":
        return "outline", "script", f"seen.{s['id']}"
    return MOD.get(s["id"], "cut"), None, f"seen.{s['id']}"


def step_words(round_id):
    """[zh, en] of a round's step by name (旁白稿, 大纲 …), from its page id (1b → gate ①: the concept or outline)."""
    m = re.match(r"^(E\d|\d)", str(round_id or ""))
    k = "step.notes" if round_id == "notes" else f"step.{m.group(1)}" if m and f"step.{m.group(1)}" in WORDS else "step.other"
    return [w(k, 0), w(k, 1)]


def newest_file(project, limit=4000):
    """(mtime, path from the project, whole) of the newest change among the film's own files, or None. Where source lives is
    looked at first (the film's folder, then its folders breadth first, four deep); out/, media/, renders/ … are not its
    source. A heavy folder (HEAVY by name, or one of more than BIG entries: assets, sound, frame sequences) is judged by its
    own time (it changes when a file in it is added, removed or renamed), not file by file. whole: False when the walk was
    cut short at limit entries, so something newer may be there unseen."""
    best, seen, whole = None, 0, True
    queue = [(Path(project), 0)]

    def take(m, path):
        nonlocal best
        if best is None or m > best[0]:
            best = (m, path)
    while queue:
        d, depth = queue.pop(0)
        try:
            it = list(os.scandir(d))
        except OSError:
            continue
        if depth and len(it) > BIG:   # a frame sequence, a stock of clips: the folder's own time stands for it
            try:
                take(d.stat().st_mtime, os.path.relpath(d, project) + "/")
            except OSError:
                pass
            continue
        for e in it:
            if seen >= limit:
                whole = False
                break
            seen += 1
            if e.name.startswith("."):
                continue
            try:
                if e.is_dir(follow_symlinks=False):
                    if e.name in NOT_SOURCE:
                        continue
                    if e.name.lower() in HEAVY:
                        take(e.stat(follow_symlinks=False).st_mtime, os.path.relpath(e.path, project) + "/")
                    elif depth < 4:
                        queue.append((Path(e.path), depth + 1))
                elif e.is_file(follow_symlinks=False) and not (depth == 0 and e.name in NOT_AGENTS):
                    take(e.stat(follow_symlinks=False).st_mtime, os.path.relpath(e.path, project))
            except OSError:
                continue
        if not whole:
            break
    return (best[0], best[1], whole) if best else None


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
        return (t, [w("sign.check_found", 0, n=n), w("sign.check_found", 1, n=n, things="thing" if n == 1 else "things")], "found")
    return (t, [w("sign.found", 0, x=c[0]), w("sign.found", 1, t=c[2])], "found")


def signs(project, o, talk, took):
    """Every sign of life on the film the disk keeps, oldest first: ([(t, [zh, en], kind, path, short [zh, en] or None)], whole);
    whole: False when the look through the film's files was cut short (a newer change may be there unseen)."""
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
        fw = FILE_WORDS.get(Path(f[1]).name) if "/" not in f[1] else None   # a film's own document by its name (简报), any other file as it is
        out.append((f[0], [w("sign.file", 0, f=fw[0] if fw else " " + f[1]), w("sign.file", 1, f=fw[1] if fw else f[1])], "file", f[1], None))
    return sorted(out, key=lambda x: x[0]), bool(f is None or f[2])


def open_agent(o, project, newest, now):
    """The agent program the newest recorded run was started under, while that very process lives: ("here", record) when its
    most recent recorded work is this film or this film's newest sign of life is within OPEN_FOR; ("elsewhere", record) when
    it lives but works elsewhere (a long-lived program, such as the one behind Studio's column, that served many films); None."""
    act = o.get("activity") or {}
    runs = [r for r in (act.get("running") or []) + (act.get("listening") or []) + (act.get("recent") or []) if isinstance(r.get("agent"), dict)]
    if not runs:
        return None
    r = max(runs, key=lambda x: x.get("end") or x.get("start") or 0)
    try:
        import activity
        if not activity.agent_alive(r["agent"]):
            return None
        last_film = activity.agent_work(r["agent"])
        here = last_film == os.path.realpath(str(project)) or (newest is not None and now - newest < OPEN_FOR)
        return ("here" if here else "elsewhere", r["agent"])
    except Exception:
        return None


def holder(project, o, now=None):
    """The agent program open on this film now (the one its newest recorded run was started under, alive, and this film its
    latest work): {program: claude | codex | … | None, outside: it is not one Studio's own column started}, or None. Studio
    names it when it says who picks the person's notes up."""
    held = open_agent(o, project, None, time.time() if now is None else now)
    if not held or held[0] != "here":
        return None
    return {"program": program_of(held[1]), "outside": in_studio(held[1]) is False}


def say(code, who, you, s, more=None, short=None, act=None, paths=(), tone=None, **facts):
    """s, short: {zh, en}; more: a list of {zh, en} (None skipped), joined into the line under the sentence."""
    parts = [m for m in more or [] if m]
    line = two("".join(m["zh"] for m in parts), " ".join(m["en"] for m in parts)) if parts else None
    tone = tone or ("you" if you in ("decide", "nudge") else "quiet")
    return {"code": code, "who": who, "you": you, "tone": tone, "say": s, "more": line, "short": short or both(code + ".short"),
            "act": act or {"kind": "none"}, "facts": dict(facts, paths=[p for p in dict.fromkeys(paths) if p])}


def act_open(mod, label, sub=None):
    return {"kind": "open", "mod": mod, "sub": sub, "label": label}


def act_settings(label, sub):
    return {"kind": "settings", "mod": None, "sub": sub, "label": label}


DOES = {"tts": {"voice", "timing"}, "voices": {"voice"}, "pace": {"timing"}, "music": {"music"}, "image": {"image"}}   # the kinds of work a run that ended fine did
NEED_OF = {"tts": "voice", "voices": "voice", "pace": "timing", "music": "music", "image": "image"}   # a record that does not say what its key was for


def need_of(r):
    return (r.get("error") or {}).get("need") or NEED_OF.get(r.get("cmd"))


def key_stop(runs):
    """The newest finished run that stopped for want of an API Key (code no_key) that nothing after it settled, or None.
    A later run that did the same kind of work fine settles it (a voice-over clears a voice or a timing stop; a picture an
    image stop); a later run of anything that failed or was cut off takes the line, since it is newer news; one stopped on
    purpose, and the console's own run, count for neither. The whole log is read (bin/vh status passes it as
    activity.key_stop), not a window of the last few runs."""
    done = [r for r in runs if r.get("state") in ("ok", "failed", "gone") and r.get("cmd") != "desk"]
    at = max((i for i, r in enumerate(done) if r.get("state") == "failed" and (r.get("error") or {}).get("code") == "no_key"), default=None)
    if at is None:
        return None
    need = need_of(done[at])
    for r in done[at + 1:]:
        if r.get("cancelled") or r.get("exit") in (130, 143):
            continue
        if r.get("state") == "gone" or r.get("exit") != 0:
            return None
        if need in DOES.get(r.get("cmd"), ()):
            return None
    return done[at]


def needs_key(o):
    """The run that stopped for want of a service's API Key (key_stop) while that key is still not set: (run, the key names
    it waits on, the service, what the key was for), or None. Once a key it names is set (in Studio or the environment),
    the film waits no more."""
    act = o.get("activity") or {}
    r = act["key_stop"] if "key_stop" in act else key_stop(act.get("recent") or [])
    if not r:
        return None
    try:
        import keys
    except Exception:
        return None
    err = r.get("error") or {}
    names = [n for n in err.get("keys") or [] if n in keys.KEY_NAMES] or [n for n in keys.KEY_NAMES if re.search(r"\b" + n + r"\b", err.get("message") or "")]
    try:
        left = keys.wanted(names)
    except Exception:
        left = []
    if not left:
        return None
    return r, left, (keys.module_of(left[0]) or {}).get("name"), need_of(r)


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
    talk = conversation(project)
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
    un = unread(project)
    cur_pid = page_of(nxt) if nxt else None
    covered = not un or (wait is None and nxt is not None and fb.get("pending") and all(j.get("round") == cur_pid and not late for _, j, late in un))
    if wait:   # what the waiting page asks about: a gate ① page without cards is the outline, E1 is the script (its tab)
        mod, tab, seen_key = stop_place(project, wait)
        n, many, ear = (both(seen_key) if seen_key in WORDS else seen(wait)), wait["id"] in PLURAL and seen_key != "seen.outline", wait["id"] in LISTEN
        v = [w("take.listen" if ear else "take.look", i) for i in (0, 1)]
    if not covered:   # notes the person sent that nobody took: said first, with who takes them; never "received" until a run took them
        held0 = open_agent(o, project, None, now)
        prog = program_of(held0[1]) if held0 and held0[0] == "here" else None
        outside = bool(held0 and held0[0] == "here" and in_studio(held0[1]) is False)
        late = [(f, j) for f, j, lt in un if lt]
        if late:
            r = late[-1][1].get("round")
            sw = step_words(r)
            if str(r).startswith("1") and not has_cards(project, r):
                sw = [w("step.outline", 0), w("step.outline", 1)]
            nl = sum(len(j.get("items") or []) + (1 if j.get("general") else 0) + len(j.get("decisions") or {}) for _, j in late if isinstance(j, dict))
            nl = nl or len(late)
            head = two(w("notes_late", 0, s=sw[0], n=nl), w("notes_late", 1, s=sw[1], n=nl, n_notes="note" if nl == 1 else "notes"))
            code = "notes_late"
        else:
            rounds = list(dict.fromkeys(str(j.get("round")) for _, j, _ in un))
            sws = [step_words(r) if not (r.startswith("1") and not has_cards(project, r)) else [w("step.outline", 0), w("step.outline", 1)] for r in rounds]
            k = len(un)
            head = two(w("notes_left", 0, n=k, s=w("plan.list", 0).join(x[0] for x in sws)),
                       w("notes_left", 1, N=k, n_subs="submission" if k == 1 else "submissions", are="is" if k == 1 else "are", s=w("plan.list", 1).join(x[1] for x in sws)))
            code = "notes_left"
        a = prog_words(prog)
        who_line = two(w("notes_left.outside", 0, a=a[0]), w("notes_left.outside", 1, A=cap(a[1]))) if outside else both("notes_left.next")
        also = two(w("notes_left.also", 0, s=n["zh"], v=v[0]), w("notes_left.also", 1, S=cap(n["en"]), be="are" if many else "is")) if wait else None
        act = act_open(mod, two(w("act.look", 0, v=v[0], s=n["zh"]), w("act.look", 1, V=cap(v[1]), s=n["en"])), tab) if wait else \
            (None if outside else act_tell(both("act.fetch"), both("say.fetch")))
        return say(code, "agent", "nudge", head, [who_line, also], both(code + ".short"), act,
                   tone="you", unread=len(un), late=len(late), live=False, outside=outside, program=prog)
    if wait:
        h0 = open_agent(o, project, None, now)
        p0 = program_of(h0[1]) if h0 and h0[0] == "here" else None
        wa = prog_words(p0)   # the agent by its name where it is known: Claude Code, Codex, else AI
        wb = [" " + wa[0] + " ", wa[1]] if p0 and f"prog.{p0}" in WORDS else [w("who.film", 0), w("who.film", 1)]
        return say("waiting_you", who, "decide",
                   two(w("waiting_you", 0, s=n["zh"], v=v[0]), w("waiting_you", 1, S=cap(n["en"]), be="are" if many else "is", wait="wait" if many else "waits")),
                   [two(w("waiting_you.alone", 0, a=wb[0]), w("waiting_you.alone", 1, a=wb[1]))],
                   two(w("waiting_you.short", 0, s=n["zh"], v=v[0]), w("waiting_you.short", 1, s=n["en"])),
                   act_open(mod, two(w("act.look", 0, v=v[0], s=n["zh"]), w("act.look", 1, V=cap(v[1]), s=n["en"])), tab),
                   stop=wait["id"], listening=False)
    took = None   # when an agent was handed the person's submissions for this stop
    if fb.get("handed"):
        try:
            took = (project / "out" / "review" / "feedback" / ".consumed").stat().st_mtime
        except OSError:
            took = None
    if fb.get("pending"):   # the newest submission: nobody has it yet, whatever else runs
        try:
            tl = clock((project / fb["last"]).stat().st_mtime, now)
        except (OSError, KeyError, TypeError):
            tl = clock(now, now)
        c, pr = (cmd_words(working[0]), progress(working[0])) if working else (None, None)
        held0 = open_agent(o, project, None, now)
        outside = bool(held0 and held0[0] == "here" and in_studio(held0[1]) is False)
        if outside and not c:   # the agent that would fetch them is outside this window: what to say there, no button that starts another
            a = prog_words(program_of(held0[1]))
            return say("notes_unheard", who, "nudge", both("notes_unheard"), [two(w("notes_left.outside", 0, a=a[0]), w("notes_left.outside", 1, A=cap(a[1])))],
                       stop=nxt["id"], pending=fb["pending"], outside=True)
        more = [two(w("notes_unheard.busy", 0, x=c[0], p=pr[0], t=tl), w("notes_unheard.busy", 1, X=cap(c[2]), p=pr[1], t=tl)) if pr else
                two(w("notes_unheard.busy0", 0, x=c[0], t=tl), w("notes_unheard.busy0", 1, X=cap(c[2]), t=tl))] if c else [both("notes_unheard.more")]
        return say("notes_unheard", who, "nudge", both("notes_unheard"), more, act=act_tell(both("act.fetch"), both("say.fetch")),
                   stop=nxt["id"], pending=fb["pending"])
    if fb.get("handed") and working:   # an agent has the submission, and something works on this film now
        x = doing(working[0])
        return say("notes_taken", who, "none", both("notes_taken"), [two(w("now_doing", 0, x=x[0]), w("now_doing", 1, X=cap(x[1])))],
                   tone="busy", cmd=working[0].get("cmd"))
    if working:
        x = doing(working[0])
        return say("running", who, "none", two(w("running", 0, x=x[0]), w("running", 1, X=cap(x[1]))),
                   short=two(w("running.short", 0, x=x[0]), w("running.short", 1, x=x[1])), tone="busy", cmd=working[0].get("cmd"))
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
    nk = needs_key(o)
    if nk:   # only the person can give a key: what to do and where, and what works without one
        r, names, svc, need = nk
        c, sv = cmd_words(r), both(f"svc.{svc}") if f"svc.{svc}" in WORDS else two(svc or "", svc or "")
        try:   # what does the same work with no key on this computer (the platform decides: tools/keys.py)
            import keys
            way = keys.local_way(need)[0] if need else None
        except Exception:
            way = None
        return say("needs_key", who, "decide", two(w("needs_key", 0, x=c[0], s=sv["zh"]), w("needs_key", 1, T=cap(c[2]), s=sv["en"])),
                   [both("needs_key.more"), both(f"needs_key.{way}" if way else "needs_key.only")], both("needs_key.short"),
                   act_settings(both("act.settings"), "services"), cmd=r.get("cmd"), keys=names, service=svc, need=need)
    # the agent's move, and nothing works on the film now: the last thing seen and when; "stopped" only on positive evidence
    do = (o.get("next_step") or {}).get("do") or ""
    made = (o.get("media") or {}).get("film") or next((r["path"] for r in o.get("renders") or []), None)
    has = both("made", f=made) if made else None
    read = two(w("read_at", 0, t=clock(took, now)), w("read_at", 1, t=clock(took, now))) if took else None
    seen_all, whole = signs(project, o, talk, took)
    last = seen_all[-1] if seen_all else None
    lastw = None
    if last:
        a = ago(now - last[0])
        k = "last" if whole else "last.partial"   # a look cut short says only what it saw
        lastw = two(w(k, 0, a=a[0], x=last[1][0]), w(k, 1, A=cap(a[1]), x=last[1][1]))
    paths = [made] + [s[3] for s in seen_all[-1:] if s[3]]
    held = open_agent(o, project, last[0] if last else None, now)
    agent = held if held and held[0] == "here" else None
    away = both("agent_away") if held and held[0] == "elsewhere" else None   # the program lives, busy with another film perhaps
    recent = bool(last) and now - last[0] < RECENT
    carry = act_tell(both("act.carry"), both("say.carry"), confirm=recent, secondary=recent)   # something happened lately: an offer, said second
    if last and last[2] in ("gone", "talk_cancelled", "talk_error", "talk_cut") and not agent:   # it broke, and nothing came after
        a, why, short = ago(now - last[0]), last[1], last[4] or last[1]
        k = "stopped.since" if whole else "stopped.at"   # "nothing since" only when every file was looked at
        return say("stopped", who, "nudge", two(w("stopped", 0, x=short[0]), w("stopped", 1, x=short[1])),
                   [two(w(k, 0, a=a[0], x=why[0]), w(k, 1, a=a[1], X=cap(why[1]))), read, has, later, away],
                   act=act_tell(both("act.carry"), two(w("say.stopped", 0, x=why[0]), w("say.stopped", 1, x=why[1]))), paths=paths)   # (it broke: nothing to ask twice)
    if agent and in_studio(agent[1]) is False:   # an agent outside this window: Studio cannot reach that conversation, and says so
        a = prog_words(program_of(agent[1]))
        sec = act_tell(both("act.second"), both("say.carry"), confirm=True, secondary=True)
        sec.update(sure=both("act.second_sure"), sure_note=two(w("act.second_note", 0, a=a[0]), w("act.second_note", 1, A=cap(a[1]))))
        return say("agent_outside", who, "offer", two(w("agent_outside", 0, a=a[0]), w("agent_outside", 1, A=cap(a[1]))),
                   [both("agent_outside.more"), lastw, read, later], act=sec, paths=paths, program=program_of(agent[1]))
    if agent:
        a = prog_words(program_of(agent[1]))
        return say("agent_open", who, "offer", two(w("agent_open", 0, a=a[0]), w("agent_open", 1, a=a[1])), [lastw, read, later],
                   act=act_tell(both("act.carry_open"), both("say.carry"), confirm=True, secondary=True), paths=paths)
    if nxt is not None and nxt["id"] == "deliver" and nxt["state"] == "in_progress":
        chk = o.get("check") or {}
        g = "cut" if "not decided" in ((deliver or {}).get("note") or "") else "check" if chk.get("verdict") == "fail" and not chk.get("stale") else "final"
        return say("ship_missing", who, "none", two(w("ship_missing", 0, x=w(f"gap.{g}", 0)), w("ship_missing", 1, x=w(f"gap.{g}", 1))), [has, lastw],
                   act=act_open("cut", both("act.go_cut")) if g == "cut" else act_open("ship", both("act.go_ship"), "check"), paths=paths)
    if do.startswith("the engine's scaffold is not there") or "the engine is not installed yet" in do:
        return say("setup", who, "offer", both("setup"), [both("setup.more"), lastw, away], act=carry, paths=paths)
    return say("idle", who, "offer", both("idle"), [lastw, read, later, has, away], act=carry, paths=paths)


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
    """[zh, en] of the BRIEF's narration: none when the value is, or begins with, a negative (about the narration itself:
    "none (music only)", "无旁白"; not "TTS voice, no music"); a song when it is one; a voice when it names one; None when it
    cannot be told (template, 待定, ?)."""
    m = re.search(r"narration:\s*([^{<|]+)", lang_line or "")
    v = m.group(1).strip().lower() if m else ""
    if not v or re.fullmatch(r"[?？]+|tbd|todo|unknown|未定|待定|不确定|看情况", v.rstrip("。.")):
        return None
    if re.match(r"(none|no\b|without\b|无|没有|不要|不用|不配)", v):
        k = "plan.silent"
    elif re.match(r"(song|歌)", v):
        k = "plan.song"
    else:
        k = "plan.narrated"
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
