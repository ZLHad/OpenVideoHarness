// The reads (DOM, never motion-blurred), the terminal, the HUD. Same words and windows as the gate-① animatic.
import { TL, BEAT, clamp, seg, eOut, eIn, eOutExpo, eInOut } from "./open-time.js";

const win = (t, a, b, fi = 0.3, fo = 0.3) => Math.min(eOut(seg(t, a - fi, a)), 1 - eIn(seg(t, b, b + fo)));
export const TXT = {
  t1: { en: "So many AI video tools.", zh: "AI 视频工具，多到数不清。" },
  t2: { en: "What’s missing?", zh: "差的是什么？" },
  t3: { title: "OpenVideoHarness", en: "Not more tools. Know-how.", zh: "不缺工具，缺门道。" },
  req: { en: "Make a vertical science short: why does a low-orbit satellite’s signal change pitch?",
         zh: "做一个竖屏科普：为什么低轨卫星的信号会“变调”。" },   // the request showcase 02 answers (it runs 24.8 s, so no "30-second")
  resp: { en: "→ type 02 of 9 · standard", zh: "→ 9 类里的 02 类 · standard" },
};

export function makeOverlay(root, opts) {
  const div = (id, css, html = "") => { const d = document.createElement("div"); d.id = id; d.style.cssText = css; d.innerHTML = html; root.appendChild(d); return d; };
  const EN = "'SF Pro Display', system-ui, -apple-system, sans-serif", ZH = "'PingFang SC', 'Hiragino Sans GB', sans-serif", MONO = "'SF Mono', Menlo, monospace";
  // a soft dark bed under every big read ("type wants a quiet background")
  const bed = (a) => `position:absolute;left:160px;right:160px;text-align:center;pointer-events:none;padding:56px 0 64px;` +
    `background:radial-gradient(ellipse at 50% 50%,rgba(4,5,8,${a}) 0%,rgba(4,5,8,${a * 0.7}) 40%,rgba(4,5,8,0) 72%);`;
  const t1 = div("o-t1", bed(0.55) + "top:690px;", `<div class="l1" style="font:600 74px ${EN};color:#F2F2F4;letter-spacing:-0.012em">${TXT.t1.en}</div>
    <div class="l2" style="font:500 46px ${ZH};color:#DADAE0;margin-top:12px">${TXT.t1.zh}</div>`);
  const t2 = div("o-t2", bed(0.62) + "top:330px;", `<div class="l1" style="font:650 124px ${EN};color:#F2F2F4;letter-spacing:-0.02em">${TXT.t2.en}</div>
    <div class="l2" style="font:500 66px ${ZH};color:#DADAE0;margin-top:16px">${TXT.t2.zh}</div>`);
  const t3 = div("o-t3", bed(0.66) + "top:270px;", `<div class="l1" style="font:650 118px ${EN};color:#F2F2F4;letter-spacing:-0.025em">${TXT.t3.title}</div>
    <div class="l2" style="font:500 58px ${EN};color:#FFB224;margin-top:26px">${TXT.t3.en}</div>
    <div class="l3" style="font:500 54px ${ZH};color:#DADAE0;margin-top:12px">${TXT.t3.zh}</div>`);
  const term = div("o-term", "position:absolute;left:192px;top:236px;width:1536px;height:536px;border:2px solid #5A5A63;border-radius:12px;background:rgba(8,9,11,0.94);pointer-events:none;transform-origin:50% 45%;box-shadow:0 0 120px rgba(255,178,36,0.10);",
    `<div style="position:absolute;left:0;right:0;top:0;height:60px;border-bottom:2px solid #3A3A40;font:400 26px ${MONO};color:#8B8B94">
       <span style="position:absolute;left:28px;top:16px"><b style="color:#FFB224;font-weight:500">▍</b> OpenVideoHarness</span>
       <span style="position:absolute;right:28px;top:16px">~/projects · t <span id="tt">00.00</span></span></div>
     <div style="position:absolute;left:44px;right:44px;top:92px;font:500 46px ${MONO};line-height:1.4;color:#EDEDEF;white-space:pre-wrap;word-break:break-word"><span style="color:#FFB224">› </span><span id="typed"></span><span id="caret" style="color:#FFB224">▍</span></div>
     <div id="gloss" style="position:absolute;left:88px;right:44px;top:262px;font:400 46px ${ZH};color:#C4C4CC">${TXT.req.zh}</div>
     <div id="resp" style="position:absolute;left:88px;right:44px;top:362px;font:500 48px ${MONO};color:#FFB224">${TXT.resp.en}<div style="font:400 46px ${ZH};color:#D9B46A;margin-top:10px">${TXT.resp.zh}</div></div>`);
  const hud = div("o-hud", `position:absolute;left:40px;bottom:28px;font:400 22px ${MONO};color:#6b6b73;white-space:pre;pointer-events:none;`);
  hud.style.display = opts.hud ? "block" : "none";
  const typed = term.querySelector("#typed"), caret = term.querySelector("#caret"), gloss = term.querySelector("#gloss"), resp = term.querySelector("#resp"), tt = term.querySelector("#tt");
  // a read arrives: rises 14 px, unblurs, tracks in; leaves by fading
  const arrive = (el, t, a, k = 1) => { const u = eOutExpo(seg(t, a - 0.35, a + 0.5));
    el.style.transform = `translateY(${(14 * (1 - u) * k).toFixed(1)}px)`; el.style.filter = u < 0.999 ? `blur(${(6 * (1 - u)).toFixed(2)}px)` : "none";
    el.style.letterSpacing = ""; };
  return (t, tn = t) => {   // t: the story's time (the terminal's hold is stretched, js/tmap.js); tn: the film's own time
    t1.style.opacity = win(t, TL.t1[0], TL.t1[1]).toFixed(3); arrive(t1, t, TL.t1[0]);
    t2.style.opacity = win(t, TL.t2[0], TL.t2[1]).toFixed(3); arrive(t2, t, TL.t2[0]);
    t3.style.opacity = win(t, TL.t3[0], TL.t3[1], 0.3, 0.15).toFixed(3); arrive(t3, t, TL.t3[0]);
    const ot = eOut(seg(t, TL.term[0], TL.term[0] + 0.45));
    const hold = 0.03 * eInOut(seg(tn, 21.3, window.__tNew(22.0)));   // a slow push while the request holds (the story is nearly still there)
    const push = eIn(seg(t, TL.enter, 23.0)); term.style.transform = `scale(${(0.97 + 0.03 * ot + hold + 0.12 * push + 1.4 * eIn(seg(t, 22.45, 23.0))).toFixed(4)})`;
    term.style.opacity = (ot * (1 - seg(t, 22.72, 22.95))).toFixed(3);
    const n = Math.floor(clamp((t - 19.15) / 1.85) * TXT.req.en.length); typed.textContent = TXT.req.en.slice(0, n);
    caret.style.opacity = t < 21.0 || Math.floor((t - 21.0) / 0.5) % 2 === 0 ? "1" : "0";
    gloss.style.opacity = win(t, 19.6, 99, 0.3).toFixed(3);
    resp.style.opacity = win(t, TL.answer, 99, 0.15).toFixed(3);
    tt.textContent = tn.toFixed(2).padStart(5, "0");
    const bb = Math.floor(t / BEAT + 1e-6);
    hud.textContent = `look-dev ${opts.fx} · t ${t.toFixed(2).padStart(5, "0")} · f ${String(Math.round(t * 30)).padStart(3, "0")} · ♩ ${Math.floor(bb / 4) + 1}.${(bb % 4) + 1}`;
  };
}
