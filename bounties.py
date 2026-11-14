# bounties.py — the bug-bounty board engine (0.2.0e Build 7,
# Scope Addition 5).
#
# Programs from ProjectDiscovery's Chaos index — the public,
# keyless JSON of public bug-bounty programs. Verified live at
# bake time (2026-11-13): the index moved off the marketing
# host (chaos.projectdiscovery.io/index.json answers 404) and
# lives on the data host:
#   https://chaos-data.projectdiscovery.io/index.json
# Entries carry: name, program_url (the program link),
# platform, bounty (pays-money flag), count (the program's
# enumerated scope size in the Chaos dataset), is_new,
# last_updated. The index carries NO safe-harbor field — cards
# say "not stated by the index" rather than inventing one.
#
# Disclosed reports: HackerOne's hacktivity was probed live at
# bake time and no keyless feed proved out (the GraphQL
# endpoint answers, but exposes no public hacktivity field
# without an account). Per the build's ruling, the family
# ships programs-first with the reports section as a NAMED
# empty state — a sentence, never invented rows. The store and
# payload keep a reports slot so a proven feed can land later
# without a shape change.
#
# Same posture as the wire: outbound-only, no accounts, no
# keys, local cache (config/bounties/bounties.json), named
# staleness, a dead source is a sentence. Stdlib only; never
# imports the bridge; the fetcher is injectable for fixtures.

import gzip
import json
import os
import threading
import time
import urllib.request
import urllib.error

CHAOS_URL = "https://chaos-data.projectdiscovery.io/index.json"
MAX_PROGRAMS = 3000
REPORTS_SENTENCE = ("No keyless disclosed-reports feed proved out at bake time — "
                    "HackerOne's hacktivity needs an account, so this section "
                    "ships empty on purpose rather than inventing rows.")


def _fetch(url, state, timeout=30):
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


def normalize_program(p):
    if not isinstance(p, dict):
        return None
    name = str(p.get("name") or "").strip()
    link = str(p.get("program_url") or "").strip()
    if not name or not link:
        return None
    try:
        scope = int(p.get("count") or 0)
    except Exception:
        scope = 0
    return {
        "name": name,
        "platform": str(p.get("platform") or "").strip(),
        "link": link,
        "bounty": bool(p.get("bounty")),
        "safeHarbor": None,  # the index does not state it; the card says so
        "scopeSize": scope,
        "isNew": bool(p.get("is_new")),
        "lastUpdated": str(p.get("last_updated") or ""),
        "dataUrl": str(p.get("URL") or ""),
    }


def parse_programs(raw):
    data = json.loads(raw.decode("utf-8", "replace"))
    if isinstance(data, dict):
        data = data.get("programs") or []
    out = []
    for p in data if isinstance(data, list) else []:
        norm = normalize_program(p)
        if norm:
            out.append(norm)
    # Bounty-paying first, then the freshly changed, then name.
    out.sort(key=lambda p: (not p["bounty"], p["name"].lower()))
    return out[:MAX_PROGRAMS]


class Bounties:
    def __init__(self, root, settings_getter, fetch=None):
        self.root = root
        self._settings = settings_getter
        self._fetch = fetch or _fetch
        self._lock = threading.Lock()
        self._pulling = False
        self.dir = os.path.join(root, "config", "bounties")
        self.path = os.path.join(self.dir, "bounties.json")

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("programs", [])
                data.setdefault("reports", [])
                return data
        except Exception:
            pass
        return {"programs": [], "reports": []}

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

    def refresh_now(self):
        # Threaded like the Center's: the caller never waits
        # on a feed; state() carries the outcome when it lands.
        with self._lock:
            if self._pulling:
                return {"ok": True, "pulling": True}
            self._pulling = True

        def run():
            try:
                self._refresh_cycle()
            finally:
                with self._lock:
                    self._pulling = False

        threading.Thread(target=run, daemon=True).start()
        return {"ok": True, "started": True}

    def _refresh_cycle(self):
        now = int(time.time())
        data = self._load()
        state = {"etag": data.get("etag") or "", "lastmod": data.get("lastmod") or ""}
        try:
            status, raw, new_state = self._fetch(CHAOS_URL, state)
            programs = list(data.get("programs") or []) if status == 304 \
                else parse_programs(raw)
            data = {"programs": programs, "reports": list(data.get("reports") or []),
                    "lastTry": now, "lastOk": now, "error": "",
                    "etag": new_state.get("etag", ""), "lastmod": new_state.get("lastmod", "")}
            self._save(data)
            return {"ok": True, "programs": len(programs)}
        except Exception as e:
            data["lastTry"] = now
            data["error"] = ("The Chaos index could not be fetched (" + str(e)[:140] + ").")
            self._save(data)
            return {"ok": False, "error": data["error"]}

    def start(self):
        def loop():
            while True:
                try:
                    s = self.settings()
                    if s.get("enabled", True):
                        data = self._load()
                        last = data.get("lastTry") or 0
                        interval = max(30, int(s.get("intervalMinutes") or 360)) * 60
                        if time.time() - last >= interval:
                            self.refresh_now()
                except Exception:
                    pass
                time.sleep(60)
        threading.Thread(target=loop, daemon=True).start()

    def staleness_sentence(self, data=None):
        data = data or self._load()
        last_ok = data.get("lastOk") or 0
        if data.get("error"):
            base = "The bounty board's source is not answering: " + data["error"]
            if last_ok:
                base += " The programs below are the last good fetch, from " + \
                    time.strftime("%Y-%m-%d %H:%M", time.gmtime(last_ok)) + " UTC."
            return base
        if not last_ok:
            return "The bounty board has not fetched the Chaos index yet."
        age_h = round((time.time() - last_ok) / 3600.0, 1)
        when = "under an hour ago" if age_h < 1 else str(age_h) + " hours ago"
        return "The Chaos index last fetched cleanly " + when + "."

    def state(self):
        s = self.settings()
        data = self._load()
        programs = list(data.get("programs") or [])
        return {
            "ok": True,
            "enabled": bool(s.get("enabled", True)),
            "intervalMinutes": int(s.get("intervalMinutes") or 360),
            "pulling": self._pulling,
            "lastOk": data.get("lastOk") or 0,
            "staleness": self.staleness_sentence(data),
            "error": data.get("error") or "",
            "programs": programs,
            "payingCount": sum(1 for p in programs if p.get("bounty")),
            "reports": list(data.get("reports") or []),
            "reportsSentence": REPORTS_SENTENCE,
        }

    def brief_block(self, limit=1000):
        s = self.settings()
        if not s.get("enabled", True):
            return ""
        st = self.state()
        if not st["programs"] and not st["lastOk"]:
            return ""
        lines = ["[On the bounty board — public programs from ProjectDiscovery's Chaos index]",
                 self.staleness_sentence(),
                 str(len(st["programs"])) + " programs listed, " + str(st["payingCount"])
                 + " of them bounty-paying."]
        fresh = [p for p in st["programs"] if p.get("isNew")][:4]
        for p in fresh:
            lines.append("- NEW: " + p["name"] + " (" + (p["platform"] or "platform unlisted")
                         + ", " + ("pays bounties" if p["bounty"] else "no bounty listed") + ").")
        lines.append("When the operator asks about bounties, speak from this board and cite "
                     "the Chaos index with its fetch stamp. The index does not state "
                     "safe-harbor terms — say so rather than guessing a program's terms.")
        return "\n".join(lines)[:limit]
