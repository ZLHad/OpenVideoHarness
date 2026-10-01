# 桌面微缩剧场 · tabletop-miniature

一句话：把故事搬到一张桌面上。真实尺寸的家具、乐器、文具就是舞台，几何体的小角色只靠步态和两只眼睛演戏；光只来自房间里真有的灯和窗，光的颜色和方向推着时间走；镜头放在角色眼睛的高度，清晰范围只有几毫米。适合温暖、亲切、带点童话感的小故事：角色短片、产品小剧场、原声小品的 MV、知识短片里"把一个过程演成小物件"的一段。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 0 帧镜头贴着桌面，近近地对着一块睡着的毛毡小圆饼（2.2 cm 高），它身后虚着一只真实尺寸的石器茶杯，窗外深蓝，远处几盏灯化成光斑，房间里只有冷蓝的月光，窗框是深色的剪影。0.1 s 画外左上的台灯咔哒一声亮起（三帧灯丝预热，第二帧略过曝），暖光铺满桌面。0.33 s 小圆饼被惊醒：压扁一个姿势，蹦起来拉长 18% 一个姿势，落地睁眼，往右看一眼。0.3–1.2 s 镜头往后拉、往右移，三块木块依次进画；0.8 s 一张象牙色节目单卡片挂在两根线上从画面上方降下，它抬头看着，1.12 s 卡片拉到线头，弹两下、晃一晃，1.7 s 前停稳。1.2–1.53 s 它在桌上挪两小步，走到第一块木块前。2.0 / 2.4 / 2.8 s 它依次跳上三块木块："大纲"是原木，"分镜"下半截刷了红漆，"初版"整块上了红漆：漆刷了多少就是进度。前两跳镜头跟着推近、右移，这一段角色改成一拍一；在"分镜"上它停一下，抬头看红色的木块，蹲得更深，2.6 s 起跳，这一跳最快，也是一拍一，落地压得更扁。每一跳起跳一个钢琴音，落地一个高音区的钢琴音，一级比一级高。3.03 s 它回头看一眼爬过的台阶，眨一下眼，3.2 s 眯眼笑（^ ^）扭一扭，3.47 s 原地蹦一下，3.73 s 转头看灯。4.0 s 正好在最后一小节的强拍上，灯灭：房间退回月光的蓝，木块上的字还看得见，镜头还在慢慢往里靠，钢琴的属七和弦在黑里悬着；4.4 s 和弦解决，窗外天亮，晨光从窗格里斜照进来，颜色从粉走到金，纸卡被背光照透，镜头往窗户那边摇；它转向窗户，眼皮先垂下一半，4.8 s 闭上眼睛，点一下头，最后 6 帧停住。角色和道具一拍二（15 fps），每个姿势带 ±0.3 mm、±0.6° 的手放抖动；镜头和灯一拍一，像运动控制轨道；没有运动模糊。实际字体：Big Caslon Medium、Songti SC Bold。配乐 150 BPM、F 大调，只用一台小房间里的立式钢琴（明亮音色）：低音区铺底，高音区是角色的落地，底下一层房间底噪；拟音是台灯开关、毛毡落在木头上、线被拉直、纸、一只鸟。引擎是 Blender（Cycles），做法见下面的"引擎做法"。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| Wallace & Gromit 的第一部短片 *A Grand Day Out* | 1989 · Nick Park，Aardman Animations | 角色可以极简、可以不说话：Gromit 全片没有一句台词，靠动作和眼睛演戏；所有东西都是摆在布景里的实物，看得出材质 |
| 《鬼妈妈》*Coraline* | 2009 · 导演 Henry Selick，Laika；摄影 Pete Kozachik；概念设计 上杉忠弘 | 用光和色温讲故事：现实世界的颜色灰淡，"另一个世界"暖而鲜艳；微缩布景按真实光照来布光 |
| *Site Specific* 系列 | 1999 起 · Olivo Barbieri | 移轴摄影的"微缩感"：极浅的景深让真实的城市看起来像模型。尺度是靠虚化告诉观众的 |
| 一支 Claude Opus 5.5 做的钢琴短片（[X 帖子](https://x.com/kevin_t_ngo/status/2105304249060274631)） | 2026 · Kevin Ngo；作者自述用 Python 写钢琴曲、用 Python 做 3D 动画、在 Blender 里渲染 | 一件真实尺寸的乐器当舞台，几何体角色走在琴键上，按下的键就是音符；从烛光的夜到窗光的早晨就是全片的弧线 |

核实：*A Grand Day Out* 的年份、导演、工作室和 Gromit 不说话，*Coraline* 的导演、工作室、摄影、概念设计和"现实灰、另一个世界鲜"的配色，Barbieri 的系列名和起始年份，都对照了 Wikipedia 等资料（2026-10-01）。Kevin Ngo 那支片子的内容是在浏览器里逐帧看的，作者没有公开 prompt 和代码，"按下的键就是音符"是看帧得出的推测。

**不照搬**：不做 Clawd、黑猫和走在琴键上的那一场；不用 Wallace & Gromit 的黏土人物造型、*Coraline* 的纽扣眼；不复制任何作品的具体镜头。角色只用最简单的几何体。

## 视觉语法

- **尺度**：按真实尺寸建模，单位是米。角色 2–4 cm 高，舞台是真实尺寸的日常物件。景深由尺度决定：50–55 mm、f/4–4.5、对焦 30 cm 时，清晰范围只有 7–9 mm，焦平面之外的东西全化开，这就是"微缩"的来源。字和角色的脸必须放在焦平面上。
- **色板**：

  | 角色 | 颜色 | 含义 |
  |---|---|---|
  | 台灯暖光 | `#FFB067`（约 2700 K） | 有人在的时间 |
  | 夜、月光 | `#22355C`、`#7E9BD6` | 屋外，没人的时间 |
  | 晨光 | `#FF9A7A` → `#FFD08A` | 时间过去了 |
  | 胡桃木桌面 | `#6E4A2E`、`#3A2516` | 舞台 |
  | 纸、墨 | `#EFE4CC`、`#2A211C` | 印在道具上的字 |
  | 角色毛毡 | `#3F7F78` | 唯一的冷色实体，和暖光互补 |
  | 三块木头 | 原木 `#D9C29A`；下半截刷红漆；整块红漆 `#9C2C24` | 从毛坯到成品：漆刷了多少就是进度，只用一种漆色 |

  暖的实用光对冷的环境光。
- **光**：只用房间里真有的光源：台灯、蜡烛、窗户。光源可以在画外，但要说得出是哪一盏，所有阴影都指回它。光的颜色和方向变了，就是时间变了。夜里不是一片黑：月光从房间里照回来，暗部落在冷蓝的 12–20（8 位），字还读得出；没有光照到的东西（窗框）在夜里是剪影，不能比灯下的主体亮。
- **字**：印在道具上，不做浮在画面上的字幕层。卡片、标签、木块、乐谱、票根都行。英文用 Big Caslon Medium，中文用 Songti SC Bold，墨色 `#2A211C`；红漆上用奶油色 `#F2E6C8`。节目单式的双线框（外线粗、内线细，相距约 1 mm）。道具小，字就容易小：按 1080p 成片量，主标题不小于 84 px，辅助字不小于 44 px（`TASTE_CHECKLIST` 第 6 条）。样片的木块只印大字中文，英文"OUTLINE / STORYBOARD / DRAFT"在 2.8 cm 的木块上到不了 44 px，所以不印。
- **构图**：机位在角色眼睛的高度（离桌面约 3 cm），微微仰拍；桌面前景占下方 5–10%，背景是化开的墙和窗。主体沿一条斜线或台阶从左往右排。放一件真实尺寸的日常物件（茶杯、书、线轴）虚在角色身后，它告诉观众角色有多小。道具挂在角色前面时，它在画面上的位置要避开角色的运动路线：样片里卡片的下边缘按每一帧的投影算过，跳到最高时角色头顶离它还有 20 px。
- **质感**：真实材质，不加 2D 的颗粒或纸纹叠层：木纹、毛毡的绒毛、纸的纤维、漆面的清漆，都是材质本身。

## 运动语法

帧数按 30 fps 计。

- **一拍二**：角色和道具 15 fps（每两帧换一个姿势），每个姿势带 ±0.3 mm 位移、±0.6° 转角的手放抖动，抖动按姿势号哈希，同一个姿势两帧完全相同。镜头和灯 30 fps 平滑，像运动控制轨道。
- **镜头跟着角色动的时候、最快的动作，角色改一拍一**：定格动画的行规，机位一动就逐格拍，快动作也逐格拍。不这样，角色在画面上每到奇数帧就往回退（样片里第一版退了 8–16 px，看起来在抖）；最后那一跳在空中只有 3 个姿势，也一卡一卡的。只有位置和姿势改一拍一，手放抖动仍按两帧换一次。
- **没有运动模糊**：逐格拍摄的相机没有运动模糊。
- **缓动**：
  - 跳：起跳前蹲一个姿势（压到 0.88，后仰 4°）；空中每个姿势都离地，4 个姿势（8 帧，走抛物线，拉长到 1.08、向前倾 9°），爬得高的那一跳多给一个姿势；落地那个姿势压扁到 0.85，下一个姿势回弹到 1.03，再下一个停稳。连着跳时，落地的压扁就是下一跳的下蹲。少于 4 个姿势的跳看起来像瞬移。
  - 挂着的道具：降下时用 ease-in（越落越慢），到线头后上下弹、左右晃，都是闭式的阻尼正弦，1.5 s 内停稳。
  - 镜头：关键位置之间用 `cubic-bezier(0.37,0,0.63,1)`。样片的机位依次是：贴近睡着的角色（它占画面高度的四分之一）；0.3–1.2 s 往后拉、右移，把卡片和木块收进来；1.6–2.5 s 跟着角色推近 9%、横移约 3 cm；慢推，灭灯的那一拍也在慢慢往里靠；天亮时往窗户那边摇。镜头一直在动，但每一段只做一件事。
- **时长**：每一拍（0.4 s）至少一个动作：一次眨眼、一次转头、一次落地、一次晃动都算。灯一亮就要有角色的反应（醒来、抬头），而且要整个身体动，不能只换眼睛。表情之间插一个闭眼的姿势当眨眼，不要硬切。高潮前停一下：最后一跳之前站住、抬头看目标、蹲得更深，三跳不能是同一个节拍器。光的大变化（开灯、关灯）落在强拍上。灭灯的那一拍镜头也别停。结尾的光走完以后停 6 帧。
- **转场**（全片只用这 3 种）：
  - 开关灯：一拍之内整个画面的光换掉，构图不动；
  - 拉焦：焦点从前景的物件移到后面的物件，或者反过来；
  - 窗光延时：光的颜色和角度在 0.5–1 s 里走完几个小时。
- **文字动画**：字跟着道具出场：吊景降下、被翻过来、被灯照亮、被推进画面。不逐字出。

## 声音语法

- **配乐**：一件原声乐器，近距离收在小房间里（rt60 0.3–0.5 s）。角色的每个动作是一个音（起跳、落地、醒来、转头、睡着），音高跟着高度走：往上跳，音就往上走。样片的 `score.json` 只用 `piano`（`tone: bright`）：低音区带踏板铺底，起跳一个中音，落地一个不带踏板的高音，`roomtone` 一直垫在下面。两个音挨得太近（60 ms 以内）时，cue check 分不开，会把它们当成一个起音。
- **音效**：小、近、干：开关的咔哒、毛毡落在木头上的闷响、线被拉直、纸。声像跟着物体在画面上的 x。内置库里没有这类声音，样片的都在 `styles/_swatch/custom_sfx.py` 里合成（固定种子，可以逐字节重建）。
- **声画关系**：落地音和画面上落地的那一帧对齐（cue check）；起跳、醒来、转头、闭眼也各有一个音。关灯落在强拍上，之后的一拍是屏息：钢琴的属七和弦在黑里悬着，房间底噪垫着，天亮时才解决到主和弦。
- **样片的转场音效**：开关灯本身的咔哒就是转场声；天亮用 `air`（`dir: up`，0.7 s）托起来，再加一只远处的鸟。

## 适合与不适合

- **适合**：07 角色小短片；02 知识短片里把抽象过程演成小物件的一段；03 产品小剧场（用户自己的产品按真实尺寸放上桌）；04 钢琴、原声小品的 MV。
- **不适合**：数据密集、需要大量文字的段落；快剪的梗片；需要写实人物的内容；要求当天出片的项目（见下面的渲染时间）。
- **容易被误用成**：光滑的 CG 广告 3D：处处清楚、光从四面八方来、动作每帧平滑、带运动模糊。那只是"3D"，不是微缩。

## 禁止项

1. 全景深，从前到后都清楚：尺度感就没了。
2. 说不出来源的补光、从不存在的方向来的轮廓光、互相矛盾的阴影方向。
3. 浮在画面上的 2D 字幕层，或者悬在空中、不属于任何道具的标题。
4. 运动模糊；角色每帧平滑插值。
5. 照搬 Clawd、Gromit、*Coraline* 的角色造型。
6. 渲染噪点在静止区域闪烁（采样或降噪不够）。
7. 纯黑的夜：大片像素压到 0，看起来是 CG 的空洞，不是有月光的房间。

## Prompt 块

```text
Visual style: tabletop miniature, shot like stop-motion miniature photography. The set is a real-scale tabletop (a desk, a piano, a windowsill) modelled in metres; the characters are simple geometric puppets 2–4 cm tall (a felt puck, a wooden block) that act only with their gait and two bead eyes. Put one real-size everyday object (a teacup, a book, a spool) out of focus behind them so the scale reads. Camera at the puppet's eye height (about 3 cm above the table), 50–55 mm, f/4, focused at 30 cm, so only a few millimetres are sharp and the room melts into blur; keep every word and every face on the focus plane. Light comes only from practical sources in the room (a desk lamp, a candle, a window), warm 2700 K practicals against cool night ambience; changing the colour and angle of that light is how time passes (lamp clicks off, moonlight, dawn through the window bars). All text is printed on props (a playbill card with a double rule, labels on blocks), serif Latin (Big Caslon) and bold Song Chinese, dark ink; never a floating caption layer. Puppets and props move on twos (15 fps) with a sub-millimetre hand-placed jitter per pose, and on ones while the camera follows them; camera and lights move smoothly on ones like a motion-control rig; no motion blur. Hops: one crouched drawing, at least four drawings in the air on a parabola with stretch and lean, one squashed drawing on landing, a small overshoot, settled. The puppet reacts the moment the light changes; the camera follows the action in and holds still at the end. Real materials only: wood grain, felt fuzz, paper fibre, lacquer; no 2D grain overlay. Sound: one acoustic instrument recorded close in a small room (an upright piano): a pedalled low register underneath, each puppet action a dry high note that climbs as the puppet climbs, small dry foley (switch clicks, felt on wood, paper, thread), room tone underneath, a breath of silence-with-room-tone when the light goes out.
```

## 引擎做法

- **首选 Blender（Cycles）**。样片是 `swatch.py`：`build(env)` 搭场景，`apply(t, env)` 按 t 设好每个会动的属性，`styles/_swatch/blender_render.py` 逐帧调用、渲成 PNG。不打关键帧、不用 handler，所以没有运动模糊，这正是本风格要的；需要运动模糊的项目按 `engines/blender.md` 的做法逐帧采样成关键帧。
- **一拍二**：`twos(t) = floor(round(30 t) / 2) · 2 / 30`，角色和道具的姿势都从 `twos(t)` 算；镜头和灯直接用 `t`。手放抖动用 `env.hash(姿势号, i)`。
- **景深**：相机的 `dof.focus_object` 放一个空物体在角色眼睛的平面上，`aperture_fstop = 4.5`、`aperture_blades = 0`（圆形光斑）；镜头 54 mm。窗外的远灯是天空面上的 Voronoi 小亮点，约一半亮着、亮度各不相同，经过景深变成光斑。
- **光**：台灯是画外的 Spot（半径 3 cm，软影）加一盏大面光模拟它照亮房间；灯丝预热是逐帧的强度表（0.35、1.12、0.9、1.0）。月光是窗外的面光；天亮是一盏 Sun，`angle` 1.2°，仰角 9° → 18°，颜色粉 → 金，窗框挡出窗格的影子。天亮时整个场景是逆光，角色的脸会变成剪影，所以再加一盏窄的暖色 Spot 只照它的脸，代表镜头后面被晨光照亮的房间。纸卡的材质混 35% 的 Translucent，背光时会透亮。
- **字**：Blender 的文字物体，字体由 `blender_prep.py` 用 fc-match 找到本机字体文件；.ttc 里要的不是第一个字形时（宋体 Bold 是 Songti.ttc 的第 2 个），先把那一面写成单独的字体文件，放在 `out/` 里，不入库。
- **渲染时间**（M3 Max）：正式版用 CPU（每次运行逐像素相同），32 spp + OIDN，每帧 15–19 s，150 帧约 40 分钟；草稿用 Metal（20 spp，150 帧约 4 分钟）。64 spp 每帧 32–43 s，和 32 spp 并排放大看不出差别。
- **先算再渲**：动作、镜头和道具的位置都是纯 Python 函数，不用 Blender 就能逐帧投影检查遮挡、安全框和道具进画的那一帧；渲染只用来看光和材质。
- **退路**：没有 Blender 时，Three.js 加景深后处理能做出构图和动作，但软阴影、台灯在墙上的漫反射和纸的透光都会变成游戏画面的样子。只当 animatic 用。
- **许可**：调用 Blender Python API 的文件（`swatch.py`、`blender_render.py`）按 GPL-3.0-or-later 分发，文件头有 SPDX 标注；仓库其余部分是 MIT。

## 自查重点

- **焦平面**：100% 裁切看标题、标签和角色的眼睛，字边是清楚的。焦点放在角色的眼睛上，字的平面放在离它 ±3.5 mm 以内。
- **字号**：按 1080p 成片量，主标题 ≥ 84 px，辅助字 ≥ 44 px。道具上的小字最容易不够。
- **光源一致**：每一道影子都能指回一盏灯；画面里没有说不出来源的亮面。
- **一拍二**：逐帧 strip 里角色每两帧换一次姿势，而镜头每一帧都在动。两样都平滑或者都一拍二，就是错的。
- **遮挡**：挂在前景的道具不能挡住角色的运动路线。最省事的办法是不渲染就先算：用和场景同一个针孔相机模型，把道具的边和角色的头顶逐帧投影到画面上，看最小间距（样片是 20 px）。
- **闪烁**：静止区域相邻帧做差，降噪残余不能闪。
- **声音**：每个落地音和画面上落地的那一帧对齐（`bin/vh qa` 的 cue check），关灯后的屏息里不能有数字静音。

## 相关资源

- lemo-opuscar 的 `brick-toy`（LemoLab，MIT）是同一家族：桌面、微距、一拍二、真实的房间当背景。区别是它用的是有光泽的塑料积木和摄影棚的柔光箱，这里是毛毡、木头、纸这类软材质，光只用房间里的实用光，并且拿光来计时。见 `references/repos/lemo-opuscar/styles/brick-toy/STYLE.md`。
- `engines/blender.md`（Blender 的版本、色彩、安全、许可）；`styles/_swatch/README.md` 的"Blender 场景"。
- `video-types/07-hand-drawn.md`（角色小片）、`video-types/03-product-promo.md`（产品小剧场）、`playbook/08-vfx-and-motion-sources.md`（声画联动）。
