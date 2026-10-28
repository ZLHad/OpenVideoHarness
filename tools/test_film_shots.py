"""Real page/CLI regressions for the shot registry and its two consumers (Chrome + uv/Pillow)."""
import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FilmShotsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="vh-film-shots-")
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name) / "project"
        shutil.copytree(ROOT / "engines/canvas-film/template", self.p)
        html = self.p / "film.html"
        html.write_text(re.sub(r"@font-face\s*\{[^}]*\}", "", html.read_text()))
        (self.p / "src/50-shots.js").write_text('''Object.assign(FILM, {width:320,height:180,lead:0.5,tail:1,
grain:0,fadeOut:0,images:{}});
const CHAPTERS=[{at:0,title:'Opening'},{at:'@next',title:'Body'}];
function paint(t,s){rect(0,0,W,H,{fill:s.id==='S01'?'#ee2222':'#2222ee'});}
const SHOTS=[{id:'S01',at:0,see:'First idea',draw:paint},
{id:'S04a',at:'@next',tin:['dim',0.3],see:'Fallback idea',reads:['Actual idea'],label:'Detail',unsure:'check timing',
 camera:{size:'medium-close',angle:'low',move:'push-in'},draw:paint},
{id:'tail/odd',at:'@tail',segment:'Ending',see:'Last idea',draw:paint}];''')
        self.write_timeline(0)

    def write_timeline(self, shift):
        (self.p / "audio/timeline.zh.json").write_text(json.dumps({"duration": 7 + shift, "segments": [
            {"id": "next", "start": 2 + shift, "end": 4 + shift, "text": "Next"},
            {"id": "tail", "start": 5 + shift, "end": 7 + shift, "text": "Tail"}]}))

    def vh(self, *args, code=0):
        r = subprocess.run([os.environ.get("VH_BASH", "bash"), str(ROOT / "bin/vh"), *map(str, args)],
                           capture_output=True, text=True, timeout=100)
        self.assertEqual(r.returncode, code, r.stdout + r.stderr)
        return r.stdout + r.stderr

    def review_shots(self, out):
        review = json.loads((out / "review.json").read_text())
        return [s for segment in review["segments"] for s in segment["shots"]]

    def assert_same_picture(self, a, b):
        """Two captures of one page: GitHub's macOS runner does not rasterise it to the same bytes twice, so the same
        picture is a PSNR of 45 dB or more (CLAUDE.md, hard rule 1), measured with ffmpeg when the bytes differ."""
        if a.read_bytes() == b.read_bytes():
            return
        if not shutil.which("ffmpeg"):
            self.fail(f"{a.name} differs between the two runs (no ffmpeg to say by how much)")
        r = subprocess.run(["ffmpeg", "-v", "info", "-nostdin", "-i", str(a), "-i", str(b), "-lavfi", "[0:v]format=rgb24[a];[1:v]format=rgb24[b];[a][b]psnr",
                            "-f", "null", "-"], capture_output=True, text=True, timeout=60)
        m = re.findall(r"average:(inf|[\d.]+)", r.stderr)
        self.assertTrue(m, f"no PSNR between the two runs' {a.name}: {r.stderr[-400:]}")
        self.assertTrue(m[-1] == "inf" or float(m[-1]) >= 45, f"the two runs' {a.name} are {m[-1]} dB apart (under 45)")

    def test_live_times_ids_metadata_frames_and_timeline_edit(self):
        out = self.p / "out/check/storyboard"
        log = self.vh("storyboard", self.p, "--lang", "en")
        self.assertIn("window.film.shots", log)
        self.assertIn("window.film.frame", log)
        shots = self.review_shots(out)
        self.assertEqual([s["id"] for s in shots], ["S01", "S04a", "tail/odd"])
        self.assertEqual([(s["t0"], s["t1"]) for s in shots], [(0, 2.5), (2.5, 5.5), (5.5, 8.5)])
        self.assertEqual(shots[1]["see"], "Detail / Actual idea")
        # a shot's camera from SHOTS through window.film.shots: printed by the cards' codes, kept as codes in review.json
        self.assertEqual((shots[1].get("camera"), shots[1].get("camera_codes")), ("MCU · low · push-in", {"size": "MCU", "angle": "low", "move": "push-in"}))
        self.assertNotIn("camera", shots[0])
        self.assertEqual(json.loads((out / "index.json").read_text())["shot_source"], "film.html (window.film.shots)")
        frames = [(self.p / s["frame"]).read_bytes() for s in shots]
        self.assertTrue(all(f.startswith(b"\x89PNG") for f in frames))
        self.assertNotEqual(frames[0], frames[1])
        self.assertFalse((self.p / "shots.json").exists())
        before = (out / "overview.png").read_bytes()
        self.vh("storyboard", self.p, "--lang", "en")
        self.assertEqual(before, (out / "overview.png").read_bytes())
        log = self.vh("rhythm", self.p, "--segment", "Body", "--lang", "en")
        self.assertIn("2.5–5.5", log)
        self.assertIn("film.html (window.film.shots)", log)
        if shutil.which("ffmpeg"):
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=green:s=320x180:r=1:d=10",
                            "-c:v", "libx264", "-y", str(self.p / "out/final.mp4")], check=True)
            log = self.vh("storyboard", self.p, "--lang", "en")
            self.assertIn("frames from out/final.mp4", log)
        self.write_timeline(1)
        self.assertIn("window.film.frame", self.vh("storyboard", self.p, "--snapshot", "--at", "1", "--lang", "en"))
        self.assertEqual([(s["t0"], s["t1"]) for s in self.review_shots(out)], [(0, 3.5), (3.5, 6.5), (6.5, 9.5)])
        self.assertIn("3.5–6.5", self.vh("rhythm", self.p, "--segment", "Body", "--lang", "en"))

    def test_manual_precedence_does_not_open_browser_or_overwrite(self):
        (self.p / "film.html").write_text("broken page, should never be loaded")
        frame = self.p / "manual.png"
        frame.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aB1kAAAAASUVORK5CYII="))
        manual = self.p / "shots.json"
        manual.write_text(json.dumps([{"id": "manual", "start": 0, "end": 2, "frame": "manual.png"}]))
        original = manual.read_bytes()
        alternate = self.p / "alternate.json"
        alternate.write_text(original.decode().replace('"manual"', '"alternate"'))
        self.vh("storyboard", self.p, "--browser", "/no/chrome", "--lang", "en")
        self.assertEqual(self.review_shots(self.p / "out/check/storyboard")[0]["id"], "manual")
        for command in ("storyboard", "rhythm"):
            log = self.vh(command, self.p, "--shots", "alternate.json", "--browser", "/no/chrome", "--lang", "en")
            self.assertIn("alternate.json", log)
        self.assertEqual(self.review_shots(self.p / "out/check/storyboard")[0]["id"], "alternate")
        self.assertEqual(manual.read_bytes(), original)

    def test_explicit_page_and_concurrent_outputs(self):
        page = self.p / "other.html"
        page.write_text('''<canvas id="c" width="320" height="180"></canvas><script>
window.film={width:320,height:180,duration:2,shots(){return [{id:'explicit',start:0,end:2,reads:'Page'}]},
frame(){const x=document.getElementById('c').getContext('2d');x.fillStyle='green';x.fillRect(0,0,320,180)}};
</script>''')
        (self.p / "shots.json").write_text("invalid, explicit page wins")
        with ThreadPoolExecutor(max_workers=2) as pool:
            jobs = [pool.submit(self.vh, "storyboard", self.p, "--shots", "other.html", "--out", self.p / f"out/run{i}", "--lang", "en") for i in range(2)]
            for job in jobs:
                self.assertIn("other.html (window.film.shots)", job.result())
        self.assertEqual(self.review_shots(self.p / "out/run0")[0]["id"], "explicit")
        self.assert_same_picture(self.p / "out/run0/frames/explicit.png", self.p / "out/run1/frames/explicit.png")
        self.assertIn("other.html", self.vh("rhythm", self.p, "--shots", "other.html", "--lang", "en"))

    def test_manual_shots_can_capture_without_reading_unused_live_registry(self):
        (self.p / "shots.json").write_text('[{"id":"manual","start":0,"end":2}]')
        (self.p / "film.html").write_text('''<canvas id="c" width="320" height="180"></canvas><script>
window.film={width:320,height:180,duration:2,get shots(){throw new Error('unused registry')},
frame(){document.getElementById('c').getContext('2d').fillRect(0,0,320,180)}};</script>''')
        self.assertIn("window.film.frame", self.vh("storyboard", self.p, "--snapshot", "--lang", "en"))
        self.assertEqual(self.review_shots(self.p / "out/check/storyboard")[0]["id"], "manual")

    def test_invalid_or_failed_live_registry_is_not_silently_skipped(self):
        page = self.p / "film.html"
        for body, message in [
            ("shots:{bad:true}", "must be an array"),
            ("shots:[]", "empty"),
            ("shots:[{id:'x',start:0,end:2},{id:'x',start:2,end:4}]", "used twice"),
            ("shots:[{id:'x',start:0,end:NaN}]", "needs start and end"),
            ("ready:Promise.reject(new Error('broken ready'))", "broken ready"),
        ]:
            page.write_text(f"<script>window.film={{frame(){{}},duration:5,{body}}};</script>")
            for command in ("storyboard", "rhythm"):
                self.assertIn(message, self.vh(command, self.p, code=1))
        page.write_text("<script>window.film={frame(){},duration:5};</script>")
        self.assertIn("no window.film.shots", self.vh("storyboard", self.p, code=1))
        self.vh("rhythm", self.p)  # absent optional registry leaves the narration lane
        page.write_text("<img src='missing.png'><script>window.film={frame(){},duration:5,shots:[{start:0,end:5}]};</script>")
        self.assertIn("missing.png", self.vh("rhythm", self.p, code=1))
        page.write_text("<script>window.film={frame(){throw new Error('broken frame')},duration:5,shots:[{start:0,end:5}]};</script>")
        self.assertIn("broken frame", self.vh("storyboard", self.p, code=1))
        self.assertEqual(list((self.p / "out/check/storyboard/frames").glob("*.png")), [])


if __name__ == "__main__":
    unittest.main()
