"""Put the film's sound and footage on the stretched timeline of js/tmap.js (the holds where a read needs more time).

The picture is written on the old 87.5 s timeline and plays through the time map. This script applies the same map to
  - audio/score.json   from audio/score.base.json (the body score, v3.4 at 80 BPM): a bar that holds a stretch is
                       longer by add / beat and its patterns keep repeating (no held breath: the music never stalls
                       for a read); every position (events, the score's own holds, layer from/until) moves through the map;
  - audio/events.json  from audio/events.base.json (the SFX, old film time), after moving two card pops (the station's
                       second pair of cards now lands 0.75 s later);
  - index.html         the composition's duration and the proof hall's four <video> windows (start, duration,
                       media-start: the frame shown when the camera arrives is kept where the clip is long enough).
The body score's time is the old film time + 4.0 (the score starts 27.0 s in at film 23.0).
usage (from the film folder): python3 tools/retime.py
"""
import bisect, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads(re.search(r"window\.__STRETCH = (\[.*?\]);", (ROOT / "js/tmap.js").read_text()).group(1))
OLD_DUR, T0, BEAT = 87.5, 4.0, 60 / 80


def t_new(o, stretches=S):
    s = 0.0
    for a, b, add in stretches:
        if o < a:
            return o + s
        if o < b:
            return a + s + (o - a) * (b - a + add) / (b - a)
        s += add
    return o + s


# ---- the body score (score time = old film time + 4; only the stretches after the opening) ----
BODY = [(a + T0, b + T0, add) for a, b, add in S if a >= 23.0]
sc = json.loads((ROOT / "audio/score.base.json").read_text())
assert sc["bpm"] == 80
old_beats = [int(sc.get("meters", {}).get(str(k), 4)) for k in range(1, sc["bars"] + 1)]
old_starts = [0.0]
for n in old_beats:
    old_starts.append(old_starts[-1] + n * BEAT)
new_beats = list(old_beats)
for a, b, add in BODY:
    k = bisect.bisect_right(old_starts, a)            # 1-based bar holding a
    assert old_starts[k - 1] <= a and b <= old_starts[k] + 1e-9, (a, b, k)
    n = add / BEAT
    assert abs(n - round(n)) < 1e-9, add
    new_beats[k - 1] += round(n)
new_starts = [0.0]
for n in new_beats:
    new_starts.append(new_starts[-1] + n * BEAT)
tb = lambda T: t_new(T, BODY)


def fmt(x):
    return f"{x:.4f}".rstrip("0").rstrip(".")


def pos_new(p):
    if isinstance(p, (int, float)):
        return tb(float(p))
    k, beat = p.split(":")
    T = old_starts[int(k) - 1] + (float(beat) - 1) * BEAT
    Tn = tb(T)
    k2 = bisect.bisect_right(new_starts, Tn + 1e-9)
    return f"{k2}:{fmt((Tn - new_starts[k2 - 1]) / BEAT + 1)}"


def to_pos(Tn):
    k2 = bisect.bisect_right(new_starts, Tn + 1e-9)
    return f"{k2}:{fmt((Tn - new_starts[k2 - 1]) / BEAT + 1)}"


def at_time(p, starts):
    k, beat = p.split(":")
    return starts[int(k) - 1] + (float(beat) - 1) * BEAT


for e in sc["events"]:
    e["at"] = pos_new(e["at"])
    if "until" in e:
        e["until"] = pos_new(e["until"])
for sec in sc["sections"]:
    for L in sec["layers"]:
        for key in ("from", "until"):
            if key in L:
                L[key] = pos_new(L[key])
sc["master"]["fade"] = [pos_new(x) for x in sc["master"]["fade"]]   # the end fade moves with the last bar's stretch
holds = [(at_time(pos_new(a), new_starts), at_time(pos_new(b), new_starts)) for a, b in sc.get("holds", [])]
holds.sort()
merged = []
for a, b in holds:
    if merged and a <= merged[-1][1] + 1e-6:
        merged[-1] = (merged[-1][0], max(merged[-1][1], b))
    else:
        merged.append((a, b))
sc["holds"] = [[to_pos(a), to_pos(b)] for a, b in merged]
sc["meters"] = {str(k): n for k, n in enumerate(new_beats, 1) if n != 4}
sc["title"] = sc["title"].split(" (")[0] + f" (v5: 80 BPM, {sum(n != o for n, o in zip(new_beats, old_beats))} bars longer by the beats in meters)"
(ROOT / "audio/score.json").write_text(json.dumps(sc, indent=1, ensure_ascii=False) + "\n")

# ---- the SFX ----
ev = json.loads((ROOT / "audio/events.base.json").read_text())
moved = {31.25: 32.0, 31.625: 32.3}                    # station 3's second pair of cards lands later (js/arch.js)
for e in ev:
    for o, n in moved.items():
        if abs(e["t"] - o) < 1e-6 and e["sfx"] == "pop":
            e["t"] = n
    e["t"] = round(t_new(e["t"]), 4)
ev.sort(key=lambda e: e["t"])
(ROOT / "audio/events.json").write_text("[\n" + ",\n".join(" " + json.dumps(e, ensure_ascii=False) for e in ev) + "\n]\n")

# ---- index.html: duration and the proof hall's footage ----
CLIP = {"01": 12.0, "02": 24.8, "03": 25.0, "00": 20.0}
FOCUS = {"v01": 66.5, "v03": 68.75, "v02": 71.0, "v00": 73.25, "v02k": 50.0}   # v02k: the final cut plays 02 (pipeline node K, on at(18))   # old film time the camera arrives (js/main.js MON tFocus − 4)
BASE = {"v01": (62.971, 6.3, 5.6), "v03": (62.971, 13.387, 11.67), "v02": (62.971, 13.387, 11.36), "v00": (73.062, 2.475, 5.5), "v02k": (49.9, 2.3, 7.5)}   # 00 from 5.5 s: its terminal and routing panels (from 0.2 s the whip out landed on a half-typed sentence)
html = (ROOT / "index.html").read_text()
html = re.sub(r'data-duration="[0-9.]+" data-width', f'data-duration="{fmt(t_new(OLD_DUR))}" data-width', html, count=1)
for vid, (st, du, ms) in BASE.items():
    clip = CLIP[vid[1:3]]
    st_n, en_n = t_new(st), t_new(st + du)
    m_focus = ms + (FOCUS[vid] - st)                    # the clip's time when the camera arrives
    ms_n = m_focus - (t_new(FOCUS[vid]) - st_n)
    du_n = en_n - st_n
    ms_n = max(0.0, min(ms_n, clip - du_n - 0.05))
    assert ms_n + du_n <= clip, (vid, ms_n, du_n)
    html, k = re.subn(rf'(<video id="{vid}"[^>]*?) data-start="[0-9.]+" data-duration="[0-9.]+" data-media-start="[0-9.]+"',
                      rf'\1 data-start="{st_n:.3f}" data-duration="{du_n:.3f}" data-media-start="{ms_n:.3f}"', html)
    assert k == 1, vid
    print(f"{vid}: start {st_n:.3f} dur {du_n:.3f} media-start {ms_n:.3f} (clip {clip} s)")
(ROOT / "index.html").write_text(html)
print(f"film {t_new(OLD_DUR):.3f} s · score bars longer: {[(k, n) for k, n in enumerate(new_beats, 1) if n != old_beats[k - 1]]} · holds {len(merged)} · {len(ev)} SFX")
