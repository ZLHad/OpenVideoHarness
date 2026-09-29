# 水墨 · ink-wash

大面积空白宣纸上，一滴墨晕开成远山，一笔枯墨就是一个动作。适合慢节奏、带哲思的叙事：寓言、人生感悟、传统文化题材，以及"从无到有"的发布片开场。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《小蝌蚪找妈妈》 | 1960 · 上海美术电影制片厂，导演特伟、钱家骏；造型取材齐白石笔下的鱼虾 | 没骨造型：一笔浓墨就是身体，边缘自然洇开；角色和背景用同一种笔墨，画面浑然一体 |
| 《牧笛》 | 1963 · 上海美术电影制片厂，导演特伟、钱家骏；无对白 | 声音做叙事线：笛声牵着情节走；小人物放在大片空白里，靠留白给出距离感 |
| 《山水情》 | 1988 · 上海美术电影制片厂，总导演特伟，导演阎善春、马克宣；美术吴山明、卓鹤君；古琴龚一 | 留白即空间；远山分三到四层淡墨叠出纵深；镜头运动跟着琴音的停顿呼吸，静比动长 |
| 《鹬蚌相争》 | 1983 · 上海美术电影制片厂，导演胡进庆；"拉毛"水墨剪纸 | 软边纸片：纸偶边缘拉出绒毛，硬边变成晕染边。代码里可以用"纸片 + 边缘晕化"便宜地做出水墨感 |

**不照搬**：不复刻蝌蚪、牧童与水牛、老琴师与少年这些角色和桥段，不描原片画面，不用片中的琴曲和笛曲。

## 视觉语法

- **色板**：墨分五色，是同一种墨在宣纸上的五档浓度。下面的 hex 是落在纸上之后的成色；实现时用一种墨色加不同不透明度 multiply 到纸上，调到接近这些成色即可。
  - 纸 `#F1EADB`（暖宣纸，底色，不用纯白）；
  - 焦墨 `#1E1B18`（书法、点苔、决定性的一笔）、浓墨 `#3A3531`（轮廓、近景）、重墨 `#5E5853`（次要线）、淡墨 `#8C8580`（山体、衣袍）、清墨 `#C9C2B6`（远山、雾）；
  - 朱砂 `#B8352A`：只给印章和全片唯一一处点睛（一条剑穗、一片枫叶），同一帧最多一处；
  - 可选点染：赭石 `#A8764A`、花青 `#5B7083`，面积各不超过画面 5%。
- **字体**：
  - 题字：`Kaiti SC` → `STKaiti`；题款、落款用 `Xingkai SC`（行楷）。竖排，放在留白里；
  - 正文、字幕：`Songti SC` → `STSong`，字幕 44–52px，墨色 `#3A3531`，不加底框；
  - 英文题跋：`Baskerville` 斜体，字距 +0.02em。
  - 样片实际用字：`Baskerville` Italic 96px（英文题跋）、`Kaiti SC` 76px 竖排（中文题字）、标签 `Kaiti SC` 50px + `Baskerville` Italic 32px、印章 `Kaiti SC` Bold 反白。
- **构图**：
  - 留白占画面 60–80%，主体偏到三分线或角落（6×6 网格的 A 列、F 列），不居中；
  - 地平线（或水面）放在 y≈0.62H；远山三层依次用清墨、淡墨、浓墨的成色（`#C9C2B6`、`#8C8580`、`#3A3531`），每层下缘化进一条横向雾带，雾带就是留白；
  - 印章 72–96px 方形，贴在题字左下，与题字共用一条竖轴。
- **质感**：宣纸纤维（长纤维 ±2% 亮度）+ 墨的湿边：晕染区外缘有一圈比内部深约 12% 的水线（tide line），宽 6–10px。飞白处露出纸色，笔触断续。不加胶片颗粒和暗角。

## 运动语法

帧数按 30 fps 计；用 24 fps 的引擎时乘 0.8。

- **缓动**：
  - 进场用 easeOutQuint `cubic-bezier(0.22,1,0.36,1)`，出场用 easeInQuint `cubic-bezier(0.64,0,0.78,0)`；
  - 墨晕半径按指数衰减：`r(t) = R·(1 − e^(−t/τ))`，τ = 0.6 s，湿墨越扩越慢；
  - 单笔笔画：起笔顿 3 帧、行笔快、收笔提 4 帧，行笔段用 easeInOutCubic；
  - 禁止 overshoot、bounce 和弹簧回弹。spring 只用过阻尼：stiffness 60、damping 18（ζ≈1.16）。
- **时长**：进场 24 帧（0.8 s）；每个画面至少停 2 s；每 3–4 s 发生一件新事。允许 1.5–3 s 的"静"，但静的时候雾要漂（≤ 8px/s），不能冻结。
- **转场**：全片只用三种：墨晕（下一场在一滴晕开的墨里长出来）、手卷横移（从右往左展开）、褪回纸白（墨迹变淡直到只剩纸，再落新墨；不是两画面 crossfade）。
- **镜头**：以横移（pan）为主，右往左，速度 ≤ 120px/s；推镜每镜不超过 5%。决定性的一笔前，镜头停住。
- **文字动画**：按笔顺书写（handwrite）。每个字 0.35–0.6 s，按真实笔顺逐笔出现，不用从左到右的矩形遮罩一扫而过。样片没有笔顺数据，退而求其次：每个字自上而下湿墨渗开、再干透（ink-bleed 滤镜），正式片子要补上笔顺中线。

## 声音语法

- **配乐**：`bin/vh music`，`bpm: 60`，`key: "A"`，`mode: "minor"`。`bin/vh music` 的中国色层在 minor 下取羽调五声，这里就是 A 羽（A C D E G，与 C 宫同一组音），幽远、偏冷。编制：`zheng` 当古琴用，段落里开 `bend: true` 得到按弦上滑；`dizi` 带气声，当箫用；`pad` 只做极轻的底，`energy ≤ 0.3`。不用鼓组。起点可以是 `bin/vh music --example zh`，把速度降到 60、删掉 `taiko` 段。
- **音效**：墨滴落纸（短"嗒" + 湿闷声）、毛笔擦纸（带通噪声，4–8 kHz）、翻卷轴的纸声、一声水滴。决定性的一笔配一次宽频"撕空气"声。内置音效库没有这些：先用 `pop`（墨滴）、`whoosh`（笔擦纸、撕空气）、`ding`（水滴）占位，成片前换成有授权的录音或自己合成，记进 NOTES 的素材台账。
- **声画关系**：卡点稀疏，一个乐句一件事。高潮前 0.5–1 s "屏息"：撤掉旋律和拨弦，只留混响尾音或一个持续的低音 `pad` 垫着（音量降 10–12 dB），然后一记决定性的拨弦或笛音落在那一笔上（样片的做法：屏息段只留一声极轻的 `bell` 余音加 `pad`，4.0 s 落下的墨滴对上 `zheng` 和 `bell`）。绝不做成数字静音（`TASTE_CHECKLIST` #18，`bin/vh qa scan` 会查）。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：150 BPM 记谱、半速的感觉，A 羽；古筝拨弦和竹笛长音，3.2–4.0 s 屏息只留 `pad` 和一声极轻的 `bell` 余音，4.0 s 墨滴落下时 `zheng` + `bell` 一齐落拍。

## 适合与不适合

- 适合：`07` 手绘叙事、`04` A 路线的慢歌 MV、`06` 人文社科类论文的章节过场、`03` 发布片的冷开场（一滴墨长成产品轮廓）。
- 不适合：信息密度高的讲解、大量数字和 UI 截图、快节奏卡点。硬套会变成"水墨贴图 + PPT"。

## 禁止项

- 墨色铺满画面，留白不到 50%；
- 用线性 alpha 渐变或高斯模糊冒充墨晕：墨晕必须有不规则边缘和水线；
- 一帧里出现两处以上朱红，或把朱红当主色；
- 水墨上叠霓虹、bloom、镜头光晕、3D 透视；
- 把"东方"符号堆在一起：太极图、灯笼、龙、熊猫、竹林同框，或用笔画模仿汉字的英文花体字（chop suey 字体）；
- 印章里乱刻字：要么刻真实可读的字，要么只做无字的朱红方块。

## Prompt 块

```text
STYLE: Chinese ink wash on warm rice paper (#F1EADB). Everything is one ink at five densities, multiplied onto the paper (resulting tones #1E1B18, #3A3531, #5E5853, #8C8580, #C9C2B6); the only colour is a vermilion seal #B8352A, at most once per frame.
Leave 60–80% of the frame as empty paper; subjects sit off-centre on the thirds. Distant mountains in three pale layers with horizontal mist bands between them; horizon at 0.62H.
Forms are boneless brush strokes: a loaded stroke whose dark edge is the contour, wet washes that bleed with a darker tide line, dry fast strokes that break into flying white.
Motion is slow and breathes: easeOutQuint in, no overshoot, ink blooms that slow down exponentially, 2s minimum holds, a held breath before one decisive stroke.
Transitions: an ink drop blooming into the next scene, a right-to-left handscroll pan, or ink fading back to bare paper. No crossfades.
Titles are written stroke by stroke in correct stroke order, vertical, in the empty paper, with a seal. Music: slow plucked zither and breathy low flute in a pentatonic mode, 60 BPM; before the climax the melody drops out over a quiet sustained drone (never digital silence), then one decisive pluck.
```

## 引擎做法

- **首选 ClaudeAnimationBase（p5.brush）**：远山和雾用 `paint(pts, { fill, fillOp, bleed: .2–.3, tex: .6–.8, ink: null })`；飞白用 `inkLine(pts, sw, '#1E1B18', 'dry')`；角色用淡墨 `wash` 加浓墨描边。每层先 `boilSeed(key)`，远山静止时不能 boil。
- **需要更浓的笔墨**时，照 lemo 的做法自写 Canvas2D 笔刷：中线（Catmull-Rom）× 压力曲线 × 4–60 根鬃毛轨迹，鬃毛的断点用沿"归一化弧长"的长尺度噪声，这样一拍二重画时飞白不会爬动。湿层和干层分两张画布，湿层做 12 点 Poisson 模糊（约 5px）+ 边缘色素堆积（小模糊减大模糊）。
- **墨晕转场**：`mask(p) = d(p)·(0.62 + 0.8·fbm(p·s)) < r(t)`，fbm 用 `hash(i)` 种子；在 `r(t)` 内外 8px 的环带里压暗 12% 做水线。全部是 t 的纯函数。
- **笔顺书写**：拿 `Kaiti SC` 的字形做骨架参考，手写每一笔的中线点列和顺序；不要用字形轮廓去裁笔触（交叉处会出缺口）。
- 手卷横移用单一的世界坐标，字幕等屏幕层画之前重置 transform。

## 自查重点

- 抽 3 帧算"纸色像素"占比（亮度 ≥ 纸色 − 8）：必须 ≥ 60%；
- 同一帧能数出至少 3 档墨色吗？只有一档就成了剪影；
- 墨晕边缘放大看（`--crop`）：有没有水线、有没有规则圆形；
- 静止的远山和字在相邻两帧是否逐像素相同（boil 只给运动物体）；
- 每帧朱红处数 ≤ 1；"屏息"段落的底垫是否一直在（`bin/vh qa scan` 不能报数字静音或掉音）。

## 相关资源

- `references/repos/lemo-opuscar/styles/ink-wash/STYLE.md`（LemoLab，CC BY 4.0，https://creativecommons.org/licenses/by/4.0/）。本文为重写：墨分五色的档位、湿干分层、归一化弧长鬃毛噪声和墨晕 mask 的思路改编自该文，数值和规则按本仓库重新定过。
- `references/repos/story-to-handdrawn-video/references/handdrawn-style-library.json` 的 `ink-wash`（水墨写意）配方，MIT。
- `video-types/07-hand-drawn.md`、`engines/ClaudeAnimationBase/ANIMATION_GUIDE.md`、`playbook/03-motion-design.md`、`playbook/04-audio.md`。
- 相近预设：`styles/silhouette-papercut/`（纸片分层）、`styles/watercolor-pastoral/`（同一引擎的水彩用法）。
