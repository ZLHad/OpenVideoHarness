# Acknowledgments · 致谢

OpenVideoHarness is a harness, not a renderer. It runs on the libraries and tools in the first table, carries a few files adapted from other projects under their licences, and learned a great deal from the public work listed after that. Thank you to every author.

The main docs (the READMEs, `CLAUDE.md`, `playbook/`, `video-types/`, `styles/`, `recipes/`) describe how to make a film and name the tools they tell you to run. Works we only read and learned from are credited here, in one place, rather than in the text that teaches the method. Licence notices that a licence asks to keep next to the material stay next to it.

This project is independent. It is not affiliated with or endorsed by Anthropic, HeyGen, Remotion, Show Lab (NUS), Alibaba Cloud, or any author listed here. Product and model names (Claude, Claude Code, Codex, Seedance, etc.) belong to their owners.

## Licence scope

The MIT license in [LICENSE](LICENSE) covers this repository's original content. Third-party material keeps its own licence:

- `engines/ClaudeAnimationBase/` is (c) John Heibel, MIT License (`engines/ClaudeAnimationBase/LICENSE`).
- `engines/canvas-film/three/` carries three.js r186 and fflate, MIT ([`engines/canvas-film/three/NOTICE.md`](engines/canvas-film/three/NOTICE.md)).
- `recipes/`: files modified from seven projects, two under Apache-2.0 (video-shotcraft, HyperFrames) and five under MIT (lemo-opuscar, motion-graphics-skills, awesome-ai-motion, gl-transitions, MengTo/Skills). The upstream parts stay under their licence and our changes are MIT. Each file's 来源 section says what changed and its 许可 paragraph names the upstream files and commit; the licences are in `recipes/LICENSES/`, and [`recipes/NOTICE.md`](recipes/NOTICE.md) lists every file (Apache-2.0 §4).
- `components/`: `lib/motion.js` and `spring-scene/component.js` are modified from Barty-Bart's motion-graphics (MIT) ([`components/NOTICE.md`](components/NOTICE.md)).
- `tools/model3d/blender_qa.py` adapts MIT code from blender-skills and is GPL-3.0-or-later as it imports bpy ([`tools/model3d/NOTICE.md`](tools/model3d/NOTICE.md)). Every file that imports bpy is GPL-3.0-or-later, with an SPDX header ([`LICENSES/GPL-3.0-or-later.txt`](LICENSES/GPL-3.0-or-later.txt)).
- `tools/readcheck.py`, `tools/audio/instruments.py` and `tools/assets/footage.py` adapt MIT code from lemo-opuscar; each file's header names the upstream files.
- `playbook/12-ideation.md` §3 has a Chinese rewrite of parts of HyperFrames' `skills/hyperframes/references/pitch-round.md` (commit `a46095f`; Apache-2.0, Copyright 2026 HeyGen, Inc.). That part stays under Apache-2.0; the licence copy is `recipes/LICENSES/Apache-2.0-hyperframes.txt`.
- `styles/paper-desk-dossier/photo-half-dome.jpg` and `photo-merced-river.jpg` are Carleton E. Watkins's photographs *Half Dome* and *Merced River, Yosemite Valley, California* (ca. 1865), public domain, from the Library of Congress via Wikimedia Commons; reduced in size here. The preset's `STYLE.md` (素材) has the file pages.
- Some style presets in `styles/` rewrite parts of lemo-opuscar `STYLE.md` files taken while those were under CC BY 4.0; each such preset says so in its last section (see "Adapted into this repository" below).
- `docs/site/fonts/`: Inter Tight and JetBrains Mono, SIL Open Font License 1.1.
- Repositories that `references/fetch.sh` clones into `references/repos/` are not part of this distribution; each keeps its own licence.

## Libraries and tools we use · 用到的库和工具

These are installed, called or bundled by `bin/vh`, the engines and the docs' workflows. [`tools/modules.json`](tools/modules.json) is the full list with pinned versions and what each command needs; `bin/vh doctor` reports which are on this machine.

| Library or tool | Licence | What it does here |
|---|---|---|
| [HyperFrames](https://github.com/heygen-com/hyperframes) and its registry | Apache-2.0 | The HTML composition engine of short, promo, data and meme films; many motion numbers in `playbook/03-motion-design.md` come from its skills |
| [GSAP](https://gsap.com) | GSAP Standard "no charge" licence | The animation library of HyperFrames compositions |
| [Manim Community](https://www.manim.community), [ManimGX](https://github.com/academa-labs/manimgx) | MIT | Math, physics and paper explainers |
| [Remotion](https://www.remotion.dev) and [remotion-dev/skills](https://github.com/remotion-dev/skills) | Remotion License (the skills repository has no LICENSE file) | An alternative React route; its skills for captions and determinism |
| [ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase), [p5.js](https://p5js.org), [p5.brush](https://github.com/acamposuribe/p5.brush) | MIT | The bundled hand-drawn engine |
| [Three.js](https://threejs.org) | MIT | 3D in the canvas engine (r186 in `engines/canvas-film/three/`) and the intro film's world |
| [Blender](https://www.blender.org) | GPL-2.0-or-later | Path-traced shots, physics and real depth of field |
| [Chrome](https://www.google.com/chrome/) or Chromium, [Puppeteer](https://pptr.dev) | Google's terms or BSD-3-Clause; Apache-2.0 | Drawing pages into frames; web captures |
| [FFmpeg](https://ffmpeg.org) | LGPL-2.1-or-later (GPL builds) | Decoding, encoding, probing and mixing every picture and sound |
| [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) via [mlx-audio](https://github.com/Blaizzy/mlx-audio) | Apache-2.0, MIT | The default local voice of `bin/vh tts` |
| [mlx-whisper](https://github.com/ml-explore/mlx-examples), [whisper.cpp](https://github.com/ggml-org/whisper.cpp), [FunASR](https://github.com/modelscope/FunASR) | MIT | Word timing and transcripts |
| [NumPy](https://numpy.org), [SciPy](https://scipy.org), [librosa](https://librosa.org), [beat_this](https://github.com/CPJKU/beat_this), [Demucs](https://github.com/adefossez/demucs) | BSD-3-Clause, ISC, MIT | Code-composed music and sound effects, beat maps, vocal separation for lyric alignment |
| [Pillow](https://python-pillow.org), [jieba](https://github.com/fxsjy/jieba), [fontTools](https://github.com/fonttools/fonttools) | MIT-CMU, MIT | Contact sheets, Chinese word breaks, font checks |
| [uv](https://github.com/astral-sh/uv), [Node.js](https://nodejs.org), Python, git | MIT / Apache-2.0, MIT, PSF-2.0, GPL-2.0 | Running the tools and fetching the reference repos |
| [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense | Reading video sites for scouting and reference |
| [edge-tts](https://github.com/rany2/edge-tts), Gemini, MiniMax, ElevenLabs, DashScope | LGPL-3.0; the services' terms | Other voices and word timing |
| Internet Archive, Wikimedia Commons, NASA Image and Video Library, [Openverse](https://openverse.org) (incl. Freesound), [Poly Haven](https://polyhaven.com) | each item's own licence | Footage, sound effects and HDRIs found by `bin/vh footage`, `sfx` and `hdri` |
| [Make Me a Hanzi](https://github.com/skishore/makemeahanzi) by Shaunak Kishore | Arphic Public License, LGPL | Stroke-order data for Chinese characters (`video-types/07-hand-drawn.md`); not shipped or fetched: each project downloads the characters it needs and records them in its asset ledger |
| [Inter Tight](https://github.com/rsms/inter-tight), [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) | SIL OFL 1.1 | The homepage's two fonts, shipped in `docs/site/fonts/` |
| [Codex](https://github.com/openai/codex), [Claude Code](https://claude.com/claude-code) | Apache-2.0; Anthropic's terms | The agents that read `AGENTS.md` and `CLAUDE.md` |

## Shipped in this repository (vendored)

| Component | Author | Licence | Where / how it is used |
|---|---|---|---|
| [ClaudeAnimationBase](https://github.com/JohnHeibel/ClaudeAnimationBase) | John Heibel | MIT | `engines/ClaudeAnimationBase/`: the hand-painted p5.js + p5.brush engine, its `ANIMATION_GUIDE.md` and renderer. Copied unmodified; `.git` and build output are not included. Its "reads" timing method, review loop and failure list shaped `playbook/01-pipeline.md`, `playbook/02-verification.md` and `templates/TASTE_CHECKLIST.md`. |
| [three.js](https://github.com/mrdoob/three.js) 0.186.1 | three.js authors | MIT | `engines/canvas-film/three/build/` and `addons/`: the canvas engine's Three.js layer (`bin/vh new … --engine canvas-film --three` copies it into a project). The npm package's files, unmodified; each file's sha256 in `engines/canvas-film/three/NOTICE.md`, the licence in its `LICENSES/`. |
| [fflate](https://github.com/101arrowz/fflate) 0.8.2 | Arjun Barrett | MIT | `engines/canvas-film/three/addons/libs/fflate.module.js`, as three.js ships it: EXRLoader reads compressed EXRs with it. |
| [Inter Tight](https://github.com/rsms/inter-tight) | The Inter Project Authors | SIL OFL 1.1 | `docs/site/fonts/InterTight-latin.woff2`: the homepage's display face, cut to Latin and weights 500–700 from the google/fonts copy, so the page loads no web font from elsewhere. Licence: `docs/site/fonts/OFL-InterTight.txt`. |
| [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) | The JetBrains Mono Project Authors | SIL OFL 1.1 | `docs/site/fonts/JetBrainsMono-latin.woff2`: the homepage's mono face, cut to Latin and weights 400–500 the same way. Licence: `docs/site/fonts/OFL-JetBrainsMono.txt`. |

## Adapted into this repository · 改编进来的代码和文字

Text or code from these projects was rewritten into files here. The notice each licence asks for sits next to the material; this table says where.

| Project | Author | Licence | What came in, and where its notice is |
|---|---|---|---|
| [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | Vincent Wei (Wei Yihao) | Apache-2.0 | 17 recipes, 3 pacing skeletons and `recipes/sequences/README.md`, modified from its shot cards, demos and `promo-energy-arc` skeleton (commit `e2d8928`); picking shots by frontmatter along an energy arc is its idea. Text rewritten, parameters adjusted to this repo's rules, no code copied. `recipes/NOTICE.md`; the case study is `cases/promo-video-shotcraft.md` |
| [HyperFrames](https://github.com/heygen-com/hyperframes) skills | HeyGen | Apache-2.0 | The recipes `cut-the-curve`, `zoom-through` and `oversized-cursor` (from its `cut-the-curve` and `oversized-cursor` skills, commit `a46095f`); the divergence step in `playbook/12-ideation.md` §3 (four questions, a rough probability per idea, the silhouette check), from its pitch round. `recipes/NOTICE.md` |
| [motion-graphics-skills](https://github.com/charlie947/motion-graphics-skills) | Charlie Hills | MIT | Its sixteen effect recipes, rewritten into `recipes/`. `recipes/NOTICE.md` |
| [awesome-ai-motion](https://github.com/gongnyang/awesome-ai-motion) | gongnyang | MIT | Thirty of its type and interface cards, rewritten into `recipes/`, with their parameters and "avoid" rules. `recipes/NOTICE.md` |
| [gl-transitions](https://github.com/gl-transitions/gl-transitions) | gl-transitions contributors (Eke Péter, pschroen, mikolalysenko, gre) | MIT | Five shaders ported into `recipes/seam/gl-transition.md`, author comments kept. `recipes/NOTICE.md` |
| [MengTo/Skills](https://github.com/MengTo/Skills) | Meng To | MIT | Its browser-recording skill, rewritten as `recipes/interaction/browser-walkthrough.md`. `recipes/NOTICE.md` |
| [motion-graphics](https://github.com/Barty-Bart/motion-graphics) | Bart | MIT | The closed-form springs, presets and scene state in `components/lib/motion.js` and `components/spring-scene/component.js`. `components/NOTICE.md` |
| [blender-skills](https://github.com/EL4CTEO/blender-skills) | EL4CTEO | MIT | The z-fighting search and the inside-out and winding tests of `bin/vh model3d check --blender` (`tools/model3d/blender_qa.py`), from `skills/blender-asset-qa/scripts/qa_check.py` (commit `71d031d`). `tools/model3d/NOTICE.md` |
| [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) | LemoLab (Lemomo) | Its licence changed over time: before 2026-09-29 (`02dce5b`) the guides, `STYLE.md` files and films were CC BY 4.0; from then until 2026-11-12 the whole repository was MIT; since 2.0.0 (2026-11-12, `2ef41cc`) its Markdown (guides and every `STYLE.md`) is CC BY-NC 4.0, its demo films and stills CC BY 4.0 and its code MIT | Code, taken in the MIT period: the reading-time formula of `tools/readcheck.py` (from `core/render/readcheck.mjs` and `DIRECTOR.md` §7); parameter ranges and presets of the plucked strings in `tools/audio/instruments.py` (from `core/audio/pluck.py`); `tools/assets/footage.py` (from its countdown demo's `footage.py` and `grab.py`); the `live-countdown` skeleton in `recipes/sequences/` (from that style's `STYLE.md`). Each file's header or 许可 paragraph names the upstream. Style text, taken in the CC BY 4.0 period: fifteen presets rewrite parts of its `STYLE.md` files: `blueprint` and `clockwork-map` (from its `blueprint`), `bouncy-flat-2d` (`rubber-hose`), `crt-terminal` (`ascii-crt`), `cutout-jazz` (`spy-titles`), `editorial-data` (`dataviz`), `halftone-comic` (`halftone-dossier`), `ink-wash` (`ink-wash`), `product-keynote` (`dark-keynote`, `glass-product`), `risograph` (`risograph`), `shadow-puppet` (`shadow-puppet`), `silhouette-papercut` (`papercut-red`), `swiss-grid-type` (`swiss-motion`), `synthwave-outrun` (`cel-anime-80s`) and `watercolor-pastoral` (`watercolor`). Each preset's last section carries the CC BY 4.0 notice and says what changed |

## Works we learned from · 参考过的作品

We read these, took ideas from them, and wrote our own docs and code; nothing of theirs is copied here. Repositories marked *fetched* are cloned by `references/fetch.sh` into `references/repos/` (git-ignored) for reading, and each keeps its own licence; `references/community-skills.md` and `references/open-source.md` say what is in each and how far it may be reused.

### Repositories and skills

- [PDoomVideo](https://github.com/JohnHeibel/PDoomVideo) (John Heibel; no licence declared, read only; *fetched*): contract files plus parallel chapter subagents; something happens in every shot (`cases/mv-pdoom.md`).
- [functional-emotions-video](https://github.com/ledbetterljoshua/functional-emotions-video) (Joshua Ledbetter; MIT for the code, the song and audio excluded; *fetched*): a lyric-alignment pipeline, a reference chapter before the parallel ones, a GPU brushstroke renderer (`cases/mv-functional-emotions.md`).
- [hyperframes-launches](https://github.com/heygen-com/hyperframes-launches) (HeyGen; Apache-2.0, bundled assets per its NOTICE; *fetched*): 20 production launch films with their storyboards and design systems (`cases/promo-hyperframes-launches.md`).
- [Battle-of-Austerlitz-Film](https://github.com/WinterArc21/Battle-of-Austerlitz-Film) (Winter, @WinterArc2125; no licence declared, read only; *fetched*): a five-minute WebGL2 history film on real terrain, where measured narration drives every shot and sound cues take their distance and pan from the picture (`cases/opus55-gallery.md` §6).
- [abstract-algebra-promo](https://github.com/AnctyEnly453/abstract-algebra-promo) (AnctyEnly453; no LICENSE, so read, not fetched): a 4:23 Canvas/WebGL promo with a bar-based scene table, sub-frame motion blur that never crosses a cut, math data computed and asserted by script, and a bus-mixed procedural score (`cases/opus55-gallery.md` §7).
- [Code2Video](https://github.com/showlab/Code2Video) (Show Lab, NUS; MIT; prompts and src *fetched*): the anchor-grid critic, ScopeRefine and parallel sections; the "code as video" idea this project generalises (`cases/explainer-code2video.md`).
- [Paper2Video](https://github.com/showlab/Paper2Video) (Show Lab, NUS; MIT): several channels aligned in one talk, and letting a VLM pick among variants (`cases/paper-paper2video.md`).
- [3brown1blue](https://github.com/AmitSubhash/3brown1blue) (Amit Subhash; MIT; *fetched*): 3b1b-style and paper-explainer rules, Manim's common crashes.
- [awesome-claude-video-skills](https://github.com/zhuyansen/awesome-claude-video-skills) (Jason Zhu / Agent Skills Hub; CC0-1.0; *fetched*): a catalogue of 183 agent video skills with safety grades, the starting point of `references/community-skills.md`.
- [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) (LemoLab, Lemomo; licence by period, see the table above; *fetched*): its library of film styles, each a `STYLE.md` with a film made in code, was the main reference for the aesthetics of `styles/`. Besides the fifteen presets in the table above, `pixel-16bit` took from its `pixel-rpg` an indexed frame buffer with a lookup table, ×6 nearest neighbour, Bayer dithering, a mosaic with a palette swap at the peak, the dialogue box as subtitles, row gradients with 8-neighbour outlines and a silhouette mark per character; `isotype` its `pictogram-motion`'s key poses on the beat; `bubble-chart-story` its `dataviz`'s one dot as one character; `monumental-scifi` its `dark-keynote` sweep reveal and `glass-product` slow exploded view; `risograph` its demo film *Sunday Ride* (three plates kept in RGB channels, a plate added at each turn); the other presets were compared against its styles. `bin/vh image --provider codex` follows its `news-package` demo's `gen_image.py` (`codex exec` in a read-only sandbox, the picture found by a job token; the code is ours).
- [OpenMontage](https://github.com/calesthio/OpenMontage) (calesthio; AGPL-3.0; *fetched*): a full agentic production system, compared for scope; its six style YAMLs as a contrast for the style presets; terminal demos as synthetic screen recordings (`crt-terminal`); no code reused.
- [OpenFilm](https://github.com/openfilm/openfilm) ([openfilm.dev](https://openfilm.dev); MIT; *fetched*): a "video as a web page" toolkit with a Studio. The `window.film` contract fields in `engines/CONTRACT.md` follow its protocol 0.1 so our pages open in its Studio; its clock fallback, hold rules and ACP connection to local agents shaped the console proposals (`docs/proposals/01-client-and-workflow.md` takes it apart).
- [OpenChatCut](https://github.com/0xsline/OpenChatCut) (AGPL-3.0) and [AutoClip](https://github.com/zhouxiaoka/autoclip) (MIT): conversational editing that is local-first and talks to Codex and Claude Code; a Tauri shell around a local service, one pipeline for the CLI and the desktop, publish packages per platform (ideas for `docs/proposals/02-studio-client.md`).
- motioner: the `sync_check` idea in `tools/audio/qa.py`, confirming a near-pure-tone sound effect by cross-correlating it with the mix within ±250 ms.
- [video-talkcraft](https://github.com/Vincentwei1021/video-talkcraft) (Vincent Wei; PolyForm Noncommercial 1.0.0, so reference only; *fetched*): voiceover-driven explainer motion: cut the recording before timing it, and treat the script as the truth; its index of input types gave the recipes' `needs` filter.
- [guizang-product-video-skill](https://github.com/op7418/guizang-product-video-skill) (归藏, op7418; AGPL-3.0, `assets/fallback/` also BSL 1.1; *fetched*): product update films built from real product components. Its audio method (music from the user's track, then a local model, then a code-composed score; sound effects as their own event layer on the picture's landmarks; music making way for key effects) and its friendly README shaped ours; `tools/audio/music.py` and `sfx.py` were written from scratch.
- [Paper-Cut](https://github.com/aijiduonadegou/Paper-Cut) (Paper Cut contributors; MIT; *fetched*): Vox-style paper collage without video models.
- [gbro-collage-info](https://github.com/pyang5166/gbro-collage-info) (狗哥笔记, pyang5166; MIT, bundled GSAP and Mixkit sound effects under their own terms; *fetched*): halftone paper-collage information animation in plain HTML and GSAP, with the information kept in the top two thirds of a vertical frame.
- [vox-director](https://github.com/Alisa0808/vox-director) (Alisa Qian; MIT; *fetched*): an end-to-end Vox-style explainer pipeline.
- [claude-faceless-shorts-creator](https://github.com/hassancs91/claude-faceless-shorts-creator) (Hasan Aboul Hasan; MIT; *fetched*): a faceless Shorts factory with word-exact captions, a grammar of beats, and a hard loop where frame 0 is complete and the last frame equals the first.
- [data-animation-skills](https://github.com/iart-ai/data-animation-skills) (iart.ai; MIT; *fetched*): CSV to accurate animated charts: every value computed from the current frame, ranks and positions interpolated rather than jumping.
- [MathLens](https://github.com/shuyicc/MathLens) (shuyicc; CC BY-NC 4.0 per its README, no LICENSE file, read only; *fetched*): Chinese math-problem explainers with Manim: an animation fires when the narration reaches its keyword, and the geometry is checked before it is animated.
- [hand-drawn-explainer-video-nikola](https://github.com/hi-nikola/hand-drawn-explainer-video-nikola) (hi-nikola; Apache-2.0; *fetched*): Chinese hand-drawn knowledge explainers, and the difference between strokes being drawn and hand-drawn elements moving.
- [story-to-handdrawn-video](https://github.com/gnipbao/story-to-handdrawn-video) (gnipbao; MIT; *fetched*): Chinese stories as hand-drawn diary comics; its 327 styles shown on one scene side by side, and its brush recipes for Dunhuang mineral colours, guochao, ink wash and paper-cut collage.
- [remotion-guofeng-starter](https://github.com/AllenAI2014/remotion-guofeng-starter) (AllenAI2014; MIT for the code, demo assets excluded; *fetched*): Guofeng paper-cut animation from poems and idioms; vermilion used only as a touch, a seal as the accent, and the split between Song, Kai and a sans for different text (`guochao-festive`).
- [viral-video-decomposer](https://github.com/sharon-laicc/viral-video-decomposer) (sharon-laicc; MIT; *fetched*): shot-level breakdowns of reference videos (`playbook/07-reverse-engineer.md`).
- [Anatomy](https://github.com/wheresryan22/anatomy) (Ryan, wheresryan22; MIT): the grammar of `iso-anatomy`: the thing itself is the explanation, a concept built as a working machine of forty-odd convex parts, a 30° near-isometric view with four-step shading, one part lit at a time; its toolkit is what `iso-anatomy` suggests for full films.
- [anatomy-reveal](https://github.com/annnguyentt/anatomy-reveal-skill) (Ann Nguyen, annnguyentt; MIT, its `template/kit/` from Anatomy): the beats of a reveal film (tumble in, a 0.24 s whip to a detail, take apart and close), motion blur that adapts to how far a part moves, warm paper with `feTurbulence` fibres, models built to real millimetres.
- [motion-video-skill](https://github.com/bestagentkits/motion-video-skill) (bestagentkits): beat-synced motion graphics on HyperFrames.
- [paperview](https://github.com/ssrajadh/paperview) (ssrajadh): papers turned into explainer videos.
- [huashu-design](https://github.com/alchaincyf/huashu-design) and [huashu-art-motion](https://github.com/alchaincyf/huashu-art-motion) (花叔, alchaincyf; MIT): a page of six thumbnails to pick three from, a blind test in which forced metaphors and quotas lost, and an author's spec for adding a style (`references/community-skills.md` §8).
- [dream-loop](https://github.com/achimala/dream-loop) (achimala; MIT): a target picture and a critic in a loop (`playbook/target-critic.md`).
- wtt-code-animation-studio: comparing directions on the same key shot.
- [awesome-opus5-5-videos](https://github.com/yihui-dev/awesome-opus5-5-videos) (yihui-dev; no licence declared, read only; *fetched*): 389 community Opus 5.5 code videos with their prompts; the statistics and picks in `cases/opus55-gallery.md`, whose authors and post links live in this list.
- [awesome-opus-5.5-video](https://github.com/zhuyansen/awesome-opus-5.5-video) (Jason Zhu, @GoSailGlobal; no licence declared, read only; *fetched*): metadata for 962 Opus 5.5 works, the prompts on jasonzhu.ai (`cases/opus55-gallery.md` §5).
- [awesome-opus-5-5-videos](https://github.com/athemeroy/awesome-opus-5-5-videos) (athemeroy; CC BY 4.0, stills, linked posts and prompts excluded; *fetched*): seven production paths, a production brief template, a visual-effects fit guide, a colour-mode study, and the theme × style atlas behind the remark in `styles/README.md` that most community films look alike.
- [awesome-opus-5-5-video-prompts](https://github.com/X-RayLuan/awesome-opus-5-5-video-prompts) (X-RayLuan): the second-hand collection of prompts behind `cases/community-prompts.md`.
- [claude-animation-skill](https://github.com/buildwithhanif/claude-animation-skill) (Hanif, @hanifproduktif; MIT; *fetched*): hand-drawn 2D in Node canvas: the detail bible (base → texture → edge), a seek-order `verify` step, staged renders that never overwrite a good file after a failed encode.
- [product-film-skill](https://github.com/Rieranthony/product-film-skill) (Anthony Riera; MIT, Remotion under its own licence; *fetched*): product films from the product's own design system: `BRAND.md`, three style frames before building, a 240 fps master for motion blur, a muted loop plus poster, decode checks in `verify.py`.
- [procedural-film](https://github.com/kuhnhomeuk-cell/procedural-film) (Dean Kuhn; MIT; *fetched*): zero-asset JavaScript films: one agent per shot, waves of critics, a six-check gate that is green from the first stub scenes.
- [xilo-opus-video](https://github.com/Kianzzz/xilo-opus-video) (xilo, 周行; MIT): four spring registers (`playbook/03-motion-design.md` §1), the green-screen keying steps behind the pattern in `playbook/05-hybrid-genvideo.md`, and an environment check that launches a real headless browser and probes WebGL2, the model for `bin/vh doctor`'s WebGL probe and its OS-aware hints.
- The idea sources that awesome-ai-motion's cards credit in its `ATTRIBUTIONS.md`, carried over when its cards became recipes: GSAP's docs, react-bits, motion-primitives, motion.dev, Magic UI, textillate, Motion Canvas, Codrops, reelforge, animista, awesome-html-scrolline-deck, Hover, MDN's `pathLength`, and the research of Heer & Robertson and of Mayer on multimedia learning.

### Editing your own footage (type 09)

Ideas and rules only, read for `engines/editing.md` and `video-types/09-editing-talking-head.md`; not fetched.

- [video-use](https://github.com/browser-use/video-use) (browser-use; MIT): an edit list with a reason per cut, a phrase-line view of the transcript, twelve hard rules for cutting talking heads, and how many sound effects a short cut can carry.
- [open-edit](https://github.com/veedstudio/open-edit) (veedstudio; Apache-2.0): the gap rule of `speech-probe`, frame-snapped single-pass edits, refusing sources with a different colour or frame rate.
- [cut-motion](https://github.com/Endless1936/cut-motion) (Endless1936; Apache-2.0): the median of three thresholds for cut boundaries, asymmetric handles, picture-evidence classes, the Chinese subtitle segmentation standard.
- [kinocut](https://github.com/KyaniteLabs/kinocut) (KyaniteLabs; Apache-2.0): an approval hash over the edit list, six timeline-diff checks, a reframing planner that abstains.
- [timecode-agent](https://github.com/mupozg823/timecode-agent) (mupozg823; MIT): seam metrics, FCPXML and OTIO export, refusing variable frame rate.
- [ghost-editor](https://github.com/kurbaitaev/ghost-editor) (kurbaitaev; MIT): face-safe caption placement, measured platform overlay pixels, YuNet tracking, snap zoom.
- [mandarin-talking-head-rough-cut](https://github.com/m15851855393-boop/mandarin-talking-head-rough-cut) (m15851855393-boop; Apache-2.0): rules for Chinese fillers, retakes and false starts, the read-through test, energy-valley snapping (paraphrased, not copied).
- [proofcut](https://github.com/tydude001/proofcut) (tydude001; PolyForm Shield 1.0.0): the idea only, comparing a fresh transcript of the render with the edit list by word order.
- [SeeCut](https://github.com/YeJe-cpu/SeeCut) (YeJe-cpu; PolyForm Noncommercial 1.0.0): the idea only, pairwise judging with swapped positions, a function-to-treatment table, layered hand-off for JianYing.
- [clipify](https://github.com/louisedesadeleer/clipify) and [doza-assist](https://github.com/DozaVisuals/doza-assist) (louisedesadeleer, DozaVisuals; MIT): per-speaker crop expressions with a hard cut on speaker change; learning an editing style from the user's own cuts.
- diffusionstudio (MPL-2.0): contact sheets for scanning footage, sampled at 2 fps only when the picture settles, at most 2576×1456 and 12 cells a sheet.
- [auto-editor](https://github.com/WyattBlue/auto-editor) (WyattBlue; Unlicense): silence cutting and export to several editors.
- [capcut-cli](https://github.com/renezander030/capcut-cli) and [pyJianYingDraft](https://github.com/GuanYixuan/pyJianYingDraft) (renezander030, GuanYixuan; MIT, Apache-2.0): the CapCut and JianYing draft formats and the encryption since JianYing 6.0 (documentation only).
- [fcp-mcp-server](https://github.com/DareDev256/fcp-mcp-server) (DareDev256; MIT): rational frame rates in FCPXML.

### Films, posts and articles

Public experiments, films and generously shared prompts. We link to them; we do not redistribute their media. The case studies in `cases/` take some of them apart by content.

- **deckard (@slimer48484)**: the song *Claude-Pop – I'm Upping My P(Doom)*.
- **John Heibel (@other__reality, NotinReality)**: the *I'm Upping My P(doom)* MV, with PDoomVideo and ClaudeAnimationBase.
- **@pleometric**, **mexicat (@_mexicat)** and **YC (@yucheng)**: remixes and the Chinese version of that MV, which showed a code film can be forked.
- **@eudaemonea** and **Joshua Ledbetter**: *Functional Emotions*.
- **donald jewkes (@donaldjewkes)**: *Claude Pop* and its prompt: generated footage as a plate that JS redraws, an aesthetic stance given by counter-examples, lyrics at two sizes (`cases/mv-claude-pop.md`); @anabology posted the same prompt to the catalogue.
- **Andy L (@AndyL5cc)**: one-sentence science explainers (the *Interstellar* black hole, the Marquis Yi bells): one main visual through the film, a restrained documentary look (`cases/explainer-interstellar-blackhole.md`).
- **viggo (@decohack)**: the Applore promo, a one-line prompt with real material and a mascot as the hook; **@ajith_io** and **@achxvi**: the showreel prompt it grew from (`cases/promo-applore.md`).
- **@kimmonismus**, **@pradeepXkapoor**, **@jake11moran**, **@dotey (宝玉)**, **@AxtonLiu** and **@goodside**: prompts analysed in `cases/community-prompts.md` (specs down to the frame, a character bible, numeric camera language, "surprise me", Chinese constraints with a time budget, a format specific enough for one sentence).
- **Movez (@0xMovez)**: the 12-step course *How to build motion design studio with Opus 5.5*, through which the techniques of **Tony Dinh** (the TypingMind promo: a URL, real assets and music), **@oozn** (score and cuts on one 120 BPM grid) and **@mablesjoseph** (a watercolour film over 163 calls) reached `cases/community-prompts.md`; and a later post on keeping a character the same (a fixed description, a small fixed mark, variants as separate entries) and on a strict director scoring by dimension.
- **Eian (@EianLu)**: a Chinese guide to motion videos with Opus 5.5 (a drum event table; a code-composed score used as the script) and two films, *AGENT/0* and *华夏·五千年* (chapter titles written in true stroke order; characters reacting one after another); and the long article *Claude code/Codex+Seedance AI视频：从一个想法到成片的全流程* (X, 2026-11-05), whose way of stopping each mistake at the cheapest stage (first and last frames, a review before paying) is behind "模式 A 的落地" in `playbook/05-hybrid-genvideo.md`.
- **xilo (周行; @xilo2991)**: the long Chinese article 《零基础入门Opus5.5做视频》 (X, 2026-09-29), taking apart a green-screen character over a code-built scene.
- **@Cara_Mosquito**: a compositor's post on shot cards for image models: light and imperfection instead of "8K, hyper-realistic" (`playbook/05-hybrid-genvideo.md`).
- **Adrian Punk (@AdrianPunk115)**: the two-part *AI 视频运镜词典* (X, 2026-09-27/28), behind "给视频模型写运镜" in `playbook/05-hybrid-genvideo.md`: four layers, start → path → end → constraints, a trigger between two moves, at most two main moves per short clip.
- **Gorden Sun (@Gorden_Sun)**: a dance clip generated by Grok on a green screen and finished in code, the example behind the green-screen pattern in `playbook/05-hybrid-genvideo.md`.
- **Kevin Ngo (@kevin_t_ngo)**: a piano short (X) where a real-size instrument is the stage, the character's moves are the notes, and the light walks from candlelit night to window-lit morning (`tabletop-miniature`).
- **@majidmanzarpour**: the "pixel wizard" prompt (read from a transcript; the post itself would not open): a logical canvas scaled by the largest integer with smoothing off, about 24 colours, sprites about 24 × 32, poses quantised to 8–12 a second (`pixel-16bit`).
- Four world-journey shorts made with Claude Fable 5.2 in November 2026 (an art-history one-take, a little boat through eight worlds, a low flight over a flower field, an aurora ice arch), whose authors we did not record: `walk-in-world` is distilled from them (the material comes from the subject; one narrow palette, one light and one weather a stop; transitions that grow inside the world; one thing carried all the way).
- **Chris Tyson (The Agent Architect)**: a long article on Claude Code + Remotion in production (2026-08-24): audio sets the frame count; subpixel flicker, non-integer scaling, stale outputs, S3 403s (`cases/remotion-production.md`).
- The five films in `cases/oneshot-five.md`: 《你问 AI 一句话之后的 3 秒钟》 by 科了个喵 (a time magnifier with the slow-down written on screen), 《我眼中的你》 by 陈与小金 (a portrait from the machine's point of view), the Opus 5.5 self-introduction posted by 云野FLOW from a prompt by 光郡 (telling the method with the method), *FunTech Showreel 2026* by ハシモトタクマ (@tkm_hmng8; one mascot holding a tour of styles together; also the flash frames measured for `recipes/seam/flash-stitch.md`), and Mirage's *Tesseract for design* launch film (the product's workflow as the story).
- The authors of the works picked in `cases/opus55-gallery.md` §1–§5, whose posts the catalogue above links: @LinearUncle, @ParkerRex, @emollick, @AstroTheWizard, @x4b47x, @songkeys, @Michaelzsguo, @moritzkremb, @HowDevelop, @twoclipping, @Bilimfili1, @jake11moran, @pound75423, @doubleunplussed, @anabology, @samaote, @KamStudioLabs, @GroundControl, @RetropunkAI, @nummanali, @tak3sh8, @henkvaness, @eric_khun, @itsolelehmann, @koldo2k, @techhalla, @kloss_xyz, @Gdgtify, @alexalbert__, @zeezomb, @mdaman010, @FornYapayZeka, @AxtonLiu, @abhinayguptha, @op7418, @zacxbt, @gandamu_ml, @1stnoel_, @MengTo, @dangreenheck and @Aurelien_Gz ([clearwater](https://github.com/Aureliengmz/clearwater), MIT).
- **Jason Zhu (@GoSailGlobal)** and **余温 (@gkxspace)**: curating and surfacing the community skill list; Jason Zhu also for the 962-work catalogue.
- **yihui-dev** and **huangserva (@servasyy_ai)**: collecting and surfacing 389 Opus 5.5 videos with their prompts.

## Research

- Chen et al., **Code2Video: A Code-centric Paradigm for Educational Video Generation**, ICML 2026. [arXiv:2510.01174](https://arxiv.org/abs/2510.01174)
- Zhu et al., **Paper2Video: Automatic Video Generation from Scientific Papers**. [arXiv:2510.05096](https://arxiv.org/abs/2510.05096)
- Ku et al., **TheoremExplainAgent**, ACL 2025. [arXiv:2502.19400](https://arxiv.org/abs/2502.19400)
- Rammuni Silva et al., **Training and Agentic Inference Strategies for LLM-based Manim Animation Generation** (ManimTrainer / RITL). [arXiv:2604.18364](https://arxiv.org/abs/2604.18364)
- Jiang et al., **ManimAgent: Self-Evolving Multimodal Agents for Visual Education**. [arXiv:2606.30296](https://arxiv.org/abs/2606.30296)
- Lopez et al., **SGA: Plug&Play Geometric Verification for Educational Video Synthesis**. [arXiv:2607.18116](https://arxiv.org/abs/2607.18116)
- Huang et al., **Agentic Visual Generation: From Generative Models to Agentic Control** (survey). [arXiv:2609.06758](https://arxiv.org/abs/2609.06758)
- Zhang et al., **Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity**, ICML 2026. [arXiv:2510.01171](https://arxiv.org/abs/2510.01171) (the probability per idea in `playbook/12-ideation.md` §3)
- Heer & Robertson, **Animated Transitions in Statistical Data Graphics**, InfoVis 2007.
- Karplus & Strong, **Digital Synthesis of Plucked-String and Drum Timbres**, Computer Music Journal 7(2): 43–55, 1983. [doi:10.2307/3680062](https://doi.org/10.2307/3680062)
- Jaffe & Smith, **Extensions of the Karplus-Strong Plucked-String Algorithm**, Computer Music Journal 7(2): 56–69, 1983. [doi:10.2307/3680063](https://doi.org/10.2307/3680063)
- Smith, **Physical Modeling Using Digital Waveguides**, Computer Music Journal 16(4): 74–91, 1992. [doi:10.2307/3680470](https://doi.org/10.2307/3680470)
- Laakso, Välimäki, Karjalainen & Laine, **Splitting the Unit Delay: Tools for Fractional Delay Filter Design**, IEEE Signal Processing Magazine 13(1): 30–60, January 1996. [doi:10.1109/79.482137](https://doi.org/10.1109/79.482137)
- Välimäki, Huopaniemi, Karjalainen & Jánosy, **Physical Modeling of Plucked String Instruments with Application to Real-Time Sound Synthesis**, Journal of the Audio Engineering Society 44(5): 331–353, May 1996.
- Van Duyne & Smith, **A Simplified Approach to Modeling Dispersion Caused by Stiffness in Strings and Plates**, Proceedings of the International Computer Music Conference (ICMC), Århus, 1994, pp. 407–410.
- Karjalainen & Smith, **Body Modeling Techniques for String Instrument Synthesis**, Proceedings of the International Computer Music Conference (ICMC), Hong Kong, 1996, pp. 232–239.
- Tolonen, Välimäki & Karjalainen, **Modeling of Tension Modulation Nonlinearity in Plucked Strings**, IEEE Transactions on Speech and Audio Processing 8(3): 300–310, May 2000. [doi:10.1109/89.841212](https://doi.org/10.1109/89.841212)
- Bensa, Bilbao, Kronland-Martinet & Smith, **The Simulation of Piano String Vibration: From Physical Models to Finite Difference Schemes and Digital Waveguides**, Journal of the Acoustical Society of America 114(2): 1095–1107, 2003 (the b1 + b3·f² decay law of the loss filter). [doi:10.1121/1.1587146](https://doi.org/10.1121/1.1587146)
- EBU R95 (safe areas); Netflix Timed Text Style Guides (Chinese Simplified and English USA: line length and reading-speed limits used in `playbook/03-motion-design.md` and `tools/readcheck.py`).

Style references named in the style presets and prompts (3Blue1Brown, Kurzgesagt, Fireship, Vox, 回形针 PaperClip, Saul Bass and others) describe a look; no affiliation is implied.

If we missed or mis-credited your work, please open an issue. We will fix it.
