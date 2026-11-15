"use strict";
/* The console's modules besides the cut (docs/proposals/02-studio-client.md, 3), laid out as the prototype draws them
   (docs/proposals/figs/02-studio-prototype.html): 立意, 大纲, 分镜, 声音, 交付, 素材, 账本. A section a module: its words,
   its page and its wiring, registered in MODVIEW; studio.js draws a module's first tab from it. Loaded before studio.js
   (and before a static page's static.js): nothing here runs until the host calls it, and then it uses the host's helpers
   and state (esc, t, src, D, FB, ROUND, setScope, pick …).
   Everything a person can select says what it is: data-mark names a feedback target (tools/desk/README.md, 反馈文件),
   data-scope a place with no target of its own, whose note goes into the round's overall words with its name in front;
   data-label is the name a note carries. Every part reads a file bin/vh has already made; a part that is not there says
   so and names the command that makes it. */

const MSTR = { zh: {}, en: {} };   // the modules' words; t() (studio.js) looks here after the shell's own
const moduleWords = (zh, en) => { Object.assign(MSTR.zh, zh); Object.assign(MSTR.en, en); };
const MODVIEW = {};   // module → { main(): html, wire(), sync(decision, option), drawn(gate view): what the module draws itself }
const readOnly = () => typeof STATIC_PAGE !== "undefined";   // a static page (bin/vh review): nothing to note, nothing to send

/* ---------- shared pieces ---------- */
moduleWords({ page_rest: "{g} 的页里还有这些" }, { page_rest: "Also on {g}'s page" });
const dattr = (o) => Object.entries(o).filter(([, v]) => v != null && v !== "").map(([k, v]) => ` data-${k}="${esc(v)}"`).join("");
const rich = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\n/g, "<br>");   // a gate page's own marks
const panel = (title, sub, body, cls) => `<section class="pn${cls ? " " + cls : ""}">${title ? `<h2 class="pn-h"><span>${esc(title)}</span>${sub ? `<span class="pn-sub">${esc(sub)}</span>` : ""}</h2>` : ""}${body}</section>`;
const voidLine = (s) => `<p class="void">${esc(s)}</p>`;
function headM(mod, title, sub, extra) {
  return `<header class="mh2"><div class="mh2-t"><span class="kick">${esc(kickOf(mod))}</span><h1>${esc(title)}</h1>${sub ? `<p>${esc(sub)}</p>` : ""}</div>${extra || ""}</header>`;
}
function barM(text, mod, label) {   // the bar under a module: where its stop stands, and the next module
  return `<footer class="mbar"><span>${esc(text)}</span>${mod && !readOnly() ? `<a class="btn" href="${projHash(PKEY, mod)}">${esc(label)} →</a>` : ""}</footer>`;
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
  bar_idea_wait: "关卡 ① 等你选：选好以后，在右边一列提交这一轮", bar_idea_done: "立意定了：再改它，大纲和分镜都要跟着重做", to_outline: "看大纲",
}, {
  idea_title: "{n} concept cards: pick one", idea_sub: "Pick a card and the concept, the look and the hook are settled together. On the left: what only this subject has.",
  mat_h: "What only this subject has", k_number: "Numbers", k_object: "Objects", k_quote: "Words", k_conflict: "Contradictions", k_surprise: "Surprises", k_other: "Other",
  same_topic: "What videos on it usually look like", same_none: "NOTES.md's ideas don't say yet what other videos on this subject look like (playbook/12-ideation.md, 3).",
  mat_none: "NOTES.md has no material list yet: first list the numbers, objects and words only this material has (playbook/12-ideation.md, 2).",
  rec: "recommended", picked: "your pick", pick_this: "Pick this", picked_btn: "Picked", like_this: "Another like it", like_say: "Another card like {x}: ",
  pro: "Pro", con: "Cost", l_card: "Concept card {x}",
  cards_none: "No concept cards yet: once gate ①'s page is written (bin/vh gate <project> 1), they are here. Below is the concept the BRIEF has.",
  bar_idea_wait: "Gate ① waits for you: once you have picked, submit this round in the right column", bar_idea_done: "The concept is settled: change it now, and the outline and the storyboard follow", to_outline: "See the outline",
});
const KINDS = [["number", /数字|数据|number/i], ["object", /物件|物|object|thing/i], ["quote", /原话|引文|引语|quote|words/i], ["conflict", /矛盾|冲突|contradict|conflict/i], ["surprise", /意外|反常|surpris/i]];
const kindOf = (k) => (KINDS.find(([, re]) => re.test(k || "")) || ["other"])[0];
function conceptRound() {   // the newest gate ① page and its concept decision: the one drawn with pictures, else one named for it
  const r = D.rounds.filter((x) => gateBase(x.id) === "1").pop();
  if (!r) return null;
  const decs = (r.data.decisions || []).filter((d) => d && Array.isArray(d.options) && d.options.length);
  const dec = decs.find((d) => d.options.some((o) => o && o.frame)) || decs.find((d) => /concept|立意|idea/i.test(`${d.id} ${d.question || ""}`));
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
        <div class="well"><span class="ph">${esc(o.id)}</span>${o.frame ? `<img src="${esc(src(o.frame))}" alt="${esc(o.id)}" loading="lazy">` : ""}</div>
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
    + barM(t(wait ? "bar_idea_wait" : "bar_idea_done"), "outline", t("to_outline"));
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
MODVIEW.idea = { main: mIdea2, wire: wireIdea, sync: syncIdea,
  drawn(root) { const cr = conceptRound(); if (cr) $$(".g-dec.wide", root).filter((x) => x.dataset.dec === cr.dec.id).forEach((x) => x.remove()); } };

/* ---------- 大纲: the parts in proportion, the BRIEF, the engine and the cost ---------- */
moduleWords({
  outline_title: "{n} 段大纲", outline_sub: "段名按内容起，看名字就知道这段讲什么。点一段，就能只对它说。", seg_know: "要看懂", seg_pic: "画面", unsure_n: "{n} 处没把握",
  brief_h: "BRIEF", engine_cost: "引擎和花费", engine: "引擎", voice: "配音", budget: "预算", spent: "已花", stops: "停在哪", free: "不调付费接口",
  b_concept: "立意", b_spine: "主线", b_end: "看完以后", b_hook: "钩子", b_audience: "观众", b_watch: "在哪看", b_output: "规格", b_pace: "节奏", b_effort: "档位", b_director: "谁拍板",
  outline_none: "BRIEF 的大纲还没写成表格（列名见 tools/desk/README.md 的读取约定）。", bar_outline: "大纲属于关卡 ①（{s}）：改它，分镜要跟着重做", to_board: "去分镜",
}, {
  outline_title: "An outline in {n} parts", outline_sub: "Each part is named by what it says. Click one to say something about it alone.", seg_know: "Reads", seg_pic: "Picture", unsure_n: "{n} unsure",
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
  return headM("outline", O.length ? t("outline_title", { n: O.length }) : t("m_outline"), t("outline_sub")) + subtabs("outline")
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
