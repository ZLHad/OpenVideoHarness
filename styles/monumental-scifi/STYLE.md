# 纪念碑科幻 · monumental-scifi

一句话：巨大的形体、层层的雾、极慢的镜头、极少的字，再加一条低到胸腔的持续音。它用尺度差讲"人面对一个比自己大得多的东西"。适合产品和技术发布的 teaser、宇宙和未来题材、大片感的开场与片名。本仓库自己的介绍片（`showcase/04-intro-film/`：一镜到底穿过雾中的"帧的档案馆"，琥珀色是唯一的光）就属于这一族。

样片：`media/swatch.mp4`（5 s，含 `score.json` 配乐）· 封面 `media/poster.jpg`（t = 3.0 s）

样片里：三块黑色巨碑高于画框（被画框顶部裁掉），碑后是唯一的主光——琥珀色的雾。开场几乎全黑，碑和天空只差一层暗。0.1 s 第一记 braam 落下，一道钠光地平线在同一帧横贯全宽点亮，碑后的雾光随之涌起（先冲高、再回落），镜头开始缓慢下降。片名放在地平线下的暗地面上：76 px 宽字距大写，对比度远高于 7:1。镜头全程匀速横移，远、中、近几层有视差；2.0–4.0 s 再叠一段匀速慢推（线性，不加缓动，碑层约放大 3.6%）。2.0 s 起三块碑依次点亮：大纲只亮边线，分镜亮起接缝，初版的琥珀光缝在 2.8 s 点燃；名字刻在碑面上。初版碑脚下站着一个 52 px 的人，挡在光前面。3.2–4.0 s 是屏息：一个光点沿光缝匀速往上爬，雾光慢慢涨起，人影被拉长，三者在 4.0 s 一起到顶。4.0 s 第二记 braam，镜头加速推进光缝，整帧被雾吞没，再从雾里显出结束画面。实际字体：Avenir Next Medium、PingFang SC（样片没有用等宽字）。配乐 150 BPM，走《银翼杀手 2049》的 braam 加 CS-80 一路：0.1 s 第一记 `braam`（D，和拟音 `boom` 同时落），低鸣一直拖到 2.6 s；0.8 s 起 `cs80` 铜管感的 pad 慢慢涨起（Dm → Bbmaj7），底下一条 `drone` 持续低音；2.0 / 2.8 s 碑点亮时是两记低通过、很远的 `timpani`；3.2–4.0 s 一小节是屏息：没有打击，也不放任何拟音，只剩 drone 和一个 Ebmaj7（bII）的 CS-80 渐强，把人推向 4.0 s；4.0 s 第二记 `braam` 回到 D，定音鼓同落。大教堂混响（rt60 6.5 s）。全片 braam 只有这两记：0.1 s（配乐 `braam` + 拟音 `boom`）和 4.0 s（配乐 `braam`）。其余拟音都是低沉的 `whoosh`，按距离做远：2.05 / 2.35 s 碑的点亮、2.8 s 光缝点燃、4.3 s 推进光缝。拟音的落点写在 swatch.js 的 `FOLEY` 常量里，`events.json` 由它生成。

## 学习对象

| 作品 | 年份 · 作者 / 工作室 | 从它身上学什么 |
|---|---|---|
| 《银翼杀手 2049》*Blade Runner 2049* | 2017 · 导演 Denis Villeneuve；摄影 Roger Deakins；美术 Dennis Gassner；屏幕图形 Territory Studio；配乐 Hans Zimmer、Benjamin Wallfisch | 整场只有一种有色光（橙色的霾）罩住一切；巨大的建筑和雕像把人压成一个小剪影；雾把纵深分成几层 |
| 《降临》*Arrival* | 2016 · 导演 Denis Villeneuve；摄影 Bradford Young；配乐 Jóhann Jóhannsson | 低饱和的灰；一个巨大的单体悬在雾里，镜头极慢地逼近；声音以人声和持续音为主，几乎没有旋律 |
| 《星际穿越》*Interstellar* | 2014 · 导演 Christopher Nolan；摄影 Hoyte van Hoytema（约三分之一镜头用 IMAX 70mm）；配乐 Hans Zimmer，管风琴由 Roger Sayer 在伦敦 Temple Church 演奏 | 一艘小飞船对着一个巨大天体；持续音加管风琴的"呼吸"；机器人是没有脸的方块 |
| 《2001 太空漫游》*2001: A Space Odyssey* | 1968 · Stanley Kubrick | 一块毫无装饰的黑色长方体就代表了全部的"外星"；对称构图，长时间的静 |

核实：导演、摄影、美术、配乐和 Territory Studio 的屏幕图形已对照 Wikipedia、Territory Studio 官网、ASC 与 Classic FM 的资料。三部新片的片名和字卡由谁设计**未核实**，所以本文只从成片总结"字极少、字距宽、字重细"的规律，不归到具体设计者名下。

**不照搬**：不做全息女人、巨型雕像、飞行车、贝壳状飞船、环形墨迹文字、四块板的机器人，也不做黑色长方体本身；不用任何原片的旋律和片名字形。

## 视觉语法

- **色板**：一种有色光加一组灰阶。

  | token | hex | 语义 |
  |---|---|---|
  | bg 深空 | `#0E0F10` | 空间 |
  | fog 雾灰 | `#6F6B64` | 距离：远处的物体逐渐溶进这个颜色 |
  | fg 字 | `#E9E6DF` | 片名、字幕 |
  | accent 钠光琥珀 | `#E8943A` | 唯一的有色光，只以"光"的形式出现：一道缝、一盏灯、地平线上的一条亮边、片名下的一条线 |
  | extra 钢灰 | `#3A3D40` | 结构 |
  | extra 冷昼 | `#B8C2C8` | 日景的天光；不和琥珀同场 |

  一场只选一种色温：暖霾场（琥珀 + 雾）或冷雾场（冷昼 + 雾灰），两种不在同一镜里混。
- **字体**：
  - 片名用 Avenir Next Ultra Light / Regular，全大写，字距 0.3–0.45em（静态设定，不做字距动画）；
  - 主片名 64–96 px，比"大字报"的习惯小得多；辅助字 44 px；
  - 中文用 PingFang SC 的 Ultralight / Light，字距 0.2em；
  - 元数据小字用 SF Mono → Menlo，30 px。这台机器上 SF Mono 只在 Terminal.app 包里，没有注册成系统字体，实际会落到 Menlo。
- **构图**：主形体占画面 55–80%；人或其他参照物不超过画面高度的 4%，尺度差至少 1:15。地平线压到 0.72H 或抬到 0.28H，不放在正中。字放在下三分之一或正中，一次只有一行。对称构图只留给"揭示"那一镜。
- **质感**：
  - film grain，强度 0.08；
  - 纵深分 3–5 层：近景剪影、中景主体、远景、天光；越远雾越浓（FogExp2 密度 0.012–0.03）；
  - 体积光：一道竖直或斜向的光束，亮度不超过字本身；
  - 暗角 0.25。

## 运动语法

帧数一律按 30 fps 计。

- **缓动**：
  - 镜头用 `cubic-bezier(0.65,0,0.35,1)`（easeInOutCubic），一个动作 4–8 s；
  - 字进场用 `cubic-bezier(0.22,1,0.36,1)`，36 帧淡入并上浮 8 px；
  - 字退场用 `cubic-bezier(0.64,0,0.78,0)`，24 帧。

  不用 overshoot、弹簧和快速甩镜。
- **时长**：一个画面至少 3 s；每 4 s 一个新 read，可以是新的一行字、新揭示的形体或光的变化。两个 read 之间靠镜头持续慢推和雾的漂移保持"有东西在动"。最快和最慢镜头的速度比约 3:1。
- **转场**（全片只用这 3 种）：
  - 穿雾推进：dolly 穿过一层雾，在雾最浓的那一帧换场；
  - 切黑 0.5–1 s，再切入大揭示，配一记 braam；
  - 从细节拉远，揭示尺度（pull-back reveal）。

  不用 crossfade，也不用 wipe。
- **镜头**：以 dolly 为主（推进或横移），速度恒定，可以一镜到底（oner）。允许一次极慢的上摇揭示高度（6 s 内仰 8–15°）。禁止手持。
- **文字动画**：stagger。英文逐字母淡入，每个字母间隔 60–80 ms，整行不超过 1.2 s；中文逐字，每字 100 ms。整行出完后停到读完（读时规则，TASTE_CHECKLIST #5）。

## 声音语法

- **配乐**：drone、管风琴感的 pad 和低频冲击（braam），60 BPM，D 小调，几乎没有鼓。`bin/vh music` 的做法（`parts`）：
  - `braam` 只给根音（`params.third` 3 是小三度），每次揭示一记，`onset_ms` 25 让它起音慢的冲击落在拍上；
  - `cs80` 当铜管感的 pad，`attack` 0.7 s 慢慢涨起来；揭示前那一小节换到 bII（D 小调里是 Eb），做一个渐强；
  - `drone` 给一个持续低音；
  - 远处的低鼓用 `timpani` 加 `lp` 500 和大一点的 `send`；
  - `space` 用 cathedral。

  样片的 `score.json` 就是这么写的。
- **音效**：
  - `boom` 配大揭示；
  - 远距离的低沉 `whoosh`（`dist` 3–5）配穿雾；
  - 2–4 s 的 `riser` 推向揭示；
  - 环境底是风声和低频嗡声。
- **声画关系**：大部分时间只有 drone，但不是静音。全片 braam 最多 2 次，每次都对应一次尺度揭示；braam 前 0.5–1 s 收掉高频，只留低音，像屏住呼吸。
- **样片的转场音效**：`swoosh_tonal` 加长而低的 `whoosh`：石碑的边、接缝和光缝点燃是三声远处的低音高滑音（越大越低）；4.3 s 冲进光缝是向上的长 whoosh（1.0 s，带共鸣）。

## 适合与不适合

- **适合**：03 发布 teaser（硬件、AI、基础设施、航天）；02 宇宙与未来类知识短片的开场；06 论文讲解里"这个问题有多大"的开场；片名页、章节页。
- **不适合**：信息密集或快节奏的内容（竖屏快剪、教程）；轻松可爱的品牌。
- **容易被误用成**：紫青星云加光晕粒子的"科幻壁纸"；字太大、太多；每一镜都砸一记 braam。

## 禁止项

1. 紫青渐变星云、满屏镜头光晕、粒子光球。
2. 同屏超过一行字，或主片名超过 7 个英文词。
3. 快速甩镜、手持、弹性缓动。
4. 两种有色光同时出现，例如琥珀加青色霓虹。
5. braam 超过 2 次；片中出现数字静音（屏息要靠低音垫着，不能静死）。
6. 雾只是一张半透明贴图。雾必须随深度变化，越远越灰。

## Prompt 块

```text
Visual style: monumental, minimal science fiction. Vast unadorned forms (slabs, arcs, towers) fill 55–80% of the frame, while the only human-scale reference stays under 4% of frame height. Three to five depth layers dissolve into exponential fog #6F6B64. There is one coloured light only, sodium amber #E8943A, appearing as a slit, a lamp or a horizon edge, over a grey scale from #0E0F10 to #E9E6DF. Camera: a slow, constant dolly or push, 4–8 s per move, easeInOutCubic, with one optional slow tilt-up to reveal height; no handheld, no whip pans. Type is sparse and small: one line at a time, thin geometric sans in wide-tracked caps (Avenir Next Ultra Light, 64–96 px, tracking 0.35em), letters fading in 70 ms apart and held for at least 2.5 s. Transitions: pushing through a fog layer, a cut to black before a scale reveal, a pull-back from a detail to full scale. Sound: 60 BPM D-minor drones and organ-like pads, a single low brass-like hit on the biggest reveal, and a held breath (low drone only) before it.
```

## 引擎做法

- 首选 HyperFrames 加一层 Three.js：`FogExp2`，`PerspectiveCamera` 的 fov 取 28–40；UnrealBloom 的阈值放在 1.0 以上，只让琥珀色发光。纯 2D 时用 5 层 Canvas 做视差，每层按深度混入雾色。
- **镜头路径**：写关键帧，用 Hermite 插值，按真实时间参数化。介绍片 `showcase/04-intro-film/js/main.js` 里的 `K[]` 是现成样板（只读参考，复制到自己的项目里再改）。
- **雾的漂移**：用 3D value noise 采样 `(x, y, t*0.03)`，只取低频。尘埃点用 `hash(i)` 初始化，随 t 线性漂移。
- **体积光**：一张加色混合的竖直面片，沿光束方向渐隐；亮度上限设为字亮度的 0.8。
- **字**：DOM 或 SDF 文本放在最上层，`depthTest: false`，但仍按透视放在空间里；中文副行放在英文下方 0.9 em 处。

## 自查重点

- 尺度：每个揭示镜头里，参照物高度 ÷ 主形体高度 ≤ 1/15。
- 雾：在同一镜里取近、中、远三层 crop，远层与雾色的色差 ≤ 15%。
- 字：同屏只有一行，字号不低于 44 px；光束和 bloom 压在字上的地方，亮度不超过字本身。
- 节奏：做 02 竖屏短片时，任何 3 s 窗口里都要有一个 read 或明显的镜头运动；看 1 fps 联系表，每 4 s 有没有新 read。
- braam 不超过 2 次，每次前面都有低音屏息。

## 相关资源

- 本仓库的介绍片：`showcase/04-intro-film/` 的 STYLE.md、`js/fx.js` 效果预设和 NOTES.md 里的取舍；`playbook/08-vfx-and-motion-sources.md` 的预设栈和"光效不能把字烧掉"底线。
- lemo-opuscar 里没有直接对应的风格。`dark-keynote` 的扫光揭示、`glass-product` 的"慢爆炸图、静默之后落拍"可以借用（`references/repos/lemo-opuscar/styles/<slug>/STYLE.md`，LemoLab，CC BY 4.0）。
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 里的 Shadow Cut（从黑暗中浮现、慢推）。
- `video-types/03-product-promo.md`、`cases/explainer-interstellar-blackhole.md`。
