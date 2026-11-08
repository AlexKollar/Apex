#!/usr/bin/env bash
# Starts Navi: llamafile server (launch mode), the bridge, and her
# window. Apex stands alone now: the front door is the Tauri
# shell binary (navi-apex-shell, built by the installer from shell/)
# opening her own window on the bridge's dashboard — no web browser
# is opened. The browser openers survive only as the fallback for an
# install where the shell was never built (no Rust toolchain).
# Launch command: ./navi.llamafile --server --v2 plus the runtime
# flags from the hardware profile in config/navi.config.json
# (HW_FLAGS below; the fluid floor when the config has no profile).
set -euo pipefail
cd "$(dirname "$0")"
PORT="${NAVI_LLAMAFILE_PORT:-8080}"
HW_FLAGS="$(python3 - <<'PY' 2>/dev/null || echo "--ctx-size 4096 --threads 4 --batch-size 512"
import json
try:
    with open("config/navi.config.json") as f:
        cfg = json.load(f)
    rt = cfg.get("runtime") or {}
    hp = (cfg.get("hardware_profile") or {}).get("settings") or {}
    ctx = int(rt.get("ctx_size") or hp.get("ctxSize") or 4096)
    thr = int(rt.get("threads") or hp.get("threads") or 4)
    bat = int(rt.get("batch_size") or hp.get("batchSize") or 512)
    gpu = int(rt.get("gpu_layers") if rt.get("gpu_layers") is not None else (hp.get("gpuLayers") or 0))
    out = f"--ctx-size {ctx} --threads {thr} --batch-size {bat}"
    if gpu > 0:
        out += f" --n-gpu-layers {gpu}"
    print(out)
except Exception:
    print("--ctx-size 4096 --threads 4 --batch-size 512")
PY
)"


# Everything this launcher decides also lands in start.log beside
# the app. A menu/desktop launch has no terminal: the echoes go
# nowhere there, and a window that failed to open used to fail
# in total silence while the bridge ran fine. The log is how a
# menu launch explains itself after the fact.
LOG_FILE="start.log"
log_line() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE" 2>/dev/null || true; }
log_line "launch: Apex starting (llamafile port $PORT, bridge port 8675)"

if curl -s --max-time 2 "http://localhost:$PORT/" >/dev/null 2>&1; then
  # Check first, always: a llamafile server is already answering —
  # started at boot, by an earlier launch, or by hand — so leave it
  # alone and just run the app. Spawning a second copy would only
  # fail to bind the port and litter the log with a dead start.
  echo "navi.llamafile is already running on port $PORT — leaving it alone."
  log_line "llamafile: already running on port $PORT — left alone"
elif [ -x ./navi.llamafile ]; then
  echo "navi.llamafile is not running — starting it: ./navi.llamafile --server --v2 $HW_FLAGS (output: navi.llamafile.log) …"
  log_line "llamafile: not running — starting ./navi.llamafile --server --v2 $HW_FLAGS (hardware profile from config/navi.config.json)"
  # shellcheck disable=SC2086
  ./navi.llamafile --server --v2 $HW_FLAGS >> navi.llamafile.log 2>&1 &
  LLAMA_PID=$!
  for i in $(seq 1 120); do
    if curl -s --max-time 2 "http://localhost:$PORT/" >/dev/null 2>&1; then break; fi
    if ! kill -0 "$LLAMA_PID" 2>/dev/null; then
      echo "navi.llamafile exited during startup — last log lines:" >&2
      tail -n 5 navi.llamafile.log >&2 || true
      echo "The bridge can retry the start: open the UI and click Connect." >&2
      break
    fi
    sleep 1
  done
else
  echo "navi.llamafile is not in $(pwd) — the model server cannot start until the installer downloads it." >&2
fi

# The bridge runs on the voice venv's Python when that venv exists:
# it is a plain Python 3 with the (optional) speech engines
# installed, so her voice works; without the venv, the system
# python3 runs the same bridge, stdlib-only, voice unavailable
# until the engines are installed for it.
PYTHON="python3"
if [ -x "voice/venv/bin/python" ]; then
  PYTHON="voice/venv/bin/python"
fi

# The bridge exits with code 75 when it has been replaced — a newer
# bridge.py landed on disk, or a newer bridge claimed the port — so
# supervise it: relaunch on 75 and an update takes over on its own
# instead of leaving a zombie bridge answering with old code.
supervise_bridge() {
  while true; do
    code=0
    "$PYTHON" bridge.py || code=$?
    [ "$code" -eq 75 ] || break
    echo "Bridge replaced — relaunching the current build…"
    sleep 1
  done
}

BRIDGE_PORT="8675"
echo "Starting bridge on http://localhost:$BRIDGE_PORT …"
supervise_bridge &

# Her own window — the standalone Tauri shell — is the front door.
# It is single-instance (a second launch focuses the window that is
# already open) and it loads the dashboard from the bridge, so the
# bridge verification below still gates the open exactly as it did
# for the browser. Only an install where the shell was never built
# (no Rust toolchain at install time) falls back to a browser; the
# dashboard itself stays reachable at the same URL regardless.
# A shell binary is launched only when the stamp beside it covers
# the shell sources beside it — the same hash the installer writes
# after a successful build. A binary from an older build is a
# different app wearing this one's name. Verdicts: 0 =
# verified current, 1 = verified stale (or no binary), 2 = cannot
# verify (no hashing tool) — unverifiable launches as before,
# because a missing sha256sum must not strand the operator.
shell_sources_hash() {
  local dir="shell"
  local files="Cargo.toml build.rs src/main.rs tauri.conf.json icons/icon.png README.md"
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

shell_is_current() {
  [ -x "./navi-apex-shell" ] || return 1
  local h s
  h="$(shell_sources_hash)"
  if [ -z "$h" ]; then return 2; fi
  s=""
  if [ -f "./navi-apex-shell.stamp" ]; then s="$(cat ./navi-apex-shell.stamp)"; fi
  if [ "$s" = "$h" ]; then return 0; fi
  return 1
}

open_window() {
  if [ -x "./navi-apex-shell" ]; then
    local verdict=0
    shell_is_current || verdict=$?
    if [ "$verdict" -eq 1 ]; then
      log_line "window: the shell binary beside start.sh is STALE — built from older shell sources (its stamp does not cover shell/) — not launching it. Rebuild it (cd shell && cargo build --release) or re-run the installer."
      log_line "window: falling back to the browser until the shell is rebuilt"
      open_browser_fallback
      return 0
    fi
    if [ "$verdict" -eq 2 ]; then
      log_line "window: cannot verify the shell binary against its build stamp (no sha256sum/shasum) — launching it as-is"
    fi
      log_line "window: opening the standalone Apex window (Tauri shell)"
      ./navi-apex-shell >>"$LOG_FILE" 2>&1 &
    return 0
  fi
  log_line "window: no shell binary beside start.sh — falling back to the browser (build it with: cd shell && cargo build --release)"
  open_browser_fallback
}

open_browser_fallback() {
  local url="http://localhost:$BRIDGE_PORT"
  # Try each opener in turn and CHECK that it worked. An opener
  # that merely exists but fails — xdg-open with no default
  # browser registered answers "no method available" and exits
  # nonzero — must fall through to the next opener instead of
  # ending the attempt. That unchecked single xdg-open call was
  # the menu-launch failure: the bridge came up, the dashboard
  # was live, and the browser step died without a sound where
  # nobody could see it (a menu launch has no terminal).
  if command -v xdg-open >/dev/null 2>&1 && xdg-open "$url" >>"$LOG_FILE" 2>&1; then
    log_line "browser: opened $url with xdg-open"
    return 0
  fi
  if command -v gio >/dev/null 2>&1 && gio open "$url" >>"$LOG_FILE" 2>&1; then
    log_line "browser: opened $url with gio open"
    return 0
  fi
  if command -v sensible-browser >/dev/null 2>&1 && sensible-browser "$url" >>"$LOG_FILE" 2>&1; then
    log_line "browser: opened $url with sensible-browser"
    return 0
  fi
  if command -v open >/dev/null 2>&1 && open "$url" >>"$LOG_FILE" 2>&1; then
    log_line "browser: opened $url with open"
    return 0
  fi
  local b
  for b in firefox chromium chromium-browser google-chrome google-chrome-stable brave-browser microsoft-edge; do
    if command -v "$b" >/dev/null 2>&1; then
      "$b" "$url" >>"$LOG_FILE" 2>&1 &
      log_line "browser: launched $b with $url"
      return 0
    fi
  done
  log_line "browser: NO opener worked — the dashboard is live at $url; open it manually. (Tried xdg-open, gio, sensible-browser, open, and the common browser binaries; their output is above in this log.)"
  echo "Could not open a browser automatically — the dashboard is live at $url" >&2
  return 1
}

# Open her window once the process answering on the bridge port
# is a Navi bridge. Any build counts: when the answering bridge
# is an older or newer build than this launcher, its dashboard
# is still Navi — it carries the BRIDGE OUT OF DATE banner for
# exactly that case — and demanding an exact stamp match here
# stranded the operator with a running app and no window, the
# refusal explained only to a terminal a menu launch doesn't
# have. A page that is NOT a Navi bridge at all still blocks
# the open, and gets named — in the log as well as the terminal.
BRIDGE_STAMP="2026-11-07.55"
OPENED=""
for i in $(seq 1 40); do
  STATUS=$(curl -s --max-time 2 "http://localhost:$BRIDGE_PORT/api/status" 2>/dev/null || true)
  if printf '%s' "$STATUS" | grep -q '"app": "Navi: Apex"'; then
    OPENED=1
    STAMP_NEEDLE="\"bridge\": \"$BRIDGE_STAMP\""
    if printf '%s' "$STATUS" | grep -qF "$STAMP_NEEDLE"; then
      log_line "verify: this build's bridge ($BRIDGE_STAMP) is answering on port $BRIDGE_PORT"
    else
      log_line "verify: a Navi bridge of a different build than $BRIDGE_STAMP is answering on port $BRIDGE_PORT — opening it anyway; its dashboard flags the mismatch"
    fi
    break
  fi
  sleep 1
done
if [ -n "$OPENED" ]; then
  open_window || true
else
  TITLE=$(curl -s --max-time 2 "http://localhost:$BRIDGE_PORT/" 2>/dev/null | grep -oiE '<title[^>]*>[^<]*</title>' | head -1 | sed -E 's/<[^>]+>//g' || true)
  if [ -n "$TITLE" ]; then
    log_line "verify: port $BRIDGE_PORT is held by a different program (its page is titled "$TITLE") — window not opened"
    echo "Not opening the window: http://localhost:$BRIDGE_PORT is served by a different program (its page is titled \"$TITLE\")," >&2
    echo "not by the Apex bridge — her window would show that program's page, not this dashboard." >&2
    echo "Quit the program holding the port (find it with: lsof -i :$BRIDGE_PORT), then launch Apex again." >&2
  elif curl -s --max-time 2 http://localhost:8765/api/status 2>/dev/null | grep -q '"app": "Navi: Apex"'; then
    # A Navi bridge answering on the PREVIOUS package's port can only
    # be a bridge process from that older install still running (this
    # build's bridge binds $BRIDGE_PORT and nothing else). Name it
    # and say how to clear it instead of the generic shrug — this is
    # the exact shape of the port-change stranding: the old bridge
    # alive on 8765, the new launcher polling $BRIDGE_PORT in vain.
    log_line "verify: a previous install's Navi bridge is answering on the old port 8765 — window not opened"
    echo "Not opening the window: a Navi bridge from a previous install is still running on the old port, http://localhost:8765," >&2
    echo "and this build's bridge never took port $BRIDGE_PORT. Stop the old bridge (find it with: lsof -i :8765, or run:" >&2
    echo "pkill -f bridge.py), then launch Apex again." >&2
  else
    log_line "verify: no Navi bridge answered on port $BRIDGE_PORT — window not opened; see the bridge output in this folder"
    echo "The Navi bridge did not answer on http://localhost:$BRIDGE_PORT — not opening the window. See the bridge output above." >&2
  fi
fi
wait
