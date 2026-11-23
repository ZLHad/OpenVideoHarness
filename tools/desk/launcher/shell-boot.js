// OVH Studio: bin/vh studio --install-icon wrote this from tools/desk/launcher/shell-boot.js. It runs Studio's shell
// (tools/desk/shell/main.js) from the clone below, so a git pull changes it with no reinstall.
// The clone gone (moved or deleted): started by the console (--ovh-from-console), it exits at once with 3, no alert, and
// the console falls back to a browser's window and says why; started by a click, one alert (one app at a time), which
// lets the person pick the folder OpenVideoHarness is in now: its bin/vh studio --install-icon makes the app again there
// and opens Studio.
"use strict";
const fs = require("fs"), path = require("path");
const REPO = "@@REPO@@";   // the clone (bin/vh studio --install-icon writes it in)
const ENV = {} /*@@ENV@@*/;   // the PATH the installer saw: an app started by the Dock gets the bare system one
const main = path.join(REPO, "tools", "desk", "shell", "main.js");
if (fs.existsSync(main)) {
  require(main).start({ repo: REPO, env: ENV });
} else if (process.argv.includes("--ovh-from-console")) {
  process.exit(3);   // window.shell_send: "the app no longer finds its clone"
} else {
  const { app, dialog } = require("electron");
  const { spawnSync, spawn } = require("child_process");
  const zh = () => /^zh/i.test(app.getLocale() || "");
  if (!app.requestSingleInstanceLock()) app.exit(0);   // the alert is up already
  app.whenReady().then(() => {
    if (process.platform === "darwin") app.focus({ steal: true });   // in front first: an app not yet active draws its alert half-made
    const t = (a, b) => (zh() ? a : b);
    const r = dialog.showMessageBoxSync({ type: "warning", buttons: [t("找到它…", "Find it…"), t("好", "OK")], defaultId: 0, cancelId: 1,
      message: t("找不到 OpenVideoHarness 了", "OpenVideoHarness is no longer where it was"),
      detail: t("它原来在 " + REPO + "。点“找到它”，选它现在所在的文件夹；或者让 AI 把 Studio 图标重新装一次。",
        "It was at " + REPO + ". Click “Find it” and pick the folder it is in now, or ask the AI you use to put the Studio icon back.") });
    const dir = r === 0 && dialog.showOpenDialogSync({ properties: ["openDirectory"], message: t("OpenVideoHarness 现在所在的文件夹", "The folder OpenVideoHarness is in now") });
    const repo = dir && dir[0];
    if (repo) {
      const vh = path.join(repo, "bin", "vh"), env = Object.assign({}, process.env, ENV);
      delete env.ELECTRON_RUN_AS_NODE;
      const exe = process.execPath, at = exe.indexOf(".app/") > 0 ? path.dirname(exe.slice(0, exe.indexOf(".app/") + 4)) : "";
      const args = ["studio", "--install-icon"].concat(at && at !== path.join(app.getPath("home"), "Applications") ? ["--dir", at] : []);
      const ok = fs.existsSync(vh) && fs.existsSync(path.join(repo, "tools", "desk", "studio.py"))
        && spawnSync(vh, args, { cwd: repo, env, stdio: "ignore", timeout: 900000 }).status === 0;
      if (ok) {
        app.releaseSingleInstanceLock();   // the app made again takes over
        spawn(vh, ["studio", "--icon", "open"], { cwd: repo, env, stdio: "ignore", detached: true }).unref();
      } else {
        dialog.showMessageBoxSync({ type: "warning", buttons: [t("好", "OK")], message: t("没能从那个文件夹装回 Studio", "Studio could not be set up again from that folder"),
          detail: t("那个文件夹不是 OpenVideoHarness，或者装的时候出了错。让 AI 把 Studio 图标重新装一次。",
            "That folder is not OpenVideoHarness, or the install did not finish. Ask the AI you use to put the Studio icon back.") });
      }
    }
    app.exit(repo ? 0 : 1);
  });
}
