# 暗底金线描 · gold-line-dark

一句话：近黑的底上，一根暖金色的细线连着画出整个场景，线头是一点光，走过的地方从白热冷成金色；字也是细细的金字。适合讲场景、器物、历史和一段经过：山、水、船、月亮、一件古器、一座城，用一根线勾出来，观众的眼睛跟着线头走。

**怎么借**：可以借走的是三样。一种颜色：只有金，深浅不同的金，没有第二种颜色，层次靠线的亮度和一层淡淡的金色平涂。一根线：场景尽量一笔连下来，从一样东西走到下一样东西，线头始终是全画面最亮的一点，观众知道该看哪儿。字是金箔：一道亮光扫过去，字跟在后面铺开。下面的色值、线宽、时长都是样片的数，供试做。不能放的是：细字也要过字号下限和对比度；金线描的是事实性的东西（器物、地形、天象）时，形状要对。

样片：`media/swatch.mp4`（9 s，完整视频在 Release `styles-media`，`tools/fetch_media.sh gold-line-dark` 取回）· 竖版 `media/swatch-portrait.mp4` · 封面 `media/poster.jpg`（t = 6.4 s）· 2 秒预览 `media/preview.mp4`（2.2–4.2 s）

样片里：一点光从左边出发，划出一道山脊，沿着山脚折下来，画出水岸和一圈圈涟漪，水上一条小船；光熄掉飞上天，在一条弧上依次画出五个月相：峨眉月、上弦、满月、下弦、残月，月亮之间用同一根线串起来，五个月亮就是一段时间。然后标题以金箔的样子铺开，英文一行和字幕跟着。最后线按画的顺序从头烧掉，字散成金粉飘走，光在起点重新亮起来。实际字体：中文 Songti SC Light，英文 Didot。

## 样片

| 拍 | 时间 | 这一拍做什么 | 本风格的做法 |
|---|---|---|---|
| 立住世界 | 0–1.5 s | 色板和质感一眼看清 | 一点光 0.1 s 出发，1.15 s 横穿画面拉出山脊；暖黑底、慢慢闪的星、线的金色光晕 |
| 招牌动作 | 1.5–4.5 s | 一根线画出场景 | 同一根线折下山脚，画水岸涟漪和小船；再飞上天串起五个月相，每个月亮画完，亮的那一半铺一层淡金 |
| 真实字号的字 | 4.5–7.5 s | 标题和字幕，停够读完 | 标题 96 px，一道亮光从左扫到右、字跟在后面铺开（0.75 s）；英文 44 px、字幕 48 px 随后；读的时候亮光再扫一次；水面的碎光一直在闪 |
| 收住 | 7.5–9.0 s | 落定，接回第一帧 | 线按画的顺序从起点烧掉，字一个个散成金粉往上飘；一片黑里只剩星，光在山脊的起点重新亮起 |

这一支是 9 秒，节拍 80 BPM，四拍落在 1.5、4.5、7.5 s 的小节线上。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 毕加索的光绘，Gjon Mili 拍摄 | 1949 · Pablo Picasso、Gjon Mili（瓦洛里拍摄，《LIFE》1950 年 1 月 30 日刊出） | 暗室里拿一支小灯在空中画，长曝光留下一根连续的光线：一笔画出一头牛、一个人；线头就是光 |
| 中尊寺经（紺紙金銀字交書一切経）的扉画 | 约 1117–1126 · 藤原清衡发愿，大部分藏高野山金刚峯寺 | 绀青的纸上用金银泥细线画出说法图：没有色块，只有细线和留下的暗底，字也是金银细字 |
| 高丽写经《妙法莲华经》卷二 | 约 1340 · 纽约大都会艺术博物馆藏（1994.207） | 靛蓝纸上的金银泥扉画：极细的金线画满一整幅场景，暗底衬得线发亮 |

核实：毕加索光绘的拍摄年份、地点和刊出日期，中尊寺经的发愿人、年代和收藏处（文化遗产在线），大都会馆藏的年代、材料和编号，都对照过来源（2026-11-16）。

**不照搬**：不复刻毕加索光绘里的具体形象，不用写经扉画的佛像和构图。样片的山、水、船和月相是为"一根线讲一段时间"画的。

## 视觉语法

- **色板**：底 `#0C0A07`（暖黑，不是纯黑，中间微微提亮到 `#1E1810`）；金 `#D7B064`；线头和刚画过的地方 `#FFF0C8`；英文和次要的字 `#B39462`；字幕 `#EADFC3`。没有别的颜色。
- **线**：核心 2.8 px（1080p），刚画过的 0.45 s 内更亮更粗（最多 +1.6 px）；外面两层光晕（9 px 模糊、2.5 px 模糊，叠加混合）。串月亮的线稍细稍淡。
- **面**：只有一种面：亮的那部分铺一层 26% 的淡金，告诉观众"这一半是亮的"。
- **底**：70 颗很小的金色星，各自慢慢闪；轻颗粒、暗角。
- **字**：中文用细的宋体（Songti SC Light），字距放开一点（0.08 em）；英文用 Didot。字比画面安静，留在场景下方。
- **构图**：场景横向铺开，地平线在画面中部偏上，天上留给天象；字在下方。竖版把同一个场景压窄，月亮的弧拱得更高。

## 运动语法

- **线速**：每一段按最小加加速度曲线走（`styles/_swatch/vendor/hand.js`），长线快（山脊 1.15 s 走完 1700 px），小东西慢（小船 0.42 s）。线头在两段之间熄掉飞过去，只剩三分之一的亮度。
- **金箔**：一个 90 px 宽的软边从左往右推开（outCubic），一道 240 px 宽的亮光在前面扫；读字时同样的亮光再走一次，作为这一拍的次要动作。
- **转场**：线接着画下一样东西（场景之间不剪）；收尾时线按画的顺序烧掉，字散成金粉。不用淡入淡出整幅画面。
- **镜头**：固定。线本身在走，镜头再动就抢了。

## 声音语法

- **配乐**：夜里的竖琴和高弦。80 BPM，E 大调，竖琴分解和弦、高音弦乐长音、低音持续音，读字时钢片琴三个音；大厅混响 2.6 s。
- **音效**：线头走的时候一丝光的嘶声（很轻的火花噼啪加一缕随速度起落的气声，长度和那一段线一样，`styles/_swatch/custom_sfx.py` 合成，在 `styles/gold-line-dark/sfx/`）；每画好一个月亮一声 shimmer，音高沿五声音阶往上走；金箔铺开时一道细的亮声。
- **声画关系**：稀。声音跟着线头，不跟着节拍；读字时几乎只有音乐。

## 适合与不适合

- 适合：知识短视频（02）的开场和章节、长讲解（10）里讲场景和历史的段落、原理讲解（01）里需要一幅"图"而不是图表的地方；器物、地图、天象、古建筑、一段旅程。横竖都成立。
- 不适合：数据和图表（只有一种颜色，分不出系列）；需要多种颜色区分对象的数学讲解（那是 `dark-math`）；欢快、热闹的内容。

## 常见误用及原因

- **加第二种颜色**：一加红或蓝，就成了普通的线稿配色，金线的庄重没了。要强调，用更亮的金和一层淡金平涂。
- **线太粗、光晕太重**：粗线加大光晕像霓虹灯管，变成另一个风格；金线描的线是细的，光晕只是一层气。
- **把线做成"描边动画"**：整幅图同时从各处描出来，看不出一根线在走。线头只有一个，观众跟着它。
- **金色渐变字、立体字**：金箔是平的，靠一道扫过的亮光显出金属感；加斜面、加投影就俗了。
- 【底线】细宋体在手机上容易发虚：标题按字号下限来，字幕可以用常规粗细。

## Prompt 块

```text
One warm-gold line of light (#D7B064) on warm near-black (#0C0A07) draws the whole scene, as a light pen does in a
long exposure: a single bright spark at its head, the freshly drawn line white-hot (#FFF0C8) and slightly thicker for
half a second, then cooling to gold. The line travels from one thing to the next without lifting where it can — a
ridge, the shore and its ripples, a boat, the moon's phases strung on one arc — and moves at a hand's speed, slow at the
ends of each stretch and fast in the middle. One colour only; the only fill is a faint gold wash on the lit part of a
thing. Thin gold serif type laid like gold leaf: a soft front reveals it left to right under a travelling gleam. To
close, the line burns out in the order it was drawn and the words lift away as gold dust. Camera locked; faint stars
twinkle. Sound: slow harp, high strings, a low drone, a celesta; the spark has a faint crackle and breath that rise
and fall with its speed. Sample values (try, then depart): 2.8 px core line at 1080p, glow blur 9 px and 2.5 px
added, ridge drawn in 1.15 s, gleam band 240 px.
```

## 引擎做法

- 线：`hand.js` 的 `prep` / `drawStroke` / `pen`，用 Catmull-Rom 把几个关键点连成平滑的山脊；`timeAtS` 算出线上每一段是什么时候画的，颜色和粗细按"画了多久"来，所以冷却也是 t 的纯函数。
- 光晕：线先画进离屏图层，再用 `lighter` 叠两遍模糊的副本，最后画清晰的核心。
- 烧掉：`drawStroke` 的 `from` 参数，让每段线从起点往后消失，按画的顺序错开 0.08 s。
- 金箔：每一行字一个图层（`destination-in` 的蒙版会清掉整个图层，所以不能共用），先画字，用横向渐变当蒙版推开，再用 `source-atop` 把亮光只加在字上。
- 金粉：每个字 5 粒，起飞时间和方向由序号和 `lib.hash` 定，位置是起飞后时间的函数。

## 自查重点

- 线头在每一帧都是全画面最亮的一点；没有两处同时在画。
- 月相读得出来：亮的那一边在对的一侧（上弦亮右半，下弦亮左半）。
- 细宋体在 1280×720 下不糊；金色字在暗底上对比度够（textcheck 量）。
- 最后一帧只有星和起点那一点光，和第一帧一样。

## 相关资源

- `video-types/02-knowledge-short.md`、`video-types/10-long-explainer.md`。
- 同家族的 `dark-math`（多色的数学对象，和这里的单色场景分开用）、`blueprint`（白线制图）。
