"use strict";
/* The console's modules besides the cut (docs/proposals/02-studio-client.md, 3), laid out as the prototype draws them
   (docs/proposals/figs/02-studio-prototype.html): 立意, 大纲, 分镜, 声音, 交付, 素材, 账本. A section a module: its words,
   its page and its wiring, registered in MODVIEW; studio.js draws a module's first tab from it. Loaded before studio.js
   (and before a static page's static.js): nothing here runs until the host calls it, and then it uses core.js's helpers
   (esc, t, kickOf …) and the host's state and hooks (D, FB, ROUND, src, setScope, pick …).
   Everything a person can select says what it is: data-mark names a feedback target (tools/desk/README.md, 反馈文件),
   data-scope a place with no target of its own, whose note goes into the round's overall words with its name in front;
   data-label is the name a note carries. Every part reads a file bin/vh has already made; a part that is not there says
   so and names the command that makes it. */

const MSTR = { zh: {}, en: {} };   // the modules' words; t() (core.js) looks here after the shell's own
const moduleWords = (zh, en) => { Object.assign(MSTR.zh, zh); Object.assign(MSTR.en, en); };
const MODVIEW = {};   // module → { main(): html, wire(), sync(decision, option), drawn(gate view): what the module draws itself }
const readOnly = () => typeof STATIC_PAGE !== "undefined";   // a static page (bin/vh review): nothing to note, nothing to send

/* ---------- shared pieces ---------- */
moduleWords({ page_rest: "审阅页上还有这些", file_gone: "找不到文件", part_err: "这一块读不出来",
  more_n: "还有 {n} 条",
  pic_gone: "找不到图（挪走或改了名）",
  means: "也就是：{x}",
  made_by: "agent 生成（{x}）",
}, { page_rest: "Also on the review page", file_gone: "file not found", part_err: "This part couldn't be read",
  more_n: "{n} more",
  pic_gone: "Picture not found (moved or renamed)",
  means: "That is: {x}",
  made_by: "made by the agent ({x})",
});
const partErr = (k) => { const e = ((D.mods || {}).errors || {})[k]; return e ? `<p class="void warn">${esc(t("part_err", { x: e }))}</p>` : ""; };   // a part whose file did not read: which, and why
const dattr = (o) => {   // data-* attributes, escaped; a mark feedback.py would refuse becomes a place with no target, named
  const a = Object.assign({}, o);
  if (a.mark) { a.mark = fitTarget(a.mark); if (!a.mark && !a.scope) a.scope = a.label; }
  if (a.label) a.label = fitLabel(a.label);
  if (a.scope) a.scope = fitLabel(a.scope);
  return Object.entries(a).filter(([, v]) => v != null && v !== "").map(([k, v]) => ` data-${k}="${esc(v)}"`).join("");
};
const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");   // a gate page's own marks
const panel = (title, sub, body, cls) => `<section class="pn${cls ? " " + cls : ""}">${title ? `<h2 class="pn-h"><span>${esc(title)}</span>${sub ? `<span class="pn-sub">${esc(sub)}</span>` : ""}</h2>` : ""}${body}</section>`;
const voidLine = (s) => `<p class="void">${esc(s)}</p>`;
const budgetLen = (s) => {   // tools/review.py's budget_len: a CJK character 1, any other visible one ½; text without CJK its characters
  const x = String(s || "").replace(/[`*]/g, "").replace(/\s+/g, " ").trim(), cjk = (x.match(/[　-鿿豈-﫿＀-￯]/g) || []).length;
  return cjk ? { n: cjk + 0.5 * x.replace(/[\s　-鿿豈-﫿＀-￯]/g, "").length, lim: 40 } : { n: x.length, lim: 100 };
};
function headLine(s) {   // a heading gets one line (playbook/01's budget: 40, or 100 in English): the first sentence of a longer one, the rest under it
  s = String(s || "");
  if (budgetLen(s).n <= budgetLen(s).lim) return { head: s, rest: "", long: false };
  const m = s.match(/^(.+?[。！？!?]|.+?[.;；:：](?=\s|$)|.+?：)(\s*\S[\s\S]*)$/), head = m ? m[1].trim().replace(/[：:；;]$/, "") : s, rest = m ? m[2].trim() : "";   // a heading never ends on a colon: what it introduces is under it
  return { head, rest, long: budgetLen(head).n > budgetLen(head).lim };
}
function fitHeads(root) {   // after drawing: a heading the display face wraps to a second line (wide Latin words) drops to the text face
  root.querySelectorAll(".mh2 h1, .mh2 h2").forEach((h) => { const lh = parseFloat(getComputedStyle(h).lineHeight) || 0; if (lh && h.offsetHeight > lh * 1.5) h.classList.add("long"); });
}
function headM(mod, title, sub, extra) {   // on a static page the stop's own heading is above: a title that repeats it goes
  const sum = String((ROUND.data || {}).summary || ""), H = readOnly() ? "h2" : "h1", same = readOnly() && !!title && (title === sum || sum.startsWith(title)), h = headLine(title);   // the page's own heading says it already
  return `<header class="mh2"><div class="mh2-t"><span class="kick">${esc(kickOf(mod))}</span>${same ? "" : `<${H}${h.long ? ' class="long"' : ""}>${esc(h.head)}</${H}>${h.rest ? `<p class="lead fold" tabindex="0">${esc(h.rest)}</p>` : ""}`}${sub ? `<p>${esc(sub)}</p>` : ""}</div>${extra || ""}</header>`;
}
const tRO = (k, v) => t(readOnly() ? k + "_s" : k, v);   // a read-only page (the static one) has no note box: its own words
function barM(text, mod, label) {   // the bar under a module: where its stop stands, and the next module
  return `<footer class="mbar"><span>${esc(text)}</span>${mod && !readOnly() ? `<a class="btn" href="${projHash(PKEY, mod)}">${esc(label)} →</a>` : ""}</footer>`;
}
const tabs = (mod) => (readOnly() ? "" : subtabs(mod));   // a module's sub-tabs are the console's routes
function redraw() {   // the same module again (a tab, a filter, a page): where the page was scrolled to stays
  const el = document.getElementById("stage"), sc = el && getComputedStyle(el).overflowY !== "visible" ? el : document.scrollingElement;
  const y = sc ? sc.scrollTop : 0; renderModule(); if (sc) sc.scrollTop = y;
}
const stationState = (id) => (stations().find((x) => x.id === id) || {}).state || "";
function prefill(card, words) {   // a note shortcut: select the thing, put the start of the sentence in the note box
  setScope(card.dataset.mark ? { target: card.dataset.mark, label: card.dataset.label, el: card } : { label: card.dataset.scope, el: card });
  const say = $("#say"); if (!say) return;
  say.value = words; say.focus(); say.setSelectionRange(say.value.length, say.value.length);
}

/* ---------- 立意: what only this subject has, and the concept cards ---------- */
moduleWords({
  idea_title: "选一张立意卡", idea_sub: "选一张卡，这支片子怎么讲就定了。",
  mat_h: "这个题目的素材", k_number: "数字", k_object: "物件", k_quote: "原话", k_conflict: "矛盾", k_surprise: "意外", k_other: "其他",
  same_topic: "别人常这么拍（我们要避开）", same_none: "还没写别人常怎么拍。",
  mat_none: "还没列这个题目的素材。",
  rec: "推荐", picked: "你选的", pick_this: "选这张", picked_btn: "已选", like_this: "照这个方向再出一张", like_say: "照 {x} 的方向再出一张：",
  pro: "好处", con: "代价", l_card: "立意卡 {x}",
  cards_none: "立意卡还没出来。下面是写下的立意：",
  bar_idea_wait: "等你选一张。选好在右边交给 agent。", bar_idea_wait_s: "等你选一张。选好把下面那行回复发给 agent。", bar_idea_done: "立意已定。现在改，大纲和分镜都得重来。", bar_idea_todo: "立意还没定。agent 想好几个方向，会停在这里给你挑。",
  idea_none: "立意卡还没出来，立意也还没写。", to_outline: "看大纲",
  idea_done: "你选了 {x}",
  idea_done_d: "{d} 定的。只能看；要改就写一条意见。", idea_done_d_s: "{d} 定的。要改，在对话里说。", idea_done_d0_s: "已定。要改，在对话里说。", skip_sub_s: "这一站没停下来给你看（你说了不用停）。要改，在对话里说。",
  idea_done0: "立意已定",
  cards_none_done: "这支片子没出立意卡，立意是这样定的：",
  no_screen: "不上屏",
  idea_done_d0: "只能看；要改就写一条意见。",
}, {
  idea_title: "Pick a concept card", idea_sub: "Pick a card, and that decides how this film tells it.",
  mat_h: "This subject's material", k_number: "Numbers", k_object: "Objects", k_quote: "Quotes", k_conflict: "Contradictions", k_surprise: "Surprises", k_other: "Other",
  same_topic: "How others usually film it (what we avoid)", same_none: "Not written yet: how others usually film it.",
  mat_none: "This subject's material isn't listed yet.",
  rec: "recommended", picked: "your pick", pick_this: "Pick this", picked_btn: "Picked", like_this: "Another in this direction", like_say: "Another card in the direction of {x}: ",
  pro: "Pro", con: "Cost", l_card: "Concept card {x}",
  cards_none: "No concept cards yet. Here is the concept as written:",
  bar_idea_wait: "Waiting for your pick. Then send it to the agent on the right.", bar_idea_wait_s: "Waiting for your pick. Then send the reply below to the agent.", bar_idea_done: "The concept is decided. Changing it now redoes the outline and the storyboard.", bar_idea_todo: "The concept isn't decided yet. The agent stops here with a few directions for you to pick from.",
  idea_none: "No concept cards yet, and no concept written.", to_outline: "See the outline",
  idea_done: "You picked {x}",
  idea_done_d: "Decided {d}. To look at only; to change it, write a note.", idea_done_d_s: "Decided {d}. To change it, say so in the chat.", idea_done_d0_s: "Decided. To change it, say so in the chat.", skip_sub_s: "This stop was skipped (you said not to stop). To change it, say so in the chat.",
  idea_done0: "The concept is decided",
  cards_none_done: "This film had no concept cards; the concept was decided as:",
  no_screen: "off screen",
  idea_done_d0: "To look at only; to change it, write a note.",
});
const KINDS = [["number", /数字|数据|number/i], ["object", /物件|实物|object|thing/i], ["quote", /原话|引文|引语|quote|words/i], ["conflict", /矛盾|冲突|contradict|conflict/i], ["surprise", /意外|反常|surpris/i]];
const kindOf = (k) => (KINDS.find(([, re]) => re.test(k || "")) || ["other"])[0];
function conceptRound() {   // the newest gate ① page and its concept decision: the one drawn with pictures, else one named for it
  const r = D.rounds.filter((x) => gateBase(x.id) === "1").pop();
  if (!r) return null;
  const decs = (r.data.decisions || []).filter((d) => d && Array.isArray(d.options) && d.options.length);
  const dec = decs.find((d) => d.options.some((o) => o && (o.frame || o.frame_missing))) || decs.find((d) => /concept|立意|idea/i.test(`${d.id} ${d.question || ""}`));
  return dec ? { round: r, dec, open: r.id === D.current && roundOpen() } : null;
}
function chosenOf(cr) {   // the card picked: this round's choice while it is open, else what REVIEW.md or DECISIONS.md says was decided
  if (cr.open) return FB.decisions[cr.dec.id] || "";
  const said = D.history.filter((h) => gateKey(h.title) === "1").flatMap((h) => h.notes.filter((n) => /^(定了|Decided)/.test(n.k)).map((n) => n.v))
    .concat(D.ledger.filter((l) => /concept|立意/i.test(l.what)).map((l) => l.status)).join(" ");
  const hit = cr.dec.options.find((o) => o && o.id && new RegExp(`(^|[^A-Za-z0-9])${String(o.id).replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}([^A-Za-z0-9]|$)`).test(said));
  return hit ? hit.id : "";
}
function briefConcept() {   // the BRIEF's concept, when there are no cards to pick from
  const c = D.concept;
  if (!c.line && !c.spine) return voidLine(t("no_brief"));
  return `<article class="pn idea-line"${dattr({ mark: "concept:line", label: t("concept") })}><p class="big">${esc(c.line || "—")}</p>
    <dl class="kv2">${c.spine ? `<div><dt>${esc(t("spine"))}</dt><dd>${esc(c.spine)}</dd></div>` : ""}${c.end ? `<div><dt>${esc(t("end"))}</dt><dd>${esc(c.end)}</dd></div>` : ""}</dl></article>`;
}
function matList(groups) {   // the material by kind, each kind's first few shown and the rest under a fold; "不上屏" a tag, not a line
  const off = (x) => /^\s*(不上屏|off[ -]?screen)/i.test(x || "");
  const item = (f, k) => `<div class="mat"${dattr(f.id ? { mark: "fact:" + f.id, label: t("l_fact", { x: f.id }) } : { scope: `${t("k_" + k)} · ${cut(f.claim, 24)}` })}><b>${esc(f.claim)}</b>${off(f.onscreen) ? `<span class="tagm">${esc(t("no_screen"))}</span>` : f.onscreen ? `<span>${esc(f.onscreen)}</span>` : ""}</div>`;
  return ["number", "object", "quote", "conflict", "surprise", "other"].filter((k) => groups[k]).map((k) => {
    const F = groups[k], head = F.slice(0, 4).map((f) => item(f, k)).join(""), more = F.slice(4);
    return `<h3 class="mat-h">${esc(t("k_" + k))}<span class="n">${F.length}</span></h3>${head}${more.length ? `<details class="more"><summary>${esc(t("more_n", { n: more.length }))}</summary>${more.map((f) => item(f, k)).join("")}</details>` : ""}`;
  }).join("");
}
function mIdea2() {
  const cr = conceptRound(), groups = {};
  D.facts.filter((f) => !f.dropped && f.claim).forEach((f) => { (groups[kindOf(f.kind)] = groups[kindOf(f.kind)] || []).push(f); });
  const same = D.ideas && D.ideas.same_topic;
  const left = panel(t("mat_h"), "", (matList(groups) || voidLine(t("mat_none")))
    + `<h3 class="mat-h">${esc(t("same_topic"))}</h3>` + (same ? `<p class="same"${dattr({ scope: t("same_topic") })}>${esc(same)}</p>` : voidLine(t("same_none"))), "mat-col");
  const settled = stationState("1") === "done" || stationState("1") === "skipped" || filmDelivered();
  const day = shortDate(stopDate(stations().filter((x) => x.id === "1")));
  let right, title, sub = t("idea_sub");
  if (cr) {   // the cards: to pick while the stop is open; once it is decided, what was picked, the rest faint, nothing to press
    const dec = cr.dec, cols = Array.isArray(dec.columns) ? dec.columns : [], chosen = chosenOf(cr), pick = dec.options.find((o) => o && o.id === chosen);
    if (!cr.open) { title = pick ? t("idea_done", { x: `${pick.id}：${cut(String(pick.label || "").replace(/\*\*|`/g, "").split(/[：:（(，,。；;]/)[0].trim(), 16)}` }) : t("idea_done0"); sub = day ? tRO("idea_done_d", { d: day }) : tRO("idea_done_d0"); }
    else title = t("idea_title");
    right = `<div class="cards2${cr.open ? "" : " settled"}">${dec.options.filter((o) => o && o.id).map((o) => {
      const on = chosen === o.id, rec = o.id === dec.recommend, dim = !cr.open && chosen && !on;
      const pic = o.frame ? `<div class="well"><img src="${esc(src(o.frame))}" alt="${esc(o.id)}" loading="lazy"></div>` : o.frame_missing ? `<p class="miss-line" title="${esc(o.frame_missing)}">${esc(t("pic_gone"))}</p>` : "";   // no picture: a card of words, no empty frame
      return `<article class="ccard${on ? " on" : ""}${dim ? " dim" : ""}${o.frame ? "" : " nopic"}"${dattr({ mark: "card:" + o.id, label: t("l_card", { x: o.id }) + (o.label ? " · " + o.label : ""), opt: o.id })}>
        ${pic}<div class="cc-b"><h3><span class="cid">${esc(o.id)}</span><span class="cl fold" tabindex="0">${rich(o.label || o.id)}</span>${rec && cr.open ? `<span class="chip quiet">${esc(t("rec"))}</span>` : ""}<span class="chip you-pick"${on ? "" : " hidden"}>${esc(t("picked"))}</span></h3>
        <dl>${o.pro ? `<dt>${esc(cols[0] || t("pro"))}</dt><dd>${rich(o.pro)}</dd>` : ""}${o.con ? `<dt>${esc(cols[1] || t("con"))}</dt><dd>${rich(o.con)}</dd>` : ""}</dl>
        <div class="cc-act">${cr.open ? `<button type="button" class="btn${on ? "" : " btn-primary"}" data-pick-card="${esc(o.id)}" aria-pressed="${on}">${esc(t(on ? "picked_btn" : "pick_this"))}</button>` : ""}${readOnly() || !cr.open ? "" : `<button type="button" class="btn btn-quiet" data-like="${esc(o.id)}">${esc(t("like_this"))}</button>`}</div></div></article>`;
    }).join("")}</div>`;
  } else {
    title = t(settled ? "idea_done0" : "m_idea");
    if (settled) sub = day ? tRO("idea_done_d", { d: day }) : tRO("idea_done_d0");
    right = D.concept.line || D.concept.spine ? voidLine(t(settled ? "cards_none_done" : "cards_none")) + briefConcept() : voidLine(t("idea_none"));
  }
  const wait = stationState("1") === "waiting_person" || (cr && cr.open && !chosenOf(cr));
  return headM("idea", title, sub) + `<div class="mgrid idea">${left}<div class="cards-col">${right}</div></div>`
    + barM(t(wait ? (readOnly() ? "bar_idea_wait_s" : "bar_idea_wait") : filmDelivered() ? "bar_redo" : settled || (cr && !cr.open) ? "bar_idea_done" : "bar_idea_todo"), "outline", t("to_outline"));
}
function syncIdea(dec, val) {   // a pick made anywhere (the cards here, the right column): the cards follow
  const cr = conceptRound(); if (!cr || cr.dec.id !== dec) return;
  $$(".ccard[data-opt]").forEach((c) => {
    const on = c.dataset.opt === val, b = $("[data-pick-card]", c), chip = $(".you-pick", c);
    c.classList.toggle("on", on); if (chip) chip.hidden = !on;
    if (b) { b.textContent = t(on ? "picked_btn" : "pick_this"); b.classList.toggle("btn-primary", !on); b.setAttribute("aria-pressed", String(on)); }
  });
}
function wireIdea() {
  const cr = conceptRound();
  $$("[data-pick-card]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); if (cr) pick(cr.dec.id, b.dataset.pickCard); }));
  $$("[data-like]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); prefill(b.closest("[data-mark]"), t("like_say", { x: b.dataset.like })); }));
}
MODVIEW.idea = { main: mIdea2, wire: wireIdea, sync: syncIdea,   // drawn: what of the gate view the module draws itself goes (the console) or hides (a static page)
  drawn(root, gone = (x) => x.remove()) { const cr = conceptRound(); if (cr) $$(".g-dec.wide", root).filter((x) => x.dataset.dec === cr.dec.id).forEach(gone); } };

/* ---------- 大纲: the parts in proportion, the BRIEF, the engine and the cost ---------- */
moduleWords({
  outline_title: "{n} 段大纲", outline_sub: "点一段，意见就只对着这一段。", outline_sub_s: "每段要让人看到什么、用什么画面。", seg_know: "要看到", seg_pic: "画面", unsure_n: "{n} 处没把握",
  brief_h: "这支片子", engine_cost: "用什么做、花多少", engine: "用什么做", voice: "配音", budget: "预算", spent: "已花", stops: "停下来给你看", free: "不花钱",
  b_concept: "立意", b_spine: "主线", b_end: "看完能记住", b_hook: "钩子", b_audience: "观众", b_watch: "在哪看", b_output: "画面", b_pace: "节奏", b_effort: "打磨程度", b_director: "谁来定",
  outline_none: "大纲还没写成表格。", outline_blank: "大纲还没写。", bar_outline: "大纲已定。现在改，分镜得重做。", bar_redo: "片子已经交付了；现在改，就是整支重做。", to_board: "去分镜",
  bar_outline_open: "大纲和立意一起定。",
  eff_quick: "快出",
  eff_standard: "标准",
  eff_studio: "精品",
  watch_desktop: "电脑上",
  watch_phone: "手机上",
  watch_tv: "电视上",
  pace_brisk: "明快",
  pace_calm: "从容",
  pace_default: "按默认",
  dir_own: "你定",
  dir_review: "给你过目",
  dir_delegate: "agent 定",
  about_s: "约 {s} 秒",
}, {
  outline_title: "An outline in {n} {n|part|parts}", outline_sub: "Click a part to write a note on that part alone.", outline_sub_s: "What each part should land, and with what picture.", seg_know: "Should land", seg_pic: "Picture", unsure_n: "{n} unsure",
  brief_h: "This film", engine_cost: "How it's made, and what it costs", engine: "Made with", voice: "Voice", budget: "Budget", spent: "Spent", stops: "Stops for you", free: "nothing paid",
  b_concept: "Concept", b_spine: "Spine", b_end: "Remembered after", b_hook: "Hook", b_audience: "Audience", b_watch: "Watch on", b_output: "Picture", b_pace: "Pace", b_effort: "Polish", b_director: "Who decides",
  outline_none: "The outline isn't a table yet.", outline_blank: "The outline isn't written yet.", bar_outline: "The outline is decided. Changing it now redoes the storyboard.", bar_redo: "The film has gone out; changing this now means remaking the whole film.", to_board: "To the storyboard",
  bar_outline_open: "The outline is decided with the concept.",
  eff_quick: "quick",
  eff_standard: "standard",
  eff_studio: "studio",
  watch_desktop: "on a computer",
  watch_phone: "on a phone",
  watch_tv: "on a TV",
  pace_brisk: "brisk",
  pace_calm: "calm",
  pace_default: "default",
  dir_own: "you",
  dir_review: "shown to you",
  dir_delegate: "the agent",
  about_s: "about {s} s",
});
const BRIEF_ROWS = [["b_concept", /^concept/i], ["b_spine", /^spine/i], ["b_end", /^what the viewer/i], ["b_hook", /^hook/i], ["b_audience", /^audience/i],
  ["b_watch", /^watch on/i], ["b_output", /^output/i], ["b_pace", /^pace/i], ["b_effort", /^effort/i], ["b_director", /^director/i]];
const DIR_WHAT = { fact: "事实", facts: "事实", sound: "声音", sfx: "音效", captions: "字幕", subtitles: "字幕", font: "字体", palette: "配色", camera: "镜头运动", edit: "剪辑", budget: "预算", license: "许可", assets: "素材", research: "资料", concept: "立意", spec: "规格", outline: "大纲", style: "风格", character: "主角", theme: "主旋律", voice: "配音", script: "旁白稿", hook: "钩子", storyboard: "分镜", rhythm: "节奏", packaging: "标题和封面", engine: "用什么做", process: "流程", delivery: "交付", music: "配乐", cover: "封面", title: "标题", font: "字体", lighting: "布光", model: "模型", camera: "镜头运动", color: "颜色", ending: "结尾", opening: "开场" };
function plainValue(k, v) {   // a BRIEF line as words: desktop → 电脑上, brisk → 明快, standard → 标准, concept=own … → 你定：立意; a {…} left in it unsaid
  v = String(v || "").replace(/\s*\{[^}]*\}\s*[a-zA-Z]*/g, "").replace(/[,，;；\s]+$/, "").trim();
  const low = v.toLowerCase();
  if (k === "b_effort" && ["quick", "standard", "studio"].includes(low)) return t("eff_" + low);
  if (k === "b_watch" && ["desktop", "phone", "tv"].includes(low)) return t("watch_" + low);
  if (k === "b_pace" && ["brisk", "calm", "default"].includes(low)) return t("pace_" + low);
  if (k === "b_director") {
    if (/^default$/i.test(v)) return t("pace_default");
    const by = {};
    v.split(/[,，;；]/).forEach((x) => { const m = x.trim().match(/^([a-z]+)\s*=\s*(own|review|delegate)/i); if (m) (by[m[2].toLowerCase()] = by[m[2].toLowerCase()] || []).push(LANG === "zh" ? DIR_WHAT[m[1].toLowerCase()] || m[1] : m[1]); });
    const parts = ["own", "delegate", "review"].filter((w) => by[w]).map((w) => `${t("dir_" + w)}${COLON()}${by[w].join(LANG === "zh" ? "、" : ", ")}`);
    return parts.length ? parts.join(" · ") : v;
  }
  if (k === "b_output") { const m = v.match(/(\d{3,4})\s*[x×]\s*(\d{3,4})/), fps = v.match(/(\d+(?:\.\d+)?)\s*fps/i), sec = v.match(/(\d+(?:\.\d+)?)\s*s\b/);
    return [m ? (+m[2] === 1080 || +m[1] === 1080 ? "1080p" : +m[2] === 2160 || +m[1] === 2160 ? "4K" : `${m[1]}×${m[2]}`) : "", fps ? `${fps[1]} fps` : "", sec ? t("about_s", { s: sec[1] }) : ""].filter(Boolean).join(" · ") || v; }
  return v;
}
function briefRows() {
  const all = (D.concept.fields || []).concat(D.spec);
  return BRIEF_ROWS.map(([k, re]) => { const f = all.find((x) => re.test(x.k)); const v = f && plainValue(k, f.v); return v ? { k, field: f.k, v } : null; }).filter(Boolean);
}
function unsureIn(o) {   // the shots in a part the agent is unsure of, and this round's least-sure places in its span
  const S = (D.shots.items || []).filter((s) => s.unsure && (s.seg === o.id || (o.t0 != null && s.start != null && s.start >= o.t0 && s.start < o.t1)));
  const M = gateMarks().filter((x) => x.kind === "least" && x.t != null && o.t0 != null && x.t >= o.t0 && x.t < o.t1 && !S.some((s) => sameId(s.id, x.id)));
  return S.length + M.length;
}
function mOutline2() {
  const O = D.outline, timed = O.filter((o) => o.t0 != null && o.t1 != null && o.t1 > o.t0), end = timed.length ? Math.max(...timed.map((o) => o.t1)) : 0;
  const pc = (x) => ((Math.max(0, x) / (end || 1)) * 100).toFixed(3);   // one scale from 0 to the last end: a gap, a late start or an overlap shows where it is
  const bar = timed.length ? `<div class="segbar" role="list">${timed.map((o) => `<button type="button" role="listitem" style="left:${pc(o.t0)}%;width:${(((Math.max(0, o.t1) - Math.max(0, o.t0)) / (end || 1)) * 100).toFixed(3)}%" data-seg="${esc(o.id)}" title="${esc(`${o.title} · ${fmt(o.t0)}–${fmt(o.t1)}`)}"><b>${esc(o.title)}</b><span class="mono">${esc((o.t1 - o.t0).toFixed(0))} s</span></button>`).join("")}</div>
    <div class="segticks mono">${[0, 0.25, 0.5, 0.75, 1].map((f) => `<span>${esc(fmt(end * f).replace(/\.\d$/, ""))}</span>`).join("")}</div>` : "";
  const cards = O.map((o, i) => { const u = unsureIn(o);
    return `<article class="segc" id="seg-${esc(o.id)}"${dattr({ mark: "seg:" + o.id, label: t("l_seg", { i: o.id, x: o.title }), t: o.t0 })}>
      <div class="sg-n mono"><b>${i + 1}</b>${o.t0 != null ? `<span>${esc(fmt(o.t0))}</span>` : ""}${o.t0 != null && o.t1 != null ? `<span>${esc((o.t1 - o.t0).toFixed(0))} s</span>` : o.bars ? `<span>${esc(o.bars)}</span>` : ""}</div>
      <div class="sg-b"><h3>${esc(o.title)}${u ? `<span class="chip wait">${esc(t("unsure_n", { n: u }))}</span>` : ""}</h3>${o.know ? `<p><span class="k">${esc(t("seg_know"))}</span>${esc(o.know)}</p>` : ""}${o.visual ? `<p><span class="k">${esc(t("seg_pic"))}</span>${esc(o.visual)}</p>` : ""}</div></article>`; }).join("");
  const rows = briefRows();
  const brief = panel(t("brief_h"), "", rows.length ? `<dl class="kv2">${rows.map((r) => `<div${dattr(r.k === "b_concept" ? { mark: "concept:line", label: t("concept") } : { scope: `BRIEF · ${t(r.k)}` })}><dt>${esc(t(r.k))}</dt><dd>${esc(r.v)}</dd></div>`).join("")}</dl>` : voidLine(t("no_brief")));
  const st = D.status || {}, b = ((st.assets || {}).budget) || {}, money = (o) => Object.entries(o || {}).map(([c, v]) => `${v} ${c}`).join(", ");
  const voice = (D.agent_decided.filter((a) => !a.superseded && /voice|配音/i.test(a.topic || "")).pop() || {}).what || specGet("voice");
  const budget = b.unlimited ? "∞" : money(b.limit) || (b.from ? "" : t("free"));
  const stopsWords = (v) => String(v || "").split(/[,，\s]+/).filter(Boolean).map((x) => (L.stn[x.replace(/^gate\s*/i, "")] || x)).join(LANG === "zh" ? "、" : ", ");   // "1, 2, 3" → 立意、分镜、初版
  const eng = [[t("engine"), specGet("engine")], [t("voice"), voice], [t("spent"), money(b.spent)], [t("budget"), budget], [t("stops"), stopsWords(specGet("stops"))]].filter(([, v]) => v);
  const engine = panel(t("engine_cost"), "", eng.length ? `<dl class="kv2">${eng.map(([k, v]) => `<div${dattr({ scope: `${t("engine_cost")} · ${k}` })}><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl>` : voidLine(t("no_brief")));
  return headM("outline", O.length ? t("outline_title", { n: O.length }) : t("m_outline"), t(readOnly() ? "outline_sub_s" : "outline_sub")) + tabs("outline")
    + `<div class="mgrid outline"><div class="segs">${bar}${cards || voidLine(t(D.outline_blank ? "outline_blank" : "outline_none"))}</div><aside class="side">${brief}${engine}</aside></div>`
    + barM(t(filmDelivered() ? "bar_redo" : ["done", "skipped"].includes(stationState("1")) ? "bar_outline" : "bar_outline_open"), "board", t("to_board"));
}
function wireOutline2() {
  $$(".segbar [data-seg]").forEach((b) => b.addEventListener("click", () => {
    const c = document.getElementById("seg-" + b.dataset.seg); if (!c) return;
    c.scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "center" });
    if (!readOnly()) setScope({ target: c.dataset.mark, label: c.dataset.label, el: c, t: c.dataset.t != null ? +c.dataset.t : null });
  }));
}
MODVIEW.outline = { main: mOutline2, wire: wireOutline2 };

/* ---------- 分镜: a page a part, the grey box, each shot with what it should get across ---------- */
moduleWords({
  board_title: "第 {i} 页 · {x}", board_sub2: "标黄的是 agent 没把握的镜头。其余的没写意见就算通过。",
  page_n: "第 {i} 页", this_page: "这一页", shots_k: "镜头", shots_n: "{n} 镜", unsure_k: "没把握", none: "没有", span_k: "时长", grey_k: "粗样", grey_note: "先看节奏和构图，颜色后面再上",
  no_anim: "还没有粗样视频。", anim_gone: "粗样视频找不到了，可能被挪走了。", default_pass: "没写意见就通过", you_said: "你说了", trans_k: "转场",
  board_none: "还没有镜头表。", avg_s: "平均一镜 {s} 秒", plan_k: "打算改", bar_board: "分镜 · {s}", bar_said: "分镜 · {s}。你当时说：「{q}」", to_sound: "去声音",
  pass_done: "已通过",
  page_seconds: "这一页的 {a}–{b}",
  skip_sub: "这一站没停下来给你看（你说了不用停）。只能看；要改就写一条意见。",
}, {
  board_title: "Page {i} · {x}", board_sub2: "Amber shots are the ones the agent is unsure about. The rest pass if you write no note.",
  page_n: "Page {i}", this_page: "This page", shots_k: "Shots", shots_n: "{n} {n|shot|shots}", unsure_k: "Unsure", none: "none", span_k: "Span", grey_k: "Rough cut", grey_note: "Rhythm and framing first; colour comes later",
  no_anim: "No rough cut video yet.", anim_gone: "The rough cut video can't be found; it may have been moved.", default_pass: "passes without a note", you_said: "you said", trans_k: "Transition",
  board_none: "No shot list yet.", avg_s: "{s} s a shot", plan_k: "will change", bar_board: "Storyboard · {s}", bar_said: "Storyboard · {s}. You said: “{q}”", to_sound: "To the sound",
  pass_done: "approved",
  page_seconds: "this page, {a}–{b}",
  skip_sub: "This stop was skipped (you said not to stop). To look at only; to change it, write a note.",
});
const shotName = (id) => String(id || "").replace(/^([A-Za-z]+)0+(?=\d)/, "$1");   // one way to write a shot: S4, never S04 or S004
const sameId = (a, b) => String(a || "").replace(/^([A-Za-z]+)0+(?=\d)/, "$1").toLowerCase() === String(b || "").replace(/^([A-Za-z]+)0+(?=\d)/, "$1").toLowerCase();   // S04 is S4
const sec = (...xs) => { const x = xs.find((v) => v != null && v !== "" && isFinite(+v)); return x == null ? null : +x; };
function boardRound() {   // the gate ② page the module shows: this page on a static page, else the newest
  const R = D.rounds.filter((x) => gateBase(x.id) === "2");
  return R.find((x) => x.id === D.current) || R.pop() || null;
}
function boardPages() {   // { round, pages }: the gate ② page's parts and shots when there is one, else shots.json's shots a page a part
  const S = (D.shots.items || []).filter((s) => s && s.id), gr = boardRound();
  const segs = gr && Array.isArray(gr.data.segments) ? gr.data.segments.filter((g) => g && Array.isArray(g.shots) && g.shots.some((x) => x && x.id)) : [];
  if (segs.length) {   // what the person reviews is the page the agent sent: all of it is here; shots.json only fills in a picture or a time
    const least = (Array.isArray(gr.data.least_sure) ? gr.data.least_sure : []).filter((x) => x && x.id);
    const flag = (id) => { const m = least.find((x) => sameId(x.id, id)); return m ? m.note || true : null; };
    const extra = (Array.isArray(gr.data.assets) ? gr.data.assets : []).filter((a) => a && a.path && a.for);
    return { round: gr.id, pages: segs.map((g, i) => ({ key: String(g.id || i + 1), title: String(g.title || g.id || ""), note: String(g.note || ""), n: i + 1, of: segs.length,
      t0: sec(g.t0), t1: sec(g.t1), assets: extra.filter((a) => a.for === g.id),
      shots: g.shots.filter((x) => x && x.id).map((x) => { const j = S.find((s) => sameId(s.id, x.id)) || {};
        return { id: String(x.id), label: String(x.see || ""), see: String(x.see || ""), vo: String(x.vo || ""), plan: String(x.note || ""), start: sec(x.t0, j.start), end: sec(x.t1, j.end),
          frame: x.frame || j.frame || "", frame_missing: x.frame || j.frame ? "" : x.frame_missing || "", reads: [], transition: "", unsure: flag(x.id) }; }) })) };
  }
  const pages = [];
  S.forEach((s) => {
    const o = D.outline.find((x) => x.id === s.seg) || null, key = o ? o.id : s.segment || "";
    const last = pages[pages.length - 1];
    if (last && last.key === key) last.shots.push(s); else pages.push({ key, title: o ? o.title : s.segment || "", note: "", shots: [s] });
  });
  return { round: null, pages };
}
function unsureShot(s) { return !!s.unsure || gateMarks().some((m) => m.kind === "least" && sameId(m.id, s.id)); }
function mBoard2() {
  const { pages } = boardPages();
  if (!pages.length) return headM("board", t("m_board"), t("board_sub2")) + voidLine(t("board_none")) + (docOf("STORYBOARD.md") ? `<div class="pn">${docHtml(docOf("STORYBOARD.md"))}</div>` : "");
  const i = Math.max(0, Math.min(pages.length - 1, (parseInt(SUB, 10) || 1) - 1)), pg = pages[i], S = pg.shots;
  const T0 = S.map((s) => s.start).filter((x) => x != null), T1 = S.map((s) => s.end).filter((x) => x != null);
  const t0 = pg.t0 != null ? pg.t0 : T0.length ? Math.min(...T0) : null, t1 = pg.t1 != null ? pg.t1 : T1.length ? Math.max(...T1) : null, unsure = S.filter(unsureShot), vid = D.shots.video;
  const durs = S.filter((s) => s.start != null && s.end != null).map((s) => s.end - s.start);
  const tabs = pages.length > 1 ? `<nav class="pgtabs" aria-label="${esc(t("m_board"))}">${pages.map((p, j) => readOnly() ? `<button type="button" data-page="${j + 1}" aria-current="${j === i}">${esc(t("page_n", { i: j + 1 }))}</button>`
    : `<a href="${projHash(PKEY, "board/" + (j + 1))}" aria-current="${j === i}">${esc(t("page_n", { i: j + 1 }))}</a>`).join("")}</nav>` : "";
  const first = S.find((s) => s.frame), rough = vid && !/draft|final|film/i.test(vid);   // the film itself is no rough cut: no rough-cut note for it
  const gone = D.shots.video_missing, pageT = t0 != null && t1 != null ? t("page_seconds", { a: fmt(t0), b: fmt(t1) }) : "";
  // this page's seconds only, with the console's own small transport (a browser's controls would offer the whole film)
  const player = vid ? `<div class="bplay"><div class="well"><video id="bv2" src="${esc(src(vid))}" preload="metadata" playsinline${t0 != null ? ` data-t0="${t0}"` : ""}${t1 != null ? ` data-t1="${t1}"` : ""}></video></div>
      <div class="bctl"><button type="button" class="p-btn play" id="bvPlay" aria-label="${esc(t("play"))}"><span class="i-play">${ICO.play}</span><span class="i-pause" hidden>${ICO.pause}</span></button><div class="bbar" id="bvBar"><i></i></div><span class="mono" id="bvT">${esc(pageT)}</span></div></div>`
    : first ? `<div class="bplay"><div class="well"><img src="${esc(src(first.frame))}" alt=""></div><p class="note-line">${esc(t(gone ? "anim_gone" : "no_anim"))}${gone && !readOnly() ? ` <button type="button" class="xs" data-tell="${esc(gone)}">${esc(t("tell_where"))}</button>` : ""}</p></div>`
    : `<p class="note-line wide" title="${esc(gone || "")}">${esc(t(gone ? "anim_gone" : "no_anim"))}${gone && !readOnly() ? ` <button type="button" class="xs" data-tell="${esc(gone)}">${esc(t("tell_where"))}</button>` : ""}</p>`;
  const info = panel(t("this_page"), "", `<dl class="kv2"><div><dt>${esc(t("shots_k"))}</dt><dd>${esc(t("shots_n", { n: S.length }))}</dd></div>
    <div><dt>${esc(t("unsure_k"))}</dt><dd>${unsure.length ? unsure.map((s) => `<span class="chip wait">${esc(shotName(s.id))}</span>`).join(" ") : esc(t("none"))}</dd></div>
    ${t0 != null && t1 != null ? `<div><dt>${esc(t("span_k"))}</dt><dd><span class="mono nw">${esc(fmt(t0) + "–" + fmt(t1))}</span>${durs.length ? `<br><span class="nw">${esc(t("avg_s", { s: (durs.reduce((a, b) => a + b, 0) / durs.length).toFixed(1) }))}</span>` : ""}</dd></div>` : ""}${rough ? `<div><dt>${esc(t("grey_k"))}</dt><dd class="muted">${esc(t("grey_note"))}</dd></div>` : ""}</dl>`);
  const extra = (pg.assets || []).map((a) => /\.(png|jpe?g|gif|webp|svg|avif)$/i.test(a.path) ? `<figure class="segpic"${dattr({ mark: "asset:" + a.path, label: a.caption || a.path })}><span class="well"><img src="${esc(src(a.path))}" alt="" loading="lazy"></span>${a.caption ? `<figcaption class="meta">${esc(a.caption)}</figcaption>` : ""}</figure>`
    : `<a class="meta" href="${esc(src(a.path))}" target="_blank" rel="noopener">${esc(a.caption || a.path)} ↗</a>`).join("");
  const pics = S.some((s) => s.frame), skipped = stationState("2") === "skipped", done = stationState("2") === "done" || filmDelivered();
  const cards = S.map((s) => {   // with pictures: a card a shot; with none anywhere on the page: a row a shot, no empty frames
    const said = FB.items["shot:" + s.id] && FB.items["shot:" + s.id].status, u = unsureShot(s);
    const chip = u ? `<span class="chip wait">${esc(t("unsure_k"))}</span>` : said ? `<span class="chip">${esc(t("you_said"))}</span>` : skipped ? "" : `<span class="chip ok">${esc(t(done ? "pass_done" : "default_pass"))}</span>`;
    const why = typeof s.unsure === "string" ? s.unsure : (gateMarks().find((m) => m.kind === "least" && sameId(m.id, s.id)) || {}).note || "";
    const gate = s.see != null;   // a shot of the gate page: what it shows, its line, what will change by default
    const reads = (s.reads || []).length > 1 ? `<ol>${s.reads.map((r) => `<li>${esc(r)}</li>`).join("")}</ol>` : (s.reads || []).length ? `<p class="see">${esc(s.reads[0])}</p>` : s.caption ? `<p class="capline">${esc(s.caption)}</p>` : "";
    const well = pics ? `<div class="well"${s.start != null && vid ? dattr({ play: s.start, stop: s.end }) : ""}>${s.frame ? `<img src="${esc(src(s.frame))}" alt="${esc(shotName(s.id))}" loading="lazy">` : s.frame_missing ? `<span class="miss" title="${esc(s.frame_missing)}">${esc(t("pic_gone"))}</span>` : ""}</div>` : "";
    return `<article class="shotc${u ? " unsure" : ""}${pics ? "" : " row"}" id="shot-${esc(s.id)}"${dattr({ mark: "shot:" + s.id, label: t("l_shot", { x: shotName(s.id) }) + (s.label ? " · " + cut(s.label, 24) : ""), t: s.start, t1: s.end })}>
      ${well}<div class="sc-b"><h3><b>${esc(shotName(s.id))}</b>${gate ? "" : `<span class="lab">${esc(String(s.label || "").replace(/^\d+[.、]\s*/, ""))}</span>`}${chip}</h3>${s.start != null && s.end != null ? `<p class="mono tc">${esc(fmt(s.start) + "–" + fmt(s.end))}</p>` : ""}
      ${gate ? `${s.see ? `<p class="see">${esc(s.see)}</p>` : ""}${s.vo ? `<p class="capline">${esc(s.vo)}</p>` : ""}` : reads}
      ${s.transition ? `<p class="meta">${esc(t("trans_k"))}${esc(COLON())}${esc(s.transition)}</p>` : ""}${u && why ? `<p class="unsure-note">${esc(why)}</p>` : ""}
      ${s.plan ? `<p class="plan">→ ${esc(t("plan_k"))}${esc(COLON())}${esc(s.plan)}</p>` : ""}</div></article>`;
  }).join("");
  const st = stationState("2"), q = D.history.filter((h) => gateKey(h.title) === "2").flatMap((h) => h.quotes || []).map((x) => x.text).pop();
  const of = "";   // the page tabs say which page
  const settled = ["done", "skipped"].includes(stationState("2")) || filmDelivered(), day = shortDate(stopDate(stations().filter((x) => x.id === "2")));
  return headM("board", t("board_title", { i: i + 1, x: pg.title || t("m_board") }), stationState("2") === "skipped" ? tRO("skip_sub") : settled ? (day ? tRO("idea_done_d", { d: day }) : tRO("idea_done_d0")) : t("board_sub2"), tabs)   // decided: said as such, nothing asked
    + (pg.note || of ? `<p class="segnote">${of}${pg.note ? `<span>${esc(pg.note)}</span>` : ""}</p>` : "")
    + `<div class="mgrid board${vid || first ? "" : " nopic"}">${player}${info}</div><div class="shots3${pics ? "" : " rows"}">${cards}</div>${extra ? `<div class="segpics">${extra}</div>` : ""}`
    + barM((() => { const s = flowWord(flowState(FLOW.find((f) => f.mod === "board"))) || t("st_" + (st || "not_started"));   // the stop in the top bar's words
      return q ? t("bar_said", { s, q: cut(q, 40) }) : t("bar_board", { s }); })(), "sound", t("to_sound"));
}
const ICO = { play: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>', pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5h4v14H7zM13 5h4v14h-4z" fill="currentColor"/></svg>' };
function tellWhere(path) {   // a file that moved: the person says where it went, as a note the agent reads (this console moves nothing)
  if (readOnly()) return;
  setScope({ label: `${t("file_gone")} · ${path}` });
  const say = $("#say"); if (!say) return;
  say.value = t("tell_where_say"); say.focus(); say.setSelectionRange(say.value.length, say.value.length);
}
function wireBoard2() {
  $$(".pgtabs button[data-page]").forEach((b) => b.addEventListener("click", () => { SUB = b.dataset.page; redraw(); }));   // a static page has no routes
  $$("[data-tell]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); tellWhere(b.dataset.tell); }));
  const v = $("#bv2"); if (!v) return;
  const t0 = v.dataset.t0 != null ? +v.dataset.t0 : 0, t1 = v.dataset.t1 != null ? +v.dataset.t1 : null, btn = $("#bvPlay"), bar = $("#bvBar"), tt = $("#bvT");
  let stopAt = null;
  const T1 = () => (t1 != null ? t1 : v.duration || 0);
  const paint = () => {   // this page's seconds: where in them, and play or pause
    const f = T1() > t0 ? (v.currentTime - t0) / (T1() - t0) : 0;
    if (bar) $("i", bar).style.width = (Math.max(0, Math.min(1, f)) * 100).toFixed(2) + "%";
    if (tt) tt.textContent = `${fmt(v.currentTime)} · ${fmt(t0)}–${fmt(T1())}`;
    if (btn) { $(".i-play", btn).hidden = !v.paused; $(".i-pause", btn).hidden = v.paused; }   // both icons drawn once; no markup put in later
  };
  const toggle = () => { if (v.paused) { if (v.currentTime < t0 - 0.01 || v.currentTime >= T1() - 0.05) v.currentTime = t0 + 0.01; v.play().catch(() => {}); } else v.pause(); };
  v.addEventListener("loadedmetadata", () => { if (v.currentTime < t0) v.currentTime = t0; paint(); }, { once: true });
  v.addEventListener("timeupdate", () => {   // playing stops where the page ends, or where the shot clicked ends
    const end = stopAt != null ? stopAt : T1();
    if (end && !v.paused && v.currentTime >= end - 0.03) { v.pause(); stopAt = null; }
    $$(".shotc").forEach((c) => c.classList.toggle("active", c.dataset.t != null && v.currentTime >= +c.dataset.t && v.currentTime < +c.dataset.t1));
    paint();
  });
  v.addEventListener("play", paint); v.addEventListener("pause", paint);
  if (btn) btn.addEventListener("click", (e) => { e.stopPropagation(); stopAt = null; toggle(); });
  v.addEventListener("click", (e) => { e.stopPropagation(); stopAt = null; toggle(); });
  if (bar) bar.addEventListener("click", (e) => { e.stopPropagation(); const r = bar.getBoundingClientRect(); v.currentTime = t0 + Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * (T1() - t0); paint(); });
  $$(".shotc .well[data-play]").forEach((w) => w.addEventListener("click", (e) => { e.stopPropagation(); v.currentTime = +w.dataset.play + 0.01; stopAt = w.dataset.stop != null ? +w.dataset.stop : null; v.play().catch(() => {}); }));
}
MODVIEW.board = { main: mBoard2, wire: wireBoard2,   // the gate view's storyboard goes only when the module drew that same page (all of it)
  drawn(root, gone = (x) => x.remove()) { const b = boardPages(); if (b.round && b.round === root.dataset.gate) $$(".g-board", root).forEach(gone); } };

/* ---------- 声音: the readouts, the voices, the lines, the music ---------- */
moduleWords({
  sound_title: "声音", sound_sub2: "agent 听不到声音，只看得到这些数。哪里不对，写一句就行。", sound_sub_s: "agent 听不到声音。请你听的地方在下面。",
  u_loud: "目标 {x}", u_peak: "上限 −1 dBTP", u_speech: "{u}，不算停顿", u_speech2: "{u}，算停顿",
  audition: "试听别的声音", audition_cmd: "同一句话，几个声音各念一遍", in_use: "在用", use_this: "换成它", use_say: "换成 {x}：",
  pitch: "音高", rate: "语速", misread: "读错", no_misread: "没读错", audition_none: "没试过别的声音。",
  lines: "每句快慢", lines_pace: "只算出声的部分", lines_raw: "从句首到句尾算，含停顿", line_k: "句", text_k: "文字", pause_k: "停顿",
  slower: "这句偏慢", faster: "这句偏快", lines_none: "还没配旁白。", unit_zh: "字/秒", unit_syll: "音节/秒", unit_words: "词/秒",
  music: "配乐", music_cmd: "段落和可以卡点的地方", env_cmd: "整片的响度", lift: "可以卡点的重拍", lift_src: "卡点", hit_src: "音效",
  listen_src: "请你听", play_at: "从 {t} 播", music_none: "还没有配乐。", env_none: "还没有整片的响度曲线。", film_sound: "成片的声音",
  t_loud: "响度（整片多响）",
  t_peak: "峰值（最响的一下）",
  t_speech: "语速",
  t_silence: "意外静音",
  v_ok: "合格",
  v_near: "合格，离上限很近",
  v_warn: "注意",
  v_fail: "超了",
  v_none: "没有",
  v_some: "{n} 处",
  lines_unused: "这支片子没有旁白。",
  music_unused: "这支片子没有配乐。",
  sound_unchecked: "还没检查过声音。",
  sound_unchecked_done: "这支片子的声音没有检查记录。",
  misread_as: "「{a}」读成了「{b}」",
  music_track: "下面是配乐的整条音轨，「从 x 播」从它的那一秒放。", music_track_vs: "下面是配乐的整条音轨（{m}），不是成片（{f}）；「从 x 播」从它的那一秒放。", take_gone: "录音不在本机", takes_gone: "这几段试听的录音都不在本机，只剩下面的数字。",
}, {
  sound_title: "Sound", sound_sub2: "The agent can't hear; it only sees these numbers. Anything off? Write a line.", sound_sub_s: "The agent can't hear. The places to listen to are below.",
  u_loud: "target {x}", u_peak: "limit −1 dBTP", u_speech: "{u}, pauses left out", u_speech2: "{u}, pauses in",
  audition: "Try other voices", audition_cmd: "One line, read by each voice", in_use: "in use", use_this: "Use this", use_say: "Use {x}: ",
  pitch: "Pitch", rate: "Rate", misread: "Misread", no_misread: "none", audition_none: "No other voices tried.",
  lines: "Line by line", lines_pace: "speech only", lines_raw: "first word to last, pauses in", line_k: "Line", text_k: "Text", pause_k: "Pause",
  slower: "slow", faster: "fast", lines_none: "No narration yet.", unit_zh: "chars/s", unit_syll: "syllables/s", unit_words: "words/s",
  music: "Music", music_cmd: "sections, and where to cut on the beat", env_cmd: "the whole film's loudness", lift: "a beat to cut on", lift_src: "beat", hit_src: "sound",
  listen_src: "please listen", play_at: "Play from {t}", music_none: "No music yet.", env_none: "No loudness curve of the film yet.", film_sound: "The film's sound",
  t_loud: "Loudness (whole film)",
  t_peak: "Peak (loudest instant)",
  t_speech: "Speech rate",
  t_silence: "Dropouts",
  v_ok: "fine",
  v_near: "fine, close to the limit",
  v_warn: "check",
  v_fail: "over",
  v_none: "none",
  v_some: "{n}",
  lines_unused: "This film has no narration.",
  music_unused: "This film has no music.",
  sound_unchecked: "The sound isn't checked yet.",
  sound_unchecked_done: "This film's sound has no check on record.",
  misread_as: "“{a}” read as “{b}”",
  music_track: "Below is the music's whole track; \"from x\" plays it from that second.", music_track_vs: "Below is the music's whole track ({m}), not the film ({f}); \"from x\" plays it from that second.", take_gone: "The take isn't on this computer", takes_gone: "None of these takes is on this computer; the numbers below are what's left.",
});
const unitsOf = (s) => (/[㐀-鿿]/.test(s) ? (s.match(/[㐀-鿿]/g) || []).length : s.trim().split(/\s+/).filter(Boolean).length);
function narrLines() {   // each line's rate: bin/vh pace's (voice only) when it has run, else first word to last
  const X = D.mods || {}, P = X.pace, by = {};
  ((P && P.lines) || []).forEach((x) => { if (x.id) by[x.id] = x; });
  const N = (TL().narration || []).filter((x) => x.start != null && x.end != null);
  const rows = N.map((x, i) => { const p = by[x.id], next = N[i + 1];
    const rate = p ? (p.after != null ? p.after : p.pace) : unitsOf(x.text || "") / Math.max(0.1, x.end - x.start);
    return { id: x.id || "L" + (i + 1), text: x.text || "", t0: +x.start, t1: +x.end, rate: rate != null ? +rate : null, pause: next ? Math.max(0, next.start - x.end) : null }; });
  const R = rows.map((r) => r.rate).filter((x) => x != null).sort((a, b) => a - b);
  const med = P && P.reference != null ? +P.reference : R.length ? R[Math.floor(R.length / 2)] : null;
  const take = P && Array.isArray(P.speech) ? +(P.speech[1] != null ? P.speech[1] : P.speech[0]) : med;
  const cjk = N.some((x) => /[㐀-鿿]/.test(x.text || ""));
  return { rows, med, take, paced: !!P, unit: t(P ? (P.unit === "syll/s" ? "unit_syll" : "unit_zh") : cjk ? "unit_zh" : "unit_words") };   // pace says chars/s (zh) or syll/s (en)
}
function envelope(w, h) {   // the film's loudness as an area: bin/vh peaks' bins, a column the louder of |min| and |max|
  const P = D.studio && D.studio.peaks && D.studio.peaks.peaks; if (!Array.isArray(P) || !P.length) return "";
  const n = P.length, k = Math.max(1, Math.floor(n / 240)), pts = [];
  for (let i = 0; i < n; i += k) { let a = 0; for (let j = i; j < Math.min(n, i + k); j++) { const b = P[j]; a = Math.max(a, Math.abs(+(Array.isArray(b) ? b[0] : b) || 0), Math.abs(+(Array.isArray(b) ? b[1] : 0) || 0)); } pts.push(a); }
  const top = Math.max(0.05, ...pts);
  return pts.map((a, i) => `${i ? "L" : "M"}${((i / (pts.length - 1 || 1)) * w).toFixed(1)} ${(h - (a / top) * (h - 10)).toFixed(1)}`).join("") + `L${w} ${h}L0 ${h}Z`;
}
function mergeHits(H) {   // planned sounds by name: a run of one sound becomes one row ("bits ×22 · 0:09.6–0:11.7"), not twenty-two
  const out = [];
  H.forEach((h) => { const last = out[out.length - 1];
    if (last && last.what === h.what && h.t - last.t1 <= 2.5) { last.n++; last.t1 = h.t; } else out.push({ what: h.what, t: h.t, t1: h.t, n: 1, cls: h.cls, src: h.src }); });
  return out;
}
function mSound2() {
  const X = D.mods || {}, ld = X.loudness, nl = narrLines(), done = filmDelivered();
  const sev = (s) => (s === "fail" ? "live" : s === "warn" ? "wait" : s ? "ok" : "");
  const verdict = (cls, near) => t(cls === "live" ? "v_fail" : cls === "wait" ? "v_warn" : near ? "v_near" : "v_ok");
  const tile = (k, v, unit, cls, word) => `<div class="tile ${cls}"${dattr({ scope: `${t("m_sound")} · ${t(k)}` })}><span class="tk">${esc(t(k))}</span><b class="mono">${esc(v)}</b><span class="tu">${esc(unit)}${word ? ` · <span class="tv">${esc(word)}</span>` : ""}</span></div>`;
  // the readouts, in words with a verdict; none until the sound was checked (one line then, not four dashes)
  const T = [];
  if (ld && ld.integrated != null) { const c = sev(ld.severity) || "ok"; T.push(tile("t_loud", `${(+ld.integrated).toFixed(1)} LUFS`, t("u_loud", { x: ld.target != null ? ld.target : "−14" }), c, verdict(c))); }
  if (ld && ld.true_peak != null) { const pk = +ld.true_peak, c = pk > -1 ? "live" : sev(ld.severity) || "ok"; T.push(tile("t_peak", `${pk.toFixed(1)} dBTP`, t("u_peak"), c, verdict(c, pk > -1.5))); }
  if (nl.take != null) T.push(tile("t_speech", (+nl.take).toFixed(1), t(nl.paced ? "u_speech" : "u_speech2", { u: nl.unit }), "", ""));
  if (X.silences != null) T.push(tile("t_silence", X.silences ? t("v_some", { n: X.silences }) : t("v_none"), "", X.silences ? "live" : "ok", ""));
  const tiles = T.length ? `<div class="tiles">${T.join("")}</div>` : `<p class="note-line wide">${esc(t(done ? "sound_unchecked_done" : "sound_unchecked"))}</p>`;
  const inUse = (v) => !!X.voice && String(X.voice).toLowerCase() === String(v).toLowerCase();
  const A = X.audition, film = (D.studio && D.studio.film) || "";
  const allGone = !!A && A.voices.length > 1 && A.voices.every((v) => !v.file);   // none of the takes here: said once, not on every card
  const voices = A && A.voices.length ? `${allGone ? `<p class="meta">${esc(t("takes_gone"))}</p>` : ""}<div class="voices">${A.voices.map((v) => `<article class="vcard${inUse(v.voice) ? " on" : ""}"${dattr(v.file ? { mark: "asset:" + v.file, label: `${t("audition")} · ${v.voice}` } : { scope: `${t("audition")} · ${v.voice}` })}>
      <h3><b>${esc(v.voice)}</b>${inUse(v.voice) ? `<span class="chip ok">${esc(t("in_use"))}</span>` : readOnly() ? "" : `<button type="button" class="btn btn-quiet" data-use="${esc(v.voice)}">${esc(t("use_this"))}</button>`}</h3>
      ${v.file ? `<audio src="${esc(src(v.file))}" controls preload="none"></audio>` : allGone ? "" : `<p class="meta">${esc(t("take_gone"))}</p>`}${v.error ? `<p class="meta">${esc(v.error)}</p>` : ""}
      <dl class="vm"><div><dt>${esc(t("pitch"))}</dt><dd class="mono">${v.pitch_hz != null ? esc(Math.round(v.pitch_hz) + " Hz") : "—"}</dd></div><div><dt>${esc(t("rate"))}</dt><dd class="mono">${v.speech_rate != null ? esc((+v.speech_rate).toFixed(1)) : "—"}</dd></div>
      <div><dt>${esc(t("misread"))}</dt><dd${Array.isArray(v.misread) && v.misread.length ? ' class="warn"' : ""}>${esc(Array.isArray(v.misread) ? (v.misread.length ? v.misread.map((m) => { const [a, b] = String(m).split(/\s*(?:→|->)\s*/); return b ? t("misread_as", { a, b }) : String(m); }).join("、") : t("no_misread")) : "—")}</dd></div></dl></article>`).join("")}</div>` : "";
  const lines = nl.rows.length ? `<div class="tscroll"><table class="t lines"><thead><tr>${film ? "<th></th>" : ""}<th>${esc(t("line_k"))}</th><th>${esc(t("text_k"))}</th><th>${esc(nl.unit)}</th><th>${esc(t("pause_k"))}</th><th></th></tr></thead><tbody>${nl.rows.map((r) => {
      const f = nl.med && r.rate ? r.rate / nl.med : 1, flag = f < 0.8 ? t("slower") : f > 1.25 ? t("faster") : "";
      const mark = r.t1 - r.t0 >= 0.01 ? `range:${r.t0.toFixed(2)}-${r.t1.toFixed(2)}` : `atime:${r.t0.toFixed(1)}`;   // a range must run forward (feedback.py)
      return `<tr${dattr({ mark, label: t("l_line", { x: r.id }), t: r.t0, t1: r.t1 })}>${film ? `<td><button type="button" class="pl" data-seek-film="${r.t0}" aria-label="${esc(t("play_at", { t: fmt(r.t0) }))}">▶</button></td>` : ""}<td class="mono">${esc(String(r.id).replace(/^L(?=\d)/i, ""))}</td><td>${esc(r.text)}</td><td class="mono">${r.rate != null ? esc(r.rate.toFixed(1)) : "—"}</td><td class="mono">${r.pause != null ? esc(r.pause.toFixed(2)) : "—"}</td><td>${flag ? `<span class="chip wait">${esc(flag)}</span>` : ""}</td></tr>`; }).join("")}</tbody></table></div>` : "";
  // two clocks, never mixed: the film's (its loudness, the places to listen to, what the check found in the sound), played from the
  // film; the music's (its sections, the beats to cut on, the planned sounds), played from the music
  const W = 600, H = 90, M = D.music || {}, env = envelope(W, H);
  const fdur = +((D.studio && D.studio.peaks && D.studio.peaks.duration) || TL().duration || 0) || 0, fx = (s) => (fdur ? Math.max(0, Math.min(W, (s / fdur) * W)) : 0).toFixed(1);
  const SC = (X.checks || []).filter((f) => f.severity !== "info" && /loud|peak|silence|click|clip|audio|sound|voice/i.test(`${f.kind} ${f.message}`));
  const fmarks = gateMarks().filter((m) => m.kind === "listen" && m.t != null).map((m) => ({ t: +m.t, what: m.note || "", src: t("listen_src"), cls: "listen", g: "▶" }))
    .concat(SC.filter((f) => f.t != null).map((f) => ({ t: +f.t, what: shotText(f.message || f.kind || ""), src: t("k_check"), cls: "check", g: "✕" }))).sort((a, b) => a.t - b.t);
  const secs = (Array.isArray(M.sections) ? M.sections : []).filter((s) => s && isFinite(+s.start) && isFinite(+s.end) && +s.end > +s.start);
  const mdur = +(M.duration || 0) || (secs.length ? Math.max(...secs.map((s) => +s.end)) : 0), mp = (s) => (mdur ? Math.max(0, Math.min(100, (s / mdur) * 100)) : 0).toFixed(2);
  const lifts = (X.lifts || []).filter((l) => l.t != null).map((l) => ({ t: +l.t, t1: +l.t, n: 1, what: t("lift"), src: t("lift_src"), cls: "wait" }));
  const hits = mergeHits((Array.isArray(M.hits) ? M.hits : []).filter((h) => h && h.t != null).map((h) => ({ t: +h.t, what: h.part || h.what || "", src: t("hit_src"), cls: "quiet" })).sort((a, b) => a.t - b.t));
  const mmarks = lifts.concat(hits).sort((a, b) => a.t - b.t);
  const play = (k, which) => ((which === "film" ? film : M.audio) ? `<button type="button" class="xs" data-seek-${which}="${k.t}">${esc(t("play_at", { t: fmt(k.t) }))}</button>` : "");
  const frow = (k) => `<li${dattr({ mark: "atime:" + k.t.toFixed(1), label: t("sound_label", { t: fmt(k.t) }), t: k.t })}><i class="dotw ${k.cls}" aria-hidden="true">${k.g || "●"}</i><span class="mono">${esc(fmt(k.t))}</span><span>${esc(k.what)}</span><span class="meta">${esc(k.src)}</span>${play(k, "film")}</li>`;
  const mrow = (k) => `<li${dattr({ scope: `${t("music")} ${fmt(k.t)} · ${k.what}` })}><i class="dotw ${k.cls}" aria-hidden="true">●</i><span class="mono">${esc(k.n > 1 ? fmt(k.t) + "–" + fmt(k.t1) : fmt(k.t))}</span><span>${esc(k.n > 1 ? `${k.what} ×${k.n}` : k.what)}</span><span class="meta">${esc(k.src)}</span>${play(k, "music")}</li>`;
  const listFold = (rows, f) => rows.length > 8 ? `<ul class="hits2">${rows.slice(0, 8).map(f).join("")}</ul><details class="more"><summary>${esc(t("more_n", { n: rows.length - 8 }))}</summary><ul class="hits2">${rows.slice(8).map(f).join("")}</ul></details>` : rows.length ? `<ul class="hits2">${rows.map(f).join("")}</ul>` : "";
  const fpanel = done && !(env && fdur) && !fmarks.length ? ""   // a film that went out with no curve and nothing to listen to: the line above says it
    : panel(t("film_sound"), t("env_cmd"), (env && fdur ? `<svg class="energy" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true"><path d="${env}" class="env"/>${fmarks.map((k) => `<line x1="${fx(k.t)}" x2="${fx(k.t)}" y1="0" y2="${H}" class="mk ${k.cls}"/>`).join("")}</svg>` : voidLine(t("env_none")))
    + listFold(fmarks, frow) + partErr("check") + (film ? `<audio id="fau" src="${esc(src(film))}" preload="metadata"${fmarks.length ? " controls" : ""}></audio>` : ""));
  const hasMusic = secs.length && mdur;
  const mpanel = !hasMusic && !mmarks.length && done ? `<p class="note-line">${esc(t("music_unused"))}</p>`   // done, and never had music: said in a line
    : panel(t("music"), t("music_cmd"), (hasMusic ? `<div class="secband">${secs.map((s, i) => `<span class="s${i % 2}" style="left:${mp(s.start)}%;width:${(mp(s.end) - mp(s.start)).toFixed(2)}%" title="${esc([s.name, s.label].filter(Boolean).join(" · "))}">${mp(s.end) - mp(s.start) >= 7 ? esc([s.name, s.label].filter(Boolean).join(" · ")) : ""}</span>`).join("")}${mmarks.map((k) => `<i class="tick ${k.cls}" style="left:${mp(k.t)}%"></i>`).join("")}</div>` : voidLine(t("music_none")))
      + listFold(mmarks, mrow) + partErr("lifts") + (M.audio && mmarks.length ? `<p class="meta">${esc(t(mdur && fdur && Math.abs(mdur - fdur) > 1 ? "music_track_vs" : "music_track", { m: fmt(mdur), f: fmt(fdur) }))}</p><audio id="mau" src="${esc(src(M.audio))}" preload="metadata" controls></audio>` : ""));
  // no narration: a film that is done never had any (a line, the narration's parts folded away); one in the making has none yet
  const noVoice = !nl.rows.length;
  const voicePart = noVoice ? `<p class="note-line wide">${esc(t(done ? "lines_unused" : "lines_none"))}</p>`
    : (voices ? panel(t("audition"), t("audition_cmd"), voices + partErr("audition")) : done ? "" : panel(t("audition"), t("audition_cmd"), voidLine(t("audition_none")) + partErr("audition")));
  const linesPanel = noVoice ? "" : panel(t("lines"), t(nl.paced ? "lines_pace" : "lines_raw"), lines + partErr("pace"));
  return headM("sound", t("sound_title"), t(readOnly() ? "sound_sub_s" : "sound_sub2")) + tiles + voicePart
    + `<div class="mgrid sound${noVoice ? " one" : ""}">${linesPanel}<div>${fpanel}${mpanel}</div></div>`;
}
function wireSound2() {
  const fa = $("#fau"), ma = $("#mau"), seek = (a, other, s) => { if (other) other.pause(); if (a) { a.currentTime = s; a.play().catch(() => {}); } };
  $$("[data-seek-film]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); seek(fa, ma, +b.dataset.seekFilm); }));   // the film's own sound, the mix
  $$("[data-seek-music]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); seek(ma, fa, +b.dataset.seekMusic); }));
  $$("[data-use]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); prefill(b.closest(".vcard"), t("use_say", { x: b.dataset.use })); }));
}
MODVIEW.sound = { main: mSound2, wire: wireSound2 };

/* ---------- 交付: the covers, each platform's copy, what comes out, the check before delivery ---------- */
moduleWords({
  sub_deliver: "交付", ship_title: "交付", ship_sub: "点一张封面或一条文案，意见就对着它写。",
  covers: "封面", covers_sub: "竖版和横版", vertical: "竖", horizontal: "横", square: "方", covers_none: "还没有封面。",
  copy: "文案", titles: "标题候选", t_title: "标题", t_desc: "简介", t_tags: "标签", t_chapters: "章节", copy_none: "还没写标题和文案。",
  plat_none: "还没写各平台的发布文案。",
  outputs: "要交的东西", o_master: "成片", o_upload: "上传用的版本", o_srt: "字幕文件", o_covers: "封面 {n} 张", o_copy: "各平台文案 {n} 个", pending: "还没出", made: "有了",
  precheck: "出片前检查", to_fix: "有 {n} 处要修", to_mind: "{n} 处注意", passed: "通过", stale2: "检查过后片子又改了，结果可能不准。",
  precheck_none: "没做过出片前检查。", bar_ship: "初版定了以后才交付。", to_cut: "去成片",
  g_safe: "字幕位置、字号、读得过来", g_text: "字幕看得清", g_loud: "响度和峰值", g_av: "静音、闪白、黑场、卡住的画面", g_assets: "素材许可", g_pack: "标题和文案", g_other: "其他",
  checked_all: "标题里的数字和说法都核对过了。",
  checked_todo: "标题里还有 {b} 处说法没核对。",
  bar_shipped: "已交付 {d}",
  recap: "回顾",
  recap_on: "{d} 交付",
  recap_stops: "停下来给你看过 {n} 次",
  recap_words: "你说过的话",
  recap_film_gone: "成片不在本机，可能挪到了别的盘。",
  cover_used: "用的",
  o_film: "成片 · {d} 交付",
  o_film_gone: "成片 · {d} 交付，现在不在本机",
  o_film0: "成片已交付",
  o_film_gone0: "成片已交付，现在不在本机",
  covers_more: "另外 {n} 张",
}, {
  sub_deliver: "Delivery", ship_title: "Delivery", ship_sub: "Click a cover or a line of copy to write a note on it alone.",
  covers: "Covers", covers_sub: "vertical and horizontal", vertical: "vertical", horizontal: "horizontal", square: "square", covers_none: "No covers yet.",
  copy: "Copy", titles: "Title candidates", t_title: "Title", t_desc: "Description", t_tags: "Tags", t_chapters: "Chapters", copy_none: "No titles or copy yet.",
  plat_none: "No copy for each platform yet.",
  outputs: "What goes out", o_master: "The film", o_upload: "The upload copy", o_srt: "Captions", o_covers: "{n} {n|cover|covers}", o_copy: "Copy for {n} {n|platform|platforms}", pending: "not yet", made: "made",
  precheck: "Before delivery", to_fix: "{n} to fix", to_mind: "{n} to mind", passed: "passed", stale2: "The film changed after this check; the results may be out of date.",
  precheck_none: "No check before delivery yet.", bar_ship: "Delivery comes once the first draft is decided.", to_cut: "To the cut",
  g_safe: "Caption placement, size, reading time", g_text: "Captions readable", g_loud: "Loudness and peak", g_av: "Dropouts, flashes, black, frozen frames", g_assets: "Licences", g_pack: "Titles and copy", g_other: "Other",
  checked_all: "Every number and claim in the titles is checked.",
  checked_todo: "{b} {b|claim|claims} in the titles not checked yet.",
  bar_shipped: "Delivered {d}",
  recap: "Looking back",
  recap_on: "Delivered {d}",
  recap_stops: "Stopped for you {n} {n|time|times}",
  recap_words: "What you said",
  recap_film_gone: "The film isn't on this computer; it may be on another drive.",
  cover_used: "used",
  o_film: "The film · delivered {d}",
  o_film_gone: "The film · delivered {d}, not on this computer now",
  o_film0: "The film is delivered",
  o_film_gone0: "The film is delivered, not on this computer now",
  covers_more: "{n} more",
});
const CHECK_GROUPS = [["g_safe", /safe|read|scale|subtitle|caption|size/i], ["g_text", /textcheck|^text/i], ["g_loud", /loud|peak|lufs/i],   // check's kinds (tools/desk/README.md, 检查记录)
  ["g_av", /silence|flash|black|freeze|static|fade|\.iso|periodic|\.cut|blind/i], ["g_assets", /asset|licen/i], ["g_pack", /packag|cover|title/i]];
let shipPlat = 0;
const ratioName = (r) => { const R = [["9:16", 0.5625], ["3:4", 0.75], ["1:1", 1], ["4:3", 1.333], ["16:9", 1.778]]; return R.reduce((a, b) => (Math.abs(b[1] - r) < Math.abs(a[1] - r) ? b : a))[0]; };
function srcWords(x) {   // where a file came from; one a command made ("bin/vh tts") said as what made it, the command in the tooltip
  const m = String(x || "").match(/^\s*bin\/vh\s+([\w-]+)/), w = m && CMD_WORDS[m[1]];
  return w ? t("made_by", { x: w[LANG === "zh" ? 0 : 1] }) : String(x || "");
}
function secName(h) {   // a REVIEW.md section by its stop's name, else its own title without the date it carries (the date is said beside it)
  return gateName(gateKey(h.title)) || cut(String(h.title || "").replace(/[（(][^）)]*\d{4}-\d{2}-\d{2}[^）)]*[）)]/g, "").replace(/\s+/g, " ").trim(), 16);
}
function replyWords(text, h) {   // "1 A · 2 S1" → the options' own words, from the page the section names (else the stop's last page); "" when it is not codes
  const codes = String(text || "").trim().split(/\s*[·,，、;；]\s*|\s{2,}/).filter(Boolean);
  if (!codes.length || !codes.every((c) => /^\d+\s*[A-Za-z][\w-]*$/.test(c))) return "";
  const R = (D.rounds || []).find((r) => h.page && r.id === h.page) || (D.rounds || []).filter((r) => r.gate === gateKey(h.title)).pop();
  if (!R) return "";
  const decs = (R.data || {}).decisions || [];
  const said = codes.map((c) => { const [, n, id] = c.match(/^(\d+)\s*([\w-]+)$/), d = decs[+n - 1], o = d && (d.options || []).find((x) => String(x.id).toLowerCase() === id.toLowerCase());
    if (!o) return "";
    const w = cut(String(o.label || o.id).replace(/\*\*|`/g, "").split(/[：:。]/)[0].trim(), 24), e = w.match(/^(quick|standard|studio)\b/i);
    return e ? t("eff_" + e[1].toLowerCase()) : w; });
  return said.every(Boolean) ? said.join("；") : "";
}
function quoteHtml(text, h) {   // a quote as said (two lines, a click opens a longer one), and what codes in it meant
  const w = replyWords(text, h);
  return `<q class="fold" tabindex="0">${esc(text)}</q>${w ? `<span class="means">${esc(t("means", { x: w }))}</span>` : ""}`;
}
function recapHtml(covers) {   // a film that went out, looked back on: its cover, the day, how often it stopped for you, what you said
  const dl = stations().find((x) => x.id === "deliver") || {}, day = shortDate((dl.delivered || {}).date || "");
  const cover = covers.find((c) => c.ratio && c.ratio >= 1) || covers[0];
  const Q = (D.history || []).flatMap((h) => (h.quotes || []).map((q) => ({ q: q.text, h, where: secName(h), d: shortDate(h.date) }))).filter((x) => x.q).slice(-4).reverse();
  const film = D.studio && D.studio.film;
  return `<section class="pn recap"${dattr({ scope: t("recap") })}>${cover ? `<span class="well"><img src="${esc(src(cover.path))}" alt="" loading="lazy"></span>` : ""}<div class="rc-b">
    <h2 class="rc-h">${esc(day ? t("recap_on", { d: day }) : t("f_delivered"))}</h2><p class="meta">${esc(t("recap_stops", { n: (D.rounds || []).length }))}</p>${film ? "" : `<p class="note-line gone">${esc(t("recap_film_gone"))}${readOnly() ? "" : ` <button type="button" class="xs" data-tell="${esc((dl.delivered && (dl.delivered.films || [])[0]) || "out/final.mp4")}">${esc(t("tell_where"))}</button>`}</p>`}
    ${Q.length ? `<h3 class="mat-h">${esc(t("recap_words"))}</h3><ul class="quotes">${Q.map((x) => `<li>${quoteHtml(x.q, x.h)}<span class="meta">${esc([x.where, x.d].filter(Boolean).join(" · "))}</span></li>`).join("")}</ul>` : ""}</div></section>`;
}
function mShip2() {
  const X = D.mods || {}, pk = D.packaging, covers = X.covers || [], st = D.status || {}, done = filmDelivered();
  const said = (c, i) => { const x = String(c.text || "").trim(); if (!/^同上[。.]?$|^ditto$/i.test(x)) return x; for (let j = i - 1; j >= 0; j--) { const y = String(covers[j].text || "").trim(); if (y && !/^同上/.test(y)) return y; } return ""; };   // "同上" said again: in a grid there is no row above
  const fig = (c) => `<figure class="cov${c.ratio && c.ratio < 1 ? " v" : ""}"${dattr({ mark: "asset:" + c.path, label: `${t("covers")} ${c.id || c.path.split("/").pop()}` })}>
      <span class="well"><img src="${esc(src(c.path))}" alt="${esc(c.text || c.id || "")}" loading="lazy"></span>
      <figcaption class="meta">${c.id ? `<span class="chip ok">${esc(t("cover_used"))}</span> ` : ""}${esc([c.id, said(c, covers.indexOf(c))].filter(Boolean).join(" · "))}</figcaption></figure>`;
  const used = covers.filter((c) => c.id), rest = covers.filter((c) => !c.id), main = used.length ? used : rest, more = used.length ? rest : [];   // PACKAGING.md's covers are the ones used; the others folded
  const V = main.filter((c) => c.ratio && c.ratio < 0.95), Hz = main.filter((c) => !(c.ratio && c.ratio < 0.95));   // vertical, then the rest: a grid each
  const cov = covers.length ? [[V, "vertical"], [Hz, "horizontal"]].filter(([g]) => g.length).map(([g, k]) => `${V.length && Hz.length ? `<h3 class="mat-h">${esc(t(k))}<span class="n">${g.length}</span></h3>` : ""}<div class="covers grid">${g.map(fig).join("")}</div>`).join("")
    + (more.length ? `<details class="more"><summary>${esc(t("covers_more", { n: more.length }))}</summary><div class="covers grid">${more.map(fig).join("")}</div></details>` : "") : voidLine(t("covers_none"));
  let copy = voidLine(t("copy_none"));
  if (pk) {
    const P = pk.platforms || [], i = Math.min(shipPlat, Math.max(0, P.length - 1)), p = P[i], chap = (pk.copy.find((c) => /章节|chapter/i.test(c.k)) || {}).v;
    const row = (k, v, html) => `<div${dattr({ mark: `doc:PACKAGING.md#${p ? p.name + " " : ""}${t(k)}`, label: `${p ? p.name + " · " : ""}${t(k)}` })}><dt>${esc(t(k))}</dt><dd>${html || esc(v)}</dd></div>`;
    const tabs = P.length > 1 ? `<nav class="pgtabs plat">${P.map((x, j) => `<button type="button" data-plat="${j}" aria-current="${j === i}">${esc(x.name)}</button>`).join("")}</nav>` : P.length ? `<span class="chip quiet">${esc(p.name)}</span>` : "";
    const fields = p ? `<dl class="kv2">${p.title ? row("t_title", p.title) : ""}${p.desc ? row("t_desc", "", esc(p.desc).replace(/\n/g, "<br>")) : ""}${chap ? row("t_chapters", chap) : ""}${p.tags.length ? row("t_tags", "", p.tags.map((x) => `<span class="tagc">${esc(x)}</span>`).join("")) : ""}</dl>` : voidLine(t("plat_none"));
    const T = pk.titles || [], checked = (x) => /已核实|核实过|verified|^yes$|^✓$/i.test(x.checked || ""), facts = T.filter((x) => x.fact && !/^[—–-]$/.test(x.fact)), todo = facts.filter((x) => !checked(x)).length;
    const titles = T.length ? `<h3 class="mat-h">${esc(t("titles"))}</h3><ul class="copyl">${T.map((x) => `<li${dattr({ mark: `doc:PACKAGING.md#${x.id || x.title}`, label: `${t("t_title")} ${x.id || ""}`.trim() })}><b>${esc(x.title)}</b>${x.type ? `<span class="meta">${esc(x.type)}</span>` : ""}${facts.includes(x) ? `<span class="chip ${checked(x) ? "ok" : "wait"}">${esc(x.fact)}</span>` : ""}</li>`).join("")}</ul>
      ${facts.length ? `<p class="meta fine">${esc(todo ? t("checked_todo", { b: todo }) : t("checked_all"))}</p>` : ""}` : "";
    copy = `<div class="copyhead">${tabs}</div>${fields}${titles}`;
  }
  const dl = st.deliveries || [], chk = st.check, day = shortDate(((stations().find((x) => x.id === "deliver") || {}).delivered || {}).date || "");
  const outs = [["o_master", chk && chk.verdict === "pass" && !chk.stale ? chk.video : ""], ["o_upload", dl.length ? dl[dl.length - 1].output : ""],
    ["o_srt", (X.subs || [])[0] || ""], ["o_covers", covers.length ? " " : ""], ["o_copy", pk && (pk.platforms || []).length ? " " : ""]];
  // a film that went out: what is still here, and "已交付" for the rest (moved off this machine), never "还没出"
  const outputs = `<ul class="outl">${outs.filter(([, v]) => v || !done).map(([k, v]) => `<li${v.trim() ? ` title="${esc(v)}"` : ""}><span class="chip ${v ? "ok" : "quiet"}">${esc(t(v ? "made" : "pending"))}</span><span>${esc(t(k, { n: k === "o_covers" ? covers.length : ((pk && pk.platforms) || []).length }))}</span></li>`).join("")}${done ? `<li><span class="chip ok">${esc(t("f_delivered"))}</span><span>${esc(day ? t(D.studio && D.studio.film ? "o_film" : "o_film_gone", { d: day }) : t(D.studio && D.studio.film ? "o_film0" : "o_film_gone0"))}</span></li>` : ""}</ul>`;
  const C = X.checks || [];
  const T2 = (pk && pk.titles) || [], unchecked = T2.filter((x) => x.fact && !/^[—–-]$/.test(x.fact) && !/已核实|核实过|verified|^yes$|^✓$/i.test(x.checked || "")).length;
  const groups = CHECK_GROUPS.map(([k, re]) => [k, C.filter((f) => re.test(f.kind || ""))]).concat([["g_other", C.filter((f) => !CHECK_GROUPS.some(([, re]) => re.test(f.kind || "")))]]).filter(([k, fs]) => k !== "g_other" || fs.length)
    .map(([k, fs]) => [k, k === "g_pack" && unchecked ? fs.concat([{ severity: "warn", kind: "packaging.unchecked", message: t("checked_todo", { b: unchecked }) }]) : fs]);   // one count with the titles' own
  const pre = chk ? `${chk.stale ? `<p class="notice">${esc(t("stale2"))}</p>` : ""}<ul class="checkl">${groups.map(([k, fs]) => {
      const fail = fs.filter((f) => f.severity === "fail").length, warn = fs.filter((f) => f.severity === "warn").length;
      const chip = fail ? `<span class="chip live">${esc(t("to_fix", { n: fail }))}</span>` : warn ? `<span class="chip wait">${esc(t("to_mind", { n: warn }))}</span>` : `<span class="chip ok">${esc(t("passed"))}</span>`;
      const first = fs.find((f) => f.severity !== "info");
      const go = first && first.t != null && !readOnly() ? `<button type="button" class="xs" data-goto-t="${+first.t}">${esc(t("play_at", { t: fmt(+first.t) }))}</button>` : "";   // to that second of the film
      return `<li${dattr(first && first.t != null ? { mark: "time:" + (+first.t).toFixed(1), label: `${t("precheck")} · ${t(k)}`, t: first.t } : { scope: `${t("precheck")} · ${t(k)}` })}><span><b>${esc(t(k))}</b>${first ? `<span class="meta">${esc(cut(shotText(first.message), 60))}</span>` : ""}</span>${chip}${go}</li>`; }).join("")}</ul>` : voidLine(t("precheck_none"));
  return headM("ship", t("ship_title"), t("ship_sub")) + tabs("ship") + (done ? recapHtml(covers) : "")
    + `<div class="mgrid ship"><div>${panel(t("covers"), t("covers_sub"), cov + partErr("covers"))}${panel(t("copy"), "", copy)}</div><aside class="side">${panel(t("outputs"), "", outputs + partErr("subs"))}${panel(t("precheck"), "", pre + partErr("check"))}</aside></div>`
    + barM((() => {   // where the film stands, as the column says it (bin/vh status's now): what is missing, or delivered and the film
      const nw = (D.status || {}).now, NL = LANG === "zh" ? "zh" : "en", film = nw && nw.code === "delivered" && (nw.facts || {}).film;
      if (done) return (day ? t("bar_shipped", { d: day }) : t("f_delivered")) + (film ? ` · ${film}` : "");
      return nw && nw.say ? nw.say[NL] : flowWord(flowState(FLOW.find((f) => f.mod === "ship")));
    })(), "cut", t("to_cut"));
}
function wireShip2() {
  $$("#stage [data-tell]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); tellWhere(b.dataset.tell); }));
  $$(".pgtabs.plat [data-plat]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); shipPlat = +b.dataset.plat; redraw(); }));
  $$("[data-goto-t]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); const x = +b.dataset.gotoT; if (typeof gotoTarget === "function") gotoTarget("time:" + x.toFixed(1), x, null, ""); }));
}
MODVIEW.ship = { main: mShip2, wire: wireShip2 };

/* ---------- 素材: every item with its licence, its source and its shot; the references and their transcripts ---------- */
moduleWords({
  assets_title: "素材", assets_sub2: "每一件从哪来、什么许可、用在哪一镜。",
  f_image: "图片", f_video: "视频", f_audio: "声音", f_font: "字体", f_ref: "参考", k_file: "文件",
  drop_note: "要加素材，在对话里发给 agent。",
  l_cc0: "CC0", l_pd: "公有领域", l_own: "自己做的", l_generated: "AI 生成", l_unknown: "许可不明", l_free: "免费可用", l_managed: "平台授权", l_ref: "只做参考",
  used_in: "用在 {x}", from: "来自 {x}", not_used: "还没用上", gone_file: "找不到文件", read_transcript: "读文稿", open_src: "原始链接", digest: "长视频的文字稿", none_kind: "这一类还没有。",
  licenses_ok: "{n} 件许可清楚", licenses_todo: "{n} 件许可不明，出片前会提醒你", licenses_rec: "{n} 件许可不明，出片前会提醒你", outside: "不在片子的文件夹里", assets_none: "还没有登记过素材。",
  l_system: "系统自带",
  refs_n: "{n} 件参考",
  licenses_idle: "{n} 件许可不明，没用进片子",
}, {
  assets_title: "Assets", assets_sub2: "Where each came from, its licence, and the shot it is in.",
  f_image: "Images", f_video: "Video", f_audio: "Sound", f_font: "Fonts", f_ref: "References", k_file: "File",
  drop_note: "To add one, send it to the agent in the chat.",
  l_cc0: "CC0", l_pd: "public domain", l_own: "made here", l_generated: "AI-generated", l_unknown: "licence unclear", l_free: "free to use", l_managed: "licensed", l_ref: "reference only",
  used_in: "in {x}", from: "from {x}", not_used: "not used yet", gone_file: "file not found", read_transcript: "Read the transcript", open_src: "The source", digest: "Transcripts of long videos", none_kind: "None of these yet.",
  licenses_ok: "{n} {n|licence|licences} clear", licenses_todo: "{n} unclear: you'll be reminded before delivery", licenses_rec: "{n} unclear: you'll be reminded before delivery", outside: "outside the film's folder", assets_none: "No assets on record yet.",
  l_system: "system font",
  refs_n: "{n} {n|reference|references}",
  licenses_idle: "{n} unclear, not in the film",
});
moduleWords({
  notes_ledger: "早期的素材记录", notes_ledger_sub: "",
  nl_file: "文件", nl_src: "来源", nl_lic: "许可", nl_gone: "不在", nl_gone_tip: "片子的文件夹里没有这个文件",
}, {
  notes_ledger: "Earlier asset notes", notes_ledger_sub: "",
  nl_file: "File", nl_src: "Source", nl_lic: "Licence", nl_gone: "not here", nl_gone_tip: "No such file in the film's folder",
});
let assetFilter = "all";
const LIC_WORD = { pd: "l_pd", cc0: "l_cc0", own: "l_own", generated: "l_generated", free: "l_free", managed: "l_managed", unknown: "l_unknown" };
const CLEARED = ["pd", "cc0", "cc-by", "free", "managed", "own", "generated"];   // what bin/vh assets takes under Assets: strict (tools/assets/licenses.py)
const licLamp = (c) => (c === "generated" ? "agent" : CLEARED.includes(c) ? "ok" : "wait");
const licText = (a) => (LIC_WORD[a.license] ? t(LIC_WORD[a.license]) : String(a.license || "").replace(/^cc-/, "CC ").toUpperCase());
const assetKind = (k) => (["image", "video", "audio", "font"].includes(k) ? k : "file");
function mAssets2() {
  const X = D.mods || {}, A = X.assets, R = X.refs || [], G = X.digests || [];
  const items = (A || []).map((a) => ({ k: assetKind(a.kind), a })).concat(R.map((r) => ({ k: "ref", r })));
  const shown = items.filter((x) => assetFilter === "all" || x.k === assetFilter);
  const card = (x) => {
    if (x.r) { const r = x.r, g = G.find((d) => d.id === r.id), safe = /^https?:\/\//.test(r.url || "");
      return `<article class="acard"${dattr({ mark: `doc:research/refs.json#${r.id}`, label: `${t("f_ref")} ${r.id}` })}><div class="well"><span class="ph">${esc(r.kind === "video" ? "▶" : r.kind === "audio" ? "♪" : "↗")}</span></div>
        <div class="ac-b"><h3>${esc(r.title || r.id)}</h3><p><span class="chip quiet">${esc(t("l_ref"))}</span><span class="meta">${esc(["image", "video", "audio", "font"].includes(r.kind) ? t("f_" + r.kind) : r.kind || "")}</span></p>
        <p class="meta">${esc(t("from", { x: r.author || r.url || "—" }))}</p>${r.note ? `<p class="meta">${esc(r.note)}</p>` : ""}
        <p class="links">${g ? `<a href="${esc(src(g.path))}" target="_blank" rel="noopener">${esc(t("read_transcript"))} ↗</a>` : ""}${safe ? `<a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(t("open_src"))} ↗</a>` : ""}</p></div></article>`; }
    const a = x.a, uses = (Array.isArray(a.used_by) ? a.used_by : []).join("、");
    const pic = x.k === "image" && a.there ? `<img src="${esc(src(a.path))}" alt="" loading="lazy">` : x.k === "font" ? `<span class="glyph">字 Aa</span>` : "";
    return `<article class="acard${CLEARED.includes(a.license) ? "" : " flag"}"${dattr({ mark: a.path ? "asset:" + a.path : "", scope: a.path ? "" : `${t("m_assets")} · ${a.id}`, label: `${t("m_assets")} ${a.id}` })}>
      <div class="well"><span class="ph">${esc(x.k === "audio" ? "♪" : x.k === "video" ? "▶" : x.k === "font" ? "" : String(a.id || "·").slice(0, 1))}</span>${pic}</div>
      <div class="ac-b"><h3>${esc(a.id)}</h3><p><span class="chip ${licLamp(a.license)}"${a.license_name ? ` title="${esc(a.license_name)}"` : ""}>${esc(licText(a))}</span><span class="meta">${esc(t(x.k === "file" ? "k_file" : "f_" + x.k))}</span>${a.system ? `<span class="chip quiet">${esc(t("l_system"))}</span>` : ""}${a.aigc && a.license !== "generated" ? `<span class="meta">${esc(t("l_generated"))}</span>` : ""}</p>
      <p class="meta">${esc(uses ? t("used_in", { x: uses }) : t("not_used"))}</p>${a.source ? `<p class="meta" title="${esc(a.source)}">${esc(t("from", { x: srcWords(a.source) }))}</p>` : ""}${a.note ? `<p class="meta">${esc(a.note)}</p>` : ""}${a.system ? "" : a.outside ? `<p class="meta warn" title="${esc(a.outside)}">${esc(t("outside"))}</p>` : a.path && !a.there ? `<p class="meta warn" title="${esc(a.path)}">${esc(t("gone_file"))}${readOnly() ? "" : ` <button type="button" class="xs" data-tell="${esc(a.path)}">${esc(t("tell_where"))}</button>`}</p>` : ""}</div></article>`;
  };
  const counts = { all: items.length }; items.forEach((x) => { counts[x.k] = (counts[x.k] || 0) + 1; });
  const filters = items.length ? `<nav class="pgtabs" aria-label="${esc(t("m_assets"))}">${["all", "image", "video", "audio", "font", "ref"].map((k) => `<button type="button" data-af="${k}" aria-current="${assetFilter === k}">${esc(t("f_" + k))}${counts[k] ? ` <span class="mono">${counts[k]}</span>` : ""}</button>`).join("")}</nav>` : "";   // nothing to filter: no filters
  const N = A == null && X.assets_notes && (X.assets_notes.rows || []).length ? X.assets_notes : null;   // no ledger: the older table in NOTES.md, read only
  const notesTable = N ? panel(t("notes_ledger"), t("notes_ledger_sub"), `<div class="tscroll"><table class="t nl"><thead><tr><th>${esc(t("nl_file"))}</th><th>${esc(t("nl_src"))}</th><th>${esc(t("nl_lic"))}</th></tr></thead><tbody>${N.rows.map((r) =>   // a file not in the project: a tag beside its name (a link has none)
      `<tr${dattr({ mark: r.file ? "asset:" + r.file : "", scope: r.file ? "" : `${t("notes_ledger")} · ${cut(r.source || r.license, 30)}`, label: `${t("notes_ledger")} · ${cut(r.file, 60)}` })}><td><span class="fold" tabindex="0">${esc(r.file || "—")}</span>${r.there === false ? ` <span class="chip wait" title="${esc(t("nl_gone_tip"))}">${esc(t("nl_gone"))}</span>` : ""}</td><td><span class="fold" tabindex="0">${esc(r.source || "—")}</span></td><td><span class="fold" tabindex="0">${esc(r.license || "—")}</span></td></tr>`).join("")}</tbody></table></div>`, "nl-pn") : "";   // read only: the line at the top says how to add
  const ok = (A || []).filter((a) => CLEARED.includes(a.license)).length, unclear = (A || []).filter((a) => !CLEARED.includes(a.license)), refs = R.length;
  const todo = unclear.filter((a) => (Array.isArray(a.used_by) ? a.used_by : []).length).length, idle = unclear.length - todo;   // as the check counts: an unclear licence matters once the file is in the film
  const digests = G.length ? panel(t("digest"), "", `<ul class="copyl">${G.map((g) => `<li${dattr({ mark: "asset:" + g.path, label: `${t("digest")} ${g.id}` })}><span class="mono">${esc(g.id)}</span><a href="${esc(src(g.path))}" target="_blank" rel="noopener">${esc(t("read_transcript"))} ↗</a><span class="meta mono">${esc(Math.max(1, Math.round(g.bytes / 1024)) + " kB")}</span></li>`).join("")}</ul>`) : "";
  return headM("assets", t("assets_title"), t("assets_sub2"), filters)
    + (readOnly() ? "" : `<p class="note-line add-line">${esc(t("drop_note"))}</p>`)
    + partErr("assets") + partErr("refs") + (A == null && !R.length ? (N ? "" : voidLine(t("assets_none"))) : `<div class="acards">${shown.map(card).join("") || voidLine(t("none_kind"))}</div>`) + notesTable + digests + partErr("digests")
    + (A ? `<footer class="mbar"><span><i class="dotw ok" aria-hidden="true">●</i> ${esc(t("licenses_ok", { n: ok }))}${todo ? `　<i class="dotw wait" aria-hidden="true">●</i> ${esc(t(((D.status || {}).assets || {}).policy === "record" ? "licenses_rec" : "licenses_todo", { n: todo }))}` : ""}${idle ? `　<i class="dotw quiet" aria-hidden="true">●</i> ${esc(t("licenses_idle", { n: idle }))}` : ""}${refs ? `　<i class="dotw quiet" aria-hidden="true">●</i> ${esc(t("refs_n", { n: refs }))}` : ""}</span></footer>` : "");
}
function wireAssets2() {
  $$("[data-af]").forEach((b) => b.addEventListener("click", () => { assetFilter = b.dataset.af; redraw(); }));
  $$("#stage [data-tell]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); tellWhere(b.dataset.tell); }));
}
MODVIEW.assets = { main: mAssets2, wire: wireAssets2 };

/* ---------- 账本: the decisions, your words, the versions ---------- */
moduleWords({
  ledger_title: "决定记录", ledger_sub2: "agent 替你定的事都在这儿。不同意，点那一条的「改」。",
  decisions: "决定", what: "什么事", decided: "定成什么", who: "谁定的", when: "日期", reason: "理由", you_decide: "你定", show_you: "给你过目", agent_decides: "agent 定", waits: "等你",
  overturn_say: "我不同意：", your_words: "你的原话", your_words_sub: "一字不改记下的", versions: "版本", ver_cmd: "每一版改了什么", v_n: "第 {n} 版",
  changed_n: "改了 {n} 段", changed_s: "改了 {x}", whole_film2: "整片", words_none: "还没有记下你的原话。", versions_none: "还没出过版本。",
  dec_none: "还没有决定记录。",
  who_grid: "谁来定",
  log_h: "定下的事",
}, {
  ledger_title: "Decisions", ledger_sub2: "What the agent decided for you is here. To disagree, click “Change” on that row.",
  decisions: "Decisions", what: "What", decided: "Decided", who: "By", when: "When", reason: "Why", you_decide: "you", show_you: "shown to you", agent_decides: "the agent", waits: "waiting for you",
  overturn_say: "I disagree: ", your_words: "Your words", your_words_sub: "word for word", versions: "Versions", ver_cmd: "what each changed", v_n: "v{n}",
  changed_n: "{n} {n|stretch|stretches} changed", changed_s: "changed {x}", whole_film2: "the whole film", words_none: "No words of yours recorded yet.", versions_none: "No versions yet.",
  dec_none: "No decisions recorded yet.",
  who_grid: "Who decides",
  log_h: "What was decided",
});
const dateOf = (h) => h.date || "";
const LED_STOP = { concept: "1", outline: "1", storyboard: "2", rhythm: "2", hook: "1", style: "1" };
function whatName(w) {   // "concept 立意" → 立意, "spec" → 规格: the decision by its Chinese name, the key only when there is none
  const x = String(w || "").trim(), m = x.match(/^([a-z][a-z_-]*)\s+(.+)$/i);
  if (m && /[㐀-鿿]/.test(m[2])) return LANG === "zh" ? m[2] : m[1];
  return LANG === "zh" && DIR_WHAT[x.toLowerCase()] ? DIR_WHAT[x.toLowerCase()] : x;
}
function ledStatus(s, name) {   // a cell's status in words: no "（可翻）", no stop codes, nothing when it only repeats the cell's name
  const x = stopWords(String(s || "")).replace(/[（(]\s*可翻\s*[）)]/g, "").replace(/^[\s：:·]+|[\s：:·]+$/g, "").trim();
  return x === name ? "" : x;
}
function mLedger2() {
  const who = (w, s) => (/等|wait/i.test(s || "") ? ["waits", "wait"] : /^own|你|person/i.test(w || "") ? ["you_decide", ""] : /^review|看/i.test(w || "") ? ["show_you", "quiet"] : ["agent_decides", "agent"]);
  const keyOf = (w) => String(w || "").trim().split(/\s+/)[0].toLowerCase();
  const stale = (l) => { const st = LED_STOP[keyOf(l.what)]; return (filmDelivered() || (st && ["done", "skipped"].includes(stationState(st)))) && /进行中|待|等|in progress|pending|waiting/i.test(l.status || ""); };
  const over = (i) => (readOnly() ? "" : `<button type="button" class="xs ovt" data-overturn="${esc(i)}">${esc(t("overturn"))}</button>`);   // shown where the pointer is (CSS)
  // who decides what: a cell a decision; a status written before the film went out is said as decided, the words kept in the tooltip
  const unused = (l) => filmDelivered() && /未开始|没开始|not started/i.test(String(l.status || ""));   // a film that went out: a decision it never came to is not shown
  const grid = D.ledger.length ? `<div class="whogrid">${D.ledger.map((l, i) => unused(l) ? "" : (() => { const [k, c] = who(l.who, l.status), old = stale(l);
      return `<div class="wg"${dattr({ mark: `doc:DECISIONS.md#${l.what}`, label: `${t("decisions")} · ${whatName(l.what)}` })}><b>${esc(whatName(l.what))}</b><span class="chip ${c}">${esc(t(k))}</span><span class="meta"${old ? ` title="${esc(l.status)}"` : ""}>${esc(old ? t("f_done") : ledStatus(l.status, whatName(l.what)))}</span>${k === "agent_decides" ? over("t" + i) : ""}</div>`; })()).join("")}</div>` : voidLine(t("dec_none"));
  // what was decided, newest first: the agent's decisions with their day and their reason
  const A = D.agent_decided.filter((a) => !a.superseded).map((a) => ({ a, i: D.agent_decided.indexOf(a) })).sort((x, y) => String(y.a.date || "").localeCompare(String(x.a.date || "")));
  const logRow = ({ a, i }) => `<li${dattr({ mark: "led:" + i, label: t("l_led", { x: (a.topic ? whatName(a.topic) + COLON() : "") + cut(a.what, 20) }) })}><span class="mono tc">${esc(shortDate(a.date) || "")}</span><div><b>${esc(a.topic ? whatName(a.topic) : "")}</b><span class="fold" tabindex="0">${esc(a.what)}</span>${a.why ? `<span class="meta fold" tabindex="0">${esc(t("reason"))}${esc(COLON())}${esc(a.why)}</span>` : ""}</div>${over(i)}</li>`;
  const log = A.length ? `<ul class="declog">${A.slice(0, 5).map(logRow).join("")}</ul>${A.length > 5 ? `<details class="more"><summary>${esc(t("more_n", { n: A.length - 5 }))}</summary><ul class="declog">${A.slice(5).map(logRow).join("")}</ul></details>` : ""}` : "";   // the newest five, the rest folded
  const Q = D.history.flatMap((h) => (h.quotes || []).map((q) => ({ h, q })));
  const words = Q.length ? `<ul class="quotes">${Q.map(({ h, q }) => `<li${dattr({ scope: `${t("your_words")} · ${cut(h.title, 24)}` })}>${quoteHtml(q.text, h)}<span class="meta">${esc([secName(h), /^\d{4}-\d\d-\d\d/.test(String(q.label || "")) ? "" : q.label, shortDate(dateOf(h))].filter(Boolean).join(" · "))}</span></li>`).join("")}</ul>` : voidLine(t("words_none"));
  const V = ((D.status || {}).versions || {}).list || [];
  const vers = V.length ? `<ul class="copyl vers">${V.slice().reverse().map((v) => { const n = v.n != null ? v.n : (String(v.id).match(/\d+/) || [""])[0], ch = v.changed || {};
      const what = ch.whole || !Object.keys(ch).length ? t("whole_film2") : (ch.shots || []).length ? t("changed_s", { x: ch.shots.slice(0, 4).join("、") }) : t("changed_n", { n: (ch.seconds || ch.frames || []).length });
      return `<li${dattr({ scope: `${t("versions")} · ${t("v_n", { n })}` })}><span class="chip ${v.state === "current" ? "" : "quiet"}">${esc(t("v_n", { n }))}</span><b>${esc(v.note || v.made_by || "")}</b><span class="meta">${esc(what)}</span></li>`; }).join("")}</ul>` : voidLine(t("versions_none"));
  return headM("ledger", t("ledger_title"), t("ledger_sub2")) + tabs("ledger") + panel(t("who_grid"), "", grid) + (log ? panel(t("log_h"), "", log) : "")
    + `<div class="mgrid ledger${V.length || !filmDelivered() ? "" : " one"}">${panel(t("your_words"), t("your_words_sub"), words)}${V.length || !filmDelivered() ? panel(t("versions"), t("ver_cmd"), vers) : ""}</div>`;   // a film that went out with no version record: no "还没出过版本"
}
function wireLedger2() { $$("[data-overturn]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); prefill(b.closest("[data-mark],[data-scope]"), t("overturn_say")); })); }
MODVIEW.ledger = { main: mLedger2, wire: wireLedger2 };
