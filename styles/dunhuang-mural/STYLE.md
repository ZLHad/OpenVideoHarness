# 敦煌 · dunhuang-mural

土墙上的矿物色壁画：石青、石绿、赭石、土红和一点金，铁线勾勒，飞天沿长弧线飞过，长长的飘带跟在身后。适合丝路、历史、传说、宗教艺术史这类题材，也适合横卷式的连续叙事。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

样片实况：0.0 s 一声编钟，一团像火把的光扫过昏暗的窟壁。0.1 s 起一对飞天从画面两侧飞进来，先用铁线描勾出，再上色：有头和高髻，上身赤裸、斜挎绶带，长裙下露出双足，一只手托着盛花的金盘。每人拖两条飘带，长约身长的 3–3.5 倍，沿长 S 弧飞向中轴，3.6 s 两人的头在中轴上相会，正落在编钟的强拍上。2.0 s 起，下方一条横卷叙事带分三段，画同一组云纹和莲花的三个阶段：起稿 → 平涂 → 叠晕加点金；2.8 / 3.2 / 3.6 s 每拍点一层金（边框金点、莲心、金线）。4.0 s 藻井从中心一层层打开，露出结束画面。英文标签 40 px。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 敦煌莫高窟壁画 | 据武周圣历元年（698）《李君修莫高窟佛龛碑》，前秦建元二年（366）沙门乐僔始凿，延续约千年（学界另有更早之说）· 历代画工 | 矿物色的配方与年代感；铁线描；北朝的凹凸晕染和唐代的叠晕；含铅颜料氧化后发黑的"时间色" |
| 莫高窟第 257 窟《鹿王本生图》 | 北魏（具体年份未核实）· 西壁中层横卷，约 58 × 390 cm | 横卷连环画：一条带子上异时同图，情节从两端向中间推进，高潮在正中 |
| 莫高窟第 320 窟南壁飞天 | 盛唐（具体年份未核实） | 飞天成对，以腰为轴反向回旋，从两侧向中轴汇合；飘带九曲回环，比身体长好几倍 |
| 《九色鹿》 | 1981 · 上海美术电影制片厂，导演钱家骏、戴铁郎；取材第 257 窟 | 把壁画的平面性搬进动画：平涂色块 + 铁线，侧面构图，人物沿水平方向运动 |

**不照搬**：不复刻九色鹿和任何具体洞窟的构图、佛像、菩萨像，不描壁画照片。飞天只学它的运动和飘带，不做成可识别的某一身。

## 视觉语法

一支片只选一个时期的色板。默认盛唐（写进 tokens）；做北朝题材时整片换北朝色板。

- **盛唐色板**：
  - 壁面地仗 `#D8C09A`：底色，暖土黄，不用纯白；
  - 墨线 `#3B2A20`：所有轮廓；
  - 石青 `#33698C`：强调色，飘带、衣纹主色；
  - 石绿 `#4E9A7E`：衣裙、莲叶、边饰；
  - 朱砂 `#B23A2A`、土红 `#9E4A32`、赭石 `#9A6334`：肤色阴影、衣带、边框；
  - 金 `#C8A04A`：只用于点金（头光外缘、璎珞、花心），面积不超过 5%；
  - 高岭土白 `#EFE6D2`：肤色底、云头；
  - 变色铅丹 `#4A3428`：肤色边缘的"氧化黑"，表现年代。
- **北朝色板**：土红底 `#8E3B2A`，石绿 `#5B9A80`，白 `#EDE3CF`，黑褐 `#3A2A22`，少量石青 `#3C6A86`；不用金。
- **字体**：
  - 盛唐题字：`Kaiti SC` → `STKaiti`（楷书接近唐代写经的笔意）；北朝题字：`Weibei SC`（本机未装，Font Book 可下载），缺字时退回 `Kaiti SC`；
  - 正文、字幕：`Songti SC`，44–52px，墨线色；
  - 英文：`Optima`，字距 +0.04em，全大写只用于小标签。
  - 样片实际用字：`Optima` 72px（英文）、`Kaiti SC` 88px（中文）、标签 `Kaiti SC` 52px + `Optima` 40px 大写。`Weibei SC` 本机没有，样片未用。
- **构图**：
  - 画面横分三带：上带（天空、飞天、散花）占 30%，中带（叙事）占 50%，下带（边饰）占 12%，其余是边距；带与带之间画 8–12px 的土红分隔线；
  - 飞天身体斜 30–45°，飘带是身长的 3–5 倍；成对出现时从左右两侧向中轴汇合；
  - 标题卡用藻井构图：方形套方形，中心莲花，四周边饰，严格中轴对称。
- **质感**：
  - 壁面：低频泥灰噪声 ±4% 亮度，细裂纹（Voronoi 边，宽 1px，压暗 30%）；
  - 剥落：fbm > 0.72 的区域露出地仗色，外缘 1px 暗边；每个画面剥落面积 3–8%；
  - 设色：所有颜色整体降饱和约 15%；不加高光、不加光晕；
  - 线：北朝铁线描，均匀 2px；盛唐可以有粗细，1.5–3.5px；
  - 晕染：唐用叠晕，同一色相按 100% / 82% / 64% 明度排成 3 条硬边色带；北朝用凹凸晕染，边缘深、中间浅。

## 运动语法

帧数按 30 fps 计。

- **缓动**：
  - 飞行、飘移用 easeInOutSine `cubic-bezier(0.37,0,0.63,1)`，进场同曲线，出场用 easeInSine `cubic-bezier(0.12,0,0.39,0)`；
  - spring 无回弹：stiffness 80、damping 18（ζ≈1.0）；
  - 禁止弹跳和 overshoot：飞天是飘的，不是弹的。
- **时长**：进场 30 帧（1 s）；每个画面至少停 2 s；每 3 s 发生一件新事（一身飞天飞入、一阵散花、一段横卷推进）。
- **跟随**：飘带上第 i 个点取头部路径在 `t − i·Δ` 时刻的位置，Δ = 35 ms，再沿法线加 `A·sin(2π(0.8t − i/12))` 的卷曲。飘带永远落后身体，停下后再过 0.6 s 才静止。
- **转场**：全片只用三种：
  - 横卷平移：整条带子从右往左连续推进，没有切；
  - 设色显现：按壁画的作画顺序出现，起稿墨线 → 平涂 → 叠晕 → 描金，每步 8–10 帧；
  - 藻井收放：方形套叠的遮罩一层层向中心收拢，或向外打开下一场。
- **镜头**：横移（pan）为主，速度 60–100px/s；不推镜，不做 3D。
- **文字动画**：逐字出现（stagger），每字间隔 180ms，有仪式感；每个字先出墨线双钩轮廓，再填色。

## 声音语法

- **配乐**：丝路乐舞。`bin/vh music`，`bpm: 72`，`key: "E"`，`mode: "dorian"`：E 商调，骨干是 D 宫五声里的 E F♯ A B D，G 和 C♯ 当经过音，听起来是明亮的调式音乐，不是大调也不是小调（北朝题材改 `mode: "minor"`，更暗）。写成 `parts`：`pipa` 领奏，长音用轮指（`"tremolo": 14`，`"tremolo_min": 0.9` 只让一拍左右以上的音轮指），开头可以一记扫弦；`harp` 当箜篌，八分音符上下分解和弦，段落转换时一串上行刮奏；`sheng` 垫一个空五度长音（E–B–E）；`framedrum` 每小节第一拍一下；`bell`（编钟）只在段首和汇合点敲；`space: hall`，RT60 3 s 以上。不假装复原唐代燕乐。
- **音效**：戈壁风声（低频带通噪声，贯穿全片，−24 dB）；飘带掠过的布料 swish；散花落下时极轻的铃；设色显现每一步一声干涩的笔刷声。内置库可以先占位：风用拉长的 `whoosh`，铃用压低音量的 `ding`，笔刷用 `swish_rev`。
- **声画关系**：一个乐句配一段横卷。飞天汇合到中轴时 `bell` 落在强拍上。整片没有硬切，也没有鼓点轰炸。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：150 BPM，E 商调（E 多利亚），小节是 2、3、4、1、3 拍，每小节第一拍一记框鼓。0.0 s 编钟 E4 和琵琶一记扫弦同时起，笙的空五度 E–B–E 从这里一直垫到结尾；0.2 s 琵琶在 B4 上轮指；0.8 s（A 大三和弦）琵琶弹 E–D–C♯–B–A，C♯ 那一拍轮指，箜篌八分音符上下分解；2.0 s 横卷出现，和弦 D → Em，琵琶 F♯ 轮指、E–D、E 轮指、G–F♯；3.6 s 飞天在中轴相会，编钟 E5 和琵琶高音 B5 的轮指同时落下；4.0 s 藻井打开，箜篌从 E4 一串刮奏到 E6，琵琶 A–F♯–E–D 四个十六分音符落回 E，长音轮指。拟音（`events.json`）：3.6 s 两个飞天在中轴相会时左右各一声 `whoosh`，4.0 s 藻井打开一声 `ding`。

## 适合与不适合

- 适合：`07` 手绘叙事（寓言、本生故事式的改编）、`02` 文化科普、`04` A 路线的民乐 MV、`06` 历史或艺术史类讲解的章节卡。
- 不适合：科技产品发布、快剪、需要写实人物的片子。硬套会变成"金光闪闪的古风滤镜"。

## 禁止项

- 把北凉、北魏的土红底粗犷风、隋代的联珠纹、盛唐的卷草和宝相花混成一套"敦煌风"；一支片只用一个时期，跨时期必须分章节并标明；
- 给飞天加翅膀：飞天没有翅膀，靠飘带和云气飞；也不画成性感化的"异域舞娘"；
- 把佛像、菩萨像当装饰贴图、改成搞笑表情或商品包装；
- 满屏金色、金属渐变、发光粒子、霓虹描边；
- 新鲜、饱和的"荧光矿物色"：石青石绿要沉，整体降饱和、有剥落；
- 把敦煌和日本、印度、波斯的母题拼在一起统称"丝路风"。

## Prompt 块

```text
STYLE: a mineral-pigment fresco on an earthen wall. Ground plaster #D8C09A; ink contour #3B2A20; azurite blue #33698C as the accent, malachite green #4E9A7E, cinnabar #B23A2A, red ochre #9E4A32, a little gold #C8A04A for tiny highlights only (<5% of the frame). Colours are aged and slightly desaturated; lead-based skin tones darken toward brown-black at the edges.
Use one historical period for the whole film (default: High Tang). Even iron-wire contour lines; shading as three hard-edged bands of the same hue (100/82/64% lightness). Plaster grain, hairline cracks, and 3–8% flaked patches showing the bare wall.
Layout in horizontal registers: sky band with flying figures, narrative band, ornamental border band. Flying figures have no wings; they fly on long S-curved ribbons three to five times their body length, in pairs converging on the centre axis.
Motion floats: sine in-out easing, no bounce; ribbons trail the body by 35 ms per segment and settle 0.6 s after it stops. The story unrolls as one continuous horizontal scroll; new scenes appear in the order a mural is painted: ink sketch, flat colour, banded shading, gold.
Titles appear one character at a time (180 ms apart), outline first, then fill. Music: plucked zither, transverse flute, one bronze bell per section, a sandy drone; pentatonic, 72 BPM.
```

## 引擎做法

- **首选 HyperFrames + Canvas2D**，外加一个 WebGL 壁面合成 pass：`final = pigment × plaster(x,y) × (1 − crack)` 后按剥落 mask 混入地仗色。plaster、crack（Voronoi 边距阈值）、flake（fbm 阈值）都用世界坐标的 `hash` 噪声，预先算好缓存，横卷时随世界坐标移动。
- **飘带**：头部路径 `P(s)` 写成解析曲线；飘带点列 `P(t − i·Δ) + n·A·sin(...)`，宽度从 1 渐细到 0.2，画成一个闭合多边形，再用 2px 墨线描边。所有值只依赖 t。
- **叠晕**：同一个形状按 0 / 6 / 12px 内缩画三次，三档明度，硬边，不用渐变填充。
- **设色显现**：四个图层（线、平涂、叠晕、金）各自 `seg(t, a, b)` 控制 `clip-path` 或 alpha。
- 需要手绘晕染时，平涂层可以换成 ClaudeAnimationBase 的 `paint({ wash })`，线条仍用自己的铁线。

## 自查重点

- 同一帧的纹样、配色是否都属于同一时期？列出每个纹样的出处；
- 金色像素占比 ≤ 5%；石青、石绿的饱和度是否压下来了；
- 飘带是否一直落后身体，停下后有没有 0.6 s 的余摆；
- 飞天有没有长出翅膀、有没有被性感化；
- 横卷接缝处的壁面纹理是否连续（世界坐标噪声）。

## 相关资源

- lemo-opuscar 没有对应的敦煌风格；相近的是 `references/repos/lemo-opuscar/styles/stained-glass/STYLE.md`（按光照分格上色）与 `ukiyoe`（手卷式横移），均为 CC BY 4.0（LemoLab）。
- `references/repos/story-to-handdrawn-video/references/handdrawn-style-library.json` 的 `hs-190`（飞天曲线·矿物色，MIT）。
- 敦煌研究院官网的洞窟介绍（第 257、320 窟）：https://www.dha.ac.cn/
- `video-types/07-hand-drawn.md`、`playbook/03-motion-design.md`、`playbook/04-audio.md`。
