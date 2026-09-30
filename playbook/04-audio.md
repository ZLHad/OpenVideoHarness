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
bin/vh music --example > projects/<p>/audio/score.json        # --example zh：编钟、古筝、笛子、太鼓的中国风起步谱；--example list：全部起步谱
bin/vh music --instruments                                    # 乐器声部（parts）的全部乐器和伴奏型，一行一个
bin/vh music projects/<p>/audio/score.json projects/<p>/audio/music.wav     # + music.beats.json（段落、节拍、冲击点）
# 音效：内置库 + 按动作时间摆放（立体声，事件可带 pan、dist）
bin/vh sfx lib projects/<p>/audio/sfx
bin/vh sfx place projects/<p>/audio/events.json projects/<p>/audio/sfx.wav 45 --lib projects/<p>/audio/sfx
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
- 每句合成后，provider 自带的句首句尾静音（低于 −50 dBFS）会被裁掉，只留人声前 30 ms、后 80 ms，所以句间距离就是 `--gap`，按拍落点时人声也落在拍上。qwen 的英文音色 Ryan 每句开头有约 0.45 s 空白，edge 每句结尾有约 0.85 s，不裁的话节奏全被拖慢。阈值用 −50 而不用 −45：−45 会切掉 f、h 这类弱起音（最长 70 ms）。一个响的 10 ms 窗口只有在相邻窗口也响时才算人声，所以落在单个窗口之内的 click、pop 不会让裁剪停在它那里（跨两个窗口的短促爆发仍然算），句首句尾都这样处理。第一个词之前的呼吸声、含糊声高于 −50 dBFS，不算静音，裁不掉，要靠 `--align gemini` 的句首检查标出来。`--join` 时只裁整段的首尾，段内的停顿是表演的一部分。想保留原样，加 `--keep-edges`；
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
| `elevenlabs` | 高质量多语种配音 | `ELEVENLABS_API_KEY`、voice_id | **词级**（接口给字符级，`bin/vh tts` 拼成词） | 接口已留，待实测 |
| `gemini` / `gemini-lite` | Google Gemini 3.8 Flash TTS（2026-09-23 发布）/ Flash-Lite TTS，云端。表演力强，适合讲解旁白和双人对话。Flash 支持 130 种语言，Lite 支持 101 种，都含中文，语言按文本自动识别。`--voice` 用 30 个 studio 音色之一（默认 Kore，每个都能说所有支持的语言）、音色库 id 或自己设计的 `voice_…`（见下文"音色"）；`bin/vh tts` 的第 5 个参数（`--instruct`）用一句话描述语气，例如"平静、笃定的纪录片旁白"；稿子里可以直接写 `<short pause>`、`<breath>`、`<laugh>` 这类标签，只有 gemini 会演出来，其他 provider 和字幕都会自动去掉 | `GEMINI_API_KEY`（Google AI Studio）。有免费档，但免费档的内容可能被 Google 用来改进产品；付费价格见下文"费用" | 句级；加 `--align gemini` 后为词级 | ✅ `gemini`：2026-09-30 实测中英（Kore / Charon），一次通过，逗号处有自然停顿；双人对话、整段合成、设计音色同日实测。`gemini-lite` 走同一条代码路径（只换模型 id），没有单独实测 |

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

局限：时间戳的步长是 0.1 s（30 fps 下 3 帧）；数字可能被规范化（"二十六"转成"26"），相似度会降，但不算念错；每次调用有 3–7 s 延迟，逐句模式下 4 句并发。费用约 $0.005 / 分钟音频（付费档），免费档不收费。Tier 1 每分钟只能转写 10 次，超过 10 句（算上复查）时会碰到 429：这时按接口给的时间等（通常不到 1 分钟）再重试，12 句实测 155 s 跑完。接口要求等 90 s 以上的是日配额用完了，会直接报错。转写失败到底（日配额、断网、某个文件坏了）也不丢配音：`voiceover.<lang>.wav` 和 timeline 在合成后就先写好，出错的句子保留实测时长、`asr` 里记 `error`，命令以非 0 退出；修好原因后用**同一条命令**加 `--resume` 接着跑：只补合成缺的文件（合成中途失败也一样），转写成功过的句子不再重转（结果存在 `vo/<lang>/*.asr.json`），其余重做；`--join` 时整段音频留在 `vo/<lang>/_blockNN.wav`，在那之前它的几句共用整段的起止。那次运行的稿子、provider、音色、语气指示（`--instruct`）和 `--join` 方式记录在 `vo/<lang>/_run.json` 里，`--resume` 要求它们一样，改了就拒绝并指出改了什么（对拍、间距这些时间参数可以改）。不带 `--align` 的普通合成中途失败，也用同一条命令加 `--resume` 接着合成；合成好的普通配音之后再加 `--align gemini --resume`，只做转写，不再合成。key 在合成前就检查。

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
- 顶层：`bpm`、`key`、`mode`；可选 `meters`，例如 `{"11": 6}` 让整首的第 11 小节（从 1 数）变成 6/4，其余默认 4/4；可选 `beats_per_bar`，改整首的默认拍数，写 3 就是三拍子；
- `sections[]`：`bars`、`chords`（罗马数字）、`layers`（kick clap hats bass pad arp lead，以及 bell zheng dizi taiko）、`energy`（0–1）；
- 段落的特殊效果：`riser`（上升音推向下一段；写成 `{"gain_db": -6}`，或在 `true` 旁边加 `"riser_db": -6`，可以把它调低，免得盖住旁白或画面上的重音）、`impact`（段首冲击）、`fill`（最后一拍留白）、`bend`（古筝每两小节收在一个按弦上滑的音上）；`stop`（段内停顿，只作用于 parts）；
- `parts[]`：乐器声部；`motifs`：一次写好、到处调用的动机；还有 `stereo`、`space`、`swing`、`lofi` 等总线设置。都见下文"乐器声部"。

输出的 `music.beats.json` 包含 `sections`、`beats`、`downbeats`、`hits`，引擎直接读它来切镜和打点。写了 `meters` 时还会多一个 `bars` 数组，每项是 `[小节号, 起点秒数, 本小节拍数]`，画面用同一个 `bar(k)` 取小节位置。加拍时要让配乐和画面一起改：介绍片第 11 小节就是这样多停了 2 拍，其他秒数一个都不用手改。

**中国风的四种音色**是为中国题材加的，用法和其他层一样写进 `layers`：
- `bell`：类编钟。泛音不成谐波（含一个高小三度的"侧鼓音"），带慢拍频，余音很长。每小节强拍敲一下，能量高时小节中间再敲一个高音。
- `zheng`：古筝，用 Karplus–Strong 拨弦，弹八分音符的五声音型（能量低于 0.5 时只弹四分）。段落加 `"bend": true` 后，每两小节的最后一拍换成按弦上滑：拨弦后 0.12 s 开始滑上一个五声音级，再带一点揉弦。
- `dizi`：笛子。正弦加三角波，带通噪声做气声（比乐音低约 18 dB），颤音延迟进入，长音前加倚音，两小节一句。
- `taiko`：大鼓。音高下滑的正弦加鼓皮噪声。每两拍一个重击，能量高时加八分音符的接鼓；带 `riser` 的段落，最后两拍滚奏进下一段；`fill` 同样会空出最后一拍。

旋律类音色都走调式的五声音阶：`minor` 用羽调（1 ♭3 4 5 ♭7），`major` 用宫调（1 2 3 5 6）。其他调式（dorian、mixolydian 等）里，layers 和 parts 用同一套和弦根音；调式里有小三度就用羽调，否则用宫调。四种音色共用一个单独的混响（RT60 约 2.8 s），不跟 kick 一起抽吸。每个音符用独立的种子流，所以加减一种音色不会改变其他层的声音。`bin/vh music --example zh` 是一份 D 羽调、84 BPM、约 60 s 的起步谱，两次渲染的 md5 相同，峰值 −1.0 dBFS。

**乐器声部（`parts`）**：`layers` 只有一套合成音色，所以不同风格的配乐听起来都差不多。要真的换一种声音，就在 score 里加 `parts`：每个声部是一件乐器，按一个节奏型演奏，和 `layers` 一起渲染。只写 `layers` 的旧谱子和以前逐字节相同。`bin/vh music --instruments` 列出全部乐器和伴奏型，每个一行，带默认参数；`--example list` 列出起步谱：jazz、waltz、chip、lofi、guqin、trap。

- **乐器**（纯代码合成，不用采样，详见 `tools/audio/instruments.py`）：
  - 键盘：`piano`（`tone: felt` 是柔和的毡锤钢琴，`pedal` 延音）、`epiano`（Rhodes）、`harpsichord`、`celesta`、`musicbox`、`glockenspiel`、`toypiano`、`organ`（拉杆风琴，`tone: pipe` 是管风琴）；
  - 敲击旋律：`marimba`、`xylophone`、`vibraphone`（带电机颤音）；
  - 拨弦：`nylon`、`ukulele`、`harp`、`pizzicato`、`upright`（走路贝斯用的低音提琴）、`pipa`、`guqin`（滑音、吟猱、泛音；泛音和同音高、同力度的拨弦一样响）、`balalaika`、`cimbalom`。`celesta`、`musicbox`、`glockenspiel`、`toypiano`、`marimba`、`cimbalom`、`guqin` 都接受 `damp`：音符结束时止住余音；
  - 物理建模拨弦（可选，和上面的音色并存，只把 `inst` 换个名字就能 A/B）：`guqin_pm` `pipa_pm` `harp_pm` `nylon_pm` `ukulele_pm` `upright_pm` `balalaika_pm` `cimbalom_pm`，另有新乐器 `guitar`（钢弦民谣吉他）、`koto`（箏）、`shamisen`（三味线，`buzz` 0–1 是 sawari 蜂鸣，拨得越重越响）、`banjo`、`kalimba`、`musicbox_pm`。弦是数字波导，卡林巴和八音盒是悬臂梁的模态合成：一个音里音高可以连续滑动，高次泛音先衰减，重拨时音头略高再回落，琴体是一组共鸣模态。弦的奏法写在 params 或音符的第 5 格：`slide`、`bend`（半音，±36）、`vib`（颤音：音分，或 `[Hz, 音分, 延迟秒]`）、`yin`、`nao`、`harm`（节点泛音：`true` 或第几泛音 2–8，和同音高、同力度的拨弦一样响）、`trem`（轮指：同一根弦反复拨，写 Hz（最多 40）或 `true`）、`pos`（拨弦点 0.03–0.5）、`bright`（0–1）、`decay`（余韵倍数 0.02–20）、`ring`、`damp`、`mute`，超出范围的值会被夹到范围内；声部的 `tremolo` 照旧可用。`kalimba` 和 `musicbox_pm` 只认 `ring`、`damp`、`decay`。余韵最长渲染到各音色的上限（2.5–8 s，卡林巴和八音盒 5 s；`decay` 会把它拉长，最多 20 s），到上限还没衰减完的音在最后一秒淡出。每个音的峰值都一样；旧音色只校准了参考音，越往高音越弱，所以从旧音色换过来，默认八度的音量差不多（±5 dB），往高走会响出来，高三个八度时响 6–26 dB（cimbalom 26、balalaika 17、pipa 16、ukulele 15、upright 13），换完要重新听一下 `gain_db`；
  - 拉弦：`strings`（弦乐组，`marcato` 是短促有力的奏法）、`violin`、`fiddle`、`cello`、`banhu`。独奏乐器是单音的：间隔不到 40 ms 的音连成一句，会滑过去，有揉弦；要每个音都重新起音，写 `"retrigger": true`（放在 params、某一段的 params，或单个音的奏法里）；
  - 管乐：`flute`、`xiao`、`whistle`、`suona`、`sheng`；铜管 `brass`（`stab` 短促、`swell` 渐强、`mute` 弱音器），`braam`（《盗梦空间》式的低音铜管轰鸣）；
  - 合成器：`pulse`（芯片方波，`duty` 占空比，`chiparp` 快速琶音当和弦）、`triangle`（4-bit 三角波贝斯）、`sq_bass`、`sub808`（带滑音和失真；和独奏弦乐一样，紧挨着的音会连成滑音，要一下一下地打就写 `"retrigger": true`）、`seq`（`attack` 给音头一点起音，滤波开得很大时 qa 就不会把音头当成 click）、`cs80`、`drone`、`polysynth`；旧的 `layers` 音色也能当声部用：`saw_pad` `saw_lead` `bell` `zheng` `dizi` `taiko` 等；
  - 鼓和打击乐：`kick` `snare` `rim` `brush`（刷子，`o` 是扫）`ride` `hihat`、`bb_kick` `bb_snare`（boom-bap）、`trap_hat` `trap_snare` `clap` `gated`（合成波门限混响军鼓）、`cowbell` `shaker` `bongo` `conga` `woodblock`、`bangzi` `gong` `smallgong`（小锣，音高上扬）`cymbals`（铙钹）`danpigu`（单皮鼓）、`framedrum` `timpani` `clock` `metal` `noiseburst` `scratch`（搓碟）`noise` `chipkick`；`luogu` 直接读锣鼓经的字：仓 才 台 七 令 顷 冬 大 八。大锣默认从 240 Hz 往下滑，用 params 的 `daluo`（Hz）改音高，或者给声部写 `"pitch"`（例如 `"d1"`）让它跟着调走；小锣用 `xiaoluo`（Hz）；
  - 底噪：`vinyl`（黑胶噼啪）`tape`（磁带嘶声）`hum`（50/60 Hz 电源嗡声加风扇）`wind` `rain` `roomtone`，在声部所在的段落里连续铺满。
- **步进网格**：`"pattern": "x...x...x...x..."`，一个字符一步，默认 16 分音符（`"step": 8` 是八分，`12` 是八分三连）。字符的含义：
  - `X` 重音，`x` 普通，`g` 幽灵音，`1`–`9` 力度 0.1–0.9；
  - `o` / `O` 是这件乐器的另一种打法：开镲、边击、拍面、ride 的碗、刷子的扫、闷掉的铙钹；
  - `r` 滚奏（一步里 2 下），`R` 滚 3 下，`f` 装饰音（flam）；
  - `~` 把上一个音延长一步，`.` 休止；空格和 `|` 只为好读，不计。

  小节长短不一时，每小节从头读：短了循环，长了截断。所以 `"x...x...x...x..."` 在 3 拍小节里打 3 下，在 2 拍小节里打 2 下。起点落在小节里的那一步照样发声，只是被小节线截短：二分音符（`"step": 2`，或伴奏型的 `"rate": 2`）在 5 拍小节里是 3 个音，最后一个只剩一拍；在 1 拍小节里也有 1 个音。要按拍数换节奏，就写成字典，值可以是网格，也可以是一小节长的音符表：`{"3": "x...x.x.....", "*": [[0, 1, "c0"]]}`；写成列表则一小节一条，依次循环。
- **音符表**：`[[拍, 时值拍数, 音高, 力度, 奏法], …]`，拍从本小节的强拍数起，`"loop": N` 让一张表跨 N 小节。N 数的是这个声部自己的小节（它所在的那些段落），不是整首的拍数。有的音从来落不进任何一个小节（例如 `loop` 写短了）时，渲染会警告。拍位可以是负数：`[-0.5, 0.5, "d5"]` 是弱起，落在强拍之前半拍，即使这个声部不在前一段里也照样发声，但不能早于整首的开头。弱起在每个 `loop` 窗口之前都响一次，默认 `loop` 为 1 时就是每小节之前都响，所以带弱起的表要把 `loop` 写到整句的长度；弱起音的 `c`、`s` 记号按它引入的那一小节的和弦算。音高记号都相对"那一刻的和弦"和声部的八度：
  - `c0` `c1` `c2` 是和弦的根音、三音、五音，`s1` `s-2` 是从根音起的音阶步数，`d1`…`d7` 是调式音级；
  - `+7` 是根音上方七个半音，`D4` 是绝对音高；
  - 后缀 `'` 升八度、`,` 降八度。

  `"scale"` 可以换音阶：`penta`（大调用宫、小调用羽）、`gong shang jue zhi yu`、`dorian`、`harmonic` 等。和弦多了 `V7`、`Imaj7`、`iiø7`、`bVII`、`Vsus4` 这类写法，同一格写两个（`"ii7 V7"`）就是一小节换两个和弦。
- **动机（`motifs`）**：一个乐句只写一次，在别的段落、别的乐器上调用和变形。顶层写 `"motifs": {"A": {"notes": [[0, 1, "d1"], [1, 2, "d5"], [3, 1, "d4"], [4, 1, "d3"]]}}`，音符表里写 `{"motif": "A", "at": 8, "shift": 1}`，这个调用就在原处展开成普通的音；整个 `pattern` 也可以只写一个调用。常用的发展手法各是一两个键：
  - 模进：`"repeat": 3, "every": 4, "shift_each": 1`，每遍高一级；
  - 应答：`"shift": 2` 换到别的音级上，或 `"invert": true` 倒影；
  - 碎片：`"take": 3` 只取前 3 个音；
  - 扩大：`"augment": 2` 放慢一倍，`"diminish": 2` 是紧缩。

  全部变形、执行顺序和写法见 `tools/audio/motifs.py` 开头的说明，下面有一个完整的例子。
- **伴奏型**（`"figure"`）：
  - `walking` 走路贝斯：强拍根音，最后一拍半音接进下一小节；
  - `oompah` / `waltz`：低音在 1 拍，和弦在其余拍。2、3、4 拍的小节都能用；用 `"role": "bass"` 和 `"role": "chord"` 分给两件乐器。低音比声部的 `c0` 低一个八度：`"octave": 3` 时低音落在第 2 个八度（D 小调是 D2，约 73 Hz），`"octave": 2` 就掉到 D1（约 37 Hz），笔记本扬声器上听不见。所以只弹低音的声部写 3，见下面的华尔兹示例；
  - `strum` 扫弦，`D` 下扫、`U` 上扫、`x` 闷音；
  - `alberti`、`arp-up`、`arp-updown` 是键盘分解和弦；
  - `ostinato` 反复一个音型，跨小节线接着走；
  - `tremolo` 轮指、颤奏（琵琶、巴拉莱卡）；
  - `sustain` 每个和弦一个长音（`"hold": "section"` 整段一个长音，适合 drone）；
  - `stab` 在指定拍上短促的和弦；
  - `roots` 按固定节奏弹根音（`"octaves": true` 是合成波的八度贝斯）；
  - `melody` 是按种子生成的占位旋律，只用来打草稿。
- **律动**：`"swing"` 写 0–0.33 或 0.5–0.75，两种写法都行。0–0.33 表示后半拍推迟的比例，0.33 约等于三连音 shuffle；0.5–0.75 表示前半拍在一拍中所占的比例，0.667 就是三连音。`"humanize"` 是带种子的微小时间和力度抖动。起音慢的乐器写 `"onset_ms"`，提前起音，让听到的起点正好落在拍上（铜管 stab 用 8 ms）。步长和摇摆单位对不齐的声部保持平直，不被拉歪，例如八分摇摆下 `step: 12` 的三连音。
- **按段落改写**：`by_section` 里写的覆盖只作用于那一段。跨几段的声部，给后面某一段写的列表（每小节一条的网格，或带 `loop` 的音符表）默认接着这个声部前面的小节往下数，可能不从这一段的第一小节开始，这时渲染会警告，并说出这一段是从列表的第几小节开始的。声部上写 `"index": "section"`（顶层写 `"pattern_index": "section"` 则对整首生效），列表和 `loop` 就都从每段的第一小节数起。`"figure": null` 让这一段改用声部的 `"pattern"`（例如整首是伴奏型，某一段换成音符表）。段落里的 `params` 对所有乐器都生效，包括单音乐器；参数一变，就从这里开始新的一句。段落里的 `gain_db` 是在乐器之后加的音量，不会推动乐器自己的失真（`sub808` 带 `drive` 时，−12 dB 就是 −12 dB），也不会改变音色。底噪声部认段落的 `gain_db` 和 `vel`，不认 `params`。段落里写的 `onset_ms`，节拍表里的 hit 也按它来算。
- **力度起伏**：
  - `"dyn": {"1": -12, "8:3": 0, "12": -6}`：声部在整首里的音量折线（dB），像推子一样作用在整个声部上，正在响的余音也跟着走。位置写 `小节`、`小节.拍` 或 `小节:拍`，小节按整首数；两点之间线性过渡，第一个点之前、最后一个点之后保持不变；
  - `by_section` 里的 `"cresc": [-8, 0]` 或 `"dim": [0, -12]`：这一段里按 dB 从第一个值走到第二个值。这一段里声部发出的所有声音都跟着这条线走，从前面延续过来的长音也一样；段落结束后，还在响的音保持终点的音量，余音不会弹回去，之后新起的音按它自己的音量。`"vel_ramp": [0.6, 1.0]` 按音在段内的位置缩放力度，音色也跟着变亮，比只调音量更像真的渐强；
  - 单个长音的渐强、渐弱：奏法里写 `{"to": 0.9}`，这个音的力度在时值内直线走到 0.9，然后保持。轮指的每一下也跟着走。`dyn`、`cresc`、`dim` 是 dB 上的直线，发夹是力度上的直线；
  - 渐强写到 0 dB 为止，不要往上加：整首最后按峰值归一化，某一段推到 +12 dB，其余段落就会整体低下去差不多这么多，顶上还会被软削波压平；
  - 音量的台阶都在 10 ms 内滑过去，不会出咔嗒声。
- **段落停顿（`stop`）**：段落上写 `"stop": {"at": "5:2", "keep": ["pad"], "tail": 0.15}`，从这一段第 5 小节第 2 拍（小节按这一段数）到段尾，只有 `keep` 里的声部（写 id 或乐器名）接着演奏。其余声部不再发新音，正在响的音（包括长音）从停点起在 `tail` 秒内淡出，默认 0.15 s，最短 5 ms；延迟和混响的尾巴照常响完；底噪暂停，下一段照常回来；引入下一段的弱起照常演奏。写 `"hold": true` 则让正在响的音自然响完；`"stop": true` 是从段首起全停。停点按网格算，不受 `humanize` 的抖动影响。节拍表里会多一个 `stop:段落名` 的 hit，画面可以在这里卡点。这就是下文说的"屏息"：`keep` 里留一层底，不要做成数字静音。
- **总线**：
  - `"stereo": true` 输出立体声，每个声部有 `pan`；默认仍是单声道；
  - `"space"` 选混响：`dry room plate hall cathedral gated`，声部用 `"send"` 送进去；
  - `"lofi"` 加黑胶噼啪、抖晃和低通，`"tape"` 是磁带饱和。`lofi` 的 `lp` 低于 6 kHz 左右，hi-hat 就没了，因为它的声音都在这个频率之上。可听度检查量的是进总线之前的声部，看不到这个低通，所以不会提醒你：`lp` 保持在 6 kHz 以上，或者把 hat 调响；
  - 声部级的效果有 `delay`（例如 SNES 回声）、`duck`（被 kick 压，做合成波的泵感）、`lp` / `hp`、`drive`。

**写法示例**：

```json
"swing": 0.3,
"parts": [
  {"inst": "upright", "figure": "walking", "ghost": 0.2},
  {"inst": "ride", "pattern": "X.xx", "step": 8, "gain_db": -9, "pan": 0.35},
  {"inst": "brush", "pattern": {"3": "o~x~o~", "*": "o~x~o~x~"}, "step": 8, "gain_db": -6},
  {"inst": "brass", "figure": "stab", "beats": [0, 1.5], "params": {"stab": true, "mute": true}, "onset_ms": 8}
]
```

这是冷爵士：走路贝斯、ride 加刷子、弱音铜管的短促和弦，八分音符摇摆，3 拍的小节也照样成立。

```json
{"inst": "guqin", "scale": "yu", "loop": 2, "send": 0.35, "pattern": [
  [0, 1.5, "s0"], [1.5, 0.5, "s2", 0.6, {"slide": -2}], [2, 2, "s4", 0.7, {"yin": true}],
  [4, 2, "s3'", 0.6, {"harm": true}], [6, 2, "s1", 0.7, {"bend": 2}]]},
{"inst": "luogu", "pattern": "仓.才.台.才.仓.七.台台仓.", "gain_db": -6}
```

古琴的滑音、吟、泛音、按弦上滑都写在单个音的奏法里；锣鼓经直接写字。

```json
"beats_per_bar": 3,
"parts": [
  {"inst": "pizzicato", "figure": "waltz", "role": "bass", "octave": 3},
  {"inst": "strings", "figure": "waltz", "role": "chord", "octave": 4, "gain_db": -8}
]
```

三拍子华尔兹：拨弦低音在 1 拍，弦乐和弦在 2、3 拍。低音声部写 `"octave": 3`，低音落在第 2 个八度；写 2 会低到听不见。

```json
"motifs": {"A": {"notes": [[0, 1, "d1"], [1, 2, "d5"], [3, 1, "d4"], [4, 1, "d3"]]}},
"parts": [
  {"inst": "violin", "sections": ["theme"], "octave": 4, "loop": 4, "pattern": [
    {"motif": "A"}, {"motif": "A", "at": 8, "shift": 1, "vel": "+0.1"}]},
  {"inst": "brass", "sections": ["develop"], "octave": 4, "loop": 4, "by_section": {"develop": {"cresc": [-8, 0]}},
   "pattern": [{"motif": "A", "take": 3, "repeat": 3, "every": 4, "shift_each": 1, "vel_each": "+0.05"}]},
  {"inst": "celesta", "sections": ["coda"], "octave": 5, "loop": 4, "pattern": {"motif": "A", "augment": 2}}
]
```

一个动机走完三段：小提琴先陈述，再高一级、响一点重复一遍；发展段的铜管取它的前 3 个音做模进，每遍高一级、响一点，整段渐强 8 dB；尾声的钢片琴把它放慢一倍。改 `A` 里的一个音，三处一起变。

**电平**：`gain_db` 0 时，各乐器响度大致相当：单个打击或拨弦的峰值约 0.5，持续音约 −20 dBFS RMS，底噪约 −34 dBFS RMS（黑胶噼啪按峰值定，峰值约 0.2，RMS 更低）。起步可以按这个范围写：
- 主奏 0 到 −3；
- 和弦、pad −6 到 −12；
- 贝斯 0 到 −4；
- kick、snare −1 到 −6；
- 镲、沙锤 −8 到 −14；
- 底噪 −3 到 −9；
- `send` 0.1–0.4，大教堂混响可以到 0.6。

**每个声部都必须听得见**：一个音也没有的声部，或者最终文件里最响的 50 ms 低于 −40 dBFS 的声部，渲染会直接报错，并点名是哪个声部。响度按各声道功率的平均来量，硬声像的声部不会被低估；冲击类的底噪也可以按峰值减 18 dB 来算。这防的是"写了鼓却没出声"的静默故障。确实要很轻的声部，写 `"quiet": true`；但它管不了一个音都没有的声部。

**写错了会直接停下**：渲染前先检查一遍，写错时报出是哪个声部。检查的内容：
- 不存在的乐器、段落、混响空间、`duck` 对象，或 `by_section` 里的段落名；
- 重复的 `id`；
- 不是有限数字或超出范围的字段，例如 `pan` 超出 −1 到 1、`step` 小于等于 0；
- 不是 `[拍, 时值, …]` 的音符；
- 没有扫弦记号的 strum；
- 超出 MIDI 0–127 的音高；
- 写错的动机调用：没有这个动机，不认识的键、变形或调式，变形缺了参数，次数不是整数，片段一个音也不剩，`vels` 的个数和音数不一样，动机互相调用成环；
- 超出所在段落的 `stop`，`stop` 里不认识的键、不是 true / false 的 `hold`、`keep` 里不是任何声部的名字；
- 写法不对或重复的 `dyn` 位置，写在 `by_section` 之外的 `cresc`、`dim`、`vel_ramp`，写进 `params` 的发夹 `to`。

**确定性**：每个声部的随机流来自"种子 + 声部的 `id`（或乐器名和它是第几个同名声部）+ 音符序号"。加一个声部、删一个声部时，乐器不同或各有 `id` 的其他声部，stem 逐位不变（已验证：删掉 bongo、chipkick、hihat、framedrum，或在最前面插一个 shaker）。同一种乐器写了两个以上、又都没有 `id` 时，它们按先后编号：删掉前面那个，后面的就换一套随机流，声音跟着变。遇到这种情况渲染时会提示；给每个同名声部写上 `id`，声音就固定了。同一份谱子渲染两次，sha256 相同。

**老实说还做不到的**：
- 这是合成，不是采样。钢琴、弦乐组、铜管在笔记本扬声器上认得出来，凑近听仍然是"合成的"；独奏提琴的换弓和弓压变化是简化模型。
- 旧的拨弦音色用 Karplus–Strong，基频准，高次泛音略偏；古琴的泛音是近似纯音。物理建模的音色（`_pm` 结尾的，以及 `guitar`、`koto`、`shamisen`、`banjo`、`kalimba`）单根弦的基频误差在 ±1.2 音分以内，但琴体是合成的共鸣模型，不是从真琴测出来的脉冲响应，凑近听仍然是合成的。
- 旧音色 `saw_pad` 保留原样，失谐的锯齿波互相拍频，长音每秒起伏好几 dB，`qa` 可能报 pumping。新的 `strings`、`brass`、`drone`、`polysynth` 做了去拍频处理（弦乐组单音的起伏从 12 dB 降到 5 dB）。
- `braam` 和低音大提琴的锯齿波边沿会出现在 `qa` 的 click 警告里，这是设计出来的声音，不是故障。三味线的 sawari（`buzz`）每个周期拍一下琴码，拨得重时 `qa` 也会列出几处；`"buzz": 0` 就没有。
- 没有人声。
- 最耗时的是 `gong`、`luogu`、`braam`、`cs80`、`cimbalom`，每个新音约 0.05–0.3 s；物理建模的音色每个新音最多约 0.05 s，音高一直在动的长音（古琴的滑音、吟、猱）约 0.07–0.08 s；三味线因为 sawari 每个采样都走慢路径，一秒长的音在 MIDI 96 约 0.2 s，108 约 0.7 s，114 及以上约 1.4 s。一段 5 s、9 个声部的谱子，在 M3 Max 上约 1.5 s 渲染完。
- 内存：声部逐个渲染、混进总线后就释放。一首 7 个声部的立体声谱子，5 分钟峰值约 1.1 GB，10 分钟约 3.6 GB（macOS 的 peak memory footprint；RSS 会显示得更高，因为释放的页还挂在进程上）。展示片 20–81 s，用量在 0.5 GB 以内。
- 没有变速：整首只有一个 `bpm`，写不出渐慢、渐快和延长记号。要多停一会儿，只能用 `meters` 给某一小节加拍（介绍片第 11 小节就是这样）。

**戏剧性的"停"不能做成数字静音。** 要停的时候：
- 保留一层底（sub 或 pad）；
- 把滤波往下收，撤掉鼓；
- 再用一个反向渐强（reverse swell）拉进下一个重拍。

介绍片 v2 有 4 处真静音，用户听到的是"卡顿"；v3 把这 4 处都改成这样的"屏息"。`bin/vh qa` 会把检查区间里任何 ≥ 20 ms 的数字静音判为问题：区间默认从 1.0 s 起，到节拍表的淡出起点为止（没有节拍表时到片尾前 2.8 s），`--from`、`--to` 可改；区间外（片头片尾）的静音只列出来，不算失败。

### 音效（`sfx`）

- **音效是独立的事件层**，和音乐分开：`audio/events.json` 写成 `[{t, sfx, gain_db, pan, dist}]`，后两项可选。`sfx place` 输出 48 kHz 立体声。
- **`t` 是"落点"**：内置音效各自带落点偏移（例如 whoosh 的峰值、riser 的顶点），摆放时会自动对齐，保证声音峰值和动作在同一帧。
- **`pan`**（−1 最左，0 居中，1 最右）用等功率声像律，并且按"居中 = 原电平"归一。不写 pan 的事件和以前的单声道摆放逐采样相同。pan = ±1 时，那一侧 +3 dB，总功率不变，所以大声的音效打到最边上时注意削波（工具会提示削波的采样数）。
- **`dist`**（≥ 1，单位是参考距离，1 = 原样）：电平乘 1/dist，距离每翻一倍 −6 dB；再加一个平缓的一阶低通，截止频率 16 kHz / dist，最低 1 kHz。低通带来的延迟不到 0.2 ms，落点不受影响。声速延迟没有加，因为 `t` 本来就是"该听到的时刻"；要做"先见闪光、后闻炮声"，自己把 `距离米数 / 343` 加到 `t` 上。
- **pan 从画面上算，不要凭感觉写。** 取发声物体在那一刻的屏幕 x：`pan = 2·x / 画面宽度 − 1`，再乘 0.7–0.8 收一点，全左全右在耳机里很刺。3D 场景用相机坐标：`pan = v·right / |v|`，其中 v 是声源到相机的向量；距离也从同一个 v 来。镜头在动时，同一个声源在不同时刻的左右位置也不同。Austerlitz 那支片子的音效就是这样从场景事件里算出声像和距离的，见 `cases/opus55-gallery.md` 第 6 节。
- **来源顺序**：先用有授权的录音素材（在 NOTES 的素材台账里记下来源和许可）；缺的类别再用内置库补。自己的立体声素材会先折成单声道，当作一个点声源来摆。内置库有 15 个代码合成音效：click、tick、pop、toggle、typing、whoosh、swish_rev、riser、impact、boom、ding、success、error、glitch、shutter，都是 MIT 原创，可以复现。每个内置音效用自己的随机种子（按名字），所以 `sfx lib` 和 `sfx place` 得到同样的采样，不会因为前面先渲染了别的音效而变。impact 和 boom 在命中点有一层 1–4 kHz 的起音（crack），身体晚 2 ms 进来：没有这一层时，它们 98–100% 的能量在 150 Hz 以下，手机和笔记本几乎放不出来。
- **`role`**（可选：`hero`、`detail`、`ambience`、`signal`）：这个事件在混音 profile 里属于哪一类，什么时候要写见下文"混音"。`sfx place` 会检查它，并在输出旁边写一个 `<out>.events.json`：每个事件的类和原因、起点，以及它自己摆好后的电平（fast：最响 100 ms 的 K 加权响度；m400；tp：真峰值；len：持续时间；lf：150 Hz 以下能量占比），混音前就能读。
- **不要让每个音效都去压音乐。** 介绍片 v2 把 74 个音效全接进了 ducker，ratio 是 6，配乐跟着每个音效一抽一抽。混音 profile 里音效从不压音乐（只有没人说话时，hero 命中处音乐让 2–2.5 dB）；不用 profile 时默认也只让人声压音乐（`duck=voice`），真要用 `duck=on`，把 `duck_ratio` 降到 2–3。`bin/vh qa` 的抽吸一项专门查这种问题。

### 混音（`mix`）和混音报告（`qa mix`）

**按视频类型选一个 profile，所有层都相对一个锚点放。** 有旁白时锚点是旁白（各句响度的中位数），没有旁白时是音乐（它 3 s 的短时响度，最低取整体响度下方 8 LU）。顺序是人声锚点 → 音乐 VMR → 音效分级 → 纵深 → 母带：
- 旁白逐句往中位数拉平（最多 ±3 dB）；
- 音乐逐句只压到目标 VMR（人声减音乐，LU），1–4 kHz 只挖词需要的深度，中文旁白连 250 Hz–1 kHz 一起挖；
- 每个音效向本类范围的中心走一半；
- 所有音效共用一个短房间；
- 母带是一个整体增益加真峰值限幅器。

各步的细节写在 `tools/audio/mix.py` 开头。

```bash
A=projects/<p>/audio
# 旁白片：explainer / short；events= 让混音器自己摆音效（摆法和 sfx place 相同），每个事件才能单独分级
bin/vh mix $A/mix.wav profile=explainer voice=$A/voiceover.en.wav music=$A/music.wav \
           events=$A/events.json lib=$A/sfx timeline=$A/timeline.en.json music_db=-5 stems=$A/stems
# 没有旁白的片子：锚点是音乐；dur / fade 在混音里截到片长并淡出，超出片尾的长音效一起淡出
bin/vh mix $A/mix.wav profile=cartoon music=$A/music.wav events=$A/events.json lib=$A/sfx dur=12 fade=0.1 stems=$A/stems
bin/vh qa mix $A/stems --beats $A/music.beats.json   # 只看混音报告（词级时间取 timeline 里的 words，或 --words）
```

**按类型选 profile**（数值是相对锚点的 LU）：

| profile | 用于 | 锚点 | VMR 目标 / 正常范围 / 硬下限 | 挖让 SNR / 最深 (dB) | hero | detail | ambience | signal | 说话时 hero 最高 | 另外 |
|---|---|---|---|---|---|---|---|---|---|---|
| `explainer` | 01 原理讲解、06 论文 | 旁白 | 13 / 11–18 / 9 | 10 / 7 | −9…−2 | −18…−8 | −28…−16 | −12…−4 | 人声 −4 | |
| `short` | 02 知识短视频 | 旁白 | 11.5 / 10–16 / 8 | 9 / 6 | −7…−1 | −16…−7 | −26…−14 | −8…−2 | 人声 −3 | 没人说话时 hero 下音乐让 2 dB |
| `promo` | 03 发布片、05 数据故事、08 快剪 | 音乐（有旁白时是旁白） | 10 / 8–16 / 6 | 12 / 9 | −4…2 | −11…−3 | −20…−10 | −10…−3 | 人声 −2 | hero 下音乐让 2.5 dB |
| `cartoon` | 07 手绘、角色短片 | 同 promo | 10 / 8–16 / 6 | 12 / 9 | −2…4 | −6…0 | −16…−8 | −6…0 | 人声 −2 | 音效峰值 ≤ 锚点 +9 dB；hero 让 2 dB |
| `mv` | 04 MV | 音乐 | 6 / 4–12 / 3 | 12 / 9 | −8…−2 | −16…−8 | −26…−14 | −12…−5 | 人声 −4 | 不让、不加宽 |
| `swatch` | 风格样片（`render.sh`） | 音乐 | –（没有旁白） | – | −5…1 | −11…−4 | −19…−11 | −10…−3 | – | 房间 0.25 s；hero 让 2 dB |

VMR 这一列有三个数：
- 目标：混音器把每句压到这里；
- 正常范围：`qa mix` 在范围外报 `LOW`、`HIGH` 警告；
- 硬下限：低于它是硬失败。

所有 profile 一样的：
- 每个事件最多动 ±9 dB；
- 音乐的整体增益由各句下面的音乐定，限制在 −24…+6 dB 以内，被限住时日志会说明；
- `lufs=-14`，`tp=-1.65`（见下面的 AAC 编码）；
- 起始平衡是 `music_db=-6 sfx_db=0 voice_db=0`，swatch 用 `render.sh` 原来的 0 / −3。

起始平衡要写成片子原来用的值：音效（以及没有旁白时的音乐）从它出发往目标走一半。有旁白时，音乐的位置由 VMR 决定，和 `music_db` 无关。

其他参数：
- `sfx=`（一整条摆好的音效轨）只能当一层 detail，不分级，所以有 events.json 时用 `events=`；
- `roles=`、`keep=` 见下文；
- `stems=DIR` 按最终增益写出各总线和 `meta.json`，`bin/vh qa` 的 `--stems` 读它；
- 不写 `profile`（或写 `profile=none`）就是原来的 ffmpeg 链（`duck=voice` 侧链压缩，响度按 loudnorm 定），输出和以前逐字节相同。

**什么时候写 `role`**：
- 类先看事件的 `"role"`；没写时，`"layer": "sonification"` 是 signal；再没有就按名字里的整词判断（复数也算）：
  - impact、boom、stomp、slam、ding、success、error、bell、snap… 是 hero；
  - click、tick、pop、toggle、whoosh、step、typing… 是 detail；
  - gust、wind、rain、hum、hiss、creak、room、drone… 是 ambience；
  - 都不是就归 detail。`clock_tick`、`ticks` 算 tick；`airhorn`、`dropdown`、`human` 不会被当成 air、drop、hum。
- 名字和它在这支片子里的作用不一致时就写 role：
  - 01 的风（`gust_1`、`gust_2`）是这个包袱的动作本身，是 detail，不是 ambience；
  - 00 的最后一个 thock（`thock_lo`）是整个 hook 落地的那一下，是 hero；
  - 落在关键帧上的一记拨弦（ink-wash 墨滴落下时的古筝）也是 hero。
- 不想改 events.json 时，用 `roles=roles.json`：`{"<事件序号>": "hero", "<sfx 名>": "detail"}`，它覆盖事件自己的 role。对不上任何事件的键会被列出来。样片在 swatch.js 的 `FOLEY` 里写 `role`，`foley.mjs` 会带进 events.json。
- 报告 `[5]` 的 why 列写着每个事件的类是怎么来的，先看它。

**怎么读混音报告**（`bin/vh qa mix <stems>`，或 `bin/vh qa <mix.wav> … --stems` 输出的最后一段）：
- `[1] loudness`：各总线的响度和占总能量的比例。
- `[2] speech`：逐句列出人声、音乐、bed（音乐 + 音效）的响度，以及：
  - VMR；
  - VMRp10：这句里 400 ms 窗口 VMR 的第 10 百分位，也就是句中最差的时刻；
  - VBR：人声减整个底；
  - 1–4 kHz SNR。

  flag 的含义：
  - `LOW`、`HIGH`：出了正常范围；
  - `FAIL`：低于硬下限；
  - `NO VOICE`：人声 stem 里那句没有声音，timeline 和配音文件对不上，这句不参加检查；
  - `no music`：这句下面没有音乐，没有 VMR 可判。
- `[3] masking`：每个词在 1–4 kHz 的 SNR，列出最危险的 8 个。三个数分别是对整个底、对音乐、对音效，看是谁盖住的。词级时间来自 `--words`，或 timeline 里 `bin/vh tts … --align gemini` 写的 words；都没有时按 0.4 s 一段算，只给警告（段会跨过停顿，读数偏悲观）。
- `[4] gaps`：每个停顿里音乐的响度，相对锚点，也相对前后两句下的音乐。
  - 短停顿里抬高很多，听起来就是"呼吸"；配乐在那里正好有段落或 hit 时，报告会注明"可能是设计的起势"。
  - 2 s 以上只有音乐的一段，比旁白响 3 LU 以上时也会警告：音乐只有一个整体增益，如果各句下面的音乐比这里轻很多，这段就会显得很冲。
- `[5] SFX`：每个事件的类、它自己的 fast 响度和真峰值，以及三个相对值：
  - 相对锚点：类的范围判的就是这一列；
  - 相对当时的底；
  - 说话时相对人声。

  flag 的含义：
  - `HIGH`、`LOW`：出了类的范围；
  - `OVER-VOICE`：说话时 hero 高于表里"说话时 hero 最高"那一列，硬失败；
  - `MASKS-VOICE`：它的 1–4 kHz 离人声不到 6 dB；
  - `BURIED`：比底低 14 dB 以上（mv 是 16 dB），听不见。

  末尾是各类的中位数，和顺序检查：hero、signal 都应该 ≥ detail ≥ ambience，hero 和 signal 之间不排。
- `[6] depth`：各总线的宽度、分频段左右相关、盲估的混响时间、频谱重心、干湿比。人声应当最干、居中，音效其次，音乐最宽最湿。
- `[7] limiter`：母带限幅器压在哪里、压了多少。超过 2 dB，说明进限幅器之前的峰值太高。
- **硬失败**（退出码 1）：
  - 有一句低于硬下限；
  - 说话时 hero 超过它的上限；
  - 有词级时间时，低于 presence 地板的词超过 profile 允许的比例；
  - 某一类的中位数离范围超过 3 LU。低频命中低于范围时按范围下限算，因为混音器本来就不抬它，这种情况只给警告；
  - timeline 里有句子，但人声 stem 在所有句子下面都没声音；
  - 在 `bin/vh qa … --stems` 里，一个 cue 只以"弱"通过对位检查，报告又说它 `BURIED`：它对上了，但听不见。
- **怎么改**：
  - 一句 `LOW`：多半是那句本身太轻（拉平最多 3 dB），或配乐在那里有个很响的峰（看 `[4]`）。重录那句，或在 score 里把那一段收一收；
  - `OVER-VOICE`：把 hero 挪出句子，或者它本来就不是主角，写成 detail；
  - 某类中位数偏：先看 why 列；分类对的话调 `gain_db`（混音器只走一半，设计的相对大小要先对）；
  - `BURIED`：提高 `gain_db`，或换一个 1–4 kHz 更多的声音。样片里被判“弱 + BURIED”的 tick，提高 3 dB 就过了；
  - 低频 hero 在手机上弱（报告说 "% of its energy under 150 Hz"）：加一层 1–4 kHz 的起音，不要加增益。

**AAC 编码和 cue check**：
- **真峰值**：
  - AAC 编码会抬高真峰值，抬多少看内容和码率。用混音器的表（4 倍过采样）量，混音都是 `tp=-1.65`：
    - showcase 的三支片子（01–03）用 profile 混：`bin/vh mux` 的 192k 下是 −0.12…+0.08 dB，成片都在 −1.5 以下；换成 128k 是 −0.01…+0.16 dB。
    - 样片用 128k：+0.16…+0.86 dB（halftone-comic +0.86，cutout-jazz +0.53）。
    - 限幅器压得很多的合成测试更高：一段没有旁白、限幅 2.6 dB 的混音在 192k 下 +0.80 dB，一条只有合成音效的总线 +1.2…+1.5 dB。

    profile 默认的 `tp=-1.65` 只够第一种情况。
  - `render.sh` 会测编码后的 mp4：高于 −1.5 dBTP 时，从混音实际的真峰值（和原上限取较低者）再降低超出的量加 0.1 dB，重混、重编码；最多 3 次，还超就报错退出。写这一节时，28 个样片里只有 guochao-festive 需要。
  - 其他成片自己测：`ffmpeg -i final.mp4 -af ebur128=peak=true -f null -`，超了就用更低的 `tp=` 重混。
  - 真峰值按 BS.1770 的 4 倍过采样算；16 倍过采样在瞬态上最多再高 0.16 dB。
- **门禁是 WAV**：`bin/vh qa mix.wav …`。
  - 成片 mp4 再跑一次，扫描照常判定。cue check 的容差加 12 ms，单个 cue 的问题只给警告：混音实验的 16 个 mp4 里有 284 个 cue，AAC 让 onset 最多偏 5.4 ms，另有 3 个临界的 onset 一边检测到、一边没有。
  - 整个编码系统性地偏了才判失败，这是封装错位（有 8 个以上 cue，超过 20% 对不上，或者中位误差超过 15 ms）：音轨晚 20 ms 或 60 ms 都会失败。检测器自己的滞后是 +3…+8 ms。
  - 混音报告读的是 stems，不在 mp4 上重跑。
- **margin**：每个 cue 都打印 margin，即 onset 强度超出检测门槛多少。低于 0.02 标成 `OK~`，是警告：电平稍微一变，它就可能检测不到。
- **近乎纯音的音效**（tick、ding、toggle，频谱平坦度低于 0.01）在配乐下很难触发 onset 检测。onset 没找到或者临界时，用它自己的声音和混音做互相关（250 Hz–9 kHz，参考 motioner 的 sync_check）：
  - 在 1 帧以内找到、匹配度 ≥ 0.3，就算 OK；
  - 正好落在计划的采样上（±1 ms）、匹配度只有 0.15–0.3，算对齐但很弱，给 `OK~` 警告；
  - 峰值落在搜索窗边缘 4 ms 以内，或者 ±250 ms 内的更远处有明显更好的匹配（高 0.05 以上），都不算：长音挪走以后，窗口里最靠近它的那一边照样相关得很好。拿 28 个样片做了 96 个测试混音，每个把一个纯音挪开 60–100 ms：互相关原来确认了其中 19 个，现在一个也不确认（10 个变成 OFF，9 个只剩临界的 onset，给 `OK~` 警告）；位置正确的混音上，68 个确认一个没丢。

  互相关只能确认一个 cue，不会判错一个 cue。
- **第 0 帧的 cue**：前面先垫一帧静音再检测，否则 onset 没有起点。
- **同步点被压没了**：profile 把某段音效压低以后，一个同步点检测不到了，就用 `keep=<这个 cue 的时间>` 重混，那一段保持设计电平；或者提高那个事件的 `gain_db`、改它的 role。
- **抽吸**：给了 `--stems` 时，抽吸检查不算音乐 stem 里本来就有、而且一样深的凹陷（配乐自己的动态），只报混音造成的。

**局限**（测出来了，还没解决）：
- profile 只把每个事件往目标走一半：它压缩分布、保留设计的先后，不会替你判断哪个音效重要。`gain_db` 设计得离谱，结果还是会偏。
- 低频命中不能靠增益解决，要加 1–4 kHz 的一层；名字提示会分错，看 `[5]` 的 why 列。
- cue check 只看那个时刻有没有 onset，不知道是谁的：音效挪开以后，计划时刻上配乐自己的 onset，或者这个音效的第二个音（toggle 的第二下、success 的琶音），照样让它通过。上面 96 个挪开 60–100 ms 的测试里，有 39 个这样干净地通过，都是 toggle、ding、success。
- 事件电平（fast、m400）的窗口截在事件两端，这是混音实验定下的算法，类的范围就是按它标定的。所以短的、或者最响的地方在开头 50 ms 以内的声音，读数偏高：内置的 tick +7.0、click +5.2、pop +2.9、toggle +2.8、error +1.9、shutter +1.5 LU。在 profile 内部它是一致的，但不能拿去和别的表比。
- TTS 的峰均比有 13–16 dB。旁白为主的片子，人声的峰值控制最多压 2.5 dB，母带限幅器最多 1 dB。
- 抽吸检查的门槛（4 dB、60 ms）偏敏感，会把配乐自己的凹陷报出来，给 `--stems` 可以排除。
- 响度：profile 在 BS.1770 上定 −14（ebur128 读 −14.0），loudnorm 在混音实验的 8 段混音上读 −14.2 到 −13.7。不写 profile 的默认链仍按 loudnorm 定 −14。
- 确定性：同一台机器上两次输出逐字节相同（房间的 IR 用固定种子，信号路径里没有 ffmpeg 滤镜）；跨平台时 FFT 的最低几位没有验证。
- 速度和内存（M3 Max）：25 s 的片子 3–5 s（含解码），3 分钟约 24 s；内存约每分钟片长 1 GB。
- 配乐自己的空间（每个 profile 该用多大的混响、旁白下旋律往两边摆）还没有接进 `bin/vh music`，是下一步。

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
- **`qa` 的 cue check 按全片最响的 onset 归一化**：别处一个特别大的 onset，会让很弱的 cue 被判成 OFF。每个 cue 现在都打印 margin（超出门槛多少），临界的标成 `OK~`，近乎纯音的音效还会用自己的声音确认一次（见上文"混音"的 cue check），但归一化本身没有变。
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
- **音效简报**：每个动作写一句"什么东西、什么材质、多大、多远"，例如"纸片被快速抽走，干、短、偏高频，近"；先从内置 15 个里找，没有合适的再用 ElevenLabs Sound Effects 生成，或者在 `styles/_swatch/custom_sfx.py` 那样用代码合成。
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
