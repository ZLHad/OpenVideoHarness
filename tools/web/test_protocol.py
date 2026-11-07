"""A silent Chrome CDP must time out, clean up and recover once; no browser or network is used."""
import json, pathlib, shutil, subprocess, tempfile

HERE = pathlib.Path(__file__).resolve().parent
node = shutil.which("node")
assert node, "needs Node 22"

with tempfile.TemporaryDirectory(prefix="vh-web-protocol-") as tmp:
    root = pathlib.Path(tmp)
    (root / "web").mkdir()
    (root / "textcheck").mkdir()
    shutil.copyfile(HERE / "chrome.mjs", root / "web/chrome.mjs")
    log = root / "calls.jsonl"
    stub = r'''
import fs from "node:fs";
export class BrowserGone extends Error {}
let launches = 0;
const log = (event) => fs.appendFileSync(LOG, JSON.stringify(event) + "\n");
export async function launchTab(mode) {
  const attempt = ++launches;
  log({ event: "launch", attempt });
  return { sessionId: "page", browser: {
    version: "HeadlessChrome/mock",
    on() {},
    once() { return mode === "never-load" ? new Promise(() => {}) : Promise.resolve({}); },
    async send(method) {
      log({ event: "send", attempt, method });
      const stalled = mode === "always-navigate" || attempt === 1 && mode === "navigate-first";   // the whole browser stopped answering
      const stuck = stalled && (method === "Page.navigate" || method === "Browser.getVersion")
        || mode === "slow-page" && method === "Page.navigate"   // a live browser on a server slow to answer
        || attempt === 1 && (mode === "evaluate-first" && method === "Runtime.evaluate"
          || mode === "screenshot-first" && method === "Page.captureScreenshot");
      if (stuck) return new Promise(() => {});
      if (method === "Page.getFrameTree") return { frameTree: { frame: { id: "root" } } };
      if (method === "Runtime.evaluate") return { result: { value: {
        final_url: "https://evidence.example/page", title: "Evidence", body: "visible fact" } } };
      if (method === "Page.captureScreenshot") return { data: Buffer.from("PNG").toString("base64") };
      return {};
    },
    async close() { log({ event: "close", attempt }); }
  } };
}
'''.replace("LOG", json.dumps(str(log)))
    (root / "textcheck/browser.mjs").write_text(stub)

    for mode, expected_code, expected_attempts in (
        ("normal", 0, 1), ("navigate-first", 0, 2), ("evaluate-first", 0, 2),
        ("screenshot-first", 0, 2), ("always-navigate", 1, 2), ("never-load", 1, 1), ("slow-page", 1, 1),
    ):
        log.write_text("")
        config = {"browser": mode, "url": "https://evidence.example/page", "dump": "text",
                  "timeout": 0.05, "wait": 0, "allowPrivate": True,
                  "shot": str(root / "shot.png") if mode == "screenshot-first" else None}
        try:
            result = subprocess.run([node, str(root / "web/chrome.mjs")], input=json.dumps(config),
                                    text=True, capture_output=True, timeout=3)
        except subprocess.TimeoutExpired as e:
            raise AssertionError(f"{mode}: silent CDP exceeded its command timeout without recovery/cleanup") from e
        assert result.returncode == expected_code, (mode, result.returncode, result.stderr)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        assert sum(c["event"] == "launch" for c in calls) == expected_attempts, (mode, calls)
        assert sum(c["event"] == "close" for c in calls) == expected_attempts, (mode, calls)
        if expected_code == 0:
            value = json.loads(result.stdout)
            assert value["body"] == "visible fact" and value.get("attempts", 1) == expected_attempts, (mode, value)
            navigations = [c for c in calls if c.get("method") == "Page.navigate"]
            assert len(navigations) <= expected_attempts, (mode, navigations)
            if expected_attempts == 2:
                assert any("restarted" in w for w in value["warnings"]), (mode, value)
        else:
            assert not result.stdout, (mode, result.stdout)
            assert ("Page.navigate" if mode == "always-navigate" else "page load") in result.stderr, result.stderr

    # what the address guard refuses before any browser starts (6to4, Teredo, documentation, a short IPv6 outside 2000::/3,
    # an IPv4-mapped spelling, IPv6 multicast, an IPv4 special block), and a public address it lets through
    for url, refused in (("http://[2002:c0a8:101::]/", True), ("http://[2001::1]/", True), ("http://[2001:db8::1]/", True),
                         ("http://[2::1]/", True), ("http://[::ffff:a01:203]/", True), ("http://[ffff::1]/", True),
                         ("http://192.88.99.1/", True), ("http://[2606:4700::1111]/", False)):
        log.write_text("")
        config = {"browser": "normal", "url": url, "dump": "text", "timeout": 0.05, "wait": 0, "allowPrivate": False, "shot": None}
        result = subprocess.run([node, str(root / "web/chrome.mjs")], input=json.dumps(config), text=True, capture_output=True, timeout=3)
        launched = any(json.loads(line)["event"] == "launch" for line in log.read_text().splitlines())
        if refused:
            assert result.returncode == 1 and "private/local address blocked" in result.stderr and not launched, (url, result.returncode, result.stderr)
        else:
            assert result.returncode == 0 and launched, (url, result.returncode, result.stderr)

print("Chrome CDP: bounded navigation/evaluation/screenshot commands, one restart, final failure cleanup, page load timeout, "
      "a slow page reported without a restart, private and special-purpose addresses refused before a browser starts")
