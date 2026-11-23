// The cut page and the note box, driven as a person drives them: real mouse presses and keys through the DevTools protocol
// (tools/textcheck/browser.mjs's headless Chrome, no npm package). Run by test_cut_page.py, which builds the long made-up
// films and starts their desk; {chrome, url, sheets, parts} on stdin. Prints one line a failure, nothing when all hold.
import fs from "node:fs";
import { launchTab } from "../textcheck/browser.mjs";

const opt = JSON.parse(fs.readFileSync(0, "utf8"));
const base = opt.url.replace(/\?c=.*$/, "");
const bad = [];
const want = (ok, msg) => { if (!ok) bad.push(msg); };
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const watchdog = setTimeout(() => { console.log("cut page: no end within 300 s"); process.exit(1); }, 300000);

// autoplay allowed, as in Studio's own window (Electron's default): only the page's own rule keeps the film still
const { browser, sessionId: S } = await launchTab(opt.chrome, ["--window-size=1440,900", "--autoplay-policy=no-user-gesture-required"], ["Page", "Runtime"]);
const send = (m, p = {}) => browser.send(m, p, S);
try {
  await send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  const ev = async (expression) => {
    const r = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`${expression.slice(0, 80)}: ${(r.exceptionDetails.exception || {}).description || r.exceptionDetails.text}`);
    return r.result.value;
  };
  const until = async (expr, ms = 10000) => { for (const t0 = Date.now(); Date.now() - t0 < ms; await sleep(100)) { if (await ev(`!!(${expr})`)) return true; } return false; };
  const go = async (u) => { await send("Page.navigate", { url: u }); await sleep(600); };
  const rect = (sel) => ev(`(() => { const e = document.querySelector(${JSON.stringify(sel)}); if (!e) return null; const r = e.getBoundingClientRect(); return { x: r.left, y: r.top, w: r.width, h: r.height }; })()`);
  const mouse = (type, x, y, extra = {}) => send("Input.dispatchMouseEvent", { type, x, y, button: "left", clickCount: type === "mouseMoved" ? 0 : 1, ...extra });
  const click = async (x, y) => { await mouse("mouseMoved", x, y); await mouse("mousePressed", x, y); await mouse("mouseReleased", x, y); await sleep(150); };
  const clickOn = async (sel) => { const r = await rect(sel); if (!r) { bad.push(`no ${sel} on the page`); return false; } await click(r.x + r.w / 2, r.y + r.h / 2); return true; };
  const key = async (k, code, keyCode, text, modifiers = 0) => {
    await send("Input.dispatchKeyEvent", { type: text ? "keyDown" : "rawKeyDown", key: k, code, windowsVirtualKeyCode: keyCode, text, modifiers });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: k, code, windowsVirtualKeyCode: keyCode, modifiers });
    await sleep(80);
  };
  const type = (s) => send("Input.insertText", { text: s });

  await go(opt.url); await sleep(1200);   // the one-time address: this page gets the token
  await go(base + "#/"); await until(`document.querySelector('a[href*="long-tide"]')`);
  const hrefs = await ev(`Array.from(document.querySelectorAll('a[href^="#/p/"]')).map((a) => a.getAttribute("href"))`);
  const keyOf = (re) => (hrefs.find((h) => re.test(h)) || "").replace(/^#\/p\//, "").split("/")[0];
  const LONG = keyOf(/long-tide~/), EDIT = keyOf(/long-tide-edit~/);
  want(LONG && EDIT, `the space lists the two films: ${hrefs.join(" ")}`);

  // 1. the stop opens with the film still and its sound as it was; a click from code plays nothing
  await go(`${base}#/p/${LONG}`);
  want(await until(`document.querySelector('#cv') && document.querySelector('#cv').readyState >= 1`), "the cut opens on gate ③ with its film");
  await sleep(2000);
  const v0 = await ev(`(() => { const v = document.querySelector('#cv'); return { paused: v.paused, t: v.currentTime, muted: v.muted }; })()`);
  want(v0.paused && v0.t === 0 && v0.muted === false, `opening the stop played the film or changed its sound: ${JSON.stringify(v0)}`);
  await ev(`document.querySelector('#cPlay').click()`); await sleep(800);
  want(await ev(`document.querySelector('#cv').paused`), "a click from code (no person's gesture) started the film");

  // 2. a second picked, played on and paused: the note is on where the picture stopped, and one line marks it
  const ru = await rect(".ruler-l .trk");
  await click(ru.x + ru.w * (80 / 740), ru.y + ru.h / 2);
  want((await ev(`document.querySelector('#scope').textContent`)).includes("1:20"), "a click on the ruler at 1:20 does not put the note there");
  await clickOn("#cPlay"); await sleep(2500); await clickOn("#cPlay"); await sleep(400);
  const st = await ev(`({ scope: document.querySelector('#scope').textContent, tc: document.querySelector('#cTc').textContent.split(" /")[0].trim(), sel: !document.querySelector('.selr').hidden })`);
  want(st.scope.includes(st.tc) && st.tc !== "1:20.0", `played on and paused at ${st.tc}, the note box still says ${st.scope}`);
  want(!st.sel, "two lines on the timeline: the picked second's apart from the playhead it should follow");

  // 3. zoomed all the way in: about 100 px a second on a 12-minute film; playing, the playhead stays in sight and the lanes keep their names
  for (let i = 0; i < 12; i++) await clickOn("#zIn");
  const px = await ev(`(document.querySelector('#tl').clientWidth - 92) / 740`);
  want(px >= 80, `zoomed all the way in, a second is ${px.toFixed(1)} px (a 12-minute film needs about 100)`);
  await ev(`document.querySelector('#cv').playbackRate = 8`);
  await clickOn("#cPlay");
  let lost = 0, labs = 0;
  for (let i = 0; i < 8; i++) {
    await sleep(600);
    const g = await ev(`(() => { const s = document.querySelector('#tlScroll').getBoundingClientRect(), p = document.querySelector('.tl-ph').getBoundingClientRect(), l = document.querySelector('.lane.shots .lab').getBoundingClientRect();
      return { inView: p.left >= s.left + 60 && p.left <= s.right, lab: Math.abs(l.left - s.left) < 2 }; })()`);
    if (!g.inView) lost++;
    if (!g.lab) labs++;
  }
  await clickOn("#cPlay"); await ev(`document.querySelector('#cv').playbackRate = 1`);
  want(!lost, `zoomed in and playing, the playhead was out of sight ${lost} of 8 times`);
  want(!labs, "zoomed in and scrolled, the lanes' names scrolled away");
  for (let i = 0; i < 14; i++) await clickOn("#zOut");

  // 4. the 67 marked places: no pin on top of another
  const pins = await ev(`Array.from(document.querySelectorAll('.lane.marks .pin')).map((e) => { const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height]; })`);
  let over = 0;
  for (let i = 0; i < pins.length; i++) for (let j = i + 1; j < pins.length; j++) {
    const [a, b] = [pins[i], pins[j]], w = Math.min(a[0] + a[2], b[0] + b[2]) - Math.max(a[0], b[0]), h = Math.min(a[1] + a[3], b[1] + b[3]) - Math.max(a[1], b[1]);
    if (w > 1 && h > 1) over++;
  }
  want(pins.length === 67, `${pins.length} pins for the 67 marked places`);
  want(!over, `${over} pairs of the marked places' pins lie on each other`);

  // 5. the note box: ↩ is a new line; one press of 记下 keeps the note (the button stays under the pointer); ⌘/Ctrl+↩ keeps too; the keys in words beside it
  if (await ev(`!document.querySelector('#toWhole').hidden`)) await clickOn("#toWhole");
  await ev(`document.querySelector('#say').focus()`); await type("第一行"); await key("Enter", "Enter", 13, "\r"); await type("第二行");
  want((await ev(`document.querySelector('#say').value`)) === "第一行\n第二行", "↩ in the note box is not a new line");
  await sleep(400);   // the box has opened (its height eases in)
  const b0 = await rect("#sayAdd");
  await mouse("mouseMoved", b0.x + b0.w / 2, b0.y + b0.h / 2); await mouse("mousePressed", b0.x + b0.w / 2, b0.y + b0.h / 2); await sleep(200);
  const b1 = await rect("#sayAdd");
  await mouse("mouseReleased", b0.x + b0.w / 2, b0.y + b0.h / 2); await sleep(400);
  want(Math.abs(b1.y - b0.y) < 1 && Math.abs(b1.x - b0.x) < 1, `记下 moved ${Math.round(b1.y - b0.y)} px while it was pressed`);
  want((await ev(`document.querySelector('#say').value`)) === "" && (await ev(`document.querySelector('#cMine').textContent`)).includes("第二行"), "one press of 记下 did not keep the note");
  await ev(`document.querySelector('#say').focus()`); await type("第三行"); await key("Enter", "Enter", 13, "\r", 2);
  want((await ev(`document.querySelector('#say').value`)) === "", "Ctrl+↩ does not keep the note");
  want(/↩.*记下.*↩.*换行/.test(await ev(`(document.querySelector('#sayKeys') || {}).textContent || ""`)), "the note box's keys are not said in words beside it");

  // 6. a note about no moment of the film: its own place, marked as such when it goes
  if (await clickOn("#toNone")) {
    await type("给 Studio 的话"); await clickOn("#sayAdd");
    want((await ev(`payload().general`)).includes("〔不对着片子〕给 Studio 的话"), `a note not about the film goes unmarked: ${await ev("payload().general")}`);
  }

  // 7. the storyboard by shot: a tab a part with its shots, the sheets of one part together; ← → shot by shot
  await go(`${base}#/p/${LONG}/board/1`); await until(`document.querySelector('.pgtabs')`);
  const tabs = await ev(`Array.from(document.querySelectorAll('.pgtabs a')).map((a) => a.textContent.trim())`);
  want(tabs.length === opt.parts && opt.sheets > opt.parts, `${opt.sheets} sheets of ${opt.parts} parts made ${tabs.length} tabs`);
  want(tabs.every((x) => !/页|Page/.test(x)) && /^S1–S\d+ /.test(tabs[0] || ""), `the tabs say pages, not shots: ${tabs.slice(0, 3).join(" | ")}`);
  await ev(`document.activeElement && document.activeElement.blur()`);
  await key("ArrowRight", "ArrowRight", 39); await key("ArrowRight", "ArrowRight", 39); await sleep(300);
  const cur = await ev(`({ id: (document.querySelector('.shotc.cur') || {}).id || "", scope: document.querySelector('#scope').textContent })`);
  want(cur.id === "shot-S2" && /S2\b/.test(cur.scope), `→ → on the storyboard: ${JSON.stringify(cur)}`);

  // 8. an edit list's long part: a shot inside it is there to point at
  await go(`${base}#/p/${EDIT}/cut`);
  want(await until(`document.querySelector('.lane.shots [data-pick="shot:PROLOGUE.S1_3"]')`), "the shots inside an edit list's part are not on the timeline");
  if (await ev(`!!document.querySelector('.lane.shots [data-pick="shot:PROLOGUE.S1_3"]')`)) {
    await clickOn('.lane.shots [data-pick="shot:PROLOGUE.S1_3"]');
    const sc = await ev(`document.querySelector('#scope').textContent`);
    want(sc.includes("S1_3") && sc.includes("PROLOGUE"), `a click on S1_3 inside PROLOGUE names ${sc}`);
  }
} catch (e) {
  bad.push(`cut page: ${e.message}`);
} finally {
  await browser.close();
  clearTimeout(watchdog);
}
for (const b of bad) console.log(b);
process.exit(bad.length ? 1 : 0);
