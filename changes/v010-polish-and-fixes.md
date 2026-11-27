**v0.10.0 前收尾：修 5 处小毛病，润色 README 和官网**
- Why: 发 v0.10.0 前把近期真片子暴露的 5 处细节问题一次清掉，并把 README 与官网里过时的表述和互动细节补齐。
- 已交付片子认准通过检查的正式成片（`tools/status.py`）：按 `bin/vh check` 通过判定交付时记下对应成片路径，并在有多个通过的成片时优先非 `-silent` 版；不再退回去把更新的局部小样或无声循环版当成正式成片。
- 本地 Whisper 对时（`bin/vh tts --align local`）在 `timeline.json` 里如实记录本机 Whisper 模型名，不再写成 `gemini-3.5-transcribe`；`BRIEF.md` 的 `Output:` 行里括号说明自带的时刻（如 `23:42 改稿`）不再盖过主干里的片长（`tools/gatecheck.py`）；`bin/vh` 一处裸写 `mktemp -d` 补齐 `${TMPDIR:-/tmp}`；`CLAUDE.md`（同步 `AGENTS.md`）顺清"不用审、直接出"与默认档位的断句。
- 关卡 ① 没有立意卡（立意已由人定）的静态审阅页只挂大纲模块，不再先摆满屏素材、不再显示"等你挑一张"或混入旧的 `gate-1.json` 卡片（`tools/review.py`、`tools/desk/static/modules.js`）；`tools/ci.sh` 里信号检查的替身 `uv` 去掉 `sleep 0.05` 循环改用可中断 `wait`，消除 macOS 慢机器上的偶发超时。
- README 和官网：补全"API Key 也可存在 Studio 钥匙串"的口径、给需求示例补上第 12 类产品教程、拆清安装缓存与国内镜像两段说明；官网把残留的 5 处"Claude"统一为"agent"、同步"选模型和思考深度"用词、组件区换上新组件 `ui-stage` 联系表；风格墙中央主画面加上自动轮播进度细线，灯箱里打开风格支持 `←` / `→` 翻看全部 43 种风格并在关闭后还原焦点，统一卡片悬停聚光与视频播放键动效，"一镜到底"补上悬停反馈与开屏滚动提示线。
