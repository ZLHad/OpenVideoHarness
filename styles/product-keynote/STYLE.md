# 产品发布片 · product-keynote

一句话：干净的无缝背景、微距的产品、精确的字、自信的长尾缓动。一个画面只讲一件事，物体先落稳，字再出来。适合硬件和软件的发布片、功能亮点，以及品牌的"新品"短片。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：暖白无缝台上只有一个英雄产品，WebGL2 片元着色器 ray-march 出来的圆角厚板（SDF）：机身是强调色的阳极氧化铝，正面是玻璃。灯光是解析的影棚环境：顶上一块大柔光箱在玻璃上留下一条高光带，背后两条轮廓光勾出倒角，另有接触阴影和淡淡的地面倒影；2×2 超采样。第 0 帧从一个倒角的微距特写开始，0.85 s 拉出全貌，同时设备在转台上转 18°（临界阻尼弹簧）。停稳 0.3 s 后标题上浮。屏幕依次点亮大纲 → 分镜 → 初版；初版是一个巨大的"1.0"，这是发布会里那个"唯一的大数字"。2.8 s 分镜卡的橙色描边闪一下，3.2 s 一道渲染光扫过初版卡；1.0–4.0 s 镜头慢推 7%，2.9–4.0 s 转台再转 12.6°。屏幕标签英文约 45 px、中文约 57 px。4.0 s 斜向光带扫过，转到暗舞台，同一台设备只剩轮廓光。实际字体：Avenir Next Demi Bold / Regular、PingFang SC。配乐 150 BPM：`pad` + `arp` 起，3.2–4.0 s 只留 `pad` 屏息，揭示处 `impact` 后进满编。拟音：落稳时一下极轻的 pop，卡片点亮用 tick，扫光和转场用 whoosh，片名出现时全片唯一一声 ding。拟音的落点写在 swatch.js 的 `FOLEY` 常量里，`events.json` 由它生成。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| Apple Watch 发布介绍片 | 2014 · Apple；旁白 Jony Ive；9 月 9 日发布会上播放 | 纯色无缝底上拍微距：表冠、表壳、材质一件一件单独展示；镜头慢转，物体从不"弹"；声音克制，旁白一句话对应一个画面 |
| iPhone 发布主题演讲（Macworld 2007） | 2007 · Apple，Steve Jobs 主讲 | 一张幻灯片只放一个想法：一个大词或一个数字占满画面，其余全部留白；揭示之前先停一下 |

核实：Apple Watch 介绍片的旁白与首映场合来自 Fortune 与 ABC News 的报道。Macworld 2007 主题演讲的日期（2007 年 1 月 9 日）和"一张幻灯片一个想法"的描述凭常识与观看印象写成，本次没能再联网检索，**未核实**。

**不照搬**：不用 Apple 的 logo、产品轮廓（手机、手表、耳机）、系统界面和 SF Pro 字体；不用 "One more thing"、"Designed by … in California" 这类句式；不用 Apple 网页上的精确灰值。

## 视觉语法

- **色板**：两种舞台，全片选一种为主，另一种只用在一个反转段落。

  | token | hex | 语义 |
  |---|---|---|
  | bg 亮舞台 | `#F4F4F1` | 暖白无缝底，地面到背景之间看不到接缝 |
  | 暗舞台 | `#0A0A0B`，中心抬到 `#17171A` | 反转段落，或暗色产品 |
  | fg 字 | `#161618`（亮舞台）/ `#F2F2EF`（暗舞台） | 标题、副标题 |
  | accent | `#E4572E` | 默认值；实际用产品自己的主色，只给"新东西"：新颜色、新按钮、那个数字 |
  | extra 次要字 | `#8A8A8E` | 副标题、规格 |
  | extra 发丝线 | `#D9D9DC` | 分隔线、尺寸标注 |

- **字体**：
  - 标题用 Avenir Next Demi Bold，96–140 px，字距 −0.02em；副标题用 Avenir Next Regular，44–56 px。只用这两个字重，层级靠字号和字重拉开；
  - 大数字用 Avenir Next Demi Bold，240–360 px，`tabular-nums`；
  - 规格小字用 Menlo，30 px；
  - 中文用 PingFang SC 的 Semibold / Regular；fallback 是 Helvetica Neue。
- **构图**：一个画面只有一个主角。产品占画面 60–80%，或者微距只拍一处细节（按钮、接缝、材质），占满画面。字不和产品抢：产品落稳之后才出现，放在产品上方 1/4 处，或左侧 5 栏以内。留白 ≥ 40%。
- **光**：大面积柔光，加左后、右后两条轮廓光；一道缓慢的扫光在 0.8–1.2 s 内扫过产品，亮度不超过字。地面有 15–25% 的柔和倒影。不加颗粒和纹理（texture: none）。

## 运动语法

帧数一律按 30 fps 计。

- **缓动**：
  - 进场 `cubic-bezier(0.25,1,0.5,1)`（easeOutQuart），18 帧；
  - 退场 `cubic-bezier(0.5,0,0.75,0)`，12 帧；
  - 镜头运动和产品旋转用 `cubic-bezier(0.76,0,0.24,1)`（easeInOutQuart），2–4 s；
  - 需要物理感时，用临界阻尼弹簧：stiffness 170、damping 26、mass 1（ζ≈1，不回弹）。

  全片没有 overshoot。
- **先物后字**：产品运动结束 → 停 0.3 s → 标题进场（上浮 16 px 并淡入）→ 副标题再晚 6 帧。
- **时长**：一个画面 2.5–4 s，每 2.5 s 一个新事件；数字画面停 ≥ 2.5 s；揭示前留 0.5 s 的"戏剧逗号"。
- **转场**（全片只用这 3 种）：
  - 卡拍硬切，切在 downbeat 上，前后两镜的产品运动方向一致；
  - 形状匹配切：圆角对圆角，边缘对边缘；
  - 扫光转场：一道光扫过去，光过之处就是下一镜。
- **镜头**：dolly（慢推 3–5%）加产品自转 10–25°。每镜只做一个动作，做完就停住；不手持，不甩镜。
- **文字动画**：stagger，按行出，行间隔 80 ms；中文按词组出。大数字"滚到位"：每一位从模糊的字形里依次锁定，从右往左，每位 2 帧。

## 声音语法

- **配乐**：极简电子或钢琴脉冲，112 BPM，E 大调。`bin/vh music` 的分段写法：
  - 开头只有 `pad` 和 `arp`，energy 0.3；
  - 中段加 `bass` 和 `hats`；
  - 揭示处一个 `impact`，然后进入完整的 `kick` + `clap`，energy 0.9；
  - 揭示前的半小节只留 `pad` 屏息。
- **音效**：
  - 0.4 s 的 `whoosh` 配扫光；
  - `tick` / `click` 配数字锁定和部件落位；
  - `ding` 全片只用一次，给最终的片名。

  所有音效调到同一个调（E 大调五声音阶），听起来是一个家族。
- **声画关系**：每个物体停稳的那一帧都有一个声音。有旁白时，一句话对应一个画面，音乐在旁白下压低 8–10 dB。

## 适合与不适合

- **适合**：03 产品宣传（硬件、App 功能、SaaS 发布）；05 数据故事里"一个大数字"的段落；品牌的年度发布。
- **不适合**：叙事性强、需要人物和情绪的短片；手作、复古、民俗品牌；信息密集的教程。
- **容易被误用成**：紫青光球加玻璃卡片的 AI 默认发布片；字和产品同时出现、互相抢；每个元素都弹一下。

## 禁止项

1. bounce、elastic、overshoot；卡片呼吸循环。
2. 紫青渐变、玻璃拟态、渐变字、发光光球。
3. 真实品牌的 logo、产品轮廓和 UI 截图（用户自己的产品除外）。
4. 同屏超过一个标题，或超过 8 个英文词；字比产品先动。
5. 纯 `#FFFFFF` / `#000000` 背景；扫光把字烧成白斑。
6. 编造规格数字（CLAUDE.md 硬规则 5）。

## Prompt 块

```text
Visual style: precise product keynote film. One idea per frame on a seamless stage, either warm white #F4F4F1 or near-black #0A0A0B lifted to #17171A at the centre. The product fills 60–80% of the frame, or a macro detail fills all of it; soft top light, two rim lights, a slow light sweep no brighter than the type, a faint floor reflection; no grain, no gradients behind type. Typography: one geometric-humanist sans in two weights (Avenir Next Demi Bold for headlines at 96–140 px with -0.02em tracking, Regular for sublines). Text appears only after the object has come to rest, 0.3 s later; one line per screen; one giant number for the key claim. Motion is confident: easeOutQuart entrances over 18 frames, easeInOutQuart turns of 10–25° over 2–4 s, critically damped springs, no overshoot or bounce, every move ending in a hold. Transitions: hard cuts on the downbeat with matched motion, shape match cuts, a light sweep that reveals the next shot. Sound: a 112 BPM E-major minimal electronic pulse, half a bar of held breath before the reveal, one sonic family of ticks and a single chime.
```

## 引擎做法

- 首选 HyperFrames。有 3D 产品时加一层 Three.js（`MeshPhysicalMaterial`、strip light 环境、Neutral tone mapping）；只有 UI 的产品用 DOM + GSAP。
- **产品**：用原创的程序化几何（圆角长方体、圆柱、胶囊）加材质。只有用户自己的产品才用真实模型或截图。不用 Three.js 也能做：样片用 `lib.shader` 写了一个 SDF ray-marcher（圆角挤出板、解析柔光箱 + 轮廓光环境、soft shadow、一次地面反射），1080p、2×2 超采样，一帧约 40 ms。屏幕内容先画在 2D canvas 上，当纹理传进 shader。不要用 2D 渐变去假装侧面，那样做出来像玩具或 U 盘。
- **扫光**：一条宽 0.3W 的柔边亮带，沿 30° 斜线在 0.8–1.2 s 内扫过（`mix-blend-mode: screen`，或在 shader 里按 uv 加亮）；亮度上限 = 字亮度 × 0.8。
- **先物后字**：在时间线上把标题的起点写成 `productSettle + 0.3`，不要手填时间。
- **弹簧**：Remotion 里用 `spring({stiffness: 170, damping: 26, mass: 1})`，或者自己写解析解；GSAP 用 `power4.out` 近似。
- **数字滚动**：`tabular-nums`，每一位用 `steps` 在 0–9 之间跳，按位依次锁定。

## 自查重点

- 字出现的那一帧，产品是否已经停稳（前后 3 帧的位移 < 1 px）。
- 1 fps 联系表：每个画面只有一个主角；强调色只出现在"新东西"上。
- 扫光 crop：扫过字面时，亮度不超过字本身。
- 所有进场都是 easeOutQuart 的长尾；逐帧看，没有回弹。
- 规格数字、功能名称与用户提供的资料逐字一致。

## 相关资源

- `references/repos/lemo-opuscar/styles/dark-keynote/STYLE.md`（界面即主角、扫光揭示、一个巨大的数字）和 `glass-product/STYLE.md`（strip light、慢爆炸图在重拍上合拢），LemoLab，CC BY 4.0。本文的"先物后字"和"一个声音家族"改写自它们。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 里的 Velvet Standard 与 Swiss Pulse；`references/repos/OpenMontage/styles/premium-minimalist.yaml`。
- `showcase/00-promo-launch-film/`（暗舞台、单一琥珀强调色的样板）、`video-types/03-product-promo.md`。
