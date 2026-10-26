"""Where bin/vh scout and bin/vh ref read a platform: its public, no-login interfaces only (CONTRIBUTING.md, 联网的命令).
Stdlib only; yt-dlp is the one outside program (tools/modules.json).

  youtube   yt-dlp, metadata only (-J; never a download): a search (ytsearchN:), a channel's videos tab, one video. Search
            and tab entries are flat, their dates approximate (youtubetab:approximate_date: "3 years ago" made a date)
  x         fxtwitter's API (api.fxtwitter.com/2/…): a profile's latest statuses (about 20), one status, the trends
  bilibili  the public view endpoint for one video and the follower count of its uploader. Search, popular and ranking
            answer a verification code to a client without a browser's cookies (HTTP 412, code -352): read them in the
            built-in browser
  hot       Baidu's realtime board, Toutiao's hot board, Google Trends' daily RSS, X's trends (fxtwitter)
  douyin, xiaohongshu: no stable interface without a login; read in the built-in browser and added by hand (scout add)

Every request goes through tools/assets/fetch.py's opener (Live; Replay for --offline; Record under OVH_RECORD), and so
does yt-dlp: the JSON it prints is recorded and replayed under the pseudo-URL "yt-dlp:<target>[ -I 1:N]". A platform
that answers with a verification page or a risk-control code raises Blocked: scout stops there and never retries round
it. Between two requests to one host there is a pause (Pace; --sleep).
"""
import datetime, hashlib, json, os, re, shlex, subprocess, sys, time, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "assets"))
import fetch   # noqa: E402

YTDLP_ENV = "OVH_YTDLP"   # a command line to run instead of the yt-dlp on PATH ("uvx yt-dlp")
BROWSER = "read it in the built-in browser and add the rows by hand (bin/vh scout add)"


class Blocked(Exception):
    """The platform asked for a verification (a captcha page, a risk-control code, HTTP 412 or 429): stop, no retry."""


class SourceError(Exception):
    """A source that did not answer as it should (said why)."""


class Pace:
    """A pause of at least `sleep` seconds between two requests to the same host (none when replaying)."""
    def __init__(self, sleep=1.0, offline=False):
        self.sleep, self.last = (0.0 if offline else sleep), {}

    def wait(self, url):
        host = urllib.parse.urlsplit(url).netloc or url.split(":")[0]
        gap = self.sleep - (time.monotonic() - self.last.get(host, -1e9))
        if gap > 0:
            time.sleep(gap)
        self.last[host] = time.monotonic()


class Net:
    """The opener (fetch.opener_from) and the pace, shared by every request of one run."""
    def __init__(self, offline=None, sleep=1.0):
        self.offline = offline
        self.opener = fetch.opener_from(offline)
        self.pace = Pace(sleep, bool(offline))
        self.blocked = {}   # host → why: a host that asked for a verification gets no further request this run
        self.notes = []     # what a look let pass and the person should still hear (a count it could not get): the caller says them

    def stop(self, host, why):
        self.blocked[host] = why
        raise Blocked(why)

    def _gate(self, url):
        host = urllib.parse.urlsplit(url).netloc or url.split(":")[0]
        if host in self.blocked:
            raise Blocked(f"{self.blocked[host]} (not asked again this run)")
        self.pace.wait(url)
        return host

    def json(self, url, headers=None):
        host = self._gate(url)
        try:
            return fetch.get_json(url, self.opener, headers)
        except fetch.FetchError as e:
            if re.search(r"HTTP (412|429)\b", str(e)):
                self.stop(host, f"{fetch.redact(url)}: {str(e).split(': ', 1)[-1]} (a verification or a rate limit)")
            raise SourceError(str(e))

    def text(self, url):
        host = self._gate(url)
        try:
            r = self.opener.open(url, None, 60)
            try:
                data = r.read(8 << 20)
            finally:
                r.close()
        except (fetch.FetchError, ConnectionError) as e:
            if re.search(r"HTTP (412|429)\b", str(e)):
                self.stop(host, f"{fetch.redact(url)}: {e}")
            raise SourceError(str(e))
        return data.decode("utf-8", errors="replace")

    def ytdlp(self, target, items=None):
        """yt-dlp's -J for a target (metadata, never a download), or the recorded one under --offline."""
        key = "yt-dlp:" + target + (f" -I 1:{items}" if items else "")
        if isinstance(self.opener, fetch.Replay):
            try:
                r = self.opener.open(key)
            except fetch.FetchError as e:
                raise SourceError(str(e))
            return json.loads(r.read().decode("utf-8"))
        cmd = shlex.split(os.environ.get(YTDLP_ENV) or "yt-dlp")
        argv = cmd + ["-J", "--flat-playlist", "--no-warnings", "--skip-download", "--extractor-args", "youtubetab:approximate_date",
                      "--sleep-requests", "1", "--socket-timeout", "30"] + (["-I", f"1:{items}"] if items else []) + ["--", target]
        self._gate("yt-dlp:")
        try:
            r = subprocess.run(argv, capture_output=True, text=True, timeout=300, errors="replace")
        except FileNotFoundError:
            raise SourceError(f"no {cmd[0]} on PATH: install it (bin/vh doctor says how), or set {YTDLP_ENV}=\"uvx yt-dlp\"")
        except subprocess.TimeoutExpired:
            raise SourceError(f"yt-dlp took over 300 s on {target}")
        err = (r.stderr or "").strip().splitlines()
        if r.returncode != 0 or not r.stdout.strip():
            last = next((x for x in reversed(err) if x.startswith("ERROR")), err[-1] if err else f"exit {r.returncode}")
            if re.search(r"HTTP Error (412|429)|captcha|confirm you.re not a bot|Sign in to confirm", last, re.I):
                self.stop("yt-dlp", f"yt-dlp on {target}: {last}")
            raise SourceError(f"yt-dlp on {target}: {last} (an old yt-dlp is the usual cause: bin/vh doctor)")
        if os.environ.get("OVH_RECORD") and not self.offline:
            record(os.environ["OVH_RECORD"], key, r.stdout.encode("utf-8"), "application/json")
        return json.loads(r.stdout)


def record(folder, key, body, ctype):
    """One response saved the way fetch.Record saves one (for yt-dlp, which makes its own requests)."""
    d = Path(folder)
    d.mkdir(parents=True, exist_ok=True)
    f = d / "responses.json"
    try:
        recs = json.loads(f.read_text(encoding="utf-8"))["responses"]
    except (OSError, ValueError, KeyError):
        recs = []
    name = "body-" + hashlib.sha256(key.encode()).hexdigest()[:12]
    (d / name).write_bytes(body[:fetch.CUT])
    rec = {"url": key, "status": 200, "headers": {"content-type": ctype}, "body": name, "bytes": len(body)}
    if len(body) > fetch.CUT:
        rec["cut"] = True
    recs = [x for x in recs if x.get("url") != key] + [rec]
    f.write_text(json.dumps({"v": 1, "responses": recs}, indent=1) + "\n", encoding="utf-8")


# ---- what a URL is ----

def platform_of(url):
    """(platform, what, native id) for a URL: ("youtube", "video", id), ("youtube", "channel", handle or id),
    ("bilibili", "video", BV…), ("x", "status", id), ("x", "profile", handle), ("douyin", "video", id or None),
    ("xiaohongshu", "post", id or None), else ("web", "page", None). Raises SourceError for what is not a URL."""
    p = urllib.parse.urlsplit(url.strip())
    if p.scheme not in ("http", "https") or not p.netloc:
        raise SourceError(f"not a URL: {url}")
    host, path = p.netloc.lower().split(":")[0], p.path
    host = host[4:] if host.startswith("www.") else host
    q = urllib.parse.parse_qs(p.query)
    if host in ("youtube.com", "m.youtube.com", "music.youtube.com"):
        if path == "/watch" and q.get("v"):
            return "youtube", "video", q["v"][0]
        m = re.match(r"/(?:shorts|live|embed)/([\w-]{6,})", path)
        if m:
            return "youtube", "video", m.group(1)
        m = re.match(r"/(@[\w.-]+|channel/[\w-]+|c/[\w.-]+|user/[\w.-]+)", path)
        if m:
            return "youtube", "channel", m.group(1)
    if host == "youtu.be" and re.fullmatch(r"/[\w-]{6,}", path):
        return "youtube", "video", path[1:]
    if host.endswith("bilibili.com"):
        m = re.search(r"/video/(BV[0-9A-Za-z]{10})", path)
        if m:
            return "bilibili", "video", m.group(1)
        m = re.match(r"/(\d+)", path) if host == "space.bilibili.com" else None
        if m:
            return "bilibili", "channel", m.group(1)
    if host == "b23.tv":
        return "bilibili", "short", None
    if host in ("x.com", "twitter.com", "mobile.twitter.com", "fxtwitter.com", "fixupx.com", "vxtwitter.com"):
        m = re.match(r"/(?:[\w]+|i/web)/status/(\d+)", path)
        if m:
            return "x", "status", m.group(1)
        m = re.fullmatch(r"/(\w{1,15})/?", path)
        if m and m.group(1).lower() not in ("home", "search", "explore", "i", "settings", "messages", "notifications"):
            return "x", "profile", m.group(1)
    if host.endswith(("douyin.com", "iesdouyin.com")):
        m = re.search(r"/(?:video|note)/(\d+)", path)
        return "douyin", "video", m.group(1) if m else None
    if host.endswith(("xiaohongshu.com", "xhslink.com")):
        m = re.search(r"/(?:explore|discovery/item)/([0-9a-f]{24})", path)
        return "xiaohongshu", "post", m.group(1) if m else None
    return "web", "page", None


def day(ts):
    """A unix time as a local date (YYYY-MM-DD), or None."""
    return datetime.date.fromtimestamp(ts).isoformat() if isinstance(ts, (int, float)) and ts > 0 else None


def num(x):
    """An int from a count as the platforms write it (123, "123", "1.2万", "3.4K"), or None."""
    if isinstance(x, bool) or x is None:
        return None
    if isinstance(x, (int, float)):
        return int(x)
    m = re.fullmatch(r"\s*([\d.,]+)\s*([万亿kKmMbB]?)\+?\s*", str(x))
    if not m:
        return None
    try:
        v = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return int(v * {"": 1, "万": 1e4, "亿": 1e8, "k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6, "b": 1e9, "B": 1e9}[m.group(2)])


def obs(platform, kind, native, url, **kw):
    """An observation as scout records it (tools/scout/scout.py has the record): the platform's fields made common."""
    o = {"platform": platform, "kind": kind, "key": f"{platform}:{native}" if native else None, "url": url}
    o.update({k: v for k, v in kw.items() if v is not None})
    m = {k: v for k, v in (kw.get("metrics") or {}).items() if v is not None}
    if m:
        o["metrics"] = m
    else:
        o.pop("metrics", None)
    return o


# ---- youtube (yt-dlp) ----

def _yt_entry(e, method, query=None, rank=None, channel=None):
    vid = e.get("id")
    ud = str(e.get("upload_date") or "")   # the platform's own date first: a timestamp's day depends on this machine's zone
    date = f"{ud[:4]}-{ud[4:6]}-{ud[6:]}" if re.fullmatch(r"\d{8}", ud) else day(e.get("timestamp"))
    ch = channel or {}
    return obs("youtube", "video", vid, f"https://www.youtube.com/watch?v={vid}", title=e.get("title"),
               author=e.get("channel") or e.get("uploader") or ch.get("author"),
               author_id=e.get("uploader_id") or e.get("channel_id") or ch.get("author_id"),
               author_url=e.get("uploader_url") or e.get("channel_url") or ch.get("author_url"),
               followers=num(e.get("channel_follower_count")) or ch.get("followers"),
               metrics={"views": num(e.get("view_count")), "likes": num(e.get("like_count")), "comments": num(e.get("comment_count"))},
               duration=num(e.get("duration")), date=date, date_approx=(True if date and not e.get("upload_date") else None),
               thumb=_thumb(e), license=e.get("license"), query=query, rank=rank, method=method)


def _thumb(e):
    """The video's cover at its plain address (480×360, no query): the one a covers sheet fetches."""
    return f"https://i.ytimg.com/vi/{e['id']}/hqdefault.jpg" if e.get("id") else None


def youtube_search(net, query, n):
    d = net.ytdlp(f"ytsearch{n}:{query}")
    return [_yt_entry(e, "yt-dlp ytsearch (flat; dates approximate)", query, i + 1) for i, e in enumerate(d.get("entries") or [])
            if isinstance(e, dict) and e.get("id")]


def youtube_channel(net, ref, n):
    """(channel facts, its latest n videos) from the channel's videos tab."""
    url = ref if ref.startswith("http") else f"https://www.youtube.com/{ref if ref.startswith(('@', 'channel/', 'c/', 'user/')) else '@' + ref}"
    url = re.sub(r"/(videos|shorts|streams|featured)?/?$", "", url) + "/videos"
    d = net.ytdlp(url, n)
    ch = {"author": d.get("channel") or d.get("uploader"), "author_id": d.get("uploader_id") or d.get("channel_id"),
          "author_url": d.get("uploader_url") or d.get("channel_url"), "followers": num(d.get("channel_follower_count"))}
    vids = [_yt_entry(e, "yt-dlp channel tab (flat; dates approximate)", rank=i + 1, channel=ch)
            for i, e in enumerate(d.get("entries") or []) if isinstance(e, dict) and e.get("id")]
    return ch, vids


def youtube_video(net, vid):
    e = net.ytdlp(f"https://www.youtube.com/watch?v={vid}")
    if not e.get("id"):
        raise SourceError(f"yt-dlp gave no video for {vid}")
    o = _yt_entry(e, "yt-dlp -J (one video)")
    if e.get("description"):
        o["description"] = e["description"][:300]
    return o


# ---- x (fxtwitter) ----

FX = "https://api.fxtwitter.com/2"


def _x_status(s, method, rank=None):
    a = s.get("author") or {}
    return obs("x", "post", s.get("id"), s.get("url") or f"https://x.com/{a.get('screen_name', 'i')}/status/{s.get('id')}",
               title=(s.get("text") or "").replace("\n", " ")[:200], author=a.get("name") or a.get("screen_name"),
               author_id=a.get("screen_name") and "@" + a["screen_name"], author_url=a.get("url"), followers=num(a.get("followers")),
               metrics={"views": num(s.get("views")), "likes": num(s.get("likes")), "comments": num(s.get("replies")),
                        "shares": num(s.get("reposts")), "favorites": num(s.get("bookmarks")), "quotes": num(s.get("quotes"))},
               date=day(s.get("created_timestamp")), thumb=next((m.get("url") for m in ((s.get("media") or {}).get("all") or [])
                                                                 if isinstance(m, dict) and m.get("type") == "photo"), None),
               rank=rank, method=method)


def _fx(net, path):
    d = net.json(FX + path)
    if not isinstance(d, dict) or d.get("code") != 200:
        code = d.get("code") if isinstance(d, dict) else None
        raise SourceError(f"fxtwitter {path}: code {code}" + (" (no such account or post, or a private one)" if code == 404 else ""))
    return d


def x_profile(net, handle):
    h = handle.lstrip("@")
    d = _fx(net, f"/profile/{urllib.parse.quote(h)}/statuses")
    posts = [s for s in d.get("results") or [] if isinstance(s, dict) and s.get("id")]
    own = [s for s in posts if not s.get("reposted_by") and ((s.get("author") or {}).get("screen_name") or "").lower() == h.lower()]
    a = (own or posts or [{}])[0].get("author") or {}
    ch = {"author": a.get("name") or h, "author_id": "@" + (a.get("screen_name") or h), "author_url": a.get("url") or f"https://x.com/{h}",
          "followers": num(a.get("followers"))}
    return ch, [_x_status(s, "fxtwitter profile statuses", i + 1) for i, s in enumerate(own)]


def x_status(net, sid):
    d = _fx(net, f"/status/{sid}")
    s = d.get("status")
    if not isinstance(s, dict):
        raise SourceError(f"fxtwitter gave no status {sid}")
    return _x_status(s, "fxtwitter status")


# ---- bilibili (the public view endpoint) ----

BILI = "https://api.bilibili.com"
BILI_BLOCK = {-352: "risk control", -412: "request blocked", -403: "access denied", -509: "too many requests", -799: "too many requests"}


def _bili(net, path):
    d = net.json(BILI + path)
    code = d.get("code") if isinstance(d, dict) else None
    if code in BILI_BLOCK:
        net.stop(urllib.parse.urlsplit(BILI).netloc, f"bilibili {path.split('?')[0]}: code {code} ({BILI_BLOCK[code]})")
    if code != 0 or not isinstance(d.get("data"), dict):
        raise SourceError(f"bilibili {path.split('?')[0]}: code {code} {d.get('message', '') if isinstance(d, dict) else ''}".strip())
    return d["data"]


def bilibili_video(net, bvid, followers=True):
    v = _bili(net, f"/x/web-interface/view?bvid={bvid}")
    st, owner = v.get("stat") or {}, v.get("owner") or {}
    fans = None
    if followers and owner.get("mid"):
        try:
            fans = num(_bili(net, f"/x/relation/stat?vmid={owner['mid']}").get("follower"))
        except Blocked as e:   # the count is a nicety: the video's own numbers stand without it, and the block stops the host
            net.notes.append(f"no follower count, blocked: {e}; the video's own numbers stand, and Bilibili is not asked again this run")
        except SourceError as e:
            net.notes.append(f"no follower count ({e}); the video's own numbers stand")
    o = obs("bilibili", "video", v.get("bvid") or bvid, f"https://www.bilibili.com/video/{v.get('bvid') or bvid}", title=v.get("title"),
            author=owner.get("name"), author_id=owner.get("mid") and str(owner["mid"]),
            author_url=owner.get("mid") and f"https://space.bilibili.com/{owner['mid']}", followers=fans,
            metrics={"views": num(st.get("view")), "likes": num(st.get("like")), "comments": num(st.get("reply")),
                     "shares": num(st.get("share")), "favorites": num(st.get("favorite")), "coins": num(st.get("coin")),
                     "danmaku": num(st.get("danmaku"))},
            duration=num(v.get("duration")), date=day(v.get("pubdate")), thumb=v.get("pic"),
            copyright={1: "original", 2: "repost"}.get(v.get("copyright")), method="bilibili view endpoint")   # the uploader's claim, not a licence
    if v.get("desc"):
        o["description"] = v["desc"][:300]
    return o


# ---- one URL, whichever platform ----

def lookup(net, url):
    """The observation of one video or post by its URL (scout post, ref add). SourceError names the browser way for a
    platform scout does not read."""
    plat, what, nid = platform_of(url)
    if plat == "youtube" and what == "video":
        return youtube_video(net, nid)
    if plat == "bilibili" and what == "video":
        return bilibili_video(net, nid)
    if plat == "x" and what == "status":
        return x_status(net, nid)
    if plat == "bilibili" and what == "short":
        raise SourceError(f"{url}: a b23.tv short link; open it once and give the bilibili.com/video/BV… address it lands on")
    if plat in ("douyin", "xiaohongshu"):
        raise SourceError(f"{url}: {plat} has no interface scout may read without a login: {BROWSER}")
    raise SourceError(f"{url}: not a video or post scout reads ({plat} {what}): a YouTube video, a Bilibili BV, an X post")


# ---- hot lists ----

def _hot_baidu(net, geo):
    d = net.json("https://top.baidu.com/api/board?platform=pc&tab=realtime")
    try:
        card = d["data"]["cards"][0]
    except (KeyError, IndexError, TypeError):
        raise SourceError("baidu: no board in the answer")
    out = []
    for i in card.get("topContent") or []:
        out.append({"rank": 0, "title": i.get("word") or i.get("query"), "pinned": True, "url": i.get("rawUrl") or i.get("url"),
                    "desc": (i.get("desc") or "")[:120] or None})
    for n, i in enumerate(card.get("content") or [], 1):   # its index counts from 0
        out.append({"rank": n, "title": i.get("word") or i.get("query"), "score": num(i.get("hotScore")),
                    "url": i.get("rawUrl") or i.get("url"), "desc": (i.get("desc") or "")[:120] or None})
    return out, "baidu realtime board (top.baidu.com)"


def _hot_toutiao(net, geo):
    d = net.json("https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc")
    rows = d.get("data") if isinstance(d, dict) else None
    if not isinstance(rows, list):
        raise SourceError("toutiao: no board in the answer")
    out = [{"rank": 0, "title": i.get("Title"), "pinned": True, "url": (i.get("Url") or "").split("?")[0] or None}
           for i in (d.get("fixed_top_data") or []) if isinstance(i, dict)]
    for n, i in enumerate(rows, 1):
        cid = i.get("ClusterIdStr") or i.get("ClusterId")
        out.append({"rank": n, "title": i.get("Title"), "score": num(i.get("HotValue")), "label": i.get("Label") or None,
                    "url": f"https://www.toutiao.com/trending/{cid}/" if cid else None})
    return out, "toutiao hot board (toutiao.com)"


def _hot_google(net, geo):
    url = f"https://trends.google.com/trending/rss?geo={urllib.parse.quote(geo or 'US')}"
    try:
        root = ET.fromstring(net.text(url))
    except ET.ParseError as e:
        raise SourceError(f"google trends: not RSS ({e})")
    ns = {"ht": "https://trends.google.com/trending/rss"}
    out = []
    for n, it in enumerate(root.iter("item"), 1):
        title = (it.findtext("title") or "").strip()
        news = [{"title": (x.findtext("ht:news_item_title", namespaces=ns) or "").strip(), "url": x.findtext("ht:news_item_url", namespaces=ns),
                 "source": x.findtext("ht:news_item_source", namespaces=ns)} for x in it.findall("ht:news_item", ns)][:2]
        out.append({"rank": n, "title": title, "score": num((it.findtext("ht:approx_traffic", namespaces=ns) or "").replace("+", "")),
                    "url": f"https://trends.google.com/trends/explore?q={urllib.parse.quote(title)}&geo={geo or 'US'}",
                    "news": [x for x in news if x["title"]] or None})
    return out, f"google trends daily rss (geo {geo or 'US'})"


def _hot_x(net, geo):
    d = _fx(net, "/trends")
    return [{"rank": num(t.get("rank")) or n, "title": t.get("name"), "label": t.get("context")}
            for n, t in enumerate(d.get("trends") or [], 1) if isinstance(t, dict)], "x trends (fxtwitter)"


HOT = {"baidu": _hot_baidu, "toutiao": _hot_toutiao, "google": _hot_google, "x": _hot_x}


def hot(net, source, geo=None):
    """(items, method) of one hot list: [{rank (0: pinned), title, score?, url?, desc?, label?, news?}]."""
    items, method = HOT[source](net, geo)
    items = [{k: v for k, v in i.items() if v is not None} for i in items if i.get("title")]
    return items, method
