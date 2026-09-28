# STORYBOARD

<!-- Gate 2 skipped by user; written anyway as the timing sheet for review. Silent video: timings come from the reads, not from audio. -->

Logline: A square wave looks nothing like a sine; stack odd sines of shrinking size and it squares up, except for a horn at every jump that never gets shorter.
World: black void, one long graph; grey target, blue newcomer, yellow running sum, red for the one flaw. Colour never changes meaning.
Motif: the yellow running sum. Every blue harmonic is stacked onto it and turns yellow; the equation turns yellow left→right in lock-step.
Arc: "that can't work" (sine vs square) → "oh, it's converging" (terms 3, 5, 7, then many) → "but the corner never settles" (Gibbs 9%).
Audio: none (silent). Total 25.0 s = 750 frames @ 30 fps (24.0 s before the reviewer pass; final hold +1.0 s).

## Shots

| # | time (s) | visual · event · focus move | focus | transition out |
|---|---|---|---|---|
| A | 0.0–2.1 | Faint x-axis; grey square wave draws left→right over x ∈ [−π, 3π] | grey wave | camera stays; next curve draws over it |
| B | 2.1–4.3 | Blue (4/π)·sin x draws left→right over the square; hold; it turns yellow (it is now the running sum) | blue→yellow sine | colour change is the hand-off |
| C | 4.3–6.9 | Series appears whole in row A, holds, dims to 30% | equation | dim |
| D1 | 6.9–8.1 | `f(x) =` re-lights (grey f); `4/π ( sin x )` lights yellow = the yellow curve | eq ↔ curve link | — |
| D3 | 8.1–11.0 | `+ sin3x/3` lights blue; blue 3rd harmonic draws along the axis (⅓ tall, 3× faster); it lifts onto the yellow curve; yellow rises into it, blue fades, term turns yellow | blue harmonic, then corners | repeat pattern |
| D5 | 11.0–13.1 | same pattern, faster, for sin5x/5 | " | " |
| D7 | 13.1–14.9 | same pattern, faster, for sin7x/7 | " | " |
| D∞ | 14.9–17.2 | `+ ⋯ )` lights yellow, counter `N = 7` appears in A6 (held to 15.5), then runs to 25 (15.5–16.7); curve is nearly square with spikes at each jump | spikes at jumps | spike invites the zoom |
| E | 17.2–18.9 | Strictly sequential: parent shrinks to C1–E3 + equation dims to 35% (17.2–17.8) → magnifier box fades in on the settled parent at the rising jump x = 2π (17.8–18.0) → panel + link lines grow from the box to B4–F6 (18.0–18.7), hold to 18.9. Parent and box stay layered above the panel | the horn in the panel | layout move carries the eye right |
| F | 18.9–25.0 | Red dashed line at the horn peak + `1.179`, grey `1` at the panel plateau, grey ticks `1` / `−1` on the parent (jump of 2 visible); N runs 25 → 99: horn gets thinner, never shorter; red brace `≈ 9% of the jump`; hold 2.6 s | horn + brace | end on the horn (answer frame) |

### A reads
| time | read | why this timing |
|---|---|---|
| 0.2–2.1 | "a square wave: flat, jump, flat, jump" | only moving thing on screen; draw 1.2 s + 0.7 s hold |

### B reads
| time | read | why |
|---|---|---|
| 2.1–3.9 | "a single smooth sine roughly follows it (and pokes above the flat parts)" | draw 1.2 s + 0.6 s hold; blue is new so the eye follows the drawing tip |
| 3.9–4.3 | "this is now our running sum" (blue → yellow) | colour change only, nothing else moves |

### C reads
| time | read | why |
|---|---|---|
| 4.3–6.4 | "there is a formula: a sum of sines with shrinking fractions" | Write 1.0 s, hold 1.0 s (shape only, not read symbol by symbol) |
| 6.4–6.9 | dim = "we'll read it piece by piece" | 0.5 s dim, nothing else moves |

### D1 reads
| time | read | why |
|---|---|---|
| 6.9–7.3 | `f(x)` is the grey square wave | grey = grey |
| 7.3–8.1 | first term `(4/π) sin x` is the yellow curve already on screen | yellow = yellow; 0.4 s hold |

### D3 reads (D5, D7 compress the same three reads to 2.1 s and 1.8 s: repetition makes them cheaper)
| time | read | why |
|---|---|---|
| 8.1–9.3 | new blue term; its wave is ⅓ as tall and 3× as fast | term and wave light together, wave drawn on the axis where its size is easy to judge; 0.8 s + 0.4 s hold |
| 9.3–10.2 | it gets stacked on top of the yellow curve | lift 0.9 s, only the blue moves |
| 10.2–11.0 | the yellow sum absorbs it; corners are sharper | merge 0.4 s + 0.4 s hold |

### D∞ reads
| time | read | why |
|---|---|---|
| 14.9–15.5 | "…and so on", counter N = 7 appears | ⋯ lights with the counter, both yellow; 0.2 s hold so N = 7 registers |
| 15.5–16.7 | more terms → squarer | 1.2 s sweep, N ticks 7 → 25 |
| 16.7–17.2 | but spikes remain at every jump | 0.5 s hold before the zoom (dramatic comma) |

### E reads
| time | read | why |
|---|---|---|
| 17.2–18.9 | we zoom in on one corner: there's a horn | shrink 0.6 s → box 0.2 s → panel 0.7 s → hold 0.2 s; one thing moves at a time, box keeps the parent linked |

### F reads
| time | read | why |
|---|---|---|
| 18.9–19.9 | the horn peaks at 1.179 while the target is 1 (and the square goes from −1 to 1) | red line + values + parent ticks 0.6 s, hold 0.4 s |
| 19.9–21.8 | more terms (N → 99): horn gets thinner, NOT shorter | 1.6 s sweep, red line stays fixed as the reference; hold 0.3 s |
| 21.8–25.0 | the overshoot is ≈ 9% of the jump, for good | brace + label 0.6 s, final hold 2.6 s (label fully readable ≈ 2.8 s) |

## Check
- [x] every shot has an event (first ≠ last frame)
- [x] each read gets ≥ 0.4 s before the next starts; D5/D7 compressed on purpose (third/fourth repetition)
- [x] one continuous shot; start (empty axis) and end (horn) both composed
- [x] text: one equation + counter + two tick values + one 5-word label
- [x] ending answers the opening: the square wave is reached everywhere except at its corners
- [x] one transition kind (layout move), dominant direction left→right
