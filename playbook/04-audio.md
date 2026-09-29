# 04 音频

原则：**先有音频，再有时长。** 要先把音频变成时间表，agent 才能处理：旁白要有词级时间戳，音乐要有节拍网格，歌曲要有逐句歌词时间。

## 现成接口：`bin/vh` 的声音命令

声音分成 **配音、配乐、音效、歌曲** 四类。每类都有统一的命令和输入输出格式，服务商或来源可以替换，流程不变。依赖由 `uv run --with` 临时提供，不装进全局环境；**API key 只从环境变量读取**。

```bash
# 配音（双语）：audio/script.txt → voiceover.<lang>.wav + timeline.<lang>.json
bin/vh tts projects/<p> qwen Serena zh            # 本地开源 Qwen3-TTS（默认；首次下载约 2GB）
bin/vh tts projects/<p> qwen Ryan en              # 同一份稿子，英文旁白
bin/vh captions projects/<p> zh                    # → captions.zh/en/bi.srt + captions.json（给引擎画进画面）
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
- 可以加 `@id` 前缀，比如 `@hook 一句话，做出一支片子。 || One sentence in, one film out.`。

按句合成，所以每句的起止时间都是**实测**的。

**同一份稿，中文和英文旁白长度不同**（实测一段 3 句的稿子：中文 9.3s，英文 10.8s）。所以双语成片要各自按 `timeline.<lang>.json` 排时间：
- 画面可以共用，但节奏按语言重排；
- 或者只出一种语言的旁白，配中英双语字幕。

| provider | 类型 | 需要什么 | 时间精度 | 状态 |
|---|---|---|---|---|
| `qwen`（默认） | **本地开源** Qwen3-TTS（Apache-2.0），mlx-audio 运行在 Apple Silicon 上。中文音色：Serena（温暖女声）、Vivian、Uncle_Fu、Dylan（京腔）、Eric（川话）；英文音色：Ryan、Aiden | 首次运行下载约 2GB；换 1.7B 模型（`QWEN_TTS_MODEL`）后可以用 `--instruct` 控制语气 | 句级 | ✅ 已实测中英 |
| `say` | macOS 自带，离线，适合打草稿 | 无 | 句级 | ✅ 已实测 |
| `edge` | 微软免费在线音色 | 联网；非官方接口 | 句级 | 待实测 |
| `dashscope` | 阿里云百炼 Qwen3-TTS（`qwen3-tts-flash`），云端 | `DASHSCOPE_API_KEY` | 句级 | 接口已留，待实测 |
| `elevenlabs` | 高质量多语种配音 | `ELEVENLABS_API_KEY`、voice_id | **字符级** | 接口已留，待实测 |

需要字级时间（逐字高亮）时，用 `elevenlabs`，或者对句级结果再跑一次强制对齐：mlx-audio 的 Qwen3-ForcedAligner、FunASR 或 whisper.cpp。这一步的接口已留好，还没封装。

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
- **混音**：`bin/vh mix` 让音乐在人声和音效出现时自动让位，这样关键的叮咚、确认、转场声一定听得见。混音保留立体声，音效总线上的声像会原样保留下来。响度分两遍处理：先测量，再只加一个整体增益，并限制真峰值。这样电影配乐的动态范围（LRA）不会被压扁；介绍片用单遍处理时，LRA 从 13.6 被压到了 7.0。
- **不要让每个音效都去压音乐。** 介绍片 v2 把 74 个音效全接进了 ducker，ratio 是 6，配乐跟着每个音效一抽一抽。没有人声时用 `duck=off`，或者把 `duck_ratio` 降到 2–3；有人声时用 `duck=voice`，只让人声压音乐。`bin/vh qa` 的抽吸一项专门查这种问题。

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

## 选型

| 需求 | 方案 |
|---|---|
| 中文配音，本地 | `mlx-audio` 在 Apple Silicon 上跑 Qwen3-TTS（Apache-2.0，支持方言和声音设计）。要克隆声音用 CosyVoice 或 GPT-SoVITS。 |
| 配音，云端，追求稳定 | ElevenLabs 的 `/v1/text-to-speech/{voice_id}/with-timestamps` 直接返回字符级时间；国内可选火山豆包、阿里百炼、MiniMax。 |
| 免费、先凑合用 | `edge-tts`（微软中文音色，非官方接口，随时可能失效） |
| 词级时间戳 | 中文用 FunASR（字级，带标点）；通用用 whisper.cpp（Mac 上有 Metal 加速）；已有讲稿或歌词、只需对齐时用 ctc-forced-aligner |
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
- ClaudeAnimationBase 用 `src/config.js` 的 `bpm` 和 `offset`，`pulse()` 和 `beatN()` 会自动对齐节拍。
- Remotion 的做法是在 `calculateMetadata` 里读取音频时长来设置帧数；HyperFrames 的做法是 `sync-durations` 用实测时长覆盖估计值。

## 同步的五种模式

1. **音频先行**：先生成音频，按实测时长确定每个场景的帧数。
2. **按 cue 词触发**：旁白说到某个概念时，那个概念的画面正好出现。动画比旁白提前约 0.5s 开始，每句话说完后停约 1s。
3. **按拍落点**：切镜、重音动作、大字出现都落在拍点上，误差 ±1 帧；大的场景切换放在小节线上。
4. **混音**：有旁白的段落压低背景音乐（HyperFrames 的 voiceover carve 只压人声所在的频段）。响度用两遍线性处理：第一遍测量，第二遍只加一个整体增益，并限制真峰值，`bin/vh mix` 就是这样做的。单遍动态 loudnorm 会压扁配乐的动态，介绍片的 LRA 就是这样从 13.6 掉到 7.0 的。
5. **在最终混音上做 cue check**：`bin/vh qa` 拿最终混音的 onset 去对照节拍表和音效事件表，逐条检查是否在 1 帧以内，同时扫描静音、掉音、抽吸和 click。只查配乐不够，混进音效以后，有的 cue 会被盖住，有的会和别的并成一个。有旁白时加 `--voice voiceover.wav`，人声下面设计好的压低就不会被算成抽吸；另外把成片重新转写一遍，和 cue 表对比时间差。四项扫描的做法和判定标准见 `02-verification.md` 的"音频 QA"一节。

## 常用命令（示例，按项目调整）

```bash
# 本地中文 TTS（安装：uv tool install mlx-audio 或在项目 venv 里 uv add mlx-audio；模型名以 mlx-audio README 为准）
# 词级时间戳：whisper.cpp（brew install whisper-cpp）或 FunASR（uv add funasr）
# 响度标准化到 -14 LUFS（短视频平台常用），两遍线性，bin/vh mix 已经内置；手动做时：
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=20:print_format=json -f null -   # 第 1 遍：记下 input_i/tp/lra/thresh 和 target_offset
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=20:linear=true:measured_I=…:measured_TP=…:measured_LRA=…:measured_thresh=…:offset=… mix_norm.wav
# 视频与音轨合成：先出无声成片，再用 bin/vh mux 把音轨补齐或截到视频的精确长度（-shortest 按 AAC 帧截断，会吃掉最后 2 帧）
ffmpeg -framerate 30 -i out/frames/f%05d.jpg -c:v libx264 -crf 17 -pix_fmt yuv420p out/final.mp4
bin/vh mux out/final.mp4 audio/mix.wav out/final-av.mp4
```

mlx-audio 和 FunASR 的具体调用方式以各自 README 为准，第一次用时读一遍再写脚本，并把可用的命令记进项目的 `LESSONS.md`。
