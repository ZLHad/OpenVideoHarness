"""Seconds to frames, the one way the repo does it (stdlib only). tools/film/timegrid.mjs is the same two functions in JS,
written the same way, so that in IEEE doubles they give the same frame for the same seconds (tools/ci.sh checks it).

  frame_from(t, fps)   the first frame at or after t: ceil(t * fps - 1e-6). Frame k belongs to the span [s, e) when
                       s <= k / fps < e, so every boundary is this: a film's frame count (its duration), where an entry
                       of an edit list starts and ends, render --range, patch --seconds. 6.85 s at 30 fps is frame 206
                       (frame 205 starts at 6.833 s, before the cut); 4.1 s is 123 (4.1 * 30 is 122.99999999999999 in a
                       double: the 1e-6 takes that in)
  frame_at(t, rate)    the frame on screen at t: floor(t * rate + 1e-6). "Which frame is this moment": a clip's in point
                       (rate: its own, a fraction such as "24000/1001"), a tile of bin/vh thumbs, a finding's frame

rate: a whole number (30), a number (29.97 is read as it is), "24000/1001" or [24000, 1001]. Neither function rounds t
to the millisecond first: a page's duration is often computed (57.21333… s), and rounding it would move a frame boundary.
"""
import math
from fractions import Fraction

EPS = 1e-6


def rate_of(rate):
    """(num, den) of a frame rate: 30, 29.97, "30", "24000/1001", [24000, 1001] or a Fraction; ValueError for anything else."""
    if isinstance(rate, bool):
        raise ValueError(f"not a frame rate: {rate!r}")
    if isinstance(rate, Fraction):
        num, den = rate.numerator, rate.denominator
    elif isinstance(rate, (list, tuple)) and len(rate) == 2:
        num, den = rate
    elif isinstance(rate, str):
        num, _, den = rate.strip().partition("/")
        try:
            num, den = float(num), float(den or 1)
        except ValueError:
            raise ValueError(f"not a frame rate: {rate!r}") from None
    else:
        num, den = rate, 1
    if isinstance(num, bool) or isinstance(den, bool) or not all(isinstance(x, (int, float)) for x in (num, den)):
        raise ValueError(f"not a frame rate: {rate!r}")
    if not (math.isfinite(num) and math.isfinite(den) and num > 0 and den > 0):
        raise ValueError(f"not a frame rate: {rate!r}")
    num = int(num) if float(num).is_integer() else num
    den = int(den) if float(den).is_integer() else den
    return num, den


def frame_from(t, fps):
    """The first frame at or after t seconds (the boundary of a span)."""
    num, den = rate_of(fps)
    return math.ceil(t * num / den - EPS)


def frame_at(t, rate):
    """The frame on screen at t seconds."""
    num, den = rate_of(rate)
    return math.floor(t * num / den + EPS)
