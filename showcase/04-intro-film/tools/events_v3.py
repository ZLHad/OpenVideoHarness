"""v3 Phase B SFX events (30 bars, 80 s): every sound lands on the frame of its picture event
(same beat grid and times as js/main.js, js/arch.js, js/pipeline.js, js/features.js). Writes audio/events.json.
The v3.1 score already carries the musical landings (bells, clacks, typing in bar 5, the bar-20 sound demos, the star burst),
so the SFX here are the mechanical layer: node ticks, stamps, approvals, fails, whooshes on the whips, impacts."""
import json
BEAT = 60 / 90; BAR = 4 * BEAT; S16 = BEAT / 4
bar = lambda k, b=0: (k - 1) * BAR + b * BEAT + (2 * BEAT if k >= 12 else 0)  # bar 11 is 6/4
ev = []
E = lambda t, s, g: ev.append({"t": round(t, 4), "sfx": s, "gain_db": g})
# S2 program: tiles land; S3 problem: three stamps
for n in range(4): E(bar(6) + n * S16, "tick", -16)
for i in range(3): E(bar(7, 1 + i), "glitch", -8); E(bar(7, 1 + i) + 0.02, "error", -12)
E(bar(9), "boom", -7)                                                         # braam
# S5 architecture
for b in (0, 1): E(bar(10, b), "tick", -13)
E(bar(10, 2), "toggle", -9)                                                   # router
for j in range(8): E(bar(11, 0.5 * j), "tick", -17)                          # 8 video types on 8ths
for k in range(4): E(bar(12, 0.5 * k), "pop", -13)                           # 4 doc/tool cards on 8ths
for b in (0, 1): E(bar(13, b), "tick", -13)                                   # engines, references
E(bar(13, 2), "toggle", -8)                                                   # projects/ portal
# S6 workflow (local beats from bar 14)
at = lambda b: bar(14) + b * BEAT
for b in (0, 0.5, 1.0, 1.5, 4.5, 8.75, 9.0, 16.25): E(at(b), "tick", -13)
# (no tick for I at b9.25: it lights inside the whip whoosh, which masks it)
for b in (3.0, 7.0, 15.6): E(at(b), "pop", -12)                               # gates light (①② on the score's hold buttons)
for b in (4, 8, 17): E(at(b), "ding", -10)                                    # approvals
for b in (10, 11, 12): E(at(b), "error", -11)                                 # fail laps
E(at(16), "success", -8)                                                      # pass
E(at(18), "shutter", -11)                                                     # final cut
# S7 features, S8 cases
E(bar(19), "pop", -12)
for i in range(20): E(bar(19, 2) + i * S16 * 0.5, "tick", -21)               # checklist boxes
E(bar(21, 2), "click", -12)                                                   # enter
# S9 proof hall, S10 reveal, S11 title
E(bar(23), "impact", -9)
for i in range(4): E(bar(28, i), "click", -10)                                # code lines ↔ stems
E(bar(29), "impact", -8)
E(bar(29, 3), "typing", -14)                                                  # CTA
# a whoosh on every whip (same list as WHIPS in js/main.js + the modules; not on the braam)
WHIPS = [bar(3) - 0.1, bar(4), bar(7) - 0.15,
         bar(10) + 0.15, bar(11) - 0.1, bar(12) - 0.1, bar(13) - 0.05,
         at(0.8), at(4.8), at(8.95), at(17.6),
         bar(19) + 0.02, bar(20) - 0.05, bar(21) - 0.05, bar(22) - 0.05,
         bar(23) + 0.1, bar(24, 3) - 0.07, bar(25, 2) - 0.07, bar(26, 1) - 0.07, bar(27, 1), bar(29) + 0.7]
for w in WHIPS:
    if abs(w - bar(4)) > 0.05: E(w, "whoosh", -11)  # none on the request card: the score's "wake" swell carries that move
ev.sort(key=lambda e: e["t"]); json.dump(ev, open("audio/events.json", "w"), indent=1)
print(len(ev), "film events")
