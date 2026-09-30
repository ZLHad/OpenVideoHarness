# Security policy · 安全政策

## Supported versions · 支持的版本

Fixes land on `main` and in the next release. Older releases are not patched. · 修复只进 `main` 和下一个版本，旧版本不单独打补丁。

## Reporting a vulnerability · 报告漏洞

Please report privately through GitHub: **Security → Report a vulnerability** on this repository (private vulnerability reporting). Don't open a public issue for it. You should hear back within 7 days.

请通过 GitHub 私下报告：在本仓库点 **Security → Report a vulnerability**（私密漏洞报告），不要开公开 issue。一般 7 天内回复。

## What counts · 哪些算安全问题

- A way for the tools to leak an API key: keys must only be read from environment variables, never written to files, logs or reports (hard rule 7 in `CLAUDE.md`). · 工具可能泄露 API key 的途径：key 只能从环境变量读，不能写进文件、日志或报告（`CLAUDE.md` 硬规则 7）。
- Instructions from third-party repositories reaching an agent: `references/fetch.sh` renames other projects' `CLAUDE.md`, `AGENTS.md`, `.claude/`, `.agents/` and `.mcp.json` so agents don't load them. A bypass is a security issue. · 第三方仓库的指令被 agent 读到：`references/fetch.sh` 会把别人的 `CLAUDE.md`、`AGENTS.md`、`.claude/`、`.agents/`、`.mcp.json` 改名，防止被 agent 自动加载。能绕过它就算安全问题。
- Shell or code injection through `bin/vh` arguments, project names, scripts or score files. · 通过 `bin/vh` 参数、项目名、稿子或配乐文件注入命令或代码。

Bugs in rendering, timing or sound quality are regular issues. · 渲染、时序、音质上的毛病请开普通 issue。
