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
import json
import os
import re
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
    if _port_answers_expected(port, tgt_seq):
        return (True, None, "")
    holder = _port_holder_pid(port)
    if holder is None:
        try:
            sock = socket.create_connection(("127.0.0.1", port), timeout=2)
            sock.close()
            return (False, None,
                    "something is listening on the port but its process could not be identified")
        except Exception:
            return (True, None, "")
    cmd = _pid_cmdline(holder)
    desc = "process " + str(holder) + ((" (" + cmd + ")") if cmd else "")
    owned = ("bridge.py" in cmd) and (_pid_cwd(holder) == os.path.realpath(root))
    if not owned:
        return (False, holder, desc + " — not this install's bridge, so it was not touched")
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
            return (True, holder, desc)
        time.sleep(0.5)
    try:
        os.kill(holder, signal.SIGKILL)
    except Exception:
        pass
    deadline = time.time() + 10
    while time.time() < deadline:
        if _pid_gone(holder) and _port_holder_pid(port) is None:
            trace("wedge-clear", "holder gone after SIGKILL; the port is free")
            return (True, holder, desc)
        time.sleep(0.5)
    return (False, holder, desc)


def _install_log_last_step(log_path):
    # Issue #104: the installer's own step banners ("==> ...")
    # name its steps; the last banner in the log is the step the
    # run had reached when it failed — the tail step a nonzero
    # exit is reported with when the build itself landed.
    try:
        with open(log_path, "rb") as f:
            text = f.read().decode("utf-8", "replace")
    except Exception:
        return "an unnamed step"
    last = ""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("==>"):
            last = line.lstrip("=> ").strip()
    return last or "an unnamed step"


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
    try:
        with open(job["installLog"], "wb") as log:
            proc = subprocess.run(
                ["bash", os.path.join(pkg_dir, "install.sh"),
                 "--startup", startup, "--voice", voice,
                 "--dir", root],
                cwd=pkg_dir, env=env, stdout=log,
                stderr=subprocess.STDOUT, timeout=3000)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        why = "the installer did not finish within 50 minutes"
    except Exception as e:
        why = str(e)
    trace("installer-exit",
          "code " + str(code) + ((", " + why) if why else ""))

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
