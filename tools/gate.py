"""bin/vh gate: one stop, one command. Check the gate data, build the review page, make it this round, open the review
desk when this stop is reviewed there, print the chat message; with --wait, wait for the person's submission.

usage: bin/vh gate <project> [<n>] [--desk | --page | --chat] [--wait] [--timeout s] [--port N] [--json]
       bin/vh gate <project> <n> --init [--json]
  <n>       1 | 2 | 3 | E0–E5 | 2b … : out/review/gate-<n>.json (playbook/01-pipeline.md, 审阅页, has every field); left out:
            this round, as bin/vh review takes it
  where the person reviews: --desk, --page or --chat when the person asked in chat; else the 审阅方式 line in LOCAL.md
            (对话 | 审阅页 | 审阅台; chat | page | desk); else the effort's default: studio the review desk, standard and quick
            the static page. Every channel gets the static page (out/review/gate-<n>.html, also index.html) and the chat
            message; the desk channel also gets the desk, started in the background on 127.0.0.1 when it is not serving
            this project yet (it stops by itself after 12 h without a request), and its address in the message
  --wait    the desk channel only: then wait like bin/vh desk wait (print the submission, exit 0; 3 after --timeout,
            default 7100 s). An agent runs this in the background: the message is printed first, before the waiting
  --init    write out/review/gate-<n>.json as a skeleton for this stop, in the BRIEF's review language, and stop: every text
            to write is a {填：…} ({fill in: …}), and bin/vh gate refuses the file (exit 2) until none is left, so an unfilled page
            never reaches the person. It carries "version": 1. A file already there is not overwritten (exit 2)
  --json    the record on stdout, the lines a person reads on stderr: {"version": 1, "tool", "project", "gate", "page", "channel", "url",
            "message": the chat message} (--init: {"version": 1, "tool", "project", "gate", "init": true, "path"}); a failure in
            the error's shape (tools/jsonerr.py). Not with --wait, whose answer is the submission
The page and the desk read the same out/review/gate-<n>.json: it is the one file a client renders for a stop. A page that goes out is also
a snapshot of the project's text (bin/vh history); a failure to save it never stops the page.
Exit: 0 the stop is out (with --wait: the submission is printed) · 1 the page was written but breaks a rule: no message,
no desk, and bin/vh status counts it as not sent until a run of it goes through (bin/vh review's 1) · 2 nothing to send: no project, no or bad gate JSON, placeholders left, the desk did not start,
--wait without the desk, --init over a file · 3 --wait timed out.
"""
import argparse, contextlib, json, os, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "desk"))
import activity, jsonerr, review   # noqa: E402,E401
from gatecheck import effort_of, local_md, stop_of   # noqa: E402

IDLE = 12 * 3600   # a desk gate starts stops by itself after this long without a request
CHANNEL = {"对话": "chat", "审阅页": "page", "审阅台": "desk", "chat": "chat", "page": "page", "desk": "desk"}
SAY = {"zh": {"desk_wait": "审阅台：{url}（勾选、点评、提交；我在后台等着，你一提交我就接着做）",
              "desk": "审阅台：{url}（勾选、点评、提交，然后回到这里说一声“看审阅台”）"},
       "en": {"desk_wait": "Review desk: {url} (tick, comment, submit; I'm waiting and carry on as soon as you submit)",
              "desk": "Review desk: {url} (tick, comment, submit, then tell me here: “check the desk”)"}}


CHECKPOINT_WHAT = {  # what a checkpoint puts in front of the person (playbook/01-pipeline.md, 导演模式)
    "E0": ("设定图、主旋律试听或 look-dev 变体", "the design sheet, the theme to listen to, or the look-dev variants"),
    "E1": ("两种音色的试听、旁白稿或钩子画面", "two voices to listen to, the script, or the hook's frames"),
    "E2": ("一张 cue 表：主旋律在哪几段、哪里留白、音效多密", "a cue sheet: where the theme comes in, where it is silent, how dense the effects are"),
    "E3": ("最终的配音和配乐，听一遍再锁时", "the final voice and score, heard once before the timing locks"),
    "E4": ("第一章的联系表和 10–20 s 片段", "the first chapter's contact sheet and a 10–20 s clip"),
    "E5": ("锁画面：bin/vh qa 的结果和请听的几处", "the picture lock: bin/vh qa's result and the places to listen to")}


def skeleton(gate, lang):
    """A gate JSON to fill in, for this stop. Each {填：…} says what goes there; bin/vh gate takes it once none is left."""
    zh = lang != "en"

    def f(a, b):
        return f"{{填：{a}}}" if zh else f"{{fill in: {b}}}"   # a shape no stylesheet can write (.bar {fill: #e33} is a page's own text)

    def card(k):
        return {"id": k, "label": f(f"立意卡 {k}：一句话核心想法", f"concept card {k}: the idea in one line"),
                "pro": f("为什么是这份材料；推出的画面和钩子", "why this material; the picture and the hook it leads to"),
                "con": f("风险或代价", "its risk or cost")}
    d = {"version": 1, "summary": f("一句话：这页要人定什么、看完要多久", "one line: what this page asks the person, and how long it takes")}
    stop = stop_of(gate)
    if stop == "1":
        d["decisions"] = [{"id": "concept", "question": f("选哪张立意卡？写成这支片子自己的问题", "which concept card? In this film's own words"),
                           "options": [card("A"), card("B"), card("C")], "recommend": f("A、B 或 C", "A, B or C"),
                           "why": f("推荐它的一句理由", "why, in one line"), "cost": "现在改：低 · 分镜后改：很高" if zh else "now: low · after the storyboard: very high"}]
        d["assets"] = [{"path": f(f"立意卡 {k} 那一帧画面的路径", f"the path of card {k}'s frame"),
                        "caption": f("这一帧在说什么", "what this frame says"), "for": "concept"} for k in "ABC"]
        d["delegated"] = [f("替人定了的事，一项一条：规格（画幅、分辨率、帧率、时长、在哪看）、引擎、费用",
                            "what you decided for the person, one an item: the spec (frame, resolution, rate, length, where it is watched), the engine, the cost")]
        d["appendix"] = [{"title": "大纲" if zh else "Outline", "text": f("按推荐立意写的 3–7 段，竖线表：段落、时间、看完知道什么", "3–7 segments for the recommended concept, a pipe table: segment, time, what the viewer knows after it")},
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
        d["least_sure"] = [{"id": f("镜头号", "shot id"), "note": f(f"自己最不满意的第 {i} 处，和可选的修法", f"what you like least, number {i}, and how it could be fixed")} for i in (1, 2, 3)]
        d["appendix"] = [{"title": "reviewer 的分数" if zh else "The reviewer's scores", "text": f("8 项分数和没修好的几处", "the 8 scores and what is still not fixed")}]
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
            out.write(json.dumps(skeleton(g, lang), ensure_ascii=False, indent=2) + "\n")
    except FileExistsError:
        return jsonerr.fail("exists", f"gate: {path} is already there, and --init does not overwrite: edit it, then bin/vh gate {shown} {g}")
    except OSError as e:
        return jsonerr.fail("failed", f"gate: can't write {path}: {e.strerror or e}")
    say = sys.stderr if as_json else sys.stdout
    print(f"✓ {path}: a skeleton for {review.gate_title(g, lang)}", file=say)
    if effort_of(project)[0] == "quick":
        print("  a quick project has no gates: this page is for a stop the person asked for", file=say)
    print(f"  replace every {'{fill in: …}' if lang == 'en' else '{填：…}'}, delete what this page does not need; until none is left, bin/vh gate refuses the file", file=say)
    print(f'  the fields: bin/vh know --show "playbook/01-pipeline.md#审阅页"; then: bin/vh gate {shown} {g}', file=say)
    activity.note(f"{review.gate_title(g, 'en')}: a skeleton to fill in", [path])
    if as_json:
        print(json.dumps({"version": 1, "tool": "bin/vh gate", "project": str(project), "gate": g, "init": True, "path": str(path)}, ensure_ascii=False))
    return 0


def channel_of(project, flag=None):
    """(channel, where it came from): a flag, LOCAL.md's 审阅方式 line, or the effort's default."""
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
    return ("desk" if effort == "studio" else "page"), f"effort {effort} ({src})"


def start_desk(project, port=None):
    """The desk's address for this project: the one serving it, else a new one started in its own session (it outlives
    this command) through bin/vh, so its run is in the activity log. None when it did not come up within 20 s."""
    sys.path.insert(0, str(HERE / "desk"))
    import server
    url = server.running(project)
    if url:
        return url, False
    log = project / "out" / "review" / ".desk.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [os.environ.get("OVH_BASH") or "bash", str(ROOT / "bin" / "vh"), "desk", str(project), "--idle", str(IDLE)]
    if port is not None:
        cmd += ["--port", str(port)]
    with open(log, "ab") as out:
        p = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=out, stderr=out, start_new_session=True)
    for _ in range(200):
        url = server.running(project)
        if url:
            return url, True
        if p.poll() is not None:
            break
        time.sleep(0.1)
    return None, True


def main(argv):
    ap = argparse.ArgumentParser(prog="bin/vh gate", description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="project folder, or its name under projects/")
    ap.add_argument("gate", nargs="?", help="1 | 2 | 3 | E0–E5 | 2b …; default: this round")
    how = ap.add_mutually_exclusive_group()
    for c in ("desk", "page", "chat"):
        how.add_argument(f"--{c}", dest="channel", action="store_const", const=c, help=f"review in the {c} this time")
    ap.add_argument("--wait", action="store_true", help="the desk only: then wait for the submission, like bin/vh desk wait")
    ap.add_argument("--timeout", type=float, default=7100, help="with --wait: seconds (default 7100, under Claude Code's 2 h)")
    ap.add_argument("--port", type=int, help="the desk's port when it has to start (default: the first free of 8780–8799)")
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
    if a.wait and channel != "desk":
        return jsonerr.fail("usage", f"gate: --wait waits for the review desk, and this stop is reviewed on the {channel} ({why}): the person answers in "
                            "the chat. Leave --wait out, or use --desk if they want the desk")
    with contextlib.redirect_stdout(sys.stderr if a.json else sys.stdout):
        rc, page, page_path = review.publish(project, a.gate, a.project)
    if rc:   # bin/vh review said what is wrong; nothing goes to the person
        jsonerr.mark("refused" if rc == 1 else "invalid", f"bin/vh gate {a.project} --init writes a skeleton; bin/vh know --show \"playbook/01-pipeline.md#审阅页\" has the fields" if rc != 1 else None)
        return rc
    lines = [page.chat(page_path)]
    url = None
    if channel == "desk":
        url, started = start_desk(project, a.port)
        if not url:
            return jsonerr.fail("failed", f"gate: the review desk did not start (out/review/.desk.log says why); the page is {page_path}. "
                                f"Start it by hand: bin/vh desk {a.project}")
        print(f"✓ review desk {url} ({'started, in the background' if started else 'already serving this project'})", file=sys.stderr)
        lines.append(SAY[page.lang]["desk_wait" if a.wait else "desk"].format(url=url))
    print(f"  this stop is reviewed on the {channel} ({why})", file=sys.stderr)
    if a.json:
        print(json.dumps({"version": 1, "tool": "bin/vh gate", "project": str(project), "gate": page.gate, "page": str(page_path), "channel": channel, "url": url,
                          "message": "\n".join(lines)}, ensure_ascii=False), flush=True)
    else:
        print("\n".join(lines), flush=True)
    activity.note(f"{review.gate_title(page.gate, 'en')}: {len(page.d['decisions'])} decision(s) on the {channel}" + (f" · {url}" if url else ""), [page_path])
    try:   # the text as it was when the page went out (tools/history.py); a failure to save never stops the page, nor does a lock held elsewhere for long
        import history
        for x in history.save(project, f"gate {page.gate}: the page went out", wait=2)[1]:
            print(f"  history: left out: {x['path']} ({x['why']})", file=sys.stderr)
    except Exception as e:
        print(f"  history: no snapshot of this page ({e})", file=sys.stderr)
    if not a.wait:
        return 0
    import feedback
    jsonerr.mark("timeout")
    return feedback.wait(project, a.timeout)


if __name__ == "__main__":
    sys.exit(activity.exiting(lambda: jsonerr.guard(lambda: main(sys.argv[1:]))))   # bin/vh exec's into this: this process ends the run
