// page_driver: Studio's page in a headless Chrome, driven step by step, for tools/desk/test_page.py (a check, not a
// bin/vh command). The steps come as JSON on stdin; each "eval" and "until" answer goes to stdout as one JSON line.
//
// usage: node tools/desk/page_driver.mjs <chrome> < steps.json
//   {"url": "<the desk's one-time address>", "width": 1440, "height": 900, "steps": [ … ]}
//   step: {"go": "#/p/<key>/outline"}            set the address's hash (the page routes on it)
//         {"reload": true}                       reload the page and wait for it
//         {"wait": 500}                          milliseconds
//         {"until": "<js expression>", "ms": 8000, "name": "…"}   wait until it is truthy: {name, ok, value}
//         {"eval": "<js expression>", "name": "…"}               evaluate in the page: {name, value} (awaited, as JSON)
//         {"write": "<path>", "text": "…"}       write a file (a project file the agent changes while the page is open)
//         {"click": "<css selector>"}            a real click (mouse events at its middle), as the person's
// The page's own scripts see real input events: a click is the browser's, not element.click(). Nothing else is
// done to the page; a step that fails is said in its line and the rest go on.
import { launchTab } from "../textcheck/browser.mjs";
import { writeFileSync } from "node:fs";

const exe = process.argv[2];
const input = JSON.parse(await new Promise((ok) => { let s = ""; process.stdin.on("data", (d) => { s += d; }); process.stdin.on("end", () => ok(s)); }));
const out = (x) => process.stdout.write(JSON.stringify(x) + "\n");
const { browser, sessionId: S } = await launchTab(exe, [], ["Page", "Runtime"]);
const send = (m, p) => browser.send(m, p, S);
const sleep = (ms) => new Promise((ok) => setTimeout(ok, ms));
async function evaluate(expr) {
  const r = await send("Runtime.evaluate", { expression: `(async () => (${expr}))()`, awaitPromise: true, returnByValue: true });
  if (r.exceptionDetails) throw new Error((r.exceptionDetails.exception && r.exceptionDetails.exception.description) || r.exceptionDetails.text);
  return r.result.value;
}
async function loaded(navigate) {
  const done = browser.once("Page.loadEventFired", S);
  await navigate();
  await Promise.race([done, sleep(15000)]);
  await sleep(600);
}
try {
  await send("Emulation.setDeviceMetricsOverride", { width: input.width || 1440, height: input.height || 900, deviceScaleFactor: 1, mobile: false });
  await loaded(() => send("Page.navigate", { url: input.url }));
  for (const st of input.steps) {
    try {
      if (st.go != null) { await evaluate(`location.hash = ${JSON.stringify(st.go)}`); await sleep(st.after || 1500); }
      else if (st.reload) await loaded(() => send("Page.reload", {}));
      else if (st.wait) await sleep(st.wait);
      else if (st.write) writeFileSync(st.write, st.text);
      else if (st.click) {
        const box = await evaluate(`(() => { const e = document.querySelector(${JSON.stringify(st.click)}); if (!e) return null; e.scrollIntoView({ block: "center" }); const r = e.getBoundingClientRect(); return { x: r.left + r.width / 2, y: r.top + r.height / 2 }; })()`);
        if (!box) { out({ name: st.name || st.click, error: "not there" }); continue; }
        for (const type of ["mouseMoved", "mousePressed", "mouseReleased"]) await send("Input.dispatchMouseEvent", { type, x: box.x, y: box.y, button: "left", clickCount: 1 });
        await sleep(st.after || 400);
      } else if (st.until) {
        const t0 = Date.now(); let v = null;
        while (Date.now() - t0 < (st.ms || 8000)) { v = await evaluate(st.until).catch(() => null); if (v) break; await sleep(200); }
        out({ name: st.name || st.until, ok: !!v, value: v });
      } else if (st.eval) out({ name: st.name || st.eval, value: await evaluate(st.eval) });
    } catch (e) { out({ name: st.name || JSON.stringify(st).slice(0, 60), error: String(e.message || e).slice(0, 300) }); }
  }
} finally { await browser.close(); }
process.exit(0);
