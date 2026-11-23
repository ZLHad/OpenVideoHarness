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
follow = film("follow", E1)   # opened by Studio on the script; the agent sends the outline again meanwhile: the page follows (Back returns)
stay = film("stay", E1)       # the person went to 决定 themself; the agent sends the outline again: the page stays and says so
half = film("half", E1)       # a page written halfway (not JSON yet): no new round, no reload, until it reads
scroll = film("scroll", E1)   # scrolled down the script; an unrelated NOTES.md change: the page reads again and stays where it was
(scroll / "SCRIPT.md").write_text("# SCRIPT\n\n## 旁白\n\n| # | 时间 | 旁白 |\n|---|---|---|\n"
                                   + "".join(f"| c{i:02d} | {i * 1.3:.1f}–{i * 1.3 + 1.2:.1f} s | 第 {i} 句旁白，讲海水和月亮。 |\n" for i in range(1, 25)), encoding="utf-8")
LONG = "这一页要定旁白稿能不能往下做。" + "每一句都对着画面再读一遍，看读不读得完，" * 12
longp = film("longsum", dict(E1, summary=LONG))   # a 400-character summary: two lines above the tabs, whole below
tabs = film("tabs", E1)       # the stop's page on the outline module: a tab clicked opens where the tabs are
# an outline of nine parts rewritten to five: removed in the middle, two in another order, one renamed, one's words rewritten
NINE = [("开场", "一天涨两次"), ("两个鼓包", "两面都鼓起来"), ("转一圈", "地球转一圈经过两次"), ("月亮", "月亮拉着近的一面"), ("太阳", "太阳也拉一点"),
        ("大潮", "日月同向时最高"), ("小潮", "日月垂直时最低"), ("海岸", "海湾把潮差放大"), ("收尾", "回到刻度桩")]
FIVE = [("开场", "一天涨两次"), ("转一圈", "地球转一圈经过两次"), ("月亮的拉力", "月亮拉着近的一面"), ("收尾", "回到刻度桩"), ("太阳", "太阳的拉力只有月亮的一半")]


def outline(rows):
    head = "| # | 段落 | 时间 | 观众看完知道 / 感到 | 关键画面 |\n|---|---|---|---|---|\n"
    return head + "".join(f"| {i + 1} | {t} | {i * 4}–{i * 4 + 4} s | {k} | 画面{i + 1} |\n" for i, (t, k) in enumerate(rows))


nine = film("nine", E1)
nb = (nine / "BRIEF.md").read_text(encoding="utf-8")
top, rest = nb.split("## Outline", 1)
tail = rest[rest.index("\n## ", 1):] if "\n## " in rest[1:] else ""
(nine / "BRIEF.md").write_text(top + "## Outline\n\n" + outline(NINE) + tail, encoding="utf-8")
five = top + "## Outline\n\n" + outline(FIVE) + tail
stamp = film("stamp", E1)   # the stamp is taken before the read: a file written during the read leaves the page one reload behind


def stamp_before_read():   # (no browser: the server's own function, a write injected into its read)
    import reader
    real = reader.read_project

    def writing(project, *a, **k):
        out = real(project, *a, **k)
        with open(Path(project) / "BRIEF.md", "a", encoding="utf-8") as f:
            f.write("\n<!-- written while the page was being read -->\n")
        return out
    reader.read_project = writing
    try:
        d = server.project_data(stamp, ())
    finally:
        reader.read_project = real
    return d["files_stamp"] != server.files_stamp(stamp)


STAMP_OK = stamp_before_read()

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

    def opened(f, ms=12000):   # the film read and drawn, nothing reloading: a condition, never a fixed wait
        return {"until": f"typeof D !== 'undefined' && D && PKEY === {key(f)!r} && !RELOADING && !!$('#stage [data-mod]')", "name": f"open {f.name}", "ms": ms}

    def page(f, rid, d):   # the agent sends a page: its JSON, its HTML (bin/vh gate writes both), then it is this round
        return [{"write": str(f / "out" / "review" / f"gate-{rid}.json"), "text": json.dumps(d, ensure_ascii=False)},
                {"write": str(f / "out" / "review" / f"gate-{rid}.html"), "text": "<!doctype html><title>page</title>"},
                {"write": str(f / "out" / "review" / ".current"), "text": f"{rid}\n"}]
    COUNT = "(window.__reloads = 0, (() => { const o = reloadProject; reloadProject = async (...a) => { window.__reloads++; return o(...a); }; })(), true)"
    steps += [
        # bin/vh gate opens a stop at #/p/<key>/gate/<page>: the outline's second page on the outline, its question in the column
        {"go": f"#/p/{key(reopen)}/gate/1b", "after": 200}, opened(reopen), tab, {"eval": WHERE, "name": "reopen_at"},
        {"go": f"#/p/{key(script)}/gate/E1", "after": 200}, opened(script), {"eval": WHERE, "name": "script_at"},
        # opened by Studio itself (not the person's choice), a new page: the page follows it, the address names it, Back returns
        {"go": f"#/p/{key(follow)}/outline/script", "after": 200}, opened(follow), {"eval": "(CHOSE = false, window.__h = history.length, true)", "name": "as studio"},
        *page(follow, "1b", OUTLINE_AGAIN),
        {"until": f"location.hash === '#/p/{key(follow)}/outline' && D.current === '1b' && !RELOADING && !!$('#stage [data-mod=outline]')", "name": "follow_at", "ms": 15000},
        {"eval": "JSON.stringify({ grew: history.length - window.__h })", "name": "follow_history"},
        {"reload": True}, opened(follow), {"eval": WHERE, "name": "follow_reload"},
        {"eval": "(history.back(), true)", "name": "back"},
        {"until": f"location.hash === '#/p/{key(follow)}/outline/script'", "name": "follow_back", "ms": 8000},
        # the person went to 决定 themself: a new page leaves them there, says it is out
        {"go": f"#/p/{key(stay)}/ledger", "after": 200}, opened(stay), *page(stay, "1b", OUTLINE_AGAIN),
        {"until": "D.current === '1b' && !RELOADING", "name": "stay_round", "ms": 15000},
        {"eval": "JSON.stringify({ mod: MOD, hash: decodeURIComponent(location.hash), toast: $('#toast').innerText, now: ($('#colNow') || {}).innerText || '' })", "name": "stay_at"},
        # a page half-written: no new round, no reload for 10 s; once it reads, one follow
        {"go": f"#/p/{key(half)}/outline/script", "after": 200}, opened(half), {"eval": COUNT, "name": "count"},
        {"write": str(half / "out" / "review" / "gate-E2.json"), "text": '{"summary": "配乐安排", "decisions": ['},
        {"write": str(half / "out" / "review" / ".current"), "text": "E2\n"},
        {"wait": 10000}, {"eval": "JSON.stringify({ reloads: window.__reloads, current: D.current, mod: MOD, toast: $('#toast').innerText })", "name": "half_wait"},
        # scrolled down the script, an unrelated NOTES.md change: read again, the same place on the page
        {"go": f"#/p/{key(scroll)}/outline/script", "after": 200}, opened(scroll), {"until": "$('#gatePart .gate') && $('#stage').scrollHeight > $('#stage').clientHeight + 450", "name": "scroll_ready", "ms": 8000},
        {"eval": "($('#stage').scrollTop = $('#stage').scrollHeight, window.__st = D.files_stamp, $('#stage').scrollTop)", "name": "scroll_before"},   # (the very bottom: the stop's page part is there)
        {"write": str(scroll / "NOTES.md"), "text": (scroll / "NOTES.md").read_text(encoding="utf-8") + "\n- 又查到一条\n"},
        {"until": "D.files_stamp !== window.__st && !RELOADING", "name": "scroll_reloaded", "ms": 15000}, {"wait": 600},
        {"eval": "$('#stage').scrollTop", "name": "scroll_after"},
        # a radio button picked (focus stays on it) is no typing: the page still follows a change; a text box with a keystroke just now holds it
        tab, {"eval": "(($('.c-cards input[type=radio]') || $('#say')).focus(), window.__st = D.files_stamp, true)", "name": "radio_focus"},
        {"write": str(scroll / "NOTES.md"), "text": (scroll / "NOTES.md").read_text(encoding="utf-8") + "\n- 又查到两条\n"},
        {"until": "D.files_stamp !== window.__st && !RELOADING", "name": "radio_followed", "ms": 15000},
        {"eval": "($('#say').focus(), document.dispatchEvent(new KeyboardEvent('keydown', { key: 'a' })), window.__st = D.files_stamp, true)", "name": "typing"},
        {"write": str(scroll / "NOTES.md"), "text": (scroll / "NOTES.md").read_text(encoding="utf-8") + "\n- 又查到三条\n"},
        {"wait": 6000}, {"eval": "D.files_stamp === window.__st", "name": "typing_held"},
        {"eval": "(LASTKEY = Date.now() - 31000, true)", "name": "typing_idle"},
        {"until": "D.files_stamp !== window.__st && !RELOADING", "name": "typing_released", "ms": 15000},
        # a 400-character summary: two lines above the tabs, whole below
        {"go": f"#/p/{key(longp)}/outline/script", "after": 200}, opened(longp), {"until": "$('#gatePart .round-h')", "name": "long_part", "ms": 8000},
        {"eval": "JSON.stringify({ h: $('.page-sum').getBoundingClientRect().height, lh: parseFloat(getComputedStyle($('.page-sum')).lineHeight), "
                 "tabs: $('nav.subtabs').getBoundingClientRect().top, whole: ($('#gatePart').innerText || '').includes($('.page-sum').getAttribute('title')) })", "name": "long_view"},
        # the stop's page on the outline: clicking the script tab leaves the tab row where it was, and the page's rest comes after
        {"go": f"#/p/{key(tabs)}/outline", "after": 200}, opened(tabs),
        {"eval": "$('nav.subtabs').getBoundingClientRect().top", "name": "tabs_before"},
        {"click": "nav.subtabs a[href$='/outline/script']", "after": 200}, {"until": "$('nav.subtabs [aria-selected=true][href$=\"/script\"]') && $('#gatePart .gate')", "name": "tabs_ready", "ms": 8000},
        {"eval": "JSON.stringify({ top: $('nav.subtabs').getBoundingClientRect().top, body: $('#modBody') && $('#modBody').getBoundingClientRect().top, "
                 "rest: $('#gatePart') && $('#gatePart').getBoundingClientRect().top, script: !!$('nav.subtabs [aria-selected=true][href$=\"/script\"]') })", "name": "tabs_after"},
        # nine parts rewritten to five, notes kept on six of them: each stays, follows its content, or says its place changed or went
        {"go": f"#/p/{key(nine)}/outline", "after": 200}, opened(nine), tab,
        {"eval": "(" + ", ".join(KEEP.format(t=f"seg:{i}", x=f"第 {i} 段的意见", lb=f"大纲 第 {i} 段 {NINE[i - 1][0]}") for i in (1, 3, 4, 5, 7, 9)) + ")", "name": "nine_keep"},
        {"eval": "(FB.items['seg:9'].t = 32, FB.items['seg:3'].t = 8, save(), document.activeElement && document.activeElement.blur(), window.__st = D.files_stamp, true)", "name": "nine_blur"},   # (the times the row gives as a note is kept)
        {"write": str(nine / "BRIEF.md"), "text": five},
        {"until": "D.files_stamp !== window.__st && !RELOADING && document.querySelectorAll('#stage [data-mark^=\"seg:\"]').length === 5", "name": "nine_reloaded", "ms": 15000},
        {"eval": "JSON.stringify({ items: Object.fromEntries(Object.entries(FB.items).map(([k, v]) => [k, { drift: v.drift || '', moved: v.moved || '', label: v.label, t: v.t }])), "
                 "marked: [...document.querySelectorAll('#stage [data-mark^=\"seg:\"].marked')].map((e) => e.dataset.mark), "
                 "block: $('#cMine').innerText, drift_goto: [...document.querySelectorAll('#cMine li.drift')].filter((e) => e.dataset.goto).length, "
                 "sent: payload().items.map((i) => [i.target, i.label]) })", "name": "nine_after"},
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


ra, sa = js("reopen_at"), js("script_at")
check("a stop opens on what it asks about: the outline sent again (no concept cards) on the outline with its question in the column, the script on the "
      "outline's script tab; the address then names that module",
      ra.get("mod") == "outline" and ra.get("hash", "").endswith("/outline") and ra.get("cards") and sa.get("mod") == "outline"
      and sa.get("hash", "").endswith("/outline/script") and sa.get("tab", "").endswith("/script"), [ra, sa])
fr, fh = js("follow_reload"), js("follow_history")
check("a new page while Studio's own opening is on screen: the page follows it, the address names it (a history entry of its own: Back returns), and a "
      "reload stays there", (res.get("follow_at") or {}).get("ok") and fh.get("grew") == 1 and fr.get("mod") == "outline" and fr.get("hash", "").endswith("/outline")
      and (res.get("follow_back") or {}).get("ok"), [res.get("follow_at"), fh, fr, res.get("follow_back")])
sa2 = js("stay_at")
check("a new page while the person is where they went themself: the page stays there, says the page is out, and the line above the tabs has the way to it",
      (res.get("stay_round") or {}).get("ok") and sa2.get("mod") == "ledger" and sa2.get("hash", "").endswith("/ledger") and "大纲那一页出来了" in sa2.get("toast", "")
      and "去看大纲" in sa2.get("now", ""), [res.get("stay_round"), sa2])
hw = js("half_wait")
check("a page half-written: no new round and no word of a new page; at most the one quiet read a file change brings; the page as it was",
      hw.get("reloads", 9) <= 1 and hw.get("current") == "E1" and hw.get("mod") == "outline" and "那一页出来了" not in hw.get("toast", "") and "E2" not in hw.get("toast", ""), hw)
check("the stamp is taken before the film is read: a file written during the read leaves the page one reload behind, never stale for good", STAMP_OK, STAMP_OK)
sb, sa3 = v(res, "scroll_before"), v(res, "scroll_after")
check("an unrelated file change while scrolled to the bottom of the script (the stop's page part below it): the page reads again and stays where it was",
      (res.get("scroll_reloaded") or {}).get("ok") and isinstance(sb, (int, float)) and sb >= 300 and isinstance(sa3, (int, float)) and abs(sa3 - sb) <= 2, [sb, sa3])
check("busy is typing, not focus: a picked radio button does not hold the page back; a text box with a keystroke just now does, and lets go once idle 30 s",
      (res.get("radio_followed") or {}).get("ok") and v(res, "typing_held") is True and (res.get("typing_released") or {}).get("ok"),
      [res.get("radio_followed"), v(res, "typing_held"), res.get("typing_released")])
lv = js("long_view")
check("a 400-character summary keeps to two lines above the tabs, and is there whole below", lv.get("h", 1e9) <= 2 * lv.get("lh", 0) + 2 and lv.get("tabs", 1e9) < 260
      and lv.get("whole"), lv)
tb, ta = v(res, "tabs_before"), js("tabs_after")
check("the script tab clicked on a stop's page: the tab row is not pushed down, the tab's content starts right under it, and the page's decided, "
      "delegated and appendices come after that content",
      isinstance(tb, (int, float)) and ta.get("script") and ta.get("top", 1e9) <= tb + 4 and ta.get("body") and ta["body"] - ta["top"] < 80
      and ta.get("rest") and ta["rest"] > ta["body"], [tb, ta])
na = js("nine_after")
it, sent = na.get("items") or {}, dict(tuple(x) for x in na.get("sent") or [])
was = {k.split("~")[0]: x for k, x in it.items() if "~was" in k}
ok = ((res.get("nine_reloaded") or {}).get("ok")
      and "seg:1" in it and not it["seg:1"]["drift"]                                        # the same content at the same place: stays
      and it.get("seg:2", {}).get("moved") == "2" and "第 2 段 转一圈" in it["seg:2"]["label"] and it["seg:2"].get("t") == 4   # moved up from 3: goes with it, takes its time, says so
      and it.get("seg:4", {}).get("moved") == "4" and "第 4 段 收尾" in it["seg:4"]["label"] and it["seg:4"].get("t") == 12   # moved up from 9 (a reorder)
      and was.get("seg:4", {}).get("drift") == "changed"                                     # renamed: never drawn on what took its place
      and was.get("seg:5", {}).get("drift") == "changed"                                     # its words rewritten at the same place: changed
      and was.get("seg:7", {}).get("drift") == "gone"                                        # removed
      and "seg:3" not in na.get("marked", []) and "seg:5" not in na.get("marked", []) and set(na.get("marked", [])) == {"seg:1", "seg:2", "seg:4"}
      and na.get("drift_goto") == 0
      and "原来是第 3 段" in na.get("block", "") and "原来是第 9 段" in na.get("block", "") and "0:32" not in na.get("block", "") and "第 4 段 月亮（这一处后来改了）" in na.get("block", "") and "第 5 段 太阳（这一处后来改了）" in na.get("block", "")
      and "不在了" in na.get("block", "")
      and any("月亮" in lb and "这一处后来改了" in lb for lb in sent.values()))
check("an outline of nine parts rewritten to five (one removed in the middle, two in another order, one renamed, one's words rewritten): a note on the "
      "same part stays; one whose part moved goes with it, takes its number and time, and says once where it was; one whose part was renamed or rewritten is never drawn on what took its place, "
      "quotes what it was written on, goes nowhere on a click, and is sent saying so; one on a removed part says it is gone", ok, na)
print("end", flush=True)
