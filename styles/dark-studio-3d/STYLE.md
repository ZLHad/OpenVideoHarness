# 暗棚实物 3D · dark-studio-3d

一句话：深色摄影棚里一件有分量的实物（一个零件、一台机器、一件产品），物理材质，柔光箱只在金属上留下长长的反光，两侧的轮廓光把形从黑里切出来。它会拆开、再带着重量落回去；旁边一张说明卡写着它是什么、用什么做的、有多重，数是真的。适合产品和硬件、工程原理、拆解、"这东西为什么贵/为什么重"的段落。

**怎么借**：可以借走的是暗棚的打光逻辑（主光是金属里看到的柔光箱，不是照亮一切的灯；轮廓光从后侧来；背景只留一点光的衰减），零件的"重量感"（落下按重力加速、落座只弹一下、镜头跟着一震），以及"真材实料的说明卡"（材质牌号、密度、质量，从模型的体积算出来）。下面的焦距、灯位、时长是样片的参数，供试做。不能放的是事实：说明卡上的牌号、参数、质量都要能对上来源或计算；真实产品要按真实尺寸建模或取官方模型，不臆造细节。

样片：`media/swatch.mp4`（8 s；完整视频在 Release `styles-media`，`tools/fetch_media.sh dark-studio-3d` 取回）· 封面 `media/poster.jpg`（第 3.95 秒）· 2 秒预览 `media/preview.mp4`（2.3–4.3 s）。只有横版：一件实物加一张说明卡，横画面才放得下两样。

## 样片

| 拍 | 时间 | 这一拍做什么 | 本风格的做法 |
|---|---|---|---|
| 立住世界 | 0–1.5 s | 色板和质感一眼看清；0.1 s 就有大动作 | 第一帧几乎全黑，只有轮廓光勾出齿轮、轴承、螺母的边。0.1 s 起主光的柔光箱亮起来（0.9 s），齿轮端面上的车削纹一圈圈显出来；镜头同时推近（out-cubic 1.5 s） |
| 招牌动作 | 1.5–4.5 s | 这个风格最像它的那一下 | 爆炸图：螺母、轴承、齿轮沿轴依次升起（1.5–2.4 s），镜头抬高一点看清；然后按重力一件件落回：齿轮 2.95 s 落座（一声沉响，镜头一震）、轴承 3.22 s、螺母边转边落 3.50 s；3.7 s 说明卡从左边滑进，一根引线连到齿轮的齿圈 |
| 真实字号的字 | 4.5–7 s | 标题和字幕按片子里的字号，停够读完 | 标题苹方 96 px 在左上的暗处，逐字从左边滑入；英文 Helvetica Neue Light 44 px；字幕 48 px 在下方正中。说明卡留着，转台一直在转 |
| 收住 | 7–8 s | 落定，最后一帧接回第一帧 | 卡和字退场，主光暗下去只剩轮廓光，镜头退回起点。整个装配体 8 s 里正好转了 60°：齿轮 40 齿、6 个减重孔，轴承 10 颗钢球，螺母六角，60° 对每一件都是对称的，所以最后一帧就是第一帧 |

## 学习对象

| 作品 | 年份 · 作者 | 从它身上学什么 |
|---|---|---|
| 《青椒 30 号》*Pepper No. 30* | 1930 · Edward Weston | 一件普通的东西放在暗底上，光从一个方向来，形和质感全靠明暗过渡说话。学"暗底 + 一个方向的光 = 体积" |
| 《香烟》*Cigarettes* 系列（铂金印相） | 1972 · Irving Penn；1975 年在纽约现代艺术博物馆展出 | 把最不起眼的东西当珍品拍：精确的构图、极其讲究的材质细节、冷静的距离。学"把一个零件当作品拍" |

核实：Weston 的年份和画面据多家博物馆藏品页；Penn 系列的年份、工艺和 1975 年 MoMA 展览据 MoMA 当年的新闻稿和美国国家美术馆、大都会博物馆的藏品页。

**不照搬**：不用两位摄影师的任何照片和构图；样片的零件、灯光和镜头都是自己做的。

## 视觉语法

- **色板**：

  | token | hex | 语义 |
  |---|---|---|
  | bg | `#0A0B0D` | 棚：近黑，带一点冷 |
  | text | `#ECEFF2` | 标题、卡片正文 |
  | muted | `#8E959D` | 英文副标题、卡片上的型号行 |
  | hair | `#9AA3AD` | 卡片的细边框、引线 |
  | card | `#121418` | 说明卡：烟色玻璃（78% 不透明） |
  | accent | `#C9A66B` | 卡片左边一道暖色的竖线：全片唯一的颜色 |

  材质本身的颜色来自物理：钢 `#8C9196`（金属度 1、粗糙度 0.36，加一张同心车削纹的粗糙度贴图），抛光的轴承环 `#D9DDE2`（粗糙度 0.1），发黑处理的轴和螺母 `#2B2C30`，黑色清漆的底座。
- **字体**：中文苹方（PingFang SC 600），英文 Helvetica Neue Light，数字 Avenir Next，型号行 Menlo。字都在暗处，白字不加描边。
- **构图**：实物放在画面右侧三分之一附近（用相机的 view offset 平移，不是把物体挪开），左侧留给字和说明卡；26° 的长焦，镜头比物体略高（24°）。
- **质感**：反光就是质感：主光是一块从中间向边缘衰减的柔光箱（金属平面上就是一道渐变），两侧竖条柔光箱给边缘一条亮线；环境里的地面是暗灰，所以竖直的面（齿侧）读得出是暗金属，不是一个黑洞。轻颗粒（0.03）、暗角。

## 运动语法

- **转台**：整件东西匀速转，转的角度选这件东西的对称角（样片 8 s 转 60°），循环就接得上；转速慢到观众察觉不到"在转"，只看到反光在面上滑。
- **重量**：抬起用 in-out cubic，落下按重力（位移 ∝ u²，0.2 s），落座弹 2 mm、0.2 s 就停；最重的那件落座时镜头一震（0.18 单位、14/s 衰减）。分量来自"快落、几乎不弹"，不是来自弹跳。
- **灯**：开场主光亮起、收尾主光熄灭，轮廓光一直在：灯光的起落就是这个风格的开场和收尾。
- **镜头**：慢推、慢升、不晃；没有甩镜和快速环绕。
- **转场**：从实物上长出来：拆开（爆炸图）进入内部；推近到一个零件；关灯（只剩轮廓光）换段落。不用平面转场。

## 声音语法

- **配乐**：低沉的电子脉冲，D 小调，120 BPM：`drone` 低频长音（低通 700 Hz）、`polysynth` 垫和弦、`sub808` 在小节线上打低音、`seq` 八分音符的轻脉冲；板式混响。
- **音效**：灯亮起是一口上扬的 `swoosh_tonal`；零件升起一口 `whoosh`；齿轮落座 `impact`（降低 3 个半音，hero）；轴承落座 `click`（降低 5 个半音）；螺母拧下去一声 `tick`，到底一声 `click`；说明卡滑入一口短的 `swoosh_tonal`；收尾灯灭一口 `air`。
- **声画关系**：每一次落座都对一个声音，越重越低；配乐压在下面，不抢落座的那一下。

## 适合与不适合

- **适合**：03 产品和硬件的发布片、功能演示；10 长讲解里的工程原理和拆解；02 "这东西是怎么做的"的知识短片。
- **不适合**：要表现温暖、生活气息的产品（换 `product-keynote` 的白棚或 `tabletop-miniature`）；没有实物、只有概念的题目；需要大量文字的段落。
- **容易被误用成**：满屏的发光粒子和蓝色科技光；金属一片死白或一片死黑（没有柔光箱的渐变）；零件飞来飞去没有重量。

## 常见误用及原因

1. 【底线】说明卡上的牌号、参数、质量是编的。这个风格的"高级"来自真：质量就从模型的体积乘密度算，牌号和密度查标准；真实产品的参数照抄官方规格。
2. 主光直接打亮物体，金属上看不到柔光箱：金属的样子来自它反射的东西，没有灯形的反射，金属就是灰色的塑料。
3. 没有轮廓光：暗底上的暗金属会融进背景，形就没了。
4. 弹跳太多：有分量的东西落下只弹一次、很小；弹几次就成了橡胶。
5. 镜头绕着物体快速转圈：反光会闪成一片，观众也来不及看清任何一处。
6. 物体放在画面正中、字压在物体上：实物和字各占一边。

## Prompt 块

```text
Visual style: a dark product studio (#0A0B0D) and one heavy, physically shaded object. The key light is a softbox seen
only as a long graded reflection across the flat metal faces; two tall strip boxes left and right of the line of sight
put a thin rim on the silhouette; the floor and the backdrop keep only a soft falloff of light. Materials are physical:
turned steel with concentric machining marks, polished races, black-oxide parts, a black lacquer plinth. The object
turns slowly on a turntable by one of its own symmetry angles; it comes apart along its axis in an exploded view and
falls back piece by piece under gravity, each part seating with one small bounce and a low impact, the heaviest one
shaking the camera slightly. A smoked-glass spec card with a thin warm accent line sits at the left with a leader to
the part: its name, its material grade, its density and its mass (computed from the model's volume). Long lens,
camera slightly above, the object right of centre and the type in the dark at left.
```

## 引擎做法

- **引擎：Three.js（r186）画在离屏 WebGL 画布上，2D canvas 合成卡片和字**。样片在 HyperFrames 的确定性模式里用 CPU（SwiftShader）渲：1 个 worker 渲 240 帧约 50–75 s（每帧 0.2–0.3 s，这台机器负载很高时），两个 worker 时总共约 1.5 分钟。没选 Blender（Cycles）的理由：这条路线是后面一批 3D 风格的地基，它们大多要的是可控的光和材质、能逐帧检查的字、分钟级的迭代，Three.js 都满足；路径追踪的透射、体积光、真实景深留给 Blender（`tabletop-miniature` 的路线，正式版每帧十几秒起）。
- **three.js 从哪来**：仓库里钉住的 r186 在 `engines/canvas-film/three/`（许可和逐文件哈希在它的 `NOTICE.md`），`render.sh` 搭 stage 时把它的 `build/` 复制成 `three/`；场景在 setup 里 `await import(new URL("../../three/build/three.module.js", import.meta.url).href)`。动态导入是为了 `foley.mjs` 在 Node 里读 `FOLEY` 时不去加载 three。只带 `build/`：addons 按名字导入 `three`，stage 没有 import map，所以样片自己搭了柔光箱环境，没有用 `RoomEnvironment`。
- **灯**：环境是一个暗盒子里放几块自发光的板（柔光箱，贴一张中间亮、边缘暗的衰减图），用 `PMREMGenerator.fromScene` 做成环境贴图挂到每个材质上；另有一盏投影的聚光灯（主光的阴影）、两盏方向光（轮廓）。开场和收尾只改主光和环境的强度。
- **模型**：齿轮是一条轮廓（40 个齿，直线齿侧近似渐开线）加孔，用 `ExtrudeGeometry` 挤出并倒角；轴承、轴、底座用 `LatheGeometry` 车出来；螺母是六边形挤出。全部用基本几何体建，不用别人的模型。
- **质量**：齿轮轮廓的面积（鞋带公式）减去孔，乘厚度，加上轮毂，乘 42CrMo4 的密度 7.85 g/cm³，就是卡上的 3.0 kg。
- **确定性**：一切按 t 设置（转台角度、每个零件的高度、灯的强度、镜头），每帧从头渲；`renderer.compile` 在 setup 里先编译着色器。
- **真实项目**：产品优先用官方的 AR 模型或按实测尺寸建模（`bin/vh model3d`）；HDRI 用许可清楚的（Poly Haven，CC0）；参数照抄官方规格表。

## 自查重点

- 联系表：主光亮起后，金属平面上是不是一道渐变（不是死白、不是死黑）；齿侧和边缘有没有轮廓光。
- 落座那几帧单独抽 strip：落下是加速的、落座只弹一下；镜头震动不超过两三帧。
- 说明卡上的每个数对照来源或计算过程；引线落在零件上，不落在背景上。
- 最后一帧和第一帧：转台角度是对称角（`bin/vh style check` 量循环接缝）。

## 相关资源

- `video-types/03-product-promo.md`、`playbook/08-vfx-and-motion-sources.md`、`engines/canvas-film/README.md`（Three.js 层）、`engines/blender.md`（要路径追踪时）。
- 同一家族的 `product-keynote`（白棚、明亮、发布会）：这一个是暗棚、重、冷静；`monumental-scifi` 是巨大的形和体积光，这一个是手边大小的真东西。
