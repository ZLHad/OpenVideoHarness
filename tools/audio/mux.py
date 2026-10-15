"""Mux the picture and checked audio, making deliberate duration changes explicit."""
import argparse
import json
import math
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

from mixstate import InvalidMix, as_created, verified


def duration(path, kind):
    result = subprocess.run(["ffprobe", "-v", "error", "-select_streams", kind + ":0", "-show_entries",
                             "stream=duration:format=duration", "-of", "json", str(path)],
                            check=True, capture_output=True, text=True)
    data = json.loads(result.stdout)
    if not data.get("streams"):
        raise ValueError(f"{path}: no {kind} stream")
    value = data["streams"][0].get("duration")
    seconds = float(value if value not in (None, "N/A") else data.get("format", {}).get("duration", "nan"))
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError(f"{path}: no finite positive duration")
    return seconds


def subtitles_off(path):
    # MP4 enables its first subtitle even with no default disposition. Clear each
    # subtitle track's enabled flag, preserving the selectable tracks (old mux rule).
    b = bytearray(path.read_bytes())
    def boxes(a, end):
        while a + 8 <= end:
            n, t = struct.unpack(">I4s", b[a:a + 8]); h = 8
            if n == 1:
                n, h = struct.unpack(">Q", b[a + 8:a + 16])[0], 16
            elif n == 0:
                n = end - a
            if n < h:
                break
            yield t, a + h, a + n
            a += n
    for t, c, e in boxes(0, len(b)):
        for tt, tc, te in (boxes(c, e) if t == b"moov" else ()):
            if tt != b"trak":
                continue
            kids = {k: (kc, ke) for k, kc, ke in boxes(tc, te)}
            hdlr = next((bytes(b[hc + 8:hc + 12]) for h, hc, he in boxes(*kids.get(b"mdia", (0, 0))) if h == b"hdlr"), b"")
            if b"tkhd" in kids and hdlr in (b"sbtl", b"subt", b"text"):
                b[kids[b"tkhd"][0] + 3] &= 0xFE
    path.write_bytes(b)


def main():
    ap = argparse.ArgumentParser(prog="bin/vh mux", description=__doc__)
    ap.add_argument("video", type=Path)
    ap.add_argument("audio", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("subtitles", nargs="*", type=Path)
    ap.add_argument("--subs-off", action="store_true", help="keep soft subtitles selectable, initially off")
    ap.add_argument("--allow-short", action="store_true", help="deliberately pad audio more than 0.1 s shorter than the picture")
    ap.add_argument("--allow-long", action="store_true", help="deliberately trim audio more than 0.1 s longer than the picture")
    a = ap.parse_intermixed_args()
    inputs = [a.video, a.audio, *a.subtitles]
    if any(a.out.resolve() == p.resolve() or (a.out.exists() and p.exists() and os.path.samefile(a.out, p)) for p in inputs):
        ap.error("output is also an input; choose a different output")
    temp = None
    try:
        with verified(a.audio) as tracked:
            vd, ad = duration(a.video, "v"), duration(a.audio, "a")
            delta = ad - vd
            # a profile mix takes dur=: the music's tail (2.5 s by default) or a narration that ends early is fitted inside the mix
            fit = f"rebuild it at the picture's length (a profile mix: dur={vd:.3f} fade=0.5)"
            if delta < -0.1 - 1e-6 and not a.allow_short:
                ap.error(f"audio is {-delta:.3f} s shorter than the picture ({ad:.3f} vs {vd:.3f} s): {fit}, "
                         "or pass --allow-short to end on silence (a film with sound must not)")
            if delta > 0.1 + 1e-6 and not a.allow_long:
                ap.error(f"audio is {delta:.3f} s longer than the picture ({ad:.3f} vs {vd:.3f} s): {fit}, "
                         "or pass --allow-long to cut it at the picture's end with a 40 ms fade")
            print("mux: " + ("mix inputs and audio match the successful build" if tracked else "external/legacy audio: no mix record; duration checked, source freshness not verified"), flush=True)
            fade = f",afade=t=out:st={max(0, vd - 0.04):.9f}:d=0.04" if ad > vd + 0.001 else ""
            ins, maps, meta = ["-i", str(a.video), "-i", str(a.audio)], ["-map", "0:v", "-map", "[a]"], []
            for s, path in enumerate(a.subtitles):
                lang = "chi" if re.search(r"(?:^|[._-])zh\.", path.name) else "eng" if re.search(r"(?:^|[._-])en\.", path.name) else "und"
                ins += ["-i", str(path)]
                maps += ["-map", str(s + 2)]
                meta += [f"-metadata:s:s:{s}", f"language={lang}"]
            fd, name = tempfile.mkstemp(prefix=f".{a.out.stem}.mux-", suffix=a.out.suffix, dir=a.out.parent)
            os.close(fd)
            temp = Path(name)
            as_created(temp)
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *ins, "-filter_complex", f"[1:a]apad,atrim=0:{vd:.9f}{fade}[a]",
                            *maps, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", *(["-c:s", "mov_text"] if a.subtitles else []),
                            *meta, *(["-disposition:s", "0"] if a.subs_off else []), "-movflags", "+faststart", str(temp)], check=True)
            if a.subs_off and a.subtitles:
                subtitles_off(temp)
        os.replace(temp, a.out)
    finally:
        if temp is not None and temp.exists():
            temp.unlink()
    n = len(a.subtitles)
    print(f"✓ {a.out}" + (f" (+{n} subtitle track(s){', off by default' if a.subs_off else ''})" if n else ""))


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:   # ffmpeg has said why on stderr
        sys.exit(f"mux: {Path(e.cmd[0]).name} failed (exit {e.returncode})")
    except (InvalidMix, OSError, ValueError) as e:
        sys.exit(f"mux: {e}")
