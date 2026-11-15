"use strict";
/* What the console (studio.js) and a static review page (static.js) share: the words (STR; the other modules add theirs in
   modules.js), escaping and formatting, the film's flow of stops and its lamps, a module's kicker and sub-tabs, and the few
   readers of the project's data the modules use. Nothing here touches the page when it loads; the host declares the state
   these functions read (D, PKEY, SUB) and runs them. */
const STR = {
  zh: {
    brand: "片场", noServer: "读不到数据：请用 bin/vh desk 打开这一页。", loading: "…", gate: "关卡",
    m_new: "新建", new_tip: "从一句话新建要接上 agent（第二期）；这一版在空间页把这句话拼好，复制给你的 agent",
    m_space: "空间", m_idea: "立意", m_outline: "大纲", m_board: "分镜", m_sound: "声音", m_cut: "成片", m_ship: "交付", m_assets: "素材", m_ledger: "账本",
    f_done: "过了", f_wait: "等你", f_agent: "轮到 agent", f_todo: "还没到", f_skip: "跳过", f_off: "这支片子这一站不停", f_norec: "没有审阅记录",
    pick_film: "先在空间里选一支片子", search: "搜片子", search_ph: "片名、文件夹或类型，回车打开", no_match: "没有对上的片子", lang: "EN", lang_tip: "Switch to English", themes: "主题",
    th_darkfield: "暗场", th_prism: "棱镜", th_bridge: "舰桥", skip: "跳到内容", rail: "模块", flow: "这支片子的几站",
    ask_kick: "从一句话开始", ask_h: "你想做一支什么样的片子？", ask_ph: "比如：做一支一分钟的科普，讲海水为什么一天涨两次",
    ask_note: "这一版控制台不连 agent：写好这一句，复制到你的 agent 对话里，它会建项目、往下做。", ask_copy: "复制给 agent", ask_copied: "复制好了：粘贴到你的 agent 对话里",
    ask_prefix: "用 OpenVideoHarness 做一支片子：", ask_empty: "先写一句",
    films: "片子", home_meta: "{n} 支 · {w} 支等你", home_meta0: "{n} 支", g_wait: "等你看的", g_rest: "其余", roots: "从这些文件夹里找的：{r}",
    no_projects: "这里还没有片子。bin/vh new 建一个，或者 bin/vh desk --root <文件夹> 告诉我去哪找。",
    st_waiting_person: "等你看", st_waiting_agent: "轮到 agent", st_in_progress: "进行中", st_delivered: "已交付", st_paused: "暂停",
    st_no_record: "没有审阅记录", st_not_started: "还没开始", st_skipped: "跳过", st_done: "过了",
    ask_n: "要你定 {n} 件：{q}", ask_0: "看一眼：{q}", just_now: "刚才", ago_m: "{n} 分钟前", ago_h: "{n} 小时前", ago_d: "{n} 天前",
    col_space: "空间", col_space_note: "选一支片子：点评和决定都记在那支片子里。", waiting_list: "等你看的", agent_list: "正在跑的", none_waiting: "没有片子在等你。",
    col_round: "这一轮", col_notes: "随手点评", live_on: "agent 在等", live_off: "agent 没在等",
    live_on_tip: "提交后 agent 会自动接着做，不用回对话", live_off_tip: "提交后回到对话里说一声“看审阅台”",
    c_decide: "要你定", c_rec: "没动的按推荐", c_least: "它最没把握的", c_listen: "请你听", c_mine: "我的点评", c_next: "下一步", c_running: "正在跑", c_spend: "花费",
    c_spent: "已花 {s}", c_of: "预算 {l}", c_none_mine: "还没有。选中一处（一秒、一段、一个镜头），在下面写一句。", who_agent: "agent", who_person: "你", who_nobody: "交付了",
    round_sum: "{n} 条点评 · {d} 个决定", submit_round: "提交这一轮", c_whole_note: "整体", round_quiet: "{g} · {s}：现在没有要你定的事。", static_page: "静态页", recent: "最近定下的", agent_decided_k: "agent 定的 · {x}",
    at: "对着", whole: "整个{m}", whole_film: "整片", to_whole: "换成整个模块", say_agent: "说给 agent", say_agent_tip: "这一版控制台不连 agent：写成点评，提交这一轮时交给它",
    as_note: "记成点评", c_ph: "对「{x}」说一句", note_add: "记下", note_keys: "⌘↩ 记下", noted: "记下了：{x}", del: "删",
    d_dropped: "这 {n} 条写不进反馈文件，不会提交（对着的东西认不出，或者字太长）",
    d_title: "提交这一轮", d_decisions: "决定", d_items: "点评", by_rec: "（按推荐）", d_none: "没有逐条点评；没标的都算通过。",
    general: "整体意见（可选）", general_ph: "比如：整体节奏偏慢；开场很好……", submit: "提交", cancel: "再看看", preview: "会提交的内容",
    submit_hint: "提交后写进项目的 out/review/feedback/，你的原话同时抄进 REVIEW.md。没动的决定按推荐算。",
    sent_live: "已提交，agent 已经在接着做", sent: "已提交：{f}",
    hint_live: "已写进 {f}，原话也抄进了 REVIEW.md。agent 在等这份反馈，已经自动接着做了，不用再回对话。",
    hint_idle: "已写进 {f}，原话也抄进了 REVIEW.md。agent 这会儿没在等：回到对话里说一声“看审阅台”。",
    offline: "没有连上本地服务：回复已复制，粘贴到对话里即可", offline2: "没有连上本地服务：请复制下面的内容", refused: "没有提交成功：{e}", moved: "没有提交：这个地址现在指的已经不是你打开的那支片子了。重新载入页面，再交一次（草稿还在）。",
    reply_head: "《{p}》{r} 的回复", rest: "其余没标的都算通过。", round_name: "关卡 {r}", notes_round: "随手点评", overall: "整体",
    submitted: "这一轮已经提交过（{at}）。再提交会另存一份，REVIEW.md 里也会多一节。", new_round: "agent 发来了新的一页：{g}",
    sent_n: "已交 {n} 条点评、{d} 个决定（{at}）。再交只发新写的点评和改过的决定。", proj_ph: "<项目>", ns_raw: "bin/vh status 的原话",
    past: "这是之前的一页（{g}），看看就好。", to_round: "回到这一轮 →", page_of: "看{g}那一页 →", st_ok: "可以", st_change: "要改", st_ask: "疑问",
    fb_ok: "✓ 可以", fb_change: "✎ 要改", fb_ask: "? 疑问", fb_def: "不点就算通过", ph_change: "哪里要改、为什么", ph_ask: "哪里没看懂？",
    ph_suggest: "直接改成……（可选）", agree: "✓ 同意", overturn: "✎ 翻案", def_agree: "不点就算同意",
    fact_ok: "✓ 对", fact_bad: "✎ 有问题", fact_unsure: "? 拿不准", fact_def: "不点 = 没看",
    l_least: "没把握：{x}", l_deleg: "我替你定的：{x}", l_shot: "镜头 {x}", l_seg: "大纲 第 {i} 段 {x}", l_line: "旁白 {x}",
    film_label: "成片 {t}", range_label: "成片 {a}–{b}", sound_label: "声音 {t}", chapter_label: "章节 {x}",
    // the cut module
    l_shots: "镜头", l_script: "旁白稿", l_captions: "字幕", l_notes: "点评", l_checks: "检查",
    no_shots: "还没有镜头表。shots.json 写好后（或 bin/vh storyboard），镜头就排在这里。", no_narr: "还没有旁白的时间。bin/vh tts 出了配音，旁白稿和词的时间就到这里。",
    no_checks: "还没跑检查：bin/vh check <片子>。", check_stale: "片子在这次检查之后改过：再跑一次 bin/vh check", verdict: "结论",
    n_notes: "{n} 条点评", unsure: "没把握", n_checks: "{n} 处检查", reads: "要看懂", ver_n: "第 {n} 版", proxy: "代理",
    no_film_frames: "还没有成片：bin/vh render 之后在这里播。现在是分镜的关键帧。", no_film_sheet: "还没有成片：bin/vh render 之后在这里播。现在是联系表。", no_film0: "还没有成片，也没有分镜的关键帧和联系表。", film_gone_frames: "文件不在了：{p}（移走或改了名）。现在是分镜的关键帧。", film_gone_sheet: "文件不在了：{p}（移走或改了名）。现在是联系表。", film_gone0: "文件不在了：{p}（移走或改了名），也没有分镜的关键帧和联系表。",
    safe: "安全框", compare: "和{v}对比", ver_now: "{v} · 现在", lay_review: "审片", lay_fine: "精修", lay_sound: "听声音", layout: "布局",
    tl_hint: "点一下选这一秒，拖一段选区间，点镜头或章节选中它 · I/O 入点出点 · 空格播放 · ←→ 逐镜 · N 下一处",
    next_place: "下一处要看的", snap: "吸附", zoom_in: "放大", zoom_out: "缩小", play: "播放 / 暂停（空格）", prev_shot: "上一个镜头（←）", next_shot: "下一个镜头（→）",
    g_pic: "画面", g_sound: "声音", g_review: "审阅", ln_chap: "章节", ln_shots: "镜头", ln_voice: "旁白", ln_music: "音乐", ln_hits: "卡点", ln_wave: "波形", ln_marks: "点评·检查", ln_diff: "这一版改了",
    e_chap: "没有章节，大纲也没写时间", e_shots: "没有镜头表 · shots.json", e_voice: "没有旁白的时间 · bin/vh tts", e_music: "没有配乐的段落和节拍 · bin/vh beats", e_wave: "没有波形 · bin/vh peaks <项目>",
    e_diff: "这一版没有记下改了哪里（bin/vh patch 才记）", e_marks: "这里还没有点评和检查", whole_render: "整支重渲",
    diff_label: "{v} 改了这里", next_q: "下一处 · {x}", no_next: "后面没有要看的了", k_least: "没把握", k_listen: "请你听", k_check: "检查", k_mine: "我",
    sev_fail: "没过", sev_warn: "注意", no_thumbs: "bin/vh thumbs <项目> 做了缩略图，拖动时就能看到每一秒的画面",
    // the other modules (the desk's views, moved in)
    sub_outline: "大纲", sub_script: "字幕 / 旁白", sub_facts: "事实", sub_check: "检查", sub_versions: "版本", sub_decisions: "决定", sub_history: "历史", sub_docs: "文档",
    concept: "立意", spine: "故事线", motif: "贯穿全片的", end: "看完以后", spec: "规格", outline_tip: "点色块跳到那一段",
    seg_n: "第 {i} 段", know: "看完知道 / 感到", visual: "关键画面", seg_caps: "这一段的 {n} 条", to_script: "去逐条看 →", bars: "第 {b} 小节",
    no_outline: "大纲还没有写成表格（BRIEF 的 Outline 一节，列名见 tools/desk/README.md），下面是 BRIEF 原文。", no_brief: "还没有 BRIEF.md。",
    script_sub: "{n} 条，按大纲分段。读速按这一条占的时间粗算：中文 {g} 字/秒以内绿、{y} 以内黄；英文 {eg} / {ey} 字符/秒。",
    f_all: "全部", f_mine: "我标过的", f_terms: "带术语的", f_facts: "带出处编号的", f_fast: "可能读不完的",
    no_script: "SCRIPT.md 里没有字幕或旁白表格（列名见 tools/desk/README.md），下面是原文。", no_script_file: "还没有字幕稿或旁白稿（SCRIPT.md）。",
    other_seg: "没对上大纲的", per_s: "/秒", chars: "{n} 字 · {s} s", none_match: "没有符合的条目。", l_cap: "字幕 {x}", l_vo: "旁白 {x}", term: "术语",
    board_sub: "点画面播这一镜，播放时当前镜头会亮起；琥珀框是我没把握的镜头。", no_shot_caption: "（这一镜没有字幕）", transition: "转场：", unsure_x: "我没把握：",
    no_board: "还没有镜头表（shots.json 或 edit.json），下面是 STORYBOARD.md。", no_board_file: "还没有分镜。", no_video: "（没有可播放的视频，只看关键帧）",
    sound_sub: "agent 听不见，只能看谱面和响度；这一页请你用耳朵。{bpm} BPM，{d} s。", comment_at: "在 {t} 处点评",
    sec_tip: "色块是乐段，点一下从那里播；刻度是落在画面动作上的音", listen: "请你听这几处", your_sound: "你的声音点评",
    none_sound: "还没有。播到哪里觉得不对，就点上面的“在 … 处点评”。", roll: "谱面和响度（每一行是一件乐器，颜色越深越响）",
    no_music: "还没有配乐。", no_audio: "没有找到可以播放的音频（gate JSON 的 music.audio）。",
    facts_sub: "上屏的说法，和它背后的原话、出处。请重点看“上屏说法”有没有简化到错。", todo: "还没核实的", th_id: "#", th_claim: "素材（原文）",
    th_screen: "上屏说法", th_src: "出处", th_you: "你看", dropped: "（已不用）", l_fact: "事实 {x}",
    no_facts: "NOTES.md 里没有素材清单表格，下面是原文。", no_notes: "还没有 NOTES.md。",
    ledger_sub: "每件事谁拍板、现在是什么状态；我替你定的事都在下面，随时可以翻案。", th_what: "事", th_who: "谁拍板", th_status: "现在",
    agent_n: "我替你定的（{n}）", superseded: "已经作废的（{n}）", why: "理由", undo: "翻案要花", l_led: "决定 {x}",
    no_ledger: "DECISIONS.md 里没有决定表和“agent 定的事”，下面是原文。", no_dec: "还没有 DECISIONS.md。",
    history_sub: "每一轮你说的原话，和之后定了、改了什么（REVIEW.md）。", desk_subs: "审阅台的提交记录", no_history: "还没有记录。",
    docs_sub: "项目里的文档，原样排版。结构化的页面读不出来的内容，都在这里。", warnings: "这些没能按约定读出来（tools/desk/README.md）",
    no_docs: "项目里还没有文档。", l_doc: "{f} · {s}",
    check_sub: "bin/vh check 最近一次的结果，和最近的几支渲染。", no_check: "还没有 bin/vh check 的记录。", fails: "没过的",
    renders: "最近的渲染", th_file: "文件", th_size: "大小", th_when: "时间", th_check: "检查",
    versions_sub: "bin/vh versions 记着的每一版：哪一版是现在的，哪些留着。", no_versions: "还没有版本记录（第一次 bin/vh render 或 patch 之后才有）。",
    th_ver: "版", th_state: "状态", th_made: "怎么来的", th_note: "说明",
    assets_sub: "素材台账（bin/vh assets）：登记了多少，哪些许可还没清，花了多少。", no_assets: "还没有素材台账。",
    a_records: "登记", a_uncleared: "许可没清", a_not_taken: "片子用了但没登记", a_aigc: "生成的", a_spent: "已花", a_budget: "预算",
    stn: { "1": "立意", "2": "分镜", "3": "初版", E0: "样帧", E1: "脚本", E2: "声音", E3: "锁时", E4: "样板章", E5: "锁画面", deliver: "交付" },
  },
  en: {
    brand: "Studio", noServer: "Can't read the data: open this page with bin/vh desk.", loading: "…", gate: "Gate",
    m_new: "New", new_tip: "Starting a film from a sentence needs the agent (phase two); for now the space puts the sentence together for you to copy to your agent",
    m_space: "Space", m_idea: "Concept", m_outline: "Outline", m_board: "Storyboard", m_sound: "Sound", m_cut: "Cut", m_ship: "Delivery", m_assets: "Material", m_ledger: "Ledger",
    f_done: "passed", f_wait: "waiting for you", f_agent: "the agent's turn", f_todo: "not yet", f_skip: "skipped", f_off: "not a stop in this film", f_norec: "no review record",
    pick_film: "Pick a film in the space first", search: "Find a film", search_ph: "Title, folder or type; Enter opens it", no_match: "No film matches", lang: "中", lang_tip: "切换到中文", themes: "Theme",
    th_darkfield: "Darkfield", th_prism: "Prism", th_bridge: "Bridge", skip: "Skip to content", rail: "Modules", flow: "This film's stops",
    ask_kick: "Start from a sentence", ask_h: "What film do you want to make?", ask_ph: "e.g. a one-minute explainer on why the tide comes in twice a day",
    ask_note: "This console doesn't talk to an agent yet: write the sentence, paste it into your agent's chat, and it sets the project up and carries on.", ask_copy: "Copy for the agent",
    ask_copied: "Copied: paste it into your agent's chat", ask_prefix: "Make a film with OpenVideoHarness: ", ask_empty: "Write a sentence first",
    films: "Films", home_meta: "{n} · {w} waiting for you", home_meta0: "{n}", g_wait: "Waiting for you", g_rest: "The rest", roots: "Found under: {r}",
    no_projects: "No films here yet. Make one with bin/vh new, or tell me where to look: bin/vh desk --root <folder>.",
    st_waiting_person: "waiting for you", st_waiting_agent: "the agent's turn", st_in_progress: "in progress", st_delivered: "delivered",
    st_paused: "paused", st_no_record: "no review record", st_not_started: "not started", st_skipped: "skipped", st_done: "passed",
    ask_n: "{n} to decide: {q}", ask_0: "To look at: {q}", just_now: "just now", ago_m: "{n} min ago", ago_h: "{n} h ago", ago_d: "{n} {n|day|days} ago",
    col_space: "Space", col_space_note: "Pick a film: notes and decisions go into that film.", waiting_list: "Waiting for you", agent_list: "Running now", none_waiting: "No film is waiting for you.",
    col_round: "This round", col_notes: "Notes", live_on: "the agent is waiting", live_off: "the agent isn't waiting",
    live_on_tip: "Submit and the agent carries on by itself; no need to go back to the chat", live_off_tip: "After submitting, tell the agent in the chat: “check the desk”",
    c_decide: "To decide", c_rec: "untouched = recommended", c_least: "Least sure", c_listen: "Listen to", c_mine: "My notes", c_next: "Next", c_running: "Running", c_spend: "Spent",
    c_spent: "{s} spent", c_of: "of {l}", c_none_mine: "None yet. Select a place (a second, a span, a shot) and write a line below.", who_agent: "agent", who_person: "you", who_nobody: "delivered",
    round_sum: "{n} {n|note|notes} · {d} {d|decision|decisions}", submit_round: "Submit this round", c_whole_note: "Overall", round_quiet: "{g} · {s}: nothing waits for you to decide now.", static_page: "Static page", recent: "Recently decided", agent_decided_k: "the agent decided · {x}",
    at: "On", whole: "the whole {m}", whole_film: "the whole film", to_whole: "the whole module", say_agent: "Tell the agent", say_agent_tip: "This console doesn't talk to the agent yet: write a note, and it goes with this round",
    as_note: "Note it", c_ph: "A line on “{x}”", note_add: "Add", note_keys: "⌘↩ adds", noted: "Noted: {x}", del: "Delete",
    d_dropped: "{n} not sent: the feedback file cannot take what they are on, or they are too long",
    d_title: "Submit this round", d_decisions: "Decisions", d_items: "Notes", by_rec: " (recommended)", d_none: "No item notes; anything not marked passes.",
    general: "Overall (optional)", general_ph: "e.g. the pace drags overall; the opening works…", submit: "Submit", cancel: "Keep looking", preview: "What will be submitted",
    submit_hint: "Submissions go to the project's out/review/feedback/, and your words into REVIEW.md. Untouched decisions go by the recommendation.",
    sent_live: "Submitted; the agent is on it", sent: "Submitted: {f}",
    hint_live: "Saved to {f}; your words are in REVIEW.md too. The agent was waiting for this and has carried on; no need to go back to the chat.",
    hint_idle: "Saved to {f}; your words are in REVIEW.md too. The agent isn't waiting right now: tell it in the chat, “check the desk”.",
    offline: "Couldn't reach the local server: the reply is copied, paste it into the chat", offline2: "Couldn't reach the local server: copy the text below", refused: "Not submitted: {e}", moved: "Not submitted: this address no longer names the film you opened. Reload the page and submit again (your draft is kept).",
    reply_head: "Reply to {r} of “{p}”", rest: "Everything not marked passes.", round_name: "gate {r}", notes_round: "notes", overall: "Overall",
    submitted: "Already submitted this round ({at}). Submitting again saves another copy and adds another section to REVIEW.md.", new_round: "The agent sent a new page: {g}",
    sent_n: "Sent {n} {n|note|notes} and {d} {d|decision|decisions} ({at}). Submitting again sends only new notes and changed decisions.", proj_ph: "<project>", ns_raw: "bin/vh status's words",
    past: "An earlier page ({g}), to look at only.", to_round: "Back to this round →", page_of: "See the page of {g} →", st_ok: "ok", st_change: "change", st_ask: "question",
    fb_ok: "✓ OK", fb_change: "✎ Change", fb_ask: "? Question", fb_def: "untouched = approved", ph_change: "What to change, and why", ph_ask: "What's unclear?",
    ph_suggest: "Change it to… (optional)", agree: "✓ Agree", overturn: "✎ Overturn", def_agree: "untouched = agreed",
    fact_ok: "✓ Right", fact_bad: "✎ Wrong", fact_unsure: "? Not sure", fact_def: "untouched = not checked",
    l_least: "Unsure: {x}", l_deleg: "Decided for you: {x}", l_shot: "Shot {x}", l_seg: "Outline part {i} {x}", l_line: "Narration {x}",
    film_label: "Film {t}", range_label: "Film {a}–{b}", sound_label: "Sound {t}", chapter_label: "Chapter {x}",
    l_shots: "Shots", l_script: "Narration", l_captions: "Captions", l_notes: "Notes", l_checks: "Checks",
    no_shots: "No shot table yet. Once shots.json is written (or bin/vh storyboard), the shots line up here.", no_narr: "No narration timing yet. Once bin/vh tts has voiced it, the lines and their times come here.",
    no_checks: "No check yet: bin/vh check <film>.", check_stale: "The film changed after this check: run bin/vh check again", verdict: "Verdict",
    n_notes: "{n} {n|note|notes}", unsure: "unsure", n_checks: "{n} {n|check|checks}", reads: "Reads", ver_n: "v{n}", proxy: "proxy",
    no_film_frames: "No film yet: it plays here after bin/vh render. These are the storyboard's key frames.", no_film_sheet: "No film yet: it plays here after bin/vh render. This is the contact sheet.", no_film0: "No film yet, and no storyboard key frames or contact sheet.", film_gone_frames: "Not there any more: {p} (moved or renamed). These are the storyboard's key frames.", film_gone_sheet: "Not there any more: {p} (moved or renamed). This is the contact sheet.", film_gone0: "Not there any more: {p} (moved or renamed), and no storyboard key frames or contact sheet.",
    safe: "Safe area", compare: "Compare with {v}", ver_now: "{v} · now", lay_review: "Review", lay_fine: "Fine cut", lay_sound: "Listen", layout: "Layout",
    tl_hint: "Click a second, drag a span, click a shot or chapter to select it · I/O in and out · Space plays · ←→ shot by shot · N next place",
    next_place: "Next place", snap: "Snap", zoom_in: "Zoom in", zoom_out: "Zoom out", play: "Play / pause (Space)", prev_shot: "Previous shot (←)", next_shot: "Next shot (→)",
    g_pic: "Picture", g_sound: "Sound", g_review: "Review", ln_chap: "Chapters", ln_shots: "Shots", ln_voice: "Voice", ln_music: "Music", ln_hits: "Hits", ln_wave: "Waveform", ln_marks: "Marks", ln_diff: "Changed",
    e_chap: "No chapters, and the outline has no times", e_shots: "No shot table · shots.json", e_voice: "No narration timing · bin/vh tts", e_music: "No music sections or beats · bin/vh beats", e_wave: "No waveform · bin/vh peaks <project>",
    e_diff: "This version doesn't record what changed (bin/vh patch does)", e_marks: "No notes or checks here yet", whole_render: "re-rendered whole",
    diff_label: "{v} changed this", next_q: "Next · {x}", no_next: "Nothing more after here", k_least: "unsure", k_listen: "listen", k_check: "check", k_mine: "me",
    sev_fail: "failed", sev_warn: "warning", no_thumbs: "bin/vh thumbs <project> makes thumbnails: then dragging shows every second",
    sub_outline: "Outline", sub_script: "Captions / narration", sub_facts: "Facts", sub_check: "Check", sub_versions: "Versions", sub_decisions: "Decisions", sub_history: "History", sub_docs: "Documents",
    concept: "Concept", spine: "Spine", motif: "Recurring motif", end: "At the end", spec: "Spec", outline_tip: "click a block to jump to it",
    seg_n: "Part {i}", know: "The viewer knows / feels", visual: "Key visual", seg_caps: "{n} {n|line|lines} in this part", to_script: "go through them →", bars: "bars {b}",
    no_outline: "The outline isn't a table yet (BRIEF's Outline section; columns in tools/desk/README.md). Here is the BRIEF as written.", no_brief: "No BRIEF.md yet.",
    script_sub: "{n} {n|line|lines} by outline part. Reading speed, roughly, from each line's span: Chinese up to {g} chars/s green, {y} yellow; English {eg} / {ey}.",
    f_all: "All", f_mine: "Marked by me", f_terms: "With a term", f_facts: "With a source #", f_fast: "Maybe too fast",
    no_script: "SCRIPT.md has no caption or narration table (columns in tools/desk/README.md). Here it is as written.", no_script_file: "No captions or narration yet (SCRIPT.md).",
    other_seg: "Not matched to the outline", per_s: "/s", chars: "{n} {n|char|chars} · {s} s", none_match: "Nothing matches.", l_cap: "Caption {x}", l_vo: "Narration {x}", term: "Term",
    board_sub: "Click a frame to play that shot; the current shot lights up while playing; amber frames are shots I'm unsure about.", no_shot_caption: "(no caption in this shot)",
    transition: "Transition: ", unsure_x: "Unsure: ", no_board: "No shot table yet (shots.json or edit.json). Here is STORYBOARD.md.", no_board_file: "No storyboard yet.",
    no_video: "(no video to play; keyframes only)",
    sound_sub: "The agent can't hear; it reads the score and the loudness. This page is for your ears. {bpm} BPM, {d} s.", comment_at: "Comment at {t}",
    sec_tip: "blocks are sections, click one to play from there; ticks are notes that land on actions", listen: "Please listen to these", your_sound: "Your sound notes",
    none_sound: "None yet. When something sounds off, click “Comment at …” above.", roll: "Score and loudness (one row per instrument, darker = louder)",
    no_music: "No music yet.", no_audio: "No playable audio found (the gate JSON's music.audio).",
    facts_sub: "What goes on screen, and the source behind it. Check that the on-screen wording isn't simplified into something wrong.", todo: "Not verified yet",
    th_id: "#", th_claim: "Item (source wording)", th_screen: "On screen", th_src: "Source", th_you: "You", dropped: "(dropped)", l_fact: "Fact {x}",
    no_facts: "NOTES.md has no material table. Here it is as written.", no_notes: "No NOTES.md yet.",
    ledger_sub: "Who decides each thing and where it stands; what I decided for you is below, and you can overturn any of it.", th_what: "Decision", th_who: "Who decides", th_status: "Now",
    agent_n: "Decided for you ({n})", superseded: "Superseded ({n})", why: "Why", undo: "Cost to undo", l_led: "Decision {x}",
    no_ledger: "DECISIONS.md has no ledger table and no agent decisions. Here it is as written.", no_dec: "No DECISIONS.md yet.",
    history_sub: "Your words each round, and what was decided and changed after (REVIEW.md).", desk_subs: "Submissions from the desk", no_history: "Nothing yet.",
    docs_sub: "The project's documents, as written. Whatever the structured views can't read is here.", warnings: "Not read by the contract (tools/desk/README.md)",
    no_docs: "No documents in the project yet.", l_doc: "{f} · {s}",
    check_sub: "bin/vh check's latest result, and the latest renders.", no_check: "No bin/vh check record yet.", fails: "Failed",
    renders: "Latest renders", th_file: "File", th_size: "Size", th_when: "When", th_check: "Check",
    versions_sub: "Every version bin/vh versions keeps: which is current, which are kept.", no_versions: "No version record yet (the first bin/vh render or patch makes one).",
    th_ver: "Version", th_state: "State", th_made: "Made by", th_note: "Note",
    assets_sub: "The asset ledger (bin/vh assets): what is on record, which licences are not cleared, what was spent.", no_assets: "No asset ledger yet.",
    a_records: "On record", a_uncleared: "Licence not cleared", a_not_taken: "Used but not on record", a_aigc: "Generated", a_spent: "Spent", a_budget: "Budget",
    stn: { "1": "Concept", "2": "Storyboard", "3": "Draft", E0: "Style frames", E1: "Script", E2: "Sound", E3: "Timing lock", E4: "Sample chapter", E5: "Picture lock", deliver: "Delivery" },
  },
};

const $ = (s, el = document) => el.querySelector(s), $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let LANG = "zh", L = STR.zh;
const word = (k) => {   // the shell's words first, then the modules' (modules.js), in this language and then in English
  const M = typeof MSTR !== "undefined" ? MSTR : { zh: {}, en: {} };
  return [L[k], M[LANG][k], STR.en[k], M.en[k]].find((x) => x != null);
};
const t = (k, vars) => String(word(k) != null ? word(k) : k).replace(/\{(\w+)(?:\|([^|{}]*)\|([^|{}]*))?\}/g,   // {n|note|notes}: the word for that count
  (_, v, one, many) => (one != null ? (vars && +vars[v] === 1 ? one : many) : vars && vars[v] != null ? vars[v] : ""));
const fmt = (x) => { if (x == null || isNaN(x)) return "–"; x = Math.max(0, +x); const m = Math.floor(x / 60), s = x - m * 60; return `${m}:${s.toFixed(1).padStart(4, "0")}`; };
const pad = (n) => String(n).padStart(2, "0");
const tcode = (x, fps) => { const f = Math.floor(Math.max(0, x || 0) * fps + 0.01), s = Math.floor(f / fps); return `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}:${pad(f % fps)}`; };
const enc = encodeURIComponent;
const isVideo = (p) => /\.(mp4|webm|mov|m4v)$/i.test(p || ""), isImage = (p) => /\.(png|jpe?g|gif|webp|svg|avif)$/i.test(p || "");
const cut = (s, n) => (String(s).length > n ? String(s).slice(0, n) + "…" : String(s));
const COLON = () => (LANG === "zh" ? "：" : ": ");
const reduced = () => window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

/* what a note can be made against: tools/desk/feedback.py's validate refuses a whole submission for one item it cannot take,
   so the page makes only targets and labels it takes, and drops (and says) any other before sending */
const TARGET_RE = /^(dec|least|deleg|concept|seg|cap|shot|fact|time|atime|led|doc|asset|range|chapter|card):([^\x00-\x1f\x7f]+)$/;
const cps = (s) => Array.from(String(s));   // code points, as Python counts them
function targetOk(tg) {
  const m = typeof tg === "string" ? tg.match(TARGET_RE) : null;
  if (!m || cps(m[2]).length > 180) return false;
  const kind = m[1], rest = m[2];
  if (kind === "range") {   // seconds, ASCII digits, a < b as kept (to the hundredth)
    const m = tg.match(/^range:([0-9]+(?:\.[0-9]+)?)-([0-9]+(?:\.[0-9]+)?)$/), r2 = (x) => Math.round(+x * 100) / 100;
    return !!m && r2(m[1]) < r2(m[2]) && r2(m[2]) < 1e6;
  }
  if (kind === "asset") return rest === rest.trim() && !/^[/~\\]/.test(rest) && !/^[A-Za-z][A-Za-z0-9+.-]*:/.test(rest) && !rest.split(/[/\\]/).map((x) => x.trim()).includes("..");
  return true;
}
function fitTarget(tg) {   // a target feedback.py takes, or "": control characters out; a long name cut (an asset's path or a span never is)
  const s = String(tg == null ? "" : tg).replace(/[\x00-\x1f\x7f]+/g, " "), i = s.indexOf(":");
  if (i < 1) return "";
  const kind = s.slice(0, i), rest = s.slice(i + 1).trim(), keep = kind === "asset" || kind === "range" ? rest : cps(rest).slice(0, 180).join("").trim();
  return targetOk(kind + ":" + keep) ? kind + ":" + keep : "";
}
const fitLabel = (s) => { const c = cps(String(s == null ? "" : s).replace(/[\x00-\x08\x0b-\x1f\x7f]/g, "")); return c.length > 200 ? c.slice(0, 199).join("") + "…" : c.join(""); };

/* a submission goes once. Each is its own feedback file and its own section of REVIEW.md, so what the server took leaves the
   draft (counted in fb.sent), and a decision already sent goes again only when it is picked differently */
function toSend(decs, picked, sent, open) {   // {decisions, defaulted}: this round's decisions not sent yet, or changed since
  const decisions = {}, defaulted = [], P = picked || {}, S = sent || {};
  (open ? decs || [] : []).forEach((d) => {
    const v = P[d.id] || d.recommend;
    if (!v || !(d.options || []).some((o) => (o && o.id != null ? o.id : o) === v) || S[d.id] === v) return;
    decisions[d.id] = v; if (!P[d.id]) defaulted.push(d.id);
  });
  return { decisions, defaulted };
}
function afterSent(fb, p, at) {   // the draft once the server has taken p: its notes out (one reworded since stays), its decisions remembered
  const items = Object.assign({}, fb.items), was = fb.sent || { n: 0, d: 0 };
  (p.items || []).forEach((i) => { const v = items[i.target]; if (v && (v.text || "") === (i.text || "") && v.status === i.status) delete items[i.target]; });
  const general = fb.general && !String(p.general || "").includes(fb.general.trim()) ? fb.general : "";
  return Object.assign({}, fb, { items, general, submittedAt: at, sentDec: Object.assign({}, fb.sentDec, p.decisions),
    sent: { at, n: was.n + (p.items || []).length + (p.general ? 1 : 0), d: was.d + Object.keys(p.decisions || {}).length } });
}

/* bin/vh status speaks English to the agent. A Chinese page says its known lines in Chinese; one it does not know stays as
   status wrote it (the page says whose words they are). The project's own folder is written <项目> / <project> */
const ZH_MISSING = { "the person's words (原话) in REVIEW.md": "REVIEW.md 里人的原话", "the concept row in DECISIONS.md": "DECISIONS.md 里立意那一行" };
const STATUS_ZH = [
  [/^(.+?) is running \(bin\/vh activity [^)]*\); when it ends: ([\s\S]*)$/, (m, f) => `${m[1]} 正在跑；跑完以后：${f(m[2])}`],
  [/^the submission was handed over; REVIEW\.md has no decision for it yet$/, () => "反馈已经交给 agent，REVIEW.md 里还没写这一关定了什么"],
  [/^(\d+) submission\(s\) not handed to the agent yet \(bin\/vh desk feedback\)$/, (m) => `${m[1]} 份反馈还没交给 agent（bin/vh desk feedback）`],
  [/^this round moved on to (.+?); REVIEW\.md has no decision for (.+)$/, (m) => `这一轮已经换到 ${m[1]}，REVIEW.md 里没有 ${m[2]} 的决定`],
  [/^waived in the user's words \(([\s\S]*)\)$/, (m) => `用户说了不用审（${m[1]}）`],
  [/^Effort quick: no gates$/, () => "quick 档：不设关卡"],
  [/^decided, but the person's words are not in REVIEW\.md$/, () => "定了，但 REVIEW.md 里没有人的原话"],
  [/^decided, but without (.+?): bin\/vh render and check refuse the whole film$/, (m) => `定了，但还缺 ${m[1].split(" and ").map((x) => ZH_MISSING[x] || x).join("、")}：bin/vh render 和 check 不放整片`],
  [/^decided, but without (.+?): bin\/vh gate does not send gate ③'s page, and bin\/vh check fails the film$/, (m) => `定了，但还缺 ${m[1].split(" and ").map((x) => ZH_MISSING[x] || x).join("、")}：bin/vh gate 不发关卡 ③ 的页，bin/vh check 也不放这支片子`],
  [/^decided in its REVIEW\.md section, read by date: [\s\S]*$/, () => "定了：按日期认出的 REVIEW.md 小节（那一节没写页面）"],
  [/^its REVIEW\.md section has a decision, but names no page and is older than the page: not counted \(its 页面 line: (.+)\)$/, (m) => `REVIEW.md 那一节有决定，但没写页面、又比这一页旧，不算（页面一行该写 ${m[1]}）`],
  [/^bin\/vh gate refused this page, so that run sent the person nothing: fix it and send it again$/, () => "bin/vh gate 没发这一页，人什么也没收到：改好再发"],
  [/^the person reviews (.+?) on (?:the desk (\S+)|the chat|(.+?)): stop here, and write their words into REVIEW\.md when they answer$/,
    (m) => `等人看 ${m[1]}${m[2] ? "（审阅台）" : m[3] ? `（${m[3]}）` : "（在对话里）"}：停在这里，人回了以后把原话写进 REVIEW.md`],
  [/^read the person's submission for (.+?), then write what was decided into REVIEW\.md$/, (m) => `读人对 ${m[1]} 交的反馈，把定下的写进 REVIEW.md`],
  [/^write what was decided and changed under the desk's section for (.+?) in REVIEW\.md \(定了 \/ 改了\)$/, (m) => `在 REVIEW.md 里 ${m[1]} 那一节写下定了什么、改了什么`],
  [/^record the decision for (.+?) in REVIEW\.md$/, (m) => `把 ${m[1]} 的决定记进 REVIEW.md`],
  [/^paused \(REVIEW\.md\): the person resumes it$/, () => "暂停中（REVIEW.md）：等人恢复"],
  [/^delivered: what this film taught goes into LESSONS\.md$/, () => "已交付：这支片子学到的写进 LESSONS.md"],
  [/^carry on$/, () => "接着做"],
  [/^the engine's scaffold is not there: this makes it$/, () => "引擎的脚手架还没有：下面这条命令搭起来"],
  [/^check (.+?) and look at its contact sheet$/, (m) => `检查 ${m[1]}，看它的联系表`],
  [/^fix what bin\/vh check failed on (\S+)(?:: ([\s\S]*))?$/, (m) => `修 bin/vh check 在 ${m[1]} 上没过的地方${m[2] ? "：" + m[2] : ""}`],
  [/^render the final at delivery quality$/, () => "按交付画质渲染成片"],
  [/^bin\/vh gate refused the page for (.+?), so the person got nothing: fix it \(([\s\S]*)\), then send it again$/, (m) => `bin/vh gate 没发 ${m[1]} 的页，人什么也没收到：先修（${m[2]}），再发一次`],
];
function stepPoint(shots, x, dir, dur) {   // ← → in the cut, from second x: {shot, t} the next or previous shot's start, else {t}
  const S = (shots || []).filter((s) => s && isFinite(+s.t0)).slice().sort((a, b) => a.t0 - b.t0);
  if (!S.length) return { t: x + dir * 5 };
  const P = [0].concat(S.map((s) => +s.t0), [+S[S.length - 1].t1]).filter((p) => isFinite(p)).sort((a, b) => a - b);
  const n = dir > 0 ? P.find((p) => p > x + 0.05) : P.slice().reverse().find((p) => p < x - 0.3);   // back: this shot's start first
  if (n == null) return { t: dir > 0 ? dur : 0 };
  const at = S.find((s) => Math.abs(s.t0 - n) < 0.01);
  return at ? { shot: at.id, t: +at.t0 } : { t: n };
}
function shortPath(s) {   // the project's own folder as <项目>: a command stays short, and says which folder goes there
  const p = (typeof D !== "undefined" && D && D.status && D.status.project && D.status.project.path) || "";
  return p && p.length > 1 ? String(s == null ? "" : s).split(p).join(t("proj_ph")) : String(s == null ? "" : s);
}
function statusWords(s) {   // {text, known}: one of bin/vh status's lines in this page's language, when the page knows it
  const x = shortPath(s).trim();
  if (!x || LANG !== "zh") return { text: x, known: true };
  const one = (y) => { for (const [re, f] of STATUS_ZH) { const m = y.match(re); if (m) return f(m, (z) => statusWords(z).text); } return null; };
  const whole = one(x); if (whole != null) return { text: whole, known: true };
  const parts = x.split("; ").map((y) => one(y));   // notes joined by "; "
  return parts.length > 1 && parts.every((y) => y != null) ? { text: parts.join("；"), known: true } : { text: x, known: false };
}

const SUBS = { outline: ["outline", "script", "facts"], ship: ["deliver", "check", "versions"], ledger: ["decisions", "history", "docs"] };
const FLOW = [   // the flow bar: a fixed six, each the film's stops that belong to it
  { mod: "idea", st: ["1", "E0"] }, { mod: "outline", st: ["1", "E1"] }, { mod: "board", st: ["2"] },
  { mod: "sound", st: ["E2", "E3"] }, { mod: "cut", st: ["3", "E4", "E5"] }, { mod: "ship", st: ["deliver"] }];
const GATE_MOD = { "1": "idea", E0: "idea", E1: "outline", "2": "board", E2: "sound", E3: "sound", "3": "cut", E4: "cut", E5: "cut", deliver: "ship" };
const gateBase = (g) => { const m = String(g || "").match(/^(\d|E\d)/); return m ? m[1] : ""; };
const gateMod = (g) => GATE_MOD[gateBase(g)] || "idea";
const projHash = (key, rest) => `#/p/${enc(key)}${rest ? "/" + rest : ""}`;

function stations() { return (D && D.status && D.status.stations) || []; }
function flowState(f) {   // a flow item's lamp: from the film's own stops; none of them in the plan: not a stop
  const S = stations().filter((s) => f.st.includes(s.id));
  if (!S.length) return { state: "off", S };
  if (S.some((s) => s.state === "waiting_person")) return { state: "wait", S };
  if (S.some((s) => s.state === "waiting_agent" || s.state === "in_progress")) return { state: "agent", S };
  if (S.every((s) => s.state === "skipped")) return { state: "skip", S };
  if (S.every((s) => s.state === "done" || s.state === "skipped")) return { state: "done", S };
  if (S.some((s) => s.state === "no_record")) return { state: "norec", S };
  return { state: "todo", S };
}
function glyphOf(S) {
  const g = S.find((s) => /^\d$/.test(s.id));
  if (g) return "①②③④⑤"[+g.id - 1];
  const e = S.find((s) => /^E\d$/.test(s.id));
  return e ? e.id : "";
}
const STATE_WORD = { done: "f_done", wait: "f_wait", agent: "f_agent", todo: "f_todo", skip: "f_skip", off: "f_off", norec: "f_norec" };
function kickOf(mod) {
  const f = FLOW.find((x) => x.mod === mod); if (!f) return t("m_" + mod);
  const fs = flowState(f), g = fs.state === "off" ? "" : glyphOf(fs.S);
  return `${t("m_" + mod)}${g ? " " + g : ""} · ${t(STATE_WORD[fs.state])}`;
}
function subtabs(mod) {
  const S = SUBS[mod]; if (!S) return "";
  const cur = SUB && S.includes(SUB) ? SUB : S[0];
  return `<nav class="subtabs" role="tablist">${S.map((s) => `<a href="${projHash(PKEY, mod + "/" + s)}" role="tab" aria-selected="${s === cur}">${esc(t("sub_" + s))}</a>`).join("")}</nav>`;
}
const docOf = (f) => D.docs.find((d) => d.file === f);
function docHtml(doc, onlySection) {
  if (!doc) return "";
  const secs = onlySection ? doc.sections.filter((s) => onlySection.test(s.title)) : doc.sections;
  return `<div class="md">${onlySection ? "" : doc.intro}${secs.map((s) => `<h2>${esc(s.title)}</h2>${s.html}`).join("")}</div>`;
}
const specGet = (k) => (D.spec.find((s) => s.k.toLowerCase().startsWith(k)) || {}).v || "";
function TL() { return (D.studio && D.studio.timeline) || {}; }
