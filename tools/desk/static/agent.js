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
    tab_chat: "对话", tab_round: "这一站", tab_ask: "等你批准 {n}", tab_dec: "等你定 {n}", ask_bar: "{a} 在等你批准：{x}", ag_pick: "用哪个 agent", ag_new: "新对话", ag_hist: "历史",
    ag_atstop: "片子等你拍板", n_own: "你交了意见，{a} 自己接着做了。", n_own_plain: "{a} 自己接着做下去了。", n_own_busy: "{a} 自己接着做了，但这支片子正被别的 agent 占着。",
    ag_idle: "空闲", ag_lookonly: "只能看", ag_ready: "可以说了", ag_fresh: "还没开始", ag_thinking: "在想", ag_working: "在做", ag_writing: "在写回复", ag_waiting: "等你批准",
    ag_stopping: "正在停", ag_gone: "已停止", ag_starting: "在启动", ag_doing: "在{v}：{x}",
    set_mode: "模式", set_model: "模型", set_effort: "思考深度", set_more: "更多设置", set_personal_off: "不带个人设置",
    pick_first: "选模型和思考深度", retry_login: "登录后重试",
    eff_tip: "思考越深，想得越久，用掉你订阅的额度也越多；在这里调低就行。", new_with: "开始时请它用：{x}；它没有的话，用它自己的默认。开始以后，上面写着用的是哪个，随时可以换。", new_own: "开始时用 {a} 自己的默认。开始以后，上面写着用的是哪个，随时可以换。", own_default: "{a} 自己的默认", eff_is: "思考深度{e}",
    u_ctx: "对话记忆 {u} / {s}", u_cost: "这个对话约花 {c}", u_rate: "{who}：这 {w}的额度用了 {p}{r}", u_rate_out: "{who}：额度用完了，{at} 恢复",
    w_seven_day: "7 天", u_reset: "，{at} 恢复", w_five_hour: "5 小时", w_daily: "今天的", w_weekly: "这周的",
    ph_say: "对{x}说点什么，发送后马上到它那里…", ph_say0: "跟 {a} 说点什么，发送后马上到它那里…", send: "发送", stop: "停止", send_keys: "↩ 发送 · ⇧↩ 换行",
    you: "你", t_on: "对着 {x}", empty_h: "和 {a} 说话", empty_b: "它在这支片子的文件夹里干活，用的是你在终端里的登录和设置。它每读一个文件、跑一条命令、改一处，下面都会出一张卡；要动手之前问你的，会停下来等你批准。", empty_c: "这里说的话会直接发给它；“这一站”页上记的意见，要点“交给 agent”才一起交出去。可以先问一句，比如：读一下简报，告诉我还缺什么。",
    empty_dsh: "DeepSeek Harness 的回复是整段一起到的：它在做的时候，这里只显示它正在用的工具。",
    not_inst_h: "{a} 还没装到 Studio 里", not_inst_b: "点「装上」，Studio 自己把它装好（会下载约 {s}，不放进片子的文件夹）。它用你自己的登录，不用另外设置；没登录的话，{l}。",
    inst_go: "装上", inst_again: "再试一次", inst_stop: "停下", inst_run: "正在装 {a}（约 {s}），已经 {t}，最多等 {m} 分钟。装好以前可以先做别的。", inst_done: "{a} 装好了",
    inst_no_npm: "这台电脑上还没有 Node（装 {a} 要用它带的 npm）：跟你的 agent 说“帮我装上 Node 22”，装好以后再点一次「装上」。",
    inst_fail: "没装上，多半是网络断了。再点一次试试；还不行，把下面这一行交给你在终端里用的 agent，或者自己在终端里运行，看它说什么。",
    inst_timeout: "装了 {m} 分钟还没装好，停下了，多半是网络太慢。网络好的时候再点一次「装上」。", inst_cancelled: "停下了。想装的时候再点一次「装上」。",
    inst_busy: "另一处（别的 Studio 窗口或终端）正在装 {a}。等它装完，再回来看这一页。",
    login_claude: "在终端里运行 claude，输入 /login", login_codex: "在终端里运行 codex login", login_dsh: "在 DeepSeek Harness 桌面版里登录一次",
    copy: "复制", copied: "复制好了", no_start_h: "{a} 没有启动起来", no_start_b: "常见的原因是还没登录：{l}。它说的是：",
    busy_turn: "{a} 还在做上一句。等它做完，或者点停止。",
    busy_console: "{a} 正在这支片子上干活（另一个对话，或另一个页面）。等它做完，或者去那边停下它。",
    busy_command: "终端里正在跑 {x}。等它跑完再让 agent 动手。",
    busy_process: "终端里有 {x} 开在这支片子的文件夹里，它可能正在改东西。现在让 {a} 动手，两边可能改到同一处。",
    busy_waiting: "终端里有个 agent 在等你交这一站。现在让 {a} 动手，两边可能改到同一处。", busy_anyway: "仍然发这一句", busy_not: "先不发",
    perm_h: "{a} 想{v}", perm_toast: "{a} 想{v}，等你批准", perm_wait: "等你批准", perm_by_person: "你选了：{o}", perm_by_stop: "你点了停止，取消了", perm_by_timeout: "没有页面开着，{m} 分钟后按“不行”处理了",
    perm_by_gone: "agent 停了，这一问不算了", perm_by_restart: "Studio 重启过，这一问不算了", perm_by_turn: "它这一句做完了，这一问不算了", perm_by_desk: "Studio 关了，这一问不算了",
    o_allow_once: "允许这一次", o_allow_always: "这个对话里同类的都允许", o_reject_once: "不允许", o_reject_always: "一直不允许",
    v_read: "读", v_edit: "改", v_delete: "删", v_move: "挪", v_search: "找", v_execute: "跑", v_think: "想", v_fetch: "上网取", v_switch_mode: "换模式", v_other: "用",
    v_read_w: "读文件", v_edit_w: "改文件", v_delete_w: "删文件", v_move_w: "挪文件", v_search_w: "找文件", v_execute_w: "跑命令", v_fetch_w: "上网取东西", v_other_w: "用工具",
    st_pending: "准备中", st_in_progress: "在跑", st_asking: "等你批准", st_completed: "好了", st_failed: "没做成", st_refused: "你没允许，所以没做", out_show: "看输出", out_lines: "{n} 行",
    new_file: "新文件", own_opts: "它给的选项原文：", seen_note: "这一段比框长：滚到底，或者点“全部展开”看完，才能点允许。“不行”随时能点。", seen_all: "全部展开",
    f_title: "它给这一步的标题", f_command: "要跑的命令", f_description: "它自己的说明（是它说的，不一定准）", f_sandbox_on: "不用沙箱跑：这条命令不受沙箱限制",
    f_sandbox_off: "照常在沙箱里跑", f_bg: "在后台跑：它这一句做完了，命令可能还在跑", f_timeout: "最长跑多久（毫秒）", f_file: "文件", f_content: "要写进去的内容",
    f_old: "改之前", f_new: "改之后", f_all: "文件里每一处都换", f_cwd: "在哪个文件夹里跑", f_url: "要打开的网址", f_pattern: "要找的", f_where: "涉及的位置",
    f_said: "它附的话", f_other: "它请求里的内容", f_in_diff: "（就是下面改动里的那一段，一字不差）",
    too_long: "这条请求太长，这里显示不全，所以只能拒绝。", set_open: "设置", set_close: "收起", diff_cut: "太长了，只显示前面一段", thought: "它的想法", raw_said: "它的原话", plan_h: "它的计划",
    turn_cancelled: "停下了", turn_halted: "它停在这里了", turn_signed_out: "没登录，这一句没做", turn_error: "出错了：{e}", turn_took: "用了 {s}", turn_gone: "agent 中途停了",
    turn_restart: "Studio 重启过，这一句没说完", n_fresh: "接着上次的话说：这个 agent 记不得前面说过什么，从这里重新开始。",
    n_placed: "建好了这支片子：{x}。这段对话跟着它，接下来都在它里面。", n_place_busy: "建好了 {x}，但它正被{w}占着，这段对话先留在空间里。",
    sp_own: "在开的新片子", sp_wait: "等你", sp_doing: "在做", stray: "从空间开的对话「{x}」可能就是做这支片子的，它还没跟过来。", stray_go: "把它带到这里", stray_fail: "没带过来：这支片子不像是那段对话建的",
    sp_h: "想做一支什么样的片子？", sp_b: "写一句发给 {a}：它照这个工作台的做法定类型、建好片子、先想立意。片子一建好，窗口就转过去，这段对话跟着过去。", sp_c: "它要停下来问你的，问题会出现在这里；它停在哪一站，那一站等你定的事也会摆出来。",
    sp_ph: "比如：做一支一分钟的科普，讲海水为什么一天涨两次", sp_copy: "复制给别处的 agent", sp_copied: "复制好了，贴给你的 agent", sp_empty: "先写一句",
    of_keep: "你选的「{x}」那一句先留着：装上以后，在下面点一下就写进框里。", of_ready: "你选的「{x}」那一句：", of_go: "写进框里", of_no: "不用了",
    of_busy: "空间里这段对话还在做，或在等你批准；它停下以后，再把「{x}」那一句写进新片子的框里。", of_moved: "开了新片子的框，之前那段对话在「历史」里",
    n_gone: "agent 的进程停了。再说一句会重新启动它。", n_signed_out: "{a} 还没登录，或者登录过期了：{l}，再回来说一句就行。", n_unsupported: "agent 问了一件这一页还答不了的事，回了“不支持”。", n_restarted: "{a} 收到停止以后没有停下来：这一句在这里结束了，它也重新启动了（再说一句会接着这个对话）。",
    unknown: "{a} 发来一条这里还显示不了的更新（点开看原样）", working_dsh: "{a} 在做，回复会整段一起到", sec: "{n} 秒", min: "{m} 分 {s} 秒",
    m_default: "改动前都问", m_acceptEdits: "改文件不问", m_plan: "只出计划", m_auto: "危险的才问", m_bypassPermissions: "什么都不问",
    "m_read-only": "只读", "m_workspace-write": "只改它所在文件夹里的", m_agent: "危险的才问", "m_agent-full-access": "不设限",
    e_off: "关", mdl_default: "默认", e_low: "低", e_medium: "中", e_high: "高", e_xhigh: "很高", e_max: "最高", e_ultra: "最高并分派", e_default: "默认",
    personal_on: "带上我的个人设置（放行规则、skills、插件）", personal_tip: "关掉：只带这个文件夹自己的设置，你的 skills、插件和放行规则都不带；模式还是 Claude Code 自己的默认，可以在上面改",
    new_h: "开一个新对话", new_go: "开始", cancel: "先不", reconnect: "连接断了，正在重连…", reload: "和 Studio 断开了",
    err_send: "没发出去：{e}", sent_fail: "没发出去",
  },
  en: {
    tab_chat: "Chat", tab_round: "This stop", tab_ask: "{n} for your OK", tab_dec: "{n} to decide", ask_bar: "{a} is waiting for your OK: {x}", ag_pick: "Which agent", ag_new: "New chat", ag_hist: "History",
    ag_atstop: "Your call", n_own: "You sent your notes; {a} carried on by itself.", n_own_plain: "{a} carried on by itself.", n_own_busy: "{a} carried on by itself, but another agent holds this film.",
    ag_idle: "Idle", ag_lookonly: "Look only", ag_ready: "Ready", ag_fresh: "Not started", ag_thinking: "Thinking", ag_working: "Working", ag_writing: "Writing", ag_waiting: "Needs OK",
    ag_stopping: "Stopping", ag_gone: "Stopped", ag_starting: "Starting", ag_doing: "{v}: {x}",
    set_mode: "Mode", set_model: "Model", set_effort: "Effort", set_more: "More settings", set_personal_off: "Without personal settings",
    pick_first: "Choose model and effort", retry_login: "Retry after sign-in",
    eff_tip: "A higher effort thinks longer and uses more of your plan; lower it here.", new_with: "Starts by asking it for: {x}; if it doesn't offer that, its own default. Once started, the menus above show what is in use, and you can change it any time.", new_own: "Starts with {a}'s own default. Once started, the menus above show what is in use, and you can change it any time.", own_default: "{a}'s own default", eff_is: "{e} effort",
    u_ctx: "Chat memory {u} / {s}", u_cost: "this chat: about {c}", u_rate: "{who}: {p} of the {w} limit used{r}", u_rate_out: "{who}: limit reached, back at {at}",
    w_seven_day: "7-day", u_reset: "; it resets {at}", w_five_hour: "5-hour", w_daily: "daily", w_weekly: "weekly",
    ph_say: "Say something about {x}; it goes as soon as you send…", ph_say0: "Say something to {a}; it goes as soon as you send…", send: "Send", stop: "Stop", send_keys: "↩ send · ⇧↩ new line",
    you: "You", t_on: "on {x}", empty_h: "Talk to {a}", empty_b: "It works in this film's folder with your own login and settings from the terminal. Every file it reads, command it runs and change it makes shows up below as a card; when it asks before doing something, it waits for your click.", empty_c: "What you say here goes to it at once; the notes on “This stop” go only when you press “Send to agent”. Try: read the brief and tell me what is missing.",
    empty_dsh: "DeepSeek Harness sends its reply in one piece: while it works, only the tool it is using shows here.",
    not_inst_h: "{a} isn't set up in Studio yet", not_inst_b: "Press “Set it up” and Studio installs it (it downloads about {s}, kept out of the film's folder). It uses your own login, nothing else to set up; if it isn't signed in, {l}.",
    inst_go: "Set it up", inst_again: "Try again", inst_stop: "Stop", inst_run: "Setting up {a} (about {s}): {t} so far, {m} minutes at most. You can do other things meanwhile.", inst_done: "{a} is set up",
    inst_no_npm: "This computer has no Node yet ({a} installs with the npm that comes with it): tell your agent “install Node 22 for me”, then press “Set it up” again.",
    inst_fail: "It didn't install; most often the network dropped. Try again; if it still fails, give the line below to the agent you use in a terminal, or run it in a terminal yourself to see what it says.",
    inst_timeout: "After {m} minutes it still wasn't set up, so it was stopped; most likely the network is too slow. Press “Set it up” again when it's better.", inst_cancelled: "Stopped. Press “Set it up” again when you want it.",
    inst_busy: "{a} is being set up somewhere else (another Studio window or a terminal). Wait for that, then come back to this page.",
    login_claude: "run claude in a terminal and type /login", login_codex: "run codex login in a terminal", login_dsh: "sign in once in the DeepSeek Harness desktop app",
    copy: "Copy", copied: "Copied", no_start_h: "{a} did not start", no_start_b: "Usually it isn't signed in yet: {l}. What it said:",
    busy_turn: "{a} is still on your last message. Wait for it, or press Stop.",
    busy_console: "{a} is working on this film (in another chat or page). Wait for it, or stop it there.",
    busy_command: "{x} is running in a terminal. Let it finish before the agent starts.",
    busy_process: "{x} is open in this film's folder in a terminal and may be editing. If {a} starts now, both may edit the same thing.",
    busy_waiting: "An agent in a terminal is waiting for you to send this stop. If {a} starts now, both may edit the same thing.", busy_anyway: "Send this one anyway", busy_not: "Not now",
    perm_h: "{a} wants to {v}", perm_toast: "{a} wants to {v}: waiting for your OK", perm_wait: "Waiting for your OK", perm_by_person: "You chose: {o}", perm_by_stop: "Cancelled when you pressed Stop", perm_by_timeout: "No page was open; after {m} minutes it was refused",
    perm_by_gone: "The agent stopped, so this request no longer counts", perm_by_restart: "Studio restarted, so this request no longer counts", perm_by_turn: "Its reply ended, so this request no longer counts", perm_by_desk: "Studio closed, so this request no longer counts",
    o_allow_once: "Allow this once", o_allow_always: "Allow the same kind in this chat", o_reject_once: "Don't allow", o_reject_always: "Never allow",
    v_read: "read", v_edit: "edit", v_delete: "delete", v_move: "move", v_search: "search", v_execute: "run", v_think: "think", v_fetch: "fetch", v_switch_mode: "switch mode", v_other: "use",
    v_read_w: "read a file", v_edit_w: "edit a file", v_delete_w: "delete a file", v_move_w: "move a file", v_search_w: "search", v_execute_w: "run a command", v_fetch_w: "fetch from the web", v_other_w: "use a tool",
    st_pending: "getting ready", st_in_progress: "running", st_asking: "waiting for your OK", st_completed: "done", st_failed: "failed", st_refused: "You didn't allow it, so it wasn't done", out_show: "Output", out_lines: "{n} lines",
    new_file: "new file", own_opts: "Its options as it wrote them: ", seen_note: "This is longer than the box: scroll to the end, or press “Show it all”, before you can allow it. “No” works any time.", seen_all: "Show it all",
    f_title: "Its title for this step", f_command: "The command", f_description: "Its own description (its words, maybe not accurate)", f_sandbox_on: "Without the sandbox: nothing limits this command",
    f_sandbox_off: "In the sandbox, as usual", f_bg: "In the background: it may still run after this reply", f_timeout: "How long it may run (ms)", f_file: "File", f_content: "What it writes",
    f_old: "Before", f_new: "After", f_all: "Every match in the file", f_cwd: "The folder it runs in", f_url: "The address it opens", f_pattern: "What it looks for", f_where: "Places it touches",
    f_said: "What it added", f_other: "What it asks", f_in_diff: "(the very text of the change below)",
    too_long: "This request is too long to show whole here, so it can only be refused.", set_open: "Settings", set_close: "Hide", diff_cut: "Too long: only the start is shown", thought: "Its thinking", raw_said: "What it said", plan_h: "Its plan",
    turn_cancelled: "Stopped", turn_halted: "It stopped here", turn_signed_out: "Not signed in: this one wasn't done", turn_error: "Something went wrong: {e}", turn_took: "took {s}", turn_gone: "The agent stopped midway",
    turn_restart: "Studio restarted before this finished", n_fresh: "Picking up an earlier chat: this agent can't recall what was said, so it starts over from here.",
    n_placed: "Made the film {x}. This chat goes with it from here.", n_place_busy: "Made {x}, but {w} is working on it, so this chat stays on the space for now.",
    sp_own: "New films under way", sp_wait: "waiting for you", sp_doing: "working", stray: "The chat begun on the space, “{x}”, may be the one that made this film; it hasn't followed it here.", stray_go: "Bring it here", stray_fail: "Not brought: this film doesn't look like that chat's",
    sp_h: "What film do you want to make?", sp_b: "Write a sentence to {a}: it works the way this workbench does, picks the kind of film, makes it and starts on the idea. Once the film is made, the window goes there and this chat goes with it.", sp_c: "When it stops to ask you something, the questions show here; when it stops at a step, what that step needs from you is laid out too.",
    sp_ph: "e.g. a one-minute explainer on why the tide comes in twice a day", sp_copy: "Copy for an agent elsewhere", sp_copied: "Copied: paste it to your agent", sp_empty: "Write a sentence first",
    of_keep: "The “{x}” sentence you picked is kept: once it is set up, one click below puts it in the box.", of_ready: "The “{x}” sentence you picked:", of_go: "Put it in the box", of_no: "Not now",
    of_busy: "The space's chat is still working, or waiting for your approval; once it stops, put the “{x}” sentence in a new film's box.", of_moved: "A new film's box is open; the earlier chat is in History",
    n_gone: "The agent's process stopped. Say something and it starts again.", n_signed_out: "{a} isn't signed in, or its login expired: {l}, then say something again.", n_unsupported: "The agent asked for something this page can't do yet; it was told no.", n_restarted: "{a} did not stop when asked: the turn was ended here and the agent restarted (say something to carry on in this chat).",
    unknown: "{a} sent an update this page can't show yet (open it to see it as sent)", working_dsh: "{a} is working; its reply comes in one piece", sec: "{n} s", min: "{m} min {s} s",
    m_default: "Ask before changes", m_acceptEdits: "Edit without asking", m_plan: "Plan only", m_auto: "Ask only if risky", m_bypassPermissions: "Never ask",
    "m_read-only": "Read only", "m_workspace-write": "Edit its own folder only", m_agent: "Ask only if risky", "m_agent-full-access": "No limits",
    e_off: "Off", mdl_default: "Default", e_low: "Low", e_medium: "Medium", e_high: "High", e_xhigh: "Very high", e_max: "Max", e_ultra: "Max, delegating", e_default: "Default",
    personal_on: "Bring my personal settings (allow rules, skills, plugins)", personal_tip: "Off: only this folder's own settings, none of your skills, plugins or allow rules; the mode is still Claude Code's own default, which you can change above",
    new_h: "Start a new chat", new_go: "Start", cancel: "Cancel", reconnect: "Connection lost, reconnecting…", reload: "Lost touch with Studio",
    err_send: "Not sent: {e}", sent_fail: "Not sent",
  },
};
const at = (k, vars) => { const s = (ASTR[LANG] || ASTR.zh)[k]; return s == null ? t(k, vars) : String(s).replace(/\{(\w+)\}/g, (_, v) => (vars && vars[v] != null ? vars[v] : "")); };

const SPACE = "~space";   // the space's column: a film begun with a sentence, before it has a folder (its own addresses, /api/space/…)
const AGENT = (() => {
  let TOKEN_ = deskToken();
  let KEYOK = true;   // the page holds this run's token (studio.js asks /api/hello); without it the box is not offered
  let KEYP = "", INFO = null, KIND = "", S = null, ES = null, BUSY = null, TAB = "", ERR = null, NEWBOX = false, tick = null, raf = 0;
  let NEWASK = {};   // the model and effort the person chose for the conversation they are about to start (only what they changed)
  let LISTEN = false;   // this film's stop has an agent waiting for the person's submission (bin/vh desk wait, gate --wait: studio.js's poll)
  const kinds = () => ((INFO && INFO.agents) || []);
  const meta = (k) => kinds().find((a) => a.kind === k) || { kind: k, label: k };
  const label = () => meta(KIND).label || KIND;
  const base = () => (KEYP === SPACE ? "/api/space" : `/api/p/${enc(KEYP)}`);
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
      if (e.state === "start") { S.running = true; S.stopping = false; S.turnAt = e.t; S.cur = null; if (e.own) item("o" + e.seq, () => ({ kind: "notice", code: e.locked === false ? "own_busy" : e.notes ? "own" : "own_plain" })); }
      else { const stopped = S.stopping || S.stopAsked; S.running = false; S.stopping = false; S.stopAsked = false; item("e" + e.seq, () => ({ kind: "end", stop: stopped && !e.error ? "cancelled" : e.stop, asked: stopped, error: e.error, took: S.turnAt ? e.t - S.turnAt : null })); S.turnAt = null; }
      if (KEYP !== SPACE && typeof renderFlow === "function") setTimeout(renderFlow, 0);   // the stops' lamps: the agent's while its turn runs
    } else if (ty === "state") { Object.assign(S.config, e); }
    else if (ty === "permission") { const it = item("p" + e.rid, () => ({ kind: "perm", rid: e.rid, tool: e.tool || {}, options: e.options || [], answered: null, clipped: !!e.clipped })); S.perms[e.rid] = it; const tl = e.tool && S.tools[e.tool.toolCallId]; if (tl) tl.v++; }
    else if (ty === "answered") { const it = S.perms[e.rid]; if (it) { it.answered = e; it.v++; const tl = it.tool && S.tools[it.tool.toolCallId]; if (tl) tl.v++; } }
    else if (ty === "notice") {
      if (e.code === "agent_gone") S.gone = true;
      if (e.code === "stopping") { S.stopping = true; S.stopAsked = true; return; }
      item("n" + e.seq, () => ({ kind: "notice", code: e.code, method: e.method, name: e.name, who: e.who }));
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
    else if (/^async_task_/.test(k || "")) { /* its background work's lifecycle: the server turns its own turn into a turn; the commands are their tool calls */ }
    else item("x" + e.seq, () => ({ kind: "unknown", k: String(k || "?"), u }));
  }

  /* ---------- talking to the server ---------- */
  async function post(path, body) {
    try {
      const r = await fetch(`${base()}/agent/${path}`, { method: "POST", headers: { "Content-Type": "application/json", "X-Desk-Token": TOKEN_ }, body: JSON.stringify(Object.assign({ pid: INFO && INFO.pid }, body || {})) });
      const j = await r.json().catch(() => null);
      return { ok: r.ok, status: r.status, data: j };
    } catch (e) { return { ok: false, status: 0, data: null }; }
  }
  async function load() {
    const sid = KEYP === SPACE ? (store_.get(`desk:agent:${SPACE}`) || {}).sid : "";
    const r = await getJSON(`${base()}/agents${sid ? `?sid=${enc(sid)}` : ""}`);
    if (!r.ok || !r.data) return false;
    INFO = r.data;
    if (KEYP === SPACE && INFO.went && !(S && S.id === INFO.went.id)) {   // reloaded while it made its film (its own stream says so when open): go there
      store_.set(`desk:agent:${INFO.went.key}`, { kind: KIND, sid: INFO.went.id }); store_.set(`desk:coltab:${INFO.went.key}`, "chat"); store_.set(`desk:agent:${SPACE}`, { kind: KIND });
      if (typeof spacePlaced === "function") spacePlaced(INFO.went.key);
    }
    const saved = store_.get(`desk:agent:${KEYP}`) || {};
    KIND = KIND || saved.kind || defaultKind();   // this place's last agent decides which conversation shows; a new one starts with the default
    return true;
  }
  let INSTWATCH = 0;
  async function installKind(cancel) {   // the person's click: the console installs this kind's adapter (or stops it), and the column follows it
    const kind = KIND, r = await post("install", cancel ? { kind, cancel: true } : { kind });
    if (r.ok && r.data && r.data.installing) meta(kind).installing = r.data.installing;
    else toast(at("err_send", { e: (r.data && r.data.error) || r.status }));
    render(); followInstall();
  }
  function followInstall() {
    clearTimeout(INSTWATCH);
    if (!kinds().some((a) => a.installing && a.installing.state === "running")) return;
    INSTWATCH = setTimeout(async () => {
      const before = kinds().filter((a) => a.installed).map((a) => a.kind);
      if (await load()) {
        kinds().filter((a) => a.installed && !before.includes(a.kind)).forEach((a) => toast(at("inst_done", { a: a.label })));
        if (meta(KIND).installed && ERR && ERR.code === "not_installed") ERR = null;
      }
      render(); followInstall();
    }, 1500);
  }
  function sessionsOf(kind) { return ((INFO && INFO.sessions) || []).filter((s) => s.kind === kind); }
  function histOf() { return KEYP === SPACE ? ((INFO && INFO.sessions) || []) : sessionsOf(KIND); }   // the space: every new film's conversation, whichever agent
  function back(sid) {   // one click back to a conversation of the list (another agent's too)
    const s = histOf().find((x) => x.id === sid); if (!s) return;
    if (s.kind !== KIND) { KIND = s.kind; NEWASK = {}; }
    NEWBOX = false; ERR = null; open(s); render();
  }
  function ownHtml() {   // the space's conversations that work or wait for you, under the sentence: one click back to each
    const L2 = ((INFO && INFO.sessions) || []).filter((x) => (x.running || x.pending) && (!S || x.id !== S.id));
    if (!L2.length) return "";
    return `<section class="ag-own"><h3 class="blk-h"><b>${esc(at("sp_own"))}</b><span class="n mono">${L2.length}</span></h3><ul class="ag-own-l">${L2.map((x) => `<li><button type="button" data-own="${esc(x.id)}"><b>${esc(cut(x.title || x.first || "—", 40))}</b><span class="q">${esc(x.label || "")} · ${esc(at(x.pending ? "sp_wait" : "sp_doing"))}</span></button></li>`).join("")}</ul></section>`;
  }
  function open(sum) {
    close();
    if (!KEYOK) return;   // a page without this run's token opens no conversation
    S = blank(sum); ERR = null; BUSY = null;
    store_.set(`desk:agent:${KEYP}`, { kind: KIND, sid: sum.id });
    if (sum.config) Object.assign(S.config, sum.config);
    const url = `${base()}/agent/${sum.id}/events?token=${enc(TOKEN_)}&after=0`;
    ES = new EventSource(url);
    ES.addEventListener("hello", (m) => { try { const h = JSON.parse(m.data); S.live = h.live; S.caps = h.caps || {}; if (h.config) Object.assign(S.config, h.config); S.gone = false; schedule(); } catch (e) { /* a bad line */ } });
    ES.onmessage = (m) => { let e; try { e = JSON.parse(m.data); } catch (x) { return; } const was = Object.keys(S.perms).filter((r) => !S.perms[r].answered).length; apply(e); schedule();
      if (e.type === "notice" && e.code === "placed" && KEYP === SPACE && e.key) placed(e); if (e.type === "permission" && TAB !== "chat" && !was) toast(at("perm_toast", { a: label(), v: verbWords(e.tool) })); };
    ES.onerror = () => { if (S) { S.offline = ES && ES.readyState === 2 ? "closed" : true; schedule(); } if (ES && ES.readyState === 2 && typeof checkKey === "function") checkKey(); };   // closed: the desk restarted (a new token) or the conversation is gone
    ES.onopen = () => { if (S) { S.offline = false; schedule(); } };
    clearInterval(tick); tick = setInterval(() => { if (S && S.running) renderHead(); }, 1000);
  }
  function close() { if (ES) { ES.close(); ES = null; } clearInterval(tick); S = null; }
  function placed(e) {   // the conversation begun on the space made its film: that film opens on this very conversation
    store_.set(`desk:agent:${e.key}`, { kind: KIND, sid: S.id });
    store_.set(`desk:coltab:${e.key}`, "chat");
    store_.set(`desk:agent:${SPACE}`, { kind: KIND });
    if (typeof spacePlaced === "function") spacePlaced(e.key, e.name);
  }
  async function start(kind, personal) {   // a new conversation: the agent starts (its settings show before the first word)
    if (ERR && ERR.code === "starting") return;
    const starting = { code: "starting" }, body = Object.assign({ kind, personal: personal !== false }, NEWASK);
    NEWASK = {};
    close(); KIND = kind; BUSY = null; ERR = starting; render();
    const r = await post("new", body);
    if (ERR !== starting) return;   // the person switched chats or films while the adapter was starting
    if (r.data && r.data.id) {
      INFO.sessions = [r.data].concat((INFO.sessions || []).filter((x) => x.id !== r.data.id));
      if (r.ok) { open(r.data); ERR = null; } else { ERR = { code: r.data.error, detail: r.data.detail }; S = null; }
    } else ERR = { code: (r.data && r.data.error) || "no_start", detail: r.data && (r.data.detail || r.data.error) };
    render();
    return S;
  }
  function defaultKind(info) {   // a new conversation's agent: the settings page's 新对话默认用 when it is set up, else the first set up
    const ks = ((info || INFO || {}).agents) || [], d = (info || INFO || {}).default;
    return (ks.find((a) => a.installed && a.kind === d) || ks.find((a) => a.installed) || ks[0] || {}).kind || "claude";
  }
  async function pickKind(kind) {
    KIND = kind; NEWBOX = false; ERR = null; NEWASK = {}; close();
    store_.set(`desk:agent:${KEYP}`, { kind });
    const m = meta(kind);
    if (!m.installed) { ERR = { code: "not_installed" }; render(); return; }
    const last = sessionsOf(kind)[0];
    if (last) open(last); else S = null;
    render();
  }

  /* ---------- what the person does ---------- */
  let OFFER = null;   // the sample the person picked on the space's wall while the box could not take it (no agent set up, the
  // space's chat working or waiting for approval): kept here and offered again with one click, never put in the box by itself
  const busyNow = () => !!(S && (S.running || Object.values(S.perms).some((p) => !p.answered)));
  const offerName = () => (OFFER ? t(`smp_${OFFER}_type`) : "");
  function offerKept() { return OFFER && KEYP === SPACE ? `<p class="ag-offer-keep">${esc(at("of_keep", { x: offerName() }))}</p>` : ""; }
  let TELLING = "";   // the carry-on words a refused click was for: the busy line's "anyway" sends them, never the box's draft
  async function sayWords(text, despite) {
    const r = await post(`${S.id}/say`, { text, despite: !!despite });
    if (r.ok) { BUSY = null; TELLING = ""; S.sum.turns = (S.sum.turns || 0) + 1; }
    else if (r.status === 409 && r.data && r.data.who) { BUSY = r.data.who; TELLING = text; }
    else toast(at("sent_fail"));
    render();
  }
  async function again(e) {   // "send it anyway" on the busy line: what was refused, the carry-on words or the box
    if (!e || !e.isTrusted) return;
    if (TELLING && S) return sayWords(TELLING, true);
    return send(e, true);
  }
  async function send(e, despite) {
    if (!e || !e.isTrusted) return;   // only a real key press or click sends, and only what is in the box
    const ta = $("#agSay"), text = ta ? ta.value.trim() : "";
    if (!text) { if (ta) ta.focus(); return; }
    if (!S && !(await start(KIND, true))) return;
    const sc = typeof SCOPE !== "undefined" && SCOPE && SCOPE.target ? SCOPE : null;
    const scope = sc ? { kind: sc.target.split(":")[0], id: sc.target.split(":").slice(1).join(":"), t: sc.t, t1: sc.t1, module: typeof MOD !== "undefined" ? MOD : "", label: sc.label } : null;
    const btn = $("#agSend"); if (btn) btn.disabled = true;
    const r = await post(`${S.id}/say`, { text, scope, despite: !!despite });
    if (btn) btn.disabled = false;
    if (r.ok) { ta.value = ""; store_.set(`desk:agent:say:${KEYP}`, ""); BUSY = null; TELLING = ""; S.sum.turns = (S.sum.turns || 0) + 1; }
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
    if (LISTEN && KEYP !== SPACE) return { k: "ag_atstop", cls: "wait" };   // its turn ended, its wait goes on in the background
    return { k: S.items.length ? "ag_idle" : "ag_ready", cls: "" };
  }
  function optWord(cat, x) {   // a value of the agent's settings in our words when we know it, else its own name
    const w = cat === "mode" ? at("m_" + x.value) : cat === "thought_level" ? at("e_" + x.value) : cat === "model" && x.value === "default" ? at("mdl_default") : "";
    return w && !/^(m|e|mdl)_/.test(w) ? w : x.name || x.value;
  }
  function selectOf(o, cat) {   // one of the agent's settings as a menu, in its own words (the known ones in ours)
    const flat = []; (o.options || []).forEach((x) => (Array.isArray(x.options) ? x.options.map((y) => Object.assign({ group: x.name }, y)) : [x]).forEach((y) => flat.push(y)));
    const name = (x) => { const w = optWord(cat, x); return w !== (x.name || x.value) ? w : (x.group && flat.filter((y) => y.name === x.name).length > 1 ? `${x.name} · ${x.group}` : x.name || x.value); };
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
    const more = opts.filter((o) => o.type === "select" && !["mode", "model", "thought_level"].includes(o.category) && (o.options || []).length > 1);
    if (!parts.length && !more.length && S.personal) return "";
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
    // the model and the effort are plain menus (the choice a person makes most); the mode and the rest fold behind one button
    const model = byCat("model"), eff = byCat("thought_level");
    const picks = (model ? `<label class="ag-pick"><span>${esc(at("set_model"))}</span>${selectOf(model, "model")}</label>` : "")
      + (eff ? `<label class="ag-pick" title="${esc(at("eff_tip"))}"><span>${esc(at("set_effort"))}</span>${selectOf(eff, "thought_level")}</label>` : "");
    const sum = mode || (model || eff ? "" : [nameOf(model, "model"), nameOf(eff, "thought_level")].filter(Boolean).join(" · "));
    const use = [S.usage && S.usage.used != null && S.usage.size ? at("u_ctx", { u: kilo(S.usage.used), s: kilo(S.usage.size) }) : "", S.cost ? at("u_cost", { c: money(S.cost) }) : ""].filter(Boolean).join(" · ");
    const extra = settingsHtml();   // the mode and the rest: a button only when there is something behind it
    return `<div class="ag-line">${picks}${extra || !picks ? `<button type="button" class="ag-sum" id="agSum" aria-expanded="${SETOPEN}" title="${esc(at(SETOPEN ? "set_close" : "set_open"))}"><span>${esc(sum || at("set_more"))}</span><i aria-hidden="true">${SETOPEN ? "▴" : "▾"}</i></button>` : ""}${use ? `<span class="ag-usetxt mono" title="${esc([S.usage && S.usage.used != null ? at("u_ctx", { u: kilo(S.usage.used), s: kilo(S.usage.size || 0) }) : "", S.cost ? at("u_cost", { c: money(S.cost) }) : ""].filter(Boolean).join(" · "))}">${esc(use)}</span>` : ""}</div>${SETOPEN ? extra : ""}`;
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
    const el = S && S.running && S.turnAt && st.k !== "ag_waiting" ? secs(Date.now() / 1000 - S.turnAt) : "";   // waiting for the person: the word alone, never cut
    const list = histOf().filter((x) => !S || x.id !== S.id);
    const mark = (x) => (x.pending ? `<span class="chip wait">${esc(at("sp_wait"))}</span>` : x.running ? `<span class="chip agent">${esc(at("sp_doing"))}</span>` : "");
    const waits = list.filter((x) => x.pending).length;
    const pick = `<select id="agKind" aria-label="${esc(at("ag_pick"))}">${kinds().map((a) => `<option value="${esc(a.kind)}"${a.kind === KIND ? " selected" : ""}>${esc(a.label)}${a.installed ? "" : LANG === "zh" ? "（没装）" : " (not set up)"}</option>`).join("")}</select>`;
    const top = `<span class="ag-orb" id="agOrb" aria-hidden="true"></span>${pick}<span class="ag-state" id="agState" role="status"></span>
        <span class="ag-acts"><button type="button" class="xs" id="agNew">${esc(at("ag_new"))}</button>${list.length ? `<details class="ag-hist"><summary class="xs">${esc(at("ag_hist"))}${waits ? ` <span class="chip wait">${esc(at("sp_wait"))} ${waits}</span>` : ""}</summary><ul>${list.map((x) => `<li><button type="button" data-sid="${esc(x.id)}"><b>${esc(cut(x.title || x.first || "—", 34))}${mark(x)}</b><span class="mono">${esc(new Date((x.last || x.created || 0) * 1000).toLocaleString(LANG === "zh" ? "zh-CN" : "en", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" }))}</span></button></li>`).join("")}</ul></details>` : ""}</span>`;
    if (part("agTop", top)) {
      DRAWN.agState = null;
      $("#agKind").addEventListener("change", (e) => pickKind(e.target.value));
      $("#agNew").addEventListener("click", async () => { if (KEYP === SPACE) return fresh(); NEWBOX = true; NEWASK = {}; await load(); KIND = defaultKind(); render(); const b = $("#agNewGo"); if (b) b.focus(); });   // (load: the agent's list as this run last saw it)
      $$("#agTop [data-sid]").forEach((b) => b.addEventListener("click", () => back(b.dataset.sid)));
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
    if (ERR && ERR.code === "not_installed" || !m.installed) {   // the person's click installs it (the console runs bin/vh desk agents install)
      const cmd = m.install || `bin/vh desk agents install ${KIND}`, j = m.installing || null, about = String(m.size || "").replace(/^≈\s*/, ""), h = `<h3>${esc(at("not_inst_h", { a: m.label }))}</h3>`;
      if (j && j.state === "running") {
        const s = Math.max(0, Math.round(Date.now() / 1000 - j.since)), took = s < 60 ? at("sec", { n: s }) : at("min", { m: Math.floor(s / 60), s: s % 60 });
        return `<div class="ag-empty">${offerKept()}${h}<div class="ag-working ag-inst" role="status"><span class="ag-dots" aria-hidden="true"><i></i><i></i><i></i></span><span>${esc(at("inst_run", { a: m.label, s: about, t: took, m: Math.round((j.limit || 1800) / 60) }))}</span></div>${KEYOK ? `<div class="ag-opts"><button type="button" class="btn ghost" id="agInstallStop">${esc(at("inst_stop"))}</button></div>` : ""}</div>`;
      }
      const SAY = { failed: "inst_fail", no_npm: "inst_no_npm", timeout: "inst_timeout", cancelled: "inst_cancelled", busy: "inst_busy" };   // a sentence each, never what it printed
      const failed = !!(j && SAY[j.state]);
      const fall = j && j.state === "failed" ? `<div class="ag-cmd"><code class="mono">${esc(cmd)}</code><button type="button" class="btn" data-copy="${esc(cmd)}">${esc(at("copy"))}</button></div>` : "";
      return `<div class="ag-empty">${h}<p${failed ? ' class="ag-bad"' : ""}>${failed ? esc(at(SAY[j.state], { a: m.label, m: Math.round((j.limit || 1800) / 60) })) : at("not_inst_b", { s: esc(about), l })}</p>${fall}${KEYOK ? `<div class="ag-opts"><button type="button" class="btn btn-primary" id="agInstall">${esc(at(failed && j.state !== "cancelled" ? "inst_again" : "inst_go"))}</button></div>` : ""}${offerKept()}</div>`;
    }
    if (!KEYOK) return "";   // the note above the column says it once, with what to do
    const signedOut = KIND === "codex" && (ERR ? ERR.code === "signed_out" : !S && m.signed_in === false);
    const prepare = KIND === "codex" && !S && (!ERR || ERR.code === "signed_out")
      ? `<button type="button" class="btn ghost xs" id="agPickFirst">${esc(at(signedOut ? "retry_login" : "pick_first"))}</button>` : "";
    if (signedOut) {
      return `<div class="ag-empty"><p class="ag-note warn">${esc(at("n_signed_out", { a: m.label, l: at("login_codex") }))}</p>${prepare}</div>`;
    }
    if (ERR && ERR.code && ERR.code !== "starting") return `<div class="ag-empty bad"><h3>${esc(at("no_start_h", { a: m.label }))}</h3><p>${at("no_start_b", { l })}</p><pre>${esc(cut(ERR.detail || ERR.code, 600))}</pre></div>`;
    if (KEYP === SPACE) return `<div class="ag-empty ag-space"><h3>${esc(at("sp_h"))}</h3>${S ? "" : startPicks()}<p>${esc(at("sp_b", { a: m.label }))}</p><p class="ag-mute">${esc(at("sp_c"))}</p><div class="ag-opts">${prepare}<button type="button" class="btn ghost xs" id="agCopyAsk">${esc(at("sp_copy"))}</button></div></div>${ownHtml()}<section id="spaceRun"></section>`;
    const st = !S && INFO && (INFO.strays || [])[0];
    if (st) return `<div class="ag-empty"><h3>${esc(at("empty_h", { a: m.label }))}</h3><p>${esc(at("stray", { x: cut(st.first || "—", 40) }))}</p><div class="ag-opts"><button type="button" class="btn btn-primary" id="agBring" data-sid="${esc(st.id)}">${esc(at("stray_go"))}</button></div></div>`;
    return `<div class="ag-empty"><h3>${esc(at("empty_h", { a: m.label }))}</h3>${S ? "" : startPicks()}<p>${esc(at("empty_b"))}</p><p class="ag-mute">${esc(at("empty_c"))}</p>${prepare}${KIND === "dsh" ? `<p class="ag-mute">${esc(at("empty_dsh"))}</p>` : ""}</div>`;
  }
  function itemHtml(it) {
    const a = esc(label());
    if (it.kind === "user") return `<div class="ag-me">${it.scope && it.scope.label ? `<span class="chip">${esc(at("t_on", { x: cut(it.scope.label, 40) }))}</span>` : ""}<p>${esc(it.text)}</p></div>`;
    if (it.kind === "msg" && AUTH_MSG.test(it.text)) return `${HINTS.has(it.key) ? signInHint("warn") : ""}<details class="ag-thought"><summary>${esc(at("raw_said"))}</summary><div class="ag-md">${md(it.text)}</div></details>`;
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
      if (it.error && /auth/i.test(it.error)) return HINTS.has(it.key) ? signInHint("bad") : `<p class="ag-sys bad">${esc(at("turn_signed_out"))}</p>`;   // "Authentication required", a stopped turn too
      if (it.stop === "cancelled") return `<p class="ag-sys">${esc(at(it.asked ? "turn_cancelled" : "turn_halted"))}${it.took ? " · " + esc(secs(it.took)) : ""}</p>`;   // Codex ends a turn so after a refusal
      if (it.error === "agent_stuck") return "";   // the notice after it says what happened
      if (it.error) return `<p class="ag-sys bad">${esc(it.error === "agent_gone" ? at("turn_gone") : it.error === "desk_restart" ? at("turn_restart") : at("turn_error", { e: cut(it.error, 160) }))}</p>`;
      return it.took ? `<p class="ag-sys">${esc(at("turn_took", { s: secs(it.took) }))}</p>` : "";
    }
    if (it.kind === "notice" && it.code === "signed_out") return HINTS.has(it.key) ? signInHint("warn") : "";
    if (it.kind === "notice" && it.code === "place_busy") return `<p class="ag-note warn">${esc(at("n_place_busy", { x: it.name || "", w: it.who || "?" }))}</p>`;
    if (it.kind === "notice" && it.code === "placed") return `<p class="ag-note ok">${esc(at("n_placed", { x: it.name || "" }))}</p>`;
    if (it.kind === "notice" && /^own/.test(it.code || "")) return `<p class="ag-note${it.code === "own_busy" ? " warn" : " ok"}">${esc(at("n_" + it.code, { a: label() }))}</p>`;
    if (it.kind === "notice" && it.code === "restarted") return `<p class="ag-note warn">${esc(at("n_restarted", { a: label() }))}</p>`;
    if (it.kind === "notice") return `<p class="ag-sys">${esc(at({ fresh: "n_fresh", agent_gone: "n_gone", unsupported: "n_unsupported" }[it.code] || "n_gone", { m: it.method || "" }))}</p>`;
    if (it.kind === "unknown") return `<details class="ag-unknown"><summary>${esc(at("unknown", { a: label() }))}</summary><pre>${esc(cut(JSON.stringify(it.u, null, 1), 2000))}</pre></details>`;
    return "";
  }
  const AUTH_MSG = /^\s*(Failed to authenticate|Authentication required|Not logged in|Invalid API key)/i;   // the agent's own words for it
  let HINTS = new Set();   // the lines that say how to sign in (loginHints): the others say it no more
  const signInHint = (cls) => `<p class="ag-note ${cls}">${esc(at("n_signed_out", { a: label(), l: at("login_" + KIND) }))}</p>`;
  function loginHints(items) {   // how to sign in, said once a stretch, and always once: the first sign of it (the agent's "not
    // signed in" notice, its own words for it, a turn that failed for it, a stopped one too) says how; the ones after it only that the
    // sentence wasn't done (a turn), or nothing (a notice; its words stay folded), until a turn ends well (signed in again; a stopped
    // turn is not that). Decided in order, so a notice that comes after the failed turn (Claude Code's login check can) doesn't say it twice
    const out = new Set(); let said = false;
    for (const x of items || []) {
      const auth = (x.kind === "notice" && x.code === "signed_out") || (x.kind === "end" && x.error && /auth/i.test(x.error)) || (x.kind === "msg" && AUTH_MSG.test(x.text || ""));
      if (auth) { if (!said) out.add(x.key); said = true; }
      else if (x.kind === "end" && !x.error && x.stop !== "cancelled") said = false;
    }
    return out;
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
      : at({ stop: "perm_by_stop", timeout: "perm_by_timeout", agent_gone: "perm_by_gone", desk_restart: "perm_by_restart", turn_end: "perm_by_turn", desk_stop: "perm_by_desk" }[ans.by] || "perm_by_turn", { m: Math.round(((INFO && INFO.approval_timeout) || 600) / 60) });
    return `<p class="ag-ans ${/^allow/.test(ans.kind || "") ? "ok" : "no"}">${esc(by)}</p>`;
  }
  const DOM = new Map();   // an item's key → [its version, its element, whether it says how to sign in]: only what changed is drawn again
  function renderThread() {
    const th = $("#agThread"); if (!th) return;
    if (!S || !S.items.length || NEWBOX) {
      DOM.clear();
      th.innerHTML = NEWBOX ? newBoxHtml() : emptyHtml() + (S && S.running ? workingHtml() : "");
      wireThread(th);
      if (KEYP === SPACE && typeof spaceRunning === "function") spaceRunning();   // the films an agent is on now, under the sentence
      return;
    }
    const stick = th.scrollHeight - th.scrollTop - th.clientHeight < 40;
    if (th.querySelector(".ag-empty, .ag-new")) th.innerHTML = "";
    const wk = th.querySelector(".ag-working"); if (wk) wk.remove();
    HINTS = loginHints(S.items);
    for (const it of S.items) {
      const was = DOM.get(it.key), hint = HINTS.has(it.key);
      if (was && was[0] === it.v && was[2] === hint && was[1].isConnected) continue;
      const box = document.createElement("div"); box.className = "ag-item"; box.dataset.k = it.key;
      const open = was ? [...was[1].querySelectorAll("details")].map((x) => x.open) : [];
      box.innerHTML = itemHtml(it);
      [...box.querySelectorAll("details")].forEach((x, i) => { if (open[i]) x.open = true; });
      if (was && was[1].isConnected) was[1].replaceWith(box); else th.appendChild(box);
      DOM.set(it.key, [it.v, box, hint]);
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
  function startPicks() {   // where a conversation starts: the model and effort it will start with, as menus when this run has seen the agent's list
    const m = meta(KIND), ch = m.choices || {}, off = ch.offered || null, own = at("own_default", { a: m.label });
    const menus = [["model", "model", "set_model"], ["effort", "thought_level", "set_effort"]].map(([role, cat, k]) => {
      const list = off && Array.isArray(off[role]) ? off[role] : [];
      if (!list.length) return "";
      const cur = NEWASK[role] || (ch[role] && ch[role].value) || "";
      return `<label class="ag-pick"${role === "effort" ? ` title="${esc(at("eff_tip"))}"` : ""}><span>${esc(at(k))}</span><select data-new="${role}">${cur ? "" : `<option value="" selected>${esc(own)}</option>`}${list.map((x) => `<option value="${esc(x.value)}"${x.value === cur ? " selected" : ""}>${esc(optWord(cat, x))}</option>`).join("")}</select></label>`;
    }).join("");
    if (menus) return `<div class="ag-line ag-start">${menus}</div>`;
    const word = (role, cat) => { const c = ch[role] || {}; return c.name ? optWord(cat, { value: c.value || c.name, name: c.name }) : ""; };
    const eff = word("effort", "thought_level"), x = [word("model", "model"), eff ? at("eff_is", { e: eff }) : ""].filter(Boolean);
    return `<p class="ag-mute">${esc(x.length ? at("new_with", { x: x.join(LANG === "zh" ? "，" : ", ") }) : at("new_own", { a: m.label }))}</p>`;
  }
  function newBoxHtml() {
    const m = meta(KIND);
    return `<div class="ag-new"><h3>${esc(at("new_h"))} · ${esc(m.label)}</h3>${startPicks()}${m.settings_toggle ? `<label class="ag-check" title="${esc(at("personal_tip"))}"><input type="checkbox" id="agPersonal" checked> ${esc(at("personal_on"))}</label>` : ""}<div class="ag-opts"><button type="button" class="btn btn-primary" id="agNewGo">${esc(at("new_go"))}</button><button type="button" class="btn ghost" id="agNewNo">${esc(at("cancel"))}</button></div></div>`;
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
      if (e.target.closest("#agInstall") && e.isTrusted) { installKind(); return; }
      if (e.target.closest("#agInstallStop") && e.isTrusted) { installKind(true); return; }
      if (e.target.closest("#agPickFirst") && e.isTrusted) { start(KIND, true); return; }
      if (e.target.closest("#agNewGo")) { const p = $("#agPersonal"); NEWBOX = false; start(KIND, p ? p.checked : true); return; }
      if (e.target.closest("#agNewNo")) { NEWBOX = false; render(); }
      const own = e.target.closest("[data-own]");
      if (own) { e.preventDefault(); back(own.dataset.own); return; }
      const br = e.target.closest("#agBring");
      if (br && e.isTrusted) { br.disabled = true; bring(br.dataset.sid); return; }
      if (e.target.closest("#agCopyAsk") && e.isTrusted) {   // the sentence, for an agent somewhere else (the way it was before Studio could start one)
        const ta = $("#agSay"), x = ta ? ta.value.trim() : "";
        if (!x) { toast(at("sp_empty")); if (ta) ta.focus(); return; }
        copyText(t("ask_prefix") + x).then(() => toast(at("sp_copied")));
      }
    };
    th.onchange = (e) => { const x = e.target.closest("select[data-new]"); if (x && e.isTrusted) { if (x.value) NEWASK[x.dataset.new] = x.value; else delete NEWASK[x.dataset.new]; } };
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
      f.innerHTML = `<div class="ag-offer" id="agOffer" hidden></div><button type="button" class="ag-ask" id="agAsk" hidden></button><div class="ag-busy" id="agBusy" hidden></div><div class="crow"><span id="agAt">${esc(t("at"))}</span><span class="chip" id="agScope"></span><span class="kbd" aria-hidden="true">${esc(at("send_keys"))}</span><button type="button" class="btn ghost" id="agStop" hidden>${esc(at("stop"))}</button><button type="button" class="btn btn-primary" id="agSend">${esc(at("send"))}</button></div>
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
        if (e.target.closest("#agAnyway")) again(e);
        else if (e.target.closest("#agNotNow")) { BUSY = null; TELLING = ""; renderFoot(); }
        else if (e.target.closest("#agOfferGo")) offer(e, OFFER);
        else if (e.target.closest("#agOfferNo")) { OFFER = null; render(); }
        else if (e.target.closest("#agAsk")) { const c = $("#agThread .ag-perm:not(.done)"); if (c) c.scrollIntoView({ block: "center", behavior: reduced() ? "auto" : "smooth" }); }
      });
    }
    const sp = KEYP === SPACE, first = sp && !(S && S.items.length);   // the space: nothing selected to be on
    $("#agScope").textContent = sp ? "" : x; $("#agScope").className = "chip" + (sc ? "" : " quiet"); $("#agScope").hidden = sp; $("#agAt").hidden = sp;
    $("#agSay").placeholder = first ? at("sp_ph") : sc ? at("ph_say", { x: sc.label }) : at("ph_say0", { a: label() });
    $("#agSay").disabled = !meta(KIND).installed || !KEYOK;
    $("#agStop").hidden = !running; $("#agStop").disabled = !!(S && S.stopping);
    $("#agSend").disabled = !meta(KIND).installed || !KEYOK || !!(ERR && ERR.code === "starting");
    f.classList.toggle("off", !KEYOK);
    const waitp = S ? Object.values(S.perms).filter((p) => !p.answered) : [];
    const ask = $("#agAsk"); ask.hidden = !waitp.length;
    ask.textContent = waitp.length ? at("ask_bar", { a: label(), x: cut(toolTitle(Object.assign({}, (S.tools[(waitp[0].tool || {}).toolCallId] || {}).d || {}, waitp[0].tool || {})) || verbWords(waitp[0].tool || {}), 48) }) + " ↑" : "";
    const of = $("#agOffer"), ofOn = !!(OFFER && sp && KEYOK && meta(KIND).installed);   // not set up: the install panel says it
    of.hidden = !ofOn;
    const ofHtml = ofOn ? `<span>${esc(at(busyNow() ? "of_busy" : "of_ready", { x: offerName() }))}</span><span class="ag-opts">${busyNow() ? "" : `<button type="button" class="btn btn-primary" id="agOfferGo">${esc(at("of_go"))}</button>`}<button type="button" class="btn ghost" id="agOfferNo">${esc(at("of_no"))}</button></span>` : "";
    if (of.dataset.html !== ofHtml) { of.innerHTML = ofHtml; of.dataset.html = ofHtml; }
    const bz = $("#agBusy"); bz.hidden = !busy;
    bz.innerHTML = busy ? `<span>${esc(busy)}</span>${anyway ? `<span class="ag-opts"><button type="button" class="btn" id="agAnyway">${esc(at("busy_anyway"))}</button><button type="button" class="btn ghost" id="agNotNow">${esc(at("busy_not"))}</button></span>` : ""}` : "";
  }
  function render() { renderHead(); renderThread(); renderFoot(); }
  async function bring(sid) {   // the person's click on a new film's empty column: that conversation from the space comes here
    const r = await post(`${sid}/bring`, {});
    if (!(r.ok && r.data && r.data.ok)) { toast(at("stray_fail")); render(); return; }
    await load();
    const s = ((INFO && INFO.sessions) || []).find((x) => x.id === sid);
    if (s) { KIND = s.kind; open(s); }
    render();
  }
  let SPACETICK = 0;
  function watchSpace() {   // the space's list follows its conversations: one that starts waiting for you shows at once
    clearInterval(SPACETICK);
    SPACETICK = setInterval(async () => {
      if (KEYP !== SPACE) return clearInterval(SPACETICK);
      const sig = () => JSON.stringify([((INFO && INFO.sessions) || []).map((x) => [x.id, x.running, x.pending]), kinds().map((k) => k.installed)]);
      const before = sig();
      if (!(await load()) || KEYP !== SPACE || sig() === before) return;
      if (meta(KIND).installed && ERR && ERR.code === "not_installed") { ERR = null; renderFoot(); }   // set up from a terminal meanwhile
      renderHead(); if (!S || !S.items.length) renderThread();
    }, 4000);
  }
  async function fresh() {   // the space: a sentence box for another new film (the one open stays in the history, and goes on)
    close(); NEWBOX = false; ERR = null; BUSY = null; NEWASK = {};
    await load(); KIND = defaultKind();   // a new film's conversation starts with the default agent
    store_.set(`desk:agent:${SPACE}`, { kind: KIND });
    render();
    const ta = $("#agSay"); if (ta) ta.focus();
  }

  async function offer(e, id) {   // the space's sample wall (studio.js): the person's click puts that sample's sentence (Studio's own
    // words, core.js smp_<id>_say, never a page's or a file's) in the box for a new film, and sends nothing. A box that can't be typed in
    // is not filled: a page that can only look says so; with no agent set up the sample is kept, the install panel says it and comes
    // into view; while the space's chat works or waits for approval, it stays (a line under the box offers the sentence once it stops).
    // An idle chat open on the space gives way to a new film's box (it stays in the history: said so); what the person had written is
    // replaced as typing would (⌘Z brings it back); a ［…］ to fill in is selected
    const sample = /^[a-z]+$/.test(String(id || "")) ? word(`smp_${id}_say`) : null;
    if (!e || !e.isTrusted || KEYP !== SPACE || typeof sample !== "string") return false;
    if (!KEYOK) { toast(t("nokey")); return false; }
    const keep = (where) => { OFFER = id; render(); const el = $(where); if (el) el.scrollIntoView({ block: "nearest", behavior: reduced() ? "auto" : "smooth" }); return false; };
    if (!meta(KIND).installed) return keep("#agThread .ag-empty");
    if (busyNow()) return keep("#agOffer");
    const moved = !!(S && S.items.length);
    if (moved) await fresh();
    const ta = $("#agSay");
    if (!ta || ta.disabled) return keep("#agOffer");
    OFFER = null; renderFoot();
    ta.focus(); ta.select();
    let typed = false;
    try { typed = document.execCommand("insertText", false, sample) && String(ta.value) === sample; } catch (x) { typed = false; }
    if (!typed) ta.value = sample;
    store_.set(`desk:agent:say:${KEYP}`, ta.value);
    const m = /［[^］]*］|\[[^\]]*\]/.exec(sample);
    if (m) ta.setSelectionRange(m.index, m.index + m[0].length); else ta.setSelectionRange(sample.length, sample.length);
    ta.scrollIntoView({ block: "nearest" });
    toast(moved ? at("of_moved") : t("smp_filled"));
    return true;
  }

  /* ---------- the column's two tabs: this conversation, this round ---------- */
  function tabs() {
    const bar = $("#colTabs"); if (!bar) return;
    const waiting = S ? Object.values(S.perms).filter((p) => !p.answered).length : 0;
    const handed = typeof handedNow === "function" && handedNow() && !(typeof REHAND !== "undefined" && REHAND[KEY]);   // handed over: nothing left to decide here
    const decs = !handed && typeof GV !== "undefined" && GV && GV.current && typeof roundOpen === "function" && roundOpen() ? ((ROUND && ROUND.data && ROUND.data.decisions) || []).length : 0;
    const mine = typeof myItems === "function" && FB ? myItems().length : 0;
    bar.hidden = !KEYP || KEYP === SPACE;
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
    async enter(key) {   // a film opened (or drawn again): its conversations, the last one this page had open; SPACE: the space's
      if (key === KEYP && INFO) { tabs(); renderFoot(); renderHead(); return; }
      this.leave();
      KEYP = key;
      const decs = key !== SPACE && typeof GV !== "undefined" && GV && GV.current && typeof roundOpen === "function" && roundOpen() && ((ROUND && ROUND.data && ROUND.data.decisions) || []).length;
      TAB = key === SPACE ? "chat" : store_.get(`desk:coltab:${key}`) || (decs ? "round" : "chat");
      $("#col").classList.toggle("chat", TAB === "chat");
      if (!(await load()) || KEYP !== key) { tabs(); return; }
      const saved = store_.get(`desk:agent:${KEYP}`) || {};
      const m = meta(KIND);
      if (!m.installed) ERR = { code: "not_installed" };
      else {   // the space opens on the sentence box, unless a film begun there is still going (or this page had it open)
        const mine = sessionsOf(KIND).find((x) => x.id === saved.sid);
        const s = key === SPACE ? mine || sessionsOf(KIND).find((x) => x.running || x.pending) : mine || sessionsOf(KIND)[0];
        if (s) open(s);
      }
      render(); followInstall();   // an install still running (started before this page opened): followed to its end
      if (key === SPACE) watchSpace();
    },
    leave() { clearTimeout(INSTWATCH); clearInterval(SPACETICK); close(); KEYP = ""; INFO = null; KIND = ""; BUSY = null; ERR = null; NEWBOX = false; DOM.clear(); const b = $("#colTabs"); if (b) b.hidden = true; $("#col").classList.remove("chat"); const f = $("#agFoot"); if (f) f.dataset.ready = ""; const h = $("#agHead"); if (h) h.dataset.ready = ""; },
    scope() { if (KEYP) renderFoot(); },
    keyOk(ok) { KEYOK = !!ok; if (!KEYOK) close(); if (KEYP) render(); },   // without this run's token the conversation is not opened at all (the note at the top says why)
    token(t) { TOKEN_ = t; },   // the token the page got after it loaded: its code traded, or another tab's of this run (studio.js)
    lang() { if (KEYP) { const f = $("#agFoot"); if (f) f.dataset.ready = ""; const h = $("#agHead"); if (h) h.dataset.ready = ""; const b = $("#colTabs"); if (b) b.dataset.html = ""; DOM.clear(); render(); } },
    tabs, setTab, fresh,
    offer,
    listening(on) { if (LISTEN !== !!on) { LISTEN = !!on; if (KEYP && KEYP !== SPACE) renderHead(); } },
    async tell(e, text) {   // Studio's own button (the column's one action): its own words (bin/vh status's, Studio's word table and numbers), sent in this
      // film's conversation, the newest one, else a new one; the box keeps the person's draft (it is filled only by them)
      if (!e || !e.isTrusted || !KEYP || KEYP === SPACE || !text || !KEYOK) return;
      setTab("chat");
      if (!S && meta(KIND).installed) { const last = sessionsOf(KIND)[0]; if (last) open(last); }
      if (!S && !(await start(KIND, true))) return;
      await sayWords(text, false);
    },
    _again: (e) => again(e),   // for tools/desk/test_agents.py (node): the busy line's "anyway" after a refused carry-on
    busy: () => !!(S && S.running && KEYP !== SPACE),   // a turn in this film's column now (the flow strip's agent lamp)
    _md: md, _diff: diffLines, _hints: (items) => [...loginHints(items)],
    _draw: (items) => { const keep = [S, KIND]; S = blank({ id: "t", kind: "claude" }); KIND = "claude"; items.forEach((x) => { x.v = 1; S.items.push(x); S.index[x.key] = x; }); HINTS = loginHints(S.items); const out = S.items.map(itemHtml); [S, KIND] = keep; return out; }, _ask: (pm, d) => askHtml(pm, d), _defaultKind: defaultKind, _state: () => (S ? { id: S.id, items: S.items.length, seq: S.seq, es: ES ? ES.readyState : null, url: ES ? ES.url.replace(/token=[^&]*/, "token=…") : null } : null),   // for tools/desk/test_agents.py (node): the escaping and the diff, without a page
  };
})();
