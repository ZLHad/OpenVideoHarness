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
the record wins over this table. The categories follow documentary-storyboard-archival-finder's rights_classifier.py
(MIT); the table is written anew here.

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
    (r"public ?domain|\bpdm\b|^pd$|\bpd [a-z]|公有领域|公共领域|\bno copyright\b|not (?:subject to|protected by) copyright|"
     r"copyright (?:has )?expired|版权已过期|work of the u ?s(?: federal)? government|\bus government work\b", "pd", "public domain"),
]
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


def classify(text, url=None):
    """(class, why) for a licence as written, and its URL. Unrecognised: ("unknown", why)."""
    for s in (url, text):
        m = _URL.search(s or "")
        if not m:
            continue
        kind, code = m.group(1).lower(), m.group(2).lower()
        if kind == "publicdomain" and code in ("zero", "mark"):
            return ("cc0", "the CC0 deed") if code == "zero" else ("pd", "the Public Domain Mark")
        if kind == "licenses" and re.fullmatch(r"by(?:-nc)?(?:-sa|-nd)?", code):
            return "cc-" + code, f"the CC {code.upper()} deed"
        if "sampling" in code:
            return "unknown", "a CC Sampling licence (retired)"
    t = norm(text)
    if not t:
        return "unknown", "no licence given"
    for pat, cls, why in _BEFORE:
        if re.search(pat, t):
            return cls, why
    cc = _cc(t)
    if cc:
        return cc, NAMES[cc]
    for pat, cls, why in _AFTER:
        if re.search(pat, t):
            return cls, why
    return "unknown", f"not a licence this table knows ({(text or '').strip()[:60]!r})"


def risks(cls):
    """The risk tags of a class, in a fixed order: nc, nd, sa; unknown for unknown (or a class this table lacks)."""
    if cls not in CLASSES or cls == "unknown":
        return ["unknown"]
    return [r for r in ("nc", "nd", "sa") if f"-{r}" in cls]


def accepted(cls, policy):
    return policy == "record" or cls in STRICT


def attribution(cls):
    if cls.startswith("cc-by"):
        return "required"
    return {"managed": "agreement", "pd": "courtesy"}.get(cls)
