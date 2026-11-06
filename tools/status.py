"""bin/vh status: where a project stands, from the files it already has. Read-only; no browser, no ffprobe.

usage: bin/vh status <project> [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

The stops, in the pipeline's order: gate ① ② ③ always; a checkpoint E0–E5 when it has a page, a REVIEW.md section or the
BRIEF's Director line asks for it (stop=E3); a review page with another name ("final") as a stop of its own; then delivery.
Each has a state:
  done            a decision for it is on record in REVIEW.md: "定了：…" (the template's {…} does not count), in the last
                  section about its latest page (the desk's section for a submission, or one that names
                  out/review/gate-<n>.html, as the template's sections do: REVIEW.md grows downwards, so a second
                  review of the page comes after the first); with no such section, in the stop's section when REVIEW.md
                  was written after that page (said in the stop's note). Gate ① goes by gatecheck.py's own rule, as
                  bin/vh render and check do: a decision and the person's words in a gate ① section, and the concept
                  on record in DECISIONS.md
  skipped         Effort quick (and no page of its own), or waived in the user's own words in REVIEW.md
  waiting_person  its page is out (bin/vh gate made it: a gate JSON not sent yet is not), it is this round (out/review/.current),
                  and nothing has come back for it yet
  waiting_agent   the person submitted on the desk and no agent has it yet, or an agent has it and REVIEW.md has no
                  decision for it yet; or the project moved on past its page with no decision on record; gate ①
                  decided, but its record lacks the person's words or DECISIONS.md's concept (render and check refuse)
  in_progress     the first stop with nothing yet after the last one that has something, when all before it are done or
                  skipped: what the agent works towards
  not_started     later stops; a stop passed over without a record stays not_started
  no_record       every stop of a standard or studio project with no REVIEW.md (made before the templates had one):
                  nothing to read its review from (gatecheck.py does not check those either)
Delivery is done once bin/vh deliver has written a record, or the final film (out/final*, out/final/, media/) has a passing
bin/vh check record of that very film (the size and mtime_ns it kept are the film's now; a record from before those: newer
than the film), and gate ③ is done or skipped (a delivery before it is said in the note); in progress once every stop is
done or skipped.
waiting_on: person (a stop waits for them, or REVIEW.md says the project is paused), agent (one waits for the agent,
the agent works towards one, or a command is running), nobody (delivered), or unknown (no REVIEW.md).
Also: the versions of the project's films (out/versions/versions.json, bin/vh versions; out/versions and out/proxy are not
listed as renders), the latest renders with what their sidecars say (.render.json, .deliver.json, the check record), the review items
still open (a desk submission's change and ask items whose REVIEW.md section has no 定了 / 改了 yet), the facts NOTES.md
still lists to verify, the last check, the material on record (bin/vh assets: how many, the licences not cleared, what
the films loaded that the ledger lacks, the spend against the budget), the cast in cast/ (bin/vh cast: the entries by
kind, the settled ones, what its check would fail), the research in research/ (bin/vh scout's
records, the days with a hot-list snapshot, bin/vh ref's references), and the commands running now and the last ones
(the activity log).
The next step, from the stop the project is at: who has it (the person, the agent), what to do, which commands, which sections
to read (each a "<file.md>#<section>" for bin/vh know --show), and how many {…} are still unfilled in BRIEF.md, STYLE.md and
STORYBOARD.md. The line starts "next:"; --json has it as next_step (the older "next" is one sentence, and stays).
--json: every field (tools/desk/README.md, 给客户端的数据, has the schema; "version": 1). Exit 0, 2 when there is no project.
"""
import json, os, re, shlex, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "desk"))
import activity, checkrec as C, gatecheck as G, proxy as P, review as R, versions as V   # noqa: E402,E401
import feedback as F, reader   # noqa: E402,E401

ORDER = ["1", "E0", "E1", "2", "E2", "E3", "E4", "3", "E5"]
VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v"}
SKIP_DIRS = {"frames", "node_modules", "__pycache__", ".venv", "venv"}
OUT_SKIP = {"versions", "proxy"}   # out/versions (listed from its record) and out/proxy: not renders; only directly in out/
STATE_MARK = {"done": "✓", "skipped": "–", "waiting_person": "●", "waiting_agent": "◆", "in_progress": "…", "not_started": "·",
              "no_record": "○"}
STATE_WORDS = {"done": "done", "skipped": "skipped", "waiting_person": "waiting for you", "waiting_agent": "waiting for the agent",
               "in_progress": "in progress", "not_started": "not started", "no_record": "no record"}
LISTENING = ("desk", "gate")   # a running desk or gate --wait is someone waiting, not work being done
PLACEHOLDER = re.compile(r"\{[^{}\n]*\}")
# what the next step sends an agent to read, each for bin/vh know --show (tools/ci.sh checks each is there)
R_PAGE, R_DESK, R_GATES, R_DIRECTOR = (f"playbook/01-pipeline.md#{x}" for x in ("审阅页", "审阅台", "三道人工关卡", "导演模式"))
R_ANIMATIC, R_LONG = "playbook/01-pipeline.md#animatic", "playbook/01-pipeline.md#长片"
R_IDEAS, R_CARDS = "playbook/12-ideation.md#4.", "playbook/12-ideation.md#7."
R_FRAMES, R_PHONE, R_SILENT = (f"playbook/02-verification.md#{x}" for x in ("各引擎的取帧命令", "手机测试", "静默失败"))
R_SCORES, R_LAYERS, R_QUICK = "templates/TASTE_CHECKLIST.md#打分层", "playbook/02-verification.md#七层检查", "playbook/quick.md"
R_NARRATIVE, R_SOUND, R_HF, R_MANIM = "playbook/09-narrative.md#5. 长片", "playbook/04-audio.md#常用命令", "engines/README.md#HyperFrames", "engines/README.md#Manim CE"
READS = (R_PAGE, R_DESK, R_GATES, R_DIRECTOR, R_ANIMATIC, R_LONG, R_IDEAS, R_CARDS, R_FRAMES, R_PHONE, R_SILENT, R_SCORES, R_LAYERS, R_QUICK,
         R_NARRATIVE, R_SOUND, R_HF, R_MANIM)


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
    """The checkpoints a Director line asks for: stop=E3, stop=E1,E3, and every stop= on the line (stop=E1, stop=E3)."""
    return {s.upper() for grp in re.findall(r"\bstop\s*=\s*(E[0-9](?![0-9])(?:\s*[,，]?\s*E[0-9](?![0-9]))*)", director_line or "", re.I)
            for s in re.findall(r"E[0-9]", grp, re.I)}


def feedback_records(project):
    """[(path, record)] of the desk's submissions, oldest first."""
    return sorted(F._records(project), key=lambda x: F._order(*x))


def review_section_for(review, fb_path):
    """The REVIEW.md section the desk wrote for one submission (it names the submission's JSON), as (title, lines)."""
    name = f"out/review/feedback/{fb_path.name}"
    return next(((t, ls) for t, ls in G.sections(review)[1:] if any(name in x for x, c in ls if not c)), None)


def stops(project, review_text, review_mtime, effort, asked, lang, no_review=False):
    """The stops and their states (but in_progress / not_started, which need the order): ([dict], this round).
    no_review: a standard or studio project without REVIEW.md, every stop no_record."""
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
        # the record. Gate ①: gatecheck's own rule over every gate ① section, as bin/vh render and check read it. Another
        # stop: the latest section about its latest page (REVIEW.md grows downwards: a second review of the same page,
        # the desk's section, comes after the first); with none, the stop's own section, if REVIEW.md was written after
        # the page (by date, then: said in the note, as the template's 页面 line would settle it)
        page_secs = G.page_sections(review_text, pid) if pid else []
        stop_secs = G.stop_sections(review_text, key) if is_stop else []
        decided = said = False
        how = None
        if key == "1":
            decided, said = G.gate1(review_text)
            how = "gate1"
        elif page_secs:
            decided = G.record(page_secs[-1][1])[0]
            said = any(G.record(ls)[1] for _, ls in page_secs)
            how = "page"
        elif stop_secs:
            d = s = False
            for _, ls in stop_secs:
                a, b = G.record(ls)
                d, s = d or a, s or b
            if latest is None or review_mtime >= latest.stat().st_mtime:
                decided, said, how = d, s, "stop" if latest is None else "stop_by_date"
            elif d:
                how = "stop_older"   # a decision in the stop's section, written before its page: not counted
        waived = G.waived_stop(review_text, key) if is_stop else None
        st["record"] = {"decided": decided, "said": said, "waived": waived, "from": how}
        missing = []
        if key == "1":
            dec = project / "DECISIONS.md"
            st["record"]["concept_on_record"] = concept = dec.is_file() and G.concept_decided(G.read(dec))
            if decided and effort != "quick":   # what gatecheck would still ask for
                missing = ([] if said else ["the person's words (原话) in REVIEW.md"]) + ([] if concept else ["the concept row in DECISIONS.md"])
        # the desk's submissions for this stop's latest page, after it was written
        mine = [(f, j) for f, j in subs if pid and j.get("round") == pid and f.stat().st_mtime >= latest.stat().st_mtime]
        pend = [f for f, _ in mine if f.name not in consumed]
        handed = [f for f, _ in mine if f.name in consumed]
        if mine:
            st["feedback"] = {"submitted": len(mine), "handed": len(handed), "pending": len(pend),
                              "last": rel(project, mine[-1][0])}
        stub = f"out/review/gate-{pid or key}.html"
        if no_review and effort != "quick":
            st["state"] = "no_record"
        elif waived or (effort == "quick" and not plist):
            st["state"] = "skipped"
            st["note"] = f"waived in the user's words ({waived})" if waived else "Effort quick: no gates"
        elif decided and missing:   # gatecheck's verdict: not on record yet
            st["state"], st["note"] = "waiting_agent", f"decided, but without {' and '.join(missing)}: bin/vh render and check refuse the whole film"
        elif decided:
            st["state"] = "done"
            if not said:
                st["note"] = "decided, but the person's words are not in REVIEW.md"
            elif how == "stop_by_date":
                st["note"] = f"decided in its REVIEW.md section, read by date: the section names no page (its 页面 line: {stub})"
        elif latest is not None and not latest.with_suffix(".html").exists() and not pend and not handed:
            pass   # written, not sent yet: bin/vh gate makes the page, so it has not reached the person
        elif latest is not None and pid == cur:
            if pend:
                st["state"], st["note"] = "waiting_agent", f"{len(pend)} submission(s) not handed to the agent yet (bin/vh desk feedback)"
            elif handed:
                st["state"], st["note"] = "waiting_agent", "the submission was handed over; REVIEW.md has no decision for it yet"
            else:
                st["state"] = "waiting_person"
        elif latest is not None:
            st["state"], st["note"] = "waiting_agent", f"this round moved on to {cur}; REVIEW.md has no decision for {pid}"
        if how == "stop_older" and st["state"] not in ("done", "skipped", "no_record"):
            st["note"] = ((st["note"] + "; ") if st["note"] else "") + \
                f"its REVIEW.md section has a decision, but names no page and is older than the page: not counted (its 页面 line: {stub})"
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
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith(".") and len(depth) < 3
                       and not (top == "out" and not depth and x in OUT_SKIP)]
            for f in files:
                if Path(f).suffix.lower() in VIDEO and not f.startswith("."):
                    p = Path(d) / f
                    try:
                        found.append((p, p.stat()))
                    except OSError:   # gone since the listing
                        pass
    return sorted(found, key=lambda x: -x[1].st_mtime)


def load(p):
    try:
        j = json.loads(Path(p).read_text(encoding="utf-8"))
        return j if isinstance(j, dict) else None
    except (OSError, ValueError):
        return None


def num(x):
    """A number from a machine-written record, else None (a string, a bool, a list: the record is not trusted)."""
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def text(x):
    return x if isinstance(x, str) else None


def check_records(project):
    """bin/vh check's records (out/check/*.check.json), newest first; each one's fields of the wrong type dropped."""
    d = project / "out" / "check"
    recs = [(load(p), p) for p in d.glob("*.check.json")] if d.is_dir() else []
    out = []
    for r, p in recs:
        if not r or r.get("version") != 1:
            continue
        fs = r.get("findings") if isinstance(r.get("findings"), list) else []
        counts = r.get("counts") if isinstance(r.get("counts"), dict) else {}
        out.append((dict(r, video=text(r.get("video")), t=num(r.get("t")), at=text(r.get("at")), verdict=text(r.get("verdict")),
                         exit=r.get("exit") if isinstance(r.get("exit"), int) and not isinstance(r.get("exit"), bool) else None,
                         findings=[f for f in fs if isinstance(f, dict)], counts={k: v for k, v in counts.items() if num(v) is not None}), p))
    return sorted(out, key=lambda x: -(x[0]["t"] or 0))


def film_changed(r, st):
    """Is the film (st: its os.stat) other than the one the check record r was made of? By the size and mtime_ns the record
    kept (a film put back with an old modification time differs in one of them); a record from before those: the film is
    newer than the record."""
    ch = C.film_changed(r, st)
    return st.st_mtime > (r["t"] or 0) if ch is None else ch


def check_summary(project, r, p):
    v = (project / r["video"] if not os.path.isabs(r["video"]) else Path(r["video"])) if r["video"] else None
    try:
        stale = film_changed(r, v.stat()) if v else None
    except (OSError, ValueError):
        stale = None
    fails = [f["message"] for f in r["findings"] if f.get("severity") == "fail" and isinstance(f.get("message"), str)]
    return {"record": rel(project, p), "video": r["video"], "at": r["at"], "t": r["t"], "verdict": r["verdict"],
            "exit": r["exit"], "counts": r["counts"], "fails": fails[:3], "stale": stale}


def render_info(side):
    """What a .render.json says, each field of the wrong type dropped: frames, fps, pixels [w, h], span [a, b], seconds."""
    def pair(x):
        return x if isinstance(x, list) and len(x) == 2 and all(num(y) is not None for y in x) else None
    return {"frames": num(side.get("frames")), "fps": num(side.get("fps")), "pixels": pair(side.get("pixels")),
            "span": pair(side.get("span")), "seconds": num(side.get("seconds"))}


def unfilled(project):
    """{file: how many {…} are still in it}, comments aside; the template's {none} is a value, not a blank."""
    out = {}
    for name in ("BRIEF.md", "STYLE.md", "STORYBOARD.md"):
        f = project / name
        n = sum(1 for x in PLACEHOLDER.findall(reader.strip_comments(G.read(f))) if x[1:-1].strip().lower() != "none") if f.is_file() else 0
        if n:
            out[name] = n
    return out


def shown(project):
    """The project as a command takes it: from the repo's root when it is under it (bin/vh runs from there), else whole."""
    try:
        return shlex.quote(project.relative_to(HERE.parent.resolve()).as_posix())
    except ValueError:
        return shlex.quote(str(project))


def scaffold_todo(project, proj):
    """The command that finishes a scaffold bin/vh new could not (an engine it sets up, and its files are not there); else None."""
    p = shown(project)
    kind = (proj["type"] or "")[:2]
    if (project / "film.html").is_file() or (project / "edit.json").is_file():
        return None
    if kind in ("02", "03", "05", "08") and not (project / "hyperframes.json").is_file() and not (project / "index.html").is_file():
        m = re.search(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", proj["spec"].get("Output") or "")
        frame = {(1080, 1350): "4:5", (1080, 1440): "3:4", (1080, 1080): "square", (1920, 1080): "landscape"}.get((int(m[1]), int(m[2])) if m else None, "portrait")
        return f"bin/vh hf-init {p} {frame}"
    if kind in ("04", "07") and (project / "render.mjs").is_file() and not (project / "node_modules").is_dir():
        return f"(cd {p} && npm install)"
    return None


def render_cmd(project, proj, final):
    """The command that renders this project's film (out/draft.mp4 or out/final.mp4), by the engine its files show."""
    p, name = shown(project), "out/final.mp4" if final else "out/draft.mp4"
    if (project / "edit.json").is_file() or (project / "film.html").is_file():
        return f"bin/vh render {p} --out {p}/{name}"
    if (project / "hyperframes.json").is_file():
        return f"(cd {p} && HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1 npx hyperframes render --quality {'delivery' if final else 'draft'} --output {name})"
    if (project / "render.mjs").is_file():
        return f"(cd {p} && node render.mjs --clip --out={name})"
    if (proj["type"] or "")[:2] in ("01", "06"):
        return f"(cd {p} && uv run manim {'-qh --fps 30' if final else '-ql'} scene.py <Scene>)"
    return f"bin/vh render {p} --out {p}/{name}"


def film_state(project, by_video):
    """The newest film and its check: (path from the project or None, none | unchecked | stale | failed | passed, what failed)."""
    film = P.newest_film(project)
    if film is None:
        return None, "none", []
    r = rel(project, film)
    c = by_video.get(r)
    if not c:
        return r, "unchecked", []
    try:
        if film_changed(c[0], film.stat()):
            return r, "stale", []
    except OSError:
        return r, "unchecked", []
    if c[0]["verdict"] == "pass":
        return r, "passed", []
    return r, "failed", [f["message"] for f in c[0]["findings"] if f.get("severity") == "fail" and isinstance(f.get("message"), str)][:2]


def is_final(path):
    """out/final*, out/final/…, media/…: a film that counts as the delivery (as main takes it)."""
    parts = Path(path).parts
    return parts[-1].lower().startswith("final") or "final" in parts[:-1] or parts[0] == "media"


def next_step(project, proj, st, paused, no_record, working, desk, by_video):
    """{who, do, commands, read, unfilled}: who has the next move at the stop the project is at, and how to take it."""
    p = shown(project)
    left = unfilled(project)
    doc = f"video-types/{proj['type']}.md" if proj["type"] else None
    long_film = (proj["type"] or "").startswith("10-")
    m = re.search(r"(\d+)\s*s\b", proj["spec"].get("Output") or "")
    if m and int(m.group(1)) > 180:
        long_film = True

    def out(who, do, commands=(), read=()):
        return {"who": who, "do": do, "commands": [c for c in commands if c], "read": list(dict.fromkeys(x for x in read if x)), "unfilled": left}
    busy = f"{working[0]['cmd']} is running (bin/vh activity {p}); when it ends: " if working else ""
    if no_record:
        return out("agent" if working else "unknown", busy + "no REVIEW.md: this project keeps no review record (made before the templates had one), so carry on from its files")
    if paused:
        return out("person", "paused (REVIEW.md): the person resumes it")
    wait = next((s for s in st if s["state"] == "waiting_person"), None)
    if wait:
        where = f"the desk {desk['url']}" if desk else wait["page"] or "the chat"
        return out("person", f"the person reviews {wait['name']} on {where}: stop here, and write their words into REVIEW.md when they answer",
                   [f"bin/vh desk wait {p}"] if desk and not desk.get("listening") else [], [R_DESK] if desk else [])
    s = next((x for x in st if x["state"] in ("waiting_agent", "in_progress")), None)
    if s is None:
        delivered = st[-1]["state"] == "done"
        return out("nobody" if delivered and not working else "agent", busy + ("delivered: what this film taught goes into LESSONS.md" if delivered else "carry on"))
    todo = scaffold_todo(project, proj)
    if todo:
        return out("agent", busy + "the engine's scaffold did not finish: this finishes it", [todo], [R_HF] if "hf-init" in todo else [])
    if s["state"] == "waiting_agent":
        fb = s["feedback"] or {}
        if fb.get("pending"):
            return out("agent", busy + f"read the person's submission for {s['name']}, then write what was decided into REVIEW.md", [f"bin/vh desk feedback {p}"], [R_DESK])
        if fb.get("handed"):
            return out("agent", busy + f"write what was decided and changed under the desk's section for {s['name']} in REVIEW.md (定了 / 改了)", [], [R_DESK])
        return out("agent", busy + (s["note"] or f"record the decision for {s['name']} in REVIEW.md"), [], [R_GATES])
    key = s["id"]
    film, fstate, fails = film_state(project, by_video)
    check = [f"bin/vh check {p}"]

    def fill(what):
        """what, with the {…} the files it names still have in front of it."""
        return ", ".join(f"fill {n} ({left[n]} {{…}} left)" for n in what if n in left)

    def page():
        """The gate JSON's state: what to say about it, and the commands that send it."""
        f = project / "out" / "review" / f"gate-{key}.json"
        send = f"bin/vh gate {p} {key}"
        try:
            n = len(R.placeholders(json.loads(f.read_text(encoding="utf-8-sig")))) if f.is_file() else None
        except (OSError, ValueError):
            n = None
        if n:
            return f"fill out/review/gate-{key}.json ({n} {{填：…}} left), then send it", [send]
        return (f"send the page for {s['name']}", [send]) if f.is_file() else (f"then the page for {s['name']}", [f"bin/vh gate {p} {key} --init", send])
    if key == "1":
        say, cmds = page()
        return out("agent", busy + "; ".join(x for x in (fill(["BRIEF.md"]), "NOTES.md's material first, then 2–3 concept cards with a frame each and the outline", say) if x),
                   cmds, [doc, R_IDEAS, R_CARDS, R_PAGE])
    if key == "2":
        say, cmds = page()
        return out("agent", busy + "; ".join(x for x in (fill(["STYLE.md", "STORYBOARD.md"]), "the shots in shots.json, then their key frames and the rhythm chart", say) if x),
                   [f"bin/vh storyboard {p}", f"bin/vh rhythm {p}"] + cmds, [R_PAGE, R_ANIMATIC, R_FRAMES, R_LONG if long_film else None, R_NARRATIVE if long_film else None])
    if key == "3":
        if fstate == "none":
            return out("agent", busy + "write the scenes, look at their frames, then render a draft", [f"bin/vh frames {p} --at 1,5,9", render_cmd(project, proj, False)],
                       [R_FRAMES, R_LONG if long_film else None])
        if fstate in ("unchecked", "stale"):
            return out("agent", busy + f"check {film} and look at its contact sheet", check + [f"bin/vh sheet {p}/{film}"], [R_FRAMES, R_PHONE, R_SILENT])
        if fstate == "failed":
            return out("agent", busy + f"fix what bin/vh check failed on {film}" + (": " + "; ".join(fails) if fails else ""), check, [R_SILENT])
        say, cmds = page()
        return out("agent", busy + f"a fresh reviewer scores {film}, fix the worst of it (at most 3 places), write down the 2–3 places you like least; {say}", cmds, [R_SCORES, R_LAYERS, R_PAGE])
    if s["kind"] != "deliver":
        say, cmds = page()
        return out("agent", busy + f"prepare {s['name']}, a stop the director mode asks for; {say}", cmds, [R_DIRECTOR, R_PAGE])
    # delivery: quick's whole path, and the end of the others'
    quick = proj["effort"] == "quick"
    if fstate == "none":
        return out("agent", busy + "; ".join(x for x in (fill(["BRIEF.md"]), "a short storyboard table, the scenes, then a draft" if quick else "render the final") if x),
                   [render_cmd(project, proj, not quick)], [R_QUICK, f"{doc}#工作流" if doc else None, f"{doc}#禁止" if doc else None, R_PHONE] if quick else [R_FRAMES])
    if fstate in ("unchecked", "stale"):
        return out("agent", busy + f"check {film}" + (" and look at its contact sheet" if not is_final(film) else ""),
                   check + ([f"bin/vh sheet {p}/{film}"] if not is_final(film) else []), [R_PHONE] if quick else [])
    if fstate == "failed":
        return out("agent", busy + f"fix what bin/vh check failed on {film}" + (": " + "; ".join(fails) if fails else ""), check, [R_SILENT])
    if not is_final(film):
        return out("agent", busy + "render the final at delivery quality, put the sound on when it has any (bin/vh mix, qa, mux), and check it",
                   [render_cmd(project, proj, True), f"bin/vh check {p}/out/final.mp4"], [R_SOUND])
    return out("agent", busy + "the final passes bin/vh check: bin/vh deliver makes the copy to upload", [f"bin/vh deliver {p}/{film}"], [])


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
    no_record = not rv.is_file() and proj["effort"] != "quick"   # made before the templates had one: nothing to read
    paused = reader._history(review_text)[1] if review_text else False
    st, cur = stops(project, review_text, review_mtime, proj["effort"], director_stops(proj["director"]), proj["lang"], no_record)
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
            if j and text(j.get("output")):
                deliveries.append({"record": rel(project, rec), "output": rel(project, rec.parent / j["output"]),
                                   "master": rel(project, (rec.parent / j["master"]).resolve()) if text(j.get("master")) else None,
                                   "time": text(j.get("time"))})
    vids = renders(project)
    checks = check_records(project)
    by_video = {}
    for r, p in checks:
        if r["video"]:
            by_video.setdefault(r["video"], (r, p))
    finals = [(v, s) for v, s in vids if v.name.lower().startswith("final") or "final" in v.relative_to(project).parts[:-1] or v.parent.name == "media"]
    final_ok = any((c := by_video.get(rel(project, v))) and c[0]["verdict"] == "pass" and not film_changed(c[0], s) for v, s in finals)
    gates_through = all(s["state"] in ("done", "skipped") for s in st)
    g3 = next((s for s in st if s["id"] == "3"), None)
    g3_through = g3 is not None and g3["state"] in ("done", "skipped")   # delivered: the person has seen the draft (or waived it)
    shipped = bool(deliveries or final_ok)
    deliver = {"id": "deliver", "name": "交付" if proj["lang"] == "zh" else "Delivery", "kind": "deliver", "pages": [], "page": None,
               "current": False, "record": None, "feedback": None, "note": None,
               "state": "no_record" if no_record else "done" if shipped and g3_through else "in_progress" if gates_through else "not_started"}
    if shipped:
        what = f"bin/vh deliver: {deliveries[-1]['output']}" if deliveries else "the final film passed bin/vh check"
        deliver["note"] = what if deliver["state"] == "done" else f"{what} (no REVIEW.md says whether gate ③ was passed)" if no_record \
            else f"{what}, but gate ③ is not decided yet: the delivery counts once it is"
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
        for it in j.get("items") if isinstance(j.get("items"), list) else []:
            if isinstance(it, dict) and it.get("status") in ("change", "ask") and isinstance(it.get("target"), str):
                try:   # the label as REVIEW.md shows it (a span with its times)
                    label = F.readable(dict(it, label=it.get("label") or it["target"]), j.get("lang"))
                except (KeyError, TypeError, ValueError):
                    label = text(it.get("label")) or it["target"]
                open_items.append({"round": text(j.get("round")), "file": rel(project, f), "target": it["target"], "status": it["status"],
                                   "label": str(label), "text": (text(it.get("text")) or "")[:200]})
    warnings = []
    _, todo = reader._facts(reader.strip_comments(reader._read(project / "NOTES.md", warnings)), warnings)
    facts = [x["text"] for x in todo if not x["done"] and not x["text"].startswith("{")]   # not the template's {claim} line
    # who is waited on, and the next step in one line
    waiting = [s for s in st if s["state"] == "waiting_person"]
    agent = [s for s in st if s["state"] in ("waiting_agent", "in_progress")]
    if no_record:
        waiting_on, nxt = ("agent", f"the agent: {working[0]['cmd']} is running") if working else \
            ("unknown", "no REVIEW.md: this project keeps no review record (made before the templates had one)")
    elif paused:
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
    # the versions of the project's films (bin/vh versions): null before the first render or patch recorded one
    vers = None
    if (V.store(project) / V.RECORD).is_file():
        try:
            L = V.listing(project)
            vers = {"record": L["record"], "keep": L["keep"], "current": L["current"], "kept_bytes": L["kept_bytes"],
                    "list": [{k: x.get(k) for k in ("id", "at", "t", "film", "file", "state", "made_by", "from", "note", "changed", "frames",
                                                     "pixels", "check")} for x in L["versions"]]}
        except (ValueError, OSError) as e:
            vers = {"error": str(e)}
    cur_of = {f: i for f, i in (vers or {}).get("current", {}).items()}
    # the material on record (bin/vh assets, tools/assets/uses.py): how many, the licences not cleared, what the films loaded
    # that the ledger lacks, and the spend against the budget; a ledger that cannot be read is said, never a failure
    try:
        sys.path.insert(0, str(HERE / "assets"))
        import uses as U
        assets = U.overview(project)
    except Exception as e:
        assets = {"error": f"the asset ledger could not be read ({e})"}
    # the cast's settled references (bin/vh cast, tools/cast.py's overview): files only, never a failure
    try:
        import cast as CA
        cast = CA.overview(project)
    except Exception as e:
        cast = {"error": f"cast/ could not be read ({e})"}
    # the research on record (bin/vh scout, bin/vh ref; tools/scout/scout.py's overview): files only, never a failure
    try:
        sys.path.insert(0, str(HERE / "scout"))
        import scout as S
        research = S.overview(project)
    except Exception as e:
        research = {"error": f"research/ could not be read ({e})"}

    def vinfo(v, s):
        side = load(str(v) + ".render.json")
        dl = load(str(v) + ".deliver.json")
        c = by_video.get(rel(project, v))
        return {"path": rel(project, v), "size": s.st_size, "mtime": iso(s.st_mtime), "t": round(s.st_mtime, 3),
                "render": render_info(side) if side else None,
                "patches": len(side["patches"]) if side and isinstance(side.get("patches"), list) else 0,
                "delivery": {"master": text(dl.get("master")), "time": text(dl.get("time"))} if dl else None,
                "check": check_summary(project, *c) if c else None, "version": cur_of.get(rel(project, v))}
    out = {"version": 1, "project": proj, "paused": paused, "waiting_on": waiting_on, "next": nxt, "stations": st,
           "review": {"current": cur, "page": cur_stop["page"] if cur_stop else None, "desk": desk},
           "open": {"review_items": open_items, "facts_to_verify": facts},
           "renders": [vinfo(v, s) for v, s in vids[:10]], "deliveries": deliveries, "versions": vers,
           "check": check_summary(project, *checks[0]) if checks else None, "assets": assets, "cast": cast, "research": research,
           "activity": {"running": working, "listening": listening, "recent": recent},
           "next_step": next_step(project, proj, st, paused, no_record, [r for r in working if r.get("run") != os.environ.get("OVH_ACTIVITY_RUN")], desk, by_video)}   # (not the command that asks: bin/vh new)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    show(out, now)
    return 0


def show(o, now):
    p = o["project"]
    spec = p["spec"]
    m = re.search(r"\d{3,4}\s*[x×]\s*\d{3,4}", spec.get("Output") or "")   # the frame size, however the line is written
    watch = (spec.get("Watch on") or "").split()
    head = " · ".join(x for x in (p["title"], p["type"], p["effort"], f"director {p['director']}" if p["director"] != "default" else "",
                                   m.group(0) if m else "", watch[0] if watch and "{" not in watch[0] else "") if x)
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
    n = o["next_step"]
    print(f"next: {n['who']} — {n['do']}")
    if n["commands"]:
        print("  run: " + " · ".join(n["commands"]))
    if n["read"]:
        print("  read (bin/vh know --show): " + " · ".join(n["read"]))
    ri, fv = o["open"]["review_items"], o["open"]["facts_to_verify"]
    if ri or fv:
        print("open: " + " · ".join(x for x in (f"{len(ri)} review item(s) (round {', '.join(dict.fromkeys(str(i['round']) for i in ri))})" if ri else "",
                                               f"{len(fv)} fact(s) to verify (NOTES.md)" if fv else "") if x))
    bits = []
    if o["renders"]:
        r = o["renders"][0]
        rd = r["render"]
        d = ([f"{rd['frames']} frames"] if rd and rd.get("frames") is not None else []) \
            + ([f"{rd['pixels'][0]}x{rd['pixels'][1]}"] if rd and rd.get("pixels") else [])
        bits.append(f"last render {r['path']} ({r['mtime'][5:16].replace('T', ' ')}" + (", " + " ".join(d) if d else "") + ")")
    c = o["check"]
    if c and c.get("verdict"):
        n = c.get("counts") or {}
        bits.append(f"last check {c['verdict']} on {c['video']} ({n.get('fail', 0)} fail, {n.get('warn', 0)} warn"
                    + (", the video changed since" if c.get("stale") else "") + ")")
    if bits:
        print(" · ".join(bits))
    a = o.get("assets") or {}
    bud = a.get("budget") or {}
    if a.get("ledger") or bud.get("spent") or bud.get("limit") or bud.get("unlimited") or a.get("error"):
        try:
            import budget
            money = budget.line(Path(o["project"]["path"]))
        except Exception:   # tools/assets could not be read (said in a["error"])
            money = ""
        bits = [f"{a.get('records', 0)} on record"] + [x for x in (
            f"{a['uncleared']} not cleared" + (f" ({a['not_taken']} not taken under {a['policy']})" if a.get("not_taken") else "") if a.get("uncleared") else "",
            f"{a['unregistered']} loaded but not on record" if a.get("unregistered") else "", f"{a['aigc']} AI-generated" if a.get("aigc") else "") if x]
        print("assets: " + ", ".join(bits) + (f" · {money}" if money else "") + (f" · {a['error']}" if a.get("error") else "") + " (bin/vh assets)")
    ca = o.get("cast") or {}
    if ca.get("entries") or ca.get("error"):
        kinds = ", ".join(f"{n} {k}{'' if n == 1 else 's'}" for k, n in sorted((ca.get("by_kind") or {}).items()))
        print("cast: " + (ca["error"] if ca.get("error") else f"{ca['entries']} entr{'y' if ca['entries'] == 1 else 'ies'} ({kinds}), {ca.get('final', 0)} settled"
              + (f", {ca['failures']} failure{'' if ca['failures'] == 1 else 's'} in its check" if ca.get("failures") else "")) + " (bin/vh cast)")
    rs = o.get("research") or {}
    sc, hot, refs = rs.get("scout") or {}, rs.get("hot") or {}, rs.get("refs") or {}
    bits = [x for x in (
        f"{sc['records']} scout record{'s' if sc['records'] != 1 else ''} ({sc['latest']} looked at"
        + (f", {sc['films']} your own" if sc.get("films") else "") + ")" if sc.get("records") else "",
        f"hot lists on {hot['days']} day{'s' if hot['days'] != 1 else ''} (the last {hot['last']})" if hot.get("days") else "",
        f"{refs['records']} reference{'s' if refs['records'] != 1 else ''}" if refs.get("records") else "",
        refs.get("error") or "", rs.get("error") or "") if x]
    if bits:
        print("research: " + " · ".join(bits) + " (bin/vh scout, bin/vh ref)")
    vs = o.get("versions") or {}
    if vs.get("list"):
        kept = sum(1 for x in vs["list"] if x["state"] == "kept")
        print("versions: " + (", ".join(f"{i} current at {f}" for f, i in vs["current"].items()) or "none current")
              + (f" · {kept} kept" if kept else "") + " (bin/vh versions)")
    elif vs.get("error"):
        print(f"versions: {vs['error']}")
    for r in o["activity"]["running"]:
        pr = r.get("progress") or {}
        print(f"running: {r['cmd']} {' '.join(str(x) for x in r['args'][1:4])}".rstrip()
              + f" ({int(now - r['start'])} s" + (f", {pr['done']}/{pr.get('total', '?')} {pr.get('unit', '')}".rstrip() if pr.get("done") is not None else "") + ")")


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
