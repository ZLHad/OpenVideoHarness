"""Read feedback and revision records saved by earlier releases."""
import json
import math
import re
from pathlib import Path


ROUND = re.compile(r"^[A-Za-z0-9_-]{1,24}$")
DIRECTORY = Path("out/review/revisions")
VIDEO = {".mp4", ".m4v", ".mov", ".webm"}
ID = re.compile(r"[0-9a-f]{24}")
SHA = re.compile(r"[0-9a-f]{64}")


def clock(x):
    """12.4 → 0:12.4, 75 → 1:15.0 (as the desk shows times; 59.96 → 1:00.0, not 0:60.0)"""
    x = round(x, 1)
    m = int(x // 60)
    return f"{m}:{x - 60 * m:04.1f}"


NAMES = {"zh": {"range": "片段 {x}", "chapter": "章节 {x}", "asset": "素材 {x}", "card": "立意卡 {x}", "time": "小样 {x}", "atime": "声音 {x}"},
         "en": {"range": "Span {x}", "chapter": "Chapter {x}", "asset": "Asset {x}", "card": "Concept card {x}", "time": "Film {x}", "atime": "Sound {x}"}}


def readable(it, lang):
    """An item's label as REVIEW.md shows it: the one the page sent, else one made from the target; a span always says
    its times (片段 0:12.4–0:15.0)."""
    kind, _, rest = it["target"].partition(":")
    span = f"{clock(it['t'])}–{clock(it['t1'])}" if kind == "range" and "t1" in it else None
    names = NAMES.get(lang, NAMES["zh"])
    if it["label"] == it["target"] and kind in names:
        x = span or (clock(it["t"]) if kind in ("time", "atime") and "t" in it else rest)
        return names[kind].format(x=x)
    return it["label"] + (f"（{span}）" if lang == "zh" else f" ({span})") if span and span not in it["label"] else it["label"]


def _order(f, j):
    """Sort key of a submission: its time, then the -2, -10 … suffix added within one second, numerically."""
    m = re.search(r"-(\d+)\.json$", f.name) if re.search(r"-\d{8}-\d{6}-\d+\.json$", f.name) else None
    return (str(j.get("submitted_at", "")), int(m.group(1)) if m else 1, f.name)


def _records(project):
    fdir = Path(project) / "out" / "review" / "feedback"
    for f in fdir.glob("*.json") if fdir.is_dir() else []:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(j, dict):
            yield f, j


def _consumed_record(project):
    try:
        d = json.loads((Path(project) / "out" / "review" / "feedback" / ".consumed").read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def consumed(project):
    """Names of the submissions an agent has already been handed (feedback/.consumed)."""
    names = _consumed_record(project).get("files", [])
    return {n for n in names if isinstance(n, str)} if isinstance(names, list) else set()


def taken(project):
    """{name: {t, run, program, by}}: when each handed-over submission was taken, by which bin/vh run (its activity run id,
    when it ran under bin/vh), the agent program it ran under (claude, codex …, when one was found) and how (wait |
    feedback). Older .consumed files have the names only: those are taken with nothing more known."""
    d = _consumed_record(project)
    info = d.get("taken") if isinstance(d.get("taken"), dict) else {}
    return {n: (info.get(n) if isinstance(info.get(n), dict) else {}) for n in consumed(project)}


def answered(project):
    """Names of the submissions whose REVIEW.md section (the one naming the .json) has a 定了: an agent read it
    and wrote what was decided, however it read it."""
    try:
        import gatecheck as G
        text = G.read(Path(project) / "REVIEW.md")
    except (OSError, ImportError):
        return set()
    out = set()
    for _title, lines in G.sections(text)[1:]:
        names = re.findall(r"out/review/feedback/([^`\s)]+\.json)", "\n".join(x for x, c in lines if not c))
        if names and G.record(lines)[0]:
            out.update(names)
    return out


def unread(project):
    """Every submission no agent has been handed and no agent has answered, of any round, oldest first: [(path, record,
    late)]. late: a submission of the same round was handed over before it (the person wrote more after the round was
    taken). These are listed by bin/vh status."""
    done, ans, took = consumed(project), answered(project), taken(project)
    recs = sorted(((f, j) for f, j in _records(project) if isinstance(j.get("round"), str) and ROUND.match(j["round"]) and isinstance(j.get("submitted_at"), str)),
                  key=lambda x: _order(*x))   # (submissions as save() writes them: a stray or broken file is no note of the person's)
    out = []
    for i, (f, j) in enumerate(recs):
        if f.name in done or f.name in ans:
            continue
        late = any(g.name in done and (took.get(g.name) or {}).get("t") and k.get("round") == j.get("round") for g, k in recs[:i])   # (a hand-over recorded with its time: an older record's names say nothing of when)
        out.append((f, j, late))
    return out


def project_path(project, path):
    p = (project / path).resolve()
    if not p.is_relative_to(project):
        raise ValueError(f"{path}: needs to be inside the project")
    return p


def read(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: expected a JSON object")
    return data


def clip_span(start, end):
    if not all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in (start, end)):
        return None
    return [start, end] if 0 <= start < end else None


def available(project, info):
    if not isinstance(info, dict) or not isinstance(info.get("file"), str):
        return False
    path = Path(info["file"])
    if path.parent != DIRECTORY / "media" or path.suffix not in VIDEO or not SHA.fullmatch(path.stem) or path.stem != info.get("sha256"):
        return False
    try:
        stat = project_path(project, path).stat()
        return stat.st_size == info.get("size") and str(stat.st_mtime_ns) == info.get("mtime_ns")
    except (OSError, ValueError):
        return False


def listing(project):
    project = Path(project).resolve()
    try:
        files = sorted(project_path(project, DIRECTORY).glob("*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    except (OSError, ValueError):
        return []
    if not files:
        return []
    replies = {}
    for _, data in sorted(_records(project), key=lambda entry: _order(*entry)):
        items = data.get("items")
        for it in items if isinstance(items, list) else []:
            if not isinstance(it, dict) or not isinstance(it.get("target"), str):
                continue
            if it["target"].startswith("revision:") and it.get("status") in ("ok", "change"):
                replies[it["target"].split(":", 1)[1]] = it
    out = []
    for file in files:
        if not ID.fullmatch(file.stem):
            continue
        try:
            row = read(project_path(project, file))
        except (OSError, ValueError):
            continue
        span = row.get("span")
        if row.get("version") != 1 or row.get("id") != file.stem or not isinstance(span, list) or len(span) != 2 or not clip_span(*span):
            continue
        reply = replies.get(file.stem)
        state = {"ok": "approved", "change": "changes_requested"}[reply["status"]] if reply else "pending"
        out.append(dict(row, state=state, reply=reply,
                        available=all(available(project, row.get(k)) for k in ("before", "after"))))
    return out
