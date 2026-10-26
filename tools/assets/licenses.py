"""A licence string (and its URL) to a clearance class, and what each class asks of a film. Stdlib only.

classify(text, url=None) -> (class, why). The classes (an asset record's license.class, tools/assets/asset.schema.json):
  pd           public domain: expired, a government work, the Public Domain Mark, "no copyright"
  cc0          CC0 1.0, a dedication to the public domain (Kenney's packs are CC0)
  cc-by        CC BY, any version (Attribution)
  cc-by-sa     CC BY-SA (ShareAlike: a film that adapts it must carry the same licence)
  cc-by-nc     CC BY-NC (NonCommercial)
  cc-by-nc-sa  CC BY-NC-SA
  cc-by-nd     CC BY-ND (NoDerivatives: no edit, no sync to pictures)
  cc-by-nc-nd  CC BY-NC-ND
  free         a permissive licence that is not CC: MIT, BSD, Apache-2.0, ISC, Unlicense, zlib; the font licences that allow
               embedding and use (SIL OFL, Arphic, GUST, IPA, Ubuntu); the Pixabay, Unsplash, Pexels, Mixkit and Sonniss
               content licences
  managed      used under an agreement: stock bought for the film (rights-managed or royalty-free), "used with permission",
               a licence from the owner (the agreement belongs in the record: its note, or terms)
  own          made in the project (code, a TTS take, a recording) or the user's own material
  generated    a model's output under its vendor's terms (with aigc: true; references/genvideo-ledger.md has the terms)
  unknown      anything else: no licence, a bare copyright notice ("all rights reserved", ©), "no known copyright
               restrictions", a software copyleft (GPL family) whose terms for media need reading, a retired CC licence,
               "Creative Commons" without saying which
Anything not recognised is unknown (not cleared): a licence is never guessed upward, and an explicit class given with
the record wins over this table. A text with a restriction or a negation the table cannot weigh ("editorial use only",
"for personal use", "non-commercial", "not in the public domain", "except", 仅限, 不得商用) is unknown, whatever else
it names: only the CC elements (NC, ND, SA) are read as part of a licence. When the text and the URL give different
classes, the stricter one is taken (the one whose risks hold the other's: CC BY with a BY-NC deed is BY-NC); classes
that cannot be ranked so (BY-SA against BY-ND, a CC deed against a vendor's licence) are unknown. The categories follow
documentary-storyboard-archival-finder's rights_classifier.py (MIT); the table is written anew here.

risks(class) -> the risk tags a film inherits: nc, nd, sa, unknown. accepted(class, policy) -> True when the BRIEF's
Assets policy takes it: strict takes pd, cc0, cc-by, free, managed, own and generated (clear for commercial use, with
a credit at most); record takes everything, and bin/vh assets check lists the risks instead of failing on them.
attribution(class) -> "required" (the BY family), "agreement" (managed: as the agreement says), "courtesy" (public
domain: a credit is good manners, NASA asks for one) or None.
"""
import re

CLASSES = ("pd", "cc0", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa", "cc-by-nd", "cc-by-nc-nd",
           "free", "managed", "own", "generated", "unknown")
POLICIES = ("strict", "record")
STRICT = {"pd", "cc0", "cc-by", "free", "managed", "own", "generated"}
NAMES = {"pd": "public domain", "cc0": "CC0", "cc-by": "CC BY", "cc-by-sa": "CC BY-SA", "cc-by-nc": "CC BY-NC",
         "cc-by-nc-sa": "CC BY-NC-SA", "cc-by-nd": "CC BY-ND", "cc-by-nc-nd": "CC BY-NC-ND", "free": "a permissive licence",
         "managed": "used under an agreement", "own": "own work", "generated": "generated (vendor terms)", "unknown": "unknown"}
RISK_WORDS = {"nc": "non-commercial", "nd": "no derivatives", "sa": "share-alike", "unknown": "no licence on record"}

# (pattern on the normalised text, class, why), tried in order before and after the CC names: the first match wins
_BEFORE = [
    (r"no known copyright restrictions", "unknown", "\"no known copyright restrictions\" is a statement, not a licence"),
    (r"\bsampling\b", "unknown", "a CC Sampling licence (retired)"),
    (r"\bcc ?0\b|\bcc zero\b|\bcczero\b|public ?domain dedication|\bkenney\b", "cc0", "CC0"),
    (r"public ?domain|\bpdm\b|^pd$|\bpd [a-z]|公有领域|公共领域|copyright (?:has )?expired|版权已过期|"
     r"work of the u ?s(?: federal)? government|\bus government work\b", "pd", "public domain"),
]
# a restriction or a negation the table cannot weigh: in any text it makes the licence unknown (the CC elements NC, ND
# and SA are read by _cc, not here). Chinese: 仅限 / 仅供 (only), 个人 (personal), 内部 (internal), 不得 / 不可 / 禁止商用
# / 非商用 (must not, not commercial), 除外 (except)
_LIMITS = (r"\b(?:not|never|without|except|excluding|unless|only|editorial|personal|internal|restricted|prohibited|forbidden)\b|"
           r"\bno\b|仅限|仅供|个人|内部|不得|不可|禁止商用|非商用|除外|编辑用途")
_NONCC_NC = r"\bnc\b|non ?commercial|非商业"   # outside a CC licence: a restriction, not an element
_AFTER = [
    (r"\bgpl\b|\blgpl\b|\bagpl\b|gnu (?:general|lesser|affero)", "unknown", "a software copyleft licence (GPL family): read its terms for media"),
    (r"\bmit\b|\bapache\b|\bbsd\b|\bisc\b|\bunlicense\b|\bzlib\b|\bwtfpl\b|\bofl\b|open font licen[cs]e|\barphic\b|\bgust\b|"
     r"\bipa font\b|ubuntu font|\bpixabay\b|\bunsplash\b|\bpexels\b|\bmixkit\b|\bsonniss\b", "free", "a permissive licence"),
    (r"rights ?managed|licen[cs]ed (?:from|by)|licen[cs]e from|\bpurchased\b|\bbought\b|\binvoice\b|used with permission|"
     r"with (?:the )?(?:owner s |author s |artist s |creator s )?permission|permission granted|\bagreement\b|royalty ?free|"
     r"已授权|获得授权|经授权|授权使用|已购|购买|\buppbeat\b|\bgetty\b|shutterstock|adobe stock|\bistock\b|\benvato\b|\bartlist\b|"
     r"epidemic sound|\bmusicbed\b|\bstoryblocks\b", "managed", "used under an agreement"),
    (r"^own$|\bown work\b|\bself ?made\b|\bmade (?:here|in (?:this|the) project|by us)\b|\boriginal work\b|\buser s own\b|"
     r"\bour own\b|procedural(?:ly)? generated|code ?generated|generated (?:in|by) (?:the )?code|自制|原创|代码生成|程序生成|"
     r"自己(?:画|拍|录|做|写)|用户(?:提供|自有|自己)", "own", "own work"),
    (r"\bgenerated\b|\bai ?generated\b|\baigc\b|ai ?生成|生成式|模型生成", "generated", "a model's output"),
    (r"all rights reserved|版权所有|\bcopyright\b|©", "unknown", "a copyright notice, no licence to us"),
]
# a CC licence: named with "CC" / Creative Commons / 知识共享, by its legal name ("Attribution-NonCommercial 4.0
# International", "署名-相同方式共享 4.0"), or by the bare code Openverse gives (by, by-nc-sa)
_CC_CTX = r"\bcc\b|creative ?commons|知识共享"
_CC_PARTS = r"\bby\b|\battribution\b|署名|\bnc\b|\bnd\b|\bsa\b|non ?commercial|share ?alike|no ?deriv|非商业|相同方式共享|禁止演绎"
_CC_LEGAL = (r"^attribution(?: (?:non ?commercial|share ?alike|no ?deriv\w*))* \d|"
             r"^署名(?:\s*(?:非商业性使用|相同方式共享|禁止演绎))*\s*\d")
_CC_CODE = r"^by(?: (?:nc|sa|nd))*(?: \d(?: \d)?)?(?: (?:international|generic|unported))?$"
_NC, _ND, _SA = r"\bnc\b|non ?commercial|非商业", r"\bnd\b|no ?deriv|禁止演绎", r"\bsa\b|share ?alike|相同方式共享"
# creativecommons.org/licenses/<code>/ and /publicdomain/<zero|mark>/
_URL = re.compile(r"creativecommons\.org/(licenses|publicdomain)/([a-z+-]+)", re.I)


def norm(s):
    """Lower case, separators to single spaces: "CC-BY_SA 4.0" and "cc by sa 4.0" read alike."""
    s = (s or "").lower().replace("–", "-").replace("—", "-")
    s = re.sub(r"[\s_\-/.,;:()\[\]\"'“”‘’]+", " ", s)
    return s.strip()


def _cc(t):
    """The CC class of normalised text that names a CC licence, else None."""
    if not ((re.search(_CC_CTX, t) and re.search(_CC_PARTS, t)) or re.search(_CC_LEGAL, t) or re.fullmatch(_CC_CODE, t)):
        return None
    nc, nd, sa = (bool(re.search(p, t)) for p in (_NC, _ND, _SA))
    if nd and sa:
        return None   # no such licence
    return "cc-by" + ("-nc" if nc else "") + ("-sa" if sa else "-nd" if nd else "")


def _from_url(url):
    """(class, why) from a creativecommons.org deed, or None."""
    m = _URL.search(url or "")
    if not m:
        return None
    kind, code = m.group(1).lower(), m.group(2).lower()
    if kind == "publicdomain" and code in ("zero", "mark"):
        return ("cc0", "the CC0 deed") if code == "zero" else ("pd", "the Public Domain Mark")
    if kind == "licenses" and code == "publicdomain":   # CC's Public Domain Dedication and Certification, retired for CC0 and the Mark
        return "pd", "the CC Public Domain Dedication or Certification (before CC0)"
    if kind == "licenses" and re.fullmatch(r"by(?:-nc)?(?:-sa|-nd)?", code):
        return "cc-" + code, f"the CC {code.upper()} deed"
    if "sampling" in code:
        return "unknown", "a CC Sampling licence (retired)"
    return None


def _from_text(text):
    """(class, why) from a licence as written, or None when it is empty."""
    m = _URL.search(text or "")   # a deed's URL written as the licence
    if m:
        return _from_url(text)
    t = norm(text)
    if not t:
        return None
    for pat, cls, why in _BEFORE[:2]:   # the statements that are no licence
        if re.search(pat, t):
            return cls, why
    cc = _cc(t)
    lim = re.search(_LIMITS, t)
    if cc:
        return ("unknown", f"{NAMES[cc]} with a restriction it cannot carry ({lim.group(0)!r})") if lim else (cc, NAMES[cc])
    nc = re.search(_NONCC_NC, t)
    if lim or nc:
        return "unknown", f"a restriction or a negation the table cannot weigh ({(lim or nc).group(0)!r}): give the class when it is clear"
    for pat, cls, why in _BEFORE[2:] + _AFTER:
        if re.search(pat, t):
            return cls, why
    return "unknown", None   # not a licence this table knows: a URL that names one is read instead


DEEDS = {"pd", "cc0"} | {c for c in CLASSES if c.startswith("cc-by")}


def stricter(a, b):
    """The stricter of two classes (the one whose risks hold the other's; pd over cc0; a BY licence over pd or cc0), or
    None when they cannot be ranked (BY-SA against BY-ND, a deed against a vendor's licence)."""
    if a == b:
        return a
    if a not in DEEDS or b not in DEEDS:
        return None
    if {a, b} == {"pd", "cc0"}:
        return "pd"
    ra, rb = set(risks(a)), set(risks(b))
    if ra < rb or ra == rb and b.startswith("cc-by") and not a.startswith("cc-by"):
        return b
    if rb < ra or ra == rb and a.startswith("cc-by") and not b.startswith("cc-by"):
        return a
    return None


def classify(text, url=None):
    """(class, why) for a licence as written, and its URL. Unrecognised: ("unknown", why)."""
    t, u = _from_text(text), _from_url(url)
    if t and t[1] is None:   # a text the table does not know: the URL's deed, when there is one
        t = None if u else ("unknown", f"not a licence this table knows ({(text or '').strip()[:60]!r})")
    if not t and not u:
        return "unknown", f"not a licence this table knows ({url.strip()[:80]!r})" if (url or "").strip() else "no licence given"
    if not t or not u or t[0] == u[0]:
        return t or u
    s = stricter(t[0], u[0])
    if s:
        return s, f"the stricter of the text ({t[1]}) and the URL ({u[1]})"
    return "unknown", f"the text ({t[1]}) and the URL ({u[1]}) do not agree"


def risks(cls):
    """The risk tags of a class, in a fixed order: nc, nd, sa; unknown for unknown (or a class this table lacks)."""
    if not isinstance(cls, str) or cls not in CLASSES or cls == "unknown":
        return ["unknown"]
    return [r for r in ("nc", "nd", "sa") if f"-{r}" in cls]


def accepted(cls, policy):
    return policy == "record" or isinstance(cls, str) and cls in STRICT


def attribution(cls):
    if not isinstance(cls, str):
        return None
    if cls.startswith("cc-by"):
        return "required"
    return {"managed": "agreement", "pd": "courtesy"}.get(cls)
