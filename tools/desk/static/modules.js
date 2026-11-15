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
moduleWords({ page_rest: "{g} 的页里还有这些", file_gone: "文件不在了" }, { page_rest: "Also on {g}'s page", file_gone: "the file is gone" });
const dattr = (o) => Object.entries(o).filter(([, v]) => v != null && v !== "").map(([k, v]) => ` data-${k}="${esc(v)}"`).join("");
const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");   // a gate page's own marks
const panel = (title, sub, body, cls) => `<section class="pn${cls ? " " + cls : ""}">${title ? `<h2 class="pn-h"><span>${esc(title)}</span>${sub ? `<span class="pn-sub">${esc(sub)}</span>` : ""}</h2>` : ""}${body}</section>`;
const voidLine = (s) => `<p class="void">${esc(s)}</p>`;
function headM(mod, title, sub, extra) {   // on a static page the stop's own heading is above: a title that repeats it goes
  const H = readOnly() ? "h2" : "h1", same = readOnly() && title === String((ROUND.data || {}).summary || "");
  return `<header class="mh2"><div class="mh2-t"><span class="kick">${esc(kickOf(mod))}</span>${same ? "" : `<${H}>${esc(title)}</${H}>`}${sub ? `<p>${esc(sub)}</p>` : ""}</div>${extra || ""}</header>`;
}
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
  idea_title: "{n} 张立意卡，选一张", idea_sub: "选一张卡，立意、风格方向和钩子就一起定了。左边是只属于这个题目的东西。",
  mat_h: "只属于这个题目的", k_number: "数字", k_object: "物件", k_quote: "原话", k_conflict: "矛盾", k_surprise: "意外", k_other: "其他",
  same_topic: "同题的视频常见的样子", same_none: "NOTES.md 的「点子」里还没写同题的视频都长什么样（playbook/12-ideation.md 第 3 节）。",
  mat_none: "NOTES.md 还没有素材清单：先列只属于这份材料的数字、物件、原话（playbook/12-ideation.md 第 2 节）。",
  rec: "推荐", picked: "你选的", pick_this: "选这张", picked_btn: "已选", like_this: "再想一张像它的", like_say: "再想一张像 {x} 的：",
  pro: "好处", con: "代价", l_card: "立意卡 {x}",
  cards_none: "还没有立意卡：关卡 ① 的页（bin/vh gate <项目> 1）写好后，卡在这里。下面是 BRIEF 写下的立意。",
  bar_idea_wait: "关卡 ① 等你选：选好以后，在右边一列提交这一轮", bar_idea_wait_s: "关卡 ① 等你选：在卡上或下面选好，把下面那行回复发给 agent", bar_idea_done: "立意定了：再改它，大纲和分镜都要跟着重做", to_outline: "看大纲",
}, {
  idea_title: "{n} concept cards: pick one", idea_sub: "Pick a card and the concept, the look and the hook are settled together. On the left: what only this subject has.",
  mat_h: "What only this subject has", k_number: "Numbers", k_object: "Objects", k_quote: "Words", k_conflict: "Contradictions", k_surprise: "Surprises", k_other: "Other",
  same_topic: "What videos on it usually look like", same_none: "NOTES.md's ideas don't say yet what other videos on this subject look like (playbook/12-ideation.md, 3).",
  mat_none: "NOTES.md has no material list yet: first list the numbers, objects and words only this material has (playbook/12-ideation.md, 2).",
  rec: "recommended", picked: "your pick", pick_this: "Pick this", picked_btn: "Picked", like_this: "Another like it", like_say: "Another card like {x}: ",
  pro: "Pro", con: "Cost", l_card: "Concept card {x}",
  cards_none: "No concept cards yet: once gate ①'s page is written (bin/vh gate <project> 1), they are here. Below is the concept the BRIEF has.",
  bar_idea_wait: "Gate ① waits for you: once you have picked, submit this round in the right column", bar_idea_wait_s: "Gate ① waits for you: pick on a card or below, then send the reply line below to the agent", bar_idea_done: "The concept is settled: change it now, and the outline and the storyboard follow", to_outline: "See the outline",
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
  const said = D.history.filter((h) => /①|gate ?1\b/i.test(h.title)).flatMap((h) => h.notes.filter((n) => /^(定了|Decided)/.test(n.k)).map((n) => n.v))
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
function mIdea2() {
  const cr = conceptRound(), groups = {};
  D.facts.filter((f) => !f.dropped && f.claim).forEach((f) => { (groups[kindOf(f.kind)] = groups[kindOf(f.kind)] || []).push(f); });
  const mat = ["number", "object", "quote", "conflict", "surprise", "other"].filter((k) => groups[k]).map((k) => `<h3 class="mat-h">${esc(t("k_" + k))}</h3>`
    + groups[k].map((f) => `<div class="mat"${dattr(f.id ? { mark: "fact:" + f.id, label: t("l_fact", { x: f.id }) } : { scope: `${t("k_" + k)} · ${cut(f.claim, 24)}` })}><b>${esc(f.claim)}</b>${f.onscreen || f.source ? `<span>${esc(f.onscreen || f.source)}</span>` : ""}</div>`).join("")).join("");
  const same = D.ideas && D.ideas.same_topic;
  const left = panel(t("mat_h"), "NOTES.md", (mat || voidLine(t("mat_none")))
    + `<h3 class="mat-h">${esc(t("same_topic"))}</h3>` + (same ? `<p class="same"${dattr({ scope: t("same_topic") })}>${esc(same)}</p>` : voidLine(t("same_none"))), "mat-col");
  let right, title;
  if (cr) {
    const dec = cr.dec, cols = Array.isArray(dec.columns) ? dec.columns : [], chosen = chosenOf(cr);
    title = (cr.round.data.summary && String(cr.round.data.summary)) || t("idea_title", { n: dec.options.length });
    right = `<div class="cards2">${dec.options.filter((o) => o && o.id).map((o) => {
      const on = chosen === o.id, rec = o.id === dec.recommend;
      return `<article class="ccard${on ? " on" : ""}"${dattr({ mark: "card:" + o.id, label: t("l_card", { x: o.id }) + (o.label ? " · " + o.label : ""), opt: o.id })}>
        <div class="well"><span class="ph">${esc(o.id)}</span>${o.frame ? `<img src="${esc(src(o.frame))}" alt="${esc(o.id)}" loading="lazy">` : o.frame_missing ? `<span class="miss" title="${esc(o.frame_missing)}">${esc(t("file_gone"))}</span>` : ""}</div>
        <div class="cc-b"><h3><span class="cid">${esc(o.id)}</span><span class="cl">${rich(o.label || o.id)}</span>${rec ? `<span class="chip quiet">${esc(t("rec"))}</span>` : ""}<span class="chip you-pick"${on ? "" : " hidden"}>${esc(t("picked"))}</span></h3>
        <dl>${o.pro ? `<dt>${esc(cols[0] || t("pro"))}</dt><dd>${rich(o.pro)}</dd>` : ""}${o.con ? `<dt>${esc(cols[1] || t("con"))}</dt><dd>${rich(o.con)}</dd>` : ""}</dl>
        <div class="cc-act">${cr.open || readOnly() ? `<button type="button" class="btn${on ? "" : " btn-primary"}" data-pick-card="${esc(o.id)}" aria-pressed="${on}">${esc(t(on ? "picked_btn" : "pick_this"))}</button>` : ""}${readOnly() ? "" : `<button type="button" class="btn btn-quiet" data-like="${esc(o.id)}">${esc(t("like_this"))}</button>`}</div></div></article>`;
    }).join("")}</div>`;
  } else {
    title = t("m_idea");
    right = voidLine(t("cards_none")) + briefConcept();
  }
  const wait = stationState("1") === "waiting_person" || (cr && cr.open && !chosenOf(cr));
  return headM("idea", title, t("idea_sub")) + `<div class="mgrid idea">${left}<div class="cards-col">${right}</div></div>`
    + barM(t(wait ? (readOnly() ? "bar_idea_wait_s" : "bar_idea_wait") : "bar_idea_done"), "outline", t("to_outline"));
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
  outline_title: "{n} 段大纲", outline_sub: "段名按内容起，看名字就知道这段讲什么。点一段，就能只对它说。", outline_sub_s: "段名按内容起，看名字就知道这段讲什么。", seg_know: "要看懂", seg_pic: "画面", unsure_n: "{n} 处没把握",
  brief_h: "BRIEF", engine_cost: "引擎和花费", engine: "引擎", voice: "配音", budget: "预算", spent: "已花", stops: "停在哪", free: "不调付费接口",
  b_concept: "立意", b_spine: "主线", b_end: "看完以后", b_hook: "钩子", b_audience: "观众", b_watch: "在哪看", b_output: "规格", b_pace: "节奏", b_effort: "档位", b_director: "谁拍板",
  outline_none: "BRIEF 的大纲还没写成表格（列名见 tools/desk/README.md 的读取约定）。", bar_outline: "大纲属于关卡 ①（{s}）：改它，分镜要跟着重做", to_board: "去分镜",
}, {
  outline_title: "An outline in {n} parts", outline_sub: "Each part is named by what it says. Click one to say something about it alone.", outline_sub_s: "Each part is named by what it says.", seg_know: "Reads", seg_pic: "Picture", unsure_n: "{n} unsure",
  brief_h: "BRIEF", engine_cost: "Engine and cost", engine: "Engine", voice: "Voice", budget: "Budget", spent: "Spent", stops: "Stops", free: "no paid calls",
  b_concept: "Concept", b_spine: "Spine", b_end: "At the end", b_hook: "Hook", b_audience: "Audience", b_watch: "Watch on", b_output: "Output", b_pace: "Pace", b_effort: "Effort", b_director: "Director",
  outline_none: "The BRIEF's outline isn't a table yet (its columns are in tools/desk/README.md, the reading contract).", bar_outline: "The outline belongs to gate ① ({s}): change it, and the storyboard follows", to_board: "To the storyboard",
});
const BRIEF_ROWS = [["b_concept", /^concept/i], ["b_spine", /^spine/i], ["b_end", /^what the viewer/i], ["b_hook", /^hook/i], ["b_audience", /^audience/i],
  ["b_watch", /^watch on/i], ["b_output", /^output/i], ["b_pace", /^pace/i], ["b_effort", /^effort/i], ["b_director", /^director/i]];
function briefRows() {
  const all = (D.concept.fields || []).concat(D.spec);
  return BRIEF_ROWS.map(([k, re]) => { const f = all.find((x) => re.test(x.k)); return f && f.v ? { k, field: f.k, v: f.v } : null; }).filter(Boolean);
}
function unsureIn(o) {   // the shots in a part the agent is unsure of, and this round's least-sure places in its span
  const S = (D.shots.items || []).filter((s) => s.unsure && (s.seg === o.id || (o.t0 != null && s.start != null && s.start >= o.t0 && s.start < o.t1)));
  const M = gateMarks().filter((x) => x.kind === "least" && x.t != null && o.t0 != null && x.t >= o.t0 && x.t < o.t1);
  return S.length + M.length;
}
function mOutline2() {
  const O = D.outline, timed = O.filter((o) => o.t0 != null && o.t1 != null && o.t1 > o.t0), end = timed.length ? Math.max(...timed.map((o) => o.t1)) : 0;
  const bar = timed.length ? `<div class="segbar" role="list">${timed.map((o) => `<button type="button" role="listitem" style="flex:${(o.t1 - o.t0).toFixed(2)}" data-seg="${esc(o.id)}"><b>${esc(o.title)}</b><span class="mono">${esc((o.t1 - o.t0).toFixed(0))} s</span></button>`).join("")}</div>
    <div class="segticks mono">${[0, 0.25, 0.5, 0.75, 1].map((f) => `<span>${esc(fmt(end * f))}</span>`).join("")}</div>` : "";
  const cards = O.map((o, i) => { const u = unsureIn(o);
    return `<article class="segc" id="seg-${esc(o.id)}"${dattr({ mark: "seg:" + o.id, label: t("l_seg", { i: o.id, x: o.title }), t: o.t0 })}>
      <div class="sg-n mono"><b>${i + 1}</b>${o.t0 != null ? `<span>${esc(fmt(o.t0))}</span>` : ""}${o.t0 != null && o.t1 != null ? `<span>${esc((o.t1 - o.t0).toFixed(0))} s</span>` : o.bars ? `<span>${esc(o.bars)}</span>` : ""}</div>
      <div class="sg-b"><h3>${esc(o.title)}${u ? `<span class="chip wait">${esc(t("unsure_n", { n: u }))}</span>` : ""}</h3>${o.know ? `<p><span class="k">${esc(t("seg_know"))}</span>${esc(o.know)}</p>` : ""}${o.visual ? `<p><span class="k">${esc(t("seg_pic"))}</span>${esc(o.visual)}</p>` : ""}</div></article>`; }).join("");
  const rows = briefRows();
  const brief = panel(t("brief_h"), "BRIEF.md", rows.length ? `<dl class="kv2">${rows.map((r) => `<div${dattr(r.k === "b_concept" ? { mark: "concept:line", label: t("concept") } : { scope: `BRIEF · ${t(r.k)}` })}><dt>${esc(t(r.k))}</dt><dd>${esc(r.v)}</dd></div>`).join("")}</dl>` : voidLine(t("no_brief")));
  const st = D.status || {}, b = ((st.assets || {}).budget) || {}, money = (o) => Object.entries(o || {}).map(([c, v]) => `${v} ${c}`).join(", ");
  const voice = (D.agent_decided.filter((a) => !a.superseded && /voice|配音/i.test(a.topic || "")).pop() || {}).what || specGet("voice");
  const budget = b.unlimited ? "∞" : money(b.limit) || (b.from ? "" : t("free"));
  const eng = [[t("engine"), specGet("engine")], [t("voice"), voice], [t("spent"), money(b.spent)], [t("budget"), budget], [t("stops"), specGet("stops")]].filter(([, v]) => v);
  const engine = panel(t("engine_cost"), "BRIEF · bin/vh assets", eng.length ? `<dl class="kv2">${eng.map(([k, v]) => `<div${dattr({ scope: `${t("engine_cost")} · ${k}` })}><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("")}</dl>` : voidLine(t("no_brief")));
  return headM("outline", O.length ? t("outline_title", { n: O.length }) : t("m_outline"), t(readOnly() ? "outline_sub_s" : "outline_sub")) + tabs("outline")
    + `<div class="mgrid outline"><div class="segs">${bar}${cards || voidLine(t("outline_none"))}</div><aside class="side">${brief}${engine}</aside></div>`
    + barM(t("bar_outline", { s: t("st_" + (stationState("1") || "not_started")) }), "board", t("to_board"));
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
  board_title: "第 {i} 页 · {x}", board_sub2: "每镜写着观众要依次看懂什么。没把握的镜头标出来了，其余默认通过；先看灰盒的节奏。",
  page_n: "第 {i} 页", this_page: "这一页", shots_k: "镜头", shots_n: "{n} 镜", unsure_k: "没把握", none: "没有", span_k: "时长", grey_k: "灰盒", grey_note: "只看节奏和构图，颜色到成片才上",
  no_anim: "还没有灰盒 animatic：有了就在这里播这一页（shots.json 的 video，或 out/animatic.mp4）。", anim_gone: "灰盒 animatic 不在了：{x}（移走或改名了）。", default_pass: "默认通过", you_said: "你说了", trans_k: "转场",
  board_none: "还没有镜头表：shots.json 写好后（bin/vh storyboard 读它），镜头按段落分页排在这里。", bar_board: "关卡 ② · {s}", bar_said: "关卡 ② · {s}：你当时说「{q}」", to_sound: "去声音",
}, {
  board_title: "Page {i} · {x}", board_sub2: "Each shot says what the viewer should get, in order. The shots the agent is unsure of are marked; the rest pass unless you say. Watch the grey box for the pace first.",
  page_n: "Page {i}", this_page: "This page", shots_k: "Shots", shots_n: "{n} shots", unsure_k: "Unsure", none: "none", span_k: "Span", grey_k: "Grey box", grey_note: "pace and framing only; colour comes with the film",
  no_anim: "No grey-box animatic yet: once there is one (shots.json's video, or out/animatic.mp4), this page plays here.", anim_gone: "The grey-box animatic is gone: {x} (moved or renamed).", default_pass: "passes", you_said: "you said", trans_k: "Transition",
  board_none: "No shot table yet: once shots.json is written (bin/vh storyboard reads it), the shots are laid out here, a page a part.", bar_board: "Gate ② · {s}", bar_said: "Gate ② · {s}: you said “{q}”", to_sound: "To the sound",
});
const sameId = (a, b) => String(a || "").replace(/^([A-Za-z]+)0+(?=\d)/, "$1").toLowerCase() === String(b || "").replace(/^([A-Za-z]+)0+(?=\d)/, "$1").toLowerCase();   // S04 is S4
function boardPages() {   // shots.json's shots, a page a part of the outline; without it, the gate ② page's own shots
  const S = (D.shots.items || []).filter((s) => s && s.id);
  if (S.length) {
    const pages = [];
    S.forEach((s) => {
      const o = D.outline.find((x) => x.id === s.seg) || null, key = o ? o.id : s.segment || "";
      const last = pages[pages.length - 1];
      if (last && last.key === key) last.shots.push(s); else pages.push({ key, title: o ? o.title : s.segment || "", shots: [s] });
    });
    return pages;
  }
  const r = D.rounds.filter((x) => gateBase(x.id) === "2").pop();
  return (r && Array.isArray(r.data.segments) ? r.data.segments : []).map((g) => ({ key: g.id, title: g.title || g.id || "",
    shots: (g.shots || []).filter((x) => x && x.id).map((x) => ({ id: x.id, label: x.see || "", start: x.t0 != null ? +x.t0 : null, end: x.t1 != null ? +x.t1 : null,
      frame: x.frame || "", reads: x.see ? [x.see] : [], caption: x.vo || "", transition: x.transition || "", unsure: x.unsure || null })) })).filter((p) => p.shots.length);
}
function unsureShot(s) { return !!s.unsure || gateMarks().some((m) => m.kind === "least" && sameId(m.id, s.id)); }
function mBoard2() {
  const pages = boardPages();
  if (!pages.length) return headM("board", t("m_board"), t("board_sub2")) + voidLine(t("board_none")) + (docOf("STORYBOARD.md") ? `<div class="pn">${docHtml(docOf("STORYBOARD.md"))}</div>` : "");
  const i = Math.max(0, Math.min(pages.length - 1, (parseInt(SUB, 10) || 1) - 1)), pg = pages[i], S = pg.shots;
  const T0 = S.map((s) => s.start).filter((x) => x != null), T1 = S.map((s) => s.end).filter((x) => x != null);
  const t0 = T0.length ? Math.min(...T0) : null, t1 = T1.length ? Math.max(...T1) : null, unsure = S.filter(unsureShot), vid = D.shots.video;
  const tabs = pages.length > 1 ? `<nav class="pgtabs" aria-label="${esc(t("m_board"))}">${pages.map((p, j) => readOnly() ? `<button type="button" data-page="${j + 1}" aria-current="${j === i}">${esc(t("page_n", { i: j + 1 }))}</button>`
    : `<a href="${projHash(PKEY, "board/" + (j + 1))}" aria-current="${j === i}">${esc(t("page_n", { i: j + 1 }))}</a>`).join("")}</nav>` : "";
  const first = S.find((s) => s.frame);
  const player = vid ? `<div class="bplay"><div class="well"><video id="bv2" src="${esc(src(vid))}" preload="metadata" playsinline controls${t0 != null ? ` data-t0="${t0}"` : ""}${t1 != null ? ` data-t1="${t1}"` : ""}></video></div></div>`
    : `<div class="bplay"><div class="well">${first ? `<span class="ph">${esc(first.id)}</span><img src="${esc(src(first.frame))}" alt="">` : ""}</div><p class="void">${esc(D.shots.video_missing ? t("anim_gone", { x: D.shots.video_missing }) : t("no_anim"))}</p></div>`;
  const info = panel(t("this_page"), "", `<dl class="kv2"><div><dt>${esc(t("shots_k"))}</dt><dd>${esc(t("shots_n", { n: S.length }))}</dd></div>
    <div><dt>${esc(t("unsure_k"))}</dt><dd>${unsure.length ? unsure.map((s) => `<span class="chip wait">${esc(s.id)}</span>`).join(" ") : esc(t("none"))}</dd></div>
    ${t0 != null && t1 != null ? `<div><dt>${esc(t("span_k"))}</dt><dd class="mono">${esc(fmt(t0) + "–" + fmt(t1))}</dd></div>` : ""}<div><dt>${esc(t("grey_k"))}</dt><dd class="muted">${esc(t("grey_note"))}</dd></div></dl>`);
  const cards = S.map((s) => {
    const said = FB.items["shot:" + s.id] && FB.items["shot:" + s.id].status, u = unsureShot(s);
    const chip = u ? `<span class="chip wait">${esc(t("unsure_k"))}</span>` : said ? `<span class="chip">${esc(t("you_said"))}</span>` : `<span class="chip ok">${esc(t("default_pass"))}</span>`;
    const why = typeof s.unsure === "string" ? s.unsure : (gateMarks().find((m) => m.kind === "least" && sameId(m.id, s.id)) || {}).note || "";
    return `<article class="shotc${u ? " unsure" : ""}"${dattr({ mark: "shot:" + s.id, label: t("l_shot", { x: s.id }) + (s.label ? " · " + cut(s.label, 24) : ""), t: s.start, t1: s.end })}>
      <div class="well"${s.start != null && vid ? dattr({ play: s.start, stop: s.end }) : ""}><span class="ph">${esc(s.id)}</span>${s.frame ? `<img src="${esc(src(s.frame))}" alt="${esc(s.id)}" loading="lazy">` : ""}</div>
      <div class="sc-b"><h3><b>${esc(s.id)}</b><span class="lab">${esc(s.label || "")}</span>${chip}</h3>${s.start != null && s.end != null ? `<p class="mono tc">${esc(fmt(s.start) + "–" + fmt(s.end))}</p>` : ""}
      ${(s.reads || []).length ? `<ol>${s.reads.map((r) => `<li>${esc(r)}</li>`).join("")}</ol>` : s.caption ? `<p class="capline">${esc(s.caption)}</p>` : ""}
      ${s.transition ? `<p class="meta">${esc(t("trans_k"))}${esc(COLON())}${esc(s.transition)}</p>` : ""}${u && why ? `<p class="unsure-note">${esc(why)}</p>` : ""}</div></article>`;
  }).join("");
  const st = stationState("2"), q = D.history.filter((h) => /②|gate ?2\b/i.test(h.title)).flatMap((h) => h.quotes || []).map((x) => x.text).pop();
  return headM("board", t("board_title", { i: i + 1, x: pg.title || t("m_board") }), t("board_sub2"), tabs)
    + `<div class="mgrid board">${player}${info}</div><div class="shots3">${cards}</div>`
    + barM(q ? t("bar_said", { s: t("st_" + (st || "not_started")), q: cut(q, 40) }) : t("bar_board", { s: t("st_" + (st || "not_started")) }), "sound", t("to_sound"));
}
function wireBoard2() {
  $$(".pgtabs button[data-page]").forEach((b) => b.addEventListener("click", () => { SUB = b.dataset.page; redraw(); }));   // a static page has no routes
  const v = $("#bv2"); if (!v) return;
  const t0 = v.dataset.t0 != null ? +v.dataset.t0 : null, t1 = v.dataset.t1 != null ? +v.dataset.t1 : null;
  let stopAt = null;
  v.addEventListener("loadedmetadata", () => { if (t0 != null && v.currentTime < t0) v.currentTime = t0; }, { once: true });
  v.addEventListener("timeupdate", () => {   // this page's stretch: playing stops where the page ends, or where the shot clicked ends
    const end = stopAt != null ? stopAt : t1;
    if (end != null && !v.paused && v.currentTime >= end - 0.03) { v.pause(); stopAt = null; }
    $$(".shotc").forEach((c) => c.classList.toggle("active", c.dataset.t != null && v.currentTime >= +c.dataset.t && v.currentTime < +c.dataset.t1));
  });
  $$(".shotc .well[data-play]").forEach((w) => w.addEventListener("click", (e) => { e.stopPropagation(); v.currentTime = +w.dataset.play + 0.01; stopAt = w.dataset.stop != null ? +w.dataset.stop : null; v.play().catch(() => {}); }));
}
MODVIEW.board = { main: mBoard2, wire: wireBoard2, drawn(root, gone = (x) => x.remove()) { if (boardPages().length) $$(".g-board", root).forEach(gone); } };

/* ---------- 声音: the readouts, the voices, the lines, the music ---------- */
moduleWords({
  sound_title: "音色、旁白、配乐和混音", sound_sub2: "agent 听不见，读的是这些数。换音色、重念要 agent：这一版写成点评，随这一轮交给它。", sound_sub_s: "agent 听不见，读的是这些数；请你听的地方在下面。",
  u_loud: "LUFS · 目标 {x}", u_peak: "dBTP · 上限 −1", u_speech: "{u} · 不算停顿", u_speech2: "{u} · 含句中停顿", u_silence: "处数字静音",
  no_check_val: "bin/vh check", no_narr_val: "bin/vh tts",
  audition: "试听音色", audition_cmd: "bin/vh voices audition · 同一段话，几个音色各念一遍", in_use: "在用", use_this: "换成它", use_say: "换成 {x}：",
  pitch: "音高中位", rate: "语速", misread: "误读", no_misread: "没有误读", audition_none: "还没试听过音色：bin/vh voices audition <文本> --voices A,B,C。",
  lines: "旁白逐句", lines_pace: "bin/vh pace：只算有声的部分", lines_raw: "按句首到句尾算，含句中停顿 · bin/vh pace --dry-run 给只算有声的", line_k: "句", text_k: "文字", pause_k: "句后停顿",
  slower: "比中位数慢 ×{x}", faster: "比中位数快 ×{x}", lines_none: "还没有旁白的时间：bin/vh tts 出了配音才有。", unit_zh: "字/秒", unit_syll: "音节/秒",
  music: "配乐", music_cmd: "段落和候选落点 · bin/vh beats", env_cmd: "响度包络 · bin/vh peaks", lift: "换气之后的重拍", lift_src: "bin/vh beats 的 lifts 候选", hit_src: "计划的音效",
  listen_src: "请你听", play_at: "从 {t} 播", music_none: "还没有配乐的段落：bin/vh beats <音乐>；波形：bin/vh peaks <项目>。", sound_checks: "bin/vh check 里和声音有关的",
}, {
  sound_title: "Voice, narration, music and mix", sound_sub2: "The agent can't hear; it reads these numbers. Recasting and rereading need the agent: write them as notes for now, and they go with this round.", sound_sub_s: "The agent can't hear; it reads these numbers. The places to listen to are below.",
  u_loud: "LUFS · target {x}", u_peak: "dBTP · limit −1", u_speech: "{u} · pauses left out", u_speech2: "{u} · pauses inside lines in", u_silence: "digital silences",
  no_check_val: "bin/vh check", no_narr_val: "bin/vh tts",
  audition: "Voice audition", audition_cmd: "bin/vh voices audition · the same text, read in each voice", in_use: "in use", use_this: "Use this", use_say: "Use {x}: ",
  pitch: "Pitch", rate: "Rate", misread: "Misreads", no_misread: "none", audition_none: "No audition yet: bin/vh voices audition <text> --voices A,B,C.",
  lines: "Narration, line by line", lines_pace: "bin/vh pace: voice only", lines_raw: "first word to last, pauses inside the line in · bin/vh pace --dry-run gives voice only", line_k: "Line", text_k: "Text", pause_k: "Pause after",
  slower: "×{x} slower than the median", faster: "×{x} faster than the median", lines_none: "No narration timing yet: bin/vh tts makes it.", unit_zh: "chars/s", unit_syll: "syllables/s",
  music: "Music", music_cmd: "sections and candidate lifts · bin/vh beats", env_cmd: "loudness · bin/vh peaks", lift: "the hit after a breath", lift_src: "a bin/vh beats lift", hit_src: "a planned sound",
  listen_src: "please listen", play_at: "Play from {t}", music_none: "No music sections yet: bin/vh beats <music>; the waveform: bin/vh peaks <project>.", sound_checks: "bin/vh check, on the sound",
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
  return { rows, med, take, paced: !!P, unit: t(P && P.unit === "syll/s" ? "unit_syll" : "unit_zh") };   // pace says chars/s (zh) or syll/s (en)
}
function envelope(w, h) {   // the film's loudness as an area: bin/vh peaks' bins, a column the louder of |min| and |max|
  const P = D.studio && D.studio.peaks && D.studio.peaks.peaks; if (!Array.isArray(P) || !P.length) return "";
  const n = P.length, k = Math.max(1, Math.floor(n / 240)), pts = [];
  for (let i = 0; i < n; i += k) { let a = 0; for (let j = i; j < Math.min(n, i + k); j++) { const b = P[j]; a = Math.max(a, Math.abs(+(Array.isArray(b) ? b[0] : b) || 0), Math.abs(+(Array.isArray(b) ? b[1] : 0) || 0)); } pts.push(a); }
  const top = Math.max(0.05, ...pts);
  return pts.map((a, i) => `${i ? "L" : "M"}${((i / (pts.length - 1 || 1)) * w).toFixed(1)} ${(h - (a / top) * (h - 10)).toFixed(1)}`).join("") + `L${w} ${h}L0 ${h}Z`;
}
function soundSource() { return (D.music && D.music.audio) || (D.studio && D.studio.film) || ""; }
function mSound2() {
  const X = D.mods || {}, ld = X.loudness, nl = narrLines();
  const sev = (s) => (s === "fail" ? "live" : s === "warn" ? "wait" : s ? "ok" : "");
  const tile = (k, v, unit, cls, empty) => `<div class="tile ${v == null ? "" : cls}"${dattr({ scope: `${t("m_sound")} · ${k}` })}><span class="tk mono">${esc(k)}</span><b class="mono">${esc(v == null ? "—" : v)}</b><span class="tu">${esc(v == null ? empty : unit)}</span></div>`;
  const peakCls = ld && ld.true_peak != null ? (+ld.true_peak > -1 ? "live" : sev(ld.severity)) : "";
  const tiles = `<div class="tiles">${tile("LOUDNESS", ld && ld.integrated != null ? (+ld.integrated).toFixed(1) : null, t("u_loud", { x: ld && ld.target != null ? ld.target : "−14" }), sev(ld && ld.severity), t("no_check_val"))}`
    + tile("TRUE PEAK", ld && ld.true_peak != null ? (+ld.true_peak).toFixed(1) : null, t("u_peak"), peakCls, t("no_check_val"))
    + tile("SPEECH", nl.take != null ? (+nl.take).toFixed(1) : null, t(nl.paced ? "u_speech" : "u_speech2", { u: nl.unit }), "", t("no_narr_val"))
    + tile("SILENCE", X.silences != null ? String(X.silences) : null, t("u_silence"), X.silences ? "live" : "ok", t("no_check_val")) + `</div>`;
  const inUse = (v) => !!X.voice && String(X.voice).toLowerCase() === String(v).toLowerCase();
  const A = X.audition;
  const voices = A && A.voices.length ? `<div class="voices">${A.voices.map((v) => `<article class="vcard${inUse(v.voice) ? " on" : ""}"${dattr(v.file ? { mark: "asset:" + v.file, label: `${t("audition")} · ${v.voice}` } : { scope: `${t("audition")} · ${v.voice}` })}>
      <h3><b>${esc(v.voice)}</b>${inUse(v.voice) ? `<span class="chip ok">${esc(t("in_use"))}</span>` : readOnly() ? "" : `<button type="button" class="btn btn-quiet" data-use="${esc(v.voice)}">${esc(t("use_this"))}</button>`}</h3>
      ${v.file ? `<audio src="${esc(src(v.file))}" controls preload="none"></audio>` : ""}${v.error ? `<p class="meta">${esc(v.error)}</p>` : ""}
      <dl class="vm"><div><dt>${esc(t("pitch"))}</dt><dd class="mono">${v.pitch_hz != null ? esc(Math.round(v.pitch_hz) + " Hz") : "—"}</dd></div><div><dt>${esc(t("rate"))}</dt><dd class="mono">${v.speech_rate != null ? esc((+v.speech_rate).toFixed(1)) : "—"}</dd></div>
      <div><dt>${esc(t("misread"))}</dt><dd${Array.isArray(v.misread) && v.misread.length ? ' class="warn"' : ""}>${esc(Array.isArray(v.misread) ? (v.misread.length ? v.misread.join("、") : t("no_misread")) : "—")}</dd></div></dl></article>`).join("")}</div>` : voidLine(t("audition_none"));
  const lines = nl.rows.length ? `<div class="tscroll"><table class="t lines"><thead><tr><th>${esc(t("line_k"))}</th><th>${esc(t("text_k"))}</th><th>${esc(nl.unit)}</th><th>${esc(t("pause_k"))}</th><th></th></tr></thead><tbody>${nl.rows.map((r) => {
      const f = nl.med && r.rate ? r.rate / nl.med : 1, flag = f < 0.8 ? t("slower", { x: (1 / f).toFixed(1) }) : f > 1.25 ? t("faster", { x: f.toFixed(1) }) : "";
      const mark = r.t1 - r.t0 >= 0.01 ? `range:${r.t0.toFixed(2)}-${r.t1.toFixed(2)}` : `atime:${r.t0.toFixed(1)}`;   // a range must run forward (feedback.py)
      return `<tr${dattr({ mark, label: t("l_line", { x: r.id }), t: r.t0, t1: r.t1 })}><td class="mono">${esc(r.id)}</td><td>${esc(r.text)}</td><td class="mono">${r.rate != null ? esc(r.rate.toFixed(1)) : "—"}</td><td class="mono">${r.pause != null ? esc(r.pause.toFixed(2)) : "—"}</td><td>${flag ? `<span class="chip wait">${esc(flag)}</span>` : ""}</td></tr>`; }).join("")}</tbody></table></div>` : voidLine(t("lines_none"));
  const W = 600, H = 110, M = D.music || {}, dur = +(M.duration || (D.studio && D.studio.peaks && D.studio.peaks.duration) || TL().duration || 0) || 1;
  const x = (s) => Math.max(0, Math.min(W, (s / dur) * W)), env = envelope(W, H), secs = Array.isArray(M.sections) ? M.sections : [];
  const marks = gateMarks().filter((m) => m.kind === "listen" && m.t != null).map((m) => ({ t: +m.t, what: m.note, src: t("listen_src"), cls: "you" }))
    .concat((X.lifts || []).filter((l) => l.t != null).map((l) => ({ t: +l.t, what: t("lift"), src: t("lift_src"), cls: "wait" })))
    .concat((Array.isArray(M.hits) ? M.hits : []).filter((h) => h && h.t != null).map((h) => ({ t: +h.t, what: h.part || h.what || "", src: t("hit_src"), cls: "quiet" })))
    .sort((a, b) => a.t - b.t);
  const chart = env || secs.length ? `<svg class="energy" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none" aria-hidden="true">${secs.map((s, i) => `<rect x="${x(s.start).toFixed(1)}" y="0" width="${Math.max(1, x(s.end) - x(s.start)).toFixed(1)}" height="${H}" class="sec s${i % 2}"/>`).join("")}
      ${env ? `<path d="${env}" class="env"/>` : ""}${marks.map((k) => `<line x1="${x(k.t).toFixed(1)}" x2="${x(k.t).toFixed(1)}" y1="0" y2="${H}" class="mk ${k.cls}"/>`).join("")}</svg>
      <div class="secnames">${secs.map((s) => `<span style="left:${((s.start / dur) * 100).toFixed(2)}%;width:${(((s.end - s.start) / dur) * 100).toFixed(2)}%">${esc([s.name, s.label].filter(Boolean).join(" · "))}</span>`).join("")}</div>` : "";
  const can = !!soundSource() || (!readOnly() && !!(D.studio && D.studio.film));   // a sound file plays here; else the console's cut has the film
  const list = marks.length ? `<ul class="hits2">${marks.map((k) => `<li${dattr({ mark: "atime:" + k.t.toFixed(1), label: t("sound_label", { t: fmt(k.t) }), t: k.t })}><i class="dotw ${k.cls}" aria-hidden="true">●</i><span class="mono">${esc(fmt(k.t))}</span><span>${esc(k.what)}</span><span class="meta">${esc(k.src)}</span>${can ? `<button type="button" class="xs" data-seek="${k.t}">${esc(t("play_at", { t: fmt(k.t) }))}</button>` : ""}</li>`).join("")}</ul>` : "";
  const SC = (X.checks || []).filter((f) => f.severity !== "info" && /loud|peak|silence|click|clip|audio|sound|voice/i.test(`${f.kind} ${f.message}`));
  const checks = SC.length ? `<p class="mat-h">${esc(t("sound_checks"))}</p><ul class="hits2">${SC.map((f) => `<li${dattr(f.t != null ? { mark: "atime:" + (+f.t).toFixed(1), label: t("sound_label", { t: fmt(f.t) }), t: f.t } : { scope: `${t("m_sound")} · ${f.kind}` })}><i class="dotw ${f.severity === "fail" ? "live" : "wait"}" aria-hidden="true">●</i><span class="mono">${f.t != null ? esc(fmt(f.t)) : ""}</span><span>${esc(f.message)}</span></li>`).join("")}</ul>` : "";
  const music = chart || list ? `${chart}${list}${checks}` : voidLine(t("music_none")) + checks;
  const src2 = soundSource();
  return headM("sound", t("sound_title"), t(readOnly() ? "sound_sub_s" : "sound_sub2")) + tiles + panel(t("audition"), t("audition_cmd"), voices)
    + `<div class="mgrid sound">${panel(t("lines"), t(nl.paced ? "lines_pace" : "lines_raw"), lines)}${panel(t("music"), env ? `${t("music_cmd")} · ${t("env_cmd")}` : t("music_cmd"), music + (src2 ? `<audio id="mau" src="${esc(src(src2))}" preload="none" controls></audio>` : ""))}</div>`;
}
function wireSound2() {
  const a = $("#mau");
  $$("[data-seek]").forEach((b) => b.addEventListener("click", (e) => {
    e.stopPropagation(); const s = +b.dataset.seek;
    if (a) { a.currentTime = s; a.play().catch(() => {}); } else gotoTarget("time:" + s.toFixed(1), s);   // no sound file of its own: the cut, at that second
  }));
  $$("[data-use]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); prefill(b.closest(".vcard"), t("use_say", { x: b.dataset.use })); }));
}
MODVIEW.sound = { main: mSound2, wire: wireSound2 };

/* ---------- 交付: the covers, each platform's copy, what comes out, the check before delivery ---------- */
moduleWords({
  sub_deliver: "交付", ship_title: "母版、封面和各平台文案", ship_sub: "成片那一站通过以后才出片。点哪张封面、哪条文案，都能单独说。",
  covers: "封面", covers_sub: "竖 9:16、横 4:3 或 16:9，标题要大", vertical: "竖", horizontal: "横", square: "方", covers_none: "还没有封面：PACKAGING.md 的封面表，或 out/covers/。",
  copy: "文案", titles: "标题候选", t_title: "标题", t_desc: "简介", t_tags: "标签", t_chapters: "章节", copy_none: "还没有 PACKAGING.md：标题、封面和各平台的文案写在那里（templates/PACKAGING.md）。",
  plat_none: "PACKAGING.md 的「发布文案」还没有平台小节（### B站 …），bin/vh check 会量它们的长度。", checked_n: "标题里的数字和说法：{a} 条核实过，{b} 条还没有（硬规则 5）",
  outputs: "会出什么", o_master: "母版（bin/vh render，检查通过）", o_upload: "上传用的副本（bin/vh deliver）", o_srt: "字幕 SRT", o_covers: "封面 {n} 张", o_copy: "各平台文案 {n} 个", pending: "待出", made: "已出",
  precheck: "出片前检查", to_fix: "有 {n} 处要修", to_mind: "{n} 处注意", passed: "过了", stale2: "片子在这次检查之后改过：再跑一次 bin/vh check",
  precheck_none: "还没跑出片前检查：bin/vh check <片子>。", next_cmd: "成片通过以后：", bar_ship: "成片那一站通过以后才出片", to_cut: "去成片",
  g_safe: "安全框、字号、读时", g_text: "字不被光烧白", g_loud: "响度和真峰值", g_av: "数字静音、闪白、黑场、冻帧", g_assets: "素材许可", g_pack: "标题和文案", g_other: "其他",
}, {
  sub_deliver: "Delivery", ship_title: "Master, covers and copy for each platform", ship_sub: "The film is delivered once the cut's stop has passed. Click a cover or a line of copy to say something about it alone.",
  covers: "Covers", covers_sub: "vertical 9:16, horizontal 4:3 or 16:9, a big title", vertical: "vertical", horizontal: "horizontal", square: "square", covers_none: "No covers yet: PACKAGING.md's cover table, or out/covers/.",
  copy: "Copy", titles: "Title candidates", t_title: "Title", t_desc: "Description", t_tags: "Tags", t_chapters: "Chapters", copy_none: "No PACKAGING.md yet: the titles, the covers and each platform's copy go there (templates/PACKAGING.md).",
  plat_none: "PACKAGING.md's 发布文案 has no platform yet (### Bilibili …); bin/vh check measures them.", checked_n: "The numbers and claims in the titles: {a} checked, {b} not yet (hard rule 5)",
  outputs: "What comes out", o_master: "The master (bin/vh render, checked)", o_upload: "The copy to upload (bin/vh deliver)", o_srt: "Captions (SRT)", o_covers: "{n} covers", o_copy: "Copy for {n} platforms", pending: "to come", made: "made",
  precheck: "Before delivery", to_fix: "{n} to fix", to_mind: "{n} to mind", passed: "passed", stale2: "The film changed after this check: run bin/vh check again",
  precheck_none: "No check before delivery yet: bin/vh check <film>.", next_cmd: "Once the cut has passed:", bar_ship: "The film is delivered once the cut's stop has passed", to_cut: "To the cut",
  g_safe: "Safe area, type size, read time", g_text: "Type not burnt out by light", g_loud: "Loudness and true peak", g_av: "Digital silence, flashes, black, freezes", g_assets: "Licences", g_pack: "Titles and copy", g_other: "Other",
});
const CHECK_GROUPS = [["g_safe", /safe|read|scale|subtitle|caption|size/i], ["g_text", /textcheck|^text/i], ["g_loud", /loud|peak|lufs/i],   // check's kinds (tools/desk/README.md, 检查记录)
  ["g_av", /silence|flash|black|freeze|static|fade|\.iso|periodic|\.cut|blind/i], ["g_assets", /asset|licen/i], ["g_pack", /packag|cover|title/i]];
let shipPlat = 0;
const ratioName = (r) => { const R = [["9:16", 0.5625], ["3:4", 0.75], ["1:1", 1], ["4:3", 1.333], ["16:9", 1.778]]; return R.reduce((a, b) => (Math.abs(b[1] - r) < Math.abs(a[1] - r) ? b : a))[0]; };
function mShip2() {
  const X = D.mods || {}, pk = D.packaging, covers = X.covers || [], st = D.status || {};
  const cov = covers.length ? `<div class="covers">${covers.map((c) => `<figure class="cov${c.ratio && c.ratio < 1 ? " v" : ""}"${dattr({ mark: "asset:" + c.path, label: `${t("covers")} ${c.id || c.path.split("/").pop()}` })}>
      <span class="well"><span class="ph">${esc(c.id || "")}</span><img src="${esc(src(c.path))}" alt="${esc(c.text || c.id || "")}" loading="lazy"></span>
      <figcaption class="meta">${esc([c.ratio ? `${t(c.ratio < 0.95 ? "vertical" : c.ratio > 1.05 ? "horizontal" : "square")} ${ratioName(c.ratio)}` : "", c.id, c.text].filter(Boolean).join(" · "))}</figcaption></figure>`).join("")}</div>` : voidLine(t("covers_none"));
  let copy = voidLine(t("copy_none"));
  if (pk) {
    const P = pk.platforms || [], i = Math.min(shipPlat, Math.max(0, P.length - 1)), p = P[i], chap = (pk.copy.find((c) => /章节|chapter/i.test(c.k)) || {}).v;
    const row = (k, v, html) => `<div${dattr({ mark: `doc:PACKAGING.md#${p ? p.name + " " : ""}${t(k)}`, label: `${p ? p.name + " · " : ""}${t(k)}` })}><dt>${esc(t(k))}</dt><dd>${html || esc(v)}</dd></div>`;
    const tabs = P.length > 1 ? `<nav class="pgtabs plat">${P.map((x, j) => `<button type="button" data-plat="${j}" aria-current="${j === i}">${esc(x.name)}</button>`).join("")}</nav>` : P.length ? `<span class="chip quiet">${esc(p.name)}</span>` : "";
    const fields = p ? `<dl class="kv2">${p.title ? row("t_title", p.title) : ""}${p.desc ? row("t_desc", "", esc(p.desc).replace(/\n/g, "<br>")) : ""}${chap ? row("t_chapters", chap) : ""}${p.tags.length ? row("t_tags", "", p.tags.map((x) => `<span class="tagc">${esc(x)}</span>`).join("")) : ""}</dl>` : voidLine(t("plat_none"));
    const T = pk.titles || [], checked = (x) => /已核实|核实过|verified|^yes$|^✓$/i.test(x.checked || ""), facts = T.filter((x) => x.fact && !/^[—–-]$/.test(x.fact));
    const titles = T.length ? `<h3 class="mat-h">${esc(t("titles"))}</h3><ul class="copyl">${T.map((x) => `<li${dattr({ mark: `doc:PACKAGING.md#${x.id || x.title}`, label: `${t("t_title")} ${x.id || ""}`.trim() })}><span class="mono">${esc(x.id)}</span><b>${esc(x.title)}</b>${x.type ? `<span class="meta">${esc(x.type)}</span>` : ""}${facts.includes(x) ? `<span class="chip ${checked(x) ? "ok" : "wait"}">${esc(x.fact)}</span>` : ""}</li>`).join("")}</ul>
      ${facts.length ? `<p class="meta fine">${esc(t("checked_n", { a: facts.filter(checked).length, b: facts.filter((x) => !checked(x)).length }))}</p>` : ""}` : "";
    copy = `<div class="copyhead">${tabs}</div>${fields}${titles}`;
  }
  const dl = st.deliveries || [], chk = st.check;
  const outs = [["o_master", chk && chk.verdict === "pass" && !chk.stale ? chk.video : ""], ["o_upload", dl.length ? dl[dl.length - 1].output : ""],
    ["o_srt", (X.subs || [])[0] || ""], ["o_covers", covers.length ? " " : ""], ["o_copy", pk && (pk.platforms || []).length ? " " : ""]];
  const outputs = `<ul class="outl">${outs.map(([k, v]) => `<li><span class="chip ${v ? "ok" : "quiet"}">${esc(t(v ? "made" : "pending"))}</span><span>${esc(t(k, { n: k === "o_covers" ? covers.length : ((pk && pk.platforms) || []).length }))}</span>${v.trim() ? `<span class="meta mono">${esc(v)}</span>` : ""}</li>`).join("")}</ul>`;
  const C = X.checks || [];
  const groups = CHECK_GROUPS.map(([k, re]) => [k, C.filter((f) => re.test(f.kind || ""))]).concat([["g_other", C.filter((f) => !CHECK_GROUPS.some(([, re]) => re.test(f.kind || "")))]]).filter(([k, fs]) => k !== "g_other" || fs.length);
  const pre = chk ? `${chk.stale ? `<p class="notice">${esc(t("stale2"))}</p>` : ""}<ul class="checkl">${groups.map(([k, fs]) => {
      const fail = fs.filter((f) => f.severity === "fail").length, warn = fs.filter((f) => f.severity === "warn").length;
      const chip = fail ? `<span class="chip live">${esc(t("to_fix", { n: fail }))}</span>` : warn ? `<span class="chip wait">${esc(t("to_mind", { n: warn }))}</span>` : `<span class="chip ok">${esc(t("passed"))}</span>`;
      const first = fs.find((f) => f.severity !== "info");
      return `<li${dattr(first && first.t != null ? { mark: "time:" + (+first.t).toFixed(1), label: `${t("precheck")} · ${t(k)}`, t: first.t } : { scope: `${t("precheck")} · ${t(k)}` })}><span><b>${esc(t(k))}</b>${first ? `<span class="meta">${esc(cut(first.message, 60))}</span>` : ""}</span>${chip}</li>`; }).join("")}</ul>` : voidLine(t("precheck_none"));
  const next = `<p class="meta fine">${esc(t("next_cmd"))} <code>bin/vh deliver ${esc((chk && chk.video) || "<master>")}</code></p>`;
  return headM("ship", t("ship_title"), t("ship_sub")) + tabs("ship")
    + `<div class="mgrid ship"><div>${panel(t("covers"), t("covers_sub"), cov)}${panel(t("copy"), "PACKAGING.md", copy)}</div><aside class="side">${panel(t("outputs"), "", outputs)}${panel(t("precheck"), "bin/vh check", pre + next)}</aside></div>`
    + barM(t("bar_ship"), "cut", t("to_cut"));
}
function wireShip2() { $$(".pgtabs.plat [data-plat]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); shipPlat = +b.dataset.plat; redraw(); })); }
MODVIEW.ship = { main: mShip2, wire: wireShip2 };

/* ---------- 素材: every item with its licence, its source and its shot; the references and their transcripts ---------- */
moduleWords({
  assets_title: "素材库", assets_sub2: "每一件都记着从哪来、什么许可、用在哪一镜。许可没写清的，出片前会拦下来。",
  f_image: "图片", f_video: "视频", f_audio: "声音", f_font: "字体", f_ref: "参考", k_file: "文件",
  drop: "把文件拖进来，或者贴一个链接", drop_note: "这一版不接 agent：登记用 bin/vh assets add <项目> <文件>，参考用 bin/vh ref add",
  l_cc0: "CC0", l_pd: "公有领域", l_own: "自己做的", l_generated: "自己生成", l_unknown: "来源没写许可", l_free: "免费可用", l_managed: "平台授权", l_ref: "只做参考",
  used_in: "用在 {x}", from: "来自 {x}", not_used: "还没用上", gone_file: "文件不在了", read_transcript: "读文稿", open_src: "原始链接", digest: "长视频读成的文稿", none_kind: "这一类还没有。",
  licenses_ok: "{n} 件许可记清了", licenses_todo: "{n} 件许可没清：只能当参考，不能放进片子", ledger_at: "记在 assets/ledger.json（bin/vh assets）", assets_none: "还没有素材台账：bin/vh assets add <项目> <文件>。",
}, {
  assets_title: "Material", assets_sub2: "Each item says where it came from, its licence and the shot it is in. Anything whose licence isn't clear is stopped before delivery.",
  f_image: "Images", f_video: "Video", f_audio: "Sound", f_font: "Fonts", f_ref: "References", k_file: "File",
  drop: "Drop a file here, or paste a link", drop_note: "No agent in this console yet: bin/vh assets add <project> <file> records an item, bin/vh ref add a reference",
  l_cc0: "CC0", l_pd: "public domain", l_own: "made here", l_generated: "generated", l_unknown: "no licence given", l_free: "free to use", l_managed: "licensed", l_ref: "reference only",
  used_in: "in {x}", from: "from {x}", not_used: "not used yet", gone_file: "the file is gone", read_transcript: "Read the transcript", open_src: "The source", digest: "Long videos read as transcripts", none_kind: "None of these yet.",
  licenses_ok: "{n} licences on record", licenses_todo: "{n} not cleared: reference only, not in the film", ledger_at: "in assets/ledger.json (bin/vh assets)", assets_none: "No asset ledger yet: bin/vh assets add <project> <file>.",
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
    const a = x.a, uses = (a.used_by || []).join("、");
    const pic = x.k === "image" && a.there ? `<img src="${esc(src(a.path))}" alt="" loading="lazy">` : x.k === "font" ? `<span class="glyph">字 Aa</span>` : "";
    return `<article class="acard${CLEARED.includes(a.license) ? "" : " flag"}"${dattr({ mark: a.path ? "asset:" + a.path : "", scope: a.path ? "" : `${t("m_assets")} · ${a.id}`, label: `${t("m_assets")} ${a.id}` })}>
      <div class="well"><span class="ph">${esc(x.k === "audio" ? "♪" : x.k === "video" ? "▶" : x.k === "font" ? "" : String(a.id || "·").slice(0, 1))}</span>${pic}</div>
      <div class="ac-b"><h3>${esc(a.id)}</h3><p><span class="chip ${licLamp(a.license)}"${a.license_name ? ` title="${esc(a.license_name)}"` : ""}>${esc(licText(a))}</span><span class="meta">${esc(t(x.k === "file" ? "k_file" : "f_" + x.k))}</span>${a.aigc ? `<span class="meta">AIGC</span>` : ""}</p>
      <p class="meta">${esc(uses ? t("used_in", { x: uses }) : t("not_used"))}${a.source ? " · " + esc(t("from", { x: a.source })) : ""}</p>${a.note ? `<p class="meta">${esc(a.note)}</p>` : ""}${a.path && !a.there ? `<p class="meta warn">${esc(t("gone_file"))}</p>` : ""}</div></article>`;
  };
  const counts = { all: items.length }; items.forEach((x) => { counts[x.k] = (counts[x.k] || 0) + 1; });
  const filters = `<nav class="pgtabs" aria-label="${esc(t("m_assets"))}">${["all", "image", "video", "audio", "font", "ref"].map((k) => `<button type="button" data-af="${k}" aria-current="${assetFilter === k}">${esc(t("f_" + k))}${counts[k] ? ` <span class="mono">${counts[k]}</span>` : ""}</button>`).join("")}</nav>`;
  const ok = (A || []).filter((a) => CLEARED.includes(a.license)).length, todo = (A || []).length - ok;
  const digests = G.length ? panel(t("digest"), "bin/vh ref digest", `<ul class="copyl">${G.map((g) => `<li${dattr({ mark: "asset:" + g.path, label: `${t("digest")} ${g.id}` })}><span class="mono">${esc(g.id)}</span><a href="${esc(src(g.path))}" target="_blank" rel="noopener">${esc(t("read_transcript"))} ↗</a><span class="meta mono">${esc(Math.max(1, Math.round(g.bytes / 1024)) + " kB")}</span></li>`).join("")}</ul>`) : "";
  return headM("assets", t("assets_title"), t("assets_sub2"), filters)
    + (readOnly() ? "" : `<div class="drop"><b>${esc(t("drop"))}</b><span class="meta">${esc(t("drop_note"))}</span></div>`)
    + (A == null && !R.length ? voidLine(t("assets_none")) : `<div class="acards">${shown.map(card).join("") || voidLine(t("none_kind"))}</div>`) + digests
    + (A ? `<footer class="mbar"><span><i class="dotw ok" aria-hidden="true">●</i> ${esc(t("licenses_ok", { n: ok }))}${todo ? `　<i class="dotw wait" aria-hidden="true">●</i> ${esc(t("licenses_todo", { n: todo }))}` : ""}</span><span class="meta">${esc(t("ledger_at"))}</span></footer>` : "");
}
function wireAssets2() { $$("[data-af]").forEach((b) => b.addEventListener("click", () => { assetFilter = b.dataset.af; redraw(); })); }
MODVIEW.assets = { main: mAssets2, wire: wireAssets2 };

/* ---------- 账本: the decisions, your words, the versions ---------- */
moduleWords({
  ledger_title: "谁定的、为什么、什么时候", ledger_sub2: "DECISIONS.md 和 REVIEW.md 在这里一起看。agent 定的每一条都能翻案：这一版写成点评，随这一轮交给它。",
  decisions: "决定", what: "什么事", decided: "定成什么", who: "谁定的", when: "时间", reason: "理由", you_decide: "你定", show_you: "给你看", agent_decides: "agent 定", waits: "等你",
  overturn_say: "翻案：", your_words: "你的原话", your_words_sub: "逐字记在 REVIEW.md", versions: "版本", ver_cmd: "bin/vh versions", v_n: "第 {n} 版",
  changed_n: "改了 {n} 段", changed_s: "改了 {x}", whole_film2: "整片", words_none: "REVIEW.md 里还没有原话。", versions_none: "还没有版本记录：第一次 bin/vh render 或 patch 之后才有。",
  dec_none: "DECISIONS.md 里还没有决定。", you_said2: "你说：{q}",
}, {
  ledger_title: "Who decided, why, and when", ledger_sub2: "DECISIONS.md and REVIEW.md side by side. Anything the agent decided can be overturned: write it as a note for now, and it goes with this round.",
  decisions: "Decisions", what: "What", decided: "Decided", who: "By", when: "When", reason: "Why", you_decide: "you", show_you: "shown to you", agent_decides: "the agent", waits: "waiting for you",
  overturn_say: "Overturn: ", your_words: "Your words", your_words_sub: "verbatim in REVIEW.md", versions: "Versions", ver_cmd: "bin/vh versions", v_n: "v{n}",
  changed_n: "{n} stretches changed", changed_s: "changed {x}", whole_film2: "the whole film", words_none: "No words of yours in REVIEW.md yet.", versions_none: "No versions recorded yet: the first bin/vh render or patch makes one.",
  dec_none: "No decisions in DECISIONS.md yet.", you_said2: "you said: {q}",
});
const dateOf = (h) => h.date || "";
function mLedger2() {
  const who = (w, s) => (/等|wait/i.test(s || "") ? ["waits", "wait"] : /^own|你|person/i.test(w || "") ? ["you_decide", ""] : /^review|看/i.test(w || "") ? ["show_you", "quiet"] : ["agent_decides", "agent"]);
  const quoteFor = (where) => { const g = (String(where || "").match(/[①②③]|E\d/) || [""])[0]; const h = g ? D.history.find((x) => x.title.includes(g)) : null; return h && h.quotes && h.quotes.length ? h.quotes[h.quotes.length - 1].text : ""; };
  const rows = D.ledger.map((l) => { const [k, c] = who(l.who, l.status), q = quoteFor(l.where), h = D.history.find((x) => /[①②③]|E\d/.test(l.where || "") && x.title.includes((String(l.where).match(/[①②③]|E\d/) || [""])[0]));
      return `<tr${dattr({ mark: `doc:DECISIONS.md#${l.what}`, label: `${t("decisions")} · ${l.what}` })}><td>${esc(l.what)}</td><td>${esc(l.status)}</td><td><span class="chip ${c}">${esc(t(k))}</span></td><td class="mono">${esc(h ? dateOf(h) : "")}</td><td class="muted">${esc(q ? t("you_said2", { q }) : l.where || "")}</td><td></td></tr>`; })
    .concat(D.agent_decided.filter((a) => !a.superseded).map((a) => { const i = D.agent_decided.indexOf(a);
      return `<tr${dattr({ mark: "led:" + i, label: t("l_led", { x: (a.topic ? a.topic + COLON() : "") + cut(a.what, 20) }) })}><td>${esc(a.topic || "—")}</td><td>${esc(a.what)}</td><td><span class="chip agent">${esc(t("agent_decides"))}</span></td><td class="mono">${esc(a.date || "")}</td><td class="muted">${esc(a.why || "")}</td><td>${readOnly() ? "" : `<button type="button" class="xs" data-overturn="${i}">${esc(t("overturn"))}</button>`}</td></tr>`; })).join("");
  const dec = rows ? `<div class="tscroll"><table class="t ledger"><thead><tr><th>${esc(t("what"))}</th><th>${esc(t("decided"))}</th><th>${esc(t("who"))}</th><th>${esc(t("when"))}</th><th>${esc(t("reason"))}</th><th></th></tr></thead><tbody>${rows}</tbody></table></div>` : voidLine(t("dec_none"));
  const Q = D.history.flatMap((h) => (h.quotes || []).map((q) => ({ h, q })));
  const words = Q.length ? `<ul class="quotes">${Q.map(({ h, q }) => `<li${dattr({ scope: `${t("your_words")} · ${cut(h.title, 24)}` })}><q>${esc(q.text)}</q><span class="meta">${esc([cut(h.title, 30), q.label, dateOf(h)].filter(Boolean).join(" · "))}</span></li>`).join("")}</ul>` : voidLine(t("words_none"));
  const V = ((D.status || {}).versions || {}).list || [];
  const vers = V.length ? `<ul class="copyl vers">${V.slice().reverse().map((v) => { const n = v.n != null ? v.n : (String(v.id).match(/\d+/) || [""])[0], ch = v.changed || {};
      const what = ch.whole || !Object.keys(ch).length ? t("whole_film2") : (ch.shots || []).length ? t("changed_s", { x: ch.shots.slice(0, 4).join("、") }) : t("changed_n", { n: (ch.seconds || ch.frames || []).length });
      return `<li${dattr({ scope: `${t("versions")} · ${t("v_n", { n })}` })}><span class="chip ${v.state === "current" ? "" : "quiet"}">${esc(t("v_n", { n }))}</span><b>${esc(v.note || v.made_by || "")}</b><span class="meta">${esc(what)}</span></li>`; }).join("")}</ul>` : voidLine(t("versions_none"));
  return headM("ledger", t("ledger_title"), t("ledger_sub2")) + tabs("ledger") + panel(t("decisions"), "DECISIONS.md · REVIEW.md", dec)
    + `<div class="mgrid ledger">${panel(t("your_words"), t("your_words_sub"), words)}${panel(t("versions"), t("ver_cmd"), vers)}</div>`;
}
function wireLedger2() { $$("[data-overturn]").forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); prefill(b.closest("[data-mark]"), t("overturn_say")); })); }
MODVIEW.ledger = { main: mLedger2, wire: wireLedger2 };
