// Studio's window of its own: an Electron shell around the console page (tools/desk/README.md, "打开 Studio").
// OVH Studio.app (bin/vh studio --install-icon) runs this file from the clone, so a git pull changes it with no reinstall.
//
// How it is reached: the console starts this program with --ovh-from-console and one line of JSON on stdin,
//   {url, role, w}: url is the console page with a one-time code; role names the desk (one window a desk); w is the
//   window's id for the console's presence stream.
// Access: this process trades the code for the console's token itself (POST /api/claim) and keeps the token in memory
// alone, tied to the window it was traded for; it adds it (X-Desk-Token) to that window's own page's requests to that same
// console (rules.tokenFor), and the page holds only a placeholder ("shell"). So the token is in no command line, no page,
// no storage and no file. A link that opens a new page of the same console opens in a reader window of the app's own
// (rules.readerUrl: a project file through the console's reader, /v/, so it never shows empty; no system title bar, no
// token, closing with its opener); other sites open in the default browser. A second start (the console again, a
// second click) hands its line to the running one through Electron's single-instance lock and exits: one app, one
// window a desk, raised by itself.
// Started by a click (no stdin), it asks the clone to show Studio (bin/vh studio --icon open), which starts it as above.
// {close: role} closes that desk's window (the desk is stopping); with no window left, the app quits. {quit: true}: the app
// quits (bin/vh studio --remove-icon, before it takes the app away). Any local program can hand the app a line: a window
// whose console still answers with the app's token is never pointed at another console (rules.show).
// Quitting it: the console the icon started stops too (bin/vh studio --icon quit; it asks first while an agent is mid-turn).
"use strict";
const { app, BrowserWindow, Menu, dialog, ipcMain, net, shell, session } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const R = require("./rules.js");   // the decisions, which plain node checks (tools/ci.sh)

const T = (zh, en) => (/^zh/i.test((app.isReady() && app.getLocale()) || Intl.DateTimeFormat().resolvedOptions().locale || "") ? zh : en);
const MAC = process.platform === "darwin";
// where the window buttons sit in each theme's top bar (macOS): the bar is 52 px high, inside 8 px (棱镜) or 6 px (舰桥)
const BUTTONS = { darkfield: { x: 18, y: 19 }, prism: { x: 22, y: 27 }, bridge: { x: 20, y: 25 } };
const BG = { darkfield: "#111111", prism: "#04060b", bridge: "#06080a" };

let opts = { repo: path.resolve(__dirname, "..", "..", ".."), env: {} };
const windows = new Map();   // role → BrowserWindow (one a desk)
const access = new Map();    // role → {origin, token}: what the app traded that window's code for, in this process's memory alone
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

const live = (role) => { const w = windows.get(role); return w && !w.isDestroyed() ? w : null; };
const roleOf = (id) => { for (const [r, w] of windows) if (!w.isDestroyed() && w.webContents.id === id) return r; return null; };

async function claim(url) {   // the window's one-time code traded here, not by the page → {url without it, token or ""}
  let u;
  try { u = new URL(url); } catch (e) { return { url, token: "" }; }
  const c = u.searchParams.get("c");
  u.searchParams.delete("c");
  let token = "";
  if (c) {
    try {
      const r = await net.fetch(u.origin + "/api/claim", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ c }) });
      const d = await r.json().catch(() => ({}));
      if (r.ok && typeof d.token === "string") token = d.token;
    } catch (e) { /* the console is gone: the page says so */ }
  }
  return { url: u.toString(), token };
}

async function answers(a) {   // does the console this window shows still take the app's token?
  if (!a || !a.token) return false;
  try { return (await net.fetch(a.origin + "/api/hello", { headers: { "X-Desk-Token": a.token }, cache: "no-store" })).status === 200; } catch (e) { return false; }
}

function guard(ses) {   // the token on a console page's own requests to its own console (rules.tokenFor); never on anything else
  ses.webRequest.onBeforeSendHeaders({ urls: ["http://127.0.0.1/*", "http://127.0.0.1:*/*"] }, (d, cb) => {
    const h = d.requestHeaders;
    if (d.webContentsId === undefined) return cb({ requestHeaders: h });   // the app's own (its code trade, its check)
    for (const k of Object.keys(h)) if (k.toLowerCase() === "x-desk-token") delete h[k];
    const role = roleOf(d.webContentsId);
    const t = role && R.tokenFor(access.get(role), d.url, windows.get(role).webContents.getURL(), !d.frame || !d.frame.parent);
    if (t) h["X-Desk-Token"] = t;
    cb({ requestHeaders: h });
  });
}

function rules(win) {   // where its page may go (decided against the page it shows now), and where a new page opens
  win.webContents.on("will-navigate", (e, to) => {
    const n = R.navigation(win.webContents.getURL(), to);
    if (n !== "stay") { e.preventDefault(); if (n === "browser") shell.openExternal(to); }
  });
  win.webContents.setWindowOpenHandler(({ url: to }) => {
    const n = R.newPage(win.webContents.getURL(), to);
    if (n === "browser") shell.openExternal(to);
    if (n === "inside") reader(win, R.readerUrl(win.webContents.getURL(), to));
    return { action: "deny" };
  });
}

function reader(opener, url) {   // a page of the same console in a window of the app's own: no system title bar, the theme's
  // ground, the reader's slim bar to drag by with the buttons in it and the file's name as the window's; no token (the
  // reader and project files need none); it goes with the window that opened it, and ⌘W closes it
  const s = settings(), bg = s.bg || BG[BG[s.theme] ? s.theme : "darkfield"];
  const win = new BrowserWindow({
    width: 1100, height: 820, minWidth: 520, minHeight: 360, show: false, backgroundColor: bg, title: "",
    titleBarStyle: "hidden",
    ...(MAC ? { trafficLightPosition: { x: 14, y: 13 } } : { titleBarOverlay: { color: bg, symbolColor: "#b4b0a8", height: 38 } }),
    webPreferences: Object.assign({ preload: path.join(__dirname, "preload.js") }, HARD),
  });
  win.once("ready-to-show", () => { win.show(); win.focus(); });
  rules(win);
  opener.once("closed", () => { if (!win.isDestroyed()) win.destroy(); });
  win.loadURL(url);
}
const HARD = { contextIsolation: true, nodeIntegration: false, sandbox: true, webSecurity: true, allowRunningInsecureContent: false,
  spellcheck: false, webviewTag: false, navigateOnDragDrop: false };

function makeWindow(role, url) {
  const s = settings();
  const theme = BG[s.theme] ? s.theme : "darkfield";
  const b = s.bounds && s.bounds.width >= 900 ? s.bounds : { width: 1440, height: 900 };
  const win = new BrowserWindow({
    width: b.width, height: b.height, x: b.x, y: b.y, minWidth: 900, minHeight: 600,
    show: false, backgroundColor: s.bg || BG[theme], title: "Studio",
    titleBarStyle: "hidden",
    ...(MAC ? { trafficLightPosition: BUTTONS[theme] } : { titleBarOverlay: { color: s.bg || BG[theme], symbolColor: "#b4b0a8", height: 52 } }),
    webPreferences: Object.assign({ preload: path.join(__dirname, "preload.js") }, HARD),
  });
  win.once("ready-to-show", () => { win.show(); win.focus(); });
  rules(win);
  win.on("close", () => { if (!win.isFullScreen()) save({ bounds: win.getBounds() }); });
  win.on("enter-full-screen", () => win.webContents.send("ovh:fullscreen", true));
  win.on("leave-full-screen", () => win.webContents.send("ovh:fullscreen", false));
  win.on("closed", () => { if (windows.get(role) === win) { windows.delete(role); access.delete(role); } });
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

async function handle(raw) {   // a line from the console: show a desk's window, close it, or quit (rules.line)
  const msg = R.line(raw);
  if (!msg) return;
  if (msg.quit) { quitting = true; app.exit(0); return; }
  if (msg.close) {
    const w = live(msg.close);
    if (w) w.destroy();
    if (!windows.size) { quitting = true; app.exit(0); }
    return;
  }
  const role = msg.role, win = live(role), old = access.get(role);
  const act = R.show(win && win.webContents.getURL(), msg);
  if (act === "raise") { raise(win); return; }
  // another console's address: taken only when the console this window shows no longer answers (any local program can
  // hand the app a line; it never points a working window elsewhere)
  if (act === "check" && await answers(old)) { raise(win); return; }
  const got = await claim(msg.url);
  if (act === "load" && !got.token && await answers(old)) { raise(win); return; }   // a fresh address whose code did not trade: keep what works
  if (got.token) access.set(role, { origin: R.originOf(msg.url), token: got.token });
  else access.delete(role);
  const w = live(role);
  if (w) { w.loadURL(got.url); raise(w); } else makeWindow(role, got.url);
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
        detail: T("再点一次 OVH Studio 图标；还是不行，就让 agent 打开 Studio，它会说是哪里出了问题。",
          "Click the OVH Studio icon again; if it still does not open, ask your agent to open Studio, and it will say what went wrong.") });
      quitting = true;
      app.exit(1);
    }
  });
}

function openSettings(_item, focused) {   // the menu's 设置… (⌘,): the window in front goes to Studio's settings page, in place
  const win = focused && !focused.isDestroyed() ? focused : BrowserWindow.getFocusedWindow();
  if (!win) return;
  try {
    const u = new URL(win.webContents.getURL());
    if (u.protocol !== "http:" || !["/", "/index.html"].includes(u.pathname)) return;   // a reader window: no settings there
    u.hash = "/settings";
    win.webContents.loadURL(u.href);   // only the part after # changes: the page stays and follows its hash
  } catch (e) { /* no page yet */ }
}

function menu() {
  const m = [
    ...(MAC ? [{ label: "OVH Studio", submenu: [
      { role: "about", label: T("关于 OVH Studio", "About OVH Studio") }, { type: "separator" },
      { label: T("设置…", "Settings…"), accelerator: "CmdOrCtrl+,", click: openSettings }, { type: "separator" },
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
      { role: "close", label: T("关闭窗口", "Close Window") },   // ⌘W / Ctrl+W
      ...(MAC ? [{ type: "separator" }, { role: "front", label: T("前置全部窗口", "Bring All to Front") }] : [])] },
    ...(MAC ? [] : [{ label: T("文件", "File"), submenu: [{ label: T("设置…", "Settings…"), accelerator: "CmdOrCtrl+,", click: openSettings }, { type: "separator" }, { role: "quit", label: T("退出", "Quit") }] }]),
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
      // full screen for the console's own page (the player's button); no camera, microphone, location or anything else
      session.defaultSession.setPermissionRequestHandler((wc, perm, cb, d) => cb(R.permission(perm, (d && d.requestingUrl) || wc.getURL(), wc.getURL())));
      guard(session.defaultSession);
      app.setAboutPanelOptions({ applicationName: "OVH Studio", applicationVersion: "Electron " + process.versions.electron,
        copyright: "OpenVideoHarness", credits: T("Studio：看你的每支片子，在每一站拍板，和这台电脑上的 agent 说话。", "Studio: see each film, decide at each stop, and talk to the agents on this computer.") });
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
