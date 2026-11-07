# The standalone window

Apex opens in her own window — no web browser. The window is a
small [Tauri](https://tauri.app) shell: Rust plus the operating
system's own webview (WebKitGTK on Linux, WKWebView on macOS, WebView2
on Windows), so no Chromium is bundled and the footprint stays small.

The shell changes nothing underneath it. The bridge and the
llamafile run exactly as before, and the window simply loads the
dashboard the bridge serves at http://localhost:8675:

- **Check-first startup** lives in the launcher (start.sh):
  the bridge and the llamafile start only when they are
  not already running, and boot-mode installs keep their service
  behavior. The shell itself also waits up to ~60s for the bridge to
  answer before its window appears, so a cold start lands on the
  dashboard, not an error page.
- **Single instance**: launching the app again while it is running
  hands the launch to the existing instance instead of opening a
  duplicate (tauri-plugin-single-instance).
- **Name and icon**: the window is titled "Apex" and carries
  the app icon (icons/icon.png; the package's .ico/.icns renditions
  are carried for the planned Windows/macOS builds).

## Her window, and nothing else

The shell is one window. Closing it quits the app; launching again
while it is running focuses the existing window. There is no tray
icon, no mini terminal, and no login autostart — a tray round was
built and tested on the operator's machine, then reverted at his
call; the idea is parked on the roadmap for later. (Installers
from this build remove the tray login autostart earlier builds
registered, so an upgraded machine starts nothing at login.) The
launchers run the binary only when its build stamp covers the
shipped shell sources, and a failed rebuild retires the previous
binary to navi-apex-shell.stale, so an older shell can never be
launched as if it were this build.

## The documentation's own window

One exception to "one window", made on purpose: the dashboard's
Docs **Pop out** opens the documentation in another window
entirely. A webview refuses the page's own `window.open`, so the
shell does it natively — the dashboard invokes the shell's
`open_docs_window` command (tauri.conf.json sets
`withGlobalTauri` so the dashboard can reach the shell's own
commands through `window.__TAURI__.core.invoke`), and the shell
creates a second window labeled `docs`, titled "Apex —
Documentation", loading the same bridge dashboard flagged
`#popdocs`, which boots into the docs-only view. Popping out
again raises that window instead of duplicating it;
`close_docs_window` (Pop back in, from either window) closes it,
and `docs_window_open` lets the main window notice when the
operator closes the docs window directly so the wiki docks back
into the Docs view. Closing the main window still quits the app,
docs window and all.

## Microphone in the shell

Calls and push-to-talk need the webview's getUserMedia. On Linux,
WebKitGTK denies permission requests by default and wry never
answers them, which left the mic silently dead in the shell while
the same dashboard worked in a browser. The shell answers the
webview's permission requests directly and allows them: the only
page these webviews load is the operator's own local dashboard.
The shell's code also covers the other platforms' permission
models, ready for when their installers return (a macOS bundle
carries the NSMicrophoneUsageDescription string the OS consent
prompt needs; on Windows, WebView2 shows its standard prompt) —
today only the Linux install ships.

## Building

The installer builds the shell during install — but only when it
has to. A completed build is stamped: the installer records a hash
of the shipped shell sources beside the binary
(navi-apex-shell.stamp). On a later install, if the binary exists,
passes a basic sanity check, and the stamp matches the sources this
package ships, the cargo build is skipped and the installer says
so. Changed sources, a missing or suspect binary, or --fresh
always rebuild. If no Rust toolchain (cargo) is on the machine, the
installer first installs one with [rustup](https://rustup.rs) — the
official installer, per-user (no sudo/admin), non-interactive,
minimal profile — refreshes PATH, and builds with that toolchain in
the same run. An existing toolchain is used as-is. By hand it is
just:

    cd shell
    cargo build --release
    # binary: target/release/navi-apex-shell
    # (navi-apex-shell.exe on Windows)

and the installer copies the binary beside start.sh as
`navi-apex-shell`. The
launchers prefer it whenever it exists. Linux builds need the
WebKitGTK development packages (e.g. libwebkit2gtk-4.1-dev plus
libgtk-3-dev, librsvg2-dev, libayatana-appindicator3-dev on
Debian/Ubuntu) — the install log (shell/shell-build.log, which also
carries the rustup attempt) names
whatever is missing.

Only when Rust cannot be had at all — the rustup download or run
failed, no network being the usual cause — does the install finish
without the window: it says so plainly, and start.sh
falls back to opening the dashboard in the default browser, as before.
The plain web dashboard remains reachable at
http://localhost:8675 at all times — it is a fallback
surface, just no longer the front door.
