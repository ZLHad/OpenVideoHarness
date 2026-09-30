<!-- Open as a draft. See CONTRIBUTING.md. · 先开成草稿，规则见 CONTRIBUTING.md。 -->

## What and why · 改了什么、为什么

## How it was verified · 怎么验证的
<!-- For a bug fix: how you reproduced it, and before / after. · 修 bug：怎么复现的，改前改后对比。 -->

## Checklist · 自查
- [ ] `tools/ci.sh --committed` passes · 通过
- [ ] User-visible change noted in `CHANGELOG.md` → Unreleased · 用户能感知的改动已记进 CHANGELOG
- [ ] Changed `CLAUDE.md` → ran `bin/vh sync-agents` · 改了 CLAUDE.md 已同步 AGENTS.md
- [ ] No API keys, `LOCAL.md`, `projects/` or render output committed · 没有提交 key、LOCAL.md、projects/ 和渲染产物
- [ ] Swatch media under `styles/<slug>/media/` changed only on purpose · 样片媒体只在有意更新时才改
- [ ] README changes made in both `README.md` and `README.zh-CN.md` · README 中英文两份都改了
