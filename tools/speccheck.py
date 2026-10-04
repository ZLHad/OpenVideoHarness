"""Spec check: is a delivered video what the project's BRIEF says it is?

usage: python3 tools/speccheck.py <video> [--brief BRIEF.md]
exit status: 0 matches (WARNs allowed), 1 a FAIL, 2 the video could not be read; no BRIEF.md: says so, exit 0

The BRIEF is the nearest BRIEF.md at or above the video (a project's out/ is inside the project), or --brief.
It reads two lines of its Spec section (templates/BRIEF.md):
  - Output: 1920x1080, 30 fps, exactly 103.0s (3090 frames)
        the composition size (what the code is written at), the frame rate, and the length: "exactly N s" and/or
        "(N frames)" ("帧" too), or a range such as "{120–300}s" / "60–90 s" for a target that is not fixed yet;
        "~700 frames", "约 160 s" and the like are targets and are not checked
  - Resolution: 1080p | 4k | 1080p, 4k
        the deliveries; 4k is the composition at twice the size (3840x2160 for a 1920x1080 one). No line: 1080p.
FAIL: a frame size that is none of the listed deliveries (4K when the BRIEF lists only 1080p, too), another aspect,
an odd width or height, another frame rate (0.05 % tolerance: 29.97 is not 30, 30.0008 is), another length than an
exact one (one frame of tolerance). WARN: a length outside a range, an Output line that still has {placeholders} or
gives no size or rate, a variable frame rate, non-square pixels.
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

def main():
    ap = argparse.ArgumentParser(prog="speccheck.py", usage="python3 tools/speccheck.py <video> [--brief BRIEF.md]")
    ap.add_argument("video"); ap.add_argument("--brief")
    a = ap.parse_args()
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-count_packets", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height,r_frame_rate,avg_frame_rate,nb_read_packets,sample_aspect_ratio:format=duration",
                              "-of", "json", a.video], capture_output=True, text=True)
    except OSError as e:
        print(f"speccheck: cannot run {e.filename or 'ffprobe'}: {e.strerror}", file=sys.stderr); sys.exit(2)
    pr = json.loads(out.stdout or "{}"); st = (pr.get("streams") or [None])[0]
    if out.returncode or not st:
        print(f"speccheck: no video stream in {a.video}", file=sys.stderr); sys.exit(2)
    W, H, n = st["width"], st["height"], int(st.get("nb_read_packets") or 0)
    rate = Fraction(st["r_frame_rate"]); fps = float(rate)
    dur = float((pr.get("format") or {}).get("duration") or 0)
    brief = Path(a.brief) if a.brief else find_brief(a.video)
    if not brief or not brief.is_file():
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
    if o is None:
        warns.append(f"{brief.name} has no '- Output:' line")
    else:
        if "{" in o:
            warns.append(f"the Output line still has placeholders: {o[:80]}")
        m = re.search(r"(\d{3,4})\s*[x×]\s*(\d{3,4})", o)
        res = [x for x in re.split(r"[,/\s]+", (r or "1080p").lower()) if x] or ["1080p"]
        ks = sorted({2 if x in ("4k", "2160p", "uhd") else 1 for x in res})
        if m:
            cw, ch = int(m.group(1)), int(m.group(2))
            if abs(W / H - cw / ch) > 0.01:
                fails.append(f"aspect {W}x{H}, the BRIEF's composition is {cw}x{ch}")
            elif (W, H) not in [(cw * k, ch * k) for k in ks]:
                want = " or ".join(f"{cw * k}x{ch * k}" for k in ks)
                extra = " (4K: add 4k to the Resolution line)" if (W, H) == (cw * 2, ch * 2) else ""
                fails.append(f"frame {W}x{H}, the BRIEF's deliveries are {want}{extra}")
        elif "{" not in o:
            warns.append("the Output line gives no frame size")
        m = re.search(r"(\d+(?:\.\d+)?)\s*fps", o)
        if m:
            want = float(m.group(1))
            if abs(fps - want) > want * 5e-4:
                fails.append(f"{fps:.3f} fps, the BRIEF says {m.group(1)}")
        elif "{" not in o:
            warns.append("the Output line gives no frame rate")
        APPROX = r"(?<![~≈约]\s)(?<![~≈约])(?<!about )(?<!approx\. )"   # "~700 frames", "约 4800 帧" are targets, not specs
        mf = re.search(APPROX + r"\b(\d+)\s*(?:frames|帧)", o)
        me = re.search(r"exactly\s*\**\s*(\d+(?:\.\d+)?)\s*s", o)
        mr = re.search(r"(\d+(?:\.\d+)?)\s*[–-]\s*(\d+(?:\.\d+)?)\s*\}?\s*s\b", o)
        if mf and n and n != int(mf.group(1)) and abs(n - int(mf.group(1))) > 1:
            fails.append(f"{n} frames, the BRIEF says {mf.group(1)}")
        elif me and abs(dur - float(me.group(1))) > 1.5 / fps:
            fails.append(f"{dur:.3f} s, the BRIEF says exactly {me.group(1)} s")
        elif not (mf or me) and mr and not float(mr.group(1)) <= dur <= float(mr.group(2)):
            warns.append(f"{dur:.1f} s, outside the BRIEF's {mr.group(1)}–{mr.group(2)} s")
    rel = brief.parent.name + "/" + brief.name
    head = f"spec: {W}x{H}, {fps:g} fps, {n} frames, {dur:.2f} s against {rel} (Output: {(o or '—')[:60]}; Resolution: {r or '— (1080p)'})"
    print(head)
    for f in fails: print(f"FAIL {f}")
    for w in warns: print(f"WARN {w}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
