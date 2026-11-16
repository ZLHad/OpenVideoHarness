# 白板速写 · whiteboard

一句话：一支马克笔在一块白板上边讲边画，画过的留着，讲到哪里镜头就沿着这块板走到哪里。适合论文讲解、方法和流程、"第一次把一件事讲明白"的讲解片：观众看着图一笔一笔长出来，顺序本身就是讲解的顺序。

**怎么借**：白板讲解好看，是因为观众看得见一只手在想：图按讲的顺序一笔笔长出来，长到哪里就讲到哪里。最该借的是手速。每一笔起笔慢、中间快、收笔慢，线宽和马克笔的声音都跟着这条速度曲线走；匀速描出来的线，颜色再像马克笔，看着也是软件在画。其次是不翻页：画过的留在板上，讲到下一件事就往旁边画，镜头也往旁边走，前面的图一直是后面的上下文。颜色只分工、不装饰：黑色画结构，蓝色画流动的东西，红色只圈出要看的那一处。下面的数是样片里的，换了题目就按理由重定；字号下限和读时照样要守，手写体也一样。

样片：`media/swatch.mp4`（10 s，完整视频在 Release `styles-media`，`tools/fetch_media.sh whiteboard` 取回）· 竖版 `media/swatch-portrait.mp4` · 封面 `media/poster.jpg`（t = 8.0 s）· 2 秒预览 `media/preview.mp4`（2.4–4.4 s）

样片里讲的是"每一帧都是 t 的函数"：先画一条时间轴，再画一张写着代码的卡片（一对花括号、三行），一支蓝笔画箭头指向三格画面，每格里一个蓝点，低、高、低，连起来是一次弹跳；红笔圈住中间那一格。然后手写标题、英文一行和字幕。最后镜头沿着板滑到一段干净的白板上，回到第一帧。实际字体：中文 Hannotate SC（手札体，macOS 按需下载的系统字体，没有时回落到 Kaiti SC、PingFang SC），英文 Noteworthy Bold。

## 样片

| 拍 | 时间 | 本风格的做法 |
|---|---|---|
| 立住世界 | 0–1.5 s | 0.1 s 马克笔落下，一笔画出横贯半个画面的时间轴、箭头、字母 t 和三个刻度；板上有擦过没擦干净的灰影 |
| 招牌动作 | 1.5–4.5 s | 一笔一笔地画：代码卡片、三格画面、蓝色箭头和三个点，每一笔都是起笔慢、中间快、收笔慢；换颜色只发生在笔抬起来的时候 |
| 真实字号的字 | 4.5–9.0 s | 红圈落下，然后手写标题（96 px，每字 0.11 s）、英文一行（44 px）、字幕（48 px，每字 0.06 s）；写完笔退到右边，字停 2.2 s 以上 |
| 收住 | 9.0–10 s | 镜头沿着同一块板滑过 1800 px，画过的留在原处出画，停在一段干净的板上，笔也回到开头的位置 |

这一支是 10 秒：手写本身就是招牌，写完标题和字幕要 2 秒，再留够读一遍的时间，8 秒放不下。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| RSA Animate《Drive: The surprising truth about what motivates us》 | 2010 · 英国皇家艺术学会（RSA），演讲 Dan Pink，手绘 Andrew Park（Cognitive Media） | 画随着讲话一笔一笔出来，图和字混在一张大板上，画过的都留着；镜头在板上移动，而不是换页 |
| MinutePhysics《Is it Better to Walk or Run in the Rain?》 | 2012-12-20 · Henry Reich | 一张白纸上的马克笔画，边讲边画出来：黑线画雨滴和走路的人，几笔就把问题画成能比较的两种情形，图比字多 |
| *The coordination of arm movements: an experimentally confirmed mathematical model* | 1985 · Tamar Flash、Neville Hogan，《Journal of Neuroscience》5(7):1688–1703 | 人手从一点画到另一点时，速度是一条钟形曲线：起止慢、中间快（最小加加速度）。样片的笔速、线宽和笔声都用这条曲线 |

核实：RSA Animate《Drive》的年份（2010-04-01 上线）、演讲者和手绘者对照了 RSA 官网（thersa.org/comment/2010/04/rsa-animate---drive）；MinutePhysics 的创办人、年份和《Is it Better to Walk or Run in the Rain?》的上线日期对照了 Wikipedia 的 MinutePhysics 条目；Flash 与 Hogan 的论文题目、卷期和页码对照了 Crossref（doi:10.1523/jneurosci.05-07-01688.1985）。都在 2026-11-16。

**不照搬**：不用 RSA Animate 的画面、角色和那只入画的真手，也不用 MinutePhysics 的角色和片头。样片里只有一支画出来的马克笔，没有手。

## 视觉语法

- **色板**：板 `#F5F5F1`（略暖的白，不是纯白）；黑笔 `#22252B` 画结构、框、轴和字；蓝笔 `#1D5BB5` 画流动的东西（箭头、数据、在动的那个点）；红笔 `#D23A2E` 只圈出要看的那一处，一屏最多一次；绿笔 `#1E8A4A` 留给"对了、通过了"。颜色一旦定了含义，整片不换。
- **板面**：擦过没擦干净的灰影（大片的擦痕 3.5–7.5%，断续的旧线 3.5–7.5%）让它像一块用过的板；左上一块柔和的反光，下缘略暗。灰影要淡到不和墨线抢。
- **线**：8 px（1080p），起笔有一个小墨点；快的地方细一点（最多细 22%）、干一点（颜色往板色混 10%）。线走 1.6 px 左右的手抖，框的最后一笔越过起点一点，圆不完全闭合。
- **字**：标题和字幕是手写体（样片用 Hannotate SC 粗体），英文用 Noteworthy Bold；字写在图的下方或旁边，和图一样是"写上去的"，不是贴上去的。
- **构图**：一块板就是整个舞台。图从左往右、从上往下按讲解的顺序排开，留白多；字在图下方，字幕在下三分之一。

## 运动语法

- **笔速**：每一笔按最小加加速度曲线走：位置 `10u³ − 15u⁴ + 6u⁵`，速度在中间最大。笔画时长按长度定，长笔平均更快（时长约 ∝ 长度^0.6）；样片取四档：0.07、0.14、0.34、0.62 s。笔和笔之间抬起来飞过去，0.04–0.1 s，影子跟着离远一点。
- **写字**：一个字一个字地从左往右露出来，笔头在字上走 Z 字。标题每字 0.11 s，字幕每字 0.06 s，比真写快，比打字机慢。
- **镜头**：一镜到底。画的时候镜头几乎不动，只有很慢的一呼一吸（缩放 2%）；换内容时沿着板滑过去（样片 1800 px、0.97 s、inOutCubic），带半帧快门的横向拖影。画过的东西从来不消失，只是出画。
- **转场**：滑到板上干净的地方；或者红圈圈住一处，镜头推进去接着画细节。不用淡入淡出和翻页。
- **签名**：手的速度。同一张图，匀速描出来像软件在画，有快有慢才像人在讲。

## 声音语法

- **配乐**：讲座间隙的尼龙弦指弹。120 BPM，G 大调，尼龙弦分解和弦、拨弦低音提琴、刷子，红圈落下时颤音琴敲一下；读字的那几小节只剩吉他和刷子。用 `bin/vh music` 的 `nylon_pm`、`upright_pm`、`brush`、`vibraphone`。
- **音效**：每一笔一个马克笔声：落笔的一下轻敲，然后摩擦声和断续的吱声，跟着笔速起落，长度和笔画一样。这些声音由 `styles/_swatch/custom_sfx.py` 带种子合成，渲染样片时生成在 `styles/whiteboard/sfx/`（不进 git），没有录音素材。滑板时一声 air。
- **声画关系**：笔声密，配乐稀；笔声是 detail 一级，红圈那一声是 hero。读字时不再加音效。

## 适合与不适合

- 适合：论文讲解（06）、原理讲解（01）、知识短视频（02）的方法、流程、因果链、对比；需要观众"跟着画一遍"才懂的东西。横竖都成立，竖版把图排成一列。
- 不适合：情绪片、发布片的高光段、需要真实质感的产品；图本身就很复杂（几十个节点）时，一笔一笔画会太慢，先画骨架、再整块浮现细节。

## 常见误用及原因

- **线是匀速描出来的**：看上去就是 SVG 描边动画，因为人手从来不匀速。救法：每一笔按最小加加速度曲线走，时长随长度增长但增得比长度慢（约 ∝ 长度^0.6），快的地方线细一点、干一点；笔和笔之间留一点抬笔的空。
- **画满了就整页换掉**：前面的图一走，观众得重新找上下文，看着像在翻幻灯片。救法：往旁边画，镜头沿着板滑过去；真要腾地方，就让板擦当着观众擦。
- **红色到处都是**：焦点散了，红圈就不再是"看这里"。救法：一屏只红一处，别的强调交给位置、大小和先后。
- **入画一只写实的手**：照片质感的手和画出来的线不在一个世界里，还挡住正在画的地方。一支画出来的笔就够说明"有人在画"。
- 【底线】手写体读不出来：换一款更规整的手写字体或加粗，过字号下限和读时（`bin/vh style check --text`）。

## Prompt 块

```text
A dry-erase marker explains the idea by drawing it live on one long, slightly warm white board (#F5F5F1) with faint
ghosts of earlier erasures. Diagrams appear stroke by stroke in the order of the explanation; nothing is erased —
when the board fills, the camera slides along the board to clean space. Every stroke follows a human hand's speed
profile (minimum jerk: slow off the mark, fastest mid-stroke, slow into the end); lines thin and dry slightly where
the hand is fast, boxes overshoot their first corner, circles don't quite close. Black for structure, blue for things
that flow, red only to circle the one thing to look at, green for "correct". Titles and captions are handwritten in a
legible marker hand, revealed glyph by glyph under the pen. One drawn marker (no real hand) leans down-right from the
nib; when lifted its shadow moves away. Sound: soft nylon-guitar fingerpicking and brushes; each stroke has its own
marker squeak shaped by the same speed curve. Sample values (try, then depart): 8 px lines at 1080p, strokes of
0.07/0.14/0.34/0.62 s, title 0.11 s per glyph, slide 1800 px in ~1 s with a half-frame horizontal smear.
```

## 引擎做法

- HyperFrames 的 canvas 场景；笔画在 `styles/_swatch/vendor/hand.js`：`prep()` 在 setup 里把路径按 4 px 重采样并加一点低频手抖，`drawStroke()` 按 `mj(u)` 画到 t 时刻的位置，一小段一小段画，每段按那一点的手速定粗细和颜色；`pen()` 给出笔头在 t 时的位置（在画、在飞、在等）。全是 t 的纯函数。
- 字：`layoutText` 排好，每个字一段 clip 矩形从左往右展开，笔头沿一条 Z 字路径跟着走。
- 镜头滑动：整块板（灰影、墨线、字）先画进一个离屏图层，再按速度叠 n 份做横向拖影（每 3 px 一份，最多 32 份）。灰影是一张宽 1800 px 的贴图，按滑动距离循环，所以最后一帧和第一帧是同一段板。
- 笔声：`custom_sfx.py` 按同一条速度曲线合成，时长和 `swatch.js` 的四档一致；`FOLEY` 引用它们，`node styles/_swatch/foley.mjs whiteboard` 写 `events.json`。

## 自查重点

- 抽一笔的 strip（5–6 帧）：起笔和收笔处每帧走得少，中间走得多；不是每帧等距。
- 换颜色只在笔抬起时；红色一屏只出现一次。
- 字写完以后，笔不压在任何字上；手写体在 1280×720 下还读得清。
- 滑动的那几帧是一道拖影，不是几层叠影；最后一帧和第一帧是同一段干净的板。

## 相关资源

- `video-types/06-paper-explainer.md`、`video-types/01-math-science-explainer.md`；`playbook/03-motion-design.md`（字号和读时）。
- 同家族的 `chalkboard`（黑板粉笔）、`blueprint`（工程蓝图）、`gold-line-dark`（暗底金线描）。
