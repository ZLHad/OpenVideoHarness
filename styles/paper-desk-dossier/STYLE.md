# 纸桌档案 · paper-desk-dossier

一句话：俯拍一张深褐木桌，桌上铺着一张奶白色的长纸，镜头沿着纸走。照片、索引卡、印章、回形针一样样落到纸上，每一样都带着分量和影子；一支红笔在照片上圈出要看的地方，在页边写下一行批注。适合人物和历史、长讲解里的"来龙去脉"、照片回顾，任何"证据要摆在桌面上给人看"的段落。

**怎么借**：让一张纸做全片的身体。东西都落在同一张纸上，换段落就是镜头走到纸的下一截；每样东西落下时影子从大而虚收到小而实，分量就出来了；红色只留给那支笔。秒数、尺寸、弹簧参数照样片试，嫌慢嫌快就改。唯一动不得的是纸上的字：照片、日期、出处都照抄原件，照片的许可记进素材表。

样片：`media/swatch.mp4`（9 s，比默认的 8 s 长一秒，让镜头沿纸滑那一下有 1.2 s；完整视频在 Release `styles-media`，`tools/fetch_media.sh paper-desk-dossier` 取回）· 竖版 `media/swatch-portrait.mp4` · 封面 `media/poster.jpg`（第 3.95 秒）· 2 秒预览 `media/preview.mp4`（1.45–3.45 s）

## 样片

| 拍 | 时间 | 本风格的做法 |
|---|---|---|
| 立住世界 | 0–1.5 s | 第一帧只有木桌。镜头从桌面一路滑过来，长纸的头从画面右边进来，1.25 s 停稳；1.12 s 第一张照片已经落下 |
| 招牌动作 | 1.5–4.2 s | 东西一样样落下：索引卡落下后自己打出三行字，第二张照片压着回形针，印章从上方按下、抬起，留下不匀的红印；红笔进画，圈住照片里的半圆顶，拉一根箭头到页边，写下"约 1865 年"，然后离开 |
| 真实字号的字 | 4.2–7.78 s | 镜头沿纸滑到干净的一截（4.2–5.4 s，in-out sine，慢到看得清照片和卡片怎么滑出去、空白的纸怎么进来），一张标题纸条落下（宋体粗 96 px，英文 Baskerville 斜体 44 px）；字幕是片子的字幕，横版放在纸下方的桌面上（48 px 米白），竖版放在纸上（65 px 墨色）；红笔回来在标题下划一道线，又离开 |
| 收住 | 7.78–8.95 s | 镜头加速走过纸的尾巴，回到空桌面。木纹在整段行程里正好一个周期，所以最后一帧就是第一帧 |

竖版重新构图：纸竖着放，镜头从上往下走，照片、卡片、第二张照片上下排开，批注写在照片上方，标题拆成两行（130 px）。

## 学习对象

| 作品 | 年份 · 作者 | 从它身上学什么 |
|---|---|---|
| 《Griffin & Sabine: An Extraordinary Correspondence》 | 1991 · Nick Bantock，Chronicle Books | 整本书由明信片、信封、夹在书页里能抽出来的信组成：手写、邮戳、贴纸、纸的厚薄都是叙事。学"东西本身就是信息"：一张卡片、一个印章，用它的材质说话 |
| 《战争迷雾》*The Fog of War* | 2003 · Errol Morris（配乐 Philip Glass） | 访谈之间切进来的物件和文件特写、落在地图上的多米诺骨牌：图像和人说的话形成对位，一个物理动作把抽象的道理演出来。学"让真实的东西在桌面上做一个动作" |

核实：书的出版年和出版社据 Wikipedia 与 Chronicle Books 的书页；电影的年份、导演、多米诺镜头据影评（Senses of Cinema、Design Observer 等）。

**不照搬**：不用这两部作品里的任何图像、文字和镜头；Bantock 的手绘明信片画风、Morris 的多米诺装置都不拿来。

## 视觉语法

- **色板**：

  | token | hex | 语义 |
  |---|---|---|
  | desk / desk2 | `#24170F` / `#4A3121` | 深胡桃木桌的暗部和亮部，只做底 |
  | paper | `#EEE5D1` | 长纸，全片的"身体" |
  | card / border | `#F6F1E4` / `#F4EEE1` | 索引卡、标题纸条、照片的白边：比长纸亮一档，叠上去分得出层 |
  | ink | `#2A2420` | 正文、打字、标题 |
  | pen | `#B4231B` | 红笔：只给批注、圈、箭头、下划线。全片唯一的饱和色 |
  | stamp | `#A0372B` | 印泥，比红笔暗、偏砖色，正片叠底印在纸上 |
  | muted | `#6E6458` | 英文副标题、次要字 |
  | caption | `#F1E8D6` | 压在木桌上的字幕 |

  照片保持原片的蛋白相纸暖调，只加一点 sepia（0.25）和对比，不重新上色。
- **字体**：标题和字幕用宋体（Songti SC，粗 700），红笔批注用楷体（Kaiti SC 粗，本机按需下载的字体，换机器可能回落到宋体），英文用 Baskerville（斜体做副标题），卡片上打字机的字用 American Typewriter。四种字各管一件事：印出来的、手写的、打出来的、英文的。
- **构图**：俯拍，纸占画面高度的七成，上下各露一条桌面。纸上的东西沿纸的方向排开，彼此留出纸面，不叠成一堆；每样东西略歪（±2–4°），像手放的。要读的标题放在纸的干净一截，不和照片挤在一屏。
- **质感**：木纹是长纤维加一圈圈生长纹的程序纹理；纸有低频的斑、细的纸齿和少量纤维，两道折痕；照片有白边、一点高光、胶带或回形针；印章的墨不匀（随机的空点和一角发干）。一盏暖灯在左上，四角压暗到约 42%；颗粒很轻（0.045，12 fps）。

## 运动语法

- **落下**：每样东西从大 13% 开始落，阻尼弹簧（ω 17、ζ 0.58）落到原大，略微压过一点再回来；影子跟着高度走：在空中时又大又虚又远（blur 47、偏移 30/41），落定时又小又实（blur 7、偏移 4/7）。分量感主要来自影子收紧的那一下，不是弹跳。
- **印章**：章从斜上方落下 0.2 s（ease-in），按下那一帧画面轻轻一震（3 px，0.15 s 衰减），抬起 0.24 s，印留在纸上。
- **红笔**：一支看得见的笔，笔尖跟着正在画的那一笔走；两笔之间抬起，影子变大变远；画完从右下角离开。圈 0.42 s，箭头 0.24 s，写一行字 0.4 s。笔在画面里，观众才知道这些红线是"有人刚画的"。
- **镜头**：只有一个方向，沿着纸走。进场 ease-out，滑到下一截 in-out sine（1.2 s，只加四分之一快门的运动模糊，纸上的东西一路看得清），离场 ease-in；停住的时候也在极慢地漂（3 s 漂 70 px），画面不冻住。
- **转场**：换段落 = 镜头走到纸的下一截。另外两种从纸上长出来：推进到一张照片里；拉远露出"原来这是纸上的一张照片"。不做整屏淡化和左右推页。
- **文字动画**：打字机（46 字/秒，逐字出现）给卡片；红笔手写（从左到右露出）给批注；标题和字幕不做逐字动画，随纸条落下、整行淡入。

## 声音语法

- **配乐**：室内乐小品，D 小调，120 BPM（样片按 3/3/3/5/2 拍的小节，四拍的分界落在小节线上）。毡锤钢琴（`piano`，`tone: felt`，踩踏板）弹分解和弦，大提琴（`cello`）拉一条长音旋律，底下垫一层很轻的 `roomtone`。和弦 i – VI – iv V – III – i，收在主和弦上，循环接得回去。
- **音效**：每样东西落下都有一声短的 `paper`（按东西的大小调 `dur` 和 `bright`：照片暗一点、卡片亮一点）；打字是 `typing`；印章是 `impact`（升高 9 个半音，压到 −15 dB，只剩一下闷响）；红笔是很亮、很短、很轻的 `paper`（`bright` 0.8–0.9，−19 dB）；镜头滑动是 `air`；纸被拉过去是一声长的 `paper`，声像从右到左。
- **声画关系**：动作密，声音也密，但每一下都轻；配乐不卡每一下，只在段落上换和弦。

## 适合与不适合

- **适合**：10 长讲解里的人物生平、来龙去脉；06 论文讲解的"研究史"；11 照片回顾（照片就是主角）；02 历史、人物类知识短片。题材上：传记、调查、档案、旅行、家族史。
- **不适合**：没有真实素材的题目（这个风格靠真东西，编出来的"档案"会露馅）；数据密集、需要图表一张接一张的段落；快节奏的卡点片。
- **容易被误用成**：桌面摆满东西、什么都在动；所有东西都用同一个落下的动作和同一声；红色到处用，失去"批注"的意思。

## 常见误用及原因

1. 【底线】纸上的字和照片说不出出处。这个风格靠"这是真的"撑着，编一处就全塌：照片、日期、引文照抄原件，许可记进素材表；没有真照片时自己画，但别画成"像档案"的样子去冒充。
2. **东西像贴上去的，不像落下来的**：多半是只做了淡入或弹出。救法是让影子跟着高度变：在空中又大又虚又远，落定时又小又实，再让它略歪着落，像手放的。
3. **观众不知道该看哪**：红色用到了标题、底色、装饰上，或者一屏塞了太多东西。把红收回到批注和那支笔，每样东西周围留出纸面，标题单独占一截纸。
4. **红线像印在纸上的**：没有笔。让笔进画、笔尖跟着线走、两笔之间抬起来，观众就知道这些线是有人刚画的。

## Prompt 块

```text
Visual style: a paper dossier filmed from directly above. A long cream sheet (#EEE5D1) lies on a dark walnut desk
(#24170F–#4A3121, long grain, a warm lamp pool upper left, corners falling to about 40%). The camera only travels along
the sheet: each new section of the film is the next stretch of paper. Real things land on the sheet one at a time, each
with weight: it drops from about 13% larger with a wide, soft, distant shadow that tightens to a small crisp one as it
touches down (damped spring, slight settle), and each is set a few degrees off square as if placed by hand. Archival
photographs keep their white borders and their own tone; index cards type themselves in a typewriter face; a rubber stamp
presses down, the frame gives slightly, and an uneven brick-red impression stays. One visible red pen (#B4231B) does every
annotation: it circles the detail that matters, draws an arrow to the margin and writes a short note in a handwritten
face, lifting between strokes, then leaves frame. Red is used for annotation only. Titles are set in a bold Song serif on
a pasted paper slip; English in an italic old-style serif. Every label, date and caption is copied from its source.
Sound: a small chamber piece (felt piano, cello) in a minor key; every landing has its own short paper sound.
```

## 引擎做法

- 首选 canvas-film 或 HyperFrames 的一张 2D canvas。纸、木纹、印章的纹理都在 setup 里生成一次（带种子），每帧只是按镜头位置把它们贴上去，再画落下的东西：`swatch.js` 就是这样，横竖两版各 1 个 worker 约 20 s 渲完。
- **纸坐标**：所有东西用"沿纸的距离 u、横跨纸的位置 v"摆放，镜头只有一个数 c（屏幕前沿对着纸上的哪个 u）。横版 u 沿 x，竖版 u 沿 y：同一张表画两个画幅。
- **木纹首尾相接**：木纹沿镜头行程是周期的（噪声在一个圆上取样：`fbm2(R·cos θ, R·sin θ)`，θ = 2π·行程/周期），周期等于整段行程，所以最后一帧和第一帧逐像素相同，样片能无缝循环。
- **落下**：`h = 1 − spring(t − t0)`，缩放 `1 + 0.13h`，影子的 blur、偏移和透明度都按 h 插值。
- **红笔**：每一笔是一条折线，`strokePartial` 画已经画到的部分，笔尖位置用同一套弧长取点；两笔之间笔尖走一段 ease，抬起量另算，只用来放大影子。
- **运动模糊**：镜头快速移动的三段（进场、滑动、离场）用 `lib.motionBlur`；滑动那一段只开四分之一快门（4 个采样），进场和离场半个快门；停住的时候直接画，字在读的时候是清楚的。别拿运动模糊撑一个太快的移动：快到整屏是糊的，就该放慢或加长。
- **照片**：只用公有领域或许可清楚的照片，缩到画面上用到的尺寸（样片两张合计约 120 KB）。

## 自查重点

- 联系表每一拍各看一遍：东西落下时影子有没有从虚到实；同一屏里有没有留出纸面。
- 抽一张有红笔的帧放大看：笔尖是不是正好在线头上，笔的影子方向和其他东西一致。
- 所有卡片、批注、标题上的事实对照出处逐字核对；照片的来源和许可写进素材表。
- 最后一帧和第一帧并排：木纹接得上（`bin/vh style check` 量循环接缝）。
- 标题读的那段时间里，红笔和下划线没有压到字。

## 素材

| 文件 | 内容 | 来源 | 许可 |
|---|---|---|---|
| `photo-half-dome.jpg` | Carleton E. Watkins, *Half Dome, Yosemite Valley, California*, ca. 1865（缩到 720 px 宽） | Library of Congress，经 Wikimedia Commons：`File:Carleton_Watkins,_Half_Dome,_Yosemite_Valley,_California,_ca._1865.jpg` | 公有领域（Watkins 1916 年去世；Commons 标注 Public domain） |
| `photo-merced-river.jpg` | Carleton E. Watkins, *Merced River, Yosemite Valley, California*, ca. 1865（缩到 480 px 宽） | Library of Congress，经 Wikimedia Commons：`File:Carleton_Watkins,_Merced_River,_Yosemite_Valley,_California,_ca._1865.jpg` | 公有领域（同上） |

其余（木纹、纸、印章、红笔、回形针、胶带）都在 `swatch.js` 里程序生成。音效是 `bin/vh sfx` 的内置合成音效，配乐由 `score.json` 合成。

## 相关资源

- `video-types/10-long-explainer.md`、`video-types/11-photo-recap.md`、`video-types/06-paper-explainer.md`；`playbook/04-audio.md`（转场音效按风格选：纸面类用 `paper`）。
- 同一家族的 `cutout-jazz`、`risograph` 是印出来、剪出来的平面；这一个是真东西摆在纸上。和 `archival-pan-zoom` 的区别：那个是镜头在一张照片里推拉，这个是照片作为物件落在桌上。
