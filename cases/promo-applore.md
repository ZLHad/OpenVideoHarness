# 案例：Applore 宣传片（viggo）

**类型**：15 秒的产品宣传片，由吉祥物口播介绍
**源码**：未公开，渲染栈也没有说明
**来源**：[viggo 的帖子](https://x.com/decohack/status/2104502625055949242)，[@achxvi 的 prompt 模板](https://x.com/achxvi/status/2103938227786654016)

## prompt

viggo 自己的输入只有一句话："Hi, Opus 5.5, 给我的产品做一个宣传视频，需要创意十足并且足够震撼 + 网址（applore.app）"。

他转发的模板来自 @achxvi。@achxvi 又是改写自 @ajith_io 的原版，大意是：

> make a dynamic 15-second motion graphics video about {product} that shows what an incredible motion designer you are, like it's your showreel for a résumé. go all out. here is elevenlabs key: … make a video where a character talks about {product} and how people can use it …

viggo 说几分钟就做完了。

## 画面拆解（逐帧看过）

| 时间 | 画面 |
|---|---|
| 0–1s | 光芒放射的开场 |
| 1–2s | 吉祥物 Ace 登场，它是一个带脸的光泽 app 图标。字幕 "Hey! I'm Ace, from Applore"，配音应该是 ElevenLabs TTS |
| 2–5s | 数字滚动到 **17,550**，"real app icons"，背后是真实 app 图标组成的图标墙 |
| 6–8s | 搜索框里打出 "cozy moon icon for a sleep app"，演示 AI 检索（"Describe it. AI finds it."） |
| 9–12s | 自己生成图标，一键导出所有尺寸（"Or make your own, and export every size in one click."） |
| 13–15s | 结尾 logo 卡：APPLORE，applore.app |

## 为什么有效

- **素材是真实的**：图标墙用的是产品库里真实的 app 图标，数字 17,550 也是产品的真实数据。
- **结构是标准的产品片节拍**：角色 hook → 规模证据（计数）→ 功能 1 演示 → 功能 2 演示 → logo 定版。
- **让模型自己选风格**："当你的动效设计作品集，go all out"，把风格决策交给了模型，炫技效果最好。

## 局限

- 品牌控制力弱：每次生成的风格都可能不一样。
- 要稳定出片时，改用 `video-types/03-product-promo.md` 的逐拍规定写法，把语域、节拍、镜头语言都写死。

## 能借用什么

- 探索阶段先用一句话 prompt，让模型给出 2–3 个风格方向，选定后再用逐拍 prompt 定稿。
- 让吉祥物或角色出来说话，用 TTS 配上同步字幕，是低成本的 hook。
- "当你的作品集"这类话，能激发模型拿出最好的水平。
