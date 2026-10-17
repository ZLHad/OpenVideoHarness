"""Confirmed alerts: the project's confirmed.json, where the author says that a detector's finding is intended.

A detector judges by thresholds, and at one place it can be wrong, or right only in context: a one-frame flash the
storyboard asks for, a sparse passage the score is written with. An entry names that place, why it is intended, the
file that shows it, and the key the tool printed: a coarse fingerprint of the picture or the sound there. The report
keeps the raw finding and says it is confirmed; when the picture or the sound there changes, or the finding moves, the
key no longer matches and the confirmation lapses, so the finding counts again. Floors are never confirmed here: they
are fixed, or relaxed by the user's own words in REVIEW.md (CLAUDE.md, 规则冲突时). playbook/02-verification.md, 确认告警.

<project>/confirmed.json (the project is the nearest folder upwards that holds BRIEF.md):
  {"items": [{"tool": "check.iso", "at": "1.000", "key": "pic:…", "why": "…", "evidence": "STORYBOARD.md S01", "date": "…"}]}
  tool      check.iso    an isolated frame (bin/vh check)
            qa.dropout   a dropout, qa.pump a pumping dip (bin/vh qa, scan)
            qa.click     clicks over a span a-b, with "n": how many there were when confirmed (more lapse it)
  at        seconds or a span a-b, as the tool's `confirm?` line has it (a click span may be widened by hand)
  key       copied from that line; never written by hand
  why       what was intended (a shot id helps)
  evidence  a file in the project that shows it (a #part after it is fine; several separated by ";"): the storyboard,
            the score, a strip or a crop. A sound cannot be heard by an agent: point at the score or the stems' numbers.
Used by tools/isoframes.py and tools/audio/qa.py; standard library only.
"""
import datetime, json, re
from pathlib import Path

NAME = "confirmed.json"
KINDS = {"check.iso": "isolated frame", "qa.dropout": "dropout", "qa.pump": "pumping dip", "qa.click": "click span"}
NOT = {   # kinds that are never confirmed here, and what to do instead
    "qa.silence": "digital silence is a floor: fix it, or record the user's own words in REVIEW.md",
    "qa.cue": "a declared sync point is a floor, and the cue check is not confirmed (not for now)",
    "check.spec": "a render that does not match the BRIEF is a build error: fix the render, or the BRIEF if the spec changed",
    "check.gate": "the gates are the person's: their words in REVIEW.md",
    "check.static": "the motion lines are advice, nothing to confirm (a reviewer's point you keep: 不采纳 in NOTES)",
    "check.cut": "the motion lines are advice, nothing to confirm (a reviewer's point you keep: 不采纳 in NOTES)",
    "readcheck.fail": "text under the reading floor is a floor: fix it, or record the user's own words in REVIEW.md",
}
MANY = 5   # this many confirmations of one kind in a film: the detector may be what is wrong
DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"   # a key's levels, one character each
NUM = r"(\d+(?:\.\d*)?|\.\d+)"


class Bad(ValueError):
    """confirmed.json cannot be read: a tool stops instead of checking without it (a typo must not switch it off)"""


def code(levels):
    """Levels 0–63 as a key's characters."""
    return "".join(DIGITS[int(v)] for v in levels)


def uncode(text):
    """A key's characters as levels, or None when one is not a key character."""
    try:
        return [DIGITS.index(ch) for ch in text]
    except ValueError:
        return None


def project_of(path):
    """The nearest folder, from `path` upwards, that holds BRIEF.md; None outside a project."""
    p = Path(path).resolve()
    for d in ([p] if p.is_dir() else []) + list(p.parents):
        if (d / "BRIEF.md").is_file():
            return d
    return None


def span(at):
    """"1.0" / 1.0 / "84.2-86.1" → (a, b), else None."""
    if isinstance(at, (int, float)) and not isinstance(at, bool):
        return float(at), float(at)
    m = re.fullmatch(rf"\s*{NUM}(?:\s*-\s*{NUM})?\s*", at) if isinstance(at, str) else None
    if not m:
        return None
    a, b = float(m.group(1)), float(m.group(2) if m.group(2) is not None else m.group(1))
    return (a, b) if b >= a else None


def evidence_problem(ev, home):
    """None when at least one part of `ev` names a file under `home` and none names a missing one; else why not."""
    found, missing = [], []
    for part in (x.strip() for x in ev.split(";") if x.strip()):
        word = part.split()[0].split("#")[0]
        if "/" in word or re.search(r"\.[A-Za-z0-9]{1,5}$", word):   # a path, not a word of prose
            (found if (home / word).exists() else missing).append(word)
    if missing:
        return "evidence names a file that is not in the project: " + ", ".join(missing)
    return None if found else "evidence names no file in the project (the storyboard, the score, a strip or a crop)"


def load(path, prefix):
    """The entries of `path` whose tool starts with `prefix` ("check.", "qa."): (taken, refused). taken: dicts with
    their span in "_a", "_b" and their place in the file in "_n"; refused: [(n, at, reason)]. Raises Bad when the
    file is not a JSON object with an "items" list."""
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        raise Bad(f"{p}: {getattr(e, 'strerror', None) or e}") from None
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise Bad(f'{p}: expected {{"items": [ … ]}} (tools/confirm.py)')
    taken, refused = [], []
    for n, it in enumerate(items, 1):
        tool = it.get("tool") if isinstance(it, dict) else None
        if not isinstance(tool, str) or not tool.startswith(prefix):
            continue   # another tool's
        at, s = it.get("at"), span(it.get("at"))
        why = next((r for bad, r in (
            (tool in NOT, NOT.get(tool, "")),
            (tool not in KINDS, f"no such kind {tool!r} (confirmable here: {', '.join(k for k in KINDS if k.startswith(prefix))})"),
            (s is None, f"at {at!r} is not seconds or a span a-b"),
            (not isinstance(it.get("key"), str) or ":" not in it.get("key", ""), "no key: copy the confirm? line the tool printed"),
            (tool == "qa.click" and not (isinstance(it.get("n"), int) and it["n"] >= 1), 'a click span needs "n", the clicks in it'),
            (not str(it.get("why") or "").strip(), "no why: say what was intended"),
            (not str(it.get("evidence") or "").strip(), "no evidence: name the file that shows it")) if bad), None)
        why = why or evidence_problem(str(it["evidence"]), p.parent)
        if why:
            refused.append((n, at, why))
        else:
            taken.append({**it, "_a": s[0], "_b": s[1], "_n": n})
    return taken, refused


def judge(entries, kind, findings, tol, same, keyfn=None, cover=False, what="the picture"):
    """Match the entries of `kind` with the findings ([{"a", "b", "key"}], seconds). An entry is at a finding when its
    start and end are within `tol` of the finding's; with cover (qa.click) it holds every finding inside its span, and
    there must be no more of them than its "n". The key to compare is keyfn(entry start, end) when given (a sound's key
    is taken over the entry's own span), else the finding's. Confirmed when same(entry key, that key), else lapsed.
    → (state per finding: ("confirmed" | "lapsed" | "open", entry or None), [(entry, "confirmed" | "lapsed" | "unused", why)])."""
    state, notes = [("open", None)] * len(findings), []
    for e in (x for x in entries if x["tool"] == kind):
        if cover:
            at = [k for k, f in enumerate(findings) if e["_a"] - tol <= f["a"] and f["b"] <= e["_b"] + tol]
        else:
            at = [k for k, f in enumerate(findings) if abs(f["a"] - e["_a"]) <= tol and abs(f["b"] - e["_b"]) <= tol]
        if not at:
            notes.append((e, "unused", "nothing flagged there now"))
            continue
        many = cover and len(at) > e["n"]
        ok = [] if many else [k for k in at if same(e["key"], keyfn(e["_a"], e["_b"]) if keyfn else findings[k]["key"])]
        notes.append((e, "confirmed" if ok else "lapsed",
                      "" if ok else f"{len(at)} there now, {e['n']} when confirmed" if many else f"{what} there changed since it was confirmed"))
        for k in at:
            if k in ok:
                state[k] = ("confirmed", e)
            elif state[k][0] == "open":
                state[k] = ("lapsed", e)
    return state, notes


def lines(notes, refused):
    """The report lines for the entries: confirmed, lapsed (it counts again), unused, refused; plus a note when one
    kind is confirmed MANY times or more."""
    out, say = [], lambda e: f"{e['_a']:g}" + (f"-{e['_b']:g}" if e["_b"] > e["_a"] else "") + " s"
    for e, st, why in notes:
        if st == "confirmed":
            out.append(f"  confirmed (已确认, {NAME}): {KINDS[e['tool']]} at {say(e)} · {str(e['why']).strip()} · {str(e['evidence']).strip()}")
        elif st == "lapsed":
            out.append(f"  LAPSED (已失效, {NAME}, {e.get('date') or 'undated'}): {KINDS[e['tool']]} at {say(e)}: {why}; it counts again. "
                       "Look again, then fix it or confirm it again")
        else:
            out.append(f"  unused ({NAME}): {KINDS[e['tool']]} at {say(e)}: {why}; remove the entry")
    for n, at, why in refused:
        out.append(f"  not taken ({NAME}, item {n}, at {at!r}): {why}")
    count = {}
    for e, st, _ in notes:
        if st == "confirmed":
            count[e["tool"]] = count.get(e["tool"], 0) + 1
    for k, c in count.items():
        if c >= MANY:
            out.append(f"  note: {c} {KINDS[k]}s confirmed in one film: the detector may be what is wrong here; say so in NOTES "
                       "(已知局限) and report it rather than confirming more")
    return out


def offer(kind, a, b, key, n=None):
    """A `confirm?` line for an open finding: the entry to paste into confirmed.json once why and evidence are filled."""
    at = f"{a:.3f}" if b <= a else f"{a:.3f}-{b:.3f}"
    it = {"tool": kind, "at": at, **({"n": n} if n is not None else {}), "key": key, "why": "", "evidence": "",
          "date": datetime.date.today().isoformat()}
    return "  confirm? " + json.dumps(it, ensure_ascii=False)
