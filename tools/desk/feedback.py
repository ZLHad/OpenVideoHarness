"""Review desk, feedback: check a submission, save it, copy the reviewer's words into REVIEW.md, and wait for one.

A submission is saved as out/review/feedback/<round>-<YYYYMMDD-HHMMSS>.json plus a .md copy an agent or a human
reads; the same .md text goes into REVIEW.md verbatim, as a dated section (CLAUDE.md: the human's words are recorded
word for word). The .json is written last, atomically: it is what the watcher (wait) waits for.
"""
import datetime, json, os, re, signal, sys, threading, time
from pathlib import Path

MAX_BODY = 256 * 1024
MAX_ITEMS, MAX_DECISIONS = 400, 20
LIMIT = {"text": 4000, "suggest": 2000, "orig": 2000, "label": 300, "general": 8000}
STATUS = ("ok", "change", "ask")
TARGET = re.compile(r"^(dec|least|deleg|concept|seg|cap|shot|fact|time|atime|led|doc|asset):[^\x00-\x1f]{1,180}$")
ROUND = re.compile(r"^[A-Za-z0-9_-]{1,24}$")
NO_ROUND = "notes"           # comments sent while no gate page is out
REFERENCE = re.compile(r"^## (授权跳过怎么记|给人看的提示|How to record a waived gate|Notes for the reviewer)", re.M)
WORDS = {
    "zh": dict(title="# 审阅反馈 · {round} · {at}", decision="决定 {id}：{v}", default="（按推荐，没改）",
               st={"ok": "可以", "change": "要改", "ask": "疑问"}, orig="（原句：{x}）", suggest="改成「{x}」",
               general="整体意见：{x}", rest="其余未标注的条目默认通过。", colon="：",
               head="## 审阅台反馈 · {round} · {at}", round_name="关卡 {r}", no_round="随手点评",
               page="- 页面：审阅台（`bin/vh desk`）；反馈原件 `{json}`",
               said="- 原话（审阅台里逐条写的，照抄）：", after="- 定了：　改了："),
    "en": dict(title="# Review feedback · {round} · {at}", decision="Decision {id}: {v}", default=" (the recommendation, untouched)",
               st={"ok": "ok", "change": "change", "ask": "question"}, orig=" (was: {x})", suggest="change to “{x}”",
               general="Overall: {x}", rest="Everything not marked passes by default.", colon=": ",
               head="## Review desk feedback · {round} · {at}", round_name="gate {r}", no_round="notes",
               page="- Page: the review desk (`bin/vh desk`); the original `{json}`",
               said="- Verbatim (written item by item in the desk):", after="- Decided:　Changed:"),
}
_lock = threading.Lock()


def _text(x, key, where):
    if x is None:
        return ""
    if not isinstance(x, str):
        raise ValueError(f"{where}: expected text")
    x = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", x.replace("\r\n", "\n").replace("\r", "\n"))
    if len(x) > LIMIT[key]:
        raise ValueError(f"{where}: longer than {LIMIT[key]} characters")
    return x


def gate_options(project, rid):
    """{decision id: [option ids]} of out/review/gate-<rid>.json; None when there is no such page."""
    p = Path(project) / "out" / "review" / f"gate-{rid}.json"
    try:
        d = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None
    out = {}
    for x in (d.get("decisions") or []) if isinstance(d, dict) else []:
        if isinstance(x, dict) and isinstance(x.get("id"), str):
            out[x["id"]] = [o.get("id") if isinstance(o, dict) else str(o) for o in x.get("options") or []]
    return out


def validate(project, fb):
    """A submission from the desk → the clean record to save. Raises ValueError with what is wrong."""
    if not isinstance(fb, dict):
        raise ValueError("expected a JSON object")
    rid = fb.get("round")
    if not isinstance(rid, str) or not ROUND.match(rid):
        raise ValueError("round: a gate page id like 1, 2b or E3")
    opts = gate_options(project, rid)
    if opts is None and rid != NO_ROUND:
        raise ValueError(f"round {rid}: there is no out/review/gate-{rid}.json")
    decisions, defaulted = {}, []
    dec = fb.get("decisions") or {}
    if not isinstance(dec, dict) or len(dec) > MAX_DECISIONS:
        raise ValueError("decisions: an object of at most 20 {id: option}")
    for k, v in dec.items():
        if not isinstance(v, str) or k not in (opts or {}) or (opts[k] and v not in opts[k]):
            raise ValueError(f"decisions: {k!r} → {v!r} is not a decision and option of gate-{rid}.json")
        decisions[k] = v
    for k in fb.get("defaulted") or []:
        if isinstance(k, str) and k in decisions:
            defaulted.append(k)
    items = fb.get("items") or []
    if not isinstance(items, list) or len(items) > MAX_ITEMS:
        raise ValueError(f"items: a list of at most {MAX_ITEMS}")
    clean = []
    for i, it in enumerate(items):
        w = f"items[{i}]"
        if not isinstance(it, dict):
            raise ValueError(f"{w}: expected an object")
        tgt, st = it.get("target"), it.get("status")
        if not isinstance(tgt, str) or not TARGET.match(tgt):
            raise ValueError(f"{w}.target: like cap:c04, shot:S03, time:12.4, doc:BRIEF.md#Spec")
        if st not in STATUS:
            raise ValueError(f"{w}.status: ok, change or ask")
        c = {"target": tgt, "status": st, "label": _text(it.get("label"), "label", w + ".label") or tgt,
             "text": _text(it.get("text"), "text", w + ".text")}
        for k in ("suggest", "orig"):
            if it.get(k):
                c[k] = _text(it[k], k, f"{w}.{k}")
        t = it.get("t")
        if t is not None:
            if not isinstance(t, (int, float)) or isinstance(t, bool) or not 0 <= t < 1e6:
                raise ValueError(f"{w}.t: seconds")
            c["t"] = round(float(t), 2)
        clean.append(c)
    lang = fb.get("lang") if fb.get("lang") in WORDS else "zh"
    return {"round": rid, "lang": lang, "decisions": decisions, "defaulted": defaulted, "items": clean,
            "general": _text(fb.get("general"), "general", "general").strip()}


def to_markdown(fb):
    """The .md copy: what the reviewer marked and wrote, one line each, their words untouched."""
    w = WORDS[fb.get("lang") if fb.get("lang") in WORDS else "zh"]
    lines = [w["title"].format(round=fb["round"], at=fb.get("submitted_at", "")), ""]
    for k, v in fb["decisions"].items():
        lines.append("- " + w["decision"].format(id=k, v=v) + (w["default"] if k in fb.get("defaulted", []) else ""))
    for it in fb["items"]:
        line = f"- {it['label']} [{it['target']}] · {w['st'][it['status']]}"
        if it.get("orig") and it["target"].startswith("cap:"):
            line += w["orig"].format(x=it["orig"])
        if it.get("text"):
            line += w["colon"] + it["text"].strip()
        if it.get("suggest") and it.get("suggest") != it.get("orig"):
            line += (" → " if it.get("text") else w["colon"]) + w["suggest"].format(x=it["suggest"])
        lines.append(line.replace("\n", "\n  "))
    if fb.get("general"):
        lines += ["", w["general"].format(x=fb["general"])]
    lines += ["", w["rest"]]
    return "\n".join(lines) + "\n"


def _write(p, text):
    tmp = p.with_name(p.name + ".part")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, p)


def append_review(project, fb, md, json_rel):
    """Copy the submission into REVIEW.md as a dated section, before the template's reference sections
    (授权跳过怎么记 / 给人看的提示) when they are there, else at the end. The agent adds 定了 / 改了 under it."""
    w = WORDS[fb.get("lang") if fb.get("lang") in WORDS else "zh"]
    p = Path(project) / "REVIEW.md"
    old = p.read_text(encoding="utf-8") if p.exists() else ("# REVIEW：人的原话\n" if fb.get("lang") != "en" else "# REVIEW: the human's words\n")
    run = max([len(x) for x in re.findall(r"`+", md)] + [2])
    fence = "`" * (run + 1)
    rname = w["no_round"] if fb["round"] == NO_ROUND else w["round_name"].format(r=fb["round"])
    at = fb.get("submitted_at", "").replace("T", " ")[:16]
    block = "\n".join([w["head"].format(round=rname, at=at), "", w["page"].format(json=json_rel), w["said"], "",
                       fence + "text", md.rstrip("\n"), fence, "", w["after"], "", ""])
    m = REFERENCE.search(old)
    new = old[:m.start()] + block + old[m.start():] if m else old.rstrip("\n") + "\n\n" + block
    _write(p, new)


def save(project, fb, now=None):
    """Save a validated submission: the .md, then REVIEW.md, then the .json (the watcher's trigger). → the .json path."""
    project = Path(project)
    now = now or datetime.datetime.now()
    fb = dict(fb, project=project.name, submitted_at=now.isoformat(timespec="seconds"))
    out = project / "out" / "review" / "feedback"
    with _lock:
        out.mkdir(parents=True, exist_ok=True)
        stem, n = f"{fb['round']}-{now:%Y%m%d-%H%M%S}", 1
        while (out / f"{stem}.json").exists() or (out / f"{stem}.md").exists():
            n += 1
            stem = f"{fb['round']}-{now:%Y%m%d-%H%M%S}-{n}"
        md = to_markdown(fb)
        _write(out / f"{stem}.md", md)
        rel = f"out/review/feedback/{stem}.json"
        append_review(project, fb, md, rel)
        _write(out / f"{stem}.json", json.dumps(fb, ensure_ascii=False, indent=1) + "\n")
    return out / f"{stem}.json"


def listening(project):
    """Is an agent waiting for this project's feedback (bin/vh desk wait running)? {listening, since, until}."""
    flag = Path(project) / "out" / "review" / "feedback" / ".listening"
    try:
        info = json.loads(flag.read_text())
        os.kill(int(info["pid"]), 0)
    except PermissionError:   # alive, someone else's process
        pass
    except (OSError, ValueError, KeyError, TypeError):
        return {"listening": False}
    if float(info.get("until") or 0) < time.time():
        return {"listening": False}
    return {"listening": True, "since": info.get("since"), "until": info.get("until")}


def latest(project, rid=None):
    """The newest submission (for one round when rid is given): (json path, record) or (None, None)."""
    fdir = Path(project) / "out" / "review" / "feedback"
    best = (None, None, "")
    for f in fdir.glob("*.json") if fdir.is_dir() else []:
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(j, dict) or (rid and j.get("round") != rid):
            continue
        key = f"{j.get('submitted_at', '')}|{f.name}"
        if key > best[2]:
            best = (f, j, key)
    return best[0], best[1]


def show(path, record, out=sys.stdout):
    md = path.with_suffix(".md")
    try:
        text = md.read_text(encoding="utf-8")
    except OSError:
        text = to_markdown(record)
    out.write(text if text.endswith("\n") else text + "\n")
    out.write(f"json: {path}\n")
    out.flush()


def wait(project, timeout, poll=1.0, out=sys.stdout):
    """Block until a new feedback file appears, print it, return 0; 3 on timeout. Keeps feedback/.listening
    ({pid, since, until}) while waiting, so the desk can say an agent is waiting; files already there are ignored."""
    fdir = Path(project) / "out" / "review" / "feedback"
    fdir.mkdir(parents=True, exist_ok=True)
    flag, start = fdir / ".listening", time.time()
    seen = {p.name for p in fdir.glob("*.json")}
    _write(flag, json.dumps({"pid": os.getpid(), "since": start, "until": start + timeout}))

    def done(code):
        try:
            if json.loads(flag.read_text()).get("pid") == os.getpid():
                flag.unlink()
        except (OSError, ValueError):
            pass
        return code

    def stop(signum, _frame):
        raise SystemExit(done(128 + signum))
    for s in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(s, stop)
    while time.time() - start < timeout:
        new = sorted(p for p in fdir.glob("*.json") if p.name not in seen)
        if new:
            for p in new:
                try:
                    show(p, json.loads(p.read_text(encoding="utf-8")), out)
                except (OSError, ValueError):
                    continue
            out.write("The reviewer's words are also in REVIEW.md (a dated section): add what you decided and changed "
                      "under it. Items not marked pass by default.\n")
            out.flush()
            return done(0)
        time.sleep(poll)
    out.write(f"no feedback within {timeout:.0f} s; arm it again: bin/vh desk wait {project}\n")
    out.flush()
    return done(3)
