"""Where a caption breaks: at word boundaries, chosen by dynamic programming; and when each piece shows, from the words' times.

Used by tools/audio/captions.py (bin/vh captions). Word boundaries come from jieba when it is installed (bin/vh captions
brings it through uv), else from a fallback that keeps Latin words and numbers whole and may break between any two Chinese
characters, as before. Each piece costs 150 and each break what it is worth below; the lowest total wins:
  - a piece wider than the limit is not allowed (one token wider than the limit stands alone);
  - pieces of even width (the sentence's width split evenly);
  - a break right after a comma, a pause or a colon is cheap; one that leaves a piece ending on 把 被 将 对 向 从 在 和 与 跟 及
    或 是 让 给 比 为 由, or the next starting on 了 的 地 得 着 过 吗 呢 吧 啊 么 们 (as one-character words) costs more;
  - a piece whose last pause leaves only a word or two after it ("怎么测，写"), or that starts with one character and a
    pause ("纸，折了"), costs more;
  - a closing mark never starts a piece and an opening mark never ends one; a colon before a quote is a good break;
  - in wrapped lines, the punctuation at a line's end hangs past the limit (it is not counted), as it always did.
A sentence ends at 。？！… and at a Latin . ? ! that no ASCII letter or digit follows (3.5, Node.js and 12:30 stay whole), as
the canvas-film engine cuts its own captions.
A manual break table (audio/capbreaks.json: a list of phrases, or {line id: [phrases]}) starts a new piece at each phrase
(an empty phrase, or one that starts inside a Latin word, is left out). In wrapped lines it is used only where a caption
needs more than one line.
"""
import difflib, json, math, re, unicodedata
from pathlib import Path

STOPS = "。？！?!….．"
PAUSES = "，、：；,;:"
CLOSERS = "”’」』）》)\"'】〉"
OPENERS = "“‘「『（《(【〈"
END_BAD = set("把被将对向从在和与跟及或是让给比为由")
START_BAD = set("了的地得着过吗呢吧啊么们")
PIECE = 150   # the cost of one more piece (line or card), against the costs of bad breaks below
LATIN = re.compile(r"[A-Za-z0-9.+\-_/%#&@']+")

try:
    import logging
    import jieba
    jieba.setLogLevel(logging.ERROR)
    HAVE_JIEBA = True
except Exception:   # not installed, or broken: the fallback below
    HAVE_JIEBA = False


def width(s):
    """Display width: a full-width character is 1, ASCII is 1/2 (as wrap_zh counts)."""
    return sum(0.5 if ord(c) < 128 else 1.0 for c in s)


def raw_tokens(text):
    if HAVE_JIEBA:
        return [t for t in jieba.lcut(text, HMM=True) if t]
    return re.findall(r"[A-Za-z0-9_./<>:@#%&+=\-]+|\s+|.", text)


def tokens(text, forced=()):
    """The text as break units, every character in one: Latin words and numbers whole ("Node.js", "GPT-4", "3.5"),
    punctuation and spaces kept with the word before (an opening mark with the word after), split at each forced index."""
    toks, pos = [], 0
    for t in raw_tokens(text):
        toks.append([pos, t]); pos += len(t)
    # Latin runs without a space between them are one word (jieba cuts "Node.js" into three)
    merged = []
    for p, t in toks:
        if merged and LATIN.fullmatch(t) and LATIN.fullmatch(merged[-1][1]) and merged[-1][0] + len(merged[-1][1]) == p:
            merged[-1][1] += t
        else:
            merged.append([p, t])
    # punctuation and spaces go with the word before; an opening mark with the word after
    out = []
    for p, t in merged:
        if out and (t.isspace() or all(c in STOPS + PAUSES + CLOSERS for c in t)):
            out[-1][1] += t
        elif out and all(c in OPENERS for c in out[-1][1]):
            out[-1][1] += t
        else:
            out.append([p, t])
    # forced starts (the break table): a token that holds one is cut there
    for f in sorted(set(forced)):
        for k, (p, t) in enumerate(out):
            if p < f < p + len(t):
                out[k:k + 1] = [[p, t[:f - p]], [f, t[f - p:]]]
                break
    return [(p, t) for p, t in out]


def display(s, cards):
    """What a piece shows: as it is for wrapped lines; for one-line cards, pauses become a space and the closing
    punctuation at the end goes (？ ！ … stay), as the canvas-film engine shows them."""
    if not cards:
        return s.strip()
    s = re.sub(r"[，、：；。,;:]+\s*$", "", s.strip())
    s = re.sub(r"(?<!\.)\.\s*$", "", s)
    return re.sub(r"\s+", " ", re.sub(r"[，、：；]", " ", s)).strip()


ASCII_ALNUM = re.compile(r"[A-Za-z0-9]")


def sentences(toks):
    """Token lists, cut after a sentence end: 。？！… always; a Latin . ! ? only when the character right after it in the
    text (a space, a closing mark, a Chinese character) is not an ASCII letter or digit."""
    out, cur = [], []
    for k, (p, t) in enumerate(toks):
        cur.append((p, t))
        core = t.rstrip(CLOSERS + " \t")
        if not core or core[-1] not in STOPS:
            continue
        after = t[len(core):] + (toks[k + 1][1] if k + 1 < len(toks) else "")
        if core[-1] in ".!?" and ASCII_ALNUM.match(after[:1] or " "):
            continue   # 3.5, Node.js, "e.g.x": the text goes on
        out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def best_breaks(toks, limit, cards, forced=()):
    """[(start index, end index)] of pieces over toks, by DP: each piece costs PIECE, plus the cost of its breaks, so
    one more piece is worth it only to avoid a bad break."""
    n = len(toks)
    if not n:
        return []
    forced = set(forced)
    total = width(display("".join(t for _, t in toks), cards))
    target = total / max(1, math.ceil(total / limit))
    starts = [p for p, _ in toks]
    INF = float("inf")

    def cost(i, j):
        text = "".join(t for _, t in toks[i:j])
        # a wrapped line's closing punctuation hangs past the limit; a card shows its ？！… and counts them
        w = width(display(text, cards) if cards else text.strip().rstrip(STOPS + PAUSES + CLOSERS + " "))
        if w > limit and j - i > 1:
            return INF
        if any(starts[k] in forced for k in range(i + 1, j)):
            return INF   # a forced start inside this piece
        c = 100 * ((target - w) / limit) ** 2 + (500 if w > limit else 0)
        last = toks[j - 1][1].strip()
        if j < n:   # the break after this piece
            core = last.rstrip(CLOSERS)
            if core[-1:] and core[-1] in PAUSES:
                c -= 30
                if core[-1] in "：:" and toks[j][1][:1] in OPENERS: c -= 50   # a colon before a quote: break there
            elif len(core) == 1 and core in END_BAD:
                c += 60
            nxt = toks[j][1].strip()
            if len(nxt) == 1 and nxt in START_BAD:
                c += 60
            elif len(nxt.rstrip(PAUSES + STOPS + CLOSERS)) == 1 and nxt[-1:] in PAUSES + STOPS:
                c += 200   # "一张 / 纸，折了": one character stranded before a pause at the next piece's start (worth one more piece)
        inner = [m.end() for m in re.finditer(f"[{re.escape(PAUSES)}]", text.rstrip(PAUSES + CLOSERS + STOPS + " "))]
        if inner and width(text[inner[-1]:].strip(PAUSES + STOPS + CLOSERS + " ")) <= 2:
            c += 80   # "怎么测，写": a word or two left after the last pause
        return c

    dp = [(0, 0.0)] + [(INF, INF)] * n
    back = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(max(0, j - 80), j):
            if dp[i][0] == INF:
                continue
            c = cost(i, j)
            if c == INF:
                continue
            cand = (0, dp[i][1] + c + PIECE)
            if cand < dp[j]:
                dp[j], back[j] = cand, i
    if dp[n][0] == INF:   # nothing fits (should not happen: a single token always may stand alone)
        return [(k, k + 1) for k in range(n)]
    cuts, j = [], n
    while j > 0:
        cuts.append((back[j], j)); j = back[j]
    return cuts[::-1]


def load_breaks(audio_dir):
    """The manual break table: {line id: [phrases]} with "*" for every line, from audio/capbreaks.json."""
    f = Path(audio_dir) / "capbreaks.json"
    if not f.is_file():
        return {}
    j = json.loads(f.read_text(encoding="utf-8"))
    if isinstance(j, list):
        return {"*": [str(x) for x in j]}
    return {str(k): [str(x) for x in (v if isinstance(v, list) else [v])] for k, v in j.items()}


def forced_starts(text, line_id, table):
    """Where the break table starts a piece: each phrase's every place in the text, but not at its start, not for an
    empty phrase, and not inside a Latin word or number ("Node.js" stays whole)."""
    out = []
    for ph in table.get("*", []) + table.get(str(line_id), []):
        if not ph.strip():
            continue
        for m in re.finditer(re.escape(ph), text):
            i = m.start()
            if i > 0 and not (LATIN.fullmatch(text[i - 1]) and LATIN.fullmatch(text[i])):
                out.append(i)
    return out


def pieces(text, limit, cards, line_id=None, table=None):
    """[(start char index, raw text)] of a line's pieces: one-line cards (cards=True: never across a sentence end)
    or the lines one caption wraps into."""
    forced = forced_starts(text, line_id, table or {})
    toks = tokens(text, forced)
    groups = sentences(toks) if cards else [toks]
    out = []
    for g in groups:
        for i, j in best_breaks(g, limit, cards, forced):
            raw = "".join(t for _, t in g[i:j])
            if re.sub(r"[\s\W_]+", "", raw):   # a "……" alone is a pause, not a piece
                out.append((g[i][0], raw))
    return out


# ---- times ----
def letters(s):
    return [c for c in unicodedata.normalize("NFKC", s).lower() if not (c.isspace() or unicodedata.category(c)[0] in "PSZ")]


def letter_times(text, words, start, end):
    """The time each letter of text is spoken (punctuation and spaces left out): matched to the aligned words' letters,
    interpolated between matches; spread evenly over start–end without words."""
    a = letters(text)
    if not a:
        return []
    hc, ht = [], []
    for w in words or []:
        cs = letters(str(w.get("w", "")))
        ws, we = float(w.get("start", start)), float(w.get("end", w.get("start", start)))
        for k, c in enumerate(cs):
            hc.append(c); ht.append(ws + (we - ws) * k / len(cs))
    anchors = [(-1, start)]
    if hc:
        for blk in difflib.SequenceMatcher(None, a, hc, autojunk=False).get_matching_blocks():
            for k in range(blk.size):
                anchors.append((blk.a + k, ht[blk.b + k]))
    anchors.append((len(a), end))
    T = [None] * len(a)
    for (i0, t0), (i1, t1) in zip(anchors, anchors[1:]):
        for q in range(i0 + 1, i1):
            T[q] = t0 + (t1 - t0) * (q - i0) / (i1 - i0)
        if i1 < len(a):
            T[i1] = t1
    return T


def letter_index(text, char_index):
    """How many letters come before char_index in text."""
    return len(letters(text[:char_index]))
