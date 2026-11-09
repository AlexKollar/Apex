# Changelog

All notable changes to Apex are recorded here. Version language, from 0.1.7 on: a full release carries the bare number (tag v0.1.7); a pre-release is an Edge build and carries the e suffix (tag v0.1.7e). Releases before 0.1.7 were cut as alphas with the a suffix — that history stands as written below.

## 0.1.7

Release tag: v0.1.7. The bundled release: the Updater round (#70) and Navi's memory from chat (#72), built together in build 2026-11-09.81, first prepped as an alpha in build .82, and re-cut as this full release — with release channels built in — in build 2026-11-09.83. The installer hardening (#75) landed in build .84, before the release went out.

### Release channels, and the new version language

- **Two channels in the Updater.** The Updater now follows a channel, chosen in the Updater view and remembered. **Stable** (the default) follows full releases only, cut from the main branch. **Edge** follows the newest release including pre-releases — test builds cut from a separate dev branch, kept apart from main — so opting into Edge is how a machine gets those builds at all. Checks and installs both run on the chosen channel.
- **Full releases wear the bare number; pre-releases are Edge.** A full release is just its number — 0.1.7, tag v0.1.7, no status word, no letter. An Edge build of a version reads 0.1.7e (tag v0.1.7e). The old alpha word and "a" suffix are retired: older VERSION files and tags written that way still read correctly everywhere, as Edge. An Edge build of a version is its preview, not an upgrade over the full release; when the full release of the same numbers lands, graduating to it is the update.
- **The current release's page, in the Updater.** The Updater gains an "About this release" dropdown carrying everything the GitHub release page offers for the version you are running — release name, tag, Edge/full badge, published date, the link, the package asset, and the full patch notes rendered in place — fetched alongside the update check.

### The installer stops dying in shells with no terminal (#75)

- **A terminal counts only if it opens.** The installer asks its two questions (startup mode, her voice) only when it can actually hear the answer: the test is opening /dev/tty, not checking whether the device node is readable. In a shell with no controlling terminal — her own CLI shell is the field-proven case — the old readability check passed and the read died mid-prompt ("/dev/tty: No such device or address"), killing a staged v0.1.7a install on NeoArcadia after the bridge had already stopped for it. A terminal-less run now gets the plain instruction instead — re-run with --startup / --voice — and a terminal that stops answering mid-question ends the same clean way.
- **The update path carries the answers as flags.** The one-click apply and the manual fallback command both pass --startup and --voice from the install's own settings (the config's startup mode; her voice counts as installed when her venv is on disk), so an update never depends on the staged installer being able to ask anything.

### The Updater learns to warn, and the install chain moves (#70)

- **Turn Sudo Mode on before you update.** The installer's system step needs root; without it an update can stall or finish without its system packages — field-proven on NeoArcadia, where a deliberate rollback test (VERSION edited back to 0.1.0, then updated under Sudo Mode) completed clean end to end, twice. When an update is available and Sudo Mode is off, the Updater now shows a red warning directly above the Download & install button: "Enable Sudo Mode before updating. The installer's system step needs root. Without it, an update can stall or finish without its system packages." With Sudo Mode on, the warning is replaced by a quiet green "Sudo Mode is on — ready to update." It is a warning, never a lock: the button still works.
- **The chain above the notes, with a slim progress bar.** Once the operator opts into an update, the install chain (downloading, verifying, staging, installing, DHD prerequisites, restarting) renders directly above the release notes instead of below them, with a slim progress bar across the top of the chain card — the bar for the glance, the chain for the receipts.
- **"Taking a while?"** Once the Installing step has been underway a while, the chain says what the time is going on: "This step is likely rebuilding the UI — that can take a few minutes on modest hardware. It's working, not stuck. We're working on making it faster." No countdown, no ETA.

### Navi pulls memories from chat (#72)

- **Two doors.** A natural trigger — "remember this", "remember: …", "save this to your memory", or the Save to memory button under any operator message — and autonomous saves: when the operator says something durable (a fact, a preference, a decision, a commitment, a correction), Navi saves it in the same reply she was already generating. No second inference pass; the fluidity law holds on modest hardware.
- **Nothing is saved silently.** Every save leaves a receipt in the chat showing exactly what she wrote, word for word, with a one-tap Undo. The Memory tab's entries say how they got there: added by hand, from chat (asked), from chat (her call), or from chat (correction).
- **Corrections replace.** A save about the same fact as an existing entry replaces it — matched by fact key (name, home, work, favorite …) or heavy word overlap — instead of piling up a duplicate; Undo restores the old line.
- **Secrets are never saved**, on any path. A password, key, or card number is refused in words, and the refusal receipt shows no payload.
- **The leash is a setting.** Memory mode: She saves on her own (the default), Ask first (autonomous saves wait as proposals, in the chat receipt and the Memory tab), or Only when I say (trigger only). In the shipped app the judgment rides her persona prompt as a [[remember: …]] marker the bridge strips before the reply is shown or spoken; the saves return as payload data and the dashboard files them and draws the receipts.

## 0.1.6 (alpha)

Release tag: v0.1.6a. The polish release: the Enter Code gate (#64), the Vault tree menus (#65), and the Servers collapse with the tag-form menu footer (#66) are first published here, together with two fixes from the v0.1.5a field test — the Servers group's missing spacer (#67) and the Vault navigation panel's move to the right, rebuilt so it cannot drift again (#68).

### The Enter Code window (#64)

- **One gate, both doors.** The two bare code-entry snippets — one for the Apex Node (LAN) door, one for the DHD door — are replaced by a single shared gate page in the bridge, parameterized by door, so there is no second copy to drift. The contract is unchanged: the same POST to /__gate, the same acceptance cookie, the same redirect into the dashboard; loopback is never gated and the API's 403 answers are untouched. The page still serves nothing before the code — one self-contained HTML page, inline CSS and SVG only, no external assets, fonts, or scripts — and no version string appears anywhere on it.
- **The look.** A deep-space backdrop — layered nebula gradients and a fine starfield — behind a glassy card. The DHD dial glyph, twelve chevrons around a glowing core, turns slowly above the APEX wordmark on the DHD door and rests calm and dimmer on the Apex Node door; all motion honors prefers-reduced-motion. The card names the door being knocked on — the domain for DHD, the machine's hostname at home. The page ends at the card: no footer tagline (Alex's ruling on the mockup).
- **The field and the failures.** The code box autofocuses on load, accepts one-time-code autocomplete, renders at full phone size with no focus zoom, and Enter submits as before. A wrong code re-renders the same page with the error in place, the field cleared and refocused, and a shake on the card. The DHD door now shows the throttle it always enforced: attempts remaining before lockout, and — while locked — the form disabled with the remaining lockout time. The Apex Node door's copy is corrected: the code is found on the DHD page of the machine Apex runs on.

### The Vault — tree menus and the right-side panel (#65, #68)

- **The Vault tree gets its names back (#65).** On the live field screenshot the file-tree panel's header controls were crushed into two-letter stubs and every note row spent most of its width on permanent Move / Rename / Delete buttons while the note names truncated. Now the create controls wrap to two lines with full labels instead of truncating, and each note and folder carries a single ⋯ menu (a 44px touch target, keyboard-reachable) holding its actions — Move, Rename, and Delete-with-confirm for notes; New note and Delete for folders. The names take the row's width; drag-and-drop, the touch Move picker, import, search, and templates are unchanged.
- **The navigation panel sits on the right — by placement, not by reversal (#68).** The editor/tree pair claimed the right side since build .73 through a reversed flex row, and the operator's live read diverged twice: at shell and browser widths alike the pair could sit left-anchored mid-page, its placement hostage to how each engine resolves a reversed, wrapping flex line. The pair is now an explicit two-column grid that spans the full width of the view: the editor is assigned the first column, the files panel the second (280px), each by name, in the shell's webview and in a browser alike. On phones (≤800px) nothing changes: the panel stacks full-width above the editor, exactly as before.

### Servers — a parent, with its spacer (#66, #67)

- **Servers is a parent now (#66).** The status column's Servers header collapses and expands the whole group — Llamafile, Apex Node [local], DHD [public] — and remembers the operator's choice across re-renders, exactly like the per-row dropdowns it parents. Shut, the header still carries one dot per server in that row's own colors, so collapsing never hides a problem. Rows, dots, and dropdown contents are untouched.
- **The spacer is back (#67).** The Servers parent was the one status block without the column's standard boundary, so in the expanded default state Sudo rendered flush against the DHD row. The block now carries the same boundary as every other status block — the same gap, padding, and divider — in the expanded and collapsed states alike. Section order and the collapse behavior are unchanged.
- **The menu footer reads like GitHub (#66).** The version at the foot of the side menu is centered and written in tag form — **v0.1.6a** — in the same status colors as before (alpha red, beta yellow, stable blue, no tag on stable); the collapsed rail keeps the same whole string, centered, unclipped. Display only: the VERSION file, the bridge's reporting, and the Updater's comparisons are untouched.

## 0.1.5 (alpha)

Release tag: v0.1.5a. The DHD release: Apex gains its public door — and the door tells the truth about its address. The honest public-address model (#59) and the installer/packaging fixes (#60) land here, and the Vault and markdown rounds (#53/#54), whose fixes shipped in earlier builds, close at this release.

### Fix — honest DHD addresses (#59, from the Build 10 field test)

- **A LAN address is never a public address again.** The DHD state now carries three separate addresses: the domain (the public address once its certificate is live and the name resolves to this machine), the detected public IP, and the LAN address — which lives in its own labeled home, **On this network (LAN)**, on the DHD page and in the status dropdown, and never under a public label.
- **WAN detection.** The bridge learns this home's public IP with a small cached HTTPS echo lookup that degrades to "couldn't detect" instead of ever blocking an enable. A detected address that is itself private or carrier-NAT (100.64.0.0/10) is reported plainly as **behind another router/NAT**.
- **"Reachable anywhere" is earned.** It appears only when the public path is proven — domain set, resolving to this machine, ACME certificate live. Otherwise a running DHD reads **on/listening, outside reach unverified** and names the next step (forward 443 + 80 on the router to this machine, or add your domain). The ladder's last step is labeled a **local check** — "answered on this machine."
- **Its own proxy is a healthy state.** When 80/443 are held by Apex's own DHD proxy, the availability rows read **"In use by Apex's DHD proxy — this door working"** and re-enabling treats its own listener as success — never "port is not free."

### Installer and packaging fixes (#60)

- **A --fresh reinstall keeps your DHD certificate.** The certificate home (config/dhd/) joins the installer's keep-list: it is stashed before the fresh wipe and restored after it, the same treatment the Vault already had — a real certificate survives a fresh reinstall instead of being wiped and re-issued.
- **The package's docs install with the app.** The installer now copies the package's docs/ into the installed tree, so docs/DHD.md sits on the machine beside everything it documents, and the shipped tree and the installed tree agree.
- **A fresh package starts with the DHD off.** The packaged config defaults ship dhd.enabled=false no matter what state the machine that generated the package was in — package defaults never inherit live session state, and the door opens only when the operator clicks it on.

### DHD — Apex from anywhere

- **DHD** (Dial-Home Device — the way home) is a new top-level menu destination, after the Vault and before the Updater, with a theme-tuned dial glyph. It extends Apex Node's same dashboard to a genuinely public address on your own machine — everything self-contained: no Tailscale, no external tunnel or proxy service, no Certbot.
- **One click.** The DHD page's master switch does everything: Apex generates a certificate, brings up its own reverse proxy on 80/443 in front of the bridge (the bridge itself binds loopback only in DHD mode — the proxy is the only public face), runs a reachability self-check, and reports the live state and URL — or names the failed step in plain words, leaving the previous state untouched.
- **TLS from the first click**: a self-signed certificate Apex generates when no domain is set; when you add a domain — optional, free-form, addable at any time — Apex's own built-in ACME client obtains a real Let's Encrypt certificate (HTTP-01 through the Apex proxy) and renews it automatically at 30 days remaining or less.
- The door keeps the **existing access code** (same code, same cookie as Apex Node), now with public-side throttling: progressive delays and a five-minute lockout after five wrong codes. A session through DHD is a full session — the one-click Updater works from it end to end.
- The status column gains a **Servers** group — Llamafile, Apex Node [local], DHD [public] — each with a pulsing green/amber/grey status dot and its own dropdown of details; directly under Navi's status, bracketed by separators, a single update line reads a green **Up to date** or a yellow **Update available**. The Apex Node controls live on the DHD page, under the DHD options; Settings → System keeps only a pointer to them.
- Docs gain a DHD page (and docs/DHD.md): the one-click flow plus the backend you may still handle by hand — router forwarding for 80/443, DNS and dynamic-IP caveats, the self-signed warning, renewal, and turning it off.
- **Prerequisites ship with the install.** The installer lands everything DHD needs (OpenSSL, the certificate home, the low-port capability check) on every distro family at install and update time, DHD on or not — and the Updater's ladder shows "DHD prerequisites" as its own named step, installed by the update's own installer run.
- **Self-healing safety net.** If a prerequisite later goes missing, the DHD page detects it and offers the install in the flow; one click installs it and the enable continues automatically. If an install — or any ladder step with a manual remedy — fails, the failure card shows the exact distro-correct commands in a copyable block.
- **Operation cards in chat.** Multi-step work (the DHD enable first) renders in the chat thread as a live step card driven entirely by the bridge's deterministic state — no model generation while an operation runs — fully self-contained (commands and output inline, nothing to open elsewhere), and the finished card persists in the thread.

### Also closing at this release

- **Markdown everywhere (#53)** and **the Vault (#54)** shipped in earlier builds and close here: static text across the app renders as markdown (the Updater's release notes and update log included, headings whole at every line ending), and the Vault — an Obsidian-compatible folder of plain markdown at config/vault/ with its own menu destination, editor and file tree, and Navi's own desk inside it — sits on the installer's keep-list beside everything else that is yours.

## 0.1.4 (alpha)

Release tag: v0.1.4a. The next major update, live-confirmed by Alex before this release was cut: the Updater release notes (#47), full Linux support (#48), and the docs formatting pass (#51).

### Updater release notes

- When an update is available, the Updater screen shows that release's notes in a rendered panel, readable before you press Download & install. The words come from the GitHub release body; when the release page carries none, the matching section of this changelog stands in and the panel says so.
- A check that cannot reach GitHub — no network, or GitHub's rate limit — says that in plain words and shows no panel; it never pretends you are up to date.

### One installer, every major Linux family

- The installer reads /etc/os-release, announces the family it found in plain words, and branches only its dependency step: the Debian family (Debian, Ubuntu, Pop!_OS, Mint and their kin) via apt, Fedora via dnf, and Arch via pacman. Everything else — hardware profiling, the model download, what an update keeps, the startup choice — is shared.
- Bazzite takes a user-space path: the installer never layers packages with rpm-ostree and never asks for a reboot. Her window is built inside a Fedora distrobox when one is available; without one, the window build is skipped in plain words and the complete core install — the bridge and the browser dashboard — still lands.
- An unrecognized distro is named, no package manager is guessed at, everything that can be installed user-space still is, and the core install completes.

### Docs formatting

- Full markdown in the in-app Docs — headings, bulleted and numbered lists, tables, grouped blockquotes, inline code, fenced code blocks, and links — the same set the GitHub wiki renders, on both sides.
- Fenced code blocks are syntax-highlighted with the chat's per-theme palettes, in every theme.
- Prose enumerations are real bulleted lists and instruction sequences are numbered steps, in the in-app Docs and on the wiki alike.

## 0.1.3 (alpha)

Release tag: v0.1.3a. Everything from the phone round (builds .62–.68), live-confirmed by Alex on his phone and desktop before this release was cut.

### Apex Node and phone chrome

- **Apex Node** [local]: it serves only your home network, never the outside world. Its controls live on the DHD page. Turning it on is one flip: the choice saves, Apex restarts her bridge bound for the network, and the row confirms the live state from the answering bridge.
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
