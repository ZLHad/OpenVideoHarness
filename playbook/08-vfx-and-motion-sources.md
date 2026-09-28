# 08 特效与动画：去哪里找、怎么接进来

特效和动画都是画面代码的一部分，同样必须是 t 的纯函数。本篇只讲**来源和接法**。审美规则见 `03-motion-design.md`；什么时候该用、用多少，看类型文档。

## 原则

1. **特效服务于内容**。每个特效都要能说出一句"因为这支片子（产品、概念）有 X，所以用 Y"（借鉴归藏的做法）。说不出来的，就是装饰。
2. **全片一套特效语汇**：2–3 种转场、1 种主背景手法，反复使用，不要每个镜头换一种。
3. **声画同源**：特效的触发点从 `music.beats.json` 的 `beats`、`downbeats`、`hits`，或者 `timeline.json` 的句子边界读取，不要手填时间。
4. **随机要可复现**：粒子、噪声、抖动全部用带种子的 hash。着色器里只用 `uTime = t`，不用系统时钟。

## 按引擎找现成的

| 需要什么 | HyperFrames（HTML + GSAP） | p5 / ClaudeAnimationBase | Manim | 通用 |
|---|---|---|---|---|
| 转场 | `npx hyperframes add <block>` 注册表里有着色器转场（例如 `flash-through-white`）；速度匹配的切法见 `references/repos/hyperframes/_upstream_claude/skills/cut-the-curve/` | `brushWipe`、`iris`、`irisShape`（见 ANIMATION_GUIDE） | `Transform`、`FadeTransform`、摄像机移动 | 跟着动作切、形状匹配切 |
| 背景和氛围 | Three.js 或 canvas 层；`hyperframes-creative/references/audio-reactive.md` | 水彩 fill、纸纹、`glow()` | `NumberPlane`、渐变背景 | 颗粒、暗角（成片后处理，见下） |
| 粒子、汇聚、流线场 | canvas 或 Three.js 自己写，用 `hash(i)` 定初始状态 | `hash` + `jit` | `VMobject` 点阵 | 思路参考 guizang 的 `assets/fx-lab/`（AGPL，只看思路不复用代码） |
| 文字动效 | 逐词 stagger、`steps()` 打字、`clip-path` 揭示（数值见 03 篇） | `letter()`、`sfx()` | `Write`、`TransformMatchingTex` | — |
| 数据图表动画 | `npx hyperframes add data-chart`；`hyperframes-creative/references/data-in-motion.md` | — | `Axes`、`BarChart` | `references/repos/data-animation-skills/` |
| 角色动画 | — | Clawd 的 31 种情绪、转身、舞蹈（ANIMATION_GUIDE） | — | 生成视频打底 + 转描（`05-hybrid-genvideo.md`） |
| 3D、着色器 | Three.js 层 + postprocessing | — | `ThreeDScene` | `references/repos/awesome-opus5-5-videos/` 的 3d 类作品和 prompt |
| 光标、UI 演示 | `oversized-cursor` 技法（`_upstream_claude/skills/oversized-cursor/`） | — | — | 用真实 UI，不用占位 |

更多风格来源：
- `references/community-skills.md` §2 收录了 lemo-opuscar 的 39 种影片风格，每种都有风格 prompt 和纯代码样片；
- `references/repos/hyperframes/skills/hyperframes-creative/references/visual-styles.md` 是 8 种设计师风格预设。

## 一镜到底（3D 世界）的做法

来自介绍片（`projects/…-intro-film`，成片发布后会放进 showcase）：

- **世界而不是幻灯片**：所有章节都是同一个空间里的"地点"，换场靠摄像机穿过物体、沿轴飞行、拉远看到全貌，不靠剪切。
- **字是世界里的物体**：大字是空间里的平面，按"在画面上占多宽"反推尺寸和距离，保证读的那一刻够大；字的出现和摄像机的运动一起设计。
- **关卡、停顿就是摄像机的停顿**：音乐在这一拍静下来，摄像机也在这里停住（stop 关键帧），然后盖章、开门，继续前进。
- **真实素材放在世界里**：成片挂在空间里的屏幕上，联系表立成一面墙；每一帧都能追溯到真实来源。
- **一个节拍函数给画面和配乐共用**，比如 `bar(k, beat)`。90 BPM 在 30fps 下一拍正好 20 帧，所有细分都落在整帧上。

## 声画联动的接法

```js
// 引擎里读节拍表（music.beats.json）和字幕（captions.json），全部按 t 查表
const beat = beats.beats.findLast(b => b <= t);            // 最近一拍
const k = Math.exp(-(t - beat) / 0.12);                     // 每拍的衰减脉冲，用于缩放或亮度
const hit = beats.hits.find(h => Math.abs(h.t - t) < 1/30); // 冲击点所在帧 → 闪白、抖动
const cap = captions.find(c => c.start <= t && t < c.end);  // 当前字幕
```

音效同理：画面上发生动作的帧就是 `events.json` 里的 `t`。先定画面的时间，再生成音效轨，不要反过来去凑。

## 成片后处理（ffmpeg，可选）

本机的 ffmpeg 可能没有编译文字绘制功能，但这几种滤镜可以直接用：

```bash
ffmpeg -i in.mp4 -vf "noise=alls=6:allf=t,vignette=PI/5" -c:a copy out.mp4     # 轻颗粒 + 暗角
```

颗粒会让 GIF 体积暴涨，给 README 用的 GIF 要从无颗粒版本生成（见 `video-types/03-product-promo.md`）。
