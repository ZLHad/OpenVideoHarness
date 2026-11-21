**安装更轻，最后一屏只说第一支片要知道的事；本地配音第一次下载前先说**
- Why: 在干净的机器上量过，安装 90 秒里有 71 秒、305 MB 在拉参考仓库，而第一支片用不到它们；安装最后一屏是 60 多行 doctor，十几行黄色提示大多和第一支片无关，Linux 上真挡路的缺项淹在里面，最后照样说"ready"；本地配音第一次用要静默下载约 2.5 GB。
- 37 个参考仓库安装时不再拉：agent 用到文档指的那一个时再拉，`references/fetch.sh <目录>` 拉之前用一行说清拉什么、从哪、多大（大小表在脚本里，CI 查每一个都有）；名字写错时说清并退出 2。`install.sh --refs` 一次拉全；`--no-refs` 照旧认，现在就是默认。之前拉过的留着不动。
- 安装最后几行换成 `bin/vh doctor --first`：能不能做第一支片，缺什么、一句怎么补（Node、FFmpeg、Python、uv、能渲染的浏览器、一个 agent），Linux 上缺中文字体也说，配音在这台机器上怎么来；有缺的就不说 ready。完整报告照旧是 `bin/vh doctor`。skill 注册只说一行。示例句换成 README 那条无声 15 秒。
- `bin/vh tts` 用本地配音、第一次要下载时，先说一行：约多大、大概多久、显示进度，以及不用下载的办法（`--provider edge`，免费，在线：稿子会发到微软的配音服务）；Python 包的下载逐个显示，模型下载每 10 秒说一次下了多少。默认配音只在 `tools/audio/tts.py` 的 `DEFAULT_PROVIDER` 一处设，`bin/vh tts` 问它。
- doctor 找本地配音模型时也看 `XDG_CACHE_HOME`（Hugging Face 自己就这样找）。
- README 中英文和官网的安装大小按实测更新：安装约 400 MB，`--refs` 再约 300 MB，本地配音约 2.5 GB。
