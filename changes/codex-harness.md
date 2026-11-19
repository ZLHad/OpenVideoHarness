**Codex 可在开片前选择 GPT‑6.2，接手时从项目记录恢复**
- Why: Studio 原先在首次发送后才加载 Codex 的模型选项，外部影片也可能没加载工作台规则。Codex 新版 ACP 的登录通知此前没有被识别。
- Codex 空对话可先选模型和推理档。Studio 识别 Codex 登录状态，并把规则和状态命令的路径交给已有影片的新会话。
- Codex 出审阅页后可等人回来继续。`bin/vh status` 给出待处理反馈的轮次，CI 检查 `AGENTS.md` 是否符合 Codex 默认加载上限。
