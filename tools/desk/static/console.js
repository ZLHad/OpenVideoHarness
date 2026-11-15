"use strict";
/* The console (bin/vh desk): the home of every film, a project's page, and a stop's gate view. It reads the server's JSON
   (tools/desk/server.py: the project files and bin/vh, read fresh) and the gate view's markup (tools/review.py, the same
   as the static review page's; ui.js mounts it). The reviewer's draft stays in this browser (localStorage) until it is
   submitted to /api/p/<key>/feedback, the desk's one submission channel. No framework, no CDN; every text from a project
   is escaped before it reaches the page (documents arrive as HTML that reader.py has already escaped). */

const STR = {
  zh: {
    brand: "片场", home: "片场", noServer: "读不到数据：请用 bin/vh desk 打开这一页。", loading: "…",
    home_meta: "{n} 支片子 · {w} 支等你", home_meta0: "{n} 支片子", g_wait: "等你看的", g_rest: "其余",
    no_projects: "这里还没有片子。bin/vh new 建一个，或者 bin/vh desk --root <文件夹> 告诉我去哪找。",
    st_waiting_person: "等你看", st_waiting_agent: "agent 在做", st_in_progress: "进行中", st_delivered: "已交付", st_paused: "暂停",
    st_no_record: "没有审阅记录", st_not_started: "还没开始", st_skipped: "跳过", st_done: "过了",
    ask_n: "要你定 {n} 件：{q}", ask_0: "看一眼：{q}", just_now: "刚才", ago_m: "{n} 分钟前", ago_h: "{n} 小时前", ago_d: "{n} 天前",
    search: "搜项目", search_ph: "片名、文件夹或类型，回车打开", no_match: "没有对上的片子",
    next: "下一步", recent: "最近定下的", who_agent: "agent", who_person: "等你", who_nobody: "交付了", agent_decided_k: "agent 定的 · {x}",
    past: "这是之前的一页（{g}），看看就好。", to_round: "回到这一轮 →", this_round_gone: "这一轮还没有审阅页。",
    stage_none: "还没有画面", film_from: "成片 · {p}", picture_from: "最新的一张图 · {p}",
    t_concept: "立意", t_board: "分镜", t_sound: "声音", t_facts: "事实", t_film: "逐秒点评", t_check: "检查", t_versions: "版本",
    t_assets: "素材", t_ledger: "账本", t_history: "历史", t_docs: "文档", t_caption: "字幕", t_narration: "旁白", t_script: "字幕 / 旁白",
    side_pages: "静态审阅页",
    live_on: "agent 在等你提交", live_off: "agent 没在等", live_on_tip: "提交后 agent 会自动接着做，不用回对话",
    live_off_tip: "提交后回到对话里说一声“看审阅台”", theme: "深色 / 浅色", lang: "EN", lang_tip: "Switch to English", my: "我的点评",
    submit: "提交", general: "整体意见（可选）", general_ph: "比如：整体节奏偏慢；开场很好……", preview: "会提交的内容", cancel: "再看看",
    d_title: "提交给 agent", d_decisions: "决定", d_items: "点评", by_rec: "（按推荐）", d_none: "没有逐条点评；没标的都算通过。",
    submit_hint: "提交后写进项目的 out/review/feedback/，你的原话同时抄进 REVIEW.md。没动的决定按推荐算。",
    say: "说一句", fb_ok: "✓ 可以", fb_change: "✎ 要改", fb_ask: "? 疑问", fb_def: "不点就算通过", ph_change: "哪里要改、为什么", ph_ask: "哪里没看懂？",
    ph_suggest: "直接改成……（可选）", agree: "✓ 同意", overturn: "✎ 翻案", def_agree: "不点就算同意",
    fact_ok: "✓ 对", fact_bad: "✎ 有问题", fact_unsure: "? 拿不准", fact_def: "不点 = 没看", st_ok: "可以", st_change: "要改", st_ask: "疑问",
    l_least: "没把握：{x}", l_deleg: "我替你定的：{x}", l_dec: "决定：{x}",
    concept: "立意", spine: "故事线", motif: "贯穿全片的", end: "看完以后", spec: "规格", outline: "大纲", outline_tip: "点色块跳到那一段",
    seg_n: "第 {i} 段", know: "看完知道 / 感到", visual: "关键画面", seg_caps: "这一段的 {n} 条", to_script: "去逐条看 →", bars: "第 {b} 小节",
    concept_sub: "一句话立意、故事线，和按时间排开的 {n} 段。", l_concept: "立意与故事线", l_seg: "大纲 第 {i} 段 {x}",
    no_outline: "大纲还没有写成表格（BRIEF 的 Outline 一节，列名见 tools/desk/README.md），下面是 BRIEF 原文。", no_brief: "还没有 BRIEF.md。",
    script_sub: "{n} 条，按大纲分段。读速按这一条占的时间粗算：中文 {g} 字/秒以内绿、{y} 以内黄；英文 {eg} / {ey} 字符/秒。",
    f_all: "全部", f_mine: "我标过的", f_terms: "带术语的", f_facts: "带出处编号的", f_fast: "可能读不完的",
    no_script: "SCRIPT.md 里没有字幕或旁白表格（列名见 tools/desk/README.md），下面是原文。", no_script_file: "还没有字幕稿或旁白稿（SCRIPT.md）。",
    other_seg: "没对上大纲的", per_s: "/秒", chars: "{n} 字 · {s} s", none_match: "没有符合的条目。", l_cap: "字幕 {x}", l_vo: "旁白 {x}", term: "术语",
    board_sub: "点画面播这一镜，播放时当前镜头会亮起；红框是我没把握的镜头。", no_shot_caption: "（这一镜没有字幕）", transition: "转场：", unsure: "我没把握：",
    no_board: "还没有镜头表（shots.json 或 edit.json），下面是 STORYBOARD.md。", no_board_file: "还没有分镜。", l_shot: "分镜 {x}", no_video: "（没有可播放的视频，只看关键帧）",
    sound_sub: "agent 听不见，只能看谱面和响度；这一页请你用耳朵。{bpm} BPM，{d} s。", comment_at: "在 {t} 处点评",
    sec_tip: "色块是乐段，点一下从那里播；刻度是落在画面动作上的音", listen: "请你听这几处", your_sound: "你的声音点评",
    none_sound: "还没有。播到哪里觉得不对，就点上面的“在 … 处点评”。", roll: "谱面和响度（每一行是一件乐器，颜色越深越响）",
    no_music: "还没有配乐。", sound_label: "声音 {t}", no_audio: "没有找到可以播放的音频（gate JSON 的 music.audio）。",
    facts_sub: "上屏的说法，和它背后的原话、出处。请重点看“上屏说法”有没有简化到错。", todo: "还没核实的", th_id: "#", th_claim: "素材（原文）",
    th_kind: "类别", th_screen: "上屏说法", th_src: "出处", th_you: "你看", dropped: "（已不用）", l_fact: "事实 {x}",
    no_facts: "NOTES.md 里没有素材清单表格，下面是原文。", no_notes: "还没有 NOTES.md。",
    film_sub: "播到哪里有话说，按 C 或点按钮，就在那一秒留一条；要说一段，按 I 设入点、O 设出点。", film_list: "点评按时间排在下面",
    film_none: "还没有逐秒点评。", no_film: "这一轮没有视频。", film_label: "小样 {t}", del: "删",
    range_in: "入点 (I)", range_out: "出点 (O)", range_from: "从 {t} 起", range_label: "小样 {a}–{b}",
    ledger_sub: "每件事谁拍板、现在是什么状态；我替你定的事都在下面，随时可以翻案。", th_what: "事", th_who: "谁拍板", th_status: "现在",
    agent_n: "我替你定的（{n}）", superseded: "已经作废的（{n}）", why: "理由", undo: "翻案要花", l_led: "决定 {x}",
    no_ledger: "DECISIONS.md 里没有决定表和“agent 定的事”，下面是原文。", no_dec: "还没有 DECISIONS.md。",
    history_sub: "每一轮你说的原话，和之后定了、改了什么（REVIEW.md）。", desk_subs: "审阅台的提交记录", no_history: "还没有记录。",
    docs_sub: "项目里的文档，原样排版。结构化的页面读不出来的内容，都在这里。", warnings: "这些没能按约定读出来（tools/desk/README.md）",
    no_docs: "项目里还没有文档。", l_doc: "{f} · {s}",
    check_sub: "bin/vh check 最近一次的结果，和最近的几支渲染。", no_check: "还没有 bin/vh check 的记录。", verdict: "结论", fails: "没过的",
    stale: "片子在这次检查之后改过：再跑一次 bin/vh check", renders: "最近的渲染", th_file: "文件", th_size: "大小", th_when: "时间", th_check: "检查",
    versions_sub: "bin/vh versions 记着的每一版：哪一版是现在的，哪些留着。", no_versions: "还没有版本记录（第一次 bin/vh render 或 patch 之后才有）。",
    th_ver: "版", th_state: "状态", th_made: "怎么来的", th_note: "说明",
    assets_sub: "素材台账（bin/vh assets）：登记了多少，哪些许可还没清，花了多少。", no_assets: "还没有素材台账。",
    a_records: "登记", a_uncleared: "许可没清", a_not_taken: "片子用了但没登记", a_aigc: "生成的", a_spent: "已花", a_budget: "预算",
    sent_live: "已提交，agent 已经在接着做", sent: "已提交：{f}",
    hint_live: "已写进 {f}，原话也抄进了 REVIEW.md。agent 在等这份反馈，已经自动接着做了，不用再回对话。",
    hint_idle: "已写进 {f}，原话也抄进了 REVIEW.md。agent 这会儿没在等：回到对话里说一声“看审阅台”。",
    offline: "没有连上本地服务：回复已复制，粘贴到对话里即可", offline2: "没有连上本地服务：请复制下面的内容", refused: "没有提交成功：{e}",
    reply_head: "《{p}》{r} 的回复", rest: "其余没标的都算通过。", round_name: "关卡 {r}", notes_round: "随手点评", overall: "整体",
    submitted: "这一轮已经提交过（{at}）。再提交会另存一份，REVIEW.md 里也会多一节。", new_round: "agent 发来了新的一页：{g}",
    rail: { "1": "立意", "2": "分镜", "3": "初版", E0: "样帧", E1: "脚本", E2: "声音", E3: "锁时", E4: "样板章", E5: "锁画面", deliver: "交付" },
  },
  en: {
    brand: "Studio", home: "Studio", noServer: "Can't read the data: open this page with bin/vh desk.", loading: "…",
    home_meta: "{n} films · {w} waiting for you", home_meta0: "{n} films", g_wait: "Waiting for you", g_rest: "The rest",
    no_projects: "No films here yet. Make one with bin/vh new, or tell me where to look: bin/vh desk --root <folder>.",
    st_waiting_person: "waiting for you", st_waiting_agent: "the agent is on it", st_in_progress: "in progress", st_delivered: "delivered",
    st_paused: "paused", st_no_record: "no review record", st_not_started: "not started", st_skipped: "skipped", st_done: "passed",
    ask_n: "{n} to decide: {q}", ask_0: "To look at: {q}", just_now: "just now", ago_m: "{n} min ago", ago_h: "{n} h ago", ago_d: "{n} days ago",
    search: "Find a film", search_ph: "Title, folder or type; Enter opens it", no_match: "No film matches",
    next: "Next", recent: "Recently decided", who_agent: "agent", who_person: "you", who_nobody: "delivered", agent_decided_k: "the agent decided · {x}",
    past: "An earlier page ({g}), to look at only.", to_round: "Back to this round →", this_round_gone: "No review page this round yet.",
    stage_none: "No picture yet", film_from: "The film · {p}", picture_from: "The newest picture · {p}",
    t_concept: "Concept", t_board: "Storyboard", t_sound: "Sound", t_facts: "Facts", t_film: "Timecoded notes", t_check: "Check",
    t_versions: "Versions", t_assets: "Material", t_ledger: "Ledger", t_history: "History", t_docs: "Documents", t_caption: "Captions",
    t_narration: "Narration", t_script: "Captions / narration", side_pages: "Static review pages",
    live_on: "The agent is waiting", live_off: "The agent isn't waiting", live_on_tip: "Submit and the agent carries on by itself; no need to go back to the chat",
    live_off_tip: "After submitting, tell the agent in the chat: “check the desk”", theme: "Dark / light", lang: "中", lang_tip: "切换到中文", my: "My notes",
    submit: "Submit", general: "Overall (optional)", general_ph: "e.g. the pace drags overall; the opening works…", preview: "What will be submitted", cancel: "Keep looking",
    d_title: "Submit to the agent", d_decisions: "Decisions", d_items: "Notes", by_rec: " (recommended)", d_none: "No item notes; anything not marked passes.",
    submit_hint: "Submissions go to the project's out/review/feedback/, and your words into REVIEW.md. Untouched decisions go by the recommendation.",
    say: "Say something", fb_ok: "✓ OK", fb_change: "✎ Change", fb_ask: "? Question", fb_def: "untouched = approved", ph_change: "What to change, and why", ph_ask: "What's unclear?",
    ph_suggest: "Change it to… (optional)", agree: "✓ Agree", overturn: "✎ Overturn", def_agree: "untouched = agreed",
    fact_ok: "✓ Right", fact_bad: "✎ Wrong", fact_unsure: "? Not sure", fact_def: "untouched = not checked", st_ok: "ok", st_change: "change", st_ask: "question",
    l_least: "Unsure: {x}", l_deleg: "Decided for you: {x}", l_dec: "Decision: {x}",
    concept: "Concept", spine: "Spine", motif: "Recurring motif", end: "At the end", spec: "Spec", outline: "Outline", outline_tip: "click a block to jump to it",
    seg_n: "Part {i}", know: "The viewer knows / feels", visual: "Key visual", seg_caps: "{n} lines in this part", to_script: "go through them →", bars: "bars {b}",
    concept_sub: "The concept in a line, the spine, and the {n} parts laid out in time.", l_concept: "Concept and spine", l_seg: "Outline part {i} {x}",
    no_outline: "The outline isn't a table yet (BRIEF's Outline section; columns in tools/desk/README.md). Here is the BRIEF as written.", no_brief: "No BRIEF.md yet.",
    script_sub: "{n} lines by outline part. Reading speed, roughly, from each line's span: Chinese up to {g} chars/s green, {y} yellow; English {eg} / {ey}.",
    f_all: "All", f_mine: "Marked by me", f_terms: "With a term", f_facts: "With a source #", f_fast: "Maybe too fast",
    no_script: "SCRIPT.md has no caption or narration table (columns in tools/desk/README.md). Here it is as written.", no_script_file: "No captions or narration yet (SCRIPT.md).",
    other_seg: "Not matched to the outline", per_s: "/s", chars: "{n} chars · {s} s", none_match: "Nothing matches.", l_cap: "Caption {x}", l_vo: "Narration {x}", term: "Term",
    board_sub: "Click a frame to play that shot; the current shot lights up while playing; red frames are shots I'm unsure about.", no_shot_caption: "(no caption in this shot)",
    transition: "Transition: ", unsure: "Unsure: ", no_board: "No shot table yet (shots.json or edit.json). Here is STORYBOARD.md.", no_board_file: "No storyboard yet.", l_shot: "Shot {x}",
    no_video: "(no video to play; keyframes only)",
    sound_sub: "The agent can't hear; it reads the score and the loudness. This page is for your ears. {bpm} BPM, {d} s.", comment_at: "Comment at {t}",
    sec_tip: "blocks are sections, click one to play from there; ticks are notes that land on actions", listen: "Please listen to these", your_sound: "Your sound notes",
    none_sound: "None yet. When something sounds off, click “Comment at …” above.", roll: "Score and loudness (one row per instrument, darker = louder)",
    no_music: "No music yet.", sound_label: "Sound {t}", no_audio: "No playable audio found (the gate JSON's music.audio).",
    facts_sub: "What goes on screen, and the source behind it. Check that the on-screen wording isn't simplified into something wrong.", todo: "Not verified yet",
    th_id: "#", th_claim: "Item (source wording)", th_kind: "Kind", th_screen: "On screen", th_src: "Source", th_you: "You", dropped: "(dropped)", l_fact: "Fact {x}",
    no_facts: "NOTES.md has no material table. Here it is as written.", no_notes: "No NOTES.md yet.",
    film_sub: "Wherever you have something to say, press C or the button to leave a note at that second; for a span, I sets its start and O its end.",
    film_list: "notes are listed below in time order", film_none: "No timecoded notes yet.", no_film: "No video this round.", film_label: "Film {t}", del: "Delete",
    range_in: "In (I)", range_out: "Out (O)", range_from: "from {t}", range_label: "Film {a}–{b}",
    ledger_sub: "Who decides each thing and where it stands; what I decided for you is below, and you can overturn any of it.", th_what: "Decision", th_who: "Who decides", th_status: "Now",
    agent_n: "Decided for you ({n})", superseded: "Superseded ({n})", why: "Why", undo: "Cost to undo", l_led: "Decision {x}",
    no_ledger: "DECISIONS.md has no ledger table and no agent decisions. Here it is as written.", no_dec: "No DECISIONS.md yet.",
    history_sub: "Your words each round, and what was decided and changed after (REVIEW.md).", desk_subs: "Submissions from the desk", no_history: "Nothing yet.",
    docs_sub: "The project's documents, as written. Whatever the structured views can't read is here.", warnings: "Not read by the contract (tools/desk/README.md)",
    no_docs: "No documents in the project yet.", l_doc: "{f} · {s}",
    check_sub: "bin/vh check's latest result, and the latest renders.", no_check: "No bin/vh check record yet.", verdict: "Verdict", fails: "Failed",
    stale: "The film changed after this check: run bin/vh check again", renders: "Latest renders", th_file: "File", th_size: "Size", th_when: "When", th_check: "Check",
    versions_sub: "Every version bin/vh versions keeps: which is current, which are kept.", no_versions: "No version record yet (the first bin/vh render or patch makes one).",
    th_ver: "Version", th_state: "State", th_made: "Made by", th_note: "Note",
    assets_sub: "The asset ledger (bin/vh assets): what is on record, which licences are not cleared, what was spent.", no_assets: "No asset ledger yet.",
    a_records: "On record", a_uncleared: "Licence not cleared", a_not_taken: "Used but not on record", a_aigc: "Generated", a_spent: "Spent", a_budget: "Budget",
    sent_live: "Submitted; the agent is on it", sent: "Submitted: {f}",
    hint_live: "Saved to {f}; your words are in REVIEW.md too. The agent was waiting for this and has carried on; no need to go back to the chat.",
    hint_idle: "Saved to {f}; your words are in REVIEW.md too. The agent isn't waiting right now: tell it in the chat, “check the desk”.",
    offline: "Couldn't reach the local server: the reply is copied, paste it into the chat", offline2: "Couldn't reach the local server: copy the text below", refused: "Not submitted: {e}",
    reply_head: "Reply to {r} of “{p}”", rest: "Everything not marked passes.", round_name: "gate {r}", notes_round: "notes", overall: "Overall",
    submitted: "Already submitted this round ({at}). Submitting again saves another copy and adds another section to REVIEW.md.", new_round: "The agent sent a new page: {g}",
    rail: { "1": "Concept", "2": "Storyboard", "3": "Draft", E0: "Style frames", E1: "Script", E2: "Sound", E3: "Timing lock", E4: "Sample chapter", E5: "Picture lock", deliver: "Delivery" },
  },
};

const TOKEN = (document.querySelector('meta[name="desk-token"]') || {}).content || "";
const HOME = (document.querySelector('meta[name="desk-home"]') || {}).content || "";
const $ = (s, el = document) => el.querySelector(s), $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
let LANG = "zh", L = STR.zh;
const t = (k, vars) => String(L[k] != null ? L[k] : STR.en[k] != null ? STR.en[k] : k).replace(/\{(\w+)\}/g, (_, v) => (vars && vars[v] != null ? vars[v] : ""));
const fmt = (x) => { if (x == null || isNaN(x)) return "–"; const m = Math.floor(x / 60), s = x - m * 60; return `${m}:${s.toFixed(1).padStart(4, "0")}`; };
const enc = encodeURIComponent;
const isVideo = (p) => /\.(mp4|webm|mov|m4v)$/i.test(p || ""), isImage = (p) => /\.(png|jpe?g|gif|webp|svg|avif)$/i.test(p || ""), isAudio = (p) => /\.(wav|mp3|m4a|ogg|flac|aac|opus)$/i.test(p || "");
const cut = (s, n) => (String(s).length > n ? String(s).slice(0, n) + "…" : String(s));
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* a private window: the draft just isn't kept */ } },
};
const COLON = () => (LANG === "zh" ? "：" : ": ");
function toast(m) { const el = $("#toast"); el.textContent = m; el.classList.add("show"); clearTimeout(el._h); el._h = setTimeout(() => el.classList.remove("show"), 3200); }
async function getJSON(url) {
  try { const r = await fetch(url, { cache: "no-store" }); const j = await r.json().catch(() => null); return { ok: r.ok, status: r.status, data: j }; }
  catch (e) { return { ok: false, status: 0, data: null }; }
}

/* ---------- state: the project on screen, read fresh from the server ---------- */
let D = null, ROUND = null, FB = null, KEY = "", PKEY = "", LIST = null;
let MAIN = "", TAB = "", DOC = "", GATE = null, capFilter = "all", filmT = 0, filmIn = null;
const src = (p) => (/^https?:\/\//.test(p || "") ? p : `/f/${enc(PKEY)}/` + String(p || "").split("/").map(enc).join("/"));
const VIEWS = ["concept", "board", "script", "sound", "facts", "film", "check", "versions", "assets", "ledger", "history", "docs"];
const KIND = { dec: "", least: "", deleg: "", concept: "concept", seg: "concept", cap: "script", shot: "board", atime: "sound", fact: "facts", time: "film", range: "film", led: "ledger", doc: "docs" };
const LEGACY = ["round", "concept", "script", "board", "sound", "facts", "film", "ledger", "history", "docs"];   // the desk's first hashes

function setLang(l) {
  LANG = l === "en" ? "en" : "zh"; L = STR[LANG];
  document.documentElement.lang = LANG === "zh" ? "zh-CN" : "en";
  $("#lang").textContent = t("lang"); $("#lang").title = t("lang_tip"); $("#theme").title = t("theme"); $("#theme").setAttribute("aria-label", t("theme"));
  $("#searchLabel").textContent = t("search"); $("#q").placeholder = t("search_ph"); $("#mark").title = t("home");
  $("#myLabel").textContent = t("my"); $("#drawerTitle").textContent = t("d_title"); $("#submit").textContent = t("submit"); $("#cancel").textContent = t("cancel");
  $("#generalLabel").textContent = t("general"); $("#general").placeholder = t("general_ph"); $("#previewLabel").textContent = t("preview"); $("#submitHint").textContent = t("submit_hint");
}
function pickLang(fallback) {
  let pick = null; try { pick = localStorage.getItem("desk:lang"); } catch (e) { /* no storage */ }
  return pick === "zh" || pick === "en" ? pick : fallback || (/^zh/i.test(navigator.language || "zh") ? "zh" : "en");
}

/* ---------- routes: #/ home · #/p/<key> a project (its gate view when it waits for you) · #/p/<key>/gate/<id> · #/p/<key>/<tab> ---------- */
function parse() {
  const h = decodeURIComponent(location.hash.replace(/^#/, ""));
  if (!h) return HOME ? { view: "project", key: HOME } : { view: "home" };
  if (h === "/") return { view: "home" };
  const m = h.match(/^\/p\/([^/]+)(?:\/(.*))?$/);
  if (m) {
    const rest = m[2] || "", g = rest.match(/^gate\/([A-Za-z0-9_-]{1,24})$/);
    if (g) return { view: "project", key: m[1], gate: g[1] };
    const [tab, ...more] = rest.split("/");
    return { view: "project", key: m[1], tab: VIEWS.includes(tab) ? tab : "", doc: tab === "docs" ? more.join("/") : "" };
  }
  const [v, ...rest] = h.split("/");
  if (HOME && LEGACY.includes(v)) return { view: "project", key: HOME, tab: v === "round" ? "" : v, doc: v === "docs" ? rest.join("/") : "" };
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

/* ---------- the top bar ---------- */
function crumbs(parts) {
  $("#crumbs").innerHTML = parts.map((p, i) => `<span class="cr${p.cls ? " " + p.cls : ""}">${i ? '<span class="sep">/</span>' : ""}${p.href ? `<a href="${p.href}">${esc(p.text)}</a>` : `<b>${esc(p.text)}</b>`}</span>`).join("");
  document.title = parts.map((p) => p.text).reverse().join(" · ") + " · OpenVideoHarness";
}
let liveTimer = null;
async function pollLive() {
  if (!PKEY) return;
  const r = await getJSON(`/api/p/${enc(PKEY)}/status`);
  const on = !!(r.ok && r.data && r.data.listening);
  $("#live").hidden = false; $("#live").classList.toggle("on", on);
  $("#liveTxt").textContent = on ? t("live_on") : t("live_off"); $("#live").title = on ? t("live_on_tip") : t("live_off_tip");
  if (r.ok && r.data && D && r.data.round !== undefined && r.data.round !== (D.current || null) && r.data.key === PKEY) {   // the agent sent a new page
    toast(t("new_round", { g: r.data.round || "" })); await loadProject(PKEY, true); route();
  }
}

/* ---------- the home: a card a film ---------- */
function ago(sec) {
  if (!sec) return "";
  const d = Date.now() / 1000 - sec;
  if (d < 90) return t("just_now");
  if (d < 3600) return t("ago_m", { n: Math.round(d / 60) });
  if (d < 86400 * 1.5) return t("ago_h", { n: Math.round(d / 3600) });
  if (d < 86400 * 14) return t("ago_d", { n: Math.round(d / 86400) });
  return new Date(sec * 1000).toISOString().slice(0, 10);
}
function stateWords(r) {
  const s = r.station ? (L.rail[r.station.id] || r.station.name || "") : "";
  const g = r.station && /^(\d|E\d)$/.test(r.station.id) ? (/^\d$/.test(r.station.id) ? "①②③④⑤"[+r.station.id - 1] + " " : r.station.id + " ") : "";
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
  const a = r.ask;
  const ask = a ? `<span class="pcard-ask">${esc(a.decisions ? t("ask_n", { n: a.decisions, q: cut(a.question, 60) }) : t("ask_0", { q: cut(a.question, 60) }))}</span>` : "";
  const when = r.last_activity ? ago(r.last_activity.t) : "";
  return `<a class="pcard" href="${projHash(r.key)}" data-state="${esc(r.state || "")}" data-key="${esc(r.key)}">${picture(r)}
    <span class="pcard-name">${esc(r.title || r.name)}</span>
    <span class="pcard-meta meta"><span class="st">${esc(stateWords(r))}</span>${when ? `<span>${esc(when)}</span>` : ""}${r.type ? `<span>${esc(String(r.type).replace(/^\d+-/, ""))}</span>` : ""}</span>
    ${ask}${r.error ? `<span class="err">${esc(cut(r.error, 120))}</span>` : ""}</a>`;
}
let homeTimer = null;
async function listing() {
  const r = await getJSON("/api/projects");
  if (r.ok && r.data) LIST = r.data;
  return r;
}
async function showHome(quiet) {
  if (GATE) { GATE.destroy(); GATE = null; }
  PKEY = ""; D = null; $("#live").hidden = true; $("#openDrawer").hidden = true; document.onkeydown = null;
  if (!quiet) { setLang(pickLang(LANG)); crumbs([{ text: t("home") }]); }
  const r = await listing();
  if (parse().view !== "home") return;
  if (!r.ok || !LIST) { $("#view").innerHTML = `<p class="empty">${esc(t("noServer"))}</p>`; return; }
  const rows = LIST.projects, wait = rows.filter((x) => x.state === "waiting_person"), rest = rows.filter((x) => x.state !== "waiting_person");
  const meta = LIST.waiting ? t("home_meta", { n: rows.length, w: LIST.waiting }) : t("home_meta0", { n: rows.length });
  const html = `<section class="home"><header class="home-h"><h1>${esc(t("home"))}</h1><span class="meta">${esc(meta)}</span></header>
    ${rows.length ? "" : `<p class="empty-home">${esc(t("no_projects"))}</p>`}
    ${wait.length ? `<section class="group"><h2 class="g-h">${esc(t("g_wait"))}<span class="n">${wait.length}</span></h2><div class="cards">${wait.map(card).join("")}</div></section>` : ""}
    ${rest.length ? `<section class="group">${wait.length ? `<h2 class="g-h">${esc(t("g_rest"))}<span class="n">${rest.length}</span></h2>` : ""}<div class="cards">${rest.map(card).join("")}</div></section>` : ""}</section>`;
  const y = window.scrollY;
  $("#view").innerHTML = html;
  if (quiet) window.scrollTo(0, y);
  midFrames($("#view"));
  clearTimeout(homeTimer); homeTimer = setTimeout(() => { if (parse().view === "home") showHome(true); }, 15000);
}
function midFrames(root) {   // a card of a film shows its middle frame: the video's metadata and one frame, only once it is on screen
  const vids = $$("video[data-mid]", root);
  const load = (v) => { if (v.src) return; v.addEventListener("loadedmetadata", () => { try { v.currentTime = v.duration / 2; } catch (e) { /* not seekable */ } }, { once: true }); v.preload = "metadata"; v.src = v.dataset.src; };
  if (!("IntersectionObserver" in window)) return vids.forEach(load);
  const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { load(e.target); io.unobserve(e.target); } }), { rootMargin: "200px" });
  vids.forEach((v) => io.observe(v));
}

/* ---------- search: / anywhere ---------- */
let hits = [], sel = 0;
async function openSearch() {
  $("#search").hidden = false; const q = $("#q"); q.value = ""; q.focus();
  if (!LIST) await listing();
  renderHits();
}
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
  const a = document.activeElement, typing = a && (/^(INPUT|TEXTAREA|SELECT)$/.test(a.tagName) && a.type !== "radio" || a.isContentEditable);
  if (e.key === "/" && !typing && !e.metaKey && !e.ctrlKey) { e.preventDefault(); openSearch(); }
  else if (e.key === "Escape") { if (!$("#search").hidden) closeSearch(); else if ($("#drawer").classList.contains("open")) closeDrawer(); }
});

/* ---------- a project ---------- */
async function loadProject(key, fresh) {
  if (!fresh && D && PKEY === key) return true;
  const r = await getJSON(`/api/p/${enc(key)}/data`);
  if (!r.ok || !r.data) { $("#view").innerHTML = `<p class="empty">${esc(r.data && r.data.error ? r.data.error : t("noServer"))}</p>`; return false; }
  D = r.data; PKEY = key;
  ROUND = D.rounds[D.rounds.length - 1] || { id: "notes", gate: "", data: { decisions: [], least_sure: [], decided: [], delegated: [], assets: [], appendix: [], listen: [] } };
  KEY = `desk:${D.project.slug}:${ROUND.id}`;
  FB = store.get(KEY) || { decisions: {}, items: {}, general: "" };
  $("#general").value = FB.general || "";
  setLang(pickLang(D.lang));
  return true;
}
function station(id) { return ((D.status && D.status.stations) || []).find((s) => s.id === id); }
function waitingGate() {   // this round's page, when its stop waits for the person
  if (!D.current) return null;
  const st = D.status && D.status.stations ? D.status.stations.find((s) => s.current) : null;
  if (st) return st.state === "waiting_person" ? D.current : null;
  return D.feedback.some((f) => f.round === D.current) ? null : D.current;   // no status: a page nobody answered
}
function rail() {
  const S = (D.status && D.status.stations) || [];
  if (!S.length) return "";
  return `<ol class="rail" aria-label="stops">${S.map((s) => {
    const glyph = /^\d$/.test(s.id) ? "①②③④⑤"[+s.id - 1] : s.id === "deliver" ? "" : s.id;
    const name = L.rail[s.id] || s.name;
    const sub = t("st_" + (s.state || "not_started"));
    const page = s.pages && s.pages.length ? s.pages[s.pages.length - 1] : null;
    const here = MAIN === page ? " here" : "";
    const inner = `<span class="tick" aria-hidden="true"></span><span class="nm">${esc(glyph ? glyph + " " : "")}${esc(name)}</span><span class="sub">${esc(sub)}</span>`;
    return `<li data-state="${esc(s.state || "")}" class="${here.trim()}" title="${esc(s.name + (s.note ? " · " + s.note : ""))}">${page ? `<a href="${projHash(PKEY, "gate/" + enc(page))}">${inner}</a>` : `<span class="st">${inner}</span>`}</li>`;
  }).join("")}</ol>`;
}
async function showProject(r) {
  clearTimeout(homeTimer);
  const switching = PKEY !== r.key;
  if (switching || !D) { if (GATE) { GATE.destroy(); GATE = null; } MAIN = ""; if (!(await loadProject(r.key, true))) return; }
  const main = r.gate || waitingGate() || "overview";
  TAB = r.tab || TAB && !switching && TAB || defaultTab(main); DOC = r.doc || DOC;
  crumbs([{ text: t("home"), href: "#/", cls: "c-home" }, { text: D.project.title, href: r.gate || r.tab ? projHash(PKEY) : null }].concat(main !== "overview" ? [{ text: gateName(main), cls: "hide-s" }] : []));
  $("#openDrawer").hidden = false; renderCount();
  if (main !== MAIN || switching || !$("#pmain")) {
    if (GATE) { GATE.destroy(); GATE = null; }
    MAIN = main;
    const spec = ["output", "effort", "watch on"].map((k) => (D.spec.find((s) => s.k.toLowerCase().startsWith(k)) || {}).v || "").filter(Boolean).map((x) => x.split("（")[0].split("  ")[0]);
    $("#view").innerHTML = `<section class="ph"><div class="meta">${esc([D.status && D.status.project && D.status.project.type ? String(D.status.project.type).replace(/^\d+-/, "") : ""].concat(spec).filter(Boolean).join(" · "))}</div>
      <h1 class="ph-title">${esc(D.project.title)}</h1>${rail()}</section><div id="pmain"></div>
      <section class="tabs-wrap" id="tabs"><nav class="tabs" role="tablist" id="tabnav"></nav><div id="tab" role="tabpanel"></div></section>`;
    if (main === "overview") await showOverview(); else await showGate(main);
  }
  renderTabs(); renderTab();
  if (r.tab) { const el = $("#tabs"); if (el) el.scrollIntoView({ block: "start" }); }
  else if (switching) window.scrollTo(0, 0);
  clearInterval(liveTimer); pollLive(); liveTimer = setInterval(pollLive, 4000);
}
function gateName(g) {
  const m = String(g).match(/^(\d|E\d)(.*)$/);
  if (!m) return g;
  const glyph = /^\d$/.test(m[1]) ? (LANG === "zh" ? "关卡 " : "Gate ") + "①②③④⑤"[+m[1] - 1] : m[1];
  return `${glyph} ${L.rail[m[1]] || ""}${m[2] ? " · " + m[2] : ""}`.trim();
}
function defaultTab(main) {
  const g = String(main).match(/^(\d|E\d)/), n = g ? g[1] : "";
  if (n === "1") return "concept";
  if (n === "2") return (D.shots.items || []).length ? "board" : "concept";
  if (n === "3" || n === "E5") return (D.shots.items || []).length ? "board" : "concept";   // the film is already above, with its marks
  if (n === "E2" || n === "E3") return "sound";
  if (D.status && D.status.check) return "check";
  return "concept";
}

/* the gate view: the same markup as the static page, mounted with the desk's channel */
async function showGate(gid) {
  const r = await getJSON(`/api/p/${enc(PKEY)}/gate/${enc(gid)}?lang=${LANG}`);
  const pm = $("#pmain");
  if (!r.ok || !r.data) { pm.innerHTML = `<p class="empty">${esc((r.data && r.data.error) || t("this_round_gone"))}</p>`; return; }
  const g = r.data, past = !g.current;
  pm.innerHTML = (past ? `<p class="past">${esc(t("past", { g: gateName(g.gate) }))}${D.current ? ` <a href="${projHash(PKEY)}">${esc(t("to_round"))}</a>` : ""}</p>` : "")
    + (FB.submittedAt && !past ? `<p class="notice" style="margin-top:20px">${esc(t("submitted", { at: FB.submittedAt }))}</p>` : "") + g.html;
  const root = $(".gate", pm);
  if (past) { $$("input[type=radio]", root).forEach((x) => { x.disabled = true; }); const a = $(".g-act", root); if (a) a.remove(); }
  else says(root);
  GATE = OVH.mount(root, past ? {} : { initial: FB.decisions, onPick(d, o) { FB.decisions[d] = o; save(); }, onSubmit: openDrawer });
  $$("[data-mark]", root).forEach(markHost);
}
function says(root) {   // a quiet "say something" on what the gate view lists: the least-sure places, the places to listen to, the shots, what was decided for you
  $$("li[data-target], figure[data-target]", root).forEach((el) => {
    const tg = el.dataset.target; if (!tg) return;
    const kind = tg.split(":")[0];
    let label = "", opt = {};
    if (kind === "least") label = t("l_least", { x: tg.slice(6) || cut(el.textContent, 24) });
    else if (kind === "atime") { const x = +tg.slice(6); label = t("sound_label", { t: fmt(x) }); opt = { t: x }; }
    else if (kind === "shot") label = t("l_shot", { x: tg.slice(5) });
    else if (kind === "deleg") { label = t("l_deleg", { x: cut(el.textContent, 28) }); opt = { labels: [t("agree"), t("overturn"), t("fb_ask")], def: t("def_agree") }; }
    else return;
    el.setAttribute("data-mark", tg);
    const host = el.tagName === "FIGURE" ? $("figcaption", el) || el : el.closest(".g-marks") ? el.lastElementChild || el : el;
    const box = document.createElement("span"); box.className = "says";
    box.innerHTML = FB.items[tg] ? fbCtl(tg, label, opt) : `<button type="button" class="say">${esc(t("say"))}</button>`;
    host.appendChild(box);
    const b = $(".say", box); if (b) b.addEventListener("click", (e) => { e.stopPropagation(); box.innerHTML = fbCtl(tg, label, opt); });
  });
}

/* the overview, when no stop waits: the film (or the newest picture) with its ruler, and what was decided last */
async function showOverview() {
  const pm = $("#pmain"), st = D.status || {};
  const ns = st.next_step || {};
  const who = ns.who === "person" ? "person" : ns.who === "nobody" ? "nobody" : "agent";
  const hist = D.history.slice().reverse().flatMap((h) => h.notes.filter((n) => /^(定了|Decided)/.test(n.k) && n.v && !/^[—–-]?$/.test(n.v.trim())).map((n) => ({ k: h.title, v: n.v }))).slice(0, 3);
  const agent = D.agent_decided.filter((a) => !a.superseded).slice(-3).reverse().map((a) => ({ k: t("agent_decided_k", { x: a.topic || "" }), v: a.what }));
  const recent = hist.concat(agent);
  pm.innerHTML = `<div class="g-body has-side overview"><div class="g-main" id="stage"><div class="well blank"><span>${esc(t("loading"))}</span></div></div>
    <aside class="g-side">${ns.do ? `<section><h2 class="g-h">${esc(t("next"))}</h2><p class="small"><span class="who ${who}">${esc(t("who_" + who))}</span>${esc(ns.do)}</p></section>` : ""}
    ${recent.length ? `<section><h2 class="g-h">${esc(t("recent"))}</h2><ul class="side-list">${recent.map((x) => `<li><span class="k">${esc(x.k)}</span>${esc(x.v)}</li>`).join("")}</ul></section>` : ""}</aside></div>`;
  const r = await getJSON(`/api/p/${enc(PKEY)}/stage`);
  const stage = $("#stage"); if (!stage || !r.ok || !r.data) return;
  if (r.data.kind === "video") { stage.innerHTML = r.data.html + `<p class="cap">${esc(t("film_from", { p: r.data.path }))}</p>`; GATE = OVH.mount(stage, {}); }
  else if (r.data.kind === "image") stage.innerHTML = `<a class="well" href="${esc(r.data.href)}" target="_blank" rel="noopener"><img src="${esc(r.data.href)}" alt=""></a><p class="cap">${esc(t("picture_from", { p: r.data.path }))}</p>`;
  else stage.innerHTML = `<div class="well blank"><span>${esc(t("stage_none"))}</span></div>`;
}

/* ---------- tabs: the project's standing views ---------- */
function viewName(v) { return v === "script" ? t(D.captions.kind === "narration" ? "t_narration" : D.captions.kind === "caption" ? "t_caption" : "t_script") : t("t_" + v); }
function marked(view) { return Object.entries(FB.items).filter(([k, v]) => KIND[k.split(":")[0]] === view && v.status && v.status !== "ok").length; }
function tabCount(id) {
  const st = D.status || {};
  switch (id) {
    case "concept": return D.outline.length || (D.docs.some((d) => d.file === "BRIEF.md") ? "" : null);
    case "board": return (D.shots.items || []).length || (D.docs.some((d) => d.file === "STORYBOARD.md") ? "" : null);
    case "script": return D.captions.rows.length || (D.docs.some((d) => d.file === "SCRIPT.md") ? "" : null);
    case "sound": return D.music && (D.music.audio || (D.music.sections || []).length) ? "" : null;
    case "facts": return D.facts.filter((f) => !f.dropped).length || (D.docs.some((d) => d.file === "NOTES.md") ? "" : null);
    case "film": return filmAsset() ? Object.keys(FB.items).filter((k) => /^(time|range):/.test(k)).length || "" : null;
    case "check": return st.check ? "" : (st.renders || []).length ? "" : null;
    case "versions": return st.versions && st.versions.list ? st.versions.list.length : null;
    case "assets": return st.assets && !st.assets.error && (st.assets.records || st.assets.ledger) ? st.assets.records : null;
    case "ledger": return D.ledger.length || D.agent_decided.filter((a) => !a.superseded).length || (D.docs.some((d) => d.file === "DECISIONS.md") ? "" : null);
    case "history": return D.history.length || D.feedback.length || null;
    case "docs": return D.docs.length || null;
  }
  return null;
}
function renderTabs() {
  const nav = $("#tabnav"); if (!nav) return;
  const shown = VIEWS.filter((v) => tabCount(v) != null);
  if (!shown.includes(TAB)) TAB = shown[0] || "";
  nav.innerHTML = shown.map((v) => { const n = tabCount(v), c = marked(v); return `<a href="${projHash(PKEY, v)}" role="tab" aria-selected="${v === TAB}" data-tab="${v}">${esc(viewName(v))}${n !== "" && n != null ? `<span class="n">${n}</span>` : ""}${c ? `<span class="n chg">· ${c} ✎</span>` : ""}</a>`; }).join("")
    + (D.rounds.some((r) => r.page) ? `<a href="${esc(src(D.rounds[D.rounds.length - 1].page))}" target="_blank" rel="noopener" class="meta" style="margin-left:auto">${esc(t("side_pages"))} ↗</a>` : "");
}
document.addEventListener("click", (e) => {   // a link to a tab of this project switches the tab in place: the page above (an earlier gate page too) stays
  const a = e.target.closest("#tabs a[href^='#/p/']");
  if (!a || e.metaKey || e.ctrlKey || e.shiftKey || !D) return;
  const m = decodeURIComponent(a.getAttribute("href")).match(/^#\/p\/([^/]+)\/([a-z]+)(?:\/(.*))?$/);
  if (!m || m[1] !== PKEY || !VIEWS.includes(m[2])) return;
  e.preventDefault(); TAB = m[2]; if (m[2] === "docs") DOC = m[3] || DOC; renderTabs(); renderTab();
});
const VIEWFN = { concept: vConcept, script: vScript, board: vBoard, sound: vSound, facts: vFacts, film: vFilm, check: vCheck, versions: vVersions, assets: vAssets, ledger: vLedger, history: vHistory, docs: vDocs };
const WIRE = { script: wireScript, board: wireBoard, sound: wireSound, film: wireFilm, concept: wireConcept };
function renderTab() {
  const el = $("#tab"); if (!el || !TAB) { if (el) el.innerHTML = ""; return; }
  el.innerHTML = VIEWFN[TAB]();
  $$("[data-mark]", el).forEach(markHost);
  document.onkeydown = null;   // the timecoded notes set their own C, I and O keys
  (WIRE[TAB] || (() => {}))();
}
function save() { store.set(KEY, FB); renderCount(); const nav = $("#tabnav"); if (nav) { const y = nav.scrollLeft; renderTabs(); $("#tabnav").scrollLeft = y; } }
function renderCount() { if (!FB) return; $("#cnt").textContent = Object.values(FB.items).filter((v) => v.status).length + Object.keys(FB.decisions).length + (FB.general ? 1 : 0); }

/* ---------- the ✓ / ✎ / ? control ---------- */
function fbCtl(target, label, opt = {}) {
  const v = FB.items[target] || {}, st = v.status || "";
  const lab = opt.labels || [t("fb_ok"), t("fb_change"), t("fb_ask")];
  return `<div class="fb" data-target="${esc(target)}" data-label="${esc(label)}"${opt.suggest != null ? ` data-orig="${esc(opt.suggest)}"` : ""}${opt.t != null ? ` data-t="${opt.t}"` : ""}${opt.t1 != null ? ` data-t1="${opt.t1}"` : ""}${opt.labels ? ` data-labels="${esc(JSON.stringify(opt.labels))}"` : ""}${opt.def ? ` data-def="${esc(opt.def)}"` : ""}>
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
  else FB.items[tgt] = Object.assign({}, cur, { status: st, label: box.dataset.label }, box.dataset.t ? { t: +box.dataset.t } : {}, box.dataset.t1 ? { t1: +box.dataset.t1 } : {}, box.dataset.orig != null ? { orig: box.dataset.orig } : {});
  save(); refreshFb(box);
});
document.addEventListener("input", (e) => {
  const el = e.target.closest(".fb-more [data-k]"); if (!el) return;
  const tgt = el.closest(".fb").dataset.target; FB.items[tgt] = Object.assign({}, FB.items[tgt] || {}, { [el.dataset.k]: el.value }); store.set(KEY, FB);
});
function refreshFb(box) {
  const wrap = document.createElement("div");
  wrap.innerHTML = fbCtl(box.dataset.target, box.dataset.label, { suggest: box.dataset.orig != null ? box.dataset.orig : null, t: box.dataset.t != null ? box.dataset.t : null,
    t1: box.dataset.t1 != null ? box.dataset.t1 : null, labels: box.dataset.labels ? JSON.parse(box.dataset.labels) : null, def: box.dataset.def || null });
  const nb = wrap.firstElementChild; box.replaceWith(nb);
  const host = nb.closest("[data-mark]"); if (host) markHost(host);
  const ta = nb.querySelector("textarea"); if (ta && !nb.querySelector(".fb-more").hidden) ta.focus();
}
function markHost(host) { const st = (FB.items[host.dataset.mark] || {}).status; host.classList.toggle("marked", !!st); host.classList.toggle("st-ok", st === "ok"); host.classList.toggle("st-ask", st === "ask"); }

/* ---------- the desk's item views ---------- */
const atTime = (id) => esc(t("comment_at", { t: "\u0001" })).replace("\u0001", `<span id="${id}">0:00.0</span>`);   // "在 0:12.4 处点评"
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
const filmAsset = () => {
  const g = ROUND.data, want = typeof g.film === "string" ? g.film : "";
  const a = (g.assets || []).find((x) => x && (want ? x.path === want : isVideo(x.path))) || (want ? { path: want } : null);
  if (a) return a;
  const f = D.status && D.status.media && D.status.media.film;
  return f ? { path: f } : null;
};
const segIndex = (id) => D.outline.findIndex((o) => o.id === id);

function vConcept() {
  const c = D.concept, O = D.outline.filter((o) => o.t0 != null && o.t1 != null), total = O.length ? Math.max(...O.map((o) => o.t1)) : 0;
  if (!docOf("BRIEF.md")) return `<div class="empty">${esc(t("no_brief"))}</div>`;
  const specGet = (k) => (D.spec.find((s) => s.k.toLowerCase().startsWith(k)) || {}).v || "";
  const head = `<div class="card" data-mark="concept:line"><div class="tiny muted">${esc(t("concept"))}</div><div class="serif" style="font-size:22px;line-height:1.5;margin:4px 0 10px">${esc(c.line || "—")}</div>
    <dl class="kv">${c.spine ? `<dt>${esc(t("spine"))}</dt><dd>${esc(c.spine)}</dd>` : ""}${c.motif ? `<dt>${esc(t("motif"))}</dt><dd>${esc(c.motif)}</dd>` : ""}${c.end ? `<dt>${esc(t("end"))}</dt><dd>${esc(c.end)}</dd>` : ""}
    <dt>${esc(t("spec"))}</dt><dd>${["output", "effort", "watch on", "review language"].map(specGet).filter(Boolean).map((x) => `<span class="chip">${esc(x.split("（")[0].split("  ")[0])}</span>`).join("")}</dd></dl>
    ${fbCtl("concept:line", t("l_concept"))}</div>`;
  if (!D.outline.length) return `<p class="sub">${esc(t("concept_sub", { n: 0 }))}</p>${head}<h2>${esc(t("outline"))}</h2>${fallback(t("no_outline"), "BRIEF.md", /^(Outline|大纲)/i)}`;
  const bar = O.length ? `<div class="tbar">${O.map((o) => `<div data-seg="${esc(o.id)}" style="flex:${Math.max(0.1, o.t1 - o.t0).toFixed(2)}">${esc(o.title)}</div>`).join("")}</div><div class="tticks">${[0, 0.25, 0.5, 0.75, 1].map((f) => `<span>${fmt(total * f)}</span>`).join("")}</div>` : "";
  const segs = D.outline.map((o, i) => {
    const caps = D.captions.rows.filter((x) => x.seg === o.id);
    const when = o.t0 != null ? `${fmt(o.t0)}–${fmt(o.t1)}${o.t1 != null ? ` · ${(o.t1 - o.t0).toFixed(0)} s` : ""}` : "";
    return `<div class="card segcard" id="seg-${esc(o.id)}" data-mark="seg:${esc(o.id)}"><div class="stripe"></div><div>
      <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><div><span class="tiny muted">${esc(t("seg_n", { i: o.id || i + 1 }))}</span> <span class="serif" style="font-size:17px">${esc(o.title)}</span>${o.tag ? `<span class="tag">${esc(o.tag)}</span>` : ""} ${o.stage && o.stage !== "—" ? `<span class="chip acc">${esc(o.stage)}</span>` : ""}</div>
        <span class="tiny muted">${when}${o.bars ? ` · ${esc(t("bars", { b: o.bars }))}` : ""}</span></div>
      ${o.know ? `<div style="margin-top:6px"><span class="chip">${esc(t("know"))}</span>${esc(o.know)}</div>` : ""}
      ${o.visual ? `<div class="small muted" style="margin-top:4px"><span class="chip">${esc(t("visual"))}</span>${esc(o.visual)}</div>` : ""}
      ${caps.length ? `<details style="margin-top:8px"><summary class="small">${esc(t("seg_caps", { n: caps.length }))}</summary>${caps.map((x) => `<div class="segcap serif"><span class="id">${esc(x.id)}</span>${esc(x.text)}</div>`).join("")}<div class="tiny"><a href="${projHash(PKEY, "script")}">${esc(t("to_script"))}</a></div></details>` : ""}
      ${fbCtl("seg:" + o.id, t("l_seg", { i: o.id, x: o.title }))}</div></div>`;
  }).join("");
  return `<p class="sub">${esc(t("concept_sub", { n: D.outline.length }))}</p>${head}
    <h2>${esc(t("outline"))} <span class="tiny muted">${O.length ? esc(t("outline_tip")) : ""}</span></h2>${bar}<div class="grid">${segs}</div>`;
}
function wireConcept() { $$(".tbar [data-seg]").forEach((el) => el.addEventListener("click", () => { const s = document.getElementById("seg-" + el.dataset.seg); if (s) s.scrollIntoView({ behavior: "smooth", block: "center" }); })); }

const SPEED = { zh: [6, 9], en: [15, 20] };
function speed(x) {
  const cjk = /[㐀-鿿]/.test(x.text), n = cjk ? (x.text.match(/[㐀-鿿A-Za-z0-9]/g) || []).length : x.text.trim().length;
  const s = x.t0 != null && x.t1 != null ? Math.max(0.1, x.t1 - x.t0) : null, lim = SPEED[cjk ? "zh" : "en"];
  return { n, s, r: s ? n / s : null, lim };
}
function vScript() {
  const C = D.captions;
  if (!C.rows.length) return docOf("SCRIPT.md") ? fallback(t("no_script"), "SCRIPT.md") : `<div class="empty">${esc(t("no_script_file"))}</div>`;
  const keep = (x) => capFilter === "all" || (capFilter === "mine" && FB.items["cap:" + x.id]) || (capFilter === "terms" && x.term) || (capFilter === "facts" && x.facts.length) || (capFilter === "fast" && speed(x).r > speed(x).lim[0]);
  const lab = C.kind === "narration" ? "l_vo" : "l_cap";
  const row = (x) => {
    const sp = speed(x), col = sp.r == null ? "var(--text-3)" : sp.r <= sp.lim[0] ? "var(--ok)" : sp.r <= sp.lim[1] ? "var(--accent)" : "var(--flag)";
    return `<div class="capr" id="cap-${esc(x.id)}" data-mark="cap:${esc(x.id)}"><div><div class="id">${esc(x.id)}</div><div class="tm">${x.t0 != null ? fmt(x.t0) : esc(x.bars)}</div></div>
      <div>${x.term ? `<div class="term" title="${esc(t("term"))}">${esc(x.term)}</div><br>` : ""}<div class="txt">${esc(x.text)}</div>${x.visual ? `<div class="vis">${esc(t("visual"))}${COLON()}${esc(x.visual)}</div>` : ""}
        <div class="meter">${sp.r != null ? `<span>${esc(t("chars", { n: sp.n, s: sp.s.toFixed(1) }))}</span><span class="bar"><i style="width:${Math.min(100, (sp.r / (sp.lim[1] * 1.2)) * 100)}%;background:${col}"></i></span><span style="color:${col}">${sp.r.toFixed(1)}${esc(t("per_s"))}</span>` : ""}${x.facts.map((f) => `<a class="chip acc" href="${projHash(PKEY, "facts")}">${esc(f)}</a>`).join("")}</div></div>
      <div>${fbCtl("cap:" + x.id, t(lab, { x: x.id }), { suggest: x.text })}</div></div>`;
  };
  const groups = D.outline.map((o) => ({ o, rows: C.rows.filter((x) => x.seg === o.id && keep(x)) })).concat([{ o: null, rows: C.rows.filter((x) => !D.outline.some((o) => o.id === x.seg) && keep(x)) }]);
  const html = groups.filter((g) => g.rows.length).map(({ o, rows }) => `<div class="capgroup"><div class="gh">${o ? `<span>${esc(t("seg_n", { i: o.id }))} · ${esc(o.title)}</span>${o.stage && o.stage !== "—" ? `<span class="chip acc">${esc(o.stage)}</span>` : ""}${o.t0 != null ? `<span class="tiny muted">${fmt(o.t0)}–${fmt(o.t1)}</span>` : ""}` : `<span>${esc(t("other_seg"))}</span>`}</div>${rows.map(row).join("")}</div>`).join("");
  const F = [["all", "f_all"], ["mine", "f_mine"], ["terms", "f_terms"], ["facts", "f_facts"], ["fast", "f_fast"]].filter(([k]) => k !== "terms" || C.rows.some((x) => x.term));
  return `<p class="sub">${esc(t("script_sub", { n: C.rows.length, g: SPEED.zh[0], y: SPEED.zh[1], eg: SPEED.en[0], ey: SPEED.en[1] }))}</p>
    <div class="filters">${F.map(([k, n]) => `<button type="button" data-f="${k}" class="${capFilter === k ? "on" : ""}">${esc(t(n))}</button>`).join("")}</div>${html || `<div class="empty">${esc(t("none_match"))}</div>`}`;
}
function wireScript() { $$(".filters button").forEach((b) => b.addEventListener("click", () => { capFilter = b.dataset.f; renderTab(); })); }

function vBoard() {
  const S = D.shots.items || [];
  if (!S.length) return docOf("STORYBOARD.md") ? fallback(t("no_board"), "STORYBOARD.md") : `<div class="empty">${esc(t("no_board_file"))}</div>`;
  const timed = S.filter((s) => s.start != null && s.end != null);
  const track = timed.map((s) => `<div data-shot="${esc(s.id)}" class="${s.unsure ? "unsure" : ""}" style="flex:${Math.max(0.1, s.end - s.start).toFixed(2)}">${esc(s.id)}</div>`).join("");
  const cards = S.map((s) => `<div class="card shot ${s.unsure ? "unsure" : ""}" id="bshot-${esc(s.id)}" data-id="${esc(s.id)}" data-mark="shot:${esc(s.id)}">
      <div class="thumb" data-shot="${esc(s.id)}">${s.frame ? `<img src="${esc(src(s.frame))}" alt="" loading="lazy">` : ""}<span class="sid">${esc(s.id)}</span>${s.start != null ? `<span class="play">▶ ${fmt(s.start)}–${fmt(s.end)}</span>` : ""}</div>
      <div class="body"><div class="lab">${esc(s.label || "")} <span class="tiny muted">${esc(s.segment || "")}${s.start != null && s.end != null ? ` · ${(s.end - s.start).toFixed(1)} s` : ""}</span></div>
        ${s.caption ? `<div class="capline">${esc(s.caption)}</div>` : `<div class="tiny muted" style="margin-top:6px">${esc(t("no_shot_caption"))}</div>`}
        ${s.reads.length ? `<ul>${s.reads.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}
        ${s.transition ? `<div class="tiny muted" style="margin-top:6px">${esc(t("transition"))}${esc(s.transition)}</div>` : ""}
        ${s.unsure ? `<div class="unsure-note">${esc(t("unsure"))}${esc(typeof s.unsure === "string" ? s.unsure : "")}</div>` : ""}
        ${fbCtl("shot:" + s.id, t("l_shot", { x: s.id }))}</div></div>`).join("");
  const player = D.shots.video ? `<div class="bplayer"><video id="bv" src="${esc(src(D.shots.video))}" controls preload="metadata"></video>${track ? `<div class="strack">${track}<div class="playhead" id="bph"></div></div>` : ""}</div>` : `<p class="small muted">${esc(t("no_video"))}</p>`;
  return `<p class="sub">${esc(D.shots.note ? D.shots.note + " · " : "")}${esc(t("board_sub"))}</p>${player}<div class="grid g3">${cards}</div>`;
}
function wireBoard() {
  const v = $("#bv"); if (!v) return;
  const S = (D.shots.items || []).filter((s) => s.start != null && s.end != null), total = S.length ? Math.max(...S.map((s) => s.end)) : 1; let stopAt = null;
  const play = (id) => { const s = S.find((x) => x.id === id); if (!s) return; v.currentTime = s.start + 0.01; stopAt = s.end; v.play(); };
  $$("#tab [data-shot]").forEach((el) => el.addEventListener("click", () => play(el.dataset.shot)));
  v.addEventListener("timeupdate", () => {
    if (stopAt != null && v.currentTime >= stopAt - 0.03) { v.pause(); stopAt = null; }
    const ph = $("#bph"); if (ph) ph.style.left = Math.min(100, (v.currentTime / total) * 100) + "%";
    const cur = S.find((s) => v.currentTime >= s.start && v.currentTime < s.end);
    $$("#tab .shot").forEach((c) => c.classList.toggle("active", !!cur && c.dataset.id === cur.id));
  });
}

function vSound() {
  const M = D.music;
  if (!M || (!M.audio && !(M.sections || []).length)) return `<div class="empty">${esc(t("no_music"))}</div>`;
  const dur = M.duration || Math.max(1, ...(M.sections || []).map((s) => s.end));
  const secs = (M.sections || []).map((s) => `<div data-t="${s.start}" title="${esc(s.name)}" style="flex:${Math.max(0.05, s.end - s.start).toFixed(2)}">${esc(s.label || s.name)}</div>`).join("");
  const hits = (M.hits || []).map((h) => `<i style="left:${(h.t / dur) * 100}%" title="${esc(h.part)} ${fmt(h.t)}"></i>`).join("");
  const listen = (ROUND.data.listen || []).map((l) => `<button class="btn" type="button" data-seek="${l.t}">▶ ${fmt(l.t)} · ${esc(l.note)}</button>`).join("");
  const tcs = Object.entries(FB.items).filter(([k]) => k.startsWith("atime:")).sort((a, b) => a[1].t - b[1].t);
  return `<p class="sub">${esc(t("sound_sub", { bpm: M.bpm || "–", d: (+dur).toFixed(1) }))}</p>
    <div>${M.audio ? `<audio id="au" src="${esc(src(M.audio))}" controls preload="metadata"></audio>` : `<p class="small muted">${esc(t("no_audio"))}</p>`}
      ${secs ? `<div class="secbar" id="secbar">${secs}<div class="playhead" id="aph"></div></div><div class="hits">${hits}</div>` : ""}
      ${M.audio ? `<div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap"><button class="btn" type="button" id="atc">${atTime("atnow")}</button><span class="tiny muted">${esc(t("sec_tip"))}</span></div>` : ""}</div>
    ${listen ? `<h2>${esc(t("listen"))}</h2><div class="listen">${listen}</div>` : ""}
    <h2>${esc(t("your_sound"))} <span class="n">${tcs.length}</span></h2>
    <div>${tcs.map(([k, v]) => `<div class="card" style="margin-bottom:10px" data-mark="${esc(k)}"><span class="chip acc" data-seek="${v.t}">${fmt(v.t)}</span>${fbCtl(k, t("sound_label", { t: fmt(v.t) }), { t: v.t })}</div>`).join("") || `<div class="muted small">${esc(t("none_sound"))}</div>`}</div>
    ${M.roll ? `<details style="margin-top:22px"><summary>${esc(t("roll"))}</summary><img class="roll" src="${esc(src(M.roll))}" alt="" loading="lazy"></details>` : ""}`;
}
function wireSound() {
  const a = $("#au"); if (!a) return;
  const dur = D.music.duration || 1;
  $$("#tab [data-seek]").forEach((b) => b.addEventListener("click", () => { a.currentTime = +b.dataset.seek; a.play(); }));
  $$("#secbar [data-t]").forEach((b) => b.addEventListener("click", () => { a.currentTime = +b.dataset.t; a.play(); }));
  a.addEventListener("timeupdate", () => { const ph = $("#aph"); if (ph) ph.style.left = Math.min(100, (a.currentTime / (a.duration || dur)) * 100) + "%"; $("#atnow").textContent = fmt(a.currentTime); });
  $("#atc").addEventListener("click", () => { const x = +a.currentTime.toFixed(1); a.pause(); FB.items["atime:" + x] = { status: "change", label: t("sound_label", { t: fmt(x) }), t: x, text: "" }; save(); renderTab(); const ta = $(`[data-target="atime:${x}"] textarea`); if (ta) ta.focus(); });
}

function vFacts() {
  if (!D.facts.length) return docOf("NOTES.md") ? fallback(t("no_facts"), "NOTES.md") : `<div class="empty">${esc(t("no_notes"))}</div>`;
  const rows = D.facts.map((f) => `<tr class="${f.dropped ? "dropped" : ""}" id="fact-${esc(f.id.slice(1))}" data-mark="fact:${esc(f.id)}"><td><b>${esc(f.id)}</b><div class="tiny muted">${esc(f.kind)}</div></td>
      <td>${esc(f.claim)}${f.dropped ? `<div class="tiny">${esc(t("dropped"))}</div>` : ""}</td><td class="serif">${esc(f.onscreen)}</td><td class="small muted">${esc(f.source)}</td>
      <td style="min-width:230px">${f.dropped || !f.id ? "" : fbCtl("fact:" + f.id, t("l_fact", { x: f.id }), { labels: [t("fact_ok"), t("fact_bad"), t("fact_unsure")], def: t("fact_def") })}</td></tr>`).join("");
  return `<p class="sub">${esc(t("facts_sub"))}</p>
    ${D.fact_todo.length ? `<div class="card" style="margin-bottom:16px"><b class="small">${esc(t("todo"))}</b><ul class="small" style="margin:6px 0 0;padding-left:18px">${D.fact_todo.map((x) => `<li>${x.done ? "✓ " : ""}${esc(x.text)}</li>`).join("")}</ul></div>` : ""}
    <div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_id"))}</th><th>${esc(t("th_claim"))}</th><th>${esc(t("th_screen"))}</th><th>${esc(t("th_src"))}</th><th>${esc(t("th_you"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function vFilm() {
  const v = filmAsset();
  if (!v) return `<div class="empty">${esc(t("no_film"))}</div>`;
  const tcs = Object.entries(FB.items).filter(([k]) => k.startsWith("time:") || k.startsWith("range:")).sort((a, b) => a[1].t - b[1].t);
  const col = (x) => (x.status === "ask" ? "var(--text)" : x.status === "ok" ? "var(--ok)" : "var(--accent)");
  const when = (x) => (x.t1 != null ? `${fmt(x.t)}–${fmt(x.t1)}` : fmt(x.t));
  return `<p class="sub">${v.caption ? esc(v.caption) + " · " : ""}${esc(t("film_sub"))}</p>
    <div class="bplayer"><video id="fv" src="${esc(src(v.path))}"${v.poster ? ` poster="${esc(src(v.poster))}"` : ""} controls preload="metadata"></video>
      <div class="scrub" id="scrub"><div class="fill" id="sfill"></div>${tcs.map(([, x]) => x.t1 != null ? `<div class="rg" data-mt="${x.t}" data-mt1="${x.t1}" style="background:${col(x)}" title="${when(x)}"></div>` : `<div class="mk" data-mt="${x.t}" style="background:${col(x)}" title="${fmt(x.t)}"></div>`).join("")}<div class="rg pending" id="rgin" hidden></div></div>
      <div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap"><button class="btn" type="button" id="tcadd">${atTime("tnow")} (C)</button><button class="btn btn-quiet" type="button" id="rgi">${esc(t("range_in"))}</button><button class="btn btn-quiet" type="button" id="rgo" disabled>${esc(t("range_out"))}</button><span class="tiny muted" id="rgnote"></span><span class="tiny muted">${esc(t("film_list"))}</span></div></div>
    <div>${tcs.map(([k, x]) => `<div class="tc" data-mark="${esc(k)}"><span class="t" data-seek="${x.t}">${when(x)}</span><div>${fbCtl(k, x.t1 != null ? t("range_label", { a: fmt(x.t), b: fmt(x.t1) }) : t("film_label", { t: fmt(x.t) }), { t: x.t, t1: x.t1 })}</div><button class="btn btn-quiet" type="button" data-del="${esc(k)}">${esc(t("del"))}</button></div>`).join("") || `<div class="muted small" style="margin-top:12px">${esc(t("film_none"))}</div>`}</div>`;
}
function wireFilm() {
  const v = $("#fv"); if (!v) return;
  const pct = (x) => (v.duration ? Math.min(100, (x / v.duration) * 100) : 0);
  const place = () => {
    const d = v.duration || 0;
    $$("#scrub .mk").forEach((m) => { m.style.left = pct(+m.dataset.mt) + "%"; m.style.display = d ? "" : "none"; });
    $$("#scrub .rg[data-mt]").forEach((m) => { m.style.left = pct(+m.dataset.mt) + "%"; m.style.width = (pct(+m.dataset.mt1) - pct(+m.dataset.mt)) + "%"; m.style.display = d ? "" : "none"; });
    const pin = $("#rgin"), on = filmIn != null && d;
    pin.hidden = !on; if (on) { pin.style.left = pct(filmIn) + "%"; pin.style.width = Math.max(0, pct(v.currentTime) - pct(filmIn)) + "%"; }
    $("#rgo").disabled = filmIn == null; $("#rgnote").textContent = filmIn != null ? t("range_from", { t: fmt(filmIn) }) : "";
  };
  v.addEventListener("loadedmetadata", () => { if (filmT) v.currentTime = Math.min(filmT, v.duration || filmT); place(); }, { once: true });
  v.addEventListener("timeupdate", () => { filmT = v.currentTime; $("#tnow").textContent = fmt(v.currentTime); $("#sfill").style.width = (v.duration ? (v.currentTime / v.duration) * 100 : 0) + "%"; if (filmIn != null) place(); });
  $("#scrub").addEventListener("click", (e) => { if (!v.duration) return; const r = e.currentTarget.getBoundingClientRect(); v.currentTime = ((e.clientX - r.left) / r.width) * v.duration; });
  const open = (k) => { save(); renderTab(); const ta = $(`[data-target="${CSS.escape(k)}"] textarea`); if (ta) ta.focus(); };
  const add = () => { const x = +v.currentTime.toFixed(1); v.pause(); FB.items["time:" + x] = { status: "change", label: t("film_label", { t: fmt(x) }), t: x, text: "" }; open("time:" + x); };
  const mark = () => { filmIn = +v.currentTime.toFixed(1); place(); };
  const close = () => {   // a span from the in point to here (either order), as range:<a>-<b>
    if (filmIn == null) return;
    const x = +v.currentTime.toFixed(1), a = Math.min(filmIn, x), b = Math.max(filmIn, x);
    if (b - a < 0.1) return;
    const k = `range:${a}-${b}`; v.pause(); filmIn = null;
    FB.items[k] = { status: "change", label: t("range_label", { a: fmt(a), b: fmt(b) }), t: a, t1: b, text: "" }; open(k);
  };
  $("#tcadd").addEventListener("click", add); $("#rgi").addEventListener("click", mark); $("#rgo").addEventListener("click", close);
  $$("#tab [data-seek]").forEach((b) => b.addEventListener("click", () => { v.currentTime = +b.dataset.seek; v.play(); }));
  $$("[data-del]").forEach((b) => b.addEventListener("click", () => { delete FB.items[b.dataset.del]; save(); renderTab(); }));
  document.onkeydown = (e) => {
    if (TAB !== "film" || /TEXTAREA|INPUT/.test(document.activeElement.tagName) || e.metaKey || e.ctrlKey || e.altKey) return;
    const key = e.key.toLowerCase();
    if (key === "c") { e.preventDefault(); add(); } else if (key === "i") { e.preventDefault(); mark(); } else if (key === "o") { e.preventDefault(); close(); }
  };
  place();
}

function vCheck() {
  const st = D.status || {}, c = st.check, R = st.renders || [];
  const size = (n) => (n > 1e9 ? (n / 1e9).toFixed(1) + " GB" : n > 1e6 ? (n / 1e6).toFixed(1) + " MB" : Math.round(n / 1e3) + " kB");
  const verdictCls = (v) => (/pass|ok/i.test(v || "") ? "ok" : /fail/i.test(v || "") ? "bad" : "");
  const head = c ? `<div class="card"><dl class="kv"><dt>${esc(t("verdict"))}</dt><dd class="${verdictCls(c.verdict)}">${esc(c.verdict || "–")}${c.exit != null ? ` · exit ${c.exit}` : ""}</dd>
      <dt>${esc(t("th_file"))}</dt><dd>${esc(c.video || "")}</dd><dt>${esc(t("th_when"))}</dt><dd>${esc((c.at || "").replace("T", " ").slice(0, 16))}</dd>
      ${Object.keys(c.counts || {}).length ? `<dt>·</dt><dd>${Object.entries(c.counts).map(([k, v]) => `<span class="chip">${esc(k)} ${esc(v)}</span>`).join("")}</dd>` : ""}</dl>
      ${c.stale ? `<p class="notice" style="margin:12px 0 0">${esc(t("stale"))}</p>` : ""}
      ${(c.fails || []).length ? `<h2>${esc(t("fails"))}</h2><ul class="small">${c.fails.map((f) => `<li>${esc(f)}</li>`).join("")}</ul>` : ""}</div>` : `<div class="empty">${esc(t("no_check"))}</div>`;
  const rows = R.map((r) => `<tr><td>${esc(r.path)}</td><td>${esc(size(r.size || 0))}</td><td>${esc((r.mtime || "").replace("T", " ").slice(0, 16))}</td><td class="${verdictCls(r.check && r.check.verdict)}">${esc(r.check ? r.check.verdict : "–")}</td></tr>`).join("");
  return `<p class="sub">${esc(t("check_sub"))}</p>${head}${rows ? `<h2>${esc(t("renders"))}</h2><div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_file"))}</th><th>${esc(t("th_size"))}</th><th>${esc(t("th_when"))}</th><th>${esc(t("th_check"))}</th></tr></thead><tbody>${rows}</tbody></table></div>` : ""}`;
}
function vVersions() {
  const V = (D.status || {}).versions;
  if (!V || !V.list) return `<div class="empty">${esc(V && V.error ? V.error : t("no_versions"))}</div>`;
  const rows = V.list.slice().reverse().map((x) => `<tr><td>${esc(x.id)}</td><td>${esc((x.at || "").replace("T", " ").slice(0, 16))}</td><td>${esc(x.film || "")}</td><td class="${x.state === "current" ? "ok" : ""}">${esc(x.state || "")}</td><td>${esc(x.made_by || "")}</td><td class="small muted">${esc(x.note || "")}</td><td>${esc(x.check && x.check.verdict ? x.check.verdict : "")}</td></tr>`).join("");
  return `<p class="sub">${esc(t("versions_sub"))}</p><div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_ver"))}</th><th>${esc(t("th_when"))}</th><th>${esc(t("th_file"))}</th><th>${esc(t("th_state"))}</th><th>${esc(t("th_made"))}</th><th>${esc(t("th_note"))}</th><th>${esc(t("th_check"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}
function vAssets() {
  const A = (D.status || {}).assets;
  if (!A || A.error) return `<div class="empty">${esc(A && A.error ? A.error : t("no_assets"))}</div>`;
  const b = A.budget || {}, money = (o) => Object.entries(o || {}).map(([c, v]) => `${v} ${c}`).join(", ") || "–";
  return `<p class="sub">${esc(t("assets_sub"))}</p><div class="card"><dl class="kv">
    <dt>${esc(t("a_records"))}</dt><dd>${esc(A.records)}</dd><dt>${esc(t("a_uncleared"))}</dt><dd class="${A.uncleared ? "bad" : ""}">${esc(A.uncleared)}</dd>
    <dt>${esc(t("a_not_taken"))}</dt><dd class="${A.not_taken ? "bad" : ""}">${esc(A.not_taken)}</dd><dt>${esc(t("a_aigc"))}</dt><dd>${esc(A.aigc)}</dd>
    <dt>${esc(t("a_spent"))}</dt><dd>${esc(money(b.spent))}</dd><dt>${esc(t("a_budget"))}</dt><dd>${esc(b.unlimited ? "∞" : money(b.limit))}</dd></dl></div>`;
}
function vLedger() {
  if (!D.ledger.length && !D.agent_decided.length) return docOf("DECISIONS.md") ? fallback(t("no_ledger"), "DECISIONS.md") : `<div class="empty">${esc(t("no_dec"))}</div>`;
  const cur = D.agent_decided.filter((a) => !a.superseded), old = D.agent_decided.filter((a) => a.superseded);
  const item = (a, live) => { const i = D.agent_decided.indexOf(a); return `<div class="card led" data-mark="led:${i}"><div><div class="topic">${esc(a.topic || "—")}</div><div class="tiny muted">${esc(a.date)}</div></div>
    <div><div>${esc(a.what)}</div>${a.group ? `<div class="tiny muted">${esc(a.group)}</div>` : ""}${a.why ? `<div class="small muted" style="margin-top:4px"><span class="chip">${esc(t("why"))}</span>${esc(a.why)}</div>` : ""}${a.undo ? `<div class="small muted" style="margin-top:4px"><span class="chip chg">${esc(t("undo"))}</span>${esc(a.undo)}</div>` : ""}${a.note ? `<div class="tiny muted" style="margin-top:4px">${esc(a.note)}</div>` : ""}
    ${live ? fbCtl("led:" + i, t("l_led", { x: (a.topic ? a.topic + COLON() : "") + cut(a.what, 20) }), { labels: [t("agree"), t("overturn"), t("fb_ask")], def: t("def_agree") }) : ""}</div></div>`; };
  return `<p class="sub">${esc(t("ledger_sub"))}</p>
    ${D.ledger.length ? `<div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_what"))}</th><th>${esc(t("th_who"))}</th><th>${esc(t("th_status"))}</th></tr></thead><tbody>${D.ledger.map((l) => `<tr><td>${esc(l.what)}</td><td class="small">${esc(l.who)}</td><td class="small">${esc(l.status)}</td></tr>`).join("")}</tbody></table></div>` : ""}
    ${cur.length ? `<h2>${esc(t("agent_n", { n: cur.length }))}</h2><div class="grid">${cur.map((a) => item(a, true)).join("")}</div>` : ""}
    ${old.length ? `<details class="fold" style="margin-top:20px"><summary>${esc(t("superseded", { n: old.length }))}</summary><div class="grid body" style="opacity:.6">${old.map((a) => item(a, false)).join("")}</div></details>` : ""}`;
}
function vHistory() {
  const H = D.history.slice().reverse(), F = D.feedback.slice().reverse();
  if (!H.length && !F.length) return docOf("REVIEW.md") ? `<div class="card">${docHtml(docOf("REVIEW.md"))}</div>` : `<div class="empty">${esc(t("no_history"))}</div>`;
  return `<p class="sub">${esc(t("history_sub"))}</p>` + H.map((h) => `<details class="fold" ${h === H[0] ? "open" : ""}><summary>${esc(h.title)}</summary><div class="body md">${h.html}</div></details>`).join("")
    + (F.length ? `<h2>${esc(t("desk_subs"))}</h2><ul class="small">${F.map((f) => `<li><a href="${esc(src(f.file.replace(/\.json$/, ".md")))}" target="_blank" rel="noopener">${esc(f.round)} · ${esc(f.submitted_at.replace("T", " "))}</a> · ${f.items.length} ✎</li>`).join("")}</ul>` : "");
}
function vDocs() {
  if (!D.docs.length) return `<div class="empty">${esc(t("no_docs"))}</div>`;
  const doc = docOf(DOC) || D.docs[0];
  const nav = `<div class="docnav">${D.docs.map((d) => `<a href="${projHash(PKEY, "docs/" + d.file)}" class="${d === doc ? "on" : ""}">${esc(d.file)}</a>`).join("")}</div>`;
  const warn = D.warnings.length ? `<div class="notice"><b>${esc(t("warnings"))}</b><ul style="margin:4px 0 0;padding-left:18px">${D.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>` : "";
  const intro = doc.intro ? `<div class="docsec"><div class="md">${doc.intro}</div></div>` : "";
  const secs = doc.sections.map((s) => { const k = "doc:" + doc.file + "#" + cut(s.title, 100); return `<div class="card docsec" data-mark="${esc(k)}"><div class="md"><h2 style="margin-top:0">${esc(s.title)}</h2>${s.html}</div>${fbCtl(k, t("l_doc", { f: doc.file, s: s.title }))}</div>`; }).join("");
  return `<p class="sub">${esc(t("docs_sub"))}</p>${warn}${nav}${intro}${secs}`;
}

/* ---------- the drawer: everything that will be submitted, then one button ---------- */
function payload() {
  const g = ROUND.data, decisions = {}, defaulted = [];
  (g.decisions || []).forEach((d) => {
    const v = FB.decisions[d.id] || d.recommend;
    if (v && (d.options || []).some((o) => o.id === v)) { decisions[d.id] = v; if (!FB.decisions[d.id]) defaulted.push(d.id); }
  });
  const items = Object.entries(FB.items).filter(([, v]) => v.status).map(([k, v]) => Object.assign({ target: k, status: v.status, label: v.label || k, text: v.text || "" },
    v.suggest && v.suggest !== v.orig ? { suggest: v.suggest } : {}, v.orig && k.startsWith("cap:") ? { orig: v.orig } : {}, v.t != null ? { t: v.t } : {}, v.t1 != null ? { t1: v.t1 } : {}));
  return { round: ROUND.id, lang: LANG, decisions, defaulted, items, general: ($("#general").value || "").trim() };
}
function summaryText(p) {
  const st = { ok: t("st_ok"), change: t("st_change"), ask: t("st_ask") };
  const L2 = [t("reply_head", { p: D.project.title, r: p.round === "notes" ? t("notes_round") : t("round_name", { r: p.round }) })];
  Object.entries(p.decisions).forEach(([k, v]) => L2.push(`${k}: ${v}${p.defaulted.includes(k) ? t("by_rec") : ""}`));
  p.items.forEach((i) => L2.push(`${i.label} · ${st[i.status]}${i.text ? COLON() + i.text : ""}${i.suggest ? ` → ${i.suggest}` : ""}`));
  if (p.general) L2.push(`${t("overall")}${COLON()}${p.general}`);
  L2.push(t("rest"));
  return L2.join("\n");
}
function renderDrawer() {
  const p = payload(), st = { ok: t("st_ok"), change: t("st_change"), ask: t("st_ask") };
  const decs = (ROUND.data.decisions || []).map((d, i) => { const v = p.decisions[d.id], mine = !p.defaulted.includes(d.id); const o = (d.options || []).find((x) => x.id === v) || {};
    return `<li data-go="dec:${esc(d.id)}"><span class="q">${i + 1} · ${esc(d.question || d.id)}</span><span class="v ${mine ? "mine" : "rec"}">${esc(v || "–")}${o.label ? " · " + esc(cut(o.label, 40)) : ""}${mine ? "" : esc(t("by_rec"))}</span></li>`; }).join("");
  const items = p.items.map((i) => `<li data-go="${esc(i.target)}"><span class="q">${esc(i.label)} · ${esc(st[i.status])}</span>${i.text ? `<span>${esc(i.text)}</span>` : ""}${i.suggest ? `<span class="serif">→ ${esc(i.suggest)}</span>` : ""}</li>`).join("");
  $("#drawerBody").innerHTML = `<ul class="sum">${decs ? `<h3>${esc(t("d_decisions"))}</h3>${decs}` : ""}<h3>${esc(t("d_items"))}</h3>${items || `<li class="meta">${esc(t("d_none"))}</li>`}</ul>`;
  $("#preview").textContent = summaryText(p);
  $$("#drawerBody [data-go]").forEach((el) => el.addEventListener("click", () => {
    const k = el.dataset.go, kind = k.split(":")[0]; closeDrawer();
    const tab = kind === "doc" ? "docs/" + k.slice(4).split("#")[0] : KIND[kind];
    if (tab) go(projHash(PKEY, tab)); else go(projHash(PKEY));
    setTimeout(() => { const x = kind === "dec" ? document.getElementById("d-" + k.slice(4)) : $(`[data-mark="${CSS.escape(k)}"]`); if (x) x.scrollIntoView({ behavior: "smooth", block: "center" }); }, 160);
  }));
}
function openDrawer() { if (!D) return; renderDrawer(); $("#drawer").classList.add("open"); $("#drawer").setAttribute("aria-hidden", "false"); $("#scrim").hidden = false; setTimeout(() => $("#submit").focus(), 50); }
function closeDrawer() { $("#drawer").classList.remove("open"); $("#drawer").setAttribute("aria-hidden", "true"); $("#scrim").hidden = true; }
async function submit() {
  FB.general = $("#general").value; store.set(KEY, FB);
  const p = payload(), text = summaryText(p);
  let r = null;
  try { r = await fetch(`/api/p/${enc(PKEY)}/feedback`, { method: "POST", headers: { "Content-Type": "application/json", "X-Desk-Token": TOKEN }, body: JSON.stringify(p) }); } catch (e) { r = null; }
  if (r && r.ok) {
    const j = await r.json();
    FB.submittedAt = new Date().toLocaleString(); store.set(KEY, FB);
    toast(j.listening ? t("sent_live") : t("sent", { f: j.saved }));
    $("#submitHint").textContent = t(j.listening ? "hint_live" : "hint_idle", { f: j.saved });
    closeDrawer(); await loadProject(PKEY, true); MAIN = ""; route(); return;
  }
  if (r) { let e = r.status; try { e = (await r.json()).error || e; } catch (x) { /* not JSON */ } toast(t("refused", { e })); return; }
  try { await navigator.clipboard.writeText(text); toast(t("offline")); } catch (e) { toast(t("offline2")); }
  $("#drawer details").open = true;
}
$("#openDrawer").addEventListener("click", openDrawer);
$("#closeDrawer").addEventListener("click", closeDrawer);
$("#cancel").addEventListener("click", closeDrawer);
$("#scrim").addEventListener("click", closeDrawer);
$("#submit").addEventListener("click", submit);
$("#general").addEventListener("input", () => { FB.general = $("#general").value; store.set(KEY, FB); renderCount(); $("#preview").textContent = summaryText(payload()); });
$("#lang").addEventListener("click", () => { const n = LANG === "zh" ? "en" : "zh"; try { localStorage.setItem("desk:lang", n); } catch (e) { /* no storage */ } setLang(n); MAIN = ""; route(); });

setLang(pickLang());
route();
