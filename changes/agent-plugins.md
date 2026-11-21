**在 Claude Code 和 Codex 里一条命令就能装上；打开 Studio 时悄悄更新旧的 skill 短桩**
- Why: 原来要么跑安装脚本，要么用 `npx skills add`；在 agent 自己的插件市场里搜不到、装不上。另外，旧版本写下的 skill 短桩过期以后，要等人看了 `bin/vh doctor` 再手动重装。
- 仓库本身是一个插件市场：`.claude-plugin/marketplace.json`（Claude Code）和 `.agents/plugins/marketplace.json`（Codex），指向 `plugins/open-video-harness/`，里面是两个 skill 的副本（`bin/vh sync-agents` 从 `skills/` 复制，CI 核对一致）和两家各自的清单。不钉版本号，更新跟着 main 走。Claude Code：`/plugin install open-video-harness --marketplace ZLHad/OpenVideoHarness`；Codex：`codex plugin marketplace add ZLHad/OpenVideoHarness`，再 `codex plugin add open-video-harness@open-video-harness`。装上的仍是指针：第一次用时征得同意，再装完整的工作台。
- `bin/vh studio` 打开之前，把本克隆写过、而 doctor 判为过期的短桩重写一遍，只在 stderr 说一行；没给某个 agent 装过的不装，指向另一个还在的克隆的不动。
