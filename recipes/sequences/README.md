# 全片骨架：节奏语法

单张配方管一个镜头怎么动，骨架管整支片子的节奏：能量怎么起伏，每一镜先留多少静止，镜头之间用哪种接缝，哪些手法全片只能用几次。镜头一个个都做对了，片子仍然可能是平的、挤的、吵的，问题几乎都出在这一层。

它和 `playbook/09-narrative.md` 分工：playbook/09 定片子的形状（讲什么、在哪里转、好奇缺口怎么走），这里把形状落成帧数、停顿和接缝。开头的钩子怎么写见 `playbook/10-hooks-and-packaging.md`。

本目录有三条骨架，是填空用的起点，不是命令；有意偏离的地方在 `NOTES.md` 写一句为什么。

| 骨架 | 长度 | 适合 | 一句话 |
|---|---|---|---|
| [launch-15s](launch-15s.md) | 15 s | 发布 teaser、社交平台的短宣传 | 主角一弧、一个功能冲刺、屏息一秒、最响的一击砸出字标 |
| [explainer-30s](explainer-30s.md) | 30 s | 有旁白的知识短片、产品讲解 | 钩子、三步、兑现、回到开头；旁白定时长，接缝跟着句子走 |
| [product-film-60s](product-film-60s.md) | 60 s | 多功能 web / 桌面产品的发布片 | 低开品牌、单主角立传、功能和字卡交替爬升、发布会收场 |

## 能量的六档

配方的 `energy` 字段、骨架的能量弧和 `playbook/09-narrative.md` 节拍表里的"能量"用同一把尺子（0–5）：

| 档 | 画面上是什么 | 例子 |
|---|---|---|
| 0 | 屏息：黑场或几乎全静，声音只剩一层底（不是数字静音） | 黑场蓄爆的 12 帧、"转"之前的静一拍 |
| 1 | 近乎静止：只有一件事在慢慢发生，或者完全停住 | 字卡停留、落款、满板静止 |
| 2 | 慢而稳：一个主体、一种运动，观众在读 | 虚焦接力、文档写入 |
| 3 | 中：一个主角完成一条完整的动作弧 | 聚光单主角、交互演示 |
| 4 | 高：一群东西在动，或者镜头在快速移动 | 发牌入网格、甩镜、穿暗场 |
| 5 | 峰值：全片最强的冲击，整画面参与 | 递进硬切串、发布会合影 |

## 五条规则

**1. 先画能量弧，再选镜头。** 默认的形状是：低开（品牌或钩子）→ 中段立一个主角 → 功能段高低交替地往上爬 → 收场是全片最高点。两端不能省：开场要有一个完整的静止时刻让观众记住名字，收场要是真正的峰值。连着两个高能镜头读作嘈杂，高低交替本身就是节奏。

**2. 每一镜先划走 hold，再排动作。** 不是排完动作再找空隙。这些是底线：

| 什么停住 | 至少停多久 | 出处 |
|---|---|---|
| 字标、要读的字 | max(1 s, 读时规则)；读时规则是 max(2.5 s, 汉字数 ÷ 4.5 + 其他字符数 ÷ 15 + 1.5 s)，旁白念的字跟旁白走 | shotcraft 判例 R1；本仓库 TASTE_CHECKLIST #5 |
| 一批元素入场之后 | 15 帧（0.5 s）整体静止 | 判例 R2 |
| 开场主角的动作弧 | 3 s（产品片） | 判例 R3 |
| 重击之后（切串、连闪、黑场蓄爆） | 平常的两倍：35–60 帧 | shotcraft `beat-cut-moves` |
| 高潮之前 | 0.3–0.75 s 的"戏剧逗号" | playbook/03 §2 |

**3. 接缝先看叙事关系，再按能量落差选一式，一个接缝只用一式。** A 和 B 是什么关系（同一样东西换尺度、动作延续、段落边界、反转）决定用哪一类，见 playbook/09 §6；同一类里，按下表的能量落差挑。接缝占用的帧从相邻两镜的预算里划；一支片子只用 2–3 种接缝，反复用（playbook/03 §6）；开头和结尾也要有处置，不留裸切。

| 两侧 | 首选 | 备选 | 为什么 |
|---|---|---|---|
| 高 → 高，换空间 | [dark-tunnel](../seam/dark-tunnel.md)（暗色调片子） | [whip-pan](../seam/whip-pan.md)（亮色调、要快） | 同一条镜头一路飞过去，动量不断 |
| 中 → 中，页面到页面 | [flash-cut](../seam/flash-cut.md)；平面、排版为主的片子用 [cut-the-curve](../seam/cut-the-curve.md) | whip-pan | 最不抢戏，可以当全片的默认接缝 |
| 大字到大字（同一场景里换一句） | [zoom-through](../seam/zoom-through.md) 推进款 | cut-the-curve 的逐词版 | 沿纵深走，"更深一层"；拉回款留给兑现和片尾 |
| 同一空间里换地方看 | [focus-handoff](../seam/focus-handoff.md) | flash-cut | 镜头不动，焦点就是剪辑点 |
| 总览 → 某一项的详情 | [portal-wipe](../seam/portal-wipe.md) | flash-cut 加推近 | 接缝本身在说"点开它" |
| 一镜到底里换章节 | [gate-as-door](../seam/gate-as-door.md) | 甩镜变速（[one-take-world-travel](../camera/one-take-world-travel.md)） | 穿过一扇形状就是下一章的门 |
| 快剪里换"世界"（媒介、配色全变） | 落拍的硬切 + [flash-stitch](../seam/flash-stitch.md) | 直接硬切 | 1 帧高反差把两种媒介焊在同一个节拍上 |
| 任意 → 呼吸位、换章节 | [black-card](../seam/black-card.md)，或 flash-cut 接一张 [breath-title-card](../type/breath-title-card.md) | 直接硬切到字卡 | 能量往下落，给一句话的时间 |
| 往上冲进高潮 | 落在最强拍上的硬切 | 让高潮镜头自己开场（例如 [accelerando-cuts](../rhythm/accelerando-cuts.md) 的建立段） | 高潮不需要过渡，需要一记准的 |

**4. 限额：克制写成数字。** 有了上限，强的地方才显得强。

- 作用于整个画面或相机层的冲击（整画面缩放泵、震屏、闪帧、负片帧），全片不超过 3 处，钉在配乐最强的几个 hit 上，相邻两处至少隔 16 拍（shotcraft 判例 R4）；其余拍点只动主角元素。一次手法算一处，不按它内部的子事件计。
- 节拍泵一次最多连打 4 拍，全片最多 1 次；频闪全片最多 1 次，并且守住全屏闪白每秒不超过 3 次（CLAUDE.md 底线）。
- 一种手法全片只当一次主角（判例 P4）；光效只给主角，只给一次（判例 Q4）。
- 黑场字卡一支 30 s 的片子最多 2 次；呼吸字卡全片 2–4 张。
- 配方自己的 `max_per_film` 和 `conflicts` 照样生效。

**5. 有配乐时，镜头边界锚在小节线上。** 先出音乐的结构表（`bin/vh music` 的 sections，或 `bin/vh beats` 分析外来音乐），最强的 2–3 个 hit 留给整画面冲击，breakdown 段放呼吸位。鼓点命中表是候选池，不是触发器：kick 几乎每拍都有，逐拍打画面就是抖动（判例 R4）。旁白和音乐同时有时，旁白的关键句落在 drop 或小节头（`bin/vh tts … --beats`）。

## 怎么填一条骨架

1. **列功能清单**，数出功能镜头的个数 N。每个核心功能都要有镜头，漏了就是返工（判例 P4）。
2. **按段位分帧**：先扣掉开场、主角、收场和呼吸位的固定预算，剩下的给功能段均分。
3. **每一镜先划 hold**（规则 2），剩下的帧才给动作。放不下就加长镜头或删掉一条 read，不要硬挤（playbook/01）。
4. **排能量**：功能段高低交替；信息最密的一镜（文档、报告）放在收场前倒数第 2–3 位。
5. **按位置挑配方**：`bin/vh recipes list --role feature --energy 4 --have ui-page,ui-element`，选中的读全文。
6. **逐个接缝选一式**（规则 3），写进 STORYBOARD 的"转场出"列。
7. **对一遍限额**（规则 4），再给关卡 ② 出分镜预览图；节奏要紧的片子做 animatic。

## 来源

五条规则和 60 s 骨架的段位改写自 video-shotcraft（Vincent Wei，Apache-2.0）的全片骨架 `references/sequences/promo-energy-arc.md`、转场卡 `shot-transitions` 和审美准则 R1–R4、P4、Q4；原骨架来自一支 36 s 模板片和两次独立复现，作者注明是"单例判例"。15 s 和 30 s 两条骨架是本仓库按同一套规则推出来的，还没有在成片里验证过。读时规则、闪白底线和接缝数量来自本仓库的 CLAUDE.md、TASTE_CHECKLIST 和 playbook/03。

**许可**：本文件修改自 [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) 在 commit `e2d8928` 时的 `references/sequences/promo-energy-arc.md`、`references/shots/transition/shot-transitions.md`、`references/aesthetic-rules.md`（Copyright 2026 Wei Yihao，Apache-2.0），改了什么见上一段。来自上游的部分仍按 Apache-2.0 授权，许可全文见 [`LICENSES/Apache-2.0-video-shotcraft.txt`](../LICENSES/Apache-2.0-video-shotcraft.txt)；本仓库的改动按仓库根目录的 MIT 许可。所有改编文件和上游出处的清单见 [`NOTICE.md`](../NOTICE.md)。
