# STYLE — OpenVideoHarness launch film

Register: **Linear / Vercel** (near-black, 1px hairlines, blueprint grid). Why this and not Apple: see NOTES.md, 创作决策.

## Canvas
- Size 1920x1080, fps 30; safe box x 96–1824, y 54–1026 (EBU 90% graphics-safe); no caption band (silent, no captions) but key reads stay above y 900 anyway.
- Grid: 120px blueprint grid (16 × 9 cells), hairlines rgba(237,237,239,0.06). Panes snap to grid lines: x 144 / 264 … ; label baseline sits one cell above its pane.

## Palette
| token | hex | 用途 |
|---|---|---|
| bg | #0A0A0B | stage ground (also on #root, opaque — seam-craft white-flash guard) |
| surface | #111113 | pane fill |
| hairline | #26262B | 1px pane borders, table rules, stat dividers |
| grid | rgba(237,237,239,.06) | blueprint grid |
| fg | #EDEDEF | primary text |
| muted | #8B8B94 | secondary text, prompt, labels |
| dim | #55555D | table text that is not the answer, timecode |
| accent | #FFB224 | the ONE accent: what the harness is acting on right now (focus ring, ✓, routed row, FAIL flag, playhead). Never decorative. |

No second saturated colour: PASS is shown in fg with a ✓, not green.

## Type
- Display / body: SF Pro via `-apple-system, system-ui, sans-serif` (lint treats these as generic families — no @font-face needed); CJK falls back to PingFang SC.
- Mono: "LF Mono" = `@font-face` with `src: local("SF Mono"), local("SFMono-Regular"), local("Menlo-Regular"), local("Menlo")`, then `ui-monospace, monospace`. (Plain `ui-monospace` renders proportional in `hyperframes render` — see NOTES 2026-09-29.)
- Weights: 400 and 600 only. Tracking: display -0.035em, body -0.01em, mono 0.
- Sizes: hero 136px, wordmark 168px ("OpenVideoHarness", block centred), stat numbers 148px, feature label 44px, stat label 44px, NOTES line 44px, pane text 26–32px (routed row ≈ 35–37px and terminal ≈ 31px effective after the push-in), timecode 30px mono.

## Motion tokens
| token | value |
|---|---|
| enter | power3.out / expo.out, 0.5–0.8s |
| exit | power4.in, 0.3s (cut-the-curve half) |
| move / camera | power2.inOut (≈ easeInOutCubic), 1.6–2.2s, then HOLD (move-then-stop, no drift) |
| stagger | 40 ms per item (tree, table rows), total ≤ 0.4s |
| type-on | 30 ms/char, steps (no easing) |
| hold before climax | 0.3–0.4s before every click result |
| cursor | 7cqw ≈ 134px white arrow, 1.4px near-black stroke; enter from below power3.out 0.6s; click 0.1s in / 0.22s out, pivot at tip `21% 14%` |
| register exceptions | none — no overshoot anywhere |

## Transitions (3 kinds, reused)
- **cut-the-curve LEFT** (default seam): exit x 0→−230 power4.in 0.3s + opacity out by 70%; entry x +230→0 power4.out 0.36s from opacity .35; blur 8px on the wrapper at the cut.
- **waterfall cut** word-by-word, LEFT, for text→text (hook → problem).
- **inverse zoom-through** (reserved: ARRIVAL) for proof → wordmark only.
- Dominant direction: LEFT. The cursor is the carrier across C→D→E.

## Banned
purple-cyan gradients, glow orbs, glassmorphism, gradient text, neon, pure #000/#fff, bounce/elastic, idle breathing loops, crossfades, @keyframes / CSS transitions, Math.random, third-party logos, traffic-light window chrome, placeholder UI, invented numbers.
