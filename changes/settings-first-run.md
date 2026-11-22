**少了 API Key 时，命令和 Studio 都用一句话说清去哪设、去哪拿、不用它还能怎么做**
- Why: 配音、对时间、出图、作曲缺 key 时，原来各说各的（"set GEMINI_API_KEY (Google AI Studio → Get API key)"），只说了环境变量；Studio 里只看得到"配音结束时报了问题"，人不知道片子在等什么、该去哪里补。
- 缺 key 停下的命令（`bin/vh tts` 各家、`--align gemini`、`voices audition`、`pace --align gemini`、`music --provider lyria`、`image gen`）都说同一句：哪一家、哪个 key，在 Studio 的设置 → 服务里填上（或者设环境变量），去哪拿，不用它时这台电脑上还能怎么做（本地配音、本地对时间、本地作曲）。这句由 `tools/keys.py` 写，记进这次运行的记录，代码是新的 `no_key`。
- `bin/vh status` 和 Studio 的现状行在片子等 key 时说："配音停下了：还没有 Gemini 的 API Key。在设置 → 服务里填上，再让 agent 接着做。"Studio 里那一行带一个按钮，点了直接到设置 → 服务。key 设上了（Studio 里或环境变量里），或者同一条命令再跑一次没为它停，这句就不说了。
- 不花钱：检查在调用之前，什么都没调就停。
