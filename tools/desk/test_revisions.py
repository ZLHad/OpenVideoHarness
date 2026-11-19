"""Exercise the revision command with an audio-only edit and an actual saved submission."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
import feedback
import revisions
import schemalite


def run(*args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=True,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}).stdout


def save(project, target, state, text):
    return feedback.save(project, feedback.validate(project, {
        "round": "notes", "items": [{"target": target, "status": state, "text": text}],
    }))


def test():
    with tempfile.TemporaryDirectory(prefix="vh-revision-") as d:
        project = Path(d).resolve()
        (project / "out").mkdir()
        (project / "BRIEF.md").write_text("# Voice cut\n\n- Effort: quick\n", encoding="utf-8")
        source = [project / "out" / name for name in ("draft.mp4", "after.mp4")]
        for film, hz in zip(source, (300, 450)):
            run("ffmpeg", "-nostdin", "-loglevel", "error", "-f", "lavfi", "-i", "color=black:size=160x90:rate=24",
                "-f", "lavfi", "-i", f"sine=frequency={hz}", "-t", "2", "-c:v", "libx264", "-c:a", "aac", str(film))
        note = save(project, "range:0.25-1.75", "change", "把这句旁白换掉。")
        cmd = (str(ROOT / "bin/vh"), "desk", "revision", str(project), note.name,
               "--before", "out/draft.mp4", "--after", "out/after.mp4", "--json")
        record = json.loads(run(*cmd))
        assert not schemalite.problems(schemalite.load(ROOT / "tools/schemas/review-revision.schema.json"), record)
        wrong = subprocess.run((*cmd, "--span", "0-9"), cwd=ROOT, text=True, capture_output=True)
        assert wrong.returncode == 1
        assert not schemalite.problems(schemalite.load(ROOT / "tools/schemas/output/error.schema.json"), json.loads(wrong.stdout))
        assert record == json.loads(run(*cmd))
        assert record["text"] == "把这句旁白换掉。" and record["span"] == [0.25, 1.75]
        assert record["feedback"] == note.relative_to(project).as_posix()
        for cut, film in zip(("before", "after"), source):
            data = film.read_bytes()
            assert record[cut]["audio"] and record[cut]["sha256"] == hashlib.sha256(data).hexdigest()
            assert (project / record[cut]["file"]).read_bytes() == data

        source[0].write_bytes(b"Another render replaced the original path")
        pending, = revisions.listing(project)
        assert pending["state"] == "pending" and pending["available"]
        reply_target = "revision:" + record["id"]
        note2 = save(project, reply_target, "change", "第二个版本再慢一点。")
        assert revisions.listing(project)[0]["state"] == "changes_requested"
        assert revisions.listing(project)[0]["reply"]["text"] == "第二个版本再慢一点。"
        again = revisions.publish(project, note2.name, 1, record["after"]["file"], record["before"]["file"])
        assert again["span"] == record["span"]
        assert len(list((project / revisions.DIRECTORY / "media").glob("*.mp4"))) == 2
        save(project, "revision:" + again["id"], "ok", "")
        status = json.loads(run(str(ROOT / "bin/vh"), "status", str(project), "--json"))
        assert {r["state"] for r in status["review"]["revisions"]} == {"approved", "changes_requested"}
        assert all("/revisions/" not in r["path"] for r in status["renders"])
        with (project / again["before"]["file"]).open("ab") as f:
            f.write(b"other bytes")
        assert not revisions.can_review(project, again["id"])
        assert not next(r for r in revisions.listing(project) if r["id"] == again["id"])["available"]
        assert not revisions.can_review(project, "missing")


if __name__ == "__main__":
    test()
    print("Saved range, voiced cuts, retries, original replaced, follow-up states and replaced snapshots")
