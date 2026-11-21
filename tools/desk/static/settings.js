/* Studio's settings page, #/settings[/<section>] (tools/desk/settings_api.py serves it; tools/desk/README.md "设置").
   One page with its sections on the left and one section at a time. What a person changes is kept in this machine's
   settings file (tools/settings.py), so a second window, another port or the terminal see the same; the language and the
   look are also kept in this browser, so the first paint already has them. The top bar's language and look buttons stay:
   they change the same two settings (the clicks are heard here). Loaded before studio.js; it uses studio.js's and
   core.js's names only when it runs. */
const SETTINGS = (() => {
  const W = {
    zh: {
      title: "设置", back: "返回", rail: "设置", rail_tip: "设置（⌘,）",
      s_general: "通用", s_agent: "agent", s_films: "片子的默认", s_machine: "这台电脑", s_about: "关于", s_account: "账号",
      lang: "语言", look: "外观", th_darkfield: "暗场", th_prism: "棱镜", th_bridge: "舰桥",
      where: "片子放在哪", where_how: "想换个地方，让 agent 帮你改，改完重新打开 Studio。", where_none: "还没读到片子放在哪。",
      ag_default: "新对话默认用", ag_not: "还没装", ag_not_how: "在右边的对话里点「装上」。", ag_model: "模型", ag_effort: "思考深度",
      ag_from_default: "Studio 的默认", ag_from_agent: "{a} 自己的默认", ag_from_dsh: "DeepSeek Harness 桌面版里的设置",
      ag_later: "开一次对话以后，这里能改。", ag_none: "这台电脑上还没有装好的 agent。",
      f_lead: "这些是这台电脑给每支片子的默认。片子自己写了的，以片子的为准。",
      f_effort: "默认努力程度", f_review: "在哪看每一站", f_assets: "素材许可", f_sound: "声音库", f_director: "谁拍板哪些事",
      f_subagent: "帮手 agent 用的模型", f_budget: "默认预算", f_unset: "没写", f_unset_effort: "没写：按标准", f_unset_review: "没写：按努力程度",
      f_unset_assets: "没写：严格", f_unset_sound: "没写：用 ~/.ovh/sound", f_unset_budget: "没写：不调收费的接口",
      f_how: "让 agent 帮你改。",
      mirror: "下载镜像", m_auto: "自动", m_cn: "国内镜像", m_off: "官方源",
      m_auto_d: "从官方源下载；安装时官方源连不上，会自己换成国内镜像。", m_cn_d: "以后的下载都走国内镜像。", m_off_d: "只从官方源下载。",
      m_set: "（{d} 设的）", mc_rest: "别的做片子要的都有了。",
      v_quick: "快速", v_standard: "标准", v_studio: "精品", v_chat: "对话里", v_page: "网页", v_desk: "Studio", v_strict: "严格", v_record: "记下就能用", mc_lead: "做片子要的", mc_ok: "做片子要的都有了。", mc_wait: "正在看这台电脑…", mc_fail: "这次没看成，过一会儿再打开这一页。",
      ab_version: "版本", ab_where: "工作台在哪", ab_news: "更新了什么",
      saved: "记下了", see: "去设置里看", failed: "没记下：{x}", nokey: "这一页现在只能看：在 Studio 自己的窗口里才能改。",
    },
    en: {
      title: "Settings", back: "Back", rail: "Settings", rail_tip: "Settings (⌘,)",
      s_general: "General", s_agent: "Agent", s_films: "Film defaults", s_machine: "This computer", s_about: "About", s_account: "Account",
      lang: "Language", look: "Look", th_darkfield: "Darkfield", th_prism: "Prism", th_bridge: "Bridge",
      where: "Where films are kept", where_how: "To keep them somewhere else, ask your agent to change it, then reopen Studio.", where_none: "Not known yet.",
      ag_default: "New chats start with", ag_not: "Not set up", ag_not_how: "Press “Set it up” in the chat on the right.", ag_model: "Model", ag_effort: "Effort",
      ag_from_default: "Studio's default", ag_from_agent: "{a}'s own default", ag_from_dsh: "as set in the DeepSeek Harness app",
      ag_later: "Start one chat and you can change it here.", ag_none: "No agent is set up on this computer yet.",
      f_lead: "This computer's defaults for every film. What a film says for itself comes first.",
      f_effort: "Default effort", f_review: "Where you look at each stop", f_assets: "Asset licences", f_sound: "Sound library", f_director: "Who decides what",
      f_subagent: "Model for helper agents", f_budget: "Default budget", f_unset: "Not set", f_unset_effort: "Not set: standard", f_unset_review: "Not set: by effort",
      f_unset_assets: "Not set: strict", f_unset_sound: "Not set: ~/.ovh/sound", f_unset_budget: "Not set: no paid services are called",
      f_how: "Ask your agent to change it.",
      mirror: "Download mirror", m_auto: "Automatic", m_cn: "Mainland China mirrors", m_off: "Official sources",
      m_auto_d: "Downloads come from the official sources; if they don't answer during install, it switches to the mirrors by itself.", m_cn_d: "Every later download comes from the mainland China mirrors.", m_off_d: "Downloads only come from the official sources.",
      m_set: "(set {d})", mc_rest: "Everything else films need is here.",
      v_quick: "Quick", v_standard: "Standard", v_studio: "Studio", v_chat: "In the chat", v_page: "A web page", v_desk: "Studio", v_strict: "Strict", v_record: "Allowed if recorded", mc_lead: "Needed for films", mc_ok: "Everything films need is here.", mc_wait: "Looking at this computer…", mc_fail: "Couldn't look this time; open this page again in a moment.",
      ab_version: "Version", ab_where: "Where the workbench is", ab_news: "What's new",
      saved: "Saved", see: "See it in Settings", failed: "Not saved: {x}", nokey: "This page can only look: change settings in Studio's own window.",
    },
  };
  const w = (k, v) => String((W[LANG] || W.zh)[k] != null ? (W[LANG] || W.zh)[k] : W.en[k] != null ? W.en[k] : k).replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ""));
  // the sections, in order; account waits for accounts (not shown)
  const SECTIONS = [{ id: "general" }, { id: "agent" }, { id: "films" }, { id: "machine" }, { id: "about" }, { id: "account", hidden: true }];
  const THEMES = ["darkfield", "prism", "bridge"];
  let ST = null, BACK = "#/", SEC = "general";

  async function call(method, body) {
    try {
      const r = await fetch("/api/settings", { method, cache: "no-store", headers: Object.assign({ "X-Desk-Token": TOKEN }, body ? { "Content-Type": "application/json" } : {}), body: body ? JSON.stringify(body) : undefined });
      const j = await r.json().catch(() => null);
      return { ok: r.ok, status: r.status, data: j };
    } catch (e) { return { ok: false, status: 0, data: null }; }
  }
  async function load() { const r = await call("GET"); if (r.ok && r.data) ST = r.data; return r; }
  async function save(name, value, quiet) {
    const r = await call("POST", { name, value });
    if (r.ok && r.data) { ST = r.data; if (!quiet) toast(w("saved")); }
    else if (!quiet) toast(r.status === 403 ? w("nokey") : w("failed", { x: (r.data && r.data.error) || r.status }));
    return r.ok;
  }

  /* the rail's entry, at its foot (studio.js's renderRail adds it) */
  const GEAR = '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>';
  function railItem(proj) {
    const here = parse().view === "settings";
    return `${proj ? "" : '<span class="grow"></span>'}<hr><a class="mod" href="#/settings" title="${esc(w("rail_tip"))}" aria-current="${here ? "page" : "false"}" data-settings><svg viewBox="0 0 24 24" aria-hidden="true">${GEAR}</svg><span>${esc(w("rail"))}</span></a>`;
  }

  /* the page */
  async function show(sec) {
    if (parse().view !== "settings") return;
    SEC = SECTIONS.some((s) => s.id === sec && !s.hidden) ? sec : "general";
    leaveProject(); D = null; PKEY = ""; MOD = ""; GV = null;
    crumbs([{ text: t("m_space"), href: "#/" }, { text: w("title") }]); renderFlow(); renderRail(); spaceColumn();
    if (!ST) $("#stage").innerHTML = `<p class="loading">…</p>`;
    const r = await load();
    if (parse().view !== "settings") return;
    if (!ST) { $("#stage").innerHTML = `<p class="void module">${esc(r.status === 403 ? w("nokey") : t("noServer"))}</p>`; return; }
    if (SEC === "general" && !LIST) await listing();
    if (parse().view !== "settings") return;
    draw();
    if (SEC === "machine") machine().then(() => { if (parse().view === "settings" && SEC === "machine") draw(); });
  }
  function draw() {
    const area = $("#stage"), y = area.scrollTop;
    const nav = SECTIONS.filter((s) => !s.hidden).map((s) => `<a href="#/settings/${s.id}" aria-current="${s.id === SEC ? "page" : "false"}">${esc(w("s_" + s.id))}</a>`).join("");
    area.innerHTML = `<section class="module settings"><div class="mh"><h1>${esc(w("title"))}</h1><a class="st-back btn btn-quiet" href="${esc(BACK)}">${esc(w("back"))}</a></div>
      <div class="st-wrap"><nav class="st-nav" aria-label="${esc(w("title"))}">${nav}</nav><div class="st-body">${({ general, agent, films, machine: machineSec, about })[SEC === "machine" ? "machine" : SEC]()}</div></div></section>`;
    area.scrollTop = y;
  }
  const row = (label, body, note) => `<div class="st-row"><div class="st-k">${esc(label)}</div><div class="st-v">${body}${note ? `<p class="st-note">${note}</p>` : ""}</div></div>`;
  const seg = (name, opts, cur) => `<div class="st-seg" role="radiogroup">${opts.map(([v, label]) => `<button type="button" role="radio" aria-checked="${v === cur}" data-set="${esc(name)}" data-val="${esc(v)}">${esc(label)}</button>`).join("")}</div>`;

  function general() {
    const theme = document.documentElement.getAttribute("data-theme") || "darkfield";
    const looks = `<div class="st-looks" role="radiogroup">${THEMES.map((x) => `<button type="button" role="radio" class="st-look st-look-${x}" aria-checked="${x === theme}" data-theme-set="${x}"><i aria-hidden="true"><b></b><b></b><b></b></i><span>${esc(w("th_" + x))}</span></button>`).join("")}</div>`;
    const roots = ((LIST && LIST.roots) || []).map((x) => x.path || x).filter(Boolean);
    const where = roots.length ? `<ul class="st-paths">${roots.map((p) => `<li><code>${esc(p)}</code></li>`).join("")}</ul>` : `<p class="st-dim">${esc(w("where_none"))}</p>`;
    return row(w("lang"), seg("studio_lang", [["zh", "中文"], ["en", "English"]], LANG))
      + row(w("look"), looks)
      + row(w("where"), where, esc(w("where_how")));
  }
  function agent() {
    const kinds = (ST.agents && ST.agents.kinds) || [], got = kinds.filter((k) => k.installed);
    if (!got.length) return row(w("ag_default"), `<p class="st-dim">${esc(w("ag_none"))}</p>`, esc(w("ag_not_how")));
    const def = (got.find((k) => k.kind === ST.agents.default) || got[0]).kind;
    const pick = got.length > 1 ? seg("agent_default", got.map((k) => [k.kind, k.label]), def) : `<p>${esc(got[0].label)}</p>`;
    const missing = kinds.filter((k) => !k.installed).map((k) => `<li class="st-dim">${esc(k.label)} · ${esc(w("ag_not"))}</li>`).join("");
    let out = row(w("ag_default"), pick + (missing ? `<ul class="st-list">${missing}</ul>` : ""), missing ? esc(w("ag_not_how")) : "");
    for (const k of got) {
      const ch = k.choices || {}, offered = ch.offered || {};
      const one = (role) => {
        const c = ch[role] || {}, opts = offered[role] || [];
        if (opts.length) return `<select data-set="${role}:${esc(k.kind)}">${opts.map((o) => `<option value="${esc(o.value)}"${o.value === c.value ? " selected" : ""}>${esc(o.name)}</option>`).join("")}</select>`;
        const from = c.from === "default" ? w("ag_from_default") : c.from === "dsh" ? w("ag_from_dsh") : c.from === "agent" || !c.name ? w("ag_from_agent", { a: k.label }) : "";
        return `<p>${esc(c.name || "")}${c.name && from ? " · " : ""}<span class="st-dim">${esc(from)}</span></p>`;
      };
      const later = !(offered.model || offered.effort);
      out += `<h2 class="st-h">${esc(k.label)}</h2>` + row(w("ag_model"), one("model")) + row(w("ag_effort"), one("effort"), later ? esc(w("ag_later")) : "");
    }
    return out;
  }
  function films() {
    const L = (ST.local && ST.local.lines) || {}, M = ST.mirror || {};
    const said = (k) => {   // a known value in the page's words (LOCAL.md's own words for the way a stop is looked at, too)
      const m = String(L[k]).match(/^(quick|standard|studio|对话|chat|审阅页|page|审阅台|desk|strict|record)(?![A-Za-z])/i);
      return m && ["effort", "review", "assets"].includes(k) ? w("v_" + m[1].toLowerCase().replace(/^对话$/, "chat").replace(/^审阅页$/, "page").replace(/^审阅台$/, "desk")) : L[k];
    };
    const val = (k) => (L[k] ? `<p>${esc(said(k))}</p>` : `<p class="st-dim">${esc(w(W.zh["f_unset_" + k] ? "f_unset_" + k : "f_unset"))}</p>`);
    const mirror = seg("mirror", [["auto", w("m_auto")], ["cn", w("m_cn")], ["off", w("m_off")]], M.mode || "auto");
    const when = M.at ? ` <span class="st-dim">${esc(w("m_set", { d: M.at }))}</span>` : "";
    return `<p class="st-lead">${esc(w("f_lead"))}</p>`
      + row(w("mirror"), mirror, esc(w("m_" + (M.mode || "auto") + "_d")) + when)
      + ["effort", "review", "assets", "sound", "director", "subagent", "budget"].map((k) => row(w("f_" + k), val(k))).join("")
      + `<p class="st-note st-foot">${esc(w("f_how"))}</p>`;
  }
  function machineSec() {
    if (!MACHINE) return `<p class="st-dim">${esc(w("mc_wait"))}</p>`;
    if (MACHINE.error) return `<p class="st-dim">${esc(w("mc_fail"))}</p>`;
    return (MACHINE.lacks || []).length ? lacksHtml() + `<p class="st-note">${esc(w("mc_rest"))}</p>` : row(w("mc_lead"), `<p>${esc(w("mc_ok"))}</p>`);
  }
  function about() {
    const a = ST.about || {};
    return row(w("ab_version"), `<p>${esc(a.version || "")}</p>`)
      + row(w("ab_where"), `<code>${esc(a.workspace || "")}</code>`)
      + row(w("ab_news"), `<a href="https://github.com/ZLHad/OpenVideoHarness/blob/main/CHANGELOG.md" target="_blank" rel="noopener">CHANGELOG</a>`);
  }

  /* the page's clicks; the top bar's language and look buttons (their own handlers ran first: the new value is in place) */
  document.addEventListener("click", async (e) => {
    if (e.target.closest("#lang")) { save("studio_lang", LANG, true); if (parse().view === "settings") draw(); return; }
    const th = e.target.closest("[data-theme-set]");
    if (th) { save("studio_theme", th.dataset.themeSet, true); if (parse().view === "settings" && SEC === "general") draw(); return; }
    const b = e.target.closest(".settings [data-set]");
    if (!b || b.tagName === "SELECT") return;
    const name = b.dataset.set, v = b.dataset.val;
    if (name === "studio_lang") { if (v !== LANG) $("#lang").click(); return; }
    if (await save(name, v) && parse().view === "settings") draw();
  });
  document.addEventListener("change", async (e) => {
    const s = e.target.closest(".settings select[data-set]");
    if (s && await save(s.dataset.set, s.value) && parse().view === "settings") draw();
  });
  document.addEventListener("keydown", (e) => {   // ⌘, (Ctrl+, elsewhere): in Studio's own window the menu item does this
    if (e.key === "," && (e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey) { e.preventDefault(); go("#/settings"); }
    else if (e.key === "Escape" && parse().view === "settings" && !typing()) go(BACK);
  });
  window.addEventListener("hashchange", (e) => {   // where Back goes: the page this one was opened from
    const from = new URL(e.oldURL).hash || "#/";
    if (!from.startsWith("#/settings") && location.hash.startsWith("#/settings")) BACK = from;
  });

  /* at start: what is kept for this machine wins over this browser's copy; a copy with nothing kept yet is kept */
  async function sync(tries) {
    const r = await load();
    if (!r.ok) { if (r.status === 403 && tries < 10) setTimeout(() => sync(tries + 1), 1000); return; }
    const st = ST.studio || {}, theme = document.documentElement.getAttribute("data-theme");
    if (st.studio_theme && st.studio_theme !== theme) OVH.theme(st.studio_theme);
    else if (!st.studio_theme && theme && theme !== "darkfield") save("studio_theme", theme, true);
    if (st.studio_lang && st.studio_lang !== LANG) $("#lang").click();
    else if (!st.studio_lang && LANG !== "zh") save("studio_lang", LANG, true);
  }
  setTimeout(() => sync(0), 300);

  return { show, railItem, word: w, words: W };
})();
