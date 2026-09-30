# 11 作曲：篇章、主题与起伏

配乐听起来"套路"，多半不是音色的问题，是结构的问题。维护者 2026-10-01 听完现有配乐的意见是：太套路，缺旋律，缺详略起伏。这篇讲怎么从分镜出发，先定篇章，再定起伏曲线和主题的出场计划，最后落到 `score.json`。

- **什么时候读**：`studio` 档位的片子；MV；介绍片、发布片；45 s 以上、靠音乐撑起结构的片子；人要亲自定主题或 BGM 的时候。只是配一段旁白、铺一层底，看 `04-audio.md` 就够了。
- **前提**：`score.json` 的写法（`sections`、`parts`、乐器、音高记号）、帧对齐的速度、混音参数都在 `04-audio.md` 的"配乐"和"让声音有表情、有节奏"两节。这里只用现有引擎能渲染的写法；第 7 节的示例用当前引擎渲两次，字节相同，`bin/vh qa` 通过。
- **标记**：【综合】是本仓库在来源之上的归纳。括号里是来源的作者或出处，链接在文末。
- **和叙事的关系**：配乐的篇章就是 `09-narrative.md` 的节拍表分出来的章，换挡装置里的"配乐换配器或换调"也在这里落地。

先量一下现有的配乐（EBU R128 的 short-term 响度，量法见第 6 节）：

| 曲子 | LRA | 各段平均响度的最大差 | 形状 |
|---|---|---|---|
| 介绍片 v4 的配乐（`showcase/04`，81 s） | 8.5 LU | 10.0 LU | 16 s 以后的 8 段都在 −11.5 到 −14.5 LUFS 之间，是一块平台；最响的 braam 段只比其余高约 2 LU，而且落在全片 28% 处 |
| `bin/vh music --example`（EDM 起步谱） | 7.6 LU | 6.2 LU | intro、build、drop 是同一套 i–VI–III–VII 循环，旋律层是固定的四音型 |
| `bin/vh music --example zh` | 7.0 LU | 6.7 LU | 五段的旋律层都是固定音型 |
| 第 7 节的产品片示例（58.5 s） | 11.2 LU | 11.5 LU | 一个低谷（问题段），唯一的高点在全片 70–84% 处，主题一句比一句高 |

LRA 只差 3 LU，差别在形状：一块平台，对"先压后放、有谷有峰"。套路感的来源【综合】：

- **循环不发展**：`layers` 的 `lead` 每两小节弹同样四个音，`arp` 永远是十六分音符，`bass` 永远是八分音符；`figure: "melody"` 是按种子随机游走的占位旋律。Richards（2016）统计了 482 部奥斯卡提名配乐，1990 年代起"有前后两半的主题"少了约 20%，他把原因归到音序器：短片段方便复制粘贴，于是短小的动机循环取代了有问有答的主题。Magenta 早期的旋律模型也是因为缺少重复和长程结构，才专门加了 lookback 和 attention。
- **从头到尾一个密度**：所有声部每段都在，段落之间只改音量。
- **和弦转圈不落地**：流行乐的循环可以故意不回主和弦（Spicer 2017），片子的篇章却需要落点：每章结尾要有一个终止，或者一个明确的问号（停在属和弦上）。
- **处处打点**："打得越重，越被推到焦点上"（Art of Composing），每个动作都打，就没有一个在焦点上。v4 的节拍表里有 143 个 hit。
- **只用音量做起伏**：真正的轻重来自配器、音区、密度和节奏，不只是 `gain_db`。v4 从 8 s 起，每一章都有 50–91% 的能量在 250 Hz 以下，音区一直没"变轻"过；示例的这个比例随章节从 12% 变到 84%。

## 1. 从分镜到谱子：四步

**① 节拍表：先写叙事，再写音乐。** 从 STORYBOARD 抄出叙事节拍（`09-narrative.md` 的节拍表可以直接用），每行写功能、情绪、音乐要做的事和必须落拍的时间点。必须落拍的点要少：一章最多一个大的（揭晓、标题、drop），小动作交给音效。

| 时间 | 叙事功能 | 情绪 | 音乐要做的事 | 必须落点 |
|---|---|---|---|---|
| 0–8 s | 铺垫：工具太多、信息轰炸 | 压迫、混乱 | 低音区、密、不协和，动机藏在里面 | — |
| 8 s | 爆炸 | 冲击 | 全曲唯一的大打击 | 8.0 s |
| 10–15 s | "差距在哪？" | 悬置 | 几乎只剩一件乐器，动机只说半句 | 10.0 s |
| 15 s | 主角出现 | 豁然开朗 | 主题第一次完整出现 | 15.0 s |

**② 篇章：选一种曲式，把节拍分进段落。** 一个 `section` 就是一章。

| 曲式 | 结构 | 适合 |
|---|---|---|
| 弧线 | 铺垫、上升、高潮、回落 | 产品片、发布片、介绍片 |
| 三幕预告 + button | 铺垫 / 冲突加码 / 高潮，最后一个短句收住 | 预告、宣传短片 |
| ABA'（三段体） | 主题、对比段、主题变化再现 | 情绪片、故事短片 |
| 起承转合 | 起引出，承展开，转换调式、换音区或加密，合再现收束 | 中国题材、诗意短片 |
| 回旋（ABACA） | 同一个副歌在各章之间回来 | 较长的讲解片，每章一个"章节标志" |
| 旁白底（underscore） | 人声段稳住，停顿处回应，只有一处让音乐当主角 | 知识短视频、讲解 |

| 时长 | 章数 | 主题怎么用 |
|---|---|---|
| 5–15 s（样片、logo、sting） | 1 个手势：弱起 → 强拍上的落点 → 余音 | 2–4 个音的动机说一次，落在主和弦上；要循环播放的停在开放的和弦上 |
| 15–30 s | 2 章：A 加 button，或 AB | 动机出现两次，第二次换配器或升高音区 |
| 30–90 s | 3–5 章，一个低谷、一个高点 | 完整主题最多 2–3 次，中间是发展 |
| 2–3 min | 5–8 章：ABA'、回旋，或三幕加 button | 主题完整出现 2–3 次，每次换配器；章与章之间用副主题或发展段隔开；低谷不止一个 |

- 段落长度用小节数，对齐画面用 `meters`：画面节点落在两拍之间时，把前一小节改成 5/4 或 2/4，不改速度（iZotope 的建议是插一个 2/4 小节）。速度仍从 `04-audio.md` 的"帧对齐的速度"里选。
- 三幕预告的比例：Pryn 给的 2.5 分钟预告是第一幕约 30 s，第二幕约 60 s（前半交代、后半行动，用滴答声这类固定节奏加紧张），第三幕约 60 s（先推进，后顶点），最后约 5 s 的收尾，用第三幕的一句旋律做成完整的短句。30–60 s 的片子按比例缩。
- drop 只有一次，而且要晚：太早会平，太晚冲劲已经用完（Rareform）。stopdown（停一拍再回来）可以有几次，给一句台词或一个标题让位；本仓库不许数字静音，所以 stopdown 要留一层底（pad、drone、锣的余音或底噪）。

**③ 起伏曲线：每一章多响、多密、在哪个音区。** 每个 section 定四个量：相对最高点的响度（LU）、同时发声的声部数、主要音区、和声节奏。起步值，按片子调：

- 最高点唯一，放在全片 60–85% 处，比其余任何一段至少高 2 LU；
- 前三分之一之后至少一个低谷，比最高点低 8 LU 以上，而且低谷里要有东西可听（一件独奏乐器），否则听起来是"音乐没了"（介绍片 v2 的教训）；
- 相邻两章要分得开：响度差 2 LU 以上，或者配器、音区明显换了；
- 密度的峰值可以在高潮之前：示例第 20 小节每秒约 44 个音头（加花、滚奏、音阶），高潮段约 16 个，但高潮更响，靠长音、全音区和更多声部撑起来，不靠更密。

响度是听感紧张度里权重最大的一项，其次是音高（音区）、粗糙度（不协和）和调性紧张度，速度的权重很小（Barchet 等 2024 的 TenseMusic 模型；Farbood 2012 的实验考察的参数还有和声、旋律预期和音头密度）。所以起伏曲线首先是响度曲线，再用音区和和声配合它。

**④ 主题地图：动机在哪一章、以什么样子出现。** 一个动机的生命周期通常是：藏起来的碎片 → 不完整的陈述 → 完整陈述 → 发展（第 3 节的手法）→ 再现。电影常把完整主题留到关键时刻：《侏罗纪公园》的主题在一行人第一次看见腕龙时才出现，整部片只完整出现三次，每次性格不同（Lehman 2025）；《007：大战皇家赌场》把经典 Bond 主题留到最后一轨，中途只暗示过一次；《飞屋环游记》的 "Married Life" 随剧情反复出现，配器、速度和性格都在变（thematic transformation）。示例的主题地图见第 7 节。

## 2. 写主题

- **8 小节或它的倍数，分前后两半。** Richards（2016）的语料里，电影主题最常见的就是这种有"开头 / 结尾"两半的结构。
  - **Sentence**：基本动机 2 小节，重复（可以变化）2 小节，再 4 小节的延续：碎片化、模进、节奏或和声节奏加快，最后终止。它天然往前推，适合发展段和预告片。
  - **Period**：前句以半终止（停在 V）结束，是问；后句重复开头，以完满终止结束，是答。适合揭晓：问句先让人等一下（Open Music Theory）。
- **快速度下用半速感写旋律**：120 BPM 时旋律以四分和二分音符为主（听起来像 60），下面八分或十六分音符的伴奏保持推进。
- **短片可以把问和答压成一个动机的两半**：问句向上，停在不稳定的音级上，讲解过程中反复出现；到"顿悟"时才接上答句，落在主音。
- **轮廓**：拱形最常见（Huron 1996 统计的西方民歌）。一个最高音，常在乐句 2/3 到 3/4 处，越靠后冲劲越大（MyMusicTheory、Ewer），整首的最高音留给高潮。大跳之后反向级进，这是跨文化的倾向，von Hippel 和 Huron（2000）认为主要来自音域的限制。开头给一个有辨识度的音程和节奏：动机的身份主要由节奏和轮廓决定，所以变形之后仍认得出（Open Music Theory）。音域一个八度到十度，好在乐器之间移交。
- **选对音高记号**，同一条旋律才能在不同章节、乐器、八度和调式里复用：

| 想要 | 用 | 例 |
|---|---|---|
| 旋律固定在调里，换八度、乐器、调式都能复用 | `d1` `d2` …（按声部的 `scale` 往上数，七声音阶里 `d8` 是 `d1` 的高八度），配合声部的 `octave`、`scale` | 同一张表给 `"octave": 5` 的弦乐就是高八度重复，给 `"scale": "phrygian"` 就是暗色版本 |
| 动机跟着和弦走（模进、自动换和声） | `s0` `s2`（从和弦根音数的音阶步）或 `c0` `c1` `c2`（和弦音），加 `+5` 这种半音偏移 | D 大调里 `c0 c2 +5` 在 I、ii、iii 上是 D-A-G、E-B-A、F#-C#-B |
| 调外和弦（bVI、bVII）上的动机 | 用 `c`，不用 `s`：调外根音上，`s` 从下方最近的调内音开始数 | — |
| 固定的绝对音高（调好的打击乐、延留和弦） | `A3`、`D4` | — |

旋律写成音符表 `[[拍, 时值, 记号, 力度], …]`，`"loop"` 设成它跨的小节数。力度要写出乐句的起伏：前句弱一点，后句强一点，最高音最强。

## 3. 发展手法

| 手法 | 起什么作用 | 现在怎么写 |
|---|---|---|
| 原样重复 | 建立身份。重复本身会让声音更像音乐：Margulis 的实验里，同一串随机音听 6 遍后被评得更有音乐性 | 复制音符表 |
| 模进 | 往前推、加紧张 | 用 `s` 或 `c` 写一次，放在一串上行的和弦上；或把 `d` 记号整体加一 |
| 碎片化 | 加速，准备终止 | 只留动机头两个音，一小节放两次，同时和声节奏加倍（`chords` 的一格写两个和弦） |
| 紧缩（节奏减值） | 把主题变成推进的引擎 | 时值减半；或做成 `step` 网格加 `pitch` 列表的固定音型 |
| 扩大（节奏增值） | 庄严、告别、收束 | 时值加倍 |
| 倒影 | 对立面、镜像 | 音阶步取负：`s0 s4 s3 s2` → `s0 s-4 s-3 s-2` |
| 换和声 | 同一句话换一种语气 | `d` 记号不动，只改这一段的 `chords` |
| 换配器 | 同一个主题在不同章节换性格。拉威尔的《波莱罗》整首就是两个旋律轮流出现，每次换一件或一组乐器，整首一个大渐强 | 同一张音符表给另一个声部（`by_section` 不能换乐器，只能另起声部） |
| 换调式 | 明暗转换 | 同一张 `d` 表换 `scale`：`phrygian`、`minor`、`major`，五声的 `yu`、`gong` 等 |
| 不完整陈述 | 悬念，把完整主题留到揭晓 | 在终止前停下，最后一个音停在不稳定音上，底下垫 sus 或 V |

## 4. 起伏靠配器、音区和密度，不只靠音量

- **分层加减**是最直接的起伏：一章一章加声部、减声部。游戏音乐叫它 vertical re-orchestration，按强度加减层，音乐不中断。高潮之前先减，对比才出得来。编曲时也可以用 *Making Music* 说的减法：先把素材铺满整首，再一段一段往下删。
- **音区是重量**：低音区（第 2–3 个八度）是压迫和分量，高音区（钢片琴、长笛、高八度的弦乐）是空气和光。高潮同时占两头。
- **力度即音色**：多数声部的 `vel` 同时改变响度和亮度（弦乐的低通截止频率随力度升高，铜管越响越亮），所以渐强用力度写，比用 `gain_db` 更像真的。现有的写法：网格里的数字 `1`–`9`，例如军鼓滚奏 `"2345678999XXXXXX"`；音符表里逐音写力度；弦乐的长 `attack`、铜管的 `swell` 做单个长音上的渐强；跨小节的阶梯渐强，把 `pattern` 写成每小节一条的列表。
- **和声节奏也是起伏**：一小节一个和弦变成一小节两个，是发展段最省事的加速。
- **留白**："突然的安静也是一种打点，可能是最强的一种"（Art of Composing）。本仓库不许数字静音，所以留白是只留一层底（drone、pad、锣的余音、`roomtone`），再让一件乐器独奏。
- **打点预算**：每章最多一个大打点，其余交给音效。多数时候，节奏对上就够了（Art of Composing）。
- **跟画面同步，还是反着走**：动作和音乐完全对齐（mickey-mousing）适合卡通、UI 演示，用在成人向的片子里容易显得幼稚；反过来是 Chion 说的"无动于衷的音乐"（anempathetic），画面激烈，音乐照常往前走，适合反讽和冷峻的段落。产品片和讲解片大多居中：跟情绪走，不跟每一个剪辑点。

## 5. 按片型

- **预告片、发布片**：三幕加 button：铺垫（钢琴、弦乐长音、轻的质感）→ 冲突加码（打击乐、更大的配器、riser）→ 高潮（大鼓、铜管、全奏）→ button（Nathan Fields、Rareform、Pryn）。riser 最好是音乐性的：定音鼓或军鼓滚奏的力度渐强、弦乐上行音阶、越来越密的固定音型；段落的 `riser`（噪声加扫频）不在调上，偶尔用一次可以，不要每 4 小节一次。braam 这类"预告片声音"一首最多一次，放在唯一的高点上。
- **讲解、知识短视频（有旁白）**：
  - 人声段里音乐稳住：一个不动的持续和弦（iZotope），稳定的脉冲和受控的动态（Audio Network）；人声说话时不换配器、音区、调性或速度，不在人声里开始或结束一句旋律，大跳和倚音放进停顿（Garfinkle）；
  - 按频段让位：人声的能量主体在 500 Hz–1 kHz 左右（Thinkspace），辅音的清晰度在更高的 1–4 kHz【综合】。持续的 pad 做低通（`"lp": 2500`），贝斯放在 250 Hz 以下，沙锤这类放在 6 kHz 以上（`"hp": 6000`）；
  - 旋律只放在停顿里，越到后面越密；整片只有一处让音乐当主角：旁白停下来的"顿悟"段；
  - 混音：配乐本身已经为旁白设计好了底（人声段压着，停顿处才上来，像第 7 节的第二个示例）时，用 `bin/vh mix … music_db=0`。默认的 −6 dB 是按响度平直的配乐设计的，对这种配乐再降 6 dB，句间停顿就会被 `bin/vh qa` 判成掉音（判据：0.1 s 窗口低于这一段的中位电平 12 dB，有人声的段落中位电平主要是人声）。那个示例实测：默认 −6 dB 时 2 处掉音，`music_db=0` 时 0 处。没有专门设计过底的配乐，仍按 `04-audio.md` 的默认混（`duck=voice`，−6 dB）。
- **产品片**：动机可以当声音 logo：一个短而独特的旋律放在开头或结尾，和品牌绑在一起（Intel、Netflix，见 Sonic branding）。"问题"段用同一个动机的暗色版本（换调式、放低音区），揭晓时主题第一次完整出现，第 7 节的示例就是这样。
- **中国题材**：起承转合可以直接当四章用。"转"的做法：同主音换五声调式（羽 → 宫），换音区，或者用节奏减值做出"加快"的感觉（整首只有一个 `bpm`，不能变速）。"合"可以用支声复调：两件乐器奏同一条旋律，一件加花（古琴的滑音、吟、猱），一件平直（箫低八度）。锣鼓经当标点：一个"仓"收住一章，余音接进下一章。
- **共同的落点规则**：大的篇章切换落在小节线上，揭晓落在强拍上，标题落在 button 上；音乐的进入可以藏在音效或剪辑后面，让人察觉不到它从哪一刻开始（Art of Composing）；主题和动机的入口写成 `"hit": "section"`，节拍表里就有这些时间点，画面和 `bin/vh qa` 的 cue check 都能用。
- **音效也在调上**：能调音的打击乐都给音高，`gong`、`luogu`、`timpani` 接受 `"pitch"`，示例里爆炸的那一锣调到 D，和整首同调。要和配乐同调、同拍的叮、咚、钟声，写成谱子里的声部（`celesta`、`glockenspiel`、`bell`），加 `"hit": true`。内置音效不在调上：`ding` 固定在 E6（1318 Hz），`boom`、`impact` 收在 34–40 Hz，和配乐的调冲突时改用谱子里的声部。《极盗车神》（Baby Driver）的声音设计按小节和拍子工作，警报、刹车、警笛都对着音乐的速度，只有约 15% 是那辆车真实的声音（Julian Slater）；《敦刻尔克》把诺兰自己怀表的滴答声合成进配乐当脉冲。但速度到处跑的画面，不要硬拿一个恒定的声音去对拍（Slater）。

## 6. 听不见时怎么检查

agent 听不到声音，每一步都要能读出来。

**响度曲线**：ffmpeg 的 `ebur128` 滤镜每 0.1 s 给一个 momentary（0.4 s 窗）和 short-term（3 s 窗）响度，最后给 LRA（short-term 响度分布的 10% 到 95% 分位之差；EBU Tech 3341、3342）。每个值标在窗口的末尾，所以 short-term 往前挪 1.5 s，再按节拍表的段落求平均：

```bash
# 在项目目录里跑
ffmpeg -nostats -i audio/music.wav -af ebur128=framelog=info -f null - 2> audio/ebur128.log
python3 - audio/ebur128.log audio/music.beats.json <<'PY'
import json, re, sys
log, beats = open(sys.argv[1]).read(), json.load(open(sys.argv[2]))
S = [(float(t) - 1.5, float(v)) for t, v in re.findall(r"t:\s*([\d.]+)\s.*?S:\s*(-?[\d.]+)", log)]   # short-term, centred
lra = float(re.findall(r"LRA:\s*([\d.]+) LU", log)[-1])
rows = []
for s in beats["sections"]:
    v = [x for t, x in S if s["start"] <= t < s["end"] and x > -70]
    if v: rows.append((round(sum(v) / len(v), 1), s["name"], s["start"], s["end"]))
for m, n, a, b in rows: print(f"{n:12s} {a:6.1f}–{b:5.1f} s {m:6.1f} LUFS")
top = sorted(rows, reverse=True); dur = beats.get("duration") or rows[-1][3]
print(f"LRA {lra} LU · spread {top[0][0] - top[-1][0]:.1f} LU · loudest {top[0][1]} at "
      f"{(top[0][2] + top[0][3]) / 2 / dur:.0%}, {top[0][0] - top[1][0]:.1f} LU above the next")
PY
```

示例跑出来是 `LRA 11.2 LU · spread 11.5 LU · loudest climax at 77%, 4.4 LU above the next`。起步目标，按片子调：
- 有高潮的片子（产品片、预告）：各段平均响度的最大差 ≥ 8 LU；最响的一段唯一，比第二响的至少高 2 LU，落在全片 60–85%；
- 旁白底和起承转合的起伏可以小一些，写示例时量到的是 7–8 LU，"转"也可以早一点（57%）；
- 有旁白时再按第 5 节的判据看停顿处的掉音。

**旋律压不压得住伴奏**："缺旋律"听不见，只能量。起步目标【综合】：主旋律比这一段最响的伴奏声部高 3 dB 以上；在旋律和人声所在的 300 Hz–4 kHz 里，比所有伴奏加起来至少高 2 dB。只剩一件乐器加一层底的段落，看第二个数就行。引擎的 `render()` 能交出每个声部的干声 stem（`music.py` 里给测试和工具用的接口，签名以代码为准），按段落比电平：

```bash
# 在仓库根目录跑；第二个参数是主旋律声部的 id，逗号分隔
uv run --with numpy --with scipy python - projects/<p>/audio/score.json brass_theme,str_theme <<'PY'
import json, sys; sys.path.insert(0, "tools/audio")
import numpy as np, music, instruments as ins
score, lead = json.load(open(sys.argv[1])), set(sys.argv[2].split(","))
stems, info = {}, {}; _, bm = music.render(score, stems=stems, info=info)
g, SR = info["gain"], music.SR
plays, n = {}, {}
for p in score["parts"]:                                   # 声部名和引擎的一样：id，或"乐器#序号"
    k = p.get("id") or f'{p["inst"]}#{n.setdefault(p["inst"], 0)}'
    if "id" not in p: n[p["inst"]] += 1
    plays[k] = p.get("sections", "all")
db = lambda x: 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
band = lambda x: ins.hpf(ins.lpf(x, 4000, 4), 300, 4)
for s in bm["sections"]:
    i, j = int(s["start"] * SR), int(s["end"] * SR)
    here = {k: v[:, i:j].mean(0) * g for k, v in stems.items() if plays[k] == "all" or s["name"] in plays[k]}
    L, O = [k for k in here if k in lead], [k for k in here if k not in lead]
    if not L: continue
    top = max((db(here[k]) for k in O), default=-120.0)
    lo = sum((here[k] for k in O), np.zeros(j - i))
    print(f"{s['name']:10s} lead {max(db(here[k]) for k in L) - top:+5.1f} dB over the loudest other part · "
          f"{db(band(sum(here[k] for k in L))) - db(band(lo)):+5.1f} dB over all others in 300 Hz–4 kHz")
PY
```

产品片示例（主旋律声部是 `piano_q`、`mel_str`、`mel_pno`、`mel_fl`、`brass_theme`、`str_theme`、`celesta`）：高潮段 +6.7 / +7.9 dB，主题后句 +6.8 / +8.3 dB；只剩钢琴加 drone 的问题段 +1.8 / +6.0 dB。

**音符对不对**：如果 `bin/vh music --roll` 可用，渲染前先用它看每个声部每小节实际奏出的音：旋律是不是写的那样，模进是不是在走。

**成品有没有毛病**：`bin/vh qa music.wav music.beats.json` 查数字静音、掉音、抽吸、click，并做 cue check。

**写示例时踩到的合成坑**（都已修掉；前三条在当前引擎上用 `bin/vh qa` 复现过）：
- **同度重叠会拍频**：两个合成声部在同一音高上叠同一条旋律（钢琴加弦乐），相位互相抵消，qa 在 27.4 s 报了一处 4 dB 多的抽吸 → 重叠按八度来。
- **note 型管乐的音之间有缝**：`dizi` 这类声部每个音自带起音和收尾，音符首尾相接时中间会塌下去，qa 当成抽吸 → 让音符重叠约 0.15 拍，或者改用 mono 型的 `flute`、`xiao`，它们会连成一句。
- **颤音加大混响会起伏**：近似正弦的独奏（笛子、长笛、箫）在长音上加颤音，再多送混响，干声和混响会周期性地互相抵消，形成约 5 Hz 的起伏，qa 报抽吸 → 这类声部的 `send` 不超过约 0.2。
- **鼓太响会吃掉峰值余量**：整首按峰值归一到 `master_db`（默认 −1 dBFS），鼓的瞬态一高，持续的旋律就被整体压低 → 鼓放在旋律下面。示例的第一版高潮段，定音鼓只比铜管主旋律低 0.7 dB；把鼓调低以后，主旋律高出最响的伴奏 7 dB，高潮段整体还响了 0.5 LU。
- 两个小的：`loop` 和按小节的 `pattern` 列表数的是这个声部自己的小节，一个声部跨好几段时，列表要轮换，或者每段单独起一个声部；片头第一个音（t = 0）的 cue 检测会晚约 48 ms，不要把 t = 0 写成 hit。

## 7. 两个示例

两首都只用现有引擎，两次渲染字节相同，`bin/vh qa` 通过。

### 7.1 产品片弧线（58.5 s）

120 BPM（30 fps 下一拍 15 帧），D 大调，开头用 D 弗里吉亚。一个动机撑起全曲：1-5-4-3（D A G F#），上行纯五度，再级进落回。`sections` 的小节数是 chaos 4 · nova 1 · question 2 · theme_a 4 · theme_b 4 · develop 5 · climax 4 · coda 3，`"meters": {"7": 6, "27": 6}`：第 7 小节的 6/4 相当于写出来的延长记号，第 27 小节让最后一个和弦响完。

| 段 | 时间 | 平均响度 | 动机的样子 | 谁来演 |
|---|---|---|---|---|
| chaos | 0–8 s | −17.8 LUFS（−22 → −14 渐强） | 紧缩成十六分音符的固定音型，弗里吉亚调式（D A G F），藏在低音区；第 3–4 小节低音铜管用二分音符把它放慢奏一遍 | 弦乐 marcato、合成器、铜管 |
| nova | 8–10 s | −15.5 | 全曲唯一的大打击：大鼓、定音鼓、调到 D 的锣、铙钹和铜管和弦同时砸下，然后只剩锣的余音 | 打击乐、铜管 |
| question | 10–15 s | −21.6（全曲最低） | 只说半句：D、A、G……停在 E，底下是渐强的 Asus4 | 毡锤钢琴独奏 |
| theme_a、theme_b | 15–31 s | −16.8、−14.7 | 完整的 8 小节乐段：前句停在 A（半终止），大提琴在空当里接一句；后句在第 14 小节到最高音 F#5，落在主和弦 | 弦乐 + 高八度钢琴，后句加长笛和沙锤 |
| develop | 31–41 s | −14.5（−16.8 → −11.0） | 动机头在 D、E、F# 上逐级模进；第 19–20 小节只剩"根音 → 五音"，一小节两个和弦，进 bVI–bVII；军鼓、定音鼓力度渐强的滚奏，一条两个八度的弦乐上行 | 铜管；弦乐八分音符的固定音型 |
| climax | 41–49 s | −10.1（全曲最高，在 77% 处） | 主题后句全奏 | 铜管 + 高八度弦乐、定音鼓、镲 |
| coda | 49–56 s | −16.7，然后淡出 | 放慢（扩大）：D、A、G、F#，把问题段悬着的 E 解决到 F#；和声 IV → iv → I | 钢片琴 |

问题段和主题（摘录；同样的音符表还复制给了高八度的钢琴、theme_b 的长笛和高潮段的铜管）：

```json
{"inst": "piano", "id": "piano_q", "sections": ["question"], "octave": 4, "loop": 2,
 "params": {"tone": "felt", "pedal": true}, "gain_db": 4, "send": 0.35, "hit": "section",
 "pattern": [[0, 8, "d1,,", 0.35], [0, 1.5, "d1", 0.62], [1.5, 2.5, "d5", 0.68], [4, 1, "d4", 0.58], [5, 5, "d2", 0.55]]},

{"inst": "strings", "id": "mel_str", "sections": ["theme_a", "theme_b"], "octave": 4, "loop": 8,
 "params": {"attack": 0.1, "release": 0.35}, "gain_db": -2, "send": 0.3, "hit": "section",
 "pattern": [[0, 1, "d1", 0.6], [1, 2, "d5", 0.68], [3, 1, "d4", 0.6], [4, 1, "d3", 0.58], [5, 1, "d4", 0.6], [6, 2, "d2", 0.55],
             [8, 1, "d3", 0.6], [9, 1, "d4", 0.64], [10, 1, "d5", 0.68], [11, 1, "d6", 0.72], [12, 4, "d5", 0.66],
             [16, 1, "d1", 0.7], [17, 2, "d5", 0.78], [19, 1, "d4", 0.72], [20, 1, "d3", 0.72], [21, 1, "d5", 0.78], [22, 2, "d8", 0.84],
             [24, 1.2, "d6", 0.84], [25, 2, "d10", 0.95], [27, 0.5, "d9", 0.84], [27.5, 0.5, "d8", 0.8], [28, 2, "d7", 0.78], [30, 2, "d8", 0.74]]}
```

同一个动机在 chaos 段（紧缩、弗里吉亚、逐小节渐强）和发展段（跟着和弦模进，最后碎片化）：

```json
{"inst": "strings", "id": "ost_chaos", "sections": ["chaos"], "scale": "phrygian", "octave": 3, "step": 16,
 "pitch": ["d1", "d5", "d4", "d3"], "params": {"marcato": true}, "legato": 0.8, "gain_db": -3,
 "pattern": ["4222422242224222", "5333533353335333", "6444644464446444", "8666866686668666"]},

{"inst": "brass", "id": "brass_seq", "sections": ["develop"], "octave": 4, "loop": 5, "gain_db": 0, "hit": "section",
 "pattern": [[0, 1, "c0", 0.7], [1, 2, "c2", 0.74], [3, 1, "+5", 0.7],
             [4, 1, "c0", 0.74], [5, 2, "c2", 0.78], [7, 1, "+5", 0.74],
             [8, 1, "c0", 0.78], [9, 2, "c2", 0.82], [11, 1, "+5", 0.78],
             [12, 0.5, "c0", 0.82], [12.5, 1.5, "c2", 0.86], [14, 0.5, "c0", 0.86], [14.5, 1.5, "c2", 0.9],
             [16, 0.5, "c0", 0.9], [16.5, 1.5, "c2", 0.94], [18, 0.5, "c0'", 0.94], [18.5, 1.5, "c2'", 1.0]]}
```

发展段的和弦是 `["I", "ii", "iii", "IV V", "bVI bVII"]`：前三小节的 `c0 c2 +5` 自动变成 D-A-G、E-B-A、F#-C#-B；后两小节只剩"根音 → 五音"，一小节两个和弦。bVI、bVII 是调外和弦，所以这里用 `c` 记号。

### 7.2 讲解片的旁白底（39.7 s）

旁白讲"天空为什么是蓝的？"，100 BPM（30 fps 下一拍 18 帧），G 大调。动机是一个问句 Q：和弦的 3、5、6 音（`s2 s4 s5`，在 G 上是 B-D-E），往上停在不稳定的六级。它用和弦相对的记号写，每次出现自动换和声：D 上是 F#-A-B，C 上是 E-G-A。人声说话时音乐不动：一个低通到 2.5 kHz 的 pad、G2–D3 的低音、轻底鼓、6 kHz 以上的沙锤，500 Hz–3 kHz 里不起新东西；Q 只在句与句之间出现。

| 段 | 时间 | 平均响度 | 音乐在做什么 |
|---|---|---|---|
| hook | 0–2.4 s | −18.6 LUFS | 问句之后，钢片琴只奏 Q：B-D-E |
| setup | 2.4–12 s | −20.1 | 人声段只有底；第 5 小节人声停下后，Q 在属和弦上出现（F#-A-B），这一段停在"问号"上 |
| explain | 12–24 s | −18.1 | 加边击和中低音区的竖琴分解和弦（有节奏、没有旋律）；Q 的片段只在两句之间，第 10 小节连续两次、第二次高一级；然后 stopdown，只留 pad 给"这就是——" |
| aha | 24–31.2 s | −12.8（全曲最高，在 70% 处） | 没有人声，全片唯一让音乐当主角的地方：Q、高一级的 Q、答句 E-D-A-G 落在主音；钢琴，弦乐低八度，钟琴高八度，鼓进来 |
| button | 31.2–37.2 s | −19.5 | 人声说出"瑞利散射"，只剩底；然后钢片琴单独奏答句，做片尾的 sting |

Q 在讲解段的写法（摘录）：

```json
{"inst": "celesta", "id": "q_explain", "sections": ["explain"], "octave": 4, "loop": 5, "gain_db": -10, "hit": true,
 "pattern": [[7, 0.25, "s2", 0.6], [7.25, 0.25, "s4", 0.62], [7.5, 0.5, "s5", 0.64],
             [16, 0.25, "s2", 0.62], [16.25, 0.25, "s4", 0.64], [16.5, 0.5, "s5", 0.66],
             [17, 0.25, "s3", 0.66], [17.25, 0.25, "s5", 0.68], [17.5, 0.5, "s6", 0.72]]}
```

第 10 小节第 2 拍的 stopdown 要在每个还在响的声部里分别写：伴奏型没法在小节中间停，就改写成网格；跨段的按小节列表（这里的底鼓、低音、沙锤）要按声部自己的小节数轮换：底鼓在 setup 里已经走了 4 个小节，所以 explain 的第 1 小节取的是列表的第 5 条。混音用 `music_db=0`（第 5 节）。

## 延伸阅读 / 来源

乐理与主题写作
- Open Music Theory, [The sentence](https://openmusictheory.github.io/sentence)；[The period](https://elliotthauser.com/openmusictheory/period.html)（OMT 的镜像）。
- Mark Richards (2016), [Film Music Themes: Analysis and Corpus Study](https://www.mtosmt.org/issues/mto.16.22.1/mto.16.22.1.richards.html), *Music Theory Online* 22.1。
- David Huron (1996), [The Melodic Arch in Western Folksongs](https://www.researchgate.net/publication/239063783_The_Melodic_Arch_in_Western_Folksongs), *Computing in Musicology* 10。
- Paul von Hippel & David Huron (2000), [Why Do Skips Precede Reversals? The Effect of Tessitura on Melodic Structure](https://online.ucpress.edu/mp/article-abstract/18/1/59/62088/), *Music Perception* 18(1)。
- Gary Ewer, [3 Pointers for Calculating a Melody's Climactic High Point](https://www.secretsofsongwriting.com/2010/09/27/3-pointers-for-calculating-a-melodys-climactic-high-point/)；MyMusicTheory, [Composing a solo melody](https://mymusictheory.com/composition/q3b-composing-a-solo-melody/)。
- Wikipedia, [Thematic transformation](https://en.wikipedia.org/wiki/Thematic_transformation)、[Leitmotif](https://en.wikipedia.org/wiki/Leitmotif)、[Ternary form](https://en.wikipedia.org/wiki/Ternary_form)、[Rondo](https://en.wikipedia.org/wiki/Rondo)、[Cadence](https://en.wikipedia.org/wiki/Cadence)。

电影配乐里的主题
- Frank Lehman (2025), ["Remembering Petticoat Lane," Revisited: Themes, Topics, and Codes in the Music of Jurassic Park](https://publications-prairial.fr/emergences/index.php?id=297), *Émergences* 2。
- Wikipedia, [Jurassic Park (film score)](https://en.wikipedia.org/wiki/Jurassic_Park_(film_score))、[Casino Royale (2006 soundtrack)](https://en.wikipedia.org/wiki/Casino_Royale_(2006_soundtrack))、[Up (soundtrack)](https://en.wikipedia.org/wiki/Up_(soundtrack))。
- Scott Davie, [Ravel's Boléro](https://theconversation.com/decoding-the-music-masterpieces-ravels-bolero-a-sinuous-and-sexy-composition-with-no-music-in-it-149528), *The Conversation*。

张力、起伏与编曲
- Barchet, Rimmele & Pelofi (2024), [TenseMusic: An automatic prediction model for musical tension](https://pmc.ncbi.nlm.nih.gov/articles/PMC10798497/), *PLOS ONE*。
- Morwaread Farbood (2012), [A parametric, temporal model of musical tension](https://nyuscholars.nyu.edu/en/publications/a-parametric-temporal-model-of-musical-tension), *Music Perception* 29(4)，[doi:10.1525/mp.2012.29.4.387](https://doi.org/10.1525/mp.2012.29.4.387)。
- Dennis DeSantis, *Making Music* (Ableton)：[Dramatic Arc](https://makingmusic.ableton.com/dramatic-arc)、[Arranging as a Subtractive Process](https://makingmusic.ableton.com/arranging-as-a-subtractive-process)、[Unique Events](https://makingmusic.ableton.com/unique-events)。
- Wikipedia, [Adaptive music](https://en.wikipedia.org/wiki/Adaptive_music)（vertical re-orchestration）。

对画面作曲
- Rareform Audio, [Drop vs. Stopdown](https://www.rareformaudio.com/blog/trailer-music-drop-vs-stopdown)、[Trailer Music Structure](https://www.rareformaudio.com/blog/how-production-music-reveals-trailer-structure)。
- Nathan Fields, [Building Epic Trailers: How Music Follows a Three-Act Structure](https://www.nathanfieldsmusic.com/blog/three-act-structure-trailer-music)。
- Richard Pryn, [How to structure your trailer music](https://richardpryn.com/how-to-structure-trailer-music/)。
- Craig Stuart Garfinkle, [Composing Under Dialogue: The Unwritten Rules](http://craigstuartgarfinkle.blogspot.com/2012/10/composing-under-dialogue-unwritten-rules.html)；Thinkspace, [How to Underscore](https://thinkspace.ac.uk/blog/blog-how-to-underscore/)。
- iZotope, [Beginner Tips for Writing Music to Picture](https://www.izotope.com/en/learn/writing-music-to-picture-film-tv-beyond.html)。
- Audio Network, [How To Choose Music for a Voiceover Heavy Video](https://blog.audionetwork.com/the-edit/music/how-to-choose-music-for-a-voiceover-heavy-video)。
- Art of Composing, [How to Spot a Film](https://www.artofcomposing.com/how-to-spot-a-film)。
- Wikipedia, [Mickey Mousing](https://en.wikipedia.org/wiki/Mickey_Mousing)、[Anempathetic sound](https://en.wikipedia.org/wiki/Anempathetic_sound)、[Sonic branding](https://en.wikipedia.org/wiki/Sonic_branding)。

声音设计
- MPA *The Credits*, [Baby Driver's Supervising Sound Editor Dissects the Movie's Unique Syncopated Style](https://www.motionpictures.org/2018/01/oscar-watch-baby-drivers-sound-editor-dissects-movies-unique-syncopated-style/)（Julian Slater）。
- Wikipedia, [Dunkirk (soundtrack)](https://en.wikipedia.org/wiki/Dunkirk_(soundtrack))。
- MusicRadar, [How to blend sound design and score](https://www.musicradar.com/how-to/sound-design-scoring)。

算法作曲为什么容易套路
- Magenta (2016), [Generating Long-Term Structure in Songs and Stories](https://magenta.tensorflow.org/2016/07/15/lookback-rnn-attention-rnn)。
- Huang et al. (2018), [Music Transformer: Generating Music with Long-Term Structure](https://arxiv.org/abs/1809.04281)。
- Elizabeth Hellmuth Margulis (2014), [On Repeat: How Music Plays the Mind](https://www.semanticscholar.org/paper/On-Repeat:-How-Music-Plays-the-Mind-Margulis/58df7e47741bfc220244b96192a019a486b6fd9d)。
- Mark Spicer (2017), [Fragile, Emergent, and Absent Tonics in Pop Music](https://mtosmt.org/issues/mto.17.23.2/mto.17.23.2.spicer.pdf), *Music Theory Online* 23.2。

测量
- EBU [Tech 3341](https://tech.ebu.ch/docs/tech/tech3341.pdf)（momentary 0.4 s、short-term 3 s）、[Tech 3342](https://tech.ebu.ch/docs/tech/tech3342.pdf)（LRA）。
