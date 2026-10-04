# 07 拉片：拆解一支参考视频，反推它是怎么做的

看到一支好视频想学时，用这个流程。它和做视频是反过来的：做视频是从 BRIEF 到成片，拉片是从成片反推出 STORYBOARD、STYLE 和 BRIEF。拆完的结果直接当作新项目的起点。

## 1. 拿到帧

- **本地文件**：用 ffmpeg 抽帧（见下面的命令）。
- **网页上的视频**（X、B站、YouTube、抖音）：
  - 下载属于文件下载，要先征得用户同意；还要注意平台条款和版权，拆解结果只用于学习，不要重新发布原片的画面。
  - 不下载的做法：在浏览器里用 JS 把 `<video>` 跳到指定时刻，用 canvas 的 `drawImage` 画出当前帧，拼成联系表显示在页面上，再截图。截图工具直接拍视频层往往是黑的，所以要先画到 canvas 上。本仓库的 `cases/explainer-interstellar-blackhole.md` 就是这样拆出来的。
  - 每次调用只处理 6–9 帧，否则会超时；流媒体会自适应降低分辨率，属于正常现象。
  - **抖音**（2026-10 实测）：电脑版页面不登录会弹登录框，还会跳回首页。改走手机版分享页：
    1. `curl -sI -A "Mozilla/5.0" https://v.douyin.com/<短码>/`，从返回的 Location 里取 `video/<id>`。id 右移 32 位就是发布时间（unix 秒）。
    2. 浏览器切到手机尺寸（内置浏览器用 `resize_window` 的 mobile），打开 `https://www.iesdouyin.com/share/video/<id>/`，等几秒；标题只显示"抖音"时再开一次。页面的 `meta[name=description]` 里有完整文案、发布日期和精确赞数；`<video>` 的 src 是一个 `playwm` 地址；页面文字里还列着作者的其他作品和赞数。用 curl 抓分享页拿不到这些，它们是前端加载的。
    3. 切回电脑尺寸，直接打开那个 `playwm` 地址，浏览器会当作媒体文件播放，再照上一条画到 canvas 上。
    `cases/douyin-vibe-knowledge.md` 就是这样拆的。
  - **X**：不登录也能播。`<video>` 一开始是 480p，先 `play()` 约 3 秒再跳帧，能拿到 1080p。
  - **量字幕和标签多大**：只把那一条画到 canvas 上并放大，叠一层网格（每格 10 个原片像素），截图数格子，换算成 1080p 的 px，再对照 `03-motion-design.md` §4 各档的下限。
  - 和别的 agent 共用一个浏览器时，先开自己的标签页，后面每一步都指定这个标签页。

```bash
ffmpeg -i ref.mp4 -vf "fps=1/3,scale=480:-1,tile=4x6" -frames:v 1 ref_sheet.png      # 每 3 秒一帧的总览
ffmpeg -i ref.mp4 -vf "select='gt(scene,0.3)',showinfo,scale=480:-1,tile=6x5" -vsync vfr -frames:v 1 ref_cuts.png 2>&1 | grep pts_time   # 按镜头切换抽帧，同时得到切点时间
ffmpeg -i ref.mp4 -vn -ac 1 -ar 16000 ref.wav                                            # 抽出音轨，交给 whisper / FunASR 转写
```

## 2. 逐层拆

| 层 | 要回答的问题 | 写到哪 |
|---|---|---|
| 结构 | 分几段？每段讲什么？开场钩子是什么？结尾有没有和开头呼应？ | `STORYBOARD.md` 的时间表 |
| 节奏 | 平均镜头多长？快慢怎么交替？高潮前有没有停顿？ | STORYBOARD 的时间列 |
| 视觉系统 | 底色、强调色（取色）、字体（衬线还是无衬线）、标注样式、年份卡或标题卡的位置 | `STYLE.md` |
| 主视觉 | 有没有一个贯穿全片、反复使用的核心画面？ | STYLE 和 BRIEF 的 motif |
| 运动 | 缓动、转场种类、主流向；镜头按四层拆：稳定方式（固定 / 稳定器 / 手持）、运动路线（起点、路径、终点）、观看视角（旁观还是 POV）、时间结构（切点在哪、有没有长镜头）（拆法见 `05-hybrid-genvideo.md`"给视频模型写运镜"） | STYLE 的 motion tokens |
| 声音 | 有没有旁白、BGM、音效？字幕是旁白稿还是静音可读的屏幕文字？ | BRIEF |
| 手法推测 | 每种画面最可能用什么实现（着色器、SVG、Manim、生成视频、实拍）？ | NOTES，标【推测】 |
| 作者信息 | 作者有没有公开 prompt、工具或耗时？评论区有没有补充？ | NOTES，附链接 |

## 3. 反推 BRIEF

把上面拆出的结果填进 `templates/BRIEF.md`，最后再写一句话：如果让 agent 一句话做出这支片，那句话是什么。一句话 prompt 用来探索方向，完整的 BRIEF 用来精确复刻。两者都保留。

## 4. 交付格式

在 `cases/` 下新建一份拆解文档，结构参考 `cases/explainer-interstellar-blackhole.md`：
1. 作者说了什么；
2. 画面拆解表；
3. 为什么有效；
4. 怎样用本仓库复刻。

复刻出来的项目放在 `projects/`。

## 相关工具

`references/repos/viral-video-decomposer/`（MIT）：把爆款短视频拆成镜头级拉片、爆款机制分析、AI 生产蓝图和视频生成 brief。适合批量拆短视频。
