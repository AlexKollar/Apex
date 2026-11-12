#!/usr/bin/env python3
"""Guardian — Apex's system monitor (Build 14, #156).

Stdlib only, and deliberately NOT importing bridge: bridge imports
this module, so this module must stand on its own (no cycles).

Guardian watches the machine Navi lives on and protects her
headroom. While the bridge runs (including headless), a daemon
sampler reads /proc every sampleSeconds: how much memory is really
available, and which processes are eating CPU / RAM. Pressure is
judged against the operator's reserve:

  ok       free >= reserve * 1.5
  tight    free <  reserve * 1.5
  critical free <  reserve

While a local generation is running the same ladder is one level
stricter (tight below reserve * 2, critical below reserve * 1.25)
— generation is when starvation hurts: a swapped-out, CPU-starved
llamafile is the "she is not chatting" failure wearing a different
coat.

Offenders (our uid only, never protected processes, never kernel
threads) climb a ladder while pressure is tight/critical:

  warn     an event, at most once per pid per 60 seconds
  throttle after warnAfterSeconds of continuous offence:
           a duty-cycle CPU cap (SIGSTOP/SIGCONT in 100ms slices
           approximating cpuCapPercent) plus a best-effort renice
           to 19. The duty cycle is the reversible mechanism — an
           unprivileged process cannot always restore its own
           nice value, so unthrottling never depends on that.
  kill     only when the process NAME is on the operator's
           expendable list, killEnabled is on, and pressure has
           stayed critical for killGraceSeconds after the
           throttle: SIGTERM, a 3-second grace, then SIGKILL.

Guardian also learns, in config/guardian-stats.json: which process
names were burning CPU while Navi generated, and — when the bridge
reports a slow generation via note_generation() — which of them
collided with it. Every action lands in an in-memory log (last
200) mirrored to config/guardian-log.jsonl.

No exception in a tick may kill the sampler thread or propagate:
a dead guardian protects nothing, and a crashing one is worse.
"""

import collections
import json
import os
import signal
import socket
import threading
import time

# Names Guardian will never act on, whatever they do — the
# machine's own skeleton. (Pids are protected separately: pid 1,
# our own pid, and every llamafile pid.)
HARD_DENY = frozenset(("systemd", "sshd", "init"))

DEFAULT_SETTINGS = {
    "enabled": True,
    "reserveMb": 1024,
    "sampleSeconds": 2,
    "slowGenSeconds": 20,
    "cpuCapPercent": 50,
    "killEnabled": True,
    "expendable": [],
    "warnAfterSeconds": 6,
    "killGraceSeconds": 15,
}

# A process counts as offending at/above this CPU, or at/above the
# reserve in RSS (see the ladder in the module docstring).
OFFENDER_CPU_PERCENT = 50.0
# While generating, a process at/above this CPU accrues exposure —
# the raw material note_generation() turns into collisions.
EXPOSURE_CPU_PERCENT = 20.0


def _as_int(value, fallback):
    try:
        return int(value)
    except Exception:
        return fallback


def _as_float(value, fallback):
    try:
        return float(value)
    except Exception:
        return fallback


def normalize_settings(raw):
    """A complete Guardian settings dict from a partial/absent one."""
    s = raw if isinstance(raw, dict) else {}
    expendable = s.get("expendable")
    if not isinstance(expendable, list):
        expendable = []
    expendable = [str(x).strip() for x in expendable if str(x).strip()]
    return {
        "enabled": s.get("enabled") is not False,
        "reserveMb": max(16, _as_int(s.get("reserveMb"), DEFAULT_SETTINGS["reserveMb"])),
        "sampleSeconds": min(60.0, max(0.2, _as_float(s.get("sampleSeconds"), DEFAULT_SETTINGS["sampleSeconds"]))),
        "slowGenSeconds": max(1, _as_int(s.get("slowGenSeconds"), DEFAULT_SETTINGS["slowGenSeconds"])),
        "cpuCapPercent": min(100, max(1, _as_int(s.get("cpuCapPercent"), DEFAULT_SETTINGS["cpuCapPercent"]))),
        "killEnabled": s.get("killEnabled") is not False,
        "expendable": expendable,
        "warnAfterSeconds": max(0, _as_int(s.get("warnAfterSeconds"), DEFAULT_SETTINGS["warnAfterSeconds"])),
        "killGraceSeconds": max(0, _as_int(s.get("killGraceSeconds"), DEFAULT_SETTINGS["killGraceSeconds"])),
    }


def _empty_stat_row():
    return {
        "seen": 0,
        "genExposureTicks": 0,
        "collisions": 0,
        "warns": 0,
        "throttles": 0,
        "kills": 0,
        "lastSeen": 0,
    }


class Guardian:
    """The Guardian engine. One instance per bridge process.

    root_dir: the install root — learning store and log live in
    <root>/config/. settings_getter: a callable returning the raw
    guardian settings dict; it is read FRESH every tick, so a
    settings save takes effect without a restart. callbacks: a
    dict with own_pid (an int, or a callable returning one),
    llamafile_pids (callable -> list[int]) and is_generating
    (callable -> bool); mesh_getter (callable -> (enabled, peers)
    or {"enabled":…, "peers":…}) may ride in the same dict or be
    passed as its own keyword.
    """

    def __init__(self, root_dir, settings_getter=None, callbacks=None, mesh_getter=None):
        self.root_dir = str(root_dir or ".")
        self._settings_getter = settings_getter
        self._callbacks = callbacks if isinstance(callbacks, dict) else {}
        if mesh_getter is None:
            mesh_getter = self._callbacks.get("mesh_getter") or self._callbacks.get("mesh")
        self._mesh_getter = mesh_getter
        self._config_dir = os.path.join(self.root_dir, "config")
        self._stats_path = os.path.join(self._config_dir, "guardian-stats.json")
        self._log_path = os.path.join(self._config_dir, "guardian-log.jsonl")
        try:
            self._clk_tck = float(os.sysconf("SC_CLK_TCK"))
        except Exception:
            self._clk_tck = 100.0
        try:
            self._page_size = float(os.sysconf("SC_PAGE_SIZE"))
        except Exception:
            self._page_size = 4096.0
        try:
            self._our_uid = os.getuid()
        except Exception:
            self._our_uid = None

        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._sampler = None
        self._throttler = None

        self._settings = normalize_settings(None)
        self._enabled = True
        self._pressure = "ok"
        self._free_mb = 0
        self._llama_rss_mb = 0.0
        self._generating = False
        self._last_tick = 0.0
        self._procs = []            # latest sample, dicts (see _read_processes)
        self._offenders_now = []    # latest sample's offender dicts

        self._prev_cpu = {}         # pid -> (jiffies, stamp, starttime)
        self._tracks = {}           # pid -> ladder state for one offence episode
        self._throttled = {}        # pid -> {"name", "since", "last_offense"}
        self._warn_cooldown = {}    # pid -> stamp of its last warn event
        self._killing = set()       # pids with a kill already in flight

        self._events = collections.deque(maxlen=200)
        self._stats = self._load_stats()
        self._stats_dirty = False
        self._gen_exposure = {}     # name -> ticks, this generation only

    # -- callbacks, all failure-proof --------------------------------

    def _own_pid(self):
        cb = self._callbacks.get("own_pid")
        try:
            if callable(cb):
                return int(cb())
            if cb is not None:
                return int(cb)
        except Exception:
            pass
        return os.getpid()

    def _llamafile_pids(self):
        pids = []
        cb = self._callbacks.get("llamafile_pids")
        if callable(cb):
            try:
                for p in cb() or []:
                    try:
                        pids.append(int(p))
                    except Exception:
                        pass
            except Exception:
                pids = []
        if not pids:
            # Fallback (Build 14, #156): the bridge's handle on the
            # llamafile process can be empty (it was started by a
            # launcher, not by this bridge) — find her in /proc by
            # the binary's name on the command line instead.
            pids = self._scan_llamafile_pids()
        return pids

    @staticmethod
    def _scan_llamafile_pids():
        found = []
        try:
            names = os.listdir("/proc")
        except Exception:
            return found
        for name in names:
            if not name.isdigit():
                continue
            try:
                with open(os.path.join("/proc", name, "cmdline"), "rb") as f:
                    cmd = f.read().decode("utf-8", "replace")
                if "navi.llamafile" in cmd:
                    found.append(int(name))
            except Exception:
                continue
        return found

    def _is_generating(self):
        cb = self._callbacks.get("is_generating")
        if callable(cb):
            try:
                return bool(cb())
            except Exception:
                return False
        return False

    def _mesh(self):
        getter = self._mesh_getter
        if not callable(getter):
            return {"enabled": False, "peers": 0}
        try:
            value = getter()
        except Exception:
            return {"enabled": False, "peers": 0}
        if isinstance(value, dict):
            return {"enabled": bool(value.get("enabled")), "peers": _as_int(value.get("peers"), 0)}
        if isinstance(value, (list, tuple)) and len(value) >= 2:
            return {"enabled": bool(value[0]), "peers": _as_int(value[1], 0)}
        return {"enabled": False, "peers": 0}

    def settings(self):
        """The current normalized settings — read fresh, every call."""
        raw = None
        if callable(self._settings_getter):
            try:
                raw = self._settings_getter()
            except Exception:
                raw = None
        self._settings = normalize_settings(raw)
        return dict(self._settings)

    # -- learning store ------------------------------------------------

    def _load_stats(self):
        try:
            with open(self._stats_path) as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
            out = {}
            for name, row in data.items():
                if not isinstance(row, dict):
                    continue
                clean = _empty_stat_row()
                for key in clean:
                    clean[key] = _as_int(row.get(key), 0) if key != "lastSeen" else _as_float(row.get(key), 0)
                out[str(name)] = clean
            return out
        except Exception:
            return {}

    def _save_stats(self):
        # Atomic: write beside the store, then replace — a crash
        # mid-write can never leave a torn stats file behind.
        try:
            os.makedirs(self._config_dir, exist_ok=True)
            tmp = self._stats_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(self._stats, f, indent=1, sort_keys=True)
            os.replace(tmp, self._stats_path)
            self._stats_dirty = False
        except Exception:
            pass

    def _stat_row(self, name):
        row = self._stats.get(name)
        if row is None:
            row = _empty_stat_row()
            self._stats[name] = row
        return row

    def note_generation(self, duration_s):
        """Called by the bridge after each local generation.

        A generation at/over slowGenSeconds was slow; the three
        process names that burned the most CPU while it ran take a
        collision each. Exposure counters reset every generation,
        slow or not — they describe ONE generation at a time.
        """
        try:
            settings = self.settings()
            dur = _as_float(duration_s, 0)
            with self._lock:
                exposure = dict(self._gen_exposure)
                self._gen_exposure = {}
                if dur >= settings["slowGenSeconds"] and exposure:
                    top = sorted(exposure.items(), key=lambda kv: (-kv[1], kv[0]))[:3]
                    for name, _ticks in top:
                        self._stat_row(name)["collisions"] += 1
                    self._stats_dirty = True
                if self._stats_dirty:
                    self._save_stats()
        except Exception:
            pass

    # -- event log ------------------------------------------------------

    def _origin(self):
        # Provenance (Build 14, #156, Alex's schema favor): every
        # event names the node it happened on — the Mesh nodeName
        # from this install's config when the operator set one,
        # else the OS hostname. Read at event time from the config
        # beside the log, tolerantly: a Guardian event must never
        # fail to land because its provenance could not be read.
        device = ""
        try:
            with open(os.path.join(self._config_dir, "navi.config.json")) as f:
                cfg = json.load(f)
            mesh = cfg.get("mesh") if isinstance(cfg, dict) else None
            if isinstance(mesh, dict):
                device = str(mesh.get("nodeName") or "").strip()
        except Exception:
            device = ""
        if not device:
            try:
                device = socket.gethostname() or "unknown"
            except Exception:
                device = "unknown"
        return {"device": device, "door": "engine"}

    def _log_event(self, kind, text, pid=None, name=None):
        # The single event-creation point: the in-memory deque,
        # guardian-log.jsonl, and state()["log"] all carry exactly
        # what is built here — including the provenance fields
        # (Build 14, #156): "origin" (this node + the door that
        # raised the event; engine-generated events say "engine")
        # and "foreground", the posture tag later policy keys on.
        # This build does NOT detect foreground context — the
        # honest value is "unknown" (working / gaming / idle are
        # future values, recorded by whoever can actually know).
        entry = {"ts": time.time(), "kind": str(kind), "text": str(text),
                 "origin": self._origin(), "foreground": "unknown"}
        if pid is not None:
            entry["pid"] = pid
        if name is not None:
            entry["name"] = name
        with self._lock:
            self._events.append(entry)
        try:
            os.makedirs(self._config_dir, exist_ok=True)
            with open(self._log_path, "a") as f:
                f.write(json.dumps(entry) + "\n")
            if os.path.getsize(self._log_path) > 1024 * 1024:
                with open(self._log_path) as f:
                    lines = f.readlines()
                tmp = self._log_path + ".tmp"
                with open(tmp, "w") as f:
                    f.writelines(lines[-500:])
                os.replace(tmp, self._log_path)
        except Exception:
            pass
        return entry

    # -- /proc sampling ---------------------------------------------------

    @staticmethod
    def _mem_available_mb():
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemAvailable:"):
                        return int(line.split()[1]) // 1024
        except Exception:
            pass
        return 0

    def _read_processes(self, now):
        procs = []
        try:
            names = os.listdir("/proc")
        except Exception:
            return procs
        new_prev = {}
        for name in names:
            if not name.isdigit():
                continue
            pid = int(name)
            base = os.path.join("/proc", name)
            try:
                with open(os.path.join(base, "stat"), "rb") as f:
                    raw = f.read().decode("utf-8", "replace")
                # comm sits in parens and may itself contain spaces
                # or parens — split on the FIRST '(' and LAST ')'.
                lp = raw.find("(")
                rp = raw.rfind(")")
                if lp < 0 or rp <= lp:
                    continue
                comm = raw[lp + 1:rp]
                rest = raw[rp + 2:].split()
                # rest[0] is field 3 (state); utime/stime are fields
                # 14/15, starttime field 22, rss field 24.
                jiffies = int(rest[11]) + int(rest[12])
                starttime = int(rest[19])
                rss_pages = int(rest[21])
                uid = os.stat(base).st_uid
            except Exception:
                continue
            cpu = 0.0
            prev = self._prev_cpu.get(pid)
            if prev is not None and prev[2] == starttime:
                dt = now - prev[1]
                if dt > 0:
                    cpu = ((jiffies - prev[0]) / self._clk_tck) / dt * 100.0
            new_prev[pid] = (jiffies, now, starttime)
            rss_mb = max(0.0, rss_pages * self._page_size / 1048576.0)
            procs.append({
                "pid": pid,
                "name": comm,
                "uid": uid,
                "rssMb": rss_mb,
                "cpu": round(max(0.0, cpu), 1),
                "ours": (self._our_uid is not None and uid == self._our_uid),
            })
        self._prev_cpu = new_prev
        return procs

    # -- the ladder -------------------------------------------------------

    def _set_priority(self, pid, nice):
        try:
            os.setpriority(os.PRIO_PROCESS, pid, nice)
            return True
        except Exception:
            return False

    @staticmethod
    def _signal(pid, sig):
        try:
            os.kill(pid, sig)
            return True
        except Exception:
            return False

    def _throttle(self, pid, name, settings, now):
        self._throttled[pid] = {"name": name, "since": now, "last_offense": now}
        ok = self._set_priority(pid, 19)
        with self._lock:
            self._stat_row(name)["throttles"] += 1
            self._stats_dirty = True
        self._log_event(
            "throttle",
            "Throttled %s (pid %d) to about %d%% CPU — it kept offending under %s pressure."
            % (name, pid, settings["cpuCapPercent"], self._pressure),
            pid=pid, name=name)
        if not ok:
            # Swallowed, but not silently (Build 14, #156): the
            # renice is best-effort only; the duty cycle below is
            # what actually caps the process, and it needs no
            # privilege at all.
            self._log_event(
                "note",
                "Could not renice %s (pid %d) — the duty-cycle cap still applies; unprivileged renice is best-effort." % (name, pid),
                pid=pid, name=name)

    def _unthrottle(self, pid, reason):
        info = self._throttled.pop(pid, None)
        if info is None:
            return
        self._signal(pid, signal.SIGCONT)
        ok = self._set_priority(pid, 0)
        self._log_event(
            "unthrottle",
            "Released %s (pid %d) — %s." % (info.get("name") or "?", pid, reason),
            pid=pid, name=info.get("name"))
        if not ok:
            self._log_event(
                "note",
                "Could not restore the nice value of %s (pid %d) — it is no longer duty-cycled, and its priority returns to normal when it next restarts." % (info.get("name") or "?", pid),
                pid=pid, name=info.get("name"))

    def _kill(self, pid, name):
        # SIGTERM, a 3-second grace, SIGKILL — run on its own
        # thread so the sampler never stalls on a dying process.
        try:
            self._signal(pid, signal.SIGCONT)  # a stopped process cannot act on SIGTERM
            self._signal(pid, signal.SIGTERM)
            deadline = time.time() + 3.0
            while time.time() < deadline:
                try:
                    os.kill(pid, 0)
                    # A zombie is dead for every purpose that
                    # matters here — its parent just hasn't reaped
                    # it yet, and os.kill(pid, 0) still answers.
                    with open("/proc/%d/stat" % pid, "rb") as _zf:
                        _zraw = _zf.read().decode("utf-8", "replace")
                    if _zraw[_zraw.rfind(")") + 2:].split()[0] == "Z":
                        break
                except Exception:
                    break
                time.sleep(0.1)
            else:
                self._signal(pid, signal.SIGKILL)
                time.sleep(0.2)
            with self._lock:
                self._stat_row(name)["kills"] += 1
                self._stats_dirty = True
                self._save_stats()
            self._log_event(
                "kill",
                "Killed %s (pid %d) — expendable, and pressure stayed critical past the grace after its throttle." % (name, pid),
                pid=pid, name=name)
        except Exception:
            pass
        finally:
            self._throttled.pop(pid, None)
            self._tracks.pop(pid, None)
            self._killing.discard(pid)

    def _ladder(self, settings, procs, protected_pids, now):
        reserve = settings["reserveMb"]
        by_pid = {p["pid"]: p for p in procs}
        offenders = {}
        for p in procs:
            if p["pid"] in protected_pids or p["pid"] == 1:
                continue
            if not p["ours"] or p["rssMb"] <= 0:
                continue
            if p["name"] in HARD_DENY:
                continue
            if p["cpu"] >= OFFENDER_CPU_PERCENT or p["rssMb"] >= reserve:
                offenders[p["pid"]] = p
        # A throttled process has its CPU suppressed BY US — it
        # stays on the ladder while pressure holds and it lives,
        # or the kill grace could never run out.
        for pid in list(self._throttled):
            p = by_pid.get(pid)
            if p is not None and pid not in offenders:
                offenders[pid] = p
        self._offenders_now = sorted(
            offenders.values(), key=lambda p: (p["cpu"], p["rssMb"]), reverse=True)

        if self._pressure in ("tight", "critical"):
            for pid, p in offenders.items():
                track = self._tracks.get(pid)
                if track is None:
                    track = {"since": now, "warn_ts": None, "throttle_ts": None, "name": p["name"]}
                    self._tracks[pid] = track
                track["name"] = p["name"]
                track["last"] = now
                if track["warn_ts"] is None:
                    last_warn = self._warn_cooldown.get(pid, 0)
                    if now - last_warn >= 60:
                        self._warn_cooldown[pid] = now
                        track["warn_ts"] = now
                        with self._lock:
                            self._stat_row(p["name"])["warns"] += 1
                            self._stats_dirty = True
                        self._log_event(
                            "warn",
                            "Warned %s (pid %d): %.0f%% CPU, %.0f MB RSS while pressure is %s (%.0f MB free, reserve %d MB)."
                            % (p["name"], pid, p["cpu"], p["rssMb"], self._pressure, self._free_mb, reserve),
                            pid=pid, name=p["name"])
                    else:
                        # Already warned inside the cooldown — the
                        # ladder times from that warn, not from a
                        # warn it was not allowed to repeat.
                        track["warn_ts"] = last_warn
                if pid in self._throttled:
                    info = self._throttled[pid]
                    track["throttle_ts"] = info["since"]
                    if p["cpu"] >= OFFENDER_CPU_PERCENT or p["rssMb"] >= reserve:
                        info["last_offense"] = now
                elif track["warn_ts"] is not None and now - track["warn_ts"] >= settings["warnAfterSeconds"]:
                    # Still offending warnAfterSeconds after its
                    # warn — that IS the "sustained" test.
                    self._throttle(pid, p["name"], settings, now)
                    track["throttle_ts"] = now
                if (pid in self._throttled
                        and p["name"] in settings["expendable"]
                        and settings["killEnabled"]
                        and self._pressure == "critical"
                        and track.get("throttle_ts") is not None
                        and now - track["throttle_ts"] >= settings["killGraceSeconds"]
                        and pid not in self._killing):
                    self._killing.add(pid)
                    t = threading.Thread(target=self._kill, args=(pid, p["name"]), daemon=True)
                    t.start()
            # Episodes end when the offence does — except throttled
            # pids, whose release the unthrottle pass below owns.
            for pid in list(self._tracks):
                if pid not in offenders and pid not in self._throttled:
                    del self._tracks[pid]
        else:
            for pid in list(self._tracks):
                if pid not in self._throttled:
                    del self._tracks[pid]

        # Release pass: pressure cleared, the process died, or it
        # stopped offending for a full 30 seconds.
        for pid in list(self._throttled):
            p = by_pid.get(pid)
            if p is None:
                self._throttled.pop(pid, None)
                self._tracks.pop(pid, None)
                continue
            if self._pressure == "ok":
                self._unthrottle(pid, "pressure cleared")
            elif now - self._throttled[pid].get("last_offense", now) >= 30:
                self._unthrottle(pid, "it stopped offending for 30 seconds")

    # -- threads ------------------------------------------------------------

    def _tick(self):
        now = time.time()
        settings = self.settings()
        self._enabled = bool(settings["enabled"])
        procs = self._read_processes(now)
        self._free_mb = self._mem_available_mb()
        generating = self._is_generating()
        self._generating = generating
        llama_pids = set(self._llamafile_pids())
        self._llama_rss_mb = sum(p["rssMb"] for p in procs if p["pid"] in llama_pids)

        reserve = float(settings["reserveMb"])
        if generating:
            tight_below, critical_below = reserve * 2.0, reserve * 1.25
        else:
            tight_below, critical_below = reserve * 1.5, reserve
        if self._free_mb < critical_below:
            pressure = "critical"
        elif self._free_mb < tight_below:
            pressure = "tight"
        else:
            pressure = "ok"
        if pressure != self._pressure:
            old, self._pressure = self._pressure, pressure
            self._log_event(
                "pressure",
                "Pressure %s -> %s: %.0f MB free, reserve %d MB%s."
                % (old, pressure, self._free_mb, settings["reserveMb"],
                   ", generation in flight" if generating else ""))
        self._procs = procs
        self._last_tick = now

        # Learning: who is present, and who burns CPU mid-generation.
        seen_names = set()
        with self._lock:
            for p in procs:
                if p["name"] in seen_names:
                    continue
                seen_names.add(p["name"])
                row = self._stat_row(p["name"])
                row["seen"] += 1
                row["lastSeen"] = now
                self._stats_dirty = True
                if generating and p["cpu"] >= EXPOSURE_CPU_PERCENT:
                    row["genExposureTicks"] += 1
                    self._gen_exposure[p["name"]] = self._gen_exposure.get(p["name"], 0) + 1

        if not self._enabled:
            for pid in list(self._throttled):
                self._unthrottle(pid, "Guardian was turned off")
            self._tracks = {}
            self._offenders_now = []
        else:
            protected = set(llama_pids)
            protected.add(self._own_pid())
            protected.add(1)
            self._ladder(settings, procs, protected, now)
        with self._lock:
            if self._stats_dirty:
                self._save_stats()

    def _sampler_loop(self):
        while not self._stop.is_set():
            try:
                self._tick()
            except Exception:
                # Exception-proof by construction: no tick failure
                # kills the thread or reaches the bridge.
                pass
            wait = self._settings.get("sampleSeconds", 2) if isinstance(self._settings, dict) else 2
            self._stop.wait(max(0.2, _as_float(wait, 2)))

    def _throttler_loop(self):
        # Duty-cycle cap: in each 100ms slice a throttled pid runs
        # for cpuCapPercent of the slice, then sleeps for the rest.
        while not self._stop.is_set():
            try:
                pids = list(self._throttled)
                if not pids:
                    self._stop.wait(0.1)
                    continue
                cap = self._settings.get("cpuCapPercent", 50) if isinstance(self._settings, dict) else 50
                cap = min(99, max(1, _as_int(cap, 50)))
                on = 0.1 * cap / 100.0
                off = 0.1 - on
                for pid in pids:
                    self._signal(pid, signal.SIGCONT)
                if self._stop.wait(on):
                    break
                # Only stop pids still throttled at this instant —
                # one released during the on-phase stays running.
                for pid in list(self._throttled):
                    self._signal(pid, signal.SIGSTOP)
                self._stop.wait(off)
            except Exception:
                self._stop.wait(0.1)

    def start(self):
        """Start the sampler + throttler threads (idempotent)."""
        if self._sampler is not None and self._sampler.is_alive():
            return True
        self._stop.clear()
        self._sampler = threading.Thread(target=self._sampler_loop, daemon=True, name="guardian-sampler")
        self._sampler.start()
        self._throttler = threading.Thread(target=self._throttler_loop, daemon=True, name="guardian-throttler")
        self._throttler.start()
        return True

    def stop(self):
        """Stop both threads and release every throttled process."""
        self._stop.set()
        for pid in list(self._throttled):
            try:
                self._unthrottle(pid, "Guardian is stopping")
            except Exception:
                self._signal(pid, signal.SIGCONT)
        for t in (self._sampler, self._throttler):
            try:
                if t is not None and t.is_alive() and t is not threading.current_thread():
                    t.join(timeout=2)
            except Exception:
                pass

    # -- read surfaces ------------------------------------------------------

    def state(self):
        """The Guardian face's whole world, as one JSON-ready dict."""
        if self._last_tick == 0:
            try:
                self._tick()
            except Exception:
                pass
        settings = self.settings()
        mesh = self._mesh()
        top = sorted(self._procs, key=lambda p: (p["cpu"], p["rssMb"]), reverse=True)[:8]
        with self._lock:
            rows = []
            for name, row in self._stats.items():
                r = dict(row)
                r["name"] = name
                rows.append(r)
            events = list(self._events)
        rows.sort(key=lambda r: (-r.get("collisions", 0), -r.get("warns", 0), -r.get("kills", 0), r["name"]))
        return {
            "enabled": bool(settings["enabled"]),
            "pressure": self._pressure,
            "freeMb": int(round(self._free_mb)),
            "reserveMb": settings["reserveMb"],
            "llamafileRssMb": round(float(self._llama_rss_mb), 1),
            "generating": bool(self._generating),
            "mesh": mesh,
            "top": [{
                "pid": p["pid"],
                "name": p["name"],
                "cpu": p["cpu"],
                "rssMb": round(float(p["rssMb"]), 1),
                "ours": bool(p["ours"]),
                "throttled": p["pid"] in self._throttled,
            } for p in top],
            "offenders": rows[:10],
            "expendable": list(settings["expendable"]),
            "settings": settings,
            "log": events[-20:],
        }

    def context_block(self):
        """A <=~110-word brief for chat injection."""
        try:
            st = self.state()
        except Exception:
            return "Guardian: state unavailable right now."
        notable = [e for e in st["log"] if e.get("kind") in ("warn", "throttle", "kill", "unthrottle")]
        offenders = self._offenders_now
        if st["pressure"] == "ok" and not offenders and not notable:
            return ("Guardian: all clear — %d MB free (reserve %d MB), no process is crowding Navi."
                    % (st["freeMb"], st["reserveMb"]))
        parts = ["Guardian: pressure %s — %d MB free, reserve %d MB; llamafile using %s MB%s."
                 % (st["pressure"], st["freeMb"], st["reserveMb"], st["llamafileRssMb"],
                    ", generating now" if st["generating"] else "")]
        if offenders:
            desc = []
            for p in offenders[:2]:
                desc.append("%s (pid %d, %.0f%% CPU, %.0f MB)" % (p["name"], p["pid"], p["cpu"], p["rssMb"]))
            parts.append("Top offenders: " + "; ".join(desc) + ".")
        elif st["offenders"]:
            desc = []
            for r in st["offenders"][:2]:
                if r.get("collisions") or r.get("warns"):
                    desc.append("%s (%d collisions, %d warns)" % (r["name"], r.get("collisions", 0), r.get("warns", 0)))
            if desc:
                parts.append("Known offenders: " + "; ".join(desc) + ".")
        if notable:
            recent = []
            for e in notable[-3:]:
                recent.append(str(e.get("text") or ""))
            if recent:
                parts.append("Recent: " + " ".join(recent))
        text = " ".join(parts)
        # Keep to the ~110-word budget: drop recent events first.
        while len(text.split()) > 110 and len(parts) > 1:
            parts.pop()
            text = " ".join(parts)
        if len(text.split()) > 110:
            text = " ".join(text.split()[:110])
        return text
