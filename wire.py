# wire.py — the Navi news wire engine (0.2.0e Build 7, #188).
#
# A bridge-side RSS/Atom fetcher on an interval over a curated
# set of security news sources, plus the CVE sources (NVD
# recent + CISA KEV additions). Outbound-only, no accounts, no
# keys, local storage only (config/wire/wire.json). The store
# keeps headline, source, published, link and a summary-depth
# excerpt per item; dedupe is by link/guid, and a story whose
# text changes after first sighting updates in place and is
# marked developing — that is how she can say "this one is
# still moving" honestly. Retention defaults to 7 days and is
# the operator's setting.
#
# Honesty rules, same as the Center's: the wire names its
# staleness (last successful fetch per source), and a dead feed
# is a named sentence on every surface, never silent emptiness.
# The composed behavior has a name: asking "what's the sitch"
# returns the situation briefing — top news, new CVEs,
# developing stories — with her assessment as a clearly
# separate layer ("My take"), never dressed as reporting.
#
# Stdlib only; it never imports the bridge — the bridge imports
# it and hands it a settings getter (the Guardian's shape). The
# fetcher is injectable so the benches run on recorded fixtures.

import gzip
import html as html_mod
import json
import os
import re
import threading
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

NEWS_SOURCES = [
    ("bleepingcomputer", "BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
    ("hackernews", "The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
    ("krebs", "Krebs on Security", "https://krebsonsecurity.com/feed/"),
    ("darkreading", "Dark Reading", "https://www.darkreading.com/rss.xml"),
    ("securityweek", "SecurityWeek", "https://www.securityweek.com/feed/"),
    ("therecord", "The Record", "https://therecord.media/feed/"),
    ("cisa", "CISA advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
]
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
SOURCE_LABELS = dict((sid, label) for sid, label, _u in NEWS_SOURCES)
SOURCE_LABELS.update({"kev": "CISA KEV", "nvd": "NVD"})
MAX_ITEMS = 400
EXCERPT_CAP = 1200


def _fetch(url, state, timeout=25):
    # One conditional GET (the Center's fetcher shape). Returns
    # (status, bytes, new_state); raises on failure, and the
    # caller records the failure as a sentence.
    req = urllib.request.Request(url, headers={
        "User-Agent": "Apex-Wire/1.0 (local-first news wire; operator machine)",
        "Accept-Encoding": "gzip",
    })
    if state.get("etag"):
        req.add_header("If-None-Match", state["etag"])
    if state.get("lastmod"):
        req.add_header("If-Modified-Since", state["lastmod"])
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                raw = gzip.decompress(raw)
            return 200, raw, {
                "etag": resp.headers.get("ETag") or state.get("etag") or "",
                "lastmod": resp.headers.get("Last-Modified") or state.get("lastmod") or "",
            }
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return 304, b"", state
        raise


def _iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)) if ts else ""


def _parse_date(value):
    # RFC 822 (RSS) or ISO 8601 (Atom / APIs) -> epoch, or 0.
    if not value:
        return 0
    text = str(value).strip()
    try:
        dt = parsedate_to_datetime(text)
        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return 0


_TAG_RE = re.compile(r"<[^>]+>")


def _plain(raw_html, cap=EXCERPT_CAP):
    if not raw_html:
        return ""
    text = _TAG_RE.sub(" ", str(raw_html))
    text = html_mod.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:cap]


def _local(tag):
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _child_text(el, names):
    for child in el:
        if _local(child.tag) in names:
            text = "".join(child.itertext()).strip() if child is not None else ""
            if text:
                return text
    return ""


def feed_items(raw):
    # RSS 2.0, RDF/RSS 1.0 and Atom in one pass: item/entry
    # elements wherever they sit, fields by local name.
    root = ET.fromstring(raw)
    out = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        title = _child_text(el, ("title",))
        link = _child_text(el, ("link",))
        if not link:
            for child in el:
                if _local(child.tag) == "link":
                    href = child.get("href") or ""
                    rel = child.get("rel") or "alternate"
                    if href and rel in ("alternate", ""):
                        link = href
                        break
        guid = _child_text(el, ("guid", "id")) or link
        published = 0
        for name in ("pubDate", "published", "date", "updated"):
            published = _parse_date(_child_text(el, (name,)))
            if published:
                break
        body = (_child_text(el, ("encoded", "content", "description", "summary")) or "")
        excerpt = _plain(body)
        if title and link:
            out.append({
                "key": guid or link, "title": title.strip(),
                "link": link.strip(), "published": published,
                "excerpt": excerpt,
            })
    return out


def kev_items(raw, since_ts):
    # KEV additions inside the retention window become wire
    # items (the catalog itself is the Center's store, not the
    # wire's). dateAdded is a plain date; it stamps at 00:00Z.
    feed = json.loads(raw.decode("utf-8", "replace"))
    out = []
    for v in feed.get("vulnerabilities") or []:
        added = _parse_date(str(v.get("dateAdded") or "") + "T00:00:00Z"
                            if v.get("dateAdded") else "")
        if not added or added < since_ts:
            continue
        cid = str(v.get("cveID") or "").strip()
        if not cid:
            continue
        vendor = str(v.get("vendorProject") or "").strip()
        product = str(v.get("product") or "").strip()
        bits = []
        if vendor or product:
            bits.append(" — ".join(x for x in (vendor, product) if x))
        if v.get("shortDescription"):
            bits.append(str(v["shortDescription"]))
        if v.get("dueDate"):
            bits.append("Federal remediation due " + str(v["dueDate"]) + ".")
        if str(v.get("knownRansomwareCampaignUse") or "").lower() == "known":
            bits.append("Known ransomware campaign use.")
        out.append({
            "key": "kev:" + cid, "kind": "kev", "cveId": cid,
            "title": cid + " added to the Known Exploited catalog",
            "link": "https://www.cisa.gov/known-exploited-vulnerabilities-catalog",
            "published": added, "excerpt": _plain(" ".join(bits)),
        })
    return out


def nvd_items(raw):
    # The NVD 2.0 window response, wire-shaped: the CVE id is
    # the headline; the English description is the excerpt.
    data = json.loads(raw.decode("utf-8", "replace"))
    out = []
    for item in data.get("vulnerabilities") or []:
        cve = item.get("cve") or {}
        cid = str(cve.get("id") or "").strip()
        if not cid:
            continue
        desc = ""
        for d in cve.get("descriptions") or []:
            if d.get("lang") == "en":
                desc = str(d.get("value") or "")
                break
        out.append({
            "key": "nvd:" + cid, "kind": "cve", "cveId": cid,
            "title": cid + " — newly published or revised in NVD",
            "link": "https://nvd.nist.gov/vuln/detail/" + cid,
            "published": _parse_date(cve.get("published") or cve.get("lastModified")),
            "excerpt": _plain(desc),
        })
    return out


# -- the article reader (Scope Addition 4) --------------------
# On demand only, one article at a time, outbound-only. A
# stdlib readability pass: collect the text of block elements
# outside the page furniture; a page that yields too little —
# paywall shells, script shells, non-articles — fails with a
# NAMED reason and the page falls back to the original. The
# reader never dresses a failed extraction up as the article.

_SKIP_TAGS = {"script", "style", "nav", "aside", "footer", "form",
              "header", "noscript", "svg", "button", "select", "textarea"}
_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "blockquote", "pre"}
_PAYWALL_MARKERS = ("subscribe to read", "paywall", "create a free account to",
                    "already a subscriber", "metered paywall", "sign in to continue reading")


class _ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.stack = []
        self.blocks = []
        self.title = ""
        self._in_title = False
        self._title_buf = []
        self.script_count = 0

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS:
            self.skip_depth += 1
            if tag == "script":
                self.script_count += 1
        if tag == "title":
            self._in_title = True
        if tag in _BLOCK_TAGS and not self.skip_depth:
            self.stack.append((tag, []))

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        if tag == "title":
            self._in_title = False
            self.title = " ".join("".join(self._title_buf).split())
        if self.stack and self.stack[-1][0] == tag:
            _t, buf = self.stack.pop()
            text = " ".join("".join(buf).split())
            if text:
                self.blocks.append(text)

    def handle_data(self, data):
        if self._in_title:
            self._title_buf.append(data)
        if self.skip_depth:
            return
        if self.stack:
            self.stack[-1][1].append(data)


def extract_article(url, fetch=None):
    fetch = fetch or _fetch
    try:
        status, raw, _ns = fetch(url, {}, timeout=25)
    except Exception as e:
        return {"ok": False, "reason": "fetch-failed",
                "sentence": "The article could not be fetched (" + str(e)[:120] + ")."}
    if status != 200:
        return {"ok": False, "reason": "fetch-failed",
                "sentence": "The article answered with HTTP " + str(status) + " instead of a page."}
    try:
        text_html = raw.decode("utf-8", "replace")
    except Exception:
        return {"ok": False, "reason": "not-an-article",
                "sentence": "That link is not a readable article page."}
    if "<html" not in text_html[:2000].lower() and "<body" not in text_html.lower():
        return {"ok": False, "reason": "not-an-article",
                "sentence": "That link is not a readable article page."}
    parser = _ArticleParser()
    try:
        parser.feed(text_html)
    except Exception:
        pass
    paragraphs = [b for b in parser.blocks if len(b) >= 40]
    total = sum(len(b) for b in paragraphs)
    low = text_html.lower()
    if total < 600:
        if any(m in low for m in _PAYWALL_MARKERS):
            return {"ok": False, "reason": "paywall",
                    "sentence": "The reader hit a paywall — the page shows its gate, not its article."}
        if parser.script_count >= 8:
            return {"ok": False, "reason": "script-shell",
                    "sentence": "The page is a script shell — the article is built in the browser and never arrives as text."}
        return {"ok": False, "reason": "too-little-text",
                "sentence": "The page yielded too little readable text to call it the article."}
    return {"ok": True, "title": parser.title or "",
            "paragraphs": paragraphs[:80],
            "textChars": total}


class Wire:
    def __init__(self, root, settings_getter, fetch=None):
        self.root = root
        self._settings = settings_getter
        self._fetch = fetch or _fetch
        self._lock = threading.Lock()
        self._pulling = False
        self.dir = os.path.join(root, "config", "wire")
        self.path = os.path.join(self.dir, "wire.json")

    # -- store ------------------------------------------------
    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("items", [])
                data.setdefault("sources", {})
                return data
        except Exception:
            pass
        return {"items": [], "sources": {}}

    def _save(self, data):
        try:
            os.makedirs(self.dir, exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(tmp, self.path)
        except Exception:
            pass

    def settings(self):
        return self._settings() or {}

    # -- fetching ----------------------------------------------
    def refresh_now(self):
        # The Center's pattern: the cycle runs on its own
        # thread and the caller never waits on a feed. The
        # return value says the cycle started; state() carries
        # the outcome when it lands.
        with self._lock:
            if self._pulling:
                return {"ok": True, "pulling": True}
            self._pulling = True

        def run():
            try:
                self._refresh()
            finally:
                with self._lock:
                    self._pulling = False

        threading.Thread(target=run, daemon=True).start()
        return {"ok": True, "started": True}

    def _refresh(self):
        s = self.settings()
        retention = int(s.get("retentionDays") or 7)
        cutoff = time.time() - retention * 86400
        data = self._load()
        sources = data.setdefault("sources", {})
        merged = dict((it["key"], it) for it in data.get("items") or [])
        now = time.time()
        results = {}

        def note(source_id, error, count=None, state=None):
            row = sources.setdefault(source_id, {})
            row["lastTry"] = now
            if error:
                row["error"] = error
                results[source_id] = error
            else:
                row["lastOk"] = now
                row["error"] = ""
                if state:
                    row["etag"] = state.get("etag", "")
                    row["lastmod"] = state.get("lastmod", "")
                results[source_id] = "ok"
            if count is not None:
                row["count"] = count

        def ingest(source_id, label, items):
            stamp = time.time()
            for it in items:
                it.setdefault("kind", "news")
                it["source"] = source_id
                it["sourceLabel"] = label
                old = merged.get(it["key"])
                if old:
                    changed = (old.get("title") != it["title"]
                               or old.get("excerpt") != it["excerpt"]
                               or old.get("published") != it["published"])
                    it["firstSeen"] = old.get("firstSeen") or stamp
                    it["developing"] = bool(old.get("developing")) or changed
                    it["updatedAt"] = stamp if changed else (old.get("updatedAt") or stamp)
                else:
                    it["firstSeen"] = stamp
                    it["updatedAt"] = stamp
                    it["developing"] = False
                merged[it["key"]] = it

        for source_id, label, url in NEWS_SOURCES:
            row = sources.get(source_id) or {}
            try:
                status, raw, new_state = self._fetch(url, row)
                if status == 304:
                    note(source_id, "", state=row)
                    continue
                ingest(source_id, label, feed_items(raw))
                note(source_id, "", count=None, state=new_state)
            except Exception as e:
                note(source_id, label + " could not be fetched (" + str(e)[:140] + ").")
        # KEV additions.
        row = sources.get("kev") or {}
        try:
            status, raw, new_state = self._fetch(KEV_URL, row)
            if status == 304:
                note("kev", "", state=row)
            else:
                ingest("kev", "CISA KEV", kev_items(raw, cutoff))
                note("kev", "", state=new_state)
        except Exception as e:
            note("kev", "CISA KEV could not be fetched (" + str(e)[:140] + ").")
        # NVD recent: one window page — the wire carries
        # headlines, not the whole database (that is the
        # Center's store).
        row = sources.get("nvd") or {}
        try:
            start = (row.get("lastOk") or (now - 7 * 86400))
            fmt = "%Y-%m-%dT%H:%M:%S.000"
            q = ("?lastModStartDate=" + time.strftime(fmt, time.gmtime(start))
                 + "&lastModEndDate=" + time.strftime(fmt, time.gmtime(now))
                 + "&resultsPerPage=200&startIndex=0")
            _status, raw, _ns = self._fetch(NVD_URL + q, {}, timeout=40)
            ingest("nvd", "NVD", nvd_items(raw))
            note("nvd", "")
        except Exception as e:
            note("nvd", "NVD could not be fetched (" + str(e)[:140] + ").")
        # Retention prune + cap, newest first.
        items = [it for it in merged.values()
                 if (it.get("published") or it.get("firstSeen") or 0) >= cutoff]
        items.sort(key=lambda it: (it.get("published") or it.get("firstSeen") or 0),
                   reverse=True)
        data["items"] = items[:MAX_ITEMS]
        data["lastFetch"] = now
        ok_any = any(v == "ok" for v in results.values())
        if ok_any:
            data["lastOk"] = now
        self._save(data)
        return {"ok": True, "results": results, "items": len(data["items"])}

    def start(self):
        def loop():
            while True:
                try:
                    s = self.settings()
                    if s.get("enabled", True):
                        data = self._load()
                        last = data.get("lastFetch") or 0
                        interval = max(5, int(s.get("intervalMinutes") or 30)) * 60
                        if time.time() - last >= interval:
                            self.refresh_now()
                except Exception:
                    pass
                time.sleep(60)
        threading.Thread(target=loop, daemon=True).start()

    # -- surfaces ------------------------------------------------
    def _source_rows(self, data):
        rows = []
        ids = [sid for sid, _l, _u in NEWS_SOURCES] + ["kev", "nvd"]
        for sid in ids:
            row = (data.get("sources") or {}).get(sid) or {}
            rows.append({
                "source": sid, "label": SOURCE_LABELS.get(sid, sid),
                "lastOk": row.get("lastOk") or 0, "lastTry": row.get("lastTry") or 0,
                "error": row.get("error") or "",
                "ageHours": (round((time.time() - row["lastOk"]) / 3600.0, 1)
                             if row.get("lastOk") else None),
            })
        return rows

    def staleness_sentence(self, data=None, brief=False):
        data = data or self._load()
        last_ok = data.get("lastOk") or 0
        dead = [r for r in self._source_rows(data) if r["error"]]
        if not last_ok:
            base = "The wire has not fetched cleanly yet."
        else:
            age_min = int((time.time() - last_ok) / 60)
            when = ("under a minute ago" if age_min < 1
                    else str(age_min) + " minutes ago" if age_min < 90
                    else str(round(age_min / 60.0, 1)) + " hours ago")
            base = "The wire last fetched cleanly " + when + "."
        if dead and brief:
            # The brief names the dark feeds; the full failure
            # sentences live on the wire tab.
            base += " Not answering: " + ", ".join(r["label"] for r in dead[:4]) + "."
        elif dead:
            base += " Not answering: " + "; ".join(
                r["label"] + " — " + r["error"] for r in dead[:3])
        return base

    def state(self):
        s = self.settings()
        data = self._load()
        items = list(data.get("items") or [])
        return {
            "ok": True,
            "enabled": bool(s.get("enabled", True)),
            "intervalMinutes": int(s.get("intervalMinutes") or 30),
            "retentionDays": int(s.get("retentionDays") or 7),
            "pulling": self._pulling,
            "lastOk": data.get("lastOk") or 0,
            "staleness": self.staleness_sentence(data),
            "sources": self._source_rows(data),
            "items": items,
        }

    def item_for_link(self, link):
        for it in self._load().get("items") or []:
            if it.get("link") == link:
                return it
        return None

    def read_article(self, link):
        # The reader opens wire items only: the URL must be one
        # the wire itself is carrying. Anything else is refused
        # by name — the reader is not a general proxy.
        item = self.item_for_link(link)
        if not item:
            return {"ok": False, "reason": "not-a-wire-item",
                    "sentence": "That link is not a story the wire is carrying, so the reader will not fetch it."}
        got = extract_article(link, fetch=self._fetch)
        got["item"] = {"title": item.get("title"), "source": item.get("sourceLabel"),
                       "published": item.get("published") or 0, "link": link}
        if got.get("ok") and not got.get("title"):
            got["title"] = item.get("title") or ""
        return got

    def brief_block(self, limit=2800):
        s = self.settings()
        if not s.get("enabled", True):
            return ""
        data = self._load()
        items = data.get("items") or []
        if not items and not data.get("lastOk"):
            return ""
        news = [it for it in items if it.get("kind") == "news"][:5]
        cves = [it for it in items if it.get("kind") in ("cve", "kev")][:4]
        dev = [it for it in items if it.get("developing")][:3]
        lines = ["[The wire — the security news Navi is carrying]",
                 self.staleness_sentence(data, brief=True)]
        if news:
            lines.append("TOP NEWS")
            for it in news:
                lines.append("- " + it["title"] + " — " + it["sourceLabel"]
                             + ", " + _iso(it.get("published") or it.get("firstSeen"))[:10]
                             + ". " + (it.get("excerpt") or "")[:170])
        if cves:
            lines.append("NEW CVEs & KNOWN-EXPLOITED (wire CVE sources)")
            for it in cves:
                lines.append("- " + it["title"] + " — " + it["sourceLabel"]
                             + ", " + _iso(it.get("published") or it.get("firstSeen"))[:10]
                             + ". " + (it.get("excerpt") or "")[:170])
        if dev:
            lines.append("DEVELOPING (changed since first seen — still moving)")
            for it in dev:
                lines.append("- " + it["title"] + " — " + it["sourceLabel"])
        lines.append(
            "When the operator asks \"what's the sitch\" (or what's happening, what's new), "
            "answer with this briefing: the facts first, each with its source and date, then — "
            "clearly separated under the heading \"My take\" — your own assessment: what "
            "matters, what is noise, what you would watch. The take is your opinion and must "
            "read as opinion, never as reporting. You may open a story up from the wire tab "
            "and discuss it; carry uncertainty honestly — confirmed, unknown, and speculated "
            "are three different things. If the wire is stale or a feed is down, say so in "
            "the same breath as the briefing.")
        return "\n".join(lines)[:limit]
