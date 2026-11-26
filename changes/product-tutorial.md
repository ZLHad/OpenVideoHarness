**第 12 类视频：产品使用教程，操作用代码重做、不录屏**
- Why: 一支 5 分 17 秒的使用教程做完了，它的做法（真界面一步一张截图按时间放、拼音打字和键盘、逐处定停顿、只看节奏的一轮评审）值得每支同类片子直接用，不用再从头摸。
- 新类型文档 `video-types/12-product-tutorial.md`：先在干净的副本里把产品真走一遍，大纲按"看完能做"排，一步一镜，停顿加在新画面出来以后，字幕句号处断，单独一轮只看叙事节奏；带单位的数都是那支片子上量的。`bin/vh new tutorial <slug>` 建 canvas-film 项目，路由表、`bin/vh types`、两份 README、官网和 Studio 的类型名都加上了它。
- 新组件 `components/ui-stage`：终端、浏览器或应用的窗口，逐字打出、粘贴、打印的行（中文走拼音和候选框），跟着按下的键盘，光标和按压，步骤标签，真截图回放（镜头在截图自己的像素里推、聚光、光圈）；canvas 和 DOM 两种落笔，`events()` 给出音效的时刻，`loader()` 按帧载入截图。
- 五张新配方：`ime-typing`（拼音打字，键盘跟着按）、`caret-character`（光标是个角色）、`step-capture`（真界面逐步回放）、`sentence-to-shot`（一句话散开，落成新镜头）、`window-assemble`（真窗口一块块拼起来），各带联系表和那支片子里用户的判例。`bin/vh recipes list --type tutorial` 连带列出发布片的界面和交互配方。
