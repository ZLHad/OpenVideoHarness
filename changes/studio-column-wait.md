**Studio 的对话列跟得上 agent 在后台等这一站**

- 对话里的 agent 把等这一站的命令放到后台、这一轮结束以后，这一列写"片子等你拍板"，不再是"空闲"。
- 你点"交给 agent"以后，Claude Code 自己接着做的那一轮，这一列当成在做：有停止按钮，拿着片子的锁，做完放掉；记录里写一句"你交了意见，Claude Code 自己接着做了"（只在这支片子的意见刚交到它手里时；别的时候只说它自己接着做了一轮）。Codex 和 DeepSeek Harness 没有这一轮，照旧在这一列说一声。
- Studio 开着时，`standard` 档的片子停下来等你的那一步也开在 Studio 里：`bin/vh gate` 看到 Studio 在跑才这样（不会为此起 Studio），带 `--wait` 时你点"交给 agent"它就接着做；Studio 没开、或者接不下这支片子时照旧出静态审阅页，`--wait` 这时退出 5，告诉 agent 这一轮没人答复、在聊天里等你回；`quick` 不变。agent 给你的那句话直接说是哪一站、点"交给 agent"，不带命令。
