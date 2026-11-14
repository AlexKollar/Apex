#!/usr/bin/env python3
# Apex apply bootstrap (v0.3.0e Build 1, #205).
#
# The bootstrap patch, in one small file: an apply is governed
# by the INCOMING build's machinery, because a pull is executed
# end-to-end by the running build's spawner and no spawner fix
# can protect the pull that installs it (incident 22, #205).
# This script ships INSIDE the update package, beside
# apply-helper.py (the package's own helper, byte-identical to
# the one the incoming bridge embeds). It has exactly two
# callers:
#
#   1. The incoming bridge itself, when it stages a package
#      that carries this file: it runs the bootstrap, which
#      spawns the package's helper under the same spawn
#      discipline the bridge uses (a transient systemd scope
#      where one can be had, a plain own-session spawn named
#      as such where one cannot) and answers with a JSON
#      verdict.
#
#   2. The incoming package's install.sh, when an OLDER bridge's
#      helper is running it mid-apply (the transition): the
#      installer hands off — this bootstrap spawns the
#      package's helper in takeover mode (it waits, signalling
#      nobody, for the older helper to finish and die), and the
#      installer exits without installing, leaving the real
#      install to machinery the old bridge's unit stops cannot
#      reach.
#
# Usage: apply-bootstrap.py <apply-job.json> [wait-for-pid]
# Prints one JSON line: {"ok": bool, "helperPid": int|null,
# "mode": str, "note": str}. Exit code 0 iff the helper armed.
# The verdict is also written beside the job as
# apply-bootstrap-result.json.

import json
import os
import re
import shutil
import subprocess
import sys
import time


def _spawn_argv(helper_path, job_path, tag_dir):
    # The same probe discipline as the bridge's
    # _apply_helper_spawn_argv (Build 12, #201): a transient
    # scope of the helper's own where systemd-run can give one,
    # a plain own-session spawn — named honestly — where it
    # cannot. Returns (argv, mode, note).
    base = [sys.executable, helper_path, job_path]
    sd = shutil.which("systemd-run")
    if sd:
        probe = None
        try:
            probe = subprocess.run(
                [sd, "--user", "--scope", "--collect", "-q",
                 "/bin/true"],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=10)
        except Exception:
            probe = None
        if probe is not None and probe.returncode == 0:
            unit = ("apex-apply-"
                    + re.sub(r"[^0-9A-Za-z_-]+", "-",
                             str(tag_dir or "apply"))
                    + "-" + str(os.getpid()))
            argv = [sd, "--user", "--scope", "--collect", "-q",
                    "--unit=" + unit, "--"] + base
            return (argv, "systemd-run-scope",
                    "the apply helper runs in its own transient "
                    "scope (" + unit + ".scope), outside any "
                    "bridge's systemd unit — a stop of a bridge's "
                    "unit during the install cannot signal it "
                    "(#201).")
    return (base, "plain-session",
            "systemd-run could not give the apply helper a scope "
            "of its own here (not installed, or no user manager "
            "answers), so it runs plainly in its own session — "
            "the installer's ordering is this run's protection: "
            "it stops processes by proven pid and never stops "
            "the unit it may be running under (#201).")


def main():
    job_path = sys.argv[1] if len(sys.argv) > 1 else ""
    wait_pid = None
    if len(sys.argv) > 2:
        try:
            wait_pid = int(sys.argv[2])
        except Exception:
            wait_pid = None
    verdict = {"ok": False, "helperPid": None, "mode": "",
               "note": ""}
    try:
        with open(job_path) as f:
            job = json.load(f)
    except Exception as e:
        verdict["note"] = "the apply job could not be read: " + str(e)
        print(json.dumps(verdict))
        return 1
    stage_root = os.path.dirname(os.path.abspath(job_path))
    pkg_dir = str(job.get("pkgDir") or "")
    helper_path = os.path.join(pkg_dir, "apply-helper.py")
    if not os.path.isfile(helper_path):
        verdict["note"] = ("the package carries no apply-helper.py "
                           "beside apply-bootstrap.py — nothing "
                           "to govern the apply with")
        print(json.dumps(verdict))
        return 1
    # The job learns what governs it before the helper reads it:
    # the bootstrap flag (the helper marks the installer's
    # environment with it) and, on a transition, the pid of the
    # older helper the new one must wait out.
    job["bootstrap"] = True
    marker = None
    if wait_pid:
        job["takeoverWaitPid"] = wait_pid
        marker = os.path.join(stage_root, "apply-takeover.marker")
        job["takeoverMarker"] = marker
        try:
            os.remove(marker)
        except Exception:
            pass
    argv, mode, note = _spawn_argv(helper_path, job_path,
                                   job.get("tagDir"))
    job["spawnMode"] = "package-bootstrap/" + mode
    try:
        with open(job_path, "w") as f:
            json.dump(job, f)
    except Exception as e:
        verdict["note"] = "the apply job could not be updated: " + str(e)
        print(json.dumps(verdict))
        return 1
    logf = open(os.path.join(stage_root, "apply.log"), "ab")
    try:
        proc = subprocess.Popen(
            argv, cwd=stage_root, stdin=subprocess.DEVNULL,
            stdout=logf, stderr=subprocess.STDOUT,
            start_new_session=True, close_fds=True)
    finally:
        logf.close()
    verdict["helperPid"] = proc.pid
    verdict["mode"] = mode
    verdict["note"] = note
    if marker:
        # Transition: armed means the new helper has written its
        # marker — proof it is past its first instructions and
        # into the takeover wait. A helper that cannot arm is
        # stopped again, so the caller can fall back to
        # installing the ordinary way instead of stranding the
        # apply between two helpers.
        deadline = time.time() + 15
        armed = False
        while time.time() < deadline:
            if os.path.isfile(marker):
                armed = True
                break
            if proc.poll() is not None:
                break
            time.sleep(0.2)
        if not armed:
            try:
                proc.kill()
            except Exception:
                pass
            verdict["note"] = ("the package's helper did not arm "
                               "its takeover in time — the handoff "
                               "is refused and the installer "
                               "carries on itself")
            print(json.dumps(verdict))
            return 1
    verdict["ok"] = True
    try:
        with open(os.path.join(stage_root,
                               "apply-bootstrap-result.json"),
                  "w") as f:
            json.dump(verdict, f)
    except Exception:
        pass
    print(json.dumps(verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
