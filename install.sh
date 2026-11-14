#!/usr/bin/env bash
# Apex installer — 0.2.0e Build 10 (#193): the manifest-driven,
# stage-and-swap installer. Three laws, learned from eighteen
# field incidents (files/installer-audit.md):
#
#   A) The payload is a CONTRACT, not a habit. MANIFEST.txt
#      declares every file this package carries, its class and
#      its sha256. The installer copies and verifies FROM the
#      manifest — there are no hand-written per-file copy lists
#      left to desync (the #192 class: engines present in the
#      zip, absent from the tree, silence in the product).
#   B) Placement is ONE ACT. The new tree is assembled in a
#      staging directory BESIDE the live tree and promoted by
#      rename; a kill or failure at any point leaves the
#      previous version ENTIRELY live (payload, app, config) or
#      the new version entirely live — never a mixture (the
#      incident-18 chimera: Build 9's face over Build 7's
#      bridge). The two-file .pending flip ceremony is gone.
#   C) Provisioning is not placement. A first install
#      provisions an operator-owned install root ONCE; every
#      placement after that runs in the operator's own context
#      and never needs sudo. An install invoked through sudo
#      (root's context wearing the operator's name) REFUSES up
#      front, by name, before anything is touched: under sudo,
#      systemctl --user cannot reach the operator's bus and
#      files land root-owned (incidents 16/17). After the swap,
#      the product verifies ITSELF — stamps, manifest hashes,
#      engine imports — and the install stands or rolls back on
#      that verdict, not on a version proxy.
#
# What an install preserves, untouched as ever: the llamafile,
# installed chips and RAG packs, the Vault, DHD certificates,
# the Mesh identity, chats, config, the voice venv and the
# operator's Soul/Memory. --fresh still means a clean payload
# over the same keep-list.
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SRC_DIR"

STAMP="2026-11-14.10"
BUILD_STAMP="2026-11-14.10"

# --- Who is running this, and in whose name -------------------
# SUDO in the old sense is GONE: placement runs unprivileged in
# the operator's context, always. PKG_SUDO survives for the
# provisioning steps that genuinely need the package manager.
OPERATOR="$(id -un)"
PKG_SUDO=""
if [ "$(id -u)" -ne 0 ]; then PKG_SUDO="sudo"; fi
# SUDO is always empty now — placement never escalates (piece C).
# The variable survives only so the proven regions spliced into
# this installer, which prefix their copies with $SUDO, run
# exactly as written: unprivileged, in the operator's context.
SUDO=""
LLAMAFILE_URL="https://huggingface.co/saintssec/navi.llamafile/resolve/main/navi.llamafile"

# Root wearing the operator's name (sudo from an operator shell)
# is refused BEFORE anything is touched: its $HOME, its user
# bus and its file ownership are all root's, and an install from
# that context can only strand root-owned files in an
# operator-owned tree (incident 17). A genuine root shell (a
# container's first boot, a root login — no SUDO_USER) installs
# as root, the operator of that context, and converges the same
# way.
if [ "$(id -u)" -eq 0 ] && [ -n "${SUDO_USER:-}" ] && [ "$SUDO_USER" != "root" ]; then
  echo "ERROR: this install was invoked through sudo (root's context wearing $SUDO_USER's name) — refusing before anything is touched." >&2
  echo "       Under sudo, systemctl --user cannot reach $SUDO_USER's session bus and files would land root-owned in" >&2
  echo "       $SUDO_USER's tree. Run it as $SUDO_USER instead:  ./install.sh (no sudo — placement never needs it)." >&2
  exit 1
fi

# --- Where Apex lives ------------------------------------------
INSTALL_DIR="/opt/navi-apex"
OLD_DIR="$HOME/.local/share/navi"
STARTUP=""
VOICE=""
FRESH=""
NO_RELAUNCH=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dir) INSTALL_DIR="$2"; shift 2 ;;
    --startup) STARTUP="$2"; shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    --fresh) FRESH=1; shift ;;
    --no-relaunch) NO_RELAUNCH=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
case "$INSTALL_DIR" in
  /*) ;;
  *) INSTALL_DIR="$PWD/$INSTALL_DIR" ;;
esac
while [ "$INSTALL_DIR" != "/" ] && [ "${INSTALL_DIR%/}" != "$INSTALL_DIR" ]; do INSTALL_DIR="${INSTALL_DIR%/}"; done
PARENT_DIR="$(dirname "$INSTALL_DIR")"
STAGE_DIR="$PARENT_DIR/.apex-stage"
PREV_DIR="$PARENT_DIR/.apex-prev"
FAILED_DIR="$PARENT_DIR/.apex-failed-$STAMP"
CARRY_DIR="$PARENT_DIR/.apex-carry"

# A previous install killed between the two renames of its swap
# heals here, before anything else reads the tree: the install
# dir missing while a complete previous tree waits beside it
# means the previous version comes back, whole.
if [ ! -d "$INSTALL_DIR" ] && [ -d "$PREV_DIR" ]; then
  echo "==> Healing an interrupted swap: restoring the previous install from $PREV_DIR"
  mv "$PREV_DIR" "$INSTALL_DIR"
fi

# --- Up-front ownership truth (incidents 16/17) ----------------
# An existing tree that this context cannot write is refused
# BEFORE the bridge is stopped or a file is moved — never
# discovered mid-copy with the old install already stopped.
if [ -d "$INSTALL_DIR" ] && [ ! -w "$INSTALL_DIR" ]; then
  echo "ERROR: the existing install at $INSTALL_DIR is not writable by $OPERATOR — refusing before anything is touched." >&2
  echo "       Its files are owned by another user (a past install run as root leaves exactly this). Repair ownership" >&2
  echo "       once, as that user:  sudo chown -R $OPERATOR: $INSTALL_DIR   — then run this installer again, without sudo." >&2
  exit 1
fi
# Foreign-owned FILES inside a writable tree do not refuse the
# install (incident 16, second reading): stage-and-swap never
# writes into the old tree's files — it renames the whole tree
# aside and renames a wholly operator-owned stage in. A payload
# file a past sudo repair left root-owned is simply left behind
# in the previous tree; if that tree then cannot be fully
# deleted by the operator, its retirement below says so by name
# and keeps it, rather than failing an install that already
# succeeded. What still refuses, above, is a tree the operator
# cannot write at all — the rename itself would be a lie there.
if [ ! -d "$INSTALL_DIR" ]; then
  # First install: provision the operator-owned root, once.
  mkdir -p "$INSTALL_DIR" 2>/dev/null || {
    echo "ERROR: cannot create the install root $INSTALL_DIR as $OPERATOR — provision it once, owned by the operator:" >&2
    echo "       sudo mkdir -p $INSTALL_DIR && sudo chown $OPERATOR: $INSTALL_DIR   — then run this installer again, without sudo." >&2
    exit 1
  }
  [ -w "$INSTALL_DIR" ] || {
    echo "ERROR: the install root $INSTALL_DIR exists but is not writable by $OPERATOR." >&2
    echo "       Provision it once, owned by the operator:  sudo chown $OPERATOR: $INSTALL_DIR" >&2
    exit 1
  }
fi

echo "== Apex installer — build $STAMP (manifest-driven, stage-and-swap)"
echo "   Installing into: $INSTALL_DIR (as $OPERATOR; placement is unprivileged)"

# With no --startup choice, an interactive run on a real terminal
# asks; a detached run (the updater's apply helper, piped output)
# decides from the config the previous install recorded rather
# than dying on a prompt nobody can answer (#75).
HAVE_TTY=""
if ( : < /dev/tty ) 2>/dev/null; then HAVE_TTY=1; fi
if [ -z "$STARTUP" ]; then
  _cfg_mode=""
  if [ -f "$INSTALL_DIR/config/navi.config.json" ]; then
    _cfg_mode="$(python3 -c "import json,sys
try:
    print(json.load(open(sys.argv[1])).get('startup') or '')
except Exception:
    print('')" "$INSTALL_DIR/config/navi.config.json" 2>/dev/null || true)"
  fi
  _units_on=""
  if [ -f "$HOME/.config/systemd/user/navi-bridge.service" ]; then _units_on=1; fi
  if [ -n "$_cfg_mode" ]; then
    case "$_cfg_mode" in
      on-boot) STARTUP="boot" ;;
      *) STARTUP="launch" ;;
    esac
    echo "    startup choice: keeping the recorded choice from the installed config ($_cfg_mode)"
  elif [ -n "$_units_on" ]; then
    STARTUP="boot"
    echo "    startup choice: boot services are registered for this install — keeping boot mode"
  elif [ -n "$HAVE_TTY" ]; then
    echo ""
    echo "How should Apex start?"
    echo "  1) When you launch the app (default)"
    echo "  2) At boot — services start with the machine (headless-friendly)"
    printf "Choose [1/2, Enter = 1]: "
    read -r _ans < /dev/tty || _ans=""
    case "$_ans" in 2) STARTUP="boot" ;; *) STARTUP="launch" ;; esac
  else
    STARTUP="launch"
    echo "    startup choice: no terminal and nothing recorded — defaulting to launch mode"
    echo "    (pass --startup boot to run Apex as boot services instead)."
  fi
fi
case "$STARTUP" in
  launch|boot) ;;
  *) echo "ERROR: --startup must be launch or boot (got: $STARTUP)" >&2; exit 2 ;;
esac


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

# --- The running window (0.2.0e Build 3, issue #174) ----------------
# The field failure this closes: the detached apply stopped the
# bridge but not the running window, then the shell rebuild copied
# the new binary over the live one — "cp: cannot create regular
# file '…/navi-apex-shell': Text file busy" — and the whole apply
# exited 1. Two belts, both worn: the window is stopped with the
# same care as the bridge (below), and the binary is installed by
# temp-write + atomic rename (install_shell_binary), which a
# running binary can never block — rename replaces the directory
# entry, not the open file.
shell_pids() {
  # Pids whose executable IS <dir>/navi-apex-shell — matched on
  # /proc/<pid>/exe, never on the command line (a text match also
  # catches editors, greps, and this installer's own shell).
  local target="$1/navi-apex-shell" pid exe
  for pid in $(ls /proc 2>/dev/null | grep -E '^[0-9]+$'); do
    [ "$pid" = "$$" ] && continue
    exe="$(readlink "/proc/$pid/exe" 2>/dev/null || true)"
    exe="${exe% (deleted)}"
    if [ "$exe" = "$target" ]; then
      echo "$pid"
    fi
  done
}

stop_shell() {
  local dir="$1" pids pid tries
  pids="$(shell_pids "$dir" | tr '\n' ' ')"
  pids="${pids% }"
  if [ -z "$pids" ]; then
    return 0
  fi
  echo "    stopping the running shell window (pid(s): $pids)..."
  for pid in $pids; do kill "$pid" 2>/dev/null || true; done
  tries=0
  while [ "$tries" -lt 50 ]; do
    local alive=0
    for pid in $pids; do
      if ! bridge_pid_gone "$pid"; then alive=1; fi
    done
    [ "$alive" = "0" ] && return 0
    sleep 0.2
    tries=$((tries + 1))
  done
  for pid in $pids; do kill -9 "$pid" 2>/dev/null || true; done
  tries=0
  while [ "$tries" -lt 25 ]; do
    local alive2=0
    for pid in $pids; do
      if ! bridge_pid_gone "$pid"; then alive2=1; fi
    done
    [ "$alive2" = "0" ] && return 0
    sleep 0.2
    tries=$((tries + 1))
  done
  echo "  *** the running shell window (pid(s): $pids) did not stop; the new binary still lands by atomic rename, and the old window keeps running the old build until it is closed." >&2
  return 0
}

install_shell_binary() {
  # Write-to-temp + atomic rename: the destination is never opened
  # for writing, so a still-running old binary cannot make this
  # fail with Text file busy — ever (#174).
  local src="$1" dest="$INSTALL_DIR/navi-apex-shell" tmp
  tmp="$INSTALL_DIR/.navi-apex-shell.new.$$"
  rm -f "$tmp"
  cp "$src" "$tmp" || { rm -f "$tmp"; return 1; }
  chmod +x "$tmp" || { rm -f "$tmp"; return 1; }
  mv -f "$tmp" "$dest"
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
# Build 3 (#174): a detached apply (the Updater's helper, a DHD
# session) has no terminal — sudo's password or fingerprint prompt
# can never be answered there, and the field log showed the
# attempt dying against PAM before the step degraded. Say it
# plainly, once, and take the graceful-degrade path directly:
# the system-package step is skipped, the core install continues.
if [ -n "$PKG_SUDO" ] && [ ! -t 0 ] && ! sudo -n true 2>/dev/null; then
  echo "    note: this install is running detached (no terminal), and a detached apply cannot answer a sudo prompt — the system-package step is being skipped; the core install continues without it."
  PKG_SUDO=""
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

# --- The manifest contract (piece A) ---------------------------
# MANIFEST.txt lines: <path>\t<class>\t<sha256 | "-">
# Classes: payload (lands in the tree, hash-verified in place by
# the product's self-check), seed-config (lands only where the
# tree has none), generated (ships as a template; the installer
# generates the real file), package-only (never lands).
MANIFEST="$SRC_DIR/MANIFEST.txt"
manifest_rows() {
  [ -f "$MANIFEST" ] || return 0
  grep -v '^#' "$MANIFEST" | grep -v '^$' || true
}
# Verify the package against its own declaration BEFORE anything
# is stopped or staged: a payload file missing from the package,
# or one whose bytes are not the declared bytes, fails the
# install BY NAME here — the #192 failure shape (a build whose
# package and payload disagreed) can no longer reach the machine.
echo "==> Verifying the package against its manifest"
_missing=""
_bad=""
while IFS=$'\t' read -r _p _c _h; do
  [ -n "$_p" ] || continue
  case "$_c" in
    payload|seed-config|generated)
      if [ ! -f "$SRC_DIR/$_p" ]; then _missing="$_missing $_p"; continue; fi
      if [ "$_h" != "-" ]; then
        _got="$(sha256sum "$SRC_DIR/$_p" | awk '{print $1}')"
        [ "$_got" = "$_h" ] || _bad="$_bad $_p"
      fi
      ;;
  esac
done <<EOF_MANIFEST
$(manifest_rows)
EOF_MANIFEST
if [ -n "$_missing" ]; then
  echo "ERROR: this package is incomplete — its manifest declares files it does not carry:$_missing" >&2
  echo "       Nothing was stopped or changed. Re-download the package and run the installer again." >&2
  exit 1
fi
if [ -n "$_bad" ]; then
  echo "ERROR: package files whose bytes are not the bytes the manifest declares:$_bad" >&2
  echo "       Nothing was stopped or changed. Re-download the package and run the installer again." >&2
  exit 1
fi
echo "    the package matches its manifest"



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
# A file that starts with an HTML doctype is a web page, not the
# llamafile binary (older installs could end up holding the Hugging
# Face repo page under this name). Such a file is never treated as an
# installed llamafile and never kept.
is_html_file() {
  [ -f "$1" ] && head -c 4096 "$1" 2>/dev/null | grep -qiE '<!doctype html|<html'
}

# --- Migration: the pre-/opt location, carried not moved -------
# The old location's state lands in the carry dir beside the
# install; the stage assembly below consumes it. The old tree
# itself is removed only after the new one is verified live.
MIGRATED=""
if [ -d "$OLD_DIR" ] && [ "$OLD_DIR" != "$INSTALL_DIR" ]; then
  MIGRATED=1
  echo "==> Carrying the earlier install at $OLD_DIR across"
  if ! stop_bridge "$OLD_DIR"; then
    echo "ERROR: the previous install's bridge could not be stopped — aborting before anything is carried." >&2
    exit 1
  fi
  UNIT_FILE="$HOME/.config/systemd/user/navi-llamafile.service"
  if [ -f "$UNIT_FILE" ] && grep -q "$OLD_DIR" "$UNIT_FILE"; then
    systemctl --user disable --now navi-llamafile.service 2>/dev/null || true
    rm -f "$UNIT_FILE"
    systemctl --user daemon-reload 2>/dev/null || true
    echo "    old boot service (pointing at $OLD_DIR) disabled and removed"
  fi
  rm -rf "$CARRY_DIR"; mkdir -p "$CARRY_DIR"
  if [ -f "$OLD_DIR/navi.llamafile" ] && is_html_file "$OLD_DIR/navi.llamafile"; then
    rm -f "$OLD_DIR/navi.llamafile"
  fi
  [ -f "$OLD_DIR/navi.llamafile" ] && mv "$OLD_DIR/navi.llamafile" "$CARRY_DIR/navi.llamafile" && echo "    navi.llamafile carried — no re-download"
  for _d in config chips rag-packs; do
    [ -d "$OLD_DIR/$_d" ] && cp -r "$OLD_DIR/$_d" "$CARRY_DIR/$_d"
  done
  [ -f "$OLD_DIR/voice/calls.json" ] && mkdir -p "$CARRY_DIR/voice" && cp "$OLD_DIR/voice/calls.json" "$CARRY_DIR/voice/calls.json"
  echo "    config, chips and packs carried from the old location"
fi

# --- Stage assembly (piece B) ----------------------------------
# The new tree is built BESIDE the live one. The live tree is not
# touched by anything in this section: a kill here leaves the
# previous version entirely live, down to its config.
echo "==> Assembling the new tree beside the live one"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR"
IS_UPDATE=""
[ -f "$INSTALL_DIR/bridge.py" ] && IS_UPDATE=1
if [ -n "$IS_UPDATE" ] && [ -z "$FRESH" ]; then
  # The whole previous tree is the stage's foundation — operator
  # state, runtime residue and all — minus the shell's build
  # residue (regenerated by the build step). The llamafile and
  # the voice venv are hardlinked where the filesystem allows:
  # the bridge never writes the llamafile, and the venv is only
  # ever replaced wholesale by the voice step.
  (cd "$INSTALL_DIR" && tar --exclude='./shell/target' --exclude='./updates' -cf - .) | (cd "$STAGE_DIR" && tar --no-same-owner -xf -)
  if [ -f "$INSTALL_DIR/navi.llamafile" ]; then
    rm -f "$STAGE_DIR/navi.llamafile"
    ln "$INSTALL_DIR/navi.llamafile" "$STAGE_DIR/navi.llamafile" 2>/dev/null || cp "$INSTALL_DIR/navi.llamafile" "$STAGE_DIR/navi.llamafile"
  fi
  if [ -d "$INSTALL_DIR/voice/venv" ]; then
    rm -rf "$STAGE_DIR/voice/venv"
    cp -al "$INSTALL_DIR/voice/venv" "$STAGE_DIR/voice/venv" 2>/dev/null || cp -r "$INSTALL_DIR/voice/venv" "$STAGE_DIR/voice/venv"
  fi
  # The stage starts from the OLD tree, so update staging the
  # updater left behind never rides into the new version.
  rm -rf "$STAGE_DIR/updates"
elif [ -n "$IS_UPDATE" ]; then
  echo "    fresh install: keeping the llamafile, chips, packs, the Vault, DHD and Mesh homes,"
  echo "    chats, config and the voice venv — everything else is rebuilt from the package"
  for _d in chips rag-packs; do
    [ -d "$INSTALL_DIR/$_d" ] && cp -r "$INSTALL_DIR/$_d" "$STAGE_DIR/$_d"
  done
  if [ -d "$INSTALL_DIR/config" ]; then
    mkdir -p "$STAGE_DIR/config"
    for _d in vault dhd mesh chats; do
      [ -d "$INSTALL_DIR/config/$_d" ] && cp -r "$INSTALL_DIR/config/$_d" "$STAGE_DIR/config/$_d"
    done
    for _f in navi.config.json soul.md memory.md; do
      [ -f "$INSTALL_DIR/config/$_f" ] && cp "$INSTALL_DIR/config/$_f" "$STAGE_DIR/config/$_f"
    done
  fi
  [ -f "$INSTALL_DIR/navi.llamafile" ] && { ln "$INSTALL_DIR/navi.llamafile" "$STAGE_DIR/navi.llamafile" 2>/dev/null || cp "$INSTALL_DIR/navi.llamafile" "$STAGE_DIR/navi.llamafile"; }
  [ -d "$INSTALL_DIR/voice/models" ] && mkdir -p "$STAGE_DIR/voice" && cp -r "$INSTALL_DIR/voice/models" "$STAGE_DIR/voice/models"
  [ -d "$INSTALL_DIR/voice/venv" ] && { cp -al "$INSTALL_DIR/voice/venv" "$STAGE_DIR/voice/venv" 2>/dev/null || cp -r "$INSTALL_DIR/voice/venv" "$STAGE_DIR/voice/venv"; }
  [ -f "$INSTALL_DIR/voice/calls.json" ] && mkdir -p "$STAGE_DIR/voice" && cp "$INSTALL_DIR/voice/calls.json" "$STAGE_DIR/voice/calls.json"
fi
if [ -d "$CARRY_DIR" ]; then
  [ -f "$CARRY_DIR/navi.llamafile" ] && [ ! -f "$STAGE_DIR/navi.llamafile" ] && mv "$CARRY_DIR/navi.llamafile" "$STAGE_DIR/navi.llamafile"
  for _d in config chips rag-packs; do
    if [ -d "$CARRY_DIR/$_d" ] && [ ! -d "$STAGE_DIR/$_d" ]; then cp -r "$CARRY_DIR/$_d" "$STAGE_DIR/$_d"; fi
  done
  if [ -f "$CARRY_DIR/voice/calls.json" ] && [ ! -f "$STAGE_DIR/voice/calls.json" ]; then
    mkdir -p "$STAGE_DIR/voice"; cp "$CARRY_DIR/voice/calls.json" "$STAGE_DIR/voice/calls.json"
  fi
fi
# A target holding ONLY a pre-seeded llamafile (no bridge.py —
# the documented skip: the operator fetched the binary
# themselves, or a bench pre-seeds it) is neither an update
# nor a fresh tree above, so neither branch inherited the
# binary and the download below fired for a file already
# sitting at the target. Inherit it here.
if [ -z "$IS_UPDATE" ] && [ -f "$INSTALL_DIR/navi.llamafile" ] && [ ! -f "$STAGE_DIR/navi.llamafile" ]; then
  ln "$INSTALL_DIR/navi.llamafile" "$STAGE_DIR/navi.llamafile" 2>/dev/null || cp "$INSTALL_DIR/navi.llamafile" "$STAGE_DIR/navi.llamafile"
  echo "    navi.llamafile already present at the target — keeping it (no download)"
fi
# The payload, FROM the manifest: every payload file lands;
# every seed-config file lands only where the tree has none.
while IFS=$'\t' read -r _p _c _h; do
  [ -n "$_p" ] || continue
  case "$_c" in
    payload)
      mkdir -p "$STAGE_DIR/$(dirname "$_p")"
      cp "$SRC_DIR/$_p" "$STAGE_DIR/$_p"
      ;;
    seed-config)
      if [ ! -f "$STAGE_DIR/$_p" ]; then
        mkdir -p "$STAGE_DIR/$(dirname "$_p")"
        cp "$SRC_DIR/$_p" "$STAGE_DIR/$_p"
      fi
      ;;
  esac
done <<EOF_MANIFEST
$(manifest_rows)
EOF_MANIFEST
find "$STAGE_DIR" -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
echo "    payload placed from the manifest"

# Generated files: the desktop entry and the service units are
# templates in the package; the real ones are generated here,
# into the stage, carrying the FINAL install path.
mkdir -p "$STAGE_DIR/config/dhd" "$STAGE_DIR/config/mesh" "$STAGE_DIR/config/chats" "$STAGE_DIR/voice/models" "$STAGE_DIR/systemd"
sed -e "s|__INSTALL_DIR__|$INSTALL_DIR|g" "$SRC_DIR/assets/navi-apex.desktop" > "$STAGE_DIR/assets/navi-apex.desktop"
if [ "$STARTUP" = "boot" ]; then
  cat > "$STAGE_DIR/systemd/navi-llamafile.service" <<EOF_UNITS
[Unit]
Description=Navi llamafile server (Apex)
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/run-llamafile.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF_UNITS
  cat > "$STAGE_DIR/systemd/navi-bridge.service" <<EOF_UNITS
[Unit]
Description=Navi bridge (Apex dashboard + API)
After=network.target navi-llamafile.service
Wants=navi-llamafile.service

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/start.sh --headless
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF_UNITS
fi

# The model file: carried across above when one exists; a first
# install downloads it into the STAGE — a failed download aborts
# here, with the live tree (if any) entirely untouched.
if [ -f "$STAGE_DIR/navi.llamafile" ] && is_html_file "$STAGE_DIR/navi.llamafile"; then
  rm -f "$STAGE_DIR/navi.llamafile"
fi
if [ ! -f "$STAGE_DIR/navi.llamafile" ]; then
  echo "==> Downloading the Navi llamafile"
  echo "    from: $LLAMAFILE_URL"
  if ! curl -fL -o "$STAGE_DIR/navi.llamafile" "$LLAMAFILE_URL"; then
    echo "ERROR: the model download failed — aborting with the live tree untouched." >&2
    echo "       The staged tree is left at $STAGE_DIR for inspection; nothing was stopped or replaced." >&2
    exit 1
  fi
  if is_html_file "$STAGE_DIR/navi.llamafile"; then
    rm -f "$STAGE_DIR/navi.llamafile"
    echo "ERROR: the download produced an HTML page, not the llamafile binary." >&2
    echo "       Expected the file itself from: $LLAMAFILE_URL" >&2
    exit 1
  fi
fi
chmod +x "$STAGE_DIR/navi.llamafile" 2>/dev/null || true
chmod +x "$STAGE_DIR/bridge.py" "$STAGE_DIR/start.sh" "$STAGE_DIR/run-llamafile.sh" 2>/dev/null || true
[ -f "$STAGE_DIR/install.sh" ] && rm -f "$STAGE_DIR/install.sh" || true


# Record the chosen startup mode in the installed config — and
# re-stamp the two fields that describe THIS package on THIS machine:
# the bridge port and the install directory. A config carried across
# from an older install (the migration above, or any plain reinstall)
# still names the old build's port and the old location; left alone,
# the bridge once bound that stale port while its launcher polled
# the new one. The operator's own settings stay untouched.
$SUDO python3 - "$STAGE_DIR/config/navi.config.json" "$STARTUP" "$INSTALL_DIR" "8675" <<'PY'
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
$SUDO python3 - "$STAGE_DIR/config/navi.config.json" "$STAGE_DIR/hardware-profile.log" <<'PY'
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

# The version witnesses, stamped into the STAGED config (the
# #104 discipline, kept): the config's version record is written
# here — into the stage, before the swap — so a failure anywhere
# before promotion leaves the live tree's witnesses entirely the
# old build's, and the swap lands every witness together.
python3 - "$STAGE_DIR/config/navi.config.json" "$STAGE_DIR/VERSION" <<'PY'
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



# DHD prerequisites land in the STAGE's cert home (the function
# is the proven one; only its target home is the stage's, and its
# DHD-PREREQS: summary line is printed exactly as the updater's
# apply helper expects to read it back).
DHD_CERT_HOME="$STAGE_DIR/config/dhd"
install_dhd_prereqs



# --- The stop, the refresh, the swap ---------------------------
# Only NOW — the stage complete and verified — is the running
# bridge stopped, with the proven machinery. If the port cannot
# be cleared, the install aborts with the live tree untouched
# and the stage left for inspection.
echo "==> Stopping any bridge still running from the live tree"
if ! stop_bridge "$INSTALL_DIR"; then
  echo "ERROR: the previous bridge could not be stopped — aborting with the live tree untouched." >&2
  echo "       The staged tree is left at $STAGE_DIR for inspection." >&2
  exit 1
fi
stop_shell "$INSTALL_DIR" || true
# The final refresh: state written by the bridge in its last
# moments (chats, Mesh and federation state, config) is copied
# from the now-stopped live tree into the stage, so the swap
# loses nothing the copy at assembly time could have raced.
if [ -n "$IS_UPDATE" ] && [ -z "$FRESH" ]; then
  # navi.config.json is EXCLUDED from the refresh: the stage's
  # copy already carries the assembly-time operator state plus
  # this install's restamps (startup, port, install dir, the
  # version stamps and the fresh hardware profile); the live
  # copy's installer-owned fields are the OLD build's. Every
  # other config file — chats, Mesh and federation state, the
  # Vault, DHD certificates, Soul and Memory — refreshes.
  (cd "$INSTALL_DIR/config" && tar --exclude='./navi.config.json' -cf - .) | (cd "$STAGE_DIR/config" && tar --no-same-owner -xf -) 2>/dev/null || true
  [ -d "$INSTALL_DIR/chips" ] && (cd "$INSTALL_DIR/chips" && tar -cf - .) | (mkdir -p "$STAGE_DIR/chips" && cd "$STAGE_DIR/chips" && tar --no-same-owner -xf -) 2>/dev/null || true
  [ -d "$INSTALL_DIR/rag-packs" ] && (cd "$INSTALL_DIR/rag-packs" && tar -cf - .) | (mkdir -p "$STAGE_DIR/rag-packs" && cd "$STAGE_DIR/rag-packs" && tar --no-same-owner -xf -) 2>/dev/null || true
  [ -f "$INSTALL_DIR/voice/calls.json" ] && cp "$INSTALL_DIR/voice/calls.json" "$STAGE_DIR/voice/calls.json" 2>/dev/null || true
fi

echo "==> Promoting the staged tree — one act"
rm -rf "$PREV_DIR" 2>/dev/null || true
if [ -d "$PREV_DIR" ]; then
  # A stale previous tree that will not delete (foreign-owned
  # files) must not sit under the promotion rename — mv would
  # nest the live tree INSIDE it. Rename it aside instead; the
  # rename needs only the parent directory, which the swap
  # already depends on.
  mv "$PREV_DIR" "$PARENT_DIR/.apex-prev-kept-$(date +%s)" 2>/dev/null || {
    echo "ERROR: a previous tree at $PREV_DIR can neither be deleted nor moved aside — nothing was changed; the staged tree is left at $STAGE_DIR." >&2
    exit 1
  }
  echo "    (a previous tree that would not delete was moved aside, not nested into)"
fi
if [ -d "$INSTALL_DIR" ]; then
  if ! mv "$INSTALL_DIR" "$PREV_DIR"; then
    echo "ERROR: the live tree could not be moved aside — nothing was changed; the staged tree is left at $STAGE_DIR." >&2
    exit 1
  fi
fi
if ! mv "$STAGE_DIR" "$INSTALL_DIR"; then
  echo "ERROR: the promotion rename failed — restoring the previous tree." >&2
  [ -d "$PREV_DIR" ] && mv "$PREV_DIR" "$INSTALL_DIR"
  exit 1
fi

# --- The self-check, in the product ----------------------------
# The install stands or rolls back on the product's own verdict
# against the live tree — stamps, manifest hashes, engine
# imports — not on any version proxy kept by this script.
echo "==> The product verifies itself (self-check)"
SC_OUT="$(python3 "$INSTALL_DIR/bridge.py" --self-check 2>&1)" || SC_OUT="$SC_OUT"
echo "    $SC_OUT"
case "$SC_OUT" in
  *"SELF-CHECK OK:"*)
    echo "    self-check passed — the install stands"
    ;;
  *)
    echo "ERROR: the new tree failed its self-check — rolling back to the previous version, whole." >&2
    stop_bridge "$INSTALL_DIR" 2>/dev/null || true
    rm -rf "$FAILED_DIR"
    mv "$INSTALL_DIR" "$FAILED_DIR"
    if [ -d "$PREV_DIR" ]; then
      mv "$PREV_DIR" "$INSTALL_DIR"
      echo "    the previous version is back in place at $INSTALL_DIR; the failed tree is kept at $FAILED_DIR" >&2
      if [ -n "${STOPPED_BRIDGE:-}" ] && [ -z "$NO_RELAUNCH" ]; then
        nohup "$INSTALL_DIR/start.sh" >> "$INSTALL_DIR/start.log" 2>&1 &
        echo "    the previous version was relaunched" >&2
      fi
    else
      echo "    there was no previous version; the failed tree is kept at $FAILED_DIR and $INSTALL_DIR is empty" >&2
      rmdir "$INSTALL_DIR" 2>/dev/null || true
    fi
    exit 1
    ;;
esac



# --- Post-swap provisioning (operator context, always) ---------
# Everything below runs as the operator against the live tree:
# boot services, the menu entry, the shell build, her voice. None
# of it can strand the install — the tree is already verified —
# and none of it is ever run under sudo, so systemctl --user
# always talks to the operator's own bus (incident 17).
PROVISIONED_MARK="$INSTALL_DIR/.apex-provisioned"
printf '{"operator": "%s", "at": "%s", "build": "%s"}\n' "$OPERATOR" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$STAMP" > "$PROVISIONED_MARK"


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
    install_shell_binary "$BOX_BUILD_DIR/target/release/navi-apex-shell"
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
    install_shell_binary "$INSTALL_DIR/shell/target/release/navi-apex-shell"
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



# The old location's files are removed only now that the new
# tree is verified live (the migration's standing rule).
if [ -n "$MIGRATED" ] && [ -d "$OLD_DIR" ]; then
  rm -rf "$OLD_DIR"
  echo "    the old location ($OLD_DIR) is removed — everything lives at $INSTALL_DIR now"
fi
rm -rf "$CARRY_DIR"

# --- Relaunch what the install stopped, and verify it ----------
# (The build .91 discipline, kept: a bridge stopped by this
# install is relaunched through start.sh and the answering
# bridge's stamp must be the NEW build's before the install
# calls itself done. --no-relaunch says so plainly instead.)
RELAUNCH_OK=""
if [ -n "${STOPPED_BRIDGE:-}" ] && [ -z "$NO_RELAUNCH" ]; then
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
    echo "    verified: the bridge answering on port 8675 is the new build ($NEW_STAMP)"
  else
    echo "    WARNING: the bridge was relaunched but the new build's stamp could not be confirmed" >&2
    echo "    on port 8675 within 90 seconds. The tree itself passed its self-check; see start.log" >&2
    echo "    in $INSTALL_DIR for the launcher's account of the start." >&2
  fi
elif [ -n "${STOPPED_BRIDGE:-}" ] && [ -n "$NO_RELAUNCH" ]; then
  echo "==> --no-relaunch: the bridge this install stopped stays stopped, by your word."
fi

# The success record — written only now, after the self-check
# passed: an install whose record exists is an install the
# product itself confirmed.
printf '{"operator": "%s", "at": "%s", "build": "%s", "version": "%s", "selfCheck": "passed"}\n' \
  "$OPERATOR" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$STAMP" "$(cat "$INSTALL_DIR/VERSION")" \
  > "$INSTALL_DIR/.apex-install-record"
# The previous tree retires only after the new one is verified.
# Best-effort by design: if it holds files this operator cannot
# delete (root-owned leftovers of a past sudo repair, incident
# 16), the install still stands — the kept tree is named, with
# the one command that removes it.
rm -rf "$PREV_DIR" 2>/dev/null || true
if [ -d "$PREV_DIR" ]; then
  echo "NOTE: the previous install is kept at $PREV_DIR" >&2
  echo "      It holds files not owned by $OPERATOR (a past sudo repair leaves exactly this), so this" >&2
  echo "      operator cannot delete it. The new install is complete without it. Remove it with:" >&2
  echo "        sudo rm -rf $PREV_DIR" >&2
fi

echo ""
echo "== Apex build $BUILD_STAMP is installed at $INSTALL_DIR"
echo "   Verified by the product itself: $(python3 -c "import json; print(json.load(open('$INSTALL_DIR/config/install-self-check.json'))['sentence'])" 2>/dev/null || echo 'self-check passed')"
if [ "$STARTUP" = "boot" ]; then
  echo "   Startup: at boot (systemd user services: navi-llamafile, navi-bridge)"
else
  echo "   Startup: when you launch the app (the Apex entry in your app menu, or $INSTALL_DIR/start.sh)"
fi
