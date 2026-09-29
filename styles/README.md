# 风格库：从名作里学来的 26 种口味

社区里用 Opus 5.5 做的视频，很大一部分长得差不多：暗底、发光、玻璃卡片、动态 UI。athemeroy 的主题 × 风格图谱里，"广告/发布片"这一行有 154 个文件落在"动态图形/界面"一格，是这一行最大的一格，是第二大的"三维渲染"（25）的 6 倍多（见 `references/repos/opus55-guide-athemeroy/docs/domain-style-atlas.zh-CN.md`）。agent 默认会走向最常见的那一种，所以这里给它一个明确的选择空间。

这里的每个风格都从名作里提炼出一套语法：色板、字体、构图、运动、转场、声音。每个风格都**用本仓库的工具真渲了一段 5 秒样片**。26 段样片的内容完全一样，都是标题"每一帧，都是代码。"加上"大纲 → 分镜 → 初版"三元素，差别只来自风格。

![26 种风格的样片封面](gallery.jpg)

连播版：[`gallery.mp4`](gallery.mp4)（每种风格约 1.5 秒）。

## 怎么用

1. **在关卡 ① 给人选**。从这里挑 2–3 个彼此拉得开的风格，附上样片（`<slug>/media/swatch.mp4`），让人选或混搭。不要默认只给一种口味。
2. **建项目时带上预设**：

   ```bash
   bin/vh style list                                  # 26 个风格、家族、有没有样片
   bin/vh new promo launch-film --style cutout-jazz   # 项目里多出 STYLE_PRESET.md 和 style.tokens.json，BRIEF 末尾追加预设的 prompt 块
   ```
3. **在项目的 `STYLE.md` 里只写改动**。预设是起点，不是牢笼：换一个强调色、改转场节奏都可以，写清楚改了什么、为什么改。
4. **混搭的规矩**：一个主风格，最多再借一样东西，例如借另一个风格的转场或字体；不要同时叠两种质感（半调加水墨、扫描线加纸纹）。
5. **自查**：先按预设 STYLE.md 的"自查重点"，再按 `templates/TASTE_CHECKLIST.md`。

## 26 个风格

每个目录里有：
- `STYLE.md`：学习对象、视觉语法、运动语法、声音语法、适合与不适合、禁止项、prompt 块、引擎做法、自查重点；
- `tokens.json`：机器可读的数值；
- `swatch.js`、`score.json`：样片的画面和配乐源码；
- `media/`：样片和封面。

### 电影与片头

| 风格 | 学习对象 | 一句话 | 适合 |
|---|---|---|---|
| [剪纸爵士片头](cutout-jazz/) `cutout-jazz` | Saul Bass 的片头（《金臂人》1955、《迷魂记》1958、《桃色血案》1959） | 几种纸色、剪刀边、铜管每记重音就是一刀 | 概念或产品的片头式开场 |
| [刮擦字片头](scratched-type/) `scratched-type` | 《七宗罪》片头（1995）；McLaren、Len Lye 的直接电影 | 在片基上刮出来的字，一格一格地抖 | 悬疑、犯罪、工业噪音类 MV |
| [纪念碑科幻](monumental-scifi/) `monumental-scifi` | 《银翼杀手 2049》《降临》《星际穿越》 | 巨大的形体、层层雾、极少的字 | 发布 teaser、未来题材、片名 |
| [对称粉彩绘本](symmetry-pastel/) `symmetry-pastel` | 《布达佩斯大饭店》《月升王国》 | 中轴对称、每章换色、章节字卡、甩镜 | 轻幽默的知识短片、人物小传 |
| [霓虹抽帧](neon-step-print/) `neon-step-print` | 《重庆森林》《堕落天使》《花样年华》 | 抽帧拉出光带，红绿互补，贴身手持 | 城市夜景、情绪 MV |
| [档案推拉](archival-pan-zoom/) `archival-pan-zoom` | 《黄金之城》（1957）、《南北战争》（1990） | 在静止照片上极慢地推拉，衬线小字 | 历史、人物传记、项目来历 |
| [机械钟表地图](clockwork-map/) `clockwork-map` | 《权力的游戏》片头（2011）、布拉格天文钟 | 地点是被齿轮顶出地面的黄铜机械 | 路线、版图、多地点关系 |

### 品牌与发布

| 风格 | 学习对象 | 一句话 | 适合 |
|---|---|---|---|
| [产品发布片](product-keynote/) `product-keynote` | Apple Watch 发布片（2014）、2007 年 iPhone 发布会 | 无缝背景，产品先落稳、字再出来 | 软硬件发布、功能亮点 |
| [瑞士网格动态字](swiss-grid-type/) `swiss-grid-type` | Müller-Brockmann 的音乐会与展览海报 | 可见网格、一个无衬线家族、红黑白 | 规则、流程、时间线、宣言 |
| [野兽派梗](brutalist-meme/) `brutalist-meme` | 《The Face》杂志、Internet Ugly、brutalistwebsites.com | 系统字、裸网格、每拍一刀的硬切 | 梗视频、科技推特快剪（类型 08） |

### 数据与讲解

| 风格 | 学习对象 | 一句话 | 适合 |
|---|---|---|---|
| [暗底数学](dark-math/) `dark-math` | 3Blue1Brown《线性代数的本质》 | 纯黑底，每个数学对象一个颜色 | 原理、定理、算法（类型 01） |
| [编辑部数据叙事](editorial-data/) `editorial-data` | NYT The Upshot、The Pudding | 标题就是结论句，灰加一个强调色 | 数据新闻、研究结果 |
| [气泡图现场讲](bubble-chart-story/) `bubble-chart-story` | Hans Rosling《200 个国家，200 年，4 分钟》（2010） | 一张气泡图就是舞台，时间可以快进倒回 | 群体随时间的变化 |
| [电影界面 HUD](fui-hud/) `fui-hud` | 《火星救援》《遗落战境》《银翼杀手 2049》的屏幕设计 | 点阵、发丝线、等宽读数，每个读数都是真数据 | 系统、监测、agent 的内部视角 |

### 插画与印刷

| 风格 | 学习对象 | 一句话 | 适合 |
|---|---|---|---|
| [弹性扁平 2D](bouncy-flat-2d/) `bouncy-flat-2d` | UPA《Gerald McBoing-Boing》（1950）、《生命的幻象》 | 亮底四色，几何形状靠挤压拉伸演戏 | 轻松知识短片、App 小剧场 |
| [半调漫画](halftone-comic/) `halftone-comic` | 《蜘蛛侠：平行宇宙》（2018）、Ben-Day 网点 | 网点代替渐变，套色故意不准，一拍二动 | 动作感强、节奏快的内容 |
| [孔版印刷](risograph/) `risograph` | Risograph 专色印刷 | 两三种专色叠印，永远套不准 | 温暖、独立、手作感的故事 |
| [剪影剪纸](silhouette-papercut/) `silhouette-papercut` | 《阿赫迈德王子历险记》（1926）、《猪八戒吃瓜》（1958） | 多层剪纸视差，每秒 12 格 | 童话、寓言、民间故事 |
| [水彩田园](watercolor-pastoral/) `watercolor-pastoral` | 《龙猫》《岁月的童话》的背景美术、《小鹿斑比》 | 湿画天空，风一波一波吹过草地 | 治愈系、季节自然、慢歌 MV |

### 中国美学

| 风格 | 学习对象 | 一句话 | 适合 |
|---|---|---|---|
| [水墨](ink-wash/) `ink-wash` | 《小蝌蚪找妈妈》（1960）、《牧笛》（1963）、《山水情》（1988） | 一滴墨晕开成远山，大片留白 | 寓言、哲思、传统文化 |
| [敦煌](dunhuang-mural/) `dunhuang-mural` | 莫高窟第 257 窟《鹿王本生图》、第 320 窟飞天、《九色鹿》（1981） | 矿物色、铁线描、飞天长飘带 | 丝路、历史、横卷叙事 |
| [皮影](shadow-puppet/) `shadow-puppet` | 中国皮影戏（2011 年列入人类非遗名录） | 油灯背光的布幕，关节皮影和三根签子 | 民间故事、戏曲、台前幕后 |
| [国潮](guochao-festive/) `guochao-festive` | 桃花坞等木版年画、《大闹天宫》 | 红底金线、粗宋大字、纹样逐拍铺开 | 节日、国风发布、竖屏 hook |

### 复古与科技

| 风格 | 学习对象 | 一句话 | 适合 |
|---|---|---|---|
| [工程蓝图](blueprint/) `blueprint` | 晒图（1842）、美国专利图规范 | 白线按制图顺序画出，尺寸随零件实时变化 | 结构、机制、系统架构 |
| [CRT 终端](crt-terminal/) `crt-terminal` | 《异形》飞船屏幕、《战争游戏》、VT100 | 单色荧光、等宽字符、打字和余辉 | 代码、黑客、系统日志 |
| [合成器浪潮](synthwave-outrun/) `synthwave-outrun` | 《电子世界争霸战》（1982）、《Out Run》（1986） | 条纹落日、霓虹透视网格、铬字、录像带质感 | 复古科技、游戏、强节拍片头 |

本仓库自己的介绍片属于"纪念碑科幻"一族；showcase 01 和 03 分别接近"水彩田园"和"暗底数学"。

## 原则

- **学语法，不复制作品**：
  - 不用原作的角色、logo、具体镜头和素材；
  - 在世作者和导演的名字只出现在"学习对象"表里，prompt 块只描述语法，不写"in the style of 某人"；
  - 每个预设都有一行"不照搬"。
- **文化题材要准确、要尊重**：
  - 不把不同朝代、不同地区的纹样混成一锅；
  - 不堆"东方元素套餐"；
  - 飞天不长翅膀，中国皮影不和 wayang kulit 混为一谈。
- **声音也是风格的一半**：每个样片的配乐都按该风格的声音语法写，用 `bin/vh music` 合成。和全仓库一样，片中不许出现数字静音；风格需要的"静"都做成屏息，保留一层底垫。
- **只用本机字体**：字体通过 `@font-face local()` 引用，不分发字体文件。本机没有的字体会回退，每个 STYLE.md 都注明样片实际用了什么字。
- **事实要核实**：年份、作者、出处都查过，拿不准的标"未核实"。

## 加一个新风格

1. **拉片**：用 `playbook/07-reverse-engineer.md` 拆解 1–3 部作品，写下能执行的规律：hex、帧数、缓动曲线、字体、配器。
2. **写文档**：复制 `_TEMPLATE.md` 写 `STYLE.md`，按其他预设的键写 `tokens.json`。
3. **写样片**：从 `_swatch/demo/` 复制 `swatch.js`，按 `_swatch/README.md` 的内容规格写；想要声音就加 `score.json`。
4. **渲染迭代**：用 `bin/vh style <slug> --draft --hud` 反复改，满意后跑 `bin/vh style <slug>` 出正式样片，渲染器会自动检查帧数、错误卡片、冻帧和音频。
5. **检查确定性**：`bin/vh style check <slug>`，比较无损帧。
6. **更新总览**：`bin/vh style gallery --mp4` 重建 `gallery.jpg` 和 `gallery.mp4`，再在上面的表里加一行。

## 和其他风格库的关系

| 来源 | 规模 | 关系 |
|---|---|---|
| [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) 的 `styles/` | 39 种，每种有 STYLE.md 和纯代码样片 | STYLE.md 为 CC BY 4.0；有对应项的预设，在"相关资源"里写明参考并署名。没收进来的（浮世绘、木刻、彩色玻璃、装饰艺术等）可以直接读它的文档 |
| HyperFrames `hyperframes-creative/references/` | 8 种设计师风格 | 偏 UI 和品牌，本库的"产品发布片""瑞士网格"与它相近 |
| OpenMontage `styles/*.yaml` | 6 种 | 偏讲解和商务 |
| story-to-handdrawn-video 的风格资产 | 327 种手绘画风和配色 | 需要生图模型，本库只借它"同一场景横向比较"的展示方法 |

以上都在 `references/repos/` 下，只读，许可证结论见 `references/community-skills.md`。
