# 01 · Voice, music and SFX levels: why the narration still got buried

*Written 2026-10-01 · Status: merged ([#21](https://github.com/ZLHad/OpenVideoHarness/pull/21)) · [中文](../01-mix-hierarchy.md)*

> **Current state (2026-10-01)**
>
> - **Landed**: [#21](https://github.com/ZLHad/OpenVideoHarness/pull/21) merged the prototype into the repo. The mixer is [`tools/audio/mix.py`](../../../tools/audio/mix.py) (`bin/vh mix … profile=explainer|short|promo|cartoon|mv|swatch`), the mix report is `qa mix` in [`tools/audio/qa.py`](../../../tools/audio/qa.py), and the usage and the numbers per profile are in the mixing section of [`playbook/04-audio.md`](../../../playbook/04-audio.md).
> - **Recomputed**: with the merged implementation, the VMR and the words at risk of row C below do not change: film 03 at 13.1 / 13.0 LU (median / worst line), film 02 at 11.5 / 11.2 LU, words at risk 3 of 46 and 1 of 26.
> - **Master**: it still defaults to `tp=-1.65`, 0.15 dB under −1.5 dBTP, but what the AAC encode does to the true peak depends on the content and the bitrate (+0.16 to +0.86 dB at 128k on four swatches in #21; −1.9 to +1.4 dB on the 28 new soundtracks in [#31](https://github.com/ZLHad/OpenVideoHarness/pull/31)), so 0.15 dB is not always enough. `styles/_swatch/render.sh` therefore measures the encoded mp4 and mixes again with a lower `tp` while it is over −1.5 dBTP (at most 3 times).
> - **Words at risk**: without word times the report only warns instead of failing (it works in 0.4 s chunks, which read 11 % on film 03 where the real words read 7 %).
> - **Pumping check**: with `--stems` it no longer counts the score's own dips.

## Question

After `music_db` and `duck_ratio` were tuned by ear, 27–41 % of the words in our narrated showcase films still had a 1–4 kHz signal-to-noise ratio under 6 dB. Which levels was nobody in charge of?

## Setup

- **Material**: four showcase films (`showcase/03-math-fourier`: English narration, explainer; `02-short-leo-doppler`: Chinese narration, short; `00-promo-launch-film` and `01-handdrawn-clawd-leaf`: no narration; called 03, 02, 00 and 01 below) and four 5 s style swatches (music plus foley).
- **Three versions**: **A** is what we had (the three buses rebuilt from each film's build; for the two narrated films the rebuild differs from the shipped mix by −39.5 and −36.2 dB); **B** is the obvious fix applied to 03 only, music 3 dB lower (`music_db` −5 → −8); **C** is the prototype `mix_layers.py` (now `tools/audio/mix.py`) with a per-film profile.
- **Meter**: `mix_report.py` (now `bin/vh qa mix`), BS.1770 K-weighted loudness in LU, computed with numpy and scipy (ffmpeg only decodes), 1–2 s for a 30 s film, deterministic:
  - **anchor**: the median loudness of the narration lines; with no narration, the music's 3 s short-term loudness, floored at its integrated loudness minus 8 LU.
  - **VMR** (voice-to-music ratio): a line's voice loudness minus the music's loudness over the same span.
  - **words at risk**: word times from a local Whisper on the script; a word whose 1–4 kHz SNR against music plus SFX is under 6 dB is at risk.
  - **rise in pauses**: the music's loudness inside a pause minus the average music loudness under the two neighbouring lines.
  - It also reports every SFX event against the anchor, the local bed and the voice, the width and correlation of each bus, and what the limiter took.
- **Commands** (prototype scripts, not in the repo; in the repo the equivalent is the first code block of the mixing section in [`playbook/04-audio.md`](../../../playbook/04-audio.md)):

```bash
uv run --with numpy --with scipy python mix_layers.py OUT --profile explainer --voice vo.flac --music music.wav \
    --events events.json --sfx-lib sfx/ --timeline timeline.en.json --dur 25 --fade 0.5
uv run --with numpy --with scipy python mix_report.py --stems OUT --profile explainer --timeline timeline.en.json --words words.json
```

Sources: the mix lab's design brief, the build scripts of versions A, B and C, and the fit log from rebuilding the A buses (the residuals for the two narrated films and for cutout-jazz). These are files of the lab and are not in the repo. The metrics are defined and implemented in the header of [`tools/audio/qa.py`](../../../tools/audio/qa.py) (`qa mix`; [#21](https://github.com/ZLHad/OpenVideoHarness/pull/21), ported from the lab's `mix_report.py`).

## Findings

**1. The narration sits too close to the music, and not equally close on every line.** Film 03 version A has 6 lines under the 9 LU hard floor and 19 of 46 words under 6 dB: 7 hard failures. Its worst line is only 4.9 LU above the music; film 02's worst is 1.3 LU.

| film · version | VMR median / worst line (LU) | words at risk | spread of line loudness | music rise in pauses (median) | hard failures |
|---|---|---|---|---|---|
| 03 A as built | 8.3 / 4.9 | 41 % (19/46) | 5.4 LU | +6.0 LU | 7 |
| 03 B music −3 dB | 11.3 / 7.9 | 24 % (11/46) | 5.4 LU | +6.0 LU | 3 |
| 03 C layered | 13.1 / 13.0 | 7 % (3/46) | 2.2 LU | +3.4 LU | 0 |
| 02 A as built | 7.9 / 1.3 | 27 % (7/26) | 3.8 LU | +6.1 LU | 7 |
| 02 C layered | 11.5 / 11.2 | 4 % (1/26) | 1.4 LU | +2.3 LU | 0 |

![Film 03 fourier, versions A, B and C: 400 ms loudness of voice, music and SFX, and the VMR of each narration line](../figs/01-fourier-abc.png)

*Figure 1 · 03 fourier (25 s, English narration): 400 ms loudness of voice (blue), music (orange) and SFX (green); bottom, the VMR of each line (grey band: target 11–18 LU; red dashed line: 9 LU hard floor).*

**2. Turning the music down fixes only half of it.** B lifts the median VMR to 11.3 but the worst line is still 7.9 and 3 checks still fail: the narration's own loudness differs by 5.4 LU from line to line, and a global fader cannot touch that. C first pulls the lines toward their median (the `mix_layers` log says 5.5 → 2.2 LU, with per-line gains between −1.5 and +1.8 dB), then solves how far to duck the music under each line (2.0 to 6.3 dB in 03). The last six lines land at 13.0–13.2 LU; the first two are higher (16.9 and 13.9) because the duck depth has a 2.0 dB floor and the music is quiet there anyway.

**3. The music comes back up in the pauses.** The ducker is `sidechaincompress=threshold=0.02:ratio=1.6:attack=15:release=350`: 350 ms after a line ends the music is on its way up. In version A the music in pauses sits only 3.2 LU (03) and 2.3 LU (02) below the narration's median level; in 02, during the 22.17–22.85 s pause, it is 2.6 LU above it. In C the same figure is −10.4 and −8.9 LU.

**4. SFX are not uniformly loud, they have no order.** In 00 the detail sounds reach +2.0 LU and the hero sounds +3.7 LU over the music around them; in 01, inside a gap in the music, +6.0 and +7.9 (after C: −0.7 and +0.7 in 00, +0.8 and +3.8 in 01). Across four 5 s swatches the median foley level relative to the music runs from −5.7 to −21.8 LU, a spread of 16.0 LU (the detail sounds of pixel-16bit and monumental-scifi sit near −20 LU, essentially under the music). After C the spread is 6.1 LU.

![Every SFX event of four 5 s swatches against the anchor, A versus C, with the detail and hero target bands](../figs/01-swatch-foley-levels.png)

*Figure 2 · the level of every foley event of four 5 s swatches against the anchor (59 per version): the bar is the median, the green and orange bands are the detail and hero ranges, on the right the spread of the four medians.*

**5. Only two depth planes.** `tools/audio/mix.py` as it was before #21 has no reverb, so voice and SFX are dry by construction and all space comes from the score itself (direct-to-reverberant ratio of the four scores: 14.0 dB for 00, 8.2 for 01, 10.4 for 02, 6.8 for 03; lower is wetter). In version A of 03 the voice and SFX buses are mono (L/R correlation 1.00); in 01 the music and SFX buses are equally wide (side/mid −11.6 and −11.7 dB).

![Film 02 doppler, versions A and C: Chinese narration, VMR per line](../figs/01-doppler-ac.png)

*Figure 3 · 02 doppler (24.8 s, Chinese narration), A against C; for Chinese the carve also takes 250 Hz–1 kHz (`body_share` 0.6), because the tone information lives there too.*

Sources: the mix reports of versions A, B and C (every figure in the table, the pause numbers in point 3, the words at risk, the per-event levels of Figure 2), the prototype's run logs (per-line gains and duck depths) and the DRR measurement of the four scores. They are outputs of the mix lab and are not in the repo; the C figures were recomputed with the merged implementation in #21 and agree (see "Current state"). Section [6] depth of `qa mix` also reports a dry/wet ratio per bus, which is not necessarily the same measure as the DRR here. The ducker settings are those of the default chain in [`tools/audio/mix.py`](../../../tools/audio/mix.py). Figures 1 and 3 are the lab's originals scaled down; Figure 2 is redrawn from the per-event data in the reports.

## What we changed because of it

### Design: how C orders the levels

Everything is set relative to one anchor, in this order: **voice → music VMR → SFX classes → depth → master**.

- **Voice**: 80 Hz high-pass; each line moves 60 % of the way to the median, capped at ±3 dB; peaks stay within anchor + 10.5 dB.
- **Music**: a per-line look-ahead fader ride, not a compressor. It starts 0.15 s early, keeps half of the duck in pauses shorter than 1.5 s, and solves each line's duck depth in a closed loop until the line reaches the profile's VMR (explainer: target 13, floor 11, ceiling 18 LU). A 1–4 kHz carve then cuts only as deep as the words need, at most 7 dB.
- **SFX**: each event is classed hero, detail, ambience or signal (by `role`, or by a hint in its name) and moves half way to its class centre, staying 0.5 LU inside the range; one gesture, or a burst within 0.2 s, moves as a unit; events with more than 60 % of their energy in the lows are never raised; a class moves at most ±9 dB. All SFX share one short room (RT60 0.25–0.3 s).
- **Master**: one static gain, then a numpy look-ahead true-peak limiter, leaving 0.15 dB for the AAC encode.

This also removes the `sidechaincompress` end-of-file problem (see [note 03](03-render-determinism.md)).

Sources: the mix lab's design brief, and the header and `PROFILES` of the prototype `mix_layers.py`; in the repo these are the header and `PROFILES` of [`tools/audio/mix.py`](../../../tools/audio/mix.py), and the numbers per profile are in the mixing section of [`playbook/04-audio.md`](../../../playbook/04-audio.md).

### What is in the repo

- [#2](https://github.com/ZLHad/OpenVideoHarness/pull/2): the default `duck_ratio` went from 6 to 1.6 (same narration at three ratios; qa pumping: 3 dips, 2 dips, 0). That was a knob-level fix; the numbers above show why a knob is not enough.
- [#15](https://github.com/ZLHad/OpenVideoHarness/pull/15): `bin/vh mix` made deterministic (twelve runs of one command used to give six different files).
- [#21](https://github.com/ZLHad/OpenVideoHarness/pull/21): mix profiles, `bin/vh mix … profile=explainer|short|promo|cartoon|mv|swatch`; `bin/vh qa mix`, which reads the buses and exits 1 when a hard target fails; `bin/vh sfx` takes a `role` per event and writes an `events.json` sidecar; `styles/_swatch/render.sh` mixes with `profile=swatch`. On the eight test mixes the port reproduces the prototype byte for byte at the prototype's last `lufs` / `tp`; at the product defaults (`lufs=-14`, `tp=-1.65`) every relative metric is the same and only the master gain and the limiter differ.
- Docs in the same PR: the mixing section of [`playbook/04-audio.md`](../../../playbook/04-audio.md) is rewritten in this order, with the numbers per profile.

Sources: the descriptions of PR #2, #15 and #21.

## Limits and open questions

- **No listening verdict.** The files hold no listening record for A/B/C; every number here is a meter reading, not an ear.
- **Small sample**: two narrated films (about 25 s each) and four swatches; the A buses are rebuilt, not exported (the cutout-jazz rebuild differs by only −18.6 dB, where the limiter works hardest).
- **The targets are design choices.** Numbers like 13 and 11.5 LU were not calibrated by listening. For reference, the UK DPP delivery spec recommends at least 4 LU between dialogue and background, and a study reports that commentary over music needs at least 10 LU (Torcoli et al., 2019; only the abstract is in our research notes).
- **Warnings that remain in C**: in 02 the music still rises by more than 5 LU in the 5.09–6.45 s and 22.17–22.85 s pauses; two sonification sounds in 03 (10.2 s, 12.5 s) still have 1–4 kHz energy close to the voice's; the hero at 18.97 s in 02 has 99 % of its energy under 150 Hz and is weak on phones. Gain cannot fix the lows; that needs sound design (`bin/vh sfx` now adds a 1–4 kHz crack to impact and boom).
- **The ±9 dB cap leaves a tail**: monumental-scifi's detail sounds end at −13.1 LU, still under the −11…−4 range.
- The pumping check in `bin/vh qa` (4 dB / 60 ms) is touchy: one false positive at 8.45 s in 01. Whether the lowest FFT bits agree across platforms is unverified. loudnorm and ebur128 differ by 0.2 LU on 03's mp4 (−14.0 against −13.8), so the master is gated on the BS.1770 meter.

Sources: the lab's list of risks and the warnings in the A/B/C reports, and the lab's reading notes (the DPP and Torcoli references are abstracts only); none of this is in the repo. The same kinds of warning are now raised by `qa mix`, and the known limits are listed at the end of the mixing section of [`playbook/04-audio.md`](../../../playbook/04-audio.md) under "局限" (limits).
