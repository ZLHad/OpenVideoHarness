"use strict";
/* The console (bin/vh desk): Studio without the agent connected (docs/proposals/02-studio-client.md, 2–4). The shell is the
   module rail, the flow bar of the film's stops and the right column (what waits for you, this round's notes and its one
   submission, a box that writes a note against what is selected). The space lists every film; a film opens on the module of
   the stop that waits (gate ① 立意, ② 分镜, ③ 成片). The cut module lays the film, its shots, narration, music, checks and
   notes out on one timeline. It reads the server's JSON (tools/desk/server.py: the project files and bin/vh, read fresh) and
   the gate view's markup (tools/review.py; ui.js mounts it). The reviewer's draft stays in this browser (localStorage) until it
   goes to /api/p/<key>/feedback, the desk's one submission channel. No framework, no CDN. Every text from a project is escaped
   before it reaches the page (documents arrive as HTML that reader.py has already escaped). The words and the helpers a
   static review page shares are in core.js, the other modules in modules.js; both load before this file. */
const TOKEN = (document.querySelector('meta[name="desk-token"]') || {}).content || "";
const HOME = (document.querySelector('meta[name="desk-home"]') || {}).content || "";
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
let COLCTL = null, PARTCTL = null, CUT = null, liveTimer = null, homeTimer = null;
const src = (p) => (/^https?:\/\//.test(p || "") ? p : `/f/${enc(PKEY)}/` + String(p || "").split("/").map(enc).join("/"));
const MODS = ["idea", "outline", "board", "sound", "cut", "ship", "assets", "ledger"];
const LEGACY = { round: "", concept: "idea", script: "outline/script", board: "board", sound: "sound", facts: "outline/facts", film: "cut", check: "ship/check",
  versions: "ship/versions", assets: "assets", ledger: "ledger", history: "ledger/history", docs: "ledger/docs" };
const ICON = {
  space: '<path d="M4 11l8-6 8 6v8.5a.5.5 0 0 1-.5.5H15v-5H9v5H4.5a.5.5 0 0 1-.5-.5z"/>',
  new: '<path d="M12 5v14M5 12h14"/>',
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
  $("#rail").setAttribute("aria-label", t("rail")); $("#flow").setAttribute("aria-label", t("flow")); $("#themes").setAttribute("aria-label", t("themes")); $("#themeBtn").textContent = t("themes");
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
function renderFlow() {
  const el = $("#flow");
  if (!D) { el.innerHTML = ""; return; }
  el.innerHTML = FLOW.map((f) => {   // each stop by its name, its state in words under it (已定 11-14, 等你, 跳过): no numbers, no strikes
    const fs = flowState(f), word = flowWord(fs);
    const tip = [t("m_" + f.mod), word].concat(fs.S.map((s) => s.note).filter(Boolean).map((n) => { const w = statusWords(n); return w.known ? w.text : `${t("ns_raw")}${COLON()}${w.text}`; })).join(" · ");
    return `<li><button type="button" class="stn ${fs.state}" data-go-mod="${f.mod}" title="${esc(tip)}" aria-current="${MOD === f.mod}"><span class="nm"><i aria-hidden="true"></i>${esc(t("m_" + f.mod))}</span><small>${esc(word)}</small></button></li>`;
  }).join("");
}
function waitsIn(mod) { const f = FLOW.find((x) => x.mod === mod); return !!f && flowState(f).state === "wait"; }
function renderRail() {   // the space and a new film; a film's modules only while a film is open (on the space they would point at nothing, or at the last film)
  const proj = !!D;
  const item = (m) => {
    if (m === "space") return `<a class="mod" href="#/" aria-current="${!proj ? "page" : "false"}">${svg("space")}<span>${esc(t("m_space"))}</span></a>`;
    const dot = waitsIn(m) ? '<i class="dot" aria-hidden="true"></i>' : "";
    return `<a class="mod" href="${projHash(PKEY, m)}" aria-current="${MOD === m ? "page" : "false"}" data-mod="${m}">${svg(m)}<span>${esc(t("m_" + m))}</span>${dot}</a>`;
  };
  const fresh = `<a class="mod" href="#/" data-new title="${esc(t("new_tip"))}">${svg("new")}<span>${esc(t("m_new"))}</span></a>`;   // its place kept: it needs the agent
  $("#rail").innerHTML = item("space") + fresh + (proj ? "<hr>" + ["idea", "outline", "board", "sound", "cut", "ship"].map(item).join("") + '<span class="grow"></span><hr>' + ["assets", "ledger"].map(item).join("") : "");
}
$("#rail").addEventListener("click", (e) => { if (e.target.closest("[data-new]")) setTimeout(() => { const x = $("#oneLine"); if (x) x.focus(); }, 300); });   // 新建: the space's sentence box
$("#flow").addEventListener("click", (e) => { const b = e.target.closest("[data-go-mod]"); if (b && PKEY) go(projHash(PKEY, b.dataset.goMod)); });

/* ---------- the space: the films waiting for you first and biggest, then the ones in progress, then the ones done ---------- */
function dayOf(sec) {   // one way to write a day everywhere on the space: 今天, 11-14, 2025-11-14
  if (!sec) return "";
  const d = new Date(sec * 1000);
  return d.toDateString() === new Date().toDateString() ? t("today") : shortDate(`${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`);
}
const TYPE_WORDS = { "01": ["原理讲解", "Explainer"], "02": ["知识短视频", "Knowledge short"], "03": ["产品片", "Product film"], "04": ["MV", "Music video"],
  "05": ["数据故事", "Data story"], "06": ["论文讲解", "Paper explainer"], "07": ["手绘短片", "Hand-drawn"], "08": ["快剪", "Fast cut"],
  "09": ["口播剪辑", "Talking head"], "10": ["长讲解", "Long explainer"], "11": ["照片回顾", "Photo recap"] };
const TYPE_KEYS = { math: "01", short: "02", promo: "03", mv: "04", data: "05", paper: "06", handdrawn: "07", meme: "08", edit: "09", long: "10", recap: "11" };
function typeWords(ty) {   // a film's kind by its name in this page's language ("01-math-science-explainer", "math" → 原理讲解)
  const x = String(ty || "").trim().toLowerCase(), m = x.match(/^(\d\d)\b/), k = m ? m[1] : TYPE_KEYS[x];
  return k && TYPE_WORDS[k] ? TYPE_WORDS[k][LANG === "zh" ? 0 : 1] : "";
}
function lampOf(r) {   // violet only for what is running now (bin/vh status's activity), not for every film the agent could pick up
  return r.state === "waiting_person" ? "wait" : (r.running || []).length ? "agent" : r.state === "delivered" ? "done" : "";
}
function stopOf(r) { return r.station ? (L.stn[r.station.id] || r.station.name || "") : ""; }
function filmName(r) { return r.title && r.title !== r.name ? r.title : String(r.name || "").replace(/^\d{4}-\d{2}-\d{2}-/, ""); }   // a film with no title of its own: its folder, without the date in front
function stateWords(r) {   // where a film is, in words: 初版 · 等你看, 大纲 · 在做, 正在渲染, 已交付 10-23
  if ((r.running || []).length && r.state !== "waiting_person") return cmdWords(r.running[0]);
  if (r.state === "delivered") return r.delivered ? t("f_delivered_d", { d: shortDate(r.delivered) }) : t("st_delivered");
  const s = stopOf(r), st = t("st_" + (r.state || "not_started"));
  return ["waiting_person", "waiting_agent", "in_progress"].includes(r.state) && s ? `${s} · ${st}` : st;
}
function picture(r, cls) {   // the film's letter is always under the picture: a picture that does not come leaves the letter, not a void
  const p = r.picture, ph = `<span class="ph">${esc(String(filmName(r) || "·").trim().slice(0, 1))}</span>`;
  if (p && p.kind === "image") return `<span class="well ${cls || ""}">${ph}<img src="${esc(p.href)}" alt="" loading="lazy"></span>`;
  if (p && p.kind === "video") return `<span class="well ${cls || ""}">${ph}<video muted playsinline preload="none" data-mid data-src="${esc(p.href)}"></video></span>`;
  return `<span class="well ${cls || ""}">${ph}<span class="ph-why">${esc(t(r.state === "delivered" ? "no_pic_gone" : "no_pic"))}</span></span>`;   // no picture at all: say so, so it does not read as one still loading
}
function card(r) {   // its picture, its name, where it is, its kind, its day
  const day = r.last_activity && r.state !== "delivered" ? dayOf(r.last_activity.t) : "", kind = typeWords(r.type);   // a film that went out: its day is in "已交付 10-23"
  return `<a class="pcard" href="${projHash(r.key)}" data-state="${esc(r.state || "")}" data-key="${esc(r.key)}" title="${esc(r.name)}">${picture(r)}
    <span class="pcard-name">${esc(filmName(r))}</span>
    <span class="pcard-meta"><span class="st ${lampOf(r)}"><i aria-hidden="true"></i>${esc(stateWords(r))}</span>${kind ? `<span>${esc(kind)}</span>` : ""}${day ? `<span>${esc(day)}</span>` : ""}</span>
    ${r.error ? `<span class="err" title="${esc(r.error)}">${esc(t("card_err"))}</span>` : ""}</a>`;
}
function heroCard(r) {   // a film that waits for you: what it asks, every question, the agent's line about it, and one button
  const a = r.ask || {}, qs = (a.questions || []).length ? a.questions : a.question ? [a.question] : [];
  const head = [stopOf(r), a.decisions ? t("ask_count", { n: a.decisions }) : t("st_waiting_person")].filter(Boolean).join(" · ");
  const sum = a.summary && !qs.includes(a.summary) ? a.summary : "";
  const day = r.last_activity ? dayOf(r.last_activity.t) : "", kind = typeWords(r.type);
  return `<a class="hero" href="${projHash(r.key)}" data-state="waiting_person" data-key="${esc(r.key)}" title="${esc(r.name)}">${picture(r)}
    <span class="hero-txt"><span class="pcard-meta"><span class="st wait"><i aria-hidden="true"></i>${esc(head)}</span>${kind ? `<span>${esc(kind)}</span>` : ""}${day ? `<span>${esc(day)}</span>` : ""}</span>
      <span class="hero-name">${esc(filmName(r))}</span>
      ${sum ? `<span class="hero-sum">${esc(cut(sum, 120))}</span>` : ""}
      ${qs.length ? `<span class="hero-q">${qs.map((q) => `<span>${esc(cut(q, 80))}</span>`).join("")}</span>` : ""}
      <span class="btn btn-primary">${esc(t("go_look"))}</span></span></a>`;
}
async function listing() { const r = await getJSON("/api/projects"); if (r.ok && r.data) LIST = r.data; return r; }
function leaveProject() {
  if (COLCTL) { COLCTL.destroy(); COLCTL = null; }
  if (PARTCTL) { PARTCTL.destroy(); PARTCTL = null; }
  if (CUT) { CUT.destroy(); CUT = null; }
  clearInterval(liveTimer);
  SCOPE = null;
  $("#app").classList.remove("is-cut"); $("#stage").classList.remove("is-cut");   // the space and other films lay out as pages again
}
async function showHome(quiet) {
  if (!quiet) {
    leaveProject(); D = null; PKEY = ""; MOD = ""; GV = null;
    setLang(pickLang(LANG)); crumbs([{ text: t("m_space") }]); renderFlow(); renderRail(); spaceColumn();
  }
  const r = await listing();
  if (parse().view !== "home") return;
  if (!r.ok || !LIST) { $("#stage").innerHTML = `<p class="void module">${esc(t("noServer"))}</p>`; return; }
  const rows = LIST.projects, wait = rows.filter((x) => x.state === "waiting_person"), done = rows.filter((x) => x.state === "delivered");
  const RANK = { waiting_agent: 0, in_progress: 1, paused: 2, not_started: 3, no_record: 4 };   // in progress: the ones moving first, the ones with no record last
  const doing = rows.filter((x) => !wait.includes(x) && !done.includes(x)).map((x, i) => [x, i]).sort((a, b) => ((RANK[a[0].state] ?? 5) - (RANK[b[0].state] ?? 5)) || a[1] - b[1]).map((x) => x[0]);
  const meta = LIST.waiting ? t("home_meta", { n: rows.length, w: LIST.waiting }) : t("home_meta0", { n: rows.length });
  const sect = (k, list, body) => (list.length ? `<section class="sect"><h2>${esc(t(k))}<span class="n">${list.length}</span></h2>${body}</section>` : "");
  const roots = LIST.roots || [];
  const html = `<section class="module space">
    <div class="mh"><h1>${esc(t("films"))}</h1><span class="meta">${esc(meta)}</span></div>
    ${rows.length ? "" : `<p class="void">${esc(t("no_projects"))}</p>`}
    ${sect("g_wait", wait, `<div class="heroes">${wait.map(heroCard).join("")}</div>`)}
    ${sect("g_doing", doing, `<div class="cards">${doing.map(card).join("")}</div>`)}
    ${sect("g_done", done, `<div class="cards">${done.map(card).join("")}</div>`)}
    ${roots.length ? `<p class="roots" title="${esc(roots.map((x) => x.path || x).join("\n"))}">${esc(t("roots_n", { n: roots.length }))}</p>` : ""}</section>`;
  const area = $("#stage"), y = area.scrollTop;
  area.innerHTML = html;
  if (quiet) area.scrollTop = y;
  midFrames(area); hoverClips(area); spaceRunning();
  clearTimeout(homeTimer); homeTimer = setTimeout(() => { if (parse().view === "home") showHome(true); }, 15000);
}
function copyText(s) {
  return new Promise((ok) => {
    const old = () => { const x = document.createElement("textarea"); x.value = s; document.body.appendChild(x); x.select(); try { document.execCommand("copy"); } catch (e) { /* nothing to do */ } x.remove(); ok(); };
    try { navigator.clipboard.writeText(s).then(ok, old); } catch (e) { old(); }
  });
}
function loadMid(v) { if (v.src) return; v.addEventListener("loadedmetadata", () => { try { v.currentTime = v.duration / 2; } catch (e) { /* not seekable */ } }, { once: true }); v.preload = "metadata"; v.src = v.dataset.src; }
function midFrames(root) {   // a card of a film shows its middle frame: the first cards' at once, the others' once they are near the screen
  const vids = $$("video[data-mid]", root);
  vids.slice(0, 12).forEach(loadMid);   // (a hidden or background tab never reports what is on screen)
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
function spaceColumn() {   // the column is where you talk to the agent: on the space, the sentence that starts a new film
  $("#colRound").hidden = true; $("#composer").hidden = true; $("#confirm").hidden = true;
  $("#colHead").innerHTML = `<b>${esc(t("new_film"))}</b>`;
  $("#colBody").innerHTML = `<section class="ask"><label class="blk-h" for="oneLine"><b>${esc(t("ask_h"))}</b></label>
      <textarea id="oneLine" rows="2" placeholder="${esc(t("ask_ph"))}">${esc(store.get("desk:oneLine") || "")}</textarea>
      <div class="row"><span>${esc(t("ask_note"))}</span><button type="button" class="btn btn-primary" id="copyAsk">${esc(t("ask_copy"))}</button></div></section>
    <section id="spaceRun"></section>`;
  $("#oneLine").addEventListener("input", (e) => store.set("desk:oneLine", e.target.value));
  $("#copyAsk").addEventListener("click", () => {
    const s = $("#oneLine").value.trim();
    if (!s) { toast(t("ask_empty")); $("#oneLine").focus(); return; }
    copyText(t("ask_prefix") + s).then(() => toast(t("ask_copied")));
  });
  spaceRunning();
}
function spaceRunning() {   // what the agent is doing now, a film a line, in words; nothing running: one quiet line
  const el = $("#spaceRun"); if (!el) return;
  const agent = ((LIST && LIST.projects) || []).filter((x) => (x.running || []).length);
  el.innerHTML = `<h3 class="blk-h"><b>${esc(t("agent_list"))}</b>${agent.length ? `<span class="n mono">${agent.length}</span>` : ""}</h3>`
    + (agent.length ? `<ul class="film-list agent">${agent.map((r) => `<li><a href="${projHash(r.key)}"><b>${esc(filmName(r))}</b><span class="q">${esc(cmdWords(r.running[0]))}</span></a></li>`).join("")}</ul>`
      : `<p class="quiet-line">${esc(t("agent_idle"))}</p>`);
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
  else if (e.key === "Escape") {
    if (!$("#search").hidden) closeSearch(); else if (!$("#confirm").hidden) closeConfirm();
    else if (typing()) { e.preventDefault(); document.activeElement.blur(); }   // out of the box, so the keys work again (what was typed stays)
  }
});
document.addEventListener("click", (e) => { if (!$("#search").hidden && !e.target.closest("#search,#searchBtn")) closeSearch(); });

/* ---------- a project ---------- */
async function fetchProject(key) {   // a project's data and its round's gate view, read before anything on screen changes
  const r = await getJSON(`/api/p/${enc(key)}/data`);
  if (!r.ok || !r.data) return { error: r.data && r.data.error ? r.data.error : t("noServer") };
  let gv = null;
  if (r.data.current) { const g = await getJSON(`/api/p/${enc(key)}/gate/${enc(r.data.current)}?lang=${pickLang(r.data.lang)}`); if (g.ok && g.data) gv = g.data; }
  return { data: r.data, gv };
}
function applyProject(key, x) {
  D = x.data; PKEY = key;
  ROUND = D.rounds[D.rounds.length - 1] || { id: "notes", gate: "", data: { decisions: [], least_sure: [], decided: [], delegated: [], assets: [], appendix: [], listen: [] } };
  KEY = `desk:${PKEY}:${ROUND.id}`;   // the draft goes with the folder (its key), never with a folder of the same name
  FB = store.get(KEY) || { decisions: {}, items: {}, general: "" };
  FB.items = FB.items || {}; FB.decisions = FB.decisions || {};
  setLang(pickLang(D.lang));
  GV = x.gv;
}
async function loadProject(key) {
  const x = await fetchProject(key);
  if (x.error) { $("#stage").innerHTML = `<p class="void module">${esc(x.error)}</p>`; return false; }
  applyProject(key, x);
  return true;
}
let RELOADING = false;
async function reloadProject(follow) {   // the same film read again (a submission went, the agent sent a page): what is on screen stays until the new data is in
  const key = PKEY; if (!key || RELOADING) return;
  RELOADING = true;
  let x; try { x = await fetchProject(key); } finally { RELOADING = false; }
  if (PKEY !== key) return;   // the person went elsewhere meanwhile
  if (x.error) { toast(x.error); return; }
  const at = CUT && !follow ? CUT.time() : null, y = window.scrollY, s = $("#stage").scrollTop;
  leaveProject(); applyProject(key, x);
  const r = follow ? { view: "project", key } : Object.assign(parse(), { key });   // follow: a new page opens on its own stop's module
  MOD = r.mod || defaultMod(); SUB = r.sub || ""; DOC = r.doc || DOC; GATE = r.gate || "";
  crumbs([{ text: t("m_space"), href: "#/" }, { text: D.project.title }]);
  renderFlow(); renderRail(); renderColumn(); renderModule(); updateComposer();
  liveTimer = setInterval(pollLive, 4000);
  if (at != null && CUT) CUT.seekTo(at);   // the playhead where it was
  $("#stage").scrollTop = s; window.scrollTo(0, y);
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
  if (filmDelivered()) return "ship";
  if (filmPath() || cutShots().length) return "cut";
  return "idea";
}
async function showProject(r) {
  clearTimeout(homeTimer);
  const switching = PKEY !== r.key || !D, was = MOD;
  if (switching) { leaveProject(); D = null; renderShellLoading(); if (!(await loadProject(r.key))) return; }
  MOD = r.mod || defaultMod(); SUB = r.sub || ""; DOC = r.doc || DOC; GATE = r.gate || "";
  crumbs([{ text: t("m_space"), href: "#/" }, { text: D.project.title }]);
  renderFlow(); renderRail();
  if (switching) { renderColumn(); clearInterval(liveTimer); pollLive(); liveTimer = setInterval(pollLive, 4000); }
  else if (was !== MOD) renderColumn();   // the column says what this module is for: the stop's decisions on its own module, one line elsewhere
  renderModule();
  updateComposer();
}
function renderShellLoading() { $("#stage").innerHTML = `<p class="loading">${esc(t("loading"))}</p>`; }

/* ---------- the right column: what waits for you, this round, one note box ---------- */
function renderColumn() {
  const live = $("#colHead .state"); const on = live && live.classList.contains("agent");
  const dl = filmDelivered(), day = dl ? shortDate(stopDate(stations().filter((x) => x.id === "deliver"))) : "";
  const roundName = dl ? (day ? t("f_delivered_d", { d: day }) : t("f_delivered")) : ROUND.id === "notes" ? t("col_notes") : gateName(ROUND.id);   // the stop, not its page
  // the agent's being there is said when it waits (a desk wait); its absence is not news, so nothing is shown then
  $("#colHead").innerHTML = `<b>${esc(t(dl ? "col_film" : "col_round"))}</b><span class="who">${esc(roundName)}</span><span class="state${on ? " agent" : ""}" title="${esc(t("live_on_tip"))}"${on ? "" : " hidden"}><i aria-hidden="true"></i><span>${esc(t("live_on"))}</span></span>`;
  const g = GV && GV.current && roundOpen() ? GV : null;   // the cards while this round's stop is open (not passed or skipped)
  const home = GATE_MOD[gateBase(ROUND.id)] || "cut", here = !g || MOD === home, n = (ROUND.data.decisions || []).length;
  const page = ROUND.page ? ` <a class="meta" href="${esc(src(ROUND.page))}" target="_blank" rel="noopener" title="${esc(ROUND.page)}">${esc(t("static_page"))} ↗</a>` : "";
  const decs = g && !here ? `<section><a class="away" href="${projHash(PKEY, home)}">${esc(n ? t("away_decide", { s: gateName(ROUND.id), n }) : t("away_look", { s: gateName(ROUND.id) }))} →</a></section>`   // another module: one line to the stop's own
    : g && n ? `<section class="c-decs"><h3 class="blk-h"><b>${esc(t("c_decide"))}</b><span class="n mono">${n}</span><span class="tag">${esc(t("c_rec"))}</span></h3>${g.summary ? `<p class="round-h">${esc(g.summary)}${page}</p>` : ""}<div class="c-cards">${g.cards}</div></section>`
    : g && g.summary ? `<section><p class="round-h">${esc(g.summary)}${page}</p></section>`
    : `<section><p class="next quiet-line">${esc(t(filmDelivered() ? "col_done" : "round_quiet"))}</p></section>`;   // nothing to decide: one line ("最近定下的" is the ledger's)
  const sent = FB.sent ? t("sent_n", { n: FB.sent.n, d: FB.sent.d, at: FB.sent.at }) : FB.submittedAt ? t("submitted", { at: FB.submittedAt }) : "";   // what went, and that it does not go again
  $("#colBody").innerHTML = `${sent ? `<p class="notice">${esc(sent)}</p>` : ""}${decs}<section id="cMarks"></section><section id="cMine"></section><section id="colNext"></section>`;
  if (COLCTL) { COLCTL.destroy(); COLCTL = null; }
  const cards = $(".c-cards", $("#colBody"));
  if (cards) COLCTL = OVH.mount(cards, { initial: FB.decisions, onPick: pick, advance: true });
  renderMarks(); renderMine(); renderNext(); renderRound(); syncPhoneDec();
  if (!$("#composer").dataset.ready) buildComposer();
  $("#composer").hidden = false;
}
function syncPhoneDec() {   // a phone lays the cut out picture, timeline, then the column: a bar above the picture goes to the decisions
  const pd = $("#phoneDec"); if (!pd || !D) return;
  const g = GV && GV.current && roundOpen() ? GV : null, n = (ROUND.data.decisions || []).length, home = GATE_MOD[gateBase(ROUND.id)] || "cut";
  pd.hidden = !(g && n && MOD === home);
  pd.textContent = pd.hidden ? "" : `${t("away_decide", { s: gateName(ROUND.id), n })} ↓`;
}
document.addEventListener("click", (e) => {
  if (!e.target.closest("#phoneDec")) return;
  e.preventDefault();
  const d = $(".c-decs", $("#colBody")); if (d) d.scrollIntoView({ block: "start", behavior: "smooth" });
});
function pick(dec, val) {
  FB.decisions[dec] = val; save();
  $$(`.g-dec[data-dec="${CSS.escape(dec)}"] input[type=radio]`).forEach((x) => { x.checked = x.value === val; });   // its twin in the module
  const V = typeof MODVIEW !== "undefined" && MODVIEW[MOD];
  if (V && V.sync) V.sync(dec, val);   // a module that draws the decision itself (立意's cards)
}
function roundOpen() {   // this round's stop is not settled yet (the server reads it from bin/vh status: not passed, not skipped)
  if (!D || !D.current || ROUND.id !== D.current) return false;
  if (typeof D.round_open === "boolean") return D.round_open;
  return !["done", "skipped"].includes(roundState());
}
function roundState() { const s = stations().find((x) => (x.pages || []).includes(ROUND.id)); return s ? s.state : ""; }
function gateMarks() { return (GV && GV.current && roundOpen() && GV.marks) || []; }
function recentHtml() {   // what was decided last, when nothing is open: REVIEW.md's "定了" lines and what the agent decided for you
  const hist = D.history.slice().reverse().flatMap((h) => h.notes.filter((n) => /^(定了|Decided)/.test(n.k) && n.v && !/^[—–-]?$/.test(n.v.trim())).map((n) => ({ k: h.title, v: n.v }))).slice(0, 3);
  const agent = D.agent_decided.filter((a) => !a.superseded).slice(-3).reverse().map((a) => ({ k: t("agent_decided_k", { x: a.topic || "" }), v: a.what }));
  const R = hist.concat(agent);
  return R.length ? `<h3 class="blk-h" style="margin-top:14px"><b>${esc(t("recent"))}</b></h3><ul class="note-list recent">${R.map((x) => `<li><span class="mono tc">·</span><span class="fold" tabindex="0"><b>${esc(cut(x.k, 40))}</b> ${esc(x.v)}</span></li>`).join("")}</ul>` : "";   // two lines each; a click opens one
}
function renderMarks() {   // the round's places in the film: on the round's own module (elsewhere its one line goes there)
  const home = GATE_MOD[gateBase(ROUND.id)] || "cut", M = MOD === home ? gateMarks() : [], least = M.filter((m) => m.kind === "least"), listen = M.filter((m) => m.kind === "listen");
  const li = (m) => `<li tabindex="0" data-goto="${esc(m.target)}"${m.t != null ? ` data-t="${+(m.t)}"` : ""}${m.t1 != null ? ` data-t1="${+(m.t1)}"` : ""}><span class="mono tc">${m.t != null ? esc(fmt(m.t) + (m.t1 != null ? "–" + fmt(m.t1) : "")) : ""}</span><span>${m.id && !/^\s*\d/.test(m.id) ? `<b>${esc(shotName(m.id))}</b> ` : ""}${esc(m.note)}</span></li>`;
  // folded to their headings and counts: the decisions above take the room (their pros and costs whole); a click opens one, and it stays open
  const fold = (k, title, list) => `<details class="cfold" data-k="${k}"${COLOPEN[k] ? " open" : ""}><summary class="blk-h"><b>${esc(title)}</b><span class="n mono">${list.length}</span></summary><ul class="note-list marks">${list.map(li).join("")}</ul></details>`;
  $("#cMarks").innerHTML = (least.length ? fold("least", t("c_least"), least) : "") + (listen.length ? fold("listen", t("c_listen"), listen) : "");
  $$("#cMarks details").forEach((d) => d.addEventListener("toggle", () => { COLOPEN[d.dataset.k] = d.open; }));
}
const COLOPEN = { least: false, listen: false };
function myItems() { return Object.entries(FB.items).filter(([, v]) => v && v.status); }
function renderMine() {
  const items = myItems().sort((a, b) => (a[1].t != null ? a[1].t : 1e9) - (b[1].t != null ? b[1].t : 1e9));
  const st = { ok: t("st_ok"), change: t("st_change"), ask: t("st_ask") };
  const row = ([k, v]) => `<li tabindex="0" data-goto="${esc(k)}"${v.t != null ? ` data-t="${+(v.t)}"` : ""}${v.t1 != null ? ` data-t1="${+(v.t1)}"` : ""}><span class="mono tc">${v.t != null ? esc(fmt(v.t) + (v.t1 != null ? "–" + fmt(v.t1) : "")) : ""}</span><span><b>${esc(cut(v.label || k, 40))}</b> ${esc(v.text || st[v.status] || "")}</span><button type="button" class="x" data-del="${esc(k)}" title="${esc(t("del"))}" aria-label="${esc(t("del"))} ${esc(v.label || k)}">×</button></li>`;
  const gen = FB.general ? `<li class="general"><span class="mono tc">·</span><span><b>${esc(t("c_whole_note"))}</b> ${esc(FB.general)}</span><button type="button" class="x" data-del="#general" aria-label="${esc(t("del"))}">×</button></li>` : "";
  const none = !items.length && !gen;   // none yet: the heading and how to start, on one line
  $("#cMine").innerHTML = `<h3 class="blk-h"><b>${esc(t("c_mine"))}</b><span class="n mono">${items.length + (FB.general ? 1 : 0)}</span>${none ? `<span class="hint-inline">${esc(t(MOD === "cut" ? "c_mine_how" : "c_mine_how_m"))}</span>` : ""}</h3>`
    + (none ? "" : `<ul class="note-list mine">${items.map(row).join("")}${gen}</ul>`);
}
function renderNext() {   // what happens next, in a line: who, and what (status's words in this page's language; its commands only in a tooltip)
  const st = (D && D.status) || {}, ns = st.next_step || {}, run = ((st.activity || {}).running || []);
  const who = ns.who === "person" ? "person" : ns.who === "nobody" ? "nobody" : "agent";
  const b = ((st.assets || {}).budget) || {}, money = (o) => Object.entries(o || {}).map(([c, v]) => `${v} ${c}`).join(", ");
  const spent = money(b.spent), limit = b.unlimited ? "∞" : money(b.limit);
  const said = statusWords(ns.do || ""), cmds = [shortPath(ns.do || "")].concat((ns.commands || []).map(shortPath)).filter(Boolean).join("\n");   // the tooltip: status's own line and its commands
  const wait = stations().find((s) => s.state === "waiting_person"), words = who === "person" ? (wait ? t("next_you", { s: gateName(wait.id) }) : t("next_you0")) : t("next_agent");
  const said_here = who === "person" && $(".c-cards, .away", $("#colBody"));   // the cards above (or the line to them) and 交给 agent already say the person's next step
  const next = ns.do && who !== "nobody" && !said_here ? `<h3 class="blk-h"><b>${esc(t("c_next"))}</b></h3><p class="next" title="${esc([said.text].concat(cmds ? [cmds] : []).join("\n"))}"><span class="who ${who}">${esc(t("who_" + who))}</span><span>${esc(words)}</span></p>` : "";
  $("#colNext").innerHTML = (run.length ? `<h3 class="blk-h"><b>${esc(t("c_running"))}</b></h3><ul class="note-list">${run.map((x) => `<li title="${esc(shortPath(x.cmd || x))}"><span class="mono tc" style="color:var(--agent)">●</span><span>${esc(cmdWords(x.cmd || x))}</span></li>`).join("")}</ul>` : "")
    + next + (spent || (limit && limit !== "") ? `<h3 class="blk-h"><b>${esc(t("c_spend"))}</b></h3><p class="next">${esc([spent ? t("c_spent", { s: spent }) : "", limit ? t("c_of", { l: limit }) : ""].filter(Boolean).join(" · "))}</p>` : "");
}
function roundCounts() {   // {n, d, r}: notes to send, decisions the person picked and not sent yet, decisions left to the recommendation
  const ts = toSend(ROUND.data.decisions, FB.decisions, FB.sentDec, roundOpen());
  const d = Object.keys(ts.decisions).filter((k) => !ts.defaulted.includes(k)).length;
  return { n: myItems().length + (FB.general ? 1 : 0), d, r: ts.defaulted.length };
}
function renderRound() {   // what the next submission would send, said plainly ("还没写意见 · 2 件按推荐"); nothing to send: the button rests
  const { n, d, r } = roundCounts();
  const words = [n ? t("rs_notes", { n }) : t("rs_none")].concat(d ? [t("rs_picked", { d })] : [], r ? [t("rs_rec", { r })] : []).join(" · ");
  const idle = !n && !d && !r;
  $("#colRound").hidden = false;
  $("#colRound").innerHTML = `<span>${esc(words)}</span><button type="button" class="btn btn-primary" id="openConfirm"${idle ? " disabled" : ""}>${esc(t("submit_round"))}</button>`;
  $("#openConfirm").addEventListener("click", openConfirm);
  requestAnimationFrame(fadeMore);
}
function fadeMore() { const b = $("#colBody"); if (b) b.classList.toggle("more", b.scrollHeight - b.scrollTop - b.clientHeight > 6); }   // more below: say so
$("#colBody").addEventListener("scroll", fadeMore); window.addEventListener("resize", fadeMore);
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
  // one row: what the note is on, and the button that notes it; the box under it (the agent's side of the box waits, hidden, until one is connected)
  c.innerHTML = `<div class="crow send"><span>${esc(t("at"))}</span><span class="chip" id="scope"></span><button type="button" class="xs" id="toWhole" hidden>${esc(t("to_whole"))}</button><span class="meta" id="sayHint"></span><span class="kbd" aria-hidden="true">${esc(t("note_keys"))}</span><button type="button" class="btn" id="sayAdd">${esc(t("note_add"))}</button></div>
    <div class="crow" hidden><span class="modes" role="group"><button type="button" disabled title="${esc(t("say_agent_tip"))}">${esc(t("say_agent"))}</button><button type="button" aria-pressed="true">${esc(t("as_note"))}</button></span></div>
    <textarea id="say" rows="2" maxlength="4000"></textarea>`;
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
  $("#say").placeholder = t("c_ph", { x: /[\x21-\x7e]$/.test(x) && LANG === "zh" ? x + " " : x });
}
function setScope(s) {
  SCOPE = s; updateComposer();
  $$("#stage .scoped").forEach((el) => el.classList.remove("scoped"));
  if (s && s.el) s.el.classList.add("scoped");
}
function addNote() {
  const ta = $("#say"), text = ta.value.trim();
  if (!text) { ta.focus(); return; }
  if (!SCOPE || !SCOPE.target) {   // the whole module, or a place with no target of its own: the round's overall words, named
    const pre = SCOPE ? `〔${SCOPE.label}〕` : MOD && MOD !== "cut" ? `〔${t("m_" + MOD)}〕` : "";
    FB.general = (FB.general ? FB.general + "\n" : "") + pre + text;
  } else {
    const cur = FB.items[SCOPE.target];
    FB.items[SCOPE.target] = Object.assign({}, cur || {}, { status: cur && cur.status === "ask" ? "ask" : "change", label: SCOPE.label, text: cur && cur.text ? cur.text + "\n" + text : text },
      SCOPE.t != null ? { t: SCOPE.t } : {}, SCOPE.t1 != null ? { t1: SCOPE.t1 } : {});
  }
  ta.value = ""; save(); toast(t("noted", { x: scopeLabel() }));
  const li = $(`#cMine li[data-goto="${CSS.escape(SCOPE && SCOPE.target ? SCOPE.target : "")}"]`) || $("#cMine li.general");   // the note in the column, in view and lit for a moment
  if (li) { li.scrollIntoView({ block: "nearest", behavior: "smooth" }); li.classList.add("just"); setTimeout(() => li.classList.remove("just"), 1600); }
  ta.blur();   // noted: the next key (N, ← →, Space) goes to the film, not into the box
}
$("#stage").addEventListener("error", (e) => { if (e.target.tagName === "IMG") e.target.hidden = true; }, true);   // a picture not there: the letter under it shows
const unfold = (e) => { const f = e.target.closest(".fold"); if (f && (e.type === "click" || e.key === "Enter")) f.classList.toggle("open"); };   // a long line folded to two: open it
document.addEventListener("click", unfold); document.addEventListener("keydown", unfold);
$("#stage").addEventListener("click", (e) => {   // a place in a module: the note box writes against it
  if (MOD === "cut" || e.target.closest("button,a,input,textarea,select,label,.fb,summary,video,audio")) return;
  const el = e.target.closest("[data-mark],[data-target],[data-scope]");
  if (!el || !$("#stage").contains(el)) return;
  const target = el.dataset.mark || el.dataset.target;
  if (!target) { setScope({ label: el.dataset.scope, el }); return; }   // no target of its own: a note on it goes into the overall words
  if (!/^[a-z]+:/.test(target) || target.startsWith("dec:")) return;
  const fb = $(".fb", el), kind = target.split(":")[0], x = target.slice(kind.length + 1);
  let label = el.dataset.label || (fb ? fb.dataset.label : "");
  if (!label) label = kind === "least" ? t("l_least", { x: x || cut(el.textContent.trim(), 24) }) : kind === "shot" ? t("l_shot", { x }) : kind === "deleg" ? t("l_deleg", { x: cut(el.textContent.trim(), 28) }) : kind === "atime" ? t("sound_label", { t: fmt(+x) }) : target;
  if (!targetOk(target)) { setScope({ label: fitLabel(label), el }); return; }   // a target feedback.py would refuse: the overall words, named
  setScope({ target, label: fitLabel(label), el, t: el.dataset.t != null ? +el.dataset.t : null, t1: el.dataset.t1 != null ? +el.dataset.t1 : null });
});

/* submitting: everything this round holds, then one button (the desk's channel; bin/vh desk wait wakes on it) */
function payload() {
  // a stop already settled is not decided again by a later note; a decision sent before goes again only when picked differently
  const { decisions, defaulted } = toSend(ROUND.data.decisions, FB.decisions, FB.sentDec, roundOpen());
  const all = myItems().map(([k, v]) => Object.assign({ target: k, status: v.status, label: fitLabel(v.label || k), text: v.text || "" },
    v.suggest && v.suggest !== v.orig ? { suggest: v.suggest } : {}, v.orig && k.startsWith("cap:") ? { orig: v.orig } : {}, v.t != null ? { t: v.t } : {}, v.t1 != null ? { t1: v.t1 } : {}));
  // an item feedback.py would refuse costs only itself, said before sending, never the round (its limits: tools/desk/feedback.py)
  const fits = (i) => targetOk(i.target) && cps(i.text).length <= 4000 && cps(i.suggest || "").length <= 2000 && cps(i.orig || "").length <= 2000;
  const items = all.filter(fits), dropped = all.filter((i) => !fits(i));
  const general = cps([FB.general || "", ($("#cGeneral") || {}).value || ""].map((x) => x.trim()).filter(Boolean).join("\n")).slice(0, 8000).join("");
  const p = { round: ROUND.id, lang: LANG, decisions, defaulted, items, general, pid: D.pid };
  Object.defineProperty(p, "dropped", { value: dropped, enumerable: false });   // shown in the sheet, not sent
  return p;
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
    return `<li><span class="q">${i + 1} · ${esc(d.question || d.id)}</span><span class="v ${mine ? "mine" : "rec"}">${esc(o.label ? cut(String(o.label).replace(/\*\*|`/g, ""), 60) : v || "–")}${mine ? "" : esc(t("by_rec"))}</span></li>`; }).join("");   // an option by its words; the code only in the reply for the chat
  const least = gateMarks().filter((m) => m.kind === "least");   // what "改完下面两处" points at, here in the sheet
  const leastHtml = least.length ? `<h4>${esc(t("c_least"))}</h4>${least.map((m) => `<li><span class="q">${esc(m.t != null ? fmt(m.t) + (m.t1 != null ? "–" + fmt(m.t1) : "") : "")}${m.id && !/^\s*\d/.test(m.id) ? " " + esc(shotName(m.id)) : ""}</span><span>${esc(m.note)}</span></li>`).join("")}` : "";
  const items = p.items.map((i) => `<li><span class="q">${esc(i.label)} · ${esc(st[i.status])}</span>${i.text ? `<span>${esc(i.text)}</span>` : ""}${i.suggest ? `<span class="serif">→ ${esc(i.suggest)}</span>` : ""}</li>`).join("")
    + (p.dropped.length ? `<h4 class="dropped">${esc(t("d_dropped", { n: p.dropped.length }))}</h4>${p.dropped.map((i) => `<li class="dropped"><span class="q">${esc(cut(i.label, 60))}</span><span>${esc(cut(i.text, 120))}</span></li>`).join("")}` : "");
  const c = $("#confirm");
  c.innerHTML = `<div class="c-body"><h3>${esc(t("d_title"))}</h3><ul class="sum">${decs ? `<h4>${esc(t("d_decisions"))}</h4>${decs}` : ""}${leastHtml}<h4>${esc(t("d_items"))}</h4>${items || `<li class="meta">${esc(t("d_none"))}</li>`}${FB.general ? `<li><span class="q">${esc(t("overall"))}</span><span>${esc(FB.general)}</span></li>` : ""}</ul>
      <label class="meta" for="cGeneral">${esc(t("general"))}</label><textarea id="cGeneral" rows="2" maxlength="4000" placeholder="${esc(t("general_ph"))}"></textarea>
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
    const box = $("#cGeneral"); if (box) box.value = "";
    FB = afterSent(FB, p, new Date().toLocaleString()); store.set(KEY, FB);   // what went leaves the draft: it is not sent twice
    toast(j.listening ? t("sent_live") : t("sent", { f: j.saved }));
    $("#submitHint").textContent = t(j.listening ? "hint_live" : "hint_idle", { f: j.saved });
    renderMine(); renderRound();
    setTimeout(async () => { $("#confirm").hidden = true; await reloadProject(); }, 1400);
    return;
  }
  if (r && r.status === 409) { toast(t("moved")); $("#submitHint").textContent = t("moved"); return; }   // the address names another folder now
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
  if (!PKEY || RELOADING) return;
  const r = await getJSON(`/api/p/${enc(PKEY)}/status`);
  const on = !!(r.ok && r.data && r.data.listening), el = $("#colHead .state");
  if (el) { el.classList.toggle("agent", on); el.hidden = !on; }
  if (r.ok && r.data && D && r.data.round !== undefined && r.data.round !== (D.current || null) && r.data.key === PKEY) {   // the agent sent a new page
    toast(t("new_round", { g: r.data.round || "" }));
    await reloadProject(true);
  }
}

/* ---------- the modules ---------- */
function moduleHead(kick, title, sub) {
  return `<div class="mh"><span class="kick">${esc(kick)}</span>${title ? `<h1>${esc(title)}</h1>` : ""}${sub ? `<p>${esc(sub)}</p>` : ""}</div>`;
}
function renderModule() {
  if (PARTCTL) { PARTCTL.destroy(); PARTCTL = null; if (COLCTL && COLCTL.own) COLCTL.own(); }
  const bench = MOD === "cut" && !(GATE && GATE !== D.current);   // the cut's workbench; an earlier page of its stop is shown as a page
  if (CUT && !bench) { CUT.destroy(); CUT = null; }
  if (SCOPE && SCOPE.el) setScope(null); else if (SCOPE && !bench) setScope(null);
  const area = $("#stage");
  area.classList.toggle("is-cut", bench); $("#app").classList.toggle("is-cut", bench);   // narrow: the picture, then what to decide, then the lists
  if (bench) { if (CUT && !GATE) { CUT.refresh(); return; } if (CUT) CUT.destroy(); CUT = CutModule(area); return; }
  const cur = SUB && (SUBS[MOD] || []).includes(SUB) ? SUB : (SUBS[MOD] || [""])[0];
  const V = typeof MODVIEW !== "undefined" && MODVIEW[MOD], page0 = stopPage(MOD);
  if (V && (!SUBS[MOD] || cur === SUBS[MOD][0]) && (!page0 || page0 === D.current)) {   // a module laid out as the prototype draws it (modules.js)
    area.innerHTML = `<section class="module m2" data-mod="${MOD}">${V.main()}</section>`;
    if (page0) {   // the rest of the stop's page: after the module, above its bar
      const bar = $(".mbar", area), gp = '<div id="gatePart" class="after"></div>';
      if (bar) bar.insertAdjacentHTML("beforebegin", gp); else $(".m2", area).insertAdjacentHTML("beforeend", gp);
      loadGatePart(page0, V);
    } else { const link = pastPageLink(MOD); if (link) $(".mh2", area).insertAdjacentHTML("beforeend", link); }
    $$("[data-mark]", area).forEach(markHost);
    if (V.wire) V.wire();
    fitHeads(area);
    area.scrollTop = 0;
    return;
  }
  const fn = { idea: mIdea, outline: () => ({ outline: vOutline, script: vScript, facts: vFacts }[cur] || vOutline)(), board: mBoard, sound: vSound,
    ship: () => (cur === "versions" ? vVersions() : vCheck()), assets: vAssets,
    ledger: () => ({ decisions: vLedger, history: vHistory, docs: vDocs }[cur] || vLedger)(), cut: () => "" }[MOD] || mIdea;
  const page = stopPage(MOD);
  area.innerHTML = `<section class="module" data-mod="${MOD}">${moduleHead(kickOf(MOD), "", "")}${page ? '<div id="gatePart"></div>' : ""}${subtabs(MOD)}<div id="modBody">${fn()}</div></section>`;
  if (page) loadGatePart(page);
  else { const link = pastPageLink(MOD); if (link) $(".mh", area).insertAdjacentHTML("beforeend", link); }
  $$("[data-mark]", area).forEach(markHost);
  ({ outline: cur === "script" ? wireScript : wireOutline, board: wireBoard, sound: wireSound }[MOD] || (() => {}))();
  area.scrollTop = 0;
}
function stopPage(mod) {   // the stop's page this module shows on top: the one asked for, else this round's while it is open here
  if (GATE && gateMod(GATE) === mod) return GATE;
  return D.current && roundOpen() && gateMod(D.current) === mod ? D.current : null;
}
function pastPageLink(mod) {
  const f = FLOW.find((x) => x.mod === mod); if (!f) return "";
  const s = stations().filter((x) => f.st.includes(x.id) && x.pages && x.pages.length && /^\d$/.test(x.id) && GATE_MOD[x.id] === mod).pop();
  if (!s) return "";
  const pg = s.pages[s.pages.length - 1];
  return `<a class="meta" style="margin-left:auto" href="${projHash(PKEY, "gate/" + enc(pg))}">${esc(t("page_of", { g: gateName(pg, true) }))}</a>`;
}
async function loadGatePart(gid, V) {   // V: the module draws the page's picture itself; the rest of the page comes after it
  const r = await getJSON(`/api/p/${enc(PKEY)}/gate/${enc(gid)}?lang=${LANG}`);
  const host = $("#gatePart"); if (!host) return;
  if (!r.ok || !r.data) { host.innerHTML = `<p class="void">${esc((r.data && r.data.error) || "")}</p>`; return; }
  const g = r.data, past = !g.current;
  host.innerHTML = (past ? `<p class="notice">${esc(t("past", { g: gateName(g.gate, true) }))}${D.current ? ` <a href="${projHash(PKEY, gateMod(D.current))}">${esc(t("to_round"))}</a>` : ""}</p>` : "") + g.html;
  const root = $(".gate", host);
  if (V) {   // its heading is the module's; a missing file's warning stays
    const head = $(".g-head", root);
    if (head) { $$(".g-warn, .g-gone", head).forEach((w) => root.prepend(w)); head.remove(); }
    if (V.drawn) V.drawn(root);
    root.insertAdjacentHTML("afterbegin", `<h2 class="pn-h"><span>${esc(t("page_rest", { g: gateName(g.gate, true) }))}</span></h2>`);
  }
  // the decisions live in the right column; a decision drawn with pictures stays here as the picture, its pick kept in step with the column's
  $$(".g-side, .g-act, .g-decs", root).forEach((x) => x.remove());
  $$(".g-dec:not(.wide)", root).forEach((x) => x.remove());
  const body = $(".g-body", root); if (body) body.classList.remove("has-side");
  if (!past) $$(".g-marks", root).forEach((x) => { const s = x.closest("section"); if (s) s.remove(); });   // they are in the column
  $$("input[type=radio]", root).forEach((x) => { if (past) x.disabled = true; else x.name = "m-" + x.name; });
  PARTCTL = OVH.mount(root, past ? {} : { initial: FB.decisions, onPick: pick, advance: false });
  if (past) $$(".g-dec", root).forEach((d) => { d.classList.remove("active"); $$("input[type=radio]", d).forEach((x) => { x.checked = false; }); });   // what was picked then is in REVIEW.md, not here
  if (V) { const main = $(".g-main", root); if (main && !main.children.length) main.closest(".g-body").remove(); }   // nothing left of the picture part
  $$("[data-mark]", root).forEach(markHost);
}

/* ✓ / ✎ / ? on an item (the desk's views, moved into the modules) */
function fbCtl(target, label, opt = {}) {
  const v = FB.items[target] || {}, st = v.status || "";
  const lab = opt.labels || [t("fb_ok"), t("fb_change"), t("fb_ask")];
  return `<div class="fb" data-target="${esc(target)}" data-label="${esc(label)}"${opt.suggest != null ? ` data-orig="${esc(opt.suggest)}"` : ""}${opt.t != null ? ` data-t="${+(opt.t)}"` : ""}${opt.labels ? ` data-labels="${esc(JSON.stringify(opt.labels))}"` : ""}${opt.def ? ` data-def="${esc(opt.def)}"` : ""}>
    <span class="seg3"><button type="button" data-st="ok" class="${st === "ok" ? "on" : ""}">${esc(lab[0])}</button><button type="button" data-st="change" class="${st === "change" ? "on" : ""}">${esc(lab[1])}</button><button type="button" data-st="ask" class="${st === "ask" ? "on" : ""}">${esc(lab[2])}</button></span>
    ${st ? "" : `<span class="def">${esc(opt.def || t("fb_def"))}</span>`}
    <div class="fb-more" ${st === "change" || st === "ask" ? "" : "hidden"}>
      <textarea rows="2" data-k="text" maxlength="4000" placeholder="${esc(st === "ask" ? t("ph_ask") : t("ph_change"))}">${esc(v.text || "")}</textarea>
      ${opt.suggest != null && st === "change" ? `<input data-k="suggest" maxlength="2000" placeholder="${esc(t("ph_suggest"))}" value="${esc(v.suggest != null ? v.suggest : opt.suggest)}">` : ""}
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

function fallback(note, file, onlySection) {
  const doc = docOf(file); if (!doc) return "";
  const part = onlySection && doc.sections.some((s) => onlySection.test(s.title)) ? onlySection : null;
  return `<p class="notice">${esc(note)}</p><div class="card" data-mark="doc:${esc(file)}">${docHtml(doc, part)}${fbCtl("doc:" + file, file)}</div>`;
}

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
      ${caps.length ? `<details style="margin-top:8px"><summary class="small">${esc(t("seg_caps", { n: caps.length }))}</summary>${caps.map((x) => `<div class="segcap serif"><span class="id">${esc(x.id)}</span>${esc(x.text)}</div>`).join("")}<div class="meta"><a href="${projHash(PKEY, "outline/script")}">${esc(t("to_script"))}</a></div></details>` : ""}
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
  const secs = (M.sections || []).map((s) => `<div data-t="${+(s.start)}" title="${esc(s.name)}" style="flex:${Math.max(0.05, s.end - s.start).toFixed(2)}">${esc(s.label || s.name)}</div>`).join("");
  const hits = (M.hits || []).map((h) => `<i style="left:${(h.t / dur) * 100}%" title="${esc(h.part)} ${fmt(h.t)}"></i>`).join("");
  const listen = (ROUND.data.listen || []).map((l) => `<button class="btn" type="button" data-seek="${+(l.t)}">▶ ${fmt(l.t)} · ${esc(l.note)}</button>`).join("");
  const tcs = Object.entries(FB.items).filter(([k]) => k.startsWith("atime:")).sort((a, b) => a[1].t - b[1].t);
  return `<p class="sub">${esc(t("sound_sub", { bpm: M.bpm || "–", d: (+dur).toFixed(1) }))}</p>
    <div>${M.audio ? `<audio id="au" src="${esc(src(M.audio))}" controls preload="metadata"></audio>` : `<p class="small muted">${esc(t("no_audio"))}</p>`}
      ${secs ? `<div class="secbar" id="secbar">${secs}<div class="playhead" id="aph"></div></div><div class="hits">${hits}</div>` : ""}
      ${M.audio ? `<div style="display:flex;gap:8px;align-items:center;margin-top:8px;flex-wrap:wrap"><button class="btn" type="button" id="atc">${esc(t("comment_at", { t: "\u0001" })).replace("\u0001", '<span id="atnow">0:00.0</span>')}</button><span class="meta">${esc(t("sec_tip"))}</span></div>` : ""}</div>
    ${listen ? `<div class="sect"><h2>${esc(t("listen"))}</h2><div class="listen">${listen}</div></div>` : ""}
    <div class="sect"><h2>${esc(t("your_sound"))} <span class="n">${tcs.length}</span></h2>
    <div>${tcs.map(([k, v]) => `<div class="card" style="margin-bottom:10px" data-mark="${esc(k)}"><span class="chip" data-seek="${+(v.t)}">${fmt(v.t)}</span>${fbCtl(k, t("sound_label", { t: fmt(v.t) }), { t: v.t })}</div>`).join("") || `<div class="muted small">${esc(t("none_sound"))}</div>`}</div></div>
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
  const row = (f) => `<tr class="${f.dropped ? "dropped" : ""}" id="fact-${esc(f.id.slice(1))}" data-mark="fact:${esc(f.id)}"><td><b>${esc(f.id)}</b><div class="meta">${esc(f.kind)}</div></td>
      <td>${esc(f.claim)}${f.dropped ? `<div class="meta">${esc(t("dropped"))}</div>` : ""}</td><td class="serif">${esc(f.onscreen)}</td><td class="small muted">${esc(f.source)}</td>
      <td style="min-width:230px">${f.dropped || !f.id ? "" : fbCtl("fact:" + f.id, t("l_fact", { x: f.id }), { labels: [t("fact_ok"), t("fact_bad"), t("fact_unsure")], def: t("fact_def") })}</td></tr>`;
  const kinds = [];
  D.facts.forEach((f) => { const k = f.kind || t("fact_other"); let g = kinds.find((x) => x.k === k); if (!g) kinds.push((g = { k, list: [] })); g.list.push(f); });
  const head = `<thead><tr><th>${esc(t("th_id"))}</th><th>${esc(t("th_claim"))}</th><th>${esc(t("th_screen"))}</th><th>${esc(t("th_src"))}</th><th>${esc(t("th_you"))}</th></tr></thead>`;
  const shut = D.facts.length > 8;
  return `<p class="sub">${esc(t("facts_sub"))}</p>
    ${D.fact_todo.length ? `<div class="card" style="margin-bottom:16px"><b class="small">${esc(t("todo"))}</b><ul class="small" style="margin:6px 0 0;padding-left:18px">${D.fact_todo.map((x) => `<li>${x.done ? "✓ " : ""}${esc(x.text)}</li>`).join("")}</ul></div>` : ""}
    ${kinds.map((g) => `<details class="fgrp"${shut ? "" : " open"}><summary><b>${esc(g.k)}</b><span class="n">${g.list.length}</span></summary><div style="overflow-x:auto"><table class="t">${head}<tbody>${g.list.map(row).join("")}</tbody></table></div></details>`).join("")}`;
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
function filmPath() {   // the server's pick, only a file that is there: this round's film at the cut's stop, else bin/vh status's, else its proxy
  return (D && D.studio && D.studio.film) || "";
}
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
  const checkMarks = () => findings.map((f, i) => ({ kind: "check", t: +f.t, t1: f.t1 != null ? +f.t1 : null, target: "time:" + (+f.t).toFixed(1), label: f.kind || "", note: shotText(f.message || ""), sev: f.severity, i }));
  const allMarks = () => agentMarks().concat(checkMarks(), notesOf()).sort((a, b) => a.t - b.t);

  area.innerHTML = `<div class="cut layout-${layout}" id="cut">
    <a class="phone-dec" id="phoneDec" href="#colBody" hidden></a>
    <aside class="lists" aria-label="${esc(t("m_cut"))}"><div class="ltabs" role="tablist" id="ltabs"></div><div class="lbody" id="lbody"></div></aside>
    <section class="viewer">
      <div class="readout" id="readout"></div>
      <div class="screen" id="screen"><div class="frame" id="frame"></div></div>
      <div class="transport">
        <button type="button" class="p-btn" id="cPrev" title="${esc(t("prev_shot"))}" aria-label="${esc(t("prev_shot"))}">${svg("prev")}</button>
        <button type="button" class="p-btn play" id="cPlay" title="${esc(t("play"))}" aria-label="${esc(t("play"))}">${svg("play")}</button>
        <button type="button" class="p-btn" id="cNext" title="${esc(t("next_shot"))}" aria-label="${esc(t("next_shot"))}">${svg("next")}</button>
        <span class="tc" id="cTc"></span>
        <button type="button" class="btn" id="cN" title="${esc(t("next_tip"))}" hidden></button>
        <button type="button" class="btn toggle" id="cSafe" aria-pressed="false">${esc(t("safe"))}</button>
        ${prevV ? `<button type="button" class="btn toggle" id="cCmp" aria-pressed="false">${esc(t("compare", { v: vnum(prevV.id) }))}</button>` : ""}
        <span class="seg push" role="group" aria-label="${esc(t("layout"))}">${layouts.map((l) => `<button type="button" data-lay="${l}" aria-pressed="${l === layout}">${esc(t("lay_" + l))}</button>`).join("")}</span>
      </div>
    </section>
    <section class="timeline" aria-label="timeline">
      <div class="tl-bar"><span class="legend" id="tlLegend"></span><span class="push"></span>
        <button type="button" class="btn toggle" id="cSnap" aria-pressed="${snapOn}" title="${esc(t("snap_tip"))}">${esc(t("snap"))}</button>
        <span class="zoom"><button type="button" class="p-btn" id="zOut" title="${esc(t("zoom_out"))}" aria-label="${esc(t("zoom_out"))}">−</button><button type="button" class="p-btn" id="zIn" title="${esc(t("zoom_in"))}" aria-label="${esc(t("zoom_in"))}">+</button></span>
        <button type="button" class="btn help" id="tlHelp" aria-expanded="false" aria-controls="tlHelpBox" title="${esc(t("help"))}" aria-label="${esc(t("help"))}">?</button></div>
      <div class="tl-help" id="tlHelpBox" hidden><p>${esc(t("tl_hint"))}</p>${["mouse", "keys"].map((l) => `<p class="h keys-only">${esc(t("h_" + l))}</p><dl class="keys-only">${t(l + "_list").split("；").map((x) => { const [k, ...w] = x.split("："); return `<dt><span class="kbd">${esc(k)}</span></dt><dd>${esc(w.join("："))}</dd>`; }).join("")}</dl>`).join("")}</div>
      <div class="tl-scroll" id="tlScroll"><div class="tl" id="tl"></div></div>
    </section></div>`;
  const root = $("#cut", area), tl = $("#tl", area), scroll = $("#tlScroll", area), screen = $("#screen", area), frame = $("#frame", area);
  let video = null, vb = null;
  if (film) {
    frame.innerHTML = `<video id="cv" src="${esc(src(film))}" preload="metadata" playsinline></video>${prevV ? `<video class="vb" id="cvb" src="${esc(src(prevV.file))}" preload="metadata" playsinline muted hidden></video><div class="wipe-line" id="wl" hidden></div><span class="wipe-l" hidden>${esc(t("ver_now", { v: vnum(curV.id) }))}</span><span class="wipe-r" hidden>${esc(vnum(prevV.id))}</span>` : ""}<div class="safe" hidden></div>`;
    video = $("#cv", frame); vb = $("#cvb", frame);
  } else {
    // no film to play: the storyboard's key frames as the picture, else the contact sheet; the line under it says which, and
    // names the file that was asked for when it is not there (moved, renamed, on another drive)
    const cover = ((D.mods || {}).covers || []).find((c) => c.ratio && c.ratio >= 1) || ((D.mods || {}).covers || [])[0];
    const dl = (stations().find((x) => x.id === "deliver") || {}).delivered, shipped = filmDelivered();
    const gone = ST.film_missing || (shipped ? ((dl && (dl.films || [])[0]) || "out/final.mp4") : ""), pics = shots.some(shotPic) ? "frames" : gone && cover ? "cover" : ST.sheet ? "sheet" : "";   // a film gone: its cover stands for it better than a contact sheet
    const say = pics ? t(gone ? "film_gone_" + pics : "no_film_" + pics) : gone ? t("film_gone0") : t("no_film0");
    const tell = gone && !readOnly() ? ` <button type="button" class="xs" data-tell="${esc(gone)}">${esc(t("tell_where"))}</button>` : "";
    frame.innerHTML = `<img id="cimg" alt=""${pics === "sheet" ? ` src="${esc(src(ST.sheet))}"` : pics === "cover" ? ` src="${esc(src(cover.path))}"` : ""}>${pics ? "" : `<p class="none" title="${esc(gone)}">${esc(say)}${tell}</p>`}<div class="safe" hidden></div>`;
    if (pics) screen.insertAdjacentHTML("beforeend", `<p class="screen-note" title="${esc(gone)}">${esc(say)}${tell}</p>`);
    $$("[data-tell]", screen).forEach((b) => b.addEventListener("click", (e) => { e.stopPropagation(); tellWhere(b.dataset.tell); }));
    if (pics !== "frames") setTimeout(() => ["#cPlay", "#cPrev", "#cNext"].forEach((q) => { const b = $(q, area); if (b) { b.disabled = true; b.title = t("no_play"); } }), 0);   // a cover or a sheet is one picture: nothing to play
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
    const nl = allMarks().filter((m) => m.kind === "listen").length;
    const n = { shots: shots.length, notes: allMarks().filter((m) => m.kind !== "check" && m.kind !== "listen").length + (FB.general ? 1 : 0), checks: findings.length };
    const T2 = [["shots", t("l_shots"), n.shots], ["script", linesAreCaptions ? t("l_captions") : t("l_script"), lines.length || ""]].concat(nl ? [["listen", t("c_listen"), nl]] : [], [["notes", t("l_notes"), n.notes], ["checks", t("l_checks"), n.checks]]);
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
          h += `<button type="button" class="lrow${on ? " sel" : ""}" data-pick="shot:${esc(s.id)}"><span class="lthumb">${pic ? `<img src="${esc(pic)}" alt="" loading="lazy">` : ""}</span><span class="lt"><b>${esc(shotName(s.id))} ${esc(s.label)}</b><span>${esc(fmt(s.t0))}–${esc(fmt(s.t1))}</span>${shotStatus(s) ? `<span>${shotStatus(s)}</span>` : ""}</span></button>`;
        });
      }
    } else if (tab === "script") {
      h = lines.length ? lines.map((l, i) => `<button type="button" class="lrow text${SEL && SEL.kind === "line" && SEL.i === i ? " sel" : ""}" data-pick="line:${i}"><span class="tc">${esc(fmt(l.t0))}</span><span class="tx">${esc(l.text)}</span></button>`).join("") : `<p class="void">${esc(t("no_narr"))}</p>`;
    } else if (tab === "listen") {
      h = allMarks().filter((m) => m.kind === "listen").map((m) => `<button type="button" class="lrow text" data-pick="mark:${esc(m.target)}" data-t="${+(m.t)}"${m.t1 != null ? ` data-t1="${+(m.t1)}"` : ""}><span class="tc">▶ ${esc(fmt(m.t))}</span><span class="tx">${esc(m.note || m.label)}</span></button>`).join("");
    } else if (tab === "notes") {
      const R = allMarks().filter((m) => m.kind !== "check" && m.kind !== "listen");
      const who = (m) => (m.kind === "mine" ? `<em style="color:var(--you)">${esc(t("k_mine"))}</em>` : m.kind === "least" ? `<em style="color:var(--wait)">${esc(t("k_least"))}</em>` : `<em style="color:var(--wait)">${esc(t("k_listen"))}</em>`);
      h = R.map((m) => `<button type="button" class="lrow text" data-pick="mark:${esc(m.target)}" data-t="${+(m.t)}"${m.t1 != null ? ` data-t1="${+(m.t1)}"` : ""}><span class="tc">${esc(fmt(m.t))}</span><span class="tx">${who(m)} ${esc(m.kind === "mine" ? (m.note || m.label) : m.note)}</span></button>`).join("")
        + (FB.general ? `<div class="lrow text"><span class="tc">·</span><span class="tx"><em style="color:var(--you)">${esc(t("c_whole_note"))}</em> ${esc(FB.general)}</span></div>` : "");
      if (!h) h = `<p class="void">${esc(t("c_none_mine"))}</p>`;
    } else {
      if (!chk) h = `<p class="void">${esc(t("no_checks"))}</p>`;
      else {
        h = `<p class="meta" style="margin:4px 6px 8px">${esc(t("verdict"))} <b class="${verdictCls(chk.verdict)}">${esc(chk.verdict || "–")}</b> · ${esc(chk.video || "")}</p>${chk.stale ? `<p class="notice">${esc(t("check_stale"))}</p>` : ""}`;
        h += findings.map((f) => `<button type="button" class="lrow text" data-pick="check:${findings.indexOf(f)}"><span class="tc">${esc(fmt(f.t))}</span><span class="tx"><em style="color:var(--live)">✕ ${esc(f.severity === "fail" ? t("sev_fail") : t("sev_warn"))}</em> ${esc(shotText(f.message || f.kind || ""))}</span></button>`).join("");
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
    // drawn to the loudest peak, so the shape fills the lane (where it is loud, quiet, silent); the level itself is 声音's readout.
    // A film that is all but silent stays a line: the gain is capped at ×20
    const g = 1 / P.reduce((m, p) => Math.max(m, Math.abs(+p[0] || 0), Math.abs(+p[1] || 0)), 0.05);
    let top = "", bot = "";
    P.forEach((p, i) => { const x = ((i / n) * 1000 * sc).toFixed(1), a = Math.max(-1, Math.min(1, (+p[1] || 0) * g)), b2 = Math.max(-1, Math.min(1, (+p[0] || 0) * g)); top += `${i ? "L" : "M"}${x} ${(50 - a * 48).toFixed(1)}`; bot = `L${x} ${(50 - b2 * 48).toFixed(1)}` + bot; });
    return `<svg class="wav" viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true"><path d="${top}${bot}Z"/></svg>`;
  }
  function draw() {
    if (!dur) dur = 1;
    const blk = (cls, a, b, inner, data, title) => `<div class="blk ${cls}" style="left:${pct(a)}%;width:${Math.max(0.15, pct(b) - pct(a))}%"${data ? ` data-pick="${esc(data)}"` : ""}${title ? ` title="${esc(title)}"` : ""}>${inner}</div>`;
    const chapH = chapters.map((c) => blk("chap" + (SEL && (SEL.kind === "chapter" || SEL.kind === "seg" || SEL.kind === "part") && SEL.id === c.id ? " sel" : ""), c.t0, c.t1, esc(c.title), (c.kind === "chapter" ? "chapter:" : c.kind === "seg" ? "seg:" : "part:") + c.id, c.title)).join("");
    const AM = allMarks(), pxPerS = trackW() / dur;
    const shotH = shots.map((s) => { const pic = shotPic(s), st = s.unsure || AM.some((m) => m.kind === "least" && m.t >= s.t0 && m.t < s.t1) ? "flag" : AM.some((m) => m.kind === "mine" && m.t >= s.t0 && m.t < s.t1) ? "note" : "";
      const w = (s.t1 - s.t0) * pxPerS, showPic = pic && w >= 20, showId = w >= 28, showName = w >= 150;   // narrow: its picture and number; narrower: the picture alone, the number in its tooltip
      return blk("shot" + (showId ? "" : " thin") + (SEL && SEL.kind === "shot" && SEL.id === s.id ? " sel" : ""), s.t0, s.t1, `${showPic ? `<img src="${esc(pic)}" alt="" loading="lazy">` : ""}${showId ? `<b class="sid${st ? " " + st : ""}">${esc(shotName(s.id))}</b>` : ""}${showName && s.label ? `<span class="slab">${esc(s.label)}</span>` : ""}`, "shot:" + s.id, `${shotName(s.id)} ${s.label} · ${fmt(s.t0)}–${fmt(s.t1)}`); }).join("");
    // a line of the narration: ▶ plays just that line
    const lineH = lines.map((l, i) => blk("line" + (SEL && SEL.kind === "line" && SEL.i === i ? " sel" : ""), l.t0, l.t1, `<i class="pl" data-pick="play:${i}" role="button" aria-label="${esc(t("play_line"))}">▶</i>${esc(l.text)}`, "line:" + i, `${l.id} · ${l.text}`)).join("");
    const beatH = beats.filter((b) => b.downbeat || pxPerS * (60 / (+T.bpm || 120)) > 10).map((b) => `<i class="bl${b.downbeat ? " down" : ""}" style="left:${pct(+b.t)}%"></i>`).join("");
    const secH = sections.map((s) => `<span class="sec" style="left:${pct(s.start)}%;width:${pct(s.end) - pct(s.start)}%" title="${esc(s.name)}">${esc(s.label || s.name)}</span>`).join("");
    const hitH = hitsL.map((h) => `<i class="hit" style="left:${pct(+h.t)}%" title="${esc((h.part || "") + " " + fmt(h.t))}"></i>`).join("");
    const markH = AM.map((m) => `${m.t1 != null ? `<span class="span-mark ${m.kind}" style="left:${pct(m.t)}%;width:${pct(m.t1) - pct(m.t)}%"></span>` : ""}<button type="button" class="pin ${m.kind === "mine" ? "note" : m.kind}" style="left:${pct(m.t)}%" data-pick="mark:${esc(m.target)}" data-t="${+(m.t)}"${m.t1 != null ? ` data-t1="${+(m.t1)}"` : ""} title="${esc(fmt(m.t) + " · " + (m.note || m.label))}" aria-label="${esc(fmt(m.t) + " " + (m.note || m.label))}"></button>`).join("");
    const diffH = changed.map((s) => `<span class="diff" style="left:${pct(s[0])}%;width:${Math.max(0.3, pct(s[1]) - pct(s[0]))}%">${esc(t("diff_label", { v: vnum(curV.id) }))}</span>`).join("")
      || (curV && curV.changed && curV.changed.whole ? `<span class="diff" style="left:0;width:100%">${esc(vnum(curV.id))} · ${esc(t("whole_render"))}</span>` : "");
    // a group folds from its name only (a button): the row around it is inert, so a click a little off a lane never folds one
    const grp = (k, name) => { const shut = layout !== "review" && closed.has(k); return `<div class="grp${shut ? " closed" : ""}" data-grp="${k}"><button type="button" class="grp-t" aria-expanded="${!shut}" title="${esc(t(shut ? "g_unfold" : "g_fold"))}">${esc(name)}</button>${shut ? `<span class="grp-n">${esc(t("g_folded"))}</span>` : ""}</div>`; };
    tl.style.width = zoom * 100 + "%";
    tl.innerHTML = `<div class="lane ruler-l"><span class="lab"></span><div class="trk" data-ruler>${rulerTicks()}</div></div>`
      + grp("pic", t("g_pic")) + lane("chap", t("ln_chap"), chapH, "pic", t("e_chap")) + lane("shots", t("ln_shots"), shotH, "pic", t("e_shots"))
      + grp("sound", t("g_sound")) + lane("voice extra", t("ln_voice"), lineH, "sound", t("e_voice")) + lane("music extra", t("ln_music"), beatH + secH, "sound", t("e_music"))
      + (hitsL.length ? lane("thin extra", t("ln_hits"), hitH, "sound") : "") + lane("wave extra", t("ln_wave"), wave(), "sound", t("e_wave"))
      + grp("review", t("g_review")) + lane("marks", t("ln_marks"), markH, "review", t("e_marks")) + (diffH ? lane("thin extra", t("ln_diff"), diffH, "review") : "")   // what changed: a lane only when it is on record
      + (layout === "review" && (lines.length || peaks || sections.length || beats.length) ? `<div class="tl-more"><span>${esc(t("tl_more"))}</span><button type="button" data-lay-go="fine">${esc(t("lay_fine"))}</button><button type="button" data-lay-go="sound">${esc(t("lay_sound"))}</button></div>` : "")   // the review layout keeps the picture and the review: say where the sound is
      + `<div class="over" aria-hidden="true"><div class="selr" hidden><span class="cap"></span></div><div class="tl-ph"><span class="cap"></span></div></div><div class="hover-tip" hidden></div>`;
    const kinds = [["mine", "note", "k_mine"], ["least", "least", "k_least"], ["listen", "listen", "k_listen"], ["check", "check", "k_check"]].filter(([k]) => k === "mine" || AM.some((m) => m.kind === k) || (k === "least" && shots.some((s) => s.unsure)));   // a shot flagged unsure carries the ○ too
    $("#tlLegend", area).innerHTML = kinds.map(([, cls, w]) => `<span class="lg"><i class="pin ${cls}" aria-hidden="true"></i>${esc(t(w))}</span>`).join("");
    if (layout !== "review") closed.forEach((g) => { $$(`.lane[data-g="${g}"]`, tl).forEach((x) => { x.hidden = true; }); });
    paintSel(); tick();
  }
  const closed = new Set(store.get("desk:cut-folded") || []);   // a new key: what the old full-width row folded by a stray click opens again
  tl.addEventListener("click", (e) => {
    const p = e.detail === 0 && e.target.closest("[data-pick]");   // Enter or Space on a pin
    if (p) { pickThing(p.dataset.pick, p); return; }
    const lg = e.target.closest("[data-lay-go]"); if (lg) { setLayout(lg.dataset.layGo); return; }
    const g = e.target.closest(".grp-t"); if (!g) return;
    const k = g.parentElement.dataset.grp; if (closed.has(k)) closed.delete(k); else closed.add(k);
    store.set("desk:cut-folded", [...closed]); draw();
    const b = $(`.grp[data-grp="${k}"] .grp-t`, tl); if (b) b.focus({ preventScroll: true });   // the keyboard stays on it
  });

  /* the playhead, the readout, the picture when there is no film */
  let lastShot = null, lastPlaying = null;
  function tick() {
    const x = now(), ph = $(".tl-ph", tl);
    if (playing() !== lastPlaying) { lastPlaying = playing(); $("#cPlay", area).innerHTML = svg(lastPlaying ? "pause" : "play"); }
    if (ph) ph.style.left = pct(x) + "%";
    $("#cTc", area).innerHTML = `${esc(fmt(x))} <i>/ ${esc(fmt(dur))}</i>`;
    placeLabel();
    const s = shotAt(x);
    if (s !== lastShot || !$("#readout", area).innerHTML) {
      lastShot = s;
      const size = video && video.videoWidth ? `${video.videoWidth}×${video.videoHeight}` : (String(specGet("output")).match(/\d{3,5}\s*[x×]\s*\d{3,5}/) || [""])[0].replace(/\s/g, "").replace("x", "×");
      const ver = curV ? vnum(curV.id) : (D.status && D.status.media && D.status.media.version) ? vnum(D.status.media.version) : "";
      const isProxy = film && D.status && D.status.media && film === D.status.media.proxy && film !== D.status.media.film;
      $("#readout", area).innerHTML = (s ? `<span><b>${esc(shotName(s.id))}</b> ${esc(s.label)}</span>${s.reads && s.reads.length ? `<span>${esc(t("reads"))}${COLON()}${esc(s.reads.join(" → "))}</span>` : s.caption ? `<span>${esc(cut(s.caption, 60))}</span>` : ""}` : "<span>·</span>")
        + `<span class="ver">${esc([size, t("fps_n", { n: fps }), ver, isProxy ? t("proxy") : ""].filter(Boolean).join(" · "))}</span>`;
      if (!video) { const img = $("#cimg", frame); const pic = s ? shotPic(s) : ""; if (img && shots.some(shotPic)) { if (pic) { if (img.getAttribute("src") !== pic) img.src = pic; img.hidden = false; } else img.hidden = true; } }
      if (tab === "shots") $$("#lbody .lrow", area).forEach((r) => r.classList.toggle("now", !!s && r.dataset.pick === "shot:" + s.id));
    }
    if (tab === "script") { const li = lines.findIndex((l) => x >= l.t0 && x < l.t1); $$("#lbody .lrow", area).forEach((r, i) => r.classList.toggle("now", i === li)); }
    if (vb && cmp && Math.abs((vb.currentTime || 0) - x) > 0.12 && !(video && !video.paused && !vb.paused)) { try { vb.currentTime = x; } catch (e) { /* not loaded */ } }
  }
  function paintSel() {
    const r = $(".selr", tl); if (!r) return;
    if (!SEL || SEL.t1 == null) {
      if (SEL && SEL.kind === "time") { r.hidden = false; r.style.left = pct(SEL.t) + "%"; r.style.width = "1px"; $(".cap", r).textContent = ""; }   // the second is in the note box's line already
      else r.hidden = true;
      return;
    }
    r.hidden = false; r.style.left = pct(SEL.t) + "%"; r.style.width = Math.max(0.2, pct(SEL.t1) - pct(SEL.t)) + "%";
    $(".cap", r).textContent = `${SEL.label} · ${(SEL.t1 - SEL.t).toFixed(1)} s`;
  }

  /* selecting: a second, a span, a shot, a chapter, a line, a mark; the note box follows */
  function select(s, play, at) {   // at: the second a click was at, inside what it selects (the playhead goes there); else its start
    SEL = s;
    if (s) {
      seek(at != null && !play && at >= s.t && (s.t1 == null || at <= s.t1) ? at : s.t);
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
  function pickThing(p, el, at) {   // at: the second a click on it was at; a mark always takes its own second
    const [kind, ...rest] = p.split(":"), id = rest.join(":");
    if (kind === "shot") { const s = shots.find((x) => x.id === id); if (s) select({ kind: "shot", id: s.id, name: s.label, t: s.t0, t1: s.t1, label: `${s.id} ${s.label}` }, false, at); }
    else if (kind === "chapter" || kind === "seg" || kind === "part") { const c = chapters.find((x) => x.id === id); if (c) select({ kind: c.kind === "part" ? "range" : c.kind, id: c.id, name: c.title, t: c.t0, t1: c.t1, label: c.title }, false, at); }
    else if (kind === "line" || kind === "play") { const i = +id, l = lines[i]; if (l) select({ kind: "line", i, id: l.id, name: t("l_line", { x: l.id }), t: l.t0, t1: l.t1, label: t("l_line", { x: l.id }) }, kind === "play", kind === "play" ? null : at); }
    else if (kind === "check") { const f = findings[+id]; if (f) select({ kind: f.t1 != null ? "range" : "time", t: +f.t, t1: f.t1 != null ? +f.t1 : null, name: `${t("k_check")} ${f.kind || ""}`.trim(), label: fmt(f.t) }); }
    else if (kind === "mark") {
      const m = allMarks().find((x) => x.target === id && (!el || el.dataset.t == null || Math.abs(x.t - +el.dataset.t) < 0.01)) || allMarks().find((x) => x.target === id);
      if (m) select(m.kind === "check" ? { kind: m.t1 != null ? "range" : "time", t: m.t, t1: m.t1, name: m.label, label: fmt(m.t) }
        : { kind: "mark", target: m.target, t: m.t, t1: m.t1, name: m.kind === "mine" ? m.label : m.kind === "listen" ? t("sound_label", { t: fmt(m.t) }) : t("l_least", { x: m.label || fmt(m.t) }), label: m.kind === "mine" ? m.label : fmt(m.t) });
    }
  }
  /* the pointer on the lanes, as in an editor's timeline: a click puts the playhead where you click, and on a shot, a line, a
     chapter or a mark selects it too (the note box names it); a drag scrubs and selects nothing; Shift + drag chooses a span,
     the one gesture that snaps (while 吸附 is on); Shift + click, from the playhead to there; a double click on a shot, a line
     or a chapter plays just that */
  let drag = null, lastClick = null;
  tl.addEventListener("pointerdown", (e) => {
    if (e.button !== 0 || e.target.closest(".grp")) return;
    const trk = e.target.closest(".trk"); if (!trk) return;
    drag = { x0: e.clientX, t0: tAt(e.clientX, e.shiftKey), span: e.shiftKey, pick: e.target.closest("[data-pick]"), moved: false, id: e.pointerId, before: SEL };
    tl.setPointerCapture(e.pointerId);
  });
  tl.addEventListener("pointermove", (e) => {
    const tip = $(".hover-tip", tl);
    if (tip && dur && !drag) hoverTip(e, tip);
    if (!drag) return;
    if (!drag.moved && Math.abs(e.clientX - drag.x0) > 4) { drag.moved = true; if (!drag.span && playing()) stop(); }
    if (!drag.moved) return;
    if (drag.span) {
      const x = tAt(e.clientX, true), a = Math.min(drag.t0, x), b = Math.max(drag.t0, x);
      SEL = { kind: "range", t: a, t1: b, label: `${fmt(a)}–${fmt(b)}` }; paintSel();
    } else seek(tAt(e.clientX, false));   // scrubbing: the picture follows the pointer
  });
  tl.addEventListener("pointerleave", () => { const tip = $(".hover-tip", tl); if (tip) tip.hidden = true; });
  const endDrag = (e) => {
    if (!drag) return;
    const d = drag; drag = null;
    if (e.type === "pointercancel") { SEL = d.before; paintSel(); return; }   // the gesture was taken away: nothing changes by it
    if (d.moved) {
      if (d.span) { const s = SEL; if (s && s.t1 - s.t >= 0.1) select({ kind: "range", t: s.t, t1: s.t1, label: s.label }); else { SEL = d.before; paintSel(); } }
      else if (SEL && SEL.kind === "time") select({ kind: "time", t: now(), label: fmt(now()) });   // a selected second goes along with the playhead
      return;
    }
    const x = tAt(e.clientX, d.span), p = d.pick && d.pick.dataset.pick;
    if (d.span) { const a = Math.min(now(), x), b = Math.max(now(), x); if (b - a >= 0.1) return select({ kind: "range", t: a, t1: b, label: `${fmt(a)}–${fmt(b)}` }); }
    const twice = !!p && !!lastClick && lastClick.p === p && e.timeStamp - lastClick.at < 400;
    lastClick = p ? { p, at: e.timeStamp } : null;
    if (twice && /^(shot|line|chapter|seg|part):/.test(p)) { lastClick = null; const [k, ...r] = p.split(":"); return playPiece(k, r.join(":")); }
    if (p) return pickThing(p, d.pick, x);
    select({ kind: "time", t: x, label: fmt(x) });
  };
  tl.addEventListener("pointerup", endDrag); tl.addEventListener("pointercancel", endDrag);
  tl.addEventListener("dragstart", (e) => e.preventDefault());   // a shot's picture is an image: pressed and moved, the browser would drag it away and end the scrub
  function playPiece(kind, id) {   // a double click: that shot, line or chapter, once, from its start to its end
    if (kind === "line") return pickThing("play:" + id);
    const it = kind === "shot" ? shots.find((x) => x.id === id) : chapters.find((x) => x.id === id);
    if (!it) return;
    pickThing(kind + ":" + id);
    stopAt = it.t1; start();
  }
  function hoverTip(e, tip) {   // over the ruler only, drawn above it: over the lanes it covered what the pointer was about to press
    const ru = e.target.closest(".ruler-l"), r = overRect(); if (!ru || e.clientX < r.left || e.clientX > r.right) { tip.hidden = true; return; }
    const x = tAt(e.clientX, false), s = shotAt(x);
    const fr = document.createElement("span");   // the frame under the pointer, its address set through the style object, never written into markup
    fr.className = "fr";
    if (thumbs) {
      const T3 = thumbs.tiles; let best = T3[0]; for (const q of T3) { if (Math.abs(q.t - x) < Math.abs(best.t - x)) best = q; }
      const sh = thumbs.sheets[best.sheet], W = 176, sc = W / thumbs.tile[0];
      if (sh) Object.assign(fr.style, { backgroundImage: `url(${JSON.stringify(src(sh.file))})`, backgroundSize: `${sh.size[0] * sc}px ${sh.size[1] * sc}px`,
        backgroundPosition: `-${best.x * sc}px -${best.y * sc}px`, height: `${Math.round(thumbs.tile[1] * sc)}px` });
    } else if (s && shotPic(s)) Object.assign(fr.style, { backgroundImage: `url(${JSON.stringify(shotPic(s))})`, backgroundSize: "cover", backgroundPosition: "center" });
    tip.replaceChildren(...(fr.style.backgroundImage ? [fr] : []), document.createTextNode(fmt(x) + (s ? " · " + s.id : "")));
    tip.hidden = false;
    tip.style.left = Math.min(Math.max(e.clientX, 100), window.innerWidth - 100) + "px"; tip.style.top = (ru.getBoundingClientRect().top - 4) + "px";
  }

  /* N: the next place to look at */
  function nextIdx() { const P = allMarks(), x = now() + 0.05, i = P.findIndex((q) => q.t > x); return { P, i: i < 0 ? 0 : i }; }
  function placeLabel() {   // "下一处（2/4）": which place N goes to, of how many; no places, no button
    const b = $("#cN", area); if (!b) return;
    const { P, i } = nextIdx(), lab = P.length ? t("next_place_n", { k: i + 1, n: P.length }) : "";
    b.hidden = !P.length; if (b.textContent !== lab) b.textContent = lab;
  }
  function nextPlace() {
    const { P, i } = nextIdx(), m = P[i];
    if (!m) { flash(t("no_next")); return; }
    if (SEL && SEL.kind === "range") seek(m.t);   // a span you chose stays until Esc or a click: N only takes the playhead there
    else pickThing("mark:" + m.target, { dataset: { t: String(m.t) } });
    flash(t("next_q", { x: `${fmt(m.t)} ${cut(m.note || m.label, 40)}` }));
  }
  function flash(msg) { nextq.textContent = msg; nextq.hidden = false; clearTimeout(nextq._h); nextq._h = setTimeout(() => { nextq.hidden = true; }, 2600); }
  function jumpShot(dir) {   // ← →: the next or previous shot, selected as a click on it would, so the note box names what is on screen
    const p = stepPoint(shots, now(), dir, dur);
    if (p.shot) return pickThing("shot:" + p.shot);
    if (SEL) select({ kind: "time", t: p.t, label: fmt(p.t) }); else seek(p.t, playing());   // past the last shot: that second
  }
  function nudge(by) {   // a second or a frame along; a selected second goes along with it (a span or a shot stays as it is)
    seek(now() + by);
    if (SEL && SEL.kind === "time") select({ kind: "time", t: now(), label: fmt(now()) });
  }
  function setLayout(l) {
    layout = l; store.set("desk:cut-layout", l);
    root.className = "cut layout-" + l;
    $$("[data-lay]", area).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lay === l)));
    if (l === "sound" && (tab === "shots" || tab === "notes")) { tab = allMarks().some((m) => m.kind === "listen") ? "listen" : "script"; renderTabs(); renderList(); }
    setTimeout(() => { fit(); draw(); }, 0);
  }
  $("#cPlay", area).addEventListener("click", toggle);
  $("#cPrev", area).addEventListener("click", () => jumpShot(-1));
  $("#cNext", area).addEventListener("click", () => jumpShot(1));
  $("#cN", area).addEventListener("click", nextPlace);
  $("#tlHelp", area).addEventListener("click", (e) => { const box = $("#tlHelpBox", area), open = box.hidden; box.hidden = !open; e.currentTarget.setAttribute("aria-expanded", String(open)); });
  $("#cSnap", area).addEventListener("click", (e) => { snapOn = !snapOn; store.set("desk:cut-snap", snapOn); e.currentTarget.setAttribute("aria-pressed", String(snapOn)); });
  $("#cSafe", area).addEventListener("click", (e) => { safe = !safe; e.currentTarget.setAttribute("aria-pressed", String(safe)); $(".safe", frame).hidden = !safe; });
  $("#zIn", area).addEventListener("click", () => { zoom = Math.min(16, zoom * 1.6); draw(); centerOn(now()); });
  $("#zOut", area).addEventListener("click", () => { zoom = Math.max(1, zoom / 1.6); draw(); centerOn(now()); });
  $$("[data-lay]", area).forEach((b) => b.addEventListener("click", () => setLayout(b.dataset.lay)));
  scroll.addEventListener("wheel", (e) => {   // ⌘ or Ctrl + wheel, and a trackpad's pinch: zoom, the second under the pointer staying under it
    if (!(e.ctrlKey || e.metaKey) || !dur) return;
    e.preventDefault();
    const at = tAt(e.clientX, false), z = Math.max(1, Math.min(16, zoom * Math.exp(-e.deltaY * 0.003)));
    if (Math.abs(z - zoom) < 1e-3) return;
    zoom = z; draw();
    const o = overRect(); scroll.scrollLeft += o.left + (at / dur) * o.width - e.clientX;
  }, { passive: false });
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
    else if (k === "ArrowLeft" || k === "ArrowRight") { if ((document.activeElement || {}).type === "radio") return; e.preventDefault(); if (e.shiftKey) nudge(k === "ArrowRight" ? 1 : -1); else jumpShot(k === "ArrowRight" ? 1 : -1); }
    else if (k === "," || k === ".") { e.preventDefault(); stop(); nudge((k === "." ? 1 : -1) / fps); }
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

  renderTabs(); renderList(); draw(); fit(); syncPhoneDec();
  if (!thumbs && film) $(".tl-bar span", area).title = t("no_thumbs");
  return {
    refresh() { renderTabs(); renderList(); draw(); },
    time: () => now(),
    seekTo(x) { seek(x); },
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
