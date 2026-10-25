"""What a project may spend on paid interfaces, what it has spent, and the refusal when a call would go over. Stdlib only.

The budget: the Budget line in BRIEF.md's Spec, else LOCAL.md's 默认预算 (or Budget / Default budget) line, else none.
Amounts: $5, 5 USD, 5 美元, ¥30, 30 元, $1,000, €5, 500 TRIPO-CREDITS (a vendor's own credits); one a currency, several
currencies with commas ($5, ¥30); words around them are left out ("每支片子 20 美元" is $20). 0, none or 无 is a budget
of nothing; 不限, unlimited or no limit is no cap at all (said by the user: CLAUDE.md's floors). "default", an empty
line or a template's {…} goes on to LOCAL.md. Money is never guessed: a bare number (Budget: 5) and two amounts in one
currency ($5 per film, $20 total) are no budget, said. No budget means no paid call: hold() refuses every one, and says
what to write.

The record: assets/spend.jsonl, a line each ({"v": 1, "kind", "t", "at", "amount", "currency", "what", "tool", "asset",
"estimate", "run"}), appended in one write under an flock on assets/.spend.lock:
  payment   money spent (a line with no kind is one too): spend(), or ledger.add(…, cost=…) for what the log lacks
  hold      an estimate held for a call in flight ("id": the hold's): counted as spent until it is settled
  settle    what the held call cost ("hold": its id; 0 when it was not billed): counted instead of the estimate
Spent is the payments and the settled calls; held is the holds not settled yet (a hold whose process died stays held,
at its estimate); the budget is checked against both. Generated clips' ledgers from before v1 add their cost_usd
(unless a line names the clip). Amounts are added up per currency, never converted: a call in a currency the budget
does not name is refused (write that currency on the Budget line too).

A paid command (bin/vh image, genvideo, model3d …):
    with budget.hold(project, estimate, "USD", "image gen hero", asset="hero") as h:   # Refused: not called at all
        result = call()                       # an exception settles the hold at its estimate
        h.settle(result.cost)                 # what it cost; 0 when the vendor did not bill it
    ledger.add(project, file, id="hero", cost={"amount": total, "currency": "USD"}, …)   # adds only what the log lacks
check() answers the same question without holding anything (an estimate shown before asking).
"""
import contextlib, fcntl, json, os, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger   # noqa: E402

SPEND = Path("assets") / "spend.jsonl"
LOCK = Path("assets") / ".spend.lock"
UNITS = {"$": "USD", "us$": "USD", "usd": "USD", "美元": "USD", "美金": "USD", "¥": "CNY", "￥": "CNY", "cny": "CNY", "rmb": "CNY",
         "元": "CNY", "人民币": "CNY", "块": "CNY", "块钱": "CNY", "€": "EUR", "eur": "EUR", "欧元": "EUR"}
_NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"   # 1,000.50 or 1000.50: a comma before three digits groups them
_PRE = r"(?P<pre>us\$|\$|¥|￥|€)"
_POST = (r"(?P<post>美元|美金|人民币|块钱|块|元|欧元|(?:usd|cny|rmb|eur|gbp|jpy|hkd|twd|sgd|aud|cad|krw|chf)\b|"
         r"[a-z][a-z0-9-]{0,20}credits?\b)")   # ISO codes and a vendor's credits only: "20 for drafts" names no currency
AMOUNT = re.compile(_PRE + rf"[ \t]*(?P<n>{_NUM})|(?P<n2>{_NUM})[ \t]*" + _POST, re.I)
ZERO = re.compile(r"^[ \t]*(?:0+(?:\.0+)?|none|no|off|nothing|无|不花钱|零)[ \t]*[。.]?[ \t]*$", re.I)
UNLIMITED = re.compile(r"^[ \t]*(?:不限|无上限|不设上限|unlimited|no limit|no cap)[ \t]*[。.]?[ \t]*$", re.I)
EPS = 1e-9
BRIEF_LINE = r"^[ \t]*[-*][ \t]*(?:\*\*)?Budget(?:\*\*)?[ \t]*[:：][ \t]*(.*?)[ \t]*$"
LOCAL_LINE = r"^[ \t]*[-*]?[ \t]*(?:\*\*)?(?:默认预算|预算|default[ \t]+budget|budget)(?:\*\*)?[ \t]*[:：][ \t]*(.*?)[ \t]*$"


class Refused(Exception):
    """A paid call the budget does not allow; str(e) says why and what to change, e.check has the numbers."""
    def __init__(self, msg, check):
        super().__init__(msg)
        self.check = check


def cur_of(c):
    return UNITS.get(str(c).lower(), str(c).upper())


def parse(value):
    """{"amounts": {currency: amount}, "unlimited", "error": None or why} for a Budget line's value; None when it says
    nothing (default, empty, a template's {…}), so the next place is read."""
    v = (value or "").strip().strip("*`").strip()
    if not v or v.lower() == "default" or v.startswith("{") or v == "默认":
        return None
    if UNLIMITED.match(v):
        return {"amounts": {}, "unlimited": True, "error": None}
    if ZERO.match(v):
        return {"amounts": {}, "unlimited": False, "error": None}
    amounts, twice = {}, set()
    for m in AMOUNT.finditer(re.sub(r"[（(][^)）]*[)）]", " ", v)):
        n = float((m.group("n") or m.group("n2")).replace(",", ""))
        cur = cur_of(m.group("pre") or m.group("post") or "")
        if not ledger.CURRENCY.match(cur):
            continue
        if cur in amounts:
            twice.add(cur)
        amounts[cur] = n
    if twice:
        return {"amounts": {}, "unlimited": False, "error": f"two amounts in {', '.join(sorted(twice))} in {v!r}: write one a currency"}
    if not amounts:
        if re.search(r"\d", v) and all(float(x.replace(",", "")) == 0 for x in re.findall(_NUM, v)):
            return {"amounts": {}, "unlimited": False, "error": None}
        return {"amounts": {}, "unlimited": False, "error": f"no amount with a currency in {v!r}: write $5, ¥30 or 5 USD"}
    return {"amounts": amounts, "unlimited": False, "error": None}


def budget_of(project):
    """{"amounts", "unlimited", "from" ("BRIEF", "LOCAL.md" or None), "raw", "error"}: the project's budget, or none."""
    for raw, where in ledger.spec_lines(project, BRIEF_LINE, LOCAL_LINE):
        got = parse(raw)
        if got is not None:
            return dict(got, **{"from": where, "raw": raw})
    return {"amounts": {}, "unlimited": False, "from": None, "raw": None, "error": None}


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x >= 0


def lines(project, said=None):
    """The lines of assets/spend.jsonl that are records (a bad line is skipped, said)."""
    out = []
    try:
        text = (Path(project) / SPEND).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return out
    for n, line in enumerate(text, 1):
        if not line.strip():
            continue
        try:
            p = json.loads(line)
        except ValueError:
            p = None
        if isinstance(p, dict) and _num(p.get("amount")) and isinstance(p.get("currency"), str) and ledger.CURRENCY.match(p["currency"]) \
                and p.get("kind", "payment") in ("payment", "hold", "settle"):
            out.append(p)
        elif said is not None:
            said.append(f"{SPEND}:{n}: not a payment, a hold or a settlement: left out")
    return out


def tally(project):
    """({currency: spent}, {currency: held}, the assets the log names): payments and settlements, the holds not settled,
    and the generated clips' cost_usd from before v1 that no line names."""
    spent, held, named = {}, {}, set()
    recs = lines(project)
    settled = {p.get("hold") for p in recs if p.get("kind") == "settle"}
    for p in recs:
        k = p.get("kind", "payment")
        if k == "hold":
            if p.get("id") not in settled:
                held[p["currency"]] = held.get(p["currency"], 0.0) + p["amount"]
        else:
            spent[p["currency"]] = spent.get(p["currency"], 0.0) + p["amount"]
        named.add(p.get("asset"))
    for clip in sorted(Path(project).glob(ledger.GENCLIPS)):
        try:
            o = json.loads(clip.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(o, dict) and o.get("v") is None and _num(o.get("cost_usd")) and o.get("id") not in named:
            spent["USD"] = spent.get("USD", 0.0) + o["cost_usd"]
    rnd = lambda d: {k: round(v, 6) for k, v in d.items()}   # noqa: E731
    return rnd(spent), rnd(held), named


def spent(project):
    """{currency: spent}: the payments and the settled calls (not the holds in flight)."""
    return tally(project)[0]


def money(amount, cur):
    sym = {"USD": "$", "CNY": "¥", "EUR": "€"}.get(cur)
    s = f"{amount:,.2f}" if abs(amount - round(amount, 2)) < EPS else f"{amount:,.4f}".rstrip("0")
    return f"{sym}{s}" if sym else f"{s} {cur}"


def where_said(b):
    return {"BRIEF": "BRIEF.md", "LOCAL.md": "LOCAL.md"}.get(b["from"], "")


def check(project, amount, currency):
    """Would a call that costs amount (in currency) fit, with what is spent and held? {"ok", "amount", "currency", "budget",
    "spent", "held", "after", "short", "from", "message"}. budget is None when it names no such currency (or there is none)."""
    currency = cur_of(currency)
    b = budget_of(project)
    s, h, _ = tally(project)
    have, used = b["amounts"].get(currency), round(s.get(currency, 0.0) + h.get(currency, 0.0), 6)
    after = round(used + amount, 6)
    out = {"ok": False, "amount": amount, "currency": currency, "budget": have, "spent": s.get(currency, 0.0), "held": h.get(currency, 0.0),
           "after": after, "short": None, "from": b["from"]}
    cost, inflight = money(amount, currency), (f" ({money(h[currency], currency)} of it held by calls in flight)" if h.get(currency) else "")
    if b["error"]:
        out["message"] = f"paid call refused: the Budget line in {where_said(b)} has {b['error']}"
    elif b["unlimited"]:
        out["ok"] = True
        out["message"] = f"no cap (Budget: {b['raw']}, {where_said(b)}): {money(after, currency)} after it"
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
                          f"({where_said(b)}) is spent{inflight}: {money(out['short'], currency)} short. Raise Budget to at least "
                          f"{money(after, currency)}, or make it cheaper (a draft tier, fewer attempts)")
    else:
        out["ok"] = True
        out["message"] = f"within the budget: {money(after, currency)} of {money(have, currency)} after it ({where_said(b)})"
    return out


@contextlib.contextmanager
def locked(project):
    """The spend log's flock (assets/.spend.lock): a check and the line it allows are one step."""
    f = Path(project) / LOCK
    f.parent.mkdir(parents=True, exist_ok=True)
    with open(f, "a") as h:
        fcntl.flock(h.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(h.fileno(), fcntl.LOCK_UN)


def _append(project, rec):
    """One line, in one write (O_APPEND). Raises OSError when it cannot be written: money spent and not on record must
    not pass silently."""
    t = time.time()
    rec = {"v": 1, **rec, "t": round(t, 3), "at": ledger.iso(t), "run": os.environ.get("OVH_ACTIVITY_RUN") or None}
    f = Path(project) / SPEND
    f.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(f, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        os.write(fd, (json.dumps(rec, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8"))
    finally:
        os.close(fd)
    return rec


def _money_in(amount, currency):
    currency = cur_of(currency)
    if not (_num(amount) and ledger.CURRENCY.match(currency)):
        raise ValueError(f"not an amount of money: {amount!r} {currency!r}")
    return round(float(amount), 6), currency


class Hold:
    """An estimate held for a paid call; settle(cost) once it is known (0: not billed)."""
    def __init__(self, project, rec):
        self.project, self.rec, self.settled = project, rec, None

    def settle(self, amount, asset=None):
        if self.settled is not None:
            raise ValueError(f"hold {self.rec['id']} is settled already")
        amount, _ = _money_in(amount, self.rec["currency"])
        with locked(self.project):
            self.settled = _append(self.project, {"kind": "settle", "hold": self.rec["id"], "amount": amount, "currency": self.rec["currency"],
                                                  "what": self.rec["what"], "tool": self.rec["tool"], "asset": asset or self.rec.get("asset"),
                                                  "estimate": self.rec["amount"]})
        return self.settled


@contextlib.contextmanager
def hold(project, amount, currency, what, tool=None, asset=None):
    """Hold an estimate for a paid call: checked and written under the spend log's lock, so two calls at once cannot both
    fit in what is left. Refused (raised before anything is held) when it does not fit. Yields the Hold: settle(cost)
    when the call is done; leaving the block unsettled (an exception too) settles it at the estimate."""
    amount, currency = _money_in(amount, currency)
    with locked(project):
        c = check(project, amount, currency)
        if not c["ok"]:
            raise Refused(f"{what}: {c['message']}", c)
        rec = _append(project, {"kind": "hold", "id": f"h{int(time.time() * 1000)}-{os.getpid()}", "amount": amount, "currency": currency,
                                "what": str(what)[:300], "tool": tool or os.environ.get("OVH_ACTIVITY_CMD") or None, "asset": asset, "estimate": amount})
    h = Hold(project, rec)
    try:
        yield h
    finally:
        if h.settled is None:
            h.settle(amount)


def spend(project, amount, currency, what, tool=None, asset=None, estimate=None):
    """A payment made without a hold (bought by hand, recorded after the fact), appended under the lock; returned."""
    amount, currency = _money_in(amount, currency)
    with locked(project):
        return _append(project, {"kind": "payment", "amount": amount, "currency": currency, "what": str(what)[:300],
                                 "tool": tool or os.environ.get("OVH_ACTIVITY_CMD") or None, "asset": asset, "estimate": estimate})


def record_cost(project, asset, cost, what, tool=None):
    """What an asset cost, as ledger.add records it: a payment of what the log does not have for this asset yet (its
    holds' settlements and payments in that currency), or None when it has it all."""
    amount, currency = _money_in(cost["amount"], cost["currency"])
    with locked(project):
        have = sum(p["amount"] for p in lines(project) if p.get("asset") == asset and p["currency"] == currency and p.get("kind", "payment") != "hold")
        if amount - have <= EPS:
            return None
        return _append(project, {"kind": "payment", "amount": round(amount - have, 6), "currency": currency, "what": str(what)[:300],
                                 "tool": tool or os.environ.get("OVH_ACTIVITY_CMD") or None, "asset": asset, "estimate": None})


def summary(project):
    """{"limit": {currency: amount}, "unlimited", "from", "raw", "error", "spent", "held", "left" (all {currency: amount}),
    "over": [currencies past their limit, or spent with none]}: the one shape bin/vh assets list --json and status --json
    give, and the review page shows."""
    b = budget_of(project)
    s, h, _ = tally(project)
    curs = set(s) | set(h)
    left = {} if b["unlimited"] else {k: round(v - s.get(k, 0.0) - h.get(k, 0.0), 6) for k, v in b["amounts"].items()}
    over = [] if b["unlimited"] else sorted([k for k, v in left.items() if v < -EPS] + [k for k in curs if k not in b["amounts"] and s.get(k, 0) + h.get(k, 0) > EPS])
    return {"limit": b["amounts"], "unlimited": b["unlimited"], "from": b["from"], "raw": b["raw"], "error": b["error"], "spent": s, "held": h,
            "left": left, "over": over}


def line(project):
    """One line: spent and budget, per currency ("spent $1.20 of $5.00 (BRIEF.md)"; "no budget: paid calls are off")."""
    s = summary(project)
    if s["error"]:
        return f"budget: the Budget line has {s['error']}"
    curs = list(s["limit"]) + [k for k in list(s["spent"]) + list(s["held"]) if k not in s["limit"]]
    curs = list(dict.fromkeys(curs))
    held = (lambda k: f" (+{money(s['held'][k], k)} held)" if s["held"].get(k) else "")   # noqa: E731
    if s["unlimited"]:
        return f"budget: no cap ({where_said(s)})" + (": spent " + ", ".join(money(s["spent"].get(k, 0.0), k) + held(k) for k in curs) if curs else "")
    if not curs:
        return "budget: none (paid calls are off: Budget in BRIEF.md, or 默认预算 in LOCAL.md)" if not s["from"] else f"budget: 0 ({where_said(s)}): paid calls are off"
    bits = [f"{money(s['spent'].get(k, 0.0), k)}{held(k)} of {money(s['limit'][k], k)}" if k in s["limit"] else
            f"{money(s['spent'].get(k, 0.0), k)}{held(k)} with no {k} budget" for k in curs]
    return f"spent {', '.join(bits)}" + (f" ({where_said(s)})" if s["from"] else "") + (" · over: " + ", ".join(s["over"]) if s["over"] else "")
