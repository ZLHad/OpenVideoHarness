"""Build sketch.json: the v5 chapter sketch (106 s, 53 bars at 120 BPM), motif B written out longhand.
Run: python3 make_sketch.py  → sketch.json. Motif A would replace every note table marked # MOTIF."""
import json

SEC = [  # name, bars, chords, chapter
 ("chaos", 4, ["i", "bII", "i", "bII"], "Ch0"), ("nova", 1, ["i"], "Ch0"), ("question", 2, ["IVadd9", "Vsus4"], "Ch0"),
 ("reveal", 4, ["I", "IV", "vi", "V"], "Ch0"),
 ("route", 5, ["I", "IV", "vi", "V I", "I"], "Ch1"),
 ("gates", 8, ["I", "ii", "IV", "Vsus4", "I", "iii", "IV", "Vsus4"], "Ch2"),
 ("sound", 4, ["vi", "IV", "I", "V"], "Ch3"), ("code", 3, ["vi", "IV", "V"], "Ch3"),
 ("loop", 4, ["ii", "IV", "bVI", "V"], "Ch3"), ("hold3", 1, ["Vsus4"], "Ch3"),
 ("climax", 4, ["I", "IV", "vi", "V I"], "Ch4"), ("proof", 3, ["IV", "I", "V"], "Ch4"),
 ("stop", 1, ["IVadd9"], "Ch5"), ("rebuild", 3, ["I", "IV", "V"], "Ch5"),
 ("coda", 6, ["IV", "IV", "iv", "I", "I", "I"], "Ch6"),
]
sections = [{"name": n, "bars": b, "chords": c} for n, b, c, _ in SEC]

def notes(lst, v0=0.6, dv=0.0, off=0):
    return [[b + off, d, p, round(min(1.0, (v if v is not None else v0)), 2)] for b, d, p, v in lst]

# MOTIF B, longhand. degrees in D major: d3 F#, d5 A, d6 B, d8 D', d9 E', d10 F#', d12 A'
ANTE = [(0,1,"d3",.60),(1,1,"d5",.64),(2,2,"d6",.70), (4,1.5,"d8",.72),(5.5,.5,"d6",.62),(6,2,"d5",.64),
        (8,1,"d3",.62),(9,1,"d5",.66),(10,1,"d6",.70),(11,1,"d8",.74), (12,4,"d9",.70)]
CONS = [(0,1,"d3",.66),(1,1,"d5",.70),(2,2,"d6",.76), (4,1.5,"d8",.78),(5.5,.5,"d9",.80),(6,2,"d10",.86),
        (8,1,"d9",.80),(9,1,"d8",.76),(10,1,"d6",.72),(11,1,"d5",.70), (12,1,"d6",.72),(13,1,"d9",.78),(14,6,"d8",.72)]
CLIMAX = [(0,1,"d3",.86),(1,1,"d5",.90),(2,2,"d6",.94), (4,1.5,"d8",.92),(5.5,.5,"d9",.94),(6,2,"d10",.98),
          (8,2,"d12",1.0),(10,1,"d9",.92),(11,1,"d8",.90), (12,1,"d6",.88),(13,1,"d9",.92),(14,2,"d8",.94)]

P = []
add = P.append
# ---------------- Ch0 opening: chaos → nova → question → reveal ----------------
add({"inst": "drone", "id": "drone", "sections": ["chaos", "nova", "question", "hold3", "stop"], "figure": "sustain", "pitch": ["d1"],
     "octave": 2, "hold": "section", "gain_db": -10, "send": 0.1,
     "by_section": {"nova": {"gain_db": -7}, "question": {"gain_db": -21}, "hold3": {"gain_db": -24}, "stop": {"gain_db": -22}}})
add({"inst": "strings", "id": "ost_chaos", "sections": ["chaos"], "scale": "phrygian", "octave": 3, "step": 16,
     "pitch": ["d3", "d5", "d6", "d5"], "params": {"marcato": True}, "legato": 0.8, "gain_db": -3, "pan": -0.2, "send": 0.12,
     "pattern": ["3111311131113111", "4222422242224222", "6444644464446444", "8666866686668666"]})   # MOTIF (hidden, phrygian)
add({"inst": "seq", "id": "seq_chaos", "sections": ["chaos"], "scale": "phrygian", "octave": 4, "step": 16, "pitch": ["d8", "d6", "d5"],
     "pitch_cycle": "part", "params": {"cutoff": 900, "decay": 0.1, "attack": 0.004}, "gain_db": -12, "pan": 0.4, "send": 0.15,
     "delay": {"beats": 0.75, "fb": 0.3, "mix": 0.25, "lp": 3000, "pingpong": True},
     "pattern": ["................", "3333333333333333", "5445445445445445", "7667667667667667"]})
add({"inst": "strings", "id": "swell_chaos", "sections": ["chaos"], "chord": True, "voicing": "close", "octave": 3, "step": 1,
     "params": {"attack": 1.6, "release": 0.6}, "gain_db": -10, "send": 0.25, "pattern": ["3", "5", "6", "8"]})
add({"inst": "brass", "id": "brass_shadow", "sections": ["chaos"], "scale": "phrygian", "octave": 3, "loop": 4, "gain_db": -3, "send": 0.2,
     "pattern": notes([(8,2,"d3",.55),(10,2,"d5",.68),(12,4,"d6",.82)])})                       # MOTIF shadow: F A Bb
add({"inst": "taiko", "id": "taiko", "sections": ["chaos", "nova", "gates", "code", "loop", "climax", "proof", "rebuild"], "gain_db": -9, "send": 0.12,
     "pattern": ["................", "7.......5.......", "8...5...8...5...", "9.6.6.6.9.6.7789"],
     "by_section": {"nova": {"pattern": "X...............", "gain_db": -6},
                    "gates": {"pattern": ["5.......3.......", "5...3...5...3...", "6...3...6...3.3.", "................",
                                          "5.......3.......", "5...3...5...3...", "6...4...6...4.4.", "................"], "gain_db": -14},
                    "code": {"pattern": ["6...3...6...3...", "6...4...6...4...", "7...4...7.4.4.4."], "gain_db": -13},
                    "loop": {"pattern": ["6.......6.......", "6...4...6...4...", "X...X...X.......", "8.......6......."], "gain_db": -12},
                    "climax": {"pattern": "X.......8.......", "gain_db": -11},
                    "proof": {"pattern": "6.......4...4...", "gain_db": -12},
                    "rebuild": {"pattern": ["................", "................", "6...4...7...5.6."], "gain_db": -13}}})
add({"inst": "timpani", "id": "timp_nova", "sections": ["nova"], "pitch": ["d1"], "octave": 2, "pattern": "X...............", "gain_db": -6, "send": 0.2})
add({"inst": "gong", "id": "gong_nova", "sections": ["nova"], "pitch": ["d1"], "octave": 2, "pattern": "X...............",
     "params": {"decay": 2.5, "length": 6.0}, "gain_db": -9, "send": 0.3, "hit": True})
add({"inst": "cymbals", "id": "cym_nova", "sections": ["nova"], "pattern": "X...............", "gain_db": -9, "send": 0.25})
add({"inst": "brass", "id": "brass_nova", "sections": ["nova"], "figure": "stab", "beats": [0], "len": 1.2, "voicing": "spread", "octave": 3,
     "params": {"stab": True}, "gain_db": -2, "send": 0.3})
add({"inst": "piano", "id": "piano_q", "sections": ["question"], "octave": 4, "loop": 2, "params": {"tone": "felt", "pedal": True},
     "gain_db": 4, "send": 0.35, "hit": "section",
     "pattern": notes([(0,8,"d1,,",.35),(0,1.5,"d3",.62),(1.5,1.5,"d5",.66),(3,4,"d6",.60),(5,1,"d3",.44),(6,2,"d5",.40)])})  # MOTIF question: F# A B … (hangs), F# A …
add({"inst": "strings", "id": "air_q", "sections": ["question"], "figure": "sustain", "pitch": ["d6"], "octave": 5, "hold": "section",
     "params": {"attack": 1.5, "release": 2.0}, "vel": 0.5, "gain_db": -11, "send": 0.4})
add({"inst": "strings", "id": "breath_q", "sections": ["question"], "loop": 2, "params": {"attack": 2.2, "release": 0.5}, "gain_db": -12,
     "send": 0.35, "pattern": [[4.5, 3.5, ["A3", "D4", "E4"], 0.55]]})
# reveal = antecedent, first full statement (strings + piano 8va), cello answer in the gap
add({"inst": "strings", "id": "mel_rev", "sections": ["reveal"], "octave": 4, "loop": 4, "params": {"attack": 0.1, "release": 0.35},
     "gain_db": -2, "send": 0.3, "hit": "section", "pattern": notes(ANTE)})                   # MOTIF full (antecedent)
add({"inst": "piano", "id": "pno_rev", "sections": ["reveal"], "octave": 5, "loop": 4, "gain_db": -7, "send": 0.25, "pan": 0.1,
     "pattern": notes(ANTE)})
add({"inst": "cello", "id": "answer", "sections": ["reveal"], "octave": 3, "loop": 4, "gain_db": -7, "send": 0.25, "pan": -0.25,
     "pattern": notes([(13,0.5,"d5",.60),(13.5,0.5,"d6",.64),(14,0.5,"d8",.68),(14.5,1.5,"d9",.70)])})
add({"inst": "harp", "id": "arps", "sections": ["reveal", "route", "gates", "proof"], "figure": "arp-updown", "rate": 8, "span": 2, "octave": 3,
     "gain_db": -17, "send": 0.3, "pan": 0.2, "by_section": {"route": {"gain_db": -15}, "gates": {"gain_db": -18}, "proof": {"gain_db": -13}}})
add({"inst": "strings", "id": "pad", "sections": ["reveal", "route", "gates", "sound", "code", "loop", "hold3", "climax", "proof", "stop", "rebuild", "coda"],
     "figure": "sustain", "voicing": "close", "octave": 3, "params": {"attack": 0.8, "release": 1.2}, "gain_db": -19, "send": 0.3,
     "by_section": {"route": {"gain_db": -17}, "gates": {"gain_db": -17}, "sound": {"gain_db": -20}, "code": {"gain_db": -17},
                    "loop": {"gain_db": -16}, "hold3": {"gain_db": -22}, "climax": {"gain_db": -13}, "proof": {"gain_db": -13},
                    "stop": {"gain_db": -20}, "rebuild": {"gain_db": -18}, "coda": {"gain_db": -16}}})
add({"inst": "cello", "id": "bass", "sections": ["reveal", "route", "gates", "code", "loop", "climax", "proof", "coda"], "figure": "sustain",
     "pitch": ["c0,"], "octave": 3, "params": {"retrigger": True, "glide": 0.02}, "gain_db": -11, "send": 0.15,
     "by_section": {"route": {"gain_db": -10}, "gates": {"gain_db": -10}, "code": {"gain_db": -9}, "loop": {"gain_db": -9},
                    "climax": {"gain_db": -8}, "proof": {"gain_db": -10}, "coda": {"gain_db": -13}}})
# ---------------- Ch1 route: consequent, flute 8va, shaker ----------------
add({"inst": "strings", "id": "mel_route", "sections": ["route"], "octave": 4, "loop": 5, "params": {"attack": 0.1, "release": 0.35},
     "gain_db": -2, "send": 0.3, "hit": "section", "pattern": notes(CONS)})                  # MOTIF full (consequent)
add({"inst": "flute", "id": "fl_route", "sections": ["route"], "octave": 5, "loop": 5, "gain_db": -8, "send": 0.2, "pan": -0.15,
     "pattern": notes(CONS)})
add({"inst": "shaker", "id": "shk", "sections": ["route", "gates", "proof"], "gain_db": -20, "pan": 0.3,
     "pattern": "x.g.x.g.x.g.x.g.",
     "by_section": {"gates": {"pattern": ["x.g.x.g.x.g.x.g.", "x.g.x.g.x.g.x.g.", "x.g.x.g.x.g.x.g.", "................",
                                          "x.g.x.g.x.g.x.g.", "x.g.x.g.x.g.x.g.", "x.g.x.g.xgxgxgxg", "................"]},
                    "proof": {"gain_db": -18}}})
# ---------------- Ch2 gates: head sequenced on each chord, the 28-note styles run, holds before each ✓ ----------------
HEADSEQ = [(0,1,"s2",.66),(1,1,"s4",.70),(2,2,"s5",.74)]
add({"inst": "brass", "id": "brass_gates", "sections": ["gates"], "octave": 4, "loop": 8, "gain_db": -2, "send": 0.25, "pan": 0.1, "hit": "section",
     "pattern": notes(HEADSEQ, off=0) + notes(HEADSEQ, off=4) + notes(HEADSEQ, off=8) +
                notes(HEADSEQ, off=16) + notes(HEADSEQ, off=20) + notes(HEADSEQ, off=24)})   # MOTIF developed: head on I, ii, IV / I, iii, IV
PENTA = ["d1", "d2", "d3", "d5", "d6", "d8", "d9", "d10", "d12", "d13", "d15", "d16", "d17", "d19"]
run = []
for i in range(28):   # 28 sixteenths = 7 beats: one note per style swatch lighting up
    k = i if i < 14 else 27 - i
    run.append([4 + i * 0.25, 0.25, PENTA[k], round(0.45 + 0.02 * (i % 7), 2)])
add({"inst": "celesta", "id": "styles_run", "sections": ["gates"], "octave": 4, "loop": 8, "gain_db": -13, "send": 0.35, "pan": -0.2,
     "pattern": run})   # not a hit: 16ths are too dense for the cue check; the picture reads the 16th grid
add({"inst": "glockenspiel", "id": "check", "sections": ["gates", "hold3"], "octave": 5, "loop": 8, "gain_db": -14, "send": 0.3, "hit": True,
     "pattern": [[16, 1.5, "d8", 0.7], [16.25, 1.25, "d10", 0.6]],
     "by_section": {"hold3": {"pattern": [[3.5, 0.5, "d5", 0.5]], "loop": 1}}})
add({"inst": "pizzicato", "id": "pizz", "sections": ["gates", "sound"], "octave": 3, "step": 8, "pitch": ["c0", "c2", "c1", "c2"],
     "gain_db": -12, "send": 0.2, "pan": -0.1,
     "pattern": ["xxxxxxxx", "xxxxxxxx", "xxxxxxxx", "........", "xxxxxxxx", "xxxxxxxx", "xxxxxxxx", "........"],
     "by_section": {"sound": {"pattern": ["........", "x...x...", "x.x.x.x.", "x.x.x.x."], "gain_db": -11}}})
# ---------------- Ch3 make: sound first (one instrument per row) → code → self-review loop → hold ----------------
add({"inst": "marimba", "id": "mar", "sections": ["sound", "rebuild"], "octave": 4, "step": 8, "pitch": ["c0", "c1", "c2", "c1'"],
     "gain_db": -10, "send": 0.25, "pan": 0.25, "hit": "section",
     "pattern": "xxxxxxxx", "by_section": {"rebuild": {"pattern": ["..xxxxxx", "xxxxxxxx", "xxxxxxxx"], "gain_db": -12}}})
add({"inst": "celesta", "id": "cel_sound", "sections": ["sound"], "octave": 5, "loop": 4, "gain_db": -5, "send": 0.35,
     "pattern": notes([(8,1,"d3",.6),(9,1,"d5",.62),(10,2,"d6",.66),(12,1,"d3",.62),(13,1,"d5",.64),(14,1,"d6",.66),(15,1,"d8",.7)])})  # MOTIF fragment
add({"inst": "hihat", "id": "hat", "sections": ["sound", "code", "loop"], "gain_db": -18, "pan": 0.35,
     "pattern": "................",
     "by_section": {"sound": {"pattern": ["................", "................", "................", "x.x.x.x.x.x.xxxx"]},
                    "code": {"pattern": "x.xgx.xgx.xgx.xg", "gain_db": -15}, "loop": {"pattern": "x.x.x.x.x.x.x.x.", "gain_db": -18}}})
add({"inst": "seq", "id": "seq_code", "sections": ["code", "loop"], "octave": 4, "step": 16, "pitch": ["c0", "c1", "c2", "c1'", "c2", "c1"],
     "pitch_cycle": "part", "params": {"cutoff": 1400, "decay": 0.09, "attack": 0.004}, "gain_db": -10, "pan": 0.3, "send": 0.15,
     "delay": {"beats": 0.75, "fb": 0.25, "mix": 0.2, "lp": 3500, "pingpong": True},
     "pattern": ["4444444444444444", "5555555555555555", "6666666666666666"],
     "by_section": {"loop": {"pattern": ["5555555555555555", "5555555555555555", "7.7.7.7.7.7.....", "................"]}}})
add({"inst": "brass", "id": "brass_code", "sections": ["code"], "octave": 4, "loop": 3, "gain_db": -2, "send": 0.25,
     "pattern": notes(HEADSEQ, off=0) + notes(HEADSEQ, off=4) + notes([(8,.5,"s2",.8),(8.5,.5,"s4",.84),(9,1,"s5",.88),(10,.5,"s2",.84),(10.5,.5,"s4",.88),(11,1,"s5",.92)])})  # MOTIF sequenced, then fragmented
add({"inst": "snare", "id": "snare", "sections": ["code", "loop", "hold3", "climax"], "gain_db": -14, "send": 0.15,
     "pattern": ["....4.......4...", "....5.......5...", "....6.......6.66"],
     "by_section": {"loop": {"pattern": ["....5.......5...", "....5.......5.5.", "X...X...X.......", "....6.......6..."]},
                    "hold3": {"pattern": "........23456789", "gain_db": -15},
                    "climax": {"pattern": "....X.......X...", "gain_db": -15}}})
add({"inst": "celesta", "id": "try_loop", "sections": ["loop"], "octave": 5, "loop": 4, "gain_db": -8, "send": 0.3,
     "pattern": notes([(0,.5,"d3",.6),(.5,.5,"d5",.62),(1,1,"d6",.64),(2,1,"C6",.6),   # tries: F# A B … C (wrong)
                       (4,.5,"d3",.62),(4.5,.5,"d5",.64),(5,1,"d6",.66),(6,1,"C6",.62),
                       (12,.5,"d3",.7),(12.5,.5,"d5",.72),(13,1,"d6",.76),(14,2,"d8",.8)])})  # MOTIF: two wrong endings, then right
add({"inst": "brass", "id": "fail", "sections": ["loop"], "octave": 3, "loop": 4, "gain_db": -4, "send": 0.2, "hit": True,
     "pattern": [[8, 0.45, ["F#3", "G3", "C4"], 0.9], [9, 0.45, ["F#3", "G3", "C4"], 0.9], [10, 0.45, ["F#3", "G3", "C4"], 0.95]]})
add({"inst": "strings", "id": "pass", "sections": ["loop"], "chord": True, "voicing": "close", "octave": 4, "step": 1, "params": {"attack": 0.05, "release": 0.8},
     "gain_db": -8, "send": 0.3, "hit": True, "pattern": [".", ".", ".", "7"]})
add({"inst": "timpani", "id": "timp_roll", "sections": ["hold3"], "pitch": ["d5"], "octave": 2, "gain_db": -13, "send": 0.2,
     "pattern": "........3456789X"})
add({"inst": "strings", "id": "air_hold", "sections": ["hold3", "stop", "coda"], "figure": "sustain", "pitch": ["d5"], "octave": 5, "hold": "section",
     "params": {"attack": 1.0, "release": 1.5}, "vel": 0.5, "gain_db": -12, "send": 0.4})
# ---------------- Ch4 film: climax (the only peak, A5 in bar 3) → proof ----------------
add({"inst": "brass", "id": "brass_climax", "sections": ["climax"], "octave": 4, "loop": 4, "gain_db": 0, "send": 0.3, "hit": "section",
     "pattern": notes(CLIMAX)})                                                               # MOTIF tutti
add({"inst": "strings", "id": "str_climax", "sections": ["climax"], "octave": 5, "loop": 4, "params": {"attack": 0.06, "release": 0.4},
     "gain_db": -1, "send": 0.35, "pattern": notes(CLIMAX)})
add({"inst": "strings", "id": "ost_climax", "sections": ["climax"], "octave": 3, "step": 8, "pitch": ["c0", "c2", "c1'", "c2"],
     "params": {"marcato": True}, "legato": 0.7, "gain_db": -8, "pan": -0.2, "send": 0.15, "pattern": "X8X8X8X8"})
add({"inst": "brass", "id": "brass_pad", "sections": ["climax"], "figure": "sustain", "voicing": "close", "octave": 3, "vel": 0.65, "gain_db": -9, "send": 0.25})
add({"inst": "timpani", "id": "timp_climax", "sections": ["climax"], "octave": 2, "pattern": "X.......6.......", "gain_db": -12, "send": 0.2})
add({"inst": "cymbals", "id": "cym_climax", "sections": ["climax"], "loop": 4, "pattern": [[0, 1, None, 1.0], [8, 1, None, 0.85]], "gain_db": -11, "send": 0.25})
add({"inst": "strings", "id": "mel_proof", "sections": ["proof"], "octave": 5, "loop": 3, "params": {"attack": 0.12, "release": 0.4}, "gain_db": 0, "send": 0.35,
     "pattern": notes([(0,1,"d3",.62),(1,1,"d5",.66),(2,2,"d6",.7),(4,1.5,"d8",.72),(5.5,.5,"d6",.64),(6,2,"d5",.66),(8,1,"d6",.64),(9,1,"d9",.7),(10,2,"d8",.66)])})  # MOTIF echo
add({"inst": "piano", "id": "pno_proof", "sections": ["proof"], "octave": 4, "step": 8, "pitch": ["c0", "c2", "c1'", "c2"], "gain_db": -8, "send": 0.25,
     "pattern": "xxxxxxxx"})
# ---------------- Ch5 reveal: stop (the question's B again), rebuild one part per beat ----------------
add({"inst": "piano", "id": "pno_stop", "sections": ["stop"], "octave": 4, "loop": 1, "params": {"tone": "felt", "pedal": True}, "gain_db": 2, "send": 0.4,
     "hit": "section", "pattern": [[0, 4, "d6", 0.55]]})                                      # MOTIF callback: the hanging B
add({"inst": "cello", "id": "bass_rb", "sections": ["rebuild"], "octave": 3, "loop": 3, "gain_db": -10, "send": 0.15,
     "pattern": [[1, 3, "c0,", 0.7], [4, 4, "c0,", 0.72], [8, 4, "c0,", 0.75]]})
add({"inst": "piano", "id": "pno_rb", "sections": ["rebuild"], "octave": 5, "loop": 3, "gain_db": -2, "send": 0.3, "hit": "section",
     "pattern": notes([(3,.5,"d3",.6),(3.5,.5,"d5",.62),(4,2,"d6",.66),(8,1,"d3",.64),(9,1,"d5",.66),(10,1,"d6",.7),(11,1,"d8",.74)])})
add({"inst": "brass", "id": "brass_rb", "sections": ["rebuild"], "figure": "sustain", "voicing": "close", "octave": 3, "vel": 0.6, "gain_db": -15, "send": 0.25,
     "params": {"swell": True}})
# ---------------- Ch6 coda: augmented motif on celesta, resolves the hanging B to D ----------------
add({"inst": "celesta", "id": "cel_coda", "sections": ["coda"], "octave": 5, "loop": 6, "gain_db": -4, "send": 0.4, "hit": "section",
     "pattern": notes([(0,2,"d3",.6),(2,2,"d5",.62),(4,4,"d6",.6),(8,8,"d8",.62)])})              # MOTIF augmented, lands on D
add({"inst": "piano", "id": "pno_coda", "sections": ["coda"], "figure": "sustain", "voicing": "close", "octave": 3,
     "params": {"tone": "felt", "pedal": True}, "vel": 0.5, "gain_db": -8, "send": 0.35})

marks = [{"bar": 1, "label": "motif hidden (phrygian 16ths)"}, {"bar": 3, "label": "shadow: low brass"},
         {"bar": 5, "label": "supernova (gong on D)"}, {"bar": 6, "label": "question: F# A B … (hangs)"},
         {"bar": 8, "label": "reveal: first full statement"}, {"bar": 12, "label": "consequent, flute 8va"},
         {"bar": 17, "label": "head sequenced per gate"}, {"bar": 18, "label": "28-note styles run"},
         {"bar": 25, "label": "sound first: one part per bar"}, {"bar": 29, "label": "code: head sequenced, fragmented"},
         {"bar": 34, "beat": 0, "label": "fail ×3"}, {"bar": 36, "label": "hold before gate ③"},
         {"bar": 37, "label": "climax: tutti"}, {"bar": 39, "label": "peak note A5"}, {"bar": 44, "label": "stop: the question's B"},
         {"bar": 45, "label": "rebuild: one part per beat"}, {"bar": 48, "label": "coda: augmented, B → D"}]
# bar indices above are 1-based bar numbers of the whole score
score = {"_about": "OpenVideoHarness intro v5 · chapter sketch for gate ① (not the final score). 53 bars at 120 BPM = 106 s, D major; "
                   "one motif (B: 3-5-6, F# A B) hidden in the chaos, left hanging at the question, stated whole at the reveal, "
                   "developed through the gates and the self-review loop, sung tutti once at the climax, left hanging again at "
                   "'this film, too' and resolved (B → D) in the coda. Built by make_sketch.py.",
         "_chapters": {c: [n for n, _, _, cc in SEC if cc == c] for c in ["Ch0", "Ch1", "Ch2", "Ch3", "Ch4", "Ch5", "Ch6"]},
         "_marks": marks, "bpm": 120, "key": "D", "mode": "major", "seed": 17, "stereo": True,
         "space": {"type": "hall", "rt60": 2.6}, "sections": sections, "parts": P}
json.dump(score, open("sketch.json", "w"), ensure_ascii=False, indent=1)
print(sum(b for _, b, _, _ in SEC), "bars,", len(P), "parts")
