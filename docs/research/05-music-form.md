# 05 · 配乐的篇章、主题和起伏：没人能听的音乐怎么量

*记录于 2026-10-01 · 状态：知识稿已并入 [`playbook/11-composition.md`](../../playbook/11-composition.md)（[#23](https://github.com/ZLHad/OpenVideoHarness/pull/23)），引擎缺口的实现已合并（[#24](https://github.com/ZLHad/OpenVideoHarness/pull/24)、[#25](https://github.com/ZLHad/OpenVideoHarness/pull/25)）；示范的完整谱面和度量脚本没有入库 · [English](en/05-music-form.md)*

> **现状（2026-10-01）**
>
> - **知识稿**：成了 [`playbook/11-composition.md`](../../playbook/11-composition.md)（[#23](https://github.com/ZLHad/OpenVideoHarness/pull/23)）。它的第 6 节给了用 ffmpeg `ebur128` 取响度曲线、按节拍表的段落求平均的一段代码，和用引擎的 `render()` 取各声部 stem、比旋律与伴奏电平的一段代码；第 7 节的两个示例就是这里的示范 1 和示范 3。示范 2（起承转合）和三首示范的完整谱面没有入库。
> - **复算**：#23 写它时用入库的引擎复算了这里的几个数，结果一致：介绍片配乐（LRA 8.5，各段平均响度的最大差 10.0 LU，最响一段在 28 %）、`--example`（7.6 / 6.2）、`--example zh`（7.0 / 6.7）、250 Hz 以下的能量占比（介绍片 50–91 %）、示范 1 第 20 小节约 44 个音头/s 对高潮约 16 个/s、介绍片节拍表里的 143 个 hit。
> - **引擎**：缺口的前四条加上弱起在 [#24](https://github.com/ZLHad/OpenVideoHarness/pull/24) 里实现了（动机块 [`tools/audio/motifs.py`](../../tools/audio/motifs.py)、`"index": "section"`、`dyn` / `cresc` / `dim` / `vel_ramp`、段落的 `stop`、负拍位的弱起）；它的描述里有用动机改写的示范 1：音频逐字节不变，音符条目从 137 条减到 54 条。变速（tempo map）和片头弱起小节没有做，#24 的描述里有设计记录。`bin/vh music --roll` 在 [#25](https://github.com/ZLHad/OpenVideoHarness/pull/25)（[`tools/audio/roll.py`](../../tools/audio/roll.py)）。
> - **脚本**：度量脚本 `arc.py`、`stems.py`、`dump_events.py` 没有入库，下面的"命令"是它们当时的用法。

## 问题

现有配乐的响度是一块平台，缺少可哼的主题，也缺少详略和起伏（见"发现"里的表）。缺的到底是什么？没人能听的时候，怎样量"有没有篇章、有没有主题、有没有起伏"？

## 做法

- **度量**（只读的小脚本，没有入库；入库的做法见"现状"）：
  - `arc.py`：用 ffmpeg 的 `ebur128` 取 short-term（3 s）和 momentary（0.4 s）响度，按节拍表里的段落统计各段平均、最小、最大和 LRA；`section_contrast` = 各段平均响度的最大值减最小值。
  - `dump_events.py --density`：用引擎自己的解析器，不渲染就打印每小节的音头数和发声的声部数。
  - `stems.py`：各声部 stem 的电平，主旋律比最响的伴奏高多少。再加上 `bin/vh qa`（掉音、抽吸、click、cue check）。
- **对照**：三个基线，即介绍片现有的配乐（81.3 s，节拍表里 143 个 hit）、`bin/vh music --example`（EDM 起步谱）和 `--example zh`；三首只用现有引擎写的示范：**示范 1** 产品片弧线（120 BPM，58.5 s，35 个声部）、**示范 2** 起承转合（72 BPM，44.2 s，19 个声部）、**示范 3** 讲解片的旁白底（100 BPM，39.7 s，15 个声部）。
- **命令**（上面几个脚本当时的用法，脚本没有入库）：

```bash
uv run --with numpy --with scipy --with matplotlib python arc.py music.wav --beats music.beats.json --score score.json --engine <repo>/tools/audio --out arc.png --json arc.json
uv run --with numpy --with scipy python dump_events.py score.json <repo>/tools/audio --density
```

来源：作曲知识稿（其中的量法已写进 [`playbook/11-composition.md`](../../playbook/11-composition.md) 第 6 节）、三个度量脚本的说明和各示范的响度 JSON；脚本和 JSON 是作者本地的文件，没有入库。

## 发现

**1. 现有配乐在响度上是一块平台。** 介绍片的配乐 16 s 以后，到 76 s 之间的八段平均响度全在 −11.5 到 −14.5 LUFS；最响的 braam 只比第二响的段高 1.8 LU。三首示范有一个低谷和一个唯一的高点。

| 曲子 | LRA (LU) | 各段平均响度的最大差 (LU) | 最响一段比第二响高 (LU) | 距最响不到 2 LU 的段 | 最响一段的位置（占文件时长） |
|---|---|---|---|---|---|
| 介绍片现有配乐 | 8.5 | 10.0 | 1.8 | 3 / 11 | 28 % |
| `--example`（EDM） | 7.6 | 6.2 | 2.2 | 1 / 4 | 57 % |
| `--example zh` | 7.0 | 6.7 | 1.6 | 2 / 5 | 67 % |
| 示范 1 产品片弧线 | 11.2 | 11.5 | 4.4 | 1 / 8 | 77 % |
| 示范 2 起承转合 | 10.1 | 7.6 | 3.8 | 1 / 4 | 57 % |
| 示范 3 旁白底 | 9.5 | 7.3 | 5.3 | 1 / 5 | 70 % |

![介绍片现有配乐与三首示范的 short-term 响度曲线和各段平均](figs/05-loudness-arcs.png)

*图 1 · short-term（3 s）响度（蓝）和各段平均（橙）：第一块是介绍片现有的配乐，爬升后一直是平台；其余三块是示范 1、2、3，有谷有峰。*

单看指标，差别没有想象的大：LRA 只差 3 LU 左右，介绍片的"各段最大差"10.0 LU 甚至超过示范 2 和 3，因为它有一个很轻的开头（−21.5 LUFS）。真正区分它们的是形状：最响一段是否唯一、有几段挨着最响值。

**2. 对位点太密，没有一个被推到焦点上。** 介绍片的节拍表在 81.3 s 里记了 143 个 hit（123 个是起音，20 个是 swell 的峰），平均每秒 1.8 个；三首示范的节拍表只有 7、8、17 个。示范的做法是每章最多一个大打点，其余交给音效。

**3. 音区从头到尾没有"变轻"过。** 按 250 Hz 分，介绍片从 8 s 起每一段都有 50–91 % 的能量在 250 Hz 以下（sub、drone、大鼓）；示范 1 各段是：chaos 84 %、nova 92 %、question 21 %、theme 23 % 和 15 %、develop 33 %、climax 29 %、coda 12 %。（这些占比是对每一段的 WAV 做 FFT 重算的。）

**4. 密度的峰值可以在高潮之前。** 示范 1 的第 20 小节（39 s）每秒有 44.0 个音头（加花、滚奏、音阶），高潮段（第 21–24 小节）只有 15.5–17.0 个，发声的声部是 10–12 个，前者是 9 个。高潮更响（−10.1 LUFS，全片最高）靠的是长音、全音区和更多的声部，不是更密。

![示范 1 的响度曲线、段落与动机入口，下方是每秒音头数和发声声部数](figs/05-product-arc.png)

*图 2 · 示范 1（120 BPM）：上，响度曲线和谱子自己标的记号（动机入口、nova 的一击、最高音）；下，灰柱是每秒音头数，折线是同时发声的声部数。*

**5. 一个动机的生命周期（示范 1）。**

| 章 · 时间 | 动机的样子 |
|---|---|
| chaos · 0–8 s | 1-5-4-3 紧缩成十六分音符，D 弗里吉亚，藏在低音弦乐的固定音型里，逐小节渐强 |
| question · 10–15 s | 只说半句：D A G，停在 E，底下是 Asus4，不解决；一台毡锤钢琴，全片最轻（−21.6 LUFS） |
| theme · 15–31 s | 完整的 8 小节乐段：前句停在属和弦，后句到最高音 F#5，落回主和弦 |
| develop · 31–41 s | 动机头在 I、ii、iii 上逐级模进，最后只剩"根音 → 五音"的碎片，和声节奏加倍 |
| climax · 41–49 s | 后句全奏，铜管加高八度弦乐 |
| coda · 49–56 s | 放慢一倍再现，把 question 悬着的 E 解决到 F# |

**6. 合成层面踩到的坑。**
- 钢琴和弦乐在同一音高上叠旋律，相位互相抵消，`bin/vh qa` 在 27.4 s 报了 4.6 dB 的抽吸；把钢琴改成高八度就没了。
- 音符型的管乐（如 `dizi`）每个音自带起音和收尾，音与音之间有缝，qa 当成抽吸；让音符重叠约 0.15 拍，或改用连奏型的 `flute`、`xiao`。
- 近似正弦的独奏加颤音，再送很多混响，干声和湿声会周期性抵消，出现约 5 Hz 的电平起伏；`send` 从 0.35 降到 0.18 就不报了。
- 鼓太响会吃掉峰值余量（整首按峰值归一）：第一版高潮段里定音鼓只比铜管主旋律低 0.7 dB，调低鼓之后，主旋律比最响的伴奏高 7 dB，高潮段整体还响了 0.5 LU。
- `loop` 和按小节的 `pattern` 列表数的是这个声部自己的小节，不是这一段的小节，不报错，只是听起来不对；示范 3 的底鼓只好手工轮换列表。片头 t = 0 的 cue 会被检测得晚约 48 ms。

来源：各曲的响度 JSON（段平均由其中的 short-term 均值算出；最响一段的位置取该段中点占全片的比例，全片取节拍表里的 `duration`，也就是文件时长，和 playbook/11 第 6 节的代码一样：引擎渲出的文件比最后一段的终点多约 2.5 s 尾音，介绍片是剪好的片子，没有尾音）；节拍表里的 hit 条目数（介绍片配乐的节拍表是 [`showcase/04-intro-film/audio/music.beats.json`](../../showcase/04-intro-film/audio/music.beats.json)：143 条，123 个起音、20 个 swell 峰；81.33 s，30 小节，11 段）；三首示范的谱面配合 `--density` 重跑的每小节音头数（第 4 点）；对应 WAV 的分段 FFT（第 3 点）；作曲知识稿里的动机表、鼓和抽吸的细节；引擎缺口分析的 §11。示范的数据是作者本地的文件，没有入库；[#23](https://github.com/ZLHad/OpenVideoHarness/pull/23) 用入库的引擎复算过一批，见"现状"。图 1、2 是实验里画图脚本的原图缩小。

## 因此改了什么

- **知识稿**（现在是 [`playbook/11-composition.md`](../../playbook/11-composition.md)，[#23](https://github.com/ZLHad/OpenVideoHarness/pull/23)）给出按时长选篇章数、起伏曲线和主题地图的做法，以及几个起步目标：有高潮的片子各段平均响度的最大差至少 8 LU，最响一段比第二响至少高 2 LU；主旋律比最响伴奏高 3 dB 以上；有旁白时配乐底要在人声中位电平的 12 dB 以内。这些是起步值，不是规定；后来写进了 playbook/11：前两条的量法和目标在第 6 节，旁白底的 12 dB 在第 5 节，写成 `bin/vh qa` 的掉音判据（0.1 s 窗口低于该段中位电平 12 dB）。
- **引擎缺口**（分析文档共 12 条，没有入库）：最值得做的四条是动机块、按段落计数的 `loop` 和列表、段内力度曲线、段落级 stopdown。示范 1 写了 35 个声部、137 行音符，光是主题的两句旋律就复制了五遍（82 行）。[#24](https://github.com/ZLHad/OpenVideoHarness/pull/24) 已实现动机调用和变形、`pattern_index: "section"`、`dyn` / `cresc` / `dim` / `vel_ramp`、段落的 `stop` 和负拍位的弱起；里面没有变速（tempo map）。
- **工具**：`bin/vh music --roll`（每个声部的钢琴卷帘加能量曲线）在 [#25](https://github.com/ZLHad/OpenVideoHarness/pull/25)。

来源：PR [#23](https://github.com/ZLHad/OpenVideoHarness/pull/23)、[#24](https://github.com/ZLHad/OpenVideoHarness/pull/24)、[#25](https://github.com/ZLHad/OpenVideoHarness/pull/25) 的描述（知识稿现在是 playbook/11；引擎缺口的实现和没做的部分在 #24 的描述里，`--roll` 在 #25）；引擎缺口分析本身（12 条）没有入库。

## 局限与没解决的

- **响度只是"张力"的一个代理。** 知识稿引用的张力模型（TenseMusic、Farbood）认为响度权重最大；原文没有读，不知道它们对合成乐器和 5 s 到 1 分钟的短片成不成立。
- **样本很小，也没人听过。** 三个基线、三首示范，起步目标是从这六条曲线里归纳的；示范 3 只配了 macOS `say` 的占位旁白，用来判断音乐让不让得开人声。所有判断来自表读数。
- **合成乐器近听仍然是合成的**（#13 的已知局限）。
- **和[笔记 01](01-mix-hierarchy.md) 的数字没有对齐。** 知识稿说有旁白时配乐底要在人声中位电平的 12 dB 以内（再低，`bin/vh qa` 会把停顿处判成掉音）；混音原型把 explainer 的 VMR 目标定在 13 LU（范围 11–18）。两者量的不完全是同一件事，也没有在同一部片子上对过。
- **指标是钝的**：LRA 和"各段最大差"会被一个很轻的开头抬高（介绍片就是），所以另外看了最响一段是否唯一。
- **命名容易混**：基线文件叫 `intro_v4_music`，但它是 `showcase/04-intro-film` 里那支 81.3 s 片子（修订计划文档里叫 v3）的配乐；playbook/11 里也叫"介绍片 v4 的配乐"，指的是同一份。

来源：作曲知识稿；介绍片配乐的节拍表（81.33 s，30 小节），即 [`showcase/04-intro-film/audio/music.beats.json`](../../showcase/04-intro-film/audio/music.beats.json)。
