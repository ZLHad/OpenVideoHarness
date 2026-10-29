"""The README files and the homepage against the repo: the counts they state, the files they link, the two languages
side by side (stdlib only).

usage: python3 tools/readme.py          the counts, from the repo: what to write when a README or the homepage says one
       python3 tools/readme.py check    the pages below against the repo (tools/ci.sh)

check reads README.md, README.zh-CN.md and docs/assets/overview.en.svg / overview.zh.svg:
  - counts: every phrase like "32 styles" / "32 种风格" (COUNT_PHRASES) states the repo's number, and each page states
    the counts REQUIRED lists for it, so a reworded sentence cannot leave its number unchecked;
  - links: every relative link and image is a file or folder in the repo, and a #anchor on a markdown page is one of
    that page's headings (GitHub's anchors);
  - the two READMEs: as many sections (##) each, and the same relative links and images once the language is taken out
    of their names (README.zh-CN.md is README.md, docs/research/en/x is docs/research/x, overview.zh.svg is overview.svg).
Links to the web are not fetched (CI runs offline). Exit status: 0 all good, 1 a problem (each said), 2 usage.
"""
import ast, json, os, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

EN_WORDS = {w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
ZH_DIGITS = {c: i for i, c in enumerate("零一二三四五六七八九")} | {"两": 2, "十": 10}


def number(word):
    """'32', 'five' or '五' → 32, 5, 5; None when it is not a number this checker reads."""
    w = word.strip().lower()
    if w.isdigit():
        return int(w)
    if w in EN_WORDS:
        return EN_WORDS[w]
    if w and all(c in ZH_DIGITS for c in w):   # 五, 十, 十四, 三十七
        if w == "十":
            return 10
        if "十" in w:
            tens, _, ones = w.partition("十")
            return (ZH_DIGITS[tens] if tens else 1) * 10 + (ZH_DIGITS[ones] if ones else 0)
        return ZH_DIGITS[w] if len(w) == 1 else None
    return None


# ── the counts, from the repo ──────────────────────────────────────────────────────────────────────────────────────

def _section_lines(path, start, stop):
    """The lines of a markdown file from the heading `start` up to the next heading of its level (`stop` a prefix)."""
    out, on = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(start):
            on = True
            continue
        if on and line.startswith(stop):
            break
        if on:
            out.append(line)
    return out


def counts():
    import recipes   # tools/recipes.py: the library's own loader (recipe, sequence and grammar cards by their kind)
    kinds = {}
    for _, fm in recipes.load_library().values():
        k = fm.get("kind", "recipe")
        kinds[k] = kinds.get(k, 0) + 1
    sfx_lib = None
    for node in ast.walk(ast.parse((ROOT / "tools/audio/sfx.py").read_text(encoding="utf-8"))):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "LIB" for t in node.targets) and isinstance(node.value, ast.Dict):
            sfx_lib = len(node.value.keys)
    checklist = _section_lines(ROOT / "templates/TASTE_CHECKLIST.md", "## 检查项", "## ")
    scoring = _section_lines(ROOT / "templates/TASTE_CHECKLIST.md", "## 打分层", "## ")
    table = []
    for line in scoring:   # the eight dimensions: the rows of the table whose header starts with | 维度 |
        if line.strip().startswith("| 维度 |"):
            table = ["in"]
        elif table and line.strip().startswith("|") and not line.strip().startswith("|---"):
            table.append(line)
        elif table and table[0] == "in" and len(table) > 1 and not line.strip().startswith("|"):
            break
    fetch = (ROOT / "references/fetch.sh").read_text(encoding="utf-8")
    return {
        "commands": len(json.loads((ROOT / "tools/commands.json").read_text(encoding="utf-8"))["commands"]),
        "styles": sum(1 for p in (ROOT / "styles").glob("*/STYLE.md") if not p.parent.name.startswith("_")),
        "recipes": kinds.get("recipe", 0),
        "sequences": kinds.get("sequence", 0),
        "grammar": kinds.get("grammar", 0),
        "components": sum(1 for p in (ROOT / "components").glob("*/slots.json")),
        "showcase": sum(1 for p in (ROOT / "showcase").glob("*/README.md")),
        "types": sum(1 for p in (ROOT / "video-types").glob("[0-9][0-9]-*.md")),
        "cases": sum(1 for p in (ROOT / "cases").glob("*.md") if p.name != "README.md"),
        "playbook": sum(1 for p in (ROOT / "playbook").glob("[0-9][0-9]-*.md")),
        "templates": sum(1 for p in (ROOT / "templates").glob("*.md")),
        "refs": len(re.findall(r"^(?:full|sparse|textonly)\s+\S+/\S+\s+\S+", fetch, re.M)),
        "modules": len(json.loads((ROOT / "tools/modules.json").read_text(encoding="utf-8"))["modules"]),
        "sfx": sfx_lib or 0,
        "checklist": sum(1 for line in checklist if re.match(r"\d+\. ", line)),
        "scores": len(table) - 1 if table else 0,
    }


WHAT = {   # what each count is, for the listing
    "commands": "bin/vh commands (tools/commands.json)",
    "styles": "style presets (styles/<slug>/STYLE.md)",
    "recipes": "shot recipes (recipes/<family>/, kind recipe)",
    "sequences": "whole-film skeletons (recipes/sequences/, kind sequence)",
    "grammar": "shot-grammar cards (recipes/shot/, kind grammar)",
    "components": "motion components (components/<name>/slots.json)",
    "showcase": "showcase films (showcase/<film>/README.md)",
    "types": "video types (video-types/NN-*.md)",
    "cases": "case studies (cases/*.md but README.md)",
    "playbook": "playbook docs (playbook/NN-*.md)",
    "templates": "project templates (templates/*.md)",
    "refs": "read-only reference repos (references/fetch.sh)",
    "modules": "outside modules (tools/modules.json)",
    "sfx": "built-in synthesized sound effects (tools/audio/sfx.py LIB)",
    "checklist": "taste checklist items (templates/TASTE_CHECKLIST.md 检查项)",
    "scores": "scoring dimensions (templates/TASTE_CHECKLIST.md 打分层)",
}

# ── where the pages state them ─────────────────────────────────────────────────────────────────────────────────────
# Each phrase captures a number (digits, or an English or Chinese number word); every match must be the count. Keep a
# phrase narrow enough that it cannot catch another number (第 09 类 is a type's number, not the count of types).
N = r"(\d+|[a-z]+|[零一二两三四五六七八九十]+)"
COUNT_PHRASES = {
    "commands": [rf"\b{N} commands\b", rf"{N} 条命令"],
    "styles": [rf"\b{N} styles\b", rf"\b{N}-style\b", rf"{N} 种风格"],
    "recipes": [rf"\b{N} shot recipes\b", rf"{N} 张镜头配方"],
    "sequences": [rf"\b{N} whole-film skeletons\b", rf"{N} 条全片骨架"],
    "grammar": [rf"\b{N} shot-grammar cards\b", rf"{N} 张镜头语法卡"],
    "components": [rf"\b{N} (?:motion )?components\b", rf"{N} 个(?:动效)?组件"],
    "showcase": [rf"\b{N} showcase films\b", rf"{N} 支样片"],
    "types": [rf"\b{N} video types\b", rf"(?<!第 ){N} 类视频"],
    "cases": [rf"\b{N} case studies\b", rf"{N} 个案例"],
    "playbook": [rf"\b{N} playbook docs\b", rf"{N} 篇 playbook"],
    "templates": [rf"\b{N} project templates\b", rf"{N} 个项目模板"],
    "refs": [rf"\b{N} (?:read-only )?reference repos\b", rf"{N} 个(?:只读的?)?参考仓库"],
    "modules": [rf"\b{N} outside (?:programs|modules)\b", rf"{N} 个外接模块"],
    "sfx": [rf"\b{N} sound effects\b", rf"{N} 个(?:用代码合成的|代码合成的)?音效"],
    "checklist": [rf"\b{N}-point checklist\b", rf"{N} 条的?清单"],
    "scores": [rf"\bon {N} points\b", rf"按 {N} 项打分"],
}

PAGES = {   # page: the counts it must state somewhere (each is also checked wherever else it appears)
    "README.md": ["commands", "styles", "recipes", "sequences", "grammar", "components", "showcase", "types", "cases",
                  "refs", "modules", "sfx", "checklist", "scores"],
    "README.zh-CN.md": ["commands", "styles", "recipes", "sequences", "grammar", "components", "showcase", "types", "cases",
                        "refs", "modules", "sfx", "checklist", "scores"],
    "docs/assets/overview.en.svg": ["types", "playbook", "styles", "recipes", "components", "cases", "refs", "commands"],
    "docs/assets/overview.zh.svg": ["types", "playbook", "styles", "recipes", "components", "cases", "refs", "commands"],
}
READMES = ("README.md", "README.zh-CN.md")


def blank(m):
    """A match replaced by its newlines alone, so the lines after it keep their numbers."""
    return "\n" * m.group(0).count("\n")


def visible_text(path, text):
    """The text a reader sees: a markdown page without its fenced code and HTML comments (line numbers kept); an SVG's
    <text> runs, one a line."""
    if path.suffix == ".svg":
        return "\n".join(re.sub(r"<[^>]+>", "", t) for t in re.findall(r"<text\b[^>]*>(.*?)</text>", text, re.S)).replace("&amp;", "&")
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    return re.sub(r"^```.*?^```", blank, text, flags=re.S | re.M)


def count_problems(have):
    bad = []
    for page, required in PAGES.items():
        p = ROOT / page
        if not p.is_file():
            bad.append(f"{page}: not there")
            continue
        text = visible_text(p, p.read_text(encoding="utf-8"))
        for key, phrases in COUNT_PHRASES.items():
            seen = []
            for pat in phrases:
                for m in re.finditer(pat, text, re.I):
                    n = number(m.group(1))
                    if n is None:
                        continue
                    seen.append(n)
                    if n != have[key]:
                        where = f"line {text.count(chr(10), 0, m.start()) + 1}" if p.suffix == ".md" else "a <text>"
                        bad.append(f"{page} ({where}): \"{m.group(0)}\", but the repo has {have[key]} {WHAT[key]}")
            if key in required and not seen:
                bad.append(f"{page}: states no count of {WHAT[key]} (a phrase in tools/readme.py COUNT_PHRASES: "
                           f"{' or '.join(phrases)}); say it, or take it out of PAGES")
    return bad


# ── links ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def strip_inline(s):
    s = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", s)        # links and images: their text
    s = re.sub(r"<[^>]+>", "", s)                            # inline HTML
    return s.replace("`", "").replace("*", "")


def anchors(path):
    """GitHub's anchors for a markdown page's headings: lowercase, punctuation and symbols but - and _ dropped, spaces
    to -, a repeat numbered -1, -2 …"""
    out, seen, fence = set(), {}, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            fence = not fence
            continue
        m = None if fence else re.match(r"#{1,6}\s+(.*?)\s*#*\s*$", line)
        if not m:
            continue
        s = "".join(c for c in strip_inline(m.group(1)).strip().lower()
                    if c in "-_ " or not unicodedata.category(c)[0] in "PS").replace(" ", "-")
        k = seen.get(s, 0)
        seen[s] = k + 1
        out.add(s if k == 0 else f"{s}-{k}")
    return out


def links(text):
    """The link and image targets of a markdown page (markdown and HTML), outside fenced code."""
    text = re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    found = re.findall(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", text)
    found += re.findall(r"\b(?:href|src)=\"([^\"]+)\"", text)
    return found


def local(target):
    return not re.match(r"[a-z][a-z0-9+.-]*:", target, re.I)   # http:, https:, mailto:, data: … are not files here


def link_problems(page):
    bad = []
    p = ROOT / page
    for t in links(p.read_text(encoding="utf-8")):
        if not local(t):
            continue
        path, _, frag = t.partition("#")
        dest = Path(os.path.normpath(p.parent / path)) if path else p   # lexical: a link may not climb out of the repo
        if not dest.is_relative_to(ROOT) or not dest.exists():
            bad.append(f"{page}: links {t}, which is not in the repo")
            continue
        if frag and dest.is_file() and dest.suffix == ".md" and frag not in anchors(dest):
            bad.append(f"{page}: links {t}, but {dest.relative_to(ROOT)} has no heading with that anchor")
    return bad


def same_file(target):
    """A relative target with its language taken out, for comparing the two READMEs."""
    t = target.partition("#")[0]
    t = re.sub(r"(^|/)README(?:\.zh-CN)?\.md$", r"\1", t)
    t = t.replace("docs/research/en/", "docs/research/")
    t = re.sub(r"\.(?:en|zh)\.(svg|png|jpg)$", r".\1", t)
    return t.rstrip("/") or "."


def pair_problems():
    a, b = ((ROOT / r).read_text(encoding="utf-8") for r in READMES)
    bad = []
    h2 = [len(re.findall(r"^## ", re.sub(r"^```.*?^```", "", x, flags=re.S | re.M), re.M)) for x in (a, b)]
    if h2[0] != h2[1]:
        bad.append(f"{READMES[0]} has {h2[0]} sections (##), {READMES[1]} {h2[1]}: write each in both")
    la = {same_file(t) for t in links(a) if local(t)}
    lb = {same_file(t) for t in links(b) if local(t)}
    for name, only in ((READMES[0], la - lb), (READMES[1], lb - la)):
        if only:
            bad.append(f"only {name} links {', '.join(sorted(only))}")
    return bad


def check():
    have = counts()
    bad = [f"tools/readme.py: the repo has no {WHAT[k]}" for k, v in have.items() if not v]
    bad += count_problems(have)
    for page in READMES:
        bad += link_problems(page)
    bad += pair_problems()
    return bad


def main(argv):
    if argv in ([], ["counts"]):
        for k, v in counts().items():
            print(f"{v:5}  {WHAT[k]}")
        return 0
    if argv == ["check"]:
        bad = check()
        if bad:
            print("\n".join(bad))
            return 1
        have = counts()
        print(f"README.md, README.zh-CN.md and the overview diagrams: {len(have)} counts as the repo has them "
              f"({have['commands']} commands, {have['styles']} styles, {have['recipes']} recipes …), their links in the repo, "
              f"the two READMEs side by side")
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
