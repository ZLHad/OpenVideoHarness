"""Spec check: is a delivered video what the project's BRIEF says it is?

usage: python3 tools/speccheck.py <video> [--brief BRIEF.md]
exit status: 0 matches (WARNs allowed), 1 a FAIL, 2 the video could not be read; no BRIEF.md: says so, exit 0

The BRIEF is the nearest BRIEF.md at or above the video (a project's out/ is inside the project), or --brief.
It reads two lines of its Spec section (templates/BRIEF.md):
  - Output: 1920x1080, 30 fps, exactly 103.0s (3090 frames)
        the composition size (what the code is written at), the frame rate, and the length: "exactly N s" and/or
        "(N frames)" ("帧" too), or a range such as "{120–300}s" / "60–90 s" for a target that is not fixed yet;
        "~700 frames", "约 160 s", "about", "around", "左右" and the like (in the same clause) are targets and are not
        checked; "exactly N s" always is; with several "N frames" the film has to match one of them
  - Resolution: 1080p | 4k | 1080p, 4k
        the deliveries; 4k is the composition at twice the size (3840x2160 for a 1920x1080 one). No line: 1080p.
FAIL: a frame size that is none of the listed deliveries (4K when the BRIEF lists only 1080p, too), another aspect,
an odd width or height, another frame rate (0.05 % tolerance: 29.97 is not 30, 30.0008 is), another length than an
exact one (one frame of tolerance; the picture's length, an audio tail does not count). WARN: a frame smaller than every
delivery in the same aspect (a draft: only an exact length in seconds is still checked), a length outside a range, an Output line that still has
{placeholders} or gives no size or rate, a variable frame rate, non-square pixels, audio running past the picture.
"""
import argparse, json, re, subprocess, sys
from fractions import Fraction
from pathlib import Path

def find_brief(video):
    d = Path(video).resolve().parent
    for _ in range(6):
        if (d / "BRIEF.md").is_file():
            return d / "BRIEF.md"
        if d.parent == d or (d / ".git").exists():
            return None
        d = d.parent
    return None

def spec_line(text, key):
    m = re.search(rf"(?m)^\s*[-*]\s*{key}\s*[:：]\s*(.*)$", text)
    return re.sub(r"<!--.*?(-->|$)", "", m.group(1)).strip() if m else None

APPROX = re.compile(r"[~≈]|约(?!束)|左右|\babout\b|\baround\b|\bapprox|\btarget\b", re.I)
NUM = r"(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)"   # 1,200 reads as 1200
num = lambda x: float(x.replace(",", ""))

def main():
    ap = argparse.ArgumentParser(prog="speccheck.py", usage="python3 tools/speccheck.py <video> [--brief BRIEF.md]")
    ap.add_argument("video"); ap.add_argument("--brief")
    a = ap.parse_args()
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height,r_frame_rate,avg_frame_rate,nb_read_packets,sample_aspect_ratio,duration:format=duration",
                              "-of", "json", a.video], capture_output=True, text=True)
    except OSError as e:
        print(f"speccheck: cannot run {e.filename or 'ffprobe'}: {e.strerror}", file=sys.stderr); sys.exit(2)
    pr = json.loads(out.stdout or "{}"); st = (pr.get("streams") or [None])[0]
    if out.returncode or not st:
        print(f"speccheck: no video stream in {a.video}", file=sys.stderr); sys.exit(2)
    W, H, n = st["width"], st["height"], int(st.get("nb_read_packets") or 0)
    rate = Fraction(st["r_frame_rate"]); fps = float(rate)
    whole = float((pr.get("format") or {}).get("duration") or 0)
    dur = n / fps if n and fps else float(st.get("duration") or whole)   # the picture's length; the audio may run longer
    if a.brief:
        brief = Path(a.brief)
        if not brief.is_file():
            print(f"speccheck: no BRIEF at {a.brief}", file=sys.stderr); sys.exit(2)
    else:
        brief = find_brief(a.video)
    if not brief:
        print(f"spec: {W}x{H}, {fps:g} fps, {n} frames, {dur:.2f} s; no BRIEF.md above the video, nothing to compare"); return
    text = brief.read_text(encoding="utf-8", errors="replace")
    o, r = spec_line(text, "Output"), spec_line(text, "Resolution")
    fails, warns = [], []
    if W % 2 or H % 2:
        fails.append(f"{W}x{H} has an odd side (yuv420p players need even sizes)")
    sar = st.get("sample_aspect_ratio") or "1:1"
    if sar not in ("1:1", "0:1", "N/A"):
        warns.append(f"non-square pixels (SAR {sar})")
    avg = st.get("avg_frame_rate") or "0/0"
    if avg != "0/0" and abs(float(Fraction(avg)) - fps) > fps * 5e-4:
        warns.append(f"variable frame rate (nominal {rate}, average {avg})")
    if whole - dur > 0.1:
        warns.append(f"the file runs {whole - dur:.2f} s past the last frame (audio longer than the picture)")
    draft = False
    if o is None:
        warns.append(f"{brief.name} has no '- Output:' line")
    else:
        if re.search(r"\{[^}]*[A-Za-z][^}]*\}", o):   # {W}x{H}, {fps}; a range such as {60–90}s is not a placeholder
            warns.append(f"the Output line still has placeholders: {o[:80]}")
        m = re.search(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", o)
        ks = sorted({2 if x in ("4k", "2160p", "uhd") else 1 for x in re.findall(r"4k|2160p|uhd|1080p|720p", (r or "1080p").lower())} or {1})
        if m:
            cw, ch = int(m.group(1)), int(m.group(2))
            sizes = [(cw * k, ch * k) for k in ks]
            if abs(W / H - cw / ch) > 0.01:
                fails.append(f"aspect {W}x{H}, the BRIEF's composition is {cw}x{ch}")
            elif W < min(w for w, _ in sizes):
                draft = True
                warns.append(f"{W}x{H} is smaller than every delivery ({' or '.join(f'{w}x{h}' for w, h in sizes)}): a draft, so its rate and frame count are not checked")
            elif (W, H) not in sizes:
                want = " or ".join(f"{w}x{h}" for w, h in sizes)
                extra = " (a 4K delivery: Resolution: 1080p, 4k)" if (W, H) == (cw * 2, ch * 2) else ""
                fails.append(f"frame {W}x{H}, the BRIEF's deliveries are {want}{extra}")
        elif not re.search(r"\{", o):
            warns.append("the Output line gives no frame size")
        mfps = re.search(r"(?:(\d+(?:\.\d+)?)\s*[–-]\s*)?(\d+(?:\.\d+)?)\s*fps", o, re.I)
        lo = float(mfps.group(1)) if mfps and mfps.group(1) else None
        fps_range = lo is not None and lo < float(mfps.group(2)) <= 240   # "24–30 fps"; not "1080 – 30 fps"
        if draft:
            pass
        elif fps_range:
            warns.append(f"the Output line gives a frame-rate range ({mfps.group(0)}): not checked")
        elif mfps:
            want = float(mfps.group(2))
            if abs(fps - want) > want * 5e-4:
                fails.append(f"{fps:.3f} fps, the BRIEF says {mfps.group(2)}")
        elif not re.search(r"\{", o):
            warns.append("the Output line gives no frame rate")
        clause = lambda i: re.split(r"[,，;；]|exactly", o[:i])[-1]   # since the clause began; a bracket explains the figure before it
        approx = lambda mm: bool(APPROX.search(clause(mm.start())) or re.match(r"\s*左右", o[mm.end():]))
        me = re.search(r"exactly\s*\**\s*" + NUM + r"\s*s", o)   # "exactly" is never approximate
        counts = [num(m.group(1)) for m in re.finditer(NUM + r"\s*(?:frames|帧)", o) if not approx(m)]
        mr = re.search(NUM + r"\s*[–-]\s*" + NUM + r"\s*\}?\s*s\b", o)
        if me:
            want = num(me.group(1))
            if abs(dur - want) > 1.5 / fps:
                fails.append(f"{dur:.3f} s of picture, the BRIEF says exactly {me.group(1)} s")
        elif counts and not draft:   # a frame count holds at the BRIEF's rate only; "28 bars × 64 frames = 1792 frames": any of them
            if n and all(abs(n - c) > 1 for c in counts):
                fails.append(f"{n} frames, the BRIEF says {' or '.join(f'{c:g}' for c in counts)}")
        elif mr and not num(mr.group(1)) <= dur <= num(mr.group(2)):
            warns.append(f"{dur:.1f} s, outside the BRIEF's {mr.group(1)}–{mr.group(2)} s")
    rel = f"{brief.resolve().parent.name}/{brief.name}"
    print(f"spec: {W}x{H}, {fps:g} fps, {n} frames, {dur:.2f} s against {rel} (Output: {(o or '—')[:60]}; Resolution: {r or '— (1080p)'})")
    for f in fails: print(f"FAIL {f}")
    for w in warns: print(f"WARN {w}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
