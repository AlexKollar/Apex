# ctf.py — the CTF board engine (0.2.0e Build 7, #189).
#
# A CTFtime API fetcher + local cache, same posture as the
# wire: outbound-only, no accounts, no keys, named staleness, a
# dead source is a sentence. The board carries everything the
# API gives per event — name, start/finish, format, online or
# on-site + location, weight, restrictions, organizers, logo,
# description, prizes where listed, the CTFtime link. Running
# now and upcoming are the two sections; past events fall off.
# Times ride as epochs in the payload and are rendered in the
# operator's own timezone by the page.
#
# CTFtime refuses requests without a User-Agent (403); the
# fetcher sends Apex's, as the Center's does.
#
# Stdlib only; never imports the bridge; the fetcher is
# injectable so the benches run on a recorded fixture.

import gzip
import html as html_mod
import json
import os
import re
import threading
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_URL = "https://ctftime.org/api/v1/events/"
FORMAT_LABELS = {1: "Jeopardy", 2: "Attack-Defense"}
DESC_CAP = 4000
_TAG_RE = re.compile(r"<[^>]+>")


def _fetch(url, state, timeout=25):
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


def _epoch(value):
    if isinstance(value, (int, float)):
        return int(value)
    if not value:
        return 0
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp())
    except Exception:
        return 0


def _plain(raw_html, cap=DESC_CAP):
    if not raw_html:
        return ""
    text = _TAG_RE.sub(" ", str(raw_html))
    text = html_mod.unescape(text)
    return re.sub(r"\s+", " ", text).strip()[:cap]


def normalize_event(ev):
    if not isinstance(ev, dict):
        return None
    start = _epoch(ev.get("start"))
    finish = _epoch(ev.get("finish"))
    title = str(ev.get("title") or "").strip()
    if not title or not start:
        return None
    fmt = str(ev.get("format") or "").strip()
    if not fmt:
        fmt = FORMAT_LABELS.get(ev.get("format_id"), "")
    organizers = []
    for org in ev.get("organizers") or []:
        if isinstance(org, dict) and org.get("name"):
            organizers.append(str(org["name"]))
        elif isinstance(org, str) and org:
            organizers.append(org)
    try:
        weight = float(ev.get("weight") or 0)
    except Exception:
        weight = 0.0
    return {
        "id": ev.get("id"),
        "title": title,
        "start": start,
        "finish": finish,
        "format": fmt,
        "onsite": bool(ev.get("onsite")),
        "location": str(ev.get("location") or ""),
        "weight": weight,
        "restrictions": str(ev.get("restrictions") or ""),
        "organizers": organizers,
        "logo": str(ev.get("logo") or ""),
        "description": _plain(ev.get("description") or ""),
        "prizes": _plain(ev.get("prizes") or "", cap=1200),
        "url": str(ev.get("url") or ""),
        "ctftimeUrl": str(ev.get("ctftime_url") or ""),
        "participants": ev.get("participants"),
    }


def parse_events(raw):
    data = json.loads(raw.decode("utf-8", "replace"))
    if isinstance(data, dict):
        data = data.get("events") or data.get("results") or []
    out = []
    for ev in data if isinstance(data, list) else []:
        norm = normalize_event(ev)
        if norm:
            out.append(norm)
    out.sort(key=lambda e: e["start"])
    return out


class Ctf:
    def __init__(self, root, settings_getter, fetch=None):
        self.root = root
        self._settings = settings_getter
        self._fetch = fetch or _fetch
        self._lock = threading.Lock()
        self._pulling = False
        self.dir = os.path.join(root, "config", "ctf")
        self.path = os.path.join(self.dir, "events.json")

    def _load(self):
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                data.setdefault("events", [])
                return data
        except Exception:
            pass
        return {"events": []}

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
        url = (API_URL + "?limit=100&start=" + str(now - 2 * 86400)
               + "&finish=" + str(now + 60 * 86400))
        data = self._load()
        try:
            status, raw, _ns = self._fetch(url, {})
            events = list(data.get("events") or []) if status == 304 \
                else parse_events(raw)
            data = {"events": events, "lastTry": now, "lastOk": now,
                    "error": ""}
            self._save(data)
            return {"ok": True, "events": len(events)}
        except Exception as e:
            data["lastTry"] = now
            data["error"] = ("CTFtime could not be fetched (" + str(e)[:140] + ").")
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
                        interval = max(10, int(s.get("intervalMinutes") or 60)) * 60
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
            base = "CTFtime is not answering: " + data["error"]
            if last_ok:
                base += " The board below is the last good fetch, from " + \
                    time.strftime("%Y-%m-%d %H:%M", time.gmtime(last_ok)) + " UTC."
            return base
        if not last_ok:
            return "The CTF board has not fetched yet."
        age_min = int((time.time() - last_ok) / 60)
        when = ("under a minute ago" if age_min < 1
                else str(age_min) + " minutes ago" if age_min < 90
                else str(round(age_min / 60.0, 1)) + " hours ago")
        return "The board last fetched cleanly " + when + "."

    def state(self):
        s = self.settings()
        data = self._load()
        now = time.time()
        events = [e for e in data.get("events") or [] if (e.get("finish") or 0) >= now]
        running = [e for e in events if e["start"] <= now <= e["finish"]]
        upcoming = [e for e in events if e["start"] > now]
        return {
            "ok": True,
            "enabled": bool(s.get("enabled", True)),
            "intervalMinutes": int(s.get("intervalMinutes") or 60),
            "pulling": self._pulling,
            "lastOk": data.get("lastOk") or 0,
            "staleness": self.staleness_sentence(data),
            "error": data.get("error") or "",
            "running": running,
            "upcoming": upcoming,
        }

    def brief_block(self, limit=1200):
        s = self.settings()
        if not s.get("enabled", True):
            return ""
        st = self.state()
        if not st["running"] and not st["upcoming"] and not st["lastOk"]:
            return ""
        lines = ["[On the CTF board — from CTFtime, via the local cache]",
                 self.staleness_sentence()]
        for e in st["running"][:3]:
            lines.append("- RUNNING NOW: " + e["title"] + " (" + (e["format"] or "format unlisted")
                         + ", " + ("on-site, " + e["location"] if e["onsite"] else "online")
                         + ") — ends " + time.strftime("%Y-%m-%d %H:%M", time.gmtime(e["finish"])) + " UTC.")
        for e in st["upcoming"][:4]:
            lines.append("- " + e["title"] + " — starts "
                         + time.strftime("%Y-%m-%d %H:%M", time.gmtime(e["start"])) + " UTC ("
                         + (e["format"] or "format unlisted") + ", "
                         + ("on-site, " + e["location"] if e["onsite"] else "online")
                         + ", weight " + str(e["weight"]) + ").")
        lines.append("When the operator asks what's on or what's worth playing, speak from "
                     "this board and cite the listing (CTFtime, with its fetch stamp) — the "
                     "board's times here are UTC; the CTF tab shows them in the operator's "
                     "own timezone.")
        return "\n".join(lines)[:limit]
