# 气泡图现场讲 · bubble-chart-story

一句话：一张气泡散点图就是整个舞台。横轴收入（对数）、纵轴寿命、气泡面积是人口、颜色是地区，年份以巨大的淡色数字铺在背景里滚动；讲述者一边说，一边让时间快进、放慢、停住、倒回，指着某一个气泡讲它的故事。适合"一个群体随时间怎么变"的叙事：发展、健康、城市、行业、公司群。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：0.1 s 坐标轴射出、巨大的年份水印滚入、44 个虚构实体的气泡在 1950 年弹出，时间立刻开跑（30 年/秒），缓停在 2000 年；其余气泡降到 20%，一根带黄铜头的木指示棒依次点三个带轨迹的气泡（大纲、分镜、初版，中文标签 58 px）；2.5–3.0 s 签名倒带：年份倒着滚回 1985，轨迹回缩；3.0 s 停在 1985，指示棒点两下；3.5 s 时间再冲到 2020；4.0–4.6 s 结尾：时间倒回 2000，同时坐标轴重新定标（放大到故事所在的区间），主标题退场，结束标题出现。刻度字 36 px、轴标题 32 px。数据是示意的，画面写明。实际字体：Avenir Next（年份水印用 Ultra Light）、PingFang SC。配乐 120 BPM、G 大调，`meters` 让 2.0、2.5、3.0、3.5、4.0 s 都是小节线；乐队演的就是年份计数器，音符时间由 swatch.js 的同一张 `KEYS` 缓动表反解：时间在走时，马林巴在每个 5 年刻度上敲一下（0.1 s 起每 1/6 s 一个，逢十年低、逢五年高，一低一高地弹跳），沙锤跟着同一个时钟，每过一个十年拨弦拨一下低音，0.2 s 气泡弹出时拨弦先进来；1995→2000 缓停时一年一个音，越来越慢，2.08 s 停在 2000 上响一个 Em 和弦；指示棒每点一个气泡，拨弦点一个高音；两次倒带时马林巴顺着缓动曲线往下落，冲向 2020 时 5 年刻度越来越密、越爬越高；4.6 s 结束标题出现时一记 G 大调和弦收尾。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《200 Countries, 200 Years, 4 Minutes》（BBC Four 纪录片《The Joy of Stats》中的一段） | 2010 · Hans Rosling；Wingspan Productions 制作，导演 Dan Hillman | 一张图讲 200 年：年份作背景大字；时间不是匀速走，讲到关键年份就放慢、停住；讲述者和数据同框，用手势"推"着气泡走 |
| TED 演讲《The best stats you've ever seen》 | 2006 · Hans Rosling | 先说出观众的错误直觉，再让气泡动起来推翻它；解说像体育解说一样实时、口语、兴奋 |
| Trendalyzer / Gapminder 气泡图 | 2005 起 · Gapminder 基金会（Ola Rosling、Anna Rosling Rönnlund、Hans Rosling）；2007 年被 Google 收购 | 编码约定：收入用对数轴并按倍数标刻度，气泡面积 ∝ 人口，按地区上色，选中的实体留下轨迹 |

核实：《The Joy of Stats》的播出时间、制作公司和导演来自 Wingspan 官网与 Letterboxd；TED 演讲时间、Gapminder 成立时间与创始人、Trendalyzer 被收购的年份来自 Wikipedia 与 Gapminder 官网。Gapminder 的数据以 CC BY 4.0 开放，可以用，署名 "Free data from www.gapminder.org"（来自 gapminder.org/data）。

**不照搬**：不用 Gapminder 工具的界面、logo 和四色地区配色原值；不复刻 BBC 片段里的实拍 AR 合成镜头和讲述者形象；数据自己取、自己标出处。

## 视觉语法

- **色板**：浅底，四个地区色，淡色年份水印。

  | token | hex | 语义 |
  |---|---|---|
  | bg 纸 | `#F7F5F0` | 背景 |
  | fg 墨 | `#23211E` | 轴标题、标签、选中气泡的描边环、指示棒 |
  | 地区 A 朱红 | `#E4572E` | accent，也是默认"主角地区" |
  | 地区 B 青 | `#29A0B1` | |
  | 地区 C 橄榄绿 | `#8FB339` | |
  | 地区 D 琥珀 | `#F2B134` | |
  | 年份水印 | `#E6E1D6` | 背景大字，只比底色深一点 |
  | 轴与刻度 | `#8A857C` | 轴线、刻度字、来源行 |

  气泡填充 85% 不透明、1.5 px 白描边，重叠时分得开。聚焦时其余气泡降到 20%，选中的保持 100% 并加 3 px 墨环。
- **字体**：Avenir Next 一个家族：年份水印 Ultra Light，轴标题和标签 Demi Bold，数字 `tabular-nums`。中文用 PingFang SC。
- **构图**：图表区约占画面宽 80%、高 70%；年份水印居中偏下、铺在气泡后面，高约画面的 35–40%；轴标题写成人话，单位写清（"人均收入，美元，经通胀和购买力调整，对数刻度"）；对数刻度按倍数标（500、1 000、2 000、4 000……），不标 10 的整次幂以外的零碎数。标签贴着气泡，离气泡不超过一格。
- **讲述者的化身**：做不了真人出镜时，用一根指示棒代表讲述者：墨色 4 px 细线从画面边缘伸进来，末端一个小圆点，指着正在讲的那个气泡，跟着气泡走。
- **质感**：无。

## 运动语法

帧数按 30 fps 计。

- **缓动只作用在"时间映射"上，不作用在数据上**：年份 `year(t)` 是分段函数，快进时约 8–12 年/秒；到关键年份前用 easeOutCubic 减速 0.5 s，停 2–3 s，再用 easeInCubic 起步。气泡位置由 `year` 对数据线性插值得到（收入在对数空间插值），自己不再缓动。
- **倒带**（签名动作之一）：讲到"等一等，回到那一年"时，年份倒着走，气泡沿轨迹退回去。
- **标签与指示棒**：入场 easeOutCubic 12 帧，出场 easeInCubic 9 帧。
- **时长**：停在关键年份 ≥ 2 s；每 3 s 左右一个讲述节拍（一个新气泡被点名、一次停顿、一次倒带）。
- **转场**（只用这 3 种）：
  - 时间拖动（time-scrub）：年份水印滚动，数据从一年滑到另一年；
  - 换轴（axis-swap）：轴标题翻面 → 刻度重新定标 → 气泡移动，分三段约 1 s；
  - 聚焦（focus-dim）：其余气泡变暗，选中的留下轨迹。
- **镜头**：固定。需要看局部时改坐标轴范围（重新定标），不放大画面，所以气泡大小不变。
- **文字动画**：标签逐词（stagger）淡入；年份水印用里程表式滚动，每一位数字单独滚。

## 声音语法

- **配乐**：旁白是主角，但音乐要"演"时间。G 大调，120 BPM（30 fps 下一拍 15 帧），轻快、俏皮，像统计科普片。签名是马林巴（`marimba`，短止音）的弹跳音型，它按年份计数器走：时间快进时每过一个固定的年数敲一下，缓停时跟着慢下来，停住时只剩一个响着的和弦，倒带时顺着缓动曲线往下落，冲刺时越来越密、越爬越高。沙锤（`shaker`）跟同一个时钟；拨弦（`pizzicato`）逢十年拨一下低音，也给指示棒的每一下点击配一个高音。小房间混响，不用鼓组。停住时和弦一直响着，不能声画同时停死。
- **音效**：快进时每过一年一声很轻的 `tick`（最多 16 次/秒），停住一声 `click`，点名一个气泡一声轻 `pop`。
- **声画关系**：年份停在关键年份的那一帧，旁白正好念出那个年份（cue 词触发）；讲述口吻口语、第一人称、实时（"看这里，它开始往右上跑了"）。
- **样片拟音**：`events.json` 20 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs <slug>` 生成，落点全部引用动作所用的同一张时间表，声像取发声物体的屏幕 x（`(2x/W − 1)·0.7`），按 `profile=swatch` 混在配乐下：坐标轴 `whoosh`、气泡弹出 `pop`；年份每过一个十年一声 `tick`（落点由同一张 `KEYS` 缓动表反解，比"每年一声"克制）；停在 2000 一声 `click`；指示棒每点一个气泡一声轻 `pop`；两次倒带各一声 `swish_rev`，落点在倒带结束；冲到 2020 一声 `click`，结束标题 `ding`。
- **样片的转场音效**：`air` 加倒带：坐标轴射出是短促的 air（0.35 s）；两次倒带用按倒带时长塑形的 `swish_rev`，结尾那次更低更暗。

## 适合与不适合

- **适合**：05 数据故事（主类型）；02 横屏科普；06 需要展示许多实体随时间变化的结果。
- **不适合**：实体少于约 15 个（用折线）；没有时间维度；需要精确读数的比较。
- **容易被误用成**：没有讲述、从头匀速播到尾的"动态气泡图演示"，或者花哨的 bar chart race。

## 禁止项

1. 气泡半径 ∝ 数值。应该面积 ∝ 数值，也就是 `r ∝ √值`。
2. 线性收入轴，把九成的实体挤在左下角。
3. 时间从头到尾匀速播放，没有停顿、减速和讲解。
4. 超过 3 个带轨迹的气泡，或者给所有气泡都贴标签。
5. 缺年的数据悄悄插值；插值的段落要标"插值"或直接跳过。
6. 用图例解释颜色：第一次出现时在每个地区的气泡群旁直接写地区名。

## Prompt 块

```text
Visual style: live-narrated animated bubble chart. Light page #F7F5F0, ink #23211E. One chart is the whole stage: x = income per person on a log axis labelled at doublings, y = life expectancy, bubble area proportional to population (radius ∝ √value), colour = region (vermilion #E4572E, teal #29A0B1, olive #8FB339, amber #F2B134), 85% fill with a thin white rim. The current year sits behind the bubbles as a huge pale numeral (#E6E1D6, Avenir Next Ultra Light) that rolls like an odometer. Time is performed, not played: it races at ~10 years per second, eases out into a key year, holds 2–3 s while the narrator explains, sometimes rewinds; easing applies only to the year-versus-time mapping, never to the data, and bubbles interpolate linearly between data years (income in log space). The narrator is embodied by a thin ink pointer that reaches in from the edge and follows the bubble being discussed. Focus dims all other bubbles to 20% and leaves a dotted trail for at most three selected bubbles. Plain-language axis titles with units, direct labels, no legend. Avenir Next throughout, PingFang SC for Chinese. A playful 120 BPM major-key marimba that plays the year odometer (a note per fixed number of years, slowing and speeding with the easing, falling on rewinds), a shaker on the same clock, pizzicato plucks on each decade and each pointer tap; a held chord while time holds; ticks while time runs.
```

## 引擎做法

- **首选 HyperFrames + SVG 或 Canvas**。数据是 `data/panel.json`（实体 × 年份），真实数据推荐 Gapminder 的开放数据（CC BY 4.0，按其要求署名）。
- **时间映射**：写一张关键帧表 `[{t: 0, year: 1950}, {t: 1.9, year: 1990, ease: "linear"}, {t: 2.4, year: 2000, ease: "outCubic"}, …]`，`year(t)` 分段插值；倒带就是一段 year 递减的关键帧。
- **插值**：`x = lerp(log(inc[y0]), log(inc[y1]), f)`、`y = lerp(life[y0], life[y1], f)`、`r = k · √lerp(pop[y0], pop[y1], f)`。每帧按半径从大到小排序画（同半径按 id），小气泡不会被埋掉。
- **轨迹**：对选中的实体，在当前年份之前每个整年画一个 35% 不透明的小点。
- **里程表**：每一位数字 `d = floor(year / 10^k) % 10`，最后 20% 的时间里向上滚到下一位。
- 样片 `swatch.js` 用的是**虚构的示意数据**（画面上标明 "illustrative data"），只演示语法，逐段做法见开头"样片里"。实现要点：坐标轴的定义域是 t 的函数（结尾重新定标），所有位置、刻度和轨迹都经过同一个比例尺函数，气泡在定标时裁到绘图区内。

## 自查重点

- 抽 3 个气泡、3 个年份，对照数据文件核对位置（x 要换算成对数）。
- 人口翻倍时面积翻倍（半径 ×1.41），不是半径翻倍。
- 停帧时，年份水印和当前数据年份一致。
- 停住的 2 s 里，选中的气泡没有被别的气泡挡住。
- 对数刻度的标签是整倍数，单位写清；来源行在画面上。

## 相关资源

- `references/repos/data-animation-skills/skills/chart-animation/SKILL.md`（MIT）：每个值从当前帧算出，排名和位置都插值、不跳。
- `references/repos/lemo-opuscar/styles/dataviz/STYLE.md`（LemoLab，CC BY 4.0）：把 Rosling 的"一个点就是一个角色"列为对标，本文沿用这个思路，改成气泡图、浅底和指示棒。
- `references/repos/hyperframes/skills/hyperframes-creative/references/data-in-motion.md`。
- `video-types/05-data-story.md`（"Gapminder 式动画适合讲故事"一条）；`playbook/04-audio.md`（cue 词触发）。
