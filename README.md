# Apex - Powered by Navi

Apex is the standalone desktop app that puts Navi — a cybersecurity-tuned local AI — on your own hardware. CLI-first chat, cartridge-style chips, knowledge packs, and a fully local voice, answering to no server but yours.

> **Status: v0.1.0 (alpha)** — first public release. Linux is the supported install today; Windows and macOS installers are planned. Expect rough edges, and please file what you find in [Issues](https://github.com/AlexKollar/Apex/issues).

## Latest release — 0.1.1 (alpha)

- Chat folds finished work into reopenable cards, and the composer completes the zsh set — recall, Ctrl+R, path completion, preview-only history expansion.
- Syntax highlighting is tuned per theme across eleven palettes, including resource-light Dark Liquid Glass and five new themes.
- Chips and knowledge packs publish to GitHub from the app, and Local Chips is the one home for managing them.
- The GitHub lists reconcile what is already installed, packs wear flip cards, and pulse entries open their issues.
- A link that fails in the desktop shell lands on an honest warning toast with the Web UI address.

[Read the changelog](CHANGELOG.md)

## Install

1. Download the app package (`.zip`) from the [latest release](https://github.com/AlexKollar/Apex/releases).
2. Unzip it and run the installer:

   ```
   ./install.sh
   ```

   The scripts in the release package ship with their executable permission already set — no `chmod` step needed. (If you cloned this repo instead, run `chmod +x install.sh start.sh run-llamafile.sh` first.)
3. Launch **Apex** from your applications menu.

The installer detects your hardware (CPU, cores, RAM, GPU) and tunes Navi's runtime settings to fit your machine, asks whether her model server should load on app launch or at boot, and downloads the model (~3.3 GB, a 3B cybersecurity fine-tune packaged as a single llamafile) unless it's already installed. Reinstalls and `--fresh` installs preserve your chips, knowledge packs, Soul/Memory, and voice setup.

Once she's up, the dashboard is also reachable in a browser at `http://localhost:8675` as a fallback surface.

## What she does

- **CLI-first chat** — known commands run instantly and their raw output lands in the thread as context she reasons over; talk to her in the same breath. A whole reply at a time, markdown everywhere, `$` forces CLI, `>` forces Navi.
- **Chips** — purpose-built tools packaged as PICO-8-style cartridge `.png` files with the code inside the image. Browse and install community chips from the **NUR** (Navi User Repo — GitHub repos tagged `navi-chips`), or forge your own in **Chip Studio**, a full multi-file editor that exports GitHub-ready chip repos.
- **Knowledge packs (RAG)** — installable GitHub repos tagged `navi-rag`, indexed locally; only the packs you switch on feed her answers, and answers cite their sources as breadcrumbs (pack › document). First pack: **first-response** — the CISA incident & vulnerability response playbooks plus NIST SP 800-61 Rev. 3.
- **Local voice** — faster-whisper speech-to-text and Kokoro text-to-speech, both on your machine. Call mode included; she speaks replies sentence by sentence. Nothing is transcribed or spoken by a cloud.
- **GitHub built in** — a pulse window on this project (overview, issues, roadmap, discussions), optional Device-Flow sign-in, and backups of your Soul, Memory, settings, chips, and packs to your own private `navi-backup` repo. Sign-in is never required to use Apex.
- **Themes** — signature dark, light, high-contrast, and a Nordic dark theme (Polar Night surfaces, Snow Storm text, Aurora accents).
- **Persona you own** — Navi's Soul and Memory are plain documents you can read and edit in Settings. She calls you what you tell her to (default: "Operator").

## Roadmap & community

- 📍 [Project roadmap](https://github.com/users/AlexKollar/projects/9)
- 💬 [Discussions](https://github.com/AlexKollar/Apex/discussions)
- 🐛 [Issues](https://github.com/AlexKollar/Apex/issues) — bug reports and tester call-outs welcome

Known issue at 0.1.0: microphone access inside the desktop window is not yet working on all systems (typing to her always works). It's documented in the in-app wiki's Troubleshooting page.

## Lineage

Navi was born as an open-source CLI project at [SaintsSec/Navi](https://github.com/SaintsSec/Navi) — that repo stays as the legacy archive. Apex is her next evolution: the same mind, a real app around her. Model: [`saintssec/navi.llamafile`](https://huggingface.co/saintssec/navi.llamafile).

## License

AGPL-3.0 — see [LICENSE](LICENSE).
