"use strict";
/* A static review page (bin/vh review, opened from disk with no server) as the read-only version of its stop's module: the
   console's own renderers (modules.js) and helpers (core.js), drawn from the data tools/review.py wrote into the page
   (a JSON script element, #ovh-data). There is no note box and nothing is sent: a decision is picked on the
   gate view under the module, or on the module's own cards, which pick the same option there, and the gate view copies the
   reply. Without JavaScript, or without that data (an old page, a project that could not be read), the page is the gate
   view alone, as it was. */
const STATIC_PAGE = true;   // modules.js: read only
let D = null, PKEY = "", SUB = "", MOD = "", REL = "", VIEWS = [];
let FB = { decisions: {}, items: {}, general: "" }, ROUND = { id: "", data: {} };
const src = (p) => (/^https?:\/\//.test(p || "") ? p : REL + String(p || "").split("/").map(enc).join("/"));   // the project's files, from the page's folder
const setScope = () => {}, gotoTarget = () => {};
const roundOpen = () => { const r = gateRoot(); return !(r && r.hasAttribute("data-settled")); };   // open, picking builds the reply to copy; a page of a stop settled since, a record
const gateMarks = () => (D && D.marks) || [];
const gateRoot = () => document.querySelector(".gate[data-static]");
function follow(dec, val) { FB.decisions[dec] = val; VIEWS.forEach((m) => { const V = MODVIEW[m]; if (V.sync) V.sync(dec, val); }); }
function pick(dec, val) {   // a card picked on the module: the same option on the gate view, whose reply follows
  const root = gateRoot(), r = root && [...root.querySelectorAll(".g-dec input[type=radio]")].find((x) => x.name === "dec-" + dec && x.value === val);
  if (r && !r.checked) { r.checked = true; r.dispatchEvent(new Event("change", { bubbles: true })); }
  follow(dec, val);
}
function renderModule() {
  const host = document.getElementById("spMod"); if (!host) return;
  host.innerHTML = VIEWS.map((m) => { MOD = m; return `<section class="m2" data-mod="${m}">${MODVIEW[m].main()}</section>`; }).join("");
  VIEWS.forEach((m) => { MOD = m; const V = MODVIEW[m]; if (V.wire) V.wire(); });
  fitHeads(host);
}
(function boot() {
  const el = document.getElementById("ovh-data"), root = gateRoot();
  if (!el || !root || typeof MODVIEW === "undefined") return;
  let x = null;
  try { x = JSON.parse(el.textContent); } catch (e) { return; }
  D = x && x.data; REL = (x && x.rel) || ""; VIEWS = ((x && x.modules) || []).filter((m) => MODVIEW[m]);
  if (!D || !VIEWS.length) return;
  LANG = x.lang === "en" ? "en" : "zh"; L = STR[LANG];
  ROUND = { id: D.current || "", data: ((D.rounds || []).find((r) => r.id === D.current) || {}).data || {} };
  root.querySelectorAll(".g-dec input[type=radio]:checked").forEach((r) => { FB.decisions[r.name.replace(/^dec-/, "")] = r.value; });   // the recommended, checked as the page loads
  const head = root.querySelector(".g-head"), host = document.createElement("div");
  host.id = "spMod"; host.className = "sp-mod";
  host.addEventListener("error", (e) => { if (e.target.tagName === "IMG") e.target.hidden = true; }, true);   // a picture not there: the letter under it shows
  if (head) root.parentNode.insertBefore(head, root);   // the page's heading first (its stop, what it asks, the spend, a missing file), then the module
  root.parentNode.insertBefore(host, root);
  try { renderModule(); } catch (e) {   // a module that cannot draw this project: the gate view alone, as before
    host.remove(); if (head) root.prepend(head); return;
  }
  VIEWS.forEach((m) => { const V = MODVIEW[m]; if (V.drawn) V.drawn(root, (y) => { y.hidden = true; y.querySelectorAll("[id]").forEach((z) => z.removeAttribute("id")); }); });   // drawn once, in the module (whose cards take the ids the page's links go to); the hidden one still picks
  const unfold = (e) => { const f = e.target.closest(".fold"); if (f && (e.type === "click" || e.key === "Enter")) f.classList.toggle("open"); };
  document.addEventListener("click", unfold); document.addEventListener("keydown", unfold);
  const main = root.querySelector(".g-main");
  if (main && ![...main.children].some((c) => !c.hidden)) {   // nothing of the picture part is left: the decisions and the reply take the width
    main.hidden = true; const b = main.closest(".g-body"); if (b) b.classList.remove("has-side");
  }
  root.addEventListener("change", (e) => { const r = e.target; if (r.type === "radio" && r.name.startsWith("dec-")) follow(r.name.slice(4), r.value); });
  document.documentElement.classList.add("has-mod");
})();
