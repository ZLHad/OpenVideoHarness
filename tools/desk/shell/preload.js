// The shell's preload (main.js): the least the page needs, and nothing else crosses over. The page (ui.js, which loads in
// its <head>, before the first paint) sees ovhShell, marks itself as running in Studio's own window (the top bar then
// leaves room for the window buttons and is what the window is dragged by), and tells the window its theme (the window's
// colour and where its buttons sit). Full screen hides the buttons; the page is told so. access: the app holds the
// console's token and adds it to the page's requests, so the page uses a placeholder and never sees or stores the token.
"use strict";
const { contextBridge, ipcRenderer } = require("electron");

ipcRenderer.on("ovh:fullscreen", (_e, on) => { const r = document.documentElement; if (r) r.classList.toggle("shell-full", !!on); });

contextBridge.exposeInMainWorld("ovhShell", {
  platform: process.platform === "darwin" ? "mac" : "other",
  access: true,
  theme: (name, bg) => ipcRenderer.send("ovh:theme", String(name || ""), String(bg || "")),
});
