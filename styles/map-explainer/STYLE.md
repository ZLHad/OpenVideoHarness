# 立体地图解说 · map-explainer

一句话：一张晕渲地形图：山脉被西北方的光照出立体，河流沿谷地流进海里，浅海一圈淡青。镜头从高处看全境，然后推近、压低，地形立起来；一条路线沿河而上、翻过垭口、下到湖边，一段一段长出来，每一站标上编号和从地形上读出的海拔。标题放在地图的图例框里。适合地理、历史上的行军和迁徙、旅行路线、物流和航线，任何"在哪里、怎么走过去"的讲解。

**怎么借**：先把地形画对：光从西北来，越高对比越强，阴影偏冷，颜色压低，山自己就立起来了。然后让路线一段一段长，每段一个动作、一个声音、一个站点，站点上写一个真实的数；标题放进地图自己的图例框。光照角度、夸张系数、镜头参数照样片试；地名、海拔、距离要来自数据，国界不需要就不画。

样片：`media/swatch.mp4`（8 s；完整视频在 Release `styles-media`，`tools/fetch_media.sh map-explainer` 取回）· 竖版 `media/swatch-portrait.mp4` · 封面 `media/poster.jpg`（第 5.6 秒）· 2 秒预览 `media/preview.mp4`（2.2–4.2 s）

**样片里的地形是生成的**：海岸、山脉、河谷、垭口、湖都是带种子的噪声和几条手画的河道算出来的，不对应任何真实的地方，所以上面没有国界，也没有真实地名；"河口、河谷、垭口、湖岸"是地形类型，海拔是从这张生成的高程里读出来的。

## 样片

| 拍 | 时间 | 本风格的做法 |
|---|---|---|
| 立住世界 | 0–1.5 s | 第一帧是全境的正射晕渲图（左边海、中间平原、右边山脉和湖）。0 s 起镜头推近并开始压低（缩放按对数缓动，俯仰 0° → 14°），远处开始泛起雾 |
| 招牌动作 | 1.5–4.5 s | 路线分三段长出来（每段 0.7–0.8 s）：从河口沿河谷而上、翻过垭口、下到湖岸；线头带一个箭头，每到一站弹出一个编号圆钉，旁边写地名和海拔（46 px 宋体加暗描边，海拔 28 px）；镜头一路跟着线头，压到约 35° |
| 真实字号的字 | 4.5–7 s | 图例框从上方落下：标题宋体 96 px（竖版两行 130 px）、英文 Baskerville 斜体 44 px、10 km 比例尺（按当前镜头的缩放算）和指北针；站名退到 30%；字幕 48 px 垫一块深色底 |
| 收住 | 7–8 s | 路线和标注淡出，镜头抬回正上方、拉回全境，回到第一帧 |

竖版：地图按高度铺满，镜头一开始只看西半边，跟着路线往东走；图例框在上方，字幕在下方。

## 学习对象

| 作品 | 年份 · 作者 | 从它身上学什么 |
|---|---|---|
| 《地形的地图表现》*Kartographische Geländedarstellung*（英文版 *Cartographic Relief Presentation*，1982） | 1965 · Eduard Imhof（苏黎世联邦理工学院），de Gruyter | 晕渲的规矩：光从西北来；越高对比越强（空气透视）；阴影偏冷、受光面偏暖；分层设色要低饱和，让地形自己说话 |
| 米纳德的拿破仑远征图 *Carte figurative des pertes successives en hommes de l'Armée Française dans la campagne de Russie 1812–1813* | 1869 · Charles Joseph Minard | 一条有宽度的带子沿着真实的地理走，带子本身就是数据；河流、地名和时间都挂在这条路线上。学"路线是主角，地图是舞台" |

核实：Imhof 一书的德文初版（1965，de Gruyter）、英文版（1982）、作者在 ETH 的教职据 Esri 和 Tufte 的书评与图书馆目录；米纳德地图的标题和年份据公开的图版资料。

**不照搬**：不用这两部作品的地图、配色表和图形；样片的地形、配色和路线都是自己做的。

## 视觉语法

- **色板**（分层设色，从深海到雪线）：

  | token | hex | 语义 |
  |---|---|---|
  | sea_deep / sea / shallow | `#1D3644` / `#36606C` / `#7DA6A6` | 海：越深越暗，海底只留一点起伏 |
  | sand | `#D8CDA6` | 海岸线 |
  | low / mid / high | `#93A27A` / `#B9AE85` / `#A48A6C` | 平原、丘陵、山地：都压得很低调 |
  | rock / snow | `#9B8F84` / `#F1EEE8` | 高山和雪：只在最高的地方 |
  | river | `#3F86A2` | 河流：源头细而淡，到河口变宽 |
  | haze | `#C9D7DC` | 远处的雾，倾斜越大越重 |
  | route / route_edge | `#E0532C` / `#3B1E14` | 路线：画面里唯一的饱和色，带深色边 |
  | pin / label / halo | `#FBF6EC` / `#FBF6EC` / `#20262A` | 站点圆钉和地名：亮字加暗描边，任何地形上都读得清 |
  | legend / ink / ink_soft | `#F4EFE3` / `#22262A` / `#5A5F63` | 图例框和它里面的字 |
- **字体**：地名和标题用宋体（Songti SC），数字（海拔、比例尺、编号）用 Avenir Next，英文副标题用 Baskerville 斜体。地图上的字一律加暗描边。
- **构图**：路线大致横穿画面，站点标注放在路线外侧的空地上，碰到安全框就换到另一侧；图例框放左上，字幕放下方正中。
- **质感**：晕渲：光从西北、高 29°，垂直夸张 20 倍，对比随高度增加；阴影里加一点蓝。海岸一条很淡的浪线。颗粒很轻（0.015）。

## 运动语法

- **镜头**：从高处推近并压低是这个风格的签名。缩放在对数空间里缓动（每一段的放大感觉一样快），俯仰从 0° 压到 35–40°，远处随倾斜泛雾；镜头跟着路线的线头走，不跟每一个弯。
- **路线**：一段一段长，每段 in-out sine，0.7–0.8 s；段与段之间留 0.2 s，让站点先弹出来。线宽按地图单位算，所以近处粗、远处细（透视）。
- **站点**：弹簧（ω 20、ζ 0.55）弹出圆钉，0.12 s 后写出地名和海拔。
- **转场**：都在地图里完成：推近到一个站点（换到细节）；拉远到全境（换到概览）；沿路线平移（换到下一段）。不用切到别的画面再切回来。

## 声音语法

- **配乐**：开阔的管弦，D 大调，120 BPM：竖琴（`harp_pm`）八分音符分解和弦，弦乐组垫长音（低通 3.2 kHz），铜管在路线那两小节里渐强（`swell`），大厅混响。和弦 Iadd9 – IV – vi – IVmaj7 – Iadd9。
- **音效**：推近时一口高空的风（长而低的 `air`）；每段路线一口上扬的 `swoosh_tonal`（长度等于这一段的时长，声像跟着线头走）；每个站点一声 `pop`（音高一站比一站高）；图例框落下一声 `paper`；拉回全境时一口上扬的 `air`。
- **声画关系**：每一段路线、每一个站点各有一个声音；配乐只管气氛，不卡每一站。

## 适合与不适合

- **适合**：05 数据故事里的地理和路线；10 长讲解里的历史行军、迁徙、探险、贸易路线；02 地理和旅行类知识短片。
- **不适合**：不需要地理位置的题目（只是为了"好看"套一张地图）；涉及争议边界又核实不了的题目；需要大量统计图表的段落（换 `editorial-data`、`bubble-chart-story`）。
- **容易被误用成**：卫星图加发光线条的"大片"感；路线一次画完、没有段落；到处是标注，地图被字盖满。

## 常见误用及原因

1. 【底线】地图上的线说不清来历：国界、争议地区、地名没核对，或者底图和高程的许可不清楚。不需要国界就不画；高程用公有领域的数据或自己生成的地形，来源写进素材表。
2. **山看不出立体，或者山像谷**：颜色太艳把阴影压掉了，或者光放到了东南。颜色压低，光放回左上（西北），高处的对比再拉大一点。
3. **观众跟不上路线**：路线一口气画完。拆成几段，每段一个站点、一个声音，镜头跟着线头走，推近的同时压低一点，远处加雾，立体感就回来了。

## Prompt 块

```text
Visual style: a shaded-relief map in the manner of classic Swiss cartography. Light comes from the north-west about 30°
up; contrast grows with height and shadows lean slightly blue; hypsometric tints are muted (sea #1D3644 to #7DA6A6,
plains #93A27A, hills #B9AE85, mountains #A48A6C, rock and a little snow only at the top). Rivers are thin and pale at
the source, wider at the mouth. The camera starts high over the whole region and pushes in (zoom eased in log space)
while tilting down to about 35–40°, the far edge fading into haze. A route grows leg by leg as a band with a dark edge
(#E0532C on #3B1E14) and an arrowhead, each leg 0.7–0.8 s, each stop a numbered pin with its name and a real number
(height, distance, date) in a serif with a dark halo. The title sits in a cream legend box with a scale bar and a north
arrow. No borders unless the film needs them and they are checked. Sound: harp arpeggios, strings, a horn swell; a
rising breath for each leg and a small pop for each stop.
```

## 引擎做法

- 一张 2D canvas，横竖两版各约 20–35 s 渲完。地形在 setup 里算一次：粗网格（1536×960）上的高程 = 向东抬升的底 + 一条山脉（沿脊线拉长的 ridged 噪声做出垂直于山脊的支脉）+ 刻出来的河谷、垭口和湖；双线性放大到 3072×1920，陆地再加一层细噪声；然后按法线和光照算晕渲、按高度插值分层设色，写进一张纹理。河流画在纹理上。
- **倾斜**：一个倾斜的平面（"mode 7"）：屏幕上每两行反算到纹理上的一行和它的缩放，`drawImage` 一条；路线、站点、比例尺用同一个投影函数，所以和地形严丝合缝。纹理之外填雾的颜色，像地平线。
- **海拔**：站点旁的海拔是从同一张高程里读出来的（h × 2 800 m），不是写死的数。真实项目里换成真实数据，读法不变。
- **真实数据**：高程用公有领域的数据（例如美国地质调查局、NASA 发布的 DEM），裁到用到的范围、降到用到的分辨率再入库；海岸线和河流同理。出处和许可写进素材表。

## 自查重点

- 联系表：路线每一段出来时，站点标注有没有出画、有没有压到别的标注或图例框。
- 放大一帧看山：阴影方向是不是一致的左上受光；颜色有没有比阴影还抢眼。
- 比例尺：按当前镜头的缩放算，镜头一推，比例尺跟着变长。
- 真实项目：每个地名、海拔、距离对照来源；没有画国界，或者画了的都核实过。

## 相关资源

- `video-types/05-data-story.md`、`video-types/10-long-explainer.md`；`recipes/README.md`（镜头推拉的配方）。
- 同一家族的 `clockwork-map`（机械钟表式的地图仪器）：那个是黄铜齿轮和仪表，这个是真实感的地形和光；`isotype`、`editorial-data` 管数字，这个管位置。
