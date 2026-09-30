"""Motion energy of a clip: where the action peaks, and frames that repeat in the middle of motion.

usage (from the repo root): python3 tools/motion.py <clip> [--out curve.json]

Energy of frame n = mean luma of |frame n - frame n-1| (ffmpeg `tblend=difference` into `signalstats` YAVG), measured on
a grey copy scaled to at most 480 px wide. Needs ffmpeg, nothing else. One JSON line on stdout:
  frames                          frame count of the clip
  motion_p75                      75th percentile of the energy; 0 means the clip does not move
  peak_frame_smoothed/peak_t_smoothed
                                  the middle of the frames whose smoothed energy (median of 5, then mean of 5 frames) is
                                  within 90 % of its maximum; null when nothing moves
  peak_window_frames              first and last frame of that run: the peak is a window, not a frame, because the top of a
                                  smooth move is flat. Settle the cut on a strip of frames
  duplicate_frames_inside_motion  frame numbers (from 0) that equal the frame before them while both neighbours are moving:
                                  energy under 15 % of motion_p75 between two frames above 50 %. A fps conversion that
                                  repeats frames shows as a regular pattern (24 -> 30 fps with `fps=30`: every 5th frame).
                                  A list of candidates, not a verdict: a deliberate hold at the top of a move is listed too
--out writes the whole curve (pts, energy, energy_smoothed) next to that summary, for plotting.

Used for cut-on-action and for checking a generated clip or a frame-rate conversion (playbook/05-hybrid-genvideo.md).
Checked on synthetic clips only: look at the frames it names before trusting it.
"""
import argparse, json, os, re, shutil, statistics, subprocess, sys

# grey, at most 480 px wide, first frame dropped by tblend (it has no predecessor); -2 keeps the height even
FILTER = ("format=gray,scale='min(480,iw)':-2,tblend=all_mode=difference,signalstats,"
          "metadata=print:key=lavfi.signalstats.YAVG:file=-")
NUM = r"([-+0-9.eE]+)"   # ffmpeg prints values under 1e-4 as 7.7e-06: a bare [\d.]+ would read that as 7.7
PTS, YAVG = re.compile(r"pts_time:" + NUM), re.compile(r"YAVG=" + NUM)
K = 5   # median of K then mean of K: removes isolated spikes before looking for the peak


def parse(text):
    """The `metadata=print` text ffmpeg writes -> (timestamps in s, energies), one of each per frame."""
    pts, val = [], []
    for line in text.splitlines():
        m = PTS.search(line)
        if m:
            pts.append(float(m.group(1)))
        m = YAVG.search(line)
        if m:
            val.append(float(m.group(1)))
    return pts, val


def energy(clip):
    if shutil.which("ffmpeg") is None:
        sys.exit("motion.py: ffmpeg not found on PATH")
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-an", "-i", clip, "-vf", FILTER, "-f", "null", "-"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"motion.py: ffmpeg could not read {clip}:\n{r.stderr.strip()}")
    pts, val = parse(r.stdout)
    if len(val) < 3 or len(val) != len(pts):
        sys.exit(f"motion.py: {clip} has too few video frames to measure motion")
    return pts, val


def summarize(pts, val):
    n = len(val)
    med = [statistics.median(val[max(0, i - K // 2):i + K // 2 + 1]) for i in range(n)]
    smooth = [statistics.mean(med[max(0, i - K // 2):i + K // 2 + 1]) for i in range(n)]
    p75 = sorted(val)[int(0.75 * (n - 1))]
    dups = [i + 1 for i in range(1, n - 1) if val[i] < 0.15 * p75 and val[i - 1] > 0.5 * p75 and val[i + 1] > 0.5 * p75]
    top = max(smooth)
    res = {"frames": n + 1, "motion_p75": round(p75, 3)}
    if top < 1e-3:   # nothing moves: the argmax of a flat-zero curve would be frame 1
        res.update(peak_frame_smoothed=None, peak_t_smoothed=None, peak_window_frames=None)
    else:
        # the top of a smooth move is flat and noisy, so take the middle of the run of frames within 90 % of the maximum
        lo = hi = max(range(n), key=smooth.__getitem__)
        while lo > 0 and smooth[lo - 1] >= 0.9 * top:
            lo -= 1
        while hi < n - 1 and smooth[hi + 1] >= 0.9 * top:
            hi += 1
        mid = (lo + hi) // 2
        res.update(peak_frame_smoothed=mid + 1, peak_t_smoothed=pts[mid], peak_window_frames=[lo + 1, hi + 1])
    res["duplicate_frames_inside_motion"] = dups
    return smooth, res


def main():
    ap = argparse.ArgumentParser(description="motion energy, peak frame and repeated frames of a clip")
    ap.add_argument("clip")
    ap.add_argument("--out", help="write the whole curve as JSON")
    args = ap.parse_args()
    if args.out and not os.path.isdir(os.path.dirname(os.path.abspath(args.out))):
        sys.exit(f"motion.py: the folder for --out does not exist: {os.path.dirname(os.path.abspath(args.out))}")
    pts, val = energy(args.clip)
    smooth, res = summarize(pts, val)
    print(json.dumps(res))
    if args.out:
        with open(args.out, "w") as fh:
            json.dump({"pts": pts, "energy": val, "energy_smoothed": smooth, **res}, fh)


if __name__ == "__main__":
    main()
