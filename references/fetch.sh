#!/usr/bin/env bash
# 拉取参考仓库到 references/repos/，供 agent 阅读。可重复运行以更新。
# 这些是只读参考：不要在里面改代码，要用就复制到 projects/ 下。
#
# 中和（neutralize）：很多仓库自带 .claude/（skills、settings）、CLAUDE.md、AGENTS.md、.mcp.json。
# Claude Code 读到子目录文件时会自动加载它们，可能让别人的规则劫持本仓库的路由。
# 所以拉取后统一改名为 _upstream_*（内容照样可读，但不会被自动加载）；更新前先还原，保证 git pull 不冲突。
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p repos && cd repos

AGENT_FILES=(.claude CLAUDE.md AGENTS.md .mcp.json)
restore() {    # 更新前：删掉改名副本，还原原文件，保证 git pull 不冲突
  local d=$1; [ -d "$d/.git" ] || return 0
  rm -rf "$d"/_upstream_*; git -C "$d" checkout -q -- . 2>/dev/null || true
}
neutralize() { # 更新后：改名为 _upstream_*（git status 会把原路径显示为已删除，这是预期的）
  local d=$1 f
  for f in "${AGENT_FILES[@]}"; do [ -e "$d/$f" ] && mv "$d/$f" "$d/_upstream_${f#.}"; done
  return 0
}

full() {   # full <owner/repo> <dir>：整仓浅克隆
  restore "$2"
  if [ -d "$2/.git" ]; then git -C "$2" pull --ff-only -q || true
  else git clone -q --depth 1 "https://github.com/$1.git" "$2"; fi
  neutralize "$2"; echo "ok  $2"
}
sparse() { # sparse <owner/repo> <dir> <path...>：只检出指定目录（大仓库用）
  local r=$1 d=$2; shift 2
  restore "$d"
  if [ ! -d "$d/.git" ]; then git clone -q --depth 1 --filter=blob:none --sparse "https://github.com/$r.git" "$d"; fi
  git -C "$d" sparse-checkout set "$@" && git -C "$d" pull --ff-only -q || true
  neutralize "$d"; echo "ok  $d ($*)"
}
textonly() { # textonly <owner/repo> <dir>：只检出代码和文档，跳过视频、音频、图片、字体（素材很大的仓库用）
  local r=$1 d=$2
  restore "$d"
  if [ ! -d "$d/.git" ]; then git clone -q --depth 1 --filter=blob:none --no-checkout "https://github.com/$r.git" "$d"; fi
  git -C "$d" sparse-checkout set --no-cone '/*' '!*.mp4' '!*.mov' '!*.webm' '!*.mkv' '!*.gif' '!*.mp3' '!*.wav' '!*.m4a' '!*.aac' '!*.flac' \
    '!*.png' '!*.jpg' '!*.jpeg' '!*.webp' '!*.psd' '!*.ttf' '!*.otf' '!*.woff' '!*.woff2' '!*.zip' '!*.pdf' '!*.onnx' '!*.bin'
  git -C "$d" checkout -q 2>/dev/null || git -C "$d" pull --ff-only -q || true
  neutralize "$d"; echo "ok  $d (text only)"
}

# 案例源码
full   JohnHeibel/PDoomVideo                   PDoomVideo                 # 歌词 MV，p5.brush，无 license：只读参考
full   ledbetterljoshua/functional-emotions-video functional-emotions-video # MV，歌词对齐 + 7 个 subagent 并行
full   heygen-com/hyperframes-launches         hyperframes-launches       # HeyGen 发布会视频源码（产品宣传范例）
# 框架文档与 skills
sparse heygen-com/hyperframes                  hyperframes    skills .claude/skills   # motion-doctrine、字幕审美、风格预设、各工作流 skill
full   remotion-dev/skills                     remotion-skills
sparse showlab/Code2Video                      Code2Video     prompts src      # 锚点网格 prompt、ScopeRefine
sparse AmitSubhash/3brown1blue                 3brown1blue    src/three_b1b/skill  # 3b1b 式讲解 + 论文讲解规则

# 社区清单与精选 skill（清单 CC0；精选条目的说明见 references/community-skills.md）
sparse   zhuyansen/awesome-claude-video-skills  awesome-claude-video-skills data   # 183 个视频 skill 的分类清单与 skills.json
textonly lemomo-ai/lemo-opuscar                 lemo-opuscar               # 39 种影片风格：风格 prompt + Opus 5.5 纯代码样片（代码 MIT；指南、STYLE.md、成片 CC BY 4.0）
textonly calesthio/OpenMontage                  OpenMontage                # 全套 agent 视频制作系统：12 条管线、700+ skill/知识文件（AGPL）
textonly Vincentwei1021/video-shotcraft         video-shotcraft            # 产品片：150+ 张镜头配方卡 + Remotion（Apache-2.0；部分音效来源待核）
full     op7418/guizang-product-video-skill     guizang-product-video      # 产品更新片：复用真实产品组件、原创配乐音效（AGPL；assets/fallback 另受 BSL 1.1 约束）
full     aijiduonadegou/Paper-Cut               Paper-Cut                  # Vox 纸拼贴科普：图像模型出图→拆层→HyperFrames 代码动画（MIT）
full     pyang5166/gbro-collage-info            gbro-collage-info          # 半调纸拼贴信息动画，不用图像模型，HyperFrames（MIT）
textonly Alisa0808/vox-director                 vox-director               # Vox 纸拼贴讲解，端到端（依赖 Atlas Cloud，MIT）
textonly Vincentwei1021/video-talkcraft         video-talkcraft            # 旁白驱动的讲解动效（PolyForm Noncommercial：只读，商用需作者授权）
textonly hassancs91/claude-faceless-shorts-creator faceless-shorts-creator # 不露脸 Shorts 工厂：Remotion + ElevenLabs 逐词字幕（MIT）
textonly iart-ai/data-animation-skills          data-animation-skills      # CSV → 数字精确的动态图表（MIT）
textonly shuyicc/MathLens                       MathLens                   # 数学题讲解 → Manim 视频，中文（README 声明 CC BY-NC 4.0：只读）
textonly hi-nikola/hand-drawn-explainer-video-nikola hand-drawn-explainer  # 中文手绘知识讲解（Apache-2.0）
textonly gnipbao/story-to-handdrawn-video       story-to-handdrawn-video   # 中文故事 → 手绘日记漫画动画（MIT）
textonly AllenAI2014/remotion-guofeng-starter   remotion-guofeng-starter   # 国风纸片动画：诗/成语 → Remotion（代码 MIT；public/ 演示素材不授权商用）
full     sharon-laicc/viral-video-decomposer    viral-video-decomposer     # 拆解爆款视频：镜头级拉片 → 生产蓝图（MIT）
