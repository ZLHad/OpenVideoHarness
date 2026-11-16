# 时代媒介接力 · era-media-relay

一句话：同一样东西，每到一个时代就用那个时代自己的笔再画一遍：毛笔、雕版、显像管、像素。东西不动，换的是笔；换笔的那一下，就是新的那支笔自己干活的样子。适合技术史、媒介史、时间轴长片：一段一个时代，观众不用看字幕也知道"现在到了哪个年代"。

**怎么借**：要让观众看出“到了另一个时代”，靠的是换笔，不是换景：同一样东西钉在原处、大小不变，只有画它的工具在换。每次接力就是新工具自己在干活：滚筒压过去，电子束扫下来，画面粗成方块，一滴水晕开。观众看见了工具，也就认出了年代。每个时代都用它自己的全套，材料、颜色、字、声音一起换；配乐的调和速度不变，只换乐器。样片里的四个时代只是一种挑法，换了题目就重挑，标准是一眼认得出、彼此离得够远。工具和质感要对得上那个时代；字号下限和读时照样要守。

样片：`media/swatch.mp4`（9 s，完整视频在 Release `styles-media`，`tools/fetch_media.sh era-media-relay` 取回）· 竖版 `media/swatch-portrait.mp4` · 封面 `media/poster.jpg`（t = 3.05 s，电子束扫到一半：上面是荧光屏，下面还是印版）· 2 秒预览 `media/preview.mp4`（1.4–3.4 s）

样片里：一支毛笔在宣纸上四笔画出一只燕子（身子连尾巴、上翅、下翅、另一根尾羽），笔头先轻落再压下去，笔尾的毛干了就散成飞白；一根滚筒从左往右压过去，燕子变成雕版印刷的黑白版画，木纹印在墨里，翅膀上的刻线是白的，然后盖一方红印；一道绿色的电子束从上往下扫，燕子变成显像管上的荧光线框，还跳了一下；屏幕粗成一格格方块，燕子变成两帧交替扇翅的像素精灵，标题、英文、字幕一个字一个字地打出来，字也是像素；最后一滴水落在屏幕中央，晕开成一张空白的宣纸，毛笔回到开头的位置。实际字体：中文 Hiragino Sans GB W6（按 3 px 的网格量化成像素），英文 Silom。

## 样片

| 拍 | 时间 | 本风格的做法 |
|---|---|---|
| 立住世界 | 0–1.5 s | 0.1 s 毛笔落下，四笔画出燕子：笔画的头轻、身子重、尾巴干；宣纸纤维和湿墨的晕 |
| 招牌动作 | 1.5–4.5 s | 滚筒压出雕版（0.75 s）并盖印；电子束扫出荧光线框（0.55 s）；屏幕粗成像素、燕子变成精灵（0.58 s）。每次换的是笔，燕子在原地 |
| 真实字号的字 | 4.5–7.5 s | 像素时代：标题 96 px、英文 44 px、字幕 48 px 一字一字打出来，按 3 px 网格量化，带一像素的硬投影；燕子在上面每秒 6 帧扇翅 |
| 收住 | 7.5–9.0 s | 一滴水落下，从中央晕开成宣纸，晕的边缘带一圈湿痕；毛笔回到起点 |

这一支是 9 秒，120 BPM，四拍落在 1.5、4.5、7.5 s 的小节线上；每个时代一小节，乐器跟着换代。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《Sita Sings the Blues》 | 2008 · Nina Paley | 同一个故事的几条线各用一种画法：拉其普特细密画风格的《罗摩衍那》、皮影样的叙述者、矢量动画的歌舞段、作者自己故事的 Squigglevision。换画法就是换叙述层，观众一眼分得清 |
| 《蜘蛛侠：平行宇宙》 | 2018 · Bob Persichetti、Peter Ramsey、Rodney Rothman；Sony Pictures Animation | 每个蜘蛛侠带着自己媒介的画法进同一个画面：黑白的侦探漫画、日本动画、卡通。画法本身说明"他从哪里来" |

核实：两部片子的年份、导演和画法对照了 Wikipedia（2026-11-16）。

**不照搬**：不用这两部片子的角色和具体画面。样片的燕子、四个时代和接力动作是自己设计的；换题目时，主体和时代都按题目重新选。

## 视觉语法

- **一个主体，四套材料**：

  | 时代 | 底 | 主体 | 质感 |
  |---|---|---|---|
  | 毛笔 | 宣纸 `#EEE5CF` | 墨 `#1A1814`，每笔 11 根毛，笔画后半段干毛逐根脱落 | 纸纤维，3 px 的湿晕 |
  | 雕版 | 米色纸 `#E8DCC0` | 实心墨块，木纹透白，刻线是白的 | 红印 `#B8382B` 一方（印文用几何笔画，不写字） |
  | 显像管 | 玻璃 `#07100A` | 荧光绿 `#6CFF9B` 线框，两层光晕 | 4 px 扫描线、管子的暗边、轻的闪烁 |
  | 像素 | 夜蓝 `#141A33`，格点 `#3A4A7A` | 白 `#F3F1E7` 精灵、蓝 `#6FC3FF` 描边，20 px 一格 | 字按 3 px 网格量化，硬投影 |

- **构图**：主体在画面上半部的正中，所有时代同一个位置、同一个大小，接力时观众的眼睛不用动。字在下方。
- **时代的选法**：挑能一眼认出年代的工具，而且彼此差得够远（软笔 → 印刷 → 电子 → 数字）。三四个就够；每个时代至少停 0.6 s 让人看清。

## 运动语法

- **接力**：新的那支笔怎么干活，接力就怎么做：滚筒横着压过去（左边已经是印版）、电子束从上往下扫（上面已经是荧光屏）、画面粗成方块再换成像素精灵、一滴水晕开。每次接力 0.55–1.0 s，缓动用 inOutCubic 或线性扫描（电子束是匀速的）。
- **毛笔**：每一笔按最小加加速度曲线走（`styles/_swatch/vendor/hand.js`），笔头先轻落（宽度从一半开始），再压下去，尾巴变细变干。
- **每个时代里的小动作**：印章盖下去（放大落定）、显像管跳一下（横移 26 px、50 ms 衰减）、像素精灵每秒 6 帧扇翅。
- **镜头**：固定。主体不动，才看得出是笔在换。

## 声音语法

- **配乐**：乐器跟着换代，调和速度不变（A 小调，120 BPM，每小节三拍）：毛笔是古琴，雕版是羽管键琴的分解和弦加木鱼，显像管是合成器音序加低音嗡声，像素是方波旋律、三角波低音和噪声镲，结尾回到古琴；一层很轻的弦乐垫在底下把四段连起来。
- **音效**：毛笔一声软的扫（落笔一点轻触），滚筒的隆隆声和墨的黏响，印章一声木头落纸，显像管亮起的"嗡"和静电，像素是一串下行的方波，打字是芯片的短音，水滴一声"啵"。全部由 `styles/_swatch/custom_sfx.py` 带种子合成，渲染样片时生成在 `styles/era-media-relay/sfx/`（不进 git）。
- **声画关系**：每次接力的那一下是 hero；时代内部的声音轻。

## 适合与不适合

- 适合：长讲解（10）里的时间轴段落、数据故事（05）里"同一个指标在不同年代"、知识短视频（02）讲一样东西的演变（文字、地图、照片、计算机）。横竖都成立。
- 不适合：只有一个时代的内容；时代多到十几个时（每个只停一下就成了幻灯片，挑三四个代表，其余用一条时间轴带过）。

## 常见误用及原因

- **换的是地点，不是笔**：从书房到工厂再到机房，观众读到的是一趟旅行，不是媒介在变（那是 `walk-in-world`）。救法：主体钉在同一个位置、同一个大小，只换画法。
- **接力用推拉、淡化、闪白**：工具不见了，接力就成了幻灯片换页。救法：让新工具的动作本身完成交接：印上去、扫下来、量化成格、晕开。
- **时代感靠一层滤镜**：同一张图加上"复古"效果，看起来是一张图换了皮。救法：每个时代重画一遍：毛笔有笔锋和飞白，雕版是凸版的黑白，显像管有扫描线和余辉。
- **每个时代配一个年份大字**：画法已经说明了年代，再贴大字就成了 PPT。真需要年份，放在角落的小字里，或交给旁白。
- 【底线】像素字读不出来：把量化网格调小，过 textcheck 和 readcheck。

## Prompt 块

```text
The same subject drawn again and again with the tools of successive eras, in the same place and at the same size, so
only the medium changes: a brush on rice paper (tapered strokes that land light, press, and dry out into separate hairs),
a woodblock print (solid black with the block's grain and white carved lines, a red seal), a cathode-ray screen (green
phosphor vectors with glow, scanlines, a dark tube edge), then pixels (a two-frame sprite on a dotted grid, type
snapped to the pixel grid). Each handover is the new tool at work — a roller pulls the print across the painting, the
beam scans down over the print, the screen coarsens into blocks that become the sprite — and the loop closes with a
drop of water blooming back into blank paper. Camera locked. The music keeps its key and tempo while its instruments
change era: guqin, harpsichord and woodblock, synth sequence and hum, chip square waves. Sample values (try, then
depart): handovers 0.55–0.75 s, 20 px pixel cells, type quantised to 3 px.
```

## 引擎做法

- 每个时代是一个整帧的绘制函数（`paintBrush`、`paintPrint`、`paintScreen`、`paintPixel`），接力时把新时代画进离屏图层，按工具的进度裁剪（滚筒的 x、电子束的 y）合到旧时代上面，再画上工具本身。
- 毛笔：每一笔是 `hand.js` 重采样的路径，沿路径每 3 px 画一排 11 根"毛"，哪根毛在笔尾断掉由 `lib.hash` 和这一笔走到哪儿决定，所以飞白是固定的。
- 雕版的木纹是一张预先画好的贴图，用 `destination-out` 从墨块里扣出来；像素精灵是在 setup 里把燕子的多边形按格子栅格化（格心在多边形里就点亮，邻格有空的就是描边）。
- 像素化：把整帧缩小到 1/b 再关掉平滑放大回来；字同理，按 3 px 网格。
- 水晕：带噪声边缘的圆，`source-in` 把空白宣纸裁进去，边缘描一圈模糊的湿痕。

## 自查重点

- 四个时代里燕子都认得出是燕子（不是飞机、不是十字），位置和大小没跳。
- 每次接力都看得到工具（滚筒、扫描线、方块），不是硬切。
- 像素字在 1280×720 下读得出；字和精灵不挤在一起。
- 最后一帧是空白宣纸和停在起点的毛笔，和第一帧一样。

## 相关资源

- `video-types/10-long-explainer.md`、`video-types/05-data-story.md`、`video-types/02-knowledge-short.md`。
- 同家族的 `whiteboard`、`chalkboard`；画面相近但换的是地点的 `walk-in-world`；像素时代可以借 `pixel-16bit` 的调色和字。
