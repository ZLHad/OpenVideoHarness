# changes/：还没发版的改动

每个 PR 在这里加一个文件，记它改了什么。文件名是 `<简短名>.md`，用小写字母、数字和连字符，比如 `changelog-notes.md`。

一个文件就是一条 CHANGELOG 条目，写法照旧：第一行是粗体标题，下面一行一条，先写为什么。

```markdown
**一句话说清改了什么**
- Why: 为什么要改。
- 改了哪些地方，人用起来有什么不同。
```

两个 PR 各加各的文件，不会在同一行上冲突。`tools/land.py` 用 PR 加的那个文件写 squash 说明。

- 看还没发版的改动：`python3 tools/changes.py show`（`--titles` 只列标题）。按落地先后排，新的在前；`CHANGELOG.md` 的 Unreleased 里旧写法的条目也一起排。
- 发版：`python3 tools/changes.py release vX.Y.Z` 把这里的文件合进 `CHANGELOG.md` 的新一节，再删掉它们。步骤见 `CONTRIBUTING.md` 的"版本 tag 和 Release"。
- 发版只收已经提交的文件：没提交的、提交后又改过的，它不收，会说是哪个。
- `tools/ci.sh` 跑 `python3 tools/changes.py check`，查每个文件的名字和格式；git 忽略的文件（比如 `.DS_Store`）不算。
- 旧写法（往 `CHANGELOG.md` 的 Unreleased 加条目）到第一次发版为止还认；发版后那个标题没了，要写就写在这里。
