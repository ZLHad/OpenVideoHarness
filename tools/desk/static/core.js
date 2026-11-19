"use strict";
/* What the console (studio.js) and a static review page (static.js) share: the words (STR; the other modules add theirs in
   modules.js), escaping and formatting, the film's flow of stops and its lamps, a module's kicker and sub-tabs, and the few
   readers of the project's data the modules use. Nothing here touches the page when it loads; the host declares the state
   these functions read (D, PKEY, SUB) and runs them. */
const STR = {
  zh: {
    revisions: "复审", revision_pending: "待复审", revision_approved: "复审通过", revision_changes_requested: "待修改",
    revision_compare: "查看修改对比", revision_before: "修改前", revision_after: "修改后", revision_sound: "试听音轨",
    revision_play: "播放这一段", revision_seek: "两版共用的播放位置", revision_gone: "留下的那一版视频被挪走或改过了，没法对比。",
    revision_load_error: "两版视频放不出来：让 agent 看看留下的两版还在不在。", revision_reply: "对改后版本的意见",
    revision_change: "要求再改", revision_sent: "复审意见已保存", revision_send_error: "复审意见尚未保存",
    revision_close: "关闭", revision_pause: "暂停",
    brand: "Studio", nokey: "这一页现在只能看。", reopen: "在 Studio 窗口里打开", reopened: "Studio 的窗口在前面了",
    reopen_failed: "Studio 的窗口没能打开：点 OVH Studio 图标，或者让 agent 再打开一次 Studio",
    taken: "这台电脑上有别的程序抢在这个窗口前面连上了 Studio，已经换过两次窗口。让 agent 重启 Studio 再试。", noServer: "读不到这支片子。这一页要在这台电脑的 Studio 里打开。", loading: "…",
    m_new: "新建", new_tip: "写一句想做什么，发给 agent，它开一支新片子",
    m_space: "空间", m_idea: "立意", m_outline: "大纲", m_board: "分镜", m_sound: "声音", m_cut: "成片", m_ship: "交付", m_assets: "素材", m_ledger: "决定",
    f_done: "已定", f_wait: "等你看", wait_ear: "等你听", f_agent: "agent 在做", f_todo: "没开始", f_open: "还没定", f_skip: "跳过", f_off: "随初版看", f_norec: "没有记录",
    search: "搜片子", search_ph: "片名、文件夹或类型，回车打开", no_match: "没有对上的片子", lang: "EN", lang_tip: "Switch to English", themes: "主题",
    th_darkfield: "暗场", th_prism: "棱镜", th_bridge: "舰桥", skip: "跳到内容", rail: "模块", flow: "这支片子的几站",
    ask_prefix: "用 OpenVideoHarness 做一支片子：",
    films: "片子", home_meta: "{n} 支 · {w} 支等你", home_meta0: "{n} 支", g_wait: "等你看",
    no_projects: "这里还没有片子。在右边写一句想做什么，agent 就开一支。",
    st_waiting_person: "等你看", st_waiting_agent: "agent 在做", st_in_progress: "在做", st_delivered: "已交付", st_paused: "暂停",
    st_no_record: "没有审阅记录", st_not_started: "没开始", st_skipped: "跳过", st_done: "已定",
    agent_list: "agent 在做",
    col_round: "这一站", col_notes: "随手记的意见", live_on: "agent 在等你交",
    live_on_tip: "交给 agent 以后它会接着做",
    c_decide: "等你定", c_rec: "不选就按推荐", c_least: "agent 没把握的", c_listen: "请你听", c_mine: "我的意见", c_next: "下一步", c_running: "正在做", c_spend: "花费",
    c_spent: "已花 {s}", c_of: "预算 {l}", c_none_mine: "还没写。点一下时间轴或一个镜头，在下面写一句。", who_agent: "agent", who_person: "你", who_nobody: "已交付",
    submit_round: "交给 agent", c_whole_note: "整体", round_quiet: "现在没有等你定的事。", static_page: "单独打开审阅页", recent: "最近定下的", agent_decided_k: "agent 定的 · {x}",
    at: "对着", whole: "这一页", whole_film: "整片", to_whole: "取消选中",
    c_ph: "对{x}的意见写在这里，点“交给 agent”时一起交出去", note_add: "记下", note_keys: "⌘↩", noted: "记下了：{x}", del: "删",
    d_dropped: "这 {n} 条写不进去，不会交给 agent（对着的东西认不出，或者字太长）",
    d_title: "交给 agent 之前看一眼", d_decisions: "决定", d_items: "意见", by_rec: "（你没选，按推荐）", d_none: "你没写具体意见。",
    general: "整体意见（可选）", general_ph: "比如：整体节奏偏慢；开场很好……", submit: "交给 agent", cancel: "再看看", preview: "会交给 agent 的原文",
    submit_hint: "交给 agent 以后，它下次开工会先看你的意见。",
    sent_live: "交给 agent 了，它已经在接着做", sent: "交给 agent 了",
    hint_live: "交给 agent 了。它正等着，已经接着做了。",
    hint_idle: "交给 agent 了。它下次开工会先看你的意见；想让它马上看，在对话里说一声。",
    offline: "没有连上本地服务：回复已复制，粘贴到对话里即可", offline2: "没有连上本地服务：请复制下面的内容", moved: "没有交成功：这个地址现在指的已经不是你打开的那支片子了。重新载入页面，再交一次（草稿还在）。",
    reply_head: "《{p}》{r} 的回复", rest: "没写意见的都算通过。", notes_round: "随手记的意见", overall: "整体",
    submitted: "这一站已经交过一次（{at}）。再交，会多交一份，agent 两份都会看到。", new_round: "agent 发来了新的一页：{g}",
    sent_n: "已交 {n} 条意见、{d} 件决定（{at}）。之后再交，只发新写的。", proj_ph: "<项目>", ns_raw: "agent 那边的原话",
    past: "这是之前的审阅页（{g}），只能看。", to_round: "回到这一站 →", page_of: "看当时的审阅页 →", st_ok: "可以", st_change: "要改", st_ask: "疑问",
    fb_ok: "✓ 可以", fb_change: "✎ 要改", fb_ask: "? 疑问", fb_def: "不点就算通过", ph_change: "哪里要改、为什么", ph_ask: "哪里没看懂？",
    ph_suggest: "直接改成……（可选）", agree: "✓ 同意", overturn: "改", def_agree: "不点就算同意",
    fact_ok: "✓ 对", fact_bad: "✎ 有问题", fact_unsure: "? 拿不准", fact_def: "不点就算没核对",
    l_least: "没把握：{x}", l_deleg: "agent 替你定的：{x}", l_shot: "镜头 {x}", l_seg: "大纲 第 {i} 段 {x}", l_line: "旁白 {x}",
    film_label: "成片 {t}", range_label: "成片 {a}–{b}", sound_label: "声音 {t}", chapter_label: "章节 {x}",
    // the cut module
    l_shots: "镜头", l_script: "旁白稿", l_captions: "字幕", l_notes: "标记", l_checks: "检查",
    no_shots: "还没有镜头表。", no_narr: "还没配旁白。",
    no_checks: "还没检查过。", check_stale: "检查过后片子又改了，结果可能不准。", verdict: "结论",
    n_notes: "{n} 条意见", unsure: "没把握", n_checks: "{n} 处检查", reads: "要看到", ver_n: "第 {n} 版", proxy: "预览版",
    no_film_frames: "还没出成片，先看分镜的关键帧。", no_film_sheet: "还没出成片，先看联系表。", no_film0: "还没出成片。", film_gone_frames: "成片不在本机（可能挪到了别的盘），先看分镜的关键帧。", film_gone_sheet: "成片不在本机（可能挪到了别的盘），先看联系表。", film_gone0: "成片不在本机（可能挪到了别的盘）。",
    safe: "安全框", compare: "和{v}对比", ver_now: "{v} · 现在", lay_review: "审片", lay_fine: "精修", lay_sound: "听声音", layout: "布局",
    tl_hint: "点哪，播放头就到哪；点在镜头、旁白或标记上，右边的意见就对着它。", h_mouse: "鼠标", h_keys: "键盘", tl_more: "旁白、音乐和波形在这两个布局里：",
    snap: "对齐镜头", snap_tip: "Shift + 拖选一段时，贴到镜头边、旁白和标记上", g_fold: "收起这一组", g_unfold: "展开这一组", g_folded: "已收起", zoom_in: "放大", zoom_out: "缩小", play: "播放 / 暂停（空格）", prev_shot: "上一个镜头（←）", next_shot: "下一个镜头（→）",
    g_pic: "画面", g_sound: "声音", g_review: "审阅", ln_chap: "章节", ln_shots: "镜头", ln_voice: "旁白", ln_music: "音乐", ln_hits: "卡点", ln_wave: "波形", ln_marks: "标记", ln_diff: "这一版改了",
    e_chap: "没有章节", e_shots: "没有镜头表", e_voice: "没有旁白", e_music: "没有配乐", e_wave: "还没有波形",
    e_diff: "这一版没记下改了哪里（只有局部重新渲染的版本会记）", e_marks: "还没有标记", whole_render: "整支重渲",
    diff_label: "{v} 改了这里", next_q: "下一处 · {x}", no_next: "后面没有要看的了", k_least: "agent 没把握", k_listen: "请你听", k_check: "检查发现的", k_mine: "我的意见",
    sev_fail: "没过", sev_warn: "注意", no_thumbs: "还没做缩略图：拖动时看不到每一秒的画面",
    // the other modules (the desk's views, moved in)
    sub_outline: "大纲", sub_script: "字幕 / 旁白", sub_facts: "事实", sub_check: "检查", sub_versions: "版本", sub_decisions: "决定", sub_history: "历史", sub_docs: "文档",
    concept: "立意", spine: "故事线", motif: "贯穿全片的", end: "看完能记住", spec: "规格", outline_tip: "点色块跳到那一段",
    seg_n: "第 {i} 段", know: "看完知道 / 感到", visual: "关键画面", seg_caps: "这一段的 {n} 条", to_script: "去逐条看 →", bars: "第 {b} 小节",
    no_outline: "大纲还没写成表格，下面是原文。", no_brief: "还没写简报。",
    script_sub: "{n} 条，按大纲分段。标黄、标红的读得偏快。",
    f_all: "全部", f_mine: "我标过的", f_terms: "带术语的", f_facts: "带出处编号的", f_fast: "可能读不完的",
    no_script: "字幕稿还没写成表格，下面是原文。", no_script_file: "还没有字幕稿和旁白稿。",
    other_seg: "没对上大纲的", per_s: "/秒", chars: "{n} 字 · {s} s", none_match: "没有符合的条目。", l_cap: "字幕 {x}", l_vo: "旁白 {x}", term: "术语",
    board_sub: "点画面播这一镜。标黄的是 agent 没把握的镜头。", no_shot_caption: "（这一镜没有字幕）", transition: "转场：", unsure_x: "我没把握：",
    no_board: "还没有镜头表，下面是分镜稿原文。", no_board_file: "还没有分镜。", no_video: "（没有可播放的视频，只看关键帧）",
    sound_sub: "agent 听不见，只能看谱面和响度；这一页请你用耳朵。{bpm} BPM，{d} s。", comment_at: "在 {t} 写意见",
    sec_tip: "色块是乐段，点一下从那里播；刻度是落在画面动作上的音", listen: "请你听这几处", your_sound: "你对声音的意见",
    none_sound: "还没有。播到哪里觉得不对，就点上面的“在 … 写意见”。", roll: "谱面和响度（每一行是一件乐器，颜色越深越响）",
    no_music: "还没有配乐。", no_audio: "没有找到能播的音频。",
    facts_sub: "上屏的说法和它的出处。重点看有没有简化到错。", todo: "还没核实的", th_id: "#", th_claim: "素材（原文）",
    th_screen: "上屏说法", th_src: "出处", th_you: "你看", dropped: "（已不用）", l_fact: "事实 {x}",
    no_facts: "素材清单还没写成表格，下面是原文。", no_notes: "还没有素材清单。",
    ledger_sub: "每件事谁定、定了什么。不同意就写一句。", th_what: "事", th_who: "谁拍板", th_status: "现在",
    agent_n: "agent 替你定的（{n}）", superseded: "已经作废的（{n}）", why: "理由", undo: "改它要花", l_led: "决定 {x}",
    no_ledger: "决定记录还没写成表格，下面是原文。", no_dec: "还没有决定记录。",
    history_sub: "每一站你说的原话，和之后定了、改了什么。", desk_subs: "从 Studio 交的", no_history: "还没有记录。",
    docs_sub: "这支片子文件夹里的文档，照原样排。", warnings: "这些没能读出来",
    no_docs: "这支片子的文件夹里还没有文档。", l_doc: "{f} · {s}",
    check_sub: "最近一次检查的结果，和最近渲染的几支。", no_check: "还没检查过。", fails: "没过的",
    renders: "最近的渲染", th_file: "文件", th_size: "大小", th_when: "时间", th_check: "检查",
    versions_sub: "每一版：哪一版是现在的，哪些留着。", no_versions: "还没出过版本。",
    th_ver: "版", th_state: "状态", th_made: "怎么来的", th_note: "说明",
    assets_sub: "登记了多少素材，哪些许可还不明，花了多少。", no_assets: "还没有素材记录。",
    a_records: "登记", a_uncleared: "许可不明", a_not_taken: "用了但没登记", a_aigc: "生成的", a_spent: "已花", a_budget: "预算",
    stn: { "1": "立意", "2": "分镜", "3": "初版", E0: "画风样张", E1: "脚本", E2: "配乐安排", E3: "定声音", E4: "第一章样片", E5: "定画面", deliver: "交付" },
    f_done_d: "已定 {d}",
    f_delivered: "已交付",
    f_delivered_d: "已交付 {d}",
    g_doing: "在做",
    g_done: "做完了",
    today: "今天",
    go_look: "去看",
    rs_notes: "{n} 条意见",
    rs_none: "还没写意见",
    rs_picked: "你定了 {d} 件",
    rs_rec: "{r} 件按推荐",
    col_done: "这支片子做完了，没有等你的事。",
    no_narr_used: "这支片子没有旁白。",
    film_gone_cover: "成片不在本机（可能挪到了别的盘），这是它的封面。",
    tell_where: "告诉 agent 它在哪",
    tell_where_say: "成片现在在：",
    doing: "正在{x}",
    doing0: "做",
    page_k: "第 {n} 页",
    ask_count: "等你定 {n} 件",
    card_err: "这支片子的记录读不出来",
    roots_n: "从 {n} 个文件夹里找的片子",
    next_place_n: "下一处（{k}/{n}）",
    next_tip: "跳到下一处要看的地方（N）",
    help: "怎么用",
    play_line: "播这一句",
    fact_other: "其他",
    col_film: "这支片子",
    c_mine_how: "点时间轴或一个镜头，在下面写一句", c_mine_how_m: "点页面上任意一处，在下面写一句", no_pic: "还没有画面", no_pic_gone: "画面不在本机",
    subs_waiting: "你交的 {n} 份意见 agent 还没读",
    blanks_n: "{n} 处没填",
    f_past: "没单独看",
    f_off_sound: "随初版听",
    f_nosound: "没有声音",
    away_decide: "{s}等你定 {n} 件",
    away_look: "{s}等你看", away_listen: "{s}等你听",
    next_you: "看{s}，定好以后交给 agent。",
    next_you0: "看一眼，定好以后交给 agent。",
    next_agent: "接着做。",
    refused_token: "没有交成功：这一页过期了。重新载入页面再交一次，写好的意见还在。", refused_404: "没有交成功：Studio 找不到这支片子了。回到空间重新打开它，写好的意见还在。",
    refused_origin: "没有交成功：这一页不是从 Studio 的窗口打开的。在 Studio 里打开这支片子再交，写好的意见还在。", refused_too_big: "没有交成功：这一份太长了。删掉一些再交。",
    refused_page_changed: "没有交成功：这一站的页在你写的时候换过了。重新载入页面，看一眼再交，写好的意见还在。",
    refused_invalid: "没有交成功：有一处写不进去（比如对着的东西已经不在了）。看一眼你的意见再交。", refused_slow: "没有交成功：没传完整。再交一次。",
    refused_any: "没有交成功。再交一次；还不行，跟 agent 说一声。", c_handed: "交给 agent 的", handed_opt: "（选了一项）", handed_gone: "（这一项已经不在这一页上了）", handed_q: "一件决定", handed_none: "只交了推荐的选项，没写意见。", rehand: "改了再交", rs_handed: "已经交给 agent 了", now_unread: "现在读不到这支片子的状态。", now_sure: "确定，让 agent 接着做", now_sure_note: "最近还有动静，它可能还在做。", look_frames: "先看分镜的关键帧。", look_sheet: "先看联系表。", look_cover: "这是它的封面。",
    fps_n: "{n} 帧/秒",
    no_play: "只有一张画面，没什么可播",
    no_sound: "这一版没有声音", mute: "静音", unmute: "打开声音", volume: "音量", playing_instead: "放的是 {f}（{g} 没有声音）",
    lacks_h: "这台电脑上还缺", lk_missing: "没有它，{s}。", lk_old: "装的版本太旧，{s}。",
    lk_ffmpeg_n: "FFmpeg", lk_ffmpeg_s: "画面和声音合不成一支片子", lk_ffmpeg_d: "跟你的 agent 说“帮我装上 FFmpeg”。",
    lk_node_n: "Node", lk_node_s: "画面渲染不出来", lk_node_d: "跟你的 agent 说“帮我装上 Node 22”。",
    lk_uv_n: "uv", lk_uv_s: "配音、配乐和量声音的工具都用不了", lk_uv_d: "跟你的 agent 说“帮我装上 uv”。",
    lk_git_n: "git", lk_git_s: "这个工作台更新不了", lk_git_d: "跟你的 agent 说“帮我装上 git”。",
    lk_browser_n: "浏览器", lk_browser_s: "网页做的画面渲染不出来，也取不了帧来检查", lk_browser_d: "跟你的 agent 说“帮我装上 Chrome”。",
    lk_agent_n: "Studio 里的 agent", lk_agent_s: "右边的「对话」现在只能看，还不能和 agent 说话。", lk_agent_d: "打开一支片子，在右边「对话」里点「装上」。",
  },
  en: {
    revisions: "Revisions", revision_pending: "Ready for review", revision_approved: "Accepted", revision_changes_requested: "Changes requested",
    revision_compare: "Compare the change", revision_before: "Before", revision_after: "After", revision_sound: "Audio to audition",
    revision_play: "Play this span", revision_seek: "Shared playhead", revision_gone: "A saved version was moved or changed, so there is nothing to compare.",
    revision_load_error: "The two versions won't play: ask the agent whether both are still there.", revision_reply: "Notes on the revised version",
    revision_change: "Request changes", revision_sent: "Your notes on the change are saved", revision_send_error: "Your notes on the change weren't saved",
    revision_close: "Close", revision_pause: "Pause",
    nokey: "This page can only look.", reopen: "Open in Studio's window", reopened: "Studio's window is in front",
    reopen_failed: "Studio's window did not open: click the OVH Studio icon, or ask your agent to open Studio",
    taken: "Another program on this computer connected to Studio before this window did, and the window was replaced twice already. Ask your agent to restart Studio.",
    brand: "Studio", noServer: "Can't read this film. Open this page in Studio on this computer.", loading: "…",
    m_new: "New", new_tip: "Write what you want to make; an agent starts the film",
    m_space: "Space", m_idea: "Concept", m_outline: "Outline", m_board: "Storyboard", m_sound: "Sound", m_cut: "Cut", m_ship: "Delivery", m_assets: "Assets", m_ledger: "Decisions",
    f_done: "decided", f_wait: "waiting for you", wait_ear: "waiting for you", f_agent: "agent working", f_todo: "not started", f_open: "not decided yet", f_skip: "skipped", f_off: "with the first draft", f_norec: "no record",
    search: "Find a film", search_ph: "Title, folder or type; Enter opens it", no_match: "No film matches", lang: "中", lang_tip: "切换到中文", themes: "Theme",
    th_darkfield: "Darkfield", th_prism: "Prism", th_bridge: "Bridge", skip: "Skip to content", rail: "Modules", flow: "This film's stops", ask_prefix: "Make a film with OpenVideoHarness: ",
    films: "Films", home_meta: "{n} · {w} waiting for you", home_meta0: "{n}", g_wait: "Waiting for you",
    no_projects: "No films here yet. Write what you want to make on the right, and an agent starts one.",
    st_waiting_person: "waiting for you", st_waiting_agent: "agent working", st_in_progress: "in progress", st_delivered: "delivered",
    st_paused: "paused", st_no_record: "no review record", st_not_started: "not started", st_skipped: "skipped", st_done: "decided",
    agent_list: "The agent is on",
    col_round: "This stop", col_notes: "Notes", live_on: "the agent is waiting for you",
    live_on_tip: "Once you send it, the agent carries on",
    c_decide: "To decide", c_rec: "If you don't pick: recommended", c_least: "Where the agent is unsure", c_listen: "Listen to", c_mine: "My notes", c_next: "Next", c_running: "Working on", c_spend: "Spent",
    c_spent: "{s} spent", c_of: "of {l}", c_none_mine: "None yet. Click the timeline or a shot, then write a line below.", who_agent: "agent", who_person: "you", who_nobody: "delivered",
    submit_round: "Send to agent", c_whole_note: "Overall", round_quiet: "Nothing to decide now.", static_page: "Open the review page", recent: "Recently decided", agent_decided_k: "the agent decided · {x}",
    at: "On", whole: "this page", whole_film: "the whole film", to_whole: "Deselect",
    c_ph: "A note on {x}: it goes when you press “Send to agent”", note_add: "Add note", note_keys: "⌘↩", noted: "Noted: {x}", del: "Delete",
    d_dropped: "{n} can't be sent: what they are on can't be read, or they are too long",
    d_title: "Before you send it", d_decisions: "Decisions", d_items: "Notes", by_rec: " (you didn't pick: the recommended one)", d_none: "You wrote no notes.",
    general: "Overall (optional)", general_ph: "e.g. the pace drags overall; the opening works…", submit: "Send to agent", cancel: "Keep looking", preview: "The text that will be sent",
    submit_hint: "Once it is sent, the agent reads your notes first the next time it works.",
    sent_live: "Sent; the agent is on it", sent: "Sent",
    hint_live: "Sent. The agent was waiting and has carried on.",
    hint_idle: "Sent. The agent reads your notes the next time it works; to have it read them now, tell it in the chat.",
    offline: "Couldn't reach the local server: the reply is copied, paste it into the chat", offline2: "Couldn't reach the local server: copy the text below", moved: "Not sent: this address no longer names the film you opened. Reload the page and send again (your draft is kept).",
    reply_head: "Reply to {r} of “{p}”", rest: "No note means it passes.", notes_round: "notes", overall: "Overall",
    submitted: "You already sent this stop once ({at}). Sending again sends another copy; the agent sees both.", new_round: "The agent sent a new page: {g}",
    sent_n: "Sent {n} {n|note|notes} and {d} {d|decision|decisions} ({at}). Sending again sends only what is new.", proj_ph: "<project>", ns_raw: "the agent's own words",
    past: "An earlier review page ({g}), to look at only.", to_round: "Back to this stop →", page_of: "See the review page of then →", st_ok: "ok", st_change: "change", st_ask: "question",
    fb_ok: "✓ OK", fb_change: "✎ Change", fb_ask: "? Question", fb_def: "No click means it passes", ph_change: "What to change, and why", ph_ask: "What's unclear?",
    ph_suggest: "Change it to… (optional)", agree: "✓ Agree", overturn: "Change", def_agree: "No click means you agree",
    fact_ok: "✓ Right", fact_bad: "✎ Wrong", fact_unsure: "? Not sure", fact_def: "No click means not checked",
    l_least: "Unsure: {x}", l_deleg: "Decided for you: {x}", l_shot: "Shot {x}", l_seg: "Outline part {i} {x}", l_line: "Narration {x}",
    film_label: "Film {t}", range_label: "Film {a}–{b}", sound_label: "Sound {t}", chapter_label: "Chapter {x}",
    l_shots: "Shots", l_script: "Narration", l_captions: "Captions", l_notes: "Marks", l_checks: "Checks",
    no_shots: "No shot list yet.", no_narr: "No narration yet.",
    no_checks: "Not checked yet.", check_stale: "The film changed after this check; the results may be out of date.", verdict: "Verdict",
    n_notes: "{n} {n|note|notes}", unsure: "unsure", n_checks: "{n} {n|check|checks}", reads: "Should see", ver_n: "v{n}", proxy: "preview copy",
    no_film_frames: "No film yet: these are the storyboard's key frames.", no_film_sheet: "No film yet: this is the contact sheet.", no_film0: "No film yet.", film_gone_frames: "The film isn't on this computer (moved to another drive?): these are the storyboard's key frames.", film_gone_sheet: "The film isn't on this computer (moved to another drive?): this is the contact sheet.", film_gone0: "The film isn't on this computer (moved to another drive?).",
    safe: "Safe area", compare: "Compare with {v}", ver_now: "{v} · now", lay_review: "Review", lay_fine: "Fine cut", lay_sound: "Listen", layout: "Layout",
    tl_hint: "The playhead goes where you click; click a shot, a line or a mark and your note is about it.", h_mouse: "Mouse", h_keys: "Keys", tl_more: "Narration, music and the waveform are in:",
    snap: "Snap to shots", snap_tip: "When you Shift-drag a span, it snaps to shot edges, lines and marks", g_fold: "Fold this group", g_unfold: "Unfold this group", g_folded: "folded", zoom_in: "Zoom in", zoom_out: "Zoom out", play: "Play / pause (Space)", prev_shot: "Previous shot (←)", next_shot: "Next shot (→)",
    g_pic: "Picture", g_sound: "Sound", g_review: "Review", ln_chap: "Chapters", ln_shots: "Shots", ln_voice: "Voice", ln_music: "Music", ln_hits: "Hits", ln_wave: "Waveform", ln_marks: "Marks", ln_diff: "Changed",
    e_chap: "No chapters", e_shots: "No shot list", e_voice: "No narration", e_music: "No music", e_wave: "No waveform yet",
    e_diff: "This version doesn't record what changed (only a partial re-render records it)", e_marks: "No marks yet", whole_render: "re-rendered whole",
    diff_label: "{v} changed this", next_q: "Next · {x}", no_next: "Nothing more after here", k_least: "agent unsure", k_listen: "listen", k_check: "found by the check", k_mine: "my note",
    sev_fail: "failed", sev_warn: "warning", no_thumbs: "No thumbnails yet: dragging won't show each second",
    sub_outline: "Outline", sub_script: "Captions / narration", sub_facts: "Facts", sub_check: "Check", sub_versions: "Versions", sub_decisions: "Decisions", sub_history: "History", sub_docs: "Documents",
    concept: "Concept", spine: "Spine", motif: "Recurring motif", end: "Remembered after", spec: "Spec", outline_tip: "click a block to jump to it",
    seg_n: "Part {i}", know: "The viewer knows / feels", visual: "Key visual", seg_caps: "{n} {n|line|lines} in this part", to_script: "go through them →", bars: "bars {b}",
    no_outline: "The outline isn't a table yet; here it is as written.", no_brief: "No brief yet.",
    script_sub: "{n} {n|line|lines} by outline part. Amber and red ones read fast.",
    f_all: "All", f_mine: "Marked by me", f_terms: "With a term", f_facts: "With a source #", f_fast: "Maybe too fast",
    no_script: "The captions aren't a table yet; here they are as written.", no_script_file: "No captions or narration script yet.",
    other_seg: "Not matched to the outline", per_s: "/s", chars: "{n} {n|char|chars} · {s} s", none_match: "Nothing matches.", l_cap: "Caption {x}", l_vo: "Narration {x}", term: "Term",
    board_sub: "Click a frame to play that shot. Amber ones are shots the agent is unsure about.", no_shot_caption: "(no caption in this shot)",
    transition: "Transition: ", unsure_x: "Unsure: ", no_board: "No shot list yet; here is the storyboard as written.", no_board_file: "No storyboard yet.",
    no_video: "(no video to play; keyframes only)",
    sound_sub: "The agent can't hear; it reads the score and the loudness. This page is for your ears. {bpm} BPM, {d} s.", comment_at: "Note at {t}",
    sec_tip: "blocks are sections, click one to play from there; ticks are notes that land on actions", listen: "Please listen to these", your_sound: "Your notes on the sound",
    none_sound: "None yet. When something sounds off, click “Note at …” above.", roll: "Score and loudness (one row per instrument, darker = louder)",
    no_music: "No music yet.", no_audio: "No playable audio found.",
    facts_sub: "What goes on screen, and its source. Check it isn't simplified into something wrong.", todo: "Not verified yet",
    th_id: "#", th_claim: "Item (source wording)", th_screen: "On screen", th_src: "Source", th_you: "You", dropped: "(dropped)", l_fact: "Fact {x}",
    no_facts: "The material list isn't a table yet; here it is as written.", no_notes: "No material list yet.",
    ledger_sub: "Who decides each thing, and what was decided. Disagree? Write a line.", th_what: "Decision", th_who: "Who decides", th_status: "Now",
    agent_n: "Decided for you ({n})", superseded: "Superseded ({n})", why: "Why", undo: "Cost to change", l_led: "Decision {x}",
    no_ledger: "The decisions aren't a table yet; here they are as written.", no_dec: "No decisions recorded yet.",
    history_sub: "Your words at each stop, and what was decided and changed after.", desk_subs: "Sent from Studio", no_history: "Nothing yet.",
    docs_sub: "The documents in this film's folder, as written.", warnings: "These couldn't be read",
    no_docs: "No documents in this film's folder yet.", l_doc: "{f} · {s}",
    check_sub: "The latest check, and the latest renders.", no_check: "Not checked yet.", fails: "Failed",
    renders: "Latest renders", th_file: "File", th_size: "Size", th_when: "When", th_check: "Check",
    versions_sub: "Every version: which is current, which are kept.", no_versions: "No versions yet.",
    th_ver: "Version", th_state: "State", th_made: "Made by", th_note: "Note",
    assets_sub: "What is on record, which licences are unclear, what was spent.", no_assets: "No assets on record yet.",
    a_records: "On record", a_uncleared: "Licence unclear", a_not_taken: "Used but not on record", a_aigc: "Generated", a_spent: "Spent", a_budget: "Budget",
    stn: { "1": "Concept", "2": "Storyboard", "3": "First draft", E0: "Style frames", E1: "Script", E2: "Sound plan", E3: "Final sound", E4: "First chapter", E5: "Picture lock", deliver: "Delivery" },
    f_done_d: "decided {d}",
    f_delivered: "delivered",
    f_delivered_d: "delivered {d}",
    g_doing: "In progress",
    g_done: "Done",
    today: "today",
    go_look: "Open",
    rs_notes: "{n} {n|note|notes}",
    rs_none: "No notes yet",
    rs_picked: "{d} picked",
    rs_rec: "{r} recommended",
    col_done: "This film is done; nothing waits for you.",
    no_narr_used: "This film has no narration.",
    film_gone_cover: "The film isn't on this computer (moved to another drive?): this is its cover.",
    tell_where: "Tell the agent where it is",
    tell_where_say: "The film is now at: ",
    doing: "{x}",
    doing0: "working",
    page_k: "page {n}",
    ask_count: "{n} to decide",
    card_err: "This film's record can't be read",
    roots_n: "Films from {n} {n|folder|folders}",
    next_place_n: "Next ({k}/{n})",
    next_tip: "Go to the next place to look at (N)",
    help: "How it works",
    play_line: "Play this line",
    fact_other: "Other",
    col_film: "This film",
    c_mine_how: "click the timeline or a shot, write below", c_mine_how_m: "click anything on the page, write below", no_pic: "No picture yet", no_pic_gone: "Its pictures are not on this machine",
    subs_waiting: "The agent hasn't read {n} {n|batch|batches} of your notes yet",
    blanks_n: "{n} {n|blank|blanks}",
    f_past: "not shown on its own",
    f_off_sound: "heard with the first draft",
    f_nosound: "no sound",
    away_decide: "{s}: {n} to decide",
    away_look: "{s} is waiting for you", away_listen: "{s} is waiting for you",
    next_you: "look at the {s}, decide, and send it to the agent.",
    next_you0: "take a look, decide, and send it to the agent.",
    next_agent: "carries on.",
    refused_token: "Not sent: this page has expired. Reload the page and send again; your notes are kept.", refused_404: "Not sent: Studio cannot find this film any more. Open it again from the Space; your notes are kept.",
    refused_origin: "Not sent: this page was not opened from Studio's window. Open the film in Studio and send again; your notes are kept.", refused_too_big: "Not sent: this is too long. Remove some and send again.",
    refused_page_changed: "Not sent: this stop's page changed while you wrote. Reload it, look again and send; your notes are kept.",
    refused_invalid: "Not sent: one of your notes could not be taken (what it points at may be gone). Look them over and send again.", refused_slow: "Not sent: it did not arrive whole. Send again.",
    refused_any: "Not sent. Send again; if it still fails, tell the agent.", c_handed: "Sent to the agent", handed_opt: "(an option was picked)", handed_gone: "(that option is no longer on this page)", handed_q: "A decision", handed_none: "Only the recommended options went, with no notes.", rehand: "Change it and send again", rs_handed: "Sent to the agent", now_unread: "This film's state cannot be read right now.", now_sure: "Yes, ask an agent to carry on", now_sure_note: "There was activity lately; it may still be working.", look_frames: "Meanwhile, the storyboard's key frames.", look_sheet: "Meanwhile, the contact sheet.", look_cover: "This is its cover.",
    fps_n: "{n} fps",
    no_play: "One picture only: nothing to play",
    no_sound: "This version has no sound", mute: "Mute", unmute: "Sound on", volume: "Volume", playing_instead: "Playing {f} ({g} has no sound)",
    lacks_h: "This computer still lacks", lk_missing: "Without it, {s}.", lk_old: "The version here is too old: {s}.",
    lk_ffmpeg_n: "FFmpeg", lk_ffmpeg_s: "picture and sound can't be put together into a film", lk_ffmpeg_d: "Tell your agent “install FFmpeg for me”.",
    lk_node_n: "Node", lk_node_s: "nothing renders", lk_node_d: "Tell your agent “install Node 22 for me”.",
    lk_uv_n: "uv", lk_uv_s: "the voice, music and sound-measuring tools don't work", lk_uv_d: "Tell your agent “install uv for me”.",
    lk_git_n: "git", lk_git_s: "this workbench can't update", lk_git_d: "Tell your agent “install git for me”.",
    lk_browser_n: "A browser", lk_browser_s: "pictures made as web pages can't render, and frames can't be grabbed to check them", lk_browser_d: "Tell your agent “install Chrome for me”.",
    lk_agent_n: "An agent in Studio", lk_agent_s: "The Chat on the right can only show, not talk to an agent yet.", lk_agent_d: "Open a film and press “Set it up” in its Chat on the right.",
  },
};

const $ = (s, el = document) => el.querySelector(s), $$ = (s, el = document) => [...el.querySelectorAll(s)];
function deskToken() {   // the console's token, kept in this origin's storage (one port's) once the page traded its window's
  if (window.ovhShell && window.ovhShell.access) return "shell";   // Studio's own app holds it and adds it to the page's requests
  // one-time code for it (studio.js), so a reload of the window has it too. The static review page never calls this
  const given = (document.querySelector('meta[name="desk-token"]') || {}).content || "";
  try {
    if (given) {
      localStorage.setItem("desk:token", given);
      if (/[?&]k=/.test(location.search)) history.replaceState(null, "", location.pathname + location.hash);
      return given;
    }
    return localStorage.getItem("desk:token") || "";
  } catch (e) { return given; }
}
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
// bin/vh status's lines, said to the person: what happens next in plain words. Files and commands stay out of the words (the
// line as status wrote it is the tooltip); a line the page does not know is shown as status wrote it, marked so
const FILE_WORDS = { "REVIEW.md": ["审阅记录", "the review record"], "BRIEF.md": ["简报", "the brief"], "DECISIONS.md": ["决定记录", "the decision record"],
  "LESSONS.md": ["经验记录", "the lessons"], "NOTES.md": ["笔记", "the notes"], "SCRIPT.md": ["旁白稿", "the script"], "STORYBOARD.md": ["分镜表", "the storyboard"],
  "PACKAGING.md": ["标题和封面", "the titles and covers"], "STYLE.md": ["风格说明", "the style notes"], "shots.json": ["镜头表", "the shot table"] };
const fileWord = (f) => { const w = FILE_WORDS[String(f).trim()]; return w ? w[LANG === "zh" ? 0 : 1] : String(f).trim(); };
const ZH_MISSING = { "the person's words (原话) in REVIEW.md": "你的原话", "the concept row in DECISIONS.md": "决定记录里立意那一行" };
const STATUS_ZH = [
  [/^(.+?) is running \(bin\/vh activity [^)]*\); when it ends: ([\s\S]*)$/, (m, f) => `${cmdWords(m[1])}；跑完以后：${f(m[2])}`],
  [/^the submission was handed over; REVIEW\.md has no decision for it yet$/, () => "意见已经交给 agent，它还没记下这一站定了什么"],
  [/^(\d+) submission\(s\) not handed to the agent yet \(bin\/vh desk feedback\)$/, (m) => t("subs_waiting", { n: +m[1] })],
  [/^this round moved on to (.+?); REVIEW\.md has no decision for (.+)$/, (m) => `现在的这一页已经是${stopWords(m[1])}的，${stopWords(m[2])}还没记下定了什么`],
  [/^waived in the user's words \(([\s\S]*)\)$/, (m) => `你说了不用审（${m[1]}）`],
  [/^Effort quick: no gates$/, () => "快出：中间不停"],
  [/^decided, but the person's words are not in REVIEW\.md$/, () => "定了，但还没记下你的原话"],
  [/^decided, but without (.+?): bin\/vh render and check refuse the whole film$/, (m) => `定了，但还缺 ${m[1].split(" and ").map((x) => ZH_MISSING[x] || x).join("、")}：缺了不能出整片`],
  [/^decided, but without (.+?): bin\/vh gate does not send gate ③'s page, and bin\/vh check fails the film$/, (m) => `定了，但还缺 ${m[1].split(" and ").map((x) => ZH_MISSING[x] || x).join("、")}：初版的审阅页发不出去，检查也不放这支片子`],
  [/^decided in its REVIEW\.md section, read by date: [\s\S]*$/, () => "定了（按日期认出的那一节记录）"],
  [/^its REVIEW\.md section has a decision, but names no page and is older than the page: not counted \(its 页面 line: (.+)\)$/, () => "那一节记录有决定，但没写是哪一页、又比这一页旧，不算"],
  [/^bin\/vh gate refused this page, so that run sent the person nothing: fix it and send it again$/, () => "这一页没发出去，你什么也没收到：agent 改好再发"],
  [/^the person reviews (.+?) on (?:the desk (\S+)|the chat|(.+?)): stop here, and write their words into REVIEW\.md when they answer$/, (m) => `等你看${stopWords(m[1])}：agent 停在这里，你回了以后记下原话`],
  [/^read the person's submission for (.+?), then write what was decided into REVIEW\.md$/, (m) => `读你对${stopWords(m[1])}交的意见，记下定了什么`],
  [/^write what was decided and changed under the desk's section for (.+?) in REVIEW\.md \(定了 \/ 改了\)$/, (m) => `记下${stopWords(m[1])}定了什么、改了什么`],
  [/^record the decision for (.+?) in REVIEW\.md$/, (m) => `记下${stopWords(m[1])}的决定`],
  [/^paused \(REVIEW\.md\): the person resumes it$/, () => "暂停中：等你说继续"],
  [/^no REVIEW\.md: this project keeps no review record \(made before the templates had one\), so carry on from its files$/, () => "这支片子没有审阅记录（做在有审阅记录之前），照它现有的文件接着做"],
  [/^delivered: what this film taught goes into LESSONS\.md$/, () => "已交付：这支片子学到的记进经验"],
  [/^carry on$/, () => "接着做"],
  [/^the engine's scaffold is not there: this makes it$/, () => "引擎的工程还没搭"],
  [/^check (.+?) and look at its contact sheet$/, () => "检查成片，看联系表"],
  [/^fix what bin\/vh check failed on (\S+)(?:: ([\s\S]*))?$/, (m) => `修检查没过的地方${m[2] ? "：" + m[2] : ""}`],
  [/^render the final at delivery quality$/, () => "按交付画质渲染成片"],
  [/^render the final$/, () => "渲染成片"],
  [/^fill ([^,(]+?) \((\d+) \{…\} left\)$/, (m) => `把${fileWord(m[1])}填完（还有 ${m[2]} 处没填）`],
  [/^the shots in shots\.json, then their key frames and the rhythm chart$/, () => "先写镜头表，再出关键帧和节奏图"],
  [/^bin\/vh gate refused the page for (.+?), so the person got nothing: fix it \(([\s\S]*)\), then send it again$/, (m) => `${stopWords(m[1])}的页没发出去，你什么也没收到：agent 先修好再发`],
];
const STATUS_EN = [   // the English lines status writes with a file or a command in them, said plainly
  [/^(.+?) is running \(bin\/vh activity [^)]*\); when it ends: ([\s\S]*)$/, (m, f) => `${cmdWords(m[1])}; when it ends: ${f(m[2])}`],
  [/^(\d+) submission\(s\) not handed to the agent yet \(bin\/vh desk feedback\)$/, (m) => t("subs_waiting", { n: +m[1] })],
  [/^decided, but without (.+?): bin\/vh render and check refuse the whole film$/, (m) => `decided, but without ${m[1]}: the whole film can't go out yet`],
  [/^decided, but without (.+?): bin\/vh gate does not send gate ③'s page, and bin\/vh check fails the film$/, (m) => `decided, but without ${m[1]}: the draft's page can't be sent and the check fails the film`],
  [/^bin\/vh gate refused this page, so that run sent the person nothing: fix it and send it again$/, () => "this page didn't go out, so you got nothing: the agent fixes it and sends it again"],
  [/^bin\/vh gate refused the page for (.+?), so the person got nothing: fix it \(([\s\S]*)\), then send it again$/, (m) => `the page for ${stopWords(m[1])} didn't go out, so you got nothing: the agent fixes it and sends it again`],
  [/^fix what bin\/vh check failed on (\S+)(?:: ([\s\S]*))?$/, (m) => `fix what the check failed${m[2] ? ": " + m[2] : ""}`],
  [/^check (.+?) and look at its contact sheet$/, () => "check the film and look at its contact sheet"],
  [/^fill ([^,(]+?) \((\d+) \{…\} left\)$/, (m) => `fill in ${fileWord(m[1])} (${t("blanks_n", { n: +m[2] })} left)`],
];
const CMD_WORDS = { render: ["渲染", "rendering"], check: ["检查", "checking"], tts: ["配音", "voicing"], music: ["作曲", "composing"], thumbs: ["做缩略图", "making thumbnails"],
  peaks: ["画波形", "drawing the waveform"], review: ["出审阅页", "making the review page"], gate: ["出审阅页", "making the review page"], deliver: ["出上传版", "making the upload copy"],
  patch: ["重渲改过的几段", "re-rendering the changed parts"], sheet: ["出联系表", "making a contact sheet"], proxy: ["做预览版", "making a preview copy"], beats: ["找节拍", "finding the beats"],
  voices: ["试听声音", "trying voices"], sfx: ["找音效", "finding sound effects"], mix: ["混音", "mixing"], mux: ["合音轨", "putting the sound on"], image: ["出图", "making images"] };
function cmdWords(cmd) {   // a running command, as what it does ("正在渲染"); one the page doesn't know: "正在做"
  const x = String(cmd || "").trim(), m = x.match(/bin\/vh\s+([\w-]+)/) || x.match(/^([\w-]+)$/), w = m && CMD_WORDS[m[1]];   // "bin/vh render …", or the bare name status's activity gives
  return t("doing", { x: w ? w[LANG === "zh" ? 0 : 1] : t("doing0") });
}
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
  if (!x) return { text: x, known: true };
  const T = LANG === "zh" ? STATUS_ZH : STATUS_EN;
  const one = (y) => { for (const [re, f] of T) { const m = y.match(re); if (m) return f(m, (z) => statusWords(z).text); } return null; };
  const plain = (y) => stopWords(y.replace(/\s*\(bin\/vh [^)]*\)/g, "").replace(/\b[A-Z]+\.md\b|\bshots\.json\b/g, (f) => fileWord(f)));   // English: files and stops said as words
  const whole = one(x); if (whole != null) return { text: whole, known: true };
  const parts = x.split("; ").map((y) => one(y));   // notes joined by "; "
  if (parts.length > 1 && parts.every((y) => y != null)) return { text: parts.join(LANG === "zh" ? "；" : "; "), known: true };
  if (LANG !== "zh") return { text: x.split("; ").map((y) => one(y) || plain(y)).join("; "), known: true };
  return { text: x, known: false };
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
function filmDelivered() { const s = stations().find((x) => x.id === "deliver"); return !!s && s.state === "done"; }   // bin/vh status says it went out
function agentWorking() {   // an agent at work on this film right now: a bin/vh command running in it, or a turn in its column
  const run = (D && D.status && D.status.activity && D.status.activity.running) || [];
  return run.length > 0 || (typeof AGENT !== "undefined" && typeof AGENT.busy === "function" && AGENT.busy());
}
function flowState(f) { return Object.assign(flowLamp(f), { mod: f.mod }); }   // the lamp, and which item it is (flowWord says sound apart)
function filmSilent() {   // a film with no sound at all: its cut has no sound track, and it has no narration and no music
  return !!D && D.studio && D.studio.film_sound === false && !(TL().narration || []).length && !((D.music || {}).sections || []).length;
}
function flowLamp(f) {   // a flow item's lamp: from the film's own stops; none of them in the plan: not a stop
  const S = stations().filter((s) => f.st.includes(s.id));
  const gone = filmDelivered() && !f.st.includes("deliver");   // it went out: a stop it skipped, never had, or left open waits for no one (no word, not 跳过)
  if (!S.length) return { state: gone ? "past" : "off", S };
  if (S.some((s) => s.state === "waiting_person")) return { state: "wait", S };
  if (gone && (S.every((s) => s.state === "skipped") || !S.every((s) => s.state === "done" || s.state === "skipped"))) return { state: "past", S };
  if (S.some((s) => s.state === "waiting_agent" || s.state === "in_progress")) return agentWorking() ? { state: "agent", S } : { state: "todo", open: true, S };   // the agent's lamp only while it works: else not decided yet
  if (S.every((s) => s.state === "skipped")) return { state: "skip", S };
  if (S.every((s) => s.state === "done" || s.state === "skipped")) return { state: "done", S };
  if (S.some((s) => s.state === "no_record")) return { state: "norec", S };
  return { state: "todo", S };
}
const STATE_WORD = { done: "f_done", wait: "f_wait", agent: "f_agent", todo: "f_todo", skip: "f_skip", off: "f_off", norec: "f_norec", past: "f_past" };
function gateKey(s) {   // the stop a title or a "where" names, in either language: 关卡 ②, Gate ②, gate 2, E2, 检查点 E2 → "2", "E2"
  const x = String(s || ""), c = x.match(/[①②③④⑤]/), e = x.match(/(?:^|[^A-Za-z0-9])(E\d)(?![0-9])/), g = x.match(/(?:gate|关卡)\s*(\d)(?![0-9])/i);
  return c ? String("①②③④⑤".indexOf(c[0]) + 1) : e ? e[1] : g ? g[1] : "";
}
const GATE_NAMES = ["立意和大纲", "分镜", "初版", "样帧", "脚本", "声音", "锁时", "样板章", "锁画面", "画风样张", "配乐安排", "定声音", "第一章样片", "定画面",   // review.py's GATES: a stop's name after its code
  "concept and outline", "storyboard", "first draft", "style frames", "script", "sound", "timing lock", "sample chapter", "picture lock", "sound plan", "final sound", "first chapter"];
const STOP_RE = new RegExp(`(?:关卡|检查点|Gate|Checkpoint)\\s*([①②③④⑤]|E\\d|\\d)(?![0-9])(?:\\s*(?:${GATE_NAMES.slice().sort((a, b) => b.length - a.length).join("|")}))?`, "gi");   // longest name first: "sound plan" before "sound"
const EAR = new Set(["E3"]);   // the stops a person listens to (tools/standing.py's LISTEN): 等你听, not 等你看
function earOf(id) { return EAR.has(String(id || "").replace(/[a-z]+$/, "")); }
function stopWords(s) {   // a stop written as a code inside a short status ("已定（关卡 ①）", "Gate ③ first draft") → its name ("已定（立意）", "初版"), once
  return String(s || "").replace(STOP_RE, (m, k) => { const g = gateKey("关卡 " + k) || k; return L.stn[g] || m; });
}
function gateName(g, pages) {   // a stop by its name ("初版"); a later page of it by its number only when asked ("初版 · 第 3 页"), never a code
  const b = gateBase(g); if (!b) return g;
  const rest = String(g).slice(b.length), letter = rest.match(/^([b-z])$/);
  const more = !pages ? "" : letter ? t("page_k", { n: letter[1].charCodeAt(0) - 96 }) : rest.replace(/^[-_·\s]+/, "");
  return `${L.stn[b] || b}${more ? " · " + more : ""}`;
}
const shotText = (s) => String(s || "").replace(/(^|[^A-Za-z0-9])S0+(?=\d)/g, "$1S");   // a shot inside a tool's sentence, written one way: S06 → S6
function shortDate(d) {   // one way to write a day: "11-14" this year, "2025-11-14" another year
  const m = String(d || "").match(/^(\d{4})-(\d\d)-(\d\d)/); if (!m) return "";
  return +m[1] === new Date().getFullYear() ? `${m[2]}-${m[3]}` : `${m[1]}-${m[2]}-${m[3]}`;
}
function stopDate(S) {   // the day a flow item was settled: the delivery's, else the latest date of its stops' REVIEW.md sections
  const dl = S.find((s) => s.delivered && s.delivered.date); if (dl) return dl.delivered.date;
  const keys = S.map((s) => s.id);
  return ((D && D.history) || []).filter((h) => h.date && keys.includes(gateKey(h.title))).map((h) => h.date).sort().pop() || "";
}
function flowWord(fs) {   // a flow item's state in words: 已定 11-14, 已交付 10-23, 等你, agent 在做, 没开始, 跳过
  if (fs.open) return t("f_open");
  if (fs.mod === "sound" && (fs.state === "off" || fs.state === "past") && filmSilent()) return t("f_nosound");   // not 随初版听: there is nothing to hear
  if (fs.mod === "sound" && fs.state === "off") return t("f_off_sound");   // sound is no stop of its own: it is heard on the first draft's page
  if (fs.state === "wait" && fs.S.some((s) => s.state === "waiting_person" && earOf(s.id))) return t("wait_ear");
  if (fs.state !== "done") return t(STATE_WORD[fs.state]);
  const d = shortDate(stopDate(fs.S)), ship = fs.S.some((s) => s.id === "deliver");
  return t(ship ? (d ? "f_delivered_d" : "f_delivered") : (d ? "f_done_d" : "f_done"), { d });
}
function kickOf(mod) {
  const f = FLOW.find((x) => x.mod === mod); if (!f) return t("m_" + mod);
  const w = flowWord(flowState(f));
  return w ? `${t("m_" + mod)} · ${w}` : t("m_" + mod);
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
