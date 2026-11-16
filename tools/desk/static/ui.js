"use strict";
/* OpenVideoHarness review UI: the one script of a gate view, shared by the static review page (bin/vh review inlines this
   file, so it runs from disk with no server) and the console (bin/vh desk serves it, and studio.js mounts each gate view
   with hooks that send the picks through the desk's submission channel). It reads only the page's own markup (tools/review.py
   writes it) and keeps no state of its own beyond the light/dark choice. No framework, no network. */
(function () {
  const $ = (s, el) => (el || document).querySelector(s), $$ = (s, el) => Array.from((el || document).querySelectorAll(s));
  const clock = (x) => { if (x == null || isNaN(x)) return "–"; x = Math.max(0, x); const m = Math.floor(x / 60), s = x - m * 60; return `${m}:${s.toFixed(1).padStart(4, "0")}`; };
  /* ---------- the theme: three, one default (docs/proposals/02-studio-client.md, 5); changing the default is this one value ---------- */
  const THEMES = ["darkfield", "prism", "bridge"], DEFAULT_THEME = "darkfield";
  function theme(t) {
    t = THEMES.includes(t) ? t : DEFAULT_THEME;
    document.documentElement.setAttribute("data-theme", t);
    try { localStorage.setItem("ovh-theme", t); } catch (e) { /* a private window: not kept */ }
    document.querySelectorAll("[data-theme-set]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.themeSet === t)));
    document.querySelectorAll("select[data-theme-select]").forEach((s) => { s.value = t; });
    if (window.ovhShell) {   // Studio's own window (tools/desk/shell): its colour and its buttons follow the theme
      try { window.ovhShell.theme(t, getComputedStyle(document.documentElement).getPropertyValue("--bg").trim()); } catch (e) { /* a plain page */ }
    }
    return t;
  }
  if (window.ovhShell) {   // Studio's own window (tools/desk/shell/preload.js): its frame is the page's top bar, from the first paint
    document.documentElement.classList.add("shell", window.ovhShell.platform === "mac" ? "shell-mac" : "shell-other");
  }
  {   // before the page paints (the static page's head script has done it already, from ?theme= too)
    let t = document.documentElement.getAttribute("data-theme");
    if (!THEMES.includes(t)) { try { t = localStorage.getItem("ovh-theme"); } catch (e) { t = null; } }
    document.documentElement.setAttribute("data-theme", THEMES.includes(t) ? t : DEFAULT_THEME);
  }
  const typing = (el) => el && (/^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) && el.type !== "radio" || el.isContentEditable);

  /* ---------- the player: a video on its mat, the ruler as its progress bar ---------- */
  function Player(el) {
    const v = $("video", el), well = $(".well", el), ruler = $(".ruler", el), head = $(".r-head", el), done = $(".r-done", el);
    const tip = $(".r-tip", el), time = $(".p-time", el);
    const span0 = el.dataset.t0 != null ? +el.dataset.t0 : null, span1 = el.dataset.t1 != null ? +el.dataset.t1 : null;
    let stopAt = span1, dragging = false, laid = 0;
    const listeners = [];
    v.removeAttribute("controls");
    el.classList.add("js");
    const dur = () => (isFinite(v.duration) && v.duration > 0 ? v.duration : +el.dataset.dur || 0);
    const pct = (t) => { const d = dur(); return d ? Math.min(100, Math.max(0, (t / d) * 100)) : 0; };
    const shots = () => $$(".r-shot", ruler).map((s) => ({ t: +s.dataset.t, id: s.dataset.id, label: s.dataset.label || "", frame: s.dataset.frame || "" })).sort((a, b) => a.t - b.t);
    const segs = () => $$(".r-seg", ruler).map((s) => ({ t: +s.dataset.t, t1: +s.dataset.t1, label: s.title }));

    function layout() {
      const d = dur(); if (!d || laid === d) return; laid = d;
      $$(".r-tick", ruler).forEach((x) => x.remove());
      const steps = [0.5, 1, 2, 5, 10, 15, 30, 60, 120, 300, 600];
      const step = steps.find((s) => d / s <= 90) || 600;
      const long = steps.find((s) => s >= step * 4 && d / s <= 9) || step * 10;
      const frag = document.createDocumentFragment();
      for (let t = 0; t <= d + 1e-6; t += step) {
        const isLong = Math.abs(t / long - Math.round(t / long)) < 1e-6, i = document.createElement("span");
        i.className = "r-tick" + (isLong ? " long" : ""); i.style.left = pct(t) + "%";
        if (isLong && pct(t) < 96) { const l = document.createElement("span"); l.textContent = clock(t).replace(/\.0$/, ""); i.appendChild(l); }
        frag.appendChild(i);
      }
      ruler.insertBefore(frag, head);
      $$(".r-seg", ruler).forEach((s) => { s.style.left = pct(+s.dataset.t) + "%"; s.style.width = Math.max(0, pct(+s.dataset.t1) - pct(+s.dataset.t)) + "%"; });
      $$(".r-shot,.r-mark", ruler).forEach((s) => { s.style.left = pct(+s.dataset.t) + "%"; });
      ruler.setAttribute("aria-valuemax", d.toFixed(1));
      el.classList.add("ready");
      update();
    }
    function update() {
      const t = v.currentTime || 0, d = dur();
      head.style.left = pct(t) + "%"; done.style.width = pct(t) + "%";
      if (time) time.textContent = `${clock(t)} / ${clock(d)}`;
      ruler.setAttribute("aria-valuenow", t.toFixed(1));
      $$(".r-mark", ruler).forEach((m) => m.classList.toggle("on", Math.abs(+m.dataset.t - t) < 1.2));
      listeners.forEach((f) => f(t));
    }
    function seek(t, play) {
      t = Math.max(0, Math.min(t, dur() || t));
      try { v.currentTime = t; } catch (e) { /* not loaded yet */ }
      update();
      if (play) v.play().catch(() => {});
    }
    function toggle() { if (v.paused) { if (stopAt != null && v.currentTime >= stopAt - 0.05) seek(span0 || 0); v.play().catch(() => {}); } else v.pause(); }
    function playRange(a, b) { stopAt = b != null ? b : null; seek(a + 0.01, true); }
    function jump(dir) {   // ← →: the shot before or after (the parts of the outline, or 5 s, when there are no shots)
      const t = v.currentTime || 0;
      let marks = shots().map((s) => s.t);
      if (!marks.length) marks = segs().map((s) => s.t);
      if (!marks.length) return seek(t + dir * 5);
      marks = [0, ...marks].sort((a, b) => a - b);
      const next = dir > 0 ? marks.find((m) => m > t + 0.05) : [...marks].reverse().find((m) => m < t - 0.4);
      seek(next != null ? next : dir > 0 ? dur() : 0, !v.paused);
    }
    function at(e) { const r = ruler.getBoundingClientRect(); return Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * dur(); }
    function showTip(t) {
      if (!tip) return;
      const sh = shots().filter((s) => s.t <= t + 1e-3).pop(), sg = segs().find((s) => t >= s.t && t < s.t1);
      const label = sh ? `${sh.id}${sh.label ? " · " + sh.label : ""}` : sg ? sg.label : "";
      const parts = [];   // nodes, never markup: a frame's address and a label are the project's words
      if (sh && sh.frame) { const im = document.createElement("img"); im.alt = ""; im.src = sh.frame; parts.push(im); }
      const at = document.createElement("span"); at.textContent = clock(t); parts.push(at);
      if (label) { const l = document.createElement("span"); l.textContent = label; parts.push(document.createTextNode(" "), l); }
      tip.replaceChildren(...parts);
      tip.style.left = Math.min(Math.max(pct(t), 8), 92) + "%";
    }
    v.addEventListener("loadedmetadata", () => { laid = 0; layout(); if (span0 != null && !v.currentTime) seek(span0); });
    v.addEventListener("durationchange", layout);
    v.addEventListener("timeupdate", () => { if (stopAt != null && v.currentTime >= stopAt - 0.03) { v.pause(); stopAt = span1; } update(); });
    v.addEventListener("play", () => el.classList.add("playing"));
    v.addEventListener("pause", () => el.classList.remove("playing"));
    well.addEventListener("click", (e) => { e.preventDefault(); toggle(); });
    const pb = $(".p-play", el); if (pb) pb.addEventListener("click", toggle);
    const mb = $(".p-mute", el); if (mb) mb.addEventListener("click", () => { v.muted = !v.muted; mb.style.opacity = v.muted ? 0.45 : 1; });
    const fb = $(".p-full", el);
    if (fb) fb.addEventListener("click", () => { if (document.fullscreenElement) document.exitFullscreen(); else if (well.requestFullscreen) well.requestFullscreen(); else if (v.webkitEnterFullscreen) v.webkitEnterFullscreen(); });
    ruler.addEventListener("pointerdown", (e) => {
      const mk = e.target.closest(".r-mark"); if (mk) { seek(+mk.dataset.t, true); return; }
      dragging = true; ruler.classList.add("drag"); ruler.setPointerCapture(e.pointerId); stopAt = span1; seek(at(e)); showTip(at(e));
    });
    ruler.addEventListener("pointermove", (e) => { const t = at(e); showTip(t); if (dragging) seek(t); });
    const end = () => { dragging = false; ruler.classList.remove("drag"); };
    ruler.addEventListener("pointerup", end); ruler.addEventListener("pointercancel", end);
    ruler.addEventListener("keydown", (e) => {
      if (e.key === "ArrowLeft" || e.key === "ArrowRight") { e.preventDefault(); e.stopPropagation(); seek((v.currentTime || 0) + (e.key === "ArrowRight" ? 1 : -1) * (e.shiftKey ? 5 : 1)); }
      else if (e.key === "Home") { e.preventDefault(); seek(0); } else if (e.key === "End") { e.preventDefault(); seek(dur()); }
    });
    layout(); update();
    return { el, video: v, seek, toggle, playRange, jump, onTime: (f) => listeners.push(f) };
  }

  /* ---------- the light table ---------- */
  function gallery(g) {
    const img = $(".gal-main img", g), a = $(".gal-main", g), cap = $(".gal-cap", g);
    $$(".gal-strip button", g).forEach((b) => b.addEventListener("click", () => {
      img.src = b.dataset.src; a.href = b.dataset.src;
      const c = $(".gal-cap-src", b);   // the caption as the page wrote it (review.py escapes it): copied as nodes
      if (cap) cap.replaceChildren(...(c ? Array.from(c.cloneNode(true).childNodes) : []));
      $$(".gal-strip button", g).forEach((x) => x.setAttribute("aria-current", x === b ? "true" : "false"));
    }));
  }

  /* ---------- copy a reply (the static page) ---------- */
  function copy(text, btn) {
    const label = btn.textContent, done = () => { btn.textContent = btn.dataset.done || "✓"; setTimeout(() => { btn.textContent = label; }, 1400); };
    const old = () => { const t = document.createElement("textarea"); t.value = text; document.body.appendChild(t); t.select(); try { document.execCommand("copy"); done(); } catch (e) { /* nothing to do */ } t.remove(); };
    try { navigator.clipboard.writeText(text).then(done, old); } catch (e) { old(); }
  }

  /* ---------- a gate view ---------- */
  let keyOwner = null;   // one gate view answers the keyboard at a time: the one mounted last
  function mount(root, hooks) {
    hooks = hooks || {};
    const players = $$(".player", root).map(Player);
    const main = players.find((p) => p.el.closest(".g-stage")) || players[0] || null;
    const decs = $$(".g-dec", root);
    let active = decs[0] || null;
    const setActive = (d) => { active = d; decs.forEach((x) => x.classList.toggle("active", x === d)); };
    setActive(active);
    $$(".gallery", root).forEach(gallery);
    const lead = $(".g-lead[data-long]", root);
    if (lead) lead.addEventListener("click", () => lead.classList.toggle("open"));

    // the picks: the recommendation is checked to begin with; hooks.initial (the console's draft) comes on top
    // a decision the person picked (data-picked) is framed; one left alone shows the recommendation as its default, unframed
    Object.entries(hooks.initial || {}).forEach(([id, v]) => { const r = $$(`.g-dec[data-dec] input[type=radio]`, root).find((x) => x.closest(".g-dec").dataset.dec === id && x.value === v); if (r) { r.checked = true; r.closest(".g-dec").dataset.picked = "1"; } });
    const choices = () => { const o = {}; decs.forEach((d) => { const r = $("input:checked", d); if (r) o[d.dataset.dec] = r.value; }); return o; };
    const reply = () => decs.map((d, i) => { const r = $("input:checked", d); return r ? `${i + 1} ${r.value}` : ""; }).filter(Boolean).join(" · ");
    function refreshReply() {
      const k = $(".g-reply-k", root), v = $(".g-reply-v", root); if (!k || !v) return;
      if (k.dataset.take == null) k.dataset.take = k.textContent;
      const r = reply(); v.textContent = r;
      k.textContent = r === root.dataset.takeall ? k.dataset.take : k.dataset.yours || k.dataset.take;
      k.classList.toggle("changed", r !== root.dataset.takeall);
    }
    decs.forEach((d, i) => {
      d.addEventListener("focusin", () => setActive(d));
      d.addEventListener("pointerdown", () => setActive(d));
      $$("input[type=radio]", d).forEach((r) => r.addEventListener("change", () => {
        d.dataset.picked = "1"; setActive(d); refreshReply();
        if (hooks.onPick) hooks.onPick(d.dataset.dec, r.value, r.value === d.dataset.rec);
        const next = decs[i + 1]; if (next && hooks.advance !== false) setActive(next);
      }));
    });
    refreshReply();
    const cb = $(".g-copy", root); if (cb) cb.addEventListener("click", () => copy($(".g-reply-v", root).textContent, cb));
    const sb = $(".g-submit", root); if (sb && hooks.onSubmit) sb.addEventListener("click", () => hooks.onSubmit(choices()));

    // times: every [data-seek] plays the main film from there; a shot's picture plays that shot
    root.addEventListener("click", (e) => {
      const s = e.target.closest("[data-seek]");
      if (s && main) { e.preventDefault(); main.seek(+s.dataset.seek, true); main.el.scrollIntoView({ block: "nearest", behavior: "smooth" }); return; }
      const w = e.target.closest(".g-shot .well");
      if (w && main) { const f = w.closest(".g-shot"); if (f.dataset.t != null) { e.preventDefault(); main.playRange(+f.dataset.t, f.dataset.t1 != null ? +f.dataset.t1 : null); main.el.scrollIntoView({ block: "nearest", behavior: "smooth" }); } }
    });
    if (main) {
      const cards = $$(".g-shot[data-t]", root), rows = $$(".g-marks li[data-t]", root);
      main.onTime((t) => {
        cards.forEach((c) => c.classList.toggle("active", t >= +c.dataset.t && (c.dataset.t1 == null || t < +c.dataset.t1) && !main.video.paused));
        rows.forEach((r) => r.classList.toggle("on", Math.abs(+r.dataset.t - t) < 1.2));
      });
    }

    const keys = (e) => {
      if (keyOwner !== ctl || e.metaKey || e.ctrlKey || e.altKey || typing(document.activeElement)) return;
      if (hooks.keys && hooks.keys(e) === false) return;
      if (e.key === " " && main && !(document.activeElement && /^(BUTTON|A|SUMMARY)$/.test(document.activeElement.tagName)) && (document.activeElement || {}).type !== "radio") { e.preventDefault(); main.toggle(); }
      else if ((e.key === "ArrowLeft" || e.key === "ArrowRight") && main && (document.activeElement || {}).type !== "radio") { e.preventDefault(); main.jump(e.key === "ArrowRight" ? 1 : -1); }
      else if (/^[1-9]$/.test(e.key) && active) {
        const r = $$("input[type=radio]", active)[+e.key - 1];
        if (r) { e.preventDefault(); r.checked = true; r.dispatchEvent(new Event("change", { bubbles: true })); r.focus({ preventScroll: true }); }
      }
    };
    document.addEventListener("keydown", keys);
    const own = () => { keyOwner = ctl; };   // the view last touched answers the keys (the console mounts two: a module's page and its right column)
    root.addEventListener("focusin", own); root.addEventListener("pointerdown", own);
    const ctl = { root, players, main, choices, reply, own, destroy() { document.removeEventListener("keydown", keys); players.forEach((p) => p.video.pause()); if (keyOwner === ctl) keyOwner = null; } };
    keyOwner = ctl;
    return ctl;
  }

  window.OVH = { mount, Player, theme, clock, THEMES, DEFAULT_THEME };
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-theme-set]"); if (b) theme(b.dataset.themeSet);
    document.querySelectorAll("details.tmenu[open]").forEach((d) => { if (b || !d.contains(e.target)) d.open = false; });   // a pick, or a click elsewhere, closes the menu
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") document.querySelectorAll("details.tmenu[open]").forEach((d) => { d.open = false; }); });
  document.addEventListener("change", (e) => { if (e.target.matches("select[data-theme-select]")) theme(e.target.value); });
  document.addEventListener("DOMContentLoaded", () => theme(document.documentElement.getAttribute("data-theme")));
  const auto = document.querySelector(".gate[data-static]");
  if (auto) mount(auto);
})();
