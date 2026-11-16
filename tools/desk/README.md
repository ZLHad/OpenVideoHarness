# 审阅台和控制台（bin/vh desk）

审阅台是一个本地网页控制台，样子是 Studio 的外壳：左边一列模块，顶上这支片子走到哪一站，右边一列分两页：和这台机器上的 agent 说话（Claude Code、Codex、DeepSeek Harness），以及这一轮要人定的事和人的点评。不带项目打开，是这台机器上所有片子的空间；进了一个项目，打开在等人的那一站（立意、分镜或成片），成片模块把片子、镜头、旁白、音乐、检查和点评排在一条时间线上。人点卡片选选项、选中一处写一句、提交；agent 在后台等着，人一提交就接着做。它是 `studio` 档位默认的审阅界面，`standard` 想用也可以（什么时候用、agent 怎么挂等待，见 `playbook/01-pipeline.md` 的"审阅台"）。这一页讲它读什么、写什么，也就是项目文件要怎么写，审阅台才排得出来。

**文件是唯一的事实来源。** 审阅台每次刷新都从项目文件重新读，自己不存状态；人的草稿只留在浏览器里，提交以后才落进项目。读不出结构的文档不会被藏起来：每份文档都在"文档"页原样排版，结构化的页面空着时，就地显示那份文档的原文，"文档"页顶上列出哪些没按约定读出来。

## 命令

```bash
bin/vh gate <项目> <n> [--desk|--page|--chat] [--wait]   # 一次停一条命令：查 gate-<n>.json，出静态页并记成这一轮，审阅方式是审阅台时在后台起服务（12 小时没人访问自己停），打印聊天消息；--wait 再像 desk wait 一样等
bin/vh desk [--root 文件夹 …] [--port N] [--no-open]   # 控制台：bin/vh projects 找得到的所有项目（$OVH_PROJECTS、<仓库>/projects、每个 --root）；在终端里起时，起好就在你的浏览器里打开它的控制台地址（--no-open 不开），agent 起的只打印地址；同样的 roots 已经有一个在跑，就只打印它的地址
bin/vh desk <项目> [--root 文件夹 …] [--port N] [--idle 秒] [--only]   # 同一个页面，打开在这个项目上，空间里照样有 roots 下的每一支片子；只听 127.0.0.1；默认 8780–8799 里第一个空闲端口；这个项目已经有一个在跑，就只打印它的地址；--idle：这么久没人访问就自己停；--only：只服务这一个项目（bin/vh gate 在后台起的就是 --only --idle 43200）
bin/vh desk wait <项目> [--timeout 秒]          # 等人提交：打印反馈，退出码 0；超时退出码 3（默认 7100 s）
bin/vh desk feedback <项目> [--round 1b] [--json]   # 打印最近一次提交，并记为"已交给 agent"
bin/vh desk data <项目>                        # 审阅台从项目里读出了什么（JSON），排查"为什么这一页是空的"时用
bin/vh desk link [<项目>] [--root 目录 …] [--force]   # 要一个新的控制台地址（页面说只能看、或者地址找不到时）：停掉在跑的那一个，照原样再起，打印新地址，在终端里直接打开浏览器；旧地址不再能操作
bin/vh desk agents [--json]                    # 右栏能和哪几家 agent 说话：装没装、钉的版本、装在哪
bin/vh desk agents install <claude|codex|dsh>  # 装那一家的 ACP 适配器（版本钉死），装在仓库外面：$OVH_AGENTS_DIR，没有就是 $XDG_CACHE_HOME/ovh/agents
```

只用 Python 标准库，不联网，页面不构建、不从 CDN 拉任何东西、不下载字体（只用系统字体），三套深色主题（暗场默认、棱镜、舰桥），界面有中文和英文。

**关卡视图只有一套。** 静态页（`bin/vh review`，file:// 直接打开，不起服务）和审阅台里的这一轮，是 `tools/review.py` 写的同一份标记，用同一个样式表 `static/ui.css` 和同一个脚本 `static/ui.js`（静态页把两个文件整个内嵌进去）：画面在前（播放器和它下面的标尺、立意卡并排、或者分镜的镜头格），决定是能点的卡（推荐的预先选上），没把握的地方是标尺上的记号和一条一句，已经定了、替人定了、材料和附录收起来只露条数。两处的差别只有最后一步：静态页是一句跟着选择变的回复，复制回聊天；审阅台是一个提交按钮。改样子改一处，两处一起变。颜色全是 `ui.css` 里的变量，三套主题各是一块取值（见下面的"主题"）。

**静态页也是这一站模块的只读版。** 关卡 ① 的静态页在关卡视图上面画立意和大纲，② 画分镜，E2、E3 画声音，用的是控制台同一套渲染（`static/core.js`、`modules.js`，加一个只给静态页的 `static/static.js`），数据是 `bin/vh review` 出页时按控制台的读法（`server.project_data`）读出来、只留这一站用得上的那些，写进页里的一个 JSON 块；文件地址相对页面所在的文件夹。没有写点评的框，什么也不发：模块上的立意卡和下面关卡视图里的同一件决定联动，回复照旧复制回聊天。模块已经画了的（立意卡、分镜格），关卡视图里藏起来，不再画一遍。关卡 ③ 和 E4、E5 没有模块：关卡视图的播放器和标尺就是成片模块的静态版。不开 JavaScript，或这个项目读不出来（老项目里缺这缺那），页面还是原来的关卡视图。

`bin/vh gate`（`tools/gate.py`）把一次停要做的事做完：审阅方式取 `--desk` / `--page` / `--chat`，没有就取 `LOCAL.md` 的"审阅方式"一行，再没有就按档位（`studio` 审阅台，`standard`、`quick` 静态页）。每种方式都出静态页、打印聊天消息；审阅台方式再起服务，把地址加进消息。退出码：0 发出去了（`--wait` 时是收到了提交）；1 页面写了但不合规矩，不发消息也不起服务；2 没东西可发（没有 gate JSON、服务起不来、不是审阅台却要 `--wait`）；3 `--wait` 超时。

**一站的数据就是 `out/review/gate-<n>.json` 这一个文件。** 静态页（`bin/vh review`）、审阅台和以后的客户端都只渲染它（审阅台另外读下面这些项目文件），各自不另存一份。

## 控制台：Studio 的外壳

`bin/vh desk` 打开的是 Studio（`docs/proposals/02-studio-client.md`）的外壳。右栏能直接和本机的 agent 说话（见下面的"agent 那一列"）；计划卡、结果卡、两版对比、按次退回、从一句话直接新建这一版还没有，位置留着。

- **外壳**：左边一列模块（空间、立意、大纲、分镜、声音、成片、交付、素材、账本；有一站在等人时，它的模块亮一个琥珀点）。顶上一条流程：立意 ① · 大纲 ① · 分镜 ② · 声音 · 成片 ③ · 交付，每一站的灯取这支片子自己的停（`bin/vh status` 的 stations）：过了是绿，等你是琥珀，agent 在做是紫，还没到是灰，这支片子不在这一站停是一个空心的点。右边一整列见下面。
- **空间**（`#/`）：上面一个写一句话的框，写好复制给自己的 agent（这一版不直接新建）；下面一张卡一支片，等人的在前，卡上写等人定什么；鼠标停在卡上，卡上的片子静音播 4 秒。卡上的画面按这个顺序取：等人时取这一轮要人看的（第一张立意卡的帧，没有就是它的片子、第一张图、第一个关键帧）；不等人时取封面（`out/final/covers/`、`out/final/cover*`、`out/review/cover*`），没有就是当前成片的中间一帧（浏览器自己从视频里取，服务不跑 ffmpeg），再没有是分镜关键帧，最后是 `out/review/`、`out/check/`、`out/frames/` 里最新的一张图。
- **一支片子**（`#/p/<键>[/<模块>]`）：打开在等人的那一站的模块（关卡 ① 立意，② 分镜，③ 成片）；没人等时打开正在做的那一站，再没有就是成片。关卡不再是另一页：等人那一站的模块就是这一轮的关卡页，要你定的事在右栏。照原型排的模块自己画关卡页的画面（立意卡、镜头），关卡页里其余的东西（替你定的、附录、别的图）接在模块下面；成片模块把关卡页的画面放在它的时间线上。`#/p/<键>/gate/<页>` 打开那一页所在的模块，之前的页只看不交。
- **其余模块**照原型排（`static/modules.js`、`modules.css`），画面在前，字少；每样东西都能选中再写点评，点评带着它是什么。数据只来自已有的命令和项目文件，缺的那一块照实说空，写上做它的命令。
  - **立意**：左边是 NOTES.md 素材清单里只属于这个题目的东西，按数字、物件、原话、矛盾、意外分组，和「点子」里那条同题的视频常见的样子；右边是最新一页关卡 ① 的立意卡（带画面的那件决定），各配一帧。关卡 ① 开着时，"选这张"就是这一轮的决定，和右栏同步；"再想一张像它的"要 agent，这一版把这半句话放进写点评的框。还没有关卡 ① 的页时，显示 BRIEF 写下的立意。
  - **大纲**：BRIEF 大纲表按时长比例的段落条和段落卡（要看懂什么、画面、几处没把握），旁边是 BRIEF 的立意、主线、在哪看、规格这些行，和引擎、配音、已花、预算、停在哪。页签：大纲 · 字幕 / 旁白 · 事实（后两个是原来审阅台的视图）。
  - **分镜**：有关卡 ② 的页时，照那一页排：一个段落一页，段落的编号、时间和备注，每镜看到什么、旁白、没把握的（关卡页的 `least_sure`，`S04` 和 `S4` 算同一镜）、默认改什么，段落的配图；人审的是 agent 送来的那一页，所以那一页有的这里都有，`shots.json` 只补那一页没给的画面和时间。没有关卡 ② 的页时，`shots.json` 的镜头按大纲的段落分页，每镜写着 reads 和转场，没把握的是 `unsure`。有灰盒 animatic（`shots.json` 的 `video`，`out/animatic.mp4`、`out/draft.mp4`）就播这一页那一段，点一镜播那一镜；不在的文件写明不在，不去请求。其余默认通过。
  - **声音**：四个读数：响度、真峰值（最近一次 `bin/vh check` 的 `check.loudness`），语速（`bin/vh pace` 写进旁白时间轴的 `pace`，只算有声的部分；没跑过 pace 时按句首到句尾算，写明含句中停顿），数字静音（`check.silence` 的条数）。试听音色（最新的 `audition.json`，`bin/vh voices audition` 写的；旁白用的那个标"在用"），旁白逐句的语速和句后停顿（比中位数快或慢得多的标出来），然后是两条时间，不混着画：成片的时间上是成片的响度（`bin/vh peaks`）、这一轮请你听的地方和检查里关于声音的问题，点一下从成片那一秒播（听的是混好的声音）；配乐的时间上是它的段落、候选落点（`bin/vh beats` 的 lifts）和计划的音效，点一下从配乐那一秒播。缺哪样就说缺，写上做它的命令，不画空图。换音色、重念要 agent，这一版写成点评。
  - **交付**：竖横封面（PACKAGING.md 封面表的原图，`out/covers/`、`out/final/covers/`）；各平台的标题、简介、标签（PACKAGING.md 的「发布文案」，和 `bin/vh check` 量长度时读的是同一份，`tools/packcheck.py`），章节，标题候选和里面的事实核过没有；会出什么（母版、上传用的副本、字幕、封面、各平台文案，各自出了没有）；出片前检查按类归组（安全框和字号、字被光烧白、响度、静音闪白黑场冻帧、许可、文案）。页签：交付 · 检查 · 版本。
  - **素材**：素材台账（`assets/ledger.json`）的每一件：许可（`Assets: strict` 收下的是绿，生成的是紫，其余琥珀，标"许可没清"）、来源、用在哪一镜、文件在不在；`research/refs.json` 的参考，和 `bin/vh ref digest` 读成的文稿（`research/digest/<id>/transcript.md`），点开就是那个文件。按类筛（什么都没有时不摆筛选）。没有 `assets/ledger.json` 的老项目，读 NOTES.md 里旧模板的「素材台账」表（文件、来源、许可三列，2026-10-26 以前的模板带着它），只读列出，写明来自 NOTES.md；登记进台账才查许可、出署名。登记要 `bin/vh assets add`、`bin/vh ref add`，这一版不接 agent。
  - **账本**：DECISIONS.md 的决定表和 agent 定的事：谁定的、什么时候、为什么（人定的那几件附 REVIEW.md 那一关的原话）；agent 定的每一条有"翻案"，这一版写成点评。你的原话（REVIEW.md 逐字记的），`bin/vh versions` 的每一版改了什么。页签：决定 · 历史 · 文档。
  - **新建**要 agent，这一版没有，位置留着：模块栏里的"新建"打开空间页那个写一句话的框（拼好一句话，复制给自己的 agent）。
  - **点评对着什么**：有 target 的（`card:`、`seg:`、`shot:`、`fact:`、`asset:`、`led:`、`doc:`、`range:`、`atime:`、`time:`、`concept:line`）照 target 记；没有 target 的（一个读数、一个音色、BRIEF 的一行、一条检查）记进这一轮的整体意见，前面带上它的名字，比如 `〔声音 · LOUDNESS〕`。页面只做 `feedback.py` 收得下的 target 和标签：控制字符去掉，太长的名字截短，项目外的路径和倒着的时段不当 target（它们记进整体意见）；提交前再查一遍，收不下的那几条列在提交单上、不发，不会让整轮被拒。反馈文件的格式不变。
- **成片模块**（提案第 4 节）：左边是列表（镜头、旁白稿、点评、检查），中间是画面：四周中性灰，上面一行等宽字的读数（哪一镜、要看懂什么、尺寸、帧率、第几版）；左边和中间的下面是时间线，三组轨道：画面（章节、带缩略图的镜头）、声音（旁白、音乐的段落和节拍、卡点、波形）、审阅（你的点评，agent 没把握和请你听的记号，检查查出的问题，这一版改了哪里）。点一下选这一秒，拖一下选一段，点镜头或章节选中它；`I` `O` 设入点出点，拖的时候吸附到镜头边界、节拍、旁白和记号，`N` 跳到下一处要看的，空格播放（选了一段就只播这一段），`←` `→` 逐镜（选中那一镜，和点它一样：写点评的框跟着换），`,` `.` 逐帧、`Shift` `←` `→` 一秒一秒走（选着的是一秒时，那一秒跟着走），`C` 在这一秒写一条。三种布局：审片（画面最大，只留主轨道；关卡 ③ 打开就是它）、精修、听声音（旁白稿和声音轨道放大，波形最高，按全片最响的地方画满）。窄屏（手机）上先是画面，接着是右边一列（要你定的、提交），再是时间线，列表在最后。有留着的上一版时，可以和它擦着对比（只看）。数据都来自已有的命令：`bin/vh timeline --resolved`（镜头、章节、旁白、节拍）、`bin/vh thumbs`（拖动时每一秒的画面、镜头图）、`bin/vh peaks`（波形）、`bin/vh check`（问题和它们的时间）、`bin/vh versions`（第几版、改了哪里、上一版）；缺哪样，那条轨道就照实说空，写上做它的命令。没有成片时，画面是分镜的关键帧，没有关键帧就是联系表；要的那支片子不在了（移走、改名、在别的硬盘上），画面下写明是哪个文件。页面从不请求不在的文件：关卡页里引用的文件不在了，那里写"文件不在了"，不给链接；镜头的关键帧不在，就当没有。
- **右边一列**：这一轮要你定的事（关卡页的选项卡，能点，推荐的预先选上，`1`–`9` 给当前这件选第几个），它最没把握的和请你听的（点一下到那一秒），你的点评（点一下回到那一处，× 删掉），下一步、正在跑的命令和花费（`bin/vh status` 写给 agent 的英文，中文界面里认得的说成中文，不认得的照原话、标明是它的话；项目文件夹写成 `<项目>`），一个"提交这一轮"，和一个写点评的框：对着什么，就是模块里选中的那一处（一秒、一段、一个镜头、一章、一个记号、一张卡），没选就是整个模块（记进这一轮的整体意见）。右栏顶上两页："对话"是和 agent 说话（下面一节），"这一轮"是上面这些；这一轮有要你定的事时先打开"这一轮"，agent 等你点头时"对话"上亮一个琥珀色的数。
- **提交**：先列出每件决定选了什么（没动的标"按推荐"）和每条点评，可以再写一句整体意见；走的还是 `POST …/feedback` 这一条通道，`bin/vh desk wait` 照样被唤醒。服务没起来时，回复复制到剪贴板。每次提交是一份反馈文件、REVIEW.md 里一节，所以一样东西只交一次：交上去的点评从草稿里拿掉（右栏写"已交 N 条"），决定交过以后只有改了选项才再交；写了一半没记下的字照留。交完重新读项目时，原来的画面留在屏幕上，新数据到了才换。
- **输入框**：`Esc` 离开输入框（写的字留着），`⌘↩` 记下一条后也离开，接着按 `N`、`←` `→`、空格都是给片子的。
- **主题**：暗场（默认）、棱镜、舰桥三套，顶上切换，浏览器记住；三套是 `ui.css` 里同一组语义变量的三块取值，默认用哪一套是 `ui.js` 里的一个值（`DEFAULT_THEME`）。四条规矩不随主题变：画面四周是中性灰；读数用等宽字；颜色只说谁、在发生什么（青是你选的和标的，紫是 agent，红是播放头、出错和正在发生，琥珀是等你，绿是过了），其余是灰；只有深色。
- **关卡页的标尺**（静态页和模块下面的关卡页）：有镜头表（关卡页自己的分段和镜头，或项目的 `shots.json`、剪辑表）时标镜头和分段；都没有时用 BRIEF 大纲表的段落和时间；大纲也没写时间时，只是一把带秒刻度的尺子，加上没把握和请你听的记号。
- **键盘**：`/` 搜片子（↑↓ 选，回车打开，Esc 关）；成片模块的见上面；关卡页里空格播放，`←` `→` 跳镜头，`1`–`9` 选选项。

### agent 那一列

右栏的"对话"页直接和这台机器上的 agent 说话：Claude Code、Codex、DeepSeek Harness，各自用它们的 ACP（Agent Client Protocol）适配器。服务端 `agents.py` 是会话管家，`acp.py` 是只用标准库的 ACP 客户端（`acp_guard.py` 是它给每个适配器配的看门进程），`agentlock.py` 是项目锁；页面是 `static/agent.js`、`agent.css`。

- **装法**：`bin/vh desk agents install <claude|codex|dsh>` 用 `npm ci` 照仓库里的锁文件（`agent-locks/<家>/package-lock.json`：整棵依赖树钉死，每个包带完整性校验；Claude 和 Codex 的树里没有安装脚本，装时加 `--ignore-scripts`；DeepSeek Harness 有五个要编译或取本机模块的包得跑脚本，名单写在 `agents.py` 里，CI 对着锁文件查，多一个就不过；锁文件里每个包都从 `registry.npmjs.org` 取，CI 也查）把适配器装到仓库外面（`tools/modules.json` 的 `claude-agent-acp`、`codex-acp`、`dsh-acp`；`bin/vh doctor` 列出装没装）：Claude 的约 0.4 GB，Codex 的约 0.4 GB，DeepSeek Harness 的约 1.4 GB。没装时这一页写出要运行的那一行。适配器用你自己的登录，不用也不存任何 key。DeepSeek Harness 另起一个配置目录（装的地方下的 `home/`），只读地引用你 `~/.dsh/.credentials.yaml` 里的凭据，默认模型取你桌面版的设置，不动 `~/.dsh`。想走镜像，自己设 npm 的 registry（`npm config set registry …`）：npm 会把锁文件里 `registry.npmjs.org` 的地址换成你设的那个，完整性校验照样查。DeepSeek Harness 那五个安装脚本里，koffi 和 node-pty 用包里带的预编译二进制（在校验过的包里）；没有合这台机器的，就地编译，编译时 node-gyp 会下载 Node 的头文件，这一步下载的东西不在锁文件的校验里。
- **进程**：每家一个常驻的适配器进程，第一次说话（或开一个新对话）时才起，进程组单独一个；会话按项目文件夹分，agent 的工作目录就是这支片子的文件夹。起进程用干净的环境：只留 `HOME`、`USER`、`PATH`、语言这几样，不带任何 API key，也不带宿主的 `ANTHROPIC_*`、`CLAUDE_CODE_*` 和别的 `*_TOKEN`、`*_SECRET`（`CLAUDE_CONFIG_DIR`、`CODEX_HOME` 照带，它们是你设置所在的地方）。服务退出时先把等着的批准回成取消，再给每个适配器的进程组发 TERM（DeepSeek Harness 关了输入也不退，靠这一步），宽限过后给整组补一次 KILL：适配器自己先退了也补，它起的子进程可能不理 TERM。服务被直接杀掉、来不及收尾时，每个适配器头上的 `acp_guard.py`（进程组的组长，只看着服务的进程号，不碰对话）发现服务没了，就把整组停掉。
- **起进程用干净的环境**之外，代理和证书照带：`HTTPS_PROXY`、`HTTP_PROXY`、`ALL_PROXY`、`NO_PROXY`（大小写都认）、`NODE_EXTRA_CA_CERTS`、`SSL_CERT_FILE`、`SSL_CERT_DIR`、`REQUESTS_CA_BUNDLE`，靠它们上网的人照样连得上。
- **默认和终端里一样**：会话开出来用的是你自己的设置（Claude 的模式、放行规则、skills、插件、模型；Codex 的模式、模型、推理档；DeepSeek Harness 桌面版的模型和推理档）。顶上一行写着现在的模式、模型、推理档，每个会话可以改（只能改成 agent 自己报上来的选项）。Claude 开新对话时可以关掉"带上我的个人设置"：只读项目自己的设置（`settingSources: project, local`），实测你的 42 个个人 skill、插件带的子 agent 都不带了；模式仍是 Claude Code 自己的默认（没有设置时它从"自己判断"开始），可以在顶上改。
- **一个会话的记录**：每一件事是一个事件，追加写进 `<项目>/.ovh/agents/<id>.jsonl`（`<id>.json` 是它的头：哪家 agent、它自己的会话号、带没带个人设置）：你说的话、agent 的每一条更新（边写边出的文字、想法、工具调用和它的改动、计划、上下文用量和花费）、每一次请你批准和怎么答的、每一轮的开始和结束。项目里的路径写成相对路径，家目录写成 `~`，太长的输出截短（agent 自己的话和请你批准的内容不截；请你批准的那一条原样记，路径也不改写：`cd /tmp && rm -rf <项目>/x` 改写成相对路径就成了另一条命令）；agent 列出的个人 skill 只记个数，Claude 的"子 agent"设置只记在用的那一个和一共几个（名字来自你的插件）；边写边出的文字隔 0.12 秒并成一条记（一轮几万个碎片不会变成几万行）。这个文件夹里有一个内容是 `*` 的 `.gitignore`：放在自己 git 仓库里的项目，`git add -A` 也不会把对话加进去。页面用 SSE（`EventSource`，带 Last-Event-ID）读它：关了重开、断了重连，补上错过的，没答的批准卡重新出现。服务重启后，会话从这份记录读回来；接着说话时，能接回原会话的（Claude、Codex 的 `session/load`，DeepSeek Harness 的 `session/resume`）就接回，接不回的开新的并写一句"它记不得前面的话"。
- **画什么**：你说的话（带着"对着"什么）；agent 的文字边到边显示（DeepSeek Harness 是整段一起到，中间显示"在做，回复会整段一起到"和它正在用的工具）；每个工具调用一张卡：读了哪个文件、跑了什么命令、改了哪里（有改动对比的画对比），输出折起来；请你批准时一张琥珀色的卡，把请求里的东西一样不少摆出来：它给这一步起的标题，输入里的每一个字段（键和值原样、转义过；认识的配一句人话，比如 `dangerouslyDisableSandbox` 是"不用沙箱跑"、`run_in_background` 是"在后台跑"，`description` 标明是"它自己的说明"，不认识的原样列出），涉及的位置，它附的话，改动对比（不截）。这些放在一个限高、能滚动的框里，不做首尾拼接；框装不下时，"允许"那几个按钮要等你滚到底、或点"全部展开"才能点，旁边写着为什么，"不行"随时能点。一条请求长到这里显示不全（一个字段超过 20 万字），就只能拒绝，服务端也这样拦。按钮用这一页的话（允许这一次、这个对话里同类的都允许、不允许……），下面并排写着它给的选项原文（它可能写明一个选项管到哪儿）；问题就放在那个工具的卡里；它在等时输入框上面多一条"在等你点头"，点一下回到那张卡；它的计划；想法折起来；不认识的消息按通用样子显示（名字和原样内容），不报错。顶上写着它现在在干什么（在想、在跑某条命令、在写回复、等你批准）和几秒了；下面一行是模式 · 模型 · 推理档，右边是上下文用量和这个对话的花费（agent 报了才有），点一下这一行才展开成能改的菜单；额度警告（比如 Claude 订阅 7 天额度用到多少、哪天恢复）只在 agent 报了警告时单独一行；没登录或登录过期时，写清怎么登录。被你拒绝的命令写成"你没允许，所以没做"，请求照样完整显示。
- **停止**：先把没答的批准都回成取消，再让这一轮停下。适配器收到停止以后 `OVH_AGENT_STOP_GRACE` 秒（默认 8）还没结束这一轮，就在这里结束它、放掉项目锁、重启这个适配器（接着说话时接回原对话），这一列写清发生了什么；不会因为一个不理停止的适配器把项目锁上几个小时。
- **输入框**：回车发送，Shift+回车换行（输入法选字时的回车不算）；"对着"跟着你在模块里选中的东西，发出去时附一句控制台自己写的说明（哪一镜、哪一段时间、哪个模块），不带项目文件里的文字。
- **项目锁**：一轮开始前查四样，有就不发，写清是谁占着：控制台里别的对话（`<项目>/.ovh/agent.lock`，一轮进行时拿着，O_EXCL 建，进程不在了就当没锁）；终端里正在跑的 `bin/vh` 命令（活动记录，控制台自己的 agent 起的不算）；终端里一个 agent 在等这一轮的提交（`bin/vh desk wait` 或 `bin/vh gate --wait` 的 `.listening`；等着的那条 `bin/vh gate` 不另算成在跑的命令）；文件夹里开着的 agent 程序（`lsof` 找得到时：在这个文件夹起的 claude、codex，以及用 node、python 跑的 dsh 这类命令行）。后两种不一定在改东西，你可以点"仍然发这一句"（话里写明两边可能改到同一处）；前两种直接不发。锁是建议性的，和 `bin/vh` 其他命令各自的锁（混音的、素材台账的、反馈的）不共用文件，互不等待。
- **"动手前先问"做不到三家一致**：Claude 在"先问再做"模式下只读命令和放行名单里的命令照样直接跑；Codex 在只读模式下写文件是被它的沙箱直接拒绝，在"只改项目里的"模式下写项目外才问；DeepSeek Harness 在项目里写文件不问。所以这一列不假装能全拦：每一个工具调用都实时显示成卡。


| 地址 | 给什么 |
|---|---|
| `GET /?k=<启动钥匙>` | 页面，和打开在哪个项目上；用 GET 带着这一次启动的一次性钥匙来的第一个页面拿到令牌（之后钥匙作废；HEAD 不算），别的请求拿到的页面不带令牌 |
| `GET /api/hello` | 页面手里的令牌是不是这一次启动的（`X-Desk-Token`）：200 是；403 不是（控制台重启过，或者这个页面不是从那条链接打开的），带着 `link`（换新链接的那一行），控制台锁住了还有 `locked` |
| `POST /api/key-reused` | `{k}`：页面带着钥匙来却没拿到令牌、手里也没有这一次的令牌时报的：钥匙对，控制台就锁住（已发出的令牌全作废，什么都不收），回 403 `{locked, link}`；手里有令牌的页面报了不算（200），钥匙不对也不算（403） |
| `GET /static/<文件>` | `ui.css`、`ui.js`（关卡视图的，静态页内嵌的是同两份）、`studio.css`、`studio.js`（控制台的外壳和成片模块）、`modules.css`、`modules.js`（其余模块）、`core.js`（控制台和静态页共用的文字和小函数） |
| `GET /api/projects` | `{version, home, roots, count, waiting, projects}`：`bin/vh projects` 的每一行，等人的在前，其余按最后一次动静从新到旧，交付了的在最后；加 `key`（地址里的项目键，见下面）、`picture`（`{path, kind: image \| video, from, href}`：封面，`bin/vh thumbs` 的镜头图，片子本身，联系表，关卡页里的图，分镜关键帧，最新的一张图，只取在的文件）、`ask`（等人时：`{gate, title, title_en, question, questions, summary, decisions}`：`questions` 是这一页的问题，最多四个，`summary` 是这一页的那一句）；`title` 在 BRIEF 没写片名时取最新一页关卡页的标题里关卡名之前的那一段 |
| `GET /api/p/<键>/data` | `bin/vh desk data` 的内容，加 `status`（`bin/vh status --json`）、`key`、`home`、`pid`（这个项目文件夹的身份：真实路径的 SHA-1，提交要带上）、`only`、`current`（这一轮的页名）、`round_open`（这一轮那一站还没定：不是 done、skipped；这时提交带上它还没交过、或交过以后改了的决定），和 `studio`（`film` 是成片模块播的那一支，只取在的文件；要的那支不在时，`film_missing` 是它的路径；`sheet` 是最新的联系表；成片模块用的：`timeline` 是 `bin/vh timeline --resolved` 的内容；`thumbs`、`peaks` 是 `bin/vh thumbs`、`peaks` 做过才有的记录；`check` 和 `findings` 是最近一次检查的结论和带时间的问题，没过和要注意的；读不出来的那一样是 `null`，原因记在 `warnings`），和 `mods`（其余模块读的，都是已有命令写下的文件：`loudness` `{integrated, true_peak, lra, target, severity}` 和 `silences`、`checks`（最近一次检查的每条 finding：`kind, severity, message, t, t1`）；`pace`（旁白时间轴里 `bin/vh pace` 写的 `reference, unit, speech, with_pauses` 和逐句的 `lines`）、`voice`（旁白用的音色）、`audition`（最新的 `audition.json`：`{file, provider, unit, text, voices: [{voice, file, duration, pitch_hz, speech_rate, misread, error}]}`）、`lifts`（最新的 `*.beats.json` 的候选落点）；`covers` `[{path, ratio, id, text}]`、`subs`（字幕文件）；`assets`（台账里没删的每一件：`{id, kind, path, there, system, license, license_name, source, url, aigc, used_by, note}`；`system` 是系统自带的字体（`/System/Library/…`、`/Library/Fonts/`、Windows 的 Fonts 这些），算在，不算在项目外；没有台账是 `null`）、`refs`（`research/refs.json`）、`digests` `[{id, path, bytes}]`；没有台账时 `assets_notes` `{file, rows: [{file, source, license, there}]}` 是 NOTES.md 里旧的素材台账表（`there` 对链接是 `null`）；每一部分各读各的：读不出的那部分是空的，`errors` 写着它的文件和原因，别的照样有；只读项目里面的文件，指到项目外的链接不跟，和 `/f/` 一样） |
| `GET /api/p/<键>/gate/<页>[?lang=zh\|en]` | 那一页的关卡视图：`{version, gate, current, this_round, title, lang, takeall, html, errors, warnings, decisions: [{id, question, recommend, options}], summary, cards, marks, not_reviewed}`；`html` 和静态页同一份标记，文件地址换成 `/f/<键>/…`；`cards` 是所有决定的选项卡（右栏用，同一份标记），`marks` 是没把握和请你听的地方 `[{kind: least \| listen, t, t1, id, note, target}]` |
| `GET /api/p/<键>/stage` | 不等人时的画面：`{kind: "video", path, html}`（同一个播放器和标尺），或 `{kind: "image", path, href}`，或 `{kind: null}` |
| `GET /api/p/<键>/status` | 有没有 agent 在等这个项目的反馈，和这一轮的页名 `round` |
| `POST /api/p/<键>/feedback` | 一次提交（格式见下面"写什么"），另带 `pid`：和这个地址现在指的文件夹对不上（或没带）就 409，不写进任何项目 |
| `GET /f/<键>/<路径>` | 这个项目里的一个文件（支持 Range） |
| `GET /api/p/<键>/agents` | `{agents: [{kind, label, installed, version, pinned, outdated, size, install, settings_toggle, signed_in}], sessions: [{id, kind, label, title, first, created, last, live, running, pending, personal, turns}], pid, approval_timeout, lock}`：右栏能用哪几家、这个项目的对话（新的在前），和谁拿着项目锁 |
| `GET /api/p/<键>/agent/<id>/events?token=…[&after=N]` | 这个对话的事件，SSE：先一个 `hello`（会话的状态、设置、agent 报的能力），然后 `after`（或 `Last-Event-ID`）之后的每一件，再来的边到边推；每 5 秒一行注释保活。要页面的令牌 |
| `POST /api/p/<键>/agent/new` | `{kind, personal}`：开一个新对话，起好 agent，带着它的设置回来；没装 424，起不来 503 |
| `POST /api/p/<键>/agent/<id>/say` | `{text, scope, despite}`：人在输入框里打的字，开一轮；有人占着项目 409（`who` 写是谁） |
| `POST /api/p/<键>/agent/<id>/answer` | `{request, option}`：回答一个还在等的批准，只能是 agent 给的选项之一，只能答一次 |
| `POST /api/p/<键>/agent/<id>/stop` | 先把没答的批准回成取消，再让这一轮停下 |
| `POST /api/p/<键>/agent/<id>/mode`、`/config` | `{mode}`、`{id, value}`：改模式、模型、推理档，只能改成 agent 报上来的选项 |

**项目键**是项目名（子文件夹里的项目，`/` 换成 `~`）加 `~` 和文件夹真实路径 SHA-1 的前六位，比如 `demo~0e4e17`：同一个文件夹永远是同一个键，roots 下多了、少了别的文件夹（包括同名的）都不会让它指到别处；两个同名文件夹前六位撞上时，后一个多带六位。浏览器里的草稿也按键存，同名文件夹的草稿不会串。一个没见过的键至多每 10 秒让服务把 roots 再走一遍。

起服务时给了项目的，原来的 `/api/data`、`/api/status`、`/api/feedback`、`/p/<路径>` 照旧只对这个项目。这些 JSON 不是命令的 `--json` 输出，没有 schema；字段同样只加不改。

## 读什么

表格按表头的**开头几个字**认列（中英文都行，英文不分大小写），列的顺序随意，多出来的列不管。

### BRIEF.md

| 位置 | 读什么 | 英文项目 |
|---|---|---|
| 第一行 `# BRIEF：片名` | 片名 | `# BRIEF: title` |
| `## Spec` 的 `- 键: 值` | 全部列出；`Effort`、`Review language`（`zh` / `en`，界面语言；这一轮的 gate JSON 写了 `lang` 时以它为准，和 `bin/vh review` 同一条规则）、`Output`、`Watch on` 放在立意卡上 | 同左 |
| `## Content` 的 `- 键: 值` | `Concept (one line)`、`Spine (one line)`、`Recurring motif`、`What the viewer should know/feel at the end`；`Specifics` 下面缩进的几条 | 同左 |
| `## Outline`（或 `## 大纲`）里的表 | 每段一行，见下 | `## Outline` |

大纲表的列：

| 列（开头是） | 用途 | 英文 |
|---|---|---|
| `#` | 段号；不写就按顺序编 | `#` |
| `段落` | **段名，按内容或阶段起**（"按下发送""信道编码与调制"） | `Segment` |
| `标签` | 可选的小标签，起承转合、幕之类，显示在段名旁边的小框里 | `Tag` |
| `环节` / `阶段` | 可选，这一段讲的环节 | `Stage` |
| `时间` | `0–10 s`、`1:30–1:52`；时间条按它画 | `Time` |
| `小节` | `4–7`；没有"时间"列时，用配乐的节拍表换成秒 | `Bars` |
| `观众` | 观众看完知道 / 感到什么 | `Viewer`、`Takeaway` |
| `关键画面` / `画面` | 关键画面 | `Key visual`、`Visual` |

旧写法的段名"承 · 发出去"会拆成标签"承"和段名"发出去"。

### SCRIPT.md

第一张带 `字幕`（字幕稿）或 `旁白`（旁白稿）列的表。

| 列（开头是） | 用途 | 英文 |
|---|---|---|
| `#` | 条目编号，点评按它记 | `#`、`ID` |
| `段` / `段落` | 属于大纲哪一段：写段名或段号；对不上时按时间归段 | `Segment` |
| `时间` 或 `小节` | 同大纲 | `Time`、`Bars` |
| `术语` | 可选，术语卡上的词（`video-types/02` 的"术语卡"） | `Term` |
| `字幕` / `旁白` | 正文；读速按"这一条占的时间"粗算 | `Caption`、`On-screen`、`Narration`、`VO` |
| `画面` | 画面 | `Visual` |
| `素材` | NOTES 素材清单的编号（`#2 #4`） | `Facts`、`Source` |

### NOTES.md

- `## 素材清单` 里的表：`#`、`素材`、`类别`、`上屏说法`（可选）、`出处`。不再用的素材整格划掉 `~~…~~`（老写法"（关卡 ① 后不用）……"也认），事实核对页把它淡化、不给点评。英文：`## Material`，列 `#`、`Item`、`Kind`、`On screen`、`Source`。
- `## 待核实的事实` 里的 `- [ ]` / `- [x]`。英文：`## To verify`。
- `## 点子` 里的每条；其中写"同题的视频都长什么样：……"（或"常见的样子"）的那一条，立意模块放在素材清单下面。英文：`## Ideas`，`Videos on the same topic look like: …`。

### DECISIONS.md

- 表头以 `决定` 开头的表：`决定`、`谁拍板`、`状态`、`在哪看`（导演模式的账本）。英文：`Decision`、`Who`、`Status`、`Where`。
- `## agent 定的事` 下的每条 `- 日期 话题 · 定了什么 — 理由：… — 翻案：…`，中间可以有 `###` 小标题（显示成分组）。**作废的整行划掉**，后面写原因：`- ~~2026-10-03 style · 夜色画面 — 理由：…~~（关卡 ① 后作废）`，审阅台把它收进"已经作废的"，不再给"翻案"按钮。英文：`## Decided by the agent`，`— why: … — undo: …`。

### REVIEW.md

每个 `## ` 小节是一轮（"页面"那一行的日期，没有就是小节里第一个 `YYYY-MM-DD`，是这一关的日期，账本用它；`关卡 ②`、`Gate ②`、`gate 2`、`E2` 都认）：`- 原话（说明）："……"` 是人的原话，`- 定了：…`、`- 改了：…`（同一行写 `定了：A　改了：B` 也行）是之后的处理。只有空占位的小节（模板里还没填的关卡 ②③）和模板最后两节参考文字不算历史。标题以"暂停"开头、又没写"恢复"的小节，让顶栏显示"暂停"。英文：`- Verbatim: "…"`、`- Decided: …`、`- Changed: …`，`Paused`。

### PACKAGING.md

平台那一行、`## 标题` 的表（`#`、`标题`、`类型`、`里面的数字或事实`、`核实`）、`## 封面` 的表（`#`、`画面`、`封面字`、`原图`、`信息流大小`）、「简介和章节」「署名」小节的 `- 键：值`，和「发布文案」下每个 `### 平台` 的标题、简介、标签（`tools/packcheck.py` 怎么读，这里就怎么读）。占位的 `{…}` 不算。交付模块用它。

### 镜头表：shots.json 或 edit.json

和 `bin/vh storyboard` 同一份（`tools/shot_source.py` 找它）。有剪辑表（`edit.json`，`engines/EDIT.md`）时读它的段，起止是解好的秒，段上的 `transition` 写成文字（`turn 0.8 s`）；剪辑表解不开时，原因写进 warnings。否则读 `shots.json`（格式见 `bin/vh storyboard -h`）：一个列表，或 `{"video", "note", "shots": [...]}`；每镜 `id`、`start`、`end`、`segment`、`label`、`reads`、`caption`、`transition`、`unsure`、`frame`。关键帧取 `frame`，没有就取 `bin/vh storyboard` 写的 `out/check/storyboard/frames/<id>.png`。分镜页播放的视频：`shots.json` 的 `video`，否则最新审阅页的 `animatic`，否则 `out/animatic.mp4`、`out/draft.mp4`。

### out/review/gate-<n>.json

和 `bin/vh review` 是同一份文件，字段见 `playbook/01-pipeline.md` 的"审阅页"（`include` 照样生效）。"这一轮"是 `bin/vh review <项目> <n>`（`bin/vh gate` 也一样）最后做的那一页：它每次把页名写进 `out/review/.current`，审阅台和 `bin/vh desk wait` 都先读它；违反规则、没发出去的那一页照样写出来，但不写进 `.current`，这一轮还是正在外面的那一页；`out/review/.gate-<n>.refused.json` 记着它哪里违反规则，下一次发成功就删，`bin/vh status` 据此不把它算成发给了人。所以关卡 ② 之后回头出一页立意 `1b`、关卡 ③ 之后重定配音出 `E3b`、自己起名的 `final`，都会是"这一轮"。`.current` 没有，或者它指的那一页已经删了，才按流程顺序取最后一页：先按站（1、E0、E1、2、E2、E3、E4、3、E5），同一站再按页（1、1b、1c……，不分大小写）；不合这个写法的页名排在最前，彼此之间看修改时间。复制项目、碰一下旧文件，都不会改变哪一页是"这一轮"。`bin/vh review <项目>` 不写页名时，渲染的也是这一轮；要出新的一页，写上它的名字。页名是 1–24 个字母、数字、`-` 或 `_`，按磁盘上文件本来的写法算（APFS 不分大小写：写 `1D` 找到的是 `gate-1d.json`，这一页就叫 `1d`）；链接到项目外面的 gate 文件不读。关卡视图另外认几个可选字段（只加不改，老的页照样出得来）：选项的 `frame`（这张卡的那一帧，立意卡用它，卡就并排放大）；`least_sure` 每条的时间，可以写 `t`、`t1`（秒），也可以把 `id` 写成时间（`12.4 s`、`0–5 s`、`1:05–1:12`），写镜头号的取那一镜的起点：有时间的落在标尺上；还有下面三个：

```json
{
  "listen": [{"t": 9.4, "note": "17 个字飞出手机：每个字一个八音盒的音"}],
  "music": {"audio": "audio/film_mix.wav", "beats": "audio/film.beats.json", "roll": "audio/film.roll/overview.png",
            "labels": {"type": "打字", "send": "发送"}},
  "film": "out/review/open-F2.mp4"
}
```

- `listen`："请你听这几处"，`t` 是秒：关卡视图标尺上的记号（和静态页一样），声音页签里的按钮。
- `music`：声音页签播哪条音轨、读哪份节拍表、乐段在色块上叫什么（`labels` 把乐段的 `name` 换成人看得懂的名字）。不写时，读 `audio/` 里最新的 `*.beats.json`，音轨取同名的 `*_mix.wav`，没有再取 `*.wav`，谱面取同名的 `.roll/overview.png`。节拍表也用来把"小节"换成秒。只有审阅台用它。
- `film`：关卡视图顶上播哪支视频，逐秒点评页签也播它；不写就用 `assets` 里第一支视频，再没有用 `animatic`。时长从视频本身读。

路径都相对项目目录；审阅台只给项目目录里的文件（不给隐藏文件，不出项目目录）。

## 写什么

提交后，服务按这个顺序写：

1. `out/review/feedback/<轮>-<YYYYMMDD-HHMMSS>.md`：一条一行的文字版，人的话原样不动；
2. `REVIEW.md`：插一节 `## 审阅台反馈 · 关卡 <轮> · <日期 时间>`，把上面的文字整段原样放进代码块，下面留一行"定了：　改了："给 agent 填；插在模板的"授权跳过怎么记"之前，没有这一节就接在文末；
3. `out/review/feedback/<轮>-<YYYYMMDD-HHMMSS>.json`：最后写，原子替换。`bin/vh desk wait` 等的就是它。同一秒里的第二份、第三份加 `-2`、`-3`，按数字排。

交给 agent 的提交记在 `out/review/feedback/.consumed`：`bin/vh desk wait` 打印过的、`bin/vh desk feedback` 打印过的，都算交过了。`wait` 一启动，先看这一轮有没有还没交过、又晚于这一页 gate JSON 的提交（比如上一次 `wait` 超时之后人才提交），有就立刻打印、退出 0；没有才开始等新的。`.listening`（有 agent 在等）和 `.desk.json`（服务在跑）里都记着项目目录的完整路径，从别的项目拷来的这两个文件不算数。

JSON 的格式：

```json
{
  "round": "1c", "lang": "zh", "project": "2026-10-01-glass-of-water", "submitted_at": "2026-10-04T02:38:50",
  "decisions": {"look": "F2"}, "defaulted": [],
  "items": [
    {"target": "seg:9", "status": "change", "label": "大纲 第 9 段 这一次", "text": "这个压根没有升华主题……"},
    {"target": "cap:c11", "status": "change", "label": "字幕 c11", "text": "", "orig": "信号好，一次装 8 个；信号差，只装 2 个。", "suggest": "……"},
    {"target": "time:12.4", "status": "ask", "label": "小样 0:12.4", "text": "这里看不清", "t": 12.4},
    {"target": "range:20-24.5", "status": "change", "label": "小样 0:20.0–0:24.5", "text": "这一段太慢", "t": 20, "t1": 24.5}
  ],
  "general": "大体可以"
}
```

- `decisions`：这一页每个决定选了哪个选项；`defaulted` 列出人没动、按推荐算的。
- `items[].status`：`ok` 可以、`change` 要改、`ask` 疑问。没标的条目都算通过。
- `items[].target` 的前缀说明点评的是什么：`dec:` 决定、`least:` 没把握的、`deleg:` 替人定的（gate JSON `delegated` 的序号）、`concept:line` 立意、`seg:` 大纲段、`cap:` 字幕或旁白条、`shot:` 镜头、`fact:` 素材、`time:` 小样的某一秒、`range:<a>-<b>` 小样的一段（秒，ASCII 数字，存到百分之一秒后仍要 a < b；小样页按 I、O 选）、`atime:` 音轨的某一秒、`chapter:<id>` 一章、`asset:<路径>` 项目里的一件素材（相对项目的路径，不出项目；路径前后、每一段前后都不能有空格）、`card:<id>` 一张立意卡、`led:` DECISIONS 里 agent 定的事（序号）、`doc:<文件>#<小节>` 文档的某一节。整个 target 都要合这个写法：结尾多一个换行、带控制字符的都不收。
- `t` 是秒；`range:` 的条目另有 `t1`，两个都按 target 里的数存，页面发来的不算。没写 `label` 的，`desk feedback` 和 REVIEW.md 按 target 起一个（"片段 0:12.4–0:15.0""章节 c2""素材 assets/a.jpg""立意卡 B"）；一段的 `label` 后面总带着它的起止。
- `suggest` 是人直接写的"改成"，`orig` 是原句。

服务会检查：轮次对得上一份 `gate-<轮>.json`（还没有审阅页时用 `notes`），决定和选项都在那一页里，每个字段的类型、状态和 target 合法，单条文字不超过 4000 字、整份不超过 256 KiB，正文和 Content-Length 对得上；不合的回 400，不会断开连接。

## 给客户端的数据

客户端（审阅台，以后的 Studio）只是项目文件和 `bin/vh` 外面的一层壳：它要的数据都由命令给出，终端里的 agent 拿到的是同一份。以后只加字段，改了含义就升版本号。

版本字段有两种拼法，已有的不改名，新文件一律用 `version`。命令的 `--json` 输出，和这些文件用 `version`：`<成片>.render.json`（有版本字段之前的记录没有它，形状相同）、`<成片>.mux.json`、`<副本>.deliver.json`（同上）、`<混音>.mix.json`、`audio/captions.args.json`、`out/versions/versions.json`、`out/check/*.check.json`、`out/proxy/` 的记录、`cast/<id>/cast.json`、`research/web.jsonl` 的每行、`.ovh/project.json`、`.ovh/history/index.jsonl` 的每行、gate JSON（可写可不写）。这些用 `v`：`edit.json`、`out/edit.resolved.json`、`assets/ledger.json` 和它的每条记录、`assets/spend.jsonl`、`research/refs.json`、`research/scout.jsonl`、`research/hot/*.json`、`.ovh/activity.jsonl` 的每行、`clip.json`、`series.json`。每种文件用哪个，`bin/vh artifacts spec --json` 的 `version_key` 写着。

一个客户端要的东西，从这里找：

| 要什么 | 哪条命令 | 只读吗 |
|---|---|---|
| 这台机器上所有项目，各自到哪了 | `bin/vh projects --json` | 是（`--assign` 写 id） |
| 一个现成的本地服务：所有项目、它们的画面、关卡视图、提交 | `bin/vh desk`，上面的"HTTP 接口" | 提交写反馈 |
| 一个项目认得住的身份 | `.ovh/project.json` 的 `id`；`bin/vh status --json` 的 `project.id` | 是 |
| 一个项目的全貌和下一步 | `bin/vh status <项目> --json` | 是 |
| 这支片子该有哪些文件，缺什么、什么过期了 | `bin/vh artifacts list <项目> --json` | 是 |
| 播放和拖动用的文件（当前片子、代理、缩略图、波形） | `bin/vh status --json` 的 `media`；还没有的，对着 `media.film` 这个路径跑 `bin/vh proxy`、`thumbs`、`peaks` | `media` 是 |
| 整条时间线：镜头、旁白、字幕、节拍，秒和帧 | `bin/vh timeline <项目> --resolved --json` | 是 |
| 一条命令跑得怎么样 | `bin/vh activity <项目> --follow --json`，见下面 | 是 |
| 停下一条命令 | `bin/vh cancel <项目> [run] --json` | 写结束行 |
| 文本的退路 | `bin/vh history save|list|diff|restore` | `list`、`diff` 是 |
| 失败了怎么读 | 下面"错误的形状" | |
| 这些输出长什么样 | `tools/schemas/output/`，下面"输出的契约" | |

### 所有项目：`bin/vh projects [--root DIR …] [--assign] [--json]`

在 `$OVH_PROJECTS`、`<仓库>/projects` 和每个 `--root` 下面找带 `BRIEF.md` 的文件夹（不进 `out/`、`node_modules`、隐藏文件夹这些；一个文件夹只算一次），一行一个项目，最近动过的在前。每行：`id`（还没有时是 `null`）、`name`（文件夹名，和项目根之间隔着文件夹时带上它们：`旧片/docs`）、`title`、`path`（真实路径，和 `bin/vh status` 的一样）、`type`、`effort`、`state`、`station`（停在哪一站：`{"id", "name"}`）、`waiting_on`、`next_step`（这两个和 `bin/vh status --json` 同一个形状）、`running`（正在跑的命令名）、`last_activity`（`t`、`at`、`cmd`、`run`、`state`、`exit`）、`film`（当前片子：`path`、`size`、`mtime`、`version`、`check`、`stale`）、`delivered`（交付了的片子哪天交付的，`YYYY-MM-DD`；没交付是 `null`）、`same_id_as`（同一个 id 的别的路径：整个文件夹拷过一份）、`error`（读不了时为什么，其余字段是 `null`，列表照常往下）。

`state` 是一个词：`paused`、`delivered`、`waiting_person`、`waiting_agent`、`in_progress`、`no_record`（模板有 REVIEW.md 之前的项目）、`not_started`。它用 `bin/vh status` 自己的读法（`tools/status.py` 的 `collect`，不读素材台账、cast 和调研，列表用不上），30 个项目 0.2 s 左右，不用缓存。

**身份**：`.ovh/project.json`（`"version": 1`、`id`、`created`）。`id` 随机，和路径无关，从不改，文件夹搬走还是它：客户端用它认项目。`bin/vh new` 写它；老项目没有，`bin/vh projects --assign` 才写（`created` 是这时的时间），只读的命令从不写。整个文件夹拷过一份，两份同一个 `id`，列表用 `same_id_as` 说出来：删掉副本里的 `.ovh/project.json`，再 `--assign` 一次。

### 跟着一条正在跑的命令

每条作用在项目上的命令都往日志写，所以客户端不用自己起命令也能跟：`bin/vh activity <项目> --follow --json`，一行一个 JSON（`start`、`progress`、`note`、`end`，见下面"活动记录"），先是最近的，然后新的一行来一行，不会自己结束，不要了就结束这个进程。

**崩溃没有行可写**，所以只跟 `--follow` 看不出来：命令被 `kill -9`、机器重启、bash 被 TERM 杀掉，都不会有 `end`。客户端在有命令 `running` 又好一阵没新行时，隔几秒问一次 `bin/vh activity <项目> --json`，看这个 `run` 的 `state`：

- `running`：没有结束行，进程还在；
- `ok`：退出码 0；
- `failed`：别的退出码。`error`（`{"code", "message"}`）是工具说的原因，有的工具说不出来就是 `null`，看 `exit`；`cancelled` 为 `true` 是 `bin/vh cancel` 停的，不算出错；
- `gone`：没有结束行，进程也没了：这就是崩溃，或者被杀掉、机器重启过。它留下了什么，看 `outputs` 和 `kept`。

### 错误的形状

下面这些命令加了 `--json`，失败时 stdout 是一行 `{"version": 1, "error": {"code", "message", "hint"}}`，给人看的那一行照旧在 stderr，退出码和不加 `--json` 时一样：`status`、`activity`、`versions`、`check`、`assets`、`edit`、`proxy`、`thumbs`、`peaks`、`artifacts`、`projects`、`cancel`、`history`、`timeline --resolved`、`commands`、`doctor`、`desk data`（它总是 JSON）、`gate`、`new`，连同 `bin/vh` 自己在 Python 起来之前发现的（打错的命令、`--json` 时没有 python3，退出码 127）。

`code` 是稳定的，按它分支，别按文字：`usage`（参数错）、`no_project`（没有这个项目，或者这个文件夹不是）、`not_found`（项目在，它说的文件、片子、版本、run 不在）、`invalid`（文件在，读不成它该是的样子：不是 JSON、不合 schema、还有占位）、`exists`（要写的东西已经有了）、`refused`（规矩不让：页面犯了规）、`missing_tool`（少一个程序）、`timeout`（等到头了）、`failed`（别的）。`hint` 有话说时是一句接下来怎么办，否则 `null`。

几种记录有自己的字段，不是这个形状：`bin/vh check --json` 读不了片子时打它的记录，`error` 是字符串，退出码 1（这是对这支片子的判决）；`bin/vh doctor --json` 没有 python3 时 `error` 也是字符串，退出码 0；清单和检查（`artifacts list --strict`、`assets check`、`edit check`）退出码 1 时打它们的记录。所以先看 `error` 是不是对象。

在日志里跑的命令失败时，同样的话也写进 `.ovh/activity.jsonl`（`note`，带 `"level": "error"`），加不加 `--json` 都写，`bin/vh activity` 能说出一条命令为什么失败。这句话可能重复用户打的东西，所以日志和 `message` 里的 key 一律写成 `…`（`tools/activity.py` 的 `scrub`，和开始行藏参数的规矩相同），只有 stderr 上是原话。

### 停下一条命令：`bin/vh cancel <项目> [run] [--timeout S] [--json]`

只停这份日志起的：没有结束行、pid 活着、开始的时间对得上（pid 会被复用）、命令行还是那条命令（`./vh` 也算，exec 进去的工具也算：`music` 的 `lyria.py`）、开始行写的项目（`project`，真实路径）就是这个文件夹。日志谁都能复制、能写，里面的话不照单全收：pid 没了或者是别的时间起的，状态 `not_that_process`，这个 run 从此读出来是 `gone`；开始行是别的文件夹的（这里是复制出来的一份，或者挪过），也是 `not_that_process`，什么都不发、不写；时间对得上而命令行对不上、开始行没写项目（旧版 `bin/vh` 写的）、run 的 id 不是 `bin/vh` 写的那种，状态 `not_confirmed`，什么都不发、不写，退出码 1：它可能还在跑，要人看一眼。`ps` 说不出来（失败了、不让看）时同样什么都不写，接着等，最后是 `still_running`。不写 `run` 就停所有在跑的，但只是在等人的（审阅台、`gate --wait`）要点名才停。

怎么停：`bin/vh` exec 进去的工具（render、patch、页面工具）只给它自己发 SIGINT，浏览器和编码器它自己收；`bin/vh` 等着的工具（tts、deliver、proxy……）给它和它底下的进程发 SIGINT，和 Ctrl-C 一样，3 s 没停再发 SIGTERM（脚本里用 `&` 起的命令忽略 SIGINT）。还不停就不再加码，说出来，退出码 1；记号留着，工具卡在收不到信号的一步（`spawnSync` 的 ffmpeg）时，这一步结束它自己停，结束行还是写 `cancelled`。

结束行都写清楚：`"cancelled": true`，`exit` 是 130 或 143，不是 `gone`。工具留了什么可以接着做，`kept` 一句话（render 的 chunk，tts 的句子），`--json` 的每个 `run` 里都有；没有就是什么也没留。字段见 `bin/vh cancel -h`。

### 波形：`bin/vh peaks <音频|片子|项目> [--bins 1000] [--json]`

每一格的最小和最大值（`peaks`：`[[min, max], …]`，-1 到 1，各声道放在一起算），ffmpeg 解成 48 kHz、声道不混、分块读，只用标准库，两小时的片子半分钟，内存 130 MB 上下，和片长无关。看不到的：两个采样点之间的峰值（真峰值可能更高），和 24 kHz 以上的内容。记录放在代理旁边（`out/proxy/<名字>.peaks.json`，别的 `--bins` 是 `<名字>.peaks-<N>.json`），带着来源的大小和修改时间，来源没变再跑一次只读记录，不起 ffmpeg。字段见 `bin/vh peaks -h`。

### 一条时间线：`bin/vh timeline <项目> --resolved [zh|en] [--words] [--json]`

`shots`（剪辑表的段，或 `shots.json` 的镜头，或页面渲染时记在 `.render.json` 里的镜头）、`narration`、`captions`、`beats`，每一项都有秒和帧（`start`、`end`、`start_frame`、`end_frame`，`end_frame` 是下一段的第一帧；节拍是 `t`、`frame`），`sources` 是每个来源文件的路径和 sha256。有剪辑表时读 `bin/vh edit build` 解出来的东西（`out/edit.resolved.json` 还是这份 `edit.json`、读的文件也都没变时就用它，否则同一段代码在内存里解一次，不写文件）。每一行带着表里的其他字段；章节来自剪辑表或片子的 `.render.json`；只渲了一段的片子，镜头从它自己的第一帧算，超出的不要、跨边界的截断。少的部分（读不了、不是 UTF-8、时间是 NaN 也算）是空列表，`missing` 说哪部分、为什么，退出码还是 0；模板自带的示例时间轴不算旁白。只读，不开浏览器，不记日志。字段见 `tools/resolved.py` 开头。

### 文本的退路：`bin/vh history save|list|diff|restore`

`tools/artifacts.json` 里 `made_by` 是 person 或 agent、格式是 markdown、json、text 的文件（不超过 1 MiB），按内容存在 `.ovh/history/objects/<sha256>`，每个快照是 `.ovh/history/index.jsonl` 的一行。`save` 没有变化就什么都不写；`bin/vh gate` 每发出一页存一次，存不了也不挡页面，锁被占着最多等 2 s，跳过时说一声；`restore <文件> [--at <快照>]` 先存当下的状态，读回来确认存下的就是这些字节，所以能撤销（`undo` 就是那条命令）；存不下（超过 1 MiB、里面像有 key）就什么都不写，退出码 1，`code` 是 `refused`；路径上有链接、那个位置是文件夹，同样拒绝。里面像有 key 的文件不进快照，`skipped` 说是哪个文件，不说内容；`.ovh/history/.gitignore` 让项目自己的 git 不提交这个库。`diff` 是 unified diff。很多项目不在 git 下，这是它们唯一的退路。字段见 `bin/vh history -h`。

### 输出的契约：`tools/schemas/output/`

上面这些 `--json` 输出（`status`、`activity`、`versions`、`check`、`commands`、`desk data`、`edit list`、`edit build`、`assets list`、`artifacts list`、`projects`、`cancel`、`peaks`、`proxy`、`thumbs`、`timeline --resolved`、`history list`、`save`、`diff`、`restore`、`gate`、`new`）和错误的形状各有一份 schema：只钉必需的字段和类型，多的字段允许，所以客户端要容忍不认识的字段。`tools/ci.sh` 的 `contract_checks` 每次都建一个小项目、真跑这些命令、对着 schema 查：少了字段、改了类型会红，多了 schema 没写的字段也会红（写进去，它的丢失以后才看得见）。要自己校验：`tools/schemalite.py`（只用标准库），或任何 JSON Schema 2020-12 的实现。

### 现在还没有的

这些是故意没做的，等 Studio 决定了再说，不要指望它们：

- **写入的命令**：改一句旁白、改 BRIEF 的一行，都还是直接改文件；改之前 `bin/vh history save`，出了错能退。
- **项目锁**：两个进程同时写同一个项目没有东西拦着。各命令自己的写是原子的、记录有各自的锁，但没有项目一级的。

### 命令表：`bin/vh commands [--stage <阶段>] [--json]`

命令面板读它：每条命令的名字、一句话、什么时候用、属于哪几个阶段（playbook/01 总表的 0–9，加 `env`、`any`；`stages[0]` 是主站）、读写什么、用法和子命令，来源是 `tools/commands.json`。`reads`、`writes` 是给人看的文字，带 `<project>`、`<x>` 这类占位，不是能直接解析的路径；子命令名带尖括号的（`style` 的 `<preset>`）也是占位。字段见 `bin/vh commands -h`。

### 这台机器能用什么：`bin/vh doctor [--json] [--probe]`

每个外接模块（`tools/modules.json`：程序、包、模型、服务、agent）在这台机器上的状态：找到没有、版本对不对、服务的 key 设了没有（只说有没有，从不给值），再加上页面工具的浏览器和 WebGL、参考仓库、LOCAL.md、AGENTS.md。`--probe` 给每个设了 key 的服务在不花钱的接口上打一次。字段见 `bin/vh doctor -h`。

### 项目里的文件：`bin/vh artifacts spec|list|check [--json]`

每种中间文件的规范在 `tools/artifacts.json`，`spec` 打印它；`list <项目>` 只读，不开浏览器（零点几秒）：这支片子每种文件有哪些路径、版本、schema 的结果、过期没有和为什么、还剩几处 `{…}`，以及到现在该有而没有的。字段见 `bin/vh artifacts -h`。schema 在 `tools/schemas/`：字段只加不改，所以 schema 只钉必需的字段和类型。

### 一个项目到哪了：`bin/vh status <项目> [--json]`

只读，只看已有的文件，不开浏览器、不跑 ffprobe（`tools/status.py`，零点一秒左右）。默认几行字；`--json` 的字段：

- `project`：`id`（`.ovh/project.json` 的 id，还没有时是 `null`；见 `bin/vh projects`）、`path`、`slug`、`title`（BRIEF 第一行）、`type`（类型文档，如 `02-knowledge-short`）、`effort` 和 `effort_from`（BRIEF、LOCAL.md 或默认）、`director`（BRIEF 的 Director 一行）、`lang`（审阅语言）、`spec`（BRIEF 的 Spec 各行，原样的键）。
- `stops`：这支片子在哪几处停（`tools/gatecheck.py` 的 `plan_of`）：`gates`（计划里的关卡，`["1", "3"]` 或 `["1", "2", "3"]`；quick 是空的）、`checkpoints`（Stops 行和 Director 行点名的检查点）、`line`（BRIEF 的 `Stops:` 一行，没有这一行是 `null`：按三道关卡算）、`costly`（关卡 ② 为什么在计划里：片长、3D、付费）、`kept`（Stops 行没写、片子自己留下的关卡）、`note`（一句话）。
- `stations`：按流程顺序的各站。计划里的关卡总在（① 和 ③；② 在片子长、3D 渲染重、有付费调用，或 Stops、Director 行点名时在；没有 `Stops:` 行的项目和 quick 的项目照旧列 ①②③），关卡 ② 不在计划里但有页面或有记录时也列出来；检查点 E0–E5 有页面、REVIEW.md 有它的一节或 Stops、Director 要它（写了 `stop=E3`，或者 `voice=own` 这种人要亲自定的事，按 `playbook/01` 导演模式的表落到最早的那一站：`voice`、`script` 在 E1，`character`、`theme` 在 E0）时才在；别的名字的审阅页（`final`）自成一站；最后是交付。每站：`id`、`name`、`kind`（gate、checkpoint、page、deliver）、`state`、`pages`（这一站的页名）、`page`（最新一页的路径）、`current`（是不是这一轮）、`record`（`decided`、`said`、`waived`、`from`：从哪读出来的，`gate1`（关卡 ① 按 gatecheck 的规则）、`page`（写了这一页的节）、`stop`（这一站的节，还没有页）、`stop_by_date`（这一站的节没写页面，按日期算它是关于这一页的）、`stop_older`（这一站的节有定了，但没写页面、又早于这一页，不算）；关卡 ① 另有 `concept_on_record`）、`feedback`（这一页之后的提交：`submitted`、`handed`、`pending`、`last`）、`note`（一句为什么）；交付那一站交付了还有 `delivered`（`date`：哪天交付的；`films`：记录里点名的成片，可能已经不在本机。来自交付记录、成片过了检查、REVIEW.md 里写了日期的成片那一行，或者更早的片子写完了 LESSONS.md：做在交付记录之前、日志里没有 render、关卡 ③ 已过或跳过的片子，日期取 NOTES.md 或 REVIEW.md 里写定稿的那一行）。
- `state` 七种：`done`（REVIEW.md 里有它的"定了"：先看关于最新那一页的最后一节，审阅台为提交写的那节、或写了 `gate-<n>.html` 的那节，模板的三节都预先写了；没有这种节，就看这一站自己的节，而且 REVIEW.md 要晚于这一页，`note` 里会说是按日期算的。关卡 ① 和 `bin/vh render`、`check` 用同一条规则（`tools/gatecheck.py`）：关卡 ① 的节里有定了和人的原话，DECISIONS.md 里立意定了）、`skipped`（quick 档：这一站没有自己的页面，Director 也没要它（`stop=`、`x=own`）；或者 REVIEW.md 里有用户原话授权跳过）、`waiting_person`（这一页发出去了（`bin/vh gate` 出的页面：写好还没发的 gate JSON 不算，上一次被 `bin/vh gate` 拒绝、退出码 1 的也不算，那一次什么都没发给人），是这一轮（`out/review/.current`），还没有回音）、`waiting_agent`（人提交了还没交给 agent，或者交了但 REVIEW.md 还没写定了；或者这一轮已经往后走、这一页没有记录；或者关卡 ① 定了，但缺人的原话或 DECISIONS.md 的立意，render 和 check 会拒绝）、`in_progress`（前面都过了，agent 正朝这一站做）、`not_started`、`no_record`（standard、studio 的项目没有 REVIEW.md，模板有它之前做的：无从读起，gatecheck 也不查）。交付：`bin/vh deliver` 写过记录，或成片（`out/final*`、`out/final/`、直接放在 `media/` 下的文件、Manim 1080p 及以上的渲染；不含它 480p15、720p30 的草稿，也不含 `bin/vh patch` 留下的 `.failed`）有一份通过的检查记录、而且就是这支成片的（记录里的 `size` 和 `mtime_ns` 和它现在的一样；没有这两个字段的老记录，要比它晚），而且关卡 ③ 过了（`done` 或 `skipped`），就是 `done`；关卡 ③ 还没过时 `note` 会说；各站都过了是 `in_progress`；没有 REVIEW.md 是 `no_record`。
- `waiting_on`：`person`、`agent`、`nobody`（交付了）或 `unknown`（没有 REVIEW.md，又没有命令在跑）；REVIEW.md 写了暂停（`paused: true`）也是 `person`。机器写的记录（检查记录、`.render.json`、`.deliver.json`、审阅台的提交）里类型不对的字段当作没有。`next`：一句话，谁下一步做什么。
- `next_step`：下一步，按项目停在哪一站算出来：`who`（`person`、`agent`、`nobody`、`unknown`）、`do`（一句话，还没填的 `{…}` 和 gate 骨架里的占位有几处都说出来；Director 写了 `x=own`、还没有记录的事排在最前面，记录是它那一站过了，或者 DECISIONS.md 里它那一行写了已定）、`commands`（能直接跑的命令，`<Scene>` 这类尖括号是要换的）、`read`（该读的：`<文件>#<节>` 由 `bin/vh know --show` 打印，没有 `#` 的整篇读）、`unfilled`（`BRIEF.md`、`STYLE.md`、`STORYBOARD.md` 各还有几处 `{…}`，不算代码块和行内代码里的，也不算模板的 `{none}` 和 `{fill: #e33}` 这种带值的花括号；交付以后 `who` 是 `nobody`，这里是空的，没有要填的了）。
- `review`：`current`（这一轮的页名）、`page`、`desk`（在跑时：`url`、`listening`）。
- `open`：`review_items`（审阅台提交里标了要改、疑问，而 REVIEW.md 那一节还没写定了 / 改了的条目：`round`、`file`、`target`、`status`、`label`、`text`）、`facts_to_verify`（NOTES.md 待核实里没打勾的）。
- `renders`：`out/`（不含 `out/versions/` 和 `out/proxy/`）、`renders/`、`media/` 往下三层的视频（不含 Manim 的 `partial_movie_files/`），新的在前，最多 10 个：`path`、`size`、`mtime`、`render`（`.render.json` 的帧数、帧率、像素、时间段）、`patches`、`delivery`（它是 `bin/vh deliver` 出的上传版时）、`check`（它最近的检查记录）、`version`（它是哪一版的当前文件，见下面"版本"）。`deliveries`：`bin/vh deliver` 的记录。
- `versions`：版本记录（下面"版本"）的摘要，还没有记录时是 `null`：`record`、`keep`、`current`、`kept_bytes`、`list`（每版 `id`、`at`、`t`、`film`、`file`、`state`、`made_by`、`from`、`note`、`changed`、`frames`、`pixels`、`check`）；记录读不了时是 `{"error"}`。
- `check`：最近一次 `bin/vh check` 的记录摘要：`record`、`video`、`at`、`verdict`、`exit`、`counts`、`fails`（前三条）、`stale`（视频不是检查时的那一支了：检查记录里的 `size` 或 `mtime_ns` 和视频现在的不同；没有这两个字段的老记录，看视频的修改时间是不是比记录晚，见"检查记录"）。
- `activity`：`running`（正在跑的命令）、`listening`（在跑的审阅台、`gate --wait`：是在等人，不是在干活）、`recent`（最近结束的五条），每条是下面活动记录里的一个 run。
- `media`：客户端播放和拖动要的文件，都是相对项目的路径，只读、不算什么：`film`（当前片子：最新的当前版，否则 `bin/vh check` 取的那支；都没有是 `null`）、`version`、`from`（`versions` 或 `newest`）、`proxy`、`thumbs`（它的 `thumbs.json`）、`peaks`（它的记录），还没做的是 `null`；`stale`：其中不是这支片子做的（记录里的大小和修改时间对不上），比如 `["proxy"]`，对应的命令再跑一遍就是新的。
- `assets`：素材台账的摘要（`tools/assets/uses.py` 的 `overview`，下面"素材台账"）：`ledger`（有台账时是 `assets/ledger.json`，否则 `null`）、`records`（没删的记录条数）、`removed`、`uncleared`（许可有风险的：NC、ND、BY-SA、未知）、`not_taken`（其中这一档许可策略不收的）、`aigc`、`unregistered`（成片的页面载了、台账没有的素材个数；还没有一支成片记下载了哪些文件时是 `null`）、`films_known`（记下了的成片数）、`policy`、`policy_from`、`budget`（和 `bin/vh assets list --json` 的 `budget` 同一个形状，见下面"素材台账"）、`error`（台账或 Budget 一行读不了时）。不算哈希，很快。
- `cast`：项目 `cast/` 里的定稿参考（`tools/cast.py` 的 `overview`，`bin/vh cast`），没有这个文件夹时是 `null`：`entries`（条数）、`by_kind`（`character`、`costume`、`prop`、`set` 各几条）、`final`（定稿的条数）、`failures`（`bin/vh cast check` 会报的失败数，例如参考图在记录之后改过）；读不了时是 `{"error"}`。只读文件，算参考图的哈希。
- `research`：项目 `research/` 里的调研（`tools/scout/scout.py` 的 `overview`），没有这个文件夹时是 `null`：`scout`（`bin/vh scout` 的记录：`file`、`records` 行数、`latest` 看过的视频和帖子数、`films` 其中当作自己的片子记的、`last` 最后一条的 `fetched_at`）、`hot`（`days` 有热榜快照的天数、`first`、`last`）、`refs`（`bin/vh ref` 的参考：`file`、`records`、`error`）、`web`（`bin/vh web` 存下的网页：`file`、`records`、`error`、`last` 最后一条的 `retrieved`）；读不了时是 `{"error"}`。只读文件，不联网。

### 活动记录：`bin/vh activity <项目> [--json] [--follow] [--limit N]`

每条作用在项目上的 `bin/vh` 命令往 `<项目>/.ovh/activity.jsonl` 追加 JSON 行；只读的 `status`、`activity`、`artifacts`、`projects`、`desk data`、`doctor`、`timeline --resolved`、`history list`、`history diff` 不记，找不到项目的命令也不记。项目从参数里找：第一个是文件夹或文件（含 `--out=f`、`voice=f` 这种）的参数，往上最近的带 BRIEF.md 的文件夹；`review`、`gate`、`desk` 这些也认 projects/ 下的项目名。每行都有 `v`（1）、`event`、`t`（epoch 秒），属于某条命令的还有 `run`：

| event | 字段 | 谁写 |
|---|---|---|
| `start` | `cmd`、`args`（照打的写，但不写秘密：名字（`=` 前那段）里带 key、token、secret、pass、auth、cred、cookie、header、bearer 的选项和 `名字=值` 的值，大写的 `NAME=值`、单字母选项后面的值，URL 里的 `用户:密码@`、查询参数的值和 `#` 后面，Bearer token，名字像秘密的 header，像 key 的参数，都写成 `…`；最多 24 个）、`cwd`、`pid`、`project`（这条命令所在文件夹的真实路径，复制出来的一份不算它；路径太长时没有）、`parent`（由另一条 `bin/vh` 起的） | `bin/vh` |
| `progress` | `done`、`total`、`unit`（`render`：frames，开头、每 15 s、结尾各一行；`patch`、`proxy`：frames；`tts`：lines；`thumbs`：pictures；`deliver`：percent，另有 `pass`、`passes`：这一行是第几遍；这些最多 5 到 10 s 一行，第一行和到头的一行总写） | 工具 |
| `note` | `summary`（一行）、`outputs`（写了哪些文件，项目里的写相对路径）；为什么失败的那一条：`level`（`error`）、`code`（`tools/jsonerr.py` 的错误码）、`summary` 是那句话；`kept`（工具被停下时，留了什么可以接着做：`render` 的 chunk、`tts` 的句子）；`gone`（`true`：`bin/vh cancel` 发现这个 pid 已经是别的进程，这条命令读出来是 `gone`） | 工具：render、patch、review、gate、mix、qa、tts、check、`desk wait`、`versions compare`、`versions use`；为什么失败：`tools/jsonerr.py` 和 `bin/vh` 的 `vh_fail`，render、patch 自己 |
| `end` | `exit`（退出码；Ctrl-C 是 130，写完 `bin/vh` 再用 SIGINT 结束自己，调用它的 shell 才知道是 Ctrl-C；自己处理信号 n 的工具（desk、`desk wait`、`gate --wait`）停下时是 128 + n；被 TERM、HUP 直接杀掉的命令当场结束，没有这一行，读出来是 `gone`）、`duration`（秒；没有 `EPOCHREALTIME` 的 bash，比如 macOS 自带的 3.2，只到整秒）、`cancelled`（`bin/vh cancel` 停的：`true`，`exit` 是 130 或 143） | `bin/vh` 的 EXIT trap；`bin/vh` exec 进去的工具（render、patch、frames 这些页面工具，desk、gate）自己写 |
| `feedback` | `round`、`file`、`items`（按状态计数）、`decisions` | 审阅台存下一份提交时；不属于哪条命令 |

`bin/vh` 把这条命令交给它起的进程：环境变量 `OVH_ACTIVITY_LOG`、`_RUN`、`_PID`、`_T0`、`_CMD`。不写进去的：环境变量、key、文件内容。每行一次 O_APPEND 的 write，几条命令同时写也不会把行写乱：`bin/vh` 写的不超过 1 KiB（bash 的 printf 会把更长的一行拆成 1024 字节一段段写），Python、Node 写的不超过 4 KiB；写不进去（磁盘满、项目只读）就丢掉这一行，命令照常跑完、不多说一句。

`--json` 是 `{"version", "project", "log", "runs", "events"}`。`runs` 里每条命令一项：`run`、`cmd`、`args`、`cwd`、`pid`、`parent`、`start`、`end`、`exit`、`duration`、`summary`、`outputs`、`progress`、`state`、`error`（为什么失败，工具说得出时是 `{"code", "message"}`，否则 `null`）、`cancelled`（`bin/vh cancel` 停的）、`kept`（留了什么可以接着做，否则 `null`）。`state` 是 `running`（没有结束行，进程还在，开始不到 7 天）、`ok`（退出码 0）、`failed`、`gone`（没有结束行，进程也没了：被杀掉，或者机器重启过）。`events` 是不属于命令的行（`feedback`）。`--follow` 先打印最近的，再一行一行跟着打印新的；加 `--json` 是一行一个 JSON。读的时候，读不了的行跳过，类型不对的字段丢掉（`outputs` 不是列表、`summary` 不是字符串……），一行坏了不会让 `activity`、`status` 或客户端停下来。只读日志最后 4 MB。

### 版本：`bin/vh versions <项目> [--json]`

项目里的视频每经 `bin/vh render`、`bin/vh patch` 出一次，就是这支片子的一版（`tools/versions.py`），记在 `<项目>/out/versions/versions.json`。项目外的视频不记；`OVH_VERSIONS=off` 也不记，这时 render 照旧直接盖掉原来的文件。

- **旧的片子怎么留**：render 或 `patch --in-place` 要盖掉的那支片子，先整个挪进 `out/versions/<id>/`（连同 `.render.json` 和它的检查记录；只是改名，不复制，不花时间）。路径上原有的文件不是这两条命令出的（`mux` 出的、手放的、有记录之前渲的），先记成一版 `found` 再留。`out/versions/` 里的东西从不被覆盖（编号也跳过那里已有的文件夹），记录跟着字节走：片子一挪就记它的新位置。路径上是一个链接时，换掉的是链接本身，它指向的文件不动（和有版本之前一样，`OVH_VERSIONS=off` 也是）。输出落在 `out/versions/` 里的 render 和 patch 在画之前就拒绝（退出码 2）。`patch --in-place` 只在路径上还是它切开的那支片子时（大小和修改时间）才放进去；中途被换过就不动它，新片放在旁边，退出码 1。新片放不进去时放在旁边一个没人用的名字（`<stem>.new.mp4`、`.new-2.mp4`……）。
- **默认按磁盘留**：挪走之后磁盘还剩它两倍大小、并且至少 5 GB，才留在项目里；每支片子最多留 `OVH_KEEP_VERSIONS`（默认 3）个旧版，多出来的最旧那个、或者磁盘留不下的，移到废纸篓（`<项目名> v2` 这样一个文件夹），在命令的输出、活动记录和这份记录里都写明；从不直接删。`bin/vh clean` 按它的规矩修剪旧版（先列出，`--yes` 才移到废纸篓，`--keep-versions N` 每支片子留最新的 N 个）。
- **`versions.json`**（`"version": 1`）：`next`（下一个编号）、`versions`、`events`（`use` 的记录：`t`、`at`、`event`、`id`、`film`、`displaced`）。每版：`id`（`v1`、`v2`……不复用）、`n`、`t`、`at`、`film`（出片时的路径，`use` 放回这里）、`file`（现在字节在哪：当前就是 `film`，留着的在 `out/versions/<id>/`，进了废纸篓是 `null`）、`sidecar`、`made_by`（`render`、`patch`、`found`）、`from`（render：它替掉的那一版；patch：它从哪一版改来）、`note`（`--note`）、`changed`、`size`、`mtime`、`frames`、`fps`、`pixels`、`span`、`edit`（剪辑表的片子：`path`、`sha256`、`resolved`，它从哪份剪辑表渲来）、`check`（留下时一起存的检查记录）、`problems`（render 报了问题的帧数，有才写）、`gone`（`at`、`why`：为什么不在了）。
- **`changed`**：render 是 `{"whole": true}`（剪辑表的片子另有 `entries`：画了哪些段）；patch 是 `{"whole": false, "frames": [[a, b]…], "seconds": [[s, e]…], "drawn": [[A, B]…], "shots": [...], "asked": {"shots", "chapters"}}`：点名的帧（含两端）、对应的秒、为了对上关键帧实际重画的帧、这些帧跨过的镜头（项目有 `shots.json` 用它，否则用页面的 `window.film.shots`），`asked` 是 `--shot`、`--chapter` 原样点的名；剪辑表的片子另有 `entries`：重画的窗口碰到的段。
- **`--json`** 输出 `{"version": 1, "project", "record", "keep", "current": {片子路径: id}, "kept_bytes", "versions", "events"}`；每版另算 `state`：`current`（它的路径上就是这些字节）、`kept`（在 `out/versions/` 里）、`trashed`、`gone`（不在记录说的地方了）、`changed`（它的路径上现在是别的字节：在 render 和 patch 之外被换掉了），按文件大小和修改时间判断；`check` 是它的检查记录摘要（当前版取 `out/check/` 里属于它的那份：记录里的 `size` 和 `mtime_ns` 和它现在的一样，没有这两个字段的老记录看是不是比它新；留着的版本，记录若带着这两个字段而和它们不一样就不给）：`verdict`、`at`、`counts`、`record`。读不了的记录：退出码 2；render 和 patch 遇到它会把它改名成 `versions.json.bad-<时间>` 留着，另起一份，不因此失败。

`bin/vh versions compare <项目> <vA> <vB> --t <秒> [--wipe [0.5]] [--out f.png] [--json]`：两版在 `--t` 秒显示的那一帧（第 floor(t·fps) 帧），并排（vA 在左）或擦除对比（线左 vA、线右 vB，默认在一半处），每边最宽 1920 px；默认写到 `out/check/versions/<vA>-<vB>-t<秒>.png`。PSNR（dB，RGB；尺寸不同时把 vB 缩到 vA 的大小）是从两支编码后的片子解出来的帧算的，两边都带着 x264 的损失，所以它说的是两支片子在那一刻差多远，不是两版页面画得差多远。`--json`：`{"version", "project", "t", "a": {"id", "file", "frame", "fps"}, "b", "psnr"（数，或 `"inf"`）, "layout", "wipe", "image", "from": "the encoded films"}`。

`bin/vh versions use <项目> <vN>`：让 vN 重新成为它路径上的当前片子。路径上现在的那支先挪进 `out/versions/` 留着（这里从不进废纸篓，也不按数量修剪），它在 `out/check/` 的检查记录跟着挪走；vN 的文件、`.render.json` 和它自己的检查记录放回原处。所以换完以后，这个路径的检查记录要么是 vN 自己的，要么没有，不会把别的片子的结论算在 vN 头上。render 或原地 patch 正在写这支片子时（它们的锁）拒绝。什么都不删。退出码：0；1 这一版不在项目里（进了废纸篓或不见了）、ffmpeg 失败；2 用法错、没有这个项目、记录读不了。`compare` 和 `use` 记进活动记录，列表不记。

### 拖动用的代理和缩略图：`bin/vh proxy`、`bin/vh thumbs`

都只用 ffmpeg（`tools/proxy.py`），参数给一支片子或一个项目；项目指它的片子：最新的当前版（`bin/vh versions`），否则 `out/` 里最新的、旁边有 `.render.json` 的视频，否则 `out/` 里最新的视频（不看 `out/check`、`out/review`、`out/proxy`、`out/versions`）。输出在 `<项目>/out/proxy/`（项目外的片子：它旁边的 `proxy/`），文件名照检查记录的起法（`out/review/sketch.mp4` 是 `review-sketch`）。`bin/vh clean` 把 `out/proxy/` 当作工具能重做的东西。退出码：0 做好了或本来就是新的；1 ffmpeg 或页面失败；2 用法错、`proxy` 没有片子、`thumbs` 既没片子也没页面。

`bin/vh proxy <片子|项目> [--size 360] [--gop N] [--crf 28] [--full] [--out 目录] [--json]`：`<名字>.mp4`，短边 `--size` 像素（不放大），H.264，每 `--gop` 帧一个关键帧（默认五分之一秒，30 fps 是 6），没有 B 帧，按快速解码调过，带片子的声音（AAC）：任意一处拖过去，最多解 `--gop` 帧。旁边的 `<名字>.mp4.json`（`"version": 1`）：`source`、`source_ident`（片子的 `size`、`mtime`）、`source_version`、`proxy`、`settings`（`size`、`gop`、`crf`）、`fps`、`frames`、`duration`、`audio`、`made`（`full`、`refreshed`）、`windows`（refreshed 时重编的帧段）、`t`、`at`、`seconds`。再跑一次：片子没变就什么都不做（`up to date`）；片子在那之后只经过原地 patch（版本记录里从代理那一版到现在每一步都是这支片子的 `patch --in-place`），就只把重画的帧所在的代理关键帧段从新片子重编、接进去，其余照拷，声音照旧；别的情况（重新 render、换了参数、`--full`）整支重做。接进去的几段和整支重做的同一段可能差一点点（x264 的码率控制会看段外的帧），在测试片上最差的一帧约 65 dB。`--json` 打印这份记录，另加 `state`。

`bin/vh thumbs <片子|项目> [--every 2] [--width 160] [--shot-width 320] [--full] [--out 目录] [--json]`：`<名字>.thumbs/` 里每 `--every` 秒一格（`--width` 宽），每 10×10 格拼一张 `sheet-01.jpg`……；每个镜头一张 `shots/<id>.jpg`（`--shot-width` 宽），取它的 `at`，没有就取镜头 60% 处，和 `bin/vh storyboard` 一样；`thumbs.json` 是对照表。镜头表：项目的 `shots.json`；没有的话，给的是片子就用它 `.render.json` 里记的（渲的时候页面的 `window.film.shots`；对片子不开浏览器，sidecar 里没有镜头就不出镜头图），还没有片子就读页面的。帧从同一支片子做的代理里取（快），没有就从片子取，没有片子就画页面（`bin/vh frames`，要 Chrome）。片子只经过原地 patch 时，只重取落在重画帧里的格子和镜头。`thumbs.json`（`"version": 1`）：`source`、`from`（`proxy`、`film`、`page`）、`source_ident`、`source_version`、`fps`、`duration`、`frames`、`settings`、`tile`（`[宽, 高]`）、`shot`（镜头图的 `[宽, 高]`）、`sheets`（每张 `file`、`tiles`、`size`）、`tiles`（每格 `i`、`t`、`frame`、`sheet`、`x`、`y`：在那张拼图里的左上角）、`shots`（每镜 `id`、`t`、`frame`、`start`、`end`、`file`）、`shots_from`、`made`（`full`、`refreshed`）、`taken`（这次取了几格、几个镜头）、`t`、`at`、`seconds`。时间都是片子的秒（从 `--range` 渲的片子，镜头时间已经减去它的起点）。

### 检查记录：`bin/vh check <视频> --json`

`bin/vh check` 每跑一次，都把结果存成视频所在项目的 `out/check/<名字>.check.json`（名字是文件名去掉扩展名，前面加上 `out/` 之后的文件夹：`out/review/sketch.mp4` 是 `review-sketch`；项目外的视频不存），`bin/vh clean` 留着它。`--json` 把同一份打到标准输出，给人看的那些行改去标准错误；检查本身、退出码和不加 `--json` 时一样（`tools/checkrec.py`）。

顶层：`version`、`tool`、`video`（项目里的写相对路径）、`project`、`record`、`t`、`at`、`size` 和 `mtime_ns`（检查开始时视频文件的字节数和修改时间，纳秒，都是整数，取自 `os.stat`，不算哈希；读不了视频时是 `null`）、`args`（`allow`、`against`）、`exit`、`verdict`（`pass` / `fail`，和退出码一致）、`counts`（`fail`、`warn`、`info` 各几条）、`probe`（时长、大小、各条流）、`motion`（动着的帧对占比、静止占比、硬切数）、`findings`、`skipped`（没跑成的检查和原因）。读不了视频时只有 `error`。建不了临时文件夹（`mktemp -d` 失败，比如 `TMPDIR` 指向不存在的地方）时，检查照跑，输出和退出码不变，多一行提示，不存记录；`--json` 只打 `verdict`、`exit` 和 `error`。

`size` 和 `mtime_ns` 是用来认片子的：`bin/vh status`（`check.stale`、各个 render 的 `check.stale`、交付那一站）和 `bin/vh versions`（每一版的 `check`）拿它们和视频现在的大小、`mtime_ns` 比，有一个不同，这份记录就不是这支片子的了（`stale` 为真，或这一版没有 `check`）。只看记录的时间认不出被换回来的旧片子：`cp -p`、`rsync -a`、`bin/vh versions use` 会把旧的修改时间一起放回去，视频看上去比记录还早；检查跑到一半被换上的片子也一样（记录存的是检查开始时的那一支）。没有这两个字段的老记录照旧：视频的修改时间比记录晚就算改过（`versions` 留 1 s 的宽限）。`mtime_ns` 超过 2^53，JavaScript 的 `JSON.parse` 读成数会丢低位：客户端要自己比就用 BigInt，一般直接看 `stale`。

每条 finding：`kind`、`severity`（`fail` 让退出码是 1，`warn` 要看一眼，`info` 只是说一声）、`message`、`t` 和 `t1`（秒，有时间或时间段的才有）、`frame` 和 `frames`（`[第一帧, 最后一帧]`）、`evidence`（判断依据：量到的数、BRIEF 那一行、画面的 key、确认它的那一条……）、`confirmed`（confirmed.json 盖住了是 true，能确认但没确认是 false，这一类从来不在那里确认就是 null）。没确认的孤立帧还带 `confirm`：填上 why 和 evidence 就能贴进 confirmed.json 的那一条。`kind` 用 confirmed.json 的名字：`check.spec`、`check.gate`、`check.black`、`check.freeze`、`check.silence`、`check.iso`（孤立帧；`declared: true` 是这次 `--allow` 声明的，`lapsed: true` 是确认失效了）、`check.periodic`、`check.static`、`check.cut`（从暗到亮的硬切）、`check.blind`（动得太多、扫描判断不了的一段）、`check.subtitles`、`check.captions`（字幕比它依据的时间轴旧：`audio/captions.args.json` 记的 sha256 和时间轴现在的不同）、`check.colour`、`check.packaging`、`check.scale`、`check.confirmed`（confirmed.json 里没用上、失效或没收下的条目）。

### 素材台账：`bin/vh assets <项目> [--json]`

一个项目用到的素材，一个文件（或一个文件夹，比如从片段烘出来的一组帧）一条记录，记在 `<项目>/assets/ledger.json`（`tools/assets/`，只用标准库）。记录的格式是 `tools/assets/asset.schema.json` 的 v1；仓库外的声音库、跨片的外观账本以后也是这种记录，只是放在别处（库是 `ledger.jsonl`，一行一条）。

- **一条记录**（`"v": 1`）：`id`（不复用）、`kind`（`image`、`video`、`audio`、`font`、`model`、`data`、`other`）、`path`（相对项目；文件夹以 `/` 结尾）、`sha256`（文件夹是它的清单的 sha256：每个文件一行"相对路径\tsha256\n"，按路径排）、`bytes`、`license`（`class`、`name`、`url`、`by`：分类器认的还是登记时给的）、`source`（`origin`：`download`、`generated`、`self`、`user`、`library`、`purchased`；`url`、`file_url`、`provider`、`provider_id`、`title`、`author`、`retrieved`、`range`）、`attribution`、`aigc`、`model`、`prompt`、`prompt_file`、`seed`、`cost`（`amount`、`currency`）、`added_at`、`updated_at`、`used_by`、`tags`、`derived_from`、`note`、`removed`（`at`、`why`）。没命名的字段原样留着（厂商条款、请求号、输入素材）。
- **`license.class`** 十三类（`tools/assets/licenses.py`）：`pd`、`cc0`、`cc-by`、`cc-by-sa`、`cc-by-nc`、`cc-by-nc-sa`、`cc-by-nd`、`cc-by-nc-nd`、`free`、`managed`、`own`、`generated`、`unknown`。认不出的一律 `unknown`。风险标签 `nc`、`nd`、`sa`、`unknown`；`Assets: strict` 收 `pd`、`cc0`、`cc-by`、`free`、`managed`、`own`、`generated`。
- **`ledger.json`**：`{"v": 1, "note", "assets", "events"}`；`events` 每条 `t`、`at`、`event`（`add`、`update`、`remove`）、`id`、`sha256`、`by`、`why`。记录从不删：`remove` 只是标上 `removed`。整份在 `assets/.ledger.lock` 的 flock 下先写临时文件再 `os.replace`，和 `versions.json` 一样。项目里以前每个生成片段一份的 `assets/genclips/<id>/ledger.json`（没有 `v`）照读成记录，台账里有同 id 或同路径的就以台账为准（`references/genvideo-ledger.md` 有字段对照）。
- **`assets/spend.jsonl`**：花钱的记录，一行一条，在 `assets/.spend.lock` 的 flock 下追加写（一次 O_APPEND）：`v`、`kind`、`t`、`at`、`amount`、`currency`、`what`、`tool`、`asset`、`estimate`、`run`。`kind` 三种：`payment`（花掉的钱，没有 `kind` 的老行也算）、`hold`（调用前预占的估价，另有 `id`，结算前算作已花）、`settle`（那次调用实际花了多少，另有 `hold`；没计费是 0）。预算读 BRIEF 的 `Budget:`，没有就读 LOCAL.md 的"默认预算"；按货币分别累计，不换算（`tools/assets/budget.py`）。
- **`list --json`**：`{"version": 1, "tool", "project", "ledger", "policy": {"assets", "from"}, "budget", "counts": {"assets", "removed", "uncleared", "aigc", "missing"}, "assets", "said"}`。`assets` 每项：`record`（原样），加上现在看到的 `from`（哪份台账）、`exists`、`class`、`risks`、`accepted`（这一档许可策略收不收）、`attribution`（`required`、`agreement`、`courtesy` 或 `null`）、`removed`、`problems`（对 schema 不合的地方）。`budget`：`limit`（上限，按货币）、`unlimited`（`不限`）、`from`、`raw`、`error`、`spent`、`held`（预占还没结算的）、`left`（都按货币）、`over`（超了的货币）；`bin/vh status --json` 的 `assets.budget` 是同一个形状。不算哈希，很快。
- **`check --json`**：`{"version": 1, "tool", "project", "ledger", "policy", "exit", "verdict", "counts": {"fail", "warn", "info"}, "records", "findings", "said", "uses"}`；每条 finding：`kind`、`severity`、`id`、`path`、`message`。台账自己的：`record`（对 schema 不合）、`missing`、`sha256`（另有 `sha256_now`）、`prompt_file`、`license`（另有 `class`、`risks`）、`credit`（要署名却没记作者）、`derived`（`derived_from` 指向不存在的记录，或者从别的素材做出来却登记了更宽的许可）。和成片两头比的（`tools/assets/uses.py`）：`unregistered`（页面载了、台账没有的素材，失败）、`stale`（成片载的这个文件和台账的字节不一样）、`unused`（没有成片载、没有混音用、也没写 `used_by` 的记录；至少有一支成片记下了文件时才报）、`mix`（混音用了、台账没有的声音文件，`info`，另有 `paths`）。`uses`：`films`（每支 `film`、`sidecar`、`page`、`files` 个数）、`older`、`unknown`（记下文件之前渲的成片）、`mixes`。要读每个文件算哈希，大项目要几秒。
- **成片用了什么**：`bin/vh render` 把浏览器加载过的、页面文件夹里的每个文件和它的 sha256 写进 `<成片>.render.json` 的 `files`（从页面所在的文件夹算的相对路径；宿主自己的脚本只记在续渲用的 `plan.json` 里）；`bin/vh patch` 把新画的帧载的文件并进去，成片原来没有这张表就不写（几帧的表不是整支片子的）。一个页面出过几支成片时只比最新的一支（按 `versions.json` 里当前那一版的时间，没有就按文件时间，整支的排在只渲一段的前面），`check --film <片子>` 只比那一支，`--all-films` 全比；`uses` 另有 `older`（没比的旧片子）。混音用的文件来自 `<混音>.mix.json` 的 `inputs`。不改页面合约（`engines/CONTRACT.md`）。
- **`credits --json`**：`{"version": 1, "tool", "project", "film", "lang", "left_out", "required", "courtesy", "aigc": {"count", "kinds", "models", "public", "declare", "notice"}, "missing", "text"}`；`required`、`courtesy` 每项 `id`、`ids`（合进这一行的所有记录）、`line`、`merged`（被合掉的不同写法）。`text` 是可以直接贴的文字，AI 那一段只有 `public`；`declare` 是给发布人的话，`notice` 是两句连起来（原有字段）。`--film` 给了时，`left_out` 是没列进去的记录。

## 安全

- 只绑定 127.0.0.1，只回答 Host 是自己的请求（挡住 DNS rebinding）。
- 提交要带这一次启动的令牌、JSON 格式，浏览器带了 Origin 时必须是同源；所以同一个浏览器里别的网页既读不到项目，也没法冒充人提交反馈。
- **令牌只给一个浏览器**：服务启动时生成一把一次性的启动钥匙，只出现在它打印的地址里（`http://127.0.0.1:N/?k=…`）；`bin/vh gate` 起的审阅台，钥匙从标准输入交给服务、写在 gate 自己的消息里，不进项目里的 `.desk.log`、`.desk.json`、活动记录。用 GET 带着钥匙打开的第一个页面拿到令牌（HEAD 和别的地址都不用掉钥匙），存进它自己源的存储里（一个端口一份：cookie 会被发给 127.0.0.1 的每一个端口，所以不用 cookie），钥匙随即作废、从地址栏里抹掉；同一个浏览器重新打开、新开一个标签页、再点一次旧链接，都照样能用。别处来的请求拿到的页面不带令牌：能看，不能提交、不能和 agent 说话、不能替它批准；页面顶上写明为什么，给出换新链接的那一行。
- **钥匙被别人先用了，人看得出来**：用过的钥匙又被一个手里没有这一次令牌的页面带来（你在别的浏览器或窗口打开了，或者别的程序抢先用了），这个页面告诉服务（`POST /api/key-reused`），服务当场作废已经发出的令牌（抢先的那一方随即失效）：等着的批准按"不行"回，在跑的一轮停下，事件流断开，之后什么 POST 都不收。页面写明"这条链接已经被用过一次"、可能是谁，给出换新链接的那一行。
- **自己打开浏览器**：在终端里起的 `bin/vh desk`（标准输出是终端），起好后自己用带钥匙的地址打开默认浏览器（标准库的 `webbrowser`），人不用复制地址，钥匙随即用掉，没有留给别人抢先的空当；`--no-open` 不开，打不开就照旧打印。agent 或后台起的（比如 `bin/vh gate … --desk`，标准输出不是终端）不开，只打印，由 agent 把地址交给人。`bin/vh desk link` 在终端里也一样。打开浏览器时，地址会在打开它的子进程（macOS 的 `open`、Linux 的 `xdg-open`）的参数里出现一下，这一瞬间 `ps` 看得到。
- **换一条新链接**：`bin/vh desk link <项目>`（控制台是 `bin/vh desk link`，带上起它时的 `--root`）把在跑的那一个停掉，照原样（同一个端口、同样的范围）在后台再起一个，打印带新钥匙的地址；旧钥匙、旧令牌都作废，对话从记录里读回来。控制台里的 agent 正在这个项目上做一轮时它不动（`--force` 照样换，那一轮停下）。`bin/vh gate … --desk` 遇到已经在跑的审阅台也走这一步，每一站的消息里都是一条能用的链接；例外是人在终端里自己起的审阅台（它在那里打印的链接带着钥匙）和 agent 正在做一轮的时候：这两种照旧给地址（不带钥匙），并写上换新链接的那一行。
- `/f/<键>/`（和 `/p/`）下的每个文件都带 `Content-Security-Policy: sandbox allow-scripts allow-popups`（没有 `allow-same-origin`）：项目里的 HTML、SVG（HyperFrames 的 `index.html`、`node_modules` 里的页面、下载来的参考图）在浏览器里打开时是一个不透明的源，脚本照样能跑，但读不到审阅台的页面和令牌，也没法替人提交。
- `/f/<键>/` 和 `/p/` 只给那个项目目录里的普通文件（键只认 roots 下找得到的项目，和起服务时给的那一个）：不出目录、不跟着符号链接出去；隐藏文件和 `*.env` 不给，按请求的名字和解析后的真实文件各查一遍，不分大小写（指向 `.env` 的链接、`keys.ENV` 都不给）。
- 每个连接 30 s 不动就断开，发了一半的请求不会一直占着线程。
- **agent 那一列**：新加的地址全部照上面的规矩（只认自己的 Host、令牌、同源、JSON），每个 POST 还要带这个项目文件夹的身份（`pid`），对不上就 409；事件流也要令牌（它就是对话，带着文件内容和命令）。
  - **令牌是唯一的门**。agent 自己跑的命令能读项目里的每个文件、能连 127.0.0.1，但项目里没有令牌和钥匙：项目锁里不写服务的地址，事件记录、`.ovh/` 下的文件、传给适配器的环境里都没有。CI 的 `agent_checks` 照独立评审的做法真攻一遍：从项目文件夹出发，读遍项目和控制台的信息文件夹，连回环，拿到的每一串像钥匙、令牌的字都试过，`/answer`、`/mode` 全是 403。拿到了令牌的进程，不管是谁，都能做页面能做的事：服务端分不出回环上的一个请求来自哪个进程（按对端端口反查进程，挡不住双 fork 和半关的连接，所以不做）。
  - **钥匙在哪，谁能抢先**：项目外不是没有。钥匙在 `bin/vh gate` 的输出和 `--json` 的 `url` 里，起它的那个终端 agent 一定拿得到，还会把这条输出记进自己的对话记录（在 `HOME` 下）或后台任务的输出文件；控制台的适配器保留着 `HOME` 和 `TMPDIR`，agent 跑的命令读得到这些文件。所以从 gate 打印出链接，到人在浏览器里打开它，这段时间里一个能读 `HOME`、能连回环的进程可以抢先拿到令牌。抢先了不会悄悄得手：人一打开就看到"这条链接已经被用过一次"，对方的令牌当场作废，控制台不再接受操作，直到人运行 `bin/vh desk link` 换一条新链接。人一直不打开，抢先的一方就一直拿着令牌。
  - 剩下的边界：同一个用户下能读终端输出或对话记录（钥匙在那里，人打开以前有效）、能读浏览器资料（令牌存在浏览器里）、或者能模拟点击和按键的进程，仍然进得来。真正的边界是 agent 自己的模式和沙箱：在"危险的才问""什么都不问"这类模式下，它跑的命令本来就不经过你。
  - 记录里写的是服务端知道的事：批准由"page"（带着这一次令牌的请求）回答。
  - 发给 agent 的只有请求里的 `text`，也就是人在输入框里打的字：页面只在真的按键或点击（`event.isTrusted`）时发，输入框里只会是人自己打的字（或他自己没发完的草稿）；项目文件里的文字、agent 自己的输出，页面都不会放进输入框，也不会拿去当人的话发。"对着"什么只发控制台自己写的一句（种类、编号、时间），不发项目里的标题。
  - 批准只能由页面上的人点：只能是 agent 给的选项之一，只能答一次，按钮也只认真的点击；"允许"要等请求整个在屏幕上出现过（滚到底或全部展开）才能点，显示不全的请求只能拒绝。没有页面连着时，请求挂着等；`OVH_AGENT_APPROVAL_TIMEOUT` 秒（默认 600）都没有页面，就按"不行"（agent 给的拒绝选项）回它，从不默认放行。
  - 页面上 agent 的话全部先转义再排版，不生成链接。
  - 仓库的规矩照样拦：花钱的命令没有预算就拒绝、关卡没记录时 `render` 和 `check` 不放行，这些是 `bin/vh` 自己在拦，agent 从这里调用和从终端调用走的是同一条命令。
- **一个项目的审阅台能看到多少**：人自己开的 `bin/vh desk <项目>`，和不带项目的控制台一样，空间里有 roots 下的每一支片子，也给它们的文件、收它们的反馈（从一支片子回到空间是 Studio 的基本动作；同一个人、同一台机器，防护和上面一样）。`bin/vh gate` 在后台起的那一个带 `--only`，只服务这一站的项目：没人要它当控制台，它一个人在后台开到 12 小时没人访问才停，这一站也用不着别的片子。
- 控制台记"已经在跑"的文件放在临时文件夹里这个用户自己的 `ovh-desk-<uid>/` 里（0700）；这个文件夹是链接、不归这个用户、别人能写时都不用它，文件不归这个用户、或者它说的进程这个用户发不了信号，都当没有在跑（在多人共用 `/tmp` 的 Linux 上，别人放的文件不能让 `bin/vh desk` 打印他的地址）。

## 限制

- 开着的项目页每 4 秒问一次这一轮是哪一页，agent 发了新的一页就自己换过去；断网或休眠醒来的那几秒里提交的，记在旧的那一轮（那一页的 gate JSON 还在，服务照收）。
- 控制台（和人自己开的 `bin/vh desk <项目>`）把 roots 下的项目都摆出来，也给它们的文件：只绑 127.0.0.1、只认自己的 Host、提交要令牌，但别把 `--root` 指到不想让本机浏览器看到的地方；只想给一个项目，加 `--only`。
- 几个 `bin/vh desk` 进程同时动手（比如两个 `bin/vh desk wait` 一起启动，或者一边 `wait` 一边 `desk feedback`），最坏是同一份反馈交出去两次：它们各自先看到这份反馈还没交过，各打印一遍。不会崩，也不会丢反馈：每次写文件都用自己的临时文件再原子替换，`.consumed` 的读改写在 `.consumed.lock` 上加了文件锁（flock），谁都不会把别人记下的名字冲掉。

## 测试

agent 那一列另有一组（`agent_checks`，`tools/desk/test_agents.py`）：`fixtures/agents/` 里是三家真适配器 2026-11-16 的消息（去掉了个人的东西：路径写成 `{cwd}`，没有 skills 列表和账户），`fake_acp.py` 照着回放，`stage.py` 把它们摆成"装好了"的样子；CI 里不起真 agent、不装适配器。测的是：适配器的干净环境，新地址的各种拒绝，一轮对话，发给 agent 的只有打的字，批准只认 agent 给的选项、只答一次、没页面时超时按拒绝，停止先取消批准，改设置，断线重连补事件，项目锁的四种占用，不带个人设置时发出的设置来源，Codex 和 DeepSeek Harness 的不同（想法、计划、不认识的消息、整段到的回复），服务退出时适配器全收干净（包括不理会输入关闭的那一家，和自己先退了、留下一个不理 TERM 的子进程的那一种），服务被 kill -9 时也一样，重启后读回对话并接着说；请你批准的请求原样到页面（中间藏了第二条命令的长命令、关掉沙箱的字段）；启动钥匙（HEAD 不用掉它，被别人先用了就锁住、页面说得出原因，`desk link` 和下一次 `gate` 换新钥匙、旧的作废，agent 做着一轮时不换）；锁文件全从 `registry.npmjs.org` 取；页面在 node 里测转义、对比和批准卡（整条请求在框里、每个字段都在、"允许"先不能点）。

`tools/ci.sh` 用 `tools/desk/fixtures/` 里的小项目测：`zh`、`en` 两个测读取；`demo` 是一支编的片子（海水为什么一天涨两次），关卡 ①②③ 都有，画面是几张小 SVG，它还带着旁白的时间、节拍表和一份检查记录，成片模块的每条轨道都有东西。`console_checks` 用它测关卡视图（静态页整个内嵌 `ui.css` 和 `ui.js`、不从外面加载东西、推荐的卡预先选上、立意卡带帧、分镜就是画面、没把握的时间，关卡 ①② 的页带着这一站的模块）、七个模块按它的数据画出来（node 里跑 `core.js` 和 `modules.js`，控制台的和静态页只读的都画）、三套主题（同一组变量，每种字色对底色 4.5:1 以上，样式里没有变量以外的颜色）、字数提醒和控制台（外壳、多个项目、键、等人的排前面和它的问题与画面、项目数据和成片模块的数据、关卡视图和右栏的卡与记号、文件、各种拒绝、一次提交）；PR 的截图也只用它。读取的测试（包括读不出表格时退回原文、"这一轮"取 `.current`（2 之后的 1b、3 之后的 E3b、自起的页名，`.current` 指向已删的页时退回流程顺序）、语言规则、超长和深层嵌套的 markdown），在空闲端口起一个服务测 `/api/data`、206 Range、`/p/` 的 sandbox、各种拒绝和坏请求、提交到临时副本、REVIEW.md 的追加，测 `wait` 在有提交时退出 0、启动前就到的提交立刻交出、交过的不再交，拷来的 `.desk.json` 和 `.listening` 不算数，以及 `bin/vh desk -h`。

## 整套截图（开发用）

改了控制台以后，用截图验收：在几个项目上按原尺寸截全套图，请人或只看图的评审一页一页看。`tools/desk/shoot.py` 截这一套。它不是 `bin/vh` 的命令，`tools/ci.sh` 也不跑它。

```bash
bin/vh desk --root <放项目的文件夹>          # 先起一个控制台，它打印地址
uv run --no-project --with playwright python3 tools/desk/shoot.py http://127.0.0.1:8780/ <输出文件夹> [--project 名字 …] [--max 3] [--focus 名字]
```

- 它用 Playwright 驱动这台机器装的 Google Chrome，不下载浏览器。Playwright 只在跑它时由 `uv` 临时装上。
- 截的是：空间页；每支片子打开时的样子和左栏的每个模块（模块一列能往下滚的，再截一张往下一屏的）；一支片子的成片模块，选中一镜、三种布局和提交前的汇总；三套主题；英文界面；手机宽度（390）。
- `index.json` 写着每张图是什么：文件名、说明、页面地址、尺寸，以及片子、模块、主题、语言。
- 按钮按上面的字或角色找，不写死坐标。找不到的那一步记进 `index.json` 的 `skipped`，写明原因，其余照截。按钮的字改了，就改脚本开头的 `LABELS`。
- 它不会提交任何东西：发给 `/feedback` 的 POST 一律被拦下。
