"""Studio's page in a headless Chrome (tools/ci.sh desk_checks): what the person sees of their notes' hand-over, on copies
of the demo film, a desk of these checks' own on a free port, nothing sent anywhere else. One line a check on stdout:
"ok\t<what>", "bad\t<what>: <why>", or "skip\t<what>: <why>" (no Chrome or no node), then "end".

  python3 tools/desk/test_page.py <scratch folder>

The page is driven by tools/desk/page_driver.mjs (the repo's own headless Chrome launcher, tools/textcheck/browser.mjs).
"""
import json, os, re, shutil, signal, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
T = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else sys.exit("usage: python3 tools/desk/test_page.py <scratch folder>")
VH = ROOT / "bin" / "vh"
ENV = dict(os.environ, HOME=str(T / "home"), TMPDIR=str(T / "tmp"), XDG_CACHE_HOME=str(T / "cache"), XDG_DATA_HOME=str(T / "data"),
           XDG_CONFIG_HOME=str(T / "config"), OVH_PROJECTS=str(T / "none"), OVH_STUDIO_PROFILES=str(T / "profiles"),
           OVH_STUDIO_SHELL_PROFILE=str(T / "shellprof"), OVH_STUDIO_SHELL_CACHE=str(T / "shellcache"), OVH_AGENTS_DIR=str(T / "agents"),
           OVH_LOCAL_MD="/dev/null/LOCAL.md", OVH_STUDIO_SHELL="none", OVH_STUDIO_BROWSER="none", OVH_GATE_STUDIO="0", OVH_KEYSTORE="none",
           BROWSER="/usr/bin/true", OVH_ACTIVITY_AGENT="0")
for k in ("HOME", "TMPDIR", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME"):
    Path(ENV[k]).mkdir(parents=True, exist_ok=True)
os.environ.update({k: ENV[k] for k in ("TMPDIR", "OVH_ACTIVITY_AGENT")})
import feedback as F   # noqa: E402
import server          # noqa: E402


def say(kind, what, why=""):
    print(f"{kind}\t{what}" + (f": {why}" if why else ""), flush=True)


def chrome():
    for p in (os.environ.get("CHROME_PATH"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/usr/bin/google-chrome",
              "/usr/bin/google-chrome-stable", "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if p and os.access(p, os.X_OK):
            return p
    return None


def film(name, gate_e1):
    """A copy of the demo film at its script stop (gate ① decided, page E1 out)."""
    p = T / "root" / name
    shutil.copytree(ROOT / "tools" / "desk" / "fixtures" / "demo", p)
    g = p / "out" / "review"
    for x in ("gate-2.json", "gate-3.json"):
        (g / x).unlink()
    r = (p / "REVIEW.md").read_text(encoding="utf-8")
    (p / "REVIEW.md").write_text(r[:r.index("## 关卡 ② 分镜")], encoding="utf-8")
    (g / "gate-E1.json").write_text(json.dumps(gate_e1, ensure_ascii=False), encoding="utf-8")
    subprocess.run(["bash", str(VH), "review", str(p), "E1"], capture_output=True, text=True, env=ENV, timeout=60, check=True)
    return p


def key(p):
    return server.keyify(p.name, p)


def drive(url, steps):
    r = subprocess.run(["node", str(HERE / "page_driver.mjs"), BROWSER], input=json.dumps({"url": url, "width": 1440, "height": 900, "steps": steps}),
                       capture_output=True, text=True, timeout=300, env=ENV)
    out = {}
    for line in r.stdout.splitlines():
        try:
            j = json.loads(line)
            out[j.get("name")] = j
        except ValueError:
            pass
    if not out:
        raise RuntimeError(f"the page driver said nothing: {(r.stdout + r.stderr)[-400:]}")
    return out


def v(res, name):
    x = res.get(name) or {}
    return x.get("value") if "error" not in x else f"<{x['error']}>"


BROWSER = chrome()
if not BROWSER or not shutil.which("node"):
    say("skip", "Studio's page in a headless Chrome", "no Chrome" if not BROWSER else "no node")
    print("end")
    sys.exit(0)

E1 = {"summary": "旁白稿第一版，逐句看", "decisions": [{"id": "names", "question": "英文名念不念？", "options": [{"id": "N1", "label": "不念"}, {"id": "N2", "label": "念"}], "recommend": "N1"},
                                                    {"id": "go", "question": "旁白稿能定吗？", "options": [{"id": "OK", "label": "可以，往下做"}, {"id": "FIX", "label": "先改"}], "recommend": "OK"}],
      "appendix": [{"title": "大纲", "text": "| 段落 | 时间 |\n|---|---|\n| 开场 | 0–9 s |"}, {"title": "事实清单", "text": "- 一天两次"}, {"title": "引用", "text": "- 某教材"}],
      "decided": ["立意：从海边讲起"], "delegated": ["配音用男声"]}
late = film("late", E1)   # the script's round was submitted and an agent took it; the person writes more
first = F.save(late, F.validate(late, {"round": "E1", "lang": "zh", "decisions": {"names": "N1", "go": "OK"}, "items": [{"target": "seg:1", "status": "change", "text": "开头再短点"}]}))
F.mark_consumed(late, [first])   # (as an agent's wait or desk feedback leaves it)
fix = film("fix", E1)     # nothing submitted yet: "先改" picked with no note
busy = film("busy", dict(E1, least_sure=[{"id": f"c0{i}", "note": f"第 {i} 句会不会太书面，念出来像在读稿"} for i in range(1, 5)]))   # eight notes kept beside a full column: the newest and the state line on screen at 1440 x 900

proc = subprocess.Popen([sys.executable, str(HERE / "fixtures" / "with_tty.py"), "bash", str(VH), "desk", "--root", str(T / "root"), "--port", "0", "--no-open", "--print-address"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=ENV, start_new_session=True)
url, t0, seen = None, time.time(), ""
try:
    while time.time() - t0 < 30 and not url:
        line = proc.stdout.readline()
        seen += line
        m = re.search(r"(http://127\.0\.0\.1:\d+/\?c=[A-Za-z0-9_-]+)", line)
        url = m.group(1) if m else None
    if not url:
        say("bad", "Studio's page: the desk did not start", seen[-300:])
        print("end")
        sys.exit(0)
    tab = {"click": "#colTabs [data-tab=round]", "name": "tab"}
    KEEP = "(FB.items[{t!r}] = {{ status: 'change', text: {x!r}, label: {lb!r} }}, save(), renderColumn(), true)"
    steps = [
        {"go": f"#/p/{key(late)}/outline", "after": 2500}, tab,
        {"eval": KEEP.format(t="seg:2", x="这段再短一点", lb="大纲 第 2 段"), "name": "keep"},
        {"eval": "$('#colRound').innerText", "name": "late_bar"},
        {"eval": "$('#cMine').innerText", "name": "late_block"},
        {"click": "#openConfirm"}, {"eval": "$('#submitHint').innerText", "name": "late_sheet"},
        {"click": "#doSubmit", "after": 3000},
        {"until": "$('#cMine') && /补交的 1 条，还没人取/.test($('#cMine').innerText) && $('#colRound').innerText", "name": "late_after", "ms": 10000},
        {"go": f"#/p/{key(fix)}/outline/script", "after": 2500}, tab,
        {"eval": "(pick('go', 'FIX'), true)", "name": "pick"},
        {"click": "#openConfirm"},
        {"eval": "JSON.stringify({ ask: ($('#fixAsk') || {}).innerText || '', back: !!$('#fixBack'), go: ($('#doSubmit') || {}).innerText })", "name": "fix_sheet"},
        {"click": "#fixBack"},
        {"eval": "JSON.stringify({ hidden: $('#confirm').hidden, focus: document.activeElement && document.activeElement.id })", "name": "fix_back"},
        {"eval": "(FB.general = '第三句改口语', save(), true)", "name": "general"},
        {"click": "#openConfirm"},
        {"eval": "JSON.stringify({ ask: ($('#fixAsk') || {}).innerText || '', back: !!$('#fixBack') })", "name": "fix_with_note"},
        {"click": "#noSubmit"},
        {"eval": "(" + ", ".join(KEEP.format(t=f"cap:c0{i}", x=f"第 {i} 句", lb=f"字幕 c0{i}") for i in (1, 2)) + ")", "name": "two"},
        {"eval": "JSON.stringify({ bar: $('#colRound').innerText, block: $('#cMine .blk-h').innerText, rows: document.querySelectorAll('#cMine ul.mine li').length })", "name": "counts"},
        {"go": f"#/p/{key(busy)}/outline/script", "after": 2500}, tab,
        {"eval": "(" + ", ".join(KEEP.format(t=f"cap:c0{i}", x=f"第 {i} 句再口语一点", lb=f"字幕 c0{i}") for i in range(1, 9)) + ")", "name": "eight"},
        {"wait": 800},
        {"eval": "JSON.stringify((() => { const m = $('#cMine'), h = $('#cMine .blk-h'), n = $('#cMine li[data-goto=\"cap:c08\"]'), r = (e) => e && e.getBoundingClientRect(); "
                 "const H = r(h), N = r(n), M = r(m), B = r($('#colBody')); return { h: H && [H.top, H.bottom], n: N && [N.top, N.bottom], m: M && [M.top, M.bottom], "
                 "body: [B.top, B.bottom], text: h && h.innerText }; })())",
         "name": "busy_view"},
    ]
    res = drive(url, steps)
finally:
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except OSError:
        pass
    proc.wait(timeout=10)


def check(what, ok, why):
    say("ok" if ok else "bad", what, "" if ok else str(why)[:500])


bar, block, sheet, after = v(res, "late_bar") or "", v(res, "late_block") or "", v(res, "late_sheet") or "", res.get("late_after") or {}
check("a round an agent already took: the bar says these notes go on their own as a later batch (补交), the notes block says the earlier ones were "
      "picked up, the sheet says so before sending and who picks them up; after sending, the block says they are not picked up yet, never that they went to the agent",
      "补充 1 条" in bar and "补交" in bar and "已经交给" not in bar and "还没交 1 条" in block and "取走" in block and "已经被 AI 取走了" in sheet
      and "单独交" in sheet and "现在没有 AI 在等" in sheet and after.get("ok") and "交了，还没人取" in str(after.get("value")) and "已经交给 agent" not in str(after.get("value")),
      [bar, block, sheet, after])
fs, fb, fn = v(res, "fix_sheet"), v(res, "fix_back"), v(res, "fix_with_note")
try:
    fs, fb, fn = json.loads(fs), json.loads(fb), json.loads(fn)
    ok = "先改" in fs["ask"] and "还没写改哪里" in fs["ask"] and fs["back"] and fs["go"] == "就这样交" and fb["hidden"] and fb["focus"] == "say" and not fn["back"] and not fn["ask"]
except (TypeError, ValueError, KeyError):
    ok = False
check("\"先改\" picked with no note: the sheet asks what to change, \"回去写\" closes it with the note box ready, \"就这样交\" still sends; with a note it does not ask",
      ok, [fs, fb, fn])
cn = v(res, "counts")
try:
    c = json.loads(cn)
    ok = c["rows"] == 3 and f"{c['rows']} 条意见" in c["bar"] and f"还没交 {c['rows']} 条" in c["block"]
except (TypeError, ValueError, KeyError):
    ok = False
check("the bar's count, the notes block's count and the notes listed agree (two notes on lines and the overall words)", ok, cn)
bv = v(res, "busy_view")
try:
    b = json.loads(bv)
    def seen(x):   # inside the column's visible part, and inside the block's own
        return x[0] >= b["body"][0] - 1 and x[1] <= min(b["body"][1], b["m"][1]) + 1
    ok = b["h"] and b["n"] and seen(b["h"]) and seen(b["n"]) and b["n"][0] >= b["h"][1] - 2 and "还没交 8 条" in b["text"]
except (TypeError, ValueError, KeyError):
    ok = False
check("eight notes kept beside two decisions, four unsure places and three appendices at 1440 x 900: the notes' state line and the note kept last are on screen, no scrolling", ok, bv)
print("end", flush=True)
