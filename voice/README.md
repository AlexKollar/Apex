# Her voice

Navi's voice is fully local and CPU-only: she hears through
**faster-whisper** and speaks through **Kokoro** (Piper is the
lighter fallback). No cloud speech service, no account — nothing
you say leaves this machine.

- `models/` — downloaded speech models: the Whisper cache
  (`models/whisper/`) and any Piper voices (`models/piper/`).
  They download once, on first use. **This folder is on the
  persistence keep-list**: updates, reinstalls, and --fresh
  installs never remove it, exactly like her chips, the llamafile,
  and her Soul/Memory. Only deleting it by hand makes her
  re-download her ears.
- `venv/` — the optional speech dependencies
  (requirements-voice.txt), installed here by the installer when
  you say yes at the voice step. The launchers run bridge.py with
  this Python when it exists. A reinstall may rebuild the venv;
  the models above are never touched.
- `state.json` — the call in progress, if any (turns as they
  happen). Safe to delete; it just forgets a dangling call.
- `calls.json` — the permanent record of finished calls:
  when, how long, and every turn, hers and yours.

Settings (enabled, Whisper model, engine, voice, speed, pitch)
live in `config/navi.config.json`'s `voice` section and are
edited from the dashboard's Voice tab.
