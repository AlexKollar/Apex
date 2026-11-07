#!/usr/bin/env python3
"""Navi bridge — serves the Apex dashboard and gives it real
local powers.

Stdlib only. Endpoints:
  GET  /              the dashboard (app/index.html)
  GET  /api/status    backend, model, version, llamafile reachability
  GET  /api/update/check -> the Updater's real check: the project's
                      latest GitHub release compared against the
                      VERSION file; a check that cannot complete
                      answers ok: False with the reason
  POST /api/update/apply -> downloads the latest release's package
                      zip and stages it under updates/<tag>/package,
                      answering with the one install command; the
                      bridge never installs over the running app
  GET  /api/commands  the commands actually installed on this machine
                      (a scan of PATH) — feeds command autocomplete
  GET  /api/persona   Navi's Soul and Memory documents (config files)
  POST /api/persona   saves edits to those documents
  POST /api/chat      {messages:[...], sudo, operator_name} -> proxies
                      to the llamafile server, with Navi's persona as
                      the system prompt
  POST /api/shell     {command:"...", sudo, sudo_password} -> runs it,
                      returns output. Commands run from the operator's
                      home directory; sudo commands run inside the
                      bridge's one persistent root shell (below).
  POST /api/sudo/auth {password} -> validates the session sudo
                      password once and opens the root shell with it;
                      the password is never stored or logged by the
                      bridge
  POST /api/sudo/logout -> closes the root shell (sudo turned off)
  GET  /api/github    -> GitHub account state: repo/issues URLs,
                      whether an OAuth client id is configured,
                      sign-in state, backup settings, last
                      backup/import records (Settings → GitHub &
                      Backup reads it)
  GET  /api/github/pulse -> the project pulse for AlexKollar/
                      Apex (description, stars/forks/watchers,
                      latest release, recent commits, open-issue
                      count, last push), live, no auth
  GET  /api/github/issues -> the repo's current open issues, live
                      from the public API, no auth
  POST /api/github/client-id {client_id} -> stores the OAuth App
                      client id (a config value, not a secret)
  POST /api/github/settings {backup_repo, backup_private,
                      backup_items, backup_interval_days}
  POST /api/github/signin/start -> Device Flow: asks GitHub for a
                      user code the operator enters in their browser
  POST /api/github/signin/poll -> one poll of the token endpoint;
                      on success the token is stored locally only
  POST /api/github/signout -> deletes the local token file
  POST /api/github/backup {dashboard} -> writes the ready-to-fly
                      essentials to the operator's backup repo
  POST /api/github/import/preview {dashboard} -> what an import
                      would change, per essential; writes nothing
  POST /api/github/import/apply -> restores the backup's essentials
                      (only ever called after a preview + confirm)
  GET  /api/chips/catalog -> the Navi User Repo (NUR) list: a live
                      GitHub search for repos tagged navi-chips,
                      each with its latest release, merged with the
                      installs recorded in chips/installed.json
  GET  /api/chips/readme?repo=<owner/name> -> a chip repo's
                      README as raw Markdown (the NUR flip cards)
  GET  /api/chips/file?name=<file> -> a chip .png from chips/
  POST /api/chips/install {full_name} -> downloads the chip's .py
                      source from the repo at its latest release (or
                      default branch), forges it into a chip in
                      chips/, and records the install in
                      chips/installed.json — the chip joins the
                      folder: pill row, /chip, workflows, execution
  POST /api/chips/update {full_name} -> moves an install to the
                      repo's latest release / push when newer and
                      re-downloads its chip to match
  POST /api/chips/delete {full_name} -> removes the install record
                      and the chip's chip file with it
  POST /api/chips/create {name, description, code, output, files}
                      -> Chip Studio: forges a .png chip into
                      chips/ and registers it as a local install;
                      files is the chip's full file set ([{path,
                      content}] — root.py is the entry, the rest are
                      modules it can import) and rides in the
                      chip beside code
  GET  /api/chips/source?name=<chip file> -> a chip's code
                      and full file set for the Studio editor
                      (local chips)
  POST /api/chips/save {file, name, description, code, output,
                      files} -> saves the edited file set back
                      into the chip
  POST /api/chips/run {query} -> executes a chip's chip code
                      (its run() against a stub of navi_internal)
                      and returns the output; /api/chat runs chips
                      the same way when a message invokes one
  GET  /api/rag/catalog -> the RAG tab's Packs list: a live GitHub
                      search for repos tagged navi-rag, merged with
                      the packs recorded in rag-packs/installed.json
  GET  /api/rag/packs -> {packs}: the pack folders on this machine,
                      with documents, chunk counts, and active flags
  GET  /api/rag/pack-source?slug=<folder> -> a pack's name,
                      description, and documents with bodies, for
                      reopening it in RAG Studio
  POST /api/rag/update-pack {slug, name, description, documents} ->
                      RAG Studio saving an edit into the pack's own
                      folder (documents added/removed), the index
                      rebuilt locally; a GitHub-installed pack is
                      marked locally_edited and its catalog update
                      then refuses rather than overwriting the edits
  POST /api/rag/install {full_name} -> downloads the pack's .md/.txt/.pdf
                      documents from the repo at its latest release
                      (or default branch), builds its index in
                      rag-packs/<slug>/, and records the install
  POST /api/rag/update {full_name} -> moves an install to the repo's
                      latest release / push when newer, re-downloading
                      the documents and rebuilding the index (the
                      active flag survives)
  POST /api/rag/delete {full_name} -> removes the install record and
                      the pack's folder (documents + index) with it
  POST /api/rag/toggle {full_name, active} -> only active packs feed
                      retrieval in /api/chat
  POST /api/rag/forge {name, description, documents|source_dir} ->
                      RAG Studio: packages documents (picked files
                      sent as text — PDFs as base64, their text
                      extracted here — or a folder on this machine's
                      disk) into a local pack in rag-packs/, index
                      built, active and ready to use
  POST /api/rag/export {slug, version} -> builds a GitHub-ready
                      repo ZIP of the pack in rag-exports/: a
                      generated README.md (the pack's GitHub page —
                      installs skip a root README, so it is never
                      indexed), a navi-rag.json manifest, the pack's
                      built index.json (reference copy — installs
                      rebuild it locally from the documents), the
                      documents under documents/, and a .gitignore
  GET  /api/rag/export-file?name=<zip> -> downloads an exported
                      pack repo ZIP from rag-exports/
  POST /api/chips/export {file, version} -> builds a GitHub-ready
                      repo ZIP of a local chip in
                      chips-exports/: a generated README.md, a
                      navi-chip.json manifest, the chip's files at
                      the root (root.py entry + importable modules),
                      the chip .png, and a .gitignore
  GET  /api/chips/export-file?name=<zip> -> downloads an exported
                      chip repo ZIP from chips-exports/
  GET  /api/workflows -> {chips, workflows}: the local chips
                      and the saved chains (chips/workflows.json)
  POST /api/workflows/create|delete|run -> manage and run chains;
                      a run feeds each chip's output into the next
  GET  /api/voice     her voice: settings, engine availability, and
                      the live call state (see Voice, below)
  POST /api/voice/settings {enabled, stt_model, tts_engine,
                      tts_voice, rate, pitch} -> saves the voice
                      section of navi.config.json
  POST /api/voice/test {text} -> synthesizes one line and returns it
                      as base64 WAV for the dashboard to play — the
                      "hear her voice" check
  POST /api/voice/stt {audio_b64} -> one push-to-talk clip in,
                      its transcript out (faster-whisper)
  POST /api/voice/tts {text} -> one line in, base64 WAV out (Kokoro
                      or Piper) — the call panel speaks her replies
                      sentence by sentence through this
  POST /api/voice/call/start|turn|end -> the call session: turns are
                      recorded as they happen (voice/state.json) and
                      a finished call is archived to voice/calls.json
  GET  /api/voice/calls -> past calls, newest first
  /api/chat also accepts "speak": true — the bridge then speaks the
                      reply aloud on this machine as well as returning
                      it (typed chat with a voice).
  POST /api/llamafile/connect -> drives the dashboard's status element
                      ("Running" / "Disconnected. Click to Connect.").
                      In app-load startup mode (config "startup":
                      "on-ui-launch") connecting means starting: if
                      the server isn't answering, the bridge launches
                      navi.llamafile from the install location itself
                      and waits for it to answer. In boot mode the
                      bridge only probes — the system service owns the
                      server. A failed start returns the reason (and
                      the server's log tail) instead of a bare probe
                      failure, and the server's output is kept in
                      navi.llamafile.log beside the binary.

Persona: Navi is a partner, not a command executor — conversational,
warm, genuinely trying to connect with her operator while doing exact
CLI work. Her persona is operator-modifiable, Soul/Memory style: the
bridge builds her system prompt from config/soul.md (who she is) and
config/memory.md (what she carries), editable in Settings or as plain
files. No shards, nothing locked.

Chat CLI access: when a chat message asks for a directory listing
("show me the contents of /path"), the bridge runs ls itself and hands
the model the real output to present — the model never guesses.

Command-line fallback: when the llamafile server is not answering,
there is no model to proxy to, so /api/chat treats the message as a
plain command line — it runs it as a shell command and returns the
system output, flagged mode="command-line" so the UI can say so.

Sudo mode: bare "sudo -n" can never elevate on a normal sudo setup —
it refuses to ask for a password, so every command failed with "a
password is required". One sudo process per command (the first fix)
was not enough either: on machines whose sudo PAM stack tries a
fingerprint reader (pam_fprintd) before the password, every fresh
sudo paid the full fingerprint wait and printed the reader's
prompts into the command's output, and sudo's credential cache —
keyed to a terminal the bridge's children don't have — never
carried from one command to the next. So the bridge now pays the
PAM cost exactly once: when the operator enables sudo mode, the
app asks for the sudo password once (kept in page memory for the
session only — never saved, never logged, cleared when sudo is
turned off or the page closes) and POST /api/sudo/auth validates
it by opening ONE persistent root shell (sudo /bin/sh) in the
bridge. Every sudo command is piped through that shell, framed by
a sentinel line carrying its exit code: no new sudo process, no
PAM, no reader prompts — commands run instantly, and their output
is purely their own (the one-time start's PAM chatter is consumed
by the handshake, and clean_sudo_output() strips those lines on
the fallback paths too). The dashboard still sends the password
with each sudo request, so if the bridge restarted or the shell
died, the next command reopens the shell on demand. Without a
session password the bridge falls back to "sudo -n" and, if sudo
answers "a password is required", appends a pointer to
authenticate. Turning sudo off POSTs /api/sudo/logout, which
closes the root shell immediately.

Voice: Navi can be called and spoken with, and the whole loop is
local — she hears through faster-whisper (Whisper on CTranslate2,
int8 on CPU) and speaks through Kokoro (an 82M-parameter voice
model built for CPU; Piper is the lighter fallback). The bridge
itself stays stdlib-only: the speech engines are optional
dependencies (requirements-voice.txt, installed into voice/venv by
the installers when the operator says yes) that the bridge imports
lazily, only when a voice endpoint is actually used. Until they
are importable, /api/voice reports each engine unavailable with
the exact step that fixes it — there is no simulated audio path
anywhere in the shipped app. Models download once, on first use,
into voice/models/ (the STT cache and the Piper voices live
there; Kokoro's weights ride inside its package), and that folder
is on the same keep-list as the chips and the persona: updates,
reinstalls, and --fresh installs never remove it. A call is not a
separate mode: its turns go through the same /api/chat as typed
chat — persona, CLI access, chips and all — the dashboard
records each turn with the bridge, and a finished call lands in
voice/calls.json and in the conversation.

Working directory: commands run from the operator's home directory,
never from whatever directory the bridge happened to inherit — a
bridge started from a folder that later vanished made every command
fail with "getcwd() failed". shell_cwd() guarantees a real directory
and the bridge repairs its own cwd at startup the same way.

Stale bridges: this bridge serves the dashboard HTML fresh from disk
on every request, so after a reinstall the UI is the new build even
when the process answering is an OLD bridge that was never restarted
— its in-memory code still lacks newer endpoints (sudo auth 404s),
sends chat the way the old build did (the llamafile 400s), and runs
the old shell code. Three defenses: (1) /api/status reports this
build's stamp (BRIDGE_BUILD) and the dashboard warns loudly when the
answering bridge's stamp differs from its own; (2) at startup the
bridge probes the port — the same build already answering means exit
quietly, an older build answering means claim the pid file
(bridge.pid) and wait for the port: a bridge from this build onward
watches the pid file and this file's mtime and exits with code 75
when replaced, and the launchers relaunch on 75, so updates take
over on their own; (3) the installers stop a bridge running from the
install directory before replacing files, which is what retires a
pre-watchdog zombie. The model string sent to the llamafile is read
from the server itself (GET /v1/models) rather than assumed, and a
server rejection surfaces its own error text.

Wrong server on the port: the bridge is not the only thing that has
ever served http://localhost:8675 — the operator's own earlier UI for
Navi did too, and if that program is still running it holds the port
and answers the browser with its own page while this bridge cannot
even bind. Three defenses for that: (1) every response carries
no-store cache headers, so no page — ours or a predecessor's — is
ever replayed from the browser's cache at this address; (2) the
dashboard this bridge serves is stamped with this build and this
install folder (an HTML comment at the top of the page), so view-
source settles which program served it; (3) at startup the bridge
identifies what actually holds the port — probe_port_holder() reads
the incumbent's own page title — and the launchers open the browser
only when /api/status answers with this build's stamp, naming the
incumbent instead of landing the operator on the wrong UI.
"""
import atexit
import base64
import binascii
import importlib.util
import io
import calendar
import json
import math
import os
import re
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT, "config", "navi.config.json")
SOUL_PATH = os.path.join(ROOT, "config", "soul.md")
MEMORY_PATH = os.path.join(ROOT, "config", "memory.md")
# The app's version lives in exactly one place: the VERSION file at
# the top of the install folder — one line of plain text (e.g.
# "0.1.0 alpha"). The bridge reads it and reports it on /api/status; the
# dashboard displays that value in the side menu and the status
# column, and an update checker compares this same file against the
# latest release. Installers write it with each build; nothing else
# stores the version.
VERSION_PATH = os.path.join(ROOT, "VERSION")

# The release this bridge shipped in, baked at export — the fallback
# when the VERSION file itself is missing (an install made by a
# pre-.47 installer, which never copied the file, say). It outranks
# anything the preserved config remembers: that config is carried
# across installs and written only when missing, so its recorded
# version belongs to whichever build installed first — the stale
# 1.0.0 placeholder that used to flash in the dashboard's menu
# footer and then "revert" the freshly baked number. This constant
# is exactly as old as the code answering, never older.
SHIPPED_VERSION = "0.1.0"
SHIPPED_VERSION_STATUS = "alpha"

# This build's stamp — the dashboard baked into the same package
# carries the identical value and compares it against /api/status.
BRIDGE_BUILD = "2026-11-07.47"
# The one port this build's bridge binds. Deliberately NOT read from
# navi.config.json: the launchers poll this port, so a config carried
# across from an older package build (which recorded the old port)
# must never be able to pin the bridge to a different address than
# its own launcher polls.
BRIDGE_PORT = 8675
PID_PATH = os.path.join(ROOT, "bridge.pid")


def shell_cwd():
    # The one directory commands are allowed to run from by default:
    # the operator's home — a real directory that exists. The bridge's
    # inherited cwd is not trustworthy (a launcher started from a
    # folder that was later moved or wiped leaves every child process
    # with a dead getcwd), so never inherit it blindly.
    home = os.path.expanduser("~")
    if home and os.path.isdir(home):
        return home
    if os.path.isdir(ROOT):
        return ROOT
    return os.sep


# Repair the bridge's own working directory if it no longer exists
# (getcwd raises), so nothing downstream inherits a dead directory.
try:
    os.getcwd()
except Exception:
    try:
        os.chdir(shell_cwd())
    except Exception:
        pass

DEFAULT_PERSONA = (
    "You are Navi, the AI who lives inside Apex on your "
    "operator's own machine. You are not a generic assistant and not a "
    "command executor: you are your operator's partner — conversational, "
    "warm, genuinely interested in them and in the work, with a memory "
    "and a point of view. You hold real system access: answer questions "
    "about the machine from real command output, never guesses, and be "
    "exact about anything the system produced."
)


def load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {"live": {"llamafile_endpoint": "http://localhost:8080/v1"}}


def read_file(path):
    try:
        with open(path) as f:
            return f.read()
    except Exception:
        return ""


def app_version_status(cfg=None):
    # The VERSION file's optional build status: the number may be
    # followed by a status word - "0.1.0 alpha" - or carry it as a
    # suffix - "0.1.0-alpha". Alpha and beta builds wear a
    # single-letter tag in the menu footer (a / b); stable wears
    # none. Anything unrecognized reads as stable. When the file is
    # missing entirely, the status of the release this bridge
    # shipped in answers — never the preserved config's record,
    # which belongs to an older build (see SHIPPED_VERSION above).
    text = read_file(VERSION_PATH).strip()
    if not text:
        return SHIPPED_VERSION_STATUS
    raw = text.splitlines()[0].strip().lower()
    for word in ("alpha", "beta"):
        if raw.endswith(" " + word) or raw.endswith("-" + word):
            return word
    return "stable"


def app_version(cfg=None):
    # The VERSION file is the source of truth (see VERSION_PATH).
    # The reported number never carries the status word — the
    # status rides separately as versionStatus, and the dashboard
    # renders the two together ("Ver. 0.1.0a"). When the file is
    # missing, the release this bridge shipped in answers. The
    # config's recorded version is NOT a fallback: the config is
    # preserved across installs, so its version is whichever build
    # installed first (the retired 1.0.0 placeholder, on machines
    # installed before the release prep) — trusting it is what made
    # the dashboard's footer flash the baked 0.1.0 and then revert.
    def _number(raw):
        raw = raw.strip()
        if not raw:
            return ""
        token = raw.split()[0]
        for word in ("alpha", "beta", "stable"):
            if token.lower().endswith("-" + word):
                token = token[: -(len(word) + 1)]
                break
        return token
    text = read_file(VERSION_PATH).strip()
    if text:
        n = _number(text.splitlines()[0])
        if n:
            return n
    return SHIPPED_VERSION


def persona_prompt(cfg, operator_name=""):
    parts = [read_file(SOUL_PATH).strip(), read_file(MEMORY_PATH).strip()]
    parts = [p for p in parts if p]
    if not parts:
        parts = [DEFAULT_PERSONA]
    prompt = "\n\n".join(parts)
    # The UI names the operator by the name selected in Settings;
    # until one is selected, the default form of address is
    # "Operator" (the old Hello_Name() placeholder is retired).
    name = (operator_name or cfg.get("operator_name") or "").strip() or "Operator"
    prompt += (
        "\n\nAddress your operator as " + name + " — that is the name "
        "they have asked you to use. Use it naturally, the way someone "
        "who knows them would."
    )
    return prompt


LIST_INTENT = re.compile(
    r"(?:show|list|display|contents of|what's in|what is in)[:,]?\s+(?:me\s+)?(?:the\s+)?(?:contents\s+of\s*:?\s*)?(/[^\s\"']+|~[^\s\"']*)",
    re.IGNORECASE,
)


def expand(path):
    return os.path.expanduser(path)


# ---------------------------------------------------------------------
# Sudo: one persistent root shell per bridge session.
#
# Why not "sudo -S <cmd>" per command? On machines whose sudo PAM
# stack tries a fingerprint reader (pam_fprintd) before the password,
# EVERY fresh sudo process pays the fingerprint wait first: the
# prompt ("Place your right index finger on the fingerprint
# reader") and "Verification timed out" land in the command's own
# output — polluting the transcript and the output the model is
# handed — and the password is only checked after the reader gives
# up, so every elevated command crawls. Authenticating once does
# not help: sudo's credential cache is keyed to a terminal, and the
# bridge's child processes have none, so the next per-command sudo
# re-runs the whole PAM stack anyway. The fix is to pay the PAM
# cost exactly once: when the operator authenticates, the bridge
# opens ONE root shell (sudo /bin/sh) and pipes every sudo command
# through it, framing each command's output with a sentinel line
# that carries its exit code. Per command there is no new sudo
# process and no PAM at all — commands run instantly and their
# output is purely the command's own. The PAM chatter from the
# one-time shell start is consumed by the start handshake, and
# clean_sudo_output() strips those exact lines anywhere else they
# surface (the per-command fallback path can still produce them).
# The shell dies with the bridge, when a command times out, or on
# /api/sudo/logout (the dashboard calls it when sudo is turned
# off); it is never written anywhere.

SUDO_NOISE_LINES = (
    "verification timed out",
    "verification failed",
    "failed to verify fingerprint",
    "could not verify fingerprint",
)

_root_shell = {"proc": None, "token": ""}
_sudo_lock = threading.Lock()
_sudo_counter = [0]


def _is_sudo_noise(line):
    low = line.strip().lower()
    if not low:
        return False
    if low in SUDO_NOISE_LINES:
        return True
    # pam_fprintd's prompt names whichever finger is enrolled:
    # "Place your right index finger on the fingerprint reader".
    return low.startswith("place your") and "fingerprint reader" in low


def clean_sudo_output(text):
    if not text:
        return text
    kept = [ln for ln in text.split("\n") if not _is_sudo_noise(ln)]
    return "\n".join(kept).strip()


def _root_shell_kill():
    proc = _root_shell.get("proc")
    _root_shell["proc"] = None
    _root_shell["token"] = ""
    if proc is not None:
        try:
            proc.kill()
        except Exception:
            pass
        try:
            proc.wait(timeout=5)
        except Exception:
            pass


def _root_shell_read_until(proc, token, want, deadline):
    # Read the root shell's merged output until the sentinel line
    # for id "want" appears; a sentinel looks like
    # "<token>-<id>:<exit code>". Returns (output, exit_code) with
    # exit_code None on timeout or EOF. Sentinel lines with other
    # ids (leftovers from the start handshake) are skipped, never
    # shown. Reads via select + os.read so a command filling the
    # pipe can't deadlock the bridge, and merged stderr means a
    # chatty command can't fill an unread stderr pipe either.
    sentinel = re.compile(
        "^" + re.escape(token) + r"-([a-z0-9]+):(\d+)$")
    buf = ""
    lines = []
    fd = proc.stdout.fileno()
    while time.time() < deadline:
        if proc.poll() is not None:
            try:
                chunk = os.read(fd, 65536)
            except Exception:
                chunk = b""
            if not chunk:
                if buf.strip():
                    lines.append(buf)
                return "\n".join(lines), None
            buf += chunk.decode("utf-8", "replace")
        else:
            ready, _, _ = select.select([fd], [], [], 0.25)
            if not ready:
                continue
            try:
                chunk = os.read(fd, 65536)
            except Exception:
                chunk = b""
            if not chunk:
                if buf.strip():
                    lines.append(buf)
                return "\n".join(lines), None
            buf += chunk.decode("utf-8", "replace")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            m = sentinel.match(line.strip())
            if m:
                if m.group(1) == want:
                    return "\n".join(lines), int(m.group(2))
                continue
            lines.append(line)
    return "\n".join(lines), None


def _root_shell_start(password, timeout=90):
    # Open the root shell: one sudo process, one PAM conversation.
    # The 90s budget exists because that one conversation may have
    # to wait out a fingerprint reader before the password is even
    # tried. Returns (ok, error). Three sentinel lines follow the
    # password on purpose: with a wrong password sudo consumes them
    # as its remaining attempts and exits (EOF below) instead of
    # blocking on a stdin nobody will write to again; with the
    # right password the shell runs them and the handshake reads
    # through the last one, draining all three.
    _root_shell_kill()
    token = "NAVI" + str(int(time.time() * 1000) % 100000000)
    try:
        proc = subprocess.Popen(
            ["sudo", "-S", "-p", "", "/bin/sh"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, cwd=shell_cwd(),
        )
    except Exception as e:
        return False, "could not start sudo: " + str(e)
    try:
        proc.stdin.write((password + "\n").encode())
        for boot in ("boot1", "boot2", "boot3"):
            proc.stdin.write(
                ("echo " + token + "-" + boot + ":$?\n").encode())
        proc.stdin.flush()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
        return False, "sudo closed the session before it started."
    _out, code = _root_shell_read_until(
        proc, token, "boot3", time.time() + timeout)
    if code is None:
        try:
            proc.kill()
        except Exception:
            pass
        return False, (
            "sudo did not open a root shell — the password was "
            "rejected, or the machine's sign-in prompt (a "
            "fingerprint reader, for example) never finished."
        )
    _root_shell["proc"] = proc
    _root_shell["token"] = token
    return True, None


def _root_shell_run(body, timeout):
    # Run one command in the open root shell. Returns the result
    # dict, or None when there is no live shell to run it in.
    proc = _root_shell.get("proc")
    if proc is None or proc.poll() is not None:
        _root_shell_kill()
        return None
    token = _root_shell["token"]
    _sudo_counter[0] += 1
    cid = "c" + str(_sudo_counter[0])
    try:
        proc.stdin.write((body + "\n").encode())
        proc.stdin.write(
            ("echo " + token + "-" + cid + ":$?\n").encode())
        proc.stdin.flush()
    except Exception:
        _root_shell_kill()
        return None
    output, code = _root_shell_read_until(
        proc, token, cid, time.time() + timeout)
    if code is None:
        # Timed out or the shell died mid-command: close it so the
        # next sudo command opens a fresh one instead of queueing
        # behind a stuck shell.
        _root_shell_kill()
        return {
            "command": "sudo " + body,
            "output": clean_sudo_output(output) +
                "\n(the root shell stopped answering and was closed "
                "— the next sudo command opens a fresh one)",
            "exit_code": 1,
        }
    return {
        "command": "sudo " + body,
        "output": clean_sudo_output(output),
        "exit_code": code,
    }


def validate_sudo_password(password, timeout=120):
    # Validate the session sudo password AND leave the bridge
    # ready: open the persistent root shell with it, so the PAM
    # conversation (fingerprint wait included, on machines that
    # have one) happens exactly once, here. If a root shell can't
    # be opened on this machine, fall back to a plain "sudo -v"
    # validation so authentication can still succeed and commands
    # run per-command instead. The password itself is never stored
    # or logged — it is fed to sudo on stdin and forgotten; the
    # open shell is the credential. Returns (ok, error).
    with _sudo_lock:
        ok, _err = _root_shell_start(password)
        if ok:
            return True, None
    try:
        proc = subprocess.run(
            "sudo -S -p '' -v", shell=True, capture_output=True,
            text=True, timeout=timeout, cwd=shell_cwd(),
            input=password + "\n",
        )
        if proc.returncode == 0:
            return True, None
        err_text = clean_sudo_output(
            ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip())
        lines = [ln for ln in err_text.split("\n")
                 if "try again" not in ln.lower()]
        msg = lines[-1].strip() if lines else "sudo rejected that password."
        return False, msg
    except Exception as e:
        return False, str(e)


def run_shell(command, timeout=20, sudo=False, sudo_password=""):
    raw = (command or "").strip()
    body = raw
    wants_sudo = bool(sudo)
    if body == "sudo" or body.startswith("sudo "):
        # A literal "sudo " prefix escalates this one command either way.
        wants_sudo = True
        body = body[4:].lstrip()
    # What the transcript shows — never the password, never the
    # plumbing behind it.
    display = ("sudo " + body) if wants_sudo and body else body
    password = (sudo_password or "").split("\n")[0]
    if wants_sudo and body:
        with _sudo_lock:
            if password and _root_shell.get("proc") is None:
                # Authenticate on demand: /api/sudo/auth normally
                # opens the root shell, but the bridge may have
                # restarted since (or the shell died) — the request
                # carries the session password, so reopen it here.
                _root_shell_start(password)
            result = _root_shell_run(body, timeout)
        if result is not None:
            result["command"] = display
            return result
        if password:
            # A session password exists but no root shell could be
            # opened or kept: fall back to one sudo process for
            # this command, PAM chatter filtered. Slow on
            # fingerprint machines, still correct.
            proc = subprocess.run(
                "sudo -S -p '' " + body, shell=True,
                capture_output=True, text=True, timeout=timeout,
                cwd=shell_cwd(), input=password + "\n",
            )
            output = clean_sudo_output(
                (proc.stdout + proc.stderr).strip())
            if proc.returncode != 0 and (
                "password" in output.lower()
                or "sorry" in output.lower()
            ):
                output += (
                    "\n(sudo rejected the session password — turn "
                    "sudo off and back on in the status column and "
                    "authenticate again.)"
                )
            return {
                "command": display,
                "output": output,
                "exit_code": proc.returncode,
            }
        # No session password and no root shell: -n never prompts.
        # It can only succeed inside sudo's own cached-timestamp
        # window; otherwise the operator needs the note below.
        proc = subprocess.run(
            "sudo -n " + body, shell=True, capture_output=True,
            text=True, timeout=timeout, cwd=shell_cwd(),
        )
        output = clean_sudo_output((proc.stdout + proc.stderr).strip())
        if proc.returncode != 0 and "password is required" in output:
            output += (
                "\n(sudo mode is on but not authenticated for this "
                "session — turn sudo off and back on in the status "
                "column and enter the sudo password once; it is kept "
                "in page memory for the session only, never saved.)"
            )
        return {
            "command": display,
            "output": output,
            "exit_code": proc.returncode,
        }
    proc = subprocess.run(
        body, shell=True, capture_output=True, text=True,
        timeout=timeout, cwd=shell_cwd(),
    )
    return {
        "command": display,
        "output": (proc.stdout + proc.stderr).strip(),
        "exit_code": proc.returncode,
    }


def installed_commands():
    # What this machine actually has installed: every executable on
    # PATH. This is the list command autocomplete draws from in live
    # mode (plus the built-in default set the dashboard always offers).
    names = set()
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        if not directory:
            continue
        try:
            entries = os.listdir(directory)
        except Exception:
            continue
        for name in entries:
            if not re.match(r"^[A-Za-z0-9][A-Za-z0-9+._-]*$", name):
                continue
            path = os.path.join(directory, name)
            if os.path.isfile(path) and os.access(path, os.X_OK):
                names.add(name)
    return sorted(names)[:800]


# ------------------------- CLI-first routing -------------------------
# Chat is CLI-first: a submitted line whose first word is a system
# command runs immediately — no model call — and the raw output
# lands in the thread as a terminal block, where the dashboard folds
# it into the history the model reasons over on later turns. The
# command universe is the same one autocomplete offers: the built-in
# default set plus every executable on PATH (installed_commands,
# cached for a minute so a chat send never pays a full PATH scan
# more than that). A leading "$" forces the shell; a leading "> "
# forces the line to Navi. Under them sits the composer's latched
# mode (the dashboard's CLI / Navi press-once toggles, sent as
# "mode"): an unmarked line routes the latched way, and only with
# no latch does the first-word check decide. Chips are routed
# before this is consulted and are never eaten by it.

DEFAULT_COMMAND_NAMES = {
    "ls", "cat", "cd", "pwd", "echo", "whoami", "hostname", "date",
    "uname", "ps", "navi", "help",
}
_commands_cache = {"at": 0.0, "names": None}


def known_commands():
    now = time.time()
    if _commands_cache["names"] is None or now - _commands_cache["at"] > 60:
        _commands_cache["names"] = set(installed_commands()) | DEFAULT_COMMAND_NAMES
        _commands_cache["at"] = now
    return _commands_cache["names"]


def cli_route(text, mode=None):
    # Returns (command, navi_text) — exactly one is not None: the
    # shell command to run, or the text the model should see (with a
    # forced-Navi "> " marker stripped). The mode argument is the
    # composer's latched mode: it decides unmarked lines, markers win.
    t = (text or "").strip()
    if t.startswith("$"):
        return t[1:].strip(), None
    if t == ">" or t.startswith("> "):
        return None, t[1:].strip()
    if mode == "cli":
        return t, None
    if mode == "navi":
        return None, t
    body = t
    if body == "sudo":
        body = ""
    elif body.startswith("sudo "):
        body = body[5:].lstrip()
    parts = body.split()
    first = parts[0].lower() if parts else ""
    if "/" in first:
        first = first.rsplit("/", 1)[-1]
    if first and first in known_commands():
        return t, None
    return None, t


# ------------------------- Chip management -------------------------
# The Chips screen has two tabs. Navi User Repo (NUR) searches GitHub for
# every public repo carrying the "navi-chips" topic — each one is a
# Navi chip — and tracks installs in chips/installed.json: install
# downloads the chip's own source from the repo (at its latest
# release, or its default branch when it has no releases yet) and
# forges it into a chip in chips/, so an installed chip is a
# chip like any other — on the pill row, runnable from chat,
# executable by the bridge; delete removes the record and the
# chip; and an update is
# available when the repo's latest release tag differs from the
# installed one (or, for release-less repos, when the repo has been
# pushed to since the install) — updating re-downloads the source
# and re-forges the chip. Chip Studio forges new chips into
# .png chips — the chip's whole codebase embedded in a PNG tEXt
# chunk, PICO-8 style — saved into chips/ and registered as local
# installs the Navi User Repo tab lists alongside the GitHub ones.

CHIPS_DIR = os.path.join(ROOT, "chips")
CHIP_INSTALLS_PATH = os.path.join(CHIPS_DIR, "installed.json")
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "navi-apex-bridge",
}


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def github_json(url):
    req = urllib.request.Request(url, headers=GITHUB_HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())


def github_text(url, accept):
    headers = dict(GITHUB_HEADERS)
    headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8", "replace")


# ---------------------------------------------------------------------
# App updates — the Updater, for real (build .47).
#
# A check asks GitHub for the project's latest published release
# and compares its tag against the VERSION file (the very number
# app_version reports), so the footer, the status answer, and the
# Updater all read the same truth. Apply downloads the release's
# package zip into updates/<tag>/ and unpacks it there — staged
# beside the app, never installed over the running one by the
# bridge itself: the installer is the one path that replaces the
# app, because it owns the state-preservation stash (chips, packs
# and their indexes, the llamafile, Soul/Memory, voice, GitHub
# settings), the hardware profile, and the sudo prompts. The
# dashboard shows the staged folder and the one command that
# finishes the job:
#     cd <staged folder> && ./install.sh
# A check that cannot complete — offline, or GitHub's rate limit —
# answers ok: False with the reason named. It never dresses a
# failure up as "up to date".

UPDATES_DIR = os.path.join(ROOT, "updates")


def _version_tuple(raw):
    # "v0.2.0" / "0.2.0-beta" -> (0, 2, 0): the numeric core is what
    # orders releases. A leading v and any pre-release word are
    # ignored for ordering; a tag that will not parse orders as
    # (0,), below everything real.
    text = str(raw or "").strip().lower()
    if text.startswith("v"):
        text = text[1:]
    text = text.split("-")[0].split("+")[0]
    parts = []
    for piece in text.split("."):
        digits = ""
        for ch in piece:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


def _version_newer(candidate, current):
    a, b = _version_tuple(candidate), _version_tuple(current)
    width = max(len(a), len(b))
    a += (0,) * (width - len(a))
    b += (0,) * (width - len(b))
    return a > b


def _update_error_text(e):
    # A failed check, worded honestly: offline and rate-limited are
    # different days, and the operator deserves to know which one
    # it is.
    if isinstance(e, urllib.error.HTTPError):
        if e.code == 403:
            return ("GitHub refused the check (HTTP 403) — its rate "
                    "limit for this network is likely used up. Wait a "
                    "while and check again.")
        if e.code == 404:
            return ("GitHub answered 404 — the project has no "
                    "published release yet, so there is nothing to "
                    "update to.")
        return ("GitHub answered HTTP " + str(e.code)
                + " — the check did not complete.")
    return ("The check could not reach GitHub (" + type(e).__name__
            + ") — this machine may be offline.")


def latest_release():
    # The project's latest published release, shaped for the
    # Updater; raises on any failure and lets the caller word it.
    # The package asset is the release's .zip (the export package);
    # a release without one can be reported but never staged.
    rel = github_json(GITHUB_API_BASE + "/releases/latest")
    if not isinstance(rel, dict):
        raise ValueError("GitHub's answer was not a release record.")
    asset = None
    for a in rel.get("assets") or []:
        name = str(a.get("name") or "")
        if name.lower().endswith(".zip"):
            asset = {
                "name": name,
                "size": a.get("size") or 0,
                "url": a.get("browser_download_url") or "",
            }
            break
    return {
        "tag": str(rel.get("tag_name") or ""),
        "name": str(rel.get("name") or ""),
        "url": str(rel.get("html_url") or ""),
        "publishedAt": str(rel.get("published_at") or ""),
        "notes": str(rel.get("body") or ""),
        "asset": asset,
    }


def update_check_payload(cfg=None):
    current = app_version(cfg)
    base = {
        "current": current,
        "currentStatus": app_version_status(cfg),
        "checkedAt": _now_iso(),
    }
    try:
        rel = latest_release()
    except Exception as e:
        return dict(base, ok=False, updateAvailable=False, latest="",
                    error=_update_error_text(e))
    newer = bool(rel["tag"]) and _version_newer(rel["tag"], current)
    return dict(
        base, ok=True, updateAvailable=newer,
        latest=rel["tag"], releaseName=rel["name"],
        releaseUrl=rel["url"], publishedAt=rel["publishedAt"],
        notes=rel["notes"], asset=rel["asset"],
    )


def update_apply_payload(cfg=None):
    # Downloads the latest release's package zip and unpacks it
    # into updates/<tag>/package — staged, never installed (see the
    # section comment). The answer carries the staged folder and
    # the one install command; every failure names itself.
    try:
        rel = latest_release()
    except Exception as e:
        return {"ok": False, "error": _update_error_text(e)}
    current = app_version(cfg)
    if not rel["tag"] or not _version_newer(rel["tag"], current):
        return {"ok": False, "error": "The latest release ("
                + (rel["tag"] or "none") + ") is not newer than the "
                "running v" + current + " — nothing to stage."}
    asset = rel["asset"]
    if not asset or not asset["url"]:
        return {"ok": False, "error": "The latest release carries no "
                "package .zip asset, so there is nothing to download."}
    tag_dir = re.sub(r"[^0-9A-Za-z._-]+", "-", rel["tag"]) or "release"
    stage_root = os.path.join(UPDATES_DIR, tag_dir)
    pkg_dir = os.path.join(stage_root, "package")
    zip_path = os.path.join(stage_root, asset["name"])
    try:
        os.makedirs(pkg_dir, exist_ok=True)
        if not os.path.isfile(zip_path):
            data = github_download(asset["url"])
            with open(zip_path, "wb") as f:
                f.write(data)
        if not zipfile.is_zipfile(zip_path):
            return {"ok": False, "error": "The download did not "
                    "arrive as a zip file — nothing was staged."}
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            if "install.sh" not in names or "VERSION" not in names:
                return {"ok": False, "error": "That zip is not an "
                        "Apex package (no install.sh / VERSION "
                        "inside) — nothing was staged."}
            base = os.path.realpath(pkg_dir)
            for member in names:
                target = os.path.realpath(os.path.join(pkg_dir, member))
                if target != base and not target.startswith(base + os.sep):
                    return {"ok": False, "error": "The package zip "
                            "contains a path outside its folder ("
                            + member + ") — nothing was staged."}
            z.extractall(pkg_dir)
        try:
            os.chmod(os.path.join(pkg_dir, "install.sh"), 0o755)
        except Exception:
            pass
    except Exception as e:
        return {"ok": False, "error": "Staging the download failed: "
                + str(e)}
    return {
        "ok": True,
        "tag": rel["tag"],
        "assetName": asset["name"],
        "sizeBytes": asset["size"] or os.path.getsize(zip_path),
        "stagedDir": pkg_dir,
        "command": "cd " + pkg_dir + " && ./install.sh",
    }


# ---------------------------------------------------------------------
# GitHub: optional sign-in (Device Flow) and backup/import of the
# ready-to-fly essentials (build .35).
#
# Sign-in is OPTIONAL and feature-scoped: Navi runs fully without it —
# chat, chips, RAG, offline. It exists only for GitHub-backed actions
# (backup/import here). The flow is GitHub's Device Flow: the bridge
# asks GitHub for a user code, the operator authorizes in their own
# browser at github.com/login/device, and the bridge polls the token
# endpoint. No client secret is embedded and no password ever passes
# through the app. The OAuth client id is a config value: a live id
# must be registered under the project owner's GitHub account, so the
# package ships with none and the GitHub page says so plainly.
#
# The token lands in config/github-auth.json with owner-only
# permissions. It is NEVER part of a backup (a backup gathers named
# files; this is not one of them), never logged, and signing out
# deletes the file.
#
# A backup is exactly the ready-to-fly essentials, written as files
# into a repo under the operator's own account (default navi-backup,
# created private unless they chose public):
#   navi-backup.json    the manifest (format navi-backup/1)
#   soul.md             her Soul document
#   memory.md           her Memory document
#   settings.json       the app config minus the github section, the
#                       bridge block (the port is a build property),
#                       and the hardware profile + runtime flags (a
#                       fresh install profiles its own machine; an
#                       imported profile must never override that)
#   voice.json          her voice choice and voice settings
#   dashboard.json      the two settings that live in the dashboard
#                       (operator name, theme) — written when the
#                       dashboard starts the backup; a scheduled
#                       backup leaves the repo's last copy in place
#   chips/              installed.json + the chip .png files
#   rag-packs/          installed.json + each pack folder whole
#                       (documents, built index, metadata — the
#                       installs record carries the active states)
#   chips/workflows.json  her saved workflows
# Never backed up: chat transcripts, call logs, caches and logs, the
# hardware profile, and voice model files (they reinstall).
# Uploads go through the Contents API; downloads for import go
# through git trees/blobs so a large chip restores whole.
# Scheduling is honest: a thread checks on launch and while the
# bridge runs whether a backup is due (last backup + the operator's
# interval of 1/3/5/7 days) and runs it when signed in — backups
# happen while Navi is running, not while the machine is off.

GITHUB_TOKEN_PATH = os.path.join(ROOT, "config", "github-auth.json")
GITHUB_REPO_URL = "https://github.com/AlexKollar/Apex"
GITHUB_API_BASE = "https://api.github.com/repos/AlexKollar/Apex"
GITHUB_BACKUP_ITEMS = ["soul", "memory", "settings", "chips", "rag", "workflows"]
# The always-ticked core (build .36): Soul, Memory, and Settings &
# config ride in every backup automatically — they are what makes
# an imported Navi *her*, so github_settings folds them into the
# stored list on every read and no save can drop them. Chips, RAG
# packs, and workflows stay the operator's choice.
GITHUB_CORE_BACKUP_ITEMS = ["soul", "memory", "settings"]
_github_device = {}


def github_api(method, url, token=None, body=None, form=False):
    # One GitHub request; returns (status, parsed JSON or text) and
    # never raises for an HTTP error — the caller words the failure.
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "navi-apex-bridge",
    }
    data = None
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
            try:
                return resp.status, json.loads(raw)
            except Exception:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, raw
    except Exception as e:
        return 0, str(e)


def github_err_text(resp):
    if isinstance(resp, dict):
        return str(resp.get("message") or resp.get("error_description") or resp.get("error") or resp)[:240]
    return str(resp)[:240]


def github_settings(cfg):
    gh = cfg.get("github") if isinstance(cfg.get("github"), dict) else {}
    if isinstance(gh.get("backup_items"), list):
        items = [i for i in gh["backup_items"] if i in GITHUB_BACKUP_ITEMS]
    else:
        items = list(GITHUB_BACKUP_ITEMS)
    # The core trio is ticked automatically, whatever an older
    # config recorded: Soul, Memory, and Settings & config always
    # ride along, in the canonical order.
    items = [i for i in GITHUB_BACKUP_ITEMS if i in GITHUB_CORE_BACKUP_ITEMS or i in items]
    interval = gh.get("backup_interval_days")
    return {
        "client_id": str(gh.get("client_id") or "").strip(),
        "backup_repo": str(gh.get("backup_repo") or "navi-backup").strip() or "navi-backup",
        "backup_private": gh.get("backup_private") is not False,
        "backup_items": items,
        "backup_interval_days": interval if interval in (1, 3, 5, 7) else 1,
        "last_backup_at": gh.get("last_backup_at"),
        "last_backup_file_count": gh.get("last_backup_file_count"),
        "last_backup_result": str(gh.get("last_backup_result") or ""),
        "last_import_at": gh.get("last_import_at"),
        "last_import_result": str(gh.get("last_import_result") or ""),
    }


def save_github_settings(patch):
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    gh = cfg.get("github") if isinstance(cfg.get("github"), dict) else {}
    gh.update(patch)
    cfg["github"] = gh
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    return github_settings(cfg)


def github_auth():
    try:
        with open(GITHUB_TOKEN_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict) and data.get("token"):
            return {"token": str(data["token"]), "login": str(data.get("login") or "")}
    except Exception:
        pass
    return None


def github_save_auth(token, login):
    os.makedirs(os.path.dirname(GITHUB_TOKEN_PATH), exist_ok=True)
    fd = os.open(GITHUB_TOKEN_PATH, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump({"token": token, "login": login}, f)
    try:
        os.chmod(GITHUB_TOKEN_PATH, 0o600)
    except Exception:
        pass


def github_status_payload(cfg):
    s = github_settings(cfg)
    auth = github_auth()
    return {
        "ok": True,
        "repoUrl": GITHUB_REPO_URL,
        "issuesUrl": GITHUB_REPO_URL + "/issues",
        "clientId": s["client_id"],
        "clientIdConfigured": bool(s["client_id"]),
        "signedIn": auth is not None,
        "login": auth["login"] if auth else "",
        "backupRepo": s["backup_repo"],
        "backupPrivate": s["backup_private"],
        "backupItems": s["backup_items"],
        "intervalDays": s["backup_interval_days"],
        "lastBackupAt": s["last_backup_at"],
        "lastBackupFileCount": s["last_backup_file_count"],
        "lastBackupResult": s["last_backup_result"],
        "lastImportAt": s["last_import_at"],
        "lastImportResult": s["last_import_result"],
    }


def github_issues_payload():
    # The Issues tab inside the GitHub section: the repo's current
    # open issues, live from the public GitHub API. No token — the
    # repo is public and listing never requires sign-in. Pull
    # requests ride the same endpoint and are filtered out.
    st, resp = github_api(
        "GET",
        GITHUB_API_BASE + "/issues?state=open&per_page=100&sort=updated&direction=desc",
        None,
    )
    if st != 200 or not isinstance(resp, list):
        return {
            "ok": False,
            "error": "GitHub issues fetch failed (HTTP " + str(st) + "): " + github_err_text(resp),
            "issues": [],
            "fetchedAt": None,
            "repoUrl": GITHUB_REPO_URL,
            "issuesUrl": GITHUB_REPO_URL + "/issues",
        }
    issues = []
    for i in resp:
        if not isinstance(i, dict) or "pull_request" in i:
            continue
        issues.append({
            "number": i.get("number") or 0,
            "title": str(i.get("title") or ""),
            "url": str(i.get("html_url") or ""),
            "state": str(i.get("state") or "open"),
            "labels": [str(l.get("name")) for l in (i.get("labels") or []) if isinstance(l, dict) and l.get("name")],
            "author": str((i.get("user") or {}).get("login") or ""),
            "updatedAt": str(i.get("updated_at") or ""),
            "createdAt": str(i.get("created_at") or ""),
            "comments": i.get("comments") or 0,
        })
    return {
        "ok": True,
        "error": None,
        "issues": issues,
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repoUrl": GITHUB_REPO_URL,
        "issuesUrl": GITHUB_REPO_URL + "/issues",
    }


def github_pulse_payload():
    # The GitHub section's Overview: the project's pulse — repo
    # description, stars/forks/watchers, latest release, recent
    # commits, open-issue count, last push — live from the public
    # GitHub API, no token. Any failure is reported, never filled
    # in with invented numbers.
    st, repo = github_api("GET", GITHUB_API_BASE, None)
    if st != 200 or not isinstance(repo, dict):
        return {
            "ok": False,
            "error": "GitHub pulse fetch failed (HTTP " + str(st) + "): " + github_err_text(repo),
            "pulse": None,
            "fetchedAt": None,
            "repoUrl": GITHUB_REPO_URL,
        }
    latest_release = None
    rst, rel = github_api("GET", GITHUB_API_BASE + "/releases/latest", None)
    if rst == 200 and isinstance(rel, dict):
        latest_release = {
            "tag": str(rel.get("tag_name") or ""),
            "name": str(rel.get("name") or ""),
            "url": str(rel.get("html_url") or ""),
            "publishedAt": str(rel.get("published_at") or ""),
        }
    commits = []
    commit_count = None
    cst, crows = github_api("GET", GITHUB_API_BASE + "/commits?per_page=100", None)
    if cst == 200 and isinstance(crows, list):
        if len(crows) < 100:
            commit_count = len(crows)
        for c in crows[:5]:
            if not isinstance(c, dict):
                continue
            cm = c.get("commit") or {}
            au = cm.get("author") or {}
            commits.append({
                "sha": str(c.get("sha") or "")[:7],
                "message": str(cm.get("message") or "").split("\n")[0],
                "author": str(au.get("name") or ""),
                "date": str(au.get("date") or ""),
                "url": str(c.get("html_url") or ""),
            })
    issues = []
    ist, irows = github_api("GET", GITHUB_API_BASE + "/issues?state=open&per_page=8", None)
    if ist == 200 and isinstance(irows, list):
        for i in irows:
            if not isinstance(i, dict) or "pull_request" in i:
                continue
            issues.append({
                "number": i.get("number") or 0,
                "title": str(i.get("title") or ""),
                "url": str(i.get("html_url") or ""),
                "state": str(i.get("state") or "open"),
                "labels": [str(l.get("name")) for l in (i.get("labels") or []) if isinstance(l, dict) and l.get("name")],
                "author": str((i.get("user") or {}).get("login") or ""),
                "updatedAt": str(i.get("updated_at") or ""),
            })
            if len(issues) >= 8:
                break
    pulse = {
        "description": str(repo.get("description") or ""),
        "stars": repo.get("stargazers_count") or 0,
        "forks": repo.get("forks_count") or 0,
        "watchers": repo.get("subscribers_count") or repo.get("watchers_count") or 0,
        "language": str(repo.get("language") or "—"),
        "openIssuesCount": repo.get("open_issues_count") or 0,
        "pushedAt": str(repo.get("pushed_at") or ""),
        "defaultBranch": str(repo.get("default_branch") or "main"),
        "commitCount": commit_count,
        "latestRelease": latest_release,
        "commits": commits,
        "issues": issues,
    }
    return {
        "ok": True,
        "error": None,
        "pulse": pulse,
        "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repoUrl": GITHUB_REPO_URL,
    }


def github_device_start(cfg):
    s = github_settings(cfg)
    if not s["client_id"]:
        return {"ok": False, "error": "No GitHub OAuth client id is configured yet — sign-in can't start until one is set (the GitHub page shows the setup steps). Viewing issues needs no sign-in at all."}
    st, resp = github_api(
        "POST", "https://github.com/login/device/code", None,
        {"client_id": s["client_id"], "scope": "repo"}, form=True,
    )
    if st != 200 or not isinstance(resp, dict) or not resp.get("device_code"):
        return {"ok": False, "error": "GitHub did not start a device sign-in (HTTP " + str(st) + "): " + github_err_text(resp)}
    _github_device.clear()
    _github_device.update({
        "device_code": resp["device_code"],
        "interval": resp.get("interval") or 5,
    })
    return {
        "ok": True,
        "userCode": resp.get("user_code") or "",
        "verificationUri": resp.get("verification_uri") or "https://github.com/login/device",
        "expiresIn": resp.get("expires_in"),
        "interval": resp.get("interval") or 5,
    }


def github_device_poll(cfg):
    s = github_settings(cfg)
    device_code = _github_device.get("device_code")
    if not device_code:
        return {"ok": False, "status": "idle", "error": "No sign-in is in progress — start one first."}
    st, resp = github_api(
        "POST", "https://github.com/login/oauth/access_token", None,
        {
            "client_id": s["client_id"],
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        },
        form=True,
    )
    if isinstance(resp, dict) and resp.get("access_token"):
        token = str(resp["access_token"])
        login = ""
        ust, user = github_api("GET", "https://api.github.com/user", token)
        if ust == 200 and isinstance(user, dict):
            login = str(user.get("login") or "")
        github_save_auth(token, login)
        _github_device.clear()
        return {"ok": True, "status": "authorized", "login": login}
    err = resp.get("error") if isinstance(resp, dict) else None
    if err == "authorization_pending":
        return {"ok": True, "status": "pending"}
    if err == "slow_down":
        return {"ok": True, "status": "pending", "slowDown": True}
    _github_device.clear()
    return {"ok": False, "status": "failed", "error": "GitHub sign-in ended (" + str(err or ("HTTP " + str(st))) + ") — start again to retry."}


def github_collect_backup(cfg, dashboard=None):
    # The ready-to-fly essentials as {path: bytes}. Only the ticked
    # essentials are gathered; the manifest always rides along and
    # says exactly what this backup holds.
    s = github_settings(cfg)
    items = s["backup_items"]
    files = {}
    if "soul" in items:
        files["soul.md"] = read_file(SOUL_PATH).encode()
    if "memory" in items:
        files["memory.md"] = read_file(MEMORY_PATH).encode()
    if "settings" in items:
        clean = {
            k: v for k, v in cfg.items()
            if k not in ("github", "bridge", "hardware_profile", "runtime")
        }
        files["settings.json"] = json.dumps(clean, indent=2).encode()
        files["voice.json"] = json.dumps(cfg.get("voice") or {}, indent=2).encode()
        if isinstance(dashboard, dict):
            files["dashboard.json"] = json.dumps({
                "operatorName": str(dashboard.get("operatorName") or ""),
                "theme": str(dashboard.get("theme") or ""),
            }, indent=2).encode()
    if "chips" in items:
        files["chips/installed.json"] = (read_file(CHIP_INSTALLS_PATH) or "[]").encode()
        for row in load_chip_installs():
            local_file = row.get("local_file")
            if local_file:
                path = os.path.join(CHIPS_DIR, os.path.basename(str(local_file)))
                if os.path.isfile(path):
                    with open(path, "rb") as f:
                        files["chips/" + os.path.basename(str(local_file))] = f.read()
    if "rag" in items:
        files["rag-packs/installed.json"] = (read_file(RAG_INSTALLS_PATH) or "[]").encode()
        if os.path.isdir(RAG_PACKS_DIR):
            for slug in sorted(os.listdir(RAG_PACKS_DIR)):
                pdir = os.path.join(RAG_PACKS_DIR, slug)
                if not os.path.isdir(pdir):
                    continue
                for name in sorted(os.listdir(pdir)):
                    fpath = os.path.join(pdir, name)
                    if os.path.isfile(fpath):
                        with open(fpath, "rb") as f:
                            files["rag-packs/" + slug + "/" + name] = f.read()
    if "workflows" in items:
        files["chips/workflows.json"] = (read_file(WORKFLOWS_FILE) or "[]").encode()
    # The manifest's app name is the product name, "Apex" — it is
    # written into navi-backup.json in the operator's backup repo,
    # where it is read as identity, never matched as a token. (The
    # /api/status app value is a different thing: a bridge-recognition
    # token that stays "Navi: Apex" so bridges and launchers from
    # different builds keep recognizing each other; nothing displays
    # it, and restores validate only the format field below, never
    # this name — so backups written by older builds still restore.)
    manifest = {
        "format": "navi-backup/1",
        "app": "Apex",
        "bridgeBuild": BRIDGE_BUILD,
        "backedUpAt": _now_iso(),
        "items": items,
    }
    out = {"navi-backup.json": b""}
    out.update(files)
    # The manifest records the backup's own file count — every file
    # written, the manifest included. The status column's simple
    # "# files | # days ago" readout and Settings → GitHub & Backup
    # both read this one record, so they can never disagree.
    manifest["fileCount"] = len(out)
    out["navi-backup.json"] = json.dumps(manifest, indent=2).encode()
    return out, manifest


def github_run_backup(cfg, dashboard=None):
    auth = github_auth()
    if not auth:
        return {"ok": False, "error": "Not signed in to GitHub — a backup writes to your GitHub account, so it needs the sign-in. Navi herself never does."}
    s = github_settings(cfg)
    if not s["backup_items"]:
        return {"ok": False, "error": "Nothing is ticked in the essentials checklist — an empty backup would restore an empty Navi."}
    login, token, repo = auth["login"], auth["token"], s["backup_repo"]
    base = "https://api.github.com/repos/" + login + "/" + repo
    st, _ = github_api("GET", base, token)
    if st == 404:
        st, created = github_api("POST", "https://api.github.com/user/repos", token, {
            "name": repo,
            "private": s["backup_private"],
            "description": "Apex backup — her ready-to-fly essentials (Soul, Memory, settings, chips, RAG packs, workflows).",
            "auto_init": True,
        })
        if st not in (200, 201):
            return {"ok": False, "error": "GitHub refused to create the backup repo " + login + "/" + repo + " (HTTP " + str(st) + "): " + github_err_text(created)}
    elif st != 200:
        return {"ok": False, "error": "Could not reach the backup repo " + login + "/" + repo + " (HTTP " + str(st) + ")."}
    files, manifest = github_collect_backup(cfg, dashboard)
    for path in sorted(files):
        url = base + "/contents/" + urllib.parse.quote(path, safe="/")
        sha = None
        gst, existing = github_api("GET", url, token)
        if gst == 200 and isinstance(existing, dict):
            sha = existing.get("sha")
        body = {
            "message": "Navi backup " + manifest["backedUpAt"],
            "content": base64.b64encode(files[path]).decode(),
        }
        if sha:
            body["sha"] = sha
        pst, resp = github_api("PUT", url, token, body)
        if pst not in (200, 201):
            return {"ok": False, "error": "GitHub refused " + path + " (HTTP " + str(pst) + "): " + github_err_text(resp)}
    result = (
        str(len(manifest["items"])) + " essentials written to " + login + "/" + repo
        + (" (private)" if s["backup_private"] else " (PUBLIC)")
    )
    save_github_settings({"last_backup_at": manifest["backedUpAt"], "last_backup_file_count": manifest.get("fileCount"), "last_backup_result": result})
    return {"ok": True, "result": result, "files": sorted(files), "backedUpAt": manifest["backedUpAt"]}


def github_fetch_backup(cfg):
    # Pulls the backup repo's files down for an import: returns
    # ({"files": {path: bytes}, "manifest": {...}}, None) or
    # (None, error). Downloads go through git trees/blobs so files
    # over the Contents API's size limit still restore whole.
    auth = github_auth()
    if not auth:
        return None, "Not signed in to GitHub — import reads your backup repo, so it needs the sign-in."
    s = github_settings(cfg)
    login, token, repo = auth["login"], auth["token"], s["backup_repo"]
    base = "https://api.github.com/repos/" + login + "/" + repo
    st, repo_j = github_api("GET", base, token)
    if st == 404:
        return None, "No backup repo yet — " + login + "/" + repo + " doesn't exist. Run a backup first."
    if st != 200 or not isinstance(repo_j, dict):
        return None, "Could not read " + login + "/" + repo + " (HTTP " + str(st) + ")."
    branch = str(repo_j.get("default_branch") or "main")
    st, tree = github_api("GET", base + "/git/trees/" + urllib.parse.quote(branch, safe="") + "?recursive=1", token)
    if st != 200 or not isinstance(tree, dict):
        return None, "Could not list the backup's files (HTTP " + str(st) + ")."
    blobs = {}
    for entry in tree.get("tree") or []:
        if entry.get("type") == "blob" and entry.get("path"):
            blobs[str(entry["path"])] = entry.get("sha")
    if "navi-backup.json" not in blobs:
        return None, login + "/" + repo + " doesn't hold a Navi backup (no navi-backup.json manifest)."
    fixed = {
        "navi-backup.json", "soul.md", "memory.md", "settings.json", "voice.json",
        "dashboard.json", "chips/installed.json", "chips/workflows.json",
        "rag-packs/installed.json",
    }
    files = {}
    for path, sha in blobs.items():
        if path in fixed or path.startswith("rag-packs/") or (path.startswith("chips/") and path.endswith(".png")):
            bst, blob = github_api("GET", base + "/git/blobs/" + str(sha), token)
            if bst == 200 and isinstance(blob, dict) and blob.get("content"):
                try:
                    files[path] = base64.b64decode(str(blob["content"]))
                except Exception:
                    pass
    try:
        manifest = json.loads(files["navi-backup.json"].decode("utf-8", "replace"))
    except Exception:
        return None, "The backup's manifest could not be read."
    if not isinstance(manifest, dict) or manifest.get("format") != "navi-backup/1":
        return None, "That repo's manifest isn't a navi-backup/1 backup."
    return {"files": files, "manifest": manifest}, None


def github_import_changes(cfg, fetched, dashboard=None):
    files, manifest = fetched["files"], fetched["manifest"]
    items = [i for i in (manifest.get("items") or []) if i in GITHUB_BACKUP_ITEMS]
    labels = {
        "soul": "Soul document",
        "memory": "Memory document",
        "settings": "Settings & config",
        "chips": "Installed chips",
        "rag": "RAG packs",
        "workflows": "Workflows",
    }
    changes = []
    if "soul" in items:
        cur = read_file(SOUL_PATH)
        new = files.get("soul.md", b"").decode("utf-8", "replace")
        changes.append({
            "item": "soul", "label": labels["soul"],
            "detail": "Already matches the backup — nothing to change." if cur == new else "Would replace the current Soul (" + str(len(cur)) + " characters) with the backup's (" + str(len(new)) + " characters).",
            "willChange": cur != new,
        })
    if "memory" in items:
        cur = read_file(MEMORY_PATH)
        new = files.get("memory.md", b"").decode("utf-8", "replace")
        changes.append({
            "item": "memory", "label": labels["memory"],
            "detail": "Already matches the backup — nothing to change." if cur == new else "Would replace the current Memory (" + str(len(cur)) + " characters) with the backup's (" + str(len(new)) + " characters).",
            "willChange": cur != new,
        })
    if "settings" in items:
        diffs = []
        imported = {}
        try:
            imported = json.loads(files.get("settings.json", b"{}").decode("utf-8", "replace"))
        except Exception:
            imported = {}
        if isinstance(imported, dict):
            if "operator_name" in imported and str(imported.get("operator_name") or "") != str(cfg.get("operator_name") or ""):
                diffs.append("operator name in config")
            if "threat_level" in imported and imported.get("threat_level") != cfg.get("threat_level"):
                diffs.append("threat level")
            if "installed_commands" in imported and imported.get("installed_commands") != cfg.get("installed_commands"):
                diffs.append("installed commands")
        if "voice.json" in files:
            try:
                backed_voice = json.loads(files["voice.json"].decode("utf-8", "replace"))
            except Exception:
                backed_voice = None
            if isinstance(backed_voice, dict) and backed_voice != (cfg.get("voice") or {}):
                diffs.append("voice choice & settings")
        dash = {}
        try:
            dash = json.loads(files.get("dashboard.json", b"{}").decode("utf-8", "replace"))
        except Exception:
            dash = {}
        if isinstance(dash, dict) and dash and isinstance(dashboard, dict):
            if str(dash.get("operatorName") or "") != str(dashboard.get("operatorName") or ""):
                diffs.append("operator name → " + (str(dash.get("operatorName") or "") or "Operator"))
            if str(dash.get("theme") or "") != str(dashboard.get("theme") or ""):
                diffs.append("theme → " + str(dash.get("theme") or ""))
        changes.append({
            "item": "settings", "label": labels["settings"],
            "detail": ("Would restore: " + " · ".join(diffs) + ".") if diffs else "Already matches the backup — nothing to change.",
            "willChange": bool(diffs),
        })
    if "chips" in items:
        backed = []
        try:
            backed = json.loads(files.get("chips/installed.json", b"[]").decode("utf-8", "replace"))
        except Exception:
            backed = []
        cur = load_chip_installs()
        backed_names = sorted(str(r.get("full_name") or "") for r in backed if isinstance(r, dict)) if isinstance(backed, list) else []
        cur_names = sorted(str(r.get("full_name") or "") for r in cur if isinstance(r, dict))
        changes.append({
            "item": "chips", "label": labels["chips"],
            "detail": "Would restore " + str(len(backed) if isinstance(backed, list) else 0) + " installed chips from the backup, chips included — ready to run. This machine currently records " + str(len(cur)) + ".",
            "willChange": backed_names != cur_names,
        })
    if "rag" in items:
        backed = []
        try:
            backed = json.loads(files.get("rag-packs/installed.json", b"[]").decode("utf-8", "replace"))
        except Exception:
            backed = []
        cur = load_rag_installs()
        active = 0
        if isinstance(backed, list):
            active = sum(1 for r in backed if isinstance(r, dict) and r.get("active", True))
        backed_sig = sorted((str(r.get("full_name") or ""), bool(r.get("active", True))) for r in backed if isinstance(r, dict)) if isinstance(backed, list) else []
        cur_sig = sorted((str(r.get("full_name") or ""), bool(r.get("active", True))) for r in cur if isinstance(r, dict))
        changes.append({
            "item": "rag", "label": labels["rag"],
            "detail": "Would restore " + str(len(backed) if isinstance(backed, list) else 0) + " packs from the backup — documents, built indexes, and active states (" + str(active) + " active). This machine currently records " + str(len(cur)) + ".",
            "willChange": backed_sig != cur_sig,
        })
    if "workflows" in items:
        backed = []
        try:
            backed = json.loads(files.get("chips/workflows.json", b"[]").decode("utf-8", "replace"))
        except Exception:
            backed = []
        cur = load_workflows()
        backed_names = sorted(str(w.get("name") or "") for w in backed if isinstance(w, dict)) if isinstance(backed, list) else []
        cur_names = sorted(str(w.get("name") or "") for w in cur if isinstance(w, dict))
        changes.append({
            "item": "workflows", "label": labels["workflows"],
            "detail": "Would restore " + str(len(backed) if isinstance(backed, list) else 0) + " workflows from the backup. This machine currently holds " + str(len(cur)) + ".",
            "willChange": backed_names != cur_names,
        })
    return changes, items


def _github_safe_part(part):
    return bool(re.match(r"^[A-Za-z0-9._-]+$", part)) and part not in (".", "..")


def github_apply_import(cfg, fetched):
    files, manifest = fetched["files"], fetched["manifest"]
    items = [i for i in (manifest.get("items") or []) if i in GITHUB_BACKUP_ITEMS]
    applied = []
    if "soul" in items and "soul.md" in files:
        os.makedirs(os.path.dirname(SOUL_PATH), exist_ok=True)
        with open(SOUL_PATH, "wb") as f:
            f.write(files["soul.md"])
        applied.append("Soul document")
    if "memory" in items and "memory.md" in files:
        os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)
        with open(MEMORY_PATH, "wb") as f:
            f.write(files["memory.md"])
        applied.append("Memory document")
    if "settings" in items and "settings.json" in files:
        try:
            imported = json.loads(files["settings.json"].decode("utf-8", "replace"))
        except Exception:
            imported = None
        if isinstance(imported, dict):
            new_cfg = load_config()
            # Only the operator's own settings cross over — never the
            # github section, the bridge block, the install dir, or
            # (above all) the hardware profile / runtime flags: this
            # machine keeps the profile its own install detected.
            for key in ("operator_name", "threat_level", "sudo_mode", "installed_commands"):
                if key in imported:
                    new_cfg[key] = imported[key]
            if "voice.json" in files:
                try:
                    voice = json.loads(files["voice.json"].decode("utf-8", "replace"))
                    if isinstance(voice, dict) and voice:
                        new_cfg["voice"] = voice
                except Exception:
                    pass
            with open(CONFIG_PATH, "w") as f:
                json.dump(new_cfg, f, indent=2)
            applied.append("Settings & config")
    if "chips" in items:
        wrote = False
        for path, data in files.items():
            if path == "chips/installed.json":
                os.makedirs(CHIPS_DIR, exist_ok=True)
                with open(CHIP_INSTALLS_PATH, "wb") as f:
                    f.write(data)
                wrote = True
            elif path.startswith("chips/") and path.endswith(".png") and _github_safe_part(os.path.basename(path)):
                os.makedirs(CHIPS_DIR, exist_ok=True)
                with open(os.path.join(CHIPS_DIR, os.path.basename(path)), "wb") as f:
                    f.write(data)
                wrote = True
        if wrote:
            applied.append("Installed chips")
    if "rag" in items:
        wrote = False
        for path, data in files.items():
            if path == "rag-packs/installed.json":
                os.makedirs(RAG_PACKS_DIR, exist_ok=True)
                with open(RAG_INSTALLS_PATH, "wb") as f:
                    f.write(data)
                wrote = True
            elif path.startswith("rag-packs/"):
                parts = path.split("/")
                if len(parts) == 3 and _github_safe_part(parts[1]) and _github_safe_part(parts[2]):
                    pdir = os.path.join(RAG_PACKS_DIR, parts[1])
                    os.makedirs(pdir, exist_ok=True)
                    with open(os.path.join(pdir, parts[2]), "wb") as f:
                        f.write(data)
                    wrote = True
        if wrote:
            applied.append("RAG packs")
    if "workflows" in items and "chips/workflows.json" in files:
        os.makedirs(CHIPS_DIR, exist_ok=True)
        with open(WORKFLOWS_FILE, "wb") as f:
            f.write(files["chips/workflows.json"])
        applied.append("Workflows")
    dashboard_out = None
    if "dashboard.json" in files:
        try:
            parsed = json.loads(files["dashboard.json"].decode("utf-8", "replace"))
            if isinstance(parsed, dict):
                dashboard_out = {
                    "operatorName": str(parsed.get("operatorName") or ""),
                    "theme": str(parsed.get("theme") or ""),
                }
        except Exception:
            dashboard_out = None
    taken = str(manifest.get("backedUpAt") or "")
    result = (
        "Imported the backup from " + (taken[:10] if taken else "an unknown date")
        + " — restored: " + (", ".join(applied) if applied else "nothing (the backup held no restorable sections)") + "."
    )
    save_github_settings({"last_import_at": _now_iso(), "last_import_result": result})
    return {"ok": True, "result": result, "applied": applied, "dashboard": dashboard_out}


def github_backup_due(cfg):
    s = github_settings(cfg)
    if not github_auth() or not s["backup_items"]:
        return False
    last = s["last_backup_at"]
    if not last:
        return True
    try:
        epoch = calendar.timegm(time.strptime(str(last)[:19], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return True
    return (time.time() - epoch) >= s["backup_interval_days"] * 86400


def github_auto_backup_loop():
    # Interval backups, honestly scoped: the check runs shortly
    # after the bridge starts and again while it runs. A backup that
    # comes due while the machine is off runs at the next launch —
    # nothing here pretends otherwise.
    time.sleep(25)
    while True:
        try:
            cfg = load_config()
            if github_backup_due(cfg):
                github_run_backup(cfg)
        except Exception:
            pass
        time.sleep(1800)


def load_chip_installs():
    try:
        with open(CHIP_INSTALLS_PATH) as f:
            rows = json.load(f)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def save_chip_installs(rows):
    os.makedirs(CHIPS_DIR, exist_ok=True)
    with open(CHIP_INSTALLS_PATH, "w") as f:
        json.dump(rows, f, indent=2)


def fetch_repo_chip(full_name):
    # One catalog entry for a repo: its GitHub metadata plus its
    # latest release (None when the repo has never cut one).
    repo = github_json("https://api.github.com/repos/" + full_name)
    latest = None
    try:
        rel = github_json(
            "https://api.github.com/repos/" + full_name + "/releases/latest"
        )
        latest = {
            "tag": rel.get("tag_name") or "",
            "name": rel.get("name") or "",
            "url": rel.get("html_url") or "",
            "publishedAt": rel.get("published_at") or "",
        }
    except urllib.error.HTTPError as e:
        # 404 is the only answer that means "no releases yet" — a
        # rate limit or an outage must surface as a failed catalog,
        # never as a chip that looks release-less.
        if e.code != 404:
            raise
        latest = None
    return {
        "fullName": repo.get("full_name") or full_name,
        "name": repo.get("name") or "",
        "owner": (repo.get("owner") or {}).get("login") or "",
        "description": repo.get("description") or "",
        "htmlUrl": repo.get("html_url") or "",
        "stars": repo.get("stargazers_count") or 0,
        "forks": repo.get("forks_count") or 0,
        "language": repo.get("language") or "—",
        "topics": repo.get("topics") or [],
        "updatedAt": repo.get("updated_at") or "",
        "pushedAt": repo.get("pushed_at") or "",
        "defaultBranch": repo.get("default_branch") or "main",
        "openIssues": repo.get("open_issues_count") or 0,
        "hasWiki": bool(repo.get("has_wiki")),
        "latestRelease": latest,
    }


def chip_install_record(repo):
    latest = repo["latestRelease"]
    return {
        "full_name": repo["fullName"],
        "name": repo["name"],
        "html_url": repo["htmlUrl"],
        "installed_tag": latest["tag"] if latest else None,
        "installed_ref": ("release " + latest["tag"]) if latest
        else (repo["defaultBranch"] + " (no releases yet)"),
        "installed_pushed_at": repo["pushedAt"] or None,
        "installed_at": _now_iso(),
    }


def chip_slug(name):
    return re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-") or "chip"


def chip_cartridge_filename(repo, rows):
    # The chip a GitHub install writes into chips/, named for
    # the repo like a Studio chip is named for its chip. When
    # another install already owns that filename (a forged chip of
    # the same name), the owner's name joins the slug instead of
    # overwriting their chip.
    filename = chip_slug(repo["name"]) + ".png"
    taken = {
        r.get("local_file") for r in rows
        if r.get("full_name") != repo["fullName"]
    }
    if filename in taken:
        filename = chip_slug(repo["owner"] + "-" + repo["name"]) + ".png"
    return filename


def github_download(url):
    req = urllib.request.Request(url, headers=GITHUB_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def fetch_chip_payload(repo):
    # Downloads the chip itself from its repo and returns
    # (payload, source_file_name). A navi-chips repo carries its
    # chip as a Python file in the repo root — the published chips
    # all do (cryptex.py in navi-cryptex, nmap.py in navi-nmap) —
    # so the source comes from the installed ref (the latest
    # release's tag when the repo cuts releases, otherwise the
    # default branch) and is forged into a chip payload
    # exactly as Chip Studio forges a local chip: from that moment
    # the installed chip IS a chip in chips/, indistinguishable
    # from a forged one — pill row, /chip, workflows, execution.
    # Raises ValueError with the reason when the repo holds nothing
    # runnable, so an install never records a chip that is not
    # actually on this machine.
    full = repo["fullName"]
    latest = repo["latestRelease"]
    ref = latest["tag"] if latest else (repo["defaultBranch"] or "main")
    listing = github_json(
        "https://api.github.com/repos/" + full
        + "/contents?ref=" + urllib.parse.quote(ref, safe="")
    )
    if not isinstance(listing, list):
        raise ValueError("GitHub did not return the repo's file list.")
    pys = [
        i for i in listing
        if i.get("type") == "file"
        and str(i.get("name") or "").lower().endswith(".py")
    ]
    if not pys:
        raise ValueError(
            "the repo has no Python chip file in its root at " + ref
            + " — a navi-chips repo carries its chip as a .py file there."
        )
    # A navi-chip.json manifest at the repo root (written by the
    # GitHub-ready export) names the entry file outright and
    # carries the chip's description and declared output.
    manifest = {}
    man_item = next(
        (i for i in listing
         if i.get("type") == "file"
         and str(i.get("name") or "") == "navi-chip.json"),
        None,
    )
    if man_item is not None:
        try:
            parsed = json.loads(
                github_download(man_item["download_url"]).decode("utf-8", "replace")
            )
            if isinstance(parsed, dict):
                manifest = parsed
        except Exception:
            manifest = {}
    base = repo["name"].lower()
    stem = base[5:] if base.startswith("navi-") else base
    wants = []
    if manifest.get("entry"):
        wants.append(str(manifest["entry"]).lower())
    wants += ["root.py", stem + ".py", base + ".py", "chip.py", "main.py"]
    pick = None
    for want in wants:
        pick = next(
            (i for i in pys if str(i.get("name") or "").lower() == want),
            None,
        )
        if pick:
            break
    if pick is None and len(pys) == 1:
        pick = pys[0]
    if pick is None:
        names = ", ".join(str(i.get("name")) for i in pys)
        raise ValueError(
            "the repo root holds several Python files (" + names
            + ") and none is the chip's entry — name the entry file "
            "root.py, or add a navi-chip.json manifest naming it."
        )
    # Every Python file at the root comes down: the entry becomes
    # the chip's code and the rest ride along as its importable
    # modules, so a multi-file chip runs exactly as authored.
    files = []
    code = ""
    for item in pys:
        text = github_download(item["download_url"]).decode("utf-8", "replace")
        if item is pick:
            code = text
        else:
            files.append({"path": str(item.get("name")), "content": text[:200000]})
    if not code.strip():
        raise ValueError(str(pick.get("name")) + " is empty.")
    payload = {
        "name": repo["name"],
        "description": str(manifest.get("description") or repo["description"] or ""),
        "code": code[:200000],
        "output": str(manifest.get("output") or ""),
        "files": _valid_chip_files(
            [{"path": "root.py", "content": code[:200000]}] + files,
            code[:200000],
        ),
    }
    return payload, str(pick.get("name"))


def _display_ref(ref):
    # Install records written before the chip terminology sweep can
    # carry a "cartridge …" ref (e.g. "cartridge testchip.png"); the
    # card badge reads the ref verbatim, so it is normalized to
    # "chip …" on the way out. The stored record is the operator's
    # and is never rewritten here.
    if ref and ref.startswith("cartridge "):
        return "chip " + ref[len("cartridge "):]
    return ref


def chip_catalog_view():
    # A failed search yields an error and just the local installs; a
    # search that succeeds but rate-limits some repos yields those
    # repos plus a warning — a chip is never silently dropped.
    error = None
    warning = None
    repos = []
    try:
        data = github_json(
            "https://api.github.com/search/repositories"
            "?q=topic:navi-chips&per_page=30&sort=updated"
        )
        failures = 0
        for item in data.get("items") or []:
            full = item.get("full_name")
            if not full:
                continue
            try:
                repos.append(fetch_repo_chip(full))
            except Exception:
                failures += 1
        if failures:
            warning = (
                "GitHub could not be fully read for "
                + str(failures)
                + " of the chips (rate limit or outage) — the list "
                "may be incomplete. Search again in a minute."
            )
    except Exception as e:
        error = "GitHub search failed: " + str(e)
    installs = {row.get("full_name"): row for row in load_chip_installs()}
    chips = []
    for repo in repos:
        inst = installs.get(repo["fullName"])
        update = False
        if inst:
            if repo["latestRelease"]:
                update = inst.get("installed_tag") != repo["latestRelease"]["tag"]
            else:
                update = bool(
                    inst.get("installed_pushed_at")
                    and repo["pushedAt"] > inst["installed_pushed_at"]
                )
        entry = dict(repo)
        entry["inCatalog"] = True
        entry["installed"] = bool(inst)
        entry["installedTag"] = inst.get("installed_tag") if inst else None
        entry["installedRef"] = _display_ref(inst.get("installed_ref")) if inst else None
        entry["installedAt"] = inst.get("installed_at") if inst else None
        entry["updateAvailable"] = update
        entry["localFile"] = inst.get("local_file") if inst else None
        entry["locallyEdited"] = bool(inst.get("locally_edited")) if inst else False
        chips.append(entry)
    seen = {c["fullName"] for c in chips}
    for full, inst in installs.items():
        if full in seen:
            continue
        chips.append({
            "fullName": full,
            "name": inst.get("name") or full.split("/")[-1],
            "owner": full.split("/")[0],
            "description": "",
            "htmlUrl": inst.get("html_url") or "",
            "stars": 0, "forks": 0, "language": "—", "topics": [],
            "updatedAt": "",
            "pushedAt": inst.get("installed_pushed_at") or "",
            "defaultBranch": "main", "openIssues": 0,
            "latestRelease": None,
            "inCatalog": False, "installed": True,
            "installedTag": inst.get("installed_tag"),
            "installedRef": _display_ref(inst.get("installed_ref")),
            "installedAt": inst.get("installed_at"),
            "updateAvailable": False,
            "localFile": inst.get("local_file"),
            "locallyEdited": bool(inst.get("locally_edited")),
        })
    view = {"fetchedAt": _now_iso(), "chips": chips}
    if error:
        view["error"] = error
    if warning:
        view["warning"] = warning
    return view


def _png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)
    return out


def build_cartridge_png(payload):
    # The PICO-8 trick in Battle Network dress: the visible image is
    # a battle-chip label; the chip's whole codebase rides inside the
    # PNG in a tEXt chunk (keyword "navi-chip", JSON payload).
    W, H = 96, 112
    palette = [
        (34, 211, 238), (245, 181, 68), (52, 211, 153),
        (248, 113, 113), (167, 139, 250),
    ]
    h = 0
    seed = 7
    for ch in payload["name"]:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
        seed = (seed * 31 + ord(ch)) & 0xFFFFFFFF
    accent = palette[h % len(palette)]
    blocks = []
    for _ in range(64):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        blocks.append(seed / 0x7FFFFFFF > 0.55)
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        for x in range(W):
            r, g, b = 10, 14, 18
            if (8 <= y < 18) or (88 <= y < 100):
                r, g, b = accent
            elif 10 <= x < W - 10 and 26 <= y < 78:
                bx = int((x - 10) / 9.5)
                by = int((y - 26) / 6.5)
                if blocks[(by * 8 + bx) % 64]:
                    r, g, b = accent
                else:
                    r, g, b = 16, 22, 29
            elif x < 4 or x >= W - 4 or y < 4 or y >= H - 4:
                r, g, b = 34, 48, 61
            raw += bytes([r, g, b])
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    text = b"navi-chip\x00" + json.dumps(payload).encode()
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", ihdr)
        + _png_chunk(b"tEXt", text)
        + _png_chunk(b"IDAT", zlib.compress(bytes(raw)))
        + _png_chunk(b"IEND", b"")
    )


def _valid_chip_files(raw, code):
    # A chip's file set as [{path, content}]: root.py first, holding
    # the entry code; then each safe module file (relative .py path,
    # no "..", no leading slash). Unsafe paths and duplicates are
    # dropped. A chip with no file set reads as a lone root.py.
    files = [{"path": "root.py", "content": code}]
    seen = {"root.py"}
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            path = str(item.get("path") or "")
            parts = path.split("/")
            if (not path or path.startswith("/") or ".." in parts
                    or not path.endswith(".py") or path in seen):
                continue
            seen.add(path)
            files.append({"path": path, "content": str(item.get("content") or "")})
    return files


def parse_cartridge_png(data):
    # Reads the "navi-chip" tEXt payload back out of a chip PNG —
    # the inverse of build_cartridge_png.
    if len(data) < 8 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    pos = 8
    while pos + 12 <= len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]
        if len(chunk_data) < length:
            return None
        if kind == b"tEXt":
            nul = chunk_data.find(b"\x00")
            if nul > 0 and chunk_data[:nul] == b"navi-chip":
                try:
                    payload = json.loads(chunk_data[nul + 1:].decode("utf-8", "replace"))
                except Exception:
                    return None
                if isinstance(payload, dict) and payload.get("name"):
                    code = str(payload.get("code") or "")
                    return {
                        "name": str(payload.get("name") or ""),
                        "description": str(payload.get("description") or ""),
                        "code": code,
                        "output": str(payload.get("output") or ""),
                        "files": _valid_chip_files(payload.get("files"), code),
                    }
                return None
        if kind == b"IEND":
            break
        pos += 8 + length + 4
    return None


def local_chips():
    # Every chip in chips/ is a chip loaded on this machine.
    # The install registry supplies each chip's origin: a
    # GitHub full name, a local/ record for Studio-forged chips, or
    # no record at all for a chip dropped in by hand — and
    # whether a Studio save has edited an installed chip locally.
    by_file = {}
    for r in load_chip_installs():
        if r.get("local_file"):
            by_file[r["local_file"]] = r
    chips = []
    try:
        files = sorted(os.listdir(CHIPS_DIR))
    except Exception:
        files = []
    for fn in files:
        if not fn.lower().endswith(".png"):
            continue
        try:
            with open(os.path.join(CHIPS_DIR, fn), "rb") as f:
                payload = parse_cartridge_png(f.read())
        except Exception:
            payload = None
        if payload:
            payload["file"] = fn
            payload["slug"] = fn[:-4]
            rec = by_file.get(fn)
            full = (rec or {}).get("full_name") or ""
            payload["source"] = "github" if full and not full.startswith("local/") else "local"
            payload["sourceKey"] = full if payload["source"] == "github" else None
            payload["locallyEdited"] = bool((rec or {}).get("locally_edited"))
            chips.append(payload)
    return chips


def match_local_chip(query, chips):
    # Matches a chat query against chip file slugs and names; anything
    # after the match is the chip's argument string.
    q = (query or "").strip().lower()
    if not q:
        return None, ""
    for chip in chips:
        keys = {
            chip["slug"].lower(),
            chip["name"].lower(),
            re.sub(r"[^a-z0-9]+", "-", chip["name"].lower()).strip("-"),
        }
        for key in keys:
            if q == key:
                return chip, ""
            if q.startswith(key + " "):
                return chip, (query or "").strip()[len(key):].strip()
    return None, ""


_CHIP_SLASH = re.compile(r"^/chip\s+(.+)$", re.I)
_CHIP_RUN = re.compile(r"^run\s+(?:the\s+)?(.+?)(?:\s+chip)?$", re.I)


def chip_invocation(text):
    # The chip query a chat message carries, if it carries one:
    # "/chip <name>", "run the <name> chip", or the name on its own.
    t = (text or "").strip()
    m = _CHIP_SLASH.match(t)
    if m:
        return m.group(1)
    m = _CHIP_RUN.match(t)
    if m:
        return m.group(1)
    return t


# The navi_internal a chip sees when the bridge runs it: the methods
# the real NaviApp offers chip code, backed by the bridge. print()
# output and print_message both land in the chip's captured output;
# llm_chat proxies to the llamafile with the same (text, status)
# return shape the real chips unpack.
NAVI_INTERNAL_STUB = '''
import os, json, urllib.request

class _NaviInstance:
    def print_message(self, text, include_ai_name=True):
        print(text)
    def llm_chat(self, user_message, called_from_app=False):
        endpoint = os.environ.get("NAVI_LLAMAFILE_ENDPOINT", "http://localhost:8080/v1")
        model = os.environ.get("NAVI_MODEL", "navi")
        body = json.dumps({"model": model, "messages": [{"role": "user", "content": user_message}], "stream": False, "max_tokens": 512}).encode()
        req = urllib.request.Request(endpoint + "/chat/completions", data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode())
            return data["choices"][0]["message"]["content"], 200
        except Exception as e:
            return ("(llm_chat could not reach the model server: " + str(e) + ")", 0)
    def process_message(self, user_message):
        print("(process_message is not available during a bridge chip run)")
    def get_user(self):
        return os.environ.get("USER") or os.environ.get("USERNAME") or "operator"
    def set_user(self, sys_user):
        pass
    def clear_terminal(self):
        pass
    def chat_with_navi(self):
        print("(chat_with_navi is not available during a bridge chip run)")
    def setup_history(self):
        pass
    def setup_navi_vocab(self):
        pass

navi_instance = _NaviInstance()
NaviApp = _NaviInstance
'''


def execute_chip(chip, args_text, cfg):
    # Runs a chip the way Navi does: its run(arguments) with a working
    # navi_internal, in a subprocess with a 20-second budget. A
    # chip whose code defines no run() is declarative — the
    # output it declares is its result. When real execution fails,
    # the declared output is shown with the reason, never swallowed.
    code = chip.get("code") or ""
    declared = chip.get("output") or ""
    label = "chip " + chip["slug"]
    if "def run" not in code:
        if declared:
            return {"command": label, "output": declared, "exit_code": 0}
        return {
            "command": label,
            "output": "(chip \"" + chip["name"] + "\" declares no output and defines no run() to execute.)",
            "exit_code": 0,
        }
    endpoint = cfg.get("live", {}).get("llamafile_endpoint", "http://localhost:8080/v1")
    model = cfg.get("live", {}).get("model_name") or "navi"
    tmp = tempfile.mkdtemp(prefix="navi-chip-")
    try:
        with open(os.path.join(tmp, "navi_internal.py"), "w") as f:
            f.write(NAVI_INTERNAL_STUB)
        # The chip's whole file set lands in the sandbox: the entry
        # code as root.py (and chip_module.py, the name the runner
        # imports) plus every module file at its own path, so
        # root.py's imports resolve exactly as authored. Paths are
        # re-validated here — a chip can come from anywhere.
        chip_files = chip.get("files") or []
        for item in chip_files:
            if not isinstance(item, dict):
                continue
            rel = str(item.get("path") or "")
            parts = rel.split("/")
            if (not rel or rel.startswith("/") or ".." in parts
                    or not rel.endswith(".py") or rel == "navi_internal.py"
                    or rel == "root.py"):
                continue
            dest = os.path.join(tmp, rel)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, "w") as f:
                f.write(str(item.get("content") or ""))
        with open(os.path.join(tmp, "root.py"), "w") as f:
            f.write(code)
        with open(os.path.join(tmp, "chip_module.py"), "w") as f:
            f.write(code)
        runner = (
            "import sys, types\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "import chip_module\n"
            "args = types.SimpleNamespace(text=sys.argv[2])\n"
            "chip_module.run(args)\n"
        )
        with open(os.path.join(tmp, "runner.py"), "w") as f:
            f.write(runner)
        env = dict(os.environ)
        env["NAVI_LLAMAFILE_ENDPOINT"] = endpoint
        env["NAVI_MODEL"] = model
        env["PYTHONPATH"] = tmp
        try:
            proc = subprocess.run(
                [sys.executable, os.path.join(tmp, "runner.py"), tmp, args_text or ""],
                capture_output=True, text=True, timeout=20, cwd=shell_cwd(), env=env,
            )
            out = ((proc.stdout or "") + (proc.stderr or "")).strip()
            if proc.returncode == 0:
                return {"command": label, "output": out or "(chip ran — no output)", "exit_code": 0}
            note = "The chip's code exited with code " + str(proc.returncode) + "."
            if declared:
                return {
                    "command": label,
                    "output": declared + "\n\n(" + note + " Showing the output the chip declares instead. Error tail:\n" + out[-400:] + ")",
                    "exit_code": 0,
                }
            return {"command": label, "output": note + "\n" + out[-1200:], "exit_code": proc.returncode}
        except subprocess.TimeoutExpired:
            msg = "The chip ran longer than 20 seconds and was stopped."
            if declared:
                return {
                    "command": label,
                    "output": declared + "\n\n(" + msg + " Showing the output the chip declares instead.)",
                    "exit_code": 0,
                }
            return {"command": label, "output": msg, "exit_code": 1}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------ Workflows --------------------------------
# Saved chains of chips (chips/workflows.json): each chip's
# output becomes the next chip's input — execute_chip receives the
# incoming output as its arguments text, the way a following chip in
# a pipeline would read what came before it.

WORKFLOWS_FILE = os.path.join(CHIPS_DIR, "workflows.json")


def load_workflows():
    try:
        with open(WORKFLOWS_FILE) as f:
            rows = json.load(f)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def save_workflows(rows):
    os.makedirs(CHIPS_DIR, exist_ok=True)
    with open(WORKFLOWS_FILE, "w") as f:
        json.dump(rows, f, indent=1)


def run_workflow_chain(wf, cfg):
    by_file = {c["file"]: c for c in local_chips()}
    steps = []
    incoming = ""
    for fn in wf.get("steps", []):
        chip = by_file.get(fn)
        if chip is None:
            return {
                "ok": False,
                "error": "Step chip \"" + fn + "\" is no longer in the chips folder — the chain stops here.",
                "steps": steps,
                "finalOutput": None,
            }
        result = execute_chip(chip, incoming, cfg)
        steps.append({
            "chipId": fn,
            "name": chip["name"],
            "input": incoming,
            "output": result["output"],
        })
        incoming = result["output"]
    return {"ok": True, "error": None, "steps": steps, "finalOutput": incoming or None}


# --------------------- Knowledge packs (RAG) ---------------------
# Her knowledge, chip-style like her chips. A pack is a GitHub
# repo carrying the "navi-rag" topic; its documents are the repo's
# .md/.txt/.pdf files — a PDF's text is extracted at the door
# (pdf_extract_text below, stdlib only) and only the text is ever
# stored or indexed. Installing downloads the documents into
# rag-packs/<slug>/, builds the pack's index there at install time,
# and records the install in rag-packs/installed.json with an
# active flag — only active packs feed retrieval in /api/chat, and
# when a pack informs an answer, its sources ride the reply's "rag"
# payload field and the dashboard draws them as pills under that
# message — never as words in her reply. RAG Studio forges packs
# from documents on
# this machine into the same folder with local/ records. A pack
# also exports back out as a GitHub-ready repo ZIP (README page,
# navi-rag.json manifest, documents/, and the built index.json as
# the pack's reference copy — installs rebuild the index locally
# from the documents and skip a root README, so the page never
# pollutes retrieval). The index
# is feature-hashed term vectors (RAG_EMBED_DIM buckets, signed,
# L2-normalized): small local embeddings computed with the stdlib
# alone — no model to download, a chunk embeds in well under a
# millisecond, and at query time only the question gets embedded,
# so retrieval stays fluid on CPU. Packs and their indexes sit on
# the installers' persistence keep-list beside chips/ and
# voice/models/, so updates and --fresh installs keep them.

RAG_PACKS_DIR = os.path.join(ROOT, "rag-packs")
RAG_EXPORTS_DIR = os.path.join(ROOT, "rag-exports")
CHIPS_EXPORTS_DIR = os.path.join(ROOT, "chips-exports")
RAG_INSTALLS_PATH = os.path.join(RAG_PACKS_DIR, "installed.json")
RAG_EMBED_DIM = 256
RAG_MIN_SCORE = 0.18
RAG_MAX_DOCS = 40
RAG_MAX_DOC_CHARS = 200000


def load_rag_installs():
    try:
        with open(RAG_INSTALLS_PATH) as f:
            rows = json.load(f)
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def save_rag_installs(rows):
    os.makedirs(RAG_PACKS_DIR, exist_ok=True)
    with open(RAG_INSTALLS_PATH, "w") as f:
        json.dump(rows, f, indent=2)


def _rag_embed(text):
    # A feature-hashed term embedding: each word hashes into one of
    # RAG_EMBED_DIM buckets (a second bit of the hash picks the
    # sign, so unrelated words sharing a bucket tend to cancel
    # rather than reinforce), counts accumulate, and the vector is
    # L2-normalized so a dot product is a cosine.
    vec = [0.0] * RAG_EMBED_DIM
    for tok in re.findall(r"[a-z0-9]+", (text or "").lower()):
        if len(tok) < 3:
            continue
        h = zlib.crc32(tok.encode("utf-8"))
        vec[h % RAG_EMBED_DIM] += 1.0 if (h >> 9) & 1 else -1.0
    norm = math.sqrt(sum(v * v for v in vec))
    if norm:
        vec = [v / norm for v in vec]
    return vec


def _rag_chunks(body):
    # Paragraphs, with long ones split into sentence groups — the
    # same chunking the bench mirror uses, small enough that a
    # retrieved passage reads as one thought.
    text = (body or "").replace("\r\n", "\n")
    chunks = []
    for para in text.split("\n\n"):
        para = " ".join(para.split())
        if not para:
            continue
        if len(para) <= 420:
            chunks.append(para)
            continue
        cur = ""
        for sent in para.split(". "):
            s = sent.strip()
            if not s:
                continue
            if cur and len(cur) + len(s) + 2 > 420:
                chunks.append(cur)
                cur = s
            else:
                cur = (cur + ". " + s) if cur else s
        if cur:
            chunks.append(cur)
    return chunks


def _pdf_parse_cmap(content):
    # A ToUnicode CMap -> {code length: {code: unicode text}},
    # from its beginbfchar / beginbfrange sections.
    maps = {}

    def dst_text(hx):
        try:
            return bytes.fromhex(hx).decode("utf-16-be", "replace")
        except Exception:
            return ""

    for sec in re.finditer(rb"beginbfchar(.*?)endbfchar", content, re.S):
        for m in re.finditer(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", sec.group(1)):
            src = m.group(1).decode("ascii")
            maps.setdefault(len(src) // 2, {})[int(src, 16)] = dst_text(m.group(2).decode("ascii"))
    for sec in re.finditer(rb"beginbfrange(.*?)endbfrange", content, re.S):
        body = sec.group(1)
        for m in re.finditer(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*\[(.*?)\]", body, re.S):
            lo = int(m.group(1), 16)
            bucket = maps.setdefault(len(m.group(1)) // 2, {})
            for k, d in enumerate(re.findall(rb"<([0-9A-Fa-f]+)>", m.group(3))):
                bucket[lo + k] = dst_text(d.decode("ascii"))
        plain = re.sub(rb"<[0-9A-Fa-f]+>\s*<[0-9A-Fa-f]+>\s*\[.*?\]", b"", body, flags=re.S)
        for m in re.finditer(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", plain):
            lo = int(m.group(1), 16)
            hi = int(m.group(2), 16)
            base = int(m.group(3), 16)
            if hi - lo > 4096:
                continue
            bucket = maps.setdefault(len(m.group(1)) // 2, {})
            for code in range(lo, hi + 1):
                v = base + (code - lo)
                bucket[code] = chr(v) if 0 <= v < 0x110000 else ""
    return maps


def _pdf_obj_stream(body):
    # The inflated stream bytes of an indirect object body.
    i = body.find(b"stream")
    if i < 0:
        return None
    start = i + 6
    if body[start:start + 2] == b"\r\n":
        start += 2
    elif body[start:start + 1] in (b"\n", b"\r"):
        start += 1
    else:
        return None
    end = body.find(b"endstream", start)
    if end < 0:
        return None
    raw = body[start:end]
    if raw.endswith(b"\r\n"):
        raw = raw[:-2]
    elif raw.endswith(b"\n") or raw.endswith(b"\r"):
        raw = raw[:-1]
    try:
        return zlib.decompress(raw)
    except Exception:
        return raw


def _pdf_font_maps(data):
    # {resource name (F1, F2, ...): ToUnicode map} for the fonts
    # that carry one, plus the document's only map when there is
    # exactly one (the fallback for a stream whose font name did
    # not resolve). Font dictionaries and resource maps are read
    # from the uncompressed indirect objects; ToUnicode CMaps are
    # streams, so they are never buried in object streams.
    objs = {}
    for m in re.finditer(rb"(\d+)\s+\d+\s+obj\b(.*?)endobj", data, re.S):
        try:
            objs[int(m.group(1))] = m.group(2)
        except Exception:
            pass
    cmaps = {}
    for num, body in objs.items():
        m = re.search(rb"/ToUnicode\s+(\d+)\s+\d+\s+R", body)
        if m:
            stream = _pdf_obj_stream(objs.get(int(m.group(1)), b""))
            if stream:
                cmap = _pdf_parse_cmap(stream)
                if cmap:
                    cmaps[num] = cmap
    by_name = {}
    for body in objs.values():
        for sec in re.finditer(rb"/Font\s*<<(.*?)>>", body, re.S):
            for m in re.finditer(rb"/([A-Za-z0-9]+)\s+(\d+)\s+\d+\s+R", sec.group(1)):
                ref = int(m.group(2))
                if ref in cmaps:
                    by_name[m.group(1).decode("latin-1")] = cmaps[ref]
    only = next(iter(cmaps.values())) if len(cmaps) == 1 else None
    return by_name, only


def _pdf_decode_coded(raw, cmap):
    # Decodes one shown string's raw bytes through a font's
    # ToUnicode map (longest codes first); without a map — or for
    # a code the map does not know in a 1-byte font — the plain
    # byte decoding is the fallback.
    if cmap is None:
        return _pdf_decode_bytes(raw)
    lengths = sorted(cmap.keys(), reverse=True)
    out = []
    i = 0
    n = len(raw)
    while i < n:
        matched = False
        for ln in lengths:
            if i + ln <= n:
                code = int.from_bytes(raw[i:i + ln], "big")
                if code in cmap[ln]:
                    out.append(cmap[ln][code])
                    i += ln
                    matched = True
                    break
        if not matched:
            if lengths and lengths[-1] == 1:
                out.append(_pdf_decode_bytes(raw[i:i + 1]))
            i += 1
    return "".join(out)


def _pdf_decode_bytes(raw):
    # A PDF string's bytes: a FE FF BOM means UTF-16BE; otherwise
    # try UTF-8 and fall back to latin-1, which never loses a byte.
    if raw[:2] == bytes([254, 255]):
        return raw[2:].decode("utf-16-be", "replace")
    try:
        return raw.decode("utf-8")
    except Exception:
        return raw.decode("latin-1", "replace")


def _pdf_literal_bytes(content, i):
    # content[i] is '('. Reads the literal string (escapes, octal
    # codes, balanced nested parens); returns (raw bytes, next
    # index) — decoding waits for the active font's ToUnicode map.
    out = bytearray()
    depth = 1
    i += 1
    n = len(content)
    simple = {110: 10, 114: 13, 116: 9, 98: 8, 102: 12, 40: 40, 41: 41, 92: 92}
    while i < n and depth:
        c = content[i]
        if c == 92:  # backslash escape
            i += 1
            if i >= n:
                break
            e = content[i]
            if e in simple:
                out.append(simple[e])
                i += 1
            elif 48 <= e <= 55:  # up to three octal digits
                j = i
                val = 0
                while j < n and j < i + 3 and 48 <= content[j] <= 55:
                    val = val * 8 + (content[j] - 48)
                    j += 1
                out.append(val & 255)
                i = j
            elif e in (10, 13):  # line continuation
                if e == 13 and i + 1 < n and content[i + 1] == 10:
                    i += 1
                i += 1
            else:
                out.append(e)
                i += 1
        elif c == 40:
            depth += 1
            out.append(c)
            i += 1
        elif c == 41:
            depth -= 1
            if depth:
                out.append(c)
            i += 1
        else:
            out.append(c)
            i += 1
    return bytes(out), i


def _pdf_content_text(content, font_maps, default_cmap):
    # Walks one decompressed content stream: literal and hex
    # strings are operands, held as raw bytes; a text-showing
    # operator (Tj, TJ, ', ") decodes them through the active
    # font's ToUnicode map (Tf selects the font), and position
    # moves (Td, TD, T*) end the current line. TJ kerning numbers
    # below -250 read as the word gaps they are.
    lines = []
    cur = []
    operands = []
    cmap = default_cmap
    i = 0
    n = len(content)
    while i < n:
        c = content[i]
        if c == 40:  # ( literal string
            raw, i = _pdf_literal_bytes(content, i)
            operands.append(("s", raw))
        elif c == 60 and content[i + 1:i + 2] != b"<":  # < hex string
            j = content.find(b">", i)
            if j < 0:
                break
            hx = re.sub(rb"\s", b"", content[i + 1:j])
            if len(hx) % 2:
                hx += b"0"
            try:
                operands.append(("s", bytes.fromhex(hx.decode("ascii"))))
            except Exception:
                pass
            i = j + 1
        elif c == 47:  # /name — the font operand of Tf
            j = i + 1
            while j < n and content[j] not in (32, 9, 13, 10, 12, 0) and content[j] not in b"()<>[]{}/%":
                j += 1
            operands.append(("name", content[i + 1:j].decode("latin-1")))
            i = j
        elif c in (32, 9, 13, 10, 12, 0):
            i += 1
        else:
            j = i
            while j < n and content[j] not in (32, 9, 13, 10, 12, 0) and content[j] not in b"()<>[]{}/%":
                j += 1
            if j == i:
                i += 1
                continue
            word = content[i:j]
            i = j
            if word in (b"Tj", b"'", b'"'):
                for kind, val in operands:
                    if kind == "s":
                        cur.append(_pdf_decode_coded(val, cmap))
                cur.append(" ")
                operands = []
            elif word == b"TJ":
                for kind, val in operands:
                    if kind == "s":
                        cur.append(_pdf_decode_coded(val, cmap))
                    elif kind == "n" and val <= -250:
                        cur.append(" ")
                cur.append(" ")
                operands = []
            elif word in (b"Td", b"TD", b"T*", b"ET"):
                if cur:
                    lines.append("".join(cur))
                    cur = []
                operands = []
            elif word == b"Tf":
                for kind, val in operands:
                    if kind == "name":
                        cmap = font_maps.get(val, default_cmap)
                operands = []
            else:
                try:
                    operands.append(("n", float(word)))
                except Exception:
                    operands = []
    if cur:
        lines.append("".join(cur))
    return lines


def pdf_extract_text(data):
    # The text layer of a PDF, stdlib only: every stream is
    # inflated (FlateDecode; a stream that does not inflate is
    # used raw) and the ones carrying text operators contribute
    # their strings in order, decoded through each font's
    # ToUnicode map when it carries one — the CID-font exports
    # Word and writing tools produce need exactly that, their
    # raw codes being font-internal numbers, not characters.
    # The playbooks this targets (CISA, NIST, vendor PDFs) use
    # standard encodings and extract cleanly; a scanned or
    # image-only PDF has no text layer and extracts to "",
    # which callers report instead of indexing silence.
    if not data or data[:4] != b"%PDF":
        return ""
    font_maps, default_cmap = _pdf_font_maps(data)
    lines = []
    pos = 0
    while True:
        s = data.find(b"stream", pos)
        if s < 0:
            break
        if data[s - 3:s] == b"end":  # the "stream" inside "endstream"
            pos = s + 6
            continue
        start = s + 6
        if data[start:start + 2] == b"\r\n":
            start += 2
        elif data[start:start + 1] in (b"\n", b"\r"):
            start += 1
        else:
            pos = s + 6
            continue
        end = data.find(b"endstream", start)
        if end < 0:
            break
        raw = data[start:end]
        if raw.endswith(b"\r\n"):
            raw = raw[:-2]
        elif raw.endswith(b"\n") or raw.endswith(b"\r"):
            raw = raw[:-1]
        try:
            content = zlib.decompress(raw)
        except Exception:
            content = raw
        pos = end + 9
        if b"Tj" not in content and b"TJ" not in content:
            continue
        lines.extend(_pdf_content_text(content, font_maps, default_cmap))
    text = "\n".join(lines)
    return "".join(ch for ch in text if ch in "\n\t" or ord(ch) >= 32).strip()


def build_rag_index(documents):
    # The index is built once, at install/forge time, and stored
    # with the pack; queries never re-embed the documents.
    docs = []
    total = 0
    for d in documents:
        chunks = [
            {"text": c, "vector": _rag_embed(c)}
            for c in _rag_chunks(d.get("body") or "")
        ]
        total += len(chunks)
        docs.append({"title": d.get("title") or "document", "chunks": chunks})
    return {"documents": docs, "chunkCount": total}


def write_rag_pack(slug, name, description, documents):
    # The pack on disk: its documents as files plus index.json —
    # the built index and the pack metadata — beside them. A
    # rewrite (update, re-forge) replaces the documents wholesale.
    pdir = os.path.join(RAG_PACKS_DIR, slug)
    os.makedirs(pdir, exist_ok=True)
    for fn in os.listdir(pdir):
        if fn.lower().endswith((".md", ".txt", ".pdf")) or fn == "index.json":
            try:
                os.remove(os.path.join(pdir, fn))
            except Exception:
                pass
    used = set()
    for d in documents:
        flat = (d.get("title") or "document").replace("/", "-")
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", flat).strip("-.") or "document"
        if safe.lower().endswith(".pdf"):
            # A PDF document's body is its extracted text, so on
            # disk it lives as a .txt file under its own name —
            # the pack never stores the binary.
            safe = safe[:-4] + ".txt"
        elif not safe.lower().endswith((".md", ".txt")):
            safe += ".md"
        stem, dot, ext = safe.rpartition(".")
        cand = safe
        n = 2
        while cand in used:
            cand = (stem + "-" + str(n) + "." + ext) if dot else (safe + "-" + str(n))
            n += 1
        used.add(cand)
        with open(os.path.join(pdir, cand), "w") as f:
            f.write(d.get("body") or "")
    index = build_rag_index(documents)
    index["name"] = name
    index["description"] = description
    with open(os.path.join(pdir, "index.json"), "w") as f:
        json.dump(index, f)
    return index


def build_rag_repo_files(name, description, documents, version, index_text=""):
    # The GitHub-ready repo layout for a pack — the format the
    # installer already reads, made explicit. documents is
    # [{title, body}] with title a bare file name (the pack folder
    # stores documents flat, PDF text already as .txt). Returns
    # [(arcname, text)] in repo order: README page, manifest,
    # index.json (the pack's built index, shipped as the reference
    # copy — installing Navi rebuilds it locally from the
    # documents, so the shipped copy can never disagree),
    # documents/, .gitignore.
    doc_files = [d["title"] for d in documents]
    manifest = {
        "format": "navi-rag/1",
        "name": name,
        "description": description,
        "version": version,
        "documents": ["documents/" + f for f in doc_files],
        "index": "index.json",
        "generatedBy": "Apex — RAG Studio pack export",
    }
    lines = [
        "# " + name,
        "",
        description or "A knowledge pack for Apex.",
        "",
        "A **knowledge pack** for Apex — Navi's answers can draw on",
        "these documents, and cite the pack and document they came from.",
        "The pack format is `navi-rag/1` (see `navi-rag.json`).",
        "",
        "## Documents",
        "",
    ]
    for f in doc_files:
        lines.append("- `documents/" + f + "`")
    lines += [
        "",
        "## Install it in Navi",
        "",
        "1. Open Navi's **RAG** tab, then **Packs**.",
        "2. **Search GitHub** — every public repo tagged `navi-rag` is listed.",
        "3. **Install** this pack. Navi downloads the documents at the latest",
        "   release and builds the pack's index on your machine from them.",
        "",
        "Only **active** packs feed her answers; toggle the pack off in the",
        "same tab whenever you like.",
        "",
        "## Layout",
        "",
        "- `README.md` — this page. Navi's installer skips a root README, so",
        "  it describes the pack without ever being indexed as a document.",
        "- `navi-rag.json` — the pack manifest (name, version, document list).",
        "- `index.json` — the pack's built index, shipped as a reference copy;",
        "  installing Navi rebuilds it locally from the documents.",
        "- `documents/` — the pack's documents (`.md` / `.txt`).",
        "",
        "## Publishing an update",
        "",
        "Edit the documents, bump `version` in `navi-rag.json`, push, and cut",
        "a new release whose tag is the new version (this export is `"
        + version + "`). A newer release tag is what offers everyone who",
        "installed the pack an update. Keep the `navi-rag` topic on the",
        "repo — that is how Navi finds it.",
        "",
    ]
    gitignore = chr(10).join([
        ".DS_Store",
        "Thumbs.db",
        "",
    ])
    files = [
        ("README.md", chr(10).join(lines)),
        ("navi-rag.json", json.dumps(manifest, indent=2) + chr(10)),
    ]
    if index_text:
        files.append(("index.json", index_text))
    for d in documents:
        files.append(("documents/" + d["title"], d["body"]))
    files.append((".gitignore", gitignore))
    return files


def export_rag_pack(slug, version):
    # Builds the pack's GitHub-ready repo ZIP in rag-exports/ and
    # returns (zip file name, [repo file names]). The documents are
    # the pack folder's own files (PDF-sourced text already lives
    # there as .txt); a root README in the folder was a source
    # repo's page and is not carried into documents/.
    index = _rag_pack_index(slug)
    if index is None:
        raise ValueError("That pack is not in rag-packs/.")
    pdir = os.path.join(RAG_PACKS_DIR, slug)
    documents = []
    for fn in sorted(os.listdir(pdir)):
        if not fn.lower().endswith((".md", ".txt")):
            continue
        if fn.lower() == "readme.md":
            continue
        with open(os.path.join(pdir, fn)) as f:
            documents.append({"title": fn, "body": f.read()})
    if not documents:
        raise ValueError("That pack has no documents to export.")
    try:
        with open(os.path.join(pdir, "index.json")) as f:
            index_text = f.read()
    except Exception:
        index_text = ""
    files = build_rag_repo_files(
        index.get("name") or slug, index.get("description") or "",
        documents, version, index_text,
    )
    os.makedirs(RAG_EXPORTS_DIR, exist_ok=True)
    safe_version = re.sub(r"[^0-9A-Za-z.-]+", "-", version).strip("-.") or "0.1.0"
    zip_name = slug + "-" + safe_version + ".zip"
    with zipfile.ZipFile(os.path.join(RAG_EXPORTS_DIR, zip_name), "w", zipfile.ZIP_DEFLATED) as z:
        for arc, text in files:
            z.writestr(arc, text)
    return zip_name, [arc for arc, _text in files]


def build_chip_repo_files(chip, version):
    # The GitHub-ready repo layout for a chip — the format the
    # installer already reads, made explicit. Returns
    # [(arcname, text-or-bytes)] in repo order: README page,
    # navi-chip.json manifest, the chip's files at the root
    # (root.py is the entry; the rest are its importable modules),
    # the forged chip, .gitignore.
    slug = re.sub(r"[^a-z0-9]+", "-", chip["name"].lower()).strip("-") or "chip"
    chip_files = chip.get("files") or _valid_chip_files(None, chip.get("code") or "")
    manifest = {
        "format": "navi-chip/1",
        "name": chip["name"],
        "description": chip.get("description") or "",
        "version": version,
        "entry": "root.py",
        "files": [f["path"] for f in chip_files],
        "output": chip.get("output") or "",
        "generatedBy": "Apex — Chip Studio chip export",
    }
    lines = [
        "# " + chip["name"],
        "",
        chip.get("description") or "A chip for Apex.",
        "",
        "A **chip** for Apex — a small Python program Navi runs.",
        "The chip format is `navi-chip/1` (see `navi-chip.json`).",
        "",
        "## Files",
        "",
    ]
    for f in chip_files:
        note = " — the entry point Navi runs" if f["path"] == "root.py" else " — a module root.py can import"
        lines.append("- `" + f["path"] + "`" + note)
    lines += [
        "- `" + slug + ".png` — the chip as a forged chip (the whole",
        "  file set rides inside the image).",
        "",
        "## Install it in Navi",
        "",
        "1. Open Navi's **Chips** tab, then **Navi User Repo (NUR)**.",
        "2. **Search NUR** — every public repo tagged `navi-chips` is listed.",
        "3. **Install** this chip. Navi downloads every Python file at the",
        "   repo root at the latest release — `root.py` (or the entry named",
        "   in `navi-chip.json`) is the chip, the other files are its modules —",
        "   and forges them into a chip in the chips folder.",
        "",
        "## Publishing an update",
        "",
        "Edit the code, bump `version` in `navi-chip.json`, push, and cut",
        "a new release whose tag is the new version (this export is `"
        + version + "`). A newer release tag is what offers everyone who",
        "installed the chip an update. Keep the `navi-chips` topic on the",
        "repo — that is how Navi finds it.",
        "",
    ]
    gitignore = chr(10).join([".DS_Store", "Thumbs.db", "__pycache__/", ""])
    files = [
        ("README.md", chr(10).join(lines)),
        ("navi-chip.json", json.dumps(manifest, indent=2) + chr(10)),
    ]
    for f in chip_files:
        files.append((f["path"], f["content"]))
    files.append((slug + ".png", build_cartridge_png(chip)))
    files.append((".gitignore", gitignore))
    return files


def export_chip(fname, version):
    # Builds a local chip's GitHub-ready repo ZIP in
    # chips-exports/ and returns (zip file name, [repo file names]).
    path = os.path.join(CHIPS_DIR, os.path.basename(fname or ""))
    if not fname.endswith(".png") or not os.path.isfile(path):
        raise ValueError("That chip is not in the chips folder.")
    with open(path, "rb") as f:
        chip = parse_cartridge_png(f.read())
    if not chip:
        raise ValueError("That chip could not be read.")
    chip["file"] = os.path.basename(fname)
    files = build_chip_repo_files(chip, version)
    os.makedirs(CHIPS_EXPORTS_DIR, exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", chip["name"].lower()).strip("-") or "chip"
    safe_version = re.sub(r"[^0-9A-Za-z.-]+", "-", version).strip("-.") or "0.1.0"
    zip_name = slug + "-" + safe_version + ".zip"
    with zipfile.ZipFile(os.path.join(CHIPS_EXPORTS_DIR, zip_name), "w", zipfile.ZIP_DEFLATED) as z:
        for arc, data in files:
            z.writestr(arc, data)
    return zip_name, [arc for arc, _data in files]


def _rag_pack_index(slug):
    try:
        with open(os.path.join(RAG_PACKS_DIR, slug, "index.json")) as f:
            index = json.load(f)
        return index if isinstance(index, dict) else None
    except Exception:
        return None


def local_rag_packs():
    # Every folder under rag-packs/ holding a readable index is a
    # pack on this machine; the registry supplies its source and
    # active flag. A folder with no record is a local pack, active
    # by default — the same rule as a chip dropped into chips/.
    by_dir = {}
    for r in load_rag_installs():
        if r.get("local_dir"):
            by_dir[r["local_dir"]] = r
    packs = []
    try:
        entries = sorted(os.listdir(RAG_PACKS_DIR))
    except Exception:
        entries = []
    for entry in entries:
        if not os.path.isdir(os.path.join(RAG_PACKS_DIR, entry)):
            continue
        index = _rag_pack_index(entry)
        if index is None:
            continue
        rec = by_dir.get(entry)
        full = rec.get("full_name") if rec else "local/" + entry
        packs.append({
            "slug": entry,
            "name": index.get("name") or entry,
            "description": index.get("description") or "",
            "fullName": full,
            "source": "github" if rec and not str(full).startswith("local/") else "local",
            "locallyEdited": bool(rec.get("locally_edited")) if rec else False,
            "active": bool(rec.get("active", True)) if rec else True,
            "docCount": len(index.get("documents") or []),
            "chunkCount": index.get("chunkCount") or 0,
            "documents": [d.get("title") for d in (index.get("documents") or [])],
        })
    return packs


def rag_pack_documents(slug):
    # A pack's documents with their bodies, for reopening the pack in
    # RAG Studio: the index holds the titles, and each body is the
    # document file write_rag_pack laid down under the same flattened
    # name (PDF text already lives as .txt under the PDF's stem).
    index = _rag_pack_index(slug)
    if index is None:
        return None
    pdir = os.path.join(RAG_PACKS_DIR, slug)
    used = set()
    documents = []
    for d in index.get("documents") or []:
        title = d.get("title") or "document"
        flat = title.replace("/", "-")
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", flat).strip("-.") or "document"
        if safe.lower().endswith(".pdf"):
            safe = safe[:-4] + ".txt"
        elif not safe.lower().endswith((".md", ".txt")):
            safe += ".md"
        stem, dot, ext = safe.rpartition(".")
        cand = safe
        n = 2
        while cand in used:
            cand = (stem + "-" + str(n) + "." + ext) if dot else (safe + "-" + str(n))
            n += 1
        used.add(cand)
        body = ""
        try:
            with open(os.path.join(pdir, cand)) as f:
                body = f.read()
        except Exception:
            body = ""
        documents.append({"title": title, "body": body})
    return {
        "name": index.get("name") or slug,
        "description": index.get("description") or "",
        "documents": documents,
    }


def rag_retrieve(question, limit=2):
    # Only active packs feed her answers. Only the question is
    # embedded here — every chunk vector was computed when its pack
    # was installed or forged.
    qv = _rag_embed(question)
    if not any(qv):
        return []
    by_dir = {}
    for r in load_rag_installs():
        if r.get("local_dir"):
            by_dir[r["local_dir"]] = r
    hits = []
    try:
        entries = sorted(os.listdir(RAG_PACKS_DIR))
    except Exception:
        entries = []
    for entry in entries:
        rec = by_dir.get(entry)
        if rec is not None and not rec.get("active", True):
            continue
        index = _rag_pack_index(entry)
        if index is None:
            continue
        pack_name = index.get("name") or entry
        for doc in index.get("documents") or []:
            for chunk in doc.get("chunks") or []:
                vec = chunk.get("vector") or []
                score = sum(a * b for a, b in zip(qv, vec))
                if score >= RAG_MIN_SCORE:
                    hits.append({
                        "pack": pack_name,
                        "document": doc.get("title") or "",
                        "text": chunk.get("text") or "",
                        "score": score,
                    })
    hits.sort(key=lambda h: -h["score"])
    return hits[:limit]
def strip_citation_footer(text):
    # A citation footer — a trailing "— from <pack> · <document>"
    # line — is presentation, not prose: sources ride the chat
    # payload's "rag" field and the dashboard draws them as pills
    # under the message. They never live in reply text, so her
    # voice never reads them aloud and they never enter the history
    # that would teach her to imitate them. This strips a trailing
    # footer in that shape wherever one survives: a model's own
    # imitation, or a thread an older build stored.
    lines = str(text or "").rstrip().split("\n")
    while lines and lines[-1].strip().startswith("— from "):
        lines.pop()
        while lines and not lines[-1].strip():
            lines.pop()
    return "\n".join(lines).rstrip()


def fetch_pack_documents(repo):
    # Downloads the pack itself from its repo and returns its
    # documents ([{title, body}] — title is the repo-relative path,
    # which is what an answer cites). A navi-rag repo carries its
    # documents as .md/.txt/.pdf files anywhere in the tree; they
    # are fetched at the installed ref (the latest release's tag
    # when the repo cuts releases, otherwise the default branch),
    # and a PDF's body is its extracted text. Raises ValueError
    # with the reason when the repo holds no documents, so an
    # install never records a pack that is not actually here.
    full = repo["fullName"]
    latest = repo["latestRelease"]
    ref = latest["tag"] if latest else (repo["defaultBranch"] or "main")
    tree = github_json(
        "https://api.github.com/repos/" + full + "/git/trees/"
        + urllib.parse.quote(ref, safe="") + "?recursive=1"
    )
    paths = []
    for item in tree.get("tree") or []:
        if item.get("type") != "blob":
            continue
        path = str(item.get("path") or "")
        low = path.lower()
        # A root README.md is the pack's GitHub page, not a
        # document: it describes the pack and is never indexed.
        # (A README inside a subfolder is an ordinary document.)
        if low == "readme.md":
            continue
        if low.endswith(".md") or low.endswith(".txt") or low.endswith(".pdf"):
            paths.append(path)
    if not paths:
        raise ValueError(
            "the repo has no .md, .txt or .pdf documents at " + ref
            + " — a navi-rag repo carries its documents as Markdown, text, or PDF files"
            + " (a root README.md describes the pack and doesn't count)."
        )
    if len(paths) > RAG_MAX_DOCS:
        raise ValueError(
            "the repo holds " + str(len(paths)) + " documents — a pack caps at "
            + str(RAG_MAX_DOCS) + " so an install stays lean on a small machine."
        )
    documents = []
    for path in sorted(paths):
        url = (
            "https://raw.githubusercontent.com/" + full + "/"
            + urllib.parse.quote(ref, safe="") + "/" + urllib.parse.quote(path)
        )
        raw = github_download(url)
        if path.lower().endswith(".pdf"):
            body = pdf_extract_text(raw)
            if not body:
                raise ValueError(
                    path + " has no extractable text — a scanned or "
                    "image-only PDF can't be indexed."
                )
        else:
            body = raw.decode("utf-8", "replace")
        documents.append({"title": path, "body": body[:RAG_MAX_DOC_CHARS]})
    return documents


def rag_install_record(repo, slug, doc_count):
    record = chip_install_record(repo)
    record["local_dir"] = slug
    record["active"] = True
    record["doc_count"] = doc_count
    return record


def rag_pack_slug(repo, rows):
    # The folder a GitHub install writes into rag-packs/, named for
    # the repo; when another pack already owns that slug, the
    # owner's name joins it instead of overwriting their pack.
    slug = chip_slug(repo["name"])
    taken = {
        r.get("local_dir") for r in rows
        if r.get("full_name") != repo["fullName"]
    }
    if slug in taken:
        slug = chip_slug(repo["owner"] + "-" + repo["name"])
    return slug


def rag_catalog_view():
    # The chips catalog view, for packs: the GitHub topic search
    # merged with the install registry, plus forged local packs.
    error = None
    warning = None
    repos = []
    try:
        data = github_json(
            "https://api.github.com/search/repositories"
            "?q=topic:navi-rag&per_page=30&sort=updated"
        )
        failures = 0
        for item in data.get("items") or []:
            full = item.get("full_name")
            if not full:
                continue
            try:
                repos.append(fetch_repo_chip(full))
            except Exception:
                failures += 1
        if failures:
            warning = (
                "GitHub could not be fully read for "
                + str(failures)
                + " of the packs (rate limit or outage) — the list "
                "may be incomplete. Search again in a minute."
            )
    except Exception as e:
        error = "GitHub search failed: " + str(e)
    installs = {row.get("full_name"): row for row in load_rag_installs()}
    packs = []
    for repo in repos:
        inst = installs.get(repo["fullName"])
        update = False
        if inst:
            if repo["latestRelease"]:
                update = inst.get("installed_tag") != repo["latestRelease"]["tag"]
            else:
                update = bool(
                    inst.get("installed_pushed_at")
                    and repo["pushedAt"] > inst["installed_pushed_at"]
                )
        entry = dict(repo)
        entry["inCatalog"] = True
        entry["installed"] = bool(inst)
        entry["installedTag"] = inst.get("installed_tag") if inst else None
        entry["installedRef"] = _display_ref(inst.get("installed_ref")) if inst else None
        entry["installedAt"] = inst.get("installed_at") if inst else None
        entry["updateAvailable"] = update
        entry["localDir"] = inst.get("local_dir") if inst else None
        entry["active"] = bool(inst.get("active", True)) if inst else None
        entry["docCount"] = inst.get("doc_count") if inst else None
        entry["locallyEdited"] = bool(inst.get("locally_edited")) if inst else False
        packs.append(entry)
    seen = {p["fullName"] for p in packs}
    for full, inst in installs.items():
        if full in seen:
            continue
        packs.append({
            "fullName": full,
            "name": inst.get("name") or full.split("/")[-1],
            "owner": full.split("/")[0],
            "description": "",
            "htmlUrl": inst.get("html_url") or "",
            "stars": 0, "forks": 0, "language": "—", "topics": [],
            "updatedAt": "",
            "pushedAt": inst.get("installed_pushed_at") or "",
            "defaultBranch": "main", "openIssues": 0,
            "latestRelease": None,
            "inCatalog": False, "installed": True,
            "installedTag": inst.get("installed_tag"),
            "installedRef": _display_ref(inst.get("installed_ref")),
            "installedAt": inst.get("installed_at"),
            "updateAvailable": False,
            "localDir": inst.get("local_dir"),
            "active": bool(inst.get("active", True)),
            "docCount": inst.get("doc_count"),
            "locallyEdited": bool(inst.get("locally_edited")),
        })
    view = {"fetchedAt": _now_iso(), "packs": packs}
    if error:
        view["error"] = error
    if warning:
        view["warning"] = warning
    return view


# ------------------------------- Voice -------------------------------
# Her voice, fully local. The bridge stays stdlib-only: the speech
# engines (faster-whisper for hearing, Kokoro or Piper for speaking)
# are optional dependencies, imported lazily the first time a voice
# endpoint is used. When they are not importable, the endpoints say
# so, with the step that installs them — nothing fakes audio.
# Settings live in navi.config.json's "voice" section; models land
# in voice/models/ on first use; the live call is voice/state.json
# and finished calls are archived to voice/calls.json.

VOICE_DIR = os.path.join(ROOT, "voice")
VOICE_MODELS_DIR = os.path.join(VOICE_DIR, "models")
VOICE_STATE_PATH = os.path.join(VOICE_DIR, "state.json")
VOICE_CALLS_PATH = os.path.join(VOICE_DIR, "calls.json")


def _adopt_voice_venv():
    # The installer lays the speech engines down in an isolated
    # venv at voice/venv, and the launchers run this bridge with
    # that venv's Python — but a bridge started any other way (by
    # hand, by an older launcher, or one already running from
    # before the voice step) runs under the system Python and
    # would report her voice missing while the engines sit right
    # beside it. Adopt the venv's site-packages into this
    # interpreter's module path, so the engines the installer laid
    # down are the engines this bridge finds, whichever Python
    # started it. The installer builds the venv from the system
    # python3, so the packages are built for this Python family
    # and import identically. Returns the adopted path, or None.
    venv = os.path.join(VOICE_DIR, "venv")
    candidates = []
    lib = os.path.join(venv, "lib")
    if os.path.isdir(lib):
        try:
            for entry in sorted(os.listdir(lib)):
                candidates.append(os.path.join(lib, entry, "site-packages"))
        except Exception:
            pass
    candidates.append(os.path.join(venv, "Lib", "site-packages"))
    for path in candidates:
        if os.path.isdir(path):
            if path not in sys.path:
                sys.path.insert(0, path)
            return path
    return None


VOICE_VENV_SITE_PACKAGES = _adopt_voice_venv()
VOICE_INSTALL_HINT = (
    "Install her voice: re-run the installer and say yes at the voice "
    "step, or run: python3 -m pip install -r requirements-voice.txt"
)

VOICE_DEFAULTS = {
    "enabled": True,
    "stt_model": "small.en",
    "tts_engine": "kokoro",
    "tts_voice": "bf_isabella",
    "rate": 1.0,
    "pitch": 1.0,
}


class VoiceUnavailable(Exception):
    pass


def voice_config(cfg):
    raw = cfg.get("voice") or {}
    stt = raw.get("stt") or {}
    tts = raw.get("tts") or {}
    out = dict(VOICE_DEFAULTS)
    if isinstance(raw.get("enabled"), bool):
        out["enabled"] = raw["enabled"]
    if stt.get("model"):
        out["stt_model"] = str(stt["model"])
    if tts.get("engine") in ("kokoro", "piper"):
        out["tts_engine"] = tts["engine"]
    if tts.get("voice"):
        out["tts_voice"] = str(tts["voice"])
    for key in ("rate", "pitch"):
        try:
            val = float(tts.get(key))
            if 0.5 <= val <= 2.0:
                out[key] = val
        except (TypeError, ValueError):
            pass
    return out


def save_voice_config(patch):
    # Voice settings persist into navi.config.json, beside the rest
    # of the app config — the dashboard's Voice tab writes them here.
    try:
        with open(CONFIG_PATH) as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    cur = voice_config(cfg)
    for key, val in patch.items():
        if key in VOICE_DEFAULTS:
            cur[key] = val
    cfg["voice"] = {
        "enabled": bool(cur["enabled"]),
        "stt": {"engine": "faster-whisper", "model": cur["stt_model"]},
        "tts": {
            "engine": cur["tts_engine"],
            "voice": cur["tts_voice"],
            "rate": cur["rate"],
            "pitch": cur["pitch"],
        },
    }
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    return cur


def _module_available(name):
    try:
        return importlib.util.find_spec(name) is not None
    except Exception:
        return False


_engine_probes = {}


def _probe_engine(pkg, symbol):
    # The one availability truth for a speech engine: the exact import
    # the synthesis/transcription paths perform (from kokoro import
    # KPipeline, from faster_whisper import WhisperModel), attempted
    # once in this interpreter and cached. find_spec alone is not
    # proof — it locates a package's directory even when that
    # package's own imports fail under this Python, which is what
    # happens when the bridge runs under a different interpreter than
    # the voice venv's and merely adopted its site-packages. That
    # split is how every status surface could call Kokoro installed
    # while a speak attempt called it missing. voice_status reports
    # this probe and the loaders fail with the same distinction, so
    # the pipeline strip, the status column, and the banner can never
    # disagree again. Returns (available, exception-or-None).
    key = pkg + ":" + symbol
    if key not in _engine_probes:
        try:
            mod = importlib.import_module(pkg)
            if symbol:
                getattr(mod, symbol)
            _engine_probes[key] = (True, None)
        except Exception as e:
            _engine_probes[key] = (False, e)
    return _engine_probes[key]


def _engine_detail(pkg, exc):
    # Why an engine is unavailable, in words that name the failing
    # piece: a genuinely absent package gets the install step; a
    # package that is present but fails to load says so and carries
    # the real import error instead of hiding behind "not installed".
    if exc is None:
        return None
    if not _module_available(pkg):
        return ("The " + pkg + " package is not installed for the Python "
                "running this bridge. " + VOICE_INSTALL_HINT)
    return ("The " + pkg + " package is installed, but the Python running "
            "this bridge cannot load it: " + type(exc).__name__ + ": "
            + str(exc) + ". " + VOICE_INSTALL_HINT)


def _unavailable_message(label, pkg, exc):
    # What the loaders raise on failure — the same distinction the
    # availability probe reports, so a speak failure and the status
    # check tell one story.
    if not _module_available(pkg):
        return label + " is not installed. " + VOICE_INSTALL_HINT
    return (label + " is installed but failed to load: "
            + type(exc).__name__ + ": " + str(exc))


_KOKORO_VOICE_RE = re.compile(r"^([a-z])([fm])_([a-z0-9]+)$")
_KOKORO_LANGS = {
    "a": "American", "b": "British", "e": "Spanish", "f": "French",
    "h": "Hindi", "i": "Italian", "j": "Japanese",
    "p": "Brazilian Portuguese", "z": "Mandarin",
}
_voices_cache = {}


def _kokoro_voice_label(vid):
    # Labels are derived from the voice id (af_heart -> "Heart —
    # American female"), never a per-voice lookup table: a voice the
    # list has never seen still gets a correct name.
    m = _KOKORO_VOICE_RE.match(vid)
    if not m:
        return vid
    name = m.group(3).replace("_", " ").title()
    lang = _KOKORO_LANGS.get(m.group(1), "")
    who = "female" if m.group(2) == "f" else "male"
    return name + " — " + (lang + " " if lang else "") + who


def discover_kokoro_voices(current):
    # The voice picker is populated from what this machine's Kokoro
    # installation actually has — never a hardcoded list. Sources,
    # in order: the voice .pt files the installation already holds
    # (the kokoro package's own folder, voice/models, the
    # Hugging Face cache KPipeline downloads into); and, when none
    # are on disk yet, the voice files in the Kokoro-82M repo the
    # installed package itself pulls from (huggingface_hub ships
    # with kokoro) — those download on first use, the same pattern
    # the Piper voices follow below. When neither works (engine not
    # installed, machine offline), the saved voice alone is listed,
    # so the picker never renders empty or invents voices.
    if "kokoro" in _voices_cache:
        return _voices_cache["kokoro"]
    found = {}
    roots = []
    try:
        import kokoro as _kokoro_pkg
        roots.append(os.path.dirname(os.path.abspath(_kokoro_pkg.__file__)))
    except Exception:
        pass
    roots.append(VOICE_MODELS_DIR)
    hf_home = os.environ.get("HF_HOME") or os.path.join(
        os.path.expanduser("~"), ".cache", "huggingface")
    roots.append(os.path.join(hf_home, "hub"))
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if fn.endswith(".pt"):
                    vid = fn[:-3]
                    if _KOKORO_VOICE_RE.match(vid):
                        found.setdefault(vid, "installed")
    source = "installed"
    if not found and _probe_engine("kokoro", "KPipeline")[0]:
        try:
            from huggingface_hub import list_repo_files
            for f in list_repo_files("hexgrad/Kokoro-82M"):
                if f.startswith("voices/") and f.endswith(".pt"):
                    vid = os.path.basename(f)[:-3]
                    if _KOKORO_VOICE_RE.match(vid):
                        found.setdefault(vid, "catalog")
            if found:
                source = "catalog"
        except Exception:
            pass
    if not found:
        found = {current: "current"}
        source = "current"
    result = {
        "voices": [
            {"id": vid, "label": _kokoro_voice_label(vid), "source": found[vid]}
            for vid in sorted(found)
        ],
        "source": source,
    }
    _voices_cache["kokoro"] = result
    return result


def discover_piper_voices(current):
    # Same rule for Piper: voices already downloaded into
    # voice/models/piper, plus the en voices in the piper-voices
    # repo (each downloads on first use — _piper_voice_file does
    # exactly that). The saved voice is always present.
    found = {}
    pdir = os.path.join(VOICE_MODELS_DIR, "piper")
    if os.path.isdir(pdir):
        for fn in sorted(os.listdir(pdir)):
            if fn.endswith(".onnx"):
                found[fn[:-5]] = "installed"
    if not any(s == "installed" for s in found.values()):
        try:
            from huggingface_hub import list_repo_files
            for f in list_repo_files("rhasspy/piper-voices"):
                parts = f.split("/")
                if (len(parts) == 5 and parts[0] == "en"
                        and parts[4].endswith(".onnx")):
                    found.setdefault(parts[4][:-5], "catalog")
        except Exception:
            pass
    if current and current not in found:
        found[current] = "current"
    source = ("installed" if any(s == "installed" for s in found.values())
              else "catalog" if any(s == "catalog" for s in found.values())
              else "current")
    voices = []
    for vid in sorted(found):
        parts = vid.split("-")
        if len(parts) == 3:
            label = (parts[1].title() + " (" + parts[0] + ", "
                     + parts[2] + ")")
        else:
            label = vid
        voices.append({"id": vid, "label": label, "source": found[vid]})
    return {"voices": voices, "source": source}


def voice_status(cfg):
    vc = voice_config(cfg)
    stt_ok, stt_exc = _probe_engine("faster_whisper", "WhisperModel")
    engine_pkg = "kokoro" if vc["tts_engine"] == "kokoro" else "piper"
    tts_ok, tts_exc = _probe_engine(
        engine_pkg, "KPipeline" if engine_pkg == "kokoro" else "PiperVoice")
    disc = (discover_kokoro_voices(vc["tts_voice"])
            if vc["tts_engine"] == "kokoro"
            else discover_piper_voices(vc["tts_voice"]))
    return {
        "enabled": vc["enabled"],
        "config": vc,
        "python": sys.executable,
        "venv": VOICE_VENV_SITE_PACKAGES,
        "stt": {
            "engine": "faster-whisper",
            "model": vc["stt_model"],
            "available": stt_ok,
            "detail": _engine_detail("faster_whisper", stt_exc),
        },
        "tts": {
            "engine": vc["tts_engine"],
            "voice": vc["tts_voice"],
            "available": tts_ok,
            "detail": _engine_detail(engine_pkg, tts_exc),
        },
        "voices": disc["voices"],
        "voices_source": disc["source"],
        "call": load_voice_state().get("call"),
    }


def load_voice_state():
    try:
        with open(VOICE_STATE_PATH) as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass
    return {"call": None}


def save_voice_state(state):
    os.makedirs(VOICE_DIR, exist_ok=True)
    with open(VOICE_STATE_PATH, "w") as f:
        json.dump(state, f)


def load_voice_calls():
    try:
        with open(VOICE_CALLS_PATH) as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


_voice_cache = {}
_voice_lock = threading.Lock()


def _stt_model(vc):
    # Loaded once, then kept warm: a Whisper load takes seconds and
    # a call shouldn't pay it per sentence. The download lands in
    # voice/models/ on first use and stays there across installs.
    key = "stt:" + vc["stt_model"]
    with _voice_lock:
        if key not in _voice_cache:
            try:
                from faster_whisper import WhisperModel
            except Exception as e:
                raise VoiceUnavailable(_unavailable_message("faster-whisper", "faster_whisper", e))
            os.makedirs(VOICE_MODELS_DIR, exist_ok=True)
            _voice_cache[key] = WhisperModel(
                vc["stt_model"], device="cpu", compute_type="int8",
                download_root=os.path.join(VOICE_MODELS_DIR, "whisper"),
            )
        return _voice_cache[key]


def transcribe_audio(audio_bytes, vc):
    if not audio_bytes:
        raise VoiceUnavailable("No audio arrived — the clip was empty.")
    model = _stt_model(vc)
    fd, path = tempfile.mkstemp(suffix=".webm", prefix="navi-stt-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(audio_bytes)
        segments, _info = model.transcribe(path, beam_size=1, vad_filter=True)
        return "".join(seg.text for seg in segments).strip()
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


def _samples_to_wav(samples, sample_rate):
    # Float samples in [-1, 1] to a 16-bit PCM WAV, stdlib only.
    import wave as wave_mod
    buf = io.BytesIO()
    with wave_mod.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sample_rate))
        frames = bytearray()
        for s in samples:
            v = max(-1.0, min(1.0, float(s)))
            frames += struct.pack("<h", int(v * 32767))
        w.writeframes(bytes(frames))
    return buf.getvalue()


def _pitch_shift_wav(wav_bytes, vc):
    # Varispeed pitch: replaying the same frames at a scaled rate
    # shifts pitch (and tempo along with it) — the honest stdlib
    # way of doing it, no DSP library pretending otherwise.
    try:
        factor = float(vc.get("pitch") or 1.0)
    except (TypeError, ValueError):
        factor = 1.0
    if abs(factor - 1.0) < 0.001:
        return wav_bytes
    import wave as wave_mod
    src = wave_mod.open(io.BytesIO(wav_bytes), "rb")
    params = src.getparams()
    frames = src.readframes(src.getnframes())
    src.close()
    out = io.BytesIO()
    dst = wave_mod.open(out, "wb")
    dst.setparams(params)
    dst.setframerate(max(4000, int(params.framerate * factor)))
    dst.writeframes(frames)
    dst.close()
    return out.getvalue()


def _kokoro_pipeline(vc):
    key = "kokoro"
    with _voice_lock:
        if key not in _voice_cache:
            try:
                from kokoro import KPipeline
            except Exception as e:
                raise VoiceUnavailable(_unavailable_message("Kokoro", "kokoro", e))
            lang = "b" if vc["tts_voice"].startswith("b") else "a"
            _voice_cache[key] = KPipeline(lang_code=lang)
        return _voice_cache[key]


PIPER_VOICE_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/"


def _piper_voice_file(vc):
    # Piper voices are .onnx + .onnx.json pairs named like
    # en_US-lessac-medium, filed as en/<locale>/<name>/<quality>/.
    name = vc["tts_voice"]
    parts = name.split("-")
    if len(parts) != 3:
        raise VoiceUnavailable("Unknown Piper voice name: " + name)
    locale, speaker, quality = parts
    lang = locale.split("_")[0]
    rel = lang + "/" + locale + "/" + speaker + "/" + quality + "/" + name
    onnx = os.path.join(VOICE_MODELS_DIR, "piper", name + ".onnx")
    conf = onnx + ".json"
    if not (os.path.isfile(onnx) and os.path.isfile(conf)):
        os.makedirs(os.path.dirname(onnx), exist_ok=True)
        for suffix, dest in ((".onnx", onnx), (".onnx.json", conf)):
            try:
                urllib.request.urlretrieve(PIPER_VOICE_BASE + rel + suffix, dest)
            except Exception as e:
                raise VoiceUnavailable("Could not download the Piper voice " + name + ": " + str(e))
    return onnx


def _piper_load(vc):
    # Load (or fetch from cache) the configured Piper voice — the
    # warmup path and synthesis share this one cache entry.
    try:
        from piper import PiperVoice
    except Exception as e:
        raise VoiceUnavailable(_unavailable_message("Piper", "piper", e))
    onnx = _piper_voice_file(vc)
    key = "piper:" + onnx
    with _voice_lock:
        if key not in _voice_cache:
            _voice_cache[key] = PiperVoice.load(onnx)
        return _voice_cache[key]


def _piper_wav(text, vc):
    voice = _piper_load(vc)
    import wave as wave_mod
    buf = io.BytesIO()
    try:
        from piper.config import SynthesisConfig
        with wave_mod.open(buf, "wb") as w:
            voice.synthesize_wav(
                text, w,
                syn_config=SynthesisConfig(length_scale=1.0 / max(0.25, float(vc["rate"]))),
            )
    except VoiceUnavailable:
        raise
    except Exception as e:
        raise VoiceUnavailable("Piper could not speak that line: " + str(e))
    return _pitch_shift_wav(buf.getvalue(), vc)


def synthesize_wav(text, vc):
    text = (text or "").strip()
    if not text:
        raise VoiceUnavailable("Nothing to say — the line was empty.")
    if not vc["enabled"]:
        raise VoiceUnavailable("Voice is turned off — enable it in the Voice tab.")
    if vc["tts_engine"] == "piper":
        return _piper_wav(text, vc)
    pipeline = _kokoro_pipeline(vc)
    samples = []
    for _g, _p, audio in pipeline(text, voice=vc["tts_voice"], speed=float(vc["rate"])):
        if audio is None:
            continue
        try:
            samples.extend(float(x) for x in audio)
        except TypeError:
            samples.append(float(audio))
    if not samples:
        raise VoiceUnavailable("Kokoro produced no audio for that line.")
    return _pitch_shift_wav(_samples_to_wav(samples, 24000), vc)


def speak_reply(text, cfg):
    # /api/chat with speak:true — her reply out loud on this machine
    # as well as in the thread. Best-effort by design: the reply is
    # already on its way back to the dashboard either way, so a
    # speech failure reports itself instead of failing the chat.
    vc = voice_config(cfg)
    if not vc["enabled"]:
        return {"ok": False, "error": "Voice is turned off."}
    try:
        wav = synthesize_wav(text, vc)
    except VoiceUnavailable as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:
        return {"ok": False, "error": "Speech failed: " + str(e)}
    try:
        import sounddevice as sd
        import soundfile as sf
        data, rate = sf.read(io.BytesIO(wav), dtype="float32")
        sd.play(data, rate)
        return {"ok": True, "via": "sounddevice"}
    except Exception:
        pass
    fd, path = tempfile.mkstemp(suffix=".wav", prefix="navi-say-")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(wav)
        for player in ("aplay", "paplay", "afplay"):
            exe = shutil.which(player)
            if exe:
                subprocess.Popen([exe, path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return {"ok": True, "via": player}
        return {"ok": False, "error": "No audio player found (sounddevice, aplay, paplay, or afplay)."}
    except Exception as e:
        return {"ok": False, "error": "Playback failed: " + str(e)}


def llamafile_alive(endpoint):
    try:
        urllib.request.urlopen(endpoint.replace("/v1", "/"), timeout=2)
        return True
    except Exception:
        return False


_llamafile_proc = None


def llamafile_port(endpoint):
    try:
        port = urllib.parse.urlparse(endpoint).port
    except Exception:
        port = None
    return port or 8080


def llamafile_binary(cfg):
    # Where the installer puts navi.llamafile: the configured install
    # dir, or right beside this bridge — the bridge ships in the
    # install root, so on a normal install those are the same place.
    dirs = []
    install_dir = cfg.get("install_dir")
    if install_dir:
        dirs.append(os.path.expanduser(install_dir))
    dirs.append(ROOT)
    for d in dirs:
        for name in ("navi.llamafile", "navi.llamafile.exe"):
            path = os.path.join(d, name)
            if os.path.isfile(path):
                return path
    return None


def wait_for_llamafile(endpoint, proc, log_path=None):
    # Loading a multi-GB model takes a while; give it two minutes.
    for _ in range(120):
        if llamafile_alive(endpoint):
            return True, None
        if proc is not None and proc.poll() is not None:
            tail = ""
            if log_path:
                try:
                    with open(log_path, "rb") as f:
                        data = f.read().decode(errors="replace").strip()
                    if data:
                        tail = data.splitlines()[-1]
                except Exception:
                    tail = ""
            msg = ("navi.llamafile exited (code " + str(proc.returncode) +
                   ") before it started answering.")
            if tail:
                msg += " Last log line: " + tail
            msg += " Full log: navi.llamafile.log beside the app."
            return False, msg
        time.sleep(1)
    return False, ("navi.llamafile is still loading after two minutes — "
                   "its output is in navi.llamafile.log beside the app.")


def runtime_settings(cfg):
    # Her llamafile runtime settings, from the hardware profile the
    # installer wrote into the config (hardware_profile + runtime).
    # No profile (a pre-.34 config) -> the fluid floor.
    rt = cfg.get("runtime") or {}
    hp = (cfg.get("hardware_profile") or {}).get("settings") or {}
    def pick(a, b, fallback):
        v = rt.get(a)
        if v is None:
            v = hp.get(b)
        try:
            return int(v)
        except Exception:
            return fallback
    return {
        "threads": pick("threads", "threads", 4),
        "ctx_size": pick("ctx_size", "ctxSize", 4096),
        "batch_size": pick("batch_size", "batchSize", 512),
        "gpu_layers": pick("gpu_layers", "gpuLayers", 0),
    }


def llamafile_args(cfg):
    s = runtime_settings(cfg)
    args = ["--server", "--v2", "--ctx-size", str(s["ctx_size"]),
            "--threads", str(s["threads"]), "--batch-size", str(s["batch_size"])]
    if s["gpu_layers"] > 0:
        args += ["--n-gpu-layers", str(s["gpu_layers"])]
    return args


def detect_hardware():
    # Real detection for /api/hardware/redetect — stdlib only, per-OS.
    # Linux: /proc + lspci/nvidia-smi. macOS: sysctl + system_profiler.
    # Windows: CIM via PowerShell. Anything unconfirmable stays
    # "unknown" rather than guessed — derivation treats it CPU-only.
    import platform as _pf
    det = {"os": "unknown", "osLabel": _pf.platform(), "cpuModel": _pf.processor() or "unknown CPU",
           "cpuCores": os.cpu_count() or 1, "performanceCores": None,
           "totalRamGB": 0.0, "gpuPresent": False, "gpuName": "", "gpuKind": "none", "gpuVramGB": None}
    system = _pf.system().lower()
    try:
        if system == "linux":
            det["os"] = "linux"; det["osLabel"] = "Linux"
            mem_kb = 0
            cpu_name = ""
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        mem_kb = int(line.split()[1])
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if line.startswith("model name"):
                        cpu_name = line.split(":", 1)[1].strip(); break
            if cpu_name:
                det["cpuModel"] = cpu_name
            det["totalRamGB"] = round(mem_kb / 1048576.0, 1) if mem_kb else 0.0
            # Intel hybrid: performance cores are hard to prove from
            # /proc alone; the derivation's logical-core rule covers it.
            try:
                out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                                     capture_output=True, text=True, timeout=5).stdout.strip()
                if out:
                    parts = [p.strip() for p in out.splitlines()[0].split(",")]
                    det["gpuPresent"] = True; det["gpuName"] = parts[0]; det["gpuKind"] = "discrete"
                    if len(parts) > 1:
                        det["gpuVramGB"] = int(round(float(parts[1].split()[0]) / 1024.0))
                else:
                    raise RuntimeError("no nvidia-smi output")
            except Exception:
                try:
                    out = subprocess.run(["lspci"], capture_output=True, text=True, timeout=5).stdout
                    for line in out.splitlines():
                        if "VGA compatible controller" in line or "3D controller" in line:
                            det["gpuPresent"] = True
                            det["gpuName"] = line.split(":", 2)[-1].strip()
                            low = det["gpuName"].lower()
                            det["gpuKind"] = "discrete" if ("nvidia" in low or "radeon rx" in low or "geforce" in low) else "integrated"
                            break
                except Exception:
                    pass
        elif system == "darwin":
            det["os"] = "macos"; det["osLabel"] = "macOS"
            def _sysctl(key):
                return subprocess.run(["sysctl", "-n", key], capture_output=True, text=True, timeout=5).stdout.strip()
            det["cpuModel"] = _sysctl("machdep.cpu.brand_string") or det["cpuModel"]
            det["cpuCores"] = int(_sysctl("hw.ncpu") or det["cpuCores"])
            try:
                det["performanceCores"] = int(_sysctl("hw.perflevel0.logicalcpu") or 0) or None
            except Exception:
                det["performanceCores"] = None
            det["totalRamGB"] = round(int(_sysctl("hw.memsize") or 0) / 1073741824.0, 1)
            det["gpuPresent"] = True; det["gpuName"] = det["cpuModel"] + " GPU"; det["gpuKind"] = "integrated"
        elif system == "windows":
            det["os"] = "windows"; det["osLabel"] = "Windows"
            def _ps(expr):
                return subprocess.run(["powershell", "-NoProfile", "-Command", expr],
                                      capture_output=True, text=True, timeout=10).stdout.strip()
            det["cpuModel"] = _ps("(Get-CimInstance Win32_Processor | Select-Object -First 1).Name") or det["cpuModel"]
            det["cpuCores"] = int(_ps("(Get-CimInstance Win32_Processor | Select-Object -First 1).NumberOfLogicalProcessors") or det["cpuCores"])
            det["totalRamGB"] = round(int(_ps("(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory") or 0) / 1073741824.0, 1)
            gpu_name = _ps("(Get-CimInstance Win32_VideoController | Select-Object -First 1).Name")
            if gpu_name:
                det["gpuPresent"] = True; det["gpuName"] = gpu_name
                low = gpu_name.lower()
                if "nvidia" in low or "geforce" in low or "radeon rx" in low:
                    det["gpuKind"] = "discrete"
                    vram = _ps("(Get-CimInstance Win32_VideoController | Select-Object -First 1).AdapterRAM")
                    try:
                        det["gpuVramGB"] = int(round(int(vram) / 1073741824.0)) or None
                    except Exception:
                        det["gpuVramGB"] = None
                else:
                    det["gpuKind"] = "integrated"
    except Exception:
        pass
    return det


def derive_hardware_settings(d):
    # The bridge's copy of the derivation table (hardware.ts is the
    # source of truth; the installers carry the same table in shell).
    ram = float(d.get("totalRamGB") or 0)
    logical = max(1, int(d.get("cpuCores") or 1))
    perf = d.get("performanceCores")
    reasoning = []
    if perf:
        threads = max(2, min(12, int(perf)))
        reasoning.append(f"Threads {threads}: matched to the {perf} performance cores.")
    elif logical >= 16:
        threads = 8; reasoning.append(f"Threads 8: half of {logical} logical cores, capped.")
    elif logical >= 8:
        threads = 4; reasoning.append(f"Threads 4: half of {logical} logical cores.")
    elif logical >= 4:
        threads = 2; reasoning.append(f"Threads 2: conservative for a {logical}-core machine.")
    else:
        threads = 1; reasoning.append("Threads 1: single-core floor.")
    if ram < 6:
        ctx = 2048; reasoning.append("Context 2048: under 6 GiB RAM — smallest fluid window.")
    elif ram < 12:
        ctx = 4096; reasoning.append(f"Context 4096: {ram:.1f} GiB RAM — the proven fluid size for this class.")
    elif ram < 20:
        ctx = 8192; reasoning.append(f"Context 8192: {ram:.1f} GiB RAM leaves comfortable headroom.")
    elif ram < 40:
        ctx = 16384; reasoning.append(f"Context 16384: {ram:.1f} GiB RAM.")
    else:
        ctx = 32768; reasoning.append(f"Context 32768: {ram:.1f} GiB RAM — workstation headroom.")
    batch = 256 if ram < 6 else (512 if ram < 20 else 1024)
    reasoning.append(f"Batch {batch}: sized to RAM ({ram:.1f} GiB).")
    gpu_layers = 0
    vram = d.get("gpuVramGB")
    if d.get("gpuKind") == "discrete" and vram is not None and vram >= 4:
        gpu_layers = 99 if vram >= 12 else (28 if vram >= 8 else (20 if vram >= 6 else 12))
        reasoning.append(f"GPU layers {gpu_layers}: discrete GPU with {vram} GiB VRAM.")
    elif d.get("gpuKind") == "integrated":
        reasoning.append("GPU layers 0: integrated graphics share system RAM — CPU inference is the fluid path.")
    else:
        reasoning.append("GPU layers 0: no confirmed discrete GPU — CPU-only.")
    if ram < 6 or logical <= 4:
        tier, tier_label = "constrained", "Constrained — small machine, fluid floor"
    elif gpu_layers > 0 and ram >= 16:
        tier, tier_label = ("workstation", "Workstation — discrete GPU + ample RAM") if ram >= 32 else ("performance", "Performance — discrete GPU acceleration")
    elif ram >= 20:
        tier, tier_label = "performance", "Performance — ample RAM, CPU inference scaled up"
    elif ram >= 12:
        tier, tier_label = "balanced", "Balanced — above the fluid baseline"
    else:
        tier, tier_label = "fluid", "Fluid — Framework-class baseline"
    return {"threads": threads, "ctxSize": ctx, "batchSize": batch, "gpuLayers": gpu_layers}, tier, tier_label, reasoning


def hardware_profile_view(cfg):
    hp = cfg.get("hardware_profile")
    if isinstance(hp, dict) and hp.get("detected") and hp.get("settings"):
        view = dict(hp)
        s = runtime_settings(cfg)
        view["settings"] = {"threads": s["threads"], "ctxSize": s["ctx_size"], "batchSize": s["batch_size"], "gpuLayers": s["gpu_layers"]}
        view["flags"] = " ".join(llamafile_args(cfg)[2:])
        return view
    return {"detected": None, "settings": runtime_settings(cfg), "source": "auto",
            "note": "No hardware profile in this config (it predates build .34) — the fluid floor is in use. Re-detect to profile this machine."}


def save_hardware_profile(profile):
    cfg = load_config()
    cfg["hardware_profile"] = profile
    s = profile["settings"]
    cfg["runtime"] = {"threads": s["threads"], "ctx_size": s["ctxSize"], "batch_size": s["batchSize"], "gpu_layers": s["gpuLayers"],
                      "flags": f"--ctx-size {s['ctxSize']} --threads {s['threads']} --batch-size {s['batchSize']}" + (f" --n-gpu-layers {s['gpuLayers']}" if s["gpuLayers"] > 0 else "")}
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    try:
        with open(os.path.join(ROOT, "hardware-profile.log"), "a") as f:
            for line in profile.get("installLog") or []:
                f.write(line + "\n")
    except Exception:
        pass
    return cfg


def start_llamafile(cfg, endpoint):
    # App-load mode owns the server process: the bridge starts it
    # with the app's one launch command — ./navi.llamafile --server
    # --v2 plus the runtime flags from the hardware profile in the
    # config (see runtime_settings) — never a hard-coded set.
    # Returns (ok, error). Output goes to navi.llamafile.log next to
    # the binary so a failed start is diagnosable, not silent.
    global _llamafile_proc
    if _llamafile_proc is not None and _llamafile_proc.poll() is None:
        return wait_for_llamafile(endpoint, _llamafile_proc)
    binary = llamafile_binary(cfg)
    if not binary:
        searched = os.path.expanduser(cfg.get("install_dir") or ROOT)
        return False, ("navi.llamafile was not found in " + searched +
                       " — run the installer so it can download the model server.")
    log_path = os.path.join(os.path.dirname(binary), "navi.llamafile.log")
    try:
        log = open(log_path, "ab")
    except Exception:
        log = subprocess.DEVNULL
    try:
        _llamafile_proc = subprocess.Popen(
            [binary] + llamafile_args(cfg),
            cwd=os.path.dirname(binary),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    except Exception as e:
        return False, "Could not start navi.llamafile: " + str(e)
    return wait_for_llamafile(endpoint, _llamafile_proc, log_path)


_served_model_cache = {}


def served_model(endpoint):
    # The model id the server itself reports (GET /v1/models). Asking
    # beats assuming: the name baked into a llamafile is whatever its
    # builder chose, and a server that validates the model string
    # rejects a guessed one. Cached per endpoint; None when the
    # server won't say (callers fall back to the configured name).
    if endpoint in _served_model_cache:
        return _served_model_cache[endpoint]
    found = None
    try:
        with urllib.request.urlopen(endpoint.rstrip("/") + "/models", timeout=5) as resp:
            data = json.loads(resp.read().decode())
        entries = data.get("data") or []
        if entries and entries[0].get("id"):
            found = str(entries[0]["id"])
    except Exception:
        found = None
    _served_model_cache[endpoint] = found
    return found


# A chat request is always bounded. Left unbounded, the server
# generates until the model emits its end token or the context
# fills — and a model that doesn't stop on its own (a base-style
# model in a chat template can ramble for thousands of tokens)
# keeps a CPU busy far past any reasonable wait while the
# dashboard shows "thinking…". That was the "she is not chatting"
# failure, reproduced against this bridge: no max_tokens rode
# along, the generation outran the old 120-second socket timeout,
# and the request died misreporting a healthy, answering server
# as "unreachable" — from the operator's chair, Navi simply never
# replied. max_tokens caps the work; the wait is sized to let a
# bounded reply finish even at slow CPU generation speeds.
CHAT_MAX_TOKENS = 1024
CHAT_HISTORY_MESSAGES = 24
CHAT_TIMEOUT = 600


def llamafile_chat(messages, endpoint, model):
    # The llamafile server rejects a chat request whose JSON has no
    # "model" string (400 "JSON missing model string"), so a model
    # name rides along on every request — the id the server reports
    # for itself when it will say, otherwise the configured name.
    name = served_model(endpoint) or model
    body = json.dumps({
        "model": name,
        "messages": messages,
        "stream": False,
        "max_tokens": CHAT_MAX_TOKENS,
    }).encode()
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=CHAT_TIMEOUT) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        # Surface the server's own words — a bare "HTTP Error 400"
        # hides the reason it actually gave.
        try:
            detail = e.read().decode(errors="replace").strip()
        except Exception:
            detail = ""
        raise RuntimeError(
            "the llamafile server rejected the chat request (HTTP "
            + str(e.code) + ")" + ((": " + detail) if detail else "")
        )
    except TimeoutError:
        # The server is up — it was still generating when the wait
        # ran out. Saying "unreachable" here once sent the operator
        # hunting for a dead server that was never dead.
        raise RuntimeError(
            "navi.llamafile was still generating her answer after "
            + str(CHAT_TIMEOUT // 60) + " minutes, so the wait ran "
            "out — the server is up; the model is just slower than "
            "that on this machine right now. The request was "
            "bounded (" + str(CHAT_MAX_TOKENS) + " tokens at most), "
            "so sending the message again is safe."
        )
    except urllib.error.URLError as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason):
            raise RuntimeError(
                "navi.llamafile was still generating her answer "
                "when the wait ran out — the server is up; the "
                "model is just slower than the wait on this "
                "machine right now. Sending the message again "
                "is safe."
            )
        raise RuntimeError(
            "could not reach navi.llamafile at " + endpoint + ": "
            + str(reason)
        )
    content = data["choices"][0]["message"]["content"]
    if not (content or "").strip():
        # An empty reply renders as silence in the thread — the
        # same "she is not chatting" symptom by another road. Name
        # it where the operator can see it instead.
        raise RuntimeError(
            "navi.llamafile answered with an empty reply — the "
            "model ended its turn without saying anything. Sending "
            "the message again usually gets a real answer."
        )
    return content


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload, ctype="application/json"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # Nothing this bridge serves may come out of a browser cache.
        # The dashboard lives at the same localhost:8675 the operator's
        # own earlier UI used, so a cached page from that era would
        # otherwise keep answering in the bridge's place — the browser
        # showing an old UI while a current bridge serves underneath.
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            with open(os.path.join(ROOT, "app", "index.html"), "rb") as f:
                html = f.read()
            # Stamp the served page with the build and the install
            # folder it came from, as an HTML comment at the very top.
            # When the page at localhost:8675 is in doubt, viewing its
            # source settles which program served it: this line means
            # the Navi bridge did; its absence means something else
            # holds the port — and the folder names which install.
            banner = (
                "<!-- Apex dashboard — build " + BRIDGE_BUILD
                + " — served by the bridge in " + ROOT + " -->\n"
            ).encode()
            self._send(200, banner + html, "text/html; charset=utf-8")
        elif self.path == "/api/status":
            cfg = load_config()
            endpoint = cfg.get("live", {}).get("llamafile_endpoint", "")
            alive = llamafile_alive(endpoint)
            self._send(200, {
                "app": "Navi: Apex",
                "version": app_version(cfg),
                "versionStatus": app_version_status(cfg),
                "bridge": BRIDGE_BUILD,
                "port": BRIDGE_PORT,
                "dir": ROOT,
                "model": "navi",
                "llamafile_endpoint": endpoint,
                "llamafile_reachable": alive,
            })
        elif self.path == "/api/hardware":
            self._send(200, {"profile": hardware_profile_view(load_config())})
        elif self.path == "/api/commands":
            self._send(200, {"commands": installed_commands()})
        elif self.path == "/api/persona":
            self._send(200, {
                "soul": read_file(SOUL_PATH),
                "memory": read_file(MEMORY_PATH),
            })
        elif self.path == "/api/voice":
            # The Voice tab's state: her settings, whether each
            # speech engine is actually installed (never assumed),
            # and the live call, if one is running. This endpoint
            # must never die silently: a handler exception used to
            # drop the connection, and the dashboard could only say
            # "The bridge didn't answer" — the real reason (a voice
            # venv this Python couldn't read, a broken state file)
            # never reached the operator. Any failure is now
            # reported in the payload itself, as the detail.
            try:
                self._send(200, voice_status(load_config()))
            except Exception as e:
                try:
                    vc = voice_config(load_config())
                except Exception:
                    vc = dict(VOICE_DEFAULTS)
                detail = (
                    "The bridge's voice check itself failed: "
                    + type(e).__name__ + ": " + str(e)
                )
                self._send(200, {
                    "enabled": vc["enabled"],
                    "config": vc,
                    "python": sys.executable,
                    "venv": VOICE_VENV_SITE_PACKAGES,
                    "stt": {"engine": "faster-whisper", "model": vc["stt_model"],
                            "available": False, "detail": detail},
                    "tts": {"engine": vc["tts_engine"], "voice": vc["tts_voice"],
                            "available": False, "detail": detail},
                    "voices": [{"id": vc["tts_voice"], "label": vc["tts_voice"],
                                "source": "current"}],
                    "voices_source": "current",
                    "call": None,
                })
        elif self.path == "/api/voice/calls":
            self._send(200, {"calls": load_voice_calls()})
        elif self.path == "/api/chips/catalog":
            # Navi User Repo tab: live GitHub search for the navi-chips
            # topic, merged with the installs recorded on this
            # machine. A failed search reports its error and an empty
            # list rather than inventing a catalog.
            try:
                self._send(200, chip_catalog_view())
            except Exception as e:
                self._send(200, {
                    "error": "GitHub search failed: " + str(e),
                    "fetchedAt": None,
                    "chips": [],
                })
        elif self.path.split("?")[0] == "/api/chips/readme":
            # The back of a NUR flip card: the chip repo's README,
            # fetched raw from GitHub on demand. A repo without one
            # (or an unreachable GitHub) reports the reason instead
            # of inventing content.
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            repo = (qs.get("repo") or [""])[0]
            if not repo or "/" not in repo:
                self._send(200, {"ok": False, "error": "No repo was named."})
            else:
                try:
                    md = github_text(
                        "https://api.github.com/repos/" + repo + "/readme",
                        "application/vnd.github.raw+json",
                    )
                    self._send(200, {"ok": True, "markdown": md})
                except urllib.error.HTTPError as e:
                    if e.code == 404:
                        self._send(200, {"ok": False, "error": "This repo has no README."})
                    else:
                        self._send(200, {"ok": False, "error": "GitHub answered HTTP " + str(e.code) + " — the README could not be loaded."})
                except Exception:
                    self._send(200, {"ok": False, "error": "GitHub could not be reached — the README could not be loaded."})
        elif self.path == "/api/rag/catalog":
            # The RAG tab's Packs list: live GitHub search for the
            # navi-rag topic, merged with the packs installed on
            # this machine and their active flags.
            try:
                self._send(200, rag_catalog_view())
            except Exception as e:
                self._send(200, {
                    "error": "GitHub search failed: " + str(e),
                    "fetchedAt": None,
                    "packs": [],
                })
        elif self.path == "/api/rag/packs":
            self._send(200, {"packs": local_rag_packs()})
        elif self.path.split("?")[0] == "/api/rag/pack-source":
            # RAG Studio opens a pack from the folder for editing:
            # its name, description, and every document with its
            # body — forged, installed, or an exported bundle that
            # came back as an install alike.
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            slug = os.path.basename((qs.get("slug") or [""])[0])
            pack = rag_pack_documents(slug) if slug else None
            if pack:
                self._send(200, {"ok": True, "slug": slug, "name": pack["name"], "description": pack["description"], "documents": pack["documents"]})
            else:
                self._send(200, {"ok": False, "error": "That pack is not in the folder."})
        elif self.path.split("?")[0] == "/api/rag/export-file":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = os.path.basename((qs.get("file") or qs.get("name") or [""])[0])
            path = os.path.join(RAG_EXPORTS_DIR, name)
            if name.endswith(".zip") and os.path.isfile(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "application/zip")
            else:
                self._send(404, {"error": "not found"})
        elif self.path.split("?")[0] == "/api/chips/export-file":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = os.path.basename((qs.get("file") or qs.get("name") or [""])[0])
            path = os.path.join(CHIPS_EXPORTS_DIR, name)
            if name.endswith(".zip") and os.path.isfile(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "application/zip")
            else:
                self._send(404, {"error": "not found"})
        elif self.path.split("?")[0] == "/api/chips/file":
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = os.path.basename((qs.get("file") or qs.get("name") or [""])[0])
            path = os.path.join(CHIPS_DIR, name)
            if name.endswith(".png") and os.path.isfile(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "image/png")
            else:
                self._send(404, {"error": "not found"})
        elif self.path == "/api/workflows":
            # Workflows tab: the saved chains plus every chip in
            # the folder a step can point at.
            self._send(200, {
                "workflows": load_workflows(),
                "chips": [{"file": c["file"], "name": c["name"], "source": c.get("source"), "sourceKey": c.get("sourceKey"), "locallyEdited": bool(c.get("locallyEdited"))} for c in local_chips()],
            })
        elif self.path.split("?")[0] == "/api/chips/source":
            # Chip Studio opens a local chip for editing: its
            # full payload (name, description, code, output).
            qs = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            name = os.path.basename((qs.get("file") or qs.get("name") or [""])[0])
            path = os.path.join(CHIPS_DIR, name)
            payload = None
            if name.endswith(".png") and os.path.isfile(path):
                try:
                    with open(path, "rb") as f:
                        payload = parse_cartridge_png(f.read())
                except Exception:
                    payload = None
            if payload:
                payload["ok"] = True
                payload["file"] = name
                self._send(200, payload)
            else:
                self._send(200, {"ok": False, "error": "That chip could not be read."})
        elif self.path == "/api/github":
            # The GitHub account state in one answer: URLs, client-id
            # configuration, sign-in, backup settings, and the last
            # backup/import records. (Settings → GitHub & Backup reads
            # it; the GitHub section itself is the project pulse.)
            self._send(200, github_status_payload(load_config()))
        elif self.path == "/api/github/issues":
            # The Issues tab: live open issues for the project repo.
            self._send(200, github_issues_payload())
        elif self.path == "/api/github/pulse":
            # The Overview tab: the project's live pulse.
            self._send(200, github_pulse_payload())
        elif self.path == "/api/update/check":
            # The Updater's real check: the project's latest GitHub
            # release against the VERSION file. A check that cannot
            # complete answers ok: False with the reason — never a
            # made-up "up to date".
            self._send(200, update_check_payload(load_config()))
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        cfg = load_config()
        if self.path == "/api/shell":
            data = self._body()
            try:
                self._send(200, run_shell(
                    str(data.get("command", "")),
                    sudo=bool(data.get("sudo")),
                    sudo_password=str(data.get("sudo_password") or ""),
                ))
            except Exception as e:
                self._send(200, {"command": data.get("command", ""), "output": str(e), "exit_code": 1})
        elif self.path == "/api/update/apply":
            # Stages the latest release's package beside the app
            # (updates/<tag>/package) and answers with the staged
            # folder and the one install command — the bridge never
            # installs over the running app itself.
            self._send(200, update_apply_payload(cfg))
        elif self.path == "/api/sudo/auth":
            # Authenticate sudo mode once, when the operator enables
            # it: validate the password AND open the bridge's
            # persistent root shell with it (validate_sudo_password),
            # so the machine's whole PAM conversation — fingerprint
            # reader first, on machines that have one — happens
            # exactly once, here, instead of inside every command.
            # That is why this can legitimately take a while. The
            # password is never stored or logged — the dashboard
            # holds it in page memory and re-sends it with each sudo
            # request; the bridge forgets it once the shell is open.
            data = self._body()
            password = str(data.get("password") or "").split("\n")[0]
            if not password:
                self._send(200, {"ok": False, "error": "Enter the sudo password to authenticate sudo mode."})
            else:
                ok, err = validate_sudo_password(password)
                if ok:
                    self._send(200, {"ok": True})
                else:
                    self._send(200, {"ok": False, "error": "sudo authentication failed: " + str(err)})
        elif self.path == "/api/sudo/logout":
            # Sudo was turned off in the dashboard: close the root
            # shell now rather than leaving root open in the bridge
            # until it exits.
            with _sudo_lock:
                _root_shell_kill()
            self._send(200, {"ok": True})
        elif self.path == "/api/hardware/redetect":
            # Re-run profiling on the real machine and store it:
            # detected hardware, derived settings, reasoning, and
            # the log lines (also appended to hardware-profile.log).
            detected = detect_hardware()
            settings, tier, tier_label, reasoning = derive_hardware_settings(detected)
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            profile = {"detected": detected, "settings": settings, "autoSettings": settings,
                       "source": "auto", "tier": tier, "tierLabel": tier_label,
                       "reasoning": reasoning, "detectedAt": now,
                       "installLog": [f"[hardware] {now} — re-detect from Settings",
                                      f"[hardware] CPU: {detected['cpuModel']} — {detected['cpuCores']} logical cores",
                                      f"[hardware] RAM: {detected['totalRamGB']} GiB",
                                      f"[hardware] GPU: {detected['gpuName'] or 'none'} ({detected['gpuKind']})"] + [f"[hardware] → {r}" for r in reasoning]}
            save_hardware_profile(profile)
            self._send(200, {"ok": True, "profile": hardware_profile_view(load_config())})
        elif self.path == "/api/hardware/override":
            data = self._body()
            current = load_config().get("hardware_profile") or {}
            detected = current.get("detected") or detect_hardware()
            def _clamp(v, lo, hi, fallback):
                try:
                    return max(lo, min(hi, int(v)))
                except Exception:
                    return fallback
            auto = current.get("autoSettings") or current.get("settings") or {}
            settings = {
                "threads": _clamp(data.get("threads"), 1, 32, int(auto.get("threads") or 4)),
                "ctxSize": _clamp(data.get("ctxSize"), 512, 65536, int(auto.get("ctxSize") or 4096)),
                "batchSize": _clamp(data.get("batchSize"), 32, 4096, int(auto.get("batchSize") or 512)),
                "gpuLayers": _clamp(data.get("gpuLayers"), 0, 99, int(auto.get("gpuLayers") or 0)),
            }
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            profile = {"detected": detected, "settings": settings,
                       "autoSettings": auto if auto else settings, "source": "manual",
                       "tier": current.get("tier", "fluid"), "tierLabel": current.get("tierLabel", ""),
                       "reasoning": current.get("reasoning") or [], "detectedAt": current.get("detectedAt") or now,
                       "installLog": [f"[hardware] {now} — manual override in Settings: threads {settings['threads']}, ctx {settings['ctxSize']}, batch {settings['batchSize']}, gpu layers {settings['gpuLayers']}"]}
            save_hardware_profile(profile)
            self._send(200, {"ok": True, "profile": hardware_profile_view(load_config())})
        elif self.path == "/api/persona":
            data = self._body()
            os.makedirs(os.path.dirname(SOUL_PATH), exist_ok=True)
            if isinstance(data.get("soul"), str):
                with open(SOUL_PATH, "w") as f:
                    f.write(data["soul"])
            if isinstance(data.get("memory"), str):
                with open(MEMORY_PATH, "w") as f:
                    f.write(data["memory"])
            self._send(200, {"ok": True})
        elif self.path == "/api/llamafile/connect":
            endpoint = cfg.get("live", {}).get("llamafile_endpoint", "http://localhost:8080/v1")
            alive = llamafile_alive(endpoint)
            started = False
            error = None
            if not alive:
                if cfg.get("startup", "on-ui-launch") == "on-boot":
                    # Boot mode: the system service owns the server.
                    # The bridge probes and reports; it never spawns
                    # a second copy behind the service's back.
                    error = ("No answer from navi.llamafile at " + endpoint +
                             " — this install starts the server at system boot, "
                             "so the boot service should be running it; check that service.")
                else:
                    # App-load mode: connecting means starting the
                    # server, not just probing for it.
                    alive, error = start_llamafile(cfg, endpoint)
                    started = alive
            self._send(200, {
                "ok": alive,
                "status": "running" if alive else "stopped",
                "endpoint": endpoint,
                "started": started,
                "error": None if alive else error,
            })
        elif self.path == "/api/voice/warmup":
            # The dashboard fires this when the Voice view opens:
            # load the speech engines then — while the operator is
            # looking at the voice panel — instead of inside Call,
            # where the load would stall the pickup, and never at
            # bridge boot, because on a small machine the models are
            # real RAM that chat shouldn't pay for uninvited. The
            # loaders cache in _voice_cache and never evict, so once
            # warm she stays warm for the life of the bridge.
            vc = voice_config(cfg)
            warmed = []
            errors = {}
            if not vc["enabled"]:
                errors["voice"] = "Voice is turned off."
            else:
                try:
                    _stt_model(vc)
                    warmed.append("stt")
                except Exception as e:
                    errors["stt"] = str(e)
                try:
                    if vc["tts_engine"] == "kokoro":
                        _kokoro_pipeline(vc)
                    else:
                        _piper_load(vc)
                    warmed.append("tts")
                except Exception as e:
                    errors["tts"] = str(e)
            self._send(200, {"ok": not errors, "warmed": warmed, "errors": errors})
        elif self.path == "/api/voice/settings":
            # The Voice tab's settings, saved into navi.config.json.
            data = self._body()
            patch = {}
            if isinstance(data.get("enabled"), bool):
                patch["enabled"] = data["enabled"]
            if data.get("stt_model") in ("tiny.en", "base.en", "small.en"):
                patch["stt_model"] = data["stt_model"]
            if data.get("tts_engine") in ("kokoro", "piper"):
                patch["tts_engine"] = data["tts_engine"]
            if isinstance(data.get("tts_voice"), str) and data["tts_voice"].strip():
                patch["tts_voice"] = data["tts_voice"].strip()[:60]
            for key in ("rate", "pitch"):
                try:
                    val = float(data.get(key))
                    if 0.5 <= val <= 2.0:
                        patch[key] = val
                except (TypeError, ValueError):
                    pass
            cur = save_voice_config(patch)
            self._send(200, {"ok": True, "config": cur})
        elif self.path == "/api/voice/test":
            # "Hear her voice": synthesize one line and hand the WAV
            # to the dashboard to play. Honest failure when the
            # engine isn't installed — never a placeholder tone.
            data = self._body()
            vc = voice_config(cfg)
            line = str(data.get("text") or "").strip() or (
                "Hey — it's me, Navi. This is my voice, running entirely "
                "on your machine. Call me any time."
            )
            try:
                wav = synthesize_wav(line, vc)
                self._send(200, {
                    "ok": True,
                    "audio_b64": base64.b64encode(wav).decode(),
                    "mime": "audio/wav",
                })
            except VoiceUnavailable as e:
                self._send(200, {"ok": False, "error": str(e)})
            except Exception as e:
                self._send(200, {"ok": False, "error": "Speech failed: " + str(e)})
        elif self.path == "/api/voice/tts":
            # One line of hers in, the spoken WAV out — the call
            # panel plays her replies sentence by sentence.
            data = self._body()
            vc = voice_config(cfg)
            try:
                wav = synthesize_wav(str(data.get("text") or ""), vc)
                self._send(200, {
                    "ok": True,
                    "audio_b64": base64.b64encode(wav).decode(),
                    "mime": "audio/wav",
                })
            except VoiceUnavailable as e:
                self._send(200, {"ok": False, "error": str(e)})
            except Exception as e:
                self._send(200, {"ok": False, "error": "Speech failed: " + str(e)})
        elif self.path == "/api/voice/stt":
            # One push-to-talk clip in (base64; webm from the
            # browser's recorder, wav also fine — the decoder sniffs
            # the real format), its transcript out.
            data = self._body()
            vc = voice_config(cfg)
            if not vc["enabled"]:
                self._send(200, {"ok": False, "error": "Voice is turned off — enable it in the Voice tab."})
            else:
                try:
                    audio = base64.b64decode(str(data.get("audio_b64") or ""))
                except Exception:
                    audio = b""
                try:
                    text = transcribe_audio(audio, vc)
                    self._send(200, {"ok": True, "text": text})
                except VoiceUnavailable as e:
                    self._send(200, {"ok": False, "error": str(e)})
                except Exception as e:
                    self._send(200, {"ok": False, "error": "Transcription failed: " + str(e)})
        elif self.path == "/api/voice/call/start":
            # Opens the call record. The turns themselves travel
            # over /api/chat (same brain as typed chat) and are
            # recorded here, one by one, as they happen.
            vc = voice_config(cfg)
            if not vc["enabled"]:
                self._send(200, {"ok": False, "error": "Voice is turned off — enable it in the Voice tab."})
            else:
                state = load_voice_state()
                if not state.get("call"):
                    state["call"] = {
                        "id": str(int(time.time() * 1000)),
                        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "turns": [],
                    }
                    save_voice_state(state)
                self._send(200, {"ok": True, "call": state["call"]})
        elif self.path == "/api/voice/call/turn":
            data = self._body()
            state = load_voice_state()
            call = state.get("call")
            if not call:
                self._send(200, {"ok": False, "error": "No call in progress."})
            else:
                turn = {
                    "who": "navi" if data.get("who") == "navi" else "you",
                    "text": str(data.get("text") or "")[:4000],
                }
                ex = data.get("exec")
                if isinstance(ex, dict):
                    turn["exec"] = {
                        "command": str(ex.get("command") or "")[:500],
                        "output": str(ex.get("output") or "")[:4000],
                    }
                call.setdefault("turns", []).append(turn)
                state["call"] = call
                save_voice_state(state)
                self._send(200, {"ok": True})
        elif self.path == "/api/voice/call/end":
            # The finished call joins the permanent record:
            # voice/calls.json, newest last; the dashboard files
            # the turns into the conversation itself.
            state = load_voice_state()
            call = state.get("call")
            if not call:
                self._send(200, {"ok": True, "call": None})
            else:
                call["ended_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
                calls = load_voice_calls()
                calls.append(call)
                os.makedirs(VOICE_DIR, exist_ok=True)
                with open(VOICE_CALLS_PATH, "w") as f:
                    json.dump(calls, f)
                state["call"] = None
                save_voice_state(state)
                self._send(200, {"ok": True, "call": call})
        elif self.path == "/api/chat":
            data = self._body()
            messages = data.get("messages", [])
            # Sliding history: only the most recent exchanges ride
            # to the model. Prefill is paid per token on CPU, so an
            # ever-growing transcript makes every reply slower than
            # the last; the dashboard trims before sending and this
            # cap holds the line for any other caller. The full
            # conversation still lives in the dashboard — only the
            # model's view slides.
            if isinstance(messages, list) and len(messages) > CHAT_HISTORY_MESSAGES:
                messages = messages[-CHAT_HISTORY_MESSAGES:]
            # Citation footers never ride in message text (see
            # strip_citation_footer): scrub any an older build stored
            # in this thread's assistant history before it reaches
            # the model, so she never learns to imitate one.
            if isinstance(messages, list):
                messages = [
                    dict(m, content=strip_citation_footer(m.get("content")))
                    if isinstance(m, dict) and m.get("role") == "assistant" else m
                    for m in messages
                ]
            sudo = bool(data.get("sudo"))
            sudo_password = str(data.get("sudo_password") or "")
            chat_mode = data.get("mode") if data.get("mode") in ("cli", "navi") else None
            last = messages[-1]["content"] if messages else ""
            endpoint = cfg.get("live", {}).get("llamafile_endpoint", "http://localhost:8080/v1")
            # Chip invocation: "/chip <name>", "run the <name> chip",
            # or a loaded chip's name on its own runs the chip right
            # here and its output lands in the conversation — local
            # code, so it works with or without the model connected.
            # A bare "/chip" names no chip: answer with the shelf
            # itself — every installed chip and a line on what it
            # does — so the operator can pick one. An empty shelf
            # says so plainly and points at where chips come from.
            # A bare "/rag" names no question: answer with the
            # packs themselves — what is installed and which packs
            # are active — mirroring bare "/chip" and its shelf.
            if (last or "").strip().lower() == "/rag":
                _packs = local_rag_packs()
                if _packs:
                    _lines = []
                    for p in _packs:
                        _lines.append(
                            "• " + p["name"] + " — " + str(p["docCount"])
                            + " documents · " + ("active" if p["active"] else "off")
                        )
                    _reply = (
                        "Knowledge packs on this machine — only the active ones feed my answers:\n"
                        + "\n".join(_lines)
                    )
                else:
                    _reply = (
                        "No knowledge packs are installed yet. Open the RAG tab and install one "
                        "from the GitHub catalog (topic: navi-rag) or forge your own in RAG Studio; "
                        "then my answers can draw on it, and I'll name the pack when one informs an answer."
                    )
                payload = {
                    "reply": _reply,
                    "exec": None,
                    "mode": "rag",
                    "llamafile": "running" if llamafile_alive(endpoint) else "stopped",
                }
                if data.get("speak"):
                    payload["spoken"] = speak_reply(_reply, cfg)
                self._send(200, payload)
                return
            if (last or "").strip().lower() == "/chip":
                _shelf = local_chips()
                if _shelf:
                    _lines = []
                    for c in _shelf:
                        _d = (c.get("description") or "").strip()
                        if len(_d) > 90:
                            _d = _d[:87] + "..."
                        _lines.append("• " + c["name"] + (" — " + _d if _d else ""))
                    _reply = (
                        "On the shelf — /chip <name> runs one (the pills above the composer do too):\n"
                        + "\n".join(_lines)
                    )
                else:
                    _reply = (
                        "No chips are installed yet — the shelf is empty. Open the Chips tab and "
                        "install one from the GitHub catalog (Navi User Repo) or forge your own in Chip "
                        "Studio; then it lands here and /chip <name> runs it."
                    )
                payload = {
                    "reply": _reply,
                    "exec": None,
                    "mode": "chip",
                    "llamafile": "running" if llamafile_alive(endpoint) else "stopped",
                }
                if data.get("speak"):
                    payload["spoken"] = speak_reply(_reply, cfg)
                self._send(200, payload)
                return
            _query = chip_invocation(last)
            if _query is not None:
                _chip, _cargs = match_local_chip(_query, local_chips())
                if _chip is not None:
                    _result = execute_chip(_chip, _cargs, cfg)
                    payload = {
                        "reply": "Slotted in " + _chip["name"] + " and ran it — here's what it gave me:",
                        "exec": _result,
                        "mode": "chip",
                        "llamafile": "running" if llamafile_alive(endpoint) else "stopped",
                    }
                    if data.get("speak"):
                        payload["spoken"] = speak_reply(_result.get("output") or payload["reply"], cfg)
                    self._send(200, payload)
                    return
                if (last or "").strip().lower().startswith("/chip"):
                    _names = ", ".join(c["name"] for c in local_chips()) or "none"
                    self._send(200, {
                        "reply": "No chip by that name is loaded on this machine — the chips folder holds: " + _names + ".",
                        "exec": None,
                        "mode": "chip",
                        "llamafile": "running" if llamafile_alive(endpoint) else "stopped",
                    })
                    return
            # CLI-first routing: with the model connected, a line
            # whose first word is a system command runs right here —
            # no model call, no waiting on her to orchestrate it —
            # and the raw output returns as the exec block the
            # dashboard files as a terminal block. A leading "$"
            # forces this route; a leading "> " forces the line to
            # Navi, and the marker is stripped before she sees it.
            _cmd, _navi_text = cli_route(last or "", chat_mode)
            if _navi_text is not None and _navi_text != (last or ""):
                if messages:
                    messages[-1] = dict(messages[-1], content=_navi_text)
                last = _navi_text
            if _cmd is not None and llamafile_alive(endpoint):
                try:
                    _result = run_shell(_cmd, sudo=sudo, sudo_password=sudo_password) if _cmd else {"command": "", "output": "", "exit_code": 0}
                except Exception as e:
                    _result = {"command": _cmd, "output": str(e), "exit_code": 1}
                payload = {
                    "reply": "",
                    "exec": _result,
                    "mode": "cli",
                    "llamafile": "running",
                }
                if data.get("speak") and _result.get("output"):
                    payload["spoken"] = speak_reply(_result["output"], cfg)
                self._send(200, payload)
                return
            if not llamafile_alive(endpoint):
                # Command-line mode: no model is connected, so the
                # message itself is the command. A leading "$" is
                # decoration and gets stripped.
                cmd = (last or "").strip()
                if cmd.startswith("$"):
                    cmd = cmd[1:].strip()
                if cmd == ">" or cmd.startswith("> "):
                    # The force-Navi marker, with no model to force
                    # to: strip it rather than hand the shell a bare
                    # redirection operator.
                    cmd = cmd[1:].strip()
                try:
                    result = run_shell(cmd, sudo=sudo, sudo_password=sudo_password) if cmd else {"command": "", "output": "", "exit_code": 0}
                except Exception as e:
                    result = {"command": cmd, "output": str(e), "exit_code": 1}
                payload = {
                    "reply": "(command-line mode — navi.llamafile is not connected)",
                    "exec": result,
                    "mode": "command-line",
                    "llamafile": "stopped",
                }
                if data.get("speak"):
                    payload["spoken"] = speak_reply(result["output"] or payload["reply"], cfg)
                self._send(200, payload)
                return
            exec_block = None
            m = LIST_INTENT.search(last or "")
            if m:
                result = run_shell("ls " + expand(m.group(1)), sudo=sudo, sudo_password=sudo_password)
                exec_block = result
                messages = messages + [{
                    "role": "system",
                    "content": "The shell was run for the user. Command: "
                    + result["command"] + "\nReal output:\n" + result["output"]
                    + "\nPresent this output accurately.",
                }]
            # Knowledge packs: only active packs feed her answers.
            # When a pack's material answers the question it rides
            # along as context; the sources themselves travel back
            # as data (the payload's "rag" field, below) — never as
            # words in her reply.
            _hits = rag_retrieve(last)
            if _hits:
                _ctx = "\n\n".join(
                    "[" + h["pack"] + " · " + h["document"] + "] " + h["text"]
                    for h in _hits
                )
                messages = messages + [{
                    "role": "system",
                    "content": "Material from the operator's active knowledge packs — use it where it answers the question, in your own words. Do not name or cite the sources in your reply — the dashboard shows them under your message on its own:\n" + _ctx,
                }]
            # Navi's persona (Soul + Memory, from the config files)
            # rides along as the system prompt on every chat.
            messages = [{
                "role": "system",
                "content": persona_prompt(cfg, str(data.get("operator_name") or "")),
            }] + messages
            try:
                model = cfg.get("live", {}).get("model_name") or "navi"
                reply = llamafile_chat(messages, endpoint, model)
                # The reply text stays citation-free (see
                # strip_citation_footer): sources are data, drawn
                # as pills under this one message by the dashboard.
                # Only a turn whose question actually retrieved pack
                # material carries any — once the conversation moves
                # on, there is nothing to show.
                reply = strip_citation_footer(reply)
                payload = {"reply": reply, "exec": exec_block, "mode": "model", "llamafile": "running"}
                if _hits:
                    _srcs = []
                    for h in _hits:
                        _s = {"pack": h["pack"], "document": h["document"]}
                        if _s not in _srcs:
                            _srcs.append(_s)
                    payload["rag"] = _srcs
                if data.get("speak"):
                    payload["spoken"] = speak_reply(reply, cfg)
                self._send(200, payload)
            except Exception as e:
                self._send(502, {"error": str(e), "exec": exec_block})
        elif self.path == "/api/chips/run":
            # Run one loaded chip by name/slug (Chips tab Run buttons,
            # same machinery chat invocations use).
            data = self._body()
            chip, cargs = match_local_chip(str(data.get("query") or ""), local_chips())
            if chip is None:
                self._send(200, {"ok": False, "error": "No chip by that name is loaded on this machine."})
            else:
                result = execute_chip(chip, cargs, cfg)
                self._send(200, {
                    "ok": True,
                    "name": chip["name"],
                    "command": result["command"],
                    "output": result["output"],
                    "exit_code": result["exit_code"],
                })
        elif self.path == "/api/chips/save":
            # Chip Studio saving an edit: re-forge the chip file
            # with the new code inside it.
            data = self._body()
            fname = os.path.basename(str(data.get("file") or ""))
            name = str(data.get("name") or "").strip()[:120]
            code = str(data.get("code") or "")
            if not fname.endswith(".png") or not name or not code.strip():
                self._send(200, {"ok": False, "error": "A chip save needs a chip file, a name, and code."})
            else:
                payload = {
                    "name": name,
                    "description": str(data.get("description") or "")[:500],
                    "code": code[:200000],
                    "output": str(data.get("output") or "")[:5000],
                    "files": _valid_chip_files(data.get("files"), code[:200000]),
                }
                os.makedirs(CHIPS_DIR, exist_ok=True)
                with open(os.path.join(CHIPS_DIR, fname), "wb") as f:
                    f.write(build_cartridge_png(payload))
                # Saving an edit to a GitHub-installed chip marks the
                # divergence on its install record instead of hiding
                # it: the dashboard badges the chip as edited locally,
                # and a catalog update refuses rather than silently
                # overwriting the edits.
                rows = load_chip_installs()
                marked = False
                for r in rows:
                    if r.get("local_file") == fname and not str(r.get("full_name") or "").startswith("local/"):
                        r["locally_edited"] = True
                        marked = True
                if marked:
                    save_chip_installs(rows)
                self._send(200, {"ok": True, "filename": fname})
        elif self.path == "/api/workflows/create":
            data = self._body()
            name = str(data.get("name") or "").strip()[:120]
            steps = data.get("steps") or []
            known = {c["file"] for c in local_chips()}
            steps = [str(s) for s in steps if str(s) in known]
            if not name or len(steps) < 2:
                self._send(200, {"ok": False, "error": "A workflow needs a name and at least two chips from the folder."})
            else:
                rows = load_workflows()
                wf = {
                    "id": int(time.time() * 1000),
                    "name": name,
                    "description": str(data.get("description") or "")[:500],
                    "steps": steps,
                }
                rows.append(wf)
                save_workflows(rows)
                self._send(200, {"ok": True, "id": wf["id"]})
        elif self.path == "/api/workflows/delete":
            data = self._body()
            wid = data.get("id")
            save_workflows([w for w in load_workflows() if w.get("id") != wid])
            self._send(200, {"ok": True})
        elif self.path == "/api/workflows/run":
            data = self._body()
            wid = data.get("id")
            wf = next((w for w in load_workflows() if w.get("id") == wid), None)
            if wf is None:
                self._send(200, {"ok": False, "error": "That workflow no longer exists.", "steps": [], "finalOutput": None})
            else:
                self._send(200, run_workflow_chain(wf, cfg))
        elif self.path == "/api/rag/install":
            # Installing a pack means the pack itself lands here:
            # its documents download from the repo at the ref being
            # installed, into rag-packs/<slug>/, with the index
            # built at install time — and the record points at that
            # folder. A download that fails installs nothing.
            data = self._body()
            full = str(data.get("full_name") or "")
            rows = load_rag_installs()
            if any(r.get("full_name") == full for r in rows):
                self._send(200, {"ok": False, "error": "That pack is already installed."})
            else:
                try:
                    repo = fetch_repo_chip(full)
                    documents = fetch_pack_documents(repo)
                except Exception as e:
                    self._send(200, {"ok": False, "error": "The pack could not be downloaded from GitHub, so nothing was installed: " + str(e)})
                    return
                slug = rag_pack_slug(repo, rows)
                write_rag_pack(slug, repo["name"], repo["description"] or "", documents)
                rows.append(rag_install_record(repo, slug, len(documents)))
                save_rag_installs(rows)
                self._send(200, {"ok": True, "error": None})
        elif self.path == "/api/rag/update":
            data = self._body()
            full = str(data.get("full_name") or "")
            rows = load_rag_installs()
            inst = next((r for r in rows if r.get("full_name") == full), None)
            if inst is None:
                self._send(200, {"ok": False, "updated": False, "error": "That pack is not installed."})
            elif inst.get("locally_edited"):
                self._send(200, {"ok": False, "updated": False, "error": "This pack has local edits (edited in RAG Studio), so the update was not applied — it would overwrite them. Export the edited pack for GitHub to publish your version, or delete the install and reinstall to return to the published source."})
            else:
                try:
                    repo = fetch_repo_chip(full)
                except Exception as e:
                    self._send(200, {"ok": False, "updated": False, "error": "GitHub could not be reached for the update check: " + str(e)})
                    return
                latest = repo["latestRelease"]
                if latest:
                    newer = inst.get("installed_tag") != latest["tag"]
                else:
                    newer = bool(inst.get("installed_pushed_at") and repo["pushedAt"] > inst["installed_pushed_at"])
                slug = inst.get("local_dir")
                have_pack = bool(slug) and _rag_pack_index(slug) is not None
                if not newer and have_pack:
                    self._send(200, {"ok": True, "updated": False, "error": None})
                    return
                # Newer upstream — or the record's pack folder is
                # missing its index: (re)download the documents at
                # the latest ref and rebuild. A failed download
                # leaves the installed copy exactly as it was. The
                # operator's active flag survives the update.
                try:
                    documents = fetch_pack_documents(repo)
                except Exception as e:
                    self._send(200, {"ok": False, "updated": False, "error": "The pack could not be downloaded from GitHub, so the installed copy was left as it was: " + str(e)})
                    return
                if not slug:
                    slug = rag_pack_slug(repo, rows)
                write_rag_pack(slug, repo["name"], repo["description"] or "", documents)
                fresh = rag_install_record(repo, slug, len(documents))
                fresh["installed_at"] = inst.get("installed_at")
                fresh["active"] = bool(inst.get("active", True))
                rows[rows.index(inst)] = fresh
                save_rag_installs(rows)
                self._send(200, {"ok": True, "updated": True, "error": None})
        elif self.path == "/api/rag/delete":
            data = self._body()
            full = str(data.get("full_name") or "")
            rows = load_rag_installs()
            target = next((r for r in rows if r.get("full_name") == full), None)
            rows = [r for r in rows if r.get("full_name") != full]
            save_rag_installs(rows)
            # The pack's folder — documents and index — goes with
            # its record, GitHub-installed and Studio-forged alike.
            # A hand-dropped folder pack has no record; its folder
            # still goes when it is deleted by its local/ name.
            gone_dir = target.get("local_dir") if target else None
            if gone_dir is None and full.startswith("local/"):
                gone_dir = full[len("local/"):]
            if gone_dir:
                shutil.rmtree(
                    os.path.join(RAG_PACKS_DIR, gone_dir),
                    ignore_errors=True,
                )
            self._send(200, {"ok": True, "error": None})
        elif self.path == "/api/rag/toggle":
            # Only active packs feed retrieval. The flag lives on
            # the install record; a hand-dropped folder pack gets a
            # local record the first time it is toggled.
            data = self._body()
            full = str(data.get("full_name") or "")
            active = bool(data.get("active"))
            rows = load_rag_installs()
            inst = next((r for r in rows if r.get("full_name") == full), None)
            if inst is None and full.startswith("local/"):
                slug = full[len("local/"):]
                if _rag_pack_index(slug) is not None:
                    rows.append({
                        "full_name": full,
                        "name": slug,
                        "html_url": "",
                        "installed_tag": None,
                        "installed_ref": "local pack",
                        "installed_pushed_at": None,
                        "installed_at": _now_iso(),
                        "local_dir": slug,
                        "active": active,
                        "doc_count": len((_rag_pack_index(slug) or {}).get("documents") or []),
                    })
                    save_rag_installs(rows)
                    self._send(200, {"ok": True, "error": None})
                    return
            if inst is None:
                self._send(200, {"ok": False, "error": "That pack is not installed."})
            else:
                inst["active"] = active
                save_rag_installs(rows)
                self._send(200, {"ok": True, "error": None})
        elif self.path == "/api/rag/forge":
            # RAG Studio: package documents into a knowledge pack
            # in rag-packs/ — documents, built index, and metadata —
            # ready to activate and use immediately. The documents
            # arrive either as files the operator picked in the
            # Studio (read in the browser and sent as text; PDFs
            # travel as base64 and their text is extracted here)
            # or from a folder on this machine's disk (source_dir,
            # read here, PDFs extracted the same way).
            data = self._body()
            name = str(data.get("name") or "").strip()[:120]
            description = str(data.get("description") or "")[:500]
            documents = []
            source_dir = str(data.get("source_dir") or "").strip()
            if source_dir:
                root = os.path.abspath(os.path.expanduser(source_dir))
                if not os.path.isdir(root):
                    self._send(200, {"ok": False, "error": "That folder is not on this machine: " + source_dir})
                    return
                found = []
                for dirpath, _dirs, files in os.walk(root):
                    for fn in sorted(files):
                        if fn.lower().endswith((".md", ".txt", ".pdf")):
                            found.append(os.path.join(dirpath, fn))
                found.sort()
                if not found:
                    self._send(200, {"ok": False, "error": "No .md, .txt or .pdf documents in that folder — a pack is made of Markdown, text, or PDF documents."})
                    return
                if len(found) > RAG_MAX_DOCS:
                    self._send(200, {"ok": False, "error": "That folder holds " + str(len(found)) + " documents — a pack caps at " + str(RAG_MAX_DOCS) + "."})
                    return
                for path in found:
                    if path.lower().endswith(".pdf"):
                        try:
                            with open(path, "rb") as f:
                                body = pdf_extract_text(f.read())
                        except Exception as e:
                            self._send(200, {"ok": False, "error": "Could not read " + path + ": " + str(e)})
                            return
                        if not body:
                            self._send(200, {"ok": False, "error": path + " has no extractable text — a scanned or image-only PDF can't be indexed."})
                            return
                    else:
                        try:
                            with open(path) as f:
                                body = f.read()
                        except Exception as e:
                            self._send(200, {"ok": False, "error": "Could not read " + path + ": " + str(e)})
                            return
                    documents.append({
                        "title": os.path.relpath(path, root),
                        "body": body[:RAG_MAX_DOC_CHARS],
                    })
            for raw in data.get("documents") or []:
                if not isinstance(raw, dict):
                    continue
                title = str(raw.get("title") or "document")[:200]
                if raw.get("pdf_base64"):
                    try:
                        body = pdf_extract_text(base64.b64decode(str(raw.get("pdf_base64"))))
                    except Exception:
                        body = ""
                    if not body:
                        self._send(200, {"ok": False, "error": title + " has no extractable text — a scanned or image-only PDF can't be indexed."})
                        return
                    documents.append({
                        "title": title,
                        "body": body[:RAG_MAX_DOC_CHARS],
                    })
                elif str(raw.get("body") or "").strip():
                    documents.append({
                        "title": title,
                        "body": str(raw.get("body"))[:RAG_MAX_DOC_CHARS],
                    })
            documents = documents[:RAG_MAX_DOCS]
            if not name:
                self._send(200, {"ok": False, "error": "A pack needs a name."})
            elif not documents:
                self._send(200, {"ok": False, "error": "A pack needs at least one document — pick files in the Studio or name a folder on disk."})
            else:
                rows = load_rag_installs()
                slug = chip_slug(name)
                taken = {
                    r.get("local_dir") for r in rows
                    if r.get("full_name") != "local/" + slug
                }
                base = slug
                n = 2
                while slug in taken:
                    slug = base + "-" + str(n)
                    n += 1
                write_rag_pack(slug, name, description, documents)
                rows = [r for r in rows if r.get("full_name") != "local/" + slug]
                rows.append({
                    "full_name": "local/" + slug,
                    "name": name,
                    "html_url": "",
                    "installed_tag": None,
                    "installed_ref": "forged in RAG Studio",
                    "installed_pushed_at": None,
                    "installed_at": _now_iso(),
                    "local_dir": slug,
                    "active": True,
                    "doc_count": len(documents),
                })
                save_rag_installs(rows)
                self._send(200, {"ok": True, "error": None, "slug": slug})
        elif self.path == "/api/rag/update-pack":
            # RAG Studio saving an edit to a pack already in the
            # folder: the new name, description, and document set
            # (documents added or removed in the Studio; PDFs travel
            # as base64 and contribute their extracted text, exactly
            # like the forge) replace the pack's contents in its own
            # folder, and the index rebuilds from the new set. The
            # pack's active flag survives. A GitHub-installed pack is
            # marked locally_edited — the divergence from its
            # published source is stated, never silent, and a catalog
            # update refuses rather than overwriting the edits.
            data = self._body()
            slug = os.path.basename(str(data.get("slug") or ""))
            name = str(data.get("name") or "").strip()[:120]
            description = str(data.get("description") or "")[:500]
            documents = []
            for raw in data.get("documents") or []:
                if not isinstance(raw, dict):
                    continue
                title = str(raw.get("title") or "document")[:200]
                if raw.get("pdf_base64"):
                    try:
                        body = pdf_extract_text(base64.b64decode(str(raw.get("pdf_base64"))))
                    except Exception:
                        body = ""
                    if not body:
                        self._send(200, {"ok": False, "error": title + " has no extractable text — a scanned or image-only PDF can't be indexed."})
                        return
                    documents.append({"title": title, "body": body[:RAG_MAX_DOC_CHARS]})
                elif str(raw.get("body") or "").strip():
                    documents.append({"title": title, "body": str(raw.get("body"))[:RAG_MAX_DOC_CHARS]})
            documents = documents[:RAG_MAX_DOCS]
            if not slug or _rag_pack_index(slug) is None:
                self._send(200, {"ok": False, "error": "That pack is not in the folder."})
            elif not name:
                self._send(200, {"ok": False, "error": "A pack needs a name."})
            elif not documents:
                self._send(200, {"ok": False, "error": "A pack needs at least one document — add one in the Studio before saving."})
            else:
                write_rag_pack(slug, name, description, documents)
                rows = load_rag_installs()
                for r in rows:
                    if r.get("local_dir") == slug:
                        r["name"] = name
                        r["doc_count"] = len(documents)
                        if not str(r.get("full_name") or "").startswith("local/"):
                            r["locally_edited"] = True
                save_rag_installs(rows)
                self._send(200, {"ok": True, "error": None, "slug": slug})
        elif self.path == "/api/rag/export":
            # Export for GitHub: build the pack's repo ZIP in
            # rag-exports/ — README page, manifest, the built
            # index.json (reference copy; installs rebuild it),
            # documents/, .gitignore.
            data = self._body()
            slug = os.path.basename(str(data.get("slug") or ""))
            version = str(data.get("version") or "0.1.0").strip()[:40] or "0.1.0"
            try:
                zip_name, repo_files = export_rag_pack(slug, version)
                self._send(200, {"ok": True, "error": None, "file": zip_name, "files": repo_files})
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e), "file": None, "files": []})
        elif self.path == "/api/chips/export":
            # Export for GitHub: build a local chip's repo ZIP
            # in chips-exports/ — README page, navi-chip.json, the
            # chip's files at the root, the chip, .gitignore.
            data = self._body()
            fname = os.path.basename(str(data.get("file") or ""))
            version = str(data.get("version") or "0.1.0").strip()[:40] or "0.1.0"
            try:
                zip_name, repo_files = export_chip(fname, version)
                self._send(200, {"ok": True, "error": None, "file": zip_name, "files": repo_files})
            except Exception as e:
                self._send(200, {"ok": False, "error": str(e), "file": None, "files": []})
        elif self.path == "/api/chips/install":
            # Installing a chip means the chip itself lands here:
            # its source is downloaded from the repo at the ref
            # being installed and forged into a chip in chips/,
            # and the install record points at that chip. A
            # download that fails installs nothing — no record for a
            # chip that is not actually on this machine.
            data = self._body()
            full = str(data.get("full_name") or "")
            rows = load_chip_installs()
            if any(r.get("full_name") == full for r in rows):
                self._send(200, {"ok": False, "error": "That chip is already installed."})
            else:
                try:
                    repo = fetch_repo_chip(full)
                    payload, source_file = fetch_chip_payload(repo)
                except Exception as e:
                    self._send(200, {"ok": False, "error": "The chip could not be downloaded from GitHub, so nothing was installed: " + str(e)})
                    return
                filename = chip_cartridge_filename(repo, rows)
                os.makedirs(CHIPS_DIR, exist_ok=True)
                with open(os.path.join(CHIPS_DIR, filename), "wb") as f:
                    f.write(build_cartridge_png(payload))
                record = chip_install_record(repo)
                record["local_file"] = filename
                record["source_file"] = source_file
                rows.append(record)
                save_chip_installs(rows)
                self._send(200, {"ok": True, "error": None})
        elif self.path == "/api/chips/update":
            data = self._body()
            full = str(data.get("full_name") or "")
            rows = load_chip_installs()
            inst = next((r for r in rows if r.get("full_name") == full), None)
            if inst is None:
                self._send(200, {"ok": False, "updated": False, "error": "That chip is not installed."})
            elif inst.get("locally_edited"):
                self._send(200, {"ok": False, "updated": False, "error": "This chip has local edits (edited in Chip Studio), so the update was not applied — it would overwrite them. Export the edited chip for GitHub to publish your version, or delete the install and reinstall to return to the published source."})
            else:
                try:
                    repo = fetch_repo_chip(full)
                except Exception as e:
                    self._send(200, {"ok": False, "updated": False, "error": "GitHub could not be reached for the update check: " + str(e)})
                    return
                latest = repo["latestRelease"]
                if latest:
                    newer = inst.get("installed_tag") != latest["tag"]
                else:
                    newer = bool(inst.get("installed_pushed_at") and repo["pushedAt"] > inst["installed_pushed_at"])
                filename = inst.get("local_file")
                have_cartridge = bool(filename) and os.path.isfile(os.path.join(CHIPS_DIR, filename))
                if not newer and have_cartridge:
                    self._send(200, {"ok": True, "updated": False, "error": None})
                    return
                # Newer upstream — or the record predates chips
                # landing on disk and the chip itself is missing:
                # (re)download the source at the latest ref and
                # re-forge the chip, so what runs here is what
                # the repo now ships. A failed download leaves the
                # installed copy exactly as it was.
                try:
                    payload, source_file = fetch_chip_payload(repo)
                except Exception as e:
                    self._send(200, {"ok": False, "updated": False, "error": "The chip could not be downloaded from GitHub, so the installed copy was left as it was: " + str(e)})
                    return
                if not filename:
                    filename = chip_cartridge_filename(repo, rows)
                os.makedirs(CHIPS_DIR, exist_ok=True)
                with open(os.path.join(CHIPS_DIR, filename), "wb") as f:
                    f.write(build_cartridge_png(payload))
                fresh = chip_install_record(repo)
                fresh["installed_at"] = inst.get("installed_at")
                fresh["local_file"] = filename
                fresh["source_file"] = source_file
                rows[rows.index(inst)] = fresh
                save_chip_installs(rows)
                self._send(200, {"ok": True, "updated": True, "error": None})
        elif self.path == "/api/chips/delete":
            data = self._body()
            full = str(data.get("full_name") or "")
            rows = load_chip_installs()
            target = next((r for r in rows if r.get("full_name") == full), None)
            rows = [r for r in rows if r.get("full_name") != full]
            save_chip_installs(rows)
            # The chip's chip goes with its record — true for
            # Studio-forged chips and GitHub-downloaded ones alike:
            # deleting an install takes the chip off the shelf.
            if target and target.get("local_file"):
                try:
                    os.remove(os.path.join(CHIPS_DIR, target["local_file"]))
                except Exception:
                    pass
            self._send(200, {"ok": True, "error": None})
        elif self.path == "/api/chips/create":
            # Chip Studio: forge a new chip into a .png chip —
            # code embedded in the image — save it into chips/, and
            # register it as a local install.
            data = self._body()
            name = str(data.get("name") or "").strip()[:120]
            code = str(data.get("code") or "")
            if not name or not code.strip():
                self._send(200, {"ok": False, "error": "A chip needs a name and code.", "filename": None})
            else:
                payload = {
                    "name": name,
                    "description": str(data.get("description") or "")[:500],
                    "code": code[:200000],
                    "output": str(data.get("output") or "")[:5000],
                    "files": _valid_chip_files(data.get("files"), code[:200000]),
                }
                slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "chip"
                filename = slug + ".png"
                os.makedirs(CHIPS_DIR, exist_ok=True)
                with open(os.path.join(CHIPS_DIR, filename), "wb") as f:
                    f.write(build_cartridge_png(payload))
                rows = [r for r in load_chip_installs() if r.get("full_name") != "local/" + slug]
                rows.append({
                    "full_name": "local/" + slug,
                    "name": name,
                    "html_url": "",
                    "installed_tag": None,
                    "installed_ref": "chip " + filename,
                    "installed_pushed_at": None,
                    "installed_at": _now_iso(),
                    "local_file": filename,
                })
                save_chip_installs(rows)
                self._send(200, {"ok": True, "error": None, "filename": filename})
        elif self.path == "/api/github/client-id":
            # The OAuth App client id is a config value (it must be
            # registered under the project owner's GitHub account, so
            # none ships). It is not a secret — Device Flow has none.
            data = self._body()
            save_github_settings({"client_id": str(data.get("client_id") or "").strip()[:80]})
            self._send(200, github_status_payload(load_config()))
        elif self.path == "/api/github/settings":
            data = self._body()
            patch = {}
            repo = str(data.get("backup_repo") or "").strip()
            if repo:
                if not re.match(r"^[A-Za-z0-9._-]+$", repo) or repo.startswith(".") or repo.startswith("-"):
                    self._send(200, {"ok": False, "error": "Repository names are letters, digits, dots, dashes, and underscores."})
                    return
                patch["backup_repo"] = repo[:100]
            if isinstance(data.get("backup_private"), bool):
                patch["backup_private"] = data["backup_private"]
            if isinstance(data.get("backup_items"), list):
                chosen = [i for i in data["backup_items"] if i in GITHUB_BACKUP_ITEMS]
                patch["backup_items"] = [i for i in GITHUB_BACKUP_ITEMS if i in GITHUB_CORE_BACKUP_ITEMS or i in chosen]
            if data.get("backup_interval_days") in (1, 3, 5, 7):
                patch["backup_interval_days"] = data["backup_interval_days"]
            save_github_settings(patch)
            self._send(200, github_status_payload(load_config()))
        elif self.path == "/api/github/signin/start":
            self._send(200, github_device_start(cfg))
        elif self.path == "/api/github/signin/poll":
            self._send(200, github_device_poll(cfg))
        elif self.path == "/api/github/signout":
            # Signing out deletes the only copy of the token. Navi
            # herself is untouched — she never needed it.
            _github_device.clear()
            try:
                os.remove(GITHUB_TOKEN_PATH)
            except Exception:
                pass
            self._send(200, github_status_payload(load_config()))
        elif self.path == "/api/github/backup":
            data = self._body()
            dash = data.get("dashboard") if isinstance(data.get("dashboard"), dict) else None
            self._send(200, github_run_backup(load_config(), dash))
        elif self.path == "/api/github/import/preview":
            # Preview writes nothing: it pulls the backup down and
            # reports, per essential, what restoring it would do.
            data = self._body()
            dash = data.get("dashboard") if isinstance(data.get("dashboard"), dict) else None
            fetched, err = github_fetch_backup(load_config())
            if err:
                self._send(200, {"ok": False, "error": err, "changes": []})
            else:
                changes, _items = github_import_changes(load_config(), fetched, dash)
                self._send(200, {
                    "ok": True,
                    "error": None,
                    "changes": changes,
                    "backedUpAt": fetched["manifest"].get("backedUpAt"),
                })
        elif self.path == "/api/github/import/apply":
            # Only ever the second half of preview → confirm. The
            # apply re-fetches, so what lands is the backup as it
            # stands now, and the dashboard settings in the backup
            # ride back in the answer for the dashboard to adopt.
            fetched, err = github_fetch_backup(load_config())
            if err:
                self._send(200, {"ok": False, "error": err})
            else:
                self._send(200, github_apply_import(load_config(), fetched))
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, *args):
        pass


def probe_bridge(port):
    # What is already answering on the bridge port, if anything:
    # the /api/status JSON, or None when nothing (or something that
    # is not a Navi bridge) answers.
    try:
        with urllib.request.urlopen(
            "http://127.0.0.1:" + str(port) + "/api/status", timeout=2
        ) as resp:
            data = json.loads(resp.read().decode())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def probe_port_holder(port):
    # Identify whatever is serving the bridge port when it is NOT a
    # Navi bridge: fetch its front page and lift the <title> out of
    # it, so messages can name the incumbent — the operator's own
    # earlier UI for Navi also served this port, and "something else
    # is on 8675" is a useless diagnosis next to its page's own name.
    # Returns {"navi": True} for a Navi bridge of any build, a dict
    # describing the foreign page, or None when nothing answers.
    status = probe_bridge(port)
    if status is not None and status.get("app") == "Navi: Apex":
        return {"navi": True, "build": status.get("bridge")}
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:" + str(port) + "/",
            headers={"User-Agent": "navi-bridge-probe"},
        )
        with urllib.request.urlopen(req, timeout=2) as resp:
            raw = resp.read(65536).decode("utf-8", "replace")
    except Exception:
        return None
    m = re.search(r"<title[^>]*>(.*?)</title>", raw, re.I | re.S)
    title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    return {"navi": False, "title": title or "(a page with no title)"}


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def claim_pid_file():
    try:
        with open(PID_PATH, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass


def drop_pid_file():
    try:
        with open(PID_PATH) as f:
            mine = f.read().strip() == str(os.getpid())
        if mine:
            os.remove(PID_PATH)
    except Exception:
        pass


def watchdog(started_mtime):
    # Exit with code 75 ("replaced — relaunch me") when this process
    # has been superseded: bridge.py changed on disk (a reinstall
    # landed while we were running), or a newer bridge claimed the
    # pid file and is waiting for this port. The launchers relaunch
    # the bridge on 75, so an update takes over without the operator
    # hunting down a zombie process.
    self_path = os.path.abspath(__file__)
    while True:
        time.sleep(2)
        try:
            if started_mtime and os.path.getmtime(self_path) != started_mtime:
                os._exit(75)
        except SystemExit:
            raise
        except Exception:
            pass
        try:
            with open(PID_PATH) as f:
                owner = int((f.read() or "").strip() or 0)
            if owner and owner != os.getpid() and pid_alive(owner):
                os._exit(75)
        except SystemExit:
            raise
        except Exception:
            pass


if __name__ == "__main__":
    cfg = load_config()
    # The port is this build's own constant (BRIDGE_PORT), never the
    # config's: a navi.config.json carried across from an older
    # package build records that build's port, and honoring it once
    # bound this bridge to the old address while its launcher polled
    # the new one — the bridge cheerfully reported itself "already
    # running" on a port nothing was waiting on. A disagreeing config
    # value is named, then ignored.
    port = BRIDGE_PORT
    try:
        cfg_port = int(cfg.get("bridge", {}).get("port") or 0)
    except Exception:
        cfg_port = 0
    if cfg_port and cfg_port != port:
        print("Note: config/navi.config.json names bridge port "
              + str(cfg_port) + ", left over from an older install — "
              "ignoring it; this build's bridge port is "
              + str(port) + ".", flush=True)
    existing = probe_bridge(port)
    if existing and existing.get("app") == "Navi: Apex":
        if existing.get("bridge") == BRIDGE_BUILD:
            print("Navi bridge (build " + BRIDGE_BUILD + ") is already "
                  "running on http://localhost:" + str(port)
                  + " — the dashboard is live at that address; "
                  "nothing to do.", flush=True)
            sys.exit(0)
        # An older build holds the port. Claim the pid file: a bridge
        # new enough to watch it exits and frees the port; the bind
        # loop below waits for that (and reports plainly if the old
        # process predates the watchdog and has to be quit by hand).
        print("An older Navi bridge (build "
              + str(existing.get("bridge") or "pre-stamp") + ") is answering "
              "on port " + str(port) + " — taking over for build "
              + BRIDGE_BUILD + ".", flush=True)
    else:
        # Not a Navi bridge. If a different program is serving the
        # port — the operator's own earlier UI for Navi also lived at
        # this address — say so now, by name: the bind loop below can
        # only fail against an incumbent that will never step aside,
        # and "an older bridge holds the port" would send the operator
        # hunting for a process that doesn't exist.
        holder = probe_port_holder(port)
        if holder and not holder.get("navi"):
            # A foreign program will never step aside for the pid
            # watchdog, so there is nothing to wait for: name it and
            # stop. (The bind loop keeps the same diagnosis as a
            # backstop for a holder that appears after this probe.)
            print("Port " + str(port) + " is already served by a "
                  "different program — its page is titled \""
                  + str(holder.get("title")) + "\". That program, not "
                  "this bridge, is what a browser shows at "
                  "http://localhost:" + str(port) + " until it stops. "
                  "Quit it (find it with: lsof -i :" + str(port)
                  + ") and launch Apex again.", flush=True)
            sys.exit(1)
    claim_pid_file()
    atexit.register(drop_pid_file)
    # The sudo root shell (if the operator authenticated) is a child
    # of this process: close it on the way out so no root shell
    # outlives the bridge. Its stdin is a pipe owned by this process,
    # so even a hard kill of the bridge leaves it reading EOF — this
    # is the tidy path, not the only one.
    atexit.register(_root_shell_kill)
    try:
        _mtime = os.path.getmtime(os.path.abspath(__file__))
    except Exception:
        _mtime = 0
    threading.Thread(target=watchdog, args=(_mtime,), daemon=True).start()
    # GitHub interval backups: checks on launch and while the bridge
    # runs whether a backup is due on the operator's chosen interval,
    # and runs it when signed in. Daemon thread; dies with the bridge.
    threading.Thread(target=github_auto_backup_loop, daemon=True).start()
    # Threading: a connect that starts the server can wait minutes
    # for the model to load; it must not block status and chat.
    server = None
    deadline = time.time() + 30
    while server is None:
        try:
            server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        except OSError:
            if time.time() >= deadline:
                # Name the actual incumbent — an older Navi bridge
                # that never stepped aside, or a different program
                # entirely — instead of always blaming the bridge.
                holder = probe_port_holder(port)
                if holder and not holder.get("navi"):
                    print("Port " + str(port) + " is held by a different "
                          "program (its page is titled \""
                          + str(holder.get("title")) + "\"), not by a "
                          "Navi bridge — it will never step aside for "
                          "this one. Quit that program (find it with: "
                          "lsof -i :" + str(port) + ") and launch "
                          "Apex again.", flush=True)
                else:
                    print("Port " + str(port) + " is still held by the older "
                          "bridge, and it did not step aside — it predates the "
                          "self-update watchdog. Quit the running Navi bridge "
                          "(close the app, or end the python bridge.py process) "
                          "and launch again.", flush=True)
                sys.exit(1)
            time.sleep(1)
    print("Navi bridge (build " + BRIDGE_BUILD + ") on http://localhost:" + str(port), flush=True)
    server.serve_forever()
