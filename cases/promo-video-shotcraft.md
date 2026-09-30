# 案例：video-shotcraft，电影感产品片的镜头配方库

**类型**：产品宣传片（web 和桌面产品）；镜头卡也能单独用在发布片、功能演示、品牌片里
**源码**：`references/repos/video-shotcraft/`（Apache-2.0，可复用，保留声明并注明修改；`assets/audio/` 里有来源待核的素材，音频不复用）
**来源**：[repo](https://github.com/Vincentwei1021/video-shotcraft)（2026-10-01：10,029⭐）、[在线 Gallery](https://vincentwei1021.github.io/video-shotcraft/)、作者 Vincent Wei（[@VincentWei93](https://x.com/VincentWei93)）。同系列的 video-talkcraft、anything2explainer 是 PolyForm Noncommercial，只读
**本仓库的落地**：[`recipes/`](../recipes/README.md) 镜头配方库和 [`recipes/sequences/`](../recipes/sequences/README.md) 全片骨架，大部分改写自这个仓库

## 做了什么

- 一个 Claude Code / Codex skill：指向一个前端项目，它用 Remotion 做出电影感的产品宣传片。画面用真实页面截图，镜头是 2.5D 运镜，切点卡在拍上，配电影系音效。
- 库里有：
  - 157 张镜头配方卡（214 个样式，分 10 类）；
  - 216 个 Remotion demo 动效（README 的数，是能拖进工作台的那些；`demos/` 下共 218 个 TSX）；
  - 一支 36.2 s 的模板片 Ink Press；
  - 27 条判例式审美准则、终检清单、卡点和声音方法论；
  - 交付后的浏览器工作台和剪映工程导出。

## 怎么做的

- **先判模式**：模板、自主自由创作、共同创作三选一。用户已经点名某张卡，就不再介绍模板（`SKILL.md`）。
- **八个阶段**（`references/pipeline.md`）：
  - 0 产品理解，敏感数据先虚构或冻结；
  - 1 视觉方向：tokens 从产品设计系统提取，做 2–3 张 HTML styleframe；
  - 2 功能到镜头映射，扫全部卡的 frontmatter；
  - 3 分镜：先套全片能量骨架，每镜先划 hold 预算，逐接缝选转场；
  - 4 放行后才采素材：2x 全页 + 元素 cutout + layout.json；
  - 5 逐镜头实现，每镜两个验收帧；
  - 6 声音：画面锁定后做，钉帧表写相对帧；
  - 7 独立终检：干净上下文的 subagent 按 P/F/V/S/B/D/A/Q 八块逐条查，每条附帧号。
- **一张卡的样子**：frontmatter 有一句话、适用、时长、能量；正文是意图、动效核心、参数表（典型值 + 调节手感）、已知坑、参考实现（到具体 TSX）。用卡要"三读"：先在索引里校验卡名，再读卡，最后读准确的 demo 源码。命门参数不得降档（`references/shots/`、`references/guided-free-creation.md` §5）。
- **审美准则的写法**：每条三要素，规则 + 用户原话 + 自检问句。编号 R/Q/S/C/P，只追加不重排；可以有意违反，但要写进项目说明（`references/aesthetic-rules.md`）。

## 为什么有效

- **素材真实而且锐利**：真实页面按 2x 截，推近时在布局层放大（CSS `zoom`），字不糊（准则 Q1、Q2）。
- **节奏有骨架也有预算**：
  - 低开品牌 → 单主角立传 → 功能段与呼吸字卡交替 → 发布会峰值收场；
  - 字标落定 ≥ 1 s，批量收尾 0.5 s，开场主体动作 ≥ 3 s；
  - 整画面冲击全片 ≤ 3 处（`references/sequences/promo-energy-arc.md`、准则 R1–R4）。
- **接缝经过设计**：六式转场按能量落差选，没有裸切（`references/shots/transition/shot-transitions.md`）。
- **克制写成了数字**：光效只给主角一次；切串、频闪、节拍泵全片 ≤ 1 次；重拳之后 hold 加倍。
- **声音是时间线级的资产**：电影系词汇（whoosh / impact / riser / sparkle），给动作配拟音，收尾固定 riser → impact → sparkle，防机枪三招，成片音轨偏移实测补偿（`references/sound-design.md`）。
- **验收查的是"是否按确认的方案做"**，不只查好不好看（`references/final-review.md`）。

## 需要知道的局限

- 157 张卡里 105 张自称"在灰阶或占位素材上调校，首次实战须回验"；有用户判例的只有模板片衍生的 10 张。
- 能量、时长是自由文本，机器筛不了，选卡只能把全部 frontmatter 读一遍。
- 实现只有 Remotion，公司使用可能要买它的许可。
- 交付环节带作者的推广话术（@作者、投稿展示页）。

## 本仓库借了什么、怎么改的

**已经落地**（本次改写，逐张在 frontmatter 的 `derived_from` 写明来源卡）：

- **镜头配方库** → [`recipes/`](../recipes/README.md)。把"一镜怎么动"写成带受控词表 frontmatter 的配方，和 `styles/` 正交：风格给皮，配方给骨。首批 24 张里有 17 张改写自它的卡：
  - 六式转场：`flash-cut`、`dark-tunnel`、`focus-handoff`、`black-card`、`whip-pan`、`portal-wipe`；
  - 节奏：`accelerando-cuts`、`paparazzi-flash`、`drop-blackout-slam`；
  - 模板片里有用户判例的镜头：`breath-title-card`、`brand-imprint-open`、`spotlight-hero`、`deal-to-grid`、`type-and-filter`、`row-embed`、`doc-self-writing`、`group-photo-launch`。

  其中 9 张（模板片里的 8 张加 `flash-cut`）标 `upstream-tested`，其余标 `tuned`。另外 7 张来自别处：HyperFrames 的 `cut-the-curve`、`zoom-through`、`oversized-cursor`，本仓库介绍片的 `decode-type`、`one-take-world-travel`、`gate-as-door`，以及一次拉片拆解出来的 `flash-stitch`。
- **全片骨架、hold 预算、转场选型、限额** → [`recipes/sequences/`](../recipes/sequences/README.md)：五条规则、按能量落差选接缝的表，以及 15 s、30 s、60 s 三条骨架（60 s 那条从它的 `promo-energy-arc` 重排而来）。
- **可以按条件筛** → `bin/vh recipes list --intent … --energy … --engine …` 和 `bin/vh recipes check`。它的能量、时长是自由文本，我们改成固定词表和数字范围，`check` 会校验 frontmatter、README 索引和草图语法。
- **分镜里写配方和验收帧** → `templates/STORYBOARD.md` 多了"配方""验收帧"两列（可选）。

**改写时和本仓库规则对齐的地方**：

- **读时规则更严**：它的字卡整张 1.8 s、字标停 1 s。本仓库要求没人念的画面文字从完整显示起至少停 max(2.5 s, 读时公式)（TASTE_CHECKLIST #5），所以改写后的字卡、黑场字卡、字标开场都变长了，骨架里的呼吸字卡也因此更少。
- **强调不用斜体**：它的字卡用"斜体 + 强调色"标重点词，本仓库改成字重或颜色（playbook/03 §4）。
- **blur 只在 canvas 里动画**：DOM 里不动画 `blur`（playbook/03 §4），压印和虚焦的模糊放到 canvas 层。
- **要读的小字至少 44 px**：它的副标、标语是 25–26 px 的装饰小字，改写后提到 1080p 的辅助文字下限。
- **急刹甩镜改成一条曲线**：它的 demo 把路程拆成两段各自 ease-out，交界处速度先掉到 0 再起步；我们改成一条速度连续的曲线。
- **实现换成引擎无关的草图**：每张配方附一段 `styles/_swatch` 场景接口的 canvas 草图，能用任何一个风格预设的 tokens 渲出来（见 `recipes/README.md`"草图怎么跑"）。

**还没做的**（箭头后是建议的落点）：

- 剩下的种子配方：`trailer-bumper`、`jump-cut-punch-in`、`speed-ramp-freeze`、`karaoke-fill`，以及模板片里的最后一张判例卡 `list-stack-press` → `recipes/`。其余的卡链到它的在线 Gallery。
- reviewer 加"计划一致性"块（产品目标、功能完整、分镜一致、数据安全、配方还原度），每条附帧号 → `playbook/02` 第 5 层。
- 需求到执行决策表 → `templates/BRIEF.md`、关卡 ①。
- 真实页面采集三件套（2x 全页 + 元素 cutout + layout.json）和推近清晰度 → `video-types/03-product-promo.md` 工作流 1。
- 有效字高按最终像素量，文字分"纹理"和"要读"两态 → `playbook/03` §4。
- 判例式的 LESSONS 格式（规则 + 原话 + 自检问句）→ `templates/LESSONS.md`。
- 成片音轨偏移实测（AAC priming）→ `playbook/04`、`bin/vh qa`。

## 不照搬什么

- **Remotion 栈和 Ink Press 模板**：我们的产品片首选 HyperFrames；模板截图来自一个内部工具。只读它的 TSX 取参数，改写成引擎无关的配方。
- **`assets/audio/`**：5 个音效和 1 首 BGM 来源无法反查（`assets/audio/ATTRIBUTION.md`）。我们有程序化音效和代码作曲，只借它的音效词汇和钉帧纪律。
- **"宁慢勿快""tech-house 当默认 BGM"当成通用规则**：两者都有片种前提，只放进产品片。
- **整库导入 157 张卡**：105 张没经过实战，又偏 web UI，全读下来上下文太贵。精选改写，其余链到它的在线 Gallery。
- **交付收尾的推广环节**、**工作台和剪映导出**：前者不是工作台该做的事，后者体量大，属于以后的客户端方向。

## 先读哪几个文件

1. `SKILL.md`：模式判断和九条核心理念。
2. `references/pipeline.md`：八个阶段和每阶段的"常见坑"。
3. `references/aesthetic-rules.md`：判例式准则的写法。
4. `references/sequences/promo-energy-arc.md`：全片骨架。
5. 三张代表卡：`references/shots/opening/spotlight-hero-card.md`、`references/shots/transition/shot-transitions.md`、`references/shots/rhythm/beat-cut-moves.md`。
6. `references/final-review.md`：终检清单。
7. `references/music-beat-sync.md`：外来音乐的网格验收和渲后回测。

读完这些，再对照本仓库改写后的 [`recipes/seam/`](../recipes/seam/) 和 [`recipes/sequences/product-film-60s.md`](../recipes/sequences/product-film-60s.md)，能看出哪些数照搬、哪些按本仓库的规则改了。

## 许可

- 仓库是 Apache-2.0（Copyright 2026 Wei Yihao），在用到的 commit `e2d8928` 没有 NOTICE 文件。改编它的文件要按第 4 条处理：带上许可原文，标明改过、改自哪里，保留版权行，并在 `ACKNOWLEDGMENTS.md` 登记。本仓库 `recipes/` 里改编自它的 21 个文件都这样做了：没有复制代码，文字重写；许可原文在 `recipes/LICENSES/`，每个文件的"来源"一节写明改动、上游文件和 commit，总表在 `recipes/NOTICE.md`。
- 音频按 `assets/audio/ATTRIBUTION.md` 逐条核对，来源待核的不用。
- 卡片研究自公开的商业片和 X 个人作品，作者只取手法、全部重写（`references/shots/ATTRIBUTION.md`，逐卡列了 48 张，本库改编的卡都不在其中），并写明"公开发布不等于授予复刻许可"。转场卡注明 B、C 两式来自对 Linear 发布片的抽帧逆向，这句话在 `dark-tunnel`、`focus-handoff` 的"来源"里保留了。我们借用时守同一条边界：只学时序、编排、缓动，不复刻具体的画面、文案和品牌。
