# 目标图 + critic 卡

关卡 ② 里没把握的关键帧，先做一张"目标图"：这一帧做好以后该是什么样子。镜头写出来、渲出来以后，由一个全新上下文的 critic 把实渲的帧和目标图并排比，说出最要紧的几处差别和改法，回去改，再比。思路来自 [dream-loop](https://github.com/achimala/dream-loop)（MIT）：先用生图"梦"出一张目标截图，朝它做，再由另一个 agent 拿实渲截图来比，循环到 critic 满意。这里只借流程，文字是本仓库写的。

这张卡是可选的做法，不是关卡。用了它，`STORYBOARD.md` 那一镜的备注写一句"有目标图"。

## 什么时候用

- `studio` 的钩子、高潮，和分镜里标了"没把握"的镜头；`standard` 只在人点名要先看效果时用；`quick` 不用。
- 不用在以字、读数、图表为主的镜头上：目标图里的字和数是模型编的，没法对照。也不用在真人、新闻和史实画面上：生成图不能冒充它们。

## 目标图从哪来

按花钱多少排，先用前面的：

1. 人给的参考图、拉片截下来的帧（`playbook/07-reverse-engineer.md`）、风格预设的样片帧（`styles/<slug>/media/poster.jpg`）；
2. 先渲一帧灰盒或草图，再让生图模型照着描述把它"补完"（bin/vh image gen 的 --ref 喂这一帧）：以现有画面为底，目标和做法不会差得太远；
3. 直接生图：bin/vh image gen，先估价，每次付费调用都按预算扣，产物记进台账，算 AIGC。这是付费接口，守 CLAUDE.md 的预算底线：BRIEF 没写 `Budget:` 就不调。

提示词写"渲出来的一帧画面"，不写"概念图""插画"：要的是能对着像素比的画面，不是画家的诠释。画幅、构图、安全框和字号下限照片子的规格写进提示词。目标图放在 `assets/targets/<镜头>.png`，它不进成片；要进成片，它就是素材，照许可和 AIGC 记账。

## critic 怎么比

- **并排图**：同一时刻的实渲帧（`bin/vh frames <项目> --at <秒>`；HyperFrames 用 `npx hyperframes snapshot --at <秒> --describe false`）和目标图，拼成一张：

  ```bash
  ffmpeg -i assets/targets/S04.png -i out/frames/index-t0012.000.png -filter_complex "[0:v]scale=-2:720[a];[1:v]scale=-2:720[b];[a][b]hstack" out/check/S04-side.png
  ```

- **交给 critic**：这张并排图，和这一镜在 `STORYBOARD.md` 里要观众看懂的 reads。先不给代码，也不给作者的解释。
- **critic 交回**：最多 3 处会改变观众读法的差别（构图、主次、光、颜色、质感、字的大小和位置），每处写在画面哪里，附一条能直接做的改法，照 `playbook/02-verification.md` 第 4 层"给离散选项"的写法；已经对上了就说对上了，不凑问题。
- **不比的**：目标图里编出来的字和数、模型画糊的细节。目标图给方向，不是规格：片子有意走开的地方写进 `DECISIONS.md`，critic 不再追。

## 停在哪

- 一镜最多比 3 轮。3 轮还差得远，多半是目标图本身做不到（引擎、时长、读时），把差距写进 NOTES 的"已知局限"，不再追。
- 可选的最后一步：拿现在的实渲帧当底，再生成一张更好的目标图，再走一轮（dream-loop 的第 5 步）。只在 `studio`、预算够时做。
- 整片评审照旧（`playbook/02-verification.md` 第 5 层）。这张卡只管单镜的视觉，不代替整片的 reviewer。
