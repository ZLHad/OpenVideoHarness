"""bin/vh gate: one stop, one command. Check the gate data, build the review page, make it this round, open the review
desk when this stop is reviewed there, print the chat message; with --wait, wait for the person's submission.
At gate ① the message also says where this film stops (tools/gatecheck.py's plan_of), so one sentence from the person adds
or takes away a stop. Gate ③'s page is not sent while gate ②, when the film's plan has it, has nothing on record.

usage: bin/vh gate <project> [<n>] [--desk | --page | --chat] [--wait] [--timeout s] [--port N] [--print-address] [--json]
       bin/vh gate <project> <n> --init [--json]
  <n>       1 | 2 | 3 | E0–E5 | 2b … : out/review/gate-<n>.json (playbook/01-pipeline.md, 审阅页, has every field); left out:
            this round, as bin/vh review takes it
  where the person reviews: --desk, --page or --chat when the person asked in chat; else the 审阅方式 line in LOCAL.md
            (对话 | 审阅页 | 审阅台; chat | page | desk); else the effort's default: studio the review desk; standard the
            review desk while Studio is open on this machine (it is looked for, never started: a running console that can take
            this film; else, or when it cannot take it, the static page), the static page otherwise; quick the static page.
            Every channel gets the static page (out/review/gate-<n>.html, also index.html) and the chat
            message; the desk channel also gets the desk: Studio (bin/vh studio) when it is running and has this project,
            else this project's desk, started in the background on 127.0.0.1 when it is not serving yet (it stops by itself
            after 12 h without a request). The desk shows its window at this stop itself, and the message says it is open
            there (nothing secret in it); when the window did not open, the message says so and what to run
  --print-address   the desk channel, for a browser on another machine: show nothing; write an address that opens one
            page, once, within ten minutes, to your terminal alone (the message says only where it is). Refused with no
            terminal (an agent's shell has none) and while this film's desk runs (bin/vh desk link --print-address)
  --wait    the desk channel: then wait like bin/vh desk wait (exit 0 only when a submission was received, and it is
            printed; 3 after --timeout, default 43200 s (12 h); 4 when the agent it waits for is gone; 6 when the desk it
            waits on closed; 7 when another page went out before anything came for this one: run bin/vh status and wait on
            the round open now). Notes nobody has taken yet, of any round, are printed first. Hosts with background wakeup can run this in the background: the message is printed first. A standard
            film's stop that went out as the static page by default (Studio not open): the page goes out as usual, exit 5:
            nothing was answered; end the turn and wait for the person's reply in the chat
  --init    write out/review/gate-<n>.json as a skeleton for this stop, in the BRIEF's review language, and stop: every text
            to write is a {填：…} ({fill in: …}), and bin/vh gate refuses the file (exit 2) until none is left, so an unfilled page
            never reaches the person. It carries "version": 1. A file already there is not overwritten (exit 2)
  --json    the record on stdout, the lines a person reads on stderr: {"version": 1, "tool", "project", "gate", "page", "channel", "url",
            "message": the chat message} (--init: {"version": 1, "tool", "project", "gate", "init": true, "path"}); a failure in
            the error's shape (tools/jsonerr.py). Not with --wait, whose answer is the submission
The page and the desk read the same out/review/gate-<n>.json: it is the one file a client renders for a stop. A page that goes out is also
a snapshot of the project's text (bin/vh history); a failure to save it never stops the page.
Exit: 0 the stop is out (with --wait: only when a submission was received, and it is printed) · 1 the page was written but breaks a rule: no message,
no desk, and bin/vh status counts it as not sent until a run of it goes through (bin/vh review's 1) · 2 nothing to send: no project, no or bad gate JSON, placeholders left, the desk did not start,
--wait without the desk, --init over a file, gate ③'s page while gate ① is not on record (standard, studio), or gate ② (in the plan, a BRIEF with a
Stops line: REVIEW.md lacks the person's words and "定了：…" for it, or the user's own words waiving it) · 3 --wait timed out ·
4 --wait: the agent it waited for is gone · 5 --wait, and a standard film's stop went out as the static page by default
(Studio not open): the page goes out as usual; nothing was answered; end the turn and wait for the person's reply in the chat
(stdout is the message to pass on, as without --wait) · 6 --wait: the desk it waited on closed · 7 --wait: another page went out
before anything came for this one: run bin/vh status, and wait on the round open now.
"""
import argparse, contextlib, json, os, re, sys
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "desk"))
import activity, jsonerr, review   # noqa: E402,E401
import gatecheck   # noqa: E402
from gatecheck import effort_of, local_md, stop_of   # noqa: E402

IDLE = 12 * 3600   # a desk gate starts stops by itself after this long without a request
CHANNEL = {"对话": "chat", "审阅页": "page", "审阅台": "desk", "chat": "chat", "page": "page", "desk": "desk"}
SAY = {"zh": {"desk_wait": "{s}在 Studio 里打开了：选好，写下意见，点“交给 agent”。我在等，你一交我就接着做。",
              "desk": "{s}在 Studio 里打开了：选好，写下意见，点“交给 agent”，然后回到这里跟我说一声“我交了”。",
              "tab": "（这台电脑上没有 Chrome、Edge 这类浏览器，所以它开在了浏览器的一个标签页里。）",
              "closed": "Studio 的窗口这次没能打开（{why}）。跟我说一声“打开 Studio”，我再试一次；页面在 {page}。",
              "no_browser": "这台电脑上找不到 Chrome、Edge 这类浏览器，浏览器的标签页也没有连上", "no_connect": "窗口开了，但里面的页面没有连上",
              "printed": "Studio 的地址（另一台电脑上的浏览器用）写在了运行这条命令的终端里：十分钟内能打开一页、只能打开一次，谁先打开谁就能在里面操作，别转给别人。"},
       "en": {"desk_wait": "{s} {be} open in Studio: pick, add your notes, press “Send to agent”. I'm waiting, and carry on as soon as you send it.",
              "desk": "{s} {be} open in Studio: pick, add your notes, press “Send to agent”, then tell me here: “I've sent it”.",
              "tab": "(No Chrome, Edge or the like on this computer, so it opened in a tab of your browser.)",
              "closed": "Studio's window did not open this time ({why}). Say \"open Studio\" and I will try again; the page is {page}.",
              "no_browser": "no Chrome, Edge or the like on this computer, and no browser tab connected", "no_connect": "the window opened, but its page did not connect",
              "printed": "Studio's address (for a browser on another computer) is in the terminal this ran in: it opens one page, once, within ten minutes; whoever opens it first can work in it, so keep it to yourself."}}

CHECKPOINT_WHAT = {  # what a checkpoint puts in front of the person (playbook/01-pipeline.md, 导演模式)
    "E0": ("设定图、主旋律试听或 look-dev 变体", "the design sheet, the theme to listen to, or the look-dev variants"),
    "E1": ("两种音色的试听、旁白稿或钩子画面", "two voices to listen to, the script, or the hook's frames"),
    "E2": ("一张 cue 表：主旋律在哪几段、哪里留白、音效多密", "a cue sheet: where the theme comes in, where it is silent, how dense the effects are"),
    "E3": ("最终的配音和配乐，听一遍再锁时", "the final voice and score, heard once before the timing locks"),
    "E4": ("第一章的联系表和 10–20 s 片段", "the first chapter's contact sheet and a 10–20 s clip"),
    "E5": ("锁画面：bin/vh qa 的结果和请听的几处", "the picture lock: bin/vh qa's result and the places to listen to")}


PACKAGED = ("02",)   # the types whose concept cards carry 2 titles and a cover layout (video-types/02, playbook/10 §1)


def type_of(project):
    """The project's type number ("02"), as its BRIEF names its type doc or bin/vh new marked it; None when it says none."""
    try:
        s = (Path(project) / "BRIEF.md").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"video-types/(\d\d)-[\w-]+\.md", s) or re.search(r"<!-- from (\d\d)-[\w-]+\.md -->", s)
    return m.group(1) if m else None


def skeleton(gate, lang, plan=None, kind=None):
    """A gate JSON to fill in, for this stop. Each {填：…} says what goes there; bin/vh gate takes it once none is left.
    plan: the film's stops (gatecheck.plan_of); with no gate ② in it, gate ③'s page carries the storyboard.
    kind: the project's type number (type_of); a type in PACKAGED gets each concept card's titles and cover."""
    zh = lang != "en"

    def f(a, b):
        return f"{{填：{a}}}" if zh else f"{{fill in: {b}}}"   # a shape no stylesheet can write (.bar {fill: #e33} is a page's own text)

    def card(k):
        c = {"id": k, "label": f(f"立意卡 {k}：核心想法，不超过 20 个字", f"concept card {k}: the idea, in at most 50 characters"),
             "frame": f(f"立意卡 {k} 那一帧画面的路径（卡上就放这一帧）", f"the path of card {k}'s frame (the card shows it)"),
             "pro": f("推出的画面、钩子、首尾，各一句一行（JSON 里用 \\n 换行）",
                      "the picture, the hook and the ending it leads to, a sentence a line (\\n in the JSON)"),
             "con": f("风险或代价，一句", "its risk or cost, in a sentence")}
        if kind in PACKAGED:   # what goes out with the film: two draft titles and a cover layout a card (playbook/10 §5, §6)
            c["titles"] = [f(f"立意卡 {k} 的标题 {n}（数字和断言在 NOTES.md 有出处）", f"card {k}'s title {n} (its numbers and claims sourced in NOTES.md)") for n in (1, 2)]
            c["cover"] = f(f"立意卡 {k} 的封面版式：playbook/10 第 6 节的 C1–C5 之一，加主文案", f"card {k}'s cover layout: one of playbook/10 §6's C1–C5, and its main words")
        return c
    d = {"version": 1, "summary": f("这页要人定什么、看完要多久，不超过 40 个字：人第一眼读的就是这句",
                                    "what this page asks the person and how long it takes, in at most 100 characters: the first thing they read")}
    stop = stop_of(gate)
    if stop == "1":
        d["decisions"] = [{"id": "concept", "question": f("选哪张立意卡？写成这支片子自己的问题，一行", "which concept card? In this film's own words, one line"),
                           # two cards to start from: as many as really differ, each with its frame (add a C, or keep to two)
                           "options": [card("A"), card("B")], "recommend": f("A 或 B", "A or B"),
                           "columns": ["这张卡讲什么", "风险或代价"] if zh else ["what the card is", "its risk or cost"],
                           "why": f("推荐它的一句理由", "why, in one line"), "cost": "现在改：低 · 分镜后改：很高" if zh else "now: low · after the storyboard: very high"}]
        d["delegated"] = [f("替人定了的事，一项一条：规格（画幅、分辨率、帧率、时长、在哪看）、引擎、费用",
                            "what you decided for the person, one an item: the spec (frame, resolution, rate, length, where it is watched), the engine, the cost")]
        d["appendix"] = [{"title": "大纲" if zh else "Outline", "text": f("按推荐立意写的大纲，这支片子有几段写几段，竖线表：段落、时间、看完知道什么", "the outline for the recommended concept, as many segments as this film has, a pipe table: segment, time, what the viewer knows after it")},
                         {"title": "BRIEF", "path": "BRIEF.md"}]
    elif stop == "2":
        d["include"] = "out/check/storyboard/review.json"   # bin/vh storyboard writes it: segments, key frames, least-sure shots, animatic
        d["decisions"] = []
        d["assets"] = [{"path": "out/check/rhythm.png", "caption": f("节奏图上要人看的地方（bin/vh rhythm 出图）", "what the rhythm chart shows (bin/vh rhythm draws it)")},
                       {"path": f("前 5 s 连帧的路径（bin/vh frames <项目> --strip 0:5 --fps 6 的拼图，在 out/frames/；还没有页面就放开头几个时刻的关键帧）",
                                  "the path of the first 5 s as a strip (bin/vh frames <project> --strip 0:5 --fps 6 puts one picture in out/frames/; no page yet: key frames of the first moments)"),
                        "caption": f("开头这几秒发生了什么", "what happens in these seconds")},
                       {"path": f("每一帧都在的东西（进度条、字幕样式、字体）实拍样子的路径", "the path of what is on screen in every frame (progress bar, captions, type), as it will really look"),
                        "caption": f("这些后改一次就是整片重渲，这一关定", "changed later, these mean rendering the whole film again: settled here")}]
    elif stop == "3":
        d["decisions"] = [{"id": "draft", "question": f("这版初稿放行吗？写清差什么", "does this draft pass? Say what is missing"),
                           "options": [{"id": "OK", "label": "放行，出正式画质" if zh else "It passes: render the final",
                                        "pro": f("好处", "what it gains"), "con": f("代价", "what it costs")},
                                       {"id": "FIX", "label": "改完下面几处再看" if zh else "Fix the places below, then look again",
                                        "pro": f("好处", "what it gains"), "con": f("代价", "what it costs")}],
                           "recommend": f("OK 或 FIX", "OK or FIX"), "why": f("一句理由", "why, in one line"),
                           "cost": "现在改：中 · 锁画面后改：高" if zh else "now: medium · after the picture lock: high"}]
        d["assets"] = [{"path": f("初版成片的路径，例如 out/draft.mp4", "the draft's path, e.g. out/draft.mp4"), "caption": f("初版：多长、什么画质", "the draft: its length and quality"), "for": "draft"},
                       {"path": f("联系表的路径（bin/vh sheet 出图）", "the contact sheet's path (bin/vh sheet draws it)"), "caption": f("整片的形状", "the whole film at a glance"), "for": "draft"}]
        d["least_sure"] = [{"id": f("镜头号（S04）或片子里的时间（12.4 s、0–5 s）：有时间的落在标尺上", "a shot id (S04) or a time in the film (12.4 s, 0–5 s): a time lands on the ruler"),
                            "note": f("自己最不满意的一处和默认的修法，一句；有几处写几处", "a place you like least and the fix it gets by default, a sentence; as many entries as there are such places")}]
        d["appendix"] = [{"title": "评审打的分" if zh else "The reviewer's scores", "text": f("8 项分数和没修好的几处", "the 8 scores and what is still not fixed")}]
        if plan and not plan["quick"] and "2" not in plan["gates"]:   # no storyboard stop: the storyboard is shown here, each shot passed unless the person says otherwise
            d["include"] = "out/check/storyboard/review.json"   # bin/vh storyboard writes it, from the draft's own frames
    else:
        what = CHECKPOINT_WHAT.get(stop, ("这一站要人看的东西", "what this stop puts in front of the person"))[0 if zh else 1]
        d["decisions"] = [{"id": "pick", "question": f(f"要人定什么（{what}）", f"what the person decides ({what})"),
                           "options": [{"id": k, "label": f(f"选项 {k}", f"option {k}"), "pro": f("好处", "what it gains"), "con": f("代价", "what it costs")} for k in "AB"],
                           "recommend": f("A 或 B", "A or B"), "why": f("一句理由", "why, in one line"),
                           "cost": f("现在改和以后改各要花多少", "what a change costs now, and later")}]
        d["assets"] = [{"path": f("给人看或听的文件的路径", "the path of what the person sees or hears"), "caption": f("一行说明", "one line about it"), "for": "pick"}]
    return d


def init_page(project, gate_arg, shown, as_json=False):
    """bin/vh gate <project> <n> --init: the skeleton, written once. → the exit status."""
    g = re.sub(r"\.json$", "", re.sub(r"^gate-", "", (gate_arg or "").strip()))
    if not review.GATE_ID.fullmatch(g):
        return jsonerr.fail("usage", f"gate: --init needs the stop it is for: bin/vh gate {shown} 1 --init (1, 2, 3, E0–E5, 2b …)")
    path = project / "out" / "review" / f"gate-{g}.json"
    lang = review.review_lang(project) or "zh"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "x", encoding="utf-8") as out:   # "x": never over a page someone wrote
            out.write(json.dumps(skeleton(g, lang, gatecheck.plan_of(project), type_of(project)), ensure_ascii=False, indent=2) + "\n")
    except FileExistsError:
        return jsonerr.fail("exists", f"gate: {path} is already there, and --init does not overwrite: edit it, then bin/vh gate {shown} {g}")
    except OSError as e:
        return jsonerr.fail("failed", f"gate: can't write {path}: {e.strerror or e}")
    say = sys.stderr if as_json else sys.stdout
    print(f"✓ {path}: a skeleton for {review.gate_title(g, lang)}", file=say)
    if effort_of(project)[0] == "quick":
        print("  a quick project has no gates: this page is for a stop the person asked for", file=say)
    elif stop_of(g) == "2" and "2" not in gatecheck.plan_of(project)["gates"]:
        print("  gate ② is not in this film's plan (bin/vh status says why): a page for it makes it a stop, which adding always may", file=say)
    elif stop_of(g) == "3" and "2" not in gatecheck.plan_of(project)["gates"]:
        print("  this film has no storyboard stop, so this page includes the storyboard: bin/vh storyboard writes out/check/storyboard/review.json", file=say)
    print(f"  replace every {'{fill in: …}' if lang == 'en' else '{填：…}'}, delete what this page does not need; until none is left, bin/vh gate refuses the file", file=say)
    print("  keep it short: summary at most 40 CJK characters (100 letters), a question one line, a label 20 (50), pro, con and each "
          "least-sure note a sentence; reasons go into why, details into the appendix", file=say)
    print("  an option's id is what the person types back (\"1 A\"): keep it short (A / B, H1 / H2, OK / FIX), and different "
          "between the page's decisions; the label beside it is what the person reads, so the label carries the meaning", file=say)
    print(f'  the fields: bin/vh know --show "playbook/01-pipeline.md#审阅页"; then: bin/vh gate {shown} {g}', file=say)
    activity.note(f"{review.gate_title(g, 'en')}: a skeleton to fill in", [path])
    if as_json:
        print(json.dumps({"version": 1, "tool": "bin/vh gate", "project": str(project), "gate": g, "init": True, "path": str(path)}, ensure_ascii=False))
    return 0


def gate_seen(stop, lang):
    """What the person sees at a stop, by its own name (tools/standing.py's words: 初版, the first cut)."""
    try:
        import standing
        k = f"seen.{stop}"
        if k in standing.WORDS:
            x = standing.w(k, 0 if lang == "zh" else 1)
            return x if lang == "zh" else x[:1].upper() + x[1:]
    except Exception:
        pass
    return review.gate_title(stop, lang)


STUDIO_OPEN = "and Studio is open"


def page_reason(why):
    """Why a standard film's stop went out as the page, in the words of where it came from (never a reason that is not it)."""
    if "could not take" in why:
        return "Studio closed meanwhile" if "closed meanwhile" in why else "Studio could not take this film"
    if os.environ.get("OVH_GATE_STUDIO") == "0":
        return "this run does not look for Studio (OVH_GATE_STUDIO=0)"
    return "Studio is not open"


def desk_since(info):
    """(pid, since) of a running desk's record: since in epoch seconds (an older record: its local "started")."""
    import datetime
    since = info.get("since")
    if not isinstance(since, (int, float)):
        try:
            since = datetime.datetime.fromisoformat(info["started"]).timestamp() if info.get("started") else None
        except (ValueError, TypeError):
            since = None
    return (info.get("pid"), since)


def studio_open():
    """Studio (the console) runs on this machine now: it is used, never started, for a standard film's stop. Its record must
    name a process that is alive and answers on its port (server.running_info), and that started no later than the record
    says (a pid another process took since is not Studio): a record left behind falls back to the static page.
    OVH_GATE_STUDIO=0: do not look (tools/ci.sh sets it: its checks test the page and their own desks, and must never reach
    a Studio they did not start)."""
    if os.environ.get("OVH_GATE_STUDIO") == "0":
        return False
    try:
        import server
        info = server.running_info(None, [])
        return bool(info) and activity._alive(*desk_since(info))
    except Exception:
        return False


def channel_of(project, flag=None):
    """(channel, where it came from): a flag, LOCAL.md's 审阅方式 line, or the effort's default: studio's stops in Studio,
    standard's too while Studio is open on this machine (only then: it is not started for this), else the static page."""
    if flag:
        return flag, f"--{flag}"
    try:
        text = re.sub(r"<!--.*?-->", "", local_md().read_text(encoding="utf-8", errors="replace"), flags=re.S)
        m = re.search(r"^\s*[-*]?\s*(?:\*\*)?(?:审阅方式|review(?:\s+(?:channel|surface|mode))?)(?:\*\*)?\s*[:：]\s*\**\s*(对话|审阅页|审阅台|chat|page|desk)\b",
                      text, re.M | re.I)
        if m:
            return CHANNEL[m.group(1).lower()], "LOCAL.md"
    except OSError:
        pass
    effort, src = effort_of(project)
    if effort == "standard" and studio_open():
        return "desk", f"effort {effort} ({src}), {STUDIO_OPEN}"
    return ("desk" if effort == "studio" else "page"), f"effort {effort} ({src})"


def start_desk(project, gate, port=None, print_address=False, studio_only=False):
    """The desk for this stop, its window shown at this stop's gate view: Studio (the console) when it runs, this project
    joining its space when it is outside Studio's folders; else the desk serving this project, or a new one started in its own session (it outlives this command). The
    window gets its access from the desk itself; nothing secret is in this command's output. print_address: show nothing;
    a fresh desk of this project (main refuses while one runs; Studio is left alone), and its address with a one-time code
    back, which main writes to the terminal alone.
    → (address, how, shown, why): how is studio, running, started or restarted; shown is the desk's answer ({opened, how,
    why}); address None when none came up (why). studio_only: Studio or nothing (a standard film's default: no desk is
    started for it; Studio closed meanwhile, or it cannot take this film → None)."""
    sys.path.insert(0, str(HERE / "desk"))
    import server, launch
    route = f"/gate/{quote(gate, safe='')}"
    if not print_address:
        console = server.running_info(None, [])
        at = launch.place(console["url"], project) if console else None
        if console and not at and server.join(project):   # a film outside Studio's folders joins the Studio that runs
            at = launch.place(console["url"], project)
        if at:
            return console["url"], "studio", launch.show(console["url"], at + route), None
        if studio_only:
            return None, "studio", {"opened": False}, "Studio closed meanwhile" if not console else "it is not one of Studio's films and could not join"
    at = "/p/" + quote(server.keyify(project.name, project), safe="") + route
    info = server.running_info(project)
    if print_address:
        url, why = launch.start(project, (), True, port, IDLE, True)
        return (url + "#" + at if url else None), "started", {"opened": False}, why
    if info:
        url, how = info.get("url"), "running"
    else:
        url, why = launch.start(project, (), True, port, IDLE)
        if not url:
            return None, "started", {"opened": False}, why
        how = "running" if why == "running" else "started"   # another start made it meanwhile
    return url, how, launch.show(url, at), None


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh gate", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project folder, or its name under projects/")
    ap.add_argument("gate", nargs="?", help="1 | 2 | 3 | E0–E5 | 2b …; default: this round")
    how = ap.add_mutually_exclusive_group()
    for c in ("desk", "page", "chat"):
        how.add_argument(f"--{c}", dest="channel", action="store_const", const=c, help=f"review in the {c} this time")
    ap.add_argument("--wait", action="store_true", help="the desk only: then wait for the submission, like bin/vh desk wait")
    ap.add_argument("--timeout", type=float, default=43200, help="with --wait: seconds (default 43200: 12 h)")
    ap.add_argument("--port", type=int, help="the desk's port when it has to start (default: the first free of 8780–8799)")
    ap.add_argument("--print-address", action="store_true", help="the desk only, for a browser on another machine: open none, write an "
                                                                 "address that opens one page to your terminal alone (refused with no terminal, "
                                                                 "and while this film's desk runs)")
    ap.add_argument("--init", action="store_true", help="write out/review/gate-<n>.json as a skeleton to fill in, and stop")
    ap.add_argument("--json", action="store_true", help="the record on stdout, the lines a person reads on stderr")
    a = ap.parse_args(argv)
    project = review.find_project(a.project)
    if not project:
        jsonerr.mark("no_project")
        return 2
    if a.init:
        if a.channel or a.wait:
            return jsonerr.fail("usage", "gate: --init only writes the skeleton: leave --desk, --page, --chat and --wait for the run that sends it")
        return init_page(project, a.gate, a.project, a.json)
    if a.json and a.wait:
        return jsonerr.fail("usage", "gate: --json is for a run that only sends the page; --wait's answer is the submission (bin/vh desk feedback --json has it as JSON)")
    channel, why = channel_of(project, a.channel)
    no_wait = False   # --wait, and a standard film's stop went to the page by default: the page goes out, nothing is waited for (5)
    if a.wait and channel != "desk":
        if a.channel or why == "LOCAL.md" or effort_of(project)[0] != "standard":
            return jsonerr.fail("usage", f"gate: --wait waits for the review desk, and this stop is reviewed on the {channel} ({why}): the person answers in "
                                "the chat. Leave --wait out, or use --desk if they want the desk")
        no_wait = True
    if a.print_address and channel != "desk":
        return jsonerr.fail("usage", f"gate: --print-address is the desk's address, and this stop is reviewed on the {channel} ({why})")
    if a.print_address:   # before the page goes out: the address goes to a person's terminal, and comes with a fresh desk only
        sys.path.insert(0, str(HERE / "desk"))
        import server
        if not server.has_terminal():
            return jsonerr.fail("refused", f"gate: {server.NO_TERMINAL}")
        if server.running_info(project):
            return jsonerr.fail("refused", "gate: this film's review desk is running already, and an address for another computer comes only with a "
                                f"fresh start; this never closes a window that is open. To start it again on purpose (its window closes): bin/vh desk link {a.project} "
                                f"--print-address, then bin/vh gate {a.project} without it")
    asked = stop_of(re.sub(r"\.json$", "", re.sub(r"^gate-", "", (a.gate or review.current_page(project) or "").strip())))
    if asked == "3":   # gate ① before it (standard, studio: as render and check ask it), and gate ② when this film's plan has it (a BRIEF with a Stops line)
        lacking = gatecheck.not_on_record(project, asked)
        if lacking:
            names = " and ".join(review.gate_title(g, "en") for g in lacking)
            plan = gatecheck.plan_of(project)
            why = f" ({'; '.join(c['say'] for c in plan['costly'])})" if "2" in lacking and plan["costly"] else ""
            return jsonerr.fail("refused", f"gate: {names} is in this film's plan{why} and REVIEW.md has no record of it (the person's words and a decision): the page for {review.gate_title(asked, 'en')} is not sent. "
                                f"Put that stop to the person first (bin/vh gate {a.project} {lacking[0]}), then their words (\"- 原话：“…”\") and \"- 定了：…\" under its section; "
                                "only the user's own words take a stop away (\"- 用户授权跳过（YYYY-MM-DD）。原话：“…”\", templates/REVIEW.md)",
                                f"bin/vh status {a.project} shows the plan and each stop's record")
    with contextlib.redirect_stdout(sys.stderr if a.json else sys.stdout):
        rc, page, page_path = review.publish(project, a.gate, a.project)
    if rc:   # bin/vh review said what is wrong; nothing goes to the person
        jsonerr.mark("refused" if rc == 1 else "invalid", f"bin/vh gate {a.project} --init writes a skeleton; bin/vh know --show \"playbook/01-pipeline.md#审阅页\" has the fields" if rc != 1 else None)
        return rc
    lines = [page.chat(page_path)]
    if stop_of(page.gate) == "1" and effort_of(project)[0] != "quick":   # the first stop says where the film stops
        lines.append(gatecheck.plan_words(gatecheck.plan_of(project), page.lang, lambda g: review.gate_name(g, page.lang)))   # the person reads it: names, no codes
    url = None
    if channel == "desk" and why.endswith(STUDIO_OPEN):   # the default of a standard film: Studio only, never a desk started for it
        url, how, shown, why_not = start_desk(project, page.gate, a.port, a.print_address, studio_only=True)
        if not url:
            channel, why = "page", f"effort standard, and Studio could not take this film ({why_not})"
            no_wait = bool(a.wait)
    elif channel == "desk":
        url, how, shown, why_not = start_desk(project, page.gate, a.port, a.print_address)
    if channel == "desk":
        if not url:
            return jsonerr.fail("failed", f"gate: the review desk did not start ({why_not or 'out/review/.desk.log says why'}); the page is {page_path}. "
                                f"Start it by hand: bin/vh studio {a.project}")
        print("✓ review desk (" + {"studio": "Studio, already running", "running": "already serving this project",
                                   "started": "started, in the background"}[how]
              + ("" if a.print_address else f": its window {shown.get('how')}" if shown.get("opened") else f": no window ({shown.get('why')})") + ")", file=sys.stderr)
        if a.print_address:
            sys.path.insert(0, str(HERE / "desk"))
            import server
            if not server.to_terminal(server.address_words(url)):
                return jsonerr.fail("failed", f"gate: the desk started, but its address could not be written to your terminal; the page is {page_path}")
            lines.append(SAY[page.lang]["printed"])
        elif shown.get("opened"):
            n = stop_of(page.gate) or page.gate
            say_s = gate_seen(n, page.lang)
            lines.append(SAY[page.lang]["desk_wait" if a.wait else "desk"].format(s=say_s, be="are" if n in ("1", "E0") else "is"))
            if shown.get("how") == "tab":
                lines.append(SAY[page.lang]["tab"])
        else:
            lines.append(SAY[page.lang]["closed"].format(why=SAY[page.lang].get(shown.get("code") or "", shown.get("why") or "?"), page=page_path))
        url = url.partition("?")[0].partition("#")[0]   # an address that opens nothing by itself
    print(f"  this stop is reviewed on the {channel} ({why})", file=sys.stderr)
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh gate", "project": str(project), "gate": page.gate, "page": str(page_path), "channel": channel, "url": url,
                          "message": "\n".join(lines)}, ensure_ascii=False), flush=True)
    else:
        print("\n".join(lines), flush=True)
    activity.note(f"{review.gate_title(page.gate, 'en')}: {len(page.d['decisions'])} decision(s) on the {channel}" + (f" · {url.partition('?')[0]}" if url else ""), [page_path])   # the log is in the project: never the key
    try:   # the text as it was when the page went out (tools/history.py); a failure to save never stops the page, nor does a lock held elsewhere for long
        import history
        for x in history.save(project, f"gate {page.gate}: the page went out", wait=2)[1]:
            print(f"  history: left out: {x['path']} ({x['why']})", file=sys.stderr)
    except Exception as e:
        print(f"  history: no snapshot of this page ({e})", file=sys.stderr)
    if no_wait:   # (stdout is the message the agent passes on: it stays the page's)
        print(f"  nothing was answered: {page_reason(why)}, so this stop went out as the static page and nothing is waited for here. "
              "End your turn and wait for the person's reply in the chat (exit 5)", file=sys.stderr)
        return 5
    if not a.wait:
        return 0
    import feedback
    jsonerr.mark("timeout")
    watch = None   # the desk the wait is on: when it closes, nothing more can come (6)
    try:
        import server
        info = server.running_info(None, []) if how == "studio" else server.running_info(project)
        watch = desk_since(info) if info else None
    except Exception:
        watch = None
    return feedback.wait(project, a.timeout, desk=watch, round=page.gate)


if __name__ == "__main__":
    sys.exit(activity.exiting(lambda: jsonerr.guard(lambda: main(sys.argv[1:]))))   # bin/vh exec's into this: this process ends the run
