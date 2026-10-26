"""bin/vh check's loudness: the film's sound as it is in the file that will be uploaded, measured (ITU-R BS.1770 through
ffmpeg's ebur128 filter, true peak 4× oversampled): integrated loudness, true peak and loudness range. Stdlib only, and
ffmpeg.

usage: python3 tools/loudcheck.py <video> [--json f.json] [--lufs -14] [--tol 1] [--tp -1]
The target is the mix's (bin/vh mix: −14 LUFS; its true-peak ceilings are −1.5 and −1.65 dBTP, and an AAC encode moves the
peak by about ±0.1 dB): integrated within --tol LU of --lufs, true peak at most --tp dBTP (the platforms' −1). Off the
target is said ("WARN …"), not failed: a quiet art film may be on purpose. A film with no sound is said and left there.
Exit 0 (the words say how it went); 2 a usage error, or ffmpeg could not measure it.
--json: {"audio": bool, "integrated", "true_peak", "lra", "target": {"lufs", "tol", "tp"}, "ok", "problems": [text]}.
"""
import argparse, json, re, subprocess, sys


def measure(video):
    """{"integrated", "true_peak", "lra"} of the first audio stream, or None when there is none."""
    has = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_type", "-of", "csv=p=0", video],
                         capture_output=True, text=True).stdout.strip()
    if not has:
        return None
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", video, "-map", "0:a:0", "-af", "ebur128=peak=true:framelog=quiet", "-f", "null", "-"],
                       capture_output=True, text=True, errors="replace")
    summary = r.stderr[r.stderr.rfind("Summary:"):] if "Summary:" in r.stderr else ""
    def num(pat):
        m = re.search(pat, summary, re.S)
        try:
            return float(m.group(1)) if m else None
        except ValueError:
            return None
    got = {"integrated": num(r"Integrated loudness:.*?I:\s*(-?[\d.]+|-inf)\s*LUFS"), "true_peak": num(r"True peak:.*?Peak:\s*(-?[\d.]+|-inf)\s*dBFS"),
           "lra": num(r"Loudness range:.*?LRA:\s*(-?[\d.]+)\s*LU")}
    if r.returncode or got["integrated"] is None:
        raise RuntimeError(f"ffmpeg ebur128 gave no summary (exit {r.returncode}): {r.stderr.strip()[-300:]}")
    return got


def main(argv):
    ap = argparse.ArgumentParser(prog="loudcheck.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("video")
    ap.add_argument("--json")
    ap.add_argument("--lufs", type=float, default=-14.0)
    ap.add_argument("--tol", type=float, default=1.0)
    ap.add_argument("--tp", type=float, default=-1.0)
    a = ap.parse_args(argv)
    try:
        m = measure(a.video)
    except (RuntimeError, OSError) as e:
        print(f"loudness: {e}", file=sys.stderr)
        return 2
    target = {"lufs": a.lufs, "tol": a.tol, "tp": a.tp}
    if m is None:
        res = {"audio": False, "target": target, "ok": True, "problems": []}
        line = "loudness: no sound (a silent film)"
    else:
        probs = []
        if abs(m["integrated"] - a.lufs) > a.tol + 1e-9:
            probs.append(f"{m['integrated']:.1f} LUFS integrated, {m['integrated'] - a.lufs:+.1f} LU off the mix's {a.lufs:g}: "
                         + ("louder than the platforms play: they turn it down, and the limiting that made it this loud stays" if m["integrated"] > a.lufs
                            else "quieter than the platforms' playback level (bin/vh mix … lufs=-14, then mux again)"))
        if m["true_peak"] is not None and m["true_peak"] > a.tp + 1e-9:
            probs.append(f"true peak {m['true_peak']:.1f} dBTP, over {a.tp:g}: it may clip on a phone once the platform re-encodes it "
                         "(bin/vh mix's true-peak ceiling, then mux again)")
        res = {"audio": True, **m, "target": target, "ok": not probs, "problems": probs}
        line = (f"loudness: {m['integrated']:.1f} LUFS integrated · true peak {m['true_peak']:.1f} dBTP · LRA {m['lra']:.1f} LU"
                f" (target {a.lufs:g} ±{a.tol:g}, ≤ {a.tp:g} dBTP)")
        if probs:
            line = "WARN " + line + "".join(f"\n   {p}" for p in probs)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f)
    print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
