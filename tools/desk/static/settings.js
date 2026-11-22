/* Studio's settings page, #/settings[/<section>] (tools/desk/settings_api.py serves it; tools/desk/README.md "设置页").
   One page with its sections on the left and one section at a time. What a person changes is kept in this machine's
   settings file (tools/settings.py), so a second window, another port or the terminal see the same; the console writes
   the language and the look into the page it serves, so the first paint has them, and this browser keeps a copy. The top
   bar's language and look buttons stay: they change the same two settings (their clicks are heard here). Loaded before
   studio.js; it uses studio.js's and core.js's names only when it runs. */
const SETTINGS = (() => {
  const W = {
    zh: {
      title: "设置", back: "返回", rail: "设置", rail_tip: "设置（⌘,）",
      s_general: "通用", s_agent: "agent", s_services: "服务", s_films: "片子的默认", s_machine: "这台电脑", s_about: "关于", s_account: "账号",
      lang: "语言", look: "外观", th_darkfield: "暗场", th_prism: "棱镜", th_bridge: "舰桥",
      where: "片子放在哪", where_how: "想换个地方，让 agent 帮你改，改完重新打开 Studio。", where_none: "还没有这样的文件夹。", reveal: "在访达里打开", reveal_other: "打开文件夹",
      ag_default: "新对话默认用", ag_not: "还没装", ag_not_how: "在右边的对话里点「装上」。", ag_model: "模型", ag_effort: "思考深度",
      ag_from_default: "Studio 的默认", ag_from_agent: "{a} 自己的默认", ag_from_dsh: "DeepSeek Harness 桌面版里的设置",
      ag_later: "开一次对话以后，这里能改。", ag_none: "这台电脑上还没有装好的 agent。",
      col_space: "这里是空间的对话：在这里写一句，agent 会开一支新片子。片子自己的对话，回到那支片子里看。",
      f_lead: "这些是这台电脑给每支片子的默认。片子自己写了的，以片子的为准。",
      f_effort: "默认努力程度", f_review: "在哪看每一站", f_assets: "素材许可", f_sound: "声音库", f_director: "谁拍板哪些事",
      f_subagent: "帮手 agent 用的模型", f_budget: "默认预算", f_unset: "没写", f_unset_effort: "没写：按标准", f_unset_review: "没写：按努力程度",
      f_unset_assets: "没写：严格", f_unset_sound: "没写：用 ~/.ovh/sound", f_unset_budget: "没写：不调收费的服务",
      f_unset_director: "没写：按努力程度的默认", f_unset_subagent: "没写：比 agent 自己便宜一档",
      f_how: "让 agent 帮你改。",
      mirror: "下载镜像", m_auto: "自动", m_cn: "国内镜像", m_off: "官方源",
      m_auto_d: "从官方源下载；安装时官方源连不上，会自己换成国内镜像。", m_cn_d: "以后的下载走国内镜像。", m_off_d: "以后的下载只从官方源。",
      m_restart: "已经开着的对话里，agent 自己的 npm、uv 下载要新开一个对话才跟着变。", m_own: "这几处你自己设了别的源，照旧用你的：", newer: "这台电脑的设置文件是更新版本的 OpenVideoHarness 写的，这里不改它。",
      m_set: "（{d} 设的）", mc_lead: "做片子要的", mc_ok: "做片子要的都有了。", mc_rest: "别的做片子要的都有了。",
      mc_wait: "正在看这台电脑…", mc_fail: "这次没看成，过一会儿再打开这一页。", mc_agent_d: "在右边的对话里点「装上」。",
      v_quick: "快速", v_standard: "标准", v_studio: "精品", v_chat: "对话里", v_page: "网页", v_desk: "Studio", v_strict: "严格", v_record: "记下就能用",
      ab_version: "版本", ab_where: "工作台在哪", ab_news: "更新了什么", ab_news_link: "这一版的说明",
      saved: "记下了", see: "去设置里看", failed: "没记下：{x}",
      sv_lead: "配音默认用这台电脑上的声音，不用 API Key。下面的在线服务，用到哪家再设哪家。",
      sv_gemini: "Gemini（Google）", sv_gemini_d: "在线配音、给字幕对时间、出图、作曲", sv_minimax: "MiniMax", sv_minimax_d: "在线配音",
      sv_elevenlabs: "ElevenLabs", sv_elevenlabs_d: "在线配音", sv_dashscope: "阿里云百炼", sv_dashscope_d: "在线配音",
      k_key: "API Key", k_MINIMAX_TOKEN_PLAN_KEY: "Token Plan 的 API Key", k_MINIMAX_API_KEY: "按量计费的 API Key",
      c_free: "免费", c_free_tier: "有免费额度", c_paid: "收费",
      st_none: "没设", st_studio: "在 Studio 里设了", st_env: "在环境变量里设了（优先用它）",
      b_set: "填上", b_replace: "换一个", b_clear: "拿掉", b_clear_sure: "确定拿掉", b_test: "测一下", b_save: "保存", b_cancel: "取消",
      ph: "粘贴 {s} 的 API Key", get_key: "去哪拿 API Key", clear_note: "拿掉以后，用到它的命令会停下来告诉你。",
      t_wait: "正在问…", t_ok: "能用了", t_fail: "没通过，服务的回答：{x}", t_skip: "还没有 API Key 可以测", t_free: "测一下不花钱。",
      sv_kept_keychain: "存在这台电脑的钥匙串里，不写进任何文件。", sv_kept_secret: "存在这台电脑的密码库里，不写进任何文件。",
      sv_none: "这台电脑上没有 Studio 能妥善保管 API Key 的地方。要用在线服务，就把 API Key 写进终端每次启动都会读的那个文件，再从新开的终端里打开 Studio。", how: "怎么写",
      e_not_a_key: "这不像 API Key：从服务商的页面把它整段复制下来，不带空格和引号，再粘贴一次。",
      e_not_kept: "没存进去：{s}没收下。再粘贴一次试试；还是不行，就照说明写进终端启动时读的文件。", e_not_cleared: "没拿掉：{s}没响应。再试一次。",
      s_keychain: "钥匙串", s_secret: "密码库",
      sv_env_note: "在终端里设的环境变量，这一页不一定看得到；在这里填上的，终端里和右边的对话里都用得上。",
      sv_budget: "有 API Key 不等于有预算。出图和 Lyria 作曲，片子和这台电脑都没写预算就不调；用这几家配音、给字幕对时间、试音，是直接调用，花的是那个账户的钱（有免费额度的先用免费额度）。这台电脑的默认预算：{x}",
      nokey: "这一页要在 Studio 的窗口里打开才看得到。", reopen: "在 Studio 窗口里打开",
    },
    en: {
      title: "Settings", back: "Back", rail: "Settings", rail_tip: "Settings (⌘,)",
      s_general: "General", s_agent: "Agent", s_services: "Services", s_films: "Film defaults", s_machine: "This computer", s_about: "About", s_account: "Account",
      lang: "Language", look: "Look", th_darkfield: "Darkfield", th_prism: "Prism", th_bridge: "Bridge",
      where: "Where films are kept", where_how: "To keep them somewhere else, ask your agent to change it, then reopen Studio.", where_none: "No such folder yet.", reveal: "Show in Finder", reveal_other: "Open folder",
      ag_default: "New chats start with", ag_not: "Not set up", ag_not_how: "Press “Set it up” in the chat on the right.", ag_model: "Model", ag_effort: "Effort",
      ag_from_default: "Studio's default", ag_from_agent: "{a}'s own default", ag_from_dsh: "as set in the DeepSeek Harness app",
      ag_later: "Start one chat and you can change it here.", ag_none: "No agent is set up on this computer yet.",
      col_space: "This is the space's chat: a sentence here starts a new film. A film's own chat is in that film.",
      f_lead: "This computer's defaults for every film. What a film says for itself comes first.",
      f_effort: "Default effort", f_review: "Where you look at each stop", f_assets: "Asset licences", f_sound: "Sound library", f_director: "Who decides what",
      f_subagent: "Model for helper agents", f_budget: "Default budget", f_unset: "Not set", f_unset_effort: "Not set: standard", f_unset_review: "Not set: by effort",
      f_unset_assets: "Not set: strict", f_unset_sound: "Not set: ~/.ovh/sound", f_unset_budget: "Not set: no paid services are called",
      f_unset_director: "Not set: the effort's own defaults", f_unset_subagent: "Not set: one tier cheaper than the agent's own",
      f_how: "Ask your agent to change it.",
      mirror: "Download mirror", m_auto: "Automatic", m_cn: "Mainland China mirrors", m_off: "Official sources",
      m_auto_d: "Downloads come from the official sources; if they don't answer during install, it switches to the mirrors by itself.", m_cn_d: "Later downloads come from the mainland China mirrors.", m_off_d: "Later downloads come only from the official sources.",
      m_restart: "In a chat that is already open, the agent's own npm and uv downloads follow from its next chat.", m_own: "These sources you set yourself stay yours:", newer: "This computer's settings file was written by a newer OpenVideoHarness, so it isn't changed here.",
      m_set: "(set {d})", mc_lead: "Needed for films", mc_ok: "Everything films need is here.", mc_rest: "Everything else films need is here.",
      mc_wait: "Looking at this computer…", mc_fail: "Couldn't look this time; open this page again in a moment.", mc_agent_d: "Press “Set it up” in the chat on the right.",
      v_quick: "Quick", v_standard: "Standard", v_studio: "Studio", v_chat: "In the chat", v_page: "A web page", v_desk: "Studio", v_strict: "Strict", v_record: "Allowed if recorded",
      ab_version: "Version", ab_where: "Where the workbench is", ab_news: "What's new", ab_news_link: "This version's notes",
      saved: "Saved", see: "See it in Settings", failed: "Not saved: {x}",
      sv_lead: "Voices are made on this computer by default, no API Key needed. Set up an online service below only when you want it.",
      sv_gemini: "Gemini (Google)", sv_gemini_d: "online voices, timing the captions, pictures, music", sv_minimax: "MiniMax", sv_minimax_d: "online voices",
      sv_elevenlabs: "ElevenLabs", sv_elevenlabs_d: "online voices", sv_dashscope: "Alibaba Cloud Model Studio", sv_dashscope_d: "online voices",
      k_key: "API Key", k_MINIMAX_TOKEN_PLAN_KEY: "Token Plan API Key", k_MINIMAX_API_KEY: "Pay-as-you-go API Key",
      c_free: "Free", c_free_tier: "Free tier", c_paid: "Paid",
      st_none: "Not set", st_studio: "Set in Studio", st_env: "Set in the environment (used first)",
      b_set: "Set up", b_replace: "Replace", b_clear: "Remove", b_clear_sure: "Yes, remove", b_test: "Test", b_save: "Save", b_cancel: "Cancel",
      ph: "Paste your {s} API Key", get_key: "Get an API Key", clear_note: "Once removed, commands that need it stop and tell you.",
      t_wait: "Asking…", t_ok: "Works", t_fail: "Didn't work; the service said: {x}", t_skip: "No API Key to test yet", t_free: "Testing costs nothing.",
      sv_kept_keychain: "Kept in this computer's Keychain, never written into any file.", sv_kept_secret: "Kept in this computer's password store, never written into any file.",
      sv_none: "This computer has no place where Studio can keep an API Key safely. To use an online service, put the API Key in the file your terminal reads each time it starts, then open Studio from a new terminal.", how: "How",
      e_not_a_key: "That doesn't look like an API Key: copy the whole key from the provider's page, with no spaces or quotes, and paste it again.",
      e_not_kept: "Not saved: {s} didn't take it. Paste it again; if it still fails, put it in the file your terminal reads when it starts.", e_not_cleared: "Not removed: {s} didn't answer. Try again.",
      s_keychain: "the Keychain", s_secret: "the password store",
      sv_env_note: "Environment variables set in your terminal may not show on this page; a key set here works in the terminal and in the chat on the right.",
      sv_budget: "An API Key isn't a budget. Pictures and Lyria music are not made unless the film or this computer has a budget; voices, caption timing and auditions with these services are called directly and bill that account (a free tier is used first). This computer's default budget: {x}",
      nokey: "This page shows only in Studio's own window.", reopen: "Open in Studio's window",
    },
  };
  const w = (k, v) => String((W[LANG] || W.zh)[k] != null ? (W[LANG] || W.zh)[k] : W.en[k] != null ? W.en[k] : k).replace(/\{(\w+)\}/g, (_, x) => (v && v[x] != null ? v[x] : ""));
  // the sections, in order; account waits for accounts (not shown)
  const SECTIONS = [{ id: "general" }, { id: "agent" }, { id: "services" }, { id: "films" }, { id: "machine" }, { id: "about" }, { id: "account", hidden: true }];
  const THEMES = ["darkfield", "prism", "bridge"];
  let ST = null, BACK = "#/", SEC = "general";
  let EDIT = "", ARM = "", TESTS = {}, SVERR = {};   // the services: the key being typed, the key whose 拿掉 asks once more, each service's last test, what a failed save of a key said
  const HOWTO = () => `https://github.com/ZLHad/OpenVideoHarness/blob/main/README${LANG === "en" ? "" : ".zh-CN"}.md#api-key`;   // the front page's "API Key": how to put a key where the terminal reads it
  const why_err = (r) => {   // a refusal of the console's as the page's own word (said in the language shown), when it gave a reason
    const why = r.data && r.data.reason;
    return why === "not_a_key" ? "e_not_a_key" : why === "not_kept" ? "e_not_kept" : why === "no_store" ? "sv_none" : null;
  };
  const store_word = () => w(ST && ST.store === "secret-service" ? "s_secret" : "s_keychain");
  const said_err = (r) => { const k = why_err(r); return k ? w(k, { s: store_word() }) : null; };

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
    if (r.ok && r.data && r.data.version) ST = r.data;
    if (!quiet || (!r.ok && r.data && r.data.reason === "newer")) toast(r.ok ? w("saved") : r.status === 403 ? w("nokey") : r.data && r.data.reason === "newer" ? w("newer") : said_err(r) || w("failed", { x: (r.data && r.data.error) || r.status }));
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
    const now = $("#colNow");   // the column is the space's here, not the film's it came from: said above it
    now.className = "col-now"; now.innerHTML = `<p class="now-say"><span>${esc(w("col_space"))}</span></p>`; now.dataset.html = ""; now.hidden = false;
    if (!ST) $("#stage").innerHTML = `<p class="loading">…</p>`;
    const r = await load();
    if (parse().view !== "settings") return;
    if (!ST) {
      $("#stage").innerHTML = r.status === 403 ? `<section class="module settings"><p class="void">${esc(w("nokey"))}</p><button type="button" class="btn" id="stReopen">${esc(w("reopen"))}</button></section>`
        : `<p class="void module">${esc(t("noServer"))}</p>`;
      const b = $("#stReopen"); if (b) b.addEventListener("click", (e) => { if (e.isTrusted) reopen(); });
      return;
    }
    draw();
    if (SEC === "machine") machine().then(() => { if (parse().view === "settings" && SEC === "machine") draw(); });
  }
  function draw() {
    const area = $("#stage"), y = area.scrollTop, f = $("#stage :focus"), refocus = f && (f.dataset.val || f.dataset.themeSet || f.dataset.set);
    const nav = SECTIONS.filter((s) => !s.hidden).map((s) => `<a href="#/settings/${s.id}" aria-current="${s.id === SEC ? "page" : "false"}">${esc(w("s_" + s.id))}</a>`).join("");
    area.innerHTML = `<section class="module settings"><div class="mh"><h1>${esc(w("title"))}</h1><a class="st-back btn btn-quiet" href="${esc(BACK)}">${esc(w("back"))}</a></div>
      <div class="st-wrap"><nav class="st-nav" aria-label="${esc(w("title"))}">${nav}</nav><div class="st-body">${({ general, agent, services, films, machine: machineSec, about })[SEC]()}</div></div></section>`;
    area.scrollTop = y;
    if (refocus) { const b = [...area.querySelectorAll("[role=radio], select")].find((x) => (x.dataset.val || x.dataset.themeSet || x.dataset.set) === refocus); if (b) b.focus(); }
  }
  const row = (label, body, note) => `<div class="st-row"><div class="st-k">${esc(label)}</div><div class="st-v">${body}${note ? `<p class="st-note">${note}</p>` : ""}</div></div>`;
  const radios = (label, items) =>   // a radio group: one tab stop (the chosen one), arrows move and choose
    `<div class="st-seg" role="radiogroup" aria-label="${esc(label)}">${items.map((x) => `<button type="button" role="radio" aria-checked="${x.on}" tabindex="${x.on ? 0 : -1}" ${x.attrs}>${x.body}</button>`).join("")}</div>`;
  const seg = (name, opts, cur, label) => radios(label, opts.map(([v, text]) => ({ on: v === cur, attrs: `data-set="${esc(name)}" data-val="${esc(v)}"`, body: esc(text) })));

  function general() {
    const st = ST.studio || {}, theme = st.studio_theme || document.documentElement.getAttribute("data-theme") || "darkfield";
    const looks = radios(w("look"), THEMES.map((x) => ({ on: x === theme, attrs: `class="st-look st-look-${x}" data-theme-set="${x}"`, body: `<i aria-hidden="true"><b></b><b></b><b></b></i><span>${esc(w("th_" + x))}</span>` })))
      .replace('class="st-seg"', 'class="st-looks"');
    const mac = /Mac/i.test(navigator.platform || navigator.userAgent || "");
    const roots = ST.roots || [];
    const where = roots.length ? `<ul class="st-paths">${roots.map((r) => `<li><code title="${esc(r.path)}">${esc(r.shown)}</code><button type="button" class="btn btn-quiet xs" data-reveal="${esc(r.path)}">${esc(w(mac ? "reveal" : "reveal_other"))}</button></li>`).join("")}</ul>`
      : `<p class="st-dim">${esc(w("where_none"))}</p>`;
    return row(w("lang"), seg("studio_lang", [["zh", "中文"], ["en", "English"]], st.studio_lang || "zh", w("lang")))
      + row(w("look"), looks)
      + row(w("where"), where, esc(w("where_how")));
  }
  function agent() {
    const kinds = (ST.agents && ST.agents.kinds) || [], got = kinds.filter((k) => k.installed);
    if (!got.length) return row(w("ag_default"), `<p class="st-dim">${esc(w("ag_none"))}</p>`, esc(w("ag_not_how")));
    const def = (got.find((k) => k.kind === ST.agents.default) || got[0]).kind;
    const pick = got.length > 1 ? seg("agent_default", got.map((k) => [k.kind, k.label]), def, w("ag_default")) : `<p>${esc(got[0].label)}</p>`;
    const missing = kinds.filter((k) => !k.installed).map((k) => `<li class="st-dim">${esc(k.label)} · ${esc(w("ag_not"))}</li>`).join("");
    let out = row(w("ag_default"), pick + (missing ? `<ul class="st-list">${missing}</ul>` : ""), missing ? esc(w("ag_not_how")) : "");
    for (const k of got) {
      const ch = k.choices || {}, offered = ch.offered || {};
      const one = (role) => {
        const c = ch[role] || {}, opts = offered[role] || [];
        if (opts.length) return `<select data-set="${role}:${esc(k.kind)}" aria-label="${esc(k.label)} · ${esc(w("ag_" + role))}">${opts.map((o) => `<option value="${esc(o.value)}"${o.value === c.value ? " selected" : ""}>${esc(o.name)}</option>`).join("")}</select>`;
        const from = c.from === "default" ? w("ag_from_default") : c.from === "dsh" ? w("ag_from_dsh") : c.from === "agent" || !c.name ? w("ag_from_agent", { a: k.label }) : "";
        return `<p>${esc(c.name || "")}${c.name && from ? " · " : ""}<span class="st-dim">${esc(from)}</span></p>`;
      };
      const later = !(offered.model || offered.effort);
      out += `<h2 class="st-h">${esc(k.label)}</h2>` + row(w("ag_model"), one("model")) + row(w("ag_effort"), one("effort"), later ? esc(w("ag_later")) : "");
    }
    return out;
  }
  function services() {
    const store = ST.store || "none", list = ST.services || [], L = (ST.local && ST.local.lines) || {};
    const anySaved = list.some((s) => s.keys.some((k) => k.saved));
    const keyRow = (s, k) => {
      const label = (W.zh["k_" + k.name] ? w("k_" + k.name) : w("k_key")), status = w(k.source === "env" ? "st_env" : k.source === "studio" ? "st_studio" : "st_none");
      // (no <form> and no password box: a browser would offer to keep the key in its own password manager; the box is masked by its style)
      if (EDIT === k.name) return `<div class="sv-key"><span class="st-dim">${esc(label)}</span><div class="sv-form" data-sv-form="${esc(k.name)}"><input type="text" class="sv-in" autocomplete="off" autocapitalize="off" spellcheck="false" data-1p-ignore data-lpignore="true" data-form-type="other" id="svIn" placeholder="${esc(w("ph", { s: w("sv_" + s.module) }))}" aria-label="${esc(w("sv_" + s.module))} · ${esc(label)}"><button type="button" class="btn" data-sv-save>${esc(w("b_save"))}</button><button type="button" class="btn btn-quiet" data-sv-cancel>${esc(w("b_cancel"))}</button></div>${SVERR[k.name] ? `<p class="st-note sv-err" role="alert">${esc(SVERR[k.name].k ? w(SVERR[k.name].k, { s: store_word() }) : SVERR[k.name].x)}${["e_not_kept", "sv_none"].includes(SVERR[k.name].k) ? ` <a href="${esc(HOWTO())}" target="_blank" rel="noopener">${esc(w("how"))} ↗</a>` : ""}</p>` : ""}</div>`;
      const acts = store === "none" ? "" : k.saved ? `<button type="button" class="btn btn-quiet xs" data-sv-edit="${esc(k.name)}">${esc(w("b_replace"))}</button><button type="button" class="btn btn-quiet xs${ARM === k.name ? " warn" : ""}" data-sv-clear="${esc(k.name)}">${esc(w(ARM === k.name ? "b_clear_sure" : "b_clear"))}</button>`
        : k.source === "env" ? "" : `<button type="button" class="btn xs" data-sv-edit="${esc(k.name)}">${esc(w("b_set"))}</button>`;
      return `<div class="sv-key"><span class="st-dim">${esc(label)}</span><span class="sv-st${k.source ? " on" : ""}">${esc(status)}</span><span class="sv-acts">${acts}</span>${ARM === k.name ? `<p class="st-note">${esc(w("clear_note"))}</p>` : ""}</div>`;
    };
    const card = (s) => {
      const t = TESTS[s.module], has = s.keys.some((k) => k.source);
      const test = s.probe && has ? `<button type="button" class="btn btn-quiet xs" data-sv-test="${esc(s.module)}" title="${esc(w("t_free"))}">${esc(w("b_test"))}</button>` : "";
      const said = !t ? "" : t === "wait" ? w("t_wait") : t.state === "ok" ? w("t_ok") : t.state === "skipped" ? w("t_skip") : w("t_fail", { x: t.note || "" });
      return `<section class="sv" aria-label="${esc(w("sv_" + s.module))}"><div class="sv-h"><b>${esc(w("sv_" + s.module))}</b><span class="chip quiet">${esc(w("c_" + (s.cost || "paid")))}</span><span class="sv-d">${esc(w("sv_" + s.module + "_d"))}</span>${test}</div>`
        + s.keys.map((k) => keyRow(s, k)).join("")
        + `${said ? `<p class="st-note sv-test${t && t.state === "ok" ? " ok" : ""}">${esc(said)}</p>` : ""}${s.key_url ? `<a class="sv-get" href="${esc(s.key_url)}" target="_blank" rel="noopener">${esc(w("get_key"))} ↗</a>` : ""}</section>`;
    };
    return `<p class="st-lead">${esc(w("sv_lead"))}</p>`
      + (store === "none" ? `<p class="st-note">${esc(w("sv_none"))} <a href="${esc(HOWTO())}" target="_blank" rel="noopener">${esc(w("how"))} ↗</a></p>` : anySaved ? `<p class="st-note sv-kept">${esc(w(store === "keychain" ? "sv_kept_keychain" : "sv_kept_secret"))}</p>` : "")
      + list.map(card).join("")
      + `<p class="st-note st-foot">${store === "none" ? "" : `${esc(w("sv_env_note"))}<br>`}${esc(w("sv_budget", { x: L.budget || w("f_unset") }))}</p>`;
  }
  function films() {
    const L = (ST.local && ST.local.lines) || {}, M = ST.mirror || {};
    const said = (k) => {   // a known value in the page's words (LOCAL.md's own words for the way a stop is looked at, too)
      const m = String(L[k]).match(/^(quick|standard|studio|对话|chat|审阅页|page|审阅台|desk|strict|record)(?![A-Za-z])/i);
      return m && ["effort", "review", "assets"].includes(k) ? w("v_" + m[1].toLowerCase().replace(/^对话$/, "chat").replace(/^审阅页$/, "page").replace(/^审阅台$/, "desk")) : L[k];
    };
    const val = (k) => (L[k] ? `<p>${esc(said(k))}</p>` : `<p class="st-dim">${esc(w(W.zh["f_unset_" + k] ? "f_unset_" + k : "f_unset"))}</p>`);
    const mode = M.mode || "auto", mirror = seg("mirror", [["auto", w("m_auto")], ["cn", w("m_cn")], ["off", w("m_off")]], mode, w("mirror"));
    const when = M.at ? ` <span class="st-dim">${esc(w("m_set", { d: M.at }))}</span>` : "";
    return `<p class="st-lead">${esc(w("f_lead"))}</p>`
      + row(w("mirror"), mirror, esc(w("m_" + mode + "_d")) + when + `<br>${esc(w("m_restart"))}`
        + ((M.kept_own || []).length ? `<br>${esc(w("m_own"))}${M.kept_own.map((o) => `<br><code>${esc(o.kind)}</code> ${esc(o.why)}`).join("")}` : ""))
      + ["effort", "review", "assets", "sound", "director", "subagent", "budget"].map((k) => row(w("f_" + k), val(k))).join("")
      + `<p class="st-note st-foot">${esc(w("f_how"))}</p>`;
  }
  function machineSec() {
    if (!MACHINE) return `<p class="st-dim">${esc(w("mc_wait"))}</p>`;
    if (MACHINE.error) return `<p class="st-dim">${esc(w("mc_fail"))}</p>`;
    const L = MACHINE.lacks || [];
    if (!L.length) return row(w("mc_lead"), `<p>${esc(w("mc_ok"))}</p>`);
    const items = L.map((x) => `<li><b>${esc(t("lk_" + x.what + "_n"))}</b>${esc(COLON())}${esc(x.what === "agent" ? t("lk_agent_s") : t(x.state === "outdated" ? "lk_old" : "lk_missing", { s: t("lk_" + x.what + "_s") }))} <span class="do">${esc(x.what === "agent" ? w("mc_agent_d") : t("lk_" + x.what + "_d"))}</span></li>`).join("");
    return `<aside class="lacks" aria-label="${esc(t("lacks_h"))}"><h2>${esc(t("lacks_h"))}</h2><ul>${items}</ul></aside><p class="st-note">${esc(w("mc_rest"))}</p>`;
  }
  function about() {
    const a = ST.about || {};
    return row(w("ab_version"), `<p>${esc(a.version || "")}</p>`)
      + row(w("ab_where"), `<code>${esc(a.workspace || "")}</code>`)
      + row(w("ab_news"), `<a href="${esc(a.url || "")}" target="_blank" rel="noopener">${esc(w("ab_news_link"))}</a>`);
  }

  /* the page's clicks; the top bar's language and look buttons (their own handlers ran first: the new value is in place) */
  async function choose(b) {   // a radio of this page, by click or by arrow: always saved, even when it shows as chosen already
    if (b.dataset.themeSet) { OVH.theme(b.dataset.themeSet); return save("studio_theme", b.dataset.themeSet, true).then(() => draw()); }
    const name = b.dataset.set, v = b.dataset.val;
    if (name === "studio_lang") { if (v !== LANG) $("#lang").click(); else { await save("studio_lang", v, true); draw(); } return; }
    if (await save(name, v) && parse().view === "settings") draw();
  }
  document.addEventListener("click", async (e) => {
    if (e.target.closest("#lang")) { await save("studio_lang", LANG, true); if (parse().view === "settings") draw(); return; }
    const th = e.target.closest("[data-theme-set]");
    if (th && !th.closest(".settings")) { await save("studio_theme", th.dataset.themeSet, true); if (parse().view === "settings" && SEC === "general") draw(); return; }
    const rv = e.target.closest(".settings [data-reveal]");
    if (rv) { if (e.isTrusted) save("reveal", rv.dataset.reveal, true); return; }
    const b = e.target.closest('.settings [role="radio"]');
    if (b) choose(b);
  });
  document.addEventListener("click", async (e) => {   // the services' buttons (the page's own clicks only)
    const b = e.target.closest(".settings [data-sv-edit], .settings [data-sv-cancel], .settings [data-sv-save], .settings [data-sv-clear], .settings [data-sv-test]");
    if (!b || !e.isTrusted) return;
    if (b.dataset.svEdit) { EDIT = b.dataset.svEdit; ARM = ""; SVERR = {}; draw(); const i = $("#svIn"); if (i) i.focus(); return; }
    if (b.hasAttribute("data-sv-cancel")) { EDIT = ""; SVERR = {}; draw(); return; }
    if (b.hasAttribute("data-sv-save")) return sendKey(b.closest("[data-sv-form]"));
    if (b.dataset.svClear) {
      if (ARM !== b.dataset.svClear) { ARM = b.dataset.svClear; EDIT = ""; draw(); return; }
      ARM = ""; const r = await call("POST", { name: "key:" + b.dataset.svClear, value: null });
      if (r.ok && r.data && r.data.version) ST = r.data;
      toast(r.ok ? w("saved") : r.status === 403 ? w("nokey") : r.data && r.data.reason === "not_kept" ? w("e_not_cleared", { s: w(ST && ST.store === "secret-service" ? "s_secret" : "s_keychain") }) : said_err(r) || w("failed", { x: (r.data && r.data.error) || r.status }));
      draw(); return;
    }
    const m = b.dataset.svTest; TESTS[m] = "wait"; draw();
    const r = await call("POST", { name: "test:" + m });
    TESTS[m] = r.ok && r.data && r.data.probe ? r.data.probe : { state: "failed", note: r.status === 403 ? w("nokey") : String((r.data && r.data.error) || r.status) };
    if (parse().view === "settings") draw();
  });
  async function sendKey(f) {   // a key typed into the box: sent once, the box emptied at once, never kept in the page
    const i = f && f.querySelector("input");
    if (!i) return;
    const v = i.value.trim(), name = f.dataset.svForm; i.value = "";
    if (!v) return;
    const r = await call("POST", { name: "key:" + name, value: v });
    if (r.ok && r.data && r.data.version) { ST = r.data; EDIT = ""; SVERR = {}; toast(w("saved")); }
    else SVERR = { [name]: r.status === 403 ? { k: "nokey" } : why_err(r) ? { k: why_err(r) } : { x: w("failed", { x: (r.data && r.data.error) || r.status }) } };   // the box stays open, empty, with what to do next
    if (parse().view === "settings") { draw(); const n = $("#svIn"); if (n && EDIT) n.focus(); }
  }
  document.addEventListener("keydown", (e) => {   // Enter in the key's box sends it (there is no form to submit)
    if (e.key !== "Enter" || !e.isTrusted || e.isComposing || !(e.target.matches && e.target.matches(".settings .sv-in"))) return;
    e.preventDefault(); sendKey(e.target.closest("[data-sv-form]"));
  });
  document.addEventListener("change", async (e) => {
    const s = e.target.closest(".settings select[data-set]");
    if (s && await save(s.dataset.set, s.value) && parse().view === "settings") draw();
  });
  document.addEventListener("keydown", (e) => {
    const r = e.target.closest && e.target.closest('.settings [role="radio"]');
    if (r && /^Arrow(Left|Right|Up|Down)$/.test(e.key)) {   // a radio group: the arrows move to the next one and choose it
      const all = [...r.parentNode.querySelectorAll('[role="radio"]')], i = all.indexOf(r), d = /Left|Up/.test(e.key) ? -1 : 1, n = all[(i + d + all.length) % all.length];
      e.preventDefault(); n.focus(); choose(n); return;
    }
    if (e.key === "," && (e.metaKey || e.ctrlKey) && !e.altKey && !e.shiftKey) { e.preventDefault(); go("#/settings"); }   // in Studio's own window the menu item does this
    else if (e.key === "Escape" && parse().view === "settings" && !typing()) go(BACK);
  });
  window.addEventListener("hashchange", (e) => {   // where Back goes: the page this one was opened from
    const from = new URL(e.oldURL).hash || "#/";
    if (!from.startsWith("#/settings") && location.hash.startsWith("#/settings")) BACK = from;
  });

  /* at start: what this machine keeps wins over this browser's copy; a copy with nothing kept yet is kept */
  function plan(st, theme, lang) {   // → {theme, lang}: what to show; {keep_theme, keep_lang}: what to write into the file
    st = st || {};
    return { theme: st.studio_theme || theme, lang: st.studio_lang || lang,
      keep_theme: !st.studio_theme && theme && theme !== "darkfield" ? theme : null, keep_lang: !st.studio_lang && lang && lang !== "zh" ? lang : null };
  }
  async function sync(tries) {
    const r = await load();
    if (!r.ok) { if (r.status === 403 && tries < 10) setTimeout(() => sync(tries + 1), 1000); return; }
    const p = plan(ST.studio, document.documentElement.getAttribute("data-theme"), LANG);
    if (p.theme !== document.documentElement.getAttribute("data-theme")) OVH.theme(p.theme);
    if (p.lang !== LANG) $("#lang").click();
    if (p.keep_theme) save("studio_theme", p.keep_theme, true);
    if (p.keep_lang) save("studio_lang", p.keep_lang, true);
  }
  setTimeout(() => sync(0), 300);

  return { show, railItem, word: w, words: W, _plan: plan };
})();
