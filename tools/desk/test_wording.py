"""The words a person reads, both languages: Studio's three word tables (core.js, modules.js, agent.js, read in node), bin/vh
status's lines as Studio says them (STATUS_ZH, STATUS_EN), where a film stands (tools/standing.py), the review page's words
and the lines bin/vh gate prints for the person. Each key in both languages; none of the names retired for plainer ones
(tools/desk/README.md). The strings outside the tables (studio.js, ui.js, reader.js, index.html, OVH Studio's shell and
launcher, install.sh) get the same search. Prints a line and exits 0 when they hold, the problems and 1 when not; without
node the tables are not read, said so, and the rest is still searched."""
import json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import gate as G, review as RV, standing as SD   # noqa: E402

# the words a person reads in Studio, the review pages and gate's lines, retired for plainer ones (tools/desk/README.md, 页面上的字):
# a step by its own name (审文案, 看初版), never 站; a note 意见, sent with 发 (发出去), added with 加一条; the AI by its name or "AI",
# never "agent"; the script 文案; codes (①, E3), files and commands stay out of the words
CODE = r"[①②③④⑤⑥⑦⑧⑨]|(?<![A-Za-z0-9_])E[0-5](?![A-Za-z0-9_])"
CIRCLED = re.compile(r"[①②③④⑤⑥⑦⑧⑨]")   # a stop's code that is never code: searched in every string
RETIRED_ZH = re.compile(r"审阅台|控制台|关卡|检查点|这一轮|这一关|点评|反馈|评论|要你定|待你定|点头|待批准|等你点|默认通过|上下文|推理|代理|"
                        r"硬规则|写成意见|记成点评|提交|锁时|样板章|样帧|锁画面|项目|BRIEF|\.md\b|bin/vh|"
                        r"(?i:agent)|站|交给|(?<!提)交(?!付)|记下|对着|脚本|旁白稿|字幕 / 旁白|要看到|动静|随初版|不点就算|" + CODE)
RETIRED_EN = re.compile(r"(?i)\bdesk\b|\bconsole\b|\bgate\b|checkpoint|\bround\b|\bcomments?\b|feedback|submission|\bsubmit|\(s\)|untouched|"
                        r"to allow|\bcontext\b|\bproxy\b|hard rule|conversation|bin/vh|\.md\b|timing lock|sample chapter|first cut|"
                        r"\bagents?\b|\b(?:this|that|each|every|a) stop\b|add note|should (?:see|land)|last activity|captions / narration|" + CODE)
WORDS_KEEP = {"proj_ph"}   # the film's folder inside a command, in that command's tooltip (<项目> / <project>)
WORDS_OK = {"smp_launch_say": "我的开源项目"}   # a word a key may say: the homepage's sentence names the person's software, not a film
TERMINAL_OK = re.compile(r"bin/vh|\.md\b|\bproxy\b")   # a terminal line may name the command to run, a file, the network's proxy
CJK = re.compile(r"[一-鿿]")
PROSE = re.compile(r"[A-Za-z]{2,}[,:;.!?]? [A-Za-z]{2,}")   # English words a space apart: not an identifier, a key or a file name
PAGES = ["tools/desk/static/studio.js", "tools/desk/static/settings.js", "tools/desk/static/ui.js", "tools/desk/static/reader.js", "tools/desk/static/index.html",
         "tools/desk/shell/main.js", "tools/desk/launcher/shell-boot.js"]
TERMINAL = ["install.sh", "tools/desk/launcher/studio-launch.sh", "tools/desk/launcher/studio.applescript"]


def js_strings(text):
    """A script's string literals, its comments and regular expressions left out; a template's ${…} becomes a space and the
    strings inside it are strings of their own."""
    out, n = [], len(text)

    def regex_here(i):   # a / that opens a regular expression: after an operator, an opening bracket, or a keyword
        j = i - 1
        while j >= 0 and text[j] in " \t\n":
            j -= 1
        return j < 0 or text[j] in "(,=:[!&|?{};+-*%<>~^" or re.search(r"\b(return|typeof|case|in|of)$", text[max(0, j - 6):j + 1])

    def code(i, closing=False):   # code from i; with closing, up to the } that ends a ${…}
        depth = 0
        while i < n:
            c = text[i]
            if text.startswith("//", i):
                j = text.find("\n", i)
                i = n if j < 0 else j
            elif text.startswith("/*", i):
                j = text.find("*/", i + 2)
                i = n if j < 0 else j + 2
            elif c in "\"'":
                j, buf = i + 1, []
                while j < n and text[j] != c and text[j] != "\n":
                    buf.append(text[j:j + 2] if text[j] == "\\" else text[j])
                    j += 2 if text[j] == "\\" else 1
                out.append("".join(buf))
                i = j + 1
            elif c == "`":
                i = template(i + 1)
            elif c == "/" and regex_here(i):
                j, cls = i + 1, False
                while j < n and text[j] != "\n" and (cls or text[j] != "/"):
                    cls = (cls or text[j] == "[") and text[j] != "]"
                    j += 2 if text[j] == "\\" else 1
                i = j + 1
            elif closing and c == "{":
                depth, i = depth + 1, i + 1
            elif closing and c == "}":
                if not depth:
                    return i + 1
                depth, i = depth - 1, i + 1
            else:
                i += 1
        return i

    def template(i):
        buf = []
        while i < n and text[i] != "`":
            if text[i] == "\\":
                buf.append(text[i:i + 2])
                i += 2
            elif text.startswith("${", i):
                buf.append(" ")
                i = code(i + 2, closing=True)
            else:
                buf.append(text[i])
                i += 1
        out.append("".join(buf))
        return i + 1

    code(0)
    return out


def page_strings(path):
    """What a page or script shows: a script's strings; an HTML page's text, its titles, labels and placeholders, and its
    scripts' strings."""
    text = (ROOT / path).read_text(encoding="utf-8")
    if not path.endswith(".html"):
        return js_strings(text)
    scripts = re.findall(r"<script\b[^>]*>(.*?)</script>", text, re.S)
    body = re.sub(r"<(script|style)\b[^>]*>.*?</\1>|<!--.*?-->", " ", text, flags=re.S)
    attrs = re.findall(r'\b(?:title|aria-label|placeholder|alt)="([^"]*)"', body)
    return [x for x in re.split(r"<[^>]+>", body) if x.strip()] + attrs + [s for x in scripts for s in js_strings(x)]


def terminal_lines(path):
    """What a shell script or an AppleScript says to the person: the lines that print or show something, its comments left out."""
    out = []
    for line in (ROOT / path).read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith(("#", "--")) or not re.search(r"\b(echo|say|printf|display (dialog|alert)|warn|die)\b", s):
            continue
        out += [m.group(1) or m.group(2) for m in re.finditer(r'"((?:[^"\\]|\\.)*)"|\'([^\']*)\'', s)]
    return out


def searched(where, strings, terminal=False):
    """The retired names in strings a person reads: Chinese ones in a string with Chinese in it, English ones in English prose."""
    bad = []
    for x in strings:
        x = re.sub(r"<[^>]+>", " ", x)
        for rx in ((RETIRED_ZH,) if CJK.search(x) else (RETIRED_EN,) if PROSE.search(x) else (CIRCLED,)):
            for m in rx.finditer(x):
                if not (terminal and TERMINAL_OK.fullmatch(m.group(0))):
                    bad.append(f"{where} says {m.group(0)!r}: {x.strip()[:60]}")
                    break
    return bad


def tables(node):
    """Studio's three word tables, both languages, from node: {name: {zh: {...}, en: {...}}}, or an error string."""
    prog = r"""
const vm = require("vm"), fs = require("fs");
const doc = { querySelector: () => null, querySelectorAll: () => [], documentElement: { lang: "" }, addEventListener() {} };
const g = vm.createContext({ console, document: doc, window: {}, localStorage: { getItem: () => null, setItem() {} }, setTimeout, clearInterval, setInterval,
  requestAnimationFrame: () => 0, matchMedia: () => ({ matches: false }) });
for (const f of ["core.js", "modules.js", "agent.js"]) vm.runInContext(fs.readFileSync(process.argv[1] + "/" + f, "utf8"), g);
vm.runInContext("this.__T = { STR, MSTR, ASTR };", g);
console.log(JSON.stringify(g.__T));
"""
    out = subprocess.run([node, "-e", prog, str(HERE / "static")], capture_output=True, text=True, timeout=30)
    if out.returncode:
        return "the word tables did not load in node: " + out.stderr.strip()[-300:]
    try:
        return json.loads(out.stdout)
    except ValueError:
        return "the word tables did not load in node: " + out.stdout.strip()[-200:]


def wording_check():
    """Every string a person reads, both languages; the problems in a line, or None when there are none."""
    bad, node = [], shutil.which("node")
    tb_all = tables(node) if node else {}
    if isinstance(tb_all, str):
        bad.append(tb_all)
        tb_all = {}
    for name, tb in tb_all.items():
        flat = {}
        for lang in ("zh", "en"):
            if not isinstance(tb.get(lang), dict):
                bad.append(f"{name} has no {lang} table")
                continue
            for k, v in tb[lang].items():
                for kk, vv in (v.items() if isinstance(v, dict) else [(None, v)]):
                    flat.setdefault((k, kk), {})[lang] = vv
        for (k, kk), v in flat.items():
            key = k + ("." + kk if kk else "")
            if set(v) != {"zh", "en"}:
                bad.append(f"{name}.{key} only in {'/'.join(v)}")
            elif k not in WORDS_KEEP:
                for lang, rx in (("zh", RETIRED_ZH), ("en", RETIRED_EN)):
                    m = rx.search(str(v[lang]).replace(WORDS_OK.get(k, "\0"), ""))
                    if m:
                        bad.append(f"{name}.{key} ({lang}) says {m.group(0)!r}")
    core = (HERE / "static" / "core.js").read_text(encoding="utf-8")
    for table, rx in (("STATUS_ZH", RETIRED_ZH), ("STATUS_EN", RETIRED_EN)):
        part = core.split(f"const {table} = [", 1)[1].split("];", 1)[0]
        for m in re.finditer(r'=>\s*(["`])(.*?)\1', part):
            w = rx.search(re.sub(r"\$\{[^}]*\}", "", m.group(2)))
            if w:
                bad.append(f"{table} says {w.group(0)!r}: {m.group(2)[:60]}")
    for k, v in SD.WORDS.items():
        if len(v) < 2:
            bad.append(f"standing {k} only in zh")
        elif not k.startswith("say."):   # the words a button sends to the agent, as the person's own message: they name bin/vh status for it
            for i, x in enumerate(v):
                m = (RETIRED_ZH if i == 0 else RETIRED_EN).search(x)
                if m:
                    bad.append(f"standing {k} ({'zh' if i == 0 else 'en'}) says {m.group(0)!r}")
    for lang, rx in (("zh", RETIRED_ZH), ("en", RETIRED_EN)):
        for k, v in list(RV.T.get(lang, {}).items()) + list(G.SAY.get(lang, {}).items()):
            if k == "warn":   # the page's own rule breaks, for the agent: a page with any goes to nobody
                continue
            for x in (v if isinstance(v, tuple) else (v,)):
                m = rx.search(re.sub(r"<[^>]+>", "", str(x)))
                if m:
                    bad.append(f"review/gate {k} ({lang}) says {m.group(0)!r}")
    for what, t in (("review page", RV.T), ("gate's lines", G.SAY)):
        if set(t.get("zh", {})) != set(t.get("en", {})):
            bad.append(f"{what}: keys in one language only: {sorted(set(t.get('zh', {})) ^ set(t.get('en', {})))}")
    for p in PAGES:
        bad += searched(p, page_strings(p))
    for p in TERMINAL:
        bad += searched(p, terminal_lines(p), terminal=True)
    return "; ".join(bad[:20]) + (f" … ({len(bad)} in all)" if len(bad) > 20 else "") if bad else None


def wall_check(tb_all):
    """Studio's sample wall (studio.js SAMPLES, core.js smp_*, server.py SAMPLES) says what the homepage's showcase says
    (docs/site/index.html #films): the same films in the same order, each length, and each "make one like this" sentence word
    for word in both languages; every style and recipe a sentence names is in the repo; every poster is there."""
    import ast
    tree = ast.parse((HERE / "server.py").read_text(encoding="utf-8"))
    SAMPLES = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SAMPLES")
    bad, site = [], (ROOT / "docs/site/index.html").read_text(encoding="utf-8")
    films = re.findall(r'<figure class="(film[^"]*)"(.*?)</figure>', site.split('id="films"', 1)[1].split("</section>", 1)[0], re.S)
    js = (HERE / "static" / "studio.js").read_text(encoding="utf-8").split("const SAMPLES = [", 1)[1].split("];", 1)[0]
    rows = re.findall(r'\{ id: "(\w+)", secs: ([\d.]+), w: (\d+), h: (\d+)(?:, style: "([\w-]+)")? \}', js)
    if [r[0] for r in rows] != list(SAMPLES):
        bad.append(f"studio.js SAMPLES {[r[0] for r in rows]} and server.py SAMPLES {list(SAMPLES)} name different films")
    if len(rows) != len(films):
        bad.append(f"the wall has {len(rows)} films, the homepage {len(films)}")
    styles = {d.name for d in (ROOT / "styles").iterdir() if (d / "tokens.json").is_file()}
    recipes = {m.group(1) for f in (ROOT / "recipes").rglob("*.md") for m in [re.search(r"^id: ([\w-]+)$", f.read_text(encoding="utf-8"), re.M)] if m}
    for (sid, secs, w, h, style), (cls, fig) in zip(rows, films):
        small = re.search(r'<small><span lang="en">[^<·]*· ([\d.]+) s', fig)
        if not small or float(small.group(1)) != float(secs):
            bad.append(f"{sid}: {secs} s here, {small and small.group(1)} s on the homepage")
        if (int(h) > int(w)) != ("tall" in cls.split()):
            bad.append(f"{sid}: vertical here and not on the homepage, or the other way round")
        for lang in ("zh", "en"):
            say = (tb_all.get("STR", {}).get(lang) or {}).get(f"smp_{sid}_say")
            site_say = re.search(rf'<span data-copy-text lang="{lang}">(.*?)</span>', fig)
            if say is None or not site_say or say != site_say.group(1):
                bad.append(f"{sid} ({lang}): the sentence is not the homepage's: {str(say)[:50]!r} / {site_say and site_say.group(1)[:50]!r}")
            for st in re.findall(r"styles/([\w-]+)", say or ""):
                if st not in styles:
                    bad.append(f"{sid} ({lang}) names a style that is not there: {st}")
            if style and f"styles/{style}" not in (say or ""):
                bad.append(f"{sid} ({lang}): the card's style {style} is not in its sentence")
            named = re.search(r"(?:recipes|配方) (.+?)(?:，| for )", say or "")
            for rc in re.findall(r"[a-z]+(?:-[a-z]+)+", named.group(1) if named else ""):
                if rc not in recipes:
                    bad.append(f"{sid} ({lang}) names a recipe that is not there: {rc}")
    for sid, (poster, _film) in SAMPLES.items():
        if not (ROOT / poster).is_file():
            bad.append(f"{sid}: no poster at {poster}")
    return bad


if __name__ == "__main__":
    r = wording_check()
    if shutil.which("node"):
        tb = tables(shutil.which("node"))
        w = wall_check(tb) if isinstance(tb, dict) else []
        if w:
            r = "; ".join(([r] if r else []) + w)
    if r:
        print(r)
        sys.exit(1)
    print("every key in both languages, none of the retired names" + ("; the sample wall says what the homepage says" if shutil.which("node") else " (no node: Studio's word tables and the sample wall not read)"))
