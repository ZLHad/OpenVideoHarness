# 剪纸爵士片头 · cutout-jazz

一句话：五十年代的剪纸片头语法。画面只用几种不透明的纸色，边缘是剪刀剪出来的，演职员字本身就是画面结构，铜管每一记重音就是一刀。适合给一个概念、产品或章节做"片头式"开场：抽象纸片追逐、聚合，最后拼出主题的符号和名字。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：黑色横梁和三根竖条先落位，片名字母按 16 分音符一片片拍上横梁，中文在芥黄纸条上；母题是三根黑条 → 三块黑版 → 唯一的朱红圆；结尾整幅画面切成 6 条交替滑走，朱红圆原地不动（形状匹配）。实际字体：Futura Condensed ExtraBold（`Futura` 800 + `font-stretch: condensed`）、Futura Medium、PingFang SC Semibold。样片配乐和画面都用 150 BPM（0.8 / 2.0 / 4.0 s 都落在拍上），正片仍按下文的 138 BPM。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《金臂人》*The Man with the Golden Arm* 片头 | 1955 · Saul Bass；导演 Otto Preminger；配乐 Elmer Bernstein | 黑底上几根白条出现、消失、重排，最后汇成全片唯一的符号。3–5 个元素只讲一件事：聚合成符号 |
| 《迷魂记》*Vertigo* 片头 | 1958 · Saul Bass；螺旋图形与 John Whitney 合作 | 全段只有一个几何母题，靠旋转、换色、变形撑满时长 |
| 《桃色血案》*Anatomy of a Murder* 片头 | 1959 · Saul Bass；配乐 Duke Ellington | 人形剪影切成几块，块和字卡轮流跳上画面；爵士的切分重音就是切点 |
| 《西北偏北》*North by Northwest* 片头 | 1959 · Saul Bass | 斜线网格先是抽象图形，再变成建筑立面；字沿网格线滑入滑出 |
| 《惊魂记》*Psycho* 片头 | 1960 · Saul Bass；配乐 Bernard Herrmann | 横竖灰条扫过，把字切开再合上；弦乐的急促重复就是条的扫动节奏 |

核实：片名、年份和合作者已对照 Wikipedia、Art of the Title、BFI 和 Criterion 的资料。1961 年以后的片头多为夫妇二人合作署名，本表只取早期作品。

**不照搬**：不用那只扭曲的手臂、螺旋眼、被肢解的人形剪影，也不用原片任何片名字形；演职员一律写虚构职位（"MUSIC BY THE SAMPLER"），不写真实人名。

## 视觉语法

- **色板**：四种不透明纸色，不用渐变。

  | token | hex | 语义 |
  |---|---|---|
  | paper 奶油纸 | `#EDE3CC` | 留白、呼吸、片名页的底 |
  | ink 墨黑 | `#1B1916` | 结构：剪影、条、字 |
  | vermilion 朱红 | `#D5412B` | 唯一的"事件"：被追的东西、危险、答案 |
  | ochre 芥黄 | `#DFA235` | 第二场景的底色，不和朱红同时做主角 |
  | shade 深朱 | `#8E2B1C` | 只用于纸片阴影和远景，不单独出现 |

  每个场景只有一个主底色（纸、黑、朱、芥四选一），换场景就换底色。朱红面积 ≤ 画面 15%，整场以它为底时除外。
- **字体**：展示用 Futura Condensed ExtraBold，全大写，字距 0.02em（CSS 写 `@font-face { font-family: "CutDisplay"; src: local("Futura-CondensedExtraBold"); }`；fallback 依次是 Avenir Next Condensed Heavy、Impact）。职位小字用 Futura Medium，44 px 起。中文用 PingFang SC Semibold，笔画粗细要接近 Futura Condensed ExtraBold；需要"剪出来"的中文字，用 Heiti SC Medium 的轮廓再剪。所有字形都要"重剪"：轮廓重采样后沿法线加 ±1.2 px 噪声，单字旋转 ±0.8°，基线上下错落 ±2 px。
- **构图**：一段只有一个主母题，占画面 30–50%，留白 ≥ 40%。条和网格只走 30° 或 90°，全片选定一种斜角。字参与结构：一行字当一道横梁，字母 O 当一扇圆窗，破折号当地平线；每行字都要有一刻完整可读。主体偏心放（x≈0.38W 或 0.62W），只有片名页居中。
- **质感**：paper 纹理强度 0.12（低频斑驳 multiply 加稀疏纤维）。剪刀边的做法：轮廓每 10 px 重采样，沿法线位移 1–2 px；**在纸片的局部坐标里算一次并缓存**（seed = piece id，不随 t 变），移动中的纸片边缘才不会"爬"。纸片之间留 2 px 底色缝，投影偏移 (3, 4) px、blur 4 px、alpha 0.25。不用半调，不发光，不用渐变。

## 运动语法

帧数一律按 30 fps 计。

- **缓动**：进场 `cubic-bezier(0.25,1,0.3,1)`，8 帧滑到位后**立刻停死**；退场 `cubic-bezier(0.7,0,0.84,0)`，6 帧。不用 overshoot、bounce 和 spring。背景的持续卷动用线性。
- **两套帧率**：纸片的姿态和位置"一拍二"步进，每 2 帧更新一次（15 fps）；镜头推移、网格生长、字的滑入每帧都更新。镜头也跟着步进，看起来就是卡顿。
- **时长**：一次纸片动作 6–10 帧。每 2 拍一个新动作（138 BPM 下约 0.87 s），每小节换一个构图。字卡停留 ≥ 1.2 s，职位加名字不超过 6 个词。
- **转场**（全片只用这 3 种）：
  - 铜管重音上的硬切（cut-on-stab）；
  - 黑条横扫，擦出下一场的底色（bar-wipe，10 帧，全片统一从左往右）；
  - 形状匹配切，比如圆 → 圆，切点两侧圆心位置和半径完全一致。
- **镜头**：以固定机位为主；需要纵深时做 2D 横移（truck），不做透视推拉。高潮时整幅画面沿选定的斜角切成条，交替滑出，片名字母沿同一条斜线飞入。
- **文字动画**：签名是 cutout。字母就是纸片，按 16 分音符逐个"拍"到位，每落一个配一声纸拍。

## 声音语法

- **配乐**：big-band / cool jazz，138 BPM，F 小调，走路贝斯 + 刷子鼓 + 铜管短促齐奏。`bin/vh music` 只能做近似：
  - `bass` 八分音符根音；
  - `hats`，`clap` 放在 2、4 拍；
  - 高 energy 的 `lead` 充当铜管齐奏；
  - `impact` 放在片名那一小节。

  真正的铜管和走路贝斯，要用有授权的采样（记进 NOTES 素材台账），或在项目里扩展一份 `music.py`。只有 bass、hats、clap 时，段落交界处的音量会掉坑（`bin/vh qa scan` 报 pumping），样片在标题段以后垫了一层低 energy 的 `pad`。
- **音效**：
  - 纸拍（`pop` 降调叠 `click`）配每个字母落位；
  - 剪刀（`shutter`）配每次条被切开；
  - 纸滑（0.3 s 的短 `whoosh`）配横移。

  落点对齐画面停死的那一帧。
- **声画关系**：重音就是切点，每小节 2–4 个。片名落下前留 1 拍"屏息"：只留贝斯的一个持续音，纸片停住，背景保持极慢横移（不许声画同时停死，见 TASTE #18）。结尾用一记干的小鼓收住。

## 适合与不适合

- **适合**：03 产品宣传的 teaser 和片头；04 MV（爵士、swing、复古流行）；07 剪纸类短片；也可以给长视频做 15–30 s 的"片头 + 章节字卡"。题材上适合悬疑、侦探、追逐，"一个东西被找到"的故事。
- **不适合**：信息和数字密集的讲解（05、06 的主体段落）；温情和生活方式题材；需要真人或写实物体的片子。
- **容易被误用成**：扁平插画风（圆角、描边、渐变），或者一层"复古海报滤镜"。滤镜只是纹理，不是语法。

## 禁止项

1. 渐变、描边、圆角、发光，或者出现这 4 种纸色以外的颜色。
2. 纸片边缘按屏幕坐标逐帧重算，一动边缘就"爬"。
3. 纸片 bounce、overshoot 或橡皮筋式弹性。纸是硬的，只会滑、停、翻。
4. 一个画面里有两个主母题；朱红铺满画面却又不是整场底色。
5. 字只当标签贴在图上，不参与结构。
6. 堆砌五十年代"复古"字体，比如斜体手写体、霓虹招牌体。

## Prompt 块

```text
Visual style: mid-century cut-paper title design. Flat opaque paper shapes in four inks only: cream paper #EDE3CC, ink black #1B1916, vermilion #D5412B (the one thing that matters), ochre #DFA235. No gradients, outlines or glow. Every shape has a hand-cut scissor edge (edge noise computed once per piece, never per frame), a 2 px ground-colour gap and a small paper shadow. One motif per sequence (a bar, a circle, a silhouette fragment) keeps transforming until it assembles into the final symbol. Typography is structure: condensed geometric sans in caps (Futura Condensed ExtraBold), letters re-cut with ±1 px edge noise and jaunty ±2 px baselines; a line of credits becomes a beam, a letter O becomes a window. Pieces step on twos (15 fps), slide in over 8 frames and stop dead on the beat; camera moves and scrolling stay smooth at 30 fps; nothing bounces. Transitions: a hard cut on the brass stab, a black bar wiping left to right, circle-to-circle match cuts. Each scene has one dominant ground colour. Sound: 138 BPM minor-key big-band jazz, a paper slap on every letter landing, one held-breath beat before the title lands.
```

## 引擎做法

- 首选 HyperFrames：SVG 纸片 + GSAP，时间线按 t seek。也可以用纯 Canvas2D 写 `render(t)`；手绘类项目用 ClaudeAnimationBase 的 p5 层。
- **剪刀边**：`cutEdge(poly, seed)` 在纸片局部坐标里重采样、加噪声，结果按 piece id 缓存；逐帧只做仿射变换。
- **一拍二**：`const tStep = Math.floor(t * 15) / 15;`，只喂给纸片的姿态和位置，镜头照常用 t。
- **纸缝和投影**：先把纸片画进离屏层，用底色描一圈 2 px 外轮廓，再合成一个偏移投影。同一个剪影内部不描缝，只在关节处切 1.5 px 的细缝。
- **卡拍**：从 `music.beats.json` 读 `beats`。纸片动作的到位帧 = 拍点帧，起动帧 = 拍点前 8 帧。
- **纸纹与颗粒**：纸纹放在最上层 multiply；颗粒交给 ffmpeg 的 `noise` 滤镜（强度约 6），不画在页面里。

## 自查重点

- 任选一张移动中的纸片，取 6 帧 crop：边缘形状完全一致，只有平移和旋转。
- 1 fps 联系表：每个场景只有一个主底色、一个主母题。
- 每行字卡至少完整可读 1.2 s，不被纸片挡住一半。
- 形状匹配切：切点前后圆心和半径的差 ≤ 2 px。
- 逐帧 strip：纸片按 15 fps 步进，镜头保持 30 fps 平滑。
- 缩到 20% 看：朱红是否正好落在观众该看的那一个东西上。

## 相关资源

- `references/repos/lemo-opuscar/styles/spy-titles/STYLE.md`（LemoLab，CC BY 4.0）：同一语法的完整样片。剪刀边缓存、纸缝、一拍二、停拍这几个做法来自它；本文按 OpenVideoHarness 的规则改写了数值、禁止项和"屏息"的处理。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 里的 Shadow Cut，可以作暗场景的对照。
- `video-types/07-hand-drawn.md`（剪纸：3–5 层纸、软投影、12 fps 步进）、`video-types/03-product-promo.md`、`playbook/03-motion-design.md` §6 转场。
