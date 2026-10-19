"""bin/vh gate: one stop, one command. Check the gate data, build the review page, make it this round, open the review
desk when this stop is reviewed there, print the chat message; with --wait, wait for the person's submission.

usage: bin/vh gate <project> [<n>] [--desk | --page | --chat] [--wait] [--timeout s] [--port N]
  <n>       1 | 2 | 3 | E0–E5 | 2b … : out/review/gate-<n>.json (playbook/01-pipeline.md, 审阅页, has every field); left out:
            this round, as bin/vh review takes it
  where the person reviews: --desk, --page or --chat when the person asked in chat; else the 审阅方式 line in LOCAL.md
            (对话 | 审阅页 | 审阅台; chat | page | desk); else the effort's default: studio the review desk, standard and quick
            the static page. Every channel gets the static page (out/review/gate-<n>.html, also index.html) and the chat
            message; the desk channel also gets the desk, started in the background on 127.0.0.1 when it is not serving
            this project yet (it stops by itself after 12 h without a request), and its address in the message
  --wait    the desk channel only: then wait like bin/vh desk wait (print the submission, exit 0; 3 after --timeout,
            default 7100 s). An agent runs this in the background: the message is printed first, before the waiting
The page and the desk read the same out/review/gate-<n>.json: it is the one file a client renders for a stop.
Exit: 0 the stop is out (with --wait: the submission is printed) · 1 the page was written but breaks a rule: no message,
no desk (bin/vh review's 1) · 2 nothing to send: no project, no or bad gate JSON, the desk did not start, --wait without
the desk · 3 --wait timed out.
"""
import argparse, os, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "desk"))
import activity, review   # noqa: E402,E401
from gatecheck import effort_of, local_md   # noqa: E402

IDLE = 12 * 3600   # a desk gate starts stops by itself after this long without a request
CHANNEL = {"对话": "chat", "审阅页": "page", "审阅台": "desk", "chat": "chat", "page": "page", "desk": "desk"}
SAY = {"zh": {"desk_wait": "审阅台：{url}（勾选、点评、提交；我在后台等着，你一提交我就接着做）",
              "desk": "审阅台：{url}（勾选、点评、提交，然后回到这里说一声“看审阅台”）"},
       "en": {"desk_wait": "Review desk: {url} (tick, comment, submit; I'm waiting and carry on as soon as you submit)",
              "desk": "Review desk: {url} (tick, comment, submit, then tell me here: “check the desk”)"}}


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
    a = ap.parse_args(argv)
    project = review.find_project(a.project)
    if not project:
        return 2
    channel, why = channel_of(project, a.channel)
    if a.wait and channel != "desk":
        print(f"gate: --wait waits for the review desk, and this stop is reviewed on the {channel} ({why}): the person answers in "
              "the chat. Leave --wait out, or use --desk if they want the desk", file=sys.stderr)
        return 2
    rc, page, page_path = review.publish(project, a.gate, a.project)
    if rc:   # bin/vh review said what is wrong; nothing goes to the person
        return rc
    lines = [page.chat(page_path)]
    url = None
    if channel == "desk":
        url, started = start_desk(project, a.port)
        if not url:
            print(f"gate: the review desk did not start (out/review/.desk.log says why); the page is {page_path}. "
                  f"Start it by hand: bin/vh desk {a.project}", file=sys.stderr)
            return 2
        print(f"✓ review desk {url} ({'started, in the background' if started else 'already serving this project'})", file=sys.stderr)
        lines.append(SAY[page.lang]["desk_wait" if a.wait else "desk"].format(url=url))
    print(f"  this stop is reviewed on the {channel} ({why})", file=sys.stderr)
    print("\n".join(lines), flush=True)
    activity.note(f"{review.gate_title(page.gate, 'en')}: {len(page.d['decisions'])} decision(s) on the {channel}" + (f" · {url}" if url else ""), [page_path])
    if not a.wait:
        return 0
    import feedback
    return feedback.wait(project, a.timeout)


if __name__ == "__main__":
    sys.exit(activity.exiting(lambda: main(sys.argv[1:])))   # bin/vh exec's into this: this process ends the run
