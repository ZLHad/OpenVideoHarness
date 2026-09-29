# 国潮 · guochao-festive

红底、金线、现代粗宋大字，传统纹样按网格一拍一格地铺开：喜庆但克制的节日图形。适合春节和节日祝福、国风新品发布、文化活动宣传、竖屏短视频的开场 hook。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 桃花坞木版年画 | 年代起点未核实 · 苏州桃花坞年画艺人 | 一色一版的套色平刷，五六套色（红、绿、黄、桃红、紫、淡墨）"不分浓淡"；构图对称、饱满；一色一版的套印天然会有轻微错位，本预设把它借来当签名 |
| 中国五大木版年画产地（桃花坞、杨柳青、朱仙镇、潍坊杨家埠、绵竹） | 国家级非遗 · 各地年画艺人 | 门神式的中轴对称和成对构图；大面积纯色对小面积线描；吉祥题材靠图形讲，不靠文字堆 |
| 《大闹天宫》 | 1961（上集）/ 1964（下集）· 上海美术电影制片厂，导演万籁鸣、唐澄；美术设计张光宇、张正宇 | 装饰化造型：几何化的平面色块、对称的建筑布景；京剧锣鼓点给动作卡拍 |

**不照搬**：不用任何真实品牌（老字号、运动品牌、博物馆文创）的字标、吉祥物和配色组合；不复刻具体年画里的门神、戏文画面，也不用《大闹天宫》的角色造型。

## 视觉语法

- **色板**：红、金、象牙三色撑起全片，比例约 65 : 10 : 20，剩下 5% 给墨和冷色点缀。
  - 中国红 `#C21F1F`：底色、大色块；
  - 深红 `#7A0E12`：第二层纸、投影、印章底；
  - 金 `#D8A33A`：强调色，纹样线、数字、分隔线，平涂，不做渐变；
  - 象牙 `#F6E7C1`：大字和正文；
  - 墨 `#1D1414`：细线描和小字；
  - 石青 `#1F5F7A`、松绿 `#1E6B52`：冷色对比，合计不超过 5%；桃红 `#E0567A` 只作年画式点缀，不超过 3%。
- **字体**：
  - 主标题：`Songti SC` Black（900），字距 −0.02em，一屏 2–6 个字，字号 240–420px；
  - 副标题、正文：`PingFang SC` Light（300），和 900 的主标题拉开对比；
  - 印章、落款：`Kaiti SC` Bold；
  - 英文与数字：`Futura` Condensed ExtraBold，计数时每一位数字放进固定宽度的格子，避免跳动；等宽标签用 `Menlo`。
  - 样片实际用字：`Songti SC` Black 148px（中文主标题）、`Futura` Condensed ExtraBold 64px 大写（英文）、标签 `Songti SC` Bold 52px + `Futura` Condensed ExtraBold 28px、印章 `Kaiti SC` Bold。
- **构图**：
  - 中轴对称是默认：标题压在中轴上，两侧纹样镜像；每个画面只允许一个元素打破对称（通常是印章或一个斜放的数字）；
  - 12 栏网格：1920 宽时左右边距 96px、栏间距 24px；大字可以出血，但裁掉的部分不超过字宽的 15%；
  - 边框：回纹带宽 48px，距画面边缘 40px；印章 120px，放在右下第 11–12 栏；
  - 竖屏时关键内容放在 x 90–900、y 330–1520。
- **质感**：
  - 纸：细纸纹，强度 0.25；
  - 套色错位：每个颜色层固定偏移 1–3px（每镜用 `hash(shot)` 定一次，镜内不变），这是木版套印的签名；
  - 不加 bloom、不加光斑、不加颗粒闪烁。

## 运动语法

帧数按 30 fps 计。

- **缓动**：
  - 进场 easeOutExpo `cubic-bezier(0.16,1,0.3,1)`，出场 easeInExpo `cubic-bezier(0.7,0,0.84,0)`；
  - 纹样块弹入用 spring：stiffness 300、damping 26（ζ≈0.75，约 3% 回弹），只给小元素；大字不回弹；
  - 印章：放大 1.35→1，4 帧 easeOutExpo，落地后 2 帧 ±4px 震动。
- **时长**：进场 9 帧（0.3 s）；每个画面至少停 1 s；每一小节（128 BPM 下 1.875 s）发生一件新事。
- **转场**：全片只用三种：中轴对开（两扇红门从中线向左右滑开，12 帧）、印章切（印章砸下的那一帧硬切到下一场）、纹样带横扫（一条回纹带从右往左扫过，10 帧）。
- **镜头**：固定机位（locked），只在重拍上做 2 帧 punch-in（100→108%）。
- **文字动画**：逐字砸入（stagger），每个字落在一个八分音符上（128 BPM 下间隔 0.234 s），放大 1.4→1，4 帧；纹样线按拍子一格一格画出来（每拍多一个回纹单元）。

## 声音语法

- **配乐**：`bin/vh music`，`bpm: 128`，`key: "D"`，`mode: "major"`（中国色层取 D 宫五声：D E F♯ A B，明亮）。编制：`taiko` 打重拍，`kick` + `clap` 给现代律动，`bell`（编钟）在段首和高潮，`dizi` 走主旋律，`zheng` 弹八分音符分解（副歌段开 `bend: true`，得到按弦上滑），`bass` 跟根音。
- **音效**：印章 `impact`；鞭炮用 20–60 ms 间隔、逐渐加密的 `tick` + `pop` 串；纸片 `whoosh`；金色纹样闭合时一声 `ding`。
- **声画关系**：卡点密，但每个卡点只对应一个视觉动作。副歌前留一拍空白（`fill`），空白后的第一拍是全片最大的字。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：样片按 150 BPM 走（不是正文的 128），让 0.8 / 2.0 / 4.0 s 都落在拍上；大鼓和编钟开场，0.8 s 起底鼓、拍手、古筝、贝斯，2.0 s 全编制加竹笛，4.0 s 开门时编钟收尾。

## 适合与不适合

- 适合：`03` 国风产品和活动宣传、`02` 竖屏节日内容与知识短片的片头、`04` B 路线的民乐电子歌词视频、`05` 喜庆场合的数据海报（年度数字）。
- 不适合：需要安静、留白、哀伤情绪的内容；严肃的历史讲解。硬套会变成"红金电商促销页"。

## 禁止项

- 金色渐变、斜面浮雕、3D 金属字、镜头光晕、满屏闪光粒子：这些是廉价感的来源；
- 红金之外再加紫、荧光粉、荧光绿，或把桃红用成大色块；
- 龙、灯笼、熊猫、功夫、筷子、旗袍的"中国元素套餐"同框；
- 纹样出处乱配：商周饕餮纹、明清海水江崖、敦煌飞天放在一起当"古风"；卍字纹（海外观众容易误读）一律不用；
- 真实品牌的字标、吉祥物、配色组合；用笔画模仿汉字的英文花体字（chop suey 字体）；
- 繁简混排、字形写错（尤其是"福""囍"这类常被做成图形的字）。

## Prompt 块

```text
STYLE: modern Chinese festive graphics. China red #C21F1F field, deep red #7A0E12 for the second paper layer, flat gold #D8A33A for linework and numbers, ivory #F6E7C1 for type, ink #1D1414 for fine lines; red:gold:ivory about 65:10:20, cool accents under 5%. No gradients, no bevels, no glow.
Layout on a strict centre axis with mirrored ornaments; exactly one element per frame breaks the symmetry (a seal or a tilted number). 12-column grid, 96px margins. Ornamental meander borders 48px wide, drawn code-side module by module.
Type: an ultra-black Song/Ming serif for 2–6 huge characters (240–420px, may bleed up to 15%), a light sans for sublines. Woodblock misregistration: each colour layer offset 1–3px, fixed per shot.
Motion is beat-locked and punchy but not bouncy: easeOutExpo in, easeInExpo out; characters slam in one per eighth note (scale 1.4→1 in 4 frames); ornaments grow one module per beat; a seal stamps with a 2-frame shake. Transitions: centre-split doors, hard cut on the stamp, a meander band wiping right to left.
Music: big drums on the downbeats, bronze bells at section starts, bamboo flute lead, running zither eighth notes with pitch bends in the chorus, 128 BPM pentatonic; one empty beat before the biggest word. No real brands, no dragon-lantern-panda cliché set.
```

## 引擎做法

- **首选 HyperFrames**（DOM + SVG），字多、排版为主。遵守硬规则 1：所有进度从 t 算，不用 CSS animation 和 transition。
- **纹样全部由代码生成**：
  - 回纹：单位格上的回旋路径（右、下、左、上，每圈缩一格）作为一个模块，沿边框平铺；`stroke-dasharray` 的偏移由拍号 `n = floor((t − offset) / beat)` 决定（`beat`、`offset` 取自 `music.beats.json`），每拍多画一个模块；
  - 云纹：成对的对数螺线加一条连接弧，镜像使用；
  - 如意、冰裂、窗棂格同理，写成参数化函数，不贴图片。
- **印章**：方形 SVG，字用 `Kaiti SC` Bold 反白；边缘用 `hash` 种子的噪声 mask 做残缺和印泥颗粒。
- **套色错位**：每个颜色层包一层 `translate(dx, dy)`，`dx, dy = (hash(shot·7+layer) − 0.5)·6px`。
- 数字计数按 `steps(N)` 跳，每一位数字放在固定宽度的格子里。

## 自查重点

- 截一帧算颜色占比：红约 65%、金不超过 12%、冷色不超过 5%；
- 每个画面是否只有一个元素打破对称；
- 每个字、每个纹样模块是否落在拍子上（对照 `music.beats.json`，误差 ±1 帧）；
- 列出片中每种纹样和它的出处，检查有没有跨时代乱配；
- 有没有任何能被认出的真实品牌字标或吉祥物；字形逐字核对。

## 相关资源

- lemo-opuscar 没有直接对应的风格；相近的是 `references/repos/lemo-opuscar/styles/papercut-red/STYLE.md`（红色剪纸，CC BY 4.0，LemoLab）和 `game-show`（卡在 BPM 网格上的扁平图形）。
- `references/repos/remotion-guofeng-starter/style/design.md` 与 `palette.md`（代码 MIT；`public/` 素材不授权）：朱红只点一下、印章当重音、宋楷苹方三种系统字的分工，本预设借了这套分工，把配色推向更饱和的节日红。
- `references/repos/story-to-handdrawn-video/references/handdrawn-style-library.json` 的 `hs-132`、`hs-189`（国潮插画、新国潮工笔，MIT）。
- `video-types/03-product-promo.md`、`video-types/02-knowledge-short.md`、`playbook/03-motion-design.md`、`playbook/04-audio.md`。
