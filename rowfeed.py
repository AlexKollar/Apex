#!/usr/bin/env python3
# rowfeed.py — the Row's public record, fetched and parsed
# (v0.4.9e, #248, Context Awareness leg 2).
#
# Apex and nocturnerow.com are one ecosystem, and this module
# is the bridge's read path into the Row's half of it: the
# Dispatches, the Roadmap's chapters, her own page and the
# Apex page, the release signals, and the gate's seven steps.
# The site publishes no feed, JSON, or sitemap for these (the
# checks were made: /feed.xml and /sitemap.xml answer 404),
# so the record is parsed from the public HTML itself — the
# one structured exception is the release wire, which is the
# same GitHub releases JSON the Apex page's own Signals
# section reads as you open it. The site's wire is the wire.
#
# Everything here is pure: fetchers are injected, parsers take
# text and return data, and no function keeps state. The
# bridge owns the cache (config/row-feed.json), the refresh
# throttle, and the honesty rules — a section that fails to
# fetch keeps its last good data in the cache and its error
# is NAMED in the record, never silently emptied.
import html as _html
import json
import re
import time
import urllib.request

SITE = "https://nocturnerow.com"
BLOG_URL = SITE + "/blog.html"
ROADMAP_URL = SITE + "/roadmap.html"
APEX_URL = SITE + "/apex.html"
NAVI_URL = SITE + "/navi.html"
GATE_URL = SITE + "/rockport-mesh.html"
RELEASES_URL = ("https://api.github.com/repos/AlexKollar/Apex"
                "/releases?per_page=5")

BODY_CAP = 6000


def _fetch(url, timeout=25):
    # The wire.py/_fetch idiom: one plain GET, an honest
    # user agent, no retries hidden from the caller — a
    # failure raises and the bridge names it.
    req = urllib.request.Request(url, headers={
        "User-Agent": "Apex-RowFeed/1.0 (local-first; operator machine)",
        "Accept": "text/html, application/json",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace")


def _text(fragment):
    # HTML fragment -> plain text: scripts and styles out,
    # tags out, entities unescaped, whitespace collapsed.
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", fragment or "")
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = _html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


# -- Dispatches ---------------------------------------------------------

_CARD_RE = re.compile(r'(?s)<article class="post">(.*?)</article>')
_TITLE_RE = re.compile(r'(?s)<h3 class="ptitle"><a href="([^"]+)">(.*?)</a></h3>')
_META_RE = re.compile(r'(?s)<div class="meta">(.*?)</div>')
_EXCERPT_RE = re.compile(r'(?s)<p class="excerpt">(.*?)</p>')
_DTG_RE = re.compile(r'TRANSMISSION //\s*([0-9A-Z ]+)')


def parse_dispatch_index(page_html):
    """The Dispatches index -> [{title, date, dtg, url,
    excerpt}], newest first, exactly as the page files them."""
    out = []
    for card in _CARD_RE.findall(page_html or ""):
        t = _TITLE_RE.search(card)
        if not t:
            continue
        meta = _META_RE.search(card)
        exc = _EXCERPT_RE.search(card)
        dtg = _DTG_RE.search(card)
        out.append({
            "title": _text(t.group(2)),
            "url": SITE + t.group(1) if t.group(1).startswith("/") else t.group(1),
            "date": (_text(meta.group(1)).split("·")[0].strip()
                     if meta else ""),
            "dtg": dtg.group(1).strip() if dtg else "",
            "excerpt": _text(exc.group(1)) if exc else "",
        })
    return out


def parse_dispatch_body(page_html):
    """One Dispatch's page -> its body as plain text (the
    article if the layout gives one, else the main column),
    bounded by BODY_CAP at the caller's request."""
    m = re.search(r"(?s)<article[^>]*>(.*?)</article>", page_html or "")
    if not m:
        m = re.search(r"(?s)<main[^>]*>(.*?)</main>", page_html or "")
    return _text(m.group(1) if m else (page_html or ""))


# -- The Roadmap ----------------------------------------------------------

_CH_RE = re.compile(
    r'(?s)<span class="tl-date[^"]*">(.*?)</span>\s*'
    r'<span class="tl-title[^"]*">(.*?)</span>\s*'
    r'<span class="tl-tag[^"]*">(.*?)</span>')


def parse_roadmap(page_html):
    """The Roadmap -> [{title, date, tag}] in the page's own
    order — the story of record, chapter by chapter."""
    out = []
    for date, title, tag in _CH_RE.findall(page_html or ""):
        tag = _text(tag)
        if tag.startswith("SHIPPED"):
            tag = "SHIPPED"
        elif tag.startswith("LIVE"):
            tag = "LIVE"
        elif "HORIZON" in tag:
            tag = "HORIZON"
        out.append({"title": _text(title), "date": _text(date),
                    "tag": tag})
    return out


# -- The pages ------------------------------------------------------------

_PILL_RE = re.compile(
    r'Apex <b>v([^<]+) Stable</b>\s*·\s*Edge <b>v([^<]+)</b>')
_DESC_RE = re.compile(r'(?s)<meta name="description" content="([^"]*)"')
_TITLE_TAG_RE = re.compile(r"(?s)<title>(.*?)</title>")


def parse_apex_page(page_html):
    """The Apex page -> {stable, edge} from its version pill,
    the facts the page itself leads with."""
    m = _PILL_RE.search(page_html or "")
    return {"stable": m.group(1) if m else "",
            "edge": m.group(2) if m else ""}


def parse_navi_page(page_html):
    """Her own page -> {title, description}: who the site
    says she is, in the site's own words."""
    t = _TITLE_TAG_RE.search(page_html or "")
    d = _DESC_RE.search(page_html or "")
    return {"title": _text(t.group(1)) if t else "",
            "description": _html.unescape(d.group(1)).strip() if d else ""}


# -- The gate -------------------------------------------------------------

def parse_gate_steps(page_html):
    """The gate page -> the seven join steps, as plain text,
    from the 'How to connect' ordered list — the walkthrough
    script, sourced from the page itself, never retyped."""
    m = re.search(r'(?s)<div class="join-body">\s*<ol>(.*?)</ol>', page_html or "")
    if not m:
        return []
    return [_text(li) for li in re.findall(r"(?s)<li>(.*?)</li>", m.group(1))]


# -- Release signals --------------------------------------------------------

def parse_releases(json_text):
    """The releases wire (the same JSON the Apex page's
    Signals section renders) -> [{tag, name, kind, date,
    excerpt, url}], newest first as the wire files them."""
    try:
        rows = json.loads(json_text or "[]")
    except Exception:
        return []
    out = []
    for r in rows if isinstance(rows, list) else []:
        if not isinstance(r, dict):
            continue
        body = re.sub(r"\s+", " ", re.sub(r"[#>*`_]", "", r.get("body") or "")).strip()
        out.append({
            "tag": r.get("tag_name") or "",
            "name": r.get("name") or r.get("tag_name") or "",
            "kind": "Edge" if r.get("prerelease") else "Stable",
            "date": (r.get("published_at") or "")[:10],
            "excerpt": body[:300],
            "url": r.get("html_url") or "",
        })
    return out


# -- The whole record -------------------------------------------------------

def fetch_record(fetcher=None):
    """One refresh of the whole record. Every source is
    fetched independently: a source that answers lands in
    sections with its own fetch time; a source that fails is
    NAMED in errors and contributes nothing — the bridge's
    merge keeps the cached section standing (see bridge.py).
    The latest Dispatch's body rides along (bounded) so a
    news answer never needs a second fetch."""
    fetch = fetcher or _fetch
    now = time.time()
    sections, errors = {}, {}

    def take(name, url, parse, key):
        try:
            data = parse(fetch(url))
            sections[name] = {"at": now, key: data}
        except Exception as e:
            errors[name] = "fetch-failed: %s: %s" % (type(e).__name__, e)

    take("dispatches", BLOG_URL, parse_dispatch_index, "items")
    take("roadmap", ROADMAP_URL, parse_roadmap, "chapters")
    take("releases", RELEASES_URL, parse_releases, "items")
    take("gate", GATE_URL, parse_gate_steps, "steps")
    pages = {}
    try:
        pages["apex"] = parse_apex_page(fetch(APEX_URL))
        pages["navi"] = parse_navi_page(fetch(NAVI_URL))
        sections["pages"] = {"at": now, "pages": pages}
    except Exception as e:
        errors["pages"] = "fetch-failed: %s: %s" % (type(e).__name__, e)
    disp = sections.get("dispatches", {}).get("items") or []
    if disp:
        try:
            body = parse_dispatch_body(fetch(disp[0]["url"]))
            sections["dispatches"]["latest_body"] = body[:BODY_CAP]
        except Exception as e:
            errors["dispatch-body"] = "fetch-failed: %s: %s" % (
                type(e).__name__, e)
    return {"fetched_at": now, "sections": sections, "errors": errors}
