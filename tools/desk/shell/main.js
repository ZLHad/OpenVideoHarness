// Studio's window of its own: an Electron shell around the console page (tools/desk/README.md, "打开 Studio").
// OVH Studio.app (bin/vh studio --install-icon) runs this file from the clone, so a git pull changes it with no reinstall.
//
// How it is reached: the console starts this program with --ovh-from-console and one line of JSON on stdin,
//   {url, role, w}: url is the console page with a one-time code; role names the desk (one window a desk); w is the
//   window's id for the console's presence stream.
// Access: this process trades the code for the console's token itself (POST /api/claim) and keeps the token in memory
// alone; it adds it to the page's own requests to that console (X-Desk-Token) and the page holds only a placeholder
// ("shell"). So the token is in no command line, no page, no storage and no file. A second start (the console again, a second click) hands its line
// to the running one through Electron's single-instance lock and exits: one app, one window a desk, raised by itself.
// Started by a click (no stdin), it asks the clone to show Studio (bin/vh studio --icon open), which starts it as above.
// {close: role} closes that desk's window (the desk is stopping); with no window left, the app quits.
// Quitting it: the console the icon started stops too (bin/vh studio --icon quit; it asks first while an agent is mid-turn).
"use strict";
const { app, BrowserWindow, Menu, dialog, ipcMain, net, shell, session } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");

const T = (zh, en) => (/^zh/i.test((app.isReady() && app.getLocale()) || Intl.DateTimeFormat().resolvedOptions().locale || "") ? zh : en);
const MAC = process.platform === "darwin";
// where the window buttons sit in each theme's top bar (macOS): the bar is 52 px high, inside 8 px (棱镜) or 6 px (舰桥)
const BUTTONS = { darkfield: { x: 18, y: 19 }, prism: { x: 22, y: 27 }, bridge: { x: 20, y: 25 } };
const BG = { darkfield: "#111111", prism: "#04060b", bridge: "#06080a" };

let opts = { repo: path.resolve(__dirname, "..", "..", ".."), env: {} };
const windows = new Map();   // role → BrowserWindow
const access = new Map();    // a console's origin → its token: in this process's memory and nowhere else
let quitting = false;

function settingsPath() { return path.join(app.getPath("userData"), "ovh-studio.json"); }
function settings() { try { return JSON.parse(fs.readFileSync(settingsPath(), "utf8")); } catch (e) { return {}; } }
function save(patch) {
  try { fs.writeFileSync(settingsPath(), JSON.stringify(Object.assign(settings(), patch))); } catch (e) { /* no state then */ }
}

function vh(args, done) {   // bin/vh in the clone, with the PATH the installer saw (an app started by the Dock has the bare one)
  const env = Object.assign({}, process.env, opts.env);
  delete env.ELECTRON_RUN_AS_NODE;
  let out = "";
  const p = spawn(path.join(opts.repo, "bin", "vh"), args, { cwd: opts.repo, env, stdio: ["ignore", "pipe", "pipe"] });
  p.stdout.on("data", (d) => { out += d; });
  p.stderr.on("data", (d) => { out += d; });
  p.on("error", (e) => done(127, String(e)));
  p.on("close", (code) => done(code, out.trim()));
}

function originOf(u) { try { return new URL(u).origin; } catch (e) { return ""; } }

async function claim(url) {   // the window's one-time code traded here, not by the page → the address without it
  let u;
  try { u = new URL(url); } catch (e) { return url; }
  const c = u.searchParams.get("c");
  u.searchParams.delete("c");
  if (c) {
    try {
      const r = await net.fetch(u.origin + "/api/claim", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ c }) });
      const d = await r.json().catch(() => ({}));
      if (r.ok && typeof d.token === "string") access.set(u.origin, d.token);
    } catch (e) { /* the console is gone: the page says so */ }
  }
  return u.toString();
}

function guard(ses) {   // the token on the console page's own requests to its console; never on anything else
  ses.webRequest.onBeforeSendHeaders({ urls: ["http://127.0.0.1/*", "http://127.0.0.1:*/*"] }, (d, cb) => {
    const h = d.requestHeaders;
    for (const k of Object.keys(h)) if (k.toLowerCase() === "x-desk-token") delete h[k];
    const t = access.get(originOf(d.url));
    const ours = [...windows.values()].some((w) => !w.isDestroyed() && w.webContents.id === d.webContentsId);
    const top = !d.frame || !d.frame.parent;   // the page itself, not a project's file inside it
    if (t && ours && top) h["X-Desk-Token"] = t;
    cb({ requestHeaders: h });
  });
}

function makeWindow(role, url) {
  const s = settings();
  const theme = BG[s.theme] ? s.theme : "darkfield";
  const b = s.bounds && s.bounds.width >= 900 ? s.bounds : { width: 1440, height: 900 };
  const win = new BrowserWindow({
    width: b.width, height: b.height, x: b.x, y: b.y, minWidth: 900, minHeight: 600,
    show: false, backgroundColor: s.bg || BG[theme], title: "Studio",
    titleBarStyle: "hidden",
    ...(MAC ? { trafficLightPosition: BUTTONS[theme] } : { titleBarOverlay: { color: s.bg || BG[theme], symbolColor: "#b4b0a8", height: 52 } }),
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true, nodeIntegration: false, sandbox: true, webSecurity: true,
      allowRunningInsecureContent: false, spellcheck: false, webviewTag: false, navigateOnDragDrop: false,
    },
  });
  const origin = originOf(url);
  win.once("ready-to-show", () => { win.show(); win.focus(); });
  win.webContents.on("will-navigate", (e, to) => {   // the console's own pages only; anything else in the default browser
    if (originOf(to) !== origin) { e.preventDefault(); if (/^https?:/.test(to)) shell.openExternal(to); }
  });
  win.webContents.setWindowOpenHandler(({ url: to }) => { if (/^https?:/.test(to)) shell.openExternal(to); return { action: "deny" }; });
  win.on("close", () => { if (!win.isFullScreen()) save({ bounds: win.getBounds() }); });
  win.on("enter-full-screen", () => win.webContents.send("ovh:fullscreen", true));
  win.on("leave-full-screen", () => win.webContents.send("ovh:fullscreen", false));
  win.on("closed", () => { if (windows.get(role) === win) windows.delete(role); });
  windows.set(role, win);
  win.loadURL(url);
  return win;
}

function raise(win) {
  if (win.isMinimized()) win.restore();
  win.show();
  win.focus();
  if (MAC) app.focus({ steal: true });
}

function handle(msg) {   // a line from the console: show a desk's window, or close it
  if (!msg || typeof msg !== "object") return;
  if (typeof msg.close === "string") {
    const w = windows.get(msg.close);
    if (w && !w.isDestroyed()) w.destroy();
    if (!windows.size) { quitting = true; app.exit(0); }
    return;
  }
  if (typeof msg.url !== "string" || !/^http:\/\/127\.0\.0\.1:\d+\//.test(msg.url)) return;
  const role = typeof msg.role === "string" ? msg.role : "console";
  const win = windows.get(role);
  if (win && !win.isDestroyed() && originOf(win.webContents.getURL()) === originOf(msg.url) && !msg.fresh) { raise(win); return; }
  claim(msg.url).then((url) => {   // a new window, or the same one on a console started again
    const w = windows.get(role);
    if (w && !w.isDestroyed()) { w.loadURL(url); raise(w); } else makeWindow(role, url);
  });
}

function readStdin(done) {   // one line of JSON from the console that started this
  let buf = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (d) => { buf += d; });
  process.stdin.on("end", () => { try { done(JSON.parse(buf.trim() || "null")); } catch (e) { done(null); } });
  process.stdin.on("error", () => done(null));
}

function askClone() {   // a click: ask the clone to show Studio; it starts this program again with the console's line
  vh(["studio", "--icon", "open"], (code, out) => {
    if (code !== 0 && !windows.size) {
      dialog.showMessageBoxSync({ type: "warning", buttons: [T("好", "OK")], message: T("Studio 没有打开", "Studio did not open"),
        detail: out.split("\n").slice(-3).join("\n") });
      quitting = true;
      app.exit(1);
    }
  });
}

function menu() {
  const m = [
    ...(MAC ? [{ label: "OVH Studio", submenu: [
      { role: "about", label: T("关于 OVH Studio", "About OVH Studio") }, { type: "separator" },
      { role: "hide", label: T("隐藏 OVH Studio", "Hide OVH Studio") }, { role: "hideOthers", label: T("隐藏其他", "Hide Others") },
      { role: "unhide", label: T("全部显示", "Show All") }, { type: "separator" },
      { role: "quit", label: T("退出 OVH Studio", "Quit OVH Studio") }] }] : []),
    { label: T("编辑", "Edit"), submenu: [
      { role: "undo", label: T("撤销", "Undo") }, { role: "redo", label: T("重做", "Redo") }, { type: "separator" },
      { role: "cut", label: T("剪切", "Cut") }, { role: "copy", label: T("拷贝", "Copy") }, { role: "paste", label: T("粘贴", "Paste") },
      { role: "selectAll", label: T("全选", "Select All") }] },
    { label: T("显示", "View"), submenu: [
      { role: "reload", label: T("重新载入", "Reload") }, { type: "separator" },
      { role: "resetZoom", label: T("实际大小", "Actual Size") }, { role: "zoomIn", label: T("放大", "Zoom In") },
      { role: "zoomOut", label: T("缩小", "Zoom Out") }, { type: "separator" },
      { role: "togglefullscreen", label: T("进入全屏", "Toggle Full Screen") }] },
    { label: T("窗口", "Window"), submenu: [
      { role: "minimize", label: T("最小化", "Minimize") }, { role: "zoom", label: T("缩放", "Zoom") },
      ...(MAC ? [{ type: "separator" }, { role: "front", label: T("前置全部窗口", "Bring All to Front") }] : [{ role: "close", label: T("关闭", "Close") }])] },
    ...(MAC ? [] : [{ label: T("文件", "File"), submenu: [{ role: "quit", label: T("退出", "Quit") }] }]),
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(m));
}

function start(given) {
  opts = Object.assign(opts, given || {});
  app.setName("OVH Studio");
  if (process.env.OVH_STUDIO_SHELL_PROFILE) app.setPath("userData", process.env.OVH_STUDIO_SHELL_PROFILE);   // the checks' own
  const fromConsole = process.argv.includes("--ovh-from-console");
  const go = (msg) => {
    if (!app.requestSingleInstanceLock(msg ? { line: msg } : {})) { app.exit(0); return; }   // the running one has it now
    app.on("second-instance", (_e, _argv, _cwd, data) => {
      if (data && data.line) handle(data.line);
      else { const w = [...windows.values()].find((x) => !x.isDestroyed()); if (w) raise(w); else askClone(); }
    });
    app.whenReady().then(() => {
      session.defaultSession.setPermissionRequestHandler((_wc, _perm, cb) => cb(false));   // no camera, microphone, location …
      guard(session.defaultSession);
      app.setAboutPanelOptions({ applicationName: "OVH Studio", applicationVersion: "Electron " + process.versions.electron,
        copyright: "OpenVideoHarness", credits: T("Studio：看片子、审一站、和本机的 agent 说话。", "Studio: every film, each stop, the agents on this machine.") });
      menu();
      if (msg) handle(msg); else askClone();
    });
  };
  if (fromConsole) readStdin(go); else go(null);

  app.on("web-contents-created", (_e, wc) => { wc.on("will-attach-webview", (ev) => ev.preventDefault()); });
  app.on("activate", () => {   // a click on the Dock icon while it runs
    const w = [...windows.values()].find((x) => !x.isDestroyed());
    if (w) raise(w); else askClone();
  });
  app.on("window-all-closed", () => {   // closing the window leaves the console running: a Mac keeps the app, Linux ends it
    if (!MAC) { quitting = true; app.exit(0); }
  });
  app.on("before-quit", (e) => {   // a quit by the person: the console the icon started goes too (asked first mid-turn)
    if (quitting) return;
    e.preventDefault();
    vh(["studio", "--icon", "quit"], (code, out) => {
      if (code === 3) {
        const r = dialog.showMessageBoxSync({ type: "warning", buttons: [T("继续开着", "Keep it open"), T("退出", "Quit")], defaultId: 0, cancelId: 0,
          message: T("Studio 里的 agent 正在做事", "An agent in Studio is at work"), detail: T("退出会让它停下。", "Quitting stops it.") });
        if (r === 0) return;
        return vh(["studio", "--icon", "quit", "--force"], () => { quitting = true; app.exit(0); });
      }
      quitting = true;
      app.exit(0);
    });
  });
  ipcMain.on("ovh:theme", (e, name, bg) => {   // the page's theme: the window's colour, and where its buttons sit
    const win = BrowserWindow.fromWebContents(e.sender);
    if (!win || typeof name !== "string") return;
    const colour = /^#[0-9a-fA-F]{3,8}$/.test(bg || "") ? bg : BG[name] || BG.darkfield;
    win.setBackgroundColor(colour);
    if (MAC && BUTTONS[name] && win.setWindowButtonPosition) win.setWindowButtonPosition(BUTTONS[name]);
    if (!MAC && win.setTitleBarOverlay) win.setTitleBarOverlay({ color: colour });
    save({ theme: BG[name] ? name : "darkfield", bg: colour });
  });
}

module.exports = { start };
if (require.main === module) start();   // electron <this folder>: a run from the clone without the app (development)
