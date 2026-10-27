// Joining a film's chunks (bin/vh render, bin/vh patch): ffmpeg's concat of the chunk files, stream-copied, with every
// packet's DTS set again to (i − D) / fps in decoding order, D being the deepest reorder of any packet.
//
// Why: each chunk is an x264 run of its own. One of one or two frames ends before x264 has seen its B-frame delay, so
// its DTS lag its PTS by less than the other chunks' do; the MP4 muxer then keeps the DTS rising by moving the next
// chunk's up a tick at a time. The film still has every frame (nb_frames, the PTS), but packets of 1 tick and of 3
// frames, which a constant-rate decode (bin/vh check's) reads as one frame too many and some frames late. One DTS step a
// frame keeps every packet one frame long; a film with no short chunk gets the DTS x264 gave it.
import { spawnSync } from "node:child_process";

// list: a concat list (file '…' and duration lines); out: the joined video; args: more output arguments (-movflags …).
// → spawnSync's result, as the caller's ffmpeg call returned it before
export function concatChunks(list, out, fps, args = []) {
  const probe = spawnSync("ffprobe", ["-v", "error", "-f", "concat", "-safe", "0", "-i", list, "-select_streams", "v:0", "-show_entries", "packet=pts_time",
    "-of", "csv=p=0"], { encoding: "utf8", maxBuffer: 1 << 28 });
  if (probe.status !== 0) return probe;
  let deepest = 0, i = 0;
  for (const line of probe.stdout.split("\n")) {
    const t = parseFloat(line);
    if (!Number.isFinite(t)) continue;
    deepest = Math.max(deepest, i++ - Math.round(t * fps));   // this packet is decoded i − (its frame) frames before it is shown
  }
  return spawnSync("ffmpeg", ["-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", list, "-map", "0:v", "-c", "copy",
    "-bsf:v", `setts=pts=PTS:dts=(N-${deepest})/(${fps}*TB)`, ...args, out], { encoding: "utf8" });
}
