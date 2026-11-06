"""A failure a program can read. Stdlib only.

With --json among a command's arguments, a failure prints {"version": 1, "error": {"code", "message", "hint"}} on stdout (one
line); the line a person reads stays on stderr, and the exit status is what it was. Under a logged command (bin/vh hands the
run over in OVH_ACTIVITY_*) the message also goes into the project's activity log, as a note with "level": "error" and
"code", so bin/vh activity can say why a run failed, with or without --json. bin/vh does the same for what fails before
Python starts (vh_fail). The record and the note hold the message as activity.scrub writes it, since it may repeat what was typed: a
key given to the wrong option is … there (bin/vh's act_scrub, by the same rules), and only stderr has the words as they were.

The codes are stable; a client branches on them, not on the words:
  usage         the arguments are wrong (exit 2)
  no_project    no project at that path or name, or the folder is none
  not_found     the project is there; a file, film, version or run it names is not
  invalid       a file is there and cannot be read as what it should be: not JSON, not its schema, placeholders left
  exists        what it would make is there already
  refused       a rule says no: a page that breaks one, a render before gate ① is on record
  missing_tool  a program it needs is not installed (the hint says which way to get it)
  timeout       it waited as long as it was told to
  failed        anything else that went wrong while it worked (exit 1 as a rule)
A record the command prints of its own stays as it is: bin/vh check --json on a film it cannot read, bin/vh doctor --json
with no python3 (their "error" is a string: a verdict of the record, not this shape), a list or a check that exits 1 with
its findings.

In a tool:  sys.exit(jsonerr.guard(lambda: main(sys.argv[1:])))   nothing else is needed for a failure to have this shape:
what exits non-zero with nothing on stdout says its last stderr line, code usage on exit 2, else failed; a usage error from
argparse, a SystemExit with words and a traceback all count. A site that knows better says so: return jsonerr.fail(code,
message, hint) prints the line and reports it; jsonerr.mark(code, hint) names the failure whose words another function
prints; jsonerr.report(code, message, hint) when the lines are printed already. Exits of 128 and up (a signal) say nothing.
"""
import json, sys, traceback

HINTS = {"usage": "bin/vh <command> -h prints its usage", "no_project": "bin/vh projects lists the projects"}
TAIL = 2000   # characters of stderr kept for the message
_said = _forced = False
_mark = None
_out = None   # guard's stdout: what was printed on it


def force():
    """This command speaks JSON whatever its arguments (bin/vh desk data): a failure is JSON too."""
    global _forced
    _forced = True


def wanted(argv=None):
    return _forced or "--json" in (sys.argv[1:] if argv is None else argv)


def record(code, message, hint=None):
    return {"version": 1, "error": {"code": code, "message": message, "hint": hint if hint is not None else HINTS.get(code)}}


def _note(code, message):
    try:
        import activity
        activity.note(message, level="error", code=code)
    except Exception:   # the failure is said all the same
        pass


def report(code, message, hint=None):
    """The failure on record, once a run: JSON on stdout with --json (unless a record is out already), a note in the log. The
    line a person reads is the caller's."""
    global _said
    if _said:
        return
    _said = True
    try:
        import activity
        message = activity.scrub(activity._text(str(message)))   # a raw byte in a path: \\xNN, so it prints anywhere; a key typed by mistake: …, here and in the log
        hint = activity.scrub(activity._text(str(hint))) if hint is not None else None
    except Exception:
        message = str(message)
    _note(code, message)
    if wanted() and not (_out is not None and _out.count):
        print(json.dumps(record(code, message, hint), ensure_ascii=False), flush=True)


def fail(code, message, hint=None, rc=2):
    """Say a failure: the line on stderr, the record. → rc, for a return."""
    print(message, file=sys.stderr, flush=True)
    report(code, message, hint)
    return rc


def mark(code, hint=None):
    """What the failure now coming is: its words are printed by another function (review.find_project)."""
    global _mark
    _mark = (code, hint)


def project_arg(word, tool):
    """The project a command's argument names: a folder, a file inside one, or a name under $OVH_PROJECTS / projects/. None when there is
    none, the failure said (no_project): the caller returns 2."""
    from pathlib import Path
    import gatecheck, review
    p = Path(word).expanduser()
    project = gatecheck.project_of(p) if p.exists() else None
    if project is not None:
        return project
    project = review.find_project(word)   # (it says why, on stderr)
    if project is None:
        mark("no_project")
        return None
    if not (project / "BRIEF.md").is_file():
        fail("no_project", f"{tool}: {project} is not a project (no BRIEF.md)")
        return None
    return project


class _Through:
    """A stream that goes on to the real one (isatty, encoding, buffer and the rest too) and remembers what passed."""

    def __init__(self, real):
        self.real, self.count, self.tail = real, 0, ""

    def write(self, s):
        self.count += len(s)
        self.tail = (self.tail + s)[-TAIL:]
        return self.real.write(s)

    def flush(self):
        self.real.flush()

    def __getattr__(self, name):
        return getattr(self.real, name)


def _exit_status(code):
    if code is None:
        return 0
    if isinstance(code, int):
        return int(code)
    print(code, file=sys.stderr)   # as the interpreter does with sys.exit("words")
    return 1


def guard(main):
    """main() (→ an exit status) with a net: a failure that said nothing of its own gets its record. → the exit status."""
    global _out
    err, out = _Through(sys.stderr), _Through(sys.stdout)
    real = sys.stderr, sys.stdout
    sys.stderr, sys.stdout, _out = err, out, out
    try:
        try:
            rc = _exit_status(main())
        except SystemExit as e:
            rc = _exit_status(e.code)
        except BrokenPipeError:   # a closed pipe goes on (bin/vh … | head), and so does KeyboardInterrupt: each tool has its way with those
            raise
        except Exception:
            traceback.print_exc()
            rc = 1
        if 0 < rc < 128 and not _said:
            line = next((x.strip() for x in reversed(err.tail.splitlines()) if x.strip()), "")
            code, hint = _mark or ("usage" if rc == 2 else "failed", None)
            if line or (wanted() and not out.count):
                report(code, line or f"exit {rc}", hint)
        return rc
    finally:
        sys.stderr, sys.stdout = real
        _out = None
