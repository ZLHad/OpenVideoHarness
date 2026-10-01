# BRIEF

<!-- 关卡 1：用户已授权本次 showcase 跳过确认（"skip approval gates"），文件仍照写，作为自查依据。 -->

> 2026-10-01：下面的画面按静音片做完、交付。之后才给它补了中文配音（念的就是字幕）、轻配乐和音效，时间对齐已经定好的画面（README › Soundtrack）；这里的时长和字幕一处没改。

## Spec
- Output: 1080x1920, 30 fps, exactly 24.8s (744 frames)
- Engine: HyperFrames 0.8.82 (HTML + GSAP), single monolithic `index.html`
- Platform / audience: 竖屏知识短视频（抖音 / 视频号 / 小红书 / Shorts），好奇的普通观众；**静音观看**——没有旁白、没有音乐，所有信息靠烧录中文字幕和画面
- Language: zh-CN, narration: 画面阶段没有（字幕即旁白）；2026-10-01 补了配音，念的就是这些字幕
- Deliverables: final.mp4, 3:4 cover frame（hook 文字），contact sheet，preview GIF（README 用）

## Content
- Spine (one line): 低轨卫星飞得极快，信号频率在一次过顶里从"偏高"滑到"偏低"（多普勒频移），但轨道是已知的，所以系统能提前算好、反向补偿。
- Recurring motif: 一条"信号波"——开场它被挤紧又拉松（"变调"），中段它连接卫星和你、随靠近/远离变密变疏，结尾它的频移曲线被补偿成一条平线（不再变调）。
- What the viewer should know/feel at the end: "卫星变调"不是故障，是速度造成的物理现象：靠近偏高、头顶归零、远离偏低；2 GHz 最多约 ±50 kHz，20 GHz 大 10 倍；工程上用已知轨道提前补偿。
- Source material: 用户 brief（见下）+ 自己的轨道力学计算（NOTES.md 记录公式、参数和结果）。

## Style
- Refs (2–3 named works): Kurzgesagt（扁平矢量、深色底、一个暖色强调）；Fireship（快、干、数字说话）；回形针 PaperClip（高信息密度的示意图）
- Explicitly NOT: 紫青/蓝紫科技渐变、粒子背景、光球、玻璃拟态、图库图标、品牌 logo、"关注我"卡片、全程 Hormozi 字幕
- Palette: bg #0E1726, fg #F5EFE6, ONE accent #FF8A3D（暖橙）；无纯黑纯白
- Type: Noto Sans SC（OFL，Google Fonts）500 + 800 两个字重；层级只靠字重和字号

## Motion defaults (override per type doc)
Entrances easeOutExpo cubic-bezier(0.16,1,0.3,1) / power3.out; exits ease-in at ~75% of entry; entries <=0.8s; total stagger <=0.5s. No bounce/elastic, no idle breathing loops, no crossfades between scenes; transitions grow out of content; 0.3–0.75s stillness before each climax.

## Text rules
<= 16 CJK chars per line on screen; caption block visible >= 2.0s（hook 副标题 c1 例外 1.9s，NOTES 记录）；字幕 72px/800，hook 140px/800，标签 >= 44px；everything inside safe box x 90–900, y 330–1520.

## Determinism
Every frame is a pure function of t. No Math.random / Date.now / CSS transitions; seed all noise; no state carried between frames. 物理画面（卫星位置、信号波、频移曲线）由一个 `drawStage(t)` 纯函数绘制，挂在 GSAP 主时间线的一个 proxy tween 的 onUpdate 上。

## Process
1. STORYBOARD.md: per shot = time range, caption, visual, focal element, the reads (each with start–end), transition out. （本次授权跳过确认）
2. Audio first: **N/A — 画面按静音片做**（配音、配乐是成片之后补的，对齐画面）。时间由字幕阅读量决定：每条字幕按 ≤ 6 字/秒、≥ 2.0s 留时（比 9 字/秒上限宽松，因为观众还要看图）。
3. Build scene by scene; after each scene render stills + a contact sheet + strips for key motions; critique against TASTE_CHECKLIST.md and log in NOTES.md; fix before moving on.
4. Uncertain facts and creative decisions go in NOTES.md, never invented into the video.
5. Deliver: MP4 path, contact sheet of the whole piece, NOTES.md, the 2–3 spots you're least happy with.

## Acceptance
- [ ] 静音、第 1 秒就能读到"卫星信号会变调"
- [ ] 3 秒内出现"多普勒频移"（看完能学到什么）
- [ ] 每个数字都和 NOTES.md 的计算一致：7.6 km/s、500–550 km、2 GHz 接近 ±50 kHz、20 GHz 大 10 倍（约 ±500 kHz）、一次过顶几分钟
- [ ] 频移曲线是用真实几何算出来的 S 形（正 → 0 → 负），不是手画的
- [ ] 所有文字在安全框内；字幕单行 ≤ 16 字
- [ ] 24.8s ±1 帧，1080x1920，30 fps，画面渲染无音轨（配音、配乐和音效后来合进成片）
- [ ] 画面上任何 3 秒窗口内都有变化

## TYPE
+ TYPE: vertical knowledge short. 1080x1920 30fps 24.8s, **silent** (no narration, no music) + burned-in zh-CN captions carry everything (picture phase; narration, music and SFX were added on 2026-10-01). Platform: 抖音 / 视频号 / 小红书 / Shorts.
Style: "Kurzgesagt meets Fireship": flat vector shapes, one accent, dry humor. NOT: blue-purple tech gradients, particle backgrounds, stock icons.
0–1s: the counterintuitive claim/number as a full-bleed visual (no logo, no greeting). By 3s: what the viewer will learn.
A new visual payoff every 3–5s; one idea per shot; cut on caption phrase boundaries.
Captions: one line, <=16 CJK chars, 72–90px, weight 800, #F5EFE6 with 3px dark stroke; accent on 1–2 key words max. Hook text 140px.
Safe box x 90–900, y 330–1520 (platform UI zones stay clear). End on the payoff visual, not a subscribe card.
Also export a 3:4 cover frame with the hook text.

<!-- from 02-knowledge-short.md（原块写的是 "zh-CN narration" 和 30–60s；本片按用户要求改为静音、20–25s） -->
