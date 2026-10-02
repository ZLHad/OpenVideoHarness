"""Generate the AI-image films for the opening's waterfall (user approved 2026-10-02, about $1.8):
40 stills, gemini-3.1-flash-image, 16:9, 512 px. Fictional people and places only; no brands, no logos, no real persons.
Each image is saved to assets/ai/NN.jpg with its prompt in assets/ai/prompts.json (the ledger in NOTES.md).

The key is read from the environment (GEMINI_API_KEY); it is never written or printed.
usage (from the project root): uv run --no-project python tools/gen_images.py [--only 3,7]
"""
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "ai"
MODEL = "gemini-3.1-flash-image"
STYLE = " Cinematic still from an AI-generated video, 16:9, rich colour, sharp focus, no text, no watermark, no logos."
PROMPTS = [
    "Close-up portrait of an elderly fisherman (fictional) at golden hour on a wooden boat, warm rim light, film grain.",
    "A red fox standing in a snowy pine forest, shallow depth of field, soft falling snow.",
    "Anime-style scene: a girl (original character) on a rooftop at sunset looking over a city skyline, painterly clouds.",
    "Futuristic city at night with flying vehicles, neon reflections on wet streets, rain.",
    "A sculpted glass perfume bottle on black velvet, studio product lighting, caustic highlights.",
    "An astronaut floating above the curve of the Earth, sunrise on the horizon.",
    "A humpback whale underwater with sun rays piercing the blue water.",
    "A desert caravan of camels walking along a dune ridge at dusk, long shadows.",
    "A lone swordsman (fictional) in a misty bamboo forest, morning light.",
    "Macro shot of a hummingbird drinking nectar from a red flower, frozen wings.",
    "A cozy wooden cabin in snowy mountains at blue hour, warm windows glowing.",
    "Macro shot of a dewdrop on a green leaf reflecting a sunrise.",
    "A dragon flying over a mountain lake at dawn, epic fantasy landscape.",
    "A sports car (no badge) drifting on a wet race track at night, sparks and motion blur.",
    "A chef (fictional) plating a colourful dish in a warm restaurant kitchen.",
    "A ballet dancer mid-leap on a dark stage under a single spotlight.",
    "A cyberpunk street market at night with paper lanterns and steam.",
    "An ancient pavilion on a cliff in misty mountains, Chinese ink-wash atmosphere.",
    "A child (fictional) flying a kite on a green hill under big summer clouds.",
    "A tiger walking through tall golden grass, low angle.",
    "Aerial view of a coral atoll with turquoise lagoons.",
    "A small robot gardener watering plants in a sunlit greenhouse.",
    "Northern lights over a frozen lake with a lone glowing tent.",
    "A bloom of glowing jellyfish in the dark deep ocean.",
    "A surfer riding inside a barrel wave, spray backlit by the sun.",
    "Close-up of a steaming bowl of ramen with soft bokeh lights.",
    "A medieval castle on a sea cliff at sunrise, mist below.",
    "A pianist's hands on piano keys, dramatic side light, dark background.",
    "Hot air balloons rising over a valley at dawn.",
    "A giant panda eating bamboo in a green forest.",
    "A lighthouse in a storm with huge crashing waves.",
    "A person in a red coat (fictional) walking through a snowy city street at night, shallow depth of field.",
    "3D cartoon style: a cute original creature in a glowing mushroom forest.",
    "A spaceship approaching a ringed planet, lens flare.",
    "A vintage steam train crossing a stone viaduct in autumn forest.",
    "An owl on a branch in moonlight, silver light.",
    "Paper-craft style landscape with layered hills and a tiny house (original style).",
    "A tall waterfall in a lush tropical jungle, mist and rainbow.",
    "Claymation style: a small original robot on a wooden desk, warm lamp light.",
    "Night sky over a desert rock arch with the Milky Way, long exposure look.",
]


def generate(prompt, key):
    body = {"model": MODEL, "input": [{"type": "text", "text": prompt + STYLE}],
            "response_format": {"type": "image", "mime_type": "image/jpeg", "aspect_ratio": "16:9", "image_size": "512"}}
    req = urllib.request.Request("https://generativelanguage.googleapis.com/v1beta/interactions", data=json.dumps(body).encode(),
                                 headers={"x-goog-api-key": key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read())


def find_image(obj):
    """the first base64 image anywhere in the response (the field name has moved between API versions)"""
    if isinstance(obj, dict):
        for k in ("output_image", "inline_data", "inlineData"):
            v = obj.get(k)
            if isinstance(v, dict) and isinstance(v.get("data"), str): return v["data"]
        mt = str(obj.get("mime_type") or obj.get("mimeType") or "")
        if mt.startswith("image/") and isinstance(obj.get("data"), str) and len(obj["data"]) > 1000: return obj["data"]
        for v in obj.values():
            got = find_image(v)
            if got: return got
    if isinstance(obj, list):
        for v in obj:
            got = find_image(v)
            if got: return got
    return None


def keys_of(obj, depth=0):
    if isinstance(obj, dict) and depth < 4: return {k: keys_of(v, depth + 1) for k, v in obj.items() if k != "data"}
    if isinstance(obj, list) and obj: return [keys_of(obj[0], depth + 1)]
    return type(obj).__name__


def main():
    key = os.environ.get("GEMINI_API_KEY")
    if not key: sys.exit("GEMINI_API_KEY is not set")
    only = None
    if "--only" in sys.argv: only = {int(x) for x in sys.argv[sys.argv.index("--only") + 1].split(",")}
    OUT.mkdir(parents=True, exist_ok=True)
    ledger = OUT / "prompts.json"; led = json.loads(ledger.read_text()) if ledger.exists() else {}
    for i, p in enumerate(PROMPTS):
        dst = OUT / f"{i:02d}.jpg"
        if (only and i not in only) or (not only and dst.exists()): continue
        for attempt in range(4):
            try:
                res = generate(p, key); data = find_image(res)
                if not data:
                    print(f"[ai] {i:02d}: no image in the response; shape: {json.dumps({k: v for k, v in keys_of(res).items() if k != 'usage'})[:900]}"); break
                dst.write_bytes(base64.b64decode(data)); led[f"{i:02d}"] = {"prompt": p + STYLE, "model": MODEL, "date": time.strftime("%Y-%m-%d")}
                ledger.write_text(json.dumps(led, ensure_ascii=False, indent=1)); print(f"[ai] {i:02d} ok ({dst.stat().st_size // 1024} KB)"); break
            except urllib.error.HTTPError as e:
                msg = e.read().decode(errors="replace")[:300]
                print(f"[ai] {i:02d}: HTTP {e.code} {msg}")
                if e.code in (429, 503): time.sleep(20 * (attempt + 1)); continue
                break
            except Exception as e:
                print(f"[ai] {i:02d}: {type(e).__name__} {e}"); time.sleep(5)
        time.sleep(7)                                          # stay under ~8 requests a minute


main()
