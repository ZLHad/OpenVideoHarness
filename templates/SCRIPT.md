# SCRIPT：旁白稿

<!-- 有旁白时写：导演模式里的 script，和 voice（配音）一起在检查点 E1 定。人看的是每句多长、合起来对不对得上目标时长，不是字数。
     做法：把每句写进 audio/script.txt（# 列就是那里的 @id），用选定的配音跑一遍 `bin/vh tts`，再把 audio/timeline.json 里每句的实测时长抄进下表。
     还没选定时先用草稿音色：macOS 上 `bin/vh tts <project> say`，其他系统用 `bin/vh tts <project> edge`（要联网）；换了音色语速会变，选定后重测一遍。
     关键词标 {cue}（说到这个词时画面要出现），写进 script.txt 时去掉花括号。
     结构和 90 s / 3 min 的节拍表见 playbook/09-narrative.md；开头那一句见 playbook/10-hooks-and-packaging.md。 -->

目标 {90} s · 实测合计 {..} s · 差 {+..} s · 音色 {say 草稿 / qwen Serena} · 平均 {..} 字/秒

| # | 段 | 旁白 | 实测 s | 目标 s | 差 |
|---|---|---|---|---|---|
| {h1} | {钩子} | {两颗卫星，每秒 11.7 公里，撞了。} | {2.9} | {3.0} | {−0.1} |

## 超了先砍什么

- {哪几句可以删、可以并；哪一句必须留}

## 句子里的事实

- 每个数字都在 NOTES.md 的"待核实的事实"里；没核实的不念。
