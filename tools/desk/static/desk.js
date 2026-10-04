"use strict";
/* The review desk's page. It reads /api/data (tools/desk/reader.py: the project's own files, read fresh) and posts the
   reviewer's ticks and comments to /api/feedback. Drafts stay in this browser (localStorage) until submitted. No
   framework, no CDN; every text from the project is escaped before it reaches the page (documents arrive as HTML that
   reader.py has already escaped). */

const STR = {
  zh: {
    brand: "审阅台", noServer: "读不到项目数据：请用 bin/vh desk <项目> 打开这一页。",
    v_round: "这一轮要你看的", v_concept: "立意与大纲", v_caption: "字幕稿", v_narration: "旁白稿", v_script: "字幕 / 旁白",
    v_board: "分镜", v_sound: "声音", v_facts: "事实核对", v_film: "小样 · 逐秒点评", v_ledger: "决定账本", v_history: "历史", v_docs: "文档",
    side_project: "这个项目", side_pages: "静态审阅页",
    stages: ["选路径", "立意 · 大纲", "风格", "分镜", "声音", "搭引擎", "写场景", "自评", "初版", "交付"], gate_mark: "人工关卡",
    st_paused: "暂停", st_round: "关卡 {id} · 等你看", st_none: "进行中",
    live_on: "agent 在等你提交", live_off: "agent 没在等", live_on_tip: "提交后 agent 会自动接着做，不用回对话",
    live_off_tip: "提交后回到对话里说一声“看审阅台”", theme: "深色 / 浅色", lang: "EN", lang_tip: "Switch to English", reload: "重新读取项目文件",
    my: "我的点评", submit: "提交", general: "整体意见（可选）", general_ph: "比如：整体节奏偏慢；开场很好……", preview: "会提交的内容",
    submit_hint: "没标的条目都算通过。提交后写进项目的 out/review/feedback/，你的原话同时抄进 REVIEW.md。",
    fb_ok: "✓ 可以", fb_change: "✎ 要改", fb_ask: "? 疑问", fb_def: "不点就算通过", ph_change: "哪里要改、为什么", ph_ask: "哪里没看懂？",
    ph_suggest: "直接改成……（可选）", agree: "✓ 同意", overturn: "✎ 翻案", def_agree: "不点就算同意",
    dec_ok: "✓ 就这样", dec_more: "✎ 补一句", dec_def: "不点就按上面选的", fact_ok: "✓ 对", fact_bad: "✎ 有问题", fact_unsure: "? 拿不准", fact_def: "不点 = 没看",
    st_ok: "可以", st_change: "要改", st_ask: "疑问",
    decision_n: "决定 {i}", recommend: "我推荐 {r}", rec_chip: "推荐", pro: "好处", con: "代价", none_to_decide: "这一轮没有要你定的事。",
    least: "我最没把握的", delegated: "我替你定了", delegated_sub: "不同意就点“翻案”", decided: "已经定了", not_reviewed: "这一轮不审",
    other_assets: "其他材料", appendix: "附录", prev_said: "上一轮（{r}）你在审阅台里说 · {at}", prev_ok: "另有 {n} 条点了“可以”",
    changed: "我改了", overall: "整体", to_film: "去逐秒点评 →", no_round: "还没有审阅页（out/review/gate-<n>.json）。下面各页照样可以看、可以点评。",
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
    no_board: "还没有 shots.json（关卡 ② 才有），下面是 STORYBOARD.md。", no_board_file: "还没有分镜。", l_shot: "分镜 {x}", no_video: "（没有可播放的视频，只看关键帧）",
    sound_sub: "agent 听不见，只能看谱面和响度；这一页请你用耳朵。{bpm} BPM，{d} s。", comment_at: "在 {t} 处点评",
    sec_tip: "色块是乐段，点一下从那里播；刻度是落在画面动作上的音", listen: "请你听这几处", your_sound: "你的声音点评",
    none_sound: "还没有。播到哪里觉得不对，就点上面的“在 … 处点评”。", roll: "谱面和响度（每一行是一件乐器，颜色越深越响）",
    no_music: "还没有配乐。", sound_label: "声音 {t}", no_audio: "没有找到可以播放的音频（gate JSON 的 music.audio）。",
    facts_sub: "上屏的说法，和它背后的原话、出处。请重点看“上屏说法”有没有简化到错。", todo: "还没核实的", th_id: "#", th_claim: "素材（原文）",
    th_kind: "类别", th_screen: "上屏说法", th_src: "出处", th_you: "你看", dropped: "（已不用）", l_fact: "事实 {x}",
    no_facts: "NOTES.md 里没有素材清单表格，下面是原文。", no_notes: "还没有 NOTES.md。",
    film_sub: "播到哪里有话说，按 C 或点按钮，就在那一秒留一条。", film_list: "点评按时间排在下面",
    film_none: "还没有逐秒点评。", no_film: "这一轮没有视频。", film_label: "小样 {t}", del: "删",
    ledger_sub: "每件事谁拍板、现在是什么状态；我替你定的事都在下面，随时可以翻案。", th_what: "事", th_who: "谁拍板", th_status: "现在",
    agent_n: "我替你定的（{n}）", superseded: "已经作废的（{n}）", why: "理由", undo: "翻案要花", l_led: "决定 {x}",
    no_ledger: "DECISIONS.md 里没有决定表和“agent 定的事”，下面是原文。", no_dec: "还没有 DECISIONS.md。",
    history_sub: "每一轮你说的原话，和之后定了、改了什么（REVIEW.md）。", desk_subs: "审阅台的提交记录", no_history: "还没有记录。",
    docs_sub: "项目里的文档，原样排版。结构化的页面读不出来的内容，都在这里。", warnings: "这些没能按约定读出来（tools/desk/README.md）",
    no_docs: "项目里还没有文档。", l_doc: "{f} · {s}",
    tray_empty: "还没有点评。\n没标的条目都算通过。", sent_live: "已提交，agent 已经在接着做", sent: "已提交：{f}",
    hint_live: "已写进 {f}，原话也抄进了 REVIEW.md。agent 在等这份反馈，已经自动接着做了，不用再回对话。",
    hint_idle: "已写进 {f}，原话也抄进了 REVIEW.md。agent 这会儿没在等：回到对话里说一声“看审阅台”。",
    offline: "没有连上本地服务：回复已复制，粘贴到对话里即可", offline2: "没有连上本地服务：请复制下面的内容", refused: "没有提交成功：{e}",
    reply_head: "《{p}》{r} 的回复", by_rec: "（按推荐）", rest: "其余没标的都算通过。", round_name: "关卡 {r}", notes_round: "随手点评",
    submitted: "这一轮已经提交过（{at}）。再提交会另存一份，REVIEW.md 里也会多一节。",
  },
  en: {
    brand: "Review desk", noServer: "Can't read the project: open this page with bin/vh desk <project>.",
    v_round: "This round", v_concept: "Concept & outline", v_caption: "Captions", v_narration: "Narration", v_script: "Captions / narration",
    v_board: "Storyboard", v_sound: "Sound", v_facts: "Fact check", v_film: "Film · timecoded notes", v_ledger: "Decision ledger", v_history: "History", v_docs: "Documents",
    side_project: "This project", side_pages: "Static review pages",
    stages: ["Route", "Concept · outline", "Style", "Storyboard", "Sound", "Engine", "Scenes", "Self-review", "Draft", "Delivery"], gate_mark: "human gate",
    st_paused: "Paused", st_round: "Gate {id} · waiting for you", st_none: "In progress",
    live_on: "The agent is waiting", live_off: "The agent isn't waiting", live_on_tip: "Submit and the agent carries on by itself; no need to go back to the chat",
    live_off_tip: "After submitting, tell the agent in the chat: “check the desk”", theme: "Dark / light", lang: "中", lang_tip: "切换到中文", reload: "Read the project files again",
    my: "My notes", submit: "Submit", general: "Overall (optional)", general_ph: "e.g. the pace drags overall; the opening works…", preview: "What will be submitted",
    submit_hint: "Anything not marked passes. Submissions go to the project's out/review/feedback/, and your words into REVIEW.md.",
    fb_ok: "✓ OK", fb_change: "✎ Change", fb_ask: "? Question", fb_def: "untouched = approved", ph_change: "What to change, and why", ph_ask: "What's unclear?",
    ph_suggest: "Change it to… (optional)", agree: "✓ Agree", overturn: "✎ Overturn", def_agree: "untouched = agreed",
    dec_ok: "✓ As chosen", dec_more: "✎ Add a note", dec_def: "untouched = the option picked above", fact_ok: "✓ Right", fact_bad: "✎ Wrong", fact_unsure: "? Not sure", fact_def: "untouched = not checked",
    st_ok: "ok", st_change: "change", st_ask: "question",
    decision_n: "Decision {i}", recommend: "I recommend {r}", rec_chip: "recommended", pro: "Pro", con: "Cost", none_to_decide: "Nothing to decide this round.",
    least: "Least sure about", delegated: "Decided for you", delegated_sub: "disagree? click “Overturn”", decided: "Already decided", not_reviewed: "Not reviewed here",
    other_assets: "Other material", appendix: "Appendix", prev_said: "Last round ({r}) you said in the desk · {at}", prev_ok: "plus {n} marked “ok”",
    changed: "What I changed", overall: "Overall", to_film: "Timecoded notes →", no_round: "No review page yet (out/review/gate-<n>.json). You can still read and comment on every view.",
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
    transition: "Transition: ", unsure: "Unsure: ", no_board: "No shots.json yet (it comes at gate ②). Here is STORYBOARD.md.", no_board_file: "No storyboard yet.", l_shot: "Shot {x}",
    no_video: "(no video to play; keyframes only)",
    sound_sub: "The agent can't hear; it reads the score and the loudness. This page is for your ears. {bpm} BPM, {d} s.", comment_at: "Comment at {t}",
    sec_tip: "blocks are sections, click one to play from there; ticks are notes that land on actions", listen: "Please listen to these", your_sound: "Your sound notes",
    none_sound: "None yet. When something sounds off, click “Comment at …” above.", roll: "Score and loudness (one row per instrument, darker = louder)",
    no_music: "No music yet.", sound_label: "Sound {t}", no_audio: "No playable audio found (the gate JSON's music.audio).",
    facts_sub: "What goes on screen, and the source behind it. Check that the on-screen wording isn't simplified into something wrong.", todo: "Not verified yet",
    th_id: "#", th_claim: "Item (source wording)", th_kind: "Kind", th_screen: "On screen", th_src: "Source", th_you: "You", dropped: "(dropped)", l_fact: "Fact {x}",
    no_facts: "NOTES.md has no material table. Here it is as written.", no_notes: "No NOTES.md yet.",
    film_sub: "Wherever you have something to say, press C or the button to leave a note at that second.",
    film_list: "notes are listed below in time order", film_none: "No timecoded notes yet.", no_film: "No video this round.", film_label: "Film {t}", del: "Delete",
    ledger_sub: "Who decides each thing and where it stands; what I decided for you is below, and you can overturn any of it.", th_what: "Decision", th_who: "Who decides", th_status: "Now",
    agent_n: "Decided for you ({n})", superseded: "Superseded ({n})", why: "Why", undo: "Cost to undo", l_led: "Decision {x}",
    no_ledger: "DECISIONS.md has no ledger table and no agent decisions. Here it is as written.", no_dec: "No DECISIONS.md yet.",
    history_sub: "Your words each round, and what was decided and changed after (REVIEW.md).", desk_subs: "Submissions from the desk", no_history: "Nothing yet.",
    docs_sub: "The project's documents, as written. Whatever the structured views can't read is here.", warnings: "Not read by the contract (tools/desk/README.md)",
    no_docs: "No documents in the project yet.", l_doc: "{f} · {s}",
    tray_empty: "No notes yet.\nAnything not marked passes.", sent_live: "Submitted; the agent is on it", sent: "Submitted: {f}",
    hint_live: "Saved to {f}; your words are in REVIEW.md too. The agent was waiting for this and has carried on; no need to go back to the chat.",
    hint_idle: "Saved to {f}; your words are in REVIEW.md too. The agent isn't waiting right now: tell it in the chat, “check the desk”.",
    offline: "Couldn't reach the local server: the reply is copied, paste it into the chat", offline2: "Couldn't reach the local server: copy the text below", refused: "Not submitted: {e}",
    reply_head: "Reply to {r} of “{p}”", by_rec: " (recommended)", rest: "Everything not marked passes.", round_name: "gate {r}", notes_round: "notes",
    submitted: "Already submitted this round ({at}). Submitting again saves another copy and adds another section to REVIEW.md.",
  },
};

let D = null, ROUND = null, FB = null, KEY = "", VIEW = "round", DOC = "", LANG = "zh", L = STR.zh;
let capFilter = "all", filmT = 0;
const TOKEN = (document.querySelector('meta[name="desk-token"]') || {}).content || "";
const $ = (s, el = document) => el.querySelector(s), $$ = (s, el = document) => [...el.querySelectorAll(s)];
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const t = (k, vars) => String(L[k] != null ? L[k] : STR.en[k] != null ? STR.en[k] : k).replace(/\{(\w+)\}/g, (_, v) => (vars && vars[v] != null ? vars[v] : ""));
const fmt = (x) => { if (x == null || isNaN(x)) return "–"; const m = Math.floor(x / 60), s = x - m * 60; return `${m}:${s.toFixed(1).padStart(4, "0")}`; };
const src = (p) => (/^https?:\/\//.test(p || "") ? p : "/p/" + String(p || "").split("/").map(encodeURIComponent).join("/"));
const isVideo = (p) => /\.(mp4|webm|mov|m4v)$/i.test(p || ""), isImage = (p) => /\.(png|jpe?g|gif|webp|svg|avif)$/i.test(p || ""), isAudio = (p) => /\.(wav|mp3|m4a|ogg|flac|aac|opus)$/i.test(p || "");
const cut = (s, n) => (String(s).length > n ? String(s).slice(0, n) + "…" : String(s));
const store = {
  get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private window: the draft just isn't kept */ } },
};
function toast(m) { const el = $("#toast"); el.textContent = m; el.classList.add("show"); clearTimeout(el._h); el._h = setTimeout(() => el.classList.remove("show"), 3200); }
function cssVar(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
const SEGC = () => ["--seg1", "--seg2", "--seg3", "--seg4", "--seg5", "--seg6"].map(cssVar);
function segColor(id) { const i = D.outline.findIndex((o) => o.id === id); const c = SEGC(); return i < 0 ? cssVar("--soft") : c[i % c.length]; }
function partColor(part) { let h = 0; for (const ch of String(part)) h = (h * 31 + ch.charCodeAt(0)) >>> 0; return SEGC()[h % 6]; }
try { const th = localStorage.getItem("desk:theme"); if (th) document.documentElement.dataset.theme = th; } catch (e) { /* no storage */ }

const VIEWS = ["round", "concept", "script", "board", "sound", "facts", "film", "ledger", "history", "docs"];
const KIND = { dec: "round", least: "round", deleg: "round", concept: "concept", seg: "concept", cap: "script", shot: "board", atime: "sound", fact: "facts", time: "film", led: "ledger", doc: "docs" };

// ---------- load ----------
async function load() {
  let data = null;
  try { const r = await fetch("/api/data", { cache: "no-store" }); if (r.ok) data = await r.json(); } catch (e) { /* server down */ }
  if (!data) { $("#view").innerHTML = `<div class="empty">${esc(t("noServer"))}</div>`; return; }
  D = data;
  let pick = null; try { pick = localStorage.getItem("desk:lang"); } catch (e) { /* no storage */ }
  setLang(pick === "zh" || pick === "en" ? pick : D.lang === "en" ? "en" : "zh");
  ROUND = D.rounds[D.rounds.length - 1] || { id: "notes", gate: "", data: { decisions: [], least_sure: [], decided: [], delegated: [], assets: [], appendix: [], listen: [] } };
  KEY = `desk:${D.project.slug}:${ROUND.id}`;
  FB = store.get(KEY) || { decisions: {}, items: {}, general: "" };
  $("#general").value = FB.general || "";
  $("#ptitle").textContent = D.project.title;
  renderChrome(); route();
}
function save() { store.set(KEY, FB); renderSide(); renderCount(); }
function setLang(l) {
  LANG = l; L = STR[l]; document.documentElement.lang = l === "zh" ? "zh-CN" : "en";
  document.title = `${t("brand")}${D ? " · " + D.project.title : ""}`;
  $("#brand").textContent = t("brand"); $("#myLabel").textContent = t("my"); $("#trayTitle").textContent = t("my");
  $("#submitTop").textContent = t("submit"); $("#submit").textContent = t("submit"); $("#generalLabel").textContent = t("general");
  $("#general").placeholder = t("general_ph"); $("#previewLabel").textContent = t("preview"); $("#submitHint").textContent = t("submit_hint");
  $("#lang").textContent = t("lang"); $("#lang").title = t("lang_tip"); $("#theme").title = t("theme"); $("#reload").title = t("reload");
}

// ---------- chrome ----------
function renderChrome() {
  const ps = $("#pstatus");
  ps.textContent = D.project.paused ? t("st_paused") : D.rounds.length ? t("st_round", { id: ROUND.id }) : t("st_none");
  ps.className = "pill" + (D.project.paused ? " paused" : "");
  const gates = { 1: "①", 3: "②", 8: "③" };
  $("#rail").innerHTML = L.stages.map((n, i) => `${i ? '<span class="sep"></span>' : ""}<li class="${i < D.stage ? "done" : i === D.stage ? "current" : ""}"><span class="st">${i} ${esc(n)}</span>${gates[i] ? `<span class="gate" title="${esc(t("gate_mark"))}">${gates[i]}</span>` : ""}</li>`).join("");
  pollLive();
}
function viewName(v) { return v === "script" ? t(D.captions.kind === "narration" ? "v_narration" : D.captions.kind === "caption" ? "v_caption" : "v_script") : t("v_" + v); }
function marked(view) { return Object.entries(FB.items).filter(([k, v]) => KIND[k.split(":")[0]] === view && v.status && v.status !== "ok").length; }
function renderSide() {
  const n = { script: D.captions.rows.length, board: (D.shots.items || []).length, facts: D.facts.filter((f) => !f.dropped).length,
    ledger: D.agent_decided.filter((a) => !a.superseded).length, history: D.history.length, docs: D.docs.length };
  const need = (ROUND.data.decisions || []).length;
  $("#side").innerHTML = `<h6>${esc(t("side_project"))}</h6>` + VIEWS.map((id) => {
    const c = marked(id);
    const extra = id === "round" && need ? `<span class="cnt">${need}${c ? ` · <b>${c} ✎</b>` : ""}</span>` : n[id] ? `<span class="cnt">${n[id]}${c ? ` · <b>${c} ✎</b>` : ""}</span>` : c ? `<span class="cnt"><b>${c} ✎</b></span>` : "";
    return `<a href="#${id}" class="${VIEW === id ? "on" : ""}"><span>${esc(viewName(id))}</span>${extra}</a>`;
  }).join("") + (D.rounds.some((r) => r.page) ? `<h6>${esc(t("side_pages"))}</h6>` + D.rounds.filter((r) => r.page).map((r) => `<a href="${esc(src(r.page))}" target="_blank" rel="noopener"><span>gate-${esc(r.id)}</span><span class="cnt">↗</span></a>`).join("") : "");
}
function renderCount() { $("#cnt").textContent = Object.values(FB.items).filter((v) => v.status).length + (FB.general ? 1 : 0); }
function route() {
  const h = decodeURIComponent((location.hash || "#round").slice(1)), [v, ...rest] = h.split("/");
  VIEW = VIEWS.includes(v) ? v : "round"; DOC = VIEW === "docs" ? rest.join("/") : DOC;
  renderSide(); renderCount(); render();
}
window.addEventListener("hashchange", route);

// ---------- the ✓ / ✎ / ? control ----------
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
  const box = b.closest(".fb"), tgt = box.dataset.target, cur = FB.items[tgt] || {};
  const st = cur.status === b.dataset.st ? "" : b.dataset.st;
  if (!st) delete FB.items[tgt];
  else FB.items[tgt] = Object.assign({}, cur, { status: st, label: box.dataset.label }, box.dataset.t ? { t: +box.dataset.t } : {}, box.dataset.orig != null ? { orig: box.dataset.orig } : {});
  save(); refreshFb(box);
});
document.addEventListener("input", (e) => {
  const el = e.target.closest(".fb-more [data-k]"); if (!el) return;
  const tgt = el.closest(".fb").dataset.target; FB.items[tgt] = Object.assign({}, FB.items[tgt] || {}, { [el.dataset.k]: el.value }); store.set(KEY, FB);
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

// ---------- views ----------
const VIEWFN = { round: vRound, concept: vConcept, script: vScript, board: vBoard, sound: vSound, facts: vFacts, film: vFilm, ledger: vLedger, history: vHistory, docs: vDocs };
const WIRE = { round: wireRound, script: wireScript, board: wireBoard, sound: wireSound, film: wireFilm, concept: wireConcept };
function render() {
  $("#view").innerHTML = VIEWFN[VIEW]();
  $$("[data-mark]").forEach(markHost);
  document.onkeydown = null;   // the film view sets its own C key
  (WIRE[VIEW] || (() => {}))();
  window.scrollTo(0, 0);
}
const COLON = () => (LANG === "zh" ? "：" : ": ");
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
  return `<p class="note">${esc(note)}</p><div class="card" data-mark="doc:${esc(file)}">${docHtml(doc, part)}${fbCtl("doc:" + file, file)}</div>`;
}
function media(a, opts = {}) {
  const cap = a.caption ? `<figcaption>${esc(a.caption)}</figcaption>` : "";
  if (isVideo(a.path)) return `<figure class="media"><video src="${esc(src(a.path))}"${a.poster ? ` poster="${esc(src(a.poster))}"` : ""} controls preload="metadata"${opts.id ? ` id="${opts.id}"` : ""}></video>${cap}</figure>`;
  if (isImage(a.path)) return `<figure class="media"><a href="${esc(src(a.path))}" target="_blank" rel="noopener"><img src="${esc(src(a.path))}" alt="" loading="lazy"></a>${cap}</figure>`;
  if (isAudio(a.path)) return `<figure class="media"><audio src="${esc(src(a.path))}" controls preload="metadata" style="width:100%"></audio>${cap}</figure>`;
  return `<p class="small"><a href="${esc(src(a.path))}" target="_blank" rel="noopener">${esc(a.path)}</a>${a.caption ? " · " + esc(a.caption) : ""}</p>`;
}
const filmAsset = () => { const g = ROUND.data; const want = typeof g.film === "string" ? g.film : ""; return (g.assets || []).find((a) => a && (want ? a.path === want : isVideo(a.path))) || (want ? { path: want } : null); };

function vRound() {
  const g = ROUND.data, ST = { ok: [t("st_ok"), "ok"], change: [t("st_change"), "chg"], ask: [t("st_ask"), "acc"] };
  if (!D.rounds.length) return `<h1>${esc(t("v_round"))}</h1><p class="note">${esc(t("no_round"))}</p>`;
  const prev = [...D.feedback].reverse().find((f) => f.round !== ROUND.id);
  const last = [...D.history].reverse().find((h) => h.notes.length);
  const decs = (g.decisions || []).map((d, i) => {
    const pick = FB.decisions[d.id] || d.recommend;
    return `<div class="card dec"><div class="tiny muted">${esc(t("decision_n", { i: i + 1 }))}${d.cost ? " · " + esc(d.cost) : ""}</div><p class="q">${esc(d.question || "")}</p>
      ${d.recommend ? `<div class="small muted">${esc(t("recommend", { r: d.recommend }))}${d.why ? COLON() + esc(d.why) : ""}</div>` : ""}
      <div class="opts">${(d.options || []).map((o) => `<label class="opt ${pick === o.id ? "on" : ""}"><input type="radio" name="dec-${esc(d.id)}" value="${esc(o.id)}" ${pick === o.id ? "checked" : ""} data-dec="${esc(d.id)}">
        <div><div class="l">${esc(o.id)}${o.label ? " · " + esc(o.label) : ""} ${o.id === d.recommend ? `<span class="chip acc">${esc(t("rec_chip"))}</span>` : ""}</div>
        ${o.pro || o.con ? `<div class="pc"><div class="p"><b>${esc(t("pro"))}</b>${esc(o.pro || "")}</div><div class="c"><b>${esc(t("con"))}</b>${esc(o.con || "")}</div></div>` : ""}</div></label>`).join("")}</div>
      ${(g.assets || []).filter((a) => a && a.for === d.id && !isVideo(a.path)).map((a) => media(a)).join("")}
      ${fbCtl("dec:" + d.id, t("l_dec", { x: d.question || d.id }), { labels: [t("dec_ok"), t("dec_more"), t("fb_ask")], def: t("dec_def") })}</div>`;
  }).join("");
  const vids = (g.assets || []).filter((a) => a && isVideo(a.path));
  const film = filmAsset();
  const side = vids.map((a, i) => media(a) + (i === 0 && film ? `<div class="small" style="margin:-8px 0 14px"><a href="#film">${esc(t("to_film"))}</a></div>` : "")).join("");
  const least = (g.least_sure || []).map((l, i) => { const k = "least:" + (l.id || i); return `<div class="card" data-mark="${esc(k)}"><b>${esc(l.id || "")}</b><div class="small" style="margin-top:4px">${esc(l.note || "")}</div>${fbCtl(k, t("l_least", { x: l.id || cut(l.note, 24) }))}</div>`; }).join("");
  const deleg = (g.delegated || []).map((x, i) => `<div class="card" data-mark="deleg:${i}"><div class="small">${esc(x)}</div>${fbCtl("deleg:" + i, t("l_deleg", { x: cut(x, 28) }), { labels: [t("agree"), t("overturn"), t("fb_ask")], def: t("def_agree") })}</div>`).join("");
  const others = (g.assets || []).filter((a) => a && !isVideo(a.path) && !(g.decisions || []).some((d) => d.id === a.for)).map((a) => media(a)).join("");
  const appendix = (g.appendix || []).map((a) => a && (a.html ? `<details class="card" style="margin-bottom:10px"><summary>${esc(a.title || "")}</summary><div class="md">${a.html}</div></details>`
    : a.path ? `<div class="card small" style="margin-bottom:10px">${esc(a.title || "")} · ${docOf(a.path) ? `<a href="#docs/${esc(a.path)}">${esc(a.path)}</a>` : `<a href="${esc(src(a.path))}" target="_blank" rel="noopener">${esc(a.path)}</a>`}</div>` : "")).join("");
  const before = prev || last ? `<div class="card" style="margin-bottom:18px">
      ${prev ? `<div class="tiny muted">${esc(t("prev_said", { r: prev.round, at: prev.submitted_at.replace("T", " ") }))}</div>
        <div style="margin:6px 0 4px">${Object.entries(prev.decisions).map(([k, v]) => `<span class="chip acc">${esc(k)}: ${esc(v)}</span>`).join("")}</div>
        ${prev.items.filter((i) => i.status !== "ok" || i.text).map((i) => `<div class="small" style="margin:4px 0"><span class="chip ${(ST[i.status] || ST.ok)[1]}">${esc((ST[i.status] || ST.ok)[0])}</span>${esc(i.label)}${i.text ? `${COLON()}<b style="font-weight:500">${esc(String(i.text).trim())}</b>` : ""}</div>`).join("")}
        ${prev.general ? `<div class="small" style="margin-top:4px"><span class="chip">${esc(t("overall"))}</span>${esc(prev.general)}</div>` : ""}
        <div class="tiny muted" style="margin-top:4px">${esc(t("prev_ok", { n: prev.items.filter((i) => i.status === "ok" && !i.text).length }))}</div>` : ""}
      ${last ? `<div class="tiny muted" style="margin-top:10px">${esc(t("changed"))} · ${esc(last.title)}</div><ul class="small" style="margin:4px 0 0;padding-left:18px">${last.notes.map((n) => `<li>${esc(n.k)}${COLON()}${esc(n.v)}</li>`).join("")}</ul>` : ""}</div>` : "";
  const sent = FB.submittedAt ? `<p class="note">${esc(t("submitted", { at: FB.submittedAt }))}</p>` : "";
  return `<h1>${esc(g.title || t("st_round", { id: ROUND.id }))}</h1><p class="sub">${esc(g.summary || "")}</p>${sent}${before}
    <div class="grid g2" style="align-items:start"><div>${decs || `<div class="card muted">${esc(t("none_to_decide"))}</div>`}</div><div>${side}</div></div>
    ${least ? `<h2>${esc(t("least"))} <span class="tiny muted">（${(g.least_sure || []).length}）</span></h2><div class="grid g3">${least}</div>` : ""}
    ${deleg ? `<h2>${esc(t("delegated"))} <span class="tiny muted">${esc(t("delegated_sub"))}</span></h2><div class="grid g3">${deleg}</div>` : ""}
    ${(g.decided || []).length ? `<h2>${esc(t("decided"))}</h2><div class="card small"><ul style="margin:0;padding-left:18px">${g.decided.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>` : ""}
    ${g.not_reviewed ? `<p class="small muted" style="margin-top:14px">${esc(t("not_reviewed"))}${COLON()}${esc(g.not_reviewed)}</p>` : ""}
    ${others ? `<h2>${esc(t("other_assets"))}</h2><div class="grid g3">${others}</div>` : ""}
    ${appendix ? `<h2>${esc(t("appendix"))}</h2>${appendix}` : ""}`;
}
function wireRound() { $$("input[data-dec]").forEach((r) => r.addEventListener("change", () => { FB.decisions[r.dataset.dec] = r.value; save(); render(); })); }

function vConcept() {
  const c = D.concept, O = D.outline.filter((o) => o.t0 != null && o.t1 != null), total = O.length ? Math.max(...O.map((o) => o.t1)) : 0;
  if (!docOf("BRIEF.md")) return `<h1>${esc(t("v_concept"))}</h1><div class="empty">${esc(t("no_brief"))}</div>`;
  const specGet = (k) => (D.spec.find((s) => s.k.toLowerCase().startsWith(k)) || {}).v || "";
  const head = `<div class="card" data-mark="concept:line"><div class="tiny muted">${esc(t("concept"))}</div><div class="serif" style="font-size:21px;line-height:1.5;margin:4px 0 10px">${esc(c.line || "—")}</div>
    <dl class="kv">${c.spine ? `<dt>${esc(t("spine"))}</dt><dd>${esc(c.spine)}</dd>` : ""}${c.motif ? `<dt>${esc(t("motif"))}</dt><dd>${esc(c.motif)}</dd>` : ""}${c.end ? `<dt>${esc(t("end"))}</dt><dd>${esc(c.end)}</dd>` : ""}
    <dt>${esc(t("spec"))}</dt><dd>${["output", "effort", "watch on", "review language"].map(specGet).filter(Boolean).map((x) => `<span class="chip">${esc(x.split("（")[0].split("  ")[0])}</span>`).join("")}</dd></dl>
    ${fbCtl("concept:line", t("l_concept"))}</div>`;
  if (!D.outline.length) return `<h1>${esc(t("v_concept"))}</h1>${head}<h2>${esc(t("outline"))}</h2>${fallback(t("no_outline"), "BRIEF.md", /^(Outline|大纲)/i)}`;
  const bar = O.length ? `<div class="tbar">${O.map((o) => `<div data-seg="${esc(o.id)}" style="flex:${Math.max(0.1, o.t1 - o.t0).toFixed(2)};background:${segColor(o.id)}">${esc(o.title)}</div>`).join("")}</div><div class="tticks">${[0, 0.25, 0.5, 0.75, 1].map((f) => `<span>${fmt(total * f)}</span>`).join("")}</div>` : "";
  const segs = D.outline.map((o, i) => {
    const caps = D.captions.rows.filter((x) => x.seg === o.id);
    const when = o.t0 != null ? `${fmt(o.t0)}–${fmt(o.t1)}${o.t1 != null ? ` · ${(o.t1 - o.t0).toFixed(0)} s` : ""}` : "";
    return `<div class="card segcard" id="seg-${esc(o.id)}" data-mark="seg:${esc(o.id)}"><div class="stripe" style="background:${segColor(o.id)}"></div><div>
      <div style="display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap"><div><span class="tiny muted">${esc(t("seg_n", { i: o.id || i + 1 }))}</span> <b style="font-size:16px">${esc(o.title)}</b>${o.tag ? `<span class="tag">${esc(o.tag)}</span>` : ""} ${o.stage && o.stage !== "—" ? `<span class="chip acc">${esc(o.stage)}</span>` : ""}</div>
        <span class="tiny muted">${when}${o.bars ? ` · ${esc(t("bars", { b: o.bars }))}` : ""}</span></div>
      ${o.know ? `<div style="margin-top:6px"><span class="chip">${esc(t("know"))}</span>${esc(o.know)}</div>` : ""}
      ${o.visual ? `<div class="small muted" style="margin-top:4px"><span class="chip">${esc(t("visual"))}</span>${esc(o.visual)}</div>` : ""}
      ${caps.length ? `<details style="margin-top:8px"><summary class="small">${esc(t("seg_caps", { n: caps.length }))}</summary>${caps.map((x) => `<div class="segcap serif"><span class="id">${esc(x.id)}</span>${esc(x.text)}</div>`).join("")}<div class="tiny"><a href="#script">${esc(t("to_script"))}</a></div></details>` : ""}
      ${fbCtl("seg:" + o.id, t("l_seg", { i: o.id, x: o.title }))}</div></div>`;
  }).join("");
  return `<h1>${esc(t("v_concept"))}</h1><p class="sub">${esc(t("concept_sub", { n: D.outline.length }))}</p>${head}
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
  if (!C.rows.length) return `<h1>${esc(viewName("script"))}</h1>` + (docOf("SCRIPT.md") ? fallback(t("no_script"), "SCRIPT.md") : `<div class="empty">${esc(t("no_script_file"))}</div>`);
  const keep = (x) => capFilter === "all" || (capFilter === "mine" && FB.items["cap:" + x.id]) || (capFilter === "terms" && x.term) || (capFilter === "facts" && x.facts.length) || (capFilter === "fast" && speed(x).r > speed(x).lim[0]);
  const lab = C.kind === "narration" ? "l_vo" : "l_cap";
  const row = (x) => {
    const sp = speed(x), col = sp.r == null ? "var(--faint)" : sp.r <= sp.lim[0] ? "var(--ok)" : sp.r <= sp.lim[1] ? "var(--chg)" : "var(--bad)";
    return `<div class="cap" id="cap-${esc(x.id)}" data-mark="cap:${esc(x.id)}"><div><div class="id">${esc(x.id)}</div><div class="tm">${x.t0 != null ? fmt(x.t0) : esc(x.bars)}</div></div>
      <div>${x.term ? `<div class="term" title="${esc(t("term"))}">${esc(x.term)}</div><br>` : ""}<div class="txt serif">${esc(x.text)}</div>${x.visual ? `<div class="vis">${esc(t("visual"))}${COLON()}${esc(x.visual)}</div>` : ""}
        <div class="meter">${sp.r != null ? `<span>${esc(t("chars", { n: sp.n, s: sp.s.toFixed(1) }))}</span><span class="bar"><i style="width:${Math.min(100, (sp.r / (sp.lim[1] * 1.2)) * 100)}%;background:${col}"></i></span><span style="color:${col}">${sp.r.toFixed(1)}${esc(t("per_s"))}</span>` : ""}${x.facts.map((f) => `<a class="chip acc" href="#facts">${esc(f)}</a>`).join("")}</div></div>
      <div>${fbCtl("cap:" + x.id, t(lab, { x: x.id }), { suggest: x.text })}</div></div>`;
  };
  const groups = D.outline.map((o) => ({ o, rows: C.rows.filter((x) => x.seg === o.id && keep(x)) })).concat([{ o: null, rows: C.rows.filter((x) => !D.outline.some((o) => o.id === x.seg) && keep(x)) }]);
  const html = groups.filter((g) => g.rows.length).map(({ o, rows }) => `<div class="capgroup"><div class="gh">${o ? `<i style="background:${segColor(o.id)}"></i><span>${esc(t("seg_n", { i: o.id }))} · ${esc(o.title)}</span>${o.stage && o.stage !== "—" ? `<span class="chip acc" style="font-weight:400">${esc(o.stage)}</span>` : ""}${o.t0 != null ? `<span class="tiny muted" style="font-weight:400">${fmt(o.t0)}–${fmt(o.t1)}</span>` : ""}` : `<span>${esc(t("other_seg"))}</span>`}</div>${rows.map(row).join("")}</div>`).join("");
  const F = [["all", "f_all"], ["mine", "f_mine"], ["terms", "f_terms"], ["facts", "f_facts"], ["fast", "f_fast"]].filter(([k]) => k !== "terms" || C.rows.some((x) => x.term));
  return `<h1>${esc(viewName("script"))}</h1><p class="sub">${esc(t("script_sub", { n: C.rows.length, g: SPEED.zh[0], y: SPEED.zh[1], eg: SPEED.en[0], ey: SPEED.en[1] }))}</p>
    <div class="filters">${F.map(([k, n]) => `<button type="button" data-f="${k}" class="${capFilter === k ? "on" : ""}">${esc(t(n))}</button>`).join("")}</div>${html || `<div class="empty">${esc(t("none_match"))}</div>`}`;
}
function wireScript() { $$(".filters button").forEach((b) => b.addEventListener("click", () => { capFilter = b.dataset.f; render(); })); }

function vBoard() {
  const S = D.shots.items || [];
  if (!S.length) return `<h1>${esc(t("v_board"))}</h1>` + (docOf("STORYBOARD.md") ? fallback(t("no_board"), "STORYBOARD.md") : `<div class="empty">${esc(t("no_board_file"))}</div>`);
  const timed = S.filter((s) => s.start != null && s.end != null);
  const track = timed.map((s) => `<div data-shot="${esc(s.id)}" class="${s.unsure ? "unsure" : ""}" style="flex:${Math.max(0.1, s.end - s.start).toFixed(2)};background:${segColor(s.seg)}">${esc(s.id)}</div>`).join("");
  const cards = S.map((s) => `<div class="card shot ${s.unsure ? "unsure" : ""}" id="shot-${esc(s.id)}" data-id="${esc(s.id)}" data-mark="shot:${esc(s.id)}">
      <div class="thumb" data-shot="${esc(s.id)}">${s.frame ? `<img src="${esc(src(s.frame))}" alt="" loading="lazy">` : ""}<span class="sid">${esc(s.id)}</span>${s.start != null ? `<span class="play">▶ ${fmt(s.start)}–${fmt(s.end)}</span>` : ""}</div>
      <div class="body"><div class="lab">${esc(s.label || "")} <span class="tiny muted">${esc(s.segment || "")}${s.start != null && s.end != null ? ` · ${(s.end - s.start).toFixed(1)} s` : ""}</span></div>
        ${s.caption ? `<div class="capline serif">${esc(s.caption)}</div>` : `<div class="tiny muted" style="margin-top:6px">${esc(t("no_shot_caption"))}</div>`}
        ${s.reads.length ? `<ul>${s.reads.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>` : ""}
        ${s.transition ? `<div class="tiny muted" style="margin-top:6px">${esc(t("transition"))}${esc(s.transition)}</div>` : ""}
        ${s.unsure ? `<div class="unsure-note">${esc(t("unsure"))}${esc(typeof s.unsure === "string" ? s.unsure : "")}</div>` : ""}
        ${fbCtl("shot:" + s.id, t("l_shot", { x: s.id }))}</div></div>`).join("");
  const player = D.shots.video ? `<div class="player"><video id="bv" src="${esc(src(D.shots.video))}" controls preload="metadata"></video>${track ? `<div class="strack">${track}<div class="playhead" id="bph"></div></div>` : ""}</div>` : `<p class="small muted">${esc(t("no_video"))}</p>`;
  return `<h1>${esc(t("v_board"))}</h1><p class="sub">${esc(D.shots.note ? D.shots.note + " · " : "")}${esc(t("board_sub"))}</p>${player}<div class="grid g3">${cards}</div>`;
}
function wireBoard() {
  const v = $("#bv"); if (!v) return;
  const S = (D.shots.items || []).filter((s) => s.start != null && s.end != null), total = S.length ? Math.max(...S.map((s) => s.end)) : 1; let stopAt = null;
  const go = (id) => { const s = S.find((x) => x.id === id); if (!s) return; v.currentTime = s.start + 0.01; stopAt = s.end; v.play(); };
  $$("[data-shot]").forEach((el) => el.addEventListener("click", () => go(el.dataset.shot)));
  v.addEventListener("timeupdate", () => {
    if (stopAt != null && v.currentTime >= stopAt - 0.03) { v.pause(); stopAt = null; }
    const ph = $("#bph"); if (ph) ph.style.left = Math.min(100, (v.currentTime / total) * 100) + "%";
    const cur = S.find((s) => v.currentTime >= s.start && v.currentTime < s.end);
    $$(".shot").forEach((c) => c.classList.toggle("active", !!cur && c.dataset.id === cur.id));
  });
}

function vSound() {
  const M = D.music;
  if (!M || (!M.audio && !(M.sections || []).length)) return `<h1>${esc(t("v_sound"))}</h1><div class="empty">${esc(t("no_music"))}</div>`;
  const dur = M.duration || Math.max(1, ...(M.sections || []).map((s) => s.end));
  const secs = (M.sections || []).map((s, i) => `<div data-t="${s.start}" title="${esc(s.name)}" style="flex:${Math.max(0.05, s.end - s.start).toFixed(2)};background:${SEGC()[i % 6]}">${esc(s.label || s.name)}</div>`).join("");
  const hits = (M.hits || []).map((h) => `<i style="left:${(h.t / dur) * 100}%;background:${partColor(h.part)}" title="${esc(h.part)} ${fmt(h.t)}"></i>`).join("");
  const listen = (ROUND.data.listen || []).map((l) => `<button class="btn" type="button" data-seek="${l.t}">▶ ${fmt(l.t)} · ${esc(l.note)}</button>`).join("");
  const tcs = Object.entries(FB.items).filter(([k]) => k.startsWith("atime:")).sort((a, b) => a[1].t - b[1].t);
  return `<h1>${esc(t("v_sound"))}</h1><p class="sub">${esc(t("sound_sub", { bpm: M.bpm || "–", d: (+dur).toFixed(1) }))}</p>
    <div class="card">${M.audio ? `<audio id="au" src="${esc(src(M.audio))}" controls preload="metadata" style="width:100%"></audio>` : `<p class="small muted">${esc(t("no_audio"))}</p>`}
      ${secs ? `<div class="secbar" id="secbar">${secs}<div class="playhead" id="aph"></div></div><div class="hits">${hits}</div>` : ""}
      ${M.audio ? `<div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap"><button class="btn" type="button" id="atc">${atTime("atnow")}</button><span class="tiny muted">${esc(t("sec_tip"))}</span></div>` : ""}</div>
    ${listen ? `<h2>${esc(t("listen"))}</h2><div class="listen">${listen}</div>` : ""}
    <h2>${esc(t("your_sound"))} <span class="tiny muted">（${tcs.length}）</span></h2>
    <div>${tcs.map(([k, v]) => `<div class="card" style="margin-bottom:10px" data-mark="${esc(k)}"><span class="chip acc" data-seek="${v.t}">${fmt(v.t)}</span>${fbCtl(k, t("sound_label", { t: fmt(v.t) }), { t: v.t })}</div>`).join("") || `<div class="muted small">${esc(t("none_sound"))}</div>`}</div>
    ${M.roll ? `<details style="margin-top:22px"><summary>${esc(t("roll"))}</summary><img class="roll" src="${esc(src(M.roll))}" alt="" loading="lazy"></details>` : ""}`;
}
function wireSound() {
  const a = $("#au"); if (!a) return;
  const dur = D.music.duration || 1;
  $$("[data-seek]").forEach((b) => b.addEventListener("click", () => { a.currentTime = +b.dataset.seek; a.play(); }));
  $$("#secbar [data-t]").forEach((b) => b.addEventListener("click", () => { a.currentTime = +b.dataset.t; a.play(); }));
  a.addEventListener("timeupdate", () => { const ph = $("#aph"); if (ph) ph.style.left = Math.min(100, (a.currentTime / (a.duration || dur)) * 100) + "%"; $("#atnow").textContent = fmt(a.currentTime); });
  $("#atc").addEventListener("click", () => { const x = +a.currentTime.toFixed(1); a.pause(); FB.items["atime:" + x] = { status: "change", label: t("sound_label", { t: fmt(x) }), t: x, text: "" }; save(); render(); const ta = $(`[data-target="atime:${x}"] textarea`); if (ta) ta.focus(); });
}

function vFacts() {
  if (!D.facts.length) return `<h1>${esc(t("v_facts"))}</h1>` + (docOf("NOTES.md") ? fallback(t("no_facts"), "NOTES.md") : `<div class="empty">${esc(t("no_notes"))}</div>`);
  const rows = D.facts.map((f) => `<tr class="${f.dropped ? "dropped" : ""}" id="fact-${esc(f.id.slice(1))}" data-mark="fact:${esc(f.id)}"><td><b>${esc(f.id)}</b><div class="tiny muted">${esc(f.kind)}</div></td>
      <td>${esc(f.claim)}${f.dropped ? `<div class="tiny">${esc(t("dropped"))}</div>` : ""}</td><td class="serif">${esc(f.onscreen)}</td><td class="small muted">${esc(f.source)}</td>
      <td style="min-width:230px">${f.dropped || !f.id ? "" : fbCtl("fact:" + f.id, t("l_fact", { x: f.id }), { labels: [t("fact_ok"), t("fact_bad"), t("fact_unsure")], def: t("fact_def") })}</td></tr>`).join("");
  return `<h1>${esc(t("v_facts"))}</h1><p class="sub">${esc(t("facts_sub"))}</p>
    ${D.fact_todo.length ? `<div class="card" style="margin-bottom:16px"><b class="small">${esc(t("todo"))}</b><ul class="small" style="margin:6px 0 0;padding-left:18px">${D.fact_todo.map((x) => `<li>${x.done ? "✓ " : ""}${esc(x.text)}</li>`).join("")}</ul></div>` : ""}
    <div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_id"))}</th><th>${esc(t("th_claim"))}</th><th>${esc(t("th_screen"))}</th><th>${esc(t("th_src"))}</th><th>${esc(t("th_you"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
}

function vFilm() {
  const v = filmAsset();
  if (!v) return `<h1>${esc(t("v_film"))}</h1><div class="empty">${esc(t("no_film"))}</div>`;
  const tcs = Object.entries(FB.items).filter(([k]) => k.startsWith("time:")).sort((a, b) => a[1].t - b[1].t);
  return `<h1>${esc(t("v_film"))}</h1><p class="sub">${v.caption ? esc(v.caption) + " · " : ""}${esc(t("film_sub"))}</p>
    <div class="player"><video id="fv" src="${esc(src(v.path))}"${v.poster ? ` poster="${esc(src(v.poster))}"` : ""} controls preload="metadata"></video>
      <div class="scrub" id="scrub"><div class="fill" id="sfill"></div>${tcs.map(([, x]) => `<div class="mk" data-mt="${x.t}" style="background:${x.status === "ask" ? "var(--ask)" : x.status === "ok" ? "var(--ok)" : "var(--chg)"}" title="${fmt(x.t)}"></div>`).join("")}</div>
      <div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap"><button class="btn" type="button" id="tcadd">${atTime("tnow")} (C)</button><span class="tiny muted">${esc(t("film_list"))}</span></div></div>
    <div>${tcs.map(([k, x]) => `<div class="tc" data-mark="${esc(k)}"><span class="t" data-seek="${x.t}">${fmt(x.t)}</span><div>${fbCtl(k, t("film_label", { t: fmt(x.t) }), { t: x.t })}</div><button class="btn ghost" type="button" data-del="${esc(k)}">${esc(t("del"))}</button></div>`).join("") || `<div class="muted small" style="margin-top:12px">${esc(t("film_none"))}</div>`}</div>`;
}
function wireFilm() {
  const v = $("#fv"); if (!v) return;
  const place = () => { const d = v.duration || 0; $$("#scrub .mk").forEach((m) => { m.style.left = d ? Math.min(100, (+m.dataset.mt / d) * 100) + "%" : "0"; m.style.display = d ? "" : "none"; }); };
  v.addEventListener("loadedmetadata", () => { if (filmT) v.currentTime = Math.min(filmT, v.duration || filmT); place(); }, { once: true });
  v.addEventListener("timeupdate", () => { filmT = v.currentTime; $("#tnow").textContent = fmt(v.currentTime); $("#sfill").style.width = (v.duration ? (v.currentTime / v.duration) * 100 : 0) + "%"; });
  $("#scrub").addEventListener("click", (e) => { if (!v.duration) return; const r = e.currentTarget.getBoundingClientRect(); v.currentTime = ((e.clientX - r.left) / r.width) * v.duration; });
  const add = () => { const x = +v.currentTime.toFixed(1); v.pause(); FB.items["time:" + x] = { status: "change", label: t("film_label", { t: fmt(x) }), t: x, text: "" }; save(); render(); const ta = $(`[data-target="time:${x}"] textarea`); if (ta) ta.focus(); };
  $("#tcadd").addEventListener("click", add);
  $$("[data-seek]").forEach((b) => b.addEventListener("click", () => { v.currentTime = +b.dataset.seek; v.play(); }));
  $$("[data-del]").forEach((b) => b.addEventListener("click", () => { delete FB.items[b.dataset.del]; save(); render(); }));
  document.onkeydown = (e) => { if (VIEW !== "film" || /TEXTAREA|INPUT/.test(document.activeElement.tagName)) return; if (e.key === "c" || e.key === "C") { e.preventDefault(); add(); } };
  place();
}

function vLedger() {
  if (!D.ledger.length && !D.agent_decided.length) return `<h1>${esc(t("v_ledger"))}</h1>` + (docOf("DECISIONS.md") ? fallback(t("no_ledger"), "DECISIONS.md") : `<div class="empty">${esc(t("no_dec"))}</div>`);
  const cur = D.agent_decided.filter((a) => !a.superseded), old = D.agent_decided.filter((a) => a.superseded);
  const card = (a, live) => { const i = D.agent_decided.indexOf(a); return `<div class="card led" data-mark="led:${i}"><div><div class="topic">${esc(a.topic || "—")}</div><div class="tiny muted">${esc(a.date)}</div></div>
    <div><div>${esc(a.what)}</div>${a.group ? `<div class="tiny muted">${esc(a.group)}</div>` : ""}${a.why ? `<div class="small muted" style="margin-top:4px"><span class="chip">${esc(t("why"))}</span>${esc(a.why)}</div>` : ""}${a.undo ? `<div class="small muted" style="margin-top:4px"><span class="chip chg">${esc(t("undo"))}</span>${esc(a.undo)}</div>` : ""}${a.note ? `<div class="tiny muted" style="margin-top:4px">${esc(a.note)}</div>` : ""}
    ${live ? fbCtl("led:" + i, t("l_led", { x: (a.topic ? a.topic + COLON() : "") + cut(a.what, 20) }), { labels: [t("agree"), t("overturn"), t("fb_ask")], def: t("def_agree") }) : ""}</div></div>`; };
  return `<h1>${esc(t("v_ledger"))}</h1><p class="sub">${esc(t("ledger_sub"))}</p>
    ${D.ledger.length ? `<div style="overflow-x:auto"><table class="t"><thead><tr><th>${esc(t("th_what"))}</th><th>${esc(t("th_who"))}</th><th>${esc(t("th_status"))}</th></tr></thead><tbody>${D.ledger.map((l) => `<tr><td><b>${esc(l.what)}</b></td><td class="small">${esc(l.who)}</td><td class="small">${esc(l.status)}</td></tr>`).join("")}</tbody></table></div>` : ""}
    ${cur.length ? `<h2>${esc(t("agent_n", { n: cur.length }))}</h2><div class="grid">${cur.map((a) => card(a, true)).join("")}</div>` : ""}
    ${old.length ? `<details style="margin-top:20px"><summary>${esc(t("superseded", { n: old.length }))}</summary><div class="grid" style="margin-top:10px;opacity:.6">${old.map((a) => card(a, false)).join("")}</div></details>` : ""}`;
}

function vHistory() {
  const H = D.history.slice().reverse(), F = D.feedback.slice().reverse();
  if (!H.length && !F.length) return `<h1>${esc(t("v_history"))}</h1>` + (docOf("REVIEW.md") ? `<div class="card">${docHtml(docOf("REVIEW.md"))}</div>` : `<div class="empty">${esc(t("no_history"))}</div>`);
  return `<h1>${esc(t("v_history"))}</h1><p class="sub">${esc(t("history_sub"))}</p>` + H.map((h) => `<details class="card" style="margin-bottom:14px" ${h === H[0] ? "open" : ""}><summary><b>${esc(h.title)}</b></summary><div class="md">${h.html}</div></details>`).join("")
    + (F.length ? `<h2>${esc(t("desk_subs"))}</h2><ul class="small">${F.map((f) => `<li><a href="${esc(src(f.file.replace(/\.json$/, ".md")))}" target="_blank" rel="noopener">${esc(f.round)} · ${esc(f.submitted_at.replace("T", " "))}</a> · ${f.items.length} ✎</li>`).join("")}</ul>` : "");
}

function vDocs() {
  if (!D.docs.length) return `<h1>${esc(t("v_docs"))}</h1><div class="empty">${esc(t("no_docs"))}</div>`;
  const doc = docOf(DOC) || D.docs[0];
  const nav = `<div class="docnav">${D.docs.map((d) => `<a href="#docs/${esc(d.file)}" class="${d === doc ? "on" : ""}">${esc(d.file)}</a>`).join("")}</div>`;
  const warn = D.warnings.length ? `<div class="note"><b>${esc(t("warnings"))}</b><ul style="margin:4px 0 0;padding-left:18px">${D.warnings.map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>` : "";
  const intro = doc.intro ? `<div class="card docsec"><div class="md">${doc.intro}</div></div>` : "";
  const secs = doc.sections.map((s) => { const k = "doc:" + doc.file + "#" + cut(s.title, 100); return `<div class="card docsec" data-mark="${esc(k)}"><div class="md"><h2 style="margin-top:0">${esc(s.title)}</h2>${s.html}</div>${fbCtl(k, t("l_doc", { f: doc.file, s: s.title }))}</div>`; }).join("");
  return `<h1>${esc(t("v_docs"))}</h1><p class="sub">${esc(t("docs_sub"))}</p>${warn}${nav}${intro}${secs}`;
}

// ---------- tray and submit ----------
function payload() {
  const g = ROUND.data, decisions = {}, defaulted = [];
  (g.decisions || []).forEach((d) => {
    const v = FB.decisions[d.id] || d.recommend;
    if (v && (d.options || []).some((o) => o.id === v)) { decisions[d.id] = v; if (!FB.decisions[d.id]) defaulted.push(d.id); }
  });
  const items = Object.entries(FB.items).filter(([, v]) => v.status).map(([k, v]) => Object.assign({ target: k, status: v.status, label: v.label || k, text: v.text || "" },
    v.suggest && v.suggest !== v.orig ? { suggest: v.suggest } : {}, v.orig && k.startsWith("cap:") ? { orig: v.orig } : {}, v.t != null ? { t: v.t } : {}));
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
function renderTray() {
  const items = Object.entries(FB.items).filter(([, v]) => v.status), st = { ok: [t("st_ok"), "ok"], change: [t("st_change"), "chg"], ask: [t("st_ask"), "acc"] };
  $("#trayList").innerHTML = items.length ? items.map(([k, v]) => `<div class="it" data-go="${esc(k)}"><span class="chip ${st[v.status][1]}">${esc(st[v.status][0])}</span><b class="small">${esc(v.label || k)}</b>${v.text ? `<div class="small muted">${esc(v.text)}</div>` : ""}${v.suggest && v.suggest !== v.orig ? `<div class="small serif">→ ${esc(v.suggest)}</div>` : ""}</div>`).join("") : `<div class="empty">${esc(t("tray_empty"))}</div>`;
  $("#preview").textContent = summaryText(payload());
  $$("#trayList [data-go]").forEach((el) => el.addEventListener("click", () => {
    const k = el.dataset.go, kind = k.split(":")[0]; $("#tray").classList.remove("open");
    location.hash = kind === "doc" ? "docs/" + k.slice(4).split("#")[0] : KIND[kind] || "round";
    setTimeout(() => { const x = $(`[data-mark="${CSS.escape(k)}"]`); if (x) x.scrollIntoView({ behavior: "smooth", block: "center" }); }, 80);
  }));
}
function openTray() { renderTray(); $("#tray").classList.add("open"); }
async function submit() {
  FB.general = $("#general").value; store.set(KEY, FB);
  const p = payload(), text = summaryText(p);
  let r = null;
  try { r = await fetch("/api/feedback", { method: "POST", headers: { "Content-Type": "application/json", "X-Desk-Token": TOKEN }, body: JSON.stringify(p) }); } catch (e) { r = null; }
  if (r && r.ok) {
    const j = await r.json();
    FB.submittedAt = new Date().toLocaleString(); store.set(KEY, FB);
    toast(j.listening ? t("sent_live") : t("sent", { f: j.saved }));
    $("#submitHint").textContent = t(j.listening ? "hint_live" : "hint_idle", { f: j.saved }); pollLive(); return;
  }
  if (r) { let e = r.status; try { e = (await r.json()).error || e; } catch (x) { /* not JSON */ } toast(t("refused", { e })); openTray(); return; }
  try { await navigator.clipboard.writeText(text); toast(t("offline")); } catch (e) { toast(t("offline2")); }
  openTray(); $("#tray details").open = true;
}
$("#openTray").addEventListener("click", openTray);
$("#closeTray").addEventListener("click", () => $("#tray").classList.remove("open"));
$("#submit").addEventListener("click", submit);
$("#submitTop").addEventListener("click", openTray);
$("#general").addEventListener("input", () => { FB.general = $("#general").value; store.set(KEY, FB); renderCount(); $("#preview").textContent = summaryText(payload()); });
$("#theme").addEventListener("click", () => {
  const d = document.documentElement, dark = d.dataset.theme ? d.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches, n = dark ? "light" : "dark";
  d.dataset.theme = n; try { localStorage.setItem("desk:theme", n); } catch (e) { /* no storage */ } if (D) render();
});
$("#lang").addEventListener("click", () => { const n = LANG === "zh" ? "en" : "zh"; try { localStorage.setItem("desk:lang", n); } catch (e) { /* no storage */ } setLang(n); renderChrome(); route(); });
$("#reload").addEventListener("click", load);
async function pollLive() {
  let on = false;
  try { const r = await fetch("/api/status", { cache: "no-store" }); on = r.ok && (await r.json()).listening; } catch (e) { on = false; }
  $("#live").classList.toggle("on", on);
  $("#liveTxt").textContent = on ? t("live_on") : t("live_off");
  $("#live").title = on ? t("live_on_tip") : t("live_off_tip");
}
setInterval(pollLive, 4000);
load();
