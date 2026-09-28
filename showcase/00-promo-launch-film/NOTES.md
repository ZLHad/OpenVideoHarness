# NOTES

## 待核实的事实
<!-- 拿不准的数字、引文、论文元数据写在这里，不要编进视频 -->
- [x] "8 video types" — `ls video-types/` = 01…08 — 已核实
- [x] "10 stages" — `playbook/01-pipeline.md` is now titled 十阶段流程（阶段 0–9）. (First cut said "9 stages" when the doc still said 九阶段 over a 10-row table; changed in the rebrand pass.)
- [x] "3 review gates" — CLAUDE.md step 5 was rewritten *during this session* from 两道关卡 (BRIEF, STORYBOARD) to 三道人工审阅关卡 (大纲 / 分镜 / 初版); the stat was changed from "2 approval gates" to "3 review gates" in the final. In the rebrand pass beat C was re-cut to what `bin/vh new` prints now (REVIEW.md + hf-init).
- [x] "20 taste checks" — `templates/TASTE_CHECKLIST.md` items 1–20 — 已核实
- [x] terminal stdout + tree — `bin/vh new promo launch-film` re-run on 2026-09-29 01:38 into a throwaway project (`projects/2026-09-29-launch-film`, deleted right after); stdout verbatim in `assets/vh-new-stdout.txt` (ANSI stripped), `ls -p` in `assets/vh-new-tree.txt`. That is why the screen says 2026-09-29 while this project folder is 2026-09-28.
- [x] routing table rows 01–05 — verbatim from CLAUDE.md (案例 column not shown; long cells ellipsized by the column width, text itself unchanged)
- [x] review beat — the contact sheet is `bin/vh sheet …/out/draft-v1.mp4 6 1` of draft v1 **as rebuilt after the rename** by `tools/draft-v1.sh`: the current film with the draft-v1 route table + 1.4× push (the real #3 flaw, same numbers as the original v1) and the draft-v1 stand-in review beat. Every other v1 bug had already been fixed, so it doesn't appear. Flagged overlay = draft-v1 frame 315 (tile "0:10.50"); fixed overlay = frame 315 of the current film. Both carry the tile label via `tools/label-tile.py`.
- [x] request text "a 15–20 s launch film for OpenVideoHarness" — paraphrase of the actual brief for this film (15–20 s, README hero launch film)

## 创作决策
- 2026-09-28 Engine: HyperFrames 0.8.82 — the router's first choice for `promo`; installed as a project devDependency (`npm i -D hyperframes@0.8.82`) so nothing is global.
- 2026-09-28 **Register: Linear/Vercel, not Apple** — OpenVideoHarness has no glossy product surface to macro-crop; its real UI *is* a terminal, a markdown routing table and a contact sheet. Those read natively as near-black + 1px hairlines + mono, so the register lets the real UI be the hero. Guard against the Linear/AI-slop collision (type doc 审美要点): one amber accent with a fixed meaning, no orbs/gradients/glass, no Inter (SF Pro via system-ui), real UI only.
- 2026-09-28 Accent #FFB224 ("tally light") means *what the harness is acting on now*: focus ring → routed row → FAIL flag → wordmark playhead. PASS is not green (would be a second saturated colour, #9).
- 2026-09-28 Fonts: Geist is not installed locally and downloading fonts was avoided; SF Pro via `system-ui`. Consequence: the composition renders as designed only on macOS.
- 2026-09-29 **Mono correction**: `ui-monospace, monospace` passed lint and looked mono in `hyperframes snapshot`, but in `hyperframes render` (chrome-headless-shell) it fell back to a *proportional* face — every "terminal" in the first cut was SF Pro. Now `@font-face { font-family: "LF Mono"; src: local("SF Mono"), local("SFMono-Regular"), local("Menlo-Regular"), local("Menlo") }` in each file that uses mono (lint accepts it, render honours it). Route columns re-fitted for true mono (path col 750 px, underline 560 px).
- 2026-09-28 Silent film: no SFX/music (brief). The type doc's "music-driven, SFX on key hits" and the 4:5 / 9:16 re-framed cuts are out of scope for a README hero.
- 2026-09-28 Text blocks: hook and problem are each on screen ~2.2–2.3 s, a little under the 2.5 s template rule; each is ≤ 6 words and read in ~1.2 s. Accepted to keep the mandated 7-beat structure inside 20 s.
- 2026-09-28 Clawd (ClaudeAnimationBase still) not used as a hero asset: the review beat is more honest with the film's own contact sheet. A ClaudeAnimationBase `--sheet` render was the stand-in sheet in draft v1 (kept as `assets/draft-v1/` so the v1 rebuild is faithful).
- 2026-09-29 Rebrand: wordmark "OpenVideoHarness" (16 chars) at the same 168 px; the lockup is now a left-aligned block centred on the frame (word ≈ 288–1613 px) instead of hanging off x = 144 — fixes the left weight. Beat C +0.3 s (more real stdout), hook −0.1 s, review −0.1 s, proof −0.1 s; total still 20.0 s.
- 2026-09-28 Cursor lives on the root timeline (not in a sub-composition) so it can carry the eye across the C→D→E seams; it is an `<img>` (assets/cursor.svg) because a nested `<svg>` in a root clip triggers lint `nested_structure_needs_subcomposition`.
- 2026-09-28 Word gaps: inter-span spaces inside the sub-composition templates were lost in render ("Onecatch:", "watchvideo."); replaced by `margin-right: .26em` on the word spans.

## 自评记录
<!-- 每渲染完一个场景，对照 TASTE_CHECKLIST 写一次。格式：[场景 · 时间段] 联系表路径，然后列出 FAIL 的条目和改法 -->

[snapshots · pre-render] out/check/snap1/contact-sheet-1.jpg (hyperframes snapshot, 11 frames)
- #19 FAIL: word spaces missing ("Onecatch:", "watchvideo.", "codingagents.") → margin on word spans, no whitespace text nodes
- #2 / #6 FAIL: hook type 112 px leaves the lower half dead; route table text 27–30 px, ~12 px in an 800 px GIF → hook 136 px; header + clipped camera viewport so panes can be pushed in without covering the label
- others PASS

[draft v1 · 0–20 s] sheet: out/check/sheet-v1.png · seams: out/check/seams_v1.png · cell crop: out/check/cell_v1_10.png
- #3 FAIL [D · 10.47 s]: the 1.4× push-in cuts the row text at the left edge and the answer itself reads "HyperFra…"; right third of the frame empty → reflow the table (narrower 用户想要 col with ellipsis, wider 首选引擎), push 1.15× centred so the request pill stays in view
- #14 FAIL [E→F seam · 14.90 s]: the first proof frame is an empty grid (columns start 0.08 s after the cut) → dead frame on the cut → first column on screen at the cut frame, stagger 0.06 s
- #19 FAIL [C · 4.80–4.87 s]: the cursor flashes in the top-left corner for 2 frames before its entry tween → cursor clip starts at 4.90, the frame its off-screen entry begins
- #19 FAIL [E · 11.1–14.9 s]: stand-in sheet (ClaudeAnimationBase demo) and "placeholder" NOTES text → this sheet + the #3 line above; fixed cell = v2 frame at 10.47 s
- others PASS (hook readable at 1 s; one accent; no bounce; every click causes its beat on the same frame; LEFT current holds; F→G inverse zoom keeps the shrinking sign)

[draft v2 · first cut] out/draft-v2.mp4 — route/proof/cursor fixes only (review beat still stand-in); used solely to take the "fixed" frame f 314 → assets/review-fixed.png
- #3 PASS at 10.47 s: full row visible, "HyperFrames" in full, request pill stays on screen

[snapshots · review beat] out/check/snap3, snap4
- #1 FAIL [E · 13.2 s]: at 1.75× the flagged cell (272 px → 476 px) is too small to read the flaw; the cursor tip sat on the routed row → push 3× and overlay the same frame at 960×540 (sheet → crop), click target moved to the cell's empty lower-right
- #19 FAIL [E]: leading spaces of the NOTES line collapsed ("#3 FAIL10.47s") → `white-space: pre` on the typed span
- contrast warning (check) on the 22 px sheet command label → #6c6c75 → #8b8b94
- others PASS

[first final · before the rename · 0–20 s] sheet: out/check/sheet-final.png (since overwritten by the rebrand final) · seams: out/check/seams_final.png · `hyperframes check`: 0 errors, 0 warnings (11 layout infos = intentional camera overflow / ellipsized table cells)
- every seam cuts mid-motion on both sides, LEFT current, no empty frame at any cut; F→G inverse zoom keeps the shrinking sign
- `bin/vh check`: 20.000 s, 1920×1080, 30 fps, no audio stream; blackdetect flags 0–0.4 s on the high-quality master (bare grid before the first word at 0.25 s — deliberate) and nothing on the web encode
- #5 note: hook/problem blocks ~2.2 s (see 创作决策); #6 note: routed row ≈ 35–37 px effective, labels 44 px, ≈ 15–18 px in the 800 px GIF — checked legible
- Determinism: two renders with 5 vs 3 workers are not bit-identical (315/600 decoded frames differ, min PSNR 48.9 dB, i.e. ±1 LSB; still 175/600 with `PRODUCER_BROWSER_GPU_MODE=software`). No visible difference; logic is seek-pure (set-then-to reveals, onUpdate text from the playhead). Recorded as a harness lesson: "identical" should mean perceptually identical unless a png-sequence is compared.
- Least happy with: (1) the hook/problem frames leave the lower half empty — type-only frames in a 16:9 poster layout; (2) the review crop is an upscaled thumbnail of a UI frame — legible, not crisp, in the GIF; (3) the lockup is left-weighted and could carry the quick-start command if the 8-word rule were relaxed.

[fresh-context reviewer · final candidate] general-purpose subagent given only sheet-final.png, seams_final.png, 8 key frames, TASTE_CHECKLIST.md, STORYBOARD.md (playbook/01 stage 7)
- #5 FAIL [E · 11.95–14.90]: NOTES line 10–11 words at 34 px (~16 px in the GIF), each state readable ~1 s → "#3 FAIL  10.47s  push-in cuts the row" / "✓ #3 PASS  10.47s  full row visible", 44 px
- #9 FAIL [E]: saturated blue/green/purple thumbnails in the embedded draft sheet (the v1 stand-in) = a second accent family → `filter: grayscale(1)` on the sheet; only the flagged cell (hi-res overlay) keeps colour
- #4 FAIL [E · 13.2–13.9]: real cursor on the flag box edge ~90 px from a cursor baked into the sheet → click point moved to (940, 690), below the routed row, ≥250 px from baked cursors
- reviewer note: seams dim both sides to ~30–40 % for 1–2 frames — that is cut-the-curve's fade trick (exit fade + entry ignition at .35), kept
- reviewer note (#19): CLAUDE.md now has three review gates → stat changed to "3 review gates"
- all three fixed in the final render; others PASS

[rebrand pass · 2026-09-29] out/check/fin_review.png, out/check/seams_rb.png, out/check/sheet-final.png, out/check/v1r_cell10.png
- (all pre-rebrand renders, snapshots and seam strips referenced above were deleted from `out/` after the rename so no image with the old name survives; the records stay here)
- #19 FAIL (found by comparing snapshot vs render): mono text rendered proportional in the MP4 → "LF Mono" @font-face (see 创作决策)
- #3 FAIL [D · 10.50 s, first rebrand draft]: row 01 path ellipsized once the path column was true mono → path col 730 → 750 px, 用户想要 col 560 → 540 px, underline 560 px
- #9 / #4 note [E]: the tool's tile labels are saturated yellow; the sheet is greyscaled, so they read grey; the flagged/fixed overlays got the same label in the same grey (tools/label-tile.py) — otherwise the flagged tile was the only one without a timestamp
- contrast warning (check) on the 22 px tree/terminal headers at 3.48:1 → #8b8b94
- seams: all six cuts mid-motion, no empty frame; `bin/vh check`: no black/freeze segments; `hyperframes check` passed 0/0
- others PASS

## 素材台账
| 文件 | 来源 | 许可 |
|---|---|---|
| assets/grain.png | generated here (seeded Gaussian noise, Python `random.Random(20260928)`) | original |
| assets/cursor.svg | arrow path geometry from the oversized-cursor house style (`references/repos/hyperframes/_upstream_claude/skills/oversized-cursor`), redrawn | Apache-2.0 reference; trivial shape |
| assets/vh-new-stdout.txt, vh-new-tree.txt | real output of `bin/vh new promo launch-film` (2026-09-29 01:38, throwaway project deleted) | original |
| assets/review-sheet.png | `bin/vh sheet` of the rebuilt draft v1 (`tools/draft-v1.sh`) | original |
| assets/review-flagged.png | frame 315 of the rebuilt draft v1 at 960×540 + tile label (`tools/label-tile.py`) | original |
| assets/review-fixed.png | frame 315 of the current film at 960×540 + tile label | original |
| assets/draft-v1/standin-sheet.jpg, standin-cell.png | `engines/ClaudeAnimationBase` demo (Clawd), `node render.mjs --sheet=…` — the draft-v1 stand-in; appears only as tiny greyscale thumbnails inside the review sheet | MIT, © John Heibel |
| fonts | SF Pro / SF Mono (or Menlo) / PingFang SC, macOS system fonts via `system-ui` and `local()`, not redistributed | Apple system fonts |
| GSAP 3.14.2 | jsDelivr CDN (HyperFrames template default) | GSAP standard license |
