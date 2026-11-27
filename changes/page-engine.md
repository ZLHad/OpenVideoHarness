**不用引擎也能开片：`bin/vh new … --engine page`，只守页面合约，怎么画由 agent 自己定**
- Why: 仓库的取帧、出片、检查和审阅本来就只认页面合约 `window.film`、不认引擎，可开片时只能按类型分到一个引擎，没有一条路通向"自己写一个页面"；现在的模型几十行代码就能写出一个只由 t 决定的页面，按类型分配引擎、开工前读完类型文档，反倒把它往同一种做法上推。只守底线的那组片子在研究笔记 06 的盲评里两次被选去发布。
- `bin/vh new <type> <slug> --engine page`：任何类型、任何画幅（`--aspect`，4K 渲染时 `--dpr 2`），复制一个按合约写好的占位 `film.html`（尺寸按 BRIEF 的 Output 写好，带种子随机、缓动和按旁白字词取时间的 `at()`）和它的说明 `ENGINE_README.md`，不装任何依赖。BRIEF 的 Engine 一行写 `page`。
- 新的说明卡 `engines/page/README.md`：合约的几个字段，取帧、出片、只重画几秒、分镜、字体检查和声音的命令，CLAUDE.md 底线里有命令在查的那几样各由哪条命令查、没有命令能查的几样要自己盯，时间怎么从旁白、音乐和事件表里取，动手前先用三种明显不同的做法各画一帧再挑，交之前看什么，想用组件、Three.js 和剪辑表时怎么拿进来。
- CLAUDE.md 路由表下面加了"不用引擎"：用户说"自由发挥""不用照模板"，或者没有贴切的类型时走这条路，开工前只读那张卡，类型文档、playbook、配方、风格按需用 `bin/vh know` 查，档位、关卡和底线照旧。`playbook/00` 的引擎选型表、`engines/README.md`、quick 卡各加了一处。
- `bin/vh status` 认得 page 项目：必读从类型文档和 quick 卡换成那张卡（关卡要用的几节照旧），写场景时只列命令查不到的几节（预算、事实核查、有声片的音频 QA），出 4K 终版时带 `--dpr 2`；`tools/readpath.py` 的读量表多了一行 page。`bin/vh components add` 给 page 项目的提示是直接 `import`。
- 修了一处 `bin/vh textcheck` 的毛病：不是 HyperFrames 的页面，它只认 `data-width`，竖屏、方形的页面会按 1920×1080 去查；现在和出片的宿主一样，先看 viewport，载入后以 `window.film` 给的尺寸为准。
