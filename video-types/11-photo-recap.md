# 11 照片回顾（人自己的照片和片段）

> **实验性：按仓库已有的工具写成，还没有用它做过一支完整的片子。** 拿第一批真实素材校准后再回来改。

**适用**：婚礼、旅行、一年回顾、纪念日、孩子长大。素材是人自己的照片和手机片段，配一首歌，加几行字。

**不适用**：
- 靠人说话撑的口播、访谈、Vlog：`09-editing-talking-head.md`；
- 没有真实素材、要生成人物：`playbook/05-hybrid-genvideo.md`；
- 档案和历史影像的纪录片：`playbook/05-hybrid-genvideo.md` 的"边界"。

**素材是别人的脸**：照片里的人不只是来找你的这一位。先问清片子给谁看；要公开发的，里面的人（尤其孩子，和已经不来往的人）同意了吗；不确定的不放，或者问人怎么处理。照片和片段默认只留在这台机器上：要传给云端服务（转写、生图、云端评审）先问，答复记进 BRIEF；不当参考图送给生成模型。agent 看联系表，也是把画面发给模型，开工前跟人说一声。

## 引擎

`bin/vh new recap <slug>` 建 canvas-film 项目。两条路可以混用：

- **剪辑表 `edit.json`**（`engines/EDIT.md`，默认走这条）：一段一张照片或一个片段，硬切。照片写 `{"image": "assets/photos/a.jpg"}`，推拉写 `move`（画面中心落在照片的哪一点、放大多少）。浏览器解码，手机照片的方向和颜色配置都对。HEIC 不收，先转成 jpg（macOS：`sips -s format jpeg a.heic --out a.jpg`）。片段写 `{"clip": "assets/clips/b.mov"}`，原声默认关，要留就写 `sound`；手机的可变帧率、旋转和 HDR 片段 `bin/vh edit build` 会拒绝，并给出规整它的 ffmpeg 命令（HDR 转 SDR 时颜色怎么转是个决定，要看一眼）。
- **页面**（`src/50-shots.js`）：要在照片上写字、要叠化或翻页（`dim`、`turn`）、要照片墙时，写成镜头，整页作为一段放进剪辑表（`{"page": "film.html", "clock": "film"}`）。剪辑表这一版不画转场和上层字幕，所以这些都在页面里做。没有旁白时，时间用歌（`engines/canvas-film/README.md` 的"配乐主导片"）。

**竖屏**：`edit.json` 的 `size` 写 `[1080, 1920]`，BRIEF 的 Output 一起改；页面只有 16:9（canvas-film 的局限），`bin/vh new` 的 `--aspect` 也不收。

## 工作流

1. **先问清（关卡 ①；`quick` 最多问 1 个，先问给谁看）**：给谁看、发在哪；多长（一首歌的长度常常就是片长）；哪些照片和人必须有、哪些不能有；要不要字，字谁给。
2. **入库**：照片放 `assets/photos/`，片段放 `assets/clips/`，整个文件夹登记一条：`bin/vh assets add <项目> assets/photos --origin user --class own`。原图不改，要处理的另存一份。
3. **读拍摄时间，按时间排**：照片读 EXIF，片段读 `creation_time`：

   ```bash
   uv run -q --no-project --with pillow python - assets/photos/*.jpg <<'PY'
   import sys
   from PIL import Image
   for f in sys.argv[1:]:
       print(Image.open(f).getexif().get_ifd(0x8769).get(36867, "no date"), f)
   PY
   ffprobe -v error -show_entries format_tags=creation_time -of csv=p=0 assets/clips/b.mov
   ```

   文件的修改时间不算数，传一次就变了。几台手机的时钟可能差几分钟甚至一个时区，找一个都拍到的时刻对一下。读不出时间的（截图、转发过的图）列出来问人，不猜。排好的清单写进 `NOTES.md`。
4. **选片和结构（关卡 ①②）**：连拍只留一张。立意不只有"按时间走"：也可以按一个人、按一件反复出现的东西（同一个地方每年一张）、从今天倒着走。大纲的段落按真实的时间或地点分。把清单写成 `edit.json`，`bin/vh storyboard <项目>` 每段出一页预览：人这时候删照片、换顺序最便宜。
5. **音乐定时长**：人给的歌，或者 `bin/vh bgm search` 挑的，都用 `bin/vh assets add` 记来源和许可。`bin/vh beats audio/song.mp3 audio/song.beats.json` 出拍点，切点写它 `downbeats` 里的秒数（剪辑表的 `{"$music": …}` 只认 `bin/vh music` 的谱子，不认外来的歌）。抒情歌检出来的拍子可能不准（`--check` 查），就按乐句切，不硬卡。全片的节奏可以借 `recipes/sequences/` 的骨架。
6. **出片**：`bin/vh edit build`、`bin/vh render`、`bin/vh mix … music=audio/song.wav edit=<项目>`（把留着的片段原声放进来）、`bin/vh qa`、`bin/vh mux`，最后 `bin/vh check` 和 `bin/vh assets check`。

要一段公共领域的空镜或一张老地图时才用 `bin/vh footage`；人自己的片段不走它，它只收 archive、commons、nasa 和 https 链接。

## 审美要点

- **手机上认得出脸**：`bin/vh new recap` 默认 `Watch on: feed`，横屏片竖着拿手机看，画面只有约 360 px 宽。合影里的脸只剩几个像素：用 `move` 从整张推到要看的那张脸，或者拆成两段。手、戒指、请柬上的字这类小细节要放到占满画面。按 `playbook/02-verification.md` 的"手机测试"缩小联系表看。
- **竖照片放进横屏**：`fit: contain` 留边（`bg` 定底色）；`fit: cover` 会裁掉上下，要看脸有没有被裁，再用 `move` 的 `from` 把中心放到脸上。
- **一张照片多给几秒**：起点是 2–5 s，人多的多给；全片 2–3 种推拉，推向脸，不推向空白；照片和片段交替着来。
- **真实的瑕疵留着**：糊的、歪的，有时候那一刻只有这一张。不磨皮，不把静帧扭成会动的脸。
- **字越少越好**：地点、日期、名字，只写人给的。
- **结尾留一张最安静的**，音乐收干净，不停在半句上。

## 禁止

底线（同意、隐私、事实）：
- 照片里的人没同意就公开发；孩子的脸、住址、车牌、证件、请柬上的电话没处理就公开发；
- 没问就把照片传到云端，或送给生成模型；
- 编造关于真实事件的字幕：人名、关系、日期、地点、谁说了什么、当时的心情，人没给的不写，也不从照片里猜；
- 用生成模型改真实的照片（换脸、补人、去掉人）却不说，或者生成没发生过的画面当真事；
- 歌和素材的许可没记。公开发的片子用没授权的歌，先跟人说清。

常见误用（参考）：
- 按文件名排序；连拍全放；
- 每张照片一样长、一样的推拉；
- 合影缩在画面中间，手机上认不出人；
- 一张一个花哨转场。

## Prompt 增量块

```text
+ TYPE: photo recap from the person's own photos and clips ({a wedding | a trip | a year}). {2–4} min, {1920x1080 | 1080x1920} 30fps, music: {song, its licence}, watched on {feed | phone | desktop}, seen by {family only | the public}.
Ask first: who sees it, whether the people in it agree, what must stay out. The material stays on this machine unless the person says otherwise.
Order by capture time read from the files (EXIF DateTimeOriginal, creation_time), not by file name or modification time; ask about what has none.
Layout in edit.json: one entry a photo or clip, `move` towards a face, at most 2–3 kinds of move, cuts on the song's bars or phrases. A group photo pushes in to the faces that matter; faces and small details must read at 360 px wide.
Words on screen: only what the person gave (names, dates, places). Nothing invented about real events; no generated or retouched picture passed off as what happened.
```

## 自查重点

- 手机大小的联系表：每张的主角认得出吗？小细节看得清吗？
- 时间顺序对吗？几台手机、跨时区有没有排错？
- 每行字都是人给的吗？名字写对了吗？
- 有没有不该放的：人没同意的、证件、住址？
- 切点落在歌的小节或乐句上吗（`bin/vh beats … --check`）？片尾的音乐收好了吗？
- `bin/vh assets check` 过了吗？歌的许可记了吗？

## 可参考的案例与源码

- `engines/EDIT.md`：来源、段的字段、片段的规矩、声音。`engines/canvas-film/README.md`：页面、转场、配乐主导片。
- `playbook/09-narrative.md` 第 1、2 节：先定三件事，再选骨架。
- `recipes/sequences/README.md`：全片节奏的骨架（`data-along-time` 也是按时间走）。
- `styles/archival-pan-zoom/`：只有静止的照片、镜头慢慢推拉的一种风格，想借就 `bin/vh style apply archival-pan-zoom <项目>`。
- `engines/editing.md`：可变帧率、避脸字幕、人脸追踪，留片段原声时有用。
