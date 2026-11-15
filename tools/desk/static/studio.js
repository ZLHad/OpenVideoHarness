"use strict";
/* The console (bin/vh desk): Studio without the agent connected (docs/proposals/02-studio-client.md, 2–4). The shell is the
   module rail, the flow bar of the film's stops and the right column (what waits for you, this round's notes and its one
   submission, a box that writes a note against what is selected). The space lists every film; a film opens on the module of
   the stop that waits (gate ① 立意, ② 分镜, ③ 成片). The cut module lays the film, its shots, narration, music, checks and
   notes out on one timeline. It reads the server's JSON (tools/desk/server.py: the project files and bin/vh, read fresh) and
   the gate view's markup (tools/review.py; ui.js mounts it). The reviewer's draft stays in this browser (localStorage) until it
   goes to /api/p/<key>/feedback, the desk's one submission channel. No framework, no CDN. Every text from a project is escaped
   before it reaches the page (documents arrive as HTML that reader.py has already escaped). */

const STR = {
  zh: {
    brand: "片场", noServer: "读不到数据：请用 bin/vh desk 打开这一页。", loading: "…", gate: "关卡",
    m_space: "空间", m_idea: "立意", m_outline: "大纲", m_board: "分镜", m_sound: "声音", m_cut: "成片", m_ship: "交付", m_assets: "素材", m_ledger: "账本",
    f_done: "过了", f_wait: "等你", f_agent: "agent 在做", f_todo: "还没到", f_skip: "跳过", f_off: "这支片子这一站不停", f_norec: "没有审阅记录",
    pick_film: "先在空间里选一支片子", search: "搜片子", search_ph: "片名、文件夹或类型，回车打开", no_match: "没有对上的片子", lang: "EN", lang_tip: "Switch to English", themes: "主题",
    th_darkfield: "暗场", th_prism: "棱镜", th_bridge: "舰桥", skip: "跳到内容", rail: "模块", flow: "这支片子的几站",
    ask_kick: "从一句话开始", ask_h: "你想做一支什么样的片子？", ask_ph: "比如：做一支一分钟的科普，讲海水为什么一天涨两次",
    ask_note: "这一版控制台不连 agent：写好这一句，复制到你的 agent 对话里，它会建项目、往下做。", ask_copy: "复制给 agent", ask_copied: "复制好了：粘贴到你的 agent 对话里",
    ask_prefix: "用 OpenVideoHarness 做一支片子：", ask_empty: "先写一句",
    films: "片子", home_meta: "{n} 支 · {w} 支等你", home_meta0: "{n} 支", g_wait: "等你看的", g_rest: "其余", roots: "从这些文件夹里找的：{r}",
    no_projects: "这里还没有片子。bin/vh new 建一个，或者 bin/vh desk --root <文件夹> 告诉我去哪找。",
    st_waiting_person: "等你看", st_waiting_agent: "agent 在做", st_in_progress: "进行中", st_delivered: "已交付", st_paused: "暂停",
    st_no_record: "没有审阅记录", st_not_started: "还没开始", st_skipped: "跳过", st_done: "过了",
    ask_n: "要你定 {n} 件：{q}", ask_0: "看一眼：{q}", just_now: "刚才", ago_m: "{n} 分钟前", ago_h: "{n} 小时前", ago_d: "{n} 天前",
    col_space: "空间", col_space_note: "选一支片子：点评和决定都记在那支片子里。", waiting_list: "等你看的", agent_list: "agent 在做的", none_waiting: "没有片子在等你。",
    col_round: "这一轮", col_notes: "随手点评", live_on: "agent 在等", live_off: "agent 没在等",
    live_on_tip: "提交后 agent 会自动接着做，不用回对话", live_off_tip: "提交后回到对话里说一声“看审阅台”",
    c_decide: "要你定", c_rec: "没动的按推荐", c_least: "它最没把握的", c_listen: "请你听", c_mine: "我的点评", c_next: "下一步", c_running: "正在跑", c_spend: "花费",
    c_spent: "已花 {s}", c_of: "预算 {l}", c_none_mine: "还没有。选中一处（一秒、一段、一个镜头），在下面写一句。", who_agent: "agent", who_person: "你", who_nobody: "交付了",
    round_sum: "{n} 条点评 · {d} 个决定", submit_round: "提交这一轮", c_whole_note: "整体", round_quiet: "{g} · {s}：现在没有要你定的事。",
    at: "对着", whole: "整个{m}", whole_film: "整片", to_whole: "换成整个模块", say_agent: "说给 agent", say_agent_tip: "这一版控制台不连 agent：写成点评，提交这一轮时交给它",
    as_note: "记成点评", c_ph: "对「{x}」说一句", note_add: "记下", note_keys: "⌘↩ 记下", noted: "记下了：{x}", del: "删",
    d_title: "提交这一轮", d_decisions: "决定", d_items: "点评", by_rec: "（按推荐）", d_none: "没有逐条点评；没标的都算通过。",
    general: "整体意见（可选）", general_ph: "比如：整体节奏偏慢；开场很好……", submit: "提交", cancel: "再看看", preview: "会提交的内容",
    submit_hint: "提交后写进项目的 out/review/feedback/，你的原话同时抄进 REVIEW.md。没动的决定按推荐算。",
    sent_live: "已提交，agent 已经在接着做", sent: "已提交：{f}",
    hint_live: "已写进 {f}，原话也抄进了 REVIEW.md。agent 在等这份反馈，已经自动接着做了，不用再回对话。",
    hint_idle: "已写进 {f}，原话也抄进了 REVIEW.md。agent 这会儿没在等：回到对话里说一声“看审阅台”。",
    offline: "没有连上本地服务：回复已复制，粘贴到对话里即可", offline2: "没有连上本地服务：请复制下面的内容", refused: "没有提交成功：{e}",
    reply_head: "《{p}》{r} 的回复", rest: "其余没标的都算通过。", round_name: "关卡 {r}", notes_round: "随手点评", overall: "整体",
    submitted: "这一轮已经提交过（{at}）。再提交会另存一份，REVIEW.md 里也会多一节。", new_round: "agent 发来了新的一页：{g}",
    past: "这是之前的一页（{g}），看看就好。", to_round: "回到这一轮 →", page_of: "看{g}那一页 →", st_ok: "可以", st_change: "要改", st_ask: "疑问",
    say: "说一句", fb_ok: "✓ 可以", fb_change: "✎ 要改", fb_ask: "? 疑问", fb_def: "不点就算通过", ph_change: "哪里要改、为什么", ph_ask: "哪里没看懂？",
    ph_suggest: "直接改成……（可选）", agree: "✓ 同意", overturn: "✎ 翻案", def_agree: "不点就算同意",
    fact_ok: "✓ 对", fact_bad: "✎ 有问题", fact_unsure: "? 拿不准", fact_def: "不点 = 没看",
    l_least: "没把握：{x}", l_deleg: "我替你定的：{x}", l_dec: "决定：{x}", l_shot: "镜头 {x}", l_seg: "大纲 第 {i} 段 {x}", l_line: "旁白 {x}",
    film_label: "成片 {t}", range_label: "成片 {a}–{b}", sound_label: "声音 {t}", chapter_label: "章节 {x}",
    // the cut module
    l_shots: "镜头", l_script: "旁白稿", l_captions: "字幕", l_notes: "点评", l_checks: "检查",
    no_shots: "还没有镜头表。shots.json 写好后（或 bin/vh storyboard），镜头就排在这里。", no_narr: "还没有旁白的时间。bin/vh tts 出了配音，旁白稿和词的时间就到这里。",
    no_checks: "还没跑检查：bin/vh check <片子>。", check_stale: "片子在这次检查之后改过：再跑一次 bin/vh check", verdict: "结论",
    n_notes: "{n} 条点评", unsure: "没把握", n_checks: "{n} 处检查", reads: "要看懂", ver_n: "第 {n} 版", proxy: "代理",
    no_film: "还没有成片：bin/vh render 之后在这里播。现在是分镜的关键帧。", no_film0: "还没有成片，也没有分镜的关键帧。",
    safe: "安全框", compare: "和{v}对比", ver_now: "{v} · 现在", lay_review: "审片", lay_fine: "精修", lay_sound: "听声音", layout: "布局",
    tl_hint: "点一下选这一秒，拖一段选区间，点镜头或章节选中它 · I/O 入点出点 · 空格播放 · ←→ 逐镜 · N 下一处",
    next_place: "下一处要看的", snap: "吸附", zoom_in: "放大", zoom_out: "缩小", play: "播放 / 暂停（空格）", prev_shot: "上一个镜头（←）", next_shot: "下一个镜头（→）",
    g_pic: "画面", g_sound: "声音", g_review: "审阅", ln_chap: "章节", ln_shots: "镜头", ln_voice: "旁白", ln_music: "音乐", ln_hits: "卡点", ln_wave: "波形", ln_marks: "点评·检查", ln_diff: "这一版改了",
    e_chap: "没有章节，大纲也没写时间", e_shots: "没有镜头表 · shots.json", e_voice: "没有旁白的时间 · bin/vh tts", e_music: "没有配乐的段落和节拍 · bin/vh beats", e_wave: "没有波形 · bin/vh peaks <项目>",
    e_hits: "没有卡点", e_diff: "这一版没有记下改了哪里（bin/vh patch 才记）", e_marks: "这里还没有点评和检查", whole_render: "整支重渲",
    diff_label: "{v} 改了这里", next_q: "下一处 · {x}", no_next: "后面没有要看的了", k_least: "没把握", k_listen: "请你听", k_check: "检查", k_mine: "我",
    sev_fail: "没过", sev_warn: "注意", no_thumbs: "bin/vh thumbs <项目> 做了缩略图，拖动时就能看到每一秒的画面",
    // the other modules (the desk's views, moved in)
    sub_outline: "大纲", sub_script: "字幕 / 旁白", sub_facts: "事实", sub_check: "检查", sub_versions: "版本", sub_decisions: "决定", sub_history: "历史", sub_docs: "文档",
    concept: "立意", spine: "故事线", motif: "贯穿全片的", end: "看完以后", spec: "规格", outline: "大纲", outline_tip: "点色块跳到那一段",
    seg_n: "第 {i} 段", know: "看完知道 / 感到", visual: "关键画面", seg_caps: "这一段的 {n} 条", bars: "第 {b} 小节",
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
    idea_none: "这支片子还没有立意卡。", ship_none: "交付的东西（标题、封面、多平台文案）在 bin/vh deliver 之后出现在这里。",
    stn: { "1": "立意", "2": "分镜", "3": "初版", E0: "样帧", E1: "脚本", E2: "声音", E3: "锁时", E4: "样板章", E5: "锁画面", deliver: "交付" },
  },
  en: {
    brand: "Studio", noServer: "Can't read the data: open this page with bin/vh desk.", loading: "…", gate: "Gate",
    m_space: "Space", m_idea: "Concept", m_outline: "Outline", m_board: "Storyboard", m_sound: "Sound", m_cut: "Cut", m_ship: "Delivery", m_assets: "Material", m_ledger: "Ledger",
    f_done: "passed", f_wait: "waiting for you", f_agent: "agent at work", f_todo: "not yet", f_skip: "skipped", f_off: "not a stop in this film", f_norec: "no review record",
    pick_film: "Pick a film in the space first", search: "Find a film", search_ph: "Title, folder or type; Enter opens it", no_match: "No film matches", lang: "中", lang_tip: "切换到中文", themes: "Theme",
    th_darkfield: "Darkfield", th_prism: "Prism", th_bridge: "Bridge", skip: "Skip to content", rail: "Modules", flow: "This film's stops",
    ask_kick: "Start from a sentence", ask_h: "What film do you want to make?", ask_ph: "e.g. a one-minute explainer on why the tide comes in twice a day",
    ask_note: "This console doesn't talk to an agent yet: write the sentence, paste it into your agent's chat, and it sets the project up and carries on.", ask_copy: "Copy for the agent",
    ask_copied: "Copied: paste it into your agent's chat", ask_prefix: "Make a film with OpenVideoHarness: ", ask_empty: "Write a sentence first",
    films: "Films", home_meta: "{n} · {w} waiting for you", home_meta0: "{n}", g_wait: "Waiting for you", g_rest: "The rest", roots: "Found under: {r}",
    no_projects: "No films here yet. Make one with bin/vh new, or tell me where to look: bin/vh desk --root <folder>.",
    st_waiting_person: "waiting for you", st_waiting_agent: "the agent is on it", st_in_progress: "in progress", st_delivered: "delivered",
    st_paused: "paused", st_no_record: "no review record", st_not_started: "not started", st_skipped: "skipped", st_done: "passed",
    ask_n: "{n} to decide: {q}", ask_0: "To look at: {q}", just_now: "just now", ago_m: "{n} min ago", ago_h: "{n} h ago", ago_d: "{n} days ago",
    col_space: "Space", col_space_note: "Pick a film: notes and decisions go into that film.", waiting_list: "Waiting for you", agent_list: "The agent is on", none_waiting: "No film is waiting for you.",
    col_round: "This round", col_notes: "Notes", live_on: "the agent is waiting", live_off: "the agent isn't waiting",
    live_on_tip: "Submit and the agent carries on by itself; no need to go back to the chat", live_off_tip: "After submitting, tell the agent in the chat: “check the desk”",
    c_decide: "To decide", c_rec: "untouched = recommended", c_least: "Least sure", c_listen: "Listen to", c_mine: "My notes", c_next: "Next", c_running: "Running", c_spend: "Spent",
    c_spent: "{s} spent", c_of: "of {l}", c_none_mine: "None yet. Select a place (a second, a span, a shot) and write a line below.", who_agent: "agent", who_person: "you", who_nobody: "delivered",
    round_sum: "{n} notes · {d} decisions", submit_round: "Submit this round", c_whole_note: "Overall", round_quiet: "{g} · {s}: nothing waits for you to decide now.",
    at: "On", whole: "the whole {m}", whole_film: "the whole film", to_whole: "the whole module", say_agent: "Tell the agent", say_agent_tip: "This console doesn't talk to the agent yet: write a note, and it goes with this round",
    as_note: "Note it", c_ph: "A line on “{x}”", note_add: "Add", note_keys: "⌘↩ adds", noted: "Noted: {x}", del: "Delete",
    d_title: "Submit this round", d_decisions: "Decisions", d_items: "Notes", by_rec: " (recommended)", d_none: "No item notes; anything not marked passes.",
    general: "Overall (optional)", general_ph: "e.g. the pace drags overall; the opening works…", submit: "Submit", cancel: "Keep looking", preview: "What will be submitted",
    submit_hint: "Submissions go to the project's out/review/feedback/, and your words into REVIEW.md. Untouched decisions go by the recommendation.",
    sent_live: "Submitted; the agent is on it", sent: "Submitted: {f}",
    hint_live: "Saved to {f}; your words are in REVIEW.md too. The agent was waiting for this and has carried on; no need to go back to the chat.",
    hint_idle: "Saved to {f}; your words are in REVIEW.md too. The agent isn't waiting right now: tell it in the chat, “check the desk”.",
    offline: "Couldn't reach the local server: the reply is copied, paste it into the chat", offline2: "Couldn't reach the local server: copy the text below", refused: "Not submitted: {e}",
    reply_head: "Reply to {r} of “{p}”", rest: "Everything not marked passes.", round_name: "gate {r}", notes_round: "notes", overall: "Overall",
    submitted: "Already submitted this round ({at}). Submitting again saves another copy and adds another section to REVIEW.md.", new_round: "The agent sent a new page: {g}",
    past: "An earlier page ({g}), to look at only.", to_round: "Back to this round →", page_of: "See the page of {g} →", st_ok: "ok", st_change: "change", st_ask: "question",
    say: "Say something", fb_ok: "✓ OK", fb_change: "✎ Change", fb_ask: "? Question", fb_def: "untouched = approved", ph_change: "What to change, and why", ph_ask: "What's unclear?",
    ph_suggest: "Change it to… (optional)", agree: "✓ Agree", overturn: "✎ Overturn", def_agree: "untouched = agreed",
    fact_ok: "✓ Right", fact_bad: "✎ Wrong", fact_unsure: "? Not sure", fact_def: "untouched = not checked",
    l_least: "Unsure: {x}", l_deleg: "Decided for you: {x}", l_dec: "Decision: {x}", l_shot: "Shot {x}", l_seg: "Outline part {i} {x}", l_line: "Narration {x}",
    film_label: "Film {t}", range_label: "Film {a}–{b}", sound_label: "Sound {t}", chapter_label: "Chapter {x}",
    l_shots: "Shots", l_script: "Narration", l_captions: "Captions", l_notes: "Notes", l_checks: "Checks",
    no_shots: "No shot table yet. Once shots.json is written (or bin/vh storyboard), the shots line up here.", no_narr: "No narration timing yet. Once bin/vh tts has voiced it, the lines and their times come here.",
    no_checks: "No check yet: bin/vh check <film>.", check_stale: "The film changed after this check: run bin/vh check again", verdict: "Verdict",
    n_notes: "{n} notes", unsure: "unsure", n_checks: "{n} checks", reads: "Reads", ver_n: "v{n}", proxy: "proxy",
    no_film: "No film yet: it plays here after bin/vh render. These are the storyboard's key frames.", no_film0: "No film yet, and no storyboard key frames.",
    safe: "Safe area", compare: "Compare with {v}", ver_now: "{v} · now", lay_review: "Review", lay_fine: "Fine cut", lay_sound: "Listen", layout: "Layout",
    tl_hint: "Click a second, drag a span, click a shot or chapter to select it · I/O in and out · Space plays · ←→ shot by shot · N next place",
    next_place: "Next place", snap: "Snap", zoom_in: "Zoom in", zoom_out: "Zoom out", play: "Play / pause (Space)", prev_shot: "Previous shot (←)", next_shot: "Next shot (→)",
    g_pic: "Picture", g_sound: "Sound", g_review: "Review", ln_chap: "Chapters", ln_shots: "Shots", ln_voice: "Voice", ln_music: "Music", ln_hits: "Hits", ln_wave: "Waveform", ln_marks: "Notes · checks", ln_diff: "Changed",
    e_chap: "No chapters, and the outline has no times", e_shots: "No shot table · shots.json", e_voice: "No narration timing · bin/vh tts", e_music: "No music sections or beats · bin/vh beats", e_wave: "No waveform · bin/vh peaks <project>",
    e_hits: "No hits", e_diff: "This version doesn't record what changed (bin/vh patch does)", e_marks: "No notes or checks here yet", whole_render: "re-rendered whole",
    diff_label: "{v} changed this", next_q: "Next · {x}", no_next: "Nothing more after here", k_least: "unsure", k_listen: "listen", k_check: "check", k_mine: "me",
    sev_fail: "failed", sev_warn: "warning", no_thumbs: "bin/vh thumbs <project> makes thumbnails: then dragging shows every second",
    sub_outline: "Outline", sub_script: "Captions / narration", sub_facts: "Facts", sub_check: "Check", sub_versions: "Versions", sub_decisions: "Decisions", sub_history: "History", sub_docs: "Documents",
    concept: "Concept", spine: "Spine", motif: "Recurring motif", end: "At the end", spec: "Spec", outline: "Outline", outline_tip: "click a block to jump to it",
    seg_n: "Part {i}", know: "The viewer knows / feels", visual: "Key visual", seg_caps: "{n} lines in this part", bars: "bars {b}",
    no_outline: "The outline isn't a table yet (BRIEF's Outline section; columns in tools/desk/README.md). Here is the BRIEF as written.", no_brief: "No BRIEF.md yet.",
    script_sub: "{n} lines by outline part. Reading speed, roughly, from each line's span: Chinese up to {g} chars/s green, {y} yellow; English {eg} / {ey}.",
    f_all: "All", f_mine: "Marked by me", f_terms: "With a term", f_facts: "With a source #", f_fast: "Maybe too fast",
    no_script: "SCRIPT.md has no caption or narration table (columns in tools/desk/README.md). Here it is as written.", no_script_file: "No captions or narration yet (SCRIPT.md).",
    other_seg: "Not matched to the outline", per_s: "/s", chars: "{n} chars · {s} s", none_match: "Nothing matches.", l_cap: "Caption {x}", l_vo: "Narration {x}", term: "Term",
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
    idea_none: "No concept cards for this film yet.", ship_none: "What gets delivered (titles, covers, copy for each platform) shows up here after bin/vh deliver.",
    stn: { "1": "Concept", "2": "Storyboard", "3": "Draft", E0: "Style frames", E1: "Script", E2: "Sound", E3: "Timing lock", E4: "Sample chapter", E5: "Picture lock", deliver: "Delivery" },
  },
};

const TOKEN = (document.querySelector('meta[name="desk-token"]') || {}).content || "";
const HOME = (document.querySelector('meta[name="desk-home"]') || {}).content || "";
const $ = (s, el = document) => el.querySelector(s), $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let LANG = "zh", L = STR.zh;
const t = (k, vars) => String(L[k] != null ? L[k] : STR.en[k] != null ? STR.en[k] : k).replace(/\{(\w+)\}/g, (_, v) => (vars && vars[v] != null ? vars[v] : ""));
const fmt = (x) => { if (x == null || isNaN(x)) return "–"; x = Math.max(0, +x); const m = Math.floor(x / 60), s = x - m * 60; return `${m}:${s.toFixed(1).padStart(4, "0")}`; };
const pad = (n) => String(n).padStart(2, "0");
const tcode = (x, fps) => { const f = Math.floor(Math.max(0, x || 0) * fps + 0.01), s = Math.floor(f / fps); return `${pad(Math.floor(s / 3600))}:${pad(Math.floor(s / 60) % 60)}:${pad(s % 60)}:${pad(f % fps)}`; };
const enc = encodeURIComponent;
const isVideo = (p) => /\.(mp4|webm|mov|m4v)$/i.test(p || ""), isImage = (p) => /\.(png|jpe?g|gif|webp|svg|avif)$/i.test(p || "");
const cut = (s, n) => (String(s).length > n ? String(s).slice(0, n) + "…" : String(s));
const COLON = () => (LANG === "zh" ? "：" : ": ");
const reduced = () => window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* a private window: the draft just isn't kept */ } },
};
function toast(m) { const el = $("#toast"); el.textContent = m; el.classList.add("show"); clearTimeout(el._h); el._h = setTimeout(() => el.classList.remove("show"), 3200); }
async function getJSON(url) {
  try { const r = await fetch(url, { cache: "no-store" }); const j = await r.json().catch(() => null); return { ok: r.ok, status: r.status, data: j }; }
  catch (e) { return { ok: false, status: 0, data: null }; }
}
const typing = () => { const a = document.activeElement; return !!a && (/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) && a.type !== "radio" || a.isContentEditable); };

/* ---------- state ---------- */
let LIST = null, D = null, PKEY = "", ROUND = null, FB = null, KEY = "", GV = null;   // GV: this round's gate view (decisions, marks)
let MOD = "", SUB = "", DOC = "", GATE = "", SCOPE = null, capFilter = "all";
let COLCTL = null, PARTCTL = null, CUT = null, liveTimer = null, homeTimer = null, LAST = store.get("desk:last") || "";
const src = (p) => (/^https?:\/\//.test(p || "") ? p : `/f/${enc(PKEY)}/` + String(p || "").split("/").map(enc).join("/"));
const MODS = ["idea", "outline", "board", "sound", "cut", "ship", "assets", "ledger"];
const SUBS = { outline: ["outline", "script", "facts"], ship: ["check", "versions"], ledger: ["decisions", "history", "docs"] };
const FLOW = [   // the flow bar: a fixed six, each the film's stops that belong to it
  { mod: "idea", st: ["1", "E0"] }, { mod: "outline", st: ["1", "E1"] }, { mod: "board", st: ["2"] },
  { mod: "sound", st: ["E2", "E3"] }, { mod: "cut", st: ["3", "E4", "E5"] }, { mod: "ship", st: ["deliver"] }];
const GATE_MOD = { "1": "idea", E0: "idea", E1: "outline", "2": "board", E2: "sound", E3: "sound", "3": "cut", E4: "cut", E5: "cut", deliver: "ship" };
const gateBase = (g) => { const m = String(g || "").match(/^(\d|E\d)/); return m ? m[1] : ""; };
const gateMod = (g) => GATE_MOD[gateBase(g)] || "idea";
const LEGACY = { round: "", concept: "idea", script: "outline/script", board: "board", sound: "sound", facts: "outline/facts", film: "cut", check: "ship/check",
  versions: "ship/versions", assets: "assets", ledger: "ledger", history: "ledger/history", docs: "ledger/docs" };
const ICON = {
  space: '<path d="M4 11l8-6 8 6v8.5a.5.5 0 0 1-.5.5H15v-5H9v5H4.5a.5.5 0 0 1-.5-.5z"/>',
  idea: '<path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8"/>',
  outline: '<path d="M9 6h11M9 12h11M9 18h11"/><circle cx="4.5" cy="6" r=".8"/><circle cx="4.5" cy="12" r=".8"/><circle cx="4.5" cy="18" r=".8"/>',
  board: '<rect x="4" y="4" width="7" height="7" rx="1"/><rect x="13" y="4" width="7" height="7" rx="1"/><rect x="4" y="13" width="7" height="7" rx="1"/><rect x="13" y="13" width="7" height="7" rx="1"/>',
  sound: '<path d="M4 12h1.5M8 8v8M12 4.5v15M16 8.5v7M20 11v2"/>',
  cut: '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M8 4v16M16 4v16M4 9h4M4 15h4M16 9h4M16 15h4"/>',
  ship: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
  assets: '<path d="M3.5 7a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2z"/>',
  ledger: '<path d="M6 3h9l4 4v14H6z"/><path d="M9 11h7M9 15h7M9 7h3"/>',
  play: '<path d="M8 5v14l11-7z"/>', pause: '<path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z"/>', prev: '<path d="M6 5v14M18 5L9 12l9 7z"/>', next: '<path d="M18 5v14M6 5l9 7-9 7z"/>',
};
const svg = (k, cls) => `<svg viewBox="0 0 24 24" aria-hidden="true"${cls ? ` class="${cls}"` : ""}>${ICON[k]}</svg>`;

function setLang(l) {
  LANG = l === "en" ? "en" : "zh"; L = STR[LANG];
  document.documentElement.lang = LANG === "zh" ? "zh-CN" : "en";
  $("#lang").textContent = t("lang"); $("#lang").title = t("lang_tip");
  $("#searchLabel").textContent = t("search"); $("#q").placeholder = t("search_ph"); $("#skip").textContent = t("skip");
  $("#rail").setAttribute("aria-label", t("rail")); $("#flow").setAttribute("aria-label", t("flow")); $("#themes").setAttribute("aria-label", t("themes"));
  $$("#themes [data-theme-set]").forEach((b) => { b.textContent = t("th_" + b.dataset.themeSet); });
}
function pickLang(fallback) {
  let pick = null; try { pick = localStorage.getItem("desk:lang"); } catch (e) { /* no storage */ }
  return pick === "zh" || pick === "en" ? pick : fallback || (/^zh/i.test(navigator.language || "zh") ? "zh" : "en");
}

/* ---------- routes: #/ the space · #/p/<key>[/<module>[/<sub>[/<doc>]]] · #/p/<key>/gate/<id> ---------- */
function parse() {
  const h = decodeURIComponent(location.hash.replace(/^#/, ""));
  if (!h) return HOME ? { view: "project", key: HOME } : { view: "home" };
  if (h === "/") return { view: "home" };
  const m = h.match(/^\/p\/([^/]+)(?:\/(.*))?$/);
  if (m) {
    const rest = m[2] || "", g = rest.match(/^gate\/([A-Za-z0-9_-]{1,24})$/);
    if (g) return { view: "project", key: m[1], gate: g[1], mod: gateMod(g[1]) };
    let [mod, sub, ...more] = rest.split("/");
    if (LEGACY[mod] != null && !MODS.includes(mod)) { const x = LEGACY[mod].split("/"); return { view: "project", key: m[1], mod: x[0], sub: x[1] || "", doc: x[1] === "docs" ? [sub].concat(more).filter(Boolean).join("/") : "" }; }
    return { view: "project", key: m[1], mod: MODS.includes(mod) ? mod : "", sub: sub || "", doc: sub === "docs" ? more.join("/") : "" };
  }
  const [v, ...rest] = h.split("/");   // the single-project desk's first hashes: #concept, #film …
  if (HOME && LEGACY[v] != null) { const x = LEGACY[v].split("/"); return { view: "project", key: HOME, mod: x[0], sub: x[1] || "", doc: x[1] === "docs" ? rest.join("/") : "" }; }
  return HOME ? { view: "project", key: HOME } : { view: "home" };
}
const go = (h) => { if (location.hash !== h) location.hash = h; else route(); };
const projHash = (key, rest) => `#/p/${enc(key)}${rest ? "/" + rest : ""}`;
async function route() {
  const r = parse();
  closeSearch();
  if (r.view === "home") return showHome();
  return showProject(r);
}
window.addEventListener("hashchange", route);

/* ---------- the shell: crumbs, the flow bar, the rail ---------- */
function crumbs(parts) {
  $("#crumbs").innerHTML = parts.map((p, i) => `<span class="cr">${i ? '<span class="sep">/</span>' : ""}${p.href ? `<a href="${p.href}">${esc(p.text)}</a>` : `<b>${esc(p.text)}</b>`}</span>`).join("");
  document.title = (parts.length > 1 ? parts.slice(1).map((p) => p.text).reverse().join(" · ") : parts[0].text) + " · " + t("brand");
}
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
function renderFlow() {
  const el = $("#flow");
  if (!D) { el.innerHTML = ""; return; }
  el.innerHTML = FLOW.map((f) => {
    const fs = flowState(f), g = fs.state === "off" ? "" : glyphOf(fs.S);
    const tip = [t("m_" + f.mod), t(STATE_WORD[fs.state])].concat(fs.S.map((s) => s.note).filter(Boolean)).join(" · ");
    return `<li><button type="button" class="stn ${fs.state}" data-go-mod="${f.mod}" title="${esc(tip)}" aria-current="${MOD === f.mod}"><i aria-hidden="true"></i>${esc(t("m_" + f.mod))}${g ? `<small>${esc(g)}</small>` : ""}${fs.state === "wait" ? `<em>${esc(t("f_wait"))}</em>` : ""}<span class="sr">${esc(t(STATE_WORD[fs.state]))}</span></button></li>`;
  }).join("");
}
function waitsIn(mod) { const f = FLOW.find((x) => x.mod === mod); return !!f && flowState(f).state === "wait"; }
function renderRail() {
  const proj = !!D, key = PKEY || LAST;
  const item = (m) => {
    if (m === "space") return `<a class="mod" href="#/" aria-current="${!proj ? "page" : "false"}">${svg("space")}<span>${esc(t("m_space"))}</span></a>`;
    const href = key ? projHash(key, m) : null;
    const dot = proj && waitsIn(m) ? '<i class="dot" aria-hidden="true"></i>' : "";
    return href ? `<a class="mod" href="${href}" aria-current="${proj && MOD === m ? "page" : "false"}" data-mod="${m}">${svg(m)}<span>${esc(t("m_" + m))}</span>${dot}</a>`
      : `<span class="mod" aria-disabled="true" title="${esc(t("pick_film"))}" style="opacity:.35">${svg(m)}<span>${esc(t("m_" + m))}</span></span>`;
  };
  $("#rail").innerHTML = item("space") + "<hr>" + ["idea", "outline", "board", "sound", "cut", "ship"].map(item).join("") + '<span class="grow"></span><hr>' + ["assets", "ledger"].map(item).join("");
}
$("#flow").addEventListener("click", (e) => { const b = e.target.closest("[data-go-mod]"); if (b && PKEY) go(projHash(PKEY, b.dataset.goMod)); });

/* ---------- the space: a card a film ---------- */
function ago(sec) {
  if (!sec) return "";
  const d = Date.now() / 1000 - sec;
  if (d < 90) return t("just_now");
  if (d < 3600) return t("ago_m", { n: Math.round(d / 60) });
  if (d < 86400 * 1.5) return t("ago_h", { n: Math.round(d / 3600) });
  if (d < 86400 * 14) return t("ago_d", { n: Math.round(d / 86400) });
  return new Date(sec * 1000).toISOString().slice(0, 10);
}
function lampOf(state) { return state === "waiting_person" ? "wait" : state === "waiting_agent" || state === "in_progress" ? "agent" : state === "delivered" || state === "done" ? "done" : ""; }
function stateWords(r) {
  const s = r.station ? (L.stn[r.station.id] || r.station.name || "") : "";
  const g = r.station && /^\d$/.test(r.station.id) ? "①②③④⑤"[+r.station.id - 1] + " " : r.station && /^E\d$/.test(r.station.id) ? r.station.id + " " : "";
  const st = t("st_" + (r.state || "not_started"));
  return r.state === "waiting_person" || r.state === "waiting_agent" || r.state === "in_progress" ? `${g}${s} · ${st}` : st;
}
function picture(r, cls) {
  const p = r.picture;
  if (p && p.kind === "image") return `<span class="well ${cls || ""}"><img src="${esc(p.href)}" alt="" loading="lazy"></span>`;
  if (p && p.kind === "video") return `<span class="well ${cls || ""}"><video muted playsinline preload="none" data-mid data-src="${esc(p.href)}"></video></span>`;
  return `<span class="well ${cls || ""}"><span class="ph">${esc(String(r.title || r.name || "·").trim().slice(0, 1))}</span></span>`;
}
function card(r) {
  const a = r.ask, lamp = lampOf(r.state);
  const ask = a ? `<span class="pcard-ask">${esc(a.decisions ? t("ask_n", { n: a.decisions, q: cut(a.question, 60) }) : t("ask_0", { q: cut(a.question, 60) }))}</span>` : "";
  const when = r.last_activity ? ago(r.last_activity.t) : "";
  const meta = [r.effort, r.type ? String(r.type).replace(/^\d+-/, "") : ""].filter(Boolean).join(" · ");
  return `<a class="pcard" href="${projHash(r.key)}" data-state="${esc(r.state || "")}" data-key="${esc(r.key)}">${picture(r)}
    <span class="pcard-name">${esc(r.title || r.name)}</span>
    <span class="pcard-meta"><span class="st ${lamp}"><i aria-hidden="true"></i>${esc(stateWords(r))}</span>${meta ? `<span class="mono">${esc(meta)}</span>` : ""}${when ? `<span>${esc(when)}</span>` : ""}</span>
    ${ask}${r.error ? `<span class="err">${esc(cut(r.error, 120))}</span>` : ""}</a>`;
}
async function listing() { const r = await getJSON("/api/projects"); if (r.ok && r.data) LIST = r.data; return r; }
function leaveProject() {
  if (COLCTL) { COLCTL.destroy(); COLCTL = null; }
  if (PARTCTL) { PARTCTL.destroy(); PARTCTL = null; }
  if (CUT) { CUT.destroy(); CUT = null; }
  clearInterval(liveTimer);
  SCOPE = null;
}
async function showHome(quiet) {
  if (!quiet) {
    leaveProject(); D = null; PKEY = ""; MOD = ""; GV = null;
    setLang(pickLang(LANG)); crumbs([{ text: t("m_space") }]); renderFlow(); renderRail(); spaceColumn();
  }
  const r = await listing();
  if (parse().view !== "home") return;
  if (!r.ok || !LIST) { $("#stage").innerHTML = `<p class="void module">${esc(t("noServer"))}</p>`; return; }
  const rows = LIST.projects, wait = rows.filter((x) => x.state === "waiting_person"), rest = rows.filter((x) => x.state !== "waiting_person");
  const meta = LIST.waiting ? t("home_meta", { n: rows.length, w: LIST.waiting }) : t("home_meta0", { n: rows.length });
  const draft = ($("#oneLine") || {}).value || store.get("desk:oneLine") || "";
  const html = `<section class="module space">
    <div class="ask"><span class="kick">${esc(t("ask_kick"))}</span><h2>${esc(t("ask_h"))}</h2>
      <textarea id="oneLine" rows="2" placeholder="${esc(t("ask_ph"))}" aria-label="${esc(t("ask_h"))}">${esc(draft)}</textarea>
      <div class="row"><span>${esc(t("ask_note"))}</span><button type="button" class="btn btn-primary" id="copyAsk">${esc(t("ask_copy"))}</button></div></div>
    <div class="mh"><h1>${esc(t("films"))}</h1><span class="meta">${esc(meta)}</span></div>
    ${rows.length ? "" : `<p class="void">${esc(t("no_projects"))}</p>`}
    ${wait.length ? `<section class="sect"><h2>${esc(t("g_wait"))}<span class="n">${wait.length}</span></h2><div class="cards">${wait.map(card).join("")}</div></section>` : ""}
    ${rest.length ? `<section class="sect">${wait.length ? `<h2>${esc(t("g_rest"))}<span class="n">${rest.length}</span></h2>` : ""}<div class="cards">${rest.map(card).join("")}</div></section>` : ""}
    ${LIST.roots && LIST.roots.length ? `<p class="roots">${esc(t("roots", { r: LIST.roots.map((x) => x.path || x).join(" · ") }))}</p>` : ""}</section>`;
  const area = $("#stage"), y = area.scrollTop, focused = document.activeElement && document.activeElement.id === "oneLine";
  area.innerHTML = html;
  if (quiet) area.scrollTop = y;
  if (focused) $("#oneLine").focus();
  $("#oneLine").addEventListener("input", (e) => store.set("desk:oneLine", e.target.value));
  $("#copyAsk").addEventListener("click", () => {
    const s = $("#oneLine").value.trim();
    if (!s) { toast(t("ask_empty")); $("#oneLine").focus(); return; }
    copyText(t("ask_prefix") + s).then(() => toast(t("ask_copied")));
  });
  midFrames(area); hoverClips(area); spaceColumn();
  clearTimeout(homeTimer); homeTimer = setTimeout(() => { if (parse().view === "home") showHome(true); }, 15000);
}
function copyText(s) {
  return new Promise((ok) => {
    const old = () => { const x = document.createElement("textarea"); x.value = s; document.body.appendChild(x); x.select(); try { document.execCommand("copy"); } catch (e) { /* nothing to do */ } x.remove(); ok(); };
    try { navigator.clipboard.writeText(s).then(ok, old); } catch (e) { old(); }
  });
}
function loadMid(v) { if (v.src) return; v.addEventListener("loadedmetadata", () => { try { v.currentTime = v.duration / 2; } catch (e) { /* not seekable */ } }, { once: true }); v.preload = "metadata"; v.src = v.dataset.src; }
function midFrames(root) {   // a card of a film shows its middle frame: the video's metadata and one frame, only once it is on screen
  const vids = $$("video[data-mid]", root);
  if (!("IntersectionObserver" in window)) return vids.forEach(loadMid);
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { loadMid(e.target); io.unobserve(e.target); } }), { rootMargin: "200px" });
  vids.forEach((v) => io.observe(v));
}
function hoverClips(root) {   // a film's card plays 4 s of it, muted, while the pointer is on it (from lemo-opuscar's styleboard)
  if (reduced()) return;
  $$(".pcard", root).forEach((c) => {
    const v = $("video", c); if (!v) return;
    let timer = null;
    const start = () => { try { v.currentTime = Math.max(0, (v.duration || 8) / 2 - 2); } catch (e) { /* not seekable */ } v.play().catch(() => {}); clearTimeout(timer); timer = setTimeout(() => v.pause(), 4000); };
    c.addEventListener("mouseenter", () => { loadMid(v); if (v.readyState >= 1) start(); else v.addEventListener("loadedmetadata", start, { once: true }); });
    c.addEventListener("mouseleave", () => { clearTimeout(timer); v.pause(); try { v.currentTime = v.duration / 2; } catch (e) { /* not loaded */ } });
  });
}
function spaceColumn() {
  $("#colRound").hidden = true; $("#composer").hidden = true; $("#confirm").hidden = true;
  $("#colHead").innerHTML = `<b>${esc(t("col_space"))}</b>`;
  const rows = (LIST && LIST.projects) || [], wait = rows.filter((x) => x.state === "waiting_person"), agent = rows.filter((x) => x.state === "waiting_agent" || x.state === "in_progress");
  const li = (r) => `<li><a href="${projHash(r.key)}"><b>${esc(r.title || r.name)}</b><span class="meta">${esc(stateWords(r))}</span>${r.ask ? `<span class="q">${esc(cut(r.ask.question || "", 70))}</span>` : ""}</a></li>`;
  $("#colBody").innerHTML = `<section><h3 class="blk-h"><b>${esc(t("waiting_list"))}</b><span class="n mono">${wait.length}</span></h3>
      ${wait.length ? `<ul class="film-list">${wait.map(li).join("")}</ul>` : `<p class="next">${esc(t("none_waiting"))}</p>`}</section>
    ${agent.length ? `<section><h3 class="blk-h"><b>${esc(t("agent_list"))}</b><span class="n mono">${agent.length}</span></h3><ul class="film-list agent">${agent.map(li).join("")}</ul></section>` : ""}
    <p class="next">${esc(t("col_space_note"))}</p>`;
}

/* ---------- search: / anywhere ---------- */
let hits = [], sel = 0;
async function openSearch() { $("#search").hidden = false; const q = $("#q"); q.value = ""; q.focus(); if (!LIST) await listing(); renderHits(); }
function closeSearch() { $("#search").hidden = true; }
function renderHits() {
  const q = $("#q").value.trim().toLowerCase(), rows = (LIST && LIST.projects) || [];
  hits = rows.filter((r) => !q || [r.title, r.name, r.type].some((x) => String(x || "").toLowerCase().includes(q))).slice(0, 12);
  sel = Math.min(sel, Math.max(0, hits.length - 1));
  const mark = (s) => { const x = esc(s); if (!q) return x; const i = String(s).toLowerCase().indexOf(q); return i < 0 ? x : esc(String(s).slice(0, i)) + "<mark>" + esc(String(s).slice(i, i + q.length)) + "</mark>" + esc(String(s).slice(i + q.length)); };
  $("#results").innerHTML = hits.length ? hits.map((r, i) => `<li role="option" aria-selected="${i === sel}"><a href="${projHash(r.key)}">${picture(r)}<span><b>${mark(r.title || r.name)}</b><br><span class="meta">${esc(r.name)}</span></span><span class="meta">${esc(stateWords(r))}</span></a></li>`).join("")
    : `<li class="meta" style="padding:10px 0">${esc(t("no_match"))}</li>`;
}
$("#q").addEventListener("input", () => { sel = 0; renderHits(); });
$("#q").addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown" || e.key === "ArrowUp") { e.preventDefault(); sel = Math.max(0, Math.min(hits.length - 1, sel + (e.key === "ArrowDown" ? 1 : -1))); renderHits(); }
  else if (e.key === "Enter" && hits[sel]) { e.preventDefault(); closeSearch(); go(projHash(hits[sel].key)); }
  else if (e.key === "Escape") { e.preventDefault(); closeSearch(); }
});
$("#searchBtn").addEventListener("click", () => ($("#search").hidden ? openSearch() : closeSearch()));
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && !typing() && !e.metaKey && !e.ctrlKey) { e.preventDefault(); openSearch(); }
  else if (e.key === "Escape") { if (!$("#search").hidden) closeSearch(); else if (!$("#confirm").hidden) closeConfirm(); }
});
document.addEventListener("click", (e) => { if (!$("#search").hidden && !e.target.closest("#search,#searchBtn")) closeSearch(); });

/* ---------- a project ---------- */
async function loadProject(key) {
  const r = await getJSON(`/api/p/${enc(key)}/data`);
  if (!r.ok || !r.data) { $("#stage").innerHTML = `<p class="void module">${esc(r.data && r.data.error ? r.data.error : t("noServer"))}</p>`; return false; }
  D = r.data; PKEY = key; LAST = key; store.set("desk:last", key);
  ROUND = D.rounds[D.rounds.length - 1] || { id: "notes", gate: "", data: { decisions: [], least_sure: [], decided: [], delegated: [], assets: [], appendix: [], listen: [] } };
  KEY = `desk:${D.project.slug}:${ROUND.id}`;
  FB = store.get(KEY) || { decisions: {}, items: {}, general: "" };
  FB.items = FB.items || {}; FB.decisions = FB.decisions || {};
  setLang(pickLang(D.lang));
  GV = null;
  if (D.current) { const g = await getJSON(`/api/p/${enc(key)}/gate/${enc(D.current)}?lang=${LANG}`); if (g.ok && g.data) GV = g.data; }
  return true;
}
function waitingGate() {   // this round's page, when its stop waits for the person
  if (!D.current) return null;
  const st = stations().find((s) => s.current);
  if (st) return st.state === "waiting_person" ? D.current : null;
  return D.feedback.some((f) => f.round === D.current) ? null : D.current;   // no status: a page nobody answered
}
function defaultMod() {
  const g = waitingGate();
  if (g) return gateMod(g);
  const cur = stations().find((s) => s.current && s.state !== "done" && s.state !== "skipped");
  if (cur && GATE_MOD[cur.id] && GATE_MOD[cur.id] !== "ship") return GATE_MOD[cur.id];
  if (filmPath() || cutShots().length) return "cut";
  return "idea";
}
async function showProject(r) {
  clearTimeout(homeTimer);
  const switching = PKEY !== r.key || !D;
  if (switching) { leaveProject(); D = null; renderShellLoading(); if (!(await loadProject(r.key))) return; }
  MOD = r.mod || defaultMod(); SUB = r.sub || ""; DOC = r.doc || DOC; GATE = r.gate || "";
  crumbs([{ text: t("m_space"), href: "#/" }, { text: D.project.title }]);
  renderFlow(); renderRail();
  if (switching) { renderColumn(); clearInterval(liveTimer); pollLive(); liveTimer = setInterval(pollLive, 4000); }
  renderModule();
  updateComposer();
}
function renderShellLoading() { $("#stage").innerHTML = `<p class="loading">${esc(t("loading"))}</p>`; }
function gateName(g) {
  const b = gateBase(g); if (!b) return g;
  const glyph = /^\d$/.test(b) ? t("gate") + " " + "①②③④⑤"[+b - 1] : b;
  const rest = String(g).slice(b.length);
  return `${glyph} ${L.stn[b] || ""}${rest ? " · " + rest : ""}`.trim();
}

/* ---------- the right column: what waits for you, this round, one note box ---------- */
function renderColumn() {
  const live = $("#colHead .state"); const on = live && live.classList.contains("agent");
  const roundName = ROUND.id === "notes" ? t("col_notes") : gateName(ROUND.id);
  $("#colHead").innerHTML = `<b>${esc(t("col_round"))}</b><span class="who">${esc(roundName)}</span><span class="state${on ? " agent" : ""}" title="${esc(t(on ? "live_on_tip" : "live_off_tip"))}"><i aria-hidden="true"></i><span>${esc(t(on ? "live_on" : "live_off"))}</span></span>`;
  const g = GV && GV.current && roundWaits() ? GV : null;   // the cards only while this round's stop waits for the person
  const decs = g && (ROUND.data.decisions || []).length ? `<section class="c-decs"><h3 class="blk-h"><b>${esc(t("c_decide"))}</b><span class="n mono">${ROUND.data.decisions.length}</span><span class="tag">${esc(t("c_rec"))}</span></h3>${g.summary ? `<p class="round-h">${esc(g.summary)}</p>` : ""}<div class="c-cards">${g.cards}</div></section>`
    : g && g.summary ? `<section><p class="round-h">${esc(g.summary)}</p></section>`
    : ROUND.id !== "notes" ? `<section><p class="next">${esc(t("round_quiet", { g: roundName, s: t("st_" + (roundState() || "done")) }))}</p></section>` : "";
  $("#colBody").innerHTML = `${FB.submittedAt ? `<p class="notice">${esc(t("submitted", { at: FB.submittedAt }))}</p>` : ""}${decs}<section id="cMarks"></section><section id="cMine"></section><section id="cNext"></section>`;
  if (COLCTL) { COLCTL.destroy(); COLCTL = null; }
  const cards = $(".c-cards", $("#colBody"));
  if (cards) COLCTL = OVH.mount(cards, { initial: FB.decisions, onPick: pick, advance: true });
  renderMarks(); renderMine(); renderNext(); renderRound();
  if (!$("#composer").dataset.ready) buildComposer();
  $("#composer").hidden = false;
}
function pick(dec, val) {
  FB.decisions[dec] = val; save();
  $$(`.g-dec[data-dec="${CSS.escape(dec)}"] input[type=radio]`).forEach((x) => { x.checked = x.value === val; });   // its twin in the module
}
function roundWaits() { return !!(D && D.current && ROUND.id === D.current && waitingGate() === D.current); }
function roundState() { const s = stations().find((x) => (x.pages || []).includes(ROUND.id)); return s ? s.state : ""; }
function gateMarks() { return (GV && GV.current && roundWaits() && GV.marks) || []; }
function renderMarks() {
  const M = gateMarks(), least = M.filter((m) => m.kind === "least"), listen = M.filter((m) => m.kind === "listen");
  const li = (m) => `<li tabindex="0" data-goto="${esc(m.target)}"${m.t != null ? ` data-t="${m.t}"` : ""}${m.t1 != null ? ` data-t1="${m.t1}"` : ""}><span class="mono tc">${m.t != null ? esc(fmt(m.t) + (m.t1 != null ? "–" + fmt(m.t1) : "")) : ""}</span><span>${m.id && !/^\s*\d/.test(m.id) ? `<b>${esc(m.id)}</b> ` : ""}${esc(m.note)}</span></li>`;
  $("#cMarks").innerHTML = (least.length ? `<h3 class="blk-h"><b>${esc(t("c_least"))}</b><span class="n mono">${least.length}</span></h3><ul class="note-list marks">${least.map(li).join("")}</ul>` : "")
    + (listen.length ? `<h3 class="blk-h" style="margin-top:12px"><b>${esc(t("c_listen"))}</b><span class="n mono">${listen.length}</span></h3><ul class="note-list marks">${listen.map(li).join("")}</ul>` : "");
}
function myItems() { return Object.entries(FB.items).filter(([, v]) => v && v.status); }
function renderMine() {
  const items = myItems().sort((a, b) => (a[1].t != null ? a[1].t : 1e9) - (b[1].t != null ? b[1].t : 1e9));
  const st = { ok: t("st_ok"), change: t("st_change"), ask: t("st_ask") };
  const row = ([k, v]) => `<li tabindex="0" data-goto="${esc(k)}"${v.t != null ? ` data-t="${v.t}"` : ""}${v.t1 != null ? ` data-t1="${v.t1}"` : ""}><span class="mono tc">${v.t != null ? esc(fmt(v.t) + (v.t1 != null ? "–" + fmt(v.t1) : "")) : ""}</span><span><b>${esc(cut(v.label || k, 40))}</b> ${esc(v.text || st[v.status] || "")}</span><button type="button" class="x" data-del="${esc(k)}" title="${esc(t("del"))}" aria-label="${esc(t("del"))} ${esc(v.label || k)}">×</button></li>`;
  const gen = FB.general ? `<li class="general"><span class="mono tc">·</span><span><b>${esc(t("c_whole_note"))}</b> ${esc(FB.general)}</span><button type="button" class="x" data-del="#general" aria-label="${esc(t("del"))}">×</button></li>` : "";
  $("#cMine").innerHTML = `<h3 class="blk-h"><b>${esc(t("c_mine"))}</b><span class="n mono">${items.length + (FB.general ? 1 : 0)}</span></h3>`
    + (items.length || gen ? `<ul class="note-list mine">${items.map(row).join("")}${gen}</ul>` : `<p class="next">${esc(t("c_none_mine"))}</p>`);
}
function renderNext() {
  const st = (D && D.status) || {}, ns = st.next_step || {}, run = ((st.activity || {}).running || []);
  const who = ns.who === "person" ? "person" : ns.who === "nobody" ? "nobody" : "agent";
  const b = ((st.assets || {}).budget) || {}, money = (o) => Object.entries(o || {}).map(([c, v]) => `${v} ${c}`).join(", ");
  const spent = money(b.spent), limit = b.unlimited ? "∞" : money(b.limit);
  $("#cNext").innerHTML = (run.length ? `<h3 class="blk-h"><b>${esc(t("c_running"))}</b></h3><ul class="note-list">${run.map((x) => `<li><span class="mono tc" style="color:var(--agent)">●</span><span class="mono">${esc(cut(x.cmd || x, 80))}</span></li>`).join("")}</ul>` : "")
    + (ns.do ? `<h3 class="blk-h"><b>${esc(t("c_next"))}</b></h3><p class="next"><span class="who ${who}">${esc(t("who_" + who))}</span>${esc(ns.do)}</p>` : "")
    + (spent || (limit && limit !== "") ? `<h3 class="blk-h"><b>${esc(t("c_spend"))}</b></h3><p class="next mono">${esc([spent ? t("c_spent", { s: spent }) : "", limit ? t("c_of", { l: limit }) : ""].filter(Boolean).join(" · "))}</p>` : "");
}
function renderRound() {
  const n = myItems().length + (FB.general ? 1 : 0), d = roundWaits() ? Object.keys(FB.decisions).length : 0;
  $("#colRound").hidden = false;
  $("#colRound").innerHTML = `<span>${esc(t("round_sum", { n, d }))}</span><button type="button" class="btn btn-primary" id="openConfirm">${esc(t("submit_round"))}</button>`;
  $("#openConfirm").addEventListener("click", openConfirm);
}
$("#colBody").addEventListener("click", (e) => {
  const x = e.target.closest("[data-del]");
  if (x) { e.stopPropagation(); if (x.dataset.del === "#general") FB.general = ""; else delete FB.items[x.dataset.del]; save(); return; }
  const li = e.target.closest("[data-goto]");
  if (li && !e.target.closest("button:not([data-goto]),a,input,textarea")) {
    const tg = li.dataset.goto, k = tg.split(":")[0], words = cut(((li.querySelector("span:last-of-type") || li).textContent || "").trim(), 28);
    const label = (FB.items[tg] && FB.items[tg].label) || (k === "least" ? t("l_least", { x: words }) : k === "atime" ? t("sound_label", { t: fmt(+li.dataset.t) }) : "");
    gotoTarget(tg, li.dataset.t != null ? +li.dataset.t : null, li.dataset.t1 != null ? +li.dataset.t1 : null, label);
  }
});
$("#colBody").addEventListener("keydown", (e) => {   // a mark or a note in the column answers Enter like a click
  const li = e.target.closest && e.target.closest("li[data-goto]");
  if (li && e.target === li && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); li.click(); }
});
const KIND_MOD = { concept: "idea", card: "idea", seg: "outline", cap: "outline", fact: "outline", led: "ledger", doc: "ledger", deleg: "ledger", atime: "sound", asset: "assets",
  time: "cut", range: "cut", chapter: "cut", line: "cut" };
function gotoTarget(target, tt, t1, label) {   // a note or a mark in the column: go to its place
  const kind = target.split(":")[0];
  let mod = KIND_MOD[kind];
  if (kind === "shot") mod = filmPath() || cutShots().length ? "cut" : "board";
  if (kind === "least" || kind === "dec") mod = ROUND.gate ? gateMod(ROUND.id) : MOD;
  if (tt != null && kind !== "cap" && (filmPath() || cutShots().length)) mod = "cut";   // a place with a time is on the cut's timeline
  const after = () => {
    if (mod === "cut" && CUT) { CUT.goto(target, tt, t1); return; }
    const el = kind === "dec" ? document.getElementById("d-" + target.slice(4)) : $(`#stage [data-mark="${CSS.escape(target)}"], #stage [data-target="${CSS.escape(target)}"]`);
    if (el) { el.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "center" }); el.classList.add("flash"); setTimeout(() => el.classList.remove("flash"), 1200); }
    else if (label && kind !== "dec") setScope({ target, label, t: tt, t1 });   // a place the page does not draw (the agent's doubt on the concept): the note box writes against it
  };
  if (mod && mod !== MOD) { go(projHash(PKEY, mod + (kind === "cap" ? "/script" : kind === "fact" ? "/facts" : kind === "doc" ? "/docs" : ""))); setTimeout(after, 260); }
  else after();
}

/* the note box: writes against what is selected (a second, a span, a shot, a chapter, a place the agent marked) or the module */
function buildComposer() {
  const c = $("#composer");
  c.dataset.ready = "1";
  c.innerHTML = `<div class="crow"><span>${esc(t("at"))}</span><span class="chip" id="scope"></span><button type="button" class="xs" id="toWhole" hidden>${esc(t("to_whole"))}</button></div>
    <div class="crow"><span class="modes" role="group"><button type="button" disabled title="${esc(t("say_agent_tip"))}">${esc(t("say_agent"))}</button><button type="button" aria-pressed="true">${esc(t("as_note"))}</button></span><span class="meta">${esc(t("note_keys"))}</span></div>
    <textarea id="say" rows="3"></textarea>
    <div class="send"><span class="meta" id="sayHint"></span><button type="button" class="btn" id="sayAdd">${esc(t("note_add"))}</button></div>`;
  $("#toWhole").addEventListener("click", () => setScope(null));
  $("#sayAdd").addEventListener("click", addNote);
  $("#say").addEventListener("keydown", (e) => { if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) { e.preventDefault(); addNote(); } });
}
function scopeLabel() { return SCOPE ? SCOPE.label : MOD === "cut" ? t("whole_film") : t("whole", { m: t("m_" + (MOD || "cut")) }); }
function updateComposer() {
  if (!$("#composer").dataset.ready) return;
  const x = scopeLabel();
  $("#scope").textContent = x; $("#scope").className = "chip" + (SCOPE ? "" : " quiet");
  $("#toWhole").hidden = !SCOPE;
  $("#say").placeholder = t("c_ph", { x });
}
function setScope(s) {
  SCOPE = s; updateComposer();
  $$("#stage .scoped").forEach((el) => el.classList.remove("scoped"));
  if (s && s.el) s.el.classList.add("scoped");
}
function addNote() {
  const ta = $("#say"), text = ta.value.trim();
  if (!text) { ta.focus(); return; }
  if (!SCOPE) {   // the whole module: the round's overall words
    const pre = MOD && MOD !== "cut" ? `〔${t("m_" + MOD)}〕` : "";
    FB.general = (FB.general ? FB.general + "\n" : "") + pre + text;
  } else {
    const cur = FB.items[SCOPE.target];
    FB.items[SCOPE.target] = Object.assign({}, cur || {}, { status: cur && cur.status === "ask" ? "ask" : "change", label: SCOPE.label, text: cur && cur.text ? cur.text + "\n" + text : text },
      SCOPE.t != null ? { t: SCOPE.t } : {}, SCOPE.t1 != null ? { t1: SCOPE.t1 } : {});
  }
  ta.value = ""; save(); toast(t("noted", { x: scopeLabel() }));
}
$("#stage").addEventListener("click", (e) => {   // a place in a module: the note box writes against it
  if (MOD === "cut" || e.target.closest("button,a,input,textarea,select,label,.fb,summary,video")) return;
  const el = e.target.closest("[data-mark],[data-target]");
  if (!el || !$("#stage").contains(el)) return;
  const target = el.dataset.mark || el.dataset.target;
  if (!/^[a-z]+:/.test(target) || target.startsWith("dec:")) return;
  const fb = $(".fb", el), kind = target.split(":")[0], x = target.slice(kind.length + 1);
  let label = fb ? fb.dataset.label : "";
  if (!label) label = kind === "least" ? t("l_least", { x: x || cut(el.textContent.trim(), 24) }) : kind === "shot" ? t("l_shot", { x }) : kind === "deleg" ? t("l_deleg", { x: cut(el.textContent.trim(), 28) }) : kind === "atime" ? t("sound_label", { t: fmt(+x) }) : target;
  setScope({ target, label, el, t: el.dataset.t != null ? +el.dataset.t : null, t1: el.dataset.t1 != null ? +el.dataset.t1 : null });
});

/* submitting: everything this round holds, then one button (the desk's channel; bin/vh desk wait wakes on it) */
function payload() {
  const g = ROUND.data, decisions = {}, defaulted = [];
  (roundWaits() ? g.decisions || [] : []).forEach((d) => {   // a stop already settled is not decided again by a later note
    const v = FB.decisions[d.id] || d.recommend;
    if (v && (d.options || []).some((o) => o.id === v)) { decisions[d.id] = v; if (!FB.decisions[d.id]) defaulted.push(d.id); }
  });
  const items = myItems().map(([k, v]) => Object.assign({ target: k, status: v.status, label: v.label || k, text: v.text || "" },
    v.suggest && v.suggest !== v.orig ? { suggest: v.suggest } : {}, v.orig && k.startsWith("cap:") ? { orig: v.orig } : {}, v.t != null ? { t: v.t } : {}, v.t1 != null ? { t1: v.t1 } : {}));
  const general = [FB.general || "", ($("#cGeneral") || {}).value || ""].map((x) => x.trim()).filter(Boolean).join("\n");
  return { round: ROUND.id, lang: LANG, decisions, defaulted, items, general };
}
function summaryText(p) {
  const st = { ok: t("st_ok"), change: t("st_change"), ask: t("st_ask") };
  const out = [t("reply_head", { p: D.project.title, r: p.round === "notes" ? t("notes_round") : t("round_name", { r: p.round }) })];
  Object.entries(p.decisions).forEach(([k, v]) => out.push(`${k}: ${v}${p.defaulted.includes(k) ? t("by_rec") : ""}`));
  p.items.forEach((i) => out.push(`${i.label} · ${st[i.status]}${i.text ? COLON() + i.text : ""}${i.suggest ? ` → ${i.suggest}` : ""}`));
  if (p.general) out.push(`${t("overall")}${COLON()}${p.general}`);
  out.push(t("rest"));
  return out.join("\n");
}
function openConfirm() {
  if (!D) return;
  const p = payload(), st = { ok: t("st_ok"), change: t("st_change"), ask: t("st_ask") };
  const decs = (ROUND.data.decisions || []).filter((d) => p.decisions[d.id]).map((d, i) => { const v = p.decisions[d.id], mine = !p.defaulted.includes(d.id), o = (d.options || []).find((x) => x.id === v) || {};
    return `<li><span class="q">${i + 1} · ${esc(d.question || d.id)}</span><span class="v ${mine ? "mine" : "rec"}">${esc(v || "–")}${o.label ? " · " + esc(cut(o.label, 40)) : ""}${mine ? "" : esc(t("by_rec"))}</span></li>`; }).join("");
  const items = p.items.map((i) => `<li><span class="q">${esc(i.label)} · ${esc(st[i.status])}</span>${i.text ? `<span>${esc(i.text)}</span>` : ""}${i.suggest ? `<span class="serif">→ ${esc(i.suggest)}</span>` : ""}</li>`).join("");
  const c = $("#confirm");
  c.innerHTML = `<div class="c-body"><h3>${esc(t("d_title"))}</h3><ul class="sum">${decs ? `<h4>${esc(t("d_decisions"))}</h4>${decs}` : ""}<h4>${esc(t("d_items"))}</h4>${items || `<li class="meta">${esc(t("d_none"))}</li>`}${FB.general ? `<li><span class="q">${esc(t("overall"))}</span><span>${esc(FB.general)}</span></li>` : ""}</ul>
      <label class="meta" for="cGeneral">${esc(t("general"))}</label><textarea id="cGeneral" rows="2" placeholder="${esc(t("general_ph"))}"></textarea>
      <p class="meta" id="submitHint">${esc(t("submit_hint"))}</p>
      <details class="fold"><summary>${esc(t("preview"))}</summary><pre id="preview"></pre></details></div>
    <div class="c-act"><button type="button" class="btn btn-primary" id="doSubmit">${esc(t("submit"))}</button><button type="button" class="btn" id="noSubmit">${esc(t("cancel"))}</button></div>`;
  c.hidden = false;
  const pv = () => { $("#preview").textContent = summaryText(payload()); };
  pv(); $("#cGeneral").addEventListener("input", pv);
  $("#doSubmit").addEventListener("click", submit); $("#noSubmit").addEventListener("click", closeConfirm);
  setTimeout(() => $("#doSubmit").focus(), 30);
}
function closeConfirm() { $("#confirm").hidden = true; const b = $("#openConfirm"); if (b) b.focus(); }
async function submit() {
  const p = payload(), text = summaryText(p);
  let r = null;
  try { r = await fetch(`/api/p/${enc(PKEY)}/feedback`, { method: "POST", headers: { "Content-Type": "application/json", "X-Desk-Token": TOKEN }, body: JSON.stringify(p) }); } catch (e) { r = null; }
  if (r && r.ok) {
    const j = await r.json();
    FB.submittedAt = new Date().toLocaleString(); FB.general = p.general; store.set(KEY, FB);
    toast(j.listening ? t("sent_live") : t("sent", { f: j.saved }));
    $("#submitHint").textContent = t(j.listening ? "hint_live" : "hint_idle", { f: j.saved });
    setTimeout(async () => { $("#confirm").hidden = true; const key = PKEY; leaveProject(); D = null; PKEY = ""; await showProject(Object.assign(parse(), { key })); }, 1400);
    return;
  }
  if (r) { let e = r.status; try { e = (await r.json()).error || e; } catch (x) { /* not JSON */ } toast(t("refused", { e })); return; }
  copyText(text).then(() => toast(t("offline")), () => toast(t("offline2")));
  $("#confirm details").open = true;
}
function save() {
  store.set(KEY, FB);
  if (!D) return;
  renderMine(); renderRound();
  if (CUT) CUT.refresh();
  $$("#stage [data-mark]").forEach(markHost);
}
async function pollLive() {
  if (!PKEY) return;
  const r = await getJSON(`/api/p/${enc(PKEY)}/status`);
  const on = !!(r.ok && r.data && r.data.listening), el = $("#colHead .state");
  if (el) { el.classList.toggle("agent", on); el.title = t(on ? "live_on_tip" : "live_off_tip"); $("span", el).textContent = t(on ? "live_on" : "live_off"); }
  if (r.ok && r.data && D && r.data.round !== undefined && r.data.round !== (D.current || null) && r.data.key === PKEY) {   // the agent sent a new page
    toast(t("new_round", { g: r.data.round || "" }));
    const key = PKEY; leaveProject(); D = null; PKEY = ""; await showProject({ view: "project", key });
  }
}

/* ---------- the modules ---------- */
function moduleHead(kick, title, sub) {
  return `<div class="mh"><span class="kick">${esc(kick)}</span>${title ? `<h1>${esc(title)}</h1>` : ""}${sub ? `<p>${esc(sub)}</p>` : ""}</div>`;
}
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
function renderModule() {
  if (PARTCTL) { PARTCTL.destroy(); PARTCTL = null; if (COLCTL && COLCTL.own) COLCTL.own(); }
  const bench = MOD === "cut" && !(GATE && GATE !== D.current);   // the cut's workbench; an earlier page of its stop is shown as a page
  if (CUT && !bench) { CUT.destroy(); CUT = null; }
  if (SCOPE && SCOPE.el) setScope(null); else if (SCOPE && !bench) setScope(null);
  const area = $("#stage");
  area.classList.toggle("is-cut", bench);
  if (bench) { if (CUT && !GATE) { CUT.refresh(); return; } if (CUT) CUT.destroy(); CUT = CutModule(area); return; }
  const cur = SUB && (SUBS[MOD] || []).includes(SUB) ? SUB : (SUBS[MOD] || [""])[0];
  const fn = { idea: mIdea, outline: () => ({ outline: vOutline, script: vScript, facts: vFacts }[cur] || vOutline)(), board: mBoard, sound: vSound,
    ship: () => (cur === "versions" ? vVersions() : vCheck() + `<p class="void">${esc(t("ship_none"))}</p>`), assets: vAssets,
    ledger: () => ({ decisions: vLedger, history: vHistory, docs: vDocs }[cur] || vLedger)(), cut: () => "" }[MOD] || mIdea;
  const page = stopPage(MOD);
  area.innerHTML = `<section class="module" data-mod="${MOD}">${moduleHead(kickOf(MOD), "", "")}${page ? '<div id="gatePart"></div>' : ""}${subtabs(MOD)}<div id="modBody">${fn()}</div></section>`;
  if (page) loadGatePart(page);
  else { const link = pastPageLink(MOD); if (link) $(".mh", area).insertAdjacentHTML("beforeend", link); }
  $$("[data-mark]", area).forEach(markHost);
  ({ outline: cur === "script" ? wireScript : wireOutline, board: wireBoard, sound: wireSound }[MOD] || (() => {}))();
  area.scrollTop = 0;
}
function stopPage(mod) {   // the stop's page this module shows on top: the one asked for, else this round's when it waits here
  if (GATE && gateMod(GATE) === mod) return GATE;
  const w = waitingGate();
  return w && gateMod(w) === mod ? w : null;
}
function pastPageLink(mod) {
  const f = FLOW.find((x) => x.mod === mod); if (!f) return "";
  const s = stations().filter((x) => f.st.includes(x.id) && x.pages && x.pages.length && /^\d$/.test(x.id) && GATE_MOD[x.id] === mod).pop();
  if (!s) return "";
  const pg = s.pages[s.pages.length - 1];
  return `<a class="meta" style="margin-left:auto" href="${projHash(PKEY, "gate/" + enc(pg))}">${esc(t("page_of", { g: gateName(pg) }))}</a>`;
}
async function loadGatePart(gid) {
  const r = await getJSON(`/api/p/${enc(PKEY)}/gate/${enc(gid)}?lang=${LANG}`);
  const host = $("#gatePart"); if (!host) return;
  if (!r.ok || !r.data) { host.innerHTML = `<p class="void">${esc((r.data && r.data.error) || "")}</p>`; return; }
  const g = r.data, past = !g.current;
  host.innerHTML = (past ? `<p class="notice">${esc(t("past", { g: gateName(g.gate) }))}${D.current ? ` <a href="${projHash(PKEY, gateMod(D.current))}">${esc(t("to_round"))}</a>` : ""}</p>` : "") + g.html;
  const root = $(".gate", host);
  // the decisions live in the right column; a decision drawn with pictures stays here as the picture, its pick kept in step with the column's
  $$(".g-side, .g-act, .g-decs", root).forEach((x) => x.remove());
  $$(".g-dec:not(.wide)", root).forEach((x) => x.remove());
  const body = $(".g-body", root); if (body) body.classList.remove("has-side");
  if (!past) $$(".g-marks", root).forEach((x) => { const s = x.closest("section"); if (s) s.remove(); });   // they are in the column
  $$("input[type=radio]", root).forEach((x) => { if (past) x.disabled = true; else x.name = "m-" + x.name; });
  PARTCTL = OVH.mount(root, past ? {} : { initial: FB.decisions, onPick: pick, advance: false });
  if (past) $$(".g-dec", root).forEach((d) => { d.classList.remove("active"); $$("input[type=radio]", d).forEach((x) => { x.checked = false; }); });   // what was picked then is in REVIEW.md, not here
  $$("[data-mark]", root).forEach(markHost);
}

/* ✓ / ✎ / ? on an item (the desk's views, moved into the modules) */
function fbCtl(target, label, opt = {}) {
  const v = FB.items[target] || {}, st = v.status || "";
  const lab = opt.labels || [t("fb_ok"), t("fb_change"), t("fb_ask")];
  return `<div class="fb" data-target="${esc(target)}" data-label="${esc(label)}"${opt.suggest != null ? ` data-orig="${esc(opt.suggest)}"` : ""}${opt.t != null ? ` data-t="${opt.t}"` : ""}${opt.labels ? ` data-labels="${esc(JSON.stringify(opt.labels))}"` : ""}${opt.def ? ` data-def="${esc(opt.def)}"` : ""}>
    <span class="seg3"><button type="button" data-st="ok" class="${st === "ok" ? "on" : ""}">${esc(lab[0])}</button><button type="button" data-st="change" class="${st === "change" ? "on" : ""}">${esc(lab[1])}</button><button type="button" data-st="ask" class="${st === "ask" ? "on" : ""}">${esc(lab[2])}</button></span>
    ${st ? "" : `<span class="def">${esc(opt.def || t("fb_def"))}</span>`}
    <div class="fb-more" ${st === "change" || st === "ask" ? "" : "hidden"}>
      <textarea rows="2" data-k="text" placeholder="${esc(st === "ask" ? t("ph_ask") : t("ph_change"))}">${esc(v.text || "")}</textarea>
      ${opt.suggest != null && st === "change" ? `<input data-k="suggest" placeholder="${esc(t("ph_suggest"))}" value="${esc(v.suggest != null ? v.suggest : opt.suggest)}">` : ""}
    </div></div>`;
}
document.addEventListener("click", (e) => {
  const b = e.target.closest(".fb .seg3 button"); if (!b) return;
  e.stopPropagation();
  const box = b.closest(".fb"), tgt = box.dataset.target, cur = FB.items[tgt] || {};
  const st = cur.status === b.dataset.st ? "" : b.dataset.st;
  if (!st) delete FB.items[tgt];
  else FB.items[tgt] = Object.assign({}, cur, { status: st, label: box.dataset.label }, box.dataset.t ? { t: +box.dataset.t } : {}, box.dataset.orig != null ? { orig: box.dataset.orig } : {});
  save(); refreshFb(box);
});
document.addEventListener("input", (e) => {
  const el = e.target.closest(".fb-more [data-k]"); if (!el) return;
  const tgt = el.closest(".fb").dataset.target; FB.items[tgt] = Object.assign({}, FB.items[tgt] || {}, { [el.dataset.k]: el.value }); store.set(KEY, FB);
  clearTimeout(el._h); el._h = setTimeout(renderMine, 400);
});
function refreshFb(box) {
  const wrap = document.createElement("div");
  wrap.innerHTML = fbCtl(box.dataset.target, box.dataset.label, { suggest: box.dataset.orig != null ? box.dataset.orig : null, t: box.dataset.t != null ? box.dataset.t : null,
    labels: box.dataset.labels ? JSON.parse(box.dataset.labels) : null, def: box.dataset.def || null });
  const nb = wrap.firstElementChild; box.replaceWith(nb);
  const host = nb.closest("[data-mark]"); if (host) markHost(host);
  const ta = nb.querySelector("textarea"); if (ta && !nb.querySelector(".fb-more").hidden) ta.focus();
}
function markHost(host) { const st = (FB.items[host.dataset.mark] || {}).status; host.classList.toggle("marked", !!st); host.classList.toggle("st-ok", st === "ok"); host.classList.toggle("st-ask", st === "ask"); }

const docOf = (f) => D.docs.find((d) => d.file === f);
function docHtml(doc, onlySection) {
  if (!doc) return "";
  const secs = onlySection ? doc.sections.filter((s) => onlySection.test(s.title)) : doc.sections;
  return `<div class="md">${onlySection ? "" : doc.intro}${secs.map((s) => `<h2>${esc(s.title)}</h2>${s.html}`).join("")}</div>`;
}
function fallback(note, file, onlySection) {
  const doc = docOf(file); if (!doc) return "";
  const part = onlySection && doc.sections.some((s) => onlySection.test(s.title)) ? onlySection : null;
  return `<p class="notice">${esc(note)}</p><div class="card" data-mark="doc:${esc(file)}">${docHtml(doc, part)}${fbCtl("doc:" + file, file)}</div>`;
}
const specGet = (k) => (D.spec.find((s) => s.k.toLowerCase().startsWith(k)) || {}).v || "";

function mIdea() {
  const c = D.concept;
  if (!docOf("BRIEF.md")) return `<div class="void">${esc(t("no_brief"))}</div>`;
  return `<div class="card idea-card" data-mark="concept:line"><div class="meta">${esc(t("concept"))}</div><div class="idea-line">${esc(c.line || "—")}</div>
    <dl class="kv">${c.spine ? `<dt>${esc(t("spine"))}</dt><dd>${esc(c.spine)}</dd>` : ""}${c.motif ? `<dt>${esc(t("motif"))}</dt><dd>${esc(c.motif)}</dd>` : ""}${c.end ? `<dt>${esc(t("end"))}</dt><dd>${esc(c.end)}</dd>` : ""}
    <dt>${esc(t("spec"))}</dt><dd>${["output", "effort", "watch on", "review language"].map(specGet).filter(Boolean).map((x) => `<span class="chip quiet">${esc(x.split("（")[0].split("  ")[0])}</span>`).join(" ")}</dd></dl>
    ${fbCtl("concept:line", t("concept"))}</div>`;
}
function vOutline() {
  const O = D.outline.filter((o) => o.t0 != null && o.t1 != null), total = O.length ? Math.max(...O.map((o) => o.t1)) : 0;
  if (!D.outline.length) return docOf("BRIEF.md") ? fallback(t("no_outline"), "BRIEF.md", /^(Outline|大纲)/i) : `<div class="void">${esc(t("no_brief"))}</div>`;
  const bar = O.length ? `<div class="tbar">${O.map((o) => `<div data-seg="${esc(o.id)}" style="flex:${Math.max(0.1, o.t1 - o.t0).toFixed(2)}">${esc(o.title)}</div>`).join("")}</div><div class="tticks">${[0, 0.25, 0.5, 0.75, 1].map((f) => `<span>${fmt(total * f)}</span>`).join("")}</div>` : "";
  const segs = D.outline.map((o, i) => {
    const caps = D.captions.rows.filter((x) => x.seg === o.id);
    const when = o.t0 != null ? `${fmt(o.t0)}–${fmt(o.t1)}${o.t1 != null ? ` · ${(o.t1 - o.t0).toFixed(0)} s` : ""}` : "";
    return `<div class="card segcard" id="seg-${esc(o.id)}" data-mark="seg:${esc(o.id)}"><div class="stripe"></div><div>
      <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><div><span class="meta">${esc(t("seg_n", { i: o.id || i + 1 }))}</span> <span class="serif" style="font-size:17px">${esc(o.title)}</span>${o.tag ? ` <span class="tag">${esc(o.tag)}</span>` : ""} ${o.stage && o.stage !== "—" ? `<span class="chip">${esc(o.stage)}</span>` : ""}</div>
        <span class="meta mono">${when}${o.bars ? ` · ${esc(t("bars", { b: o.bars }))}` : ""}</span></div>
      ${o.know ? `<div style="margin-top:6px"><span class="chip quiet">${esc(t("know"))}</span> ${esc(o.know)}</div>` : ""}
      ${o.visual ? `<div class="small muted" style="margin-top:4px"><span class="chip quiet">${esc(t("visual"))}</span> ${esc(o.visual)}</div>` : ""}
      ${caps.length ? `<details style="margin-top:8px"><summary class="small">${esc(t("seg_caps", { n: caps.length }))}</summary>${caps.map((x) => `<div class="segcap serif"><span class="id">${esc(x.id)}</span>${esc(x.text)}</div>`).join("")}</details>` : ""}
      ${fbCtl("seg:" + o.id, t("l_seg", { i: o.id, x: o.title }))}</div></div>`;
  }).join("");
  return `${O.length ? `<p class="sub">${esc(t("outline_tip"))}</p>` : ""}${bar}<div class="grid">${segs}</div>`;
}
function wireOutline() { $$(".tbar [data-seg]").forEach((el) => el.addEventListener("click", () => { const s = document.getElementById("seg-" + el.dataset.seg); if (s) s.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "center" }); })); }
const SPEED = { zh: [6, 9], en: [15, 20] };
function speed(x) {
  const cjk = /[㐀-鿿]/.test(x.text), n = cjk ? (x.text.match(/[㐀-鿿A-Za-z0-9]/g) || []).length : x.text.trim().length;
  const s = x.t0 != null && x.t1 != null ? Math.max(0.1, x.t1 - x.t0) : null, lim = SPEED[cjk ? "zh" : "en"];
  return { n, s, r: s ? n / s : null, lim };
}
function vScript() {
  const C = D.captions;
  if (!C.rows.length) return docOf("SCRIPT.md") ? fallback(t("no_script"), "SCRIPT.md") : `<div class="void">${esc(t("no_script_file"))}</div>`;
  const keep = (x) => capFilter === "all" || (capFilter === "mine" && FB.items["cap:" + x.id]) || (capFilter === "terms" && x.term) || (capFilter === "facts" && x.facts.length) || (capFilter === "fast" && speed(x).r > speed(x).lim[0]);
  const lab = C.kind === "narration" ? "l_vo" : "l_cap";
  const row = (x) => {
    const sp = speed(x), col = sp.r == null ? "var(--ink-3)" : sp.r <= sp.lim[0] ? "var(--ok)" : sp.r <= sp.lim[1] ? "var(--wait)" : "var(--live)";
    return `<div class="capr" id="cap-${esc(x.id)}" data-mark="cap:${esc(x.id)}"><div><div class="id">${esc(x.id)}</div><div class="tm">${x.t0 != null ? fmt(x.t0) : esc(x.bars)}</div></div>
      <div>${x.term ? `<div class="term" title="${esc(t("term"))}">${esc(x.term)}</div><br>` : ""}<div class="txt">${esc(x.text)}</div>${x.visual ? `<div class="vis">${esc(t("visual"))}${COLON()}${esc(x.visual)}</div>` : ""}
        <div class="meter">${sp.r != null ? `<span>${esc(t("chars", { n: sp.n, s: sp.s.toFixed(1) }))}</span><span class="bar"><i style="width:${Math.min(100, (sp.r / (sp.lim[1] * 1.2)) * 100)}%;background:${col}"></i></span><span style="color:${col}">${sp.r.toFixed(1)}${esc(t("per_s"))}</span>` : ""}${x.facts.map((f) => `<a class="chip" href="${projHash(PKEY, "outline/facts")}">${esc(f)}</a>`).join("")}</div></div>
      <div>${fbCtl("cap:" + x.id, t(lab, { x: x.id }), { suggest: x.text })}</div></div>`;
  };
  const groups = D.outline.map((o) => ({ o, rows: C.rows.filter((x) => x.seg === o.id && keep(x)) })).concat([{ o: null, rows: C.rows.filter((x) => !D.outline.some((o) => o.id === x.seg) && keep(x)) }]);
  const html = groups.filter((g) => g.rows.length).map(({ o, rows }) => `<div class="capgroup"><div class="gh">${o ? `<span>${esc(t("seg_n", { i: o.id }))} · ${esc(o.title)}</span>${o.t0 != null ? `<span class="meta mono">${fmt(o.t0)}–${fmt(o.t1)}</span>` : ""}` : `<span>${esc(t("other_seg"))}</span>`}</div>${rows.map(row).join("")}</div>`).join("");
  const F = [["all", "f_all"], ["mine", "f_mine"], ["terms", "f_terms"], ["facts", "f_facts"], ["fast", "f_fast"]].filter(([k]) => k !== "terms" || C.rows.some((x) => x.term));
  return `<p class="sub">${esc(t("script_sub", { n: C.rows.length, g: SPEED.zh[0], y: SPEED.zh[1], eg: SPEED.en[0], ey: SPEED.en[1] }))}</p>
    <div class="filters">${F.map(([k, n]) => `<button type="button" data-f="${k}" class="${capFilter === k ? "on" : ""}">${esc(t(n))}</button>`).join("")}</div>${html || `<div class="void">${esc(t("none_match"))}</div>`}`;
}
function wireScript() { $$(".filters button").forEach((b) => b.addEventListener("click", () => { capFilter = b.dataset.f; $("#modBody").innerHTML = vScript(); $$("#modBody [data-mark]").forEach(markHost); wireScript(); })); }
function mBoard() {
  const S = D.shots.items || [];
  if (!S.length) return docOf("STORYBOARD.md") ? fallback(t("no_board"), "STORYBOARD.md") : `<div class="void">${esc(t("no_board_file"))}</div>`;
  const timed = S.filter((s) => s.start != null && s.end != null);
  const track = timed.map((s) => `<div data-shot="${esc(s.id)}" class="${s.unsure ? "unsure" : ""}" style="flex:${Math.max(0.1, s.end - s.start).toFixed(2)}">${esc(s.id)}</div>`).join("");
  const cards = S.map((s) => `<div class="card bshot ${s.unsure ? "unsure" : ""}" id="bshot-${esc(s.id)}" data-id="${esc(s.id)}" data-mark="shot:${esc(s.id)}">
      <div class="thumb" data-shot="${esc(s.id)}">${s.frame ? `<img src="${esc(src(s.frame))}" alt="" loading="lazy">` : ""}<span class="sid">${esc(s.id)}</span>${s.start != null ? `<span class="play">▶ ${fmt(s.start)}–${fmt(s.end)}</span>` : ""}</div>
      <div class="body"><div class="lab">${esc(s.label || "")} <span class="meta">${esc(s.segment || "")}${s.start != null && s.end != null ? ` · ${(s.end - s.start).toFixed(1)} s` : ""}</span></div>
        ${s.caption ? `<div class="capline">${esc(s.caption)}</div>` : `<div class="meta" style="margin-top:6px">${esc(t("no_shot_caption"))}</div>`}
        ${s.reads.length ? `<ul>${s.reads.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}
        ${s.transition ? `<div class="meta" style="margin-top:6px">${esc(t("transition"))}${esc(s.transition)}</div>` : ""}
        ${s.unsure ? `<div class="unsure-note">${esc(t("unsure_x"))}${esc(typeof s.unsure === "string" ? s.unsure : "")}</div>` : ""}
        ${fbCtl("shot:" + s.id, t("l_shot", { x: s.id }))}</div></div>`).join("");
  const player = D.shots.video ? `<div class="bplayer"><video id="bv" src="${esc(src(D.shots.video))}" controls preload="metadata"></video>${track ? `<div class="strack">${track}<div class="playhead" id="bph"></div></div>` : ""}</div>` : `<p class="small muted">${esc(t("no_video"))}</p>`;
  return `<p class="sub">${esc(D.shots.note ? D.shots.note + " · " : "")}${esc(t("board_sub"))}</p>${player}<div class="grid g3" style="margin-top:14px">${cards}</div>`;
}
function wireBoard() {
  const v = $("#bv"); if (!v) return;
  const S = (D.shots.items || []).filter((s) => s.start != null && s.end != null), total = S.length ? Math.max(...S.map((s) => s.end)) : 1; let stopAt = null;
  const play = (id) => { const s = S.find((x) => x.id === id); if (!s) return; v.currentTime = s.start + 0.01; stopAt = s.end; v.play(); };
  $$("#modBody [data-shot]").forEach((el) => el.addEventListener("click", () => play(el.dataset.shot)));
  v.addEventListener("timeupdate", () => {
    if (stopAt != null && v.currentTime >= stopAt - 0.03) { v.pause(); stopAt = null; }
    const ph = $("#bph"); if (ph) ph.style.left = Math.min(100, (v.currentTime / total) * 100) + "%";
    const cur = S.find((s) => v.currentTime >= s.start && v.currentTime < s.end);
    $$("#modBody .bshot").forEach((c) => c.classList.toggle("active", !!cur && c.dataset.id === cur.id));
  });
}
function vSound() {
  const M = D.music;
  if (!M || (!M.audio && !(M.sections || []).length)) return `<div class="void">${esc(t("no_music"))}</div>`;
  const dur = M.duration || Math.max(1, ...(M.sections || []).map((s) => s.end));
  const secs = (M.sections || []).map((s) => `<div data-t="${s.start}" title="${esc(s.name)}" style="flex:${Math.max(0.05, s.end - s.start).toFixed(2)}">${esc(s.label || s.name)}</div>`).join("");
  const hits = (M.hits || []).map((h) => `<i style="left:${(h.t / dur) * 100}%" title="${esc(h.part)} ${fmt(h.t)}"></i>`).join("");
  const listen = (ROUND.data.listen || []).map((l) => `<button class="btn" type="button" data-seek="${l.t}">▶ ${fmt(l.t)} · ${esc(l.note)}</button>`).join("");
  const tcs = Object.entries(FB.items).filter(([k]) => k.startsWith("atime:")).sort((a, b) => a[1].t - b[1].t);
  return `<p class="sub">${esc(t("sound_sub", { bpm: M.bpm || "–", d: (+dur).toFixed(1) }))}</p>
    <div>${M.audio ? `<audio id="au" src="${esc(src(M.audio))}" controls preload="metadata"></audio>` : `<p class="small muted">${esc(t("no_audio"))}</p>`}
      ${secs ? `<div class="secbar" id="secbar">${secs}<div class="playhead" id="aph"></div></div><div class="hits">${hits}</div>` : ""}
      ${M.audio ? `<div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap"><button class="btn" type="button" id="atc">${esc(t("comment_at", { t: "\u0001" })).replace("\u0001", '<span id="atnow">0:00.0</span>')}</button><span class="meta">${esc(t("sec_tip"))}</span></div>` : ""}</div>
    ${listen ? `<div class="sect"><h2>${esc(t("listen"))}</h2><div class="listen">${listen}</div></div>` : ""}
    <div class="sect"><h2>${esc(t("your_sound"))} <span class="n">${tcs.length}</span></h2>
    <div>${tcs.map(([k, v]) => `<div class="card" style="margin-bottom:10px" data-mark="${esc(k)}"><span class="chip" data-seek="${v.t}">${fmt(v.t)}</span>${fbCtl(k, t("sound_label", { t: fmt(v.t) }), { t: v.t })}</div>`).join("") || `<div class="muted small">${esc(t("none_sound"))}</div>`}</div></div>
    ${M.roll ? `<details class="fold" style="margin-top:22px"><summary>${esc(t("roll"))}</summary><img class="roll" src="${esc(src(M.roll))}" alt="" loading="lazy"></details>` : ""}`;
}
function wireSound() {
  const a = $("#au"); if (!a) return;
  const dur = D.music.duration || 1;
  $$("#modBody [data-seek]").forEach((b) => b.addEventListener("click", () => { a.currentTime = +b.dataset.seek; a.play(); }));
  $$("#secbar [data-t]").forEach((b) => b.addEventListener("click", () => { a.currentTime = +b.dataset.t; a.play(); }));
  a.addEventListener("timeupdate", () => { const ph = $("#aph"); if (ph) ph.style.left = Math.min(100, (a.currentTime / (a.duration || dur)) * 100) + "%"; $("#atnow").textContent = fmt(a.currentTime); });
  $("#atc").addEventListener("click", () => { const x = +a.currentTime.toFixed(1); a.pause(); FB.items["atime:" + x] = { status: "change", label: t("sound_label", { t: fmt(x) }), t: x, text: "" }; save(); renderModule(); const ta = $(`[data-target="atime:${x}"] textarea`); if (ta) ta.focus(); });
}
function vFacts() {
  if (!D.facts.length) return docOf("NOTES.md") ? fallback(t("no_facts"), "NOTES.md") : `<div class="void">${esc(t("no_notes"))}</div>`;
  const rows = D.facts.map((f) => `<tr class="${f.dropped ? "dropped" : ""}" id="fact-${esc(f.id.slice(1))}" data-mark="fact:${esc(f.id)}"><td><b>${esc(f.id)}</b><div class="meta">${esc(f.kind)}</div></td>
      <td>${esc(f.claim)}${f.dropped ? `<div class="meta">${esc(t("dropped"))}</div>` : ""}</td><td class="serif">${esc(f.onscreen)}</td><td class="small muted">${esc(f.source)}</td>
      <td style="min-width:230px">${f.dropped || !f.id ? "" : fbCtl("fact:" + f.id, t("l_fact", { x: f.id }), { labels: [t("fact_ok"), t("fact_bad"), t("fact_unsure")], def: t("fact_def") })}</td></tr>`).join("");
  return `<p class="sub">${esc(t("facts_sub"))}</p>
    ${D.fact_todo.length ? `<div class="card" style="margin-bottom:16px"><b class="small">${esc(t("todo"))}</b><ul class="small" style="margin:6px 0 0;padding-left:18px">${D.fact_todo.map((x) => `<li>${x.done ? "✓ " : ""}${esc(x.text)}</li>`).join("")}</ul></div>` : ""}
    <div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_id"))}</th><th>${esc(t("th_claim"))}</th><th>${esc(t("th_screen"))}</th><th>${esc(t("th_src"))}</th><th>${esc(t("th_you"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}
const verdictCls = (v) => (/pass|ok/i.test(v || "") ? "ok" : /fail/i.test(v || "") ? "bad" : "");
function vCheck() {
  const st = D.status || {}, c = st.check, R = st.renders || [];
  const size = (n) => (n > 1e9 ? (n / 1e9).toFixed(1) + " GB" : n > 1e6 ? (n / 1e6).toFixed(1) + " MB" : Math.round(n / 1e3) + " kB");
  const head = c ? `<div class="card"><dl class="kv"><dt>${esc(t("verdict"))}</dt><dd class="${verdictCls(c.verdict)}">${esc(c.verdict || "–")}${c.exit != null ? ` · exit ${c.exit}` : ""}</dd>
      <dt>${esc(t("th_file"))}</dt><dd>${esc(c.video || "")}</dd><dt>${esc(t("th_when"))}</dt><dd>${esc((c.at || "").replace("T", " ").slice(0, 16))}</dd>
      ${Object.keys(c.counts || {}).length ? `<dt>·</dt><dd>${Object.entries(c.counts).map(([k, v]) => `<span class="chip quiet">${esc(k)} ${esc(v)}</span>`).join(" ")}</dd>` : ""}</dl>
      ${c.stale ? `<p class="notice" style="margin:12px 0 0">${esc(t("check_stale"))}</p>` : ""}
      ${(c.fails || []).length ? `<h3>${esc(t("fails"))}</h3><ul class="small">${c.fails.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}</div>` : `<div class="void">${esc(t("no_check"))}</div>`;
  const rows = R.map((r) => `<tr><td>${esc(r.path)}</td><td>${esc(size(r.size || 0))}</td><td>${esc((r.mtime || "").replace("T", " ").slice(0, 16))}</td><td class="${verdictCls(r.check && r.check.verdict)}">${esc(r.check ? r.check.verdict : "–")}</td></tr>`).join("");
  return `<p class="sub">${esc(t("check_sub"))}</p>${head}${rows ? `<div class="sect"><h2>${esc(t("renders"))}</h2><div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_file"))}</th><th>${esc(t("th_size"))}</th><th>${esc(t("th_when"))}</th><th>${esc(t("th_check"))}</th></tr></thead><tbody>${rows}</tbody></table></div></div>` : ""}`;
}
function vVersions() {
  const V = (D.status || {}).versions;
  if (!V || !V.list) return `<div class="void">${esc(V && V.error ? V.error : t("no_versions"))}</div>`;
  const rows = V.list.slice().reverse().map((x) => `<tr><td>${esc(x.id)}</td><td>${esc((x.at || "").replace("T", " ").slice(0, 16))}</td><td>${esc(x.film || "")}</td><td class="${x.state === "current" ? "ok" : ""}">${esc(x.state || "")}</td><td>${esc(x.made_by || "")}</td><td class="small muted">${esc(x.note || "")}</td><td>${esc(x.check && x.check.verdict ? x.check.verdict : "")}</td></tr>`).join("");
  return `<p class="sub">${esc(t("versions_sub"))}</p><div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_ver"))}</th><th>${esc(t("th_when"))}</th><th>${esc(t("th_file"))}</th><th>${esc(t("th_state"))}</th><th>${esc(t("th_made"))}</th><th>${esc(t("th_note"))}</th><th>${esc(t("th_check"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}
function vAssets() {
  const A = (D.status || {}).assets;
  if (!A || A.error) return `<div class="void">${esc(A && A.error ? A.error : t("no_assets"))}</div>`;
  const b = A.budget || {}, money = (o) => Object.entries(o || {}).map(([c, v]) => `${v} ${c}`).join(", ") || "–";
  return `<p class="sub">${esc(t("assets_sub"))}</p><div class="card"><dl class="kv">
    <dt>${esc(t("a_records"))}</dt><dd>${esc(A.records)}</dd><dt>${esc(t("a_uncleared"))}</dt><dd class="${A.uncleared ? "bad" : ""}">${esc(A.uncleared)}</dd>
    <dt>${esc(t("a_not_taken"))}</dt><dd class="${A.not_taken ? "bad" : ""}">${esc(A.not_taken)}</dd><dt>${esc(t("a_aigc"))}</dt><dd>${esc(A.aigc)}</dd>
    <dt>${esc(t("a_spent"))}</dt><dd>${esc(money(b.spent))}</dd><dt>${esc(t("a_budget"))}</dt><dd>${esc(b.unlimited ? "∞" : money(b.limit))}</dd></dl></div>`;
}
function vLedger() {
  if (!D.ledger.length && !D.agent_decided.length) return docOf("DECISIONS.md") ? fallback(t("no_ledger"), "DECISIONS.md") : `<div class="void">${esc(t("no_dec"))}</div>`;
  const cur = D.agent_decided.filter((a) => !a.superseded), old = D.agent_decided.filter((a) => a.superseded);
  const item = (a, live) => { const i = D.agent_decided.indexOf(a); return `<div class="card led" data-mark="led:${i}"><div><div class="topic">${esc(a.topic || "—")}</div><div class="meta">${esc(a.date)}</div></div>
    <div><div>${esc(a.what)}</div>${a.group ? `<div class="meta">${esc(a.group)}</div>` : ""}${a.why ? `<div class="small muted" style="margin-top:4px"><span class="chip quiet">${esc(t("why"))}</span> ${esc(a.why)}</div>` : ""}${a.undo ? `<div class="small muted" style="margin-top:4px"><span class="chip wait">${esc(t("undo"))}</span> ${esc(a.undo)}</div>` : ""}${a.note ? `<div class="meta" style="margin-top:4px">${esc(a.note)}</div>` : ""}
    ${live ? fbCtl("led:" + i, t("l_led", { x: (a.topic ? a.topic + COLON() : "") + cut(a.what, 20) }), { labels: [t("agree"), t("overturn"), t("fb_ask")], def: t("def_agree") }) : ""}</div></div>`; };
  return `<p class="sub">${esc(t("ledger_sub"))}</p>
    ${D.ledger.length ? `<div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_what"))}</th><th>${esc(t("th_who"))}</th><th>${esc(t("th_status"))}</th></tr></thead><tbody>${D.ledger.map((l) => `<tr><td>${esc(l.what)}</td><td class="small">${esc(l.who)}</td><td class="small">${esc(l.status)}</td></tr>`).join("")}</tbody></table></div>` : ""}
    ${cur.length ? `<div class="sect"><h2>${esc(t("agent_n", { n: cur.length }))}</h2><div class="grid">${cur.map((a) => item(a, true)).join("")}</div></div>` : ""}
    ${old.length ? `<details class="fold" style="margin-top:20px"><summary>${esc(t("superseded", { n: old.length }))}</summary><div class="grid body" style="opacity:.6">${old.map((a) => item(a, false)).join("")}</div></details>` : ""}`;
}
function vHistory() {
  const H = D.history.slice().reverse(), F = D.feedback.slice().reverse();
  if (!H.length && !F.length) return docOf("REVIEW.md") ? `<div class="card">${docHtml(docOf("REVIEW.md"))}</div>` : `<div class="void">${esc(t("no_history"))}</div>`;
  return `<p class="sub">${esc(t("history_sub"))}</p>` + H.map((h) => `<details class="fold" ${h === H[0] ? "open" : ""}><summary>${esc(h.title)}</summary><div class="body md">${h.html}</div></details>`).join("")
    + (F.length ? `<div class="sect"><h2>${esc(t("desk_subs"))}</h2><ul class="small">${F.map((f) => `<li><a href="${esc(src(f.file.replace(/\.json$/, ".md")))}" target="_blank" rel="noopener">${esc(f.round)} · ${esc(f.submitted_at.replace("T", " "))}</a> · ${f.items.length} ✎</li>`).join("")}</ul></div>` : "");
}
function vDocs() {
  if (!D.docs.length) return `<div class="void">${esc(t("no_docs"))}</div>`;
  const doc = docOf(DOC) || D.docs[0];
  const nav = `<div class="docnav">${D.docs.map((d) => `<a href="${projHash(PKEY, "ledger/docs/" + d.file)}" class="${d === doc ? "on" : ""}">${esc(d.file)}</a>`).join("")}</div>`;
  const warn = D.warnings.length ? `<div class="notice"><b>${esc(t("warnings"))}</b><ul style="margin:4px 0 0;padding-left:18px">${D.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>` : "";
  const intro = doc.intro ? `<div class="docsec"><div class="md">${doc.intro}</div></div>` : "";
  const secs = doc.sections.map((s) => { const k = "doc:" + doc.file + "#" + cut(s.title, 100); return `<div class="card docsec" data-mark="${esc(k)}"><div class="md"><h2 style="margin-top:0">${esc(s.title)}</h2>${s.html}</div>${fbCtl(k, t("l_doc", { f: doc.file, s: s.title }))}</div>`; }).join("");
  return `<p class="sub">${esc(t("docs_sub"))}</p>${warn}${nav}${intro}${secs}`;
}

/* ---------- the cut module (docs/proposals/02-studio-client.md, 4): lists, the picture, one timeline ---------- */
function filmPath() {   // this round's film when its stop is the cut's, else the film bin/vh status names, else its proxy
  if (!D) return "";
  const g = ROUND.data || {};
  if (ROUND.gate && gateMod(ROUND.id) === "cut") {
    const want = typeof g.film === "string" ? g.film : "";
    const a = (g.assets || []).find((x) => x && (want ? x.path === want : isVideo(x.path)));
    if (want || a) return want || a.path;
  }
  const m = (D.status && D.status.media) || {};
  return m.film || m.proxy || "";
}
function TL() { return (D.studio && D.studio.timeline) || {}; }
function cutShots() {
  const T = TL(), raw = T.shots && T.shots.length ? T.shots : (D.shots.items || []);
  return raw.filter((s) => s && s.start != null && s.end != null && +s.end > +s.start).map((s) => ({ id: String(s.id), t0: +s.start, t1: +s.end, label: s.label || "", seg: s.segment || "",
    frame: s.frame || "", unsure: s.unsure || null, reads: s.reads || [], caption: s.caption || "" })).sort((a, b) => a.t0 - b.t0);
}
function cutChapters(shots) {
  const T = TL();
  const ch = (T.chapters || []).map((c) => ({ id: String(c.id != null ? c.id : c.title), title: c.title || c.name || String(c.id), t0: +(c.start != null ? c.start : c.t0), t1: +(c.end != null ? c.end : c.t1), kind: "chapter" }))
    .filter((c) => isFinite(c.t0) && isFinite(c.t1) && c.t1 > c.t0);
  if (ch.length) return ch;
  const O = D.outline.filter((o) => o.t0 != null && o.t1 != null && o.t1 > o.t0).map((o) => ({ id: String(o.id), title: o.title || String(o.id), t0: +o.t0, t1: +o.t1, kind: "seg" }));
  if (O.length) return O;
  const out = [];   // else the shots' own parts, run by run
  shots.forEach((s) => { if (!s.seg) return; const last = out[out.length - 1]; if (last && last.title === s.seg && Math.abs(last.t1 - s.t0) < 0.05) last.t1 = s.t1; else out.push({ id: s.seg, title: s.seg, t0: s.t0, t1: s.t1, kind: "part" }); });
  return out;
}

function CutModule(area) {
  const T = TL(), ST = D.studio || {}, fps = +T.fps || 30;
  const film = filmPath(), shots = cutShots(), chapters = cutChapters(shots);
  const lines = (T.narration && T.narration.length ? T.narration : T.captions || []).filter((x) => x.start != null && x.end != null).map((x, i) => ({ id: String(x.id || i + 1), t0: +x.start, t1: +x.end, text: x.text || "" }));
  const linesAreCaptions = !(T.narration && T.narration.length) && lines.length > 0;
  const M = D.music || {}, sections = (M.sections || []).filter((s) => s.end > s.start), hitsL = M.hits || [], beats = T.beats || [];
  const peaks = ST.peaks && Array.isArray(ST.peaks.peaks) && ST.peaks.peaks.length ? ST.peaks : null;
  const thumbs = ST.thumbs && Array.isArray(ST.thumbs.tiles) && ST.thumbs.tiles.length ? ST.thumbs : null;
  const findings = (ST.findings || []).filter((f) => f.t != null);
  const chk = ST.check || null;
  const V = (D.status && D.status.versions) || null, vlist = (V && V.list) || [];
  const curV = vlist.find((v) => v.state === "current" && v.film === film) || null;
  const prevV = curV ? vlist.filter((v) => v.state === "kept" && v.file && v.film === curV.film && v.id !== curV.id).slice(-1)[0] || null : null;
  const changed = curV && curV.changed && curV.changed.whole === false && Array.isArray(curV.changed.seconds) ? curV.changed.seconds.filter((s) => Array.isArray(s) && s[1] > s[0]) : [];
  const vnum = (id) => { const m = String(id || "").match(/^v(\d+)$/); return m ? t("ver_n", { n: m[1] }) : String(id || ""); };
  const thumbOf = {}; ((thumbs && thumbs.shots) || (ST.thumbs && ST.thumbs.shots) || []).forEach((s) => { if (s && s.id != null && s.file) thumbOf[String(s.id)] = s.file; });
  const shotPic = (s) => (thumbOf[s.id] ? src(thumbOf[s.id]) : s.frame && !/^https?:/i.test(s.frame) && isImage(s.frame) ? src(s.frame) : "");
  let dur = +T.duration || (thumbs && +thumbs.duration) || (shots.length ? shots[shots.length - 1].t1 : 0) || +M.duration || 0;
  const layouts = ["review", "fine", "sound"];
  let layout = store.get("desk:cut-layout");
  if (GATE && gateBase(GATE) === "3" || waitingGate() && gateMod(waitingGate()) === "cut" && !layout) layout = "review";   // gate ③ opens on the review layout
  if (!layouts.includes(layout)) layout = "review";
  let tab = "shots", zoom = 1, snapOn = store.get("desk:cut-snap") !== false, safe = false, cmp = false, wipe = 0.5;
  let SEL = null, inPt = null, stopAt = null, clockT = 0, raf = 0, simPlaying = false, simLast = 0;
  const notesOf = () => myItems().filter(([, v]) => v.t != null).map(([k, v]) => ({ kind: "mine", t: +v.t, t1: v.t1 != null ? +v.t1 : null, target: k, label: v.label || k, note: v.text || "" }));
  const agentMarks = () => gateMarks().filter((m) => m.t != null).map((m) => ({ kind: m.kind, t: +m.t, t1: m.t1 != null ? +m.t1 : null, target: m.target, label: m.id || "", note: m.note }));
  const checkMarks = () => findings.map((f, i) => ({ kind: "check", t: +f.t, t1: f.t1 != null ? +f.t1 : null, target: "time:" + (+f.t).toFixed(1), label: f.kind || "", note: f.message || "", sev: f.severity, i }));
  const allMarks = () => agentMarks().concat(checkMarks(), notesOf()).sort((a, b) => a.t - b.t);

  area.innerHTML = `<div class="cut layout-${layout}" id="cut">
    <aside class="lists" aria-label="${esc(t("m_cut"))}"><div class="ltabs" role="tablist" id="ltabs"></div><div class="lbody" id="lbody"></div></aside>
    <section class="viewer">
      <div class="readout" id="readout"></div>
      <div class="screen" id="screen"><div class="frame" id="frame"></div></div>
      <div class="transport">
        <button type="button" class="p-btn" id="cPrev" title="${esc(t("prev_shot"))}" aria-label="${esc(t("prev_shot"))}">${svg("prev")}</button>
        <button type="button" class="p-btn play" id="cPlay" title="${esc(t("play"))}" aria-label="${esc(t("play"))}">${svg("play")}</button>
        <button type="button" class="p-btn" id="cNext" title="${esc(t("next_shot"))}" aria-label="${esc(t("next_shot"))}">${svg("next")}</button>
        <span class="tc" id="cTc"></span>
        <button type="button" class="btn toggle" id="cSafe" aria-pressed="false">${esc(t("safe"))}</button>
        ${prevV ? `<button type="button" class="btn toggle" id="cCmp" aria-pressed="false">${esc(t("compare", { v: vnum(prevV.id) }))}</button>` : ""}
        <span class="seg push" role="group" aria-label="${esc(t("layout"))}">${layouts.map((l) => `<button type="button" data-lay="${l}" aria-pressed="${l === layout}">${esc(t("lay_" + l))}</button>`).join("")}</span>
      </div>
    </section>
    <section class="timeline" aria-label="timeline">
      <div class="tl-bar"><span>${esc(t("tl_hint"))}</span><span class="push"></span>
        <button type="button" class="btn" id="cN">${esc(t("next_place"))} <span class="kbd">N</span></button>
        <button type="button" class="btn toggle" id="cSnap" aria-pressed="${snapOn}">${esc(t("snap"))}</button>
        <button type="button" class="p-btn" id="zOut" title="${esc(t("zoom_out"))}" aria-label="${esc(t("zoom_out"))}">−</button><button type="button" class="p-btn" id="zIn" title="${esc(t("zoom_in"))}" aria-label="${esc(t("zoom_in"))}">+</button></div>
      <div class="tl-scroll" id="tlScroll"><div class="tl" id="tl"></div></div>
    </section></div>`;
  const root = $("#cut", area), tl = $("#tl", area), scroll = $("#tlScroll", area), screen = $("#screen", area), frame = $("#frame", area);
  let video = null, vb = null;
  if (film) {
    frame.innerHTML = `<video id="cv" src="${esc(src(film))}" preload="metadata" playsinline></video>${prevV ? `<video class="vb" id="cvb" src="${esc(src(prevV.file))}" preload="metadata" playsinline muted hidden></video><div class="wipe-line" id="wl" hidden></div><span class="wipe-l" hidden>${esc(t("ver_now", { v: vnum(curV.id) }))}</span><span class="wipe-r" hidden>${esc(vnum(prevV.id))}</span>` : ""}<div class="safe" hidden></div>`;
    video = $("#cv", frame); vb = $("#cvb", frame);
  } else {
    frame.innerHTML = `<img id="cimg" alt="">${shots.some(shotPic) ? "" : `<p class="none">${esc(t("no_film0"))}</p>`}<div class="safe" hidden></div>`;
    if (shots.some(shotPic)) screen.insertAdjacentHTML("beforeend", `<p class="screen-note">${esc(t("no_film"))}</p>`);
  }
  const nextq = document.createElement("div"); nextq.className = "nextq"; nextq.hidden = true; screen.appendChild(nextq);

  /* the clock: the film's, or a plain one over the storyboard's key frames */
  const now = () => (video ? video.currentTime || 0 : clockT);
  const playing = () => (video ? !video.paused : simPlaying);
  function seek(x, play) {
    x = Math.max(0, Math.min(x, dur || x));
    if (video) { try { video.currentTime = x; } catch (e) { /* not loaded */ } } else clockT = x;
    if (vb && cmp) { try { vb.currentTime = x; } catch (e) { /* not loaded */ } }
    tick();
    if (play) start();
  }
  function start() {
    if (stopAt != null && now() >= stopAt - 0.04) stopAt = null;
    if (video) { video.play().catch(() => {}); if (vb && cmp) vb.play().catch(() => {}); }
    else if (dur) { if (clockT >= dur - 0.01) clockT = 0; simPlaying = true; simLast = performance.now(); }
    loop();
  }
  function stop() { if (video) { video.pause(); if (vb) vb.pause(); } simPlaying = false; tick(); }
  function toggle() {
    if (playing()) return stop();
    if (SEL && SEL.t1 != null && (now() < SEL.t - 0.01 || now() >= SEL.t1 - 0.04)) { seek(SEL.t); stopAt = SEL.t1; }   // a span selected: play it
    start();
  }
  function loop() {
    cancelAnimationFrame(raf);
    const step = (ts) => {
      if (!video && simPlaying) { clockT += (ts - simLast) / 1000; simLast = ts; if (clockT >= dur) { clockT = dur; simPlaying = false; } }
      if (stopAt != null && now() >= stopAt) { stop(); seek(stopAt); stopAt = null; }
      tick();
      if (playing()) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
  }
  if (video) {
    video.addEventListener("loadedmetadata", () => { if (isFinite(video.duration) && video.duration > 0) dur = video.duration; lastShot = undefined; fit(); draw(); tick(); });
    video.addEventListener("play", loop);
    video.addEventListener("pause", () => { if (vb) vb.pause(); tick(); });
    video.addEventListener("seeked", tick);
    video.addEventListener("error", () => { frame.insertAdjacentHTML("beforeend", `<p class="none">${esc(film)}</p>`); });
  }

  /* the picture's frame keeps the film's shape inside its grey surround, so the safe area and the wipe sit on the picture */
  function fit() {
    const r = screen.getBoundingClientRect(); if (!r.width || !r.height) return;
    const ar = video && video.videoWidth ? video.videoWidth / video.videoHeight : (() => { const m = String(specGet("output")).match(/(\d{3,5})\s*[x×]\s*(\d{3,5})/); return m ? +m[1] / +m[2] : 16 / 9; })();
    let w = r.width, h = w / ar; if (h > r.height) { h = r.height; w = h * ar; }
    frame.style.width = Math.floor(w) + "px"; frame.style.height = Math.floor(h) + "px";
  }
  const ro = "ResizeObserver" in window ? new ResizeObserver(() => { fit(); }) : null;
  if (ro) ro.observe(screen); else window.addEventListener("resize", fit);

  /* what is where */
  const shotAt = (x) => shots.find((s) => x >= s.t0 - 1e-6 && x < s.t1) || null;
  const chapterAt = (x) => chapters.find((c) => x >= c.t0 && x < c.t1) || null;
  const pct = (x) => (dur ? Math.max(0, Math.min(100, (x / dur) * 100)) : 0);
  function snapPoints() {
    const P = [0, dur];
    shots.forEach((s) => P.push(s.t0, s.t1)); chapters.forEach((c) => P.push(c.t0, c.t1)); lines.forEach((l) => P.push(l.t0, l.t1));
    beats.forEach((b) => P.push(+b.t)); allMarks().forEach((m) => P.push(m.t));
    return P.filter((x) => isFinite(x));
  }
  const overRect = () => $(".over", tl).getBoundingClientRect();
  function tAt(clientX, snap) {
    const r = overRect(); let x = Math.max(0, Math.min(1, (clientX - r.left) / r.width)) * dur;
    if (snap && snapOn && dur) { const px = r.width / dur; let best = null; snapPoints().forEach((p) => { const d = Math.abs(p - x) * px; if (d < 7 && (!best || d < best.d)) best = { p, d }; }); if (best) x = best.p; }
    return x;
  }

  /* the lists on the left */
  function renderTabs() {
    const n = { shots: shots.length, notes: allMarks().filter((m) => m.kind !== "check").length + (FB.general ? 1 : 0), checks: findings.length };
    const T2 = [["shots", t("l_shots"), n.shots], ["script", linesAreCaptions ? t("l_captions") : t("l_script"), lines.length || ""], ["notes", t("l_notes"), n.notes], ["checks", t("l_checks"), n.checks]];
    $("#ltabs", area).innerHTML = T2.map(([k, name, c]) => `<button type="button" role="tab" aria-selected="${k === tab}" data-tab="${k}">${esc(name)}${c !== "" && c != null ? `<b>${c}</b>` : ""}</button>`).join("");
  }
  function shotStatus(s) {
    const M2 = allMarks(), inS = (m) => m.t >= s.t0 && m.t < s.t1;
    const mine = M2.filter((m) => m.kind === "mine" && inS(m)).length + (FB.items["shot:" + s.id] && FB.items["shot:" + s.id].status && !(FB.items["shot:" + s.id].t != null) ? 1 : 0);
    const unsure = !!s.unsure || M2.some((m) => m.kind === "least" && inS(m)), checks = M2.filter((m) => m.kind === "check" && inS(m)).length;
    return [checks ? `<em style="color:var(--live)">${esc(t("n_checks", { n: checks }))}</em>` : "", unsure ? `<em style="color:var(--wait)">${esc(t("unsure"))}</em>` : "", mine ? `<em style="color:var(--you)">${esc(t("n_notes", { n: mine }))}</em>` : ""].filter(Boolean).join(" ");
  }
  function renderList() {
    const b = $("#lbody", area); let h = ""; lastShot = undefined;
    if (tab === "shots") {
      if (!shots.length) h = `<p class="void">${esc(t("no_shots"))}</p>`;
      else {
        let last = null;
        shots.forEach((s) => {
          const c = chapterAt(s.t0 + 0.01);
          if (c && c !== last) { h += `<div class="lgroup">${esc(c.title)}</div>`; last = c; }
          const pic = shotPic(s), on = SEL && SEL.kind === "shot" && SEL.id === s.id;
          h += `<button type="button" class="lrow${on ? " sel" : ""}" data-pick="shot:${esc(s.id)}"><span class="lthumb">${pic ? `<img src="${esc(pic)}" alt="" loading="lazy">` : ""}</span><span class="lt"><b>${esc(s.id)} ${esc(s.label)}</b><span>${esc(fmt(s.t0))}–${esc(fmt(s.t1))}</span>${shotStatus(s) ? `<span>${shotStatus(s)}</span>` : ""}</span></button>`;
        });
      }
    } else if (tab === "script") {
      h = lines.length ? lines.map((l, i) => `<button type="button" class="lrow text${SEL && SEL.kind === "line" && SEL.i === i ? " sel" : ""}" data-pick="line:${i}"><span class="tc">${esc(fmt(l.t0))}</span><span class="tx">${esc(l.text)}</span></button>`).join("") : `<p class="void">${esc(t("no_narr"))}</p>`;
    } else if (tab === "notes") {
      const R = allMarks().filter((m) => m.kind !== "check");
      const who = (m) => (m.kind === "mine" ? `<em style="color:var(--you)">${esc(t("k_mine"))}</em>` : m.kind === "least" ? `<em style="color:var(--wait)">${esc(t("k_least"))}</em>` : `<em style="color:var(--wait)">${esc(t("k_listen"))}</em>`);
      h = R.map((m) => `<button type="button" class="lrow text" data-pick="mark:${esc(m.target)}" data-t="${m.t}"${m.t1 != null ? ` data-t1="${m.t1}"` : ""}><span class="tc">${esc(fmt(m.t))}</span><span class="tx">${who(m)} ${esc(m.kind === "mine" ? (m.note || m.label) : m.note)}</span></button>`).join("")
        + (FB.general ? `<div class="lrow text"><span class="tc">·</span><span class="tx"><em style="color:var(--you)">${esc(t("c_whole_note"))}</em> ${esc(FB.general)}</span></div>` : "");
      if (!h) h = `<p class="void">${esc(t("c_none_mine"))}</p>`;
    } else {
      if (!chk) h = `<p class="void">${esc(t("no_checks"))}</p>`;
      else {
        h = `<p class="meta" style="margin:4px 6px 8px">${esc(t("verdict"))} <b class="${verdictCls(chk.verdict)}">${esc(chk.verdict || "–")}</b> · ${esc(chk.video || "")}</p>${chk.stale ? `<p class="notice">${esc(t("check_stale"))}</p>` : ""}`;
        h += findings.map((f) => `<button type="button" class="lrow text" data-pick="check:${findings.indexOf(f)}"><span class="tc">${esc(fmt(f.t))}</span><span class="tx"><em style="color:var(--live)">✕ ${esc(f.severity === "fail" ? t("sev_fail") : t("sev_warn"))}</em> ${esc(f.message || f.kind || "")}</span></button>`).join("");
      }
    }
    b.innerHTML = h;
  }
  $("#ltabs", area).addEventListener("click", (e) => { const b = e.target.closest("[data-tab]"); if (!b) return; tab = b.dataset.tab; renderTabs(); renderList(); });
  $("#lbody", area).addEventListener("click", (e) => { const b = e.target.closest("[data-pick]"); if (b) pickThing(b.dataset.pick, b); });

  /* the timeline */
  function lane(cls, label, inner, group, empty) {
    return `<div class="lane ${cls}" data-g="${group || ""}"><span class="lab">${esc(label)}</span><div class="trk">${inner || (empty ? `<span class="lane-empty">${esc(empty)}</span>` : "")}</div></div>`;
  }
  const trackW = () => Math.max(200, (scroll.clientWidth || 800) * zoom - 92);   // less the lanes' label column and the right padding
  function rulerTicks() {
    const w = trackW(), steps = [0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600];
    const step = steps.find((s) => (w / (dur || 1)) * s >= 64) || 600;
    let h = "";
    for (let x = 0; x <= dur + 1e-6; x += step / 5) {
      const long = Math.abs(x / step - Math.round(x / step)) < 1e-6;
      h += `<span class="tk${long ? " long" : ""}" style="left:${pct(x)}%">${long && pct(x) < 97 ? `<span>${esc(fmt(x).replace(/\.0$/, ""))}</span>` : ""}</span>`;
    }
    return h;
  }
  function wave() {
    if (!peaks) return "";
    const P = peaks.peaks, n = P.length, d = +peaks.duration || dur, sc = d && dur ? d / dur : 1;
    let top = "", bot = "";
    P.forEach((p, i) => { const x = ((i / n) * 1000 * sc).toFixed(1), a = Math.max(-1, Math.min(1, +p[1] || 0)), b2 = Math.max(-1, Math.min(1, +p[0] || 0)); top += `${i ? "L" : "M"}${x} ${(50 - a * 48).toFixed(1)}`; bot = `L${x} ${(50 - b2 * 48).toFixed(1)}` + bot; });
    return `<svg class="wav" viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true"><path d="${top}${bot}Z"/></svg>`;
  }
  function draw() {
    if (!dur) dur = 1;
    const blk = (cls, a, b, inner, data, title) => `<div class="blk ${cls}" style="left:${pct(a)}%;width:${Math.max(0.15, pct(b) - pct(a))}%"${data ? ` data-pick="${esc(data)}"` : ""}${title ? ` title="${esc(title)}"` : ""}>${inner}</div>`;
    const chapH = chapters.map((c) => blk("chap" + (SEL && (SEL.kind === "chapter" || SEL.kind === "seg" || SEL.kind === "part") && SEL.id === c.id ? " sel" : ""), c.t0, c.t1, esc(c.title), (c.kind === "chapter" ? "chapter:" : c.kind === "seg" ? "seg:" : "part:") + c.id, c.title)).join("");
    const AM = allMarks();
    const shotH = shots.map((s) => { const pic = shotPic(s), st = s.unsure || AM.some((m) => m.kind === "least" && m.t >= s.t0 && m.t < s.t1) ? "flag" : AM.some((m) => m.kind === "mine" && m.t >= s.t0 && m.t < s.t1) ? "note" : "";
      return blk("shot" + (SEL && SEL.kind === "shot" && SEL.id === s.id ? " sel" : ""), s.t0, s.t1, `${pic ? `<img src="${esc(pic)}" alt="" loading="lazy">` : ""}<i class="s ${st}"></i><b>${esc(s.id)}</b>${esc(s.label)}`, "shot:" + s.id, `${s.id} ${s.label} · ${fmt(s.t0)}–${fmt(s.t1)}`); }).join("");
    const lineH = lines.map((l, i) => blk("line" + (SEL && SEL.kind === "line" && SEL.i === i ? " sel" : ""), l.t0, l.t1, esc(l.text), "line:" + i, `${l.id} · ${l.text}`)).join("");
    const pxPerS = trackW() / dur;
    const beatH = beats.filter((b) => b.downbeat || pxPerS * (60 / (+T.bpm || 120)) > 10).map((b) => `<i class="bl${b.downbeat ? " down" : ""}" style="left:${pct(+b.t)}%"></i>`).join("");
    const secH = sections.map((s) => `<span class="sec" style="left:${pct(s.start)}%;width:${pct(s.end) - pct(s.start)}%" title="${esc(s.name)}">${esc(s.label || s.name)}</span>`).join("");
    const hitH = hitsL.map((h) => `<i class="hit" style="left:${pct(+h.t)}%" title="${esc((h.part || "") + " " + fmt(h.t))}"></i>`).join("");
    const markH = AM.map((m) => `${m.t1 != null ? `<span class="span-mark ${m.kind}" style="left:${pct(m.t)}%;width:${pct(m.t1) - pct(m.t)}%"></span>` : ""}<button type="button" class="pin ${m.kind === "mine" ? "note" : m.kind}" style="left:${pct(m.t)}%" data-pick="mark:${esc(m.target)}" data-t="${m.t}"${m.t1 != null ? ` data-t1="${m.t1}"` : ""} title="${esc(fmt(m.t) + " · " + (m.note || m.label))}" aria-label="${esc(fmt(m.t) + " " + (m.note || m.label))}"></button>`).join("");
    const diffH = changed.map((s) => `<span class="diff" style="left:${pct(s[0])}%;width:${Math.max(0.3, pct(s[1]) - pct(s[0]))}%">${esc(t("diff_label", { v: vnum(curV.id) }))}</span>`).join("")
      || (curV && curV.changed && curV.changed.whole ? `<span class="diff" style="left:0;width:100%">${esc(vnum(curV.id))} · ${esc(t("whole_render"))}</span>` : "");
    const grp = (k, name) => `<div class="grp" data-grp="${k}" role="button" tabindex="0">${esc(name)}</div>`;
    tl.style.width = zoom * 100 + "%";
    tl.innerHTML = `<div class="lane ruler-l"><span class="lab"></span><div class="trk" data-ruler>${rulerTicks()}</div></div>`
      + grp("pic", t("g_pic")) + lane("chap", t("ln_chap"), chapH, "pic", t("e_chap")) + lane("shots", t("ln_shots"), shotH, "pic", t("e_shots"))
      + grp("sound", t("g_sound")) + lane("voice extra", t("ln_voice"), lineH, "sound", t("e_voice")) + lane("music extra", t("ln_music"), beatH + secH, "sound", t("e_music"))
      + (hitsL.length ? lane("thin extra", t("ln_hits"), hitH, "sound") : "") + lane("wave extra", t("ln_wave"), wave(), "sound", t("e_wave"))
      + grp("review", t("g_review")) + lane("marks", t("ln_marks"), markH, "review", t("e_marks")) + lane("thin extra", t("ln_diff"), diffH, "review", t("e_diff"))
      + `<div class="over" aria-hidden="true"><div class="selr" hidden><span class="cap"></span></div><div class="tl-ph"><span class="cap"></span></div></div><div class="hover-tip" hidden></div>`;
    if (layout !== "review") closed.forEach((g) => { const el = $(`.grp[data-grp="${g}"]`, tl); if (el) el.classList.add("closed"); $$(`.lane[data-g="${g}"]`, tl).forEach((x) => { x.hidden = true; }); });
    paintSel(); tick();
  }
  const closed = new Set(store.get("desk:cut-closed") || []);
  tl.addEventListener("click", (e) => {
    const p = e.detail === 0 && e.target.closest("[data-pick]");   // Enter or Space on a pin
    if (p) { pickThing(p.dataset.pick, p); return; }
    const g = e.target.closest(".grp"); if (!g) return;
    const k = g.dataset.grp; if (closed.has(k)) closed.delete(k); else closed.add(k);
    store.set("desk:cut-closed", [...closed]); draw();
  });
  tl.addEventListener("keydown", (e) => { const g = e.target.closest(".grp"); if (g && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); g.click(); } });

  /* the playhead, the readout, the picture when there is no film */
  let lastShot = null, lastPlaying = null;
  function tick() {
    const x = now(), ph = $(".tl-ph", tl);
    if (playing() !== lastPlaying) { lastPlaying = playing(); $("#cPlay", area).innerHTML = svg(lastPlaying ? "pause" : "play"); }
    if (ph) { ph.style.left = pct(x) + "%"; $(".cap", ph).textContent = fmt(x); }
    $("#cTc", area).innerHTML = `${esc(tcode(x, fps))} <i>/ ${esc(tcode(dur, fps))}</i>`;
    const s = shotAt(x);
    if (s !== lastShot || !$("#readout", area).innerHTML) {
      lastShot = s;
      const size = video && video.videoWidth ? `${video.videoWidth}×${video.videoHeight}` : (String(specGet("output")).match(/\d{3,5}\s*[x×]\s*\d{3,5}/) || [""])[0].replace(/\s/g, "").replace("x", "×");
      const ver = curV ? vnum(curV.id) : (D.status && D.status.media && D.status.media.version) ? vnum(D.status.media.version) : "";
      const isProxy = film && D.status && D.status.media && film === D.status.media.proxy && film !== D.status.media.film;
      $("#readout", area).innerHTML = (s ? `<span><b>${esc(s.id)}</b> ${esc(s.label)}</span>${s.reads && s.reads.length ? `<span>${esc(t("reads"))}${COLON()}${esc(s.reads.join(" → "))}</span>` : s.caption ? `<span>${esc(cut(s.caption, 60))}</span>` : ""}` : "<span>·</span>")
        + `<span class="ver">${esc([size, fps + " FPS", ver, isProxy ? t("proxy") : ""].filter(Boolean).join(" · "))}</span>`;
      if (!video) { const img = $("#cimg", frame); const pic = s ? shotPic(s) : ""; if (img) { if (pic) { if (img.getAttribute("src") !== pic) img.src = pic; img.hidden = false; } else img.hidden = true; } }
      if (tab === "shots") $$("#lbody .lrow", area).forEach((r) => r.classList.toggle("now", !!s && r.dataset.pick === "shot:" + s.id));
    }
    if (tab === "script") { const li = lines.findIndex((l) => x >= l.t0 && x < l.t1); $$("#lbody .lrow", area).forEach((r, i) => r.classList.toggle("now", i === li)); }
    if (vb && cmp && Math.abs((vb.currentTime || 0) - x) > 0.12 && !(video && !video.paused && !vb.paused)) { try { vb.currentTime = x; } catch (e) { /* not loaded */ } }
  }
  function paintSel() {
    const r = $(".selr", tl); if (!r) return;
    if (!SEL || SEL.t1 == null) {
      if (SEL && SEL.kind === "time") { r.hidden = false; r.style.left = pct(SEL.t) + "%"; r.style.width = "1px"; $(".cap", r).textContent = SEL.label; }
      else r.hidden = true;
      return;
    }
    r.hidden = false; r.style.left = pct(SEL.t) + "%"; r.style.width = Math.max(0.2, pct(SEL.t1) - pct(SEL.t)) + "%";
    $(".cap", r).textContent = `${SEL.label} · ${(SEL.t1 - SEL.t).toFixed(1)} s`;
  }

  /* selecting: a second, a span, a shot, a chapter, a line, a mark; the note box follows */
  function select(s, play) {
    SEL = s;
    if (s) {
      seek(s.t);
      const kind = s.kind, a = +(+s.t).toFixed(1), b = s.t1 != null ? +(+s.t1).toFixed(1) : null;
      let scope;
      if (kind === "shot") scope = { target: "shot:" + s.id, label: t("l_shot", { x: s.id + (s.name ? " " + s.name : "") }), t: a, t1: b };
      else if (kind === "seg") scope = { target: "seg:" + s.id, label: t("l_seg", { i: s.id, x: s.name }), t: a, t1: b };
      else if (kind === "chapter") scope = { target: "chapter:" + s.id, label: t("chapter_label", { x: s.name }), t: a, t1: b };
      else if (kind === "mark") scope = { target: s.target, label: s.name, t: a, t1: b };
      else if (b != null && b - a >= 0.1) scope = { target: `range:${a}-${b}`, label: s.name || t("range_label", { a: fmt(a), b: fmt(b) }), t: a, t1: b };
      else scope = { target: "time:" + a, label: t("film_label", { t: fmt(a) }), t: a };
      setScope(scope);
      if (play) { stopAt = s.t1; start(); }
    } else setScope(null);
    const a = document.activeElement, keep = a && a.dataset && a.dataset.pick && area.contains(a) ? [a.closest("#lbody") ? "#lbody" : "#tl", a.dataset.pick] : null;
    draw(); renderList();
    if (keep) { const n = $(`${keep[0]} [data-pick="${CSS.escape(keep[1])}"]`, area); if (n) n.focus({ preventScroll: true }); }   // the keyboard stays where it was
  }
  function pickThing(p, el) {
    const [kind, ...rest] = p.split(":"), id = rest.join(":");
    if (kind === "shot") { const s = shots.find((x) => x.id === id); if (s) select({ kind: "shot", id: s.id, name: s.label, t: s.t0, t1: s.t1, label: `${s.id} ${s.label}` }); }
    else if (kind === "chapter" || kind === "seg" || kind === "part") { const c = chapters.find((x) => x.id === id); if (c) select({ kind: c.kind === "part" ? "range" : c.kind, id: c.id, name: c.title, t: c.t0, t1: c.t1, label: c.title }); }
    else if (kind === "line") { const i = +id, l = lines[i]; if (l) select({ kind: "line", i, id: l.id, name: t("l_line", { x: l.id }), t: l.t0, t1: l.t1, label: t("l_line", { x: l.id }) }); }
    else if (kind === "check") { const f = findings[+id]; if (f) select({ kind: f.t1 != null ? "range" : "time", t: +f.t, t1: f.t1 != null ? +f.t1 : null, name: `${t("k_check")} ${f.kind || ""}`.trim(), label: fmt(f.t) }); }
    else if (kind === "mark") {
      const m = allMarks().find((x) => x.target === id && (!el || el.dataset.t == null || Math.abs(x.t - +el.dataset.t) < 0.01)) || allMarks().find((x) => x.target === id);
      if (m) select(m.kind === "check" ? { kind: m.t1 != null ? "range" : "time", t: m.t, t1: m.t1, name: m.label, label: fmt(m.t) }
        : { kind: "mark", target: m.target, t: m.t, t1: m.t1, name: m.kind === "mine" ? m.label : m.kind === "listen" ? t("sound_label", { t: fmt(m.t) }) : t("l_least", { x: m.label || fmt(m.t) }), label: m.kind === "mine" ? m.label : fmt(m.t) });
    }
  }
  let drag = null;
  tl.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 || e.target.closest(".grp")) return;
    const trk = e.target.closest(".trk"); if (!trk) return;
    drag = { x0: e.clientX, t0: tAt(e.clientX, true), pick: e.target.closest("[data-pick]"), moved: false, id: e.pointerId };
    tl.setPointerCapture(e.pointerId);
  });
  tl.addEventListener("pointermove", (e) => {
    const tip = $(".hover-tip", tl);
    if (tip && dur && !drag) hoverTip(e, tip);
    if (!drag) return;
    if (!drag.moved && Math.abs(e.clientX - drag.x0) > 4) drag.moved = true;
    if (drag.moved) {
      const x = tAt(e.clientX, true), a = Math.min(drag.t0, x), b = Math.max(drag.t0, x);
      SEL = { kind: "range", t: a, t1: b, label: `${fmt(a)}–${fmt(b)}` }; paintSel();
      if (!playing()) { if (video) { try { video.currentTime = x; } catch (err) { /* not loaded */ } } else clockT = x; tick(); }
    }
  });
  tl.addEventListener("pointerleave", () => { const tip = $(".hover-tip", tl); if (tip) tip.hidden = true; });
  const endDrag = (e) => {
    if (!drag) return;
    const d = drag; drag = null;
    if (d.moved) { const s = SEL; if (s && s.t1 - s.t >= 0.1) select({ kind: "range", t: s.t, t1: s.t1, label: s.label }); else select({ kind: "time", t: s ? s.t : d.t0, label: fmt(s ? s.t : d.t0) }); return; }
    if (d.pick && e.type === "pointerup") return pickThing(d.pick.dataset.pick, d.pick);
    const x = d.t0; select({ kind: "time", t: x, label: fmt(x) });
  };
  tl.addEventListener("pointerup", endDrag); tl.addEventListener("pointercancel", endDrag);
  function hoverTip(e, tip) {
    const r = overRect(); if (e.clientX < r.left || e.clientX > r.right) { tip.hidden = true; return; }
    const x = tAt(e.clientX, false), s = shotAt(x);
    let fr = "";
    if (thumbs) {
      const T3 = thumbs.tiles; let best = T3[0]; for (const q of T3) { if (Math.abs(q.t - x) < Math.abs(best.t - x)) best = q; }
      const sh = thumbs.sheets[best.sheet], W = 176, sc = W / thumbs.tile[0];
      if (sh) fr = `<span class="fr" style="background-image:url('${esc(src(sh.file))}');background-size:${sh.size[0] * sc}px ${sh.size[1] * sc}px;background-position:-${best.x * sc}px -${best.y * sc}px;height:${Math.round(thumbs.tile[1] * sc)}px"></span>`;
    } else if (s && shotPic(s)) fr = `<span class="fr" style="background-image:url('${esc(shotPic(s))}');background-size:cover;background-position:center"></span>`;
    tip.innerHTML = `${fr}${esc(fmt(x))}${s ? " · " + esc(s.id) : ""}`;
    tip.hidden = false;
    tip.style.left = Math.min(Math.max(e.clientX, 100), window.innerWidth - 100) + "px"; tip.style.top = (e.clientY - 12) + "px";
  }

  /* N: the next place to look at */
  function nextPlace() {
    const x = now() + 0.05, m = allMarks().find((q) => q.t > x);
    if (!m) { flash(t("no_next")); return; }
    pickThing("mark:" + m.target, { dataset: { t: String(m.t) } });
    flash(t("next_q", { x: `${fmt(m.t)} ${cut(m.note || m.label, 40)}` }));
  }
  function flash(msg) { nextq.textContent = msg; nextq.hidden = false; clearTimeout(nextq._h); nextq._h = setTimeout(() => { nextq.hidden = true; }, 2600); }
  function jumpShot(dir) {
    const x = now(); let P = shots.map((s) => s.t0).concat(shots.length ? [shots[shots.length - 1].t1] : []);
    if (!P.length) return seek(x + dir * 5);
    P = [0].concat(P).sort((a, b) => a - b);
    const n = dir > 0 ? P.find((p) => p > x + 0.05) : P.slice().reverse().find((p) => p < x - 0.3);
    seek(n != null ? n : dir > 0 ? dur : 0, playing());
  }
  function setLayout(l) {
    layout = l; store.set("desk:cut-layout", l);
    root.className = "cut layout-" + l;
    $$("[data-lay]", area).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lay === l)));
    if (l === "sound" && tab === "shots") { tab = "script"; renderTabs(); renderList(); }
    setTimeout(() => { fit(); draw(); }, 0);
  }
  $("#cPlay", area).addEventListener("click", toggle);
  $("#cPrev", area).addEventListener("click", () => jumpShot(-1));
  $("#cNext", area).addEventListener("click", () => jumpShot(1));
  $("#cN", area).addEventListener("click", nextPlace);
  $("#cSnap", area).addEventListener("click", (e) => { snapOn = !snapOn; store.set("desk:cut-snap", snapOn); e.currentTarget.setAttribute("aria-pressed", String(snapOn)); });
  $("#cSafe", area).addEventListener("click", (e) => { safe = !safe; e.currentTarget.setAttribute("aria-pressed", String(safe)); $(".safe", frame).hidden = !safe; });
  $("#zIn", area).addEventListener("click", () => { zoom = Math.min(16, zoom * 1.6); draw(); centerOn(now()); });
  $("#zOut", area).addEventListener("click", () => { zoom = Math.max(1, zoom / 1.6); draw(); centerOn(now()); });
  $$("[data-lay]", area).forEach((b) => b.addEventListener("click", () => setLayout(b.dataset.lay)));
  function centerOn(x) { const w = tl.scrollWidth; scroll.scrollLeft = Math.max(0, (x / (dur || 1)) * w - scroll.clientWidth / 2); }
  if (prevV && vb) {   // a read-only wipe between this version and the one kept before it
    const wl = $("#wl", frame), labs = $$(".wipe-l,.wipe-r", frame);
    const place = () => { vb.style.clipPath = `inset(0 0 0 ${wipe * 100}%)`; wl.style.left = wipe * 100 + "%"; };
    $("#cCmp", area).addEventListener("click", (e) => {
      cmp = !cmp; e.currentTarget.setAttribute("aria-pressed", String(cmp));
      vb.hidden = wl.hidden = !cmp; labs.forEach((x) => { x.hidden = !cmp; });
      if (cmp) { try { vb.currentTime = now(); } catch (err) { /* not loaded */ } if (playing()) vb.play().catch(() => {}); place(); } else vb.pause();
    });
    let wd = false;
    wl.addEventListener("pointerdown", (e) => { wd = true; wl.setPointerCapture(e.pointerId); e.stopPropagation(); });
    wl.addEventListener("pointermove", (e) => { if (!wd) return; const r = frame.getBoundingClientRect(); wipe = Math.max(0.02, Math.min(0.98, (e.clientX - r.left) / r.width)); place(); });
    wl.addEventListener("pointerup", () => { wd = false; });
  }
  screen.addEventListener("click", (e) => { if (!e.target.closest(".wipe-line")) toggle(); });

  const keys = (e) => {
    if (e.defaultPrevented || MOD !== "cut" || typing() || e.metaKey || e.ctrlKey || e.altKey || !$("#search").hidden || !$("#confirm").hidden) return;
    const k = e.key;
    if (k === " ") { if (document.activeElement && /^(BUTTON|A|SUMMARY)$/.test(document.activeElement.tagName) && !document.activeElement.closest(".transport,.tl,.lists")) return; e.preventDefault(); spaceDown = true; toggle(); }
    else if (k === "ArrowLeft" || k === "ArrowRight") { if ((document.activeElement || {}).type === "radio") return; e.preventDefault(); if (e.shiftKey) seek(now() + (k === "ArrowRight" ? 1 : -1)); else jumpShot(k === "ArrowRight" ? 1 : -1); }
    else if (k === "," || k === ".") { e.preventDefault(); stop(); seek(now() + (k === "." ? 1 : -1) / fps); }
    else if (k === "i" || k === "I") { e.preventDefault(); inPt = now(); select({ kind: "time", t: inPt, label: fmt(inPt) }); }
    else if (k === "o" || k === "O") { e.preventDefault(); const x = now(), a = inPt != null ? Math.min(inPt, x) : SEL ? Math.min(SEL.t, x) : 0, b = inPt != null ? Math.max(inPt, x) : x; if (b - a >= 0.1) select({ kind: "range", t: a, t1: b, label: `${fmt(a)}–${fmt(b)}` }); inPt = null; }
    else if (k === "n" || k === "N") { e.preventDefault(); nextPlace(); }
    else if (k === "c" || k === "C") { e.preventDefault(); stop(); select({ kind: "time", t: now(), label: fmt(now()) }); $("#say").focus(); }
    else if (k === "Escape") { if (SEL) { e.preventDefault(); select(null); } }
    else if (k === "Home") { e.preventDefault(); seek(0); } else if (k === "End") { e.preventDefault(); seek(dur); }
  };
  let spaceDown = false;
  const spaceUp = (e) => { if (e.key === " ") setTimeout(() => { spaceDown = false; }, 0); };
  const eatClick = (e) => { if (spaceDown && e.detail === 0) { e.preventDefault(); e.stopImmediatePropagation(); } };
  document.addEventListener("keydown", keys);
  document.addEventListener("keyup", spaceUp);
  area.addEventListener("click", eatClick, true);

  renderTabs(); renderList(); draw(); fit();
  if (!thumbs && film) $(".tl-bar span", area).title = t("no_thumbs");
  return {
    refresh() { renderTabs(); renderList(); draw(); },
    goto(target, tt, t1) {
      const m = allMarks().find((x) => x.target === target);
      if (m) return pickThing("mark:" + target, { dataset: { t: String(m.t) } });
      if (target.startsWith("shot:")) return pickThing(target);
      if (target.startsWith("chapter:") || target.startsWith("seg:")) return pickThing(target);
      if (tt != null) select(t1 != null ? { kind: "range", t: tt, t1, label: `${fmt(tt)}–${fmt(t1)}` } : { kind: "time", t: tt, label: fmt(tt) });
    },
    destroy() { document.removeEventListener("keydown", keys); document.removeEventListener("keyup", spaceUp); area.removeEventListener("click", eatClick, true); cancelAnimationFrame(raf); if (video) video.pause(); if (vb) vb.pause(); if (ro) ro.disconnect(); else window.removeEventListener("resize", fit); },
  };
}

$("#lang").addEventListener("click", () => {
  const n = LANG === "zh" ? "en" : "zh"; try { localStorage.setItem("desk:lang", n); } catch (e) { /* no storage */ }
  setLang(n);
  if (D) { const key = PKEY; leaveProject(); D = null; PKEY = ""; $("#composer").dataset.ready = ""; showProject(Object.assign(parse(), { key })); }
  else route();
});

setLang(pickLang());
OVH.theme(document.documentElement.getAttribute("data-theme"));
route();
