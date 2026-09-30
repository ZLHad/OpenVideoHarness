"""Code-composed soundtrack: a JSON score → a deterministic WAV + an exact beat/section map.

usage (via bin/vh music): python tools/audio/music.py <score.json> <out.wav>      (writes <out>.beats.json too)
       python tools/audio/music.py --example [name] > score.json    (a starter score; --example list names them all)
       python tools/audio/music.py --instruments                    (every part instrument and figure, one line each)

Why: "even the soundtrack is code". The score is versioned with the film, sections line up with shots,
and because we composed it, the beat grid is exact — no beat detection needed for cuts and hits.

Score fields
  bpm, key ("C".."B", optional "#"/"b"), mode ("minor"|"major"; parts also read dorian phrygian lydian mixolydian
    locrian harmonic melodic), seed, master_db (peak, default -1)
  beats_per_bar (optional): beats per bar for the whole score (3 = waltz time); default 4.
  meters (optional): {"11": 6} makes bar 11 (1-based, counted over the whole score) a 6/4 bar; default 4/4.
    With meters (or beats_per_bar) the beat map also carries "bars": [[bar, start_s, beats_in_bar], …] so visuals use one bar(k).
  sections: [{ "name", "bars", "chords": ["i","VI","III","VII"] (roman, cycled per bar),
               "layers": subset of kick clap hats bass pad arp lead  +  bell zheng dizi taiko (Chinese colour:
                 bianzhong-like bell, Karplus–Strong guzheng, breathy dizi, taiko; melodic ones use the key's
                 pentatonic — minor → 羽 1 b3 4 5 b7, major → 宫 1 2 3 5 6 — and share their own hall reverb;
                 in other modes, e.g. dorian, the layers take the parts' chord roots and 羽 when the mode has a
                 minor third, 宫 otherwise),
               "energy": 0..1 (layer gain + filter brightness),
               "riser": true  (noise+tone rise over this section, into the next; {"gain_db": -6}, or "riser_db": -6
                               beside true, lowers it under a narration line or an on-screen hit; default 0 dB),
               "impact": true (boom on this section's first downbeat),
               "fill": true   (drop the kick and taiko on the last beat for a breath),
               "bend": true   (zheng: every 2nd bar ends on a 按弦上滑 press-up note),
               "swing": this section's swing for parts (below),
               "stop": {"at": "5:2", "keep": ["pad"], "tail": 0.15} (parts only: from bar 5, beat 2 of this section
                 (bars counted in the section) to its end, only the kept parts (ids or instruments) play. The others
                 start no new notes; what they still sound fades out over tail s (default 0.15, at least 0.005) from
                 the stop, held notes too; delay and reverb tails ring on; a texture pauses; a pickup into the next
                 section still plays. "hold": true lets the sounding notes ring instead; "bar" and "beat" can replace
                 "at"; "stop": true stops every part from the section's first beat. Judged on the grid, before
                 humanize. The beat map gets a "stop:<section>" hit) }]
  stereo, space, swing, swing_unit, humanize, lofi, tape, drive, parts, motifs, pattern_index: below. A score with only
    `layers` and none of these renders exactly as before, byte for byte.

Parts: instruments playing patterns, rendered beside the layers
  "parts": [{"inst": "upright", "figure": "walking", "gain_db": -2, "pan": -0.2},
            {"inst": "ride", "pattern": "X.xxX.xx", "step": 8, "send": 0.15},
            {"inst": "pipa", "sections": ["theme"], "scale": "yu", "tremolo": 14, "loop": 2,
             "pattern": [[0, 1, "s0"], [1, 0.5, "s1"], [1.5, 0.5, "s2"], [2, 2, "s4"], [4, 4, "s3", 0.9]]}]
  inst      one of the instruments below (--instruments prints them with a line each)
  sections  names this part plays in (default all). by_section {"name": {…}} overrides pattern, figure, params, pitch,
            vel, gain_db, octave, swing, onset_ms … for one section (not pan, send or effects: those are per part).
            "figure": null there switches the part to its "pattern" for that section. A section's params reach every
            voice, the mono ones too (a change starts a new phrase); its gain_db is a level applied after the voice (it
            never drives a voice's own saturation); textures take a section's gain_db and vel, not its params
  octave    register of c0, the chord root (default per instrument: upright 2, cello 3, piano 4, violin 5, glockenspiel 6)
  mix       gain_db, pan (-1..1), send (0..1 into the space), space (override the score's), vel (velocity scale),
            lp / hp (Hz), drive (tanh), delay {"beats": 0.75, "fb": 0.35, "mix": 0.3, "lp": 3000, "pingpong": true},
            duck ("kick", or {"by": part inst or id, "depth": 0.5, "release": 0.2}: dips under that part's hits),
            hit (true: every onset joins the beat map's hits; "section": the first onset of each section), id (a name),
            onset_ms (start that many ms early so a slow attack lands on the beat; hits keep the grid time, using the
            section's onset_ms when by_section sets one),
            detune (cents: a detuned double of another part), quiet (true: skip the audibility check below)
  params    the instrument's own knobs, e.g. piano {"tone": "felt", "pedal": true}; see the instrument list
  Play one of: a step grid, a note list (both in "pattern"), or a "figure".
  Step grid "pattern": "x...x...x...x..." — one character per step; "step": 16 (16ths, default) | 8 | 12 (8th triplets) |
    24 | 4. X accent 1.0 · x 0.72 · g ghost 0.35 · 1–9 velocity 0.1–0.9 · o / O the other stroke (open hat, rim, slap,
    bell, swish, choke, low block, tock) · r roll (2 hits in the step; "roll" changes it) · R roll of 3 · f flam ·
    ~ hold the previous hit one step longer · . - _ rest · spaces and | are ignored. luogu reads 锣鼓经 syllables:
    仓 才 台 七 令 顷 冬 大 八 (e.g. "仓.才.台.才.仓.七.台台仓.").
    Bars of any length: step k of each bar reads character k; a shorter string repeats, a longer one is cut at the bar
    line ("x...x...x...x..." plays 3 hits in a 3-beat bar, 2 in a 2-beat bar). A step that starts inside the bar plays
    even when the bar line cuts it short: half notes ("step": 2, or a figure's "rate": 2) give 3 notes in a 5-beat bar,
    the last one a beat long, and 1 in a 1-beat bar. A list of strings is one per bar, cycled over the bars this part
    plays; a dict chooses by beats in the bar, a grid or a one-bar note list: {"3": "x...x.x.....", "*": [[0, 1, "c0"]]}.
    Pitched instruments take "pitch": ["c0", "c2", "s4"] (one token per hit, restarting each bar; "pitch_cycle": "part"
    keeps counting across bars) or "chord": true (the whole voicing on each hit); "legato" (0.9) scales note lengths.
  Note list "pattern": [[beat, beats, pitch, vel, art], …] — beat from the downbeat; "loop": N (default 1) lets the list
    span N bars (beats run on across bar lines; notes past the loop are dropped). loop counts the part's own bars (those of
    the sections it plays), not the score's beats; a note that never lands in a bar makes the render warn. A negative
    beat is a pickup: it sounds before the first bar of every loop window (with the default loop 1, before every bar),
    even when the part is silent in the section before, but not before the score starts; its c and s tokens read the
    chord of the bar it leads into. pitch: a token, a list (a chord), "chord" or null (a drum); vel default 0.8; art:
    "o" for drums, or per-note knobs such as {"slide": -2}, or {"to": 0.9}: a hairpin, the note's velocity moving in a
    straight line from vel to 0.9 over its length, then holding (a tremolo's strikes follow it).
  Section counting: a part that plays several sections counts its bar lists and its loop from its own first bar, so a
    list given in by_section for a later section can start part-way through; the render warns when it does and names
    the bar. "index": "section" on the part (or "pattern_index": "section" on the score) counts both from the first
    bar of each section instead.
  Motifs: "motifs": {"A": {"notes": [[0, 1, "d1"], [1, 2, "d5"], [3, 1, "d4"], [4, 1, "d3"]]}} defines a phrase once;
    any note list calls it, {"motif": "A", "at": 8, "shift": 2}, and the call unfolds in place into plain notes (a
    pattern can also be a single call: "pattern": {"motif": "A"}). Ops: shift (scale steps), transpose, octave,
    invert, retro, augment, diminish, rhythm, take / drop / slice, mode, legato, then vels / vel, then repeat with every,
    shift_each, transpose_each and vel_each (sequences). take / drop / slice given as keys run first, then the
    "transform" list in its order, then the other keys in a fixed order; tools/audio/motifs.py has the syntax.
  Pitch tokens, against the chord sounding at that moment, in the part's octave:
    c0 c1 c2 c3 … chord tones (root 3rd 5th 7th; past the top they wrap up an octave, c-1 = top tone an octave down)
    s0 s1 s-2 …  scale steps from the chord root · d1 … d7 degrees of the key · +7 -5 semitones from the root ·
    D4 Bb2 F#5 absolute · 60 a MIDI number · ' or , after a token: up or down an octave (c0, = a bass root)
    Scale: the key's mode, or the part's "scale": major minor dorian phrygian lydian mixolydian locrian harmonic melodic,
    penta (宫 in major, 羽 in minor), gong shang jue zhi yu (宫 商 角 徵 羽), blues, whole, chromatic.
  Chords: the roman numerals above plus b/# prefixes and qualities, e.g. V7 ii7 Imaj7 iiø7 vii°7 IV6 V9 Vsus4 I5 bVII;
    two chords in one slot ("ii7 V7") split the bar evenly. The old layers read only the first chord of a slot.
  Figures ("figure": name, its knobs beside it; "voicing": close | root | spread | guitar, "notes": count):
    sustain   one held chord (or "pitch" tokens) per chord change; "hold": "section" = one note for the whole section
    stab      short chord hits on "beats": [0, 1.5] ("len" in beats, default 0.3)
    strum     "pattern" on 8ths: D down, U up, d / u soft, X accent, x muted chuck, . let ring; "strings" 4 | 6, "spread" s
    walking   walking bass: root on 1, chord and scale steps, a chromatic approach into the next bar; "ghost" 0–1
    oompah    bass on beats 1 and 3 (root, then the fifth), chord between; waltz: bass on 1, chord on the rest. Both fit
              2-, 3- and 4-beat bars; "role": "bass" | "chord" splits them over two instruments. The bass sounds an
              octave below the part's c0: "octave": 3 puts it in octave 2, so give a bass-only part one octave more
    alberti · arp-up · arp-down · arp-updown   keyboard figures at "rate" (8 | 12 | 16 | 24), over "span" octaves
    ostinato  a "cell" of tokens at "rate", running on across bar lines ("reset": "bar" restarts it each bar)
    tremolo   rapid re-strikes (pipa 轮指, balalaika, mandolin) of the "pitch" tokens spread over the bar. On any part,
              "tremolo": Hz (or true) re-strikes every note of at least "tremolo_min" beats
    roots     the chord root at "rate" ("octaves": true alternates octaves, the synthwave bass)
    melody    a seeded placeholder tune in the scale on a rhythm "pattern" (chord tones on the beats)
  Dynamics: "dyn": {"1": -12, "8:3": 0, "12": -6} on a part is a gain line in dB over the whole score (bars counted in
    the whole score: "bar", "bar.beat" or "bar:beat"), flat before the first point and after the last: a fader ride on
    the part, so ringing notes follow it. In by_section, "cresc": [-8, 0] or "dim": [0, -12] is a line in dB across that
    section: everything the part sounds while it lasts follows the line (a note held over from before too); after it,
    whatever still rings keeps the end level, so a tail never jumps back up, and notes that start later play at their
    own level. A note counts by the section it belongs to, so one that starts early (onset_ms, humanize) still gets
    its own section's level. Textures follow the line in that section's bars. "vel_ramp": [0.6, 1.0] scales each note's
    velocity by its place in the section, so the timbre follows. Level changes glide over 10 ms. Ramp up to 0 dB rather
    than boosting: the mix is normalised to its peak, so a section pushed to +12 dB turns every other one down by
    about as much, and the soft clip flattens its top. dyn, cresc and dim are straight lines in dB; a hairpin (above)
    is a straight line in velocity.
  Feel: "swing" (score, section or part) delays each off-beat 8th: 0–0.33 is the delay as a fraction of an 8th (0.33 ≈
    triplet shuffle, 0.15–0.2 lazy); 0.5–0.75 is read as the first 8th's share of the beat (0.6 light, 0.667 triplet).
    "swing_unit": 16 swings 16ths. A part whose step grid does not line up with that unit (8th triplets, step 12, under
    8th swing) stays straight. "humanize" 0–1: seeded timing (±8 ms × h) and velocity jitter.
  Buses: "stereo": true writes stereo (pan, stereo instruments, decorrelated reverb); default mono. "space": dry | room |
    plate | hall | cathedral | gated, or {"type": "hall", "rt60": 3.2, "return_db": -2}; default room. "lofi":
    {"crackle": 0.3, "wow": 0.3, "lp": 6000, "hiss": 0.2} and "tape": 0–1 (saturation) act on the master. With parts,
    the mix is scaled to peak "drive" (default 1) before the old master: tanh, then peak-normalised to master_db.
    A lofi "lp" below about 6 kHz takes the hi-hats away (they sit above it); the audibility check measures parts before
    the master effects, so it cannot warn you: keep lp at 6 kHz or more, or give the hats more gain_db.
  Determinism: a part's random streams come from (seed, its "id" or instrument and occurrence, note index), so adding or
    removing a part never changes another part with a different instrument or id. Two parts of the same instrument
    without ids are seeded by position (the render warns): give them ids, or removing one re-seeds the later ones.
  Checks before anything renders, naming the part: an unknown instrument, section, space, duck target or by_section
    section; a duplicate id; a field that is not a finite number or out of range (pan beyond −1..1, step ≤ 0 …); a
    note-list entry that is not [beat, beats, …]; a strum without strokes; a pitch outside MIDI 0–127; a motif call
    naming no motif, with an unknown key, transform or mode, an op without its value, a count that is not whole, a
    fragment that keeps no note, vels of the wrong length, or a cycle; a stop outside its section, with an unknown key,
    a hold that is not true / false, or a keep that names no part; a dyn position that is not "bar", "bar.beat" or
    "bar:beat", or two at the same place; cresc / dim / vel_ramp outside by_section; a "to" hairpin in params.
  Every part must sound: a part with no notes, or whose loudest 50 ms stays below −40 dBFS (power averaged over the
    channels, or its peak − 18 dB) in the final file, stops the render with its name. Raise its gain_db, or mark it
    "quiet": true (which does not excuse a part with no notes).
  Memory: parts are mixed and dropped one by one. A 5-minute stereo score with 7 parts peaks at about 1.1 GB (macOS peak
    memory footprint; RSS reads higher because freed pages stay mapped), a 10-minute one at about 3.6 GB.
  Instruments (synthesis only, tools/audio/instruments.py; default octave in brackets where it matters):
    keys     piano (tone felt|bright, pedal) · epiano (trem) · harpsichord · celesta · musicbox · glockenspiel · toypiano ·
             organ (drawbars "888000000", leslie Hz, tone pipe)
    mallets  marimba · xylophone · vibraphone (motor Hz, depth, pedal)
    plucked  nylon · ukulele · harp · pizzicato · upright [2] · pipa · guqin (slide, bend, yin, nao, harm) · balalaika ·
             cimbalom; all take ring (let ring) and mute; a guqin harmonic is as loud as a plucked note of its pitch.
             celesta, musicbox, glockenspiel, toypiano, marimba, cimbalom and guqin take damp (stop at the note's end)
    modelled plucked strings as physical models, opt-in beside the voices above: guqin_pm [3] · pipa_pm · harp_pm ·
             nylon_pm [3] · ukulele_pm · upright_pm [2] · balalaika_pm · cimbalom_pm, and guitar [3] (steel-string) · koto ·
             shamisen (buzz: sawari 0–1, stronger when plucked harder) · banjo · kalimba [5] · musicbox_pm [6]. The strings
             are digital waveguides: the pitch can move inside a note, high partials die first, a hard pluck starts a little
             sharp, and every note's tone peaks at the same level. Their knobs, as params or a note's: ring, damp, mute;
             slide, bend (semitones, ±36); vib (cents, or [Hz, cents, delay s]); yin, nao; harm (true, or the harmonic 2–8:
             a node harmonic, as loud as a pluck of its pitch); trem (Hz up to 40, or true: re-pluck the same string, 轮指);
             pos (pluck point 0.03–0.5), bright (0–1), decay (0.02–20, × the ring); out-of-range values are clamped.
             kalimba and musicbox_pm are modal bars and read only ring, damp and decay. A ringing note renders until it dies
             away or reaches its voice's limit (2.5–8 s, the bars 5 s; decay stretches it, up to 20 s), and there it fades
             over its last second. The part's "tremolo" works as for pipa. Switched from the Karplus–Strong voice, a part is
             about as loud at the default octave (±5 dB) and louder higher up, since those fade toward the top: 6–26 dB
             three octaves up (cimbalom 26, balalaika 17, pipa 16, ukulele 15, upright 13). Check its gain_db
    bowed    strings (section: marcato, attack, release) · violin · fiddle · cello [3] · banhu — the solo ones are mono:
             notes less than 40 ms apart join into one phrase and glide (glide s), vibrato (vib [Hz, cents, delay]), scoop
             into notes (scoop semitones); "retrigger": true (param, section param or a note's knob) gives every note
             its own attack instead
    winds    flute · xiao [4] · whistle (kind lips|tin) · suona — mono like the solo strings · sheng (笙, poly: reed chords)
    brass    brass (section: stab, swell, mute) · braam (give it the root only; third 3|4)
    synth    pulse (duty, vib, chiparp [0, 4, 7]) · triangle · sq_bass · seq (cutoff, res, env, decay, attack s) · cs80 ·
             drone · polysynth · sub808 [1] (mono: glides on legato notes, retrigger for separate hits; drop, decay, drive) ·
             the old voices as saw_pad
             saw_lead saw_pluck synth_bass bell zheng dizi
    drums    kick snare rim brush ride hihat bb_kick bb_snare trap_hat trap_snare clap gated cowbell shaker bongo conga
             woodblock bangzi gong (tune, drop, decay) smallgong (rise) cymbals framedrum timpani clock metal noiseburst
             scratch noise chipkick danpigu luogu (锣鼓经 kit: 大锣 at 240 Hz, or params daluo Hz, or the part's "pitch";
             xiaoluo Hz), and the old taiko edm_kick edm_clap edm_hat.
             Pitched when the part gives "pitch" (timpani always: c0)
    textures vinyl · tape · hum (hz, fan) · wind · rain · roomtone — continuous over the part's sections
Beat map (<out>.beats.json): {"bpm","offset":0,"beats":[…],"downbeats":[…],
  "sections":[{"name","start","end","bars"}], "hits":[{"t","what"}]}  — engines read it for cuts and punches. Parts add
  hits ("hit": true or "section"), and each section stop one "stop:<section>".
Layers are simple subtractive/percussive synthesis (numpy + scipy); ~1–3 s to render a minute on Apple Silicon. Parts
cost more (each note is rendered once and cached per pitch, length and velocity step): a 5 s score with 9 parts takes
~1.5 s on an M3 Max; the heaviest voices are gong, luogu, braam, cs80 and cimbalom (~0.05–0.3 s per new note). The
physically modelled ones take up to ~0.05 s per new note, ~0.07–0.08 s for a long note whose pitch moves all through it
(a guqin slide, 吟 or 猱), and a one-second shamisen note 0.2 s at MIDI 96, 0.7 s at 108, 1.4 s from 114 up (the sawari
keeps every sample on the slow path).
"""
import json, os, re, sys, wave
import numpy as np
from scipy.signal import butter, lfilter, fftconvolve
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import instruments as ins
import motifs as mt

SR = 48000
NOTE = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
        "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
DEG = {"i": 0, "ii": 2, "iii": 3, "iv": 5, "v": 7, "vi": 8, "vii": 10}          # natural minor
DEG_MAJ = {"i": 0, "ii": 2, "iii": 4, "iv": 5, "v": 7, "vi": 9, "vii": 11}

EXAMPLE = {
    "bpm": 112, "key": "F", "mode": "minor", "seed": 7,
    "sections": [
        {"name": "intro", "bars": 4, "chords": ["i", "VI", "III", "VII"], "layers": ["pad", "arp"], "energy": 0.35},
        {"name": "build", "bars": 4, "chords": ["i", "VI", "III", "VII"], "layers": ["pad", "arp", "hats", "bass"], "energy": 0.6, "riser": True, "fill": True},
        {"name": "drop", "bars": 8, "chords": ["i", "VI", "III", "VII"], "layers": ["kick", "clap", "hats", "bass", "pad", "arp", "lead"], "energy": 1.0, "impact": True},
        {"name": "outro", "bars": 4, "chords": ["VI", "VII", "i", "i"], "layers": ["pad", "arp"], "energy": 0.3},
    ],
}
EXAMPLE_ZH = {   # D 羽 pentatonic (D F G A C), ~57 s
    "bpm": 84, "key": "D", "mode": "minor", "seed": 12,
    "sections": [
        {"name": "dawn", "bars": 4, "chords": ["i", "i", "VI", "VII"], "layers": ["bell", "pad"], "energy": 0.3},
        {"name": "theme", "bars": 4, "chords": ["i", "VII", "VI", "VII"], "layers": ["zheng", "dizi", "pad", "bell"], "energy": 0.5, "bend": True},
        {"name": "drums", "bars": 4, "chords": ["i", "VI", "VII", "i"], "layers": ["taiko", "zheng", "bass", "pad"], "energy": 0.8, "riser": True, "fill": True},
        {"name": "climax", "bars": 4, "chords": ["i", "VII", "VI", "VII"], "layers": ["taiko", "bell", "zheng", "dizi", "bass", "pad"], "energy": 1.0, "impact": True, "bend": True},
        {"name": "coda", "bars": 4, "chords": ["VI", "VII", "i", "i"], "layers": ["bell", "dizi", "pad"], "energy": 0.3},
    ],
}

def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)

def chord_notes(root_pc, mode, roman, octave=4):
    r = roman.strip().split()[0]
    if r.lower() not in DEG or mode not in ("minor", "major"):   # V7, bVII, iiø7 …, or a mode such as dorian: the parts'
        # parser, so layers and parts agree on every root; the layers play its triad (root, third or sus note, fifth)
        c = parse_chord(r, mode); base = 12 * (octave + 1) + root_pc + c[0]
        return [base + c[1][0], base + c[1][1], base + c[1][min(2, len(c[1]) - 1)]]
    minor_quality = r.islower()
    deg = (DEG if mode == "minor" else DEG_MAJ)[r.lower()]
    base = 12 * (octave + 1) + root_pc + deg
    third = 3 if minor_quality else 4
    return [base, base + third, base + 7]

def env(n, a, d, sustain=0.0, r=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4))
    decay = sustain + (1 - sustain) * np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    e = e * np.where(t > a, decay, 1.0)
    if r > 0:
        e *= np.clip((n / SR - t) / r, 0, 1)
    return e

def lp(x, fc, order=2):
    b, a = butter(order, min(fc, SR * 0.45) / (SR / 2), "low"); return lfilter(b, a, x)

def hp(x, fc, order=2):
    b, a = butter(order, fc / (SR / 2), "high"); return lfilter(b, a, x)

def saw(f, n, phase=0.0):
    t = np.arange(n) / SR; return 2 * ((f * t + phase) % 1.0) - 1

def add(buf, x, at):
    i = int(round(at * SR)); j = min(len(buf), i + len(x))
    if i < len(buf): buf[i:j] += x[: j - i]

# ---------- instruments ----------
def kick():
    n = int(0.45 * SR); t = np.arange(n) / SR; f = 45 + 110 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16) * 0.95

def clap(rng):
    n = int(0.25 * SR); x = hp(rng.standard_normal(n), 900) * env(n, 0.002, 0.07)
    for k in (0.012, 0.024): x[int(k * SR):] += 0.6 * x[: n - int(k * SR)]
    return lp(x, 7000) * 0.35

def hat(rng, open_=False):
    n = int((0.18 if open_ else 0.05) * SR); return hp(rng.standard_normal(n), 7000) * env(n, 0.001, 0.06 if open_ else 0.015) * 0.18

def pluck(freq, dur, bright):
    n = int(dur * SR); x = saw(freq, n) * 0.6 + saw(freq * 1.003, n) * 0.4
    return lp(x, 900 + 4500 * bright) * env(n, 0.003, 0.18) * 0.22

def pad(notes, dur, bright):
    n = int(dur * SR); x = np.zeros(n)
    for m in notes:
        for det in (-0.08, 0.0, 0.08):
            x += saw(mtof(m + det), n, phase=(m % 7) / 7)
    return lp(x / (3 * len(notes)), 500 + 2200 * bright) * env(n, 0.35, 10, 1.0, 0.4) * 0.5

def bass(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) * 0.8 + lp(saw(freq, n), 400) * 0.35
    return x * env(n, 0.005, 0.25, 0.4, 0.03) * 0.45

def lead(freq, dur, bright):
    n = int(dur * SR); t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.2, 0, 1)
    x = saw(freq, n) * 0.5 + np.sign(np.sin(2 * np.pi * freq * vib * t)) * 0.25
    return lp(x, 1800 + 3000 * bright) * env(n, 0.02, 0.5, 0.6, 0.08) * 0.16

def riser(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; k = t / dur
    noise = hp(rng.standard_normal(n), 300) * k ** 2 * 0.25
    tone = np.sin(2 * np.pi * np.cumsum(200 + 1600 * k ** 2) / SR) * k ** 3 * 0.12
    return lp(noise, 12000) + tone

def impact(rng):
    n = int(2.2 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.9) * 0.9
    return boom + lp(rng.standard_normal(n), 1500) * np.exp(-t / 0.35) * 0.3

# ---------- Chinese colour: bell zheng dizi taiko (each note has its own seeded rng, so adding a layer never changes the others) ----------
BELL = [(0.5, .25, 1.4), (1.0, 1.0, 1.0), (1.19, .6, .75), (2.0, .3, .5), (2.76, .35, .32), (3.9, .2, .2), (5.4, .12, .12), (6.9, .07, .08)]

def penta(root_pc, mode):  # pentatonic MIDI notes: a minor third in the mode (minor, dorian …) → 羽 (1 b3 4 5 b7), else 宫 (1 2 3 5 6)
    # up to MIDI 111: dizi grace notes sit ~2 octaves above the chord's scale note, so B minor or high chords need the headroom
    return [m for m in range(36, 112) if (m - root_pc) % 12 in ((0, 3, 5, 7, 10) if mode7(mode)[2] == 3 else (0, 2, 4, 7, 9))]

def near(scale, m): return min(range(len(scale)), key=lambda i: (abs(scale[i] - m), -scale[i]))

def bell(freq, rng, T=3.2):  # bianzhong-like: inharmonic partials (1.19 = the 侧鼓音 a minor third up), slow beating, long decay
    n = int(6.0 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for r, a, d in BELL:
        if freq * r < SR * 0.45:
            x += a * (np.sin(2 * np.pi * freq * r * t + rng.uniform(0, 2 * np.pi)) + 0.35 * np.sin(2 * np.pi * freq * r * 1.0016 * t)) * np.exp(-t / (T * d))
    x += lp(hp(rng.standard_normal(n), 700), 5000) * np.exp(-t / 0.006) * 0.5          # mallet
    return x * np.minimum(1, t / 0.0015) * np.clip((6.0 - t) / 0.5, 0, 1) * 0.18

def ks(f, n, t60, bright, rng):
    """Karplus–Strong string; f in Hz, scalar or per-sample (a bend). Vectorised one period-block at a time."""
    f = np.broadcast_to(np.asarray(f, float), (n,)); D = SR / f - 0.5; M = D.astype(int); q = D - M   # loop = M + q + ½
    rho = 10 ** (-3 / (t60 * f)); P = int(M.max()) + 3; N0 = int(SR / f[0]); c = 0.6 - 0.45 * bright
    x = lfilter([1 - c], [1, -c], rng.uniform(-1, 1, N0)); k = int(N0 * 0.15)
    x = x - np.concatenate([np.zeros(k), x[:-k]]); y = np.zeros(n + P); y[P:P + N0] = x - x.mean()   # pluck near the bridge
    for s in range(0, n, int(M.min())):
        e = min(n, s + int(M.min())); j = np.arange(s, e) - M[s:e] + P
        y[P + s:P + e] += rho[s:e] * 0.5 * ((1 - q[s:e]) * y[j] + y[j - 1] + q[s:e] * y[j - 2])
    return y[P:]

def zheng(f, dur, bright, rng):  # guzheng pluck; f may be a per-sample curve (按弦上滑)
    n = int(dur * SR); f0 = float(np.asarray(f).flat[0]); t60 = float(np.clip(2.6 * (262 / f0) ** 0.5, 0.8, 3.5))
    return lp(ks(f, n, t60, bright, rng), 2500 + 5000 * bright) * np.clip((dur - np.arange(n) / SR) / 0.05, 0, 1) * 0.64

def press(f0, semis, n, at=0.12, over=0.18):  # 按弦上滑: smooth press up by `semis` after the pluck, then a little 揉弦
    t = np.arange(n) / SR; u = np.clip((t - at) / over, 0, 1); u = u * u * (3 - 2 * u)
    return f0 * 2 ** ((semis * u + 0.12 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - at - over) / 0.2, 0, 1)) / 12)

def dizi(freq, dur, bright, rng, grace=None):  # bamboo flute: sine + triangle, band-passed breath, delayed vibrato, 倚音 grace
    n = int(dur * SR); t = np.arange(n) / SR
    fv = freq * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.3) / 0.4, 0, 1)) * (1 - 0.015 * np.exp(-t / 0.05))
    if grace: fv = np.where(t < 0.07, grace, fv)
    ph = 2 * np.pi * np.cumsum(fv) / SR; nz = rng.standard_normal(n)
    tone = 0.7 * np.sin(ph) + 0.25 * (2 / np.pi) * np.arcsin(np.sin(ph)) + 0.08 * np.sin(2 * ph)
    breath = lp(hp(nz, 1200), 6000) * (0.10 + 0.2 * np.exp(-t / 0.07)) + lp(hp(nz, freq * 0.8), freq * 1.25) * 0.6
    return lp(tone + breath, 2500 + 5000 * bright) * env(n, 0.06, 0.4, 0.85, 0.1) * 0.18

def taiko(rng, big=True):  # big drum: pitch-dropping sine + skin noise + stick
    n = int(1.3 * SR); t = np.arange(n) / SR; f0 = 55 if big else 85
    body = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.9 * np.exp(-t / 0.04))) / SR) * np.exp(-t / (0.55 if big else 0.3))
    skin = lp(hp(rng.standard_normal(n), 90), 700) * np.exp(-t / 0.08) * 0.7
    return (body + skin + hp(rng.standard_normal(n), 1500) * np.exp(-t / 0.003) * 0.3) * np.minimum(1, t / 0.001) * 0.6

ZHENG = [0, 1, 2, 4, 3, 2, 1, 2]                      # 8th-note pentatonic steps above the chord's scale note (cycled)
DIZI = [[(0, 1.5, 2), (1.5, 0.5, 3), (2, 2, 4), (4, 1, 3), (5, 1, 2), (6, 2, 0)],     # 2-bar phrases: (beat, beats, step)
        [(0, 1, 4), (1, 1, 5), (2, 1.5, 4), (3.5, 0.5, 3), (4, 3, 2), (7, 1, 1)]]
ZH = {"bell": 0.45, "zheng": 0.25, "dizi": 0.3, "taiko": 0.12}   # reverb send per layer (own hall, no kick pumping)

def render(score, stems=None, info=None):
    validate(score)   # parts-related fields only; stops with the part's name before anything renders
    rng = np.random.default_rng(score.get("seed", 7))
    sub = lambda *k: np.random.default_rng([int(score.get("seed", 7)), *k])   # per-note streams for the new layers
    bpm = float(score["bpm"]); beat = 60.0 / bpm
    meters = {int(k): int(v) for k, v in score.get("meters", {}).items()}   # {"11": 6}: bar 11 (1-based, whole score) is 6/4
    root = NOTE[score.get("key", "C")]; mode = score.get("mode", "minor"); scale = penta(root, mode)
    total_bars = sum(s["bars"] for s in score["sections"])
    dflt = int(score.get("beats_per_bar", 4))   # beats per bar unless meters says otherwise
    out = np.zeros(int((sum(meters.get(k, dflt) for k in range(1, total_bars + 1)) * beat + 3.0) * SR))
    sidechain = np.ones_like(out); zh, send = np.zeros_like(out), np.zeros_like(out); cache = {}
    beats, downbeats, secs, hits, bars = [], [], [], [], []
    K = kick(); t0 = 0.0
    def put(layer, x, at): add(zh, x, at); add(send, x * ZH[layer], at)
    for s in score["sections"]:
        e = float(s.get("energy", 0.7)); L = set(s.get("layers", [])); chords = s.get("chords", ["i"])
        nbs = [meters.get(len(bars) + b + 1, dflt) for b in range(s["bars"])]; sec = sum(nbs) * beat
        secs.append({"name": s["name"], "start": round(t0, 3), "end": round(t0 + sec, 3), "bars": s["bars"]})
        if s.get("impact"):
            add(out, impact(rng) * (0.6 + 0.4 * e), t0); hits.append({"t": round(t0, 3), "what": f"impact:{s['name']}"})
        for b in range(s["bars"]):
            nb = nbs[b]; tb = t0 + sum(nbs[:b]) * beat; notes = chord_notes(root, mode, chords[b % len(chords)])
            downbeats.append(round(tb, 3)); bars.append([len(bars) + 1, round(tb, 3), nb])
            if "pad" in L: add(out, pad(notes, nb * beat + 0.4, e), tb)
            for q in range(nb):
                tq = tb + q * beat; beats.append(round(tq, 3))
                last_beat = s.get("fill") and b == s["bars"] - 1 and q == nb - 1
                if "kick" in L and not last_beat:
                    add(out, K * (0.7 + 0.3 * e), tq)
                    i = int(tq * SR); m = min(len(out), i + int(0.22 * SR))
                    sidechain[i:m] = np.minimum(sidechain[i:m], 0.35 + 0.65 * np.linspace(0, 1, m - i) ** 0.7)
                if "clap" in L and q % 2 == 1: add(out, clap(rng) * e, tq)
                if "hats" in L:
                    add(out, hat(rng) * e, tq + beat / 2)
                    if e > 0.8: add(out, hat(rng) * 0.5 * e, tq + beat / 4); add(out, hat(rng) * 0.5 * e, tq + 3 * beat / 4)
                if "bass" in L:
                    for h in (0, 0.5):
                        add(out, bass(mtof(notes[0] - 24), beat / 2 * 0.9) * (0.6 + 0.4 * e), tq + h * beat)
                if "taiko" in L and not last_beat:   # big drum every other beat, 8th pickups, a 16th roll into a riser peak
                    if s.get("riser") and b == s["bars"] - 1 and q >= nb - 2:
                        taps = [(r / 4, r == 0 and q % 2 == 0, 0.35 + 0.65 * (q - nb + 2 + r / 4) / 2) for r in range(4)]
                    else:
                        taps = ([(0, True, 1.0)] if q % 2 == 0 else []) + \
                               ([(0.5, False, 0.55)] if (e >= 0.75 and q == nb - 1) or (e >= 0.9 and q == 1) else [])
                    for h, big, g in taps:
                        v = len(beats) % 3; key = ("taiko", big, v)
                        if key not in cache: cache[key] = taiko(sub(4, int(big), v), big)
                        put("taiko", cache[key] * g * (0.6 + 0.4 * e), tq + h * beat)
            if "arp" in L:
                seq = notes + [notes[0] + 12]
                for k16 in range(4 * nb):
                    add(out, pluck(mtof(seq[k16 % 4] + 12), beat / 2, e) * (0.5 + 0.5 * e), tb + k16 * beat / 4)
            if "lead" in L and b % 2 == 0:
                phrase = [notes[2] + 12, notes[1] + 12, notes[0] + 12, notes[1] + 12]
                for k, m in enumerate(phrase): add(out, lead(mtof(m), beat * 0.95, e), tb + k * beat * 2)
            a = near(scale, notes[0])
            if "bell" in L:   # strike the chord's scale note on the downbeat; a higher bell mid-bar when energy is high
                for at, i, g in [(0, a, 1.0)] + ([(nb // 2 * beat, a + 2, 0.45)] if e >= 0.7 and nb >= 3 else []):
                    if ("bell", i) not in cache: cache[("bell", i)] = bell(mtof(scale[i]), sub(2, scale[i]))
                    put("bell", cache[("bell", i)] * g * (0.5 + 0.5 * e), tb + at)
            if "zheng" in L:  # flowing 8ths (quarters when calm); with "bend", every 2nd bar ends on a pressed-up note
                bent = s.get("bend") and b % 2 == 1
                for k8 in range(2 * nb - (2 if bent else 0)):
                    if e < 0.5 and k8 % 2: continue
                    m = scale[a + ZHENG[k8 % 8]]; key = ("zheng", m, k8 % 3)
                    if key not in cache: cache[key] = zheng(mtof(m), 1.8, e, sub(1, m, k8 % 3))
                    put("zheng", cache[key] * (0.55 + 0.45 * e) * (1.0 if k8 % 2 == 0 else 0.8), tb + k8 * beat / 2)
                if bent:
                    lo, hi = scale[a + 1], scale[a + 2]; n = int(2.2 * SR)
                    put("zheng", zheng(press(mtof(lo), hi - lo, n), 2.2, e, sub(5, len(bars))) * (0.8 + 0.5 * e), tb + (nb - 1) * beat)
            if "dizi" in L and b % 2 == 0:   # 2-bar phrases on the scale around the chord, grace notes on long notes
                for at, ln, st in DIZI[(b // 2) % 2]:
                    if e < 0.5 and ln < 1.5: continue
                    m = scale[a + 5 + st]
                    put("dizi", dizi(mtof(m), ln * beat * 0.97, e, sub(3, len(bars), int(at * 2)),
                                     mtof(scale[a + 6 + st]) if ln >= 2 else None) * (0.6 + 0.4 * e), tb + at * beat)
        if s.get("riser"):
            rdb = s["riser"].get("gain_db", 0) if isinstance(s["riser"], dict) else s.get("riser_db", 0)
            add(out, riser(sec, rng) * 10 ** (float(rdb) / 20) if rdb else riser(sec, rng), t0)   # default: exactly as before
            hits.append({"t": round(t0 + sec, 3), "what": f"riser-peak:{s['name']}"})
        t0 += sec
    # pump everything except kick/impact would need stems; a gentle global pump reads as sidechain
    out *= 0.6 + 0.4 * sidechain
    if cache:   # the new layers skip the pump and get their own hall (RT60 ≈ 2.8 s, send high-passed so drums stay dry)
        hn = int(2.8 * SR); hr = sub(9).standard_normal(hn) * np.exp(-np.arange(hn) / SR / 0.41); hr[: int(0.025 * SR)] = 0
        out += zh + fftconvolve(hp(send, 180), lp(hr, 5000) / np.sqrt(np.sum(hr ** 2)))[: len(out)] * 0.7
    ir_n = int(1.6 * SR); ir = rng.standard_normal(ir_n) * np.exp(-np.arange(ir_n) / SR / 0.45)
    wet = fftconvolve(lp(out, 6000), ir)[: len(out)] * 0.012
    mix = out + wet
    if score.get("parts") or score.get("stereo") or score.get("lofi") or score.get("tape"):
        del out, sidechain, zh, send, wet   # the layers are mixed: free their buffers before the parts render (long scores)
        info_gain = [1.0]
        mix, checks = parts_bus(score, mix, hits, stems, info_gain)   # parts, stereo, spaces, lofi/tape; (n,) or (n, 2)
    if not np.isfinite(mix).all(): sys.exit("music: the mix has samples that are not finite numbers (NaN or inf)")
    mix = np.tanh(mix * 1.2) / np.tanh(1.2)
    peak = np.max(np.abs(mix)) or 1.0
    if score.get("parts"):   # every part must be heard: ≥ −40 dBFS (loudest 50 ms RMS, or its peak − 18 dB) in the final file
        g = 1.2 / np.tanh(1.2) * 10 ** (score.get("master_db", -1.0) / 20) / peak
        if info is not None:   # for tests and tools: each part's level as the check sees it, and stem → file gain (small signal)
            info.update(levels={k: round(20 * np.log10(v * g + 1e-12), 2) for k, v in checks}, gain=g * info_gain[0])
        low = [(k, 20 * np.log10(v * g + 1e-12)) for k, v in checks if v * g < 0.01]
        if low: sys.exit("music: inaudible part(s) " + ", ".join(f"{k} at {d:.0f} dBFS RMS" for k, d in low) +
                         ' (the floor is −40): raise gain_db, or mark the part "quiet": true if that is intended')
    mix *= 10 ** (score.get("master_db", -1.0) / 20) / peak
    end = int((t0 + 2.5) * SR); mix = mix[:end]
    fade = int(1.5 * SR); mix[-fade:] *= np.linspace(1, 0, fade) if mix.ndim == 1 else np.linspace(1, 0, fade)[:, None]
    beatmap = {"bpm": bpm, "offset": 0.0, "beats": beats, "downbeats": downbeats, "sections": secs, "hits": hits,
               "duration": round(len(mix) / SR, 3)}
    if "meters" in score or "beats_per_bar" in score: beatmap.update(bars=bars, bars_note="[bar number (1-based, whole score), start (s), beats in bar]")
    return mix, beatmap

# ======================= parts: instruments playing patterns (voices in tools/audio/instruments.py) =======================
import bisect, math
from collections import namedtuple

MODES = {"major": (0, 2, 4, 5, 7, 9, 11), "minor": (0, 2, 3, 5, 7, 8, 10), "dorian": (0, 2, 3, 5, 7, 9, 10),
         "phrygian": (0, 1, 3, 5, 7, 8, 10), "lydian": (0, 2, 4, 6, 7, 9, 11), "mixolydian": (0, 2, 4, 5, 7, 9, 10),
         "locrian": (0, 1, 3, 5, 6, 8, 10), "harmonic": (0, 2, 3, 5, 7, 8, 11), "melodic": (0, 2, 3, 5, 7, 9, 11)}
PENTA = {"gong": (0, 2, 4, 7, 9), "shang": (0, 2, 5, 7, 10), "jue": (0, 3, 5, 8, 10), "zhi": (0, 2, 5, 7, 9), "yu": (0, 3, 5, 7, 10)}
SCALES = {**MODES, **PENTA, **dict(zip("宫商角徵羽", PENTA.values())), "blues": (0, 3, 5, 6, 7, 10),
          "whole": (0, 2, 4, 6, 8, 10), "chromatic": tuple(range(12))}
ROMAN = {"i": 0, "ii": 1, "iii": 2, "iv": 3, "v": 4, "vi": 5, "vii": 6}
CHORD_RE = re.compile(r"^([b#]?)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)(.*)$")
TOK_RE = re.compile(r"^([csd])(-?\d+)$")
NOTE_RE = re.compile(r"^([A-G])([#b]?)(-?\d+)$")
GRID = {"X": (1.0, "", 1), "x": (0.72, "", 1), "g": (0.35, "", 1), "o": (0.72, "o", 1), "O": (1.0, "o", 1),
        "r": (0.55, "", "r"), "R": (0.75, "", "R"), "f": (0.72, "", "f")}
Chord = namedtuple("Chord", "pc iv")

def mode7(mode):   # the 7-note scale the roman numerals count in
    if mode in MODES: return MODES[mode]
    return MODES["minor" if mode in ("minor", "yu", "羽", "jue", "角", "shang", "商", "blues") else "major"]

def parse_chord(sym, mode):
    """roman chord → (root in semitones above the tonic, intervals): i IV bVII V7 ii7 Imaj7 iiø7 vii°7 IV6 V9 Vsus4 I5 …"""
    m = CHORD_RE.match(str(sym).strip())
    if not m: sys.exit(f"music: chord {sym!r}: write a roman numeral such as i, IV, bVII, V7, iiø7, Imaj7, vii°7")
    acc, rn, s = m.groups()
    third, fifth, ext, dim = (3 if rn.islower() else 4), 7, [], False
    def take(*ps):
        nonlocal s
        for p in ps:
            if s.startswith(p): s = s[len(p):]; return True
        return False
    if take("°", "dim", "o"): third, fifth, dim = 3, 6, True
    elif take("ø", "m7b5"): third, fifth, ext = 3, 6, [10]
    elif take("+", "aug"): third, fifth = 4, 8
    if take("maj9", "M9"): ext += [11, 14]
    elif take("maj7", "M7", "Δ"): ext += [11]
    elif take("13"): ext += [10, 14, 21]
    elif take("11"): ext += [10, 14, 17]
    elif take("9"): ext += [10, 14]
    elif take("7"): ext += [9 if dim else 10]
    elif take("6"): ext += [9]
    elif take("5"): third = None
    if take("sus4"): third = 5
    elif take("sus2"): third = 2
    if take("add9"): ext += [14]
    if s: sys.exit(f"music: chord {sym!r}: cannot read {s!r} (qualities: 7 maj7 6 9 11 13 ø ° + sus2 sus4 add9 5)")
    iv = sorted({0, fifth, *ext} | ({third} if third is not None else set()))
    return mode7(mode)[ROMAN[rn.lower()]] + {"b": -1, "#": 1, "": 0}[acc], tuple(iv)

class Bar:   # one bar of the score as the parts see it
    pass

class Ctx:
    def __init__(self, score):
        self.key_pc = NOTE[score.get("key", "C")]; self.mode = score.get("mode", "minor"); self.seed = int(score.get("seed", 7))
        self.beat = 60.0 / float(score["bpm"]); self.swing = float(score.get("swing", 0))
        self.swing_unit = int(score.get("swing_unit", 8)); self.humanize = float(score.get("humanize", 0)); self._sc, self._ch = {}, {}
        self.motifs = score.get("motifs", {}); self.index = score.get("pattern_index", "part")   # "section": lists count from each section
        meters = {int(k): int(v) for k, v in score.get("meters", {}).items()}; dflt = int(score.get("beats_per_bar", 4))
        self.grid, t0 = [], 0.0   # same arithmetic as render(), so parts sit on exactly the same bar lines
        for si, s in enumerate(score["sections"]):
            nbs = [meters.get(len(self.grid) + b + 1, dflt) for b in range(s["bars"])]; chords = s.get("chords", ["i"])
            for b in range(s["bars"]):
                B = Bar(); B.i, B.sec, B.si, B.b, B.nb = len(self.grid), s["name"], si, b, nbs[b]
                B.tb = t0 + sum(nbs[:b]) * self.beat; B.sec_beats = sum(nbs); B.swing = s.get("swing"); B.sec_off = sum(nbs[:b])
                syms = str(chords[b % len(chords)]).split(); B.chords = [(j * nbs[b] / len(syms), self.chord(c)) for j, c in enumerate(syms)]
                self.grid.append(B)
            t0 += sum(nbs) * self.beat

    def at(self, pos):
        """A position in the whole score → seconds (see bar_beat). A bar past the end means the end."""
        b, q = bar_beat(pos, "position")
        if b > len(self.grid): return self.grid[-1].tb + self.grid[-1].nb * self.beat
        return self.grid[b - 1].tb + (q - 1) * self.beat

    def chord(self, sym):
        if sym not in self._ch:
            r, iv = parse_chord(sym, self.mode); self._ch[sym] = Chord((self.key_pc + r) % 12, iv)
        return self._ch[sym]

    def scale(self, name=None):
        name = name or "_mode"
        if name not in self._sc:
            if name == "_mode": pcs = mode7(self.mode)
            elif name == "penta": pcs = PENTA["yu" if mode7(self.mode)[2] == 3 else "gong"]
            elif name in SCALES: pcs = SCALES[name]
            else: sys.exit(f"music: scale {name!r}: use {', '.join(['penta', *SCALES])}")
            self._sc[name] = [m for m in range(128) if (m - self.key_pc) % 12 in pcs]
        return self._sc[name]

def chord_at(B, pos):
    ch = B.chords[0][1]
    for p, c in B.chords:
        if p <= pos + 1e-9: ch = c
    return ch

def resolve(tok, ch, O, key_pc, sc):
    """A pitch token → MIDI (float), or None for a rest."""
    if tok is None: return None
    if isinstance(tok, (int, float)): return float(tok)
    t = str(tok).strip()
    if t in ("", ".", "r", "-", "_"): return None
    up = t.count("'") - t.count(","); t = t.replace("'", "").replace(",", ""); root = 12 * (O + 1) + ch.pc
    at = lambda i: sc[min(max(i, 0), len(sc) - 1)]
    m = TOK_RE.match(t)
    if m:
        k = int(m.group(2))
        if m.group(1) == "c": v = root + ch.iv[k % len(ch.iv)] + 12 * (k // len(ch.iv))
        elif m.group(1) == "s": v = at(bisect.bisect_right(sc, root) - 1 + k)
        else: v = at(bisect.bisect_right(sc, 12 * (O + 1) + key_pc) - 1 + k - 1)
    elif re.fullmatch(r"[+-]\d+", t): v = root + int(t)
    elif t.isdigit(): v = int(t)
    elif NOTE_RE.match(t): n = NOTE_RE.match(t); v = 12 * (int(n.group(3)) + 1) + NOTE[n.group(1) + n.group(2)]
    else:
        hint = (f' A drum stroke goes in the 5th slot: [beat, beats, null, vel, "{t}"].' if t in GRID or t in ins.LUOGU else "")
        sys.exit(f"music: pitch {tok!r}: use c0 c1 … (chord tones), s0 s1 … (scale steps), d1 … (key degrees), +7, D4, 60.{hint}")
    return float(v + 12 * up)

def voicing(ch, O, cfg):
    """The chord as MIDI notes: close (inside one octave from C#, smooth changes), root, spread (+ bass), guitar (6 strings)."""
    kind = cfg.get("voicing", "close"); root = 12 * (O + 1) + ch.pc; iv = ch.iv
    if kind == "root": v = [root + i for i in iv]
    elif kind == "guitar":
        r = root - 12; th = iv[1] if len(iv) > 2 else iv[-1]; fi = iv[2] if len(iv) > 2 else 7
        v = sorted([r, r + fi, r + 12, r + 12 + th, r + 12 + fi, r + 12 + iv[3] if len(iv) > 3 else r + 24])
    else:
        base = 12 * (O + 1) + 1; v = sorted({base + (root + i - base) % 12 for i in iv})
        if kind == "spread": v = [root - 12] + v
    n = cfg.get("notes")
    if n: v = (v + [x + 12 for x in v] + [x + 24 for x in v])[:int(n)]
    return [float(x) for x in v]

def swing_amount(v):
    """0–0.33: how late the off-beat is, as a fraction of a step; 0.5–0.75: the first step's share of the pair (0.667 = triplet)."""
    v = float(v or 0); return 2 * v - 1 if v >= 0.5 else v

def warp(p, s, u):
    """Swing: inside each pair of `u`-beat steps the off-beat moves late by s·u (0.33 of an 8th ≈ a triplet shuffle)."""
    if not s: return p
    q = math.floor(p / (2 * u) + 1e-9) * 2 * u; x = p - q
    return q + (x * (1 + s) if x < u else u * (1 + s) + (x - u) * (1 - s))

def _num(v, what, lo=None, hi=None, above=None):
    """A finite number (a numeric string or a bool is read as one), optionally ≥ lo, ≤ hi, > above; otherwise stop."""
    try: x = float(v)
    except (TypeError, ValueError): sys.exit(f"music: {what} must be a number, not {v!r}")
    if not math.isfinite(x): sys.exit(f"music: {what} must be a finite number, not {v!r}")
    if (lo is not None and x < lo) or (hi is not None and x > hi) or (above is not None and x <= above):
        want = " and ".join(w for w in (f"≥ {lo:g}" if lo is not None else "", f"≤ {hi:g}" if hi is not None else "",
                                        f"> {above:g}" if above is not None else "") if w)
        sys.exit(f"music: {what} must be {want}, not {v!r}")
    return x

PART_NUM = {   # numeric part fields (also inside by_section): (≥ lo, ≤ hi, > above)
    "gain_db": (None, None, None), "vel": (0, None, None), "pan": (-1, 1, None), "send": (0, None, None), "detune": (None, None, None),
    "onset_ms": (None, None, None), "humanize": (0, None, None), "swing": (0, 0.75, None), "drive": (0, None, None), "lp": (None, None, 0),
    "hp": (None, None, 0), "step": (None, None, 0), "rate": (None, None, 0), "legato": (0, None, None), "len": (0, None, None),
    "octave": (-1, 9, None), "tremolo_min": (0, None, None), "ghost": (0, 1, None), "span": (1, None, None), "strings": (1, None, None),
    "spread": (0, None, None), "bass_len": (0, None, None), "loop": (1, None, None), "roll": (1, None, None), "swing_unit": (8, 16, None)}

def bar_beat(pos, what):
    """ "20:3.5" (bar 20, beat 3.5), "20.3" (bar 20, beat 3) or "20" (its downbeat) → (20, 3.5); both count from 1."""
    m = re.fullmatch(r"(\d+)(?::(\d+(?:\.\d+)?)|\.(\d+))?", str(pos).strip())
    if not m or int(m.group(1)) < 1 or float(m.group(2) or m.group(3) or 1) < 1:
        sys.exit(f'music: {what} {pos!r}: write "bar", "bar.beat" or "bar:beat" (e.g. "20:3.5"); bars and beats count from 1')
    return int(m.group(1)), float(m.group(2) or m.group(3) or 1)

def _is_grid(pat):
    return isinstance(pat, (str, dict)) or (isinstance(pat, list) and bool(pat) and isinstance(pat[0], str))

def _check_notes(pv, w_):
    for j, ev in enumerate(pv):
        if not isinstance(ev, (list, tuple)) or len(ev) < 2:
            sys.exit(f'music: {w_}: note {j} of the note list is {ev!r}; write [beat, beats, pitch, vel, art] or a motif call')
        _num(ev[0], f"{w_}: note {j} beat"); _num(ev[1], f"{w_}: note {j} length", 0)
        if len(ev) > 3 and ev[3] is not None: _num(ev[3], f"{w_}: note {j} velocity", 0)
        if len(ev) > 4 and not isinstance(ev[4], (str, dict)): sys.exit(f'music: {w_}: note {j}: the 5th slot is a stroke ("o") or an object of knobs')
        if len(ev) > 4 and isinstance(ev[4], dict) and "to" in ev[4]: _num(ev[4]["to"], f"{w_}: note {j} hairpin \"to\"", 0)
        if len(ev) > 4 and isinstance(ev[4], dict) and ev[4].get("_scale", "penta") not in ("penta", *SCALES):   # a motif call's mode
            sys.exit(f"music: {w_}: mode {ev[4]['_scale']!r}: use {', '.join(['penta', *SCALES])}")

def validate(score):
    """One pass over the parts-related fields before anything renders, naming the part (or field) that is wrong."""
    parts = score.get("parts")
    if parts is None: parts = []
    if not isinstance(parts, list): sys.exit('music: "parts" must be a list: [{"inst": …}, …]')
    secs = {s.get("name") for s in score["sections"]}
    for k, (lo, hi, above) in {"swing": (0, 0.75, None), "humanize": (0, None, None), "drive": (None, None, 0), "swing_unit": (8, 16, None),
                               "master_db": (None, None, None)}.items():
        if k in score: _num(score[k], k, lo, hi, above)
    if "swing_unit" in score and float(score["swing_unit"]) not in (8, 16): sys.exit('music: "swing_unit" is 8 or 16')
    for s in score["sections"]:
        if "swing" in s: _num(s["swing"], f"section {s.get('name')!r} swing", 0, 0.75)
        if "riser_db" in s: _num(s["riser_db"], f"section {s.get('name')!r} riser_db")
        if isinstance(s.get("riser"), dict) and "gain_db" in s["riser"]: _num(s["riser"]["gain_db"], f"section {s.get('name')!r} riser gain_db")
    if "space" in score:
        sp = score["space"] if isinstance(score["space"], dict) else {"type": score["space"]}
        if sp.get("type", "room") not in ("dry", *ins.SPACES): sys.exit(f"music: space {sp.get('type')!r}: use dry {' '.join(ins.SPACES)}")
        if "rt60" in sp: _num(sp["rt60"], "space rt60", above=0)
        if "return_db" in sp: _num(sp["return_db"], "space return_db")
    if isinstance(score.get("lofi"), dict):
        for k in ("crackle", "wow", "hiss"):
            if k in score["lofi"]: _num(score["lofi"][k], f"lofi {k}", 0)
        if "lp" in score["lofi"]: _num(score["lofi"]["lp"], "lofi lp", above=0)
    if score.get("tape") not in (None, False, True): _num(score["tape"], "tape", 0)
    motifs = score.get("motifs", {})
    if not isinstance(motifs, dict): sys.exit('music: "motifs" maps names to notes: {"A": {"notes": [[0, 1, "d1"], …]}, …}')
    for name in motifs: _check_notes(mt.motif_notes(motifs, name, "motifs")[0], f"motif {name!r}")
    if score.get("pattern_index", "part") not in ("part", "section"): sys.exit('music: "pattern_index" is "part" or "section"')
    meters = {int(k): int(v) for k, v in score.get("meters", {}).items()}; dflt = int(score.get("beats_per_bar", 4))
    ids, keys, idless = set(), set(), {}
    for i, part in enumerate(parts):
        if not isinstance(part, dict) or "inst" not in part: sys.exit(f'music: part {i} must be an object with an "inst", e.g. {{"inst": "piano", "figure": "sustain"}}')
        inst = part["inst"]
        if inst not in ins.INSTR: sys.exit(f"music: part {i}: instrument {inst!r} unknown; --instruments lists them")
        if "id" in part:
            if not isinstance(part["id"], str) or not part["id"]: sys.exit(f"music: part {i} ({inst}): \"id\" must be a non-empty string")
            if part["id"] in ids: sys.exit(f"music: two parts share the id {part['id']!r}: ids name the parts and seed them, so each must be unique")
            ids.add(part["id"])
        else: idless[inst] = idless.get(inst, 0) + 1
        keys |= {inst, part.get("id")}
    labels = {p.get("id") or f"{p['inst']}#{sum(1 for q in parts[:j] if q['inst'] == p['inst'] and 'id' not in q)}" for j, p in enumerate(parts)}
    nbars = 0
    for s in score["sections"]:
        stp, w_ = s.get("stop"), f"section {s.get('name')!r} stop"
        if stp is not None and stp is not False:
            if stp is True: stp = {}   # every part stops at the section's first beat
            elif not isinstance(stp, dict) or not stp:
                sys.exit(f'music: {w_}: write {{"at": "5:2", "keep": ["pad"]}}, or true to stop every part from the section\'s first beat, not {stp!r}')
            if not parts: sys.exit(f"music: {w_}: a stop acts on parts, and this score has none")
            if set(stp) - {"at", "bar", "beat", "keep", "tail", "hold"}:
                sys.exit(f"music: {w_}: unknown key(s) {sorted(set(stp) - {'at', 'bar', 'beat', 'keep', 'tail', 'hold'})}; use at (or bar, beat), keep, tail, hold")
            bar, beat = stop_at(stp, w_); _num(bar, f"{w_} bar", 1, s["bars"]); _num(beat, f"{w_} beat", 1, meters.get(nbars + bar, dflt) + 0.999)
            _num(stp.get("tail", 0.15), f"{w_} tail", 0)
            if "hold" in stp and not isinstance(stp["hold"], bool): sys.exit(f"music: {w_}: hold is true or false, not {stp['hold']!r}")
            keep = stp.get("keep", [])
            if not isinstance(keep, list) or not all(isinstance(k, str) for k in keep):
                sys.exit(f'music: {w_}: keep is a list of part ids or instruments, e.g. ["pad"], not {keep!r}')
            if set(keep) - labels - keys:
                sys.exit(f"music: {w_}: keep names no part: {sorted(set(keep) - labels - keys)} (use ids or instruments)")
        nbars += s["bars"]
    for i, part in enumerate(parts):   # the same labels the renderer uses: the id, or instrument#occurrence
        name = part.get("id") or f"{part['inst']}#{sum(1 for p in parts[:i] if p['inst'] == part['inst'] and 'id' not in p)}"
        bs = part.get("by_section", {})
        if not isinstance(bs, dict): sys.exit(f'music: part {name}: "by_section" must map section names to overrides, e.g. {{"b": {{"gain_db": -6}}}}')
        for sec, o in bs.items():
            if sec not in secs: sys.exit(f"music: part {name}: by_section names no section {sec!r} (sections: {', '.join(map(str, secs))})")
            if not isinstance(o, dict): sys.exit(f"music: part {name}: by_section[{sec!r}] must be an object of overrides, not {o!r}")
        if part.get("index", "part") not in ("part", "section"): sys.exit(f'music: part {name}: "index" is "part" or "section"')
        dyn = part.get("dyn")
        if dyn is not None:
            if not isinstance(dyn, dict) or not dyn: sys.exit(f'music: part {name}: "dyn" maps positions to dB: {{"16": -12, "20:3": -4}}')
            seen_ = {}
            for pos_, v in dyn.items():
                bar, beat = bar_beat(pos_, f"part {name}: dyn position")
                if bar <= nbars: _num(beat, f"part {name}: dyn {pos_!r} beat", 1, meters.get(bar, dflt) + 0.999)
                _num(v, f"part {name}: dyn {pos_!r}")
                if (bar, beat) in seen_: sys.exit(f"music: part {name}: dyn {seen_[(bar, beat)]!r} and {pos_!r} are the same position")
                seen_[(bar, beat)] = pos_
        for key in ("cresc", "dim", "vel_ramp"):
            if key in part: sys.exit(f'music: part {name}: {key} goes in by_section, for one section: "by_section": {{"b": {{"{key}": […]}}}} ("dyn" shapes the whole part)')
        for sec, o in bs.items():
            if "cresc" in o and "dim" in o: sys.exit(f"music: part {name} in section {sec!r}: give cresc or dim, not both")
            for key in ("cresc", "dim", "vel_ramp"):
                if key in o:
                    if not isinstance(o[key], list) or len(o[key]) != 2: sys.exit(f"music: part {name} in section {sec!r}: {key} is [from, to]")
                    for v in o[key]: _num(v, f"part {name} in section {sec!r}: {key}", 0 if key == "vel_ramp" else None)
        for cfg, where in [(part, f"part {name}")] + [({**part, **o}, f"part {name} in section {sec!r}") for sec, o in bs.items()]:
            for k, (lo, hi, above) in PART_NUM.items():
                if k in cfg: _num(cfg[k], f"{where}: {k}", lo, hi, above)
            if cfg.get("tremolo") not in (None, False, True): _num(cfg["tremolo"], f"{where}: tremolo (strikes a second)", hi=50, above=0)
            if not isinstance(cfg.get("params", {}), dict): sys.exit(f'music: {where}: "params" must be an object')
            if "to" in cfg.get("params", {}): sys.exit(f'music: {where}: "to" is one note\'s hairpin; write it in the note: [0, 4, "d1", 0.4, {{"to": 0.9}}]')
            pat = cfg.get("pattern")
            if mt.is_call(pat): pat = [pat]   # a single motif call is a note list
            for key_, pv in (pat.items() if isinstance(pat, dict) else [(None, pat)]):   # a dict: a grid or a one-bar note list per bar length
                w_ = f"{where} (pattern {key_!r})" if key_ is not None else where
                if key_ is not None and mt.is_call(pv): pv = [pv]   # a single motif call is a one-bar note list here too
                if isinstance(pv, list) and pv and not all(isinstance(e, str) for e in pv):
                    pv = mt.expand_pattern(pv, motifs, w_)   # motif calls → notes (a bad call stops here with its part)
                    if key_ is not None and not all(isinstance(e, (list, tuple)) for e in pv):
                        sys.exit(f"music: {w_}: inside a dict, a pattern is a grid string or a note list (one bar), not {pv!r}")
                    _check_notes(pv, w_)
                elif pv is not None and not isinstance(pv, (str, list) if key_ is not None else (str, dict, list)):
                    sys.exit(f"music: {w_}: \"pattern\" is a grid string, a list of them, a dict by beats per bar, or a note list")
            if cfg.get("figure") == "strum" and pat is not None:
                grids = [pat] if isinstance(pat, str) else pat if isinstance(pat, list) else None
                if not grids or not all(isinstance(g, str) for g in grids):
                    sys.exit(f"music: {where}: a strum pattern is a string, or a list of strings (one per bar), not {pat!r}")
                if not all(g.replace(" ", "").replace("|", "") for g in grids):
                    sys.exit(f"music: {where}: the strum pattern {pat!r} has no strokes; write D U d u X x and . (e.g. \"D.DU.UDU\")")
        if part.get("index", score.get("pattern_index", "part")) != "section":   # a later section's list or loop starting part-way through
            names_ = part.get("sections", "all"); names_ = [names_] if isinstance(names_, str) and names_ != "all" else names_
            before, warned = 0, set()
            for x in score["sections"]:
                if names_ != "all" and x["name"] not in names_: continue
                o = bs.get(x["name"]); pv = None if o is None else o.get("pattern", part.get("pattern") if "loop" in o else None)
                n_, what = 1, ""
                if isinstance(pv, list) and len(pv) > 1 and all(isinstance(e, str) for e in pv): n_, what = len(pv), "list"
                elif _is_notes(pv) or mt.has_calls(pv): n_, what = int(_num(o.get("loop", part.get("loop", 1)), f"part {name}: loop")), "loop"
                if before and n_ > 1 and before % n_ and x["name"] not in warned:
                    warned.add(x["name"])
                    print(f"music: warning: part {name}: section {x['name']!r} starts on bar {before % n_ + 1} of its {n_}-bar {what}, because "
                          f"the part has played {before} bars before it; add \"index\": \"section\" to start it at the section's first bar", file=sys.stderr)
                before += x["bars"]
        dk = part.get("duck")
        if dk is not None:
            by = dk if isinstance(dk, str) else dk.get("by") if isinstance(dk, dict) else None
            if by not in keys - {None}: sys.exit(f'music: part {name}: duck {dk!r} names no part (by an "inst" or an "id" of this score)')
            if isinstance(dk, dict):
                for k in ("depth", "release"):
                    if k in dk: _num(dk[k], f"part {name}: duck {k}", 0)
        if isinstance(part.get("delay"), dict):
            for k in ("beats", "fb", "mix"):
                if k in part["delay"]: _num(part["delay"][k], f"part {name}: delay {k}", 0)
            if "lp" in part["delay"]: _num(part["delay"]["lp"], f"part {name}: delay lp", above=0)
    dup = {k: n for k, n in idless.items() if n >= 2}
    if dup:
        print("music: warning: " + ", ".join(f"{n} {k} parts" for k, n in dup.items()) + ' have no "id"; they are seeded by position, '
              'so removing one changes the sound of the later ones. Give each an "id" to keep it fixed.', file=sys.stderr)

def steps_in(B, step):
    """Steps of a grid that start inside the bar: ceil, so a half note in a 5-beat bar gives 3 (the last one cut at the bar
    line) and one in a 1-beat bar still sounds. Exact divisions give the same count as before."""
    return int(math.ceil(B.nb * step / 4 - 1e-9))

def _cut(pos, dur, B):   # a step that runs past the bar line ends there
    return B.nb - pos if pos + dur > B.nb + 1e-9 else dur

def _is_notes(x): return isinstance(x, list) and bool(x) and isinstance(x[0], (list, tuple))

def pick_grid(pat, B, k):
    if isinstance(pat, dict): return pat.get(str(B.nb), pat.get("*"))
    if isinstance(pat, list): return pat[k % len(pat)] if pat else None
    return pat

def grid_events(pat, B, k, cfg, pitched, res, st, cx, O):
    s = pick_grid(pat, B, k)
    chars = [c for c in (s or "") if c not in " |"]
    if not chars: return []
    step = float(cfg.get("step", 16)); slot = 4.0 / step; ns = steps_in(B, step); roll = int(cfg.get("roll", 2))
    pl = cfg.get("pitch") or ["c0"]; pl = pl if isinstance(pl, list) else [pl]
    if cfg.get("pitch_cycle") != "part": st["pi"] = 0
    out, last = [], None
    for j in range(ns):
        c = chars[j % len(chars)]; pos = j * slot
        if c == "~":
            if last: last[1] += slot
            continue
        if c in ".-_" or c == "0": last = None; continue
        if c.isdigit(): vel, art, kind = int(c) / 10, "", 1
        elif c in GRID: vel, art, kind = GRID[c]
        elif c in ins.LUOGU and cfg.get("inst") == "luogu": vel, art, kind = 0.9, c, 1
        else: sys.exit(f"music: grid character {c!r}: use X x g o O r R f 1-9 ~ . - _ (spaces and | are ignored; "
                       f"luogu also reads {''.join(ins.LUOGU)})")
        p = None
        if pitched:
            if cfg.get("chord"): p = voicing(chord_at(B, pos), O, cfg)
            else:
                i = st.get("pi", 0); st["pi"] = i + 1; tok = pl[i % len(pl)]
                p = [m for m in (res(x, pos) for x in (tok if isinstance(tok, list) else [tok])) if m is not None]
                if not p: last = None; continue
        if kind == "f":
            out.append([pos - 0.025 / cx.beat, slot, p, vel * 0.45, art, {}])
        if kind in ("r", "R"):
            h = roll if kind == "r" else roll + 1
            out += [[pos + i * slot / h, slot / h, p, vel, art, {}] for i in range(h)]; last = None
        else:
            last = [pos, slot, p, vel, art, {}]; out.append(last)
    for e in out: e[1] = _cut(e[0], e[1], B)
    if pitched:
        for e in out: e[1] *= float(cfg.get("legato", 0.9))
    return out

def scale_step(m, n, sc):
    """m moved n steps along the scale sc (a note between scale notes keeps its distance from the one below)."""
    i = bisect.bisect_right(sc, m + 1e-9) - 1; return sc[min(max(i + n, 0), len(sc) - 1)] + (m - sc[max(i, 0)])

def note_list(pat, B, k, cfg, pbars, pitched, res, O, cx=None, seen=None):
    loop = int(cfg.get("loop", 1)); k0 = k - k % loop; off = sum(pb.nb for pb in pbars[k0:k]); out = []
    for j, ev in enumerate(pat):
        b, d = float(ev[0]), float(ev[1])
        if not (off <= b < off + B.nb or (b < 0 and k == k0)): continue   # a negative beat: a pickup before the window
        if seen is not None: seen.add(j)
        pos = b - off; vel = float(ev[3]) if len(ev) > 3 and ev[3] is not None else 0.8
        tok = ev[2] if len(ev) > 2 and ev[2] is not None else ((cfg.get("pitch") or "c0") if pitched else None)
        art = ev[4] if len(ev) > 4 else ""
        kn = {}
        if isinstance(art, dict) and any(x in art for x in mt.KNOBS + ("_stroke",)):   # left by a motif transform
            kn = {x: art[x] for x in mt.KNOBS + ("_stroke",) if x in art}; art = {x: v for x, v in art.items() if x not in kn}
            if not art and "_stroke" in kn: art = kn["_stroke"]
        r_ = res if "_scale" not in kn else (lambda tok, pos: resolve(tok, chord_at(B, pos), O, cx.key_pc, cx.scale(kn["_scale"])))
        if tok == "chord": p = voicing(chord_at(B, pos), O, cfg)
        elif tok is None and not pitched: p = None
        else:
            p = [m for m in (r_(x, pos) for x in (tok if isinstance(tok, list) else [tok])) if m is not None]
            if not p: continue
        for op, v in kn.get("_ops", ()):   # pitch ops a motif transform left for after the pitch resolved, in their order
            if not p: break
            p = [scale_step(m, v, cx.scale(kn.get("_scale") or cfg.get("scale"))) for m in p] if op == "shift" else [m + v for m in p]
        out.append([pos, d, p, vel, art if isinstance(art, str) else "", art if isinstance(art, dict) else {}])
    return out

def _tokens(cfg, res, pos):
    toks = cfg.get("pitch"); toks = toks if isinstance(toks, list) else [toks]
    return [m for m in (res(t, pos) for t in toks) if m is not None]

def fig_sustain(B, k, cfg, O, res, cx, st, R):
    notes = lambda pos: _tokens(cfg, res, pos) if cfg.get("pitch") else voicing(chord_at(B, pos), O, cfg)
    if cfg.get("hold") == "section": return [[0.0, B.sec_beats, notes(0), 0.8, "", {}]] if B.b == 0 else []
    segs = B.chords + [(B.nb, None)]
    return [[p0, p1 - p0, notes(p0), 0.8, "", {}] for (p0, _), (p1, _) in zip(segs, segs[1:])]

def fig_stab(B, k, cfg, O, res, cx, st, R):
    pat = cfg.get("pattern")
    if isinstance(pat, (str, dict)) or (isinstance(pat, list) and pat and isinstance(pat[0], str)):
        return grid_events(pat, B, k, {**cfg, "chord": not cfg.get("pitch")}, True, res, st, cx, O)
    ln = float(cfg.get("len", 0.3))
    return [[float(b), ln, _tokens(cfg, res, b) if cfg.get("pitch") else voicing(chord_at(B, b), O, cfg), 0.9, "", {}]
            for b in cfg.get("beats", [0]) if b < B.nb]

def fig_strum(B, k, cfg, O, res, cx, st, R):
    pat = cfg.get("pattern") or "D.DU.UDU"; step = float(cfg.get("step", 8)); slot = 4.0 / step
    s = [c for c in (pat if isinstance(pat, str) else pat[k % len(pat)]) if c not in " |"]; hits = []
    for j in range(steps_in(B, step)):
        c = s[j % len(s)]
        if c in "DUduXx": hits.append((j * slot, c))
        elif c not in ".~-_": sys.exit(f"music: strum character {c!r}: use D U d u X x . (x = muted chuck)")
    nstr = int(cfg.get("strings", 4)); spread = float(cfg.get("spread", 0.012)) / cx.beat
    V = {"X": 1.0, "D": 0.8, "d": 0.55, "U": 0.6, "u": 0.4, "x": 0.5}; out = []
    for h, (pos, c) in enumerate(hits):
        end = hits[h + 1][0] if h + 1 < len(hits) else B.nb
        v = voicing(chord_at(B, pos), O, {**cfg, "voicing": cfg.get("voicing", "guitar" if nstr >= 6 else "close"), "notes": nstr})
        up = c in "Uu"; order = v[::-1][:4] if up else v
        for i, m in enumerate(order):
            p = pos + i * spread * (0.8 if up else 1.0)
            out.append([p, max(0.05, end - p + 0.05), [m], V[c] * (1 - 0.05 * i), "", {"mute": True} if c == "x" else {}])
    return out

def fig_walking(B, k, cfg, O, res, cx, st, R):
    rng = R(5, B.i); lo, hi = 12 * (O + 1) - 8, 12 * (O + 1) + 16; sc = set(cx.scale(cfg.get("scale")))
    near = lambda pc, x: min((m for m in range(lo, hi + 1) if m % 12 == pc), key=lambda m: (abs(m - x), m))
    ch0 = chord_at(B, 0); line = [near(ch0.pc, st.get("prev", 12 * (O + 1) + ch0.pc))]
    nxt = cx.grid[B.i + 1].chords[0][1] if B.i + 1 < len(cx.grid) else B.chords[0][1]; target = near(nxt.pc, line[0])
    for q in range(1, B.nb):
        cur = line[-1]
        if q == B.nb - 1:   # approach the next root: a half step from the side we come from (sometimes the other side)
            side = -1 if cur <= target else 1
            c = target + (side if rng.random() < 0.75 else -side)
            line.append(c if c != cur and lo <= c <= hi else target - side)
        else:
            chq = chord_at(B, q); tones = {(chq.pc + i) % 12 for i in chq.iv}; want = cur + (target - cur) / (B.nb - q)
            cands = sorted((m for m in range(cur - 7, cur + 8) if lo <= m <= hi and m != cur and (m % 12 in tones or m in sc)),
                           key=lambda m: abs(m - want) - (1.5 if m % 12 in tones else 0))
            line.append(cands[min(len(cands) - 1, int(rng.integers(2)))] if cands else cur)
    st["prev"] = line[-1]; leg = float(cfg.get("legato", 0.92))
    ev = [[float(q), leg, [float(line[q])], 0.9 if q == 0 else 0.78, "", {}] for q in range(B.nb)]
    for q in range(1, B.nb):
        if rng.random() < float(cfg.get("ghost", 0)): ev.append([q - 1 / 3, 0.3, [float(line[q - 1])], 0.35, "", {}])
    return ev

def fig_oompah(B, k, cfg, O, res, cx, st, R, waltz=False):
    role = cfg.get("role", "both"); out = []
    for q in range(B.nb):
        ch = chord_at(B, q); bass = q == 0 if waltz else q % 2 == 0
        if bass and role != "chord":
            r = 12 * O + ch.pc; alt = (k % 2 == 1) if waltz else (q // 2) % 2 == 1
            out.append([float(q), float(cfg.get("bass_len", 0.9)), [float(r + (ch.iv[2] if len(ch.iv) > 2 else 7) - 12 if alt else r)],
                        0.9 if q == 0 else 0.8, "", {}])
        elif not bass and role != "bass":
            out.append([float(q), float(cfg.get("len", 0.8 if waltz else 0.45)), voicing(ch, O, cfg), 0.62 if q == 1 else 0.55, "", {}])
    return out

def fig_arp(kind):
    def f(B, k, cfg, O, res, cx, st, R):
        step = float(cfg.get("rate", 8 if kind == "alberti" else 16)); slot = 4.0 / step; span = int(cfg.get("span", 1))
        if cfg.get("reset", "bar") == "bar": st["i"] = 0
        out = []
        for j in range(steps_in(B, step)):
            pos = j * slot; ch = chord_at(B, pos); root = 12 * (O + 1) + ch.pc
            tones = sorted({root + i + 12 * o for o in range(span) for i in ch.iv} | {root + 12 * span})
            if kind == "alberti": v = [root + i for i in ch.iv[:3]]; seq_ = [v[0], v[-1], v[min(1, len(v) - 1)], v[-1]]
            elif kind == "arp-up": seq_ = tones
            elif kind == "arp-down": seq_ = tones[::-1]
            else: seq_ = tones + tones[-2:0:-1]
            i = st.get("i", 0); st["i"] = i + 1
            out.append([pos, _cut(pos, slot, B) * float(cfg.get("legato", 0.95)), [float(seq_[i % len(seq_)])], 0.85 if abs(pos - round(pos)) < 1e-9 else 0.7, "", {}])
        return out
    return f

def fig_ostinato(B, k, cfg, O, res, cx, st, R):
    cell = cfg.get("cell") or ["c0", "c2", "c1", "c2"]; step = float(cfg.get("rate", 8)); slot = 4.0 / step
    if cfg.get("reset") == "bar": st["i"] = 0
    out = []
    for j in range(steps_in(B, step)):
        i = st.get("i", 0); st["i"] = i + 1; tok = cell[i % len(cell)]; pos = j * slot
        p = [m for m in (res(x, pos) for x in (tok if isinstance(tok, list) else [tok])) if m is not None]
        if p: out.append([pos, _cut(pos, slot, B) * float(cfg.get("legato", 0.9)), p, 0.95 if i % len(cell) == 0 else 0.75, "", {}])
    return out

def fig_tremolo(B, k, cfg, O, res, cx, st, R):
    toks = cfg.get("pitch") or ["c0"]; toks = toks if isinstance(toks, list) else [toks]; d = B.nb / len(toks)
    return [[j * d, d, [m], 0.8, "", {}] for j, t in enumerate(toks) for m in [res(t, j * d)] if m is not None]

def fig_roots(B, k, cfg, O, res, cx, st, R):
    step = float(cfg.get("rate", 8)); slot = 4.0 / step; out = []
    for j in range(steps_in(B, step)):
        pos = j * slot; m = 12 * (O + 1) + chord_at(B, pos).pc + (12 if cfg.get("octaves") and j % 2 else 0)
        out.append([pos, _cut(pos, slot, B) * float(cfg.get("legato", 0.8)), [float(m)], 0.9 if abs(pos - round(pos)) < 1e-9 else 0.7, "", {}])
    return out

def fig_melody(B, k, cfg, O, res, cx, st, R):
    rng = R(6, B.i); sc = cx.scale(cfg.get("scale")); pat = cfg.get("pattern") or {"3": "x..x.xx..x..", "*": "x..x..x.x.x.x..."}
    raw = grid_events(pat, B, k, {**cfg, "pitch": None}, False, res, st, cx, O)
    ci = bisect.bisect_right(sc, res("c2", 0)) - 1; i = st.get("mi", ci); out = []
    for h, (pos, dur, _, vel, art, opts) in enumerate(raw):
        if abs(pos - round(pos)) < 1e-9:   # on a beat: the nearest chord tone
            ch = chord_at(B, pos); tones = {(ch.pc + x) % 12 for x in ch.iv}
            c = [j for j in range(i - 3, i + 4) if 0 <= j < len(sc) and sc[j] % 12 in tones]
            if c: i = min(c, key=lambda j: (abs(j - i), j))
        else: i += int(rng.choice([-2, -1, -1, 1, 1, 2]))
        i = int(np.clip(i, ci - 6, ci + 6)); end = raw[h + 1][0] if h + 1 < len(raw) else min(B.nb, pos + 2)
        out.append([pos, (end - pos) * 0.95, [float(sc[i])], vel, art, opts])
    st["mi"] = i
    return out

def swing_grid(cfg, fig, pat):
    """The step grid a part plays on (steps per whole note), or None when its notes can sit anywhere (note lists, stabs on beats …)."""
    if fig in ("arp-up", "arp-down", "arp-updown"): return float(cfg.get("rate", 16))
    if fig in ("alberti", "ostinato", "roots"): return float(cfg.get("rate", 8))
    if fig == "strum": return float(cfg.get("step", 8))
    if fig == "melody" or ((fig == "stab" or not fig) and _is_grid(pat)): return float(cfg.get("step", 16))
    return None

def _whole(x): return abs(x - round(x)) < 1e-9

FIGURES = {"sustain": fig_sustain, "stab": fig_stab, "strum": fig_strum, "walking": fig_walking, "oompah": fig_oompah,
           "waltz": lambda *a: fig_oompah(*a, waltz=True), "alberti": fig_arp("alberti"), "arp-up": fig_arp("arp-up"),
           "arp-down": fig_arp("arp-down"), "arp-updown": fig_arp("arp-updown"), "ostinato": fig_ostinato,
           "tremolo": fig_tremolo, "roots": fig_roots, "melody": fig_melody}

def part_events(part, spec, pbars, cx, R, label=None, cuts=(), stats=None):
    """Every note of a part: [t (s), dur (s), [MIDI…] or None, vel, art, opts, bar, level, early], sorted by time. level is
    the section's gain_db relative to the part's, applied after the voice renders (so it never drives a saturating voice);
    early is the section's onset_ms in seconds (t is already that much early; the beat map adds it back).
    cuts: the section stops this part does not survive, (start s, end s, tail s or None for a hold, section index). On
    the grid, before humanize: a stopped section's notes inside its stop are dropped (stats["stopped"] counts them), and a
    note that starts before a stop ends by its tail and carries "_cut" for render_voice."""
    evs, st, label = [], {}, label or part.get("id") or part["inst"]
    pitched = spec.kind != "drum" or spec.defaults.get("pitched") or "pitch" in part
    expanded, by_sec, run = {}, part.get("index", cx.index) == "section", 0   # motif calls unfolded once per pattern
    placed = {}   # id of a note list → (the list, the indices of its notes that landed in a bar)
    for k, B in enumerate(pbars):
        bs = part.get("by_section", {}).get(B.sec, {}); cfg = {**part, **bs}
        O = int(cfg.get("octave", spec.octave)); sc = cx.scale(cfg.get("scale"))
        res = lambda tok, pos, B=B, O=O, sc=sc: resolve(tok, chord_at(B, pos), O, cx.key_pc, sc)
        fig, pat = cfg.get("figure"), cfg.get("pattern")
        if mt.has_calls(pat):
            if id(pat) not in expanded: expanded[id(pat)] = mt.expand_pattern(pat, cx.motifs, f"part {label}")
            pat = expanded[id(pat)]
        bar_pat = pat.get(str(B.nb), pat.get("*")) if isinstance(pat, dict) else pat   # a dict picks by beats in the bar
        if by_sec:   # lists and loop windows count from the start of this section, not from the part's first bar
            if k == 0 or pbars[k - 1].si != B.si: run = k
            kk, lbars = k - run, [b_ for b_ in pbars[run:] if b_.si == B.si]
        else: kk, lbars = k, pbars
        if fig:
            if fig not in FIGURES: sys.exit(f"music: figure {fig!r}: use {' '.join(FIGURES)}")
            raw = FIGURES[fig](B, kk, cfg, O, res, cx, st, R)
        elif isinstance(pat, dict) and _is_notes(bar_pat):   # one bar
            raw = note_list(bar_pat, B, 0, {**cfg, "loop": 1}, [B], pitched, res, O, cx, placed.setdefault(id(bar_pat), (bar_pat, set()))[1])
        elif _is_notes(pat): raw = note_list(pat, B, kk, cfg, lbars, pitched, res, O, cx, placed.setdefault(id(pat), (pat, set()))[1])
        elif pat is not None: raw = grid_events(pat, B, kk, cfg, pitched, res, st, cx, O)
        else: sys.exit(f"music: part {label} needs a \"pattern\" or a \"figure\"")
        sw = swing_amount(cfg.get("swing", B.swing if B.swing is not None else cx.swing)); u = 0.25 if int(cfg.get("swing_unit", cx.swing_unit)) == 16 else 0.5
        gs = swing_grid(cfg, fig, bar_pat)
        if sw and gs and not (_whole(u * gs / 4) or _whole(4 / (gs * u))): sw = 0.0   # 8th triplets under 8th swing stay straight
        g = float(cfg.get("vel", 1.0))   # velocity: dynamics and timbre
        lv = 10 ** ((float(cfg.get("gain_db", 0)) - float(part.get("gain_db", 0))) / 20)   # this section's level, applied after the voice
        early = float(cfg.get("onset_ms", 0)) / 1000   # a slow-speaking voice starts early; hits keep the grid time
        dt = float(cfg.get("detune", 0)) / 100          # cents: a detuned double of another part
        trem = cfg.get("tremolo", True if fig == "tremolo" else None)
        rate = float(spec.defaults.get("tremolo_rate", 12) if trem is True else (trem or 0)); tmin = float(cfg.get("tremolo_min", 0)) * cx.beat
        ramp = bs.get("vel_ramp")   # [from, to]: velocity across this section, by each note's place in it
        for pos, dur, p, vel, art, opts in raw:
            t = B.tb + warp(pos, sw, u) * cx.beat; d = max(B.tb + warp(pos + dur, sw, u) * cx.beat - t, 0.005); t -= early
            if pos < 0 and t + early < -1e-9:   # a pickup before the first bar has nowhere to sound
                print(f"music: warning: part {label}: the pickup at beat {pos:g} before bar {B.i + 1} falls before the score starts "
                      'and is dropped (for an upbeat bar: "meters": {"1": 1})', file=sys.stderr); continue
            o = {**bs.get("params", {}), **opts}
            rf = float(ramp[0]) + (float(ramp[1]) - float(ramp[0])) * min(max((B.sec_off + pos) / B.sec_beats, 0.0), 1.0) if ramp else 1.0
            if ramp: vel = vel * rf
            if "to" in o: o = {**o, "to": float(o["to"]) * g * rf}   # a hairpin's target scales like the note's velocity
            if p and dt: p = [m + dt for m in p]
            if p and not all(0 <= m <= 127 for m in p):
                sys.exit(f"music: part {label}: pitch {next(m for m in p if not 0 <= m <= 127):g} in bar {B.i + 1} is outside MIDI 0–127; "
                         "check its \"octave\" and the ' , marks")
            if rate and d >= max(tmin, 1.5 / rate):   # tremolo: re-strike every 1/rate s, 4-finger accents, a gentle swell
                n = int(d * rate + 0.5); hp = o.pop("to", None)   # a hairpin moves the strikes from vel to "to"
                v0 = [vel * g if hp is None else vel * g + (hp - vel * g) * j / max(n - 1, 1) for j in range(n)]
                evs += [[t + j / rate, 1.2 / rate, p, v0[j] * (1.0, 0.8, 0.9, 0.75)[j % 4] * (0.85 + 0.15 * math.sin(math.pi * (j + 0.5) / n)),
                         art, {**o, "ring": False}, B, lv, early] for j in range(n)]
            else: evs.append([t, d, p, vel * g, art, o, B, lv, early])
    for pat_, seen in placed.values():
        miss = [j for j in range(len(pat_)) if j not in seen]
        if miss:
            print(f"music: warning: part {label}: {len(miss)} of the {len(pat_)} notes in a note list never play (the first at beat "
                  f"{float(pat_[miss[0]][0]):g}): they fall outside every bar of its loop window; check \"loop\" and the sections", file=sys.stderr)
    keep = None
    if cuts:   # section stops, judged on the grid (before humanize moves anything)
        keep = []
        for e in evs:
            g = e[0] + e[8]
            if any(a <= g < b and e[6].si == si for a, b, _, si in cuts): keep.append(False); continue   # a pickup into the next section stays
            c = min(((a, tl) for a, _, tl, _ in cuts if tl is not None and a > g), default=None)
            if c is not None:   # it starts before a stop: it sounds at most until the stop's tail has faded
                if e[0] + e[1] > c[0] + c[1]: e[1] = max(c[0] + c[1] - e[0], 0.005)
                e[5] = {**e[5], "_cut": [c[0], c[1]]}
            keep.append(True)
        if stats is not None: stats["stopped"] = keep.count(False)
    h = float(part.get("humanize", cx.humanize))
    if h:
        rh = R(3)
        for e in evs:
            e[0] = max(0.0, e[0] + float(np.clip(rh.normal() * 0.008 * h, -0.02 * h, 0.02 * h)))
            f = float(np.clip(1 + rh.normal() * 0.1 * h, 0.7, 1.3)); e[3] *= f
            if "to" in e[5]: e[5] = {**e[5], "to": e[5]["to"] * f}
    if keep is not None: evs = [e for e, k in zip(evs, keep) if k]
    evs.sort(key=lambda e: e[0])
    return evs

MONO_NOTE = ("glide", "scoop", "slide", "bend", "vibrato", "retrigger", "to")   # knobs read per note inside a phrase

def part_ramps(part, pbars, cx):
    """[start s, end s, from dB, to dB, section index] for each section this part plays with a "cresc" / "dim", in order."""
    bs = part.get("by_section", {}); out = []
    for B in pbars:
        rd = bs.get(B.sec, {}).get("cresc", bs.get(B.sec, {}).get("dim"))
        if rd is not None and B.b == 0: out.append([B.tb, B.tb + B.sec_beats * cx.beat, float(rd[0]), float(rd[1]), B.si])
    return out

def ramp_gain(rp, t, n):
    """One cresc / dim as gains for n samples from t: its line inside the section (its start value before it), its end
    value after it."""
    s0, s1, d0, d1 = rp[:4]; u = np.clip((t + np.arange(n) / SR - s0) / max(s1 - s0, 1e-9), 0.0, 1.0)
    return 10 ** ((d0 + (d1 - d0) * u) / 20)

def ramp_env(ramps, t, n, si, smooth=True):
    """The gains a sound of n samples starting at t, from a note of section si, takes from its part's cresc / dim
    sections, or None when none touches it. The note's own section decides by section, not by time, so a note that
    starts early (onset_ms, humanize) still gets its own section's line from its first sample, and an earlier
    section's line never reaches it. A held note that rings into a later section follows that section's line from
    where it starts. After a section, whatever still rings keeps the end level, so a tail never jumps back up."""
    g = None
    for rp in ramps:
        if rp[4] < si: continue   # an earlier section's line: over before this note's section began
        if rp[4] == si: i0 = 0   # its own section, from its first sample (before the section: the start value)
        elif rp[0] >= t + n / SR: continue   # a later section this sound never reaches
        else: i0 = max(0, int(round((rp[0] - t) * SR)))
        if g is None: g = np.ones(n)
        g[i0:] = ramp_gain(rp, t + i0 / SR, n - i0)
        if i0 and smooth: k = np.exp(-1 / (0.01 * SR)); g = lfilter([1 - k], [1, -k], g, zi=[k * g[0]])[0]   # the step into the section glides
    return g

def render_mono(spec, P, notes, R, place, vi, ramps=()):
    """Monophonic phrases: notes closer than 40 ms join (legato: glide, re-bow dip, vibrato carries on). "retrigger" (a
    param, a section param or a note's knob) gives every note its own attack instead. A note whose section params differ
    (by_section) starts a new phrase that uses them; a section's gain_db is applied after the voice, so it never drives
    the voice's own saturation (sub808)."""
    key = lambda o: json.dumps({k: v for k, v in o.items() if k not in MONO_NOTE}, sort_keys=True, default=str)
    phrases = []
    for nt in sorted(notes, key=lambda x: x[0]):
        if (phrases and nt[0] - (phrases[-1][-1][0] + phrases[-1][-1][1]) < 0.04 and nt[0] > phrases[-1][-1][0] + 0.01
                and not nt[4].get("retrigger", P.get("retrigger")) and key(nt[4]) == key(phrases[-1][-1][4])):
            p = phrases[-1]; p[-1] = (p[-1][0], nt[0] - p[-1][0], *p[-1][2:]); p.append(nt)
        else: phrases.append([nt])
    for ph in phrases:
        Q = {**P, **{k: v for k, v in ph[0][4].items() if k not in MONO_NOTE and k != "_cut"}}   # the part's params, then the section's
        glide, att, rel = float(Q.get("glide", 0.06)), float(Q.get("attack", 0.05)), float(Q.get("release", 0.1))
        rea, vib = float(Q.get("rearticulate", 0.3)), Q.get("vib") or (0, 0, 0)
        scoop, sct = float(Q.get("scoop", 0)), float(Q.get("scoop_time", 0.06))
        rng = R(2, vi, ph[0][5]); t0 = ph[0][0]; end = ph[-1][0] + ph[-1][1] - t0; n = int((end + rel) * SR) + 1; t = ins.secs(n)
        s, lvl, vd, onsets = np.zeros(n), np.zeros(n), np.zeros(n), []
        rgs = []   # each note's share of the phrase under its part's cresc / dim sections (by the note's own section)
        for j, nt in enumerate(ph):
            a = int(round((nt[0] - t0) * SR)); b = int(round((ph[j + 1][0] - t0) * SR)) if j + 1 < len(ph) else n
            rgs.append(ramp_env(ramps, t0 + a / SR, b - a, nt[7], False) if ramps else None)
        gl = np.ones(n) if any(nt[6] != 1 for nt in ph) or any(r is not None for r in rgs) else None
        for j, (tn, dn, m, vel, o, idx, lv, _) in enumerate(ph):
            a = int(round((tn - t0) * SR)); b = int(round((ph[j + 1][0] - t0) * SR)) if j + 1 < len(ph) else n; tt = t[:b - a]
            s[a:b] = m; lvl[a:b] = vel
            if o.get("to") is not None:   # a hairpin: the level moves from vel to "to" across the note, then holds
                nn = min(b - a, max(1, int(round(dn * SR)))); lvl[a:a + nn] = np.linspace(vel, float(o["to"]), nn); lvl[a + nn:b] = float(o["to"])
            if gl is not None: gl[a:b] = lv if rgs[j] is None else lv * rgs[j]   # the section's level and any cresc / dim (smoothed below)
            gln = min(b - a, int(float(o.get("glide", glide)) * SR))
            if j and gln > 0:
                u = np.arange(gln) / gln; s[a:a + gln] = ph[j - 1][2] + (m - ph[j - 1][2]) * u * u * (3 - 2 * u)
            sc = float(o.get("scoop", scoop)) * (0.5 if j else 1.0)
            if sc: kk = min(b - a, int(5 * sct * SR)); s[a:a + kk] += sc * np.exp(-t[:kk] / sct)
            if o.get("slide"): u = np.clip(tt / 0.2, 0, 1); s[a:b] += float(o["slide"]) * (1 - u * u * (3 - 2 * u))
            if o.get("bend"): u = np.clip((tt - 0.12) / 0.2, 0, 1); s[a:b] += float(o["bend"]) * u * u * (3 - 2 * u)
            vd[a:b] = np.clip((tt - float(vib[2])) / 0.3, 0, 1) * float(o.get("vibrato", 1.0)); onsets.append((a, vel, j > 0))
        k1 = np.exp(-1 / (0.012 * SR)); env = lfilter([1 - k1], [1, -k1], lvl) * np.clip(t / max(att, 1e-3), 0, 1)
        for a, v, leg in onsets[1:]:
            w = int(0.05 * SR); lo = max(0, a - w // 2); hi = min(n, lo + w); env[lo:hi] *= 1 - rea * np.hanning(hi - lo + 2)[1:-1]
        env *= ins.release_after(n, end, rel)
        if float(vib[1]):
            ph_ = np.cumsum(float(vib[0]) * (1 + 0.05 * ins.wander(rng, n, 0.7))) / SR
            s = s + float(vib[1]) / 100 * vd * np.sin(ins.TAU * ph_ + rng.uniform(0, ins.TAU))
        x = spec.fn(ins.mtof(s), env, onsets, Q, rng) * spec.level
        if gl is not None: x = x * lfilter([1 - k1], [1, -k1], gl, zi=[k1 * gl[0]])[0]   # the level, after the voice, smoothed
        place(x, t0, ph[0][4].get("_cut"))

def render_voice(part, spec, evs, P, R, N, C, pbars, cuts=(), ramps=()):
    """One part → (mono stem, stereo stem or None). cuts: the section stops the part does not survive, as part_events
    takes them; notes carry their own ("_cut"), a texture pauses through each stop. ramps: part_ramps."""
    mono = np.zeros(N); st2 = [None]; cache = {}   # the stereo buffer only exists once a stereo voice lands in it
    def place(x, t, cut=None):
        i = int(round(t * SR))
        if i >= N: return
        if cut is not None:   # [stop s, tail s]: whatever still sounds at the stop fades out over the tail (a cosine), then silence
            k = int(round((cut[0] - t) * SR)); nt = max(1, int(round(cut[1] * SR)))
            if k + nt <= 0: return
            if x.shape[-1] > k:
                n_ = min(x.shape[-1], k + nt); j0 = max(k, 0); env = np.ones(n_)
                env[j0:] = 0.5 + 0.5 * np.cos(np.pi * (np.arange(j0, n_) - k) / nt); x = x[..., :n_] * env
        if i < 0: x = x[..., -i:]; i = 0
        j = min(N, i + x.shape[-1])
        if x.ndim == 1: mono[i:j] += x[:j - i]
        elif C == 2:
            if st2[0] is None: st2[0] = np.zeros((2, N))
            st2[0][:, i:j] += x[:, :j - i]
        else: mono[i:j] += x[:, :j - i].mean(0)
    if spec.kind == "texture":   # continuous over each run of consecutive bars, 0.1 s in, 0.4 s out
        runs = []
        for B in pbars:
            t1 = B.tb + B.nb * (60.0 / float(part["_bpm"]))
            if runs and runs[-1][2] == B.i - 1: runs[-1][1:3] = [t1, B.i]
            else: runs.append([B.tb, t1, B.i, None])
        for a, b, tl, _ in cuts:   # a stop pauses a texture: its run breaks at the stop and picks up where the stop ends
            cut = []
            for r0, r1, ri, c in runs:
                if r1 <= a or r0 >= b: cut.append([r0, r1, ri, c]); continue
                if r0 < a: cut.append([r0, a, ri, None if tl is None else [a, tl]])
                if r1 > b: cut.append([b, r1, ri, c])
            runs = cut
        bs, v0, g0 = part.get("by_section", {}), float(part.get("vel", 1.0)), float(part.get("gain_db", 0))
        lvl = lambda B: ((float(bs.get(B.sec, {}).get("vel", v0)) / v0 if v0 else 1.0)   # a section's vel and gain_db, relative to the part's
                         * 10 ** ((float(bs.get(B.sec, {}).get("gain_db", g0)) - g0) / 20))
        rdb = lambda B: bs.get(B.sec, {}).get("cresc", bs.get(B.sec, {}).get("dim"))   # a section's cresc / dim
        beat = 60.0 / float(part["_bpm"])
        for r, (a, b, _, cut) in enumerate(runs):
            n = int((b - a + 0.4) * SR); x = spec.fn(n, R(4, r), P) * spec.level * float(part.get("vel", 1.0))
            bars = [B for B in pbars if a - 1e-9 <= B.tb < b - 1e-9]
            if any(lvl(B) != 1 or rdb(B) is not None for B in bars):   # a level per section, 10 ms glides between them (textures have no notes to carry it)
                e = np.ones(n)
                for j, B in enumerate(bars):
                    i0 = int(round((B.tb - a) * SR)); i1 = int(round((bars[j + 1].tb - a) * SR)) if j + 1 < len(bars) else n
                    e[i0:i1] = lvl(B)
                    if rdb(B) is not None:
                        s0 = B.tb - B.sec_off * beat; e[i0:i1] *= ramp_gain([s0, s0 + B.sec_beats * beat, float(rdb(B)[0]), float(rdb(B)[1])], a + i0 / SR, i1 - i0)
                k = np.exp(-1 / (0.01 * SR)); x = x * lfilter([1 - k], [1, -k], e, zi=[k * e[0]])[0]
            place(ins.fade(x, 0.1, 0.4), a, cut)
    elif spec.kind == "mono":
        voices = {}
        for idx, e in enumerate(evs):
            for vi, m in enumerate(e[2] or []): voices.setdefault(vi, []).append((e[0], e[1], m, e[3], e[5], idx, e[7], e[6].si))
        for vi, notes in voices.items(): render_mono(spec, P, notes, R, place, vi, ramps)
    else:
        for idx, (t, dur, pitches, vel, art, opts, B, lv, _) in enumerate(evs):
            hp, cut = opts.get("to"), opts.get("_cut")   # a hairpin, a section stop
            if hp is not None or cut is not None: opts = {k: v for k, v in opts.items() if k not in ("to", "_cut")}
            vq = min(8, max(1, round(min(vel, 1.0) * 8))) / 8 if spec.vt else 1.0; ok = json.dumps(opts, sort_keys=True) if opts else ""
            for vi, m in enumerate(pitches if pitches else [None]):
                var = (idx + vi) % spec.rr; dq = round(dur, 2)
                if spec.kind == "drum":
                    f = None if m is None else float(ins.mtof(m)); key = (art, vq, var, dq, None if f is None else round(f, 2), ok)
                    if key not in cache: cache[key] = spec.fn(vq, art, dq, R(1, var, ord(art[:1] or " "), int(vq * 8)), {**P, **opts}, f) * spec.level
                else:
                    key = (round(m, 2), dq, vq, var, ok)
                    if key not in cache: cache[key] = spec.fn(m, dq, vq, R(1, int(round(m * 100)), var), {**P, **opts}) * spec.level
                rg = ramp_env(ramps, t, cache[key].shape[-1], B.si) if ramps else None   # the cresc / dim sections it sounds under
                if hp is None and rg is None: y = cache[key] * vel if lv == 1 else cache[key] * (vel * lv)
                else:   # the hairpin moves the level from vel to "to" over the note's length, then holds; a ramp rides on top
                    y = cache[key]; amp = np.full(y.shape[-1], vel * lv)
                    if hp is not None:
                        nn = max(1, int(round(dur * SR))); k = min(nn, y.shape[-1]); amp[k:] = float(hp) * lv
                        amp[:k] = np.linspace(vel * lv, float(hp) * lv, nn)[:k]
                    if rg is not None: amp *= rg
                    y = y * amp
                place(y, t, cut)
    return mono, st2[0]

def delay_fx(x, D, beat):
    d = int(float(D.get("beats", 0.75)) * beat * SR); fb, mix, lp_hz = float(D.get("fb", 0.35)), float(D.get("mix", 0.3)), float(D.get("lp", 3500))
    y, tap, N = x.copy(), x, x.shape[1]
    for r in range(1, 16):
        g = mix * fb ** (r - 1)
        if g < 0.003 or d * r >= N or d <= 0: break
        tap = ins.lpf(tap, lp_hz); sh = np.zeros_like(x); sh[:, d * r:] = tap[:, :N - d * r] * g
        if D.get("pingpong") and x.shape[0] == 2: sh[1 - r % 2] = 0; sh[r % 2] *= 1.4
        y += sh
    return y

def lofi_fx(x, L, rng):
    """Master lo-fi: wow/flutter (a slowly moving read head), low-pass, crackle and hiss relative to the mix peak."""
    L = L if isinstance(L, dict) else {}; N = x.shape[1]; pk = float(np.max(np.abs(x))) or 1.0; t = ins.secs(N)
    w = float(L.get("wow", 0.3))
    if w:
        d = (w * 0.002 * (0.7 * np.sin(ins.TAU * 0.5 * t) + 0.3 * ins.wander(rng, N, 1.0)) + w * 0.0001 * np.sin(ins.TAU * 7 * t)) * SR
        idx = np.arange(N) - d - w * 0.003 * SR; x = np.stack([np.interp(idx, np.arange(N), c) for c in x])
    x = ins.hpf(ins.lpf(x, float(L.get("lp", 6000))), 40)
    cr, hs = float(L.get("crackle", 0.3)), float(L.get("hiss", 0.2))
    if cr: v = ins.vinyl(N, rng, {}); x = x + (v[:x.shape[0]] if x.shape[0] == 2 else v.mean(0, keepdims=True)) * cr * 0.25 * pk
    if hs: x = x + ins.tape(N, rng, {})[:x.shape[0]] * hs * 0.01 * pk
    return x

def tape_fx(x, a):
    """Tape saturation 0–1: asymmetric soft clip (even harmonics), a softer top, DC removed."""
    a = 0.5 if a is True else float(a); pk = float(np.max(np.abs(x))) or 1.0; k, b = 1 + 3 * a, 0.15 * a
    y = (np.tanh(k * x / pk + b) - np.tanh(b)) / np.tanh(k) * pk
    return ins.hpf(ins.lpf(y, 16000 - 6000 * a), 20)

def dyn_db(part, cx, N):
    """A part's "dyn" {"bar:beat": dB, …} in dB per sample, or None: a line through the whole score, flat before the first
    point and after the last, like a fader ride on the stem (ringing notes follow it). 10 ms glides: a step never clicks."""
    pts = part.get("dyn")
    if not pts: return None
    xy = sorted((cx.at(k), float(v)) for k, v in pts.items()); db = np.interp(np.arange(N) / SR, [x for x, _ in xy], [y for _, y in xy])
    k = np.exp(-1 / (0.01 * SR)); return lfilter([1 - k], [1, -k], db, zi=[k * db[0]])[0]

def stop_at(stp, what):
    """A stop's place in its section: "at": "5:2" (or "5.2", "5"), or "bar" and "beat"; (bar, beat), from 1."""
    if "at" in stp: return bar_beat(stp["at"], f"{what} at")
    return int(_num(stp.get("bar", 1), f"{what} bar", 1)), _num(stp.get("beat", 1), f"{what} beat", 1)

def section_stops(score, cx):
    """Each section's "stop": (start s, end of the section s, parts kept, tail s, hold, section name, section index)."""
    out = []
    for si, s in enumerate(score["sections"]):
        stp = s.get("stop")
        if not stp: continue
        stp = stp if isinstance(stp, dict) else {}   # "stop": true stops everything at the section's first beat
        bars = [B for B in cx.grid if B.si == si]; bar, beat = stop_at(stp, f"section {s['name']!r} stop")
        t0 = bars[bar - 1].tb + (beat - 1) * cx.beat
        out.append((t0, bars[-1].tb + bars[-1].nb * cx.beat, set(stp.get("keep", [])), float(stp.get("tail", 0.15)), stp.get("hold") is True, s["name"], si))
    return out

def parts_bus(score, legacy, hits, stems=None, info_gain=None):
    """Render the parts, add them to the layers' mix (centred), run the spaces and master effects; returns ((n,) or (n, 2), checks).
    Two passes keep memory flat: first every part's notes (cheap; ducks and the beat map need all the onsets), then each part
    is rendered, mixed into the buses and dropped before the next one."""
    C = 2 if score.get("stereo") else 1; N = len(legacy); cx = Ctx(score); parts = score.get("parts") or []
    sp = score.get("space", "room"); sp = sp if isinstance(sp, dict) else {"type": sp}
    plan, onsets, part_hits, checks = [], {}, [], []
    stops = section_stops(score, cx)   # a section's stop: only the kept parts play on; the others stop sounding within its tail
    part_hits += [{"t": round(t0, 3), "what": f"stop:{name}"} for t0, *_, name, _ in stops]
    for i, part in enumerate(parts):
        inst = part["inst"]; spec = ins.INSTR[inst]; pid = part.get("id"); occ = sum(1 for p in parts[:i] if p.get("inst") == inst and "id" not in p)
        pk = (ins.crc(pid), 0) if pid else (ins.crc(inst), occ); label = pid or f"{inst}#{occ}"
        R = lambda *k, pk=pk: np.random.default_rng([cx.seed, 101, *pk, *k])
        names = part.get("sections", "all")
        if names != "all":
            names = [names] if isinstance(names, str) else names; unknown = set(names) - {B.sec for B in cx.grid}
            if unknown: sys.exit(f"music: part {label}: no section named {sorted(unknown)}")
        pbars = [B for B in cx.grid if names == "all" or B.sec in names]
        cuts = [(a, b, None if hold else max(tail, 0.005), si) for a, b, keep, tail, hold, _, si in stops if not ({label, inst, pid} & keep)]
        stat = {}   # cuts: the stops this part does not survive; the tail is at least 5 ms, so a stop never clicks
        try: evs = [] if spec.kind == "texture" else part_events(part, spec, pbars, cx, R, label, cuts, stat)
        except SystemExit as e:   # a bad pitch, grid or strum character, figure or scale: say which part
            msg = str(e)
            if msg.startswith("music: ") and f"part {label}" not in msg: sys.exit(f"music: part {label}: {msg[7:]}")
            raise
        silenced = bool(stat.get("stopped")) and not evs   # every note fell inside a stop: nothing to measure
        if cuts and spec.kind == "texture":   # likewise a texture whose every bar is inside a stop
            silenced = all(any(a <= B.tb + 1e-9 and B.tb + B.nb * cx.beat <= b + 1e-9 for a, b, _, _ in cuts) for B in pbars)
        if spec.kind != "texture" and not evs and not silenced:
            sys.exit(f'music: part {label} plays no notes: check its sections, pattern, figure and pitch ("quiet": true does not skip this)')
        plan.append((part, spec, label, R, pbars, evs, cuts, silenced))
        for key in {inst, pid} - {None}: onsets.setdefault(key, []).extend(e[0] for e in evs)
        if part.get("hit"):
            seen = set()
            for e in evs:
                if part["hit"] == "section" and e[6].si in seen: continue
                seen.add(e[6].si); part_hits.append({"t": round(e[0] + e[8], 3), "what": f"{label}:{e[6].sec}"})   # the section's onset_ms
    dry = np.zeros((C, N)); sends = {}
    for part, spec, label, R, pbars, evs, cuts, silenced in plan:
        P = {**spec.defaults, **part.get("params", {})}
        mono, st2 = render_voice({**part, "_bpm": score["bpm"]}, spec, evs, P, R, N, C, pbars, cuts, part_ramps(part, pbars, cx))
        pan = float(part.get("pan", 0)); stem = mono[None] if C == 1 else ins.pan2(mono, pan)
        if st2 is not None: stem = stem + ins.pan2(st2, pan)
        del mono, st2
        if part.get("hp"): stem = ins.hpf(stem, part["hp"])
        if part.get("lp"): stem = ins.lpf(stem, part["lp"])
        if part.get("drive"): m = float(np.max(np.abs(stem))) or 1.0; stem = ins.drive(stem / m, float(part["drive"])) * m
        if part.get("delay"): stem = delay_fx(stem, part["delay"], cx.beat)
        stem *= 10 ** (float(part.get("gain_db", 0)) / 20)
        db = dyn_db(part, cx, N)
        if db is not None: stem *= 10 ** (db / 20); del db
        if not np.isfinite(stem).all():   # a NaN compares false, so the level check below would pass it and the file would be silence
            sys.exit(f"music: part {label}: its voice produced samples that are not finite numbers (NaN or inf); check its params and note knobs")
        if not part.get("quiet") and not silenced:   # where it plays loudest: the top 50 ms of power averaged over the channels (a hard pan reads
            # as loud as the centre), or the peak of that power − 18 dB (crackle, ticks)
            a = int((evs[0][0] if evs else pbars[0].tb) * SR); b = int(((evs[-1][0] + evs[-1][1]) if evs else pbars[-1].tb + pbars[-1].nb * cx.beat) * SR) + SR // 2
            w = int(0.05 * SR); seg = stem[:, max(0, a):min(N, b)]; pw = seg[0] ** 2
            for c in range(1, C): pw += seg[c] ** 2
            pw /= C; k = max(1, len(pw) // w)
            checks.append((label, max(float(np.sqrt(pw[:k * w].reshape(k, -1).mean(1).max())), float(np.sqrt(pw.max())) / 8) if len(pw) >= w else 0.0))
        dk = part.get("duck")
        if dk:
            dk = dk if isinstance(dk, dict) else {"by": dk}; depth, rel = float(dk.get("depth", 0.5)), int(float(dk.get("release", 0.2)) * SR)
            env = np.ones(N)
            for t in onsets.get(dk["by"], []):
                a = int(t * SR); b = min(N, a + rel)
                if a < N: env[a:b] = np.minimum(env[a:b], 1 - depth + depth * np.linspace(0, 1, b - a) ** 0.7)
            stem *= env
        if stems is not None: stems[label] = stem.copy()
        dry += stem; s = float(part.get("send", 0)); name = part.get("space", sp["type"])
        if s and name != "dry":
            if name in sends: sends[name] += stem * s
            else: sends[name] = 0 + stem * s
        del stem
    mix = dry; mix += legacy   # the layers' mix, centred on every channel
    for name in list(sends):
        if name not in ins.SPACES: sys.exit(f"music: space {name!r}: use dry {' '.join(ins.SPACES)}")
        g = 10 ** (float(sp.get("return_db", 0)) / 20) if name == sp["type"] else 1.0
        bus = ins.lpf(ins.hpf(sends.pop(name), 150), 9000)
        for c in range(C):
            mix[c] += fftconvolve(bus[c], ins.space_ir(name, c, sp.get("rt60") if name == sp["type"] else None))[:N] * g
        del bus
    if score.get("lofi"): mix = lofi_fx(mix, score["lofi"], np.random.default_rng([cx.seed, 102]))
    if score.get("tape"): mix = tape_fx(mix, score["tape"])
    if parts:
        g = float(score.get("drive", 1.0)) / (float(np.max(np.abs(mix))) or 1.0); mix *= g; checks = [(k, v * g) for k, v in checks]
        if info_gain is not None: info_gain[0] = g
    if part_hits: hits.extend(part_hits); hits.sort(key=lambda h: h["t"])
    return (mix[0] if C == 1 else np.ascontiguousarray(mix.T)), checks

# the old voices, playable as parts too
ins.INSTR.update({
    "saw_pad": ins.Inst("note", lambda m, d, v, rng, P: pad([m], d + 0.4, v), 4, 1.0),
    "saw_lead": ins.Inst("note", lambda m, d, v, rng, P: lead(mtof(m), d, v), 5, 1.0),
    "saw_pluck": ins.Inst("note", lambda m, d, v, rng, P: pluck(mtof(m), d, v), 5, 1.0),
    "synth_bass": ins.Inst("note", lambda m, d, v, rng, P: bass(mtof(m), d), 2, 1.0),
    "bell": ins.Inst("note", lambda m, d, v, rng, P: bell(mtof(m), rng), 5, 1.0),
    "zheng": ins.Inst("note", lambda m, d, v, rng, P: zheng(mtof(m), max(d, 1.8), v, rng), 4, 1.0),
    "dizi": ins.Inst("note", lambda m, d, v, rng, P: dizi(mtof(m), d, v, rng), 5, 1.0),
    "taiko": ins.Inst("drum", lambda v, a, d, rng, P, f=None: taiko(rng, a != "o"), 2, 1.0),
    "edm_kick": ins.Inst("drum", lambda v, a, d, rng, P, f=None: ins.fade(kick(), 0, 0.03), 2, 1.0),   # the layer's kick stops at 0.45 s
    "edm_clap": ins.Inst("drum", lambda v, a, d, rng, P, f=None: clap(rng), 4, 1.0),
    "edm_hat": ins.Inst("drum", lambda v, a, d, rng, P, f=None: hat(rng, a == "o"), 4, 1.0),
})
for _k, _v in {"saw_pad": 0.687, "saw_lead": 2.366, "saw_pluck": 2.25, "synth_bass": 1.712, "bell": 0.941, "zheng": 0.589,
               "dizi": 0.997, "taiko": 0.618, "edm_kick": 0.532, "edm_clap": 0.675, "edm_hat": 1.176}.items():
    ins.INSTR[_k].level = _v   # same loudness rule as instruments.LEVEL
for _k, _v in {"saw_pad": "the layers' detuned saw pad", "saw_lead": "the layers' saw + square lead", "saw_pluck": "the layers' arp pluck",
               "synth_bass": "the layers' sine + saw bass", "bell": "the layers' 编钟-like bell", "zheng": "the layers' Karplus–Strong 古筝",
               "dizi": "the layers' breathy 笛子", "taiko": "the layers' taiko (o = the small drum)", "edm_kick": "the layers' EDM kick",
               "edm_clap": "the layers' clap", "edm_hat": "the layers' hat (o = open)"}.items():
    ins.INSTR[_k].about = _v

# ---------- starter scores for parts (--example <name>) ----------
EXAMPLES = {
    "jazz": ("cool jazz: walking upright, brushes and ride, muted brass stabs, swung 8ths", {
        "bpm": 138, "key": "F", "mode": "minor", "seed": 3, "stereo": True, "space": "room", "swing": 0.3,
        "sections": [{"name": "head", "bars": 4, "chords": ["i7", "iv7", "iiø7 V7", "i7"]},
                     {"name": "shout", "bars": 4, "chords": ["i7", "bVI7", "iiø7 V7", "i7"]}],
        "parts": [{"inst": "upright", "figure": "walking", "ghost": 0.2, "pan": -0.15},
                  {"inst": "ride", "pattern": "X.xxX.xx", "step": 8, "gain_db": -9, "pan": 0.35, "send": 0.1},
                  {"inst": "brush", "pattern": "o~x~o~x~", "step": 8, "gain_db": -7, "pan": -0.2},
                  {"inst": "hihat", "pattern": ".x.x", "step": 4, "gain_db": -14, "pan": 0.3},
                  {"inst": "piano", "figure": "stab", "beats": [1.5, 3.5], "len": 0.35, "sections": ["head"], "gain_db": -8, "pan": 0.2},
                  {"inst": "brass", "figure": "stab", "beats": [0, 1.5, 3], "sections": ["shout"], "params": {"stab": True, "mute": True},
                   "gain_db": -3, "send": 0.2},
                  {"inst": "bongo", "pattern": "......x.....x.xo", "sections": ["shout"], "gain_db": -12, "pan": 0.5}]}),
    "waltz": ("3/4 string waltz: pizzicato bass on 1, strings on 2 and 3, a violin line with portamento", {
        "bpm": 150, "key": "D", "mode": "minor", "seed": 8, "beats_per_bar": 3, "stereo": True, "space": "hall",
        "sections": [{"name": "a", "bars": 4, "chords": ["i", "iv", "V7", "i"]}, {"name": "b", "bars": 4, "chords": ["VI", "iv", "V7", "i"]}],
        "parts": [{"inst": "pizzicato", "figure": "waltz", "role": "bass", "octave": 3, "send": 0.2},
                  {"inst": "strings", "figure": "waltz", "role": "chord", "params": {"marcato": True}, "gain_db": -8, "send": 0.3},
                  {"inst": "violin", "loop": 4, "gain_db": -2, "send": 0.35, "pan": 0.15,
                   "pattern": [[0, 2, "c2"], [2, 1, "s3"], [3, 3, "c2"], [6, 1.5, "s2"], [7.5, 1.5, "s1"], [9, 3, "c0"]]},
                  {"inst": "rain", "gain_db": -4}]}),
    "chip": ("SNES-style JRPG: pulse lead with echo, 12.5 % arpeggio, 4-bit triangle bass, noise drums", {
        "bpm": 150, "key": "C", "mode": "major", "seed": 4, "stereo": True, "space": "dry",
        "sections": [{"name": "town", "bars": 4, "chords": ["I", "vi", "IV", "V"]}],
        "parts": [{"inst": "pulse", "figure": "melody", "params": {"duty": 0.25, "vib": 15}, "pan": 0.1,
                   "delay": {"beats": 0.75, "fb": 0.35, "mix": 0.35, "pingpong": True}},
                  {"inst": "pulse", "id": "arp", "figure": "arp-up", "octave": 4, "params": {"duty": 0.125, "sus": 0.3}, "gain_db": -10, "pan": -0.3},
                  {"inst": "triangle", "figure": "roots", "octaves": True, "octave": 2, "gain_db": -3},
                  {"inst": "chipkick", "pattern": "x.......x.x.....", "gain_db": -2},
                  {"inst": "noise", "pattern": "....x.......x...", "gain_db": -6},
                  {"inst": "noise", "id": "hat", "pattern": "o.o.o.o.o.o.o.o.", "gain_db": -14}]}),
    "lofi": ("lo-fi hip-hop: Rhodes maj7 chords, dusty swung drums, soft upright, crackle and wow", {
        "bpm": 82, "key": "F", "mode": "major", "seed": 5, "stereo": True, "space": "room", "swing": 0.2, "swing_unit": 16,
        "humanize": 0.5, "lofi": {"crackle": 0.4, "wow": 0.5, "lp": 5000}, "tape": 0.4,
        "sections": [{"name": "loop", "bars": 4, "chords": ["IVmaj7", "iii7", "ii9", "Imaj7"]}],
        "parts": [{"inst": "epiano", "figure": "stab", "beats": [0, 1.75], "len": 1.5, "voicing": "spread", "params": {"trem": 0.25}, "send": 0.25},
                  {"inst": "upright", "pattern": [[0, 1.5, "c0"], [2.5, 0.75, "c2,"], [3.5, 0.5, "c0"]], "gain_db": -2},
                  {"inst": "bb_kick", "pattern": "x.........x.x...", "gain_db": -1},
                  {"inst": "bb_snare", "pattern": "....x.......x..g", "gain_db": -4},
                  {"inst": "hihat", "pattern": "x.gxx.gxx.gxx.gx", "gain_db": -4, "pan": 0.25},
                  {"inst": "vinyl", "gain_db": 0}]}),
    "guqin": ("ink-wash 古琴 + 箫: slides, 吟 vibrato, a harmonic, 羽 pentatonic, lots of space", {
        "bpm": 60, "key": "D", "mode": "minor", "seed": 9, "stereo": True, "space": "hall",
        "sections": [{"name": "mist", "bars": 2, "chords": ["i", "VII"]}, {"name": "peak", "bars": 2, "chords": ["iv", "i"]}],
        "parts": [{"inst": "guqin", "scale": "yu", "loop": 2, "send": 0.35, "pattern": [
                      [0, 1.5, "s0", 0.8], [1.5, 0.5, "s2", 0.6, {"slide": -2}], [2, 2, "s4", 0.7, {"yin": True}],
                      [4, 2, "s3'", 0.6, {"harm": True}], [6, 2, "s1", 0.7, {"bend": 2}]]},
                  {"inst": "xiao", "sections": ["peak"], "scale": "yu", "loop": 2, "gain_db": -5, "send": 0.5,
                   "pattern": [[0, 3, "s4"], [3, 1, "s3"], [4, 4, "s2"]]},
                  {"inst": "wind", "gain_db": -8}]}),
    "trap": ("phonk / trap: gliding distorted 808, cowbell riff, rolling hats, half-time snare", {
        "bpm": 140, "key": "C", "mode": "minor", "seed": 6, "stereo": True, "space": "dry",
        "sections": [{"name": "drop", "bars": 4, "chords": ["i", "i", "VI", "VII"]}],
        "parts": [{"inst": "sub808", "pattern": [[0, 0.75, "c0"], [1.5, 0.5, "c0"], [2, 1.5, "c0'"], [3.5, 0.5, "s-1"]], "params": {"drive": 3}},
                  {"inst": "cowbell", "pattern": "x..x..x...x..x..", "pitch": ["c0", "c0", "s2", "c0", "s-1"], "octave": 5, "gain_db": -9,
                   "drive": 2, "pan": 0.2},
                  {"inst": "trap_hat", "pattern": ["x.x.x.x.x.x.x.x.", "x.x.x.x.x.rrx.x.", "x.x.x.x.x.x.x.x.", "x.x.RRRRx.x.rrrr"], "gain_db": -9, "pan": -0.2},
                  {"inst": "trap_snare", "pattern": "........x.......", "gain_db": -3},
                  {"inst": "clap", "pattern": "........x.......", "gain_db": -8, "send": 0.1},
                  {"inst": "edm_kick", "pattern": "x......x..x.....", "gain_db": -3}]}),
}

def compact(score):
    """JSON with one section / part per line, so a starter score stays short and readable."""
    keys = list(score); lines = ["{"]
    for i, k in enumerate(keys):
        end = "," if i < len(keys) - 1 else ""; v = score[k]
        if k in ("sections", "parts"):
            lines.append(f'  "{k}": [')
            lines += ["    " + json.dumps(x, ensure_ascii=False) + ("," if j < len(v) - 1 else "") for j, x in enumerate(v)]
            lines.append("  ]" + end)
        else: lines.append(f'  "{k}": {json.dumps(v, ensure_ascii=False)}{end}')
    return "\n".join(lines + ["}"])

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--example":
        name = sys.argv[2] if len(sys.argv) > 2 else ""
        if name == "list":
            print("  (none)  layers: EDM build and drop (pad arp hats bass kick clap lead)\n  zh      layers: 编钟 古筝 笛子 太鼓, D 羽")
            for k, (desc, _) in EXAMPLES.items(): print(f"  {k:<7} parts: {desc}")
            return
        if name in ("", "zh"): print(json.dumps(EXAMPLE_ZH if name == "zh" else EXAMPLE, indent=2)); return
        if name not in EXAMPLES: sys.exit(f"music: no example {name!r} (--example list names them)")
        print(compact(EXAMPLES[name][1])); return
    if len(sys.argv) > 1 and sys.argv[1] == "--instruments":
        for name, spec in ins.INSTR.items():
            doc = spec.about
            knobs = ", ".join(f"{k}={v}" for k, v in spec.defaults.items() if not k.startswith("_"))
            print(f"  {name:<12} {spec.kind:<7} {'octave ' + str(spec.octave) if spec.kind in ('note', 'mono') else '':<9} {doc}"
                  + (f"  [defaults: {knobs}]" if knobs else ""))
        print("  figures: " + " ".join(FIGURES)); return
    if len(sys.argv) < 3: sys.exit("usage: music.py <score.json> <out.wav> | --example [name|list] | --instruments")
    score = json.load(open(sys.argv[1])); out = sys.argv[2]
    mix, beatmap = render(score)
    with wave.open(out, "wb") as w:
        w.setnchannels(1 if mix.ndim == 1 else 2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
    bm = out.rsplit(".", 1)[0] + ".beats.json"
    json.dump(beatmap, open(bm, "w"), indent=2)
    print(f"{out} ({beatmap['duration']}s, {score['bpm']} bpm, {len(beatmap['sections'])} sections{', stereo' if mix.ndim == 2 else ''}) · beat map {bm}")

if __name__ == "__main__":
    main()
