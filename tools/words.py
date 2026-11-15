#!/usr/bin/env python3
"""bin/vh words — where a script leans on the sentence shapes model drafts reach for. A report: it never edits the script,
writes no replacement sentences, and exits 0 whatever it finds (2 on a usage error, 1 when there is no text to read).

  bin/vh words <project|SCRIPT.md|file.md|file.txt|audio/script.txt> [--col 旁白|字幕|<header>] [--style FILE] [--all] [--json]

What it reads: a project folder → its SCRIPT.md tables, else audio/script.txt. In a .md, every table with a 旁白 /
Narration column is read (a script in one table a chapter is read whole), or, where no table has one, every table with a
字幕 / Caption column; a header that starts with the word counts (旁白（定稿）), spaces aside; --col names another header.
Any other .md or .txt → its prose (headings, tables, code, HTML comments left out). audio/script.txt → what the voice
reads, parsed as bin/vh tts parses it: @speakers and @pronounce are directives, not speech; @id, a leading [direction],
a speaker's label once @speakers declared it (主持：…) and the English after || are left out. Line numbers are the file's.

The checks, each named by one paired experiment that set model drafts against human ones on the same topics (about
five million characters of Chinese prose; the ratio is how many times as often model drafts used it). Not re-measured
here, and measured on other writing than film scripts, so a count is a place to reread, not a verdict:
  not_but           不是 A 而是 B, 不是 A，(他)是 B, 不在于 A，在于 B, 与其说 A 不如说 B   3.4×
  colon_verdict     a full-width colon that hands over the conclusion (答案很简单：…)  2.1×
  dun_triple        three or more items in a row joined by 顿号 (A、B、C)              1.8×
  triple_parallel   three clauses in a row that start or end alike (排比)              2.75×
  long_attributive  a long run of modifiers before 的 and its noun, no pause in it     named, no ratio quoted
  chain_link        a paragraph (table row, script line) that opens on the words the last one ended on   named, no ratio quoted
How each is found is a heuristic of this tool's own (the 16-character run before 的, for one; the patterns are in this
file), so expect a miss or a stray hit now and then. A colon after a speech verb (他回忆：), before a quotation or a list,
or after a bare label (时间：…) is not counted; a run of names before 的 (…研究团队的成员) is not a long modifier.
Not found: whether a metaphor fits, which the same experiment found to be the real problem with metaphors and no
pattern can see; other ways of saying "not A but B" (并不…而…, 不…却…); 排比 whose clauses differ in length and share
neither a start nor an end. English text: none of these were measured on English, so it reports that and nothing else.

A project's own style comes first: under a heading 允许的句式 (or "Allowed patterns") in its STYLE.md, or in a file given
with --style, a list item naming a check (its id or Chinese name: "- 不是……而是：…") stops counting it, and a list item
holding a quoted sentence ("- “不是第一次，而是第三次”") stops counting the hits inside that sentence. Allowed hits are
summed, and listed with --all. A list item it cannot read as either is reported, not passed over.

--json, "version": 1 (fields are only added): {"version", "tool", "source", "input": {"kind": "table"|"script"|"text",
"column", "units"}, "lang": "zh"|"en", "chars", "checks": [{"id", "name", "ratio" (null when none is quoted), "count",
"allowed", "per_1000", "reading", "hits": [{"line", "text", "context", "allowed_by"?}]}], "allowed_rules": [{"rule",
"from"}], "allowed_unread": [{"item", "from"}], "not_checked", "note"}. chars counts Han characters, letters and digits
(punctuation and spaces not). column is the header read, or several joined with " / " when the tables differ.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jsonerr   # noqa: E402  (tools/jsonerr.py: a failure's --json record)


class Unreadable(Exception):
    """Nothing to read: (a tools/jsonerr.py code, the line a person reads)."""

CJK = r"㐀-䶿一-鿿豈-﫿"
IS_CJK = re.compile(f"[{CJK}]")
COUNTED = re.compile(f"[{CJK}A-Za-z0-9]")
END = "。！？!?；;…"
CLAUSE = re.compile(r"[，,；;。！？!?：:、“”\"‘’「」『』（）()—…\n]+")

CHECKS = [   # id, name, ratio from the experiment (None: named there, no ratio to quote), how to read a count
    ("not_but", "不是 A 而是 B", 3.4,
     "Model drafts used it about 3.4 times as often as human drafts on the same topics. Once can be the point of a line; "
     "the second time in a short script is more often habit than choice."),
    ("colon_verdict", "下结论的冒号", 2.1,
     "About 2.1 times as often in model drafts: the colon that announces a conclusion instead of letting the sentence get "
     "there. A colon before a list or a quotation is not counted."),
    ("dun_triple", "顿号连排三项", 1.8,
     "About 1.8 times as often in model drafts. A list that is really a list is fine; three items because three sounds "
     "complete is the habit."),
    ("triple_parallel", "三连排比", 2.75,
     "About 2.75 times as often in model drafts. One built on purpose can carry a peak; several read as a pattern."),
    ("long_attributive", "超长前置定语", None,
     "Named by the same experiment, with no ratio to quote. A long run of modifiers before the noun is hard to follow by "
     "ear; spoken Chinese usually breaks it into two clauses. The 16-character threshold is this tool's own."),
    ("chain_link", "段与段首尾相接", None,
     "Named by the same experiment, with no ratio to quote: each paragraph picking up the last one's final words. Once is "
     "a link; paragraph after paragraph, it is a tic."),
]
ALIASES = {   # what a STYLE.md list item may call a check (compared on its Han characters alone, or the id)
    "not_but": ("不是而是", "不是是", "与其说不如说"),
    "colon_verdict": ("冒号", "下结论的冒号"),
    "dun_triple": ("顿号", "顿号连排", "顿号连排三项"),
    "triple_parallel": ("排比", "三连排比", "三连"),
    "long_attributive": ("前置定语", "长定语", "超长前置定语"),
    "chain_link": ("首尾相接", "顶真", "段与段首尾相接"),
}
NOT_CHECKED = ["whether a metaphor fits (the experiment's finding about metaphors; a reader's call)",
               "other ways of saying not A but B (并不…而…, 不…却…), and 排比 whose clauses share neither a start, an end nor one frame",
               "the other habits playbook/09-narrative.md §10 lists (对仗, 或许, 某种意义上, a closing line after a dash): not measured"]


# ---------------------------------------------------------------- reading the input into units (paragraphs, rows, lines)

class Unit:
    """One paragraph, table row or script line: its text joined, and where each piece of it came from."""
    def __init__(self):
        self.text, self.starts = "", []   # starts: (offset into text, line number)

    def add(self, s, line):
        if s:
            self.starts.append((len(self.text), line))
            self.text += s

    def line(self, at):
        n = self.starts[0][1] if self.starts else 0
        for off, ln in self.starts:
            if off > at:
                break
            n = ln
        return n


def inline(s):
    s = re.sub(r"`[^`]*`", "", s)
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"(\*\*|__|\*|~~)", "", s)
    return s.strip()


def strip_comments(lines):
    """Lines with HTML comments and fenced code blanked (kept as empty lines, so the numbering holds)."""
    out, in_c, in_f = [], False, False
    for ln in lines:
        if in_f:
            out.append("")
            in_f = not ln.strip().startswith(("```", "~~~"))
            continue
        if not in_c and ln.strip().startswith(("```", "~~~")):
            out.append("")
            in_f = True
            continue
        s, keep = ln, ""
        while s:
            if in_c:
                j = s.find("-->")
                if j < 0:
                    s = ""
                else:
                    s, in_c = s[j + 3:], False
            else:
                j = s.find("<!--")
                if j < 0:
                    keep, s = keep + s, ""
                else:
                    keep, s, in_c = keep + s[:j], s[j + 4:], True
        out.append(keep)
    return out


def cells(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def tables(lines):
    """[(header cells, [(line number, cells)])] for each markdown table."""
    out, i = [], 0
    while i < len(lines) - 1:
        if lines[i].lstrip().startswith("|") and re.fullmatch(r"\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*", lines[i + 1]):
            head, rows, j = cells(lines[i]), [], i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j + 1, cells(lines[j])))
                j += 1
            out.append((head, rows))
            i = j
        else:
            i += 1
    return out


NARRATION = ("旁白", "narration", "vo", "voiceover")   # (compared with the header's spaces taken out, in lower case)
CAPTION = ("字幕", "caption", "captions", "on-screen")


def norm_head(h):
    return re.sub(r"\s+", "", h).lower()


def pick_column(head, names):
    """The first of names (in order: exact, then a header that starts with it) that this header row has."""
    low = [norm_head(h) for h in head]
    for n in names:
        if n in low:
            return low.index(n)
        if n != "vo":   # 旁白（字幕写法）, Narration (final)
            hit = next((i for i, h in enumerate(low) if h.startswith(n)), None)
            if hit is not None:
                return hit
    return None


def from_table(lines, want):
    """Every table with the column: --col's, else 旁白 / Narration where any table has one, else 字幕 / Caption (a script
    in one table a chapter is read whole). → (units, the column's header(s)), or (None, None) with no such table."""
    found = tables(lines)
    for names in ([norm_head(want)],) if want else (NARRATION, CAPTION):
        picked = [(head, rows, k) for head, rows in found for k in [pick_column(head, names)] if k is not None]
        if not picked:
            continue
        units, heads = [], []
        for head, rows, k in picked:
            if head[k] not in heads:
                heads.append(head[k])
            for ln, row in rows:
                cell = row[k] if k < len(row) else ""
                if re.fullmatch(r"\{[^{}]*\}", cell):   # a template placeholder, {两颗卫星…}
                    continue
                if re.match(r"^\**\d{1,2}\s", cell) and not re.search(f"[{END}，,]", cell):   # a chapter's title row, 03 刹车片：…
                    continue
                u = Unit()
                u.add(inline(cell.replace("<br>", "")), ln)
                if u.text:
                    units.append(u)
        return units, " / ".join(heads)
    return None, None


def from_script_txt(lines):
    """What the voice reads, parsed as tools/audio/tts.py's parse_script does: # comments, the @speakers and @pronounce
    lines (directives, not speech), @id, a [direction] at the start, a speaker's label only once @speakers declared it,
    and the side before || (the side tts reads in Chinese; a line without || as it is)."""
    units, speakers = [], set()
    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        head = re.fullmatch(r"@speakers((?:\s+[^\s=]+=\S+)+)", line)
        if head:
            speakers.update(p.split("=", 1)[0] for p in head.group(1).split())
            continue
        if re.fullmatch(r"@pronounce\s+(.+/.+)", line):
            continue
        if line.startswith("@") and " " in line:
            line = line.split(" ", 1)[1]
        line = re.sub(r"^\[[^\]]+\]\s*", "", line.strip())
        m = re.match(r"(\S+?)\s*[:：]\s*", line) if speakers else None
        if m and m.group(1) in speakers:   # 主持：… once @speakers 主持=Kore said so; an undeclared 注意：… stays speech
            line = re.sub(r"^\[[^\]]+\]\s*", "", line[m.end():])
        u = Unit()
        u.add(line.partition("||")[0].strip(), i)
        if u.text:
            units.append(u)
    return units


def from_prose(lines):
    units, u, front = [], Unit(), bool(lines) and lines[0].strip() == "---"
    for i, ln in enumerate(lines, 1):
        if front:   # YAML front matter
            if i > 1 and ln.strip() == "---":
                front = False
            continue
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("|") or re.fullmatch(r"[-*_]{3,}", s):
            if u.text:
                units.append(u)
            u = Unit()
            continue
        s = re.sub(r"^(>\s*)+", "", s)
        s = re.sub(r"^([-*+]|\d+[.)])\s+", "", s)
        if u.text and re.match(r"^[A-Za-z0-9]", s) and re.search(r"[A-Za-z0-9]$", u.text):
            u.add(" ", i)
        u.add(inline(s), i)
    if u.text:
        units.append(u)
    return units


def read_input(path, col):
    """(units, kind, column, the file read). A folder is a project: SCRIPT.md's table, else audio/script.txt."""
    p = Path(path)
    if p.is_dir():   # SCRIPT.md's table, else what the voice reads (audio/script.txt), else SCRIPT.md's prose
        script, spoken = p / "SCRIPT.md", p / "audio" / "script.txt"
        found = read_input(script, col) if script.is_file() else None
        if found and found[1] == "table" and found[0]:
            return found
        if spoken.is_file() and not col:
            got = read_input(spoken, None)
            if got[0]:
                return got
        if found and found[0]:
            return found
        raise Unreadable("not_found", f"words: {path} has no SCRIPT.md and no audio/script.txt with text to read")
    try:
        text = p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise Unreadable("not_found" if isinstance(e, OSError) else "invalid", f"words: cannot read {path}: {e}")
    lines = strip_comments(text.splitlines())
    if p.suffix.lower() == ".md":
        units, column = from_table(lines, col)
        if units is not None:
            return units, "table", column, p
        if col:
            raise Unreadable("invalid", f"words: {path} has no table with a column headed {col!r}")
        return from_prose(lines), "text", None, p
    body = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if p.name == "script.txt" or (body and sum(ln.lstrip().startswith("@") for ln in body) * 2 >= len(body)):
        return from_script_txt(text.splitlines()), "script", None, p
    return from_prose(lines), "text", None, p


# ---------------------------------------------------------------- the checks

def sentence_at(t, a, b):
    """The sentence around t[a:b], for the context field."""
    s = max(t.rfind(c, 0, a) for c in END + "\n") + 1
    e = min([j for j in (t.find(c, b) for c in END + "\n") if j >= 0] or [len(t)])
    return t[s:min(len(t), e + 1)].strip()


NOT_BUT = [
    re.compile(r"(?<![是要可])(?:不是|并不是|并非|不再是)[^。！？!?；;\n]{1,30}?[，,；;—…\s]*(?:而是|而在于)"),
    re.compile(r"(?<![是要可])(?:不是|并不是)[^。！？!?；;\n，,]{1,20}[，,]\s*(?:[他她它我你这那]们?)?是(?![不否])"),   # 他不是医生，他是…
    re.compile(r"不在于[^。！？!?；;\n，,]{1,20}[，,]\s*(?:而是?)?在于"),   # 问题不在于速度，在于时间
    re.compile(r"与其说[^。！？!?\n]{1,30}?不如说"),
]


def find_not_but(t):
    seen = []
    for rx in NOT_BUT:
        for m in rx.finditer(t):
            if not any(a <= m.start() < b for a, b in seen):
                seen.append((m.start(), m.end()))
    return sorted(seen)


SPEECH = re.compile(r"((说|道|答|回|讲|喊|叫|写|念|称|想|笑|骂|吼|表示|宣布|提到|回忆|心想|感叹|解释|补充|强调|承认|指出|认为|坦言|"
                    r"记得|嘟囔|嘀咕|透露|回应|描述|形容|发问)(了|着|过|道)?(她|他|我|你|它|我们|你们|他们|她们|大家)?"
                    r"(一句|一声|一个词|一句话|一行字?)?(话)?|(问|告诉|审问|回答|提醒|追问|反问)[^：，。]{0,5})$")   # 她说：, 他回忆：, 有人问她：
INTRO = re.compile(r"((第一|最后|下一|上一|这|那|一)(句|个词|行|段|条)(话)?(是|写着|写的是)?|[两三四五六几]+(个|种|件|样|条|点|句)[^：，。]{0,6})$")
VERDICT = re.compile(r"^(答案|结论|真相|原因|关键|结果|秘密|重点|核心|代价|区别|办法|方法|道理|本质|问题|事实)$")   # 答案：… is the shape


def find_colon(t):
    out = []
    for m in re.finditer("：", t):
        i = m.start()
        s = max(t.rfind(c, 0, i) for c in END + "\n") + 1
        before = t[s:i]
        e = min([j for j in (t.find(c, i + 1) for c in END + "\n") if j >= 0] or [len(t)])
        after = t[i + 1:e].strip()
        if (s, e) in out or len(IS_CJK.findall(before)) < 2 or not after or len(after) > 20:   # (a sentence once, however many colons)
            continue
        if after[0] in "“\"「『‘(（" or re.match(r"\d+[.)、]", after) or "、" in after or after.count("，") > 1:
            continue
        if SPEECH.search(before) or INTRO.search(before):   # 她说：…, 书的第一句是：…, 有两个关键词：…
            continue
        lead = before.strip()
        if len(lead) <= 4 and IS_CJK.fullmatch(lead[:1] or "x") and not re.search("[是很就只都最才]", lead) and not VERDICT.match(lead):
            continue   # a label, as captions write them: 时间：晚上八点。地点：老城区。
        out.append((s, e))
    return out


DUN = re.compile(r"[^\s、，,。；;：:！？!?“”\"「」（）()]{1,10}(?:、[^\s、，,。；;：:！？!?“”\"「」（）()]{1,10}){2,}")


def find_dun(t):
    out = []
    for m in DUN.finditer(t):
        items = m.group().split("、")
        cut = max(0, len(items[0]) - 4)    # the match runs into the words around the list (no spaces to stop it), so its
        over = max(0, len(items[-1]) - 6)  # ends are cut and marked with …: …克服延迟、抖动、丢包和功耗; the context has it whole
        a, b = m.start() + cut, m.end() - over
        out.append((a, b, ("…" if cut else "") + t[a:b] + ("…" if over else "")))
    return out


def clauses(t):
    out, pos = [], 0
    for m in CLAUSE.finditer(t + "\n"):
        c = t[pos:m.start()].strip()
        if c:
            off = t.index(c, pos)
            out.append((off, off + len(c), c))
        pos = m.end()
    return out


def common(a, b, rev=False):
    if rev:
        a, b = a[::-1], b[::-1]
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n] and IS_CJK.match(a[n]):
        n += 1
    return n


def same_shape(cs, loose=True):
    lens = [len(c) for c in cs]
    if min(lens) < 2 or max(lens) > 2.5 * min(lens):
        return False
    pre = min(common(cs[0], c) for c in cs[1:])
    suf = min(common(cs[0], c, rev=True) for c in cs[1:])
    if max(pre, suf) >= 2 and max(pre, suf) < min(lens):
        return True
    if loose and pre >= 1 and max(lens) <= 5 and pre < min(lens):   # 更快，更高，更远
        return True
    if pre >= 1 and len(set(lens)) == 1 and lens[0] <= 8:   # one frame, the words swapped: 让协作更顺畅，让创新更自由
        same = sum(1 for i in range(lens[0]) if IS_CJK.match(cs[0][i]) and all(c[i] == cs[0][i] for c in cs[1:]))
        return 2 <= same < lens[0]
    return False


def alike(cs):
    if same_shape(cs):
        return True
    for k in (1, 2):   # the subject in the first clause alone: 它让沟通更高效，让协作更顺畅，让创新更自由
        if len(cs[0]) > k + 1 and cs[0][k] == cs[1][0] == cs[2][0] and same_shape([cs[0][k:]] + cs[1:], loose=False):
            return True
    return False


def find_triple(t):
    cl, out, i = clauses(t), [], 0
    while i + 2 < len(cl):
        if alike([c for _, _, c in cl[i:i + 3]]):
            j = i + 3
            while j < len(cl) and alike([cl[i][2], cl[i + 1][2], cl[j][2]]):
                j += 1
            out.append((cl[i][0], cl[j - 1][1]))
            i = j
        else:
            i += 1
    return out


MARK = re.compile(r"[一这那每某][个种位场段次件部本条项些群名座片家]|了|是|有|把|让"   # where a modifier run starts, roughly:
                  r"|开始|进入|尝试|成为|变成|带来|提出|找到|看到|发现|需要|出现|做出|给出|留下|探索出|递过来")   # after a measure word or a verb


CLAUSAL = re.compile("[被在把了过着地得不没很最更都也又就才从对向给让使所而因为曾已正将能会要]")   # a modifier with a clause in it


def find_long_attr(t):
    out = []
    for a, b, c in clauses(t):
        for m in re.finditer("的", c):
            k = m.start()
            if k + 1 >= len(c) or not IS_CJK.match(c[k + 1]) or c[k + 1] == "确" or (k and c[k - 1] in "目我你他她它们己"):   # 的确, 目的, a possessive
                continue
            head = c[:k]
            marks = [x.end() for x in MARK.finditer(head)]
            run = head[marks[-1]:] if marks else head
            if len(IS_CJK.findall(run)) >= 16 and CLAUSAL.search(run):   # a name alone (中国科学院…研究团队的) is not one
                out.append((a + k - len(run), a + k + 1, run + "的…"))
                break
    return out


LEAD = re.compile(r"^(?:而|但|可|这|那|于是|所以|因为|而且|就|也|还|更|再)?")


def find_chain(units):
    out = []
    for prev, nxt in zip(units, units[1:]):
        p = re.sub(f"[^{CJK}A-Za-z0-9]+$", "", prev.text)
        q = nxt.text.lstrip("“”\"「」『』‘’（(—… ")
        q = q[LEAD.match(q).end():]
        for k in range(min(6, len(p)), 1, -1):
            tail = p[-k:]
            if not all(IS_CJK.match(ch) for ch in tail):
                continue
            j = q.find(tail)
            if 0 <= j <= 3:
                if len(tail) > 2 and tail[0] in "个只张本种位条件":   # 一个本子 / 这个本子: the noun, not its measure word
                    tail = tail[1:]
                start = nxt.text.find(tail)
                k = len(tail)
                out.append((nxt, start, start + k, f"{prev.text[-12:]} / {nxt.text[:16]}"))
                break
    return out


# ---------------------------------------------------------------- the project's own style

def allowed_rules(files):
    """([(rule, file)], [(an item it could not read, file)]): rule is a check id, or ("text", a quoted sentence)."""
    rules, unread = [], []
    for f in files:
        try:
            lines = Path(f).read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        level = None
        for ln in lines:
            h = re.match(r"^(#{1,6})\s*(.+?)\s*#*\s*$", ln)
            if h:
                if level is not None and len(h.group(1)) <= level:
                    level = None
                if re.match(r"^(允许的句式|allowed patterns)", h.group(2), re.I):
                    level = len(h.group(1))
                continue
            if level is None:
                continue
            m = re.match(r"^\s*[-*+]\s+(.+)$", ln)
            if not m:
                continue
            item = m.group(1).strip()
            q = re.match(r"^[“\"「『](.+?)[”\"」』]", item)
            if q:
                rules.append((("text", q.group(1)), str(f)))
                continue
            name = re.split(r"[：:（(—，,；;]", item, maxsplit=1)[0].strip()   # 排比，片尾故意的 · 排比：… · 排比（…）
            ids = [cid for cid, *_ in CHECKS if name.lower().replace("-", "_") == cid]
            han = "".join(IS_CJK.findall(name))
            ids += [cid for cid, al in ALIASES.items() if han and han in al and cid not in ids]
            rules += [(cid, str(f)) for cid in ids]
            if not ids:
                unread.append((item, str(f)))
    return rules, unread


def style_files(src, extra):
    out = list(extra)
    d = src.parent
    for folder in (d, d.parent, d.parent.parent):
        f = folder / "STYLE.md"
        if f.is_file():
            out.insert(0, f)
            break
        if (folder / "BRIEF.md").is_file():
            break
    return out


# ---------------------------------------------------------------- the report

def run(path, col=None, extra_styles=(), show_all=False):
    units, kind, column, src = read_input(path, col)
    if not units:
        raise Unreadable("invalid", f"words: no text to read in {src}")
    alltext = "\n".join(u.text for u in units)
    han, letters = len(IS_CJK.findall(alltext)), len(re.findall(r"[A-Za-z]", alltext))
    chars = len(COUNTED.findall(alltext))
    lang = "zh" if han and han * 10 >= 3 * (han + letters) else "en"
    rules, unread = allowed_rules(style_files(src, extra_styles))
    report = {"version": 1, "tool": "words", "source": str(src), "input": {"kind": kind, "column": column, "units": len(units)},
              "lang": lang, "chars": chars, "checks": [], "allowed_rules": [], "not_checked": list(NOT_CHECKED),
              "note": "A report: the hits are places to reread, not errors. The ratios were measured once, on other writing; "
                      "a count says where to look, not whether the script is good. Edit only what the person agrees to, "
                      "and only the words hit."}
    report["allowed_rules"] = [{"rule": r if isinstance(r, str) else f"“{r[1]}”", "from": f} for r, f in rules]
    report["allowed_unread"] = [{"item": i, "from": f} for i, f in unread]
    if lang == "en":
        report["note"] = ("These markers were measured on Chinese prose; none has been measured on English here, so "
                          "English text gets no counts.")
        report["not_checked"].insert(0, "every check: the text is English")
        return report
    finders = {"not_but": find_not_but, "colon_verdict": find_colon, "dun_triple": find_dun,
               "triple_parallel": find_triple, "long_attributive": find_long_attr}
    found = {cid: [] for cid, *_ in CHECKS}   # (unit, start, end, the words shown, the context)
    for u in units:
        for cid, fn in finders.items():
            for a, b, *show in fn(u.text):
                found[cid].append((u, a, b, show[0] if show else u.text[a:b].strip(), sentence_at(u.text, a, b)))
    for nxt, a, b, ctx in find_chain(units):
        found["chain_link"].append((nxt, a, b, nxt.text[a:b], ctx))

    def inside(u, a, b, q):   # the hit lies within an occurrence of the quoted sentence in the script
        o = u.text.find(q)
        while o >= 0:
            if o <= a and b <= o + len(q):
                return True
            o = u.text.find(q, o + 1)
        return False
    for cid, name, ratio, reading in CHECKS:
        whole = next((f for r, f in rules if r == cid), None)
        hits, n_allowed = [], 0
        for u, a, b, text, ctx in found[cid]:
            by = whole or next((f for r, f in rules if isinstance(r, tuple) and inside(u, a, b, r[1])), None)
            h = {"line": u.line(a), "text": text, "context": ctx}
            if by:
                h["allowed_by"] = by
                n_allowed += 1
            hits.append(h)
        count = len(hits) - n_allowed
        report["checks"].append({"id": cid, "name": name, "ratio": ratio, "count": count, "allowed": n_allowed,
                                 "per_1000": round(count * 1000 / chars, 1) if chars else 0.0, "reading": reading,
                                 "hits": hits if show_all else [h for h in hits if "allowed_by" not in h]})
    return report


def shown(p):
    try:
        return str(Path(p).resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(p)


def text_report(r):
    inp = r["input"]
    what = {"table": f"the {inp['column']} column, {inp['units']} rows", "script": f"{inp['units']} script lines",
            "text": f"{inp['units']} paragraphs"}[inp["kind"]]
    out = [f"words: {shown(r['source'])} ({what}, {r['chars']} characters)"]
    if r["lang"] == "en":
        out += ["  " + r["note"], ""]
        return "\n".join(out)
    out += ["  " + r["note"], ""]
    for c in r["checks"]:
        ratio = f"model drafts {c['ratio']}× human ones" if c["ratio"] else "named, no ratio"
        extra = f" · {c['allowed']} allowed by the style guide" if c["allowed"] else ""
        out.append(f"{c['name']} ({c['id']}): {c['count']} · {c['per_1000']} per 1000 characters · {ratio}{extra}")
        if c["count"] or c["hits"]:
            out.append("  " + c["reading"])
        for h in c["hits"][:12]:
            tag = "  (allowed)" if "allowed_by" in h else ""
            ctx = h["context"] if h["context"].rstrip(END) != h["text"].rstrip(END) else ""
            ctx = f"   ← {ctx if len(ctx) <= 60 else ctx[:58] + '…'}" if ctx else ""
            out.append(f"  L{h['line']}  {h['text']}{ctx}{tag}")
        if len(c["hits"]) > 12:
            out.append(f"  … {len(c['hits']) - 12} more (--json lists them all)")
    if r["allowed_rules"]:
        out += ["", "style guide: " + "; ".join(f"{a['rule']} ({shown(a['from'])})" for a in r["allowed_rules"])]
    if r.get("allowed_unread"):
        out += ["style guide, not understood (name a check, e.g. 排比 or not_but, or quote a sentence): "
                + "; ".join(f"- {a['item']} ({shown(a['from'])})" for a in r["allowed_unread"])]
    out += ["", "not checked: " + "; ".join(r["not_checked"])]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bin/vh words", description=__doc__.split("\n\n", 1)[0],
                                 epilog=__doc__.split("\n\n", 1)[1], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", help="a project folder, SCRIPT.md, a .md or .txt, or audio/script.txt")
    ap.add_argument("--col", help="the table column to read (default: 旁白 / Narration, else 字幕 / Caption)")
    ap.add_argument("--style", action="append", default=[], help="another file with an 允许的句式 section (repeatable)")
    ap.add_argument("--all", action="store_true", help="list allowed hits too")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        r = run(a.path, a.col, a.style, a.all)
    except Unreadable as e:
        return jsonerr.fail(e.args[0], e.args[1], rc=1)
    print(json.dumps(r, ensure_ascii=False, indent=1) if a.json else text_report(r))
    return 0


if __name__ == "__main__":
    sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
