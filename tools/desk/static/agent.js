"use strict";
/* The agent column (docs/proposals/02-studio-client.md, 2): the agents installed on this machine (Claude Code, Codex,
   DeepSeek Harness), talked to in the column beside the film. The server (tools/desk/agents.py) runs them and keeps each
   conversation as events; this page reads them as Server-Sent Events from /api/p/<key>/agent/<id>/events and draws: what you
   said, the agent's words as they come, each thing it does as a card (a file read, a command, a change with its diff), a card
   when it asks before doing something, its plan, and at the top which agent, what it is doing, its mode, model and effort,
   the context it uses and what it costs. The column's other tab is this round (what waits for you, your notes): studio.js.

   Three rules this file keeps, because the server can only check so much:
   - Only the person's typing reaches the agent: send() takes the text box's value, from a real key press or click
     (event.isTrusted). Nothing the page shows (a project file, the agent's own words) is ever put into the box or sent.
   - Only the person answers a request: an option button, really clicked. Nothing answers by itself.
   - Every text from the agent or a project is escaped before it is drawn; links are not made clickable. */
const ASTR = {
  zh: {
    tab_chat: "对话", tab_round: "这一轮", tab_ask: "待批准 {n}", tab_dec: "待你定 {n}", ask_bar: "{a} 在等你点头：{x}", ag_pick: "用哪个 agent", ag_new: "新对话", ag_hist: "历史", ag_hist_none: "这支片子还没有别的对话",
    ag_idle: "空闲", ag_lookonly: "只能看", ag_ready: "可以说了", ag_fresh: "还没开始", ag_thinking: "在想", ag_working: "在做", ag_writing: "在写回复", ag_waiting: "等你批准",
    ag_stopping: "正在停", ag_gone: "已停止", ag_starting: "在启动", ag_doing: "在{v}：{x}",
    set_mode: "模式", set_model: "模型", set_effort: "推理", set_more: "更多设置", set_personal_off: "不带个人设置",
    u_ctx: "上下文 {u} / {s}", u_cost: "这个对话花了 {c}", u_rate: "{who}：这 {w}的额度用了 {p}{r}", u_rate_out: "{who}：额度用完了，{at} 恢复",
    w_seven_day: "7 天", u_reset: "，{at} 恢复", w_five_hour: "5 小时", w_daily: "今天的", w_weekly: "这周的",
    ph_say: "对{x}说点什么…", ph_say0: "跟 {a} 说点什么…", send: "发送", stop: "停止", send_keys: "↩ 发送 · ⇧↩ 换行",
    you: "你", t_on: "对着 {x}", empty_h: "和 {a} 说话", empty_b: "它在这支片子的文件夹里干活，用的是你在终端里的登录和设置。它每读一个文件、跑一条命令、改一处，下面都会出一张卡；要动手之前问你的，会停下来等你点。", empty_c: "这里说的话会直接发给它；“这一轮”页上记的意见，要点“交给 agent”才一起交出去。可以先问一句，比如：读一下 BRIEF，告诉我还缺什么。",
    empty_dsh: "DeepSeek Harness 的回复是整段一起到的：它在做的时候，这里只显示它正在用的工具。",
    not_inst_h: "{a} 还没装到控制台里", not_inst_b: "把下面这一行复制到终端里，回车（会下载约 {s}，不放进这个项目），装好后刷新这一页。它用你自己的登录，不用另外设置；没登录的话，{l}。",
    login_claude: "在终端里运行 claude，输入 /login", login_codex: "在终端里运行 codex login", login_dsh: "在 DeepSeek Harness 桌面版里登录一次",
    copy: "复制", copied: "复制好了", no_start_h: "{a} 没有启动起来", no_start_b: "常见的原因是还没登录：{l}。它说的是：",
    busy_turn: "{a} 还在做上一句。等它做完，或者点停止。",
    busy_console: "{a} 正在这支片子上干活（另一个对话，或另一个页面）。等它做完，或者去那边停下它。",
    busy_command: "终端里正在跑 {x}（进程 {p}）。等它跑完再让 agent 动手。",
    busy_process: "终端里有 {x}（进程 {p}）开在这支片子的文件夹里，它可能正在改东西。现在让 {a} 动手，两边可能改到同一处。",
    busy_waiting: "终端里有个 agent 在等你交这一轮。现在让 {a} 动手，两边可能改到同一处。", busy_anyway: "仍然发这一句", busy_not: "先不发",
    perm_h: "{a} 想{v}，要你点头", perm_wait: "等你点", perm_by_person: "你选了：{o}", perm_by_stop: "你点了停止，取消了", perm_by_timeout: "没有页面开着，{m} 分钟后按“不行”处理了",
    perm_by_gone: "agent 停了，这一问作废", perm_by_restart: "控制台重启过，这一问作废", perm_by_turn: "这一轮结束了，这一问作废", perm_by_desk: "控制台关了，这一问作废", perm_by_locked: "控制台不再接受操作，这一问按“不行”处理了",
    o_allow_once: "允许这一次", o_allow_always: "这个对话里同类的都允许", o_reject_once: "不允许", o_reject_always: "一直不允许",
    v_read: "读", v_edit: "改", v_delete: "删", v_move: "挪", v_search: "找", v_execute: "跑", v_think: "想", v_fetch: "上网取", v_switch_mode: "换模式", v_other: "用",
    v_read_w: "读文件", v_edit_w: "改文件", v_delete_w: "删文件", v_move_w: "挪文件", v_search_w: "找文件", v_execute_w: "跑命令", v_fetch_w: "上网取东西", v_other_w: "用工具",
    st_pending: "准备中", st_in_progress: "在跑", st_asking: "等你点头", st_completed: "好了", st_failed: "没做成", st_refused: "你没允许，所以没做", out_show: "看输出", out_lines: "{n} 行",
    new_file: "新文件", own_opts: "它给的选项原文：", seen_note: "这一段比框长：滚到底，或者点“全部展开”看完，才能点允许。“不行”随时能点。", seen_all: "全部展开",
    f_title: "它给这一步的标题", f_command: "要跑的命令", f_description: "它自己的说明（是它说的，不一定准）", f_sandbox_on: "不用沙箱跑：这条命令不受沙箱限制",
    f_sandbox_off: "照常在沙箱里跑", f_bg: "在后台跑：这一轮结束了它可能还在跑", f_timeout: "最长跑多久（毫秒）", f_file: "文件", f_content: "要写进去的内容",
    f_old: "改之前", f_new: "改之后", f_all: "文件里每一处都换", f_cwd: "在哪个文件夹里跑", f_url: "要打开的网址", f_pattern: "要找的", f_where: "涉及的位置",
    f_said: "它附的话", f_other: "它请求里的内容", f_in_diff: "（就是下面改动里的那一段，一字不差）",
    too_long: "这条请求太长，这里显示不全，所以只能拒绝。", set_open: "设置", set_close: "收起", diff_cut: "太长了，只显示前面一段", thought: "它的想法", raw_said: "它的原话", plan_h: "它的计划",
    turn_cancelled: "停下了", turn_halted: "它停在这里了", turn_signed_out: "没登录，这一句没做", turn_error: "出错了：{e}", turn_took: "用了 {s}", turn_gone: "agent 中途停了",
    turn_restart: "控制台重启过，这一句没说完", n_fresh: "接着上次的话说：这个 agent 记不得前面说过什么，从这里重新开始。",
    n_gone: "agent 的进程停了。再说一句会重新启动它。", n_signed_out: "{a} 还没登录，或者登录过期了：{l}，再回来说一句就行。", n_unsupported: "agent 问了一件这一页还答不了的事（{m}），回了“不支持”。", n_restarted: "{a} 收到停止以后没有停下来：这一轮在这里结束了，它也重新启动了（再说一句会接着这个对话）。", n_locked: "控制台的地址在别处又打开过，它不再接受操作：这一轮停下了。", n_stopping: "正在停…",
    unknown: "{a} 发来一条这里还显示不了的更新（点开看原样）", working_dsh: "{a} 在做，回复会整段一起到", sec: "{n} 秒", min: "{m} 分 {s} 秒",
    m_default: "改动前都问", m_acceptEdits: "改文件不问", m_plan: "只出计划", m_auto: "危险的才问", m_bypassPermissions: "什么都不问",
    "m_read-only": "只读", "m_workspace-write": "只改项目里的", m_agent: "危险的才问", "m_agent-full-access": "不设限",
    e_off: "不推理", mdl_default: "默认", e_low: "低", e_medium: "中", e_high: "高", e_xhigh: "很高", e_max: "最高", e_ultra: "最高并分派", e_default: "默认",
    personal_on: "带上我的个人设置（放行规则、skills、插件）", personal_tip: "关掉：只带这个项目自己的设置，你的 skills、插件和放行规则都不带；模式还是 Claude Code 自己的默认，可以在上面改",
    new_h: "开一个新对话", new_go: "开始", cancel: "先不", reconnect: "连接断了，正在重连…", reload: "和控制台断开了", gone_page: "这个对话找不到了",
    err_send: "没发出去：{e}", sent_fail: "没发出去", scope_whole: "整个{x}",
  },
  en: {
    tab_chat: "Chat", tab_round: "This round", tab_ask: "{n} to allow", tab_dec: "{n} to decide", ask_bar: "{a} is waiting for your OK: {x}", ag_pick: "Which agent", ag_new: "New chat", ag_hist: "History", ag_hist_none: "No other chats in this film yet",
    ag_idle: "Idle", ag_lookonly: "Look only", ag_ready: "Ready", ag_fresh: "Not started", ag_thinking: "Thinking", ag_working: "Working", ag_writing: "Writing", ag_waiting: "Waiting for you",
    ag_stopping: "Stopping", ag_gone: "Stopped", ag_starting: "Starting", ag_doing: "{v}: {x}",
    set_mode: "Mode", set_model: "Model", set_effort: "Effort", set_more: "More settings", set_personal_off: "Without personal settings",
    u_ctx: "Context {u} / {s}", u_cost: "This chat cost {c}", u_rate: "{who}: {p} of the {w} limit used{r}", u_rate_out: "{who}: limit reached, back at {at}",
    w_seven_day: "7-day", u_reset: "; it resets {at}", w_five_hour: "5-hour", w_daily: "daily", w_weekly: "weekly",
    ph_say: "Say something about {x}…", ph_say0: "Say something to {a}…", send: "Send", stop: "Stop", send_keys: "↩ send · ⇧↩ new line",
    you: "You", t_on: "on {x}", empty_h: "Talk to {a}", empty_b: "It works in this film's folder with your own login and settings from the terminal. Every file it reads, command it runs and change it makes shows up below as a card; when it asks before doing something, it waits for your click.", empty_c: "What you say here goes to it at once; the notes on “This round” go only when you press “Send to agent”. Try: read the BRIEF and tell me what is missing.",
    empty_dsh: "DeepSeek Harness sends its reply in one piece: while it works, only the tool it is using shows here.",
    not_inst_h: "{a} isn't set up for the console yet", not_inst_b: "Copy this line into a terminal and press Enter (it downloads about {s}, kept out of this project), then reload this page. It uses your own login, nothing else to set up; if it isn't signed in, {l}.",
    login_claude: "run claude in a terminal and type /login", login_codex: "run codex login in a terminal", login_dsh: "sign in once in the DeepSeek Harness desktop app",
    copy: "Copy", copied: "Copied", no_start_h: "{a} did not start", no_start_b: "Usually it isn't signed in yet: {l}. What it said:",
    busy_turn: "{a} is still on your last message. Wait for it, or press Stop.",
    busy_console: "{a} is working on this film (in another chat or page). Wait for it, or stop it there.",
    busy_command: "{x} is running in a terminal (process {p}). Let it finish before the agent starts.",
    busy_process: "{x} (process {p}) is open in this film's folder in a terminal and may be editing. If {a} starts now, both may edit the same thing.",
    busy_waiting: "An agent in a terminal is waiting for you to send this round. If {a} starts now, both may edit the same thing.", busy_anyway: "Send this one anyway", busy_not: "Not now",
    perm_h: "{a} wants to {v}", perm_wait: "Waiting for you", perm_by_person: "You chose: {o}", perm_by_stop: "Cancelled when you pressed Stop", perm_by_timeout: "No page was open; after {m} minutes it was refused",
    perm_by_gone: "The agent stopped; this request lapsed", perm_by_restart: "The console restarted; this request lapsed", perm_by_turn: "The turn ended; this request lapsed", perm_by_desk: "The console closed; this request lapsed", perm_by_locked: "The console stopped accepting anything; this request was refused",
    o_allow_once: "Allow this once", o_allow_always: "Allow the same kind in this chat", o_reject_once: "Don't allow", o_reject_always: "Never allow",
    v_read: "read", v_edit: "edit", v_delete: "delete", v_move: "move", v_search: "search", v_execute: "run", v_think: "think", v_fetch: "fetch", v_switch_mode: "switch mode", v_other: "use",
    v_read_w: "read a file", v_edit_w: "edit a file", v_delete_w: "delete a file", v_move_w: "move a file", v_search_w: "search", v_execute_w: "run a command", v_fetch_w: "fetch from the web", v_other_w: "use a tool",
    st_pending: "getting ready", st_in_progress: "running", st_asking: "waiting for you", st_completed: "done", st_failed: "failed", st_refused: "You didn't allow it, so it wasn't done", out_show: "Output", out_lines: "{n} lines",
    new_file: "new file", own_opts: "Its options as it wrote them: ", seen_note: "This is longer than the box: scroll to the end, or press “Show it all”, before you can allow it. “No” works any time.", seen_all: "Show it all",
    f_title: "Its title for this step", f_command: "The command", f_description: "Its own description (its words, maybe not accurate)", f_sandbox_on: "Without the sandbox: nothing limits this command",
    f_sandbox_off: "In the sandbox, as usual", f_bg: "In the background: it may still run after this turn", f_timeout: "How long it may run (ms)", f_file: "File", f_content: "What it writes",
    f_old: "Before", f_new: "After", f_all: "Every match in the file", f_cwd: "The folder it runs in", f_url: "The address it opens", f_pattern: "What it looks for", f_where: "Places it touches",
    f_said: "What it added", f_other: "What it asks", f_in_diff: "(the very text of the change below)",
    too_long: "This request is too long to show whole here, so it can only be refused.", set_open: "Settings", set_close: "Hide", diff_cut: "Too long: only the start is shown", thought: "Its thinking", raw_said: "What it said", plan_h: "Its plan",
    turn_cancelled: "Stopped", turn_halted: "It stopped here", turn_signed_out: "Not signed in: this one wasn't done", turn_error: "Something went wrong: {e}", turn_took: "took {s}", turn_gone: "The agent stopped midway",
    turn_restart: "The console restarted before this finished", n_fresh: "Picking up an earlier chat: this agent can't recall what was said, so it starts over from here.",
    n_gone: "The agent's process stopped. Say something and it starts again.", n_signed_out: "{a} isn't signed in, or its login expired: {l}, then say something again.", n_unsupported: "The agent asked for something this page can't do yet ({m}); it was told no.", n_restarted: "{a} did not stop when asked: the turn was ended here and the agent restarted (say something to carry on in this chat).", n_locked: "The console's address was opened somewhere else, so it accepts nothing now: this turn was stopped.", n_stopping: "Stopping…",
    unknown: "{a} sent an update this page can't show yet (open it to see it as sent)", working_dsh: "{a} is working; its reply comes in one piece", sec: "{n} s", min: "{m} min {s} s",
    m_default: "Ask before changes", m_acceptEdits: "Edit without asking", m_plan: "Plan only", m_auto: "Ask only if risky", m_bypassPermissions: "Never ask",
    "m_read-only": "Read only", "m_workspace-write": "Edit the project only", m_agent: "Ask only if risky", "m_agent-full-access": "No limits",
    e_off: "Off", mdl_default: "Default", e_low: "Low", e_medium: "Medium", e_high: "High", e_xhigh: "Very high", e_max: "Max", e_ultra: "Max, delegating", e_default: "Default",
    personal_on: "Bring my personal settings (allow rules, skills, plugins)", personal_tip: "Off: only this project's settings, none of your skills, plugins or allow rules; the mode is still Claude Code's own default, which you can change above",
    new_h: "Start a new chat", new_go: "Start", cancel: "Cancel", reconnect: "Connection lost, reconnecting…", reload: "Lost the console", gone_page: "This chat is gone",
    err_send: "Not sent: {e}", sent_fail: "Not sent", scope_whole: "the whole {x}",
  },
};
const at = (k, vars) => { const s = (ASTR[LANG] || ASTR.zh)[k]; return s == null ? t(k, vars) : String(s).replace(/\{(\w+)\}/g, (_, v) => (vars && vars[v] != null ? vars[v] : "")); };

const AGENT = (() => {
  const TOKEN_ = deskToken();
  let KEYOK = true;   // the page holds this run's token (studio.js asks /api/hello); without it the box is not offered
  let KEYP = "", INFO = null, KIND = "", S = null, ES = null, BUSY = null, TAB = "", ERR = null, NEWBOX = false, tick = null, raf = 0;
  const kinds = () => ((INFO && INFO.agents) || []);
  const meta = (k) => kinds().find((a) => a.kind === k) || { kind: k, label: k };
  const label = () => meta(KIND).label || KIND;
  const store_ = { get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } }, set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private window */ } } };

  /* ---------- the conversation, as the events make it ---------- */
  function blank(sum) {
    return { id: sum.id, kind: sum.kind, sum, items: [], index: {}, tools: {}, perms: {}, config: {}, usage: {}, rate: null, cost: null, title: sum.title || "",
      running: false, stopping: false, live: false, gone: false, turnAt: null, last: null, seq: 0, ver: 0, personal: sum.personal !== false };
  }
  function item(key, make) { let it = S.index[key]; if (!it) { it = make(); it.key = key; it.v = 0; S.items.push(it); S.index[key] = it; } it.v++; return it; }
  function apply(e) {
    if (!S || e.seq <= S.seq) return;
    S.seq = e.seq; S.ver++; S.last = e;
    const ty = e.type;
    if (ty === "user") { item("u" + e.seq, () => ({ kind: "user", text: e.text, scope: e.scope, t: e.t })); }
    else if (ty === "turn") {
      if (e.state === "start") { S.running = true; S.stopping = false; S.turnAt = e.t; S.cur = null; }
      else { const stopped = S.stopping || S.stopAsked; S.running = false; S.stopping = false; S.stopAsked = false; item("e" + e.seq, () => ({ kind: "end", stop: stopped && !e.error ? "cancelled" : e.stop, asked: stopped, error: e.error, took: S.turnAt ? e.t - S.turnAt : null })); S.turnAt = null; }
    } else if (ty === "state") { Object.assign(S.config, e); }
    else if (ty === "permission") { const it = item("p" + e.rid, () => ({ kind: "perm", rid: e.rid, tool: e.tool || {}, options: e.options || [], answered: null, clipped: !!e.clipped })); S.perms[e.rid] = it; const tl = e.tool && S.tools[e.tool.toolCallId]; if (tl) tl.v++; }
    else if (ty === "answered") { const it = S.perms[e.rid]; if (it) { it.answered = e; it.v++; const tl = it.tool && S.tools[it.tool.toolCallId]; if (tl) tl.v++; } }
    else if (ty === "notice") {
      if (e.code === "agent_gone") S.gone = true;
      if (e.code === "stopping") { S.stopping = true; S.stopAsked = true; return; }
      item("n" + e.seq, () => ({ kind: "notice", code: e.code, method: e.method }));
    } else if (ty === "update") update(e.u || {}, e);
  }
  function update(u, e) {
    const k = u.sessionUpdate;
    const text = (u.content && u.content.type === "text") ? u.content.text || "" : "";
    if (k === "agent_message_chunk" || k === "agent_thought_chunk") {
      const kind = k === "agent_message_chunk" ? "msg" : "thought";
      const prev = S.items[S.items.length - 1];
      const id = u.messageId || "";
      if (prev && prev.kind === kind && (prev.mid === id || !id)) { prev.text += text; prev.v++; S.cur = kind; return; }
      item(kind + e.seq, () => ({ kind, mid: id, text }));
      S.cur = kind;
    } else if (k === "user_message_chunk") { /* history replayed by the agent: the log has it already */ }
    else if (k === "tool_call" || k === "tool_call_update") {
      const id = u.toolCallId || "t" + e.seq;
      const it = item("t" + id, () => ({ kind: "tool", id, d: {} }));
      for (const [a, b] of Object.entries(u)) if (b != null && !(Array.isArray(b) && !b.length && it.d[a]) && !(a === "rawInput" && b && typeof b === "object" && !Object.keys(b).length && it.d[a])) it.d[a] = b;
      S.tools[id] = it; S.cur = "tool:" + id;
    } else if (k === "plan") { item("plan", () => ({ kind: "plan", entries: [] })).entries = u.entries || []; }
    else if (k === "usage_update") {
      if (u.used != null) S.usage = { used: u.used, size: u.size };
      if (u.cost && u.cost.amount != null) S.cost = u.cost;
      const rl = u._meta && u._meta["_claude/rateLimit"]; if (rl) S.rate = rl;
    } else if (k === "session_info_update") { if (u.title) S.title = u.title; }
    else if (k === "current_mode_update") { if (S.config.modes) S.config.modes = Object.assign({}, S.config.modes, { currentModeId: u.currentModeId }); }
    else if (k === "config_option_update") { if (Array.isArray(u.configOptions)) S.config.configOptions = u.configOptions; }
    else if (k === "available_commands_update") { /* the agent's commands: not offered in this column */ }
    else item("x" + e.seq, () => ({ kind: "unknown", k: String(k || "?"), u }));
  }

  /* ---------- talking to the server ---------- */
  async function post(path, body) {
    try {
      const r = await fetch(`/api/p/${enc(KEYP)}/agent/${path}`, { method: "POST", headers: { "Content-Type": "application/json", "X-Desk-Token": TOKEN_ }, body: JSON.stringify(Object.assign({ pid: INFO && INFO.pid }, body || {})) });
      const j = await r.json().catch(() => null);
      return { ok: r.ok, status: r.status, data: j };
    } catch (e) { return { ok: false, status: 0, data: null }; }
  }
  async function load() {
    const r = await getJSON(`/api/p/${enc(KEYP)}/agents`);
    if (!r.ok || !r.data) return false;
    INFO = r.data;
    const saved = store_.get(`desk:agent:${KEYP}`) || {};
    KIND = KIND || saved.kind || (kinds().find((a) => a.installed) || kinds()[0] || {}).kind || "claude";
    return true;
  }
  function sessionsOf(kind) { return ((INFO && INFO.sessions) || []).filter((s) => s.kind === kind); }
  function open(sum) {
    close();
    if (!KEYOK) return;   // a page without this run's token opens no conversation
    S = blank(sum); ERR = null; BUSY = null;
    store_.set(`desk:agent:${KEYP}`, { kind: KIND, sid: sum.id });
    if (sum.config) Object.assign(S.config, sum.config);
    const url = `/api/p/${enc(KEYP)}/agent/${sum.id}/events?token=${enc(TOKEN_)}&after=0`;
    ES = new EventSource(url);
    ES.addEventListener("hello", (m) => { try { const h = JSON.parse(m.data); S.live = h.live; S.caps = h.caps || {}; if (h.config) Object.assign(S.config, h.config); S.gone = false; schedule(); } catch (e) { /* a bad line */ } });
    ES.onmessage = (m) => { let e; try { e = JSON.parse(m.data); } catch (x) { return; } const was = Object.keys(S.perms).filter((r) => !S.perms[r].answered).length; apply(e); schedule(); if (e.type === "permission" && TAB !== "chat" && !was) toast(at("perm_h", { a: label(), v: verbWords(e.tool) })); };
    ES.onerror = () => { if (S) { S.offline = ES && ES.readyState === 2 ? "closed" : true; schedule(); } if (ES && ES.readyState === 2 && typeof checkKey === "function") checkKey(); };   // closed: the desk restarted (a new token) or the conversation is gone
    ES.onopen = () => { if (S) { S.offline = false; schedule(); } };
    clearInterval(tick); tick = setInterval(() => { if (S && S.running) renderHead(); }, 1000);
  }
  function close() { if (ES) { ES.close(); ES = null; } clearInterval(tick); S = null; }
  async function start(kind, personal) {   // a new conversation: the agent starts (its settings show before the first word)
    KIND = kind; BUSY = null; ERR = { code: "starting" }; S = null; render();
    const r = await post("new", { kind, personal: personal !== false });
    if (r.data && r.data.id) {
      INFO.sessions = [r.data].concat((INFO.sessions || []).filter((x) => x.id !== r.data.id));
      if (r.ok) { open(r.data); ERR = null; } else { ERR = { code: r.data.error, detail: r.data.detail }; S = null; }
    } else ERR = { code: (r.data && r.data.error) || "no_start", detail: r.data && (r.data.detail || r.data.error) };
    render();
  }
  async function pickKind(kind) {
    KIND = kind; NEWBOX = false; ERR = null; close();
    store_.set(`desk:agent:${KEYP}`, { kind });
    const m = meta(kind);
    if (!m.installed) { ERR = { code: "not_installed" }; render(); return; }
    const last = sessionsOf(kind)[0];
    if (last) open(last); else S = null;
    render();
  }

  /* ---------- what the person does ---------- */
  async function send(e, despite) {
    if (!e || !e.isTrusted) return;   // only a real key press or click sends, and only what is in the box
    const ta = $("#agSay"), text = ta ? ta.value.trim() : "";
    if (!text) { if (ta) ta.focus(); return; }
    if (!S) { await start(KIND, true); if (!S) return; }
    const sc = typeof SCOPE !== "undefined" && SCOPE && SCOPE.target ? SCOPE : null;
    const scope = sc ? { kind: sc.target.split(":")[0], id: sc.target.split(":").slice(1).join(":"), t: sc.t, t1: sc.t1, module: typeof MOD !== "undefined" ? MOD : "", label: sc.label } : null;
    const btn = $("#agSend"); if (btn) btn.disabled = true;
    const r = await post(`${S.id}/say`, { text, scope, despite: !!despite });
    if (btn) btn.disabled = false;
    if (r.ok) { ta.value = ""; store_.set(`desk:agent:say:${KEYP}`, ""); BUSY = null; S.sum.turns = (S.sum.turns || 0) + 1; }
    else if (r.status === 409 && r.data && r.data.who) BUSY = r.data.who;
    else if (r.data && r.data.error) { ERR = { code: r.data.error, detail: r.data.detail }; toast(at("err_send", { e: r.data.detail || r.data.error })); }
    else toast(at("sent_fail"));
    render();
  }
  async function answer(e, rid, option) {
    if (!e || !e.isTrusted || !S) return;   // a real click on one of the options the agent offered
    const r = await post(`${S.id}/answer`, { request: rid, option });
    if (!r.ok) toast(at("err_send", { e: (r.data && r.data.error) || r.status }));
  }
  async function stop(e) {
    if (!e || !e.isTrusted || !S) return;
    S.stopping = true; renderHead();
    await post(`${S.id}/stop`, {});
  }
  async function setting(e, what, id, value) {
    if (!e || !e.isTrusted || !S) return;
    const r = await post(`${S.id}/${what}`, what === "mode" ? { mode: value } : { id, value });
    if (!r.ok) toast(at("err_send", { e: (r.data && (r.data.detail || r.data.error)) || r.status }));
  }

  /* ---------- words ---------- */
  function verbOf(tool) {   // the tool's kind, or (DeepSeek Harness says "other") its title's word
    const k = tool.kind && tool.kind !== "other" ? tool.kind : "";
    if (k) return k;
    const ti = String(tool.title || "").toLowerCase();
    return /^(read|view|cat)\b/.test(ti) ? "read" : /^(write|edit|str_replace|patch|create)/.test(ti) ? "edit" : /^(bash|shell|exec|terminal|run)/.test(ti) ? "execute"
      : /^(glob|grep|search|find|ls)\b/.test(ti) ? "search" : /^(fetch|web)/.test(ti) ? "fetch" : /^(rm|delete)/.test(ti) ? "delete" : "other";
  }
  function verbWords(tool) { const v = verbOf(tool || {}); return at("v_" + v + "_w") !== "v_" + v + "_w" ? at("v_" + v + "_w") : at("v_other_w"); }
  const PLACEHOLDER = /^(terminal|preparing file…?|read file|write file|edit file|tool|bash|read|write|glob|grep)$/i;
  function toolTitle(d) {   // what it did, in a line: the command, the file, else the agent's own title (not its "Terminal" placeholder)
    const ri = d.rawInput || {}, loc = (d.locations || [])[0];
    if (ri.command) return String(ri.command);
    if (loc && loc.path) return String(loc.path);
    if (ri.file_path) return String(ri.file_path);
    if (ri.pattern) return String(ri.pattern);
    const ti = String(d.title || d.name || "");
    return PLACEHOLDER.test(ti.trim()) ? "" : ti;
  }
  function optWords(o) { const w = at("o_" + o.kind); return w && w !== "o_" + o.kind ? w : o.name || o.optionId; }
  function secs(s) { s = Math.max(0, Math.round(s || 0)); return s < 60 ? at("sec", { n: s }) : at("min", { m: Math.floor(s / 60), s: s % 60 }); }
  function kilo(n) { return n >= 1e6 ? (n / 1e6).toFixed(n % 1e6 ? 1 : 0) + "M" : n >= 1000 ? Math.round(n / 1000) + "k" : String(n); }
  function money(c) { return c ? (c.currency === "USD" ? "$" : (c.currency || "") + " ") + (+c.amount).toFixed(c.amount < 1 ? 3 : 2) : ""; }
  function md(s) {   // the agent's words: escaped first; then code, bold, lists and line breaks (no links: a URL stays text)
    const parts = String(s || "").split(/```[\w-]*\n?/);
    return parts.map((p, i) => {
      if (i % 2) return `<pre class="ag-code">${esc(p.replace(/\n$/, ""))}</pre>`;
      return esc(p).split(/\n{2,}/).filter((para) => para.trim()).map((para) => {   // a paragraph: its lines, a run of list lines a list
        const LI = /^\s*([-*•]|\d+[.)])\s+/, out = []; let text = [], list = [];
        const flush = () => { if (text.length) out.push(`<p>${text.join("<br>")}</p>`); if (list.length) out.push(`<ul>${list.map((x) => `<li>${x}</li>`).join("")}</ul>`); text = []; list = []; };
        for (const l of para.split("\n")) {
          if (!l.trim()) continue;
          if (LI.test(l)) { if (text.length) { out.push(`<p>${text.join("<br>")}</p>`); text = []; } list.push(inline(l.replace(LI, ""))); }
          else { if (list.length) { out.push(`<ul>${list.map((x) => `<li>${x}</li>`).join("")}</ul>`); list = []; } const h = /^#{1,6}\s+/.test(l); text.push(h ? `<b>${inline(l.replace(/^#{1,6}\s+/, ""))}</b>` : inline(l)); }
        }
        flush();
        return out.join("");
      }).join("");
    }).join("");
  }
  function inline(h) { return h.replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>"); }

  /* ---------- the diff: line by line, from the agent's old and new text ---------- */
  function diffLines(a, b, full) {   // full: every line (a request to approve shows the change whole)
    const lines = (x) => { const v = String(x).split("\n"); if (v.length > 1 && v[v.length - 1] === "") v.pop(); return v; };
    const A = a == null ? [] : lines(a), B = lines(b == null ? "" : b);
    if (A.length * B.length > 250000) return full ? { rows: A.map((x) => ["-", x]).concat(B.map((x) => ["+", x])), cut: false } : { rows: B.slice(0, 200).map((x) => ["+", x]), cut: true };
    const n = A.length, m = B.length, L2 = Array.from({ length: n + 1 }, () => new Uint32Array(m + 1));
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) L2[i][j] = A[i] === B[j] ? L2[i + 1][j + 1] + 1 : Math.max(L2[i + 1][j], L2[i][j + 1]);
    const rows = []; let i = 0, j = 0;
    while (i < n || j < m) {
      if (i < n && j < m && A[i] === B[j]) { rows.push([" ", A[i]]); i++; j++; }
      else if (i < n && (j >= m || L2[i + 1][j] >= L2[i][j + 1])) { rows.push(["-", A[i]]); i++; }   // what went, then what came
      else { rows.push(["+", B[j]]); j++; }
    }
    // only the changed lines and two around each
    const keep = rows.map((r, k) => r[0] !== " " || rows.slice(Math.max(0, k - 2), k + 3).some((x) => x[0] !== " "));
    const out = []; let gap = false;
    rows.forEach((r, k) => { if (keep[k]) { out.push(r); gap = false; } else if (!gap) { out.push(["…", ""]); gap = true; } });
    return full ? { rows: out, cut: false } : { rows: out.slice(0, 400), cut: out.length > 400 };
  }
  function diffHtml(c, full) {
    const { rows, cut } = diffLines(c.oldText, c.newText, full === true);
    return `<div class="ag-diff"><div class="ag-diff-h mono">${esc(c.path || "")}${c.oldText == null ? ` <em>${esc(at("new_file"))}</em>` : ""}</div><pre>${rows.map(([s, x]) => `<span class="d${s === "+" ? "a" : s === "-" ? "r" : s === "…" ? "g" : ""}">${esc(s === "…" ? "⋯" : s + " " + x)}</span>`).join("\n")}</pre>${cut ? `<p class="ag-mute">${esc(at("diff_cut"))}</p>` : ""}</div>`;
  }
  function contentHtml(d) {   // a tool's diffs, then its output folded (the text it printed, the agent's rawOutput)
    const cs = Array.isArray(d.content) ? d.content : [];
    let h = cs.filter((c) => c && c.type === "diff").map(diffHtml).join("");
    let out = cs.filter((c) => c && c.type === "content" && c.content && c.content.type === "text").map((c) => c.content.text).join("\n");
    if (!out && typeof d.rawOutput === "string") out = d.rawOutput;
    if (!out && d._meta && d._meta.terminal_output_delta && d._meta.terminal_output_delta.data) out = d._meta.terminal_output_delta.data;
    out = String(out || "").replace(/^```\w*\n?|\n?```$/g, "").trim();
    const desc = d.rawInput && d.rawInput.description && cs.length === 1 && out === d.rawInput.description ? "" : out;
    if (desc) { const n = desc.split("\n").length; h += `<details class="ag-out"><summary>${esc(at("out_show"))} <span class="mono">${esc(at("out_lines", { n }))}</span></summary><pre>${esc(desc)}</pre></details>`; }
    return h;
  }

  /* ---------- drawing ---------- */
  function schedule() {   // a short timer, not an animation frame: a page in a hidden pane may get no frames at all, and the
    if (raf) return;     // one it waits for would never come (many events a second still draw once per tick)
    raf = setTimeout(() => { raf = 0; renderHead(); renderThread(); renderFoot(); }, 30);
  }
  function stateNow() {   // {k: word key, cls, x}: what the agent is doing, said in a few words
    if (!KEYOK) return { k: "ag_lookonly", cls: "" };
    if (!S) return ERR && ERR.code === "starting" ? { k: "ag_starting", cls: "agent" } : { k: "ag_fresh", cls: "" };
    if (S.offline === "closed") return { k: "reload", cls: "live" };
    if (S.offline) return { k: "reconnect", cls: "live" };
    if (Object.values(S.perms).some((p) => !p.answered)) return { k: "ag_waiting", cls: "wait" };
    if (S.stopping) return { k: "ag_stopping", cls: "live" };
    if (S.running) {
      const cur = S.cur || "", tl = cur.startsWith("tool:") ? S.tools[cur.slice(5)] : null;
      if (tl && !/completed|failed/.test(tl.d.status || "")) return { k: "ag_doing", cls: "agent", v: at("v_" + verbOf(tl.d)), x: cut(toolTitle(tl.d), 40) };
      if (cur === "msg") return { k: "ag_writing", cls: "agent" };
      return { k: cur === "thought" ? "ag_thinking" : "ag_working", cls: "agent" };
    }
    if (S.gone) return { k: "ag_gone", cls: "" };
    return { k: S.items.length ? "ag_idle" : "ag_ready", cls: "" };
  }
  function selectOf(o, cat) {   // one of the agent's settings as a menu, in its own words (the known ones in ours)
    const flat = []; (o.options || []).forEach((x) => (Array.isArray(x.options) ? x.options.map((y) => Object.assign({ group: x.name }, y)) : [x]).forEach((y) => flat.push(y)));
    const name = (x) => { const w = cat === "mode" ? at("m_" + x.value) : cat === "thought_level" ? at("e_" + x.value) : cat === "model" && x.value === "default" ? at("mdl_default") : ""; return w && !/^(m|e|mdl)_/.test(w) ? w : (x.group && flat.filter((y) => y.name === x.name).length > 1 ? `${x.name} · ${x.group}` : x.name || x.value); };
    return `<select data-cfg="${esc(o.id)}" title="${esc((flat.find((x) => x.value === o.currentValue) || {}).description || o.description || "")}">${flat.map((x) => `<option value="${esc(x.value)}"${x.value === o.currentValue ? " selected" : ""}>${esc(name(x))}</option>`).join("")}</select>`;
  }
  function settingsHtml() {
    if (!S) return "";
    const C = S.config || {}, opts = Array.isArray(C.configOptions) ? C.configOptions : [];
    const byCat = (c) => opts.find((o) => o.category === c && o.type === "select");
    const parts = [];
    const mode = byCat("mode");
    if (mode) parts.push(["set_mode", selectOf(mode, "mode")]);
    else if (C.modes && (C.modes.availableModes || []).length) parts.push(["set_mode", `<select data-mode="1">${C.modes.availableModes.map((m) => `<option value="${esc(m.id)}"${m.id === C.modes.currentModeId ? " selected" : ""} title="${esc(m.description || "")}">${esc(at("m_" + m.id) !== "m_" + m.id ? at("m_" + m.id) : m.name)}</option>`).join("")}</select>`]);
    const model = byCat("model"); if (model) parts.push(["set_model", selectOf(model, "model")]);
    const eff = byCat("thought_level"); if (eff) parts.push(["set_effort", selectOf(eff, "thought_level")]);
    const more = opts.filter((o) => o.type === "select" && !["mode", "model", "thought_level"].includes(o.category) && (o.options || []).length > 1);
    return `<div class="ag-set">${parts.map(([k, sel]) => `<label><span>${esc(at(k))}</span>${sel}</label>`).join("")}${more.length ? `<details class="ag-more"><summary>${esc(at("set_more"))}</summary>${more.map((o) => `<label><span>${esc(o.name || o.id)}</span>${selectOf(o, o.category)}</label>`).join("")}</details>` : ""}${S.personal ? "" : `<span class="chip quiet">${esc(at("set_personal_off"))}</span>`}</div>`;
  }
  let SETOPEN = false;   // the settings unfolded (one line otherwise)
  function headLine() {   // mode · model · effort, the context used and the cost, in a line; a click opens the settings
    if (!S) return "";
    const C = S.config || {}, opts = Array.isArray(C.configOptions) ? C.configOptions : [];
    const byCat = (c) => opts.find((o) => o.category === c && o.type === "select");
    const nameOf = (o, cat) => { if (!o) return ""; const flat = []; (o.options || []).forEach((x) => (Array.isArray(x.options) ? x.options : [x]).forEach((y) => flat.push(y)));
      const x = flat.find((y) => y.value === o.currentValue) || {}; const w = cat === "mode" ? at("m_" + x.value) : cat === "thought_level" ? at("e_" + x.value) : cat === "model" && x.value === "default" ? at("mdl_default") : "";
      return w && !/^(m|e|mdl)_/.test(w) ? w : x.name || x.value || ""; };
    let mode = nameOf(byCat("mode"), "mode");
    if (!mode && C.modes) { const m = (C.modes.availableModes || []).find((x) => x.id === C.modes.currentModeId) || {}; mode = at("m_" + m.id) !== "m_" + m.id ? at("m_" + m.id) : m.name || ""; }
    const sum = [mode, nameOf(byCat("model"), "model"), nameOf(byCat("thought_level"), "thought_level")].filter(Boolean).join(" · ");
    const use = [S.usage && S.usage.used != null && S.usage.size ? `${kilo(S.usage.used)} / ${kilo(S.usage.size)}` : "", S.cost ? money(S.cost) : ""].filter(Boolean).join(" · ");
    return `<div class="ag-line"><button type="button" class="ag-sum" id="agSum" aria-expanded="${SETOPEN}" title="${esc(at(SETOPEN ? "set_close" : "set_open"))}"><span>${esc(sum || at("set_open"))}</span><i aria-hidden="true">${SETOPEN ? "▴" : "▾"}</i></button>${use ? `<span class="ag-usetxt mono" title="${esc([S.usage && S.usage.used != null ? at("u_ctx", { u: kilo(S.usage.used), s: kilo(S.usage.size || 0) }) : "", S.cost ? at("u_cost", { c: money(S.cost) }) : ""].filter(Boolean).join(" · "))}">${esc(use)}</span>` : ""}</div>${SETOPEN ? settingsHtml() : ""}`;
  }
  function usageHtml() {
    if (!S) return "";
    const bits = [];   // the quota, when the agent warns of it: context and cost are on the head's line
    const r = S.rate;
    if (r && r.status && r.status !== "allowed") {
      const who = label(), w = at("w_" + (r.rateLimitType || "")) !== "w_" + (r.rateLimitType || "") ? at("w_" + r.rateLimitType) : "";
      const out = /reject|exceed|block/.test(r.status);
      const when = r.resetsAt ? new Date(r.resetsAt * 1000).toLocaleString(LANG === "zh" ? "zh-CN" : "en", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "";
      bits.push(`<span class="${out ? "bad" : "warn"}">${esc(out ? at("u_rate_out", { who, at: when }) : at("u_rate", { who, w, p: Math.round((r.utilization || 0) * 100) + "%", r: when ? at("u_reset", { at: when }) : "" }))}</span>`);
    }
    return bits.length ? `<div class="ag-use mono">${bits.join("")}</div>` : "";
  }
  const DRAWN = {};   // what each part of the head shows now: a part is drawn again only when its words change (a menu or a
  // button replaced under the pointer loses the click, and the agent's text streams many events a second)
  function part(id, html) { const el = document.getElementById(id); if (!el || DRAWN[id] === html) return false; el.innerHTML = html; DRAWN[id] = html; return true; }
  function renderHead() {
    const h = $("#agHead"); if (!h) return;
    if (!h.dataset.ready) { h.dataset.ready = "1"; h.innerHTML = `<div class="ag-top" id="agTop"></div><div id="agSetBox"></div><div id="agUseBox"></div>`; Object.keys(DRAWN).forEach((k) => { DRAWN[k] = null; }); }
    const st = stateNow(), word = at(st.k, { v: st.v, x: st.x });
    const el = S && S.running && S.turnAt ? secs(Date.now() / 1000 - S.turnAt) : "";
    const list = sessionsOf(KIND).filter((x) => !S || x.id !== S.id);
    const pick = `<select id="agKind" aria-label="${esc(at("ag_pick"))}">${kinds().map((a) => `<option value="${esc(a.kind)}"${a.kind === KIND ? " selected" : ""}>${esc(a.label)}${a.installed ? "" : LANG === "zh" ? "（没装）" : " (not set up)"}</option>`).join("")}</select>`;
    const top = `<span class="ag-orb" id="agOrb" aria-hidden="true"></span>${pick}<span class="ag-state" id="agState" role="status"></span>
        <span class="ag-acts"><button type="button" class="xs" id="agNew">${esc(at("ag_new"))}</button>${list.length ? `<details class="ag-hist"><summary class="xs">${esc(at("ag_hist"))}</summary><ul>${list.map((x) => `<li><button type="button" data-sid="${esc(x.id)}"><b>${esc(cut(x.title || x.first || "—", 34))}</b><span class="mono">${esc(new Date((x.last || x.created || 0) * 1000).toLocaleString(LANG === "zh" ? "zh-CN" : "en", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }))}</span></button></li>`).join("")}</ul></details>` : ""}</span>`;
    if (part("agTop", top)) {
      DRAWN.agState = null;
      $("#agKind").addEventListener("change", (e) => pickKind(e.target.value));
      $("#agNew").addEventListener("click", () => { NEWBOX = true; render(); const b = $("#agNewGo"); if (b) b.focus(); });
      $$("#agTop [data-sid]").forEach((b) => b.addEventListener("click", () => { const s = sessionsOf(KIND).find((x) => x.id === b.dataset.sid); if (s) { open(s); render(); } }));
    }
    $("#agOrb").className = "ag-orb " + st.cls;
    $("#agState").className = "ag-state " + st.cls;
    part("agState", `${esc(word)}${el ? ` <span class="mono">${esc(el)}</span>` : ""}`);
    if (part("agSetBox", headLine())) {
      const sb = $("#agSum"); if (sb) sb.addEventListener("click", () => { SETOPEN = !SETOPEN; renderHead(); });
      $$("#agSetBox select[data-cfg]").forEach((x) => x.addEventListener("change", (e) => setting(e, "config", x.dataset.cfg, x.value)));
      $$("#agSetBox select[data-mode]").forEach((x) => x.addEventListener("change", (e) => setting(e, "mode", null, x.value)));
    }
    part("agUseBox", usageHtml());
    tabs();
  }
  function emptyHtml() {
    const m = meta(KIND), l = esc(at("login_" + KIND));
    if (ERR && ERR.code === "not_installed" || !m.installed) {
      const cmd = m.install || `bin/vh desk agents install ${KIND}`;
      return `<div class="ag-empty"><h3>${esc(at("not_inst_h", { a: m.label }))}</h3><p>${at("not_inst_b", { s: esc(m.size || ""), l })}</p><div class="ag-cmd"><code class="mono">${esc(cmd)}</code><button type="button" class="btn" data-copy="${esc(cmd)}">${esc(at("copy"))}</button></div></div>`;
    }
    if (!KEYOK) return "";   // the note above the column says it once, with what to do
    if (ERR && ERR.code && ERR.code !== "starting") return `<div class="ag-empty bad"><h3>${esc(at("no_start_h", { a: m.label }))}</h3><p>${at("no_start_b", { l })}</p><pre>${esc(cut(ERR.detail || ERR.code, 600))}</pre></div>`;
    return `<div class="ag-empty"><h3>${esc(at("empty_h", { a: m.label }))}</h3><p>${esc(at("empty_b"))}</p><p class="ag-mute">${esc(at("empty_c"))}</p>${KIND === "dsh" ? `<p class="ag-mute">${esc(at("empty_dsh"))}</p>` : ""}</div>`;
  }
  function itemHtml(it) {
    const a = esc(label());
    if (it.kind === "user") return `<div class="ag-me">${it.scope && it.scope.label ? `<span class="chip">${esc(at("t_on", { x: cut(it.scope.label, 40) }))}</span>` : ""}<p>${esc(it.text)}</p></div>`;
    if (it.kind === "msg" && /^\s*(Failed to authenticate|Authentication required|Not logged in)/i.test(it.text)) return `<details class="ag-thought"><summary>${esc(at("raw_said"))}</summary><div class="ag-md">${md(it.text)}</div></details>`;
    if (it.kind === "msg") return `<div class="ag-say"><div class="ag-who"><i></i>${a}</div><div class="ag-md">${md(it.text)}</div></div>`;
    if (it.kind === "thought") return it.text.trim() ? `<details class="ag-thought"><summary>${esc(at("thought"))}</summary><div class="ag-md">${md(it.text)}</div></details>` : "";
    if (it.kind === "tool") {
      const pm = permOf(it.id);   // a request about this very tool: the question goes into its card, not a second one
      if (pm && !pm.answered) return askHtml(pm, Object.assign({}, it.d, pm.tool));
      const d = it.d, v = verbOf(d), ti = toolTitle(d), st = d.status || "pending";
      const refused = st === "failed" && pm && pm.answered && !/^allow/.test(pm.answered.kind || "");   // its failure is the person's no
      const fail = st === "failed" && !refused ? String((typeof d.rawOutput === "string" && d.rawOutput) || "").split("\n")[0] : "";
      if (refused) return `<div class="ag-tool st-refused"><div class="ag-tool-h"><span class="ag-verb">${esc(at("v_" + v))}</span><span class="ag-st">${esc(/^(page|person)$/.test(pm.answered.by) ? at("st_refused") : at("st_failed"))}</span></div>${askBox("", Object.assign({}, d, pm.tool))}${/^(page|person)$/.test(pm.answered.by) ? "" : answerHtml(pm)}</div>`;
      return `<div class="ag-tool st-${esc(st)}"><div class="ag-tool-h"><span class="ag-verb">${esc(at("v_" + v))}</span><span class="ag-ti mono" title="${esc(ti)}">${esc(ti ? cut(ti, 120) : verbWords(d))}</span><span class="ag-st">${esc(at("st_" + st) !== "st_" + st ? at("st_" + st) : st)}</span></div>${fail ? `<p class="ag-fail">${esc(cut(fail, 200))}</p>` : ""}${contentHtml(Object.assign({}, pm ? { content: pm.tool.content } : {}, d))}${pm ? answerHtml(pm) : ""}</div>`;
    }
    if (it.kind === "perm") {   // a request about no tool on screen: a card of its own
      if (S.tools[(it.tool || {}).toolCallId]) return "";
      return it.answered ? `<div class="ag-perm done">${askHead(it)}${askBox("", it.tool || {})}${answerHtml(it)}</div>` : askHtml(it, it.tool || {});
    }
    if (it.kind === "plan") return `<div class="ag-plan"><div class="ag-who"><i></i>${esc(at("plan_h"))}</div><ol>${it.entries.map((p) => `<li class="ps-${esc(p.status || "")}">${esc(p.content || "")}</li>`).join("")}</ol></div>`;
    if (it.kind === "end") {
      if (it.stop === "cancelled") return `<p class="ag-sys">${esc(at(it.asked ? "turn_cancelled" : "turn_halted"))}${it.took ? " · " + esc(secs(it.took)) : ""}</p>`;   // Codex ends a turn so after a refusal
      if (it.error && /auth/i.test(it.error)) return S.items.some((x) => x.kind === "notice" && x.code === "signed_out") ? `<p class="ag-sys bad">${esc(at("turn_signed_out"))}</p>`
        : `<p class="ag-note bad">${esc(at("n_signed_out", { a: label(), l: at("login_" + KIND) }))}</p>`;   // "Authentication required"
      if (it.error === "agent_stuck") return "";   // the notice after it says what happened
      if (it.error) return `<p class="ag-sys bad">${esc(it.error === "agent_gone" ? at("turn_gone") : it.error === "desk_restart" ? at("turn_restart") : at("turn_error", { e: cut(it.error, 160) }))}</p>`;
      return it.took ? `<p class="ag-sys">${esc(at("turn_took", { s: secs(it.took) }))}</p>` : "";
    }
    if (it.kind === "notice" && it.code === "signed_out") return `<p class="ag-note warn">${esc(at("n_signed_out", { a: label(), l: at("login_" + KIND) }))}</p>`;
    if (it.kind === "notice" && it.code === "restarted") return `<p class="ag-note warn">${esc(at("n_restarted", { a: label() }))}</p>`;
    if (it.kind === "notice" && it.code === "locked") return `<p class="ag-note bad">${esc(at("n_locked"))}</p>`;
    if (it.kind === "notice") return `<p class="ag-sys">${esc(at({ fresh: "n_fresh", agent_gone: "n_gone", unsupported: "n_unsupported" }[it.code] || "n_gone", { m: it.method || "" }))}</p>`;
    if (it.kind === "unknown") return `<details class="ag-unknown"><summary>${esc(at("unknown", { a: label() }))}</summary><pre>${esc(cut(JSON.stringify(it.u, null, 1), 2000))}</pre></details>`;
    return "";
  }
  function permOf(toolId) { let out = null; for (const p of Object.values(S.perms)) if (p.tool && p.tool.toolCallId === toolId) out = p; return out; }
  function askHead(pm) { return `<div class="ag-perm-h"><b>${esc(at("perm_h", { a: label(), v: verbWords(pm.tool || {}) }))}</b>${pm.answered ? "" : `<span class="chip warn">${esc(at("perm_wait"))}</span>`}</div>`; }
  const FIELD = { command: "f_command", description: "f_description", timeout: "f_timeout", file_path: "f_file", path: "f_file", notebook_path: "f_file",
    content: "f_content", old_string: "f_old", new_string: "f_new", cwd: "f_cwd", url: "f_url", pattern: "f_pattern" };
  function gloss(k, v) {   // a field we know, in words: [word key, class]
    if (k === "dangerouslyDisableSandbox") return v === true ? ["f_sandbox_on", "warn"] : ["f_sandbox_off", ""];
    if (k === "run_in_background") return v === true ? ["f_bg", "warn"] : ["", ""];
    if (k === "replace_all") return v === true ? ["f_all", ""] : ["", ""];
    return [FIELD[k] || "", ""];
  }
  function fieldRow(k, v, word, inDiff) {   // one field of the request: its key and its value as the agent sent them (escaped), and what it means when
    const [g, cls] = word ? [word, ""] : gloss(k, v);   // we know; a text that is the change's own (Write's content) is shown once, in the change
    return `<div class="ag-f${cls ? " " + cls : ""}"><div class="ag-fk"><span class="mono">${esc(k)}</span>${g ? `<span>${esc(at(g))}</span>` : ""}</div>${inDiff ? `<p class="ag-fv ag-mute">${esc(at("f_in_diff"))}</p>` : `<pre class="ag-fv mono">${esc(typeof v === "string" ? v : JSON.stringify(v, null, 1))}</pre>`}</div>`;
  }
  function askFields(d) {   // everything the request carries: its title, every field of its input in the agent's order (the command first),
    const ri = d.rawInput, rows = [];   // the places, what it added, the change: each whole
    const obj = ri && typeof ri === "object" && !Array.isArray(ri);
    const ti = String(d.title || "");
    if (ti && !(obj && String(ri.command) === ti) && !PLACEHOLDER.test(ti.trim())) rows.push(fieldRow("title", ti, "f_title"));
    const cs = Array.isArray(d.content) ? d.content : [];
    const diffText = new Set(cs.filter((c) => c && c.type === "diff").flatMap((c) => [c.oldText, c.newText]).filter((x) => typeof x === "string" && x.length > 0));
    if (obj) Object.keys(ri).sort((x, y) => (y === "command") - (x === "command")).forEach((k) => rows.push(fieldRow(k, ri[k], "", typeof ri[k] === "string" && diffText.has(ri[k]))));
    else if (ri != null) rows.push(fieldRow("rawInput", ri, "f_other"));
    const locs = (d.locations || []).map((l) => l && l.path).filter(Boolean);
    if (locs.length && !(obj && locs.every((x) => Object.values(ri).includes(x)))) rows.push(fieldRow("locations", locs.join("\n"), "f_where"));
    const said = cs.filter((c) => c && c.type === "content" && c.content && c.content.type === "text").map((c) => c.content.text).join("\n");
    if (said) rows.push(fieldRow("content", said, "f_said"));
    return rows.join("") + cs.filter((c) => c && c.type === "diff").map((c) => diffHtml(c, true)).join("");
  }
  function askBox(rid, d) {   // in a box of its own height: with rid, "allow" waits until the person has seen the end of it
    return `<div class="ag-askbox${rid && OPENED.has(rid) ? " open" : ""}"${rid ? ` data-rid="${esc(rid)}"` : ""} tabindex="0">${askFields(d)}</div>`
      + (rid ? `<p class="ag-seenote" hidden>${esc(at("seen_note"))} <button type="button" class="btn ghost" data-expand="${esc(rid)}">${esc(at("seen_all"))}</button></p>` : "");
  }
  function askHtml(pm, d) {   // the options in this page's words, the agent's own wording beside them (it may say what an option reaches)
    const own = pm.options.map((o) => o.name).filter(Boolean), seen = SEEN.has(pm.rid);
    return `<div class="ag-perm">${askHead(pm)}${askBox(pm.rid, d)}${pm.clipped ? `<p class="ag-note bad">${esc(at("too_long"))}</p>` : ""}<div class="ag-opts">${pm.options.map((o) => {
      const allow = /^allow/.test(o.kind || "");
      return `<button type="button" class="btn${allow ? "" : " ghost"}${o.kind === "allow_once" ? " btn-primary" : ""}" data-rid="${esc(pm.rid)}" data-opt="${esc(o.optionId)}"${allow ? ` data-allow="1"${pm.clipped ? ' data-clip="1"' : ""}${pm.clipped || !seen ? " disabled" : ""}` : ""}>${esc(optWords(o))}</button>`;
    }).join("")}</div>${own.length ? `<p class="ag-mute">${esc(at("own_opts"))}${own.map((x) => `「${esc(x)}」`).join(" ")}</p>` : ""}</div>`;
  }
  const SEEN = new Set(), OPENED = new Set();   // requests whose whole text the person has had on screen; those unfolded
  let RO = null;
  function unlock(box) {
    const card = box.closest(".ag-perm"); if (!card) return;
    card.querySelectorAll("button[data-allow]").forEach((b) => { if (!b.dataset.clip) b.disabled = false; });
    const n = card.querySelector(".ag-seenote"); if (n) n.hidden = true;
  }
  function judge(box) {   // seen when it all fits, once scrolled to its end, or unfolded; a box with no size yet (a hidden pane) waits
    const rid = box.dataset.rid; if (!rid) return;
    if (SEEN.has(rid)) return unlock(box);
    if (!box.clientHeight) return;
    if (box.scrollHeight - box.clientHeight <= 2 || box.scrollTop + box.clientHeight >= box.scrollHeight - 2) { SEEN.add(rid); return unlock(box); }
    const n = box.closest(".ag-perm") && box.closest(".ag-perm").querySelector(".ag-seenote"); if (n) n.hidden = false;
  }
  function gateAsks(th) {
    th.querySelectorAll(".ag-askbox[data-rid]").forEach((box) => {
      if (box.dataset.wired) return judge(box);
      box.dataset.wired = "1";
      box.addEventListener("scroll", () => judge(box), { passive: true });
      if (typeof ResizeObserver !== "undefined") { RO = RO || new ResizeObserver((es) => es.forEach((e) => judge(e.target))); RO.observe(box); }
      judge(box);
    });
  }
  function answerHtml(pm) {   // how the request was answered, and by whom
    const ans = pm.answered; if (!ans) return "";
    const by = ans.by === "page" || ans.by === "person" ? at("perm_by_person", { o: optWords(pm.options.find((o) => o.optionId === ans.option) || { kind: ans.kind, name: ans.option }) })
      : at({ stop: "perm_by_stop", timeout: "perm_by_timeout", agent_gone: "perm_by_gone", desk_restart: "perm_by_restart", turn_end: "perm_by_turn", desk_stop: "perm_by_desk", locked: "perm_by_locked" }[ans.by] || "perm_by_turn", { m: Math.round(((INFO && INFO.approval_timeout) || 600) / 60) });
    return `<p class="ag-ans ${/^allow/.test(ans.kind || "") ? "ok" : "no"}">${esc(by)}</p>`;
  }
  const DOM = new Map();   // an item's key → [its version, its element]: only what changed is drawn again
  function renderThread() {
    const th = $("#agThread"); if (!th) return;
    if (!S || !S.items.length || NEWBOX) {
      DOM.clear();
      th.innerHTML = NEWBOX ? newBoxHtml() : emptyHtml() + (S && S.running ? workingHtml() : "");
      wireThread(th); return;
    }
    const stick = th.scrollHeight - th.scrollTop - th.clientHeight < 40;
    if (th.querySelector(".ag-empty, .ag-new")) th.innerHTML = "";
    const wk = th.querySelector(".ag-working"); if (wk) wk.remove();
    for (const it of S.items) {
      const was = DOM.get(it.key);
      if (was && was[0] === it.v && was[1].isConnected) continue;
      const box = document.createElement("div"); box.className = "ag-item"; box.dataset.k = it.key;
      const open = was ? [...was[1].querySelectorAll("details")].map((x) => x.open) : [];
      box.innerHTML = itemHtml(it);
      [...box.querySelectorAll("details")].forEach((x, i) => { if (open[i]) x.open = true; });
      if (was && was[1].isConnected) was[1].replaceWith(box); else th.appendChild(box);
      DOM.set(it.key, [it.v, box]);
    }
    if (S.running) th.insertAdjacentHTML("beforeend", workingHtml());
    wireThread(th);
    if (stick) th.scrollTop = th.scrollHeight;
    gateAsks(th);
  }
  function workingHtml() {   // the turn is on and nothing new is on screen: say so (DeepSeek Harness sends its reply whole)
    const st = stateNow();
    if (st.k === "ag_waiting") return "";
    const quiet = KIND === "dsh" && S && S.cur !== "msg";
    const last = S && S.items[S.items.length - 1];
    if (!quiet && last && last.kind !== "user") return "";   // the head says what it is doing; the row only fills the silence after your words
    return `<div class="ag-working"><span class="ag-dots" aria-hidden="true"><i></i><i></i><i></i></span><span>${esc(quiet ? at("working_dsh", { a: label() }) : at(st.k, { v: st.v, x: st.x }))}</span></div>`;
  }
  function newBoxHtml() {
    const m = meta(KIND);
    return `<div class="ag-new"><h3>${esc(at("new_h"))} · ${esc(m.label)}</h3>${m.settings_toggle ? `<label class="ag-check" title="${esc(at("personal_tip"))}"><input type="checkbox" id="agPersonal" checked> ${esc(at("personal_on"))}</label>` : ""}<div class="ag-opts"><button type="button" class="btn btn-primary" id="agNewGo">${esc(at("new_go"))}</button><button type="button" class="btn ghost" id="agNewNo">${esc(at("cancel"))}</button></div></div>`;
  }
  function wireThread(th) {
    th.onclick = (e) => {
      const x = e.target.closest("button[data-expand]");
      if (x && e.isTrusted) { const box = x.closest(".ag-perm").querySelector(".ag-askbox"); OPENED.add(x.dataset.expand); SEEN.add(x.dataset.expand); if (box) { box.classList.add("open"); unlock(box); } return; }
      const b = e.target.closest("button[data-rid]");
      if (b && b.dataset.allow && !SEEN.has(b.dataset.rid)) return;   // not before its whole text was on screen
      if (b) { b.disabled = true; answer(e, b.dataset.rid, b.dataset.opt); return; }
      const c = e.target.closest("button[data-copy]");
      if (c) { copyText(c.dataset.copy).then(() => toast(at("copied"))); return; }
      if (e.target.closest("#agNewGo")) { const p = $("#agPersonal"); NEWBOX = false; start(KIND, p ? p.checked : true); return; }
      if (e.target.closest("#agNewNo")) { NEWBOX = false; render(); }
    };
  }
  function renderFoot() {
    const f = $("#agFoot"); if (!f) return;
    const running = !!(S && S.running);
    const sc = typeof SCOPE !== "undefined" && SCOPE ? SCOPE : null;
    const x = sc ? sc.label : typeof scopeLabel === "function" ? scopeLabel() : "";
    const busy = BUSY ? BUSY.map((w) => at("busy_" + (w.why || "console"), { a: label(), x: w.label || "", p: w.pid || "" })).join(" ") : "";
    const anyway = BUSY && BUSY.length && BUSY.every((w) => w.why === "waiting" || w.why === "process");
    const ready = !!(f.dataset.ready);
    if (!ready) {
      f.dataset.ready = "1";
      f.innerHTML = `<button type="button" class="ag-ask" id="agAsk" hidden></button><div class="ag-busy" id="agBusy" hidden></div><div class="crow"><span>${esc(t("at"))}</span><span class="chip" id="agScope"></span><span class="kbd" aria-hidden="true">${esc(at("send_keys"))}</span><button type="button" class="btn ghost" id="agStop" hidden>${esc(at("stop"))}</button><button type="button" class="btn btn-primary" id="agSend">${esc(at("send"))}</button></div>
        <textarea id="agSay" rows="2" maxlength="20000"></textarea>`;
      const ta = $("#agSay");
      ta.value = store_.get(`desk:agent:say:${KEYP}`) || "";
      ta.addEventListener("input", () => store_.set(`desk:agent:say:${KEYP}`, ta.value));
      ta.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey && !e.isComposing && e.keyCode !== 229) { e.preventDefault(); send(e); }
        else if (e.key === "Escape") ta.blur();
      });
      $("#agSend").addEventListener("click", (e) => send(e));
      $("#agStop").addEventListener("click", (e) => stop(e));
      f.addEventListener("click", (e) => {
        if (e.target.closest("#agAnyway")) send(e, true);
        else if (e.target.closest("#agNotNow")) { BUSY = null; renderFoot(); }
        else if (e.target.closest("#agAsk")) { const c = $("#agThread .ag-perm:not(.done)"); if (c) c.scrollIntoView({ block: "center", behavior: reduced() ? "auto" : "smooth" }); }
      });
    }
    $("#agScope").textContent = x; $("#agScope").className = "chip" + (sc ? "" : " quiet");
    $("#agSay").placeholder = sc ? at("ph_say", { x: sc.label }) : at("ph_say0", { a: label() });
    $("#agSay").disabled = !meta(KIND).installed || !KEYOK;
    $("#agStop").hidden = !running; $("#agStop").disabled = !!(S && S.stopping);
    $("#agSend").disabled = !meta(KIND).installed || !KEYOK;
    f.classList.toggle("off", !KEYOK);
    const waitp = S ? Object.values(S.perms).filter((p) => !p.answered) : [];
    const ask = $("#agAsk"); ask.hidden = !waitp.length;
    ask.textContent = waitp.length ? at("ask_bar", { a: label(), x: cut(toolTitle(Object.assign({}, (S.tools[(waitp[0].tool || {}).toolCallId] || {}).d || {}, waitp[0].tool || {})) || verbWords(waitp[0].tool || {}), 48) }) + " ↑" : "";
    const bz = $("#agBusy"); bz.hidden = !busy;
    bz.innerHTML = busy ? `<span>${esc(busy)}</span>${anyway ? `<span class="ag-opts"><button type="button" class="btn" id="agAnyway">${esc(at("busy_anyway"))}</button><button type="button" class="btn ghost" id="agNotNow">${esc(at("busy_not"))}</button></span>` : ""}` : "";
  }
  function render() { renderHead(); renderThread(); renderFoot(); }

  /* ---------- the column's two tabs: this conversation, this round ---------- */
  function tabs() {
    const bar = $("#colTabs"); if (!bar) return;
    const waiting = S ? Object.values(S.perms).filter((p) => !p.answered).length : 0;
    const decs = typeof GV !== "undefined" && GV && GV.current && typeof roundOpen === "function" && roundOpen() ? ((ROUND && ROUND.data && ROUND.data.decisions) || []).length : 0;
    const mine = typeof myItems === "function" && FB ? myItems().length : 0;
    bar.hidden = !KEYP;
    const html = `<button type="button" role="tab" data-tab="chat" aria-selected="${TAB === "chat"}">${esc(at("tab_chat"))}${waiting ? `<span class="badge wait">${esc(at("tab_ask", { n: waiting }))}</span>` : S && S.running ? `<span class="dot agent" title="${esc(at("ag_working"))}"></span>` : ""}</button><button type="button" role="tab" data-tab="round" aria-selected="${TAB === "round"}">${esc(at("tab_round"))}${decs ? `<span class="badge wait">${esc(at("tab_dec", { n: decs }))}</span>` : mine ? `<span class="n mono">${mine}</span>` : ""}</button>`;
    if (bar.dataset.html !== html) { bar.innerHTML = html; bar.dataset.html = html; }
  }
  function setTab(x) {
    TAB = x === "round" ? "round" : "chat";
    store_.set(`desk:coltab:${KEYP}`, TAB);
    $("#col").classList.toggle("chat", TAB === "chat");
    tabs();
    if (TAB === "chat") { render(); }
  }
  $("#colTabs") && $("#colTabs").addEventListener("click", (e) => { const b = e.target.closest("[data-tab]"); if (b) setTab(b.dataset.tab); });

  return {
    async enter(key) {   // a film opened (or drawn again): its conversations, the last one this page had open
      if (key === KEYP && INFO) { tabs(); renderFoot(); renderHead(); return; }
      this.leave();
      KEYP = key;
      const decs = typeof GV !== "undefined" && GV && GV.current && typeof roundOpen === "function" && roundOpen() && ((ROUND && ROUND.data && ROUND.data.decisions) || []).length;
      TAB = store_.get(`desk:coltab:${key}`) || (decs ? "round" : "chat");
      $("#col").classList.toggle("chat", TAB === "chat");
      if (!(await load()) || KEYP !== key) { tabs(); return; }
      const saved = store_.get(`desk:agent:${KEYP}`) || {};
      const m = meta(KIND);
      if (!m.installed) ERR = { code: "not_installed" };
      else { const s = sessionsOf(KIND).find((x) => x.id === saved.sid) || sessionsOf(KIND)[0]; if (s) open(s); }
      render();
    },
    leave() { close(); KEYP = ""; INFO = null; KIND = ""; BUSY = null; ERR = null; NEWBOX = false; DOM.clear(); const b = $("#colTabs"); if (b) b.hidden = true; $("#col").classList.remove("chat"); const f = $("#agFoot"); if (f) f.dataset.ready = ""; const h = $("#agHead"); if (h) h.dataset.ready = ""; },
    scope() { if (KEYP) renderFoot(); },
    keyOk(ok) { KEYOK = !!ok; if (!KEYOK) close(); if (KEYP) render(); },   // without this run's token the conversation is not opened at all (the note at the top says why)
    lang() { if (KEYP) { const f = $("#agFoot"); if (f) f.dataset.ready = ""; const h = $("#agHead"); if (h) h.dataset.ready = ""; const b = $("#colTabs"); if (b) b.dataset.html = ""; DOM.clear(); render(); } },
    tabs, setTab,
    _md: md, _diff: diffLines, _ask: (pm, d) => askHtml(pm, d), _state: () => (S ? { id: S.id, items: S.items.length, seq: S.seq, es: ES ? ES.readyState : null, url: ES ? ES.url.replace(/token=[^&]*/, "token=…") : null } : null),   // for tools/desk/test_agents.py (node): the escaping and the diff, without a page
  };
})();
