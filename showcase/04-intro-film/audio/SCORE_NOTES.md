# SCORE_NOTES: intro film score

## v3 (26 bars, 2026-09-29; archived in `audio/v3-26bar/`, superseded by v3.1 at the end of this file)

The user's notes on v2 were that the music "stutters or disappears in places" and the film is "not cool enough". v2 is archived in `out/v2/`. v3 keeps 90 BPM, 26 bars / 69.333 s, the section boundaries and every picture hit (braam, impacts, router, FAIL/PASS, stems, Fourier, Doppler, gate approvals). Two renders give the same MD5 (`a022edb5…`), and a render takes about 12 s.

**What was fixed**

- **No stops.** Each former stop (26.000, 34.000, 36.667, 44.667, one beat each) is now a *hold*, a held breath:
  - a button hit (taiko ensemble + snare) on its first sample (new transient hits `hold:drop`, `gate1:hold`, `gate2:hold`, `gate3:hold`);
  - the drums drop out;
  - the synth bass and ostinato cutoffs sweep down (factor (1 − 0.85u)², floor 0.12);
  - pad and sub keep sounding;
  - a riser and reverse swell land on the next downbeat.

  The beat map has `"stops": []` and a `holds` list.
- **No bus pumping.** The kick sidechain touches only the synth bass and the ostinato (−3.5 dB, 100 ms recovery). The pad, sub, drone, keys, drums and reverbs are never ducked, and the ducks on impacts, braam and FAIL hits are gone.
- **No clicks.** Every placed sound gets a 2 ms fade-in and a 5 ms fade-out. The synth bass is one phase-continuous oscillator whose 16th envelope and accent have 3 ms attacks. v2 had two real click sources, both fixed: the bass envelope step, and the Fourier bar's per-beat re-articulation step.
- **Hook at 0.1667** (hit `spark`): spark sine + FM bell D6 + celesta D5 + a short sub hit (90→40 Hz). A rising 16th pulse enters at 1:2. The prologue now sits at −17.5 (hook peak) and −22 to −20 LUFS momentary, instead of −30 to −40.
- **Bar 22** is a filtered build rather than a vanishing band: kick on quarters rising, synth bass and ostinato opening 250→1200 / 400→2000 Hz, a snare pickup, and a riser into the reveal at 58.667.
- **Bar 23** is a breakdown with the pad, sub and a soft filtered pulse, so there is no hole.

**What was added**

- **Low end and drums:**
  - a driving 16th synth bass in S2–S5 (saw + sine, filter pluck, drive, sidechained);
  - a taiko ensemble (70→40, 105→62, 140→85 Hz, spread L/R);
  - a trailer snare;
  - hi-hats: 16ths from 28.0 and in S5, with 32nd ratchets as fills;
  - a sub drop (70→30 Hz) under every impact, including the soft one at 5.333.
- **Whips:** a riser or reverse swell lands on each whip downbeat: bars 3, 5, 9, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23 and 25. These are swell-peak hits `whipN`, `gateN`, `braam`, `reveal`, `title` etc.
- **S3 build:** taiko 8ths, then 16ths, a snare roll, hats; the riser runs 21.333→26.667 and peaks into the braam.
- **Removed:** the v2 glitch stutters in bar 9 (hits `glitch:1–3` are gone), because they are exactly what "stutters" sounds like.

**v3 numbers**

- **Loudness (ffmpeg ebur128):** −14.5 LUFS integrated, LRA 10.0 LU, true peak −2.0 dBTP. The limiter's maximum gain reduction is 5.1 dB, at the braam.
- **Holes (`check/mixcheck.txt`):** 0 violations. Lowest 0.1 s window vs its section median, 1.0–66.5 s:
  - −2.4 to −3.9 dB in every section;
  - −10.4 dB in the title ring-out.
- **Silent runs:** only 0–0.080 s (before the hook) and the tail from 68.925 s.
- **Pumping:** largest dip of the 150 ms RMS below its ±0.5 s median is 3.0 dB; nothing over 4 dB.
- **Clicks:** no HF (>10 kHz) spike above −50 dBFS and 24 dB over its local level, except within 40 ms after a placed sound's start. There are 923 placed sounds, logged in `check/placements.json`.
- **Cue check:** 92/92 within 1 frame. Onsets: median 10.7 ms, max 17.4 ms. The 21 swell-peak hits land within 29 ms (0.9 frame) of their targets.
- **Mean momentary loudness per bar, 1–26** (LUFS; bar 1 is the hook): −20.9, −22, −21, −20, −18, −17, −17, −15.5, −14, −12.7, −10.9, −11.2, −14.1, −13.4, −15.5, −14.4, −13.6, −11.7, −12.2, −12.4, −13.0, −16.5, −21.2, −14.5, −18.0, −33 (fade).

**Compromises in v3**

- **The braam is the loudest moment, but only by 0.4–1 LU** (max momentary −10.1 vs −10.5 in bar 12 and −10.9 in bars 19–20). The limiter already takes 5 dB at the braam. The SFX boom planned at 26.667 has to carry the extra weight.
- **The title impact (64.0) peaks at −12.8 LUFS**, level with the bar-24 build (−12.7). The SFX impact at 64.0 is needed there too.
- **Bar 20 (Fourier).** Each new harmonic arrives at 0.8× the fundamental's level and settles to 1/k, and the lead re-articulates on every beat (accent 0.8). The lead is up 3 dB and the pad down 3 dB so the entry at 51.333 reads as an onset; in v2 the detector only "heard" it through a click. For a strictly 1/k build set `spotlight` to 0; the entry at 51.333 then fails the onset check.

On-screen code (`onscreen-code.txt`), in order kick / bass / hats / lead: engine lines 731, 395, 411 and 368, each 43–60 characters.
- kick = the lead taiko of the ensemble;
- bass = the 16th synth bass line;
- hats = the 808-style hi-hat;
- lead = the additive lead.

The sections below describe v2 and are kept as history.

---

A cinematic hybrid score, composed as code: `score.json` holds the arrangement as data and `score_engine.py` synthesises it. The engine is an extended copy of `tools/audio/music.py`; the shared file is untouched.

- **Grid:** 90 BPM, 4/4, D minor, 26 bars. Output is stereo, 48 kHz, 16-bit, exactly 3 328 000 samples (69.3333 s).
- **Deterministic:** two renders give the same MD5 (`b1ff54fc…`).
- **Speed:** a render takes about 7 s on the M3 Max.

```bash
uv run -q --with numpy --with scipy python audio/score_engine.py audio/score.json audio/music.wav [--stems DIR]
uv run -q --with numpy --with scipy --with matplotlib --with librosa \
    python audio/check_score.py audio/music.wav [--stems DIR] [--wave assets/wave.json]
```

## Sections

| # | bars · time (s) | chords | what plays |
|---|---|---|---|
| S1 prologue | 1–4 · 0.000–10.667 | Dm Dm B♭ B♭maj7 | high spark at 0.167 (1:1.25, the nearest 16th to the requested 0.2 s); D1+A1 sub drone fades in over 6 s; dark pad slowly opens (260→1100 Hz); seeded render ticks on 16ths from bar 2 (density 12 %→40 %); reverse swell into a **soft impact at 5.333**; reverse swell + metal "wake" ring into 10.667 |
| S2 program | 5–8 · 10.667–21.333 | Dm B♭ F C | 16th pulse ostinato (accents 3-3-2), filter opening 350→1700 Hz over the 4 bars; half-time taiko on 1 and 3; frame drum on 3; sub follows roots; celesta doubles the ostinato top in bars 7–8 |
| S3 problem | 9–10 · 21.333–26.667 | B♭ C | taiko in 8ths (bar 9), then 16ths (bar 10) with a crescendo; riser 21.333→26.000; ostinato stutters at 22.000 / 22.667 / 23.333; reverse swell into 26.000; **stop 26.000–26.667** |
| S4 harness | 11–17 · 26.667–45.333 | Dm B♭ F C Dm B♭ F | **bar 11:** braam + impact at 26.667, alone for 2 beats over taiko/pad/sub; ostinato, shaker and metal slam in at 28.000 (hit `groove`). **Bar 12 (router):** drums thinned to taiko on 1 and 3 plus shaker; ostinato lower and darker; 8 ascending celesta eighths D5→D6 (29.333…31.667) raised to −11. **Bars 13–14 (gates):** full groove, taiko push on the last 16th of beat 3, frame-drum pickup fill (16ths across beat 3, crescendo) into **stops 34.000–34.667 and 36.667–37.333**; clack + approval stab on 34.667 (C) and 37.333 (F over D). **Bars 15–16 (review hall):** half-time; taiko only on 1 (bar 15) and on 1 / 3 (bar 16); no frame drum, shaker or metal; ostinato filtered 550→1100 Hz with a post-drive low-pass at 1 kHz; darker pad (900→1500 Hz); FAIL clusters D2/D3/E♭3 at 38.000 / 38.667 / 39.333. At 42.000 it opens: reverse swell into a bright D-major PASS stab, a taiko on the beat, ostinato back to 2600 Hz, shaker back. **Bar 17 (gate ③):** taiko 8ths → 16ths crescendo, frame fill on beat 3, riser 42.667→44.667 raised to −12, into **stop 44.667–45.333** |
| S5 proof | 18–22 · 45.333–58.667 | B♭ C D5 F Dm | **Bar 18:** big impact + clack + B♭ stab at 45.333; full groove; lead theme D5 (3 beats), C5. **Bar 19 (Clawd):** light, no taiko; soft frame-drum pattern, shaker and ostinato in 8ths, sub −4 dB; celesta arpeggio in 16ths (C E G D) raised to −12. **Bar 20 (Fourier):** kick (taiko) on 1 and 3 only; no shaker, frame or ostinato; pad −4 dB, open fifths. The additive lead on A4 adds harmonics 1 / 3 / 5 / 7 on each beat (50.667 / 51.333 / 52.000 / 52.667); each new harmonic arrives at 0.6× the fundamental's level and settles to 1/k over 0.3 s, with a small re-articulation on each beat. **Bar 21 (Doppler):** full drums (taiko, frame on 2 and 4, shaker, metal on 4) under a physical Doppler pass on A4 (+80 → −80 cents S-curve, 1/r level, panned L→R). **Bar 22:** band out, 4 soft projector ticks on the beats, sub tail and reverb decay |
| S6 reveal | 23–24 · 58.667–64.000 | B♭maj7 C | a soft swell lands on the pad-only bar 23; stems enter one per beat in bar 24: taiko 61.333, bass (sub + ostinato) 62.000, shaker 62.667, lead E5 63.333 (it becomes the add9 of the final chord); riser + reverse swell into 64.000 |
| S7 title | 25–26 · 64.000–69.333 | Dm(add9) | **final impact at 64.000** + a Dm(add9) chord voiced D2-A2-E3 (stacked open fifths) under A3 F4 A4 D5; a pad closing 2400→500 Hz; the spark returns; quiet typing ticks on 16ths 66.667–67.833; cosine fade from 66.667, digital silence from 68.95 |

## Instruments (all synthesised and seeded)

- **Sub drone and sub bass.** Sine plus 0.25 × 2nd harmonic, with slow 0.09–0.14 Hz swells and gentle tanh saturation. The bass is one phase-continuous oscillator that follows the chord roots (D1…C2), always mono.
- **Pad.** 5 notes × 5 detuned saws (±14 cents), each voice panned across the field. Then a high-pass at 100 Hz, −3.5 dB at 220 Hz, and a 4-pole low-pass automated per section with a 0.06 Hz drift.
- **Pulse ostinato.** Two band-limited saws (±7 cents, L/R), a filter "pluck" made of two decays, and tanh drive.
- **Taiko.** Sine gliding 70→40 Hz, skin noise (90–500 Hz) and a stick click, mono.
- **Frame drum.** Band-passed noise head plus a 175 Hz body, through a 0.35 s room.
- **Metal.** 7 inharmonic partials. The clack is the same model, high and short.
- **Shaker.** Noise band-passed 6–11 kHz, alternating L/R, with an accent pattern.
- **Risers.** Noise through an opening sweep, plus a D3→D6 tone.
- **Reverse swells.** A chord's hall tail, reversed, pre-delay removed, shaped to peak on its last sample.
- **Impacts.** Sub boom with a pitch drop (100→34 Hz) plus a stereo noise burst; 3 sizes.
- **Braam** (used once).
  - Detuned saws on D1 D2 F2 A2, with a 35-cent brass "blat".
  - A resonant 4-pole low-pass that opens 200→2500 Hz in about 0.1 s, then closes to about 250 Hz over about 3 s.
  - tanh saturation. The D1 layer decays in about 0.6 s.
- **Celesta.** Fundamental, a weak octave, and short partials at 4.16× and 6.9×.
- **Additive lead.** `sum(sin(k·ph)/k)` over odd k, each harmonic with its own entry gate. The same timbre carries the theme, the Fourier bar, the Doppler pass and the bar-24 entrance.
- **Mix.**
  - Stereo stems with per-event pan and sends.
  - Two decorrelated noise-IR reverbs (hall RT60 4.2 s, plate 2.6 s, different seeds for L/R); the sends are high-passed at 180 Hz so the low end stays dry and mono.
  - Sidechain-style ducking of pad/pulse/sub on taiko hits and impacts.
  - Stops as a full-mix mask with 5 ms fades, applied after the reverbs.
  - A 30 Hz 4th-order master high-pass.
  - Loudness targeting to −15.5 LUFS, a look-ahead limiter (−1.5 dBFS, 150 ms release), then a true-peak trim.

On-screen code (`onscreen-code.txt`) is 4 verbatim lines of `score_engine.py`, in order kick (line 620), bass (566), hats (271) and lead (363), each 41–54 characters.

## Numbers

**Loudness** (`ffmpeg -af ebur128=peak=true`):
- Integrated −15.5 LUFS, LRA 13.9 LU (low −25.1 / high −11.3), true peak −1.3 dBTP.
- The engine's own BS.1770 gives −15.54 LUFS and −1.34 dBTP. The limiter's maximum gain reduction is 3.4 dB, at the braam.

**Momentary loudness** at the key moments:

| moment | momentary loudness |
|---|---|
| braam (27.2 s) | −9.3 LUFS |
| bar-12 groove | −10.5 to −11 LUFS |
| impact:hall | about −12 LUFS |
| title impact (64.2 s) | −12.8 LUFS |
| bar-24 build | −15 LUFS |

**Short-term loudness by section:**

| section | LUFS |
|---|---|
| prologue | about −25 |
| program | −22 → −20 |
| problem | −19 → −16 |
| harness | −10.5 to −16.5 |
| proof | −12 to −14 |

**Momentary loudness per bar, bars 11–22** (mean LUFS; gate bars include their silent beat):

| bar | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LUFS | −10.3 | −11.1 | −15.7 | −14.9 | −17.9 | −15.7 | −16.0 | −12.5 | −12.0 | −13.8 | −13.8 | −29.2 |
| bar 22 | falls away (near-silence, intended) |
| bar 23 | about −26 |
| title | about −16, decaying |

**Cue check** (`check/cuecheck.txt`): 79 of 79 hits are within 1 frame.
- **Onset hits:** librosa onsets, hop 5.3 ms. Median |error| 10.6 ms, max 17.4 ms (0.52 frame). The errors are all positive, which is librosa's usual detection lag, not placement: every hit is placed on an exact sample (beat = 32 000 samples).
- **Swell and riser peaks:** 11 hits, measured on the fx stem. They peak 6–16 ms before their target.

**Stops:** every window is digital silence (RMS −240 dBFS). A scan of the whole file for silent runs (5 ms RMS < −60 dBFS, ≥ 20 ms) finds exactly these:

| silent run (s) | what it is |
|---|---|
| 0.000–0.165 | before the spark |
| 26.000–26.665 | stop |
| 34.000–34.665 | stop |
| 36.670–37.330 | stop |
| 44.670–45.330 | stop |
| 68.935–69.333 | tail, 0.40 s |

Nothing else in the file is silent.

**`assets/wave.json`:** 400 linear-RMS bins over 0–69.333 s, normalised to 0..1 (the stop windows read 0).

## Changes after the coordinator's mix QA (2026-09-29)

- A 30 Hz 4th-order master high-pass.
- Sub/drone 4–6 dB lower outside S4/S5 (prologue drone −20, S2 −18, S3 −16, bar 24 −15, title −16 with a 1.5 s decay).
- Impact booms shortened (tau 0.5 / 0.7 / 0.9 s) and ending at 34–36 Hz; the braam's D1 layer made a 0.6 s burst.
- Pad high-passed at 100 Hz with a −3.5 dB dip at 220 Hz. Its level was then raised about 7 dB, because at −34 LUFS it was inaudible under the pulse.
- The coordinator's reported silences near 26.2 / 34.9 / 36.8 / 45.3 s are not in this file; the measured windows are listed above.

## Refinement pass (coordinator request, 2026-09-29): S4/S5 groove variation

- **Picture sync unchanged.** Hit times, kinds, stops, beats, sections, length and `hits_note` in `music.beats.json` are identical to the previous version, checked by a JSON diff.
- **Untouched sections.** S1–S3, S6 and S7 match the previous render apart from a +0.28 dB master-gain shift (residual −71 to −81 dB).
- **Bar 11.** Same patterns and levels as before, but different noise draws: its layers were split, and the seeds are keyed by layer index.
- **Engine additions:**
  - layer `until` (end a layer mid-bar);
  - frame-drum accents (`X` accent, `x` ghost at −6 dB; the S2/S3 patterns were switched to `X` so they stay identical);
  - pulse `post_lp` (a low-pass after the drive; without it the tanh regenerates the highs and "filtered down" doesn't sound darker);
  - lead `spotlight` / Fourier `accent`;
  - `kind` + `hits_note` are now written by the engine.
- **Cue-check fixes.** Two cues lost their detected onsets once the drums thinned out:
  - the music-box 16ths (fixed by raising the celesta 3 dB);
  - the 7th harmonic at 52.667 (fixed by the spotlight: each new harmonic arrives at 0.6× the fundamental's level, then settles to 1/k).

## Unsure / weakest

1. **The drop is only about +2 LU above the groove that follows.** The braam is limiter-bound: more gain only adds gain reduction. Its size comes from the 0.667 s silence before it, the 2 beats it plays alone, and its spectrum. If the film needs more, add weight in the SFX layer at 26.667, or let the final mix limit harder there.
2. **The prologue drone (D1 36.7 Hz) is still the largest single band in S1** (20–60 Hz ≈ 37 % of the power), although it sits at −20 dB and under the 30 Hz high-pass. On laptop and phone speakers the prologue is carried by the pad, spark and ticks. If it still reads as rumble on headphones, pull D1 down and keep A1.
3. **Groove variation (addressed in the refinement pass).** Every bar from 12 to 22 now has its own drum and ostinato treatment. What remains:
   - The gate bars 13–14 still sit about 4–5 LU under the router bar 12, which carries the braam's hall tail and the bright plucks. Lifting their groove 2 dB moved them only about +0.7 LU, because ducking and the loudness re-normalisation absorb it.
   - The Fourier bar's harmonic "spotlight" is a design choice: each new term pings in at 0.6× the fundamental before settling. If the film wants a strictly mathematical build (partials entering at exactly 1/k), set `spotlight` to 0. The onset at 52.667 is then weaker (it was undetected before the spotlight).

---

## v3.1 (30 bars, 80 s; archived in `audio/v3.1-80s/`, superseded by v3.2 below)

Re-arranged to the new 30-bar picture (90 BPM, 80.000 s = 3,840,000 samples). The 26-bar v3 is archived in `audio/v3-26bar/` (score.json, music.wav, music.beats.json, SCORE_NOTES.md). Two renders give the same MD5 (`f62ac174…`).

**Kept from v3:** the same palette, holds instead of stops (pad and sub keep sounding), the kick sidechain on the synth bass and ostinato only, 2 ms / 5 ms edge fades, the transient / swell-peak `kind` convention and a pre-master level of −14.5 LUFS.

**Structure and chords**

| bars | section | chords |
|---|---|---|
| 1–3 | prologue | Dm Dm B♭ |
| 4–6 | program | Dm B♭ F |
| 7–8 | problem | B♭ C |
| 9 | braam | Dm |
| 10–13 | architecture | B♭ F C Dm |
| 14–18 | pipeline | B♭ F Dm B♭ D (bar 18 is the D-major lift) |
| 19–21 | features | B♭ F C |
| 22 | cases | Dm |
| 23–26 | proof | B♭ C D5 F |
| 27–28 | reveal | B♭maj7 C |
| 29–30 | title | Dm9 Dm9 |

Holds: 8:4→9:1, 14:4→15:1, 15:4→16:1 and 18:3→19:1. The last one is the "final" node: a D(add9) chord sustains for 2 beats under a soft button, and a whoosh (riser) lands on 19:1.

**New sounds and engine features**
- Per-repeat labels (`labels` on an event).
- A typing layer (code typing on 16ths in bar 5).
- An FM-bell event for module and feature landings.
- `ring` on stabs (a metal ring for the bigger landings: arch:router, mod:projects, pipe:start, pass, scaffold).
- A Fourier bar with a selectable harmonic set (now h1 / h3 / h5 at 24:4, 25:1, 25:2).
- A formant "ah" vowel blip (sound:voice), a typewriter tick (sound:captions), a stab (sound:score) and a pop + swish (sound:sfx).
- A 48-point star burst for "stars" at 22:1, then an 11-note celesta arpeggio (cases:1–11).
- Swells: the reverse-swell grow curve is now cubic, so swells lean harder into their target.
- The beat map carries a `fade` window, and the checks use it.

**Bar-specific treatment**
- Bar 11 (types) thins the drums.
- Bar 17 (read-heavy line) keeps a half-time groove with the ostinato at 700 Hz, post-drive low-pass 900 Hz, pad −4 dB and no lead, so the mids stay clear.
- Bar 20 (sound demos) thins the groove.
- Bar 24 (musicbox) has frame drum only, no taiko.
- Doppler runs 25:3→26:1.75.
- Silent-film ticks at 26:2–26:4 sit over a filtered build into 27:1.

**v3.1 numbers**
- **Loudness (ffmpeg ebur128):** −14.5 LUFS integrated, LRA 9.0 LU, true peak −1.9 dBTP. The limiter's maximum gain reduction is 3.1 dB, at the braam.
- **Tail:** master fade 30:1 → 30:4.9 (77.333 → 79.933 s). The last non-zero sample is at 79.933 s.
- **Holes:** 0 violations over 1.0–77.167 s. The lowest window sits 1.1–6.4 dB under its section median, and 11.1 dB in the title ring-out.
- **Silent runs:** only 0–0.080 s (before the hook) and 79.83 s → end.
- **Pumping:** largest dip 3.6 dB, nothing over 4 dB.
- **Clicks:** 0 unexplained HF spikes across 1,212 placed sounds.
- **Cue check:** 143/143 within 1 frame (worst 20.3 ms; onsets median 10.7 ms, max 16.0 ms). All 128 labels requested by the director are present at their exact times.
- **Mean / max momentary loudness per bar (LUFS):**

  | bars | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | mean / max | −21 / −17.6 | −22.5 / −20.8 | −20.6 / −17.9 | −22 / −20.2 | −16.8 / −15 | −15.2 / −13.7 | −15 / −13.9 | −13 / −11.6 | −11.3 / −10.4 (braam) | −12.6 / −11.4 |

  | bars | 11 | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | mean / max | −13.4 / −12.6 | −12.8 / −11.8 | −14.4 / −13.5 | −13.7 / −12.4 | −14.2 / −13.4 | −14.9 / −14 | −15.8 / −15 | −14.1 / −13.6 | −13.7 / −12 | −16.1 / −14.4 |

  | bars | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 |
  |---|---|---|---|---|---|---|---|---|---|---|
  | mean / max | −13.5 / −12.2 | −13.4 / −12.6 | −12.1 / −11.6 | −12.2 / −11.2 | −13.6 / −11.7 | −15.9 / −14.6 | −17.7 / −13.3 | −15.1 / −12.9 | −16.9 / −12.5 | −31.6 (fade) |

**v3.1 notes and compromises**
- **The braam bar is the loudest** (max −10.4 vs −11.2 to −11.8 elsewhere), but only by about 1 LU; the SFX boom still carries the weight.
- **The title impact (29:1) peaks at −12.5 LUFS**, about level with the stems build.
- **Some labels were my own choice** where the brief gave only a time:
  - "film:tile2–4" for the scrambled tile plucks after "film";
  - "node:1–3" at 14:1.5 / 14:2 / 14:2.5;
  - "taste:1–3" at 19:2–19:4;
  - "curl:1–8" for the install typing, "enter" (21:3), "scaffold" (21:4);
  - "lead:theme-2" (23:4);
  - "swell>…" / "riser>…" peaks as before;
  - "reveal" at 27:1 is a transient bell over the `swell>reveal` breakdown swell.
- **Doppler ends at 26:1.75**, not after a full 3 beats as the brief's "(3 beats)" said, because the first silent-film tick is at 26:2.
- **On-screen code:** unchanged 4 verbatim lines, now at engine lines 767 395 411 368 (kick, bass, hats, lead).

---

## v3.2 (bar 11 in 6/4, 81.333 s; archived in `audio/v3.2/`, superseded by v3.3 below)

The coordinator found the "video-types/ · 8 video workflows" list was only fully lit for about 0.6 s, so bar 11 becomes a 6/4 bar. The 80 s v3.1 is archived in `audio/v3.1-80s/`. Two renders give the same MD5 (`7c659a46…`).

- **Engine:** `meters` in score.json (`{"11": 6}`) sets beats per bar (default 4). Bar starts are cumulative, `at("bar:beat")` follows them, and a 16-step pattern repeats if a bar is longer. The beat map lists every beat (122), gives the true downbeats, and adds `"bars": [[bar, start, beats], ...]`.
- **Bar 11, beats 1–4:** unchanged (types:1–8 on 8ths, drums thinned).
- **Bar 11, beats 5–6:** the groove and pad (F) continue, and there are no new labelled hits. The drums have 24-step patterns: a soft taiko on 11:5, then a push on 11:6 (taiko x.xX, snare 16ths xxXX, a hat ratchet). The whip12 swell peaks on 12:1 (30.667) together with mod:playbook.
- **Timing:** everything from 12:1 on keeps its bar:beat and moves +1.333 s: 12:1 = 30.667, 14:1 = 36.000, 29:1 = 76.000. Holds are now 20.667–21.333, 38.000–38.667, 40.667–41.333 and 48.000–49.333. The fade runs 30:1 → 30:4.9 (78.667 → 81.267 s), and the last non-zero sample is at 81.266 s.
- **Loudness:** −14.5 LUFS, LRA 8.9 LU, true peak −1.9 dBTP.
- **Cue check:** 143/143 hits within 1 frame (worst 20.3 ms). Every v3.1 label is present with the same kind at its expected time.
- **Mix checks (1.0–78.5 s):** 0 holes (lowest window 1.6–6.4 dB under its section median, 11.4 dB in the title ring-out); largest dip 3.3 dB; 0 clicks across 1,246 placed sounds. The only silent runs are 0–0.08 s and the tail from 81.165 s.

---

## v3.3 (cards on 8ths, a title bed that stays; archived in `audio/v3.3/`, superseded by v3.4 below)

Two changes after an independent review. v3.2 is archived in `audio/v3.2/`. Two renders give the same MD5 (`9c186c1b…`).

1. **Bar 12 cards on 8ths.** mod:playbook 12:1 (30.667), mod:templates 12:1.5 (31.000), mod:cases 12:2 (31.333) and mod:binvh 12:2.5 (31.667). Beats 12:3–12:4 carry the groove into 13:1 with no new labelled hits: a push on 12:4 (taiko x.xX, snare 16ths xxXX, hat ratchet on the last beat), the same gesture as 11:6. Nothing else moved; the hit list is identical to v3.2 apart from those three times.
2. **The ending no longer disappears.** The title pad (Dm9) is +7 dB and closes only to 1800 Hz instead of 500 Hz. The title chord decays with tau 8 s instead of 2.2 s and is 2 dB louder, and the sub holds steady at −15 (no decay). The master fade is now only the last 0.567 s (`30:4.05 → 30:4.9` = 80.700 → 81.267 s; the beat map's `fade` says so).

   | time (s) | v3.2 RMS (dBFS) | v3.3 RMS (dBFS) |
   |---|---|---|
   | 76.0 (title impact) | −13 | −12.9 |
   | 77.5 | −21.9 | −19.4 |
   | 78.5 | −27.5 | −18.8 |
   | 79.5 | −32.7 | −19.8 |
   | 80.5 | −43.3 | −21.7 |

   Momentary loudness from 77 s to 80.6 s is −16 to −19 LUFS, 3–6 LU under the impact (−13). The last non-zero sample is at 81.266 s.

**v3.3 numbers**
- **Loudness:** −14.5 LUFS, LRA 8.4 LU, true peak −1.9 dBTP.
- **Cue check:** 143/143 within 1 frame (worst 20.3 ms).
- **Mix checks (1.0–80.533 s):** 0 holes (title lowest window 2.6 dB under its median); largest dip 3.2 dB; 0 clicks. The only silent runs are 0–0.08 s and 81.265 s → end.

---

## v3.4 (a fuller breakdown at 27:1): current, 2026-09-29

The 27:1–28:1 breakdown ("This film, too.", 70.667–73.333 s) sat well under the proof hall, the likeliest place to hear "the music disappears". v3.3 is archived in `audio/v3.3/`. Two renders give the same MD5 (`a79c9c45…`). Nothing moved in time: hits, kinds, beats, bars, holds and fade are identical to v3.3.

- **Bar 27 (still a breakdown, no drums groove):**
  - its own pad layer, +6 dB, brighter (1300→1900 Hz instead of starting at 900);
  - the filtered 8th pulse +8 dB (800 Hz, post-drive low-pass 1.2 kHz);
  - sub +3 dB, in both reveal bars;
  - one low taiko on 27:1 (no ensemble, unlabelled).
- **Bar 28:** pad +2 dB and the pulse starts 4.5 dB higher (ramp −13.5 → −12), so the stem payoff (kick 28:1, bass 28:2, hats 28:3, lead 28:4) still steps up from the breakdown.
- **Mean momentary loudness per bar (LUFS):**

  | version | 23 | 24 | 25 | 26 | 27 | 28 | 29 |
  |---|---|---|---|---|---|---|---|
  | v3.3 | −12.6 | −12.1 | −14.3 | −15.6 | **−18.5** | −14.4 | −15.7 |
  | v3.4 | −12.7 | −12.2 | −14.4 | −15.6 | **−15.1** | −13.6 | −15.8 |

  Bar 27 is now +3.4 LU (its quietest momentary −21.2 → −16.3), still about 2.5 LU under the proof hall and 1.5 LU under bar 28.
- **Remaining soft spot:** just before the bass stem enters, bar 28 dips briefly to −16.4 LUFS momentary at 74.0 s, after the kick of 28:1 decays. That is about level with the breakdown, then it climbs to −12.7 by the end of the bar.
- **QA:**
  - Loudness −14.5 LUFS, LRA 8.5 LU, true peak −1.9 dBTP.
  - Cue check 143/143 within 1 frame (worst 20.3 ms).
  - 0 holes (reveal section lowest window 3.1 dB under its median).
  - Largest dip 3.0 dB; 0 clicks.
  - Silent runs only at 0–0.08 s and 81.265 s → end.
