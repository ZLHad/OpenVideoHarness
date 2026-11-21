"""Room tone: the quiet bed bin/vh mix lays under a voice that has no music, so its pauses are a room, not dead air.

A synthesized narration has nothing between its words: the joins are exact digital zero and its own pauses fall under
-60 dBFS, which the film's floor forbids (no digital silence in a film with sound). A recording made in a room never
has that: it carries the room's own sound under every pause. This is that sound, made the same way each time:
pink noise (ffmpeg's anoisesrc, one fixed seed per channel, so the two sides are not the same and the bytes are),
high-passed at 60 Hz and low-passed at 5 kHz (a soft room, no hiss on top, no rumble under), at a fixed RMS level,
faded in and out over the film's first and last half second so neither end starts with a step. It goes in after the
mix's loudness gain, so its level in the film is the level asked for, and the film's integrated loudness and true peak
stay as they were (it sits 40 dB and more under speech at -14 LUFS).

The default level, DEFAULT_DB, and how it was found: on the 25 s demo film's voice-only mix (Qwen3-TTS, -14 LUFS), the
bed at each level from -74 to -56 dBFS RMS in 1 dB steps, and bin/vh qa's digital-silence scan (every channel under
-60 dBFS for 20 ms or more) counted, with the longest stretch any part of the checked span spends with every
channel under -60 dBFS. Without a bed: 22 runs, the longest 352 ms. At -74 to -69: 19 to 30 runs. At -68: 2 runs (23 ms).
At -67: none, the longest stretch 10.8 ms (half the 20 ms the scan allows). At -66: none, 7.4 ms (a third of it): the
quietest level accepted with margin, FOUND. At -60: 1.3 ms. The film's integrated loudness (-14.4 LUFS by ffmpeg's
ebur128) and true peak (-1.5 dBFS) read the same with the bed at -60 as without it. Stdlib and ffmpeg only (the
default chain runs on plain python3).
"""
import subprocess

SR = 48000
SEEDS = (19530, 26117)        # one per channel: the same film gives the same bytes, and the sides differ
HIGHPASS, LOWPASS = 60, 5000  # Hz
FADE = 0.5                    # s: in at the head, out at the tail
FOUND = -66.0                 # dBFS RMS: the quietest level the scan accepts with margin (measured 2026-11-22, below)
DEFAULT_DB = -60.0            # FOUND + 6 dB, under the -58 dBFS ceiling the bed must not pass


def source(seconds, level_db, label="bed"):
    """An ffmpeg filtergraph that makes the bed: `seconds` long, stereo, 48 kHz, at `level_db` dBFS RMS, into [label]."""
    n = round(seconds * SR)
    cal = calibration()
    nz = lambda s, o: f"anoisesrc=r={SR}:color=pink:seed={s}:amplitude=1:duration={seconds + 0.1:.4f}[{o}]"   # noqa: E731
    out = max(0.0, n / SR - FADE)
    return (f"{nz(SEEDS[0], label + 'l')};{nz(SEEDS[1], label + 'r')};"
            f"[{label}l][{label}r]join=inputs=2:channel_layout=stereo,highpass=f={HIGHPASS},lowpass=f={LOWPASS},"
            f"volume={level_db - cal:.4f}dB,atrim=end_sample={n},afade=t=in:st=0:d={FADE},afade=t=out:st={out:.4f}:d={FADE}[{label}]")


_CAL = None


def calibration():
    """The RMS (dBFS) of the filtered noise at amplitude 1, measured once from 20 s of it: what volume= has to move."""
    global _CAL
    if _CAL is None:
        nz = lambda s: f"anoisesrc=r={SR}:color=pink:seed={s}:amplitude=1:duration=20"   # noqa: E731
        g = (f"{nz(SEEDS[0])}[l];{nz(SEEDS[1])}[r];[l][r]join=inputs=2:channel_layout=stereo,highpass=f={HIGHPASS},"
             f"lowpass=f={LOWPASS},astats=measure_perchannel=none:measure_overall=RMS_level")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-filter_complex", g, "-f", "null", "-"],
                           capture_output=True, text=True, check=True)
        lines = [ln for ln in r.stderr.splitlines() if "RMS level dB" in ln]
        _CAL = float(lines[-1].split(":")[-1])
    return _CAL


def render(seconds, level_db):
    """The bed as raw float32 interleaved stereo bytes (the profile chain adds it in numpy)."""
    g = source(seconds, level_db)
    r = subprocess.run(["ffmpeg", "-v", "error", "-filter_complex", g, "-map", "[bed]", "-f", "f32le", "-acodec", "pcm_f32le", "-"],
                       capture_output=True, check=True)
    return r.stdout


def level(kv):
    """room= from the mix's arguments → the bed's level in dBFS RMS, or None (room=off). A number may go no louder than -50."""
    v = kv.get("room", "on")
    if v == "off":
        return None
    if v == "on":
        return DEFAULT_DB
    try:
        x = float(v)
    except ValueError:
        raise ValueError(f"room={v}: on (the default, {DEFAULT_DB:g} dBFS RMS), off, or a level in dBFS RMS such as -60")
    if not -90 <= x <= -50:
        raise ValueError(f"room={v}: a level between -90 and -50 dBFS RMS (a room under a voice is quiet)")
    return x
