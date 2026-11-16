#!/usr/bin/env python3
# Apex updater apply helper — written by bridge.py into
# updates/<tag>/ and run detached (its own session), so it
# outlives the bridge it replaces. It runs the staged installer
# (never --fresh), relaunches the app through start.sh, and
# records the outcome in config/update-result.json — the record
# the Updater panel reads its confirmation (or its failure and
# fallback) from. Stdlib only, like the bridge.
#
# Build 6 — the helper can no longer die traceless. The Build 4
# round-trip gate caught it dying silently: the installer ran
# through to "Done.", then nothing — apply.log 0 bytes, no
# relaunch log, the record frozen at working/installing, no
# bridge relaunched. The old helper's only diary was the record
# itself, it wrote the record only at step boundaries, it had
# no top-level guard, no signal handlers, and it printed
# nothing — so any death between two writes (a signal above
# all: an uncaught Python exception would at least have left a
# traceback in apply.log, and apply.log was empty) left no
# evidence at all. Now, from its first instruction, the helper
# keeps a step log — apply-trace.log beside the job file, its
# path carried on the apply record — and writes every step
# boundary, a 30-second heartbeat while it works, every signal
# it is handed, and every exception into that log and onto the
# record (state/step/updatedAt) as it happens. A top-level
# guard turns any Python-level failure into a failed record
# naming the step and the reason before exiting, and mirrors
# the traceback to stderr so apply.log is never 0 bytes on a
# death words could have described. Signal handlers do the
# same for SIGTERM, SIGINT and SIGHUP. The one death no
# in-process guard can survive — SIGKILL, the kernel OOM
# killer, power loss — still leaves the step log ending at the
# last completed step, and the bridge's apply watchdog closes
# a record whose helper is gone as failed at that step,
# quoting the log's last line, instead of leaving it frozen
# at working/installing forever.
#
# v0.4.3e (#237) — the stage comes home. The v0.4.2e field
# pull named the remaining updater wounds: the installer's
# own output and the staged package both lived in the stage
# folder inside the tree the installer's swap parked, so
# the paths the failure surface printed (apply-install.log
# for the diagnose command, the package folder for the
# manual fallback) did not exist in the live tree — and,
# found by the same bake, the installer itself died after
# the swap when it recomputed its own folder's path (fixed
# in install.sh). This helper now holds a copy of the staged
# package beside the install root while the installer runs,
# keeps the install log's handle open across the swap, and
# — before any verdict or record close — brings the stage
# home: the log written to the live path the diagnose
# command names, the package restored to the folder the
# fallback command points at. It also fails the record on
# the installer's owed-but-missing line: a shell build that
# was owed (the sources changed) and produced no window is
# a missing window, not the designed browser fallback.
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
import urllib.request

STATE = {"step": "starting", "job": None, "env": None,
         "trace_path": None, "result_path": None,
         "stop_beat": False}


def _stamp():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def trace(event, detail=""):
    # The step log: append-only, flushed and fsync'd per line,
    # and never allowed to raise — a helper that dies because
    # its own diary failed would be the old bug in a new coat.
    path = STATE.get("trace_path")
    if not path:
        return
    try:
        line = _stamp() + " [" + str(STATE.get("step")) + "] " + event
        if detail:
            line += " — " + str(detail)
        # The stage folder rides inside the tree the installer
        # swaps: after a same-home install it sits parked with
        # the previous tree, and the diary must not go silent
        # at exactly the steps (relaunch, confirmation) it
        # exists to record. Recreate the folder and write on.
        _tdir = os.path.dirname(path)
        if _tdir:
            os.makedirs(_tdir, exist_ok=True)
        with open(path, "a") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        pass


def write_result(patch):
    # The apply record: read-modify-write like always, now
    # stamped with the current step and a freshness time on
    # EVERY write, so the panel — and the bridge's apply
    # watchdog — can always tell a live helper from a dead
    # one. Never raises: a failed record write is traced and
    # retried once, and the step log still carries what the
    # record could not.
    job = STATE.get("job") or {}
    result_path = STATE.get("result_path") or job.get("resultPath")
    if not result_path:
        return
    patch = dict(patch)
    if "step" in patch:
        STATE["step"] = patch["step"]
    patch.setdefault("step", STATE.get("step"))
    patch["updatedAt"] = _stamp()
    patch["updatedEpoch"] = time.time()
    patch["helperStep"] = STATE.get("step")
    if job.get("traceLog"):
        patch["traceLog"] = job["traceLog"]
    for attempt in (1, 2):
        try:
            rec = {}
            try:
                with open(result_path) as f:
                    rec = json.load(f)
                if not isinstance(rec, dict):
                    rec = {}
            except Exception:
                rec = {}
            rec.update(patch)
            # v0.3.0e Build 2 (#208): a record must never argue
            # with itself. The merge above only ever ADDS keys,
            # so a previous attempt's error/failedAt/tailFailure
            # survived into a later attempt that recovered to done — the
            # field record for the v0.3.0e Build 1 pull read
            # state=done while still carrying the earlier wedge
            # error and its failedAt stamp. A verdict owns its
            # record: done clears the failure fields outright,
            # and a fresh working attempt clears a previous
            # attempt's, so what the panel reads is always THIS
            # attempt's truth.
            if patch.get("state") == "done":
                rec.pop("error", None)
                rec.pop("failedAt", None)
                rec.pop("tailFailure", None)
            elif patch.get("state") == "working":
                rec.pop("error", None)
                rec.pop("failedAt", None)
                rec.pop("tailFailure", None)
                rec.pop("tailFailure", None)
            tmp = result_path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(rec, f)
            os.replace(tmp, result_path)
            trace("record",
                  "state=" + str(rec.get("state"))
                  + " step=" + str(rec.get("step")))
            return
        except Exception as e:
            trace("record-write-failed",
                  "attempt " + str(attempt) + ": " + str(e))


def fail(step, error):
    STATE["step"] = step
    job = STATE.get("job") or {}
    write_result({
        "state": "failed", "step": step, "error": error,
        "stagedDir": job.get("pkgDir", ""),
        "command": job.get("command", ""),
        "failedAt": _stamp(),
    })


def _heartbeat():
    # While the helper lives it beats every 30 seconds into the
    # step log, naming the step it is on. A log whose beats stop
    # mid-step is a killed helper; a log still beating at one
    # step is a blocked one — the field can finally tell those
    # two deaths apart, which the frozen Build 4 record could
    # not.
    while not STATE.get("stop_beat"):
        time.sleep(30)
        if STATE.get("stop_beat"):
            break
        trace("heartbeat", "still working")


def _on_signal(signum, frame):
    # SIGTERM / SIGINT / SIGHUP get words before the exit: the
    # step log and the record both name the signal and the step
    # it interrupted, so a helper stopped from outside is a
    # recorded failure, never a silent freeze. (SIGKILL cannot
    # be handled by any process — the step log's last line and
    # the bridge's apply watchdog cover that death.)
    name = "signal " + str(signum)
    try:
        name = signal.Signals(signum).name
    except Exception:
        pass
    trace("signal", name + " received — recording the failure and exiting")
    job = STATE.get("job") or {}
    try:
        write_result({
            "state": "failed", "step": STATE.get("step"),
            "error": (
                "The apply helper was stopped by " + name
                + " at the " + str(STATE.get("step")) + " step, "
                "so the update is not confirmed. Its step log "
                "(apply-trace.log, beside the staged package) "
                "shows the last step it completed. The staged "
                "package is still in place — the manual fallback "
                "below finishes the job by hand."),
            "stagedDir": job.get("pkgDir", ""),
            "command": job.get("command", ""),
            "failedAt": _stamp(),
        })
    except Exception:
        pass
    os._exit(128 + signum)


def version_tuple(raw):
    text = str(raw or "").strip().lower()
    if text.startswith("v"):
        text = text[1:]
    text = text.split("-")[0].split("+")[0]
    parts = []
    for piece in text.split("."):
        digits = ""
        for ch in piece:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def tuples_equal(a, b):
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)) == b + (0,) * (width - len(b))


def read_installed_version(root):
    # The VERSION file at the install root, parsed the way the
    # bridge parses it: (number, status).
    try:
        with open(os.path.join(root, "VERSION")) as f:
            text = f.read().strip()
    except Exception:
        return "", "stable"
    if not text:
        return "", "stable"
    raw = text.splitlines()[0].strip()
    status = "stable"
    low = raw.lower()
    for word in ("edge", "beta", "alpha"):
        if low.endswith(" " + word) or low.endswith("-" + word):
            status = "edge" if word == "alpha" else word
            raw = raw[: -(len(word) + 1)]
            break
    parts = raw.split()
    token = parts[0] if parts else ""
    for word in ("edge", "alpha", "beta", "stable"):
        if token.lower().endswith("-" + word):
            token = token[: -(len(word) + 1)]
            break
    return token, status


def read_installed_build_seq(root):
    # The Edge build sequence baked into the bridge.py at the
    # install root (Build 4): the on-disk half of the identity a
    # same-version refresh has to prove, beside the VERSION
    # file's number — which a refresh deliberately does not
    # change. None when the file or the sequence cannot be read
    # (a bridge from before build sequences existed).
    try:
        with open(os.path.join(root, "bridge.py"), "rb") as f:
            m = re.search(
                rb"SHIPPED_BUILD_SEQ\s*=\s*([0-9]+)", f.read())
        if m:
            return int(m.group(1))
    except Exception:
        pass
    return None


def _shell_window_state(root):
    # v0.4.2e (#233): the apply's own verdict on the installed
    # standalone window, read from DISK after the installer
    # exits — never from the installer's exit code. Returns
    # (state, reason):
    #   "ok"      — the binary's build stamp covers the
    #               installed shell sources, or no binary
    #               stands beside start.sh at all (the
    #               designed browser-fallback installs retire
    #               theirs, and the launcher falls back
    #               without complaint).
    #   "stale"   — a binary stands there whose stamp does not
    #               cover the installed sources: exactly the
    #               state start.sh refuses at the next launch,
    #               and the state v0.4.1e's pull produced while
    #               reporting success.
    #   "unknown" — the sources cannot be hashed here, so
    #               nothing can be proven either way. Named in
    #               the trace, never silently passed, never
    #               failed on suspicion.
    # The hash is the installer's own pipeline (shell_sources_
    # hash in install.sh): sha256sum of the source files, the
    # listing hashed again — replicated call for call so the
    # two can never drift into different answers.
    shell_dir = os.path.join(root, "shell")
    binary = os.path.join(root, "navi-apex-shell")
    if not os.path.isfile(binary):
        return "ok", ""
    files = ["Cargo.toml", "build.rs", "src/main.rs",
             "tauri.conf.json"]
    if os.path.isfile(os.path.join(shell_dir, "icons", "icon.png")):
        files.append("icons/icon.png")
    files.append("README.md")
    for f in files:
        if not os.path.isfile(os.path.join(shell_dir, f)):
            return "unknown", ("the installed shell sources are "
                               "incomplete (" + f + " is missing), "
                               "so the window's build stamp cannot "
                               "be verified")
    try:
        p1 = subprocess.run(["sha256sum"] + files, cwd=shell_dir,
                            capture_output=True, text=True,
                            timeout=60)
        if p1.returncode != 0 or not p1.stdout:
            return "unknown", ("sha256sum could not hash the "
                               "installed shell sources")
        p2 = subprocess.run(["sha256sum"], input=p1.stdout,
                            capture_output=True, text=True,
                            timeout=60)
        parts = (p2.stdout or "").split()
        digest = parts[0] if p2.returncode == 0 and parts else ""
    except Exception as e:
        return "unknown", ("the shell sources could not be "
                           "hashed here: " + str(e))
    if not digest:
        return "unknown", ("the shell sources could not be "
                           "hashed here")
    stamp = ""
    try:
        with open(os.path.join(root, "navi-apex-shell.stamp")) as f:
            stamp = f.read().strip()
    except Exception:
        stamp = ""
    if not stamp:
        return "stale", ("the window binary beside start.sh "
                         "carries no build stamp "
                         "(navi-apex-shell.stamp is missing), so "
                         "the launcher will refuse it as "
                         "unverifiable and open the browser "
                         "instead")
    if stamp != digest:
        return "stale", ("the window binary beside start.sh was "
                         "built from older shell sources — its "
                         "build stamp does not cover the shell "
                         "sources this update installed, so the "
                         "launcher will refuse it and open the "
                         "browser instead")
    return "ok", ""


def _pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _pid_gone(pid):
    # Gone = no such process, or a zombie: a zombie holds no
    # sockets (the kernel closed them at death) and its parent
    # reaps it in its own time.
    if not pid:
        return True
    if not _pid_alive(pid):
        return True
    try:
        with open("/proc/" + str(pid) + "/stat", "rb") as f:
            parts = f.read().rsplit(b")", 1)
        state = parts[1].split()[0].decode("utf-8", "replace") if len(parts) > 1 else ""
        return state == "Z"
    except Exception:
        return False


def _pid_cmdline(pid):
    try:
        with open("/proc/" + str(pid) + "/cmdline", "rb") as f:
            raw = f.read()
        return " ".join(part.decode("utf-8", "replace") for part in raw.split(bytes([0]))).strip()
    except Exception:
        return ""


def _pid_cwd(pid):
    try:
        return os.path.realpath(os.readlink("/proc/" + str(pid) + "/cwd"))
    except Exception:
        return ""


def _port_holder_pid(port):
    # The PID holding the LISTEN socket on the port, resolved from
    # /proc alone — names a holder that answers nothing, where a
    # status probe can only shrug.
    inodes = set()
    for path in ("/proc/net/tcp", "/proc/net/tcp6"):
        try:
            with open(path) as f:
                rows = f.read().splitlines()[1:]
        except Exception:
            continue
        for row in rows:
            parts = row.split()
            if len(parts) > 9 and parts[3] == "0A":
                try:
                    if int(parts[1].rsplit(":", 1)[1], 16) == port:
                        inodes.add(parts[9])
                except Exception:
                    pass
    if not inodes:
        return None
    targets = set("socket:[" + ino + "]" for ino in inodes)
    try:
        names = os.listdir("/proc")
    except Exception:
        return None
    for name in names:
        if not name.isdigit():
            continue
        try:
            fds = os.listdir("/proc/" + name + "/fd")
        except Exception:
            continue
        for fd in fds:
            try:
                if os.readlink("/proc/" + name + "/fd/" + fd) in targets:
                    return int(name)
            except Exception:
                pass
    return None


def _port_answers_expected(port, tgt_seq):
    # True when the bridge answering on the port already reports
    # the target identity — the case where a relaunch spawn
    # failure must NOT fail the apply: the installer's own
    # relaunch (build .91) already brought the new bridge up.
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:" + str(port) + "/api/status",
            headers={"User-Agent": "navi-update-helper"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            seen = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception:
        return False
    if not isinstance(seen, dict) or seen.get("app") != "Navi: Apex":
        return False
    return tgt_seq is None or seen.get("buildSeq") == tgt_seq


def _holder_remedy(port):
    # The failure-text remedy for a held port (build .91): name
    # the holder and its exact kill command when the socket can
    # resolve it — never "launch the app again" against a wedged
    # port, the advice that stranded the field update this build
    # answers.
    holder = _port_holder_pid(port)
    if holder:
        cmd = _pid_cmdline(holder)
        return ("The port is held by process " + str(holder)
                + (" (" + cmd + ")" if cmd else "")
                + ": end it with kill -9 " + str(holder)
                + ", then run the update again — launching the app "
                "again cannot work while that process holds the port.")
    return ("If a process is holding the port, find it with lsof -i :"
            + str(port) + " and end it, then run the update again; "
            "otherwise launch the app again from its menu entry.")


def _find_install_bridge(root):
    # v0.3.0e Build 2 (#208): find THIS install's bridge by the
    # installer's own proof discipline — the pid file the bridge
    # itself writes (bridge.pid), verified against the process
    # table, and a working-directory scan for a bridge.py whose
    # cwd is the install home. Whoever supervises the bridge —
    # the systemd user unit or the desktop app (start.sh's
    # supervise loop) — the process it runs is the same shape:
    # bridge.py, cwd = install home. Returns a proven pid or
    # None. A pid counts only when BOTH proofs hold (bridge.py
    # in its command line AND its cwd the install root): the
    # same bar the socket path has always used.
    home = os.path.realpath(root)
    candidates = []
    try:
        with open(os.path.join(root, "bridge.pid")) as f:
            pid = int((f.read() or "").strip() or 0)
        if pid:
            candidates.append(pid)
    except Exception:
        pass
    try:
        for name in os.listdir("/proc"):
            if name.isdigit():
                candidates.append(int(name))
    except Exception:
        pass
    seen = set()
    for pid in candidates:
        if pid in seen or pid == os.getpid():
            continue
        seen.add(pid)
        if _pid_gone(pid):
            continue
        if "bridge.py" in _pid_cmdline(pid) and _pid_cwd(pid) == home:
            return pid
    return None


def _stop_proven_bridge(holder, port, desc):
    # The escalation both identification paths share: SIGTERM
    # (the bridge's polite exit — the installer's stop does the
    # same), wait for the process to be gone AND the port free,
    # then SIGKILL and wait again. Returns True when the port
    # is clear.
    trace("wedge-clear",
          "wedged bridge " + desc + " — escalating: SIGTERM, then SIGKILL if it holds")
    try:
        os.kill(holder, signal.SIGTERM)
    except Exception:
        pass
    deadline = time.time() + 15
    while time.time() < deadline:
        if _pid_gone(holder) and _port_holder_pid(port) is None:
            trace("wedge-clear", "holder gone after SIGTERM; the port is free")
            return True
        time.sleep(0.5)
    try:
        os.kill(holder, signal.SIGKILL)
    except Exception:
        pass
    deadline = time.time() + 10
    while time.time() < deadline:
        if _pid_gone(holder) and _port_holder_pid(port) is None:
            trace("wedge-clear", "holder gone after SIGKILL; the port is free")
            return True
        time.sleep(0.5)
    return False


def clear_wedged_bridge(root, port, tgt_seq):
    # Build .91 (issue #91): before relaunching, prove the OLD
    # bridge is actually gone — not merely that its pid file is.
    # A bridge can still hold the port while answering nothing
    # (frozen, stopped, stuck mid-work), and every relaunch
    # against it is a no-op: the new bridge cannot bind, and the
    # confirmation that follows can only report failure with a
    # remedy that cannot work. If the target build already
    # answers, there is nothing to clear; if the port is free,
    # likewise. A holder is signalled ONLY when it is provably
    # this install's bridge — bridge.py in its command line AND
    # its working directory the install root; anything else is
    # reported, never touched. Escalation mirrors the installer:
    # SIGTERM, wait for death AND a free port, SIGKILL, wait
    # again. Returns (ok, holder_pid, holder_desc).
    #
    # v0.3.0e Build 2 (#208): identification no longer rests on
    # the socket alone. The v0.3.0e Build 1 field pull wedged
    # exactly here: the port answered, the socket named no
    # readable process, and the old text declared the holder
    # unidentifiable and told the operator to kill it by hand —
    # while the holder was this install's own bridge, run by
    # the desktop app, findable the whole time by the pid file
    # and the working-directory proof the installer itself
    # uses. When the socket cannot name the holder, the helper
    # now looks the bridge up the installer's way before it
    # ever says "unidentifiable" — and when it truly cannot
    # identify anything, the failure names every proof it ran.
    if _port_answers_expected(port, tgt_seq):
        return (True, None, "")
    holder = _port_holder_pid(port)
    if holder is None:
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=2)
            sock.close()
        except Exception:
            return (True, None, "")
        found = _find_install_bridge(root)
        if found is None:
            return (False, None,
                    "something is listening on the port but its process "
                    "could not be identified — the socket named no readable "
                    "process, the install's pid file (bridge.pid) named no "
                    "live bridge, and no bridge.py process runs from this "
                    "install home")
        holder = found
        cmd = _pid_cmdline(holder)
        desc = ("process " + str(holder) + ((" (" + cmd + ")") if cmd else "")
                + " — the install's own bridge, found by its pid file / "
                "working directory after the socket named no process")
        if _stop_proven_bridge(holder, port, desc):
            return (True, holder, desc)
        return (False, holder, desc)
    cmd = _pid_cmdline(holder)
    desc = "process " + str(holder) + ((" (" + cmd + ")") if cmd else "")
    owned = ("bridge.py" in cmd) and (_pid_cwd(holder) == os.path.realpath(root))
    if not owned:
        return (False, holder, desc + " — not this install's bridge, so it was not touched")
    if _stop_proven_bridge(holder, port, desc):
        return (True, holder, desc)
    return (False, holder, desc)


def _install_log_last_step(log_path):
    # Issue #104: the installer's own step banners ("==> ...")
    # name its steps; the last banner in the log is the step the
    # run had reached when it failed — the tail step a nonzero
    # exit is reported with when the build itself landed.
    #
    # v0.3.0e Build 2 (#208): the step is NEVER "an unnamed
    # step" again — the v0.3.0e Build 1 field record carried
    # exactly that phrase as its tailFailure, a name that names
    # nothing. When no banner survives, the log's last ERROR
    # line names the failure in the installer's own words; when
    # even that is absent, the fallback names the phase plainly
    # (a post-placement closing step) instead of shrugging.
    try:
        with open(log_path, "rb") as f:
            text = f.read().decode("utf-8", "replace")
    except Exception:
        return "the installer's closing steps (its log could not be read)"
    last = ""
    last_error = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("==>") or line.startswith("== "):
            last = line.lstrip("=> ").strip()
        elif line.startswith("ERROR") or " — FAILED" in line:
            last_error = line
    if last:
        return last
    if last_error:
        return "the step that reported: " + last_error
    return "the installer's closing steps (its log names no step banner for the failure)"


def _stage_holding_dir(job):
    # The apply's insurance folder: a sibling of the install
    # root, in the installer's own sibling idiom (.apex-stage,
    # .apex-prev) — ground the installer's swap never renames.
    root = str(job.get("root") or "")
    tag = str(job.get("tagDir") or "apply")
    if not root:
        return ""
    return os.path.join(
        os.path.dirname(os.path.abspath(root)),
        ".apex-apply-stage", tag)


def _recover_stage_artifacts(job, log_handle):
    # v0.4.3e (#237): the stage comes home. The job's paths —
    # the install log, the staged package — name the stage
    # folder inside the tree the installer replaces, and the
    # swap parks that tree beside its successor (.apex-prev):
    # in the field (v0.4.2e's pull on neondrip) the parked
    # tree took the install log and the package with it, so
    # every path the failure surface printed — the diagnose
    # command's apply-install.log, the manual fallback's
    # package folder — was a path the apply had NOT left
    # behind, and the operator's own fallback cd failed with
    # "No such file or directory". The trace and relaunch
    # logs survive the swap only because their writers
    # recreate the folder; the install log and the package
    # had no such rescue. Now they do, here, before any
    # record closes:
    #   * the install log is read back through this helper's
    #     own still-open handle (an open handle survives the
    #     rename AND the installer's end-of-run deletion of
    #     the previous tree) and written to the live path the
    #     diagnose command names;
    #   * the staged package is restored to the live folder
    #     the fallback command names — from the parked tree
    #     when it stands, else from the holding copy this
    #     helper made before the installer ran.
    # A path that already stands (a no-swap apply, a parked-
    # in-place migration) is left exactly as it lies.
    # Best-effort throughout: a rescue that fails is traced,
    # never fatal — the apply's verdict must not hinge on it.
    try:
        install_log = str(job.get("installLog") or "")
        if install_log and not os.path.isfile(install_log) \
                and log_handle is not None:
            try:
                log_handle.flush()
                log_handle.seek(0)
                data = log_handle.read()
            except Exception:
                data = b""
            if data:
                _idir = os.path.dirname(install_log)
                if _idir:
                    os.makedirs(_idir, exist_ok=True)
                with open(install_log, "wb") as f:
                    f.write(data)
                trace("stage-recovered",
                      "the install log was brought home to "
                      + install_log + " (" + str(len(data))
                      + " bytes, read back through the helper's "
                      "own handle — the swap had parked the "
                      "original with the previous tree)")
        pkg_dir = str(job.get("pkgDir") or "")
        if pkg_dir and not os.path.isdir(pkg_dir):
            src = ""
            orig_root = os.path.abspath(str(job.get("root") or ""))
            if orig_root and os.path.abspath(pkg_dir).startswith(
                    orig_root + os.sep):
                parked = os.path.join(
                    os.path.dirname(orig_root), ".apex-prev") \
                    + os.path.abspath(pkg_dir)[len(orig_root):]
                if os.path.isdir(parked):
                    src = parked
            if not src:
                held = os.path.join(
                    _stage_holding_dir(job), "package")
                if held and os.path.isdir(held):
                    src = held
            if src:
                _pdir = os.path.dirname(pkg_dir)
                if _pdir:
                    os.makedirs(_pdir, exist_ok=True)
                shutil.copytree(src, pkg_dir)
                trace("stage-recovered",
                      "the staged package was restored to "
                      + pkg_dir + " from " + src
                      + " — the manual fallback's folder stands "
                      "where the fallback command points")
            else:
                trace("stage-recovery-missed",
                      "no surviving copy of the staged package "
                      "was found to restore to " + pkg_dir)
    except Exception as e:
        trace("stage-recovery-failed", str(e))
    # The holding copy has served either way; a finished
    # apply leaves no litter beside the install root.
    try:
        held_dir = _stage_holding_dir(job)
        if held_dir and os.path.isdir(held_dir):
            shutil.rmtree(held_dir, ignore_errors=True)
            try:
                os.rmdir(os.path.dirname(held_dir))
            except Exception:
                pass
    except Exception:
        pass


def version_label(number, status):
    return "v" + number + (
        "e" if status in ("edge", "alpha") else
        "b" if status == "beta" else "")


def main():
    job_path = sys.argv[1] if len(sys.argv) > 1 else ""
    if job_path:
        STATE["trace_path"] = os.path.join(
            os.path.dirname(os.path.abspath(job_path)),
            "apply-trace.log")
    trace("helper-start",
          "pid " + str(os.getpid()) + ", job " + (job_path or "(none)"))
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        try:
            signal.signal(sig, _on_signal)
        except Exception as e:
            trace("signal-handler-skipped", str(e))
    beat = threading.Thread(target=_heartbeat, daemon=True)
    beat.start()
    with open(job_path) as f:
        job = json.load(f)
    STATE["job"] = job
    if job.get("traceLog"):
        STATE["trace_path"] = job["traceLog"]
    root = job["root"]
    STATE["result_path"] = job["resultPath"]
    pkg_dir = job["pkgDir"]
    trace("job-loaded",
          "target " + str(job.get("targetLabel"))
          + ", target build " + str(job.get("targetBuildSeq")))
    # v0.4.3e (#237): before the installer runs, the staged
    # package is copied to the holding folder beside the
    # install root (see _stage_holding_dir) — the one copy of
    # the package the installer's swap and its end-of-run
    # cleanup can never take, so _recover_stage_artifacts
    # can always put the manual fallback's folder back where
    # the fallback command points.
    try:
        _held = _stage_holding_dir(job)
        if _held and os.path.isdir(pkg_dir):
            _held_pkg = os.path.join(_held, "package")
            if os.path.isdir(_held_pkg):
                shutil.rmtree(_held_pkg, ignore_errors=True)
            os.makedirs(_held, exist_ok=True)
            shutil.copytree(pkg_dir, _held_pkg)
            trace("stage-held",
                  "the staged package is held at " + _held_pkg
                  + " while the installer runs")
    except Exception as e:
        trace("stage-hold-failed", str(e))

    # v0.3.0e Build 1 (#205): takeover mode. When the staged
    # package's bootstrap spawned this helper, it takes an apply
    # over from the helper the RUNNING (older) build started:
    # the installer that old helper ran handed off and exited
    # instead of installing. Arm first — the marker file is what
    # the handing-off installer waits for — then wait for the
    # old helper to finish its own bookkeeping and die. Two
    # helpers never work the same apply at once, and this one
    # signals nobody: it only ever waits. (The invariant is
    # untouched: no step of an apply signals any process in its
    # own ancestry — a predecessor is not an ancestor.)
    _wait_pid = job.get("takeoverWaitPid")
    if _wait_pid:
        trace("takeover-armed",
              "the incoming build's helper takes this apply over "
              "from helper pid " + str(_wait_pid)
              + " — the old helper is never signalled; it is "
              "waited out")
        _marker = job.get("takeoverMarker")
        if _marker:
            try:
                with open(_marker, "w") as _mf:
                    _mf.write(str(os.getpid()))
            except Exception:
                pass
        _t0 = time.time()
        while not _pid_gone(int(_wait_pid)) and time.time() - _t0 < 180:
            time.sleep(0.5)
        trace("takeover-proceed",
              "the previous helper is gone (waited "
              + str(int(time.time() - _t0)) + "s); the apply "
              "continues under the incoming build's machinery")

    env = dict(os.environ)
    env["NAVI_HOME"] = root
    if job.get("bootstrap"):
        # The installer checks this before its own handoff: an
        # apply the package's machinery already governs must not
        # hand off a second time.
        env["APEX_APPLY_BOOTSTRAPPED"] = "1"
    STATE["env"] = env

    def relaunch():
        try:
            # The relaunch log lives in the stage folder, which
            # the installer's swap parks with the previous tree
            # on a same-home apply: without its folder recreated
            # this open fails, the relaunch never starts, and a
            # landed update records itself unconfirmed (the
            # trace goes silent the same way — trace() recreates
            # its own folder for the same reason).
            _rdir = os.path.dirname(job["relaunchLog"])
            if _rdir:
                os.makedirs(_rdir, exist_ok=True)
            log = open(job["relaunchLog"], "ab")
            subprocess.Popen(
                ["bash", os.path.join(root, "start.sh")],
                cwd=root, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT,
                start_new_session=True, close_fds=True)
            trace("relaunch", "start.sh spawned")
            return ""
        except Exception as e:
            trace("relaunch-failed", str(e))
            return str(e)

    # Give the bridge a moment to answer the apply request and
    # the panel a moment to paint the installing step before the
    # installer stops the bridge.
    time.sleep(2)
    STATE["step"] = "installing"
    write_result({"state": "working", "step": "installing"})
    startup = "boot" if job.get("startup") == "on-boot" else "launch"
    # The install's known answers ride as flags (build .84, issue
    # #75): this run is detached and terminal-less by design, so
    # the installer is never left to ask a question nobody can
    # answer — startup from the config (above), voice from whether
    # her venv is on disk, both recorded on the job by the bridge
    # when it staged the update.
    voice = "yes" if job.get("voice") == "yes" else "no"
    code = None
    why = ""
    trace("installer-start",
          "bash install.sh --startup " + startup + " --voice " + voice)
    # v0.4.3e (#237): the install log's handle stays OPEN
    # after the installer exits — it is the rescue's source
    # (see _recover_stage_artifacts): the swap renames the
    # tree the log file sits in, and a completed installer
    # deletes that tree, but an open handle reads the content
    # back through both.
    _log_handle = None
    try:
        # "a+b", not a write-only mode: the recovery below
        # reads the log back through this same handle after
        # the swap, and a write-only handle cannot be read.
        _log_handle = open(job["installLog"], "a+b")
        proc = subprocess.run(
            ["bash", os.path.join(pkg_dir, "install.sh"),
             "--startup", startup, "--voice", voice,
             "--dir", root],
            cwd=pkg_dir, env=env, stdout=_log_handle,
            stderr=subprocess.STDOUT, timeout=3000)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        why = "the installer did not finish within 50 minutes"
    except Exception as e:
        why = str(e)
    trace("installer-exit",
          "code " + str(code) + ((", " + why) if why else ""))
    # v0.3.0e Build 2 (#208): the bootstrap handoff's verdict,
    # quoted into the trace. The Build 1 installer gate decided
    # in silence — a declined handoff left no named trace in
    # the record, the install log, or here, so the field could
    # not say afterwards WHY the incoming build's machinery did
    # not govern its own pull. The installer now writes its
    # verdict (go / no / refused, with the reason) beside the
    # job; the helper quotes it into the step log, the diary
    # the operator actually reads.
    try:
        _verdict_path = os.path.join(
            os.path.dirname(os.path.abspath(job_path)),
            "apply-handoff-verdict.json")
        with open(_verdict_path) as _vf:
            _verdict = json.load(_vf)
        trace("handoff-verdict",
              str(_verdict.get("verdict") or "?") + " — "
              + str(_verdict.get("reason") or ""))
    except Exception:
        pass

    # 0.2.0e Build 11 (#198): the homecoming adoption. When the
    # installer migrated Apex to its new home, it left a machine
    # marker in this (now parked) tree naming the new home. When
    # the new home verifiably holds THIS job's target build,
    # everything from here — the landed classification below,
    # the wedge clear, the relaunch, the confirmation, and the
    # record itself — follows the install to its new home
    # instead of reading the parked tree's old witnesses.
    try:
        with open(os.path.join(root, ".apex-migration.json")) as _mf:
            _mig = json.load(_mf)
        _new_root = str(_mig.get("to") or "")
        if (_new_root and _new_root != root
                and os.path.isfile(os.path.join(_new_root, "bridge.py"))
                and read_installed_build_seq(_new_root)
                == job.get("targetBuildSeq")):
            trace("migration-adopted",
                  "the installer moved Apex to " + _new_root
                  + " — relaunch, confirmation and the record follow it there")
            root = _new_root
            STATE["result_path"] = os.path.join(
                root, "config", "update-result.json")
            env["NAVI_HOME"] = root
    except Exception:
        pass

    # v0.4.3e (#237): the stage comes home BEFORE any verdict
    # or record close below — the shell verdict's failure text
    # and every later failure text name the install log and
    # the staged package at their live paths, so those paths
    # are made true first (see _recover_stage_artifacts).
    _recover_stage_artifacts(job, _log_handle)
    if _log_handle is not None:
        try:
            _log_handle.close()
        except Exception:
            pass
        _log_handle = None

    # v0.4.2e (#233): the shell-window verdict, read from disk
    # (see _shell_window_state). An apply is NOT confirmed
    # while the installed window binary is one the launcher
    # will refuse: v0.4.1e's pull laid new shell sources over a
    # binary built from older ones, the install reported
    # success, and the operator learned it at the next launch,
    # from a launcher log. A stale verdict fails the apply
    # HERE — in the record the panel shows, with the reason in
    # words — whatever the installer's exit code claimed.
    _shell_state, _shell_reason = _shell_window_state(root)
    trace("shell-window",
          _shell_state
          + ((" — " + _shell_reason) if _shell_reason else ""))
    if _shell_state == "stale":
        fail("install",
             "The update installed, but her standalone window "
             "did not come with it: " + _shell_reason + ". The "
             "update is not confirmed. The installer's shell "
             "build log is at shell/shell-build.log in the "
             "install folder — the Rust toolchain and the "
             "WebKitGTK development packages are the usual "
             "causes. Fix the cause and run the update again, "
             "or use the manual fallback below, which re-runs "
             "its installer by hand.")
        relaunch()
        STATE["stop_beat"] = True
        return

    # v0.4.3e (#237): the owed-but-missing window. The disk
    # verdict above reads "ok" when no binary stands beside
    # start.sh — the designed browser fallback — but on an
    # update whose shell sources CHANGED, a build was owed,
    # and a build that failed retires the stale binary into
    # exactly that no-binary shape. The installer names the
    # distinction in its own log (SHELL-WINDOW:
    # owed-but-missing); when it does, the absence is a
    # missing window, not a fallback, and the apply fails on
    # it here the same way a stale verdict does.
    if _shell_state == "ok":
        _owed_missing = False
        try:
            with open(job["installLog"], "rb") as _lf:
                _owed_missing = (
                    b"SHELL-WINDOW: owed-but-missing" in _lf.read())
        except Exception:
            _owed_missing = False
        if _owed_missing:
            trace("shell-window",
                  "owed-but-missing — the shell sources changed "
                  "with this update and the build produced no "
                  "window; the apply fails on it in its record")
            fail("install",
                 "The update installed, but her standalone window "
                 "did not come with it: the shell sources changed "
                 "with this update and the build did not produce "
                 "a window — the previous binary was retired "
                 "rather than left standing stale. The update is "
                 "not confirmed. The installer's shell build log "
                 "is at shell/shell-build.log in the install "
                 "folder — the Rust toolchain and the WebKitGTK "
                 "development packages are the usual causes. Fix "
                 "the cause and run the update again, or use the "
                 "manual fallback below, which re-runs its "
                 "installer by hand.")
            relaunch()
            STATE["stop_beat"] = True
            return

    tail_failure = ""
    if code != 0:
        # Issue #104 (Build 6): a nonzero exit is not the whole
        # story, in either direction. Classify before reporting:
        # (2) the exit was nonzero BUT the target build is already
        # installed on disk — the installer's version flip is its
        # final act (Build 6), so a matching VERSION file and a
        # matching baked-in build sequence together prove the new
        # build landed and only a tail step failed. That is NOT
        # the manual-fallback failure: fall through to the normal
        # restart + confirmation with the tail failure recorded,
        # and let confirmation have the last word. (3) Anything
        # else is the original failure, unchanged.
        tgt_seq_chk = job.get("targetBuildSeq")
        chk_number, _chk_status = read_installed_version(root)
        chk_seq = read_installed_build_seq(root)
        installed_ok = bool(
            chk_number
            and tuples_equal(
                version_tuple(chk_number), tuple(job["targetTuple"]))
            and (tgt_seq_chk is None or chk_seq == tgt_seq_chk))
        if installed_ok:
            tail_failure = _install_log_last_step(job["installLog"])
            trace("installer-tail-failure",
                  "exit " + str(code) + " but the target build is "
                  "installed (version " + chk_number + ", buildSeq "
                  + str(chk_seq) + "); tail step: " + tail_failure)
        else:
            reason = why or ("it exited with code " + str(code))
            fail("install",
                 "Installing the update failed — " + reason + ". The "
                 "installer's own output is in updates/" + job["tagDir"]
                 + "/apply-install.log. Nothing is confirmed updated: "
                 "the app is being relaunched as it lies, and the "
                 "staged package is still in place — the manual "
                 "fallback below finishes the job by hand.")
            relaunch()
            STATE["stop_beat"] = True
            return

    # The installer's DHD prerequisite step is a named ladder
    # step of its own: its summary line is read back from the
    # install log the helper just captured, so the panel shows
    # the step because the installer really ran it — never as a
    # file-copy shortcut or a relabelled install phase.
    dhd_prereq_detail = ""
    try:
        with open(job["installLog"], "rb") as log:
            install_text = log.read().decode("utf-8", "replace")
        for line in install_text.splitlines():
            if line.startswith("DHD-PREREQS:"):
                dhd_prereq_detail = line.split(":", 1)[1].strip()
                break
    except Exception:
        dhd_prereq_detail = ""
    trace("dhd-prereqs",
          dhd_prereq_detail or "no DHD-PREREQS line in the install log")
    STATE["step"] = "dhd-prereqs"
    write_result({
        "state": "working", "step": "dhd-prereqs",
        "dhdPrereqs": dhd_prereq_detail or "This installer did not report a DHD prerequisite step.",
    })
    time.sleep(1)
    STATE["step"] = "restarting"
    write_result({"state": "working", "step": "restarting"})
    # Build .91 (issue #91): prove the old bridge is gone BEFORE
    # relaunching. A wedged holder makes every relaunch a no-op —
    # the new bridge cannot bind — and the old failure text's
    # remedy ("launch the app again") cannot work while the port
    # is held. Escalate here exactly as the installer does; if
    # the port still cannot be cleared, fail naming the holder
    # and the exact command that ends it.
    wedge_ok, wedge_pid, wedge_desc = clear_wedged_bridge(
        root, job["port"], job.get("targetBuildSeq"))
    if not wedge_ok:
        if wedge_pid:
            wedge_remedy = (
                "End it with: kill -9 " + str(wedge_pid)
                + " — then run the update again, or the manual "
                "fallback below. Launching the app again cannot "
                "work while that process holds the port.")
        else:
            wedge_remedy = (
                "Find what holds it with: lsof -i :" + str(job["port"])
                + " — end that process, then run the update again, "
                "or the manual fallback below. Launching the app "
                "again cannot work while the port is held.")
        fail("restart",
             "The update installed, but the old bridge could not "
             "be cleared from http://localhost:" + str(job["port"])
             + ": " + wedge_desc + ". The new bridge cannot start "
             "while the port is held, so the update is not "
             "confirmed. " + wedge_remedy
             + " The staged package is still in place.")
        STATE["stop_beat"] = True
        return
    relaunch_err = relaunch()
    if relaunch_err:
        if _port_answers_expected(job["port"], job.get("targetBuildSeq")):
            # The spawn failed but the target build is already
            # answering — the installer's own relaunch (build
            # .91) brought her up. Not a failure: fall through to
            # the confirmation loop, which will see her itself.
            trace("relaunch-skipped",
                  "spawn failed (" + relaunch_err + ") but the target build already answers")
            relaunch_err = ""
        else:
            fail("restart",
                 "The update installed, but relaunching Apex through "
                 "start.sh could not even be started (" + relaunch_err
                 + "), so the update is not confirmed. Expected "
                 + job["targetLabel"]
                 + (" Build " + str(job["targetBuildSeq"])
                    if job.get("targetBuildSeq") is not None else "")
                 + " answering on http://localhost:" + str(job["port"])
                 + "; found: no relaunch was started. The staged "
                 "package is still in place — the manual fallback "
                 "below finishes the job by hand, or launch the app "
                 "again from its menu entry.")
            STATE["stop_beat"] = True
            return
    target = tuple(job["targetTuple"])
    # Build 4: when the job names a target Build number, the
    # confirmation must observe that build answering — the
    # version number is identical on both sides of a refresh,
    # so a version-only match once certified the previous
    # build's reinstall as the new build's arrival.
    tgt_seq = job.get("targetBuildSeq")
    answered = None
    last_seen = ""
    deadline = time.time() + 300
    while time.time() < deadline:
        seen = None
        try:
            req = urllib.request.Request(
                "http://127.0.0.1:" + str(job["port"]) + "/api/status",
                headers={"User-Agent": "navi-update-helper"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                seen = json.loads(resp.read().decode("utf-8", "replace"))
        except Exception:
            seen = None
        if seen:
            last_seen = (
                "app=" + str(seen.get("app"))
                + " version=" + str(seen.get("version"))
                + " buildSeq=" + str(seen.get("buildSeq")))
        if seen and seen.get("app") == "Navi: Apex":
            if answered is None:
                trace("bridge-answered", last_seen)
            answered = seen
            if (seen.get("version")
                    and tuples_equal(
                        version_tuple(seen["version"]), target)
                    and (tgt_seq is None
                         or seen.get("buildSeq") == tgt_seq)):
                break
        time.sleep(2)
    after_number, after_status = read_installed_version(root)
    after_label = (
        version_label(after_number, after_status) if after_number else "")
    disk_seq = read_installed_build_seq(root)
    trace("confirm",
          "live: " + (last_seen or "no answer")
          + "; on disk: version=" + (after_number or "(unreadable)")
          + " buildSeq=" + str(disk_seq)
          + "; expected: " + job["targetLabel"]
          + " buildSeq=" + str(tgt_seq))
    live_ok = bool(
        answered and answered.get("version")
        and tuples_equal(version_tuple(answered["version"]), target)
        and (tgt_seq is None or answered.get("buildSeq") == tgt_seq))
    file_ok = bool(
        after_number
        and tuples_equal(version_tuple(after_number), target)
        and (tgt_seq is None or disk_seq is None
             or disk_seq == tgt_seq))
    if live_ok and file_ok:
        STATE["step"] = "done"
        write_result({
            "state": "done", "step": "done",
            **({"tailFailure": tail_failure} if tail_failure else {}),
            "afterVersion": after_number,
            "afterStatus": after_status,
            # The worker's composed to-side label when it sent
            # one (Build 3: a refresh's "Build <n>"); the label
            # read from the VERSION file otherwise — identical
            # for graduations and new versions.
            "afterLabel": job.get("afterLabel") or after_label,
            "updatedAt": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        trace("done",
              "confirmed " + str(job.get("afterLabel") or after_label))
    elif answered is None:
        fail("restart",
             "The update installed, but Apex did not answer on "
             "http://localhost:" + str(job["port"]) + " after "
             "restarting, so the update is not confirmed. Expected "
             + job["targetLabel"]
             + (" Build " + str(tgt_seq) if tgt_seq is not None else "")
             + " answering there; found: "
             + (("an answer that was not the expected bridge ("
                 + last_seen + ")")
                if last_seen else
                "no answer at all in five minutes")
             + ". "
             + _holder_remedy(job["port"])
             + " The staged package is still in place — the manual "
             "fallback below re-runs its installer by hand.")
    elif (tgt_seq is not None and disk_seq is not None
            and disk_seq != tgt_seq):
        fail("restart",
             "Apex came back after the update, but the bridge "
             "installed on disk is Build " + str(disk_seq)
             + " instead of the expected Build " + str(tgt_seq)
             + " — the update is not confirmed. The staged "
             "package is still in place — the manual fallback "
             "below finishes the job by hand.")
    elif (tgt_seq is not None and answered is not None
            and answered.get("buildSeq") is not None
            and answered.get("buildSeq") != tgt_seq):
        fail("restart",
             "Apex came back after the update, but the bridge "
             "answering reports Build "
             + str(answered.get("buildSeq"))
             + " instead of the expected Build " + str(tgt_seq)
             + " — the update is not confirmed. "
             + _holder_remedy(job["port"])
             + " The staged package is still in place — the manual "
             "fallback below finishes the job by hand.")
    else:
        fail("restart",
             "Apex came back after the update, but its VERSION "
             "file reads " + (after_label or "nothing readable")
             + " instead of the expected " + job["targetLabel"]
             + " — the update is not confirmed. The staged "
             "package is still in place — the manual fallback "
             "below finishes the job by hand.")
    STATE["stop_beat"] = True


def _guarded_main():
    # The top-level guard: any Python-level failure anywhere in
    # the apply — the job load, a record write, the relaunch,
    # the confirmation — lands in the step log with its
    # traceback, in the record as a failed state naming the
    # step it died on and the reason in words, and on stderr
    # (which the bridge points at apply.log, so that file is
    # never again 0 bytes on a death words could describe).
    try:
        main()
    except BaseException as e:
        tb = traceback.format_exc()
        trace("fatal", tb.replace("\n", " | ")[-1500:])
        try:
            print(tb, file=sys.stderr)
            sys.stderr.flush()
        except Exception:
            pass
        job = STATE.get("job") or {}
        try:
            write_result({
                "state": "failed", "step": STATE.get("step"),
                "error": (
                    "The apply helper failed at the "
                    + str(STATE.get("step")) + " step: "
                    + type(e).__name__ + ": " + str(e)
                    + " — the update is not confirmed. Its step "
                    "log (apply-trace.log, beside the staged "
                    "package) carries the full trace. The staged "
                    "package is still in place — the manual "
                    "fallback below finishes the job by hand."),
                "stagedDir": job.get("pkgDir", ""),
                "command": job.get("command", ""),
                "failedAt": _stamp(),
            })
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    _guarded_main()
