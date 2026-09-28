# STYLE

<!-- 一页纸的设计系统。数值默认取 playbook/03-motion-design.md，类型文档 02-knowledge-short 优先。 -->

## Canvas
- Size 1080x1920, fps 30; safe box x 90–900, y 330–1520（水平中心 x=495，不是 540——右侧留给平台按钮栏）
- Caption band y 1375–1485（在安全框底 1520 之上）；全片固定在这一带（24.8s 不到"每 30 秒打破一次"的门槛，hook 大字本身是一次变化）
- Stage 布局（S3–S5，一个固定舞台）：
  - 天穹区 y 430–930：地面线 y=900，"你"（地面天线）在 (495, 900)，卫星沿半径 380 的天穹弧从左 10° 仰角升起、过顶、在右 10° 落下
  - 图表区 y 1000–1300：x 150–860，零线 y=1150，满幅 ±110px
- S6–S7 图表放大到 y 560–1260（同一张图，重新布局，不缩放文字）

## Palette
| token | hex | 用途 |
|---|---|---|
| bg | #0E1726 | 全片底色（深墨蓝，不是纯黑） |
| panel | #152238 | 图表底板、地球夜面 |
| earth | #24507A | 地球 / 地面（去饱和的中蓝，平涂） |
| earth-rim | #2F6394 | 地球边缘一圈亮一点的大气带（平涂，不渐变） |
| fg | #F5EFE6 | 字幕、主体线条、卫星本体 |
| muted | #7F8FA6 | 标签、坐标轴、次要文字 |
| grid | #26364F | 网格线、轨道虚线 |
| stroke | #0A111C | 字幕 3px 描边 |
| accent | #FF8A3D | **唯一的强调色**：信号波、频移曲线、字幕关键词（每条最多 1–2 个） |

语义：accent = "信号 / 频率"。补偿曲线用 fg 虚线（不是第二种强调色）。

## Type
- Display / caption / label: Noto Sans SC（OFL，经 Google Fonts `<link>` 加载，HyperFrames 渲染时本地化），字重只用 500 和 800
- Sizes: hook 140px/800（tracking -0.02em），stat 120px/800 tabular-nums，caption 72px/800（fg + 3px stroke，paint-order: stroke），label 44–48px/500 muted
- 公式用同一字体的拉丁字形，不另加 mono

## Motion tokens
| token | value |
|---|---|
| enter | power3.out（≈easeOutExpo），0.5–0.7s |
| exit | power2.in，约 0.4s（入场的 ~75%） |
| move / camera | power2.inOut / sine.inOut，1–2s |
| stagger | 字幕两行 80ms；刻度标签 60ms；总 ≤ 0.5s |
| hold before climax | 0.4–0.6s（Ka 曲线出现前、补偿"归零"前） |
| physics driver | 一个 `ease: "none"` 的 proxy tween，onUpdate → `drawStage(t)`；卫星位置、信号波、曲线全部由 t 算出 |
| register exceptions | 无 overshoot、无 bounce |

## Transitions (pick 2–3, reuse)
- push-slide LEFT（主流向：向左 = 下一拍）：S1→S2
- zoom-through（推近 = 深入同一件事）：S2→S3，从地球轨道推近到"你头顶的天空"
- 同舞台重排（no cut）：S3→S7 全在一个舞台上，靠元素位移 / 重排衔接
- Dominant direction: left；向上只用在结尾结论

## Banned
- 紫青渐变、玻璃拟态、光球、粒子/星空背景、霓虹描边、渐变字
- 纯 #000 / #fff；第二个饱和色
- bounce / elastic；呼吸循环；场景间 crossfade
- 图库图标、品牌 logo（卫星和天线都是自己画的几何形）
- 斜体强调；每个词都上色
- 任何 Math.random / Date.now / CSS transition / @keyframes
