// OVH Studio: bin/vh studio --install-icon wrote this from tools/desk/launcher/shell-boot.js. It runs Studio's shell
// (tools/desk/shell/main.js) from the clone below, so a git pull changes it with no reinstall.
"use strict";
const fs = require("fs"), path = require("path");
const REPO = @@REPO@@;
const ENV = @@ENV@@;   // the PATH the installer saw: an app started by the Dock gets the bare system one
const main = path.join(REPO, "tools", "desk", "shell", "main.js");
if (fs.existsSync(main)) {
  require(main).start({ repo: REPO, env: ENV });
} else {
  const { app, dialog } = require("electron");
  app.whenReady().then(() => {
    dialog.showMessageBoxSync({ type: "warning", buttons: ["OK"], message: "找不到 OpenVideoHarness 了 / OpenVideoHarness is no longer there",
      detail: "原来在 " + REPO + "。在它现在的位置运行：bin/vh studio --install-icon\n\nIt was at " + REPO + ". Where it is now, run: bin/vh studio --install-icon" });
    app.exit(1);
  });
}
