# 皮影 · shadow-puppet

一块被油灯从背后照亮的白布幕，布幕上贴着镂空、染色、半透明的皮影人：关节有铆钉，三根签子挑着脖子和双手，灯火一跳，整个世界跟着明暗。适合民间故事、戏曲题材、"讲一个故事"式的科普，以及需要"台前幕后"反转的叙事。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 中国皮影戏 | 2011 年列入联合国教科文组织人类非遗代表作名录 · 各地皮影艺人 | 光透过染色皮子成像；影人以侧面为主（男角多五分脸），头茬与身子分开、可换头；一根脖签、两根手签 |
| 唐山皮影、陕西皮影 | 国家级非遗 · 唐山用驴皮（"驴皮影"），陕西用牛皮 | 镂刻密度：大面积刻空，只留细皮条；雕刻处透光最亮，两片重叠处变暗 |
| 《猪八戒吃瓜》（常被称作《猪八戒吃西瓜》） | 1958 · 上海美术电影制片厂，导演万古蟾 | 中国第一部剪纸片，筹备时专门收集各派皮影研究：给角色加关节、侧面走位、平移表演 |
| 《阿赫迈德王子历险记》（Die Abenteuer des Prinzen Achmed） | 1926 · Lotte Reiniger | 侧面表演的节奏：动作全靠轮廓读懂；蕾丝般镂空的布景 |

**不照搬**：不复刻任何现存传统影人的造型（具体戏出的人物、头茬图样），不用传统唱段原曲，也不照搬 lemo 样片里的"后羿射日"。

## 视觉语法

- **色板**（全部按"透射光"理解：颜色是灯光穿过皮子后的颜色）：
  - 亮幕 `#E9C98F`：油灯照透的布，底色；幕外暗部 `#1A0F08`；
  - 墨黑 `#1C120B`：轮廓、头发、靴子，不透光；
  - 朱红 `#B8261B`：强调色，主角的衣袍；
  - 黄 `#D9A02B`、绿 `#2F7A45`、青 `#245E7A`：其余衣饰，每个角色选两种；
  - 皮本色 `#D8B07A`：未染色的皮、脸；
  - 灯焰 `#FFB65C`：只出现在灯和"灯就是太阳"的情节里。
- **字体**：
  - 片名、唱词：`Libian SC`（隶变）→ `Kaiti SC`；
  - 字幕：`Kaiti SC`，46–52px，奶油色 `#F3E2BF`，放在幕下方的漆木条上；
  - 英文：`Baskerville` 600。
  - 样片实际用字：皮板刻字：`Baskerville` SemiBold 66px（英文）、`Libian SC` 92px（中文）；卡片标签 `Libian SC` 52px + `Baskerville` 24px 大写。
- **构图**：
  - 整个画面是一个戏台：幕框占画面 90%，框内 70% 以上是空的亮幕；
  - 影人高度 0.45–0.6H，脚踩幕的下沿（y≈0.84H），侧面朝向行进方向；
  - 景片（桌、树、山、屋）是同样镂刻的皮片，贴边放，一场不超过 3 件；
  - 亮度中心在灯的位置：幕中上方最亮，四角暖暗（暗角压向 `#6E4A26`，不要压成中性灰）。
- **质感**：
  - 皮子：半透明斑驳 ±7%、纤维细纹；每个色块外有 1.5–2.4px 的墨色刻线；
  - 镂空：盔甲是成排月牙孔，裤子是菱形格，腰带是铜钱孔（圆孔中间留方皮）；
  - 布幕：细密布纹 + 低频浓淡；轻微胶片颗粒（ffmpeg `noise=alls=4:allf=t`）。

## 运动语法

帧数按 30 fps 计。

- **缓动**：
  - 身体随主签平滑移动：进场 easeOutCubic `cubic-bezier(0.33,1,0.68,1)`，出场 easeInCubic `cubic-bezier(0.32,0,0.67,0)`；
  - 手抖：每个影人叠 2–3px、0.5–1.5Hz 的低频噪声，紧张时乘 1.8；
  - 四肢和翎子不受签子控制，按阻尼摆计算：`θ = θ0·e^(−ζωΔ)·cos(ω_d·Δ)`，Δ 为距上次身体急停的时间，ζ≈0.25（这是角色物理的例外，不是 UI 缓动）；
  - 入场的 spring：stiffness 120、damping 16（ζ≈0.73）。
- **时长**：进场 16 帧；造型亮相（亮相定格）至少 1 s，只有翎子在颤；每 2.5 s 发生一件新事。
- **贴幕与离幕**：影人从灯那边"贴上"幕：放大 1.8→1、模糊 24→0px，用 16 帧；离幕反过来，放大 ×1.9、模糊 +30px、27 帧淡出。
- **转场**：全片只用三种：灯灭灯亮（8 帧灭到全黑，12 帧重新点亮，新灯先冲到 1.5 倍亮度再回落）、离幕（主角离开布幕虚化成光）、景片横扫（一块镂空景片从幕前滑过当擦除）。
- **镜头**：固定机位（locked），就是观众席的视角；只允许每镜 ≤ 8% 的慢推。高潮后可以"绕到幕后"一次：画面水平镜像，露出灯和签子。
- **文字动画**：镂刻字（cutout）。字刻在深色皮板上、透出灯光，皮板由两根签子挑上来，离场时离幕虚化。

## 声音语法

- **配乐**：锣鼓经为骨架。`bin/vh music`，`bpm: 96`，`key: "G"`，`mode: "major"`（G 宫五声，热闹段落）；悲情段落另渲一份 `mode: "minor"`（G 羽）。一份 score 只有一个速度，"越打越紧"靠段落里逐步加 `taiko`、`clap` 和提高 `energy` 做；真要变速（比如 96 → 132），分段渲染两份 score，在小节线上拼接。`taiko` 当堂鼓、板鼓，`clap` 当梆子，`bell` 高音区当小铜碗一类的清脆点子，`dizi` 或 `zheng` 走旋律。胡琴、唢呐目前做不出来，不要用 pad 硬冒充。
- **音效**：开场和收场各一声醒木（硬木拍击）；火柴划燃和油灯"噗"地点亮；签子碰幕的轻响；皮片离幕的干皮子声；灯灭的"噗"加一声吱响。内置库可以先占位：醒木用 `click` 叠一个低音量 `impact`，签子碰幕用 `tick`，离幕用 `swish_rev`，灯亮用 `whoosh`；醒木和灯最好换成有授权的录音。
- **声画关系**：锣鼓点和动作一一对应：亮相落在大鼓上，每一击一个动作。抉择时刻锣鼓一齐收住（鼓和梆子在一拍内撤掉），只留大鼓的余响和一个极轻的低音垫，然后一声高音区 `bell` 轻敲；不做数字静音。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：150 BPM，G 宫；大鼓当堂鼓、`clap` 当梆子，0.8 s 起加古筝，2.0 s 三张卡片贴幕时竹笛和 `impact` 进来，4.0 s 灯灭时一记 `impact` 当锣，只留编钟和 `pad` 垫着。

## 适合与不适合

- 适合：`07` 民间故事短片、`04` 戏曲或民乐 MV、`02` 历史和非遗科普、`03` "灯亮了"式的产品揭示（产品就是那盏灯）。
- 不适合：需要正面表情特写、复杂手部动作、写实场景的片子。硬套会变成"彩色贴纸在黄底上平移"。

## 禁止项

- 纯黑剪影：那是剪影片或剪纸，不是皮影。皮影的签名是透光的彩色和镂空；
- 正面脸、3D 透视、影人在幕前"凌空"而没有贴幕；
- 冷白、均匀、不闪的背光：油灯是暖的，而且在跳；
- 签子凭空漂浮：签子必须连在脖子和双手上，并且伸出画框下沿；
- 把中国皮影和印度尼西亚 wayang kulit、土耳其 Karagöz 的造型混为一谈：它们是不同的传统，比例、纹样和上色都不同；
- 大面积平涂、不刻镂空：看起来会像剪贴画。

## Prompt 块

```text
STYLE: Chinese shadow puppetry. A cloth screen lit from behind by a flickering oil lamp: warm lit cloth #E9C98F, dark stage surround #1A0F08, warm (never grey) vignette. Figures are flat, translucent, dyed hide seen by transmitted light: vermilion #B8261B as the accent, yellow #D9A02B, green #2F7A45, blue #245E7A, raw hide #D8B07A, black #1C120B for outlines and boots.
Carving is density: most of each piece is cut away into crescents, lattices and coin holes; holes glow brightest, overlapping pieces darken. Every coloured region has a thin dark carved outline.
Figures are in profile, jointed with visible rivets, moved by one neck rod and two hand rods that run off the bottom of the frame. Bodies glide smoothly with a small hand tremor; limbs and plumes swing as damped pendulums after each stop. Arrivals press onto the screen from big and blurry; exits lift off into light.
Locked audience-seat camera. Transitions: the lamp dims to black and relights, a figure lifts off the cloth, a carved scenery piece slides across. Titles are letters cut out of a dark hide plaque so the lamp shines through.
Sound: gong-and-drum patterns drive every action, the drums pull back to a low held resonance before the key decision (never digital silence), a wooden clapper to open and close. Pentatonic, 96 BPM rising to 132.
```

## 引擎做法

- **首选 HyperFrames + Canvas2D**，最后一个 WebGL 合成 pass。逐像素：`image = tonemap(lamp(x,y,t) × transmission(x,y) × cloth(x,y))`：
  - `transmission` 画布起始为白，每块皮片用 `multiply` 画上去；镂空先把 `fillStyle` 设为不透明再 `destination-out`；
  - `lamp` = 宽光斑（σ≈700px）+ 热点（σ≈120px），亮度乘 `1 + 0.06·vnoise(7t) + 0.02·sin(2π·23t)`，噪声用 `hash` 种子，是 t 的纯函数；
  - `tonemap(x) = 1 − e^(−x)`，灯越多曝光越高，画面发白发烫。
- **影人**：11 块左右的皮片，关节处画圆耳和铆钉（暗环 + 浅色结）；手臂用两骨 IK 从手签位置反解。
- **阻尼摆**用闭式解，按身体急停的时刻表求 Δ，不做逐帧积分。
- **幕后镜像**：同一张 transmission 画布 x 取反，外面画暗木框、灯盏和带暖色边光的手与签子。
- 字幕条和片名画在屏幕空间，画之前重置 transform。

## 自查重点

- 放大看镂空处（`--crop`）：孔是最亮的吗？两片重叠处是否变暗？
- 连续 10 帧看灯的亮度曲线：在跳，但不闪屏（单帧变化 ≤ 8%）；
- 每个影人的三根签子是否都连着、都伸出画框；
- 急停后四肢有没有余摆，余摆是否在 1 s 内收住；
- 暗角是暖色还是灰色；锣鼓收住的地方底垫是否还在（`bin/vh qa scan` 不能报数字静音）。

## 相关资源

- `references/repos/lemo-opuscar/styles/shadow-puppet/STYLE.md`（LemoLab，CC BY 4.0，https://creativecommons.org/licenses/by/4.0/）。本文为重写：透射光合成公式、灯的闪烁参数、贴幕离幕和幕后镜像的思路改编自该文。原文说皮偶用驴皮，同时以陕西华阴皮影为参照；按中国非物质文化遗产网的资料，驴皮是唐山一路的做法，陕西多用牛皮，本文把两者分开写。
- 中国非物质文化遗产网"皮影戏（唐山皮影戏）"条目：https://www.ihchina.cn/project_details/13392.html
- `video-types/07-hand-drawn.md`（剪纸风一节）、`playbook/03-motion-design.md`、`playbook/04-audio.md`。
- 相近预设：`styles/silhouette-papercut/`（正面光、不透光的剪纸与剪影，和皮影要分清）。
