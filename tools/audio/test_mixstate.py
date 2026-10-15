"""Small real-media regressions for mix validity, run by tools/ci.sh (ffmpeg only)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from mixstate import Build, InvalidMix, record_path, verified

ROOT = Path(__file__).resolve().parents[2]


class MixBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="vh-mix-test-")
        self.addCleanup(self.tmp.cleanup)
        self.p = Path(self.tmp.name)
        self.voice = self.p / "source.wav"
        self.mix = self.p / "mix.wav"
        self.video = self.p / "picture.mp4"
        self.out = self.p / "result.mp4"
        self.tone(self.voice, 2)
        self.run_ok("ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi", "-i", "color=s=64x64:r=30:d=2", "-pix_fmt", "yuv420p", str(self.video))

    def run_ok(self, *cmd):
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def tone(self, path, length, frequency=440):
        self.run_ok("ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi", "-i", f"sine=frequency={frequency}:duration={length}", str(path))

    def build(self):
        self.run_ok(sys.executable, str(ROOT / "tools/audio/mix.py"), str(self.mix), f"voice={self.voice}")

    def mux(self, *flags):
        return subprocess.run([os.environ.get("VH_BASH", "bash"), str(ROOT / "bin/vh"), "mux", str(self.video), str(self.mix), str(self.out), *flags],
                              capture_output=True, text=True)

    def test_failed_attempt_keeps_audio_but_mux_refuses_it(self):
        self.build()
        old = self.mix.read_bytes()
        self.out.write_bytes(b"previous video")
        bad = subprocess.run([sys.executable, str(ROOT / "tools/audio/mix.py"), str(self.mix), "bad_parameter=1"], capture_output=True, text=True)
        self.assertNotEqual(bad.returncode, 0)
        self.assertEqual(self.mix.read_bytes(), old)
        self.assertEqual(json.loads(record_path(self.mix).read_text())["status"], "failed")
        r = self.mux("--allow-short", "--allow-long")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("latest mix is failed", r.stderr)
        self.assertEqual(self.out.read_bytes(), b"previous video")
        self.build()
        self.assertEqual(self.mux().returncode, 0)
        self.assertNotEqual(self.out.read_bytes(), b"previous video")

    def test_same_duration_input_change_is_stale(self):
        self.build()
        self.tone(self.voice, 2, 880)
        r = self.mux()
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("input changed", r.stderr)
        self.assertFalse(self.out.exists())

    @unittest.skipUnless(shutil.which("uv"), "profile mix needs uv (numpy/scipy)")
    def test_unsupported_ding_pitch_does_not_reuse_a_previous_profile_mix(self):
        events = self.p / "events.json"
        stems = self.p / "stems"
        events.write_text('[{"t":0.5,"sfx":"ding"}]')
        cmd = [os.environ.get("VH_BASH", "bash"), str(ROOT / "bin/vh"), "mix", str(self.mix),
               "profile=promo", f"music={self.voice}", f"events={events}", f"stems={stems}", "dur=2"]
        self.run_ok(*cmd)
        meta = json.loads((stems / "meta.json").read_text())
        self.assertEqual((stems / meta["mix"]).resolve(), self.mix.resolve())
        self.assertEqual(self.mux().returncode, 0)
        old = self.mix.read_bytes()
        events.write_text('[{"t":0.5,"sfx":"ding","pitch":3}]')
        r = subprocess.run(cmd, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("pitch", r.stderr)
        self.assertEqual(self.mix.read_bytes(), old)
        self.assertIn("latest mix is failed", self.mux().stderr)

    def test_output_change_and_corrupt_record_are_refused(self):
        self.build()
        self.tone(self.mix, 2, 880)
        self.assertIn("audio changed", self.mux().stderr)
        record_path(self.mix).write_text("{")
        self.assertIn("cannot verify", self.mux().stderr)

    def test_mux_failure_preserves_output_and_subtitles_can_start_off(self):
        self.build()
        self.out.write_bytes(b"previous video")
        self.assertNotEqual(self.mux(str(self.p / "missing.srt")).returncode, 0)
        self.assertEqual(self.out.read_bytes(), b"previous video")
        sub = self.p / "captions.en.srt"
        sub.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello\n")
        r = self.mux(str(sub), "--subs-off")
        self.assertEqual(r.returncode, 0, r.stderr)
        info = self.run_ok("ffprobe", "-v", "error", "-show_streams", "-of", "json", str(self.out))
        tracks = json.loads(info.stdout)["streams"]
        self.assertEqual([s["disposition"]["default"] for s in tracks if s["codec_type"] == "subtitle"], [0])
        for s in tracks:
            if s["codec_type"] in ("audio", "video"):
                self.assertAlmostEqual(float(s["duration"]), 2, delta=0.05)

    def test_explicit_duration_changes_and_untracked_audio(self):
        self.tone(self.mix, 0.5)
        self.assertIn("--allow-short", self.mux().stderr)
        self.assertFalse(self.out.exists())
        r = self.mux("--allow-short")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("source freshness not verified", r.stdout)
        self.tone(self.mix, 3)
        self.assertIn("--allow-long", self.mux().stderr)
        self.assertEqual(self.mux("--allow-long").returncode, 0)
        self.tone(self.mix, 1.98)
        self.assertEqual(self.mux().returncode, 0)  # codec/frame rounding inside the tolerance

    def test_interrupted_build_and_input_edit_leave_previous_audio(self):
        self.mix.write_bytes(b"previous audio")
        with self.assertRaises(InvalidMix):
            with Build(self.mix, [f"voice={self.voice}"]) as b:
                b.snapshot({"voice": str(self.voice)})
                Path(b.temp).write_bytes(b"new audio")
                self.tone(self.voice, 2, 880)
                b.commit()
        self.assertEqual(self.mix.read_bytes(), b"previous audio")
        self.assertIn("latest mix is failed", self.mux().stderr)
        self.assertFalse(list(self.p.glob(".mix.mix-*")))

    def test_in_progress_and_concurrent_builds_are_refused(self):
        with Build(self.mix, [f"voice={self.voice}"]) as b:
            b.snapshot({"voice": str(self.voice)})
            with self.assertRaises(InvalidMix):
                with Build(self.mix, []):
                    pass
            self.assertIn("another mix or mux", self.mux().stderr)
        state = json.loads(record_path(self.mix).read_text())
        state["status"] = "building"  # the durable marker left by a killed producer
        record_path(self.mix).write_text(json.dumps(state))
        self.assertIn("latest mix is building", self.mux().stderr)

    def test_changes_during_mux_are_refused_before_publishing(self):
        self.build()
        with self.assertRaisesRegex(InvalidMix, "input changed"):
            with verified(self.mix):
                self.tone(self.voice, 2, 880)
        record_path(self.mix).unlink()
        with self.assertRaisesRegex(InvalidMix, "build started during mux"):
            with verified(self.mix):
                self.build()

    def test_custom_recordings_and_symlink_retargets_are_dependencies(self):
        recording = self.p / "tap.wav"
        self.tone(recording, 0.3)
        events = self.p / "events.json"
        events.write_text(json.dumps([{"t": 0, "sfx": "tap.wav"}]))
        with Build(self.mix, [f"events={events}"]) as b:
            b.snapshot({"events": str(events), "root": str(self.p)})
            shutil.copyfile(self.voice, b.temp)
            b.commit()
        self.assertEqual(self.mux().returncode, 0)
        self.tone(recording, 0.3, 880)
        self.assertIn("input changed", self.mux().stderr)
        link = self.p / "voice-link.wav"
        link.symlink_to(self.voice)
        with Build(self.mix, [f"voice={link}"]) as b:
            b.snapshot({"voice": str(link)})
            shutil.copyfile(link, b.temp)
            b.commit()
        link.unlink()
        link.symlink_to(recording)
        with self.assertRaises(InvalidMix):
            with verified(self.mix):
                pass


if __name__ == "__main__":
    unittest.main()
