# 暗棚实物 3D · dark-studio-3d

一句话：深色摄影棚里一件有分量的实物（一个零件、一台机器、一件产品），按真实尺寸路径追踪：金属里映着柔光箱和旁边的零件，零件落在台面上有柔和的接触阴影，浅景深的焦点跟着动作走，背后的轮廓光把形从黑里切出来。它会拆开、再带着重量落回去；旁边一张说明卡写着它是什么、用什么做的、有多重，数是真的。适合产品和硬件、工程原理、拆解、"这东西为什么贵/为什么重"的段落。

**怎么借**：暗棚里的金属是靠它映出来的东西被看见的：主光是金属里那一块柔光箱，轮廓光从后侧把形切出来，背景只留一点光的衰减。零件要有分量：落下越来越快，落座只弹一下，最重的那件让镜头跟着一震。旁边的说明卡写真材实料，质量从模型的体积乘密度算。焦距、灯位、时长照样片试；卡上的牌号和参数要查得到出处。

样片：`media/swatch.mp4`（8 s；完整视频在 Release `styles-media`，`tools/fetch_media.sh dark-studio-3d` 取回）· 封面 `media/poster.jpg`（第 3.95 秒）· 2 秒预览 `media/preview.mp4`（2.3–4.3 s）。只有横版：一件实物加一张说明卡，横画面才放得下两样。Blender（Cycles）场景 `swatch.py`。

## 样片

| 拍 | 时间 | 本风格的做法 |
|---|---|---|
| 立住世界 | 0–1.5 s | 第一帧只有轮廓光和背后的一道勾边，齿轮、轴承、螺母立在黑色的底座上。0.1 s 起主光的柔光箱亮起来（0.9 s），齿轮端面上一圈圈车削纹的各向异性反光显出来；镜头同时推近（1.85 → 1.45 m，out-cubic 1.5 s） |
| 招牌动作 | 1.5–4.5 s | 爆炸图：螺母、轴承、齿轮沿轴依次升起（1.5–2.4 s），镜头抬高一点看清；然后按重力一件件落回：齿轮 2.95 s 落座（一声沉响，镜头一震）、轴承 3.22 s、螺母边转边落 3.50 s，焦点在螺母落座时从齿圈拉到螺母、再拉回来；3.7 s 说明卡出现，一根引线连到齿轮的齿 |
| 真实字号的字 | 4.5–7 s | 标题苹方 96 px 在左上的暗处，英文 Helvetica Neue Light 44 px；字幕 48 px 放在左下，说明卡下方（实物占着画面右侧和下方）。说明卡留着，转台一直在转 |
| 收住 | 7–8 s | 卡和字退场，主光暗下去只剩轮廓光，镜头退回起点。整个装配体 8 s 里正好转了 60°：齿轮 40 齿、6 个减重孔，轴承 10 颗钢球，螺母六角，60° 对每一件都是对称的，所以最后一帧就是第一帧 |

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

  材质本身的颜色来自物理：钢（金属度 1、粗糙度 0.26，各向异性 0.6，切线绕轴：车削纹的反光是一圈圈的），抛光的轴承环和钢球（粗糙度 0.07），发黑处理的轴和螺母，半光的黑色底座，哑光的黑色立柱。
- **字体**：中文苹方（PingFang SC 600），英文 Helvetica Neue Light，数字 Avenir Next，型号行 Menlo。字都在暗处，白字不加描边。
- **构图**：实物放在画面右侧三分之一附近（用镜头的平移 shift，不是把物体挪开），左侧留给字和说明卡；105 mm 的长焦、f/4，镜头比物体略高（24°）。底座放在一根往下伸出画框的黑色立柱上，地面远在画外：这样画面左下没有任何东西挡在字前面。
- **质感**：反光就是质感：主光是右后方的一块柔光箱（平面上是一道渐变），顶上一条长灯给倒角，左右两条竖灯给边缘一条亮线，背后一盏小灯（kicker）把齿形从暗底里勾出来，背景板上一团很淡的光衰减。路径追踪：零件互相映着，钢球里映着齿轮，孔里看得见底座。

## 运动语法

- **转台**：整件东西匀速转，转的角度选这件东西的对称角（样片 8 s 转 60°），循环就接得上；转速慢到观众察觉不到"在转"，只看到反光在面上滑。
- **重量**：抬起用 in-out cubic，落下按重力（位移 ∝ u²，0.2 s），落座弹 2 mm、0.2 s 就停；最重的那件落座时镜头一震（0.18 单位、14/s 衰减）。分量来自"快落、几乎不弹"，不是来自弹跳。
- **灯**：开场主光亮起、收尾主光熄灭，轮廓光一直在：灯光的起落就是这个风格的开场和收尾。
- **镜头**：慢推、慢升、不晃；没有甩镜和快速环绕。焦点跟着动作：平时在齿轮前沿的齿上，螺母落座时拉到螺母（0.3 s），说明卡出现前拉回来。
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

1. 【底线】说明卡上的牌号、参数、质量是编的。这个风格的"高级"来自真：质量从模型的体积乘密度算，牌号和密度查标准，真实产品的参数照抄官方规格。
2. **金属像灰色的塑料**：主光直接把物体照亮了，金属里却看不到灯。把主光挪到金属会把它映进来的方向（相机的镜像方向），给柔光箱一个从中间向边缘的衰减；再在背后放一盏小灯，形就从暗底里切出来了。
3. **零件像橡胶**：弹了好几下，或者匀速落下。让它越落越快，落座只弹一次、两三毫米，最重的那件带镜头一震。
4. **看不清，也看不出是真的**：镜头绕着物体快速转圈，或者字压在物体上。转台慢到察觉不到在转，只看反光在面上滑；实物和字各占一边，焦点跟着动作走。

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

- **引擎：Blender（Cycles）路径追踪**，场景是 `swatch.py`（`styles/_swatch/README.md` 的"Blender 场景"，`tabletop-miniature` 是另一个样板）。正式版 CPU 32 spp、自适应阈值 0.02、OIDN 降噪：这台 M3 Max 每帧 12–27 s（中位数 16.6 s），240 帧 70 分钟；草稿走 GPU，每帧约 3–5 s。确定性按仓库的口径：CPU 上逐像素相同。
- **为什么不用 Three.js**：先用 Three.js 做了一版（离屏 WebGL，SwiftShader 每帧 0.3 s），又加了逐帧的立方体贴图反射、模糊的接触阴影和景深后处理（每帧 1.2 s），和 Cycles 的同一套零件各渲几帧比过：光栅化的反射、接触阴影和景深都是近似，零件之间互相映照、孔里的底座、钢球里的齿轮这些"真"的东西做不出来。Three.js 适合卡通渲染、霓虹、点云这类不靠真实光的 3D；要"实物"的高级感走 Cycles。
- **字在场景里**：说明卡、标题、字幕是文字曲线和面片，挂在一个跟着相机走的空物体上，放在对焦距离处（所以清楚），只对相机光线可见（不投影、不进反射、不照亮别的东西），按屏幕像素排版：1 单位 = 1920 宽画面里的 1 px。所以底座下面不能有地面挡在对焦距离之前，画面左下要空着。`bin/vh style check --text` 对 Blender 场景只量读时（`TEXTS`），安全框、遮挡、对比度要在帧上看。
- **引线**：一根细长的方块，一头在说明卡的右边，一头在齿轮前沿的一个齿上（随转台转），两头都在对焦面附近，所以都清楚。
- **模型**：齿轮是一条轮廓（40 个齿，直线齿侧近似渐开线）挤出成柱体，布尔减去轴孔和 6 个减重孔，倒角修改器给每条边 0.9 mm 的倒角；轴承、轴、底座、立柱按截面车出来；螺母是六边形挤出、打孔、倒角。全部用基本几何体建，不用别人的模型。
- **质量**：齿轮轮廓的面积（鞋带公式）减去孔，乘厚度，加上轮毂，乘 42CrMo4 的密度 7.85 g/cm³，就是卡上的 3.0 kg（`swatch.py` 的 `gear_mass`）。
- **真实项目**：产品优先用官方的 AR 模型或按实测尺寸建模（`bin/vh model3d`）；HDRI 用许可清楚的（Poly Haven，CC0）；参数照抄官方规格表。

## 自查重点

- 联系表：主光亮起后，金属平面上是不是一道渐变（不是死白、不是死黑）；齿侧和边缘有没有轮廓光；字前面有没有东西挡着（Blender 场景的字 textcheck 看不见）。
- 落座那几帧单独抽 strip：落下是加速的、落座只弹一下；镜头震动不超过两三帧。
- 说明卡上的每个数对照来源或计算过程；引线落在零件上，不落在背景上。
- 最后一帧和第一帧：转台角度是对称角（`bin/vh style check` 量循环接缝）。

## 相关资源

- `video-types/03-product-promo.md`、`playbook/08-vfx-and-motion-sources.md`、`engines/canvas-film/README.md`（Three.js 层）、`engines/blender.md`（要路径追踪时）。
- 同一家族的 `product-keynote`（白棚、明亮、发布会）：这一个是暗棚、重、冷静；`monumental-scifi` 是巨大的形和体积光，这一个是手边大小的真东西。
