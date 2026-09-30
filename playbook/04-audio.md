# 04 音频

原则：**先有音频，再有时长。** 要先把音频变成时间表，agent 才能处理：旁白要有词级时间戳，音乐要有节拍网格，歌曲要有逐句歌词时间。

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
bin/vh music --example > projects/<p>/audio/score.json        # --example zh：编钟、古筝、笛子、太鼓的中国风起步谱
bin/vh music projects/<p>/audio/score.json projects/<p>/audio/music.wav     # + music.beats.json（段落、节拍、冲击点）
# 音效：内置库 + 按动作时间摆放（立体声，事件可带 pan、dist）
bin/vh sfx lib projects/<p>/audio/sfx
bin/vh sfx place projects/<p>/audio/events.json projects/<p>/audio/sfx.wav 45 --lib projects/<p>/audio/sfx
# 混音、成片 QA 与合成
bin/vh mix projects/<p>/audio/mix.wav voice=…/voiceover.zh.wav music=…/music.wav sfx=…/sfx.wav
bin/vh qa projects/<p>/audio/mix.wav projects/<p>/audio/music.beats.json projects/<p>/audio/events.json   # 静音、掉音、抽吸、click + cue check
bin/vh mux projects/<p>/out/final.mp4 projects/<p>/audio/mix.wav projects/<p>/out/final-av.mp4 \
           projects/<p>/audio/captions.zh.srt projects/<p>/audio/captions.en.srt   # 软字幕轨（可开关）
bin/vh beats <任意音乐文件>                          # 外来音乐的节拍 + hits、kick、snare 重音（librosa）
```

### 配音（`tts` / `captions`）

**旁白稿**：`audio/script.txt` 一行一句，一句对应一条字幕或一个 cue。
- 双语写成 `中文 || English`，`--lang` 决定念哪一边，两边都会进时间表；
- 只写一边的句子照原样念。进字幕时，含中日韩字符的算中文，不含的算英文，所以纯英文稿出的是 `captions.en.srt`。想让一句纯英文（比如品牌名）留在中文一侧，写成 `Claude Code ||`；只有标点的一句（`……`）跟着前面的单边句走；
- 可以加 `@id` 前缀，比如 `@hook 一句话，做出一支片子。 || One sentence in, one film out.`。
- 每句合成后，provider 自带的句首句尾静音（低于 −50 dBFS）会被裁掉，只留人声前 30 ms、后 80 ms，所以句间距离就是 `--gap`，按拍落点时人声也落在拍上。qwen 的英文音色 Ryan 每句开头有约 0.45 s 空白，edge 每句结尾有约 0.85 s，不裁的话节奏全被拖慢。阈值用 −50 而不用 −45：−45 会切掉 f、h 这类弱起音（最长 70 ms）。第一个词之前的呼吸声、含糊声高于 −50 dBFS，不算静音，裁不掉，要靠 `--align gemini` 的句首检查标出来。`--join` 时只裁整段的首尾，段内的停顿是表演的一部分。想保留原样，加 `--keep-edges`；
- 双人对话：先写一行 `@speakers A=Kore B=Puck`，之后每句在 `@id` 和 `[指示]` 后面写说话人，见下文"双人对话"。

按句合成，所以每句的起止时间都是**实测**的（`--join` 整段合成时除外，见下文）。

**同一份稿，中文和英文旁白长度不同**（实测一段 3 句的稿子：中文 9.3s，英文 10.8s）。所以双语成片要各自按 `timeline.<lang>.json` 排时间：
- 画面可以共用，但节奏按语言重排；
- 或者只出一种语言的旁白，配中英双语字幕。

| provider | 类型 | 需要什么 | 时间精度 | 状态 |
|---|---|---|---|---|
| `qwen`（默认） | **本地开源** Qwen3-TTS（Apache-2.0），mlx-audio 运行在 Apple Silicon 上。中文音色：Serena（温暖女声）、Vivian、Uncle_Fu、Dylan（京腔）、Eric（川话）；英文音色：Aiden（默认）、Ryan（语速慢，0.6B 模型用它时经常拖出几秒到几十秒的含糊声） | 首次运行下载约 2GB；换 1.7B 模型（`QWEN_TTS_MODEL`）后可以用 `--instruct` 控制语气 | 句级 | ✅ 已实测中英 |
| `say` | macOS 自带，离线，适合打草稿 | 无 | 句级 | ✅ 已实测 |
| `edge` | 微软免费在线音色 | 联网；非官方接口 | 句级 | ✅ 已实测英文 |
| `dashscope` | 阿里云百炼 Qwen3-TTS（`qwen3-tts-flash`），云端 | `DASHSCOPE_API_KEY` | 句级 | 接口已留，待实测 |
| `elevenlabs` | 高质量多语种配音 | `ELEVENLABS_API_KEY`、voice_id | **字符级** | 接口已留，待实测 |
| `gemini` / `gemini-lite` | Google Gemini 3.8 Flash TTS（2026-09-23 发布）/ Flash-Lite TTS，云端。表演力强，适合讲解旁白和双人对话。Flash 支持 130 种语言，Lite 支持 101 种，都含中文，语言按文本自动识别。`--voice` 用 30 个 studio 音色之一（默认 Kore，每个都能说所有支持的语言）、音色库 id 或自己设计的 `voice_…`（见下文"音色"）；`bin/vh tts` 的第 5 个参数（`--instruct`）用一句话描述语气，例如"平静、笃定的纪录片旁白"；稿子里可以直接写 `<short pause>`、`<breath>`、`<laugh>` 这类标签，只有 gemini 会演出来，其他 provider 和字幕都会自动去掉 | `GEMINI_API_KEY`（Google AI Studio）。有免费档，但免费档的内容可能被 Google 用来改进产品；付费价格见下文"费用" | 句级；加 `--align gemini` 后为词级 | ✅ 2026-09-30 实测中英（Kore / Charon）：一次通过，逗号处有自然停顿。双人对话、整段合成、设计音色同日实测 |

**已知问题**：默认的本地 Qwen3-TTS 0.6B 模型念英文短句时偶尔停不下来。实测 "One sentence in, a film out." 念完后又多出约 10 秒低电平的含糊声音，整句 12.6 s。所以每条配音都要查一遍：加 `--align gemini` 让机器查（见下一节），或者至少看一眼 `timeline.<lang>.json` 里的时长。被标出来的那句重跑，或者换 1.7B 模型、换 `gemini`。同一稿 Gemini 的四条都正常。

#### 词级时间和对稿检查（`--align gemini`）

`--align gemini` 对任何 provider 都能用：每句合成完，交给 Gemini 3.5 Transcribe（`gemini-3.5-transcribe`）转写一遍，拿回带时间戳的词，再和稿子逐字对齐。结果写进 timeline：
- `words`：`[{w, start, end}]`，字段和 elevenlabs 的一样，但文字用**稿子里的写法**（ASR 听成同音字也不影响字幕），时间用 ASR 的。中文基本是一字一个 word；
- `asr`：`{text, similarity, head, tail, flag?}`。`similarity` 是 ASR 文本和稿子的相似度（0–1，按汉字和英文单词比，忽略标点、大小写和他/她/它这类同音字）。低于 `--min-sim`（默认 0.85），或者第一个词之前、最后一个词之后多出 1 s 以上的声音，就标上 `flag`，命令最后逐句列出来。

被标出来的句子会自动复查一次：用 `custom_vocabulary` 把识别往稿子上偏。词表只放稿子里对不上的那几处短语、稿中的英文术语和 `--vocab` 给的词，不拿整句当词表，免得把真念错的地方也"纠正"掉。API 不允许 `custom_vocabulary` 和词级时间戳同时用（实测返回 400），所以复查只拿文字。

实测（2026-09-30）：
- 一句中文、一句英文（Gemini 合成，约 4 s）：相似度都是 1.00，每次转写 3.3–3.7 s；
- 模拟 Qwen 停不下来：同一句后面接 8 s 低音量的无关絮语，相似度掉到 0.47，并报"最后一个词之后还有 5.5 s"；接 8 s 近乎无声的底噪，文字全对（1.00），但报"最后一个词之后还有 8.2 s"。两种都抓到了；
- 双人对话里，ASR 会把 B 说话时 A 的一声"嗯"也转出来。这种插话按稿子里的 `|嗯|` 算，不扣分。

局限：时间戳的步长是 0.1 s（30 fps 下 3 帧）；数字可能被规范化（"二十六"转成"26"），相似度会降，但不算念错；每次调用有 3–7 s 延迟，逐句模式下 4 句并发。费用约 $0.005 / 分钟音频（付费档），免费档不收费。

**字幕用上词级时间**：timeline 里有 `words` 时，`bin/vh captions` 会在 `captions.json` 的每条里加上 `words`（绝对时间，引擎可以做逐字高亮、逐词弹出），并多写一个 `captions.<lang>.lines.srt`：一条字幕折成几行，就拆成几个 cue，每行在它的第一个字念出来时才出现。原来的 `captions.zh.srt` 等文件不变。

需要更细的强制对齐（音素级、离线）时，仍然可以用 mlx-audio 的 Qwen3-ForcedAligner、FunASR 或 whisper.cpp，这些没有封装。

#### 双人对话（gemini）

稿子开头写一行 `@speakers`，把说话人标签对到音色上；之后每句在 `@id` 和 `[指示]` 后面写 `标签:`（中英文冒号都行）：

```text
@speakers A=Kore B=Puck
@q1 A: [好奇] 你猜这支片子手写了几行代码？ || Guess how many lines of this film were written by hand?
@a1 B: [压低声音，卖个关子] 一行都没有。 |嗯？| 全是它自己写的。 || Not a single one. |huh?| It wrote all of them.
@q2 A: 真的假的！ || No way!
```

- 只有 `@speakers` 里声明过的标签才算说话人，普通旁白里的"注意："不受影响。英文一侧重复写的标签（`A: …`）会一并去掉；
- `|嗯？|` 是**对方**的插话（backchannel），写在当前说话人的句子里，竖线内侧不要留空格。它只在 gemini 对话里出声，字幕和其他 provider 都会去掉。只有写了 `@speakers` 的稿子才有插话，普通旁白里的 `|x|`（比如绝对值）原样保留；
- gemini 默认把一段对话（空行之间的连续句子）放进一个请求，用 `mode: "conversational"`，轮次衔接更自然。一个请求最多 2 个说话人，而且只能用库里的音色（30 个 studio 音色或 `voices list` 里的 id）。用了设计出来的 `voice_…`，或者超过 2 人时，自动改成一句一个请求，插话也随之去掉；
- 同一段里不能混着没有标签的旁白：旁白和对话之间空一行，分成不同的段；
- 用 `say` 等出草稿时，第 3 个参数写 `A=Tingting,B=Meijia`，覆盖 `@speakers` 里的音色。

实测（2026-09-30，Kore 和 Puck，上面这 3 句）：一个请求出 8.6 s，行边界靠词级时间切回每一句。对这段音频再做一次说话人分离，结果是 A 问、B 答，B 说话中间 A 插了一声"呃？"，A 再接一句，和稿子一致。英文对话里用音色库 id（`en-gb-storyteller-2`）和 studio 音色（Charon）搭配也能用。

#### 整段合成（`--join block|all`）

`--join block` 把空行之间的连续几句放进一个请求，`--join all` 把整份稿放进一个请求（gemini 单个请求最多 8,192 个输入 token）。句与句之间的语气是连着的，比一句一句拼起来自然。行边界从词级时间反推，所以会自动打开 `--align gemini`，`vo/<lang>/NN.wav` 是从整段音频里切出来的。其他 provider 也能用，只是把几句拼成一段文字去念。

代价是没法逐句控制：
- 某一句念得不好，只能整段重跑；
- 卡拍只作用在每段的开头（用这段第一句的 `@id:grid`），段内各句的间距由模型自己念出来，不能对到拍点上；
- 每句的 `[指示]` 仍然生效（gemini 把每句作为一个带 style 的 turn），但前后句的语气会互相带。

所以动效类、要卡拍的片子用默认的逐句合成；讲解、纪录片这类跟着语义走的旁白，可以整段合成。实测：两段共 3 句，第一段 2 句一次出 11.5 s，第二段单独放到网格上，三句相似度都是 1.00。

#### 音色（`bin/vh voices`）

- `bin/vh voices`：音色库概览。库里有 2,089 个音色，分布在 30 个语言区域，**没有标成中文的**。这不影响中文旁白：TTS 按文本识别语言，30 个 studio 音色都能说中文（Kore、Charon 已实测）；
- `bin/vh voices list en-GB --gender female --search narrator`：按语言前缀、性别、关键词筛选。`--search` 由服务端匹配名字和描述，所以 "Kore" 也会匹配到 "Korean"。标 `*` 的是 studio 音色；
- `bin/vh voices design "<1–2 句描述：年龄、性别、音色质感、口音、基本语气>" --lang zh-CN --gender male --out audio/voice.wav`：生成一个存在项目里的音色，打印 `voice_…` id，并把试听样音存到 `--out`。之后用 `bin/vh tts <p> gemini voice_…`。每个项目最多存 200 个音色，保存 1 年；不用了就 `bin/vh voices delete voice_…`。实测：一次设计 20.7 s，输入 256、输出 1,077 token（付费档约 $0.01），样音 33.6 s，说的是普通话；
- **音色复刻**（replication）：官方支持用 10–30 s 的参考录音复刻一个人的声音，但必须同时上传**同一位成年说话人**亲口念的同意声明（中文是"我是此声音的拥有者并授权谷歌使用此声音创建语音合成模型"），服务端会核对两段是不是同一个人。这一步涉及本人授权，本仓库没有封装。需要时在 Google AI Studio 里做，把得到的 `voice_…` id 交给 `bin/vh tts`。

#### Gemini 的费用、限制和标注

- **费用**（Standard 档，每百万 token）：Flash TTS 输入 $0.50、输出音频 $9（约 $0.00225 / 10 s）；Flash-Lite TTS 输入 $0.50、输出 $6（约 $0.0015 / 10 s）。这是 2026-12-31 之前的价格，**2027-01-01 起全部翻倍**（Flash $1 / $18，Lite $1 / $12）。Batch 和 Flex 档是一半。免费档不收费，但内容可能被用来改进 Google 的产品，有保密要求的稿子用付费档；
- 单个请求最多 8,192 个输入 token；
- **语气写短**：`--instruct` 和 `[指示]` 最后都进 `speech_metadata.style`。官方建议只写这一句的情境语气（"压低声音，卖个关子"）；年龄、性别、口音这类身份特征不要写进 style，要换音色，或者用 `voices design` 做一个。长篇的"角色设定""导演笔记"是音色漂移最常见的原因；
- **每段 Gemini 音频都带 SynthID 水印**（听不出来，但能检测到）。用了 Gemini 旁白的片子，在项目 `NOTES.md` 里写明"旁白为 AI 合成（Gemini TTS，含 SynthID 水印）"，发布时按平台要求标注。

**字幕的两种交付方式**：
- **烧进画面**：引擎读 `captions.json` 绘制，属于画面的一部分，同样必须是 t 的纯函数，样式按类型文档；
- **软字幕轨**：`bin/vh mux … captions.zh.srt captions.en.srt` 封装进 mp4，播放器或平台可以开关。

竖屏视频导出时用 `bin/vh captions <p> zh 11`，中文每行最多 11 字。

### 配乐（`music`）

来源优先级（借鉴自归藏 product-video skill 的做法）：
1. **用户给的曲子**，或用户有授权的曲库。按它的实际节拍重新对齐画面：`bin/vh beats`。
2. **本机确实能跑的音乐生成模型**：先确认权重已经下载、运行环境也装好，才算可用。接口位已留，见下文"歌曲"。
3. **代码原创作曲**：`bin/vh music`。编曲源码 `score.json` 跟着项目一起提交，段落（`sections`）按镜头边界排，音色和速度按片子的气质选。因为曲子是我们自己写的，节拍网格和冲击点是**精确的**，不用再做节拍检测。

**不要**下载来路不明的 BGM，不要扒参考视频的音乐，也不要把示例曲改个名字就当新配乐。

**免版税曲库**（未核实，使用前看条款）：Uppbeat 的免费档要求署名，而且每支视频要带一个单独的授权码；Pixabay 允许商用，不强制署名。不管用哪家，来源、授权方式和授权码都记进 NOTES 的素材台账。

**剪外来音乐时**，切点放在拍上，大的段落跳转放在小节线上（用 `bin/vh beats` 的 `beats`、`downbeats` 找点），接缝处做几毫秒的交叉淡化，例如 ffmpeg 的 `acrossfade=d=0.008`。在两个波形中间硬切，会留下一个 click。

外来音乐跑 `bin/vh beats` 时，除了 `bpm`、`offset`、`beats`、`downbeats`，还会得到三组带 `strength`（0–1，1 表示达到这首曲子前 10% 的强度）的重音：
- `hits`：所有 onset 的峰值，用来摆音效和画面上的重音；
- `kick`、`snare`：先用 librosa 的 HPSS 取出打击乐成分，再分频找 onset。40–150 Hz 当 kick；1.2–5 kHz 里频谱接近噪声的当 snare，hi-hat 和有音高的拨弦会被排除。加 `--no-drums` 跳过这一步。

精度按 ±1 帧设计（30 fps 下 33 ms）。在两段合成鼓 loop 上实测（击打时间已知，带 ±8 ms 的人为抖动，叠了 bass 和 pad）：
- kick：平均误差约 0 ms，最大 5–19 ms；
- snare：平均 +2.5 ms，最大 6 ms；
- hits：平均 +4 到 +7 ms，最大 23 ms。

三组都在 1 帧以内，没有漏检；误检的 strength 都不超过 0.12，滤掉 0.2 以下的就干净了。已知的局限有两条：
- 和 kick 同一音区的拨弦 bass 会被当成 kick（`bin/vh music --example` 的曲子上有 77 个这种误检），tom 也会；
- 切分节奏的曲子，BPM 可能报成一半（两段测试 loop 都是）。

所以硬切之前，先对照一下拍子。

`score.json` 的写法见 `bin/vh music --example`：
- 顶层：`bpm`、`key`、`mode`；可选 `meters`，例如 `{"11": 6}` 让整首的第 11 小节（从 1 数）变成 6/4，其余默认 4/4；
- `sections[]`：`bars`、`chords`（罗马数字）、`layers`（kick clap hats bass pad arp lead，以及 bell zheng dizi taiko）、`energy`（0–1）；
- 段落的特殊效果：`riser`（上升音推向下一段）、`impact`（段首冲击）、`fill`（最后一拍留白）、`bend`（古筝每两小节收在一个按弦上滑的音上）。

输出的 `music.beats.json` 包含 `sections`、`beats`、`downbeats`、`hits`，引擎直接读它来切镜和打点。写了 `meters` 时还会多一个 `bars` 数组，每项是 `[小节号, 起点秒数, 本小节拍数]`，画面用同一个 `bar(k)` 取小节位置。加拍时要让配乐和画面一起改：介绍片第 11 小节就是这样多停了 2 拍，其他秒数一个都不用手改。

**中国风的四种音色**是为中国题材加的，用法和其他层一样写进 `layers`：
- `bell`：类编钟。泛音不成谐波（含一个高小三度的"侧鼓音"），带慢拍频，余音很长。每小节强拍敲一下，能量高时小节中间再敲一个高音。
- `zheng`：古筝，用 Karplus–Strong 拨弦，弹八分音符的五声音型（能量低于 0.5 时只弹四分）。段落加 `"bend": true` 后，每两小节的最后一拍换成按弦上滑：拨弦后 0.12 s 开始滑上一个五声音级，再带一点揉弦。
- `dizi`：笛子。正弦加三角波，带通噪声做气声（比乐音低约 18 dB），颤音延迟进入，长音前加倚音，两小节一句。
- `taiko`：大鼓。音高下滑的正弦加鼓皮噪声。每两拍一个重击，能量高时加八分音符的接鼓；带 `riser` 的段落，最后两拍滚奏进下一段；`fill` 同样会空出最后一拍。

旋律类音色都走调式的五声音阶：`minor` 用羽调（1 ♭3 4 5 ♭7），`major` 用宫调（1 2 3 5 6）。四种音色共用一个单独的混响（RT60 约 2.8 s），不跟 kick 一起抽吸。每个音符用独立的种子流，所以加减一种音色不会改变其他层的声音。`bin/vh music --example zh` 是一份 D 羽调、84 BPM、约 60 s 的起步谱，两次渲染的 md5 相同，峰值 −1.0 dBFS。

**戏剧性的"停"不能做成数字静音。** 要停的时候：
- 保留一层底（sub 或 pad）；
- 把滤波往下收，撤掉鼓；
- 再用一个反向渐强（reverse swell）拉进下一个重拍。

介绍片 v2 有 4 处真静音，用户听到的是"卡顿"；v3 把这 4 处都改成这样的"屏息"。`bin/vh qa` 会把片中任何 ≥ 20 ms 的数字静音判为问题。

### 音效（`sfx`）

- **音效是独立的事件层**，和音乐分开：`audio/events.json` 写成 `[{t, sfx, gain_db, pan, dist}]`，后两项可选。`sfx place` 输出 48 kHz 立体声。
- **`t` 是"落点"**：内置音效各自带落点偏移（例如 whoosh 的峰值、riser 的顶点），摆放时会自动对齐，保证声音峰值和动作在同一帧。
- **`pan`**（−1 最左，0 居中，1 最右）用等功率声像律，并且按"居中 = 原电平"归一。不写 pan 的事件和以前的单声道摆放逐采样相同。pan = ±1 时，那一侧 +3 dB，总功率不变，所以大声的音效打到最边上时注意削波（工具会提示削波的采样数）。
- **`dist`**（≥ 1，单位是参考距离，1 = 原样）：电平乘 1/dist，距离每翻一倍 −6 dB；再加一个平缓的一阶低通，截止频率 16 kHz / dist，最低 1 kHz。低通带来的延迟不到 0.2 ms，落点不受影响。声速延迟没有加，因为 `t` 本来就是"该听到的时刻"；要做"先见闪光、后闻炮声"，自己把 `距离米数 / 343` 加到 `t` 上。
- **pan 从画面上算，不要凭感觉写。** 取发声物体在那一刻的屏幕 x：`pan = 2·x / 画面宽度 − 1`，再乘 0.7–0.8 收一点，全左全右在耳机里很刺。3D 场景用相机坐标：`pan = v·right / |v|`，其中 v 是声源到相机的向量；距离也从同一个 v 来。镜头在动时，同一个声源在不同时刻的左右位置也不同。Austerlitz 那支片子的音效就是这样从场景事件里算出声像和距离的，见 `cases/opus55-gallery.md` 第 6 节。
- **来源顺序**：先用有授权的录音素材（在 NOTES 的素材台账里记下来源和许可）；缺的类别再用内置库补。自己的立体声素材会先折成单声道，当作一个点声源来摆。内置库有 15 个代码合成音效：click、tick、pop、toggle、typing、whoosh、swish_rev、riser、impact、boom、ding、success、error、glitch、shutter，都是 MIT 原创，可以复现。
- **混音**：`bin/vh mix` 默认让音乐在人声出现时自动让位（有 voice 总线时是 `duck=voice`，没有时是 `duck=off`）。要让关键的叮咚、确认、转场声也压一下音乐，显式写 `duck=on`，同时把 `duck_ratio` 降到 2–3。混音保留立体声，音效总线上的声像会原样保留下来。响度只加一个整体增益：第一遍测量，第二遍加上"目标 − 实测"的增益；只有这个增益会把真峰值推过上限时，才在后面接一个 4 倍过采样的真峰值限幅器。最后再测一遍写出的文件，命令如实报告用的是 `static gain` 还是 `static gain + true-peak limiter (N peaks)`，并打印实测的响度和真峰值。这样电影配乐的动态范围（LRA）不会被压扁；介绍片用单遍处理时，LRA 从 13.6 被压到了 7.0。限幅器报了很多个 peak，说明音效或人声的峰值太高，先把 `sfx_db` 调低，不要靠限幅器硬压。
- **不要让每个音效都去压音乐。** 介绍片 v2 把 74 个音效全接进了 ducker，ratio 是 6，配乐跟着每个音效一抽一抽。所以默认只让人声压音乐（`duck=voice`），没有人声时不压（`duck=off`）；真要用 `duck=on`，把 `duck_ratio` 降到 2–3。`bin/vh qa` 的抽吸一项专门查这种问题。

### 歌曲（带人声演唱）

| 来源 | 做法 | 状态 |
|---|---|---|
| **Suno 等网页服务** | 用户生成、下载后放进 `audio/`；歌词逐句对齐走下面的"歌词对齐"一行；节拍用 `bin/vh beats` | ✅ 流程可用（Suno 没有官方公开 API，不接非官方封装） |
| **ElevenLabs Music**（云端） | 按提示词生成带人声的歌曲 | 接口位已留（`tools/audio/` 下加一个 provider） |
| **本地开源歌曲模型**（如 ACE-Step、YuE 一类） | 需要确认本机能跑（多数需要 GPU） | 接口位已留，没有测过，UNVERIFIED |
| **代码合成** | `bin/vh music` 只做器乐，不做人声 | ✅ |

### 已知局限

下面这些已经测出来了，但还没有修。用工具的结果时，要把它们考虑进去：
- **`qa` 的抽吸检查会漏掉又长又浅的凹陷**：约 300 ms、−8 dB 的凹陷占了 600 ms 中位数窗口的一半，查不出来，只能靠掉音检查（−12 dB）兜底。
- **`qa` 的 cue check 按全片最响的 onset 归一化**：别处一个特别大的 onset，会让很弱的 cue 被判成 OFF。
- **`qa` 的 click 只是警告，不算失败**：机器分不清设计好的尖锐起音和真故障，只豁免节拍表和事件表里的时间点。网格之外的设计性起音也会被列出来，比如十六分音符 ostinato 的音头、typing 连击、glitch 音效内部的门控。工具按倍数列出最严重的 10 处，要人耳逐个复听。门槛是局部电平的 15 倍：埋入测试里，6 个 0.37 幅度的 click 全部抓到，包括 riser 噪声下面那 2 个（17 倍、20 倍）；更深地埋在噪声里的 click 仍然可能漏掉。
- **`beats` 的 BPM 在切分节奏上可能报成一半**：两段测试 loop 分别报成了 49.7（实际 100）和 63.0（实际 127）。
- **两个内置音效的落点不在能量峰上**：whoosh 的能量峰在落点后约 34 ms（约 1 帧）；swish_rev 的落点是声音的结尾，能量峰在落点前约 280 ms。

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
- **标签**：`<short pause>`、`<long pause>`、`<breath>`、`<laugh>`、`<sigh>` 可以直接写进句子里。只有 `gemini` 会演出来；其他 provider 和字幕都会自动去掉。去掉的规则：这 5 个和 `<cough>` 一律去掉；别的 `<词>` 只要不是两边都紧贴字母或数字，也当标签去掉，所以 `x<y and y>z` 这类式子会原样保留。中文稿里也写英文标签，官方说这样效果最好。标签只管某一刻的动作（停顿、呼吸、笑），持续的语气写在 `[ ]` 里。
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
| 02 知识科普短视频 | 像在跟朋友讲一个惊人的事实：好奇、有起伏，关键词重读，句尾不拖 | 偏快，每秒 4.5–5.5 个中文字 |
| 01 / 06 原理讲解、论文 | 耐心、清楚，像在白板前讲给聪明的学生听；在"为什么"之前停一下 | 中等，每秒 3.5–4.5 字 |
| 03 产品发布片 | 年轻、有感染力、自信，抑扬顿挫明显，不要播音腔；卖点句短促有力 | 偏快，跟着拍子走 |
| 04 MV 旁白、诗 | 低声、贴近麦克风，气声多，句间留白 | 慢 |
| 08 梗、快剪 | 夸张、戏剧化，节奏感强，包袱前停顿 | 快，包袱前 `<short pause>` |
| 纪录片、历史 | 平静、笃定、克制，句尾下沉 | 中慢 |

**要做 A/B**：`studio` 档位下，同一段旁白至少试两种导演方向，把两版都给人听。实测对比见本节开头：同样三句话，只给一个"纪录片旁白"的整体语气时听起来平；逐句导演、再卡上拍之后，才有起伏和节奏。

### 2. 旁白卡拍（动效类必做）

叙事类、讲解类的旁白按语义断句就行。**动效、发布片、MV、梗这几类，旁白要骑在音乐上**。

- **参数**：`bin/vh tts … --beats audio/music.beats.json`，每一句都从下一个拍点开始，而不是固定隔 0.25 s。
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

- **旁白为主的讲解**：`duck=voice`，默认 `duck_ratio=1.6`，音乐退到旁白后面，但句间不断。要音乐退得更狠，再往 3 调，并跑一次 `bin/vh qa`。
- **动效类**：音乐是节奏的来源，只能轻轻让位。用 `music_db=-5 duck=voice duck_ratio=1.5–2`，或者干脆 `duck=off`，把音乐整体放低 6–8 dB。
- **实测**：`duck_ratio=3` 加 `music_db=-3` 时，旁白在短语之间停顿约 100 ms，音乐来不及回来，qa 在 6.90 s 和 7.90 s 报了 50 ms 的掉音，听起来像顿了一下。改成 `music_db=-5 duck_ratio=1.6` 后，掉音和抽吸都是 0。2026-09-30 又用一段句间停顿 0.25 s 的旁白加配乐比了三档：`duck_ratio=6` 抽吸 3 处，3 有 2 处，1.6 为 0，听感也最顺，于是 1.6 成了默认值。

### 5. 声音也用提示词描述

先用一段话写清楚想要什么声音，再把它落到代码或外部服务上。写进 `STYLE.md` 的声音一节。

- **配乐简报**：
  - 写法：风格和参照、速度（从上面的帧对齐速度里选）、调式、配器、每段的能量曲线（例如"前奏 2 小节只有 pad 和琶音，第 3 小节 drop，全编制"）、必须落拍的时间点、哪里屏息；
  - 翻译成 `score.json` 的 `sections`（`bars`、`layers`、`energy`、`riser`、`impact`、`fill`）；
  - 同一段简报也能直接用作 Suno 或 ElevenLabs Music 的提示词。
- **音效简报**：每个动作写一句"什么东西、什么材质、多大、多远"，例如"纸片被快速抽走，干、短、偏高频，近"；先从内置 15 个里找，没有合适的再用 ElevenLabs Sound Effects 生成，或者在 `styles/_swatch/custom_sfx.py` 那样用代码合成。
- **旁白简报**：就是上面第 1 条的整体语气和逐句指示。

## 选型

| 需求 | 方案 |
|---|---|
| 中文配音，本地 | `mlx-audio` 在 Apple Silicon 上跑 Qwen3-TTS（Apache-2.0，支持方言和声音设计）。要克隆声音用 CosyVoice 或 GPT-SoVITS。 |
| 配音，云端，追求稳定 | ElevenLabs 的 `/v1/text-to-speech/{voice_id}/with-timestamps` 直接返回字符级时间；讲解旁白要表演力、或者要双人对话时，用 Gemini 3.8 Flash TTS（`bin/vh tts … gemini`，能用一句话导演语气，有免费档）；国内可选火山豆包、阿里百炼、MiniMax。 |
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
4. **混音**：有旁白的段落压低背景音乐（HyperFrames 的 voiceover carve 只压人声所在的频段）。响度只加一个整体增益：第一遍测量，第二遍加增益；只有增益会把真峰值推过上限时才接真峰值限幅器，最后实测输出，`bin/vh mix` 就是这样做的。单遍动态 loudnorm 会压扁配乐的动态，介绍片的 LRA 就是这样从 13.6 掉到 7.0 的。loudnorm 的 `linear=true` 也不可靠：增益会让真峰值超过 TP，或者 LRA 超过目标时，它会悄悄退回动态模式。
5. **在最终混音上做 cue check**：`bin/vh qa` 拿最终混音的 onset 去对照节拍表和音效事件表，逐条检查是否在 1 帧以内，同时扫描静音、掉音、抽吸和 click。只查配乐不够，混进音效以后，有的 cue 会被盖住，有的会和别的并成一个。有旁白时加 `--voice voiceover.wav`，人声下面设计好的压低就不会被算成抽吸；另外把成片重新转写一遍，和 cue 表对比时间差。四项扫描的做法和判定标准见 `02-verification.md` 的"音频 QA"一节。

## 常用命令（示例，按项目调整）

```bash
# 本地中文 TTS（安装：uv tool install mlx-audio 或在项目 venv 里 uv add mlx-audio；模型名以 mlx-audio README 为准）
# 词级时间戳：whisper.cpp（brew install whisper-cpp）或 FunASR（uv add funasr）
# 响度标准化到 -14 LUFS（短视频平台常用），只加一个整体增益，bin/vh mix 已经内置；手动做时：
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json -f null -   # 第 1 遍：记下 input_i 和 input_tp
ffmpeg -i mix.wav -af volume=<G>dB mix_norm.wav                                   # 第 2 遍：G = −14 − input_i；input_tp + G ≤ −1.5 时到此为止
ffmpeg -i mix.wav -af "volume=<G>dB,aresample=192000,alimiter=limit=0.84:level=false:latency=true,aresample=48000" mix_norm.wav   # 否则加真峰值限幅（0.84 ≈ −1.5 dBFS）
# 再用第 1 遍的命令测 mix_norm.wav：限幅会吃掉一点响度（把 G 补回去），回到 48 kHz 会让真峰值高出约 0.2 dB（把 limit 再降一点）
# 视频与音轨合成：先出无声成片，再用 bin/vh mux 把音轨补齐或截到视频的精确长度（-shortest 按 AAC 帧截断，会吃掉最后 2 帧）
ffmpeg -framerate 30 -i out/frames/f%05d.jpg -c:v libx264 -crf 17 -pix_fmt yuv420p out/final.mp4
bin/vh mux out/final.mp4 audio/mix.wav out/final-av.mp4
```

mlx-audio 和 FunASR 的具体调用方式以各自 README 为准，第一次用时读一遍再写脚本，并把可用的命令记进项目的 `LESSONS.md`。
