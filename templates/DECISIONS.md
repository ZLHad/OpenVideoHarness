# DECISIONS：谁拍板，agent 替你定了什么

<!-- 导演模式的账本（CLAUDE.md"导演模式"）。上表每件事一行：谁拍板、定了没有、在哪看。
     下面记 agent 替人定的事，每条带理由和翻案的代价，人随时可以翻。人自己说的话记在 REVIEW.md，不记在这里。 -->

Director: {照抄 BRIEF 的 Director 行；没写就写"按 {effort} 的默认"}

| 决定 | 谁拍板 | 状态 | 在哪看 |
|---|---|---|---|
| outline 大纲 | {own / review / delegate} | {待定 / 已定（关卡 ①）} | {REVIEW.md 关卡 ①} |
| style 风格 | | | |
| character 主角 | | | |
| theme 主旋律 | | | |
| script 旁白稿 | | | |
| hook 钩子 | | | |
| storyboard 分镜 | | | |
| rhythm 剪辑节奏 | | | |
| voice 配音 | | | |
| packaging 标题封面 | | | |

## agent 替你定的

<!-- 一条一行：日期 · 决定 · 定了什么 — 理由 — 翻案：改哪里、要花多少 -->
- {YYYY-MM-DD} voice · {Qwen 女声 Serena，语速约 4.5 字/秒} — 理由：{…} — 翻案：重跑 `bin/vh tts`，约 5 分钟；每句起止会变，要重新锁时
