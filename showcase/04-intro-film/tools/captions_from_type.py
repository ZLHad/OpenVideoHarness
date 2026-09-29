"""Soft subtitle tracks (zh / en) from the film's on-screen kinetic type (same beat grid as js/main.js).
The film has no narration; these tracks carry the same words as the screen, for accessibility and platform CC.
usage: python3 tools/captions_from_type.py   → audio/captions.en.srt, audio/captions.zh.srt, audio/captions.json"""
import json
BEAT = 60 / 90; BAR = 4 * BEAT
bar = lambda k, b=0: (k - 1) * BAR + b * BEAT + (2 * BEAT if k >= 12 else 0)  # bar 11 is 6/4
CUES = [  # v3 Phase B (30 bars): the on-screen words, in order; node labels are grouped per station
    (0.35, bar(4) - 0.12, "frame = f(t) · Every frame is a function of time.", "frame = f(t) · 每一帧，都是时间的函数。"),
    (bar(4, 0.25), bar(5), "Request: Why does a LEO satellite's signal change pitch?", "请求：为什么低轨卫星的信号会“变调”？——多普勒频移"),
    (bar(5), bar(6) - 0.1, "Claude Opus 5.5 doesn't paint pixels. It writes the program.", "Claude Opus 5.5 不直接画像素。它写程序。"),
    (bar(6, 0.75), bar(7) - 0.25, "One sentence in. A film out.", "一句话进去，一支片子出来。"),
    (bar(7), bar(8), "Stunning, once.", "惊艳，一次。"),
    (bar(8), bar(9) - 0.66, "Dependable? Not yet.", "稳定？还不行。"),
    (bar(9), bar(10) - 0.12, "OpenVideoHarness turns Claude Code & Codex into a video studio.", "OpenVideoHarness：把 Claude Code 和 Codex 变成一间视频工作室。"),
    (bar(10), bar(11) - 0.15, "You: a one-line request → Claude Code / Codex → CLAUDE.md · AGENTS.md router", "你：一句话需求 → Claude Code / Codex → CLAUDE.md · AGENTS.md 路由"),
    (bar(11), bar(12) - 0.15, "video-types/ · 8 video workflows", "video-types/ · 8 类视频工作流"),
    (bar(12), bar(13) - 0.1, "playbook/ 9 know-how docs · templates/ 7 project templates · cases · showcase · bin/vh", "通用知识 9 篇 · 7 个项目模板 · 案例与样板 · 建项目 · 自查工具"),
    (bar(13), bar(14), "engines/ · references/repos/ 20+ repos · projects/date-slug", "engines/ 渲染引擎 · 20+ 参考仓库 · projects/日期-slug"),
    (bar(14), bar(14, 3.3), "How it works", "它是怎么工作的"),
    (bar(14, 3.3), bar(17, 0.25), "Human review ①, ② · Scene code → contact sheet → taste checklist", "人工审阅 ①② · 写 f(t) 代码 → 联系表 → 自查清单"),
    (bar(17, 0.3), bar(18) - 0.2, "Review every scene against the checklist, and fix it until it passes.", "每个场景都要自查，对着清单改到合格为止。"),
    (bar(18), bar(19), "pass · human review ③ · Final cut + LESSONS.md", "通过 · 人工审阅 ③ · 成片 + LESSONS.md"),
    (bar(19), bar(20), "Taste written down as numbers.", "把品味写成数字"),
    (bar(20), bar(21), "Sound, end to end.", "声音一条龙"),
    (bar(21), bar(22), "Ready to run. One command installs it, one command scaffolds a project.", "开箱即用：一条命令安装，一条命令建项目"),
    (bar(22), bar(23), "11 case studies + curated picks from 389 community videos", "11 个案例拆解 + 389 支社区作品精选"),
    (bar(23, 0.35), bar(24) - 0.1, "Made by an agent, following only these docs.", "都是 agent 只照着这套文档做的。"),
    (bar(27, 1), bar(28), "This film, too.", "这支片子也是。"),
    (bar(28), bar(29) - 0.62, "Even the soundtrack is code.", "连配乐都是代码。"),
    (bar(29), bar(31), "OpenVideoHarness · Video as code, for coding agents. · github.com/ZLHad/OpenVideoHarness", "OpenVideoHarness · 给 coding agent 的视频工作台 · github.com/ZLHad/OpenVideoHarness"),
]
def ts(x):
    ms = int(round(x * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
for lang, idx in (("en", 2), ("zh", 3)):
    with open(f"audio/captions.{lang}.srt", "w", encoding="utf-8") as f:
        for i, c in enumerate(CUES, 1):
            f.write(f"{i}\n{ts(c[0])} --> {ts(c[1])}\n{c[idx]}\n\n")
json.dump([{"start": round(a, 3), "end": round(b, 3), "en": e, "zh": z} for a, b, e, z in CUES], open("audio/captions.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(CUES), "cues → audio/captions.en.srt, audio/captions.zh.srt, audio/captions.json")
