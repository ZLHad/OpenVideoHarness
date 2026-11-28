"""bin/vh gate: validate the stop, build its local review page and print the message for the chat.

usage: bin/vh gate <project> [<n>] [--page | --chat] [--json]
       bin/vh gate <project> <n> --init [--json]
  <n>       1 | 2 | 3 | E0–E5 | 2b …, or the current round when left out.
  --page    review the local HTML page (the default). The person replies in the chat.
  --chat    review in the chat. The same local HTML page is available as a reference.
            LOCAL.md's 审阅方式 (审阅页 | 对话, page | chat) sets the default for this machine.
  --init    write out/review/gate-<n>.json as a skeleton. Existing files are preserved.
  --json    the result on stdout and the human-readable output on stderr.

At gate ① the message also says where the film stops. Gate ③ checks that the planned earlier stops
are on record before sending the page. A page that goes out saves a snapshot via bin/vh history.
Exit 0: published or initialized. Exit 1: page written with errors, so nothing is sent.
Exit 2: missing or invalid data, a refused stop, or incorrect usage.
"""
import argparse, contextlib, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import activity, jsonerr, review   # noqa: E402,E401
import gatecheck   # noqa: E402
from gatecheck import effort_of, local_md, stop_of   # noqa: E402

CHANNEL = {"对话": "chat", "审阅页": "page", "审阅台": "page", "chat": "chat", "page": "page", "desk": "page"}

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
        c = {"id": k, "label": f(f"立意卡 {k} 怎么讲，用这支片子自己的词，不超过 20 个字（「从海边的刻度桩讲起」，不写「方案 A：具象切入」）",
                                f"how card {k} tells it, in this film's own words, at most 50 characters (“Start at the tide post on the shore”, not “Option A: concrete entry”)"),
             "frame": f(f"立意卡 {k} 那一帧画面的路径（卡上就放这一帧）", f"the path of card {k}'s frame (the card shows it)"),
             "pro": f("推出的画面、钩子、首尾，各一句一行（JSON 里用 \\n 换行）；写人看得见的东西（「人人见过涨潮，第一秒就有画面」），不写评语（「代入感强」）",
                      "the picture, the hook and the ending it leads to, a sentence a line (\\n in the JSON); what the person will see, not a verdict"),
             "con": f("风险或代价，一句", "its risk or cost, in a sentence")}
        if kind in PACKAGED:   # what goes out with the film: two draft titles and a cover layout a card (playbook/10 §5, §6)
            c["titles"] = [f(f"立意卡 {k} 的标题 {n}（数字和断言在 NOTES.md 有出处）", f"card {k}'s title {n} (its numbers and claims sourced in NOTES.md)") for n in (1, 2)]
            c["cover"] = f(f"立意卡 {k} 的封面版式：playbook/10 第 6 节的 C1–C5 之一，加主文案", f"card {k}'s cover layout: one of playbook/10 §6's C1–C5, and its main words")
        return c
    d = {"version": 1, "summary": f("这页要人定什么、看完要多久，不超过 40 个字，像跟人说话（「先挑一个讲法，大纲跟着它走，约 2 分钟」）：人第一眼读的就是这句",
                                    "what this page asks the person and how long it takes, in at most 100 characters, said as to a person: the first thing they read")}
    stop = stop_of(gate)
    if stop == "1":
        d["decisions"] = [{"id": "concept", "question": f("像当面问人那样问，一行，用这支片子里的东西说（「开头从海边讲，还是从太空讲？」，不写「请确认立意方向」）",
                                          "ask as you would across a table, one line, in this film's own things (“Start on the shore, or out in space?”)"),
                           # two cards to start from: as many as really differ, each with its frame (add a C, or keep to two)
                           "options": [card("A"), card("B")], "recommend": f("A 或 B", "A or B"),
                           "columns": ["这张卡讲什么", "风险或代价"] if zh else ["what the card is", "its risk or cost"],
                           "why": f("推荐它的一句理由", "why, in one line"), "cost": "现在改：低 · 分镜后改：很高" if zh else "now: low · after the storyboard: very high"}]
        d["delegated"] = [f("替人定了的事，一项一条：规格（画幅、分辨率、帧率、时长、在哪看）、引擎、费用",
                            "what you decided for the person, one an item: the spec (frame, resolution, rate, length, where it is watched), the engine, the cost")]
        d["appendix"] = [{"title": "大纲" if zh else "Outline", "text": f("按推荐立意写的大纲，这支片子有几段写几段，竖线表：段落、时间、看完知道什么；段名说这一段讲了什么（「背面也鼓起来」），不用「开场」「钩子」「原理」这类结构名", "the outline for the recommended concept, as many segments as this film has, a pipe table: segment, time, what the viewer knows after it; name each part by what it says, not Opening or Hook")},
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
                           "options": [{"id": "OK", "label": "可以，出正式版" if zh else "It passes: render the final",
                                        "pro": f("好处", "what it gains"), "con": f("代价", "what it costs")},
                                       {"id": "FIX", "label": "先改下面几处，改完再给你看" if zh else "Fix the places below, then look again",
                                        "pro": f("好处", "what it gains"), "con": f("代价", "what it costs"), "needs_note": True}],   # (the reply needs to say what to fix)
                           "recommend": f("OK 或 FIX", "OK or FIX"), "why": f("一句理由", "why, in one line"),
                           "cost": "现在改：中 · 锁画面后改：高" if zh else "now: medium · after the picture lock: high"}]
        d["assets"] = [{"path": f("初版成片的路径，例如 out/draft.mp4", "the draft's path, e.g. out/draft.mp4"), "caption": f("初版：多长、什么画质", "the draft: its length and quality"), "for": "draft"},
                       {"path": f("联系表的路径（bin/vh sheet 出图）", "the contact sheet's path (bin/vh sheet draws it)"), "caption": f("整片的形状", "the whole film at a glance"), "for": "draft"}]
        d["least_sure"] = [{"id": f("镜头号（S04）或片子里的时间（12.4 s、0–5 s）：有时间的落在标尺上", "a shot id (S04) or a time in the film (12.4 s, 0–5 s): a time lands on the ruler"),
                            "note": f("自己最不满意的一处和默认的修法，一句；有几处写几处。用片子里的时间和画面说是哪儿（「1:23 月亮出来那一下可能太快，默认放慢一半」），不写镜头号和文件名",
                                       "a place you like least and the fix it gets by default, a sentence; as many entries as there are such places. Say where by the film's time and picture, not by shot ids or file names")}]
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
    print("  the words on this page are for a person: ask as you would across a table, name parts by what they say, and keep shot ids, "
          "file names and English states out of what the person reads", file=say)
    print("  an option's id is what the person types back (\"1 A\"): keep it short (A / B, H1 / H2, OK / FIX), and different "
          "between the page's decisions; the label beside it is what the person reads, so the label carries the meaning", file=say)
    print(f'  the fields: bin/vh know --show "playbook/01-pipeline.md#审阅页"; then: bin/vh gate {shown} {g}', file=say)
    activity.note(f"{review.gate_title(g, 'en')}: a skeleton to fill in", [path])
    if as_json:
        print(json.dumps({"version": 1, "tool": "bin/vh gate", "project": str(project), "gate": g, "init": True, "path": str(path)}, ensure_ascii=False))
    return 0


def channel_of(project, flag=None):
    """Use an explicit channel, the local review preference, or the HTML page."""
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
    effort, source = effort_of(project)
    return "page", f"effort {effort} ({source})"


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh gate", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project folder, or its name under projects/")
    ap.add_argument("gate", nargs="?", help="1 | 2 | 3 | E0–E5 | 2b …; default: this round")
    how = ap.add_mutually_exclusive_group()
    for channel in ("page", "chat"):
        how.add_argument(f"--{channel}", dest="channel", action="store_const", const=channel, help=f"review in the {channel} this time")
    ap.add_argument("--init", action="store_true", help="write out/review/gate-<n>.json as a skeleton to fill in, and stop")
    ap.add_argument("--json", action="store_true", help="the record on stdout, the lines a person reads on stderr")
    a = ap.parse_args(argv)
    project = review.find_project(a.project)
    if not project:
        jsonerr.mark("no_project")
        return 2
    if a.init:
        if a.channel:
            return jsonerr.fail("usage", "gate: --init only writes the skeleton: choose --page or --chat when you send it")
        return init_page(project, a.gate, a.project, a.json)
    channel, channel_source = channel_of(project, a.channel)
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
    print(f"  this stop is reviewed on the {channel} ({channel_source})", file=sys.stderr)
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh gate", "project": str(project), "gate": page.gate, "page": str(page_path), "channel": channel, "url": None,
                          "message": "\n".join(lines)}, ensure_ascii=False), flush=True)
    else:
        print("\n".join(lines), flush=True)
    activity.note(f"{review.gate_title(page.gate, 'en')}: {len(page.d['decisions'])} decision(s) on the {channel}", [page_path])
    try:   # the text as it was when the page went out (tools/history.py); a failure to save never stops the page, nor does a lock held elsewhere for long
        import history
        for x in history.save(project, f"gate {page.gate}: the page went out", wait=2)[1]:
            print(f"  history: left out: {x['path']} ({x['why']})", file=sys.stderr)
    except Exception as e:
        print(f"  history: no snapshot of this page ({e})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(activity.exiting(lambda: jsonerr.guard(lambda: main(sys.argv[1:]))))   # bin/vh exec's into this: this process ends the run
