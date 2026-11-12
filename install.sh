#!/usr/bin/env bash
# Apex installer — Linux (reference build)
# Script-based on purpose (no graphical wizard): it downloads the Navi
# llamafile from Hugging Face, installs the app, wires up startup, and
# registers Apex in the application menu with its icon.
# The install root is /opt/navi-apex. An earlier install under
# ~/.local/share/navi is migrated as a clean break: its bridge and
# boot service are stopped and disabled, its llamafile binary is
# MOVED into /opt (never re-downloaded), its config and persona
# documents are carried across, and the old files are removed — so
# nothing from the old location can grab port 8675 at boot or answer
# the browser with a stale page.
# One installer, every major Linux family (build .70, issue #48):
# the distro family is detected up front from /etc/os-release and
# announced in plain words, and ONLY the dependency step branches
# on it — a small per-family package table (apt / dnf / pacman)
# for the same dependency set. Bazzite is its own case (immutable:
# no rpm-ostree layering, no reboot — the window build takes the
# user-space path or is skipped, said out loud), and an
# unrecognized distro is never guessed at: the system-package
# step is skipped with a warning and the core install completes.
# If a real llamafile binary is already present in the install
# location, the download (and the llamafile setup) is skipped entirely.
# --fresh reinstalls the app from scratch — everything in the install
# location is removed and reinstalled — EXCEPT the operator's own
# state: the llamafile binary, the installed chips (the whole chips/
# folder), her knowledge packs (rag-packs/), the DHD certificate
# home (config/dhd/), and the Soul/Memory
# documents are stashed before the wipe
# and restored after it, so a fresh install never costs Navi her
# chips or who she is. Her voice venv is stashed and restored too,
# and the voice step checks it: when the engines still import, the
# voice install is skipped as already set up. A first install has
# nothing to stash and creates everything fresh, as it should.
set -euo pipefail

LLAMAFILE_URL="https://huggingface.co/saintssec/navi.llamafile/resolve/main/navi.llamafile"
INSTALL_DIR="${NAVI_HOME:-/opt/navi-apex}"
OLD_DIR="$HOME/.local/share/navi"
STARTUP=""
FRESH=""

# /opt is root-owned on most systems: file operations on the install
# root go through sudo when the operator can't write there directly.
# The finished install is chown'd back to the operator — the bridge
# runs as them and writes the persona documents as them.
SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if [ -d "$INSTALL_DIR" ]; then
    [ -w "$INSTALL_DIR" ] || SUDO="sudo"
  else
    [ -w "$(dirname "$INSTALL_DIR")" ] || SUDO="sudo"
  fi
fi

VOICE=""
NO_RELAUNCH=""
while [ $# -gt 0 ]; do
  case "$1" in
    --startup) STARTUP="$2"; shift 2 ;;
    --dir) INSTALL_DIR="$2"; shift 2 ;;
    --fresh) FRESH=1; shift ;;
    --voice) VOICE="$2"; shift 2 ;;
    --no-relaunch) NO_RELAUNCH=1; shift ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done

# Is there a terminal that can actually answer a prompt? The test
# is OPENING /dev/tty, never [ -r /dev/tty ] (build .84, issue
# #75): in a shell with no controlling terminal — the app's own
# CLI shell, cron, a detached helper — the device node exists and
# reads as readable, so the old guard passed, and the read behind
# it died mid-prompt with "/dev/tty: No such device or address"
# (the v0.1.7a field failure on NeoArcadia, which cost the remote
# install its running bridge for the night). Opening the device
# in a subshell answers the real question and changes nothing.
HAVE_TTY=""
if ( : < /dev/tty ) 2>/dev/null; then
  HAVE_TTY=1
fi

# The startup mode is the operator's call, made during the install —
# there is no hard-coded default. --startup launch|boot answers it
# ahead of time (for scripted installs); otherwise the installer asks.
if [ -z "$STARTUP" ]; then
  if [ -n "$HAVE_TTY" ]; then
    echo ""
    echo "How should the navi.llamafile server start?"
    echo "  1) On app launch — starts when you open Apex, stops when it closes"
    echo "  2) At system boot — registered as a service, warm before you open the app"
    while true; do
      printf "Enter 1 or 2: "
      if ! read -r CHOICE < /dev/tty; then
        echo "" >&2
        echo "The terminal stopped answering before a choice was made." >&2
        echo "Re-run with --startup launch or --startup boot to answer ahead of time." >&2
        exit 1
      fi
      case "$CHOICE" in
        1|launch) STARTUP="launch"; break ;;
        2|boot) STARTUP="boot"; break ;;
        *) echo "Please answer 1 or 2." ;;
      esac
    done
  else
    echo "No terminal to ask about startup mode. Re-run with --startup launch or --startup boot." >&2
    exit 1
  fi
fi

case "$STARTUP" in
  launch|boot) ;;
  *) echo "--startup must be 'launch' or 'boot'" >&2; exit 1 ;;
esac

echo "==> Apex installer (Linux) — startup mode: $STARTUP"

# --- Stopping a running bridge — a proof, not a gesture (.91, #91) --
# The old stop fired one SIGTERM at the pid file's process, deleted
# the pid file whatever happened, and slept a second: a bridge that
# did not die on cue (stopped, stuck, mid-something-it-could-not-
# put-down) kept port 8675 and kept answering — nameless,
# its pid file gone — while the files under it became the new build.
# The replacement bridge could never bind, and only killing the
# stuck process by hand (or rebooting, which asks nothing) cleared
# it. The stop below FINDS the bridge three ways, waits for the
# process to be gone AND the port to be free, escalates to SIGKILL,
# and — if the port still cannot be cleared — aborts the install
# BEFORE any file is replaced, naming the holder and the exact
# command that ends it. The pid file is deleted only once the stop
# is proven; on an abort it is left exactly where it was.

# PIDs of bridge.py processes whose working directory is $1 — how a
# start.sh-launched bridge is found at all: its command line is the
# relative "python3 bridge.py", which no path pattern can match.
bridge_pids_in_dir() {
  python3 - "$1" <<'PYEOF' 2>/dev/null || true
import os, sys
try:
    root = os.path.realpath(sys.argv[1])
except Exception:
    sys.exit(0)
found = []
for name in os.listdir("/proc"):
    if not name.isdigit():
        continue
    try:
        if os.path.realpath(os.readlink("/proc/" + name + "/cwd")) != root:
            continue
        with open("/proc/" + name + "/cmdline", "rb") as f:
            raw = f.read()
        cmd = " ".join(part.decode("utf-8", "replace") for part in raw.split(bytes([0])))
        if "bridge.py" in cmd:
            found.append(name)
    except Exception:
        pass
print(" ".join(found))
PYEOF
}

# The PID holding the LISTEN socket on the bridge port, resolved
# from /proc alone (ss/lsof are not guaranteed on a fresh box), or
# nothing when the port is free.
bridge_port_holder_pid() {
  python3 - "8675" <<'PYEOF' 2>/dev/null || true
import os, sys
port = int(sys.argv[1])
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
    sys.exit(0)
targets = set()
for ino in inodes:
    targets.add("socket:[" + ino + "]")
for name in os.listdir("/proc"):
    if not name.isdigit():
        continue
    try:
        fds = os.listdir("/proc/" + name + "/fd")
    except Exception:
        continue
    for fd in fds:
        try:
            if os.readlink("/proc/" + name + "/fd/" + fd) in targets:
                print(name)
                sys.exit(0)
        except Exception:
            pass
PYEOF
}

# A process counts as gone when it no longer exists OR is a zombie:
# a zombie holds no sockets — the kernel closed them at death — and
# its parent reaps it in its own time.
bridge_pid_gone() {
  [ -n "$1" ] || return 0
  kill -0 "$1" 2>/dev/null || return 0
  local st=""
  st="$(awk '{print $3}' "/proc/$1/stat" 2>/dev/null || true)"
  [ "$st" = "Z" ]
}

# stop_bridge <dir>: stop the bridge belonging to <dir> and PROVE
# it — every candidate dead and the port free. Sets STOPPED_BRIDGE=1
# when a bridge was in fact stopped (the end of the install
# relaunches and verifies in that case). Returns 1 — the caller
# aborts — when the port cannot be cleared; in that case nothing
# has been signalled that was not this install's own bridge, the
# pid file is untouched, and the holder is named with its remedy.
STOPPED_BRIDGE=""
stop_bridge() {
  local dir="$1" pid_file="$1/bridge.pid"
  local cands="" p=""
  if [ -f "$pid_file" ]; then
    p="$(tr -dc '0-9' < "$pid_file" 2>/dev/null || true)"
    # A pid file is a claim, not a proof: the named process counts
    # only if it really is a bridge of this install — a recycled
    # pid belonging to somebody else's process is never signalled.
    if [ -n "$p" ] && [ -d "/proc/$p" ]; then
      if [ "$(readlink "/proc/$p/cwd" 2>/dev/null || true)" = "$dir" ] || grep -aq "bridge.py" "/proc/$p/cmdline" 2>/dev/null; then
        cands="$cands $p"
      fi
    fi
  fi
  for p in $(bridge_pids_in_dir "$dir"); do
    case " $cands " in *" $p "*) ;; *) cands="$cands $p" ;; esac
  done
  if [ -n "$cands" ]; then
    STOPPED_BRIDGE=1
    echo "    stopping the running bridge (pid(s):$cands) — waiting for it to be gone and port 8675 to be free"
    for p in $cands; do kill "$p" 2>/dev/null || true; done
    local waited=0 allgone="" q=""
    while [ "$waited" -lt 15 ]; do
      allgone=1
      for q in $cands; do bridge_pid_gone "$q" || allgone=""; done
      if [ -n "$allgone" ] && [ -z "$(bridge_port_holder_pid)" ]; then
        rm -f "$pid_file"
        echo "    the previous bridge is stopped and port 8675 is free"
        return 0
      fi
      sleep 1; waited=$((waited + 1))
    done
    echo "    the bridge did not stop on a polite signal — ending it by force"
    for p in $cands; do kill -9 "$p" 2>/dev/null || true; done
    waited=0
    while [ "$waited" -lt 10 ]; do
      if [ -z "$(bridge_port_holder_pid)" ]; then
        local survivors=""
        for q in $cands; do bridge_pid_gone "$q" || survivors="$survivors $q"; done
        if [ -z "$survivors" ]; then
          rm -f "$pid_file"
          echo "    the previous bridge is stopped and port 8675 is free"
          return 0
        fi
      fi
      sleep 1; waited=$((waited + 1))
    done
  fi
  # No candidates of our own (or they are gone): the port itself is
  # the verdict. Free — the stop is proven, nothing more to do.
  local holder=""
  holder="$(bridge_port_holder_pid)"
  if [ -z "$holder" ]; then
    if [ -f "$pid_file" ]; then rm -f "$pid_file"; fi
    return 0
  fi
  # The port is held by something this stop may not signal (another
  # program, or a bridge of a different install) — or by a candidate
  # even SIGKILL could not move. Either way: abort BEFORE files are
  # replaced, name the holder, give the exact command.
  local hcmd=""
  hcmd="$(python3 -c 'import sys; raw = open(sys.argv[1], "rb").read(); print(" ".join(part.decode("utf-8", "replace") for part in raw.split(bytes([0]))).strip())' "/proc/$holder/cmdline" 2>/dev/null || true)"
  echo "ERROR: port 8675 is still held by process $holder ($hcmd) and this installer cannot clear it." >&2
  echo "       No files have been replaced, and the pid file is untouched. The update has NOT happened." >&2
  echo "       End that process with:  kill -9 $holder" >&2
  echo "       then run this installer again." >&2
  return 1
}

# --- Which Linux family is this? (build .70, issue #48) ---
# The family is read once, up front, from /etc/os-release (ID and
# ID_LIKE) and announced in plain words. Only the dependency step
# below branches on it; everything else in this installer is
# shared and behaves the same on every family. Bazzite is matched
# first and kept as its own case: it is Fedora-based but
# immutable, so it never gets packages layered onto the host.
DISTRO_FAMILY="unknown"
DISTRO_ID=""
DISTRO_ID_LIKE=""
if [ -r /etc/os-release ]; then
  DISTRO_ID="$(sed -n 's/^ID=//p' /etc/os-release | head -1 | tr -d '"')"
  DISTRO_ID_LIKE="$(sed -n 's/^ID_LIKE=//p' /etc/os-release | head -1 | tr -d '"')"
fi
case "$DISTRO_ID $DISTRO_ID_LIKE" in
  *bazzite*) DISTRO_FAMILY="bazzite" ;;
esac
if [ "$DISTRO_FAMILY" = "unknown" ]; then
  case " $DISTRO_ID " in
    " debian "|" ubuntu "|" pop "|" linuxmint "|" raspbian "|" kali "|" mx "|" devuan "|" elementary "|" zorin ") DISTRO_FAMILY="debian" ;;
    " fedora "|" rhel "|" centos "|" rocky "|" almalinux "|" nobara ") DISTRO_FAMILY="fedora" ;;
    " arch "|" manjaro "|" endeavouros "|" garuda "|" artix "|" cachyos ") DISTRO_FAMILY="arch" ;;
  esac
fi
if [ "$DISTRO_FAMILY" = "unknown" ]; then
  case "$DISTRO_ID_LIKE" in
    *debian*|*ubuntu*) DISTRO_FAMILY="debian" ;;
    *fedora*|*rhel*|*centos*) DISTRO_FAMILY="fedora" ;;
    *arch*) DISTRO_FAMILY="arch" ;;
  esac
fi
case "$DISTRO_FAMILY" in
  debian) DISTRO_LABEL="the Debian family (Debian, Ubuntu, Pop!_OS, Mint and their kin)" ;;
  fedora) DISTRO_LABEL="Fedora (or a Fedora-based distro)" ;;
  arch) DISTRO_LABEL="Arch (or an Arch-based distro)" ;;
  bazzite) DISTRO_LABEL="Bazzite — Fedora-based, but immutable/atomic" ;;
  *) DISTRO_LABEL="an unrecognized distro" ;;
esac
echo "==> Detected Linux: $DISTRO_LABEL"
echo "    (read from /etc/os-release: ID=${DISTRO_ID:-?} ID_LIKE=${DISTRO_ID_LIKE:-none})"

# --- System dependencies: the one step that branches ---
# The same dependency set on every family — the dev libraries her
# window (the Tauri shell) builds against, the C toolchain the
# Rust build links with, and the base tools this installer itself
# uses (curl for the downloads, python3 for the bridge and the
# config steps, file) — each named in that family's own packages:
#
#   dependency         debian family                 fedora                       arch
#   -----------------  ---------------------------   --------------------------   ----------------------
#   C toolchain        build-essential               gcc gcc-c++ make             base-devel
#   pkg-config         pkg-config                    pkgconf-pkg-config           pkgconf
#   webkit2gtk dev     libwebkit2gtk-4.1-dev         webkit2gtk4.1-devel          webkit2gtk-4.1
#   gtk dev            libgtk-3-dev                  gtk3-devel                   gtk3
#   rsvg dev           librsvg2-dev                  librsvg2-devel               librsvg
#   appindicator dev   libayatana-appindicator3-dev  libappindicator-gtk3-devel   libappindicator-gtk3
#   openssl dev        libssl-dev                    openssl-devel                openssl
#   base tools         curl file python3             curl file python3            curl file python
#                      (+ python3-venv for her voice's venv)
DEPS_DEBIAN="build-essential pkg-config curl file python3 python3-venv libwebkit2gtk-4.1-dev libgtk-3-dev librsvg2-dev libayatana-appindicator3-dev libssl-dev"
DEPS_FEDORA="gcc gcc-c++ make pkgconf-pkg-config curl file python3 webkit2gtk4.1-devel gtk3-devel librsvg2-devel libappindicator-gtk3-devel openssl-devel"
DEPS_ARCH="base-devel pkgconf curl file python webkit2gtk-4.1 gtk3 librsvg libappindicator-gtk3 openssl"

# System packages need real root, which is a different question
# from write access to the install dir ($SUDO above): root needs
# no prefix; anyone else goes through sudo when it exists.
PKG_SUDO=""
if [ "$(id -u)" -ne 0 ] && command -v sudo >/dev/null 2>&1; then
  PKG_SUDO="sudo"
fi

# A failed dependency step never fails the install: it says what
# happened in plain words, the steps that need the packages (her
# window, above all) degrade the way they always have, and the
# core install (bridge + dashboard) completes regardless.
install_system_deps() {
  case "$DISTRO_FAMILY" in
    debian)
      echo "==> Installing system dependencies with apt (Debian family)"
      if [ "$(id -u)" -ne 0 ] && [ -z "$PKG_SUDO" ]; then
        echo "    note: no sudo available, so system packages cannot be installed from here." >&2
        echo "          The core install continues; her window build may fail without the" >&2
        echo "          development libraries. The full set for this family:" >&2
        echo "            apt install $DEPS_DEBIAN" >&2
        return 0
      fi
      $PKG_SUDO apt-get update -y >/dev/null 2>&1 || true
      if $PKG_SUDO apt-get install -y $DEPS_DEBIAN; then
        echo "    system dependencies installed (apt)."
      else
        echo "  *** Some system dependencies did not install — the apt output above names them." >&2
        echo "  *** The core install continues; her window build may fail without them." >&2
        echo "  *** Full set for this family: apt install $DEPS_DEBIAN" >&2
      fi
      ;;
    fedora)
      echo "==> Installing system dependencies with dnf (Fedora)"
      if [ "$(id -u)" -ne 0 ] && [ -z "$PKG_SUDO" ]; then
        echo "    note: no sudo available, so system packages cannot be installed from here." >&2
        echo "          The core install continues; her window build may fail without the" >&2
        echo "          development libraries. The full set for this family:" >&2
        echo "            dnf install $DEPS_FEDORA" >&2
        return 0
      fi
      if $PKG_SUDO dnf install -y $DEPS_FEDORA; then
        echo "    system dependencies installed (dnf)."
      else
        echo "  *** Some system dependencies did not install — the dnf output above names them." >&2
        echo "  *** The core install continues; her window build may fail without them." >&2
        echo "  *** Full set for this family: dnf install $DEPS_FEDORA" >&2
      fi
      ;;
    arch)
      echo "==> Installing system dependencies with pacman (Arch)"
      if [ "$(id -u)" -ne 0 ] && [ -z "$PKG_SUDO" ]; then
        echo "    note: no sudo available, so system packages cannot be installed from here." >&2
        echo "          The core install continues; her window build may fail without the" >&2
        echo "          development libraries. The full set for this family:" >&2
        echo "            pacman -S $DEPS_ARCH" >&2
        return 0
      fi
      if $PKG_SUDO pacman -S --needed --noconfirm $DEPS_ARCH; then
        echo "    system dependencies installed (pacman)."
      else
        echo "  *** Some system dependencies did not install — the pacman output above names them." >&2
        echo "  *** The core install continues; her window build may fail without them." >&2
        echo "  *** Full set for this family: pacman -S $DEPS_ARCH" >&2
      fi
      ;;
    bazzite)
      echo "==> Bazzite: no system packages are installed on the host."
      echo "    Bazzite is immutable, and this installer never layers packages with"
      echo "    rpm-ostree and never asks for a reboot. Her window takes the user-space"
      echo "    path instead (a Fedora distrobox, when one is available — see the"
      echo "    window step below); the bridge and the dashboard need no system"
      echo "    packages at all, and everything user-space (her voice's venv, the"
      echo "    model download) works exactly as on any other family."
      ;;
    *)
      echo "==> This distro wasn't recognized (ID=${DISTRO_ID:-?} ID_LIKE=${DISTRO_ID_LIKE:-none})," >&2
      echo "    so no package manager is guessed at and no system packages are" >&2
      echo "    installed. Everything that can be installed user-space still is," >&2
      echo "    and the core install (bridge + dashboard) completes as usual. Her" >&2
      echo "    standalone window needs the WebKitGTK development libraries" >&2
      echo "    (webkit2gtk / gtk / rsvg) from your distro's packages; without them" >&2
      echo "    its build cannot succeed, and start.sh opens the dashboard in your" >&2
      echo "    browser instead — the window step below says so again when it lands." >&2
      ;;
  esac
}
install_system_deps

# --- DHD prerequisites (build .74) --------------------------------
# Everything the DHD stack needs lands HERE, at install/update time,
# whether or not the operator ever turns DHD on — so enabling it
# later is genuinely one click with nothing left to fetch. The stack
# itself is bridge.py (stdlib proxy + built-in ACME client), so the
# prerequisites are small: the openssl binary (certificate work and
# ACME signing), a cert home inside the install's config, and —
# best-effort — the low-port capability that lets the bridge bind
# 80/443 without running as root. Added weight is honest: openssl is
# a ~1 MB package that most systems already carry (it rides along
# with curl/python3), the cert home is an empty directory, and the
# capability is metadata — when openssl is already present this step
# costs a few milliseconds and zero downloads. The step prints a
# machine-readable DHD-PREREQS: summary line; the updater's apply
# helper reads it back so the update ladder can show this step by
# name. The in-app DHD flow re-checks the same prerequisites as a
# safety net (a piece removed later gets an Install offer there).
DHD_CERT_HOME="$INSTALL_DIR/config/dhd"
install_dhd_prereqs() {
  echo "==> DHD prerequisites (the public door's pieces, installed whether or not DHD is ever turned on)"
  local ossl="missing"
  if command -v openssl >/dev/null 2>&1; then
    ossl="$(openssl version 2>/dev/null | head -1)"
    echo "    openssl: present ($ossl)."
  else
    case "$DISTRO_FAMILY" in
      debian)
        $PKG_SUDO apt-get update -y >/dev/null 2>&1 || true
        if $PKG_SUDO apt-get install -y openssl >/dev/null 2>&1 && command -v openssl >/dev/null 2>&1; then
          ossl="$(openssl version 2>/dev/null | head -1)"
          echo "    openssl: installed with apt ($ossl)."
        else
          echo "  *** openssl did not install — DHD's certificate steps need it. By hand: sudo apt-get install -y openssl" >&2
        fi
        ;;
      fedora)
        if $PKG_SUDO dnf install -y openssl >/dev/null 2>&1 && command -v openssl >/dev/null 2>&1; then
          ossl="$(openssl version 2>/dev/null | head -1)"
          echo "    openssl: installed with dnf ($ossl)."
        else
          echo "  *** openssl did not install — DHD's certificate steps need it. By hand: sudo dnf install -y openssl" >&2
        fi
        ;;
      arch)
        if $PKG_SUDO pacman -S --needed --noconfirm openssl >/dev/null 2>&1 && command -v openssl >/dev/null 2>&1; then
          ossl="$(openssl version 2>/dev/null | head -1)"
          echo "    openssl: installed with pacman ($ossl)."
        else
          echo "  *** openssl did not install — DHD's certificate steps need it. By hand: sudo pacman -S --needed openssl" >&2
        fi
        ;;
      bazzite)
        echo "    openssl: Bazzite installs nothing on the host; openssl ships in the host image —" >&2
        echo "    if it is ever missing there, DHD's own page offers the distrobox remedy with exact commands." >&2
        ;;
      *)
        echo "  *** openssl is not on this machine and the distro is unrecognized, so nothing was guessed at." >&2
        echo "  *** DHD's certificate steps need the openssl package from your distro; DHD's page names the step if it is missing." >&2
        ;;
    esac
  fi
  mkdir -p "$DHD_CERT_HOME" 2>/dev/null || true
  local home_state="not created"
  if [ -d "$DHD_CERT_HOME" ]; then home_state="ready"; fi
  echo "    cert home: $DHD_CERT_HOME ($home_state)."
  local cap_state="not granted"
  local pybin=""
  pybin="$(command -v python3 2>/dev/null || true)"
  if [ -n "$pybin" ]; then
    pybin="$(readlink -f "$pybin" 2>/dev/null || echo "$pybin")"
    if command -v getcap >/dev/null 2>&1 && getcap "$pybin" 2>/dev/null | grep -q cap_net_bind_service; then
      cap_state="already granted"
    elif command -v setcap >/dev/null 2>&1; then
      if $PKG_SUDO setcap 'cap_net_bind_service=+ep' "$pybin" 2>/dev/null; then
        cap_state="granted"
      fi
    fi
  fi
  if [ "$cap_state" = "granted" ] || [ "$cap_state" = "already granted" ]; then
    echo "    low ports: the bridge's python3 may bind 80/443 without root ($cap_state)."
  else
    echo "    low ports: capability not granted here — DHD still works when the bridge runs with"
    echo "    permission for ports 80/443; the exact one-line remedy (a setcap command) lives on"
    echo "    the DHD page and in Docs -> DHD, and the enable flow shows it if the step ever bites."
  fi
  echo "DHD-PREREQS: openssl=$ossl; cert-home=$home_state; low-port-capability=$cap_state"
}
install_dhd_prereqs

# A file that starts with an HTML doctype is a web page, not the
# llamafile binary (older installs could end up holding the Hugging
# Face repo page under this name). Such a file is never treated as an
# installed llamafile and never kept.
is_html_file() {
  [ -f "$1" ] && head -c 4096 "$1" 2>/dev/null | grep -qiE '<!doctype html|<html'
}

# --- Migration: a clean break from the pre-/opt install location ---
# Retire everything the old location could use to answer again — its
# bridge, its boot service — move its llamafile instead of
# re-downloading 3.27 GB, and carry its config and persona across.
# The old files themselves are removed at the end of the install,
# once the new location is fully in place.
MIGRATED=""
if [ -d "$OLD_DIR" ] && [ "$OLD_DIR" != "$INSTALL_DIR" ]; then
  MIGRATED=1
  echo "==> Migrating the earlier install from $OLD_DIR to $INSTALL_DIR"
  # The old location's bridge gets the same proven stop as any
  # other (build .91): found by pid file, port, and working
  # directory, waited on, escalated — and if its port cannot be
  # cleared, the install aborts here, before anything is moved.
  if ! stop_bridge "$OLD_DIR"; then
    echo "ERROR: the previous install's bridge could not be stopped — aborting before anything is moved." >&2
    exit 1
  fi
  UNIT_FILE="$HOME/.config/systemd/user/navi-llamafile.service"
  if [ -f "$UNIT_FILE" ] && grep -q "$OLD_DIR" "$UNIT_FILE"; then
    systemctl --user disable --now navi-llamafile.service 2>/dev/null || true
    rm -f "$UNIT_FILE"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "    old boot service (pointing at $OLD_DIR) disabled and removed"
  fi
  $SUDO mkdir -p "$INSTALL_DIR"
  if [ -f "$OLD_DIR/navi.llamafile" ] && is_html_file "$OLD_DIR/navi.llamafile"; then
    rm -f "$OLD_DIR/navi.llamafile"
  fi
  if [ ! -f "$INSTALL_DIR/navi.llamafile" ] && [ -f "$OLD_DIR/navi.llamafile" ]; then
    $SUDO mv "$OLD_DIR/navi.llamafile" "$INSTALL_DIR/navi.llamafile"
    echo "    navi.llamafile moved from the old location — no re-download"
  fi
  # A fresh install stashes the operator's chips and Soul/Memory
  # before the wipe and restores them after it (see below) — the
  # binary move applies either way.
  if [ -z "$FRESH" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/config"
    for f in navi.config.json soul.md memory.md; do
      if [ ! -f "$INSTALL_DIR/config/$f" ] && [ -f "$OLD_DIR/config/$f" ]; then
        $SUDO cp "$OLD_DIR/config/$f" "$INSTALL_DIR/config/$f"
        echo "    config/$f carried across from the old location"
      fi
    done
  fi
  # Installed chips travel too — in fresh mode they land before the
  # wipe, so the stash below picks them up and restores them.
  if [ -d "$OLD_DIR/chips" ] && [ ! -d "$INSTALL_DIR/chips" ]; then
    $SUDO cp -r "$OLD_DIR/chips" "$INSTALL_DIR/chips"
    echo "    installed chips carried across from the old location"
  fi
  if [ -d "$OLD_DIR/config/vault" ] && [ ! -d "$INSTALL_DIR/config/vault" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/config"
    $SUDO cp -r "$OLD_DIR/config/vault" "$INSTALL_DIR/config/vault"
    echo "    the Vault carried across from the old location"
  fi
fi

$SUDO mkdir -p "$INSTALL_DIR"

# Stop the bridge this install replaces — BEFORE any of its files
# are touched (the --fresh wipe below included) — and prove the
# stop (build .91, issue #91; the machinery is defined above). If
# the port cannot be cleared, the install aborts here with the
# holder named and every file untouched.
echo "==> Stopping any bridge still running from a previous install"
if ! stop_bridge "$INSTALL_DIR"; then
  echo "ERROR: the previous bridge could not be stopped — aborting with every file untouched." >&2
  exit 1
fi
# The previous shell window goes too (build .49): a window left open
# from the old install keeps the old dashboard's process alive and
# can hold the single-instance lock, so the new build never becomes
# the one actually running. Stop it before the new files land.
pkill -f "$INSTALL_DIR/navi-apex-shell" 2>/dev/null || true

if [ -n "$FRESH" ]; then
  echo "==> Fresh install: wiping $INSTALL_DIR and reinstalling from scratch"
  echo "    (the llamafile, your installed chips, the Vault, the DHD certificate home, your chats, and your Soul/Memory documents are kept)"
  # Stash the operator's own state before the wipe: the installed
  # chips (chips, installs, workflows) and the Soul/Memory
  # documents. A first install has none of these — the stash stays
  # empty and everything is created fresh, as it should be.
  STASH_DIR="$(mktemp -d)"
  if [ -d "$INSTALL_DIR/chips" ]; then
    $SUDO cp -r "$INSTALL_DIR/chips" "$STASH_DIR/chips" 2>/dev/null || true
  fi
  if [ -d "$INSTALL_DIR/rag-packs" ]; then
    $SUDO cp -r "$INSTALL_DIR/rag-packs" "$STASH_DIR/rag-packs" 2>/dev/null || true
  fi
  # The Vault (config/vault/) rides the same keep-list (build .72):
  # the shared desk of notes survives the wipe like everything else
  # that is hers and yours.
  if [ -d "$INSTALL_DIR/config/vault" ]; then
    $SUDO cp -r "$INSTALL_DIR/config/vault" "$STASH_DIR/vault" 2>/dev/null || true
  fi
  # The DHD certificate home (config/dhd/) rides the same keep-list
  # (build .77, issue #60): a real ACME certificate lives there, and
  # a fresh reinstall must never wipe it and force re-issuance.
  if [ -d "$INSTALL_DIR/config/dhd" ]; then
    $SUDO cp -r "$INSTALL_DIR/config/dhd" "$STASH_DIR/dhd" 2>/dev/null || true
  fi
  # The Mesh identity home (config/mesh/) rides the same keep-list
  # (build .85): the node keypair and Mesh certificate live there,
  # and a fresh reinstall must never wipe the node's identity —
  # losing it would silently orphan every pairing this machine
  # holds. The ledger rides with it; it is metadata, not content.
  if [ -d "$INSTALL_DIR/config/mesh" ]; then
    $SUDO cp -r "$INSTALL_DIR/config/mesh" "$STASH_DIR/mesh" 2>/dev/null || true
  fi
  # The server-side chat store (config/chats/, Build 12, #139)
  # rides the same keep-list: the threads are the operator's
  # history with her, kept the way the Mesh identity is kept.
  if [ -d "$INSTALL_DIR/config/chats" ]; then
    $SUDO cp -r "$INSTALL_DIR/config/chats" "$STASH_DIR/chats" 2>/dev/null || true
  fi
  # Her downloaded speech models and her call log are hers too —
  # they ride the same keep-list. The voice venv rides along as
  # well: the voice step below checks whether her voice is already
  # set up in it (the engines import) and skips the rebuild when
  # it is, so a fresh install never re-pays the pip install for a
  # voice that already works.
  if [ -d "$INSTALL_DIR/voice/models" ]; then
    $SUDO cp -r "$INSTALL_DIR/voice/models" "$STASH_DIR/voice-models" 2>/dev/null || true
  fi
  if [ -d "$INSTALL_DIR/voice/venv" ]; then
    $SUDO cp -r "$INSTALL_DIR/voice/venv" "$STASH_DIR/voice-venv" 2>/dev/null || true
  fi
  if [ -f "$INSTALL_DIR/voice/calls.json" ]; then
    $SUDO cp "$INSTALL_DIR/voice/calls.json" "$STASH_DIR/voice-calls.json" 2>/dev/null || true
  fi
  for f in soul.md memory.md; do
    if [ -f "$INSTALL_DIR/config/$f" ]; then
      $SUDO cp "$INSTALL_DIR/config/$f" "$STASH_DIR/$f" 2>/dev/null || true
    fi
  done
  $SUDO find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 ! -name 'navi.llamafile' -exec rm -rf {} +
fi
$SUDO mkdir -p "$INSTALL_DIR/app" "$INSTALL_DIR/config" "$INSTALL_DIR/assets"
if [ -n "$FRESH" ] && [ -n "${STASH_DIR:-}" ]; then
  if [ -d "$STASH_DIR/chips" ]; then
    $SUDO cp -r "$STASH_DIR/chips" "$INSTALL_DIR/chips"
    echo "    installed chips restored across the fresh install"
  fi
  if [ -d "$STASH_DIR/rag-packs" ]; then
    $SUDO cp -r "$STASH_DIR/rag-packs" "$INSTALL_DIR/rag-packs"
    echo "    her knowledge packs restored across the fresh install"
  fi
  if [ -d "$STASH_DIR/vault" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/config"
    $SUDO cp -r "$STASH_DIR/vault" "$INSTALL_DIR/config/vault"
    echo "    the Vault (your shared desk of notes) restored across the fresh install"
  fi
  if [ -d "$STASH_DIR/dhd" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/config"
    $SUDO cp -r "$STASH_DIR/dhd" "$INSTALL_DIR/config/dhd"
    echo "    the DHD certificate home (config/dhd/) restored across the fresh install"
  fi
  if [ -d "$STASH_DIR/mesh" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/config"
    $SUDO cp -r "$STASH_DIR/mesh" "$INSTALL_DIR/config/mesh"
    echo "    the Mesh identity home (config/mesh/) restored across the fresh install"
  fi
  if [ -d "$STASH_DIR/chats" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/config"
    $SUDO cp -r "$STASH_DIR/chats" "$INSTALL_DIR/config/chats"
    echo "    the chat store (config/chats/) restored across the fresh install"
  fi
  if [ -d "$STASH_DIR/voice-models" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/voice"
    $SUDO cp -r "$STASH_DIR/voice-models" "$INSTALL_DIR/voice/models"
    echo "    her speech models restored across the fresh install"
  fi
  if [ -f "$STASH_DIR/voice-calls.json" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/voice"
    $SUDO cp "$STASH_DIR/voice-calls.json" "$INSTALL_DIR/voice/calls.json"
    echo "    her call log restored across the fresh install"
  fi
  if [ -d "$STASH_DIR/voice-venv" ]; then
    $SUDO mkdir -p "$INSTALL_DIR/voice"
    $SUDO cp -r "$STASH_DIR/voice-venv" "$INSTALL_DIR/voice/venv"
    echo "    her voice venv restored across the fresh install"
  fi
  for f in soul.md memory.md; do
    if [ -f "$STASH_DIR/$f" ]; then
      $SUDO cp "$STASH_DIR/$f" "$INSTALL_DIR/config/$f"
      echo "    config/$f restored across the fresh install"
    fi
  done
  rm -rf "$STASH_DIR"
fi

if [ -f "$INSTALL_DIR/navi.llamafile" ] && is_html_file "$INSTALL_DIR/navi.llamafile"; then
  echo "==> The existing $INSTALL_DIR/navi.llamafile is an HTML page, not the llamafile binary — removing it"
  $SUDO rm -f "$INSTALL_DIR/navi.llamafile"
fi

if [ -f "$INSTALL_DIR/navi.llamafile" ]; then
  echo "==> navi.llamafile already exists in $INSTALL_DIR — skipping the download and llamafile setup"
else
  echo "==> Downloading the Navi llamafile"
  echo "    from: $LLAMAFILE_URL"
  $SUDO curl -fL -o "$INSTALL_DIR/navi.llamafile" "$LLAMAFILE_URL"
  if is_html_file "$INSTALL_DIR/navi.llamafile"; then
    $SUDO rm -f "$INSTALL_DIR/navi.llamafile"
    echo "ERROR: the download produced an HTML page, not the llamafile binary." >&2
    echo "       Expected the file itself from: $LLAMAFILE_URL" >&2
    exit 1
  fi
  $SUDO chmod +x "$INSTALL_DIR/navi.llamafile"
fi

# The stop itself already happened — and was proven — before the
# files above were touched (build .91). What remains here is the
# backstop warning: if a page that is not a Navi bridge still answers on 8675 — the
# operator's own earlier UI for Navi also served this address — the
# launcher would land on that program's page, not this dashboard.
# It is not this installer's process to kill; warn, by name, now.
if curl -s --max-time 2 -o /dev/null http://localhost:8675/ 2>/dev/null; then
  if ! curl -s --max-time 2 http://localhost:8675/api/status 2>/dev/null | grep -q '"app": "Navi: Apex"'; then
    FOREIGN_TITLE=$(curl -s --max-time 2 http://localhost:8675/ 2>/dev/null | grep -oiE '<title[^>]*>[^<]*</title>' | head -1 | sed -E 's/<[^>]+>//g' || true)
    echo "WARNING: http://localhost:8675 is still served by a different program (its page is titled \"$FOREIGN_TITLE\") — not a Navi bridge." >&2
    echo "         Launching Apex will keep showing that program's page until it is stopped." >&2
    echo "         Find it with: lsof -i :8675" >&2
  fi
fi

echo "==> Installing the dashboard, bridge, icon, and config"
$SUDO cp -r app/* "$INSTALL_DIR/app/"
# Issue #104 (Build 6): the bridge is staged under a pending
# name, NOT installed — the running version witnesses (bridge.py
# with its baked-in build sequence, the config's version record,
# and the VERSION file) all keep naming the OLD build until the
# version flip at the very end of this installer lands them
# together. A failure anywhere before the flip therefore leaves
# an install that honestly reports its old version, and Check
# for updates re-offers the update instead of crying current.
$SUDO cp bridge.py "$INSTALL_DIR/bridge.py.pending"
# Guardian (Build 14, #156): the bridge imports guardian.py from
# beside itself, so the engine lands in the install root next to
# bridge.py. It is a plain source file like the assets above —
# a copy of the sources missing it (a partial tree, say) must not
# abort the install: say so in plain words and carry on; the
# bridge runs with its inert Guardian fallback until Apex is
# installed from a tree that carries the engine.
if [ -f guardian.py ]; then
  $SUDO cp guardian.py "$INSTALL_DIR/guardian.py"
else
  echo "    note: the Guardian engine file (guardian.py) is missing from this copy of the"
  echo "          sources. The install continues without it — the bridge will run, but"
  echo "          Guardian's headroom protection stays off until Apex is installed from"
  echo "          a copy of the sources that carries guardian.py (the release zip does)."
fi
# The VERSION file is the app's single source of truth for its own
# version — the bridge reads it on every /api/status and the Updater
# compares it against the latest release. It is app code, not
# operator state: replaced on every install, like bridge.py.
# (Installers before build .47 never copied it at all, so the bridge
# fell back to the version recorded in the preserved config — a
# file written by whichever build installed first — and the menu
# footer flashed the new build's baked 0.1.0 at first paint before
# the status poll "reverted" it to that stale 1.0.0.)
# Issue #104 (Build 6): staged as VERSION.pending like the bridge
# — it becomes the install's VERSION only in the flip at the end,
# and it is the LAST file the flip moves, because it is the first
# witness every reader asks.
$SUDO cp VERSION "$INSTALL_DIR/VERSION.pending"
$SUDO cp start.sh "$INSTALL_DIR/start.sh"
$SUDO chmod +x "$INSTALL_DIR/start.sh"
$SUDO cp run-llamafile.sh "$INSTALL_DIR/run-llamafile.sh"
$SUDO chmod +x "$INSTALL_DIR/run-llamafile.sh"
# The standalone window's sources (Tauri shell) — built into the
# navi-apex-shell binary by the shell step near the end of this
# installer, once the install root belongs to the operator.
$SUDO mkdir -p "$INSTALL_DIR/shell"
$SUDO cp -r shell/* "$INSTALL_DIR/shell/"
# The package's docs land in the installed tree too (build .77,
# issue #60): the shipped tree and the installed tree agree, so
# docs/DHD.md is on the machine beside everything else it documents.
$SUDO mkdir -p "$INSTALL_DIR/docs"
$SUDO cp -r docs/* "$INSTALL_DIR/docs/"
# The app icon is cosmetic — a missing copy must never abort an
# install. A git clone of the repo carries none of the binary icon
# files (they ship only inside the release zip), so a clone install
# reaches this line with no assets/icon.png: warn in plain words
# and carry on; the app and its menu entry use a fallback icon.
if [ -f assets/icon.png ]; then
  $SUDO cp assets/icon.png "$INSTALL_DIR/assets/icon.png"
else
  echo "    note: the app icon file (assets/icon.png) is missing from this copy of the sources."
  echo "          That is expected when installing from a git clone — the clone does not carry"
  echo "          the binary icon files; they ship inside the release zip. The install continues"
  echo "          without it, and the app and its menu entry will use a fallback icon."
fi
# Navi's chat portrait gets the same treatment as the icon — and
# for the same reason. The bridge serves it from the install tree
# (GET /assets/navi-portrait.jpg) for her chat gutter faces and
# the presence header, and a git clone carries none of the binary
# asset files (they ship only inside the release zip), so a clone
# install reaches this line with no portrait to copy: say so in
# plain words and carry on — chat shows without her picture, and
# nothing else about the install changes. (Build 7 shipped the
# portrait inside the zip but this copy step did not exist yet,
# so Build 7 installs served no picture at all.)
if [ -f assets/navi-portrait.jpg ]; then
  $SUDO cp assets/navi-portrait.jpg "$INSTALL_DIR/assets/navi-portrait.jpg"
else
  echo "    note: Navi's chat portrait (assets/navi-portrait.jpg) is missing from this copy"
  echo "          of the sources. That is expected when installing from a git clone — the"
  echo "          clone does not carry the binary asset files; they ship inside the release"
  echo "          zip. The install continues without it, and chat will show without her"
  echo "          picture until Apex is installed from the release zip."
fi
# The Row's icon, worn by the DHD door as its favicon (Build 13,
# issue #151), gets the same treatment: favicon-scale derivatives
# of the Nocturne Row site's logo, served by the bridge from the
# install tree (GET /favicon-32.png and /apple-touch-icon.png).
# A git clone carries none of the binary asset files, so a clone
# install reaches this line with no icons to copy: say so in
# plain words and carry on — the door simply wears no icon.
for icon_file in favicon-32.png icon-180.png; do
  if [ -f "assets/$icon_file" ]; then
    $SUDO cp "assets/$icon_file" "$INSTALL_DIR/assets/$icon_file"
  else
    echo "    note: the DHD door icon (assets/$icon_file) is missing from this copy of the"
    echo "          sources. That is expected when installing from a git clone — the clone"
    echo "          does not carry the binary asset files; they ship inside the release"
    echo "          zip. The install continues without it, and the door wears no icon"
    echo "          until Apex is installed from the release zip."
  fi
done
if [ ! -f "$INSTALL_DIR/config/navi.config.json" ]; then
  $SUDO cp config/navi.config.json "$INSTALL_DIR/config/navi.config.json"
fi
# Persona documents are the operator's to edit — never overwrite them
# on a reinstall.
[ -f "$INSTALL_DIR/config/soul.md" ] || $SUDO cp config/soul.md "$INSTALL_DIR/config/soul.md"
[ -f "$INSTALL_DIR/config/memory.md" ] || $SUDO cp config/memory.md "$INSTALL_DIR/config/memory.md"
# Her voice ships as documentation + a folder: the models download
# into voice/models/ on first use (that folder is never wiped by an
# update — see the --fresh stash above), and the call log lives
# beside them.
$SUDO cp requirements-voice.txt "$INSTALL_DIR/requirements-voice.txt"
$SUDO mkdir -p "$INSTALL_DIR/voice/models"
$SUDO cp voice/README.md "$INSTALL_DIR/voice/README.md"
# Record the chosen startup mode in the installed config — and
# re-stamp the two fields that describe THIS package on THIS machine:
# the bridge port and the install directory. A config carried across
# from an older install (the migration above, or any plain reinstall)
# still names the old build's port and the old location; left alone,
# the bridge once bound that stale port while its launcher polled
# the new one. The operator's own settings stay untouched.
$SUDO python3 - "$INSTALL_DIR/config/navi.config.json" "$STARTUP" "$INSTALL_DIR" "8675" <<'PY'
import json, sys
path, mode, install_dir, port = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
with open(path) as f:
    cfg = json.load(f)
cfg["startup"] = "on-ui-launch" if mode == "launch" else "on-boot"
cfg.setdefault("bridge", {})["host"] = "127.0.0.1"
cfg["bridge"]["port"] = port
cfg["install_dir"] = install_dir
# The config's recorded version is NOT stamped here (issue
# #104, Build 6): it is one of the version witnesses, so it is
# stamped in the flip at the end of this installer, from the
# staged VERSION.pending — stamping it here would let a later
# failure leave the witnesses disagreeing about the build.
with open(path, "w") as f:
    json.dump(cfg, f, indent=2)
PY

# --- Hardware profiling ---
# Her runtime settings are derived from THIS machine, never copied
# from the developer's: detect CPU / RAM / GPU, derive threads,
# context, batch and GPU layers, log detection + reasoning to
# hardware-profile.log, and write the profile into the config —
# every launch path reads its flags from there. A manual override
# already in the config (source=manual) is preserved and the log
# says so; anything else is re-profiled fresh on every install.
echo "==> Profiling this machine for Navi's runtime settings"
$SUDO python3 - "$INSTALL_DIR/config/navi.config.json" "$INSTALL_DIR/hardware-profile.log" <<'PY'
import json, os, platform, subprocess, sys, time
cfg_path, log_path = sys.argv[1], sys.argv[2]
with open(cfg_path) as f:
    cfg = json.load(f)
existing = cfg.get("hardware_profile") or {}
if existing.get("source") == "manual" and existing.get("settings"):
    with open(log_path, "a") as f:
        f.write("[hardware] install: preserved the operator's manual override from Settings — not re-profiling over it.\n")
    print("    hardware: kept your manual Settings override (see hardware-profile.log)")
    sys.exit(0)
det = {"os": "linux", "osLabel": "Linux", "cpuModel": platform.processor() or "unknown CPU",
       "cpuCores": os.cpu_count() or 1, "performanceCores": None, "totalRamGB": 0.0,
       "gpuPresent": False, "gpuName": "", "gpuKind": "none", "gpuVramGB": None}
try:
    mem_kb = 0; cpu_name = ""
    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemTotal:"): mem_kb = int(line.split()[1])
    with open("/proc/cpuinfo") as f:
        for line in f:
            if line.startswith("model name"): cpu_name = line.split(":", 1)[1].strip(); break
    if cpu_name: det["cpuModel"] = cpu_name
    det["totalRamGB"] = round(mem_kb / 1048576.0, 1) if mem_kb else 0.0
    # Hybrid Intel (e.g. i5-1340P: 4P+8E): performance cores = the
    # distinct max-frequency cluster is not in /proc; cpuinfo_max_freq
    # per-core gives a usable signal — count cores at the top freq.
    try:
        freqs = []
        for i in range(det["cpuCores"]):
            p = f"/sys/devices/system/cpu/cpu{i}/cpufreq/cpuinfo_max_freq"
            if os.path.exists(p):
                with open(p) as f: freqs.append(int(f.read().strip()))
        if freqs and len(set(freqs)) > 1:
            det["performanceCores"] = freqs.count(max(freqs)) or None
    except Exception: pass
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"], capture_output=True, text=True, timeout=5).stdout.strip()
        if out:
            parts = [p.strip() for p in out.splitlines()[0].split(",")]
            det.update(gpuPresent=True, gpuName=parts[0], gpuKind="discrete")
            if len(parts) > 1: det["gpuVramGB"] = int(round(float(parts[1].split()[0]) / 1024.0))
        else: raise RuntimeError("no gpu")
    except Exception:
        try:
            out = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5).stdout
            for line in out.splitlines():
                if "VGA compatible controller" in line or "3D controller" in line:
                    det["gpuPresent"] = True; det["gpuName"] = line.split(":", 2)[-1].strip()
                    low = det["gpuName"].lower()
                    det["gpuKind"] = "discrete" if ("nvidia" in low or "geforce" in low or "radeon rx" in low) else "integrated"
                    break
        except Exception: pass
except Exception as e:
    print(f"    hardware: detection partially failed ({e}) — conservative fluid floor applies")
ram = float(det["totalRamGB"] or 0); logical = max(1, int(det["cpuCores"] or 1)); perf = det["performanceCores"]
reason = []
if perf: threads = max(2, min(12, int(perf))); reason.append(f"Threads {threads}: matched to the {perf} performance cores.")
elif logical >= 16: threads = 8; reason.append(f"Threads 8: half of {logical} logical cores, capped.")
elif logical >= 8: threads = 4; reason.append(f"Threads 4: half of {logical} logical cores.")
elif logical >= 4: threads = 2; reason.append(f"Threads 2: conservative for a {logical}-core machine.")
else: threads = 1; reason.append("Threads 1: single-core floor.")
if ram < 6: ctx = 2048; reason.append("Context 2048: under 6 GiB RAM.")
elif ram < 12: ctx = 4096; reason.append(f"Context 4096: {ram:.1f} GiB RAM — proven fluid size for this class (Framework 13 baseline).")
elif ram < 20: ctx = 8192; reason.append(f"Context 8192: {ram:.1f} GiB RAM.")
elif ram < 40: ctx = 16384; reason.append(f"Context 16384: {ram:.1f} GiB RAM.")
else: ctx = 32768; reason.append(f"Context 32768: {ram:.1f} GiB RAM — workstation headroom.")
batch = 256 if ram < 6 else (512 if ram < 20 else 1024); reason.append(f"Batch {batch}: sized to RAM ({ram:.1f} GiB).")
gpu = 0; vram = det["gpuVramGB"]
if det["gpuKind"] == "discrete" and vram is not None and vram >= 4:
    gpu = 99 if vram >= 12 else (28 if vram >= 8 else (20 if vram >= 6 else 12)); reason.append(f"GPU layers {gpu}: discrete GPU with {vram} GiB VRAM.")
elif det["gpuKind"] == "integrated": reason.append("GPU layers 0: integrated graphics share system RAM — CPU inference is the fluid path.")
else: reason.append("GPU layers 0: no confirmed discrete GPU — CPU-only.")
if ram < 6 or logical <= 4: tier, tier_label = "constrained", "Constrained — small machine, fluid floor"
elif gpu > 0 and ram >= 16: tier, tier_label = ("workstation", "Workstation — discrete GPU + ample RAM") if ram >= 32 else ("performance", "Performance — discrete GPU acceleration")
elif ram >= 20: tier, tier_label = "performance", "Performance — ample RAM, CPU inference scaled up"
elif ram >= 12: tier, tier_label = "balanced", "Balanced — above the fluid baseline"
else: tier, tier_label = "fluid", "Fluid — Framework-class baseline (proven on an i5-1340P / ~9.5 GiB)"
settings = {"threads": threads, "ctxSize": ctx, "batchSize": batch, "gpuLayers": gpu}
now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
flags = f"--ctx-size {ctx} --threads {threads} --batch-size {batch}" + (f" --n-gpu-layers {gpu}" if gpu > 0 else "")
log = [f"[hardware] {now} — install-time profiling (Linux)", f"[hardware] OS: {det['osLabel']}", f"[hardware] CPU: {det['cpuModel']} — {logical} logical cores" + (f", {perf} performance" if perf else ""), f"[hardware] RAM: {ram:.1f} GiB total", f"[hardware] GPU: {det['gpuName'] or 'none detected'} ({det['gpuKind']})"] + [f"[hardware] → {r}" for r in reason] + [f"[hardware] chosen: {flags} (written to config hardware_profile + runtime)"]
profile = {"detected": det, "settings": settings, "autoSettings": settings, "source": "auto", "tier": tier, "tierLabel": tier_label, "reasoning": reason, "installLog": log, "detectedAt": now}
cfg["hardware_profile"] = profile
cfg["runtime"] = {"threads": threads, "ctx_size": ctx, "batch_size": batch, "gpu_layers": gpu, "flags": flags}
with open(cfg_path, "w") as f: json.dump(cfg, f, indent=2)
with open(log_path, "a") as f:
    for line in log: f.write(line + "\n")
print(f"    hardware: {det['cpuModel']} · {ram:.1f} GiB RAM · GPU {det['gpuName'] or 'none'} ({det['gpuKind']})")
print(f"    chosen: {flags} — {tier_label} (full log: hardware-profile.log)")
PY

# --- Her voice (optional) ---
# The speech engines (faster-whisper + Kokoro/Piper) are the app's
# only Python dependencies, and they stay optional: the bridge is
# stdlib-only and imports them lazily. Say yes and they land in an
# isolated venv at voice/venv — start.sh then runs the bridge with
# that Python. Say no (or run non-interactively without --voice)
# and the exact manual command is printed instead; the Voice tab
# keeps naming it until the engines exist. A failed voice install
# never fails the app install.
# Already set up? When the venv is on disk and its Python imports
# the engines, her voice is already installed — most often because
# a --fresh install just restored the venv it stashed before the
# wipe. Asking again, let alone rebuilding ~250 MB of packages over
# a working voice, would be pure waste: the whole step is skipped
# and the installer says so.
VOICE_READY=""
if [ -x "$INSTALL_DIR/voice/venv/bin/python" ] && "$INSTALL_DIR/voice/venv/bin/python" -c "import faster_whisper, kokoro" >/dev/null 2>&1; then
  VOICE_READY=1
fi
if [ -z "$VOICE_READY" ]; then
case "$VOICE" in
  yes|no) ;;
  *)
    if [ -n "$HAVE_TTY" ]; then
      echo ""
      echo "Give Navi a voice? She'd hear you with a local Whisper model and"
      echo "answer out loud with Kokoro — all on this machine, all on CPU."
      echo "This installs Python speech packages into an isolated venv in the"
      echo "install folder (~250 MB; the speech models download on first use)."
      echo "  1) Yes — install her voice now"
      echo "  2) No — skip it (the Voice tab will name the command)"
      while true; do
        printf "Enter 1 or 2: "
        if ! read -r VCHOICE < /dev/tty; then
          echo ""
          echo "The terminal stopped answering — skipping her voice for now."
          echo "(Install it any time with the command the Voice tab names.)"
          VOICE="no"
          break
        fi
        case "$VCHOICE" in
          1|yes) VOICE="yes"; break ;;
          2|no) VOICE="no"; break ;;
          *) echo "Please answer 1 or 2." ;;
        esac
      done
    else
      VOICE="no"
    fi
    ;;
esac
fi
if [ -n "$VOICE_READY" ]; then
  echo "==> Her voice is already set up — $INSTALL_DIR/voice/venv imports faster_whisper and kokoro — skipping the voice install"
elif [ "$VOICE" = "yes" ]; then
  echo "==> Installing her voice (Python speech engines, isolated venv)"
  # Every step is checked and logged, and the result is VERIFIED —
  # the engines must import in the venv's Python before this step
  # may call itself done. The previous shape chained the steps
  # behind pip --quiet with one generic failure line: the voice
  # step could fail (the classic Debian/Ubuntu failure is
  # python3 -m venv dying because the python3-venv package is
  # missing) and the install still finished looking successful,
  # leaving a silent Voice tab to discover later. Failures now
  # name the step that failed, keep the full log beside her voice,
  # and repeat as the last lines of the install.
  VOICE_TMP_LOG="$(mktemp)"
  VOICE_FAIL=""
  if ! $SUDO python3 -m venv "$INSTALL_DIR/voice/venv" >>"$VOICE_TMP_LOG" 2>&1; then
    VOICE_FAIL="creating the venv (python3 -m venv) — on Debian/Ubuntu this usually means the python3-venv package is missing: sudo apt install python3-venv, then re-run this installer"
  elif ! $SUDO "$INSTALL_DIR/voice/venv/bin/python" -m pip install --upgrade pip >>"$VOICE_TMP_LOG" 2>&1; then
    VOICE_FAIL="installing pip into the venv"
  elif ! $SUDO "$INSTALL_DIR/voice/venv/bin/python" -m pip install -r "$INSTALL_DIR/requirements-voice.txt" >>"$VOICE_TMP_LOG" 2>&1; then
    VOICE_FAIL="installing the speech packages from requirements-voice.txt — the log tail names the cause (a blocked download or a missing system library are the usual ones)"
  elif ! "$INSTALL_DIR/voice/venv/bin/python" -c "import faster_whisper, kokoro" >>"$VOICE_TMP_LOG" 2>&1; then
    VOICE_FAIL="verification — the packages landed, but the venv's Python cannot import faster_whisper and kokoro"
  fi
  $SUDO mkdir -p "$INSTALL_DIR/voice"
  $SUDO cp "$VOICE_TMP_LOG" "$INSTALL_DIR/voice/voice-install.log" 2>/dev/null || true
  rm -f "$VOICE_TMP_LOG"
  if [ -z "$VOICE_FAIL" ]; then
    echo "    voice installed and verified: $INSTALL_DIR/voice/venv — faster_whisper and kokoro import cleanly."
    echo "    (install log: $INSTALL_DIR/voice/voice-install.log; her speech models download on first use)"
  else
    echo "" >&2
    echo "  *** HER VOICE DID NOT INSTALL ***" >&2
    echo "  *** Failed step: $VOICE_FAIL" >&2
    echo "  *** Navi herself is fully installed — only her voice is missing." >&2
    echo "  *** Full log: $INSTALL_DIR/voice/voice-install.log" >&2
    echo "  *** Fix the step above, then re-run this installer and say yes at the voice step." >&2
  fi
else
  echo "==> Skipping her voice for now. Install it any time with:"
  echo "    python3 -m pip install -r $INSTALL_DIR/requirements-voice.txt"
  echo "    (or re-run this installer and say yes at the voice step)"
fi

echo "==> Registering Apex in the application menu"
ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$ICON_DIR" "$APP_DIR"
# Same rule as the install-tree copy above: no icon file in this
# copy of the sources (a git clone) means the menu entry is still
# written — it just uses a fallback icon — and the installer's
# report below says which of the two actually happened.
MENU_ICON=""
if [ -f assets/icon.png ]; then
  cp assets/icon.png "$ICON_DIR/navi-apex.png"
  MENU_ICON=1
else
  echo "    note: no app icon file in this copy of the sources (see the note above) —"
  echo "          the menu entry is still installed, and it will use a fallback icon."
fi
sed "s|__INSTALL_DIR__|$INSTALL_DIR|g" assets/navi-apex.desktop > "$APP_DIR/navi-apex.desktop"
chmod +x "$APP_DIR/navi-apex.desktop"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APP_DIR" || true
if [ -n "$MENU_ICON" ]; then
  echo "    launcher installed: $APP_DIR/navi-apex.desktop (icon: navi-apex)"
else
  echo "    launcher installed: $APP_DIR/navi-apex.desktop (icon: fallback — no icon file in this copy of the sources)"
fi

if [ "$STARTUP" = "boot" ]; then
  echo "==> Registering Apex as systemd user services — the llamafile, and the bridge headless"
  UNIT_DIR="$HOME/.config/systemd/user"
  mkdir -p "$UNIT_DIR"
  sed "s|__INSTALL_DIR__|$INSTALL_DIR|g" systemd/navi-llamafile.service > "$UNIT_DIR/navi-llamafile.service"
  sed "s|__INSTALL_DIR__|$INSTALL_DIR|g" systemd/navi-bridge.service > "$UNIT_DIR/navi-bridge.service"
  systemctl --user daemon-reload
  systemctl --user enable --now navi-llamafile.service
  systemctl --user enable --now navi-bridge.service
  echo "    services enabled: navi-llamafile.service, navi-bridge.service"
  # User services start at LOGIN, not boot, unless lingering is
  # on for the user. Try to enable it; when this session cannot,
  # print the exact command instead of leaving the operator to
  # believe boot-start works when it does not (Build 12, #142).
  if loginctl show-user "$(id -un)" --property=Linger --value 2>/dev/null | grep -qx "yes"; then
    echo "    linger: already on — the services start at boot"
  elif $SUDO loginctl enable-linger "$(id -un)" 2>/dev/null; then
    echo "    linger: enabled — the services start at boot, before any login"
  else
    echo "    NOTE: lingering could not be enabled from here, so for now the services start at LOGIN, not boot."
    echo "    To make Apex start at boot, run exactly:  sudo loginctl enable-linger $(id -un)"
  fi
else
  echo "==> Launch mode: start.sh will boot the llamafile server with the UI"
fi

# The install root is the operator's, whatever privileges it took to
# write there: the bridge runs as them and edits persona as them.
if [ -n "$SUDO" ]; then
  echo "==> Handing $INSTALL_DIR to $(id -un)"
  $SUDO chown -R "$(id -un):$(id -gn)" "$INSTALL_DIR"
fi

# The migration's clean break, completed: the old location goes away
# entirely, so nothing stale remains to grab port 8675 at boot.
if [ -n "$MIGRATED" ]; then
  echo "==> Removing the old install at $OLD_DIR"
  rm -rf "$OLD_DIR"
fi

# The standalone window: verify-then-skip. The same law as her
# voice and the llamafile — work already done and verifiably
# unchanged is not redone. A completed shell build is stamped: the
# hash of the shipped shell sources sits beside the binary
# (navi-apex-shell.stamp). A later install whose package ships
# those exact sources, with the binary present and sane, skips the
# Rust check and the cargo build both. Changed sources, a missing
# or suspect binary, or --fresh always rebuild — and the installer
# prints which road it took either way.
# The stamp is checked against TWO hashes of the same sources:
# the installed copies (what the launcher will verify at run time)
# and this package's own pristine copies beside the installer
# (immune to anything that happens to the installed tree between
# the copy above and this check). Either match proves the binary
# was built from exactly the sources this package ships. And when
# the build is NOT skipped on a reinstall, the installer now says
# WHY — a missing stamp used to rebuild in total silence, which
# made a lost stamp indistinguishable from changed sources.
shell_sources_hash() {
  local dir="$1"
  # The shell icon is optional in the hash: a git clone of the repo
  # carries no binary icon files (they ship only in the release
  # zip), and a missing cosmetic file must never break the shell
  # step — hash what is there. When the icon is present it is
  # hashed in its usual place, so a full package stamps exactly
  # as it always has.
  local files="Cargo.toml build.rs src/main.rs tauri.conf.json"
  if [ -f "$dir/icons/icon.png" ]; then files="$files icons/icon.png"; fi
  files="$files README.md"
  local f
  for f in $files; do
    if [ ! -f "$dir/$f" ]; then echo ""; return; fi
  done
  if command -v sha256sum >/dev/null 2>&1; then
    (cd "$dir" && sha256sum $files | sha256sum | awk '{print $1}')
  elif command -v shasum >/dev/null 2>&1; then
    (cd "$dir" && shasum -a 256 $files | shasum -a 256 | awk '{print $1}')
  else
    echo ""
  fi
}
SHELL_HASH="$(shell_sources_hash "$INSTALL_DIR/shell")"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PKG_SHELL_HASH=""
if [ "$SCRIPT_DIR" != "$INSTALL_DIR" ]; then
  PKG_SHELL_HASH="$(shell_sources_hash "$SCRIPT_DIR/shell")"
fi
SHELL_SKIP=""
if [ -z "$FRESH" ]; then
  STAMP=""
  if [ -f "$INSTALL_DIR/navi-apex-shell.stamp" ]; then STAMP="$(cat "$INSTALL_DIR/navi-apex-shell.stamp")"; fi
  if [ ! -x "$INSTALL_DIR/navi-apex-shell" ]; then
    if [ -n "$STAMP" ]; then
      echo "==> Her window: a build stamp is saved but the window binary itself is missing — rebuilding it below."
    fi
  elif [ -z "$SHELL_HASH" ] && [ -z "$PKG_SHELL_HASH" ]; then
    echo "==> Her window: the shell sources cannot be hashed here (no sha256sum/shasum, or a source file is missing) — rebuilding it below."
  else
    BIN_SIZE=$(wc -c < "$INSTALL_DIR/navi-apex-shell" | tr -d ' ')
    if [ "$BIN_SIZE" -le 100000 ]; then
      echo "==> Her window: the binary beside the installer is only $BIN_SIZE bytes — too small to be her window — rebuilding it below."
    elif [ -z "$STAMP" ]; then
      echo "==> Her window: the window binary is present but its build stamp (navi-apex-shell.stamp) is missing — rebuilding so the binary is verifiably stamped."
      echo "    (If this message appears on every install, something on this machine is removing that stamp file between installs.)"
    elif [ "$STAMP" = "$SHELL_HASH" ] || { [ -n "$PKG_SHELL_HASH" ] && [ "$STAMP" = "$PKG_SHELL_HASH" ]; }; then
      SHELL_SKIP=1
      echo "==> Her window is already built from these exact shell sources — the stamp beside the binary matches."
    else
      echo "==> Her window: the saved build stamp does not cover this binary and these shell sources — rebuilding it below."
    fi
  fi
fi

# Her window is built around its icon — the shell's own
# icons/icon.png, which the shell's config names and its build
# embeds. A git clone of the repo does not carry it (the binary
# icon files ship only in the release zip), so from a clone the
# window build genuinely cannot proceed: name it here, and the
# build step below skips itself in plain words instead of dying
# halfway through a cargo build. With the file present — every
# release-zip install — this stays empty and nothing changes.
# (The assets/ .ico/.icns renditions are never copied into the
# install tree and the Linux shell build never reads them, so
# they are not part of this check.)
SHELL_ICON_MISSING=""
if [ ! -f "$INSTALL_DIR/shell/icons/icon.png" ]; then
  SHELL_ICON_MISSING="shell/icons/icon.png"
fi

# Bazzite's window path (build .70, issue #48): the host is
# immutable, so her window can only be built inside a Fedora
# distrobox — a container whose own filesystem may change, and
# which shares this home folder (the build runs on a scratch copy
# of the shell sources under ~/.cache for exactly that reason).
# Find one now, if it exists; the Rust and window steps below
# branch on it. No distrobox, no window build — said plainly
# there, never a silent half-install.
BAZZITE_BOX=""
if [ "$DISTRO_FAMILY" = "bazzite" ] && command -v distrobox >/dev/null 2>&1; then
  BAZZITE_BOX="$(distrobox list 2>/dev/null | grep -i fedora | head -1 | awk -F'|' '{gsub(/^ +| +$/, "", $2); print $2}')"
fi

# --- Rust toolchain (rustup) ---
# The shell build below needs cargo. If cargo is not already here,
# the official rustup installer fills the gap: per-user (no sudo),
# non-interactive, minimal profile — just enough to build the shell.
# An existing toolchain is left exactly as found. The attempt is
# logged to shell/shell-build.log (the shell build appends to the
# same log), PATH is refreshed in this shell afterwards, and the
# same install run proceeds to build the window with the toolchain
# it just installed. A failed Rust install (no network is the usual
# cause) never fails the install: it says so plainly below, and
# start.sh's browser fallback covers launching.
echo "==> Checking for a Rust toolchain (her window needs one)"
if [ -n "$SHELL_SKIP" ]; then
  echo "    her window is already built from these shell sources — no Rust needed this run."
elif [ -n "$SHELL_ICON_MISSING" ]; then
  echo "    her window cannot be built from this copy of the sources (missing icon files: $SHELL_ICON_MISSING) — no Rust needed this run; the window step below explains."
elif [ "$DISTRO_FAMILY" = "bazzite" ] && [ -z "$BAZZITE_BOX" ]; then
  echo "    Bazzite with no Fedora distrobox available: her window build is skipped below (the window step explains what you got instead), so no Rust is needed this run."
elif [ "$DISTRO_FAMILY" = "bazzite" ]; then
  echo "    Bazzite with a Fedora distrobox ($BAZZITE_BOX): her window is built inside it — the toolchain lives in the container, so no host Rust is needed."
elif command -v cargo >/dev/null 2>&1; then
  echo "    Rust found: $(cargo --version 2>/dev/null || echo cargo) — using the existing toolchain as-is."
elif [ -x "$HOME/.cargo/bin/cargo" ]; then
  export PATH="$HOME/.cargo/bin:$PATH"
  echo "    Rust found at $HOME/.cargo/bin/cargo (not on PATH) — using it."
else
  echo "    no Rust toolchain here — installing one with rustup (per-user, minimal profile)…"
  mkdir -p "$INSTALL_DIR/shell"
  RUST_OK=""
  if command -v curl >/dev/null 2>&1; then
    if curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs 2>>"$INSTALL_DIR/shell/shell-build.log" | sh -s -- -y --profile minimal >> "$INSTALL_DIR/shell/shell-build.log" 2>&1; then
      RUST_OK=1
    fi
  fi
  export PATH="$HOME/.cargo/bin:$PATH"
  if [ -n "$RUST_OK" ] && command -v cargo >/dev/null 2>&1; then
    echo "    Rust installed via rustup: $(cargo --version 2>/dev/null || echo cargo) — building her window with it below."
  else
    echo "" >&2
    echo "  *** RUST DID NOT INSTALL — the rustup download or run failed (no network is the usual cause)." >&2
    echo "  *** Full log: $INSTALL_DIR/shell/shell-build.log" >&2
    echo "  *** Navi herself is fully installed — only her standalone window is missing." >&2
    echo "  *** She still launches: start.sh falls back to the dashboard in your browser." >&2
    echo "  *** Install Rust yourself (https://rustup.rs) and re-run this installer to give her a window of her own." >&2
  fi
fi

# A shell binary from an older build is a hazard, not a fallback:
# it predates whatever the current shell does, so when a new build
# fails and the old binary stays beside start.sh, the launcher would
# run the wrong app as if it were this build. When this build cannot
# be produced, the previous binary is retired — moved aside, stamp
# removed — so the launcher takes its honest fallback instead.
retire_stale_shell() {
  if [ -x "$INSTALL_DIR/navi-apex-shell" ]; then
    mv "$INSTALL_DIR/navi-apex-shell" "$INSTALL_DIR/navi-apex-shell.stale"
    rm -f "$INSTALL_DIR/navi-apex-shell.stamp"
    echo "  *** The previous window binary was built from older shell sources — moved aside as" >&2
    echo "  *** navi-apex-shell.stale (stamp removed) so it can never be launched as if it were" >&2
    echo "  *** this build. Fix the cause above and re-run this installer to rebuild her window." >&2
  fi
}

# --- The standalone window (Tauri shell) ---
# Apex opens in her own window now — a small Tauri shell over
# the OS webview (no bundled Chromium; the footprint matters on a
# 9.4 GiB machine) that loads the dashboard from the local bridge.
# It is built here, as the operator (after the chown above), from
# the sources in shell/ — cargo is incremental, so a reinstall
# rebuilds only what changed. When no Rust toolchain could be had
# (the rustup step above failed) the install still succeeds:
# start.sh falls back to opening the dashboard in the default
# browser, exactly as before, and the dashboard stays reachable at
# http://localhost:8675 either way. A failed build never
# fails the install — it names itself and keeps the log.
echo "==> Building the standalone window (Tauri shell)"
if [ -n "$SHELL_SKIP" ]; then
  echo "    already built from these exact shell sources — skipping the cargo build."
  echo "    (binary: $INSTALL_DIR/navi-apex-shell — pass --fresh, change the shell sources, or delete navi-apex-shell.stamp to force a rebuild)"
elif [ -n "$SHELL_ICON_MISSING" ]; then
  echo "    her window cannot be built from this copy of the sources: the icon files her window"
  echo "    is built with are not here (missing: $SHELL_ICON_MISSING). A git clone of the repo does"
  echo "    not carry the binary icon files — they ship inside the release zip — so the window"
  echo "    build is skipped for this install, in the open, instead of failing halfway through."
  echo "    The release zip is the complete package."
  retire_stale_shell
  echo "    Navi still launches: start.sh falls back to the dashboard in your browser."
elif [ "$DISTRO_FAMILY" = "bazzite" ] && [ -z "$BAZZITE_BOX" ]; then
  echo "    SKIPPED on Bazzite: her standalone window is not built on this install."
  echo "    Bazzite is immutable — its system cannot take the development libraries"
  echo "    her window builds against, and this installer will not layer them with"
  echo "    rpm-ostree or ask you to reboot. What you got instead is the complete"
  echo "    core install: the bridge and the dashboard, which start.sh opens in"
  echo "    your browser — everything she does works there; only the standalone"
  echo "    window is missing. To give her the window later, create a Fedora"
  echo "    distrobox (distrobox create --name fedora --image fedora:latest),"
  echo "    then re-run this installer: it will build her window inside it."
  retire_stale_shell
elif [ "$DISTRO_FAMILY" = "bazzite" ]; then
  echo "    building her window inside the Fedora distrobox '$BAZZITE_BOX'…"
  BOX_BUILD_DIR="$HOME/.cache/navi-apex-shell-build"
  rm -rf "$BOX_BUILD_DIR"
  mkdir -p "$BOX_BUILD_DIR"
  cp -r "$INSTALL_DIR/shell/." "$BOX_BUILD_DIR/"
  if distrobox enter "$BAZZITE_BOX" -- bash -c "sudo dnf install -y webkit2gtk4.1-devel gtk3-devel librsvg2-devel libappindicator-gtk3-devel openssl-devel gcc gcc-c++ make pkgconf-pkg-config curl file >/dev/null 2>&1; if ! command -v cargo >/dev/null 2>&1; then curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal >/dev/null 2>&1; fi; export PATH=\$HOME/.cargo/bin:\$PATH; cd \"$BOX_BUILD_DIR\" && cargo build --release" >> "$INSTALL_DIR/shell/shell-build.log" 2>&1 && [ -x "$BOX_BUILD_DIR/target/release/navi-apex-shell" ]; then
    cp "$BOX_BUILD_DIR/target/release/navi-apex-shell" "$INSTALL_DIR/navi-apex-shell"
    chmod +x "$INSTALL_DIR/navi-apex-shell"
    if [ -n "$SHELL_HASH" ]; then
      echo "$SHELL_HASH" > "$INSTALL_DIR/navi-apex-shell.stamp" || true
      if [ "$(cat "$INSTALL_DIR/navi-apex-shell.stamp" 2>/dev/null || true)" = "$SHELL_HASH" ]; then
        echo "    build stamp saved: $INSTALL_DIR/navi-apex-shell.stamp"
      else
        echo "  *** THE BUILD STAMP DID NOT SAVE to $INSTALL_DIR/navi-apex-shell.stamp — the window is built," >&2
        echo "  *** but the next install will rebuild it because it cannot verify this one." >&2
      fi
    fi
    echo "    standalone window built (inside the distrobox): $INSTALL_DIR/navi-apex-shell"
    echo "    (build log: $INSTALL_DIR/shell/shell-build.log)"
  else
    echo "  *** THE STANDALONE WINDOW DID NOT BUILD inside the Fedora distrobox — full log: $INSTALL_DIR/shell/shell-build.log" >&2
    retire_stale_shell
    echo "  *** Navi still launches meanwhile: start.sh falls back to the dashboard in your browser." >&2
  fi
elif command -v cargo >/dev/null 2>&1; then
  if (cd "$INSTALL_DIR/shell" && cargo build --release >> "$INSTALL_DIR/shell/shell-build.log" 2>&1) && [ -x "$INSTALL_DIR/shell/target/release/navi-apex-shell" ]; then
    cp "$INSTALL_DIR/shell/target/release/navi-apex-shell" "$INSTALL_DIR/navi-apex-shell"
    chmod +x "$INSTALL_DIR/navi-apex-shell"
    # The stamp is what lets the next install skip this build and
    # what the launcher verifies before running the binary — so
    # the write is read back, not assumed. A stamp that did not
    # land (a permissions surprise in the install root) is named
    # now, in the open, instead of silently costing a full cargo
    # build on every later install.
    if [ -n "$SHELL_HASH" ]; then
      echo "$SHELL_HASH" > "$INSTALL_DIR/navi-apex-shell.stamp" || true
      if [ "$(cat "$INSTALL_DIR/navi-apex-shell.stamp" 2>/dev/null || true)" = "$SHELL_HASH" ]; then
        echo "    build stamp saved: $INSTALL_DIR/navi-apex-shell.stamp"
      else
        echo "  *** THE BUILD STAMP DID NOT SAVE to $INSTALL_DIR/navi-apex-shell.stamp — the window is built," >&2
        echo "  *** but the next install will rebuild it because it cannot verify this one. Check that" >&2
        echo "  *** $INSTALL_DIR is writable by $(id -un), then re-run this installer." >&2
      fi
    fi
    echo "    standalone window built: $INSTALL_DIR/navi-apex-shell"
    echo "    (build log: $INSTALL_DIR/shell/shell-build.log)"
  else
    echo "  *** THE STANDALONE WINDOW DID NOT BUILD — full log: $INSTALL_DIR/shell/shell-build.log" >&2
    echo "  *** The usual cause is the WebKitGTK development packages — the dependency step" >&2
    echo "  *** near the start of this install installs them on every family it knows" >&2
    echo "  *** (Debian family, Fedora, Arch); its lines above say what happened there." >&2
    retire_stale_shell
    echo "  *** Navi still launches meanwhile: start.sh falls back to the dashboard in your browser." >&2
  fi
else
  echo "    no working Rust toolchain — skipping the shell build (the rustup step above says why)."
  retire_stale_shell
  echo "    Navi still launches: start.sh falls back to the dashboard in your browser."
fi

if [ -n "${VOICE_FAIL:-}" ]; then
  echo "" >&2
  echo "  *** REMINDER: HER VOICE DID NOT INSTALL — failed step: $VOICE_FAIL" >&2
  echo "  *** Full log: $INSTALL_DIR/voice/voice-install.log — Navi works without it, and the Voice tab will keep naming the step." >&2
fi

# The tray login autostart is retired: earlier builds registered
# an XDG autostart entry that launched her tray-resident at login.
# Remove it, so an upgrade cleans the machine — nothing starts
# Navi at login now; she runs when the operator launches her.
echo "==> Removing the retired tray login autostart, if an earlier install left one"
AUTOSTART_DIR="$HOME/.config/autostart"
if [ -f "$AUTOSTART_DIR/navi-apex.desktop" ]; then
  rm -f "$AUTOSTART_DIR/navi-apex.desktop"
  echo "    removed: $AUTOSTART_DIR/navi-apex.desktop (the tray autostart an earlier build registered)"
fi


# --- VERSION FLIP (issue #104) ---
# The install's final act, deliberately last: everything above
# this line can fail under set -e and leave an install whose
# witnesses all still name the OLD build, so Check for updates
# honestly re-offers and a retry starts clean. The flip lands
# the witnesses in an order that is safe to interrupt: the
# config's version record first (it is only the fallback
# witness), the staged bridge second (its baked-in build
# sequence becomes the disk truth), and the VERSION file LAST
# of all — it is the primary witness, the one the bridge reads
# on every /api/status, so it is the last thing that may change.
echo "==> Stamping the new version (the install's final step)"
$SUDO python3 - "$INSTALL_DIR/config/navi.config.json" "$INSTALL_DIR/VERSION.pending" <<'PY'
import json, sys
path, ver_path = sys.argv[1], sys.argv[2]
with open(ver_path) as f:
    ver_parts = f.read().strip().splitlines()[0].split()
if ver_parts:
    with open(path) as f:
        cfg = json.load(f)
    cfg["version"] = ver_parts[0]
    cfg["version_status"] = ver_parts[1] if len(ver_parts) > 1 else "stable"
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)
PY
$SUDO mv "$INSTALL_DIR/bridge.py.pending" "$INSTALL_DIR/bridge.py"
$SUDO mv "$INSTALL_DIR/VERSION.pending" "$INSTALL_DIR/VERSION"
echo "    version stamped: $(head -n 1 "$INSTALL_DIR/VERSION")"
# --- END VERSION FLIP ---

# --- Relaunch what the install stopped, and verify it (build
# .91, issue #91, Cause 3) ---
# An install that replaced a RUNNING bridge used to end here with
# the new files on disk and nothing serving: the update only took
# effect when the operator thought to launch the app. Now, when a
# bridge was stopped at the top of this install, she is relaunched
# through start.sh and the install verifies the bridge answering
# on the port is the NEW build (status stamp match) before it
# calls itself done. Over a stopped app, or with --no-relaunch,
# nothing is launched — and --no-relaunch says so plainly.
RELAUNCH_OK=""
RELAUNCH_NOW=""
if [ -n "$STOPPED_BRIDGE" ] && [ -z "$NO_RELAUNCH" ]; then
  RELAUNCH_NOW=1
  echo "==> A bridge was running when this install began — relaunching Apex on the new build"
  nohup "$INSTALL_DIR/start.sh" >> "$INSTALL_DIR/start.log" 2>&1 &
  NEW_STAMP="$(sed -n 's/^BRIDGE_BUILD = "\(.*\)".*/\1/p' "$INSTALL_DIR/bridge.py" 2>/dev/null | head -n 1)"
  if [ -n "$NEW_STAMP" ]; then
    waited=0
    while [ "$waited" -lt 90 ]; do
      body="$(curl -fsS --max-time 3 "http://127.0.0.1:8675/api/status" 2>/dev/null || true)"
      case "$body" in
        *'"app": "Navi: Apex"'*)
          if printf '%s' "$body" | grep -qF "\"bridge\": \"$NEW_STAMP\""; then
            RELAUNCH_OK=1
            break
          fi
          ;;
      esac
      sleep 2; waited=$((waited + 2))
    done
  fi
  if [ -n "$RELAUNCH_OK" ]; then
    echo "    verified live: the bridge answering on port 8675 reports the new build ($NEW_STAMP)"
  else
    echo "WARNING: Apex was relaunched but the new build could not be verified answering on port 8675." >&2
    echo "         Watch $INSTALL_DIR/start.log, and start her by hand with: $INSTALL_DIR/start.sh" >&2
  fi
fi

# Closing lines — exactly one story, and it is the true one.
echo ""
if [ -n "$NO_RELAUNCH" ] && [ -n "$STOPPED_BRIDGE" ]; then
  echo "Done — but Apex is NOT running: the bridge this install replaced was stopped and --no-relaunch asked not to restart her."
  echo "Start her with: $INSTALL_DIR/start.sh"
elif [ -n "$RELAUNCH_OK" ]; then
  echo "Done — Apex is running again on the new build."
elif [ -n "$RELAUNCH_NOW" ]; then
  echo "Done — the files are in place, but see the warning above: Apex may not be running yet."
  echo "Start her with: $INSTALL_DIR/start.sh"
else
  echo "Done. Launch \"Apex\" from your application menu, or run:"
  echo "    $INSTALL_DIR/start.sh"
fi
