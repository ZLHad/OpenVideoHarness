// One page through the same Chrome CDP transport as the film tools. The Python caller supplies JSON on stdin;
// stdout is one result. No npm package, persistent profile, injected credentials, or disabled browser sandbox.
import fs from "node:fs";
import dns from "node:dns/promises";
import net from "node:net";
import { BrowserGone, launchTab } from "../textcheck/browser.mjs";

const opt = JSON.parse(fs.readFileSync(0, "utf8"));
const warnings = [];
let browser, timer, stage = "checking the URL";
const fail = (message) => { console.error(`web: ${message}`); process.exit(1); };
// Startup and tab recovery need their own allowance: launchTab retries a Mac Chrome that never answers as its tab
// comes up (30 s plus cleanup a try). --timeout below still caps navigation, not those existing recovery attempts.
const budget = opt.timeout * 2 + (opt.wait ?? 5) * 4 + 120;
timer = setTimeout(() => fail(`Chrome did not finish within ${budget} s (${stage}, including startup/recovery)`), budget * 1000);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
class CommandTimeout extends Error {
  constructor(method) { super(`CDP ${method} did not answer within --timeout ${opt.timeout} s`); }
}
function privateIP(value) {
  const ip = value.toLowerCase().replace(/^\[|\]$/g, "");
  if (ip.startsWith("::ffff:")) {
    const mapped = ip.slice(7), m = mapped.match(/^([0-9a-f]{1,4}):([0-9a-f]{1,4})$/);
    if (!m) return privateIP(mapped);
    const n = parseInt(m[1], 16) * 65536 + parseInt(m[2], 16);
    return privateIP([Math.floor(n / 16777216), (n >>> 16) & 255, (n >>> 8) & 255, n & 255].join("."));
  }
  if (net.isIP(ip) === 4) {
    const [a, b] = ip.split(".").map(Number);
    return a === 0 || a === 10 || a === 127 || (a === 169 && b === 254) || (a === 172 && b >= 16 && b <= 31)
      || (a === 192 && (b === 168 || b === 0)) || (a === 100 && b >= 64 && b <= 127)
      || (a === 198 && (b === 18 || b === 19)) || a >= 224;
  }
  return net.isIP(ip) === 6 && !/^[23]/.test(ip);   // outside global unicast, including loopback and local/link-local
}
const allowedHosts = new Map();
async function allowed(url) {
  const u = new URL(url);
  if (!["http:", "https:"].includes(u.protocol)) return false;
  if (opt.allowPrivate) return true;
  const host = u.hostname.replace(/^\[|\]$/g, "");
  if (!allowedHosts.has(host)) allowedHosts.set(host, (async () => {
    if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local") || privateIP(host)) return false;
    const addresses = await dns.lookup(host, { all: true });
    return addresses.length > 0 && addresses.every((a) => !privateIP(a.address));
  })());
  return allowedHosts.get(host);
}

async function captureOnce() {
  if (!await allowed(opt.url)) throw new Error("private/local address blocked (only a local test: --allow-private-network)");
  stage = "starting Chrome and opening a tab";
  // The throwaway profile has nothing worth keeping in the keychain, and touching the real login
  // keychain can pop system dialogs (on macOS a missing one even offers to reset it). Mock it: the
  // profile is discarded anyway, so its cookies only need a key for this one capture.
  ({ browser, sessionId: opt.session } = await launchTab(opt.browser, ["--disable-background-networking", "--use-mock-keychain"], ["Page", "Runtime", "Network"]));
  const current = browser;
  const session = opt.session;
  const send = (method, params = {}) => {
    if (!/^Fetch\.(continue|fail)Request$/.test(method)) stage = method;
    let deadline;
    return Promise.race([current.send(method, params, session), new Promise((_, reject) => {
      deadline = setTimeout(() => reject(new CommandTimeout(method)), opt.timeout * 1000);
    })]).finally(() => clearTimeout(deadline));
  };
  const evaluate = async (expression) => {
    const r = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.text || "the page could not be read");
    return r.result.value;
  };
  // Check HTTP(S) requests paused in this page's CDP session, including redirects and subresources. WebSocket,
  // WebRTC, other targets and DNS rebinding are not contained: this host/DNS guard is not an OS egress firewall.
  current.on("Fetch.requestPaused", (p) => {
    void (async () => {
      let permit = false;
      try { permit = await allowed(p.request.url); } catch { /* unresolved or unsupported URL */ }
      if (!permit) {
        if (warnings.length < 10) warnings.push(`blocked private, unresolved or unsupported request: ${p.request.url}`);
        await send("Fetch.failRequest", { requestId: p.requestId, errorReason: "BlockedByClient" });
      } else await send("Fetch.continueRequest", { requestId: p.requestId });
    })().catch(() => {});   // the tab may have closed while a DNS lookup was pending
  });
  await send("Fetch.enable", { patterns: [{ urlPattern: "*", requestStage: "Request" }] });
  await send("Network.setCacheDisabled", { cacheDisabled: true });
  await send("Emulation.setDeviceMetricsOverride", { width: 1280, height: 720, deviceScaleFactor: 1, mobile: false });
  const frame = (await send("Page.getFrameTree")).frameTree.frame.id;
  let status = null;
  current.on("Network.responseReceived", (p) => {
    if (p.frameId === frame && p.type === "Document") status = p.response.status;
  });
  const loaded = current.once("Page.loadEventFired", session);
  loaded.catch(() => {});   // a failed navigation is reported below; closing the tab also rejects this pending wait
  let loadTimer;
  try {
    // The page-load deadline includes Page.navigate itself, rather than starting only after CDP answers it.
    const navigation = (async () => {
      const nav = await send("Page.navigate", { url: opt.url });
      if (nav.errorText) throw new Error(`the page could not be opened: ${nav.errorText}`);
      stage = "waiting for page load";
      await loaded;
    })();
    await Promise.race([navigation, new Promise((_, reject) => {
      loadTimer = setTimeout(() => reject(new Error(`page load exceeded --timeout ${opt.timeout} s`)), opt.timeout * 1000);
    })]);
  } finally { clearTimeout(loadTimer); }
  if (opt.wait ?? 1) await sleep((opt.wait ?? 1) * 1000);
  if (opt.selector) {
    const until = Date.now() + (opt.wait ?? 5) * 1000;
    let found;
    do {
      found = await evaluate(`Boolean(document.querySelector(${JSON.stringify(opt.selector)}))`);
      if (found || Date.now() >= until) break;
      await sleep(100);
    } while (true);
    if (!found) warnings.push(`selector '${opt.selector}' not found after ${opt.wait ?? 5}s`);
  }
  // Both files use this one navigation. The screenshot follows this DOM read, without reloading the page.
  const page = await evaluate(`(() => {
    const text = document.body?.innerText || '';
    const links = [...document.querySelectorAll('a[href]')].map(a => ({text: a.innerText.trim(), url: a.href}))
      .filter(a => /^https?:/.test(a.url));
    function md(node) {
      if (node.nodeType === Node.TEXT_NODE) return node.textContent;
      if (node.nodeType !== Node.ELEMENT_NODE) return '';
      const tag = node.tagName.toLowerCase();
      if (['script', 'style', 'noscript', 'template', 'svg'].includes(tag) || node.hidden || getComputedStyle(node).display === 'none') return '';
      if (tag === 'pre') return '\\n\\n' + '\\x60\\x60\\x60\\n' + node.innerText + '\\n\\x60\\x60\\x60\\n\\n';
      if (tag === 'br') return '\\n';
      const body = [...node.childNodes].map(md).join('');
      if (/^h[1-6]$/.test(tag)) return '\\n\\n' + '#'.repeat(+tag[1]) + ' ' + body.trim() + '\\n\\n';
      if (tag === 'a' && /^https?:/.test(node.href)) return '[' + body.trim() + '](' + node.href + ')';
      if (tag === 'li') return '\\n- ' + body.trim();
      return ['p','div','section','article','main','header','footer','ul','ol','blockquote','tr'].includes(tag)
        ? '\\n\\n' + body.trim() + '\\n\\n' : body;
    }
    return { final_url: location.href, title: document.title, html: (document.doctype ? '<!DOCTYPE html>\\n' : '')
      + document.documentElement.outerHTML, text, links: links.map(a => a.text + '\\t' + a.url).join('\\n'),
      markdown: md(document.body || document.documentElement).replace(/\\n[ \\t]+/g, '\\n').replace(/\\n{3,}/g, '\\n\\n').trim() + '\\n' };
  })()`);
  if (opt.shot) {
    const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    fs.writeFileSync(opt.shot, Buffer.from(png.data, "base64"));
  }
  if (status !== null && status >= 400) warnings.push(`HTTP ${status}: inspect the saved page before citing it`);
  return { body: page[opt.dump], final_url: page.final_url, title: page.title,
    status, browser: current.version, warnings };
}

try {
  const recovered = [];
  for (let attempt = 1; ; attempt++) {
    warnings.length = 0;
    try {
      const result = await captureOnce();
      process.stdout.write(JSON.stringify({ ...result, attempts: attempt, warnings: [...recovered, ...warnings] }));
      break;
    } catch (e) {
      if (browser) await browser.close();
      browser = undefined;
      // A stalled/crashed CDP connection needs a new process. A slow or invalid page is reported without retrying it.
      if (attempt < 2 && (e instanceof CommandTimeout || e instanceof BrowserGone)) {
        recovered.push(`Chrome stopped answering (${e.message}); restarted once`);
        continue;
      }
      throw e;
    }
  }
} catch (e) {
  console.error(`web: ${e.message}`);
  process.exitCode = 1;
} finally {
  clearTimeout(timer);
  if (browser) await browser.close();
}
