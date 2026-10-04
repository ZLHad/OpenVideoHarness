# CRT 终端 · crt-terminal

一句话：画面就是一台单色 CRT 终端：琥珀或绿色荧光在深色玻璃上发亮，所有东西都是等宽网格里的真实字符，信息靠打字、滚屏和光标闪烁出现，消失的字留着余辉。适合讲机器、代码、黑客、远程通讯、系统日志，以及"电脑在想什么"。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：0.05 s 一条满宽的亮线闪出，0.25 s 前展开成满屏并过曝，再退成琥珀（hook）；启动日志以机器速度、双倍大小打出，0.8 s 逐行清屏，留余辉；"> title" 之后，人以不均匀的节奏打出双倍宽高的标题，中文分两次输入法上屏；母题是 `$ tree film/` 打出的 ASCII 树：outline/ → storyboard/ → draft.mp4，每项后面是中文，draft.mp4 的渲染进度条按整格填到 3.6 s 正好 100%，然后反白显示 READY；渲染日志每 0.4 s 滚一行，光标每 0.5 s 闪一次；底部反白状态栏显示正在渲染的真实帧号；4.0 s 关机，塌成一条线再缩成一个点，点只留 0.16 s；4.36 s 管子重新亮起，反白显示风格名。实际字体：Menlo、PingFang SC。配乐记成 150 BPM（75 BPM 的双倍网格），`meters` 让 0.8、2.0、4.0、4.4 s 都落在拍上，全片单声道、干声：开机段只有 60 Hz 电源嗡声（`hum`），启动日志的 `tick` 都听得见；0.8 s 人开始打字时，低音区的方波（`pulse`，外加一个高八度、偏 14 音分的第二振荡器）一拍一个音走 E2–B2–E3；`tree` 渲染段放慢成二分音符 C3–G2–E2，2.15 s 命令回车和 3.6 s READY 各有一串调制解调器式的哔声（`pulse` 在约 1976 / 2217 Hz 之间按 32 分音符交替）；关机段只剩一个 E1 低音和嗡声；4.4 s 重新亮屏，方波动机回来，再响一串连线哔声。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《Alien》飞船电脑的屏幕图形 | 1979 · 导演 Ridley Scott；屏幕图形由 System Simulation 制作 | 单色线框加等宽字符表现"系统在工作"：框不动，框里的数字在跳 |
| 《WarGames》 | 1983 · 导演 John Badham；指挥中心大屏的图形由 HP 9845C 预先渲染 | 人和机器的对话以打字呈现，一个字一个字地出来；机器回答的节奏本身就是表演 |
| DEC VT100 视频终端 | 1978 · Digital Equipment Corporation | 80 × 24 的字符网格、反白、双倍宽双倍高的行；一块屏幕就是全部界面 |
| 单色显示器荧光粉 P1 / P3 | 通用规格 | P1 绿（峰值约 525 nm）、P3 琥珀（约 602 nm）；荧光有余辉，熄灭的字会拖尾 |

核实：《Alien》屏幕图形的制作方来自 Wikipedia（System Simulation 条目）和参与者 Brian Wyvill 的自述；《WarGames》大屏的做法来自 Wikipedia 和 HP 9845 Project；VT100 的发布时间和字符模式来自 Wikipedia；荧光粉型号和峰值波长来自 Wikipedia（Monochrome monitor 条目）。

**不照搬**：不用任何电影里的界面文字（包括那些著名的问候和提问）、计算机名、公司名和界面字体；不用真实机构的名字和标志。

## 视觉语法

- **色板**：单色，一种荧光粉贯穿全片。琥珀是默认，绿色是备选。

  | token | hex | 语义 |
  |---|---|---|
  | bg 玻璃（琥珀管） | `#0D0804` | 没点亮的玻璃，不是纯黑 |
  | 暗琥珀 | `#6B3A00` | dim 属性、背景日志 |
  | fg 琥珀 | `#FFB000` | 正常亮度的字 |
  | accent 亮琥珀 | `#FFE3A3` | bold 属性、反白块、光标；这是亮度上限，bloom 之后字心也不能更亮 |
  | 绿管玻璃 / 暗绿 / 绿 / 亮绿 | `#050A06` / `#0E5A1E` / `#33FF66` / `#C8FFD6` | 换成 P1 绿管时整套替换 |

  强调只靠亮度（dim / normal / bold）和反白，不加第二种色相。
- **字体**：全片一种等宽字体：Menlo（fallback Monaco、Andale Mono）。本机没有系统级的 SF Mono，不要写。中文每字占两个字符格，用 PingFang SC，字号取格高的 0.95。标题用 VT100 式的双倍宽双倍高行。
- **构图**：字符网格铺满屏幕的安全区：1080p 下格宽 24 px、格高 48 px，约 70 列 × 20 行；最后一行是反白状态栏，兼做字幕。屏幕有圆角（r = 40 px）和桶形弯曲（k ≈ 0.04）；只有片尾可以拉出屏幕看到机壳。
- **质感**：扫描线每 3 px 一条，强度 0.25–0.35（亮处变窄）；bloom 两三级模糊（σ 约 2、6、14 px），总量 0.5；暗角；逐帧亮度抖动 ±1.5%，由帧号决定。**没有 RGB 子像素栅格**，单色管没有。

## 运动语法

帧数按 30 fps 计。

- **一切都在格子上**：字符只会整格出现、整格跳动；打字、滚屏、计数都是离散的。连续变化的只有三样：字号（等于镜头推拉）、CRT 的物理效果（开关机、余辉、闪烁）、转场。
- **打字速度**：机器输出 12–25 ms/字，日志按行滚，40 ms/行；命令 40–60 ms/字；人打字 60–180 ms/字，由种子决定快慢，在词与词之间停顿。光标闪烁周期 530 ms（亮 265、灭 265）。
- **余辉**：字熄灭后亮度按 `e^(−Δt/τ)` 衰减，P3 琥珀 τ ≈ 0.12 s，P39 长余辉绿 τ ≈ 0.4 s；用解析式算，不存状态。
- **缓动**：开机和推拉用 easeOutExpo `cubic-bezier(0.16,1,0.3,1)`；关机塌缩用 easeInExpo `cubic-bezier(0.7,0,0.84,0)`；文字本身不缓动，一律 steps。
- **时长**：一行要读的输出打完后停到读完再出下一行（打字的时间不算读的时间；读时规则见 TASTE_CHECKLIST #5）；每 1.5–3 s 一个新事件（新行、新命令、新状态）。开机 12 帧。
- **转场**（只用这 3 种）：
  - 清屏（clear-screen）：整屏从上到下逐行熄灭，每行 2 帧，熄灭的行带余辉；
  - 字号推拉（grid-zoom）：格子变大就是推近，推进一个字符，它里面是更小的文字；
  - 关机（power-off）：画面在 0.15 s 内压成一条亮横线，再在 0.15 s 内缩成一个点，点的余辉慢慢熄灭。
- **镜头**：固定。屏幕就是镜头，推拉只靠字号。
- **文字动画**：打字机（typewriter）是签名；解码乱码（decode）全片最多一次，用在"解密"这一个剧情点上。

## 声音语法

- **配乐**：冷、极简、近。E 小调，75 BPM（30 fps 下一拍 24 帧）。签名是低音区失谐的方波琶音：`pulse` 的 `duty` 0.5，`sus` 1（不要芯片式的音量台阶），低通 1.5 kHz，再叠一个高八度、偏 14 音分的第二振荡器（`detune` 1214）；一拍一个音或更慢，比 `fui-hud` 的十六分音符滤波音序慢、干、近。`hum` 的 60 Hz 电源嗡声（风扇只留一点）从头铺到尾，当机房底噪；机器应答用调制解调器式的哔声，两个高频（约 1976 / 2217 Hz）按 32 分音符快速交替。全片单声道、`space: dry`，像终端自己那只小喇叭。很多段落没有音乐，只有嗡声。不做芯片音乐。样片的 score 写成 150 BPM（75 BPM 的双倍网格，拍子不变密，只是让 0.8、2.0、4.0 s 都落在拍上），`master_db` 设为 −4（比默认低 3 dB），给打字声和 `tick` 让出位置。
- **音效**：人打字每个字一声 `typing`（或逐字 `click`），机器输出只在行尾一声 `tick`，否则太吵；回车用更重的 `click`；报错用 `error`；开机用低通的 `impact` 加嗡声；关机用 `swish_rev` 的反向吸入。
- **声画关系**：光标闪烁的等待里只留底噪，这是悬念；关机那一刻所有声音跟着塌缩，最后只剩一声很轻的高频余音。
- **样片拟音**：`events.json` 22 个事件，由 `swatch.js` 导出的 `FOLEY` 经 `node styles/_swatch/foley.mjs <slug>` 生成，落点全部引用动作所用的同一张时间表，声像取发声物体的屏幕 x（`(2x/W − 1)·0.7`），按 `profile=swatch` 混在配乐下：开机 `boom`；开机日志每行行尾一声 `tick`；清屏 `toggle`；`> title` 和标题每个词各一段 `typing`（人手打字节奏表同时驱动画面和声音）；两次输入法上屏 `click`；`tree` 命令行尾 `tick`，渲染日志开始 `tick`，进度条每两格一声 `tick`，READY 一声 `success`；关机 `glitch` + 塌成亮点时 `swish_rev`，反白重开只用一声 `click`（`boom` 的长尾会在 5 s 片尾被硬截断，qa 报成 click）。
- **样片的转场音效**：`tape`：关机收成一个点时是一声磁带停转（`dir: down`，0.2 s），不用 swish_rev。

## 适合与不适合

- **适合**：08 科技梗、AI 和安全话题的快剪；03 CLI 和开发者工具的发布片；02 计算机史、网络安全科普；04 合成器风格的 MV。
- **不适合**：需要彩色图表或照片的内容；温暖的人情故事（除非要的就是这个反差）；大段中文长文。
- **容易被误用成**：绿色字符瀑布（数字雨）、给 VS Code 截图加扫描线、满屏 glitch。

## 禁止项

1. 给普通画面套一层"ASCII 滤镜"。字符必须是网格里真实的字符。
2. RGB 色差、彩色子像素栅格。
3. 文字平滑滑动或淡入。字只能打出、跳格、滚屏。
4. 数字雨、满屏乱码当装饰。
5. bloom 把字烧成白斑：字心亮度不超过 `#FFE3A3`，光晕不超过字本身。
6. 纯黑 `#000` 玻璃。

## Prompt 块

```text
Visual style: monochrome CRT terminal. Everything on screen is a real character on a fixed monospace grid (Menlo; about 70 × 20 cells at 1080p, 1:2 cells), lit by one amber P3 phosphor on dark glass #0D0804: dim #6B3A00, normal #FFB000, bold and inverse-video #FFE3A3 as the brightness ceiling. No second hue, no RGB fringing, no subpixel mask. Glass physics: 3 px scanlines (0.3), soft bloom that never outshines the glyph cores, slight barrel curvature with rounded corners, vignette, tiny frame-seeded flicker; characters that switch off leave an afterglow decaying with tau 0.12 s. Text never slides or fades: machine output types at 12–25 ms per character, a human types unevenly at 60–180 ms with pauses between words, the cursor blinks every 530 ms, logs scroll by whole lines. Titles use double-width, double-height lines; Chinese takes two cells per character. The only continuous motion is font size used as the camera, and CRT power-on/power-off. The bottom row is an inverse-video status line that doubles as subtitles. Transitions: line-by-line clear screen with afterglow, zoom by growing the grid, power-off collapsing to a line and then a dot. Sound: cold 75 BPM minor, a slow low detuned square-wave arpeggio, modem-like bleeps when the machine answers, a key click per typed character, a heavier return, a 60 Hz mains-hum room tone, mono and dry; long stretches with no music at all.
```

## 引擎做法

- **首选 HyperFrames**：Canvas2D 把字符画进一张灰度"电子束"图层（只记亮度），再用 `lib.shader` 做 CRT：桶形弯曲的 UV、几次采样的 bloom、亮度到琥珀的映射、扫描线、暗角和按帧号的抖动。
- **文字是 t 的函数**：`visible = typewriter(str, t, {start, cps})`；人打字的逐字时间表在 setup 里用种子生成（纯数据），逐帧只查表。光标 `on = floor(t / 0.265) % 2 === 0`。
- **余辉**：每个字符记下它的熄灭时刻 `t_off`，亮度 `= t < t_off ? 1 : exp(−(t − t_off) / τ)`。
- **关机**：在着色器里把 UV 的 y（再到 x）向中心压缩，同时把亮度推高，最后只剩一个点。
- **中文占两格**：排版时按"一个汉字 = 两个字符格"推进光标。
- 样片 `swatch.js`：逐段做法见开头"样片里"。实现要点：开机亮线是在电子束图层里先铺一层随时间衰减的整屏亮度，再让着色器把它压成一条线再展开；ASCII 树每行一次整行输出（机器速度），进度条按整格跳，READY 用反白。

## 自查重点

- 任取一帧：所有字符都落在格子上（CRT 弯曲除外）。
- 要读的句子打完后是否停 ≥ 1.5 s？
- bloom 之后，手机缩略图上的字没有糊成一片；要读的字用双倍行（中文 ≥ 46 px），80 列的小字只当背景日志。
- 消失的字有 0.1–0.4 s 的余辉，而不是瞬间消失或普通淡出。
- 从中间抽帧单独渲染，和整片逐像素一致（噪声、闪烁都由帧号决定）。

## 相关资源

- `references/repos/lemo-opuscar/styles/ascii-crt/STYLE.md`（LemoLab，CC BY 4.0）：字符按墨量排序成密度梯度、字号即镜头、余辉 τ、单色管没有 RGB 栅格、不做芯片音乐，这几条来自它；本文把它的"字变成图"换成了更日常的终端语法（打字、日志、状态栏、窗口）。
- `references/community-skills.md` §3：OpenMontage 的规则"CLI / 终端演示用合成录屏，不录真实屏幕"（AGPL，只读其思路）。
- `video-types/08-brutalist-meme.md`、`video-types/03-product-promo.md`；`playbook/08-vfx-and-motion-sources.md`（光效不能把字烧掉）。
