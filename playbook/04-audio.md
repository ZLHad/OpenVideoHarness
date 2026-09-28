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
bin/vh music --example > projects/<p>/audio/score.json
bin/vh music projects/<p>/audio/score.json projects/<p>/audio/music.wav     # + music.beats.json（段落、节拍、冲击点）
# 音效：内置库 + 按动作时间摆放
bin/vh sfx lib projects/<p>/audio/sfx
bin/vh sfx place projects/<p>/audio/events.json projects/<p>/audio/sfx.wav 45 --lib projects/<p>/audio/sfx
# 混音与合成
bin/vh mix projects/<p>/audio/mix.wav voice=…/voiceover.zh.wav music=…/music.wav sfx=…/sfx.wav
bin/vh mux projects/<p>/out/final.mp4 projects/<p>/audio/mix.wav projects/<p>/out/final-av.mp4 \
           projects/<p>/audio/captions.zh.srt projects/<p>/audio/captions.en.srt   # 软字幕轨（可开关）
bin/vh beats <任意音乐文件>                          # 外来音乐的节拍分析（librosa）
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

`score.json` 的写法见 `bin/vh music --example`：
- 顶层：`bpm`、`key`、`mode`；
- `sections[]`：`bars`、`chords`（罗马数字）、`layers`（kick clap hats bass pad arp lead）、`energy`（0–1）；
- 段落的特殊效果：`riser`（上升音推向下一段）、`impact`（段首冲击）、`fill`（最后一拍留白）。

输出的 `music.beats.json` 包含 `sections`、`beats`、`downbeats`、`hits`，引擎直接读它来切镜和打点。

### 音效（`sfx`）

- **音效是独立的事件层**，和音乐分开：`audio/events.json` 写成 `[{t, sfx, gain_db}]`。
- **`t` 是"落点"**：内置音效各自带落点偏移（例如 whoosh 的峰值、riser 的顶点），摆放时会自动对齐，保证声音峰值和动作在同一帧。
- **来源顺序**：先用有授权的录音素材（在 NOTES 的素材台账里记下来源和许可）；缺的类别再用内置库补。内置库有 15 个代码合成音效：click、tick、pop、toggle、typing、whoosh、swish_rev、riser、impact、boom、ding、success、error、glitch、shutter，都是 MIT 原创，可以复现。
- **混音**：`bin/vh mix` 让音乐在人声和音效出现时自动让位，这样关键的叮咚、确认、转场声一定听得见。

### 歌曲（带人声演唱）

| 来源 | 做法 | 状态 |
|---|---|---|
| **Suno 等网页服务** | 用户生成、下载后放进 `audio/`；歌词逐句对齐走下面的"歌词对齐"一行；节拍用 `bin/vh beats` | ✅ 流程可用（Suno 没有官方公开 API，不接非官方封装） |
| **ElevenLabs Music**（云端） | 按提示词生成带人声的歌曲 | 接口位已留（`tools/audio/` 下加一个 provider） |
| **本地开源歌曲模型**（如 ACE-Step、YuE 一类） | 需要确认本机能跑（多数需要 GPU） | 接口位已留，没有测过，UNVERIFIED |
| **代码合成** | `bin/vh music` 只做器乐，不做人声 | ✅ |

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
4. **混音**：有旁白的段落压低背景音乐（HyperFrames 的 voiceover carve 只压人声所在的频段）；最后用 `ffmpeg -af loudnorm` 统一响度。
5. **成片校验**：把成片重新转写一遍，和 cue 表对比时间差。

## 常用命令（示例，按项目调整）

```bash
# 本地中文 TTS（安装：uv tool install mlx-audio 或在项目 venv 里 uv add mlx-audio；模型名以 mlx-audio README 为准）
# 词级时间戳：whisper.cpp（brew install whisper-cpp）或 FunASR（uv add funasr）
# 响度标准化到 -14 LUFS（短视频平台常用）
ffmpeg -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 mix_norm.wav
# 视频与音轨合成
ffmpeg -framerate 30 -i out/frames/f%05d.jpg -i audio/mix_norm.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest out/final.mp4
```

mlx-audio 和 FunASR 的具体调用方式以各自 README 为准，第一次用时读一遍再写脚本，并把可用的命令记进项目的 `LESSONS.md`。
