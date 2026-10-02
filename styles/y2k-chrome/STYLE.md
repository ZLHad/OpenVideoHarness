# Y2K 铬面 · y2k-chrome

一句话：千禧年前后想象中的"未来科技"，流行的那一路。一团会变形的液态铬是主角，它映着一间看不见的摄影棚（深蓝的天、银色的地平线、暗紫的地），在酸性黄的地上跳、吐字、变形；旁边是半透明的果冻塑料、白边模切贴纸和一两个游戏小标签。进场带弹跳和过冲，全踩在拍上。适合品牌片和 showreel、科技推特风的快剪、流行 MV、游戏预告。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐和 `events.json` 拟音）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：第 0 帧一团液态铬正砸在酸性黄的地上，压扁，上方几道下落线，一圈冲击环外扩，一声铁砧。它往下弹一跳，0.4 s 落地，把第一个词的水滴溅上天；左上 SCORE 胶囊弹下来。它鼓一下，把其余字母一个个"吐"出去：水滴飞到位置上膨胀成充气铬字，过冲约 25%，四个词落在 0.8 / 1.0 / 1.2 / 1.4 s 的八分音符上。吐完它只剩直径约 110 px 的一小团，1.8 s 跳到左边歇着；1.6 s 中文贴纸从右下转着飞进来，拍在标题下方。2.0 / 2.2 / 2.4 s 三块关卡砖从地上弹出来，铬团跟着每一下点一下头：1-1 大纲是青色果冻，1-2 分镜是品红果冻，1-3 初版是银色的铬，上面一台小显示器，屏幕里就是这团铬：越接近成品越亮。2.8 / 3.2 / 3.6 s 铬团在拍上依次跳到三块砖上，和砖一起压扁，"啵"一声橡皮似的闷响一次比一次高，小星炸开，砖角拍上 CLEAR 贴纸（1-3 的贴在左下角，它的上边已经有关卡号和铬团），SCORE 加 1000。从 2.0 s 起摄影棚每拍左右摆一下，铬面高光跟着滑；3.62 s 一个小跳从左到右跑过标题。4.0 s 强拍上一根斜铬管从右上角切进来，像刮水器一样往左刮，把铬团推着卷了进去，管面反光和管脊上的闪光跟着跑；管后是一张干净的酸性黄，铬团从管子背后掉出来落在中央，鼓起来，4.4 s 炸成充气铬字"Y2K"，4.6 s 一张 CHROME 贴纸拍在右下，4.8 s 闪一下。实际字体：Arial Rounded MT Bold（描粗后"充气"）、Yuanti SC Bold。配乐 150 BPM、A 大调的千禧泡泡糖舞曲。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| FunTech Showreel 2026（[X 帖子](https://x.com/tkm_hmng8/status/2105255710531674358)，拆解见 `cases/oneshot-five.md` 第 4 节） | 2026-09-30 · ハシモトタクマ（FunTech） | 一个铬面角色和一个充气铬字标贯穿十几个风格世界，贴纸和游戏 HUD 当点缀：画面怎么换，观众都知道看的是同一个主角 |
| *Wipeout* | 1995 · Psygnosis（PlayStation）；封面、说明书、游戏内字体和各虚构车队的品牌由谢菲尔德的 The Designers Republic 设计 | 锐舞年代的未来主义品牌：logo 当图标用，游戏界面本身就是平面设计 |
| Mac OS X 的 Aqua 界面 | 2000-01-05 在旧金山 Macworld Expo 发布 · Apple | 水滴一样的组件：反光、半透明；Jobs 说过设计目标之一是让人看了想舔一口。样片的果冻砖就学这个 |

核实：事实以协调方 2026-10-02 核过的为准；Jobs 那句话是转述。**不照搬**：不用 FunTech 的头盔吉祥物和字标、*Wipeout* 的车队 logo 和字体、Aqua 的窗口按钮和 Dock；FunTech 片尾前约 1 s 的真静音也不学（本仓库底线：片中不出现数字静音）。

## 视觉语法

下面是样片的做法和理由。数字是样片的值，换题材时按理由调。

- **一个铬角色贯穿全片**（从 FunTech 学的那一条）：样片的铬团砸地、吐字、跳关、被卷走、再变成片尾的字。换成铬字标或吉祥物也行，要从头跟到尾。
- **三种材质，一个比一个亮**：哑光的地、半透明果冻、全反射的铬。样片拿它讲进度：大纲、分镜是塑料，初版是铬。
- **色板**（样片）：

  | 角色 | 颜色 | 含义 |
  |---|---|---|
  | 地 · 酸性黄 | `#E4FF1A`，边缘 `#C9EA00`，中间提亮 | 舞台，从头到尾只有这一种地色 |
  | 墨 | `#0E0D16` | 字、胶囊、铬的描边 |
  | 热品红 | `#FF2BB0` | 分镜砖、贴纸上的字、铬最底下那一道细边 |
  | 电光青 | `#00D2FF` | 大纲砖、小星 |
  | 贴纸白 | `#FCFCF7` | 模切贴纸；不用纯白 |
  | 铬的天 | `#1838FF` → `#59C8FF` → `#E6FAFF` → 银 `#C6CCD4` | 铬面朝上的部分，越近地平线越银 |
  | 铬的地 | 一道黑线 `#0D0B16` → 暗紫（夜色和品红约七三开）→ 底边一道热品红 | 铬面朝下的部分；标题字里只占下面约三分之一 |

  三个饱和色同时出现是这个语域本身（`TASTE_CHECKLIST` 第 9、10 条按覆盖处理）。约束放在别处：每种颜色只管一类东西，地只有一种颜色，铬本身大多是银、蓝和深色。白底、黑底也成立。
- **铬是反射出来的**：朝上映天，朝下映地，正对镜头映地平线附近。所以铬的语法是"它反射的那间屋子"：一条硬地平线（一道白线、一段银）、下面一道黑线、一两块柔光箱、一块黑旗。铬的地要和背景反差大、有层次（见"容易翻车"第 3 条）。
- **字**：英文 Arial Rounded MT Bold，描一圈字号 7.5% 的圆角描边再"充气"；铬字 180 px，两行，一行最多两个词。中文 Yuanti SC Bold（macOS 按需下载的字体，没有时回落 PingFang SC），黑字印在模切贴纸上。必读的长句放贴纸上，铬留给短而大的词。
- **字号按"在哪看"定**（`playbook/03-motion-design.md` 第 4 节，1080p 合成里的 px，这条是底线）：样片按 `desktop` 做，主标题 ≥ 84、辅助和标签 ≥ 44：铬字 180、中文贴纸 70、砖下标签 56、关卡号和 CLEAR 48、SCORE 44 / 数字 52、片尾 CHROME 64。推荐用法里的 X showreel、梗图快剪多半是横屏放进手机信息流（`feed`），那一档主标题 ≥ 150、贴纸和标签 ≥ 80：要么把标签砍到一两个、放大到 80 以上，要么另出竖版。
- **贴纸**：文字描一圈字号 63% 的白色粗描边，加一块垫底的圆角矩形和一个偏移的软影，歪 3–8°。
- **游戏标签少而真**：样片只留一个 SCORE（真的在数铬团落了几次）和砖上的关卡号、CLEAR。标签一多就成了"游戏系统"，和 `pixel-16bit` 撞；身份在铬和那团液体。
- **构图与质感**：居中的海报构图，上面两行铬字，中间一张斜贴纸，下面一排砖；满、挤、叠也成立，但铬字周围留出影子和一点空。不加颗粒：会让铬变脏、码率上涨。

## 运动语法

- **弹跳是这个语域的一部分**（`TASTE_CHECKLIST` 第 12 条按覆盖处理）：字母 `w 26, ζ 0.38`（约 27% 过冲），砖 `w 22, ζ 0.4`，铬团落地是 0.11 s 衰减、4.2 Hz 的压扁振荡。想更"高级"（发布会、Aqua 那种），ζ 调到 0.6 以上。压扁守体积、锚在底边，看起来是真落在地上。
- **一切踩拍，但错开**：大动作都在拍或八分音符上，同一时刻大幅过冲的最好只有一个；拍与拍之间水滴在飞、高光在滑、分数在跳。
- **液态铬可以变形**：水滴和字、铬团和铬砖在同一张高度场里，挨近了像液体一样连起来：吐字、合并、被卷走、重新长出来，是这个风格最有辨识度的动作。
- **高光要动，但别转圈**：摄影棚每拍左右摆 0.15 弧度、0.18 s 到位，所有铬面的高光一齐滑。一直往一个方向转，大块平面会整块转进黑旗或柔光箱，一拍黑一拍白。
- **转场**：招牌是铬管刮屏：倾斜约 29° 的铬管 0.6 s 从右刮到左（`cubic-bezier(0.37,0,0.63,1)`），管子就是新旧画面的分界线，扫过时管面反光跟着跑。同语系的还有：一团铬压扁铺满再弹开、撕掉贴纸露出下一场、硬切。

## 声音语法

- **配乐**：千禧年泡泡糖舞曲（eurodance 一路）。样片 150 BPM、A 大调，I–V–vi–IV–I，小节 2 + 3 + 3 + 2 + 3 拍（`meters`），段落落在 0.8 / 2.0 / 3.2 / 4.0 s：`edm_kick` 四拍子、`clap`、`hihat` 反拍开镲、`sq_bass` 反拍八度贝斯、`organ` 浩室风琴切分和弦、`pulse` 在铬团落到砖上时弹"金币"（只给第一个音标 `hit`）、`glockenspiel` 撒高音、`strings` 垫底；`metal` 铁砧和 `sub808` 只在 0 s 和 4.0 s 各来一下，铁砧给砸地补上手机放得出的 1–4 kHz 起音。和 `synthwave-outrun` 分开：那边小调、门限军鼓、超锯齿；这边大调、风琴、方波、芯片音、金属。
- **音效**：`impact` + `click`（砸地）、`pop`（小东西：弹跳、词、砖弹出、"Y2K"，按动作升降调）、`swoosh_tonal` 塑成 0.12 s 往下滑的闷音（铬团落到砖上，中心 360 → 450 → 560 Hz 一次比一次高，峰值在接触后约 60 ms、压得最扁时）、`paper`（拍贴纸）、`swoosh_tonal`（溅水滴；铬管 0.5 s 从右扫到左，峰值在过中线的 4.3 s）、`shimmer`（片尾闪光），声像按物体的 x。几乎每拍都有一个看得见的动作和一个听得见的声音，音效比音乐低约 13 dB；真要停，留着弦乐和贝斯，不做成数字静音。

## 适合与不适合

- **适合**：03 品牌片、showreel；08 科技推特风、梗图快剪；04 流行、电子 MV；游戏预告、把功能做成关卡的 App 介绍。
- **不适合**：严肃、悲伤、需要信任感的题材；大段文字的讲解；写实人物。
- **容易被误用成**：暗底霓虹（`synthwave-outrun`）；网点、拟声字、漫画格（`halftone-comic`，颜色和贴纸相近，区别是这里有真反射的铬和一个液体角色）；给字加个金属渐变就叫铬。

## 容易翻车的地方

下面这些会让它变成"廉价的金属字"或"一锅乱炖"。故意反着做也可以，但要知道换来了什么。

1. 铬用线性渐变涂出来：没有地平线和高光，像灰色塑料；一动起来更假，高光不跟着形状走。
2. 铬面上的高光完全静止：看两秒就当它是贴图。至少让摄影棚在拍上摆一下。
3. 铬的地选错颜色：和背景同色，字的下半截消失；一整片饱和色，铬变成糖；只有暗色没有层次，像每个字下面叠了个错位的副本。要黑线、深色、底边一道亮色，再加墨色描边。
4. 地平线跟着每一笔走：充气字每个转角都会挂下一条"舌头"，暗色也会占掉半个字。在标题行上把仰角和屏幕空间的高度混一下（样片 0.82），地平线就横穿整行字、落在约三分之二高处。
5. 摄影棚里放细长灯条：小字上是漂亮的高光，大铬团上就成了白杠和黑斜线。
6. 角色只在开头出现：铬团吐完字就消失，后面换成一个通用的鼠标箭头，片子就散了。
7. 同时弹、三色平均分配、游戏标签越加越多：成了果冻锅，也会和 `halftone-comic`、`pixel-16bit` 撞。

## Prompt 块

```text
Visual style: millennium pop-tech (1999–2001) carried by one character, a blob of liquid chrome that lands, spits droplets that swell into inflated chrome letters, hops through the scene on the beat, gets swept away and reforms as the end title. Chrome is a real reflection of a simple studio: deep blue above, silver and a white line at a hard horizon that runs straight through each line of letters, a black line, dark purple below, hot pink only as a thin bottom edge, one or two soft oval highlights, a thin ink outline; the studio swings a little on each beat so highlights slide. One flat saturated background (acid yellow, white or black); cyan and magenta only as accents. Glossy translucent candy-plastic shapes and white die-cut stickers at a few degrees (readable sentences on stickers, chrome for short big words); few game labels, all carrying real state. Rounded heavy type made puffy before it turns to chrome; text sized for the viewing tier (secondary text at least 44 px at 1080p on desktop, 80 px for horizontal video in a phone feed). Toy-like motion on the beat: 20–30% overshoot, volume-keeping squash anchored on the floor, staggered; a tilted chrome tube wiping across like a squeegee is the signature transition; no motion blur, no grain. Sound: bright major-key bubblegum dance near 150 BPM (four-on-the-floor kick, claps, off-beat open hats and octave bass, house-organ stabs, chip coin blips when something scores, a string bed so it never goes silent), a metallic anvil on the two biggest hits, a short rubbery squash rising in pitch on each landing, pops for small things, a paper slap for stickers, a tonal metallic swoosh for the wipe.
```

## 引擎做法

- **HyperFrames + Canvas2D，铬是 `lib.shader` 的一个片元着色器**。先把铬物体画进一张"场"画布：R 是覆盖（模糊 3 px，着色器按 0.5 取阈值，字角变圆，挨近的形状像液体一样连起来），B 是斜面高度（模糊 6 px，按 0.2 再切一次得到墨色描边），G 是大的鼓起（模糊 14 px，水滴另画球面渐变）。着色器用差分求梯度（G 取 ±5、±8 px，B 取 ±2、±3.5 px 两组平均，8-bit 台阶就平均掉了），得到法线，按反射方向查程序生成的摄影棚（天、银、白线、±0.012 的抗锯齿地平线、黑线、暗紫、底边品红、椭圆柔光箱、软边黑旗）；标题行上仰角和屏幕空间的高度项按 0.82 混合，地平线横穿每一行字、落在约三分之二高处。输出带 alpha 合到画布上，之前画一层偏移的橄榄色软影。
- **大形状解析地算**：铬团（带三瓣、五瓣起伏的椭圆球面）和铬管（圆柱截面）的高度在着色器里按公式算，否则 8-bit 场在 600 px 的面上会出等高线；uv 夹在离边 24 px 以内，碰到画面边缘的铬不会多出假高光。
- **铬团**的每个状态都是 t 的纯函数：一串预先写好的跳跃（起跳前蹲、空中拉长、落地压扁），吐字时和字同一个 pass（水滴能连上），之后单独一个 pass、画在中文贴纸后面；被管子前沿推着缩没，在结束画面里从管子背后长出来再炸成字。
- **转场**：铬管中心线 `x = X(t) + tan(0.5)·(y − 540)`，X 从 2320 走到 −482，管后的半平面画结束画面；三个 pass 共用一个 shader，按顺序渲、渲完立刻画上去。`T` 表同时给画面和 `FOLEY`（`foley.mjs` 生成 `events.json`）。
- **成本**（M3 Max，SwiftShader）：正式渲染整条流程约 40 s，`determinism.sh` 150/150 帧逐字节相同。

## 自查重点

- **像不像铬**：100% 裁切一个字母，要看到天、一条横着的硬地平线（白线和银）、暗带、底边一道细亮色、至少一块高光；缩到 640 px 宽时是"金属"，不是"蓝粉糖"。
- **角色在不在**：每一秒都能指出铬团在哪儿、在干什么。
- **字号**：按观看档量 1080p 成片里的 px（`desktop` 辅助 ≥ 44，`feed` 辅助 ≥ 80）。
- **遮挡**：跳跃的弧线、贴纸、角标和 CLEAR 有没有压住必读的字。
- **高光动没动**：相邻两拍的铬面高光位置不一样，大块平面不跟着一拍黑一拍白。
- **声音**：落点都在拍上（`bin/vh qa` 的 cue check）；砸地和换场要有 1–4 kHz 的起音；片中没有数字静音。

## 相关资源

- `references/repos/lemo-opuscar/styles/` 里的 `game-show`（踩拍的玩具感和贴纸横幅，全是平涂矢量）和 `glass-product`（自发光条状面拼的摄影棚当反射环境），LemoLab，MIT。
- 本库里容易混的：`synthwave-outrun`、`halftone-comic`、`pixel-16bit`。
- `cases/oneshot-five.md` 第 4 节；`video-types/03-product-promo.md`、`08-brutalist-meme.md`、`04-lyric-music-video.md`；`playbook/03-motion-design.md` 第 4 节（字号分档）；`playbook/04-audio.md`。
