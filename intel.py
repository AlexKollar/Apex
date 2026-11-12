# intel.py — the Threat Intelligence Center engine (Build 15, #165).
#
# A local intel store, per-source pullers, a matcher, and the
# digest Navi reasons over. Stdlib only; it never imports the
# bridge — the bridge imports it and hands it settings and
# callbacks (the Guardian's shape). Everything the design pass
# ruled is here in miniature:
#
#   * Keyless public sources only (NVD keyless tier, CISA KEV,
#     CISA advisories, EPSS, curated RSS). Nothing needs an
#     account; nothing is scraped from HTML.
#   * One collector per Mesh: a node either collects for itself
#     or receives a paired collector's digest over the Mesh door
#     (navi-intel-digest/1) and imports it. Matching is local,
#     always — the inventory never leaves the machine.
#   * Staleness is labeled everywhere: per-source last-success
#     stamps ride the surface payload, the digest header, and
#     Navi's brief. Offline, the center serves last-good data
#     with its age on it, never a silent old picture.
#
# The store is SQLite beside the rest of Apex's state
# (config/intel.db). Identity of a record is the CVE ID; each
# source owns its fields — KEV the exploited status and due
# dates, NVD the CVSS / CPE / description, EPSS the likelihood.

import gzip
import json
import os
import re
import sqlite3
import threading
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

SCHEMA = "navi-intel-digest/1"
KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
NVD_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
EPSS_URL = "https://api.first.org/data/v1/epss"
RSS_SOURCES = [
    ("cisa", "CISA advisories", "https://www.cisa.gov/cybersecurity-advisories/all.xml"),
    ("krebs", "Krebs on Security", "https://krebsonsecurity.com/feed/"),
    ("bleepingcomputer", "BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
]
SOURCE_LABELS = {
    "kev": "CISA KEV", "nvd": "NVD", "epss": "EPSS",
    "cisa": "CISA advisories", "krebs": "Krebs", "bleepingcomputer": "BleepingComputer",
    "mesh": "Mesh digest",
}
CVE_ID_RE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)
STOPWORDS = set("the and for with from this that case scope client review assessment external internal network server service services system systems test testing report reports".split())
FRESH_HOURS = 12.0
AGING_HOURS = 48.0


def _iso(ts):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts))


def _hours_since(ts, now=None):
    if not ts:
        return None
    return round(((now or time.time()) - ts) / 3600.0, 1)


def _band(age_hours):
    if age_hours is None:
        return "never"
    if age_hours < FRESH_HOURS:
        return "fresh"
    if age_hours < AGING_HOURS:
        return "aging"
    return "stale"


def _fetch(url, state, timeout=25):
    # One conditional GET. Returns (status, bytes, new_state):
    # status 200 with the body, 304 when the stored validators
    # still hold, or raises. Conditional-request headers carry
    # no operator data — they are the feed's own stamps.
    req = urllib.request.Request(url, headers={
        "User-Agent": "Apex-Intel/1.0 (local-first threat intel; operator machine)",
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
            new_state = {
                "etag": resp.headers.get("ETag") or state.get("etag") or "",
                "lastmod": resp.headers.get("Last-Modified") or state.get("lastmod") or "",
            }
            return 200, raw, new_state
    except urllib.error.HTTPError as e:
        if e.code == 304:
            return 304, b"", state
        raise


class Intel:
    def __init__(self, root, settings_getter, callbacks):
        self.root = root
        self._settings = settings_getter
        self._cb = callbacks or {}
        self.db_path = os.path.join(root, "config", "intel.db")
        self.digest_path = os.path.join(root, "config", "intel-digest.json")
        self._lock = threading.Lock()
        self._pulling = False
        self._started = False
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    # -- store ------------------------------------------------
    def _db(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._db() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS cve (
                id TEXT PRIMARY KEY, title TEXT, description TEXT,
                cvss REAL, cvss_severity TEXT, epss REAL, epss_percentile REAL,
                kev INTEGER DEFAULT 0, kev_added TEXT, kev_due TEXT, kev_ransomware TEXT,
                published TEXT, modified TEXT, refs TEXT, products TEXT,
                matched TEXT, first_seen REAL, last_seen REAL
            );
            CREATE TABLE IF NOT EXISTS epss_history (
                cve_id TEXT, date TEXT, epss REAL, percentile REAL,
                PRIMARY KEY (cve_id, date)
            );
            CREATE TABLE IF NOT EXISTS advisory (
                id TEXT PRIMARY KEY, source TEXT, title TEXT, link TEXT,
                summary TEXT, published TEXT, fetched_at REAL
            );
            CREATE TABLE IF NOT EXISTS source_state (
                source TEXT PRIMARY KEY, last_attempt REAL, last_success REAL,
                last_error TEXT, etag TEXT, lastmod TEXT, count INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT);
            """)

    def _kv_get(self, key, default=None):
        with self._db() as conn:
            row = conn.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        if row is None:
            return default
        try:
            return json.loads(row["value"])
        except Exception:
            return default

    def _kv_set(self, key, value):
        with self._db() as conn:
            conn.execute("INSERT INTO kv(key, value) VALUES(?, ?) "
                         "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                         (key, json.dumps(value)))

    def _state_row(self, conn, source):
        row = conn.execute("SELECT * FROM source_state WHERE source=?", (source,)).fetchone()
        if row is None:
            return {"etag": "", "lastmod": "", "last_attempt": 0, "last_success": 0,
                    "last_error": "", "count": 0}
        return dict(row)

    def _state_save(self, source, **fields):
        with self._db() as conn:
            cur = self._state_row(conn, source)
            cur.update(fields)
            conn.execute(
                "INSERT INTO source_state(source, last_attempt, last_success, last_error, etag, lastmod, count) "
                "VALUES(?,?,?,?,?,?,?) ON CONFLICT(source) DO UPDATE SET last_attempt=excluded.last_attempt, "
                "last_success=excluded.last_success, last_error=excluded.last_error, etag=excluded.etag, "
                "lastmod=excluded.lastmod, count=excluded.count",
                (source, cur.get("last_attempt") or 0, cur.get("last_success") or 0,
                 cur.get("last_error") or "", cur.get("etag") or "", cur.get("lastmod") or "",
                 cur.get("count") or 0))

    # -- record merge ------------------------------------------
    def _upsert_cve(self, conn, rec, nvd_owned=False, kev_owned=False):
        # Identity is the CVE ID; each source owns its fields.
        # NVD-owned: title/description/cvss/products/refs/dates.
        # KEV-owned: kev flag + added/due/ransomware. EPSS writes
        # its two columns directly in its puller.
        now = time.time()
        row = conn.execute("SELECT * FROM cve WHERE id=?", (rec["id"],)).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO cve(id, title, description, cvss, cvss_severity, kev, kev_added, "
                "kev_due, kev_ransomware, published, modified, refs, products, first_seen, last_seen) "
                "VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec["id"], rec.get("title") or "", rec.get("description") or "",
                 rec.get("cvss"), rec.get("cvss_severity") or "",
                 1 if rec.get("kev") else 0, rec.get("kev_added") or "",
                 rec.get("kev_due") or "", rec.get("kev_ransomware") or "",
                 rec.get("published") or "", rec.get("modified") or "",
                 json.dumps(rec.get("refs") or []), json.dumps(rec.get("products") or []),
                 now, now))
            return
        sets, args = ["last_seen=?"], [now]
        if nvd_owned:
            for col in ("title", "description", "cvss_severity", "published", "modified"):
                sets.append(col + "=?")
                args.append(rec.get(col) or "")
            sets.append("cvss=?")
            args.append(rec.get("cvss"))
            sets.append("refs=?")
            args.append(json.dumps(rec.get("refs") or []))
            sets.append("products=?")
            args.append(json.dumps(rec.get("products") or []))
        if kev_owned:
            sets += ["kev=?", "kev_added=?", "kev_due=?", "kev_ransomware=?"]
            args += [1 if rec.get("kev") else 0, rec.get("kev_added") or "",
                     rec.get("kev_due") or "", rec.get("kev_ransomware") or ""]
            if rec.get("title") and not row["title"]:
                sets.append("title=?")
                args.append(rec["title"])
        args.append(rec["id"])
        conn.execute("UPDATE cve SET " + ", ".join(sets) + " WHERE id=?", args)

    # -- pullers ------------------------------------------------
    def _pull_kev(self):
        with self._db() as conn:
            state = self._state_row(conn, "kev")
        self._state_save("kev", last_attempt=time.time())
        status, raw, new_state = _fetch(KEV_URL, state)
        if status == 304:
            self._state_save("kev", last_success=time.time(), last_error="")
            return "not modified"
        feed = json.loads(raw.decode("utf-8", "replace"))
        vulns = feed.get("vulnerabilities") or []
        with self._db() as conn:
            for v in vulns:
                cid = str(v.get("cveID") or "").upper()
                if not CVE_ID_RE.fullmatch(cid):
                    continue
                vendor = str(v.get("vendorProject") or "").strip()
                product = str(v.get("product") or "").strip()
                products = []
                if product:
                    products.append((vendor + ":" + product) if vendor else product)
                    products.append(product)
                self._upsert_cve(conn, {
                    "id": cid, "kev": True,
                    "kev_added": v.get("dateAdded") or "",
                    "kev_due": v.get("dueDate") or "",
                    "kev_ransomware": v.get("knownRansomwareCampaignUse") or "",
                    "title": v.get("vulnerabilityName") or "",
                    "products": [p for p in products if p],
                }, kev_owned=True)
            count = conn.execute("SELECT COUNT(*) AS n FROM cve WHERE kev=1").fetchone()["n"]
        self._state_save("kev", last_success=time.time(), last_error="",
                         etag=new_state.get("etag", ""), lastmod=new_state.get("lastmod", ""),
                         count=count)
        return str(len(vulns)) + " KEV entries"

    def _pull_nvd(self):
        with self._db() as conn:
            state = self._state_row(conn, "nvd")
        last_ok = state.get("last_success") or 0
        end = time.time()
        start = last_ok if last_ok else end - 7 * 86400
        # NVD's lastMod window is capped at 120 days; ours is far
        # inside it. Keyless tier: 5 requests / 30 s, so pages
        # are spaced — this runs on a background thread only.
        fmt = "%Y-%m-%dT%H:%M:%S.000"
        q = ("?lastModStartDate=" + time.strftime(fmt, time.gmtime(start))
             + "&lastModEndDate=" + time.strftime(fmt, time.gmtime(end))
             + "&resultsPerPage=2000&startIndex=")
        self._state_save("nvd", last_attempt=time.time())
        total, index, pages = None, 0, 0
        seen = 0
        with self._db() as conn:
            while pages < 5:
                if pages:
                    time.sleep(6.5)
                _status, raw, _ns = _fetch(NVD_URL + q + str(index), {}, timeout=40)
                data = json.loads(raw.decode("utf-8", "replace"))
                if total is None:
                    total = data.get("totalResults") or 0
                for item in data.get("vulnerabilities") or []:
                    rec = _nvd_record(item)
                    if rec:
                        self._upsert_cve(conn, rec, nvd_owned=True)
                        seen += 1
                pages += 1
                index += 2000
                if index >= (total or 0):
                    break
            count = conn.execute("SELECT COUNT(*) AS n FROM cve").fetchone()["n"]
        self._state_save("nvd", last_success=time.time(), last_error="", count=count)
        return str(seen) + " CVEs in window (" + str(total or 0) + " total)"

    def _pull_epss(self):
        with self._db() as conn:
            rows = conn.execute(
                "SELECT id FROM cve ORDER BY kev DESC, (epss IS NOT NULL) ASC, published DESC LIMIT 500").fetchall()
        ids = [r["id"] for r in rows]
        self._state_save("epss", last_attempt=time.time())
        done = 0
        today = time.strftime("%Y-%m-%d", time.gmtime())
        for i in range(0, len(ids), 100):
            batch = ids[i:i + 100]
            if not batch:
                break
            _s, raw, _n = _fetch(EPSS_URL + "?cve=" + ",".join(batch) + "&limit=100", {}, timeout=30)
            data = json.loads(raw.decode("utf-8", "replace"))
            with self._db() as conn:
                for d in data.get("data") or []:
                    cid = str(d.get("cve") or "").upper()
                    try:
                        score = float(d.get("epss"))
                        pct = float(d.get("percentile"))
                    except Exception:
                        continue
                    conn.execute("UPDATE cve SET epss=?, epss_percentile=? WHERE id=?",
                                 (score, pct, cid))
                    conn.execute("INSERT OR REPLACE INTO epss_history(cve_id, date, epss, percentile) "
                                 "VALUES(?,?,?,?)", (cid, str(d.get("date") or today), score, pct))
                    done += 1
        self._state_save("epss", last_success=time.time(), last_error="", count=done)
        return str(done) + " EPSS scores"

    def _pull_rss(self, source, _label, url):
        with self._db() as conn:
            state = self._state_row(conn, source)
        self._state_save(source, last_attempt=time.time())
        status, raw, new_state = _fetch(url, state)
        if status == 304:
            self._state_save(source, last_success=time.time(), last_error="")
            return "not modified"
        items = _rss_items(raw)
        now = time.time()
        with self._db() as conn:
            for it in items:
                conn.execute(
                    "INSERT INTO advisory(id, source, title, link, summary, published, fetched_at) "
                    "VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, "
                    "summary=excluded.summary, published=excluded.published, fetched_at=excluded.fetched_at",
                    (it["id"], source, it["title"], it["link"], it["summary"], it["published"], now))
            conn.execute("DELETE FROM advisory WHERE source=? AND id NOT IN "
                         "(SELECT id FROM advisory WHERE source=? ORDER BY fetched_at DESC LIMIT 60)",
                         (source, source))
            count = conn.execute("SELECT COUNT(*) AS n FROM advisory WHERE source=?",
                                 (source,)).fetchone()["n"]
        self._state_save(source, last_success=time.time(), last_error="",
                         etag=new_state.get("etag", ""), lastmod=new_state.get("lastmod", ""),
                         count=count)
        return str(len(items)) + " items"

    # -- collection driver ---------------------------------------
    def settings(self):
        s = self._settings() or {}
        return s

    def mode(self):
        s = self.settings()
        if s.get("collectorPeer"):
            return "receiver"
        return "collector"

    def collect_due(self, force=False):
        # One collection cycle. Receiver mode fetches the
        # collector's digest over the Mesh door instead of
        # polling the internet; the fallback to local collection
        # is a setting, never a surprise.
        if not self._lock.acquire(False):
            return {"ok": False, "error": "A pull is already running."}
        self._pulling = True
        results = {}
        try:
            s = self.settings()
            if not s.get("enabled", True):
                return {"ok": True, "skipped": "disabled"}
            if self.mode() == "receiver":
                digest = None
                fetch = self._cb.get("fetch_digest")
                if fetch:
                    try:
                        digest = fetch(s["collectorPeer"])
                    except Exception:
                        digest = None
                if digest:
                    self.import_digest(digest)
                    results["mesh"] = "digest imported"
                elif s.get("fallbackLocal"):
                    results["mesh"] = "collector unreachable — local fallback (enabled)"
                    self._collect_local(s, force, results)
                else:
                    self._state_save("mesh", last_attempt=time.time(),
                                     last_error="Collector unreachable; local fallback is off.")
                    results["mesh"] = "collector unreachable"
                return {"ok": True, "results": results}
            self._collect_local(s, force, results)
            return {"ok": True, "results": results}
        finally:
            self._pulling = False
            self._lock.release()

    def _collect_local(self, s, force, results):
        sources = s.get("sources") or {}
        cadence = float(s.get("cadenceHours") or 6) * 3600
        plan = []
        if sources.get("kev", True):
            plan.append(("kev", self._pull_kev, cadence))
        if sources.get("nvd", True):
            plan.append(("nvd", self._pull_nvd, cadence))
        if sources.get("cisa", True):
            plan.append(("cisa", lambda: self._pull_rss(*RSS_SOURCES[0]), cadence))
        if sources.get("rss", True):
            for entry in RSS_SOURCES[1:]:
                plan.append((entry[0], (lambda e=entry: self._pull_rss(*e)), cadence))
        if sources.get("epss", True):
            plan.append(("epss", self._pull_epss, 86400.0))
        for source, fn, due_after in plan:
            with self._db() as conn:
                st = self._state_row(conn, source)
            if not force and st.get("last_success") and time.time() - st["last_success"] < due_after:
                results[source] = "not due"
                continue
            try:
                results[source] = fn()
            except Exception as e:
                # One source failing never blocks the others —
                # and the failure is recorded, not hidden.
                self._state_save(source, last_attempt=time.time(),
                                 last_error=str(e)[:200])
                results[source] = "failed: " + str(e)[:120]
        self.compute_matches()
        self.build_digest()

    def refresh_now(self):
        t = threading.Thread(target=lambda: self.collect_due(force=True), daemon=True)
        t.start()
        return {"ok": True, "started": True}

    def start(self):
        if self._started:
            return
        self._started = True
        threading.Thread(target=self._loop, daemon=True).start()

    def _loop(self):
        # First cycle shortly after boot (the picture may be
        # stale from before the restart), then a light tick.
        time.sleep(20)
        while True:
            try:
                self.collect_due()
            except Exception:
                pass
            time.sleep(600)

    # -- matching -------------------------------------------------
    def match_terms(self):
        # The profile is small and specific, never PCAP-and-pray:
        # the watchlist (operator-declared), the roster (this
        # node's platform + paired peers' names), and words drawn
        # from the operator's open cases. The inventory itself
        # never leaves this machine.
        s = self.settings()
        terms = []
        for raw in s.get("watchlist") or []:
            t = str(raw or "").strip().lower()
            if t:
                terms.append({"term": t, "via": "declared"})
        try:
            import platform as _pf
            fam = (_pf.system() or "").strip().lower()
            if fam:
                terms.append({"term": fam, "via": "roster"})
        except Exception:
            pass
        peers = []
        try:
            peers = (self._cb.get("peers") or (lambda: []))() or []
        except Exception:
            peers = []
        for p in peers:
            nm = str((p or {}).get("name") or "").strip().lower()
            if nm:
                terms.append({"term": nm, "via": "roster"})
        try:
            case_terms = (self._cb.get("case_terms") or (lambda: []))() or []
        except Exception:
            case_terms = []
        for ct in case_terms:
            t = str((ct or {}).get("term") or "").strip().lower()
            if t and len(t) >= 3 and t not in STOPWORDS:
                terms.append({"term": t, "via": "case"})
        seen, out = set(), []
        for t in terms:
            key = (t["term"], t["via"])
            if key not in seen:
                seen.add(key)
                out.append(t)
        return out

    def compute_matches(self):
        terms = self.match_terms()
        if not terms:
            with self._db() as conn:
                conn.execute("UPDATE cve SET matched=NULL")
            return 0
        pats = [(t, re.compile(r"(?<![a-z0-9])" + re.escape(t["term"]) + r"(?![a-z0-9])"))
                for t in terms]
        hits = 0
        with self._db() as conn:
            rows = conn.execute("SELECT id, title, description, products, matched FROM cve").fetchall()
            for row in rows:
                try:
                    products = [str(p).lower() for p in json.loads(row["products"] or "[]")]
                except Exception:
                    products = []
                hay = ((row["title"] or "") + " " + (row["description"] or "")).lower()
                best = None
                for t, pat in pats:
                    grade = None
                    for prod in products:
                        if t["term"] == prod or t["term"] == prod.split(":")[-1]:
                            grade = "exact"
                            break
                    if not grade and pat.search(hay):
                        grade = "keyword"
                    if grade == "exact":
                        best = {"grade": "exact", "term": t["term"], "via": t["via"]}
                        break
                    if grade and not best:
                        best = {"grade": grade, "term": t["term"], "via": t["via"]}
                new_val = json.dumps(best) if best else None
                if new_val != row["matched"]:
                    conn.execute("UPDATE cve SET matched=? WHERE id=?", (new_val, row["id"]))
                if best:
                    hits += 1
        return hits

    # -- records out ----------------------------------------------
    @staticmethod
    def _lite(row):
        try:
            matched = json.loads(row["matched"]) if row["matched"] else None
        except Exception:
            matched = None
        try:
            products = json.loads(row["products"] or "[]")
        except Exception:
            products = []
        return {
            "id": row["id"], "title": row["title"] or "",
            "cvss": row["cvss"], "cvssSeverity": row["cvss_severity"] or "",
            "epss": row["epss"], "epssPercentile": row["epss_percentile"],
            "kev": bool(row["kev"]), "kevAdded": row["kev_added"] or "",
            "kevDue": row["kev_due"] or "", "kevRansomware": row["kev_ransomware"] or "",
            "published": row["published"] or "", "products": products,
            "matched": matched,
        }

    @staticmethod
    def _rank(row):
        m = 0.0
        if row["kev"]:
            m += 1000
        try:
            matched = json.loads(row["matched"]) if row["matched"] else None
        except Exception:
            matched = None
        if matched:
            m += 500 if matched.get("grade") == "exact" else 200
        m += (row["cvss"] or 0) * 10
        m += (row["epss"] or 0) * 100
        return -m

    def _sections(self, conn):
        rows = conn.execute("SELECT * FROM cve").fetchall()
        kev_rows = [r for r in rows if r["kev"]]
        matched = [r for r in rows if r["matched"]]
        prev_kev = set(self._kv_get("kev_ids_prev", []) or [])
        cur_kev = set(r["id"] for r in kev_rows)
        if prev_kev:
            kev_new = [r for r in kev_rows if r["id"] in (cur_kev - prev_kev)]
        else:
            cutoff = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400))
            kev_new = [r for r in kev_rows if (r["kev_added"] or "") >= cutoff]
        stack_matches = sorted(matched, key=self._rank)[:50]
        watchlist_hits = [r for r in stack_matches
                          if (json.loads(r["matched"] or "{}") or {}).get("via") == "declared"]
        top_new = sorted(rows, key=lambda r: (r["published"] or ""), reverse=True)
        top_new = sorted(top_new[:200], key=self._rank)[:50]
        movers = []
        week_ago = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 7 * 86400))
        for r in rows:
            if r["epss"] is None:
                continue
            old = conn.execute(
                "SELECT epss FROM epss_history WHERE cve_id=? AND date<=? ORDER BY date DESC LIMIT 1",
                (r["id"], week_ago)).fetchone()
            base = old["epss"] if old and old["epss"] is not None else None
            if base is None:
                first = conn.execute(
                    "SELECT epss FROM epss_history WHERE cve_id=? ORDER BY date ASC LIMIT 1",
                    (r["id"],)).fetchone()
                base = first["epss"] if first else None
            if base is not None and r["epss"] - base >= 0.10:
                movers.append((r, round(r["epss"] - base, 3)))
        movers.sort(key=lambda t: -t[1])
        return {
            "kev_total": len(kev_rows), "kev_new": kev_new,
            "stack_matches": stack_matches, "watchlist_hits": watchlist_hits,
            "top_new": top_new, "epss_movers": movers[:20],
            "cur_kev": cur_kev,
        }

    def build_digest(self):
        ident = {"nodeId": "", "name": ""}
        try:
            ident = (self._cb.get("identity") or (lambda: ident))() or ident
        except Exception:
            pass
        with self._db() as conn:
            sec = self._sections(conn)
            states = {}
            for source in SOURCE_LABELS:
                st = self._state_row(conn, source)
                age = _hours_since(st.get("last_success"))
                states[source] = {"source": source, "label": SOURCE_LABELS[source],
                                  "lastSuccess": st.get("last_success") or 0,
                                  "count": st.get("count") or 0,
                                  "ageHours": age, "band": _band(age),
                                  "error": st.get("last_error") or ""}
            advisories = [dict(r) for r in conn.execute(
                "SELECT source, title, link, published FROM advisory "
                "ORDER BY fetched_at DESC LIMIT 15").fetchall()]
            prev_kev = self._kv_get("kev_ids_prev", None)
        union = {}
        for group in (sec["kev_new"], sec["stack_matches"], sec["top_new"]):
            for r in group:
                union[r["id"]] = r
        for r, _d in sec["epss_movers"]:
            union[r["id"]] = r
        items = []
        for r in list(union.values())[:300]:
            lite = self._lite(r)
            lite["description"] = (r["description"] or "")[:1200]
            try:
                lite["refs"] = json.loads(r["refs"] or "[]")[:6]
            except Exception:
                lite["refs"] = []
            items.append(lite)
        digest = {
            "schema": SCHEMA,
            "generated_at": _iso(time.time()),
            "collector": {"nodeId": ident.get("nodeId") or "", "name": ident.get("name") or ""},
            "sources": [states[k] for k in SOURCE_LABELS],
            "sections": {
                "kev_new": [self._lite(r) for r in sec["kev_new"][:50]],
                "stack_matches": [self._lite(r) for r in sec["stack_matches"]],
                "watchlist_hits": [self._lite(r) for r in sec["watchlist_hits"]],
                "top_new": [self._lite(r) for r in sec["top_new"]],
                "epss_movers": [{"id": r["id"], "delta": d} for r, d in sec["epss_movers"]],
            },
            "kev_total": sec["kev_total"],
            "items": items,
            "advisories": advisories,
            "brief_text": self.brief_text(),
        }
        try:
            with open(self.digest_path, "w") as f:
                json.dump(digest, f)
        except Exception:
            pass
        if prev_kev is not None:
            self._kv_set("kev_ids_prev", sorted(sec["cur_kev"]))
        else:
            self._kv_set("kev_ids_prev", sorted(sec["cur_kev"]))
        self._kv_set("collector", digest["collector"])
        return digest

    def import_digest(self, digest):
        if not isinstance(digest, dict) or digest.get("schema") != SCHEMA:
            return {"ok": False, "error": "Not a navi-intel-digest/1 object."}
        now = time.time()
        with self._db() as conn:
            for item in digest.get("items") or []:
                cid = str(item.get("id") or "").upper()
                if not CVE_ID_RE.fullmatch(cid):
                    continue
                rec = {"id": cid, "title": item.get("title") or "",
                       "description": item.get("description") or "",
                       "cvss": item.get("cvss"), "cvss_severity": item.get("cvssSeverity") or "",
                       "kev": bool(item.get("kev")), "kev_added": item.get("kevAdded") or "",
                       "kev_due": item.get("kevDue") or "",
                       "kev_ransomware": item.get("kevRansomware") or "",
                       "published": item.get("published") or "", "modified": "",
                       "refs": item.get("refs") or [], "products": item.get("products") or []}
                self._upsert_cve(conn, rec, nvd_owned=True, kev_owned=True)
                if item.get("epss") is not None:
                    conn.execute("UPDATE cve SET epss=?, epss_percentile=? WHERE id=?",
                                 (item.get("epss"), item.get("epssPercentile"), cid))
            for adv in digest.get("advisories") or []:
                aid = "mesh:" + str(adv.get("link") or adv.get("title") or "")
                conn.execute(
                    "INSERT INTO advisory(id, source, title, link, summary, published, fetched_at) "
                    "VALUES(?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET title=excluded.title, "
                    "fetched_at=excluded.fetched_at",
                    (aid, "mesh:" + str(adv.get("source") or ""), adv.get("title") or "",
                     adv.get("link") or "", "", adv.get("published") or "", now))
            count = conn.execute("SELECT COUNT(*) AS n FROM cve").fetchone()["n"]
        gen = digest.get("generated_at") or ""
        gen_ts = now
        try:
            gen_ts = time.mktime(time.strptime(gen, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
        except Exception:
            gen_ts = now
        self._state_save("mesh", last_attempt=now, last_success=gen_ts, last_error="", count=count)
        self._kv_set("collector", digest.get("collector") or {})
        try:
            with open(self.digest_path, "w") as f:
                json.dump(digest, f)
        except Exception:
            pass
        self.compute_matches()
        return {"ok": True, "imported": len(digest.get("items") or [])}

    # -- Navi's picture ----------------------------------------------
    def brief_text(self):
        with self._db() as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM cve").fetchone()["n"]
            if not total:
                return ""
            sec = self._sections(conn)
            states = {s: self._state_row(conn, s) for s in ("nvd", "kev", "epss")}
            collector = self._kv_get("collector", {}) or {}
        who = collector.get("name") or "this node"
        lines = ["[Threat intelligence — gathered by " + who + ", as of "
                 + _iso(time.time()) + "]"]
        lines.append("Known-exploited (KEV): " + str(sec["kev_total"]) + " total, "
                     + str(len(sec["kev_new"])) + " new. Matched to this operator's stack/cases: "
                     + str(len(sec["stack_matches"])) + ".")

        def fmt(r):
            bits = [r["id"]]
            prods = []
            try:
                prods = json.loads(r["products"] or "[]")
            except Exception:
                prods = []
            if prods:
                bits.append(prods[0])
            if r["cvss"]:
                bits.append("CVSS " + str(r["cvss"]))
            if r["epss"] is not None:
                bits.append("EPSS " + str(round(r["epss"], 2)))
            if r["kev"]:
                bits.append("KEV" + ((" due " + r["kev_due"]) if r["kev_due"] else ""))
            m = None
            try:
                m = json.loads(r["matched"]) if r["matched"] else None
            except Exception:
                m = None
            if m:
                bits.append("matches " + str(m.get("via")) + " term “" + str(m.get("term")) + "” (" + str(m.get("grade")) + ")")
            title = (r["title"] or "")[:90]
            return " · ".join(bits) + (" — " + title if title else "")

        shown = 0
        if sec["stack_matches"]:
            lines.append("Stack & case matches:")
            for r in sec["stack_matches"][:6]:
                lines.append("- " + fmt(r))
                shown += 1
        if sec["kev_new"]:
            lines.append("New on the KEV list:")
            for r in sec["kev_new"][:4]:
                if shown >= 10:
                    break
                lines.append("- " + fmt(r))
                shown += 1
        if sec["top_new"]:
            lines.append("Notable new disclosures:")
            for r in sec["top_new"][:3]:
                if shown >= 12:
                    break
                lines.append("- " + fmt(r))
                shown += 1
        fresh = []
        for s in ("nvd", "kev", "epss"):
            age = _hours_since(states[s].get("last_success"))
            fresh.append(SOURCE_LABELS[s] + " " + (_band(age) if age is not None else "never")
                         + (" (" + str(age) + "h)" if age is not None else ""))
        lines.append("Freshness: " + " · ".join(fresh) + ". Treat stale bands as last-good, not current.")
        text = "\n".join(lines)
        return text[:2300]

    def brief_block(self):
        s = self.settings()
        if not s.get("enabled", True):
            return ""
        return self.brief_text()

    def _record_lines(self, rows, cap=1500):
        out = []
        for r in rows:
            desc = (r["description"] or "")[:400]
            line = (r["id"] + " — " + (r["title"] or "")
                    + (" · CVSS " + str(r["cvss"]) if r["cvss"] else "")
                    + (" · EPSS " + str(round(r["epss"], 3)) if r["epss"] is not None else "")
                    + (" · KEV, due " + (r["kev_due"] or "?") if r["kev"] else "")
                    + ("\n" + desc if desc else ""))
            out.append(line)
        return "\n".join(out)[:cap]

    def message_context(self, text):
        # Layer 3, the seam: an exact CVE ID or a watchlist/case
        # term in the operator's own message pulls the record
        # into this reply's context. Nothing is retrieved on
        # unrelated chat.
        if not text:
            return ""
        ids = list(dict.fromkeys(m.upper() for m in CVE_ID_RE.findall(text)))
        blocks = []
        with self._db() as conn:
            for cid in ids[:3]:
                row = conn.execute("SELECT * FROM cve WHERE id=?", (cid,)).fetchone()
                if row:
                    blocks.append(self._record_lines([row]))
                else:
                    blocks.append(cid + " — not in the local intel store (never matched a pull, or the store is stale). Say so plainly rather than guessing.")
            if not ids:
                low = " " + text.lower() + " "
                terms = [t for t in self.match_terms() if len(t["term"]) >= 4]
                hit_terms = [t for t in terms
                             if re.search(r"(?<![a-z0-9])" + re.escape(t["term"]) + r"(?![a-z0-9])", low)]
                if hit_terms:
                    rows = conn.execute("SELECT * FROM cve WHERE matched IS NOT NULL").fetchall()
                    mine = [r for r in rows
                            if (json.loads(r["matched"] or "{}") or {}).get("term") in
                            [t["term"] for t in hit_terms]]
                    mine.sort(key=self._rank)
                    if mine:
                        blocks.append("Intel records matching what the operator just named:\n"
                                      + self._record_lines(mine[:3]))
        if not blocks:
            return ""
        return "[Threat intelligence — records for this message]\n" + "\n".join(blocks)

    def case_context(self, terms):
        # In a case-bound chat, the case's own matched records
        # ride along (ranked, capped) — the join between the
        # Center and Case Files.
        words = [str(t or "").strip().lower() for t in (terms or [])]
        words = [w for w in words if len(w) >= 3 and w not in STOPWORDS]
        if not words:
            return ""
        with self._db() as conn:
            rows = conn.execute("SELECT * FROM cve WHERE matched IS NOT NULL").fetchall()
        mine = []
        for r in rows:
            m = json.loads(r["matched"] or "{}") or {}
            if m.get("via") == "case" and m.get("term") in words:
                mine.append(r)
        if not mine:
            return ""
        mine.sort(key=self._rank)
        return ("[Threat intelligence — records matching this case]\n"
                + self._record_lines(mine[:4]))

    def lookup(self, query):
        # Layer 2: a deliberate lookup ("intel: …", "what do we
        # know about CVE-…") answered straight from the store.
        q = (query or "").strip()
        ids = CVE_ID_RE.findall(q)
        with self._db() as conn:
            total = conn.execute("SELECT COUNT(*) AS n FROM cve").fetchone()["n"]
            if not total:
                return ("The Threat Intelligence Center's store is empty — nothing has been "
                        "collected yet. Open Apex | Apps → Threat Intelligence and pull, "
                        "or wait for the scheduled cycle.")
            if ids:
                row = conn.execute("SELECT * FROM cve WHERE id=?", (ids[0].upper(),)).fetchone()
                if not row:
                    return (ids[0].upper() + " is not in the local intel store. That means no "
                            "pull has seen it — the store may be stale; check the freshness "
                            "stamps in Threat Intelligence before treating absence as safety.")
                return self._record_lines([row], cap=1800)
            words = [w for w in re.findall(r"[a-z0-9][a-z0-9._-]{2,}", q.lower())
                     if w not in STOPWORDS]
            rows = conn.execute("SELECT * FROM cve").fetchall()
            scored = []
            for r in rows:
                hay = ((r["title"] or "") + " " + (r["description"] or "") + " "
                       + (r["products"] or "")).lower()
                score = sum(1 for w in words if w in hay)
                if score:
                    scored.append((score, r))
            scored.sort(key=lambda t: (-t[0], self._rank(t[1])))
            if not scored:
                return ("Nothing in the local intel store matches “" + q[:80] + "”. "
                        "Absence here is absence from the store, not proof of safety.")
            return ("From the local intel store (" + str(total) + " records):\n"
                    + self._record_lines([r for _s, r in scored[:5]], cap=2200))

    # -- surface ------------------------------------------------------
    def state(self):
        s = self.settings()
        with self._db() as conn:
            rows = conn.execute("SELECT * FROM cve").fetchall()
            sec = self._sections(conn)
            states = []
            for source in SOURCE_LABELS:
                st = self._state_row(conn, source)
                age = _hours_since(st.get("last_success"))
                states.append({
                    "source": source, "label": SOURCE_LABELS[source],
                    "lastAttempt": st.get("last_attempt") or 0,
                    "lastSuccess": st.get("last_success") or 0,
                    "ageHours": age, "band": _band(age),
                    "count": st.get("count") or 0, "error": st.get("last_error") or "",
                })
            advisories = [{"source": r["source"], "title": r["title"], "link": r["link"],
                           "published": r["published"]}
                          for r in conn.execute("SELECT * FROM advisory ORDER BY fetched_at DESC LIMIT 15")]
            collector = self._kv_get("collector", {}) or {}
            item_count = conn.execute("SELECT COUNT(*) AS n FROM cve WHERE matched IS NOT NULL").fetchone()["n"]
        queue = []
        seen_ids = set()
        for group in (sec["stack_matches"], sec["kev_new"], sec["top_new"]):
            for r in group:
                if r["id"] not in seen_ids:
                    seen_ids.add(r["id"])
                    queue.append(self._lite(r))
        queue = queue[:60]
        return {
            "ok": True,
            "enabled": bool(s.get("enabled", True)),
            "mode": self.mode(),
            "collector": collector,
            "collectorPeer": s.get("collectorPeer") or "",
            "fallbackLocal": bool(s.get("fallbackLocal")),
            "sources": states,
            "kevTotal": sec["kev_total"],
            "matchedCount": item_count,
            "watchlist": list(s.get("watchlist") or []),
            "queue": queue,
            "movers": [{"id": r["id"], "delta": d} for r, d in sec["epss_movers"]],
            "advisories": advisories,
            "brief": self.brief_text(),
            "pulling": bool(self._pulling),
            "cadenceHours": s.get("cadenceHours") or 6,
            "settings": {"sources": s.get("sources") or {}},
        }

    def item(self, cve_id):
        cid = str(cve_id or "").upper()
        with self._db() as conn:
            row = conn.execute("SELECT * FROM cve WHERE id=?", (cid,)).fetchone()
            if not row:
                return None
            full = self._lite(row)
            full["description"] = row["description"] or ""
            try:
                full["refs"] = json.loads(row["refs"] or "[]")
            except Exception:
                full["refs"] = []
            hist = conn.execute("SELECT date, epss FROM epss_history WHERE cve_id=? "
                                "ORDER BY date DESC LIMIT 14", (cid,)).fetchall()
            full["epssHistory"] = [{"date": h["date"], "epss": h["epss"]} for h in hist]
            return full


def _nvd_record(item):
    cve = (item or {}).get("cve") or {}
    cid = str(cve.get("id") or "").upper()
    if not CVE_ID_RE.fullmatch(cid):
        return None
    desc = ""
    for d in cve.get("descriptions") or []:
        if d.get("lang") == "en":
            desc = d.get("value") or ""
            break
    cvss, sev = None, ""
    metrics = cve.get("metrics") or {}
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        for m in metrics.get(key) or []:
            if m.get("type") == "Primary" or cvss is None:
                data = m.get("cvssData") or {}
                if data.get("baseScore") is not None:
                    cvss = float(data["baseScore"])
                    sev = data.get("baseSeverity") or ""
                    break
        if cvss is not None:
            break
    products = []
    for conf in cve.get("configurations") or []:
        for node in conf.get("nodes") or []:
            for match in node.get("cpeMatch") or []:
                crit = str(match.get("criteria") or "")
                parts = crit.split(":")
                if len(parts) >= 5 and parts[3] not in ("*", "-") and parts[4] not in ("*", "-"):
                    pair = parts[3].lower() + ":" + parts[4].lower()
                    if pair not in products:
                        products.append(pair)
                    if parts[4].lower() not in products:
                        products.append(parts[4].lower())
    refs = [r.get("url") for r in (cve.get("references") or []) if r.get("url")][:8]
    title = desc.split(". ")[0][:140] if desc else cid
    return {"id": cid, "title": title, "description": desc[:4000],
            "cvss": cvss, "cvss_severity": sev, "products": products[:24],
            "refs": refs, "published": cve.get("published") or "",
            "modified": cve.get("lastModified") or ""}


def _rss_items(raw):
    # RSS 2.0 and Atom, namespace-agnostic: news only, never a
    # scrape — the item's own fields, nothing more.
    try:
        root = ET.fromstring(raw.decode("utf-8", "replace"))
    except Exception:
        return []

    def tag(el):
        return el.tag.split("}")[-1].lower()

    def child(el, name):
        for c in el:
            if tag(c) == name:
                return c
        return None

    def text(el, name):
        c = child(el, name)
        return (c.text or "").strip() if c is not None and c.text else ""

    out = []
    containers = []
    for el in root.iter():
        if tag(el) in ("item", "entry"):
            containers.append(el)
    for it in containers[:40]:
        title = text(it, "title")
        link = text(it, "link")
        if not link:
            for c in it:
                if tag(c) == "link" and c.get("href"):
                    link = c.get("href")
                    break
        guid = text(it, "guid") or text(it, "id") or link
        summary = text(it, "description") or text(it, "summary")
        summary = re.sub(r"<[^>]+>", " ", summary)
        summary = re.sub(r"\s+", " ", summary).strip()[:400]
        published = text(it, "pubdate") or text(it, "published") or text(it, "updated")
        if title and link:
            out.append({"id": guid or link, "title": title[:220], "link": link,
                        "summary": summary, "published": published})
    return out
