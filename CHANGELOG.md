# Changelog

All notable changes to Apex are recorded here. Releases are alpha until the first stable release.

## 0.1.3 (alpha)

Release tag: v0.1.3a. Everything from the phone round (builds .62–.68), live-confirmed by Alex on his phone and desktop before this release was cut.

### Local server and phone chrome

- **Local server**: it serves only your local network, never the outside world. Turning it on is one flip: the choice saves, Apex restarts her bridge bound for the network, and the Settings row confirms the live state from the answering bridge.
- The Local network access passcode is served only to connections from Apex's own machine — a phone on the LAN receives no code from the status sidebar; you read it off the desktop and type it into the phone.
- A "Local network access" section sits in the status sidebar under the Llamafile block — indicator, the LAN link, and the passcode when it is yours to see; off reads "This machine only" with a plain pointer to Settings → System.
- Phone chrome: a persistent top bar with the menu button and "Apex | Powered by Navi" clustered left and the status toggle alone at the right edge; the main menu slides in from the left and the status sidebar from the right, both full phone-screen width, and both menus hide themselves once you pick a page. The menu button is a compact square that never stretches.

### Chat on the phone

- The CLI | Navi toggle persists: the latched mode survives sends, page switches, and reopening the app, in the shipped app and the test bench alike.
- No focus zoom anywhere: tapping the chat bar — or any field — no longer zooms the page on mobile. The viewport is pinned, double-tap zoom is off, and every editable control renders at 16px on touch devices, the size below which mobile browsers zoom on focus.
- The composer's placeholders are sized for phones, so the whole hint sits visible end to end instead of clipping mid-word.
- The composer is tidier: the hint paragraph under the chat bar is gone, and "Press enter to send." now sits beside the CLI | Navi toggle; Docs gets a full-width page dropdown on phones.

## 0.1.1 (alpha)

### Chat, CLI and themes

- Finished exchanges now fold into reopenable output cards: a folded terminal block shows its command, its exit state and its first output line, and long replies fold the same way — the history stays in the thread, and nothing leaves Navi's context.
- The composer completes the zsh set: a persistent command history, Up/Down recall when the completion list is closed, Ctrl+R reverse search, completion for paths and arguments (not just the command word), the emacs editing chords, and history expansion (!!, !$, !<n>) that always shows you the expansion before anything runs.
- Syntax highlighting is tuned per theme: commands, flags, paths, strings, numbers and operators are coloured in the composer and in the thread, with a palette chosen for each of the eleven themes.
- A command now shows exactly once — in your line. The shell block carries the output only.
- Six new themes join the picker: Dark Liquid Glass (resource-light — real blur only where it is cheap, solid fallbacks where it is not), Nocturne Row, Abyss, Case File, Blood Moon and Phosphor Amber. Nordic dark remains the default.

### Chips, packs and GitHub

- Publish to GitHub works end to end for chips and knowledge packs: Navi creates the repo, applies the navi-chips / navi-rag topic, and uploads the files; publishing the release is the only step left to you, and the version tag is created with that publish.
- GitHub sign-in for publishing is durable now: the full token set is stored and renewed, instead of quietly expiring and failing the next publish.
- Local Chips is the one place to manage the chips on this machine — Run, Download .png, Edit in Studio, Edit README, Export, Publish, Check for updates and Delete all live on its cards; the catalog is for discovering and installing.
- The GitHub catalogs reconcile what is already on this machine: an installed pack or chip reads INSTALLED with its Install button grayed out, while a genuine update stays available.
- Knowledge packs wear the same flip cards as chips, README on the back; the GitHub section's issues and pulse entries are cards too, and clicking an issue opens it.
- Edit in Studio now sits on the chip cards themselves, and a first launch no longer strands the chat in CLI-only mode while the llamafile loads — the view heals itself when she arrives.

### Fixes since 0.1.0

- The chat composer's placeholder follows the CLI/Navi latch as you flip it; Clear chat lives in the composer's hint row; the Chat view's stray header bar is gone.
- When a link cannot open in the desktop shell, the app says so in a warning toast that shows the address and points you at the Web UI (http://localhost:8675), where links open normally.

## 0.1.0 (alpha)

- First public alpha release of Apex — Powered by Navi.
