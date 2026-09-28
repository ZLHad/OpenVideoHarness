# LESSONS

## M+ 好用的做法
- 物理画面用一个 `draw(t)` 纯函数 + 主时间线上一个 `ease:"none"` 的 proxy tween（onUpdate → draw）驱动；文字进出场仍交给 GSAP tween — 场景：卫星位置、信号波、频移曲线都要从同一个物理量推出 — 效果：乱序渲染 5 个 worker 结果一致，lint/check 全过，逻辑一处可查。
- 曲线用真实公式逐点算（v_r = v·R⊕·sinθ / d），画面上只放大"波长疏密"并用小字标"示意：已放大" — 场景：科普里既要夸张又要正确 — 效果：图表刻度 ±50 kHz、曲线峰值 46 kHz 自然落在刻度线下，正好解释"接近"。
- 动画时间和物理时间分开：卫星按天穹角匀速走，图表横轴仍是物理时间 — 场景：过顶这种"物理上一闪而过、叙事上要停留"的时刻 — 效果：真实曲线形状不变，读的时间够。
- 同一张图表对象从小（天穹下）重排到大（居中），而不是切到新图 — 场景：机制 → 量级的过渡 — 效果：没有切点，观众的视线不用重新找。
- 读数标签固定在曲线永远不经过的象限，而不是跟着点走 — 场景：S 形曲线上的实时读数 — 效果：不压线。

## M− 踩过的坑
- 竖屏 72px 字幕 16 个汉字放不下 — 原因：安全框宽 810px，72px 只放得下 11 个全角字（16 字要 1152px，比画面还宽） — 解决：字幕 ≤ 11 字，或降字号。
- 接缝两侧各用 opacity 淡变，会在切点多出一帧全空 — 原因：出场在 t_cut 前淡到 0、入场从 t_cut 起从 0 开始 — 解决：cut-on-motion 只用位移，不叠淡变；非要淡也从 0.4 起。
- push-slide 位移太小时读起来像淡出 — 原因：power4.in 的前 70% 几乎不动，0.3s 内只走了 ~125px 就被淡掉 — 解决：位移 ≥ 380px，别在出场上叠 opacity。
- zoom-through 两侧的缩放原点不同，承载物（"你"）会在切点跳位 — 解决：放大时同时平移，让承载物落到下一场景的原点。
- `hyperframes snapshot` 在 tween 起点后 1 帧拍到的仍是起点状态，和 render 不一致 — 解决：接缝细节用 render 出来的 mp4 逐帧抽（`select='between(n,a,b)'`），不要只信 snapshot。
- `npx hyperframes skills update` 和 `init` 默认写全局 `~/.claude/skills`、`~/.agents/skills` — 解决：`HYPERFRAMES_SKIP_SKILLS=1`，技能文档直接读 `references/repos/hyperframes/skills/`。
- `hyperframes init` 拒绝非空目录，而 `bin/vh new` 先建好了目录 — 解决：在临时目录 init，再拷 6 个脚手架文件进项目根。
- lint 的两条建议互相打架：`gsap_repeated_fromto_without_baseline` 建议 `tl.set(...,0)`，加了之后又报 `gsap_timeline_set_initial_hide` — 解决：基线用 timeline 外的 `gsap.set()`，后续 fromTo 加 `immediateRender:false`。
- 第一次 render 打印 "A frame failed verification, so parallel drawElement capture fell back to the screenshot path and is now off for this install" — 之后每次渲染从 13.8s 变成 ~42s（24.8s 片长）。这是写在本机安装状态里的开关（`HF_DE_PARALLEL_ROUTER=true` 可重开），不是项目设置。
- `bin/vh sheet` 的默认输出是**当前目录**下的 `out/check/`；从仓库根运行会在根目录建 `out/` — 解决：从项目目录运行，或传第 4 个参数指定输出。

## 可用命令
<!-- 第一次跑通的安装和调用命令，下个项目直接复用 -->
```bash
export DO_NOT_TRACK=1 HYPERFRAMES_SKIP_SKILLS=1          # 不发遥测、不碰全局 skills
cd OpenVideoHarness && bin/vh new short leo-doppler           # 建项目 + 模板
# init 不接受非空目录：在临时目录 init，再拷进项目
cd "$SCRATCH" && npx hyperframes init leo-doppler-hf --non-interactive --example=blank --resolution=portrait --skill=faceless-explainer
cp leo-doppler-hf/{hyperframes.json,index.html,package.json,meta.json,CLAUDE.md,AGENTS.md} OpenVideoHarness/projects/2026-09-28-leo-doppler/
cd OpenVideoHarness/projects/2026-09-28-leo-doppler
npx hyperframes lint
npx hyperframes check
npx hyperframes snapshot --at 0.5,1.2,2.0,...          # → snapshots/contact-sheet-*.jpg
npx hyperframes render --quality draft --fps 30 --output out/draft.mp4
npx hyperframes render --quality delivery --fps 30 --output out/final.mp4
../../bin/vh check out/final.mp4
../../bin/vh sheet out/final.mp4 6 1 out/check/final-sheet.png
ffmpeg -v error -y -i out/draft.mp4 -vf "select='between(n\,91\,100)',scale=216:-1,tile=10x1" -frames:v 1 out/check/seam.png   # 逐帧看接缝
```
