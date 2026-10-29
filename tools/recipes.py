"""Shot-recipe library: filter recipes by their frontmatter, and validate that frontmatter.

usage: bin/vh recipes list [--intent X[,Y]] [--energy N|A-B] [--engine E] [--family F] [--role R] [--type T]
                           [--have N[,M]] [--seconds S|A-B] [--aspect A] [--jump J] [--status S] [--pitfall P]
                           [--sound S] [--ids | --json | --md]
       bin/vh recipes list --grammar [size|angle|axis|move[,…]] [--ids | --json | --md]
       bin/vh recipes check [file.md …]
       bin/vh recipes sample <id> [--style PRESET] [--draft] [--force]
       (no subcommand = list; python3 tools/recipes.py … is the same thing)

list   Every filter is optional. Values inside one flag are alternatives (`--intent breath,chapter`); different flags
       must all hold. --energy and --seconds take one number (the recipe's range must contain it) or A-B (the ranges
       must overlap). --have lists the material you have: a recipe passes when everything it needs is in the list.
       An unknown value is an error, not an empty result. --ids prints ids only, --json the parsed frontmatter (with
       path, and sample when the recipe has a sheet), --md index rows for recipes/README.md.
       --grammar: the shot-grammar cards instead (recipes/shot/, kind grammar): shot sizes, angles, the axis and camera
       moves, each with what it does to the viewer and when to take it or not; its code is what a shot table writes
       in its camera field (bin/vh storyboard prints it). Alone, every grammar; it takes no recipe filter.
check  No file: every recipe, sequence and shot-grammar card under recipes/, plus the library-wide checks (unique ids,
       file and folder names, a card's code once in its grammar, conflicts listed both ways, every file linked from
       recipes/README.md (a recipe with the same energy, length and status, a card with the row list --grammar --md
       prints), every vocabulary term documented there, a card's 什么时候用 and 什么时候别用 an item or more each,
       every file derived from licensed material listed in
       recipes/NOTICE.md, every recipe with a sketch carrying its sample sheet, rendered from the sketch as it is
       (sketch_sha) and at most 120 kB and 2000 px wide, and every sheet belonging to a recipe). Each sketch is held
       to hard rule 1 (tools/purity.py).
       With files: those files, cross-checked against the library. A sketch (a ```js block that defines renderAt) is
       syntax-checked with node when node is installed.
sample The recipe's sketch (the first ```js block of its 实现 that defines renderAt) rendered by the style swatch
       renderer (styles/_swatch/render.sh: 5 s, 1920×1080), and its contact sheet (1600 px wide, at the recipe's qa
       frames and between them) kept as recipes/<family>/media/<id>.jpg, the sketch's sha256 (12 hex digits) written
       into its frontmatter as sketch_sha: what the move looks like, for an agent to read. A sketch unchanged since
       its sheet is not rendered again (--force does). --style PRESET: another skin, its sheet beside the video, not
       the recipe's. --draft: HyperFrames' draft quality. The video stays in styles/_swatch/out/recipe-<id>/ (not in
       git). Needs styles/_swatch's npm ci, ffmpeg, uv and Chrome.

Frontmatter is a strict subset of YAML: one `key: value` per line; a value is a plain or quoted scalar, a [flow list]
or a {flow map}; a key with no value takes a block list of `  - item` lines. No anchors, no multi-line scalars.
Whatever YAML parsers read differently is refused rather than guessed: `yes`/`no`/`on`/`off`, numbers with leading
zeros, underscores, exponents or colons (`1:30`), dates, `{key:value}` without the space, `?` inside a flow value,
escapes in double quotes, a key with neither a value nor items. What passes reads the same in PyYAML. The fields and
vocabularies are documented in recipes/README.md; VOCAB in tools/recipes.py is the machine copy, and `check` fails
when the two drift apart.

A source under Apache-2.0, MIT or CC-BY-4.0 needs its upstream `commit`, a copy of its licence as
recipes/LICENSES/<license>-<repo>.txt, a "修改自 …" statement in the file's 来源 section that links that copy and names
the commit, and a row in recipes/NOTICE.md (Apache-2.0 §4; MIT and CC BY ask for the same notices).

Exit: 0 fine · 1 check found problems · 2 bad usage (unknown flag or vocabulary value). Reads files only.
"""
import hashlib, json, os, re, shutil, subprocess, sys, tempfile, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIB = ROOT / "recipes"
FPS = 30
SHEET_MAX_KB, SHEET_MAX_W, SHEET_W = 120, 2000, 1600   # a sample sheet: at most this big and this wide; rendered this wide
sys.path.insert(0, str(ROOT / "tools"))
import purity   # noqa: E402  tools/purity.py: hard rule 1's patterns (bin/vh hf add and components check read them too)

# Controlled vocabularies. Append only: a published term is never renamed or reused (recipes/README.md, "词表").
VOCAB = {
    "family": ["open", "type", "ui", "interaction", "data", "camera", "rhythm", "fx", "seam", "outro"],
    "role": ["hook", "open", "hero", "feature", "breath", "proof", "climax", "outro", "seam"],
    "intent": ["hook", "promise", "brand-imprint",
               "hero", "abundance", "process", "compare", "transform", "detail", "locate", "connect", "count", "timeline",
               "interact", "search", "generate",
               "breath", "accelerate", "punctuate", "hush", "payoff",
               "carry", "enter", "chapter", "refocus",
               "sign-off", "cta"],
    "types": ["math", "short", "promo", "mv", "data", "paper", "handdrawn", "meme"],
    "engines": ["hyperframes", "canvas", "three", "p5", "manim", "remotion"],
    "aspect": ["landscape", "portrait", "square"],
    "needs": ["ui-page", "ui-element", "text", "number", "series", "photo", "footage", "logo", "3d", "none"],
    "sound": ["required", "recommended", "optional"],
    "status": ["battle-tested", "upstream-tested", "tuned", "draft"],
    "pitfalls": ["too-fast", "no-hold", "uniform-timing", "sub-threshold", "float-not-land", "text-blur", "dead-frame",
                 "seam-mismatch", "flash-rate", "glow-spill", "overuse", "sound-dependent", "mechanical-stop",
                 "fake-ui", "off-axis-read", "motion-sickness", "state-leak", "copy-drift"],
    "jump": ["rise", "level", "drop"],
    "qa": ["read", "peak", "seam", "settle", "last"],
    "license": ["Apache-2.0", "MIT", "CC0-1.0", "CC-BY-4.0", "none"],
    "kind": ["recipe", "sequence", "grammar"],
    "grammar": ["size", "angle", "axis", "move"],
}
# field: (required, check). Recipes and sequences share the file format; `kind` picks the field set.
RECIPE = {
    "id": (True, "id"), "name": (True, "str"), "one_liner": (True, "str"), "family": (True, "family"),
    "role": (True, "role+"), "intent": (True, "intent+"), "energy": (True, "energy"), "duration_f": (True, "range"),
    "types": (True, "types+"), "engines": (True, "engines+"), "aspect": (True, "aspect+"), "needs": (True, "needs+"),
    "sound": (True, "sound"), "pitfalls": (True, "pitfalls+"), "qa": (True, "qamap"), "status": (True, "status"),
    "derived_from": (True, "sources"),
    "jump": (False, "jump+"), "max_per_film": (False, "count"), "conflicts": (False, "ids"),
    "pairs_with": (False, "ids"), "impl": (False, "paths"), "sketch_sha": (False, "sha"),
}
SEQUENCE = {
    "id": (True, "id"), "kind": (True, "kind"), "name": (True, "str"), "one_liner": (True, "str"),
    "duration_f": (True, "range"), "types": (True, "types+"), "aspect": (True, "aspect+"), "arc": (True, "arc"),
    "uses": (True, "ids"), "status": (True, "status"), "derived_from": (True, "sources"),
}
# a shot-grammar card (recipes/shot/): one choice of shot size, angle, axis or camera move, what it does to the viewer and
# when to take it or not; `code` is what a shot table writes for it (shots.json's or edit.json's "camera"), unique in its grammar
GRAMMAR = {
    "id": (True, "id"), "kind": (True, "kind"), "grammar": (True, "grammar"), "code": (True, "code"), "name": (True, "str"),
    "one_liner": (True, "str"), "derived_from": (True, "sources"), "types": (False, "types+"), "recipes": (False, "ids"),
}
RECIPE_HEADINGS = ["## 意图", "## 阶段与时值", "## 参数", "## 声音", "## 风格适配", "## 实现", "## 已知坑", "## 验收帧", "## 来源"]
SEQUENCE_HEADINGS = ["## 能量弧", "## 预算", "## 接缝", "## 限额", "## 来源"]
GRAMMAR_HEADINGS = ["## 情绪动机", "## 什么时候用", "## 什么时候别用", "## 来源"]
FIELDS_OF = {"recipe": RECIPE, "sequence": SEQUENCE, "grammar": GRAMMAR}
HEADINGS_OF = {"recipe": RECIPE_HEADINGS, "sequence": SEQUENCE_HEADINGS, "grammar": GRAMMAR_HEADINGS}
FOLDER_OF = {"sequence": "sequences", "grammar": "shot"}   # a recipe lives in its family's folder
INDICATORS = set("-?:,[]{}#&*!|>'\"%@`")
# Licences whose text and notices must travel with a file derived from the material (recipes/LICENSES/, NOTICE.md).
KEEP_NOTICE = ("Apache-2.0", "MIT", "CC-BY-4.0")
# Plain scalars that YAML 1.1 (PyYAML) or 1.2 parsers turn into something other than the text or number we would read.
AMBIGUOUS = re.compile(r"""(?x)
    (?i:y|yes|n|no|on|off|true|false|null|~|=|<<)                   # booleans and null in any case, YAML 1.1 keys
  | [-+]?0b[01_]+ | [-+]?0x[0-9a-fA-F_]+ | [-+]?0o?[0-7_]+           # binary, hex, octal (017 is 15 in YAML 1.1)
  | [-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?                # sexagesimal: 1:30 is 90
  | [-+]?(?:\.[0-9][0-9_]*|[0-9][0-9_]*(?:\.[0-9_]*)?)(?:[eE][-+]?[0-9]+)?   # +1, 1_000, 1., .5, 1e3
  | [-+]?\.(?i:inf|nan)
  | [0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:(?:[Tt]|[ \t]+)[0-9]{1,2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]*)?
                                   (?:[ \t]*(?:Z|[-+][0-9]{1,2}(?::[0-9]{2})?))?)?   # dates and timestamps
""")


class FMError(Exception):
    pass


# ---------------------------------------------------------------- the YAML subset
def strip_comment(line):
    """Drop a trailing comment the way YAML does: `#` starts one at line start or after a blank, outside quotes. A quote
    opens a quoted scalar only where a scalar starts (after `key: `, `- `, `[`, `{`, or `,` / `: ` inside a flow), so
    the apostrophe in `don't` is a letter."""
    q, depth, start = None, 0, True
    for i, c in enumerate(line):
        if q:
            if c == q:
                q, start = None, False
            continue
        if c in " \t":
            continue
        if c == "#" and (i == 0 or line[i - 1] in " \t"):
            return line[:i]
        blank_after = line[i + 1:i + 2] in ("", " ", "\t")
        if start and c in "\"'":
            q = c
            continue
        if start and c in "[{":
            depth += 1
            continue
        if depth and c == ",":
            start = True
            continue
        if depth and c in "]}":
            depth -= 1
        elif (c == ":" and blank_after) or (c == "-" and blank_after and not line[:i].strip()):
            start = True
            continue
        start = False
    return line


def scalar(s):
    s = s.strip()
    if s in ("true", "false"):
        return s == "true"
    if s in ("null", "~", ""):
        return None
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", s):
        return int(s)
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)\.[0-9]+", s):
        return float(s)
    if AMBIGUOUS.fullmatch(s):
        raise FMError(f"YAML parsers disagree on what {s!r} is (a yes/no, a date or a number): quote it")
    return s


class Flow:
    """Recursive-descent reader for a flow value: [a, b], {k: v}, quoted or plain scalars."""

    def __init__(self, text):
        self.t, self.i = text, 0

    def ws(self):
        while self.i < len(self.t) and self.t[self.i] in " \t":
            self.i += 1

    def value(self, depth):
        self.ws()
        if self.i >= len(self.t):
            raise FMError("a value is missing")
        c = self.t[self.i]
        if c == "[":
            return self.seq(depth)
        if c == "{":
            return self.mapping(depth)
        if c in "\"'":
            return self.quoted(c)
        return self.plain(depth)

    def quoted(self, q):
        j = self.t.find(q, self.i + 1)
        if j < 0:
            raise FMError(f"unclosed {q}")
        s = self.t[self.i + 1:j]
        if q == '"' and "\\" in s:
            raise FMError(f"a backslash inside double quotes is an escape in YAML: use single quotes ({self.t!r})")
        if q == "'" and self.t[j + 1:j + 2] == "'":
            raise FMError(f"'' (an escaped quote) is not supported: use double quotes ({self.t!r})")
        self.i = j + 1
        return s

    def plain(self, depth):
        j = self.i
        if depth:
            while j < len(self.t) and self.t[j] not in ",]}":
                j += 1
        else:
            j = len(self.t)
        s = self.t[self.i:j].strip()
        self.i = j
        if not s:
            raise FMError("an empty value inside a list or map")
        if s[0] in INDICATORS:
            raise FMError(f"a plain value cannot start with {s[0]!r}: quote it ({s!r})")
        if ": " in s or s.endswith(":"):
            raise FMError(f"': ' inside a plain value is not YAML: quote it ({s!r})")
        if depth and any(c in s for c in "?[{"):
            raise FMError(f"inside [ ] or {{ }}, YAML does not allow ?, [ or {{ in an unquoted value: quote it ({s!r})")
        return scalar(s)

    def expect(self, c):
        self.ws()
        if self.i >= len(self.t) or self.t[self.i] != c:
            raise FMError(f"expected {c!r} at column {self.i + 1} of {self.t!r}")
        self.i += 1

    def seq(self, depth):
        self.i += 1
        out = []
        self.ws()
        if self.t[self.i:self.i + 1] == "]":
            self.i += 1
            return out
        while True:
            out.append(self.value(depth + 1))
            self.ws()
            if self.t[self.i:self.i + 1] == ",":
                self.i += 1
                continue
            self.expect("]")
            return out

    def mapping(self, depth):
        self.i += 1
        out = {}
        self.ws()
        if self.t[self.i:self.i + 1] == "}":
            self.i += 1
            return out
        while True:
            self.ws()
            m = re.match(r"[A-Za-z_][A-Za-z0-9_-]*", self.t[self.i:])
            if not m:
                raise FMError(f"a map key is missing in {self.t!r}")
            k = m.group(0)
            self.i += len(k)
            self.expect(":")
            if self.t[self.i:self.i + 1] not in (" ", "\t"):
                raise FMError(f"put a space after {k}: in {self.t!r} (without it YAML reads one key, {k}:…)")
            if k in out:
                raise FMError(f"duplicate key {k!r} in {self.t!r}")
            out[k] = self.value(depth + 1)
            self.ws()
            if self.t[self.i:self.i + 1] == ",":
                self.i += 1
                continue
            self.expect("}")
            return out

    def done(self):
        self.ws()
        if self.i != len(self.t):
            raise FMError(f"unexpected text after the value: {self.t[self.i:]!r}")


def parse_value(text):
    f = Flow(text.strip())
    v = f.value(0)
    f.done()
    return v


def read(path):
    """→ (frontmatter dict, body text). Raises FMError with a line number."""
    lines = Path(path).read_text(encoding="utf-8").split("\n")
    if not lines or lines[0].rstrip() != "---":
        raise FMError("line 1: the file must start with a --- frontmatter block")
    end = next((i for i in range(1, len(lines)) if lines[i].rstrip() == "---"), None)
    if end is None:
        raise FMError("the frontmatter block is not closed with ---")
    data, block, indent, opened = {}, None, None, {}
    for n in range(1, end):
        raw = strip_comment(lines[n]).rstrip()
        if not raw.strip():
            continue
        try:
            item = re.match(r"( *)- (.*)$", raw)
            if item:
                if block is None:
                    raise FMError("a list item with no key above it")
                if indent is None:
                    indent = len(item.group(1))
                elif len(item.group(1)) != indent:   # YAML would read a deeper `- b` as part of the item above
                    raise FMError("list items must line up: same indentation for every `- ` of a list")
                data[block].append(parse_value(item.group(2)))
                continue
            if raw[0] in " \t":
                raise FMError("unexpected indentation (only `  - item` lines may be indented)")
            m = re.match(r"([a-z_]+):(?: +(.*))?$", raw)
            if not m:
                raise FMError(f"expected `key: value`, got {raw!r}")
            key, val = m.group(1), m.group(2)
            if key in data:
                raise FMError(f"duplicate key {key!r}")
            if val is None or not val.strip():
                data[key], block, indent, opened[key] = [], key, None, n
            else:
                data[key], block = parse_value(val), None
        except FMError as e:
            raise FMError(f"line {n + 1}: {e}")
    for key, n in opened.items():   # YAML reads `key:` with nothing under it as null, not as an empty list
        if not data[key]:
            raise FMError(f"line {n + 1}: `{key}:` has no value and no `  - item` lines (write `{key}: []` for none)")
    return data, "\n".join(lines[end + 1:])


# ---------------------------------------------------------------- validation
def span(v, lo, hi, what):
    """An int, or [a, b] with a ≤ b, all within lo..hi → (a, b)."""
    if isinstance(v, bool):
        raise FMError(f"{what}: expected a number")
    if isinstance(v, int):
        v = [v, v]
    if not (isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in v)):
        raise FMError(f"{what}: expected an integer or [min, max], got {v!r}")
    if not (lo <= v[0] <= v[1] <= hi):
        raise FMError(f"{what}: {v!r} must satisfy {lo} ≤ min ≤ max ≤ {hi}")
    return v[0], v[1]


def check_field(key, kind, v, fm):
    """Raise FMError when v does not fit kind."""
    vocab = kind.rstrip("+")
    if kind == "id":
        if not (isinstance(v, str) and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", v)):
            raise FMError(f"{key}: lower-case words joined by hyphens, got {v!r}")
    elif kind == "str":
        if not isinstance(v, str) or not v.strip():
            raise FMError(f"{key}: expected text")
    elif kind == "sha":
        if not (isinstance(v, str) and re.fullmatch(r"[0-9a-f]{12}", v)):
            raise FMError(f"{key}: the first 12 hex digits of the sketch's sha256, quoted (bin/vh recipes sample writes it), got {v!r}")
    elif kind == "code":
        if not (isinstance(v, str) and re.fullmatch(r"[A-Za-z][A-Za-z0-9-]{0,15}", v)):
            raise FMError(f"{key}: a short code a shot table writes (CU, low, push-in), letters, digits and -, got {v!r}")
    elif kind.endswith("+"):
        if not isinstance(v, list) or not v:
            raise FMError(f"{key}: expected a non-empty [list] from the {vocab} vocabulary")
        bad = [x for x in v if x not in VOCAB[vocab]]
        if bad:
            raise FMError(f"{key}: unknown {bad} (vocabulary: {', '.join(VOCAB[vocab])})")
        if len(set(v)) != len(v):
            raise FMError(f"{key}: a value is listed twice")
    elif kind in VOCAB:
        if v not in VOCAB[kind]:
            raise FMError(f"{key}: unknown {v!r} (vocabulary: {', '.join(VOCAB[kind])})")
    elif kind == "energy":
        span(v, 0, 5, key)
    elif kind == "range":
        span(v, 1, 30 * 60 * FPS, key)
    elif kind == "count":
        if not (isinstance(v, int) and not isinstance(v, bool) and v >= 1):
            raise FMError(f"{key}: expected a positive integer")
    elif kind == "arc":
        if not (isinstance(v, list) and len(v) >= 2 and all(isinstance(x, int) and not isinstance(x, bool) and 0 <= x <= 5 for x in v)):
            raise FMError(f"{key}: expected [e1, e2, …] with each energy 0–5")
    elif kind == "qamap":
        if not (isinstance(v, dict) and v):
            raise FMError(f"{key}: expected {{peak: frame, settle: frame, …}}")
        bad = [k for k in v if k not in VOCAB["qa"]]
        if bad:
            raise FMError(f"qa: unknown key {bad} (vocabulary: {', '.join(VOCAB['qa'])})")
        top = fm.get("duration_f")
        top = top[1] if isinstance(top, list) and len(top) == 2 else top if isinstance(top, int) else None
        for k, f in v.items():
            if not (isinstance(f, int) and not isinstance(f, bool) and f >= 0) or (top is not None and f > top):
                raise FMError(f"qa.{k}: {f!r} must be a frame 0–{top} (from the recipe's first frame, 30 fps)")
    elif kind == "ids":
        if not (isinstance(v, list) and all(isinstance(x, str) and re.fullmatch(r"[a-z0-9-]+", x) for x in v)):
            raise FMError(f"{key}: expected a [list] of recipe ids")
    elif kind == "paths":
        if not (isinstance(v, list) and v and all(isinstance(x, str) for x in v)):
            raise FMError(f"{key}: expected a [list] of repository paths")
        for p in v:
            f = p.split("#")[0]   # path#anchor is allowed
            if not f or f.startswith("/") or ".." in Path(f).parts or not (ROOT / f).is_file():
                raise FMError(f"{key}: {p!r} is not a file in this repository")
    elif kind == "sources":
        if not isinstance(v, list):
            raise FMError(f"{key}: expected a block list of {{repo, commit, path, license}} (or [] for an original recipe)")
        for s in v:
            if not (isinstance(s, dict) and {"repo", "path", "license"} <= set(s) <= {"repo", "commit", "path", "license", "note"}
                    and all(isinstance(s[k], str) and s[k].strip() for k in ("repo", "path"))):
                raise FMError(f"{key}: each item is {{repo: …, commit: …, path: …, license: …}} (+ optional note), got {s!r}")
            if s["license"] not in VOCAB["license"]:
                raise FMError(f"{key}: license {s['license']!r} is not one of {', '.join(VOCAB['license'])}")
            c = s.get("commit")
            if (s["license"] != "none" or c is not None) and not (isinstance(c, str) and re.fullmatch(r"[0-9a-f]{7,40}", c)):
                raise FMError(f"{key}: {s['repo']}: `commit` is the upstream commit the material was taken from, a quoted "
                              f"hex string of 7–40 characters (only a `license: none` source may leave it out), got {c!r}")
    else:
        raise AssertionError(kind)


def licence_copy(src):
    """Where the licence of a KEEP_NOTICE source lives: recipes/LICENSES/<license>-<last part of repo>.txt."""
    return f"LICENSES/{src['license']}-{src['repo'].rstrip('/').split('/')[-1]}.txt"


def kept_sources(fm):
    """The derived_from items whose licence and notices have to travel with the file."""
    v = fm.get("derived_from")
    return [s for s in v if isinstance(s, dict) and s.get("license") in KEEP_NOTICE
            and isinstance(s.get("repo"), str) and isinstance(s.get("path"), str)] if isinstance(v, list) else []


def as_list(v):
    return v if isinstance(v, list) else []


def section(body, heading):
    m = re.search(rf"^{re.escape(heading)}\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def sketch_of(body):
    """The recipe's sketch: the first ```js block of its 实现 that defines renderAt (None when it has none)."""
    return next((b for b in re.findall(r"```js\n(.*?)```", section(body, "## 实现"), re.S) if "renderAt" in b), None)


def sample_path(p, rid):
    """Where `bin/vh recipes sample` keeps a recipe's contact sheet: next to it, media/<id>.jpg."""
    return Path(p).parent / "media" / f"{rid}.jpg"


def sketch_sha(sketch):
    """The first 12 hex digits of the sketch's sha256: what its sheet was rendered from (frontmatter sketch_sha)."""
    return hashlib.sha256(sketch.encode("utf-8")).hexdigest()[:12]


def jpeg_width(path):
    """A JPEG's width from its frame header (SOFn), or None when it is not one."""
    b = Path(path).read_bytes()
    i = 2 if b[:2] == b"\xff\xd8" else len(b)
    while i + 9 < len(b):
        if b[i] != 0xFF:
            return None
        marker, n = b[i + 1], int.from_bytes(b[i + 2:i + 4], "big")
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            return int.from_bytes(b[i + 7:i + 9], "big")
        i += 2 + n
    return None


def set_sketch_sha(path, sha):
    """Write sketch_sha into the recipe's frontmatter: its line replaced, or a line added before the closing ---."""
    text = Path(path).read_text(encoding="utf-8")
    end = text.index("\n---", 4)
    head, rest = text[:end], text[end:]
    line = f'sketch_sha: "{sha}"'
    head, n = re.subn(r"(?m)^sketch_sha:.*$", line, head)
    Path(path).write_text((head if n else head + "\n" + line) + rest, encoding="utf-8")


def frontmatter_problems(fm):
    """Field-by-field problems of one parsed frontmatter (no body, no cross-references)."""
    probs = []
    kind = fm.get("kind", "recipe")
    fields = FIELDS_OF.get(kind, RECIPE)
    for key in fm:
        if key not in fields:
            probs.append(f"unknown field {key!r} for a {kind} (fields: {', '.join(fields)})")
    for key, (req, chk) in fields.items():
        if key not in fm:
            if req:
                probs.append(f"missing field {key!r}")
            continue
        try:
            check_field(key, chk, fm[key], fm)
        except FMError as e:
            probs.append(str(e))
    if kind == "recipe":
        if fm.get("family") == "seam" and "jump" not in fm:
            probs.append("a seam recipe needs `jump` (rise | level | drop): which energy change it bridges")
        if fm.get("family") != "seam" and "jump" in fm:
            probs.append("`jump` is only for seam recipes")
    return probs


def check_file(path, lib=None):
    """→ (frontmatter or None, [problems]). lib: {id: (path, fm)} of the whole library, for cross-references."""
    try:
        fm, body = read(path)
    except (FMError, OSError, UnicodeDecodeError) as e:
        return None, [str(e)]
    probs = frontmatter_problems(fm)
    kind = fm.get("kind", "recipe")
    heads = [h for h in HEADINGS_OF.get(kind, RECIPE_HEADINGS) if not re.search(rf"^{re.escape(h)}", body, re.M)]
    if heads:
        probs.append(f"missing body section(s): {', '.join(heads)} " + (
            f"(every shot-grammar card has {', '.join(GRAMMAR_HEADINGS)}; recipes/shot/close-up.md is one)" if kind == "grammar"
            else f"(every sequence has {', '.join(SEQUENCE_HEADINGS)}; recipes/sequences/launch-15s.md is one, and "
                 "recipes/sequences/README.md says what goes in each)" if kind == "sequence"
            else "(copy recipes/_TEMPLATE.md)"))
    if kind == "grammar":   # what a card is for: when to take it and when not, an item at least each
        for h in ("## 什么时候用", "## 什么时候别用"):
            if h not in heads and not re.search(r"^\s*[-*] +\S", section(body, h), re.M):
                probs.append(f"{h}: no item under it (a list of when, - …, one or more)")
    src_text = section(body, "## 来源")
    for s in kept_sources(fm):   # Apache-2.0 §4 (a) and (b): the licence travels with the file, which says it was modified
        lic = licence_copy(s)
        if not (LIB / lic).is_file():
            probs.append(f"derived_from: {s['repo']} is {s['license']}: put a copy of its licence at recipes/{lic}")
        if lic not in src_text or "修改自" not in src_text:
            probs.append(f"## 来源: say that the file is modified from {s['repo']} (修改自 …) and link recipes/{lic}")
        if isinstance(s.get("commit"), str) and s["commit"][:7] not in src_text:
            probs.append(f"## 来源: name the upstream commit {s['commit'][:7]} of {s['repo']}")
    probs += check_sketches(body)
    p = Path(path).resolve()
    inside = LIB in p.parents
    if inside and isinstance(fm.get("id"), str):
        if p.stem != fm["id"]:
            probs.append(f"file name {p.name} does not match id {fm['id']!r}")
        want = FOLDER_OF.get(kind, fm.get("family"))
        if p.parent.name != want:
            probs.append(f"lives in {p.parent.name}/, expected {want}/")
    if lib is not None:
        me = fm.get("id") if isinstance(fm.get("id"), str) else None
        if me in lib and lib[me][0] != p:
            probs.append(f"id {me!r} is already used by {rel(lib[me][0])}")
        for key in ("conflicts", "pairs_with", "uses", "recipes"):
            for other in as_list(fm.get(key)):   # a wrong type is already reported field by field
                if not isinstance(other, str):
                    continue
                if other == me:
                    probs.append(f"{key}: lists itself")
                elif other not in lib or lib[other][1].get("kind", "recipe") != "recipe":
                    probs.append(f"{key}: no recipe with id {other!r}")
                elif key == "conflicts" and me not in as_list(lib[other][1].get("conflicts")):
                    probs.append(f"conflicts: {other!r} does not list {me!r} back (conflicts go both ways)")
    return fm, probs


def check_sketches(body):
    """Every ```js block that defines renderAt (an ES module): hard rule 1 (tools/purity.py), and its syntax with node
    when node is installed."""
    node, probs = shutil.which("node"), []
    for i, block in enumerate(re.findall(r"```js\n(.*?)```", body, re.S)):
        if "renderAt" not in block:
            continue
        probs += [f"sketch {i + 1}, line {n}: {what} (hard rule 1: a frame is a function of t; a line may say purity-ok with its reason)"
                  for what, n, _ in purity.scan(block)]
        if not node:
            continue
        r = subprocess.run([node, "--input-type=module", "--check"], input=block, capture_output=True, text=True, timeout=30)
        if r.returncode:
            err = next((ln for ln in r.stderr.splitlines() if "Error" in ln), r.stderr.strip()[:200])
            probs.append(f"sketch {i + 1} does not parse: {err}")
    return probs


def span_text(v, scale=1):
    """[a, b] or n → "a–b" / "n" (seconds when scale = FPS: one decimal, two under 1 s, no trailing zeros)."""
    a, b = (v, v) if isinstance(v, int) else v
    f = (lambda x: f"{x / scale:.{2 if x < scale else 1}f}".rstrip("0").rstrip(".")) if scale != 1 else str   # < 1 s: 2 decimals
    return f(a) if a == b else f"{f(a)}–{f(b)}"


def index_row(rid, p, fm):
    return (f"| [{rid}]({rel(p)[len('recipes/'):]}) | {fm.get('one_liner', '')} | {span_text(fm['energy'])} | "
            f"{span_text(fm['duration_f'], FPS)} s | {fm['status']} |")


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT))
    except ValueError:
        return str(p)


def not_a_recipe(p):
    """README.md, NOTICE.md and other upper-case docs, the _TEMPLATE and anything under a _folder."""
    return Path(p).stem.isupper() or any(part.startswith("_") for part in Path(p).parts)


def library_files():
    """Every recipe and sequence: *.md under recipes/ that is not a doc or a template."""
    return sorted(p for p in LIB.rglob("*.md") if not not_a_recipe(p.relative_to(LIB)))


def load_library():
    lib = {}
    for p in library_files():
        try:
            fm, _ = read(p)
        except (FMError, OSError, UnicodeDecodeError):
            continue
        if isinstance(fm.get("id"), str) and fm["id"] not in lib:
            lib[fm["id"]] = (p.resolve(), fm)
    return lib


def library_checks(lib):
    """Checks that need the whole library: README index both ways, vocabulary documented in README."""
    probs = []
    readme = (LIB / "README.md").read_text(encoding="utf-8") if (LIB / "README.md").exists() else ""
    linked = set(re.findall(r"\]\(([a-z-]+/[a-z0-9-]+\.md)\)", readme))
    found = list(re.finditer(r"^\| \[[a-z0-9-]+\]\(([a-z-]+/[a-z0-9-]+\.md)\) \|.*\|$", readme, re.M))
    rows = {m.group(1): [c.strip() for c in m.group(0).strip("|").split("|")] for m in found}
    lines = {m.group(1): m.group(0) for m in found}
    for rid, (p, fm) in sorted(lib.items()):
        target = rel(p)[len("recipes/"):]
        if target not in linked:
            probs.append(f"recipes/README.md: {rid} is not linked from the index (add a row that links {target})")
        elif fm.get("kind") == "grammar" and target in lines:   # the row a shot table's code is copied from: as the card says
            try:
                want = grammar_row(rid, p, fm)
            except KeyError:   # a field missing: said by the card's own check
                continue
            if lines[target] != want:
                probs.append(f"recipes/README.md: the {rid} row is {lines[target]!r}, the card makes {want!r} "
                             f"(bin/vh recipes list --grammar --md prints the rows)")
        elif fm.get("kind", "recipe") == "recipe" and target in lines:   # the whole row as the card makes it, one-liner too
            try:
                want = index_row(rid, p, fm)
            except (KeyError, TypeError, ValueError):   # a field missing or malformed: said by the card's own check
                continue
            if lines[target] != want:
                cols = ["link", "one-liner", "energy", "length", "status"]
                got, made = rows[target], [c.strip() for c in want.strip("|").split("|")]
                which = [cols[i] if i < len(cols) else f"column {i + 1}" for i in range(max(len(got), len(made)))
                         if i >= len(got) or i >= len(made) or got[i] != made[i]]
                probs.append(f"recipes/README.md: the {rid} row differs from its card in its {', '.join(which)}: it is "
                             f"{lines[target]!r}, the card makes {want!r} (bin/vh recipes list --md prints the rows)")
    for target in sorted(linked):
        if not (LIB / target).exists():
            probs.append(f"recipes/README.md: links {target}, which does not exist")
    codes = {}   # a shot table's camera value names one grammar card: a code once in its grammar
    for rid, (p, fm) in sorted(lib.items()):
        if fm.get("kind") == "grammar" and isinstance(fm.get("code"), str):
            k = (fm.get("grammar"), fm["code"].lower())
            if k in codes:
                probs.append(f"{rel(p)}: code {fm['code']!r} is {codes[k]}'s too, in the same grammar ({fm.get('grammar')})")
            codes.setdefault(k, rid)
    tpl = LIB / "_TEMPLATE.md"   # the template must stay a valid recipe (only its file name and folder are exempt)
    if tpl.exists():
        _, tp = check_file(tpl)
        probs += [f"recipes/_TEMPLATE.md: {x}" for x in tp if not x.startswith(("file name", "lives in"))]
    for field, words in VOCAB.items():
        missing = [w for w in words if f"`{w}`" not in readme]
        if missing:
            probs.append(f"recipes/README.md: vocabulary {field!r} is missing {missing} (document each term in `backticks`)")
    notice = (LIB / "NOTICE.md").read_text(encoding="utf-8") if (LIB / "NOTICE.md").exists() else ""
    for rid, (p, fm) in sorted(lib.items()):   # Apache-2.0 §4: one place that lists every derived file and its upstream
        srcs = kept_sources(fm)
        if not srcs:
            continue
        target = rel(p)[len("recipes/"):]
        rows = "\n".join(ln for ln in notice.splitlines() if f"`{target}`" in ln or f"({target})" in ln)
        if not rows:
            probs.append(f"recipes/NOTICE.md: {target} is derived from {srcs[0]['repo']} ({srcs[0]['license']}) but not listed")
            continue
        for s in srcs:
            if s["path"] not in rows:
                probs.append(f"recipes/NOTICE.md: the row for {target} does not name its upstream file {s['path']}")
    for rid, (p, fm) in sorted(lib.items()):   # a recipe shows its move: the sketch rendered as a contact sheet
        if fm.get("kind", "recipe") != "recipe" or sample_path(p, rid).exists():
            continue
        try:
            _, body = read(p)
        except (FMError, OSError, UnicodeDecodeError):
            continue
        if sketch_of(body) is not None:
            probs.append(f"{rel(p)}: has a sketch but no sample sheet (bin/vh recipes sample {rid} --draft → "
                         f"{rel(sample_path(p, rid))})")
    for rid, (p, fm) in sorted(lib.items()):   # a sheet shows the sketch as it is now, and stays small
        sheet = sample_path(p, rid)
        if fm.get("kind", "recipe") != "recipe" or not sheet.exists():
            continue
        kb, w = sheet.stat().st_size / 1024, jpeg_width(sheet)
        if kb > SHEET_MAX_KB or not w or w > SHEET_MAX_W:
            probs.append(f"{rel(sheet)}: {kb:.0f} kB, {w or 'no JPEG'} px wide: at most {SHEET_MAX_KB} kB and {SHEET_MAX_W} px "
                         f"(bin/vh recipes sample renders {SHEET_W} px)")
        try:
            _, body = read(p)
        except (FMError, OSError, UnicodeDecodeError):
            continue
        sk = sketch_of(body)
        if sk is not None and fm.get("sketch_sha") != sketch_sha(sk):
            probs.append(f"{rel(p)}: " + ("its sheet has no sketch_sha in the frontmatter" if not fm.get("sketch_sha") else
                                          "its sketch changed since its sheet was rendered") + f" (bin/vh recipes sample {rid} --draft)")
    for sheet in sorted(LIB.glob("*/media/*.jpg")):
        owner = lib.get(sheet.stem)
        if not owner or sample_path(owner[0], sheet.stem).resolve() != sheet.resolve():
            probs.append(f"{rel(sheet)}: no recipe {sheet.stem} in {sheet.parent.parent.name}/ (a sheet left behind)")
    return probs


def cmd_check(files):
    flags = [f for f in files if f.startswith("-")]
    if flags:
        return usage(f"check takes file names, not options: {' '.join(flags)}")
    lib = load_library()
    todo = [Path(f) for f in files] if files else library_files()
    skipped = [p for p in todo if not_a_recipe(p.name)]
    for p in skipped:   # `check recipes/*/*.md` also matches READMEs, NOTICE.md and the template: not recipes
        print(f"- {rel(p)}  (skipped: not a recipe)")
    todo = [p for p in todo if p not in skipped]
    bad = 0
    for p in todo:
        fm, probs = check_file(p, lib)
        if probs:
            bad += 1
            print(f"\033[31m✗\033[0m {rel(p)}")
            for x in probs:
                print(f"    {x}")
        else:
            print(f"\033[32m✓\033[0m {rel(p)}  ({fm.get('kind', 'recipe')} {fm['id']})")
    n, lib_probs = len(todo), (library_checks(lib) if not files else [])
    for x in lib_probs:
        print(f"\033[31m✗\033[0m {x}")
    print(f"{n - bad}/{n} files pass" + (f"; {len(lib_probs)} library problem(s)" if lib_probs else ""))
    return 1 if bad or lib_probs else 0


# ---------------------------------------------------------------- list
FILTERS = {  # flag: (frontmatter field, vocabulary or special)
    "--intent": ("intent", "intent"), "--family": ("family", "family"), "--role": ("role", "role"),
    "--type": ("types", "types"), "--engine": ("engines", "engines"), "--aspect": ("aspect", "aspect"),
    "--jump": ("jump", "jump"), "--status": ("status", "status"), "--pitfall": ("pitfalls", "pitfalls"),
    "--sound": ("sound", "sound"), "--have": ("needs", "needs"),
    "--energy": ("energy", "span"), "--seconds": ("duration_f", "span"),
}


def usage(msg=None):
    if msg:
        print(f"bin/vh recipes: {msg}", file=sys.stderr)
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


def parse_span(text, flag):
    m = re.fullmatch(r"(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?", text)
    if not m:
        raise ValueError(f"{flag} takes a number or A-B, got {text!r}")
    a = float(m.group(1))
    b = float(m.group(2)) if m.group(2) else a
    if b < a:
        raise ValueError(f"{flag}: {text!r} runs backwards")
    return a, b


def grammar_cards():
    """The shot-grammar cards that validate: [(id, path, frontmatter)] by grammar, then id."""
    out = []
    for p in library_files():
        try:
            fm, _ = read(p)
        except (FMError, OSError, UnicodeDecodeError):
            continue
        if fm.get("kind") == "grammar" and not frontmatter_problems(fm):
            out.append((fm["id"], p, fm))
    order = {g: i for i, g in enumerate(VOCAB["grammar"])}
    return sorted(out, key=lambda r: (order.get(r[2]["grammar"], 99), r[0]))


def grammar_row(rid, p, fm):
    return f"| [{rid}]({rel(p)[len('recipes/'):]}) | `{fm['code']}` | {fm['name']} | {fm['one_liner']} |"


def cmd_grammar(classes, out):
    """list --grammar [size,angle…]: the shot-grammar cards of those grammars (recipes/shot/), all four by default."""
    rows = [r for r in grammar_cards() if r[2]["grammar"] in classes]
    if out == "ids":
        print("\n".join(r[0] for r in rows))
    elif out == "json":
        print(json.dumps([dict(fm, path=rel(p)) for _, p, fm in rows], ensure_ascii=False, indent=1))
    elif out == "md":
        print("\n".join(grammar_row(*r) for r in rows))
    else:
        head = ("id", "grammar", "code", "name", "one_liner")
        table = [head] + [(rid, fm["grammar"], fm["code"], fm["name"], fm["one_liner"]) for rid, _, fm in rows]
        cols = lambda s: sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)   # noqa: E731  a terminal's columns
        widths = [max(cols(r[c]) for r in table) for c in range(len(head) - 1)]
        for r in table:
            print("  " + "  ".join(x + " " * (w - cols(x)) for x, w in zip(r, widths)) + "  " + r[-1])
        print(f"{len(rows)} shot-grammar card{'' if len(rows) == 1 else 's'}: recipes/shot/<id>.md. A shot table writes the code in "
              "its camera field ({\"size\": \"MCU\", \"angle\": \"low\", \"move\": \"push-in\"}); bin/vh storyboard prints it")
    return 0


def cmd_list(args):
    want, out, grammar = {}, None, None
    i = 0
    while i < len(args):
        a = args[i]
        if a in ("--ids", "--json", "--md"):
            if out and out != a[2:]:
                return usage(f"--{out} and {a} are two output formats: pick one")
            out = a[2:]
            i += 1
            continue
        if a == "--grammar" or a.startswith("--grammar="):   # the shot-grammar cards instead of the recipes
            if "=" in a:
                val, i = a.split("=", 1)[1], i + 1
                if not val:
                    return usage(f"--grammar= names no grammar: one or more of {', '.join(VOCAB['grammar'])}, or --grammar alone for all four")
            elif i + 1 < len(args) and not args[i + 1].startswith("-"):
                val, i = args[i + 1], i + 2
            else:   # alone, or before another option: every grammar
                val, i = ",".join(VOCAB["grammar"]), i + 1
            vals = [v for v in val.split(",") if v]
            bad = [v for v in vals if v not in VOCAB["grammar"]]
            if bad or not vals:
                return usage(f"--grammar: {', '.join(bad) or repr(val)} is no grammar; they are {', '.join(VOCAB['grammar'])} (--grammar alone: all four)")
            grammar = set(vals)
            continue
        if "=" in a and a.split("=", 1)[0] in FILTERS:
            a, val = a.split("=", 1)
            i += 1
        elif a in FILTERS:
            if i + 1 >= len(args):
                return usage(f"{a} needs a value")
            val = args[i + 1]
            i += 2
        else:
            return usage(f"unknown option {a!r}")
        if a in want:
            return usage(f"{a} is given twice: put the alternatives in one flag ({a} x,y)")
        field, voc = FILTERS[a]
        if voc == "span":
            try:
                want[a] = parse_span(val, a)
            except ValueError as e:
                return usage(str(e))
        else:
            vals = [v for v in val.split(",") if v]
            bad = [v for v in vals if v not in VOCAB[voc]]
            if bad or not vals:
                return usage(f"{a}: unknown {bad or val!r}; known: {', '.join(VOCAB[voc])}")
            want[a] = set(vals)
    out = out or "table"
    if grammar is not None:
        if want:
            return usage(f"--grammar lists the shot-grammar cards, which {', '.join(want)} do not filter (those are for recipes)")
        return cmd_grammar(grammar, out)
    rows, recipes, broken = [], [], []
    for p in library_files():   # list only what validates, so a half-written recipe cannot crash the table
        try:
            fm, _ = read(p)
        except (FMError, OSError, UnicodeDecodeError):
            broken.append(p)
            continue
        if fm.get("kind", "recipe") != "recipe":
            continue
        if frontmatter_problems(fm):
            broken.append(p)
            continue
        recipes.append((fm["id"], p, fm))
    for p in broken:
        print(f"bin/vh recipes: skipped {rel(p)}: it does not pass `bin/vh recipes check`", file=sys.stderr)
    for rid, p, fm in sorted(recipes, key=lambda r: (r[2]["family"], r[0])):
        ok = True
        for flag, cond in want.items():
            field, voc = FILTERS[flag]
            v = fm.get(field)
            if voc == "span":
                try:
                    lo, hi = span(v, 0, 10 ** 9, field)
                except FMError:
                    ok = False
                    break
                if flag == "--seconds":
                    lo, hi = lo / FPS, hi / FPS
                ok = cond[0] <= hi and lo <= cond[1]
            elif flag == "--have":
                ok = set(v or []) - {"none"} <= cond
            elif isinstance(v, list):
                ok = bool(cond & set(v))
            else:
                ok = v in cond
            if not ok:
                break
        if ok:
            rows.append((rid, p, fm))
    if out == "ids":
        print("\n".join(r[0] for r in rows))
        return 0
    if out == "json":
        print(json.dumps([dict(fm, path=rel(p), **({"sample": rel(sample_path(p, rid))} if sample_path(p, rid).exists() else {}))
                          for rid, p, fm in rows], ensure_ascii=False, indent=1))
        return 0
    if out == "md":
        print("\n".join(index_row(rid, p, fm) for rid, p, fm in rows))
        return 0
    head = ("id", "family", "energy", "seconds", "intent", "engines", "status")
    table = [head] + [(rid, fm["family"], span_text(fm["energy"]), span_text(fm["duration_f"], FPS), ",".join(fm["intent"]),
                       ",".join(fm["engines"]), fm["status"]) for rid, _, fm in rows]
    widths = [max(len(r[c]) for r in table) for c in range(len(head))]
    for r in table:
        print("  " + "  ".join(x.ljust(w) for x, w in zip(r, widths)).rstrip())
    print(f"{len(rows)} of {len(recipes)} recipes. Read the whole recipe before using it: recipes/<family>/<id>.md;"
          " pacing skeletons: recipes/sequences/")
    return 0


def sample_times(fm):
    """The sheet's moments (s): the recipe's qa frames inside the sample's 5 s, filled out evenly to ten."""
    qa = sorted({round(min(4.9, max(0.1, f / FPS)), 2) for f in (fm.get("qa") or {}).values() if isinstance(f, int)})
    ts = qa[:]
    for x in (0.25, 1.25, 2.25, 3.25, 4.75, 0.75, 1.75, 2.75, 3.75, 4.25):
        if len(ts) >= 10:
            break
        if all(abs(x - y) > 0.2 for y in ts):
            ts.append(x)
    return sorted(ts)


def cmd_sample(args):
    pos = [a for a in args if not a.startswith("-")]
    style, draft, force, i = "swiss-grid-type", False, False, 0
    while i < len(args):
        if args[i] == "--draft":
            draft = True
        elif args[i] == "--force":
            force = True
        elif args[i] == "--style" and i + 1 < len(args):
            style = args[i + 1]; pos.remove(args[i + 1]); i += 1
        elif args[i].startswith("-"):
            return usage(f"unknown option {args[i]!r}")
        i += 1
    if len(pos) != 1:
        return usage("sample <id> [--style PRESET] [--draft] [--force]")
    lib = load_library()
    if pos[0] not in lib or lib[pos[0]][1].get("kind", "recipe") != "recipe":
        return usage(f"no recipe {pos[0]!r} (bin/vh recipes list --ids)")
    path, fm = lib[pos[0]]
    _, body = read(path)
    sketch = sketch_of(body)
    if sketch is None:
        print(f"bin/vh recipes sample: {rel(path)} has no sketch (a ```js block in 实现 that defines renderAt)", file=sys.stderr)
        return 2
    tokens = ROOT / "styles" / style / "tokens.json"
    if not tokens.is_file():
        return usage(f"no style {style!r} (bin/vh style list)")
    stage, default = f"recipe-{fm['id']}", style == "swiss-grid-type"   # the stage: never a style's slug
    sha = sketch_sha(sketch)
    out = sample_path(path, fm["id"]) if default else ROOT / "styles" / "_swatch" / "out" / stage / f"sheet-{style}.jpg"   # another skin: a look, not the record
    if default and out.exists() and fm.get("sketch_sha") == sha and not force:
        print(f"bin/vh recipes sample: {rel(out)} is the sketch as it is ({sha}); --force renders it again")
        return 0
    tmp = Path(tempfile.mkdtemp(prefix="vh-recipe-"))
    try:
        scene = tmp / stage   # the renderer names its stage and output after the folder
        scene.mkdir()
        (scene / "swatch.js").write_text(sketch, encoding="utf-8")
        shutil.copy2(tokens, scene / "tokens.json")
        r = subprocess.run([str(ROOT / "styles" / "_swatch" / "render.sh"), str(scene)] + (["--draft"] if draft else []))
        if r.returncode != 0:
            return 1
        hf = ROOT / "styles" / "_swatch" / "out" / scene.name / "hf.mp4"
        out.parent.mkdir(exist_ok=True)
        png = tmp / "sheet.png"
        subprocess.run(["uv", "run", "-q", "--no-project", "--with", "pillow", "python", str(ROOT / "tools" / "sheet.py"), str(hf), str(png), "5", "2",
                        str(SHEET_W // 5)], env=dict(os.environ, VH_SHEET_AT=",".join(str(x) for x in sample_times(fm))), check=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(png), "-vf", f"scale='min({SHEET_W},iw)':-2", "-q:v", "4", str(out)], check=True)
        if default:   # the sheet in git: record what it was rendered from
            set_sketch_sha(path, sha)
        print(f"bin/vh recipes sample: {rel(out)} ({out.stat().st_size // 1024} kB; the video: {rel(hf)}, not in git)")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    if argv[:1] == ["help"] or any(a in ("-h", "--help") for a in argv):   # `recipes list -h` too, not an unknown option
        print(__doc__.strip())
        return 0
    if not argv or argv[0].startswith("--"):   # bare `bin/vh recipes` (or only filters) lists, like `bin/vh style`
        return cmd_list(argv)
    if argv[0] == "list":
        return cmd_list(argv[1:])
    if argv[0] == "check":
        return cmd_check(argv[1:])
    if argv[0] == "sample":
        return cmd_sample(argv[1:])
    return usage(f"unknown subcommand {argv[0]!r}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
