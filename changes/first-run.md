**安装更轻，最后一屏只说第一支片要知道的事；几个 GB 的第一次下载都先说一声**
- Why: 在干净的机器上量过，安装 90 秒里有 71 秒、305 MB 在拉参考仓库，而第一支片用不到它们；安装最后一屏是 60 多行 doctor，十几行黄色提示大多和第一支片无关，Linux 上真挡路的缺项淹在里面，最后照样说"ready"；本地配音第一次用要静默下载约 2.6 GB。
- 37 个参考仓库安装时不再拉：agent 用到文档指的那一个时再拉，`references/fetch.sh <目录>` 拉之前用一行说清拉什么、从哪、多大（大小表在脚本里，CI 查每一个都有）；指名的那一个没拉下来就退出 1，名字写错退出 2；拉全部时断网只说一行。`install.sh --refs` 一次拉全；`--no-refs` 照旧认，现在就是默认。之前拉过的留着不动。`bin/vh doctor` 不再把没拉的参考仓库当成缺项。`bin/vh setup` 仍然拉全部，先说约 300 MB。
- 安装最后几行换成 `bin/vh doctor --first`：能不能做第一支片，缺什么、一句怎么补（Node、FFmpeg、Python 3、uv、能渲染的浏览器和它要的系统库、一个 agent；中文环境下还有中文字体），配音在这台机器上怎么来；有缺的就不说 ready，没法检查的（Linux 上问不到浏览器的系统库）说"没检查"，也不说 ready。完整报告照旧是 `bin/vh doctor`。安装前就要 python3。skill 注册只说一行。示例句跟着你的语言：中文环境是 README 那条无声 15 秒，其他是它的英文版。skill 里写明：安装看最后几行，不看退出码。
- 几个 GB 的第一次下载，开始前都先说一行：约多大、大概多久、显示进度，以及不用下载的办法。本地配音（`bin/vh tts`、`voices audition`）约 2.6 GB，`--provider edge` 只要一个小包（免费，在线：稿子会发到微软的配音服务）；本地 Whisper（`tts`、`voices audition --align local`、`pace --align whisper`）约 3.6 GB，`--align gemini` 不用下载。Python 包的下载逐个显示，模型下载每 10 秒说一次下了多少（输出给 agent 看、或者外面关了进度条时）。大小只记在 `tools/audio/firstuse.py` 一处，doctor 也从那里读。`bin/vh tts` 先查稿子：没有稿子时写一份示例就停，一个包都不下。
- 默认配音只在 `tools/audio/tts.py` 的 `DEFAULT_PROVIDER` 一处设，`bin/vh tts` 问它。
- doctor 找本地配音模型时也看 `XDG_CACHE_HOME`（Hugging Face 自己就这样找）。
- README 中英文和官网的安装大小按实测更新：安装约 400 MB，`--refs` 再约 300 MB，本地配音约 2.6 GB，本地 Whisper 约 3.6 GB。
