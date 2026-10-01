# 合成器浪潮 · synthwave-outrun

80 年代想象中的未来：条纹落日压在地平线上，霓虹透视网格朝镜头无限滚来，铬字标题一道高光扫过，全片像从一盘录像带里放出来。适合复古科技、游戏、音乐宣传、"回到过去"主题，以及需要强节拍的片头。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

样片实况：0.0 s CRT 开机，一个亮点拉成一条线，0.1 s 画面已经上下张开三分之一。条纹落日升起，青色透视网格按拍向镜头滚动。0.8 s 起铬字标题逐字升起，铬面渐变中间有一道白色地平线带，2.0 s 一道高光扫过，1.6 和 2.8 s 在拍上各闪一个四角星芒；中文像霓虹灯管一样闪着亮起。2.0 / 2.2 / 2.4 s 三件那个年代的物件依次通电：线框磁带（大纲）→ 铬边、封面分三格的录像带封套（分镜）→ 铬边 CRT 电视正在播一段小落日（初版），之后 2.8 / 3.2 / 3.6 s 每拍亮一件。4.0 s 录像带 tracking 噪声，结束画面从地平线那条线向上下展开，4.4 s 霓虹粉的手写体 "Outrun"（300 px）落拍，落日同时上升 10 px。标签英文 40 px。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《电子世界争霸战》（Tron） | 1982 · 导演 Steven Lisberger，华特迪士尼制片厂；概念设计 Syd Mead（载具）、Moebius / Jean Giraud（服装）、Peter Lloyd（环境） | 黑底上的彩色背光线条：高反差 Kodalith 胶片逐格背光上色；颜色区分阵营；轨迹只走直线和直角 |
| 《Out Run》 | 1986 · 世嘉（Sega）街机，铃木裕设计，音乐川口博史 | 这个风格名字的来源：沿公路冲向消失点的单点透视、落日、"车载电台"式的可选配乐 |
| 80 年代喷枪铬字（唱片封套、录像带封套、电影海报，泛指，不指某一件） | 1980 年代 · 众多喷枪插画师 | 铬字的反射渐变：天蓝 → 白色地平线 → 深紫褐 → 橙；星芒高光；霓虹手写体副标题 |
| 《亡命驾驶》（Drive）片头与原声 | 2011 · 导演 Nicolas Winding Refn；配乐 Cliff Martinez，片头曲 Kavinsky《Nightcall》 | 复兴期的克制：慢速、夜城、长音合成器，霓虹粉只用在一处 |

**不照搬**：不用 Tron 的光轮车、电路纹服装和片名字体，不复刻 Out Run 的车型、HUD 和赛道，不用 Drive 片头的粉色手写片名，不出现任何真实汽车品牌。

## 视觉语法

- **色板**（颜色有语义，全片不变）：
  - 夜 `#14082E`：底色；最深处 `#0B0620`（地面、天顶）；
  - 地平线紫 `#6B2FA3`：天空底部；
  - 青 `#29E0F0`：网格和地面，代表"冷、路、前方"；
  - 洋红 `#FF2E88`：强调色，太阳底部、霓虹手写字、山脊线；
  - 橙 `#FF7A3D`、黄 `#FFD23F`：太阳上半部；
  - 铬白 `#F2ECFF`：标题和 OSD 文字；铬字渐变另用天蓝 `#5EC8FF` 和紫褐 `#3A1E4A`。
  - 只有天空、太阳、铬字三处允许渐变；别的地方一律纯色线条。
- **字体**：
  - 铬字标题：`Avenir Next Condensed` Heavy Italic → `Futura` Condensed ExtraBold（加 −12° skewX）；中文用 `Lantinghei SC` Heavy；
  - 霓虹手写副标题：`SignPainter`，一屏只写一个词，旋转 −8°；
  - 正文：`Avenir Next` Demi Bold；中文 `PingFang SC` Semibold；
  - 录像带 OSD（`PLAY ▶`、时码）：`Andale Mono` → `Menlo`，32px，全大写。
  - 样片实际用字：`Avenir Next Condensed` Heavy Italic 150px 大写铬字、`Lantinghei SC` Heavy 72px 霓虹中文、标签 `PingFang SC` Semibold 48px + `Avenir Next Condensed` DemiBold 40px、OSD `Andale Mono` 32px、结束画面 `SignPainter` 300px 霓虹粉。
- **构图**：
  - 单点透视：地平线 y = 0.55H，消失点在画面中心线上；
  - 太阳圆心在地平线上方 0.1H，半径 0.22H，被地平线截掉下缘；下半部切出 7 条横缝，缝高从 2px 递增到 18px；
  - 地面网格：17 条纵线汇向消失点，横线间距按透视递减；近处线宽 2px，远处 1px；发光半径不超过线宽的 6 倍；
  - 地平线上一条线框山脊，洋红描边；天顶 0.3H 以上撒 40–80 颗 `hash` 定位的星；
  - 铬字标题放在 y≈0.28H，宽度不超过 0.7W；OSD 放左上角安全区内。
- **质感**：录像带 + CRT：3px 周期扫描线（强度 0.15，锚定输出像素）；色度横向模糊约 7px，红色差通道右移 2px；极轻的信号噪声。tracking 噪声只在转场时出现。

## 运动语法

帧数按 30 fps 计。

- **缓动**：进场 easeOutExpo `cubic-bezier(0.16,1,0.3,1)`，出场 easeInExpo `cubic-bezier(0.7,0,0.84,0)`；spring：stiffness 220、damping 24（ζ≈0.81，约 1% 回弹），只给铬字落位。网格滚动是匀速的，这是唯一允许的线性运动。
- **网格与节拍锁定**：每一拍正好有一条横线从地平线滚到镜头前，`z_offset = (t·v) mod S`，`S / v = 60 / BPM`。
- **时长**：进场 14 帧；每个画面至少停 1.6 s；每小节（118 BPM 下约 2.03 s）发生一件新事。
- **铬字**：字母按 60 ms 间隔从下方升起，落位后一道白色高光带 20 帧扫过字面，下一个强拍上在一个字角闪一次四角星芒（6 帧）。
- **转场**：全片只用三种：录像带 tracking（6–8 帧：逐行横向错位、一条滚动的噪声带、画面上跳 4px）、地平线升起（下一场从地平线那条线向上下展开，14 帧）、闪白切（强拍上 2 帧洋红白闪，然后硬切）。
- **镜头**：向前推进（dolly）：网格滚动就是推进；另加 ±1.5° 的缓慢侧倾（8 s 一个周期），像在开车。
- **文字动画**：逐字（stagger）升起；OSD 时码按帧跳数字（`steps`）。

## 声音语法

- **配乐**：`bpm: 118`，`key: "A"`，`mode: "minor"`，和弦 `i–VI–III–VII`。签名有两样：`gated`（军鼓进一个密的混响，0.3 s 处一刀切断，80 年代的门限混响）打在反拍上；明亮的 `polysynth`（7 声部 supersaw，立体声铺开）弹 3-3-2 切分的和弦 stab，它就是主奏。其余是这一路的标配：`edm_kick` 四拍，`hihat` 十六分，八分音符八度跳的锯齿贝斯（`saw_pluck` 用 `roots` + `octaves`，`duck` 给 kick，一拍一泵），十六分琶音（`saw_pluck` + 乒乓 `delay`），`saw_pad` 长音；`space: hall`。旧 `layers` 的锯齿音色（`saw_pluck` `saw_pad`）在这里只当配角。长片里 `lead` 主旋律只在副歌出现，段落用 `riser` 推进、`impact` 开副歌、`fill` 留一拍空。
- **音效**：插入录像带的机械 `click`、tracking 时的 `glitch`、转场 `whoosh`、副歌前 `riser`、标题落位 `impact`。
- **声画关系**：卡点密：切换、闪白、星芒都在拍上（±1 帧）。开场可以先放 1–2 小节只有 `pad` 和 `arp` 的前奏，网格慢慢滚进来，鼓进来的那一拍标题落下。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：样片按 150 BPM 走（网格每拍一条线），A 小调，i–VI–III–VII 每段一个和弦：0 s 开机时是 polysynth 的 Am 长和弦、十六分琶音和 pad，没有鼓；0.8 s 铬字升起时鼓机进来：四拍 kick、反拍的 gated 军鼓（第一下在 1.2 s）、十六分 hats、被 kick 压着泵的八度锯齿贝斯，polysynth 改弹 3-3-2 的切分和弦；2.0 s 进 C 和弦，三件物件在拍上通电；4.0 s tracking 噪声那一拍鼓全停，polysynth 只留一个短和弦；4.4 s "Outrun" 落拍，gated 军鼓、kick 和 polysynth 的 G 和弦一起砸回来。拟音（`events.json`）：0.07 s 开机 `boom` 加 `glitch`，1.6 / 2.8 s 星芒各一声很轻的 `ding`，2.0 / 2.2 / 2.4 s 三件物件通电各一声 `click`，4.0 s tracking `glitch`，4.4 s "Outrun" 落拍 `impact`。
- **样片的转场音效**：`tape`：4.0 s 磁带跟踪噪声是一声倒带（`dir: up`，0.27 s），落在结束帧从地平线打开的 4.27 s，代替原来的 `glitch`。

## 适合与不适合

- 适合：`03` 复古科技或游戏类产品片头、`04` B 路线的电子乐歌词视频、`08` 带怀旧梗的快剪、`02` 讲 80 年代科技史的短片。
- 不适合：自然、人文、温情题材；需要读大量文字的讲解。它也最容易滑回社区里泛滥的"暗底 + 发光"，见禁止项第一条。

## 禁止项

- 只有"暗底 + 发光"，却没有这个时代的语法（落日、透视网格、铬字、录像带质感）：那只是又一支普通科技片；
- bloom 厚到线条糊成一片；玻璃拟态卡片、紫青渐变的 UI 面板；
- 混进蒸汽波（vaporwave）的母题：希腊石膏像、Windows 95 窗口、海豚、当装饰用的日文字；那是另一个风格；
- tracking 和 glitch 每拍都来：每个段落最多一次；
- 铬字渐变用在正文上：铬只给一个标题；
- 真实汽车品牌、真实游戏界面。

## Prompt 块

```text
STYLE: 1980s retro-futurist outrun. Night violet #14082E with #0B0620 depths and a #6B2FA3 horizon glow. One-point perspective: horizon at 0.55H, vanishing point on the centre line. A striped sunset sun (yellow #FFD23F to orange #FF7A3D to magenta #FF2E88) sits on the horizon, cut by 7 horizontal slits that widen toward the bottom. A cyan #29E0F0 wireframe ground grid rolls toward the camera, exactly one grid line per beat; thin lines, glow no wider than 6x the line width. Magenta wireframe ridge on the horizon, sparse stars.
Gradients only in the sky, the sun and the chrome title. The title is heavy condensed italic chrome (sky blue to white horizon line to dark violet-brown to orange) with a dark outline; letters rise 60ms apart, a white specular sweep crosses them, a four-point star glints on a downbeat. One neon script word at -8°. Monospace VHS on-screen display in the corner.
Everything plays from a videotape on a CRT: 3px scanlines, horizontal chroma bleed, slight red shift, faint noise. Transitions: 6–8 frames of tracking noise, a new scene opening out of the horizon line, a 2-frame flash cut on the beat.
Music: 118 BPM A minor, i–VI–III–VII, four-on-the-floor kick, a big gated-reverb snare on the backbeat, bright supersaw polysynth chord stabs, octave-pumping saw bass, 16th-note arpeggio with ping-pong delay, warm pad, a lead only in the chorus, riser into the drop. Not vaporwave: no statues, dolphins or OS windows. No real car or game brands.
```

## 引擎做法

- **首选 HyperFrames + Canvas2D**，最后一个 WebGL 录像带 pass；想要真 3D 地形时加 Three.js 层，但网格仍按下面的公式由 t 决定。
- **网格**：第 k 条横线的深度 `z_k(t) = z0 + k·S − ((v·t) mod S)`，屏幕 `y = y_h + f·h_cam / z_k`；纵线 `x = x_v + f·X_j / z`。线宽和透明度随 `1/z` 衰减。
- **太阳**：先画整圆的纵向渐变，再用 `destination-out` 挖掉 7 条横缝，最后用地平线裁掉下缘。
- **铬字**：`fillText` 用五段线性渐变（`#5EC8FF 0`、`#F2ECFF .48`、`#3A1E4A .5`、`#8B4BC2 .72`、`#FF9B5E 1`），外描 3px `#1A0B2E`；高光带是裁剪在字形内的一条白色斜矩形，x 由 `seg(t, a, b)` 决定。
- **录像带 pass**：片段着色器里做 Y/C 分离、色度横向模糊、红色差右移、扫描线（按输出像素）、噪声（以帧号为种子）。可以参考 lemo `cel-anime-80s` 的 `demo/post.js` 思路，但参数按本文。
- 颗粒另在 ffmpeg 里加：`noise=c0s=2:allf=t`，GIF 从无颗粒版本生成。

## 自查重点

- 暂停任意一帧：能不能一眼认出落日、网格、铬字、录像带四样中的至少三样？
- 用 `music.beats.json` 对照：网格横线是否每拍一条、闪白是否都在拍上；
- 放大线条：发光没有把 1px 远线糊掉；
- 数 tracking / glitch 的次数：每段最多一次；
- 画面里有没有蒸汽波母题或可识别的品牌。

## 相关资源

- `references/repos/lemo-opuscar/styles/cel-anime-80s/STYLE.md`（LemoLab，CC BY 4.0，https://creativecommons.org/licenses/by/4.0/）：同一时代的另一条路，录像带 + CRT 播放层、铬字渐变的片名卡、Y/C 色度模糊和扫描线的参数思路来自该文，本文按合成器浪潮重定。
- `references/repos/lemo-opuscar/styles/ascii-crt/STYLE.md`（单色 CRT 终端，CC BY 4.0）。
- `video-types/03-product-promo.md`、`video-types/04-lyric-music-video.md`、`playbook/08-vfx-and-motion-sources.md`（bloom、扫描线的强度档）、`playbook/04-audio.md`。
