# 04 音频

原则：**先有音频，再有时长。** 要先把音频变成时间表，agent 才能处理：旁白要有词级时间戳，音乐要有节拍网格，歌曲要有逐句歌词时间。

## 现成接口：`bin/vh tts / beats / mix / mux`

音频层已经封装成统一接口，服务商可以替换，其余流程不变。依赖由 `uv run --with` 临时提供，不装进全局环境；**API key 只从环境变量读取**。

```bash
bin/vh tts projects/<p> say Tingting        # 旁白：audio/script.txt → audio/voiceover.wav + audio/timeline.json
bin/vh beats projects/<p>/audio/music.mp3    # 节拍：→ music.beats.json（bpm、offset、beats、downbeats）
bin/vh mix projects/<p>/audio/voiceover.wav projects/<p>/audio/music.mp3 projects/<p>/audio/mix.wav   # 人声出现时压低音乐，并统一到 -14 LUFS
bin/vh mux projects/<p>/out/final.mp4 projects/<p>/audio/mix.wav projects/<p>/out/final-audio.mp4   # 给成片配音轨，时长与视频一致
```

**旁白稿格式**（`audio/script.txt`）：一行一句，一句对应一条字幕或一个 cue；`#` 开头的是注释；可以加 `@id` 前缀，比如 `@hook 为什么信号会变调？`。按句合成的好处是每句的起止时间是**实测**的，画面和字幕可以直接按 `timeline.json` 对齐。

**配音服务商**（第二个参数）：

| provider | 用途 | 需要什么 | 时间精度 |
|---|---|---|---|
| `say` | macOS 自带，离线、免费，用来打草稿、跑通流程（中文音色：Tingting、Eddy、Flo…） | 无 | 句级 |
| `edge` | 微软 Edge 在线音色（zh-CN-XiaoxiaoNeural 等），免费 | 联网；非官方接口，可能失效 | 句级 |
| `elevenlabs` | 高质量多语种配音 | `ELEVENLABS_API_KEY`；第三个参数填 voice_id；`ELEVENLABS_MODEL` 可选 | **字符级**（with-timestamps） |
| `dashscope` | 阿里云百炼 Qwen3-TTS（默认 `qwen3-tts-flash`，音色如 Cherry），中文和方言强 | `DASHSCOPE_API_KEY`；国际站设 `DASHSCOPE_BASE_URL`；`DASHSCOPE_TTS_MODEL` 可选 | 句级 |
| `mlx` | 本地 Qwen3-TTS（Apple Silicon，mlx-audio），离线、免费 | `MLX_TTS_MODEL`（如 `mlx-community/Qwen3-TTS-12Hz-0.6B-CustomVoice-8bit`）；**首次运行会下载 GB 级权重，先征得用户同意** | 句级 |

需要字级时间戳（逐字高亮字幕、按词触发画面）时有两条路：用 `elevenlabs`，或者对句级结果再跑一遍强制对齐（FunASR、whisper.cpp，或 mlx-audio 的 Qwen3-ForcedAligner）。

**音乐**：
- **Suno**：没有官方公开 API（二手信息，UNVERIFIED），不接非官方封装。做法是用户在 Suno 生成、下载，放进 `audio/`，再跑 `bin/vh beats`；需要歌词时间时，按下文"歌词对齐"一行的流程处理。
- **API 接口位**：ElevenLabs 的音乐和音效接口已经预留，还没实现。需要时在 `tools/audio/` 下加一个 provider。
- **代码合成**：用 Web Audio 或 numpy 程序化生成 BGM 和音效，这样确定性最好，适合极简风格。

**已实测**：`say` → `beats` → `mix` → `mux` 离线全链路可用；混音结果 -14.1 LUFS。`edge`、`elevenlabs`、`dashscope`、`mlx` 按官方文档实现，但因为没有 key 或没下载模型，**还没实测**。第一次使用时把可用的命令记进项目的 `LESSONS.md`。

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
