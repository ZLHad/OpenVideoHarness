"""Publish a pair of cuts for a saved comment, and read the reviewer’s reply."""
import hashlib
import json
import math
import os
import re
import tempfile
from pathlib import Path

import checkrec
import feedback


DIRECTORY = Path("out/review/revisions")
FEEDBACK = Path("out/review/feedback")
VIDEO = {".mp4", ".m4v", ".mov", ".webm"}
ID = re.compile(r"[0-9a-f]{24}")
SHA = re.compile(r"[0-9a-f]{64}")
SUBMISSION = re.compile(r"[A-Za-z0-9_-]{1,64}(?:\.json)?")


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


def video_path(project, value):
    # The CLI lives next to desk feedback; a relative input is from the project.
    path = project_path(project, value)
    if not path.is_file() or path.suffix.lower() not in VIDEO:
        raise ValueError(f"{value}: expected a video file inside the project")
    return path


def clip_span(start, end):
    if not all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in (start, end)):
        return None
    return [start, end] if 0 <= start < end else None


def interval(project, item, before, explicit):
    kind, _, name = item["target"].partition(":")
    if explicit or kind == "range":
        m = feedback.RANGE.fullmatch("range:" + (explicit or name))
        if m:
            span = clip_span(*map(float, m.groups()))
            if span:
                return span
        raise ValueError("--span needs START-END in seconds, with START < END")
    if kind == "shot":
        # The earlier render's own shot table is valid even if the current board has moved.
        for suffix, muxed in ((".mux.json", True), (".render.json", False)):
            try:
                side = read(project_path(project, str(before) + suffix))
            except FileNotFoundError:
                continue
            if muxed:
                film = side.get("film")
                if not isinstance(film, dict) or film.get("size") != before.stat().st_size:
                    continue
            side = side.get("render") if muxed else side
            if isinstance(side, dict):
                for shot in side.get("shots") or []:
                    if isinstance(shot, dict) and shot.get("id") == name:
                        span = clip_span(shot.get("start"), shot.get("end"))
                        if span:
                            return span
    if kind == "revision" and ID.fullmatch(name):
        try:
            prior = read(project_path(project, DIRECTORY / (name + ".json")))
            if isinstance(prior.get("span"), list) and len(prior["span"]) == 2:
                span = clip_span(*prior["span"])
                if span:
                    return span
        except FileNotFoundError:
            pass
    raise ValueError("give --span START-END for this comment (the same seconds in both cuts)")


def fingerprint(st):
    return st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns


def copy_cut(project, source, staging, name):
    """Hash the bytes copied, then probe that copy. The source may be re-rendered later."""
    copy = staging / (name + source.suffix.lower())
    digest = hashlib.sha256()
    with source.open("rb") as src, copy.open("xb") as dst:
        original = fingerprint(os.fstat(src.fileno()))
        for block in iter(lambda: src.read(4 << 20), b""):
            dst.write(block)
            digest.update(block)
        if original != fingerprint(os.fstat(src.fileno())) or original != fingerprint(source.stat()):
            raise ValueError(f"{source.name} changed while it was being copied; retry with the cut you want to review")
    data = checkrec.probe(copy)
    duration = data.get("duration")
    if not clip_span(0, duration) or not any(s["type"] == "video" for s in data.get("streams", [])):
        raise ValueError(f"{source.name}: ffprobe could not find a video with a duration")
    return copy, {"source": source.relative_to(project).as_posix(), "sha256": digest.hexdigest(),
                  "duration": duration, "audio": any(s["type"] == "audio" for s in data["streams"])}


def publish(project, submission, item_number, before_name, after_name, explicit=None):
    project = Path(project).resolve()
    if not SUBMISSION.fullmatch(submission):
        raise ValueError("give the feedback filename shown by bin/vh desk feedback, without a directory")
    filename = submission if submission.endswith(".json") else submission + ".json"
    feedback_rel = FEEDBACK / filename
    original = read(project_path(project, feedback_rel))
    items = original.get("items")
    if not isinstance(items, list) or not 1 <= item_number <= len(items):
        raise ValueError(f"{filename}: --item must name one of its items (numbering starts at 1)")
    item = items[item_number - 1]
    if not isinstance(item, dict) or item.get("status") not in ("change", "ask") or not isinstance(item.get("target"), str):
        raise ValueError(f"{filename}: item {item_number} does not request a change or answer")
    before = video_path(project, before_name)
    after = video_path(project, after_name)
    span = interval(project, item, before, explicit)
    directory = project_path(project, DIRECTORY)
    media = project_path(project, DIRECTORY / "media")
    media.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".publish-", dir=directory) as temp:
        staging = Path(temp)
        a, base = copy_cut(project, before, staging, "before")
        b, candidate = copy_cut(project, after, staging, "after")
        if base["sha256"] == candidate["sha256"]:
            raise ValueError("the two cuts have identical bytes")
        if span[1] > min(base["duration"], candidate["duration"]) + 0.001:
            raise ValueError("the review span must fit inside both cuts")
        identity = [filename, item_number, span, base["sha256"], candidate["sha256"]]
        key = hashlib.sha256(json.dumps(identity).encode()).hexdigest()[:24]
        record_path = project_path(project, DIRECTORY / (key + ".json"))
        # Link an independent copy into place. Two publishers of the same bytes keep the same file and stat.
        for copy, info in ((a, base), (b, candidate)):
            filename = info["sha256"] + copy.suffix
            blob = media / filename
            if blob.is_symlink():
                raise ValueError(f"{blob.name}: the review copy must be a regular file")
            try:
                os.link(copy, blob)
            except FileExistsError:
                from assets.ledger import sha256_file
                if not blob.is_file() or sha256_file(blob) != info["sha256"]:
                    raise ValueError(f"{blob.name}: review copy differs; restore the stored copy and retry")
            stat = blob.stat()
            info.update(file=(DIRECTORY / "media" / filename).as_posix(), size=stat.st_size, mtime_ns=str(stat.st_mtime_ns))
        record = {"version": 1, "id": key, "span": span, "feedback": feedback_rel.as_posix(),
                  "item": item_number, "round": original.get("round", ""),
                  "target": item["target"], "label": item.get("label", item["target"]),
                  "text": item.get("text", ""), "suggest": item.get("suggest", ""),
                  "before": base, "after": candidate}
        temp_record = staging / "record.json"
        temp_record.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            os.link(temp_record, record_path)
        except FileExistsError:
            return read(record_path)
        return record


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


def can_review(project, key):
    if not ID.fullmatch(key):
        return False
    project = Path(project).resolve()
    try:
        record = read(project_path(project, DIRECTORY / (key + ".json")))
        return record.get("id") == key and all(available(project, record.get(k)) for k in ("before", "after"))
    except (OSError, ValueError):
        return False


def stamp(project):
    """Only stat directories in the desk's live poll. Media stays off that path."""
    project = Path(project).resolve()
    try:
        made = project_path(project, DIRECTORY).stat().st_mtime_ns
    except (OSError, ValueError):
        return ""
    try:
        said = project_path(project, FEEDBACK).stat().st_mtime_ns
    except (OSError, ValueError):
        said = 0
    return f"{made}:{said}"


def listing(project):
    project = Path(project).resolve()
    try:
        files = sorted(project_path(project, DIRECTORY).glob("*.json"), key=lambda p: p.stat().st_mtime_ns, reverse=True)
    except (OSError, ValueError):
        return []
    if not files:
        return []
    replies = {}
    for _, data in sorted(feedback._records(project), key=lambda entry: feedback._order(*entry)):
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
