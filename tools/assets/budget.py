"""What a project may spend on paid services, what it has spent, and the refusal when a call would go over. Stdlib only.

The budget: the Budget line in BRIEF.md's Spec, else LOCAL.md's 默认预算 (or Budget / Default budget) line, else none.
Amounts: $5, 5 USD, 5 美元, ¥30, 30 元, 30 CNY, €5, 500 TRIPO-CREDITS (a vendor's own credits), several with commas
($5, ¥30); words around them are left out ("每支片子 20 美元" is $20). 0, none or 无 is a budget of nothing. "default", an
empty line or a template's {…} goes on to LOCAL.md. A bare number with no currency (Budget: 5) is no budget: money is
never guessed. No budget means no paid call (CLAUDE.md's floors): require() refuses every one, and says what to write.

Spent: assets/spend.jsonl, one line a payment ({"v": 1, "t", "at", "amount", "currency", "what", "tool", "asset", "estimate",
"run"}), appended in one write (O_APPEND, as .ovh/activity.jsonl), so a failed attempt counts as much as a kept one; plus
the costs of generated clips' ledgers from before v1 (cost_usd), which predate the log (unless a payment names the clip). Costs are added up per currency,
never converted: a call in a currency the budget does not name is refused (write that currency on the Budget line too).

The paid commands (bin/vh image, genvideo, model3d …) call require(project, amount, currency, what) with their estimate
before the call: it returns the check, or raises Refused saying how much is missing; then spend() with what the call
cost, once a call (an attempt that failed too), and ledger.add(…, cost=…) for the file they keep.
"""
import json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger   # noqa: E402

SPEND = Path("assets") / "spend.jsonl"
UNITS = {"$": "USD", "us$": "USD", "usd": "USD", "美元": "USD", "美金": "USD", "¥": "CNY", "￥": "CNY", "cny": "CNY", "rmb": "CNY",
         "元": "CNY", "人民币": "CNY", "块": "CNY", "块钱": "CNY", "€": "EUR", "eur": "EUR", "欧元": "EUR"}
_PRE = r"(?P<pre>us\$|\$|¥|￥|€)"
_POST = (r"(?P<post>美元|美金|人民币|块钱|块|元|欧元|(?:usd|cny|rmb|eur|gbp|jpy|hkd|twd|sgd|aud|cad|krw|chf)\b|"
         r"[a-z][a-z0-9-]{0,20}credits?\b)")   # ISO codes and a vendor's credits only: "20 for drafts" names no currency
AMOUNT = re.compile(_PRE + r"\s*(?P<n>\d+(?:\.\d+)?)|(?P<n2>\d+(?:\.\d+)?)\s*" + _POST, re.I)
ZERO = re.compile(r"^\s*(?:0+(?:\.0+)?|none|no|off|nothing|无|不花钱|零)\s*[。.]?\s*$", re.I)
EPS = 1e-9


class Refused(Exception):
    """A paid call the budget does not allow; str(e) says why and what to change."""
    def __init__(self, msg, check):
        super().__init__(msg)
        self.check = check


BRIEF_LINE = r"^\s*[-*]\s*(?:\*\*)?Budget(?:\*\*)?\s*[:：]\s*(.*?)\s*$"
LOCAL_LINE = r"^\s*[-*]?\s*(?:\*\*)?(?:默认预算|预算|default\s+budget|budget)(?:\*\*)?\s*[:：]\s*(.*?)\s*$"


def parse(value):
    """{"amounts": {currency: amount}, "error": None or why} for a Budget line's value; None when it says nothing (default,
    empty, a template's {…}), so the next place is read."""
    v = (value or "").strip().strip("*`").strip()
    if not v or v.lower() == "default" or v.startswith("{") or "默认" == v:
        return None
    if ZERO.match(v):
        return {"amounts": {}, "error": None}
    amounts = {}
    for m in AMOUNT.finditer(re.sub(r"[（(][^)）]*[)）]", " ", v)):
        n = float(m.group("n") or m.group("n2"))
        u = (m.group("pre") or m.group("post") or "").lower()
        cur = UNITS.get(u) or u.upper()
        if not ledger.CURRENCY.match(cur):
            continue
        amounts[cur] = amounts.get(cur, 0.0) + n
    if not amounts:
        if re.search(r"\d", v) and all(float(x) == 0 for x in re.findall(r"\d+(?:\.\d+)?", v)):
            return {"amounts": {}, "error": None}
        return {"amounts": {}, "error": f"no amount with a currency in {v!r}: write $5, ¥30 or 5 USD"}
    return {"amounts": amounts, "error": None}


def budget_of(project):
    """{"amounts", "from" ("BRIEF", "LOCAL.md" or None), "raw", "error"}: the project's budget, or no budget (amounts {})."""
    for raw, where in ledger.spec_lines(project, BRIEF_LINE, LOCAL_LINE):
        got = parse(raw)
        if got is not None:
            return dict(got, **{"from": where, "raw": raw})
    return {"amounts": {}, "from": None, "raw": None, "error": None}


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x >= 0


def payments(project, said=None):
    """The lines of assets/spend.jsonl that are payments (a bad line is skipped, said)."""
    f = Path(project) / SPEND
    out = []
    try:
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for n, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            p = json.loads(line)
        except ValueError:
            p = None
        if isinstance(p, dict) and _num(p.get("amount")) and isinstance(p.get("currency"), str) and ledger.CURRENCY.match(p["currency"]):
            out.append(p)
        elif said is not None:
            said.append(f"{SPEND}:{n}: not a payment, left out")
    return out


def spent(project):
    """{currency: total}: the payments, and the costs of generated clips' ledgers from before v1."""
    tot, paid_for = {}, set()
    for p in payments(project):
        tot[p["currency"]] = tot.get(p["currency"], 0.0) + p["amount"]
        paid_for.add(p.get("asset"))
    for clip in sorted(Path(project).glob(ledger.GENCLIPS)):
        try:
            o = json.loads(clip.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(o, dict) and o.get("v") is None and _num(o.get("cost_usd")) and o.get("id") not in paid_for:   # once
            tot["USD"] = tot.get("USD", 0.0) + o["cost_usd"]
    return {k: round(v, 6) for k, v in tot.items()}


def money(amount, cur):
    sym = {"USD": "$", "CNY": "¥", "EUR": "€"}.get(cur)
    s = f"{amount:,.2f}" if abs(amount - round(amount, 2)) < EPS else f"{amount:,.4f}".rstrip("0")
    return f"{sym}{s}" if sym else f"{s} {cur}"


def where_said(b):
    return {"BRIEF": "BRIEF.md", "LOCAL.md": "LOCAL.md"}.get(b["from"], "")


def check(project, amount, currency):
    """Would a call that costs amount (in currency) fit? {"ok", "amount", "currency", "budget", "spent", "after", "short",
    "from", "message"}. budget is None when the budget names no such currency (or there is none)."""
    currency = UNITS.get(currency.lower(), currency.upper())
    b, s = budget_of(project), spent(project)
    have, used = b["amounts"].get(currency), s.get(currency, 0.0)
    after = round(used + amount, 6)
    out = {"ok": False, "amount": amount, "currency": currency, "budget": have, "spent": used, "after": after, "short": None, "from": b["from"]}
    cost = money(amount, currency)
    if b["error"]:
        out["message"] = f"paid call refused: the Budget line in {where_said(b)} has {b['error']}"
    elif have is None and b["amounts"]:
        names = ", ".join(money(v, k) for k, v in b["amounts"].items())
        out["message"] = (f"paid call refused: it costs {cost} and the budget ({names}, {where_said(b)}) has no {currency}: add it, "
                          f"e.g. Budget: {names}, {money(max(amount, 1), currency)}")
    elif have is None:
        out["message"] = (f"paid call refused: {'the budget is 0' if b['from'] else 'no budget'} "
                          f"({'Budget: ' + b['raw'] + ' in ' + where_said(b) if b['from'] else 'no Budget line in BRIEF.md, no 默认预算 in LOCAL.md'}); "
                          f"it would cost {cost}: write - Budget: {money(amount, currency)} (or more) in BRIEF.md's Spec to allow it")
        out["short"] = amount
    elif after > have + EPS:
        out["short"] = round(after - have, 6)
        out["message"] = (f"paid call refused: it costs {cost}, and {money(used, currency)} of the {money(have, currency)} budget "
                          f"({where_said(b)}) is spent: {money(out['short'], currency)} short. Raise Budget to at least "
                          f"{money(after, currency)}, or make it cheaper (a draft tier, fewer attempts)")
    else:
        out["ok"] = True
        out["message"] = f"within the budget: {money(after, currency)} of {money(have, currency)} after it ({where_said(b)})"
    return out


def require(project, amount, currency, what=""):
    """check(), or Refused with its message (what: the call, put in front)."""
    c = check(project, amount, currency)
    if not c["ok"]:
        raise Refused((f"{what}: " if what else "") + c["message"], c)
    return c


def spend(project, amount, currency, what, tool=None, asset=None, estimate=None):
    """Append one payment to assets/spend.jsonl (one write, O_APPEND) and return it. Raises OSError when it cannot be
    written: money spent and not on record must not pass silently."""
    currency = UNITS.get(currency.lower(), currency.upper())
    if not (_num(amount) and ledger.CURRENCY.match(currency)):
        raise ValueError(f"not a payment: {amount!r} {currency!r}")
    t = time.time()
    rec = {"v": 1, "t": round(t, 3), "at": ledger.iso(t), "amount": amount, "currency": currency, "what": str(what)[:300],
           "tool": tool or os.environ.get("OVH_ACTIVITY_CMD") or None, "asset": asset, "estimate": estimate,
           "run": os.environ.get("OVH_ACTIVITY_RUN") or None}
    f = Path(project) / SPEND
    f.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    return rec


def summary(project):
    """{"budget": {currency: amount}, "from", "raw", "error", "spent": {currency: total}, "left": {currency: amount},
    "over": [currencies over their budget or spent without one]}: what status --json and the review page show."""
    b, s = budget_of(project), spent(project)
    left = {k: round(v - s.get(k, 0.0), 6) for k, v in b["amounts"].items()}
    over = sorted([k for k, v in left.items() if v < -EPS] + [k for k, v in s.items() if v > EPS and k not in b["amounts"]])
    return {"budget": b["amounts"], "from": b["from"], "raw": b["raw"], "error": b["error"], "spent": s, "left": left, "over": over}


def line(project):
    """One line: spent and budget, per currency ("spent $1.20 of $5.00 (BRIEF.md)"; "no budget: paid calls are off")."""
    s = summary(project)
    if s["error"]:
        return f"budget: the Budget line has {s['error']}"
    curs = list(s["budget"]) + [k for k in s["spent"] if k not in s["budget"]]
    if not curs:
        return "budget: none (paid calls are off: Budget in BRIEF.md, or 默认预算 in LOCAL.md)" if not s["from"] else f"budget: 0 ({where_said(s)}): paid calls are off"
    bits = [f"{money(s['spent'].get(k, 0.0), k)} of {money(s['budget'][k], k)}" if k in s["budget"] else f"{money(s['spent'][k], k)} with no {k} budget"
            for k in curs]
    return f"spent {', '.join(bits)}" + (f" ({where_said(s)})" if s["from"] else "") + (" · over: " + ", ".join(s["over"]) if s["over"] else "")
