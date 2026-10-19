"""bin/vh status: where a project stands, from the files it already has. Read-only; no browser, no ffprobe.

usage: bin/vh status <project> [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

The stops, in the pipeline's order: gate ① ② ③ always; a checkpoint E0–E5 when it has a page, a REVIEW.md section or the
BRIEF's Director line asks for it (stop=E3); a review page with another name ("final") as a stop of its own; then delivery.
Each has a state:
  done            a decision for it is on record in REVIEW.md: "定了：…" (the template's {…} does not count), in the last
                  section about its latest page (the desk's section for a submission, or one that names
                  out/review/gate-<n>.html: REVIEW.md grows downwards, so a second review of the page comes after the
                  first); with no such section, in the stop's section when REVIEW.md was written after that page. Gate ①
                  also says whether DECISIONS.md has the concept, which bin/vh render and check wait for (gatecheck.py)
  skipped         Effort quick (and no page of its own), or waived in the user's own words in REVIEW.md
  waiting_person  its page is this round (out/review/.current) and nothing has come back for it yet
  waiting_agent   the person submitted on the desk and no agent has it yet, or an agent has it and REVIEW.md has no
                  decision for it yet; or the project moved on past its page with no decision on record
  in_progress     the first stop with nothing yet after the last one that has something, when all before it are done or
                  skipped: what the agent works towards
  not_started     later stops; a stop passed over without a record stays not_started
Delivery is done once bin/vh deliver has written a record, or the final film (out/final*, out/final/, media/) has a passing
bin/vh check record newer than it; in progress once every stop is done or skipped.
waiting_on: person (a stop waits for them, or REVIEW.md says the project is paused), agent (one waits for the agent,
the agent works towards one, or a command is running), or nobody (delivered).
Also: the latest renders with what their sidecars say (.render.json, .deliver.json, the check record), the review items
still open (a desk submission's change and ask items whose REVIEW.md section has no 定了 / 改了 yet), the facts NOTES.md
still lists to verify, the last check, and the commands running now and the last ones (the activity log).
--json: every field (tools/desk/README.md, 给客户端的数据, has the schema; "version": 1). Exit 0, 2 when there is no project.
"""
import json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "desk"))
import activity, gatecheck as G, review as R   # noqa: E402,E401
import feedback as F, reader   # noqa: E402,E401

ORDER = ["1", "E0", "E1", "2", "E2", "E3", "E4", "3", "E5"]
VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
SKIP_DIRS = {"frames", "node_modules", "__pycache__", ".venv", "venv"}
STATE_MARK = {"done": "✓", "skipped": "–", "waiting_person": "●", "waiting_agent": "◆", "in_progress": "…", "not_started": "·"}
STATE_WORDS = {"done": "done", "skipped": "skipped", "waiting_person": "waiting for you", "waiting_agent": "waiting for the agent",
               "in_progress": "in progress", "not_started": "not started"}
LISTENING = ("desk", "gate")   # a running desk or gate --wait is someone waiting, not work being done


def rel(project, p):
    try:
        return Path(os.path.relpath(p, project)).as_posix()
    except ValueError:
        return str(p)


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t)) if t else None


def basics(project):
    """The project as its BRIEF says: title, type, effort (and where it comes from), Director line, review language, Spec."""
    raw = reader._read(project / "BRIEF.md", [])
    brief = reader.strip_comments(raw)
    spec = {k: reader.plain(v) for k, v, _ in reader.bullets(reader.section(brief, r"^Spec", r"^规格"))}
    title = (re.search(r"^#\s+BRIEF\s*[：:]\s*(.+)$", brief, re.M) or [None, ""])[1].strip() or project.name
    m = re.search(r"video-types/(\d\d-[\w-]+)\.md", brief) or re.search(r"<!-- from (\d\d-[\w-]+)\.md -->", raw)
    effort, src = G.effort_of(project)
    return {"path": str(project), "slug": project.name, "title": title, "type": m.group(1) if m else None, "effort": effort,
            "effort_from": src, "director": spec.get("Director") or "default", "lang": R.review_lang(project) or "zh", "spec": spec}


def director_stops(director_line):
    """The checkpoints a Director line asks for: stop=E3, stop=E1,E3 (also stop=E1 stop=E3)."""
    return {s.upper() for grp in re.findall(r"stop\s*=\s*([A-Za-z0-9, ]+)", director_line or "", re.I)
            for s in re.split(r"[,\s]+", grp) if re.fullmatch(r"E\d", s, re.I)}


def feedback_records(project):
    """[(path, record)] of the desk's submissions, oldest first."""
    return sorted(F._records(project), key=lambda x: F._order(*x))


def review_section_for(review, fb_path):
    """The REVIEW.md section the desk wrote for one submission (it names the submission's JSON), as (title, lines)."""
    name = f"out/review/feedback/{fb_path.name}"
    return next(((t, ls) for t, ls in G.sections(review)[1:] if any(name in x for x, c in ls if not c)), None)


def stops(project, review_text, review_mtime, effort, asked, lang):
    """The stops and their states (but in_progress / not_started, which need the order): ([dict], this round)."""
    pages = R.gate_pages(project)                       # in review order, this round last
    cur = R.current_page(project) or (pages[-1].stem[5:] if pages else None)
    by_stop, extra = {}, []
    for p in pages:
        pid = p.stem[5:]
        s = G.stop_of(pid)
        (by_stop.setdefault(s, []) if s else extra).append(p)
    present = [s for s in ORDER if s in ("1", "2", "3") or s in by_stop or s in asked or G.stop_sections(review_text, s)]
    consumed = F.consumed(project)
    subs = feedback_records(project)
    out = []
    for key in present + [p.stem[5:] for p in extra]:
        is_stop = key in ORDER
        plist = by_stop.get(key, []) if is_stop else [p for p in extra if p.stem[5:] == key]
        latest = next((p for p in plist if p.stem[5:] == cur), plist[-1] if plist else None)
        pid = latest.stem[5:] if latest else None
        st = {"id": key, "name": R.gate_title(key, lang), "kind": "gate" if key.isdigit() else "checkpoint" if is_stop else "page",
              "state": None, "pages": [p.stem[5:] for p in plist], "page": None, "current": pid is not None and pid == cur,
              "record": None, "feedback": None, "note": None}
        if latest is not None:
            html = latest.with_suffix(".html")
            st["page"] = rel(project, html if html.exists() else latest)
        # the record: the latest section about the latest page itself (REVIEW.md grows downwards: a second review of the
        # same page, the desk's section, comes after the first); with none, the stop's own section written after the page
        page_secs = G.page_sections(review_text, pid) if pid else []
        stop_secs = G.stop_sections(review_text, key) if is_stop else []
        decided = said = False
        if page_secs:
            decided = G.record(page_secs[-1][1])[0]
            said = any(G.record(ls)[1] for _, ls in page_secs)
        elif stop_secs and (latest is None or review_mtime >= latest.stat().st_mtime):
            for _, ls in stop_secs:
                d, s = G.record(ls)
                decided, said = decided or d, said or s
        waived = G.waived_stop(review_text, key) if is_stop else None
        st["record"] = {"decided": decided, "said": said, "waived": waived}
        if key == "1":
            dec = project / "DECISIONS.md"
            st["record"]["concept_on_record"] = dec.is_file() and G.concept_decided(G.read(dec))
        # the desk's submissions for this stop's latest page, after it was written
        mine = [(f, j) for f, j in subs if pid and j.get("round") == pid and f.stat().st_mtime >= latest.stat().st_mtime]
        pend = [f for f, _ in mine if f.name not in consumed]
        handed = [f for f, _ in mine if f.name in consumed]
        if mine:
            st["feedback"] = {"submitted": len(mine), "handed": len(handed), "pending": len(pend),
                              "last": rel(project, mine[-1][0])}
        if waived or (effort == "quick" and not plist):
            st["state"] = "skipped"
            st["note"] = f"waived in the user's words ({waived})" if waived else "Effort quick: no gates"
        elif decided:
            st["state"] = "done"
            if not said:
                st["note"] = "decided, but the person's words are not in REVIEW.md"
            if key == "1" and not st["record"]["concept_on_record"] and effort != "quick":
                st["note"] = "DECISIONS.md has no concept row on record: bin/vh render and check will refuse the whole film"
        elif latest is not None and pid == cur:
            if pend:
                st["state"], st["note"] = "waiting_agent", f"{len(pend)} submission(s) not handed to the agent yet (bin/vh desk feedback)"
            elif handed:
                st["state"], st["note"] = "waiting_agent", "the submission was handed over; REVIEW.md has no decision for it yet"
            else:
                st["state"] = "waiting_person"
        elif latest is not None:
            st["state"], st["note"] = "waiting_agent", f"this round moved on to {cur}; REVIEW.md has no decision for {pid}"
        out.append(st)
    return out, cur


def renders(project):
    """Video files under out/ (three levels down), renders/ and media/, newest first, with what lies beside them."""
    found = []
    for top in ("out", "renders", "media"):
        base = project / top
        if not base.is_dir():
            continue
        for d, dirs, files in os.walk(base):
            depth = Path(d).relative_to(base).parts
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".") and len(depth) < 3]
            for f in files:
                if Path(f).suffix.lower() in VIDEO and not f.startswith("."):
                    p = Path(d) / f
                    try:
                        found.append((p.stat().st_mtime, p))
                    except OSError:
                        pass
    return [p for _, p in sorted(found, key=lambda x: -x[0])]


def load(p):
    try:
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except (OSError, ValueError):
        return None


def check_records(project):
    """bin/vh check's records (out/check/*.check.json), newest first."""
    d = project / "out" / "check"
    recs = [(load(p), p) for p in d.glob("*.check.json")] if d.is_dir() else []
    return sorted(((r, p) for r, p in recs if r and r.get("version") == 1), key=lambda x: -(x[0].get("t") or 0))


def check_summary(project, r, p):
    v = project / r["video"] if r.get("video") and not os.path.isabs(r["video"]) else Path(r.get("video") or "")
    try:
        stale = v.stat().st_mtime > (r.get("t") or 0)
    except OSError:
        stale = None
    fails = [f["message"] for f in r.get("findings") or [] if f.get("severity") == "fail"]
    return {"record": rel(project, p), "video": r.get("video"), "at": r.get("at"), "t": r.get("t"), "verdict": r.get("verdict"),
            "exit": r.get("exit"), "counts": r.get("counts"), "fails": fails[:3], "stale": stale}


def main(argv):
    import argparse
    ap = argparse.ArgumentParser(prog="bin/vh status", description=__doc__.split("\n\n")[0])
    ap.add_argument("project", help="project folder (or a file inside it), or its name under projects/")
    ap.add_argument("--json", action="store_true", help="every field, as JSON (version 1)")
    a = ap.parse_args(argv)
    p = Path(a.project).expanduser()
    project = G.project_of(p) if p.exists() else None
    if project is None:
        project = R.find_project(a.project)
        if project is None:
            return 2
        if not (project / "BRIEF.md").is_file():
            print(f"status: {project} is not a project (no BRIEF.md)", file=sys.stderr)
            return 2
    now = time.time()
    proj = basics(project)
    rv = project / "REVIEW.md"
    review_text = G.strip_comments(G.read(rv)) if rv.is_file() else ""
    review_mtime = rv.stat().st_mtime if rv.is_file() else 0
    paused = reader._history(review_text)[1] if review_text else False
    st, cur = stops(project, review_text, review_mtime, proj["effort"], director_stops(proj["director"]), proj["lang"])
    # in_progress: the first stop with nothing yet after the last one that has something (a skipped stop has nothing of
    # its own), once every stop before it is done or skipped; the ones passed over, and those after a stop that still
    # waits, stay not_started
    last = max((i for i, s in enumerate(st) if s["state"] not in (None, "skipped")), default=-1)
    frontier = next((i for i, s in enumerate(st) if i > last and s["state"] is None), None)
    clear = frontier is not None and all(s["state"] in ("done", "skipped") for s in st[:frontier])
    for i, s in enumerate(st):
        if s["state"] is None:
            s["state"] = "in_progress" if i == frontier and clear else "not_started"
    # delivery: bin/vh deliver's records, or the final film checked and passing
    deliveries = []
    for top in ("out", "media"):
        base = project / top
        for rec in (base.rglob("*.deliver.json") if base.is_dir() else []):
            j = load(rec)
            if j:
                deliveries.append({"record": rel(project, rec), "output": rel(project, rec.parent / str(j.get("output", ""))),
                                   "master": rel(project, (rec.parent / str(j.get("master", ""))).resolve()) if j.get("master") else None,
                                   "time": j.get("time")})
    vids = renders(project)
    checks = check_records(project)
    by_video = {}
    for r, p in checks:
        by_video.setdefault(r.get("video"), (r, p))
    finals = [v for v in vids if v.name.lower().startswith("final") or "final" in v.relative_to(project).parts[:-1] or v.parent.name == "media"]
    final_ok = any((c := by_video.get(rel(project, v))) and c[0].get("verdict") == "pass" and (c[0].get("t") or 0) >= v.stat().st_mtime for v in finals)
    gates_through = all(s["state"] in ("done", "skipped") for s in st)
    deliver = {"id": "deliver", "name": "交付" if proj["lang"] == "zh" else "Delivery", "kind": "deliver", "pages": [], "page": None,
               "current": False, "record": None, "feedback": None, "note": None,
               "state": "done" if deliveries or final_ok else "in_progress" if gates_through else "not_started"}
    if deliver["state"] == "done":
        deliver["note"] = f"bin/vh deliver: {deliveries[-1]['output']}" if deliveries else "the final film passed bin/vh check"
    st.append(deliver)
    # the activity log: what runs now (and who is only waiting), and the last runs
    runs, _ = activity.runs(activity.read(project), now)
    running = [r for r in runs if r["state"] == "running"]
    working = [r for r in running if r["cmd"] not in LISTENING]
    listening = [r for r in running if r["cmd"] in LISTENING]
    recent = [r for r in runs if r["state"] in ("ok", "failed", "gone")][-5:]
    # the review: this round's page and the desk
    desk = None
    try:
        import server
        url = server.running(project)
        if url:
            desk = {"url": url, "listening": F.listening(project).get("listening", False)}
    except Exception:   # a desk that cannot be asked is a desk not running
        desk = None
    cur_stop = next((s for s in st if s["current"]), None)
    # open review items: a submission's change / ask items whose REVIEW.md section has no decision yet
    open_items = []
    for f, j in feedback_records(project):
        sec = review_section_for(review_text, f)
        if sec and G.record(sec[1])[0]:
            continue
        for it in j.get("items") or []:
            if isinstance(it, dict) and it.get("status") in ("change", "ask") and isinstance(it.get("target"), str):
                try:   # the label as REVIEW.md shows it (a span with its times)
                    label = F.readable(dict(it, label=it.get("label") or it["target"]), j.get("lang"))
                except (KeyError, TypeError, ValueError):
                    label = it.get("label") or it["target"]
                open_items.append({"round": j.get("round"), "file": rel(project, f), "target": it["target"], "status": it["status"],
                                   "label": label, "text": (it.get("text") or "")[:200]})
    warnings = []
    _, todo = reader._facts(reader.strip_comments(reader._read(project / "NOTES.md", warnings)), warnings)
    facts = [x["text"] for x in todo if not x["done"] and not x["text"].startswith("{")]   # not the template's {claim} line
    # who is waited on, and the next step in one line
    waiting = [s for s in st if s["state"] == "waiting_person"]
    agent = [s for s in st if s["state"] in ("waiting_agent", "in_progress")]
    if paused:
        waiting_on, nxt = "person", "paused (REVIEW.md): the person resumes it"
    elif waiting:
        s = waiting[0]
        waiting_on, nxt = "person", f"the person: review {s['name']} on " + (f"the desk {desk['url']}" if desk else s["page"] or "the chat")
    elif agent or working:
        waiting_on = "agent"
        s = agent[0] if agent else None
        nxt = ("the agent: " + (s["note"] or f"work towards {s['name']}")) if s else f"the agent: {working[0]['cmd']} is running"
    elif deliver["state"] == "done":
        waiting_on, nxt = "nobody", "delivered"
    else:
        waiting_on, nxt = "agent", "the agent: carry on"
    def vinfo(v):
        side = load(str(v) + ".render.json")
        dl = load(str(v) + ".deliver.json")
        c = by_video.get(rel(project, v))
        return {"path": rel(project, v), "size": v.stat().st_size, "mtime": iso(v.stat().st_mtime), "t": round(v.stat().st_mtime, 3),
                "render": {k: side.get(k) for k in ("frames", "fps", "pixels", "span", "seconds")} if side else None,
                "patches": len(side.get("patches") or []) if side else 0,
                "delivery": {"master": dl.get("master"), "time": dl.get("time")} if dl else None,
                "check": check_summary(project, *c) if c else None}
    out = {"version": 1, "project": proj, "paused": paused, "waiting_on": waiting_on, "next": nxt, "stations": st,
           "review": {"current": cur, "page": cur_stop["page"] if cur_stop else None, "desk": desk},
           "open": {"review_items": open_items, "facts_to_verify": facts},
           "renders": [vinfo(v) for v in vids[:10]], "deliveries": deliveries,
           "check": check_summary(project, *checks[0]) if checks else None,
           "activity": {"running": working, "listening": listening, "recent": recent}}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    show(out, now)
    return 0


def show(o, now):
    p = o["project"]
    spec = p["spec"]
    size = (spec.get("Output") or "").split(",")[0] if spec.get("Output") and "{" not in spec.get("Output", "") else ""
    head = " · ".join(x for x in (p["title"], p["type"], p["effort"], f"director {p['director']}" if p["director"] != "default" else "",
                                   size, spec.get("Watch on", "").split()[0] if spec.get("Watch on") and "{" not in spec.get("Watch on") else "") if x)
    print(head)
    w = max(len(s["name"]) for s in o["stations"])
    for s in o["stations"]:
        bits = [STATE_WORDS[s["state"]]]
        if s["state"] in ("waiting_person", "waiting_agent") and s["page"]:
            bits.append(s["page"])
        if s["current"] and o["review"]["desk"] and s["state"] == "waiting_person":
            bits.append(f"desk {o['review']['desk']['url']}" + (" (the agent is waiting)" if o["review"]["desk"]["listening"] else ""))
        if s["note"]:
            bits.append(s["note"])
        print(f"  {STATE_MARK[s['state']]} {s['name']:<{w}}  {' · '.join(bits)}")
    print(f"waiting on: {o['waiting_on']} — {o['next']}")
    ri, fv = o["open"]["review_items"], o["open"]["facts_to_verify"]
    if ri or fv:
        print("open: " + " · ".join(x for x in (f"{len(ri)} review item(s) (round {', '.join(dict.fromkeys(str(i['round']) for i in ri))})" if ri else "",
                                               f"{len(fv)} fact(s) to verify (NOTES.md)" if fv else "") if x))
    bits = []
    if o["renders"]:
        r = o["renders"][0]
        rd = r["render"]
        bits.append(f"last render {r['path']} ({r['mtime'][5:16].replace('T', ' ')}"
                    + (f", {rd['frames']} frames {rd['pixels'][0]}x{rd['pixels'][1]}" if rd and rd.get("pixels") else "") + ")")
    c = o["check"]
    if c:
        n = c.get("counts") or {}
        bits.append(f"last check {c['verdict']} on {c['video']} ({n.get('fail', 0)} fail, {n.get('warn', 0)} warn"
                    + (", the video changed since" if c.get("stale") else "") + ")")
    if bits:
        print(" · ".join(bits))
    for r in o["activity"]["running"]:
        pr = r.get("progress") or {}
        print(f"running: {r['cmd']} {' '.join(str(x) for x in r['args'][1:4])}".rstrip()
              + f" ({int(now - r['start'])} s" + (f", {pr['done']}/{pr.get('total', '?')} {pr.get('unit', '')}".rstrip() if pr.get("done") is not None else "") + ")")


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
