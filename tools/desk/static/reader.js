// The reader (GET /v/<key>/<path>): one project file on its own page, in the theme the console uses. In Studio's own app
// (ovhShell) the page marks itself, and its slim bar is what the window is dragged by, with room for the window buttons.
(() => {
  const r = document.documentElement;
  let t = "";
  try { t = localStorage.getItem("ovh-theme") || ""; } catch (e) { /* no storage: the default theme */ }
  if (/^(darkfield|prism|bridge)$/.test(t)) r.setAttribute("data-theme", t);
  if (window.ovhShell) r.classList.add("shell", window.ovhShell.platform === "mac" ? "shell-mac" : "shell-other");
})();
