// The shell's decisions, kept apart from Electron so plain node checks them (tools/ci.sh, studio_checks): which lines
// from the console are taken, which requests get the console's token, which navigations stay in a window, where a new
// page opens, which permission a page gets, and what a line to show a window does to the one there.
"use strict";
const LOCAL = /^http:\/\/127\.0\.0\.1:\d+\//;

function originOf(u) { try { return new URL(u).origin; } catch (e) { return ""; } }

// A line from the console (on stdin, or handed over by a second start) → {close}, {quit}, {url, role, fresh}, or null.
function line(msg) {
  if (!msg || typeof msg !== "object" || Array.isArray(msg)) return null;
  if (typeof msg.close === "string") return { close: msg.close };
  if (msg.quit === true) return { quit: true };
  if (typeof msg.url !== "string" || !LOCAL.test(msg.url)) return null;
  return { url: msg.url, role: typeof msg.role === "string" && msg.role ? msg.role : "console", fresh: msg.fresh === true };
}

// The token for a request, or null. access: {origin, token}, what the app traded the code of that window for; topUrl:
// the window's page as it is now; topFrame: the request comes from that page itself (not a frame inside it). Only the
// console's own page asking its own console gets it: never a page from elsewhere, never a request to elsewhere.
function tokenFor(access, requestUrl, topUrl, topFrame) {
  if (!access || !access.token || !topFrame) return null;
  const o = originOf(requestUrl);
  return o && o === access.origin && o === originOf(topUrl) ? access.token : null;
}

// A navigation from the page the window shows now: "stay" (the same console), "browser" (a site elsewhere: the default
// browser), or "deny" (another address on this machine, or anything that is not http(s)).
function navigation(currentUrl, toUrl) {
  const o = originOf(toUrl);
  if (o && o === originOf(currentUrl)) return "stay";
  let host = "";
  try { host = new URL(toUrl).hostname; } catch (e) { return "deny"; }
  return /^https?:\/\//.test(toUrl) && !/^(127\.\d+\.\d+\.\d+|localhost|\[::1\]|0\.0\.0\.0)$/i.test(host) ? "browser" : "deny";
}

// A link that opens a new page: "inside" (a plain window of the app on the same console), "browser" or "deny".
function newPage(openerUrl, toUrl) {
  const n = navigation(openerUrl, toUrl);
  return n === "stay" ? "inside" : n;
}

// Full screen (the player's button) for the console's own page; nothing else.
function permission(perm, requestingUrl, windowUrl) {
  const o = originOf(requestingUrl);
  return perm === "fullscreen" && !!o && o === originOf(windowUrl);
}

// What a line to show a window does to the window there (currentUrl, or none): "make" one; "raise" it (the same console);
// "load" a fresh address of the same console (kept only when the app's code trade worked or the old token no longer
// answers); "check": another console's address, taken only when the console the window shows no longer answers.
function show(currentUrl, msg) {
  if (!currentUrl) return "make";
  if (originOf(currentUrl) !== originOf(msg.url)) return "check";
  return msg.fresh ? "load" : "raise";
}

module.exports = { originOf, line, tokenFor, navigation, newPage, permission, show };
