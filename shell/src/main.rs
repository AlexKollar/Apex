// Apex — standalone shell.
//
// A single window on the dashboard the local bridge serves at
// http://localhost:8675. The bridge and the llamafile are
// untouched: start.sh starts them check-first (only when
// not already running) before this shell is launched, and boot-mode
// installs keep their services as they were.
//
// The window is titled "Apex" and carries the app icon.
// Closing it quits the app. There is no tray icon, no mini
// terminal, and no login autostart: a tray round was built and
// tested on the operator's machine, then reverted at his call —
// the tray/mini-terminal idea is parked on the roadmap, not gone.
// She runs when the operator launches her (application menu,
// start.sh) and not before.
//
// Single instance: the single-instance plugin is registered first,
// so launching the app again while she is running hands the launch
// to the existing instance, which raises her window, instead of
// spawning a duplicate.
//
// The documentation's own window: the dashboard's Docs pop-out
// opens another window entirely. A webview refuses window.open,
// so the shell does it natively instead — the dashboard invokes
// open_docs_window (window.__TAURI__ is exposed for exactly this),
// and the shell creates — or raises, if it already lives — a
// second window labeled "docs" on the same bridge dashboard
// flagged #popdocs, which boots into the docs-only view.
// close_docs_window and docs_window_open complete the round trip
// the dashboard's Pop back in and its dock polling drive.
//
// External links: the GitHub view's Issues page must open in the
// operator's browser, not inside her webview — open_external_url
// hands an https://github.com/ address (and nothing else) to the
// OS opener for exactly that.
//
// The GitHub section's Roadmap and Discussions tabs get windows
// of their own instead (open_github_window): the project board
// and the discussions live inside the app as native webview
// windows — a top-level load, which GitHub serves, rather than
// an embedded frame, which it refuses.
//
// Microphone: WebKitGTK denies webview permission requests by
// default and wry never answers them, so getUserMedia (push-to-talk,
// calls) silently failed in the shell while the same dashboard
// worked in a browser. On Linux the shell therefore answers the
// webview's permission requests directly (grant_media_permissions):
// the only page this webview ever loads is the operator's own
// local dashboard, so its mic requests are allowed. Other
// platforms use their OS prompt; macOS additionally needs the
// usage-description string the installer's app bundle carries.
//
// Before the window is created, main() waits (up to ~60s) for the
// bridge to answer /api/status as Apex, so a cold start lands
// on the dashboard rather than a connection-error page. If the
// bridge never answers, the app starts anyway and the webview's
// error page says why — start.log beside the app carries the
// launcher's side of the story.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::{Read, Write};
use std::net::TcpStream;
use std::time::{Duration, Instant};
use tauri::{Manager, WebviewUrl, WebviewWindow, WebviewWindowBuilder};

const BRIDGE_ADDR: &str = "127.0.0.1:8675";

fn bridge_answers() -> bool {
    let addr = match BRIDGE_ADDR.parse() {
        Ok(a) => a,
        Err(_) => return false,
    };
    let mut stream = match TcpStream::connect_timeout(&addr, Duration::from_millis(800)) {
        Ok(s) => s,
        Err(_) => return false,
    };
    let _ = stream.set_read_timeout(Some(Duration::from_millis(800)));
    let _ = stream.set_write_timeout(Some(Duration::from_millis(800)));
    if stream
        .write_all(b"GET /api/status HTTP/1.0\r\nHost: localhost\r\n\r\n")
        .is_err()
    {
        return false;
    }
    let mut buf = String::new();
    let _ = stream.take(16384).read_to_string(&mut buf);
    buf.contains("\"app\": \"Navi: Apex\"")
}

fn wait_for_bridge() {
    let deadline = Instant::now() + Duration::from_secs(60);
    while Instant::now() < deadline {
        if bridge_answers() {
            return;
        }
        std::thread::sleep(Duration::from_millis(500));
    }
}

// Answer the webview's media-permission requests with "allow" — see
// the note at the top of this file. Linux-only: it reaches the
// WebKitGTK view through wry's platform handle, which is exactly
// the layer that was leaving the dashboard's mic requests
// unanswered. On macOS / Windows the OS consent flow applies.
#[cfg(target_os = "linux")]
fn grant_media_permissions(window: &WebviewWindow) {
    let _ = window.with_webview(|webview| {
        use webkit2gtk::{PermissionRequestExt, WebViewExt};
        webview.inner().connect_permission_request(|_view, request| {
            request.allow();
            true
        });
    });
}

#[cfg(not(target_os = "linux"))]
fn grant_media_permissions(_window: &WebviewWindow) {}

fn show_main(app: &tauri::AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

const DOCS_URL: &str = "http://localhost:8675/#popdocs";

// The Docs pop-out's native half: open the documentation in
// another window entirely — a real second window of this app,
// raised instead of duplicated when it already exists.
#[tauri::command]
fn open_docs_window(app: tauri::AppHandle) -> Result<(), String> {
    if let Some(docs) = app.get_webview_window("docs") {
        let _ = docs.unminimize();
        let _ = docs.show();
        let _ = docs.set_focus();
        return Ok(());
    }
    let url: tauri::Url = DOCS_URL.parse().map_err(|e| format!("bad docs URL: {e}"))?;
    WebviewWindowBuilder::new(&app, "docs", WebviewUrl::External(url))
        .title("Apex — Documentation")
        .inner_size(900.0, 1020.0)
        .min_inner_size(560.0, 480.0)
        .center()
        .build()
        .map_err(|e| e.to_string())?;
    Ok(())
}

// Pop back in: close the documentation's window, whichever side
// of the pair asked.
#[tauri::command]
fn close_docs_window(app: tauri::AppHandle) {
    if let Some(docs) = app.get_webview_window("docs") {
        let _ = docs.close();
    }
}

// The main window polls this so a docs window the operator closed
// on its own docks the wiki back into the Docs view.
#[tauri::command]
fn docs_window_open(app: tauri::AppHandle) -> bool {
    app.get_webview_window("docs").is_some()
}

// The GitHub section's webview windows: the Roadmap tab (Alex's
// GitHub project board) and the Discussions tab open as their own
// windows of this app, the same native pattern as the Docs window
// — a webview window loads the page at the top level, which is
// exactly what GitHub refuses to do inside an embedded frame on a
// web page. The page names are fixed here, not passed in: the
// dashboard asks for "roadmap" or "discussions" and the shell
// alone decides which address that means, so this is not a
// general webview launcher either.
#[tauri::command]
fn open_github_window(app: tauri::AppHandle, page: String) -> Result<(), String> {
    let (label, url, title) = match page.as_str() {
        "roadmap" => (
            "roadmap",
            "https://github.com/users/AlexKollar/projects/9",
            "Apex — Roadmap",
        ),
        "discussions" => (
            "discussions",
            "https://github.com/AlexKollar/Apex/discussions",
            "Apex — Discussions",
        ),
        _ => return Err(format!("unknown GitHub page: {page}")),
    };
    if let Some(w) = app.get_webview_window(label) {
        let _ = w.unminimize();
        let _ = w.show();
        let _ = w.set_focus();
        return Ok(());
    }
    let parsed: tauri::Url = url.parse().map_err(|e| format!("bad GitHub URL: {e}"))?;
    WebviewWindowBuilder::new(&app, label, WebviewUrl::External(parsed))
        .title(title)
        .inner_size(1080.0, 900.0)
        .min_inner_size(560.0, 480.0)
        .center()
        .build()
        .map_err(|e| e.to_string())?;
    Ok(())
}

// Open a link in the operator's real browser, outside her window —
// the GitHub view's Issues link is the caller. The webview would
// otherwise navigate itself away from the dashboard (or refuse), and
// the Issues page belongs in a browser anyway. Restricted on
// purpose: only https://github.com/ addresses the dashboard itself
// names ever open this way — this is not a general URL launcher.
#[tauri::command]
fn open_external_url(url: String) -> Result<(), String> {
    if !url.starts_with("https://github.com/") {
        return Err("only https://github.com/ links open externally".to_string());
    }
    #[cfg(target_os = "linux")]
    let spawned = std::process::Command::new("xdg-open").arg(&url).spawn();
    #[cfg(target_os = "macos")]
    let spawned = std::process::Command::new("open").arg(&url).spawn();
    #[cfg(target_os = "windows")]
    let spawned = std::process::Command::new("rundll32")
        .arg("url.dll,FileProtocolHandler")
        .arg(&url)
        .spawn();
    spawned.map(|_| ()).map_err(|e| e.to_string())
}

fn main() {
    wait_for_bridge();
    tauri::Builder::default()
        // Registered first on purpose: when a second launch arrives,
        // the plugin hands it to this callback and the new process
        // exits — the running instance raises its window instead.
        .plugin(tauri_plugin_single_instance::init(|app, _args, _cwd| {
            show_main(app);
        }))
        .invoke_handler(tauri::generate_handler![
            open_docs_window,
            close_docs_window,
            docs_window_open,
            open_github_window,
            open_external_url
        ])
        .setup(|app| {
            if let Some(main) = app.get_webview_window("main") {
                grant_media_permissions(&main);
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running Apex");
}
