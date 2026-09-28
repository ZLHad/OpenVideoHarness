# Taste checklist（给 agent 自评用）

每个项目都会复制一份这个文件。每渲染完一个场景就对照检查一遍：任何一项的答案是"是"，就返工对应片段，改完重新渲染再看。类型文档里的"自查重点"是在本清单基础上追加的检查项。

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
5. 同屏超过 8 个英文词，或停留不到 2.5s？中文每行超过 16 字，或超过 9 字/秒？
6. 字号低于下限（1080 宽主标题 84px / 辅助 44px；竖屏字幕 65px）？
7. 用了不止一个无衬线族？用斜体做强调？每个词都在强调？
8. 有写着剧情的牌子、标签、说明文字，而本可以用画面演出来？

**色彩**
9. 饱和的强调色超过一个？颜色没有语义？
10. 出现了并非刻意的紫青渐变、玻璃拟态、渐变字、霓虹？纯黑纯白？黄光叠蓝底变成灰绿？

**运动**（看切点 strip）
11. 前 25% 把所有内容倒上屏，然后画面冻结？
12. 默认用 bounce/elastic，卡片呼吸循环，或者匀速 lerp？
13. 所有元素同一个缓动、同一个时长、同一方向、同时入场？两只手臂或一群角色完全同步？
14. 切点两侧运动方向相反、一侧从静止开始，或者用了 crossfade？
15. 表情或状态在两帧之间硬切，没有预备和过渡？
16. 反应比原因晚了几帧或同时发生？高潮前没有 0.3–0.75s 的停顿？

**节奏**
17. 某个 read 少于 12 帧（0.5s）就被下一件事盖掉？两个重要 reads 重叠？
18. 超过 3s（短视频）或 8s（讲解）什么都没发生？落点没对准节拍（±1 帧）？

**内容**
19. 有占位文字、编造的数字、不存在的 UI？第 1 秒看不出这是什么、为什么要看？
20. 把这一帧换到任何别的主题也照样成立（说明它是装饰，不是设计）？说不出这一镜看完观众多知道了什么？

## 结构化输出

每次自评按这个格式写进 `NOTES.md`，便于追踪：

```text
[scene 03 · 12.0–16.5s] sheet: out/check/s03.jpg
- #11 FAIL: all 6 cards on screen by 12.4s, then static until 16.5s → stagger reveals across 12.2–14.0s, keep one moving element after
- #17 FAIL: "loss drops" read gets 7 frames → extend to 0.8s, delay the next event
- others PASS
```
