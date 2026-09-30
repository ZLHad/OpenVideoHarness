"""Motion energy of a clip: where the action peaks, and frames that repeat in the middle of motion.

usage: python3 tools/motion.py <clip> [--out curve.json]

Energy of frame n = mean luma of |frame n - frame n-1| (ffmpeg `tblend=difference` into `signalstats` YAVG), measured on
a grey copy scaled to at most 480 px wide. Needs ffmpeg, nothing else. One JSON line on stdout:
  frames                          frame count of the clip
  motion_p75                      75th percentile of the energy; 0 means the clip does not move
  peak_frame_smoothed/peak_t_smoothed
                                  where the smoothed energy (median of 5, then mean of 5 frames) is highest. The top of a
                                  smooth move is flat, so this can be off by several frames: settle the cut on a strip
  duplicate_frames_inside_motion  frame numbers (from 0) that equal the frame before them while both neighbours are moving:
                                  energy under 15 % of motion_p75 between two frames above 50 %. A fps conversion that
                                  repeats frames shows as a regular pattern (24 -> 30 fps with `fps=30`: every 5th frame).
                                  A list of candidates, not a verdict: a duplicate the encoder spoiled can be missed, and a
                                  deliberate hold at the top of a move can be listed
--out writes the whole curve (pts, energy, energy_smoothed) next to that summary, for plotting.

Used for cut-on-action and for checking a generated clip or a frame-rate conversion (playbook/05-hybrid-genvideo.md).
Measured on synthetic clips only: see that playbook for the numbers, and look at the frames it names before trusting it.
"""
import argparse, json, re, statistics, subprocess, sys

# grey, at most 480 px wide, first frame dropped by tblend (it has no predecessor); -2 keeps the height even
FILTER = ("format=gray,scale='min(480,iw)':-2,tblend=all_mode=difference,signalstats,"
          "metadata=print:key=lavfi.signalstats.YAVG:file=-")
K = 5   # median of K then mean of K: removes isolated spikes (the encoder makes them) before looking for the peak


def energy(clip):
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-an", "-i", clip, "-vf", FILTER, "-f", "null", "-"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"motion.py: ffmpeg could not read {clip}:\n{r.stderr.strip()}")
    pts, val = [], []
    for line in r.stdout.splitlines():
        m = re.search(r"pts_time:([\d.]+)", line)
        if m:
            pts.append(float(m.group(1)))
        m = re.search(r"YAVG=([\d.]+)", line)
        if m:
            val.append(float(m.group(1)))
    if len(val) < 3 or len(val) != len(pts):
        sys.exit(f"motion.py: {clip} has too few video frames to measure motion")
    return pts, val


def summarize(pts, val):
    n = len(val)
    med = [statistics.median(val[max(0, i - K // 2):i + K // 2 + 1]) for i in range(n)]
    smooth = [statistics.mean(med[max(0, i - K // 2):i + K // 2 + 1]) for i in range(n)]
    peak = max(range(n), key=smooth.__getitem__)
    p75 = sorted(val)[int(0.75 * (n - 1))]
    dups = [i + 1 for i in range(1, n - 1) if val[i] < 0.15 * p75 and val[i - 1] > 0.5 * p75 and val[i + 1] > 0.5 * p75]
    return smooth, {"frames": n + 1, "motion_p75": round(p75, 3), "peak_frame_smoothed": peak + 1,
                    "peak_t_smoothed": pts[peak], "duplicate_frames_inside_motion": dups}


def main():
    ap = argparse.ArgumentParser(description="motion energy, peak frame and repeated frames of a clip")
    ap.add_argument("clip")
    ap.add_argument("--out", help="write the whole curve as JSON")
    args = ap.parse_args()
    pts, val = energy(args.clip)
    smooth, res = summarize(pts, val)
    print(json.dumps(res))
    if args.out:
        with open(args.out, "w") as fh:
            json.dump({"pts": pts, "energy": val, "energy_smoothed": smooth, **res}, fh)


if __name__ == "__main__":
    main()
