# STYLE

<!-- 一页纸的设计系统。subagent 并行时，这份文件和 STORYBOARD 一起作为契约。数值默认取 playbook/03-motion-design.md，类型文档有要求时以类型文档为准。 -->

## Canvas
- Size {W}x{H}, fps {fps}; safe box x {..–..}, y {..–..}; caption band y {..–..} (keep faces/key action above it)
- Grid (optional, Code2Video style): animation area {x0,y0,x1,y1} divided 6×6, anchors A1–F6; place objects only via grid helpers; labels within 1 cell of their object

## Palette
| token | hex | 用途 |
|---|---|---|
| bg | | |
| fg | | |
| accent | | 唯一的强调色 |
| muted | | 次要元素、基线 |
| {entity colors} | | 讲解类：一个概念一个颜色，全片不变 |

- Color arc（按幕）：{act 1 冷白 = 未知、安静 → act 2 琥珀 = 系统在运转 → act 3 红 = 高潮、警报}。每一幕写出主色调和它的含义，与 STORYBOARD 的 World 一行一致；换幕时强调色可以变，但同一时刻仍只有一个饱和强调色

## Type
- Display: {font}, weights {..}; Body/caption: {font}; Mono: {font}
- Sizes: title {..}px, body {..}px, caption {..}px; tracking {..}em
- Font files: {assets/fonts/… or system}

## Motion tokens
| token | value |
|---|---|
| enter | easeOutExpo cubic-bezier(0.16,1,0.3,1), 0.5–0.8s |
| exit | ease-in, ~75% of enter |
| move / camera | easeInOutCubic, 1.5–3s |
| stagger | {40 / 80 / 150}ms per item, total <=0.5s |
| hold before climax | 0.3–0.75s |
| register exceptions | {e.g. overshoot allowed only for character reactions} |

## Transitions (pick 2–3, reuse)
- {e.g. brush wipe at chapter breaks}
- {e.g. match cut on shape}
- Dominant direction: {left / up / push-in}

## Banned
- {purple-cyan gradients, glassmorphism, bounce by default, crossfades, text signs repeating the narration, pure black/white, …}
