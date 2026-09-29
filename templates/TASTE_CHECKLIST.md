# Taste checklist（给 agent 自评用）

每个项目都会复制一份这个文件。每渲染完一个场景就对照检查一遍：任何一项的答案是"是"，就返工对应片段，改完重新渲染再看。类型文档里的"自查重点"是在本清单基础上追加的检查项。20 条是硬门槛；整片 draft 另外要过文末的打分层。

## 怎么取图

各引擎的取帧命令见 `playbook/02-verification.md`。优先用引擎自带的 sheet、strip、crop；只有成片 mp4 时，用 ffmpeg：

```bash
# 整片总览：每秒 1 帧，拼成 6×5
ffmpeg -i out.mp4 -vf "fps=1,scale=480:-1,tile=6x5" -frames:v 1 check/sheet.png
# 某个切点前后 0.3s，按 0.1s 步进
ffmpeg -ss {cut-0.3} -i out.mp4 -t 0.6 -vf "fps=10,scale=320:-1,tile=6x1" -frames:v 1 check/seam_N.png
# 不看图的检查：黑场、冻结、静音
ffmpeg -i out.mp4 -vf "blackdetect=d=0.3,freezedetect=d=1.5" -af silencedetect=d=1.5 -f null - 2>&1 | grep -E "black_|freeze_|silence_"
```

另外对每个镜头取首、中、末三帧。

## 检查项

**构图**
1. 眯眼看（或缩小到 20%）认不出第一焦点？一个镜头里有多个焦点在抢？
2. 主视觉不到画面的 40%，或有大块死区？
3. 有东西出了安全框、进了竖屏 UI 遮挡区、压到字幕带？
4. 标签离对象超过一格，或元素之间有遮挡？

**文字**
5. 需要观众读完的文字：同屏超过 8 个英文词，或停留不到 2.5s？中文每行超过 16 字（竖屏 72px 时 11 字），或超过 9 字/秒？读的那段时间里，字还在 decode 乱码，或被运动模糊抹花？（真实 UI 截图里的文字、背景纹理文字只要求"看得出是什么"，不要求读完）
6. 字号低于下限（1080 宽主标题 84px / 辅助 44px；竖屏字幕 65px）？按最终成片里的实际大小量：镜头推近后以推近后为准，而且推近后字不能发虚（被放大的元素挂着 CSS `will-change` 时，浏览器会把小尺寸的位图直接放大）；Manim 等不以 px 定义字号的引擎，从 1080p 成片的 crop 上量像素。GIF 预览不在考核范围内。
7. 用了不止一个无衬线族？用斜体做强调？每个词都在强调？
8. 有写着剧情的牌子、标签、说明文字，而本可以用画面演出来？

**色彩**
9. 饱和的强调色超过一个？颜色没有语义？
10. 出现了并非刻意的紫青渐变、玻璃拟态、渐变字、霓虹？纯黑纯白（类型文档明确要求的除外，比如 3b1b 式讲解的纯黑背景）？黄光叠蓝底变成灰绿？bloom、扫光或镜头光斑把字烧成白斑（压在字上的光不能比字本身亮）？

**运动**（看切点 strip）
11. 前 25% 把所有内容倒上屏，然后画面冻结？
12. 默认用 bounce/elastic，卡片呼吸循环，或者匀速 lerp？（卡通、手绘类按 ANIMATION_GUIDE 执行：预备动作、overshoot、表情 take、踩拍的 idle 动作是必需的，不算失败；匀速 lerp 在任何类型里都算失败）
13. 所有元素同一个缓动、同一个时长、同一方向、同时入场？两只手臂或一群角色完全同步？
14. 切点两侧运动方向相反、一侧从静止开始，或者用了 crossfade？循环播放的交付物（GIF、网页背景、平台自动循环），末帧接回首帧时跳一下或停一下？
15. 表情或状态在两帧之间硬切，没有预备和过渡？
16. 反应比原因晚了几帧或同时发生？高潮前没有 0.3–0.75s 的停顿？

**节奏**
17. 某个 read 少于 12 帧（0.5s）就被下一件事盖掉？两个重要 reads 重叠？换字时新旧两句同屏（旧句还没退完，新句已经进来）？
18. 超过 3s（短视频）或 8s（讲解）什么都没发生？落点没对准节拍（±1 帧）？片中（首尾之外）出现数字静音或近乎静音？停拍时声音和镜头同时停死（观众会以为播放卡住了；#16 的停顿要像屏息：低音垫着、镜头慢漂）？

**内容**
19. 有占位文字、编造的数字、不存在的 UI？第 1 秒看不出这是什么、为什么要看？
20. 把这一帧换到任何别的主题也照样成立（说明它是装饰，不是设计；最常见的通用 AI 装饰是四角的小标签、取景框式的边角线、不带信息的 HUD 读数）？说不出这一镜看完观众多知道了什么？

## 结构化输出

每次自评按这个格式写进 `NOTES.md`，便于追踪：

```text
[scene 03 · 12.0–16.5s] sheet: out/check/s03.jpg
- #11 FAIL: all 6 cards on screen by 12.4s, then static until 16.5s → stagger reveals across 12.2–14.0s, keep one moving element after
- #17 FAIL: "loss drops" read gets 7 frames → extend to 0.8s, delay the next event
- others PASS
```

## 打分层：严苛的动效导演

20 条全 PASS 只说明片子没犯错，不说明它好看。本仓库的介绍片 v2 逐条过了清单，用户看完仍然说"不够炫酷"。打分层专门抓这种"正确但不带劲"的片子，在整片 draft 上做，PASS/FAIL 仍是硬门槛。

- **谁来打**：不是作者。开一个全新上下文的 reviewer，扮演严苛的动效导演：它只看帧，不看作者的自评和解释。人设和输入见 `playbook/02-verification.md` 第 5 层。
- **打什么**：七个维度，各 1–10 分。

  | 维度 | 问的是 | 主要证据 |
  |---|---|---|
  | hook | 前 2 s 有没有让人停下来的东西（运动、反差、问题）？ | 0–2 s 的逐帧 strip |
  | 手机可读 | 缩到手机大小，必读字还读得出、主体还认得出吗？ | 每格 360 px 宽的手机联系表 |
  | 运动质量 | 缓动、重量、跟随、切点衔接像不像专业动效？ | 关键动作和转场的 strip |
  | 变化 | 每 2–4 s 有没有新东西：新构图、新运动或新信息？ | 1 fps 联系表 |
  | 构图与完成度 | 焦点、留白、对齐、细节有没有打磨到位？ | 联系表 + crop |
  | 内容 / 品牌准确 | 事实、数字、产品界面、品牌色和字体是否照实？ | crop + NOTES.md 里的出处 |
  | 声画同步 | 重音、切点、事件是否落拍？停拍时声画是否一起屏息而不是一起停死？ | cue check 结果 + 带时间码的 strip |

- **过线**：每个维度都 ≥ 8 才算过，不看平均分。
- **至少 3 轮**：每轮 reviewer 只列最差的 3 个问题，每个都写时间点和一条可以直接执行的改法；作者只重渲受影响的时间段，改完开下一轮（换一个全新上下文）。第一轮就全部过线也要跑满，分数在不同 reviewer 手里稳住才算数。跑满 3 轮仍有维度低于 8，就把分数和剩下的问题带进关卡 ③，让人决定。
- **两层的关系**：任何一条 FAIL 没修，分数再高也不能交付；20 条全 PASS 但有维度低于 8，同样要返工。
- **来源**：社区做法，主要是 Movez 在 X 上的课程 *How to build motion design studio with Opus 5.5* 和 Eian 的中文指南（经社区调研转述）：让 agent 扮演严苛的导演而不是作者，按维度打分，多轮返工。七个维度、≥ 8 分和 3 轮都是那边的经验值，原文没能逐条核实。

每轮打分同样写进 `NOTES.md`：

```text
[score round 2 · draft5] fresh-context reviewer, harsh motion director · sheets: out/check/phone_*.png, out/check/sheet.png
hook 7 · phone 8 · motion 8 · variety 6 · polish 8 · accuracy 9 · sync 8  → below 8: hook, variety
- 0.0–2.0s  logo fades in over a static gradient, nothing stops the thumb → open with the t-axis light already moving, first read at 0.3s
- 18–26s    one slow push-in for 8s → whip at 21.3s on the downbeat, macro crop at 24s
- 41.5s     CTA under the bloom halo, burnt white at 360 px → move it below the halo, cap bloom under text
re-render: 0–3s, 17–27s, 40–43s
```
