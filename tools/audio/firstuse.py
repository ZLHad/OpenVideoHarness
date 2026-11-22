"""The big first downloads the sound commands can start, said before they start. Stdlib only.

usage: python3 tools/audio/firstuse.py <kind[,kind]> [--packages-missing kind[,kind]]   the one line (nothing when nothing big
                                                                                        is to come); bin/vh's first_use helper
       python3 tools/audio/firstuse.py --package <kind>                                the Python package bin/vh probes for it

Kinds: qwen, the local voice (bin/vh tts and voices audition with the default provider); whisper, the local Whisper (tts and
voices audition --align local, pace --align whisper). Each is Python packages fetched by uv on first use and a model fetched
from Hugging Face on first load, on Apple Silicon only (mlx). Their sizes live here and only here: bin/vh doctor --first and
the line bin/vh says read them. Measured 2026-11-22 on macOS (Apple Silicon), each in an empty cache: mlx-audio and its
packages 0.8 GB, mlx-whisper and its packages 2.0 GB (torch among them; the two together 2.6 GB), the Qwen3-TTS model
1.8 GB, whisper-large-v3-turbo 1.6 GB.
"""
import os, platform, sys, threading
from pathlib import Path

KINDS = {
    "qwen": {"what": "the local voice", "package": "mlx-audio", "packages_gb": 0.8, "env": "QWEN_TTS_MODEL",
             "model": "mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit", "model_gb": 1.8,
             "around": "--provider edge needs only a small package (free, online: the script goes to Microsoft's voice service)"},
    "whisper": {"what": "the local Whisper", "package": "mlx-whisper", "packages_gb": 2.0, "env": "WHISPER_MODEL",
                "model": "mlx-community/whisper-large-v3-turbo", "model_gb": 1.6,
                "around": "--align gemini needs a Gemini key and no download"},
}


def gb(x):
    return f"{x:.1f} GB"


def total(kinds=("qwen",)):
    """The whole first download of these kinds, packages and models (what doctor --first says)."""
    return sum(KINDS[k]["packages_gb"] + KINDS[k]["model_gb"] for k in kinds)


def here():
    """These downloads run on Apple Silicon only (mlx); elsewhere the commands say so themselves."""
    return sys.platform == "darwin" and platform.machine() == "arm64"


def hub_dir():
    """Where the Hugging Face Hub keeps models, worked out as huggingface_hub does (stdlib, before it is installed)."""
    if os.environ.get("HF_HUB_CACHE"):
        return Path(os.environ["HF_HUB_CACHE"])
    home = os.environ.get("HF_HOME") or os.path.join(os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"), "huggingface")
    return Path(home) / "hub"


def model_id(kind):
    return os.environ.get(KINDS[kind]["env"], KINDS[kind]["model"])


def model_cached(kind):
    """The model is here: a local folder, or a snapshot with weights in the Hub's cache. Another model than ours (the env
    variable) counts as here when it is a folder; else as we cannot size it, it is said without a size."""
    m = model_id(kind)
    if os.path.isdir(os.path.expanduser(m)):
        return True
    d = hub_dir() / ("models--" + m.replace("/", "--")) / "snapshots"
    return any(d.glob("*/*.safetensors")) or any(d.glob("*/*.npz"))


def line(kinds, packages_missing=()):
    """The one line before a first download of these kinds (or None: nothing big to fetch, or not this platform): how much,
    roughly how long, that the progress shows, and the way around each."""
    if not here():
        return None
    parts, size, around, whats = [], 0.0, [], []
    for k in kinds:
        K = KINDS[k]; mine = model_id(k) == K["model"]
        pk, md = k in packages_missing, not model_cached(k)
        if not (pk or md):
            continue
        whats.append(K["what"])
        size += (K["packages_gb"] if pk else 0) + (K["model_gb"] if md and mine else 0)
        model = "model" if mine else f"model {model_id(k)}"
        parts.append(f"{K['what']}'s " + ("Python packages and " + model if pk and md else "Python packages" if pk else model))
        around.append(K["around"])
    if not parts:
        return None
    return (f"  first use of {' and '.join(whats)}: about {gb(size)} to download once ({', '.join(parts)}); a few minutes on a fast"
            f" line, half an hour or more on a slow one; the progress shows below. Without it: {'; '.join(around)}")


def show_progress(total_gb, every=10.0, folder=None):
    """A line every `every` seconds with how much a download has added to `folder` (default: the Hub's whole cache, as its
    xet transfer stages the parts outside the model's own folder). Written to the process's real stdout (sys.__stdout__),
    so a caller that has swapped sys.stdout (contextlib.redirect_stdout, around a library that prints as it loads) does not
    swallow it. → the thread's stop event."""
    folder = Path(folder) if folder else hub_dir()
    stop = threading.Event()

    def size():
        return sum(f.stat().st_size for f in folder.rglob("*") if f.is_file() and not f.is_symlink()) if folder.is_dir() else 0
    base = size()

    def run():
        last = None
        while not stop.wait(every):
            got = round((size() - base) / 1e9, 1)
            if got != last:
                out = sys.__stdout__ or sys.stderr
                out.write(f"  model: {got:.1f} of about {total_gb} GB\n"); out.flush(); last = got
    threading.Thread(target=run, daemon=True).start()
    return stop


def progress(kind):
    """show_progress for this kind's model when it is not here yet and no progress bar will show (output nobody watches
    live, or the Hub's bars turned off from outside): the stop event, or None."""
    if model_cached(kind):
        return None
    if sys.stderr.isatty() and not os.environ.get("HF_HUB_DISABLE_PROGRESS_BARS"):
        return None
    mine = model_id(kind) == KINDS[kind]["model"]
    return show_progress(KINDS[kind]["model_gb"] if mine else "?")


def main(argv):
    if argv[:1] in (["-h"], ["--help"]) or not argv:
        print(__doc__.strip()); return 0
    if argv[0] == "--package" and len(argv) == 2 and argv[1] in KINDS:
        print(KINDS[argv[1]]["package"]); return 0
    kinds = [k for k in argv[0].split(",") if k]
    miss = argv[2].split(",") if argv[1:2] == ["--packages-missing"] and len(argv) == 3 else []
    if any(k not in KINDS for k in kinds + miss) or len(argv) not in (1, 3):
        print(f"firstuse: kinds are {', '.join(KINDS)} (python3 tools/audio/firstuse.py -h)", file=sys.stderr); return 2
    said = line(kinds, miss)
    if said:
        print(said, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
