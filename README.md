# Apex — Powered by [Navi](https://github.com/SaintsSec/Navi)
# Apex — local app package

Project home: https://github.com/AlexKollar/Apex — the fresh repo for this rebuild. (Navi was born at SaintsSec/Navi; that repo stays as the legacy archive of the original.)

Apex: a local UI for the Navi system, running on a single
.llamafile. No Ollama, no cloud account, nothing leaves this machine
unless you point it somewhere else.

## Latest release — 0.1.8 — tag v0.1.8

- **Apex 0.1.8 is a full release.** It carries the bare number everywhere — VERSION, tag v0.1.8 — and takes Latest. It graduates the 0.1.8e Edge line (Builds 1–10) with its content unchanged: same build stamp, same code — only the version's identity flipped from Edge to stable.
- **Navi Mesh, Ring 1 (#78).** Your machines pool inference: a stronger machine answers whole chat requests for a weaker one, and the reply says which machine wrote it. Pairing is by PNG card, carried by hand; borrowing is automatic for paired machines; lending is idle-only, inside caps you set, and armed only in person on the lender. Field-proven on a real two-machine pair.
- **The pairing cards fly with the backup (#89); the text card is retired (#90).** Mesh pairing cards join the GitHub backup essentials — your own card minted fresh, a picture per paired peer — so a lost machine re-pairs from its pictures instead of starting cold. Pairing is the picture only now; a text card saved from an earlier build can no longer be pasted.
- **Updates never need a reboot (#91).** The installer proves the old bridge stopped before replacing a single file — or aborts, naming the process that holds the port and the command that ends it. A manual install relaunches Apex and verifies the new build is answering; a dashboard left open across an update offers a one-click reload onto the new build's page.
- **Lending, kept honest (#87, #88).** Paired peers are health-checked in the background and the roster says what it found; lend caps and the idle-only override are settings on the lending machine; a borrowed reply's pills share one row — Mesh first — at every width.

[Read the changelog](CHANGELOG.md)

Installing puts Apex in your application menu, like any other
app — it is not just a folder of files:

- Linux — a "Apex" launcher in the applications menu
  (a .desktop entry, with the icon installed into the icon theme).

Linux is the supported install right now. Windows and macOS
installers are planned, but they are NOT in this package yet —
there is no Windows or Mac installer to run in here.

## Quick start (Linux)

    ./install.sh

The scripts in this package (install.sh, start.sh,
run-llamafile.sh) arrive with their executable permission
already set — no chmod step needed.

Installing from a git clone — or from GitHub's source zip (the
zip the green Code button offers, the one that unpacks to a
folder like Apex-main) — works too, with two honest differences.

First, how you run the installer. From the release zip, run it
the usual way:

    ./install.sh

The scripts in the release zip arrive with their executable
permission already set, so that just works. A clone or a GitHub
source zip is different: run the installer through bash instead:

    bash install.sh

That is THE way to run it from a clone or a source zip, because
it needs no executable permission. Here is why, in plain words:
the git tree does not preserve the scripts' executable
permission, so every script that comes out of a clone or a
source zip arrives without it — and a script without that
permission cannot be run as ./install.sh until the permission
is set. Running it through bash skips that entirely: bash reads
the file itself, so the permission never comes into it. The
same goes for starting her from a source tree: bash start.sh,
not ./start.sh. If you try ./install.sh from a clone anyway,
you will meet a baffling pair of errors — bash answers
"Permission denied", and sudo ./install.sh answers
"command not found", which sounds like the file is not there
at all. It is there; it just cannot be run that way. Use
bash install.sh and both errors go away. (If you prefer
./install.sh, you can set the permission yourself first —
chmod +x install.sh start.sh run-llamafile.sh — and then run
it the usual way. That works too; bash is simply the shorter
path, and the one these instructions lead with.)

Second, the icons. The clone does not carry the binary icon
files (assets/icon.png, assets/navi-apex.ico,
assets/navi-apex.icns, shell/icons/icon.png): those ship only
inside the release zip. So a clone install runs without the
custom icon — the installer says so in plain words while it
installs, the app and its menu entry use a fallback icon, and
the standalone window is not built (it is built around that
icon), so Apex opens in your browser instead. Everything else
installs exactly the same. The release zip remains the
complete package: release zip → ./install.sh; clone or GitHub
source zip → bash install.sh.

One installer covers the major Linux families. It reads your
distro from /etc/os-release and announces the family it found in
plain words, and only its dependency step branches: apt for the
Debian family, dnf for Fedora, pacman for Arch — the same
development libraries and base tools under each family's own
package names. Bazzite is its own case: it is Fedora-based but
immutable, so the installer never layers packages with
rpm-ostree and never asks for a reboot — her standalone window
is built inside a Fedora distrobox when one is available, and
when none is, the window build is skipped in plain words and
the core install (the bridge, plus the dashboard in your
browser) completes in full. A distro the installer does not
recognize is named as such: no package manager is guessed at,
everything that can be installed user-space still is, and the
core install completes just the same.

The installer is a script (no graphical wizard). It asks one question
during the install — whether the llamafile server should load on app
launch or at system boot — and wires up your answer; there is no
hard-coded default. (Scripted installs can answer ahead of time with
--startup launch or --startup boot.) The installer downloads the
llamafile binary itself from https://huggingface.co/saintssec/navi.llamafile/resolve/main/navi.llamafile — not the repo page —
and checks what it got: an HTML file is never accepted as the binary.
If a real navi.llamafile binary is already in the install location,
the download is skipped entirely.

Fresh install: pass --fresh to wipe the install
location and reinstall the app from scratch. Your own state survives
even that: the llamafile binary is left exactly where it is (untouched
and never re-downloaded), your installed chips are stashed and
restored, and your Soul/Memory documents come through with her. Her
voice survives it too: the installer checks whether her voice is
already set up — the voice venv restored from the stash still
imports its speech engines — and skips the voice install entirely
when it is, instead of rebuilding it from scratch. Only
a first install — where none of that exists yet — creates everything
fresh.

Then launch "Apex" from your application menu (or run ./start.sh
from the install folder — from a source tree, bash start.sh).
She opens in her own window — the standalone Tauri shell — and no web
browser is involved. Launching again while the window is open focuses
it instead of opening a second one. The same dashboard stays
reachable in a browser at http://localhost:8675 as a
fallback surface (and is what you get on an install where the shell
was never built — see shell/README.md).

## Form factor

Apex is a standalone app now: a small Tauri window (Rust plus
the operating system's own webview — no bundled Chromium, so the
footprint stays small) over the same local bridge and llamafile as
always. The architecture underneath did not change — local files, a
local bridge, no cloud account — the window simply replaced the
browser as the front door. The plain web dashboard remains as a
fallback, served by the bridge at the same address.

## What's in here

- app/index.html — the Apex dashboard (left nav: Chat, Voice, Chips,
  Memory, RAG, Documentation, Updater, GitHub, Settings; central panel;
  right status column). Pure static file, no build step. Its header
  reads "Apex"; the side menu collapses to a rail while the
  status column stays visible; the Memory tab switches between saved
  chats. Every menu option carries its own icon beside its label (and
  the collapsed rail is icons alone). The frame is fixed: the dashboard
  fills the viewport, the left menu and the right status column never
  scroll away, and in Chat only the message thread scrolls (the
  composer stays pinned beneath it). Chat renders Navi's replies as
  markdown — code fences become real code blocks — shows a typing
  animation while she thinks, lines her loaded chips up as pills above
  the composer, and has a Clear chat button for a fresh start.
- shell/ — the standalone window: a Tauri app (Rust + the OS webview)
  whose single window, titled "Apex" and carrying the app icon,
  loads the dashboard from the bridge. Single-instance — a second
  launch focuses the existing window. The installers build it with
  cargo during install — installing Rust itself via rustup
  (per-user, minimal profile) first when no toolchain is present —
  and place the binary beside start.sh as navi-apex-shell; the
  launchers open it instead of a browser — and only when its build
  stamp covers the shipped shell sources: a failed rebuild retires
  the previous binary (navi-apex-shell.stale) rather than leaving
  an older shell to be launched as this build. See shell/README.md.
- bridge.py — a tiny local server (Python 3, stdlib only) that serves the
  dashboard and gives it real powers:
    * /api/chat   — proxies chat to the llamafile server
    * /api/shell  — runs real shell commands for the CLI-access chat
    * /api/status — model / version / backend state
    * /api/update/check + /api/update/apply + /api/update/result —
      the Updater: the check compares the project's latest GitHub
      release against the VERSION file; apply carries the update
      through end to end from the one click — it downloads that
      release's package zip (a gzip-wrapped package is unwrapped
      and accepted), verifies it is an Apex package, stages it
      under updates/<tag>/, hands the install to a detached helper
      that runs the staged installer (never --fresh) and relaunches
      the app, and records the outcome (version before → after,
      read from the installed VERSION file) where the panel reads
      it back as its confirmation; every failed step names itself
      and, once staging was reached, shows the staged folder and
      the one manual install command as the fallback (a check that
      cannot reach GitHub says so, too)
    * /api/llamafile/connect — probes the llamafile server for the status element
    * /api/commands — lists the commands actually installed on this
      machine (a scan of PATH), which feeds command autocomplete
    * /api/persona — reads/writes Navi's Soul and Memory documents
    * /api/sudo/auth — validates the session sudo password once when
      sudo mode is enabled and opens the bridge's persistent root
      shell with it (the password itself is never stored);
      /api/sudo/logout closes that shell when sudo is turned off
    * /api/chips/* — the Chips screen's three tabs: Navi User Repo (NUR) searches
      GitHub for repos tagged navi-chips (each one a chip) and
      installs / deletes / updates them against chips/installed.json —
      installing downloads the chip's own code from its repo and
      forges it into a chip in chips/, so a GitHub chip is a
      folder chip like any other — offering an update when a repo's
      latest release is newer than the installed one; Chip Studio is
      a full code editor that forges and edits chips as .png
      chips in chips/ (the chip API's methods live in the Docs, on
      the Navi Chip Functions page); Workflows chain chips so each step's
      output feeds the next. /api/chips/run executes a chip's
      code, /api/chips/source and /api/chips/save back the Studio
      editor, and /api/workflows/* lists, saves, and runs chains.
      Chips also run straight from chat — /chip <name>, "run the
      <name> chip", a chip pill, or the chip's name alone — and a
      bare /chip answers with the installed shelf.
    * /api/voice/* — her voice (see "Her voice" below): status and
      settings, a voice test, speech-to-text for push-to-talk clips,
      text-to-speech for her spoken replies, and the call session —
      start / turn / end, with finished calls archived to
      voice/calls.json. /api/chat accepts speak:true and the bridge
      speaks the reply aloud on this machine as well.
    * /api/github/pulse and /api/github/issues — the GitHub
      section: her pulse window into the project itself
      (AlexKollar/Apex), live from the public GitHub API, no
      sign-in needed to look. /api/github/* — Settings → GitHub &
      Backup: optional sign-in via GitHub's
      Device Flow (never required to run Navi; the token stays on
      this machine in config/github-auth.json, owner-only, never
      backed up or logged), and backup/import of the ready-to-fly
      essentials — Soul, Memory, settings/config, installed chips,
      RAG packs with their indexes and active states, workflows,
      Mesh pairing cards (the PNG pictures; the node keypair
      never rides) —
      to a repo under your own account (default navi-backup,
      private by default), on your interval (every 1/3/5/7 days,
      checked on launch and while the bridge runs). Import previews
      what would change and overwrites nothing without confirmation.
      Never backed up: transcripts, call logs, the hardware profile,
      and voice model files. The dashboard's GitHub page and the
      wiki's "GitHub — issues & backups" page carry the full story,
      including the OAuth client-id setup (a config value — a live
      id must be registered under the project owner's account, so
      none ships filled in).
- install.sh — the Linux installer (the only installer in this
  package for now; Windows and macOS installers are planned, not
  included). It detects the distro family from /etc/os-release
  (Debian family, Fedora, Arch, and Bazzite as its own immutable
  case) and installs the build dependencies with that family's
  package manager — only the dependency step branches. It
  downloads the llamafile
  from https://huggingface.co/saintssec/navi.llamafile/resolve/main/navi.llamafile, marks it executable, wires up startup, and
  registers the application-menu entry with the icon.
- assets/ — the Apex app icon as PNG (Linux/desktop use), ICO
  and ICNS renditions (carried for the planned Windows and macOS
  builds), plus the Linux
  .desktop entry template the installer fills in.
- systemd/navi-llamafile.service — the boot-mode unit (Linux).
- config/navi.config.json — backend mode, paths, ports, startup mode,
  and the settings this package was exported with (sudo mode, threat
  level, operator name, installed commands) — the app ships as the
  project stands. Its public_server block holds the Apex Node
  toggle (on the DHD page): off by default; on, the bridge binds
  0.0.0.0:8675 at launch and non-loopback visitors must enter the
  block's access code (the bridge generates one per install) before
  anything beyond the code-entry page is served.
- docs/DHD.md — the DHD guide as prepared wiki markdown: what DHD
  is, the one-click flow, and the backend the operator may still
  handle by hand (router forwarding, DNS, certificates, renewal).
- config/soul.md + config/memory.md — Navi's persona (see below).
  Yours to edit. No install ever overwrites them once they exist:
  updates and reinstalls leave them alone, and even a --fresh install
  stashes and restores them. A first install creates them fresh.
- chips/ — starts empty: Apex ships with no pre-installed
  chips. Chips you install from GitHub or forge in Chip Studio land
  here as .png chips, each image carrying its chip's full code
  inside the PNG (see chips/README.md) — and they survive updates,
  reinstalls, and --fresh installs alike.
- requirements-voice.txt + voice/ — her voice (see below): the
  optional speech dependencies, and the folder holding her
  downloaded speech models (voice/models/), the call in progress,
  and the record of finished calls (voice/calls.json). The models
  survive updates, reinstalls, and --fresh installs alike.

## Persona — Soul & Memory

Navi is a partner, not a cold command executor: conversational, warm,
genuinely trying to connect with her operator while doing exact CLI
work. Her persona is yours to modify — Soul/Memory style, no locked
"shards":

- config/soul.md — who Navi is: her identity, voice, and how she
  treats you and the work.
- config/memory.md — what Navi carries between sessions.

Edit them in Settings (the dashboard writes the same files through
bridge.py) or directly as files. bridge.py builds her system prompt
from both on every chat. Settings also holds what Navi calls you —
the operator name her persona uses when she addresses you.

## DHD — Apex from anywhere

DHD (Dial-Home Device — the way home) is Apex's public door, its own
menu page in the dashboard. Apex Node serves Apex on your home
network; DHD extends the same dashboard to a genuinely public address
on your own machine, and everything is Apex's own work — no Tailscale,
no external tunnel or proxy service, no Certbot. One click on the DHD
page does it all: Apex generates a certificate, brings up its own
reverse proxy (inside bridge.py) on ports 80/443 in front of the
bridge — in DHD mode the bridge binds 127.0.0.1:8675 only, so the
proxy is the only public face — runs a reachability self-check, and
reports the live address, or names the failed step in plain words.
TLS is on from the first click: a self-signed certificate Apex
generates into config/dhd/ when no domain is set (the browser warning
is expected — the Docs' DHD page explains it), or a real Let's Encrypt
certificate from Apex's built-in ACME client when you add a domain in
the page's optional field (addable any time, never required), renewed
automatically at 30 days remaining or less. The door uses the same
access code as the home network, with public-side throttling
(progressive delays; a five-minute lockout after five wrong codes),
and a session through DHD is a full session — the Updater included.
What stays yours: forwarding ports 80/443 on your router to this
machine, and pointing your domain's DNS at your home IP if you use
one. The in-app Docs → DHD page (also docs/DHD.md in this package)
walks through all of it. On Linux, ports below 1024 are reserved: if
the proxy step names them, grant the bridge the low-port capability
once — sudo setcap 'cap_net_bind_service=+ep' on the python3 binary
the bridge runs with — and flip the switch again.

## Command autocomplete

The chat composer autocompletes the command word from what the
system has installed: the built-in default set (ls, cat, cd, pwd, echo,
whoami, hostname, date, uname, ps, navi, help) plus installed commands.
In live mode the installed list is a real scan of this machine's PATH
via bridge.py; in mock mode it is the list managed in Settings, where
commands can be installed, removed, or registered by name.

## Sudo mode

The status column carries a sudo mode toggle. On, Navi executes
commands with admin privileges — but bare "sudo -n" can never elevate
on a normal sudo setup (it refuses to ask for a password), so turning
sudo on asks for the sudo password once: the bridge validates it by
opening one persistent root shell, and every sudo command runs
inside that shell. That shape matters on machines where sudo asks
a fingerprint reader before the password (pam_fprintd): one sudo
process per command would pay the reader's full timeout on every
command and print its prompts into the output, while here the
reader is consulted exactly once, when the shell opens — expect
Authenticate to take a moment there — and commands after that run
instantly, with output that is purely their own. The dashboard
keeps the password in page memory for the session only — never
saved to disk or config, cleared when sudo is turned off or the
page closes — and sends it with each sudo request so the bridge
can reopen the shell if it ever closes. Turning sudo off also
tells the bridge to close the root shell at once. Off, everything
runs as your regular user, and root-only paths refuse as they
should. A one-off "sudo …" prefix on a single command works either
way in a real shell. Commands run from your home directory by
default, so relative paths like "mkdir test" land there — never
in a directory that no longer exists.

## Her voice — calling Navi

Navi can be called, not just typed at — and the whole loop is local,
running on CPU on this machine, because a voice that phones home
isn't hers. You speak; **faster-whisper** (OpenAI's Whisper running
on CTranslate2, int8) turns it into text; her model answers with her
persona, her CLI access, and her chips intact; and **Kokoro** — an
82M-parameter voice model, Apache-2.0 — speaks the answer back,
sentence by sentence as it arrives, so she starts talking before
she's finished thinking. **Piper** is the lighter fallback engine.
Nothing you say is recorded anywhere but this machine.

The Voice tab is where it lives: the pipeline with each stage's real
state, her settings (which Whisper model hears you — tiny.en /
base.en / small.en — which engine and voice she speaks with, her
speed and pitch; saved in config/navi.config.json's "voice"
section), a "Hear her voice" test, and the call itself — a Call
button, push-to-talk through your real microphone, an elapsed timer,
and a live transcript. A mic beside the chat composer does
push-to-talk for one-off spoken messages, and typed chat can speak
its replies aloud too (a toggle in the Voice tab; the bridge plays
them on this machine). A call is not a separate mode: its turns go
through the same chat as typing, they land in the conversation, and
when the call ends it is archived to voice/calls.json.

**Her voice is picked in the Voice settings** — and the list there
is auto-generated, never hardcoded: the bridge enumerates the
voices this machine's Kokoro installation actually has (the voice
files it holds, or the catalog the installed package pulls from —
a catalog voice downloads the first time she speaks with it) and
builds the picker from that. She speaks as **Isabella** (British
female, "bf_isabella") by default.

The speech engines are an **optional** install, on purpose:
bridge.py stays stdlib-only and dependency-free, and imports the
engines lazily only when a voice endpoint is used. The installers
offer a voice step — say yes and they build an isolated venv at
voice/venv from requirements-voice.txt (the launchers then run the
bridge with that Python); say no and they print the one command
instead:

    python3 -m pip install -r requirements-voice.txt

Until the engines are importable, the Voice tab reports her voice
as unavailable and names that step — it never fakes audio. Speech
models download once, on first use, into voice/models/ (the Whisper
cache and any Piper voices; Kokoro's weights ride inside its
package), and that folder is on the same keep-list as her chips, the
llamafile, and her Soul/Memory: updates, reinstalls, and even
--fresh installs never remove it.

## Known chats

Conversations are saved (in the browser's local storage) and the
Memory tab lists them as known chats: switch between them, start a new
one, delete one. Chat always picks up the active chat's transcript.

## Live backend — always

The installed app is always "live" — that is the real app, talking
to your machine. There is no backend switch in the shipped app:
chat goes to the real llamafile server (OpenAI-compatible endpoint,
default http://localhost:8080/v1) through bridge.py, and the shell
runs real commands on this machine. A config saved by an older
build carrying backend "mock" is read as Live. The labeled
Mock/Live switch exists only in the Apex space's test bench, where
the simulation belongs. The llamafile's Running state in the status
column is the live signal — there is no separate BACKEND line.

## Updating the app

Reinstalling replaces the app's files — and the installers also stop
any bridge still running from the previous install, because a bridge
process that is never restarted keeps executing its old code while
serving the new dashboard from disk (the tell: chat fails with the
llamafile's 400 and sudo authentication answers "not found"). The
bridge also watches for its own replacement: if bridge.py changes on
disk, or a newer bridge starts, the old one steps aside and the
launcher relaunches the current build. The dashboard checks the
bridge's build stamp on every status poll and shows a BRIDGE OUT OF
DATE warning in the status column whenever the process answering is
not the build the page shipped with — if you ever see it, fully quit
the app and relaunch.

On Linux the app now installs to /opt/navi-apex. Installing over an
earlier install under ~/.local/share/navi migrates it as a clean
break: the old bridge and its boot service are stopped and disabled,
the llamafile binary is moved into /opt (not re-downloaded), the
config and persona documents are carried across, and the old files
are removed.

## If the page at localhost:8675 is not this dashboard

Something else is serving the port. The address is not exclusively
Navi's: an earlier UI for Navi — or any other local server — that is
still running will hold 8675 and answer the browser with its own
page, while the Navi bridge cannot even take the port. The package
defends against this in layers: the bridge sends no-store headers
with everything it serves, so no page (this dashboard, or a
predecessor's) is ever replayed from the browser's cache at this
address; the launchers open the browser only once the process
answering /api/status carries this build's stamp — otherwise they
name the page that actually holds the port, by its own title, and
open nothing; the installers warn the same way when a foreign page
still answers after the old bridges are stopped; and the dashboard
itself is stamped — view the page's source and its first line names
the build and the install folder that served it, or, by its absence,
proves it wasn't the bridge at all. To clear a foreign server: find
it with "lsof -i :8675", quit it, and launch Apex again.

One subtler version of this failure: a bridge can be running on the
WRONG port entirely. When the bridge port moved from 8765 to
8675, the first 8675 build still read its port from
config/navi.config.json — and the migration carried the old config,
with its old port, into the new install. The new bridge bound 8765,
announced itself "already running" there, and its launcher polled
8675, found nothing, and refused to open the browser. The
port is now a property of the package build, not of the config: the
bridge binds 8675 no matter what a carried config says (and
says so when the config disagrees), and every installer re-stamps
the config's bridge port and install directory on each install. If
start.sh ever reports a bridge already running on 8765, a bridge
process from the previous install is still alive: stop it with
"pkill -f bridge.py" and launch again.

## CLI-access chat

In live mode, asking "show me the contents of /home/name/" makes Navi
run the command through bridge.py and put the real output in the thread.
That is the point of the system: the model assists with system-level
access instead of guessing.

## The llamafile status element

The status column leads with the state of navi.llamafile:

- Running — the model server answered; chat goes to the model.
- "Disconnected. Click to Connect." — the server isn't answering.
  Clicking Connect actually starts it: in launch startup mode the
  bridge launches navi.llamafile from the install location and waits
  for it to answer (a first model load can take a minute or two; the
  server's output is kept in navi.llamafile.log beside the app, and a
  failed start reports the reason in the status column). In boot mode
  the bridge only probes — the system service owns the server. In mock
  mode the simulated server answers. While it's disconnected there is
  no model to talk to, so chat treats what you type as a plain command
  line: the text runs as a shell command and you get the system output
  back in the thread, as a terminal block.

## Startup modes

Chosen during install — the installer asks, and records the answer in
config/navi.config.json:

- launch — start.sh checks first whether the llamafile server is
  already answering (started at boot, by an earlier launch, or by
  hand); if it is, it leaves it alone and just runs the app, and
  only when nothing answers does it run ./navi.llamafile
  --server --v2 plus the hardware-profile flags, then the bridge,
  then open the UI. Nothing runs when the app is closed. Every
  launch path reads the same flags: start.sh, the
  bridge's Connect/start, and the boot-mode service all
  invoke the server as --server --v2 with the runtime settings from
  config/navi.config.json's hardware profile (see below).
- boot — the installer registers the server to start with the system
  (a systemd user service) so the llamafile server is warm before
  you open the UI.
  The registered command runs run-llamafile.sh,
  which reads the same hardware-profile flags from the config.

## Hardware profile

Her runtime settings are chosen from YOUR machine at install time,
never copied from the developer's. The installer detects the CPU
(model, logical cores, performance cores where the OS reports them),
total RAM, and the GPU (discrete vs integrated, VRAM where known) —
/proc + lspci/nvidia-smi on Linux —
derives threads, context size, batch size, and GPU offload layers,
and writes the result into config/navi.config.json (hardware_profile
+ runtime) with the detection and reasoning logged to
hardware-profile.log beside the app. Every launch path reads those
flags from the config; nothing hard-codes a developer's numbers.
Settings shows what was detected and what was chosen, takes a manual
override, and offers Re-detect. Floors stay conservative: a
Framework 13 (i5-1340P, ~9.5 GiB, integrated graphics) lands on
4096 context / 4 threads / batch 512 / CPU-only — the proven fluid
baseline — and stronger hardware scales up from there (more context
with more RAM, threads matched to performance cores, GPU layers only
on a discrete GPU with at least 4 GiB VRAM). A manual override set
in Settings survives reinstalls; the install log says so when it is
preserved.

## Layout after install

    /opt/navi-apex/         (the Linux install root)
      navi.llamafile        the model (downloaded by the installer)
      app/index.html        the dashboard
      bridge.py             the local bridge
      config/navi.config.json
      chips/                her chips + installs (kept across installs)
      voice/                her voice: models/, calls.json, the venv
                            (models kept across installs)
      requirements-voice.txt  the optional speech dependencies
