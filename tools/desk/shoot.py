"""Screenshots of the console, at the size a person sees it, for a review from pictures alone (a development aid: not a
bin/vh command, not run by tools/ci.sh).

usage: uv run --no-project --with playwright python3 tools/desk/shoot.py <desk url> <out folder>
           [--project NAME …] [--max N] [--focus NAME]

Start a desk first (bin/vh desk [--root <folder> …]; it prints its address). Playwright drives the Google Chrome this
machine has (channel "chrome": nothing is downloaded). Every picture is <n>-<name>.png in the out folder, 1440 x 900 at
2x (a phone: 390 x 844 at 3x), and index.json says what each one shows. The pictures:
  - the space (every film), in Chinese;
  - each film (the ones --project names, else the first --max of the space's list, 3 by default): as it opens, then
    each module its rail links to; a module whose column scrolls gets a second picture a screen further down;
  - on the focus film (--focus, else the first one waiting for its person, else the first): the cut module with a shot
    selected (→), in its three layouts, and the summary a submit shows first (closed again with its cancel button);
  - the three themes, on the focus film's cut and its concept;
  - English: the space and the focus film;
  - a phone: the space, and the focus film three screens down.
Nothing is sent: every POST to the desk's feedback is blocked, so a summary opened by mistake cannot submit. Buttons
are found by their words (both languages, a few names each, in LABELS) or their role, never by where they sit, so a
page laid out anew still works; a step whose button is not there is written in index.json as skipped, with why, and
the rest go on. Exit: 0 the pictures taken (some may be skipped) · 1 the desk did not answer · 2 usage, or no
Playwright or no Chrome (said in a line).
"""
import argparse, json, re, sys, time, urllib.request
from pathlib import Path

# the words the console's buttons carry (tools/desk/static/core.js), Chinese and English: the first that is there is used
LABELS = {
    "lang_en": ["EN", "Switch to English"],
    "lang_zh": ["中", "切换到中文"],
    "themes": ["主题", "Theme"],
    "theme": {"darkfield": ["暗场", "Darkfield"], "prism": ["棱镜", "Prism"], "bridge": ["舰桥", "Bridge"]},
    "layout": {"review": ["审片", "Review"], "fine": ["精修", "Fine cut"], "sound": ["听声音", "Listen"]},
    "submit": ["发出去", "Send"],   # the round's button, with what goes after it: 发出去（2 条意见 · 1 个选择）
    "cancel": ["再看看", "Keep looking"],
}
MODULE_NAMES = {"idea": "立意", "outline": "大纲", "board": "分镜", "sound": "声音", "cut": "成片", "ship": "交付",
                "assets": "素材", "ledger": "决定"}
DESK = (1440, 900, 2)
PHONE = (390, 844, 3)


class Shooter:
    def __init__(self, base, out):
        self.base, self.out = base.rstrip("/"), out
        self.pictures, self.skipped = [], []

    def name(self, stem):
        return f"{len(self.pictures) + 1:02d}-{re.sub(r'[^A-Za-z0-9._-]+', '-', stem).strip('-')}.png"

    def settle(self, page, s=1.2):
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(int(s * 1000))

    def shot(self, page, stem, what, scroll=True, **about):
        f = self.name(stem)
        page.screenshot(path=str(self.out / f))
        vp = page.viewport_size or {}
        self.pictures.append({"file": f, "what": what, "url": page.url.replace(self.base, ""), "size": [vp.get("width"), vp.get("height")], **about})
        if scroll and self.scroll_inner(page):
            g = self.name(stem + "-scrolled")
            page.screenshot(path=str(self.out / g))
            self.pictures.append({"file": g, "what": what + " (the same page, a screen further down)", "url": page.url.replace(self.base, ""),
                                  "size": [vp.get("width"), vp.get("height")], **about})
            page.evaluate("() => document.querySelectorAll('*').forEach((e) => { if (e.scrollTop) e.scrollTop = 0; })")
            page.wait_for_timeout(300)

    def scroll_inner(self, page):
        """Scroll the first tall column that scrolls inside the page by most of a screen; True when it moved."""
        moved = page.evaluate("""() => {
          const els = [...document.querySelectorAll('main, main *, [role=main], [role=main] *')].filter((e) => {
            const s = getComputedStyle(e); return /(auto|scroll)/.test(s.overflowY) && e.scrollHeight > e.clientHeight + 200 && e.clientHeight > 300; });
          if (!els.length) return 0;
          const e = els[0], before = e.scrollTop; e.scrollTop = before + e.clientHeight * 0.9; return e.scrollTop - before; }""")
        if moved and moved > 150:
            page.wait_for_timeout(500)
            return True
        return False

    def skip(self, what, why):
        self.skipped.append({"what": what, "why": why})
        print(f"  skipped: {what} ({why})", file=sys.stderr)

    def find(self, page, names, roles=("button", "tab", "radio", "link", "menuitem")):
        """The first visible element whose accessible name or title is one of names, by role, then by its text."""
        for n in names:
            exact = re.compile(rf"^\s*{re.escape(n)}(?:（[^）]*）| \([^)]*\))?\s*$")   # a count after the name is the same button
            for role in roles:
                loc = page.get_by_role(role, name=exact)
                for i in range(min(loc.count(), 5)):
                    if loc.nth(i).is_visible():
                        return loc.nth(i)
            for loc in (page.get_by_title(n, exact=True), page.get_by_text(n, exact=True)):
                for i in range(min(loc.count(), 5)):
                    if loc.nth(i).is_visible():
                        return loc.nth(i)
        return None

    def click(self, page, names, what, settle=0.8):
        el = self.find(page, names)
        if el is None:
            self.skip(what, f"no button named {' / '.join(names)}")
            return False
        el.click()
        self.settle(page, settle)
        return True

    def goto(self, page, route, settle=1.6):
        page.goto(f"{self.base}/{route}")
        self.settle(page, settle)


def projects(base):
    with urllib.request.urlopen(f"{base}/api/projects", timeout=20) as r:
        return json.loads(r.read().decode("utf-8")).get("projects", [])


def modules_of(page, key):
    """The modules the rail links to for this film, in the rail's order (#/p/<key>/<module>)."""
    hrefs = page.evaluate("(k) => [...document.querySelectorAll('a[href]')].map((a) => a.getAttribute('href')).filter((h) => h.startsWith('#/p/' + k + '/'))", key)
    out = []
    for h in hrefs:
        m = h.split("/")[3] if len(h.split("/")) > 3 else ""
        if m and m not in out and m != "gate":
            out.append(m)
    return out or list(MODULE_NAMES)


def main():
    ap = argparse.ArgumentParser(prog="tools/desk/shoot.py", description="Screenshots of the console for a review from pictures alone.")
    ap.add_argument("url", help="the desk's address, as bin/vh desk prints it")
    ap.add_argument("out", help="the folder for the pictures and index.json")
    ap.add_argument("--project", action="append", default=[], help="a film to take, by its folder name (repeat it); default: the space's first --max")
    ap.add_argument("--max", type=int, default=3)
    ap.add_argument("--focus", help="the film for the layouts, themes, English and phone pictures")
    a = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("shoot: needs Playwright: uv run --no-project --with playwright python3 tools/desk/shoot.py …", file=sys.stderr)
        sys.exit(2)
    base = re.sub(r"[#?].*$", "", a.url).rstrip("/")
    try:
        rows = projects(base)
    except Exception as e:
        print(f"shoot: {base}/api/projects did not answer ({e}): is bin/vh desk running there?", file=sys.stderr)
        sys.exit(1)
    if a.project:
        films = [r for want in a.project for r in rows if r.get("name") == want or r.get("key", "").startswith(want + "~")]
        for want in a.project:
            if not any(r.get("name") == want or r.get("key", "").startswith(want + "~") for r in rows):
                print(f"shoot: no film named {want} in the desk's space", file=sys.stderr)
    else:
        films = rows[:a.max]
    focus = next((r for r in rows if a.focus and (r.get("name") == a.focus or r.get("key", "").startswith(a.focus + "~"))), None) \
        or next((r for r in films if r.get("waiting")), None) or (films[0] if films else None)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    s = Shooter(base, out)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception as e:   # Playwright's own error: no Chrome where it looks, or one that would not start
            first = str(e).strip().splitlines()[0] if str(e).strip() else type(e).__name__
            print(f"shoot: needs Google Chrome installed (Playwright starts the system Chrome, channel \"chrome\"; it downloads "
                  f"none): {first[:200]}", file=sys.stderr)
            sys.exit(2)

        def context(size, **k):
            w, h, dpr = size
            ctx = browser.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, locale="zh-CN", **k)
            ctx.route(re.compile(r".*/feedback(\?.*)?$"), lambda route: route.abort() if route.request.method == "POST" else route.continue_())
            return ctx

        page = context(DESK).new_page()
        s.goto(page, "", 2.5)
        s.shot(page, "space", "the space: every film, the ones waiting for you first", lang="zh")
        for r in films:
            k, title = r["key"], r.get("title") or r.get("name")
            s.goto(page, f"#/p/{k}", 2.5)
            s.shot(page, f"{r.get('name')}-open", f"{title}: as it opens", film=r.get("name"))
            for m in modules_of(page, k):
                s.goto(page, f"#/p/{k}/{m}", 1.8)
                s.shot(page, f"{r.get('name')}-{m}", f"{title}: the {MODULE_NAMES.get(m, m)} module ({m})", film=r.get("name"), module=m)
        if focus:
            k, title, nm = focus["key"], focus.get("title") or focus.get("name"), focus.get("name")
            s.goto(page, f"#/p/{k}/cut", 2.5)
            page.locator("body").press("ArrowRight")
            s.settle(page, 0.8)
            s.shot(page, f"{nm}-cut-shot", f"{title}: the cut module with the next shot selected (→); the note box faces it", scroll=False, film=nm, module="cut")
            for lay, names in LABELS["layout"].items():
                if s.click(page, names, f"{title}: the cut's layout {names[0]}"):
                    s.shot(page, f"{nm}-cut-{lay}", f"{title}: the cut module, layout {names[0]}", scroll=False, film=nm, module="cut", layout=lay)
            if s.click(page, LABELS["layout"]["review"], "back to the review layout", 0.5) and s.click(page, LABELS["submit"], f"{title}: the summary before submitting"):
                s.shot(page, f"{nm}-submit-summary", f"{title}: what a submit shows first, before anything is sent (nothing was sent)", scroll=False, film=nm)
                if not s.click(page, LABELS["cancel"], "closing the summary", 0.5):
                    page.keyboard.press("Escape")
            for theme, names in LABELS["theme"].items():
                if not s.click(page, LABELS["themes"], "the theme menu", 0.3) or not s.click(page, names, f"the theme {names[0]}", 0.8):
                    continue
                page.keyboard.press("Escape")
                page.evaluate("() => document.querySelectorAll('details[open]').forEach((d) => d.removeAttribute('open'))")
                for m in ("cut", "idea"):
                    s.goto(page, f"#/p/{k}/{m}", 1.8)
                    s.shot(page, f"{nm}-{m}-{theme}", f"{title}: the {MODULE_NAMES[m]} module in the theme {names[0]}", scroll=False, film=nm, module=m, theme=theme)
                s.goto(page, f"#/p/{k}/cut", 1.0)
            if s.click(page, LABELS["themes"], "the theme menu", 0.3):
                s.click(page, LABELS["theme"]["darkfield"], "back to the default theme", 0.3)
                page.evaluate("() => document.querySelectorAll('details[open]').forEach((d) => d.removeAttribute('open'))")
            if s.click(page, LABELS["lang_en"], "English"):
                s.shot(page, f"{nm}-open-en", f"{title}: the cut module in English", scroll=False, film=nm, lang="en")
                s.goto(page, "", 2.0)
                s.shot(page, "space-en", "the space in English", scroll=False, lang="en")
                s.click(page, LABELS["lang_zh"], "back to Chinese")
        phone = context(PHONE, is_mobile=True, has_touch=True).new_page()
        s.goto(phone, "", 2.5)
        s.shot(phone, "phone-space", "a phone (390 wide): the space", scroll=False)
        if focus:
            s.goto(phone, f"#/p/{focus['key']}", 2.5)
            for i in range(3):
                s.shot(phone, f"phone-{focus.get('name')}-{i + 1}", f"a phone: {focus.get('title') or focus.get('name')}, screen {i + 1} from the top", scroll=False, film=focus.get("name"))
                phone.mouse.wheel(0, 780)
                phone.wait_for_timeout(700)
        browser.close()
    index = {"version": 1, "desk": base, "made": time.strftime("%Y-%m-%d %H:%M:%S"), "films": [r.get("name") for r in films],
             "focus": focus.get("name") if focus else None, "pictures": s.pictures, "skipped": s.skipped}
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"{len(s.pictures)} pictures in {out}" + (f", {len(s.skipped)} step(s) skipped (index.json says why)" if s.skipped else ""))


if __name__ == "__main__":
    main()
