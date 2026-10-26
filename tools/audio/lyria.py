"""bin/vh music --provider lyria: a generated track (Google's Lyria, through the Gemini API), made once into a file and
kept on record, as the soundtrack instead of a code-composed score. Stdlib only, and ffmpeg (the beat grid: bin/vh beats).

usage: bin/vh music --provider lyria <project> (--prompt TEXT | --prompt-file F) [--model lyria-3.5] [--len 60]
                  [--instrumental] [--as music] [--no-beats] [--id ID] [--dry-run] [--offline DIR] [--json]
       bin/vh music --provider lyria --prices [--json]
<project> as bin/vh assets takes it. bin/vh music without --provider (or --provider code) composes from a score as before.

  The track is asked for through Google's Interactions API with GEMINI_API_KEY (the key in a header only): lyria-3.5
  (the default: a whole piece, up to a few minutes, as WAV), lyria-3-clip-preview (always 30 s, MP3, half the price) or
  lyria-3-pro-preview. Its length is asked for in words, as Lyria takes it: --len adds "about N seconds long" to the
  prompt (there is no length parameter; the answer's own length is what the film gets, said and kept). --instrumental
  adds "Instrumental only, no vocals." (Lyria sings in the prompt's language unless told not to; no living artist's
  voice, no copyrighted lyrics: its filter refuses them). No seed is sent: Lyria's docs name none, and the same
  prompt can give another track.
  Every call is paid, per track: held against the project's budget first (tools/assets/budget.py: no budget, or one it
  would go over, and nothing is called, with how much is missing) and settled at its model's price per track (the
  pricing page, 2026-10-26: the clip $0.04, a whole track $0.08; the answer's usage counts tokens, not money). A
  blocked answer made no track and settles at 0, and so do an error answer and a request that never left; a timeout or
  an answer cut off keeps the price as spent, as such a call may have been billed (said so).
  The answer goes into assets/genmusic/<id>/ (track.<wav|mp3> as it came, prompt.txt, request.json without the key,
  lyrics.txt when it wrote any), on record as AI-generated (model, prompt, cost); audio/<as>.wav (48 kHz, what the
  mix reads) is on record too, made from it. audio/<as>.beats.json comes from bin/vh beats (librosa, detected, not exact
  like bin/vh music's own grid: check it before cutting hard to it; --no-beats leaves it out). Lyria's audio carries a
  SynthID watermark: the film's description says the music is AI-generated (bin/vh assets credits gives the notice).
  --dry-run: the price and the budget's verdict, nothing called. --prices: the models and their prices.
--json: {"version": 1, "tool", …}; the lines go to stderr. --offline DIR: the answer from DIR/responses.json, recorded
before (CONTRIBUTING.md, 联网的命令): no network, and nothing held or spent (the budget's verdict still applies): the
records have no cost and say they were replayed.
Exit: 0 · 1 a call refused by the budget, or failed · 2 usage: no prompt, no key (said by its name), a name taken.
"""
import argparse, json, os, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools" / "assets"))
sys.path.insert(0, str(ROOT / "tools"))
import assets as A, budget, fetch, image, ledger   # noqa: E402,E401

PROG = "bin/vh music --provider lyria"
API = image.API
GENMUSIC = Path("assets") / "genmusic"
# USD a track, from ai.google.dev/gemini-api/docs/pricing, checked 2026-10-26 (no free tier, no batch price)
PRICES = {"lyria-3.5": {"name": "Lyria 3.5", "track": 0.08, "wav": True, "note": "a whole piece, its length asked for in the prompt"},
          "lyria-3-clip-preview": {"name": "Lyria 3 Clip (preview)", "track": 0.04, "wav": False, "note": "always 30 s, MP3"},
          "lyria-3-pro-preview": {"name": "Lyria 3 Pro (preview)", "track": 0.08, "wav": False, "note": "a whole piece"}}
PRICES_CHECKED = "2026-10-26"
out = sys.stdout


class Usage(A.Usage):
    pass


class Failed(Exception):
    pass


def say(*a):
    print(*a, file=out)


def body_of(model, prompt):
    rf = {"type": "audio", **({"mime_type": "audio/wav"} if PRICES[model]["wav"] else {})}
    return {"model": model, "input": [{"type": "text", "text": prompt}], "response_format": rf, "store": False}


def probe_len(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 3)
    except ValueError:
        return None


def cmd_prices(a):
    if a.json:
        print(json.dumps({"version": 1, "tool": f"{PROG} --prices", "checked": PRICES_CHECKED, "currency": "USD", "models": PRICES}, ensure_ascii=False, indent=1))
    say(f"lyria prices (USD a track, ai.google.dev/gemini-api/docs/pricing, checked {PRICES_CHECKED}; no free tier)")
    for m, p in PRICES.items():
        say(f"  {m:<22} {p['name']:<24} ${p['track']:g}  · {p['note']}")
    return 0


def cmd_gen(a):
    project = A.find(a.project)
    if bool(a.prompt) == bool(a.prompt_file):
        raise Usage("--prompt TEXT or --prompt-file F (one of them)")
    if a.prompt_file:
        pf = ledger.find_file(project, a.prompt_file)
        if pf is None:
            raise Usage(f"no such prompt file: {a.prompt_file}")
        prompt = pf.read_text(encoding="utf-8").strip()
    else:
        prompt = a.prompt.strip()
    if not prompt:
        raise Usage("the prompt is empty")
    if a.model not in PRICES:
        raise Usage(f"--model {a.model}: one of {', '.join(PRICES)}")
    if a.len is not None and not 5 <= a.len <= 600:
        raise Usage("--len: 5 to 600 seconds")
    name = a.as_ or "music"
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,40}", name):
        raise Usage(f"--as {name!r}: letters, digits, . _ -")
    dest = project / "audio" / f"{name}.wav"
    if dest.exists():
        raise Usage(f"{ledger.rel(project, dest)} is there already: another --as, or move it away first")
    ask = prompt
    if a.len and a.model != "lyria-3-clip-preview":
        ask += f"\n\nLength: about {a.len:g} seconds."
    if a.instrumental:
        ask += "\n\nInstrumental only, no vocals."
    price = PRICES[a.model]["track"]
    chk = budget.check(project, price, "USD")
    cid = a.id or ledger.slug("music-" + "-".join(re.findall(r"[A-Za-z0-9]+", prompt)[:4]) if re.search(r"[A-Za-z0-9]", prompt) else "music")
    _, ents, _ = ledger.entries(project)
    taken = {e["record"].get("id") for e in ents}
    if a.id and (cid in taken or (project / GENMUSIC / cid).exists()):
        raise Usage(f"the id {cid} is taken (ids are never reused): another --id")
    base, k = cid, 1
    while cid in taken or (project / GENMUSIC / cid).exists():
        k += 1
        cid = f"{base}-{k}"
    plan = {"model": f"gemini/{a.model}", "price": price, "len_asked": a.len, "instrumental": a.instrumental, "id": cid, "file": ledger.rel(project, dest),
            "budget": {x: chk[x] for x in ("ok", "budget", "spent", "held", "after", "short", "message")}}
    if a.dry_run:
        if a.json:
            print(json.dumps({"version": 1, "tool": PROG, "dry_run": True, "project": str(project), **plan}, ensure_ascii=False, indent=1))
        say(f"music --provider lyria --dry-run: {a.model}, ${price:g} a track" + (f", about {a.len:g} s asked for" if a.len else ""))
        say(f"  {chk['message']}")
        say("  nothing called (--dry-run)")
        return 0
    if not a.offline and not os.environ.get("GEMINI_API_KEY"):
        raise Usage("set GEMINI_API_KEY (Google AI Studio → Get API key): it is read from the environment only")
    if not chk["ok"]:
        raise Failed(f"{chk['message']} (--dry-run shows the price)")
    folder = project / GENMUSIC / cid
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "prompt.txt").write_text(ask + "\n", encoding="utf-8")
    body = body_of(a.model, ask)
    (folder / "request.json").write_text(json.dumps(body, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if a.offline:   # a recorded answer: nothing is called, so nothing is held or spent
        try:
            data, mime, said, _ = image.media_of(fetch.post_json(API, body, fetch.opener_from(a.offline)), "audio")
        except image.Failed as e:
            raise Failed(str(e))
    else:
        try:
            with budget.hold(project, price, "USD", f"music {cid} ({a.model})", tool=PROG, asset=cid) as h:
                try:
                    answer = image.paid_call(h, price, API, body, fetch.opener_from(None), timeout=600)
                except image.Failed as e:
                    raise Failed(str(e))
                try:
                    data, mime, said, _ = image.media_of(answer, "audio")
                except image.Failed as e:   # a blocked answer made no track, and a track is what is billed
                    h.settle(0)
                    raise Failed(str(e))
                h.settle(price)
        except budget.Refused as e:
            raise Failed(str(e))
    ext = {"audio/wav": ".wav", "audio/x-wav": ".wav", "audio/wave": ".wav", "audio/mpeg": ".mp3", "audio/mp3": ".mp3"}.get(str(mime).split(";")[0].lower(), ".mp3")
    track = folder / f"track{ext}"
    track.write_bytes(data)
    if said.strip():
        (folder / "lyrics.txt").write_text(said.strip() + "\n", encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(f".{dest.stem}.part.wav")
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(track), "-vn", "-af", "aresample=48000", "-c:a", "pcm_s16le", "-ac", "2", str(tmp)],
                       capture_output=True, text=True)
    if r.returncode:
        tmp.unlink(missing_ok=True)
        raise Failed(f"the track came ({ledger.rel(project, track)}, paid) but ffmpeg cannot read it: {r.stderr.strip()[-300:]}")
    os.replace(tmp, dest)
    got = probe_len(dest)
    src = {"origin": "generated", "provider": "gemini"}
    lic = "the vendor's terms: Gemini API (Lyria)"
    try:
        rec, _, _ = ledger.add(project, str(track), id=cid, kind="audio", license=lic, license_class="generated", source=src, aigc=True,
                               model=f"gemini/{a.model}", prompt_file=str(folder / "prompt.txt"), cost=None if a.offline else {"amount": price, "currency": "USD"},
                               tags=["genmusic"], note="AI-generated music (SynthID watermark)", extra={"request": {"len_asked": a.len, "instrumental": a.instrumental},
                                      **({"offline": f"replayed from a recording: nothing called, nothing spent (a call: ${price:g})"} if a.offline else {})},
                               by=PROG)
        rec2, _, _ = ledger.add(project, str(dest), id=ledger.slug(f"{cid}-wav"), kind="audio", license=lic, license_class="generated", source=src,
                                aigc=True, model=f"gemini/{a.model}", derived_from=cid, used_by=["bgm"], note=f"48 kHz WAV of {ledger.rel(project, track)}",
                                by=PROG)
    except (ledger.Refused, ValueError, ledger.LedgerError) as e:
        raise Usage(f"made {ledger.rel(project, dest)}, but not registered: {e}")
    beats = None
    if not a.no_beats:
        bf = project / "audio" / f"{name}.beats.json"
        b = subprocess.run([str(ROOT / "bin" / "vh"), "beats", str(dest), str(bf)], capture_output=True, text=True)
        beats = ledger.rel(project, bf) if b.returncode == 0 and bf.is_file() else None
        if beats is None:
            say(f"  ! bin/vh beats failed ({(b.stderr or b.stdout).strip()[-160:]}): no beat grid (bin/vh beats {ledger.rel(project, dest)} later)")
    try:
        import activity
        activity.note(f"music {cid} ({a.model}, ${price:g})", [str(project / ledger.LEDGER), str(dest)])
    except Exception:   # the log never fails a command
        pass
    say(f"made {cid}: {ledger.rel(project, track)} → {ledger.rel(project, dest)} · {got:.1f} s · gemini/{a.model} · ${price:g}")
    if a.len and got and abs(got - a.len) > max(5, 0.15 * a.len):
        say(f"  ! asked for about {a.len:g} s, got {got:.1f} s: Lyria takes length as words; cut it on a downbeat of its grid, or ask again")
    if beats:
        say(f"  beats: {beats} (detected: check before cutting hard to them)")
    say("  " + budget.line(project))
    if a.json:
        print(json.dumps({"version": 1, "tool": PROG, "project": str(project), **plan, "length": got, "track": ledger.rel(project, track),
                          "beats": beats, "records": [rec, rec2]}, ensure_ascii=False, indent=1))
    return 0


def parser():
    ap = argparse.ArgumentParser(prog=PROG, description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="\n\n".join(__doc__.split("\n\n")[1:]))
    ap.add_argument("project", nargs="?")
    ap.add_argument("--provider", choices=("lyria",), default="lyria")
    ap.add_argument("--prompt")
    ap.add_argument("--prompt-file")
    ap.add_argument("--model", default="lyria-3.5")
    ap.add_argument("--len", type=float)
    ap.add_argument("--instrumental", action="store_true")
    ap.add_argument("--as", dest="as_")
    ap.add_argument("--id")
    ap.add_argument("--no-beats", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--prices", action="store_true")
    ap.add_argument("--offline")
    ap.add_argument("--json", action="store_true")
    return ap


def main(argv):
    global out
    a = parser().parse_args(argv)
    if a.json:
        out = sys.stderr
        A.out = sys.stderr
    try:
        if a.prices:
            return cmd_prices(a)
        if not a.project:
            raise Usage("which project? (bin/vh music --provider lyria <project> --prompt …)")
        if not shutil.which("ffmpeg"):
            raise Usage("needs ffmpeg and ffprobe (bin/vh doctor)")
        return cmd_gen(a)
    except (Usage, A.Usage) as e:
        print(f"{PROG}: {e}", file=sys.stderr)
        return 2
    except (Failed, fetch.FetchError, budget.Refused) as e:
        print(f"{PROG}: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except BrokenPipeError:
        sys.exit(0)
