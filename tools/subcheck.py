"""Subtitles shorter than it takes to read them: the film's subtitle tracks and the SRT files beside it.

usage: python3 tools/subcheck.py <video> [more.srt …]      (bin/vh check runs it on the video it checks)

Each subtitle must show for at least readcheck's subtitle rule: 1.8 s, or its characters at 9 a second for Chinese
(half-width characters count half) and 20 a second otherwise, whichever is longer (tools/readcheck.py, subtitle_check).
Where the subtitles come from: the video's own subtitle tracks (an MP4's mov_text, read with ffmpeg), and the .srt files
in the video's folder (all of them when there are five or fewer, else those whose name starts with the video's), plus
any given. Captions burned into the picture are not here: bin/vh readcheck <project> judges those.
Prints one line per source, and the short entries (the 12 shortest). Exit: 0 none short · 1 some short · 2 no video.
"""
import re, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from readcheck import subtitle_check

def ts(x):
    h, m, r = x.strip().replace(".", ",").split(":"); s, ms = r.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

def parse(srt):
    out = []
    for b in re.split(r"\r?\n\s*\r?\n", srt.strip()):
        m = re.search(r"(\d+:\d+:\d+[,.]\d+)\s*-->\s*(\d+:\d+:\d+[,.]\d+)", b)
        if not m: continue
        text = " ".join(l.strip() for l in b[m.end():].strip().splitlines() if l.strip())
        text = re.sub(r"<[^>]+>|\{\\[^}]*\}", "", text)
        if text: out.append((ts(m.group(1)), ts(m.group(2)), text))
    return out

def tracks(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "s", "-show_entries", "stream=index:stream_tags=language", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True)
    out = []
    for k, line in enumerate(l for l in r.stdout.splitlines() if l.strip()):
        lang = (line.split(",") + [""])[1] or "und"
        x = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(video), "-map", f"0:s:{k}", "-f", "srt", "-"], capture_output=True, text=True)
        if x.returncode == 0: out.append((f"track {k + 1} ({lang})", parse(x.stdout)))
    return out

def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python3 tools/subcheck.py <video> [more.srt …]")
    video = Path(sys.argv[1])
    if not video.is_file():
        print(f"subcheck: no such file {video}", file=sys.stderr); sys.exit(2)
    sources = tracks(video)
    srts = sorted(video.parent.glob("*.srt"))
    if len(srts) > 5: srts = [p for p in srts if p.name.startswith(video.stem)]
    srts += [Path(p) for p in sys.argv[2:]]
    for p in dict.fromkeys(srts):
        try: sources.append((p.name, parse(p.read_text(encoding="utf-8", errors="replace"))))
        except OSError: pass
    if not sources:
        print("subtitles: none in the video or beside it (captions burned into the picture: bin/vh readcheck <project>)"); sys.exit(0)
    bad = 0
    for name, items in sources:
        short = []
        for a, b, text in items:
            need, rate, limit = subtitle_check(text, b - a)
            if b - a < need - 1e-3: short.append((b - a, need, a, text))
        bad += bool(short)
        if not short:
            print(f"subtitles · {name}: {len(items)} entries, each on screen long enough to read (1.8 s, or 9 Chinese / 20 other characters a second)")
            continue
        print(f"subtitles · {name}: {len(short)} of {len(items)} entries are shorter than it takes to read them (1.8 s, or 9 Chinese / 20 other characters a second):")
        for d, need, a, text in sorted(short)[:12]:
            m, s = divmod(a, 60)
            print(f"    {int(m)}:{s:06.3f}  {d:.2f} s, needs {need:.2f} s  {text[:40]}")
        if len(short) > 12: print(f"    … {len(short) - 12} more")
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
