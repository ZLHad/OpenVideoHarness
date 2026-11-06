"""bin/vh status: where a project stands, from the files it already has. Read-only; no browser, no ffprobe.

usage: bin/vh status <project> [--json]
<project> is a folder (or a file inside it), or a name under $OVH_PROJECTS / projects/ (the date prefix optional).

The stops, in the pipeline's order: gate ① ② ③ always; a checkpoint E0–E5 when it has a page, a REVIEW.md section or the
BRIEF's Director line asks for it (stop=E3, or voice=own: what a person keeps goes with the stop where playbook/01's 导演模式
table first has it, voice and script at E1, character and theme at E0, packaging at gate ③); a review page with another name
("final") as a stop of its own; then delivery. Each has a state:
  done            a decision for it is on record in REVIEW.md: "定了：…" (the template's {…} does not count), in the last
                  section about its latest page (the desk's section for a submission, or one that names
                  out/review/gate-<n>.html, as the template's sections do: REVIEW.md grows downwards, so a second
                  review of the page comes after the first); with no such section, in the stop's section when REVIEW.md
                  was written after that page (said in the stop's note). Gate ① goes by gatecheck.py's own rule, as
                  bin/vh render and check do: a decision and the person's words in a gate ① section, and the concept
                  on record in DECISIONS.md
  skipped         Effort quick (no page of its own, and the Director line does not ask for this stop, by stop= or x=own), or
                  waived in the user's own words in REVIEW.md
  waiting_person  its page is out (bin/vh gate made it: a gate JSON not sent yet is not, nor a page whose last run bin/vh gate
                  refused, exit 1, for it sent nothing), it is this round (out/review/.current), and nothing has come back for it yet
  waiting_agent   the person submitted on the desk and no agent has it yet, or an agent has it and REVIEW.md has no
                  decision for it yet; or the project moved on past its page with no decision on record; gate ①
                  decided, but its record lacks the person's words or DECISIONS.md's concept (render and check refuse)
  in_progress     the first stop with nothing yet after the last one that has something, when all before it are done or
                  skipped: what the agent works towards
  not_started     later stops; a stop passed over without a record stays not_started
  no_record       every stop of a standard or studio project with no REVIEW.md (made before the templates had one):
                  nothing to read its review from (gatecheck.py does not check those either)
Delivery is done once bin/vh deliver has written a record, or the final film (out/final*, out/final/, a file directly in
media/, Manim's render at 1080p or more; not its 480p15 and 720p30 drafts, and not a film a failed patch left) has a passing
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
to read (a file to read whole, or a "<file.md>#<section>" that bin/vh know --show prints), and how many {…} are still unfilled in
BRIEF.md, STYLE.md and STORYBOARD.md (outside code; the template's kind of braces, not a stylesheet's). What the Director line keeps for the person (x=own) comes first in what to do, until it is on record: its stop
done or skipped, or its row in DECISIONS.md decided. The line starts "next:"; --json has it as next_step (the older "next" is
one sentence, and stays).
--json: every field (tools/desk/README.md, 给客户端的数据, has the schema; "version": 1). Exit 0, 2 when there is no project
(with --json, the error's shape: tools/jsonerr.py).
"""
import json, os, re, shlex, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "desk"))
import activity, checkrec as C, gatecheck as G, identity, jsonerr, proxy as P, review as R, versions as V   # noqa: E402,E401
import feedback as F, reader   # noqa: E402,E401

ORDER = ["1", "E0", "E1", "2", "E2", "E3", "E4", "3", "E5"]
OUT_SKIP = {"versions", "proxy"}   # out/versions (listed from its record) and out/proxy: not renders; only directly in out/
MANIM_FINAL = re.compile(r"(1080|1440|1920|2160|3840)p")   # media/videos/<scene>/1080p30: the folder is named by the height, so 1920p30 is a vertical 1080p
STATE_MARK = {"done": "✓", "skipped": "–", "waiting_person": "●", "waiting_agent": "◆", "in_progress": "…", "not_started": "·",
              "no_record": "○"}
STATE_WORDS = {"done": "done", "skipped": "skipped", "waiting_person": "waiting for you", "waiting_agent": "waiting for the agent",
               "in_progress": "in progress", "not_started": "not started", "no_record": "no record"}
LISTENING = ("desk", "gate")   # a running desk or gate --wait is someone waiting, not work being done
PLACEHOLDER = re.compile(r"(?<!\$)\{[^{}\n]*\}")
NOT_BLANK = re.compile(r"""\s*(?:(?:none)?\s*$|["']|[\w-]+\s*:)""", re.I)   # the template's {none}, and braces that hold a value: {}, {"a": 1}, {fill: #e33}
# what the next step sends an agent to read, each for bin/vh know --show (tools/ci.sh checks each is there)
R_PAGE, R_DESK, R_DIRECTOR, R_ANIMATIC, R_LONG, R_LOOKDEV, R_ROLES = (f"playbook/01-pipeline.md#{x}" for x in ("审阅页", "审阅台", "导演模式", "animatic", "长片", "look-dev", "子代理分工"))
R_RECORD = "templates/REVIEW.md"   # how a stop goes on record
R_IDEAS, R_CARDS = "playbook/12-ideation.md#3.", "playbook/12-ideation.md#7."
R_FRAMES, R_PHONE, R_SILENT, R_BUDGET = (f"playbook/02-verification.md#{x}" for x in ("各引擎的取帧命令", "手机测试", "静默失败", "预算"))
R_PURE, R_COLOUR, R_AUDIO_QA, R_FACTS, R_PITFALLS = (f"playbook/02-verification.md#{x}" for x in ("确定性", "色彩标签", "音频 QA", "事实核查", "已知的坑"))
R_SCORES, R_LAYERS, R_QUICK = "templates/TASTE_CHECKLIST.md#打分层", "playbook/02-verification.md#七层检查", "playbook/quick.md"
R_NARRATIVE, R_SOUND, R_HF, R_MANIM = "playbook/09-narrative.md#5. 长片", "playbook/04-audio.md#常用命令", "engines/README.md#HyperFrames", "engines/README.md#Manim CE"
R_CANVAS, R_HANDDRAWN, R_EDIT, R_EDITING = "engines/canvas-film/README.md", "engines/ClaudeAnimationBase/ANIMATION_GUIDE.md", "engines/EDIT.md", "engines/editing.md"
TYPE_ENGINE = {"01": "manim", "06": "manim", "02": "hf", "03": "hf", "05": "hf", "08": "hf", "09": "hf", "04": "p5", "07": "p5", "10": "canvas", "11": "canvas"}
# what a Director line can keep for the person (x=own), and the stop where playbook/01's 导演模式 table first has each
OWN_STOP = {"concept": "1", "spec": "1", "outline": "1", "style": "1", "hook": "1", "character": "E0", "theme": "E0", "voice": "E1", "script": "E1",
            "storyboard": "2", "rhythm": "2", "packaging": "3"}
READS = (R_PAGE, R_DESK, R_RECORD, R_DIRECTOR, R_ANIMATIC, R_LONG, R_LOOKDEV, R_ROLES, R_IDEAS, R_CARDS, R_FRAMES, R_PHONE, R_SILENT, R_BUDGET, R_PURE, R_COLOUR, R_AUDIO_QA, R_FACTS,
         R_PITFALLS, R_SCORES, R_LAYERS, R_QUICK, R_NARRATIVE, R_SOUND, R_HF, R_MANIM, R_CANVAS, R_HANDDRAWN, R_EDIT, R_EDITING)


def rel(project, p):
    try:
        return Path(os.path.relpath(p, project)).as_posix()
    except ValueError:
        return str(p)


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(t)) if t else None


def basics(project):
    """The project as its BRIEF says: title, type, effort (and where it comes from), Director line, review language, Spec; and its id (null until it has one)."""
    raw = reader._read(project / "BRIEF.md", [])
    brief = reader.strip_comments(raw)
    spec = {k: reader.plain(v) for k, v, _ in reader.bullets(reader.section(brief, r"^Spec", r"^规格"))}
    title = (re.search(r"^#\s+BRIEF\s*[：:]\s*(.+)$", brief, re.M) or [None, ""])[1].strip() or project.name
    m = re.search(r"video-types/(\d\d-[\w-]+)\.md", brief) or re.search(r"<!-- from (\d\d-[\w-]+)\.md -->", raw)
    effort, src = G.effort_of(project)
    return {"id": identity.id_of(project), "path": str(project), "slug": project.name, "title": title, "type": m.group(1) if m else None, "effort": effort,
            "effort_from": src, "director": spec.get("Director") or "default", "lang": R.review_lang(project) or "zh", "spec": spec}


def director_stops(director_line):
    """The checkpoints a Director line asks for: stop=E3, stop=E1,E3, and every stop= on the line (stop=E1, stop=E3)."""
    return {s.upper() for grp in re.findall(r"\bstop\s*=\s*(E[0-9](?![0-9])(?:\s*[,，]?\s*E[0-9](?![0-9]))*)", director_line or "", re.I)
            for s in re.findall(r"E[0-9]", grp, re.I)}


def director_own(director_line):
    """What a Director line keeps for the person, {thing: its stop} (None for a word playbook/01 does not name): voice=own, and
    rest=own for everything the line does not name."""
    said = {k.lower(): v.lower() for k, v in re.findall(r"(\w+)\s*=\s*(\w+)", director_line or "")}
    own = [k for k, v in said.items() if v == "own" and k != "rest"]
    if said.get("rest") == "own":
        own += [k for k in OWN_STOP if k not in said]
    return {k: OWN_STOP.get(k) for k in own}


def own_unsettled(project, proj):
    """director_own without what DECISIONS.md's table already has as decided."""
    f = project / "DECISIONS.md"
    dec = G.read(f) if f.is_file() else ""
    return {k: v for k, v in director_own(proj["director"]).items() if not G.row_decided(dec, rf"\b{re.escape(k)}\b")}


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
    sent = [p for p in pages if R.refusal(project, p.stem[5:]) is None]
    cur = R.current_page(project) or (sent[-1].stem[5:] if sent else None)
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
        elif waived or (effort == "quick" and not plist and key not in asked):
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
        elif latest is not None and R.refusal(project, pid) is not None and not pend and not handed:
            st["note"] = "bin/vh gate refused this page, so that run sent the person nothing: fix it and send it again"
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
    """Video files under out/, renders/ and media/, three levels down, newest first, with what lies beside them."""
    found = []
    for top in ("out", "renders", "media"):
        for p in P.videos_under(project / top, OUT_SKIP if top == "out" else ()):
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
    """{file: how many {…} are still in it}, comments and code aside (a stylesheet in a ``` block or between `…`); braces that hold
    a value (NOT_BLANK) are no blanks."""
    out = {}
    for name in ("BRIEF.md", "STYLE.md", "STORYBOARD.md"):
        f = project / name
        if not f.is_file():
            continue
        secs = G.sections(reader.strip_comments(G.read(f)))
        lines = [t for t, _ in secs] + [x for _, ls in secs for x, code in ls if not code]
        n = sum(1 for x in lines for b in PLACEHOLDER.findall(re.sub(r"`[^`\n]*`", "", x)) if not NOT_BLANK.match(b[1:-1]))
        if n:
            out[name] = n
    return out


def has_sound(project, proj):
    """Narration or music: something in audio/, or a narration the BRIEF's Language line names."""
    d = project / "audio"
    said = re.search(r"narration:\s*([^\s{}][^{}\n]*)", proj["spec"].get("Language") or "")
    return (d.is_dir() and any(not x.name.startswith(".") for x in d.iterdir())) or bool(said and said.group(1).strip().lower() not in ("none", "无"))


def shown(project):
    """The project as a command takes it: from the repo's root when it is under it (bin/vh runs from there), else whole."""
    try:
        return shlex.quote(project.relative_to(HERE.parent.resolve()).as_posix())
    except ValueError:
        return shlex.quote(str(project))


def engine_named(proj):
    """The engine the BRIEF's Engine line names first (a concept can change the type's own): hf, manim, p5, canvas, or other (Remotion:
    no commands here); with the line not filled in, the type's own, or None."""
    line = (proj["spec"].get("Engine") or "").lower()
    if not line or "{" in line:
        return TYPE_ENGINE.get((proj["type"] or "")[:2])
    m = re.search(r"hyperframes|manim|claudeanimationbase|p5|canvas", line)
    return {"hyperframes": "hf", "manim": "manim", "canvas": "canvas"}.get(m.group(0), "p5") if m else "other"


def engine_here(project, proj):
    """The engine this project runs on: what its files show (page: a page of its own, which bin/vh render draws), else the named one."""
    if (project / "edit.json").is_file() or (project / "film.html").is_file():
        return "canvas"
    if (project / "hyperframes.json").is_file():
        return "hf"
    if (project / "render.mjs").is_file():
        return "p5"
    return "page" if (project / "index.html").is_file() else engine_named(proj)


def hf_init(project, proj):
    m = re.search(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", proj["spec"].get("Output") or "")
    frame = {(1080, 1350): "4:5", (1080, 1440): "3:4", (1080, 1080): "square", (1920, 1080): "landscape"}.get((int(m[1]), int(m[2])) if m else None, "portrait")
    return f"bin/vh hf-init {shown(project)} {frame}"


def scaffold_todo(project, proj):
    """The command that makes an engine's scaffold the project lacks, by the engine the BRIEF names, else its type's; None when
    there is nothing to make, and for what bin/vh new leaves to the first picture (engine_setup)."""
    if (project / "film.html").is_file() or (project / "edit.json").is_file():
        return None
    engine = engine_named(proj)
    if engine == "hf" and (proj["type"] or "")[:2] != "09" and not (project / "hyperframes.json").is_file() and not (project / "index.html").is_file():
        return hf_init(project, proj)
    if engine == "p5" and (project / "render.mjs").is_file() and not (project / "node_modules").is_dir():
        return f"(cd {shown(project)} && npm install)"
    return None


def engine_setup(project, proj):
    """What bin/vh new only names and the first picture needs, when it is not done yet: Manim's project, HyperFrames in type 09."""
    engine = engine_here(project, proj)
    if engine == "manim" and not (project / "pyproject.toml").is_file():
        return f"(cd {shown(project)} && uv init --bare --python 3.12 && uv add manim)"
    if engine == "hf" and not (project / "hyperframes.json").is_file():
        return hf_init(project, proj)
    return None


def manim_quality(proj, final):
    """Manim's flags for a draft or the final. A vertical film goes by its size: -ql and -qh put the frame back to landscape
    (engines/README.md, 竖屏)."""
    m = re.search(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", proj["spec"].get("Output") or "")
    w, h = (int(m[1]), int(m[2])) if m else (1920, 1080)
    if h > w:
        return f"-r {w},{h} --fps 30" if final else f"-ql -r {w // 2},{h // 2}"
    return "-qh --fps 30" if final else "-ql"


def frame_cmd(project, proj):
    """How to look at a frame before there is a film. bin/vh frames draws a page; Manim has none, and keeps its last frame."""
    engine = engine_here(project, proj)
    if engine == "manim":
        return f"(cd {shown(project)} && uv run manim {manim_quality(proj, False)} -s scene.py <Scene>)"
    return None if engine == "other" else f"bin/vh frames {shown(project)} --at 1,5,9"


def render_cmd(project, proj, final):
    """The command that renders this project's film (out/draft.mp4 or out/final.mp4), by the engine it runs on."""
    p, name, engine = shown(project), "out/final.mp4" if final else "out/draft.mp4", engine_here(project, proj)
    if engine == "hf":
        return f"(cd {p} && HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1 npx hyperframes render --quality {'delivery' if final else 'draft'} --output {name})"
    if engine == "p5":
        return f"(cd {p} && node render.mjs --clip --out={name})"
    if engine == "manim":
        return f"(cd {p} && uv run manim {manim_quality(proj, final)} scene.py <Scene>)"
    return None if engine == "other" else f"bin/vh render {p} --out {p}/{name}"


def engine_docs(project, proj):
    """What to read for this project's engine at the first picture: its section or guide, and the edit list's where it goes through one."""
    kind = (proj["type"] or "")[:2]
    doc = {"canvas": R_CANVAS, "hf": R_HF, "p5": R_HANDDRAWN, "manim": R_MANIM}.get(engine_here(project, proj))
    return [doc, R_EDITING if kind == "09" else None, R_EDIT if kind == "11" or (project / "edit.json").is_file() else None]


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
    """A film (its path from the project) that counts as the delivery: out/final*, out/final/…, a file directly in media/, or
    Manim's render at 1080p or more; not its drafts (480p15, 720p30), and not a film a failed patch left."""
    parts = Path(path).parts
    if P.is_failed(parts[-1]):
        return False
    if parts[:2] == ("media", "videos"):   # Manim's tree: the folder says the quality, whatever the scene is called
        return bool(MANIM_FINAL.match(parts[-2]))
    return parts[-1].lower().startswith("final") or "final" in parts[:-1] or (len(parts) > 1 and parts[-2] == "media")


def next_step(project, proj, st, paused, no_record, working, desk, by_video):
    """{who, do, commands, read, unfilled}: who has the next move at the stop the project is at, and how to take it."""
    p = shown(project)
    left = unfilled(project)
    state = {x["id"]: x["state"] for x in st}
    own = {k: v for k, v in own_unsettled(project, proj).items() if state.get(v) not in ("done", "skipped")}   # what the person keeps, still open
    quick = proj["effort"] == "quick"
    doc = f"video-types/{proj['type']}.md" if proj["type"] else None
    long_film = (proj["type"] or "").startswith("10-")
    m = re.search(r"(\d+)\s*s\b", proj["spec"].get("Output") or "")
    if m and int(m.group(1)) > 180:
        long_film = True

    def out(who, do, commands=(), read=()):
        if who == "agent" and own:
            names = ", ".join(f"{k} (at {R.gate_title(v, proj['lang'])})" if v else k for k, v in own.items())
            do, read = f"the Director line keeps {names} for the person, with no record yet: options and your pick at that stop, then wait for them; {do}", [R_DIRECTOR, *read]
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
        return out("agent", busy + "the engine's scaffold is not there: this makes it", [todo], [R_HF] if "hf-init" in todo else [])
    if s["state"] == "waiting_agent":
        fb = s["feedback"] or {}
        if fb.get("pending"):
            return out("agent", busy + f"read the person's submission for {s['name']}, then write what was decided into REVIEW.md", [f"bin/vh desk feedback {p}"], [R_DESK])
        if fb.get("handed"):
            return out("agent", busy + f"write what was decided and changed under the desk's section for {s['name']} in REVIEW.md (定了 / 改了)", [], [R_DESK])
        return out("agent", busy + (s["note"] or f"record the decision for {s['name']} in REVIEW.md"), [], [R_RECORD])
    key = s["id"]
    mine = ", ".join(k for k, v in own.items() if v == key)   # what the person keeps at this stop
    pid = Path(s["page"]).stem[5:] if s["page"] else key
    refused = R.refusal(project, pid)
    if refused is not None:
        return out("agent", busy + f"bin/vh gate refused the page for {s['name']}, so the person got nothing: fix it ({'; '.join(refused[:3])}), then send it again", [f"bin/vh gate {p} {pid}"], [R_PAGE])
    film, fstate, fails = film_state(project, by_video)
    check = [f"bin/vh check {p}"]
    # what the scenes need to be right: the sections of 02 after the frame commands (quick reads less: playbook/quick.md)
    writing = [] if quick else [R_PURE, R_SILENT, R_COLOUR, R_AUDIO_QA if has_sound(project, proj) else None, R_FACTS, R_PITFALLS,
                                R_ROLES if long_film or proj["effort"] == "studio" else None]
    also = P.film_of(project)[1]
    named = film and film + (f" (also here: {P.also_here(project, also)})" if also else "")   # the film in a sentence

    def fill(what):
        """what, with the {…} the files it names still have in front of it."""
        return ", ".join(f"fill {n} ({left[n]} {{…}} left)" for n in what if n in left)

    def first_scenes():
        """What the first picture is made of: an edit list for a recap, or a cut, with no edit.json yet; else scenes."""
        kind = (proj["type"] or "")[:2]
        if kind in ("09", "11") and not (project / "edit.json").is_file():
            return ("write the cut as edit.json" if kind == "09" else "write the photos and clips in their order as edit.json") + " (engines/EDIT.md), look at its frames, then render a draft"
        return "write the scenes, look at their frames, then render a draft"

    def page():
        """The gate JSON's state: what to say about it, and the commands that send it."""
        f = project / "out" / "review" / f"gate-{key}.json"
        send = f"bin/vh gate {p} {key}"
        try:
            n = len(R.placeholders(json.loads(f.read_text(encoding="utf-8-sig")))) if f.is_file() else None
        except (OSError, ValueError):
            n = None
        if n:
            return f"fill out/review/gate-{key}.json ({n} placeholders left), then send it", [send]
        return (f"send the page for {s['name']}", [send]) if f.is_file() else (f"then the page for {s['name']}", [f"bin/vh gate {p} {key} --init", send])
    if key == "1":
        say, cmds = page()
        own_only = quick and mine and "concept" not in own   # quick's concept is the agent's: a page only for what the person kept
        return out("agent", busy + "; ".join(x for x in (fill(["BRIEF.md"]), f"NOTES.md's material first, your own concept (a quick film's), then options for {mine} with a frame each" if own_only
                                                         else "NOTES.md's material first, then 2–3 concept cards with a frame each and the outline", say) if x),
                   cmds, [R_QUICK, f"{doc}#工作流" if doc else None, f"{doc}#禁止" if doc else None] * quick + [None if quick else doc, R_IDEAS, R_CARDS, R_PAGE, R_DESK if proj["effort"] == "studio" else None, R_FRAMES])
    if key == "2":
        say, cmds = page()
        return out("agent", busy + "; ".join(x for x in (fill(["STYLE.md", "STORYBOARD.md"]), "the shots in shots.json, then their key frames and the rhythm chart", say) if x),
                   [f"bin/vh storyboard {p}", f"bin/vh rhythm {p}"] + cmds, [R_PAGE, R_ANIMATIC, R_LOOKDEV if proj["effort"] == "studio" else None, R_FRAMES, R_LONG if long_film else None, R_NARRATIVE if long_film else None])
    if key == "3":
        if fstate == "none":
            return out("agent", busy + "; ".join(x for x in (fill(["BRIEF.md"]) if quick else "", first_scenes()) if x),
                       [engine_setup(project, proj), frame_cmd(project, proj), render_cmd(project, proj, False)],
                       [*engine_docs(project, proj), R_FRAMES, *writing, R_LONG if long_film else None])
        if fstate in ("unchecked", "stale"):
            return out("agent", busy + f"check {named} and look at its contact sheet", check + [f"bin/vh sheet {p}/{film}"], [R_BUDGET, R_FRAMES, R_PHONE, R_SILENT])
        if fstate == "failed":
            return out("agent", busy + f"fix what bin/vh check failed on {film}" + (": " + "; ".join(fails) if fails else ""), check, [R_SILENT])
        say, cmds = page()
        if quick:   # no reviewer here: only what the person kept
            return out("agent", busy + f"put {mine or 'what they asked to see'} to the person beside {film}; {say}", cmds, [R_PAGE])
        return out("agent", busy + f"a fresh reviewer scores {film}, fix the worst of it (at most 3 places), write down the 2–3 places you like least; {say}", cmds, [R_SCORES, R_LAYERS, R_PAGE])
    if s["kind"] != "deliver":
        say, cmds = page()
        return out("agent", busy + f"prepare {s['name']}{f' for {mine}' if mine else ''}, a stop the director mode asks for; {say}", cmds, [R_DIRECTOR, R_LOOKDEV if key == "E0" else None, R_PAGE])
    # delivery: quick's whole path, and the end of the others'
    if fstate == "none":
        return out("agent", busy + "; ".join(x for x in (fill(["BRIEF.md"]), f"a short storyboard table, then {first_scenes()}" if quick else "render the final") if x),
                   [engine_setup(project, proj), render_cmd(project, proj, not quick)],
                   [R_QUICK, f"{doc}#工作流" if doc else None, f"{doc}#禁止" if doc else None, *engine_docs(project, proj), R_PHONE] if quick else [*engine_docs(project, proj), R_FRAMES, *writing])
    if fstate in ("unchecked", "stale"):
        return out("agent", busy + f"check {named}" + (" and look at its contact sheet" if not is_final(film) else ""),
                   check + ([f"bin/vh sheet {p}/{film}"] if not is_final(film) else []), [R_PHONE] if quick else [])
    if fstate == "failed":
        return out("agent", busy + f"fix what bin/vh check failed on {film}" + (": " + "; ".join(fails) if fails else ""), check, [R_SILENT])
    if not is_final(film):
        manim = engine_here(project, proj) == "manim"   # its film lands in media/videos/<scene>/1080p30/, by the scene's name
        return out("agent", busy + (f"this is Manim's draft: render it at high quality ({manim_quality(proj, True).split(' --')[0]})" if manim else "render the final at delivery quality")
                   + ", put the sound on when it has any (bin/vh mix, qa, mux), and check it",
                   [render_cmd(project, proj, True), f"bin/vh check {p}" if manim else f"bin/vh check {p}/out/final.mp4"], [R_SOUND])
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
            jsonerr.mark("no_project")
            return 2
        if not (project / "BRIEF.md").is_file():
            return jsonerr.fail("no_project", f"status: {project} is not a project (no BRIEF.md)")
    out = collect(project)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    show(out, time.time())
    return 0


def collect(project, now=None, light=False):
    """Everything bin/vh status says of a project, as its --json. Reads only, prints nothing. light leaves out what a list of
    projects does not show and that takes the most on a large project: the asset ledger, the cast and the research (null)."""
    now = time.time() if now is None else now
    proj = basics(project)
    rv = project / "REVIEW.md"
    review_text = G.strip_comments(G.read(rv)) if rv.is_file() else ""
    review_mtime = rv.stat().st_mtime if rv.is_file() else 0
    no_record = not rv.is_file() and proj["effort"] != "quick"   # made before the templates had one: nothing to read
    paused = reader._history(review_text)[1] if review_text else False
    asked = director_stops(proj["director"]) | {v for v in own_unsettled(project, proj).values() if v}
    st, cur = stops(project, review_text, review_mtime, proj["effort"], asked, proj["lang"], no_record)
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
    finals = [(v, s) for v, s in vids if is_final(rel(project, v))]
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
    assets = cast = research = None
    if not light:
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
           "next_step": None}
    try:   # not the command that asks (bin/vh new); what cannot be worked out is said, never a failure of status
        out["next_step"] = next_step(project, proj, st, paused, no_record, [r for r in working if r.get("run") != os.environ.get("OVH_ACTIVITY_RUN")], desk, by_video)
    except Exception as e:
        out["next_step"] = {"who": "unknown", "do": f"the next step could not be worked out ({e})", "commands": [], "read": [], "unfilled": {}}
    return out


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
        print("  read: " + " · ".join(n["read"]) + "  (with a #section: bin/vh know --show \"<file>#<section>\" prints it; without: the whole file)")
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
    sc, hot, refs, web = rs.get("scout") or {}, rs.get("hot") or {}, rs.get("refs") or {}, rs.get("web") or {}
    bits = [x for x in (
        f"{sc['records']} scout record{'s' if sc['records'] != 1 else ''} ({sc['latest']} looked at"
        + (f", {sc['films']} your own" if sc.get("films") else "") + ")" if sc.get("records") else "",
        f"hot lists on {hot['days']} day{'s' if hot['days'] != 1 else ''} (the last {hot['last']})" if hot.get("days") else "",
        f"{refs['records']} reference{'s' if refs['records'] != 1 else ''}" if refs.get("records") else "",
        f"{web['records']} web page{'s' if web['records'] != 1 else ''} kept" if web.get("records") else "",
        refs.get("error") or "", web.get("error") or "", rs.get("error") or "") if x]
    if bits:
        print("research: " + " · ".join(bits) + " (bin/vh scout, bin/vh ref, bin/vh web)")
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
        sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))
    except BrokenPipeError:
        sys.exit(0)
