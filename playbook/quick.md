# quick 路径卡

用户要 `quick` 时（档位怎么定见 CLAUDE.md"努力程度"），不用把各步列的文档都读完，照这张卡做。人点名要拍板的事照样停（CLAUDE.md"导演模式"）；其余都是 `delegate`。底线照旧（CLAUDE.md"任何档位都不降的底线"）。

1. **读**：路由表对应的类型文档，只读"工作流"和"禁止"两节（"Prompt 增量块"是这类片子的默认做法，挑定立意以后再读）；再读 `engines/README.md` 里对应引擎的一节，HyperFrames 先看其中的"最小写法"。
2. **建项目和立意**：`bin/vh new <type> <slug> --effort quick`。先答 `playbook/12-ideation.md` 第 3 节的四个问题，写 3 个一句话立意（至少一个估在一成以下），挑一个，再写一行刻意没选的最典型做法（第 7 节最后一条）；然后读类型文档的 Prompt 增量块，决定留哪些默认，留下的写进 BRIEF。风格从立意推出来；想参考预设就 `bin/vh style apply <preset[,preset]> <project>`（`bin/vh style list` 挑），副本放进项目的 `style-refs/`，写 STYLE.md 前翻一遍；借了什么在 `DECISIONS.md` 记一行，和它不一样不用解释。立意和风格各写一行理由进 `DECISIONS.md`；改了哪些口味默认，交付时一并列出。
3. **写**：补齐 BRIEF；分镜只写简表（镜头、时长、reads）；然后写场景代码。HyperFrames 写完一段，用 `npx hyperframes snapshot --at <秒> --describe false` 看几个关键时刻。
4. **出片**：HyperFrames 先 `export HYPERFRAMES_SKIP_SKILLS=1 DO_NOT_TRACK=1`，再 `npx hyperframes render --quality draft --output out/draft.mp4`；用 `&` 或 `nohup` 放到后台、命令在渲染结束前返回时，在那一行前加 `HYPERFRAMES_RENDER_DETACHED=1`，否则 shell 一退出，渲染就自己取消（`engines/README.md`）。手绘类用 `node render.mjs --clip --out=out/draft.mp4`。
5. **自查一遍**：`bin/vh sheet out/draft.mp4` 看整片联系表，对着 `TASTE_CHECKLIST.md` 的 20 条速查；有字就跑 `bin/vh readcheck`。再看两样（命令见 `playbook/02-verification.md` 的"手机测试"）：一张按目标屏缩的联系表（BRIEF 的 `Watch on`：phone、feed 缩到 360 px 宽，desktop 缩到 640），必读字读不读得出，读数、标签别贴着下限；前 2 s 的逐帧 strip：要进信息流的片子，看是不是第 0 帧就在动、有没有让人停下来的东西。`quick` 没有 reviewer，这两样最容易漏（`docs/research/06-concept-first-ab.md`）。
6. **声音**（要的话）：`bin/vh music` 或 `bin/vh tts`，再 `bin/vh mix`、`bin/vh qa`、`bin/vh mux`。
7. **交付**：自查过了就出正式画质（HyperFrames `npx hyperframes render --quality delivery --output out/final.mp4`），档位只管迭代多少，不降成片的画质；`bin/vh check` 必跑；交 mp4 路径、联系表、自己最不满意的 1–2 处，以及 `DECISIONS.md` 里要人看的几行：选了哪个立意、刻意没选的最典型做法、改了哪些口味默认。
