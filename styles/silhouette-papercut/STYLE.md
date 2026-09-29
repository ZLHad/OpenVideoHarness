# 剪影剪纸 · silhouette-papercut

三到五层剪纸前后叠放，角色是侧面的黑色剪影或红色剪纸，按每秒 12 张一格一格地动，镂空处透出后面一层的颜色。适合童话、寓言、民间故事和"一个人走过一段路"式的叙事，也适合给严肃题材一个手工、温和的外壳。

样片：`media/swatch.mp4`（5 s）· 封面 `media/poster.jpg`

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《阿赫迈德王子历险记》（Die Abenteuer des Prinzen Achmed） | 1926 · Lotte Reiniger，特效合作 Walter Ruttmann、Berthold Bartosch | 现存最早的动画长片。纸板和薄铅片剪成的铰接剪影，全部侧面表演；原始拷贝按场整体染色（各场具体色调未核实）；前景是蕾丝般的镂空枝叶和拱门 |
| 《猪八戒吃瓜》（常被称作《猪八戒吃西瓜》） | 1958 · 上海美术电影制片厂，导演万古蟾 | 中国第一部剪纸片：给纸偶装上关节，平面雕镂造型，背景贴在前后玻璃板上分层 |
| 《葫芦兄弟》 | 1986–1987 · 上海美术电影制片厂，导演胡进庆、葛桂云、周克勤 | 第一部剪纸系列片：大块面色 + 镂刻线，侧面走位，一格一格的跳动感 |
| 中国剪纸 | 2009 年列入联合国教科文组织人类非遗代表作名录 · 各地民间剪纸艺人 | 阴刻（在色块里刻线）与阳刻（留下线网）；锯齿纹、月牙纹；对折剪出的团花；剪处即画 |

**不照搬**：不复刻阿赫迈德王子、猪八戒、葫芦娃等角色和任何可识别的镜头，不描具体剪纸作品的纹样稿，所有纹样由代码生成。

## 视觉语法

默认是"剪影"一路（写进 tokens）：黑色剪影立在染色的背景前。需要中国味时切到"红剪纸"一路。两路不在同一个镜头里混用。

- **剪影色板**：
  - 背景染色：每场选一种，琥珀 `#E6A33E`（白天、室内，默认）、夜蓝 `#3E6A96`、林绿 `#5E8C4A`、晨玫 `#C9646A`；
  - 剪影层：近 `#16110D`（前景、主角）、中 `#4A2A1C`、远 `#9E5A2C`（越远越接近背景色）；
  - 强调：剪纸红 `#C62828`，全片只给一样东西（一盏灯、一朵花、一个信物）。
- **红剪纸色板**：宣纸 `#F2E8D0` 做白天底，靛蓝纸 `#1E2A4A` 做夜晚底；主角和窗花用 `#C8232A`，近处肢体亮一档 `#D4332F`，远处肢体暗一档 `#8E1420`；金箔 `#D6A843` 只在结尾出现。夜里背景一律是深浅不同的靛蓝纸，只有主角是红的。
- **字体**：
  - 片名：高反差衬线 `Didot` → `Bodoni 72`，做成剪出来的字（字腔是真的孔）；中文用 `Songti SC` Bold；
  - 字幕：`Baskerville` 40–48px 或 `Songti SC` 44–52px，放在画面下方的纸条上；
  - 小标签：`Kaiti SC`。
  - 样片实际用字：`Didot` 112px（英文剪字）、`Songti SC` Bold 74px（中文）、标签 `Songti SC` Bold 50px + `Didot` Italic 28px（刻在地面纸带里）。
- **构图**：
  - 表演在一条水平舞台带里完成（y 0.55–0.85H），地平线 0.8H；角色高 0.3–0.5H，全部侧面；
  - 轮廓要读得出：手臂和身体之间留缝，道具伸出轮廓外，两个角色不重叠；
  - 前景镂空框（枝叶、拱门、窗棂）只沿画面边缘，占画面不超过 20%；
  - 层次 3–5 层，远层小、浅、靠近背景色。
- **质感**：
  - 纸边：轮廓采样成折线后加 0.35px 的低频抖动，建筑用直线段加抖动，不做平滑；
  - 纸厚：每层在下一层投 4–8px 偏移、6px 模糊、`rgba(20,10,5,.35)` 的影子；
  - 背景：细纸纤维 + 一个柔和的径向亮区（在中层后面），不用线性渐变。

## 运动语法

帧数按 30 fps 计。

- **步进**：角色姿势按 12 fps 取样，`tp = Math.floor(t·12)/12`；镜头、光、飘落物按 30 fps 平滑移动（镜头也步进会被看成卡顿）。
- **缓动**：进场 easeOutCubic `cubic-bezier(0.33,1,0.68,1)`，出场 easeInCubic `cubic-bezier(0.32,0,0.67,0)`，都在步进后的时间上计算；spring：stiffness 200、damping 20（ζ≈0.71），只给落地和道具。
- **微动**：每层纸 ±1.5° 的轻摆，0.3–0.6 Hz，也按 12 fps 步进，各层相位用 `hash(layer)` 错开。
- **时长**：进场 15 帧（0.5 s，即 6 格）；每个画面至少停 1.4 s；每 2.2 s 发生一件新事。
- **转场**：全片只用三种：圆形 iris（默片式的收放）、剪影层横滑（一整层前景剪影横着滑过，完全遮住时切换）、揭纸（红剪纸一路专用：夜晚那张纸从一角掀开，露出下面的白天）。
- **镜头**：横移（pan），多层视差：远 0.3、中 0.6、近 1.0、前景框 1.4。不做 3D，不转角度。
- **文字动画**：剪纸字（cutout）。字母按 12 fps 一格一个弹上来，每个字母落下时放大 1.15 倍停一格再回到 1。

## 声音语法

- **配乐**：剪影一路：`bin/vh music`，`bpm: 96`，`key: "A"`，`mode: "minor"`；`arp` 做八音盒式的拨弦，`pad` 做弦乐底，`bass` 只在后半段进来；不用 `bell`（它的编钟音色和五声取音会把这一路拉向中国味）。红剪纸一路：改成 `key: "D"`、`mode: "major"`（中国色层取 D 宫五声）、`bpm: 120`，用 `zheng`、`dizi`，`clap` 当木鱼，`taiko` 打重拍。
- **音效**：剪刀开合（金属剪切声 2.5–9 kHz + 一声纸纤维断裂）、纸片滑动、纸片飘落、卡纸落地的闷响（55 Hz 左右，不用肉体撞击声）、翻纸。内置库可以先占位：剪刀用 `shutter` 叠 `tick`，纸片滑动用 `whoosh`，落地用压低的 `boom`，翻纸用 `swish_rev`。
- **声画关系**：每一剪、每一次落地都对着一个八分音符。高潮前 0.5 s 屏息：拨弦撤掉，只留 `pad` 低低地垫着，揭纸或 iris 张开时齐奏回来；不做数字静音。
- **样片小样**：样片的 5 s 声音小样（`score.json`）：150 BPM，A 小调；只有轻巧的 `arp` 拨弦和 `pad`，2.0 s 房子立起来时加一层 `bass`，4.0 s iris 收拢时回到拨弦。

## 适合与不适合

- 适合：`07` 童话和寓言短片、`04` A 路线的民谣或轻古典 MV、`02` 民俗和历史故事的科普、`06` 人文类讲解里的"故事插页"。
- 不适合：需要表情特写、正面对话、复杂数据的片子。硬套会变成"黑色贴纸在黄色背景上平移"。

## 禁止项

- 角色姿势用 30/60 fps 平滑补间：失去一格一格的手工感；
- 在剪影内部画线条、五官、衣纹：剪影只有轮廓和镂空；
- 纸边完美矢量、没有厚度和投影；
- 正面角色、手臂和身体粘成一团的姿势；
- 红纸主角放在红背景上；
- 把剪纸和皮影混用：剪纸、剪影是正面光、不透光的纸；皮影是背光、半透明的染色皮子，有签子。

## Prompt 块

```text
STYLE: layered cut paper. 3–5 flat paper layers stacked with soft 6px shadows (offset 4–8px). Default register: pure black silhouettes (#16110D near, #4A2A1C mid, #9E5A2C far) in front of a single tinted backdrop per scene (amber #E6A33E by default; night blue #3E6A96, forest green #5E8C4A or dawn rose #C9646A), with one red paper object #C62828 as the only accent. Alternative register: red paper figures on rice paper by day and indigo paper by night.
Everything is in profile on one horizontal stage band; silhouettes must read: gaps between arms and body, props sticking out of the outline, no interior lines. Lace-like cut foliage and arches frame the edges only. Hand-cut edges with slight wobble; no smooth vector curves.
Character poses step at 12 fps; camera, light and falling pieces move smoothly. Each layer sways ±1.5° with offset phases. Parallax pan across layers.
Transitions: a circular silent-film iris, a full-frame foreground silhouette sliding across, or a paper sheet peeled from the corner. Titles are cut-out letters whose counters are real holes, popping in one per step.
Sound: scissors, paper slides, cardboard thuds, a music-box pluck and soft pad in A minor at 96 BPM (or zither and flute in D pentatonic for the red register).
```

## 引擎做法

- **首选 HyperFrames + Canvas2D**；已经在用 ClaudeAnimationBase 的项目，可以用 p5 画同样的层（07 类型文档的剪纸一节），但剪影要用硬边，不要 p5.brush 的水彩边。
- **纸片**：多边形 + `evenodd` 路径打孔；轮廓先按弧长重采样，再加 `0.35·vnoise(s·0.02 + seed)` 的法向抖动。
- **镂空纹样生成器**：锯齿行、月牙行、云纹、团花都写成函数；团花只设计 1/8 楔形，镜像 8 次。
- **投影**：每层先画一次偏移、模糊的深色副本，再画本体；模糊副本按层预先渲染到离屏画布并缓存，比每帧 `ctx.filter = 'blur(6px)'` 更快，也更容易保证逐帧一致。
- **步进**：角色、字、纸层摆动都用 `tp`；镜头和光用原始 t。
- 关节用 2D 仿射层级（肩 → 肘 → 手），每段一个多边形，关节处多边形重叠，剪影里看不出接缝。

## 自查重点

- 把一帧转成纯黑白看：每个角色的动作还读得出来吗？
- 用 strip 看 0.5 s：角色姿势是否每 2–3 帧才变一次（30 fps 下按 12 fps 步进），镜头是否每帧都在走；
- 放大纸边：有抖动、有厚度影子、没有平滑的贝塞尔弧；
- 数每帧的红色物件：剪影一路只有一样；
- 前景镂空框是否挡住了表演带。

## 相关资源

- `references/repos/lemo-opuscar/styles/papercut-red/STYLE.md`（LemoLab，CC BY 4.0，https://creativecommons.org/licenses/by/4.0/）。本文的红剪纸一路改编自该文：夜里背景用靛蓝纸、主角才用红纸，阴刻 + 内轮廓分开红叠红，团花按 1/8 楔形镜像，纸边抖动和纸厚投影。数值按本仓库重定。
- `references/repos/lemo-opuscar/styles/paper-lantern/`、`paper-popup/`（纸雕灯箱、立体书，CC BY 4.0）。
- `references/repos/story-to-handdrawn-video/references/handdrawn-style-library.json` 的 `hs-225`（肌理剪纸拼贴绘本，MIT）。
- `video-types/07-hand-drawn.md`（剪纸风：3–5 层、投影 4–8px、12 fps、±1–2°）、`playbook/03-motion-design.md`。
- 相近预设：`styles/shadow-puppet/`（背光、半透明、有签子，和本预设分清）。
