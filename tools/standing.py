"""Where a film stands, said to the person: one short sentence of what is happening, a line more when there is more to
say, and, when it is their move or nobody's, the one thing to do. bin/vh status prints the English as its `now:` lines (and
--json has the whole record); Studio shows the same words (zh or en) above its column, the short form on the space's card,
and the one action as a button. Every word is in WORDS below, zh and en together.

Reads only what bin/vh status has already read (its record), and a few small files beside it: the review's listening flag
(an agent waiting for the person's submission: its process must be alive now, tools/desk/feedback.py), the time the last
submission was handed over (feedback/.consumed), the console's agent lock (<project>/.ovh/agent.lock: a conversation in
Studio is working on it now) and the tail of the newest conversation log (<project>/.ovh/agents/*.jsonl: how its last turn
ended). Nothing here starts, asks or writes anything.

  now = {code, who, say: {zh, en}, more: {zh, en} | None, short: {zh, en}, act, facts}
  act = {kind: open | tell | none, mod, sub, label: {zh, en}, text: {zh, en}}   (tell: the words the person's click sends)
  facts.paths: the project's files the words name (Studio opens them; the terminal prints them as they are)

plan_line(): the film in one line from its BRIEF and its stops ("30 秒竖屏，有旁白，先看方向和初版"), or None.
"""
import json, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
QUIET = 1800   # s after an agent read the person's notes with nothing since: then it reads as stopped

# ---------- the words: key → (zh, en); {x} are filled in ----------
WORDS = {
    # what the person sees at a stop
    "seen.1": ("立意卡", "the concept cards"), "seen.2": ("分镜", "the storyboard"), "seen.3": ("初版", "the first cut"),
    "seen.E0": ("样帧", "the style frames"), "seen.E1": ("脚本", "the script"), "seen.E2": ("声音", "the sound"),
    "seen.E3": ("锁时的版本", "the timing lock"), "seen.E4": ("样板章", "the sample chapter"), "seen.E5": ("锁画面的版本", "the picture lock"),
    "seen.deliver": ("交付", "the delivery"),
    # a command: what it does (zh, en), and as a thing (en)
    "cmd.render": ("渲染", "rendering", "the render"), "cmd.patch": ("补渲", "patching the film", "the patch"),
    "cmd.tts": ("配音", "voicing", "the voice-over"), "cmd.mix": ("混音", "mixing", "the mix"), "cmd.check": ("检查", "checking", "the check"),
    "cmd.deliver": ("出上传版", "making the upload copy", "the upload copy"), "cmd.proxy": ("做代理", "making a proxy", "the proxy"),
    "cmd.thumbs": ("做缩略图", "making thumbnails", "the thumbnails"), "cmd.gate": ("出审阅页", "making the review page", "the review page"),
    "cmd.music": ("作曲", "composing", "the music"), "cmd.storyboard": ("画分镜关键帧", "drawing the storyboard frames", "the storyboard frames"),
    "cmd.qa": ("查声音", "checking the sound", "the sound check"), "cmd.mux": ("合音轨", "putting the sound on", "the sound"),
    "cmd.frames": ("取帧", "taking frames", "the frames"), "cmd.sheet": ("出联系表", "making a contact sheet", "the contact sheet"),
    "cmd.new": ("建项目", "making the project", "the project"), "cmd.hf-init": ("装引擎", "setting up the engine", "the engine's setup"),
    "cmd.sfx": ("找音效", "finding sound effects", "the sound effects"), "cmd.image": ("生图", "making images", "the images"),
    "cmd.other": ("bin/vh {c}", "running bin/vh {c}", "bin/vh {c}"),
    "unit.frames": ("帧", "frames"), "unit.lines": ("句", "lines"), "unit.pictures": ("张", "pictures"),
    "progress": ("{d} / {t} {u}", "{d} of {t} {u}"), "progress.percent": ("{d}%", "{d}%"),
    "doing": ("{x}，{p}", "{x}, {p}"),
    # how a command ended half-way
    "broke.stopped": ("被停下了", "was stopped"), "broke.gone": ("中断了（进程没了）", "was cut off (its process is gone)"),
    "broke.failed": ("出错停了", "failed"),
    "broke.at": ("{x}到 {p}时{how}", "{x} {how} at {p}"), "broke.gone_at": ("{x}到 {p}时中断了（进程没了）", "{x} was cut off at {p} (its process is gone)"),
    "broke.plain": ("{x}{how}", "{x} {how}"),
    "kept.chunks": ("留了 {n} 段，可以接着用", "{n} chunks kept to carry on from"), "kept.lines": ("留了 {n} 句，可以接着用", "{n} lines kept to carry on from"),
    "kept.frames": ("留了 {n} 帧，可以接着用", "{n} frames kept to carry on from"), "with_kept": ("{x}（{k}）", "{x} ({k})"),
    # the sentences, a code each: its short sentence, the line under it (.more), the card's few words (.short)
    "paused": ("你让这支片子先停着。", "You paused this film."), "paused.short": ("暂停了", "paused"),
    "revision_ready": ("照你说的改好了，等你复审。", "Changed as you said, for you to review."),
    "revision_ready.more": ("改前改后两版放在一起，在这里对照着看、听。", "The versions before and after are side by side here, to watch and listen to together."),
    "revision_ready.short": ("改好了，等你复审", "changed, for you to review"),
    "waiting_you": ("{s}出来了，等你看。", "{S} {be} out and {wait} for you."),
    "waiting_you.listening": ("你交了，agent 就接着做。", "Once you send your notes, the agent carries on by itself."),
    "waiting_you.alone": ("交了以后，要跟 agent 说一声。", "After you send your notes, tell the agent."),
    "waiting_you.short": ("{s} · 等你看", "{s} · for you"),
    "notes_unheard": ("你的意见存好了，还没有 agent 来取。", "Your notes are saved; no agent has picked them up yet."),
    "notes_unheard.more": ("跟 agent 说一声，它就来取。", "Tell the agent and it will fetch them."),
    "notes_unheard.short": ("意见还没人取", "notes not picked up yet"),
    "notes_sent": ("你的意见交出去了，等着的 agent 正在取。", "Your notes went to the agent that was waiting; it is picking them up."),
    "notes_sent.short": ("意见交出去了", "notes sent"),
    "notes_taken": ("agent 拿到了你的意见，正在改。", "The agent has your notes and is working on them."),
    "notes_taken.short": ("在照你的意见改", "working on your notes"),
    "now_doing": ("正在{x}。", "{X}."),
    "running": ("正在{x}。", "{X}."), "running.short": ("正在{x}", "{x}"),
    "working": ("agent 正在做。", "The agent is working."), "working.more": ("在 Studio 的对话里。", "In the Studio conversation."),
    "working.short": ("agent 在做", "the agent is working"),
    "delivered": ("已交付{d}。", "Delivered{d}."), "delivered.short": ("已交付{d}", "delivered{d}"),
    "delivered.film": ("成片：{f}", "The film: {f}"), "delivered.gone": ("（不在这台电脑上了）", " (no longer on this computer)"),
    "delivered.subs": ("字幕：{f}", "subtitles: {f}"), "delivered.version": ("交付的是 {v}", "version {v}"),
    "no_record": ("这支片子没有审阅记录。", "This film keeps no review record."),
    "no_record.more": ("它做在有审阅记录之前，看不出停在哪一站。", "It was made before the templates had one, so where it stopped cannot be told."),
    "no_record.short": ("没有审阅记录", "no review record"),
    "stopped": ("agent 停下了：{x}。", "The agent stopped: {x}."), "stopped.short": ("停下了", "stopped"),
    "stopped.cmd": ("{x}没做完", "{x} did not finish"), "stopped.quiet": ("读过你的意见以后没有动静", "nothing since it read your notes"),
    "stopped.cancelled": ("对话被停下了", "the conversation was stopped"), "stopped.error": ("对话出错停了", "the conversation ended with an error"),
    "stopped.cut": ("对话做到一半断了", "the conversation was cut off"),
    "talk.cancelled": ("Studio 里的对话被停下了", "the Studio conversation was stopped"),
    "talk.error": ("Studio 里的对话出错停了", "the Studio conversation ended with an error"),
    "talk.cut": ("Studio 里的对话做到一半断了", "the Studio conversation was cut off mid-turn"),
    "quiet": ("它在 {a}前读了你的意见，之后没有动静", "it read your notes {a} ago and nothing has happened since"),
    "ship_missing": ("还没交付：{x}。", "Not delivered yet: {x}."), "ship_missing.short": ("还没交付", "not delivered yet"),
    "gap.cut": ("初版还没定", "the first cut is not decided yet"), "gap.check": ("成片没过检查", "the film has not passed its check"),
    "gap.final": ("正式版还没做好或还没检查", "the final is not made or not checked yet"),
    "setup": ("引擎还没装好。", "The engine is not set up yet."),
    "setup.more": ("agent 接着做时会先装它（要联网）。", "The agent sets it up first when it carries on (it needs the network)."),
    "setup.short": ("引擎还没装好", "engine not set up"),
    "idle": ("轮到 agent 了，现在没有 agent 在做。", "It is the agent's turn; no agent is working on it now."), "idle.short": ("轮到 agent", "the agent's turn"),
    "unknown": ("读不出这支片子现在到哪了。", "Where this film stands could not be worked out."), "unknown.short": ("读不出", "unreadable"),
    # the facts in the line under a sentence
    "read_at": ("你 {t} 交的意见它读过了。", "It has read your notes of {t}."),
    "made": ("已经做好：{f}。", "Made so far: {f}."),
    "next": ("下一步是{s}。", "Next: {s}."), "next.notes": ("下一步：照你的意见改{s}。", "Next: {s}, changed as your notes say."),
    "ago.min": ("{n} 分钟", "{n} min"), "ago.hour": ("{n} 小时", "{n} hour"), "ago.hours": ("{n} 小时", "{n} hours"), "ago.days": ("{n} 天", "{n} days"),
    # the buttons, and the words a tell button sends
    "act.look": ("去看{s}", "Look at {s}"), "act.revision": ("去复审", "Review the change"), "act.ship": ("打开交付", "Open the delivery"),
    "act.go_cut": ("去看初版", "Go to the first cut"), "act.go_ship": ("去看交付", "Go to the delivery"),
    "act.carry": ("让 agent 接着做", "Ask the agent to carry on"), "act.fetch": ("叫 agent 来看意见", "Tell the agent to read them"),
    "say.carry": ("接着做这支片子。先跑 bin/vh status 看下一步。", "Carry on with this film. Run bin/vh status first for the next step."),
    "say.stopped": ("接着做这支片子。上次{x}。先跑 bin/vh status 看下一步。", "Carry on with this film. Last time {x}. Run bin/vh status first for the next step."),
    "say.stopped_kept": ("接着做这支片子。上次{x}。先跑 bin/vh status 看下一步，留下的能接着用就接着用。",
                         "Carry on with this film. Last time {x}. Run bin/vh status first for the next step, and reuse what was kept."),
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
}
MOD = {"1": "idea", "E0": "idea", "E1": "outline", "2": "board", "E2": "sound", "E3": "sound", "3": "cut", "E4": "cut", "E5": "cut", "deliver": "ship"}   # core.js's GATE_MOD


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
    k = f"cmd.{r.get('cmd')}"
    return [w(k, i) for i in range(3)] if k in WORDS else [w("cmd.other", i, c=r.get("cmd")) for i in range(3)]


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


def broke(r):
    """A run that did not finish: [zh, en] ("渲染到 340 / 900 帧时中断了（进程没了）", "the render was cut off at 340 of 900 frames (its process is gone)")."""
    c, p = cmd_words(r), progress(r)
    how = "broke.stopped" if r.get("cancelled") or r.get("exit") in (130, 143) else "broke.gone" if r.get("state") == "gone" else "broke.failed"
    things = (c[0], c[2])
    if how == "broke.gone" and p:
        return [w("broke.gone_at", i, x=things[i], p=p[i]) for i in (0, 1)]
    return [w("broke.at", i, x=things[i], p=p[i], how=w(how, i)) if p else w("broke.plain", i, x=things[i], how=w(how, i)) for i in (0, 1)]


def kept(k):
    """[zh, en] of what an interrupted run kept to carry on from, from its numbers only (a tool's own text stays out)."""
    if isinstance(k, dict):
        for key in ("chunks", "lines", "frames"):
            n = k.get(key)
            if isinstance(n, int) and not isinstance(n, bool) and n > 0:
                return [w(f"kept.{key}", i, n=n) for i in (0, 1)]
    return None


def ago(secs):
    m = int(secs // 60)
    if m < 60:
        return [w("ago.min", i, n=max(m, 1)) for i in (0, 1)]
    if m < 48 * 60:
        return [w("ago.hour" if m < 120 else "ago.hours", i, n=m // 60) for i in (0, 1)]
    return [w("ago.days", i, n=m // 1440) for i in (0, 1)]


def clock(t, now):
    """21:14 today, else 11-18 21:14."""
    a, b = time.localtime(t), time.localtime(now)
    return time.strftime("%H:%M" if a[:3] == b[:3] else "%m-%d %H:%M", a)


def conversation(project):
    """The newest Studio conversation on this film: {ended: end_turn | cancelled | error | cut | None, t} of its last turn, or
    None. cut: a turn began and never ended (the console went away mid-turn)."""
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
    last = None
    for ln in lines:
        try:
            e = json.loads(ln)
        except ValueError:
            continue
        if isinstance(e, dict) and e.get("type") == "turn":
            last = e
    if last is None:
        return {"ended": None, "t": None}
    if last.get("state") == "start":
        return {"ended": "cut", "t": last.get("t")}
    stop = "error" if last.get("error") else str(last.get("stop") or "end_turn")
    return {"ended": "cancelled" if stop == "cancelled" else "error" if stop in ("error", "refusal") else "end_turn", "t": last.get("t")}


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
    """An agent waits for this film's submission now (bin/vh desk wait, gate --wait): its flag, and its process alive."""
    try:
        _desk()
        import feedback as F
        return bool(F.listening(project).get("listening"))
    except Exception:
        return False


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


def say(code, who, s, more=None, short=None, act=None, paths=(), **facts):
    """s, short: {zh, en}; more: a list of {zh, en} (None skipped), joined into the line under the sentence."""
    parts = [m for m in more or [] if m]
    line = two("".join(m["zh"] for m in parts), " ".join(m["en"] for m in parts)) if parts else None
    return {"code": code, "who": who, "say": s, "more": line, "short": short or both(code + ".short"), "act": act or {"kind": "none"},
            "facts": dict(facts, paths=[p for p in dict.fromkeys(paths) if p])}


def act_open(mod, label, sub=None):
    return {"kind": "open", "mod": mod, "sub": sub, "label": label}


def act_tell(label, text):
    return {"kind": "tell", "label": label, "text": text}


def of(project, o, now=None):
    """The record's `now` (see the module's doc). o: bin/vh status's record of this project."""
    now = time.time() if now is None else now
    project = Path(project)
    st = o.get("stations") or []
    act = o.get("activity") or {}
    working, recent = act.get("running") or [], act.get("recent") or []
    listening = listener(project)   # the flag and a live process: "it carries on by itself" is a promise
    turn = console_turn(project)
    talk = conversation(project)
    busy = bool(working) or turn   # something works on this film now: a command, or a Studio conversation's turn
    nxt = next((s for s in st if s["state"] in ("waiting_agent", "in_progress")), None)

    def seen(s):
        return both(f"seen.{s['id']}") if f"seen.{s['id']}" in WORDS else two(s["name"], s["name"])
    fb = (nxt or {}).get("feedback") or {}
    later = None
    if nxt:
        n, k = seen(nxt), "next.notes" if nxt["state"] == "waiting_agent" and fb.get("submitted") else "next"
        later = two(w(k, 0, s=n["zh"]), w(k, 1, s=n["en"]))
    carry = act_tell(both("act.carry"), both("say.carry"))

    if o.get("paused"):
        return say("paused", "person", both("paused"), act=act_tell(both("act.carry"), both("say.resume")))
    revs = [r for r in (o.get("review") or {}).get("revisions") or [] if r.get("state") == "pending" and r.get("available")]
    if revs:
        return say("revision_ready", "person", both("revision_ready"), [both("revision_ready.more")],
                   act=act_open("cut", both("act.revision"), "revisions"), revisions=len(revs))
    wait = next((s for s in st if s["state"] == "waiting_person"), None)
    if wait:
        n = seen(wait)
        many = n["en"].endswith("cards")
        return say("waiting_you", "person", two(w("waiting_you", 0, s=n["zh"]), w("waiting_you", 1, S=cap(n["en"]), be="are" if many else "is", wait="wait" if many else "waits")),
                   [both("waiting_you.listening" if listening else "waiting_you.alone")],
                   two(w("waiting_you.short", 0, s=n["zh"]), w("waiting_you.short", 1, s=n["en"])),
                   act_open(MOD.get(wait["id"], "cut"), two(w("act.look", 0, s=n["zh"]), w("act.look", 1, s=n["en"]))),
                   stop=wait["id"], listening=listening)
    took = None   # when an agent was handed the person's last submission for this stop
    if fb.get("handed") and not fb.get("pending"):
        try:
            took = (project / "out" / "review" / "feedback" / ".consumed").stat().st_mtime
        except OSError:
            took = None
    if fb.get("pending") and not busy:
        if listening:   # a live listener takes it within the second
            return say("notes_sent", "agent", both("notes_sent"), stop=nxt["id"])
        return say("notes_unheard", "person", both("notes_unheard"), [both("notes_unheard.more")],
                   act=act_tell(both("act.fetch"), both("say.fetch")), stop=nxt["id"], pending=fb["pending"])
    if fb.get("handed") and busy:   # an agent has the submission, and something works on this film now
        x = doing(working[0]) if working else None
        return say("notes_taken", "agent", both("notes_taken"), [two(w("now_doing", 0, x=x[0]), w("now_doing", 1, X=cap(x[1]))) if x else both("working.more")])
    if working:
        x = doing(working[0])
        return say("running", "agent", two(w("running", 0, x=x[0]), w("running", 1, X=cap(x[1]))),
                   short=two(w("running.short", 0, x=x[0]), w("running.short", 1, x=x[1])), cmd=working[0].get("cmd"))
    if turn:
        return say("working", "agent", both("working"), [both("working.more")])
    deliver = next((s for s in st if s["id"] == "deliver"), None)
    if deliver and deliver["state"] == "done":
        d = deliver.get("delivered") or {}
        films = [x["output"] for x in o.get("deliveries") or []][-1:] or d.get("films") or [f for f in [(o.get("media") or {}).get("film")] if f]
        film = films[0] if films else None
        vers = o.get("versions") or {}
        vid = next((v for f, v in (vers.get("current") or {}).items() if film and (f == film or Path(f).stem in film)), None)
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
        return say("delivered", "nobody", two(w("delivered", 0, d=f"（{day}）" if day else ""), w("delivered", 1, d=dd)), [line],
                   two(w("delivered.short", 0, d=dd), w("delivered.short", 1, d=dd)), act_open("ship", both("act.ship")),
                   paths=([film] if film and not gone else []) + subs, film=film, subtitles=subs, version=vid)
    if any(s["state"] == "no_record" for s in st):
        return say("no_record", "unknown", both("no_record"), [both("no_record.more")])
    # the agent's turn, and nothing works on it now: what stopped, what is made, the next stop, and the one action that carries on
    do = (o.get("next_step") or {}).get("do") or ""
    made = (o.get("media") or {}).get("film") or next((r["path"] for r in o.get("renders") or []), None)
    has = both("made", f=made) if made else None
    read = two(w("read_at", 0, t=clock(took, now)), w("read_at", 1, t=clock(took, now))) if took else None
    # the last command that ended, not counting the desk and a wait for the person (their ending stops no work); one older
    # than the Studio conversation's last turn, which ended as it should, was seen by that turn
    ends = [r for r in recent if r.get("cmd") != "desk" and not (r.get("cmd") == "gate" and "--wait" in (r.get("args") or []))]
    last = ends[-1] if ends else None
    if last and talk and talk.get("t") and talk.get("ended") == "end_turn" and (last.get("end") or last.get("start") or 0) < talk["t"]:
        last = None
    why = None   # (the short reason [zh, en], the long one [zh, en], whether something was kept, the command)
    if last and (last.get("state") in ("gone", "failed") or last.get("cancelled")):
        c, b, k = cmd_words(last), broke(last), kept(last.get("kept"))
        why = ([w("stopped.cmd", 0, x=c[0]), w("stopped.cmd", 1, x=c[2])], [w("with_kept", i, x=b[i], k=k[i]) for i in (0, 1)] if k else b, bool(k), last.get("cmd"))
    elif took and now - took >= QUIET:
        a = ago(now - took)
        why = ([w("stopped.quiet", 0), w("stopped.quiet", 1)], [w("quiet", 0, a=a[0]), w("quiet", 1, a=a[1])], False, None)
        read = None   # said in the reason
    elif talk and talk.get("ended") in ("cancelled", "error", "cut"):
        e = talk["ended"]
        why = ([w(f"stopped.{e}", 0), w(f"stopped.{e}", 1)], [w(f"talk.{e}", 0), w(f"talk.{e}", 1)], False, None)
    if why:
        key = "say.stopped_kept" if why[2] else "say.stopped"
        return say("stopped", "person", two(w("stopped", 0, x=why[0][0]), w("stopped", 1, x=why[0][1])),
                   [two(why[1][0] + "。", cap(why[1][1]) + "."), read, has, later],
                   act=act_tell(both("act.carry"), two(w(key, 0, x=why[1][0]), w(key, 1, x=why[1][1]))), paths=[made], last=why[3])
    if nxt is not None and nxt["id"] == "deliver" and nxt["state"] == "in_progress":
        chk = o.get("check") or {}
        g = "cut" if "not decided" in ((deliver or {}).get("note") or "") else "check" if chk.get("verdict") == "fail" and not chk.get("stale") else "final"
        return say("ship_missing", "agent", two(w("ship_missing", 0, x=w(f"gap.{g}", 0)), w("ship_missing", 1, x=w(f"gap.{g}", 1))), [has],
                   act=act_open("cut", both("act.go_cut")) if g == "cut" else act_open("ship", both("act.go_ship"), "check"), paths=[made])
    if do.startswith("the engine's scaffold is not there") or "the engine is not installed yet" in do:
        return say("setup", "agent", both("setup"), [both("setup.more"), read], act=carry)
    return say("idle", "agent", both("idle"), [read, later, has], act=carry, paths=[made])


def plan_line(o):
    """{zh, en}: what the film is planned to be and where it stops for the person, from the BRIEF's lines and the film's own
    stops (bin/vh status's stops.gates, never the effort level); None when the project says nothing of it yet. A line still
    the template's ({…}) says nothing."""
    spec = (o.get("project") or {}).get("spec") or {}
    out = spec.get("Output") or ""
    parts, size = [], ["", ""]
    m = re.search(r"(?<![{\d])(\d+)(?:\s*[–-]\s*(\d+))?\s*s\b", out)
    if m:
        a, b = int(m.group(1)), int(m.group(2)) if m.group(2) else None
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
    m = re.search(r"narration:\s*([^{<|]+)", spec.get("Language") or "")
    v = m.group(1).strip().lower() if m else ""
    if v:
        k = "plan.silent" if v in ("none", "无", "no", "没有") else "plan.song" if "song" in v or "歌" in v else "plan.narrated"
        parts.append([w(k, 0), w(k, 1)])
    gates = set((o.get("stops") or {}).get("gates") or [])
    if not gates:
        parts.append([w("plan.none", 0), w("plan.none", 1)])
    elif gates >= {"1", "2", "3"}:
        parts.append([w("plan.123", 0), w("plan.123", 1)])
    elif gates >= {"1", "3"}:
        parts.append([w("plan.13", 0), w("plan.13", 1)])
    else:
        g = sorted(gates)
        parts.append([w("plan.at", i, x=w("plan.list", i).join(w(f"seen.{x}", i) if f"seen.{x}" in WORDS else x for x in g)) for i in (0, 1)])
    if not parts:
        return None
    return two(w("plan.sep", 0).join(p[0] for p in parts), cap(w("plan.sep", 1).join(p[1] for p in parts)))
