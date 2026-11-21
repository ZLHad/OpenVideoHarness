"""Room tone: the quiet bed bin/vh mix lays under a voice that has no music, so its pauses are a room, not dead air.

A synthesized narration has nothing between its words: the joins are exact digital zero and its own pauses fall under
-60 dBFS, which the film's floor forbids (no digital silence in a film with sound). A recording made in a room never
has that: it carries the room's own sound under every pause. This is that sound, made the same way each time, in numpy
and scipy as the rest of the mixer's sound is (not by an ffmpeg filter, whose output can change from one ffmpeg build to
the next): white noise from a generator of its own (splitmix64 of the sample's number and one fixed seed per channel, in
integer arithmetic, so the noise is the same on every machine and with every numpy; the two sides differ), made pink by
Kellet's three-pole filter, high-passed at 60 Hz and low-passed at 5 kHz
(second-order Butterworth each: a soft room, no hiss on top, no rumble under), at a fixed RMS level. Its first and last
half second ramp between FOUND and that level (raised cosine), so neither end starts with a step and the film's last
samples are not digital silence either. It goes in after the mix's loudness gain, so its level in the film is the level
asked for; the integrated loudness does not move (it sits 40 dB and more under speech at -14 LUFS), the true peak may
rise by up to 0.1 dB (measured: -11.1 to -11.0 dBTP on a quiet voice, -1.57 to -1.56 against the limiter).

The level, and how it was found: on the 25 s demo film's voice-only mix (Qwen3-TTS, -14 LUFS), this bed at each level
from -74 to -56 dBFS RMS in 1 dB steps, and bin/vh qa's digital-silence scan (every channel under -60 dBFS for 20 ms or
more) counted, with the longest stretch any part of the checked span spends with every channel under -60 dBFS. Without a
bed: 22 runs, the longest 352 ms. At -74 to -69: 20 to 33 runs. At -68: 4 runs (27 ms). At -67: none, the longest stretch
11.5 ms (more than half the 20 ms the scan allows). At -66: none, 9.3 ms (under half of it): the quietest level accepted with
margin, FOUND. At -60: 1.3 ms. So room= takes FOUND … CEILING: quieter and the pauses fall back to digital silence, louder and
the bed is heard under the voice. DEFAULT_DB is FOUND + 6 dB.

What the bed needs: numpy and scipy, which the default chain (plain python3, ffmpeg doing the mixing) gets through uv; offline
with neither in uv's cache it stops with one line, and room=off mixes without it. It has the bed written by
`uv run --with numpy --with scipy python roomtone.py render SECONDS LEVEL OUT` (raw float32, stereo, 48 kHz) and adds it
as one more input; a profile mix (numpy already) calls bed() itself.
"""
import importlib.util, os, subprocess, sys

SR = 48000
SEEDS = (19530, 26117)        # one per channel: the same film gives the same bytes, and the sides differ
HIGHPASS, LOWPASS = 60, 5000  # Hz
FADE = 0.5                    # s: ramped at the head and the tail
FOUND = -66.0                 # dBFS RMS: the quietest level the scan accepts with margin (measured 2026-11-22, above)
CEILING = -58.0               # dBFS RMS: no louder (heard under the voice)
DEFAULT_DB = -60.0            # FOUND + 6 dB
PINK_B = (0.049922035, -0.095993537, 0.050612699, -0.004408786)   # Kellet's pinking filter (−3 dB/octave from 10 Hz up)
PINK_A = (1.0, -2.494956002, 2.017265875, -0.522189400)
SETTLE = SR                   # samples made first and dropped: the filters' own start
CHUNK = 1 << 20               # samples made at a time (a long film's bed in pieces, the filters' state carried over)
CAL_S = 20                    # s of the bed at unit gain its level is measured on


def _white(seed, start, n):
    """Samples start … start+n-1 of the white noise for seed, uniform in [-1, 1): splitmix64 of (seed, the sample's number),
    in 64-bit integer arithmetic that wraps, then its top 53 bits as a fraction: exact, so the bytes are ours."""
    import numpy as np
    with np.errstate(over="ignore"):
        z = np.uint64(seed) * np.uint64(0xD1B54A32D192ED03) + (np.arange(start, start + n, dtype=np.uint64) + np.uint64(1)) * np.uint64(0x9E3779B97F4A7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        z = z ^ (z >> np.uint64(31))
    return (z >> np.uint64(11)).astype(np.float64) * (2.0 ** -52) - 1.0


def _channel(seed, n):
    import numpy as np
    from scipy.signal import butter, lfilter, sosfilt
    sos = np.vstack([butter(2, HIGHPASS / (SR / 2), "high", output="sos"), butter(2, LOWPASS / (SR / 2), "low", output="sos")])
    zp, zs = np.zeros(len(PINK_A) - 1), np.zeros((sos.shape[0], 2))
    out, pos = np.empty(n), -SETTLE
    while pos < n:
        y, zp = lfilter(PINK_B, PINK_A, _white(seed, pos + SETTLE, CHUNK), zi=zp)
        y, zs = sosfilt(sos, y, zi=zs)
        lo, hi = max(0, -pos), min(CHUNK, n - pos)
        if hi > lo:
            out[pos + lo:pos + hi] = y[lo:hi]
        pos += CHUNK
    return out


_CAL = None


def calibration():
    """The bed's RMS (dBFS, both channels together) at unit gain, from its first CAL_S s: what the level has to move."""
    global _CAL
    if _CAL is None:
        import numpy as np
        x = np.concatenate([_channel(s, CAL_S * SR) for s in SEEDS])
        _CAL = float(10 * np.log10(np.mean(x ** 2)))
    return _CAL


def bed(seconds, level_db):
    """The bed: `seconds` long (rounded to a sample), stereo, at `level_db` dBFS RMS, ramped from FOUND at the head and to
    FOUND at the tail. → float32 array (n, 2)."""
    import numpy as np
    n = round(seconds * SR)
    x = np.stack([_channel(s, n) for s in SEEDS], 1) * 10 ** ((level_db - calibration()) / 20)
    f = min(round(FADE * SR), n // 2)
    if f:
        floor = 10 ** ((min(FOUND, level_db) - level_db) / 20)
        ramp = floor + (1 - floor) * (0.5 - 0.5 * np.cos(np.pi * np.arange(f) / f))
        x[:f] *= ramp[:, None]
        x[n - f:] *= ramp[::-1][:, None]
    return x.astype(np.float32)


def write(seconds, level_db, path):
    """The bed as raw float32, interleaved stereo, 48 kHz, in `path`: here when numpy and scipy are, else through uv."""
    if not all(importlib.util.find_spec(m) for m in ("numpy", "scipy")):   # plain python3: the default chain
        try:
            subprocess.run(["uv", "run", "-q", "--no-project", "--with", "numpy", "--with", "scipy", "python", os.path.abspath(__file__),
                            "render", repr(float(seconds)), repr(float(level_db)), path], check=True)
        except FileNotFoundError:
            raise ValueError("room tone is made with numpy and scipy, through uv, which is not installed here "
                             "(https://docs.astral.sh/uv/; room=off mixes without it)") from None
        except subprocess.CalledProcessError:
            raise ValueError("room tone is made with numpy and scipy, and uv could not get them (offline, and not in its cache?): "
                             "room=off mixes without it") from None
        return
    with open(path, "wb") as f:
        f.write(bed(seconds, level_db).tobytes())


def level(kv):
    """room= from the mix's arguments → the bed's level in dBFS RMS, or None (room=off). A number from FOUND to CEILING."""
    v = kv.get("room", "on")
    if v == "off":
        return None
    if v == "on":
        return DEFAULT_DB
    try:
        x = float(v)
    except ValueError:
        raise ValueError(f"room={v}: on (the default, {DEFAULT_DB:g} dBFS RMS), off, or a level from {FOUND:g} to {CEILING:g} dBFS RMS") from None
    if not FOUND <= x <= CEILING:
        raise ValueError(f"room={v}: a level from {FOUND:g} dBFS RMS (any quieter and the voice's pauses fall back to digital silence) "
                         f"to {CEILING:g} (any louder and it is heard under the voice)")
    return x


if __name__ == "__main__":
    if len(sys.argv) != 5 or sys.argv[1] != "render":
        sys.exit("usage: roomtone.py render SECONDS LEVEL_DBFS OUT  (raw float32, stereo, 48 kHz)")
    write(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
