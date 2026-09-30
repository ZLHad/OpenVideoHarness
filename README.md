<div align="center">

# OpenVideoHarness

**Coding agents like Claude Code and Codex can make videos by writing programs. This makes them do it reliably.**

Explainers, science shorts, product films, music videos, data stories, paper talks, hand-drawn shorts and meme edits: 8 video types, 28 styles, one workflow.

**English** · [中文](README.zh-CN.md) · [Wiki](https://github.com/ZLHad/OpenVideoHarness/wiki)

![License: MIT](https://img.shields.io/badge/license-MIT-black)
![Agents](https://img.shields.io/badge/agents-Claude%20Code%20%7C%20Codex-orange)
![Engines](https://img.shields.io/badge/engines-HyperFrames%20%7C%20Remotion%20%7C%20Manim%20%7C%20p5.brush-blue)
![Voice](https://img.shields.io/badge/voice-Qwen3--TTS%20zh%20%7C%20en-purple)
![Styles](https://img.shields.io/badge/styles-28-green)

<a href="showcase/04-intro-film/"><img src="showcase/04-intro-film/media/preview.gif" width="820" alt="OpenVideoHarness intro film"></a>

<sub>▶ The full intro film (81 s, with music, zh/en subtitle tracks) is in <a href="showcase/04-intro-film/media/final.mp4">showcase/04-intro-film</a>. An agent made it by following this repo, and the soundtrack is code too.</sub>

</div>

---

## What this is

AI can already make "a video from one sentence". It doesn't paint the pictures. It writes a program that works out what every frame looks like; a browser (or Manim) renders the frames one by one, and sound is added at the end. The community has made plenty of black-hole explainers, hand-drawn music videos, launch films and math animations this way.

The hard part is making it **reliable**. The same model is stunning one day and a mess the next: rushed pacing, glow everywhere, made-up numbers. The model is smart enough. What it lacks is a craft to follow.

OpenVideoHarness is that craft, written as docs and tools an agent can follow:

- **A method for each kind of video.** Say "make a science short" or "make a launch film", and it reads the workflow for that type: which engine, which steps, what looks good, what is off limits.
- **It stops and asks you three times.** At the outline, the storyboard and the first draft, it waits for your go-ahead. Direction gets settled while changes are still cheap. For a quick try, switch to the `quick` level and it just renders.
- **More than one taste.** 28 styles learned from famous work, each with a real rendered sample, offered to you before anything is built.
- **It checks its own work.** An agent can't watch video or hear sound, so it looks at rendered frames, measures the mix, and fixes things until a checklist passes. A reviewer who didn't make the film then scores it.
- **Sound included.** Chinese and English voiceover (a local open-source model), bilingual subtitles, music and sound effects written as code, mixing and a final audio check.

It isn't a new rendering engine. It is a layer of "how to do it" on top of engines like HyperFrames, Manim, Remotion and p5.brush.

## Start in 30 seconds

```bash
curl -fsSL https://raw.githubusercontent.com/ZLHad/OpenVideoHarness/main/install.sh | bash
```

This one command:
- clones the repo into `~/OpenVideoHarness` (about 330 MB; the sample films are in it);
- installs the dependencies of the built-in hand-drawn engine and the style renderer (about 210 MB);
- fetches 30 read-only reference repos (about 195 MB; `--no-refs` skips them);
- registers the `open-video-harness` skill for Claude Code and Codex, so saying "make a video" in any folder leads the agent here.

That is about 730 MB on disk. The first render and the sound tools download more the first time you use them: [what gets downloaded](#what-gets-downloaded) lists how much and where. New here? The wiki's [Getting Started](https://github.com/ZLHad/OpenVideoHarness/wiki/Getting-Started) page goes from nothing to a first video.

Then open Claude Code (or Codex) and say what you want:

```bash
cd ~/OpenVideoHarness && claude
```

```text
Make a 30-second vertical science short: why does a low-orbit satellite's signal change pitch? English voiceover, English and Chinese subtitles.
```

What happens next:
1. It hands you a one-screen outline, with two or three styles to choose from.
2. Then a storyboard and a sheet of keyframes.
3. Then a first draft, along with the two or three things it likes least.

Only when you say yes does it render the final.

## See what it makes

Every film below was made by an agent **reading only this repo's docs**. Each folder has the brief, storyboard, review notes, fix-up log and full source, so you can start a similar video from it.

<table>
<tr>
<td rowspan="2" width="30%" valign="top"><a href="showcase/02-short-leo-doppler/"><img src="showcase/02-short-leo-doppler/media/preview.gif" width="100%" alt="02 · Vertical science short"></a><br><b>02 · Vertical science short</b><br><sub>HyperFrames · 24.8 s · 1080×1920 · reads without sound</sub><br><sub>“Why does a LEO satellite's signal change pitch?”</sub></td>
<td width="35%" valign="top"><a href="showcase/04-intro-film/"><img src="showcase/04-intro-film/media/poster.png" width="100%" alt="04 · Intro film"></a><br><b>04 · Intro film (one-take 3D)</b><br><sub>HyperFrames + Three.js · 81 s · code-composed score · zh/en subtitles</sub><br><sub>This repo's own product film, revised after two rounds of human notes</sub></td>
<td width="35%" valign="top"><a href="showcase/01-handdrawn-clawd-leaf/"><img src="showcase/01-handdrawn-clawd-leaf/media/preview.gif" width="100%" alt="01 · Hand-drawn character short"></a><br><b>01 · Hand-drawn character short</b><br><sub>p5.brush · 12 s · 3 review rounds</sub><br><sub>“Clawd tries to film a falling leaf; the wind keeps stealing it”</sub></td>
</tr>
<tr>
<td width="35%" valign="top"><a href="showcase/03-math-fourier/"><img src="showcase/03-math-fourier/media/preview.gif" width="100%" alt="03 · 3b1b-style math explainer"></a><br><b>03 · 3b1b-style math explainer</b><br><sub>Manim · 25 s · revised after an independent review</sub><br><sub>“Build a square wave from sine waves, one at a time”</sub></td>
<td width="35%" valign="top"><a href="showcase/00-promo-launch-film/"><img src="showcase/00-promo-launch-film/media/preview.gif" width="100%" alt="00 · Launch short"></a><br><b>00 · Launch short</b><br><sub>HyperFrames · 20 s · silent</sub><br><sub>“A launch film for this repo, using only its real terminal and folders”</sub></td>
</tr>
</table>

The GIFs are compressed previews; each folder has the original in `media/final.mp4`. Films you make with it are welcome in `showcase/` as a PR.

<details>
<summary><b>Similar work from the community, and our breakdowns of it</b></summary>

| Work | Type | How it was made | Breakdown |
|---|---|---|---|
| [I'm Upping My P(doom)](https://x.com/other__reality/status/2102514581684052169) | Hand-drawn MV · 156 s | p5.brush, 9 chapters drawn by parallel subagents | [cases/mv-pdoom.md](cases/mv-pdoom.md) |
| [Functional Emotions](https://x.com/eudaemonea/status/2102610626321490404) | Painted MV · 372 s | A custom WebGL brush renderer, 7 subagents | [cases/mv-functional-emotions.md](cases/mv-functional-emotions.md) |
| [Claude Pop](https://x.com/donaldjewkes/status/2102801274173587569) | Hybrid MV | Generative video as a base, traced over in code; a 12-hour run | [cases/mv-claude-pop.md](cases/mv-claude-pop.md) |
| [The real physics of Interstellar: black holes](https://x.com/AndyL5cc/status/2104519528873103773) | Science explainer · 143 s | A one-sentence request; one black-hole shader carries the film | [cases/explainer-interstellar-blackhole.md](cases/explainer-interstellar-blackhole.md) |
| [Applore promo](https://x.com/decohack/status/2104502625055949242) | Product film · 15 s | One showreel prompt plus real assets | [cases/promo-applore.md](cases/promo-applore.md) |
| [Austerlitz, 2 December 1805](https://x.com/WinterArc2125/status/2103116235009347650) | 3D history film · 301 s | WebGL2 on real terrain; each shot lasts as long as its narration; sound effects are panned and distanced from the picture | [cases/opus55-gallery.md](cases/opus55-gallery.md) §6 |
| [389 community videos](https://github.com/yihui-dev/awesome-opus5-5-videos) and [a 962-work catalog](https://github.com/zhuyansen/awesome-opus-5.5-video) | Mixed | Prompt statistics, categories, curated picks | [cases/opus55-gallery.md](cases/opus55-gallery.md) |

</details>

## 28 styles, not one taste

AI-made videos drift toward one look: dark background, glow, glass cards, busy animated UI. Unless you say otherwise, that's where an agent goes.

So we studied famous work and wrote down 28 styles in [`styles/`](styles/), grouped into film titles, brand and launch, data and explainers, illustration and print, Chinese aesthetics, and retro tech. The sources include:
- **film and title design**: Saul Bass's titles, *Se7en*, *Blade Runner 2049*, Wes Anderson's symmetry, Wong Kar-wai's step-printing;
- **design**: the Swiss grid, 3Blue1Brown, New York Times data graphics, Otto Neurath's Isotype pictograms;
- **animation and print**: the halftone dots of *Spider-Verse*, 16-bit Super Nintendo pixel art;
- **Chinese aesthetics**: ink wash (水墨), Dunhuang murals, shadow puppetry and guochao.

Each style is written as instructions an agent can follow: colors and fonts, composition, how things move, how scenes change, what it sounds like, and which clichés to avoid.

**Every style comes with a real 5-second sample rendered by this repo**, each with its own code-written music. All 28 samples show exactly the same content, so the only difference is the style:

<a href="styles/"><img src="styles/gallery.jpg" width="820" alt="The 28 style samples, all showing the same content"></a>

Watch them back to back in [`styles/gallery.mp4`](styles/gallery.mp4). To use one:

```bash
bin/vh style list                                  # see all 28
bin/vh new promo launch-film --style cutout-jazz   # start a project from a style
```

We learn the *grammar* of these works; we don't copy them. No original characters, logos or shots, and the prompts never say "in the style of" a person. More in [styles/README.md](styles/README.md).

## How to ask for a video

You don't need a long brief. Say **what it's about, who it's for and where it goes**.

> **Science short:** 45 s vertical, why GPS has to account for relativity. For TikTok and Shorts, English narration, end on one concrete number.

> **Math explainer:** in the style of 3Blue1Brown, how a Fourier series builds a square wave piece by piece. 20 s, readable with the sound off.

> **Product film:** a 30 s launch film for my app in the ink-wash style. Real screenshots only, rhythmic music, sound effects on the key actions.

> **Paper talk:** turn the core method of `papers/main.tex` into a 3-minute explainer. Copy the paper's details exactly, walk through each equation, English narration with Chinese subtitles.

> **Music video:** a hand-drawn MV for `audio/song.mp3`. No lyrics on screen, the pictures tell the story, and every chorus goes bigger than the last.

> **Learn from someone else's film:** this video is good; break down how it was made, then make a similar one with this workbench.

> **Quick try:** a quick 15 s draft to see whether the cyber-glitch style suits my game trailer. Don't ask me anything.

## How it works

<p align="center"><img src="docs/assets/overview.en.svg" width="720" alt="OpenVideoHarness at a glance: a one-sentence request goes through type and effort selection, three human gates, sound-first code rendering and a self-review loop to a finished film; on the right, what the repository provides"></p>

1. **Pick the type.** From your one sentence, the agent looks up the routing table in [CLAUDE.md](CLAUDE.md), decides what kind of video this is, and reads that type's workflow.
2. **Gate ①, the outline.** It hands you an outline with two or three styles to pick from.
3. **Gate ②, the storyboard.** For each shot: what the viewer must understand, in what order, and for how long. Plus a preview sheet with one frame per shot.
4. **Sound first.** It makes the narration or music first and measures exactly when every line and beat lands, so the picture follows the sound.
5. **Write the code and check it.**
   - After each section, it lays the rendered frames out on a contact sheet, looks at them, and fixes whatever fails a 20-point checklist.
   - It measures the mix for dropouts, clicks and missed cues.
   - A reviewer who wasn't involved then scores the whole draft on 7 points; each one has to reach 8.
6. **Gate ③, the first draft.** You watch it, and it tells you the parts it likes least. If you can't say what's wrong, it makes two or three versions of one section for you to choose from.
7. **Wrap up.** It renders the final and writes what it learned back into the docs, so the next film starts better.


### You choose how hard it works

Not every film deserves the full treatment. One switch controls how much effort goes in, at three levels:

| | `quick` | `standard` (default) | `studio` |
|---|---|---|---|
| For | trying a direction, drafts, casual posts | most real videos | launch films, flagship pieces |
| Stops to ask you | never; it just renders | at the outline, storyboard and first draft | the same three, plus rendered style samples and a full-length animatic |
| Checks its own work | one contact sheet for the whole film | frames and sound, section by section | plus phone size, determinism and a full audio check |
| Outside reviewer | none | 1 round | at least 3 rounds, all 7 scores at 8+ |
| A 30 s film takes about | 10–30 min | 1–2 h | 3 h or more |

Just say "quick draft" or "make it studio quality" in your request, or start the project with `bin/vh new promo launch --effort studio`. The floor never drops at any level: every frame depends only on time, facts are copied exactly, no audio dropouts, flash-safe. `bin/vh effort` prints the full rules.

### Why this makes it reliable

A few hard rules (full version in [CLAUDE.md](CLAUDE.md)):

1. **Each frame depends only on time.** No random numbers, no system clock, so the same moment always produces the same frame. That's what allows parallel rendering, checking any single frame, and re-rendering after a one-line change.
2. **When there's sound, sound sets the timing.** The picture lines up with the audio, not the other way round.
3. **Storyboard before code.** Pacing is where AI video most often fails, so first decide what each shot must get across and for how long.
4. **Check every section.** Look at the frames, measure the sound, go through the checklist, fix what fails.
5. **Copy facts exactly.** Numbers, paper details and quotes come straight from the source; anything uncertain gets noted, not put on screen.

## 8 video types

| # | Type | Main engine | The gist | Doc |
|---|---|---|---|---|
| 01 | Math and science explainers | Manim | One color per idea; geometry before algebra | [01](video-types/01-math-science-explainer.md) |
| 02 | Science shorts (vertical or wide) | HyperFrames | Hook in the first second, something new every 3–5 s | [02](video-types/02-knowledge-short.md) |
| 03 | Product and launch films | HyperFrames | Real UI only, and show the product itself | [03](video-types/03-product-promo.md) |
| 04 | Lyric videos and MVs | p5.brush or HyperFrames | On the beat within 1 frame; each chorus bigger | [04](video-types/04-lyric-music-video.md) |
| 05 | Data stories | HyperFrames + SVG | One chart, one point; every number traceable | [05](video-types/05-data-story.md) |
| 06 | Paper and conference videos | Manim + HyperFrames | Paper details copied exactly; figures redrawn as vectors | [06](video-types/06-paper-explainer.md) |
| 07 | Hand-drawn, watercolor, whiteboard, paper-cut | p5.brush (built in) | Handmade and always moving; can write Chinese in stroke order | [07](video-types/07-hand-drawn.md) |
| 08 | Brutalist, meme and fast-cut edits | HyperFrames | Build a grid, then break it; every joke lands in 1 s | [08](video-types/08-brutalist-meme.md) |

A few more guides:
- **Realistic people or real physics:** bring in a generative video model, then layer code on top ([playbook/05](playbook/05-hybrid-genvideo.md)).
- **Effects, transitions, one-take 3D:** [playbook/08](playbook/08-vfx-and-motion-sources.md).
- **Breaking down someone else's film:** [playbook/07](playbook/07-reverse-engineer.md).
- **A story with rises and falls, or a film of 3 minutes or more:** [playbook/09](playbook/09-narrative.md) (structures, beat sheets, the tension curve, act breaks).
- **Posting to short-video platforms: the opening hook, title and cover:** [playbook/10](playbook/10-hooks-and-packaging.md).
- **Music with chapters, a theme you can hum, and real rises and falls:** [playbook/11](playbook/11-composition.md).

## Sound

The agent can't hear, so sound is built to be computed and measured:

| You want | Command | Notes |
|---|---|---|
| Voiceover (zh / en) | `bin/vh tts` | Local open-source **Qwen3-TTS** by default: offline, free; the first run downloads about 2 GB of model and about 750 MB of Python packages. 5 Chinese voices (including Beijing and Sichuan accents), 2 English. Interfaces ready for Alibaba Cloud, ElevenLabs and Gemini 3.8 Flash TTS (very expressive; direct the delivery in one sentence) |
| Narration with feeling and rhythm | `bin/vh tts … --beats` | Direct each line on its own, e.g. `[surprised question, fast, stress "one sentence"]`. With music, every line starts on a beat, and key lines can be pinned to a bar start or the drop. Default delivery per video type, frame-aligned tempos and mix settings are in [playbook/04](playbook/04-audio.md) |
| Bilingual subtitles | `bin/vh captions` | Write the script as `中文 \|\| English` and get Chinese, English and two-line subtitles, which can be packed as switchable tracks |
| Music | `bin/vh music` | Composed in code: the same score always gives the same music, plus the exact time of every beat for the picture to hit. Includes Chinese instruments (bells, guzheng, dizi, big drum) and changing time signatures. Using your own track? `bin/vh beats` finds its beats and drum hits. Chapters, a theme and dynamics: [playbook/11](playbook/11-composition.md) |
| Sound effects | `bin/vh sfx` | 15 original synthesized effects, each placed on the frame where its action happens; a sound on the left of the screen comes from the left |
| Mix | `bin/vh mix` | Music makes way for the voice; the whole mix is set to −14 LUFS without flattening a cinematic score |
| Mix check | `bin/vh qa` | Measures the finished mix for gaps, dropouts, pumping and clicks, and checks every cue lands within 1 frame |
| Songs | — | Generate in a web service like Suno and import; interfaces ready for ElevenLabs Music and local song models |

More in [playbook/04-audio.md](playbook/04-audio.md).

## What you end up with

- An **MP4** ready to post, optionally with Chinese and English subtitle tracks;
- A **project you can re-render**: change a line, get a new version, or switch it to another language or style;
- Every file from the process: brief, storyboard, review notes, fix-up log and asset sources;
- Contact sheets and keyframes for review, or to use as a cover.

## Commands `bin/vh`

| Command | What it does |
|---|---|
| `doctor` / `setup` | Check your setup / install dependencies and fetch references |
| `types` / `new <type> <name> [--style <style>] [--effort <level>]` | List the 8 types / start a new project |
| `effort [quick\|standard\|studio]` | What each effort level does |
| `style list` / `style <style>` / `style gallery` | Browse styles / render a sample / rebuild the overview |
| `tts` / `voices` / `captions` / `music` / `sfx` / `beats` | Voiceover (per-line direction, beat snapping, word alignment, two-speaker dialogue) / Gemini voice library and voice design / subtitles / music / sound effects / analyse outside music |
| `mix` / `qa` / `mux` | Mix / check the mix / put sound and subtitles on the video |
| `sheet` / `check` / `readcheck` / `gif` | Timestamped contact sheet / find black, frozen or silent stretches / is text on screen long enough to read / make a GIF for your README |
| `hf-init` / `install-skill` / `sync-agents` | Set up HyperFrames / register the skill / sync AGENTS.md |

## Requirements

| Needs | For | Required? |
|---|---|---|
| macOS or Linux, git | the basics | ✅ |
| Node.js ≥ 22, Google Chrome | rendering in the browser | ✅ |
| FFmpeg | encoding, mixing, checks | ✅ |
| Python 3 + [uv](https://github.com/astral-sh/uv) | sound tools (`bin/vh tts`, `beats`, `music`, `sfx`, `qa`), timestamped contact sheets, Manim (dependencies are fetched on first use into uv's cache, not into a global environment) | ✅ for sound and contact sheets |
| Apple Silicon | local Qwen3-TTS voiceover | For local voiceover |
| LaTeX | equations in Manim | For math explainers |

Rendering costs nothing. Only outside services, such as cloud voices or generative video, charge on their own terms, and API keys are always read from environment variables.

## Install and update

The one-line install is above. Options:

```bash
bash install.sh --dir ~/code/OpenVideoHarness   # install somewhere else
bash install.sh --no-refs                        # skip references for now (run references/fetch.sh later)
bash install.sh --no-skill                       # don't register the global skill
```

By hand:

```bash
git clone https://github.com/ZLHad/OpenVideoHarness.git && cd OpenVideoHarness
bin/vh setup            # engines, the style sample renderer, references
bin/vh install-skill    # optional: register in ~/.claude/skills and ~/.agents/skills
```

Just the skill (with the [skills CLI](https://github.com/vercel-labs/skills)):

```bash
npx skills add https://github.com/ZLHad/OpenVideoHarness --skill open-video-harness
```

The skill is only a pointer. The first time it's used, it asks before installing the full workbench.

To update: `git pull` in the repo, then `references/fetch.sh`.

### What gets downloaded

Sizes are approximate, measured on macOS (Apple Silicon); `du -sh` will show slightly different numbers.

| What | When | Where | Size |
|---|---|---|---|
| This repo, with the sample films and style samples | install | `~/OpenVideoHarness` | about 330 MB |
| Node packages of the hand-drawn engine and the style renderer | install | `node_modules` inside the repo | about 210 MB |
| 30 read-only reference repos | install, unless `--no-refs` | `references/repos/` | about 195 MB |
| Chrome for HyperFrames (`chrome-headless-shell`) | the first `hyperframes render` | `~/.cache/hyperframes` | about 100 MB to download, 200 MB on disk |
| Python packages for `bin/vh beats`, `music`, `sfx`, `qa` and `sheet` (librosa, numba, scipy …) | the first time you run each | uv's cache, `~/.cache/uv` | about 700 MB in all |
| `node_modules` of a HyperFrames project | each `bin/vh new short`, `promo`, `data` or `meme` | inside that project | about 140 MB each |
| The local Qwen3-TTS voice: `mlx-audio` and its packages, then the model | the first `bin/vh tts` with the default local provider (`qwen`); not needed with another provider | `~/.cache/uv` and `~/.cache/huggingface` | about 750 MB and 2 GB |

The installer writes inside the repo, plus (unless you pass `--no-skill`) two small skill files under `~/.claude/skills` and `~/.agents/skills`, and whatever npm keeps in its own cache. The rows from `chrome-headless-shell` down are fetched later, without asking and with little output: `bin/vh` runs `uv` quietly, and in a non-interactive shell (which is how an agent runs commands) the first render only shows "Checking browser…" while Chrome downloads. HyperFrames also keeps a small config and log in `~/.hyperframes`. All of this lives under your home directory, outside the repo, and uv's and Hugging Face's caches are shared with your other tools. On a slow or blocked connection (mainland China, for example) the 国内网络 section of [README.zh-CN.md](README.zh-CN.md#国内网络) has mirror settings for each row.

**Skipping the references.** They are other people's skills and film sources, cloned shallowly so that an agent can read them. Rendering doesn't depend on them. Install with `--no-refs`, and when a workflow doc points at a `references/repos/<name>/` you don't have, fetch just that one: `references/fetch.sh hyperframes` (about 30 MB). `references/fetch.sh` with no argument fetches all 30.

## What's in the repo

```
OpenVideoHarness/
├── CLAUDE.md · AGENTS.md     the agent's entry point: routing table, hard rules (identical)
├── install.sh                one-line installer
├── bin/vh · tools/           the command line and the scripts behind it
├── skills/                   the open-video-harness skill
├── video-types/              workflows for the 8 video types
├── playbook/                 shared know-how 00–11: pipeline, checks, motion, sound, effects, narrative, hooks and covers, composition
├── templates/                files each new project fills in: brief, storyboard, style, review, notes, lessons, checklist
├── styles/                   28 styles, each with a sample; _swatch/ renders the samples
├── cases/                    11 case studies + curated community work + a 3D long-form deep-dive
├── showcase/                 films made with this repo (source + final + process notes)
├── engines/                  the built-in hand-drawn engine + setup notes for the others
├── references/               fetch.sh (30 read-only reference repos) · open-source list · community skills
└── projects/                 your own video projects (not committed)
```

## How it relates to other projects

| Project | What it is | How this differs |
|---|---|---|
| [Code2Video](https://github.com/showlab/Code2Video) | A research pipeline for teaching videos in Manim | Takes the code-as-video idea to 8 video types, run by a general coding agent |
| [HyperFrames](https://github.com/heygen-com/hyperframes) / [Remotion](https://github.com/remotion-dev/skills) official skills | How to use one engine | Sits above the engines: choosing one, setting the process and the taste, checking the result, calling them when needed |
| [OpenMontage](https://github.com/calesthio/OpenMontage) | A full agent video production system | Lighter: mostly markdown, templates and one CLI that any coding agent can read and change |
| [guizang product-video skill](https://github.com/op7418/guizang-product-video-skill) | Software product update films | Covers 8 types, with three human gates, a style library and bilingual sound; its approach to music and sound effects inspired ours (our code is independent) |

## FAQ

**Do I have to use Claude?** No. `AGENTS.md` and `CLAUDE.md` are identical, so Codex or any agent that reads markdown works. The films here were made with Claude Opus 5.5.

**Does it cost money or need a GPU?** Not on the pure-code path. Rendering runs locally in Chrome or Manim, voiceover uses local Qwen3-TTS, and music and sound effects are generated in code.

**How good is the Chinese support?** The workflow docs are Chinese-first. Chinese subtitle layout, safe zones for vertical platforms, Chinese voiceover and bilingual subtitles are all handled, and the style library includes ink wash, Dunhuang, shadow puppetry and guochao.

**Can I avoid the dark-and-glowing look?** Yes. Name a style in your request (for example `ink-wash`), or say which film you'd like it to feel like. Even if you don't, the agent offers two or three very different styles at the outline stage.

**What about the reference repos' licenses?** `references/repos/` isn't part of this repo. `fetch.sh` pulls it from the original authors, for reading only. After fetching, the other repos' agent instruction files (`CLAUDE.md`, `AGENTS.md`, `.claude/` and so on) are renamed at every level, so an agent never mistakes someone else's rules for its own. Licenses for each are in [ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md); some have none or forbid commercial use, so check before reusing anything.

## Roadmap

- [ ] Type 9: editing and talking-head (cutting existing footage, adding subtitles and B-roll)
- [ ] Type 10: a proper workflow for 3D scenes (Three.js and shaders)
- [ ] Word-by-word highlighted subtitles (word-level forced alignment)
- [ ] English versions of the workflow docs

## Contributing

PRs welcome:
- a new video type in `video-types/`;
- a new style in `styles/`, with a sample rendered by this repo (see [styles/README.md](styles/README.md));
- a new case study in `cases/`;
- general lessons from your projects, added to `playbook/`;
- a film you made with it, with its brief, storyboard, notes and source, in `showcase/`.

## Acknowledgments

Thanks to these projects, researchers and creators:
- **Frameworks and tools:** HyperFrames, Remotion, Manim, p5.brush, Three.js, Qwen3-TTS, mlx-audio, FFmpeg;
- **Research:** Code2Video, Paper2Video, TheoremExplainAgent and others;
- **Open-source skills and cases:** ClaudeAnimationBase, PDoomVideo, functional-emotions-video, Battle-of-Austerlitz-Film, the guizang product-video skill, lemo-opuscar, product-film-skill, claude-animation-skill, OpenMontage, awesome-claude-video-skills, awesome-opus5-5-videos and others;
- **Community creators** who share their experiments, courses and prompts in public, including Movez and Eian.

The full list, with licenses and what each was used for, is in **[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)**.

This is an independent project, not affiliated with Anthropic, HeyGen, Remotion, Show Lab or Alibaba Cloud.

## License

Original content is [MIT](LICENSE). The bundled ClaudeAnimationBase is also MIT (© John Heibel). Reference repos keep their own licenses.

## Citation

```bibtex
@misc{openvideoharness2026,
  title        = {OpenVideoHarness: A Code-to-Video Harness for Coding Agents},
  author       = {ZLHad and contributors},
  year         = {2026},
  howpublished = {\url{https://github.com/ZLHad/OpenVideoHarness}}
}
```

## Support

If this project helped you make a film or saved you some time, you're welcome to buy the author a coffee ☕ (WeChat appreciation code).

<p align="center"><img src="docs/assets/wechat-reward.jpg" width="240" alt="WeChat appreciation code"></p>
