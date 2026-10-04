# STORYBOARD

<!-- 写代码前完成，给用户确认（关卡 2）。格式综合自 ClaudeAnimationBase 与 PDoom 的 STORYBOARD。
     reads = 观众必须依次看懂的信息，每条标起止时间；每条都要有被找到、被看懂、被消化的时间，重要的两条不重叠。
     reads 放不下就加长镜头或删掉一条 read，不要硬挤。 -->

Logline: {一句话：谁想要什么，遇到什么，于是怎样}
World: {场景设定；5–7 色的调色板；光线；颜色在全片中怎样变化（例如冷夜 → 暖晨）}
Motif: {反复出现、最后有回应的东西}
Arc: {主角（或核心概念）情绪/理解的关键节点，覆盖全片}
Audio: {旁白/歌曲/音乐；BPM 与 offset；timeline.json 路径}
Animatic: {out/animatic.mp4 · draft 画质的灰盒 · 真实 / 占位音频；不做就写"无"。节奏要紧的片子在关卡 ② 前做，见 playbook/01}

## Shots

<!-- 配方、验收帧两列可选（quick 可以不填）：
     配方 = recipes/ 里的 id（多式的写 id · 变体），按意图和能量挑：bin/vh recipes list --intent … --energy …；没有合适的写"自创：理由"。
     验收帧 = 这一镜要逐帧看的 1–2 个片内帧号：峰值帧和落定帧，由配方 frontmatter 的 qa 加上本镜起点换算。
     转场出 = 接缝配方的 id（flash-cut、whip-pan …），或 brush wipe / match cut 这类写法。全片节奏先套 recipes/sequences/ 的骨架。 -->

| # | 时间 | 旁白 / 歌词 | 画面：看到什么 · 发生的事件 · 反应 · 镜头运动 | 焦点 | 配方 | 验收帧 | 转场出 |
|---|---|---|---|---|---|---|---|
| A | 0.0–3.6 | {…} | {…} | {…} | {spotlight-hero / 自创：理由} | {f… 峰值 · f… 落定} | {flash-cut / match cut / cut on action / camera carry / iris …} |

### A 的 reads
| 时间 | read | 为什么这样定时 |
|---|---|---|
| 0.2–1.0 | {第一件要看懂的事} | {视线怎么被引到这里} |
| 1.0–2.2 | {…} | {…} |

<!-- 每个镜头重复一节 reads -->

## 对照检查
- [ ] 每个镜头都有事件（首帧和末帧之间有东西变了）
- [ ] 每条 read 在下一条开始前有时间落地（有 animatic 时，按它的实际速度逐镜读过一遍）
- [ ] 每个接缝都有转场，开头和结尾也有
- [ ] 文字用量符合类型文档的规则；每条要读的字停够快读一遍，舒服的时长按 BRIEF 的 `Pace`；跟着旁白念的字幕，在合成里标 `data-read="subtitle"`，镜头在走时的短标签标 `data-read="label"`，和全片节奏不一样的一段标 `data-pace`（见 playbook/03 §2）
- [ ] 结尾与开头呼应（同一地点、姿势或母题，但有变化）
- [ ] 全片只用 2–3 种转场、一个主运动方向
- [ ] 用了配方的镜头：读过配方全文和它的实现，★ 参数没有降档；全片的 max_per_film、conflicts、整画面冲击 ≤ 3 处都对过（recipes/sequences/README.md）
