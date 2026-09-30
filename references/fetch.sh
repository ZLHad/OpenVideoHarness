#!/usr/bin/env bash
# 拉取参考仓库到 references/repos/，供 agent 阅读。可重复运行以更新。
# 这些是只读参考：不要在里面改代码，要用就复制到 projects/ 下。
#
# 中和（neutralize）：很多仓库自带 .claude/、.agents/（skills、settings）、CLAUDE.md、AGENTS.md、.mcp.json，
# 而且不只在根目录（hyperframes-launches 的每个子项目都有自己的 CLAUDE.md）。
# Claude Code / Codex 读到子目录文件时会自动加载它们，可能让别人的规则劫持本仓库的路由。
# 所以拉取后把所有层级的这些文件统一改名为 _upstream_*（内容照样可读，但不会被自动加载）；更新前先还原，保证 git pull 不冲突。
#
# 用法：bash references/fetch.sh               拉取或更新全部
#       bash references/fetch.sh <dir>         只处理一个（dir 是下表第二列，例如 lemo-opuscar）
#       bash references/fetch.sh --neutralize  不联网，只对已拉取的仓库重新做一遍中和
set -euo pipefail
cd "$(dirname "$0")" && mkdir -p repos && cd repos
ARG=${1:-}

AGENT_FILES=(.claude .agents CLAUDE.md CLAUDE.local.md AGENTS.md .mcp.json)
agent_paths() { # 列出 $1 下所有层级的 agent 文件（跳过 .git），深的在前，保证先改子项再改父目录
  local d=$1 f args=()
  for f in "${AGENT_FILES[@]}"; do args+=(-name "$f" -o); done
  find "$d" -path "$d/.git" -prune -o \( "${args[@]:0:${#args[@]}-1}" \) -print | sort -r
}
restore() {    # 更新前：删掉改名副本，还原原文件，保证 git pull 不冲突
  local d=$1; [ -d "$d/.git" ] || return 0
  find "$d" -path "$d/.git" -prune -o -name '_upstream_*' -print | sort -r | while IFS= read -r p; do rm -rf "$p"; done
  git -C "$d" checkout -q -- . 2>/dev/null || true
}
neutralize() { # 更新后：改名为同目录下的 _upstream_*（git status 会把原路径显示为已删除，这是预期的）
  local d=$1 p b
  agent_paths "$d" | while IFS= read -r p; do b=$(basename "$p"); mv "$p" "$(dirname "$p")/_upstream_${b#.}"; done
  return 0
}
skip() {       # 按参数决定是否跳过这一行；--neutralize 模式只中和、不联网
  local d=$1
  if [ "$ARG" = "--neutralize" ]; then [ -d "$d" ] && neutralize "$d" && echo "ok  $d (neutralized)"; return 0; fi
  [ -n "$ARG" ] && [ "$ARG" != "$d" ]
}
SKIPPED=""
failed() {     # failed <dir> <原因>：一个上游拉不下来只跳过这一行，不中断其余仓库和调用本脚本的安装流程
  echo "skip $1 ($2)"; SKIPPED="$SKIPPED $1"
}
clone() {      # clone <owner/repo> <dir> [git clone 参数...]
  local r=$1 d=$2; shift 2
  git clone -q --depth 1 "$@" "https://github.com/$r.git" "$d" || { failed "$d" "clone failed"; return 1; }
}

full() {   # full <owner/repo> <dir>：整仓浅克隆
  skip "$2" && return 0
  restore "$2"
  if [ -d "$2/.git" ]; then git -C "$2" pull --ff-only -q || true
  else clone "$1" "$2" || return 0; fi
  neutralize "$2"; echo "ok  $2"
}
sparse() { # sparse <owner/repo> <dir> <path...>：只检出指定目录（大仓库用）
  local r=$1 d=$2; shift 2
  skip "$d" && return 0
  restore "$d"
  if [ ! -d "$d/.git" ]; then clone "$r" "$d" --filter=blob:none --sparse || return 0; fi
  git -C "$d" sparse-checkout set "$@" && git -C "$d" pull --ff-only -q || true
  neutralize "$d"; echo "ok  $d ($*)"
}
textonly() { # textonly <owner/repo> <dir>：只检出代码和文档，跳过视频、音频、图片、字体（素材很大的仓库用）
  local r=$1 d=$2 fresh=
  skip "$d" && return 0
  restore "$d"
  if [ ! -d "$d/.git" ]; then clone "$r" "$d" --filter=blob:none --no-checkout || return 0; fresh=1; fi
  git -C "$d" sparse-checkout set --no-cone '/*' '!*.mp4' '!*.mov' '!*.webm' '!*.mkv' '!*.gif' '!*.mp3' '!*.wav' '!*.m4a' '!*.aac' '!*.flac' \
    '!*.png' '!*.jpg' '!*.jpeg' '!*.webp' '!*.psd' '!*.ttf' '!*.otf' '!*.woff' '!*.woff2' '!*.zip' '!*.pdf' '!*.onnx' '!*.bin'
  # 新克隆只需检出；已有克隆要 pull（空参数的 checkout 总是成功，放在 || 前面会让 pull 永远跑不到）
  # 新克隆的检出要联网取文件：失败就删掉这个空壳，下次重新克隆
  if [ -n "$fresh" ]; then git -C "$d" checkout -q || { rm -rf "$d"; failed "$d" "checkout failed"; return 0; }
  else git -C "$d" pull --ff-only -q || true; fi
  neutralize "$d"; echo "ok  $d (text only)"
}

# 案例源码
full   JohnHeibel/PDoomVideo                   PDoomVideo                 # 歌词 MV，p5.brush，无 license：只读参考
full   ledbetterljoshua/functional-emotions-video functional-emotions-video # MV，歌词对齐 + 7 个 subagent 并行
full   heygen-com/hyperframes-launches         hyperframes-launches       # HeyGen 发布会视频源码（产品宣传范例）
textonly WinterArc21/Battle-of-Austerlitz-Film Battle-of-Austerlitz-Film  # 5 分钟 WebGL2 历史长片：SRTM 地形、Kokoro 旁白定镜头时长、events.js 推导音效（无 license：只读；成片 mp4 不拉，深读见 cases/opus55-gallery.md 第 6 节）
# 框架文档与 skills
sparse heygen-com/hyperframes                  hyperframes    skills .claude/skills   # motion-doctrine、字幕审美、风格预设、各工作流 skill
full   remotion-dev/skills                     remotion-skills
sparse showlab/Code2Video                      Code2Video     prompts src      # 锚点网格 prompt、ScopeRefine
sparse AmitSubhash/3brown1blue                 3brown1blue    src/three_b1b/skill  # 3b1b 式讲解 + 论文讲解规则

# 社区清单与精选 skill（清单 CC0；精选条目的说明见 references/community-skills.md）
sparse   zhuyansen/awesome-claude-video-skills  awesome-claude-video-skills data   # 183 个视频 skill 的分类清单与 skills.json
full     yihui-dev/awesome-opus5-5-videos       awesome-opus5-5-videos     # 389 支 Opus 5.5 代码视频 + 作者公开的 prompt（无 license：只读，精选见 cases/opus55-gallery.md）
full     zhuyansen/awesome-opus-5.5-video       opus55-catalog-zhuyansen   # 第二份 Opus 5.5 作品目录，只有元数据 cases.json，prompt 原文在网站上（无 license：只读，见 cases/opus55-gallery.md 第 5 节）
textonly athemeroy/awesome-opus-5-5-videos      opus55-guide-athemeroy     # Opus 5.5 视频的研究型目录：168 条逐条核对来源、7 条制作路径、配色模式研究、制作 brief 模板（CC BY 4.0）
full     buildwithhanif/claude-animation-skill  claude-animation-skill     # 代码手绘 2D 动画：细节圣经（底色→纹理→边缘）、verify 乱序一致性、编码失败不覆盖好文件（MIT）
full     Rieranthony/product-film-skill         product-film-skill         # Remotion 产品片：BRAND.md、先出 3 张风格帧、240fps 母版做运动模糊、verify.py 解码检查（MIT）
textonly kuhnhomeuk-cell/procedural-film        procedural-film            # 纯 JS 绘制并配乐的 30 秒竖屏片：一镜一 agent、评审波次、六项关卡、零外部素材（MIT）
textonly lemomo-ai/lemo-opuscar                 lemo-opuscar               # 43 种影片风格：风格 prompt + Opus 5.5 纯代码样片 + core/ 渲染与检查工具（MIT；2026-09-29 之前的快照里文档和成片为 CC BY 4.0）
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

[ -z "$SKIPPED" ] || echo "skipped (re-run later, e.g. bash references/fetch.sh <dir>):$SKIPPED"
exit 0
