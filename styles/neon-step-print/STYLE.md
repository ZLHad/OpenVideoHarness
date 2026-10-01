# 霓虹抽帧 · neon-step-print

一句话：夜里的霓虹、被抽帧拉成光带的人群、红与绿两种互补色，还有贴着人走的手持镜头。它把"时间"本身拍成看得见的东西：匆忙时拖出残影，想念时慢下来。适合城市夜景、情绪化的 MV、关于时间和记忆的短片，以及夜生活和城市品牌。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：0.1 s 路灯闪着亮起。青黑夜街上，人群按 8 fps 长曝光抽帧，车灯拖成光带；左侧是一个清晰的侧影人物：竖领大衣，手里一杯冒热气的纸杯，脸侧打红色轮廓光。时间戳在 2.5 s 越过午夜，数字逐位翻。三块霓虹招牌在 2.0 / 2.4 / 2.8 s 依次闪着点亮：两块绿的，初版是一个红色霓虹胶片盘，招牌的颜色洒到人物身上。中间那块在 3.2 s 电流声般闪一下，3.6 s 人物把杯子举到嘴边。字幕是宋体 78 px 和 66 px 窄体，下面垫一条暗带。4.0 s 整帧进入抽帧快摇，在光带最长处切到一张红色定格长曝光。实际字体：DIN Condensed Bold、Avenir Next Condensed Medium、Songti SC。配乐是王家卫式的弦乐华尔兹（《梦二》那一路），D 小调：150 BPM 的网格按 2 / 3 / 3 / 2 / 3 拍分小节，每小节都按华尔兹分组，`pizzicato` 低音在第 1 拍，`strings` 在其余拍上轻轻起；独奏 `violin` 宽揉弦（约 36 音分）加滑音，0.1 s 跟路灯一起进来，旋律是 A–D，滑上 G，再 F–E | F–D | C#–A，最后一句 G 挂在主和弦上再落到 F；底下一层 `rain`，暖色大厅混响。拟音：0.1 s 路灯亮起、招牌点亮用 toggle，时间戳翻页用 tick（它是读数，`role` 写成 `signal`；2.5 s 过午夜、每一位数字都翻的那一下比另外三下重 4 dB），字幕打字用 typing，招牌闪用 glitch，定格用 shutter。拟音的落点写在 swatch.js 的 `FOLEY` 常量里，`events.json` 由它生成。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《重庆森林》*Chungking Express* | 1994 · 导演 王家卫；摄影 杜可风（Christopher Doyle）、刘伟强（Andrew Lau）。抽帧镜头多在前半部，据影评由刘伟强掌机 | 抽帧（step printing）：低帧率加慢快门拍摄，再把每一格重复印几次。动的人群拉成色带，不动的人保持清楚；手持、自然光、霓虹 |
| 《堕落天使》*Fallen Angels* | 1995 · 导演 王家卫；摄影 杜可风 | 超广角贴着脸拍，画面边缘强烈变形；夜色里的红绿霓虹和荧光灯 |
| 《花样年华》*In the Mood for Love* | 2000 · 导演 王家卫；摄影 杜可风、李屏宾；梅林茂的《梦二主题曲》（原为铃木清顺 1991 年的《梦二》所作）在片中反复出现 | 反面的做法：慢动作配同一段华尔兹主题，成了"记忆"的记号；从门框、走廊、窗格里偷看，前景遮挡占掉画面一大块 |

核实：年份、导演、摄影和配乐来自 Wikipedia 与 Shazam、Wise Music 的曲目资料。抽帧镜头的具体拍法（约 6 fps 拍、每格印 4 次）和掌机归属来自影评与技术博客，**未核实**。

**不照搬**：不用原片的歌曲和旋律（《California Dreamin'》《梦二主题曲》等）；不做旗袍、快餐店柜台、过期罐头、制服警察这类具体道具和人物；时间戳字卡可以用，但不引用原片的台词和日期。

## 视觉语法

- **色板**：两种互补的强调色，分工固定。这是 TASTE #9"只用一个强调色"的刻意例外，用这个风格时要写进 NOTES。

  | token | hex | 语义 |
  |---|---|---|
  | bg 夜青黑 | `#0A1414` | 夜；暗部偏青，不偏灰 |
  | fg 暖纸白 | `#F3E9D2` | 字幕、时间戳 |
  | accent 霓虹红 | `#E0282E` | 欲望、温度、过去 |
  | extra 荧光绿 | `#2BC46A` | 孤独、此刻、冷 |
  | extra 钠灯橙 | `#F29A2E` | 街灯、皮肤上的暖光 |
  | extra 深青 | `#12383A` | 暗部的颜色 |

  一个镜头里红和绿只能有一个做主光，另一个的面积 ≤ 15%。高光允许溢出：高光周围做 12–24 px 偏红的光晕（halation）。
- **字体**：
  - 时间戳和地点用 DIN Condensed Bold，或 SF Mono → Menlo，数字用 tabular，例如 `23:59 · 5.1`；
  - 中文字幕用 Songti SC Regular，52 px，暖纸白加 2 px 深色描边；
  - 英文用 Avenir Next Condensed Medium，44 px。

  字幕放在画面下方 1/5 处，左对齐或居中都行，全片统一。
- **构图**：
  - 主体偏到画面一侧（x ≤ 0.3W 或 ≥ 0.7W），另一侧留给街道和光；
  - 前景遮挡物（门框、栏杆、玻璃反光、人群的肩膀）占画面 20–35%，失焦；
  - 地平线倾斜 3–8°；超广角贴近时允许边缘变形。
- **质感**：film，强度 0.25：颗粒加 halation。暗部抬到 `#0A1414` 左右，不压成死黑；高光偏暖。

## 运动语法

帧数一律按 30 fps 计。

- **抽帧**（签名）：画面内容按 8 fps 的有效帧率采样，每张图在 30 fps 成片里停 3–4 帧。每张图本身是一次长曝光，等效快门超过 360°：在 [t_q, t_q + 1/8 s] 里取 10–16 个子样本求平均。结果是动得快的东西拖成光带，静止的主体保持清楚。
- **两种时间**：匆忙、追逐时用抽帧加手持；记忆、凝视时用 0.4× 慢动作，每帧都采样、快门短、画面干净，并且每次都配同一个音乐动机。两种时间在片子里交替出现。
- **手持**：位置噪声 6–14 px，旋转 ±0.6°，主频 0.8–1.6 Hz，用带种子的 1D value noise(t) 生成。抽帧段里镜头也跟着画面一起步进；慢动作段里镜头保持平滑。
- **缓动**：慢动作里的物体用 `cubic-bezier(0.3,0,0.2,1)`；字幕进出用 `cubic-bezier(0.25,0.46,0.45,0.94)`，淡入 8 帧，不移动。
- **时长**：一个镜头 2–5 s，每 3 s 一个新事件；慢动作段一次 4–8 s。
- **转场**（全片只用这 3 种）：
  - 硬切，切在动作上；
  - 抽帧拖影切：A 镜的最后 8–12 帧进入抽帧，在光带最长的那一帧切到 B；
  - 定格：画面停在一张长曝光上 12–20 帧，然后切。
- **镜头**：手持跟拍、在门框外偷看、横摇跟着人走。不用稳定的滑轨推进。
- **文字动画**：时间戳的数字逐位翻动（`steps`，每位 2 帧），像电子钟跳字。

## 声音语法

- **配乐**：带揉弦的弦乐或合成器主旋律加拨弦低音，84 BPM，D 小调。记忆段用同一个 4–8 小节的主题，全片至少出现 2 次。`bin/vh music` 的做法（`parts`）：
  - `violin` 主奏，`vib` 加宽到 30–40 音分，`glide` 0.15 s 左右，连着的音会滑过去；
  - `figure: waltz` 分给两件乐器：`pizzicato` 用 `role: bass`（第 1 拍），`strings` 用 `role: chord`（其余拍）；2、3、4 拍的小节都成立，整首三拍子写 `beats_per_bar: 3`；
  - `rain` 当环境底；
  - 追逐段再加鼓。

  样片的 `score.json` 就是这么写的。
- **环境声**：霓虹灯管 50/60 Hz 的嗡声、雨、远处的车流和人群。`bin/vh music` 的 `hum`、`rain` 底噪可以直接用，其余在项目里合成（正弦加谐波、带通噪声），或用有授权的采样。
- **音效**：
  - `whoosh`（`dist` 2–3）配抽帧拖影；
  - `click` 配时间戳跳字；
  - 定格时一记 `shutter`。
- **声画关系**：抽帧段的声音是连续的，不跟着画面步进，反差就来自这里。慢动作段的环境声降 12 dB，只剩音乐。

## 适合与不适合

- **适合**：04 MV（情歌、city pop、lo-fi、电子）；02 城市、旅行、夜生活短片；03 夜间的城市品牌和餐饮；关于时间、错过、记忆的叙事。
- **不适合**：产品功能讲解、数据图表、需要读完大量文字的内容；白天的场景。
- **容易被误用成**：只剩"赛博朋克霓虹 + 雨"。没有抽帧，也没有两种时间的对比，就只是一张赛博壁纸。

## 禁止项

1. 用 CSS blur 或方向模糊贴图冒充抽帧。必须是真正的子帧累积加步进。
2. 红和绿同时做主光，或者加进第三种饱和色（青紫赛博色）。
3. 居中对称的构图、稳定器式的平滑推进。
4. 抽帧段里字幕也被拖影抹花。字幕层不参与步进和累积。
5. 通篇抽帧，没有慢动作或凝视的段落做对比。
6. 使用原片的歌曲、旋律或台词。

## Prompt 块

```text
Visual style: neon night with step-printed motion smear. Night teal-black #0A1414 with lifted shadows and two complementary neon lights with fixed meanings: red #E0282E for warmth and the past, fluorescent green #2BC46A for loneliness and the present, never both as the key light in one shot; sodium orange #F29A2E for street light; halation around highlights; film grain. Signature: step printing. Sample the scene at 8 fps, each sample a long-shutter exposure averaged from 12 sub-frames and held for 3–4 output frames, so the still subject stays sharp while the crowd and traffic smear into light trails. Alternate this with clean 0.4x slow-motion passages that always bring back the same short melodic theme. Framing: the subject pushed to one side, 20–35% out-of-focus foreground occlusion (door frames, glass, shoulders), a 3–8° dutch tilt, close wide-angle handheld (6–14 px noise, ±0.6°). Text: timestamps in condensed digits that flip digit by digit, and warm white subtitles untouched by the smear. Transitions: a cut on action, a smear-out cut at the longest trail, a 12–20 frame freeze. Sound: an 84 BPM D-minor lead with vibrato over plucked bass, with neon hum and rain underneath.
```

## 引擎做法

- 首选 HyperFrames 加一层 Canvas 或 WebGL（抽帧需要累积缓冲），纯 Canvas2D 也可以。
- **抽帧**（纯函数）：

  ```js
  const FPS_EFF = 8, SUB = 12, SHUTTER = 1.2;          // SHUTTER 1.2 ≈ 432° 快门
  function stepPrint(t, drawScene) {                    // 只用于画面层
    const tq = Math.floor(t * FPS_EFF) / FPS_EFF;
    accumulate(SUB, (k) => drawScene(tq + (k / SUB) * SHUTTER / FPS_EFF));
  }
  ```

  累积时以 `globalAlpha = 1 / SUB` 叠加到离屏 canvas；WebGL 里用 additive 混合再除以 SUB。字幕层在累积完成之后再画。
- **手持**：`shake(t) = [n1(t*1.2)*10, n2(t*0.9)*8, n3(t*1.4)*0.6°]`，n1–n3 是带种子的 1D value noise；抽帧段里代入 tq 而不是 t。
- **halation**：取亮度 0.8 以上的高光，模糊 16 px，着偏红的颜色，以 screen 叠回，强度 0.35。
- **前景遮挡**：最上层放一层失焦的黑色剪影（门框、栏杆），跟随手持做 1.3× 视差。

## 自查重点

- 抽帧 strip（连续 12 帧）：画面每 3–4 帧才变一次；动的东西有光带，主体清楚。
- 字幕在抽帧段逐帧清晰，不抖。
- 1 fps 联系表：每个镜头的主光只有红或绿之一；全片有慢动作段做对比。
- 暗部取样：亮度不低于 `#0A1414`，没有死黑。
- 记忆主题全片至少出现 2 次，每次出现时画面都是慢动作。

## 相关资源

- lemo-opuscar 里没有直接对应的风格。`cel-anime-80s`（背光霓虹、1987 年录像带质感）只在"霓虹背光"这一点上接近，见 `references/repos/lemo-opuscar/styles/cel-anime-80s/STYLE.md`（LemoLab，CC BY 4.0）。
- `playbook/08-vfx-and-motion-sources.md` 的"真正的子帧运动模糊"一节：抽帧就是它的变体，快门超过 360° 再加步进。
- `video-types/04-lyric-music-video.md`、`video-types/02-knowledge-short.md`。
