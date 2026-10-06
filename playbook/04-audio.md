# 04 音频

原则：**先有音频，再有时长。** 要先把音频变成时间表，agent 才能处理：旁白要有词级时间戳，音乐要有节拍网格，歌曲要有逐句歌词时间。

本篇讲声音怎么做、怎么判断。每条命令的参数、`score.json` 的完整写法、各家服务商的细节、混音报告怎么读，在 `tools/audio/README.md`，用到哪一节再查；拿 `bin/vh qa`、`beats`、`mix` 的读数下结论之前，先看那里的"已知局限"和"混音"一节末尾的"局限"。现成的样板：`showcase/00`–`03` 各带 `tools/build_audio.sh`，02、03 是旁白 + 字幕 + 混音 profile 的完整一套。

## 现成接口：`bin/vh` 的声音命令

声音分成 **配音、配乐、音效、歌曲** 四类。每类都有统一的命令和输入输出格式，服务商或来源可以替换，流程不变。依赖由 `uv run --with` 临时提供，不装进全局环境；**API key 只从环境变量读取**。

```bash
# 配音（双语）：audio/script.txt → voiceover.<lang>.wav + timeline.<lang>.json
bin/vh tts projects/<p> qwen Serena zh            # 本地开源 Qwen3-TTS（默认；首次下载约 2GB）
bin/vh tts projects/<p> qwen Aiden en             # 同一份稿子，英文旁白
bin/vh tts projects/<p> gemini Kore zh --align gemini   # 云端 Gemini；--align：逐句词级时间 + ASR 对稿，跑偏的句子会被标出来
bin/vh captions projects/<p> zh                    # → captions.zh/en/bi.srt + captions.json（给引擎画进画面）
bin/vh voices list en-GB --gender female           # Gemini 音色库；bin/vh voices design "<描述>" 设计一个音色 → voice_… id
# 配乐：代码作曲，段落对齐镜头，节拍精确
bin/vh music --example > projects/<p>/audio/score.json        # --example zh：编钟、古筝、笛子、太鼓的中国风起步谱；--example list：全部起步谱
bin/vh music --instruments                                    # 乐器声部（parts）的全部乐器和伴奏型，一行一个
bin/vh music projects/<p>/audio/score.json projects/<p>/audio/music.wav     # + music.beats.json（段落、节拍、冲击点）
# 音效：内置库 + 按动作时间摆放（立体声，事件可带 pan、dist）
bin/vh sfx lib projects/<p>/audio/sfx
bin/vh sfx place projects/<p>/audio/events.json projects/<p>/audio/sfx.wav 45 --lib projects/<p>/audio/sfx
bin/vh sfx audition whoosh 8 --png                 # 先听：一个音效的 8 个 variant，每个一行参数和测量（--png：频谱图）
# 混音、成片 QA 与合成：按视频类型选 profile（见下文"混音"），层次从一个锚点量起
bin/vh mix projects/<p>/audio/mix.wav profile=short voice=…/voiceover.zh.wav music=…/music.wav \
           events=…/events.json lib=…/sfx timeline=…/timeline.zh.json stems=projects/<p>/audio/stems
bin/vh qa projects/<p>/audio/mix.wav projects/<p>/audio/music.beats.json projects/<p>/audio/events.json \
          --stems projects/<p>/audio/stems   # 静音、掉音、抽吸、click + cue check + 混音报告（qa mix）
bin/vh mux projects/<p>/out/final.mp4 projects/<p>/audio/mix.wav projects/<p>/out/final-av.mp4 \
           projects/<p>/audio/captions.zh.srt projects/<p>/audio/captions.en.srt   # 软字幕轨（可开关）
bin/vh beats <任意音乐文件>                          # 外来音乐的节拍 + hits、kick、snare 重音（librosa）
```

### 配音（`tts` / `captions`）

**旁白稿**：`audio/script.txt` 一行一句，一句对应一条字幕或一个 cue。
- 双语写成 `中文 || English`，`--lang` 决定念哪一边，两边都会进时间表；
- 只写一边的句子照原样念。进字幕时，含中日韩字符的算中文，不含的算英文，所以纯英文稿出的是 `captions.en.srt`。想让一句纯英文（比如品牌名）留在中文一侧，写成 `Claude Code ||`；只有标点的一句（`……`）跟着前面的单边句走；
- 可以加 `@id` 前缀，比如 `@hook 一句话，做出一支片子。 || One sentence in, one film out.`。
- **写念法，不写字面**：单位、缩写和符号，TTS 常照字母或字面念。showcase 02 的"2 GHz"被念成了 G、H、Z 三个字母，维护者听出来才重录。送去合成的文字要写真实的念法（"2 G赫兹""50 千赫兹"），数字、公式、英文缩写也一样。
  - `script.txt` 一句只有一份文本，合成和字幕都用它。念法和字幕必须不同（比如画面烧着"2 GHz"）时，就用念法单独合成那一句，timeline 里的字幕文字留原文，再在 `script.txt` 的注释里记下念法（02 就是这样做的）。
  - 合成后，单位和数字要人耳听一遍：Gemini 转写的第一遍对这类词也不可靠（02 的新 take 第一遍只有 0.10），不能只看相似度。
- 每句合成后，provider 自带的句首句尾静音会被裁掉，所以句间距离就是 `--gap`，按拍落点时人声也落在拍上（裁法和阈值见 `tools/audio/README.md`；想保留原样，加 `--keep-edges`）；
- 双人对话：先写一行 `@speakers A=Kore B=Puck`，之后每句在 `@id` 和 `[指示]` 后面写说话人，见 `tools/audio/README.md` 的"双人对话"。

按句合成，所以每句的起止时间都是**实测**的（`--join` 整段合成时除外，见 `tools/audio/README.md` 的"整段合成"）。

**旁白晚一点进来**（片头先有几秒画面）：合成时加 `--lead <秒>`，不对拍也能用，第一句从那里开始，前面是真静音，timeline 也按片子的时间写；片尾在 profile 混音里用 `dur=` 补齐或截到片长。合成以后再自己垫静音的，别用 `anullsrc` 加 `concat` 滤镜（会把整条人声悄悄量化成 8 bit），做法见 `tools/audio/README.md` 的"手动的响度和合成命令"。

**同一份稿，中文和英文旁白长度不同**（实测一段 3 句的稿子：中文 9.3s，英文 10.8s）。所以双语成片要各自按 `timeline.<lang>.json` 排时间：
- 画面可以共用，但节奏按语言重排；
- 或者只出一种语言的旁白，配中英双语字幕。

**选哪家**（每家的音色、要什么 key、实测状态见 `tools/audio/README.md` 的"provider 一览"）：

| provider | 什么时候用 |
|---|---|
| `qwen`（默认） | 本地开源 Qwen3-TTS，免费、离线，首次下载约 2 GB；0.6B 模型念英文短句偶尔停不下来，每条都要查 |
| `gemini` | 云端，表演力最好，能用一句话导演语气，适合讲解旁白和双人对话；要 `GEMINI_API_KEY` |
| `say` / `edge` | 打草稿；只能念，不能演 |
| `elevenlabs` / `dashscope` | 接口已留，还没实测 |

**每条配音都要查**：加 `--align gemini` 让机器逐句转写、对稿（见下一节），或者至少看一眼 `timeline.<lang>.json` 里每句的时长。被标出来的句子重跑，或者换 provider。

#### 词级时间和对稿检查（`--align gemini`）

`--align gemini` 对任何 provider 都能用：每句合成完交给 Gemini 转写，拿回带时间戳的词，再和稿子逐字对齐。结果写进 timeline：`words` 是逐词时间（文字用稿子的写法），字幕和画面逐词同步用它；`asr` 是和稿子的相似度，跑偏、或者句首句尾多出 1 s 以上声音的句子标上 `flag`，命令最后逐句列出来。转写失败也不丢配音：修好原因后，同一条命令加 `--resume` 接着跑。时间步长、费用、限额和实测见 `tools/audio/README.md` 的同名一节。

有词级时间时，`bin/vh captions` 会给每条字幕加上 `words`，念得太快的短字幕会往后延到 1.8 s（`tools/audio/README.md` 的"字幕"）。

**双人对话、整段合成、音色、费用**：`@speakers` 双人对话、`--join` 整段合成、音色库和设计音色（`bin/vh voices`）、Gemini 的费用和限额，都在 `tools/audio/README.md` 的同名各节。用了 Gemini 旁白的片子，在 `NOTES.md` 写明"旁白为 AI 合成（Gemini TTS，含 SynthID 水印）"，发布时按平台要求标注。

**字幕的两种交付方式**：
- **烧进画面**：引擎读 `captions.json` 绘制，属于画面的一部分，同样必须是 t 的纯函数，样式按类型文档；
- **软字幕轨**：`bin/vh mux … captions.zh.srt captions.en.srt` 封装进 mp4，播放器或平台可以开关。画面里已经烧了字幕时加 `--subs-off`：每条字幕轨都不设成默认，播放器不会自己打开一套叠在烧录字幕上（MP4 封装器总会把第一条字幕轨标成启用，`--subs-off` 把这一位清掉）。

竖屏视频导出时用 `bin/vh captions <p> zh 11`，中文每行最多 11 字。

### 配乐（`music`）

来源优先级（借鉴自归藏 product-video skill 的做法）：
1. **用户给的曲子**，或用户有授权的曲库。按它的实际节拍重新对齐画面：`bin/vh beats`。
2. **本机确实能跑的音乐生成模型**：先确认权重已经下载、运行环境也装好，才算可用。接口位已留，见下文"歌曲"。
3. **代码原创作曲**：`bin/vh music`。编曲源码 `score.json` 跟着项目一起提交，段落（`sections`）按镜头边界排，音色和速度按片子的气质选。因为曲子是我们自己写的，节拍网格和冲击点是**精确的**，不用再做节拍检测。

**不要**下载来路不明的 BGM，不要扒参考视频的音乐，也不要把示例曲改个名字就当新配乐。

**免版税曲库**（未核实，使用前看条款）：Uppbeat 的免费档要求署名，而且每支视频要带一个单独的授权码；Pixabay 允许商用，不强制署名。不管用哪家，来源、授权方式和授权码都记进 NOTES 的素材台账。

**剪外来音乐时**，切点放在拍上，大的段落跳转放在小节线上（用 `bin/vh beats` 的 `beats`、`downbeats` 找点），接缝处做几毫秒的交叉淡化，例如 ffmpeg 的 `acrossfade=d=0.008`。在两个波形中间硬切，会留下一个 click。

外来音乐跑 `bin/vh beats` 得到 `bpm`、`beats`、`downbeats`，以及 `hits`、`kick`、`snare` 三组带强度的重音，精度在 1 帧以内；切分节奏的曲子 BPM 可能报成一半，硬切之前先对照一下拍子（`tools/audio/README.md` 的"外来音乐的节拍"）。

**代码作曲**：从 `bin/vh music --example` 起步（`--example list` 看全部起步谱，`--instruments` 看全部乐器和伴奏型）。`score.json` 的 `sections` 按镜头边界排段落（小节数、和弦、能量、冲击点），`parts` 写真正的乐器声部（钢琴、弦乐、古琴、合成器、鼓……，按节奏型或音符表演奏），`motifs` 写一次、到处调用的动机。输出的 `music.beats.json` 有段落、节拍和冲击点，引擎直接读它切镜和打点；声部加上 `"note_map": true`，还会列出它的每个音，画面可以逐音驱动（`08-vfx-and-motion-sources.md` 的"声画联动的接法"）。全部写法、电平的起点、渲染前的校验、确定性和做不到的事，见 `tools/audio/README.md` 的"score.json"；要篇章和主题，读 `11-composition.md`。

**每个声部都必须听得见**：一个音也没有的声部，或者成品里最响的 50 ms 低于 −40 dBFS 的声部，渲染会直接报错并点名。确实要很轻的写 `"quiet": true`。

**戏剧性的"停"不能做成数字静音。** 要停的时候：
- 保留一层底（sub 或 pad）；
- 把滤波往下收，撤掉鼓；
- 再用一个反向渐强（reverse swell）拉进下一个重拍。

介绍片 v2 有 4 处真静音，用户听到的是"卡顿"；v3 把这 4 处都改成这样的"屏息"。`bin/vh qa` 会把检查区间里任何 ≥ 20 ms 的数字静音判为问题：区间默认从 1.0 s 起，到节拍表的淡出起点为止（没有节拍表时到片尾前 2.8 s），`--from`、`--to` 可改；区间外（片头片尾）的静音只列出来，不算失败。

### 音效（`sfx`）

- **音效是独立的事件层**，和音乐分开：`audio/events.json` 写成 `[{t, sfx, gain_db, pan, dist}]`，后两项可选；内置音效还可以带 `variant` 和塑形参数（见下）。`sfx place` 输出 48 kHz 立体声。
- **`t` 是"落点"**：内置音效各自带落点偏移（例如 whoosh 的峰值、riser 的顶点），摆放时会自动对齐，保证声音峰值和动作在同一帧。riser 因此写在它要冲到的那一刻，声音从 `t − dur` 开始；写成铺垫开始的时刻，整段声音就早了一个 `dur`，峰值落在铺垫刚开始的地方。
- **声像和距离**：事件可以带 `pan`（−1 最左，1 最右）和 `dist`（≥ 1，越远越轻、越闷）。pan 从画面上算，不要凭感觉写：取发声物体在那一刻的屏幕 x，`pan = 2·x / 画面宽度 − 1`，再乘 0.7–0.8 收一点；3D 场景用相机坐标。公式和细节见 `tools/audio/README.md`。
- **来源顺序**：先用有授权的录音素材（在 NOTES 的素材台账里记下来源和许可）；缺的类别再用内置库补。自己的立体声素材会先折成单声道，当作一个点声源来摆。内置库有 21 个代码合成音效，都是 MIT 原创，用 numpy 合成，可以复现：
  - 转场：whoosh、swish_rev、whip、swoosh_tonal、air、paper、tape、shimmer；
  - 小动作：click、tick、pop、typing、shutter、glitch；
  - 铺垫和命中：riser、impact、boom；
  - 提示音：ding、success、error、toggle。
- **同一个音效每次都会变一点**：内置音效（四个提示音除外）的每个事件默认拿到自己的 variant，同一支片子里像同一只手的动作在慢慢变化，同一份 events.json 每次渲染逐字节相同；想留住某一下就写 `"variant": n`（机制见 `tools/audio/README.md`）。
- **转场音效按风格选。** 下表是起点，不是规定：

  | 风格（`styles/` 里的例子） | 转场 |
  |---|---|
  | 发布片、keynote、UI、机械（product-keynote、fui-hud、clockwork-map、pastel-ui 的发送和甩出、y2k-chrome 的铬管） | swoosh_tonal，短而亮的 whoosh |
  | 科幻、宏大（monumental-scifi；dunhuang-mural 的飞天用柔和的一种） | swoosh_tonal（tone 高一点），长而低的 whoosh |
  | 卡通、扁平、漫画、快摇（bouncy-flat-2d、halftone-comic、pixel-16bit、neon-step-print、swiss-grid-type，symmetry-pastel 的甩镜） | whip，配 pop |
  | 数据、讲解、纪录、留白多的（editorial-data、bubble-chart-story、archival-pan-zoom、ink-wash；dark-math 干脆不加） | air，轻的 whoosh |
  | 手绘、拼贴、剪纸、印刷（watercolor-pastoral、cutout-jazz、silhouette-papercut、risograph、isotype、guochao-festive、blueprint） | paper |
  | 复古、录像带、终端、胶片（crt-terminal、synthwave-outrun、scratched-type；brutalist-meme 的硬切是两条 glitch 录音轮换） | tape（`dir: "down"` 停带，`"up"` 倒带），glitch |
  | 揭示、标题落定（哪种风格都可能有） | shimmer（按配乐的调设 `pitch`，默认是 A 大调五声音阶） |
- **按动作给转场塑形**：转场类内置音效接受 `dur`、`pitch`（或 `center`）、`dir`、`bright`、`tone`，任何音效都能写 `pan_from`、`pan_to`。小而快的动作短、高、亮，大而慢的动作长、低、厚（字段和例子见 `tools/audio/README.md`）。
- **一支片子里不要每一刀都是同一个声音。** 默认已经会变，再往前走一步：不同性质的切换用不同的转场（段落之间 whoosh，页内的小切换 air 或 paper），每一下按它的动作塑形。
- **先听再定。** `bin/vh sfx audition whoosh 8` 把同一个音效的 8 个 variant 排进一个 WAV，两两之间隔 0.6 s，旁边的 txt 每行写出它的参数和测出来的长度、频谱重心、扫频方向；加 `dur=1.2 dir=down` 听塑形以后的家族，`--walk` 听一支片子里连着的 8 下，`all` 把 21 个内置音效的 plain 版各放一遍，`--png` 画一张标好号的频谱图（听不到的时候看它）。生成的 json 是放进去的事件表，可以直接给 `bin/vh qa`。
- **重复会被提醒**：`bin/vh qa` 拿到事件表时，同一类声音连着 3 次以上听起来一样就警告（不算失败；录音素材轮换几条就好）。
- **`role`**（可选：`hero`、`detail`、`ambience`、`signal`）：事件在混音 profile 里属于哪一类。名字和它在这支片子里的作用不一致时就写，判法见 `tools/audio/README.md` 的"什么时候写 `role`"。
- **不要让每个音效都去压音乐。** 介绍片 v2 把 74 个音效全接进了 ducker，ratio 是 6，配乐跟着每个音效一抽一抽。混音 profile 里音效从不压音乐（只有没人说话时，hero 命中处音乐让 2–2.5 dB）；不用 profile 时默认也只让人声压音乐（`duck=voice`），真要用 `duck=on`，把 `duck_ratio` 降到 2–3。`bin/vh qa` 的抽吸一项专门查这种问题。

### 混音（`mix`）和混音报告（`qa mix`）

**按视频类型选一个 profile，所有层都相对一个锚点放。** 有旁白时锚点是旁白（各句响度的中位数），没有旁白时是音乐（它 3 s 的短时响度，最低取整体响度下方 8 LU）。顺序是人声锚点 → 音乐 VMR → 音效分级 → 纵深 → 母带。各类音效的范围、所有 profile 共用的参数、`role` 的判法见 `tools/audio/README.md` 的"混音"。

| profile | 用于 | 锚点 | 人声高出音乐（VMR 目标，LU） |
|---|---|---|---|
| `explainer` | 01 原理讲解、06 论文 | 旁白 | 13 |
| `short` | 02 知识短视频 | 旁白 | 11.5 |
| `promo` | 03 发布片、05 数据故事、08 快剪 | 音乐（有旁白时是旁白） | 10 |
| `cartoon` | 07 手绘、角色短片 | 同 promo | 10 |
| `mv` | 04 MV | 音乐 | 6 |
| `swatch` | 风格样片（`render.sh`） | 音乐 | – |

```bash
A=projects/<p>/audio
# 旁白片：explainer / short；events= 让混音器自己摆音效（摆法和 sfx place 相同），每个事件才能单独分级
bin/vh mix $A/mix.wav profile=explainer voice=$A/voiceover.en.wav music=$A/music.wav \
           events=$A/events.json lib=$A/sfx timeline=$A/timeline.en.json music_db=-5 stems=$A/stems
# 没有旁白的片子：锚点是音乐；dur / fade 在混音里截到片长并淡出，超出片尾的长音效一起淡出
bin/vh mix $A/mix.wav profile=cartoon music=$A/music.wav events=$A/events.json lib=$A/sfx dur=12 fade=0.1 stems=$A/stems
bin/vh qa mix $A/stems --beats $A/music.beats.json   # 只看混音报告（词级时间取 timeline 里的 words，或 --words）
```

片尾的 `fade` 从 dur − fade 开始压所有总线，最后一帧上的音效也会被压下去：showcase 01 用 0.1 s 时，11.955 s 光圈合拢的那一声被压低了 7–12 dB，改成 0.04 s 才保住它的起音。片尾有动作时，`fade` 要短于它离片尾的距离。

**混音报告**：`bin/vh qa mix <stems>`（或 `bin/vh qa … --stems` 输出的最后一段）逐句列出人声高出音乐多少、每个词有没有被盖住、每个音效相对锚点的响度。硬失败（退出码 1）是：有一句低于 profile 的硬下限；说话时 hero 音效超过它的上限；被盖住的词超过 profile 允许的比例；同一类音效的中位数偏出范围 3 LU 以上；timeline 有句子，人声 stem 却全是静音；一个 cue 对上了却听不见（只以"弱"通过，又被判 `BURIED`）。怎么读、怎么改见 `tools/audio/README.md`。`bin/vh mix` 报错退出时什么都不写，上一次的 `mix.wav` 还在，所以先看它的退出码；`bin/vh qa` 看到混音比事件表这些输入旧，会在报告开头和最后一行写 `STALE?`，只是警告，退出码不变。

**AAC 编码会抬高真峰值**：每个成片都要量编码后的文件（`ffmpeg -i final.mp4 -af ebur128=peak=true -f null -`），高于 −1.5 dBTP 就用更低的 `tp=` 重混。门禁是 WAV（`bin/vh qa mix.wav …`）；成片 mp4 再跑一次，cue 的问题只作警告（`tools/audio/README.md` 的"AAC 编码和 cue check"）。

### 歌曲（带人声演唱）

| 来源 | 做法 | 状态 |
|---|---|---|
| **Suno 等网页服务** | 用户生成、下载后放进 `audio/`；歌词逐句对齐走下面的"歌词对齐"一行；节拍用 `bin/vh beats` | ✅ 流程可用（Suno 没有官方公开 API，不接非官方封装） |
| **ElevenLabs Music**（云端） | 按提示词生成带人声的歌曲 | 接口位已留（`tools/audio/` 下加一个 provider） |
| **本地开源歌曲模型**（如 ACE-Step、YuE 一类） | 需要确认本机能跑（多数需要 GPU） | 接口位已留，没有测过，UNVERIFIED |
| **代码合成** | `bin/vh music` 只做器乐，不做人声 | ✅ |

## 让声音有表情、有节奏

声音"对"不等于声音"好"。用户对第一版配音的评价是：内容对了，但太僵硬，不活泼，没有节奏感。这一节讲三件事：怎么导演旁白、怎么让旁白卡拍、怎么让配乐和音效跟上画面的节奏。

### 1. 旁白要导演，不要念稿

- **两层指示**：
  - 整体语气写在 `bin/vh tts` 的第 5 个参数（`--instruct`）里；
  - 每一句再在 `[ ]` 里单独导演，写在 `@id` 后面。逐句指示只作用于这一句，不会进字幕。
- **怎么写指示**：
  - 写情绪、语速、重音、句尾走向、停顿，例如"像在跟朋友分享一个惊人的发现，语速偏快，'一句话'重读，尾音上扬成问句"；
  - 用"像在……"打比方，比"专业""自然"这种抽象词好用得多；
  - 同一段里相邻两句的语气要有落差：问句接答句，铺垫接爆点，快接慢。
- **标签**：`<short pause>`、`<long pause>`、`<breath>`、`<laugh>`、`<sigh>` 可以直接写进句子里。只有 `gemini` 会演出来，其他 provider 和字幕都会自动去掉（规则见 `tools/audio/README.md`）。中文稿里也写英文标签，官方说这样效果最好。标签只管某一刻的动作（停顿、呼吸、笑），持续的语气写在 `[ ]` 里。
- **给 gemini 的指示要短**：一句话讲清情绪和节奏就够了。年龄、性别、口音属于音色，不要写进指示；长段的人设和导演笔记容易让音色漂移。
- **谁能演**：
  - `gemini` 表演力最好，整体和逐句指示都听；
  - 本地 `qwen` 的 0.6B 模型不接受指示，要换 1.7B 的 instruct 模型；
  - `say` 和 `edge` 只能念。
- **写法示例**（逐句导演，后两句用了下文的对拍写法）：

  ```text
  @hook [像在跟朋友分享一个惊人的发现，语速偏快，带点好奇，尾音上扬成问句，"一句话"重读] 一句话，能做出一支片子吗？ || One sentence. Can it make a film?
  @yes:downbeat [干脆利落地揭晓答案，短促有力，带一点笑意] 能！ || It can.
  @how [节奏明快、一气呵成，三个短句一个比一个有力] 它写代码，逐帧算，自己检查。 || It writes code, computes every frame, checks its own work.
  @end:downbeat [自信地收尾，语速放慢，最后四个字一字一顿] 你说，它做。 || You say it. It makes it.
  ```

**各类型的默认整体语气**（第 5 个参数的起点，按片子改）：

| 类型 | 整体语气 | 语速 |
|---|---|---|
| 02 知识科普短视频 | 像在跟朋友讲一个惊人的事实：好奇、有起伏，关键词重读，句尾不拖 | 偏快，句内每秒 4.5–5.5 个中文字 |
| 01 / 06 原理讲解、论文 | 耐心、清楚，像在白板前讲给聪明的学生听；在"为什么"之前停一下 | 中等，句内每秒 3.5–4.5 字 |
| 03 产品发布片 | 年轻、有感染力、自信，抑扬顿挫明显，不要播音腔；卖点句短促有力 | 偏快，跟着拍子走 |
| 04 MV 旁白、诗 | 低声、贴近麦克风，气声多，句间留白 | 慢 |
| 08 梗、快剪 | 夸张、戏剧化，节奏感强，包袱前停顿 | 快，包袱前 `<short pause>` |
| 纪录片、历史 | 平静、笃定、克制，句尾下沉 | 中慢 |

**语速的依据和用法**：表里是句内语速，不算句间停顿。普通话正常朗读、去掉 150 ms 以上的停顿后约 5.2 字/秒：七种语言的朗读语料里，汉语是 5.18 音节/秒，一个汉字一个音节（Pellegrino, Coupé & Marsico 2011，*Language* 87(3)，[doi:10.1353/lan.2011.0057](https://doi.org/10.1353/lan.2011.0057)）。电话闲聊按总时长算是每分钟 228–247 字，约 3.8–4.1 字/秒（Yuan, Liberman & Cieri 2006，Interspeech，[doi:10.21437/interspeech.2006-204](https://doi.org/10.21437/interspeech.2006-204)）。知识科普的 4.5–5.5 围着正常朗读，原理讲解慢一档。倒推稿子字数时乘 0.85，留出句间停顿【综合】：45 s 的知识短视频约 170–210 字，3 分钟的讲解约 540–690 字。TTS 的实际语速看音色：本节第 4 小节比较 `duck_ratio` 用的那段测试旁白（0.25 s 间距，本地 Qwen3-TTS 0.6B 的 Serena，7 句 107 字）句内约 4.1 字/秒。所以字数只用来起稿，时长以 `timeline.json` 的实测为准（硬规则 2）。

**要做 A/B**：`studio` 档位下，同一段旁白至少试两种导演方向，把两版都给人听。实测对比见本节开头：同样三句话，只给一个"纪录片旁白"的整体语气时听起来平；逐句导演、再卡上拍之后，才有起伏和节奏。

### 2. 旁白卡拍（动效类必做）

叙事类、讲解类的旁白按语义断句就行。**动效、发布片、MV、梗这几类，旁白要骑在音乐上**。

- **参数**：`bin/vh tts projects/<p> … --beats projects/<p>/audio/music.beats.json`（路径相对运行命令的目录，和其他参数一样），每一句都从下一个拍点开始，而不是固定隔 0.25 s。节拍表里没有 `--snap` 要的那种网格（比如只有 `downbeats`，却按默认的 `beat` 对）会直接报错；旁白比配乐长、网格用完以后，后面的句子按 `--gap` 排，并给一次警告。
  - `--snap beat|half|downbeat` 选网格：拍、半拍或小节头；
  - `--lead` 设第一句最早从哪里开始；
  - 单独一句可以用 `@id:downbeat` 指定自己的网格，例如让答案那一句落在 drop 上。
- **流程**：
  1. 先写配乐骨架（`score.json`）；
  2. 旁白对拍；
  3. 看 `timeline.json` 里每句落在哪一拍；关键句没落在小节头或 drop 上，就回头改配乐的段落长度。比如前奏从 1 小节改成 2 小节，答案就正好落在鼓点进来那一下；
  4. 最后画面按 timeline 和节拍表做。
- **实测**：上面那段旁白对 120 BPM 的配乐，"能！"落在 4.00 s 的 drop，"你说，它做"落在 10.00 s 的小节头，每句起点误差为 0。

### 3. 配乐和音效跟上画面的节奏

- **画面落拍**：每个出场、转场、切镜都落在拍或半拍上；关键揭示落在小节头或 drop 上；小动作（字逐个出现、图标弹出）落在 8 分或 16 分音符上。画面代码和配乐共用一个 `bar(k, beat)` 函数，不手写秒数（见 `playbook/08`）。
- **帧对齐的速度**：选让一拍正好是整数帧的 BPM，这样所有细分都落在整帧上。
  - 30 fps：90（20 帧/拍）、100（18）、112.5（16）、120（15）、150（12）、180（10）；
  - 24 fps：96（15）、120（12）、144（10）、160（9）、180（8）。
- **按类型的节奏密度**：

  | 类型 | 速度 | 律动 | 音效密度 |
  |---|---|---|---|
  | 动效 / UI 演示、发布片 | 110–128 | 四拍律动，副拍 hats，推进感 | 每个动作一个，每秒 ≤ 6 |
  | 梗、快剪 | 128–150 | 硬切，重拍重音 | 每刀一个 |
  | 知识科普短视频 | 90–112 | 轻律动，不抢旁白 | 只给关键揭示 |
  | 讲解、论文 | 70–90，或只有 pad | 几乎不打拍 | 很少 |
  | MV | 跟歌 | 跟歌 | 跟歌词和重拍 |
- **每个画面动作都要有声音回应**：一个音效，或者配乐里的一个重音。画面动了、声音没反应，看起来就是"僵"。音效写进 `events.json`，落点和画面的动作时间取自同一个常量（样片框架里的 `FOLEY` 做法）。

### 4. 混音：有节奏的片子，音乐要一直在场

- **选 profile 就选了音乐的位置**（见上文"混音"）：讲解（`explainer`）让旁白高出音乐 13 LU，知识短视频（`short`）11.5 LU，句间停顿里音乐只回来一半，不会一顿一顿地呼吸；发布片（`promo`）和 MV（`mv`）以音乐为锚点，有旁白时也只让到 10 和 6 LU，音乐一直在场。
- **不用 profile 的默认链**：旁白为主的讲解用 `duck=voice`，默认 `duck_ratio=1.6`，音乐退到旁白后面，但句间不断；要音乐退得更狠，再往 3 调，并跑一次 `bin/vh qa`。动效类用 `music_db=-5 duck=voice duck_ratio=1.5–2`，或者干脆 `duck=off`，把音乐整体放低 6–8 dB。
- **实测**（默认链）：`duck_ratio=3` 加 `music_db=-3` 时，旁白在短语之间停顿约 100 ms，音乐来不及回来，qa 在 6.90 s 和 7.90 s 报了 50 ms 的掉音，听起来像顿了一下。改成 `music_db=-5 duck_ratio=1.6` 后，掉音和抽吸都是 0。2026-09-30 又用一段句间停顿 0.25 s 的旁白加配乐比了三档：`duck_ratio=6` 抽吸 3 处，3 有 2 处，1.6 为 0，听感也最顺，于是 1.6 成了默认值。

### 5. 声音也用提示词描述

先用一段话写清楚想要什么声音，再把它落到代码或外部服务上。写进 `STYLE.md` 的声音一节。

- **配乐简报**：
  - 写法：风格和参照、速度（从上面的帧对齐速度里选）、调式、配器、每段的能量曲线（例如"前奏 2 小节只有 pad 和琶音，第 3 小节 drop，全编制"）、必须落拍的时间点、哪里屏息；
  - 翻译成 `score.json` 的 `sections`（`bars`、`layers`、`energy`、`riser`、`impact`、`fill`）。`layers` 的 lead、arp 是固定音型，适合打草稿；要旋律、篇章和起伏，用 `parts` 写，做法见 `11-composition.md`；
  - 同一段简报也能直接用作 Suno 或 ElevenLabs Music 的提示词。
- **音效简报**：每个动作写一句"什么东西、什么材质、多大、多远"，例如"纸片被快速抽走，干、短、偏高频，近"；先从内置 21 个里找（`bin/vh sfx audition all` 一次听完），没有合适的再用 ElevenLabs Sound Effects 生成，或者在 `styles/_swatch/custom_sfx.py` 那样用代码合成。
- **旁白简报**：就是上面第 1 条的整体语气和逐句指示。

## 作曲：篇章、主题与起伏

要配乐有篇章、有能哼出来的主题、有起伏时，读 `11-composition.md`：从节拍表定章节、写主题和发展、用配器和音区做起伏，以及听不见时怎么用响度曲线检查。这些情况值得读：`studio` 档位；MV；介绍片、发布片；45 s 以上、靠音乐撑起结构的片子；人要亲自定主题或 BGM。只是给旁白铺一层底，本篇的"配乐"一节就够了。

## 选型

| 需求 | 方案 |
|---|---|
| 中文配音，本地 | `mlx-audio` 在 Apple Silicon 上跑 Qwen3-TTS（Apache-2.0，支持方言和声音设计）。要克隆声音用 CosyVoice 或 GPT-SoVITS。 |
| 配音，云端，追求稳定 | ElevenLabs 的 `/v1/text-to-speech/{voice_id}/with-timestamps` 直接返回字符级时间（`bin/vh tts` 拼成词级）；讲解旁白要表演力、或者要双人对话时，用 Gemini 3.8 Flash TTS（`bin/vh tts … gemini`，能用一句话导演语气，有免费档）；国内可选火山豆包、阿里百炼、MiniMax。 |
| 免费、先凑合用 | `edge-tts`（微软中文音色，非官方接口，随时可能失效） |
| 词级时间戳 | 已封装：`bin/vh tts … --align gemini`（Gemini 3.5 Transcribe，词级，0.1 s 步长，顺带对稿）。离线的话，中文用 FunASR（字级，带标点）；通用用 whisper.cpp（Mac 上有 Metal 加速）；已有讲稿或歌词、只需对齐时用 ctc-forced-aligner |
| 节拍 | librosa 或 beat_this（后者 downbeat 更准）。音乐平缓时，检测出来的 BPM 只是一个强加的节拍器，不能拿来硬切。 |
| 歌词对齐 | Demucs 分离人声 → Whisper 分块转写 → 用序列对齐（Needleman–Wunsch 或 difflib）把真实歌词对到转写结果上。functional-emotions-video 的 `analysis/` 目录有完整脚本。 |
| 音乐 | Suno 没有公开的自助 API（只有二手来源，UNVERIFIED）。常规做法是人在 Suno 上生成，再把文件交给 agent。需要能调用的接口时用 Eleven Music。 |
| 音效 | ElevenLabs Sound Effects API，或者本地音效库（记录每条的来源和许可）。 |

**许可证注意**：商用时避开 fish-speech、F5-TTS 的权重和 ChatTTS，它们是非商用许可。

## 统一的时间文件

【综合】所有引擎都从同一份 `audio/timeline.json` 读时间，避免各算各的：

```json
{
  "duration": 47.82,
  "bpm": 88, "offset": 0.21,
  "segments": [
    {"id": "s01", "start": 0.00, "end": 3.40, "text": "为什么卫星信号会变调？",
     "words": [{"w": "为什么", "start": 0.05, "end": 0.48}, {"w": "卫星", "start": 0.48, "end": 0.86}]},
    {"id": "s02", "start": 3.40, "end": 9.10, "text": "...", "cues": {"doppler": 5.72}}
  ],
  "beats": [0.21, 0.89, 1.57],
  "downbeats": [0.21, 2.94]
}
```

- `cues` 对应 `SCRIPT.md` 里的 `{cue}` 标记，用来在某个词出现的那一刻触发画面。
- `words` 由 `bin/vh tts … --align gemini`（或 elevenlabs）写入；对稿结果 `asr` 和对话里的 `speaker` 也在每个 segment 里。
- ClaudeAnimationBase 用 `src/config.js` 的 `bpm` 和 `offset`，`pulse()` 和 `beatN()` 会自动对齐节拍。
- Remotion 的做法是在 `calculateMetadata` 里读取音频时长来设置帧数；HyperFrames 的做法是 `sync-durations` 用实测时长覆盖估计值。

## 同步的五种模式

1. **音频先行**：先生成音频，按实测时长确定每个场景的帧数。
2. **按 cue 词触发**：旁白说到某个概念时，那个概念的画面正好出现。动画比旁白提前约 0.5s 开始，每句话说完后停约 1s。
3. **按拍落点**：切镜、重音动作、大字出现都落在拍点上，误差 ±1 帧；大的场景切换放在小节线上。
4. **混音**：有旁白的段落压低背景音乐，而且逐句压到目标 VMR，只挖人声需要的频段（`bin/vh mix … profile=`，见上文"混音"；HyperFrames 的 voiceover carve 也只压人声所在的频段）。响度只加一个整体增益：第一遍测量，第二遍加增益；只有增益会把真峰值推过上限时才接真峰值限幅器，最后实测输出，`bin/vh mix` 就是这样做的。单遍动态 loudnorm 会压扁配乐的动态，介绍片的 LRA 就是这样从 13.6 掉到 7.0 的。loudnorm 的 `linear=true` 也不可靠：增益会让真峰值超过 TP，或者 LRA 超过目标时，它会悄悄退回动态模式。
5. **在最终混音上做 cue check**：`bin/vh qa` 拿最终混音的 onset 去对照节拍表和音效事件表，逐条检查是否在 1 帧以内，同时扫描静音、掉音、抽吸和 click。只查配乐不够，混进音效以后，有的 cue 会被盖住，有的会和别的并成一个。门禁是 WAV；成片 mp4 再查一遍，cue 的问题只作警告。有旁白时加 `--voice voiceover.wav`（或 `--stems`，它带着人声 stem），人声下面设计好的压低就不会被算成抽吸；另外把成片重新转写一遍，和 cue 表对比时间差。四项扫描的做法和判定标准见 `02-verification.md` 的"音频 QA"一节。
6. **改画面时，配乐里同一事件的重音一起挪**【实测】：cue check 只查"那一刻有没有声音"，查不出配乐的重音还落在旧位置。介绍片 v5 几轮里卡片、片尾打字挪了时间，只挪了音效事件表，配乐里给同一事件写的重音（钢片琴、铃、打字声）留在原处，有的提前 0.75 s，有的落在静止画面上，人一听就觉得"音乐和画面不同步"。查法：渲一遍配乐拿到节拍表，把每个有名字的 hit（`label`）和同一画面事件的音效配对，偏差应当是 0；配不上的，要么挪重音，要么给它一个画面事件。

## 常用命令

手动做响度标准化、合成音轨的 ffmpeg 命令（`bin/vh mix` 和 `bin/vh mux` 已经内置），见 `tools/audio/README.md` 的最后一节。
