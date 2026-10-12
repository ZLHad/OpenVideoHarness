# 07 · Does the film move? Still stretches, cuts that flash, periodic motion, found by the tools first

*Recorded 2026-10-12 · Status: the checks went into `bin/vh check` in this note's PR, all as warnings; the maintainer films are the author's local files, not in the repo, and their details are not given here · [中文](../07-motion-checks.md)*

## Question

Three kinds of fault used to be seen by a reviewer or a person, never by the tools: still stretches (research 06's reviewer scored "variety" 4 for two films whose middles stood still), a hard cut from a dark picture to a pale one that read as a flash, and a periodic bounce whose still point fell on one frame a cycle, which the isolated-frame scan reported as a string of glitches (both in a maintainer film). Can the decode `bin/vh check` already does (192×108 grey, every frame) measure these too, catching the cases above without false alarms on the showcase?

## Method

- `tools/isoframes.py --motion`, from the same decode: per frame pair the share of pixels changed by more than 12 levels, the mean change, the mean brightness, and the share changed by more than 6 levels a second apart.
  - Hard cut: over 30 % of the pixels change by more than 12 levels, the mean change is over 18 and over 3× the median of the 10 frames around it. A cut after which the brightest of the next 3 frames is at least 170 of 255 and over 90 above the mean of the 3 before is listed as a flash (a one-frame white flash between two dark shots too).
  - Still: under 0.2 % of the pixels change by more than 6 levels from one frame to the next (grain averages away at this size). Runs of 2 s or more count towards a still share; runs of 3 s or more are listed, as frozen (no change a second apart either) or a slow drift. A run with under 2 % of its pixels above 25 of 255 is black and left to blackdetect; a formula held on black is not black.
  - Periodic: four or more isolated frames evenly spaced (within one frame, 4 frames to 2 s apart), each small (at most 25 % of the picture) and alike, are periodic motion, not glitches; not looked for above 50 isolated frames.
  - Jump inside a shot: a frame-to-frame change over 8× the shot's median and over 6 levels (0.35 s after a cut and cut-sized changes left out).
- Films: the local finals of the showcase 00–04 projects (not checked against the release copies), research 06's four films, three maintainer films (landscape, narrated, several to over ten minutes each).

## Findings

| Film | Length | Moving pairs | Hard cuts | Still share (≥ 2 s) | Still runs ≥ 3 s | Flash cuts | Periodic | Largest jump |
|---|---|---|---|---|---|---|---|---|
| showcase 00 | 20 s | 41% | 0 | 0% | 0 | 0 | 0 | 12× |
| showcase 01 | 12 s | 98% | 4 | 0% | 0 | 0 | 0 | 10× |
| showcase 02 | 25 s | 54% | 0 | 0% | 0 | 0 | 0 | — |
| showcase 03 | 25 s | 24% | 0 | 24% | 1 | 0 | 0 | — |
| showcase 04 | 103 s | 80% | 18 | 0% | 0 | 1 | 0 | 25× |
| 06 · milky way A | 30 s | 31% | 0 | 48% | 3 | 0 | 0 | — |
| 06 · milky way B | 30 s | 10% | 0 | 29% | 1 | 0 | 0 | — |
| 06 · bakery A | 20 s | 33% | 0 | 41% | 1 | 0 | 0 | — |
| 06 · bakery B | 20 s | 15% | 0 | 50% | 3 | 0 | 0 | — |

1. One still run on the showcase, showcase 03's title formula held on black at 1.00–4.10 s (black before 2.77 s), a designed hold; all four 06 films have them, both B films listed (slow drifts). As in note 06, the A films are no less still than the B ones: this measures standing still, not which group is better.
2. The three maintainer films (not in the table; their details stay local) stand still more than the showcase, mostly in 2–3 s holds while the narration speaks; runs of 3 s or more are far fewer, more in the slowest film. So runs are listed from 3 s, and 2 s ones only count towards the share.
3. Two flashes found: in one long film, a hard cut from a darker scene to a nearly blank pale picture (the mean brightness jumps by about 100 levels), and showcase 04's designed one-frame white flash at 8.00 s (120 → 227). The film in the question had its flashes fixed (faded in from dark) before release, and none is reported.
4. The string of frames in the question, one every half second, each changing a little over a tenth of the picture, is reported as periodic motion and no longer fails, without `--allow`. A whole-picture change every 30 s (like a broken chunk seam) and a flicker every 3 frames still fail.
5. The jumps found on the showcase were all designed (a line of text vanishing, a fast push), so the largest jump is only a number on the summary line.
6. Cost: on a long 1080p film the isolated-frame scan alone and with all of this took about the same, under 1 s per minute of film; the decode is the time.

## What changed

- `bin/vh check` runs the scan with `--motion`: a summary line, and a warning line each for still runs of 3 s or more and for flash cuts. The exit status does not change.
- Evenly spaced isolated frames are periodic motion, not failures; `--allow` takes spans (`12-15`).
- `playbook/03` §2: periodic motion under a quarter of the frame rate, as a smooth cosine; a hard cut from dark to bright reads as a flash.

## Limits

- The thresholds were read off these 12 films, not proven: 0.2 %, 6 levels, 3 s and 90 levels are first values. None becomes a failure: stillness and bright cuts are often designed.
- Stillness is pixels only: labels lighting up one by one on a still picture count as still.
- Only hard cuts are checked for flashes; a fast dissolve from dark to bright is not.
- Periodic motion needs four evenly spaced frames; a long cycle landing on its still point two or three times is still reported as glitches. Conversely, a renderer that breaks a small patch every half second would pass as periodic motion: the frames are still listed, look at them.

**Sources**: per-frame data from `isoframes.py --motion --json` and frame checks on the 12 films, kept locally; the method is in `tools/isoframes.py`. Note 06's stillness measure (480×270, mean adjacent difference under 0.3/255) differs from this one, so the numbers do not compare.
