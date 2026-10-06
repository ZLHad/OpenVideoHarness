# 参与改进本仓库

这份规则管的是"改这个仓库本身"：`bin/vh`、`tools/`、引擎、文档、风格库。用这个仓库做视频，按 [CLAUDE.md](CLAUDE.md) 走，视频项目都在 `projects/` 里，不进版本库。

规则对人和 agent（Claude Code、Codex）一样适用。agent 那几条写得更细，因为它们推送时用的就是仓库主人的身份。

## 分支和推送

- **main 只接受 PR 合并。** 谁都不能直接推 main，包括仓库主人，也包括代表主人推送的 agent。这一条由 GitHub 规则集强制执行，见文末。
- **一件事一个分支、一个 PR。** 分支名：人用 `<名字>/<主题>`，agent 用 `claude/<主题>` 或 `codex/<主题>`。
- **PR 先开成草稿**，写清改了什么、为什么、怎么验证的。人看过以后转成正式 PR，用 squash 合并。合并后分支自动删除。
- **合并条件**：CI 的两项检查（Linux、macOS）都通过，分支已同步到最新的 main，评审里的对话都已解决。
- **不改写已经推送的历史。** 不 rebase、不 amend、不 force push 已经推送的分支。main 往前走了，就把 main 合进自己的分支，冲突在分支上解决。只有一种例外：自己的分支在 PR 合并后还要接着用，这时从最新的 main 重开，用 `git push --force-with-lease`。

## 给 agent 的规则

1. 只推自己的分支。不推 main，不删分支，不动 tag。
2. 推送前跑 `tools/ci.sh --committed`，全部通过才推。它在一份干净的检出上检查 HEAD，结果和 CI 一致；工作区里没提交的改动不算数。修 bug 要先复现，再证明修好，前后对比写进 PR。
3. PR 一律开成草稿。合并由人决定：人在对话里明确让 agent 合并时，agent 先确认 CI 全绿、自己审过 diff，再用 squash 合并。人让 agent"检查通过后合并"时，agent 审过 diff、把草稿转成正式 PR 后，可以打开 auto-merge（squash），不用守着 CI：必需的检查都通过后由 GitHub 合并，有一项失败就不合。规则集允许管理员在 PR 里"绕过规则合并"，这个开关只留给人用，agent 不碰。
4. 不提交 API key、`LOCAL.md`、`projects/` 和渲染产物。测试时改动了受版本管理的样片（`styles/<slug>/media/`），推送前要还原。视频不进 git（风格样片 `swatch.mp4` 除外）：成片、样片集锦这类文件放在 GitHub Release `media`，`tools/media.txt` 登记它们在仓库里的路径、文件名和 sha256，`tools/fetch_media.sh` 按它下载。往这个 Release 里放文件是维护者的事，agent 只在维护者要求时做。换一个文件时用新文件名上传（例如 `intro-film-1080p-v2.mp4`），在同一个 PR 里改 `tools/media.txt` 和引用它的链接，合并以后再删旧文件；不要覆盖 main 还在引用的文件，否则在合并之前，按 main 的校验和下载会失败。README 里要直接播放的短片段走 GitHub 的附件链接（每个不到 10 MB）。`tools/ci.sh` 会拦住视频和超过 8 MB 的文件。
5. 用户能感知到的改动，在 `CHANGELOG.md` 的 Unreleased 里记一笔。改了 `CLAUDE.md`，跑 `bin/vh sync-agents` 重新生成 `AGENTS.md`。
6. 提交信息写清改了什么、为什么。末尾可以带 `Co-Authored-By:` 署名行。
7. PR 说明里写"其余都没问题"之前，把涉及的每个子命令真跑一遍。只改措辞的 PR 也要逐句查行为变没变（#62 的评审就查出过一条底线和类型文档的阅读范围被顺手改了）。

## 推送前自查：`tools/ci.sh`

本地和 CI 跑的是同一个脚本，几秒钟跑完：

```bash
tools/ci.sh                        # 全部检查；没装 shellcheck、pyflakes、ffmpeg 时，相应几项会跳过
tools/ci.sh --committed            # 只检查已提交的内容（HEAD），和 CI 看到的一样；推送前用这个
VH_BASH=/bin/bash tools/ci.sh      # macOS：用系统自带的 bash 3.2 跑，Mac 用户默认用的就是它
```

本地没装 shellcheck 和 pyflakes 时，这两项会跳过，CI 的 Linux 机器却会查，推上去才红。有 `uv` 的话不用装（shellcheck-py 的版本可能和 CI 的不同，以 CI 为准）：

```bash
d=$(mktemp -d) && printf '#!/bin/sh\nexec uvx --from shellcheck-py shellcheck "$@"\n' > "$d/shellcheck" && chmod +x "$d/shellcheck" && PATH="$d:$PATH" uv run --no-project --with pyflakes -- bash tools/ci.sh --committed
```

每组检查都对应 v0.2.1 复查时发现的一类问题：

| 检查 | 防的是什么 |
|---|---|
| shell 语法、shellcheck | 语法错误、未加引号、ffmpeg 在 `while read` 循环里吃掉 stdin |
| 只在一个平台存在的命令 | `sed -i ''`、`stat -f`、`md5 -q` 这类只在 macOS 能用的写法（在 Linux 上会让样片渲染和建项目直接失败），以及只在 Linux 能用的 `stat -c`、`readlink -f`、`grep -P` |
| Python、JS 语法和 pyflakes | 语法错误、未定义的名字 |
| 文档和命令行一致 | `CLAUDE.md` 的命令列表和 `bin/vh` 实际的命令对不上；文档里写了不存在的 `bin/vh` 子命令；`AGENTS.md` 没有同步 |
| `bin/vh` 冒烟测试 | 打错命令也返回 0；`--effort`、`--style` 没写进项目；字幕语言被文件夹名带偏（`/home/zhang/…` 下的英文字幕被标成中文）；音频比画面短时被截断；gif 输出名算错 |

## 在 GitHub 上启用规则集

规则集的配置在 [`.github/rulesets/main.json`](.github/rulesets/main.json)。本仓库已经在 2026-09-30 按这个文件启用了规则集 `main-via-pr`，同一天打开了 Allow auto-merge（见下面第 3 步）。改了文件以后，把线上配置同步过去：`gh api --method PUT repos/ZLHad/OpenVideoHarness/rulesets/<id> --input .github/rulesets/main.json`，`<id>` 用 `gh api repos/ZLHad/OpenVideoHarness/rulesets` 查。

新仓库或 fork 从头启用时，按这个顺序来：

1. **先让 CI 跑起来。** 合并带 `.github/workflows/ci.yml` 的 PR，并确认它在一个 PR 上跑出过两项检查。要是 CI 还没跑过就启用规则集，它要求的两项检查永远等不到，所有 PR 都合不了。
2. **导入规则集。** Settings → 规则集（Rules → Rulesets）→ 新建规则集（New ruleset）→ 导入规则集（Import a ruleset），选 `main.json`。也可以在"新分支规则集"页面里手动填：

   | 页面上的项 | 填什么 |
   |---|---|
   | 规则集名称 | `main-via-pr` |
   | 执行状态 | 已启用（Active） |
   | 绕过列表 | 添加旁路 → 角色 → Repository admin，模式选"仅限拉取请求"（For pull requests only） |
   | 目标分支 | 添加目标 → 包括默认分支（Include default branch） |
   | 限制删除（Restrict deletions） | 勾选 |
   | 要求线性历史（Require linear history） | 勾选 |
   | 合并前需要拉取请求（Require a pull request before merging） | 勾选。所需批准数填 0；勾"合并前需要解决对话"（Require conversation resolution）；允许的合并方式只留 Squash |
   | 需要状态检查通过（Require status checks to pass） | 勾选。勾"合并前要求分支是最新的"（Require branches to be up to date）；添加 `checks (ubuntu-latest)` 和 `checks (macos-latest)` |
   | 阻止强制推送（Block force pushes） | 勾选 |

3. **仓库设置。** Settings → General → Pull Requests：只保留 Allow squash merging；勾选 Always suggest updating pull request branches、Allow auto-merge 和 Automatically delete head branches。命令行：`gh api -X PATCH repos/ZLHad/OpenVideoHarness -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false -F allow_update_branch=true -F allow_auto_merge=true -F delete_branch_on_merge=true`。

### 为什么这样设计

- **绕过模式选"仅限拉取请求"，不选"始终"。** agent 在这个仓库里推送时用的是主人的身份，[第一个 PR](https://github.com/ZLHad/OpenVideoHarness/pull/1) 的作者显示的就是仓库主人。给管理员开"始终绕过"，agent 也就能直接推 main。选"仅限拉取请求"以后，谁都不能直接推 main；主人在 PR 里仍然可以绕过检查强行合并，留作应急。
- **两项检查只认 GitHub Actions 报的结果**（`integration_id` 15368）。agent 拿着主人的 token，能给提交写一个同名的"成功"状态；指定来源以后，这种伪造的状态不算数。
- **提交关联不到 GitHub 账号时要多一个批准**（`require_extra_approval_for_unattributed_changes`）。GitHub 创建规则集时默认就会打开，文件里写明是为了和线上一致。agent 的提交要用关联了账号的邮箱，否则这个 PR 需要管理员在 PR 里绕过才能合并。
- **批准数填 0。** GitHub 不允许批准自己的 PR，而 agent 开的 PR 作者也是主人自己。要求 1 个批准的话，没有第二个人就什么都合不了。以后有了协作者，改成 1。
- **CI 同时跑 Linux 和 macOS。** 这次最严重的几个 bug 都只在一个平台上出现：维护者在 Mac 上一切正常，Linux 用户却渲染不了样片。在 macOS 上还专门用系统的 bash 3.2 跑 `bin/vh`。
- **要求分支是最新的。** [第一个 PR](https://github.com/ZLHad/OpenVideoHarness/pull/1) 开着的时候 main 发了 v0.2.1，两边改了同一个文件。要求同步到最新以后，CI 检查的是合并后的真实结果，不是过期的分支。
- **squash 加线性历史。** 一个 PR 在 main 上只留一个提交，和 CHANGELOG 的条目一一对应。
- **打开 auto-merge。** 它只是"检查过了就合并"的排队，规则集的每一项照样要满足，合并方式也只能是 squash；好处是 CI 要跑几分钟时，人和 agent 都不用守着。

**规则集挡得住误操作，挡不住拿着管理员 token 的 agent。** agent 用的是主人的 token，技术上仍然可以在 PR 里用管理员身份绕过检查合并，甚至改掉规则集；现在靠的是上面"给 agent 的规则"。要在技术上真正限住 agent，给它单独一个低权限身份：比如一个只有 Contents 和 Pull requests 写权限、没有 Administration 权限的 fine-grained token。

### 版本 tag 和 Release

2026-09-30 起，版本 tag（`refs/tags/v*`）由两个规则集保护。GitHub 的绕过权限按规则集算，不按单条规则算，所以拆成两个：

- `release-tags-create`（[`.github/rulesets/tags-create.json`](.github/rulesets/tags-create.json)）：限制创建，仓库管理员可以绕过，用来发新版本；
- `release-tags-immutable`（[`.github/rulesets/tags-immutable.json`](.github/rulesets/tags-immutable.json)）：限制更新和删除，没有任何人能绕过，包括管理员和用管理员 token 的 agent。真要改，只能由人临时停用这个规则集。

同一天补打了 `v0.1.0`、`v0.2.0`、`v0.2.1` 三个 Release，说明取自 `CHANGELOG.md` 对应的一节。

另有一个不是版本的 Release `media`（tag `media`，2026-10-04 由 agent 在维护者同意后建）：放样片和风格集锦的视频文件，规则见上面第 4 条。它的 tag 不移动，也不受上面两个规则集保护（规则集只管 `v*`）；换文件按第 4 条用新文件名，不覆盖。

发新版本的做法：把 `CHANGELOG.md` 的 Unreleased 改成 `## vX.Y.Z — 日期`，经 PR 合并进 main，然后由维护者在合并后的提交上建 Release（`gh release create vX.Y.Z --target <提交> --notes-file <这一节>`）。tag 一旦建好就不再移动；发错了就发一个新的补丁版本。改了这两个文件以后，用 `gh api --method PUT repos/ZLHad/OpenVideoHarness/rulesets/<id> --input <文件>` 同步线上配置，`<id>` 用 `gh api repos/ZLHad/OpenVideoHarness/rulesets` 查。
