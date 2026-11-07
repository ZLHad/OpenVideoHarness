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
// The whole run's last-resort deadline; bin/vh web passes it (tools/web/web.py chrome_budget). Each of the two attempts may
// spend launchTab's own recovery (up to 3 launches: a first answer within 60 s, the tab's within OVH_PAGE_TIMEOUT or 30 s,
// a close) before the page's own steps: the load, the settle, a selector's wait, then the read and the screenshot.
const tabAnswer = Math.max(30, Number(process.env.OVH_PAGE_TIMEOUT) || 0);
const budget = opt.budget ?? 2 * (3 * (70 + tabAnswer) + 3 * opt.timeout + (opt.wait ?? 1) + (opt.selector ? opt.wait ?? 5 : 0) + 10) + 10;
timer = setTimeout(() => fail(`Chrome did not finish within ${budget} s (${stage}, including startup/recovery)`), budget * 1000);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
class CommandTimeout extends Error {
  constructor(method) { super(`CDP ${method} did not answer within --timeout ${opt.timeout} s`); }
}
// Not a public address: IANA's special-purpose IPv4 blocks; in IPv6, all outside global unicast (2000::/3) and, inside it,
// the IETF protocol assignments (Teredo among them), documentation and 6to4, which wraps an IPv4 address. BlockList parses
// every spelling (2::1 is 0002::, not in 2000::/3) and checks an IPv4-mapped address (::ffff:…) against the IPv4 blocks.
const NOT_GLOBAL = new net.BlockList(), GLOBAL_UNICAST = new net.BlockList();
for (const [a, p] of [["0.0.0.0", 8], ["10.0.0.0", 8], ["100.64.0.0", 10], ["127.0.0.0", 8], ["169.254.0.0", 16], ["172.16.0.0", 12],
  ["192.0.0.0", 24], ["192.0.2.0", 24], ["192.88.99.0", 24], ["192.168.0.0", 16], ["198.18.0.0", 15], ["198.51.100.0", 24],
  ["203.0.113.0", 24], ["224.0.0.0", 3]]) NOT_GLOBAL.addSubnet(a, p, "ipv4");
for (const [a, p] of [["2001::", 23], ["2001:db8::", 32], ["2002::", 16]]) NOT_GLOBAL.addSubnet(a, p, "ipv6");
GLOBAL_UNICAST.addSubnet("2000::", 3, "ipv6");
function privateIP(value) {
  const ip = value.toLowerCase().replace(/^\[|\]$/g, "");
  if (net.isIP(ip) === 4) return NOT_GLOBAL.check(ip, "ipv4");
  if (net.isIP(ip) !== 6) return false;
  const one = new URL(`http://[${ip}]/`).hostname.slice(1, -1);   // one spelling: every IPv4-mapped form is ::ffff:x:y
  if (/^::ffff:[0-9a-f]{1,4}:[0-9a-f]{1,4}$/.test(one)) return NOT_GLOBAL.check(one, "ipv6");   // as its IPv4 address
  return NOT_GLOBAL.check(one, "ipv6") || !GLOBAL_UNICAST.check(one, "ipv6");
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
  // launch() gives every throwaway browser --use-mock-keychain, so this one never reaches the macOS login keychain either
  ({ browser, sessionId: opt.session } = await launchTab(opt.browser, ["--disable-background-networking"], ["Page", "Runtime", "Network"]));
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
  // Page.navigate answers when the navigation commits, so a server slow to answer holds it as long as it holds the load:
  // one deadline covers both, and it is the page's time. When it passes, a browser-wide command tells a slow page
  // (reported, not retried) from a browser that stopped answering (restarted once).
  const answers = async () => {
    let t;
    try {
      await Promise.race([current.send("Browser.getVersion"), new Promise((_, no) => { t = setTimeout(no, Math.min(5000, opt.timeout * 1000)); })]);
      return true;
    } catch { return false; } finally { clearTimeout(t); }
  };
  const late = new Error("deadline");
  let loadTimer;
  try {
    const navigation = (async () => {
      stage = "Page.navigate";
      const nav = await current.send("Page.navigate", { url: opt.url }, session);
      if (nav.errorText) throw new Error(`the page could not be opened: ${nav.errorText}`);
      stage = "waiting for page load";
      await loaded;
    })();
    navigation.catch(() => {});   // after the deadline nothing waits on it
    await Promise.race([navigation, new Promise((_, reject) => {
      loadTimer = setTimeout(() => reject(late), opt.timeout * 1000);
    })]);
  } catch (e) {
    if (e !== late) throw e;
    if (!await answers()) throw new CommandTimeout(stage === "Page.navigate" ? "Page.navigate" : "Page.loadEventFired");
    throw new Error(`page load exceeded --timeout ${opt.timeout} s`);
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
  // Both files use this one navigation. The screenshot follows this DOM read, without reloading the page. Only the dump
  // asked for is built: the markdown walk reads every element's style, and each is a copy of the page through the pipe.
  const page = await evaluate(`(() => {
    const want = ${JSON.stringify(opt.dump)};
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
    const body = want === 'html' ? (document.doctype ? '<!DOCTYPE html>\\n' : '') + document.documentElement.outerHTML
      : want === 'text' ? document.body?.innerText || ''
      : want === 'links' ? [...document.querySelectorAll('a[href]')].map(a => ({text: a.innerText.trim(), url: a.href}))
          .filter(a => /^https?:/.test(a.url)).map(a => a.text + '\\t' + a.url).join('\\n')
      : md(document.body || document.documentElement).replace(/\\n[ \\t]+/g, '\\n').replace(/\\n{3,}/g, '\\n\\n').trim() + '\\n';
    return { final_url: location.href, title: document.title, body };
  })()`);
  if (opt.shot) {
    const png = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    fs.writeFileSync(opt.shot, Buffer.from(png.data, "base64"));
  }
  if (status !== null && status >= 400) warnings.push(`HTTP ${status}: inspect the saved page before citing it`);
  return { body: page.body, final_url: page.final_url, title: page.title,
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
