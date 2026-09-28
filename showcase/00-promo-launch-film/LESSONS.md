# LESSONS

<!-- 项目结束时写。M+ 是好用的做法，M− 是踩过的坑。通用条目已写进 showcase README 的 friction 一节，由维护者决定是否提升到 playbook/（本次不改共享文件）。 -->

## M+ 好用的做法
- **Review your own draft on screen** — 场景：产品片的"自查"功能拍 — 效果：beat E shows the film's real v1 contact sheet, the real `#3 FAIL` line from NOTES.md and the real v2 fix. No invented UI; the proof is the process itself.
- **Header + clipped camera viewport** — 场景：UI 拍需要推镜头但标签要一直可读 — 效果：label and a 1px rule stay fixed; the pane pushes in inside `clip-path: inset(241px 0 0 0)`. Pushes never cover the label.
- **Sheet → crop with a hi-res overlay** — 场景：推进到联系表某一格 — 效果：put the same frame at 960×540 exactly over the 272 px cell; at 3× it stays sharp. Honest (same frame), legible.
- **Timecode motif** — 场景：说明"每一帧是 t 的纯函数" — 效果：a lower-left `t 00.00  f 000` written from the playhead in an onUpdate proxy; also makes every contact-sheet cell self-labelled (the sheet told me exactly which frame, f 314, to fix).
- **Cursor on the root timeline** — 场景：跨场景的光标承载 — 效果：one `<img>` cursor tweened in index.html carries the eye across C→D→E seams; sub-compositions can't animate host elements.
- **Grain as a composition variable** — 场景：README GIF — 效果：`--variables '{"grain":0}'` render for the GIF (4.3 MB) while the MP4 keeps the grain; with grain the same GIF was 24 MB.
- **Web encode of the master** — 场景：交付 — 效果：`--quality high` master is 72 MB (grain); `ffmpeg -crf 23 -tune grain -preset slow -movflags +faststart` → 5.8 MB with no visible loss on UI text.

- **Rebuildable drafts for self-referential beats** — 场景：a beat that shows the film's own draft must survive a rename — 效果：`const DRAFT = "final"` in the two scenes the draft differs in, and `tools/draft-v1.sh` copies the source, flips it to "v1" and renders `out/draft-v1.mp4`. The flaw on screen stays the real one (same numbers) and can be regenerated after any rebrand.
- **Capture real CLI output from a throwaway run** — 场景：a terminal beat after the CLI changed — 效果：run the exact command into a scratch project, save stdout (ANSI stripped) and `ls -p` into `assets/`, delete the scratch project. The screen text then has a file to cite.

## M− 踩过的坑
- `bin/vh new` then `npx hyperframes init <dir>` — 原因：init refuses a non-empty directory — 解决：init into a temp sibling (`projects/_hf-launch-film`) and move its 6 files in.
- `hyperframes init` / `skills update` install skills **globally** (`skills add … --global --agent claude-code`) — 原因：engines/README says "在项目里安装" but the CLI passes `--global` — 解决：`HYPERFRAMES_SKIP_SKILLS=1`, read the skill docs from `references/repos/hyperframes/skills/` instead.
- Word spaces vanished inside `<template>` sub-compositions ("Onecatch:") — 原因：whitespace-only text nodes between inline-block spans were dropped — 解决：no spaces in markup, `margin-right: .26em` on each word span.
- Leading spaces in JS-set text collapsed — 解决：`white-space: pre` on that span.
- Cursor flashed at (0,0) for 2 frames — 原因：clip started before its `immediateRender:false` entry tween — 解决：clip `data-start` = the tween's start.
- Empty first frame after a cut — 原因：incoming scene revealed its first element 0.08 s after the cut — 解决：first element visible on the cut frame (mid-flight).
- A 1.4× push-in cropped the table and truncated the answer ("HyperFra…") — 解决：reflow columns for the push, 1.15×, keep the request in view. Always check the *pushed* end state in a still, not the establishing frame.
- `bin/vh sheet` changed mid-session to default to `./out/check/<name>-sheet-<HHMMSS>.png` relative to the cwd — running it from the repo root created `OpenVideoHarness/out/check/`. Pass the 4th `out` argument.
- Worker-count renders are not bit-identical (±1 LSB, PSNR ≥ 48.9 dB), even with software GPU.
- **`ui-monospace` is not mono in `hyperframes render`** — 现象：terminal/path text came out in a proportional face in every MP4, while `hyperframes snapshot` showed real mono and lint passed — 原因：chrome-headless-shell doesn't map `ui-monospace`/`monospace` the way the snapshot browser does — 解决：`@font-face { font-family: "LF Mono"; src: local("SF Mono"), local("SFMono-Regular"), local("Menlo-Regular"), local("Menlo") }` and use "LF Mono" first. Always check type in a frame pulled from the MP4, not only in snapshots.
- A longer wordmark (11 → 16 chars) flipped the lockup from "left-weighted" to "about to hit the right margin" at the same x — centre the block, keep it left-aligned inside.

## 可用命令
```bash
# project + engine (today: bin/vh new does hf-init itself; the first cut had to init by hand, see README)
bin/vh new promo launch-film
cd projects/<date>-launch-film && npm i -D hyperframes@0.8.82          # local CLI, nothing global
export HYPERFRAMES_SKIP_SKILLS=1 HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1

# verify
npx hyperframes lint && npx hyperframes check
npx hyperframes snapshot --at 5.2,6.9,10.5,13.4,16.2,19.5 --no-end -o out/check/snap
npx hyperframes render --quality draft --output out/draft.mp4             # ~10 s for 600 frames
bin/vh check out/draft.mp4 && bin/vh sheet out/draft.mp4 6 1               # timestamped tiles
ffmpeg -ss 7.7 -i out/draft.mp4 -t 0.6 -vf "fps=10,scale=320:-1,tile=6x1" -frames:v 1 out/check/seam.png

# beat 03 assets (the film's own draft v1)
tools/draft-v1.sh                                                          # → out/draft-v1.mp4
bin/vh sheet out/draft-v1.mp4 6 1 assets/review-sheet.png
ffmpeg -i out/draft-v1.mp4 -vf "select=eq(n\,315),scale=960:540" -frames:v 1 assets/review-flagged.png
ffmpeg -i out/draft.mp4    -vf "select=eq(n\,315),scale=960:540" -frames:v 1 assets/review-fixed.png
for n in flagged fixed; do uv run -q --with pillow python tools/label-tile.py assets/review-$n.png assets/review-$n.png 10.5; done

# final
npx hyperframes render --quality high --output out/final.mp4               # ~28 s, 72 MB master
ffmpeg -i out/final.mp4 -c:v libx264 -preset slow -crf 23 -tune grain -pix_fmt yuv420p -movflags +faststart -an out/final-web.mp4
npx hyperframes render --quality high --variables '{"grain":0}' --output out/final-nograin.mp4
bin/vh gif out/final-nograin.mp4 800 15                                    # 5.5 MB
ffmpeg -i out/final.mp4 -vf "select=eq(n\,570)" -frames:v 1 media/poster.png
```
