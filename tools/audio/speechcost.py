"""What a per-use voice costs, and its requests held against the film's budget (tools/assets/budget.py). Stdlib only.

Billed per use, so not called without a budget (CLAUDE.md: 按次计费的配音), in bin/vh tts and bin/vh voices audition:
  minimax     with MINIMAX_API_KEY (pay-as-you-go: the account's balance). With MINIMAX_TOKEN_PLAN_KEY, which tts tries
              first, the Token Plan's credits are spent instead, and no budget is asked
  elevenlabs  billed in US dollars per character
  dashscope   Alibaba Cloud Model Studio (阿里云百炼), per 10,000 characters after a new account's free quota
Used as before, with no budget: qwen and say (on this machine), edge (no key, not billed), gemini, gemini-lite and
--align gemini (the free quota first).

The prices (PRICES) are the providers' own pages, read on CHECKED; each entry names its page. Characters are counted as
those pages count them: a Chinese character (Han, kanji, hanja) as 2 for MiniMax and DashScope, every character as 1 for
ElevenLabs. MiniMax's international page does not say how it counts; its China page's rule (2) is used there too, the
larger of the two.

A run: check() before any request and before anything is deleted (the key comes first: a budget is no use without one)
takes the whole run's estimate against the budget; no budget, or one it would go over, and nothing is called, with what to
write. Then each request is held at its own estimate and settled at what the answer says was billed (MiniMax's
extra_info.usage_characters, DashScope's usage.characters × the price) or, for ElevenLabs, whose answer says nothing, at the
estimate: an upper bound, since characters a plan includes are not billed per use (the record says so). An error answer
and a request that never left settle at 0; a timeout or an answer cut off keeps the estimate, as such a request may have
been billed (said). A model or an endpoint the table does not have: called only with a Budget line (an amount or 不限),
and recorded as cost not known, maybe billed.

  python3 tools/audio/speechcost.py [--json]     the table: provider, endpoint, model, price, page
"""
import contextlib, json, os, re, sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "assets"))
import budget   # noqa: E402  (tools/assets/budget.py: the Budget line, the spend log, hold and settle)

CHECKED = "2026-11-22"
_MM = "https://platform.minimax.io/docs/guides/pricing"
_MM_CN = "https://platform.minimax.cn/docs/guides/pricing"      # platform.minimaxi.com/docs/guides/pricing leads here
_EL = "https://elevenlabs.io/pricing/api"
_ALI = "https://www.alibabacloud.com/help/en/model-studio/model-pricing"
_ALI_CN = "https://help.aliyun.com/zh/model-studio/model-pricing"
# (provider, endpoint) → the price of `per` characters by model, in `currency`; `cjk`: what a Chinese character counts as
PRICES = {
    ("minimax", "international"): {"currency": "USD", "per": 1_000_000, "cjk": 2, "page": _MM,
                                   "models": {"speech-2.8-hd": 100.0, "speech-2.6-hd": 100.0, "speech-02-hd": 100.0,
                                              "speech-2.8-turbo": 60.0, "speech-2.6-turbo": 60.0, "speech-02-turbo": 60.0}},
    ("minimax", "china"): {"currency": "CNY", "per": 10_000, "cjk": 2, "page": _MM_CN,
                           "models": {"speech-2.8-hd": 3.5, "speech-2.6-hd": 3.5, "speech-02-hd": 3.5,
                                      "speech-2.8-turbo": 2.0, "speech-2.6-turbo": 2.0, "speech-02-turbo": 2.0}},
    ("elevenlabs", "api"): {"currency": "USD", "per": 1_000, "cjk": 1, "page": _EL, "upper": True,
                            "models": {"eleven_multilingual_v2": 0.08, "eleven_v3": 0.08, "eleven_flash_v2_5": 0.04, "eleven_turbo_v2_5": 0.04}},
    ("dashscope", "singapore"): {"currency": "USD", "per": 10_000, "cjk": 2, "page": _ALI, "models": {"qwen3-tts-flash": 0.1}},
    ("dashscope", "beijing"): {"currency": "CNY", "per": 10_000, "cjk": 2, "page": _ALI_CN, "models": {"qwen3-tts-flash": 0.8}},
}
NAME = {"minimax": "MiniMax pay-as-you-go (MINIMAX_API_KEY)", "elevenlabs": "ElevenLabs", "dashscope": "Alibaba Cloud Model Studio (DashScope)"}
UPPER = "ElevenLabs' answer does not say what it billed: settled at the estimate, an upper bound (characters a plan includes are not billed per use)"
HAN = re.compile(r"[㐀-䶿一-鿿豈-﫿\U00020000-\U0003134f]")


def paid(provider, minimax_var=None):
    """Who bills this call per use here, or None: the providers above; minimax only through MINIMAX_API_KEY."""
    if provider == "minimax":
        return NAME["minimax"] if minimax_var == "MINIMAX_API_KEY" else None
    return NAME.get(provider)


def endpoint(provider, env=None):
    """Which price list the call is billed on: minimax's international platform (the default) or China's
    (MINIMAX_BASE_URL on minimaxi.com or minimax.cn); DashScope's Beijing (the SDK's default) or Singapore
    (DASHSCOPE_BASE_URL on dashscope-intl). An address the table does not know: None (cost not known)."""
    env = os.environ if env is None else env
    if provider == "minimax":
        base = env.get("MINIMAX_BASE_URL")
        host = (urlparse(base).hostname or "") if base else "api.minimax.io"
        return "international" if host == "api.minimax.io" else "china" if host.endswith(("minimaxi.com", "minimax.cn")) else None
    if provider == "dashscope":
        base = env.get("DASHSCOPE_BASE_URL")
        host = (urlparse(base).hostname or "") if base else "dashscope.aliyuncs.com"
        return "beijing" if host == "dashscope.aliyuncs.com" else "singapore" if host == "dashscope-intl.aliyuncs.com" else None
    return "api" if provider == "elevenlabs" else None


def film_of(path):
    """The film a file is in (the nearest folder at or above it with a BRIEF.md), or None: where its spend is recorded."""
    return budget.ledger.project_of(Path(path).parent)


def chars(text, cjk):
    """The characters billed for text: every character once, a Chinese one cjk times."""
    return len(text) + (cjk - 1) * len(HAN.findall(text))


def rate(provider, model, env=None):
    """{"currency", "each" (a character's price), "cjk", "page", "upper", "endpoint"} or {"currency", "unknown": why}: the
    price of a character for this provider, endpoint and model."""
    ep = endpoint(provider, env)
    t = PRICES.get((provider, ep))
    if t is None:
        cur = {"minimax": "USD", "dashscope": "CNY", "elevenlabs": "USD"}.get(provider, "USD")
        where = (env if env is not None else os.environ).get("MINIMAX_BASE_URL" if provider == "minimax" else "DASHSCOPE_BASE_URL")
        return {"currency": cur, "cjk": 2, "unknown": f"an endpoint the price table does not have ({where})"}
    if model not in t["models"]:
        return {"currency": t["currency"], "cjk": t["cjk"], "unknown": f"{model} is not in the price table ({t['page']}, read {CHECKED})"}
    return {"currency": t["currency"], "each": t["models"][model] / t["per"], "cjk": t["cjk"], "page": t["page"],
            "upper": bool(t.get("upper")), "endpoint": ep, "price": f"{budget.money(t['models'][model], t['currency'])} per {t['per']:,} characters"}


class Refused(Exception):
    """Not called: no budget, one it would go over, or an unknown price with no Budget line; str(e) says what to write."""


class Meter:
    """One run's per-use requests: check() the whole run first, then each request() is held and settled."""
    def __init__(self, project, provider, model, tool, minimax_var=None, env=None):
        self.project, self.provider, self.model, self.tool = Path(project), provider, model, tool
        self.who = paid(provider, minimax_var)
        self.rate = rate(provider, model, env)
        self.spent = 0.0      # settled in this run (what the line at the end says)
        self.requests = 0

    def cost(self, text):
        return None if "unknown" in self.rate else round(chars(text, self.rate["cjk"]) * self.rate["each"], 6)

    def check(self, texts):
        """Before any request: the whole run (texts: each request's text) against the budget. Raises Refused."""
        texts = [t for t in texts if t]
        if not texts:
            return None
        n = sum(chars(t, self.rate["cjk"]) for t in texts)
        what = f"{self.tool}: {self.who} · {self.model} · {len(texts)} request(s), about {n:,} characters"
        if "unknown" in self.rate:
            b = budget.budget_of(self.project)
            if b["error"]:
                raise Refused(f"{what}: refused: the Budget line in {budget.where_said(b)} has {b['error']}")
            if not (b["unlimited"] or any(v > 0 for v in b["amounts"].values())):
                raise Refused(f"{what}: refused: it is billed per use and its price is not known here ({self.rate['unknown']}), and "
                              f"{'the budget is 0' if b['from'] else 'there is no budget'}. Write - Budget: and an amount (or 不限) in "
                              f"BRIEF.md's Spec to allow it; each request is then recorded as cost not known, maybe billed")
            return None
        total = round(sum(self.cost(t) for t in texts), 6)
        c = budget.check(self.project, total, self.rate["currency"])
        if not c["ok"]:
            raise Refused(f"{what} at {self.rate['price']}: {c['message']}")
        return c

    @contextlib.contextmanager
    def request(self, text, what):
        """One request: held at its estimate, then settled. The body calls r.billed(n) with the characters the answer says
        were billed, r.billed() when it says nothing (the estimate), r.not_billed() for an error answer or a request that
        never left, r.maybe() for one that timed out and is tried again; leaving with any other exception keeps the
        estimate as spent too. Both of those say it may have been billed."""
        r = _Request()
        what = f"{self.who} {self.model}: {what}"
        if "unknown" in self.rate:
            try:
                yield r
            finally:
                if not r.unbilled:
                    budget.spend(self.project, 0, self.rate["currency"], f"{what}: cost not known, maybe billed ({self.rate['unknown']})", tool=self.tool)
                    self.requests += 1
            return
        est = self.cost(text)
        with budget.hold(self.project, est, self.rate["currency"], what, tool=self.tool) as h:
            try:
                yield r
            except BaseException:
                if r.unbilled:
                    h.settle(0)
                else:
                    self.spent += est; self.requests += 1
                    self._maybe(est)
                raise
            if r.unbilled:
                h.settle(0)
                return
            if r.doubt:
                self._maybe(est)
            cost = est if r.count is None or r.doubt else round(r.count * self.rate["each"], 6)
            h.settle(cost)
            self.spent += cost; self.requests += 1

    def _maybe(self, est):
        print(f"  a request may have been billed: its estimate ({budget.money(est, self.rate['currency'])}) stays as spent; "
              f"the provider's usage page says what it was", file=sys.stderr, flush=True)

    def line(self):
        """The run's paid requests and the budget, for the end of the run."""
        if not self.requests:
            return f"  {self.who}: no request billed in this run · {budget.line(self.project)}"
        cost = "cost not known, maybe billed" if "unknown" in self.rate else budget.money(round(self.spent, 6), self.rate["currency"])
        return (f"  {self.who}: {self.requests} request(s), {cost} · {budget.line(self.project)}"
                + (f"\n  ({UPPER})" if self.rate.get("upper") else ""))


class _Request:
    def __init__(self):
        self.count, self.unbilled, self.doubt = None, False, False

    def billed(self, count=None):
        self.count = count if isinstance(count, int) and not isinstance(count, bool) and count >= 0 else None

    def not_billed(self):
        self.unbilled = True

    def maybe(self):
        self.doubt = True


def main(argv):
    rows = [{"provider": p, "endpoint": ep, "model": m, "price": v, "per": t["per"], "currency": t["currency"], "chinese_character": t["cjk"],
             "page": t["page"], "checked": CHECKED} for (p, ep), t in PRICES.items() for m, v in t["models"].items()]
    if argv == ["--json"]:
        print(json.dumps({"version": 1, "checked": CHECKED, "prices": rows}, ensure_ascii=False, indent=1))
        return 0
    if argv:
        print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
        return 2
    print(f"per-use voices (read {CHECKED}; a Chinese character counts as the page says):")
    for r in rows:
        print(f"  {r['provider']:<10} {r['endpoint']:<13} {r['model']:<24} {budget.money(r['price'], r['currency'])} per {r['per']:,}  {r['page']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
