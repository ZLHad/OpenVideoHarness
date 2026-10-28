# 剪辑表：`edit.json`

一支片子可以是一个页面，也可以是一串段。项目根目录的 `edit.json` 把片子排成一行段：每一段从一个来源取画面（一个页面、一张图、一种纯色），还没有来源的段画成灰卡。`bin/vh render` 看到它就按它出片，每一段各用各的画法，段与段之间是硬切，每个切点都是关键帧。

它就是 `shots.json` 长大了：每一行还是那些字段（`id`、`segment`、`reads`、`label`、`unsure`、`frame`、`at`），多一个 `src` 说这一段的画面从哪来。一个项目只留一份镜头表：有了 `edit.json`，段就是镜头，storyboard、rhythm、审阅台、thumbs、`patch --shot` 都从它读。两份都在时，这些命令都会停下，让你留一份。

单页片子不用它，什么都不变。

## 什么时候用

- **按章换引擎**：一章 canvas，一章手绘，一章 HyperFrames，各写各的页面，剪辑表把它们排起来。
- **照片推拉**：一张图加一个 `move`，由宿主自己的取景页画，浏览器解码，带颜色配置的手机照片颜色也对。
- **关卡 ② 的全长 animatic**：`bin/vh edit init <项目>` 把 `shots.json` 并成剪辑表，每镜一张灰卡，按原来的时间排；`bin/vh render` 出来就是整片长度的灰盒，之后一镜一镜换上真画面。
- **片头、片尾、黑场**：一张可复用的片名页（自己的钟），一个纯色段。

## 一个例子

一支 24 s 的讲解片，数字是编的：

```json
{
 "v": 1,
 "note": "咖啡从种子到杯子：四段",
 "fps": 30,
 "size": [1920, 1080],
 "refs": { "timeline": "audio/timeline.zh.json" },
 "sources": {
  "title": { "page": "pages/title.html", "clock": "local" },
  "farm": { "page": "farm.html", "clock": "film" },
  "roast": { "image": "assets/img/roast.jpg", "asset": "img-roast" },
  "black": { "color": "#000000" }
 },
 "tracks": [
  { "id": "V1", "entries": [
   { "id": "S01", "src": "title", "dur": 2.5, "segment": "开头", "reads": "片名" },
   { "id": "S02", "src": "farm", "end": "@l2>", "segment": "种植", "reads": ["咖啡树", "果实变红"] },
   { "id": "S03", "src": "roast", "end": "@l3:烘焙", "fit": "cover",
     "move": { "from": [0.5, 0.5, 1], "to": [0.6, 0.45, 1.3], "ease": "inOut" }, "segment": "烘焙", "reads": "豆子变深" },
   { "id": "S04", "src": null, "end": "@l5>", "segment": "冲煮", "reads": "手冲的水流", "unsure": "实拍素材还没到" },
   { "id": "S05", "src": "black", "end": "@l5>+1.5", "segment": "结尾" }
  ] }
 ],
 "chapters": [ { "t": 0, "title": "种植" }, { "t": "@|S03", "title": "烘焙" } ]
}
```

读法：S01 是片名页，画它自己的 0–2.5 s；S02 是种植那一章的页面，画片子的时间，到第 2 句念完为止；S03 是一张照片，从中间推到右上，旁白念到"烘焙"时切；S04 还没有画面，是灰卡；S05 黑场到最后一句念完再留 1.5 s。没写 `start` 的段都紧接上一段。

## 顶层字段

| 字段 | 必填 | 意思 |
|---|---|---|
| `v` | 是 | `1` |
| `note` | 否 | 一句话 |
| `fps` | 是 | 整数（24、25、30、50、60）。29.97 这类不收 |
| `size` | 是 | `[宽, 高]`，CSS px。4K 照旧 `bin/vh render --dpr 2` |
| `refs` | 否 | 引用读哪些时间源，和带表头的 events.json 一样：`timeline`（旁白时间轴）、`lead`、`music`（beats）、`timemap`，路径相对 `edit.json`，要在项目里面 |
| `sources` | 是 | `{键: 来源}`，见下一节 |
| `tracks` | 是 | `[{id, entries: [...]}]`。现在只画第一轨（V1）；上层轨以后再加 |
| `chapters` | 否 | `[{t, title}]`，`t` 可以写引用，包括 `"@|S03"`（S03 的起点）。不写时用页面段自己的章节，按钟换算 |
| `covers` | 否 | `[{id, t, title?}]`，`t` 是片子时间 |
| `video` | 否 | storyboard 和审阅台播放的视频，同 `shots.json` 的 `video` |
| `approval`、`removed` | 否 | 记下来给审阅页看，渲染不读 |

## 来源

每个来源只写一种：

| 种类 | 写法 | 说明 |
|---|---|---|
| 页面 | `{"page": "farm.html", "clock": "film"}` | 路径相对 `edit.json`，要在项目里面。`clock` 必填，没有默认值，见"页面的两种钟" |
| 图 | `{"image": "assets/img/roast.jpg"}` | png、jpg、webp、gif、avif、svg。由宿主的取景页 `tools/film/pages/still.html` 画 |
| 纯色 | `{"color": "#000000"}` | `#rgb` 或 `#rrggbb`。由 `tools/film/pages/color.html` 画 |
| （无） | 段上写 `"src": null` | 灰卡：`tools/film/pages/slate.html` 画出段的 id、segment、reads、unsure 和剩余秒数。`bin/vh check` 判失败、`bin/vh deliver` 拒绝出片，交付前一张都不能剩 |

来源都可以带 `asset`（素材台账里的 id，`bin/vh assets`）；页面和图还可以带 `sha256`（钉住这个文件，换了字节就报错；页面钉的是它自己的 HTML，它加载的文件由 render 的记录管），纯色没有文件可钉，写了也报错。视频片段、另一支片子、只出声的段，这一版还不收，写了会直接报出来。

## 段的字段

| 字段 | 用在 | 意思 |
|---|---|---|
| `id` | 全部 | 字母、数字和 `_`，全片唯一。`patch --shot`、`"@|S03"`、版本对比都按它找，改稿时别改它 |
| `src` | 全部 | `sources` 里的键，或 `null` |
| `start` | 全部 | 起点：秒、`"0:12.5"` 或引用。不写就紧接上一段（第一段是 0） |
| `end` / `dur` | 全部 | 终点（秒或引用）或长度（秒），二选一，必写。只有写了 `out` 的自己钟页面可以都不写 |
| `in` / `out` | 自己钟的页面 | 页面自己的时间：秒，或 `{"f": 12}`（按片子帧率的第 12 帧）。`in` 默认 0 |
| `speed` | 自己钟的页面 | 0.25–4，默认 1 |
| `hold` | 页面 | `true` 时段可以比页面长，多出来的停在页面的最后一帧；不写时比页面长就报错 |
| `fit`、`bg` | 图 | `contain`（默认：整张图放进画面，留边填 `bg`，默认黑）或 `cover`（铺满画面，裁掉多的） |
| `move` | 图 | `{"from": [cx, cy, z], "to": [cx, cy, z], "ease": "linear" 或 "inOut"}`：画面中心落在图的哪一点（0–1），在 `fit` 之上再放大多少（≥ 1）。`inOut` 是 (1 − cos πp) / 2，p 从段首的 0 走到段尾 |
| `transition` | 全部 | 进入这一段的转场，`{"type", "duration"}`。现在还不画：挨着灰卡的照硬切画，两段真画面之间写了它，render 会停下，`edit check` 判失败 |
| `segment`、`reads`、`label`、`unsure`、`frame`、`at` | 全部 | 和 `shots.json` 一样。`at` 是分镜格子取哪一刻（片子秒或引用） |
| `why`、`caption`、`recipe`、`seam`、`note` | 全部 | 给人和审阅页看的备注，渲染不读 |

## 时间：秒、帧和引用

- **引用由 `tools/audio/time_refs.py` 解**：`12.5`、`"@l4"`（第 4 句开始）、`"@l4:词"`（念到这个词）、`"@l4>"`（念完），都可以加减秒；`{"$music": [24, 1]}`（第 24 小节第 1 拍）；`"@#e2"`（时间映射的事件）。和页面里的 cue 是同一套写法。段的起止不能挂在别的段上；`"@|S03"`、`"@|S03>"` 只给章节、封面用。
- **秒变帧只有两个函数**（`tools/timegrid.py`，JS 里是 `tools/film/timegrid.mjs`）：边界用 `frame_from(t) = ⌈t·fps − 10⁻⁶⌉`，第 k 帧属于 [起点, 终点) 当且仅当起点 ≤ k/fps < 终点；"这一刻是哪一帧"用 `frame_at(t) = ⌊t·fps + 10⁻⁶⌋`。所以 10.04 s 的页面直接渲是 302 帧，写成 `end: 10.04` 的一段也是 302 帧。
- **长度这样定**：起点是写的，或上一段的终点；终点是写的 `end`，或起点加 `dur`，或（写了 `out`）起点加 (out − in) / speed。解好之后只用整数帧。
- **排不下就报错**：段间有空（会出黑帧）、重叠、短于一帧、`out` 和 `end` 对不上（差半帧以上）。要黑场就放一个纯色段。
- **推荐写法**：每段只写 `end`，挂在旁白或拍子上，起点自动紧接。换了配音，切点跟着字走，中间不会出缝。

`bin/vh edit build` 每次都说片长、帧数、各种来源有几段、还剩几张灰卡，以及和上一次 build 比，哪些段挪了、变长变短、换了来源。退出码：0 写好了；1 排不下；2 文件、格式或引用错误（一次列完，没有的 id 会给最接近的）。

## 页面的两种钟

- **`film`**：页面画片子的时间 t，和单独渲这个页面完全一样，内部的 cue 照旧挂在旁白上。适合为这支片子写的章节页。只有一段的剪辑表（`end` 写页面的 `duration`）渲出来和直接渲这个页面逐帧相同。
- **`local`**：页面画自己的时间，u = in + (t − 段起点) · speed。适合片名卡、可复用的组件页、从别处拿来的页面。自己钟的页面不该挂旁白：`bin/vh edit check` 和 `bin/vh cues` 看到它有 cue 会说一句。

两件事 render 开工前查（`bin/vh edit check` 有浏览器时也查）：页面比它的段短又没写 `hold`，停下；画片子时间的页面读的旁白时间轴、beats、时间映射和 `refs` 不是同一份（按 sha256 比），停下。所有 `film` 页面必须读同一份旁白。

剪辑表模式下宿主从 `edit.json` 所在的文件夹（项目根）起服务，页面按相对路径打开，所以 `pages/ch2/film.html` 也能读到项目根的 `audio/timeline.zh.json`。见 `engines/CONTRACT.md` 的"在序列里"。

## 解好的剪辑表

`bin/vh edit build` 写 `out/edit.resolved.json`，render 每次开工也先 build 一遍。读它的工具不再解引用：

- `edit`：`edit.json` 的路径和 sha256；`refs`：读过的时间源和它们的 sha256；
- `fps`、`size`、`frames`（总帧数）、`duration`（frames / fps）；
- `files`：每个来源的种类、路径，图的 sha256；
- `entries`：每段的 `frames: [第一帧, 下一段的第一帧]`、`start`、`end`（帧的时间，保留到毫秒）、种类、钟，原来的写法在 `ref` 里，其余字段照抄；
- `runs`：render 要画的一串串帧，每串一种画法（`page`、`still`、`slate`、`color`）和它的参数；
- `cuts`、`slates`、`chapters`、`covers`。

同一份输入写出逐字节相同的文件。

## 各命令怎么认

| 命令 | 剪辑表片子 |
|---|---|
| `render` | 先 build；按串分块，每串从自己的第一帧起每 `--gop` 帧一个关键帧，所以每个切点都是关键帧；`--fps` 必须和 `edit.json` 一样；`--alpha` 不收。默认输出 `out/edit.mp4`。sidecar 写 `"kind": "edit"`、剪辑表的哈希、每段、每串和它的块（每块一个键，说明它由什么画成） |
| `patch` | 先 build 当前的剪辑表，和片子 sidecar 里的串逐帧比：总帧数变了、或者要重画的窗口以外有一帧的画法变了，就拒绝，说是哪几段。`--shot` 收段的 id（S03）和页面段里的镜头（`S02.S05`） |
| `frames` | `--at t` 按 t 落在的那一段画；`--entry S03 --at 2` 是 S03 开始后 2 s。`--covers` 这一版还不收 |
| `determinism` | 按串抽样：每串里两帧，每个切点两边各一帧 |
| `cues` | 两层：剪辑表自己的起止（写法和解出来的秒），每个页面段的 cue（换算到片子时间）；`--save` 两层都存，下次说谁挪了 |
| `storyboard`、`rhythm` | 段就是镜头，不用浏览器读；格子角上标来源种类，灰卡是灰格；没有视频时按片子的画法取帧 |
| 审阅台、`thumbs` | 段就是镜头；thumbs 读片子 sidecar 里的段和页面里的镜头 |
| `check` | 还剩灰卡就判失败；画它的图在 render 之后变了，提醒；每条有时间的发现都标上它落在哪一段 |
| `deliver` | 还剩灰卡就不出片 |
| `versions` | 每一版记剪辑表的哈希；`compare` 两版时按段说谁挪了、谁换了来源 |
| `edit check` | build 的检查，加上 build 之后变了的文件、每个来源的许可（BRIEF 的 `Assets:`，strict 不收 NC、ND 和未知的，台账读不了也判失败）、render 会停下的转场、剩下的灰卡，有浏览器时再查每个页面（页面读不成也判失败，因为这几项就没查） |

## 这一版不做的

转场、上层轨（字幕、叠层）、把别的段的画面喂给页面、视频片段、另一支片子、只出声的段、页面里的 `<video>`，以及 `frames --covers`。格式里留了位置的（`transition`、`inputs`），写了会被拒绝或照硬切画，不会悄悄当成别的意思。
