# Changelog

All notable changes to Apex (and the Navi lineage it grows from) are recorded here.

## [0.1.0] — 2026-11-07 — First public release (alpha)

Apex's first release: the standalone app, renamed from the working title
"Navi: Apex" — the product is **Apex**, the tagline is **Powered by Navi**,
and Navi herself keeps her name. Linux is the supported install; Windows and
macOS installers are planned and tracked as issues.

### The app

- Standalone Tauri desktop window (single-instance, menu launch, no browser
  required); the dashboard remains available at `localhost:8675` as a fallback.
- Mission-control layout: left navigation (Chat, Voice, Chips, Memory, RAG,
  GitHub, Updater, Settings, Docs), central workspace, live status column.
- Version single-sourced from a plain-text `VERSION` file; the menu footer
  reads "Ver. 0.1.0" with an alpha status tag, and the collapsed icon rail
  shows a compact readout that fits the rail.
- Four themes over shared style variables: signature dark, light,
  high-contrast, and Nordic dark (Polar Night / Snow Storm / Aurora, with
  per-icon contrasting colors and full Nord markdown).
- App icon: a black anglerfish silhouette with a single glowing cyan lure —
  apex of the dark.

### Chat & CLI

- CLI-first routing: known commands execute immediately and their raw output
  becomes conversation context; press-once CLI/Navi latch toggles, with `$`
  and `>` per-message overrides and a live mode pill.
- Whole-reply rendering behind a thinking indicator; markdown everywhere;
  focus returns to the composer after every send.
- Shell touches: ghost completions from history, live syntax highlighting.
- Operator name from Settings (default "Operator"); persona defined by
  editable Soul and Memory documents.

### Chips

- Chips are `.png` cartridges — the full codebase inside a Battle Network-style
  chip image — runnable from chat by `/chip`, by name, or from the pill row.
- Chip Studio: multi-file chips (root.py + modules), fullscreen editor with
  file sidebar, minimap, multiple cursors, command palette, autosave, error
  squiggles, find-across-files, outline, smart autocomplete; GitHub-ready
  export that installs back.
- NUR (Navi User Repo): GitHub catalog by topic `navi-chips` with Saints Sec
  and Community tabs plus a Local Chips tab (Installed / Forged); fixed-size
  landscape flip cards — README scrolls on the back — with two-column actions
  (Install/Update over README on the right).
- Edited installed chips are marked EDITED LOCALLY and are never silently
  overwritten by catalog updates.

### Knowledge packs (RAG)

- Pack system replaces seeded documents: GitHub repos tagged `navi-rag`,
  installed with locally built indexes; only active packs feed answers.
- Answers cite sources as breadcrumb pills (pack › document).
- RAG Studio for building packs from your own documents (Markdown, text, and
  text-layer PDFs); exports carry the built index.
- First pack: **first-response** — CISA incident & vulnerability response
  playbooks + NIST SP 800-61 Rev. 3.

### Voice

- Fully local: faster-whisper (small.en, CPU int8) speech-to-text, Kokoro-82M
  text-to-speech, sentence-by-sentence playback.
- Call Navi mode with live transcript; calls are filed to memory. Voice
  picker is generated from the local Kokoro install (default: Isabella).
- Known issue: microphone access in the desktop window is not working on all
  systems yet; documented in-app on the Voice page and in Troubleshooting.

### GitHub & backup

- GitHub view: Overview (live repo pulse), Issues, Roadmap (project board
  webview), Discussions — with per-tab footer actions.
- Optional Device-Flow sign-in; never required to use the app.
- Backups to your own private `navi-backup` repo: Soul, Memory, and settings
  always; chips, packs (with indexes and active states), and workflows by
  choice; on a 1/3/5/7-day interval. Status column shows a plain
  "# files | # days ago" readout (or "No backup yet").
- Settings reorganized into topic tabs: Operator & Persona, Appearance,
  Voice, GitHub & Backup, System (hardware profile lives in System).

### Installer & hardware

- Install-time hardware profiling: CPU/cores, RAM, and GPU/VRAM detection
  derives threads, context size, batch, and GPU offload; logged with its
  reasoning; a manual override survives reinstalls.
- Script-based Linux installer; scripts ship executable. Verify-then-skip
  for the model, voice stack, and shell build — reinstalls print the exact
  reason whenever a rebuild does happen.
- Persistence law: installs and updates preserve chips, packs and indexes,
  the model, Soul/Memory, voice models, and GitHub settings.
- Sudo mode: one authentication opens one persistent root shell in the
  bridge; the password lives in page memory only and is never stored.
  (Guardrails — confirm-destructive, session timeout, full log — are
  designed and tracked as an issue.)

### Docs

- In-app wiki, 12 pages in plain language, grouped by topic, with a real
  pop-out window and a chip API reference ("Navi Chip Functions").

## Lineage — Navi (SaintsSec/Navi)

Apex grows out of the original open-source **Navi** project
(github.com/SaintsSec/Navi, AGPL-3.0), a local CLI AI for cybersecurity
professionals: Python, a 3B cybersecurity fine-tune, llamafile replacing the
earlier Ollama stack. That repository remains as the legacy archive; Apex is
the rebuild — same mind, a real app around her.
