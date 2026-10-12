# 07 · Does the film move? Still stretches, cuts that flash, periodic motion, found by the tools first

*Recorded 2026-10-12 · Status: the checks went into `bin/vh check` in this note's PR, all as warnings; the three maintainer films are the author's local files, not in the repo · [中文](../07-motion-checks.md)*

## Question

Three kinds of fault used to be seen by a reviewer or a person, never by the tools: still stretches (research 06's reviewer scored "variety" 4 for two films whose middles stood still), a hard cut from a dark 3D scene to a pale page that read as a flash, and a periodic bounce whose still point fell on one frame a cycle, which the isolated-frame scan reported as 7 glitches. Can the decode `bin/vh check` already does (192×108 grey, every frame) measure these too, catching the cases above without false alarms on the showcase?

## Method

- `tools/isoframes.py --motion`, from the same decode: per frame pair the share of pixels changed by more than 12 levels, the mean change, the mean brightness, and the share changed by more than 6 levels a second apart.
  - Hard cut: over 30 % of the pixels change by more than 12 levels, the mean change is over 18 and over 3× the median of the 10 frames around it. A cut whose mean brightness rises by more than 90 of 255 (3 frames each side) is listed as a flash.
  - Still: under 0.2 % of the pixels change by more than 6 levels from one frame to the next (grain averages away at this size). Runs of 2 s or more count towards a still share; runs of 3 s or more are listed, as frozen (no change a second apart either) or a slow drift.
  - Periodic: three or more isolated frames evenly spaced (within one frame, at least 3 apart) are periodic motion, not glitches.
  - Jump inside a shot: a frame-to-frame change over 8× the shot's median and over 6 levels (0.35 s after a cut and cut-sized changes left out).
- Films: the local finals of the showcase 00–04 projects (not checked against the release copies), research 06's four films, three maintainer films (9–14 minutes, landscape, narrated).

## Findings

| Film | Length | Moving pairs | Hard cuts | Still share (≥ 2 s) | Still runs ≥ 3 s | Flash cuts | Periodic | Largest jump |
|---|---|---|---|---|---|---|---|---|
| showcase 00 | 20 s | 41% | 0 | 0% | 0 | 0 | 0 | 12× |
| showcase 01 | 12 s | 98% | 4 | 0% | 0 | 0 | 0 | 10× |
| showcase 02 | 25 s | 54% | 0 | 0% | 0 | 0 | 0 | — |
| showcase 03 | 25 s | 24% | 0 | 0% | 0 | 0 | 0 | — |
| showcase 04 | 103 s | 80% | 18 | 0% | 0 | 0 | 0 | 25× |
| 06 · milky way A | 30 s | 31% | 0 | 48% | 3 | 0 | 0 | — |
| 06 · milky way B | 30 s | 10% | 0 | 29% | 1 | 0 | 0 | — |
| 06 · bakery A | 20 s | 33% | 0 | 41% | 1 | 0 | 0 | — |
| 06 · bakery B | 20 s | 15% | 0 | 50% | 3 | 0 | 0 | — |
| long film 1 | 846 s | 20% | 45 | 20% | 2 | 0 | 1 (7 frames, every 15) | 41× |
| long film 2 | 542 s | 15% | 16 | 32% | 18 | 1 | 0 | — |
| long film 3 | 184 s | 50% | 3 | 4% | 0 | 0 | 0 | 21× |

1. No still runs on the showcase; all four 06 films have them, both B films listed (slow drifts). As in note 06, the A films are no less still than the B ones: this measures standing still, not which group is better.
2. The long films spend 20–32 % of their time in still runs of 2 s or more, mostly 2–3 s holds while the narration speaks; runs of 3 s or more are 2 and 18. So runs are listed from 3 s, and 2 s ones only count towards the share.
3. One flash found: long film 2 at 35.37 s, a hard cut from a darker scene to a blank page, mean brightness 112 → 210. Long film 1's flashes had been fixed (faded in from dark) before release, and none is reported.
4. Long film 1's 7 frames at 432.0–435.0 s, one every 15 frames, are reported as periodic motion and no longer fail, without `--allow`.
5. The jumps found on the showcase were all designed (a line of text vanishing, a fast push), so the largest jump is only a number on the summary line.
6. Cost: a 9-minute 1080p film took 8.0 s for the isolated-frame scan alone and 7.6 s with all of this; the decode is the time.

## What changed

- `bin/vh check` runs the scan with `--motion`: a summary line, and a warning line each for still runs of 3 s or more and for flash cuts. The exit status does not change.
- Evenly spaced isolated frames are periodic motion, not failures; `--allow` takes spans (`432-435`).
- `playbook/03` §2: periodic motion under a quarter of the frame rate, as a smooth cosine; a hard cut from dark to bright reads as a flash.

## Limits

- The thresholds were read off these 12 films, not proven: 0.2 %, 6 levels, 3 s and 90 levels are first values. None becomes a failure: stillness and bright cuts are often designed.
- Stillness is pixels only: labels lighting up one by one on a still picture count as still.
- Only hard cuts are checked for flashes; a fast dissolve from dark to bright is not.
- Periodic motion needs three evenly spaced frames; a long cycle that lands on its still point twice is still reported as glitches.

**Sources**: per-frame data from `isoframes.py --motion --json` and frame checks on the 12 films, kept locally; the method is in `tools/isoframes.py`. Note 06's stillness measure (480×270, mean adjacent difference under 0.3/255) differs from this one, so the numbers do not compare.
