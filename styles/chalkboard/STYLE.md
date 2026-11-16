# 黑板粉笔 · chalkboard

一句话：墨绿的黑板，粉笔一笔一笔写，板擦擦过的地方留一层粉痕，下一笔就写在粉痕上。适合原理推导、公式、"先猜一个，错了擦掉再来"的讲解：黑板留得住思考的过程，错的那一步擦掉了也还看得见影子。

**怎么借**：可以借走的是三样。擦除是一个动作，不是一次转场：板擦拖过去，粉末落下来，擦过的地方比没写过的地方亮一层；错的东西擦掉以后留下影子，对的东西写在影子上，观众看得到"改过"。粉笔是颗粒，不是线：手快的地方笔跳过板面的凹凸，线就断、就淡。颜色有分工：白粉笔写结构，黄粉笔写答案，粉色只点出要看的那几个点。下面的色值、时长都是样片的数，供试做。不能放的是：字照"在哪看"的字号下限来，停够读完一遍；粉笔字的颗粒不能把字吃到读不出。

样片：`media/swatch.mp4`（10 s，完整视频在 Release `styles-media`，`tools/fetch_media.sh chalkboard` 取回）· 竖版 `media/swatch-portrait.mp4` · 封面 `media/poster.jpg`（t = 8.0 s）· 2 秒预览 `media/preview.mp4`（2.2–4.2 s）

样片里讲的是一次抛物：先画高度 h 和时间 t 的两根轴，白粉笔猜了一条直线，板擦来回擦掉它，黄粉笔在直线的粉痕上画出真正的抛物线；粉笔点出三个时刻，虚线落到时间轴上，每一个时刻就是一帧。然后写标题、英文一行和字幕。最后这块板往上推走，下面那块板升上来，上面是同样的旧粉痕，板擦也回到开头的位置。实际字体：中文 HanziPen SC（翩翩体，macOS 按需下载的系统字体，没有时回落到 Kaiti SC、PingFang SC），英文 Chalkduster。

## 样片

| 拍 | 时间 | 这一拍做什么 | 本风格的做法 |
|---|---|---|---|
| 立住世界 | 0–1.5 s | 色板和质感一眼看清 | 0.1 s 板擦从左往右拖过半块板，旧粉痕被擦薄，粉末往下落；接着白粉笔画两根轴 |
| 招牌动作 | 1.5–4.5 s | 擦除和粉痕 | 猜的直线写上去，板擦来回擦掉，留下一道模糊的影子和擦痕；黄色抛物线写在影子上，粉色点出三个时刻、虚线落到 t 轴 |
| 真实字号的字 | 4.5–9.0 s | 标题和字幕，停够读完 | 标题分两行写在图右边（96 px，每字 0.11 s），英文一行（44 px，浅蓝粉笔），字幕在下方（48 px，每字 0.06 s）；字停 2.3 s 以上 |
| 收住 | 9.0–10 s | 落定，接回第一帧 | 推拉黑板：这一块往上推走，中间的铝框滑过，下一块带着同样的旧粉痕升上来；板擦和粉笔回到开头的位置 |

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《物理定律的本性》（*The Character of Physical Law*，康奈尔大学信使讲座） | 1964 · Richard Feynman，BBC 拍摄 | 一个人对着黑板边想边写，写错了擦，板上一直留着推到一半的东西；讲的顺序就是板上的顺序 |
| 《Richtkräfte (einer neuen Gesellschaft)》 | 1974–77 · Joseph Beuys；一百块黑板，藏柏林国家美术馆（汉堡火车站） | 讲话时随手画在黑板上的图和字，被当作作品留下来：擦痕和写满的层次本身就是内容 |
| 灰底画（常被叫作"黑板画"），如《Untitled》（1970） | 1967–71 · Cy Twombly | 灰黑底上一圈一圈白色的线，像粉笔在板上反复写过又擦过：底色上永远有一层上一遍留下的白 |

核实：信使讲座的题目、地点和年份（1964 年 11 月，康奈尔，BBC）对照了加州理工的 Feynman Lectures 网站；《Richtkräfte》的年份、数量和收藏处对照了柏林国家博物馆网站；Twombly 灰底画的年份对照了 Wikipedia（2026-11-16）。

**不照搬**：不复刻 Feynman 黑板上的具体推导，不用 Beuys 黑板上的图和字，也不仿 Twombly 的笔迹。样片的抛物线、三点和虚线是为"每一帧都是 t 的函数"画的。

## 视觉语法

- **色板**：板 `#2A453A`（墨绿，带大块的明暗斑驳和细颗粒）；白粉笔 `#ECEBE3` 写结构和字；黄粉笔 `#F2D36B` 写答案；粉色 `#F1A2A7` 点出要看的点；浅蓝 `#A8D1EA` 写旁注（样片里是英文一行）；粉末 `#E6E4DA`。
- **粉痕**：板从来不干净。旧粉痕是三层：看不清的旧字（模糊的白色弯线，6–13%）、旧图的影子、板擦的弧形擦痕（3–6.5%）。新擦的地方先亮、0.7 s 内沉到 40%，然后一直留着。
- **粉笔线**：9.5 px（1080p），一张带孔的颗粒贴图当笔刷：12% 全透、14% 半透；手快的地方淡到 72%。线不收圆头，断口是平的。
- **字**：粉笔写的手写体（样片用翩翩体粗体），字上扣掉一层随机的小孔，像粉笔字一样透出板色；英文用 Chalkduster。
- **构图**：左边是图，右边是写下来的结论；字幕在下方。竖版图在上、字在下。

## 运动语法

- **笔速**：最小加加速度曲线，和 `whiteboard` 同一套（`styles/_swatch/vendor/hand.js`）；样片四档时长 0.07、0.14、0.35、0.5 s。
- **擦**：板擦是 230×92 px 的毡擦，沿一条路径走，走过的地方按一串圆角脚印擦掉（边缘模糊 5 px）。长擦一次 0.85 s，来回擦一段 0.6 s；擦的时候粉末从擦边落下（每次 70 粒，0.9 s 落完，每一粒都是 t 的函数）。被擦掉的线留下自己 4 px 模糊、30% 的影子。
- **换内容**：推拉黑板，这块往上推走、下一块升上来（0.95 s，inOutCubic，带纵向拖影）；或者把一块区域擦掉接着写。不用淡入淡出。
- **镜头**：固定。黑板讲解的动都在板上，镜头动了反而看不清在写什么。
- **签名**：擦。猜错、擦掉、在影子上写对，是这个风格最像它自己的一下。

## 声音语法

- **配乐**：阶梯教室里的钢琴。120 BPM，D dorian，八分音符轻摇摆；钢琴和弦加一条高音小旋律，拨弦低音提琴，很轻的邦戈鼓；大厅混响 1.6 s。
- **音效**：粉笔是颗粒声：落笔一下"嗒"，然后是笔在板面凹凸上跳的密集小撞击和干的摩擦，手快时更密更响；毡擦是低沉的拖擦声，来回擦时一下一下起伏；推拉黑板是一声低的 whoosh。全部由 `styles/_swatch/custom_sfx.py` 合成（`styles/chalkboard/sfx/`）。
- **声画关系**：擦是 hero，粉笔是 detail；写字时粉笔声连成一串，读字时只剩钢琴。

## 适合与不适合

- 适合：原理讲解（01）、论文讲解里的推导（06）、长讲解（10）里"想一件事"的章节；任何"先错再对"的讲法。横竖都成立。
- 不适合：要显得新、显得快的发布片；大量数据和截图（黑板上放截图会很怪，要放就画成粉笔图）。

## 常见误用及原因

- **一擦就干净**：擦完板面和没写过一样，擦除就成了转场；粉痕留下来，观众才知道这里改过。
- **粉笔线是一条均匀的白线**：那是白色的矢量线，不是粉笔。颗粒、断口、手快处变淡缺一不可。
- **整块板全写满再换**：板上要有留白，结论写在图旁边，写满了就推拉换板。
- **粉笔字颗粒太重**：孔开得太多，字就碎了。【底线】字要过字号下限和对比度检查，读不出就少开孔。
- **黑板配粉笔吱吱的尖叫声**：大多数人听到会难受；粉笔的声音是沙沙的颗粒，偶尔一下尖声就够。

## Prompt 块

```text
Chalk on a mottled slate-green board (#2A453A) that is never clean: faint unreadable ghosts of earlier writing and the
wide arcs of a felt eraser. Diagrams and words are chalked stroke by stroke at a human hand's speed (slow-fast-slow);
the line is grain, not a vector — it skips where the hand is fast, ends cut flat, no round caps. White chalk for
structure, yellow for the answer, pink only to mark the points to look at, pale blue for side notes. Erasing is the
signature gesture: a felt eraser drags across, chalk dust falls from its edge, and what it wipes leaves a pale blurred
ghost of itself plus the felt's streaks; the right answer is chalked over the ghost of the wrong one. Change boards by
sliding the double board up, not by fading. Camera locked. Sound: a warm piano in a lecture hall with plucked bass and
very soft bongos; chalk is gritty taps and scrapes, the eraser a soft low drag. Sample values (try, then depart): 9.5 px
chalk at 1080p with 12% holes, 230×92 px eraser, fresh dust settling to 40% in 0.7 s.
```

## 引擎做法

- 笔画：`styles/_swatch/vendor/hand.js` 的 `prep` / `drawStroke` / `pen`；粉笔的笔刷是 `createPattern` 的颗粒贴图，按段画，段的透明度跟手速。
- 擦除：擦到哪儿由板擦的路径和进度决定，每帧在一个离屏图层上把走过的脚印画成蒙版（`lib.layer`），被擦的东西单独一层，`destination-out` 扣掉；影子是同一层的模糊副本，`destination-in` 留在蒙版里；新擦痕是一张预先画好的条纹贴图，按蒙版留下、按时间衰减。全是 t 的纯函数，没有跨帧的累积。
- 粉末：每一粒的出生时间和位置由序号定，落下的位置是出生后时间的二次函数。
- 推拉黑板：整块板画进离屏图层，按位移叠几份做纵向拖影（`smear`）；下一块板用同一张底纹和旧粉痕，所以最后一帧和第一帧一样。

## 自查重点

- 擦过的地方看得出比别处亮一层，但不比粉笔字亮；影子认得出是刚才那条线。
- 粉笔字在 1280×720 下读得清，颗粒没有把笔画吃断。
- 擦和写不同时发生在同一个地方（板擦离开以后才写对的那一笔）。
- 推拉的那几帧是拖影，中间的铝框读得出来；最后一帧板擦、粉笔、旧粉痕都回到第一帧的样子。

## 相关资源

- `video-types/01-math-science-explainer.md`、`video-types/06-paper-explainer.md`、`video-types/10-long-explainer.md`。
- 同家族的 `whiteboard`（白板速写）、`dark-math`（暗底数学）。
