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
                                                    {"id": "go", "question": "旁白稿能定吗？", "options": [{"id": "OK", "label": "可以，往下做"}, {"id": "FIX", "label": "先改", "needs_note": True}], "recommend": "OK"}],
      "appendix": [{"title": "大纲", "text": "| 段落 | 时间 |\n|---|---|\n| 开场 | 0–9 s |"}, {"title": "事实清单", "text": "- 一天两次"}, {"title": "引用", "text": "- 某教材"}],
      "decided": ["立意：从海边讲起"], "delegated": ["配音用男声"]}
late = film("late", E1)   # the script's round was submitted and an agent took it; the person writes more
first = F.save(late, F.validate(late, {"round": "E1", "lang": "zh", "decisions": {"names": "N1", "go": "OK"}, "items": [{"target": "seg:1", "status": "change", "text": "开头再短点"}]}))
F.mark_consumed(late, [first])   # (as an agent's wait or desk feedback leaves it)
KEEP_AS_IS = {"id": "keep", "question": "开头那句保留吗？", "options": [{"id": "K1", "label": "保留"}, {"id": "K2", "label": "不要改，保持不变，不用重做"}], "recommend": "K1"}
fix = film("fix", dict(E1, decisions=E1["decisions"] + [KEEP_AS_IS]))   # nothing submitted yet: "先改" picked with no note; a "no change" option picked
moved = film("moved", E1)   # notes kept on the script, never sent, then the agent sends the outline again
AGAIN = {"summary": "大纲改成 3 段，再看一遍", "decisions": [{"id": "go", "question": "大纲能做分镜了吗？", "options": [{"id": "OK", "label": "可以"}, {"id": "FIX", "label": "先改", "needs_note": True}], "recommend": "OK"}]}
busy = film("busy", dict(E1, least_sure=[{"id": f"c0{i}", "note": f"第 {i} 句会不会太书面，念出来像在读稿"} for i in range(1, 5)]))   # eight notes kept beside a full column: the newest and the state line on screen at 1440 x 900
# the window shows what the files say, and a stop opens on what it asks about
OUTLINE_AGAIN = {"summary": "大纲改成 3 段，再看一遍", "decisions": [{"id": "go", "question": "大纲能做分镜了吗？", "options": [{"id": "OK", "label": "可以"}, {"id": "FIX", "label": "先改"}], "recommend": "OK"}]}
reopen = film("reopen", E1)   # gate ① decided, then the outline sent again (1b, no concept cards)
(reopen / "out" / "review" / "gate-1b.json").write_text(json.dumps(OUTLINE_AGAIN, ensure_ascii=False), encoding="utf-8")
subprocess.run(["bash", str(VH), "review", str(reopen), "1b"], capture_output=True, text=True, env=ENV, timeout=60, check=True)
script = film("script", E1)   # the script's stop
follow = film("follow", E1)   # open on the script; the agent sends the outline again meanwhile
files = film("files", E1)     # open on the outline; the agent cuts it from 3 parts to 2 meanwhile
brief = (files / "BRIEF.md").read_text(encoding="utf-8")
two = re.sub(r"\n\| 3 \|[^\n]*", "", brief.replace("| 2 | 两个鼓包 | 9–21 s |", "| 2 | 两面都鼓 | 9–32 s |"))
tabs = film("tabs", E1)       # the stop's page on the outline module: a tab clicked opens where the tabs are

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
        {"eval": "(pick('keep', 'K2'), true)", "name": "pick_keep"},
        {"click": "#openConfirm"},
        {"eval": "JSON.stringify({ ask: ($('#fixAsk') || {}).innerText || '', back: !!$('#fixBack') })", "name": "keep_sheet"},
        {"click": "#noSubmit"},
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
    ]
    steps += [   # drafts on a page the agent replaced: shown as not sent, sent to their own round on the person's word
        {"go": f"#/p/{key(moved)}/outline/script", "after": 2500}, tab,
        {"eval": KEEP.format(t="cap:c03", x="第三句别念英文", lb="字幕 c03"), "name": "moved_keep"},
        {"write": str(moved / "out" / "review" / "gate-1b.json"), "text": json.dumps(AGAIN, ensure_ascii=False)},
        {"write": str(moved / "out" / "review" / "gate-1b.html"), "text": "<!doctype html><title>1b</title>"},
        {"write": str(moved / "out" / "review" / ".current"), "text": "1b\n"},
        {"until": "/在旁白稿那一页写的 1 条，还没交/.test(($('#cMine') || {}).innerText || '')", "name": "moved_shown", "ms": 15000},
        {"click": "[data-left-send]", "after": 3000},
        {"until": "!/还没交/.test(($('#cMine') || {}).innerText || '') || /补交|还没人取/.test(($('#cMine') || {}).innerText || '')", "name": "moved_sent", "ms": 10000},
        {"go": f"#/p/{key(busy)}/outline/script", "after": 2500}, tab, {"wait": 800},   # (back to the film with eight notes kept, for the layout below)
    ]
    VIEW = ("JSON.stringify((() => { const m = $('#cMine'), h = $('#cMine .blk-h'), n = $('#cMine li[data-goto=\"cap:c08\"]'), r = (e) => e && e.getBoundingClientRect(); "
            "const H = r(h), N = r(n), M = r(m), B = r($('#colBody')); return { h: H && [H.top, H.bottom], n: N && [N.top, N.bottom], m: M && [M.top, M.bottom], "
            "body: [B.top, B.bottom], text: h && h.innerText, theme: document.documentElement.dataset.theme }; })())")
    for size in ((1280, 720), (1440, 900)):
        steps.append({"viewport": list(size)})
        for theme in ("darkfield", "prism", "bridge"):
            steps += [{"eval": f"(document.documentElement.dataset.theme = {theme!r}, true)", "name": "theme"}, {"wait": 500},
                      {"eval": VIEW, "name": f"busy_view {size[0]}x{size[1]} {theme}"}]
    steps += [{"eval": "(document.documentElement.dataset.theme = 'darkfield', true)", "name": "theme"}, {"click": "#lang", "after": 1500}, tab]
    for size in ((1280, 720), (1440, 900)):
        steps += [{"viewport": list(size)}, {"eval": VIEW, "name": f"busy_view {size[0]}x{size[1]} en"}]
    steps += [{"click": "#lang", "after": 1500}]
    WHERE = "JSON.stringify({ mod: ($('#stage [data-mod]') || {}).dataset && $('#stage [data-mod]').dataset.mod, hash: decodeURIComponent(location.hash), " \
            "tab: (($('nav.subtabs [aria-selected=true]') || { getAttribute: () => '' }).getAttribute('href')) || '', cards: !!$('.c-cards') })"
    steps += [
        # bin/vh gate opens a stop at #/p/<key>/gate/<page>: the outline's second page on the outline, its question in the column
        {"go": f"#/p/{key(reopen)}/gate/1b", "after": 3000}, tab, {"eval": WHERE, "name": "reopen_at"},
        {"go": f"#/p/{key(script)}/gate/E1", "after": 3000}, {"eval": WHERE, "name": "script_at"},
        # the agent sends another page while the person is on the script: the page follows, and the address names what is shown
        {"go": f"#/p/{key(follow)}/outline/script", "after": 2500},
        {"write": str(follow / "out" / "review" / "gate-1b.json"), "text": json.dumps(OUTLINE_AGAIN, ensure_ascii=False)},
        {"write": str(follow / "out" / "review" / "gate-1b.html"), "text": "<!doctype html><title>1b</title>"},   # (bin/vh gate writes the page with it)
        {"write": str(follow / "out" / "review" / ".current"), "text": "1b\n"},
        {"until": f"location.hash === '#/p/{key(follow)}/outline' && $('#stage [data-mod=outline]') && !$('nav.subtabs [aria-selected=true][href$=\"/script\"]')", "name": "follow_at", "ms": 15000},
        {"reload": True}, {"eval": WHERE, "name": "follow_reload"},
        # the agent rewrites the outline while it is open, a note kept on its third part: the page shows two parts, says the note's place is gone
        {"go": f"#/p/{key(files)}/outline", "after": 2500}, tab,
        {"eval": "document.querySelectorAll('#stage [data-mark^=\"seg:\"]').length", "name": "files_before"},
        {"eval": KEEP.format(t="seg:3", x="第三段太长", lb="大纲 第 3 段"), "name": "keep3"},
        {"eval": "(document.activeElement && document.activeElement.blur(), true)", "name": "blur"},
        {"write": str(files / "BRIEF.md"), "text": two},
        {"until": "document.querySelectorAll('#stage [data-mark^=\"seg:\"]').length === 2 && /两面都鼓/.test($('#stage').innerText)", "name": "files_after", "ms": 15000},
        {"eval": "JSON.stringify({ hash: decodeURIComponent(location.hash), gone: /不在了/.test($('#cMine').innerText) })", "name": "files_where"},
        # the stop's page on the outline: clicking the script tab leaves the tab row where it was, and the page's rest comes after
        {"go": f"#/p/{key(tabs)}/outline", "after": 2500},
        {"eval": "$('nav.subtabs').getBoundingClientRect().top", "name": "tabs_before"},
        {"click": "nav.subtabs a[href$='/outline/script']", "after": 2000},
        {"eval": "JSON.stringify({ top: $('nav.subtabs').getBoundingClientRect().top, body: $('#modBody') && $('#modBody').getBoundingClientRect().top, "
                 "rest: $('#gatePart') && $('#gatePart').getBoundingClientRect().top, script: !!$('nav.subtabs [aria-selected=true][href$=\"/script\"]') })", "name": "tabs_after"},
    ]
    res = drive(url, steps)
finally:   # the desk this check started, and everything under it (bin/vh desk runs on in its own session): by process tree, never by name
    rows = [x.split() for x in subprocess.run(["ps", "-A", "-o", "pid=,ppid="], capture_output=True, text=True).stdout.splitlines()]
    tree, grew = {proc.pid}, True
    while grew:
        more = {int(a) for a, b in (r for r in rows if len(r) == 2) if int(b) in tree} - tree
        tree, grew = tree | more, bool(more)
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for x in tree:
            try:
                os.kill(x, sig)
            except OSError:
                pass
        t1 = time.time()
        while time.time() - t1 < 5 and any(subprocess.run(["kill", "-0", str(x)], capture_output=True).returncode == 0 for x in tree):
            time.sleep(0.2)
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
try:
    ks = json.loads(v(res, "keep_sheet"))
    ok = ok and not ks["ask"] and not ks["back"]
except (TypeError, ValueError, KeyError):
    ks, ok = v(res, "keep_sheet"), False
check("\"先改\" (an option whose gate JSON says needs_note) picked with no note: the sheet asks what to change, \"回去写\" closes it with the note box "
      "ready, \"就这样交\" still sends; with a note it does not ask, nor for an option that means \"no change\" (\"不要改，保持不变，不用重做\")", ok, [fs, fb, fn, ks])
cn = v(res, "counts")
try:
    c = json.loads(cn)
    ok = c["rows"] == 3 and f"{c['rows']} 条意见" in c["bar"] and f"还没交 {c['rows']} 条" in c["block"]
except (TypeError, ValueError, KeyError):
    ok = False
check("the bar's count, the notes block's count and the notes listed agree (two notes on lines and the overall words)", ok, cn)
sent = [json.loads(f.read_text(encoding="utf-8")) for f in (moved / "out" / "review" / "feedback").glob("*.json")] if (moved / "out" / "review" / "feedback").is_dir() else []
check("notes kept on a page the agent then replaced (never sent): the notes block lists them as not sent, on that page; sent on the person's click "
      "to that page's own round, never to the new page", (res.get("moved_shown") or {}).get("ok") and (res.get("moved_sent") or {}).get("ok")
      and [(x.get("round"), [i.get("text") for i in x.get("items") or []]) for x in sent] == [("E1", ["第三句别念英文"])], [res.get("moved_shown"), res.get("moved_sent"), sent])
bad_views = []
for name in [k for k in res if k and k.startswith("busy_view")]:
    try:
        b = json.loads(v(res, name))

        def seen(x):   # inside the column's visible part, and inside the block's own
            return x[0] >= max(b["body"][0], b["m"][0]) - 1 and x[1] <= min(b["body"][1], b["m"][1]) + 1
        ok = b["h"] and b["n"] and seen(b["h"]) and seen(b["n"]) and b["n"][0] >= b["h"][1] - 2 and b["m"][1] <= b["body"][1] + 1 \
            and b["m"][1] - b["m"][0] >= 3 * (b["h"][1] - b["h"][0]) and ("还没交 8 条" in b["text"] or "8 not sent yet" in b["text"])
    except (TypeError, ValueError, KeyError):
        ok = False
    if not ok:
        bad_views.append([name, v(res, name)])
ok = not bad_views and len([k for k in res if k and k.startswith("busy_view")]) == 8
check("eight notes kept beside two decisions, four unsure places and three appendices, at 1280 x 720 and 1440 x 900, in the three themes and in English: "
      "the notes' state line and the note kept last are on screen, apart, inside the column, the block never squeezed under three lines", ok, bad_views)


def js(name):
    try:
        return json.loads(v(res, name))
    except (TypeError, ValueError):
        return {"raw": v(res, name)}


ra, sa, fr = js("reopen_at"), js("script_at"), js("follow_reload")
check("a stop opens on what it asks about: the outline sent again (no concept cards) on the outline with its question in the column, the script on the "
      "outline's script tab; the address then names that module",
      ra.get("mod") == "outline" and ra.get("hash", "").endswith("/outline") and ra.get("cards") and sa.get("mod") == "outline"
      and sa.get("hash", "").endswith("/outline/script") and sa.get("tab", "").endswith("/script"), [ra, sa])
check("a page the agent sends while the person is elsewhere: the window follows to it, the address names what is shown, and a reload stays there",
      (res.get("follow_at") or {}).get("ok") and fr.get("mod") == "outline" and fr.get("hash", "").endswith("/outline"), [res.get("follow_at"), fr])
fa, fw = res.get("files_after") or {}, js("files_where")
check("the agent rewrites the outline while it is open: within seconds the page shows the new parts, stays where it was, and a note kept on a part that "
      "is gone says so", v(res, "files_before") == 3 and fa.get("ok") and fw.get("hash", "").endswith("/outline") and fw.get("gone"), [v(res, "files_before"), fa, fw])
tb, ta = v(res, "tabs_before"), js("tabs_after")
check("the script tab clicked on a stop's page: the tab row is not pushed down, the tab's content starts right under it, and the page's decided, "
      "delegated and appendices come after that content",
      isinstance(tb, (int, float)) and ta.get("script") and ta.get("top", 1e9) <= tb + 4 and ta.get("body") and ta["body"] - ta["top"] < 80
      and ta.get("rest") and ta["rest"] > ta["body"], [tb, ta])
print("end", flush=True)
